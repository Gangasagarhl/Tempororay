"""Build every simulation from the saved docs, API specs, CLI help and installed package code."""
import ast
import collections
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import textwrap

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
if os.name == "nt":  # run at below-normal priority so the PC stays usable during long builds
    import ctypes
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
from content.glossary import GLOSSARY  # noqa: E402
from content.scenarios import SIMS  # noqa: E402
from tools.textcheck import add_leftovers, fence_label, protect, restore, unit_hash  # noqa: E402

RAW, PAGES = ROOT / "source" / "raw", ROOT / "source" / "pages"
FINAL_DATA = ROOT / "site" / "data"
SITE_DATA = pathlib.Path(os.environ.get("LAB_OUT") or ROOT / "site" / "data.new")
CHUNKS = SITE_DATA / "chunks"
SITE_PACKAGES = ROOT / ".venv" / "Lib" / "site-packages"
SDK_PACKAGES = ["langchain", "langchain_core", "langgraph", "langgraph_sdk", "langsmith", "deepagents",
                "managed_deepagents"]
VERBS = ("get", "post", "put", "patch", "delete")
ledger = json.loads((ROOT / "coverage.json").read_text(encoding="utf-8"))


def short(node, limit=70):
    text = re.sub(r"\s+", " ", ast.unparse(node))
    return text if len(text) <= limit else text[:limit - 1] + "…"


def narrate(node):
    """Describe one Python statement in plain words: (headline, text)."""
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        names = ", ".join(a.name for a in node.names)
        origin = f" from `{node.module}`" if isinstance(node, ast.ImportFrom) and node.module else ""
        return "Bring in code", f"Python loads `{names}`{origin} so later lines can use it. Nothing else runs yet."
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return f"Define {node.name}", f"Python remembers a function called `{node.name}`. Its inside does not run until something calls it."
    if isinstance(node, ast.ClassDef):
        return f"Define {node.name}", f"Python remembers a class called `{node.name}`, a blueprint for making objects."
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        target = short(node.targets[0] if isinstance(node, ast.Assign) else node.target, 40)
        value = node.value
        if value is None:
            return f"Declare {target}", f"This says `{target}` exists and what type it should be. No value is stored."
        if isinstance(value, ast.Call):
            return f"Store a result in {target}", f"Python runs `{short(value)}` and keeps what comes back under the name `{target}`."
        if isinstance(value, ast.Await):
            return f"Wait, then store in {target}", f"Python waits for `{short(value.value)}` to finish and stores the result in `{target}`."
        return f"Store a value in {target}", f"Python stores `{short(value)}` under the name `{target}`."
    if isinstance(node, ast.AugAssign):
        return f"Update {short(node.target, 40)}", f"Python changes `{short(node.target)}` using `{short(node.value)}`."
    if isinstance(node, ast.Expr):
        value = node.value
        if isinstance(value, ast.Await):
            return "Wait for work to finish", f"Python pauses here until `{short(value.value)}` is done, letting other work run meanwhile."
        if isinstance(value, (ast.Yield, ast.YieldFrom)):
            return "Hand over one piece", f"The function gives back `{short(value)}` and pauses until the next piece is asked for."
        if isinstance(value, ast.Call):
            return "Run a call", f"Python runs `{short(value)}`. Whatever it returns is not kept."
        return "Evaluate", f"Python works out `{short(value)}`."
    if isinstance(node, ast.If):
        return "Make a decision", f"Python checks `{short(node.test)}`. If that's true, the indented lines run. Otherwise it skips them."
    if isinstance(node, (ast.For, ast.AsyncFor)):
        return "Repeat for each item", f"Python goes through `{short(node.iter)}` one item at a time, calling each one `{short(node.target, 30)}`."
    if isinstance(node, ast.While):
        return "Repeat while true", f"Python repeats the indented lines as long as `{short(node.test)}` stays true."
    if isinstance(node, (ast.With, ast.AsyncWith)):
        return "Open something, use it, close it", f"Python sets up `{short(node.items[0].context_expr)}`, runs the indented lines, and cleans up afterwards."
    if isinstance(node, ast.Try):
        return "Try something risky", "Python tries the indented lines. If an error happens, it jumps to the matching `except` part."
    if isinstance(node, ast.Return):
        return ("Hand back the result", f"The function ends and gives back `{short(node.value)}`.") if node.value else ("Finish", "The function ends and gives back nothing.")
    if isinstance(node, ast.Raise):
        return ("Stop with an error", f"The function stops and reports the error `{short(node.exc)}`.") if node.exc else ("Stop with an error", "The current error is passed on.")
    if isinstance(node, ast.Assert):
        return "Check a rule", f"Python confirms that `{short(node.test)}` is true, and stops with an error if it isn't."
    if isinstance(node, ast.Pass):
        return "Do nothing", "`pass` is an empty placeholder."
    return "Next statement", f"Python runs this statement: `{short(node)}`."


def code_steps(code, heading, lang="python"):
    """One step per top-level statement, with the running line highlighted."""
    try:
        body = ast.parse(code).body
    except SyntaxError:
        return None
    if not body or len(body) > 14:
        return None
    steps = []
    for node in body:
        head, text = narrate(node)
        steps.append({"h": head, "t": text, "code": code, "lang": lang, "codeTitle": heading,
                      "l": [node.lineno, node.end_lineno]})
    return steps


# ---------------- Guides ----------------
FENCE = re.compile(r"^\s*```+\s*([\w+-]*)(.*)$")


def clean_lines(text):
    out, block = [], []

    def flush():
        nonlocal block
        if not block:
            return
        if re.match(r"^\s*>\s*\[!\w+\]", block[0]):
            out.extend(block)
        else:
            for line in block:
                line = re.sub(r"^(\s*>\s?)+", "", line)
                line = re.sub(r"^\[card\]\s*", "- ", line)
                line = re.sub(r"^\[tab\]\s*(.*)$", r"**\1**", line)
                out.append(line)
        block = []

    for line in text.splitlines():
        if line.lstrip().startswith(">"):
            block.append(line)
        else:
            flush()
            out.append(line)
    flush()
    return out


CDN_FILE = re.compile(r"https://mintcdn\.com/[^/]+/[^/]+/([^?\s)\"']+)[^)\s\"']*")
HTML_IMAGE = re.compile(r"<img\b[^>]*?\bsrc=[\"']([^\"']+)[\"'][^>]*?>")


def local_pictures(body):
    """Point pictures at the copies saved beside the lab, so they show without internet."""
    def as_markdown(match):
        alt = re.search(r"\balt=[\"']([^\"']*)[\"']", match[0])
        return f"![{alt[1] if alt else ''}]({match[1]})"
    body = HTML_IMAGE.sub(as_markdown, CDN_FILE.sub(r"media/\1", body))
    return re.sub(r"(!\[[^\]]*\]\()/((?:[\w.-]+/)*images/)", r"\1media/\2", body)


def guide_item(meta, text, python_first):
    body = local_pictures(text.split("\n", 2)[2] if text.count("\n") >= 2 else text)
    body = re.sub(r"(?m)^([\s>]*)\[card\]\s*", r"\1- ", body)
    body = re.sub(r"(?m)^([\s>]*)\[tab\]\s*(.*)$", r"\1**\2**", body)
    lines = clean_lines(body)
    steps, buf, heading, intro, i = [], [], meta["title"], "", 0

    unused_heading = False

    def flush():
        nonlocal buf, intro, unused_heading
        joined = "\n".join(buf).strip()
        buf = []
        if not joined or joined.startswith("[Connect these docs]") or joined in {"***", "---"}:
            return
        unused_heading = False
        words, group = 0, []
        for para in re.split(r"\n\s*\n", joined):
            count = len(para.split())
            if group and words + count > 130:
                steps.append({"h": heading, "t": "\n\n".join(group)})
                group, words = [], 0
            group.append(para)
            words += count
        if group:
            steps.append({"h": heading, "t": "\n\n".join(group)})

    while i < len(lines):
        line = lines[i]
        fence = FENCE.match(line)
        if fence and "```" in line:
            lang = fence.group(1).lower()
            block_label = fence_label(fence.group(2))
            i += 1
            chunk = []
            while i < len(lines) and not re.match(r"^\s*```+\s*$", lines[i]):
                chunk.append(lines[i])
                i += 1
            i += 1
            code = textwrap.dedent("\n".join(chunk)).strip("\n")
            flush()
            unused_heading = False
            if lang in {"python", "py"}:
                made = code_steps(code, f"{heading} · {block_label}" if block_label else heading)
                if made:
                    steps.extend(made)
                    continue
            label = "Run this command" if lang in {"bash", "sh", "shell", "powershell"} else "Read this example"
            if python_first and lang in {"ts", "typescript", "js", "javascript", "tsx", "jsx"}:
                label = "The same example in TypeScript"
            steps.append({"h": heading, "t": f"**{label}.**", "code": code, "lang": "python" if lang in {"python", "py"} else "text",
                          "codeTitle": block_label or lang or "Example"})
            continue
        head = re.match(r"^(#{2,6})\s+(.*)$", line)
        if head:
            flush()
            title_words = re.sub(r"[`*]", "", head.group(2)).strip()
            heading = f"{heading}: {title_words}" if unused_heading else title_words
            unused_heading = True
        elif re.match(r"^\s*</?(Warning|Note|Tip|Info|Check|Accordion\w*|Tabs?|Steps?|Card\w*|CodeGroup|Frame|Callout)\s*/?>\s*$", line):
            pass
        else:
            buf.append(line)
        i += 1
    flush()
    if unused_heading:
        steps.append({"h": heading, "t": "This section has only this heading on the original page."})
    if steps and "code" not in steps[0]:
        intro, steps = steps[0]["t"].split("\n\n")[0][:320], steps
    if not steps:
        steps = [{"h": meta["title"], "t": "This page has no further content in the saved docs."}]
    return {"title": meta["title"], "kind": "Saved docs, step by step", "intro": "", "actors": [], "code": "", "steps": steps,
            "source": meta["file"]}


