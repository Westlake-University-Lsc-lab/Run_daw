#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from tpc_runindex import iter_runinfo_paths, load_json, extract_fields_and_validate

BASE_DIR = Path("/mnt/data/TPC")
DB_DIR = BASE_DIR / "database"
DB_PATH = DB_DIR / "rundatabase.db"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def ensure_db():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            runtype TEXT NOT NULL,
            runinfo_path TEXT NOT NULL,
            trigger_mode TEXT,
            outfile_path TEXT,
            outfile_name TEXT,
            run_tag TEXT,
            run_comment TEXT,
            acq_time REAL,
            file_mtime REAL,
            raw_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_runtype ON runs(runtype)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_outfile_name ON runs(outfile_name)")
    conn.commit()
    return conn


def discover_runtypes(base_dir: Path):
    for p in sorted(base_dir.iterdir()):
        if not p.is_dir():
            continue
        if p.name == "database":
            continue
        yield p.name


def upsert_run(conn, runtype: str, runinfo_path: Path, info: dict):
    row = extract_fields_and_validate(runinfo_path.parent.name, info)
    stat = runinfo_path.stat()
    now = utc_now()

    conn.execute("""
        INSERT INTO runs (
            run_id, runtype, runinfo_path, trigger_mode, outfile_path, outfile_name,
            run_tag, run_comment, acq_time, file_mtime, raw_json, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(run_id) DO UPDATE SET
            runtype=excluded.runtype,
            runinfo_path=excluded.runinfo_path,
            trigger_mode=excluded.trigger_mode,
            outfile_path=excluded.outfile_path,
            outfile_name=excluded.outfile_name,
            run_tag=excluded.run_tag,
            run_comment=excluded.run_comment,
            acq_time=excluded.acq_time,
            file_mtime=excluded.file_mtime,
            raw_json=excluded.raw_json,
            updated_at=excluded.updated_at
        WHERE excluded.file_mtime > runs.file_mtime
    """, (
        row["run_id"],
        runtype,
        str(runinfo_path),
        row["trigger_mode"],
        row["outfile_path"],
        row["outfile_name"],
        row["run_tag"],
        row["run_comment"],
        float(row["acq_time"]) if row["acq_time"] not in ("", None) else None,
        stat.st_mtime,
        json.dumps(info, ensure_ascii=False),
        now,
        now,
    ))


def sync_once():
    conn = ensure_db()
    inserted_or_updated = 0

    try:
        for runtype in discover_runtypes(BASE_DIR):
            try:
                for meta in iter_runinfo_paths(BASE_DIR, runtype):
                    info = load_json(meta["runinfo_path"])
                    if info is None:
                        logging.error("skip invalid json: %s", meta["runinfo_path"])
                        continue
                    try:
                        upsert_run(conn, runtype, meta["runinfo_path"], info)
                        inserted_or_updated += 1
                    except Exception as e:
                        logging.error("failed to ingest %s: %s", meta["runinfo_path"], e)
                        continue
            except FileNotFoundError:
                continue

        conn.commit()
        logging.info("sync complete, processed=%d", inserted_or_updated)
    finally:
        conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
    sync_once()
