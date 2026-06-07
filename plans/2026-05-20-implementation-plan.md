# Candidate E (DLLM) and Candidate F (IHM + per-layer $\beta$_k) — Layer-Grouped Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement, validate, and compare Candidate E (Distributed Lag Linear Model, DLLM) and Candidate F (two-regime Inelastic Head Model with per-layer InSAR coupling $\beta$_k) across all 37 MLCW stations using the **layer-grouped MLCW representation** — 4–6 hydrogeological layer units (F1, T1, F2, T2, F3, F4) per station instead of 60 imaginary 5-m rings. Trend-removed GWL and InSAR are co-drivers; MLCW layer compaction is the calibration target.

**Architecture:** Three new source modules handle GWL loading and trend removal (`gwl_loader.py`), the two model fitters per layer (`track_b_models.py`), and walk-forward validation bookkeeping (`validation.py`). Three pilot scripts orchestrate data loading, fitting, and result export at increasing scale (Tuku → one no-GWL station → all 37 stations). All scripts run under the `fafalab` conda environment.

**Tech Stack:** Python 3.x, fafalab conda environment, numpy, pandas, scipy (lstsq, linalg), pyarrow (feather), pathlib, logging. No new package installations needed.

<div style="background-color:#ffebee; border-left:4px solid #c62828; padding:8px; margin:6px 0;">
~~`h5py` (GWL HDF5 read)~~ — (removed 2026-05-20: GWL is read from feather files; the HDF5 is the archived source only. No `h5py` calls needed.)
</div>

---

## Context

The station-level method decision (Decision 1 in `discussion_20260519_v3.md`) gates all subsequent spatial work. Candidates A (static proportionality) and B (anchor-only) have been tested; both are Class III. Candidates D/E/F are the first Class I/II formulas attempted: they produce per-layer predictions from InSAR and trend-removed GWL alone, without any MLCW initial state at deployment.

**Layer-grouping motivation (2026-05-20):** The 60-ring representation uses imaginary 5-m slabs that do not correspond to physical geological units. The layer-grouped representation collapses these into named aquifer/aquitard units (F1, T1, F2, T2, F3, F4), which:
1. Reduces the prediction target from 60 to ~6 outputs per station (10$\times$ fewer fits).
2. Makes GWL assignment physically direct: F2 compaction is driven by F2 aquifer head — no nearest-neighbour approximation needed.
3. Produces outputs directly interpretable for policy: "aquifer F2 contributed X mm to total surface subsidence this year."

This plan supersedes `2026-05-19-candidate-E-F-implementation.md` for the layer-grouped pipeline. Candidate D shares its IHM fitting logic with Candidate F (Candidate D is Candidate F with a layer-invariant $\beta$₀), so a single `fit_ihm_f_one_layer` function handles both.

The 2022 walk-forward fold is the operational stress test: raw MLCW data were entirely absent during the 2022 drought cycle. Track B must predict per-layer compaction using only InSAR and trend-removed GWL — the deployment scenario when future MLCW stations shut down.

---

## Pre-declared D-vs-E decision rule (written before any code is run)

After fitting Candidate D (IHM without per-layer $\beta$_k, i.e., a layer-invariant $\beta$₀) at Tuku in Pilot 1: count the fraction of calibration-window epochs that fall in the inelastic regime (raw h_layer(t) $\le$ $h_{c}$(layer)) at each layer. If more than 20% of epochs are inelastic at more than 50% of the layers → **adopt Candidate D or F as production**. If fewer → **adopt Candidate E (DLLM) as production**. This rule is evaluated once, at Pilot 1, and the result is written to `output/pilot1/decision_rule_result.txt` before any hold-out RMSE numbers are examined.

> **UPDATE 2026-05-25 — Rule Retired. IHM-F (Candidate F) Declared Universal Production Method.**
>
> The 2S-TOOL batch run (195 station$\times$ layer pairs) confirmed that $S_{kv}$ > $S_{ke}$ at the majority of layers across the network, establishing that the inelastic regime is globally active. The D-vs-E decision rule is therefore superseded: Candidate F (IHM-F, two-regime IHM with per-layer $\beta$_k) is the production method for all 37 stations. Candidate E (DLLM) is retired as a production candidate.
>
> Rationale: 2S-TOOL provided independent, data-driven estimates of $S_{ke}$ and $S_{kv}$ per layer before any IHM regression is run. These estimates confirm the physical premise (inelastic sediment is present) and provide starting values for IHM-F calibration. The decision rule is no longer needed.
>
> Candidate D (layer-invariant $\beta$₀) remains available as a simplified ablation check but is not the primary production formula. All Task 3 / Task 5 work targets IHM-F directly.

---

## Walk-forward fold definitions

| Fold | Training window | Hold-out window | Note |
|---|---|---|---|
| 1 | 2015-01-21 – 2021-11-30 | 2022-01-01 – 2022-12-31 | MLCW reconstructed; primary operational stress test for Track B |
| 2 | 2015-01-21 – 2022-12-31 | 2023-01-01 – 2023-12-31 | |
| 3 | 2015-01-21 – 2023-12-31 | 2024-01-01 – 2024-12-31 | |
| 4 | 2015-01-21 – 2024-12-31 | 2025-01-01 – 2025-12-31 | |

