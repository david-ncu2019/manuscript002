# GWL-to-MLCW Layer Assignment — Guide

**Date:** 2026-06-03 (algorithm last changed 2026-05-26)
**Source CSV:** `gwl_to_mlcw_layer_assignment_v4.csv` (195 data rows $\times$ 17 columns, 37 stations; 13 wellcode fixes applied 2026-06-04)
**Last verified:** 2026-06-06

---

## What changed on 2026-05-26

The assignment algorithm was fundamentally overhauled. The old approach (2026-05-20) used a two-phase strategy:

1. **Co-located stations** — only the station's own GWL wells were considered.
2. **Blocked/missing stations** — the single nearest GWL station by 2D distance served as a proxy.

This had a known flaw: if a station's own wells were poor depth matches (e.g., TUKU's shallowest well is screened at 81–84 m, but F1 spans 9–26 m), the algorithm would assign a 65 m depth mismatch rather than look at a nearby station with a better screen depth.

**The new approach (2026-05-26): screen-depth-first, 10 km search radius.**

For every (station, layer) pair, the algorithm searches ALL GWL stations within 10 km, scores every candidate well by depth-match quality, and picks the best — using 2D distance only as a tiebreaker. This is implemented in `scripts/04_gwl_processing/extend_layer_assignment.py`.

**Key changes at a glance:**

| Aspect | Old (2026-05-20) | New (2026-05-26) |
|--------|-------------------|-------------------|
| Algorithm | Co-located first, then nearest proxy | Screen-depth-first, all stations within 10 km |
| Search radius | 5 km (for proxy fallback only) | 10 km (for all layers) |
| Rows | 109 | 195 |
| Stations | 21 | 37 |
| FULLY_BLOCKED rows | 29 | 0 |
| `feather_file` granularity | Per-station (all layers share one file) | Per-row (each layer may use a different GWL station) |
| New columns | — | `feather_file`, `dist_to_gwl_m` |

---

## Column-by-column guide

| Column | Meaning |
|---|---|
| `station` | MLCW station name (e.g. ANHE, TUKU). One of the 37 subsidence monitoring stations with classify tables. (JINHU_XIN and LUNFENG_XIN lack classify tables and are excluded.) |
| `layer` | Hydrogeological layer code. **F1, F2, F3, F4** = aquifer units (sand/gravel — water-bearing). **T1, T2** = aquitards (clay — low-permeability confining layers). |
| `layer_depth_min_m` | Shallowest magnetic-ring depth (m below ground) classified into this layer at this station. |
| `layer_depth_max_m` | Deepest magnetic-ring depth (m below ground) classified into this layer at this station. |
| `assigned_wellcode` | The numeric ID of the GWL monitoring well whose piezometric head time series is assigned to drive this MLCW layer. Used as the column header in the feather timeseries file. |
| `screen_top_m` | Top of the well screen (m below ground). |
| `screen_bot_m` | Bottom of the well screen (m below ground). The well measures head over `[screen_top_m, screen_bot_m]`. |
| `screen_mid_m` | Midpoint = `(screen_top_m + screen_bot_m) / 2`. This is the single depth used to match wells to layers. |
| `screen_str` | Original raw screen-depth string from the data source (e.g. `"81.00~84.00"`). Multi-interval screens show multiple ranges. |
| `well_depth_m` | Total borehole depth of the well (m). |
| `assignment_method` | How the well was matched to this layer — see below. |
| `note` | Human-readable explanation of the assignment (depth gap, layer range, proxy GWL station if applicable). |
| `feather_file` | **Per-row** path to the GWL source timeseries feather file (under `data/gwl/well_timeseries/`) containing this well's data. Different layers of the same MLCW station may point to different feather files. Example: `data/gwl/well_timeseries/HONGLUN_gwl_timeseries.feather`. Note: this column points to the **source** well-timeseries files (daily rows, columns = wellcodes). The MLCW-timeline-aligned version of each assignment is stored separately under `data/gwl/mlcw_gwl_timeseries/` — see below. |
| `dist_to_gwl_m` | Horizontal (2D) distance in meters from the MLCW station to the GWL station whose well was selected. Use this to audit which assignments pull from distant proxy stations. |

---

## What the assignment methods mean (updated)

