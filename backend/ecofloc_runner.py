import subprocess

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
            #timeout=duration + 5
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
