# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import sys
import json
import shutil
import tempfile
from datetime import datetime

DEFAULT_TEMPLATE = "DAW_Config.txt"
OUTPUT_CONFIG = "configure_new.txt"
DEFAULT_RUNTYPE = "run5_Ar"
DEFAULT_TRIGGER_STYLE = "self"
BASE_PATH = "/mnt/data/TPC"


def usage(exit_code=1):
    print("USAGE:")
    print("  python writeconfig.py <runtype> <acq_time> <thresholds.json>")
    print("  python writeconfig.py <runtype> <trigger_style> <acq_time> <thresholds.json>")
    print("")
    print("  trigger_style: ext | self")
    print("  default trigger_style is self")
    print("  rec_len is automatically set:")
    print("    self -> 5")
    print("    ext  -> 25")
    print("")
    print("Examples:")
    print("  python writeconfig.py run5_Ar 60 thresholds.json")
    print("  python writeconfig.py run5_Ar self 60 thresholds.json")
    print("  python writeconfig.py run5_Ar ext 60 thresholds.json")
    sys.exit(exit_code)


def require_int(value, name):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError("{} must be an integer: {}".format(name, value))


def validate_runtype(runtype):
    if not runtype:
        raise ValueError("runtype must not be empty")
    if any(ch.isspace() for ch in runtype):
        raise ValueError("runtype must not contain whitespace: {}".format(runtype))
    return runtype


def validate_trigger_style(trigger_style):
    if trigger_style not in ("ext", "self"):
        raise ValueError("trigger_style must be 'ext' or 'self'")
    return trigger_style

def load_thresholds(thresholds_path):
    if not os.path.exists(thresholds_path):
        raise IOError("thresholds file not found: {}".format(thresholds_path))

    with open(thresholds_path, "r") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("thresholds.json must be a list of objects")

    expanded = []

    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError("thresholds.json item #{} is not an object".format(i))

        for key in ("board_id", "channel_id", "trg_threshold"):
            if key not in item:
                raise ValueError("thresholds.json item #{} missing key: {}".format(i, key))

        board_id = require_int(item["board_id"], "board_id")

        if not isinstance(item["channel_id"], list):
            raise ValueError("thresholds.json item #{} channel_id must be a list".format(i))
        if not isinstance(item["trg_threshold"], list):
            raise ValueError("thresholds.json item #{} trg_threshold must be a list".format(i))

        if len(item["channel_id"]) != len(item["trg_threshold"]):
            raise ValueError(
                "thresholds.json item #{} channel_id and trg_threshold length mismatch".format(i)
            )

        for ch, thr in zip(item["channel_id"], item["trg_threshold"]):
            expanded.append({
                "board_id": board_id,
                "channel_id": require_int(ch, "channel_id"),
                "trg_threshold": require_int(thr, "trg_threshold"),
            })

    return expanded



def parse_args(argv):
    args = argv[1:]

    if len(args) == 3:
        runtype = validate_runtype(args[0])
        trigger_style = DEFAULT_TRIGGER_STYLE
        acq_time = require_int(args[1], "acq_time")
        thresholds_json = args[2]
        return runtype, trigger_style, acq_time, thresholds_json

    if len(args) == 4:
        runtype = validate_runtype(args[0])
        trigger_style = validate_trigger_style(args[1])
        acq_time = require_int(args[2], "acq_time")
        thresholds_json = args[3]
        return runtype, trigger_style, acq_time, thresholds_json

    usage()


def get_rec_len_by_trigger_style(trigger_style):
    if trigger_style == "self":
        return 5
    if trigger_style == "ext":
        return 25
    raise ValueError("trigger_style must be 'ext' or 'self'")


def get_next_run_id(base_path, runtype):
    runtype_dir = os.path.join(base_path, runtype)
    if not os.path.exists(runtype_dir):
        os.makedirs(runtype_dir)

    max_id = 0
    for name in os.listdir(runtype_dir):
        full = os.path.join(runtype_dir, name)
        if os.path.isdir(full) and name.isdigit() and len(name) == 5:
            max_id = max(max_id, int(name))

    return "{:05d}".format(max_id + 1)


def line_key(line):
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    return stripped.split(None, 1)[0]


def format_key_value(original_line, key, value):
    leading = original_line[:len(original_line) - len(original_line.lstrip())]
    newline = "\n" if original_line.endswith("\n") else ""
    return "{}{} {}{}".format(leading, key, value, newline)


