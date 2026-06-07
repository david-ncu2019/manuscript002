# PROGRESS.md — InSAR–MLCW Subsidence Analysis

> **This is the single authoritative PROGRESS.md** (merged 2026-06-05; content from docs repo 2026-06-04).
> All future updates go here only.

**Date:** 2026-06-07
**Status:** Script 12 COMPLETE (2026-06-06). Collinearity root cause diagnosed (2026-06-07). **Key correction:** The [8–100]× gate applies to the **specific-storage ratio** $S_{skv}/S_{ske}$ [m⁻¹/m⁻¹], not the bulk ratio $S_{kv}/S_{ke}$ [mm/m / mm/m]. After two-thickness borehole conversion: F1 **passes** (9.1×), T2 **passes** (9.3×), F4 **passes** (17.3×). **Actual failures:** T1 specific ratio 2.9× (undershoots 8×); F2 specific ratio 221× (overshoots 100×); F3 $S_{ke}$=0 (undefined). Joint inversion over thickness is degenerate (RMSE flat along $S_{ske} \times$ total\_m ridge) — ruled out as dead end. **Next:** implement decoupled two-step fit in Script 12 (elastic-only OLS for $S_{ke}$, then residual NNLS for $S_{kv}$), then feasibility check vs Choushui literature bounds.

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
| Joint solver (`ihmf_model_v3.py`) | **EXISTS — 3 fixes confirmed done 2026-06-05: TAU_MAX=120, ratio guard <1e-10+8–58× WARN, Step 2 cumulative+intercept; default tau_max=120 in function signatures. S_kv upper cap removed (lumped parameters make direct cap ~4-5 orders too small).** |
| TUKU pilot — IHM-F v3 re-run | **READY TO RUN — all fixes confirmed; existing TUKU_v3_results.json (2026-06-02) is pre-fix and invalid** |
| IHM-F batch run — all 191 entries | **Blocked — TUKU v3 pilot re-run must pass physical checks first** |

---

## 4. Blocking Decision

**Current gate (2026-06-07, updated):** Script 12 complete. Collinearity root cause confirmed and specific-storage ratio gate recomputed from JSON (2026-06-07).

**Corrected gate status (specific-storage ratio $S_{skv}/S_{ske}$ [m⁻¹], not bulk ratio):**

| Layer | $S_{ske}$ (m⁻¹) | $S_{skv}$ (m⁻¹) | Specific ratio | Gate |
|-------|-----------------|-----------------|----------------|------|
| F1 | $2.12 \times 10^{-5}$ | $1.93 \times 10^{-4}$ | 9.1× | **PASS** |
| T1 | $9.55 \times 10^{-5}$ | $2.75 \times 10^{-4}$ | 2.9× | FAIL (< 8×) |
| F2 | $4.94 \times 10^{-6}$ | $1.09 \times 10^{-3}$ | 221× | FAIL (> 100×) |
| T2 | $5.50 \times 10^{-5}$ | $5.09 \times 10^{-4}$ | 9.3× | **PASS** |
| F3 | null | null | undefined | ($S_{ke}$=0) |
| F4 | $2.26 \times 10^{-5}$ | $3.92 \times 10^{-4}$ | 17.3× | **PASS** |

**Dead end ruled out (2026-06-07):** Joint inversion over (total\_m, aquitard\_m, $S_{ske}$, $S_{skv}$) is degenerate — RMSE depends only on the product $S_{ske} \times$ total\_m; optimizer finds a flat ridge with no unique solution. Thickness fixed at borehole values.

**Root cause of ratio compression:** At TUKU 93% of epochs are inelastic (continuous drawdown). Virgin term $V_j(t) \approx H_j(t) - h_c$ becomes a near-perfect linear shift of $H_j(t)$. Simultaneous NNLS cannot separate regressors and compresses the ratio. This is a physical identifiability limit.

**Decoupled two-step fit: IMPLEMENTED AND RUN (2026-06-06).** Results in `tau_demo_TUKU/results/stress_strain_per_layer.json` (`_2s` fields for all 6 layers). See `discussions/PEER_REVIEW_MATH_VERIFICATION.md` for full numerical table.

**Ratio gate bug confirmed (2026-06-07):** `12_stress_strain_per_layer.py` line 560 checks bulk ratio $S_{kv}/S_{ke}$ [mm/m] against $[8, 100]\times$. Correct gate requires specific storage ratio $S_{skv}/S_{ske}$ [m⁻¹]. The transformation factor = total\_m / compressible\_m (F2: 8.79×, T2: 1.58×). Consequence: F2 is a **false positive** (bulk 25.1× PASS, specific 220.7× → FAIL); T2 is a **false negative** (bulk 5.32× FAIL, specific 8.41× → PASS).

**Corrected TUKU decoupled feasibility (after ratio gate fix):**
- F1: FAIL ($S_{ske,2s} = 6.54 \times 10^{-6}$ m⁻¹, 10% below literature min $7.27 \times 10^{-6}$)
- T1: FAIL ($S_{ke,2s}$ = 0 — elastic channel not identifiable)
- F2: FAIL (specific ratio $220.7\times > 100\times$; only 6 elastic epochs; nnls_fallback)
- T2: **PASS** (specific ratio $8.41\times \in [8, 100]$; $S_{ske}$, $S_{skv}$ both IN bounds)
- F3: FAIL ($S_{ke,2s}$ = 0; only 7 elastic epochs; nnls_fallback)
- F4: **PASS** (specific ratio $10.76\times$; all bounds IN)

**Ratio gate FIXED (2026-06-07):** Applied `specific_ratio_2s = S_skv_2s_m1 / S_ske_2s_m1` at `12_stress_strain_per_layer.py` line 560. Script 12 re-run and confirmed: T2 `feasible_2s=true` (8.42×), F2 `feasible_2s=false` (220.68×), F4 unchanged (10.76×). Results match `PEER_REVIEW_MATH_VERIFICATION.md` predictions exactly.

**Next action (Day 2, 2026-06-08):** TUKU IHM-F v3 pilot — `$env:PYTHONPATH=""; conda run -n fafalab python scripts/10_ihmf/fit_ihm_f_v3.py --station TUKU --all`. Confirm R²_insar > 0, α ∈ (0, 1]. Then 4-fold walk-forward. See 7-day plan at `C:\Users\FAFALAB\.claude\plans\initialize-a-brand-new-composed-sloth.md`.

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
| Walk-forward RMSE | 387 rows: station × layer × fold RMSE + skill scores | `...\InSAR_MLCW_v2\results\prediction_v1\walkforward_rmse.csv` |
| TUKU evaluation JSON | Machine-readable metrics: per-fold + medians + gate | `...\InSAR_MLCW_v2\results\prediction_v1\TUKU_evaluation.json` |
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
