# Discussion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` (recommended) or `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the Discussion as three connected subsections that interpret the evidence already reported for delayed MLCW delivery, reduced MLCW measurement frequency, and the absence of subsequent MLCW measurements at Tuku.

**Architecture:** The Discussion will follow the same information-loss sequence established in Methods 3.4 and Results 4.1--4.3. A short opening will state the evidence-bounded answer, Subsection 5.1 will interpret depth-dependent monthly estimation and posterior intervals, Subsection 5.2 will connect reduced-frequency and no-subsequent-measurement designs, and Subsection 5.3 will define limitations and practical scope. Before drafting Discussion, Results 4.2 and the Supplementary Materials will receive the already approved Q12 and Q13 paired-comparison evidence needed by Subsection 5.2.

**Tech Stack:** LaTeX, BibTeX, PowerShell, existing frozen CSV evidence, `pdflatex`, and `bibtex`.

## Global Constraints

- Work only on branch `reduced_v1` in `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1`; never merge this branch.
- Do not run or refit any model. Read only the frozen Q12 and Q13 evidence under `discussion_evidence_20260821`.
- Preserve all existing `% NOTE` and `% AUTHOR RESPONSE` comments unless the author explicitly approves their removal.
- Apply `david-writing-styles` to every paragraph. Use one controlling point, known-to-new progression, topic-action-stress sentences, and a paragraph ending that resolves or prepares the next point.
- Do not use first-person pronouns, em dashes, the word `retain`, or unexplained machine-learning jargon in manuscript prose.
- Do not use `pooled`, `ablation`, `confound`, `weak`, `sufficient`, `optimal schedule`, or `spatial transfer` in the submitted manuscript.
- Q11 and the fabricated-sinusoid comparison remain internal reviewer-response evidence and must not appear in Results or Discussion.
- Report observations before interpretations. Do not introduce new numerical results in Discussion.
- Do not claim that cGNSS or hydraulic head contributes unique information beyond seasonal variation. State only that the fitted model combined hydraulic head, vertical surface displacement, and seasonal variables.
- Do not recommend a 3-, 5-, or 8-year initial record, a 6- or 12-month schedule, or permanent cessation of MLCW measurements.
- Keep limitations in Subsection 5.3. Earlier Discussion subsections may qualify a claim but must not repeat the limitations catalogue.
- Use two decimal places for ordinary deformation values. Use three decimal places for paired MAE differences and their 95% intervals because two decimal places would erase signs or produce misleading `0.00` values.
- Add one `% NOTE: ... %` immediately below every new Discussion paragraph to state its intended message in plain Vietnamese for author review.
- Preserve the current labels and citation keys. Add no citation unless the cited source has been checked for the exact claim.
- Stage and commit only files named by the current task. Leave unrelated modified and untracked files untouched.

---

## File Map

- Modify `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\results004.tex` only to add the approved Q12 and Q13 Results evidence required by Discussion 5.2.
- Modify `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\supplement001.tex` to provide the complete paired-comparison values supporting the concise Results statements.
- Modify `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\discuss003.tex` to replace both placeholders with the complete Discussion.
- Modify `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\writing_manu2.bib` only if a citation selected below is absent or malformed. The current bibliography already contains `hung_measuring_2021`, `burbey_extensometer_2020`, `mackay_bayesian_1992`, `dormann_collinearity_2013`, `hastie_elements_2009`, `gelman_bayesian_2013`, and `gneiting_probabilistic_2007`.
- Do not modify `main.tex`; it already inputs `sections/results004`, `sections/discuss003`, and `sections/appendix002`.

## Frozen Evidence Sources

- Q12 interpretation boundary and design checks:
  `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results003_calendar_aligned_38predictors\discussion_evidence_20260821\q12_reduced_frequency_reference\Q12_INTERPRETATION_REPORT.md`
- Q12 values:
  `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results003_calendar_aligned_38predictors\discussion_evidence_20260821\q12_reduced_frequency_reference\paired_metric_differences.csv`
- Q13 interpretation boundary and design checks:
  `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results003_calendar_aligned_38predictors\discussion_evidence_20260821\q13_initial_history\Q13_INTERPRETATION_REPORT.md`
- Q13 values:
  `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results003_calendar_aligned_38predictors\discussion_evidence_20260821\q13_initial_history\pairwise_history_differences.csv`
- Approved story and argument boundaries:
  `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\planning\20260821_dialogue.md`, especially Correspondence 9.

### Task 1: Create a scoped baseline checkpoint and lock the evidence

