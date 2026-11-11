"""Save reference.langchain.com for offline use. Resumable, and only 6 requests at a time."""
import hashlib
import json
import pathlib
import queue
import re
import threading
import time
import urllib.parse
import xml.etree.ElementTree as ElementTree

import httpx

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "source" / "reference"
RECORDS = OUT / "records"
SITE = "https://reference.langchain.com"
HEADERS = {"User-Agent": "langchain-lab-fetch/1.0", "Accept": "application/json"}
WORKERS = 6
RECORDS.mkdir(parents=True, exist_ok=True)

lock = threading.Lock()
seen, followed, work = set(), set(), queue.PriorityQueue()
stats = {"saved": 0, "resumed": 0, "duplicate": 0, "missing": 0, "mismatch": 0, "failed": 0, "started": time.time()}
index_file = open(OUT / "index.jsonl", "a", encoding="utf-8")
problems_file = open(OUT / "problems.jsonl", "a", encoding="utf-8")


def record_path(url):
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()
    return RECORDS / digest[:2] / f"{digest}.json"


def add(url, derived):
    with lock:
        if url in seen:
            return
        seen.add(url)
    work.put((url.count("/"), url, derived))  # shortest addresses first, so an item is kept at its real address


def problem(kind, url, detail=""):
    with lock:
        stats[kind] += 1
        problems_file.write(json.dumps({"kind": kind, "url": url, "detail": str(detail)[:200]}) + "\n")
        problems_file.flush()


def children(url, data):
    """Queue the pages this record points to, including those missing from the sitemap."""
    record_id = data.get("id")
    if record_id:  # the site can show one item at many addresses; follow its links only once
        with lock:
            if record_id in followed:
                stats["duplicate"] += 1
                return
            followed.add(record_id)
    if "package" in data:
        slug = url.rstrip("/").rsplit("/", 1)[-1]
        import_root = slug.replace("-", "_")
        for symbol in data.get("symbols", []):
            name = symbol.get("qualifiedName", "")
            if symbol.get("kind") == "alias" or not name.startswith(import_root + "."):
                continue
            add(url.rstrip("/") + "/" + urllib.parse.quote(name[len(import_root) + 1:].replace(".", "/")), True)
    for package in data.get("packages", []) if isinstance(data.get("packages"), list) else []:
        if package.get("url"):
            add(SITE + package["url"], False)
    for member in data.get("members", []) or []:
        if member.get("kind") == "alias" or member.get("visibility") not in (None, "public"):
            continue
        name = member.get("name")
        if name and not name.startswith("_"):
            add(url.rstrip("/") + "/" + urllib.parse.quote(name), True)


def valid(url, data, derived):
    if not isinstance(data, dict):
        return False
    if "package" in data or "packages" in data:
        return True
    if "id" not in data or "kind" not in data:
        return False
    if derived:
        last = urllib.parse.unquote(url.rstrip("/").rsplit("/", 1)[-1]).lower()
        return str(data.get("name", "")).lower().split(".")[-1] == last
    return True


def worker():
    client = httpx.Client(headers=HEADERS, timeout=60, follow_redirects=True)
    while True:
        _, url, derived = work.get()
        try:
            path = record_path(url)
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))["data"]
                with lock:
                    stats["resumed"] += 1
                children(url, data)
                continue
            for attempt in range(6):
                try:
                    response = client.get(url)
                except httpx.HTTPError as error:
                    if attempt == 5:
                        problem("failed", url, error)
                        response = None
                        break
                    time.sleep(2 ** attempt)
                    continue
                if response.status_code == 429 or response.status_code >= 500 and "No build" not in response.text and "not found" not in response.text.lower():
                    if attempt == 5:
                        problem("failed", url, response.status_code)
                        response = None
                        break
                    time.sleep(float(response.headers.get("retry-after", 2 ** attempt + 1)))
                    continue
                break
            if response is None:
                continue
            if response.status_code != 200 or "json" not in response.headers.get("content-type", ""):
                problem("missing", url, f"{response.status_code} {response.text[:80]}")
                continue
            data = response.json()
            if not valid(url, data, derived):
                problem("mismatch", url, data.get("qualifiedName") if isinstance(data, dict) else "not an object")
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"url": url, "derived": derived, "data": data}, ensure_ascii=False), encoding="utf-8")
            with lock:
                stats["saved"] += 1
                index_file.write(json.dumps({"url": url, "derived": derived}) + "\n")
                index_file.flush()
                done = stats["saved"]
            children(url, data)
            if done % 2000 == 0:
                rate = done / (time.time() - stats["started"])
                print(f"{time.strftime('%H:%M:%S')} saved={done} queued={work.qsize()} seen={len(seen)} per_second={rate:.1f} {stats}", flush=True)
        except Exception as error:  # keep the crawl going and record what went wrong
            problem("failed", url, repr(error))
        finally:
            work.task_done()


client = httpx.Client(headers={"User-Agent": HEADERS["User-Agent"]}, timeout=120)
sitemap_bytes = client.get(f"{SITE}/sitemap.xml").content
(OUT / "sitemap.xml").write_bytes(sitemap_bytes)
sitemap = sorted({e.text.strip().rstrip("/") for e in ElementTree.fromstring(sitemap_bytes).iter() if e.tag.endswith("loc")})
llms = client.get(f"{SITE}/llms.txt").text
(OUT / "llms.txt").write_text(llms, encoding="utf-8")
llms_full = client.get(f"{SITE}/llms-full.txt").text
(OUT / "llms-full.txt").write_text(llms_full, encoding="utf-8")
packages = [m[:-3] for m in re.findall(r"\((https://reference\.langchain\.com/[^)\s]+\.md)\)", llms)]
print(f"sitemap urls {len(sitemap)}; llms package entries {len(packages)}", flush=True)
for lang in ("python", "javascript", "java", "go"):
    add(f"{SITE}/{lang}", False)
for url in [*packages, *sitemap]:
    add(url, False)
for _ in range(WORKERS):
    threading.Thread(target=worker, daemon=True).start()
work.join()
summary = {**stats, "seen": len(seen), "minutes": round((time.time() - stats["started"]) / 60, 1)}
(OUT / "crawl_report.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
print("CRAWL FINISHED", summary, flush=True)
