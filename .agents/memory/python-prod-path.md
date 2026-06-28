---
name: Python path in production
description: python/python3 commands are not in system PATH in Replit autoscale (Cloud Run) production containers — must use absolute path.
---

## Rule

Never use bare `python` or `python3` in `artifact.toml` production run commands for Python projects. Use the absolute path instead:

```
/home/runner/workspace/.pythonlibs/bin/python3
```

## Why

In Replit's Cloud Run (autoscale) production containers, `python` and `python3` are not on the system PATH. The interpreter lives at `/home/runner/workspace/.pythonlibs/bin/python3`. Using a bare `python` command silently fails with exit 127 ("command not found"), the container generates zero logs, and the startup probe times out — causing the deployment to fail with no visible error.

## How to apply

In `[services.production]` run commands in `artifact.toml`, always prefix with the absolute path:

```toml
[services.production]
run = "cd /home/runner/workspace/gym-app && /home/runner/workspace/.pythonlibs/bin/python3 run.py"
```

Note: `run.py` uses `sys.executable` internally to spawn subprocesses (e.g. streamlit), so it automatically uses the correct Python binary once started with the absolute path.
