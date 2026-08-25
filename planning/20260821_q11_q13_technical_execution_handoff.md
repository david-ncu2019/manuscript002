# Q11-Q13 discussion evidence: technical execution handoff

**Task ID:** `Q11_Q13_DISCUSSION_EVIDENCE_20260821`
**Execution plan:** `C:\Users\FAFALAB\.claude\plans\plan-agent-writing-plans-tui-validated-engelbart.md` (SHA-256 `1C6C5AE47E92889782FB0E47B84DA956219631F7A08121B9D97268A16345F89B`)
**Source technical plan:** `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\planning\20260821_203617_q11_q13_discussion_evidence_plan.md` (SHA-256 `30C5E22D5107DD65AC75B60251A32440080FB78C43FD9D6888AEA8223ADAFCFA`)
**Overall status: COMPLETE**

This report is technical execution documentation only. It does not draft manuscript prose and
does not recommend which results belong in the Discussion or Results sections -- the author and
writing assistant decide that separately. No `.tex` file was read for editing purposes, and none
was modified.

## 1. Validation gate results

All 9 gates from the source technical plan PASSED on the final validator run. Full detail in
`validation/validation_report.json` and `validation/validation_report.md`.

| Gate | Name | Result |
|---|---|---|
| 1 | Source integrity | PASS |
| 2 | Full-model parity (Q11 Config 4 vs frozen Section 4.1, within 1e-8) | PASS (exact 0.0 max diff) |
| 3 | Calendar identity (23 cycles/138 per section; 432 rows/scenario) | PASS |
| 4 | Target identity (within 1e-10) | PASS |
| 5 | Training-only construction (pytest, 5/5 tests) | PASS |
| 6 | Determinism (rerun into temp sibling, parsed-value diff) | PASS (exact 0.0 max diff, 6 outputs compared) |
| 7 | No forbidden changes (protected regions + all 48 `.tex` files) | PASS |
| 8 | Artifact traceability (RUN_LOG.md completeness) | PASS |
| 9 | Independent review (advisor) | PASS |

**Mid-execution correction (Task 6, before Gate 9 was recorded as passed):** the independent
advisor review found two blockers before any gate was finalized -- (a) the Q12/Q13 paired
block-bootstrap was grouping by single calendar month instead of by the 6-month/12-month
measurement-interval cycle, understating uncertainty; (b) Q11's Configuration 5 (sinusoidal
control) was fit with 10 features (5 seasonal + 5 sinusoid) instead of the 5 sinusoid-only
features the source plan specifies, changing what two of the eight Q11 contrasts actually test.
Both were fixed, Tasks 3-5 were rerun against the fixes, and a second advisor pass confirmed the
fixes landed correctly (plus one cosmetic column-labeling defect, also fixed). Full detail,
verbatim advisor responses, and the resolution of every item (including two explicitly
documented judgment calls that were not changed) are in `validation/advisor_review.md`.

## 2. Files created

