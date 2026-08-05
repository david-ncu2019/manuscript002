# Experiment Planning Brief: Reduced MLCW Sampling at Tuku

**Date:** 2026-08-01  
**Purpose:** Provide the scientific problem, existing evidence, and design questions that must be resolved before preparing a programming implementation plan.  
**Important:** This document is not an implementation plan. The next assistant must inspect the current repository, challenge the assumptions below where necessary, and propose the experiment and code organization before editing or running the production analysis.

## 1. Manuscript Direction

The manuscript has been reduced to a single representative monitoring site, Tuku. Its main scientific objective is to determine whether monthly compaction within six subsurface depth sections can be estimated from monitoring information that remains available when direct multilayer compaction monitoring well (MLCW) measurements become less frequent.

The intended future monitoring scenario is:

- the MLCW remains operational;
- direct MLCW field measurements are collected once every 6 months or once every 12 months;
- groundwater level (GWL) and adjacent cGNSS observations remain available at a higher temporal frequency;
- the local borehole lithological profile provides static information that distinguishes the depth sections;
- monthly section compaction is estimated between two MLCW field visits;
- the MLCW observation at the end of an interval represents cumulative compaction since the preceding visit;
- that endpoint observation is used to check the accumulated monthly estimates, not automatically to refit or correct the model.

The 6-month and 12-month schedules are equally important. The study should not treat the annual schedule merely as a minor sensitivity test.

## 2. Reduced Data Scope

The reduced manuscript uses site-specific data only:

1. monthly compaction for six standardized depth sections, S1 through S6, derived from the Tuku MLCW;
2. GWL observations at the Tuku monitoring location;
3. vertical surface displacement from the cGNSS station adjacent to the MLCW;
4. sediment composition from the local Tuku borehole log.

SBAS-InSAR observations and the regional 3D hydrogeological model are outside the reduced study. They must not re-enter the experiment through copied regional or spatial-transfer workflows.

The current manuscript draft describes a station-specific model fitted jointly across the six sections. Internal code labels such as `P3` or `level1b` may be used for provenance, but they must eventually be translated into plain scientific language in manuscript-facing outputs.

## 3. Current Evidence to Re-verify

The following facts were found during the present review. The next assistant must verify them against the live files before relying on them:

- Frozen input candidate: `007_tests/014_ml_nowcast/input_data/20260718_run048_v1/TUKU.parquet`.
- Current candidate model contract: `run048_feature_registry.resolve_profile("P3", "level1b")`.
- The current complete-case Tuku table contains 1,056 section-month rows.
- It covers 176 months from 2010-05 through 2024-12.
- Every complete month contains all six sections.
- The currently resolved profile contains 122 predictor columns.
- The stored target is the raw monthly MLCW difference in mm/month; the existing data documentation states that negative values indicate compaction.

These observations describe the present checkout only. The next assistant should record source hashes or other provenance so that later results can be traced to the exact snapshot and code state.

## 4. Why Existing `run_048` Results Are Insufficient

The existing `run_048` rolling-block evaluation does not reproduce the new monitoring scenario.

In the current workflow, a six-month score block is followed by later training that can include all six monthly MLCW responses from that block. This represents monthly observations becoming available in batches. It does not represent one cumulative MLCW observation collected at the end of a 6-month or 12-month field interval.

Additional gaps include:

- no dedicated comparison between cumulative predicted and observed compaction at 6-month and 12-month endpoints;
- no proof that endpoint MLCW observations remain outside later prediction or model-update steps;
- no focused Tuku-only evidence package for the reduced manuscript;
- no uncertainty output tailored to the fixed monthly estimates in this reduced scenario;
- existing persistence baselines may use hidden monthly MLCW values and may therefore be operationally invalid when monthly MLCW observations do not exist;
- existing figures and summaries cover many profiles, stations, and evaluation levels that are no longer part of the reduced paper.

The new work should therefore be treated as a separate evaluation protocol that inherits verified data preparation and model components from `run_048`, not as a relabeling of the current rolling-block results.

## 5. Questions the Next Assistant Must Resolve

The next assistant should analyze the following questions before proposing code changes. The answers must be justified from the data, the existing scripts, and the manuscript objective rather than selected to maximize reported performance.

### 5.1 Temporal design

- How much early history is required to estimate a model containing the current predictor set?
- How much independent history should be reserved to calibrate monthly uncertainty intervals?
- How many complete 6-month and 12-month intervals should remain for final retrospective evaluation?
- Should the evaluation intervals follow calendar half-years and years, and what scientific or operational interpretation supports that choice?
- How can the temporal split be selected without examining final-test performance?
- Is one fixed retrospective evaluation period sufficient, or is a limited temporal sensitivity analysis needed for a defensible Q2 manuscript?

The assistant may compare several candidate splits, but it must state the decision rule before reading final-test metrics. It must also distinguish model development, uncertainty calibration, and final evaluation.

### 5.2 Meaning of sparse MLCW observations

- Confirm how cumulative compaction between two field visits should be reconstructed from the available monthly MLCW series.
- Confirm the interval boundaries and sign convention.
- Check whether summing monthly increments is numerically consistent with differencing the corresponding cumulative MLCW values.
- Decide how incomplete intervals or missing auxiliary predictors should be handled without silently shortening the evaluation.
- Demonstrate that a 6-month endpoint and a 12-month endpoint are used only for evaluation under the currently agreed scenario.

### 5.3 Model inheritance