def module_for(url):
    path = url.split("docs.langchain.com", 1)[1].lower()
    if "/javascript/" in path:
        return "ts"
    if "managed-deep-agents" in path:
        return "m4"
    if "/integrations/" in path:
        return "integrations"
    if "/deepagents/code" in path or "/dcode" in path:
        return "m10"
    if "/python/langchain" in path or "/oss/langchain" in path:
        return "m1"
    if "/python/langgraph" in path or "/oss/langgraph" in path:
        return "m2"
    if "deepagents" in path:
        return "m3"
    slug = path.rsplit("/", 1)[-1]
    rules = [
        ("m10", r"llm-gateway|fleet|engine"), ("m9", r"agent-registry|agent-environment|navigate-agents|create-an-agent"),
        ("m7", r"eval|dataset|experiment|annotation|prompt|judge|pairwise|benchmark"),
        ("m8", r"deploy|cloud|hybrid|self-host|kubernetes|byoc|standalone|control-plane|data-plane|docker|helm|aws|azure|gcp|scale"),
        ("m11", r"rbac|abac|sso|audit|admin|billing|usage|workspace|organization|user-|api-key|account|team|govern|compliance|retention|secret|setup"),
        ("m5", r"agent-server|assistant|studio|local-|thread|run|cron|webhook|stream|remote-graph|mcp|a2a|double-text|interrupt|auth"),
        ("m6", r"trac|observab|dashboard|alert|insight|rules|feedback|log-|metadata|monitor|filter|view-"),
    ]
    for module, pattern in rules:
        if re.search(pattern, slug):
            return module
    return "other"


def section_for(url):
    parts = url.split("docs.langchain.com", 1)[1].strip("/").split("/")
    if len(parts) >= 2 and parts[-2] not in {"python", "javascript", "langsmith", "oss"}:
        return parts[-2].replace("-", " ").capitalize()
    return parts[-1].split("-")[0].capitalize()


# ---------------- REST ----------------
SPEC_NAMES = {"agent-server": ("Agent Server API", "http://localhost:2024"),
              "api.host": ("Deployment Control API", "https://api.host.langchain.com"),
              "platform": ("LangSmith Platform API", "https://api.smith.langchain.com"),
              "api.smith": ("LangSmith Server API", "https://api.smith.langchain.com")}
VERB_MEANS = {"get": "reads something and changes nothing", "post": "creates something or starts a job",
              "put": "replaces something", "patch": "changes part of something", "delete": "removes something"}
STATUS = {200: "Success.", 201: "Success, and something new was created.", 202: "Accepted. The work continues in the background.",
          204: "Success, with nothing to send back.", 400: "The request was badly formed.", 401: "Your key is missing or wrong.",
          403: "Your key is valid, but it isn't allowed to do this.", 404: "That thing does not exist.",
          409: "This conflicts with something that already exists or is busy.", 422: "A field in your request has the wrong shape or value.",
          429: "Too many requests. Wait and try again.", 500: "The server itself failed."}


def deref(schema, spec, seen=()):
    while isinstance(schema, dict) and "$ref" in schema:
        ref = schema["$ref"]
        if ref in seen:
            return {}
        seen = (*seen, ref)
        node = spec
        for part in ref.lstrip("#/").split("/"):
            node = node.get(part.replace("~1", "/"), {})
        schema = node
    if isinstance(schema, dict) and "allOf" in schema:
        merged = {k: v for k, v in schema.items() if k != "allOf"}
        props, required = dict(merged.get("properties", {})), list(merged.get("required", []))
        for sub in schema["allOf"]:
            sub = deref(sub, spec, seen)
            props.update(sub.get("properties", {}))
            required += sub.get("required", [])
            for key in ("type", "description"):
                if key in sub and key not in merged:
                    merged[key] = sub[key]
        merged.update(properties=props, required=required)
        return merged
    return schema if isinstance(schema, dict) else {}


def first_option(schema, spec):
    for key in ("anyOf", "oneOf"):
        if schema.get(key):
            options = [deref(o, spec) for o in schema[key]]
            real = [o for o in options if o.get("type") != "null"]
            if real:
                return real[0]
    return schema


def sample(schema, spec, depth=0):
    schema = first_option(deref(schema, spec), spec)
    for key in ("example", "default"):
        if key in schema and schema[key] is not None:
            return schema[key]
    if schema.get("enum"):
        return schema["enum"][0]
    kind, fmt = schema.get("type"), schema.get("format", "")
    if isinstance(kind, list):
        kind = next((k for k in kind if k != "null"), None)
    if kind == "object" or "properties" in schema:
        if depth > 3:
            return {}
        required = set(schema.get("required", []))
        names = sorted(schema.get("properties", {}), key=lambda n: n not in required)
        return {n: sample(schema["properties"][n], spec, depth + 1) for n in names}
    if kind == "array":
        return [sample(schema.get("items", {}), spec, depth + 1)] if depth <= 3 else []
    if kind == "integer":
        return 1
    if kind == "number":
        return 1.5
    if kind == "boolean":
        return True
    if "uuid" in fmt:
        return "123e4567-e89b-12d3-a456-426614174000"
    if "date" in fmt:
        return "2026-01-15T10:30:00Z"
    return "text"


def whole(text):
    """The complete text on one line, for table cells."""
    return re.sub(r"\s+", " ", str(text or "")).strip()


def type_of(schema, spec, depth=0):
    schema = deref(schema, spec)
    if depth > 4:
        return "any"
    for key in ("anyOf", "oneOf"):
        if schema.get(key):
            return " or ".join(dict.fromkeys(type_of(o, spec, depth + 1) for o in schema[key]))
    kind = schema.get("type", "object" if "properties" in schema else "any")
    if isinstance(kind, list):
        kind = " or ".join(kind)
    if kind == "array":
        return "list of " + type_of(schema.get("items", {}), spec, depth + 1)
    return "one of: " + ", ".join(map(str, schema["enum"])) if schema.get("enum") else str(kind)


def meaning_of(schema):
    extras = [f"{key}: {json.dumps(schema[key], ensure_ascii=False)}" for key in ("title", "default", "example", "format", "pattern", "minimum", "maximum", "minLength", "maxLength", "minItems", "maxItems") if schema.get(key) is not None]
    text = whole(schema.get("description")) or "The spec gives no description."
    return text + (" (" + "; ".join(extras) + ")" if extras else "")


def field_rows(schema, spec, prefix="", visited=None):
    """Every field, including those nested inside other fields. Each named shape is listed once per table."""
    visited = set() if visited is None else visited
    if not isinstance(schema, dict):
        return []
    ref = schema.get("$ref")
    if ref:
        if ref in visited:
            return []
        visited.add(ref)
    resolved, rows = deref(schema, spec), []
    required = set(resolved.get("required", []))
    for name, prop in resolved.get("properties", {}).items():
        target = deref(prop, spec)
        rows.append([prefix + name, type_of(target, spec), "Yes" if name in required else "No", meaning_of(target)])
        rows += field_rows(prop, spec, f"{prefix}{name}.", visited)
    for key in ("anyOf", "oneOf"):
        for option in resolved.get(key, []):
            rows += field_rows(option, spec, prefix, visited)
    if isinstance(resolved.get("items"), dict):
        rows += field_rows(resolved["items"], spec, f"{prefix.rstrip('.')}[].", visited)
    if isinstance(resolved.get("additionalProperties"), dict):
        rows += field_rows(resolved["additionalProperties"], spec, f"{prefix}(any name).", visited)
    return rows


