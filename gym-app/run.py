import os
import sys
import subprocess
import time
import signal

os.chdir(os.path.dirname(os.path.abspath(__file__)))

port = os.environ.get("PORT", "5000")


def free_port(p):
    """Agar port koi aur process use kar raha ho to usse kill karo."""
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{p}"],
            capture_output=True, text=True
        )
        pids = result.stdout.strip().split()
        for pid in pids:
            try:
                os.kill(int(pid), signal.SIGKILL)
            except Exception:
                pass
        if pids:
            time.sleep(1)
    except Exception:
        pass


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
    free_port(port)
    result = subprocess.run(cmd)
    if result.returncode == 0:
        break
    print(f"[GymPro] App stopped (code {result.returncode}), restarting in 3s...",
          flush=True)
    time.sleep(3)
