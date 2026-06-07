# Discussion: Prediction Pipeline Design — Peer Review

**Date:** 2026-06-01
**Status:** Under review — do not implement as designed

---

## Executive Summary

**Do not implement the prediction pipeline this week.** The proposal declares itself "ready for implementation," but five independent reviewers all reached the same conclusion: the pipeline cannot work in its current form. The single biggest reason is data dependency failure. The pipeline requires three inputs that do not exist at 37-station scale: `reconstruction_metrics.csv` exists for only 3 of 37 stations, Azeriansyah zone polygons do not exist anywhere in the repository, and `direct_ratio_stats.csv` stores per-depth-ring values (60 levels) rather than per-layer values (6 layers). This week, fix the IHM-F v3 joint solver (currently returns R^2_insar = −6.48 at TUKU), run the all-stations seasonal harmonic batch, and create the zone assignment CSV. Build the prediction pipeline only after the physical model produces positive R^2 values. The pipeline is a validation wrapper around a working model — wrapping a broken model adds no value.

---

## 1. Proposal Summary

The prediction pipeline (`scripts/15_prediction/`) wraps the existing InSAR-to-MLCW direct-ratio model into a 6-module framework for temporal walk-forward validation and spatial kriging. Tier 1 predicts per-layer compaction from `f_k x InSAR(t)`. Tier 2 adds a seasonal harmonic term for F2. Kriging extends the per-layer $f_{k}$ from 37 stations to 8,577 grid points using zone-stratified interpolation. Four hold-out years (2022-2025) serve as temporal validation; leave-one-out cross-validation serves as spatial validation. The proposal declares itself "Design approved."

---

## 2. Dependency Audit

The pipeline assumes eight input files. Six exist. Two do not.

**Existing inputs (verified on disk):**

| Input | Format | Status |
|-------|--------|--------|
| InSAR station timeseries (39 rows) | Feather, `mlcw_interp_insar_IDW_extend.feather` | Exists |
| InSAR grid timeseries (8,577 rows) | Feather, `gridpnt_500m_interp_insar_IDW_extend.feather` | Exists |
| Direct ratio per-depth f_median | CSV, `results/direct_ratio/{STATION}/TUKU_direct_ratio_stats.csv` | Exists |
| Reconstruction metrics (3 stations) | CSV, `results/seasonal_insar_harmonic/{STATION}/reconstruction_metrics.csv` | Exists (3 of 37) |
| Harmonic decomposition (3 stations) | CSV, `step2_insar_harmonic_decomposition.csv` | Exists (3 of 37) |
| Phase stability summary (3 stations) | CSV, `step3_phase_stability_summary.csv` | Exists (3 of 37) |

**Missing inputs:**

| Input | Issue | Severity |
|-------|-------|----------|
| `ZONE_ASSIGNMENT_CSV` | **Does not exist.** No shapefile, CSV, or station-to-zone mapping file exists anywhere in the repository. Reviewer 5 searched across all directories. | MAJOR — blocks spatial kriging entirely |
| 37-station seasonal harmonic batch | Only 3 of 37 stations have outputs in `results/seasonal_insar_harmonic/`. Tier 2 is restricted to those 3 stations until the batch runs. The batch takes 1-3 hours of compute. | MAJOR — blocks Tier 2 rollout |

GWL trend covariate at 8,577 grid points is also unavailable. It would require its own kriging exercise from 306 well locations — a separate pipeline step that is neither specified nor budgeted.

---

## 3. Scientific and Technical Critique

### 3.1 Tier 1: $f_{k}$ source mismatch

The proposal states that `f_k` comes from `direct_ratio_stats.csv`. This file stores `f_median` at 5-meter depth intervals (60 rows per station), not per layer. The proposal's `load_fbar()` function returns a Series indexed by `depth_m`, but the walk-forward model expects a layer-keyed scalar.

`reconstruction_metrics.csv` already contains a per-layer `fbar` column computed via anchored OLS — a different method than the depth-aggregated median. Values differ systematically. At TUKU F2, the depth-aggregated `f_median` is approximately 0.046, while the anchored OLS `fbar` is 0.176. The anchored OLS value matches the harmonic baseline RMSE (TUKU F2 2022 RMSE_baseline approx 3.495 mm) and reproduces the known Hefeng benchmark (0.176 cm per 1 m head drop).

