# Data Paths — InSAR-MLCW Scripts

> Project: InSAR-MLCW subsidence analysis — GWL-driven methods under exploration.
> Repo root: `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2`.
> Always use `paths.py` constants in Python — never hardcode `D:\...` or `/mnt/hgfs/...`.

## paths.py Exported Constants

```python
from paths import (
    SCRIPTS_ROOT,          # repo root
    DATA_ROOT,             # data/
    RESULTS_ROOT,          # results/
    DOCS_ROOT,             # D:\112_PROJECT_002  (companion repo)
    MLCW_RECONST_DIR,      # data/mlcw/group_byLayer_reconstr/
    MLCW_MODELED_DIR,      # data/mlcw/group_byLayer_modeled/
    GWL_TIMESERIES_DIR,    # data/gwl/mlcw_gwl_timeseries/
    GWL_WELL_INFO,         # data/gwl/well_info/gwl_allwells_flat.csv
    GWL_ASSIGNMENT,        # data/gwl/gwl_to_mlcw_layer_assignment_v4.csv
    INSAR_FEATHER,         # data/insar/timeseries/mlcw_interp_insar_IDW_extend.feather
    IHMF_CONFIG,           # data/ihmf_config.json
    IHMF_RESULTS_DIR,      # results/ihmf/
    DATA_ANALYSIS_DIR,     # results/data_analysis/
    DIRECT_RATIO_DIR,      # results/direct_ratio/
    DISCUSSIONS_DIR,       # DOCS_ROOT/discussions/
    PROGRESS_MD,           # DOCS_ROOT/PROGRESS.md
    resolve,               # resolve(win_path: str) -> Path  [legacy migration]
)
```

Run `python paths.py` from repo root to verify platform detection.

---

## Input Data

### MLCW (Multi-Level Compaction Well)

| `paths.py` constant | Relative path | Description |
|---|---|---|
| `MLCW_RECONST_DIR / f"{S}_reconst_grouped.csv"` | `data/mlcw/group_byLayer_reconstr/{S}_reconst_grouped.csv` | **Primary MLCW input** — cumulative compaction per layer (37 stations) |
| `MLCW_RECONST_DIR / f"{S}_classify_table.csv"` | `data/mlcw/group_byLayer_reconstr/{S}_classify_table.csv` | Ring depth → layer code mapping |
| `MLCW_MODELED_DIR / f"{S}_modeled_grouped.csv"` | `data/mlcw/group_byLayer_modeled/{S}_modeled_grouped.csv` | IHM-F model output |
| *(no constant)* | `data/mlcw/modeled_nojump/detrended/` | Detrended MLCW (39 stations) |
| *(no constant)* | `data/mlcw/modeled_nojump/nojump/` | Jump-corrected MLCW (39 stations) |
| *(no constant)* | `data/mlcw/modeled_nojump/trend_only/` | Trend-only component (39 stations) |

`{S}` = station name (e.g. `TUKU`).

---

### InSAR

| `paths.py` constant | Relative path | Description |
|---|---|---|
| `INSAR_FEATHER` | `data/insar/timeseries/mlcw_interp_insar_IDW_extend.feather` | InSAR at 39 MLCW stations |
| *(no constant)* | `data/insar/timeseries/gridpnt_500m_interp_insar_IDW_extend.feather` | InSAR at 8,577 grid points (500 m grid) |

**Units:** feather values are in **metres**. Multiply by 1000 for mm. Negative = subsidence.

---

### Groundwater Level (GWL)

| `paths.py` constant | Relative path | Description |
|---|---|---|
| `GWL_TIMESERIES_DIR / f"{MLCW}_{GWL}_{WELLCODE}.feather"` | `data/gwl/mlcw_gwl_timeseries/{MLCW}_{GWL}_{WELLCODE}.feather` | MLCW-aligned GWL (189 files) |
| `GWL_ASSIGNMENT` | `data/gwl/gwl_to_mlcw_layer_assignment_v4.csv` | GWL-to-layer join key — **v4 only** (v1/v2/v3 superseded; 13 wellcode fixes applied 2026-06-04) |
| `GWL_WELL_INFO` | `data/gwl/well_info/gwl_allwells_flat.csv` | 306 wells; elevation column: `elev_leveling_m` |
| *(no constant)* | `data/gwl/2stool_outputs/2stool_results_summary.csv` | 2S-TOOL S_kv/S_ke (191 rows, diagnostic only) |

**Wellcode rule:** always 8-digit strings. Never convert to int — leading zeros will be dropped.  
**Elevation rule:** always use `elev_leveling_m`. Not `well_elev_m` or `elev_DEM_m`.

---

### Configuration

| `paths.py` constant | Relative path | Description |
|---|---|---|
| `IHMF_CONFIG` | `data/ihmf_config.json` | 191 entries: station, layer, tau_max, warmstart params |

---

## Results

| `paths.py` constant | Relative path | Description |
|---|---|---|
| `IHMF_RESULTS_DIR / f"{S}_{LAYER}_ihmf_results.json"` | `results/ihmf/{S}_{LAYER}_ihmf_results.json` | IHM-F fit output per station-layer |
| *(no constant)* | `results/ceiling_test/{S}_ceiling_test.csv` | Walk-forward ceiling test results |
| *(no constant)* | `results/seasonal_insar_harmonic/{S}/` | Phase stability, holdout, reconstruction metrics |
| *(no constant)* | `results/ring_cross_correlation/{S}/` | Raw, detrended, grouped, lagged correlation metrics |
| `DIRECT_RATIO_DIR / f"{S}/{S}_direct_ratio_stats.csv"` | `results/direct_ratio/{S}/{S}_direct_ratio_stats.csv` | Static scaling baseline |
| `DATA_ANALYSIS_DIR / "DATA_ANALYSIS_REPORT.md"` | `results/data_analysis/DATA_ANALYSIS_REPORT.md` | 8-diagnostic aggregated report |

`{S}` = station name. `{LAYER}` = F1/F2/F3/F4/T1/T2.

---

## Reference / Docs

| Relative path | Description |
|---|---|
| `docs/s_ske_skv_tables.md` | S_ske wet/dry values (31 stations, 10 cycles) |
| `docs/choushui_skeletal_storage_coeffs.md` | S_ske/S_skv summary by layer |
| `tau_demo_TUKU/results/tau_results.csv` | TUKU pilot tau search results |
| `tau_demo_TUKU/results/reconstruction_metrics.csv` | TUKU pilot reconstruction quality |

---

## Companion Repo Paths (via DOCS_ROOT)

```python
DOCS_ROOT / "PROGRESS.md"                       # Pipeline status (authoritative)
DOCS_ROOT / "discussions" / "discussion_memory.md"  # Work diary
DOCS_ROOT / "CLAUDE.md"                         # Physical constraints + sign conventions
```

Do not commit changes to `DOCS_ROOT` from this repo.