def expand_refs(node, spec, visited):
    """A copy of part of the spec with references filled in, each one once."""
    if isinstance(node, dict):
        if "$ref" in node:
            if node["$ref"] in visited:
                return {}
            visited.add(node["$ref"])
            target = spec
            for part in node["$ref"].lstrip("#/").split("/"):
                target = target.get(part.replace("~1", "/"), {})
            return expand_refs(target, spec, visited)
        return {key: expand_refs(value, spec, visited) for key, value in node.items()}
    if isinstance(node, list):
        return [expand_refs(value, spec, visited) for value in node]
    return node


def first_content(block):
    content = (block or {}).get("content") or {}
    return (content.get("application/json") or next(iter(content.values()), {})).get("schema"), list(content)


def rest_overview(spec_name, spec):
    info = spec.get("info", {})
    steps = [{"h": info.get("title", spec_name), "t": (info.get("description") or "This API has no description.") + f"\n\nVersion `{info.get('version', 'not listed')}`."}]
    if spec.get("servers"):
        steps.append({"h": "Where it runs", "t": "These are the server addresses.", "table": {"head": ["Address", "About"], "rows": [[s.get("url", ""), whole(s.get("description"))] for s in spec["servers"]]}})
    if spec.get("tags"):
        steps.append({"h": "Its areas", "t": "The API is divided into these areas.", "table": {"head": ["Area", "About"], "rows": [[t.get("name", ""), whole(t.get("description"))] for t in spec["tags"]]}})
    schemes = spec.get("components", {}).get("securitySchemes", {})
    if schemes:
        steps.append({"h": "Ways to prove who you are", "t": "Requests use one of these.", "table": {"head": ["Name", "Kind", "Header", "About"], "rows": [[n, s.get("type", ""), s.get("name", ""), whole(s.get("description"))] for n, s in schemes.items()]}})
    return add_leftovers({"title": f"{spec_name}: overview", "kind": f"API simulator · {spec_name}", "intro": "", "actors": [], "code": "", "steps": steps}, {**{k: v for k, v in spec.items() if k not in {"paths", "components"}}, "components": {k: v for k, v in spec.get("components", {}).items() if k != "schemas"}})


def schema_item(spec_name, spec, name, schema):
    rows = field_rows({"$ref": f"#/components/schemas/{name}"}, spec)
    target = deref(schema, spec)
    steps = [{"h": name, "t": target.get("description") or "The spec gives no description of this shape.", "table": {"head": ["Field", "Type", "Required", "Meaning"], "rows": rows}} if rows
             else {"h": name, "t": (target.get("description") or "The spec gives no description of this shape.") + f"\n\nType: `{type_of(target, spec)}`."}]
    return add_leftovers({"title": f"{name} (data shape)", "kind": f"API simulator · {spec_name} data shape", "intro": "", "actors": [], "code": "", "steps": steps}, expand_refs(schema, spec, set()))


def rest_item(spec_name, base, spec, verb, route, op):
    title = op.get("summary") or f"{verb.upper()} {route}"
    description = op.get("description") or op.get("summary") or "The spec gives no description."
    parameters = [deref(p, spec) for p in [*op.get("parameters", [])]]
    path_values, query, headers, rows = {}, {}, {}, []
    for param in parameters:
        value = sample(param.get("schema", {}), spec)
        rows.append([param.get("name", ""), f"{param.get('in')} · {type_of(param.get('schema', {}), spec)}",
                     "Yes" if param.get("required") else "No",
                     whole(param.get("description")) or meaning_of(deref(param.get("schema", {}), spec))])
        if param.get("in") == "path":
            path_values[param["name"]] = value
        elif param.get("in") == "query" and param.get("required"):
            query[param["name"]] = value
    url = route
    for name, value in path_values.items():
        url = url.replace("{" + name + "}", str(value))
    if query:
        url += "?" + "&".join(f"{k}={v}" for k, v in query.items())

    schemes = spec.get("components", {}).get("securitySchemes", {})
    security = op.get("security", spec.get("security", []))
    for option in security:
        for name in option:
            scheme = schemes.get(name, {})
            headers[scheme.get("name", "Authorization") if scheme.get("type") == "apiKey" else "Authorization"] = "your-secret-key"

    request_block = deref(op.get("requestBody", {}), spec)
    body_schema, body_types = first_content(request_block)
    body = sample(body_schema, spec) if body_schema else None
    responses = {code: deref(value, spec) for code, value in op.get("responses", {}).items()}
    ok_code = next((c for c in sorted(responses) if c.startswith("2")), None)
    ok_schema = first_content(responses.get(ok_code))[0] if ok_code else None
    ok_body = sample(ok_schema, spec) if ok_schema else None

    actors = ["Your code", "Server", "Storage"]
    wire = f"{verb.upper()} {url}"
    steps = [{"h": "What this does", "t": f"{description}\n\nThis is a `{verb.upper()}` request, which {VERB_MEANS[verb]}.",
              "s": {"endpoint": f"{verb.upper()} {route}"}}]
    if rows:
        steps.append({"h": "Inputs in the address", "t": "These values go in the address or the headers. A simulated value has been filled in for each.",
                      "table": {"head": ["Name", "Where and type", "Required", "Meaning"], "rows": rows}, "s": {"url": base + url}})
    else:
        steps.append({"h": "The address", "t": "This endpoint needs no values in its address.", "s": {"url": base + url}})
    if headers:
        steps.append({"h": "Prove who you are", "t": "The key travels in a header. On a real call, this would be your own secret.", "s": {"headers": headers}})
    else:
        steps.append({"h": "No key listed", "t": "The spec lists no key for this endpoint. On a local `langgraph dev` server, none is needed."})
    if body is not None:
        body_rows = field_rows(body_schema, spec)
        steps.append({"h": "Fill in the body", "t": "Here is what each field in the body means." + (f"\n\n{request_block['description']}" if request_block.get("description") else "") + "\n\nAccepted formats: " + ", ".join(f"`{t}`" for t in body_types) + ".", "s": {"body": body},
                      **({"table": {"head": ["Field", "Type", "Required", "Meaning"], "rows": body_rows}} if body_rows else {})})
    steps.append({"h": "The request leaves", "t": "Your code sends everything as one HTTP message and waits.", "a": ["Your code", "Server", wire]})
    errors = sorted(c for c in responses if c[0] in "45")
    arrive = {"h": "The server checks it", "t": "The server confirms who you are, then checks that each field has the right shape. This is where bad requests get stopped.",
              "a": ["Server", "Server"]}
    paths = {}
    if errors:
        arrive["choices"] = []
        for code in errors:
            meaning = STATUS.get(int(code), "The request could not be completed.")
            note = responses[code].get("description")
            error_schema = first_content(responses[code])[0]
            error_rows = field_rows(error_schema, spec) if error_schema else []
            arrive["choices"].append({"label": f"Simulate error {code}", "path": code})
            paths[code] = [{"h": f"The server stops: {code}", "t": f"{meaning}\n\nThe spec describes it as: {note or 'no description'}", "a": ["Server", "Your code", code],
                            "s": {"response.status": int(code)}, **({"table": {"head": ["Field", "Type", "Required", "Meaning"], "rows": error_rows}} if error_rows else {})},
                           {"h": "What you would do", "t": "Your code should check the status number before using the body. Press Back to try another path, or reopen this topic to see the success path."}]
    steps.append(arrive)
    steps.append({"h": "The server does the work", "t": f"Everything was accepted, so the server {VERB_MEANS[verb]}.", "a": ["Server", "Storage", verb.upper()]})
    steps.append({"h": "The storage answers", "t": "The stored data comes back to the server.", "a": ["Storage", "Server", "data"]})
    code_number = int(ok_code) if ok_code and ok_code.isdigit() else 200
    done = {"h": f"The answer returns: {code_number}", "t": STATUS.get(code_number, "Success."), "a": ["Server", "Your code", str(code_number)],
            "s": {"response.status": code_number, **({"response.body": ok_body} if ok_body is not None else {})}}
    response_rows = field_rows(ok_schema, spec) if ok_schema else []
    if response_rows:
        done["table"] = {"head": ["Field", "Type", "Required", "Meaning"], "rows": response_rows}
    if responses.get(ok_code, {}).get("description"):
        done["t"] += f"\n\nThe spec describes it as: {responses[ok_code]['description']}"
    steps.append(done)
    others = [[code, whole(value.get("description")), ", ".join(first_content(value)[1])] for code, value in sorted(responses.items()) if code != ok_code and code[0] not in "45"]
    if others:
        steps.append({"h": "Other possible answers", "t": "The server can also answer in these ways.", "table": {"head": ["Status", "Meaning", "Formats"], "rows": others}})
    item = {"title": title, "kind": f"API simulator · {spec_name}", "intro": f"`{verb.upper()} {route}`", "actors": actors, "code": "", "steps": steps,
            "paths": paths, "mem": True}
    return add_leftovers(item, expand_refs(op, spec, set()))


