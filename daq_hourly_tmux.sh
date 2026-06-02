#!/usr/bin/env bash
set -euo pipefail

WORKDIR="${DAQ_WORKDIR:-/home/daq/DAQ_DEMO}"
SESSION="${DAQ_SESSION:-daq_hourly}"
STATE_DIR="${WORKDIR}/.daq_hourly_state"
LOG_FILE="${STATE_DIR}/controller.log"
WRITECONFIG_LOG_FILE="${STATE_DIR}/writeconfig.log"
RUNCONFIGINFO_LOG_FILE="${STATE_DIR}/runconfiginfo.log"

DAW_PROGRAM="${DAQ_PROGRAM:-DAW_Demo}"
CONFIG_FILE="${DAQ_CONFIG_FILE:-configure_new.txt}"

# dataflux monitor
DATAFLUX_ENABLE="${DATAFLUX_ENABLE:-1}"      # 1=启用, 0=关闭
DATAFLUX_CMD="${DATAFLUX_CMD:-python3 dataflux.py}"
DATAFLUX_PID_FILE="${STATE_DIR}/dataflux.pid"
DATAFLUX_LOG_FILE="${STATE_DIR}/dataflux.log"

# writeconfig.py 参数（除采集时长外其余固定）
WRITECONFIG_RUNTYPE="${WRITECONFIG_RUNTYPE:-run6_Xe}"
WRITECONFIG_TRIGGER="${WRITECONFIG_TRIGGER:-self}"
WRITECONFIG_THRESHOLDS="${WRITECONFIG_THRESHOLDS:-./thresholds.json}"

# 采集时长（秒）-> writeconfig.py 第三个参数
DAQ_ACQ_TIME="${DAQ_ACQ_TIME:-60}"

# runconfiginfo.py 参数
RUNINFO_OPERATOR="${RUNINFO_OPERATOR:-JJ Yang}"
RUNINFO_DEC_PARAMS="${RUNINFO_DEC_PARAMS:-dec_params.json}"
RUNINFO_THRESHOLD="${RUNINFO_THRESHOLD:-thresholds.json}"
RUNINFO_MAPPING="${RUNINFO_MAPPING:-mapping.json}"
RUNINFO_COMMENT="${RUNINFO_COMMENT:-[\"tuning trigger threshold\"]}"
RUNINFO_RUN_TAG="${RUNINFO_RUN_TAG:-TPC_Xe Run}"

mkdir -p "${STATE_DIR}"

log() {
  mkdir -p "${STATE_DIR}"
  printf '[%s] %s\n' "$(date '+%F %T')" "$*" | tee -a "${LOG_FILE}"
}

