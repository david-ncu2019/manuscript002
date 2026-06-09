# PROGRESS.md — InSAR–MLCW Subsidence Analysis

> **This is the single authoritative PROGRESS.md** (merged 2026-06-05; content from docs repo 2026-06-04).
> All future updates go here only.

**Date:** 2026-06-08
**Status:** 🚨 CIRCUIT BREAKER — IHM-F v3 incremental solver structurally failed at TUKU (2026-06-08). Script 12 cumulative approach SUCCEEDED. **Key finding:** The 5-day incremental formulation $\Delta b = S_k \cdot \Delta H$ cannot accumulate the observed monotonic MLCW compaction because seasonal head oscillations (±2 m/yr) approximately cancel — the model predicts 0.1–0.9 mm/yr while MLCW records 8–15 mm/yr (8–355× gap). $R^2_{\text{MLCW,cum}}$ is negative or NaN for all 6 layers. Root cause is a physical domain mismatch: the incremental solver operates on the derivative of head (a stationary oscillatory signal) while MLCW compaction is the integral of maximum historical stress (a monotonic cumulative signal). The Riley (1969) preconsolidation memory is lost in the first-difference transformation. **Day 2 GPS mask fix completed but insufficient** — F2/F3 GWL wells (09050321, 09050331) only start 2012-08, so 2003-2012 inelastic era has zero GWL data regardless of the GPS mask. **Next:** tactical pivot — decide between cumulative-solver fork, per-layer Script 12 calibration, or data-driven fallback. See `discussions/POST_MORTEM_INCREMENTAL_CANCELLATION.md` for full post-mortem.

---

## 0. Research Objectives (Corrected 2026-06-09)

MLCW (Multi-Layer Compaction Well) monitoring wells in the Choushui River Alluvial Fan (CRAF) have stopped operating or reduced sampling from monthly to semi-annual/annual due to maintenance costs. The core problem is a broken observational record, not a model calibration exercise. InSAR (Interferometric Synthetic Aperture Radar) and GWL (groundwater level) data are continuously available and must substitute for the lost in-situ measurements.

**Three research objectives:**

1. **Obj 1 — Well-scale gap-fill and prediction (MLCW stations):** At each active MLCW station, use InSAR timeseries + GWL timeseries + borehole stratigraphy to (a) reconstruct historical compaction timeseries where MLCW data is missing or sparse, (b) predict next-month MLCW compaction, and (c) self-recalibrate when new sparse in-situ measurements become available.
   - Success criterion: gap-fill RMSE < RMSE of static linear interpolation baseline; walk-forward skill score > 0 on held-out epochs.

2. **Obj 2 — Multi-well extension:** Apply the Obj 1 method validated at TUKU pilot to all remaining MLCW stations (up to 37 stations).
   - Success criterion: Obj 1 criteria met at ≥ 80% of stations.

3. **Obj 3 — Regional grid prediction (8,577 points, no MLCW):** Predict subsurface compaction at 8,577 regional grid points with no MLCW instrumentation, using InSAR + regionally-interpolated GWL + open-source hydrofacies model (1 km × 1 km resolution).
   - Success criterion: spatial transfer validated against withheld MLCW stations; hydrofacies-to-parameter pathway resolved against CRAF literature.

**One-week time constraint:** Only the TUKU pilot evaluation (Obj 1 held-out test) must complete within the current working week. Obj 2 and Obj 3 are follow-on phases.

**Current phase:** Method review. Terzaghi consolidation theory formulated as a cumulative two-regressor NNLS (Script 12, `tau_demo_TUKU/12_stress_strain_per_layer.py`) is under evaluation as the candidate gap-fill/prediction method — NOT confirmed. No method is finalized.

---

## 1. Current Methodology (Locked — updated 2026-05-29)

**Model:** IHM-F v3 — joint constrained least squares, GWL-only per-layer drivers

**Two-step procedure (from `discussions/physics_rules_research_problem.md`):**

