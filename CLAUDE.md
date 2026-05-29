# CLAUDE.md — InSAR-MLCW Scripts Repository

> **Read first:** The authoritative project context lives at `D:\112_PROJECT_002` (Windows) or `/mnt/hgfs/112_PROJECT_002` (Ubuntu VM).
> Before working here, read `PROGRESS.md` (current status) and `discussions/discussion_memory.md` (work diary).
> The research objectives, physical constraints, and sign conventions in `D:\112_PROJECT_002\CLAUDE.md` apply in full.

## Path Reference (Windows host ↔ Ubuntu VM)

| Logical name | Windows (host) | Linux / Ubuntu VM (VMware HGFS) |
|---|---|---|
| This repo (scripts/data) | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2` | `/mnt/hgfs/1000_SCRIPTS/004_Project003/20260427_InSAR_MLCW_v2` |
| Docs root | `D:\112_PROJECT_002` | `/mnt/hgfs/112_PROJECT_002` |
| Runtime path resolver | `paths.py` (repo root) | `paths.py` (repo root) |
| IHM-F fit script | `scripts\10_ihmf\fit_ihm_f.py` | `scripts/10_ihmf/fit_ihm_f.py` |
| Data root | `data\` | `data/` |
| Results root | `results\` | `results/` |

> **Claude agents:** Use the path form for your OS. In Python, `from paths import SCRIPTS_ROOT` resolves automatically — no manual translation needed.

---

## Repository Purpose

This repo (`D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2`) holds all
**pipeline scripts, raw data, and results** for the InSAR-MLCW subsidence analysis.
Documentation, plans, and discussion files live in `D:\112_PROJECT_002`. The two
repos are linked: IHM-F fitting code lives here under `scripts/10_ihmf/`; any
shared src modules (e.g. future `src/gwl_loader.py`) are imported from
`D:\112_PROJECT_002` via `sys.path.insert`.

---

## Environment Setup

```powershell
# Always reset PYTHONPATH to prevent gemini_env contamination:
$env:PYTHONPATH = ""; conda run -n fafalab python <script.py>
```

- **`fafalab`** (Python 3.10) — all active analysis: IHM-F, direct ratio, data analysis
- **`isce_ncu3`** (scipy >= 1.17) — 2S-TOOL only (`tools/2S-TOOL-Python/`)
- Two environment YAMLs exist at the parent root: `environment.yml` (3.12, stale) and
  `fafalab_env.yml` (3.10, current). Installed is 3.10.

---

## Key Run Commands

```powershell
# IHM-F fit — single station, all layers:
$env:PYTHONPATH = ""; conda run -n fafalab python scripts/10_ihmf/fit_ihm_f.py --station TUKU --all

# IHM-F fit — single station, single layer:
$env:PYTHONPATH = ""; conda run -n fafalab python scripts/10_ihmf/fit_ihm_f.py --station TUKU --layer F2

# Data analysis — run all 8 diagnostics in order:
$env:PYTHONPATH = ""; conda run -n fafalab python scripts/11_data_analysis/analyze_correlations.py
$env:PYTHONPATH = ""; conda run -n fafalab python scripts/11_data_analysis/analyze_collinearity.py
$env:PYTHONPATH = ""; conda run -n fafalab python scripts/11_data_analysis/analyze_lagged_correlation.py
$env:PYTHONPATH = ""; conda run -n fafalab python scripts/11_data_analysis/analyze_layer_patterns.py
$env:PYTHONPATH = ""; conda run -n fafalab python scripts/11_data_analysis/analyze_proxy_quality.py
$env:PYTHONPATH = ""; conda run -n fafalab python scripts/11_data_analysis/analyze_regimes.py
$env:PYTHONPATH = ""; conda run -n fafalab python scripts/11_data_analysis/analyze_signal_decomposition.py
$env:PYTHONPATH = ""; conda run -n fafalab python scripts/11_data_analysis/summarize_for_redesign.py

