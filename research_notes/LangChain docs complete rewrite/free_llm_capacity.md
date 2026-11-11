# Free LLM capacity for bulk English rewriting (about 3M words), as of 2026-11-10

All pages below were read on 2026-11-10 unless marked otherwise. Workload assumed throughout: 4.0M input tokens and 4.0M to 5.0M output tokens (midpoint 4.5M, so output is 52.9% of total tokens and input is 0.889 tokens per output token).

Source labels: **Official** = read from the provider's own page. **Third-party** = not from the provider's page; treat as unconfirmed. **Search excerpt** = seen only in a search result, page not opened.

## What are the current free allowances for each provider?

### Takeaway
Only Google AI Studio appears able to do millions of output tokens a day with no card, but Google does not publish the numbers, so they must be confirmed in the AI Studio console. Cerebras needs a payment method, Mistral's docs say the API needs billing activation, GitHub Models is retired, and Hugging Face and Together offer nothing free for this job.

### Cited Findings

| Provider | Free limits (date read 2026-11-10) | Models | Card / phone | Training on free input | Label |
|---|---|---|---|---|---|
| Google AI Studio (Gemini) | Flash-Lite 3.5 and 3.1: 10 RPM, 250K input TPM, 500 RPD each. Flash 3.8 and 3.6: 5 RPM, 250K TPM, 20 RPD each. Per project and model. RPD resets at midnight Pacific. | Free tier also covers 2.5 Flash-Lite and Gemma 4 (limits not found). 2.5 Pro and 2.5 Flash are deprecated and reroute on 2026-12-01. | Not stated on pages read | Yes: "Used to improve our products" is Yes for free models, and human reviewers may read it | Numbers: Third-party. Model list, reset, training: Official |
| SambaNova | 20 RPM, 20 RPD, 200K TPD for each listed model | DeepSeek-V3.1, Llama-3.3-70B, gpt-oss-120b, DeepSeek-V3.2 (preview), gemma-4-31B (preview) | Free Tier applies when no payment method is linked | Not read | Official |
| Cloudflare Workers AI | 10,000 neurons/day, reset 00:00 UTC; 300 RPM for text generation unless the model requires Workers Paid | About 30 usable LLMs. Paid billing required for kimi-k2.6, kimi-k2.7-code, glm-5.2, glm-5.3, glm-5.3-flash and the three deepseek-v4 models | No card, per an October 2026 roundup (Third-party) | Not read | Official limits |
| Groq | Developer plan base: gpt-oss-120b, gpt-oss-20b, qwen3.8-27b each 30 RPM, 1K RPD, 8K TPM, 200K TPD. The Free tab's numbers did not render; the page implies Free is lower | Same | Not read | Not stated. No retention by default; logs up to 30 days for errors or abuse | Official, but Developer plan only: use as a ceiling |
| OpenRouter `:free` | 20 RPM, 50 RPD with under 10 credits bought (1,000 RPD with at least 10 credits, which breaks the $0 rule) | 12 free models live on 2026-11-10, including gemma-4-26b and 31b, nemotron-3-ultra-550b, nemotron-3.5-lightning | Not read | Varies by model; terms say some models "may store or train on your Inputs" | Official |
| Cohere | 1,000 API calls per month; 20 req/min on chat models | Command A+, Command R+, Command R, Command R7B, North Mini Code, others | Not read | Not read | Official |
| NVIDIA NIM | No published quota found. About 40 RPM is the common community figure. Community says credits were removed | Many, including deepseek-v4.1-flash, gpt-oss-20b, nemotron | Phone per one community list only | Terms: generally not stored after the session (Search excerpt) | Third-party / Search excerpt |
| Cerebras | Free Trial: gpt-oss-120b and qwen-3.8-27b, 5 RPM, 30K uncached TPM, 1M TPH, 1M TPD | Those two | **Payment method required** for the one-time $5 credit; expires after 30 days | Not stated | Official. Fails the no-card rule |
| Mistral | Docs: Free mode "doesn't include API access"; API keys and API use "require billing activation and pay-as-you-go" | n/a | Help centre search excerpt describes an Experiment plan needing a phone | Search excerpts: Experiment data may be trained on, with opt-out | Official conflicts with older pages (below) |
| Hugging Face | Free users: None; credits must be bought | n/a | n/a | n/a | Official |
| Together | No free trial | n/a | n/a | n/a | Search excerpt of official help page, updated 2026-06-01 |
| GitHub Models | Retired 2026-07-30: playground, catalog, inference API and BYOK all gone | n/a | n/a | n/a | Official |
| OpenCode Zen free | Only stated cap is LongCat 2.5 Free at 100 requests/day. None stated for DeepSeek V4.1 Flash Free or GLM-5.3 Flash Free | See OpenCode section | n/a | Both named models: zero retention, no training | Official |

