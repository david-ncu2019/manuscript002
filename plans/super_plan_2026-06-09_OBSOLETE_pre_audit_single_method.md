# Super Plan — InSAR-MLCW Subsidence Monitoring Gap-Fill and Prediction

> **For agentic workers:** REQUIRED: Read PROGRESS.md and CLAUDE.md before executing any task. Use `$env:PYTHONPATH=""; conda run -n fafalab python <script>` for all Python calls. Never use gemini_env or isce_ncu3 for IHM-F work.

**Goal:** Reconstruct broken MLCW (Multi-Layer Compaction monitoring Well) records, predict future compaction per layer, and extend spatial coverage to unmonitored grid points using InSAR (Interferometric Synthetic Aperture Radar), GWL (groundwater level), and borehole stratigraphy.

**Method under evaluation:** Terzaghi consolidation theory formulated as a cumulative two-regressor NNLS (Non-Negative Least Squares) — Script 12 (`tau_demo_TUKU/12_stress_strain_per_layer.py`). Not confirmed until Part 0 validation gate passes.

**Tech stack:** Python 3.10 (fafalab), scipy.optimize.nnls, pandas, feather format, PowerShell on Windows 10.

---

## Top-Level Milestone Summary Table

| Milestone | Description | Depends On | Estimated Effort (hours) | Scope |
|-----------|-------------|------------|--------------------------|-------|
| **M0** | Part 0 — Method Validation Gate | — | 12 h | Week 1 |
| **M1** | Part 1 — Obj 1: TUKU Pilot Gap-Fill + Prediction | M0 PASS | 20 h | Week 1–2 |
| **M2** | Part 2 — Obj 2: Multi-Well Extension (37 stations) | M1 | 16 h | Follow-on |
| **M3** | Part 3 — Obj 3: Regional Grid Prediction (8,577 pts) | M2 | 32 h | Follow-on |
| **M4** | Part 4 — Guardrails Wiring | M0 PASS (ongoing) | 6 h | Continuous |
| **M5** | Part 5 — Publication-Ready Outputs | M2, M3 | 20 h | Follow-on |

**One-week hard constraint:** M0 + M1 must complete within the current working week. M2–M5 are follow-on.

**Physical narrative:** The Choushui River Alluvial Fan (CRAF) sediment column compresses in response to declining piezometric head in confined aquifers. MLCW instruments that measured this layer-by-layer are being shut down. The cumulative two-regressor NNLS model derives skeletal storage coefficients ($S_{ke}$, $S_{kv}$) from the historical head record, retaining Terzaghi preconsolidation stress memory via the running minimum $V(t)$. This memory — absent from the failed incremental solver — is the mechanism that allows gap-fill across periods with no MLCW data.

---

## PART 0 — Method Validation Gate

**Purpose:** Confirm that the Script 12 cumulative solver can gap-fill MLCW on held-out data at TUKU before any further development. The incremental IHM-F v3 solver failed ($R^2_{\text{MLCW,cum}}$ negative or NaN for all 6 layers; 8–355× prediction gap documented 2026-06-08). Script 12 passes the physical ratio gate on 3 of 6 layers (F1=9.1×, T2=9.3×, F4=17.3×). The held-out test must cover only those three layers in the first instance.

### PHASE 0.1 — Design the Held-Out Evaluation Protocol

#### TASK 0.1.1 — Define the calibration/held-out split

**Physical meaning:** The clay and sand layers in the sediment column accumulated most of their inelastic strain during the pre-2015 era of intense groundwater extraction. Post-2015, head levels oscillate around a partial recovery trend. To test gap-fill, we need a contiguous **interior segment** where MLCW data exists on both sides so the static linear interpolation baseline is defined.

- [ ] Step A: Read the TUKU MLCW cleaned file `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\tau_demo_TUKU\data\TUKU_reconst_grouped_cleaned.csv`. Identify the date range where all 6 layers have valid MLCW observations. Print first and last valid epoch per layer.
  - **Success check:** Start date ≤ 2015-06-01; end date ≥ 2023-12-31 for F1, T2, F4.
  - **Command:** `$env:PYTHONPATH=""; conda run -n fafalab python -c "import pandas as pd; df=pd.read_csv(r'D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\tau_demo_TUKU\data\TUKU_reconst_grouped_cleaned.csv',parse_dates=['date']); print(df.groupby('date')[['F1','T2','F4']].count().iloc[[0,-1]])"` (adjust column names to actual schema)
  - **Depends on:** — (root task)

- [ ] Step B: Define a held-out interior window of 18 months — from 2021-01-01 to 2022-06-30. The calibration window is all epochs before 2021-01-01. The evaluation window is 2021-01-01 through 2022-06-30. A validation tail (2022-07-01 onward) is retained for Part 1 next-month prediction test.
  - **Physical rationale:** 18 months spans at least one full annual head cycle, testing whether the model captures both the elastic rebound (head rising in wet season) and inelastic exceedance (head setting new lows in dry season) at intra-annual resolution.
  - **Success check:** Calibration window contains ≥ 1,500 epochs; held-out window contains ≥ 108 epochs (18 months × ~6 per month at 5-day cadence).

- [ ] Step C: Document the split in a plain text file `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\tau_demo_TUKU\data\holdout_split_definition.txt` with four lines: CALIB_START, CALIB_END, HOLDOUT_START, HOLDOUT_END in ISO 8601 format.
  - **Success check:** File exists; CALIB_END = 2020-12-31; HOLDOUT_START = 2021-01-01.

> **DECISION POINT 1 (data sufficiency):**
> - **PASS:** All three gate-passing layers (F1, T2, F4) have ≥ 108 valid held-out MLCW epochs. Proceed to TASK 0.1.2.
> - **FAIL:** One or more layers have < 108 valid held-out epochs. Shorten the held-out window to 12 months (2021-01-01 to 2021-12-31) and recheck. If still < 72 epochs (12 months), record the layer as data-insufficient and exclude from evaluation; flag in PROGRESS.md.

---

#### TASK 0.1.2 — Build the held-out gap-fill evaluator script

**Physical meaning:** The script applies the $b_j(t) = S_{ke} H_j(t) + (S_{kv} - S_{ke}) V_j(t)$ model — fit on calibration epochs only — to the held-out window. Because $V(t) = \min(0, \text{cummin}(H_j(t)) - h_{c,j})$ carries the running minimum of head across the calibration/held-out boundary, the preconsolidation stress memory accumulated before 2021 automatically flows into the held-out prediction without any data leakage. This is the property that distinguishes the cumulative solver from the failed incremental solver.