**Step 1 — Per-layer fit (MLCW + GWL only, no InSAR):**
```
min_{S_j, τ_j}  Σ_t | S_j · ΔH_j(t − τ_j) − Δb_j(t) |²

  S_j = S_ke  (elastic regime: ΔH_j ≥ 0)
  S_j = S_kv  (inelastic regime: head below pre-consolidation threshold)
  τ_j ∈ {0, 1, 2, …, 120}  — integer epoch index, 5-day units (τ=6 ≈ 1 month, τ=120 = 600 days)
```

**Step 2 — Surface alignment (InSAR only, $S_{j}$ and $\tau$_j fixed from Step 1):**
```
min_α  Σ_t | (1/α) · Σ_j S_j · ΔH_j(t − τ_j) − Δd_v(t) |²

  α ∈ (0, 1)  — single scalar per station
```

**Implemented as a single joint solve** for computational efficiency: design matrix stacks MLCW rows (pin $S_{j}$) and InSAR rows (pin $\alpha$), solved with `scipy.optimize.lsq_linear` with bounds $S_{j}$ $\ge$ 0, $\beta$ = 1/$\alpha$ $\ge$ 1. $\lambda$ = 1/N balances InSAR vs MLCW weight.

**What changed from v1/v2:**
- `b_k · Δx(t)` term **removed entirely** — InSAR is the target in Step 2, not a per-layer predictor
- Two-path routing (Path A / Path B based on 2S-TOOL) **removed** — single uniform procedure for all 191 pairs
- $\tau$_max raised from 24 → 73 → **120** (600 days; T1 shallow aquitard needs >365d search room)
- 2S-TOOL $S_{kv}$/$S_{ke}$ values are **diagnostic reference only** — not used as fixed priors

---

## 2. Quantitative Data State

| Metric | Value |
|--------|-------|
| MLCW stations (layer-grouped) | 37 (JINHU_XIN + LUNFENG_XIN excluded) |
| Station-layer pairs total | 191 |
| 2S-TOOL OK (diagnostic reference only) | 134 |
| 2S-TOOL NEG_SKV (diagnostic reference only) | 57 |
| 2S-TOOL errors | 6 (excluded) |
| GWL feather files (MLCW-timeline-aligned) | 189 |
| Layers healthy (GWL-driven, low collinearity) | 84 / 191 (44%) |
| Layers weak GWL coupling | 74 |
| Layers high collinearity (raw; clears after detrend) | 16 |
| TUKU pilot: layers fitted | 6 / 6 |
| TUKU b_k = 0 layers (InSAR-dominated) | 2 (F1, F3) |
| F1 raw r($\Delta$ H, x) → detrended | 0.66 → 0.19 |
| F3 raw r(y, $\Delta$ H) → detrended | 0.15 → 0.29 |
| VIF after detrending (median) | < 1.5 |
| Optimal lag $\tau$_opt range (epochs) | F1=6, T1=4, F2=11, T2=7, F3=9, F4=8 |

---

## 3. Pipeline Status

