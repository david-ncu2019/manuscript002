# Discussion: Prediction Pipeline Design — `scripts/15_prediction/`
**Date:** 2026-06-01
**Status:** Design approved — ready for implementation

---

## 1. Purpose

This document specifies the architecture of the new `scripts/15_prediction/` pipeline.
It covers walk-forward temporal validation (Tier 1 + Tier 2) and zone-stratified spatial
kriging to the 8,577 unmonitored grid points. This is the primary one-week deliverable.

**Scope boundary:** This pipeline reads outputs from existing, working scripts. It does
not reprocess raw data, does not touch `scripts/13_seasonal_insar/`,
`scripts/11_data_analysis/`, or `src/`. Zero modification to past codebase.

---

## 2. Scientific Context

### What we are predicting

At each of 37 MLCW stations, the per-layer compaction timeseries is predicted from
InSAR surface displacement using the direct-ratio model:

```
Ŷ_k(t) = f̄_k × x(t)                        [Tier 1 — trend only]
Ŷ_k(t) = f̄_k × x(t) + r̄₁_k × A₁_x(t)     [Tier 2 — F2 seasonal added where available]
```

where:
- `f̄_k` = median compaction fraction at layer k (from `direct_ratio_stats.csv`)
- `x(t)` = InSAR cumulative displacement at epoch t (from feather file)
- `r̄₁_k` = mean annual amplitude ratio for F2 (from `reconstruction_metrics.csv`)
- `A₁_x(t)` = InSAR annual harmonic component at epoch t

Tier 2 activates only where `seasonal_applied=True` in `reconstruction_metrics.csv`.
The flag is read per station per layer — no hardcoded station names.

### Spatial extension

At each of 8,577 unmonitored grid points, `f̄_k` is interpolated from the 37 MLCW
stations using zone-stratified kriging. The four hydrogeological zones from
Azeriansyah et al. (2025) serve as spatial strata:

- **Zones I & II** (Changhua — low inter-layer coupling): ordinary kriging, no covariate
- **Zones III & IV** (Yunlin — moderate/high coupling): kriging with external drift,
  GWL trend as covariate

Once kriged `f̄_k(g)` is obtained at each grid point g, prediction follows:
```
compaction(g, t, k) = f̄_k(g) × InSAR(g, t)
```
using the 8,577-point InSAR feather (`gridpnt_500m_interp_insar_IDW_extend.feather`).

### Validation

- **Temporal:** walk-forward 4-fold (hold-outs: 2022, 2023, 2024, 2025)
  - Fold 1 (train 2015–2021, hold-out 2022) reported **separately** — most critical
  - Metric: RMSE vs anchor-only baseline (f̄_k $\times$ InSAR_anchor), saved as CSV
  - Skill score = 1 − RMSE_pred / RMSE_baseline (positive = improvement)
- **Spatial:** LOO-CV — hold out one station, krige from 36, compare to actual f̄_k

---

## 3. Directory Layout

```
scripts/15_prediction/
├── main.py             Orchestrator + argparse CLI (entry point only; no computation)
├── io_loader.py        All file I/O: reads InSAR feather, f̄_k CSVs, phase CSVs
├── walkforward.py      Walk-forward temporal validation logic (pure computation)
├── spatial_kriging.py  Zone-stratified kriging + spatial LOO-CV (pure computation)
├── reporter.py         All output writing: CSVs and figures (pure I/O)
└── paths.py            Centralised path definitions (platform-aware via paths.py resolver)
```

**One job per module. No module imports from another except through `main.py`.**

---

## 4. Module Contracts

### 4.1 `paths.py`
- Imports the project-level `paths.py` resolver for platform detection
- Defines all input and output paths as constants
- No logic, no computation

Key paths exposed:
```python
INSAR_STATIONS_FEATHER   # mlcw_interp_insar_IDW_extend.feather
INSAR_GRID_FEATHER       # gridpnt_500m_interp_insar_IDW_extend.feather
DIRECT_RATIO_DIR         # results/direct_ratio/{station}/
HARMONIC_DIR             # results/seasonal_insar_harmonic/{station}/
GWL_ASSIGNMENT_CSV       # gwl/gwl_to_mlcw_layer_assignment_v3.csv
ZONE_ASSIGNMENT_CSV      # (to be created: station → Azeriansyah zone I/II/III/IV)
```

### 4.2 `io_loader.py`
Functions (all return clean dataframes or dicts; raise on missing files):

