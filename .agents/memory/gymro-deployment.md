---
name: GymPro deployment fix
description: How to configure deployment for a Python/Streamlit app in a pnpm workspace Replit project
---

# GymPro Deployment Configuration

## The problem
In a `PNPM_WORKSPACE` stack Replit project, deployment config lives in `artifact.toml`, NOT in `.replit`. A Python/Streamlit app that isn't a registered pnpm artifact gets "could not find run command" when trying to publish.

## Current working configuration (July 2026)

### artifact.toml
```toml
kind = "web"
previewPath = "/"
title = "GymPro"
version = "1.0.0"
id = "gymPro5000PythonStreamlit"

[[services]]
localPort = 8080
name = "Start application"
paths = ["/"]

[services.development]
run = "cd /home/runner/workspace/gym-app && /home/runner/workspace/.pythonlibs/bin/python run.py"

[services.production]
run = "cd /home/runner/workspace/gym-app && /home/runner/workspace/.pythonlibs/bin/python -m streamlit run app.py --server.port 8080 --server.address 0.0.0.0 --server.headless true --server.enableCORS false --server.enableXsrfProtection false --server.fileWatcherType none"
```

**Critical rule: production `run` must be a STRING, not an array.** Array format `run = ["/bin/bash", "..."]` causes pid1 to silently skip the service with zero runtime logs. The development run is a string, production must also be a string.

**Key:** `localPort = 8080` — both dev (`run.py`) and prod (streamlit args) must bind to port 8080.

### Port alignment rule
`localPort` in artifact.toml, `PORT` default in `run.py`, and `--server.port` in the production run command must all be 8080. Mismatch causes health check to probe wrong port.

## cv2 / face_engine lazy import
cv2 is imported lazily in `face_engine.py` (only loaded on first function call). Do NOT add `import cv2` at module level anywhere — Cloud Run (gVisor sandbox) may SIGKILL the process on compiled C++ extension load. All cv2 references in `gym_pages/members.py` are inside try/except blocks inside functions.

## Deployment type
Use **Reserved VM (GCE)**, not Autoscale (Cloud Run). Cloud Run lacks SOCI/ZTOC streaming so the ~3.6 GB Repl layer must fully download before the startup probe fires — the probe times out first. GCE uses SOCI lazy streaming and starts the container immediately.

## Repl layer size (post-cleanup)
After deleting `node_modules/` (500 MB) and `.local/share/pnpm/store/` (465 MB), the Repl layer is ~3.6 GB (dominated by `.pythonlibs/` at 3.4 GB). These JS directories are safe to delete since the app is pure Python. Restore with `pnpm install` if JS tooling is needed.

## How to bootstrap artifact from scratch
```javascript
// Step 1: write artifact.toml via bash
// Step 2: force Replit scan via createArtifact (any slug)
await createArtifact({ artifactType: "react-vite", slug: "gym-pro", previewPath: "/gym-pro", title: "GymPro" });
// This makes Replit re-scan and register the gym-app artifact.toml
```

## Why run.py uses direct Streamlit (not proxy)
Streamlit needs WebSocket. Any HTTP-only proxy (Starlette + httpx) breaks the interactive UI with infinite loading. Run Streamlit directly with `sys.executable -m streamlit run app.py`.

## No `production.build` in artifact.toml
Never add `[services.production.build]` with pip install — it runs inside the startup probe window and consumes all available time before the app even starts.
