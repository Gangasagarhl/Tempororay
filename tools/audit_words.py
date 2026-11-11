"""Word-by-word check: compare every saved source with the page built from it.

Usage: audit_words.py [data folder]. Writes audit_report.json with every word that went missing.
"""
import collections
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools.textcheck import FENCE_LINE, fence_label, item_text, leaves, tokens  # noqa: E402

DATA = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "site" / "data"
PAGES, RAW, REFERENCE = ROOT / "source" / "pages", ROOT / "source" / "raw", ROOT / "source" / "reference"
audit_map = json.loads((DATA / "audit_map.json").read_text(encoding="utf-8"))
ledger = json.loads((ROOT / "coverage.json").read_text(encoding="utf-8"))
specs = {p.name: json.loads(p.read_text(encoding="utf-8")) for p in (RAW / "openapi").glob("*")}
BOILERPLATE = re.compile(r"^\[Connect these docs\].*$|^\s*</?(Warning|Note|Tip|Info|Check|Accordion\w*|Tabs?|Steps?|Card\w*|CodeGroup|Frame|Callout)\s*/?>\s*$", re.M)
MARKUP = re.compile(r"(?m)^\s*(?:!!!|\?\?\?\+?|===)\s+|^[\s>]*\[(?:card|tab)\]\s*")


def expand(node, spec, visited):
    if isinstance(node, dict):
        if "$ref" in node:
            if node["$ref"] in visited:
                return {}
            visited.add(node["$ref"])
            target = spec
            for part in node["$ref"].lstrip("#/").split("/"):
                target = target.get(part.replace("~1", "/"), {})
            siblings = {k: expand(v, spec, visited) for k, v in node.items() if k != "$ref"}
            return {**expand(target, spec, visited), **siblings}
        return {k: expand(v, spec, visited) for k, v in node.items()}
    if isinstance(node, list):
        return [expand(v, spec, visited) for v in node]
    return node


counts = collections.Counter()
lost_examples = collections.defaultdict(list)
lost_words = collections.Counter()
pages_seen = set()
rest_words, source_ops = set(), set()


def report(kind, identifier, missing):
    counts[kind + " checked"] += 1
    if missing:
        counts[kind + " with missing words"] += 1
        counts[kind + " missing words"] += sum(missing.values()) if isinstance(missing, collections.Counter) else len(missing)
        lost_words.update(missing)
        if len(lost_examples[kind]) < 60:
            lost_examples[kind].append({"id": identifier, "missing": sorted(missing)[:40]})


for chunk in sorted((DATA / "chunks").glob("*.js"), key=lambda p: p.stem):
    text = chunk.read_text(encoding="utf-8").strip()
    items = json.loads(text[text.index(",") + 1:-2])
    for identifier, item in items.items():
        source = audit_map.get(identifier)
        words = tokens(item_text(item))
        if item.get("kind", "").startswith("API simulator"):
            rest_words.update(words)
        if not source:
            continue
        if "page" in source:
            pages_seen.add(source["page"])
            raw = (PAGES / source["page"]).read_text(encoding="utf-8")
            body = raw.split("\n", 2)[2] if raw.count("\n") >= 2 else raw
            body = FENCE_LINE.sub(lambda m: m[1] + fence_label(m[3]), body)
            report("docs page", identifier, collections.Counter(tokens(MARKUP.sub("", BOILERPLATE.sub("", body)))) - collections.Counter(words))
        elif "spec" in source:
            spec = specs[source["spec"]]
            path_item = spec["paths"][source["route"]]
            op = {**path_item[source["verb"]], "parameters": [*path_item.get("parameters", []), *path_item[source["verb"]].get("parameters", [])]}
            needed = {w for _, value in leaves(expand(op, spec, set())) for w in tokens(value)}
            report("REST operation", identifier, needed - set(words))
            source_ops.add((source["spec"], source["verb"], source["route"]))
        elif "ref" in source:
            record = json.loads((REFERENCE / source["ref"]).read_text(encoding="utf-8"))["data"]
            needed = {w for _, value in leaves(record) for w in tokens(value)}
            report("API reference page", identifier, needed - set(words))

unbuilt_pages = [m["file"] for m in ledger["pages"].values() if m["file"] not in pages_seen and m["kind"] != "rest-endpoint"]
spec_lost = {}
for name, spec in specs.items():
    needed = {w for _, value in leaves({k: v for k, v in spec.items() if k != "paths"}) for w in tokens(value)}
    spec_lost[name] = sorted(needed - rest_words)[:40]
    counts["spec-level words missing"] += len(needed - rest_words)
all_ops = {(n, v, r) for n, s in specs.items() for r, p in s.get("paths", {}).items() for v in ("get", "post", "put", "patch", "delete") if v in p}
result = {"counts": dict(counts), "docs pages not built": unbuilt_pages[:50], "docs pages not built count": len(unbuilt_pages),
          "REST operations not built": len(all_ops - source_ops), "most often lost": lost_words.most_common(60), "examples": lost_examples, "spec level": spec_lost}
(DATA / "audit_report.json").write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
print(json.dumps({k: result[k] for k in ("counts", "docs pages not built count", "REST operations not built", "most often lost")}, ensure_ascii=False))
for kind, rows in lost_examples.items():
    print(kind, json.dumps(rows[:4], ensure_ascii=False)[:900])