**Fix:** Use anchored OLS `fbar` from `reconstruction_metrics.csv`, not the depth-level `f_median` from `direct_ratio_stats.csv`. The `load_fbar()` function signature should be changed to `load_fbar(station, harmonic_dir)` and read from the reconstruction metrics file.

**Confidence: HIGH.** The per-layer fbar is the directly relevant quantity, and the reconstruction_metrics file already stores it.

### 3.2 Tier 2: Seasonal gate bug and double-counting

**Gate bug (CRITICAL):** The phase stability gate at TUKU sets `seasonal_applied=True` for F1 despite `R2_seasonal = -0.105`. The F1 row in `step3_phase_stability_summary.csv` shows:

| Layer | std_dphi1_days | A1_mm_mean | corr_A1k_A1x | annual_PASS |
|-------|---------------|-----------|---------------|-------------|
| F1 | 43.0 | 1.043 | **-0.827** | True |

The gate checks `std_dphi1_days < 45` and `A1_mm_mean > 0.5`, both of which F1 satisfies. It does not check `corr_A1k_A1x > 0.0`. The F1 amplitude correlation is strongly negative (-0.827), meaning the MLCW and InSAR annual cycles are anti-correlated at F1. Adding F1 seasonal in Tier 2 actively degrades prediction (R2_seasonal = -0.105 confirms this).

**Fix:** Add `corr_A1k_A1x > 0.0` to the gate condition in `reconstruction_metrics.csv`. Then re-run the 3-station reconstruction to regenerate `seasonal_applied` and `R2_seasonal` values.

**Confidence: HIGH.** The data file confirms the exact values. The gate logic is in `scripts/13_seasonal_insar/01_seasonal_harmonic_analysis.py` and `02_reconstruction_visualization.py`.

**Double-counting (MEDIUM):** Tier 1 uses total InSAR `x(t)`, which includes the seasonal component. Tier 2 then adds `r_k A1_x(t)`. The net seasonal component is `f_k x_seasonal(t) + r_k A1_x(t)`. Since `x_seasonal(t) approx A1_x(t)`, the seasonal signal is partially double-counted.

**Fix:** Decompose InSAR into trend and seasonal components. Use only the trend component `x_trend(t)` in Tier 1. Use `A1_x(t)` in Tier 2. This requires a detrending step on InSAR that mirrors the MLCW detrending already implemented in `ihmf_detrend.py`.

**Confidence: MEDIUM.** The magnitude of double-counting depends on the proportion of seasonal variance in total InSAR. At stations where the seasonal amplitude is small relative to trend, the effect is negligible. The locked harmonic findings (Section 4 of CLAUDE.md: "F2 seasonal is reconstructable from InSAR") support the decomposition approach.

### 3.3 Walk-forward design

The walk-forward logic re-estimates `f_k` per fold rather than freezing it from the full record. This is correct — it prevents future data leakage and reflects the operational use case where only past data is available.

The fold-1 special status (`is_fold1 = True`) and 2022 hold-out RMSE comparison against the harmonic baseline (TUKU F2 RMSE approx 3.495 mm) are both sensible benchmarks.

**Gap:** The walk-forward function signature shows `insar_series` as a single `pd.Series` and expects per-station InSAR data. The actual InSAR feather file stores all 39 stations as rows and 785 epochs as columns. The loader must transpose and index by station. This is straightforward but the column-format assumption in the contract should be updated.

**Confidence: HIGH.** The proposal's walk-forward logic matches standard practice in geophysical time-series validation.

### 3.4 Baseline definition

The proposal uses "anchor-only baseline" (`f_k InSAR_anchor`, a constant equal to the last training epoch prediction). For a strongly trending process like subsidence, any model that captures the trend will beat a no-change forecast.

**Fix:** Add a trend-extrapolation baseline. Fit a linear trend to the training window and extend it into the hold-out year. This gives a meaningful skill benchmark: the model must improve upon "subsidence continues at the training-period rate."

**Confidence: HIGH.** Reviewer 1 correctly identifies this as a standard weakness of no-change baselines in trend-dominated geophysical time series.

