"""Add the live docs pages that llms-full.txt leaves out, using the docs repository to find them. Safe to rerun."""
import concurrent.futures
import json
import pathlib
import re
import sys
import time

import httpx

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
REPO_SRC = ROOT / "source" / "docs_repo" / "src"
PAGES = ROOT / "source" / "pages"
RAW = ROOT / "source" / "raw"
SITE = "https://docs.langchain.com"
HEADERS = {"User-Agent": "langchain-lab-fetch/1.0"}
RESERVED = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}
PREAMBLE = re.compile(r"\A(?:>.*\n)+\s*")
ledger_path = ROOT / "coverage.json"
ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
client = httpx.Client(headers=HEADERS, timeout=60, follow_redirects=True)


def safe_path(url):
    parts = url.split("docs.langchain.com", 1)[1].strip("/").split("/") or ["index"]
    clean = []
    for part in parts:
        part = re.sub(r"[^A-Za-z0-9._-]", "_", part) or "index"
        clean.append(part + "_" if part.lower() in RESERVED else part)
    return pathlib.Path(*clean).with_suffix(".md")


def classify(url):
    path = url.split("docs.langchain.com", 1)[1].lower()
    if "/javascript/" in path:
        return "merged", "typescript-copy"
    if re.search(r"release-notes|changelog|/migrate|/versions?\b", path):
        return "merged", "history"
    if "/integrations/" in path:
        return "reference", "integration"
    if "/reference/" in path or "/cli" in path:
        return "reference", "sdk-or-cli"
    return "lesson", "guide"


candidates = set()
for source in REPO_SRC.rglob("*.mdx"):
    relative = source.relative_to(REPO_SRC).with_suffix("").as_posix()
    if relative.startswith(("snippets/", "code-samples/")) or "/snippets/" in relative:
        continue
    relative = re.sub(r"(^|/)index$", "", relative)
    if relative.startswith("oss/") and not relative.startswith(("oss/python", "oss/javascript")):
        candidates.update({f"oss/python/{relative[4:]}", f"oss/javascript/{relative[4:]}"})
    else:
        candidates.add(relative)
known = {u.split("docs.langchain.com", 1)[1].strip("/") for u in ledger["pages"]}
todo = sorted(c for c in candidates if c and c not in known)
print(f"pages in repository: {len(candidates)}   already saved: {len(candidates) - len(todo)}   to try: {len(todo)}", flush=True)


def fetch(path):
    url = f"{SITE}/{path}"
    for attempt in range(5):
        try:
            response = client.get(url + ".md")
        except httpx.HTTPError:
            time.sleep(2 ** attempt)
            continue
        if response.status_code == 429 or response.status_code >= 500:
            time.sleep(float(response.headers.get("retry-after", 2 ** attempt + 1)))
            continue
        if response.status_code != 200 or "markdown" not in response.headers.get("content-type", ""):
            return path, "missing", None
        if str(response.url).removesuffix(".md").rstrip("/") != url:
            return path, "redirected", None
        return path, "saved", response.text
    return path, "failed", None


outcome = {"saved": 0, "missing": 0, "redirected": 0, "failed": 0}
failed = []
with concurrent.futures.ThreadPoolExecutor(4) as pool:
    for path, status, text in pool.map(fetch, todo):
        outcome[status] += 1
        if status == "failed":
            failed.append(path)
        if status != "saved":
            continue
        body = PREAMBLE.sub("", text.replace("\r\n", "\n"), count=1).strip()
        match = re.match(r"# (.+)\n", body)
        title = match.group(1).strip() if match else path.rsplit("/", 1)[-1].replace("-", " ").capitalize()
        body = body[match.end():].strip() if match else body
        url = f"{SITE}/{path}"
        relative = safe_path(url)
        target = PAGES / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"# {title}\nSource: {url}\n\n{body}\n", encoding="utf-8")
        tier, kind = classify(url)
        ledger["pages"][url] = {"title": title, "file": relative.as_posix(), "tier": tier, "kind": kind, "words": len(body.split()), "status": "extra"}

spec_url = "https://api.smith.langchain.com/openapi.json"
spec = client.get(spec_url)
spec.raise_for_status()
(RAW / "openapi" / "4_api.smith.langchain.com_openapi.json").write_bytes(spec.content)
ledger_path.write_text(json.dumps(ledger, indent=1), encoding="utf-8")
print("result:", outcome, "failed:", failed, "total pages now:", len(ledger["pages"]), "spec bytes:", len(spec.content), flush=True)
