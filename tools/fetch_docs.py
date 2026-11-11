"""Stage 1: save a local copy of the LangChain docs index, full text, sitemap and API specs."""
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "source" / "raw"
SPECS = RAW / "openapi"
SPECS.mkdir(parents=True, exist_ok=True)
SITE = "https://docs.langchain.com"


def download(url: str, target: pathlib.Path) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "langchain-lab-fetch/1.0"})
    with urllib.request.urlopen(request, timeout=180) as response:
        data = response.read()
    target.write_bytes(data)
    print(f"{len(data):>12,} bytes  {target.relative_to(ROOT)}")
    return data


index = download(f"{SITE}/llms.txt", RAW / "llms.txt").decode("utf-8")
download(f"{SITE}/llms-full.txt", RAW / "llms-full.txt")
download(f"{SITE}/sitemap.xml", RAW / "sitemap.xml")

section = index.split("OpenAPI Specs", 1)[-1].split("\n## ", 1)[0]
links = [link if link.startswith("http") else SITE + link
         for link in re.findall(r"\((https?://[^)\s]+|/[^)\s]+)\)", section)]
print("OpenAPI links:", links)
for number, link in enumerate(links, 1):
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", link.split("://", 1)[1])
    try:
        download(link, SPECS / f"{number}_{name}")
    except Exception as error:
        print(f"FAILED {link}: {error}")
