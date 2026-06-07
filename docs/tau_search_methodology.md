# Tau Search Methodology (2026-06-03)

Findings from the TUKU tau (hydraulic lag) demonstration, implemented in `tau_demo_TUKU/` scripts 01–07.

## Seasonal cycle removal (v3, not the old detrend module)

- Without seasonal removal, MSE grid search latches onto annual cycle ($\tau$ $\approx$ 365 days) — not a true hydraulic lag
- IHM-F v3 uses `remove_seasonal_cycle()` (monthly climatology subtraction) during $\tau$ grid search — this replaces the 4-parameter harmonic detrend in `scripts/10_ihmf/ihmf_detrend.py`, which is v1/v2 only
- After seasonal removal, $\tau$ values drop from 300–350 days to 15–160 days for most layers
- F2 alone retains $\tau$ $\approx$ 350 days even after seasonal removal — likely residual annual structure not captured by simple monthly means

## Outlier filtering

- 5 $\times$ MAD threshold on incremental MLCW (inc_db) catches physically impossible spikes
- F2: +2.16 mm/ep at 2021-07-01 (10 $\times$ MAD)
- F3: +4.70 mm/ep at 2021-12-01 (45 $\times$ MAD) — clearly an artifact
- Removing F3 outlier improves RMSE by 39%
- Script: `tau_demo_TUKU/05_detrended_reconstruction.py`

## Cross-correlation vs MSE for tau

- MSE grid search on non-detrended signals unreliable — annual cycle autocorrelation creates false minima
- Constrained CCF (requiring OLS slope $\ge$ 0 for physical validity) gives more robust $\tau$ estimates
- Script: `tau_demo_TUKU/07_joint_search.py` (cross-correlation tau + joint $S_{ske}$/$S_{skv}$/b search)
- Only ~30 of 74 candidate taus pass physical-sign filter (OLS slope $\ge$ 0)

## Physical $S_{ske}$/$S_{skv}$ constraints

- Reference values from 2S-TOOL are for TOTAL (multi-year) signals — over-predict by 10–300 $\times$ at 5-day resolution
- Joint 4-parameter search ($\tau$, $S_{ske}$, $S_{skv}$, b) finds $S_{ske}$ often at upper bound of reference range
- Compressible thickness b found to be 0.4–16% of classified span_m — only thin active zones compact at 5-day timescale
- Script: `tau_demo_TUKU/06_physical_ss.py` (fixed Ss, fails catastrophically)
- Script: `tau_demo_TUKU/07_joint_search.py` (joint search, Ss within physical bounds)
- Script: `scripts/10_ihmf/diagnose_seasonal_ske.py` — tests whether splitting $S_{ske}$ into wet (Apr–Sep) and dry (Oct–Mar) periods improves TUKU predictions. Reference 2S-TOOL tables show $S_{ske}$ varying 2–10 $\times$ between seasons at the same station-layer. Decision gate: PASS if >5% RMSE reduction for $\ge$ 3 of 6 layers.

## GWL–MLCW coupling by frequency band

From `scripts/11_data_analysis/analyze_correlations.py` results:
- F2: ONLY layer with genuine multiscale coupling (detrended r=+0.69)
- F1, F3, F4: trend-dominated (detrended r<0.07) — raw correlation from shared secular trend, not hydraulic coupling
- Source: `figures/prestage_data_analysis/correlation_matrix.csv`

## Preconsolidation head ($h_{c}$) — literature-supported definition

- **$h_{c}$ = historical minimum groundwater level** (前期最低地下水位) — not a fixed offset
- Source: 江崇榮, 林燕初, 陳建良 (2011), 地質 30(2):32–35 — Hefeng $h_{c}$ = 0 m MSL (pre-1975 lowest)
- The "15 m above current" rule has **no literature basis** — a Hefeng-specific coincidence (current=−15 m, $h_{c}$=0 m)
- 2S-TOOL Priority 4: `h_c = elev_leveling_m − min(head)` from long-term well timeseries
- IHM-F: uses 10th percentile of observed GWL — reasonable proxy for historical minimum
- Stress-strain breakpoint method (`scripts/12_stress_strain/`) gives the most precise per-layer $h_{c}$
- `hp_inicial_overrides.json`: use ONLY for manual corrections where automatic methods fail; never for fixed-offset rules

## IHM-F v3 context for tau_demo

The tau_demo scripts import from `scripts/10_ihmf/ihmf_model_v3`, which provides:

- **Joint constrained inversion** across all layers simultaneously (Step 1: per-layer S_ke_j, S_kv_j via `lsq_linear`; Step 2: global $\alpha$ from cumulative InSAR)
- **TAU_MAX = 73** (1 year at 5-day epochs) — wider search window than v2's TAU_MAX = 24
- **Seasonal aliasing fix**: `remove_seasonal_cycle()` subtracts monthly climatology from incremental signals before $\tau$ grid search. Without this, annual GWL autocorrelation (r $\approx$ 0.8 at $\tau$ = 24, 48) creates false MSE minima.
- **Two-regime mask** restored: elastic (head > $h_{c}$) and inelastic (head $\le$ $h_{c}$) per layer
- **Alpha bounds**: $\alpha$ $\in$ (0, 1] — physically requires surface compaction $\le$ sum of layer compactions
- **Diagnostic flags**: $\alpha$ outside bounds, $S_{kv}$ = 0, $\tau$_opt at search boundary

## Script inventory (tau_demo_TUKU/, execute in order)

| Script | Purpose |
|--------|---------|
| `01_run_tau_search.py` | MSE grid search for optimal $\tau$ per layer (no seasonal removal; shows aliasing) |
| `02_plot_timeseries.py` | 3-panel timeseries figures per layer + MSE-vs-$\tau$ curves |
| `03_reconstruct_and_evaluate.py` | Reconstruct MLCW from MSE-optimal $\tau$ (baseline, no seasonal removal) |
| `04_plot_input_data.py` | 4-panel diagnostic of all input data: GWL, MLCW, InSAR, incremental signals |
| `05_detrended_reconstruction.py` | Detrended variant + 5 $\times$ MAD outlier filter (key improvement) |
| `06_physical_ss.py` | Fixed 2S-TOOL Ss — demonstrates failure at 5-day scale |
| `07_joint_search.py` | Joint 4-parameter search ($\tau$, $S_{ske}$, $S_{skv}$, b) via constrained CCF |
| `plot_style.py` | Shared matplotlib style constants for all 7 scripts |
