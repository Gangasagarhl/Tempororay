"""Stage 0 test: can a Managed Deep Agent project be created and compiled with no account?"""
import os
import pathlib
import shutil
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPIKES = ROOT / "spikes"
MDA = str(ROOT / ".venv" / "Scripts" / "mda.exe")
PROJECT = SPIKES / "mda_test"
env = {**os.environ, "LANGSMITH_TRACING": "false"}


def step(label, args, cwd):
    with open(SPIKES / "diag" / f"mda_{label}.log", "wb") as log:
        process = subprocess.Popen([MDA, *args], cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                   stdout=log, stderr=log)
        try:
            code = process.wait(timeout=60)
        except subprocess.TimeoutExpired:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True)
            process.wait()
            code = "TIMED OUT"
    output = (SPIKES / "diag" / f"mda_{label}.log").read_text(encoding="utf-8", errors="replace")
    print(f"--- {label}: exit={code}\n{output[-700:]}")


if PROJECT.exists():
    shutil.rmtree(PROJECT)
step("init", ["init", "mda_test"], SPIKES)
if PROJECT.exists():
    print("files:", sorted(p.relative_to(PROJECT).as_posix() for p in PROJECT.rglob("*") if p.is_file())[:30])
    step("build", ["build"], PROJECT)
