# Technical Plan for Discussion Evidence Q11--Q13

**Prepared:** 2026/08/21 20:36:17  
**Submission deadline:** 2026/08/23  
**Purpose:** Produce a small, traceable evidence package that can support the Discussion without changing the approved manuscript or the frozen main-model results.

## Task Briefing

The technical assistant must complete three linked analyses. Q11 tests whether cGNSS and GWL provide predictive information beyond seasonal repetition in the delayed-delivery design of Section 4.1. Q12 compares Section 4.1 with the 6- and 12-month reduced-measurement scenarios over the same calendar months. Q13 compares initial MLCW histories of 3, 5, and 8 years within each reduced-measurement schedule.

The task produces evidence for author review. It must not edit any LaTeX manuscript file, regenerate the approved main results, or change the model used in Sections 4.1--4.3. Q11 fits comparison models only. Q12 and Q13 read existing frozen outputs and perform no model fitting.

## Author Decisions Already Fixed

1. The active station is TUKU, with sections S1--S6.
2. The active dataset is `20260718_run048_v1`.
3. The main model uses the frozen 38-variable list in the current feature manifest.
4. Q11 may fit comparison models, but it must not replace or modify the full 38-variable model.
5. Q12 and Q13 must use the existing calendar-aligned outputs.
6. Results must be stored separately and documented so another agent can trace every source and calculation.
7. No result may be inserted into Results or Discussion without separate author approval.
8. The hypothetical sinusoidal challenge is a pre-submission stress test. No reviewer has yet requested it.
9. The deadline favors a compact numerical package. Do not create manuscript figures in this task.

## Repository and Source Paths

### Analysis repository

`D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3`

### Canonical code and tests

- Script directory  
  `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts`
- Test directory  
  `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\tests`
- Core fitting functions  
  `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\run048_evaluation.py`
- Calendar-aligned Section 4.1 wrapper  
  `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\run048_tuku_p0_level1a_calendar_aligned_delayed_delivery.py`
- Calendar-aligned Section 4.2 wrapper  
  `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\run048_tuku_p0_level1a_calendar_aligned_sparse_interval.py`

### Current frozen evidence package

`D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results003_calendar_aligned_38predictors`

Required files within that package are listed below.

- Frozen variable list  
  `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results003_calendar_aligned_38predictors\feature_manifest.json`
- Source provenance  
  `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results003_calendar_aligned_38predictors\source_provenance.json`
- Decision log  
  `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results003_calendar_aligned_38predictors\DECISIONS.md`
- Section 4.1 monthly estimates  
  `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results003_calendar_aligned_38predictors\results\sec4_1\results\predictions.parquet`
- Section 4.1 run provenance  
  `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results003_calendar_aligned_38predictors\results\sec4_1\results\run_provenance.json`
- Section 4.2 monthly estimates  
  `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results003_calendar_aligned_38predictors\results\sec4_2\results\sec4_2_monthly_predictions.parquet`
- Section 4.2 endpoint errors  
  `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results003_calendar_aligned_38predictors\results\sec4_2\results\sec4_2_endpoint_errors.csv`
- Section 4.2 calendar checks  
  `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results003_calendar_aligned_38predictors\results\sec4_2\results\calendar_checks.json`

### Methodological reference only

The older audit below may be read to understand previous shared-period and seasonal-reference calculations. It must not be used as a numerical source because it reads superseded outputs.

`D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results002\previews\sec4_2_reduced_frequency\audit_outputs\audit03_shared_period_and_pairwise.py`

### Manuscript context, read-only

- Methods  
  `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\methods006.tex`
- Results  
  `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\results004.tex`
- Discussion draft  
  `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\discuss003.tex`
- Author dialogue  
  `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\planning\20260821_dialogue.md`

## New Output Location

Create one self-contained output folder and write nothing outside it except the new canonical scripts and test file specified later.

`D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results003_calendar_aligned_38predictors\discussion_evidence_20260821`

Required structure follows.

