import os
import subprocess
import multiprocessing
import time
from datetime import datetime
import signal
import shutil

from database import SessionLocal, init_db
from models import EcoflocResult

# --- CONFIG --- #
RESOURCES = os.getenv("ECO_RESOURCES", "cpu,ram").split(",")
INTERVAL_MS = int(os.getenv("ECO_INTERVAL_MS", 1000))
DURATION_S = int(os.getenv("ECO_DURATION_S", 5))
MAX_PIDS = int(os.getenv("ECO_MAX_PIDS", 10))
OUTPUT_DIR = os.getenv("ECO_OUTPUT_DIR", "./ecofloc_results")

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

base_log = os.path.join(OUTPUT_DIR, f'top1_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
LOG_FILE = base_log + ".log"
counter = 1
while os.path.exists(LOG_FILE):
    LOG_FILE = f"{base_log}_{counter}.log"
    counter += 1

def get_active_pids():
    try:
        pid_output = subprocess.check_output(
            ['ps', '-u', os.getenv('USER'), '-o', 'pid=', '--sort=-%cpu', '--no-heading'],
            text=True)
        return pid_output.splitlines()[:MAX_PIDS]
    except Exception as e:
        print(f"[ERROR] Failed to get PIDs: {e}")
        return []

def get_process_name(pid):
    try:
        with open(f'/proc/{pid}/comm', 'r') as f:
            return f.read().strip()
    except Exception:
        return "unknown"

def parse_ecofloc_output(output: str):
    results = []
    for line in output.splitlines():
        if ':' in line:
            try:
                name, rest = line.split(':', 1)
                value, unit = rest.strip().split(' ', 1)
                results.append((name.strip(), float(value.strip()), unit.strip()))
            except ValueError:
                continue
    return results

def monitor_resource_for_pid(args):
    pid, resource = args
    pname = get_process_name(pid)
    command = ['ecofloc', f'--{resource}', '-p', pid, '-i', str(INTERVAL_MS), '-t', str(DURATION_S)]
    print(f"[INFO] Monitoring {resource} for PID {pid} ({pname})")

    try:
        ecofloc_output = subprocess.check_output(command, stderr=subprocess.STDOUT, text=True)
        parsed = parse_ecofloc_output(ecofloc_output)

        db = SessionLocal()
        for metric_name, metric_value, unit in parsed:
            entry = EcoflocResult(
                pid=int(pid),
                process_name=pname,
                resource_type=resource,
                metric_name=metric_name,
                metric_value=metric_value,
                unit=unit
            )
            db.add(entry)
        db.commit()
        db.close()

        # Log to file
        with open(LOG_FILE, 'a') as log_file:
            log_file.write(f"[RES={resource}] [PID={pid}] ({pname})\n")
            log_file.write(ecofloc_output)
            log_file.write("\n*****************************\n")

        print(f"[INFO] DB saved for PID {pid} ({pname})")

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] ecofloc failed for PID {pid} ({pname}): {e.output}")
    except Exception as e:
        print(f"[ERROR] Unexpected: {e}")

def main():
    if not shutil.which("ecofloc"):
        print("[ERROR] ecofloc not found in PATH.")
        exit(1)

    init_db()
    print("[INFO] Starting continuous monitoring...")

    def handle_shutdown(signum, frame):
        print("[INFO] Shutting down...")
        exit(0)
    signal.signal(signal.SIGINT, handle_shutdown)

    while True:
        pids = get_active_pids()
        if not pids:
            print("[ERROR] No active processes found.")
            time.sleep(5)
            continue

        monitored_pids = [(pid, res) for pid in pids for res in RESOURCES]
        with multiprocessing.Pool() as pool:
            pool.map(monitor_resource_for_pid, monitored_pids)
        time.sleep(10)

if __name__ == "__main__":
    main()
