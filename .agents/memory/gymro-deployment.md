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
run = ["/bin/bash", "/home/runner/workspace/gym-app/start.sh"]

[services.production.health.startup]
path = "/_stcore/health"
```

**Key:** `localPort = 8080` — Cloud Run (Autoscale) injects PORT env and routes on port 8080. Both `start.sh` and `run.py` must default to port 8080 when PORT env is not set.

### Port alignment rule
`localPort` in artifact.toml, `PORT` default in `start.sh`, and `PORT` default in `run.py` must all match. Mismatch causes health check to probe the wrong port.

## cv2 / face_engine lazy import
cv2 is imported lazily in `face_engine.py` (only loaded on first function call). Do NOT add `import cv2` at module level anywhere — Cloud Run (gVisor sandbox) may SIGKILL the process on compiled C++ extension load. All cv2 references in `gym_pages/members.py` are inside try/except blocks inside functions.

## Deployment history / notes
- GCE (Reserved VM): attempted, failed — unknown root cause (zero runtime logs from `fetchDeploymentLogs`)
- Autoscale (Cloud Run): switched by user in UI; build 98d2a48d failed at "Creating Autoscale service" ~5 min after service creation
- Root cause theory: port mismatch — Cloud Run routes on 8080, app was starting on 5000
- Fix applied: localPort=8080, PORT defaults=8080, health path=/_stcore/health

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
