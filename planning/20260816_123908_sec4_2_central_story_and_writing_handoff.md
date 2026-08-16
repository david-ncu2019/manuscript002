# Section 4.2 Central Story and Writing Handoff

## Task briefing

Prepare a reviewable Results draft that contains the complete current Section 4.1 followed by a newly written Section 4.2 on reduced MLCW measurement frequency. Work only in the temporary LaTeX file specified below. Copy Section 4.1 from the active Results file for context, then replace the Section 4.2 placeholder with connected, evidence-led prose that follows the central story and key-message sequence in this handoff. Use only the existing `without_lithology` outputs for Section 4.2. These outputs were produced from 35 input variables and must not be regenerated. Treat the existing 36-variable outputs and figures only as audit or visual-style references. Do not invent values, reuse superseded values, interpret results as universally applicable, or edit the active manuscript, Methods, Discussion, or `main.tex`.

## Execution lock

This is a writing and display-preparation task. Do not fit, refit, recalibrate, or rerun any model. Do not rebuild the feature table or rerun upstream preprocessing. Plotting, table-building, or summary scripts may be run only when inspection confirms that they read the frozen `without_lithology` outputs listed in this handoff and do not call any model-fitting code. Derived figures and tables must preserve the frozen numerical values.

The active Section 4.1 evidence and the Section 4.2 `without_lithology` evidence do not have identical feature provenance. Therefore, do not make a numerical Section 4.1-versus-Section 4.2 comparison, do not state that both sections used the same fitted feature set, and do not report a predictor count in the Results prose or tables.

## Files the writing assistant may and may not edit

### Sole writing target

Create and write only this file:

`D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\results003_sec4_1_4_2_temp.tex`

The temporary file must contain:

1. The `\section{Results}` heading and opening currently present in the active Results file.
2. The complete current Section 4.1, copied for reading context. In this temporary copy only, replace the sentence `Each section model used 35 input variables, but presenting every coefficient would make comparisons among the depth sections difficult.` with `The section models included multiple input variables, but presenting every coefficient would make comparisons among the depth sections difficult.` Do not otherwise rewrite or delete Section 4.1 content.
3. A newly drafted Section 4.2 under the existing heading and label:

```latex
\subsection{Estimation under reduced MLCW measurement frequency}
\label{subsec:results_reduced_frequency}
```

4. No Section 4.3 content. End the temporary file after the completed Section 4.2.

### Read-only manuscript context

- Active Results source to copy and read:
  `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\results003.tex`
- Experimental design for Section 4.2:
  `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\methods005.tex`
- Discussion boundary and deferred interpretation:
  `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\discuss003.tex`
- Dataset terminology and measurement definitions:
  `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\dataset003.tex`

Do not modify any of these read-only files. Do not modify `main.tex` to include the temporary file unless the author later gives explicit permission.

## Central story

Section 4.1 establishes the reference condition. Monthly MLCW measurements still exist, but finalized monthly records are temporarily unavailable. Monthly GWL and cGNSS observations are used to estimate the missing monthly deformation increments. When the finalized MLCW records become available, every monthly estimate can be compared with its corresponding observation and the model can be updated from the complete monthly record.

Section 4.2 examines a more restrictive condition. MLCW measurements are collected only at the endpoints of 6- or 12-month intervals. The measurement at an endpoint gives cumulative deformation over the interval but does not reveal how that deformation was distributed among the intervening months. Monthly GWL and cGNSS observations remain available, so the model uses them to estimate the monthly deformation increments between successive MLCW measurements. At each endpoint, only the cumulative MLCW observation is added to the calibration record.

The central question is:

> When MLCW monitoring provides one cumulative deformation observation every 6 or 12 months, can monthly GWL and cGNSS observations support useful estimates of the intervening monthly deformation increments at Tuku?

