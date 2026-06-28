import os
import sys
import subprocess
import time

os.chdir(os.path.dirname(os.path.abspath(__file__)))

port = os.environ.get("PORT", "5000")

cmd = [
    sys.executable, "-m", "streamlit", "run", "app.py",
    "--server.port", port,
    "--server.address", "0.0.0.0",
    "--server.headless", "true",
    "--server.enableCORS", "false",
    "--server.enableXsrfProtection", "false",
    "--server.allowRunOnSave", "false",
]

while True:
    result = subprocess.run(cmd)
    if result.returncode == 0:
        break
    print(f"[GymPro] App stopped (code {result.returncode}), restarting in 3s...",
          flush=True)
    time.sleep(3)
