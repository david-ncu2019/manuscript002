# My Dataset Summary
**Project:** InSAR–MLCW Subsidence Analysis, Choushui River Alluvial Fan  
**Last updated:** 2026-05-27 (full directory re-verified; corrected stale paths — `gwl_to_mlcw_layer_assignment.csv` replaced by `_v3.csv`, `inspection_reports/` folder absent, `regular_5m_2015/` absent, `2stool_inputs/` contains TUKU-only, `2stool_outputs/` contains ANHE_F1 + TUKU×6 only; added `group_byLayer_modeled` and `group_byLayer_orig` descriptions; added GPS data section)  
**Working directory:** `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\`

---

## Part 1 — What Data I Have (Current Inventory)

### 1.1 MLCW — Subsurface Compaction at Depth

**What it is:** Per-depth compaction time series at 39 monitoring stations. Each depth level records cumulative ring-by-ring compaction at 5 m intervals from 0 to 300 m.

**Dimensions:** 39 stations × 61 depth columns × up to ~1,572 epochs (dates vary per station)

| Folder / File | Description |
|---|---|
| `data/mlcw/raw_timeseries/{STATION}_ringbyring.csv` | Raw magnetic ring measurements (original format, ~264 rows at monthly field-campaign dates). Values in whole mm (rounded). 24–25 ring depth columns. Reference epoch at t₀ = 0. |
| `data/mlcw/modeled/{STATION}_ringbyring.csv` | Decomposed and modelled ring-by-ring time series at the same ~264 field-campaign dates. Values are floating-point (model-fitted, not rounded). Same depth columns as raw_timeseries. `date` column (not `datetime`). |
| `data/mlcw/decomposed/{STATION}_ringbyring/` | Per-station subfolder. Each subfolder contains per-ring decomposition outputs (CSV + PNG + JSON + MD reports). 39 station subfolders, ~88 files per station. |
| `data/mlcw/reconstructed/{STATION}_ringbyring_reconstructed.csv` | Reconstructed (gap-filled) ring-by-ring compaction time series at original (irregular) ring depths. ~1,572 rows (5-day cadence, 2003–2025). |
| `data/mlcw/regular_5m/{STATION}_5m_grid.csv` | **Primary analysis file.** Regular 5 m depth grid, all gaps filled. Columns: `datetime`, `depth_000m` … `depth_300m` (61 columns). 39 files. |
| `data/mlcw/MLCW_InSAR_GWL_pairs.xlsx` | MLCW stations paired with nearest GWL *station* (39 rows, 2 sheets). Sheet 1 (39 × 17): `Ename`, `Code`, `gwl_feather_stem`, `gwl_station_name_zh`, `gwl_n_wells`, `gwl_well_ids`, `gwl_screen_raw_all`, `dist_to_nearest_gwl_m`, `n_gwl_stations_5km`, etc. Sheet 2 (79 rows × 10 cols): all GWL stations within 5 km, expanded one row per pair. Produced by `scripts/05_pairing/build_mlcw_insar_gwl_pairs.py`. |
| `data/mlcw/MLCW_InSAR_GWL_pairs_all.csv` | Expanded version — all GWL stations within 5 km of each MLCW station (79 rows × 10 columns). Columns: `Code`, `Ename`, `gwl_feather_stem`, `gwl_station_name_zh`, `n_wells`, `well_ids`, `screen_raw_all`, `x_twd97`, `y_twd97`, `dist_to_gwl_m`. Same content as Sheet 2 of the XLSX. |
| `data/mlcw/MLCW_data_timeline.csv` | Station metadata: 39 rows × 6 columns (`Ename`, `long`, `lat`, `start_date`, `end_date`, `duration`, `num_of_obs`). |
| `data/mlcw/MLCW_GPS_pairs.csv` | Nearest GPS station per MLCW station (39 rows × 5 columns). |
| `data/mlcw/MLCW_GPS_pairs.xlsx` | Same content as CSV in Excel format. |
| `data/mlcw/mlcw_hydrofacies_5m.csv` | Regional BME stratigraphy at MLCW stations — see §1.4. |
| `data/mlcw/extract_group_byLayer_orig.txt` | Python script excerpt documenting how `group_byLayer_orig` was produced from the HDF5 source. |

**Table preview — `{STATION}_5m_grid.csv` (primary analysis file, example: TUKU):**  
~700 rows × 62 columns (`datetime` + 61 depth columns, `depth_000m` to `depth_300m`). Values are cumulative compaction in mm (negative = compaction / subsidence).

| datetime | depth_000m | depth_005m | depth_010m | depth_015m | depth_020m | ... | depth_295m | depth_300m |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2003-12-06 | 1.068 | 0.012 | -0.062 | 0.953 | 0.681 | ... | -1.664 | -1.445 |
| 2003-12-11 | 1.049 | 0.013 | -0.060 | 0.937 | 0.669 | ... | -1.654 | -1.404 |
| 2003-12-16 | 1.030 | 0.017 | -0.054 | 0.922 | 0.658 | ... | -1.644 | -1.362 |
| 2003-12-21 | 1.011 | 0.023 | -0.046 | 0.906 | 0.647 | ... | -1.633 | -1.318 |
| 2003-12-26 | 0.990 | 0.031 | -0.035 | 0.891 | 0.636 | ... | -1.621 | -1.273 |

Tail (last 3 rows):

| datetime | depth_000m | depth_005m | depth_010m | ... | depth_295m | depth_300m |
|---|---:|---:|---:|---:|---:|---:|
| 2025-09-21 | -3.541 | -2.973 | -2.806 | ... | -10.145 | -4.224 |
| 2025-09-26 | -3.542 | -2.996 | -2.832 | ... | -10.144 | -4.224 |
| 2025-10-01 | -3.542 | -3.021 | -2.861 | ... | -10.144 | -4.225 |

> Cumulative compaction grows from ~0 mm (2003) to ~-3.5 mm at surface and ~-10 mm at depth by 2025. The `depth_300m` column is always 0.0 (reference anchor at the deepest ring).

**Table preview — `MLCW_data_timeline.csv` (station metadata, 39 rows × 6 columns):**

| Ename | long | lat | start_date | end_date | duration | num_of_obs |
|---|---:|---:|---:|---|---|---:|
| ANHE | 120.31 | 23.52 | 2004-11-23 | 2021-03-18 | 5959 | 197 |
| ANNAN | 120.25 | 23.74 | 2018-11-01 | 2021-11-02 | 1097 | 41 |
| BEICHEN | 120.303 | 23.576 | 2011-03-15 | 2025-10-02 | 5315 | 176 |
| CANLIN | 120.247 | 23.575 | 2008-05-22 | 2021-11-08 | 4918 | 164 |
| DONGGUANG | 120.272 | 23.653 | 2009-10-07 | 2021-11-05 | 4412 | 147 |

> `duration` = days of operation; `num_of_obs` = field campaigns. Stations with `end_date` before 2025 are "shutdown" stations.

**Table preview — `{STATION}_ringbyring_reconstructed.csv` (example: TUKU, ~1,572 rows × 24 columns):**  
Column headers are the physical depth (m) of each magnetic ring. TUKU has 23 rings; other stations vary.

| datetime | 8.775 | 11.938 | 25.605 | 41.577 | 50.306 | ... | 272.728 | 283.383 | 288.7 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2003-12-06 | -0.456 | 1.886 | -0.586 | 0.348 | 1.367 | ... | -8.503 | -2.101 | -3.567 |

> These are gap-filled but still at the original (irregular) ring depths — before interpolation to the uniform 5 m grid.

**Processing pipeline (raw → ready):**
1. Raw ring measurements → `data/mlcw/raw_timeseries/` (input)
2. Decompose into trend + seasonal per ring → `data/mlcw/decomposed/{STATION}_ringbyring/` (per-ring CSV + PNG + JSON + MD; script: `scripts/02_mlcw_processing/batch_process_MLCW.py`)
3. Modelled ring-by-ring output → `data/mlcw/modeled/{STATION}_ringbyring.csv` (floating-point model values at MLCW field-campaign dates)
4. Reconstruct and fill gaps (dense 5-day grid) → `data/mlcw/reconstructed/{STATION}_ringbyring_reconstructed.csv` (script: `scripts/02_mlcw_processing/batch_reconstruct_MLCW.py`)
5. Interpolate to regular 5 m depth grid → `data/mlcw/regular_5m/{STATION}_5m_grid.csv` (script: `scripts/02_mlcw_processing/mlcw_5m_grid.py`)

**Note:** `data/mlcw/regular_5m_2015/` (2015-trimmed version) is NOT present in the current directory. If needed, regenerate with `mlcw_5m_grid.py`.

**Station list (39 total):** ANHE, ANNAN, BEICHEN, CANLIN, DONGGUANG, DONGSHI, ERLUN, FENGAN, FENGRONG, GUANGFU, HAIFENG, HONGLUN, HUNAN, HUWEI, JIANYANG, JIAXING, JINHU\_XIN, JIUZHUANG, KECUO, LONGYAN, LUNFENG\_XIN, NANGUANG, NEILIAO, QIAOYI, TANQIFENXIAO, TUKU, XIGANG, XINGHUA, XINJIE, XINPI, XINSHENG, XINXING, XIUTAN, XIZHOU, YIWU, YUANCHANG, ZHENGMIN, ZHENNAN, ZHUTANG

> **Note:** 20 stations stopped operating after ~2021; 19 stations continue to 2025.

---

### 1.1b Layer-grouped MLCW (three variants)

**What it is:** The MLCW ring-by-ring timeseries aggregated by hydrogeological layer. Instead of 60 imaginary 5-m rings, each station has 4–6 named aquifer/aquitard columns (F1, T1, F2, T2, F3, F4), each equal to the sum of all magnetic ring values assigned to that layer. Three variants exist, derived from different stages of the MLCW processing pipeline.

**Coverage:** 37 stations each (JINHU_XIN and LUNFENG_XIN excluded). Each folder contains `{STATION}_classify_table.csv` (ring-to-layer mapping) + a compaction timeseries file.

| Folder / File | Description | Rows | Cadence | Source data |
|---|---|---|---|---|
| `data/mlcw/group_byLayer_reconstr/{STATION}_reconst_grouped.csv` | Layer-summed from **signal-reconstructed** (gap-filled) ring data. 6 columns (F1, T1, F2, T2, F3, F4). **Primary GWL-driven model calibration input.** | ~1,572 | Dense 5-day grid (2003–2025) | `reconstructed/` |
| `data/mlcw/group_byLayer_modeled/{STATION}_modeled_grouped.csv` | Layer-summed from **decomposed model fit** (trend+seasonal model outputs at MLCW field-campaign dates). 6 columns (F1, T1, F2, T2, F3, F4). Floating-point values. | ~264 | Monthly MLCW field campaigns | `modeled/` (STL decomposition) |
| `data/mlcw/group_byLayer_orig/{STATION}_orig_grouped.csv` | Layer-summed from **raw ring measurements** (integer-rounded, unreconstructed). 7 columns (F1, T1, F2, T2, F3, T3, F4) — note the T3 aquitard column present here but not in the other two variants. **Used as input to 2S-TOOL.** | ~264 | Monthly MLCW field campaigns | `raw_timeseries/` (HDF5) |
| `data/mlcw/group_byLayer_reconstr/{STATION}_classify_table.csv` | Ring-to-layer classification: physical depth (m) → layer code (F1/T1/F2/T2/F3/F4). Derived from borehole logs. Same files exist in all three layer-grouped folders (classify tables are identical). | ~20–30 | — | Borehole logs |

> **Note on file naming:** `group_byLayer_modeled` uses `{STATION}_modeled_grouped.csv`; `group_byLayer_reconstr` uses `{STATION}_reconst_grouped.csv`. The `modeled` variant has ~264 rows (monthly); the `reconstr` variant has ~1,572 rows (5-day).

**Table preview — `{STATION}_reconst_grouped.csv` (example: TUKU in group_byLayer_reconstr, ~1,572 rows × 7 columns):**  
Values are cumulative compaction in mm; negative = subsidence. Layer F2 is the main production aquifer and shows the largest negative values.

| datetime | F1 | T1 | F2 | T2 | F3 | F4 |
|---|---:|---:|---:|---:|---:|---:|
| 2003-12-06 | 0.844 | 0.348 | -11.061 | -2.716 | -33.101 | -5.668 |
| 2003-12-11 | 0.856 | 0.293 | -10.980 | -2.629 | -32.950 | -5.658 |
| 2003-12-16 | 0.876 | 0.231 | -10.927 | -2.556 | -32.798 | -5.646 |
| 2003-12-21 | 0.902 | 0.164 | -10.909 | -2.502 | -32.650 | -5.632 |
| 2003-12-26 | 0.933 | 0.091 | -10.934 | -2.470 | -32.508 | -5.615 |

**Table preview — `{STATION}_classify_table.csv` (example: TUKU, 26 rows × 2 columns):**

| depth | layer |
|---|---|
| 8.775 | F1 |
| 11.938 | F1 |
| 25.605 | F1 |
| 41.577 | T1 |
| 50.306 | F2 |
| 67.395 | F2 |
| 86.914 | F2 |
| 117.442 | F2 |
| 122.818 | F2 |
| 156.590 | T2 |
| 161.876 | T2 |
| 172.889 | F3 |
| ... | ... |
| 283.383 | F4 |
| 288.700 | F4 |
| 294.698 | F4 |
| 300.000 | F4 |

**Layer codes:** F1 = shallow aquifer; T1 = first clay aquitard; F2 = main production aquifer (thickest, most compaction); T2 = second clay aquitard; F3 = deep aquifer; F4 = deepest aquifer. Layer boundaries vary per station.

**Processing steps (added 2026-05-20):**
- Step 4b — Layer aggregation (reconstructed): sum rings per hydrogeological unit → `data/mlcw/group_byLayer_reconstr/` (script: `scripts/notebooks/mlcw_by_group.py`)
  - Input: `data/mlcw/reconstructed/{STATION}_ringbyring_reconstructed.csv` + HDF5 classification (`20251230_MLCW_CRFP_Imputed_v4.h5`)
  - Output: `{STATION}_reconst_grouped.csv` + `{STATION}_classify_table.csv`
  - Excluded stations: JINHU_XIN, LUNFENG_XIN
- Step 4b' — Layer aggregation (raw + modeled): sum raw and decomposed-model rings → `data/mlcw/group_byLayer_orig/` and `data/mlcw/group_byLayer_modeled/`
  - Input: HDF5 source (`20251230_MLCW_CRFP_Imputed_v4.h5`)
  - Script documented in `data/mlcw/extract_group_byLayer_orig.txt`
  - `group_byLayer_orig` used as 2S-TOOL MLCW input (raw-summed, not reconstructed)

---

### 1.1c GWL-to-MLCW Layer Assignment (2026-05-20, revised 2026-05-26)

**What it is:** Mapping of GWL monitoring well screens to MLCW hydrogeological layers (F1/T1/F2/T2/F3/F4) at each of the 37 MLCW stations (21 co-located + 16 nearest-proxy). Each MLCW layer is assigned the GWL well whose screen midpoint best represents the piezometric head driving compaction in that layer.

**Current canonical file:** `data/gwl/gwl_to_mlcw_layer_assignment_v3.csv` (195 rows × 14 columns, 37 stations)  
**Older versions retained for reference:** `data/gwl/gwl_to_mlcw_layer_assignment.xlsx` (v1), `data/gwl/gwl_to_mlcw_layer_assignment_v2.xlsx` (v2)  
**Algorithm guide:** `data/gwl/gwl_to_mlcw_layer_assign_guide.md` (2026-05-26) — explains the overhaul from v2 to v3 (screen-depth-first, 10 km radius search replacing the single-nearest-station approach)

> **Important:** The summary previously referred to `data/gwl/gwl_to_mlcw_layer_assignment.csv` (no version suffix). That file does NOT exist. The canonical file is `gwl_to_mlcw_layer_assignment_v3.csv`. The extraction script (`extract_gwl_timeseries_pair_mlcw.txt`) explicitly references `_v3.csv`.

**Data sources used:**

| Source | Description |
|---|---|
| `data/gwl/well_info/gwl_allwells_flat.csv` | Parsed screen depths (`screen_top_m`, `screen_bot_m`), coordinates, `elev_leveling_m`. 300 wells × 11 columns. **Contains the physical screen boundaries that must be matched to MLCW layers.** |
| `data/mlcw/group_byLayer_reconstr/{STATION}_classify_table.csv` | MLCW ring-to-layer mapping (37 stations). Depth range per layer derived from min/max ring depths. |
| `data/gwl/well_materials/{STATION}.txt` | **BME-derived regional lithostratigraphy** at 95 GWL station locations. **IMPORTANT:** This is NOT the physical screen depth. Physical screen depths come from `gwl_allwells_flat.csv`. |

**Assignment method — v3 algorithm (2026-05-26):**
For every (station, layer) pair, the algorithm searches ALL GWL stations within 10 km, scores every candidate well by depth-match quality, and picks the best — using 2D distance only as a tiebreaker. Prior v2 only searched the single co-located or nearest station.

**Results — 37 stations, 195 layer assignments:**

| Assignment method | Count | Meaning |
|---|---|---|
| DIRECT_MATCH | 66 | Well screen midpoint falls within the layer depth range — physically direct |
| NEAREST_FALLBACK | 129 | No well in range; nearest well by screen midpoint assigned |
| FULLY_BLOCKED | 0 | All formerly-blocked rows resolved via nearest-proxy GWL station |

**Columns of `gwl_to_mlcw_layer_assignment_v3.csv`:**

| Column | Description |
|---|---|
| `station` | MLCW station name |
| `layer` | Hydrogeological layer code (F1/T1/F2/T2/F3/F4) |
| `layer_depth_min_m` | Minimum depth of layer (m below surface) |
| `layer_depth_max_m` | Maximum depth of layer (m below surface) |
| `assigned_wellcode` | 8-digit GWL well code (string — leading zeros preserved) |
| `screen_top_m` | Top of assigned well screen (m below surface) |
| `screen_bot_m` | Bottom of assigned well screen (m below surface) |
| `screen_mid_m` | Screen midpoint depth |
| `screen_str` | Raw screen depth string (e.g., `"72.00~90.00"`) |
| `well_depth_m` | Total drilled depth of assigned well (m) |
| `assignment_method` | `DIRECT_MATCH` or `NEAREST_FALLBACK` |
| `note` | Explanation of assignment decision |
| `feather_file` | Path to source GWL feather file (e.g., `data/gwl/well_timeseries/ANHE_gwl_timeseries.feather`) |
| `dist_to_gwl_m` | Distance (m) from MLCW station to assigned GWL station |

---

### 1.2 InSAR — Total Surface Displacement

**What it is:** Satellite-measured total vertical surface displacement (mm) across the Choushui Fan. Two coverages: at the 39 MLCW locations, and at all 8,577 grid points on a 500 m grid.

**Dimensions:** 8,577 grid points × 785 epochs (2015-01-21 to 2025-12-11); 39 stations × 785 epochs

| File | Description |
|---|---|
| `data/insar/timeseries/mlcw_interp_insar_IDW_extend.feather` | InSAR at the 39 MLCW station locations. 39 rows × 791 columns (6 metadata columns + 785 epoch columns). |
| `data/insar/timeseries/mlcw_interp_insar_IDW_extend.gpkg` | Same data in GeoPackage format (for GIS use) |
| `data/insar/timeseries/gridpnt_500m_interp_insar_IDW_extend.feather` | InSAR at all 8,577 grid points. 8,577 rows × 790 columns. **Used for spatial reconstruction.** |
| `data/insar/timeseries/gridpnt_500m_interp_insar_IDW_extend.gpkg` | Same data in GeoPackage format |
| `data/insar/InSAR_measures_at_MLCW.csv` | Transposed CSV for easy loading. 785 rows (epochs) × 40 columns (date + 39 station columns). |

**Table preview — `InSAR_measures_at_MLCW.csv` (785 rows × 40 columns):**  
First column (unnamed in CSV) is the InSAR acquisition date. Remaining 39 columns are station names. Values are cumulative vertical surface displacement in mm (negative = subsidence).

| date | ANHE | ANNAN | BEICHEN | CANLIN | DONGGUANG | ... | ZHENNAN | ZHUTANG |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2015-03-01 | -0.007 | -0.003 | -0.005 | -0.009 | -0.006 | ... | -0.003 | -0.004 |
| 2015-04-01 | -0.019 | -0.011 | -0.015 | -0.024 | -0.016 | ... | -0.006 | -0.009 |
| 2015-05-01 | -0.035 | -0.023 | -0.027 | -0.040 | -0.029 | ... | -0.008 | -0.016 |

> Load with `pd.read_csv("data/insar/InSAR_measures_at_MLCW.csv", index_col=0, parse_dates=True)`. Sign convention: InSAR data originates as negative for subsidence and is negated on load so positive = subsidence.

**Processing pipeline:** Ascending + descending InSAR frames → LoS decomposition → IDW interpolation to MLCW stations and 500 m grid → feather files. Scripts in `scripts/01_insar_preprocessing/` (A1–K2 series). Key scripts: `E1_insar_asc_desc_decompose_parallel.py` (LOS decomposition), `K2_interp_timeseries_IDW.py` (IDW interpolation), `stage2_idw_compaction.py` (3D compaction field).

---

### 1.3 Groundwater Level (GWL) — Depth-Discrete Piezometric Head

**What it is:** Groundwater level observations from monitoring wells, each screened at a specific depth range in a confined or semi-confined aquifer unit. Because the wells are screened in **confined aquifers** (sandwiched between impermeable clay layers and held under pressure), the water level recorded at each screen is the **piezometric head** in that aquifer unit — not the unconfined water table. "GWL" and "piezometric head" are interchangeable in this dataset. The `data/gwl/well_info/gwl_allwells_flat.csv` is the single consolidated table for all wells with quality statistics and true physical screen depths.

| File | Description |
|---|---|
| `data/gwl/well_info/gwl_allwells_flat.xlsx` | One row per well. **300 wells, 11 columns.** Columns: `station`, `wellcode`, `well_depth_m`, `well_screen_str`, `well_elev_m`, `x_twd97`, `y_twd97`, `screen_top_m`, `screen_bot_m`, `elev_leveling_m`, `elev_DEM_m`. **`elev_leveling_m` is the canonical elevation for head-to-depth conversion** (from 2023 geodetic leveling + Kriging, ±cm). `well_elev_m` retained for reference only. Updated 2026-05-26 (backup: `gwl_allwells_flat_BACKUP_20260526.csv`). |
| `data/gwl/well_info/gwl_allwells_flat.csv` | Same content as the XLSX in CSV format. **Primary join table** for linking feather well codes to coordinates and true physical screen depths. Join key: `wellcode` = feather column name. Use `elev_leveling_m` for all head-to-depth conversions. |
| `data/gwl/well_info/gwl_allwells_flat_BACKUP_20260526.csv` | Backup of gwl_allwells_flat before the 2026-05-26 elevation update. Retained for reference. |
| `data/gwl/well_materials/{STATION}.txt` | **BME-derived regional lithostratigraphy** at 95 GWL station locations. Represents modeled regional aquifer layering within 200 m depth. **IMPORTANT:** These files represent modeled regional aquifer layering, *not* the physical well screen depths. Physical screen depths are found in `gwl_allwells_flat.csv`. 95 .txt + 95 .png = 190 files total. |
| `data/gwl/well_materials/{STATION}.png` | Visual profile plots for each station's BME regional lithostratigraphy (95 files). |
| `data/gwl/well_materials_summary.csv` | Consolidated CSV of all 95 BME TXT files with Chinese→English translation. 345 rows (91 stations). Columns: `station`, `region_model_en`, `x_twd97`, `y_twd97`, `surface_elevation_m`, `total_aquifers_within_200m`, `shows_all_layers`, `layer_number`, `layer_depth_m`, `layer_thickness_m`. Produced by `scripts/04_gwl_processing/consolidate_well_materials.py`. |
| `data/gwl/well_timeseries/{STATION}_gwl_timeseries.feather` | **Per-station GWL timeseries.** 100 files. Each contains a `datetime` column + one float64 column per well (column name = numeric well code). Daily values 2000-01-01 to 2025-12-31 (9,497 rows). GWL in metres elevation (piezometric head). Produced 2026-05-19. |
| `data/gwl/gwl_to_mlcw_layer_assignment_v3.csv` | **Current canonical Assignment Table.** 195 rows × 14 columns. See §1.1c for full column description. Use this file; the unversioned `.csv` no longer exists. |
| `data/gwl/gwl_to_mlcw_layer_assignment.xlsx` | Assignment table v1 (older version, Excel, retained for reference). |
| `data/gwl/gwl_to_mlcw_layer_assignment_v2.xlsx` | Assignment table v2 (intermediate version, Excel, retained for reference). |
| `data/gwl/gwl_to_mlcw_layer_assign_guide.md` | Human-readable guide explaining the v3 overhaul (2026-05-26): screen-depth-first algorithm, 10 km search radius, motivation for change from v2. |
| `data/gwl/extract_gwl_timeseries_pair_mlcw.txt` | Python script excerpt documenting the extraction of 189 per-pair GWL feather files (§1.3c). References `gwl_to_mlcw_layer_assignment_v3.csv`. |
| `data/gwl/well_info_combined_screenAvail_v2.gpkg` | GeoPackage with ~209 wells having available screen data (older version, pre-2026-05-26 elevation update). |
| `data/gwl/well_info_combined_screenAvail_v3.gpkg` | **Updated 2026-05-26.** GeoPackage with same 300 wells as `gwl_allwells_flat.xlsx` — includes `elev_leveling_m` and `elev_DEM_m` columns. Supersedes v2. For GIS visualisation in QGIS / ArcGIS. |
| `data/gwl/Tuku_aquifer_2_sample.csv` | Sample GWL data extract for TUKU aquifer 2 (reference/diagnostic file). |
| `data/gwl/Tuku_aquifer_4_sample.csv` | Sample GWL data extract for TUKU aquifer 4 (reference/diagnostic file). |
| `data/gwl/2stool_test.rar` | Archived 2S-TOOL test files (compressed). |
| `data/gwl/gwl_trash.rar` | Archived deprecated GWL files (compressed). |

> **Note:** The `data/gwl/inspection_reports/` folder (containing `gwl_inspection_report.json`, `gwl_inspection_slim.json`, `gwl_feather_inspection.csv`, `gwl_linkage_report.csv`, `gwl_linkage_summary.txt`) was present in earlier documentation but does NOT exist in the current directory. These files may have been moved to a different location or removed. If GWL quality diagnostics are needed, rerun the inspection scripts.

**Table preview — `gwl_allwells_flat.csv` (primary join table, 300 rows × 11 columns, updated 2026-05-26):**

| station | wellcode | well_depth_m | well_screen_str | well_elev_m | x_twd97 | y_twd97 | screen_top_m | screen_bot_m | elev_leveling_m | elev_DEM_m |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| ANHE | 10070111 | 59.0 | 40.00~52.00 | 12.449 | 179809.178 | 2601454.369 | 40.0 | 52.0 | 11.0 | 12 |
| ANHE | 10070121 | 96.3 | 72.00~90.00 | 12.412 | 179809.178 | 2601454.369 | 72.0 | 90.0 | 11.0 | 12 |
| ANHE | 10070131 | 163.5 | 144.00~156.00 | 12.484 | 179809.178 | 2601454.369 | 144.0 | 156.0 | 11.0 | 12 |

> 300 wells (rows). `wellcode` = join key to feather column headers. **Use `elev_leveling_m` for head-to-depth conversion** (2023 geodetic leveling + Kriging, ±cm accuracy). `well_elev_m` is the original well record, retained for reference. `elev_DEM_m` is from Taiwan 20m DEM — do not use for stress-strain calculations.

**Table preview — GWL feather timeseries (`{STATION}_gwl_timeseries.feather`, 100 files, ~9,497 rows each):**  

Each file has a `datetime` column (daily, 2000-01-01 to 2025-12-31) plus one float64 column per well at that station. Column names are numeric `computer_id` codes. Example structure for TUKU (2 wells):

| datetime | 09010111 | 09010121 |
|---|---:|---:|
| 2000-01-01 | 17.24 | — |
| 2000-01-02 | 17.25 | — |
| ... | ... | ... |
| 2025-12-31 | 10.82 | 9.45 |

> Values are piezometric head in metres elevation. Wells at the same station share the same feather file. `gwl_feather_stem` from `data/mlcw/MLCW_InSAR_GWL_pairs.xlsx` maps directly to the file stem (e.g. `"TUKU"` → `TUKU_gwl_timeseries.feather`). 100 feather files exist, covering the 306 wells originally catalogued (300 after cleanup).

### 1.3b MLCW-Aligned GWL Timeseries — Per-Well-Pair Format (2026-05-27)

**What it is:** GWL timeseries files aligned to the **MLCW monitoring timeline** (~monthly field-campaign dates, ~264 epochs), organised as one file per MLCW station × GWL well pair. These are the direct inputs to the 2S-TOOL stress-strain analysis pipeline.

**Coverage:** 189 files (37 stations × 4–6 layers per station = 195, minus 6 that lack a resolvable feather match). All files in `data/gwl/mlcw_gwl_timeseries/`.

| Folder / File | Description |
|---|---|
| `data/gwl/mlcw_gwl_timeseries/{MLCW_STATION}_{GWL_STATION}_{WELLCODE}.feather` | 189 files. Columns: `datetime` + one GWL column named `{MLCW_STATION}_{GWL_STATION}_{WELLCODE}`. ~264 rows, aligned to MLCW monitoring timeline. Values: piezometric head in m above MSL. |

**Example file names:**
- `ANHE_ANHE_10070111.feather` (MLCW=ANHE, GWL station=ANHE, well=10070111)
- `ANHE_BEIGANG_09060121.feather` (MLCW=ANHE, proxy GWL station=BEIGANG)
- `ANNAN_HAIYUAN_09160111.feather`
- `BEICHEN_DONGGUANG_09180411.feather`

**Example — `TUKU_TUKU_09050321.feather` (264 rows × 2 columns):**

| datetime | TUKU_TUKU_09050321 |
|---|---:|
| 2015-01-01 | 5.23 |
| 2015-01-16 | 4.81 |
| ... | ... |
| 2025-12-01 | 3.76 |

> The column naming format `{MLCW_STATION}_{GWL_STATION}_{WELLCODE}` avoids ambiguity when the GWL station differs from the MLCW station (proxy assignments). This format differs from the §1.3c InSAR-aligned format which includes a layer code in the column name.

**Processing step (added 2026-05-27):**
- **Inputs:**
  - `data/gwl/well_timeseries/{STATION}_gwl_timeseries.feather` — daily GWL source
  - `data/gwl/gwl_to_mlcw_layer_assignment_v3.csv` — 195 rows, `assigned_wellcode` field
  - `data/mlcw/group_byLayer_orig/{STATION}_orig_grouped.csv` — provides the MLCW date grid (~264 rows)
- **Algorithm:** For each station × layer row in the assignment CSV, extract the assigned well's daily GWL column and downsample to match the MLCW monitoring dates.
- **Output:** `data/gwl/mlcw_gwl_timeseries/{MLCW_STATION}_{GWL_STATION}_{WELLCODE}.feather` (189 files)
- **Script:** `data/gwl/extract_gwl_timeseries_pair_mlcw.txt` (documents the extraction procedure)

---

### 1.3c MLCW-Aligned GWL Timeseries — InSAR-Date Format (2026-05-22)

**What it is:** GWL timeseries files aligned to the **InSAR overpass dates** (~786 epochs, ~5-day cadence), pre-joined to MLCW hydrogeological layers. One file per MLCW station. Each data column is the piezometric head at one assigned well — the same well may serve multiple layers. This format is the primary GWL-driven IHM-F model input.

**Key distinction from §1.3b:**

| Format | §1.3b | §1.3c |
|---|---|---|
| File count | 189 | 37 |
| Rows per file | ~264 (MLCW monitoring dates) | 786 (InSAR dates) |
| Column scheme | `{MLCW_STATION}_{GWL_STATION}_{WELLCODE}` | `{STATION}_{LAYER}_{GWL_STATION}_{WELLCODE}` |
| Timeline reference | MLCW field-campaign dates (~monthly) | InSAR overpass dates (~5-day) |
| Primary use | 2S-TOOL S_ke / S_kv estimation | GWL-driven IHM-F model fitting |

> **Note:** At the time of the 2026-05-27 directory survey, the 37 station-level InSAR-aligned files (`{STATION}_{WELLNAME}.feather`) were NOT confirmed present in `data/gwl/mlcw_gwl_timeseries/`. The 189 per-pair files (§1.3b format) are confirmed present. The InSAR-aligned format (§1.3c) was produced by `scripts/notebooks/prepare_gwl_timeseries_match_mlcw.py` and may need to be regenerated if GWL-driven model fitting requires it.

**Table preview — `TUKU_TUKU.feather` (786 rows × 7 columns, when present):**

| datetime | TUKU_F1_TUKU_09050321 | TUKU_F2_TUKU_09050321 | TUKU_F3_TUKU_09050341 | TUKU_F4_TUKU_09050341 | TUKU_T1_TUKU_09050321 | TUKU_T2_TUKU_09050331 |
|---|---:|---:|---:|---:|---:|---:|
| 2015-01-16 | 5.491 | 5.491 | 4.466 | 4.466 | 5.491 | 4.651 |
| 2015-01-21 | 4.813 | 4.813 | 4.180 | 4.180 | 4.813 | 4.043 |

---

### 1.4 Stratigraphy — Material Classification at Depth

**What it is:** Hydrofacies (material type: Clay, Sand, Gravel, etc.) at each MLCW station, at 5 m depth intervals from 0 to 295 m. Available in two forms: a regional BME-modeled grid and station-specific borehole logs.

**Regional Model (BME):**

| File | Description |
|---|---|
| `data/mlcw/mlcw_hydrofacies_5m.csv` | **Regional BME Stratigraphy.** 2,340 rows (39 stations × 60 depth levels). Derived from the 112_BME regional model. Columns: `station`, `x_twd97`, `y_twd97`, `depth_m`, `nearest_bme_dist_m`, `material_code`, `material_class`. |

**Station-Specific (MLCW Borehole Logs):**

| File | Description |
|---|---|
| `data/mlcw/group_byLayer_reconstr/{STATION}_classify_table.csv` | **Primary MLCW Stratigraphy.** Per-station unit classification (F1, T1, etc.) defining the geological unit at each depth slab, **derived directly from the physical borehole logs taken during the construction of the MLCW station.** Same files are duplicated in `group_byLayer_modeled/` and `group_byLayer_orig/`. |

> **Original Source:** The fundamental ground-truth for the MLCW station lithology is located at `D:\1000_SCRIPTS\001_PreQE_Scripts\MultiLayerCompactionMonitoringWells\MLCW_Data_Extraction\*.xlsx` (e.g., `YL_WSYL23G1_TUKU_土庫.xlsx`).

**Material codes (BME model):**

| Code | Class |
|---|---|
| 1 | Clay |
| 2 | Mud |
| 3 | Silt |
| 4–5 | Fine Sand |
| 6 | Medium Sand |
| 7 | Coarse Sand |
| 8–11 | Gravel |
| 13 | Bedrock |
| 14–15 | Fill |

**Table preview — `mlcw_hydrofacies_5m.csv` (2,340 rows × 7 columns, 39 stations × 60 depth levels):**

| station | x_twd97 | y_twd97 | depth_m | nearest_bme_dist_m | material_code | material_class |
|---|---:|---:|---:|---:|---:|---:|
| ANHE | 179539.2 | 2602035.5 | 0 | 3699.8 | 1 | Clay |
| ANHE | 179539.2 | 2602035.5 | 5 | 3699.8 | 5 | Fine Sand |
| ANHE | 179539.2 | 2602035.5 | 10 | 3699.8 | 5 | Fine Sand |

> `nearest_bme_dist_m` = distance from station to nearest BME grid cell. Higher values mean less certain lithology assignment.

**Processing steps:**
1. 112_BME_CRAF.csv (1 m resolution) → nearest-grid lookup for each MLCW station → modal material code in 5 m bins → `data/mlcw/mlcw_hydrofacies_5m.csv` (script: `scripts/02_mlcw_processing/mlcw_hydrofacies_5m.py`, run 2026-05-16)

---

### 1.5 Derived Analysis Files — Direct Ratio Results

**What it is:** The per-depth compaction fraction f̄_k = median(Y_k / x) computed for all 39 stations. This is the primary analytical product — the model-free baseline against which all advanced models (ARX, harmonic, wet/dry) are compared.

| Folder / File | Description |
|---|---|
| `results/direct_ratio/{STATION}/` | Per-station subfolder (39 folders) |
| `results/direct_ratio/{STATION}/{STATION}_direct_ratio_stats.csv` | 60 rows × 7 columns: `depth_m`, `f_median`, `f_q25`, `f_q75`, `f_p05`, `f_p95`, `n_finite_epochs` |
| `results/direct_ratio/{STATION}/{STATION}_direct_ratio_all.npy` | Full epoch-by-epoch ratio array (NumPy binary) |
| `results/direct_ratio/all_stations_validation_summary.csv` | 39 rows × 20 columns of validation metrics per station (mean R², mean RMSE, etc.) |
| `results/direct_ratio/harmonic_allstations_summary.csv` | Results from harmonic seasonal extension (all 39 stations) |
| `results/direct_ratio/wetdry_allstations_summary.csv` | Results from wet/dry seasonal split extension (all 39 stations) |

**Processing steps:**
1. `data/mlcw/regular_5m/` + `data/insar/timeseries/mlcw_interp_insar_IDW_extend.feather` → direct ratio per depth → `{STATION}_direct_ratio_stats.csv` (script: `scripts/06_direct_ratio/direct_ratio_all_stations.py`)
2. Harmonic extension → `harmonic_allstations_summary.csv` (script: `scripts/07_analysis/harmonic_allstations.py`)
3. Wet/dry extension → `wetdry_allstations_summary.csv` (script: `scripts/07_analysis/wetdry_allstations.py`)
4. Validation → `all_stations_validation_summary.csv` (script: `scripts/07_analysis/validate_all_stations.py`)

---

### 1.6 Station Metadata

| File | Description |
|---|---|
| `gis/alpha/alpha_comparison_all_stations_v3.csv` | 39 rows × 18 columns. Columns: `Ename`, `X_TWD97`, `Y_TWD97`, `alpha_insar`, `alpha_gnss`, `alpha_diff`, `alpha_ratio`, `v_MLCW_mmyr`, `v_InSAR_mmyr`, overlap start/end dates, etc. |
| `data/gps/GPS_data_timeline.csv` | ~45 GPS stations × 8 columns: `station_co`, `long`, `lat`, `height`, `start_date`, `end_date`, `duration`, `num_of_obs`. |
| `gis/study_area/mlcw_station_utm50n.csv` | MLCW station coordinates in UTM zone 50N. |
| `gis/study_area/` | Shapefiles for MLCW stations, grid, study area boundary (including `GWL_unique_wells_2026.shp`). |
| `gis/alpha/` | Alpha prior data: `alpha_comparison_all_stations_v3.csv`, `alpha_comparison_all_stations_v2.gpkg`, shapefiles for alpha interpolation. |
| `gis/kriging/` | Kriging layer files (`.lyr`) for spatial interpolation visualization in ArcGIS. |

**Table preview — `alpha_comparison_all_stations_v3.csv` (39 rows × 18 columns):**

| Ename | v_MLCW_mmyr | v_InSAR_mmyr | alpha_insar | alpha_gnss | alpha_diff | alpha_ratio | X_TWD97 | Y_TWD97 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ANHE | -18.03 | -39.51 | 0.456 | 1.393 | -0.937 | 0.328 | 179539.2 | 2602035.5 |
| ANNAN | -22.66 | -27.24 | 0.832 | 0.826 | 0.006 | 1.007 | 173539.8 | 2626430.8 |
| BEICHEN | -17.78 | -22.44 | 0.792 | 0.862 | -0.070 | 0.919 | 178860.0 | 2608228.9 |

> `alpha_insar` = v_MLCW / v_InSAR (compaction fraction from velocities). `alpha_gnss` = v_MLCW / v_GNSS (independent check).

---

### 1.7 GPS — Geodetic Surface Displacement

**What it is:** GNSS (GPS) vertical displacement timeseries at ~100 continuous GPS stations. Used for InSAR validation (comparison of vertical velocity) and as an independent check on the compaction fraction α. The GPS data has been decomposed into trend + seasonal components using the same STL pipeline applied to MLCW.

| Folder / File | Count | Description |
|---|---|---|
| `data/gps/GPS_data_timeline.csv` | 1 file | Summary of ~45 GPS stations used in this project: `station_co`, `long`, `lat`, `height`, `start_date`, `end_date`, `duration`, `num_of_obs`. |
| `data/gps/raw_timeseries/patch_1/` | 30 files | Raw GPS vertical displacement timeseries, batch 1. Each file: `{STATION}_neu.csv` with columns `datetime`, `gpsdate`, `dN`, `dE`, `dU`, `sN`, `sE`, `sU`. Values in mm relative to reference epoch. |
| `data/gps/raw_timeseries/patch_2/` | 30 files | Raw GPS timeseries, batch 2 (same format). |
| `data/gps/raw_timeseries/patch_3/` | 40 files | Raw GPS timeseries, batch 3 (same format). 100 total raw stations across all 3 patches. |
| `data/gps/decomposed/{STATION}_neu/` | 100 subfolders | Per-station decomposition outputs: `{STATION}_neu_decomposed_dU.csv`, `{STATION}_neu_decomposed_dU.png`, `{STATION}_neu_model_dU.json`, `{STATION}_neu_report_dU.md`. Focus is on the vertical (dU) component. |
| `data/gps/modeled/{STATION}_neu.csv` | 97 files | Modelled GPS vertical timeseries: columns `date`, `orig`, `orig_nojump`, `modeled`. Parallel to MLCW `modeled/` output. |
| `data/gps/modeled/{STATION}_model.csv` | 97 files | Model parameters CSV (structure TBD — check individual files). |

> **GPS station count:** 100 raw stations in `raw_timeseries/`; 97 modeled (3 stations skipped — `CHIN_neu_skipped_dU.txt`, `ERLN_neu_skipped_dU.txt`, `PUSN_neu_skipped_dU.txt` in `decomposed/`). The `GPS_data_timeline.csv` lists ~45 stations — this is the subset used for InSAR velocity comparison; the full 100-station set was processed for decomposition.

**Table preview — raw GPS file (e.g., `8118_neu.csv`, columns):**

| datetime | gpsdate | dN | dE | dU | sN | sE | sU |
|---|---|---:|---:|---:|---:|---:|---:|
| 2010.00548 | 2010-01-02 | -96.729 | 163.961 | 33.514 | 1.145 | 1.637 | 8.200 |
| 2010.00822 | 2010-01-03 | -98.590 | 163.543 | 38.362 | 1.160 | 1.651 | 8.334 |

> `dU` = vertical displacement in mm relative to reference epoch. `sU` = formal uncertainty. `datetime` is decimal year format; `gpsdate` is ISO format.

---

### 1.8 2S-TOOL Input Files — Stress-Strain Analysis

**What it is:** Prepared input files for the 2S-TOOL stress-strain skeletal storage coefficient analysis. Each file pairs ground displacement (InSAR-derived, mm) with groundwater depth (m below surface) at a single MLCW station and hydrogeological layer.

**Coverage (current state as of 2026-05-27):** Only TUKU 6-layer files are present in `data/gwl/2stool_inputs/`. Earlier documentation referred to 195 files across all 37 stations — those may have been produced externally or in a different working directory.

| Folder / File | Description |
|---|---|
| `data/gwl/2stool_inputs/2STOOL_TUKU_F1.xlsx` | 2S-TOOL input for TUKU F1. Excel: `StrainStress` sheet (displacement + GWL depth), `InputData` sheet. |
| `data/gwl/2stool_inputs/2STOOL_TUKU_F2.xlsx` | Same for TUKU F2. |
| `data/gwl/2stool_inputs/2STOOL_TUKU_F3.xlsx` | Same for TUKU F3. |
| `data/gwl/2stool_inputs/2STOOL_TUKU_F4.xlsx` | Same for TUKU F4. |
| `data/gwl/2stool_inputs/2STOOL_TUKU_T1.xlsx` | Same for TUKU T1 (aquitard, driven by nearest aquifer head). |
| `data/gwl/2stool_inputs/2STOOL_TUKU_T2.xlsx` | Same for TUKU T2. |
| `data/gwl/2stool_inputs/preparation_log.csv` | Log of which files were prepared and when. |

> **Note:** `hp_inicial_overrides.json` is not present in `data/gwl/2stool_inputs/`. If needed, regenerate with `scripts/09_trackB/generate_hp_overrides.py` after the full 195-file batch is produced. The JSON maps input file stems to preconsolidation head values (m GWL depth) computed from the full 2000–2025 daily record using `elev_leveling_m`.

**Conversion note:** GWL depth = `elev_leveling_m − piezometric_head`, where `elev_leveling_m` comes from `gwl_allwells_flat.csv` (2023 geodetic leveling + Kriging). This was updated from `well_elev_m` on 2026-05-26.

---

### 1.9 2S-TOOL Output Files

**What it is:** Per-file outputs from the 2S-TOOL Python pipeline (`twostool_python`). Each run produces up to 6 files (CSV + JSON + PNG).

**Coverage (current state as of 2026-05-27):** 7 station-layer folders are present in `data/gwl/2stool_outputs/`: `2STOOL_ANHE_F1` and `2STOOL_TUKU_F1` through `2STOOL_TUKU_T2`. No aggregated result CSVs (`2stool_results_summary.csv`, `2stool_loops_all.csv`) are present. Earlier documentation referred to 195 processed files — those results may reside in an external location.

| Folder / File | Description |
|---|---|
| `data/gwl/2stool_outputs/{BASENAME}/{BASENAME}_sscurve.csv` | Full stress-strain curve. Columns: `index`, `disp_m`, `gwl_depth_m`. One row per epoch. |
| `data/gwl/2stool_outputs/{BASENAME}/{BASENAME}_loops.csv` | Per-loop elastic fit parameters. Columns: `loop_id`, `slope`, `intercept`, `x_start`, `x_end`, `y_fit_start`, `y_fit_end`, `delta_x_m`, `delta_y_m`, `n_pts`, `accepted`, `s_ke`, `start_idx`, `end_idx`. |
| `data/gwl/2stool_outputs/{BASENAME}/{BASENAME}_loops.json` | Same as `_loops.csv` but as JSON array. NaN values serialized as `null`. |
| `data/gwl/2stool_outputs/{BASENAME}/{BASENAME}_summary.csv` | One-row run summary: `file`, `skv`, `ske_max`, `ske_mean`, `ske_min`, `ske_weighted`, `ske_std`, `n_loops_total`, `n_loops_accepted`, `y_interval`, `x_interval`, `hc`, `pct_amplitude`. |
| `data/gwl/2stool_outputs/{BASENAME}/{BASENAME}_summary.json` | Same as `_summary.csv` but as JSON object. |
| `data/gwl/2stool_outputs/{BASENAME}/{BASENAME}_Fig02_skv_jva.png` | S_kv figure: full stress-strain cloud with fitted envelope line. |
| `data/gwl/2stool_outputs/{BASENAME}/{BASENAME}_Fig02_skv_jva_v2.png` | S_kv + peak/trough markers. |
| `data/gwl/2stool_outputs/{BASENAME}/{BASENAME}_Fig03_ske_jva.png` | S_ke figure: colour-coded elastic loops. |

**Table preview — `{BASENAME}_summary.json` (example: 2STOOL_TUKU_F1):**

| Field | Value | Description |
|---|---|---|
| `file` | `"2STOOL_TUKU_F1"` | Input file stem (no extension) |
| `skv` | `0.004452` | Anelastic (virgin) skeletal storage coefficient |
| `ske_max` | `0.001277` | Maximum elastic S_ke across accepted loops |
| `ske_mean` | `0.000396` | Arithmetic mean of accepted S_ke |
| `ske_weighted` | `0.000381` | Amplitude-weighted mean S_ke |
| `n_loops_total` | `22` | Total elastic periods identified |
| `n_loops_accepted` | `16` | Passed the amplitude threshold (PORCENTAJE) |
| `hc` | `22.783` | Preconsolidation head used in this run (m GWL depth) |

**There is also a `data/gwl/2stool_sample_outputs/` folder** containing 2 additional station-layer subfolders (`2STOOL_TUKU_F2`, `2STOOL_TUKU_F4`) and their corresponding Excel files — used for testing and documentation.

---

### 1.10 Known Issue — `gwl_min_m` / `gwl_max_m` Column Naming in `gwl_allwells_flat.csv`

The columns `gwl_min_m` and `gwl_max_m` in `data/gwl/well_info/gwl_allwells_flat.csv` (if present from an older version) store **raw piezometric head** (metres elevation above sea level), NOT groundwater depth (metres below ground surface). The `_m` suffix in the column name is misleading — it refers to elevation, not depth.

**Correct conversion:**
```
GWL_depth = elev_leveling_m − piezometric_head
hp_inicial (preconsolidation head) = elev_leveling_m − min(piezometric_head)
```

Do not use `gwl_max_m` directly as any depth measure — it is the maximum piezometric head (shallowest GWL). To get maximum GWL depth (preconsolidation head), use `elev_leveling_m − gwl_min_m`.

---

## Part 2 — Processing Pipeline (Visual Summary)

```
RAW INPUTS                    PROCESSING SCRIPTS               ANALYSIS-READY FILES
─────────────────────────     ──────────────────────────       ─────────────────────────────────────