The section answers this question at two scales. Monthly errors show whether the model recovers the distribution of deformation within each interval. Endpoint errors show whether the sum of the monthly estimates agrees with the cumulative MLCW observation. Initial monthly records of 3, 5, and 8 years show how performance changes when the model begins reduced-frequency operation with different amounts of historical MLCW information.

The intended resolution is site-specific and conditional. The section may state how closely the monthly estimates followed the observations and how endpoint errors changed among the six tested scenarios at Tuku. It must also report any shortfall in the empirical coverage of the nominal 90% Bayesian posterior predictive intervals. The section must not compare these errors numerically with Section 4.1, claim that reduced-frequency monitoring works at every station, state that 3 years is universally sufficient, or imply that MLCW monitoring can be discontinued.

## Story sequence for Section 4.2

Write Section 4.2 as one connected sequence rather than as independent result statements:

1. Move from the delayed-delivery reference in Section 4.1 to the harder reduced-frequency condition.
2. Show what happened to monthly estimates under the 3-year initial record for both 6- and 12-month measurement intervals.
3. Quantify all six scenarios using one compact main-text table.
4. Describe how errors changed as the initial record increased from 3 to 5 and 8 years. Report both full-period results and a fair shared-period comparison, but do not confuse their meanings.
5. Report posterior predictive interval coverage as a distinct result. Good point estimates do not imply adequate interval coverage.
6. End with a bounded factual resolution at Tuku and transfer interpretation to the Discussion.

## Key message 1: The reduced-frequency condition is harder than delayed delivery

### Scientific point

Section 4.1 eventually receives all monthly MLCW records. Section 4.2 receives only one cumulative MLCW observation at the end of each measurement interval. The model must therefore estimate the monthly distribution of deformation without using the hidden monthly MLCW values for calibration or updating.

### Required sentence building blocks

Build one opening paragraph from the following functions:

1. **Known topic:** refer to the delayed-delivery condition already established in Section 4.1.
2. **Contrast:** state that reduced-frequency monitoring provides only cumulative endpoint observations rather than complete monthly records.
3. **Continuity:** state that monthly GWL and cGNSS observations remain available.
4. **Evaluation target:** state that the analysis evaluates the intervening monthly estimates and their accumulated endpoint total.

Do not repeat the equations or the full update algorithm from Methods. Do not explain why the provider might reduce measurements. Results should begin from the tested condition, not from operational speculation.

### Display requirement

No separate display is needed for this message. Refer to the experimental-design figure in Methods only if the reference prevents a genuine misunderstanding.

### Evidence source

- Methods design and definitions:
  `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\methods005.tex`
- Audited algorithm description:
  `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results002\previews\sec4_2_reduced_frequency\002_sec4_2_reduced_frequency_calculation_and_data_audit_report.md`

## Key message 2: Monthly estimates remain the primary quantity being evaluated

### Scientific point

The endpoint measurement supplies only cumulative deformation. The model still estimates one deformation increment for each month. Historical monthly MLCW observations hidden from model fitting are used only for retrospective evaluation of those monthly estimates.

### Required sentence building blocks

Build the paragraph around the 3-year initial record because it uses the shortest initial monitoring history examined in this study:

1. Introduce the 3-year scenario as the visual example, not as a proven minimum requirement.
2. Describe the observed agreement and disagreement between monthly estimates and MLCW observations across S1-S6.
3. Compare the visible behavior under 6- and 12-month measurement intervals.
4. End by identifying the section-level pattern that the quantitative table will test across all six scenarios.

The prose must interpret the plotted physical quantities, not explain colors, markers, line styles, or panel arrangement. Put essential visual definitions in the figure captions.

### Main-text figure requirements

Include both measurement intervals in the main-text draft so the author can judge the resulting length.

- Figure A: 3-year initial record with 6-month MLCW measurement intervals, showing S1-S6.
- Figure B: 3-year initial record with 12-month MLCW measurement intervals, showing S1-S6.