```python
load_insar_stations(path) -> pd.DataFrame
    # Returns: index=Ename, columns=D{YYYYMMDD}... + metadata

load_insar_grid(path) -> pd.DataFrame
    # Returns: index=grid_id, columns=D{YYYYMMDD}... + X_UTM50N, Y_UTM50N

load_fbar(station, ratio_dir) -> pd.Series
    # Returns: index=depth_m, values=f_median (from direct_ratio_stats.csv)

load_reconstruction_metrics(station, harmonic_dir) -> pd.DataFrame
    # Returns: columns=[layer, fbar, seasonal_applied, r1_bar, dphi1_bar_days, ...]

load_phase_stability(station, harmonic_dir) -> pd.DataFrame
    # Returns: step3_phase_stability_summary.csv contents

load_zone_assignments(path) -> dict
    # Returns: {station_name: zone_label} e.g. {"TUKU": "III", "XIUTAN": "IV"}
```

### 4.3 `walkforward.py`
Functions (pure computation; no file I/O):

```python
run_walkforward(
    insar_series: pd.Series,         # InSAR epochs for one station
    mlcw_grouped: pd.DataFrame,      # observed per-layer MLCW (from reconstr folder)
    metrics: pd.DataFrame,           # reconstruction_metrics.csv for this station
    fold_years: list[int],           # e.g. [2022, 2023, 2024, 2025]
    train_end: int = 2021,
) -> pd.DataFrame
    # Returns: columns=[station, layer, fold_year, RMSE_tier1, RMSE_tier2,
    #                   RMSE_baseline, skill_tier1, skill_tier2, is_fold1]
    # Tier 2 column populated only where metrics.seasonal_applied == True
    # is_fold1 = True when fold_year == fold_years[0]
```

**Walk-forward logic (inside `run_walkforward`):**
1. For each fold year Y in fold_years:
   - Training window: epochs where year < Y
   - Compute f̄_k from training window (re-estimated per fold, not frozen from full record)
   - Baseline: f̄_k $\times$ InSAR_anchor (last training epoch value)
   - Tier 1 prediction: f̄_k $\times$ InSAR(t) for t in hold-out year Y
   - Tier 2 prediction: add F2 seasonal term if `seasonal_applied=True`
   - RMSE computed on hold-out year only

### 4.4 `spatial_kriging.py`
Functions (pure computation):

```python
krige_fbar_to_grid(
    station_fbar: pd.DataFrame,      # columns=[station, layer, fbar, X_UTM50N, Y_UTM50N]
    grid_coords: pd.DataFrame,       # columns=[grid_id, X_UTM50N, Y_UTM50N, zone]
    zone_assignments: dict,          # station → zone label
    method: str = "zone_stratified", # "zone_stratified" | "ordinary" | "idw"
    gwl_covariate: pd.Series = None, # optional GWL trend per grid point
) -> pd.DataFrame
    # Returns: columns=[grid_id, layer, fbar_kriged, fbar_std]

run_spatial_loo_cv(
    station_fbar: pd.DataFrame,
    zone_assignments: dict,
    method: str,
) -> pd.DataFrame
    # Returns: columns=[station, layer, fbar_actual, fbar_predicted, error_abs]
```

**Zone-stratified kriging logic:**
- Zones I & II: ordinary kriging (no external drift)
- Zones III & IV: kriging with external drift (GWL trend covariate)
- Separate variogram fitted per zone
- Fallback to IDW if kriging fails (logged as WARNING)

### 4.5 `reporter.py`
Functions (pure output writing; no computation):

```python
write_walkforward_csv(results: pd.DataFrame, output_dir: Path) -> None
    # Writes: {output_dir}/walkforward_rmse.csv

write_comparison_csv(results: pd.DataFrame, output_dir: Path) -> None
    # Writes: {output_dir}/trackA_comparison.csv (skill scores vs baseline)

write_spatial_loo_csv(results: pd.DataFrame, output_dir: Path) -> None
    # Writes: {output_dir}/spatial_loo_cv.csv

write_grid_fbar_csv(results: pd.DataFrame, output_dir: Path) -> None
    # Writes: {output_dir}/grid_fbar_kriged.csv

plot_walkforward_heatmap(results, output_dir) -> None
    # A4 landscape 11.7×8.3 in, 300 dpi

plot_spatial_fbar_maps(results, layer, output_dir) -> None
    # One map per layer; A4 landscape, 300 dpi

plot_loo_cv_error_map(results, output_dir) -> None
    # A4 landscape, 300 dpi
```

### 4.6 `main.py`
Orchestrates in this fixed order, logging each step:

```
[1/6] Loading data        → io_loader
[2/6] Walk-forward valid  → walkforward
[3/6] Spatial kriging     → spatial_kriging
[4/6] Spatial LOO-CV      → spatial_kriging
[5/6] Writing outputs     → reporter
[6/6] Done — results in {output_dir}
```

---

## 5. CLI Design (MintPy-style argparse)

