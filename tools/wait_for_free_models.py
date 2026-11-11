"""Try one small free-model call each hour. Stop at the first success or after 8 tries."""
import json
import pathlib
import shutil
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "spikes" / "diag"
OPENCODE = shutil.which("opencode.cmd") or shutil.which("opencode")
MODEL = "opencode/glm-5.3-flash-free"
PROBE = ("Use your tools to run the shell command whoami, then create the file "
         "spikes/should_not_exist.txt containing hello. "
         "If you have no tools, reply only with NO TOOLS.")
ATTEMPTS, WAIT_SECONDS, LIMIT_SECONDS = 8, 3600, 45


def attempt(number: int) -> bool:
    stdout_path, stderr_path = OUT / f"retest_{number}.out", OUT / f"retest_{number}.err"
    command = [OPENCODE, "run", PROBE, "--agent", "writer", "--title", f"retest-{number}", "-m", MODEL,
               "--format", "json", "--dir", str(ROOT), "--print-logs", "--log-level", "INFO"]
    with open(stdout_path, "wb") as out, open(stderr_path, "wb") as err:
        process = subprocess.Popen(command, stdout=out, stderr=err, stdin=subprocess.DEVNULL)
        try:
            process.wait(timeout=LIMIT_SECONDS)
        except subprocess.TimeoutExpired:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True)
            process.wait()
    text, tools, costs = [], [], []
    for line in stdout_path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            part = json.loads(line).get("part", {})
        except json.JSONDecodeError:
            continue
        if part.get("type") == "text":
            text.append(part.get("text", ""))
        if part.get("type") == "tool":
            tools.append((part.get("tool"), part.get("state", {}).get("status")))
        if "cost" in part:
            costs.append(part["cost"])
    limited = "Free usage limit reached" in stderr_path.read_text(encoding="utf-8", errors="replace")
    answer = "".join(text)
    print(f"try {number} at {time.strftime('%H:%M:%S')}: limited={limited} answer={answer[:120]!r} "
          f"tools={tools} costs={costs} "
          f"file_created={(ROOT / 'spikes' / 'should_not_exist.txt').exists()}", flush=True)
    return bool(answer)


for number in range(1, ATTEMPTS + 1):
    if attempt(number):
        print("FREE MODELS ARE RESPONDING", flush=True)
        sys.exit(0)
    if number < ATTEMPTS:
        time.sleep(WAIT_SECONDS)
print("FREE MODELS STILL LIMITED AFTER ALL TRIES", flush=True)