### 3.5 Missing physics (no GWL driver)

The prediction pipeline is entirely InSAR-driven. It does not use groundwater level data. At layers with strong GWL-InSAR coupling (F2 at TUKU, detrended r=+0.69), this is defensible because InSAR already encodes the GWL signal through surface deformation. At layers with weak coupling (F3, F4, detrended r<0.07), the InSAR-only model has no physical basis — it predicts subsurface compaction from a surface signal that does not correlate with the subsurface driver.

The IHM-F model exists precisely to address this: it uses GWL as the driver and learns storage coefficients (`S_ke`, `S_kv`, tau) per layer. The prediction pipeline should be framed as a simplified, spatially extensible alternative to IHM-F, not as the primary predictive framework.

**Confidence: HIGH.** The coupling diagnostics from `scripts/11_data_analysis/analyze_correlations.py` are locked and published.

---

## 4. Data Format Verification

Reviewer 3 compared the proposal's file format assumptions against actual file contents on disk. Table below summarizes mismatches.

| File in proposal | Proposal assumption | Actual content | Severity | Fix |
|------------------|-------------------|----------------|----------|-----|
| `direct_ratio_stats.csv` | Per-layer `f_k` | Per-depth `f_median` (60 rows of 5m intervals) | MODERATE | Use `fbar` from `reconstruction_metrics.csv` instead |
| `reconstruction_metrics.csv` | Has `r1_bar`, `dphi1_bar_days` columns | Has `station, layer, fbar, RMSE_tier1_mm, RMSE_tier2_mm, R2_tier1, R2_tier2, RMSE_seasonal_mm, R2_seasonal, seasonal_applied` | MODERATE | Update column name references in `io_loader.py`. `r1_bar` is not stored — compute from amplitude ratio data |
| `step3_phase_stability_summary.csv` | Expected amplitude fields | Has `mean_r1` (amplitude ratio), `A1_mm_mean` (MLCW amplitude), `corr_A1k_A1x` | MINOR | Rename references in loader. More columns available than expected — good |
| `step2_insar_harmonic_decomposition.csv` | Per-layer `A1_x` | Single row (station-level), columns: `A1_x_mm, phi1_x_min_doy, A2_x_mm, phi2_x_max_doy, R2_insar_full, atm_flag, phi1_x_rad, phi2_x_rad` | MODERATE | One InSAR harmonic applies to all layers. Read once per station, broadcast to layers |
| `mlcw_interp_insar_IDW_extend.feather` | Index = Ename, units = mm | RangeIndex (0-38), Ename is column. Data values are in meters (mean magnitude ~0.003-0.010), not mm | MODERATE | Load by `f.set_index('Ename')`. Multiply data columns by 1000 for mm |
| `gridpnt_500m_interp_insar_IDW_extend.feather` | Has `X_UTM50N, Y_UTM50N` | Has `X_TWD97, Y_TWD97` (no UTM columns) | MODERATE | Use TWD97 columns. Verify that UTM zone assignment can be derived from TWD97 (TWD97 is Taiwan-specific, not UTM) |
| `ZONE_ASSIGNMENT_CSV` | Exists at expected path | **Does not exist** | MAJOR | Create from Azeriansyah et al. (2025) polygon data or drop zone-stratified kriging |

**Unit conversion is load-bearing.** If InSAR feather data is in meters (three decimal places: min 0.003 m = 3 mm), then `f_k x 0.003` yields compaction in millimeters. The proposal implicitly assumes mm units throughout. Loaders must multiply by 1000.

**Confidence: HIGH** (all verified on disk).

---

## 5. Spatial Kriging Feasibility

Spatial kriging is the most complex and most blocked component of the pipeline.

### Blocked dependencies

1. **Zone assignment CSV does not exist.** The Azeriansyah et al. (2025) zone polygons — the stratification variable that determines which kriging method applies — have no digital representation in this repository. No shapefile, no CSV mapping 37 stations to zones I-IV. Creating this requires either digitizing from the published map or transcribing zone assignments from the original paper. Estimated effort: 3-6 hours.

