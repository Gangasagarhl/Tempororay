"""Pilot 2: member, parameter, module and package record shapes."""
import json
import urllib.error
import urllib.request

BASE = "https://reference.langchain.com/"
UA = "langchain-lab-fetch/1.0"


def get(path):
    request = urllib.request.Request(BASE + path, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            return response.status, response.headers.get("content-type", ""), response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        return error.code, error.headers.get("content-type", ""), error.read().decode("utf-8", "replace")[:200]


def trim(value, depth=0):
    if isinstance(value, dict):
        return {k: trim(v, depth + 1) for k, v in list(value.items())[:24]}
    if isinstance(value, list):
        return [len(value), trim(value[0], depth + 1)] if value else []
    return value[:70] if isinstance(value, str) else value


_, _, body = get("python/langchain/agents/factory/create_agent")
data = json.loads(body)
print("PARAM", json.dumps(trim(data["params"][0]))[:500])
print("TYPEREF", json.dumps(trim(data["typeRefs"][0]))[:300])
_, _, body = get("python/langchain-core/runnables/base/Runnable")
data = json.loads(body)
print("MEMBER", json.dumps(trim(data["members"][0]))[:700])
print("MEMBER KINDS", sorted({m.get("kind") for m in data["members"]}))
print("MEMBER KEYS", sorted({k for m in data["members"] for k in m}))
_, _, body = get("python/langchain-openai/chat_models/base/ChatOpenAI")
data = json.loads(body)
print("CHATOPENAI members", [(m.get("name"), m.get("kind")) for m in data["members"]][:10], "doc chars", len(data["docs"].get("summary", "")))
print("TOP KEYS", sorted(data))
for path in ["python/langchain-core/runnables/base/Runnable/invoke", "python/langchain-core/runnables/base",
             "python/langchain", "python/langgraph/types/Interrupt", "javascript/langchain", "java/langsmith-java", "go"]:
    status, kind, body = get(path)
    print(f"\n{path}: {status} {kind} {len(body)}")
    if "json" in kind:
        print(json.dumps(trim(json.loads(body)))[:900])
    else:
        print(body[:200])
