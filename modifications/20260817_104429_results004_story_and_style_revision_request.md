# Revision request for the Results section

## Purpose

Revise `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\results004.tex` so that the Results section reads as a connected scientific story rather than an inventory of model outputs. The numerical results have already been validated. This task concerns the selection, order, and wording of evidence, not new analysis.

The section-level story is the progressive reduction in new MLCW information across three monitoring conditions. The delayed-delivery condition eventually provides complete monthly records. The reduced-frequency condition provides one cumulative measurement every 6 or 12 months. The final condition provides no subsequent MLCW measurement. Each subsection must answer one scientific question arising from that progression.

1. During delayed delivery, how closely did the estimates reproduce the observed monthly deformation increments, and how did performance vary with depth and position within the update cycle?
2. When field measurements became less frequent, did the monthly errors and the error at the next cumulative measurement change with measurement interval or initial-record length?
3. When no later MLCW measurements became available, how did monthly and cumulative errors develop over a common 80-month period?

The Results section must report these patterns and the minimum numerical evidence needed to establish them. Mechanisms, broader meaning, explanations for differences among depth sections, literature comparisons, and limitations belong in `sections/discuss003.tex`, not here.

## Scope and locks

- Prepare one proposed change set for author review before editing the manuscript.
- Do not alter `dataset003.tex`, `studyarea002.tex`, `methods005.tex`, `methods006.tex`, `appendix001.tex`, or `appendix002.tex`.
- Preserve every validated value, unit, sign convention, date, label, cross-reference, table entry, and figure source unless this request explicitly identifies a wording-only change.
- Do not rerun or refit any model.
- Do not add a mechanism, causal explanation, claim of general applicability, comparison with another station, or explanation for why Tuku performed well.
- Keep all reported values to three decimal places.
- Do not use first-person pronouns, em dashes, or reader-facing internal terms such as `pooled`, `calendar-aligned`, `ablation`, `snapshot`, or `38-predictor rerun`.
- Use `across all six depth sections`, `all sections combined`, or `the row labelled All combines...` instead of `pooled`.
- Avoid `accuracy` as a standalone term. Name the actual quantity, such as MAE, RMSE, coverage, or point-estimate performance.
- Keep the figures and tables inside their present subsections. Do not move evidence between Results and Supplementary Materials in this pass.

## Required story pass

### Results opening

The current opening announces the order of presentation but does not tell readers what connects the three subsections. Replace it with a short progression based on the availability of MLCW information. The revised opening should perform the following work without reporting numerical results.

- Establish that the three conditions differ in the availability of new MLCW information.
- Distinguish delayed monthly records, less frequent cumulative measurements, and no subsequent measurements.
- State that the Results examine monthly and cumulative estimation errors under these conditions.

Recommended wording:

> The three monitoring conditions differed in the availability of new MLCW information. Finalized monthly records became available after a temporary delay in one condition. The reduced-frequency condition provided one cumulative measurement every 6 or 12 months, whereas the final condition provided no subsequent MLCW measurement. The following subsections report how monthly and cumulative estimation errors changed across these conditions.

### Section 4.1: delayed MLCW data delivery

The current subsection contains valid evidence, but its opening begins with the experimental schedule, and its coefficient discussion reproduces too many table cells in prose. Revise the subsection around the following arc.

1. Lead with the principal observed pattern. Estimated monthly increments followed the observations more closely in S1--S4 than in S5--S6.
2. Give the evaluation support once. The analysis covered 23 complete cycles and 138 estimates per section.
3. Use the time-series and scatter figures to establish the depth-dependent pattern.
4. Use the performance table to provide only representative evidence. Report the all-section MAE and RMSE, then identify the range or the most relevant contrast among sections. Do not reproduce every minimum and maximum from the table.
5. Report the interval result as a second, distinct finding. State that coverage across all sections was 78.140%, below the nominal 90%, and note only the depth contrast needed to show that the shortfall was not uniform.
6. Keep the month-position result because it answers whether performance worsened as the delay lengthened. Lead with the absence of a monotonic decline, then support it with the observed MAE range and the fact that the largest error occurred in month 2 rather than month 6.
7. Keep the selected-coefficient table for transparency, but replace the three catalogue-like paragraphs that enumerate signs for nearly every section and feature. The prose should identify only the patterns that help readers understand why the table is present.
8. End with the resolved evidence from this condition, not with repeated metadiscourse saying that implications will be discussed later.

Recommended opening:

> During delayed MLCW data delivery, estimated monthly increments followed the observed temporal patterns more closely in S1--S4 than in S5--S6. This comparison covered 23 complete six-month cycles from 05/2013 to 10/2024 and yielded 138 estimates for each depth section. After each cycle, the newly finalized monthly observations expanded the calibration record used for the next cycle (\Cref{fig:results_delayed_cycles}).

Recommended point-error and interval paragraphs:

> The depth contrast visible in the time series and scatter plots was also present in the error statistics (\Cref{tab:delayed_performance_interval}). Across all six depth sections, RMSE was 0.423~mm/month and MAE was 0.279~mm/month. Errors were smaller in S1--S4 than in S5 and S6, with S5 showing the largest RMSE and MAE.
>
> The 90\% Bayesian posterior predictive intervals contained 78.140\% of the observations across all sections, below the nominal level. Coverage varied among sections and reached its lowest value in S6, while S5 had the widest intervals. The depth sections therefore differed in both point-estimate error and interval performance.

Recommended month-position paragraph:

> Monthly estimation errors did not increase steadily with time since the preceding MLCW update (\Cref{tab:delayed_performance_by_month}). MAE ranged from 0.251 to 0.336~mm/month across the six positions, and the largest error occurred in month 2 rather than month 6. The additional time without finalized records was therefore not accompanied by a monotonic decline in monthly performance.

Recommended coefficient introduction:

> The fitted coefficients also varied among depth sections. To summarize these differences without reproducing all model coefficients, \Cref{tab:selected_coefficients} presents 14 variables whose 10th--90th percentile range remained entirely positive or negative in at least one section. This display rule did not affect model fitting and does not establish statistical significance, causal influence, or variable importance.

Recommended replacement for the three coefficient catalogue paragraphs:

> Surface-displacement terms showed the clearest repeated directional patterns across the depth sections. The current increment had a positive coefficient range in S1--S4 and S6, whereas the hydraulic-head terms showed fewer common patterns among sections. Seasonal coefficients also varied with depth, with the dry-season indicator and annual sine component having opposite directions in S6 and the five shallower sections. These results describe fitted associations and are interpreted separately in \Cref{sec:discussion}.

The assistant may adjust this wording for grammar and relay linkage, but must not add explanations for the coefficient patterns.

Table-caption corrections in Section 4.1:

- In `tab:delayed_performance_interval`, replace `Point accuracy` with `Point-estimate performance` or `Point-estimate error and fit statistics`.
- Replace `The row labelled All pools the estimates from the six sections` with `The row labelled All combines estimates from the six sections`.
- Keep the sample count in the caption rather than repeating it in every row.
- Preserve the definitions and units needed to read each table, but remove procedural wording already explained in Methods.

### Section 4.2: less frequent MLCW field measurements

The current subsection repeats too much of the experimental design before stating the result. Reorganize it around one comparison. Monthly errors changed little among the tested schedules and initial-record lengths, but errors at the next cumulative MLCW measurement were larger for the 12-month schedule.

Use this arc:

1. State the principal comparison in the opening sentence.
2. Give only the design reminder needed to interpret the comparison. Monthly hydraulic-head and cGNSS observations remained available, hidden monthly MLCW observations were used only for retrospective evaluation, and every scenario covered 05/2018--04/2024.
3. Keep the 3-year time-series figure as the representative visual example.
4. Let `tab:results_reduced_frequency` remain the primary home for all six scenarios.
5. In prose, report the monthly MAE range and the separate endpoint MAE ranges for the 6- and 12-month schedules. These values establish the main result.
6. State that increasing the initial record from 3 to 8 years did not reduce errors consistently. One representative comparison is enough. Do not narrate all six rows.
7. Report the coverage shortfall in one sentence or one short paragraph. Do not let uncertainty statistics interrupt the main comparison between monthly and endpoint error.
8. End with the observed result, not with `The implications of these findings are considered...`.

Recommended opening:

> Less frequent MLCW field measurements changed the error at the next cumulative observation more clearly than the error in individual monthly estimates. Monthly hydraulic-head and cGNSS observations remained available between MLCW measurements, and the hidden monthly MLCW observations were used only for retrospective evaluation. The 3-, 5-, and 8-year initial records were evaluated over the same 72 months from 05/2018 to 04/2024.

Recommended evidence paragraphs:

> Monthly MAE remained between 0.269 and 0.308~mm/month across the six scenarios (\Cref{tab:results_reduced_frequency}). By contrast, endpoint MAE ranged from 1.405 to 1.542~mm for the 6-month schedule and from 2.470 to 2.738~mm for the 12-month schedule. The longer measurement interval therefore produced larger differences between accumulated monthly estimates and the next cumulative MLCW observation.
>
> Extending the initial record from 3 to 8 years did not reduce error consistently. The 5-year record produced the lowest monthly MAE under both schedules, whereas the 8-year record produced the highest monthly and endpoint MAE. Coverage of the nominal 90\% intervals ranged from 77.778 to 89.352\%, remaining below the nominal level in all six scenarios.

Caption revision for `fig:results_reduced_frequency_3yr`:

- Keep the design facts needed to decode the figure.
- State once that black markers or lines show observations and colored lines show monthly estimates if the visual legend does not make this self-evident.
- Explain that the shaded bands are 90% Bayesian posterior predictive intervals.
- Explain that vertical lines mark months when a new cumulative MLCW field measurement became available for the next update.
- Keep panel (a) and panel (b) descriptions parallel.
- Do not include internal production terms or describe the figure-generation process.