2. **GWL trend covariate unavailable.** Zones III and IV use "kriging with external drift" with GWL trend as the drift variable. This requires a GWL trend surface estimated at 8,577 grid points. The data exists (306 wells, long-term records) but the interpolation is not done. Estimated effort: 4-8 hours for a basic IDW surface, longer for a secondary kriging pass.

### Inter-layer coupling as stratification variable

The proposal uses inter-layer coupling strength (from the ring cross-correlation analysis) as the stratification variable. This is a vertical property — it measures how MLCW ring displacements within a column correlate across depths. Kriging is a horizontal interpolation method. No hydrogeological principle connects a station's vertical coupling structure to the spatial continuity of its `f_k` value. The zone boundaries would create artificial discontinuities in the predicted `f_k` field.

**Fix:** Test whether zone stratification improves kriging cross-validation scores before committing to it. If not, use a single kriging method across all stations. This avoids the zone boundary issue entirely.

**Confidence: HIGH** (Reviewers 1 and 5 independently identify this).

### Library and environment

`pykrige` version 1.7.3 is available in the `isce_ncu3` conda environment. The `fafalab` environment does not exist on this VM. All 37-station harmonic batch runs and kriging must use `isce_ncu3`, not `fafalab`.

### Variogram complexity

Sixteen variograms are required (4 zones 4 layers). Small zones (5-8 stations in each of zones I and IV) require manual variogram fitting — `pykrige`'s automatic fitting is unreliable with fewer than 10 points. The fallback to IDW (logged as WARNING) is correct for these cases, but IDW has no uncertainty estimate.

**Estimated effort for `spatial_kriging.py`:** 15-22 hours (assuming inputs exist). Plus 3-6 hours for zone digitization and 4-8 hours for GWL surface creation. Total spatial pathway: 22-36 hours.

**Confidence: MEDIUM.** The effort estimate assumes no unexpected difficulty with TWD97-to-UTM coordinate transformation or variogram fitting edge cases.

---

## 6. IHM-F v3 Status

Reviewer 4 discovered that IHM-F v3 — the joint constrained inversion that uses GWL-only drivers — already exists as working code. This contradicts the pipeline status in `CLAUDE.md`, which lists v3 as "Pending."

**Existing artifacts (verified on disk):**

| File | Path | Lines | Date |
|------|------|-------|------|
| `ihmf_io_multilayer.py` | `scripts/10_ihmf/ihmf_io_multilayer.py` | 113 | May 29 |
| `ihmf_model_v3.py` | `scripts/10_ihmf/ihmf_model_v3.py` | 514 | May 29 |
| TUKU v3 results | `results/ihmf/v3/TUKU_v3_results.json` | 13 KB | May 29 |

**TUKU v3 pilot results (from JSON):**

| Metric | Value | Assessment |
|--------|-------|-----------|
| R2_insar | -6.48 | Negative — model worse than mean predictor |
| T (epochs fitted) | 58 | Should be ~700+ (full 10-year record at 5-day intervals) |
| alpha | 0.01 | Very small — suggests scaling mismatch |
| tau_max | 73 | Search window ~1 year at 5-day intervals (should be longer) |
| rmse_mlcw | 0.90 mm | Reasonable |
| rmse_insar | 187 mm | Catastrophic — indicates InSAR reconstruction failure |

**Diagnosis:** The model successfully fits MLCW (rmse_mlcw = 0.9 mm) but catastrophically fails on InSAR reconstruction (rmse_insar = 187 mm, R2 = -6.48). The T=58 epochs versus expected ~700 suggests the GWL-MLCW-InSAR alignment produces a very short common timeline. The alpha=0.01 allocation of variance to the InSAR constraint means the solver effectively ignores it.

**PROGRESS.md is stale.** It lists v3 as "Pending — next step (IHM-F track)" when the code exists and has been run with a known scaling bug. This should be updated.

**Value ranking (per Reviewer 4):**
1. **IHM-F v3 debug** — highest scientific value. Produces physical parameters ($S_{ke}$, $S_{kv}$, tau, alpha) for 191 station-layer pairs.
2. **37-station harmonic batch** — high value, low risk, unlocks Tier 2.
3. **Prediction pipeline** — medium value, high risk (blocked on multiple dependencies).
4. **Documentation polish** — low value, low risk.

