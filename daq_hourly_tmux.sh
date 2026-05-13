#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKDIR="${DAQ_WORKDIR:-${SCRIPT_DIR}}"
SESSION="${DAQ_SESSION:-daq_hourly}"
STATE_DIR="${WORKDIR}/.daq_hourly_state"
LOG_FILE="${STATE_DIR}/controller.log"
CONFIG_FILE="${DAQ_CONFIG_FILE:-configure_new.txt}"
DAW_PROGRAM="${DAQ_PROGRAM:-DAW_Demo}"
DEFAULT_BASE="pmt7_3kVcm_200Vcm_b0_chs_thr_longtime"

mkdir -p "${STATE_DIR}"

log() {
  mkdir -p "${STATE_DIR}"
  printf '[%s] %s\n' "$(date '+%F %T')" "$*" | tee -a "${LOG_FILE}"
}

usage() {
  cat <<USAGE
USAGE:
  ./daq_hourly_tmux.sh start [base_name] [start_run]
  ./daq_hourly_tmux.sh stop
  ./daq_hourly_tmux.sh status
  ./daq_hourly_tmux.sh attach
  ./daq_hourly_tmux.sh controller

ENV:
  DAQ_WORKDIR       DAQ working directory, default: this script directory
  DAQ_SESSION       tmux session name, default: daq_hourly
  DAQ_ACQ_TIME      seconds per file, default: 3600
  DAQ_GAP_SECONDS   seconds between runs, default: 5
  DAQ_PROGRAM       DAQ command, default: DAW_Demo
USAGE
}

update_config() {
  local outfile="$1"
  local acq_time="$2"

  cd "${WORKDIR}"
  python - "${CONFIG_FILE}" "${outfile}" "${acq_time}" <<'PY'
from __future__ import print_function
import os
import shutil
import sys
import tempfile

config_path, outfile, acq_time = sys.argv[1], sys.argv[2], sys.argv[3]
backup_path = config_path + ".hourly_backup"

if not os.path.exists(config_path):
    raise SystemExit("missing config file: {}".format(config_path))

if not os.path.exists(backup_path):
    shutil.copy2(config_path, backup_path)

with open(config_path, "r") as f:
    lines = f.readlines()

changed_name = False
changed_time = False
new_lines = []

for line in lines:
    stripped = line.strip()
    if stripped and not stripped.startswith("#"):
        key = stripped.split(None, 1)[0]
        leading = line[:len(line) - len(line.lstrip())]
        if key == "OUTFILE_NAME":
            new_lines.append("{}OUTFILE_NAME {}\n".format(leading, outfile))
            changed_name = True
            continue
        if key == "ACQ_TIME":
            new_lines.append("{}ACQ_TIME {}\n".format(leading, acq_time))
            changed_time = True
            continue
    new_lines.append(line)

if not changed_name:
    raise SystemExit("OUTFILE_NAME not found in {}".format(config_path))
if not changed_time:
    raise SystemExit("ACQ_TIME not found in {}".format(config_path))

fd, tmp_path = tempfile.mkstemp(prefix=".configure_hourly.", suffix=".tmp", dir=".")
try:
    with os.fdopen(fd, "w") as f:
        f.writelines(new_lines)
    shutil.move(tmp_path, config_path)
finally:
    if os.path.exists(tmp_path):
        os.remove(tmp_path)

print("OUTFILE_NAME {}".format(outfile))
print("ACQ_TIME {}".format(acq_time))
PY
}

pane_pid() {
  tmux display-message -p -t "${DAQ_WORKER_PANE}" '#{pane_pid}'
}

daw_pid_for_worker() {
  local shell_pid
  shell_pid="$(pane_pid)"
  ps --ppid "${shell_pid}" -o pid=,comm= | awk '$2 == "DAW_Demo" {print $1; exit}'
}

wait_for_daw_start() {
  local timeout_s="${1:-20}"
  local pid=""
  for _ in $(seq 1 "${timeout_s}"); do
    pid="$(daw_pid_for_worker || true)"
    if [ -n "${pid}" ]; then
      echo "${pid}"
      return 0
    fi
    sleep 1
  done
  return 1
}

