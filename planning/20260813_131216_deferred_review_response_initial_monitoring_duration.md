# Deferred Reviewer-Response Analysis: Initial Monthly Monitoring Duration

**Recorded:** 2026/08/13 13:12:16 +08:00  
**Status:** Deferred until after manuscript submission or a reviewer request  
**Priority:** Complete and submit the current manuscript first

## Decision

The manuscript will not be expanded now with an additional experiment designed to determine whether three years of continuous monthly MLCW monitoring are sufficient before field measurements become less frequent. The current reduced-frequency analysis remains the evidence used for the submission draft. Additional model runs would delay submission beyond the missed deadline of 2026/08/09.

No agent should implement the analysis described below, expand the present manuscript claim, or delay submission for this question unless the author explicitly reactivates it.

## Scientific Question Reserved for Review

The practical question is whether continuous monthly MLCW monitoring for three years provides nearly the same subsequent estimation performance as monitoring for five or eight years. If three years are sufficient at Tuku, the additional cost and field effort required to maintain monthly measurements for another two or five years may provide limited benefit before changing to a 6- or 12-month measurement schedule.

The present experiment compares three operational strategies that begin at the first available record:

- monthly monitoring for 3 years, followed by less frequent measurements;
- monthly monitoring for 5 years, followed by less frequent measurements; and
- monthly monitoring for 8 years, followed by less frequent measurements.

This comparison is operationally meaningful, but the reduced-frequency periods begin in different calendar years. Differences among the results may therefore reflect both the length of the initial record and the conditions during the later evaluation period.

## Analysis to Run Only if Needed

If a reviewer asks whether three years are genuinely sufficient, retain the existing operational comparison and add a controlled comparison in which all models begin estimation on the same dates.

At each eligible common estimation origin:

1. Fit separate models using the preceding 3, 5, and 8 years of monthly observations.
2. Use identical future months, predictors, and 6- or 12-month MLCW update schedules for all three models.
3. Compare monthly and endpoint MAE, RMSE, and mean signed error by depth section and across the monitored profile.
4. Report the absolute and relative improvement from 3 to 5 years and from 3 to 8 years.
5. Repeat the comparison at multiple eligible origins where the record permits, rather than relying on one favorable period.
6. Preserve the existing operational results and label the common-origin analysis as a controlled sensitivity test.

The evidence would support a narrow statement that three years were sufficient for the Tuku analysis only if the 5- and 8-year models provide small and inconsistent improvements across common origins and depth sections. It would not establish a universal three-year requirement for other stations or monitoring systems.

## Reviewer-Response Position

If this question is raised before the additional analysis is run, explain that the submitted experiment compares realistic monitoring strategies beginning from the first available record. Acknowledge that the different transition dates prevent the initial-history effect from being isolated completely. The common-origin analysis above can then be implemented to provide a controlled response.

## Related Files

- Reduced-frequency method: `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\methods005.tex`
- Reduced-frequency results draft: `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\results_discussion_draft.tex`
- Analysis script: `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\run048_tuku_p0_level1a_sparse_interval_sensitivity.py`
- Technical audit: `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results002\previews\sec4_2_reduced_frequency\002_sec4_2_reduced_frequency_calculation_and_data_audit_report.md`

## Current Submission Boundary

The month-of-year reference-model comparison is also reserved for reviewer response and will not be added to the current manuscript unless the author explicitly requests it. The immediate work should remain limited to correcting confirmed documentation inconsistencies, writing the existing Results and Discussion, completing figures and tables, compiling the manuscript, and submitting it.