**Depends on:** TASK 0.1.1 complete; split definition file written.

- [ ] Step A: Create script `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\tau_demo_TUKU\13_holdout_gap_fill_eval.py`. The script must:
  - Load MLCW and GWL timeseries for F1, T2, F4 (using the feather paths already defined in Script 12 header).
  - Split by the dates in `holdout_split_definition.txt`.
  - Fit NNLS coefficients ($S_{ke}$, $S_{kv}$) on calibration window only.
  - Apply fixed coefficients to held-out $H$ and $V$ arrays (no re-fitting).
  - Compute gap-fill RMSE on held-out MLCW observations.
  - Compute the static linear interpolation baseline: straight line from the last calibration epoch MLCW value to the first post-held-out epoch MLCW value.
  - Compute baseline RMSE over the same held-out window.
  - Compute walk-forward skill score: $\text{skill} = 1 - \text{RMSE}_{\text{model}} / \text{RMSE}_{\text{baseline}}$.
  - Save results to `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\tau_demo_TUKU\results\holdout_eval_results.json`.
  - **Must import:** `from scripts.guardrails import validate_layer_params, validate_sign_constraints` — call before saving any parameters.
  - **Success check:** Script runs without errors; JSON file written with keys `F1`, `T2`, `F4` each containing `rmse_model`, `rmse_baseline`, `skill_score`, `S_ke`, `S_kv`, `ratio`.
  - **Command:** `$env:PYTHONPATH=""; conda run -n fafalab python tau_demo_TUKU/13_holdout_gap_fill_eval.py`

- [ ] Step B: Verify the guardrail calls produce no fatal violations for F1, T2, F4 on calibration-window parameters. Print the full guardrail report.
  - **Success check:** `validate_sign_constraints` passes ($S_{ke} \ge 0$, $S_{kv} \ge S_{ke}$); `validate_ratio_gate` shows 3×PASS for the three gate-passing layers.

- [ ] Step C: Read back `holdout_eval_results.json` and print a formatted table: Layer | $S_{ke}$ | $S_{kv}$ | Ratio | RMSE_model (mm) | RMSE_baseline (mm) | Skill Score.
  - **Success check:** Table printed without KeyError; ratio values match previously recorded values (F1≈9.1×, T2≈9.3×, F4≈17.3×) to within 5% (calibration-window-only fit may differ slightly from full-record fit).

---

#### TASK 0.1.3 — Evaluate gap-fill results and record decision

**Physical meaning:** A positive skill score means that knowing the Terzaghi consolidation relationship between piezometric head and compaction is more informative than assuming the sediment column compacted at a constant rate during the gap. A negative skill score means the physical model adds no information over simple interpolation.

**Depends on:** TASK 0.1.2 complete; `holdout_eval_results.json` written.

- [ ] Step A: Compare model RMSE to baseline RMSE per layer. Compute skill score for each of F1, T2, F4.
  - **Success check:** Skill scores are finite numbers (not NaN, not ±inf).

- [ ] Step B: Record the result in PROGRESS.md under §4 (Blocking Decision). Add a row to the gap-fill evaluation criteria table with today's date, the three skill scores, and the PASS/FAIL verdict.
  - **Success check:** PROGRESS.md contains a line with date 2026-06-09 and three numeric skill scores.

> **DECISION POINT 2 (method validation gate — the primary gate):**
> - **PASS condition:** RMSE_model < RMSE_baseline (skill > 0) for all three gate-passing layers (F1, T2, F4). Proceed to PART 1.
> - **PARTIAL PASS condition:** Skill > 0 for ≥ 2 of 3 layers. Proceed to PART 1 with a note that the failing layer is flagged for investigation in TASK 1.2.3.
> - **FAIL condition:** Skill ≤ 0 for 2 or more layers. Do NOT proceed to PART 1. Execute the FAIL branch below.

> **FAIL branch (data-driven fallback sketch — outline only, not implemented here):**
> If Script 12 cumulative solver fails the held-out gap-fill gate, three fallback approaches are available:
>
> **Fallback A — Gradient Boosted Trees (GBT) with lagged GWL features:**
> A gradient boosted regressor (scikit-learn GradientBoostingRegressor or XGBoost) takes as inputs the GWL level at lags {0, τ_opt, 2τ_opt} plus the cumulative head exceedance $\min(0, H - h_c)$ as a preconsolidation proxy. Trained on calibration window; evaluated on held-out. No physical parameter interpretation, but may capture non-linear compaction dynamics that the two-regressor NNLS misses. Feasibility: data available for all 6 layers at TUKU; training set ~1,500 rows; no new data collection needed.
>
> **Fallback B — Gaussian Process Regression (GPR) with head kernel:**
> A GPR with a Matérn 3/2 kernel over the GWL head as input captures the smooth stress-strain relationship without requiring a two-regime parameterization. Uncertainty bounds come for free as posterior variance. Requires scikit-learn (available in fafalab). Risk: kernel hyperparameter instability with few inelastic epochs (F2: only 2 inelastic in incremental domain; cumulative may be larger).
>
> **Fallback C — MLCW trend extrapolation with InSAR correction:**
> Fit a linear trend to the calibration MLCW, then use InSAR anomaly (InSAR(t) − InSAR_trend(t)) scaled by the training-window $\bar{f}_k$ ratio to correct the trend extrapolation. This is a soft upgrade of the failed static scaling method. Expected to fail on F2/F3/F4 (where InSAR correlation is known to be negative) but may work for F1/T2.
>
> **Decision procedure for fallback selection:** Run all three fallbacks on the same held-out window as TASK 0.1.2. Select the method with the highest mean skill score across F1, T2, F4. If all fallbacks fail, expand the calibration window and retry before concluding the method family is inappropriate.

---

### PHASE 0.2 — Physical Sanity Check Before Proceeding

#### TASK 0.2.1 — Confirm calibration-window parameters satisfy guardrails

**Physical meaning:** Before using calibration-window $S_{ke}$, $S_{kv}$ values for any prediction, they must satisfy the 10 automated physical-law checks in `scripts/guardrails.py`. A ratio outside [3, 50] on calibration data means the sediment column parameters are implausible under Terzaghi consolidation theory.

**Depends on:** TASK 0.1.2 complete.

- [ ] Step A: Confirm `validate_sign_constraints` passes for F1, T2, F4. Print: `$S_{ke}$ = [value], $S_{kv}$ = [value], ratio = [value]×` for each layer.
  - **Success check:** All three print without GuardrailViolation.