**Files:**
- Review: `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\results004.tex`
- Review: `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\supplement001.tex`
- Review: `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\figure_source_manifest.json`
- Review: `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\figures\fig_results_no_subsequent_mlcw_cumulative_error.pdf`

**Interfaces:**
- Consumes: the currently approved Results 4.3 prose and revised Figure 13.
- Produces: a recoverable Git checkpoint before Discussion work begins.

- [ ] **Step 1: Confirm repository and branch**

Run:

```powershell
git -C D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1 rev-parse --show-toplevel
git -C D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1 branch --show-current
git -C D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1 status --short
```

Expected: repository root is the manuscript worktree and branch is `reduced_v1`.

- [ ] **Step 2: Review the current scoped changes**

Run:

```powershell
git -C D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1 diff -- sections/results004.tex sections/supplement001.tex figure_source_manifest.json
```

Expected: the diff contains the approved Results edits, supplementary references, and Figure 13 provenance. Do not stage unrelated files.

- [ ] **Step 3: Build the current baseline**

Run from `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1`:

```powershell
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Expected: both commands exit with code 0 and produce `main.pdf` without undefined references.

- [ ] **Step 4: Commit the baseline checkpoint**

```powershell
git add -- sections/results004.tex sections/supplement001.tex figure_source_manifest.json figures/fig_results_no_subsequent_mlcw_cumulative_error.pdf
git commit -m "checkpoint: align no-subsequent-MLCW results with revised figures"
```

If the ignored PDF is not staged, use `git add -f -- figures/fig_results_no_subsequent_mlcw_cumulative_error.pdf` and rerun the same commit. Do not add any other ignored PDF.

### Task 2: Add the approved Q12 and Q13 evidence needed by Discussion 5.2

**Files:**
- Modify: `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\results004.tex`, within `\subsection{Estimation under reduced MLCW measurement frequency}`.
- Modify: `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\supplement001.tex`, within the reduced-frequency supplementary section.

**Interfaces:**
- Consumes: frozen Q12 and Q13 CSV files listed above.
- Produces: two concise Results claims and complete supplementary evidence that Discussion 5.2 may interpret without introducing new results.

- [ ] **Step 1: Add the Q12 comparison to Results 4.2**

Insert one paragraph after the existing paragraph that compares the 3-, 5-, and 8-year monthly error series. Its exact scientific content must be:

- Comparison basis: the same six depth sections and the same 432 section-month observations from 05/2018 through 04/2024.
- Direction convention: reduced-frequency scenario minus delayed monthly-record scenario.
- Main pattern: four of the six 95% intervals for the MAE difference included zero, so those four comparisons did not establish a stable direction of change.
- Exceptions: the 8-year initial record had higher MAE under both schedules, with differences of `0.015 [0.002, 0.028]` mm/month for six-month measurements and `0.024 [0.004, 0.043]` mm/month for twelve-month measurements.
- Boundary: an interval containing zero does not establish equivalence.
- Reference the new supplementary table with `\Cref{supp-tab:supp_reduced_frequency_vs_delayed}`.
- Add a Vietnamese `% NOTE` explaining that the paragraph compares reduced-frequency estimation with the delayed-delivery reference over identical observations.

- [ ] **Step 2: Add the Q13 comparison to Results 4.2**

Insert the next paragraph so it begins from the initial-record question created by the Q12 paragraph. Its exact scientific content must be:

- Main pattern: monthly MAE did not decline monotonically from 3 to 5 to 8 years under either measurement schedule.
- Representative evidence: the 8-year record had higher MAE than the 5-year record by `0.031 [0.014, 0.047]` mm/month under the six-month schedule and `0.036 [0.018, 0.052]` mm/month under the twelve-month schedule.
- Boundary: these comparisons do not establish that 3 years is adequate, 5 years is preferable, or 8 years is excessive.
- Reference the new supplementary table with `\Cref{supp-tab:supp_initial_history_differences}`.
- Add a Vietnamese `% NOTE` explaining that more historical observations did not guarantee lower monthly error over the common evaluation period.

- [ ] **Step 3: Add the complete Q12 supplementary table**

Add a table labeled `\label{tab:supp_reduced_frequency_vs_delayed}` with six rows and these columns:

| MLCW interval | Initial record | MAE difference | 95% interval |
|---|---:|---:|---:|
| 6 months | 3 years | -0.007 | [-0.032, 0.026] |
| 6 months | 5 years | -0.016 | [-0.041, 0.009] |
| 6 months | 8 years | 0.015 | [0.002, 0.028] |
| 12 months | 3 years | 0.002 | [-0.030, 0.039] |
| 12 months | 5 years | -0.012 | [-0.042, 0.020] |
| 12 months | 8 years | 0.024 | [0.004, 0.043] |

The caption must define the difference as reduced-frequency minus delayed monthly-record estimation, state `n=432` matched section-month observations per row, and explain that an interval containing zero does not demonstrate equivalence.

- [ ] **Step 4: Add the complete Q13 supplementary table**

Add a table labeled `\label{tab:supp_initial_history_differences}` with six rows and these columns:

| MLCW interval | Initial-record contrast | MAE difference | 95% interval |
|---|---|---:|---:|
| 6 months | 5 years minus 3 years | -0.009 | [-0.035, 0.015] |
| 6 months | 8 years minus 3 years | 0.021 | [-0.003, 0.042] |
| 6 months | 8 years minus 5 years | 0.031 | [0.014, 0.047] |
| 12 months | 5 years minus 3 years | -0.014 | [-0.028, 0.004] |
| 12 months | 8 years minus 3 years | 0.022 | [0.002, 0.037] |
| 12 months | 8 years minus 5 years | 0.036 | [0.018, 0.052] |

The caption must define each value as the longer initial record minus the shorter initial record, state `n=432` matched section-month observations per comparison, and explain that negative values favor the longer record only in the limited sense of lower MAE.

- [ ] **Step 5: Verify source parity and LaTeX references**

Run:

```powershell
git diff --check
rg -n "supp_reduced_frequency_vs_delayed|supp_initial_history_differences|0\.015|0\.024|0\.031|0\.036" sections/results004.tex sections/supplement001.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error supplement.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Expected: both documents compile, both new labels resolve, and every representative value appears once in Results and once in its full supplementary table.

