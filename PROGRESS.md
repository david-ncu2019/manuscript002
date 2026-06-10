# PROGRESS.md — InSAR–MLCW Subsidence Analysis

> **This is the single authoritative PROGRESS.md** (merged 2026-06-05; content from docs repo 2026-06-04).
> All future updates go here only.

**Date:** 2026-06-10
**Status:** ✅ GWL RESIDUAL TERM EVALUATED — T1 is the only layer where adding GWL to the carrier model improves held-out RMSE (>5% gate). Script `14b_carrier_gwl_eval.py` created. `14_carrier_reconstruction_tuku.py` updated with `--use-gwl` flag. F1 is marginal (−4.2%, just below threshold). Deep layers (F2/F3/F4) reject GWL — trend dominates; adding GWL noise degrades prediction.

**Completed today (2026-06-10):**
- Phase 1.1 Task 1.1.1 Step A: Per-layer carrier fit (a_k >= 0, sum=0.624)
- Phase 1.1 Task 1.1.1 Step B: 6 per-layer reconstruction CSVs (1572 epochs each)
- Phase 1.1 Task 1.1.1 Step C: Optional refinements — DEFERRED (carrier R² already 0.80–0.99)
- Phase 1.1 Task 1.1.1 Step D: 6-panel reconstruction figure (300 dpi)
- Phase 1.1 Task 1.1.2: Calibration quality quantified (R², RMSE, bias, gap coverage)

**Next:** Part 1 Phase 1.2 — Forward prediction with carrier (`--predict_to DATE`).

**Previous (2026-06-08):** 🚨 CIRCUIT BREAKER — IHM-F v3 incremental solver structurally failed at TUKU. Script 12 cumulative approach SUCCEEDED. The incremental solver's first-difference operation erases the Riley (1969) preconsolidation memory. See `discussions/POST_MORTEM_INCREMENTAL_CANCELLATION.md` for full post-mortem.

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

