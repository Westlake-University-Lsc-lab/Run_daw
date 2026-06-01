# -*- coding: utf-8 -*-
import os
import pty
import sys
import time
import select
import signal
import subprocess
import threading
import traceback

STOP_FLAG = False
DAW_PID = None
DAW_FD = None


def log(msg):
    print(msg)
    sys.stdout.flush()


def get_input():
    try:
        return raw_input()   # Python 2
    except NameError:
        return input()       # Python 3


def input_thread():
    global STOP_FLAG, DAW_FD

    while True:
        try:
            cmd = get_input().strip()
        except EOFError:
            return

        if cmd in ("q", "stop_daq"):
            log("Received '{}', stopping DAQ...".format(cmd))
            STOP_FLAG = True

            if DAW_FD is not None:
                try:
                    os.write(DAW_FD, b"q\n")
                    log("Sent 'q' to DAW_Demo")
                except Exception as e:
                    log("Failed to send q: {}".format(e))
            break

        elif cmd == "s":
            if DAW_FD is not None:
                try:
                    os.write(DAW_FD, b"s\n")
                    log("Sent 's' to DAW_Demo")
                except Exception as e:
                    log("Failed to send s: {}".format(e))


def run_writeconfig(filename):
    cmd = ["python", "writeconfig.py", filename]
    log("[CONFIG] {}".format(" ".join(cmd)))

    ret = subprocess.call(cmd)
    if ret != 0:
        raise RuntimeError("writeconfig.py returned non-zero exit code")


def spawn_daw_demo():
    global DAW_PID, DAW_FD

    pid, fd = pty.fork()

    if pid == 0:
        os.execvp("DAW_Demo", ["DAW_Demo", "configure_new.txt"])
    else:
        DAW_PID = pid
        DAW_FD = fd
        return pid, fd


def try_wait_pid(pid):
    try:
        ended_pid, status = os.waitpid(pid, os.WNOHANG)
        if ended_pid == pid:
            return True, status
    except OSError:
        pass
    return False, None


def stop_daw_demo(pid, fd):
    log("[DAQ] Stopping DAW_Demo...")

    try:
        os.write(fd, b"q\n")
        log("[DAQ] Sent 'q' to DAW_Demo")
    except Exception as e:
        log("[ERROR] Failed to send q: {}".format(e))

    # 等待它自行退出
    for _ in range(10):  # 约 2 秒
        exited, status = try_wait_pid(pid)
        if exited:
            log("[DAQ] DAW_Demo exited with status {}".format(status))
            return
        time.sleep(0.2)

    # 还不退出则温和终止
    try:
        log("[DAQ] DAW_Demo did not exit, sending SIGTERM...")
        os.kill(pid, signal.SIGTERM)
    except Exception as e:
        log("[ERROR] Failed to SIGTERM DAW_Demo: {}".format(e))

    for _ in range(10):
        exited, status = try_wait_pid(pid)
        if exited:
            log("[DAQ] DAW_Demo exited after SIGTERM with status {}".format(status))
            return
        time.sleep(0.2)

    # 最后强杀
    try:
        log("[DAQ] DAW_Demo still alive, sending SIGKILL...")
        os.kill(pid, signal.SIGKILL)
    except Exception as e:
        log("[ERROR] Failed to SIGKILL DAW_Demo: {}".format(e))

    # 再等一下回收
    for _ in range(10):
        exited, status = try_wait_pid(pid)
        if exited:
            log("[DAQ] DAW_Demo exited after SIGKILL with status {}".format(status))
            return
        time.sleep(0.1)

def run_daq():
    global STOP_FLAG, DAW_PID, DAW_FD

    log("[DAQ] Starting DAW_Demo configure_new.txt")
    pid, fd = spawn_daw_demo()

    # 稍等让程序显示提示
    time.sleep(0.5)

    # 自动开始采数
    try:
        os.write(fd, b"s\n")
        log("[DAQ] Auto-sent 's'")
    except Exception as e:
        log("[ERROR] Failed to send 's': {}".format(e))

    normal_finished = False
    last_output_time = time.time()
    no_output_timeout = 15   # 超过15秒无输出，认为busy/卡住，重启

    try:
        while True:
            if STOP_FLAG:
                stop_daw_demo(pid, fd)
                break

            rlist, _, _ = select.select([fd], [], [], 0.2)
            if fd in rlist:
                try:
                    data = os.read(fd, 1024)
                    if not data:
                        log("[DAQ] EOF from DAW_Demo")
                        break

                    try:
                        text = data.decode("utf-8", "ignore")
                    except AttributeError:
                        text = data

                    sys.stdout.write(text)
                    sys.stdout.flush()

                    # 有输出就刷新时间
                    last_output_time = time.time()

                    # 判断正常采数结束
                    if ("Acquisition time (3600 seconds) reached. Stopping..." in text or
                        "ACQ Duration is :3600 s" in text):
                        normal_finished = True
                        log("[DAQ] Normal acquisition finished")
                        break

                except OSError:
                    break

            # 无输出超时，判定 busy / 卡住
            if time.time() - last_output_time > no_output_timeout:
                log("[ERROR] No output for too long, treat as busy and restart")
                stop_daw_demo(pid, fd)
                return False

            exited, status = try_wait_pid(pid)
            if exited:
                if normal_finished:
                    log("\n[DAQ] DAW_Demo exited normally with status {}".format(status))
                else:
                    log("\n[DAQ] DAW_Demo exited unexpectedly with status {}".format(status))
                break

    finally:
        try:
            os.close(fd)
        except Exception:
            pass

        DAW_PID = None
        DAW_FD = None

    return normal_finished


def build_filename(base_name, run_idx):
    return "{}run{}".format(base_name, run_idx)


def main():
    log("auto_daq.py started")

    if len(sys.argv) != 2:
        log("USAGE: python auto_daq.py base_filename")
        sys.exit(1)

    base_filename = sys.argv[1]
    log("Base filename: {}".format(base_filename))

    t = threading.Thread(target=input_thread)
    t.daemon = True
    t.start()

    run_idx = 0
    interval_s =  5*60

    log("Auto DAQ started.")
    log("Type 'q' or 'stop_daq' and press Enter to stop.")
    log("Type 's' and press Enter to send s manually.\n")

    try:
        while not STOP_FLAG:
            current_filename = build_filename(base_filename, run_idx)

            log("=== Cycle {} ===".format(run_idx))
            log("Filename: {}".format(current_filename))

            run_writeconfig(current_filename)

            if STOP_FLAG:
                break

            run_ok = run_daq()
            
            if not run_ok and not STOP_FLAG:
                log("[MAIN] run_daq failed, will retry after short delay")
            
            if not run_ok:
                print('run_ok ... FASLE')
            else:
                continue
            if STOP_FLAG:
                print('STOP_FLAG ... TRUE')
                break
            else:
                continue

            run_idx += 1

            log("[WAIT] waiting {} seconds...".format(interval_s))
            for _ in range(interval_s):
                if STOP_FLAG:
                    break
                time.sleep(1)

    except Exception:
        log("Unhandled exception:")
        traceback.print_exc()

    log("Auto DAQ terminated.")


if __name__ == "__main__":
    main()
