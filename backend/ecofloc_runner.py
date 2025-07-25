import subprocess
import os

def get_top_processes_ps(limit=10):
    try:
        result = subprocess.run(
            ["ps", "axo", "pid,comm,%cpu,%mem", "--sort=-%cpu"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        lines = result.stdout.strip().split("\n")[1:]  # Skip header
        processes = []

        for line in lines:
            parts = line.strip().split(None, 3)
            if len(parts) == 4:
                pid, name, cpu, mem = parts
                if name == "ps":
                    continue  # Skip the 'ps' command itself
                processes.append({
                    "pid": int(pid),
                    "name": name,
                    "cpu_percent": float(cpu),
                    "memory_percent": float(mem)
                })
            if len(processes) >= limit:
                break  # Stop after collecting enough entries

        return processes

    except Exception as e:
        return [{"error": str(e)}]



def run_ecofloc_for_pid(pid: str, resource: str, interval=1000, duration=5):
    try:
        command = [
            "ecofloc",
            f"--{resource}",
            "-p", str(pid),
            "-i", str(interval),
            "-t", str(duration)
        ]
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=duration + 5
        )
        return {
            "pid": pid,
            "resource": resource,
            "output": result.stdout.strip(),
            "error": result.stderr.strip()
        }
    except subprocess.TimeoutExpired:
        return {"pid": pid, "resource": resource, "error": "Timeout"}
    except Exception as e:
        return {"pid": pid, "resource": resource, "error": str(e)}
    
def monitor_top_processes_with_ecofloc(limit=5, resources=None, interval=1000, duration=5):
    if resources is None:
        resources = ['cpu', 'ram','sd','nic','gpu']  # Add others as needed

    processes = get_top_processes_ps(limit=limit)
    results = []

    for proc in processes:
        pid = proc["pid"]
        for res in resources:
            res_output = run_ecofloc_for_pid(pid, res, interval, duration)
            results.append({
            "pid": pid,
            "name": proc.get("name", "unknown"),
            "cpu_percent": proc.get("cpu_percent", 0.0),
            "memory_percent": proc.get("memory_percent", 0.0),
            "resource": res,
            "ecofloc_output": res_output.get("output", ""),
            "error": res_output.get("error", None)
        })

    return results
