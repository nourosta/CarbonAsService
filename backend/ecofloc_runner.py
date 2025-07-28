import subprocess
import os
import threading
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


def run_ecofloc_for_pid(pid, resource, interval_ms=1000, duration_s=5, timeout_buffer=10):
    command = [
        "ecofloc", f"--{resource}", "-p", str(pid),
        "-i", str(interval_ms), "-t", str(duration_s)
    ]
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    try:
        stdout, stderr = process.communicate(timeout=duration_s + timeout_buffer)
        if process.returncode == 0:
            return {
                "pid": pid,
                "resource": resource,
                "name": get_process_name(pid),
                "output": stdout
            }
        else:
            return {
                "pid": pid,
                "resource": resource,
                "name": get_process_name(pid),
                "error": stderr or "Process failed with non-zero exit code"
            }
    except subprocess.TimeoutExpired:
        # Terminate the process gracefully
        process.terminate()
        try:
            # Give it a short time to terminate
            stdout, stderr = process.communicate(timeout=1)
            return {
                "pid": pid,
                "resource": resource,
                "name": get_process_name(pid),
                "output": stdout or "",
                "error": "Timeout occurred, partial output captured"
            }
        except subprocess.TimeoutExpired:
            # If it doesn't terminate, kill it
            process.kill()
            stdout, stderr = process.communicate()
            return {
                "pid": pid,
                "resource": resource,
                "name": get_process_name(pid),
                "output": stdout or "",
                "error": "Process killed after timeout, partial output captured"
            }
    except Exception as e:
        return {
            "pid": pid,
            "resource": resource,
            "name": get_process_name(pid),
            "error": str(e)
        }
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
