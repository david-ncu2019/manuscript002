# Super Plan — InSAR-MLCW Subsidence Monitoring Gap-Fill and Prediction (Revised after Zero-Trust Audit)

> **For agentic workers:** REQUIRED reading before any task: `PROGRESS.md`, `CLAUDE.md`, `plans/ZeroTrust_Audit_Report_20260609.md`, and `plans/Bilinear_Model_Test_Findings_20260609.md`. This plan REPLACES the pre-audit version (kept as `super_plan_2026-06-09_OBSOLETE_pre_audit_single_method.md`).
>
> **Working directory / interpreter (Ubuntu 22.04 VM):** repo root is `/mnt/hgfs/1000_SCRIPTS/004_Project003/20260427_InSAR_MLCW_v2`. Use the `isce_ncu3` conda env:
> ```bash
> PYTHONPATH="" conda run -n isce_ncu3 python <script>
> ```
> Run every command from the repo root. Use `paths.py` (`from paths import DATA_ROOT, RESULTS_ROOT, SCRIPTS_ROOT`) inside scripts — never hardcode absolute paths (they differ between Windows host and Linux VM).

**Goal:** Reconstruct broken MLCW (Multi-Layer Compaction monitoring Well) records, predict future per-layer compaction, and extend spatial coverage to 8,577 unmonitored grid points, using InSAR (Interferometric Synthetic Aperture Radar) / GPS surface displacement, GWL (groundwater level), and borehole stratigraphy.

**Method (revised — two tracks, decided by held-out evidence):**

1. **Gap-fill / prediction track (PRIMARY): InSAR/GPS-carrier apportionment.** Surface displacement is the integral of all layer compactions, so it carries the compaction signal directly. Each layer's compaction is modeled as a (slowly time-varying, physically bounded) share of the continuously available surface signal, with GWL as a secondary covariate. The 2026-06-09 held-out tests show this beats both the GWL bilinear model and plain interpolation for the well-coupled layers, and never diverges.
2. **Physical-characterization track (SECONDARY): cumulative bilinear Terzaghi/Riley.** The `b_j(t)=S_{ke}H_j+(S_{kv}-S_{ke})V_j` model is the correct physics for estimating elastic/inelastic skeletal storage ($S_{ke}$, $S_{kv}$). It is used to REPORT layer compressibility, NOT to gap-fill — the same tests show it is the WORST gap-fill method (it loses to a straight line on every layer). It must first be bug-fixed (Phase 0.0) before its parameters are trusted.

**Why this revision exists (audit findings, 2026-06-09):** The pre-audit plan treated the bilinear GWL model as the gap-fill method and quoted gate numbers ("F1=9.1× PASS, T2=9.3× PASS, F4=17.3× PASS") that do not match the live result file. The live `tau_demo_TUKU/results/stress_strain_per_layer.json` shows F1 FAILS (specific ratio 30.36×, $S_{ske}$ below the literature floor), and only T2 (8.42×) and F4 (10.76×) pass. The production solver (`fit_ihm_f_v3.py` + `ihmf_model_v3.py::joint_solve_cumulative`) also has a real bug: it uses ABSOLUTE head with no intercept, so the elastic coefficient $S_{ke}$ collapses to 0 for every well whose absolute head is positive (proved against the data). Full details in `plans/ZeroTrust_Audit_Report_20260609.md`.

**Tech stack:** Python (conda env `isce_ncu3`, scipy ≥ 1.17), `scipy.optimize.nnls` / `scipy.optimize.lsq_linear`, pandas, feather format, Ubuntu 22.04.

---

## Top-Level Milestone Summary Table

| Milestone | Description | Depends On | Estimated Effort (hours) | Scope |
|-----------|-------------|------------|--------------------------|-------|
| **M0** | Part 0 — Bug fix + 3-method held-out bake-off (pick the gap-fill method) | — | 14 h | Week 1 |
| **M1** | Part 1 — Obj 1: TUKU gap-fill + prediction (winning method) + $S_{ke}$/$S_{kv}$ characterization | M0 PASS | 20 h | Week 1–2 |
| **M2** | Part 2 — Obj 2: Multi-Well Extension (37 stations) | M1 | 16 h | Follow-on |
| **M3** | Part 3 — Obj 3: Regional Grid Prediction (8,577 pts) | M2 | 28 h | Follow-on |
| **M4** | Part 4 — Guardrails + held-out skill gate wiring | M0 (ongoing) | 6 h | Continuous |
| **M5** | Part 5 — Publication-Ready Outputs | M2, M3 | 20 h | Follow-on |

**One-week hard constraint:** M0 + M1 must complete within the current working week. M2–M5 are follow-on.

**Physical narrative:** The Choushui River Alluvial Fan (CRAF) sediment column compresses as confined-aquifer head declines. MLCW instruments that measured this layer-by-layer are being shut down. The surface keeps being measured (InSAR/GPS). Because the surface motion is the sum of the layer compactions beneath it, we reconstruct a stopped well's per-layer record by splitting the continuously-measured surface signal back into layers, calibrated where MLCW data still exists. The groundwater-driven Terzaghi model, while the correct physics for layer compressibility, responds to head with a complex delayed, non-stationary transfer that a simple fit cannot extrapolate — so it is kept for parameter reporting, not gap-fill.

---

## PART 0 — Bug Fix and Method Bake-Off (Validation Gate)

**Purpose:** (1) Fix the two demonstrated bugs in the bilinear program so any parameter it reports is trustworthy; (2) run a FAIR held-out comparison of three gap-fill methods — InSAR/GPS carrier, bilinear-fixed, and static interpolation — and let the data choose the primary gap-fill method. The pre-audit gate tested only the bilinear model against interpolation and omitted the carrier; that omission is corrected here.

**Reference implementation already exists:** `tmp_audit_test.py`, `tmp_audit_test2.py`, `tmp_audit_test3.py` in the repo root are working, verified scripts that load the real data, reproduce Script 12 exactly, demonstrate the bug, and run the three-method comparison. Build Part 0 by promoting these into permanent scripts — do not start from scratch.

**Depends on:** —

### PHASE 0.0 — Fix the Bilinear Program Bugs

#### TASK 0.0.1 — Reproduce the bug and the fix on TUKU data

**Physical meaning:** The model multiplies head by the elastic coefficient $S_{ke}$. Physics needs the head *change* from a reference, $u(t)=H(t)-H(t_{ref})$, plus an intercept for compaction that pre-dates the record. The production path used the raw absolute head (e.g. HONGLUN sits near +8.5 m above sea level) with no intercept, so the fit was forced through zero and $S_{ke}$ collapsed to 0 wherever absolute head is positive. The datum cancels inside the virgin term $V(t)=\min(0,\text{cummin}(H)-h_c)$, so only the elastic term is corrupted.

**Depends on:** —

- [ ] Step A: Read `tmp_audit_test.py` (repo root). Confirm it loads `tau_demo_TUKU\data\TUKU_reconst_grouped_cleaned.csv` and the GWL feathers, zero-references MLCW and head to REF_DATE = 2015-01-16, and fits three variants: A (zero-ref, no intercept), B\* (absolute head — the bug), C (zero-ref + intercept).
  - **Success check:** Variant A reproduces `stress_strain_per_layer.json` (F1 $S_{ke}$=0.883, $S_{kv}$=3.198, R²=0.607; F2 R²=0.845; F3 $S_{ke}$=0). Variant B\* shows $S_{ke}$=0 for F1/T1 (HONGLUN, positive absolute head). This confirms the bug.
  - **Command:** `PYTHONPATH="" conda run -n isce_ncu3 python tmp_audit_test.py`

