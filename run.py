import subprocess
import time
import signal
import os

# Start backend
backend = subprocess.Popen(["uv", "run", "uvicorn", "main:app", "--reload"], cwd="backend")

# Give backend time to start
time.sleep(2)

try:
    # Start frontend
    subprocess.run(["uv", "run", "streamlit", "run", "streamlit_app.py"], cwd="frontend")
finally:
    # Kill backend when frontend stops
    os.kill(backend.pid, signal.SIGTERM)
