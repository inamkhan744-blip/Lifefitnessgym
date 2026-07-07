#!/bin/bash
echo "=== GymPro Production Startup ==="
echo "Date: $(date -u)"
echo "User: $(id)"
echo "PWD: $(pwd)"
echo "PATH: $PATH"
echo "PORT env: ${PORT:-NOT_SET}"

PYTHON=""

try_python() {
    local p="$1"
    if [ -f "$p" ] && [ -x "$p" ]; then
        echo "Trying: $p"
        "$p" --version 2>&1
        if "$p" -c "import sys; print('sys.version:', sys.version)" 2>&1; then
            PYTHON="$p"
            return 0
        fi
    elif [ -L "$p" ]; then
        local target
        target=$(readlink -f "$p" 2>/dev/null)
        echo "Symlink $p -> $target"
        if [ -n "$target" ] && [ -x "$target" ]; then
            echo "Symlink target exists, trying: $target"
            "$target" --version 2>&1
            PYTHON="$target"
            return 0
        else
            echo "BROKEN SYMLINK: $p -> $target (does not exist or not executable)"
        fi
    fi
    echo "Not usable: $p"
    return 1
}

echo "--- Searching for Python ---"
try_python "/home/runner/workspace/.pythonlibs/bin/python" || \
try_python "/nix/var/nix/profiles/default/bin/python3" || \
try_python "/usr/bin/python3" || \
try_python "/usr/local/bin/python3" || \
PYTHON="$(which python3 2>/dev/null)"

if [ -z "$PYTHON" ]; then
    echo "FATAL: No working Python found!"
    echo "Contents of /home/runner/workspace/.pythonlibs/bin/:"
    ls -la /home/runner/workspace/.pythonlibs/bin/ 2>/dev/null || echo "(dir missing)"
    echo "Contents of /usr/bin/python*:"
    ls -la /usr/bin/python* 2>/dev/null || echo "(none)"
    exit 1
fi

echo "=== Using Python: $PYTHON ==="
export PYTHONPATH="/home/runner/workspace/.pythonlibs/lib/python3.11/site-packages"
echo "PYTHONPATH: $PYTHONPATH"

echo "--- Verifying imports ---"
"$PYTHON" -c "import streamlit; print('streamlit:', streamlit.__version__)" || {
    echo "streamlit import FAILED"
    "$PYTHON" -c "import sys; print('sys.path:', sys.path)"
    exit 1
}
"$PYTHON" -c "import sqlalchemy; print('sqlalchemy:', sqlalchemy.__version__)" || echo "WARNING: sqlalchemy import failed"

PORT="${PORT:-5000}"
echo "=== Starting Streamlit on 0.0.0.0:${PORT} ==="

cd /home/runner/workspace/gym-app

exec "$PYTHON" -m streamlit run app.py \
    --server.port "$PORT" \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.enableCORS false \
    --server.enableXsrfProtection false \
    --server.fileWatcherType none
