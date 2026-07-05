---
name: GymPro deployment fix
description: How to configure deployment for a Python/Streamlit app in a pnpm workspace Replit project
---

# GymPro Deployment Configuration

## The problem
In a `PNPM_WORKSPACE` stack Replit project, deployment config lives in `artifact.toml`, NOT in `.replit`. A Python/Streamlit app that isn't a registered pnpm artifact gets "could not find run command" when trying to publish.

## The fix (two-step)

### Step 1 — Bootstrap artifact.toml via bash (creates the file)
```bash
mkdir -p /home/runner/workspace/gym-app/.replit-artifact
cat > /home/runner/workspace/gym-app/.replit-artifact/artifact.toml << 'EOF'
kind = "web"
previewPath = "/"
title = "GymPro"
version = "1.0.0"
id = "gymPro5000PythonStreamlit"

[[services]]
localPort = 5000
name = "GymPro App"
paths = ["/"]

[services.development]
run = "cd /home/runner/workspace/gym-app && python run.py"

[services.production]
run = "cd /home/runner/workspace/gym-app && python run.py"
EOF
```

### Step 2 — Trigger `createArtifact` with any react-vite slug to force Replit to scan and register the bash-created artifact.toml
```javascript
await createArtifact({ artifactType: "react-vite", slug: "gym-pro", previewPath: "/gym-pro", title: "GymPro" });
```
This forces Replit's artifact service to re-scan the workspace and it picks up the gym-app's artifact.toml, registering it with id `gymPro5000PythonStreamlit`.

After this, `listArtifacts()` shows the gym-app artifact as registered and `suggestDeploy()` should work.

## Why run.py uses direct Streamlit
The old proxy (Starlette + httpx forwarding to Streamlit) only handled HTTP, not WebSocket. Streamlit requires WebSocket for its interactive UI. The fix: run Streamlit directly on port 5000 with `subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "5000", "--server.address", "0.0.0.0", ...])`. No proxy needed.

**Why:** Direct Streamlit on port 5000 handles both HTTP and WebSocket natively. The old proxy caused the "loading spinner forever" bug.

**How to apply:** If `run.py` is ever changed back to a proxy setup, the preview will show an infinite loading spinner.

## Autoscale vs Reserved VM
Streamlit apps MUST use Reserved VM deployment type, not Autoscale. Two reasons:
1. Streamlit uses persistent WebSocket connections — Autoscale (Cloud Run) kills these
2. Replit's managed PostgreSQL may not be reachable from Cloud Run's GCP network

## Root causes of the 6x Autoscale failure
Three compounding problems were found by reading all 6 build logs:
1. **cv2 (OpenCV) top-level import** — attendance.py → face_engine.py → `import cv2` runs at startup. Cloud Run uses gVisor sandbox which can crash compiled C++ extensions (SIGKILL, zero logs). Fix: made cv2 lazy in face_engine.py (only loads on first function call).
2. **`production.build = "pip install..."`** in artifact.toml — this ran pip install in the production container before starting the app, consuming 3-4 minutes of the startup probe window. Fix: removed it.
3. **Deployment type** — Streamlit WebSocket incompatibility with Autoscale. User must switch to Reserved VM in the Deployments pane.

## Correct artifact.toml production run command
```toml
[services.production]
run = "cd /home/runner/workspace/gym-app && /home/runner/workspace/.pythonlibs/bin/python3 -m streamlit run app.py --server.port 5000 --server.address 0.0.0.0 --server.headless true --server.enableCORS false --server.enableXsrfProtection false --server.fileWatcherType none"

[services.production.health.startup]
path = "/_stcore/health"
```

Key: use `.pythonlibs/bin/python3` (the nix-wrapped Python that has all env vars set), NOT plain `python3`.