| Stage | Status |
|-------|--------|
| MLCW preprocessing (decompose, reconstruct, 5m regularisation) | Complete |
| MLCW layer aggregation (ring → F1/T1/F2/T2/F3/F4) | Complete — 37 stations |
| GWL-to-MLCW layer assignment | Complete v4 — 195 rows, 13 wellcodes updated 2026-06-04, all coverage_2023_2025 ≥ 100 |
| GWL timeseries extraction (MLCW-timeline-aligned) | Complete — 189 feather files |
| 2S-TOOL pipeline ($S_{kv}$, $S_{ke}$ reference values) | Complete — 134 OK, 57 NEG_SKV, 6 errors (diagnostic reference only) |
| Direct ratio baseline (static scaling f̄_k) | Complete — comparison floor |
| Data analysis (collinearity, lag, coupling diagnostics) | Complete — 8 scripts, 191 layers |
| Universal model resolution document | Complete — `discussions/2026-05-29-ihmf-universal-model-resolution.md` |
| IHM-F v3 architecture design (joint solve, $\tau$_max=73, no $\beta$_k$\cdot$ x) | Complete — 2026-05-29 |
| **Tau search campaign (TUKU, 7 scripts)** | **Complete — 2026-05-30; see §12 in discussion_memory.md** |
| **Detrending module (`ihmf_detrend.py`)** | **Complete — 2026-05-30; in `scripts/10_ihmf/`** |
| **Seasonal $S_{ske}$ diagnostic (TUKU pilot)** | **Complete — 2026-05-30; sinusoidal >5% at 3/6 layers** |
| **Batch detrended MLCW outputs (39 stations)** | **Complete — 2026-05-31; figures + CSVs in `figures/modeled_nojump/`** |
| **ML/DL brainstorm + teaching guide** | **Complete — 2026-05-30; see `discussions/discussion_20260530_ml_brainstorm*.md`** |
| **Seasonal harmonic pipeline (`scripts/13_seasonal_insar/`, 2 scripts)** | **Complete — 2026-05-31** |
| **Seasonal harmonic 3-station pilot (TUKU, XIUTAN, YUANCHANG)** | **Complete — 2026-05-31; all 3 PASS gate** |
| **Seasonal reconstruction visualization (3 stations)** | **Complete — 2026-05-31** |
| **All 37-station seasonal harmonic batch** | **Complete — 2026-06-01; 37/37 OK; insar_harmonic_timeseries.feather exists for all stations** |
| **Ring cross-correlation analysis (3 sources $\times$ 39 stations)** | **Complete — 2026-05-31; split-triangle heatmap per station** |
| **annual_PASS gate fix (corr_A1 > 0.0 added)** | **Complete — 2026-06-01; fixes anti-correlated F1 at TUKU** |
| **R2_seasonal runtime guard ($\le$ 0.0 → revert)** | **Complete — 2026-06-01; in `02_reconstruction_visualization.py`** |
| **Walk-forward prediction pipeline (`scripts/15_prediction/`, 8 modules)** | **Complete — 2026-06-01; leakage-free per-fold fbar** |
| **37-station walk-forward batch** | **Complete — 2026-06-01; 387 rows; 18 active stations; 19 closed before 2022** |
| **TUKU Day 3 evaluation (epoch CSV + JSON + 6 timeseries figures)** | **Complete — 2026-06-01; see `results/prediction_v1/`** |
| **walkforward.py Tier 1 fix — detrended + lag-aware model** | **Complete — 2026-06-01; `trend + α×InSAR_det(t−τ)` replaces static f̄_k; $\alpha$$\ge$ 0 gate; $\tau$ grid search** |
| **prediction_v2 TUKU run — detrended model evaluation** | **Complete — 2026-06-01; F1/T2 improve (−37% to −60% RMSE); F2/F3/F4 $\alpha$<0 → trend-only fallback** |
| **InSAR-only ceiling confirmed** | **Complete — 2026-06-01; F2/F3/F4 residual anti-correlated with InSAR; GWL required for main aquifers** |
| **tau_demo_TUKU v2 experiment setup** | **Complete — 2026-06-04; TAU_MAX=120, v4 assignments, Bug F (h_c window) found; fix applied 2026-06-05** |
| **tau_demo_TUKU — lag-consistency bugs (Bugs 1–3)** | **Complete — 2026-06-05/06; 3 lag-consistency fixes in ihmf_model_v3.py + fit_ihm_f_v3.py; regime mask sliced at driver-time index** |
| **tau_demo_TUKU — TUKU pilot 5-day incremental (11_fit_ihm_f_incremental.py)** | **Complete — 2026-06-06; all 6 layers fail 8–100× ratio gate; structural failure in per-epoch incremental domain confirmed** |
| **12_stress_strain_per_layer.py (cumulative domain, per-layer)** | **Complete — 2026-06-06; two-regressor NNLS. Specific-storage gate (2026-06-07 correction): F1=9.1× PASS, T2=9.3× PASS, F4=17.3× PASS; T1=2.9× FAIL; F2=221× FAIL; F3 S_ke=0. Decoupled two-step fit extension planned.** |
| **CLAUDE.md restructure + knowledge file merge** | **Complete — 2026-06-05; both CLAUDE.md files restructured; 12 discussion/notes/plans files merged from docs repo** |
| Multi-layer data assembler (`ihmf_io_multilayer.py`) | **Complete — operational, imported by `fit_ihm_f_v3.py`** |
| Joint solver (`ihmf_model_v3.py`) | **CIRCUIT BREAKER (2026-06-08) — incremental formulation structurally fails; $R^2_{\text{MLCW,cum}}$ negative/NaN for all 6 TUKU layers; 8–355× prediction gap** |
| **Day 2 α fix (2026-06-08): 4 code changes + compute_alpha_empirical.py** | **COMPLETE — commit 182b8d6; GPS mask decoupled, alpha_external param, --alpha CLI, TUKU α=0.625 verified** |
| **Day 3 TUKU GPS re-run (2026-06-08)** | **COMPLETE — `TUKU_gps_v3_results.json` written; α=0.625 preserved; n_inelastic=11–36 (failed ≥50 target); circuit breaker tripped on incremental cancellation** |
| **Automated guardrails (`scripts/guardrails.py`)** | **COMPLETE — 2026-06-08; 10 automated physical-law checks; 9/9 unit tests pass; imports Hung et al. (2021) priors + TUKU borehole materials; mandatory import for all IHM-F scripts** |
| **Cumulative diagnostics (`scripts/10_ihmf/diagnose_cumulative_tuku.py`)** | **COMPLETE — 2026-06-08; writes per-layer cumulative timeseries CSVs + PNGs to `results/ihmf/v3/diagnostics/`; 6-layer aggregate summary** |
| **Physics safeguards reference (`discussions/PHYSICS_SAFEGUARDS.md`)** | **COMPLETE — 2026-06-08; 23 KB; 11 rules with full source citations; covers sign conventions, h_c window, tau bounds, ratio gates, V(t) monotonicity** |
| **NotebookLM inventory (`docs/notebooklm_inventory.md`)** | **COMPLETE — 2026-06-08; 21 notebooks catalogued in 4 tiers; CLI command reference; project-stage mapping** |
| TUKU pilot — IHM-F v3 cumulative fork | **BLOCKED — tactical pivot decision pending** |
| IHM-F batch run — all 191 entries | **Blocked — incremental solver cannot proceed; cumulative-solver fork or data-driven fallback required** |

