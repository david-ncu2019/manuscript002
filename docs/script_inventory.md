# Script Inventory & Pipeline Organization

> Last updated: 2026-06-03
> Project: InSAR-MLCW subsidence analysis — GWL-driven methods under exploration.
> Repo root: `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2`.
> Run commands: `docs/run_commands.md`. Data paths: `docs/data_paths.md`.

## Pipeline Stages

| Stage | Directory | Status | Purpose |
|-------|-----------|--------|---------|
| 01 | `scripts/01_insar_preprocessing/` | Complete | Adaptive OMT, LOS decomposition, IDW/kriging interpolation |
| 02 | `scripts/02_mlcw_processing/` | Complete | MLCW ring decomposition, 5 m layer reconstruction |
| 03 | `scripts/03_gps_processing/` | Complete | GPS vertical decomposition |
| 04 | `scripts/04_gwl_processing/` | Complete | GWL extraction, layer assignment (v3) |
| 05 | `scripts/05_modeling/` | Retired | ARX, Prophet, ablation (superseded by IHM-F) |
| 06 | `scripts/06_direct_ratio/` | Complete | Static f̄_k baseline (comparison floor) |
| 07 | `scripts/07_analysis/` | Legacy | Cross-validation, diagnostics |
| 08 | `scripts/08_visualization/` | Active | Publication plots + data inspection |
| 09 | `scripts/09_trackB/` | Complete | 2S-TOOL batch run + result collection |
| 10 | `scripts/10_ihmf/` | **Active** | IHM-F model (GWL-driven method) |
| 11 | `scripts/11_data_analysis/` | Active | 8 diagnostics + ring cross-correlation |
| 12 | `scripts/12_stress_strain/` | Active | Preconsolidation head estimation |
| 13 | `scripts/13_seasonal_insar/` | Active | InSAR→MLCW seasonal harmonic characterisation |
| 14 | `scripts/14_lagged_ratio/` | Scratch | Contains only `inspect_data.py` / `inspect_data2.py` — no full analysis yet |
| 15 | `scripts/15_prediction/` | Active | Ceiling test, walk-forward validation |
| 16 | `scripts/16_ring_gwl_xcorr/` | Active | Ring-to-GWL cross-correlation |

---

## Active Scripts Detail

### `scripts/10_ihmf/` — IHM-F Fitting (GWL-Driven Method)

| Script | Role |
|--------|------|
| `fit_ihm_f.py` | Orchestrator for IHM-F v1 (two-regime Path A/B, TAU_MAX from config) |
| `ihmf_model.py` | Core v1 model: `prepare_signals`, `fit_one_tau`, `grid_search_tau`, `walk_forward` |
| `fit_ihm_f_v2.py` | Orchestrator for IHM-F v2 (single unified regime, detrended, TAU_MAX=24) |
| `ihmf_model_v2.py` | Core v2 model |
| `fit_ihm_f_v3.py` | Orchestrator for IHM-F v3 (joint constrained inversion across all layers, TAU_MAX=73) |
| `ihmf_model_v3.py` | Core v3 model: `remove_seasonal_cycle`, `tau_grid_search_per_layer`, `joint_solve_fixed_tau`, `run_walk_forward_v3` |
| `ihmf_io_multilayer.py` | Multi-layer loader for v3: loads all layers for one station aligned to InSAR epoch timeline |
| `ihmf_io.py` | Data loader: MLCW + GWL + InSAR alignment. **Known issue:** `merge_asof` at lines 53–58 has no tolerance parameter (stale endpoint injection risk). |
| `ihmf_plots.py` | Figures: 3-panel raw-fit + reconstruction |
| `ihmf_detrend.py` | Detrending: removes [intercept, linear, sin, cos] components. **v1/v2 only.** |
| `diagnose_seasonal_ske.py` | Wet/dry + sinusoidal $S_{ske}$ modulation tests (TUKU only) |
| `compute_tuku_metrics.py` | MAE/RMSE for TUKU v2 model predictions |
| `batch_v2.py` | Batch runner for all 191 config entries using v2 (no v3 batch runner exists yet) |

