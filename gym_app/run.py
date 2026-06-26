import os
import subprocess
import time
import sys

SERVER_PORT = 8080
STREAMLIT_PORT = 8081

print(f"[GymPro] Starting Streamlit on port {STREAMLIT_PORT}...")

subprocess.Popen([
    sys.executable, "-m", "streamlit", "run", "app.py",
    "--server.port", str(STREAMLIT_PORT),
    "--server.address", "127.0.0.1",
    "--server.headless", "true",
    "--server.enableCORS", "false",
    "--server.enableXsrfProtection", "false"
])

print(f"[GymPro] Waiting for Streamlit...")
time.sleep(5)

print(f"[GymPro] Streamlit ready on port {STREAMLIT_PORT}")
print(f"[GymPro] Starting proxy on port {SERVER_PORT}")

import uvicorn
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Route
import httpx

async def proxy(request):
    async with httpx.AsyncClient(base_url=f"http://127.0.0.1:{STREAMLIT_PORT}", timeout=60.0) as client:
        path = str(request.url.path)
        if request.url.query:
            path = f"{path}?{request.url.query}"
        resp = await client.request(request.method, path, headers=dict(request.headers), content=await request.body())
        return Response(content=resp.content, status_code=resp.status_code, headers=dict(resp.headers))

app = Starlette(routes=[Route("/{path:path}", proxy, methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])])
uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT, log_level="warning")