MLCW ring measurements        batch_process_MLCW.py         →  data/mlcw/decomposed/{STATION}_ringbyring/ (per-ring decomposition)
  (raw_timeseries/)           batch_process_MLCW.py         →  data/mlcw/modeled/{STATION}_ringbyring.csv (model fit at MLCW dates)
                              batch_reconstruct_MLCW.py     →  data/mlcw/reconstructed/{STATION}_ringbyring_reconstructed.csv
                              mlcw_5m_grid.py               →  data/mlcw/regular_5m/{STATION}_5m_grid.csv  ← PRIMARY
                              mlcw_by_group.py              →  data/mlcw/group_byLayer_reconstr/ (from reconstructed)  ← PRIMARY
                              extract_group_byLayer_orig.txt→  data/mlcw/group_byLayer_orig/ (from raw HDF5)
                              extract_group_byLayer_orig.txt→  data/mlcw/group_byLayer_modeled/ (from modeled HDF5)

InSAR ascending + descending  A1_adaptive_omt_*.py         →  data/insar/timeseries/*.feather            ← PRIMARY
  (MintPy HDF5)               E1/E2 LOS decomposition         (39 stations + 8,577 grid points)
                              K2 IDW interpolation

GPS raw timeseries            batch_process_GPS.py          →  data/gps/decomposed/{STATION}_neu/ (per-station decomposition)
  (raw_timeseries/patch_*)    batch_process_GPS.py          →  data/gps/modeled/{STATION}_model.csv
                                                               data/gps/modeled/{STATION}_neu.csv

GWL raw records               inspect_gwater_data.py        →  data/gwl/well_info/gwl_allwells_flat.xlsx
  (HDF5)                      PowerShell (Task P1)           →    + screen_top_m, screen_bot_m columns   ← READY
                              consolidate_well_materials.py →  data/gwl/well_materials_summary.csv
                              export HDF5 to feather         →  data/gwl/well_timeseries/ (100 feather files)

gwl_allwells_flat.csv         assign_gwl_to_layers() v3     →  data/gwl/gwl_to_mlcw_layer_assignment_v3.csv  ← CANONICAL
  + classify_table.csv        (extend_layer_assignment.py)
  + 10km radius search

gwl_to_mlcw_layer_assignment_v3.csv  extract_gwl_timeseries_pair_mlcw.py →  data/gwl/mlcw_gwl_timeseries/    ← READY
  + {STATION}_gwl_timeseries.feather                                         189 per-pair feather files
  + group_byLayer_orig dates                                                  (MLCW-timeline-aligned)

gwl_allwells_flat.csv         prepare_2stool_inputs.py      →  data/gwl/2stool_inputs/2STOOL_{STATION}_{LAYER}.xlsx
  + mlcw_gwl_timeseries/                                        (6 TUKU files currently; full 195 file batch pending)

2STOOL inputs                 batch_run_2stool.py           →  data/gwl/2stool_outputs/{BASENAME}/
  (2STOOL_*.xlsx)                                               (7 folders; ANHE_F1 + TUKU×6)

MLCW 5m_grid + InSAR          direct_ratio_all_stations.py  →  results/direct_ratio/{STATION}/
                              harmonic_allstations.py        →    harmonic_allstations_summary.csv
                              wetdry_allstations.py           →    wetdry_allstations_summary.csv
                              validate_all_stations.py        →    all_stations_validation_summary.csv     ← DONE

MLCW grouped + InSAR + GWL    [GWL-driven — IHM-F]             →  results/track_b/                          ← PENDING
  (group_byLayer_reconstr)    gwl_loader.py, validation.py
                              track_b_models.py
```

---

## Part 3 — Expected Data Structure for the Analysis

This section describes what files are needed for each stage of analysis.

### 3.1 Stage 1 — Static scaling baseline (MLCW + InSAR only — comparison floor)

| File | Status | Format |
|---|---|---|
| `data/mlcw/regular_5m/{STATION}_5m_grid.csv` | ✓ Ready (39 files) | CSV: rows = epochs, cols = `datetime` + 61 depth columns |
| `data/insar/timeseries/mlcw_interp_insar_IDW_extend.feather` | ✓ Ready | Feather: 39 rows × 791 cols (6 metadata + 785 epoch dates) |
| `data/insar/timeseries/gridpnt_500m_interp_insar_IDW_extend.feather` | ✓ Ready | Feather: 8,577 rows × 790 cols |
| `gis/alpha/alpha_comparison_all_stations_v3.csv` | ✓ Ready | CSV: 39 rows, station metadata |
| `results/direct_ratio/{STATION}/{STATION}_direct_ratio_stats.csv` | ✓ Ready (39 files) | CSV: 60 rows × 7 cols |

### 3.2 Stage 2 — GWL-driven method (MLCW + InSAR + GWL — under exploration)

| File | Status | Format needed |
|---|---|---|
| `data/gwl/well_info/gwl_allwells_flat.csv` | ✓ Ready (300 wells, 11 cols) | CSV: `wellcode`, `x_twd97`, `y_twd97`, `screen_top_m`, `screen_bot_m`, `elev_leveling_m`, etc. |
| Per-station GWL timeseries | ✓ Ready — `data/gwl/well_timeseries/{STATION}_gwl_timeseries.feather` (100 files) | Feather: `datetime` + one float64 column per well code. Daily, 2000–2025. |
| GWL→MLCW layer assignment | ✓ Ready — `data/gwl/gwl_to_mlcw_layer_assignment_v3.csv` (195 rows × 14 cols) | CSV: 195 assignments across 37 stations. Use `_v3.csv`, not unversioned CSV. |
| MLCW-aligned GWL timeseries (per-pair) | ✓ Ready — `data/gwl/mlcw_gwl_timeseries/*.feather` (189 files) | Feather: `datetime` + 1 GWL column, ~264 rows, MLCW-date-aligned. For 2S-TOOL. |
| MLCW layer-grouped (reconstr) | ✓ Ready — `data/mlcw/group_byLayer_reconstr/{STATION}_reconst_grouped.csv` (37 files) | CSV: `datetime` + 6 layer cols (F1–F4, T1–T2), ~1,572 rows. **Primary GWL-driven model input.** |
| MLCW layer-grouped (orig) | ✓ Ready — `data/mlcw/group_byLayer_orig/{STATION}_orig_grouped.csv` (37 files) | CSV: `datetime` + 7 layer cols (F1–F4, T1–T3), ~264 rows. Used by 2S-TOOL. |
| 2S-TOOL input files | ⚠ Partial — `data/gwl/2stool_inputs/2STOOL_TUKU_*.xlsx` (6 TUKU files only) | Excel: `StrainStress` sheet. 195-file batch not yet present in this directory. |
| 2S-TOOL per-file outputs | ⚠ Partial — `data/gwl/2stool_outputs/{BASENAME}/` (7 folders: ANHE_F1 + TUKU×6) | CSV+JSON+PNG per input file. |
| MLCW-aligned GWL (InSAR dates) | ⚠ Status TBD — `data/gwl/mlcw_gwl_timeseries/{STATION}_{WELLNAME}.feather` (37 expected) | Feather: `datetime` + 4–6 layer cols, 786 rows, InSAR-date-aligned. Regenerate if needed. |

**Linkage status (from last check 2026-05-19, inspection_reports/ no longer present):**
- Timeseries ↔ metadata: CLEAN — 0 orphan wells in either direction
- Coordinates: 6 wells broken (DOULIU/090111M2 x=0,y=0; GANYUAN ×2, XIABANTIAN ×2, ZHONGLIAO ×1 all NaN) — none are MLCW-overlap stations
- Screen depths: 26 of 71 MLCW-overlap wells missing screen_top_m / screen_bot_m, covering 15 stations — addressed via v3 assignment algorithm (10 km radius search)

### 3.3 Stage 3 (add stratigraphy — deferred)

| File | Status | Format |
|---|---|---|
| `data/mlcw/mlcw_hydrofacies_5m.csv` | ✓ Ready | CSV: 2,340 rows. Columns: `station`, `depth_m`, `material_code`, `material_class` |
| `data/mlcw/group_byLayer_reconstr/{STATION}_classify_table.csv` | ✓ Ready (37 files) | CSV: borehole-derived layer classification per station |

---

## Part 4 — Data Status Summary Table

| Dataset | File(s) | Dimensions | Status |
|---|---|---|---|
| MLCW (raw ring-by-ring) | `data/mlcw/raw_timeseries/{STATION}_ringbyring.csv` (39 files) | 39 × 23–25 rings × ~264 epochs | ✓ Ready |
| MLCW (decomposed per-ring) | `data/mlcw/decomposed/{STATION}_ringbyring/` (39 subfolders) | ~88 files per station (CSV+PNG+JSON+MD) | ✓ Ready |
| MLCW (modeled ring-by-ring) | `data/mlcw/modeled/{STATION}_ringbyring.csv` (39 files) | 39 × 23–25 rings × ~264 epochs | ✓ Ready |
| MLCW (reconstructed) | `data/mlcw/reconstructed/{STATION}_ringbyring_reconstructed.csv` (39 files) | ~23 rings × ~1,500 dates per station | ✓ Ready |
| MLCW (regularised 5m) | `data/mlcw/regular_5m/{STATION}_5m_grid.csv` (39 files) | 39 × 61 depths × ~700 epochs | ✓ Ready |
| MLCW layer-grouped (reconstructed) | `data/mlcw/group_byLayer_reconstr/{STATION}_reconst_grouped.csv` (37 files) | 37 stations × ~6 layers × ~1,572 epochs | ✓ Ready (2026-05-20) |
| MLCW layer-grouped (modeled) | `data/mlcw/group_byLayer_modeled/{STATION}_modeled_grouped.csv` (37 files) | 37 stations × ~6 layers × ~264 epochs | ✓ Ready |
| MLCW layer-grouped (original raw) | `data/mlcw/group_byLayer_orig/{STATION}_orig_grouped.csv` (37 files) | 37 stations × ~7 layers × ~264 epochs | ✓ Ready |
| MLCW ring→layer mapping | `data/mlcw/group_byLayer_reconstr/{STATION}_classify_table.csv` (37 files) | 37 stations, ~20–30 rows each | ✓ Ready (2026-05-20) |
| InSAR at MLCW stations | `data/insar/timeseries/mlcw_interp_insar_IDW_extend.feather` | 39 stations × 785 epochs | ✓ Ready |
| InSAR at 500 m grid | `data/insar/timeseries/gridpnt_500m_interp_insar_IDW_extend.feather` | 8,577 points × 785 epochs | ✓ Ready |
| GPS timeseries (raw) | `data/gps/raw_timeseries/patch_{1,2,3}/` (100 files total) | ~100 stations, daily dU/dN/dE | ✓ Ready |
| GPS timeseries (decomposed) | `data/gps/decomposed/{STATION}_neu/` (100 subfolders) | ~100 stations, CSV+PNG+JSON+MD per station | ✓ Ready |
| GPS timeseries (modeled) | `data/gps/modeled/{STATION}_{model,neu}.csv` (97 files each) | ~97 stations | ✓ Ready (3 skipped) |
| GPS station timeline | `data/gps/GPS_data_timeline.csv` | ~45 stations × 8 cols | ✓ Ready |
| Station metadata + α | `gis/alpha/alpha_comparison_all_stations_v3.csv` | 39 rows × 18 columns | ✓ Ready |
| Direct ratio f̄_k | `results/direct_ratio/{STATION}/{STATION}_direct_ratio_stats.csv` (39 files) | 60 depths × 7 metrics | ✓ Ready |
| Batch validation results | `results/direct_ratio/all_stations_validation_summary.csv` | 39 stations × 20 metrics | ✓ Ready |
| GWL flat table (all wells) | `data/gwl/well_info/gwl_allwells_flat.xlsx` / `.csv` | 300 wells × 11 columns | ✓ Ready (2026-05-26) |
| GWL→MLCW layer assignment (canonical) | `data/gwl/gwl_to_mlcw_layer_assignment_v3.csv` | 195 assignments, 37 stations | ✓ Ready (2026-05-26) |
| GWL→MLCW layer assignment (older) | `gwl_to_mlcw_layer_assignment.xlsx`, `_v2.xlsx` | 195 assignments | Reference only |
| MLCW-aligned GWL (per-pair, §1.3b) | `data/gwl/mlcw_gwl_timeseries/{MLCW}_{GWL}_{WELLCODE}.feather` (189 files) | 189 files × ~264 rows × 2 cols | ✓ Ready (2026-05-27) |
| MLCW-aligned GWL (InSAR-dates, §1.3c) | `data/gwl/mlcw_gwl_timeseries/{STATION}_{WELLNAME}.feather` (37 expected) | 37 stations × 786 epochs × 4–6 layers | ⚠ Status TBD — not confirmed present |
| GWL timeseries (per station) | `data/gwl/well_timeseries/{STATION}_gwl_timeseries.feather` | 100 files, 300 wells, daily 2000–2025 | ✓ Ready (2026-05-19) |
| BME well materials (lithostratigraphy) | `data/gwl/well_materials/` (95 .txt + 95 .png) | 95 GWL stations | ✓ Ready |
| Well materials summary | `data/gwl/well_materials_summary.csv` | 345 rows, 91 stations | ✓ Ready |
| Stratigraphy (BME-derived) | `data/mlcw/mlcw_hydrofacies_5m.csv` | 39 × 60 depths | ✓ Ready |
| 2S-TOOL input files | `data/gwl/2stool_inputs/2STOOL_TUKU_*.xlsx` (6 files) + `preparation_log.csv` | TUKU only (195-file batch not present) | ⚠ Partial |
| 2S-TOOL hp_inicial overrides | `data/gwl/2stool_inputs/hp_inicial_overrides.json` | 195 entries | ⚠ Not present — regenerate if needed |
| 2S-TOOL per-file outputs | `data/gwl/2stool_outputs/{BASENAME}/` | 7 folders (ANHE_F1 + TUKU×6) | ⚠ Partial |
| 2S-TOOL sample outputs | `data/gwl/2stool_sample_outputs/` | 2 subfolders + 2 XLSX | Reference only |
| GWL inspection reports | `data/gwl/inspection_reports/` | — | ✗ Folder NOT present — regenerate if needed |

**Key Conventions:**
- **Well Codes:** Must be treated as **8-digit strings** (e.g., `09050321`). Leading zeros are significant — never read as integers.
- **Proxy Handling:** 24 stations (16 without co-located GWL + 8 with poor co-located screen depths) use proxy GWL data from nearby stations within 10 km.
- **Sign Convention:** Positive = Compaction/Subsidence. InSAR negated on load (original data is negative for subsidence).
- **Canonical assignment file:** `gwl_to_mlcw_layer_assignment_v3.csv` (not the unversioned name which no longer exists).

---

## Part 5 — Key File Formats Reference

### `{STATION}_5m_grid.csv` (MLCW regularised)
```
datetime,depth_000m,depth_005m,...,depth_300m
2003-12-06,0.00,0.00,...,0.00
2004-01-15,-0.12,-0.05,...,-0.01
```
- Rows: one per observation epoch (irregular dates, typically every 3–4 weeks)
- Columns: `datetime` + 61 depth columns (`depth_000m` to `depth_300m` in 5 m steps)
- Values: cumulative compaction in mm (negative = compaction / subsidence)
- The `depth_300m` column is the reference anchor (always 0.0)

### InSAR `*.feather` (at MLCW or grid)
- Rows: one per station or grid point
- First 6 columns: metadata (station name, X, Y, etc.)
- Remaining 785 columns: one per InSAR epoch date (column header = date string)
- Values: cumulative surface displacement in mm

### `{STATION}_direct_ratio_stats.csv`
```
depth_m,f_median,f_q25,f_q75,f_p05,f_p95,n_finite_epochs
0.0,0.00621,0.00321,0.01274,0.00244,0.02835,771
5.0,-0.00195,-0.00502,-0.00005,-0.01118,0.00325,771
```
- 60 rows (one per depth from 0 to 295 m)
- `f_median`: the primary compaction fraction — fraction of surface InSAR subsidence attributed to this depth

### `mlcw_hydrofacies_5m.csv` (Regional BME Stratigraphy)
```
station,x_twd97,y_twd97,depth_m,nearest_bme_dist_m,material_code,material_class
ANHE,179539.2046,2602035.471,0,3699.8,1,Clay
ANHE,179539.2046,2602035.471,5,3699.8,5,Fine Sand
```
- 2,340 rows (39 stations × 60 depth levels)
- `nearest_bme_dist_m`: distance from station to closest BME model grid cell

### `gwl_allwells_flat.csv` (one row per GWL well)
```
station,wellcode,well_depth_m,well_screen_str,well_elev_m,x_twd97,y_twd97,screen_top_m,screen_bot_m,elev_leveling_m,elev_DEM_m
TUKU,09010111,...,80,40,60,-5.2,...
```
- `screen_top_m` and `screen_bot_m`: the depth range of the well screen (where water enters the well)
- `wellcode` is an 8-digit string — leading zeros are significant
- **`elev_leveling_m`** is the canonical elevation for all head-to-depth conversions (2023 geodetic leveling)

### `gwl_to_mlcw_layer_assignment_v3.csv` (one row per MLCW station × layer)
```
station,layer,layer_depth_min_m,layer_depth_max_m,assigned_wellcode,screen_top_m,screen_bot_m,screen_mid_m,screen_str,well_depth_m,assignment_method,note,feather_file,dist_to_gwl_m
ANHE,F1,2.093,39.105,10070111,40.0,52.0,46.0,40.00~52.00,58.0,NEAREST_FALLBACK,...,data/gwl/well_timeseries/ANHE_gwl_timeseries.feather,641.4
```
- `assigned_wellcode` must be read as string (8-digit, leading zeros preserved)
- `feather_file` gives the source GWL timeseries path

---

## Part 6 — Quick Reference: How to Load Each Dataset

```python
import pandas as pd

# ── MLCW ────────────────────────────────────────────

# MLCW 5m grid (primary analysis file)
mlcw = pd.read_csv("data/mlcw/regular_5m/TUKU_5m_grid.csv", parse_dates=["datetime"])

# MLCW station timeline
mlcw_meta = pd.read_csv("data/mlcw/MLCW_data_timeline.csv")

# MLCW ring-by-ring reconstructed
rings = pd.read_csv("data/mlcw/reconstructed/TUKU_ringbyring_reconstructed.csv", parse_dates=["datetime"])

# MLCW layer-grouped (GWL-driven model calibration input — signal-reconstructed, ~1572 rows, 5-day)
mlcw_grouped = pd.read_csv("data/mlcw/group_byLayer_reconstr/TUKU_reconst_grouped.csv", index_col=0, parse_dates=True)

# MLCW layer-grouped (raw-summed, ~264 monthly rows — used by 2S-TOOL)
mlcw_orig = pd.read_csv("data/mlcw/group_byLayer_orig/TUKU_orig_grouped.csv", parse_dates=["datetime"])

# MLCW layer-grouped (from decomposed model fit, ~264 monthly rows)
mlcw_modeled = pd.read_csv("data/mlcw/group_byLayer_modeled/TUKU_modeled_grouped.csv", parse_dates=["datetime"])

# MLCW ring-to-layer classification (borehole-derived)
classify = pd.read_csv("data/mlcw/group_byLayer_reconstr/TUKU_classify_table.csv")

# MLCW-GWL pairing (nearest GWL station per MLCW station)
mlcw_gwl = pd.read_excel("data/mlcw/MLCW_InSAR_GWL_pairs.xlsx", sheet_name="MLCW_InSAR_GWL_pairs")

# MLCW-GWL pairing (all GWL stations within 5 km, BOM-prefixed)
mlcw_gwl_all = pd.read_csv("data/mlcw/MLCW_InSAR_GWL_pairs_all.csv", encoding="utf-8-sig")

# ── InSAR ───────────────────────────────────────────

# InSAR at MLCW stations
insar = pd.read_csv("data/insar/InSAR_measures_at_MLCW.csv", index_col=0, parse_dates=True)

# ── GPS ─────────────────────────────────────────────

# GPS station timeline
gps_meta = pd.read_csv("data/gps/GPS_data_timeline.csv")

# GPS raw vertical timeseries (one per station)
gps_raw = pd.read_csv("data/gps/raw_timeseries/patch_1/ANES_neu.csv", parse_dates=["gpsdate"])
# columns: datetime (decimal year), gpsdate, dN, dE, dU, sN, sE, sU

# GPS modeled vertical timeseries
gps_mod = pd.read_csv("data/gps/modeled/ANES_neu.csv", parse_dates=["date"])
# columns: date, orig, orig_nojump, modeled

# ── Stratigraphy ────────────────────────────────────

# Hydrofacies (BME-derived, 39 stations × 60 depths)
facies = pd.read_csv("data/mlcw/mlcw_hydrofacies_5m.csv")

# ── Station Metadata ────────────────────────────────

# Alpha comparison (station metadata + velocity ratios)
alpha = pd.read_csv("gis/alpha/alpha_comparison_all_stations_v3.csv")

# ── GWL ──────────────────────────────────────────────

# Primary GWL join table (wellcode → coordinates, screen depths)
# elev_leveling_m is the canonical elevation
gwl_flat = pd.read_csv("data/gwl/well_info/gwl_allwells_flat.csv", encoding="utf-8-sig",
                       dtype={"wellcode": str})

# GWL→MLCW layer assignment (37 stations, 195 rows — use _v3.csv, unversioned CSV does not exist)
assign = pd.read_csv("data/gwl/gwl_to_mlcw_layer_assignment_v3.csv",
                     dtype={"assigned_wellcode": str})
# The feather_file column gives the source GWL timeseries path for each row

# GWL timeseries for a station (daily piezometric head, 2000–2025)
gwl_ts = pd.read_feather("data/gwl/well_timeseries/TUKU_gwl_timeseries.feather")

# MLCW-aligned GWL timeseries (per-pair format, MLCW dates, 189 files — for 2S-TOOL)
gwl_pair = pd.read_feather("data/gwl/mlcw_gwl_timeseries/TUKU_TUKU_09050321.feather")
# Columns: datetime + {MLCW_STATION}_{GWL_STATION}_{WELLCODE}

# BME aquifer summary (91 GWL stations)
gwl_mat = pd.read_csv("data/gwl/well_materials_summary.csv")

# ── 2S-TOOL ──────────────────────────────────────────

# 2S-TOOL per-file summary (JSON, example: TUKU F1)
import json
with open("data/gwl/2stool_outputs/2STOOL_TUKU_F1/2STOOL_TUKU_F1_summary.json") as f:
    summary = json.load(f)
with open("data/gwl/2stool_outputs/2STOOL_TUKU_F1/2STOOL_TUKU_F1_loops.json") as f:
    loops_json = json.load(f)  # list of dicts, NaN → null

# Note: aggregated 2stool_results_summary.csv and 2stool_loops_all.csv are NOT present
# in data/gwl/2stool_outputs/ as of 2026-05-27. Run collect_2stool_results.py after
# full 195-file batch is complete.
```

**Conventions:**
- Well codes are **8-digit strings** — always use `dtype={"assigned_wellcode": str}` or `dtype={"wellcode": str}`. Leading zeros are significant and will be lost if read as integers.
- Sign convention: positive = compaction / subsidence. InSAR data is negated on load.
- **Canonical GWL assignment:** use `gwl_to_mlcw_layer_assignment_v3.csv` — the unversioned `.csv` no longer exists.
- **Layer-grouped variant filenames:** `group_byLayer_modeled/` uses `{STATION}_modeled_grouped.csv` (~264 monthly rows); `group_byLayer_reconstr/` uses `{STATION}_reconst_grouped.csv` (~1572 rows). The filenames differ — do not confuse them.

---

*End of summary*