**Confidence: HIGH.** All file paths and line counts verified. R2_insar and T values read directly from the JSON output.

---

## 7. Consolidated Assessment

### 7.1 What works in the proposal

- **Walk-forward temporal validation design** is sound. Four-fold hold-out (2022-2025), separate reporting of fold 1, per-fold `f_k` re-estimation — all correct practices.
- **Module separation** (`io_loader.py`, `walkforward.py`, `reporter.py`) follows the project's established pattern (one job per module, no circular imports).
- **CLI design** (MintPy-style argparse with `--skip-kriging` for tiered execution) is practical and testable.
- **Path resolution** via project-level `paths.py` is mandatory and correctly specified.
- **Tier 2 seasonal flag** is correctly data-driven (not hardcoded station names) — once the gate bug is fixed.
- **Anchored OLS `f_k`** from `reconstruction_metrics.csv` is the correct source (see section 3.1) — the proposal just looks at the wrong file.

### 7.2 What must be fixed before implementation

1. **F1 seasonal gate bug (CRITICAL):** Add `corr_A1k_A1x > 0.0` to the phase stability gate. Re-run the 3-station reconstruction. This changes `seasonal_applied` values for F1 at TUKU and potentially other stations.

2. **$f_{k}$ source correction (HIGH):** Use `reconstruction_metrics.csv` `fbar` column, not `direct_ratio_stats.csv` `f_median`. Update `io_loader.py` function signatures accordingly.

3. **InSAR feather unit correction (HIGH):** Data is in meters. Multiply by 1000 in the loader. Verify that no other script in the pipeline has the same bug.

4. **Grid feather coordinate columns (HIGH):** Proposal assumes `X_UTM50N, Y_UTM50N`. Actual columns are `X_TWD97, Y_TWD97`. The kriging implementation must handle TWD97 coordinates or convert to UTM.

5. **Zone assignment CSV (MAJOR):** Does not exist. Create it or drop zone-stratified kriging. The proposal cannot proceed with zone-stratified kriging until this file exists.

6. **Seasonal double-counting (MEDIUM):** Decompose InSAR into trend + seasonal components. Use trend only in Tier 1. This requires adding an InSAR detrending step to the pipeline.

7. **Baseline definition (MEDIUM):** Add trend-extrapolation baseline alongside the no-change anchor baseline. Report both skill scores.

8. **File format documentation (MEDIUM):** Update the module contracts in the proposal to match actual column names and data types. The current proposal references columns that do not exist.

### 7.3 What should be dropped or deferred

1. **Zone-stratified kriging (DEFER to post-deadline):** Blocked on missing zone CSV, GWL covariate, and the unresolved question of whether vertical inter-layer coupling is a valid horizontal stratification variable. The 22-36 hour effort estimate plus unknown zone digitization time makes this infeasible within a one-week deadline. Replace with ordinary kriging (no stratification) for the MVP.

2. **Spatial LOO-CV (DEFER to post-deadline):** Depends on kriging. If zone-stratified kriging is deferred, LOO-CV over 36 stations with ordinary kriging is straightforward but adds 4-6 hours.

3. **GWL covariate kriging (DEFER to post-deadline):** Producing a GWL trend surface at 8,577 grid points from 306 wells is a separate project. It should not block the temporal validation pipeline.

4. **Tier 2 for non-F2 layers (DROP permanently):** The locked findings from `13_seasonal_insar/` show that F3 and F4 seasonal phase std > 59 days at all pilot stations. Non-F2 seasonal cannot be recovered. The pipeline should apply Tier 2 only to F2 and only where `seasonal_applied=True` passes the corrected gate.

---

## 8. Additional Issues (Blind Spots)

The five primary reviewers focused on scientific correctness, feasibility, data formats, strategy, and spatial kriging. A sixth reviewer searched for gaps none of the first five covered. Seven issues emerged.

### 8.1 A₁_x(t) is not a pre-computed file (CRITICAL)

The Tier 2 equation is:

```
Ŷ_k(t) = f̄_k × x(t) + r̄₁_k × A₁_x(t)
```

where `A₁_x(t)` is "InSAR annual harmonic component at epoch t." This is a **time series** across ~785 epochs, not a scalar. No existing output file contains it:

- `reconstruction_metrics.csv` stores scalar `r̄₁_k`, not `A₁_x(t)`
- `step3_phase_stability_summary.csv` stores `mean_r1` per layer, not `A₁_x(t)`
- No script in `scripts/13_seasonal_insar/` exports the InSAR harmonic timeseries

The pipeline must recompute the annual harmonic — the exact logic from `scripts/13_seasonal_insar/`, violating the scope boundary ("zero modification to past codebase, reads outputs from existing scripts"). Tier 2 cannot run without this data.

**Fix:** Add a step to `scripts/13_seasonal_insar/` that exports the InSAR annual harmonic component timeseries as a feather file. Reference it as a required upstream input.

### 8.2 No graceful degradation in batch mode (CRITICAL)

Every `io_loader.py` function says "raise on missing files." The `main.py` orchestrator has no try/except. One missing `reconstruction_metrics.csv` for any of 37 stations terminates the entire run. In the current state (34 stations with no harmonic files), batch mode is unusable.

**Fix:** Wrap per-station processing in try/except in `main.py`. Log WARNING with station name and missing file path. Continue to next station. Write `stations_skipped.csv` listing excluded stations and reasons. Make Tier 2 conditional: if harmonic files are missing, drop Tier 2 and set `tier2_available=False`.

### 8.3 The 37-vs-39 station gap (HIGH)

The proposal assumes 37 stations. But JINHU_XIN and LUNFENG_XIN have InSAR data and direct_ratio data but no grouped MLCW data. `--stations all` will crash when `load_fbar()` succeeds but `run_walkforward` finds no MLCW grouped file. No station-skip mechanism exists.

**Fix:** Add a station-filtering step in `main.py` that logs WARNING and skips stations without MLCW grouped data. Document that the pipeline covers 37 stations with the 2 excluded stations listed in `stations_skipped.csv`.

### 8.4 f̄_k re-estimation design contradiction (HIGH)

Section 4.3 states `run_walkforward` will re-estimate f̄_k per fold. But `load_fbar()` returns a pre-computed f_median from the full record. The walk-forward module receives InSAR and MLCW series — implying re-computation — but has no function to do it. The proposal has no `compute_fbar_from_scratch()` or `depth_to_layer()` function. Either `load_fbar` is dead code or the per-fold re-estimation is impossible.

**Fix:** Either add per-fold f̄_k computation logic (with depth-to-layer aggregation from classify table) or freeze f̄_k from the full record and remove the "re-estimated per fold" claim.

### 8.5 `seasonal_applied=True` with R^2_seasonal $\le$ 0 degrades Tier 2 (HIGH)

The pipeline blindly applies Tier 2 wherever `seasonal_applied=True`. But F1 at TUKU has `seasonal_applied=True` with `R²_seasonal = −0.105`. The pipeline will silently deploy a Tier 2 prediction worse than Tier 1 for any layer where the flag is True but R^2_seasonal $\le$ 0. This is distinct from the gate bug (Section 3.2) — even after fixing the gate, other stations may have the same problem.

**Fix:** Add a runtime guard in `io_loader.py` or `walkforward.py`: override `seasonal_applied = False` wherever `R²_seasonal ≤ 0.0`. Log WARNING each time.

### 8.6 No testing or validation strategy (HIGH)

For a 6-module pipeline producing publication-quality metrics, the proposal specifies only one verification point (check TUKU F2 2022 RMSE_baseline $\approx$ 3.495 mm). No unit tests, no integration test, no schema validation, no dry-run mode. Column name mismatches (Section 4) are discovered at runtime, not at import time.

**Fix:** Add: (a) `--check-inputs` flag that validates file existence and column schemas before computation, (b) schema validation in `io_loader.py` that checks expected columns exist, (c) one integration test on TUKU verifying output CSV structure and approximate RMSE values.

### 8.7 CLI flag conflict: `--krige none` vs `--skip-kriging` (MEDIUM)

Two mechanisms to skip kriging: `--krige {zone_stratified,ordinary,idw,none}` and `--skip-kriging`. These overlap semantically. What happens with `--krige ordinary --skip-kriging`? Eight possible flag combinations, at least three contradictory. The orchestrator has no defined behavior for these.