Caption revision for `tab:results_reduced_frequency`:

- Shorten the caption while preserving the common 72-month period, the meaning of monthly and endpoint errors, coverage, and units.
- Keep sample counts only if they help readers distinguish monthly estimates from cumulative endpoints. Do not explain why the schedules have different counts in the Results prose unless that fact is needed to prevent a specific misreading.

### Section 4.3: no subsequent MLCW field measurements

The current subsection begins with a long design reminder and then places three pairs of monthly error values in one sentence. Reorganize it around the distinction between monthly error and cumulative error.

1. Lead with the finding that monthly errors remained within a narrow range among initial-record lengths, whereas cumulative errors separated by depth section over time.
2. Remind readers in one sentence that each model was calibrated once, received no later MLCW measurements, and was evaluated over the same 80 months.
3. Report monthly MAE and RMSE as ranges rather than three separate pairs.
4. Use the figure to show the cumulative-error trajectories and the table to provide exact values at month 80.
5. In the prose, identify only the pattern needed to interpret the displays. S4 had the largest month-80 cumulative error under all three initial-record lengths. The 8-year record reduced the month-80 error in S4--S6 but did not give the smallest error in every section.
6. Remove the sentence claiming that the comparison is `not confounded`. The common-calendar design belongs in Methods; Results only needs to state that the three records were evaluated over the same calendar period.
7. End with the evidence-bounded result. Do not add a mechanism or practical recommendation.

Recommended opening and evidence:

> Without subsequent MLCW measurements, monthly errors remained within a narrow range among the three initial-record lengths, whereas cumulative errors diverged among depth sections over time. Each model was calibrated once and evaluated over the same 80 months from 05/2018 to 12/2024 while monthly hydraulic-head and cGNSS observations remained available. Across all six sections, monthly MAE ranged from 0.257 to 0.293~mm/month and RMSE ranged from 0.406 to 0.432~mm/month.
>
> The cumulative-error trajectories separated progressively during the 80-month period (\Cref{fig:results_no_subsequent_mlcw_cumulative_error}). At month 80, S4 had the largest absolute cumulative error under all three initial-record lengths (\Cref{tab:results_no_subsequent_mlcw_h80}). The 8-year initial record reduced this error in S4--S6 but did not produce the smallest value in every section.

Figure-title and caption correction:

- Replace the internal figure title `Absolute cumulative deformation error after MLCW measurements cease` with `Absolute cumulative deformation error without subsequent MLCW measurements`.
- Use the same wording in the caption to avoid implying that field measurements actually ceased at Tuku. This is a hypothetical monitoring condition.
- If the embedded title is changed, revise `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\run048_build_sec4_3_preview_figures.py`, regenerate only this figure from the frozen result table, update `figure_source_manifest.json`, verify the copied PDF hash, and compile again. Do not modify any frozen result file or model checkpoint.
- Shorten the table caption to define $A_{s,80}$, its unit, and the common 80-month period. The caption need not repeat the complete calibration procedure already stated in Methods and the subsection opening.

## Required prose audit

After revising, run a full audit of `results004.tex` and correct the following without changing scientific meaning.

- Remove all reader-facing uses of `pooled` and standalone `accuracy`.
- Remove repeated endings such as `The implications of these findings are considered in \Cref{sec:discussion}`. Each subsection should end with its own scientific result.
- Check that every paragraph has one controlling point and that its opening states the pattern before the supporting numbers.
- Check known-to-new flow. The stress of each paragraph should create the topic of the next paragraph or display.
- Do not reproduce the same complete set of values in prose and a table.
- Keep descriptions of figures in captions. Main text should state the pattern shown by the figure.
- Use `MLCW records` for finalized or delivered data records and `MLCW field measurements` for the hypothetical measurement schedule.
- Preserve the distinction among monthly deformation increments, cumulative deformation observations, vertical surface displacement, and land subsidence.
- Confirm that all numerical comparisons use the same dates and scope stated in the associated table or figure.
- Keep Results observational. Move no explanations or limitations into this section.

## Verification and handoff

Before reporting completion:

1. Show the proposed textual diff to the author and obtain approval before applying it.
2. After approval, edit only the approved scope.
3. Run the full manual LaTeX sequence from `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1`.
4. Confirm zero LaTeX errors, zero undefined references, and zero overfull boxes introduced by the revision.
5. Inspect the PDF pages containing Sections 4.1--4.3 to confirm that every figure remains inside its subsection and that continued captions are clear.
6. Search the active Results text for `pooled`, `accuracy`, `confounded`, `after MLCW measurements cease`, first-person pronouns, stale placeholders, and internal pipeline terminology.
7. Report the exact files changed, the build commands, warnings, and remaining placeholders.
8. Do not commit until the author has reviewed the revised PDF.