Fold-1 RMSE is always reported separately from folds 2–4. The exit criterion at Pilot 3 is: fold-1 median RMSE $\le$ 1.5 $\times$ folds-2-to-4 median RMSE across the 19 active stations.

---

## Key data paths (read-only inputs)

| Purpose | Path |
|---|---|
| <span style="color:#c62828">~~GWL daily HDF5 (306 wells, 2000–2025)~~</span> | <span style="color:#c62828">~~`D:\1000_SCRIPTS\004_Project003\20251229_Gwater_Levels\20260108_GWL_CRFP_daily_modeled.h5`~~ (archived source; not read by gwl_loader.py)</span> |
| GWL feather timeseries (100 files) | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\data\gwl\well_timeseries\{STATION}_gwl_timeseries.feather` |
| GWL flat table (screen depths, coordinates) | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\data\gwl\well_info\gwl_allwells_flat.csv` |
| GWL linkage report | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\data\gwl\inspection_reports\gwl_linkage_report.csv` |
| InSAR at 37 MLCW stations (feather) | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\data\insar\timeseries\mlcw_interp_insar_IDW_extend.feather` |
| **MLCW layer-grouped timeseries — signal-reconstructed (Track B model fitting)** | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\data\mlcw\group_byLayer_reconstr\{STATION}_reconst_grouped.csv` |
| **MLCW layer-grouped timeseries — raw-summed (2S-TOOL reference)** | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\data\mlcw\group_byLayer_orig\{STATION}_orig_grouped.csv` — **Note:** `group_byLayer_orig` (raw ring sums) was used for the 2026-05-27 2S-TOOL run. It produces lower $S_{kv}$ than `group_byLayer_reconstr` (reconstructed signal) because elastic recovery oscillations are retained. Declare which source is canonical before IHM-F fitting begins. |
| **MLCW ring-to-layer classification** | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\data\mlcw\group_byLayer_reconstr\{STATION}_classify_table.csv` |
| **GWL-to-MLCW layer assignment (v3)** | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\data\gwl\gwl_to_mlcw_layer_assignment_v3.csv` — 195 rows, updated 2026-05-21. Use `v3` (not `v1` or `v2`) for all Track B work. |
| **MLCW-aligned GWL timeseries (per-pair, 189 files)** | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\data\gwl\mlcw_gwl_timeseries\{MLCW}_{GWL}_{WELLCODE}.feather` — 264 rows per file, aligned to MLCW monitoring timeline. Used by `prepare_2stool_inputs.py`. |
| **2S-TOOL aggregated results** | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\data\gwl\2stool_outputs\2stool_results_summary.csv` — 182 rows (131 OK + 58 NEG_SKV; 6 errors excluded). Columns: `station`, `layer`, `skv`, `ske_weighted`, `ske_mean`, `n_accepted_loops`, `preconsolidation_depth_hc`, etc. Generated 2026-05-27. |
| BME hydrofacies voxel (fines-fraction at depth) | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\data\hydrofacies\mlcw_hydrofacies_5m.csv` |
| $\alpha$ prior (column-scaling factors) | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\data\alpha\alpha_comparison_all_stations_v3.csv` |

> **Station count:** 37 (JINHU_XIN and LUNFENG_XIN excluded — no `_reconst_grouped.csv` file produced by `mlcw_by_group.py`).

---

## Available scripts and modules

### Core inversion library (`D:\112_PROJECT_002\src\`)

**loader.py** — Data assembly for InSAR, MLCW, and $\alpha$ priors.
- `load_insar_data()` → dict with `data_cumulative` (stations $\times$ 785 epochs, mm), `dates`, `stations`. Cumulative InSAR requires explicit negation: `x_raw = -insar['data_cumulative'].loc[STATION].values`.
- <span style="color:#c62828">~~`load_mlcw_5m_grid(station_name)`~~</span> — (not used in layer pipeline; load `_reconst_grouped.csv` directly with `pd.read_csv`)
- `load_alpha_prior()` → DataFrame with $\alpha$ per station ($\alpha$ > 0.9 clamped to 0.9).
- Constants: `INSAR_REFERENCE_DATE`. <span style="color:#c62828">~~`DEPTH_GRID_ACTIVE`, `N_DEPTHS = 60`~~</span> — (not used; replaced by layer column names from `_reconst_grouped.csv` header)

**system.py, solvers_temporal.py, postprocess.py, reporting.py** — Stage 1 inversion; **not needed for Track B layer pipeline**.

### GWL processing utilities
Same feather-based scripts as documented in `discussion_20260520.md` §3:
- `scripts\04_gwl_processing\inspect_gwl_feather.py`
- `scripts\04_gwl_processing\check_gwl_linkage.py`

### Key module paths and import statements

```python
import sys
sys.path.insert(0, r'D:\112_PROJECT_002')
from src.loader import load_insar_data, load_alpha_prior, INSAR_REFERENCE_DATE
import pandas as pd
import numpy as np

# Layer-grouped MLCW loading (direct CSV read — no wrapper needed)
df = pd.read_csv(r"...\group_byLayer_reconstr\TUKU_reconst_grouped.csv", index_col=0, parse_dates=True)
layers = [c for c in df.columns]  # e.g. ['F1', 'T1', 'F2', 'T2', 'F3', 'F4']

# Track B (new modules, to be created)
from src.gwl_loader import (
    load_gwl_flat_table, load_gwl_timeseries_for_station, align_gwl_to_insar_epochs,
    fit_linear_trend, remove_trend, trend_remove_series,
    assign_gwl_to_layers, prepare_gwl_inputs_layers, find_nearest_gwl_station
)
from src.track_b_models import (
    fit_dllm_one_layer, predict_dllm,
    fit_ihm_f_one_layer, predict_ihm_f
)
from src.validation import make_fold_masks, calib_mask, fold_rmse_table, rmse
```

