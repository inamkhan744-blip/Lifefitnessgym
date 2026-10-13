import os
import sys
import subprocess
import time
import signal

os.chdir(os.path.dirname(os.path.abspath(__file__)))

port = os.environ.get("PORT", "5000")

def free_port(p):
    for _ in range(3):
        try:
            subprocess.run(["fuser", "-k", f"{p}/tcp"], capture_output=True, timeout=5)
        except Exception:
            pass
        try:
            result = subprocess.run(["lsof", "-ti", f":{p}"], capture_output=True, text=True, timeout=5)
            for pid in result.stdout.strip().split():
                try:
                    os.kill(int(pid), signal.SIGKILL)
                except Exception:
                    pass
        except Exception:
            pass
        time.sleep(1)

# Check if streamlit is installed
try:
    import streamlit
    print(f"✅ Streamlit version: {streamlit.__version__}")
except ImportError:
    print("⚠️ Streamlit not found! Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit", "--quiet"])

# Install other dependencies
try:
    print("📦 Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--quiet"])
    print("✅ Dependencies installed successfully!")
except Exception as e:
    print(f"⚠️ Error installing dependencies: {e}")

# Kill any existing process on port
free_port(port)

# Start Streamlit directly - NO LOOP, NO DELAY
cmd = [
    sys.executable, "-m", "streamlit", "run", "app.py",
    "--server.port", port,
    "--server.address", "0.0.0.0",
    "--server.headless", "true",
    "--server.enableCORS", "false",
    "--server.enableXsrfProtection", "false",
]

print(f"🚀 Starting GymPro on port {port}...")
print(f"🔗 App will be available at: https://gympro.inamkhan4.repl.co")

# Direct run - NO while loop, NO sleep
subprocess.run(cmd)