- [ ] **Step 6: Commit the Results prerequisite**

```powershell
git add -- sections/results004.tex sections/supplement001.tex
git commit -m "results: add matched comparisons for reduced MLCW information"
```

### Task 3: Write Discussion 5.1 on layerwise monthly deformation estimation

**Files:**
- Modify: `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\discuss003.tex`.

**Interfaces:**
- Consumes: Results 4.1, `tab:delayed_performance_interval`, `tab:selected_coefficients`, Methods predictive-uncertainty definitions, and checked bibliography entries.
- Produces: the Discussion opening and Subsection 5.1.

- [ ] **Step 1: Replace the general Discussion placeholder with a one-paragraph opening**

The opening must answer the paper-level question without repeating a list of metrics. Its argument must be:

1. Hydraulic head, vertical surface displacement, and seasonal observations supported monthly layerwise deformation estimation at Tuku under the three MLCW-information conditions.
2. The evidence was strongest in S1--S4 and less uniform in S5--S6.
3. Reducing MLCW information did not cause the same immediate change in monthly error in every tested case, but it reduced the frequency of independent depth-specific checks on accumulated deformation.

End on `independent depth-specific checks` so Subsection 5.1 can first establish why depth matters. Add one Vietnamese `% NOTE` stating this three-part answer.

- [ ] **Step 2: Add Subsection 5.1 heading and depth-dependent interpretation**

Use:

```latex
\subsection{Layerwise monthly deformation estimation}
\label{subsec:discussion_layerwise_estimation}
```

Write one paragraph that:

- begins with the stronger S1--S4 performance already established in Results 4.1;
- uses the reported differences in $R^2$, MAE, and RMSE only as brief reminders, not a second Results table;
- explains that a surface-displacement observation integrates deformation across the monitored profile, whereas MLCW measurements resolve deformation among depth sections;
- cites `\citet{hung_measuring_2021}` for the value of multilayer aquifer-system compaction measurements and, only if its checked text directly supports the sentence, `\citet{burbey_extensometer_2020}` for extensometer interpretation;
- ends by stating that a station-wide average cannot represent every depth section equally.

Do not assign the S5--S6 pattern to missing deep hydraulic-head observations or a particular sediment mechanism unless that mechanism has already been demonstrated in the active manuscript. Add a Vietnamese `% NOTE` explaining this evidence boundary.

- [ ] **Step 3: Interpret the fitted coefficients without causal language**

Write one paragraph that moves from the depth-dependent performance to the fitted relations. It must state that:

- current surface-displacement increments had repeated positive coefficient ranges in S1--S4 and S6;
- hydraulic-head and seasonal coefficients varied more among sections;
- these patterns show that the fitted relations were not uniform with depth;
- coefficient shrinkage helps stabilize estimation when variables contain overlapping information, but coefficient sign and magnitude remain statistical associations rather than physical causes.

Cite `\citep{dormann_collinearity_2013, hastie_elements_2009, mackay_bayesian_1992}` only on the shrinkage and overlapping-information sentence. Add a Vietnamese `% NOTE` stating that this paragraph explains model behavior without claiming causality.

- [ ] **Step 4: Interpret coverage and interval width together**

Write one paragraph that:

- begins from the distinction between point error and interval performance established in Results 4.1;
- states that coverage below 90% means the intervals contained fewer observations than their nominal level implies;
- explains that increasing interval width may raise coverage but provides less precise information, so coverage and width must be read together;
- notes that Bayesian construction does not guarantee empirical 90% coverage in a finite, temporally dependent observational record;
- cites `\citep{gneiting_probabilistic_2007, gelman_bayesian_2013}`;
- ends by preparing the reduced-information question in Subsection 5.2.

Do not list every section-level coverage value again. Add a Vietnamese `% NOTE` explaining the coverage-width tradeoff in plain language.

- [ ] **Step 5: Audit and commit Subsection 5.1**

Run:

```powershell
rg -n "\\placeholder|\b(I|we|our|us|ours)\b|pooled|ablation|retain|weak" sections/discuss003.tex
git diff --check
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Expected: the general Discussion placeholder is gone, the limitations placeholder remains for Task 5, and the manuscript compiles without undefined citations or references.

```powershell
git add -- sections/discuss003.tex
git commit -m "discussion: interpret depth-dependent monthly estimation"
```

### Task 4: Write Discussion 5.2 on reduced MLCW information

**Files:**
- Modify: `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\discuss003.tex`.

**Interfaces:**
- Consumes: Results 4.2--4.3, Q12 and Q13 supplementary tables, endpoint-error evidence, and Figure 13.
- Produces: one connected interpretation of less-frequent and absent subsequent MLCW measurements.

- [ ] **Step 1: Add Subsection 5.2 heading and interpret the matched Q12 comparison**

Use:

```latex
\subsection{Estimation with reduced MLCW information}
\label{subsec:discussion_reduced_mlcw_information}
```

Write one paragraph that:

- begins from the reduced-information question prepared by Subsection 5.1;
- explains that four of six paired MAE intervals crossed zero and therefore did not establish a stable direction of change;
- identifies the two 8-year exceptions without repeating their full intervals, because those numbers already appear in Results and Supplementary Materials;
- explicitly states that crossing zero does not establish equivalent performance;
- resolves that reduced measurement frequency did not produce one uniform monthly-error response across the tested cases at Tuku.

Add a Vietnamese `% NOTE` explaining why `no stable direction` is narrower than `no effect` or `equivalent`.

- [ ] **Step 2: Interpret initial-record length without choosing a preferred duration**

Write one paragraph that begins from the heterogeneity among Q12 scenarios and then states:

- MAE did not decline monotonically as the initial record increased from 3 to 5 to 8 years;
- the 8-year record had higher MAE than the 5-year record under both schedules;
- a longer initial record includes an earlier and different calendar period, so more observations do not necessarily provide relations that better represent the later evaluation period;
- the evidence rejects `more history always improves estimation` but does not identify a minimum or preferred initial-record length.

Treat the calendar-period explanation as an interpretation, not a tested mechanism. Add a Vietnamese `% NOTE` stating this boundary.

- [ ] **Step 3: Explain why endpoint errors differ more than monthly errors**

Write one paragraph that connects monthly error to cumulative endpoint error. It must explain:

- average monthly MAE occupied a narrow range across the six reduced-frequency scenarios;
- endpoint MAE was larger for the 12-month schedule because each endpoint accumulated twice as many monthly errors before the next MLCW measurement;
- this comparison does not show that any equal six-month portion of the 12-month schedule was less accurate than a complete six-month schedule;
- a new MLCW measurement provides both model-updating information and an independent cumulative deformation check.

Do not introduce the older local-only sensitivity outputs from `tuku_no_update_sensitivity`. Add a Vietnamese `% NOTE` explaining the distinction between monthly error and endpoint accumulation.

- [ ] **Step 4: Continue from sparse measurements to no subsequent MLCW measurements**

Write one paragraph that:

- uses the loss of the next MLCW checkpoint as the bridge from Results 4.2 to Results 4.3;
- states that monthly MAE remained similar among the 3-, 5-, and 8-year initial records;
- explains that signed monthly errors could add to or offset earlier errors, producing cumulative-error trajectories whose ordering changed over time and by depth section;
- notes that the 8-year record had the lowest average absolute cumulative error at month 80 but not throughout the period or in every section;
- does not claim that the model failed, that MLCW can be stopped, or that eight years is preferable.

Add a Vietnamese `% NOTE` explaining that monthly agreement and cumulative agreement answer different questions.

- [ ] **Step 5: Resolve Subsection 5.2 without an operational recommendation**

Write a short resolution paragraph stating that reduced MLCW information did not cause an immediate and uniform loss of monthly performance under the tested Tuku conditions, but fewer MLCW measurements also meant fewer independent opportunities to check accumulated depth-specific deformation. End on the need to define the evidence boundary, which prepares Subsection 5.3. Add a Vietnamese `% NOTE` stating that this is a scientific implication, not a recommended field schedule.

- [ ] **Step 6: Audit and commit Subsection 5.2**

Run:

```powershell
rg -n "equivalent|sufficient|optimal|recommend|can stop|pooled|ablation|weak|\b(I|we|our|us|ours)\b" sections/discuss003.tex
git diff --check
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Expected: any occurrence of `equivalent`, `sufficient`, or `recommend` appears only in a sentence explicitly rejecting that interpretation; no forbidden internal vocabulary appears.