Both figures must follow the approved Section 4.1 visual language. They must use the frozen `without_lithology` predictions. Existing figures listed below are layout and style references only because they were generated from the superseded full-feature results.

Style-reference folder:

`D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results002\previews\sec4_2_reduced_frequency\main_text`

Existing style-reference files:

- `fig_reduced_frequency_6month_3year_s1_s3.pdf`
- `fig_reduced_frequency_6month_3year_s4_s6.pdf`
- `fig_reduced_frequency_12month_3year_s1_s3.pdf`
- `fig_reduced_frequency_12month_3year_s4_s6.pdf`

Display script that may be used only after confirming that it reads the frozen `without_lithology` predictions and does not fit a model:

`D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results002\build_sec4_2_visual_package.py`

Expected manuscript destinations after technical verification and author approval:

- `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\figures\fig_results_reduced_frequency_6month_3year.pdf`
- `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\figures\fig_results_reduced_frequency_12month_3year.pdf`

Do not copy or cite the existing style-reference PDFs as final evidence. If the display script does not satisfy the execution lock, do not run it. In that case, leave clearly labeled figure placeholders in the temporary draft and report the blockage to the author.

## Key message 3: All six scenarios must be quantified compactly

### Scientific point

The 3-year figures illustrate model behavior, but the text must report results for all combinations of initial record length and measurement interval:

- 3, 5, and 8 years of initial monthly MLCW observations;
- 6- and 12-month MLCW measurement intervals.

### Required sentence building blocks

1. State the six-scenario comparison without repeating the Methods procedure.
2. Report the overall range of monthly MAE and RMSE across the six scenarios.
3. Report whether mean signed errors indicate systematic overestimation or underestimation.
4. Report endpoint MAE as the accumulated-scale result.
5. Identify the lowest- and highest-error depth sections only when this helps readers understand a depth-dependent pattern.
6. Lead into the initial-record comparison rather than ending with a list of metrics.

### Main-text table requirement

Use one compact six-row table:

| Measurement interval | Initial record | Monthly MAE | Monthly RMSE | 90% coverage | Endpoint MAE |
|---|---|---|---|---|---|
| 6 months | 3 years | verified value | verified value | verified value | verified value |
| 6 months | 5 years | verified value | verified value | verified value | verified value |
| 6 months | 8 years | verified value | verified value | verified value | verified value |
| 12 months | 3 years | verified value | verified value | verified value | verified value |
| 12 months | 5 years | verified value | verified value | verified value | verified value |
| 12 months | 8 years | verified value | verified value | verified value | verified value |

The table reports pooled Tuku results. Put sample counts in the caption if they are constant within a comparison; do not repeat the same count in every row. Full monthly and endpoint MAE, RMSE, mean signed error, interval width, and coverage by S1-S6 belong in Supplementary Materials.

### Approved frozen data sources for Section 4.2

Use the columns explicitly named `without_lithology` in these files:

- Full-period and shared-period monthly and endpoint summaries:
  `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results002\sec4_2_lithology_ablation_summary.csv`
- Monthly observations, predictions, predictive standard deviations, and 90% bounds:
  `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results002\sec4_2_lithology_ablation_monthly_predictions.parquet`
- Endpoint errors:
  `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results002\sec4_2_lithology_ablation_endpoint_errors.csv`
- Feature-set definition, provenance, parity checks, and bootstrap details:
  `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results002\sec4_2_lithology_ablation_manifest.json`

Column-selection rule:

- Use `mae_without_lithology`, `rmse_without_lithology`, `mean_signed_error_without_lithology`, `coverage_90_without_lithology`, and `mean_width_90_without_lithology` from the summary CSV.
- Use `y_predicted_without_lithology`, `predictive_std_without_lithology`, `lower_90_without_lithology`, and `upper_90_without_lithology` from the monthly Parquet.
- Do not use any corresponding `full_features` column in manuscript prose, tables, or final figures.