controller() {
  cd "${WORKDIR}"

  local base_name="${DAQ_BASE_NAME:-${DEFAULT_BASE}}"
  local run_idx="${DAQ_START_RUN:-0}"
  local acq_time="${DAQ_ACQ_TIME:-3600}"
  local gap_seconds="${DAQ_GAP_SECONDS:-5}"
  local grace_seconds="${DAQ_GRACE_SECONDS:-180}"
  local stop_file="${STATE_DIR}/stop"

  rm -f "${stop_file}"
  log "controller started: session=${SESSION}, worker=${DAQ_WORKER_PANE}, base=${base_name}, start_run=${run_idx}, acq_time=${acq_time}"

  while [ ! -f "${stop_file}" ]; do
    local outfile="${base_name}run${run_idx}"
    log "preparing run ${run_idx}: ${outfile}"
    update_config "${outfile}" "${acq_time}" >> "${LOG_FILE}" 2>&1

    tmux send-keys -t "${DAQ_WORKER_PANE}" "cd ${WORKDIR}" Enter
    tmux send-keys -t "${DAQ_WORKER_PANE}" "${DAW_PROGRAM} ${CONFIG_FILE}" Enter
    sleep 2
    tmux send-keys -t "${DAQ_WORKER_PANE}" s

    local pid=""
    if ! pid="$(wait_for_daw_start 20)"; then
      log "ERROR: DAW_Demo did not start for run ${run_idx}"
      run_idx=$((run_idx + 1))
      sleep "${gap_seconds}"
      continue
    fi

    log "run ${run_idx} started: pid=${pid}"

    local deadline=$(( $(date +%s) + acq_time + grace_seconds ))
    while kill -0 "${pid}" 2>/dev/null; do
      if [ -f "${stop_file}" ]; then
        log "stop requested; sending q to DAW_Demo pid=${pid}"
        tmux send-keys -t "${DAQ_WORKER_PANE}" q
        break
      fi
      if [ "$(date +%s)" -gt "${deadline}" ]; then
        log "run ${run_idx} exceeded ${acq_time}+${grace_seconds}s; sending q"
        tmux send-keys -t "${DAQ_WORKER_PANE}" q
        break
      fi
      sleep 2
    done

    while kill -0 "${pid}" 2>/dev/null; do
      sleep 1
    done

    log "run ${run_idx} finished"
    run_idx=$((run_idx + 1))

    if [ -f "${stop_file}" ]; then
      break
    fi
    sleep "${gap_seconds}"
  done

  log "controller stopped"
}

start() {
  local base_name="${1:-${DEFAULT_BASE}}"
  local start_run="${2:-0}"

  cd "${WORKDIR}"

  if tmux has-session -t "${SESSION}" 2>/dev/null; then
    echo "tmux session '${SESSION}' already exists."
    echo "Use './daq_hourly_tmux.sh status', './daq_hourly_tmux.sh attach', or './daq_hourly_tmux.sh stop'."
    exit 1
  fi

  rm -f "${STATE_DIR}/stop"
  : > "${LOG_FILE}"

  local worker_pane
  worker_pane="$(tmux new-session -d -s "${SESSION}" -n run -P -F '#{pane_id}' "cd ${WORKDIR}; exec bash -i")"

  tmux set-environment -t "${SESSION}" DAQ_WORKDIR "${WORKDIR}"
  tmux set-environment -t "${SESSION}" DAQ_SESSION "${SESSION}"
  tmux set-environment -t "${SESSION}" DAQ_WORKER_PANE "${worker_pane}"
  tmux set-environment -t "${SESSION}" DAQ_BASE_NAME "${base_name}"
  tmux set-environment -t "${SESSION}" DAQ_START_RUN "${start_run}"
  tmux set-environment -t "${SESSION}" DAQ_ACQ_TIME "${DAQ_ACQ_TIME:-3600}"
  tmux set-environment -t "${SESSION}" DAQ_GAP_SECONDS "${DAQ_GAP_SECONDS:-5}"
  tmux set-environment -t "${SESSION}" DAQ_PROGRAM "${DAW_PROGRAM}"

  tmux new-window -d -t "${SESSION}" -n control "cd ${WORKDIR}; exec bash ./daq_hourly_tmux.sh controller"

  echo "Started tmux session '${SESSION}'."
  echo "Attach: tmux attach -t ${SESSION}"
  echo "Status: ./daq_hourly_tmux.sh status"
  echo "Stop:   ./daq_hourly_tmux.sh stop"
}

stop() {
  touch "${STATE_DIR}/stop"
  if tmux has-session -t "${SESSION}" 2>/dev/null; then
    local worker
    worker="$(tmux show-environment -t "${SESSION}" DAQ_WORKER_PANE 2>/dev/null | sed 's/^DAQ_WORKER_PANE=//')"
    if [ -n "${worker}" ]; then
      tmux send-keys -t "${worker}" q 2>/dev/null || true
    fi
    echo "Stop requested for '${SESSION}'."
  else
    echo "tmux session '${SESSION}' is not running."
  fi
}

status() {
  if tmux has-session -t "${SESSION}" 2>/dev/null; then
    echo "tmux session '${SESSION}' is running."
    echo "--- controller log ---"
    tail -n 30 "${LOG_FILE}" 2>/dev/null || true
    echo "--- DAQ pane ---"
    local worker
    worker="$(tmux show-environment -t "${SESSION}" DAQ_WORKER_PANE 2>/dev/null | sed 's/^DAQ_WORKER_PANE=//')"
    if [ -n "${worker}" ]; then
      tmux capture-pane -pt "${worker}" -S -80
    fi
  else
    echo "tmux session '${SESSION}' is not running."
    tail -n 30 "${LOG_FILE}" 2>/dev/null || true
  fi
}

case "${1:-}" in
  start)
    shift
    start "$@"
    ;;
  stop)
    stop
    ;;
  status)
    status
    ;;
  attach)
    exec tmux attach -t "${SESSION}"
    ;;
  controller)
    controller
    ;;
  *)
    usage
    exit 1
    ;;
esac
