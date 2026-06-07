# Project Cleanup Report
**Date:** 2026-05-26  
**Cleaned by:** Claude Code (automated + manual review)  
**Project root:** `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2`

This report documents every file and directory moved to `trash/` and explains why each was removed. Files are grouped by category and reason.

---

## Summary

| Category | Items Removed | Reason |
|----------|--------------|--------|
| Headonly test infrastructure | 10 files (1 dir + 1 data dir) | Diagnostic test, superseded by production pipeline |
| Single-station TUKU diagnostic scripts | 2 scripts | Superseded by all-station equivalents |
| LLM-based extraction attempt | 1 script + 43 markdown tables | Method abandoned; direct regex extraction used instead |
| Intermediate / superseded data files | 4 files | Either intermediate steps or superseded final products |
| One-off utility scripts | 2 scripts | One-time column-fix task completed |
| E1 parallel InSAR decompose | 1 script | Superseded by memory-safe E2 version |
| Notebook exploration artefacts | 2 feather files | Scratch data from interactive notebooks |
| Cached/auto-generated (deleted, not moved) | All `__pycache__` + `.ipynb_checkpoints` | Regenerated automatically on next run |
| Previously trashed (pre-2026-05-26) | Multiple | See "Prior cleanup session" section below |

---

## 1. Headonly Test Infrastructure

### `scripts/09_trackB_test/` (3 scripts)
- `batch_run_headonly.py`
- `prepare_2stool_inputs_headonly.py`
- `compare_results.py`

**Reason:** These scripts were written to verify a mathematical invariant — that using raw piezometric head directly (y = −head) produces identical 2S-TOOL storage coefficients S_kv and S_ke as using depth (y = elev − head). The test confirmed the invariant holds. The production pipeline in `scripts/09_trackB/` uses the standard depth-based convention. These test scripts produce no outputs consumed by any downstream pipeline and are not referenced by any production code. The invariant they verified is now documented in project memory.

### `data/gwl_test/` (7 input files + partial outputs)
- `2stool_inputs_headonly/2STOOL_TUKU_{F1,F2,F3,F4,T1,T2}.xlsx`
- `2stool_inputs_headonly/preparation_log.csv`
- `2stool_outputs_headonly/2STOOL_TUKU_F1/` (5 output files)

**Reason:** Test data directory paired with `scripts/09_trackB_test/`. Only TUKU was run as a single-station proof-of-concept. The production 2S-TOOL inputs and outputs reside in `data/gwl/2stool_inputs/` (195 files) and `data/gwl/2stool_outputs/` (131 completed stations). The headonly test data has no role in the production pipeline.

---

## 2. Single-Station TUKU Diagnostic Scripts

### `scripts/07_analysis/wetdry_diagnostic_TUKU.py`

**Reason:** Single-station prototype for the wet/dry seasonal split analysis at TUKU. The script's docstring explicitly states it was "Refactored from" to produce `wetdry_allstations.py`, which is the production all-station equivalent. All results from the all-station run are in `results/wetdry/`. Running the TUKU-only version no longer produces any new information.

### `scripts/07_analysis/optionB_harmonic_TUKU.py`

**Reason:** Single-station prototype for the Option B harmonic decomposition at TUKU. Same situation as `wetdry_diagnostic_TUKU.py` — it was the development prototype; the production script is `harmonic_allstations.py`. Results for all 39 stations are already computed and saved in `results/`. The single-station prototype is redundant.

---

## 3. LLM-Based Well Info Extraction (Abandoned Approach)

### `scripts/04_gwl_processing/extract_well_info_deepseek.py`

**Reason:** An early attempt to extract structured well metadata (depth, screen intervals) from the WRA Yearbook PDF using the DeepSeek LLM API. The approach was abandoned after it produced unreliable output with hallucinated values in some cells. The production approach (`extract_well_info_direct.py`) uses direct regex parsing of the PDF text, which proved more reliable. This script has no production role.

