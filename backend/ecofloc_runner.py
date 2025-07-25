import subprocess
import os
from datetime import datetime

def get_active_pids(limit=5):
    """Get active PIDs sorted by CPU usage."""
    try:
        result = subprocess.check_output(
            ['ps', '-u', os.getenv('USER'), '-o', 'pid=', '--sort=-%cpu', '--no-heading'],
            text=True
        )
        lines = result.strip().splitlines()
        return lines[:limit]
    except Exception as e:
        return []

def get_process_name(pid):
    try:
        with open(f'/proc/{pid}/comm', 'r') as f:
            return f.read().strip()
    except Exception:
        return "unknown"


def run_ecofloc_for_pid(pid, resource, interval_ms=1000, duration_s=5):
    command = [
        "ecofloc", f"--{resource}", "-p", str(pid),
        "-i", str(interval_ms), "-t", str(duration_s)
    ]
    
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        timer = threading.Timer(duration_s + 5, process.kill)  # Avoid hanging forever
        try:
            timer.start()
            stdout, stderr = process.communicate()
        finally:
            timer.cancel()

        return {
            "pid": pid,
            "resource": resource,
            "name": get_process_name(pid),
            "output": stdout.strip() if stdout else "",
            "error": stderr.strip() if stderr else None
        }

    except Exception as e:
        return {"pid": pid, "resource": resource, "name": get_process_name(pid), "error": str(e)}

def monitor_top_processes(resources=None, limit=5, interval=1000, duration=5):
    if resources is None:
        resources = ['cpu', 'ram']

    pids = get_active_pids(limit)
    all_results = []

    for pid in pids:
        for res in resources:
            result = run_ecofloc_for_pid(pid, res, interval, duration)
            all_results.append(result)

    return all_results
