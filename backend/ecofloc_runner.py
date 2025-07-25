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
    try:
        command = [
            "ecofloc", f"--{resource}", "-p", str(pid),
            "-i", str(interval_ms), "-t", str(duration_s)
        ]
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, text=True, timeout=duration_s + 5)
        return {
            "pid": pid,
            "resource": resource,
            "name": get_process_name(pid),
            "output": output
        }
    except subprocess.TimeoutExpired:
        return {"pid": pid, "resource": resource, "name": get_process_name(pid), "error": "Timeout"}
    except subprocess.CalledProcessError as e:
        return {"pid": pid, "resource": resource, "name": get_process_name(pid), "error": e.output}
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