### `data/gwl/well_info/well_info_output/` (47 files: 43 markdown tables + 1 rar + 3 test files)
- `Well_Info_2024_page_001_table.md` through `Well_Info_2024_page_043_table.md`
- `well_info_output.rar`
- `test_deepseek_page_001_table.md`, `test_deepseek_v2_page_001_table.md`, `test_deepseek_v2_page_002_table.md`

**Reason:** Intermediate OCR/LLM extraction tables produced during development of the well-info ingestion workflow. The authoritative well metadata is now in `gwl_allwells_flat.csv` (cross-checked against the WRA 2024 yearbook on 2026-05-26 and corrected). These raw extraction tables are superseded artifacts of the extraction pipeline development and are not consumed by any script.

### `data/gwl/well_info/well_info_deepseek/` (43 markdown tables — same content, different location)

**Reason:** Duplicate of the DeepSeek extraction tables stored in a different sub-directory. Same provenance and same redundancy as `well_info_output/`. The canonical well data is in `gwl_allwells_flat.csv`.

---

## 4. Intermediate / Superseded Data Files

### `data/gwl/well_info/gwl_allwells_flat_corrected.csv`

**Reason:** Intermediate output of `correct_gwl_wellinfo.py` (2026-05-26). This was the corrected CSV before being copied over the production file. Once the correction was applied to `gwl_allwells_flat.csv` (the canonical file), this intermediate copy became redundant. The backup `gwl_allwells_flat_BACKUP_20260526.csv` (retained in `data/gwl/well_info/`) provides the rollback point if needed.

### `data/gwl/well_info/gwl_allwells_flat_updated.xlsx`

**Reason:** The source Excel file that added `elev_leveling_m` and `elev_DEM_m` columns (2026-05-26). Its content was ingested by `fix_and_export.py` and the result written to `gwl_allwells_flat.csv`. The xlsx is the upstream input that was already processed; the production CSV is the output. No script reads this xlsx directly; retaining it would create confusion about which file is authoritative.

### `data/gwl/well_info/well_info_temp.rar`

**Reason:** Temporary archive file (`_temp` suffix) created during the well info extraction workflow. Contents are OCR extraction intermediates. No script references this archive; all useful data was already incorporated into the production CSV.

### `data/gwl/well_info_combined.gpkg` and `well_info_combined_screenAvail.gpkg`

**Note:** These are v1 and v2 of the GIS GeoPackage for well locations. The production version is `well_info_combined_screenAvail_v3.gpkg`. The v1 and v2 files are superseded.

---

## 5. One-Off Utility Scripts

### `fix_and_export.py` (root-level)

**Reason:** A one-time script written to fix truncated column names in `gwl_allwells_flat_updated.xlsx` (the 10-character Excel field-name truncation artefact: `well_scree` → `well_screen_str`, etc.) and export the result as the canonical CSV. The task was completed on 2026-05-26. Column names in `gwl_allwells_flat.csv` are now correct. There is no reason to rerun this script; if the column fix were ever needed again it could be reconstructed from the corrections log.

---

## 6. Superseded InSAR Decomposition Script

### `scripts/01_insar_preprocessing/E1_insar_asc_desc_decompose_parallel.py`