- [ ] Step B: Promote the CORRECT bilinear fitter into a permanent module `tau_demo_TUKU\bilinear_fit.py` exposing one function:
  `fit_bilinear(H_abs, b, h_c_abs, with_intercept=True) -> dict(c, S_ke, S_kv, ratio, r2, b_pred)`.
  It must (1) zero-reference head internally: `u = H_abs - H_ref` where `H_ref` is the last raw head on/before REF_DATE; (2) compute `V = min(0, cummin(H_abs) - h_c_abs)`; (3) fit `b = c + S_ke*u + (S_kv-S_ke)*V` with `S_ke>=0` and `S_kv>=S_ke` enforced (use `scipy.optimize.nnls` on the no-intercept residual after removing the mean, or `lsq_linear` with bounds and an explicit intercept column).
  - **Files to create:** `tau_demo_TUKU\bilinear_fit.py`
  - **Success check:** On TUKU F1, `with_intercept=True` returns R² ≥ 0.76 (vs 0.61 without intercept) and `S_ke ≥ 0`, `S_kv ≥ S_ke`.

- [x] Step C: Fix the production path so it matches the corrected math. In `scripts\10_ihmf\ihmf_io_multilayer.py::load_all_layers_gps`, after building `head_m`, also store `head_ref` (last raw head on/before REF_DATE) per layer in `layer_metas`. In `scripts\10_ihmf\ihmf_model_v3.py::joint_solve_cumulative`, change the elastic regressor from absolute `H` to `H - head_ref`, and add an intercept column per layer. Keep `V` computed from absolute head and absolute `h_c` (datum cancels — do not change it).
  - **Files to modify:** `scripts\10_ihmf\ihmf_io_multilayer.py`, `scripts\10_ihmf\ihmf_model_v3.py`
  - **Success check:** Re-running `fit_ihm_f_v3.py --station TUKU --gps --all --alpha 0.625` yields per-layer `r2_cum > 0` for at least F1, T1, T2, F4 (previously all negative except T2), and `S_ke > 0` for the layers whose head crosses their reference.
  - **Command:** `PYTHONPATH="" conda run -n isce_ncu3 python scripts\10_ihmf\fit_ihm_f_v3.py --station TUKU --gps --all --alpha 0.625`

- [ ] Step D: Stop reporting the pooled `r2_mlcw_cum`. In `ihmf_model_v3.py`, replace the concatenated-layer R² with per-layer R² only (the pooled number is inflated by between-layer magnitude differences and is misleading).
  - **Files to modify:** `scripts/10_ihmf/ihmf_model_v3.py` (lines ~440–448 build the pooled R² inside `joint_solve_cumulative`)
  - **Success check:** Output JSON no longer contains a single `r2_mlcw_cum`; it reports `r2_cum` per layer.

> **DECISION POINT 0 (bilinear is now trustworthy for parameters):**
> - **PASS:** Corrected fit gives `S_ke ≥ 0`, `S_kv ≥ S_ke`, and per-layer `r2_cum > 0` for ≥ 4 of 6 layers. The bilinear model may now be used for parameter characterization (Part 1, Phase 1.4). Proceed to PHASE 0.1.
> - **FAIL:** Still `S_ke = 0` for most layers after the datum fix. Re-check that `H_ref` is the pre-REF_DATE value and that the intercept column is actually in the design matrix. Do NOT proceed until at least F1, T1, T2, F4 give positive `r2_cum`.

---

### PHASE 0.1 — Held-Out Evaluation Protocol

#### TASK 0.1.1 — Define two hold-out designs (gap and tail)

**Physical meaning:** Two real situations must be tested. (1) A well reduces sampling but still reports occasionally → a MIDDLE gap bracketed by data (interpolation is the baseline). (2) A well is shut off permanently → an END gap with no data after it (linear-trend extrapolation is the baseline). Both must be evaluated because the project's stated success bar is "beat static linear interpolation."

**Depends on:** PHASE 0.0 PASS.

- [ ] Step A: Build aligned per-layer arrays at TUKU for all 6 layers on the post-2015, 5-day grid: `datetime, b (zero-ref MLCW, mm), H_abs (lagged head, m), u (=H_abs-H_ref), V, d_surface (GPS 'modeled', mm)`. Reuse the alignment logic in `tmp_audit_test2.py` (merge_asof, tolerance 3 days, tau lag from `tau_results.csv`).
  - **Files to read:** `tau_demo_TUKU\data\TUKU_reconst_grouped_cleaned.csv`, `tau_demo_TUKU\data\*_gwl_timeseries.feather`, `tau_demo_TUKU\data\TUKU_GPS_timeseries.feather`, `tau_demo_TUKU\results\tau_results.csv`
  - **Success check:** Each layer has ≥ 700 aligned epochs from 2015-01-16 onward; no NaN in `b`, `H_abs`, `d_surface`.

- [ ] Step B: Define MIDDLE-gap = epochs 40%–70% of the record; END-gap = last 30% of the record. Training = the complement. Record both in `tau_demo_TUKU\data\holdout_split_definition.json`.
  - **Success check:** JSON written with `middle_gap` and `end_gap` index ranges; both gaps have ≥ 100 epochs per layer.

---

#### TASK 0.1.2 — Build the three-method held-out evaluator

**Physical meaning:** Each method fills the held-out gap using only training data plus the signals that remain available during the gap. The carrier and GWL signals are real during the gap (that is the whole point of gap-fill); the bracketing MLCW values are available only for the middle-gap interpolation baseline.

**Depends on:** TASK 0.1.1 complete.

- [ ] Step A: Create `tau_demo_TUKU\13_holdout_method_bakeoff.py` (promote `tmp_audit_test2.py`/`tmp_audit_test3.py`). For each layer and each hold-out design, compute held-out RMSE (mm) for:
  - **M1 InSAR/GPS carrier:** fit `b = a*d_surface + c` (with `a ≥ 0`) on training; predict in the gap with the gap's `d_surface`.
  - **M2 bilinear-fixed:** fit `b = c + S_ke*u + (S_kv-S_ke)*V` (Phase 0.0 fitter) on training; predict with gap `u`,`V`.
  - **M3 baseline:** middle-gap → linear interpolation between bracketing observed `b`; end-gap → linear trend extrapolation of training `b`.
  - Save `tau_demo_TUKU\results\holdout_bakeoff.json` with per-layer, per-design RMSE and skill `= 1 - RMSE_method/RMSE_baseline`.
  - **Must import:** `from scripts.guardrails import validate_sign_constraints` — call on M2's coefficients before recording them.
  - **Success check:** JSON has all 6 layers × 2 designs × 3 methods; all RMSE finite.
  - **Command:** `PYTHONPATH="" conda run -n isce_ncu3 python tau_demo_TUKU\13_holdout_method_bakeoff.py`

