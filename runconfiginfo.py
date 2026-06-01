#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import re
import shutil
from pathlib import Path


TPC_ROOT = Path("/mnt/data/TPC")
DEFAULT_CONFIGURE_NEW = Path("/home/daq/DAQ_DEMO/configure_new.txt")


def load_json_file(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def find_latest_run(tpc_root=TPC_ROOT):
    """
    Find latest run under /mnt/data/TPC/{runtype}/{run_id}/
    Return: (runtype, run_id, run_dir)
    """
    if not tpc_root.exists():
        raise FileNotFoundError(f"TPC root not found: {tpc_root}")

    candidates = []

    for runtype_dir in tpc_root.iterdir():
        if not runtype_dir.is_dir():
            continue

        for run_dir in runtype_dir.iterdir():
            if not run_dir.is_dir():
                continue
            if re.fullmatch(r"\d{5}", run_dir.name):
                candidates.append((runtype_dir.name, run_dir.name, run_dir))

    if not candidates:
        raise RuntimeError(f"No valid run directory found under {tpc_root}")

    candidates.sort(key=lambda x: (int(x[1]), x[0]))
    return candidates[-1]


def copy_config_file(configure_new_path, target_run_dir):
    """
    Copy configure_new.txt -> config.cfg into target_run_dir.
    """
    configure_new_path = Path(configure_new_path)
    if not configure_new_path.exists():
        raise FileNotFoundError(f"configure_new.txt not found: {configure_new_path}")

    target_run_dir = Path(target_run_dir)
    target_run_dir.mkdir(parents=True, exist_ok=True)

    target_config = target_run_dir / "config.cfg"
    shutil.copy2(configure_new_path, target_config)
    return target_config


def read_config_fields(config_file):
    """
    Parse config.cfg line by line, ignoring lines starting with ###.
    Extract:
      - SELF_TRIGGER
      - EXTERNAL_TRIGGER
      - ACQ_TIME
      - RECORD_LENGTH
      - OUTFILE_PATH
      - OUTFILE_NAME
    """
    config_file = Path(config_file)
    if not config_file.exists():
        raise FileNotFoundError(f"config file not found: {config_file}")

    values = {
        "SELF_TRIGGER": None,
        "EXTERNAL_TRIGGER": None,
        "ACQ_TIME": None,
        "RECORD_LENGTH": None,
        "OUTFILE_PATH": None,
        "OUTFILE_NAME": None,
    }

    with config_file.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()

            if not line or line.startswith("###"):
                continue

            for key in values.keys():
                if line.startswith(key):
                    parts = line.split(None, 1)
                    if len(parts) < 2:
                        raise ValueError(f"Cannot parse value for {key} in line: {line}")
                    values[key] = parts[1].strip()
                    break

    for k, v in values.items():
        if v is None:
            raise ValueError(f"Required field {k} not found in {config_file}")

    return values


def parse_trigger_style(self_trigger, external_trigger):
    """
    Rules:
      SELF_TRIGGER YES and EXTERNAL_TRIGGER DISABLED -> self
      SELF_TRIGGER NO  and EXTERNAL_TRIGGER ACQUISITION_ONLY -> ext
    Any other combination -> error.
    """
    self_trigger = self_trigger.upper()
    external_trigger = external_trigger.upper()

    if self_trigger == "YES" and external_trigger == "DISABLED":
        return "self"
    if self_trigger == "NO" and external_trigger == "ACQUISITION_ONLY":
        return "ext"

    raise ValueError(
        f"Unsupported trigger combination: SELF_TRIGGER={self_trigger}, "
        f"EXTERNAL_TRIGGER={external_trigger}"
    )


def infer_dec_info(runtype):
    """
    Infer dec_info from runtype:
      run<number>_Ar     -> dec=LAr, dec_name=LAr TPC
      run<number>_Xe     -> dec=LXe, dec_name=LXe TPC
      run<number>_Ar_Xe  -> dec=LAr, dec_name=LAr doping Xe TPC
    """
    rt = runtype.lower()

    if re.fullmatch(r"run\d+_ar_xe", rt):
        return {"dec": "LAr", "dec_name": "LAr doping Xe TPC"}
    if re.fullmatch(r"run\d+_ar", rt):
        return {"dec": "LAr", "dec_name": "LAr TPC"}
    if re.fullmatch(r"run\d+_xe", rt):
        return {"dec": "LXe", "dec_name": "LXe TPC"}

    raise ValueError(f"Cannot infer dec_info from runtype: {runtype}")



def expand_threshold_patches(threshold_data):
    """
    Expand board-level threshold.json to per-channel threshold_patches.
    Expected board-level format:
      [
        {
          "board_id": 0,
          "channel_id": [9, 10, 11],
          "trg_threshold": [100, 110, 120]
        },
        ...
      ]
    """
    threshold_patches = []

    for item in threshold_data:
        if not isinstance(item, dict):
            raise ValueError("Each item in threshold.json must be an object")

        board_id = item["board_id"]
        channels = item["channel_id"]
        thresholds = item["trg_threshold"]

        if len(channels) != len(thresholds):
            raise ValueError(
                f"threshold.json: board_id={board_id}, "
                f"channel_id length != trg_threshold length"
            )

        for ch, thr in zip(channels, thresholds):
            threshold_patches.append({
                "board_id": board_id,
                "channel_id": ch,
                "trg_threshold": thr
            })

    return threshold_patches


def build_runinfo(runtype, run_id, operator, trigger_style, acq_time, rec_len,
                  outfile_path, outfile_name, daq_config_source,
                  threshold_patches, mapping, dec_info, dec_params, run_comment):
    return {
        "run_info": {
            "runtype": runtype,
            "run_id": run_id,
            "operator": operator,
            "trigger_style": trigger_style,
            "acq_time": acq_time,
            "rec_len": rec_len,
            "outfile_path": outfile_path,
            "outfile_name": outfile_name,
        },
        "daq_config": {
            "source_file": str(daq_config_source),
            "note": "Copied from configure_new.txt to config.cfg during runconfiginfo.py",
        },
        "trigger_logic": {
            "self_trigger": trigger_style == "self",
            "external_trigger": trigger_style == "ext",
            "external_mode": "ACQUISITION_ONLY" if trigger_style == "ext" else "DISABLED",
        },
        "threshold_patches": threshold_patches,
        "mapping": mapping,
        "dec_info": dec_info,
        "dec_params": dec_params,
        "run_comment": run_comment or [],
        "plugins": {},
    }


def write_runinfo_json(runinfo, output_file):
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(runinfo, f, indent=2, ensure_ascii=False)
        f.write("\n")


def main():
    parser = argparse.ArgumentParser(
        description="Generate runinfo.json from fixed configure_new.txt and JSON input files."
    )

    parser.add_argument(
        "--operator",
        required=True,
        help='Operator name, e.g. "JJ Yang"',
    )
    parser.add_argument(
        "--dec_params",
        required=True,
        help="Path to dec_params.json",
    )
    parser.add_argument(
        "--threshold",
        required=True,
        help="Path to threshold.json",
    )
    parser.add_argument(
        "--mapping",
        required=True,
        help="Path to mapping.json",
    )
    parser.add_argument(
        "--run_comment",
        default="[]",
        help='Run comments in JSON array string, e.g. \'["test runinfo"]\'',
    )

    parser.epilog = """
    Example:
        python runconfiginfo.py --operator "JJ Yang" --dec_params dec_params.json --threshold threshold.json --mapping mapping.json --run_comment '["test runinfo"]'
    """

    args = parser.parse_args()

    # Step 1: find latest run directory
    runtype, run_id, run_dir = find_latest_run(TPC_ROOT)

    # Step 2: copy configure_new.txt -> config.cfg
    config_file = copy_config_file(DEFAULT_CONFIGURE_NEW, run_dir)

    # Step 3: parse config.cfg
    cfg = read_config_fields(config_file)
    trigger_style = parse_trigger_style(cfg["SELF_TRIGGER"], cfg["EXTERNAL_TRIGGER"])

    # Step 4: load external JSON files
    dec_params = load_json_file(args.dec_params)
    threshold_data = load_json_file(args.threshold)
    mapping = load_json_file(args.mapping)

    try:
        run_comment = json.loads(args.run_comment)
        if not isinstance(run_comment, list):
            raise ValueError("run_comment must be a JSON array string")
    except Exception as e:
        raise ValueError(f"Invalid --run_comment format: {e}")

    # Step 5: infer dec_info from runtype
    dec_info = infer_dec_info(runtype)

    # Step 6: expand threshold patches
    threshold_patches = expand_threshold_patches(threshold_data)

    # Step 7: build runinfo
    runinfo = build_runinfo(
        runtype=runtype,
        run_id=run_id,
        operator=args.operator,
        trigger_style=trigger_style,
        acq_time=float(cfg["ACQ_TIME"]),
        rec_len=int(cfg["RECORD_LENGTH"]),
        outfile_path=cfg["OUTFILE_PATH"],
        outfile_name=cfg["OUTFILE_NAME"],
        daq_config_source=config_file,
        threshold_patches=threshold_patches,
        mapping=mapping,
        dec_info=dec_info,
        dec_params=dec_params,
        run_comment=run_comment,
    )

    # Step 8: fixed output path
    output_file = run_dir / "runinfo.json"
    write_runinfo_json(runinfo, output_file)
    print(f"runinfo.json generated successfully: {output_file}")


if __name__ == "__main__":
    main()