```text
discussion_evidence_20260821/
|-- README.md
|-- RUN_LOG.md
|-- source_provenance.json
|-- artifact_manifest.json
|-- q11_predictor_information/
|   |-- configuration_manifest.json
|   |-- predictions.parquet
|   |-- performance_by_configuration_and_section.csv
|   |-- paired_differences_from_seasonal_reference.csv
|   |-- selected_sinusoidal_terms_by_fold.csv
|   `-- Q11_INTERPRETATION_REPORT.md
|-- q12_reduced_frequency_reference/
|   |-- matched_monthly_rows.parquet
|   |-- paired_metric_differences.csv
|   |-- paired_endpoint_differences.csv
|   `-- Q12_INTERPRETATION_REPORT.md
|-- q13_initial_history/
|   |-- matched_history_rows.parquet
|   |-- pairwise_history_differences.csv
|   `-- Q13_INTERPRETATION_REPORT.md
`-- validation/
    |-- validation_report.json
    |-- validation_report.md
    `-- advisor_review.md
```

Every report must distinguish observed numerical results from interpretation. Reports must not draft manuscript prose or recommend manuscript edits.

## New Code Files

Create these files with informative module docstrings and command-line help.

1. `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\run048_build_q11_predictor_information_evidence.py`
2. `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\run048_build_q12_q13_comparison_evidence.py`
3. `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\run048_validate_discussion_evidence.py`
4. `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\tests\test_run048_discussion_evidence.py`

Do not modify `run048_evaluation.py`, the three existing calendar-aligned scripts, any checkpoint, or any file under `manuscript_results001`, `manuscript_results002`, or the existing `results/sec4_1`, `results/sec4_2`, and `results/sec4_3` folders.

## Work Package Q11

### Scientific question

Determine whether cGNSS and GWL improve estimates beyond seasonal repetition when every comparison uses the same Section 4.1 folds, months, sections, and MLCW observations.

### Common evaluation design

Reuse the exact delayed-delivery design from `run048_tuku_p0_level1a_calendar_aligned_delayed_delivery.py`.

- Station must equal `TUKU`.
- Sections must equal `S1` through `S6`.
- The rolling evaluation block must remain six months.
- The minimum initial record must remain 36 months.
- The first complete evaluation block must begin in 05/2013.
- The comparison must contain 23 complete cycles and 138 estimates per section.
- All configurations must use identical calibration and evaluation rows.
- Construct the complete-case dataset once using the target and all 38 variables, then pass the same rows into every comparison. A smaller variable set must not gain extra rows merely because it has fewer missing values.
- Predictor centering and scaling must be calculated within each calibration fold only.
- Evaluation-period MLCW values must never be used to select variables, tune a sinusoid, scale predictors, or fit a model.

### Required comparison configurations

#### 1. Seasonal reference model

Use these five existing variables.

```text
month_sin
month_cos
month2_sin
month2_cos
is_dry_season
```

This configuration directly tests whether annual and semiannual repetition can account for the reported performance.

#### 2. cGNSS plus seasonal variation

Use the five seasonal variables and these four cGNSS variables.

```text
dS_total
d2S_total
dS_total_lag1
dS_total_lag3
```

#### 3. GWL plus seasonal variation

Use the five seasonal variables and every GWL-derived variable from the frozen 38-variable manifest. This includes the target-section, lagged, trailing-mean, cross-section, magnitude, acceleration, and dry-season interaction terms. The script must derive the GWL list by subtracting the four cGNSS names and five seasonal names from the frozen manifest and assert that this list contains 29 variables. It must then combine those 29 variables with the five seasonal variables, write the resulting 34-variable configuration to `configuration_manifest.json`, and assert the final count.

#### 4. Full observational model

Use all 38 names from `feature_manifest.json` without reordering or alteration. This is the current main model and serves as the comparison reference. Its predictions must match the frozen Section 4.1 predictions within `1e-8` for `y_true`, `y_pred`, and `y_std`.

#### 5. Training-selected sinusoidal control

This diagnostic addresses the hypothetical claim that a few fabricated sinusoidal series could fit MLCW without cGNSS or GWL.

Create a fixed candidate bank from calendar time using sine and cosine pairs with integer periods from 3 through 36 months. The bank must be generated without reading MLCW. Within each section and fold, rank individual candidate terms by absolute Pearson correlation using calibration rows only and select the five highest-ranked terms. Fit Bayesian ridge regression with those five terms. Save every selected period, function type, correlation, section, and fold to `selected_sinusoidal_terms_by_fold.csv`.

No evaluation-period target may influence candidate generation or selection. This control is diagnostic only. It must not be described as a physical model, and its results must not be combined with those of the four predefined configurations.

### Optional elementary seasonal reference

Also calculate a month-of-year mean from each calibration fold and section, then apply it to the corresponding evaluation months. If a calendar month is absent from a calibration fold, use that fold and section's overall calibration mean. This reference requires no Bayesian ridge fitting and receives no posterior interval. Report its point-estimate errors separately so missing interval statistics cannot be mistaken for failed calculations.

### Q11 metrics

For every configuration and depth section, report the following over the 23 complete cycles.

- Number of estimates
- $R^2$
- MAE in mm/month
- RMSE in mm/month
- Mean signed error using estimated minus observed
- Empirical coverage and mean width for the Bayesian posterior predictive intervals when available

Calculate paired differences using the same section-month rows. The primary contrasts are listed below.

```text
full observational model minus seasonal reference
cGNSS plus seasonal variation minus seasonal reference
GWL plus seasonal variation minus seasonal reference
full observational model minus cGNSS plus seasonal variation
full observational model minus GWL plus seasonal variation
training-selected sinusoidal control minus seasonal reference
```

For MAE, negative values mean the first configuration has smaller error. For RMSE, recompute RMSE within every resampled dataset before subtracting. Do not average monthly RMSE differences.

Use 2,000 paired block-bootstrap resamples with fixed seed `20260821`. One sampled block must contain one complete six-month evaluation cycle across all six sections. Report the 2.5th and 97.5th percentiles as a 95% uncertainty interval. These intervals describe stability across observed evaluation cycles. Do not call them proof of equivalence or causal contribution.

### Q11 interpretation boundary

- Better performance than the seasonal reference supports added predictive information under this Tuku design.
- It does not establish a causal mechanism.
- Similar performance means the current evidence does not separate the observational variables from seasonal repetition.
- Worse performance must be reported without concealment.
- Differences among cGNSS-only, GWL-only, and full configurations are not additive because their information can overlap.

## Work Package Q12

### Scientific question

Measure how monthly and endpoint errors change when the MLCW information available to the model is reduced, using Section 4.1 as the reference over exactly the same months.

### Required matched data

- Common evaluation period must equal 05/2018 through 04/2024.
- Section 4.1 must contribute 72 months for each of six sections, giving exactly 432 section-month rows.
- Each Section 4.2 scenario must be filtered to `record_role == "evaluation"` and matched to Section 4.1 by `section` and `datetime`.
- Perform the comparison separately for six scenarios formed by measurement intervals of 6 and 12 months and initial histories of 36, 60, and 96 months.
- Assert exact equality of the observed MLCW value after matching. Stop if any difference exceeds `1e-10`.

### Monthly comparisons

For each scenario, calculate the Section 4.2 minus Section 4.1 difference in the following quantities.

- MAE
- RMSE
- Mean signed error
- Empirical 90% coverage
- Mean posterior interval width

Use the interval boundaries of each Section 4.2 schedule as bootstrap blocks. A six-month block must contain all six months and all six sections. A twelve-month block must contain all twelve months and all six sections. Use 2,000 paired resamples, seed `20260821`, and percentile limits of 2.5 and 97.5%.

### Endpoint comparisons

For every Section 4.2 interval, sum the signed monthly errors from Section 4.1 over the identical section and half-open calendar interval `[interval_start, interval_end)`. Compare its absolute cumulative error with the absolute `endpoint_error` from Section 4.2.

Recompute each Section 4.2 endpoint error from `sec4_2_monthly_predictions.parquet` and verify agreement with `sec4_2_endpoint_errors.csv` within `1e-10` before using it. Do not compare a six-month endpoint with a twelve-month endpoint.

Report the paired difference in absolute endpoint error, separately for each schedule and initial-history length. Bootstrap complete endpoints while preserving all six sections within a sampled endpoint.

## Work Package Q13

### Scientific question

Determine whether increasing the initial monthly MLCW record from 3 to 5 or 8 years produces a consistent change within the same reduced-measurement schedule.

### Required comparisons

Within each 6- and 12-month schedule, match rows by section and datetime and calculate these contrasts.

```text
5 years minus 3 years
8 years minus 3 years
8 years minus 5 years
```

All scenarios already share 05/2018--04/2024, but the script must verify this rather than assume it. It must also verify identical observed MLCW values across all three history lengths.

Calculate paired differences for MAE, RMSE, mean signed error, empirical coverage, mean interval width, and absolute endpoint error. Use the same paired block-bootstrap procedure and fixed seed as Q12.

Interpret negative MAE or RMSE differences as lower error for the longer history. An uncertainty interval crossing zero means the observed direction is not stable across resampled intervals. It does not establish equivalence. Do not define 3, 5, or 8 years as sufficient because no independent operational threshold has been established.

## Validation Gates

The technical assistant must stop and report the failure before interpretation if any gate below fails.

1. **Source integrity**  
   Record SHA-256 hashes before execution for the feature manifest, both source parquet files, the endpoint CSV, all three run-provenance files, and the frozen Section 4.1 predictions. Verify the same hashes after execution.

2. **Full-model parity**  
   The Q11 full 38-variable configuration must match the existing Section 4.1 predictions within `1e-8`.

3. **Calendar identity**  
   Q11 must contain 23 complete cycles and 138 estimates per section. Q12 and Q13 must use 05/2018--04/2024 and 432 matched section-month rows per scenario.

4. **Target identity**  
   Matched conditions must have identical MLCW observations within `1e-10`.

5. **Training-only construction**  
   Seasonal means, sinusoidal selection, scaling, and model fitting must use calibration rows only. Add a test that mutates evaluation targets and confirms that Q11 estimates and selected sinusoidal terms remain unchanged.

6. **Determinism**  
   Repeat each new script into a temporary sibling folder and compare all numeric outputs. Maximum absolute difference must equal zero, except for timestamps and absolute output paths. Delete only the temporary determinism folder after confirming its resolved path lies under the new discussion-evidence root.

7. **No forbidden changes**  
   Confirm zero modified or deleted files under `checkpoints`, `manuscript_results001`, `manuscript_results002`, and the existing `results/sec4_1`, `results/sec4_2`, and `results/sec4_3` folders. Confirm that all `.tex` files in `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1` remain byte-identical.

8. **Artifact traceability**  
   `artifact_manifest.json` must list relative path, byte size, SHA-256, creation time, source files, and generating script for every output. `RUN_LOG.md` must record the exact commands, Python executable, environment versions, Git commit, start/end times, warnings, and failures.

9. **Independent review**  
   Ask the technical advisor to review fold construction, the training-only sinusoidal selection, paired matching, endpoint aggregation, bootstrap blocks, sign conventions, and interpretation boundaries. Save the questions and the advisor's response in `validation/advisor_review.md`. Resolve factual or mathematical errors before finalizing; list judgment calls without silently changing the agreed scope.

## Execution Commands

Use the proven Python executable below if `conda run` is unavailable.

```powershell
$python = "D:\Programs\miniconda3\Library\envs\fafalab2\python.exe"
$scripts = "D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts"
$output = "D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results003_calendar_aligned_38predictors\discussion_evidence_20260821"