- [ ] Step B: Confirm `validate_ratio_gate` reports PASS (not WARN) for F1, T2, F4 with the calibration-window coefficients.
  - **Success check:** No warnings; ratio values fall within [3, 50] for all three layers.

- [ ] Step C: If F1 ratio changes by more than 20% from the full-record value (9.1×), investigate the cause before proceeding. Print the calibration vs. full-record ratio side-by-side.
  - **Success check:** Ratio change ≤ 20% OR cause documented in a comment block in `13_holdout_gap_fill_eval.py`.

---

## PART 1 — Obj 1: Well-Scale Gap-Fill and Prediction (TUKU Pilot)

**Physical narrative:** Having confirmed that the cumulative NNLS model captures the sediment column's stress history on held-out epochs, the next step is to build a complete gap-fill reconstruction of the TUKU MLCW record — bridging the observation gaps caused by network shutdown — and then extend the model to forward-predict next-month compaction from GWL data alone.

**Depends on:** PART 0 PASS (or PARTIAL PASS).

### PHASE 1.1 — Historical Gap-Fill Reconstruction at TUKU

#### TASK 1.1.1 — Build the full calibration and reconstruction script

**Physical meaning:** The sediment column's compaction history at TUKU can be reconstructed by applying the $S_{ke}$, $S_{kv}$ parameters — calibrated on all available MLCW data — to the continuous GWL record extending before and after gaps in MLCW observations. Each mm of reconstructed compaction represents real pore-space collapse in the clay or sand layers between 19 m and 300 m depth.

**Depends on:** TASK 0.2.1 complete; all guardrails passing for F1, T2, F4.

- [ ] Step A: Read the current Script 12 (`tau_demo_TUKU/12_stress_strain_per_layer.py`) to confirm input/output data structure. Verify that `LAYERS` dict covers F1, T1, F2, T2, F3, F4 with correct `gwl_file`, `h_c`, and `tau_epochs` values from `tau_results.csv`.
  - **Files to read:** `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\tau_demo_TUKU\12_stress_strain_per_layer.py`, `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\tau_demo_TUKU\results\tau_results.csv`
  - **Success check:** Layer list matches: F1, T1, F2, T2, F3, F4; all `gwl_file` paths resolve to existing feather files.

- [ ] Step B: Write script `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\tau_demo_TUKU\14_full_reconstruction_tuku.py` that:
  - Fits $S_{ke}$, $S_{kv}$ on all available MLCW calibration epochs (no held-out split) for all 6 layers.
  - Extends the GWL timeseries beyond the last MLCW observation date using available GWL data.
  - Applies fixed coefficients to the full GWL record (2015-01-16 onward, including MLCW-gap periods) to produce a continuous reconstructed compaction timeseries per layer.
  - Outputs: one CSV file per layer `results/reconstruction/TUKU_{layer}_reconstruction.csv` with columns: `date`, `b_model_mm`, `b_observed_mm` (NaN where MLCW absent), `H_m`, `V_m`.
  - Imports and calls `validate_layer_params` before writing any layer result.
  - **Success check:** 6 CSV files written; no file contains all-NaN `b_model_mm`; all guardrails pass.
  - **Command:** `$env:PYTHONPATH=""; conda run -n fafalab python tau_demo_TUKU/14_full_reconstruction_tuku.py`

- [ ] Step C: Plot the 6-layer reconstruction: modeled vs. observed MLCW compaction as cumulative mm from REF_DATE, with MLCW-gap periods shown as grey shading. Save to `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\tau_demo_TUKU\plots\reconstruction\TUKU_reconstruction_6layer.png`.
  - **Figure standards:** Font ≥ 14 pt; tab10 colors; all axes labeled with units; grid on; tight layout; 300 dpi.
  - **Success check:** PNG file written at ≥ 300 dpi; all 6 subplots visible; modeled and observed lines distinguishable.

---

#### TASK 1.1.2 — Quantify reconstruction quality

**Physical meaning:** The fraction of the total compaction signal that the model captures measures how much of the sediment column's stress-driven deformation is explained by the two-regime Terzaghi model with the TUKU borehole stratigraphy. A low $R^2$ on the calibration window means the model is missing a physical process.

**Depends on:** TASK 1.1.1 complete.

- [ ] Step A: Compute $R^2$, RMSE (mm), and mean bias (mm) between `b_model_mm` and `b_observed_mm` for each layer on the calibration window. Print results.
  - **Success check:** All $R^2 \ge 0$ (guardrail 10 from `guardrails.py`); F1, T2, F4 pass the ratio gate.

- [ ] Step B: Compare $S_{ke}$, $S_{kv}$ values to the previously published full-record Script 12 results in `tau_demo_TUKU/results/stress_strain_per_layer.json`. If any value differs by more than 10%, document the cause.
  - **Success check:** Values match to within 10% OR discrepancy explained in script comments.

---

#### TASK 1.1.3 — Compute gap-fill coverage statistics

**Physical meaning:** The fraction of MLCW-gap epochs covered by the reconstruction measures how completely the monitoring record has been restored. A gap period with no GWL data cannot be reconstructed — this sets an absolute ceiling on gap-fill coverage.

**Depends on:** TASK 1.1.1 complete.

- [ ] Step A: For each layer, count total MLCW-gap epochs and the subset covered by the reconstruction (i.e., GWL data available). Print: Layer | Total epochs | MLCW present | MLCW absent | GWL-covered gap epochs | Gap coverage %.
  - **Success check:** Table printed; gap coverage ≥ 80% for F1 (GWL well HONGLUN active since 2003).

- [ ] Step B: If F2 gap coverage < 50% (expected: GWL well 09050321 started August 2012, leaving 2003–2012 uncovered), record this as a known data ceiling in a comment block in `14_full_reconstruction_tuku.py` and flag in PROGRESS.md.
  - **Success check:** PROGRESS.md updated with F2 coverage percentage and explanation.

---

### PHASE 1.2 — Next-Month Prediction Mode

#### TASK 1.2.1 — Define the forward-prediction API

**Physical meaning:** After fitting $S_{ke}$, $S_{kv}$ on the historical calibration window, the model can predict future compaction if GWL is forecast or observed. Each epoch of forward prediction requires only the lagged GWL value $H_j(t - \tau_j)$ and the current running minimum $V_j(t)$, both of which are determined by prior GWL history. No future MLCW data is needed.

**Depends on:** TASK 1.1.1 complete.