**Reason:** The E1 script decomposes ascending + descending InSAR LOS into vertical and east-west components using Python multiprocessing. It was superseded by `E2_insar_asc_desc_decompose_optimized.py`, which uses a serial tile-patching approach. The reason for the replacement (documented in E2's header): HDF5 is not concurrent-write-safe, and multiprocessing multiplies RAM usage 3–9× on the 786-date × 2674 × 2053 dataset, frequently causing OOM errors. E2's serial approach is slower but memory-safe and produces identical output. E1 is retained here for reference only.

---

## 7. Notebook Exploration Artefacts

### `scripts/notebooks/YIWU_09190112.feather` and `YIWU_09190122.feather`

**Reason:** Feather files for the YIWU station wells, created as scratch data during interactive Jupyter notebook sessions (`20260519_prepare_gwl_data.ipynb`). These are not part of the production data pipeline. Production well timeseries for all stations reside in `data/gwl/well_timeseries/` (100 feather files, one per wellcode). The YIWU production feather files there are `data/gwl/well_timeseries/YIWU_gwl_timeseries.feather`; these notebook-level copies are redundant intermediate artefacts.

---

## 8. Auto-Generated Cache (Deleted Outright, Not Moved)

These were deleted entirely rather than moved to trash, as they are regenerated automatically on the next Python import or Jupyter open:

### `__pycache__/` directories (6 removed)
- `D:\...\__pycache__\`
- `scripts/04_gwl_processing/__pycache__/`
- `scripts/05_pairing/__pycache__/`
- `scripts/09_trackB/__pycache__/`
- `scripts/notebooks/__pycache__/`
- `tools/2S-TOOL-Python/twostool_python/__pycache__/`

**Reason:** Python bytecode caches (`.pyc` files). Automatically regenerated when any `.py` file is imported. Contain no information that is not derivable from the source files.

### `.ipynb_checkpoints/` directories (2 removed)
- Root-level `.ipynb_checkpoints/`
- `scripts/notebooks/.ipynb_checkpoints/`

**Reason:** Jupyter auto-saves. Not part of the project; regenerated automatically when notebooks are reopened.

---

## 9. Empty 2S-TOOL Output Directories (Deleted Outright)

These three directories existed but contained zero files — they were created by a batch run where 2S-TOOL failed to converge or had insufficient data for those station-layer combinations:

- `data/gwl/2stool_outputs/2STOOL_JIANYANG_F3/`
- `data/gwl/2stool_outputs/2STOOL_JIAXING_F4/`
- `data/gwl/2stool_outputs/2STOOL_XINXING_F4/`

**Reason:** No outputs were ever written. Empty directories provide no value and could mislead future scripts into thinking a result exists.

---

## 10. Prior Cleanup Session (Pre-2026-05-26)

The following items were already in `trash/` from a reorganization performed on 2026-05-19 (documented in `REORGANIZATION_COMPLETE.md`). They are retained in trash pending final deletion review:

| Path in trash | Original location | Reason |
|---------------|------------------|--------|
| `archive/execute_reorganization.py` | root | One-off reorganization helper script; task complete |
| `archive/generate_path_mapping.py` | root | Generated `path_mapping.json`; task complete |
| `archive/mlcw_5m_regular_2015/` (40 CSVs) | `data/mlcw/regular_5m/` old location | Superseded by regularised grid at new canonical path |
| `archive/v1_rar_snapshots/*.rar` (6 files) | Various | Version 1 snapshots of alpha, batch_process, GPS, MLCW, and plot scripts |
| `data/gwl/gwl_material_summary.csv` | `data/gwl/` | Intermediate material summary; superseded by final assignment |
| `data/gwl/inspection_reports/archive/` (2 files) | `data/gwl/inspection_reports/` | Outdated inspection report versions |
| `data/gwl/inspection_reports/gwl_inspection_report_v1.json` | `data/gwl/inspection_reports/` | v1 superseded by v2 |
| `data/mlcw/decomposed/v1.rar` and `v2.rar` | `data/mlcw/decomposed/` | v1 and v2 snapshots; production uses v3 |
| `data/mlcw/regular_5m/fix_old_colnames.rar` | `data/mlcw/regular_5m/` | One-off column fix archive |
| `presentation/dataset_overview_v1.tex` and `v2.*` | `presentation/` | Draft presentation files; v2 LaTeX build artefacts |
| `results/direct_ratio_tuku/v1/` (4 files) | `results/direct_ratio_tuku/` | v1 results superseded by production direct_ratio run |
| `scripts/01_insar_preprocessing/D1_insar_remove_dates.py` | `scripts/01_insar_preprocessing/` | One-off date-removal preprocessing; task complete |
| `scripts/06_direct_ratio/direct_ratio_tuku.py` | `scripts/06_direct_ratio/` | Original TUKU-only direct ratio prototype; superseded by `direct_ratio_allstations.py` |

---

## Files Intentionally Retained (Not Trashed)

The following files were considered during review but explicitly kept:

| File | Reason to keep |
|------|---------------|
| `gwl_allwells_flat_BACKUP_20260526.csv` | Intentional rollback point; field-verified values (e.g., TUKU screen strings) are documented in it |
| `gwl_allwells_flat.xlsx` | Canonical production well metadata in Excel format for GIS review |
| `scripts/01_insar_preprocessing/E2_insar_asc_desc_decompose_optimized.py` | Active production script |
| `scripts/04_gwl_processing/extract_well_info_direct.py` | Active production extraction method |
| All `scripts/07_analysis/*_allstations.py` | Production all-station equivalents of the trashed TUKU prototypes |
| `path_mapping.json` | Reference for any future path migration |
| `discussion_20260519_v3.md`, `discussion_memory.md` | Project history and decision context |
| `REORGANIZATION_COMPLETE.md` | Documents the 2026-05-19 reorganization |
| All `data/gwl/2stool_inputs/` and `data/gwl/2stool_outputs/` | Production 2S-TOOL data |
| All `data/gwl/well_timeseries/*.feather` (100 files) | Production GWL timeseries |
| All `data/mlcw/` CSVs | Production MLCW data |

---

## 11. Post-Cleanup Audit (2026-05-26, second pass)

An automated audit was conducted after the initial cleanup to verify trash integrity and identify items missed or created afterward. Three explore agents checked scripts, data, and root-level directories independently.

### 11a. Trash Integrity — Path Preservation Issues

Several items were moved to trash without preserving their original subdirectory structure (flattened paths). This does not affect functionality but makes it harder to trace provenance:

| Original Path | Actual Trash Path | Issue |
|---------------|------------------|-------|
| `scripts/07_analysis/wetdry_diagnostic_TUKU.py` | `trash/scripts/wetdry_diagnostic_TUKU.py` | Missing `07_analysis/` subdir |
| `scripts/07_analysis/optionB_harmonic_TUKU.py` | `trash/scripts/optionB_harmonic_TUKU.py` | Missing `07_analysis/` subdir |
| `scripts/04_gwl_processing/extract_well_info_deepseek.py` | `trash/scripts/extract_well_info_deepseek.py` | Missing `04_gwl_processing/` subdir |
| `data/gwl/well_info/gwl_allwells_flat_corrected.csv` | `trash/data/gwl_allwells_flat_corrected.csv` | Missing `well_info/` subdir |
| `data/gwl/well_info/gwl_allwells_flat_updated.xlsx` | `trash/data/gwl_allwells_flat_updated.xlsx` | Missing `well_info/` subdir |
| `data/gwl/well_info/well_info_temp.rar` | `trash/data/well_info_temp.rar` | Missing `gwl/well_info/` subdir |
| `data/gwl/well_info/well_info_output/` (47 files) | `trash/data/well_info_output/` | Missing `gwl/well_info/` prefix |
| `scripts/notebooks/YIWU_09190112.feather` | `trash/data/YIWU_09190112.feather` | Category mismatch (scripts→data) |
| `scripts/notebooks/YIWU_09190122.feather` | `trash/data/YIWU_09190122.feather` | Category mismatch (scripts→data) |

These are cosmetic only — no data loss or functional impact.

### 11b. Items Missed During Initial Cleanup

The following items remain in the project tree and are eligible for cleanup based on the same criteria used in Sections 1–7:

| Item | Size | Reason for Cleanup | Report Section Analogue |
|------|------|-------------------|------------------------|
| `data/gwl/well_info_combined_screenAvail_v2.gpkg` | 152 KB | Superseded by v3; v1 already trashed | Section 4 |
| `data/gwl/2stool_test.rar` | 6.4 MB | Test archive, no production role | Section 4 |
| `data/gwl/mlcw_gwl_timeseries/figs.rar` | 21 MB | Figures archive, not consumed by any pipeline | Section 4 |
| `data/gwl/temp/gwl_well_checkElev_v2.*` (8 files) | ~500 KB | v2 shapefiles superseded by v3 equivalents | Section 4 |
| `data/gwl/temp/well_info_combined_screenAvail_v2.*` (7 files) | ~443 KB | v2 shapefiles superseded by v3 equivalents | Section 4 |
| `scripts/fill_well_screen_str.py` | 7.5 KB | One-time utility analogous to `fix_and_export.py` | Section 5 |
| `presentation/dataset_overview.aux` | 4.5 KB | v1 LaTeX build artifact; v2 equivalents already trashed | Section 10 |
| `presentation/dataset_overview.log` | 46 KB | v1 LaTeX build artifact | Section 10 |
| `presentation/dataset_overview.nav` | 3.0 KB | v1 LaTeX build artifact | Section 10 |
| `presentation/dataset_overview.out` | 1.0 KB | v1 LaTeX build artifact | Section 10 |
| `presentation/dataset_overview.snm` | 0 B | v1 LaTeX build artifact | Section 10 |
| `presentation/dataset_overview.toc` | 512 B | v1 LaTeX build artifact | Section 10 |
| `presentation/dataset_overview.txt` | 20 KB | v1 LaTeX build artifact | Section 10 |
| `results/batch_run_log.txt` | 119 KB | Operational artifact, not consumed by any pipeline | (new) |
| `results/data_readiness_check.txt` | 2.5 KB | Operational artifact, not consumed by any pipeline | (new) |
| `.firecrawl/` | 1.3 MB | Tool-generated web-scrape cache (2S-TOOL docs) | (new) |

Total recoverable space: ~31 MB.

### 11c. Empty Directories Left Behind

These directories had their contents moved to trash but the now-empty container directories remain:

| Empty Directory | Notes |
|----------------|-------|
| `data/gwl/well_info/well_info_output/` | 47 files moved to `trash/data/well_info_output/` |
| `data/gwl/2stool_outputs/` | Contained zero files — analogous to the 3 empty dirs in Section 9 (already deleted) |

### 11d. Stale Documentation Reference

`scripts/all_my_scripts.md` (19 KB, 192 lines) is a developer documentation index listing every script with descriptions. It references **6 scripts that are now in trash**:

| Trashed Script | all_my_scripts.md Line |
|----------------|----------------------|
| `D1_insar_remove_dates.py` | 24 |
| `E1_insar_asc_desc_decompose_parallel.py` | 33 |
| `extract_well_info_deepseek.py` | 84 |
| `direct_ratio_tuku.py` | 131 |
| `optionB_harmonic_TUKU.py` | 150 |
| `wetdry_diagnostic_TUKU.py` | 165 |

Two production scripts also contain docstring references to now-trashed files:
- `scripts/07_analysis/harmonic_allstations.py` (line 5): mentions `optionB_harmonic_TUKU.py`
- `scripts/07_analysis/wetdry_allstations.py` (line 4): mentions `wetdry_diagnostic_TUKU.py`

These are cosmetic stale-comment issues.

### 11e. Post-Audit File Modification

One file in `data/` was modified after the cleanup report timestamp:
- **`data/gwl/well_info/gwl_allwells_flat.csv`** (2026-05-26 18:43, 54 min after report) — re-exported after a well-screen-str fill attempt that confirmed 105 empty rows have no source data in the PDF markdown tables.

No other files in `scripts/`, `data/`, or the project root were modified after the cleanup.

---

## Summary of Recommended Follow-Up Actions

1. **Move 17 additional items to trash** (~31 MB) — see Section 11b.
2. **Delete 2 empty directories** — `data/gwl/well_info/well_info_output/` and `data/gwl/2stool_outputs/`.
3. **Update `scripts/all_my_scripts.md`** — remove or annotate 6 references to trashed scripts.
4. **Fix 2 docstring references** — optional cosmetic fix in `harmonic_allstations.py` and `wetdry_allstations.py`.

---

*Initial report generated 2026-05-26 17:49. Post-cleanup audit conducted 2026-05-26 by three automated explore agents.*
