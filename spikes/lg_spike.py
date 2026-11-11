"""Stage 0 test: does `langgraph dev` run on Windows with no API key?"""
import json
import os
import pathlib
import subprocess
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROJECT = ROOT / "spikes" / "lg_project"
PORT = 2124
BASE = f"http://127.0.0.1:{PORT}"


def call(path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(BASE + path, data=data,
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read())


env = {**os.environ, "LANGSMITH_TRACING": "false"}
log_path = ROOT / "spikes" / "diag" / "langgraph_dev.log"
log_path.parent.mkdir(exist_ok=True)
with open(log_path, "wb") as log:
    server = subprocess.Popen(
        [str(ROOT / ".venv" / "Scripts" / "langgraph.exe"), "dev", "--no-browser", "--no-reload",
         "--port", str(PORT)],
        cwd=PROJECT, env=env, stdout=log, stderr=log, stdin=subprocess.DEVNULL,
    )
    try:
        started = time.time()
        ready = False
        while time.time() - started < 90 and server.poll() is None:
            try:
                call("/ok")
                ready = True
                break
            except Exception:
                time.sleep(1)
        print(f"server ready: {ready} after {time.time() - started:.1f}s; exit={server.poll()}")
        if ready:
            result = call("/runs/wait", {
                "assistant_id": "agent",
                "input": {"messages": [{"role": "user", "content": "hi"}]},
            })
            print("last message:", result["messages"][-1]["content"])
            spec = call("/openapi.json")
            operations = sum(
                1 for item in spec["paths"].values() for verb in item
                if verb in {"get", "post", "put", "patch", "delete"}
            )
            print(f"local API spec: {len(spec['paths'])} paths, {operations} operations")
    finally:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(server.pid)], capture_output=True)
if not ready:
    print(log_path.read_text(encoding="utf-8", errors="replace")[-1500:])
