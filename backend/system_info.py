import os
import subprocess
import platform
import re
import psutil

def get_cpu_info():
    try:
        result = subprocess.check_output("lscpu", shell=True, text=True)
        match = re.search(r"Model name:\s*(.*)", result)
        if match:
            return match.group(1).strip()
    except Exception:
        pass

    # Fallback using /proc/cpuinfo
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if "model name" in line:
                    return line.split(":")[1].strip()
    except Exception:
        pass
    return "Unknown"

def get_ram_info():
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if "MemTotal" in line:
                    kb = int(re.findall(r'\d+', line)[0])
                    return round(kb / 1024 / 1024, 2)
    except Exception:
        pass
    return None

def get_disks():
    try:
        result = subprocess.check_output("lsblk -d -o NAME,ROTA,SIZE,MODEL", shell=True, text=True)
        lines = result.strip().split("\n")[1:]
        disks = []
        for line in lines:
            parts = line.split()
            name = parts[0]
            rota = parts[1]
            size = parts[2]
            model = " ".join(parts[3:]) if len(parts) > 3 else "Unknown"
            disk_type = "SSD" if rota == "0" else "HDD"
            disks.append({
                "name": name,
                "type": disk_type,
                "size": size,
                "model": model
            })
        return disks
    except Exception:
        return []

def get_gpu_info():
    try:
        # Try NVIDIA GPUs
        result = subprocess.check_output("nvidia-smi --query-gpu=name --format=csv,noheader", shell=True, text=True)
        return [line.strip() for line in result.strip().split("\n") if line.strip()]
    except Exception:
        pass

    try:
        # Try lshw for other GPUs
        result = subprocess.check_output("lshw -C display", shell=True, text=True)
        return re.findall(r'product:\s*(.*)', result)
    except Exception:
        pass

    return ["No GPU detected"]

def collect_system_info():
    return {
        "cpu": get_cpu_info(),
        "ram_gb": get_ram_info(),
        "disks": get_disks(),
        "gpus": get_gpu_info(),
        "os": platform.platform(),
    }



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
                "name": proc["name"],
                "cpu_percent": proc["cpu_percent"],
                "memory_percent": proc["memory_percent"],
                "resource": res,
                "ecofloc_output": res_output["output"],
                "error": res_output.get("error", None)
            })

    return results

import subprocess
import re

def measure_energy(pid: int, metric: str = "cpu", interval_ms: int = 1000, duration_s: int = 1) -> dict:
    """
    Run ecofloc for a single PID and metric (e.g. cpu, ram).
    Parses average power and total energy from the output.
    """
    cmd = [
        "ecofloc",
        f"--{metric}",
        "-p", str(pid),
        "-i", str(interval_ms),
        "-t", str(duration_s)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=duration_s + 5)
        output = result.stdout

        # Regex to extract power and energy
        avg_match = re.search(r"Average Power.*?:\s*([\d.]+)", output)
        total_match = re.search(r"Total.*Energy.*?:\s*([\d.]+)", output)

        if not avg_match or not total_match:
            return {"error": f"Could not parse output", "raw": output}

        return {
            "pid": pid,
            "metric": metric,
            "interval_ms": interval_ms,
            "duration_s": duration_s,
            "avg_power_w": float(avg_match.group(1)),
            "total_energy_j": float(total_match.group(1))
        }

    except subprocess.TimeoutExpired:
        return {"error": "Ecofloc timed out"}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import json
    print(json.dumps(collect_system_info(), indent=2))
    print(measure_energy(10847, "cpu", 1000, 2))

