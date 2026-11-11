"""One-line progress report for the lab's background work."""
import json
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOGS, SITE = ROOT / "logs", ROOT / "site"
log = (LOGS / "keep_going.log").read_text(encoding="utf-8", errors="replace").splitlines() if (LOGS / "keep_going.log").exists() else []
last = next((line for line in reversed(log) if line[:4].isdigit()), "no log yet")
live_report = SITE / "data" / "build_report.json"
expected = json.loads(live_report.read_text(encoding="utf-8"))["chunks"] if live_report.exists() else 350
stage = SITE / "data.new"
running = subprocess.run(["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | ForEach-Object { $_.CommandLine }"],
                         capture_output=True, text=True).stdout

if "build_site.py" in running:
    written = len(list((stage / "chunks").glob("*.js"))) if (stage / "chunks").exists() else 0
    out = (LOGS / "build.out.txt").read_text(encoding="utf-8", errors="replace") if (LOGS / "build.out.txt").exists() else ""
    if written == 0:
        steps = ["plain-English", "pages, endpoints", "installed code", "reference pages indexed"]
        reached = sum(1 for s in steps if s in out)
        percent = 2 * reached
        detail = f"reading sources ({reached} of {len(steps)} steps)"
    else:
        percent = min(95, 8 + round(87 * written / expected))
        detail = f"{written} of about {expected} data files written"
    print(f"Build: {percent}% done ({detail}). After it: word check, structure check, browser test, then swap in.")
elif "audit_words.py" in running or "verify_site.py" in running:
    print("Build: 96% done. Running the word check and structure check now.")
elif "rewrite.py" in running:
    done_file = ROOT / "source" / "simple" / "done.jsonl"
    units_file = ROOT / "source" / "simple" / "units.jsonl"
    total = sum(1 for _ in units_file.open(encoding="utf-8")) if units_file.exists() else 0
    accepted = sum(1 for line in done_file.open(encoding="utf-8") if '"ok": true' in line) if done_file.exists() else 0
    print(f"Simpler words: {round(100 * accepted / total) if total else 0}% ({accepted:,} of {total:,} passages).")
else:
    print("Nothing is building right now.")
print("Latest log line:", re.sub(r"\s+", " ", last)[:220])
