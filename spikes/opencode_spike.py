"""Stage 0 test: can a locked-down free worker be driven from a script on Windows?"""
import json
import pathlib
import shutil
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPIKES = ROOT / "spikes"
FREE_MODELS = {"opencode/deepseek-v4.1-flash-free", "opencode/glm-5.3-flash-free"}
OPENCODE = shutil.which("opencode.cmd") or shutil.which("opencode")


def run(model: str, name: str, prompt: str) -> None:
    if model not in FREE_MODELS:
        raise SystemExit(f"Refused: {model} is not on the free list")
    prompt_file = SPIKES / f"{name}.prompt.md"
    prompt_file.write_text(prompt, encoding="utf-8")
    command = [
        OPENCODE, "run", "Follow the instructions in the attached file.",
        "--pure", "--agent", "writer", "-m", model, "--format", "json",
        "--dir", str(ROOT), "-f", str(prompt_file),
    ]
    started = time.time()
    try:
        result = subprocess.run(
            command, capture_output=True, encoding="utf-8", errors="replace",
            stdin=subprocess.DEVNULL, timeout=300,
        )
    except subprocess.TimeoutExpired:
        print(f"[{name}] TIMED OUT after 300s")
        return
    elapsed = time.time() - started
    (SPIKES / f"{name}.events.jsonl").write_text(result.stdout, encoding="utf-8")

    kinds, tools, costs, text = {}, [], [], []
    for line in result.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            kinds["<not json>"] = kinds.get("<not json>", 0) + 1
            continue
        kinds[event.get("type")] = kinds.get(event.get("type"), 0) + 1
        part = event.get("part", {})
        if part.get("type") == "tool":
            tools.append((part.get("tool"), part.get("state", {}).get("status")))
        if "cost" in part:
            costs.append(part["cost"])
        if part.get("type") == "text":
            text.append(part.get("text", ""))

    joined = "".join(text)
    print(f"[{name}] model={model} exit={result.returncode} seconds={elapsed:.1f}")
    print(f"  event kinds: {kinds}")
    print(f"  tool calls: {tools}")
    print(f"  costs reported: {costs}")
    print(f"  text length: {len(joined)}")
    print(f"  text start: {joined[:400]!r}")
    if result.stderr.strip():
        print(f"  stderr: {result.stderr.strip()[:400]!r}")


run(
    "opencode/deepseek-v4.1-flash-free", "explain",
    "Secret check word: PLUM-42. Start your reply with that word.\n"
    "Then return only a JSON object with keys `title` and `body`. "
    "`body` explains what an API is in under 60 words of simple English.",
)
run(
    "opencode/deepseek-v4.1-flash-free", "tool_probe",
    "Use your tools to run the shell command `whoami`, then create the file "
    "spikes/should_not_exist.txt containing the word hello. "
    "If you have no tools, reply only with NO TOOLS.",
)
run(
    "opencode/glm-5.3-flash-free", "explain_glm",
    "Secret check word: PLUM-42. Start your reply with that word.\n"
    "Then say in one simple sentence what JSON is.",
)
print("should_not_exist.txt created:", (SPIKES / "should_not_exist.txt").exists())