## Key message 4: Initial record length must be compared without hiding the calendar difference

### Scientific point

Full-period results describe each operational scenario over all months available after its initial calibration period. These periods differ among the 3-, 5-, and 8-year scenarios. Shared-period results compare the three models over the same final calendar months and therefore provide the fairer descriptive comparison of initial record length.

### Required sentence building blocks

1. Report full-period results first because they describe the complete output of each scenario.
2. State that the 3-, 5-, and 8-year scenarios cover different full evaluation periods.
3. Report pooled shared-period MAE for the three initial record lengths under each measurement interval.
4. Describe only the direction and magnitude of change.
5. Do not conclude that 3 years is sufficient, optimal, or a minimum monitoring requirement.

### Display requirement

Keep the main six-row table focused on full-period results. Report the pooled shared-period comparison in prose. Place full shared-period results by S1-S6 in Supplementary Materials.

### Data source

Use rows with `evaluation_scope = full_period` and `evaluation_scope = shared_period` from:

`D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results002\sec4_2_lithology_ablation_summary.csv`

Use only the `without_lithology` metrics.

## Deferred comparison with Section 4.1

A direct numerical comparison between the endpoint errors in Sections 4.1 and 4.2 is outside this writing task because their current frozen outputs do not have identical feature provenance. The existing reference-comparison reports and scripts may be read as internal audit material, but they must not be rerun, quoted, or used as manuscript evidence. Section 4.2 should report endpoint errors only within its six reduced-frequency scenarios.

## Key message 5: Point accuracy and interval coverage are separate findings

### Scientific point

MAE and RMSE describe the distance between monthly estimates and observations. Empirical coverage describes how often observations fall inside the nominal 90% Bayesian posterior predictive intervals. Accurate point estimates do not guarantee adequate coverage.

### Required sentence building blocks

1. Report coverage across the six scenarios after reporting point errors.
2. Identify scenarios where empirical coverage fell below the nominal 90% level.
3. Describe this as undercoverage, not as failure of the point estimates.
4. Do not call the intervals confidence intervals or conformal intervals.
5. End by preparing the bounded resolution rather than explaining the cause of undercoverage.

### Data sources

- Coverage and interval width:
  `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results002\sec4_2_lithology_ablation_summary.csv`
- Monthly predictive bounds:
  `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results002\sec4_2_lithology_ablation_monthly_predictions.parquet`
- Audit correction concerning interval interpretation:
  `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results002\previews\sec4_2_reduced_frequency\004_a_sec4_2_reduced_frequency_audit_erratum.md`

## Key message 6: End with a bounded Tuku result

### Scientific point

The section should resolve the tested question without extending the finding beyond the evidence. The result concerns monthly deformation estimation at Tuku under the six scenarios examined. It does not establish universal applicability or justify ending MLCW monitoring.

### Required sentence building blocks

1. State the observed result at Tuku.
2. Qualify the result with the interval-coverage finding.
3. Transfer practical meaning, possible mechanisms, site dependence, and limitations to the Discussion through a direct cross-reference.

### Permitted resolution pattern

Use this structure only after replacing its factual components with verified `without_lithology` results:

> At Tuku, monthly deformation estimates [report the verified agreement pattern] when cumulative MLCW measurements were collected at 6- or 12-month intervals. Endpoint errors [report the verified pattern among the six scenarios], whereas empirical coverage of the nominal 90% posterior predictive intervals [report the verified coverage pattern]. These results describe the tested Tuku scenarios; their practical implications and limits are considered in `\Cref{sec:discussion}`.

Do not use the bracketed wording as a manuscript placeholder. Draft the sentence only when all values have been verified.

## Writing-style requirements

Apply the project writing rules from:

- `D:\112_PROJECT_002\.agents\skills\david-writing-styles\rules\style.md`
- `D:\112_PROJECT_002\.agents\skills\david-writing-styles\rules\sections.md`
- `D:\112_PROJECT_002\.agents\skills\david-writing-styles\rules\domain.md`