---

## Quick reference: Data directory structure

```
D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\
├── data\
│   ├── gwl\
│   │   ├── well_info\gwl_allwells_flat.csv
│   │   ├── well_timeseries\{STATION}_gwl_timeseries.feather  (100 files)
│   │   └── inspection_reports\gwl_linkage_report.csv
│   ├── insar\timeseries\mlcw_interp_insar_IDW_extend.feather
│   └── mlcw\
│       ├── group_byLayer_reconstr\{STATION}_reconst_grouped.csv  ← PRIMARY MLCW INPUT (signal-reconstructed)
│       ├── group_byLayer_reconstr\{STATION}_classify_table.csv   ← layer classification
│       ├── group_byLayer_orig\{STATION}_orig_grouped.csv  ← raw-summed MLCW (used for 2S-TOOL)
│       ├── group_byLayer_modeled\{STATION}_modeled_grouped.csv  ← IHM-F model output (Track B)
│       └── regular_5m\{STATION}_5m_grid.csv             (not used in this pipeline)

D:\112_PROJECT_002\
├── src\
│   ├── loader.py                (reuse load_insar_data, load_alpha_prior)
│   ├── gwl_loader.py            ← NEW (Task 1)
│   ├── track_b_models.py        ← NEW (Task 3)
│   └── validation.py            ← NEW (Task 2)
├── pilot1_tuku.py               ← NEW (Task 5)
├── pilot2_no_gwl_station.py     ← NEW (Task 6)
├── pilot3_allstations.py        ← NEW (Task 7)
└── output\pilot1\, pilot2\, pilot3\
```

---

## Output paths (created by this plan)

| Purpose | Path |
|---|---|
| GWL loader module | `D:\112_PROJECT_002\src\gwl_loader.py` |
| Validation utilities | `D:\112_PROJECT_002\src\validation.py` |
| Model fitters | `D:\112_PROJECT_002\src\track_b_models.py` |
| Pilot 1 script | `D:\112_PROJECT_002\pilot1_tuku.py` |
| Pilot 2 script | `D:\112_PROJECT_002\pilot2_no_gwl_station.py` |
| Pilot 3 batch script | `D:\112_PROJECT_002\pilot3_allstations.py` |
| Pilot 1–3 outputs | `D:\112_PROJECT_002\output\pilot{1,2,3}\` |
| Pilot 3 calibration table (mirror) | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\results\dllm_method\` or `ihm_f_method\` |

---

## Task 1: GWL loader module (`src/gwl_loader.py`)

**Files:**
- Create: `D:\112_PROJECT_002\src\gwl_loader.py`

**What this module does.** Reads GWL piezometric head time series from feather files, resamples daily values to the 5-day InSAR epoch grid (nearest-day within $\pm$ 3 days), assigns each MLCW layer to its nearest GWL well by screen midpoint within the layer's depth range, fits a linear trend over the calibration window, and returns trend-removed head arrays ready for model fitting.

**Key constants to define at module level:**
- <span style="color:#c62828">~~`GWL_H5_FILE`~~</span> — (removed: HDF5 not read by this module)
- `GWL_FEATHER_DIR` — `r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\data\gwl\well_timeseries"`
- `GWL_FLAT_CSV` — `r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\data\gwl\well_info\gwl_allwells_flat.csv"`
- `CALIB_END` — `datetime(2021, 11, 30)`
- `INSAR_START` — `pd.Timestamp("2015-01-21")`
- `INSAR_END` — `pd.Timestamp("2025-12-11")`

**Functions to implement:**

`load_gwl_flat_table()` — reads `gwl_allwells_flat.csv`, adds `screen_mid_m = (screen_top_m + screen_bot_m) / 2.0`. Returns DataFrame.

`load_gwl_timeseries_for_station(station_name)` — reads `{station_name}_gwl_timeseries.feather` from `GWL_FEATHER_DIR` using `pd.read_feather()`. Parses `datetime` column as DatetimeIndex. Returns `{wellcode: pd.Series}`. If feather file not found, logs warning and returns empty dict.

<div style="background-color:#ffebee; border-left:4px solid #c62828; padding:8px; margin:6px 0;">

~~Step 1.1 (old plan): Inspect the HDF5 structure. Run `python -c "import h5py; f = h5py.File(...)"` ...~~ — (removed 2026-05-20: Decision made in `discussion_20260520.md` §3. Use feather. No HDF5 inspection needed.)

</div>

`align_gwl_to_insar_epochs(gwl_series, insar_dates)` — for each of the 785 InSAR epoch dates, finds nearest GWL observation within $\pm$ 3 calendar days; returns float64 ndarray of length 785 (NaN for unmatched epochs).

