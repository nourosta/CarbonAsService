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


if __name__ == "__main__":
    import json
    print(json.dumps(collect_system_info(), indent=2))
