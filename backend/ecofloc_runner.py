from typing import List, Dict, Any
import subprocess
import json

# Simulate getting ecofloc results (you'll replace this with real execution logic)
def run_ecofloc_simulated() -> List[Dict[str, Any]]:
    # Example: replace this with actual ecofloc command output
    with open("example_output.json") as f:
        return json.load(f)["results"]
    
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



def group_results_by_pid(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped = {}

    for entry in data:
        pid = entry["pid"]
        name = entry["name"]

        key = (pid, name)
        if key not in grouped:
            grouped[key] = {
                "pid": pid,
                "name": name,
                "cpu_percent": entry.get("cpu_percent", 0),
                "memory_percent": entry.get("memory_percent", 0),
                "resources": {}
            }

        grouped[key]["resources"][entry["resource"]] = {
            "output": entry.get("ecofloc_output", ""),
            "error": entry.get("error", "")
        }

    return list(grouped.values())
