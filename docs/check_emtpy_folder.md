# Empty Folder Report

**Directory:** `/mnt/hgfs/1000_SCRIPTS/004_Project003/20260427_InSAR_MLCW_v2`  
**Date checked:** 2026-05-19

## Empty Directories Found: 0

No empty directories remain. All previous empty directories (`GPS_data/`, `scripts_2026_Apr_May/`, `output_figs/.ipynb_checkpoints/`) have been removed.

------

# Reorganization Gap Analysis — Current State vs Proposal (Round 2)

**Date checked:** 2026-05-19 (after user cleanup)  
**Proposal reference:** `reorganize_project_folder.md`

## Changes Since Previous Check

| Status | Item |
|---|---|
| Fixed | `GPS_data/` — deleted |
| Fixed | `gwl_inspection/` — deleted, contents merged into `data/gwl/` |
| Fixed | `studyarea_SHP/` — deleted, shapefile components moved to `gis/study_area/` |
| Fixed | `scripts_2026_Apr_May/` — deleted |
| Fixed | All empty directories cleared |

## Remaining Issues

### 1. RAR Archives Outside `archive/`

4 RAR files remain scattered in data directories. Per the proposal, all RAR snapshots should live in `archive/v1_rar_snapshots/`.

| # | Current Location | Action |
|---|---|---|
| 1 | `data/mlcw/decomposed/v1.rar` | Move to `archive/v1_rar_snapshots/` |
| 2 | `data/mlcw/decomposed/v2.rar` | Move to `archive/v1_rar_snapshots/` |
| 3 | `data/mlcw/regular_5m/fix_old_colnames.rar` | Move to `archive/v1_rar_snapshots/` |
| 4 | `data/gwl/well_info/well_info_output/well_info_output.rar` | Move to `archive/v1_rar_snapshots/` |

### 2. `results/arx/` — Flat Instead of Nested

Per-station CSVs (78 files) are flat at `results/arx/` level. The proposal shows them in a `per_station/` subfolder.

**Current:**
```
results/arx/
├── ANHE_arx_params.csv
├── ANHE_arx_walkforward_rmse.csv
├── ... (78 per-station CSVs)
├── ablation/
└── figures/
```

**Proposed:**
```
results/arx/
├── per_station/          # ← 78 CSVs go here
├── ablation/
└── figures/
```

**Action:** Create `results/arx/per_station/` and move all `{STATION}_arx_*.csv` files into it.

### 3. `__pycache__/` at Top Level

Contains 3 cached bytecode files:
- `batch_reconstruct_MLCW.cpython-312.pyc`
- `compare_reconstructions_per_ring.cpython-312.pyc`
- `validate_all_stations.cpython-310.pyc`

**Action:** Delete `__pycache__/` and add `__pycache__/` to `.gitignore`.

### 4. Transition/Meta Files at Top Level

| File | Recommendation |
|---|---|
| `execute_reorganization.py` | Delete (one-time use script) |
| `generate_path_mapping.py` | Delete |
| `path_mapping.json` | Delete |
| `REORGANIZATION_COMPLETE.md` | Delete or move to `docs/` |
| `reorganization_log.txt` | Delete or move to `docs/` |
| `reorganize_project_folder.md` | Keep or move to `docs/` |

### 5. Missing Proposal Directories (Low Priority)

These directories from the proposal don't exist, but the source files may never have existed either.

| Missing Directory | Explanation |
|---|---|
| `archive/direct_ratio_tuku_v1/` | v1 files may not exist separately from v2 |
| `archive/output_figs_v1/` | Old figure versions may not exist |
| `results/validation_summary/` | Validation summaries live in `results/direct_ratio/` per-station dirs; no central copy was created |

## Summary — Remaining Actions

| Priority | Action |
|---|---|
| High | Move 4 RARs from `data/` to `archive/v1_rar_snapshots/` |
| High | Delete `__pycache__/` and gitignore it |
| Medium | Create `results/arx/per_station/`, move 78 CSVs into it |
| Low | Delete 5 transition files at top level |
| Low | Create missing archive dirs if source files exist |