```powershell
git add -- sections/discuss003.tex
git commit -m "discussion: connect reduced and absent MLCW information"
```

### Task 5: Write Discussion 5.3 on limitations and practical scope

**Files:**
- Modify: `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\discuss003.tex`.

**Interfaces:**
- Consumes: the evidence boundaries already established in Discussion 5.1--5.2 and the existing label `subsec:discussion_limitations`.
- Produces: a dedicated limitations subsection that bounds generalization, causal interpretation, and posterior uncertainty.

- [ ] **Step 1: Replace the limitations placeholder while preserving its label**

Keep:

```latex
\subsection{Limitations and practical scope}
\label{subsec:discussion_limitations}
```

Delete only the placeholder command. Do not change references in Results that point to this label.

- [ ] **Step 2: State the single-site and depth-section boundary**

Write one paragraph that:

- states that the evidence establishes performance for the tested monitoring record at Tuku;
- notes that the contrast between S1--S4 and S5--S6 already demonstrates heterogeneity within one site;
- explains that the results therefore do not establish the same performance at other stations or every depth interval;
- presents Tuku as a detailed single-site evaluation rather than a spatial-generalization study.

Do not mention a future spatial-transfer manuscript. Add a Vietnamese `% NOTE` explaining that the paragraph limits generalization without dismissing the case study.

- [ ] **Step 3: Separate fitted association from physical mechanism**

Write one paragraph that:

- states that Bayesian ridge coefficients describe associations in the Tuku calibration record;
- explains that shrinkage stabilizes fitting but does not identify causal mechanisms;
- notes that the regression does not replace a coupled groundwater-flow and aquifer-system-deformation model;
- prevents the coefficient discussion from being read as proof that a particular hydraulic-head or surface-displacement variable causes deformation in one section.

Use `\citep{dormann_collinearity_2013, hastie_elements_2009}` only if needed to support the statistical boundary. Add a Vietnamese `% NOTE` explaining the distinction between association and mechanism.

- [ ] **Step 4: Define the boundary of posterior predictive uncertainty**

Write one paragraph that:

- states that posterior predictive intervals include coefficient uncertainty and residual variation represented by the fitted model;
- explains that they do not automatically include every source of uncertainty from field measurements, temporal alignment, interpolated hydraulic head, model form, or residual dependence;
- connects those omitted sources to the observed coverage below 90% as plausible contributors, not demonstrated causes;
- cites `\citep{gelman_bayesian_2013, gneiting_probabilistic_2007}`.

Add a Vietnamese `% NOTE` explaining why model-based uncertainty and total real-world uncertainty are not identical.

- [ ] **Step 5: End the Discussion on the bounded contribution**

Write one resolution paragraph that states:

- the framework quantifies monthly estimation error, cumulative discrepancy, and model-based uncertainty under three levels of MLCW information at Tuku;
- these quantities allow monitoring consequences to be evaluated explicitly;
- the study does not define an acceptable operational error threshold, an economic decision rule, or a universally suitable measurement schedule.