**Current phase:** Part 0 complete — Phase 0.1 bake-off confirmed GPS carrier as primary gap-fill method. Part 1 (TUKU carrier reconstruction) is the next blocking milestone.

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
| **12_stress_strain_per_layer.py (cumulative domain, per-layer)** | **Complete — 2026-06-06; two-regressor NNLS. Two-step specific-storage gate (live 2026-06-09): F1 S_ske=6.54e-6 FAIL (below lit. floor 7.27e-6; specific ratio=30.36 inside [3,50]); T1 S_ke=0 not identifiable; F2 specific ratio=220.68 FAIL (thickness artifact: 106.3m/12.09m clay=8.79×; bulk ratio=25.10 inside [3,50]); T2 ratio=8.42 PASS; F3 S_ke=0 not identifiable; F4 ratio=10.76 PASS. ⚠ These numbers will change after R1/R2 head zero-referencing fix.** |
| **CLAUDE.md restructure + knowledge file merge** | **Complete — 2026-06-05; both CLAUDE.md files restructured; 12 discussion/notes/plans files merged from docs repo** |
| Multi-layer data assembler (`ihmf_io_multilayer.py`) | **Complete — operational, imported by `fit_ihm_f_v3.py`** |
| Joint solver (`ihmf_model_v3.py`) | **CIRCUIT BREAKER (2026-06-08) — incremental formulation structurally fails; $R^2_{\text{MLCW,cum}}$ negative/NaN for all 6 TUKU layers; 8–355× prediction gap** |
| **Day 2 α fix (2026-06-08): 4 code changes + compute_alpha_empirical.py** | **COMPLETE — commit 182b8d6; GPS mask decoupled, alpha_external param, --alpha CLI, TUKU α=0.625 verified** |
| **Day 3 TUKU GPS re-run (2026-06-08)** | **COMPLETE — `TUKU_gps_v3_results.json` written; α=0.625 preserved; n_inelastic=11–36 (failed ≥50 target); circuit breaker tripped on incremental cancellation** |
| **Automated guardrails (`scripts/guardrails.py`)** | **COMPLETE — 2026-06-08; 10 automated physical-law checks; 9/9 unit tests pass; imports Hung et al. (2021) priors + TUKU borehole materials; mandatory import for all IHM-F scripts** |
| **Cumulative diagnostics (`scripts/10_ihmf/diagnose_cumulative_tuku.py`)** | **COMPLETE — 2026-06-08; writes per-layer cumulative timeseries CSVs + PNGs to `results/ihmf/v3/diagnostics/`; 6-layer aggregate summary** |
| **Physics safeguards reference (`discussions/PHYSICS_SAFEGUARDS.md`)** | **COMPLETE — 2026-06-08; 23 KB; 11 rules with full source citations; covers sign conventions, h_c window, tau bounds, ratio gates, V(t) monotonicity** |
| **NotebookLM inventory (`docs/notebooklm_inventory.md`)** | **COMPLETE — 2026-06-08; 21 notebooks catalogued in 4 tiers; CLI command reference; project-stage mapping** |
| TUKU pilot — IHM-F v3 cumulative fork | **COMPLETE — cumulative solver with intercept verified (2026-06-09); all 6 layers S_ke ≥ 0, R²_cum > 0** |
| IHM-F batch run — all 191 entries | **Blocked — pending Part 1 TUKU pilot completion before multi-well extension** |
| **Standalone bilinear fitter (`tau_demo_TUKU/bilinear_fit.py`)** | **COMPLETE — 2026-06-09; fit_bilinear() extracts center-then-NNLS pattern from production solver** |
| **Pooled r2_mlcw_cum removal (Step D)** | **COMPLETE — 2026-06-09; per-layer R² only in output JSON** |
| **Phase 0.1 three-method bake-off** | **COMPLETE — 2026-06-09; Decision Point 1 = CARRIER-PRIMARY; results in `tau_demo_TUKU/results/holdout_bakeoff.json`** |
| **Part 1 carrier reconstruction (`14_carrier_reconstruction_tuku.py`)** | **COMPLETE — 2026-06-10; all 6 layers fitted, CSVs + figure + JSON; sum(a_k)=0.624; --use-gwl flag added** |
| **GWL residual term eval (`14b_carrier_gwl_eval.py`)** | **COMPLETE — 2026-06-10; T1 ADOPTS GWL (−14.3% held-out RMSE); F1 marginal (−4.2%); F2/T2/F3/F4 reject; results in `carrier_gwl_eval.json`** |
| **Part 1 Phase 1.2 — Forward prediction** | **COMPLETE — 2026-06-10; --predict_to flag added; 6-month tail holdout: T1/T2 skill>0, Decision Point 2=PARTIAL** |
| **Part 1 Phase 1.3 — Self-recalibration** | **COMPLETE — 2026-06-10; --recalib_date flag added; writes _recalib_YYYYMMDD suffix outputs** |
| **Part 1 Phase 1.4 — Bilinear characterization** | **COMPLETE — 2026-06-10; `15_storage_characterization.py` created; S_ske/S_skv for all 6 layers; TUKU_storage_params.json written** |
| **Part 2 — Multi-well extension** | **NEXT — batch carrier reconstruction + characterization at 37 stations** |

---

## 4. Decision Point 1 — Gap-Fill Method Selection (2026-06-09)

**✅ DECIDED: CARRIER-PRIMARY** — GPS/InSAR carrier wins all 6 TUKU layers by held-out RMSE.

### Three-Method Held-Out Bake-Off Results