Follow these requirements throughout the draft:

1. Write for hydrogeology and land-subsidence researchers who do not know the Tuku monitoring system or this pipeline.
2. Keep one controlling point per paragraph.
3. Begin paragraphs with the result or comparison they develop.
4. Move from known information to new information. Use the end of one paragraph to create the topic of the next.
5. Keep subjects close to their verbs and place the important result in the stress position.
6. Use transitions only when they state a real relationship such as contrast, sequence, or qualification.
7. Prefer plain scientific English over machine-learning jargon.
8. Use `monthly deformation estimate`, `monthly deformation increment`, `cumulative MLCW observation`, `measurement interval`, `initial record`, and `Bayesian posterior predictive interval` consistently.
9. Do not use first-person pronouns.
10. Do not use `retain`, `obscure`, em dashes, or decorative synonyms.
11. Do not explain simple arithmetic for the reader.
12. Round manuscript values to three digits after the decimal point unless a percentage or interval requires a different precision to prevent misrepresentation.
13. Distinguish factual reporting in Results from interpretation reserved for Discussion.

## Claims that are not permitted

Do not write or imply any of the following:

- Three years of initial monitoring is sufficient, optimal, or universally adequate.
- Reduced-frequency monitoring produces equivalent performance to monthly MLCW monitoring.
- MLCW measurements can be discontinued.
- The Tuku result applies to other stations or all aquifer systems.
- Lithology is physically unimportant.
- A narrow or visually close estimate proves reliable uncertainty.
- The posterior predictive intervals are confidence intervals or conformal intervals.
- The complete upstream preprocessing pipeline has been proven temporally causal.

Other-station robustness results are private technical checks and must not appear in this manuscript draft.

## Audit and provenance sources

Use these files to understand the evidence boundary and avoid repeating corrected interpretations:

- Main Section 4.2 audit:
  `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results002\previews\sec4_2_reduced_frequency\002_sec4_2_reduced_frequency_calculation_and_data_audit_report.md`
- Audit corrections:
  `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results002\previews\sec4_2_reduced_frequency\004_a_sec4_2_reduced_frequency_audit_erratum.md`
- Corrected technical report:
  `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results002\previews\sec4_2_reduced_frequency\004_c_sec4_2_reduced_frequency_correction_report.md`
- Plain-language correction and ablation summary:
  `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results002\previews\sec4_2_reduced_frequency\005_sec4_2_corrections_and_lithology_ablation_summary_plain.md`
- Frozen-pipeline temporal leakage audit:
  `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\tuku_causal_preprocessing_audit\results\TUKU_CAUSAL_PREPROCESSING_AUDIT_REPORT.md`

## Completion checklist for the writing assistant

Before returning the temporary LaTeX draft, confirm all of the following:

- The draft exists only at `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\results003_sec4_1_4_2_temp.tex`.
- Section 4.1 is complete and differs from `results003.tex` only by the approved neutral replacement of its predictor-count sentence.
- Section 4.2 follows the six-key-message sequence above.
- Both 6- and 12-month results are presented.
- All 3-, 5-, and 8-year scenarios appear in prose and the compact main table.
- Main figures show the 3-year scenario for both measurement intervals.
- Every numerical result comes from a frozen `without_lithology` field listed in this handoff.
- No numerical value from the superseded full-feature reference comparison appears in the draft.
- No numerical Section 4.1-versus-Section 4.2 comparison appears in the draft.
- No predictor count appears in the Results prose, captions, or tables.
- No model, feature table, or upstream preprocessing step has been rerun.
- Point accuracy and interval coverage are reported separately.
- Per-section details that do not advance the main story are assigned to Supplementary Materials rather than expanded in the main text.
- No Discussion interpretation, universal claim, operational recommendation, or other-station result appears in Section 4.2.
- No file outside the sole writing target has been modified.