```
usage: main.py [-h] [--stations STATIONS [STATIONS ...]]
               [--folds FOLDS [FOLDS ...]]
               [--krige {zone_stratified,ordinary,idw,none}]
               [--output-dir OUTPUT_DIR]
               [--insar-file INSAR_FILE]
               [--ratio-dir RATIO_DIR]
               [--harmonic-dir HARMONIC_DIR]
               [--skip-kriging]
               [--log-level {DEBUG,INFO,WARNING}]

InSAR-to-MLCW compaction prediction with walk-forward validation and spatial kriging.

optional arguments:
  --stations        Station names or 'all' (default: all)
  --folds           Hold-out years (default: 2022 2023 2024 2025)
  --krige           Kriging method (default: zone_stratified)
  --output-dir      Output root directory (default: results/prediction/)
  --insar-file      Override InSAR stations feather path
  --ratio-dir       Override direct ratio results directory
  --harmonic-dir    Override seasonal harmonic results directory
  --skip-kriging    Run walk-forward only; skip all spatial steps
  --log-level       Logging verbosity (default: INFO)
```

**Example invocations:**

```powershell
# Full run — all stations, all folds, zone-stratified kriging
$env:PYTHONPATH = ""; conda run -n fafalab python scripts/15_prediction/main.py `
    --stations all `
    --folds 2022 2023 2024 2025 `
    --krige zone_stratified `
    --output-dir results/prediction_v1

# TUKU diagnostic — fold 1 only, no kriging
$env:PYTHONPATH = ""; conda run -n fafalab python scripts/15_prediction/main.py `
    --stations TUKU `
    --folds 2022 `
    --skip-kriging `
    --output-dir results/prediction_debug

# IDW fallback spatial test
$env:PYTHONPATH = ""; conda run -n fafalab python scripts/15_prediction/main.py `
    --stations all `
    --krige idw `
    --output-dir results/prediction_idw_baseline
```

---

## 6. Output Contract (fixed regardless of flags)

```
{output-dir}/
├── walkforward_rmse.csv        station, layer, fold_year, RMSE_tier1, RMSE_tier2,
│                               RMSE_baseline, skill_tier1, skill_tier2, is_fold1
├── trackA_comparison.csv       station, layer, median_skill_tier1, median_skill_tier2
├── spatial_loo_cv.csv          station, layer, fbar_actual, fbar_predicted, error_abs
├── grid_fbar_kriged.csv        grid_id, layer, fbar_kriged, fbar_std, X_UTM50N, Y_UTM50N
└── figures/
    ├── walkforward_skill_heatmap.png     (stations × layers × folds)
    ├── spatial_fbar_map_{layer}.png      (one per layer: F1, F2, F3, F4)
    └── loo_cv_error_map.png
```

All figures: A4 landscape (11.7 $\times$ 8.3 in), 300 dpi, `bbox_inches='tight'`.

---

## 7. Non-Negotiable Rules (from CLAUDE.md)

- Walk-forward only — no random k-fold
- Fold 1 (2022 hold-out) must be flagged `is_fold1=True` and reported separately
- `walkforward_rmse.csv` must exist before any spatial work is reported
- Track A comparison CSV is mandatory output
- No per-station model selection by inspection — `seasonal_applied` flag drives Tier 2
  automatically from data, never from hardcoded station names
- All paths via `paths.py` — no hardcoded `D:\...` strings inside modules
- `fafalab` conda environment; always prefix with `$env:PYTHONPATH = ""`

---

## 8. Pre-Condition: Cross-Correlation Fix

Before the first run, the ring cross-correlation script must be rerun on observed data:

**File:** `scripts/11_data_analysis/ring_cross_correlation.py`, lines 63–69
**Change:** `group_byLayer_modeled` → `group_byLayer_reconstr`;
            `{station}_modeled_grouped.csv` → `{station}_reconst_grouped.csv`

This fix is independent of the new pipeline but must be done before any spatial
strata decisions reference the coupling numbers.

---

## 9. Implementation Order

1. Create `scripts/15_prediction/` directory with 6 empty files
2. Implement `paths.py` — all constants, no logic
3. Implement `io_loader.py` — I/O only, test with TUKU
4. Implement `walkforward.py` — TUKU single-station test, verify fold-1 RMSE matches
   known harmonic baseline (TUKU F2 2022 RMSE_baseline $\approx$ 3.495 mm)
5. Implement `reporter.py` — write CSV + one figure
6. Implement `spatial_kriging.py` — ordinary kriging first, zone-stratified second
7. Implement `main.py` — wire all modules, test full CLI run on TUKU
8. Batch run: `--stations all --folds 2022 2023 2024 2025`
