# Independent Third-Party Inspection Report

**Date:** 2026-05-25  
**Inspector:** Independent AI Inspector  
**Scope:** Planning files (`.md`), Python scripts (`.py`), and selected input data files in both `D:\112_PROJECT_002` and `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2`

---

## Executive Summary

The project has produced thorough, well-documented planning and extensive data preparation work for the Track B DLLM/IHM pipeline. Two previous inspections (`inspection_v1.md`, `inspection_v2.md`) correctly flagged the gap between planning documents and executable model-fitting code. This inspection confirms that gap but provides a more nuanced assessment: the project is **not stalled** — substantial parallel work has been done on data infrastructure (2S-TOOL pipeline, GWL-MLCW pairing, pre-aligned feather files) that previous inspections overlooked entirely. The missing piece is specifically the four modules called for in Task 1–7 of the implementation plan.

---

## 1. The Planning-to-Code Gap (Confirmed)

Both previous inspections correctly identify the core problem, though with overstated severity. The following files from the `2026-05-20-implementation-plan.md` do **not exist**:

| Missing File | Purpose |
|---|---|
| `D:\112_PROJECT_002\src\gwl_loader.py` | GWL feather read, epoch alignment, layer assignment, trend removal |
| `D:\112_PROJECT_002\src\validation.py` | 4-fold walk-forward masks, RMSE table |
| `D:\112_PROJECT_002\src\track_b_models.py` | `fit_dllm_one_layer()`, `fit_ihm_f_one_layer()`, predictors |
| `D:\112_PROJECT_002\pilot1_tuku.py` | TUKU single-station DLLM + IHM diagnostic |
| `D:\112_PROJECT_002\pilot2_no_gwl_station.py` | Xizhou proxy-GWL inflation check |
| `D:\112_PROJECT_002\pilot3_allstations.py` | Batch fit all 37 stations |

These are the **only** files blocking Pilot 1 execution. They are well-specified (200+ lines of function signatures and verification steps in the plan) and should take 1–2 focused sessions to implement.

---

## 2. What Previous Inspections Overlooked

