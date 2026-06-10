# AGENTS.md — InSAR-MLCW Land Subsidence Research

## Two-repo architecture

This repo (`20260427_InSAR_MLCW_v2`) holds **all data, pipeline scripts, and active modeling code** (merged from `D:\112_PROJECT_002` on 2026-06-05). All imports use `from paths import ...` — see CLAUDE.md Path Reference section.

```python
import sys; sys.path.insert(0, r'D:\112_PROJECT_002')
from src.gwl_loader import ...
```

The VS Code workspace (`20260427_InSAR_MLCW_v2.code-workspace`) links this repo + `appsigsolv` (at `../20260501_timeseries_signal_solver/`, a separate git repo).

## Active development — IHM-F v3 (GWL-driven compaction model)

Primary method under exploration is **IHM-F v3** (joint constrained inversion, GWL-only drivers). V1/v2 are superseded. IHM-F v3 model lives at `scripts/10_ihmf/`:

- `fit_ihm_f_v3.py` — entry point: reads `data/ihmf_config.json`, fits per (station, layer), outputs to `results/ihmf/v3/`
- `ihmf_model_v3.py` — core: `build_regime_mask()`, `remove_seasonal_cycle()`, `tau_grid_search_per_layer()`, `joint_solve_fixed_tau()`, `run_walk_forward_v3()`
- `ihmf_io_multilayer.py` — data loading (MLCW grouped CSVs, GWL feather, multi-layer assembly) — **active loader for v3**
- `ihmf_io.py` — single-layer loader (v1/v2 only; do not import in v3 scripts)
- `ihmf_detrend.py` — shared detrending (used by v3 for walk-forward + diagnostic pipelines)
- `ihmf_plots.py` — diagnostics

4-fold walk-forward: fold-1 (2022) is the operational stress test — MLCW reconstructed, no raw data that year. Exit criterion: fold-1 median RMSE $\le$ 1.5$\times$ folds 2–4 median.

**Commands:**
```powershell
# Run IHM-F v3 single station (TUKU pilot)
$env:PYTHONPATH=""; conda run -n fafalab2 python scripts/10_ihmf/fit_ihm_f_v3.py --station TUKU --all

# Run IHM-F v3 batch (all 37 stations — only after TUKU pilot passes physical checks)
$env:PYTHONPATH=""; conda run -n fafalab2 python scripts/10_ihmf/fit_ihm_f_v3.py --all

# Run Stage 1 B-vector regression (legacy, D:\112_PROJECT_002)
$env:PYTHONPATH = ""; conda run -n fafalab2 python D:\112_PROJECT_002\main.py

# Run 2S-TOOL (independent git submodule)
conda run -n isce_ncu3 python tools\2S-TOOL-Python\scripts\09_trackB\batch_run_2stool.py
```

## Environment quirks

- **Conda env `fafalab2`** (Python 3.12). Active working environment for all IHM-F and data analysis.
- **`PYTHONPATH` contamination**: `fafalab2` picks up `gemini_env` paths. For `D:\112_PROJECT_002` scripts, run with `$env:PYTHONPATH = ""; conda run -n fafalab2 python <script>`.
- **2S-TOOL** requires `isce_ncu3` env (scipy $\ge$ 1.17) — separate from `fafalab`.
- **Path resolution:** Use `from paths import SCRIPTS_ROOT, DATA_ROOT, RESULTS_ROOT, DOCS_ROOT, resolve` for all new scripts. Legacy scripts may still have hardcoded `D:\...` paths; migrate them via `resolve()` when touched. See CLAUDE.md "Path Resolution Protocol" section for examples.
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
| GWL-to-MLCW layer assignment | CSV | `gwl/gwl_to_mlcw_layer_assignment_v4.csv` (use v4; 195 rows, 2026-06-04 update) |
| MLCW-aligned GWL (189 files) | Feather | `gwl/mlcw_gwl_timeseries/{MLCW}_{GWL}_{WELLCODE}.feather` |
| Hydrofacies | CSV | `hydrofacies/mlcw_hydrofacies_5m.csv` |
| $\alpha$ prior | CSV | `alpha/alpha_comparison_all_stations_v3.csv` |
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
├── 05_modeling/              ARX, Prophet, ablation (static scaling baseline)
├── 06_direct_ratio/          Static f̄_k baseline (comparison floor)
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

24 of 37 stations use nearest-proxy GWL (18 no co-located well + 6 fully-blocked: ERLUN, GUANGFU, KECUO, QIAOYI, XIUTAN, ZHENGMIN). `assign_gwl_to_layers()` matches layers to GWL wells by screen midpoint depth-range lookup. Station count excludes JINHU_XIN and LUNFENG_XIN (no grouped MLCW files).
