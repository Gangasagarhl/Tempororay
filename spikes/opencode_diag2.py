"""Stage 0 test: is the free limit per model, and is the paid title call gone?"""
import pathlib
import re
import shutil
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "spikes" / "diag"
OUT.mkdir(exist_ok=True)
OPENCODE = shutil.which("opencode.cmd") or shutil.which("opencode")
MODEL = "opencode/glm-5.3-flash-free"
LIMIT_SECONDS = 60

CASES = {
    "glm_writer": "Reply with only the word OK.",
    "glm_tool_probe": "Use your tools to run the shell command whoami, then create the file "
                      "spikes/should_not_exist.txt containing hello. "
                      "If you have no tools, reply only with NO TOOLS.",
}

for name, prompt in CASES.items():
    command = [OPENCODE, "run", prompt, "--agent", "writer", "--title", name, "-m", MODEL,
               "--format", "json", "--dir", str(ROOT), "--print-logs", "--log-level", "INFO"]
    stdout_path, stderr_path = OUT / f"{name}.out", OUT / f"{name}.err"
    started = time.time()
    with open(stdout_path, "wb") as out, open(stderr_path, "wb") as err:
        process = subprocess.Popen(command, stdout=out, stderr=err, stdin=subprocess.DEVNULL)
        try:
            code = process.wait(timeout=LIMIT_SECONDS)
        except subprocess.TimeoutExpired:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True)
            process.wait()
            code = "TIMED OUT"
    output = stdout_path.read_text(encoding="utf-8", errors="replace")
    log = stderr_path.read_text(encoding="utf-8", errors="replace")
    print(f"--- {name}: exit={code} seconds={time.time() - started:.1f}")
    print("models used:", sorted(set(re.findall(r"modelID=(\S+)", log))))
    print("errors:", sorted(set(re.findall(r'error\.error="([^"]{0,120})', log))))
    print("texts:", re.findall(r'"type":"text","text":"([^"]{0,200})', output))
    print("tool events:", re.findall(r'"tool":"([^"]+)".{0,200}?"status":"([^"]+)"', output))
    print("cost values:", re.findall(r'"cost":([0-9.e-]+)', output))
print("should_not_exist.txt created:", (ROOT / "spikes" / "should_not_exist.txt").exists())