`fit_linear_trend(values, epoch_indices)` — `numpy.polyfit(x, y, 1)` over non-NaN pairs. Requires $\ge$ 20 valid points; returns `(0.0, 0.0)` otherwise. Returns `(slope, intercept)`.

`remove_trend(values, epoch_indices, slope, intercept)` — subtracts linear trend from `values`, preserving NaN.

`trend_remove_series(values, epoch_idx, calib_mask_arr)` — convenience wrapper: fits trend on calibration-window epochs only, removes trend from full series. Returns `(tilde, slope, intercept)`.

`assign_gwl_to_layers(station_name, classify_df, gwl_flat_df, gwl_ts_dict, insar_dates)` — replaces the old 60-slab `assign_gwl_to_mlcw_depths()`. For each unique layer in `classify_df`:
1. Compute the layer depth range: `depth_min = classify_df[classify_df.layer == L].depth.min()`, `depth_max = max`.
2. Find GWL candidate wells from `gwl_flat_df` (filtered to this station) whose `screen_mid_m` falls within `[depth_min, depth_max]`.
3. If no candidate found, fall back to the well with the nearest `screen_mid_m` by absolute depth difference (same 1D nearest-neighbour, but only over ~2–5 candidates not 60).
4. Align the selected well's timeseries via `align_gwl_to_insar_epochs`.
Returns `(gwl_layer_raw, assigned_screens_dict)` where `gwl_layer_raw` is ndarray (n_epochs, n_layers) and `assigned_screens_dict` maps layer name → wellcode string.

`prepare_gwl_inputs_layers(mlcw_station_name, gwl_flat_df, insar_dates, classify_df, calib_mask)` — top-level function for pilot scripts. Calls `load_gwl_timeseries_for_station`, then `assign_gwl_to_layers`, then fits and removes trend per layer column. Computes `h_c_layer` (preconsolidation head per layer = min raw GWL over calibration window). Returns dict: `gwl_raw` (n_epochs, n_layers), `gwl_tilde` (n_epochs, n_layers), `h_c` (n_layers,), `trend_slope` (n_layers,), `trend_intercept` (n_layers,), `assigned_screens` (dict layer→wellcode), `has_gwl` (bool), `layers` (list of layer names).

If the station has no co-located GWL and `has_gwl=False` (fully blocked or no co-located station), all arrays are NaN and the calling code invokes `find_nearest_gwl_station()` as for the 24-station proxy path.

`find_nearest_gwl_station(mlcw_x, mlcw_y, gwl_flat_df, n_nearest=1)` — 2D Euclidean distance from MLCW centroid to each GWL station centroid (TWD97 metres). Returns list of `n_nearest` station names sorted ascending by distance.

**Verification step for Task 1:**
```
conda run -n fafalab python -c "
import sys; sys.path.insert(0, 'D:/112_PROJECT_002')
from src.gwl_loader import load_gwl_flat_table, load_gwl_timeseries_for_station
df = load_gwl_flat_table()
print(df.columns.tolist())
print(df[df['station']=='TUKU'][['wellcode','screen_mid_m']].head())
ts = load_gwl_timeseries_for_station('TUKU')
print(list(ts.keys()))
for k,v in ts.items():
    print(k, v.dropna().index[0], v.dropna().index[-1], v.notna().sum())
"
```
Expected: TUKU has 2–3 wells with screen midpoints at ~82, ~177, ~260 m; each series > 3000 non-NaN values.

- [ ] **Step 1.1:** Implement all functions listed above in `D:\112_PROJECT_002\src\gwl_loader.py`.
- [ ] **Step 1.2:** Run the REPL smoke test above. Confirm TUKU screen midpoints match known values.
- [ ] **Step 1.3:** Also test `assign_gwl_to_layers` for TUKU: confirm 6 layers each get an assigned wellcode.
- [ ] **Step 1.4:** Commit: `git commit -m "feat: add gwl_loader — feather read, epoch alignment, layer assignment, trend removal"`

---

## Task 2: Walk-forward validation utilities (`src/validation.py`)

**Files:**
- Create: `D:\112_PROJECT_002\src\validation.py`

**Unchanged from original plan.** Fold definitions, `make_fold_masks`, `calib_mask`, `rmse`, `fold_rmse_table` are all data-shape agnostic and require no modification for the layer-grouped pipeline.

**FOLD_DEFINITIONS:**
```
fold 1: train end 2021-11-30, hold-out 2022-01-01 to 2022-12-31
fold 2: train end 2022-12-31, hold-out 2023-01-01 to 2023-12-31
fold 3: train end 2023-12-31, hold-out 2024-01-01 to 2024-12-31
fold 4: train end 2024-12-31, hold-out 2025-01-01 to 2025-12-31
CALIB_START = '2015-01-21'
```

**Verification step:**
```
conda run -n fafalab python -c "
import sys; sys.path.insert(0, 'D:/112_PROJECT_002')
from src.loader import load_insar_data
from src.validation import make_fold_masks, calib_mask
insar = load_insar_data()
folds = make_fold_masks(insar['dates'])
for f in folds:
    print(f'Fold {f[\"fold\"]}: train={f[\"train_mask\"].sum()}, holdout={f[\"holdout_mask\"].sum()}')
"
```
Expected: train counts increase fold-to-fold; each hold-out $\approx$ 60–73 epochs.