- [ ] Step A: Add a `--predict_to DATE` command-line argument to `14_full_reconstruction_tuku.py`. When this argument is provided, the script uses GWL data from the last calibration epoch through DATE to extend the compaction prediction beyond the last MLCW observation.
  - **Files to modify:** `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\tau_demo_TUKU\14_full_reconstruction_tuku.py`
  - **Success check:** `python 14_full_reconstruction_tuku.py --predict_to 2025-12-31` runs without error and produces an extended timeseries CSV with `b_model_mm` values past the last MLCW observation.

- [ ] Step B: Test by predicting 6 months beyond the last available MLCW observation for TUKU. Save prediction CSV to `results/reconstruction/TUKU_F1_prediction_6mo.csv` (repeat for T2, F4).
  - **Success check:** CSVs exist; predicted values are plausible (within ±50% of the 12-month running mean of the calibration-window compaction rate).

---

#### TASK 1.2.2 — Evaluate prediction skill on a tail hold-out

**Physical meaning:** The tail of the TUKU MLCW record (the last 6 months of observed data) serves as the prediction test set. Predicting this period using only the calibration window and the GWL record demonstrates whether the model can forecast compaction ahead of the monitoring network's last observation.

**Depends on:** TASK 1.2.1 complete.

- [ ] Step A: Identify the last 6 months of available MLCW observations for F1, T2, F4. Define: PREDICT_START = last MLCW date − 6 months; PREDICT_END = last MLCW date. Re-fit calibration on all epochs before PREDICT_START. Predict on [PREDICT_START, PREDICT_END] using GWL only.
  - **Success check:** Re-fit converges; NNLS coefficients are non-negative.

- [ ] Step B: Compute prediction RMSE and skill vs. trend extrapolation (linear trend fitted on calibration window, extended to PREDICT_END). Print: Layer | RMSE_model | RMSE_trend | Skill.
  - **Success check:** Skill > 0 for ≥ 2 of 3 layers (F1, T2, F4).

> **DECISION POINT 3 (prediction skill):**
> - **PASS:** Skill > 0 for ≥ 2 of 3 layers. Proceed to TASK 1.2.3 and TASK 1.3.1.
> - **FAIL:** Skill ≤ 0 for 2 or more layers. Investigate: (a) check if the lag $\tau$ computed on calibration data alone shifts from the full-record $\tau$; (b) check if the running minimum $V(t)$ computed on calibration data diverges from full-record $V(t)$ in the prediction window. Document findings in PROGRESS.md. Do not proceed to batch extension (PART 2) until this is resolved.

---

#### TASK 1.2.3 — Investigate layers that fail the prediction gate

**Physical meaning:** Layers T1, F2, and F3 failed the physical ratio gate in the full-record fit (T1=2.9×, F2=221×, F3 $S_{ke}$=0). Their failure may reflect physical mechanisms outside the Terzaghi two-regime model — for example, F2 contains only 2 inelastic epochs in the incremental domain (GWL well 09050321 started 2012) and F3 is a deep aquifer where the head signal is poorly coupled to surface InSAR. Document the failure mode per layer.

**Depends on:** TASK 1.2.2 complete.

- [ ] Step A: For each of T1, F2, F3 — print the calibration-window inelastic epoch count (epochs where $H < h_c$), the ratio $S_{kv}/S_{ke}$, and the $R^2$ on calibration window. Identify the dominant failure mode.
  - **Success check:** Table printed with: Layer | $n_{inelastic}$ | $S_{kv}/S_{ke}$ | $R^2_{calib}$ | Failure mode label.

- [ ] Step B: For T1 — check whether the TUKU borehole log confirms T1 is a thin aquitard (7.423 m clay at TUKU per borehole `YL_WSYL23G1_TUKU`). If T1 compressible thickness is ≤ 8 m, record as a data-limited layer (too thin for reliable storage coefficient separation).
  - **Files to check:** `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\data\mlcw\borehole_materials\YL_WSYL23G1_TUKU_土庫.xlsx` (if parseable), or `figures/prestage_data_analysis/layer_thickness_borehole_TUKU.csv`.
  - **Success check:** T1 aquitard_m value confirmed from borehole; match to CLAUDE.md §Known Issues entry (7.423 m).

- [ ] Step C: Add a `layer_status` key to `holdout_eval_results.json` with entries: `{layer: "PASS"/"FAIL_ratio"/"FAIL_data_limited"/"FAIL_prediction"}` for all 6 layers.
  - **Success check:** JSON updated; all 6 layers have a status entry.

---

### PHASE 1.3 — Self-Recalibration

#### TASK 1.3.1 — Build the recalibration mode

**Physical meaning:** When field crews collect a new sparse in-situ MLCW measurement (e.g., a semi-annual visit to a station that now operates at reduced frequency), that new data point should be used to update (not replace) the model's calibration window. Expanding the calibration window may shift the preconsolidation threshold $h_c$ if a new minimum head was recorded since the previous calibration.

**Depends on:** TASK 1.1.1 complete.

- [ ] Step A: Add a `--recalib_date DATE` argument to `14_full_reconstruction_tuku.py`. When provided, the script expands the calibration window to include all MLCW data through that date, re-fits $S_{ke}$, $S_{kv}$, and writes new output files with a `_recalib_YYYYMMDD` suffix.
  - **Files to modify:** `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\tau_demo_TUKU\14_full_reconstruction_tuku.py`
  - **Success check:** Running `python 14_full_reconstruction_tuku.py --recalib_date 2022-06-30` produces output files with `_recalib_20220630` suffix; $S_{ke}$/$S_{kv}$ values printed.

- [ ] Step B: Test recalibration by holding out a single MLCW observation at TUKU (choose the epoch nearest 2022-01-01 for F1). Fit on calibration up to 2021-12-31. Then expand to include the held-out epoch. Compare pre- and post-recalibration RMSE on the 6 months following the new measurement.
  - **Success check:** Post-recalibration RMSE ≤ pre-recalibration RMSE on the 6-month evaluation window.

> **DECISION POINT 4 (recalibration benefit):**
> - **PASS:** Post-recalibration RMSE decreases or stays the same. The self-recalibration mechanism works and PART 2 should include it.
> - **FAIL:** Post-recalibration RMSE increases (new measurement destabilizes fit). Investigate: check whether the new measurement falls in a head regime not seen in calibration (e.g., a new minimum below $h_c$). If so, update $h_c$ before re-fitting. Document in PROGRESS.md.

---

#### TASK 1.3.2 — Verify recalibration correctness