---

## 4. Blocking Decision

> **Blocking question (2026-06-09 correction):** The blocking question is no longer "do parameters satisfy physical gates?" It is: "Does the cumulative solver produce accurate gap-fills on held-out MLCW epochs under the one-week constraint?"

**🚨 CIRCUIT BREAKER (2026-06-08):** IHM-F v3 incremental solver failed at TUKU. Day 3 re-run complete — `results/ihmf/v3/TUKU_gps_v3_results.json` written. α = 0.625 preserved. But the incremental formulation cannot reproduce MLCW compaction.

**Incremental solver failure — quantified (2026-06-08):**

| Layer | n_inelastic | $R^2_{\text{MLCW,cum}}$ | obs_range (mm) | pred_range (mm) | Ratio obs/pred |
|-------|-----------|-------------------------|----------------|-----------------|----------------|
| F1 | 36 | −2.18 | 30.4 | ~3 | ~10× |
| T1 | 36 | −2.62 | 18.5 | ~2 | ~9× |
| F2 | 2 | NaN | 206.0 | ~1 | ~200× |
| T2 | 12 | NaN | 22.8 | ~2 | ~11× |
| F3 | 29 | NaN | 337.4 | ~2 | ~170× |
| F4 | 11 | −3.94 | 36.5 | ~2 | ~18× |

**Root cause of cancellation:** 5-day head oscillations (±2 m/yr at F2) approximately cancel over annual cycles. The model predicts net ~0.1–0.9 mm/yr per layer. MLCW records monotonic 8–15 mm/yr regardless of head direction. The incremental formulation's first-difference operation erases the preconsolidation stress memory — the Riley (1969) running minimum cannot be reconstructed from derivatives alone.

**GWL data gap (binding constraint):** F2 well (09050321) and F3 well (09050331) were installed August 2012. The 2003–2012 inelastic consolidation era has zero GWL data. The Day 2 GPS mask fix could not help — the bottleneck was GWL data, not GPS.

**Contrast with Script 12 cumulative success:**

