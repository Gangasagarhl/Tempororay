"""Rewrite the docs' own wording in plain English, using the free Gemini tier. Stops at the daily limit; rerun to resume.

  rewrite.py collect     list every distinct paragraph to rewrite, and measure the job
  rewrite.py run         rewrite them (needs GEMINI_API_KEY in the .env file)
  rewrite.py test        check the safety rules on made-up rewrites
"""
import json
import os
import pathlib
import re
import sys
import time

import httpx

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools.textcheck import MARK, check_rewrite, leaves, protect, tokens, unit_hash  # noqa: E402

DATA = ROOT / "site" / "data"
OUT = ROOT / "source" / "simple"
UNITS, DONE = OUT / "units.jsonl", OUT / "done.jsonl"
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
PER_MINUTE = 9
BATCH_WORDS = 1800
PROMPT = """Rewrite each numbered passage from software documentation in plain English for someone who knows basic Python but is new to APIs and agents.
Rules:
- Keep every fact, condition, warning and example. Do not add facts. Never summarise or skip anything.
- Keep every mark like ⟦3⟧ exactly once, unchanged. Each stands for code or a link.
- Keep every number and every code name exactly as written, such as snake_case, CamelCase or dotted names.
- Keep words like not, must, only, unless, optional and may exactly as strong as in the original.
- Use short sentences and common words. Keep any Markdown such as ** or list markers.
Reply with only a JSON array of strings, one rewrite for each passage, in the same order.

"""


def env_key():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"')
    return os.environ.get("GEMINI_API_KEY", "")


def worth_rewriting(text):
    masked = MARK.sub(" ", protect(text)[0])
    return len(re.findall(r"[A-Za-z]{3,}", masked)) >= 6


def collect():
    audit_map = json.loads((DATA / "audit_map.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    units, words = {}, 0
    source_cache = {}

    def source_text(source):
        key = json.dumps(source, sort_keys=True)
        if key not in source_cache:
            if "page" in source:
                text = (ROOT / "source" / "pages" / source["page"]).read_text(encoding="utf-8")
            elif "ref" in source:
                record = json.loads((ROOT / "source" / "reference" / source["ref"]).read_text(encoding="utf-8"))["data"]
                text = "\n".join(value for _, value in leaves(record))
            else:
                text = ""
            source_cache.clear()
            source_cache[key] = " ".join(tokens(text))
        return source_cache[key]

    for chunk in sorted((DATA / "chunks").glob("*.js"), key=lambda p: int(p.stem)):
        body = chunk.read_text(encoding="utf-8").strip()
        for identifier, item in json.loads(body[body.index(",") + 1:-2]).items():
            source = audit_map.get(identifier)
            if not source:
                continue
            original = source_text(source) if ("page" in source or "ref" in source) else None
            for step in item["steps"]:
                pieces = str(step.get("t") or "").split("\n\n")
                pieces += [c for row in (step.get("table") or {}).get("rows", []) for c in row if isinstance(c, str)]
                for piece in pieces:
                    # keep only the docs' own wording; the lab's fixed narration is already plain
                    if not worth_rewriting(piece) or (original is not None and " ".join(tokens(piece)) not in original):
                        continue
                    masked, _ = protect(piece)
                    digest = unit_hash(masked)
                    if digest not in units:
                        units[digest] = masked
                        words += len(masked.split())
    with open(UNITS, "w", encoding="utf-8") as out:
        for digest, masked in units.items():
            out.write(json.dumps({"h": digest, "m": masked}, ensure_ascii=False) + "\n")
    print(f"distinct passages: {len(units):,}   words: {words:,}   about {words * 1.35 / 1_000_000:.1f} million tokens each way")


def already_done():
    if not DONE.exists():
        return {}
    return {r["h"]: r for r in map(json.loads, DONE.read_text(encoding="utf-8").splitlines())}


def batches(units):
    current, size = [], 0
    for unit in units:
        count = len(unit["m"].split())
        if current and size + count > BATCH_WORDS:
            yield current
            current, size = [], 0
        current.append(unit)
        size += count
    if current:
        yield current


def call_model(client, key, batch, notes=""):
    numbered = "\n\n".join(f"[{n}] {unit['m']}" for n, unit in enumerate(batch))
    response = client.post(f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent", headers={"x-goog-api-key": key},
                           json={"contents": [{"parts": [{"text": PROMPT + notes + numbered}]}], "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}})
    if response.status_code == 429:
        return None, response.text[:300]
    response.raise_for_status()
    text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    answer = json.loads(text)
    if not isinstance(answer, list) or len(answer) != len(batch):
        raise ValueError("wrong number of answers")
    return answer, ""


def run():
    key = env_key()
    if not key:
        sys.exit("Add GEMINI_API_KEY=your-key to the .env file first.")
    done = already_done()
    todo = [u for u in map(json.loads, UNITS.read_text(encoding="utf-8").splitlines()) if u["h"] not in done or (not done[u["h"]].get("ok") and done[u["h"]].get("tries", 0) < 3)]
    print(f"to rewrite: {len(todo):,} passages in {MODEL}", flush=True)
    client, gap = httpx.Client(timeout=180), 60 / PER_MINUTE
    with open(DONE, "a", encoding="utf-8") as out:
        for batch in batches(todo):
            started = time.time()
            for attempt in range(3):
                try:
                    answer, limit = call_model(client, key, batch)
                except (httpx.HTTPError, ValueError, KeyError, json.JSONDecodeError) as error:
                    print("retrying after:", repr(error)[:200], flush=True)
                    time.sleep(10 * (attempt + 1))
                    continue
                if answer is None:
                    print("Free limit reached. Run this again after the quota resets:", limit, flush=True)
                    return
                for unit, simple in zip(batch, answer):
                    faults, warnings = check_rewrite(unit["m"], str(simple))
                    tries = done.get(unit["h"], {}).get("tries", 0) + 1
                    record = {"h": unit["h"], "ok": not faults, "tries": tries, "faults": faults, "warnings": warnings, **({"s": str(simple)} if not faults else {})}
                    done[unit["h"]] = record
                    out.write(json.dumps(record, ensure_ascii=False) + "\n")
                out.flush()
                print(f"{time.strftime('%H:%M:%S')} saved {len(batch)}; accepted so far {sum(1 for r in done.values() if r.get('ok')):,}", flush=True)
                break
            time.sleep(max(0, gap - (time.time() - started)))


def test():
    source = "The `client` must not exceed 5 retries unless RunnableConfig sets max_retries. See [docs](https://x.y/z)."
    masked, spans = protect(source)
    good = masked.replace("The ", "Your ")
    bad = {"lost mark": masked.replace("⟦0⟧", ""), "number": masked.replace("5", "7"), "name": masked.replace("max_retries", "the limit"), "short": "Too short."}
    assert spans[0] == "`client`" and not check_rewrite(masked, good)[0], check_rewrite(masked, good)
    for label, text in bad.items():
        assert check_rewrite(masked, text)[0], label
    assert check_rewrite(masked, masked.replace("must not", "must"))[1]
    print("safety checks passed")


{"collect": collect, "run": run, "test": test}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