# ---------------- SDK ----------------
def parse_args_doc(doc):
    result, active = {}, False
    for line in (doc or "").splitlines():
        stripped = line.strip()
        if re.match(r"^(Args|Arguments|Parameters):$", stripped):
            active = True
            continue
        if active and re.match(r"^(Returns?|Yields?|Raises?|Examples?|Example|Note|Notes|Attributes)\b.*:$", stripped):
            break
        match = re.match(r"^`?(\*{0,2}\w+)`?(?:\s*\([^)]*\))?:\s*(.+)$", stripped)
        if active and match:
            result[match.group(1).lstrip("*")] = match.group(2)
    return result


def signature_rows(func, doc):
    args = func.args
    positional = [*args.posonlyargs, *args.args]
    defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
    pairs = [*zip(positional, defaults), *zip(args.kwonlyargs, args.kw_defaults)]
    described = parse_args_doc(doc)
    rows = []
    for arg, default in pairs:
        if arg.arg in {"self", "cls"}:
            continue
        rows.append([arg.arg, short(arg.annotation, 10_000) if arg.annotation else "any", "Yes" if default is None else f"No (default {short(default, 10_000)})",
                     whole(described.get(arg.arg)) or "No description in the package."])
    return rows


def slice_source(source_lines, node):
    start = min([d.lineno for d in node.decorator_list] + [node.lineno]) if hasattr(node, "decorator_list") else node.lineno
    return "\n".join(source_lines[start - 1:node.end_lineno]), start


def docstring_steps(doc, title, fallback):
    return doc_steps(doc, title, True) or [{"h": "What this is", "t": doc or fallback}]


def func_item(name, module, node, source_lines, owner=None):
    doc = ast.get_docstring(node) or ""
    full = f"{owner.name}.{node.name}" if owner else node.name
    code, offset = slice_source(source_lines, node)
    is_async = isinstance(node, ast.AsyncFunctionDef)
    steps = docstring_steps(doc, full, "The package gives no description for this, so the steps below read its real code.")
    if is_async:
        steps.append({"h": "How it runs", "t": "It is asynchronous, so you call it with `await`."})
    target = owner.name if owner else node.name
    steps.append({"h": "How you get it", "t": f"Bring it in from its module, then use `{full}`.", "code": f"from {module} import {target}", "lang": "python", "codeTitle": "Import"})
    rows = signature_rows(node, doc)
    if rows:
        steps.append({"h": "What you give it", "t": "Python matches your values to these inputs.", "table": {"head": ["Input", "Type", "Required", "Meaning"], "rows": rows},
                      "s": {inp[0]: "(your value)" for inp in rows[:8]}})
    else:
        steps.append({"h": "What you give it", "t": "This takes no inputs of its own."})
    body = [n for n in node.body if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str))]
    only_stub = all(isinstance(n, ast.Pass) or (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)) for n in body)
    if not body or only_stub:
        steps.append({"h": "Inside the code", "t": "This has no working code here. It only defines the shape, and something else provides the real behaviour.", "l": [1, 1]})
    for stmt in body:
        head, text = narrate(stmt)
        first, last = stmt.lineno - offset + 1, stmt.end_lineno - offset + 1
        steps.append({"h": head, "t": text, "l": [first, last]})
    if node.returns is not None:
        steps.append({"h": "What you get back", "t": f"It returns a value of type `{short(node.returns, 10_000)}`."})
    return {"title": f"{module}.{full}", "kind": "Python SDK simulator · " + ("async " if is_async else "") + ("method" if owner else "function"),
            "intro": "", "actors": [], "code": code, "codeTitle": "Real source code", "steps": steps}


def class_item(module, node, source_lines):
    doc = ast.get_docstring(node) or ""
    code, _ = slice_source(source_lines, node)
    bases = [short(b, 10_000) for b in node.bases]
    steps = docstring_steps(doc, node.name, "The package gives no description, so these steps read its real code.")
    steps.append({"h": "How you get it", "t": "Bring it in from its module.", "code": f"from {module} import {node.name}", "lang": "python", "codeTitle": "Import"})
    if bases:
        steps.append({"h": "What it builds on", "t": "This class starts with everything from: " + ", ".join(f"`{b}`" for b in bases) + "."})
    fields = []
    for member in node.body:
        if isinstance(member, ast.AnnAssign) and isinstance(member.target, ast.Name) and not member.target.id.startswith("_"):
            fields.append([member.target.id, short(member.annotation, 10_000), "No" if member.value is not None else "Yes", "Stored on each object."])
    init = next((m for m in node.body if isinstance(m, ast.FunctionDef) and m.name == "__init__"), None)
    if init is not None:
        rows = signature_rows(init, ast.get_docstring(init) or doc)
        steps.append({"h": "Creating one", "t": "When you create an object, Python runs its setup using these inputs.",
                      **({"table": {"head": ["Input", "Type", "Required", "Meaning"], "rows": rows}} if rows else {})})
    if fields:
        steps.append({"h": "What each object holds", "t": "Every object carries these fields.", "table": {"head": ["Field", "Type", "Required", "Meaning"], "rows": fields}})
    methods = [m.name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and not m.name.startswith("_")]
    if methods:
        steps.append({"h": "What you can ask it to do", "t": "Each of these has its own simulation: " + ", ".join(f"`{m}`" for m in methods) + "."})
    return {"title": f"{module}.{node.name}", "kind": "Python SDK simulator · class", "intro": "", "actors": [], "code": code, "codeTitle": "Real source code", "steps": steps}


def attr_item(module, target, annotation, owner=None):
    full = f"{owner.name}.{target}" if owner else target
    return {"title": f"{module}.{full}", "kind": "Python reference · attribute", "intro": "", "actors": [], "code": "",
            "steps": [{"h": "What this is", "t": f"`{full}` is a value stored " + (f"on `{owner.name}` objects." if owner else f"in the module `{module}`.")},
                      {"h": "Its type", "t": f"It holds a value of type `{short(annotation, 10_000)}`." if annotation is not None else "The code gives no type for it."}]}


def sdk_items(sources=None):
    for package, base in (sources or [(p, SITE_PACKAGES) for p in SDK_PACKAGES]):
        for path in sorted((base / package).rglob("*.py")):
            relative = path.relative_to(base).with_suffix("")
            parts = [p for p in relative.parts if p != "__init__"]
            if any(p.startswith("_") or p in {"tests", "testing"} for p in parts):
                continue
            try:
                source = path.read_text(encoding="utf-8")
                tree = ast.parse(source)
            except (SyntaxError, UnicodeDecodeError):
                continue
            lines, module = source.splitlines(), ".".join(parts)
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
                    yield package, parts, func_item(node.name, module, node, lines), f"{module}.{node.name}"
                elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                    yield package, parts, class_item(module, node, lines), f"{module}.{node.name}"
                    for member in node.body:
                        if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)) and not member.name.startswith("_"):
                            yield package, parts, func_item(member.name, module, member, lines, owner=node), f"{module}.{node.name}.{member.name}"
                        elif isinstance(member, ast.AnnAssign) and isinstance(member.target, ast.Name) and not member.target.id.startswith("_"):
                            yield package, parts, attr_item(module, member.target.id, member.annotation, node), f"{module}.{node.name}.{member.target.id}"
                elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and not node.target.id.startswith("_"):
                    yield package, parts, attr_item(module, node.target.id, node.annotation), f"{module}.{node.target.id}"
                elif isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id.isupper():
                    yield package, parts, attr_item(module, node.targets[0].id, None), f"{module}.{node.targets[0].id}"


# ---------------- API reference ----------------
REFERENCE = ROOT / "source" / "reference"
LANG_NAMES = {"python": ("refpy", "Python"), "javascript": ("refjs", "JavaScript"), "java": ("refjava", "Java"), "go": ("refgo", "Go")}


