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