**Physical meaning:** After recalibration, $h_c$ may need to be recomputed if the expanded calibration window contains head observations below the previously recorded minimum. A stale $h_c$ causes incorrect regime classification for the new measurement.

**Depends on:** TASK 1.3.1 complete.

- [ ] Step A: After recalibration, check whether the new $h_c$ (pre-calibration minimum head, pre-REF_DATE raw feather) differs from the value used in the original fit. Print old and new $h_c$ per layer.
  - **Physical note:** $h_c$ is the minimum head from the raw GWL feather rows dated before REF_DATE (2015-01-16), before zero-referencing. Per CLAUDE.md §Known Issues (Bug F). Do not recompute from post-REF_DATE data.
  - **Success check:** $h_c$ does not change when new data is from post-2015 (expected: post-2015 head is above pre-2015 minimum for most layers at TUKU).

- [ ] Step B: Confirm that all 10 guardrails pass on the post-recalibration coefficients. Print full guardrail report.
  - **Success check:** No GuardrailViolation; $S_{ke} \ge 0$, $S_{kv} \ge S_{ke}$ for all layers that previously passed.

---

## PART 2 — Obj 2: Multi-Well Extension (37 Stations)

**Physical narrative:** Once the TUKU pilot processing chain (fit, gap-fill, predict, recalibrate) is confirmed at one station, the same chain runs at all 37 MLCW stations across the CRAF. Different stations occupy different hydrogeological zones (proximal gravel, middle transitional, distal clay), so $S_{ke}$/$S_{kv}$ values will differ, but the two-regime Terzaghi model structure is the same.

**Depends on:** PART 1 complete; TASK 1.2.2 PASS (or PARTIAL PASS with documented layer exclusions).

### PHASE 2.1 — Batch Runner

#### TASK 2.1.1 — Build the batch configuration reader

**Physical meaning:** Each of the 37 MLCW stations has a different borehole stratigraphy, GWL well assignment (from `gwl_to_mlcw_layer_assignment_v4.csv`), and set of layer depths. The batch runner must load the per-station configuration from the existing `data/ihmf_config.json` (191 entries) rather than hardcoding TUKU values.

**Depends on:** TASK 1.1.1 complete (single-station script validated).

- [ ] Step A: Read `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\data\ihmf_config.json`. Print: total station count, total layer-pair count, range of $\tau_{\max}$ values, number of feather files listed that actually exist on disk.
  - **Success check:** Station count = 37; layer-pair count = 191; all listed feather files exist (or absent files listed explicitly).
  - **Command:** `$env:PYTHONPATH=""; conda run -n fafalab python -c "import json,os; cfg=json.load(open(r'D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\data\ihmf_config.json')); print(f'entries={len(cfg)}'); missing=[e for e in cfg if not os.path.exists(e['gwl_feather'])][:5]; print(f'missing(first 5)={missing}')"`

- [ ] Step B: Verify that the layer names in `ihmf_config.json` use the Taiwan CGS convention (F = aquifer, T = aquitard). Confirm no entry uses inverted naming. Print any entries where layer name starts with 'T' but the assigned GWL well belongs to an aquifer ring position.
  - **Success check:** Zero entries with T-layer assigned to aquifer ring GWL well (per CLAUDE.md note: F=aquifer, T=aquitard, do not invert).

---

#### TASK 2.1.2 — Write the batch reconstruction script

**Physical meaning:** The batch script runs the same two-regressor NNLS fitting procedure used at TUKU across all 191 station-layer pairs. For each pair, it loads the appropriate GWL feather file, computes $H$, $V$, fits $S_{ke}$/$S_{kv}$, and writes a per-layer reconstruction CSV. Wells with insufficient GWL overlap are flagged rather than silently skipped.

**Depends on:** TASK 2.1.1 complete.

- [ ] Step A: Write script `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\scripts\10_ihmf\15_batch_reconstruction.py` that:
  - Iterates over all 191 entries in `ihmf_config.json`.
  - Calls the same two-regressor NNLS logic as Script 12 / Script 14.
  - Skips a layer-pair if: (a) GWL feather is missing, (b) fewer than 10 valid MLCW epochs in the calibration window (guardrail 5), or (c) fewer than 10 inelastic epochs (guardrail 5).
  - Calls `validate_layer_params` for each fitted layer; skips and logs any layer that triggers a GuardrailViolation.
  - Saves per-station JSON to `results/batch_reconstruction/{STATION}_reconstruction.json` with per-layer $S_{ke}$, $S_{kv}$, ratio, $R^2$, RMSE, skip reason (if applicable).
  - Writes a summary CSV `results/batch_reconstruction/batch_summary.csv` with one row per station-layer pair.
  - **Must import:** `from paths import RESULTS_ROOT, DATA_ROOT` — no hardcoded paths.
  - **Success check:** Script runs on a 3-station test subset without errors; output files written to correct locations.
  - **Command:** `$env:PYTHONPATH=""; conda run -n fafalab python scripts/10_ihmf/15_batch_reconstruction.py --stations TUKU YUANCHANG XIUTAN`

- [ ] Step B: Run the full 37-station batch. Monitor for stations that skip all layers (zero valid pairs) and stations where the batch fails mid-run.
  - **Command:** `$env:PYTHONPATH=""; conda run -n fafalab python scripts/10_ihmf/15_batch_reconstruction.py --all`
  - **Success check:** `batch_summary.csv` contains 191 rows; the `status` column shows "OK", "SKIP_GWL", "SKIP_DATA", or "SKIP_GUARDRAIL"; zero Python tracebacks in stdout.

---

### PHASE 2.2 — Per-Station Validation Report

#### TASK 2.2.1 — Compute held-out skill scores for all stations

**Physical meaning:** At each of the 37 stations, the held-out validation uses the same interior-segment protocol designed in PART 0 for TUKU. The fraction of stations where skill > 0 on ≥ 2 layers determines whether the method meets the Obj 2 success criterion (≥ 80% of stations).

**Depends on:** TASK 2.1.2 complete; batch reconstruction run on all 37 stations.

- [ ] Step A: Extend `15_batch_reconstruction.py` (or write a separate script `16_batch_holdout_eval.py`) to apply the held-out split from TASK 0.1.1 to all stations. For each station-layer pair that completed with status "OK", compute: RMSE_model, RMSE_baseline (linear interpolation), skill score.
  - **Success check:** `results/batch_reconstruction/batch_holdout_eval.csv` written with one row per station-layer pair; skill_score column contains finite values.