- [ ] **Step 2.1:** Implement `validation.py`.
- [ ] **Step 2.2:** Run verification command.
- [ ] **Step 2.3:** Commit: `git commit -m "feat: add validation — walk-forward fold masks and RMSE utilities"`

---

## Task 3: Model fitter module (`src/track_b_models.py`)

**Files:**
- Create: `D:\112_PROJECT_002\src\track_b_models.py`

**What this module does.** Per-layer fitters for Candidate E (DLLM) and Candidate F / D (IHM). Both fitters receive trend-removed arrays for **one layer** and one fold's training mask, and return a dict of fitted parameters plus a `fit_ok` boolean. Function signatures are identical to the 60-depth version; the change is naming (`one_layer` instead of `one_depth`) and the understanding that inputs correspond to a geological layer unit, not a 5-m slab.

**Physical notation:**
- `Y_tilde` — trend-removed MLCW compaction at layer L (mm); regression target
- `h_tilde` — trend-removed GWL for the layer's assigned well (m)
- `x_tilde` — trend-removed InSAR surface displacement (mm); spatial co-driver
- `h_raw` — raw GWL (m); used for regime test in Candidate D/F only
- `h_c` — preconsolidation head (m, raw scale); from `prepare_gwl_inputs_layers`

**Module-level defaults:**
- `DEFAULT_L_GWL = 15` — GWL lag window (epochs, ~6 months at 12-day cadence)
- `DEFAULT_M_INSAR = 4` — InSAR lag window (~7 weeks)

**`fit_dllm_one_layer(Y_tilde, h_tilde, x_tilde, train_mask, lag_L, lag_M)` — Candidate E.**
Build OLS design matrix: each training row = `[h̃(t), h̃(t-1), …, h̃(t-L), x̃(t), …, x̃(t-M)]`. Drop rows with any NaN. Use `scipy.linalg.lstsq`. Require $\ge$ 20 valid rows; return `fit_ok=False` otherwise.
Return dict: `w_h` (L+1,), `w_x` (M+1,), `lag_L`, `lag_M`, `n_train_used`, `fit_ok`.

**`predict_dllm(h_tilde, x_tilde, w_h, w_x)` — Candidate E predictor.**
Full-length prediction array; NaN before `max(lag_L, lag_M)`.

**`fit_ihm_f_one_layer(Y_tilde, h_tilde, x_tilde, h_raw, h_c, train_mask, tau_max_epochs=50, per_layer_beta=True)` — Candidate D and F.**
Grid-search $\tau$ $\in$ {0…tau_max_epochs}. At each $\tau$, two-block OLS:
- Elastic (h_raw[t] > $h_{c}$): row = `[h̃(t-τ), 0.0, x̃(t)]`
- Inelastic (h_raw[t] $\le$ $h_{c}$): row = `[0.0, h̃(t-τ), x̃(t)]`
Columns → `[S_ske, S_skv, β_k]` (or $\beta$₀ if `per_layer_beta=False`). Minimise training RMSE over $\tau$.
Return dict: `S_ske`, `S_skv`, `beta_k`, `tau`, `h_c`, `n_train_used`, `fit_ok`, `n_inelastic_epochs`.

**`predict_ihm_f(h_tilde, x_tilde, h_raw, S_ske, S_skv, beta_k, tau, h_c)` — Candidate D/F predictor.**
Regime test per epoch; NaN before `tau`.

**Verification step:**
```
conda run -n fafalab python -c "
import sys, numpy as np; sys.path.insert(0, 'D:/112_PROJECT_002')
from src.track_b_models import fit_dllm_one_layer, predict_dllm, fit_ihm_f_one_layer
np.random.seed(0)
n = 600
h = np.sin(2*np.pi*np.arange(n)/73) * 2.0
x = np.cumsum(np.random.randn(n) * 0.1)
Y = 0.5 * np.roll(h, 3) + 0.3 * x + np.random.randn(n) * 0.05
Y[:3] = np.nan
train_mask = np.zeros(n, dtype=bool); train_mask[:500] = True
res_e = fit_dllm_one_layer(Y, h, x, train_mask, lag_L=10, lag_M=4)
print('DLLM fit_ok:', res_e['fit_ok'], '  w_h_sum:', round(float(np.nansum(res_e['w_h'])),3))
h_c = float(np.min(h[:500]))
res_f = fit_ihm_f_one_layer(Y, h, x, h, h_c, train_mask)
print('IHM-F fit_ok:', res_f['fit_ok'], '  n_inelastic:', res_f['n_inelastic_epochs'])
"
```
Expected: both `fit_ok=True`; `w_h` sum $\approx$ 0.5.

- [ ] **Step 3.1:** Implement `track_b_models.py`.
- [ ] **Step 3.2:** Run synthetic verification command.
- [ ] **Step 3.3:** Commit: `git commit -m "feat: add track_b_models — DLLM and IHM-F per-layer fitters"`

---

## Task 4: Extend `gwl_loader.py` with `trend_remove_series`

`trend_remove_series(values, epoch_idx, calib_mask_arr)` is a convenience wrapper calling `fit_linear_trend` on calibration-window epochs and `remove_trend` on the full series. Returns `(tilde, slope, intercept)`. Used by pilot scripts to detrend MLCW layer columns and InSAR with identical treatment.