**`DIRECT_MATCH`** (126 rows, 65%) — The well's screen midpoint falls **inside** the layer's depth range. Ideal case: the well is screened within the same aquifer unit. Example: TUKU F2 (50–123 m) matched to TUKU well 09050321 (screen 81–84 m, midpoint 82.5 m).

**`NEAREST_FALLBACK`** (69 rows, 35%) — No well within 10 km has a screen midpoint inside this layer, so the **closest well by vertical depth** is assigned. The algorithm searches ALL GWL stations within 10 km, not just the co-located one. Common for:

- **F1** (shallow aquifer): most wells are screened deeper than F1.
- **F4** (deepest aquifer): most wells don't reach that deep.
- **T1, T2** (clay aquitards): wells are never screened in clay — the nearest adjacent aquifer well is used. This is physically correct: clay compaction responds to head changes in adjacent sand units.

**`FULLY_BLOCKED`** (0 rows) — Retained as a possible value but unused in the current output. Would indicate no GWL station within 10 km has valid screen depths. The expanded 10 km radius eliminated all previously blocked stations.

---

## How to read a row (updated examples)

### TUKU F1 — the showcase improvement

**Old assignment:** TUKU well 09050321 (screen 81–84 m, midpoint 82.5 m, NEAREST_FALLBACK, depth gap = 57 m).

> TUKU's F1 is shallow (8.8–25.6 m), but all three TUKU wells are screened at F2/T2/F3 depths (82.5 m, 177.5 m, 260 m). The old algorithm settled for a 57 m depth gap because it never looked beyond TUKU's own wells.

**New assignment:** HONGLUN well 09050111 (screen 13–31 m, midpoint 22.0 m, DIRECT_MATCH, 4.3 km away).

> HONGLUN has a well screened at 13–31 m — its midpoint (22.0 m) falls squarely inside TUKU's F1 range (8.8–25.6 m). Despite being 4.3 km away, this well provides a physically meaningful piezometric head measurement for the shallow F1 aquifer. The algorithm chose it over TUKU's own wells because depth match (DIRECT_MATCH vs. 57 m gap) outweighs distance.

### ANNAN F2 — unchanged, still DIRECT_MATCH

> ANNAN's F2 layer spans 67.6–132.9 m depth. Well 09140111 (at HEFENG GWL station), screened at 80–110 m (midpoint 95.0 m), falls inside this range. This is a direct physical correspondence.

### TUKU F4 — cross-station improvement

**Old:** TUKU well 09050341 (screen 257–263 m, midpoint 260 m, gap = 23 m from F4 bottom at 283 m).

**New:** LIUZHUANG well 09080251 (screen 270–294 m, midpoint 282 m, NEAREST_FALLBACK, gap = 1 m, 6.1 km away).

> TUKU's deepest well stops at 263 m, leaving a 20 m gap to F4 (283–300 m). LIUZHUANG has a well screened at 270–294 m — its midpoint (282 m) is only 1 m above F4. The algorithm trades 6 km of horizontal distance for a 22$\times$ improvement in vertical depth match.

---

## Station Assignment Summary (37 stations)

Each row shows one MLCW station and the diversity of GWL sources assigned to its layers.