| Metric | Incremental (IHM-F v3) | Cumulative (Script 12) |
|--------|----------------------|----------------------|
| Domain | $\Delta H$, $\Delta b$ (5-day diffs) | $H$, $b$ (cumulative levels) |
| Stress memory | None (each epoch independent) | Running minimum via $V(t)$ |
| $R^2$ F2 | NaN | 0.845 |
| F1 specific ratio | N/A | 9.1× PASS |
| T2 specific ratio | N/A | 9.3× PASS |
| F4 specific ratio | N/A | 17.3× PASS |

**Full post-mortem:** `discussions/POST_MORTEM_INCREMENTAL_CANCELLATION.md`

**Next action:** Tactical pivot decision required. Three options tabled:
- **A — Cumulative-solver fork:** Replace `joint_solve_fixed_tau`'s per-epoch lsq_linear with Script 12's two-regressor NNLS on cumulative $H$ and $V$ arrays.
- **B — Per-layer calibration:** Use Script 12 results as the calibration basis; empirical α for surface scaling; skip incremental walk-forward.
- **C — Data-driven fallback:** Use validated Script 12 $S_{ske}$, $S_{skv}$ where gates pass; flag failures; gap-fill via spatial interpolation of validated parameters.

**Previous gate (2026-06-04):** TUKU walk-forward evaluation is complete but does NOT clear the interpolation gate. Two diagnosed failures must be addressed:
1. **F2 Tier 2 (seasonal) degrades all 4 folds** — median RMSE 4.59 → 5.97 mm; seasonal correction is counterproductive; the `_build_seasonal_term` phase-shift logic likely misaligns with cumulative MLCW signal
2. **F3 RMSE unstable across folds** — 4.7 mm (2022) → 23.4 mm (2024); the InSAR–MLCW ratio `fbar` for F3 is drifting over time; fbar is not stationary for deep layers

**Next actions before spatial interpolation:**
- Diagnose F2 Tier 2 degradation: compare phase-shifted seasonal term to observed MLCW seasonal; check if `r1` scaling is correct
- Diagnose F3 instability: plot `fbar_per_fold` across folds for F3 at TUKU and multiple stations to confirm ratio drift
- If F3 fbar drift confirmed: add rolling-window fbar update (triggered by rolling-window std > threshold — data criterion, not hardcoded station names)

**Two parallel work streams:**
- **Walk-forward validation (static scaling baseline):** Complete at 37 stations. Spatial extension (`--krige ordinary`) requires gate clearance.
- **GWL-driven IHM-F:** Fix 3 pending code issues in `fit_ihm_f_v3.py` + `ihmf_model_v3.py`, then TUKU v3 pilot.

**Key methodological decisions locked (2026-06-01, from walkforward Tier 1 fix):**
- **Static f̄_k confirmed inadequate for InSAR-only prediction** — single-coefficient model cannot capture sub-annual MLCW dynamics; confirmed by prediction_v1 results (F2 skill_vs_trend = −0.53)
- **Detrended + lag-aware model added in `walkforward.py`** — 4-param detrend (intercept + linear + annual harmonic) via `ihmf_detrend.detrend_signal()`; $\tau$ grid search over 0–73 epochs; $\alpha$$\times$ InSAR_det(t−$\tau$) added to trend component
- **$\alpha$ $\ge$ 0 constraint enforced** — InSAR and MLCW must be positively correlated after detrending; negative $\alpha$ → fall back to trend-only
- **F1 and T2: InSAR residual predictive** — RMSE reductions of 37–60% at TUKU across folds
- **F2, F3, F4: InSAR residual anti-correlated** — these layers require GWL data for sub-annual prediction
- **InSAR-only ceiling at main aquifers confirmed** — GWL data is structurally necessary for F2/F3/F4

**Key methodological decisions locked (2026-05-31, from seasonal harmonic pilot):**
- **Linear detrend only** — MA (365d/730d) returns NaN on 10-year record; never use MA for detrending
- **MLCW baseline anchoring mandatory** — anchor both MLCW and InSAR to first common valid epoch
- **Trend reconstruction R^2 > 0.82** across all layers at 3 stations
- **Seasonal reconstruction (F2): R^2_seasonal = 0.43–0.67**; T1 partial at YUANCHANG
- **F3/F4 seasonal: not recoverable** — phase std > 59d at all 3 stations
- **Seasonal amplitude NOT year-predictable** — deliverable is phase characterisation map only
- **InSAR seasonal peak: DOY 154–172 (early June)** — inelastic consolidation accumulates through May–June before monsoon rebound
- **Semi-annual component below noise** — drop from annual harmonic model