| Layer | carrier_mid | bilinear_mid | baseline_mid | carrier_end | bilinear_end | baseline_end | Primary |
|-------|------------|-------------|-------------|------------|-------------|-------------|---------|
| F1 | 1.635 | 1.519 | 5.322 | 2.540 | 5.534 | 2.626 | carrier |
| T1 | 1.057 | 1.777 | 3.406 | 2.240 | 4.471 | 2.332 | carrier |
| F2 | 4.298 | 8.354 | 40.501 | 7.128 | 9.415 | 7.676 | carrier |
| T2 | 2.032 | 2.402 | 6.174 | 3.911 | 7.214 | 4.209 | carrier |
| F3 | 7.302 | 11.293 | 60.804 | 16.967 | 25.321 | 15.591 | carrier |
| F4 | 1.639 | 3.642 | 7.516 | 3.799 | 8.525 | 3.741 | carrier |

All values in mm RMSE on held-out epochs. Two holdout designs: **middle gap** (40–70% of record, simulates reduced sampling) and **end gap** (last 30%, simulates permanent shutdown). Methods: M1 = GPS carrier (`b = a·d_surface + c`), M2 = bilinear Terzaghi (`b = c + S_ke·u + delta·V`), M3 = baseline (linear interpolation for middle gap, trend extrapolation for end gap).

### Key Findings

1. **GPS carrier wins all 6 layers** — average RMSE across both designs is lowest for carrier on every layer. Verdict: CARRIER-PRIMARY.
2. **Bilinear is the worst gap-fill method** — confirmed on 6/6 layers. The GWL bilinear model is for parameter characterization (Phase 1.4), not gap-fill.
3. **Interpolation fails badly on deep layers** — F2 (40.5 mm) and F3 (60.8 mm) middle-gap interpolation RMSE is 6–80× the carrier. Deep aquifers have strong secular trends that interpolation cannot capture.
4. **Deep layers trend-extrapolate well** — F3 (15.6 mm) and F4 (3.7 mm) end-gap trend RMSE is competitive with carrier (16.97 mm, 3.80 mm). For smooth deep layers, trend extrapolation is a credible fallback.
5. **F2 carrier RMSE (4.3 mm middle, 7.1 mm end)** — the main aquifer couples well to GPS, but 4–7 mm RMSE on a 112 mm compaction range (~200 mm total) represents ∼3–4% error.

### Method Assignment (Part 1)

| Layer | Primary Method | Fallback | Notes |
|-------|---------------|----------|-------|
| F1 | carrier | bilinear | bilinear competitive on middle gap (1.52 vs 1.64 mm) |
| T1 | carrier | bilinear | shallow acquitard, carrier RMSE < 2.3 mm |
| F2 | carrier | — | main aquifer, carrier dominates (4.3 vs 8.4 vs 40.5 mm) |
| T2 | carrier | — | carrier RMSE < 4 mm both designs |
| F3 | carrier | trend extrapolation | deep aquifer, trend competitive on end gap |
| F4 | carrier | trend extrapolation | deep aquitard, trend competitive on end gap |

**Script:** `tau_demo_TUKU/13_holdout_method_bakeoff.py`
**Results:** `tau_demo_TUKU/results/holdout_bakeoff.json`

### Previous §4 content (superseded by Decision Point 1)

The incremental solver circuit breaker (2026-06-08) and pre-audit methodological decisions are preserved in the git history. The cumulative-solver fork (Option A from the post-mortem) was implemented via R1/R2/R3 repairs. The three-method bake-off replaces the pre-audit single-method gate.

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
| Bilinear fitter | Standalone Terzaghi/Riley per-layer fitter with intercept | `...\InSAR_MLCW_v2\tau_demo_TUKU\bilinear_fit.py` |
| Holdout bake-off script | Three-method held-out evaluator (Phase 0.1) | `...\InSAR_MLCW_v2\tau_demo_TUKU\13_holdout_method_bakeoff.py` |
| Holdout bake-off results | Per-layer, per-design, per-method RMSE + primary method | `...\InSAR_MLCW_v2\tau_demo_TUKU\results\holdout_bakeoff.json` |
| Holdout split definition | Per-layer middle/end gap index ranges | `...\InSAR_MLCW_v2\tau_demo_TUKU\data\holdout_split_definition.json` |

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