Both v1 and v2 claimed "code execution has entirely stalled" and that "the data wrangling phase was highly successful" — but neither inspected the following substantial work products in `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\scripts\09_trackB\`:

### 2.1 2S-TOOL Pipeline (195 input files $\times$ 6 TUKU layers already processed)

Three scripts with **919 total lines** are already operational:

- **`prepare_2stool_inputs.py`** (427 lines) — Reads MLCW layer-grouped CSVs and GWL feather files, aligns them, computes GWL depth from well elevation minus head, and writes Excel workbooks with StrainStress sheets. Supports `--raw` (aggregate raw ring data) and `--monthly` (resample to first-of-month) flags. Has already produced **195 Excel input files** covering all station-layer combinations.

- **`batch_run_2stool.py`** (144 lines) — Batch-runs the 2S-TOOL Python analysis pipeline. The `2S-TOOL-Python` package now lives at `tools/2S-TOOL-Python/` within the project (independent git repo → github.com/david-ncu2019/twostoolspy).

- **`collect_2stool_results.py`** (348 lines) — Aggregates results from JSON (preferred), CSV, or Excel fallback. Has already collected results for **TUKU all 6 layers** (F1, F2, F3, F4, T1, T2), with storage coefficients:
  - F3: $S_{kv}$ = **0.086** (dominant inelastic compaction zone — clay-rich, as expected)
  - F2: $S_{kv}$ = **0.031**
  - F4: $S_{kv}$ = **0.0095**
  - T2: $S_{kv}$ = **0.0052**
  - F1: $S_{kv}$ = **0.0045**
  - T1: $S_{kv}$ = **0.0028**

  The TUKU F3 $S_{kv}$ = 0.086 vs S_ke_weighted = 0.0015 gives an **$S_{kv}$ / $S_{ke}$ ~57$\times$**, which confirms the physically expected order-of-magnitude contrast for clay-rich inelastic sediments. This strongly supports the two-regime IHM structure (Candidate F) at TUKU.

### 2.2 Pre-Aligned MLCW-GWL Timeseries (37 feather files)

The notebook `scripts/notebooks/prepare_gwl_timeseries_match_mlcw.py` (147 lines) has already produced **37 pre-aligned feather files** at `data/gwl/mlcw_gwl_timeseries/{STATION}_{PROXY}.feather`. These are InSAR-epoch-aligned GWL timeseries for each MLCW station paired with its assigned GWL proxy station. The v1 inspection correctly identified this as a shortcut — `gwl_loader.py` could skip the alignment step and read these pre-built files directly.

### 2.3 Spatial GWL-MLCW Pairing (39 stations, GeoPandas)

`scripts/05_pairing/build_mlcw_insar_gwl_pairs.py` (305 lines) computed the nearest GWL station for each MLCW station using spatial joins (EPSG:32650 → EPSG:3826 reprojection). Outputs:
- `data/mlcw/MLCW_InSAR_GWL_pairs.xlsx` — main pairing table with distances and feather stem names
- `data/mlcw/MLCW_InSAR_GWL_pairs_all.csv` — expanded table with all GWL stations within 5 km

Distance summary: min 0 m (co-located), max >2000 m for some stations. This is directly reusable by the plan's `find_nearest_gwl_station()`.

### 2.4 GWL-to-MLCW Layer Assignment (195 rows, complete)

`data/gwl/gwl_to_mlcw_layer_assignment.csv` already contains the complete mapping: 196 rows covering 37 stations $\times$ layers, with columns for `assigned_wellcode`, `screen_top_m`, `screen_bot_m`, `screen_mid_m`, `assignment_method` (DIRECT_MATCH or NEAREST_FALLBACK), and `feather_file` path. This is **production-ready** and could be read directly by `gwl_loader.py` instead of recomputing assignments at runtime.

### 2.5 GWL Linkage Diagnostic

`data/gwl/inspection_reports/gwl_linkage_summary.txt` documents 120/306 wells (39.2%) missing screen depths, including **26 MLCW-overlap wells** across 12 stations, of which **6 stations are fully blocked** (ERLUN, GUANGFU, KECUO, QIAOYI, XIUTAN, ZHENGMIN). These 6 are correctly redirected to nearest-proxy GWL, giving **24 total proxy stations** (18 no-GWL + 6 fully-blocked).

---

## 3. Methodological Observations

### 3.1 Track A (`main.py`) Should Not Be Archived

Previous inspections recommended archiving `main.py` and related files. This is not recommended. The Stage 1 regularised B-vector inversion solves a different question (estimating a single B(depth) profile from the full InSAR-MLCW joint dataset) and remains useful for:

1. **Cross-validation of Track B:** Comparing the Track B per-layer compaction predictions against the Stage 1 regularised estimate at each depth provides an independent sanity check.
2. **Sensitivity analysis:** The existing three $\mu$ variants (0.00, 0.10, 1.00) explore $\alpha$-prior strength, which is a physically meaningful diagnostic.
3. **Publication record:** The Stage 1 results are a completed analysis that may appear in the paper as context or supplementary material.

Recommendation: Re-classify as "diagnostic/legacy" in documentation, not "deprecated/archived."

### 3.2 Track B Implementation Can Use Pre-Computed Tables

The plan's `gwl_loader.py` specifies `assign_gwl_to_layers()` which would recompute nearest-well assignments at runtime. Since `gwl_to_mlcw_layer_assignment.csv` and the `mlcw_gwl_timeseries/*.feather` files already contain the aligned, assigned data, the module could be simplified to:

1. Read `gwl_to_mlcw_layer_assignment.csv` for the station-layer-well mapping
2. Read the corresponding `mlcw_gwl_timeseries/{STATION}_{PROXY}.feather` file for aligned timeseries
3. Apply `trend_remove_series` using calibration window mask

This shortcut would reduce runtime complexity and eliminate a source of bugs (duplicated assignment logic).

### 3.3 The Estimation-versus-Validation Distinction

The plan's `fit_ihm_f_one_layer()` estimates $S_{ske}$ and $S_{skv}$ by OLS (design matrix with regime-dependent columns). The 2S-TOOL pipeline estimates these same parameters from stress-strain curves using a completely independent method (loop identification in displacement-vs-head space). This creates a **built-in cross-validation opportunity** that is rare in applied geophysics: two independent methods estimating the same physical parameters from the same data, each with different assumptions. If they agree, the results are publication-grade.

Current status: Only TUKU's 6 layers have been processed through 2S-TOOL. The remaining 36 stations $\times$ ~6 layers $\approx$ 216 layers are queued as inputs (195 Excel files exist) but not yet run through the 2S-TOOL solver.

### 3.4 Decision Rule Outcome Is Prefigured

The 2S-TOOL results for TUKU show that **all 6 layers have accepted elastic loops** (11–21 per layer), confirming that the two-regime IHM structure is physically supported at TUKU. The pre-declared D-vs-E decision rule (count fraction of calibration-window epochs with raw head $\le$ $h_{c}$) should be computed from the GWL record once Pilot 1 runs. Based on 2S-TOOL evidence, Candidate F (IHM-F) is likely to be selected.

---

## 4. Concrete Issues Found

### 4.1 Stale `CLAUDE.md` in Data Scripts Repository

`D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\CLAUDE.md` still references:
- Pre-reorganization paths (`MLCW_5m_regular/`, `InSAR_timeries/`, `direct_ratio_MLCW_InSAR/`)
- The pipeline as a sequential scripts/01–08 structure with no reference to Track B, layer-grouped pipeline, or the DLLM/IHM candidates
- No mention of the 09_trackB directory or 2S-TOOL work

The `GEMINI.md` file in the same directory may have similar stale content. **Action:** Update these to reflect the current dual-repository structure (data prep in scripts repo, model fitting in 112 repo).

### 4.2 `AGENTS.md` Path Mismatch

`AGENTS.md` says "All new code goes under `D:\112_PROJECT_02\`" (note: missing the trailing `0` — should be `D:\112_PROJECT_002`). This is a typo that could cause import errors during development.

### 4.3 Conflicting Conda Environment Manifests

As noted in `AGENTS.md`: two YAML files at root (`environment.yml` targeting Python 3.12, `fafalab_env.yml` targeting Python 3.10). The installed environment is 3.10. If the 3.12 environment is activated by mistake, compatibility issues may surface with `h5py`, `pyarrow`, or `scipy` versions.

### 4.4 `PYTHONPATH` Contamination

The `fafalab` environment picks up `gemini_env` paths. Affected GWL-related scripts should set `$env:PYTHONPATH = ""` before `conda run -n fafalab python <script.py>`.

### 4.5 Pre-Aligned MLCW-GWL Feather Files Have Inconsistent Date Ranges

`prepare_gwl_timeseries_match_mlcw.py` aligns GWL to InSAR master dates using nearest-day matching. The resulting feather files may have varying total points depending on GWL data availability per station. The `gwl_loader.py` must handle this by checking alignment coverage and logging warnings where gaps exceed thresholds.

### 4.6 Redundant Station Lists

- CLAUDE.md says "37 layer-grouped stations" (JINHU_XIN, LUNFENG_XIN excluded)
- gwl_to_mlcw_layer_assignment.csv has 195 rows across 37 stations
- The original 39-station InSAR feather still has all 39 stations
- `scripts/09_trackB/prepare_2stool_inputs.py` processes all stations in the assignment file (37)
- `MLCW_InSAR_GWL_pairs.xlsx` has 39 rows

The inconsistency between 37 and 39 is expected (JINHU_XIN, LUNFENG_XIN exist in InSAR/GWL but lack grouped MLCW), but `MLCW_InSAR_GWL_pairs.xlsx` lists 39 stations including JINHU_XIN and LUNFENG_XIN without noting that these two cannot be used for layer-based modeling. The pairing table should either exclude them or flag them as MLCW-absent.

---

## 5. The 2S-TOOL Results Grid

| Layer | $S_{kv}$ | S_ke_weighted | $S_{kv}$/$S_{ke}$ | Accepted Loops | Verdict |
|---|---|---|---|---|---|
| TUKU F1 | 0.00445 | 0.00038 | 11.7$\times$ | 16/22 | Moderate inelastic |
| TUKU F2 | 0.03148 | 0.00176 | 17.9$\times$ | 18/22 | Strong inelastic |
| **TUKU F3** | **0.08605** | **0.00149** | **57.7$\times$** | **15/20** | **Dominant inelastic (clay-rich aquifer)** |
| TUKU F4 | 0.00947 | 0.00022 | 43.0$\times$ | 13/18 | Strong inelastic (deep) |
| TUKU T1 | 0.00276 | 0.00032 | 8.6$\times$ | 11/23 | Moderate inelastic |
| TUKU T2 | 0.00520 | 0.00058 | 9.0$\times$ | 21/28 | Moderate inelastic |

**Physical interpretation:** TUKU F3 (depth ~173–273 m) has $S_{kv}$ / $S_{ke}$ = 57.7, confirming this clay-rich aquifer unit is the primary source of irreversible compaction. The 2S-TOOL results provide independent physical validation that will strengthen the IHM parameter estimates once Pilot 1 runs.

---

## 6. Recommendations in Priority Order

1. **Implement the four missing modules** (`gwl_loader.py`, `validation.py`, `track_b_models.py`, `pilot1_tuku.py`) using the pre-computed `gwl_to_mlcw_layer_assignment.csv` and `mlcw_gwl_timeseries/*.feather` files as shortcuts. This is the critical path — nothing else blocks.

2. **Run Pilot 1 at TUKU** to evaluate the pre-declared D-vs-E decision rule and compare IHM-fitted $S_{ske}$/$S_{skv}$ against the 2S-TOOL reference values (currently available for all 6 TUKU layers).

3. **Update `CLAUDE.md` in both repositories** to reflect the dual-repo structure and Track B prioritisation.

4. **Complete the remaining 2S-TOOL batch** (~216 station-layer combinations) for independent parameter validation. Run on the Linux environment where the 2S-TOOL Python solver is installed.

5. **Fix the `AGENTS.md` path typo** (`D:\112_PROJECT_02\` → `D:\112_PROJECT_002\`).

6. **Document the environment quirks** (PYTHONPATH contamination, conflicting YAML manifests, git ignore of .py files) in a single accessible location rather than buried in AGENTS.md.

---

## 7. Summary

| Aspect | Finding |
|---|---|
| **Code deltas to production** | 6 files missing (3 modules + 3 pilot scripts) |
| **Data readiness** | Complete — all inputs on disk, 2S-TOOL partial runs done |
| **Planning quality** | High — well-specified function signatures, verification steps |
| **Previous inspections** | Correct on the gap; missed substantial parallel work (2S-TOOL pipeline, pre-aligned feather files, GeoPandas pairing) |
| **Critical path** | Implementing gwl_loader → track_b_models → pilot1_tuku |
| **Estimated effort** | 1–2 focused coding sessions for the missing modules |

---

## Update: 2026-05-27

The following claims in this report are now stale. They are corrected here; the original text above is left unchanged for the inspection record.

**Section 2.1 — 2S-TOOL pipeline status.**  
OLD: "Has already produced 195 Excel input files... NOT yet run through the 2S-TOOL solver" (implied by "Only TUKU's 6 layers have been processed" in Section 3.3).  
CORRECT: The 2S-TOOL batch was completed on 2026-05-27. All 195 station-layer combinations were processed using updated inputs (see below). Results: **126 OK, 56 NEG_SKV, 13 ERROR**. Summary table at `data/gwl/2stool_outputs/2stool_results_summary.csv` (182 rows); loop-level detail at `2stool_loops_all.csv` (3,732 rows).

**Section 2.2 — Pre-aligned feather file count and naming.**  
OLD: "37 pre-aligned feather files at `mlcw_gwl_timeseries/{STATION}_{PROXY}.feather`".  
CORRECT: **189 feather files** at `data/gwl/mlcw_gwl_timeseries/`, naming pattern `{MLCW_STATION}_{GWL_STATION}_{WELLCODE}.feather`. Each file has 264 rows (aligned to MLCW `_orig_grouped.csv` timeline) and 2 columns: `datetime` + `{MLCW_STATION}_{GWL_STATION}_{WELLCODE}` (piezometric head in m above MSL). The `prepare_2stool_inputs.py` script was updated to read from this directory and from `gwl_to_mlcw_layer_assignment_v3.csv`; GWL depth conversion now uses `elev_leveling_m` from `gwl_allwells_flat.csv`.

**Section 3.3 — Remaining 2S-TOOL batch.**  
OLD: "Only TUKU's 6 layers have been processed through 2S-TOOL. The remaining 36 stations $\times$ ~6 layers $\approx$ 216 layers are queued as inputs (195 Excel files exist) but not yet run through the 2S-TOOL solver."  
CORRECT: All 195 layers have now been processed. The batch used `group_byLayer_orig` (raw-summed MLCW) rather than the reconstructed `group_byLayer_reconstr` CSVs used in the prior TUKU-only run. This input change produced systematically lower $S_{kv}$ estimates at most TUKU layers and a sign flip at TUKU F4 (NEG_SKV).

**Section 5 — TUKU 2S-TOOL results table.**  
The $S_{kv}$ values in Section 5 (F1=0.00445, F2=0.03148, F3=0.08605, F4=0.00947, T1=0.00276, T2=0.00520) are from the **prior run using reconstructed `group_byLayer_reconstr` data**. The new run using raw-summed `group_byLayer_orig` gives: F1=0.00572, F2=0.02984, F3=0.05551, F4=−0.05720 (NEG_SKV), T1=0.00685, T2=ERROR. The discrepancy is explained by elastic recovery oscillations in the raw-summed signal compressing the inelastic slope estimate used by 2S-TOOL. TUKU F4's sign flip is a data-source artifact, not a physical result. Before IHM-F parameter fitting begins, a decision is required on which MLCW source is canonical for 2S-TOOL.

For full analysis of the new results, see `discussion_20260527_2stool_rerun.md`.