# 2S-TOOL batch run (isce_ncu3 env):
conda run -n isce_ncu3 python scripts/09_trackB/batch_run_2stool.py
conda run -n isce_ncu3 python scripts/09_trackB/collect_2stool_results.py
```

---

## Active Script Inventory

```
scripts/
├── 10_ihmf/              IHM-F model fitting (production Track B model)
│   ├── fit_ihm_f.py      Orchestrator: reads ihmf_config.json, routes by path, writes JSON + PNG
│   ├── ihmf_model.py     Core: prepare_signals, fit_one_tau[_bk], grid_search_tau, run_walk_forward
│   ├── ihmf_io.py        Data loader: aligns MLCW CSV + GWL feather + InSAR via merge_asof
│   └── ihmf_plots.py     Figures: 3-panel raw-fit + 3-panel reconstruction (150 dpi PNG)
│
├── 11_data_analysis/     8 diagnostic scripts (collinearity, lag, coupling, signal decomposition)
│   └── summarize_for_redesign.py  Aggregates all diagnostics → DATA_ANALYSIS_REPORT.md
│
├── 09_trackB/            2S-TOOL batch run + results collection
├── 06_direct_ratio/      Static f̄_k baseline (Track A floor)
├── 07_analysis/          Cross-validation, harmonic/wet-dry diagnostics (legacy)
├── 08_visualization/     Publication plots and data inspection
├── 01_insar_preprocessing/  Adaptive OMT, LOS decomposition, IDW/kriging
├── 02_mlcw_processing/   MLCW decomposition (appsigsolv), 5m reconstruction
├── 03_gps_processing/    GPS vertical decomposition
├── 04_gwl_processing/    GWL feather extraction and layer assignment
├── 05_modeling/          ARX, Prophet, ablation (Track A comparison)
└── notebooks/            Jupyter data prep and plotting
```

Legacy folders `05_pairing/` contain completed one-off scripts and are not re-run.

---

## Key Data Paths

| File / Folder | Description |
|---------------|-------------|
| `data/ihmf_config.json` | 191 entries: station, layer, tau_max, warmstart_skv/ske, gwl_feather, etc. |
| `data/mlcw/group_byLayer_reconstr/{STATION}_reconst_grouped.csv` | Primary MLCW input: datetime + F1/T1/F2/T2/F3/F4 columns (37 stations) |
| `data/mlcw/group_byLayer_reconstr/{STATION}_classify_table.csv` | Ring-to-layer classification: depth (m) → layer code |
| `data/mlcw/group_byLayer_modeled/{STATION}_modeled_grouped.csv` | IHM-F output (written by fit_ihm_f.py; not an input) |
| `data/insar/timeseries/mlcw_interp_insar_IDW_extend.feather` | InSAR at 39 MLCW stations: 39 rows × 791 cols (785 epochs) |
| `data/insar/timeseries/gridpnt_500m_interp_insar_IDW_extend.feather` | InSAR at 8,577 grid points |
| `data/gwl/mlcw_gwl_timeseries/{MLCW}_{GWL}_{WELLCODE}.feather` | MLCW-timeline-aligned GWL (189 files) |
| `data/gwl/gwl_to_mlcw_layer_assignment_v3.csv` | GWL-to-layer join key — use v3, not v1/v2 |
| `data/gwl/well_info/gwl_allwells_flat.csv` | 306 wells; use `elev_leveling_m` for head-to-depth conversion |
| `data/gwl/2stool_outputs/2stool_results_summary.csv` | 2S-TOOL results: S_kv, S_ke per layer (191 rows) |
| `results/ihmf/{STATION}_{LAYER}_ihmf_results.json` | IHM-F fit output per layer (current run) |
| `results/ihmf/run001/` | Old unconstrained OLS results (kept for comparison only) |
| `results/direct_ratio/{STATION}/{STATION}_direct_ratio_stats.csv` | Track A static ratio baseline (f_median per depth) |
| `results/data_analysis/` | 8 CSV/JSON diagnostic outputs + DATA_ANALYSIS_REPORT.md |

---

## Current Pipeline Status

| Stage | Status |
|-------|--------|
| MLCW preprocessing (decompose, reconstruct, 5m regularisation) | Complete |
| MLCW layer aggregation (ring → F1/T1/F2/T2/F3/F4) | Complete — 37 stations |
| GWL-to-MLCW layer assignment | Complete — 191 pairs |
| GWL timeseries extraction (MLCW-timeline-aligned) | Complete — 189 feather files |
| 2S-TOOL pipeline (S_kv, S_ke reference values) | Complete — 134 OK, 57 NEG_SKV |
| Direct ratio baseline (Track A f̄_k) | Complete — comparison floor |
| Data analysis (collinearity, lag, coupling diagnostics) | Complete — 8 scripts, 191 layers |
| IHM-F implementation (4 modules in scripts/10_ihmf/) | Complete |
| IHM-F Pilot 1 — TUKU all 6 layers | Complete — all non-negative |
| **Detrending module (`ihmf_detrend.py`)** | **Pending — blocking decision** |
| **TUKU re-pilot with detrending** | **Pending — after detrend module** |
| **IHM-F batch run — all 191 entries** | **Blocked — detrend decision required** |
| Walk-forward comparison (Track B vs Track A floor) | Pending — after batch run |
| Stage 2 spatial extension (kriging) | Pending — contingent on batch run |

---

## Sign Conventions

| Signal | Units | Convention |
|--------|-------|------------|
| `y_raw` (MLCW) | mm | negative = compaction |
| `dh_raw` = H(t) − H(t_ref) | m MSL | negative = head fell (drought); **never negate** |
| `x_raw` (InSAR) | mm | negative = subsidence |
| S_ske, S_skv, β | mm/m or dimensionless | always ≥ 0 (physically enforced) |

---

## Known Issues / Gotchas

- **PYTHONPATH contamination:** `gemini_env` packages leak into `fafalab` if PYTHONPATH is
  set. Always prefix with `$env:PYTHONPATH = ""`.
- **b_k = 0 at F1 and F3 (TUKU):** GWL is collinear with InSAR at these layers
  (corr(ΔH, x) = 0.66 raw, drops to 0.19 after detrending). Not a bug — the solver
  correctly assigns credit to β·x. These layers should be labelled
  "InSAR-dominated, GWL unresolvable" until the detrending module resolves this.
- **Detrending module not yet implemented:** `ihmf_detrend.py` is the next required
  module. Batch run is blocked until TUKU re-pilot with detrending confirms the
  collinearity issue is resolved (target: VIF < 5 for all layers).
- **F2 b_k at upper bound (TUKU):** b_k = 72.5 m = full classified F2 span. The true
  compressible thickness may slightly exceed the classified extent. Accepted as the
  best physically-bounded estimate.
- **GWL wellcodes are 8-digit strings:** Never convert to int — leading zeros are dropped,
  breaking feather column lookups.
- **Well elevation:** Use `elev_leveling_m` from `gwl_allwells_flat.csv`. Do not use
  `well_elev_m` (original well record) or `elev_DEM_m` (20m DEM).
- **Layer assignment file:** Use `gwl_to_mlcw_layer_assignment_v3.csv` — earlier
  versions (v1, v2) are superseded.

---

## IHM-F Two-Path Routing

`fit_ihm_f.py` reads `warmstart_skv` and `warmstart_ske` from `data/ihmf_config.json`
and routes each (station, layer) pair:

| Condition | Path | Free parameters |
|-----------|------|-----------------|
| skv > 0 AND ske > 0 (134 layers) | A — b_k model | b_k, β (S fixed at 2S-TOOL values) |
| skv ≤ 0 OR ske ≤ 0 (57 layers) | B — bounded OLS | S_ske, S_skv, β (all ≥ 0) |

Walk-forward validation: 4 folds (2022 / 2023 / 2024 / 2025 hold-outs).
Fold 1 (train 2015–2021, test 2022) is the operational stress test — 2022 MLCW is
reconstructed, no raw sensor data that year.

---

## Git State

- **This repo** has its own `.git` (initialized 2026-05-28). `.gitignore` tracks only
  `.py`, `.ipynb`, `.md`; excludes `.csv`, `.xls`, `.xlsx`.
- **`tools/2S-TOOL-Python/`** is an independent git repo
  (`origin → github.com/david-ncu2019/twostoolspy.git`). Push/pull independently.
- **`appsigsolv`** (`../20260501_timeseries_signal_solver/`) is a separate git repo.
- **Parent `D:\1000_SCRIPTS`** is also a git repo — commits from here target this
  repo's `.git`, not the parent.
