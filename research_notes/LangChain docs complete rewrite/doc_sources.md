# Inventory of public LangChain, LangGraph, LangSmith and Deep Agents documentation sources (checked 2026-11-10)

Method note: "direct request" means an HTTP request or `git` query made on 2026-11-10 from this PC, following redirects. Counts come from the GitHub tree API, a text-only shallow clone of `langchain-ai/docs` (commit `4db8ed56a4c7c8cbdca47053d9eee4fc57124ffd`, 2026-11-09), and a parse of the live `llms-full.txt` (16,968,987 bytes on 2026-11-10; the saved copy at `C:\Users\User\langchain-lab\source\raw\llms-full.txt` is 16,956,756 bytes, so it is already slightly behind).

## Summary inventory (what each source adds over llms-full.txt, and how to fetch it)

| # | Source | Status 2026-11-10 | Adds over llms-full.txt | Bulk method |
|---|---|---|---|---|
| 1 | 502 published `.md` pages not in llms-full.txt or the sitemap (348 Python, 149 JS, 5 other; 4.64 MB) | Live | **Largest text gap.** Mostly integration pages, e.g. `oss/python/integrations/chat/openai` | Derive URLs from repo `src/`, fetch `<url>.md` |
| 2 | `.md` versions of the 720 API-endpoint pages | Live | Full parameters and schema; llms-full.txt holds only a one-line stub for each | Fetch `<url>.md`, or the OpenAPI specs (row 3) |
| 3 | 4 OpenAPI specs (4.58 MB in total) | Live | Machine-readable API definitions | `curl` 4 URLs |
| 4 | `langchain-ai/docs` repo | Live, MIT | Raw MDX, fences, snippets, 772 files of runnable samples, 12 mermaid sources, 902 media files, 1,031 redirects | `git clone --depth 1` (616 MB), or text-only sparse clone (25 MB `src/`) |
| 5 | `reference.langchain.com` | Live | Generated API reference; not built from the docs repo | Sitemap (40,413 URLs) plus `.md` suffix |
| 6 | v0.1, v0.2, v0.3 docs in Git branches | Websites gone, branches live | Entire old docs | `git clone --depth 1 --branch v0.3 ...` |
| 7 | LangGraph MkDocs source at commit `23961cff` | Deleted from `main` 2026-01-09, still in history | Old LangGraph docs: 363 files | `git fetch` that commit, or GitHub tarball |
| 8 | `langsmith-docs` repo | Deprecated, public | Old LangSmith docs: 615 files, 643.8 MB | `git clone --depth 1` |
| 9 | `langchain-api-docs-html` repo | Archived | 5,663 rendered HTML API pages, 493.3 MB | `git clone --depth 1` |
| 10 | GitHub Releases (7 repos, 5,086 releases) and CHANGELOG.md files | Live | Per-package release notes | REST API, paginated; use a token |
| 11 | Academy course repos (13) and cookbooks | Live or archived | Notebooks and course code | `git clone` each |

---

## Is langchain-ai/docs the source of docs.langchain.com, and what does it hold that llms-full.txt strips? Does llms-full.txt include both Python and TypeScript?

### Takeaway
Yes, the repo is the source. llms-full.txt holds Python and JavaScript as separate per-language pages (not tabs) for the OSS docs, with fences resolved and snippets inlined, so little prose is lost from the pages it includes. But it omits about 500 published pages entirely, and the repo additionally holds raw sources and runnable samples that never reach it.