The final stress position must emphasize the contribution rather than end with `more research is needed`. Add a Vietnamese `% NOTE` stating the take-home message.

- [ ] **Step 6: Audit and commit Subsection 5.3**

Run:

```powershell
rg -n "\\placeholder|spatial transfer|optimal schedule|universal|\b(I|we|our|us|ours)\b|retain|weak" sections/discuss003.tex
git diff --check
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Expected: no Discussion placeholders remain, the existing limitations label resolves, and the final paragraph ends with the bounded contribution.

```powershell
git add -- sections/discuss003.tex
git commit -m "discussion: define limitations and practical scope"
```

### Task 6: Run the Methods--Results--Discussion integration audit

**Files:**
- Review: `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\methods006.tex`
- Review: `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\results004.tex`
- Review: `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\discuss003.tex`
- Review: `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\supplement001.tex`
- Review: `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\writing_manu2.bib`

**Interfaces:**
- Consumes: completed Discussion and supporting Results evidence.
- Produces: a submission-ready Discussion that tells one story across Methods 3.4 and Results 4.1--4.3.

- [ ] **Step 1: Audit one-to-one design coverage**

Confirm manually and record in the execution summary:

| Methods design | Results evidence | Discussion interpretation |
|---|---|---|
| 3.4.1 delayed MLCW records | 4.1 monthly errors, coefficients, coverage | 5.1 depth-dependent estimation and uncertainty |
| 3.4.2 less-frequent MLCW measurements | 4.2 monthly and endpoint errors, Q12, Q13 | first three arguments of 5.2 |
| 3.4.3 no subsequent MLCW measurements | 4.3 monthly and cumulative errors, coverage | final argument and resolution of 5.2 |

Expected: no substantial method is left uninterpreted and no Discussion claim lacks a reported result.

- [ ] **Step 2: Run the scientific-writing audit**

Read the complete `results004.tex` and `discuss003.tex` in sequence. Verify:

- each subsection opens with a scientific question or answer rather than a metric;
- each paragraph has one controlling point;
- each paragraph ending creates the next paragraph's topic;
- numbers are reminders in Discussion, not duplicated tables;
- interpretation follows evidence;
- mechanisms are explicitly marked as interpretations when not tested;
- limitations occur only in 5.3;
- terminology remains consistent for MLCW measurements, finalized MLCW records, hydraulic head, vertical surface displacement, monthly deformation increments, cumulative error, coverage, and interval width.

- [ ] **Step 3: Run text and reference checks**

```powershell
rg -n "\\placeholder|TBD|TODO|pooled|ablation|spatial transfer|retain|weak|firstly|secondly|thirdly" sections/discuss003.tex
rg -n "\\cite[p|t]?\{[^}]+\}|\\Cref\{[^}]+\}" sections/discuss003.tex
git diff --check
```

Expected: no unresolved placeholder or internal vocabulary remains. Every citation key exists in `writing_manu2.bib`, and every cross-reference resolves after the build.

- [ ] **Step 4: Run the full manuscript and supplement builds**

From `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1`:

```powershell
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error supplement.tex
pdflatex -interaction=nonstopmode -halt-on-error supplement.tex
```

Expected: all commands exit with code 0; `main.log` contains no undefined citation or reference; new overfull boxes are corrected before completion. Pre-existing warnings must be reported separately rather than silently attributed to this work.

- [ ] **Step 5: Review the PDFs**

Inspect `main.pdf` and the supplementary PDF for:

- subsection order and heading placement;
- page breaks around Discussion headings;
- supplementary table width and readability;
- citation rendering;
- unresolved yellow placeholders elsewhere in the manuscript, reported but not edited unless they block the Discussion.

- [ ] **Step 6: Create the final Discussion checkpoint**

```powershell
git status --short
git add -- sections/results004.tex sections/supplement001.tex sections/discuss003.tex writing_manu2.bib
git diff --cached --check
git commit -m "discussion: complete interpretation of reduced MLCW information"
```

Stage `writing_manu2.bib` only if Task 3 or Task 5 required an actual bibliography correction. Do not stage unrelated worktree files.

## Self-Review Result

- The plan covers the prerequisite Q12 and Q13 Results evidence, all three approved Discussion subsections, citations, integration, PDF review, and scoped commits.
- No model execution or new statistical analysis is requested.
- Q11 remains outside the manuscript.
- Every Discussion claim is linked to evidence already reported or added to Results and Supplementary Materials before interpretation.
- The plan contains no unresolved implementation placeholder.