**Key methodological decisions locked (2026-05-30, from tau search campaign):**
- Detrending [intercept + linear + annual harmonic] is mandatory before $\tau$ search
- Constrained CCF (OLS slope $\ge$ 0) preferred over MSE grid search for $\tau$ estimation
- 5$\times$ MAD outlier filter on incremental MLCW data
- 2S-TOOL Ss values 10–300$\times$ too large at 5-day resolution — diagnostic reference only
- F2 is the only TUKU layer with genuine multiscale GWL-MLCW coupling (detrended r=+0.69 at $\tau$=350d)
- F1, F3, F4 are trend-dominated at 5-day resolution (detrended r < 0.07)
- Seasonal $S_{ske}$ binary split: FAIL (0/6 layers); sinusoidal encoding: PARTIAL PASS (3/6 layers)

**Key architecture decisions locked (2026-05-29):**
- GWL is the only per-layer driver — InSAR is the total target in Step 2 only
- No `b_k · x` term anywhere
- $\tau$ is always a non-negative integer (5-day epoch units); $\tau$_max = 120 (raised 2026-06-04)
- Joint constrained least squares for [$S_1$…$S_N$, $\beta$=1/$\alpha$] simultaneously, for each fixed $\tau$ combination
- 2S-TOOL values are diagnostic reference only — not used as fixed priors
- Solver: `scipy.optimize.lsq_linear` (fafalab env)

---

## 5. Key Files

> **Path note:** Windows paths shown. Ubuntu VM: replace `D:\1000_SCRIPTS` → `/mnt/hgfs/1000_SCRIPTS`. Use forward slashes on Linux.
> **Abbreviation:** `...\InSAR_MLCW_v2` = `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2`

