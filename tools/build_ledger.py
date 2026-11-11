"""Stage 1: split the saved docs into pages and record every page and API item in coverage.json."""
import ast
import collections
import json
import pathlib
import re
import xml.etree.ElementTree as ElementTree

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "source" / "raw"
PAGES = ROOT / "source" / "pages"
SITE_PACKAGES = ROOT / ".venv" / "Lib" / "site-packages"
RESERVED = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}
VERBS = {"get", "post", "put", "patch", "delete"}
SDK_PACKAGES = ["langchain", "langchain_core", "langgraph", "langgraph_sdk", "langsmith",
                "deepagents", "managed_deepagents"]
ENDPOINT_LINE = re.compile(r"^\S*(?:openapi\S*\.json)\s+(get|post|put|patch|delete)\s+(/\S*)", re.I)
HEADER = re.compile(r"^# (.+)\r?\nSource: (https://docs\.langchain\.com\S*)\r?$", re.M)


def safe_path(url: str) -> pathlib.Path:
    parts = url.split("docs.langchain.com", 1)[1].strip("/").split("/") or ["index"]
    clean = []
    for part in parts:
        part = re.sub(r"[^A-Za-z0-9._-]", "_", part) or "index"
        clean.append(part + "_" if part.lower() in RESERVED else part)
    return pathlib.Path(*clean).with_suffix(".md")


def classify(url: str, body: str) -> tuple[str, str]:
    path = url.split("docs.langchain.com", 1)[1].lower()
    first = next((line for line in body.splitlines() if line.strip()), "")
    if ENDPOINT_LINE.match(first.strip()):
        return "reference", "rest-endpoint"
    if "/javascript/" in path:
        return "merged", "typescript-copy"
    if re.search(r"release-notes|changelog|/migrate|/versions?\b", path):
        return "merged", "history"
    if "/integrations/" in path:
        return "reference", "integration"
    if "/reference/" in path or "/cli" in path or path.startswith("/api-reference"):
        return "reference", "sdk-or-cli"
    return "lesson", "guide"


def spec_operations() -> list[dict]:
    operations = []
    for spec_file in sorted((RAW / "openapi").glob("*")):
        spec = json.loads(spec_file.read_text(encoding="utf-8"))
        for route, item in spec.get("paths", {}).items():
            for verb in item:
                if verb in VERBS:
                    operations.append({"spec": spec_file.name, "verb": verb, "path": route,
                                       "status": "todo"})
    return operations


def sdk_items() -> list[dict]:
    items = []
    for package in SDK_PACKAGES:
        for source in sorted((SITE_PACKAGES / package).rglob("*.py")):
            relative = source.relative_to(SITE_PACKAGES).with_suffix("")
            parts = [p for p in relative.parts if p != "__init__"]
            if any(p.startswith("_") or p in {"tests", "testing"} for p in parts):
                continue
            try:
                tree = ast.parse(source.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError):
                continue
            module = ".".join(parts)
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
                    items.append({"package": package, "name": f"{module}.{node.name}", "kind": "function",
                                  "status": "todo"})
                elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                    items.append({"package": package, "name": f"{module}.{node.name}", "kind": "class",
                                  "status": "todo"})
                    for member in node.body:
                        if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)) and not member.name.startswith("_"):
                            items.append({"package": package, "name": f"{module}.{node.name}.{member.name}",
                                          "kind": "method", "status": "todo"})
    return items


text = (RAW / "llms-full.txt").read_text(encoding="utf-8")
matches = list(HEADER.finditer(text))
pages, repeated = {}, 0
for index, match in enumerate(matches):
    end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
    title, url = match.group(1), match.group(2).rstrip("/")
    body = text[match.end():end].strip()
    if url in pages:
        repeated += 1
    tier, kind = classify(url, body)
    relative = safe_path(url)
    target = PAGES / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(f"# {title}\nSource: {url}\n\n{body}\n", encoding="utf-8")
    pages[url] = {"title": title, "file": relative.as_posix(), "tier": tier, "kind": kind,
                  "words": len(body.split()), "status": "todo"}

operations, sdk = spec_operations(), sdk_items()
tree = ElementTree.parse(RAW / "sitemap.xml")
sitemap = {e.text.strip().rstrip("/") for e in tree.iter() if e.tag.endswith("loc")}
(ROOT / "coverage.json").write_text(json.dumps(
    {"pages": pages, "rest_operations": operations, "sdk_items": sdk}, indent=1), encoding="utf-8")

print(f"pages: {len(pages)} (repeated headers: {repeated})")
print("by tier/kind:", dict(collections.Counter(f"{p['tier']}/{p['kind']}" for p in pages.values())))
words = collections.Counter()
for page in pages.values():
    words[page["tier"]] += page["words"]
print("words by tier:", dict(words))
print("REST operations:", dict(collections.Counter(o["spec"] for o in operations)))
print("unique REST operations:", len({(o["verb"], o["path"]) for o in operations}))
print("SDK items:", dict(collections.Counter(i["kind"] for i in sdk)))
print("SDK by package:", dict(collections.Counter(i["package"] for i in sdk)))
print(f"sitemap: {len(sitemap)}; only in sitemap: {len(sitemap - set(pages))}; only in pages: {len(set(pages) - sitemap)}")
print("sample only in sitemap:", sorted(sitemap - set(pages))[:5])
