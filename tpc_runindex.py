#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import csv
import json
import logging
import re
import sys
from pathlib import Path
from typing import Dict, Any, Iterator, List, Optional

RUNID_RE = re.compile(r"^\d{5}$")

def normalize_str(x: Any) -> str:
    if x is None:
        return ""
    s = str(x).replace("\n", " ").strip()
    return s

def load_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error("JSON parse failed: %s (%s)", path, e)
        return None

def iter_runinfo_paths(base_dir: Path, runtype: str) -> Iterator[Dict[str, Any]]:
    rt_dir = base_dir / runtype
    if not rt_dir.exists():
        raise FileNotFoundError(f"runtype dir not found: {rt_dir}")

    for p in sorted(rt_dir.iterdir()):
        if not p.is_dir():
            continue
        run_id_dir = p.name
        if not RUNID_RE.match(run_id_dir):
            continue

        runinfo_path = p / "runinfo.json"
        if not runinfo_path.exists():
            logging.warning("missing runinfo.json: %s", runinfo_path)
            continue

        yield {"runtype": runtype, "run_id_dir": run_id_dir, "runinfo_path": runinfo_path}

def extract_run_comment(run_option: Dict[str, Any], info: Dict[str, Any]) -> str:
    rc = run_option.get("run_comment")
    if rc is None:
        rc = info.get("run_comment", "")
    if isinstance(rc, list):
        return ", ".join(normalize_str(x) for x in rc if x)
    return normalize_str(rc)

def extract_fields_and_validate(run_id_dir: str, info: Dict[str, Any]) -> Dict[str, Any]:
    run_info = info.get("run_info", {})
    if not isinstance(run_info, dict):
        raise ValueError("run_info is missing or not a dict")

    run_id_json = normalize_str(run_info.get("run_id"))
    if not run_id_json:
        raise ValueError("run_info.run_id missing/empty")

    if run_id_json != run_id_dir:
        raise RuntimeError(
            f"RUN_ID MISMATCH: dir={run_id_dir} != run_info.run_id={run_id_json}"
        )

    run_option = info.get("run_option", {})

    row = {
        "run_id": run_id_json,
        "trigger_mode": normalize_str(run_info.get("trigger_mode") or run_info.get("trigger_style")),
        "outfile_path": normalize_str(run_info.get("outfile_path")),
        "outfile_name": normalize_str(run_info.get("outfile_name")),
        "run_tag": normalize_str(run_option.get("run_tag")),
        "run_comment": extract_run_comment(run_option,info),  # 从 run_option 读
        "acq_time": normalize_str(run_info.get("acq_time")),
    }
    return row


def export_csv(base_dir: Path, runtypes: List[str], out_csv: Path, include_acq_time: bool):
    fieldnames = ["run_id", "trigger_mode", "outfile_path", "outfile_name", "run_tag", "run_comment"]
    if include_acq_time:
        fieldnames.append("acq_time")

    out_csv.parent.mkdir(parents=True, exist_ok=True)

    n_rows = 0
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for runtype in runtypes:
            for meta in iter_runinfo_paths(base_dir, runtype):
                info = load_json(meta["runinfo_path"])
                if info is None:
                    # JSON 解析失败：直接退出（也可以改成跳过；按你的“怕找错”思路，建议退出）
                    raise RuntimeError(f"Failed to parse: {meta['runinfo_path']}")

                # 这里会做 run_id 一致性校验；不一致直接抛异常 -> main 捕获后退出
                row = extract_fields_and_validate(meta["run_id_dir"], info)

                writer.writerow({k: row.get(k, "") for k in fieldnames})
                n_rows += 1

    logging.info("exported %d rows to %s", n_rows, out_csv)

def match_comment(comment: str, pattern: str, mode: str) -> bool:
    if mode == "contains":
        return pattern in comment
    if mode == "exact":
        return comment == pattern
    if mode == "regex":
        return re.search(pattern, comment) is not None
    raise ValueError(f"unknown match mode: {mode}")

def find_runs_by_comment(base_dir: Path, runtypes: List[str], pattern: str, mode: str, print_mode: str):
    """
    print_mode:
      - run_id: 只打印 run_id
      - csv: 打印 runtype,run_id,run_comment
    """
    for runtype in runtypes:
        for meta in iter_runinfo_paths(base_dir, runtype):
            info = load_json(meta["runinfo_path"])
            if info is None:
                raise RuntimeError(f"Failed to parse: {meta['runinfo_path']}")

            row = extract_fields_and_validate(meta["run_id_dir"], info)
            if match_comment(row["run_comment"], pattern, mode):
                if print_mode == "run_id":
                    print(row["run_id"])
                else:
                    print(f"{runtype},{row['run_id']},{row['run_comment']}")

def parse_args():
    p = argparse.ArgumentParser(description="Index TPC runs and export to CSV / find by run_comment")
    p.add_argument("--base-dir", default="/mnt/data/TPC", type=Path)
    p.add_argument("-v", "--verbose", action="store_true")

    sub = p.add_subparsers(dest="cmd", required=True)

    p_export = sub.add_parser("export-csv", help="export run info to csv")
    p_export.add_argument("--runtypes", nargs="+", required=True, help="e.g. run6_Xe run5_Ar")
    p_export.add_argument("--out-csv", required=True, type=Path)
    p_export.add_argument("--include-acq-time", action="store_true")

    p_find = sub.add_parser("find", help="find runs by run_comment pattern")
    p_find.add_argument("--runtypes", nargs="+", required=True, help="e.g. run6_Xe run5_Ar")
    p_find.add_argument("--pattern", required=True)
    p_find.add_argument("--mode", choices=["contains", "exact", "regex"], default="contains")
    p_find.add_argument("--print-mode", choices=["run_id", "csv"], default="run_id")

    return p.parse_args()

 
def main():
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s"
    )

    try:
        if args.cmd == "export-csv":
            export_csv(args.base_dir, args.runtypes, args.out_csv, args.include_acq_time)
        elif args.cmd == "find":
            find_runs_by_comment(args.base_dir, args.runtypes, args.pattern, args.mode, args.print_mode)
    except Exception as e:
        # 按你的要求：遇到 run_id 不匹配等严重问题 -> 打印错误并退出
        logging.error("%s", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