- [ ] Step B: Compute the fraction of stations with skill > 0 on ≥ 2 layers. Compare to the 80% success criterion defined in PROGRESS.md §0.
  - **Success check:** Number printed; if < 80%, flag in PROGRESS.md as criterion not met.

> **DECISION POINT 5 (Obj 2 success criterion):**
> - **PASS:** ≥ 80% of stations have skill > 0 on ≥ 2 layers. Proceed to PART 3.
> - **FAIL:** < 80% of stations pass. Investigate whether failure clusters in a geographic zone (e.g., proximal fan with shallow GWL wells) or a specific layer type. Do not proceed to PART 3 until root cause is identified and either corrected or documented as a model boundary condition.

---

#### TASK 2.2.2 — Handle stations with insufficient GWL overlap

**Physical meaning:** F2 and F3 GWL wells at some stations were installed after 2012, leaving the 2003–2012 inelastic compaction era with no GWL data. At those stations, F2/F3 reconstruction starts only from 2012, missing up to 40% of the cumulative compaction history.

**Depends on:** TASK 2.1.2 complete.

- [ ] Step A: For each station-layer pair with `status = "SKIP_GWL"`, record the GWL start date and the fraction of the MLCW record period (2015–present) that is covered. Print: Station | Layer | GWL_start | Coverage_fraction.
  - **Success check:** Table printed; no station has coverage_fraction = 0.0 for layers assigned to wells with `coverage_2023_2025 ≥ 100` per `gwl_to_mlcw_layer_assignment_v4.csv`.

- [ ] Step B: For stations where F2 GWL coverage < 60%, add a spatial interpolation fallback: use the $S_{ke}$, $S_{kv}$ values from the nearest 3 stations (by Euclidean distance in CRAF coordinates) that did have sufficient GWL coverage, and interpolate (inverse-distance weighting). Write interpolated parameters to a separate column `S_ke_idw`, `S_kv_idw` in `batch_summary.csv`.
  - **Success check:** IDW column populated for all stations with coverage < 60%; IDW values fall within the range of the source station values.

---

## PART 3 — Obj 3: Regional Grid Prediction (8,577 Points)

**Physical narrative:** At 8,577 grid points with no MLCW, the sediment column compaction must be estimated from InSAR surface displacement + regionally-interpolated GWL + hydrofacies-derived storage parameters. The physical bridge from borehole measurements at 37 stations to 1 km × 1 km grid cells requires matching each grid cell's hydrogeological facies type (gravel, sand, clay) to a $S_{ke}$/$S_{kv}$ prior.

**Depends on:** PART 2 PASS (Obj 2 criterion met); TASK 2.2.2 complete.

### PHASE 3.1 — Hydrofacies Product Sourcing

#### TASK 3.1.1 — Identify and obtain the CRAF hydrofacies model

**Physical meaning:** The hydrofacies classification maps the subsurface of the CRAF into lithological zones (proximal gravel, middle sand, distal clay). Without this map, there is no physically grounded way to assign $S_{ke}$, $S_{kv}$ priors to grid points with no borehole data.

**Depends on:** PART 2 complete (need batch $S_{ke}$/$S_{kv}$ values to calibrate the hydrofacies-to-parameter mapping).