**Note:** This function was already specified in Task 1 above. It is listed here as a separate task to match the original plan's structure so the commit history is traceable.

**Verification step:**
```
conda run -n fafalab python -c "
import sys, numpy as np; sys.path.insert(0, 'D:/112_PROJECT_002')
from src.loader import load_insar_data
from src.validation import calib_mask
from src.gwl_loader import trend_remove_series
insar = load_insar_data()
dates = insar['dates']; epoch_idx = np.arange(len(dates)); cm = calib_mask(dates)
x_raw = -insar['data_cumulative'].loc['TUKU'].values
x_tilde, slp, icp = trend_remove_series(x_raw, epoch_idx, cm)
print('x_tilde range:', round(float(np.nanmin(x_tilde)),2), 'to', round(float(np.nanmax(x_tilde)),2), 'mm')
import pandas as pd
GROUPED = r'D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\data\mlcw\group_byLayer_reconstr\TUKU_reconst_grouped.csv'
df = pd.read_csv(GROUPED, index_col=0, parse_dates=True)
# align to insar dates
tuku_dates_set = {d.strftime('%Y%m%d') for d in dates}
df.index = pd.to_datetime(df.index)
df_aligned = df.reindex(dates, method='nearest', tolerance=pd.Timedelta('3d'))
Y_F2 = df_aligned['F2'].values
Y_tilde, _, _ = trend_remove_series(Y_F2, epoch_idx, cm)
print('Y_tilde(F2) range:', round(float(np.nanmin(Y_tilde)),2), 'to', round(float(np.nanmax(Y_tilde)),2), 'mm')
"
```
Expected: both tildes centered near zero; no error.

- [ ] **Step 4.1:** Confirm `trend_remove_series` is in `gwl_loader.py` (from Task 1).
- [ ] **Step 4.2:** Run the verification command.
- [ ] **Step 4.3:** Commit: `git commit -m "feat: add trend_remove_series to gwl_loader for MLCW and InSAR detrending"`

---

## Task 5: Pilot 1 — both candidates at Tuku (`pilot1_tuku.py`)

