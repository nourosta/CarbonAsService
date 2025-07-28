import subprocess
import time
import signal
import os

def start_process(command, cwd=None):
    return subprocess.Popen(command, cwd=cwd)

try:
    # Start backend uvicorn main:app with reload, on 0.0.0.0:8000
    proc1 = start_process(["uv", "run", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"], cwd="backend")

    # Start second uvicorn service on localhost:5000
    proc2 = start_process(["uv", "run", "uvicorn", "boaviztapi.main:app", "--host=localhost", "--port", "5000"], cwd="backend")

    # Start ecofloc_database.py
    proc3 = start_process(["uv", "run", "ecofloc_database.py"], cwd="backend")

    # Give some time for backend services to initialize
    time.sleep(3)

    # Start streamlit app in frontend directory, run in foreground
    subprocess.run(["uv", "run", "streamlit", "run", "streamlit_app.py"], cwd="frontend")

finally:
    # When streamlit app exits, terminate all background processes
    for p in [proc1, proc2, proc3]:
        try:
            os.kill(p.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