- Determine which parts of `run048_snapshot.py`, `run048_evaluation.py`, `run048_pipeline.py`, `04_conformal.py`, and the existing plotting utilities can be reused safely.
- Verify whether the present `P3` station-pooled-across-sections profile is still the correct frozen model for the reduced paper.
- Do not start another unrestricted feature search.
- Check that no MLCW target, lagged MLCW target, or endpoint MLCW value appears among the predictors.
- Determine whether existing target cleaning and scaling behavior is appropriate for a single fixed retrospective fit, and document any consequence for manuscript interpretation.

The next assistant should prefer new, focused modules or a separate supplement workflow if that protects the frozen `run_048` artifacts. It should not assume a specific file layout until it has inspected the current organization and naming patterns.

### 5.4 Reference estimates

The reduced experiment needs at least one simple reference estimate so that readers can judge whether Bayesian ridge regression adds value. However, a reference is invalid if it uses monthly MLCW observations that would be unavailable under the sparse schedule.

The assistant must:

- identify operationally valid baseline candidates;
- explain exactly what information each baseline would have at prediction time;
- exclude baselines that read hidden monthly MLCW responses;
- specify how any primary baseline is selected without using final-test outcomes;
- retain enough baseline output for transparent reporting even if only one baseline appears in the main manuscript.

No baseline has been approved in advance.

### 5.5 Monthly uncertainty

The manuscript should allocate space to uncertainty in monthly estimates. Existing split-conformal utilities and literature are available, but their use in this experiment still requires verification.

The assistant must determine:

- whether pooled or section-specific calibration is supported by the available calibration sample size;
- whether a nominal 90% interval remains the most defensible choice;
- how temporal dependence affects the interpretation of empirical coverage;
- which coverage and interval-width summaries should be reported;
- whether the existing `04_conformal.py` implementation can be reused unchanged.

Uncertainty intervals are required for monthly predictions only. Separate cumulative intervals for 6-month and 12-month endpoint totals are not currently requested. Endpoint reliability should instead be evaluated from cumulative prediction errors unless the assistant provides a strong scientific reason to revisit this decision.

### 5.6 Performance summaries

The assistant should propose a compact result set that directly answers the manuscript questions. At minimum, it should consider:

- monthly accuracy for S1 through S6 and all sections combined;
- performance relative to valid simple references;
- empirical interval coverage and interval width;
- cumulative agreement at every 6-month endpoint;
- cumulative agreement at every 12-month endpoint;
- differences in error accumulation between the two schedules;
- total profile compaction as well as section-specific compaction, where physically meaningful.

The assistant must judge which metrics are stable with the available number of endpoints. It should not report per-section statistics that are misleading when only a few annual intervals are available.

## 6. Expected Manuscript Evidence

The eventual implementation should provide enough evidence to write a short Results and Discussion section without rebuilding numbers manually. The planning assistant should specify the minimum tables, figures, and machine-readable records needed to support:

1. how accurately monthly compaction was estimated in each depth section;
2. whether the model improved on an operationally valid simple estimate;
3. whether the monthly uncertainty intervals were reasonably calibrated;
4. how monthly errors accumulated over 6-month intervals;
5. how monthly errors accumulated over 12-month intervals;
6. which sections were more or less reliable and whether the pattern has a plausible hydrogeological explanation;
7. the limits of drawing conclusions from one monitoring site and a retrospective simulation.

Figures should be limited to those needed for these claims. The planning assistant should avoid a Cartesian product of stations, profiles, levels, and diagnostics. Six- and twelve-month results should be displayed with equal visual and textual weight.

## 7. Reproducibility and Repository Requirements

Before proposing implementation, inspect:

- `007_tests/014_ml_nowcast/README.md`
- `007_tests/014_ml_nowcast/RULES.md`
- `007_tests/014_ml_nowcast/scripts/run048_feature_registry.py`
- `007_tests/014_ml_nowcast/scripts/run048_snapshot.py`
- `007_tests/014_ml_nowcast/scripts/run048_evaluation.py`
- `007_tests/014_ml_nowcast/scripts/run048_pipeline.py`
- `007_tests/014_ml_nowcast/scripts/04_conformal.py`
- relevant `run_048` tests, execution guides, manifests, and completed Tuku outputs
- `D:/112_PROJECT_002/Manuscript_reduced/sections/dataset003.tex`
- `D:/112_PROJECT_002/Manuscript_reduced/sections/methods004.tex`

The implementation plan produced afterward must:

- follow existing numeric script prefixes and snake-case folder names;
- place new outputs under a clearly separated `run_048` supplement or another location justified from current conventions;
- never overwrite frozen outputs;
- add tests for temporal leakage, endpoint aggregation, hidden-target exclusion, uncertainty calibration, output provenance, and result reproducibility;
- provide exact commands for synthetic validation, production execution, plot-only regeneration, and hash verification;
- account for the current dirty worktree and stage only files created or intentionally modified for this experiment;
- avoid changes to unrelated manuscript or regional-analysis workflows.

## 8. Required Deliverable from the Next Assistant

The next assistant should not begin by coding. Its first deliverable should be a decision-complete implementation plan containing:

1. a short diagnosis of the current `run_048` behavior and the exact mismatch with sparse field sampling;
2. a proposed temporal evaluation design and justification;
3. proposed valid baselines and a selection/reporting rule;
4. the monthly uncertainty method and its assumptions;
5. the cumulative 6-month and 12-month evaluation definitions;
6. the existing components to reuse and the new components genuinely required;
7. the proposed folder, file, and artifact organization following repository conventions;
8. test cases, expected output schemas, execution commands, and acceptance criteria;
9. explicit scientific claims the outputs can support and claims they cannot support.

Any unresolved scientific choice should be brought back for discussion before implementation. The assistant should challenge assumptions that are inconsistent with the data or the physical meaning of MLCW observations rather than silently choosing the easiest coding path.