**Fix:** Remove `--skip-kriging`. Use `--krige none` as the canonical skip. Validate mutual exclusivity in `main.py`.

---

## 9. Recommendations

### 9.1 Decision Table

| Action | Decision | Rationale |
|--------|----------|-----------|
| Debug IHM-F v3 joint solver (R^2_insar = −6.48) | **DO** | Code exists. The solver produces T=58 epochs (should be ~700+) and $\alpha$=0.01. Likely a units mismatch: InSAR feather stores metres, MLCW stores mm. Fix units first. |
| Run all-stations seasonal harmonic batch | **DO** | Gate passed at 3 stations. Run `01_seasonal_harmonic_analysis.py` for all 37 stations. Unblocks Tier 2. |
| Create zone assignment CSV | **DO** | Map 37 stations to Azeriansyah zones I-IV. 2-hour GIS task. Required for any future spatial work. |
| Aggregate f̄_k from depth-rings to layers | **DO** | Join `direct_ratio_stats.csv` with classify table. Weight f_median by ring thickness per layer. Or use `fbar` from `reconstruction_metrics.csv` directly. |
| Fix F1 seasonal gate bug | **DO** | Add `corr_A1k_A1x > 0.0` to phase gate. Re-run 3-station reconstruction. |
| Export InSAR harmonic timeseries | **DO** | Add to `scripts/13_seasonal_insar/`. Required for Tier 2 — A₁_x(t) does not exist anywhere. |
| Implement prediction pipeline (6 modules) | **DO NOT** | Three critical inputs missing. Code without test data guarantees bugs. |
| Zone-stratified kriging | **DO NOT** | Blocked on zone polygons + GWL surface. No physical rationale for coupling zones as kriging strata. |

### 9.2 Seven-Day Action Plan (June 1–7)

**Day 1 — Fix IHM-F v3 joint solver:**
Verify units in the design matrix. The InSAR feather stores values in metres. The solver parameter is named `insar_mm`. Add explicit conversion: `insar_mm = insar_metres × 1000.0`. Activate the lambda weight parameter (`lam = 1/N` to balance MLCW and InSAR objective terms). Target: R^2_insar > 0.3.

```
PYTHONPATH="" conda run -n isce_ncu3 python scripts/10_ihmf/fit_ihm_f.py --station TUKU --all
```

**Day 2 — Run all-stations seasonal harmonic batch:**
Loop `01_seasonal_harmonic_analysis.py --station {name}` over all 37 stations. Fix the F1 gate: add `corr_A1k_A1x > 0.0`. Re-run TUKU, XIUTAN, YUANCHANG. Export InSAR harmonic timeseries A₁_x(t) as a feather file.

**Day 3 — Aggregate f̄_k and create zone CSV:**
Write aggregation script: join `direct_ratio_stats.csv` with classify table, weight by ring thickness per layer. Output `f_bar_by_layer.csv`. Create `station_zone_assignments.csv` from Azeriansyah zone map. Report station count per zone.

**Day 4 — IHM-F v3 TUKU pilot, verified:**
Run joint solver on all 6 TUKU layers. Check: $S_{k}$ values positive and physically plausible, R^2_insar > 0.7, RMSE_mlcw comparable to tau_demo_TUKU baseline. Run walk-forward validation.

**Day 5 — Seasonal reconstruction visualization, all stations:**
Batch `02_reconstruction_visualization.py` for all 37 stations. Verify Tier 2 only activates for F2 (and only where seasonal_applied=True with R^2_seasonal > 0).

**Day 6 — Update PROGRESS.md and documentation:**
Sync PROGRESS.md with actual v3 code state. Update CLAUDE.md with new findings. Fix ring_cross_correlation.py path (line 66: `modeled` → `reconstr`).

**Day 7 — Build MVP prediction pipeline (Tier 1 only):**
Single script (~200 lines), not 6 modules. Walk-forward on all 37 stations, Tier 1 only, no kriging. Output: `walkforward_rmse.csv` + 1 heatmap. Two baselines: persistence + trend-extrapolation.

