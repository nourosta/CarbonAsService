from typing import List, Dict, Any
import subprocess
import json

# Simulate getting ecofloc results (you'll replace this with real execution logic)
def run_ecofloc_simulated() -> List[Dict[str, Any]]:
    # Example: replace this with actual ecofloc command output
    with open("example_output.json") as f:
        return json.load(f)["results"]


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