**Files:**
- Create: `D:\112_PROJECT_002\pilot1_tuku.py`
- Output dir: `D:\112_PROJECT_002\output\pilot1\`

**What this script does.** Loads all inputs for Tuku (InSAR, MLCW layer-grouped, GWL). Trend-removes all streams. Fits both Candidate E (DLLM) and Candidate F (IHM-F) at **all layers** (F1, T1, F2, T2, F3, F4 — ~6 total) across all 4 folds. Applies the pre-declared D-vs-E decision rule. Runs lag sensitivity analysis for DLLM at layer F2.

**Input data sources:**
- InSAR at Tuku: `load_insar_data()` → `insar['data_cumulative'].loc['TUKU']`, **negated**.
- MLCW layer-grouped: `pd.read_csv(GROUPED_DIR / 'TUKU_reconst_grouped.csv', index_col=0, parse_dates=True)` → aligned to InSAR dates.
- Layer classification: `pd.read_csv(GROUPED_DIR / 'TUKU_classify_table.csv')`.
- GWL: `prepare_gwl_inputs_layers('TUKU', gwl_flat_df, insar_dates, classify_df, calib_mask)`.
- Folds: `make_fold_masks(insar['dates'])`.

**Script structure:**
1. Load and align all data.
2. Trend-remove MLCW (per layer), InSAR, GWL (done inside `prepare_gwl_inputs_layers`).
3. For each layer L, for each fold: fit DLLM and IHM-F on training mask; predict on hold-out; record RMSE.
4. Re-fit on fold-1 training mask for calibration parameter summary.
5. Save `tuku_dllm_summary.csv` and `tuku_ihm_f_summary.csv` (~6 rows each).
6. Save `regime_activity_tuku.csv` (~6 rows: layer, $h_{c}$, n_calib_epochs, n_inelastic, frac_inelastic).
7. Apply decision rule → `decision_rule_result.txt`.
8. Lag sensitivity for layer F2: L $\in$ {5, 10, 15, 20, 30}, M $\in$ {2, 4, 6} → `lag_sensitivity_F2.csv`.

**Output file columns:**
- `tuku_dllm_summary.csv`: station, layer, w_h_sum, w_x_sum, lag_L, lag_M, fit_ok, n_train_used, rmse_fold1, rmse_fold2, rmse_fold3, rmse_fold4, rmse_folds2to4_median.
- `tuku_ihm_f_summary.csv`: station, layer, $S_{ske}$, $S_{skv}$, beta_k, tau_epochs, $h_{c}$, n_inelastic_epochs, fit_ok, n_train_used, rmse_fold1, rmse_fold2, rmse_fold3, rmse_fold4, rmse_folds2to4_median.
- `regime_activity_tuku.csv`: layer, $h_{c}$, n_calib_epochs, n_inelastic, frac_inelastic.
- `decision_rule_result.txt`: plain text — decision string (`CANDIDATE_E` or `CANDIDATE_D_OR_F`).
- `lag_sensitivity_F2.csv`: L, M, layer, rmse_fold1, rmse_fold2, rmse_fold3, rmse_fold4.

**Exit criteria before Pilot 2:**
1. Both summary CSVs have ~6 rows with `fit_ok=True` at > 4 layers.
2. `tuku_ihm_f_summary.csv` shows `S_skv / S_ske > 1.0` at F2 and F3 (clay-rich aquifers). Ratio < 1.0 at all layers is physically implausible.
3. Fold-1 RMSE within 3$\times$ of folds-2-4 median. If worse, inspect 2022 GWL data quality.
4. `decision_rule_result.txt` exists and contains a clear decision string.

**Run command:** `conda run -n fafalab python D:\112_PROJECT_002\pilot1_tuku.py`

- [ ] **Step 5.1:** Write `pilot1_tuku.py`.
- [ ] **Step 5.2:** Run script. Expected runtime: < 2 minutes (6 layers $\times$ 4 folds $\times$ $\tau$-search for IHM-F).
- [ ] **Step 5.3:** Inspect output CSVs. Verify exit criteria.
- [ ] **Step 5.4:** Commit: `git commit -m "feat: Pilot 1 — DLLM and IHM-F at Tuku (layer-grouped) with D-vs-E decision rule"`

---

## Task 6: Pilot 2 — production formula at one no-GWL station (`pilot2_no_gwl_station.py`)

**Files:**
- Create: `D:\112_PROJECT_002\pilot2_no_gwl_station.py`
- Output dir: `D:\112_PROJECT_002\output\pilot2\`

**Purpose.** Quantify RMSE inflation from horizontal GWL proxy interpolation at the 24 stations that use nearest-proxy GWL (18 no co-located + 6 fully blocked). Xizhou is the test station (3 of 7 wells have valid screen depths → confirmed in `discussion_20260520.md` §4).

**Script structure:**
1. Read Xizhou TWD97 coordinates from `mlcw_interp_insar_IDW_extend.feather` metadata.
2. Call `find_nearest_gwl_station(xizhou_x, xizhou_y, gwl_flat_df)`.
3. Load GWL from proxy station via `prepare_gwl_inputs_layers(proxy_station, ...)`.
4. Load MLCW layer-grouped and InSAR for Xizhou.
5. Read decision from `output/pilot1/decision_rule_result.txt`; default to DLLM if absent.
6. Fit chosen candidate at all layers $\times$ 4 folds.
7. Save `xizhou_pilot2_summary.csv` (~6 rows, same columns as Pilot 1).
8. Compare folds-2-to-4 median RMSE at Xizhou vs Tuku. Save `inflation_report.txt`.

**Exit criterion:** Median RMSE inflation at Xizhou vs Tuku (folds 2–4) $\le$ 1.5$\times$. If exceeded, upgrade `find_nearest_gwl_station` to return 3 nearest and use IDW averaging before Pilot 3.

**Run command:** `conda run -n fafalab python D:\112_PROJECT_002\pilot2_no_gwl_station.py`

- [ ] **Step 6.1:** Ensure `find_nearest_gwl_station` is in `gwl_loader.py`.
- [ ] **Step 6.2:** Write `pilot2_no_gwl_station.py`.
- [ ] **Step 6.3:** Run script. Check `inflation_report.txt`. Extend to 3-nearest IDW if inflation > 1.5$\times$.
- [ ] **Step 6.4:** Commit: `git commit -m "feat: Pilot 2 — production formula at no-GWL station (Xizhou) with inflation check"`

---

## Task 7: Pilot 3 — batch fit at all 37 stations (`pilot3_allstations.py`)

**Files:**
- Create: `D:\112_PROJECT_002\pilot3_allstations.py`
- Output dir: `D:\112_PROJECT_002\output\pilot3\`

**Purpose.** Produce the authoritative per-station per-layer calibration table that Stage 2 spatial work reads from.

**Script structure:**
1. Read decision from `output/pilot1/decision_rule_result.txt`.
2. Load GWL flat table.
3. Load InSAR feather metadata for TWD97 coordinates of all stations.
4. For each of the **37 stations** (JINHU_XIN and LUNFENG_XIN skipped — no `_reconst_grouped.csv`):
   a. Load `{STATION}_reconst_grouped.csv` and `{STATION}_classify_table.csv`.
   b. Align layer-grouped MLCW to InSAR epoch dates; trend-remove each layer column.
   c. Load InSAR; negate; trend-remove.
   d. Determine GWL source:
      - 15 co-located stations with valid screen depths: use own feather
      - 6 fully-blocked + 18 no-GWL = **24 stations**: use `find_nearest_gwl_station()`
   e. Call `prepare_gwl_inputs_layers(source_station, ...)`.
   f. For each layer, for each fold: fit production formula; predict; record RMSE.
   g. Re-fit on fold-1 training mask for calibration summary.
   h. Append ~6 rows (one per layer) to results list.
5. Write to `output/pilot3/dllm_allstations_summary.csv` (or `ihm_f_allstations_summary.csv`).
   **Row count: 37 $\times$ ~6 $\approx$ 222 rows** (vs. 2,340 in the 60-depth plan).
6. Mirror copy to `results\dllm_method\` (or `ihm_f_method\`).
7. Compute fold-1 vs folds-2-4 exit criterion; log result.

**Output file columns:** station, layer, model, gwl_source, [model-specific parameters], fit_ok, n_train_used, rmse_fold1, rmse_fold2, rmse_fold3, rmse_fold4, rmse_folds2to4_median.

**Exit criterion:** Median fold-1 RMSE across the 19 active stations $\le$ 1.5 $\times$ median folds-2-to-4 RMSE.

**Expected runtime:** < 5 minutes (6 layers $\times$ 37 stations $\times$ 4 folds; IHM-F $\tau$-search is the dominant cost but over only 6 layers).

**Run command:** `conda run -n fafalab python D:\112_PROJECT_002\pilot3_allstations.py`

- [ ] **Step 7.1:** Write `pilot3_allstations.py`.
- [ ] **Step 7.2:** Run script. Monitor log for per-station progress and `fit_ok=False` warnings.
- [ ] **Step 7.3:** Inspect CSV: verify ~222 rows; check fold-1 RMSE is not systematically >> folds-2-4.
- [ ] **Step 7.4:** Commit: `git commit -m "feat: Pilot 3 — batch production formula at all 37 MLCW stations (layer-grouped)"`

---

## Self-Review: Spec coverage check

| Spec requirement | Task that covers it |
|---|---|
| Candidate E formula: DLLM with trend-removed h̃_layer and x̃ | Task 3 (`fit_dllm_one_layer`) |
| Candidate F formula: two-regime IHM + per-layer $\beta$_k | Task 3 (`fit_ihm_f_one_layer`) |
| Trend-removal of all three streams consistently | Tasks 1 + 4 (`trend_remove_series`) |
| `h_c` = min raw GWL in calibration window, not fitted | Task 1 (`prepare_gwl_inputs_layers`) |
| GWL aligned to InSAR 5-day epoch grid | Task 1 (`align_gwl_to_insar_epochs`) |
| Layer-to-GWL assignment by depth range (direct lookup) | Task 1 (`assign_gwl_to_layers`) |
| 4-fold walk-forward; fold-1 = 2022 drought year separated | Task 2 (`make_fold_masks`) |
| Pre-declared D-vs-E decision rule before hold-out inspection | Task 5 |
| 24 proxy-GWL stations handled by nearest-station lookup | Tasks 1 + 6 (`find_nearest_gwl_station`) |
| Pilot 2 inflation check; upgrade to 3-nearest IDW if > 1.5$\times$ | Task 6 exit criterion |
| Exit criterion: fold-1 within 1.5$\times$ of folds-2-4 at Pilot 3 | Task 7 |
| Calibration table: one row per (station, layer) + per-fold RMSE | Task 7 output CSV |
| Lag sensitivity table for DLLM | Task 5 (`lag_sensitivity_F2.csv`) |
| `S_skv / S_ske` sanity check at clay-rich layers | Task 5 exit criteria |
| Column-total consistency check `α(s)·x ≈ ΣŶ_layer` | Post-prediction diagnostic; user applies separately |

---

## Implementation checklist — before writing any code

Before starting Task 1, verify:

- [ ] **Feather files readable:** `python -c "import pandas as pd; df = pd.read_feather(r'...\TUKU_gwl_timeseries.feather'); print(df.shape)"` — expect (9497, 3) or similar.
- [ ] **Layer-grouped files exist:** Confirm `data/mlcw/group_byLayer_reconstr/TUKU_reconst_grouped.csv` and `TUKU_classify_table.csv` are present.
- [ ] **All data paths confirmed accessible** (see Key data paths table above).
- [ ] **Conda environment:** `conda run -n fafalab python -c "import numpy, pandas, scipy, pyarrow; print('OK')"` returns OK.
- [ ] **Output folders:** Created at runtime by each pilot script — no manual prep.

---

## File inventory

| Item | Path | Status |
|---|---|---|
| GWL feather files | `data\gwl\well_timeseries\{STATION}_gwl_timeseries.feather` | ✓ 100 files |
| GWL metadata | `data\gwl\well_info\gwl_allwells_flat.csv` | ✓ 306 rows |
| MLCW layer-grouped (reconstructed) | `data\mlcw\group_byLayer_reconstr\{STATION}_reconst_grouped.csv` | ✓ 37 files |
| MLCW classify table | `data\mlcw\group_byLayer_reconstr\{STATION}_classify_table.csv` | ✓ 37 files |
| InSAR at MLCW stations | `data\insar\timeseries\mlcw_interp_insar_IDW_extend.feather` | ✓ 39 stations |
| GWL linkage report | `data\gwl\inspection_reports\gwl_linkage_report.csv` | ✓ 306 rows |
| BME hydrofacies | `data\hydrofacies\mlcw_hydrofacies_5m.csv` | ✓ |
| $\alpha$ prior | `data\alpha\alpha_comparison_all_stations_v3.csv` | ✓ 39 stations |
| Stage 1 library | `D:\112_PROJECT_002\src\loader.py` etc. | ✓ |

All paths are under `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\` unless noted otherwise.

---

## Next steps

**Plan complete and saved to `D:\112_PROJECT_002\plans\2026-05-20-implementation-plan.md`.**

This plan supersedes `2026-05-19-candidate-E-F-implementation.md` for the layer-grouped pipeline. The original plan's decisions documented in `discussion_20260520.md` §3–5 (feather files, proxy station fallback, trend-removal approach) all carry forward. Only the MLCW input representation, GWL assignment logic, and output dimensionality have changed.

Two execution options:

**1. Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks.

**2. Inline Execution** — use `superpowers:executing-plans` skill, batch with checkpoints.