**Architecture note (v1/v2/v3):** `ihmf_detrend.py` is v1/v2 only and was never wired into `fit_ihm_f.py` (v1). IHM-F v2 imports it directly. IHM-F v3 replaces 4-parameter harmonic detrending entirely with built-in seasonal-cycle removal (`remove_seasonal_cycle` in `ihmf_model_v3.py`) — monthly climatology subtraction before $\tau$ grid search. The detrend module is irrelevant for v3.

---

### `scripts/11_data_analysis/` — Diagnostics

| Script | Role |
|--------|------|
| `analyze_alpha.py` | Compressible thickness fraction per station |
| `analyze_collinearity.py` | VIF diagnostics for GWL/InSAR collinearity |
| `analyze_correlations.py` | MLCW–GWL correlation by frequency band |
| `analyze_lagged_correlation.py` | CCF-based $\tau$ per station-layer (lags 0–24) |
| `analyze_layer_patterns.py` | Layer-wise pattern analysis |
| `analyze_proxy_quality.py` | Assess whether well proximity and screen-depth match predict IHM-F model success (reads $\tau$_opt from IHM-F JSONs) |
| `analyze_regimes.py` | Elastic/inelastic regime analysis |
| `analyze_signal_decomposition.py` | Signal decomposition diagnostics |
| `ring_cross_correlation.py` | Cross-correlation matrix, 3 sources $\times$ 39 stations (uses `isce_ncu3`) |
| `summarize_for_redesign.py` | Aggregates 8 diagnostics → `DATA_ANALYSIS_REPORT.md` |

---

### `scripts/13_seasonal_insar/` — Seasonal Harmonic

| Script | Role |
|--------|------|
| `01_seasonal_harmonic_analysis.py` | 4-step pilot (Step0–Step4): fit, detrend, phase gate, holdout |
| `02_reconstruction_visualization.py` | 3 figures per station; contains `compute_fbar_anchored()` |

**Phase gate (3 conditions, all must pass):**
1. `std_dphi1 < 45 days`
2. `mean_A1 > 0.5 mm`
3. `corr_A1k_A1x > 0.0`

**Known issue:** `seasonal_applied=True` is set even when $\Delta$ R^2 $\le$ 0 (e.g. XIUTAN F1/T1). Guard not implemented.

---

### `scripts/15_prediction/` — Ceiling Test

| Script | Role |
|--------|------|
| `ceiling_test.py` | Walk-forward ceiling test: `MLCW_k(t) = a_k·InSAR_trend + b_k·InSAR_det(t−τ_k)` |

**4 folds:** train-test splits at 2022, 2023, 2024, 2025.  
**Evaluation rule:** term-2 validated only if skill > 0 in $\ge$ 2 of 4 holdout years.

---

### `scripts/12_stress_strain/` — Preconsolidation

| Script | Role |
|--------|------|
| `prepare_stress_strain.py` | Build stress-strain curves per station/layer |
| `plot_stress_strain.py` | Publication-quality stress-strain figures |
| `HAND_CALCULATION_GUIDE.md` | Manual validation of preconsolidation head estimates |

---

## tau_demo_TUKU Pilot

Located at `tau_demo_TUKU/`. Execute in strict order:

```
01_run_tau_search.py
02_plot_timeseries.py
03_reconstruct_and_evaluate.py
04_plot_input_data.py
05_detrended_reconstruction.py
06_physical_ss.py
07_joint_search.py
plot_style.py
```

Results in `tau_demo_TUKU/results/` (`tau_results.csv`, `reconstruction_metrics.csv`, etc.).  
Methodology: `docs/tau_search_methodology.md`.

---

## Legacy & External

| Location | Status | Note |
|----------|--------|------|
| `scripts/05_pairing/` | Legacy | One-off pairing scripts, preserved for reference |
| `scripts/12_validation/` | Legacy | One-off validation, preserved for reference |
| `tools/2S-TOOL-Python/` | External | Independent repo (`github.com/david-ncu2019/twostoolspy`) |
| `gis/` | Static | Shapefiles, ArcGIS project docs |
| `scripts/notebooks/` | Reference | Jupyter data prep + plotting |
| `mlcw_inspector/` | Tool | Interactive Panel/HoloViews dashboard for MLCW data exploration (`python -m mlcw_inspector`) |