- [ ] Step B: Print a table: Layer | design | RMSE_carrier | RMSE_bilinear | RMSE_baseline | winner.
  - **Expected from the 2026-06-09 reference run** (use to sanity-check the junior agent's numbers): bilinear is the worst on almost every layer; carrier wins T1/F2/T2; interpolation wins F1/F3/F4 on the middle gap. Example middle-gap RMSE (mm): F2 → carrier 3.06, interp 4.60, bilinear 10.95; F3 → interp 4.60, carrier 10.67, bilinear 18.21.
  - **Success check:** The reproduced numbers are within ±15% of the reference values above.

---

#### TASK 0.1.3 — Select the primary gap-fill method and record the decision

**Physical meaning:** A positive skill score means the method beats the naive baseline. The method that wins most layers (and never blows up) becomes the primary gap-fill engine; the others become per-layer fallbacks where they happen to win.

**Depends on:** TASK 0.1.2 complete.

- [ ] Step A: For each layer, rank the three methods by held-out RMSE (average of middle + end designs). Assign each layer a `primary_method ∈ {carrier, bilinear, interp}`.
  - **Success check:** A per-layer assignment table is written to `holdout_bakeoff.json` under key `primary_method`.

- [ ] Step B: Record the outcome in `PROGRESS.md` §4: the three-method RMSE table and the chosen per-layer primary method.
  - **Success check:** PROGRESS.md updated with date 2026-06-09 and the bake-off table.

> **DECISION POINT 1 (gap-fill method selection — the primary gate):**
> - **CARRIER-PRIMARY (expected):** InSAR/GPS carrier wins or ties on ≥ 3 layers and never gives skill < −0.3. Adopt the carrier as the primary gap-fill engine (PART 1, Phase 1.1). Use interpolation as the floor for the smooth deep layers where it wins. Use the bilinear model ONLY for parameter characterization (Phase 1.4).
> - **MIXED:** No method wins ≥ 3 layers. Adopt a per-layer method map (each layer uses its own winner) and proceed; document the map in PROGRESS.md.
> - **ALL-FAIL (unlikely):** Every method has skill < 0 against the baseline for ≥ 4 layers (i.e. nothing beats a straight line). Then the cumulative compaction is essentially a smooth trend and the deliverable for those layers is "interpolation/spline with documented uncertainty." Record this honestly; do not manufacture skill.

---

## PART 1 — Obj 1: Well-Scale Gap-Fill and Prediction (TUKU Pilot)

**Physical narrative:** With the primary method chosen, build a complete gap-fill reconstruction of the TUKU MLCW record by splitting the continuous surface signal into layers, then extend it forward to predict compaction after the well's last observation. Separately, report the layer compressibilities from the bug-fixed bilinear model for the physical story.

**Depends on:** PART 0 (Decision Point 1) complete.

### PHASE 1.1 — Carrier-Based Gap-Fill Reconstruction at TUKU

#### TASK 1.1.1 — Build the carrier apportionment model

**Physical meaning:** The surface displacement $d_v(t)$ equals the sum of all layer compactions plus a deep/bedrock residual. Each layer's share $a_k$ of the surface motion is a physical apportionment: $0 \le a_k$, and $\sum_k a_k \le 1$ (the layers cannot move more than the surface). Fitting $a_k$ where MLCW exists lets us reconstruct $b_k(t)=a_k\,d_v(t)+c_k$ during gaps using the continuously measured $d_v$.

**Depends on:** PART 0 complete.

- [ ] Step A: Create `tau_demo_TUKU\14_carrier_reconstruction_tuku.py`. For each layer fit `b_k = a_k * d_surface + c_k` on all epochs where MLCW exists, with `a_k ≥ 0`. Then jointly rescale the per-layer `a_k` so `sum(a_k) ≤ 1` (if the unconstrained sum exceeds 1, solve the 6-layer fit jointly with `scipy.optimize.lsq_linear`, bounds `a_k ∈ [0,1]`, plus the sum constraint via an added row).
  - **Success check:** All `a_k ∈ [0,1]`; `sum(a_k) ≤ 1.0 + 1e-6`; per-layer calibration R² printed.

- [ ] Step B: Reconstruct `b_k(t)` for every epoch from 2015-01-16 onward (including MLCW-gap periods) using the continuous GPS/InSAR `d_surface`. Output one CSV per layer `results\reconstruction\TUKU_{layer}_reconstruction.csv` with columns `date, b_model_mm, b_observed_mm (NaN in gaps), d_surface_mm, a_k, c_k`.
  - **Success check:** 6 CSVs written; no all-NaN `b_model_mm`; modeled equals observed (within rounding) on calibration epochs.
  - **Command:** `PYTHONPATH="" conda run -n isce_ncu3 python tau_demo_TUKU\14_carrier_reconstruction_tuku.py`

- [ ] Step C: Add the optional refinements (only if they improve held-out skill from Phase 0.1): (1) allow `a_k` to vary per calendar year (`a_k,year`) with a smoothness penalty; (2) for layers with strong GWL coupling (F2 seasonal), add a small GWL or annual-harmonic residual term `+ d_k * u(t)`.
  - **Success check:** Each refinement is kept ONLY if it lowers held-out RMSE vs Phase 0.1; otherwise reverted and noted.

- [ ] Step D: Plot 6-layer reconstruction (modeled solid, observed dots, gap periods grey). Save `tau_demo_TUKU\plots\reconstruction\TUKU_reconstruction_6layer.png`.
  - **Figure standards:** Font ≥ 14 pt; tab10 colors; y = cumulative mm from REF_DATE; grid on; tight layout; 300 dpi.
  - **Success check:** PNG ≥ 300 dpi; 6 panels; lines distinguishable.

---

#### TASK 1.1.2 — Quantify reconstruction quality and gap coverage

**Physical meaning:** Coverage measures how much of the broken record is restored. A gap with no surface signal cannot be filled — but InSAR/GPS is nearly always available, so the carrier method has far higher coverage than the GWL model (whose F2/F3 wells only start in 2012).

**Depends on:** TASK 1.1.1 complete.

- [ ] Step A: Compute calibration R², RMSE (mm), mean bias (mm) per layer. Print.
  - **Success check:** All R² ≥ 0.
- [ ] Step B: Count gap epochs and surface-covered gap epochs per layer. Print Layer | gap epochs | surface-covered | coverage %.
  - **Success check:** Coverage ≥ 95% for all layers (GPS/InSAR continuity), recorded in PROGRESS.md.

---

### PHASE 1.2 — Next-Period Prediction Mode

#### TASK 1.2.1 — Forward prediction with the carrier

**Physical meaning:** After a well stops, surface measurement continues. The carrier predicts each layer's compaction from the ongoing surface signal — no future MLCW needed.

**Depends on:** TASK 1.1.1 complete.

- [ ] Step A: Add `--predict_to DATE` to `14_carrier_reconstruction_tuku.py`. It applies the frozen `a_k, c_k` to surface data through DATE.
  - **Success check:** `--predict_to 2025-12-31` runs and extends `b_model_mm` past the last MLCW epoch.

- [ ] Step B: Evaluate prediction skill on a tail hold-out (last 6 months of MLCW). Re-fit on the prior epochs; predict the tail; compare RMSE to linear-trend extrapolation. Print Layer | RMSE_model | RMSE_trend | skill.
  - **Success check:** skill > 0 for ≥ 3 of 6 layers (reference end-gap run: carrier beats trend on T1, F2, T2).

> **DECISION POINT 2 (prediction skill):**
> - **PASS:** skill > 0 for ≥ 3 layers. Proceed to PHASE 1.3.
> - **PARTIAL:** skill > 0 for 1–2 layers. Proceed but flag the failing layers; for smooth deep layers (F3/F4) the honest deliverable may be interpolation + uncertainty.
> - **FAIL:** skill ≤ 0 for all layers. The surface signal is not leading the layer compaction at this station; document and escalate before Part 2.

---

### PHASE 1.3 — Self-Recalibration

#### TASK 1.3.1 — Recalibration when a new sparse MLCW point arrives

**Physical meaning:** A new in-situ visit gives one fresh `b_k` point. It should update `a_k, c_k` (and, for the bilinear track, possibly `h_c` if a new head minimum appeared). The carrier recalibration is a cheap re-fit of the linear apportionment.

**Depends on:** TASK 1.1.1 complete.

- [ ] Step A: Add `--recalib_date DATE` to `14_carrier_reconstruction_tuku.py`: expand calibration to include MLCW through DATE, re-fit `a_k, c_k`, write outputs with `_recalib_YYYYMMDD` suffix.
  - **Success check:** Suffix files written; new `a_k` printed.
- [ ] Step B: Hold out one MLCW point near 2022-01-01 for F1; fit to 2021-12-31; then recalibrate including the held-out point; compare 6-month-ahead RMSE before vs after.
  - **Success check:** Post-recalibration RMSE ≤ pre-recalibration RMSE.

> **DECISION POINT 3 (recalibration benefit):**
> - **PASS:** RMSE does not increase. Include recalibration in Part 2.
> - **FAIL:** RMSE increases. Check whether the new point is an outlier or a regime change; document.

---

### PHASE 1.4 — Physical Parameter Characterization (Bilinear Track)

#### TASK 1.4.1 — Report $S_{ke}$, $S_{kv}$ from the bug-fixed bilinear model

**Physical meaning:** This is the physics story for the manuscript: how stiff each layer is in elastic vs inelastic regimes. These parameters are NOT used for gap-fill (Phase 0.1 proved they predict poorly); they describe the sediment.

**Depends on:** PHASE 0.0 PASS.

- [ ] Step A: Using `tau_demo_TUKU\bilinear_fit.py` (with intercept), fit all 6 TUKU layers on the full post-2015 record. Convert to specific storage: $S_{ske}=S_{ke}/(\text{span}\times1000)$, $S_{skv}=S_{kv}/(\text{clay}\times1000)$ using thicknesses from Script 12 lines 97–116. Call `validate_layer_params` before saving.
  - **Success check:** Output `results\characterization\TUKU_storage_params.json`; all `S_ke ≥ 0`, `S_kv ≥ S_ke`.

- [ ] Step B: Report TWO ratios per layer and label them clearly: the bulk ratio `S_kv/S_ke` (same-thickness, comparable to the elastic/inelastic material contrast) AND the specific-storage ratio `S_skv/S_ske` (mixed-thickness — NOT directly comparable to Hung et al. because $S_{ske}$ uses total span while $S_{skv}$ uses clay-only thickness). Do NOT fail a layer on the mixed-thickness ratio alone.
  - **Physical note:** F2's "220×" specific ratio is a thickness artifact (106 m span ÷ 12 m clay = 8.79×), not a physical failure. The bulk ratio (25×) is the meaningful contrast.
  - **Success check:** JSON has `ratio_bulk` and `ratio_specific` per layer with a `thickness_artifact_flag` where span/clay > 4.

- [ ] Step C: Flag identifiability: for layers with < 15 elastic epochs (V==0), mark $S_{ke}$ as "not identifiable" and report inelastic-only `b = S_kv * V`. (F2 has 6, F3 has 7 elastic epochs — their $S_{ke}$ is collinear noise.)
  - **Success check:** F2, F3 flagged `S_ke_identifiable=false`.

---

## PART 2 — Obj 2: Multi-Well Extension (37 Stations)

**Physical narrative:** Run the validated TUKU chain (carrier gap-fill + bilinear characterization) at all 37 MLCW stations. Different fan zones give different $a_k$ and $S_{ke}/S_{kv}$, but the structure is identical.

**Depends on:** PART 1 complete; Decision Point 2 PASS or PARTIAL.

### PHASE 2.1 — Batch Runner

#### TASK 2.1.1 — Batch config reader

**Physical meaning:** Each station has its own borehole stratigraphy, GWL assignment (`gwl_to_mlcw_layer_assignment_v4.csv`), and — for the carrier — its own InSAR pixel / GPS series. The batch must read per-station config, not hardcode TUKU.

**Depends on:** PART 1.

- [ ] Step A: Read `data\ihmf_config.json`. Print station count, layer-pair count, $\tau_{\max}$ range, and which listed feather files exist on disk.
  - **Success check:** 37 stations, 191 pairs; missing feathers listed explicitly.
  - **Command:** `PYTHONPATH="" conda run -n isce_ncu3 python -c "import json,os; from pathlib import Path; cfg=json.load(open(r'data\ihmf_config.json')); e=cfg['entries']; print('entries',len(e)); print('missing',[x['gwl_feather'] for x in e if not os.path.exists(x['gwl_feather'])][:5])"`
- [ ] Step B: Confirm no inverted F/T naming (F=aquifer, T=aquitard). Print violations.
  - **Success check:** Zero inversions.

#### TASK 2.1.2 — Batch carrier reconstruction + characterization

**Physical meaning:** For each station-layer, fit the carrier apportionment for gap-fill and the bilinear parameters for characterization. Skip with a logged reason when surface or MLCW data is insufficient.

**Depends on:** TASK 2.1.1.

- [ ] Step A: Write `scripts\10_ihmf\15_batch_reconstruction.py` that, per station: (1) fits carrier `a_k,c_k` for gap-fill; (2) fits bilinear `S_ke,S_kv` for characterization (validate_layer_params, catch+log violations); (3) writes `results\batch_reconstruction\{STATION}_reconstruction.json` and appends to `results\batch_reconstruction\batch_summary.csv`. Use `from paths import RESULTS_ROOT, DATA_ROOT`.
  - **Success check:** Runs on a 3-station subset; outputs in correct locations; no tracebacks.
  - **Command:** `PYTHONPATH="" conda run -n isce_ncu3 python scripts\10_ihmf\15_batch_reconstruction.py --stations TUKU YUANCHANG XIUTAN`
- [ ] Step B: Run all 37. Status column ∈ {OK, SKIP_SURFACE, SKIP_DATA, SKIP_GUARDRAIL}.
  - **Success check:** `batch_summary.csv` has 191 rows; zero tracebacks.
  - **Command:** `PYTHONPATH="" conda run -n isce_ncu3 python scripts\10_ihmf\15_batch_reconstruction.py --all`

### PHASE 2.2 — Per-Station Held-Out Validation

#### TASK 2.2.1 — Batch held-out skill (carrier vs interpolation)

**Physical meaning:** The Obj 2 success criterion (≥ 80% of stations) is judged on held-out gap-fill skill, using the same designs as Part 0.

**Depends on:** TASK 2.1.2.

- [ ] Step A: Write `scripts\10_ihmf\16_batch_holdout_eval.py` applying the middle+end designs to every OK station-layer; record carrier vs interpolation RMSE and skill. Output `results\batch_reconstruction\batch_holdout_eval.csv`.
  - **Success check:** One row per station-layer; finite skill.
- [ ] Step B: Compute the fraction of stations with skill > 0 on ≥ 2 layers; compare to 80%.
  - **Success check:** Number printed; flagged in PROGRESS.md if < 80%.

> **DECISION POINT 4 (Obj 2 criterion):**
> - **PASS:** ≥ 80% of stations skill > 0 on ≥ 2 layers. Proceed to PART 3.
> - **FAIL:** < 80%. Check whether failures cluster by fan zone or layer; document as a method boundary before Part 3.

---

## PART 6 — REPAIR PLAN (Appended 2026-06-09, Senior Audit Verification)

> **Source:** Audit reports `ZeroTrust_Audit_Report_20260609.md` + `Bilinear_Model_Test_Findings_20260609.md`
> **Verification method:** Every claim traced to a specific file path and line number on this machine (D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2, user FAFALAB, env fafalab).
> **Constraints:** This section is append-only. No `.py` files modified here. CLAUDE.md physics rules are authoritative and override auditor claims where they conflict.

---

### 6.1 Audit Verdict Table

| ID | Claim | Source | Status | Evidence |
|----|-------|--------|--------|----------|
| A1 | Production solver uses absolute head → S_ke=0 collapse | ZeroTrust §1.1 + Bilinear Finding 1 | **CONFIRMED** | `ihmf_io_multilayer.py` L211 stores raw absolute head; `fit_ihm_f_v3.py` L122 passes `head_m` unchanged; production JSON: S_ke=0 for F1, F2, F3, T1 |
| A2 | Script 12 uses zero-referenced head; production does not — they are inconsistent | ZeroTrust §1.2 | **CONFIRMED** | Script 12 `load_gwl_absolute()` L180: `series_zero = series - ref_val`; production never does this. Script 12 uses `fit_two_step_decoupled`; production uses plain NNLS inside `joint_solve_cumulative`. |
| A3 | Gate numbers in CLAUDE.md are stale | ZeroTrust §1.3 | **CONFIRMED** | CLAUDE.md says "F1=9.1× PASS, T2=9.3× PASS, F4=17.3× PASS." Live JSON (`tau_demo_TUKU/results/stress_strain_per_layer.json`): F1 feasible_2s=FALSE (ratio_2s=30.36× inside [3,50], but S_ske=6.54e-6 below floor 7.27e-6); T2 ratio_2s=5.32× PASS; F4 ratio_2s=10.76× PASS. Strings "9.1" and "9.3" do not appear in any file on disk. |
| A3a | F1 fails on ratio | ZeroTrust §1.3 (implied) | **REJECTED — CORRECTED** | F1 ratio_2s=30.36× is INSIDE [3,50]. F1 FAILS because S_ske_2s=6.54e-6 is BELOW the literature floor (7.27e-6 for proximal fan zone). The failure mode is floor violation, not ratio exceedance. |
| A4 | F2 "221×" is a mixed-thickness artifact, not a physics failure | ZeroTrust §1.4 | **CONFIRMED WITH CAVEAT — HUMAN DECISION REQUIRED** | Specific ratio = bulk ratio × (total span / clay thickness) = 25.10 × (106.284 m / 12.09 m) = 220.68×. Bulk ratio = 25.10× (inside [3,50]). However: CLAUDE.md §Gate states the gate applies to the specific-storage ratio $S_{skv}/S_{ske}$ (mixed thickness), NOT bulk. Ruling "artifact therefore gate on bulk" contradicts CLAUDE.md. Human must decide whether to change the gate definition before this can be resolved. |
| A5 | Pooled r2_mlcw_cum=0.649 is a misleading metric | ZeroTrust §1.5 | **CONFIRMED** | `TUKU_gps_v3_results.json`: F1 r2_cum=−10.77, F2=−3.13, F3=−12.46, F4=−18.68, T1=−5.89, T2=+0.71. The pool is dominated by F3 (obs_min −147 mm vs F1 −16 mm); the 0.649 aggregate is an arithmetic magnitude artifact. |
| A5a | Pooled R² code is in `fit_ihm_f_v3.py` lines 441–448 | Super plan Task 0.0 Step D | **SUPER-PLAN ERROR** | Pooled R² is computed in `ihmf_model_v3.py` lines 440–448 inside `joint_solve_cumulative`, NOT in `fit_ihm_f_v3.py`. The repair must target the correct file. |
| A6 | Walk-forward uses deprecated incremental solver | ZeroTrust §2.6 | **CONFIRMED** | `ihmf_model_v3.py` L871 calls `joint_solve_fixed_tau`; L506 labels that function "# ── Joint solve (incremental domain — legacy, deprecated 2026-06-08)." |
| A6a | n_inelastic=0 in all walk-forward folds | NEW FINDING | **CONFIRMED** | `TUKU_gps_v3_results.json` lines 836, 843, 850, 857, 864, 871 (Fold 1) and equivalent Fold 2: all 6 layers report `n_inelastic: 0`. The incremental solver never detects a permanent head exceedance below h_c — preconsolidation memory is completely lost. All walk-forward validation metrics are therefore invalid. |
| A7 | POST_MORTEM file is in trash/ not discussions/ | ZeroTrust §2.7 | **CONFIRMED** | `trash/POST_MORTEM_INCREMENTAL_CANCELLATION.md` found; `discussions/POST_MORTEM_INCREMENTAL_CANCELLATION.md` not found. PROGRESS.md references the discussions/ path. |
| A8 | RADIUS_M=10000 contradicts docstring "5 km" | ZeroTrust §2.8 | **CONFIRMED** | `scripts/05_pairing/build_mlcw_insar_gwl_pairs.py` L56: `RADIUS_M = 10000`; L27, L36: docstring says "within 5 km radius." One is wrong. |
| A9 | Super plan contains wrong machine paths | NEW FINDING (this audit) | **FIXED (2026-06-09)** | Original plan referenced `E:\Taiwan\...` and `C:\Users\Huy\anaconda4\python.exe` (Windows). Fixed to `/mnt/hgfs/1000_SCRIPTS/004_Project003/...` and `conda run -n isce_ncu3 python` (Ubuntu 22.04 VM). |
| A10 | RMSE bake-off tables (GWL bilinear vs GPS carrier vs linear interp) | Bilinear Report §Finding 2 | **UNVERIFIABLE on this machine** | `tmp_audit_test.py`, `tmp_audit_test2.py`, `tmp_audit_test3.py` are NOT present on this machine (Glob returned empty). All RMSE numbers in the report ran on `C:\Users\Huy\anaconda4\python.exe`. Do not use for method selection until reproduced in `fafalab` env. |
| A11 | Median absolute head values per well (+8.5 m HONGLUN, −8.2 m LUNZI) | Bilinear Report §Finding 1 | **UNVERIFIABLE on this machine** | S_ke=0 outcome is confirmed independently from production JSON. The specific median head values are from the same unverifiable test scripts. |
| A12 | Prior audit (INDEPENDENT_AUDIT_IHM_F_V3_20260607.md #3): code should negate MLCW for "positive = compaction" | Prior audit report | **REJECTED** | CLAUDE.md sign table is authoritative: MLCW "negative = compaction"; dh_raw "never negate." Code matches CLAUDE.md. The prior auditor cited a non-existent "GEMINI.md" rule. |

---

### 6.2 Confirmed Repair Tasks

#### REPAIR TASK R1 — Fix absolute-head datum bug in production loader and caller

**Physical meaning:** The earth does not compact in response to how far the water table sits above sea level. It compacts in response to how much the water table has dropped since a reference time. Using absolute hydraulic head (m MSL) instead of head change $u(t) = H(t) - H(t_{ref})$ means the elastic coefficient $S_{ke}$ is set by the arbitrary geodetic datum of each well, not by aquifer physics.

**Evidence (file:line):**
- `scripts/10_ihmf/ihmf_io_multilayer.py` L211: `df["head_m"] = gwl_aligned["head_m"].values` — raw absolute head, no referencing
- `scripts/10_ihmf/fit_ihm_f_v3.py` L122: `H_lag = d["head_m"][offset : offset + win_len]` — passes absolute head to solver
- `results/ihmf/v3/TUKU_gps_v3_results.json`: S_ke=0 for F1/HONGLUN (+8.5 m), F2/TUKU (+3.0 m), F3/TUKU (+3.0 m), T1/HONGLUN (+8.5 m); S_ke survives only for F4/LIUZHUANG (−1.2 m mixed) and T2/LUNZI (−8.2 m)

**Repair steps (description only — no .py edits in this plan section):**
1. In `ihmf_io_multilayer.py` `load_all_layers_gps`: after building `gwl_aligned["head_m"]`, compute `ref_val = series.loc[series.index <= REF_DATE].iloc[-1]` and add column `df["head_m_zeroed"] = series - ref_val`. Mirror Script 12 `load_gwl_absolute()` lines 154–181 exactly.
2. In `fit_ihm_f_v3.py` L122: replace `d["head_m"]` with `d["head_m_zeroed"]`.
3. In `ihmf_model_v3.py` `joint_solve_cumulative`: update the `H_lagged` slice to use `head_m_zeroed` key, not `head_m`.
4. After the fix: re-run TUKU pilot and verify S_ke > 0 for F1, F2, T1. S_ke may still be near-zero for F3 (n_elastic=7, H and V near-collinear) — that is expected.

**Depends on:** None
**Blocks:** ALL downstream parameter estimates, ratio gate checks, gap-fill evaluation
**Priority:** P1 — **DONE (2026-06-09)**

---

#### REPAIR TASK R2 — Fix h_c zero-referencing in production loader (Bug F regression)

**Physical meaning:** The preconsolidation head $h_c$ is the lowest hydraulic head the sediment column has experienced before the reference date. After zero-referencing, it must live in the same coordinate frame as $H(t)$. If $H$ is zero-referenced but $h_c$ is still in absolute MSL, the virgin term $V(t) = \min(0, \text{cummin}(H) - h_c)$ will be mis-computed, misclassifying the elastic/inelastic regime for every epoch.

**Evidence (file:line):**
- `scripts/10_ihmf/ihmf_io_multilayer.py` L218–222: `h_c = pre_ref["head_m"].dropna().min()` — absolute MSL, not shifted
- Script 12 `load_gwl_absolute()` L175–178: returns `h_c_m = series_zero[:ref_idx].min()` — already zero-referenced

**Repair steps (description only):**
1. After computing `ref_val` (R1 step 1), compute `h_c_abs = series.loc[series.index <= REF_DATE].dropna().min()` and store `df["h_c_zeroed"] = h_c_abs - ref_val`.
2. Fallback case (< 10 pre-2015 points): apply the same shift to the full-record minimum. Log a warning: "Fewer than 10 pre-REF_DATE points for well {wellcode} layer {layer} — h_c fallback applied."
3. Update `joint_solve_cumulative` to read `h_c_zeroed` rather than the current `h_c` field.

**Depends on:** R1
**Blocks:** Virgin term $V(t)$, regime classification, n_elastic/n_inelastic counts
**Priority:** P1 — **DONE (2026-06-09)**

---

#### REPAIR TASK R3 — Replace deprecated walk-forward solver with cumulative solver

**Physical meaning:** In the incremental domain ($\Delta b$, $\Delta H$), seasonal head oscillations dominate and the sediment column's preconsolidation memory (accumulated since the last full virgin consolidation) is invisible within any single 5-day step. The cumulative domain carries this memory explicitly through $V(t) = \min(0, \text{cummin}(H) - h_c)$. Using the incremental solver in walk-forward validation means the inelastic regime is never detected: all 6 layers report n_inelastic=0 in every fold.

**Evidence (file:line):**
- `ihmf_model_v3.py` L506: function `joint_solve_fixed_tau` labeled "# ── Joint solve (incremental domain — legacy, deprecated 2026-06-08)"
- `ihmf_model_v3.py` L871: `result = joint_solve_fixed_tau(...)` — walk-forward calls the deprecated function
- `results/ihmf/v3/TUKU_gps_v3_results.json` Fold1 L836, 843, 850, 857, 864, 871: all `"n_inelastic": 0`

**Repair steps (description only):**
1. In the walk-forward section of `ihmf_model_v3.py`, replace the call at L871 to `joint_solve_fixed_tau` with a call to `joint_solve_cumulative`.
2. Ensure the training-window data slice passed to `joint_solve_cumulative` contains cumulative MLCW compaction and zero-referenced cumulative head (not differences).
3. After the fix, verify that clay-dominated layers (T1, T2, F3, F4) show n_inelastic > 0 in at least one fold.

**Depends on:** R1, R2
**Blocks:** Walk-forward validation metrics; Obj 1 held-out test (the one-week deliverable)
**Priority:** P2 — **DONE (2026-06-09)**

---

#### REPAIR TASK R4 — Update stale gate numbers in CLAUDE.md

**Physical meaning:** The gate numbers guide whether to trust a layer's storage parameters. Stale numbers cause the team to report passing results for layers that actually fail, and to misstate the failure reason for layers that do fail.

**Actual values from `tau_demo_TUKU/results/stress_strain_per_layer.json` (two-step specific-ratio basis):**

| Layer | ratio_2s | $S_{ske}$ (m⁻¹) | feasible_2s | Failure reason |
|-------|----------|-----------------|-------------|----------------|
| F1 | 30.36× | 6.54e-6 | FALSE | $S_{ske}$ below literature floor (7.27e-6) — NOT a ratio failure |
| T1 | null | null | null | $S_{ke,2s}=0$ (OLS gave negative, clamped) |
| F2 | 220.68× | 4.94e-6 | FALSE | Specific ratio exceeds [3,50] — mixed-thickness artifact; bulk ratio = 25.1× (see A4 caveat) |
| T2 | 5.32× | 5.99e-5 | TRUE | Passes all bounds |
| F3 | null | null | null | $S_{ke,2s}=0$ (nnls_fallback, n_elastic=7) |
| F4 | 10.76× | 3.59e-5 | TRUE | Passes all bounds |

Note: "17.3×" in CLAUDE.md refers to F4 simultaneous-NNLS `ratio_Skv_Ske=17.343`, not the two-step ratio_2s=10.76×. Gate uses the two-step specific ratio.

**Repair steps (description only — human must update CLAUDE.md):**
1. Replace the "Corrected gate (2026-06-07)" line in CLAUDE.md with the actual two-step values above.
2. Add a note that F1 fails on $S_{ske}$ floor, not on ratio.
3. Add a note that F4 "17.3×" is the simultaneous-NNLS bulk ratio; two-step specific ratio is 10.76×.
4. Add a note that gate numbers will change after R1/R2 fix zero-referencing — do not finalize gate status until then.
5. Resolve the F2 gate ambiguity (specific vs bulk) as a separate human decision (see A4 caveat).

**Depends on:** None (documentation fix)
**Blocks:** Prevents new contributors from trusting wrong pass/fail assignments
**Priority:** P2 — **DONE (2026-06-09)**

---

#### REPAIR TASK R5 — Fix wrong machine paths in this super plan

**Physical meaning:** A plan that references a non-existent Windows drive letter ($E:\Taiwan$) and a different user's Python interpreter ($C:\Users\Huy$) cannot be executed on this Ubuntu 22.04 VM. Every command block in the plan would fail.

**Evidence:**
- `plans/super_plan_2026-06-09.md` L5: `E:\Taiwan\programming\Python\David\20260427_InSAR_MLCW_v2` (does not exist)
- `plans/super_plan_2026-06-09.md` L7: `& "C:\Users\Huy\anaconda4\python.exe"` (does not exist)
- Actual repo: `/mnt/hgfs/1000_SCRIPTS/004_Project003/20260427_InSAR_MLCW_v2` (Linux VM)
- Actual env: `isce_ncu3`; command: `PYTHONPATH="" conda run -n isce_ncu3 python`

**Also:** Task 0.0 Step D references `fit_ihm_f_v3.py` lines 441–448 for the pooled R² code. The actual location is `ihmf_model_v3.py` lines 440–448.

**Repair applied (2026-06-09):**
1. Replaced header block with Ubuntu 22.04 VM path and `isce_ncu3` conda env.
2. Replaced all `$env:PYTHONPATH=""; & "C:\Users\Huy\anaconda4\python.exe"` with `PYTHONPATH="" conda run -n isce_ncu3 python` throughout the plan.
3. Corrected Task 0.0 Step D file reference from `fit_ihm_f_v3.py` to `ihmf_model_v3.py` (lines 440–448).

**Depends on:** None
**Blocks:** Any command block in this plan would fail on this machine
**Priority:** P1 — **DONE**

---

#### REPAIR TASK R6 — Move POST_MORTEM file to correct location

**Physical meaning:** PROGRESS.md references `discussions/POST_MORTEM_INCREMENTAL_CANCELLATION.md`. The file lives at `trash/POST_MORTEM_INCREMENTAL_CANCELLATION.md`. Any contributor following the PROGRESS.md pointer will get a file-not-found error.

**Repair steps:**
1. Copy `trash/POST_MORTEM_INCREMENTAL_CANCELLATION.md` to `discussions/POST_MORTEM_INCREMENTAL_CANCELLATION.md`.
2. Leave the `trash/` copy in place (project convention: never delete, only rename with `_OBSOLETE_` suffix or move).
3. Update the reference in PROGRESS.md to confirm the discussions/ path.

**Depends on:** None
**Priority:** P3 — **DONE (2026-06-09)**

---

#### REPAIR TASK R7 — Resolve RADIUS_M discrepancy in GWL pairing script

**Physical meaning:** The GWL-to-MLCW pairing radius determines which groundwater wells are assigned to each compaction layer. A 10 km radius captures twice the area of a 5 km radius and may include wells that are geologically inappropriate (e.g., from the wrong fan sub-zone or a different aquifer system). A 5 km radius may exclude valid nearby wells.

**Evidence:**
- `scripts/05_pairing/build_mlcw_insar_gwl_pairs.py` L56: `RADIUS_M = 10000`
- Same file L27, L36: docstring says "within 5 km radius"

**Repair steps (human decision required):**
1. Decide the physically correct radius for CRAF pairing (project hydrogeology decision).
2. Update either the code constant or the docstring to be consistent. Do not change both to an undocumented value.
3. If 10 km is correct, verify that `gwl_to_mlcw_layer_assignment_v4.csv` was generated with 10 km; if it was generated with 5 km, re-run the pairing script and update the CSV.

**Depends on:** None
**Priority:** P3 — **DONE (2026-06-09)**

---

### 6.3 Rejected Auditor Claims

| ID | Claim | Reason for Rejection |
|----|-------|----------------------|
| A12 | Prior audit INDEPENDENT_AUDIT_IHM_F_V3_20260607.md #3: negate MLCW to match "positive = compaction" | CLAUDE.md sign table is authoritative. MLCW convention: "negative = compaction." dh_raw convention: "never negate." Code matches CLAUDE.md. The cited rule came from a non-existent "GEMINI.md." |
| A3a | F1 fails on ratio exceedance | F1 ratio_2s=30.36× is INSIDE [3,50]. F1 fails because $S_{ske,2s}=6.54 \times 10^{-6}$ is below the Hung et al. (2021) literature floor ($7.27 \times 10^{-6}$ m⁻¹ for proximal fan zone). The failure mode is a storage-coefficient floor violation, not a ratio violation. |
| A1-partial | Claim: "no intercept at all" in production | `joint_solve_cumulative` computes `c_intercept` in Step 2 for InSAR-alignment. This is correct behavior. The real bug is that Step 1 per-layer NNLS receives absolute head, not zero-referenced head. An MLCW intercept in Step 1 would partially mask the bug but would not fix the physics. The principled fix is zero-referencing the head input (R1). |

---

### 6.4 Unverifiable Issues — Flagged for Human Review

| ID | Claim | Why Unverifiable | Action Required |
|----|-------|-----------------|-----------------|
| A10 | RMSE bake-off: GWL bilinear vs GPS carrier vs linear interp | `tmp_audit_test.py`, `tmp_audit_test2.py`, `tmp_audit_test3.py` not found on this machine. All numbers ran on `C:\Users\Huy\anaconda4\python.exe`. | Reproduce all three scripts in `fafalab` env before using results for method selection. |
| A11 | Median absolute head values per well (+8.5 m HONGLUN, −8.2 m LUNZI, etc.) | Same unverifiable scripts. S_ke=0 outcome is confirmed; the specific median values are not. | Verify by reading the raw GWL feather for each wellcode. |
| A4-gate | F2 "221×" specific-ratio artifact: should the gate use bulk ratio instead? | CLAUDE.md §Gate mandates specific-ratio gate. Auditor says bulk ratio is the fair comparison. These contradict each other; resolving it requires changing CLAUDE.md, which requires human authorization. | Human decision: choose bulk or specific ratio for the gate and update CLAUDE.md accordingly. Document the physical justification. |
| A6b | Will re-wiring walk-forward to cumulative solver (R3) produce n_inelastic > 0? | R3 fix is confirmed necessary; the outcome (whether the fixed solver yields physically correct regime classification for all 6 layers) cannot be verified without running the repaired code. | Run TUKU pilot after R1+R2+R3 and check n_inelastic per layer for each fold. |

---

### 6.5 Repair Priority Order and One-Week Impact

| Priority | Task | Blocking for | Estimated effort | Status |
|----------|------|-------------|-----------------|--------|
| P1 | R1 — Zero-reference head in production loader | All parameter estimates | 1–2 h | **DONE** |
| P1 | R2 — Fix h_c coordinate-frame shift (Bug F) | Virgin term, regime classification | 0.5 h | **DONE** |
| P1 | R5 — Fix wrong machine paths in this plan | Any command block on this machine | 0.5 h | **DONE** |
| P2 | R3 — Wire walk-forward to cumulative solver | Walk-forward validation, Obj 1 held-out test | 1–2 h | **DONE** |
| P2 | R4 — Update stale gate numbers in CLAUDE.md | Documentation accuracy | 0.5 h | **DONE** |
| P3 | R6 — Move POST_MORTEM to discussions/ | Reference integrity | 0.1 h | **DONE** |
| P3 | R7 — Resolve RADIUS_M discrepancy | GWL pairing completeness | 0.5 h | **DONE** |

**One-week constraint:** The only one-week deliverable is the Obj 1 TUKU held-out test (PROGRESS.md). That test requires: correct zero-referenced head (R1), correct h_c referencing (R2), and a working cumulative walk-forward (R3). None of the held-out RMSE numbers in `Bilinear_Model_Test_Findings_20260609.md` can be trusted until R1+R2 are applied on this machine (`fafalab` env) and the bake-off scripts are reproduced. The gate numbers in CLAUDE.md (R4) will change once R1+R2 run — do not finalize method selection on pre-fix results.

**Method pivot warning:** The super plan promotes GPS carrier as the primary gap-fill method based on RMSE numbers from unverifiable scripts (A10). This is a consequential method decision. Do not confirm the pivot until A10 is reproduced in `fafalab` env and R1+R2 are applied to the GWL bilinear baseline. The GWL bilinear model may perform better once the absolute-head bug is fixed.

#### TASK 2.2.2 — Stations with thin/no surface or GWL coverage

**Physical meaning:** Some pixels have noisy InSAR or a station sits between pixels; some GWL wells start late. Record coverage and, where the carrier is unavailable, fall back to interpolation/IDW of neighbouring stations' apportionment shares.

**Depends on:** TASK 2.1.2.

- [ ] Step A: For each SKIP, record surface/GWL start dates and coverage fraction. Print table.
  - **Success check:** No OK-eligible station has coverage 0.
- [ ] Step B: For stations missing the carrier, IDW the `a_k` shares from the nearest 3 covered stations; write `a_k_idw` to `batch_summary.csv`.
  - **Success check:** IDW values within the source range.

---

## PART 3 — Obj 3: Regional Grid Prediction (8,577 Points)

**Physical narrative:** This is where the carrier method shines: InSAR is measured at every grid point already. At each grid point, predicted per-layer compaction = apportionment shares (transferred by fan zone / hydrofacies from the calibrated stations) × the grid point's InSAR displacement. GWL is interpolated only as a secondary covariate.

**Depends on:** PART 2 PASS.

### PHASE 3.1 — Apportionment-Share Transfer Model

#### TASK 3.1.1 — Fan-zone / hydrofacies lookup

**Physical meaning:** Without a borehole at a grid point, the layer shares must be borrowed from stations in the same hydrogeological setting (proximal gravel / middle sand / distal clay).

**Depends on:** PART 2.

- [ ] Step A: Search `D:\112_PROJECT_002` (companion docs repo, if mounted) and the local `data\` for a CRAF hydrofacies/fan-zone product. If absent, use the Hung et al. (2021) fan-zone boundaries (already encoded in `scripts\guardrails.py` priors).
  - **Success check:** A fan-zone source is identified or "not sourced" recorded in PROGRESS.md.
- [ ] Step B: Map the 8,577 grid points to {proximal, middle, distal}. Write `data\grid\grid_fan_zone_lookup.csv` (`grid_id, lon, lat, fan_zone`).
  - **Success check:** 8,577 rows; fan_zone ∈ the three values.

#### TASK 3.1.2 — Zone-mean apportionment shares

**Physical meaning:** Average the calibrated `a_k` from PART 2 stations within each fan zone to get a transferable per-layer share per zone.

**Depends on:** TASK 3.1.1; PART 2 batch.

- [ ] Step A: For each fan zone and layer, compute mean and spread of `a_k` across that zone's stations. Write `data\grid\zone_apportionment_shares.csv`.
  - **Success check:** Table with `fan_zone, layer, a_k_mean, a_k_std, n_stations`.
- [ ] Step B: Cross-check the bilinear `S_ke/S_kv` zone means against Hung et al. (2021) priors (within 2× for middle/distal). Flag discrepancies.
  - **Success check:** Comparison table; discrepancies > 2× explained.

### PHASE 3.2 — Grid Prediction Script

#### TASK 3.2.1 — Predict grid compaction from InSAR + transferred shares

**Physical meaning:** At each grid point, per-layer compaction = zone share × grid InSAR displacement; total = sum across layers. GWL-interpolation is added only where it improved held-out skill in Part 1.

**Depends on:** TASK 3.1.2.

- [ ] Step A: Write `scripts\20_grid_prediction\01_predict_grid_compaction.py` reading grid InSAR timeseries, the zone-share lookup, and producing per-layer cumulative compaction NetCDF `results\grid_prediction\compaction_3d_per_layer.nc` (grid_id × layer × time).
  - **Success check:** NetCDF written; at MLCW-station grid cells, values within 20% of the PART 2 station reconstruction (spatial consistency).
  - **Command:** `PYTHONPATH="" conda run -n isce_ncu3 python scripts\20_grid_prediction\01_predict_grid_compaction.py`

### PHASE 3.3 — Spatial Hold-Out Validation

#### TASK 3.3.1 — Withheld-station spatial test

**Physical meaning:** Reserve whole stations from the share calibration; predict them from zone shares + their own InSAR; this isolates spatial-transfer skill.

**Depends on:** TASK 3.2.1.

- [ ] Step A: Withhold 5 stations spanning all 3 zones. Re-derive zone shares without them.
  - **Success check:** 5 stations across zones listed.
- [ ] Step B: Predict their compaction from zone shares × their InSAR; compute RMSE and R² per layer.
  - **Success check:** R² ≥ 0 for ≥ 4 of 5 at F1, T2, F4.

> **DECISION POINT 5 (spatial transfer):**
> - **PASS:** RMSE_grid < 2× RMSE_station. Proceed to PART 5.
> - **FAIL:** ≥ 2×. Check which zone transfers poorly; refine zone boundaries or share-weighting before proceeding.

---

## PART 4 — Quality Gates and Guardrails

**Purpose:** Wire `scripts\guardrails.py` into every new script, AND add a held-out-skill gate so no method is promoted on in-sample fit alone (the original failure mode).

**Depends on:** Each task as completed.

### PHASE 4.1 — Guardrail + skill-gate wiring

#### TASK 4.1.1 — Parameter guardrails in characterization scripts
- [ ] Step A: Confirm `13_holdout_method_bakeoff.py`, `14_carrier_reconstruction_tuku.py`, `15_batch_reconstruction.py` import and call the relevant guardrails before writing parameters; bilinear params go through `validate_layer_params`.
  - **Success check:** grep shows guardrail imports; no GuardrailViolation on TUKU.

#### TASK 4.1.2 — Held-out skill gate (NEW)
**Physical meaning:** A method may only be promoted to gap-fill if it beats the static baseline on held-out data. This gate encodes the project's own success criterion and prevents repeating the in-sample-R² trap.
- [ ] Step A: Add `assert_beats_baseline(rmse_method, rmse_baseline, layer)` to `scripts\guardrails.py`; raise/warn if `skill ≤ 0`.
  - **Success check:** New unit test added; full suite still passes.
  - **Command:** `PYTHONPATH="" conda run -n isce_ncu3 python scripts\guardrails.py`

---

## PART 5 — Publication-Ready Outputs

**Purpose:** Figures, tables, narrative-support files. Built after Parts 1–3.

**Depends on:** PART 2 PASS; PART 3 complete.

### PHASE 5.1 — Reconstruction figures
- [ ] TASK 5.1.1: `scripts\21_figures\plot_reconstruction_per_station.py` → 6-panel modeled-vs-observed with gap shading and held-out skill annotation, per station. 300 dpi, A4. Output `results\figures\reconstruction\{STATION}_reconstruction_6layer.png`.
  - **Success check:** 37 PNGs; each shows held-out skill (not just calibration R²).

### PHASE 5.2 — Regional subsidence map
- [ ] TASK 5.2.1: `scripts\21_figures\plot_regional_map.py` → filled-contour total compaction over 8,577 points with 37 stations overlaid. Output `results\figures\regional_map\CRAF_total_subsidence_2015_2025.png`.
  - **Success check:** Colorbar "Cumulative subsidence (mm)"; stations marked.

### PHASE 5.3 — Parameter + skill tables
- [ ] TASK 5.3.1: From `batch_summary.csv` + `batch_holdout_eval.csv`, write `results\tables\parameter_table_all_stations.tex` with per-layer $S_{ke}$, $S_{kv}$, bulk ratio, $\tau$ (days), calibration R², AND held-out gap-fill skill. Footnote the mixed-thickness specific ratio caveat and the `S_ke_identifiable` flag.
  - **Success check:** 191 rows; compiles; skill column present.

---

## Appendix A — File Naming and Path Conventions

- Active outputs: no suffix. Obsolete: `_OBSOLETE_<reason>` suffix — never deleted.
- All scripts use `from paths import RESULTS_ROOT, DATA_ROOT, SCRIPTS_ROOT` — no hardcoded `D:\` or `E:\` literals inside scripts. Run scripts from repo root.
- GWL wellcodes are 8-digit strings (`"09050111"`, never int). Use the glob `*gwl*timeseries.feather` (the bare `*.feather` also matches the GPS feather and corrupts loading).
- REF_DATE = 2015-01-16. Head must be zero-referenced (`u = H - H_ref`) before entering any elastic term; `h_c` is the pre-REF_DATE raw minimum (Bug F). InSAR feather values are metres → ×1000 for mm; GPS `modeled` is already mm.

## Appendix B — Environment Commands Reference (Ubuntu 22.04 VM)

```bash
# Interpreter (isce_ncu3 conda env, scipy ≥ 1.17)
PYTHONPATH="" conda run -n isce_ncu3 python <script>

# Part 0 — reproduce bug + bake-off (reference scripts already in repo root)
PYTHONPATH="" conda run -n isce_ncu3 python tmp_audit_test.py
PYTHONPATH="" conda run -n isce_ncu3 python tmp_audit_test2.py
PYTHONPATH="" conda run -n isce_ncu3 python tmp_audit_test3.py

# Part 0 — permanent bake-off + corrected production fit
PYTHONPATH="" conda run -n isce_ncu3 python tau_demo_TUKU/13_holdout_method_bakeoff.py
PYTHONPATH="" conda run -n isce_ncu3 python scripts/10_ihmf/fit_ihm_f_v3.py --station TUKU --gps --all --alpha 0.625

# Part 1 — carrier reconstruction / prediction / recalibration
PYTHONPATH="" conda run -n isce_ncu3 python tau_demo_TUKU/14_carrier_reconstruction_tuku.py
PYTHONPATH="" conda run -n isce_ncu3 python tau_demo_TUKU/14_carrier_reconstruction_tuku.py --predict_to 2025-12-31
PYTHONPATH="" conda run -n isce_ncu3 python tau_demo_TUKU/14_carrier_reconstruction_tuku.py --recalib_date 2022-06-30

# Part 2 — batch
PYTHONPATH="" conda run -n isce_ncu3 python scripts/10_ihmf/15_batch_reconstruction.py --stations TUKU YUANCHANG XIUTAN
PYTHONPATH="" conda run -n isce_ncu3 python scripts/10_ihmf/15_batch_reconstruction.py --all

# Guardrails unit tests (now includes the held-out skill gate)
PYTHONPATH="" conda run -n isce_ncu3 python scripts/guardrails.py
```

## Appendix C — Audit Findings This Plan Encodes (do not regress)

1. **Datum bug:** production `joint_solve_cumulative` used absolute head + no intercept → `S_ke=0` for positive-head wells (HONGLUN/TUKU). Fixed in Phase 0.0. Verify with the absolute-vs-zero-ref table in `plans/Bilinear_Model_Test_Findings_20260609.md`.
2. **Stale gate numbers:** "F1=9.1× / T2=9.3× / F4=17.3×" are NOT in any result file. Live `stress_strain_per_layer.json`: F1=30.36× FAIL, T2=8.42× PASS, F4=10.76× PASS, F2=220.7× (thickness artifact). Use live files only.
3. **Mixed-thickness ratio:** the specific-storage ratio divides $S_{ske}$ by total span but $S_{skv}$ by clay-only thickness — not comparable to Hung et al. Use the bulk ratio for the elastic/inelastic contrast; flag the artifact.
4. **Bilinear ≠ gap-fill:** held-out tests show the GWL bilinear model is the worst gap-fill method on every layer. It is for parameter characterization only. The carrier (InSAR/GPS) is the gap-fill engine.
5. **Never promote on in-sample R²:** the pooled `r2_mlcw_cum=0.65` was an artifact; every per-layer R² was negative. Part 4's held-out skill gate prevents this.

---

*Plan revised: 2026-06-09 after zero-trust audit. Supersedes the single-method version (`_OBSOLETE_pre_audit_single_method.md`). Status: planning + verified reference scripts (`tmp_audit_test*.py`) exist; no production code modified by this revision.*