### 9.3 Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| IHM-F v3 R^2 stays negative after unit fix | Medium | High | Print design matrix shapes and value ranges before solve. Verify MLCW/InSAR row weighting via lam. |
| Fewer than 5 stations per zone | High | High | Default to ordinary kriging without zones. Do not use zone-stratified kriging if zone counts are unbalanced. |
| Harmonic batch reveals new failure modes | Medium | Medium | If station fails phase gate, set seasonal_applied=False and continue. Expected: F2 passes at most stations, F3/F4 fail everywhere. |
| f̄_k aggregation reveals bias in thin-layer rings | Low | Medium | Compare thickness-weighted vs unweighted mean. Document difference if >10%. |
| Disk space for 37-station figures | Low | Low | ~6 MB per station $\times$ 37 $\approx$ 220 MB. Acceptable. |

### 9.4 Long-Term Guidance

Return to the full prediction pipeline only after:
1. IHM-F v3 produces R^2_insar > 0 at all 6 TUKU layers
2. The all-stations seasonal harmonic batch completes
3. The zone assignment CSV and InSAR harmonic timeseries exist

Design changes for the pipeline when revisited:
- **Decompose InSAR into trend + seasonal.** Tier 1 uses trend only. Tier 2 adds seasonal. This resolves the double-counting issue.
- **Drop zone-stratified kriging.** Use ordinary kriging without strata unless cross-validation shows stratification improves scores. The Azeriansyah coupling zones lack physical justification as kriging strata.
- **Make modules independently callable.** The user runs walk-forward first, inspects results, then decides whether to krige. Do not hardcode a 6-step sequence.
- **Separate spatial kriging into its own pipeline.** The spatial extension is a separate research question requiring its own analysis. Bundle it with Stage 2, not temporal validation.
- **Add graceful degradation.** Per-station try/except. Tier 2 conditional on data availability. `stations_skipped.csv` for audit.

---

## 10. References

- **Proposal document:** `discussions/discussion_20260601_prediction_pipeline_design.md` — specifies 6-module architecture, four-fold walk-forward, zone-stratified kriging
- **IHM-F v3 code:** `scripts/10_ihmf/ihmf_io_multilayer.py` (113 lines, May 29), `scripts/10_ihmf/ihmf_model_v3.py` (514 lines, May 29) — existing joint constrained inversion
- **IHM-F v3 results:** `results/ihmf/v3/TUKU_v3_results.json` — R2_insar = -6.48, T = 58, scaling bug
- **Seasonal harmonic analysis:** `scripts/13_seasonal_insar/01_seasonal_harmonic_analysis.py` — 3-station pilot complete, all 3 pass phase stability gate
- **Seasonal reconstruction metrics (TUKU):** `results/seasonal_insar_harmonic/TUKU/reconstruction_metrics.csv` — per-layer fbar, R2_tier1, R2_tier2, seasonal_applied flags
- **Phase stability summary (TUKU):** `results/seasonal_insar_harmonic/TUKU/step3_phase_stability_summary.csv` — F1 corr_A1k_A1x = -0.827, gate miss
- **InSAR harmonic decomposition (TUKU):** `results/seasonal_insar_harmonic/TUKU/step2_insar_harmonic_decomposition.csv` — single-row, station-level A1_x
- **Direct ratio stats (TUKU):** `results/direct_ratio/TUKU/TUKU_direct_ratio_stats.csv` — per-depth f_median at 5m intervals, not per-layer
- **InSAR station feather:** `data/insar/timeseries/mlcw_interp_insar_IDW_extend.feather` — 39 rows x 791 cols, RangeIndex, Ename as column, meters not mm
- **InSAR grid feather:** `data/insar/timeseries/gridpnt_500m_interp_insar_IDW_extend.feather` — 8,577 rows, X_TWD97/Y_TWD97 coordinates, no UTM columns
- **Locked decisions (CLAUDE.md):** Sign conventions, figure standards (A4 landscape, 300 dpi), F/T naming rules, detrending module (`ihmf_detrend.py`), tau search lessons
- **Correlation diagnostics:** `results/prestage_data_analysis/correlation_matrix.csv` — F2 detrended r=+0.69, F3/F4 detrended r<0.07
- **Project progress tracker:** `D:\112_PROJECT_002\PROGRESS.md` — currently lists IHM-F v3 as "Pending" (stale — must be updated)