- [ ] Step A: Search `D:\112_PROJECT_002` for any existing hydrofacies product covering the CRAF. Check: `D:\112_PROJECT_002\data\`, `D:\112_PROJECT_002\docs\`, `D:\112_PROJECT_002\CLAUDE.md`.
  - **Files to read:** `D:\112_PROJECT_002\CLAUDE.md`
  - **Success check:** Either a hydrofacies raster file path is found, or "hydrofacies not yet sourced" is recorded in PROGRESS.md.

- [ ] Step B: If no hydrofacies product exists in the companion repo, check published sources. The Hung et al. (2021) WRR paper covers the CRAF and reports fan-zone delineation (proximal/middle/distal). Record the fan-zone boundary coordinates from that paper.
  - **Reference:** Hung et al. (2021), "Spatiotemporal patterns of land subsidence in the Choushui River Alluvial Fan, Taiwan" — already cited in `scripts/guardrails.py` priors table.
  - **Success check:** Fan zone boundaries (proximal/middle/distal) documented with coordinate references; either from existing file or from paper.

- [ ] Step C: Map the 8,577 grid point coordinates to one of three fan zones (proximal, middle, distal) using the zone boundaries from Step B. Write a lookup table `data/grid/grid_fan_zone_lookup.csv` with columns: `grid_id`, `lon`, `lat`, `fan_zone`.
  - **Success check:** CSV written with 8,577 rows; `fan_zone` values are one of {proximal, middle, distal} only.

---

#### TASK 3.1.2 — Map hydrofacies zones to $S_{ke}$/$S_{kv}$ parameter priors

**Physical meaning:** The Hung et al. (2021) WRR paper provides CRAF-specific $S_{ske}$ and $S_{skv}$ priors by fan zone (middle: $S_{ske} = 1.15 \times 10^{-4}$ m$^{-1}$, $S_{skv} = 1.33 \times 10^{-3}$ m$^{-1}$; distal: $S_{ske} = 1.16 \times 10^{-4}$ m$^{-1}$, $S_{skv} = 1.91 \times 10^{-3}$ m$^{-1}$). These are converted to bulk storage values per layer using the compressible thickness from the borehole records.

**Depends on:** TASK 3.1.1 complete.

- [ ] Step A: For each fan zone, compute the expected $S_{ke}$ and $S_{kv}$ (bulk, mm/m units) by multiplying the Hung et al. (2021) specific storage values by the mean compressible thickness for each layer across stations in that zone.
  - **Files to read:** `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\figures\prestage_data_analysis\layer_thickness_borehole_TUKU.csv`
  - **Success check:** Parameter table written with: fan_zone | layer | $S_{ke}$ | $S_{kv}$ | compressible_thickness_m.

- [ ] Step B: Validate that the zone-mean parameters computed from the batch reconstruction (PART 2) are within 2× of the Hung et al. (2021) priors for middle and distal zones. If any layer-zone combination exceeds 2×, flag as a discrepancy requiring physical explanation before use in grid prediction.
  - **Success check:** Comparison table printed; discrepancies > 2× highlighted; explanations recorded if present.

---

### PHASE 3.2 — Grid Prediction Script

#### TASK 3.2.1 — Build the regional grid prediction script

**Physical meaning:** At each of the 8,577 grid points, the model predicts cumulative per-layer compaction by combining: (a) the InSAR surface displacement timeseries at that grid point, (b) the spatially-interpolated GWL timeseries from the nearest GWL wells, and (c) the fan-zone-derived $S_{ke}$/$S_{kv}$ priors. The compaction at each grid point is the sum across layers, each modeled by the Terzaghi two-regime equation.

**Depends on:** TASK 3.1.2 complete; PART 2 batch coefficients available.

- [ ] Step A: Write script `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\scripts\20_grid_prediction\01_build_grid_gwl_timeseries.py` that:
  - For each grid point, identifies the nearest 3 GWL wells by Euclidean distance in EPSG:32651 (UTM zone 51N).
  - Computes an inverse-distance-weighted GWL timeseries for each aquifer layer (F1, F2, F3, F4) at each grid point.
  - Outputs one feather file per grid point (or a packed 3D array in NetCDF4).
  - **Success check:** Output exists; GWL timeseries at TUKU grid coordinates matches TUKU station GWL to within 0.5 m RMS.

- [ ] Step B: Write script `02_predict_grid_compaction.py` in the same directory that:
  - Reads the grid GWL timeseries from Step A.
  - Looks up fan-zone parameters from `data/grid/grid_fan_zone_lookup.csv`.
  - Applies the two-regressor NNLS compaction model to each grid point and layer using fan-zone $S_{ke}$/$S_{kv}$ priors (not fitted — priors from literature).
  - Outputs per-layer cumulative compaction as NetCDF4: `results/grid_prediction/compaction_3d_per_layer.nc` (dimensions: grid_id × layer × time).
  - **Success check:** NetCDF file written; values at MLCW station grid points are within 20% of the batch reconstruction values from PART 2 (spatial consistency check).
  - **Command:** `$env:PYTHONPATH=""; conda run -n fafalab python scripts/20_grid_prediction/02_predict_grid_compaction.py`

---

### PHASE 3.3 — Spatial Validation Against Withheld MLCW Stations

#### TASK 3.3.1 — Spatial hold-out validation

**Physical meaning:** To test whether the regional grid method generalizes beyond the calibration stations, a spatial hold-out reserves a subset of MLCW stations from the batch parameter fitting (PART 2) and instead predicts their compaction using only grid-based fan-zone priors. This separates the method's spatial transfer skill from its per-station calibration skill.

**Depends on:** TASK 3.2.1 complete; PART 2 batch complete.

- [ ] Step A: Select 5 withheld MLCW stations from PART 2 (not used in parameter fitting). Choose stations that span all three fan zones (≥ 1 proximal, ≥ 2 middle, ≥ 2 distal). List station names and fan zones.
  - **Success check:** 5 stations identified; fan zone coverage confirmed from `data/grid/grid_fan_zone_lookup.csv`.

- [ ] Step B: Compare grid-predicted compaction at the withheld station coordinates to the actual MLCW observations. Compute RMSE and $R^2$ per layer per station.
  - **Success check:** RMSE_grid printed; $R^2 \ge 0$ for at least 4 of 5 stations at layers F1, T2, F4.

> **DECISION POINT 6 (spatial transfer validation):**
> - **PASS:** RMSE_grid < 2× RMSE_station (grid prediction is no more than 2× worse than calibrated per-station fit). Proceed to PART 5 publication outputs.
> - **FAIL:** RMSE_grid ≥ 2× RMSE_station. Investigate: check whether parameter transfer fails in a specific fan zone; check whether the IDW GWL interpolation introduces bias at the withheld stations. Adjust zone boundaries or GWL interpolation method before proceeding.

---

## PART 4 — Quality Gates and Guardrails

**Purpose:** All scripts written in Parts 1–3 must wire the existing `scripts/guardrails.py` 10-check system. No parameter value is written to disk without passing the guardrail checks. This part tracks that wiring — it is not new code, but a checklist against each new script.

**Depends on:** Each task in Parts 1–3 as it is completed.

### PHASE 4.1 — Guardrail wiring checklist

#### TASK 4.1.1 — Verify guardrail imports in every new script

**Physical meaning:** The guardrail checks enforce that $S_{ke} \ge 0$, $S_{kv} \ge S_{ke}$, $\tau \in [0, 120]$, $h_c$ is computed from pre-REF_DATE data only, and the inelastic exceedance term $V(t)$ is monotonically non-increasing. Skipping these checks risks writing physically impossible parameters to disk, which would contaminate the batch results.

- [ ] Step A: After writing `13_holdout_gap_fill_eval.py` (TASK 0.1.2), confirm it contains `from scripts.guardrails import validate_layer_params, validate_sign_constraints` and calls both functions before writing results.
  - **Success check:** `grep -n "guardrails" tau_demo_TUKU/13_holdout_gap_fill_eval.py` returns ≥ 2 lines.

- [ ] Step B: After writing `14_full_reconstruction_tuku.py` (TASK 1.1.1), confirm guardrail import and call are present.
  - **Success check:** Same grep check; no GuardrailViolation raised during test run.

- [ ] Step C: After writing `15_batch_reconstruction.py` (TASK 2.1.2), confirm guardrail call is inside the per-layer fitting loop (not just at script level).
  - **Success check:** GuardrailViolation is caught and logged (not re-raised) for layers that fail, allowing the batch to continue to next layers.

- [ ] Step D: After writing grid prediction scripts (TASK 3.2.1), confirm that fan-zone prior parameters are checked against `validate_literature_bounds()` before use.
  - **Success check:** `validate_literature_bounds` imported and called with fan_zone argument matching Hung et al. (2021) prior table.

---

#### TASK 4.1.2 — Run the full guardrails test suite

**Physical meaning:** The 9 unit tests in `scripts/guardrails.py` verify that the automated checks catch known violation patterns. These tests must pass before any batch run.

**Depends on:** TASK 4.1.1 complete.

- [ ] Step A: Run the guardrails unit tests and confirm 9/9 pass.
  - **Command:** `$env:PYTHONPATH=""; conda run -n fafalab python scripts/guardrails.py`
  - **Success check:** Output contains "9/9 tests passed" (as documented in PROGRESS.md 2026-06-08).

- [ ] Step B: After any modification to `guardrails.py` (if thresholds are adjusted based on batch findings), re-run and confirm all tests pass before committing.
  - **Success check:** Test count does not decrease; no previously-passing test begins failing.

---

## PART 5 — Publication-Ready Outputs

**Purpose:** Generate the figures, tables, and narrative-support files required for the manuscript. These outputs are the final deliverables of the research program. They are not built until Parts 1–3 are complete and validated.

**Depends on:** PART 2 PASS; PART 3 complete (even if spatial transfer only partially validated); all guardrails passing.

### PHASE 5.1 — Per-Layer Compaction Timeseries Figures

#### TASK 5.1.1 — Gap-fill vs. observed MLCW plots

**Physical meaning:** Each plot shows two curves per layer: the reconstructed compaction timeseries (from the cumulative NNLS model) and the original MLCW observations. Gap periods — where MLCW is absent but reconstruction continues — are highlighted. This figure is the primary evidence that the research objective (monitoring gap-fill) is achieved.

**Depends on:** TASK 1.1.1 complete; all 37-station reconstructions complete.

- [ ] Step A: For each MLCW station, write a figure script `scripts/21_figures/plot_reconstruction_per_station.py` that produces a 6-panel figure (one per layer). Each panel shows: modeled compaction (solid line), observed MLCW (dots), MLCW-gap periods (grey shading), $R^2$ and RMSE annotation in upper corner.
  - **Figure standards:** Font ≥ 14 pt; tab10 colors; y-axis = cumulative mm from REF_DATE; x-axis = date; grid on; tight layout; 300 dpi; A4 portrait.
  - **Output:** `results/figures/reconstruction/{STATION}_reconstruction_6layer.png`
  - **Success check:** 37 PNG files written; all have 6 subplots; file sizes > 100 KB each.

- [ ] Step B: For TUKU, produce a high-quality version with uncertainty bounds (P05–P95 estimated from fold-to-fold parameter variability). Save as `TUKU_reconstruction_6layer_with_uncertainty.pdf` for manuscript submission.
  - **Success check:** PDF written; uncertainty shading visible in all panels; legend includes 95% CI annotation.

---

### PHASE 5.2 — Regional Subsidence Map

#### TASK 5.2.1 — Build the 8,577-point subsidence map figure

**Physical meaning:** The regional subsidence map shows predicted total compaction (sum across all layers) at each of the 8,577 grid points, integrated over the study period. This map is the spatial extension of the monitoring record to the full CRAF — the core deliverable of Obj 3.

**Depends on:** TASK 3.2.1 complete; compaction NetCDF written.

- [ ] Step A: Write `scripts/21_figures/plot_regional_map.py` that reads `results/grid_prediction/compaction_3d_per_layer.nc`, sums across layers, and plots a filled-contour map in EPSG:4326 (geographic coordinates) with the 37 MLCW station locations overlaid.
  - **Tools:** matplotlib with Cartopy or plain scatter plot on lat/lon axes; ColorBrewer diverging colormap (blue=uplift, red=subsidence).
  - **Output:** `results/figures/regional_map/CRAF_total_subsidence_2015_2025.png`
  - **Success check:** PNG written; colorbar labeled "Cumulative subsidence (mm)"; MLCW stations visible as markers; coast and major rivers shown if shapefile available.

---

### PHASE 5.3 — Parameter Table for Manuscript

#### TASK 5.3.1 — Generate the $S_{ke}$, $S_{kv}$, $\tau$ parameter table

**Physical meaning:** The parameter table summarizes what the sediment column's physical properties are at each MLCW station: how stiff (or compressible) each layer is in elastic vs. inelastic regimes, and how long head changes take to produce compaction. This table is the quantitative evidence that the method recovers physically plausible parameters across diverse hydrogeological settings.

**Depends on:** TASK 2.1.2 complete; batch summary CSV written.

- [ ] Step A: Read `results/batch_reconstruction/batch_summary.csv`. Extract for each station-layer pair: station, layer, $S_{ke}$ (mm/m), $S_{kv}$ (mm/m), ratio, $\tau$ (5-day epochs), $\tau$ (days), $R^2_{calib}$, guardrail_pass.
  - **Success check:** Table has 191 rows; all required columns present.

- [ ] Step B: Write LaTeX-formatted table to `results/tables/parameter_table_all_stations.tex`. Include footnotes: (1) layers with guardrail failures are marked with dagger symbol and excluded from spatial extension; (2) $\tau$ is reported in days (= epochs × 5 days).
  - **Success check:** `.tex` file compiles without errors; table fits on two pages at 10pt font.

---

## Appendix A — File Naming and Path Conventions

All new output files in this plan must follow the naming convention in PROGRESS.md §5:
- Active outputs: no suffix.
- Obsolete outputs: `_OBSOLETE_<reason>` suffix — never deleted.

All new Python scripts must use `from paths import RESULTS_ROOT, DATA_ROOT, SCRIPTS_ROOT, DOCS_ROOT` — no hardcoded paths.

GWL wellcodes are always 8-digit strings (e.g., `"09050111"` not `9050111`). The broader feather glob `*.feather` must not be used — use `*gwl*timeseries.feather` to avoid matching GPS feather files.

All math in comments and docstrings uses LaTeX format where rendered (Jupyter, markdown). In plain Python docstrings, use `S_ke`, `S_kv`, `tau_j` with underscores.

---

## Appendix B — Environment Commands Reference

```powershell
# Reset PYTHONPATH (mandatory before every conda run call)
$env:PYTHONPATH=""