| Station | Layers | Direct | Fallback | GWL Stations | Feather Files | Max Dist (m) | Own Wells Used |
|---|---|---|---|---|---|---|---|
| ANHE | 5 | 3 | 2 | 2 | 2 | 6,579 | 3 |
| ANNAN | 6 | 5 | 1 | 4 | 4 | 7,545 | 0 |
| BEICHEN | 4 | 3 | 1 | 3 | 3 | 9,005 | 0 |
| CANLIN | 4 | 4 | 0 | 3 | 3 | 9,502 | 0 |
| DONGGUANG | 6 | 3 | 3 | 4 | 4 | 8,875 | 3 |
| DONGSHI | 4 | 2 | 2 | 2 | 2 | 8,494 | 3 |
| ERLUN | 4 | 3 | 1 | 2 | 2 | 9,650 | 0 |
| FENGAN | 4 | 3 | 1 | 4 | 4 | 9,386 | 0 |
| FENGRONG | 4 | 3 | 1 | 3 | 3 | 8,058 | 2 |
| GUANGFU | 4 | 4 | 0 | 3 | 3 | 6,060 | 0 |
| HAIFENG | 4 | 4 | 0 | 4 | 4 | 6,829 | 1 |
| HONGLUN | 5 | 4 | 1 | 3 | 3 | 8,640 | 2 |
| HUNAN | 5 | 3 | 2 | 4 | 4 | 8,913 | 0 |
| HUWEI | 5 | 4 | 1 | 4 | 4 | 9,864 | 1 |
| JIANYANG | 5 | 2 | 3 | 3 | 3 | 9,606 | 0 |
| JIAXING | 6 | 3 | 3 | 5 | 5 | 9,759 | 2 |
| JIUZHUANG | 6 | 5 | 1 | 3 | 3 | 8,818 | 0 |
| KECUO | 6 | 3 | 3 | 4 | 4 | 6,952 | 0 |
| LONGYAN | 5 | 3 | 2 | 3 | 3 | 6,542 | 0 |
| NANGUANG | 6 | 6 | 0 | 4 | 4 | 7,466 | 0 |
| NEILIAO | 6 | 3 | 3 | 3 | 3 | 9,961 | 0 |
| QIAOYI | 6 | 3 | 3 | 3 | 3 | 9,720 | 0 |
| TANQIFENXIAO | 6 | 4 | 2 | 3 | 3 | 8,910 | 0 |
| **TUKU** | **6** | **3** | **3** | **5** | **5** | **9,606** | **2** |
| XIGANG | 5 | 3 | 2 | 2 | 2 | 8,019 | 3 |
| XINGHUA | 6 | 4 | 2 | 5 | 5 | 7,894 | 0 |
| XINJIE | 6 | 3 | 3 | 4 | 4 | 9,643 | 0 |
| XINPI | 5 | 2 | 3 | 2 | 2 | 9,112 | 0 |
| XINSHENG | 6 | 4 | 2 | 4 | 4 | 8,200 | 0 |
| XINXING | 6 | 5 | 1 | 4 | 4 | 9,850 | 0 |
| XIUTAN | 6 | 3 | 3 | 5 | 5 | 7,056 | 0 |
| XIZHOU | 4 | 3 | 1 | 3 | 3 | 6,483 | 2 |
| YIWU | 6 | 2 | 4 | 3 | 3 | 7,742 | 3 |
| YUANCHANG | 6 | 3 | 3 | 5 | 5 | 9,822 | 0 |
| ZHENGMIN | 5 | 4 | 1 | 4 | 4 | 9,770 | 0 |
| ZHENNAN | 6 | 4 | 2 | 5 | 5 | 9,561 | 0 |
| ZHUTANG | 6 | 3 | 3 | 4 | 4 | 8,834 | 2 |

**Key observations:**

- **37 of 37 stations use wells from 2+ GWL stations** — mixed feather files are now the norm.
- **9 stations have zero "own" wells** (all layers assigned to proxy GWL stations). These are stations that either lack co-located GWL wells entirely, or whose own wells are poor depth matches for all layers.
- Stations with fewer GWL stations nearby (DONGSHI: 2, ERLUN: 2, XIGANG: 2, XINPI: 2) still get valid assignments thanks to the 10 km radius.
- Median assignment distance is 4,865 m; 92 of 195 rows (47%) use wells from >5 km away.

---

## Distance Distribution

| Range | Rows | % |
|---|---|---|
| < 1 km | 48 | 25% |
| 1–5 km | 55 | 28% |
| 5–10 km | 92 | 47% |

The long tail reflects the reality that shallow F1 layers and deep F4 layers often lack nearby wells with appropriate screen depths. The algorithm accepts these distances when the depth match justifies them.

---

## JSON sidecar

**`data/gwl/gwl_to_mlcw_layer_assignment.json`** (195 entries)

Auto-generated by `extend_layer_assignment.py` alongside the CSV. Contains the same 195 assignment rows as a JSON array of objects. Used for programmatic access in scripts that prefer JSON configs (e.g. IHM-F pipeline) without needing to parse the CSV.

