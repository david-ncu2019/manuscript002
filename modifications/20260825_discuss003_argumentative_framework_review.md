# Discussion review: discuss003.tex against the NHESS argumentative framework

**Scope:** `sections/discuss003.tex` (the Discussion section currently `\input` by `main.tex`).
**Compared against:** `planning/20260824_discussion_argumentative_framework_reverse_engineered.md` (a
pattern inventory built from 15 accepted NHESS papers, Steps 3-6), `sections/results004.tex` (every
number cited in the Discussion, checked against its source table), `sections/methods006.tex` (the
"38 predictors" claim), `writing_manu2.bib` (citation coverage), and `CLAUDE.md`'s novelty/framing
guardrails.
**Verdict:** No numeric error and no forbidden term found. Every value in `discuss003.tex` matches
its source table exactly. The findings below concern the Discussion's argumentative shape and one
missing mandatory citation, not factual correctness.

---

## Finding 1: every paragraph ends on a negative claim, leaving no paragraph the reader can cite as a positive conclusion

**Where:** All thirteen paragraphs of `discuss003.tex` (lines 4, 10, 13, 16, 19, 25, 28, 31, 34, 37,
43, 46, 49, 52).

**What the text shows:** Each paragraph's final sentence states what the evidence does *not*
establish. A representative sample, in order: "cannot represent every depth section equally" (line
10); "rather than physical causes" (line 13); "does not identify a physical mechanism... or show
that S5 was estimated more accurately than S6" (line 16); "does not identify a physical mechanism or
guarantee performance in later months" (line 19); "produced no single monthly-error response across
the tested cases" (line 25); "does not identify a minimum or preferred initial-record length" (line
28); "does not show whether the cumulative discrepancy... was smaller or larger" (line 31); "does not
identify a preferred initial record or support ending MLCW measurements" (line 34); "its practical
interpretation must remain within the evidence boundary established at Tuku" (line 37); "do not
establish the same performance at other monitoring stations" (line 43); "do not prove that a
particular... variable causes deformation" (line 46); "do not provide complete descriptions of
observational uncertainty" (line 49); "without defining an acceptable operational error threshold...
or a measurement schedule suitable for all settings" (line 52). Thirteen out of thirteen paragraphs
close this way.

**What the framework says about this pattern:** Design Principle 3 (framework, line 1793) and
Checklist rule 5 (line 1857) both require hedge strength to be calibrated **paragraph by paragraph**
against what that paragraph's own evidence supports, not applied at one uniform strength throughout.
The framework's strongest, most-confirmed rule (A4a, 14/15 papers, line 1774) is to place a
limitation locally next to the claim it qualifies — `discuss003.tex` does this correctly. But A4a
describes *where* a limitation belongs, not *how the paragraph should end*. None of the 15 source
papers close all of their Discussion paragraphs on a caveat; the framework's own closing-move
analysis (Step 4, item 9, line 1755) documents three legitimate ways to end a *Discussion section* —
reasserting the contribution, issuing a forward-research call, or ending on one precisely scoped
limitation — but that analysis applies to the section's *final* paragraph, not to every paragraph
inside it.

**Why this matters for the reader:** A reader who reaches the end of Section 5 cannot point to a
single sentence and say "this is what Tuku showed." The manuscript's own guardrail note
(`CLAUDE.md`, "Novelty / framing guardrails") requires the reduced-sampling and coverage claims to be
kept separate and evidence-bounded — `discuss003.tex` honors that requirement carefully. The cost is
that caution has become the paragraph's structural default rather than a property applied where the
evidence specifically calls for it.

