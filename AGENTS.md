# AGENTS.md — InSAR-MLCW Land Subsidence Research

## Two-repo architecture

This repo (`20260427_InSAR_MLCW_v2`) holds **data and pipeline scripts**. All active modeling code lives in `D:\112_PROJECT_002`. Import pattern:

```python
import sys; sys.path.insert(0, r'D:\112_PROJECT_002')
from src.gwl_loader import ...
```

The VS Code workspace (`20260427_InSAR_MLCW_v2.code-workspace`) links this repo + `appsigsolv` (at `../20260501_timeseries_signal_solver/`, a separate git repo).

## Active development — Track B / IHM-F

Production method is **IHM-F** (two-regime IHM with per-layer β_k). DLLM is retired. IHM-F model lives at `scripts/10_ihmf/`:

- `fit_ihm_f.py` — entry point: reads `data/ihmf_config.json`, fits per (station, layer)
- `ihmf_model.py` — core: `prepare_signals()`, `fit_one_tau()`, `grid_search_tau()`, `run_walk_forward()`
- `ihmf_io.py` — data loading (MLCW grouped CSVs, GWL feather, 2S-TOOL warmstarts)
- `ihmf_plots.py` — diagnostics

4-fold walk-forward: fold-1 (2022) is the operational stress test — MLCW reconstructed, no raw data that year. Exit criterion: fold-1 median RMSE ≤ 1.5× folds 2–4 median.

**Commands:**
```powershell
# Run IHM-F (all stations/layers from config)
conda run -n fafalab python scripts\10_ihmf\fit_ihm_f.py

# Run Stage 1 B-vector regression (legacy, D:\112_PROJECT_002)
$env:PYTHONPATH = ""; conda run -n fafalab python D:\112_PROJECT_002\main.py

# Run 2S-TOOL (independent git submodule)
conda run -n isce_ncu3 python tools\2S-TOOL-Python\scripts\09_trackB\batch_run_2stool.py
```

## Environment quirks

- **Conda env `fafalab`** (Python 3.10). Two conflicting YAMLs at parent root: `environment.yml` (3.12), `fafalab_env.yml` (3.10). Installed is 3.10.
- **`PYTHONPATH` contamination**: `fafalab` picks up `gemini_env` paths. For `D:\112_PROJECT_002` scripts, run with `$env:PYTHONPATH = ""; conda run -n fafalab python <script>`.
- **2S-TOOL** requires `isce_ncu3` env (scipy ≥1.17) — separate from `fafalab`.
- **All paths** hardcoded Windows absolute (`D:\...`). Portability needs find-and-replace.
- **No tests, no CI, no linters.** Research pipeline. Verify by inspecting output CSVs/PNGs.

## Key conventions

- **Sign**: positive = compaction (subsidence). InSAR negated on load.
- **Reference date**: `2015-01-16` — baseline epoch for all cumulative displacements.
- **Temporal grid**: 1st, 6th, 11th, 16th, 21st, 26th of each month (6 epochs/month).
- **GWL well codes**: 8-digit strings with leading zeros. Converting to int drops leading zeros and breaks feather column lookups.
- **Well elevation**: use `elev_leveling_m` from `gwl_allwells_flat.csv` for head-to-depth. NOT `well_elev_m` or `elev_DEM_m`.
- **Trend removal**: linear trend fitted on calibration window, applied identically to GWL, MLCW, and InSAR.

## Data layout (under `data/`)

| Data | Format | Path |
|------|--------|------|
| MLCW layer-grouped (input) | CSV | `mlcw/group_byLayer_reconstr/{STATION}_reconst_grouped.csv` (37 files) |
| MLCW layer classification | CSV | `mlcw/group_byLayer_reconstr/{STATION}_classify_table.csv` |
| MLCW layer-grouped (model output) | CSV | `mlcw/group_byLayer_modeled/{STATION}_modeled_grouped.csv` |
| InSAR at MLCW stations | Feather | `insar/timeseries/mlcw_interp_insar_IDW_extend.feather` |
| InSAR at 500m grid | Feather | `insar/timeseries/gridpnt_500m_interp_insar_IDW_extend.feather` |
| GWL timeseries (100 files) | Feather | `gwl/well_timeseries/{STATION}_gwl_timeseries.feather` |
| GWL metadata (306 wells) | CSV | `gwl/well_info/gwl_allwells_flat.csv` |
| GWL-to-MLCW layer assignment | CSV | `gwl/gwl_to_mlcw_layer_assignment_v3.csv` (use v3) |
| MLCW-aligned GWL (189 files) | Feather | `gwl/mlcw_gwl_timeseries/{MLCW}_{GWL}_{WELLCODE}.feather` |
| Hydrofacies | CSV | `hydrofacies/mlcw_hydrofacies_5m.csv` |
| α prior | CSV | `alpha/alpha_comparison_all_stations_v3.csv` |
| 2S-TOOL results | CSV | `gwl/2stool_outputs/2stool_results_summary.csv` |
| IHM-F config (all stations/layers) | JSON | `ihmf_config.json` |

JINHU_XIN and LUNFENG_XIN have no grouped files — excluded.

## Pipeline scripts (sequential stages)

```
scripts/
├── 01_insar_preprocessing/   Adaptive OMT, LOS decomposition, kriging/IDW
├── 02_mlcw_processing/       MLCW decomposition (appsigsolv), reconstruction, 5m grid
├── 03_gps_processing/        GPS vertical decomposition
├── 04_gwl_processing/        Feather extraction, layer assignment, linkage inspection
├── 05_modeling/              ARX, Prophet, ablation (Track A)
├── 06_direct_ratio/          Static f̄_k baseline (Track A floor)
├── 07_analysis/              Validation, harmonic/wetdry diagnostics
├── 08_visualization/         Publication plots, data inspection
├── 09_trackB/                2S-TOOL batch run + results collection
├── 10_ihmf/                  IHM-F fitting (active production model)
└── notebooks/                Jupyter data prep
```

## Git state

- **This repo now has its own `.git`** (initialized 2026-05-28). `.gitignore` tracks only `.py`, `.ipynb`, `.md`; excludes `.csv`, `.xls`, `.xlsx`.
- **Parent `D:\1000_SCRIPTS`** is also a git repo (ignores everything except `.ipynb`). Commits from here go to parent unless this repo's git is targeted.
- **`appsigsolv`** (`../20260501_timeseries_signal_solver/`) is a standalone git repo with its own remote.
- **`tools/2S-TOOL-Python/`** is an independent git repo (`origin → github.com/david-ncu2019/twostoolspy.git`). Push/pull independently.

## GWL proxy notes

24 of 37 stations use nearest-proxy GWL (18 no co-located well + 6 fully-blocked: ERLUN, GUANGFU, KECUO, QIAOYI, XIUTAN, ZHENGMIN). `assign_gwl_to_layers()` matches layers to GWL wells by screen midpoint depth-range lookup. Four stations need explicit wellcode overrides: DONGSHI→10090111, TUKU→09030211, XIGANG→07240213, ZHUTANG→07250111.
