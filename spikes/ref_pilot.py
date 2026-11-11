"""Pilot: what do reference pages return, and does an honest client name get JSON?"""
import json
import urllib.error
import urllib.request

BASE = "https://reference.langchain.com/python/"
PAGES = ["langchain/agents/factory/create_agent", "langchain-openai/chat_models/base/ChatOpenAI",
         "langchain-core/runnables/base/Runnable", "langchain-core/messages/ai/AIMessage",
         "langchain-community/cache/InMemoryCache"]
UA = "langchain-lab-fetch/1.0"


def get(url, accept):
    request = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            return response.status, response.headers.get("content-type", ""), response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        return error.code, error.headers.get("content-type", ""), error.read().decode("utf-8", "replace")


def shape(value, depth=0):
    if isinstance(value, dict):
        return {k: shape(v, depth + 1) for k, v in list(value.items())[:30]} if depth < 2 else "{...}"
    if isinstance(value, list):
        return [len(value), shape(value[0], depth + 1)] if value else []
    return type(value).__name__ if not isinstance(value, str) else (value[:50])


for page in PAGES:
    status, kind, body = get(BASE + page, "application/json")
    print(f"\n=== {page}\nJSON try: {status} {kind} {len(body)}")
    if "json" in kind:
        data = json.loads(body)
        print(json.dumps(shape(data), ensure_ascii=False)[:1500])
    status, kind, body = get(BASE + page + ".md", "text/markdown")
    print(f"MD: {status} {kind} {len(body)}; head: {body[:200]!r}")