| File / Folder | Purpose | Path |
|------|---------|------|
| GWL assignment (v4) | Layer-to-GWL join key (195 rows) — use v4 only | `...\InSAR_MLCW_v2\data\gwl\gwl_to_mlcw_layer_assignment_v4.csv` |
| MLCW input | Primary layer-grouped MLCW (37 stations) | `...\InSAR_MLCW_v2\data\mlcw\group_byLayer_reconstr\{STATION}_reconst_grouped.csv` |
| MLCW cleaned (TUKU) | F3 spike-cleaned version | `...\InSAR_MLCW_v2\tau_demo_TUKU\data\TUKU_reconst_grouped_cleaned.csv` |
| GWL timeseries | 189 MLCW-timeline-aligned feather files | `...\InSAR_MLCW_v2\data\gwl\mlcw_gwl_timeseries\` |
| IHM-F config | 191 entries: station, layer, $\tau$_max, GWL feather path | `...\InSAR_MLCW_v2\data\ihmf_config.json` |
| IHM-F fit (v3, active) | Main inversion script | `...\InSAR_MLCW_v2\scripts\10_ihmf\fit_ihm_f_v3.py` |
| Tau search results | TUKU optimal lag + reconstruction metrics (Bug F fixed) | `...\InSAR_MLCW_v2\tau_demo_TUKU\results\tau_results.csv` |
| Stress-strain results | Per-layer NNLS fit: $S_{ke}$, $S_{kv}$, ratio, R² (Script 12, 2026-06-06) | `...\InSAR_MLCW_v2\tau_demo_TUKU\results\stress_strain_per_layer.json` |
| Seasonal $S_{ske}$ diag. | Wet/dry and sinusoidal results for TUKU 6 layers | `...\InSAR_MLCW_v2\tau_demo_TUKU\results\seasonal_ske_diagnostics.csv` |
| Walk-forward RMSE | 387 rows: station × layer × fold RMSE + skill scores (OBSOLETE — static f̄_k, superseded) | `...\InSAR_MLCW_v2\results\prediction_v1_OBSOLETE_static_fbar\walkforward_rmse.csv` |
| TUKU evaluation JSON | Per-fold metrics (OBSOLETE — static f̄_k, superseded) | `...\InSAR_MLCW_v2\results\prediction_v1_OBSOLETE_static_fbar\TUKU_evaluation.json` |
| Data inventory | Authoritative data file catalog (REQUIRED READING) | `...\InSAR_MLCW_v2\notes\dataset\my_dataset_summary.md` |
| Work diary | Full project narrative and method history | `...\InSAR_MLCW_v2\discussions\discussion_memory.md` |
| IHM-F theory | Complete two-regime model derivation | `...\InSAR_MLCW_v2\discussions\discussion_20260528_ihm_theory.md` |
| Model resolution | Universal model decision (IHM-F v3 architecture locked) | `...\InSAR_MLCW_v2\discussions\2026-05-29-ihmf-universal-model-resolution.md` |
| ML brainstorm | ML/DL candidates + literature survey | `...\InSAR_MLCW_v2\discussions\discussion_20260530_ml_brainstorm.md` |
| ML teaching guide | Plain-language ML method decision table | `...\InSAR_MLCW_v2\discussions\discussion_20260530_ml_brainstorm_v2_teaching.md` |
| Seasonal $S_{ske}$ doc | Seasonal coefficient methodology and locked findings | `...\InSAR_MLCW_v2\discussions\discussion_20260530_seasonal_ske.md` |
| Runtime resolver | Cross-platform path detection module | `...\InSAR_MLCW_v2\paths.py` |
| Seasonal harmonic scripts | Two-script InSAR→MLCW seasonal analysis | `...\InSAR_MLCW_v2\scripts\13_seasonal_insar\` |
| Walk-forward pipeline | 8-module prediction package (leakage-free, 4-fold) | `...\InSAR_MLCW_v2\scripts\15_prediction\` |
| Tau search methodology | Full tau search lessons + $h_{c}$ definition | `...\InSAR_MLCW_v2\docs\tau_search_methodology.md` |
| Seasonal harmonic findings | Reconstruction tables, phase gate, locked decisions | `...\InSAR_MLCW_v2\docs\seasonal_harmonic_findings.md` |
| Figure standards | A4/300dpi matplotlib standards | `...\InSAR_MLCW_v2\docs\figure_standards.md` |
| Incremental fit results (TUKU) | lsq_linear per-layer fit (6 layers) — all fail 8–100× ratio gate | `...\InSAR_MLCW_v2\tau_demo_TUKU\results\incremental_fit_results.json` |

### Results directory convention (2026-06-08)

Obsolete results are renamed with `_OBSOLETE_<reason>` suffixes rather than deleted, preserving the full experimental history for the final defense. Active outputs live alongside them without the suffix.

| Status | Suffix pattern | Example |
|--------|---------------|---------|
| **ACTIVE** | No suffix | `results/ihmf/v3/TUKU_gps_v3_results.json` |
| OBSOLETE — incremental solver | `_OBSOLETE_v*_incremental*` | `results/ihmf/run001_OBSOLETE_v1_incremental_single_layer/` |
| OBSOLETE — static scaling | `_OBSOLETE_static_*` | `results/direct_ratio_OBSOLETE_static_scaling_baseline/` |
| OBSOLETE — InSAR-only prediction | `_OBSOLETE_*` | `results/prediction_v1_OBSOLETE_static_fbar/` |
| OBSOLETE — abandoned methods | `_OBSOLETE_*` | `results/prophet_OBSOLETE_ablation/` |

Active results directories: `ihmf/v3/`, `ring_cross_correlation/`, `seasonal_insar_harmonic/`, `ring_gwl_xcorr/`, `data_analysis/`, `gps_vs_mlcw/`, `stress_strain/`.

### Gap-fill evaluation criteria (corrected 2026-06-09)

| Criterion | Threshold | Status |
|-----------|-----------|--------|
| Gap-fill RMSE vs. held-out MLCW | < RMSE of static linear interpolation | Not yet tested |
| Walk-forward skill score | > 0 on all 3 pilot layers (F1, T2, F4) | Not yet tested |
| Self-recalibration | `--recalib_date` arg added to fit script | Not yet built |
| Physical guardrails | All 10 guardrails pass | Partial (F1/T2/F4 pass ratio gate) |