Sources for the table:
- Google: [AI Studio pricing](https://aistudio.google.com/docs/pricing); [AI Studio rate limits](https://aistudio.google.com/docs/rate-limits) (per project, midnight Pacific reset, no free-tier numbers shown); [Scriptbyai](https://www.scriptbyai.com/gemini-api-free-tier-limits/) (the only table found; says it comes from the AI Studio Rate Limits page; undated, image folder suggests 2026-09); [BenchLM](https://benchlm.ai/md/free-tier/google-ai-studio.md) confirms Google lists these as "Unpublished" (read 2026-10-16); [Gemini API terms](https://aistudio.google.com/docs/terms) effective 2026-03-23.
- Other Gemini figures conflict: a search result listed 1,500 RPD and 30 RPM for 3.1 Flash-Lite at [freellm.net](https://freellm.net/models/google-gemini/gemini-3-1-flash-lite). This note uses the lower 500.
- [SambaNova rate limits](https://docs.sambanova.ai/docs/en/models/rate-limits).
- [Cloudflare pricing](https://developers.cloudflare.com/workers-ai/platform/pricing/) (updated 2026-10-20); [Cloudflare limits](https://developers.cloudflare.com/workers-ai/platform/limits/) (updated 2026-09-17); no-card claim from [Apidog roundup](https://apidog.com/blog/free-ai-api/).
- [Groq rate limits](https://console.groq.com/docs/rate-limits); [Groq data page](https://console.groq.com/docs/your-data). Third-party reports that the Llama models moved to Enterprise-only on 2026-08-26: [UsagePricing](https://www.usagepricing.com/blueprint/activity/groq-2026-08-26-llama-enterprise-only). They are absent from the official table, which agrees.
- [OpenRouter limits](https://openrouter.ai/docs/api/reference/limits); [OpenRouter live model list](https://openrouter.ai/api/v1/models); [OpenRouter terms](https://openrouter.ai/terms).
- [Cohere rate limits](https://docs.cohere.com/docs/rate-limits).
- NVIDIA: [developer forum: "Is NIM free"](https://forums.developer.nvidia.com/t/is-nim-free/369368) (community replies, 2026-05); [NVIDIA API Trial Terms PDF](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf) (search excerpt, not opened).
- [Cerebras rate limits](https://inference-docs.cerebras.ai/support/rate-limits); [Cerebras pricing](https://www.cerebras.ai/pricing).
- Mistral: [usage limits docs](https://docs.mistral.ai/admin/billing-usage/usage-limits); [help article dated 2026-08-12](https://help.mistral.ai/en/articles/698531-why-am-i-hitting-api-rate-limits-and-how-do-i-increase-them) (Free mode is "intended for evaluation and prototyping"). Third-party trackers still claim about 1 RPS, 500K TPM, 1B tokens/month at [free-llm.com](https://free-llm.com/provider/mistral-ai), which contradicts the docs page. [Experiment plan help page](https://help.mistral.ai/en/articles/450104-how-can-i-try-the-api-for-free-with-the-experiment-plan) (search excerpt; opening it returned 404).
- [Hugging Face pricing](https://huggingface.co/docs/inference-providers/pricing).
- [Together help page](https://support.together.ai/articles/1862638756-changes-to-free-tier-and-billing-july-2025).
- [GitHub Models retirement notice](https://docs.github.com/en/github-models/use-github-models/prototyping-with-ai-models).
- [OpenCode Zen docs](https://opencode.ai/docs/zen/).

Cloudflare cost for this workload (neurons per 1M output = input rate x 0.889 + output rate; rates from the [official pricing page](https://developers.cloudflare.com/workers-ai/platform/pricing/)):

| Model | Neurons per 1M output | M output/day on 10,000 neurons | Days for 4.0M to 5.0M |
|---|---|---|---|
| granite-4.0-h-micro | 11,529 | 0.867 | 4.6 to 5.8 |
| llama-3.2-1b | 20,436 | 0.489 | 8.2 to 10.2 |
| qwen3-30b-a3b-fp8 | 34,586 | 0.289 | 13.8 to 17.3 |
| gemma-4-26b-a4b | 35,354 | 0.283 | 14.1 to 17.7 |
| glm-4.7-flash | 41,289 | 0.242 | 16.5 to 20.6 |
| gpt-oss-120b | 96,465 | 0.104 | 38.6 to 48.2 |
| llama-3.3-70b-fp8-fast | 228,510 | 0.044 | 91.4 to 114.3 |

### Inferences
- Request-capped providers (Google, OpenRouter, SambaNova) reward bigger chunks. Token-capped ones (Cloudflare, Groq) do not.
- Requests needed: 4K output per request gives 1,000 to 1,250 requests; 8K gives 500 to 625; 16K gives 250 to 312.
- Mistral should be treated as unavailable at $0 until the Admin Console shows otherwise. The dated official docs outweigh older trackers.

### Gaps
- Google's real per-account limits. They appear only in the signed-in [AI Studio rate-limit page](https://aistudio.google.com/docs/rate-limits). Check this first, because the whole "best" result depends on it.
- Groq's Free tab numbers did not come through in either the HTML or the `.md` version of the page.
- Training policy for SambaNova, Cloudflare, Cohere and Cerebras free use was not read.
- Maximum output tokens per request for Gemini Flash-Lite was not read.
- Whether SambaNova's per-model limits are independent or pooled is not stated.
- The [cheahjs free-llm-api-resources list](https://github.com/cheahjs/free-llm-api-resources) could not be opened (404).

## How long does the job take on the best single provider, and does the best combination reach 4M to 5M output tokens in 24 hours?

### Takeaway
Best single provider is Google AI Studio: about 4M output tokens per daily window at 4K output per request, or about 8M at 8K, if the third-party 500 RPD figure holds. The best one-account-each combination is about 5.4M per day at 4K chunks and about 9.9M at 8K, so yes, but only because of Gemini. Without Gemini the combination is about 0.9M to 1.5M per day, a 3 to 6 day job.

### Cited Findings
Inputs, all from the table above:
- Gemini Flash-Lite 3.5 and 3.1: 500 RPD each, 1,000 total; Flash 3.8 and 3.6: 20 RPD each — [Scriptbyai](https://www.scriptbyai.com/gemini-api-free-tier-limits/) (Third-party).
- SambaNova: 5 models x 200K TPD, 20 RPD each — [SambaNova](https://docs.sambanova.ai/docs/en/models/rate-limits).
- Cloudflare: 0.283M to 0.289M output/day on the better models — [Cloudflare](https://developers.cloudflare.com/workers-ai/platform/pricing/).
- Groq: at most 3 x 200K TPD, Developer-plan ceiling — [Groq](https://console.groq.com/docs/rate-limits).
- OpenRouter: 50 RPD — [OpenRouter](https://openrouter.ai/docs/api/reference/limits).

### Inferences

**Best single provider, Google AI Studio (one project):**

| Output per request | Requests per day | Output per day | Windows for 4.0M to 5.0M |
|---|---|---|---|
| 4K, both Flash-Lite models | 1,000 | 4.0M | 1 to 1.25, so 2 reset windows at the top end |
| 8K, both Flash-Lite models | 1,000 | 8.0M | 0.5 to 0.63, so 1 window |
| 4K, one Flash-Lite model | 500 | 2.0M | 2 to 2.5, so 3 windows |

- Pace check: 10 RPM x 2 models means 1,000 requests take at least 50 minutes. At 8K output, about 7.1K input x 10 RPM = 71K TPM, under the 250K limit.
- With 20% of calls lost to retries, 4K chunks give about 3.2M per day and 8K chunks about 6.4M per day.
- Windows reset at midnight Pacific, so elapsed time depends on start time. It is one account using its normal daily quota.

**Best combination, one account each, 24 hours:**

| Source | 4K output/request | 8K output/request |
|---|---|---|
| Gemini Flash-Lite x 2 (1,000 requests) | 4.00M | 8.00M |
| Gemini Flash 3.8 and 3.6 (40 requests) | 0.16M | 0.32M |
| SambaNova (100 requests; TPD cap gives 200K x 5 x 52.9% = 0.53M) | 0.40M | 0.53M |
| Cloudflare (Gemma 4 26B or Qwen3 30B) | 0.28M | 0.28M |
| Groq (ceiling only: 600K x 52.9%) | at most 0.32M | at most 0.32M |
| OpenRouter `:free` (50 requests) | 0.20M | 0.40M |
| **Total** | **about 5.36M** | **about 9.85M** |
| After 20% retry loss | about 4.29M | about 7.88M |

- Does it reach 4M to 5M in 24 hours? Yes at 8K chunks. At 4K chunks it clears 4M, and clears 5M only with few retries.
- Without Gemini: 0.88M/day at 4K (1.20M with Groq's ceiling) and 1.21M/day at 8K (1.53M with Groq's ceiling). That is 2.6 to 5.7 days for 4.0M to 5.0M.
- Next-best single official figure is SambaNova at 0.40M to 0.53M/day, so 7.5 to 12.5 days.
- Cohere is a separate one-off: 1,000 calls x 4K = 4.0M output per month, in about 50 minutes at 20 req/min, if per-call output allows it. It is not counted above because its per-call maximum and terms were not read.
- NVIDIA is left out. If about 40 RPM held, 1,125 requests would need about 28 minutes of quota, but the terms limit use to internal testing and evaluation (next section).
- Mixing models will produce uneven style. A single model family per doc set would be cleaner, which also favours Gemini alone.

### Gaps
- No live test of real throughput, 429 frequency or error rates on any provider was done.
- Rewrite quality of Flash-Lite versus the small Cloudflare models was not researched.

## Are OpenCode's free models usable, and does updating from 1.19.3 to v2 fix the error?

### Takeaway
Update anyway, because v1 is officially unsupported for free models, but do not plan the rewrite on OpenCode. Updating fixes it "for many people" by the project's own wording, yet the same error is still being reported on v2.2.6, no numeric cap is published, and the free models are only allowed inside OpenCode.

### Cited Findings
- The official Zen page lists GLM-5.3-Flash Free and DeepSeek V4.1 Flash Free as free "for a limited time" and gives a numeric cap only for LongCat 2.5 Free (100 requests/day). Both named models carry a zero-retention, no-training statement. "Free-tier chat models require OpenCode." — [OpenCode Zen docs](https://opencode.ai/docs/zen/)
- The pinned maintainer thread says "Most free tier reports come from OpenCode v1," that v1 "no longer supports free models and only gets fixes for critical bugs," and "Updating to v2 has fixed this for many people." It gives no numeric caps or windows. — [Issue #59387](https://github.com/anomalyco/opencode/issues/59387) (pinned 2026-10-26)
- The same thread shows reports continuing on v2.1.4 and on v2.2.6 (2026-11-07 to 11-09), across Desktop, TUI and Codespaces, and the issue does not resolve them. — [Issue #59387](https://github.com/anomalyco/opencode/issues/59387)
- A near-identical case: 1.19.4 CLI with the same "Free usage limit reached" error, and later commenters report it on v2.0.27 and v2.1.4. One 429 carried `retryAfterMs` 32217000, which is 8.95 hours. Direct API calls returned "FreeTierError: OpenCode's free tier can only be used from within OpenCode". Closed as not planned by the bot. — [Issue #58205](https://github.com/anomalyco/opencode/issues/58205)
- The project's bot says the limit is enforced by the Zen service per account and network. Error appeared about 5 minutes into a single prompt on the latest version. — [Issue #58963](https://github.com/anomalyco/opencode/issues/58963)
- One reporter showed zero free-model requests in Console logs for Oct 19 to 21 while blocked, and ruled out IP and API key; a VPN effect was reported by one user and contradicted by another. — [Issue #58284](https://github.com/anomalyco/opencode/issues/58284)
- Further reports of the same error: [#59252](https://github.com/anomalyco/opencode/issues/59252), [#59026](https://github.com/anomalyco/opencode/issues/59026), [#58814](https://github.com/anomalyco/opencode/issues/58814) (no reset for 2+ days).
- Releases: v2.2.6 on Nov 6 is the newest; v1.19.5 was released Oct 28. No release note mentions free usage limits, `FreeUsageLimitError`, or 429 retry behaviour. — [OpenCode releases](https://github.com/anomalyco/opencode/releases)

### Inferences
- 1.19.3 is on the unsupported line, so updating is the correct cheap test. It is a test, not a fix to count on.
- With no published cap, an unexplained block after one call and multi-day lockouts in reports, OpenCode free models cannot be scheduled for 8.5M tokens. Treat them as usable for occasional interactive use at most.
- The stuck `opencode run` retry loop recorded in the project notes is not addressed by any release note, so keep the process-tree kill and log check after updating.

### Gaps
- The real cap for DeepSeek V4.1 Flash Free and GLM-5.3 Flash Free is unknown. The "Free models, limits and privacy" page the maintainer points to could not be located (`docs.opencode.ai/docs/free-models/` returned 404).
- No root cause has been confirmed for v2 reports.
- `gh` was not installed, so issues were read through web pages rather than a full search.

## Do provider terms permit automated bulk use on free tiers?

### Takeaway
No provider read here explicitly bans scripted API use of a free tier, but several limit free use to evaluation or testing. NVIDIA is the clearest restriction. OpenRouter explicitly bans multiple accounts used to get around limits. Use one account per provider and stay inside each quota.

### Cited Findings
- **NVIDIA:** access is "for limited trial purposes only and without use of the API Service or Generated Content in production"; without a subscription, use is for "internal testing and evaluation purposes". — [NVIDIA API Trial Terms](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf) (Search excerpt)
- **Cerebras:** a pricing footnote reads "For development, evaluation, and experimentation; not intended for production use", though which tier it applies to was unclear. — [Cerebras pricing](https://www.cerebras.ai/pricing)
- **Mistral:** Free mode is "intended for evaluation and prototyping". — [Mistral help](https://help.mistral.ai/en/articles/698531-why-am-i-hitting-api-rate-limits-and-how-do-i-increase-them)
- **Cohere:** trial keys are described as "evaluation keys (free but limited in usage)". — [Cohere](https://docs.cohere.com/docs/rate-limits)
- **OpenRouter:** bans creating "multiple accounts as a single user, for purposes of bypassing or circumventing use limits", while batch and large-volume processing is described as a supported feature. — [OpenRouter terms](https://openrouter.ai/terms)
- **Google:** free-tier content may be used to improve products and read by human reviewers; "Do not submit sensitive, confidential, or personal information to the Unpaid Services"; only Paid Services may be used when making API clients available to users in the EEA, Switzerland or UK. No automation clause was found in the text read. — [Gemini API terms](https://aistudio.google.com/docs/terms)
- **Google quota scope:** limits are per project, not per key. — [AI Studio rate limits](https://aistudio.google.com/docs/rate-limits)
- **OpenCode:** free models are restricted to the OpenCode client, so calling them from another program is outside the allowance. — [OpenCode Zen docs](https://opencode.ai/docs/zen/)
- **Groq:** the public Terms of Use exclude GroqCloud, which is under a Services Agreement not read here. — [Groq terms](https://groq.com/terms-of-use)

### Inferences
- Public docs rewritten for a personal local course is low risk for Google's sensitive-data rule, and arguably not "production", but no provider's text settles that. NVIDIA's wording is the least compatible with mass-generating a finished course, so it is excluded from the plan.

### Gaps
- Not read: Cloudflare, SambaNova and Cohere terms, and the Groq Services Agreement.

## What is realistic on this PC with a local model?

### Takeaway
This laptop has a low-power CPU and only one memory module, so expect about 5 to 9 tokens per second on a 3B to 4B model. That means roughly 5 to 12 days of nonstop running for 4M to 5M output tokens, plus up to a day or so for reading the input. It works as a free fallback, not as a quick route.

### Cited Findings
- This PC, read directly on 2026-11-10 from Windows hardware info: Intel Core i5-1235U (10 cores, 12 threads), one 16 GB DDR4-3200 module in a single slot (Controller1-ChannelA-DIMM0), Intel UHD Graphics, Samsung 550XED.
- Dual-channel DDR4 i7 laptop, Q4 estimates: about 20 tok/s at 3B, about 8 at 7B, about 4 at 13B. A 16 GB laptop's practical limit is a 7B model at Q4. The page labels these estimates, not measurements. — [InsiderLLM CPU guide](https://insiderllm.com/guides/cpu-only-llms-what-actually-works/) (updated 2026-10-16)

### Inferences
- One DDR4-3200 channel gives 25.6 GB/s (3200 MT/s x 8 bytes), half of dual channel. Halving the estimates above gives about 10 tok/s at 3B and about 4 at 7B. The 15 W chip has only 2 performance cores, so real speed is likely somewhat lower.
- Working ranges and output-only time, 24 hours a day:

| Model size | Estimated tok/s | Output per day | Days for 4M to 5M |
|---|---|---|---|
| 1B to 2B | 10 to 15 | 0.86M to 1.30M | 3.1 to 5.8 |
| 3B to 4B (Qwen, Gemma class) | 5 to 9 | 0.43M to 0.78M | 5.1 to 11.6 |
| 7B to 8B | 2 to 4 | 0.17M to 0.35M | 11.6 to 28.9 |

- Reading 4M input tokens adds time. At an assumed 30 to 100 tok/s for prompt processing that is 11 to 37 hours. That speed is an assumption, not a measurement.
- A second matching memory module would be the one hardware change likely to help most. It costs money, so it is outside the $0 plan.
- Sustained 24-hour laptop runs will likely throttle. Running `llama-bench` for a few minutes would replace these estimates with real numbers.

### Gaps
- No benchmark was found for an i5-1235U or for single-channel DDR4 with Qwen or Gemma. Search summaries showed figures such as about 15 tok/s for a 4B Qwen on a desktop i5-12400 and about 9 tok/s from another run, but the source pages could not be opened or tied to hardware, so they are not used.
- Thermal throttling data for this laptop was not found.