# Run TUKU gap-fill evaluator (Part 0)
$env:PYTHONPATH=""; conda run -n fafalab python tau_demo_TUKU/13_holdout_gap_fill_eval.py

# Run full TUKU reconstruction (Part 1)
$env:PYTHONPATH=""; conda run -n fafalab python tau_demo_TUKU/14_full_reconstruction_tuku.py

# Run full TUKU reconstruction with next-month prediction
$env:PYTHONPATH=""; conda run -n fafalab python tau_demo_TUKU/14_full_reconstruction_tuku.py --predict_to 2025-12-31

# Run TUKU recalibration with new in-situ measurement
$env:PYTHONPATH=""; conda run -n fafalab python tau_demo_TUKU/14_full_reconstruction_tuku.py --recalib_date 2022-06-30

# Run batch reconstruction (3-station test)
$env:PYTHONPATH=""; conda run -n fafalab python scripts/10_ihmf/15_batch_reconstruction.py --stations TUKU YUANCHANG XIUTAN

# Run batch reconstruction (all 37 stations)
$env:PYTHONPATH=""; conda run -n fafalab python scripts/10_ihmf/15_batch_reconstruction.py --all

# Run guardrails unit tests
$env:PYTHONPATH=""; conda run -n fafalab python scripts/guardrails.py

# Run grid compaction prediction
$env:PYTHONPATH=""; conda run -n fafalab python scripts/20_grid_prediction/02_predict_grid_compaction.py
```

---

*Plan written: 2026-06-09. Status: Planning only — no code was written or modified to produce this file.*