def replace_parameters_in_config(para_map, source_config, output_config):
    print("Reading configuration from '{}'.".format(source_config))

    with open(source_config, "r") as file_obj:
        lines = file_obj.readlines()

    new_lines = []
    current_board = None
    current_channel = None

    threshold_map = {
        (x["board_id"], x["channel_id"]): x["trg_threshold"]
        for x in para_map["THRESHOLDS"]
    }
    print("threshold_map keys:", threshold_map.keys())

    found_thresholds = {k: False for k in threshold_map.keys()}

    for line in lines:
        stripped = line.strip()
    
        #print("LINE:", repr(line))
        #print("CURRENT BOARD:", current_board, "CURRENT CHANNEL:", current_channel)
        
        if stripped.startswith("[BOARD]"):
            parts = stripped.split()
            current_board = int(parts[1]) if len(parts) >= 2 and parts[1].isdigit() else None
            current_channel = None
            new_lines.append(line)
            continue

        if stripped.startswith("[CHANNEL]"):
            parts = stripped.split()
            current_channel = int(parts[1]) if len(parts) >= 2 and parts[1].isdigit() else None
            new_lines.append(line)
            continue

        key = line_key(line)
        if key is None:
            new_lines.append(line)
            continue

        replacement_value = None

        if key == "OUTFILE_PATH":
            replacement_value = para_map["OUTFILE_PATH"]
        elif key == "OUTFILE_NAME":
            replacement_value = para_map["OUTFILE_NAME"]
        elif key == "RECORD_LENGTH":
            replacement_value = para_map["RECORD_LENGTH"]
        elif key == "ACQ_TIME":
            replacement_value = para_map["ACQ_TIME"]
        elif key == "EXTERNAL_TRIGGER":
            replacement_value = para_map["EXTERNAL_TRIGGER"]
        elif key == "SELF_TRIGGER":
            replacement_value = para_map["SELF_TRIGGER"]
        elif key == "TRG_THRESHOLD":
            if current_board is not None and current_channel is not None:
                pair = (current_board, current_channel)
                if pair in threshold_map:
                    replacement_value = threshold_map[pair]
                    found_thresholds[pair] = True

        if replacement_value is None:
            new_lines.append(line)
            continue

        new_line = format_key_value(line, key, replacement_value)
        new_lines.append(new_line)
        print("writing >>>> {}".format(new_line.strip()))

    missing = [k for k, ok in found_thresholds.items() if not ok]
    if missing:
        msg = ", ".join([
            "(board_id={}, channel_id={})".format(b, c)
            for (b, c) in missing
        ])
        raise RuntimeError("Threshold target not found in config: {}".format(msg))

    output_dir = os.path.dirname(os.path.abspath(output_config)) or "."
    fd, tmp_path = tempfile.mkstemp(prefix=".configure_new.", suffix=".tmp", dir=output_dir)
    try:
        with os.fdopen(fd, "w") as tmp_obj:
            tmp_obj.writelines(new_lines)
        shutil.move(tmp_path, output_config)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    print("New configuration file has been written to '{}'.".format(output_config))


def main():
    try:
        runtype, trigger_style, acq_time, thresholds_json = parse_args(sys.argv)
        thresholds = load_thresholds(thresholds_json)

        rec_len = get_rec_len_by_trigger_style(trigger_style)

        if trigger_style == "self":
            external_trigger = "DISABLED"
            self_trigger = "YES"
        else:
            external_trigger = "ACQUISITION_ONLY"
            self_trigger = "NO"

        starttime = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_id = get_next_run_id(BASE_PATH, runtype)

        run_dir = os.path.join(BASE_PATH, runtype, run_id)
        raw_dir = os.path.join(run_dir, "RAW")
        if not os.path.exists(raw_dir):
            os.makedirs(raw_dir)

        outfile_name = "{}_{}_{}".format(runtype, starttime, run_id)
        outfile_path = raw_dir + "/"

        para_map = {
            "OUTFILE_PATH": outfile_path,
            "OUTFILE_NAME": outfile_name,
            "RECORD_LENGTH": rec_len,
            "ACQ_TIME": acq_time,
            "EXTERNAL_TRIGGER": external_trigger,
            "SELF_TRIGGER": self_trigger,
            "THRESHOLDS": thresholds,
        }

        if not os.path.exists(DEFAULT_TEMPLATE):
            raise IOError("Template file not found: {}".format(DEFAULT_TEMPLATE))

        replace_parameters_in_config(para_map, DEFAULT_TEMPLATE, OUTPUT_CONFIG)

        print("[OK] runtype        = {}".format(runtype))
        print("[OK] trigger_style  = {}".format(trigger_style))
        print("[OK] rec_len        = {}".format(rec_len))
        print("[OK] acq_time       = {}".format(acq_time))
        print("[OK] starttime      = {}".format(starttime))
        print("[OK] run_id         = {}".format(run_id))
        print("[OK] outfile_name   = {}".format(outfile_name))
        print("[OK] config saved    = {}".format(OUTPUT_CONFIG))

    except Exception as exc:
        print("[ERROR] {}".format(exc))
        usage()


if __name__ == "__main__":
    main()
