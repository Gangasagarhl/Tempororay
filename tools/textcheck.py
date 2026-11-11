"""Shared word checks: did a built page keep every word of what it was made from?"""
import collections
import hashlib
import json
import re

SKIP_KEYS = {"id", "refId", "packageId", "sha", "urls", "canonical", "url", "$ref"}
WORD = re.compile(r"[^\W_]+")
LINK_TARGET = re.compile(r"\]\([^)\s]*\)")
PICTURE_ADDRESS = re.compile(r"<img\b[^>]*>|https://mintcdn\.com/\S+")


PROTECTED = re.compile(r"!?\[[^\]]*\]\([^)\s]*\)|`[^`\n]+`|https?://[^\s)>\]]+|<[^>\n]+>")
MARK = re.compile(r"⟦(\d+)⟧")
NUMBER = re.compile(r"(?<![\w.])\d+(?:[.,]\d+)*%?")
IDENTIFIER = re.compile(r"\b(?:[a-z]+_[a-z0-9_]+|[a-z]+[A-Z]\w*|[A-Z][a-z0-9]+[A-Z]\w*|[A-Z]{2,}[A-Z0-9_]*|\w+\.\w+\(?\)?)\b")
MEANING_WORDS = re.compile(r"\b(?:not|no|never|none|cannot|can't|don't|doesn't|won't|must|required|should|may|might|only|unless|except|always|optional|before|after)\b", re.I)


def protect(text):
    """Swap code, links and addresses for numbered marks that a rewriter must leave alone."""
    spans = []

    def mark(match):
        spans.append(match[0])
        return f"⟦{len(spans) - 1}⟧"
    return PROTECTED.sub(mark, text), spans


def restore(text, spans):
    return MARK.sub(lambda m: spans[int(m[1])] if int(m[1]) < len(spans) else m[0], text)


def unit_hash(masked):
    return hashlib.sha1(masked.encode("utf-8")).hexdigest()


def check_rewrite(source, rewrite):
    """Hard faults reject a rewrite. Warnings only mark it for a human or second-model check."""
    faults, warnings = [], []
    if sorted(MARK.findall(source)) != sorted(MARK.findall(rewrite)):
        faults.append("code, link or address marks changed")
    if sorted(NUMBER.findall(MARK.sub(" ", source))) != sorted(NUMBER.findall(MARK.sub(" ", rewrite))):
        faults.append("numbers changed")
    missing = set(IDENTIFIER.findall(MARK.sub(" ", source))) - set(IDENTIFIER.findall(MARK.sub(" ", rewrite)))
    if missing:
        faults.append("names lost: " + ", ".join(sorted(missing)[:6]))
    if len(rewrite.split()) < 0.6 * len(source.split()):
        faults.append("too much shorter than the original")
    before, after = [collections.Counter(w.lower() for w in MEANING_WORDS.findall(t)) for t in (source, rewrite)]
    if before != after:
        warnings.append("words like not, must or only changed")
    return faults, warnings


FENCE_LINE = re.compile(r"(?m)^([\s>]*)```+[ \t]*([\w+-]*)(.*)$")
FENCE_FORMATTING = re.compile(r"\b(?:theme|highlight|icon|lines|focus)=(?:\{.*?\}(?=\s|$)|\"[^\"]*\"|'[^']*'|\S+)|\b(?:wrap|expandable|lines)\b")


def fence_label(info):
    """What a code block's opening line calls the block, without its display settings."""
    info = FENCE_FORMATTING.sub(" ", info or "")
    title = re.search(r"\b(?:title|filename)=[\"']([^\"']*)[\"']", info)
    rest = re.sub(r"\b(?:title|filename)=[\"'][^\"']*[\"']", " ", info).strip()
    return " ".join(x for x in (title[1] if title else "", rest) if x)


def tokens(text):
    return WORD.findall(LINK_TARGET.sub("]", PICTURE_ADDRESS.sub(" ", str(text))).lower())


def leaves(value, trail=""):
    """Every piece of text inside a nested record, with where it was found."""
    if isinstance(value, dict):
        for key, inner in value.items():
            if key in SKIP_KEYS or key.endswith("Html"):
                continue
            yield from leaves(inner, f"{trail}.{key}".lstrip("."))
    elif isinstance(value, list):
        for inner in value:
            yield from leaves(inner, trail)
    elif isinstance(value, str) and value.strip():
        yield trail, value


def step_parts(step):
    parts = [step.get("h", ""), step.get("t", ""), step.get("o") or "", step.get("code") or "", step.get("codeTitle") or ""]
    parts += [str(x) for x in step.get("a") or []]
    for key, value in (step.get("s") or {}).items():
        parts += [key, value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)]
    table = step.get("table") or {}
    parts += table.get("head", [])
    for row in table.get("rows", []):
        for cell in row:
            parts += [cell["t"], cell.get("o") or ""] if isinstance(cell, dict) else [str(cell)]
    parts += [choice.get("label", "") for choice in step.get("choices") or []]
    return parts


def item_text(item):
    parts = [item.get("title", ""), item.get("intro", ""), item.get("code") or "", *(item.get("codes") or {}).values()]
    for step in item.get("steps", []):
        parts += step_parts(step)
    for branch in (item.get("paths") or {}).values():
        for step in branch:
            parts += step_parts(step)
    return "\n".join(parts)


def add_leftovers(item, source):
    """Append any text from the source that the page has not used yet."""
    known = set(tokens(item_text(item)))
    rows = [[path, text] for path, text in leaves(source) if not set(tokens(text)) <= known]
    if rows:
        item["steps"].append({"h": "Everything else the source lists", "t": "These details come straight from the source, word for word.",
                              "table": {"head": ["Field", "Value"], "rows": rows}})
    return item
