import os
import sys
import subprocess
import time
import signal

os.chdir(os.path.dirname(os.path.abspath(__file__)))

port = os.environ.get("PORT", "5000")


def free_port(p):
    """Port par jo bhi chal raha ho usse forcefully kill karo."""
    for _ in range(3):
        try:
            subprocess.run(["fuser", "-k", f"{p}/tcp"],
                           capture_output=True, timeout=5)
        except Exception:
            pass
        try:
            result = subprocess.run(["lsof", "-ti", f":{p}"],
                                    capture_output=True, text=True, timeout=5)
            for pid in result.stdout.strip().split():
                try:
                    os.kill(int(pid), signal.SIGKILL)
                except Exception:
                    pass
        except Exception:
            pass
        time.sleep(1)
        try:
            check = subprocess.run(["lsof", "-ti", f":{p}"],
                                   capture_output=True, text=True, timeout=3)
            if not check.stdout.strip():
                break
        except Exception:
            break


cmd = [
    sys.executable, "-m", "streamlit", "run", "app.py",
    "--server.port", port,
    "--server.address", "0.0.0.0",
    "--server.headless", "true",
    "--server.enableCORS", "false",
    "--server.enableXsrfProtection", "false",
    "--server.allowRunOnSave", "false",
    "--server.fileWatcherType", "none",
]

while True:
    free_port(port)
    result = subprocess.run(cmd)
    if result.returncode == 0:
        break
    print(f"[GymPro] App stopped (code {result.returncode}), restarting in 3s...",
          flush=True)
    time.sleep(3)