def doc_steps(text, title, python_first):
    text = re.sub(r'(?m)^[ \t]*(?:!!!|\?\?\?\+?)[ \t]+([\w-]+)(?:[ \t]+"([^"]*)")?[ \t]*$', lambda m: "\n**" + (m[2] or m[1].capitalize()) + "**\n", text)
    text = re.sub(r'(?m)^[ \t]*===[ \t]+"([^"]+)"[ \t]*$', r"\n**\1**\n", text)
    made = guide_item({"title": title, "file": ""}, "x\ny\n" + text, python_first)["steps"]
    return [s for s in made if not s["t"].startswith("This page has no further content")]


def reference_files():
    """Map each saved reference page's path to the file holding it."""
    files = {}
    index = REFERENCE / "index.jsonl"
    if not index.exists():
        return files
    for line in index.read_text(encoding="utf-8").splitlines():
        url = json.loads(line)["url"]
        digest = hashlib.sha1(url.encode("utf-8")).hexdigest()
        path = REFERENCE / "records" / digest[:2] / f"{digest}.json"
        if path.exists():
            files[url.replace("https://reference.langchain.com", "").rstrip("/")] = path
    every = int(os.environ.get("LAB_SAMPLE") or 1)  # test builds can use a slice of the pages
    return dict(list(sorted(files.items()))[::every])


def read_record(path):
    return json.loads(path.read_text(encoding="utf-8"))["data"]


def ref_heading(path, record):
    language = record.get("language", "python")
    if "packages" in record:
        return f"{language} reference home", "API reference · language"
    if "package" in record:
        title = f"{record['package'].get('publishedName')} (package)"
        if (record.get("subpage") or {}).get("title"):
            title = f"{record['package'].get('publishedName')}: {record['subpage']['title']}"
        return title, f"API reference · {language} package"
    return record.get("qualifiedName", path), f"API reference · {language} {record.get('kind', 'item')}"


def cell(text, path):
    return {"t": text, "u": path} if path else text


def ref_inherited(record, by_q, by_name):
    """Walk parent classes across every downloaded package and list what is inherited."""
    own = {m.get("name") for m in record.get("members") or []}
    refs = {t.get("name"): t.get("qualifiedName") for t in record.get("typeRefs") or []}
    pending = [(name, refs, record.get("packageId")) for name in (record.get("relations") or {}).get("extends", [])]
    visited, rows, unresolved = set(), [], []
    while pending:
        name, table, package = pending.pop(0)
        plain = re.sub(r"\[.*$", "", str(name)).strip()
        path = by_q.get(table.get(plain) or "") or by_name.get((package, plain))
        if not path:
            unresolved.append(plain)
            continue
        if path in visited:
            continue
        visited.add(path)
        parent = records_ref.get(path)
        if parent is None:
            continue
        for member in parent.get("members") or []:
            title = member.get("name")
            if not title or title.startswith("_") or title in own or member.get("kind") == "alias" or member.get("visibility") not in (None, "public"):
                continue
            own.add(title)
            rows.append([cell(title, f"{path}/{title}"), member.get("kind", ""), str(member.get("type") or ""), cell(plain, path)])
        next_refs = {t.get("name"): t.get("qualifiedName") for t in parent.get("typeRefs") or []}
        pending += [(n, next_refs, parent.get("packageId")) for n in (parent.get("relations") or {}).get("extends", [])]
    return rows, unresolved


def ref_item(path, record, by_q, by_name, ast_map):
    language = record.get("language", "python")
    python = language == "python"
    code_lang = "python" if python else "text"
    title_text, kind_text = ref_heading(path, record)
    if "packages" in record:
        rows = [[cell(p.get("displayName") or p.get("name", ""), p.get("url")), whole(re.sub(r"<[^>]+>", " ", p.get("description") or ""))] for p in record["packages"]]
        return add_leftovers({"title": title_text, "kind": kind_text, "intro": "", "actors": [], "code": "",
                              "steps": [{"h": "Packages", "t": "Open any package below.", "table": {"head": ["Package", "About"], "rows": rows}}]}, record)
    if "package" in record:
        package = record["package"]
        steps = [{"h": package.get("displayName", "Package"), "t": f"Package `{package.get('publishedName')}`, version `{package.get('version')}`. It has {package.get('stats', {}).get('total', 'many')} documented items."}]
        steps += doc_steps(package.get("description") or "", package.get("displayName", ""), python)
        subpage = record.get("subpage") or {}
        if subpage.get("markdownContent"):
            steps += doc_steps(subpage["markdownContent"], subpage.get("title", ""), python)
        rows = []
        for symbol in record.get("symbols", []):
            name = symbol.get("qualifiedName", "")
            target = by_q.get(name)
            rows.append([cell(name, target), symbol.get("kind", ""), whole(re.sub(r"<[^>]+>", " ", symbol.get("summaryHtml") or ""))])
        if rows:
            steps.append({"h": "Everything in this package", "t": "Open any item below.", "table": {"head": ["Name", "Kind", "About"], "rows": rows}})
        return add_leftovers({"title": title_text, "kind": kind_text, "intro": "", "actors": [], "code": "", "steps": steps}, record)

    kind, name, qualified = record.get("kind", "item"), record.get("name", ""), record.get("qualifiedName", path)
    docs, tags = record.get("docs") or {}, record.get("tags") or {}
    notes = [t for t in (tags.get("stability") if tags.get("stability") not in (None, "stable") else None, "asynchronous" if tags.get("isAsync") else None, "abstract, so another class must fill it in" if tags.get("isAbstract") else None) if t]
    lead = f"This is a **{kind}** called `{name}`, in `{qualified}`." + (" It is " + ", ".join(notes) + "." if notes else "")
    steps = [{"h": "What this is", "t": lead}]
    body = "\n\n".join(p for p in [docs.get("summary"), docs.get("description")] if p)
    steps += doc_steps(body, name, python) if body else [{"h": "Description", "t": "The reference gives no description for this item."}]
    deprecated = docs.get("deprecated") or {}
    if deprecated.get("isDeprecated"):
        steps.append({"h": "Do not use this in new code", "t": "This has been marked as deprecated, which means it is being retired." + (f"\n\n{deprecated['message']}" if deprecated.get("message") else "")})
    for number, example in enumerate(docs.get("examples") or [], 1):
        if isinstance(example, dict) and example.get("code"):
            note = " ".join(str(v) for k, v in example.items() if k != "code" and isinstance(v, str) and v.strip())
            steps.append({"h": f"Example {number}", "t": note or "Read this example.", "code": example["code"], "lang": code_lang, "codeTitle": "Example"})
    if record.get("typeParams"):
        steps.append({"h": "Placeholder types", "t": "You choose these types when you use it.", "table": {"head": ["Details"], "rows": [[json.dumps(t, ensure_ascii=False) if not isinstance(t, str) else t] for t in record["typeParams"]]}})
    parts = qualified.rsplit(".", 1)
    if python and kind in {"class", "function"} and len(parts) == 2:
        steps.append({"h": "How you get it", "t": "This line brings it into your code.", "code": f"from {parts[0]} import {parts[1]}", "lang": "python", "codeTitle": "Import"})
    elif python and kind in {"method", "attribute", "property"} and qualified.count(".") >= 2:
        owner = parts[0].rsplit(".", 1)
        steps.append({"h": "How you get it", "t": f"This belongs to `{owner[-1]}`. Import that first, then use `.{name}` on it.", "code": f"from {owner[0]} import {owner[-1]}", "lang": "python", "codeTitle": "Import"})
    if record.get("signature") and record["signature"].strip():
        steps.append({"h": "Its exact form", "t": "This is how it's written in code.", "code": record["signature"], "lang": code_lang, "codeTitle": "Signature"})
    params = record.get("params") or []
    callable_item = kind in {"function", "method"}
    actors = ["Your code", name[:28] or "Function", "Result"] if callable_item else []
    codes = {}
    if params:
        steps.append({"h": "What you give it", "t": "Here is every input at a glance. Next, you'll go through them one at a time.",
                      "table": {"head": ["Input", "Type", "Required", "Default"], "rows": [[p.get("name", ""), str(p.get("type") or "any"), "Yes" if p.get("required") else "No", str(p.get("default") if p.get("default") is not None else "")] for p in params]}})
        for param in params:
            default = param.get("default")
            text = (param.get("description") or "The reference gives no description for this input.").strip()
            steps.append({"h": f"Input: {param.get('name')}", "t": f"Type: `{param.get('type') or 'any'}`. " + ("You must give this." if param.get("required") else "This is optional.") + f"\n\n{text}",
                          "s": {param.get("name", "?"): default if default is not None else "(your value)"}})
    if callable_item:
        steps.append({"h": "You call it", "t": "Your inputs travel into the code.", "a": ["Your code", actors[1], "inputs"]})
        ast_source = ast_map.get(qualified) if python else None
        if ast_source and ast_source.get("code"):
            codes["source"] = ast_source["code"]
            for step in ast_source["steps"]:
                if step.get("l") and "code" not in step:
                    steps.append({**step, "cr": "source", "lang": "python", "codeTitle": "Real source code"})
        returned = record.get("returns") or {}
        result = str(returned.get("type") or "nothing listed")
        steps.append({"h": "What you get back", "t": f"It returns `{result}`." + (f"\n\n{returned['description']}" if returned.get("description") else ""), "a": [actors[1], "Result", result[:40]], "s": {"result": result}})
    members = [m for m in record.get("members") or [] if m.get("kind") != "alias" and m.get("visibility") in (None, "public") and not str(m.get("name", "")).startswith("_")]
    extends = (record.get("relations") or {}).get("extends", [])
    if extends:
        refs = {t.get("name"): t.get("qualifiedName") for t in record.get("typeRefs") or []}
        rows = [[cell(str(e), by_q.get(refs.get(re.sub(r"\[.*$", "", str(e)).strip()) or "") or by_name.get((record.get("packageId"), re.sub(r"\[.*$", "", str(e)).strip())))] for e in extends]
        steps.append({"h": "What it builds on", "t": "It starts with everything from these.", "table": {"head": ["Parent"], "rows": rows}})
    if members:
        steps.append({"h": "What it contains", "t": "These are defined right here. Open any of them.",
                      "table": {"head": ["Name", "Kind", "Type or form"], "rows": [[cell(m.get("name"), f"{path}/{m.get('name')}"), m.get("kind", ""), str(m.get("type") or m.get("signature") or "")] for m in members]}})
    if kind in {"class", "interface"}:
        rows, unresolved = ref_inherited(record, by_q, by_name)
        ref_stats["inherited"] += len(rows)
        ref_stats["unresolved"] += len(unresolved)
        if rows:
            steps.append({"h": "What it inherits", "t": "It also has all of these, from its parents.", "table": {"head": ["Name", "Kind", "Type", "From"], "rows": rows}})
    links = [[cell(t.get("name", ""), by_q.get(t.get("qualifiedName") or "")), t.get("qualifiedName") or ""] for t in record.get("typeRefs") or [] if by_q.get(t.get("qualifiedName") or "")]
    if links:
        steps.append({"h": "Related types", "t": "This uses these types.", "table": {"head": ["Type", "Full name"], "rows": links}})
    source, version = record.get("source") or {}, record.get("versionInfo") or {}
    where = f"`{source.get('path')}`" + (f", lines {source.get('line')} to {source.get('endLine')}" if source.get("line") else "") if source.get("path") else "not listed"
    since = f"\n\nAvailable since version `{version['since']}`." if version.get("since") else ""
    steps.append({"h": "Where it lives", "t": f"Repository `{source.get('repo', 'not listed')}`, file {where}.{since}"})
    item = {"title": title_text, "kind": kind_text, "intro": "", "actors": actors, "code": "", "steps": steps, "beta": tags.get("stability") == "beta"}
    if codes:
        item["codes"] = codes
    return add_leftovers(item, record)


