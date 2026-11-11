"""Stage 0 test: find which part of the OpenCode call hangs. Always ends within its limit."""
import pathlib
import shutil
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "spikes" / "diag"
OUT.mkdir(exist_ok=True)
OPENCODE = shutil.which("opencode.cmd") or shutil.which("opencode")
MODEL = "opencode/deepseek-v4.1-flash-free"
LIMIT_SECONDS = 90

prompt_file = OUT / "prompt.md"
prompt_file.write_text("Reply with only the word PLUM.", encoding="utf-8")

CASES = {
    "default_agent": ["Reply with only the word OK."],
    "writer_agent": ["Reply with only the word OK.", "--agent", "writer"],
    "writer_with_file": ["Follow the attached file.", "--agent", "writer", "-f", str(prompt_file)],
}

for name, extra in CASES.items():
    command = [OPENCODE, "run", *extra, "-m", MODEL, "--format", "json", "--dir", str(ROOT),
               "--print-logs", "--log-level", "INFO"]
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
    print(f"--- {name}: exit={code} seconds={time.time() - started:.1f} output_chars={len(output)}")
    print("output start:", output[:500])
    print("log end:", log[-900:])
