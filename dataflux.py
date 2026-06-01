#!/home/siin/miniconda3/bin/python3
# -*- coding: utf-8 -*-
import os
import time
import threading
import pymysql
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ---------------- MySQL 配置 ----------------
db_config = {
    'host': '192.168.4.19',
    'user': 'daq_user',
    'password': 'westlakeE4111',
    'database': 'slowcontroldata',
    'port': 3306,
    'charset': 'utf8mb4',
    'autocommit': True
}

# ---------------- 监控配置 ----------------
FOLDER_PATH = "/mnt/data/TPC/"
EXTS = (".CSV", ".bin")
FLOW_THRESHOLD_MB = 10       # 高速流量立即写入阈值 MB/s
LOW_SPEED_INTERVAL = 30       # 低速平均写入间隔 秒
IDLE_TIME_LIMIT = 3600        # 1小时无变化退出 秒
CHECK_INTERVAL = 1            # 流量检测间隔 秒

# ---------------- 文件事件处理 ----------------
class IncrementalMonitorHandler(FileSystemEventHandler):
    def __init__(self):
        self.file_sizes = {}
        self.delta_bytes = 0
        self.lock = threading.Lock()
        self.first_scan_done = False
        self.last_write_time = time.time()
        self.last_activity_time = time.time()

        # 初始化已有文件，但不计入 delta
        for root, _, files in os.walk(FOLDER_PATH):
            for f in files:
                if f.endswith(EXTS):
                    path = os.path.join(root, f)
                    self.file_sizes[path] = os.path.getsize(path)
        self.first_scan_done = True
        print(f"Initialized {len(self.file_sizes)} existing files, first scan done.")

    def update_file(self, path):
        if not path.endswith(EXTS) or not os.path.isfile(path):
            return
        size = os.path.getsize(path)
        with self.lock:
            prev_size = self.file_sizes.get(path, 0)
            added = max(size - prev_size, 0)
            self.delta_bytes += added
            self.file_sizes[path] = size
            if added > 0:
                self.last_activity_time = time.time()

    def remove_file(self, path):
        with self.lock:
            if path in self.file_sizes:
                del self.file_sizes[path]

    def on_created(self, event):
        self.update_file(event.src_path)

    def on_modified(self, event):
        self.update_file(event.src_path)

    def on_deleted(self, event):
        self.remove_file(event.src_path)

    def get_and_reset_delta(self):
        with self.lock:
            delta = self.delta_bytes
            self.delta_bytes = 0
            return delta

# ---------------- MySQL 写入 ----------------
def write_to_mysql(rate):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            query = "INSERT INTO DAQdata (timestamp, data_rate) VALUES (%s, %s)"
            cursor.execute(query, (timestamp, rate))
        print(f"[{timestamp}] Logged rate: {rate:.2f} MB/s")
    except pymysql.MySQLError as e:
        print(f"MySQL error: {e}")
    finally:
        if connection:
            connection.close()

# ---------------- 流量计算线程 ----------------
class MonitorThread(threading.Thread):
    def __init__(self, handler: IncrementalMonitorHandler):
        super().__init__()
        self.handler = handler
        self.running = True

    def run(self):
        low_speed_accum = 0.0
        low_speed_count = 0
        while self.running:
            time.sleep(CHECK_INTERVAL)
            delta = self.handler.get_and_reset_delta()
            rate_mb = delta / 1e6 / CHECK_INTERVAL  # MB/s
            now = time.time()

            # 超过1小时无写入退出
            if now - self.handler.last_activity_time >= IDLE_TIME_LIMIT:
                print("No activity for 1 hour. Exiting.")
                os._exit(0)

            if rate_mb >= FLOW_THRESHOLD_MB:
                # 高速立即写入
                write_to_mysql(rate_mb)
                low_speed_accum = 0
                low_speed_count = 0
                self.handler.last_write_time = now
            else:
                # 低速累积，包括零流量
                low_speed_accum += rate_mb
                low_speed_count += 1
                if now - self.handler.last_write_time >= LOW_SPEED_INTERVAL:
                    avg_rate = low_speed_accum / max(low_speed_count, 1)
                    write_to_mysql(avg_rate)
                    low_speed_accum = 0
                    low_speed_count = 0
                    self.handler.last_write_time = now

    def stop(self):
        self.running = False

# ---------------- 主程序 ----------------
if __name__ == "__main__":
    event_handler = IncrementalMonitorHandler()
    observer = Observer()
    observer.schedule(event_handler, path=FOLDER_PATH, recursive=True)
    observer.start()
    print(f"Monitoring folder: {FOLDER_PATH} for {EXTS} files...")

    monitor_thread = MonitorThread(event_handler)
    monitor_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping monitor...")
        monitor_thread.stop()
        observer.stop()
    monitor_thread.join()
    observer.join()
    print("Exited cleanly.")