# ---------------- CLI ----------------
def cli_help():
    cache = ROOT / "source" / "cli_help.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    tools = {"langgraph": ROOT / ".venv/Scripts/langgraph.exe", "mda": ROOT / ".venv/Scripts/mda.exe", "dcode": ROOT / ".venv-dcode/Scripts/dcode.exe"}

    def get(exe, args):
        try:
            result = subprocess.run([str(exe), *args, "--help"], capture_output=True, encoding="utf-8", errors="replace",
                                    stdin=subprocess.DEVNULL, timeout=40)
            return (result.stdout or result.stderr).strip()
        except (subprocess.TimeoutExpired, OSError):
            return ""

    found = {}
    for name, exe in tools.items():
        top = get(exe, [])
        found[name] = top
        section = re.split(r"(?im)^\s*commands?:\s*$", top)
        if len(section) > 1:
            block = re.split(r"\n\s*\n", section[1].lstrip("\n"))[0]
            for command in re.findall(r"(?m)^\s+([a-z][\w-]*)\s{2,}", block):
                if command != "help":
                    found[f"{name} {command}"] = get(exe, [command])
    cache.write_text(json.dumps(found, indent=1), encoding="utf-8")
    return found


def cli_item(name, text):
    lines = text.splitlines()
    summary = next((l.strip() for l in lines if l.strip() and not l.lower().startswith("usage")), "")
    steps = [{"h": "What this command does", "t": whole(summary) or "The tool gives no summary.", "code": text, "lang": "text", "codeTitle": f"{name} --help"}]
    usage = next((l.strip() for l in lines if l.lower().lstrip().startswith("usage")), "")
    if usage:
        steps.append({"h": "How you type it", "t": f"The general form is `{usage}`. Square brackets mean optional."})
    for line in lines:
        match = re.match(r"^\s+(-\w(?:,\s*--[\w-]+)?|--[\w-]+)([^\n]*?)(?:\s{2,}(.*))?$", line)
        if match:
            steps.append({"h": match.group(1).strip(), "t": (match.group(3) or "See the full help text.").strip()})
    steps.append({"h": "Try it for real", "t": f"When you are ready, type `{name}` in a terminal. This page only simulates reading it."})
    return {"title": name, "kind": "CLI simulator", "intro": "", "actors": [], "code": "", "steps": steps}


# ---------------- Assemble ----------------
items, groups_index = [], collections.defaultdict(lambda: collections.defaultdict(list))
GROUPS = [
    ("m0", "Start here", "Start from zero", "APIs, tokens, agents and how the family of products fits together."),
    ("m1", "Build", "1. LangChain", "Models, messages, tools, agents, middleware and streaming."),
    ("m2", "Build", "2. LangGraph", "Nodes, edges, state, saving progress and human approval."),
    ("m3", "Build", "3. Deep Agents", "Planning, files, helpers and long-term memory."),
    ("m4", "Build", "4. Managed Deep Agents", "An agent described as a folder, file by file."),
    ("m5", "Run, watch and test", "5. Agent Server and Studio", "Assistants, threads, runs and your local server."),
    ("m6", "Run, watch and test", "6. Monitor: tracing", "Traces, dashboards, alerts, automations and feedback."),
    ("m7", "Run, watch and test", "7. Test: evaluation", "Datasets, evaluators and experiments."),
    ("m8", "Run, watch and test", "8. Deploy and hosting", "Cloud, Hybrid, Self-hosted, Standalone and billing."),
    ("m9", "Products and governance", "9. Agent Registry", "Agents, environments and identifiers."),
    ("m10", "Products and governance", "10. Gateway, Fleet, Engine, dcode", "The separate LangSmith products and the coding agent."),
    ("m11", "Products and governance", "11. Setup and governance", "Accounts, roles, SSO and audit logs."),
    ("m12", "Finish", "12. Capstone", "One agent's whole life, from code to production."),
    ("rest", "API and code reference", "REST API simulator", "Every REST endpoint: its request, checks, errors and response."),
    ("refpy", "API and code reference", "Python API reference", "Every Python package on reference.langchain.com: classes, functions, methods, attributes, modules and what they inherit."),
    ("refjs", "API and code reference", "JavaScript API reference", "Every JavaScript and TypeScript package on the reference site."),
    ("refjava", "API and code reference", "Java API reference", "Every Java item on the reference site."),
    ("refgo", "API and code reference", "Go API reference", "Every Go item on the reference site."),
    ("sdk", "API and code reference", "Installed code extras", "Public Python items found in the installed packages but not listed on the reference site."),
    ("cli", "API and code reference", "CLI simulator", "Every langgraph, mda and dcode command."),
    ("integrations", "API and code reference", "Integrations", "Connecting providers and third-party services."),
    ("other", "Library", "Other guides", "Every remaining page from the docs."),
    ("ts", "Library", "TypeScript copies and history", "TypeScript pages and release notes, kept so nothing is missing."),
]


LARGE = {"refpy", "refjs", "refjava", "refgo", "sdk"}
section_numbers, section_rows = {}, collections.defaultdict(list)
def inputs_fingerprint():
    """Changes whenever anything the build reads changes, so saved progress is only reused for the same inputs."""
    digest = hashlib.sha1()
    for path in [ROOT / "tools" / "build_site.py", ROOT / "tools" / "textcheck.py", *sorted((ROOT / "content").glob("*.py")), ROOT / "coverage.json",
                 REFERENCE / "index.jsonl", ROOT / "source" / "simple" / "done.jsonl", *sorted((RAW / "openapi").glob("*"))]:
        if path.exists():
            info = path.stat()
            digest.update(f"{path}:{info.st_size}:{info.st_mtime_ns}".encode())
    return digest.hexdigest() + os.environ.get("LAB_SAMPLE", "")