Exactly 4 new code files (as specified in the source plan's "New Code Files" section) plus this
handoff report:

- `D:\1000_SCRIPTS\...\014_ml_nowcast\scripts\run048_build_q11_predictor_information_evidence.py`
- `D:\1000_SCRIPTS\...\014_ml_nowcast\scripts\run048_build_q12_q13_comparison_evidence.py`
- `D:\1000_SCRIPTS\...\014_ml_nowcast\scripts\run048_validate_discussion_evidence.py`
- `D:\1000_SCRIPTS\...\014_ml_nowcast\tests\test_run048_discussion_evidence.py`
- `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\planning\20260821_q11_q13_technical_execution_handoff.md` (this file)

All data outputs are confined to one new folder:
`D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results003_calendar_aligned_38predictors\discussion_evidence_20260821\`

Full itemized list with hashes, sizes, and generating script: `task_created_files_manifest.json`
and `artifact_manifest.json` in that folder.

## 3. Files modified

None outside the 4 new code files themselves (edited in place during the Task 6 fix cycle, never
after Gate 9 passed). No `.tex` file, no frozen result, no checkpoint, no `manuscript_results001`
or `manuscript_results002` file was modified -- confirmed by Gate 7's byte-for-byte re-hash of
all protected regions (337 checkpoint files, 137 manuscript_results002 files, 18 sec4_1/4_2/4_3
result files, 48 `.tex` files) against the pre-execution hashes recorded in
`source_provenance.json`.

## 4. Q11 summary: does cGNSS and/or GWL add predictive information beyond seasonal repetition?

Pooled across all 6 sections (828 complete-cycle rows, 23 cycles, 138 estimates/section, exact
parity with frozen Section 4.1):

| Configuration | MAE (mm/month) | RMSE (mm/month) | R² |
|---|---|---|---|
| Seasonal reference (5 features) | 0.278 | 0.425 | 0.776 |
| cGNSS + seasonal (9 features) | 0.262 | 0.415 | 0.787 |
| GWL + seasonal (34 features) | 0.297 | 0.433 | 0.768 |
| Full model (38 features) | 0.279 | 0.423 | 0.778 |
| Sinusoidal control (5 fabricated sin/cos terms only) | 0.329 | 0.468 | 0.729 |
| Month-of-year mean (no model) | 0.283 | 0.439 | 0.761 |

Paired contrasts (MAE difference, 95% block-bootstrap CI, 23-cycle blocks, 2000 resamples):

- **Full model minus seasonal reference:** +0.0010 mm, CI [-0.0227, +0.0243] -- crosses zero, no
  stable difference detected pooled across all sections.
- **cGNSS+seasonal minus seasonal reference:** -0.0158 mm, CI [-0.0392, +0.0061] -- crosses zero.
- **GWL+seasonal minus seasonal reference:** +0.0197 mm, CI [+0.0053, +0.0347] -- excludes zero;
  GWL+seasonal has HIGHER pooled MAE than seasonal alone in this configuration.
- **Full model minus cGNSS+seasonal:** +0.0168 mm, CI [+0.0080, +0.0275] -- excludes zero; full
  model has higher error than cGNSS+seasonal alone.
- **Full model minus GWL+seasonal:** -0.0186 mm, CI [-0.0370, -0.0015] -- excludes zero; full
  model has lower error than GWL+seasonal alone.
- **Sinusoidal control minus seasonal reference:** +0.0517 mm, CI [+0.0098, +0.0960] -- excludes
  zero; 5 fabricated sinusoids alone perform worse than the 5 real seasonal features.
- **Full model minus sinusoidal control:** -0.0506 mm, CI [-0.0950, -0.0083] -- excludes zero;
  the full 38-variable model outperforms the fabricated-sinusoid-only control.
- **Full model minus month-of-year mean:** -0.0047 mm, CI [-0.0304, +0.0201] -- crosses zero.

**Caution flag:** the full-model-vs-seasonal-reference and full-model-vs-month-of-year-mean
contrasts, which are the most direct tests of "does the full model help at all," both cross
zero pooled across all 6 sections. Section-level results in
`q11_predictor_information/performance_by_configuration_and_section.csv` should be checked before
any manuscript claim of overall improvement -- pooled null results can still hide section-level
heterogeneity in either direction.

## 5. Q12 summary: reduced MLCW measurement frequency (6- or 12-month intervals) vs Section 4.1

432 matched section-month rows per scenario, 2018-05 through 2024-04, target MLCW values
identical to Section 4.1 within 1e-10 in every scenario (verified, not assumed). Sign convention:
diff = Section 4.2 (reduced frequency) minus Section 4.1 (monthly delayed-delivery).

| Interval | Initial history | MAE diff (mm) | 95% CI | Abs. coverage deviation diff |
|---|---|---|---|---|
| 6 months | 3y | -0.0068 | [-0.0321, +0.0262] | -0.0486 (closer to 90% nominal) |
| 6 months | 5y | -0.0159 | [-0.0405, +0.0095] | -0.1134 (closer to 90% nominal) |
| 6 months | 8y | +0.0147 | [+0.0017, +0.0283] | -0.0926 (closer to 90% nominal) |
| 12 months | 3y | +0.0020 | [-0.0299, +0.0394] | +0.0023 (further from nominal) |
| 12 months | 5y | -0.0119 | [-0.0425, +0.0200] | -0.0856 (closer to 90% nominal) |
| 12 months | 8y | +0.0238 | [+0.0042, +0.0435] | -0.0394 (closer to 90% nominal) |

**Caution flags:**

- Only 2 of 6 MAE-difference CIs exclude zero (6mo/8y and 12mo/8y, both positive -- reduced
  frequency has higher error in those two scenarios specifically, not as a general pattern).
- All bootstrap block structure uses `cycle_index` (12 blocks for the 6-month schedule, 6 blocks
  for the 12-month schedule) -- this was a Task 6 correction; the 12-month schedule's CIs in
  particular rest on only 6 independent blocks and should be read as wide-uncertainty even where
  the point estimate is directionally consistent.
- Raw coverage differences carry no inherent favorable direction; every comparison in this
  package uses the absolute-coverage-deviation difference instead (negative = closer to nominal
  90%), never the raw difference, per the plan's sign-convention rule.

## 6. Q13 summary: initial MLCW history length (3y / 5y / 8y) within each measurement schedule

3 pairwise contrasts (5y-3y, 8y-3y, 8y-5y) x 2 schedules (6-month, 12-month), monthly and
endpoint scope. Shared window and identical observed MLCW verified across all three history
lengths within each schedule (not assumed).

| Interval | Contrast | MAE diff (mm) | 95% CI |
|---|---|---|---|
| 6 months | 5y minus 3y | -0.0091 | [-0.0346, +0.0150] |
| 6 months | 8y minus 3y | +0.0215 | [-0.0033, +0.0416] |
| 6 months | 8y minus 5y | +0.0306 | [+0.0143, +0.0467] |
| 12 months | 5y minus 3y | -0.0139 | [-0.0282, +0.0036] |
| 12 months | 8y minus 3y | +0.0219 | [+0.0019, +0.0366] |
| 12 months | 8y minus 5y | +0.0357 | [+0.0182, +0.0519] |

**Caution flags:**

- The direction is consistently "8y has higher MAE than 5y" (both schedules, CI excludes zero in
  both cases) and "8y has higher MAE than 3y" with the 12-month schedule also excluding zero.
  Longer initial history does NOT show a monotonic error-reduction pattern in this evidence --
  the opposite direction from a naive "more history is always better" assumption.
- These CIs widened substantially after the Task 6 bootstrap-block fix (e.g. 6mo/8y-minus-5y
  went from a flawed [0.0187, 0.0422] to the corrected [0.0143, 0.0467]) -- still excludes zero,
  but on a materially wider and more defensible interval.
- No independent operational threshold exists for what counts as a "sufficient" initial-history
  length; this package does not attempt to establish one, per the source plan's interpretation
  boundary.

## 7. Discrepancies preventing manuscript use

None identified. All 9 validation gates passed on the final run, including exact-zero-diff
determinism and exact parity with the frozen Section 4.1 production predictions.

## 8. Confirmation: no manuscript or frozen result file was changed

Confirmed by Gate 7 (`validation/validation_report.json`, gate_id 7, passed=true): byte-for-byte
SHA-256 comparison of all 337 `checkpoints/` files, 137 `manuscript_results002/` files, 10+5+3
`results/sec4_1|sec4_2|sec4_3/` files, and all 48 `.tex` files in the manuscript worktree against
hashes recorded before this task's first script execution, zero mismatches. `results004.tex`,
`discuss003.tex`, and every other manuscript file were not read for editing and were not touched.
