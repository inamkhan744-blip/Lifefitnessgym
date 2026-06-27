import os
import sys
import subprocess

os.chdir(os.path.dirname(os.path.abspath(__file__)))

port = os.environ.get("PORT", "5000")

subprocess.run([
    sys.executable, "-m", "streamlit", "run", "app.py",
    "--server.port", port,
    "--server.address", "0.0.0.0",
    "--server.headless", "true",
    "--server.enableCORS", "false",
    "--server.enableXsrfProtection", "false",
    "--server.allowRunOnSave", "false",
])