# Progress is saved to disk after every finished data file, so a stopped build continues where it was.
CHECKPOINT = SITE_DATA / "checkpoint.json"
FINGERPRINT = inputs_fingerprint()
resume = None
if CHECKPOINT.exists():
    saved_progress = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
    if saved_progress.get("fingerprint") == FINGERPRINT:
        resume = saved_progress
if resume:
    for leftover in CHUNKS.glob("*.js"):
        if int(leftover.stem) >= resume["chunks"]:
            leftover.unlink()
    print(f"continuing a stopped build: {resume['emitted']:,} reference pages already done", flush=True)
else:
    if SITE_DATA.exists():
        shutil.rmtree(SITE_DATA)
    CHUNKS.mkdir(parents=True)
    (SITE_DATA / "sec").mkdir()
chunk_buffer, chunk_size, chunk_number, built_steps = {}, 0, (resume or {}).get("chunks", 0), (resume or {}).get("steps", 0)
audit_map = dict((resume or {}).get("audit", {}))
large_done_rows = dict((resume or {}).get("rows", {}))
large_index, large_skip, checkpointing = 0, (resume or {}).get("emitted", 0), True
MARKDOWN_LINK = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)\)")


def flush_chunk():
    global chunk_buffer, chunk_size, chunk_number
    if chunk_buffer:
        payload = json.dumps(chunk_buffer, ensure_ascii=False, separators=(",", ":"))
        (CHUNKS / f"{chunk_number}.js").write_text(f"window.__chunk({chunk_number},{payload});\n", encoding="utf-8")
        chunk_number += 1
        chunk_buffer, chunk_size = {}, 0
        if checkpointing:
            temporary = CHECKPOINT.with_suffix(".tmp")
            temporary.write_text(json.dumps({"fingerprint": FINGERPRINT, "emitted": large_index, "chunks": chunk_number, "steps": built_steps,
                                             "rows": large_done_rows, "audit": audit_map}), encoding="utf-8")
            temporary.replace(CHECKPOINT)


SIMPLE_FILE = ROOT / "source" / "simple" / "done.jsonl"
SIMPLE = {}
if SIMPLE_FILE.exists():
    for simple_line in SIMPLE_FILE.read_text(encoding="utf-8").splitlines():
        saved = json.loads(simple_line)
        if saved.get("ok"):
            SIMPLE[saved["h"]] = saved["s"]
print("plain-English rewrites available:", len(SIMPLE), flush=True)


def simple_version(text):
    masked, spans = protect(text)
    found = SIMPLE.get(unit_hash(masked))
    return restore(found, spans) if found else None


def local_address(url):
    return re.sub(r"^https://(docs|reference)\.langchain\.com", "", url.split("#")[0]).removesuffix("/").removesuffix(".md").removesuffix("/")


def resolve_step(step):
    def relink(match):
        target = urls.get(local_address(match[2]))
        return f"[{match[1]}](#/{target})" if target else match[0]
    if step.get("t"):
        step["t"] = MARKDOWN_LINK.sub(relink, step["t"])
        rewritten = simple_text(step["t"])
        if rewritten:
            step["o"], step["t"] = step["t"], rewritten
    table = step.get("table")
    if table:
        table["rows"] = [[({"t": c["t"], "i": urls[c["u"]]} if c.get("u") in urls else c["t"]) if isinstance(c, dict) else simple_cell(c) for c in row] for row in table["rows"]]


def simple_cell(value):
    replaced = simple_version(value) if isinstance(value, str) else None
    return {"t": replaced, "o": value} if replaced else value


def simple_text(text):
    """Use saved plain-English rewrites where they exist, keeping the original wording too."""
    changed = False
    out = []
    for paragraph in text.split("\n\n"):
        replaced = simple_version(paragraph)
        changed = changed or bool(replaced)
        out.append(replaced or paragraph)
    return "\n\n".join(out) if changed else None


def emit(identifier, item):
    """Fix the links in a finished page and write it out. Returns the file number it went into."""
    global chunk_size, built_steps
    for step in item["steps"]:
        resolve_step(step)
    for branch in (item.get("paths") or {}).values():
        for step in branch:
            resolve_step(step)
    item.setdefault("kind", "Simulation")
    built_steps += len(item["steps"])
    encoded = len(json.dumps(item, ensure_ascii=False))
    if chunk_size and chunk_size + encoded > 700_000:
        flush_chunk()
    chunk_buffer[identifier] = item
    chunk_size += encoded
    return chunk_number


def reserve(group, section, title, kind, url=None):
    """Give a large-group page its id before it is built, so other pages can link to it."""
    key = (group, section)
    number = section_numbers.setdefault(key, len(section_numbers))
    row = [f"r{number}_{len(section_rows[key])}", title, kind, "", 0]
    section_rows[key].append(row)
    if url:
        urls[re.sub(r"^https://[^/]+", "", url).rstrip("/")] = row[0]
    return row


def resumed(row):
    """True when this page was already written by a build that stopped part-way."""
    global large_index
    if large_index < large_skip:
        large_index += 1
        row[4] = large_done_rows[row[0]]
        return True
    return False


def finish(row, item, source=None):
    global large_index
    row[4] = emit(row[0], item)  # may save progress first, before this page is counted
    if source:
        audit_map[row[0]] = source
    large_done_rows[row[0]] = row[4]
    large_index += 1


def add(item, group, section, subtitle, url=None, source=None):
    identifier = f"t{len(items)}"
    item.setdefault("kind", "Simulation")
    items.append((identifier, item, subtitle))
    groups_index[group][section].append(identifier)
    if url:
        urls[re.sub(r"^https://[^/]+", "", url).rstrip("/")] = identifier
    if source:
        audit_map[identifier] = source
    return identifier


urls = {}
start = None
for sim_item in SIMS:
    identifier = add({k: v for k, v in sim_item.items() if k not in {"key", "module"}}, sim_item["module"], "A. Start with these simulations", sim_item["title"])
    start = start or identifier

SECTION_ALL = "B. Every saved page on this topic: "
rest_pages = {}
for url, meta in ledger["pages"].items():
    if meta["kind"] == "rest-endpoint":
        text = (PAGES / meta["file"]).read_text(encoding="utf-8")
        match = re.search(r"(?m)^\S*openapi\S*\.json\s+(get|post|put|patch|delete)\s+(/\S*)", text, re.I)
        if match:
            rest_pages[(match.group(1).lower(), match.group(2))] = url
        continue
    text = (PAGES / meta["file"]).read_text(encoding="utf-8")
    module = "ts" if meta["tier"] == "merged" else module_for(url)
    item = guide_item(meta, text, python_first=module != "ts")
    add(item, module, SECTION_ALL + section_for(url), url.split("docs.langchain.com", 1)[1], url, {"page": meta["file"]})

seen_ops = set()
linked = set()
for spec_file in sorted((RAW / "openapi").glob("*")):
    spec = json.loads(spec_file.read_text(encoding="utf-8"))
    key = next(k for k in SPEC_NAMES if k in spec_file.name)
    spec_name, base = SPEC_NAMES[key]
    for route, path_item in spec.get("paths", {}).items():
        for verb in VERBS:
            op = path_item.get(verb)
            if not op:
                continue
            op = {**op, "parameters": [*path_item.get("parameters", []), *op.get("parameters", [])]}
            page = rest_pages.get((verb, route))
            if page:
                linked.add(page)
            item = rest_item(spec_name, base, spec, verb, route, op)
            tag = (op.get("tags") or ["General"])[0]
            add(item, "rest", f"{spec_name}: {tag}", f"{verb.upper()} {route}", page, {"spec": spec_file.name, "verb": verb, "route": route})
            seen_ops.add((spec_file.name, verb, route))

for url, meta in ledger["pages"].items():
    if meta["kind"] == "rest-endpoint" and url not in linked:
        add(guide_item(meta, (PAGES / meta["file"]).read_text(encoding="utf-8"), True), "other",
            SECTION_ALL + "API reference pages", url.split("docs.langchain.com", 1)[1], url, {"page": meta["file"]})