usage() {
  cat <<USAGE
USAGE:
  ./daq_hourly_tmux.sh start
  ./daq_hourly_tmux.sh stop
  ./daq_hourly_tmux.sh status
  ./daq_hourly_tmux.sh attach
  ./daq_hourly_tmux.sh controller

ENV:
  DAQ_WORKDIR        working directory, default: /home/daq/DAQ_DEMO
  DAQ_SESSION        tmux session name, default: daq_hourly
  DAQ_ACQ_TIME       acquisition time (seconds) for writeconfig.py, default: 300
  DAQ_GAP_SECONDS    seconds between runs, default: 5
  DAQ_GRACE_SECONDS  extra timeout after acq_time, default: 180
  DAQ_PROGRAM        DAQ command, default: DAW_Demo
  DAQ_CONFIG_FILE    config for DAW_Demo, default: configure_nw.txt

  WRITECONFIG_RUNTYPE     default: run6_Xe
  WRITECONFIG_TRIGGER     default: self
  WRITECONFIG_THRESHOLDS  default: ./thresholds.json

  RUNINFO_OPERATOR   default: JJ Yang
  RUNINFO_DEC_PARAMS default: dec_params.json
  RUNINFO_THRESHOLD  default: thresholds.json
  RUNINFO_MAPPING    default: mapping.json
  RUNINFO_COMMENT    JSON-like string list, default: ["tuning trigger threshold"]
USAGE
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

start_dataflux() {
  [ "${DATAFLUX_ENABLE}" = "1" ] || return 0

  # 清理旧pid
  if [ -f "${DATAFLUX_PID_FILE}" ]; then
    local oldpid
    oldpid="$(cat "${DATAFLUX_PID_FILE}" 2>/dev/null || true)"
    if [ -n "${oldpid}" ] && kill -0 "${oldpid}" 2>/dev/null; then
      log "dataflux already running: pid=${oldpid}"
      return 0
    fi
    rm -f "${DATAFLUX_PID_FILE}"
  fi

  # 后台启动
  (
    #nohup bash -lc "cd '${WORKDIR}'; exec ${DATAFLUX_CMD}" >> "${DATAFLUX_LOG_FILE}" 2>&1 &
    nohup ${DATAFLUX_CMD} >> "${DATAFLUX_LOG_FILE}" 2>&1 &
    echo $! > "${DATAFLUX_PID_FILE}"
  )
  sleep 0.5

  local pid=""
  pid="$(cat "${DATAFLUX_PID_FILE}" 2>/dev/null || true)"
  if [ -n "${pid}" ] && kill -0 "${pid}" 2>/dev/null; then
    # 注意：不打印 cmd，避免出现启动参数
    log "dataflux started: pid=${pid}"
  else
    log "WARNING: failed to start dataflux"
    rm -f "${DATAFLUX_PID_FILE}"
  fi
}

stop_dataflux() {
  [ "${DATAFLUX_ENABLE}" = "1" ] || return 0

  [ -f "${DATAFLUX_PID_FILE}" ] || return 0

  local pid=""
  pid="$(cat "${DATAFLUX_PID_FILE}" 2>/dev/null || true)"
  if [ -n "${pid}" ] && kill -0 "${pid}" 2>/dev/null; then
    log "stopping dataflux pid=${pid}"
    kill "${pid}" 2>/dev/null || true
    sleep 1
    if kill -0 "${pid}" 2>/dev/null; then
      kill -9 "${pid}" 2>/dev/null || true
    fi
  fi
  rm -f "${DATAFLUX_PID_FILE}"
}


controller() {
  cd "${WORKDIR}"

  local acq_time="${DAQ_ACQ_TIME:-300}"
  local gap_seconds="${DAQ_GAP_SECONDS:-5}"
  local grace_seconds="${DAQ_GRACE_SECONDS:-180}"
  local stop_file="${STATE_DIR}/stop"

  rm -f "${stop_file}"
  log "controller started: session=${SESSION}, worker=${DAQ_WORKER_PANE}, acq_time=${acq_time}"

  while [ ! -f "${stop_file}" ]; do
    tmux send-keys -t "${DAQ_WORKER_PANE}" "cd ${WORKDIR}" Enter

    log "step1: python3 writeconfig.py ${WRITECONFIG_RUNTYPE} ${WRITECONFIG_TRIGGER} ${acq_time} ${WRITECONFIG_THRESHOLDS}"
    tmux send-keys -t "${DAQ_WORKER_PANE}" \
      "cd ${WORKDIR} && python3 writeconfig.py ${WRITECONFIG_RUNTYPE} ${WRITECONFIG_TRIGGER} ${acq_time} ${WRITECONFIG_THRESHOLDS} >> '${WRITECONFIG_LOG_FILE}' 2>&1" Enter

    sleep 5

    log "step2: python3 runconfiginfo.py --operator \"${RUNINFO_OPERATOR}\" --dec_params ${RUNINFO_DEC_PARAMS} --threshold ${RUNINFO_THRESHOLD} --mapping ${RUNINFO_MAPPING} --run_comment '${RUNINFO_COMMENT}' --run_tag \"${RUNINFO_RUN_TAG}\" "
    tmux send-keys -t "${DAQ_WORKER_PANE}" \
      "cd ${WORKDIR} && python3 runconfiginfo.py --operator \"${RUNINFO_OPERATOR}\" --dec_params ${RUNINFO_DEC_PARAMS} --threshold ${RUNINFO_THRESHOLD} --mapping ${RUNINFO_MAPPING} --run_comment '${RUNINFO_COMMENT}' --run_tag \"${RUNINFO_RUN_TAG}\" >> '${RUNCONFIGINFO_LOG_FILE}' 2>&1" Enter

    # 再停顿 5 秒，确保第二步执行后再启动 DAW
    sleep 5

    log "step3: ${DAW_PROGRAM} ${CONFIG_FILE}"
    tmux send-keys -t "${DAQ_WORKER_PANE}" "${DAW_PROGRAM} ${CONFIG_FILE}" Enter
    sleep 2
    tmux send-keys -t "${DAQ_WORKER_PANE}" s

    local pid=""
    if ! pid="$(wait_for_daw_start 20)"; then
      log "ERROR: DAW_Demo did not start"
      sleep "${gap_seconds}"
      continue
    fi

    log "run started: pid=${pid}"

    start_dataflux

    local deadline=$(( $(date +%s) + acq_time + grace_seconds ))
    while kill -0 "${pid}" 2>/dev/null; do
      if [ -f "${stop_file}" ]; then
        log "stop requested; sending q to DAW_Demo pid=${pid}"
        tmux send-keys -t "${DAQ_WORKER_PANE}" q
        break
      fi
      if [ "$(date +%s)" -gt "${deadline}" ]; then
        log "run exceeded ${acq_time}+${grace_seconds}s; sending q"
        tmux send-keys -t "${DAQ_WORKER_PANE}" q
        break
      fi
      sleep 2
    done

    while kill -0 "${pid}" 2>/dev/null; do
      sleep 1
    done

    stop_dataflux

    log "run finished"

    if [ -f "${stop_file}" ]; then
      break
    fi
    sleep "${gap_seconds}"
  done

  log "controller stopped"
}

start() {
  cd "${WORKDIR}"

  if tmux has-session -t "${SESSION}" 2>/dev/null; then
    echo "tmux session '${SESSION}' already exists."
    echo "Use './daq_hourly_tmux.sh status', './daq_hourly_tmux.sh attach', or './daq_hourly_tmux.sh stop'."
    exit 1
  fi

  rm -f "${STATE_DIR}/stop"
  : > "${LOG_FILE}"
  : > "${WRITECONFIG_LOG_FILE}"
  : > "${RUNCONFIGINFO_LOG_FILE}"


  local worker_pane
  worker_pane="$(tmux new-session -d -s "${SESSION}" -n run -P -F '#{pane_id}' "cd ${WORKDIR}; exec bash -i")"

  tmux set-environment -t "${SESSION}" DAQ_WORKDIR "${WORKDIR}"
  tmux set-environment -t "${SESSION}" DAQ_SESSION "${SESSION}"
  tmux set-environment -t "${SESSION}" DAQ_WORKER_PANE "${worker_pane}"
  tmux set-environment -t "${SESSION}" DAQ_ACQ_TIME "${DAQ_ACQ_TIME:-300}"
  tmux set-environment -t "${SESSION}" DAQ_GAP_SECONDS "${DAQ_GAP_SECONDS:-5}"
  tmux set-environment -t "${SESSION}" DAQ_GRACE_SECONDS "${DAQ_GRACE_SECONDS:-180}"
  tmux set-environment -t "${SESSION}" DAQ_PROGRAM "${DAW_PROGRAM}"
  tmux set-environment -t "${SESSION}" DAQ_CONFIG_FILE "${CONFIG_FILE}"

  tmux set-environment -t "${SESSION}" WRITECONFIG_RUNTYPE "${WRITECONFIG_RUNTYPE}"
  tmux set-environment -t "${SESSION}" WRITECONFIG_TRIGGER "${WRITECONFIG_TRIGGER}"
  tmux set-environment -t "${SESSION}" WRITECONFIG_THRESHOLDS "${WRITECONFIG_THRESHOLDS}"

  tmux set-environment -t "${SESSION}" RUNINFO_OPERATOR "${RUNINFO_OPERATOR}"
  tmux set-environment -t "${SESSION}" RUNINFO_DEC_PARAMS "${RUNINFO_DEC_PARAMS}"
  tmux set-environment -t "${SESSION}" RUNINFO_THRESHOLD "${RUNINFO_THRESHOLD}"
  tmux set-environment -t "${SESSION}" RUNINFO_MAPPING "${RUNINFO_MAPPING}"
  tmux set-environment -t "${SESSION}" RUNINFO_COMMENT "${RUNINFO_COMMENT}"
  tmux set-environment -t "${SESSION}" RUNINFO_RUN_TAG "${RUNINFO_RUN_TAG}"

  tmux set-environment -t "${SESSION}" DATAFLUX_ENABLE "${DATAFLUX_ENABLE}"
  tmux set-environment -t "${SESSION}" DATAFLUX_CMD "${DATAFLUX_CMD}"
  tmux set-environment -t "${SESSION}" DATAFLUX_PID_FILE "${DATAFLUX_PID_FILE}"
  tmux set-environment -t "${SESSION}" DATAFLUX_LOG_FILE "${DATAFLUX_LOG_FILE}"

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

    # 停dataflux
    stop_dataflux || true

    sleep 1
    tmux kill-session -t "${SESSION}" 2>/dev/null || true
    echo "Stopped and closed tmux session '${SESSION}'."
  else
    stop_dataflux || true
    echo "tmux session '${SESSION}' is not running."
  fi
}

status() {
  if tmux has-session -t "${SESSION}" 2>/dev/null; then
    echo "tmux session '${SESSION}' is running."
    echo "--- controller log ---"
    tail -n 30 "${LOG_FILE}" 2>/dev/null || true

    echo "--- writeconfig log ---"
    tail -n 30 "${WRITECONFIG_LOG_FILE}" 2>/dev/null || true
    echo "--- runconfiginfo log ---"
    tail -n 30 "${RUNCONFIGINFO_LOG_FILE}" 2>/dev/null || true

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
    start
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