### Cited Findings
- The README says the repo "contains the documentation build pipeline", that docs.langchain.com is "hosted on Mintlify", and that `.mdx` sources in `/src` are preprocessed into `/build`, which Mintlify deploys — [README](https://github.com/langchain-ai/docs/blob/main/README.md). GitHub lists the homepage as docs.langchain.com, description "Unified LangChain documentation.", default branch `main`, last push 2026-11-09, not archived — [GitHub API](https://api.github.com/repos/langchain-ai/docs).
- The site `reference.langchain.com` is explicitly "**not** built from this repository" — [README](https://github.com/langchain-ai/docs/blob/main/README.md).
- Repo size: 5,071 tree entries, 615.9 MB of files at HEAD; 2,795 `.mdx` (18.65 MB), 355 `.ts`, 317 `.py`, 64 `.kt`, 57 `.go`, 20 `.java`, 0 `.ipynb` — [Git tree API](https://api.github.com/repos/langchain-ai/docs/git/trees/main?recursive=1). (The README still describes notebooks as a supported format, but none exist at HEAD.)
- Of the 2,795 MDX files, 1,358 are page sources and 1,437 are snippets under `src/snippets/` (1,305 entries under `src/snippets/code-samples`) — parse of a shallow clone of [the repo](https://github.com/langchain-ai/docs).
- `src/code-samples/` holds 772 standalone files described as "Testable standalone code samples"; breakdown: langsmith 307, deepagents 223, langgraph 118, langchain 115 — [AGENTS.md](https://github.com/langchain-ai/docs/blob/main/AGENTS.md); [Git tree API](https://api.github.com/repos/langchain-ai/docs/git/trees/main?recursive=1).
- Language conditionals: "Every shared page under `src/oss/` builds a Python and a JavaScript version, and the fences decide what each version keeps"; fences are `:::python` and `:::js` — [AGENTS.md](https://github.com/langchain-ai/docs/blob/main/AGENTS.md). Count in page sources: 1,696 `:::python` in 177 files, 1,617 `:::js` in 176 files; 1,356 MDX import lines in 336 page files — parse of [repo](https://github.com/langchain-ai/docs).
- Deep Agents Code and OpenWiki have a single set of pages with no language split, and their fences "resolve against the Python branch" — [AGENTS.md](https://github.com/langchain-ai/docs/blob/main/AGENTS.md).
- `src/docs.json` holds site navigation and 1,031 redirect rules (old path to new path) — [docs.json](https://github.com/langchain-ai/docs/blob/main/src/docs.json).
- llms-full.txt contains 1,727 sections (`# title` then `Source: URL`), including 192 under `/oss/python/` and 199 under `/oss/javascript/`; 182 paths exist in both, 10 are Python-only, 17 JS-only — parse of [llms-full.txt](https://docs.langchain.com/llms-full.txt).
- OSS pages are single-language per URL: the Python Agents section has 106 Python code fences and 0 TypeScript; the JS section has 0 Python and 106 TypeScript. Only 1 `[tab] TypeScript` appears anywhere in OSS sections — parse of [llms-full.txt](https://docs.langchain.com/llms-full.txt).
- LangSmith pages are a different case: one URL, tabs preserved and flattened as `> [tab] Label` (Python 190, cURL 136, TypeScript 89, Go 69, Java 68, Javascript 48, JavaScript 36) — parse of [llms-full.txt](https://docs.langchain.com/llms-full.txt).
- In llms-full.txt, Mintlify components are flattened to text markers (`> [card]` 1,923; `> [tab]` 1,905; `> [accordion]` 718), MDX import lines are absent (0), and start-of-line fences are nearly absent (2 `:::python`, 2 `:::js`) — parse of [llms-full.txt](https://docs.langchain.com/llms-full.txt).
- `agents.mdx` is 18,771 bytes at source against 65,432 characters for its Python section in llms-full.txt, because it imports code-sample snippets — [source](https://github.com/langchain-ai/docs/blob/main/src/oss/langchain/agents.mdx); [llms-full.txt](https://docs.langchain.com/llms-full.txt).
- Its frontmatter has `keywords` and `boost` fields, which do not appear in the llms-full.txt section (only title, Source and description do) — [source](https://github.com/langchain-ai/docs/blob/main/src/oss/langchain/agents.mdx).
- MDX comments number 402 in page files and 52 in snippets, against 15 `{/*` strings in llms-full.txt — parse of [repo](https://github.com/langchain-ai/docs) and [llms-full.txt](https://docs.langchain.com/llms-full.txt).
- **Pages missing from llms-full.txt:** of 1,358 page sources, 546 have no matching URL in the sitemap or llms-full.txt. Requesting their `.md` URLs (587 candidates, some shared sources map to two languages) gave: 502 returned 200 at the same URL (348 `/oss/python/`, 149 `/oss/javascript/`, 5 other; 4,643,474 bytes in total; median 6,224 bytes); 71 redirected to other pages; 12 returned 404 (mostly `TEMPLATE` files); 2 timed out and need a retry — direct requests, derived from [repo](https://github.com/langchain-ai/docs) and [sitemap](https://docs.langchain.com/sitemap.xml).
- Examples present on the site but absent from llms-full.txt: [Python ChatOpenAI integration](https://docs.langchain.com/oss/python/integrations/chat/openai.md) (81,513 bytes), [Python ChatAnthropic](https://docs.langchain.com/oss/python/integrations/chat/anthropic.md) (119,459 bytes), [Chroma vector store](https://docs.langchain.com/oss/python/integrations/vectorstores/chroma.md) (20,440 bytes). Largest groups: Python providers 91, tools 38, chat 36, vectorstores 33, embeddings 27, document loaders 25 — direct requests.
- Only 1 of the 502 has `noindex: true`; 69 of the 71 redirected ones do — parse of [repo](https://github.com/langchain-ai/docs) frontmatter.
- The site's index files disagree slightly: sitemap 1,727 URLs, llms-full.txt 1,727 sections, `llms.txt` top groups 1,506 + 223 = 1,729 pages — [sitemap](https://docs.langchain.com/sitemap.xml); [llms.txt](https://docs.langchain.com/llms.txt).
- `llms.txt` is now only a 3,129-byte index of nested `/_llms/*.txt` indexes (for example [build/python](https://docs.langchain.com/_llms/agent-development-lifecycle/build/python.txt)) and links three OpenAPI specs — [llms.txt](https://docs.langchain.com/llms.txt).

### Inferences
- The 502 pages are the main hole in the current offline copy: 4.64 MB is about 27% on top of 16.97 MB, and they outnumber the 391 OSS pages llms-full.txt does hold. Integration coverage for Python is especially thin in llms-full.txt, so some "JS-only" results above are an artefact of Python pages being left out.
- The pattern suggests the omission follows the site's navigation (integration pages are linked from index pages rather than listed in `docs.json`, per AGENTS.md's note on editing only the component index page), but I did not confirm the exact rule Mintlify applies.
- The 2 start-of-line `:::python` and `:::js` hits and 15 `{/*` strings in llms-full.txt are probably literal mentions in contributor docs or code; not individually checked.
- Rebuilding from `src/` is not required to get complete prose. The repo's unique value is the 772 runnable samples, diagram sources, redirect map and the single-source view of each shared page.

### Gaps
- Could not determine why those 502 pages are excluded; no official statement found.
- Did not run the repo's own build (`make build`), so generated `/build` output was not compared directly.

---

## Are per-page .md URLs fuller than the matching llms-full.txt section?

### Takeaway
For prose pages, no: they are the same content. For the 720 API-endpoint pages, yes, greatly: llms-full.txt has only a one-line stub.

### Cited Findings
- Line-level diff of 20 sampled pages (6 chosen, 14 random) between the llms-full.txt section and its `.md` URL. In all 19 prose pages, the `.md` had exactly 2 more differing lines than the section. The differences seen were a 3-line "Documentation Index" banner, the description rendered as a blockquote, and links made absolute with a `.md` suffix — direct requests, e.g. [agents.md](https://docs.langchain.com/oss/python/langchain/agents.md) (66,504 characters against 65,432 in the section).
- The exception: `langsmith/agent-server-api/threads/search-threads` is 249 characters in llms-full.txt and 9,171 in its [.md](https://docs.langchain.com/langsmith/agent-server-api/threads/search-threads.md), which adds the OpenAPI definition inline.
- 720 of the 1,727 sections are such stubs (235,592 bytes in total): 595 against `/langsmith/langsmith-platform-openapi.json`, 64 against `/langsmith/agent-server-openapi.json`, 61 against `https://api.host.langchain.com/openapi.json` — parse of [llms-full.txt](https://docs.langchain.com/llms-full.txt).
- Specs are downloadable (direct requests): [langsmith-platform-openapi.json](https://docs.langchain.com/langsmith/langsmith-platform-openapi.json) 2,731,781 bytes; [agent-server-openapi.json](https://docs.langchain.com/langsmith/agent-server-openapi.json) 235,591 bytes; [api.host openapi.json](https://api.host.langchain.com/openapi.json) 173,476 bytes; [api.smith openapi.json](https://api.smith.langchain.com/openapi.json) 1,441,190 bytes.

### Inferences
- Prose pages need no re-download for completeness. The existing 1,726 files in `source/pages` were not audited here: if they came from `.md` URLs, the 720 API pages are already expanded (that folder's 20 MB is larger than llms-full.txt, which is consistent with this, but unconfirmed).

### Gaps
- The sample is 20 of 1,727 pages. Differences beyond the first few displayed lines were judged from line counts, not read one by one.

---

## How are images and diagrams stored, and how many are there?

### Takeaway
902 media files (587.5 MB) are in the repo, mostly in `src/langsmith/images`, `src/oss/images` and `src/images`. llms-full.txt only links to them on Mintlify's CDN. Diagrams are 120 inline mermaid blocks, 12 `.mmd` sources and 4 Excalidraw files.

### Cited Findings
- Media in the repo: 712 PNG (164.27 MB), 130 SVG (0.43 MB), 45 GIF (418.43 MB), 11 JPG (2.58 MB), 4 MP4 (1.8 MB); total 902 files, 587.5 MB — [Git tree API](https://api.github.com/repos/langchain-ai/docs/git/trees/main?recursive=1).
- Main locations: `src/langsmith/images` (546 entries), `src/oss/images` (151), `src/images` (196, including `providers/{dark,light}` logos, 46 each, and `brand`) — [Git tree API](https://api.github.com/repos/langchain-ai/docs/git/trees/main?recursive=1).
- Mermaid sources: 12 `.mmd` files at `src/oss/langchain/multi-agent/mermaid/` — [Git tree API](https://api.github.com/repos/langchain-ai/docs/git/trees/main?recursive=1).
- Inline mermaid: 120 fenced blocks in 77 page files, 0 in snippets — parse of [repo](https://github.com/langchain-ai/docs). llms-full.txt has 179 (Python and JS copies of shared pages counted separately) — [llms-full.txt](https://docs.langchain.com/llms-full.txt).
- Excalidraw sources: 4 (three in `src/images/self-hosted-terraform/`, one in `src/langsmith/images/`) — [Git tree API](https://api.github.com/repos/langchain-ai/docs/git/trees/main?recursive=1).
- Image references in llms-full.txt: 1,771 markdown images (1,190 unique), 0 HTML `<img>`. By host: static.pepy.tech 927, mintcdn.com 541, img.shields.io 298, vercel.com 3, netlify.com 2. CDN URLs look like `mintcdn.com/langchain-5e9cc07a/<hash>/langsmith/images/define-conditions.png?...&s=<sig>` — parse of [llms-full.txt](https://docs.langchain.com/llms-full.txt).

### Inferences
- About two-thirds of image references are download-count and version badges, not content; only the 541 CDN links are real docs images.
- The CDN path after the hash appears to mirror the repo path under `src/`, so a local copy can rewrite links to repo files rather than scrape the CDN. The 45 GIFs are 71% of the media weight; skipping them cuts the copy to about 169 MB.

### Gaps
- I stopped the full shallow clone after it reached 379 MB of `.git`, as a blob-limited clone was enough for counting. Full-clone time and final size are not measured; the 616 MB figure is the sum of file sizes from the tree API.
- Did not check how many of the 902 media files are actually referenced by a page.

---

## What older or versioned docs remain public, and are they live or redirected?

### Takeaway
No old website is live. Every legacy domain redirects to the current docs, losing the old content at the URL. The old content survives in Git branches and history, in a deprecated repo, in an archived HTML repo, and in the Wayback Machine.

### Cited Findings
Direct requests, 2026-11-10:

| Legacy URL | Result |
|---|---|
| [python.langchain.com](https://python.langchain.com/), `/docs/introduction/`, `/docs/how_to/`, `/docs/versions/v0_3`, `/v0.1/...`, `/v0.2/...`, `/v0.3/...` | All redirect to `docs.langchain.com/oss/python/langchain/overview` |
| [python.langchain.com/api_reference](https://python.langchain.com/api_reference) | **Still 200**, 25,324-byte Sphinx page titled "LangChain Python API Reference", langchain-core 0.3.79. Sub-pages redirect to reference.langchain.com |
| [api.python.langchain.com](https://api.python.langchain.com/) | Redirects to `reference.langchain.com/?lang=python` |
| [js.langchain.com](https://js.langchain.com/), `/docs/introduction/`, `/v0.2/...`, `/docs/versions/v0_3` | Redirect to `docs.langchain.com/oss/javascript/langchain/overview` |
| [api.js.langchain.com](https://api.js.langchain.com/), [v03.api.js.langchain.com](https://v03.api.js.langchain.com/) | Redirect to `reference.langchain.com/?lang=javascript` |
| [langchain-ai.github.io/langgraph/](https://langchain-ai.github.io/langgraph/) and deep links | HTTP 200, but a 546–757 byte stub: "Documentation has moved", meta-refresh to docs.langchain.com |
| [langchain-ai.github.io/langgraphjs/](https://langchain-ai.github.io/langgraphjs/) and deep links | Same stub |
| [docs.smith.langchain.com](https://docs.smith.langchain.com/) | Redirects to `docs.langchain.com/langsmith/observability` |
| [changelog.langchain.com](https://changelog.langchain.com/) | Redirects to `docs.langchain.com/langsmith/changelog` |
| [reference.langchain.com/v0.3/python](https://reference.langchain.com/v0.3/python) | Redirects to current reference; deep v0.3 links map to current packages |
| [reference.langchain.com/v0.3/javascript](https://reference.langchain.com/v0.3/javascript) | 404 |
| langchain-ai.github.io root and `/langchain/` | 404 |
| langchain-ai.lang.chat | No response (HTTP 000) |

Surviving copies:
- `langchain-ai/langchain` branches: `v0.1` `docs/` 1,499 files, 50.8 MB (962 `.ipynb`, 311 `.mdx`); `v0.2` `docs/` 1,539 files, 59.3 MB (979 `.ipynb`, 318 `.mdx`); `v0.3` `docs/` 2,297 files, 138 MB (1,137 `.ipynb`, 441 `.mdx`, 454 `.zlib`) — [v0.1](https://github.com/langchain-ai/langchain/tree/v0.1/docs), [v0.2](https://github.com/langchain-ai/langchain/tree/v0.2/docs), [v0.3](https://github.com/langchain-ai/langchain/tree/v0.3/docs/docs). Within v0.3 `docs/docs/`: integrations 1,376, how_to 148, concepts 33, versions 25, tutorials 12 — [Git tree API](https://api.github.com/repos/langchain-ai/langchain/git/trees/v0.3?recursive=1).
- A `v0.4` branch and `v0.0.339` also exist on that repo; not counted — direct `git ls-remote`.
- `docs/` no longer exists on `master` of langchain (404) — [master/docs](https://github.com/langchain-ai/langchain/tree/master/docs).
- `langchain-ai/langchainjs` `v0.3` `docs/core_docs/docs/`: 537 files, 10.2 MB (318 `.mdx`, 200 `.ipynb`) — [tree](https://github.com/langchain-ai/langchainjs/tree/v0.3/docs/core_docs/docs). `v0.1` and `v0.2` branches also exist (`git ls-remote`); not counted.
- LangGraph docs were removed from `main` by commit `b4630d84` ("chore: delete docs (#6488)", 2026-01-09). Parent `23961cff` still has `docs/docs/`: 363 files, 60.4 MB (161 `.md`, 38 `.ipynb`, 115 `.png`) — [GitHub API](https://api.github.com/repos/langchain-ai/langgraph/git/trees/23961cff61a42b52525f3b20b4094d8d2fba1744?recursive=1).
- `langchain-ai/langgraphjs` `main` still has `docs/`: 176 files, 15.4 MB (59 `.md`) — [Git tree API](https://api.github.com/repos/langchain-ai/langgraphjs/git/trees/main?recursive=1).
- `langchain-ai/langsmith-docs` is public, with README "This repo is deprecated"; `docs/` has 615 files, 643.8 MB (186 `.mdx`, 368 `.png`, 44 `.gif`); last push 2026-06-28, MIT — [README](https://github.com/langchain-ai/langsmith-docs), [Git tree API](https://api.github.com/repos/langchain-ai/langsmith-docs/git/trees/main?recursive=1).
- `langchain-ai/langchain-api-docs-html` is archived, "DEPRECATED/ARCHIVED": 5,711 files, 493.3 MB, 5,663 HTML — [repo](https://github.com/langchain-ai/langchain-api-docs-html).
- Wayback Machine last 200-status captures found: python how_to 2025-10-24; python v0.1 intro 2025-09-04; js how_to 2025-10-09; docs.smith root 2025-08-20; langgraph how-tos 2025-04-27 — [CDX API](https://web.archive.org/cdx/search/cdx?url=python.langchain.com/docs/how_to/&output=json&limit=-3&filter=statuscode:200). (Labelled older: these are the most recent successful captures, not a guarantee of completeness.)
- Migration history: on 2025-08-01 LangChain announced the LangGraph Platform docs were live on docs.langchain.com, with "the LangChain, LangGraph, and LangSmith docs" to follow "over the next few weeks" — [forum](https://forum.langchain.com/t/docs-migration-new-langgraph-platform-docs-are-now-live/877) (older, 2025).

### Inferences
- Git is the practical way to get old docs. Notebooks must be rendered or converted, since the old sites published them as pages. The `.zlib` files on v0.3 are probably compressed notebook data; contents not inspected.
- A blanket scrape of legacy domains would yield only duplicates of current pages, so it should be skipped.
- `langchain-api-docs-html` is probably the built output of the old Python API reference, matching the v0.3-era `python.langchain.com/api_reference`. I did not confirm which version it holds.

### Gaps
- The v0.1 and v0.2 JS branches, the `v0.4` branch and the `langchain-api-docs-html` contents were not examined in detail.
- A search result pointed to `reference.langchain.com/v0.3/python` as a live versioned reference; direct requests showed it now redirects, so that snippet is out of date.

---

## Which other official text belongs in a complete copy?

### Takeaway
Three groups sit outside llms-full.txt: generated API reference, GitHub release notes and changelog files, and Academy, cookbook and example repos. Academy video and any hosted lesson text could not be confirmed as available without enrolling.

### Cited Findings
**API reference**
- `reference.langchain.com`: sitemap has 40,413 URLs (from the project's saved sitemap of 8,718,000 bytes, same size as live). `.md` is available by suffix ("All pages are available as markdown by appending `.md` to the URL"); its `llms-full.txt` (512,105 bytes) is a symbol index that "may be truncated" — [llms.txt](https://reference.langchain.com/llms.txt), [llms-full.txt](https://reference.langchain.com/llms-full.txt), [sitemap](https://reference.langchain.com/sitemap.xml).

**Changelogs inside llms-full.txt already** (no action needed)
- `langsmith/changelog`, `agent-server-changelog`, `fleet/changelog`, `self-hosted-changelog`, `oss/python/releases/changelog`, `oss/javascript/releases/changelog`, plus v1 release notes for LangChain and LangGraph — parse of [llms-full.txt](https://docs.langchain.com/llms-full.txt).

**Changelogs outside it**
- Stub pages forward to GitHub: `oss/deepagents/code/changelog` to `langchain-ai/deepagents/blob/main/libs/code/CHANGELOG.md`; `langsmith/python/managed-deep-agents-changelog` to `langchain-ai/managed-deepagents/blob/main/CHANGELOG.md`; `oss/openwiki/changelog` to `langchain-ai/openwiki/releases` — direct requests.
- GitHub Releases counts: langchain 1,414; langchainjs 1,276; langgraph 599; langgraphjs 765; deepagents 338; deepagentsjs 190; langsmith-sdk 504; total 5,086 — [GitHub API](https://api.github.com/repos/langchain-ai/langchain/releases?per_page=1) (`Link` header, same for each repo). Bulk: `GET /repos/{owner}/{repo}/releases?per_page=100` with paging, about 54 requests in total, which needs a token at the 60-per-hour anonymous limit.

**LangChain Academy**
- Site is live; FAQ says "Our course content is always free!", with a paid certification exam — [academy](https://academy.langchain.com/). Course catalogue at [/collections](https://academy.langchain.com/collections); the HTML exposed 5 course links (foundation-introduction-to-deepagents, foundation-introduction-to-langchain-python, intro-to-langgraph, langsmith-engine, quickstart-langsmith-essentials). The course page has a free-enrolment link on a Thinkific-style checkout — [course page](https://academy.langchain.com/courses/foundation-introduction-to-langchain-python).
- Course code repos: [langchain-academy](https://github.com/langchain-ai/langchain-academy) (70 files, 30 `.ipynb`, MIT); `lca-lc-foundations`, `lca-langgraph-essentials`, `lca-langchainV1-essentials`, `lca-deployment`, `lca-production-monitoring`, `lca-reliable-agents` (MIT); `lca-deepagents`, `lca-engine`, `lca-langsmith-essentials`, `lca-skills`, `lca-tutors`, `lca_dcode` (no licence detected) — [GitHub org API](https://api.github.com/orgs/langchain-ai/repos).

**Cookbooks and example repos** (file counts from the [Git tree API](https://api.github.com/repos/langchain-ai/cookbooks/git/trees/main?recursive=1))
- `langchain-ai/cookbooks`: 114 files, 4 `.ipynb`, MIT, last push 2025-10-10.
- `langchain-ai/deployment-cookbook`: 246 files, MIT. `langchain-ai/streaming-cookbook`: 353 files, Apache-2.0.
- `langchain-ai/langsmith-cookbook`: archived, 199 files, 43 `.ipynb`, 125.2 MB, no licence detected.
- `langchain` `v0.3` `cookbook/`: 104 files, 101 `.ipynb`, 32.4 MB; removed from `master` (404) — [tree](https://github.com/langchain-ai/langchain/tree/v0.3/cookbook).
- `langgraph` `examples/`: 39 files, 35 `.ipynb`. `langgraphjs` `examples/`: 389 files, 76 `.ipynb`. `deepagents` `examples/`: 119 files, 41 `.md`.
- `langgraph-101` (75 files, 7 `.ipynb`), `langgraph-101-ts`, `ambient-agent-101`, `langsmith-agent-lifecycle-workshop` (Apache-2.0), `modular-workshops` — [GitHub org API](https://api.github.com/orgs/langchain-ai/repos).
- The `langchain-samples` GitHub organisation has 131 repositories of customer-team examples per a search listing; not independently counted — [org page](https://github.com/langchain-samples).

**Other public text**
- Blog: [www.langchain.com/blog](https://www.langchain.com/blog) (`blog.langchain.com` redirects there); [site sitemap](https://www.langchain.com/sitemap.xml) is 107,195 bytes; post count not measured. [Forum](https://forum.langchain.com/) and [chat.langchain.com](https://chat.langchain.com/) are live, but are community or interactive, not documentation.

### Inferences
- For a learning copy, in priority order after the 502 missing pages: Academy repos, `cookbooks`, `langgraph-101`, then the v0.3 branches. Release notes are large and of low value to learners unless a specific version is being studied.
- `langchain-ai/langsmith-sdk` showed as archived (last push 2026-10-16) while releases remain listed; the reason was not investigated.

### Gaps
- Could not verify whether Academy lesson text or video transcripts can be retrieved without enrolling. The full course count is not stated on the pages checked, and the 5 links found may be only part of a dynamically loaded catalogue.
- Blog post count and forum size not measured.

---

## What licence covers the docs repository content?

### Takeaway
The `langchain-ai/docs` repository carries an MIT licence file, and GitHub detects it as MIT. Nothing in the file separates documentation text from code.

### Cited Findings
- `LICENSE` is standard MIT text, "Copyright (c) 2025 LangChain" — [LICENSE](https://github.com/langchain-ai/docs/blob/main/LICENSE). GitHub reports `spdx_id: MIT` — [GitHub API](https://api.github.com/repos/langchain-ai/docs).
- It covers "this software and associated documentation files", and its terms require the copyright and permission notice to be kept in copies or substantial portions — [LICENSE](https://github.com/langchain-ai/docs/blob/main/LICENSE).
- Other repos: `langchain`, `langchainjs`, `langgraph`, `langgraphjs`, `deepagents`, `deepagentsjs`, `langsmith-docs`, `langchain-academy` are MIT; `streaming-cookbook` and `langsmith-agent-lifecycle-workshop` are Apache-2.0; `langsmith-cookbook` and several `lca-*` repos have no detected licence — [GitHub API](https://api.github.com/orgs/langchain-ai/repos).
- `docs.langchain.com/robots.txt` declares `Content-Signal: ai-train=yes, search=yes, ai-input=yes` and allows general crawling apart from `/cdn-cgi/` and `/_next/` — [robots.txt](https://docs.langchain.com/robots.txt).

### Inferences
- Repos with no detected licence default to no stated grant, which is worth noting if any of their content is ever redistributed; it is less likely to matter for a private offline copy.
- Third-party logos under `src/images/providers/` and brand images may carry their own trademark considerations regardless of the repo licence. This was not examined.

### Gaps
- Did not review terms of use on langchain.com or academy.langchain.com, or any separate licence for Academy video content.
- `reference.langchain.com` is generated output of the package repos (MIT for the main ones checked), but no licence statement was found on that site itself.