**Recommendation:** For each paragraph, identify the one finding it is built around, and open that
paragraph with the positive form of the finding (what the data show) before the caveat that bounds
it. The lead-development structure required by `style.md` (line 64-68: "state the main point... then
develop it with... qualification") already asks for this ordering; the current paragraphs instead
develop toward the qualification as the terminal move. Two paragraphs illustrate the fix directly.
Line 10-11 ("Monthly estimation was stronger in S1-S4... MLCW measurements can therefore show where a
station-level signal does not describe the profile uniformly, and a station-wide average cannot
represent every depth section equally") could close on the positive capability MLCW information adds
(what it *can* show) rather than on what a station-wide average cannot do. Line 43 ("The results
therefore do not establish the same performance at other monitoring stations... Tuku instead provides
a detailed evaluation of the framework within one instrumented monitoring system") already contains
its positive form in the same sentence — the paragraph could end there instead of one clause earlier.
This is a **story-pass** change (reordering and re-balancing existing content), not new scientific
content, and needs author confirmation only on which finding is each paragraph's intended positive
anchor.

**Severity:** Medium — does not misstate evidence, but weakens the section's ability to deliver a
citable answer to the manuscript's own research question.

---

## Finding 2: Hung et al. (2025) is required by the manuscript's own guardrail note but is absent from every section, including the Discussion

**Where:** `sections/discuss003.tex` (no citation anywhere); confirmed absent from
`sections/intro001.tex`, `dataset003.tex`, `studyarea001.tex`, `studyarea002.tex`, `discuss001.tex`,
`discuss002.tex` as well — a project-wide gap, not a Discussion-only omission.

**What the bibliography shows:** `writing_manu2.bib` contains the entry `hung2025_realtime`, titled
"Near real-time subsidence monitoring and AI forecasting with multi-depth extensometers" (Hung,
Hwang, Tosi, Lin, Lin, Chen — 2025). This is the closest prior study to the present manuscript: same
TUKU station, high-frequency extensometer records, and a forecasting model, per the project's own
characterization in `planning/20260802_hung2025_overlap_and_novelty_note.md`. The bibliography entry
exists but the citation key `hung2025_realtime` is never invoked (`\citet` or `\citep`) in any
`sections/*.tex` file.

**What the mandatory instruction says:** `CLAUDE.md`, under "Novelty / framing guardrails," states
directly: "Cite Hung et al. (2025) explicitly and state the distinction directly wherever the two
studies could be confused (Introduction, Discussion)." This is listed as a required action, not a
stylistic option, and it names the Discussion specifically as one of the two sections where the
citation and distinction must appear.

**What the framework independently confirms:** Concordance-first validation (A1, framework line
1778) is the second-strongest recurring pattern in the 15-paper corpus (10/15, clears the two-thirds
threshold), conditioned on the study having an independently measurable headline output — which this
manuscript does (Section 4.1's per-section R², RMSE, MAE). Hung et al. (2025) is the only published
study close enough in site, method family, and monitoring target to serve as that external
comparator. Its absence means the Discussion has no A1-type paragraph at all, closing off a pattern
the framework identifies as near-mandatory for a paper of this design.

**Recommendation:** Add one paragraph, most naturally adjacent to
`subsec:discussion_layerwise_estimation` or as a new opening move in
`subsec:discussion_reduced_mlcw_information`, that names Hung et al. (2025) explicitly and states the
distinction the guardrail note requires: this manuscript nowcasts monthly compaction from
groundwater-level change and cGNSS displacement at coarser (monthly) resolution, while Hung et al.
(2025) forecasts from high-frequency extensometer records using Prophet. Whether the two studies'
reported errors are numerically comparable (true concordance) or the paragraph must instead state why
they are not directly comparable (a scope-distinction move rather than a concordance move) is a
factual question this review cannot answer from the Discussion text alone — it requires reading Hung
et al. (2025)'s reported error metrics, which is exactly the kind of manuscript-grounded but
externally sourced content that `style.md` (line 112) classifies as requiring author confirmation
before drafting.

**Severity:** High — this is a named, mandatory requirement in the project's own governing
instructions, not a discretionary style improvement, and it is currently unmet everywhere in the
manuscript, not only in the Discussion.

---

## Finding 3: three questions the author marked directly in Results with Vietnamese NOTE comments remain unanswered by any mechanism in the Discussion

**Where:** `sections/results004.tex` line 50 (coefficient variation across depth sections), line 44
(why S5/S6 underperform S1-S4), and line 173 (which schedule accumulates less cumulative error over a
matched six-month span). Corresponding Discussion passages: `discuss003.tex` line 13 (responds to the
line 50 question), line 11 (responds to the line 44 question), line 31 (responds to the line 173
question).

**What the Results NOTEs ask, in the author's own words:** Line 50: "tại sao lại có sự việc này xảy
ra, hãy thảo luận nguyên do của nó trong phần Discussion" (why does this happen — discuss the reason
in the Discussion). Line 44 carries the same instruction, attached to the S1-S4 versus S5-S6
performance gap. Line 173 is more specific: it asks whether, under a twelve-month measurement
schedule, the cumulative error over that schedule's first six months would be smaller or larger than
the cumulative error over a complete six-month schedule.

**What the Discussion currently does at each location:** Line 13 restates that the fitted relations
"were not uniform across the monitored profile" and immediately adds "Coefficient signs and
magnitudes nevertheless describe statistical associations in the Tuku record rather than physical
causes" — describing the pattern again without proposing why it exists at any level, including a
hedged, literature-attributed level. Line 11 states directly that no physical cause is identified,
consistent with the manuscript's guardrail against unverified mechanism claims, but does not use the
one tool the framework documents for this exact situation. Line 31 states plainly that the current
comparison "does not show" the answer to the line-173 question — an honest and correct statement
about what the endpoint comparison alone can support, but it does not indicate whether the needed
comparison is achievable from data the manuscript already has.

**What the framework offers that has not yet been used:** Pattern A3 (framework line 1782, 1853) is
defined precisely for this situation: propose a candidate mechanism for a pattern the paper's own
data cannot directly test, but attribute it explicitly to external literature using a reporting verb,
rather than choosing only between an unqualified claim and silence. Design Principle 3 (framework
line 1793) reinforces this as the correct middle path when a mechanism concerns a variable outside
the study's own measured scope — exactly the situation for line 50 (why coefficients differ by depth)
and line 44 (why S5/S6 underperform). `discuss002.tex` (an earlier, superseded draft, dated 2026-08-05
per `git log`) contains a directly relevant sentence not carried into `discuss003.tex`: "The 200-250 m
depth section (S5) attained a near-zero or negative R², consistent with the absence of a piezometric
observation well screened within the compacting fine-grained deposits at that depth" — this is an
observational fact about instrument geometry, not a physical-mechanism claim, and could plausibly
answer part of the line-44 question without violating the guardrail against causal overclaiming. This
review does not know why that sentence was removed between `discuss002.tex` and `discuss003.tex`
and flags it only as a candidate the author should evaluate, not a recommendation to restore it
unchanged.

The line-173 question is different in kind from the other two: it is answerable by a **quantitative
comparison already latent in reported data**, not by a mechanism claim. `results004.tex` line
139-140 already reports the matched 72-month paired comparison; the specific sub-comparison the
author asks for (cumulative error over the first six months of a twelve-month schedule, versus
cumulative error over one complete six-month schedule) is a supplementary calculation on data the
manuscript states exists (`supp-tab:supp_reduced_frequency_endpoint_full`), not a new measurement.

**Recommendation:** Treat the two mechanism questions (lines 50, 44) and the one quantitative
question (line 173) differently. For lines 50 and 44, draft one attributed-mechanism sentence each,
following the A3 pattern, and bring the candidate explanation to the author as an
`[AUTHOR CONFIRMATION REQUIRED]` item before it enters manuscript prose — per `style.md` line 115,
this is new scientific content (a candidate mechanism) even when hedged, and requires explicit
confirmation rather than inference. For line 173, this is a data-availability question, not a
wording question: confirm with the author whether the described sub-comparison can be computed from
already-reported results, and if so, add it as a numeric result (likely in
`subsec:results_reduced_frequency` or its supplementary table) before the Discussion can honestly
answer it — the Discussion cannot resolve an evidence gap that Results has not yet closed.

**Severity:** Medium for lines 50 and 44 (an available, guardrail-compliant tool is not yet used).
Medium-high for line 173 (the Discussion's current "does not show" statement is accurate, but the
underlying question may be answerable with data already in hand, which would change what Results
and Discussion can jointly claim).

---

## Finding 4: `subsec:discussion_reduced_mlcw_information` merges two distinct Results experiments under one heading

**Where:** `discuss003.tex` line 22-38 (`\subsection{Estimation with reduced MLCW information}`).

**What the text shows:** Lines 25-29 discuss the reduced-measurement-frequency experiment (N=6 vs.
N=12 month schedules, corresponding to `results004.tex` `subsec:results_reduced_frequency`). Lines
31-38 shift, within the same subsection and without a new heading, to the no-subsequent-MLCW
experiment (corresponding to `results004.tex` `subsec:results_no_subsequent_mlcw` — the endpoint-MAE
and month-80 cumulative-error findings at line 34 are exclusive to that Results subsection). Results
itself treats these as two separate subsections with two separate labels.

**What the framework says:** Design Principle 1 (framework line 1791) states every Discussion
paragraph should be traceable to exactly one specific finding. The paragraphs here are each
individually traceable, but the subsection heading spans two experiments, which can make it harder
for a reader scanning by heading to locate which Results subsection a given Discussion paragraph
answers.

**Recommendation:** This is a structural question for the author, not a defect requiring a fix. The
merge may be intentional — both experiments answer the same higher-level question ("what happens when
direct MLCW information becomes less frequent") and the framework's own B3 pattern (line 1700)
confirms that where interpretive content sits does not have to mirror Results' section boundaries
one-to-one. If the merge is intentional, consider a one-sentence bridge at line 30-31 stating
explicitly that the discussion now shifts from the reduced-frequency experiment to the
no-subsequent-MLCW experiment, so the transition is signposted rather than implicit. If unintentional,
splitting into two subsections (matching Results) is the alternative.

**Severity:** Low — a navigability question, not a correctness or completeness issue.

---

## Summary table

| # | Finding | Severity | Action needed before submission? |
|---|---|---|---|
| 1 | All 13 paragraphs end on a negative claim; no paragraph offers a citable positive conclusion | Medium | Yes — rebalance paragraph endings; story-pass only, needs author sign-off on each paragraph's positive anchor |
| 2 | Hung et al. (2025) required by `CLAUDE.md` guardrail, absent from Discussion (and whole manuscript) | High | Yes — mandatory citation; needs author to supply or confirm the comparability of Hung et al. (2025)'s reported errors |
| 3 | Two mechanism questions (results004.tex lines 50, 44) and one quantitative question (line 173), all self-flagged by the author, remain open | Medium / Medium-high | Yes — mechanism questions need `[AUTHOR CONFIRMATION REQUIRED]` attributed-mechanism drafts; the quantitative question needs a data-availability check before Discussion can answer it |
| 4 | `subsec:discussion_reduced_mlcw_information` spans two distinct Results experiments under one heading | Low | Author's judgment — add a bridge sentence, or split, or leave as intentional |

**Bottom line:** `discuss003.tex` is numerically accurate throughout — every value checked against
`results004.tex` and `methods006.tex` matches exactly, and no forbidden term from `domain.md` appears.
The section also applies the framework's single strongest rule correctly: limitations sit locally,
next to the claims they qualify, rather than batched at the end. The two things most worth fixing
before this section can be said to fully deliver the manuscript's intended message are structural,
not factual: the uniform negative-ending pattern across all thirteen paragraphs (Finding 1), and the
missing, project-mandated Hung et al. (2025) comparison (Finding 2). Both are fixable without adding
any claim the evidence does not already support.
