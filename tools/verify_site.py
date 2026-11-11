"""Check the built lab: every page reachable, valid steps, full coverage, real imports in hand-written code.

Usage: verify_site.py [data folder]
"""
import ast
import collections
import importlib
import json
import pathlib
import re
import sys
import xml.etree.ElementTree as ElementTree

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from content.scenarios import SIMS  # noqa: E402

DATA = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "site" / "data"
ledger = json.loads((ROOT / "coverage.json").read_text(encoding="utf-8"))
catalog = json.loads(re.sub(r";\s*$", "", (DATA / "catalog.js").read_text(encoding="utf-8")).split("=", 1)[1])
urls = json.loads((DATA / "urls.json").read_text(encoding="utf-8"))

rows = {}
for group in catalog["groups"]:
    for section in group["sections"]:
        if "r" in section:
            section_rows = section["r"]
        else:
            text = (DATA / "sec" / f"{section['f']}.js").read_text(encoding="utf-8").strip()
            section_rows = json.loads(text[text.index(",") + 1:-2])
        if len(section_rows) != section["n"]:
            sys.exit(f"section count wrong: {section['title']}")
        rows.update({row[0]: row for row in section_rows})

problems, ids_in_files, wrong_file = [], set(), 0
steps_total = table_links = dead_links = 0
valid_ids = set(rows)
for chunk in (DATA / "chunks").glob("*.js"):
    text = chunk.read_text(encoding="utf-8").strip()
    items = json.loads(text[text.index(",") + 1:-2])
    for identifier, item in items.items():
        ids_in_files.add(identifier)
        if identifier in rows and rows[identifier][4] != int(chunk.stem):
            wrong_file += 1
        steps = item.get("steps") or []
        steps_total += len(steps)
        if not steps:
            problems.append(f"{identifier} has no steps")
        for step in [*steps, *(s for branch in (item.get("paths") or {}).values() for s in branch)]:
            if not step.get("h") or "t" not in step:
                problems.append(f"{identifier} has an empty step")
            for choice in step.get("choices", []):
                if choice["path"] not in item.get("paths", {}):
                    problems.append(f"{identifier} has a broken choice")
            if step.get("l"):
                code = (item.get("codes") or {}).get(step.get("cr")) if step.get("cr") else step.get("code", item.get("code"))
                if step["l"][0] > (code or "").count("\n") + 1:
                    problems.append(f"{identifier} highlights a line past the end")
            for row in (step.get("table") or {}).get("rows", []):
                for value in row:
                    if isinstance(value, dict):
                        table_links += 1
                        dead_links += value.get("i") not in valid_ids
            for link in re.findall(r"\]\(#/([^)]+)\)", step.get("t", "")):
                table_links += 1
                dead_links += link not in valid_ids
if ids_in_files != valid_ids:
    problems.append(f"catalog and data files disagree: {len(ids_in_files - valid_ids)} extra, {len(valid_ids - ids_in_files)} missing")
if wrong_file:
    problems.append(f"{wrong_file} topics point at the wrong data file")

titles = {r[1] for r in rows.values()} | {r[3] for r in rows.values()}
missing_pages = [u for u in ledger["pages"] if u.split("docs.langchain.com", 1)[1].rstrip("/") not in urls]
unique_ops = {(o["verb"], o["path"]) for o in ledger["rest_operations"]}
missing_ops = [o for o in unique_ops if f"{o[0].upper()} {o[1]}"[:90] not in titles]

import_errors = []
for sim in SIMS:
    if sim["lang"] != "python" or not sim["code"]:
        continue
    for node in ast.walk(ast.parse(sim["code"])):
        if isinstance(node, ast.ImportFrom):
            try:
                module = importlib.import_module(node.module)
            except Exception as error:
                import_errors.append(f"{sim['key']}: {node.module}: {error}")
                continue
            import_errors += [f"{sim['key']}: {node.module}.{a.name} missing" for a in node.names if not hasattr(module, a.name)]

print(f"topics: {len(rows):,}   steps: {steps_total:,}")
print(f"docs pages missing: {len(missing_pages)}   REST operations missing: {len(missing_ops)}")
print(f"structure problems: {len(problems)} {problems[:6]}")
print(f"hand-written import errors: {len(import_errors)} {import_errors[:8]}")
print(f"links: {table_links:,}   pointing nowhere: {dead_links:,}")

REF = ROOT / "source" / "reference"
if (REF / "sitemap.xml").exists():
    root = "https://reference.langchain.com"
    sitemap = {e.text.strip().rstrip("/") for e in ElementTree.parse(REF / "sitemap.xml").iter() if e.tag.endswith("loc")}
    missing = sorted(u for u in sitemap if u.replace(root, "") and u.replace(root, "") not in urls)
    print(f"sitemap urls: {len(sitemap):,}   not in the lab: {len(missing):,}")
    print("  by language:", dict(collections.Counter(u.replace(root, "").split("/")[1] for u in missing)), missing[:4])
    full = sorted(set(re.findall(root.replace(".", r"\.") + r"(/[^)\s]+?)(?:\.md)?\)", (REF / "llms-full.txt").read_text(encoding="utf-8"))))
    gone = [u for u in full if u.rstrip("/") not in urls]
    print(f"llms-full links: {len(full):,}   not in the lab: {len(gone):,} {gone[:4]}")
    kinds = collections.Counter()
    for line in (REF / "problems.jsonl").read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        kinds[f"{record['kind']}:{(record['url'].replace(root, '').split('/') + ['', ''])[1]}"] += 1
    print("crawl problems:", dict(kinds))
    print("reference pages by kind:", dict(collections.Counter(r[2] for r in rows.values() if r[2].startswith("API reference")).most_common(14)))
