# Automatic checks that a plain-English rewrite of technical docs kept every fact, name, number and code identifier

Notes on evidence quality: "(excerpt only)" means the claim was seen in a search-result excerpt and the full page was not read. Everything else was read on the source page. Most of the research is on medical, scientific or news text. I found no study of faithfulness checking on software documentation, so transfer to LangChain docs is an inference throughout.

## What is the practical, ranked checking recipe for a $0 script on a CPU-only 15.7 GB Windows PC?

### Takeaway
Rank checks by how sound they are, not how clever they are. Deterministic parsing and set comparison come first and can fail a chunk outright. Local NLI (entailment checking) is a weak flag only. A second free model is used last, in two separate structured passes, and even then it will miss most omissions, so the first-tier checks and a fact-coverage pass have to carry that load.

### Cited Findings
- Sound external verifiers improve LLM output, while LLM self-critique causes "significant performance collapse"; re-prompting with a sound verifier keeps most of the benefit. Tested on GPT-4 for Game of 24, graph colouring and STRIPS planning, not on rewriting — [Stechly et al. 2024](https://arxiv.org/abs/2402.08115)
- LLM judges catch added or altered content far better than omissions: paired discrimination 0.79-0.94 against 0.50-0.63, where 0.5 is chance. Domain is clinical notes — [Fox et al. 2026](https://arxiv.org/abs/2608.31016)
- Listing the source facts first and then asking a closed present-or-absent question per fact is what recovered omission detection (24.6% detection at 2.7% false alarms; 36.9% at 6.2% for an optimised single call) — [Fox et al. 2026](https://arxiv.org/html/2608.31016v1)
- On LLM-AggreFact, average balanced accuracy was GPT-4 75.3, MiniCheck-FT5 (770M parameters) 74.7, AlignScore 70.4, T5-NLI-Mixed 61.0 — [Tang et al. 2024](https://arxiv.org/html/2404.10774v2)
- Claim decomposition into atomic facts did not help MiniCheck-FT5 (73.3 against 74.7) and neither did decontextualisation (74.1) — [Tang et al. 2024](https://arxiv.org/html/2404.10774v2)
- Model choice decides reviewer value. On sentence-level faithfulness, balanced accuracy was Phi-2 48.1%, Llama2-70B 56.5%, Mixtral-8x7B base 50.7%, Mixtral-8x7B-Instruct 78.7%, Gemma2-27B-Instruct 90.8%, Llama3-70B-Instruct 92.0%, GPT-4-turbo 86.4%, GPT-4o 91.8% — [Song et al. 2024, FineSurE](https://arxiv.org/html/2407.00908v3)

### Inferences
Ranked recipe. Items 1-6 need no model. Items 1-5 are hard fails; item 6 is a flag.

**Before the model sees anything**
- Parse with a real Markdown/MDX parser and split at block level. Never send fenced code, front matter, imports or JSX to the model.

**Tier 1: no model, sound, run on every chunk**
1. Structure equality: same sequence of block types, same heading depth, same list nesting, same table shape. Code blocks byte-identical.
2. Placeholder integrity: every protected token appears exactly as many times as in the source, with none invented. Check as a multiset (a count of each token), because a plain rewrite may legitimately reorder a sentence.
3. Identifier set equality: inline code, CamelCase, snake_case, dotted paths, `--flags`, file paths and ENV_VARS. Any item in the source and missing in the rewrite is a fail, and so is any new one.
4. Number multiset with normalisation: digits, versions, percentages, units, and number words mapped to digits ("two" = 2). Unlike summarisation, where a dropped number can be fine, a full rewrite should keep them all.
5. URL and link-target equality, plus internal anchors re-checked after any heading change.
6. Meaning-word comparison per aligned sentence, grouped into classes so harmless synonyms pass:
   - Negation: not, n't, no, never, none, without, cannot.
   - Obligation: must, shall, required, have to, need to / should, recommended / may, optional, can, might.
   - Conditions and limits: if, unless, only, until, except, when, before, after, at least, at most, all, every, some, default.
   - A class count that changes is a flag, not a fail, because good plain English does restructure these. Treat "must" becoming "should" or "may" as high severity, since these are distinct requirement levels ([RFC 2119](https://www.rfc-editor.org/rfc/rfc2119)) and rewriting drifts toward stated certainty ([Belem et al. 2026](https://arxiv.org/abs/2606.07951)).

**Tier 2: local model, weak signal, flag only**
7. Sentence alignment and content-word coverage: for each source sentence, find its best match in the rewrite and compute how many content-word lemmas survive. Unmatched source sentences are omission suspects. This is my design; I found no published evaluation of it for this task.
8. NLI cross-encoder in both directions: rewrite against source finds additions, source against rewrite finds omissions. `cross-encoder/nli-deberta-v3-small` is about 0.1B parameters. Expect noise and calibrate thresholds on seeded errors.
9. Optional upgrade: MiniCheck-FT5 per rewrite sentence against its local source chunk. It beat the NLI baseline clearly on the benchmark above.

**Tier 3: second free model, a different model from the writer, fresh context, JSON output**
10. Coverage pass: list every fact in the source chunk, then answer present or absent for each one against the rewrite.
11. Faithfulness pass: judge each rewrite sentence alone, with an error category and a one-line reason.

**Leave out**: QAFactEval, QuestEval and full FActScore (see the NLI/QA section). Use readability scores only as a trend measure on masked prose.

**Prove the recipe works on your docs.** Build a seeded-error set by taking correct rewrites and mutating them: delete a sentence, change must to may, drop a "not", change a number, rename an identifier, drop an "unless" clause, add an outside fact. Report the catch rate per check. This is the only way to get real numbers, because none are published for this domain.

### Gaps
- No published head-to-head of these tiers on technical documentation.
- No published catch rates for identifier or modal-word comparison in rewrites.

## Which deterministic checks work best?

### Takeaway
These checks have little formal evaluation, but they are the only ones that are sound by construction for names, numbers and code. Placeholders protect the text; set comparison proves it survived. Modal and negation comparison needs a flag-not-fail policy because of legitimate rewording.

### Cited Findings
- Quantity hallucination is an established failure in abstractive summarisation; HERMAN checks dates, numbers and amounts against the source using spaCy NER and re-ranks candidates, but is a learned verifier and its precision gains are on ROUGE, not on entity-level accuracy (2020, older foundational) — [Zhao et al. 2020](https://arxiv.org/pdf/2009.13312) (excerpt only)
- A practitioner team on financial news extracted entities with spaCy and computed numbers-in-summary minus numbers-in-source; a rule flagging any non-verbatim number caught a high fraction of numeric errors, but no precision or recall is given — [YLD blog](https://www.yld.com/blog/evaluating-llm-summaries-at-scale-what-we-tried-and-what-worked) (excerpt only)
- A production Markdown translation pipeline uses `@@CODE_BLOCK_X@@` placeholders and found that regex detection of fences broke placeholder sync, fixed by parser-based detection and treating code blocks as atomic units — [Microsoft Co-op Translator write-up, 2026](https://techcommunity.microsoft.com/blog/azuredevcommunityblog/fixing-broken-markdown-in-ai-translation-hardening-a-production-pipeline/4511378)
- Language models raise or lower expressed certainty in up to 75% of outputs during meaning-preserving rewriting, and most are about 1.5 to 2 times as likely to raise it as to lower it. Prompt interventions reduce but do not remove this — [Belem et al. 2026, accepted EMNLP 2026](https://arxiv.org/abs/2606.07951)
- In the medical domain, claude-haiku-4.5 increased certainty in 20% of examples after one paraphrase and 40% after five, so the effect compounds with repeated rewriting — [Belem et al. 2026](https://arxiv.org/abs/2606.07951)
- RFC 2119 gives distinct definitions: MUST/SHALL are absolute, SHOULD/RECOMMENDED allow justified exceptions, MAY/OPTIONAL are truly optional — [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119)
- LLM summaries were reported as nearly five times more likely than human ones to state generalised conclusions, and newer chatbot versions did this more. I could only read press coverage; the journal page refused the fetch — [Live Science on Peters and Chin-Yee](https://www.livescience.com/technology/artificial-intelligence/ai-chatbots-oversimplify-scientific-studies-and-gloss-over-critical-details-the-newest-models-are-especially-guilty)

### Inferences
- Masked placeholders hide what an identifier means, and a rewrite often needs to explain it. A workable compromise is a short token in the text plus a per-chunk legend ("C1 = `ChatOpenAI`, copy exactly"). This keeps restoration deterministic and leaves the meaning visible. It is untested.
- Identifier set comparison also catches a failure placeholders cannot: a model describing a class in words and dropping the token, or inventing a similar name from memory.
- A number that appears in both source and rewrite can still be attached to the wrong thing, so number comparison proves presence and not correct binding. Tier 3 has to catch binding errors.
- Do not let the rewrite model re-paraphrase its own output. Compounding drift suggests every retry should start from the source text.

### Gaps
- I found no measured precision or recall for negation, modal or condition-word comparison on rewrites. The Belem abstract does not say whether modal verbs were analysed.

## What does research show about LLM simplification errors?

### Takeaway
Roughly one in six to one in three LLM simplifications has an annotated error in the largest sentence-level study. Information loss and unsupported additions are the main faithfulness problems, oversimplification is more common than outright deletion, and even humans disagree strongly on what counts as lost information.

### Cited Findings
- Wu and Arase annotated 4,500 outputs. Error occurrences across 1,200 outputs each (Turk, ASSET, Newsela, SimPA): GPT-4 285, Qwen2.5-72B 202, Llama-3.2-3B 405. That is about 24, 17 and 34 errors per 100 outputs (my arithmetic). Most erroneous outputs have one error type (1.04-1.14 average) — [Wu and Arase, arXiv 2403.04963 v4](https://ar5iv.labs.arxiv.org/html/2403.04963)
- GPT-4's named counts in the text are Lack of Simplicity-Lexical 144 and Altered Meaning-Lexical 94; lexical categories outnumber structural ones across models. On Newsela, meaning-preservation Likert averages were references 1.67, GPT-4 2.66, Qwen 2.62, Llama-3.2-3B 1.78, Control-T5 1.16, and the authors say references trade meaning for simplicity — [Wu and Arase](https://ar5iv.labs.arxiv.org/html/2403.04963)
- Added facts not inferable from the source appeared (GPT-4 4, Qwen 12, Llama-3.2-3B 5, Control-T5 12) but were checked online, found true, and not counted as errors — [Wu and Arase](https://ar5iv.labs.arxiv.org/html/2403.04963)
- CLEF 2024 SimpleText LLM runs on scientific abstracts: 69.16% of 2,659 annotations marked some error. Categories overlap and do not sum: loss of informative content 19.56%, out-of-scope generation 15.72%, faithfulness hallucination 13.54%, overgeneralisation 11.51%, contradiction 0.86%, factuality hallucination 0.86% — [Vendeville et al., SIGIR 2025](https://ar5iv.labs.arxiv.org/html/2505.16392)
- Agreement in that study was low: Fleiss kappa 0.02 for Information errors, 0.26 for Simplification. The best automatic any-error AUROC named was FactCC at 0.68 — [Vendeville et al.](https://ar5iv.labs.arxiv.org/html/2505.16392)
- In 104 GPT-4 (gpt-4-0613) simplifications of medical trial abstracts, linguists wrote 1,000 information-loss QA pairs, about 9.6 per document. Oversimplification was 74.1% and outright deletion 25.9% — [Trienes et al., ACL 2024, InfoLossQA](https://arxiv.org/html/2401.16475v2)
- Reading-comprehension testing on OneStopEnglish news: most systems left 14-17% of questions unanswerable, human-written texts 12-14%, the worst system (KIS) about 64% — [Agrawal and Carpuat, TACL 2024](https://arxiv.org/html/2312.10126v1)
- Foundational: simplification models insert unsupported statements or omit key information, and standard metrics miss this — [Devaraj et al., ACL 2022](https://arxiv.org/pdf/2204.07562v1.pdf) (excerpt only)

### Inferences
- A search summary described fabrication as "rare" in Vendeville et al. That is only true of claims wrong about the world (0.86%). Content unsupported by the source is 13.54%, and that is the category a rewrite check cares about.
- Wu and Arase did not count true outside facts as errors. For documentation they are errors, because a rewrite must not add behaviour the source does not state. Their rate understates this risk for this use.
- Since 74% of loss is oversimplification, a check for whether a sentence survived is not enough. A sentence can survive while losing its qualifier, which is why condition-word comparison matters.
- Treat the 69% as an upper-end figure: it counts fluency and format problems and individual annotators, so it is not comparable with Wu and Arase.

### Gaps
- No error rates specific to technical or software documentation were found.
- Results for current frontier models are thin; the newest models in these studies are GPT-4, Qwen2.5-72B and Llama-3.2-3B.

## How good are NLI, QA-based and claim-decomposition methods, and can any run locally?

### Takeaway
NLI and QA metrics worked reasonably on summarisation and poorly on simplification. Off-the-shelf NLI runs easily on this PC but is only a weak flag. MiniCheck-FT5 is the strongest small local option found. QAFactEval, QuestEval and FActScore are poor fits.

### Cited Findings
- TRUE (NAACL 2022, foundational): across 11 datasets, large-scale NLI and question-generation-and-answering approaches were strongest and complementary — [Honovich et al. 2022](https://arxiv.org/abs/2204.04991)
- SummaC-Conv reached 74.4% balanced accuracy on its benchmark, about 5 points above prior work; out-of-the-box NLI models were cited at 52% accuracy on the binary task (foundational) — [Laban et al.](https://arxiv.org/pdf/2111.09525) (excerpt only)
- In document simplification, the system with the highest SummaC precision out of domain (LEDpara, 0.76) was ranked last by human faithfulness ratings (0.632), and the authors call for caution with these summarisation metrics — [Cripwell et al. 2024](https://arxiv.org/html/2404.03278)
- QAFactEval correlated weakly with human reading-comprehension results for simplification, at best 0.395 Spearman. On summarisation (FRANK) it reached 0.841 Pearson at summary level, so performance does not transfer — [Agrawal and Carpuat](https://arxiv.org/html/2312.10126v1); [FineSurE](https://arxiv.org/html/2407.00908v3)
- An NLI pipeline for information loss labelled all its output as deletions and produced no oversimplification findings; GPT-4 was better at identifying unanswerable questions, and the paper concludes models struggle to reliably identify loss — [Trienes et al.](https://arxiv.org/html/2401.16475v2)
- NLI models over-rely on strong negation words and fail number and quantifier reasoning (older foundational) — [Naik et al. 2018](https://arxiv.org/pdf/1806.00692) (excerpt only). Language models also remain insensitive to negation — [Truong et al. 2023](https://arxiv.org/pdf/2306.08189) (excerpt only)
- Most NLI datasets use one or few sentences as premise, limiting success on factual consistency tasks — [arXiv 2009.09099](https://arxiv.org/pdf/2009.09099v1) (excerpt only)
- `cross-encoder/nli-deberta-v3-small`: Apache-2.0, about 0.1B parameters, SNLI 91.65, MNLI mismatched 87.55, labels in order contradiction, entailment, neutral, loaded with `CrossEncoder` not `SentenceTransformer` — [model card](https://huggingface.co/cross-encoder/nli-deberta-v3-small)
- MiniCheck-FT5 has 770M parameters; a 7B variant is on Ollama as `bespoke-minicheck:7b`, about 4.7 GB on disk at Q4_K_M, taking a document and claim and answering Yes or No — [Tang et al.](https://arxiv.org/abs/2404.10774); [Ollama registry](https://registry.ollama.ai/library/bespoke-minicheck:7b) (excerpt only)
- LettuceDetect (ModernBERT, token classification, up to 8k tokens) reports 79.22% example-level F1 on RAGTruth and 30-60 examples per second on one GPU — [Kovács et al. 2025](https://arxiv.org/html/2502.17125v1) (excerpt only)
- QAFactEval: BSD-3, only update listed is its 2022 initial commit, needs several downloaded models through a script, and CPU behaviour is undocumented — [repo](https://github.com/Salesforce/QAFactEval)
- QuestEval: MIT, Python 3.9 conda setup, has a `no_cuda=True` option, generates and answers many questions so can be slow, and its summarisation Weighter is out of date — [repo](https://github.com/ThomasScialom/QuestEval)
- FActScore splits text into atomic facts and checks them against Wikipedia; the abstract reports under 2% error for its automated estimate — [Min et al. 2023](https://arxiv.org/pdf/2305.14251.pdf) (excerpt only). Results are sensitive to the decomposition method — [Wanner et al. 2024](https://arxiv.org/html/2403.11903v1) (excerpt only). OpenFActScore is an open re-implementation reporting over 0.99 correlation — [overview](https://www.alphaxiv.org/overview/2507.05965) (excerpt only)

### Inferences
- FActScore measures precision, which only finds additions, and needs a knowledge source. Against a source chunk its machinery reduces to claim splitting plus a verifier, and the MiniCheck result suggests the splitting step is not worth its cost and noise.
- CPU fit: the 0.1B NLI model and the 770M FT5 model should fit comfortably in 15.7 GB. The 7B quantised MiniCheck should fit but will be slow. These are my estimates; no CPU benchmark was found.
- NLI should not be used to judge identifiers or numbers, given its documented number weakness, and Tier 1 already covers those.
- A natural pattern for the NLI pass is a best-match per sentence, using a local window of source rather than the whole page.

### Gaps
- No CPU speed figures for any of these models. Time them on the actual machine.
- The MiniCheck weights' licence was not confirmed; check the repository before relying on it.
- I found no direct three-way benchmark of FActScore, QAFactEval and QuestEval.

## Is a second-model reviewer reliable, and what structure reduces missed errors?

### Takeaway
It is good at catching additions and changes and poor at catching omissions. Structure helps a lot, but best-case omission detection in the strongest study was still only 25% to 37% of cases. Use it as one layer, with a strong instruction-tuned model and closed per-fact questions.

### Cited Findings
- Paired discrimination in the 495-pair set, additions-or-changes against omissions: faithfulness yes/no single call 0.875 against 0.500; best design (faithfulness plus completeness, 0-10 score, eight samples) 0.939 against 0.634; G-Eval 0.890 against 0.568; a checklist judge 0.744 against 0.647 — [Fox et al. 2026](https://arxiv.org/html/2608.31016v1)
- On single notes, no ablation design reliably flagged omissions: best was 8.3% detection at 6.5% false alarms — [Fox et al.](https://arxiv.org/html/2608.31016v1)
- Rewording, voting and prompt optimisation moved the operating point without producing usable detection. The fact list gave about a third of the recovery and closed per-fact verdicts the rest — [Fox et al.](https://arxiv.org/html/2608.31016v1)
- Omissions were detected at 0.690 when fully removed and 0.526 when a restatement survived elsewhere; the authors name restatement as unsolved. All judges were one pinned GPT-family model, with a Gemini re-run on two designs; the setting is clinical and no human baseline was run — [Fox et al.](https://arxiv.org/html/2608.31016v1)
- FineSurE uses two JSON-output prompts: sentence-by-sentence fact checking across seven error types plus "other" and "no error" with a short reason, and key-fact alignment giving Yes/No plus supporting sentence IDs. On completeness it reached 0.688 Pearson against G-Eval 0.314 — [Song et al. 2024](https://arxiv.org/html/2407.00908v3)
- Categorisation and reasoning helped the faithfulness prompt but did not improve the key-fact prompt, which is instruction-only — [Song et al.](https://arxiv.org/html/2407.00908v3)
- SummEdits (2023): most LLMs scored near chance at spotting factual inconsistencies in edited summaries, and GPT-4 was about 8% below estimated human performance — [Laban et al., EMNLP 2023](https://preview.aclanthology.org/setup/2023.emnlp-main.600) (excerpt only)
- Chain-of-Verification plans verification questions and answers them independently of the draft; factored or two-step variants were reported to beat joint verification — [Dhuliawala et al. 2023](https://mlanthology.org/iclrw/2024/dhuliawala2024iclrw-chainofverification) (excerpt only); [review](https://liner.com/review/chainofverification-reduces-hallucination-in-large-language-models) (excerpt only)

### Inferences
- Run coverage and faithfulness as two separate calls with different questions. A single "is this faithful?" prompt is the design with the worst omission result.
- Give the reviewer one source chunk and its rewrite at a time, with facts numbered, and require a quoted location for each "present". An answer with no quote gets treated as absent. The quote requirement is my addition, modelled on FineSurE's supporting sentence IDs, and is not separately evaluated.
- Use a different model from the writer so the two don't share the same blind spots. This is reasoning from general principle; I found no study measuring it for rewriting.
- Avoid small or base models as reviewers. Phi-2 and base Mixtral scored at chance in FineSurE. Check the free model on seeded errors before trusting it.
- Because a restated fact defeats omission checks, documentation that repeats itself will hide losses. Check coverage per chunk, not per page.

### Gaps
- Fox et al. is one clinical study of a GPT-family judge; I found no replication for technical documentation or free-tier models.
- No evidence on how verdicts differ with free-tier model rate limits or truncation.

## What is the proven way to preserve Markdown structure and code blocks through an LLM rewrite?

### Takeaway
Parse, send only prose, restore, then validate. This rests on engineering write-ups, not peer-reviewed comparison, so "proven" here means repeatedly reported in production.

### Cited Findings
- Failure modes in Co-op Translator v0.18.1: regex fence detection broke placeholder sync; line-by-line chunking separated list items from their indented code placeholders; per-chunk heading translation broke internal anchors — [Microsoft write-up, April 2026](https://techcommunity.microsoft.com/blog/azuredevcommunityblog/fixing-broken-markdown-in-ai-translation-hardening-a-production-pipeline/4511378)
- Fixes there: markdown-it-py parser for fences, code blocks kept atomic in chunking and restoration, a grouping step keeping nested lists with their placeholders, and a post-merge step that re-slugs headings and realigns links — [same](https://techcommunity.microsoft.com/blog/azuredevcommunityblog/fixing-broken-markdown-in-ai-translation-hardening-a-production-pipeline/4511378)
- `remark-mdx` extends remark to parse MDX, with node types `mdxjsEsm`, `mdxJsxFlowElement`, `mdxJsxTextElement`, `mdxFlowExpression` and `mdxTextExpression`; output style is controlled by options such as `quote` and `tightSelfClosing` — [MDX docs](https://mdxjs.com/packages/remark-mdx/)
- Pandoc warns "one should not expect perfect conversions between every format and every other", and that it preserves structure but not formatting details — [Pandoc manual](https://pandoc.org/MANUAL.html)

### Inferences
- Do not round-trip the whole file through a serialiser. Use the parser's position offsets to replace only prose spans in the original text, so everything else stays byte-identical and a diff shows only intended changes.
- Pandoc is a poor choice for this because of the lossiness above, and because MDX components are not part of its model.
- A rewrite differs from translation in one way: it may legitimately reorder a sentence, so compare placeholders as a multiset per block. Order should be checked only for structural placeholders.
- Heading text is the riskiest prose to rewrite because it creates anchors. Keeping headings unchanged, or checking every anchor link afterward, removes the problem.

### Gaps
- No peer-reviewed comparison of placeholder styles was found. Claims that emphasis markers are unreliable and that invisible or XML-style placeholders work better appeared only in tool documentation excerpts, and I could not confirm them.

## What are objective plain-language measures, and how misleading are they on technical text?

### Takeaway
Flesch-Kincaid, Dale-Chall and CEFR word lists are objective but measure the surface. On identifier-heavy text the scores are dominated by code tokens unless you mask them first, so use them only to compare masked before-and-after prose, never as a pass or fail target.

### Cited Findings
- Flesch-Kincaid Grade = 0.39 × (words/sentences) + 11.8 × (syllables/words) − 15.59. The formulas neglect "between-reader differences and effects of content, layout and retrieval aids" — [Wikipedia](https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests)
- Dale-Chall uses a 3,000-word familiar list (1995 revision); any word not on the list counts as difficult — [Wikipedia](https://en.wikipedia.org/wiki/Dale%E2%80%93Chall_readability_formula)
- textstat (MIT) offers `flesch_kincaid_grade`, `flesch_reading_ease`, `dale_chall_readability_score`, `smog_index` and others. SMOG needs at least 3 sentences and is described as statistically invalid under 30 — [textstat](https://github.com/textstat/textstat)
- cefrpy gives CEFR levels by word and part of speech, and with spaCy can exclude named entities from analysis — [cefrpy](https://pypi.org/project/cefrpy/) (excerpt only)
- Mapping Flesch-Kincaid to CEFR levels is an approximate mapping — [RANLP 2025 entry](https://aclanthology.org/anthology-files/pdf/ranlp/2025.ranlp-1.18.pdf) (excerpt only)
- For simplification, simplicity and meaning preservation should be assessed separately, per the title and approach of — [Cripwell et al. 2024](https://arxiv.org/html/2404.03278)

### Inferences
- Local test for these notes (textstat 0.7.13, five invented LangChain-style sentences with 12 inline identifiers). Raw text scored Flesch-Kincaid grade 8.05 and Dale-Chall 10.05, and was counted as 7 sentences. With identifiers replaced by a plain word it scored grade 0.71 and Dale-Chall 5.87, and 5 sentences. So identifiers moved the grade by about 7 and the dots inside names created false sentence breaks. Tiny sample, and the replacement word is unrealistically short, so treat the size as illustrative and the direction as the finding.
- Two errors pull in opposite directions: long identifiers push scores up, and false sentence splits push them down. A raw score can therefore look plausible while being meaningless.
- Practical use: mask code, strip Markdown, score source and rewrite the same way, and report the change. Exclude identifiers from CEFR lookups and add a project allowlist of terms the course teaches.
- A rewrite can score better simply by dropping content, so the readability gain should only count once faithfulness checks pass.

### Gaps
- I found no study measuring these formulas on identifier-heavy documentation specifically.
- Licensing of CEFR word lists (Oxford 3000/5000, English Vocabulary Profile) and of cefrpy's underlying data was not confirmed.

## How should a pipeline handle sentences that fail?

### Takeaway
Retry only when a sound check gives a specific reason, cap retries at two, restart from the source each time, then fall back to the original text with a visible flag. No research directly compares these policies for rewrites, so this is reasoned from adjacent evidence.

### Cited Findings
- Self-critique collapses performance, while a sound verifier gives significant gains, and plain re-prompting with a sound verifier keeps most of that gain — [Stechly et al. 2024](https://arxiv.org/abs/2402.08115)
- A verify-then-correct loop relies on external tool feedback; its effectiveness drops significantly without tools — [CRITIC review](https://liner.com/review/critic-large-language-models-can-selfcorrect-with-toolinteractive-critiquing) (excerpt only, secondary)
- A 2026 feedback-control paper argues self-correction should be a gated decision, and reports a near-zero error-introduction boundary separating helpful from harmful correction — [summary of arXiv 2604.22273](https://www.opentrain.ai/papers/self-correction-as-feedback-control-error-dynamics-stability-thresholds-and-prom--arxiv-2604.22273/) (excerpt only, secondary)
- Certainty drift compounds across repeated paraphrasing (20% to 40% over five iterations in one model and domain) — [Belem et al. 2026](https://arxiv.org/abs/2606.07951)
- Model reviewers have a material false-alarm rate on correct text (2.7% to 6.2% in the recovered omission methods) — [Fox et al. 2026](https://arxiv.org/html/2608.31016v1)

### Inferences
Suggested policy:

| Failure | Action |
|---|---|
| Tier 1 hard fail (structure, placeholder, identifier, number, URL) | Retry from source with the exact defect named ("`max_retries` is missing"). Two tries at most. |
| Still failing after retries | Keep the original sentence unchanged and flag it. Never publish an unverified rewrite. |
| Meaning-word flag (negation, obligation, condition) | One retry naming the word class, then keep original and flag. |
| NLI or reviewer flag only, Tier 1 clean | No automatic retry. Queue for human review, showing source and rewrite side by side with the reviewer's reason. |
| Coverage pass reports a missing fact | Retry once with that fact named; if still missing, append the original sentence or flag. |

- Keep a per-chunk record of the source hash, rewrite, every check result, retries and final status, so a re-run skips verified chunks and a human can audit decisions.
- Falling back to the original gives a less readable sentence but a correct one. In technical docs that is the right trade, and the flag rate itself is a useful quality signal for the writing model.
- For a reader-facing course, show the fallback plainly rather than hiding it, for example with a small "original wording kept" note, so readers know that passage was not simplified.

### Gaps
- No study compares retry, fallback and flag policies for rewriting. A search excerpt reported graph-colouring accuracy of 16% falling to 2% with self-verification and rising to 38% with a sound verifier, and another reported that naive "are you sure?" re-prompting lowers truthfulness, but I could not tie either figure to a specific paper, so neither is relied on here.
