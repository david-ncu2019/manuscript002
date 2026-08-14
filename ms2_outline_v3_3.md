# Manuscript Outline (v3.2) — Per-Section Bayesian Ridge Regression

This outline describes the intended content of each section and subsection.
**Internal experiment labels (P0, P3, level1a, level1b, level1c, run_028, run_035, run_048, cross-section, own-section) must not appear in manuscript text.** The manuscript describes methodology and results using physical and data-oriented language only.

[NOTE: To the assistant writing the prose: Keep your sentences direct. State the conclusion first, followed by the supporting evidence. Do not use generic filler phrases like "It can be seen that" or "Generally speaking". Let the physical mechanisms drive the explanation.]

> **Governing decision:** Each depth section is modelled independently by its own Bayesian ridge regression. Predictors include hydraulic head changes observed at the target section's screened interval, head changes observed at other monitored depth intervals, vertical surface displacement, and seasonal terms. The manuscript reports walk-forward evaluation at the Tuku station.

**What changed in v3.2:** §4 Results and §5 Discussion are merged into one section, `§4 Results and Discussion`, with five subsections (4.1–4.5). Each subsection states its claim, its supporting evidence/numbers, and its physical interpretation together, in that order, in the same paragraph — interpretation never appears before the number that justifies it. This replaces v3.1's separate Results (§4) / Discussion (§5) split; no other structural change from v3.1. Conclusions is now §5, Appendix is still §A.

Two experiments still sit at equal priority as the manuscript's critical path, both unbuilt for the per-section modelling design:
1. **Blocker #1** — sensitivity to reduced MLCW measurement frequency (every 6 or 12 months), §3.3.3 / §4.3 / A.4.
2. **Blocker #2** — sensitivity to permanent monitoring stoppage: fit the model once on 3, 5, or 8 years of training data, then predict with no refit and no further MLCW input, to see how estimation error grows over that horizon. See §3.3.4 / §4.4 / A.5.

Neither blocker has a script yet under the per-section design. The closest precedent for both is the existing no-update sensitivity analysis, built for the earlier pooled design — see the note under §3.3.4 for the exact handoff document.

---

## 🔒 Locked sections (from v2_1.md — do not edit without explicit sign-off)

- **§1 Introduction** — draft-quality placeholder; requires literature review citations before finalising.
- **§2 Study Area and Datasets (all subsections 2.1–2.2.4)** — approved and stable.
- **§3.1 Preparation of model inputs (3.1.1–3.1.3)** — approved and stable.

---

## Section-by-section content description

### 1 Introduction
🔒 *Locked (draft quality).*
Establishes the monitoring problem (delayed and declining MLCW records), reviews prior data-driven compaction reconstruction studies, identifies the knowledge gap, and states the study objectives.

[NOTE: The primary novelty to frame here is "Nowcasting to bridge data delays in a degrading monitoring network", not "Depth resolution".]
[ADD: Introduce the specific operational problem at CRAF: delayed or reduced manual MLCW readings prevent timely groundwater management decisions. Frame the research as an operational solution.]

---

### 2 Study Area and Datasets
🔒 *Locked.*

#### 2.1 Study Area Background
Describes the Choushui River Alluvial Fan, its multi-layered aquifer system, and the Tuku monitoring site.

#### 2.2 Datasets
Describes the four data streams: (2.2.1) MLCW compaction increments, (2.2.2) WRA groundwater level (GWL) observations, (2.2.3) TKJS cGNSS surface displacement, and (2.2.4) Tuku borehole lithological profile.

[NOTE: Ensure §2.2.4 mentions that sediment proportions provided physical context via the Isometric Logratio (ILR) transformation, acting as a static base rather than dynamic predictors.]