Example entry:
```json
{
  "station": "TUKU",
  "layer": "F1",
  "assigned_wellcode": "09050111",
  "feather_file": "data/gwl/well_timeseries/HONGLUN_gwl_timeseries.feather",
  "assignment_method": "DIRECT_MATCH",
  "dist_to_gwl_m": 4300,
  "screen_mid_m": 22.0
}
```

---

## Related data structures

### GWL timeseries folders

Two folders hold GWL timeseries data at different levels of processing:

**`data/gwl/well_timeseries/`** (100 files)
- One feather file per GWL monitoring station.
- Naming: `{GWL_STATION}_gwl_timeseries.feather`
- Structure: `datetime` column (2000-01-01 to 2025-12-31, 9,497 daily rows) + one column per wellcode (8-digit string, e.g. `10070111`). Values are piezometric head in metres above mean sea level.
- This is the **source** data. The `feather_file` column in `gwl_to_mlcw_layer_assignment_v4.csv` points here.

**`data/gwl/mlcw_gwl_timeseries/`** (189 files)
- One feather file per MLCW station $\times$ layer assignment pair.
- Naming: `{MLCW_STATION}_{GWL_STATION}_{wellcode}.feather` (e.g. `TUKU_HONGLUN_09050111.feather`)
- Structure: 2 columns — `datetime` (aligned to the MLCW monitoring timeline) and a single GWL column named `{MLCW_STATION}_{GWL_STATION}_{wellcode}`. Values are piezometric head in metres above mean sea level.
- These are **derived** files generated by `extract_gwl_timeseries_pair_mlcw.txt`. They are the primary GWL input for GWL-driven model calibration — each file is already trimmed and aligned to the MLCW epoch calendar, so no further date-join is needed.
- Note: 195 assignment rows but only 189 feather files — 6 rows share feather files with other rows at the same station (same GWL well assigned to multiple layers).

### MLCW layer-grouped folders

Three folders hold per-station MLCW data aggregated from 60 magnetic rings to hydrogeological layers (F1, T1, F2, T2, F3, F4):

**`data/mlcw/group_byLayer_reconstr/`** (74 files: 37 $\times$ `_reconst_grouped.csv` + 37 $\times$ `_classify_table.csv`)
- Signal-reconstructed ring values, then summed by layer.
- Naming: `{STATION}_reconst_grouped.csv` and `{STATION}_classify_table.csv`
- Covers 37 stations (JINHU_XIN and LUNFENG_XIN excluded — data quality).
- **Primary MLCW input for GWL-driven model calibration.**

**`data/mlcw/group_byLayer_orig/`** (78 files: 39 $\times$ `_orig_grouped.csv` + 39 $\times$ `_classify_table.csv`)
- Raw-summed ring values (no signal reconstruction), summed by layer.
- Naming: `{STATION}_orig_grouped.csv` and `{STATION}_classify_table.csv`
- Covers 39 stations (all MLCW stations, including JINHU_XIN and LUNFENG_XIN).
- Used for 2S-TOOL calibration runs; also serves as the unprocessed reference for cross-checking against signal-reconstructed data.

**`data/mlcw/group_byLayer_modeled/`** (74 files: 37 $\times$ `_modeled_grouped.csv` + 37 $\times$ `_classify_table.csv`)
- IHM-F model predicted per-layer compaction timeseries (GWL-driven model output).
- Naming: `{STATION}_modeled_grouped.csv` and `{STATION}_classify_table.csv`
- Covers 37 stations. Written by the IHM-F v2/v3 model fitters (`fit_ihm_f_v2.py` / `fit_ihm_f_v3.py`). Currently contains TUKU-only output; full-station batch runs are pending (no v3 batch runner exists yet).
- **GWL-driven model output, not a calibration input.** Do not use as input to other pipeline stages.

### Well metadata

**`data/gwl/well_info/gwl_allwells_flat.csv`** (300 rows $\times$ 11 columns)

Columns: `station`, `wellcode`, `well_depth_m`, `well_screen_str`, `well_elev_m`, `x_twd97`, `y_twd97`, `screen_top_m`, `screen_bot_m`, `elev_leveling_m`, `elev_DEM_m`

**Canonical elevation column (updated 2026-05-26): `elev_leveling_m`.**
This is the well elevation from 2023 geodetic leveling + Kriging interpolation ($\pm$ cm accuracy). Use this column for all head-to-depth conversions:

```
gwl_depth_m = elev_leveling_m − piezometric_head_m_msl
```

Do not use `well_elev_m` (original well record, less accurate) or `elev_DEM_m` (20 m digital elevation model). The 2S-TOOL inputs and `hp_inicial_overrides.json` were regenerated with `elev_leveling_m` on 2026-05-26.

---

## Data Reconciliation Notes

### Naming discrepancies (2026-05-21)

| Station | Excel Well ID (Source) | Physical Feather ID (Actual) | Status |
|---|---|---|---|
| **DONGSHI** | `100911T1` | `10090111` | Mapping Updated |
| **TUKU** (Proxy) | `09030212` | `09030211` | Mapping Updated |
| **XIGANG** | `07240212` | `07240213` | Mapping Updated |
| **ZHUTANG** | `072511M2` | `07250111` | Mapping Updated |

### File naming (updated 2026-06-03)

The active assignment CSV is **`gwl_to_mlcw_layer_assignment_v4.csv`** (195 data rows $\times$ 17 columns). Updated from v3 on 2026-06-04 with 13 wellcode fixes (improved coverage_2023_2025 all $\ge$ 100). V3 and earlier are retained for reference but are superseded.

**Path inconsistency (2026-06-03):** The generating script `extend_layer_assignment.py` writes to the **unversioned** path `data/gwl/gwl_to_mlcw_layer_assignment.csv` (matching `paths.py` `GWL_ASSIGNMENT`). If the file is locked, it falls back to `gwl_to_mlcw_layer_assignment_v2.csv` — **not** `_v3.csv`. This is a naming bug: the fallback path still carries the v2 suffix. The `_v3.csv` named file was placed manually. After re-running the generator, copy the output to `_v3.csv` to keep the versioned copy in sync, or update the script to write `_v3.csv` directly.

---

## Practical tips for downstream consumers

**Per-row `feather_file` loading is required.** Unlike the old output (where all layers for a station shared one feather file), the current output may assign different layers to different GWL stations. Scripts must load the `feather_file` specified in each row, not assume `{station}_gwl_timeseries.feather`.

**Use `mlcw_gwl_timeseries/` for GWL-driven model calibration, not `well_timeseries/`.** The 189 pre-aligned feather files in `mlcw_gwl_timeseries/` are already trimmed to the MLCW timeline. Loading from `well_timeseries/` requires an additional date-join step. The `feather_file` column in the assignment CSV points to `well_timeseries/` as the source; derive the `mlcw_gwl_timeseries/` path as `data/gwl/mlcw_gwl_timeseries/{MLCW}_{GWL}_{wellcode}.feather`.

**The `dist_to_gwl_m` column is your audit trail.** Sort or filter by this column to identify assignments that pull from distant proxy stations (>8 km). These are physically justified when nearby wells lack appropriate screen depths, but they deserve extra scrutiny.

**Note on `paths.py`:** The project path resolver (`paths.py`) defines `GWL_ASSIGNMENT = data/gwl/gwl_to_mlcw_layer_assignment.csv` (unversioned). As of 2026-06-01, the unversioned file and `_v3.csv` are identical (both 195 rows). However, if you copy `_v3.csv` elsewhere or rely on the `_v3` suffix, be aware that `paths.py` and `extend_layer_assignment.py` both use the bare `.csv` name. The `_v3.csv` copy is a manual snapshot — verify it stays in sync after regeneration.

**Updated downstream scripts** (all support per-row feather loading):
- `scripts/09_trackB/prepare_2stool_inputs.py`
- `scripts/09_trackB/generate_hp_overrides.py`
- `scripts/09_trackB/_check_inputs.py`
- `scripts/09_trackB/batch_run_2stool.py`
- `scripts/notebooks/prepare_gwl_timeseries_match_mlcw.py`
- `mlcw_inspector/` — interactive Panel/HoloViews dashboard (loads assignments via `data_mapper.py`)

**The generating script** is `scripts/04_gwl_processing/extend_layer_assignment.py`. It uses `all_pairs_10km` from `data/mlcw/MLCW_InSAR_GWL_pairs.xlsx` (regenerated by `scripts/05_pairing/build_mlcw_insar_gwl_pairs.py` with `RADIUS_M = 10000`).