& $python "$scripts\run048_build_q11_predictor_information_evidence.py" --output-root $output
& $python "$scripts\run048_build_q12_q13_comparison_evidence.py" --output-root $output
& $python "$scripts\run048_validate_discussion_evidence.py" --output-root $output
& $python -m pytest "D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\tests\test_run048_discussion_evidence.py" -q
```

Before execution, each new script must support `--help`, reject output paths under frozen folders, and refuse to overwrite an existing finalized evidence package. Development reruns may write only to a clearly named temporary sibling under `discussion_evidence_20260821`.

## Completion Report

The technical assistant must return a concise report containing the following items.

1. Pass or fail for every validation gate.
2. Exact files created and modified.
3. Q11 comparison summary by section, with emphasis on whether the full model improves beyond the seasonal reference.
4. Q12 changes relative to Section 4.1 for every reduced-measurement scenario.
5. Q13 pairwise changes among 3-, 5-, and 8-year initial histories.
6. Results that support a clear statement and results that require caution.
7. Any discrepancy that prevents manuscript use.
8. Confirmation that no manuscript or frozen result file was changed.

The report must not revise `results004.tex`, `discuss003.tex`, or any other manuscript file. The author and writing assistant will decide later which results belong in the Discussion.

## Rollback

This task adds only four code files and one new output folder. If the analysis is rejected, remove only the four new code files and the resolved folder below after verifying their absolute paths.

`D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results003_calendar_aligned_38predictors\discussion_evidence_20260821`

Never delete or reset any pre-existing result, checkpoint, manuscript, or unrelated worktree change during rollback.