[NOTE: Resources (verified 2026-08-06). §2.2.1 MLCW compaction: `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\raw_data\01_mlcw_compaction\TUKU.csv` (raw monthly cumulative compaction, 6 section columns), loaded as-is by `scripts\23_build_input_snapshot.py`'s `load_mlcw()` (line 141). Do-not-cite: `scripts\12_clean_mlcw_outliers.py` / `TUKU_cleaned.csv` -- a separate, unused-by-run_048 cleaning path.
§2.2.2 WRA GWL: `raw_data\08_gwl_at_mlcw_monthly_extended\monthly\TUKU_gwl_monthly.csv` + `gwl_source_manifest.json`. Confirmed via `23_build_input_snapshot.py:98` (`GWL_MONTHLY_DIR`, hardcoded, "Locked decisions") that this extended (v5) manifest is what the frozen P0/level1a snapshot actually consumed (traced via `input_data\20260724_run048_stage_c\manifest.json`'s `source_manifest.builder`/`builder_sha256`, which pins to this exact script). Do-not-cite: `raw_data\08_gwl_at_mlcw_monthly\gwl_source_manifest.json` (non-extended -- not what P0/level1a used).
§2.2.3 TKJS cGNSS: `raw_data\03_gps_subsidence\TUKU.csv` + `GPS_DATA_SOURCE_LINEAGE.md` (TUKU<->TKJS mapping, table lines 55-62). Loaded by `load_gps()`, `23_build_input_snapshot.py:148`.
§2.2.4 Borehole lithology + ILR: `raw_data\05_borehole_materials\TUKU\borehole.csv` (raw, 0.1m depth slices) -> `scripts\02_compute_section_materials.py` (`multiplicative_zero_replace()` line 83, `compute_ilr_balances()` line 99, `SECTIONS` 50m bands lines 64-67) -> `raw_data\05_borehole_materials\TUKU\section_materials.csv` (6 rows S1-S6). Static, profile/level-agnostic -- shared by every profile/level combination.]

---

### 3 Methodology

#### 3.1 Preparation of model inputs
🔒 *3.1.1 and deformation model content locked.*

##### 3.1.1 Deformation time series model
Presents the parametric model used to align MLCW and cGNSS observations to common monthly epochs.

[NOTE: Resources (verified 2026-08-06). Two branches converge at `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\23_build_input_snapshot.py`. cGNSS branch: parametric decomposition report `001_data\gps\decomposed\TKJS_neu\TKJS_neu_report_dU.md` (polynomial degree 2, 5 seasonal periods [0.5, 1.0, 3.2, 4.75, 9.14] yr, one jump 2022-06-17, 14 parameters -- the literal "parametric model"), then monthly resample per `raw_data\03_gps_subsidence\GPS_DATA_SOURCE_LINEAGE.md` lines 13-18. MLCW branch: loaded as-is, no parametric step at this stage. Both converge in `build_station_frame()` (line 479).]

##### 3.1.2 Isometric logratio transformation of sediment composition
Describes the ILR transformation of sediment proportions (gravel, coarse sand, fine sand, fine-grained deposits) to eliminate collinearity while preserving lithological context.

[NOTE: Resources (verified 2026-08-06, re-read fresh, no drift from an earlier 2026-08-05 citation). `scripts\02_compute_section_materials.py`: `multiplicative_zero_replace()` line 83 (Martin-Fernandez et al. 2003 zero replacement), `compute_ilr_balances()` line 99.]

##### 3.1.3 Assembly of monthly model inputs
States that each depth section formed a separate calibration dataset with an independent regression model.

[ADD: In Table 2, list the four predictor groups clearly: cGNSS displacement, Target-section hydraulic head, Other-section hydraulic head (as candidate predictors representing system-wide conditions), and Seasonal terms.]

[NOTE: Resources (verified 2026-08-06). Chain: `23_build_input_snapshot.py` -> `scripts\run048_snapshot.py` (`add_run048_candidate_features` line 33 -> stage A/B/C, lines 81/92/136) -> frozen `input_data\20260724_run048_stage_c\TUKU.parquet`. Predictor-group definitions: `scripts\run048_feature_registry.py`, `resolve_profile("P0","level1a")` line 250.
**Content flag, not a lookup gap:** the [ADD] instruction above names four predictor groups; `resolve_profile("P0","level1a")` actually resolves **six** -- it also keeps "static geology (ILR)" (3 features, from §3.1.2/§2.2.4, already locked/approved) and "geology/dry-season interaction" (2 features). These are real, non-trivial groups (5 of 42 nominal features), not noise. Table 2 as currently scoped would omit them. Flag to David before Table 2 is finalized.]

#### 3.2 Bayesian ridge regression
Explains the selection of Bayesian ridge regression for its regularization properties when handling overlapping predictors.

[NOTE: Clarify that the model maps statistical associations rather than replacing deterministic groundwater flow equations.]

[NOTE: Resources (verified 2026-08-06, all line numbers re-checked against the current file, no drift). `scripts\run048_evaluation.py`: `iter_level_scopes()` level1a branch `groups = data.groupby(["station","section"], sort=True)` at line 322 (function starts 248); `fit_bayesian_fold()` starts line 403 (`BayesianRidge(fit_intercept=True)` line 524, `.fit()` line 526, `.predict(..., return_std=True)` line 527); `evaluate_profile_level()` starts line 723 (call site of `fit_bayesian_fold` at line 792); walk-forward refit cadence: `make_rolling_blocks()` line 182, `BLOCK_MONTHS = 6` (line 98), `MIN_TRAIN_MONTHS = 36` (line 99). Genuinely shared/generic across every run_048 profile/level, P0/level1a included.]

#### 3.3 Model evaluation and uncertainty

##### 3.3.1 Evaluation with delayed MLCW data availability
Describes the walk-forward evaluation design: six-month blocks, initial calibration, and automatic refitting.

[NOTE: SUPERSEDED 2026-08-06 -- kept for history only, do not act on this: ~~Not yet ready to draft with real numbers. The per-section walk-forward table for this modelling design has not been assembled yet — only unaggregated per-fold results exist.~~ A 2026-08-06 session built this table. See the resource note immediately below.]

[NOTE: Resources (verified 2026-08-06) -- STATUS: RESOLVED. `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results001\scripts\run048_manuscript_p0_level1a_results.py` (`PROFILE="P0"`, `LEVEL="level1a"`, lines 48-49) reads `checkpoints\P0\level1a\predictions.parquet` directly, excludes the incomplete trailing fold, computes concatenated-series R2/RMSE/MAE per section. Verified: 23 complete 6-month folds x 6 months = 138 rows/section, matching table row counts exactly. Table: `experiments\section_pooled\run_048\supplements\manuscript_results002\sec4_1_combined_performance_interval_table.csv` (7 rows, S1-S6 + All; r2 ranges 0.076 (S5) to 0.976 (S2), pooled r2 = 0.778) + 12 obs-vs-pred/prediction-vs-actual PNGs in the same folder.]

##### 3.3.2 Prediction intervals
Presents the 90% Bayesian predictive interval derived from the posterior predictive variance.

[NOTE: Resources (verified 2026-08-06) -- STATUS: STILL-GAP for a persisted number; the calibration code exists and is wired, but nothing exports its output to a table. Split-conformal implementation: `scripts\run048_manuscript_results001.py`, `calibrate_conformal_by_section_h()` line 102 ((section, h)-stratified, strictly-prior-fold calibration on absolute errors), `finite_sample_quantile()` line 93 (finite-sample-corrected quantile). Confirmed wired to P0/level1a: `manuscript_results001\scripts\run048_manuscript_p0_level1a_diagnostics.py` imports it (line 59), hardcodes `PROFILE="P0"`/`LEVEL="level1a"` (lines 73-74), calls it at line 152 inside `prepare_calibrated_predictions()`. **But verified by full read of that script's `main()` (lines 625-704): the calibrated frame is only ever passed to plotting functions (`plot_section_obs_vs_pred`, `plot_section_prediction_vs_actual`, `plot_fold_timeline`) -- no CSV of coverage/width is ever written from it.**
**Do-not-cite, live mis-citation trap:** `run048_manuscript_p0_level1a_results.py`'s `interval_coverage_by_section.csv` (the source of the `empirical_coverage=0.780` figure already circulating for this manuscript) uses `CONFORMAL_Z = 1.645` -- a **fixed Gaussian** `y_pred +/- 1.645*y_std` band, NOT the split-conformal one -- despite variable/field names (including `run_provenance.json`'s `"conformal_z"` key) that say "conformal." These are different statistical claims: 78% coverage from a raw posterior-std band is unremarkable; 78% from a genuinely calibrated conformal band would be a real miscalibration finding worth flagging. Correct any existing report of "90% interval achieves only 78% coverage" to state plainly which band produced that number.
**To close this gap:** a small aggregation step (not yet built) is needed in `run048_manuscript_p0_level1a_diagnostics.py` or a sibling script, to export `calibrated_predictions`' per-(section,h) coverage/width to CSV. Not started as of 2026-08-06.]

##### 3.3.3 Sensitivity to less frequent MLCW measurements
Describes the experimental scenarios: observing total compaction every 6 or 12 months.

[NOTE: Explain that this sensitivity analysis directly tests an operational reality (budget-driven sampling reduction) rather than just mathematical robustness.]

[NOTE: SUPERSEDED 2026-08-06 -- kept for history only, do not act on this: ~~Not yet ready to draft with real numbers. **Blocker #1.** No reduced-frequency run exists yet for this modelling design — only a full-monitoring-stoppage analysis exists, and it was built for a different (pooled) modelling design.~~ A 2026-08-06 session built and verified this analysis for the per-section (P0/level1a) design. See the resource note immediately below.]

[NOTE: Resources (verified 2026-08-06) -- STATUS: RESOLVED. `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\run048_tuku_p0_level1a_sparse_interval_sensitivity.py` (`PROFILE="P0"`, `LEVEL="level1a"`, lines 71-73, confirmed via the constant, not the filename). Verified genuine full-refit-per-endpoint (the older P3/level1b sibling script had a documented defect of never truly refitting at endpoints -- this script does not share that defect): `fit_interval_constrained()` is called inside the per-endpoint `while True:` loop (line 255), refitting on all accumulated data strictly before scoring each held-out interval.
Outputs, all in `experiments\section_pooled\run_048\supplements\manuscript_results002\`: `sec4_3_reduced_frequency_tradeoff_table.csv` (21 rows: 6 sections + pooled "All" x 3 initial-history lengths; the pooled row is computed directly from all 486 raw endpoint errors as `sqrt(mean(err^2))`, not a naive mean of per-section RMSE, to avoid understating pooled RMSE), `sec4_3_sparse_interval_endpoints.csv` (486 raw per-endpoint errors), `sec4_3_sparse_interval_sensitivity.png`.
**Manuscript table needs a three-file join**, not one file alone: the above trade-off table (MAE/RMSE) + `manuscript_results001\P0_level1a\results\sparse_interval_summary.csv` (bias/mean-signed-error, both monthly and endpoint scope) + `sec4_3_sparse_interval_endpoints.csv` (exact N per cell).
**Exact endpoint count for the thin 12-month/96-month-initial-history cell: 6 per section** (all sections identical, confirmed from the script's own console output and the endpoint CSV) -- this corrects an earlier guess of "~3" that was based on an unrelated CSV's row count from a different protocol.]

##### 3.3.4 Sensitivity to permanent monitoring stoppage
Describes a second experimental scenario, distinct from §3.3.3: the model is fit once, using 3, 5, or 8 years of training data, and then generates predictions with no refit and no further MLCW input for the remainder of the record. This tests what happens if a station stops reporting MLCW measurements permanently, rather than on a fixed reduced schedule.

[NOTE: Explain that this scenario answers a different operational question than §3.3.3. §3.3.3 asks "how much can sampling be thinned while still checking in periodically?" §3.3.4 asks "if a station goes dark for good after 3, 5, or 8 years, how far does the estimate drift before it becomes unusable?"]

[NOTE: Not yet ready to draft with real numbers. **Blocker #2**, equal priority to Blocker #1 above. No script exists yet for this scenario under the per-section modelling design. Follow the same experimental precedent as the existing no-update sensitivity handoff at `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\docs\20260802_run048_tuku_no_update_sensitivity_manuscript_handoff.md` — that document's design (fit once, predict a fixed horizon with no refit, measure cumulative endpoint error) was built for the pooled model at 6- and 12-month horizons. This scenario needs the equivalent design built for the per-section BRR model, extended to 3-, 5-, and 8-year horizons. See D:\112_PROJECT_002\discussions\20260805_outline_v2_4_section_to_codebase_map.md for further detail.]

[NOTE: Resources (verified 2026-08-06) -- STATUS: STILL-GAP, confirmed still accurate. A design memo (no code, no numbers) exists at `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\plans\20260806_run048_p0_level1a_permanent_stoppage_plan.md`: proposes fit-once/no-refit design across 3/5/8-year training windows, explicit metric definitions (monthly vs. cumulative vs. horizon-normalized error, with a caution against reporting the normalized rate alone), a proposed 6-month checkpoint cadence, and 5 open decisions awaiting confirmation. Do not treat this as a citable numeric source.]

---

### 4 Results and Discussion
*(Proposed content: merged into results002.tex; discuss002.tex retired from this section's build)*

[NOTE: The writing tone here must be that of an operational advisor. Acknowledge that the physical monitoring network is degrading, and explain how the model helps decision-makers navigate this limitation without covering up physical gaps. Every claim below states its number first, then its physical interpretation immediately after, in the same paragraph — never interpretation before the number that justifies it.]

##### 4.1 Overall nowcasting performance and depth-dependence
**Claim:** the per-section model nowcasts monthly compaction with section-level accuracy that varies systematically with depth, and its 90% Bayesian predictive interval gives decision-makers a usable, quantified measure of uncertainty without requiring a separately archived historical test set.

**Evidence:** the evaluation blocks, observed compaction range, and section-level metrics ($R^2$, RMSE, MAE) for all six depth sections (S1–S6). Report the metrics fairly for every section, including the near-zero or negative $R^2$ at S5 (200–250 m) stated plainly alongside the other five sections. Alongside the performance metrics, report the empirical coverage and width of the posterior predictive interval, per section.

**Interpretation (same subsection, immediately following the numbers):** S5's weak performance traces to a physical observability gap, not a modelling failure. No piezometer is screened within its compacting fine-grained deposits, so the head-change predictor available for that section is an imprecise proxy for the pore-pressure conditions actually driving compaction there. Frame this as a "Network Warning": machine learning cannot invent physics if observability is strictly zero. If decision-makers remove sensors from actively compacting layers, the ability to nowcast is permanently lost. For the prediction intervals, frame their availability as "from day one" of deployment at a new or resumed station, in contrast to methods that need an accumulated error archive before they can quantify uncertainty at all.

[NOTE: State the S5 physical explanation exactly once. Do not restate the S5 reasoning a second time elsewhere in this subsection or in §4.5 Limitations.]
[NOTE: Also state, where the numbers support it, that the primary value of the model is bridging the data-release delay: timely monthly estimates allow regulators to implement pumping restrictions before irreversible inelastic compaction accumulates. Distinguish this explicitly from long-term forecasting — the model relies on contemporaneous, same-month drivers.]
[NOTE: SUPERSEDED 2026-08-06 -- kept for history only, do not act on this: ~~Not yet ready to draft with final numbers. Table 3 cannot be filled until §3.3.1's per-section walk-forward table exists; the direction of the weakest section (S5, strongly negative) is already known, but the full six-section table is not.~~ Table 3's source table now exists (see §3.3.1's resource note). **Also flag for David: the "S5, strongly negative" phrasing above is now stale.**]

[NOTE: Resources (verified 2026-08-06) -- STATUS: RESOLVED for the performance table; see §3.3.1's note for the table path (same source). **Current S5 R2 = 0.0765 (weakly positive, not strongly negative)** -- supersedes an older cited value of -0.2246, which came from a different concatenated-comparison statistic, not this table's methodology. Flag the stale "strongly negative" wording above to David as a text correction (do not silently edit the claim sentence).
**S5 physical mechanism, verified this session:** `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\raw_data\08_gwl_at_mlcw_monthly_extended\monthly\gwl_source_manifest.json`, TUKU block (starts line 344), `"200_250_m"` entry (line 369): `"source": "raw", "wellcode": "09050341"` -- the same well assigned to S6 (250-300 m), screened 257-263 m, i.e. entirely below S5's 200-250 m band. Confirmed this is the manifest the model actually trained on (traced via `input_data\20260724_run048_stage_c\manifest.json`'s `source_manifest.builder_sha256`, pinned to `23_build_input_snapshot.py`, which hardcodes this extended dir). This is the precise mechanism behind the claim above ("no piezometer is screened within its compacting fine-grained deposits") -- the claim sentence itself is already correct and needs no edit, only this citation.
Do-not-cite: the non-extended manifest at `raw_data\08_gwl_at_mlcw_monthly\gwl_source_manifest.json` -- an earlier read of this file (superseded) wrongly suggested S5 was kriged/interpolated rather than fed by a real, mis-screened well; that manifest is not what the frozen snapshot consumed.]

##### 4.2 Coefficients of driving factors at each section
**Claim:** the predictors that drive the nowcast differ by depth section, and identifying which factor dominates where explains the physical mechanism behind each section's compaction behavior.

**Evidence:** Bayesian ridge regression coefficients (posterior mean plus credible interval) for every predictor, per depth section (S1–S6) — cGNSS displacement, target-section hydraulic head, other-section hydraulic head, and seasonal terms. Report which predictor group dominates at each section, alongside a table or figure ranking driving factors by their standardized coefficient magnitude.

**Interpretation (same subsection):** explain which physical mechanism each dominant predictor represents at each section (e.g., a section whose compaction is driven mainly by its own hydraulic head behaves differently from one driven mainly by cross-section head changes or by seasonal terms), and connect this to the depth-dependent performance pattern already established in §4.1.

[NOTE: Resources (verified 2026-08-06) -- STATUS: RESOLVED. `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results002\sec4_2_coefficient_summary_by_section.csv` (216 rows = 6 sections x 36 features, median coefficient across 24 folds, sourced from `checkpoints\P0\level1a\standardized_coefficients.parquet`, section parsed from `group_id`'s `{STATION}__{SECTION}` format) + `sec4_2_driving_factor_summary.md` (one-sentence-per-section dominant-group summary) + 24 PNGs (18 driving-features + 6 fitting-parameters pages).
**Flag for David, not resolved here:** the summary's "dominant predictor" rule picks the single largest-|median| feature per section, which structurally favors compact feature families over spread-out ones. Corrected group sizes (independently audited 2026-08-06 against `sec4_2_coefficient_summary_by_section.csv` directly, S1 spot-check): **seasonality = 5 features** (`month_sin`, `month_cos`, `month2_sin`, `month2_cos`, `is_dry_season`), **groundwater_level = 25 features** (10 own-section + 15 cross-section -- this script's `feature_category()` folds `xs_*_dGWL*` cross-section terms into the same "groundwater_level" bucket). The directional claim still holds (seasonality is much smaller/tighter than GWL, so a largest-single-feature rule structurally favors it), but an earlier draft of this note understated both counts ("~4" and "~15-20") -- corrected here. The current result ("seasonality dominates 5 of 6 sections") could change under a group-level aggregate rule (e.g. sum of |median| within group). Disclosed as a live choice, not silently fixed.]

##### 4.3 Sensitivity to reduced-frequency measurements
**Claim:** reducing MLCW check-in frequency from monthly to every 6 or 12 months is an operationally real trade-off, not just a mathematical robustness test.

**Evidence:** monthly and endpoint errors under the 6-month and 12-month interval scenarios, consolidated into one table comparing endpoint errors between the two schedules, per depth section and combined across the profile.

**Interpretation (same subsection):** present the data as a trade-off curve between field-visit cost and estimation uncertainty. Synthesize directly into the operational framing: this is a tool for the Water Resources Agency (WRA) to decide how much they can safely reduce sampling frequency without blinding themselves to critical subsidence events.

[NOTE: SUPERSEDED 2026-08-06 -- kept for history only, do not act on this: ~~Not yet ready to draft with real numbers. **Depends on Blocker #1** (§3.3.3), which has no scenario runs yet for this modelling design.~~ Blocker #1 is now resolved -- see §3.3.3's resource note above for the full path/verification detail (same underlying data feeds this subsection).]

##### 4.4 Sensitivity to permanent monitoring stoppage
**Claim:** this asks a different operational question than §4.3. §4.3 asks "how thin can periodic sampling go while still checking in?" This subsection asks "if a station goes dark for good, how far does the estimate drift before it stops being usable?"

**Evidence:** cumulative estimation error growth over the 3-, 5-, and 8-year no-refit horizons, per depth section and for the complete monitored profile. Report cumulative endpoint error (MAE, RMSE, bias, in mm) at each horizon, plus horizon-normalized error (mm/month) reported alongside — never in place of — the absolute cumulative error.

**Interpretation (same subsection):** state plainly whether the model degrades gracefully or fails sharply past some horizon, once the numbers exist, framed as a WRA decision-support question: how long can this station go unmonitored before its estimate can no longer support a pumping-restriction decision?

[NOTE: The physically relevant quantity for an operator deciding how long a station can go unread is the absolute cumulative endpoint error, not the horizon-normalized rate — the normalized rate can fall even as absolute error grows, from partial cancellation, per the same caution documented in the no-update sensitivity handoff. Never report the normalized rate as a standalone headline number.]
[NOTE: Not yet ready to draft with real numbers. **Depends on Blocker #2** (§3.3.4), equal priority to Blocker #1. No script exists yet under the per-section modelling design. The closest precedent is the no-update sensitivity handoff built for the pooled model at 6-/12-month horizons (`D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\docs\20260802_run048_tuku_no_update_sensitivity_manuscript_handoff.md`), which needs the equivalent built for the per-section BRR model, extended to 3-/5-/8-year horizons. See D:\112_PROJECT_002\discussions\20260805_outline_v2_4_section_to_codebase_map.md for detail.]

[NOTE: Resources (verified 2026-08-06) -- STATUS: STILL-GAP, confirmed still accurate. See §3.3.4's resource note above -- design memo only, at `007_tests\014_ml_nowcast\plans\20260806_run048_p0_level1a_permanent_stoppage_plan.md`, no numbers yet.]

##### 4.5 Limitations and practical scope
**Claim:** the fitted model is strictly local to Tuku's specific lithology, well configuration, and stress history; only the methodology, not the fitted coefficients, is transferable.

**Interpretation only (no new evidence introduced here):** prevents overclaiming. State explicitly that while the methodology is fully transferable, the specific fitted coefficients cannot be copy-pasted to another station.

---

### 5 Conclusions

Restate the operational objective (nowcasting layer-specific compaction under delayed/degraded data delivery). Summarize the data sources and the Bayesian method.

[ADD: Deliver the principal conclusion: The approach successfully bridges temporal data gaps in well-monitored sections, offering an operational trade-off for budget-constrained networks, but it cannot overcome fundamental physical blind spots where sensors are missing.]

[NOTE: Match the prose STYLE (not the content or methodology) of the following papers when drafting this conclusion:
- Hung et al. (2025), "Near real-time subsidence monitoring and AI forecasting with multi-depth extensometers" — `D:\001_LITERATURE_v2\ZOTERO_storage\storage\GFDMNS9S\`
- Liu et al. (2025), "Deep learning time-series modeling for assessing land subsidence under reduced groundwater use" — `D:\001_LITERATURE_v2\ZOTERO_storage\storage\LAML2LM8\`
- Liu et al. (2023), "Reconstructing missing time-varying land subsidence data using back propagation neural network" — `D:\001_LITERATURE_v2\ZOTERO_storage\storage\6TYF2YLR\`
- Wang et al. (2025), "A case study on the application of a data-driven (XGBoost) approach on the environmental and socio-economic..." — `D:\001_LITERATURE_v2\ZOTERO_storage\storage\BNZ9BUGJ\`
- Nguyen et al. (2024), "Quantitative Evaluations of Pumping-Induced Land Subsidence and Mitigation Strategies" — `D:\001_LITERATURE_v2\ZOTERO_storage\storage\LMTIPY87\`]

[NOTE: Resources (verified 2026-08-06) -- all 5 folders above confirmed to exist, each with its PDF present (plus Zotero-internal cache files, not content). No action needed.]

---

### A Supplementary methodological details

##### A.1 Final predictor inventory
[NOTE: A clean table of the final frozen predictors from the pipeline run. No internal experiment tags.]
[NOTE: SUPERSEDED 2026-08-06 -- kept for history only, do not act on this: ~~Partially ready. The predictor list can be generated on demand from the existing pipeline logic, but no static table has been exported yet.~~ A static table now exists. See the resource note immediately below.]

[NOTE: Resources (verified 2026-08-06) -- STATUS: RESOLVED, with a count caveat. Generator: `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results001\scripts\run048_manuscript_p0_level1a_predictor_inventory.py`, calls `resolve_profile("P0","level1a")` from `scripts\run048_feature_registry.py` line 250. Output: `manuscript_results001\P0_level1a\results\predictor_inventory.csv` (42 nominal rows, 6 feature-group labels).
**Number caveat:** 42 nominal predictors is not the same as the number actually used by a fitted model. `checkpoints\P0\level1a\fitted_models.parquet`'s `n_active_features` column is constant at **36** across all 522 fold-fits (6 features are dropped as zero-variance in every fold). If A.1 states a predictor count, state both numbers with their sources -- do not state 42 alone.]

##### A.2 Model fitting and update settings
[NOTE: Record the technical configuration to guarantee reproducibility.]

[NOTE: Resources (verified 2026-08-06) -- STATUS: RESOLVED. `scripts\run048_evaluation.py` line 524: `BayesianRidge(fit_intercept=True)` -- no explicit override of alpha_1/alpha_2/lambda_1/lambda_2; these are sklearn defaults (cite "sklearn defaults" and the fitted posterior values, do not hand-write numeric default values from memory). Fitted posterior alpha/lambda: `checkpoints\P0\level1a\fitted_models.parquet` (`alpha`/`lambda` columns; range across 522 fits: alpha 0.82-344, lambda 3.6-1910) + figures `experiments\section_pooled\run_048\supplements\manuscript_results002\sec4_2_fitting_parameters_S{1-6}.png`. Refit cadence ("every six months"): `BLOCK_MONTHS = 6` (line 98) driving `make_rolling_blocks()` (line 182); `MIN_TRAIN_MONTHS = 36` (line 99) is the minimum history before the first fold fires.
Do-not-cite: `scripts\run048_tuku_no_update_sensitivity.py` -- P3/level1b, a deliberate *no-refit* design; wrong cadence description for A.2.]

##### A.3 Prediction interval calibration
[NOTE: Mathematical proof of the posterior predictive distribution, explaining why it works without an accumulated error archive.]

[NOTE: Resources (verified 2026-08-06) -- STATUS: STILL-GAP for a derivation write-up; implementation exists. `scripts\run048_manuscript_results001.py`: `calibrate_conformal_by_section_h()` line 102, `finite_sample_quantile()` line 93 (finite-sample-corrected quantile, `ceil((n+1)(1-alpha))/n`), `CONFORMAL_ALPHA`/`MIN_ELIGIBLE_CONFORMAL_COUNT` constants nearby. Confirmed wired to P0/level1a via `manuscript_results001\scripts\run048_manuscript_p0_level1a_diagnostics.py` (imports it line 59, calls it line 152) -- see §3.3.2's note above for the important caveat that this wiring produces figures only, no persisted coverage/width CSV yet.
**No mathematical derivation write-up exists anywhere on disk** under `manuscript_results001\` (confirmed, no `.md` files besides an unrelated summary). A.3 must be written from first principles off `calibrate_conformal_by_section_h()`'s own logic (lines 102-119) and split-conformal theory -- there is no existing derivation doc to lean on.]

##### A.4 Reduced-frequency MLCW measurement settings
[NOTE: Provide the exact endpoint constraint numerical formulation used in the 6- and 12-month sparse-sampling sensitivity scenarios (§3.3.3).]
[NOTE: SUPERSEDED 2026-08-06 -- kept for history only, do not act on this: ~~Not yet ready to draft with real numbers. The constraint formulation is designed but has not been run for this modelling design yet — same dependency as §3.3.3/§4.3 (Blocker #1).~~ Blocker #1 is resolved -- see §3.3.3's resource note above for the scenario data/tables. The numerical formulation itself (whitened interval-sum aggregation, `1/sqrt(|I|)` variance scaling, explicit intercept column) lives in `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\run048_tuku_p0_level1a_sparse_interval_sensitivity.py`'s `fit_interval_constrained()` function (see §3.3.3's note for line references) -- read that function directly for the exact formulation to describe in A.4.]

##### A.5 Permanent-stoppage scenario settings
[NOTE: Provide the exact numerical formulation used in the 3-, 5-, and 8-year no-refit sensitivity scenarios (§3.3.4): training window lengths, horizon lengths, and the no-refit constraint.]
[NOTE: Not yet ready to draft with real numbers. No script exists for this scenario yet — same dependency as §3.3.4/§4.4 (Blocker #2). See D:\112_PROJECT_002\discussions\20260805_outline_v2_4_section_to_codebase_map.md for detail.]

[NOTE: Resources (verified 2026-08-06) -- STATUS: STILL-GAP, confirmed still accurate. Design memo (proposed formulation, no numbers): `007_tests\014_ml_nowcast\plans\20260806_run048_p0_level1a_permanent_stoppage_plan.md`, §5 (metric definitions), §6 (proposed 6-month checkpoint cadence), §9 (proposed output schema).]
