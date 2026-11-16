# Final verified paper plan

15 November 2026. This file is the result of checking the plan in `Top venue niche and roadmap.md` against the primary papers and the official ICML pages. It says what held, what was corrected, and what the final plan is. The full design, cost arithmetic and source links stay in that report.

**No research can make acceptance certain.** The checks show the paper is in scope for ICML 2027 and that the gap is open among the papers read in full. They say nothing about the probability of acceptance.

## 1. What the verification found

25 claims were checked by three independent verifiers each; all 25 were confirmed, none refuted. The check covered six prior papers in full text and the official ICML and NeurIPS pages.

| Claim in the plan | Result |
|---|---|
| No prior paper tests whether stored scores still rank items correctly under a new model | Holds for the six papers read in full: MemRL, RoMeRL, CHIME, Goyal and Ray, MemCollab, Memory Transfer Learning |
| No prior paper compares keep, wipe and discount | Holds for the same six |
| Prior work "reported only that it helps against no memory" | **Wrong, corrected.** CHIME, Goyal and Ray, MemCollab and Memory Transfer Learning also include an own-memory arm. The correct statement: prior work reports only end-task accuracy; where an own-memory arm exists it compares whole memories, not the scores |
| ICML 2027: abstract 14 January, paper 22 January 2027 | Confirmed on two official pages. The author list is fixed at the abstract deadline |
| "Datasets, Evaluations and Benchmarks" fits a no-training audit | Confirmed. It covers "auditing or stress testing" and needs no new algorithm. It is a reviewing lens, not a separate track, and does not lower the bar |
| After a first-stage ICML rejection there are reviews to answer | **Wrong, corrected.** ICML promises only a short justification. An area chair decides before any reviewer reads the paper |
| A sole author with no prior paper at a listed venue may submit one paper | Confirmed. There is no room for a second sole-author ICML submission |
| LifelongAgentBench database tasks as the released-code leg | **Changed.** They are near ceiling (base 93.0 to 96.2), so a score effect cannot show. Use the operating-system tasks |

**Still not verified, and the largest remaining risk:** EvoKernel, Xia et al., arXiv 2611.03930, and the three ICLR 2027 submissions (HEIRS, "When Can a Skill Library Trust Its Execution Records?", "Beyond Semantic Relevance"). OpenReview blocks automated reading. Read these in a normal browser in week 1. If one of them already has the keep, wipe and discount comparison for numeric scores, the paper's claim must narrow.

The verification pass also did not confirm benchmark usability, memory-gain sizes on StreamBench, API prices or acceptance rates. Those figures come from the earlier research notes and are measured by the pilot.

## 2. The question and the "why"

**Question.** When the language model under an agent is replaced, do the usefulness scores stored on its memory items still rank those items correctly under the new model, and which rule should be applied on the day of the swap: keep, wipe, fixed discount, or a discount set from a few fresh checks?

**Why, in the order the introduction should give it:**

1. **A published claim that was never tested.** MemRL (NeurIPS 2026) handed one scored memory bank to three other models, saw task success rise, and wrote that this suggests "the learned utility over memories generalizes beyond any single model's inherent strength". Its only check that scores track usefulness is on a single model, its theory assumes a frozen model, and its own appendix attributes the gain to memorised answers. Quote the sentence exactly and cite version 2.
2. **A concrete failing case already in print.** In CHIME's transfer table, moving memory from Qwen to DeepSeek adds 0.78 points where the target's own memory adds 6.24. The paper does not discuss the cell. This is the one-line motivating example a reviewer can check.
3. **The swap is forced on everyone.** Vendors retire models on short notice; the retirement dates in the report come from the vendors' own pages (read in the first research round, not re-checked in this pass).
4. **The effect depends on direction.** Goyal and Ray found free-text memory moved +9.91 points one way and −13.28 the other, cancelling to near zero when pooled. So an average hides the answer, and a per-pair study is needed.

One accepted agent-memory evaluation paper (MemoryAgentBench, ICLR 2026) nearly failed on motivation: the lowest reviewer called the task "boutique" and asked for "a simple clear motivating example". Points 1 and 2 are that example. This is one review thread, not a rule.

## 3. How to produce the results

The design in the report stands, with these changes from the verification:

- **Report every result per ordered swap pair.** Never rely on a pooled average.
- **Keep two arms that prior work lacks:** the source's memory content with scores removed (the wipe arm), and the target's own freshly earned scores as the upper bound. Together they separate "the content transfers" from "the scores transfer", which MemRL, RoMeRL and CHIME cannot do.
- **Expect small effects.** Prior cross-model margins are 0.3 to 5 points. The keep-against-wipe effect will be smaller than the total memory gain, so the primary measure must be item-level (retained validity from the probe table), not task success.
- **Use the operating-system tasks** for the released-code leg, or a weaker target model that restores headroom.
- **Include a no-memory arm and a cost table.** Reviewers asked for both in the one review thread that could be read.