for spec_file in sorted((RAW / "openapi").glob("*")):
    spec = json.loads(spec_file.read_text(encoding="utf-8"))
    spec_name = SPEC_NAMES[next(k for k in SPEC_NAMES if k in spec_file.name)][0]
    add(rest_overview(spec_name, spec), "rest", f"{spec_name}: about this API", spec_name)
    for schema_name, schema in sorted(spec.get("components", {}).get("schemas", {}).items()):
        add(schema_item(spec_name, spec, schema_name, schema), "rest", f"{spec_name}: data shapes", schema_name)
REPO_SRC = ROOT / "source" / "docs_repo" / "src"
SAMPLE_LANGUAGES = {".py": "python", ".ts": "text", ".tsx": "text", ".js": "text", ".mmd": "text", ".json": "text", ".yaml": "text", ".yml": "text", ".toml": "text", ".sh": "text", ".txt": "text", ".md": "text", ".env": "text"}
repo_extras = sorted(p for p in [*(REPO_SRC / "code-samples").rglob("*"), *REPO_SRC.rglob("*.mmd")] if p.is_file() and p.suffix in SAMPLE_LANGUAGES)
for extra in repo_extras:
    relative = extra.relative_to(REPO_SRC).as_posix()
    code = extra.read_text(encoding="utf-8", errors="replace").strip("\n")
    language = SAMPLE_LANGUAGES[extra.suffix]
    made = code_steps(code, relative) if language == "python" else None
    steps = made or [{"h": extra.name, "t": "This is a complete, ready-to-read file from the docs' own source." if extra.suffix != ".mmd" else "This is the text source of a diagram.", "code": code, "lang": language, "codeTitle": relative}]
    add({"title": relative, "kind": "Saved docs, source file", "intro": "", "actors": [], "code": "", "steps": steps}, "other", "Code samples and diagrams: " + relative.split("/")[1 if relative.startswith("code-samples") else 0], relative)
print("pages, endpoints and data shapes ready:", len(items), flush=True)

ast_map = {}
for package, parts, item, full_name in sdk_items():
    ast_map.setdefault(full_name, item)
print("installed code read:", len(ast_map), flush=True)

ref_files = reference_files()
records_ref, by_q, by_name, ref_rows = {}, {}, {}, {}
ref_stats = collections.Counter()
canonical_paths, duplicate_paths = {}, {}
for ref_path, file_path in sorted(ref_files.items(), key=lambda pair: (pair[0].count("/"), pair[0])):
    record = read_record(file_path)
    if record.get("id"):
        first_path = canonical_paths.setdefault(record["id"], ref_path)
        if first_path != ref_path:  # the same item at a longer address: send that address to the real page
            duplicate_paths[ref_path] = first_path
            continue
    if record.get("qualifiedName"):
        by_q.setdefault(record["qualifiedName"], ref_path)
        by_name.setdefault((record.get("packageId"), record.get("name")), ref_path)
    if record.get("members") or (record.get("relations") or {}).get("extends"):
        records_ref[ref_path] = {"packageId": record.get("packageId"), "typeRefs": record.get("typeRefs"), "relations": record.get("relations"),
                                 "members": [{k: m.get(k) for k in ("name", "kind", "type", "visibility")} for m in record.get("members") or []]}
    pieces = ref_path.strip("/").split("/")
    group_id = LANG_NAMES.get(pieces[0], ("other", ""))[0]
    section = pieces[1] if len(pieces) > 1 else "Home"
    if len(pieces) > 2:
        section += " · " + pieces[2]
    title_text, kind_text = ref_heading(ref_path, record)
    ref_rows[ref_path] = reserve(group_id, section, title_text, kind_text, "https://reference.langchain.com" + ref_path)
ref_names = set(by_q)
for ref_path, first_path in duplicate_paths.items():
    urls[ref_path] = ref_rows[first_path][0]
print("reference pages indexed:", len(ref_rows), "same item at a longer address:", len(duplicate_paths), flush=True)

for ref_path, file_path in sorted(ref_files.items()):
    if ref_path in duplicate_paths or resumed(ref_rows[ref_path]):
        continue
    finish(ref_rows[ref_path], ref_item(ref_path, read_record(file_path), by_q, by_name, ast_map), {"ref": str(file_path.relative_to(REFERENCE))})
    ref_stats["pages"] += 1
    if ref_stats["pages"] % 20_000 == 0:
        print("reference pages built:", ref_stats["pages"], flush=True)

sdk_names = set()
for full_name, item in ast_map.items():
    if full_name not in ref_names:
        item["kind"] = "Python reference · from installed code"
        row = reserve("refpy" if full_name.startswith("managed_deepagents") else "sdk", full_name.split(".")[0] + " · installed code", item["title"], item["kind"])
        if not resumed(row):
            finish(row, item)
        sdk_names.add(full_name)
ast_map = None
community = 0
for package, parts, item, full_name in sdk_items([("langchain_community", ROOT / "source" / "community")]):
    if full_name in ref_names:
        continue
    item["kind"] = "Python reference · from package code"
    row = reserve("refpy", "langchain-community · " + (parts[1] if len(parts) > 1 else "root"), item["title"], item["kind"])
    if not resumed(row):
        finish(row, item)
    community += 1
ref_stats["community"] = community
print("reference:", dict(ref_stats), "installed-only:", len(sdk_names), flush=True)

cli_names = []
for name, text in sorted(cli_help().items()):
    if text:
        add(cli_item(name, text), "cli", name.split()[0], name)
        cli_names.append(name)

# ---------------- Write ----------------
flush_chunk()  # the last reference pages are saved with the progress record
checkpointing = False
small_rows = {}
for identifier, item, sub in items:
    number = emit(identifier, item)
    small_rows[identifier] = [identifier, item["title"], item["kind"], sub[:90], number]
flush_chunk()

catalog_groups, search_lines = [], []
total = 0
for group_id, band, title, description in GROUPS:
    if group_id in LARGE:
        keys = sorted(k for k in section_rows if k[0] == group_id)
        sections = [{"title": key[1], "n": len(section_rows[key]), "f": section_numbers[key]} for key in keys]
        for key in keys:
            (SITE_DATA / "sec" / f"{section_numbers[key]}.js").write_text(f"window.__sec({section_numbers[key]},{json.dumps(section_rows[key], ensure_ascii=False, separators=(',', ':'))});\n", encoding="utf-8")
            search_lines += [row for row in section_rows[key]]
    else:
        sections = []
        for name, ids in sorted(groups_index.get(group_id, {}).items()):
            rows = [small_rows[i] for i in ids]
            sections.append({"title": name, "n": len(rows), "r": rows})
            search_lines += rows
    if sections:
        total += sum(s["n"] for s in sections)
        catalog_groups.append({"id": group_id, "band": band, "title": title, "desc": description, "sections": sections})
catalog = {"start": start, "total": total, "groups": catalog_groups}
(SITE_DATA / "catalog.js").write_text("window.CATALOG=" + json.dumps(catalog, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
(SITE_DATA / "glossary.js").write_text("window.GLOSSARY=" + json.dumps(GLOSSARY, ensure_ascii=False) + ";\n", encoding="utf-8")
search_text = "\n".join("\t".join(re.sub(r"\s+", " ", str(v)) for v in row[:4]) for row in search_lines)
(SITE_DATA / "search.js").write_text("window.__search(" + json.dumps(search_text, ensure_ascii=False) + ");\n", encoding="utf-8")
(SITE_DATA / "urls.json").write_text(json.dumps(urls, ensure_ascii=False), encoding="utf-8")
(SITE_DATA / "audit_map.json").write_text(json.dumps(audit_map, ensure_ascii=False), encoding="utf-8")
report = json.dumps({"items": total, "sims": len(SIMS), "chunks": chunk_number, "sections": len(section_numbers), "rest": len(seen_ops), "sdk": len(sdk_names), "cli": len(cli_names),
                     "steps": built_steps, "by_group": {g["id"]: sum(s["n"] for s in g["sections"]) for g in catalog_groups}}, indent=1)
(SITE_DATA / "build_report.json").write_text(report, encoding="utf-8")
CHECKPOINT.unlink(missing_ok=True)
print(report, flush=True)
if not os.environ.get("LAB_OUT"):
    old = ROOT / "site" / "data.old"
    if old.exists():
        shutil.rmtree(old)
    FINAL_DATA.rename(old)
    SITE_DATA.rename(FINAL_DATA)
    shutil.rmtree(old)
    pictures = 0
    for media in REPO_SRC.rglob("*"):
        if media.is_file() and media.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}:
            target = ROOT / "site" / "media" / media.relative_to(REPO_SRC)
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                shutil.copy2(media, target)
            pictures += 1
    print("lab updated; pictures available offline:", pictures, flush=True)