## 4. How strong the results must be

These bars are a judgement built from the plan's own registered margins and the effect sizes in prior work. No venue publishes such a bar.

| | Minimum (enough for the journal TMLR) | Target (competitive at ICML) |
|---|---|---|
| Coverage | Two public benchmarks, six models from three makers, twelve ordered pairs, all seven arms | The same, plus the released-code leg and both score types |
| Scores mean something at home | Concordance of at least 0.60 for one score type | For both score types |
| The swap effect | Measured per pair with intervals and the self-swap noise floor, whatever its size | A drop beyond the noise floor in a clear subset of pairs, or a tight "no drop" shown by the equivalence test (within 3 points) |
| Explanation | The three predictions reported, pass or fail | At least one prediction holds across the twelve pairs, so the paper can say which swaps break and why |
| The rule | Keep, wipe and discount compared | The calibrated discount recovers most of the ceiling from a stated small number of fresh checks |
| Evidence quality | Pre-registered file, paired tests, bootstrap intervals, cost table, full release | The same |

A small drop with no explanation, or a plain "nothing changes" without the equivalence test, should go to TMLR, not ICML.

## 5. How to present it

This blueprint is a judgement from the ICML type definition, the one readable review thread and the related-work findings.

- **Title:** say "scores", not "memory" (the nearest preprint is titled "Does Your Agent's Memory Survive a Model Upgrade?"), and never "human".
- **Abstract:** one sentence on the forced swap; the untested claim; what was measured (models, pairs, benchmarks); the headline number per pair; the rule; the release.
- **First page:** the CHIME cell and the MemRL sentence, then the limits stated plainly (program-graded and model-assigned scores, one item shown at a time, single-call tasks).
- **Figure 1:** a source-by-target grid of retained validity for all ordered pairs, with the self-swap diagonal as the noise floor.
- **Main table:** one row per ordered pair, one column per arm, with intervals.
- **Related work:** a point-by-point table of what each close paper measured and left out. Do not claim as new: moving scored memory across models, comparing own with transferred memory, or the discount rule itself (it is a power prior).
- **Because an area chair screens the paper before reviewers see it,** the abstract, introduction and Figure 1 get their own week. That these decide the screen is an inference; ICML has not published the criterion.
- **Release:** code, prompts, raw answers and probe tables, anonymised and hosted at submission, plus the ICML AI disclosure statement.

## 6. Final roadmap

| Dates | Work | Result at the end |
|---|---|---|
| 15–22 Nov | Dated prediction file. OpenReview profile. Clearance request and co-author question to the employer. Read the unverified papers in a browser. Build the splitter, the two score rules, the prober and the cost log. Run the three-model pilot | **Go or no-go on 22 November** on the five conditions in the report |
| 23–29 Nov | Full build and home probes on DDXPlus for six models. Finish all Haiku 4.5 calls. Set up MemRL's code on the operating-system tasks | Home-validity table; first three cross pairs |
| 30 Nov–6 Dec | All twelve pairs on DDXPlus; BIRD build and probes; offline scoring of every arm | Main table and figure on two benchmarks (the minimum bar) |
| 7–15 Dec | Live check on four pairs; released-code leg; RoMeRL frozen banks; the three mechanism analyses. **Freeze on 15 December** | The target bar, if the effect is there |
| 16–31 Dec | Read the ICLR 2027 decisions (16 December). Choose the route from the result. Draft methods and results. Build the release package | Technical draft |
| 1–7 Jan | Abstract, introduction and Figure 1, written for the first-stage screen. One outside reader | The first page |
| 8–14 Jan | Related work, limits, disclosure statements. Fix the author list. Abstract in on 14 January | Abstract submitted |
| 15–22 Jan | Every reference checked by hand; appendix; anonymised repository; submit on 22 January 2027 | Submission |

**After submission:** first-stage notice 23 February, final decision 3 May 2027. Prepare the NeurIPS 2027 version in April regardless, because its deadline may fall days after the ICML decision; its 2027 rules are not posted, and the 2026 track welcomed "negative results, critical analyses" and audits. TMLR is the last step.

## 7. What only you or your employer can settle

- Publication clearance, and the customer-derived column names in the project's hand-over files.
- A co-author with an accepted paper at a listed venue. This removes the one-submission cap and is the largest lever outside the experiment; the author list closes on 14 January.
- Whether you have any prior paper at a listed venue (this decides whether the cap applies).
