> **ARCHIVE (2026-05-19):** This is the pre-trimming version (1419 lines) of the project work diary.
> The canonical current version is at `D:\112_PROJECT_002\discussions\discussion_memory.md`
> (431 lines, last updated 2026-05-29). This archive preserves detailed Chapters 1–14 narrative
> that was condensed during the rewrite. Use the canonical version for current project context;
> consult this archive for historical detail only.

# Discussion Memory: InSAR-MLCW-GPS Integration for Land Subsidence Monitoring
**Last updated: 2026-05-19 (Chapter 14 added: GWL feather export, linkage diagnostic; Section 3.5 updated with feather file details and data-quality flags)**

---

## 1. Research Objective and Scientific Context

Taiwan's Choushui River Alluvial Fan has been sinking for decades. At its worst — along the coast during the 1990s aquaculture boom — the land surface was dropping more than 160 mm per year. Fields drowned in storm surges that would once have drained harmlessly. Roads cracked and sank. Drainage systems that once moved water inland began moving it the wrong direction. Infrastructure built for a stable ground surface was now embedded in one that was not.

The mechanism is well understood. Farmers and fish farms draw water from aquifers at rates faster than natural rainfall can recharge them. When water leaves the pore spaces between sediment grains, the grains compact under the weight of the rock and soil above. Clay layers — the low-permeability barriers (aquitards) that separate the four main aquifer units — compress slowly and, in many cases, permanently. The land sinks. When pumping stops or slows, some sandy layers partially recover. But clay does not: the deformation is largely irreversible. Each drought cycle, each spike in agricultural demand, adds another increment of permanent loss.

Understanding subsidence at this level of mechanism requires knowing not just that the surface moved, but which layer underground caused it — and how much. A satellite radar image can measure the total displacement of the ground surface to sub-centimetre precision. But a surface displacement of 20 mm could mean 20 mm of compaction in a single shallow aquifer, or 5 mm each from four aquifer units spread across 300 m of depth. The regulatory response differs completely between these two cases. Regulators who want to reduce pumping from the most compressible layer need to know where that layer is — and how much of the total observed subsidence originates there.

This depth-stratification problem explains the need for the project. The Choushui River Alluvial Fan (CRAF) spans approximately 2,000–2,400 km² in central-western Taiwan. Its stratigraphy grades from gravel-dominated proximal deposits near the mountains — relatively stable, with limited compressible clay — to fine-grained, clay-rich distal deposits near the coast, where compaction is largest and most spatially variable. The fan is underlain by four aquifer units (F1–F4, from shallow to deep) separated by three clay-dominated aquitards. A network of 39 Multi-Layer Compaction Monitoring Wells (MLCW) — borehole instruments with magnetic extensometers at irregular depth intervals — measured compaction layer by layer from the surface to 300 m depth across the fan from 2015 onward.

In November 2021, budget constraints led the Water Resources Agency (WRA) to shut down 20 of the 39 MLCW stations. The remaining 19 continue to operate as of 2025. The budget trajectory points toward further reductions: by the late 2020s, the active network may shrink to five stations or fewer, and cannot be assumed to persist indefinitely.

This network-shrinkage problem reframed the project objective. Three transferability classes describe how dependent a method is on continued MLCW observations after calibration:

- **Class I** — the method was trained on historical MLCW data, but once trained it produces compaction estimates for future epochs using only InSAR and groundwater level (GWL) data. No further MLCW measurements are needed.
- **Class II** — the method requires periodic recalibration from a small number of surviving MLCW stations (approximately five or more). Prediction accuracy degrades gradually as the station count falls, but the method does not fail entirely.
- **Class III** — the method produces a static field fixed at the calibration date. It cannot incorporate any new observation after the calibration window closes. Its predictions become less reliable as the pumping regime or geological state evolves.

The current static baseline (f̄_k interpolated by inverse-distance weighting) and the kriging upgrade planned in Chapter 15 are both Class III. The project aimed to develop a Class I or Class II method that produces accurate 3D compaction estimates using InSAR and GWL data even after the calibration window closes. Three candidate methods — Terzaghi S_sk inversion with Gaussian Process interpolation (Class I), LSTM temporal encoder (Class II), and GP in depth × space × time feature space (Class I/II) — are documented in `opus_research_ideas_predictive_20250515.md` and constitute the next phase of work.

Three stress-test scenarios define success:
- **(a) 19-station semi-blind validation (2021–2025):** How accurately does the method predict compaction at the 19 active stations when calibrated only from pre-2021 data?
- **(b) Network degradation experiment:** How does prediction RMSE degrade as the number of active stations drops from 39 to 5 to 0?
- **(c) Zero-MLCW epoch prediction:** Can InSAR + GWL data alone produce a physically defensible 3D compaction estimate after MLCW monitoring ends entirely?

The work reported in this document addresses scenarios (a) and the foundational calibration work required for all three.

---

## 2. Study Area

The Choushui River Alluvial Fan (CRAF) encompasses approximately 2,000 to 2,400 km² in central-western Taiwan. The basin is bounded by the Wu River (north), Pekang River (south), Bagua Tableland and Douliu Hills (east), and the Taiwan Strait (west). Subsurface sediments consist of slate, metamorphic quartzite, shale, sandstone, and mudstone, with deposit thicknesses ranging from 750 to 3,000 meters.

**Geomorphological Zonation & Sediment Composition:**
Driven by frequent marine transgressions and channel migrations, the fan exhibits a highly heterogeneous, eastward-coarsening structure:
- **Proximal fan (east):** Dominated by highly permeable gravel and coarse sand (hydraulic conductivity up to $10^{-3}$ m/s). It functions as an unconfined, principal groundwater recharge zone with minimal depth stratification and low compressibility.
- **Middle fan:** A transitional environment characterized by inter-bedded layers of sand and mud, marking the onset of distinct aquitards (e.g., T1, T2).
- **Distal fan (west):** Composed of interlaced lenses of highly compressible fine sand, silt, and clay ($10^{-5}$ m/s). It exhibits complex depth stratification and severe susceptibility to consolidation.

**Hydrogeological Stratigraphy (Upper 300m):**
The upper 300 meters stratify into four distinct non-marine aquifers (F1–F4) separated by marine mud aquitards (T1–T3). These units merge into a single unconfined aquifer in the proximal fan but become distinctly confined in the middle and distal fan.
- **Aquifer F1:** Depth 19–103 m; average thickness 42 m.
- **Aquifer F2:** Depth 35–107 m; average thickness 95 m. It is the thickest, most laterally extensive unit and the primary source for agricultural, industrial, and aquacultural extraction.
- **Aquifer F3:** Depth 140–275 m; average thickness 86 m.
- **Aquifer F4:** Depth 238–300 m; average thickness 24 m.

**Compaction Dynamics & Subsidence History:**
- **Vertical Distribution:** Approximately 50% of major compaction occurs in the shallow layers (upper 100 m). However, deep groundwater extraction induces significant consolidation in Aquifers 3 and 4; compaction below the 300-meter bedrock anchor contributes 10–20 mm/yr to total vertical displacement in areas like Xizhou and Tuku.
- **Spatiotemporal Migration:** Historically, coastal aquaculture in the 1990s drove peak subsidence exceeding 160 mm/yr (e.g., Dacheng, Mailiao). Due to coastal pumping restrictions, the subsidence depocenter has migrated inland toward the middle fan (Tuku, Yuanchang) driven by agricultural extraction, with current rates ranging between 30 and 70 mm/yr.
- **Environmental Forcing:** Severe droughts, such as the 2020–2021 event, act as threat multipliers, causing subsidence velocities to spike by up to 50% (reaching 78 mm/yr). Furthermore, recent studies identify elastoplastic behavior in sandy layers, causing irrecoverable volumetric strains that exacerbate total subsidence beyond traditional clay consolidation models.

Reference files: `D:\110_PROJECT_002\resources\study_area.md`, `D:\110_PROJECT_002\resources\mlcw_info.md`

---

## 3. Datasets

All data and scripts live under the base directory:
`D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\` (referred to as `BASE` below).

### 3.1 MLCW (Multi-Layer Compaction Monitoring Wells)

**Raw input files**

| File | Description |
|------|-------------|
| `BASE\data\mlcw\raw_timeseries\{STATION}_ringbyring.csv` | Raw ring displacement: datetime index + one column per magnetic ring named by its depth in metres (e.g. `8.775`, `11.938`, `25.605`). Units: mm. Sign: negative = subsidence. 20–26 rings per station at irregular depths determined by stratigraphic boundaries. Some stations have a trailing all-NaN column (e.g. TUKU col `294.698`) — excluded during processing. |
| `BASE\MLCW_data_timeline.csv` | Station metadata: Ename, lon, lat, start_date, end_date, num_of_obs |

**Physical measurement principle:** A borehole casing is anchored in consolidated material at ~300 m. Each magnetic ring floats freely in the surrounding sediment. When the sediment between a ring and the base below compacts, the ring descends — recorded as negative displacement. Each ring value is the net cumulative compaction of the column from that ring down to the anchor. Summing rings bottom-up to depth d gives total compaction from d to the borehole bottom.

Rings are at irregular depths (20–26 rings per well) determined by stratigraphic boundaries. The shallowest ring depth varies widely across stations: 1.2 m (JIAXING) to 37.7 m (DONGSHI). A subset of stations — including DONGSHI (37.7 m), GUANGFU (28.9 m), FENGAN (19.0 m), XINJIE (17.0 m), JIANYANG (14.3 m), HONGLUN (14.0 m), XIGANG (13.1 m), XINXING (12.0 m) — have no ring in the uppermost 10 m, reflecting local instrument installation constraints or stratigraphic choices.

**Processing pipeline (3 steps, all complete for all 39 stations)**

**Step 1 — Parametric decomposition**
Script: `BASE\batch_process_MLCW.py`

- Input: `data/mlcw/raw_timeseries/{STATION}_ringbyring.csv`
- Calls `appsigsolv.cli.cmd_decompose.run_decompose` per station (library at `D:\1000_SCRIPTS\004_Project003\20260501_timeseries_signal_solver`)
- Key parameters:
  - `periods = "0.5, 1"` — fits annual (1 yr) and semi-annual (0.5 yr) harmonics
  - `auto_periods = 4`, `sigma_min = 2.0`, `sigma_max = 20.0` — significance testing: only components where signal-to-noise exceeds threshold are retained
  - `poly_deg_min = 1` — polynomial trend at least degree 1; offset-only (degree 0) excluded
  - `irregular = True` — handles non-uniform observation cadences
- Output: `data/mlcw/decomposed/{STATION}_ringbyring/` — one JSON model file per ring:
  `{STATION}_ringbyring_model_{depth}.json`

**Step 2 — Reconstruction at uniform output dates**
Script: `BASE\batch_reconstruct_MLCW.py`

- Input: JSON model files from `data/mlcw/decomposed/{STATION}_ringbyring/` + source CSV
- Reconstructs each ring's timeseries as `G_out @ m_est` — the full fitted model evaluated at the regular output dates: days [1, 6, 11, 16, 21, 26] of every month (6 dates per month, approximately 5-day cadence aligned to InSAR)
- Retains **all statistically significant components**: trend + any retained seasonal harmonics + detected jumps/steps. Only the residual noise is discarded. The output therefore contains **trend + seasonal (where retained) + jumps** — not trend only. No exponential/logarithmic relaxation terms (`no_relax=True`).
  - Candidate seasonal periods: 0.5 yr and 1 yr are always included; up to 4 periods total may be auto-detected via FFT screening. Periods are retained only if statistically significant for that ring.
- Output: `data/mlcw/reconstructed/{STATION}_ringbyring_reconstructed.csv`
  — datetime index + one column per ring at original irregular depths, mm
  — Shape: 217–1892 rows (epochs) per station; 20–28 columns (rings)
  — Data quality: noise-reduced, smooth parametric reconstruction; seasonal oscillations present only at depths where they were statistically significant in the original timeseries

**Step 3 — 5 m depth regularisation**
Script: `BASE\mlcw_5m_grid.py`

- Input: `data/mlcw/reconstructed/{STATION}_ringbyring_reconstructed.csv`
- Processing chain per epoch:
  1. Exclude all-NaN ring columns
  2. Bottom-up cumulative sum of ring values → cumulative compaction depth profile
  3. Surface extrapolation: least-squares linear fit through the 3 shallowest rings, evaluated at depth = 0 (avoids the two-point noise sensitivity of the original gradient method)
  4. PCHIP interpolation to uniform 5 m grid [0, 5, 10, … 300 m]; 300 m anchor fixed at 0.0 mm (physical boundary condition: zero compaction at the concrete borehole base). The 300 m anchor eliminates near-flat artefacts at adjacent deep levels for stations whose deepest ring is shallower than 300 m. Previously, a linear gap-fill between z_deepest and 300 m was used, which produced near-identical values at depth_290m and depth_295m for 13 stations.
  5. Difference adjacent grid levels → 60 individual 5 m layer displacements (`depth_000m` to `depth_295m`)
  - PCHIP validation tolerance: max residual ≤ 0.5 mm at original ring depths; epochs exceeding this are flagged
- Output: `data/mlcw/regular_5m/{STATION}_5m_grid.csv`
  — datetime + 61 columns (`depth_000m` to `depth_300m`), mm
  — Shape: 217–1892 rows × 62 columns; no NaN padding (all valid epochs included)

**Data summary:**
- Total epochs across all stations: ~44,700 (39 × average 1,146 epochs/station)
- Common date range: varies per station (1995–2025); matched InSAR epochs per station: 214–771 of 785 (varies by MLCW record start date)
- Row sum ≈ total compaction in 0–300 m column (e.g., TUKU mean = -457 mm)
- Value range: approximately -40 to +2.6 mm per layer (physically reasonable)

**Baseline alignment for regression:**
MLCW 5 m grid values are absolute cumulative compaction since instrument installation (~2003). InSAR values are cumulative displacement from the 2015-01-16 reference epoch. To use both in the same regression, MLCW values at each epoch are expressed relative to that reference epoch by subtracting the MLCW value at 2015-01-16:
```
Y_aligned(s, t, k) = MLCW(s, t, k) − MLCW(s, 2015-01-16, k)
```
If a station's record does not include 2015-01-16, zero is used as the reference (flagged in loader warnings). Training data scope is limited to InSAR epoch dates (2015-01-21 onward); pre-2015 MLCW data is excluded. Date matching is performed by exact calendar date (YYYYMMDD integer key), not interpolation — unmatched InSAR epochs receive NaN and are excluded from the regression.

#### Prediction target: the 60-point displacement vector

Each row of `{STATION}_5m_grid.csv` at epoch t provides the **prediction target** for the regression: a 60-point vector of individual ring displacements on the uniform 5 m grid:

```
[d(0m,t), d(5m,t), d(10m,t), ..., d(295m,t)]
```

Each value equals the compaction of the imaginary 5 m layer at that depth, directly analogous to a single ring column in `ringbyring.csv`. The processing chain that produces this vector is Steps 1–4 above; the key physical details are:

**d(0m, t) — the surface imaginary ring:**
- Represents displacement of the ground surface relative to the ~300 m concrete foundation
- This is NOT the InSAR value — different reference frame, different integration depth
- d(0m) ≈ total compaction within the 0–300 m monitored column only
- Extrapolated (not measured); included in the model with small effective weighting due to higher uncertainty

**Step 1 — Bottom-up cumulative sum** (per epoch, per station):
```python
cumsum_row = np.cumsum(row[::-1])[::-1]
```
Each element at depth z_k equals total compaction from z_k down to the deepest valid ring.

Example (TUKU, 2025-10-02, 23 valid rings):
- Original ringbyring row: `[0.525, -8.508, -18.541, ..., -16.692]`
- After cumsum:            `[-769.99, -761.48, -742.94, ..., -16.692]`
- Value at 8.775 m = −769.99 mm = total compaction from 8.775 m to 288.7 m

**Step 2 — Near-surface extrapolation to depth = 0:**
```python
slope, intercept = np.polyfit(ring_depths[:3], cumsum_row[:3], 1)
d(0m) = intercept   # least-squares value at depth=0
```
Using three rings (rather than two) averages out near-surface measurement noise for a more stable surface estimate.

**Step 3 — PCHIP interpolation to uniform 5 m grid:**
Knots: `[0, z_ring1, z_ring2, ..., z_deepest]` with an explicit anchor `(300 m, 0)` appended when the deepest ring is shallower than 300 m. The anchor is the physical boundary condition of the instrument — cumulative compaction equals zero at the concrete base — and forces PCHIP to approach zero smoothly, eliminating near-flat artefacts at adjacent deep levels.

**Step 4 — Difference adjacent levels:**
```
d_individual(z_k, t) = cumulative_profile(z_k, t) - cumulative_profile(z_{k+1}, t)  for k = 0..58
d_individual(z_59, t) = cumulative_profile(z_59, t)                                   for k = 59
```
The deepest level k = 59 (depth_295m) equals the cumulative value at that depth because the 300 m anchor is zero. The 300 m anchor is used only as an interpolation constraint and is not included in the 60-point output.

### 3.2 GPS

| File | Description |
|------|-------------|
| `BASE\GPS_timeseries\{STATION}_neu.csv` | Daily: datetime, gpsdate, dN, dE, dU, sN, sE, sU |
| `BASE\GPS_data_timeline.csv` | Station metadata: station_co, lon, lat, height, start_date, end_date |
| `BASE\MLCW_GPS_pairs.csv` | Nearest GPS station per MLCW: Ename, station_co, distance (m) |
| `BASE\ratio_MLCW_over_GPS_RBF_interpolated.csv` | GNSS-derived α pre-computed via RBF spatial interpolation |

`dU` is cumulative vertical displacement since each station's own first observation, in mm (negative = subsidence). GPS velocity was used to derive the GNSS-derived compaction fraction α; GPS data were not used directly in Stage 2 spatial reconstruction.

**MLCW–GPS proximity tiers:**
- < 500 m (~20 stations): reliable GPS proxy
- 500 m – 3 km (~7 stations): moderate reliability
- > 3 km (~6 stations: ZHENNAN, ZHUTANG, FENGAN, JINHU_XIN, JIANYANG, DONGGUANG, TANQIFENXIAO): poor proximity — handled via GNSS velocity interpolation for α estimation

### 3.3 InSAR Timeseries Data

**Raw source:** Sentinel-1 ascending and descending track time series in MintPy HDF5 format (`vert_regts_msk.h5`), processed externally to vertical LOS displacement. Each pixel's displacement was modelled parametrically — trend, four harmonics (1 yr, 0.5 yr, 5 yr, 10 yr), piecewise velocity changes at breakpoints — and re-evaluated at regular dates. The feather files contain these parametric reconstructions, not raw interferograms.

**Critical:** InSAR measures total surface displacement relative to a far-field geodetic reference, integrating ALL compaction from surface to bedrock (including below 300 m). It is on a **different reference frame** from MLCW measurements. To use both in the same regression, MLCW values must be expressed relative to the InSAR reference epoch (2015-01-16) — see Section 3.1.

#### File 1: MLCW-location InSAR (`mlcw_interp_insar_IDW_extend.feather`)

- Shape: 39 rows × 791 columns
- Rows: one per MLCW station (matching the 39 stations in the MLCW 5 m grid)
- Columns: 6 metadata (`Ename`, `Code`, `X_UTM50N`, `Y_UTM50N`, `X_TWD97`, `Y_TWD97`) + 785 epoch columns (`D20150121` to `D20251211`, 5-day intervals)
- Each cell: cumulative InSAR surface deformation in **metres** (multiply by 1000 for mm); negative = subsidence
- Reference epoch: 2015-01-16; value range: −0.679 to +0.006 m; no missing values
- Coordinate systems: UTM Zone 50N (EPSG:32650) and Taiwan Datum 97 (EPSG:3826 — primary for this analysis)

#### File 2: 500 m grid InSAR (`gridpnt_500m_interp_insar_IDW_extend.feather`)

- Shape: 8,577 rows × 790 columns
- Rows: one per regular 500 m spatial grid point across CRAF
- Columns: 5 metadata (`PointKey`, `POINT_X`, `POINT_Y`, `X_TWD97`, `Y_TWD97`) + 785 epoch columns (identical temporal grid to File 1)
  - `PointKey` = `'X' + str(int(X_TWD97*1000)) + 'Y' + str(int(Y_TWD97*1000))`
  - `POINT_X`, `POINT_Y`: UTM Zone 50N (EPSG:32650)
- Each cell: cumulative InSAR surface deformation in metres; reference epoch 2015-01-16
- Spatial extent (TWD97): X ∈ [162,441, 220,441], Y ∈ [2,600,661, 2,676,661]; value range: −0.934 to +0.016 m
- Missing values: ~44,950 NaN (~0.67%), concentrated at coastal/out-of-bounds areas — **drop any grid row containing NaN before Stage 2**; ~8,500+ valid grid points remain

#### Processing pipeline (how the feather files were produced)

The InSAR data in both feather files is not raw interferometric observations. It is the output of a multi-stage parametric modelling and reconstruction pipeline, documented in `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\scripts_2026_Apr_May\merge_tseries_notes.md`.

**Pre-processing by MintPy:** each pixel's LOS timeseries was corrected for solid earth tides (SET), ERA5 troposphere delay, orbital ramp, and DEM error before the pipeline below.

**Stage A — Adaptive parametric model fitting per pixel (OMT loop):**
Each pixel's LOS timeseries is fitted with an OLS parametric model:
```
d_model(t) = a0 + a1·t
           + b1·sin(2πt/1yr)  + c1·cos(2πt/1yr)       ← annual
           + b2·sin(2πt/0.5yr) + c2·cos(2πt/0.5yr)     ← semi-annual
           + b3·sin(2πt/5yr)  + c3·cos(2πt/5yr)        ← 5-year
           + b4·sin(2πt/10yr) + c4·cos(2πt/10yr)       ← 10-year
           + piecewise_linear_breakpoints(t)             ← velocity changes
```
Production model parameters per track:
- Ascending:  `--poly 1 --period 10 5 1 0.5 --polyline 20210301 20180701 20160301`
- Descending: `--poly 1 --period 10 5 1 0.5 --polyline 20200904 20180101 20151007`

**Stage B/H — Model projection onto regular 5-day grid:**
Scripts: `B_resample_timeseries_model.py`, `H_resample_timeseries_model.py`. The fitted model is evaluated at regular dates {1, 6, 11, 16, 21, 26} of each month (matching the MLCW output grid). Noise and residuals are discarded. Output is `G_proj @ m_params` — only what the parametric model captured.

**Stage C — Spatial crop.**

**Stage D — Date removal** (removal of specific problematic epochs).

**Stage E — Asc/Desc decomposition to vertical and horizontal:**
Linear combination of ascending and descending LOS model-reconstructed timeseries using known incidence angles to extract vertical (and east-west horizontal) components. No additional filtering.

**Stage G — Spatial subset** to the CRAF study area.

**Stage K — IDW spatial interpolation to MLCW station locations** (`K2_interp_timeseries_IDW.py`):
Weighted average over 10–20 nearest InSAR grid pixel neighbours using inverse-distance-squared weights. Produces `mlcw_interp_insar_IDW_extend.feather`.

**What the feather files contain — summary:**
The InSAR signal is a smooth analytical reconstruction containing: linear trend, annual + semi-annual + 5-year + 10-year harmonic components, piecewise linear velocity changes at specified breakpoints, and no noise or raw interferometric residuals.

**Implication for Stage 1 regression:**
Both the InSAR predictor (X_s) and the MLCW target (Y_s) are smooth parametric reconstructions evaluated on the same regular 5-day grid. The seasonal mismatch visible in per-depth fit plots therefore cannot be attributed to noise differences between the two signals. It arises from structural differences in the two modelling pipelines: InSAR includes 5-year and 10-year harmonics and piecewise velocity breakpoints that have no counterpart in the MLCW fitting (which uses only 0.5 yr and 1 yr periods with no piecewise breakpoints). See Section 8 (Results and Interpretation) for the full diagnosis of this structural limitation.

### 3.4 MLCW-GPS Station Pairs

| File | Description |
|------|-------------|
| `BASE\MLCW_GPS_pairs.csv` | Nearest GPS station per MLCW with Euclidean distance (m) |

Columns: `Code` (MLCW), `Ename`, `geometry`, `index_right`, `station_co` (GPS), `distance`

Distance tiers:
- **< 500m (~20 stations):** reliable GPS proxy
- **500m–3km (~7 stations):** moderate reliability
- **> 3km (~6 stations: ZHENNAN, ZHUTANG, FENGAN, JINHU_XIN, JIANYANG, DONGGUANG, TANQIFENXIAO):** poor proximity — handled via GNSS velocity interpolation (see Section 4)

### 3.5 Groundwater Level (GWL) — Depth-Discrete Piezometric Head

**Terminology note:** The GWL monitoring wells in this dataset are screened at specific depth intervals in confined aquifer units. Because confined aquifers are under pressure, the water level recorded at each screen is the **piezometric head** in that unit, not the unconfined water table. Multi-screen wells record independent piezometric head at each screen depth. "GWL" and "piezometric head" are interchangeable for this dataset. This distinction matters for model design: GWL records are depth-specific physical drivers of compaction, directly assignable to the aquifer unit nearest to each MLCW depth slab.

**GWL feather timeseries (exported 2026-05-19):**

The HDF5 GWL data has been exported to per-station feather files for direct use by analysis scripts:

| File | Description |
|------|-------------|
| `BASE\data\gwl\well_timeseries\{STATION}_gwl_timeseries.feather` | Per-station timeseries. 100 files. Schema: `datetime` (daily 2000-01-01 to 2025-12-31, 9,497 rows) + one float64 column per well, column name = numeric well code (e.g. `09050321`). Values in metres elevation (piezometric head). |
| `BASE\data\gwl\well_info\gwl_allwells_flat.csv` | CSV copy of `gwl_allwells_flat.xlsx`. **Primary join table** to link feather well codes to coordinates and screen depths. Join key: `wellcode` (flat CSV) = column name (feather). |
| `BASE\data\gwl\inspection_reports\gwl_feather_inspection.csv` | Feather structure summary: 100 rows, one per station. Columns: n_wells, well_codes, date range, n_rows_insar_window, per-well GWL stats. |
| `BASE\data\gwl\inspection_reports\gwl_linkage_report.csv` | Per-well linkage flag table: 306 rows. Full feather file path, coordinates, screen depths, boolean flags `coord_missing`, `screen_missing`, `no_metadata`, `is_mlcw_station`. |
| `BASE\data\gwl\inspection_reports\gwl_linkage_summary.txt` | Human-readable summary of all three linkage checks. |

**Inspection scripts:**
- `BASE\scripts\04_gwl_processing\inspect_gwl_feather.py` — reads one station (`--station TUKU`) or all 100 (`--all`); saves `gwl_feather_inspection.csv`
- `BASE\scripts\04_gwl_processing\check_gwl_linkage.py` — verifies all three linkages; saves `gwl_linkage_report.csv` and `gwl_linkage_summary.txt`

**Linkage diagnostic results (2026-05-19):**

Three checks were run on all 306 wells:

*Check A — timeseries ↔ metadata:* **CLEAN.** Every feather column name resolves to exactly one row in `gwl_allwells_flat.csv`, and every metadata row has a corresponding feather file. No orphans on either side.

*Check B — coordinates:* **6 wells have missing/zero coordinates.** None are MLCW-overlap stations so this does not block Stage 1.

| Station | Well code | Problem |
|---------|-----------|---------|
| DOULIU | 090111M2 | x=0, y=0 |
| GANYUAN | 07260111, 07260121 | NaN |
| XIABANTIAN | 10110211, 10110221 | NaN |
| ZHONGLIAO | 101111M3 | NaN |

*Check C — screen depths:* **120 / 306 wells (39.2%) lack screen_top_m / screen_bot_m.** The operationally important subset is **26 of 71 MLCW-overlap wells** at 15 stations. Without screen interval, a piezometric head cannot be assigned to a specific aquifer unit, which is required for the Terzaghi S_sk inversion pathway.

Stations where **all** wells lack screen depths (entire station blind): ERLUN, GUANGFU, KECUO, QIAOYI, XIUTAN, ZHENGMIN.
Stations with partial screen coverage: ANNAN (2 missing), JIAXING (2), XIGANG (5), XINGHUA (2), XIZHOU (4), ZHUTANG (2), XIGANG (5).

**Known environment issue:** The `fafalab` conda environment in this project has `PYTHONPATH` contaminated by `gemini_env` paths. All scripts under `scripts\04_gwl_processing\` must be run with `$env:PYTHONPATH = ""` prepended: `$env:PYTHONPATH = ""; conda run -n fafalab python <script.py>`.

**Raw source**

| File | Description |
|------|-------------|
| `D:\1000_SCRIPTS\004_Project003\20251229_Gwater_Levels\20260108_GWL_CRFP_daily_modeled.h5` | WRA permanent network: 306 wells, daily modelled GWL values, 2014–2025 |
| `D:\VINHTRUONG\001_STUDY_AREA\GroundwaterObservation\@DOWNLOAD_WRA_GWOB_YEARBOOK_PROJECT\Well_Info_2024.pdf` | WRA hydrological yearbook listing all 387 monitoring wells with screen depths (濾水管位置), casing depth, coordinates, and data period |

**Step 1 — GWL inspection and flat table**
Script: `BASE\inspect_gwater_data.py`

- Input: HDF5 above + InSAR feather (to define the InSAR overlap period 2015-01-21 to 2025-12-11)
- Uses `appgeopy.gwatertools` for HDF5 reading
- Key fix (Task P1, 2026-05-15): `well_screen_str` extracted using `_safe_str` not `_safe_float`; the HDF5 `Well_Screen(m)` attribute is a string (e.g. `'40.00~52.00'`), not numeric
- Output:

| File | Description |
|------|-------------|
| `BASE\gwl_inspection\gwl_allwells_flat.xlsx` | Per-well flat table: 306 wells × 30+ columns. Includes `screen_top_m` and `screen_bot_m` parsed from `well_screen_str` (183/306 wells have valid screen depths; 123 remain NaN). |
| `BASE\gwl_inspection\gwl_inspection_report.json` | Per-station JSON: well list, quality flags, yearly coverage. Patched 2026-05-17 — 8 wells had `well_screen_str = "nan"` or `""` in JSON but valid screen depths in PDF; these were corrected by writing the PDF-sourced strings into the JSON. |

**Key columns in `gwl_allwells_flat.xlsx`:**
- `well_depth_m` — total drill depth (m)
- `well_screen_str` — screen interval as tilde-delimited string (e.g. `'40.00~52.00'`); extracted from HDF5
- `screen_top_m`, `screen_bot_m` — numeric screen bounds parsed from `well_screen_str` (added Task P1, 2026-05-15)
- `well_elev_m` — ground surface elevation (m)
- GWL statistics: `gwl_min_m`, `gwl_max_m`, `gwl_mean_m`, `gwl_std_m`, `gwl_trend_m_per_yr`, `gwl_seasonal_amp_m`
- Coverage: `frac_valid_total`, `n_valid_insar_overlap`, `frac_valid_insar_overlap`

**Step 2 — WRA yearbook extraction (Task P2 equivalent, completed 2026-05-17)**

The WRA publishes well construction specs (screen depth `濾水管位置`, casing depth `井管深度`) in `Well_Info_2024.pdf`. This data does not exist in any open API — it must be extracted from the PDF. The extraction was done page-by-page using the DeepSeek LLM (`extract_well_info_deepseek.py`) with deterministic post-processing to separate the zone code (測區編號: `040`/`050`/`060`), screen depths, and data period from the merged PDF text.

| File | Description |
|------|-------------|
| `BASE\gwl_inspection\well_info_deepseek\Well_Info_2024_page_NNN_table.md` | 43 markdown files, one per PDF page. Each is an 11-column table (測區編號, 測區名稱, 井名, 電腦編號, X座標, Y座標, 井址, 井頂高, 井管深度, 濾水管位置, 資料起迄). |
| `BASE\gwl_inspection\well_info_combined.xlsx` | All 387 wells merged from the 43 markdown files. 12 columns. 178 wells have no screen depth (`-`) — these are newly commissioned wells, second-string wells at multi-well stations, pre-1990 piezometers, or wells in Zone 040/080 not covered by the yearbook. |
| `BASE\gwl_inspection\well_info_screen_comparison.xlsx` | Cross-check of `well_info_combined.xlsx` screen depths against `gwl_inspection_report.json`. 387 rows × 9 columns. Result categories: MATCH (183), json_missing (8, now patched), md_only (81), both_no_screen (115). |
| `BASE\gwl_inspection\well_info_combined.gpkg` | GeoPackage of all 387 wells (TWD97 coordinates) for GIS visualisation of the full monitoring network across zones 040, 050, 060. |
| `BASE\gwl_inspection\well_info_combined_screenAvail.gpkg` | GeoPackage filtered to ~209 wells with a valid screen depth (`screen_raw ≠ "-"`). |

**Scripts involved in the WRA yearbook pipeline:**
- `BASE\gwl_inspection\extract_well_info_deepseek.py` — calls DeepSeek API per page, applies `_fix_row_cells()` post-processing to separate zone code / screen / date; saves 43 markdown files to `well_info_deepseek\`
- `BASE\gwl_inspection\extract_well_info_direct.py` — deterministic regex-only extraction to `well_info_output\`; faster but lower quality than DeepSeek; used for spot-checks
- `D:\112_PROJECT_002\legacy\scripts\task_well_info_merge_check.py` — merges 43 markdown files into `well_info_combined.xlsx`; cross-checks screen depths vs. JSON; writes `discussion_well_info_check_20260516.md`
- `D:\112_PROJECT_002\legacy\scripts\patch_json_and_export_csv.py` — patches `gwl_inspection_report.json` for `json_missing` wells; exports Full Comparison Table to `well_info_screen_comparison.xlsx`

**Why 178 wells have no screen depth:** Four categories identified by web search (see `D:\112_PROJECT_002\legacy\discussions\discussion_missing_screen_depth_search_20260517.md`):
1. Newly commissioned wells (data start 2018–2024) — specs not yet published
2. Second-string wells (computer_id ending in `2`) at multi-well stations — primary well has specs; secondary often does not
3. Pre-1990 piezometers — pre-date systematic screen recording conventions
4. Zone 040/080 wells (Taichung/Nantou) — outside Choushui Fan study area; screen specs held by a different regional office

**Downstream parsing for Terzaghi S_sk inversion:**
```python
screen_top = float(well_screen_str.split('~')[0])
screen_bot = float(well_screen_str.split('~')[1])
```

**ANHE example (4 wells, one per aquifer unit):**

| wellcode | well_depth_m | well_screen_str | Aquifer |
|----------|-------------|-----------------|---------|
| 10070111 | 59.0        | 40.00~52.00     | F1      |
| 10070121 | 96.3        | 72.00~90.00     | F2      |
| 10070131 | 163.5       | 144.00~156.00   | F3      |
| 10070141 | 285.0       | 260.00~278.00   | F4      |

**MLCW–GWL co-location:** 21 of 39 MLCW stations have a co-located GWL station. The 18 stations without direct GWL coverage receive spatially interpolated head values from the 306-well network for Terzaghi S_sk inversion.

---

## 4. Compaction Fraction α: GNSS-Derived and InSAR-Derived (Completed)

**Physical definition:** α(s) is the fraction of total surface subsidence (surface to bedrock) attributable to compaction in the 0–300 m monitored column (MLCW). Each station receives one scalar α value, used as a prior constraint in the per-station W-vector regression via `Σ_k W_s[k] ≈ α(s)`.

---

### 5.1 GNSS-Derived α (original prior)

**Computation method (linear velocity ratio):**

1. A secular vertical velocity v_GPS(s) was fitted to each GNSS station with ≥ 5 years of continuous observation by removing seasonal and semi-annual components:
   `dU(t) = v·t + A·sin(2πt) + B·cos(2πt) + C·sin(4πt) + D·cos(4πt) + offset`

2. v_GPS was spatially interpolated to all 39 MLCW locations using RBF interpolation. Stations with < 5 years of GNSS data (ANNAN, JINHU_XIN, JIUZHUANG, LUNFENG_XIN, NANGUANG, ZHENGMIN) received RBF-interpolated values.

3. v_MLCW(s) was fitted to the total MLCW column compaction timeseries: `MLCW_total(s, t) = Σ all valid ring values at epoch t`

4. `α_gnss(s) = v_MLCW(s) / v_GPS_interp(s)` (both velocities are negative → α is positive)

**Output files (completed):**
- `MLCW_GPS_velocity_TWD97_v2.csv` — original 33-station table; columns: STATION, MLCW_mmyr, GPS_mmyr, Ratio, X_TWD97, Y_TWD97
- `ratio_MLCW_over_GPS_RBF_interpolated.csv` — 39 stations; columns: Code, Ename, X/Y_WGS84, X/Y_TWD97, Imputed_Ratio
  - 6 RBF-interpolated stations: ANNAN=0.826, JINHU_XIN=0.348, JIUZHUANG=0.830, LUNFENG_XIN=0.856, NANGUANG=0.735, ZHENGMIN=0.663

---

### 5.2 InSAR-Derived α (new alternative prior)

**Motivation:** GNSS-based α relies on the RBF-interpolated velocity field at locations without a co-located GNSS station. For stations far from any GNSS benchmark (e.g., TANQIFENXIAO, ANHE at > 3 km), the interpolated v_GPS may be unreliable, producing extreme α values. InSAR provides direct vertical velocity at every MLCW location without any spatial interpolation, offering an independent check and potentially better-constrained α at stations remote from GNSS.

**Computation method (epoch-aligned linear velocity ratio):**

1. v_MLCW(s) fitted from total MLCW column compaction (Σ valid rings per epoch)
2. v_InSAR(s) fitted from InSAR vertical displacement at station location (m → mm)
3. Both velocities estimated **within the overlapping date window only**: `[max(mlcw_start, insar_start), min(mlcw_end, insar_end)]`
4. `α_insar(s) = v_MLCW(s) / v_InSAR(s)`

Note: InSAR measurements are vertical displacement, decomposed from ascending + descending Sentinel-1 passes (not raw LOS). v_MLCW and v_InSAR are directly comparable in physical direction.

**Script:** `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\alpha_insar_test.py`

**Output file:** `alpha_comparison_all_stations_v3.csv` — 39 stations × 18 columns:
- `Ename`, `v_MLCW_mmyr`, `v_InSAR_mmyr`, `alpha_insar`, `alpha_gnss`, `alpha_diff`, `alpha_ratio`
- `n_valid_rings`, `overlap_start`, `overlap_end`, `n_mlcw_overlap`, `n_insar_overlap`
- `mlcw_full_start`, `mlcw_full_end`, `insar_full_start`, `insar_full_end`
- `X_TWD97`, `Y_TWD97` (EPSG:3826)

**Key findings from α comparison (epoch-aligned):**

| Station | α_insar | α_gnss | diff | Note |
|---------|---------|--------|------|------|
| ANNAN | 0.832 | 0.826 | +0.006 | excellent agreement |
| HONGLUN | 0.628 | 0.640 | −0.013 | excellent agreement |
| HUNAN | 0.792 | 0.806 | −0.014 | excellent agreement |
| TUKU | 0.558 | 0.608 | −0.050 | good agreement |
| JINHU_XIN | **2.371** | 0.348 | +2.023 | physically impossible — MLCW >> InSAR |
| XINJIE | 0.268 | 1.535 | −1.268 | large discrepancy |
| TANQIFENXIAO | 0.357 | 1.404 | −1.047 | large discrepancy |
| ANHE | 0.456 | 1.393 | −0.937 | large discrepancy |

- Stations with large discrepancies between α_insar and α_gnss are candidates for kriging-based replacement (see below)
- After epoch alignment, XIGANG (previously α_insar = 3.55) dropped to 0.426, now consistent with α_gnss = 0.399 — confirming that the earlier anomaly was a time-window artifact

---

### 5.3 Kriging-Interpolated α (refined prior — completed externally)

Stations where α_insar is physically impossible (e.g., α >> 1 or α_insar/α_gnss >> 2) were flagged and replaced by kriging interpolation from the spatially surrounding reliable stations (using EPSG:3826 coordinates). The resulting file:

**Active prior file for inversion:** `alpha_comparison_all_stations_v3.csv`
- Contains both α_gnss and α_insar columns, plus the kriging-refined values for flagged stations
- X_TWD97, Y_TWD97 coordinates included for spatial referencing

**Physical interpretation of α values (from α_insar, epoch-aligned):**
- Well-constrained stations (|α_diff| < 0.1): ANNAN, HONGLUN, HUNAN, JIAXING, XIUTAN, XIGANG, TUKU, YIWU — these form the spatial backbone for kriging
- α < 0.5 implies >50% of InSAR signal originates below 300 m (DONGSHI, HAIFENG, QIAOYI, XIZHOU, ZHENNAN)
- α > 1.0 after alignment: JINHU_XIN (2.371), JIUZHUANG (1.358), ZHENNAN (0.968) — likely instrument-specific issues or local geology anomalies

---

## 5. Stage 1: Per-Station W-Vector Regression

**Implementation:** `D:\112_PROJECT_002\` (pipeline version 2.0)

**Physical rationale:** Each MLCW station is an independent instrument measuring the local compaction depth profile, which is determined by local stratigraphy. The Choushui River Alluvial Fan exhibits strong spatial heterogeneity in hydrogeological properties, from gravel-dominated proximal-fan sediments to clay-dominated distal-fan deposits. A single shared transfer function W cannot represent this heterogeneity. Each station s therefore receives its own transfer function W_s, estimated exclusively from that station's concurrent MLCW and InSAR observations.

**Formulation (per station s):**
```
minimize_{W_s}:  ||Y_s - X_s[:,None] · W_s[None,:]||²_F
                 + λ ||Δ²W_s||²
                 + μ (Σ_k W_s[k] − α_s)²
subject to: W_s[k] ≥ 0
```

- **X_s:** shape (n_valid_s,) — negated cumulative InSAR at station s (mm), NaN epochs excluded
- **Y_s:** shape (n_valid_s, 60) — baseline-relative MLCW per-layer values at station s (mm)
- **W_s:** shape (60,) — weighting vector for station s, independent of all other stations
- **λ = 0.01** (depth smoothness weight): Without λ, the regression treats all 60 depth levels as independent unknowns. Because the InSAR signal at each epoch is a single scalar, the solver can assign wildly oscillating values across adjacent depth levels and still fit the data equally well. These oscillations are numerical artefacts — real compaction profiles are geologically smooth because stratigraphy changes gradually with depth. λ penalises the second difference Δ²W_s (the curvature of the depth profile), forcing the solver to prefer smooth profiles unless the data strongly demand otherwise.
- **μ = 1.0** (α constraint weight): Without μ, the regression has no information about the total fraction of InSAR explained by the 0–300 m column. The data term fits the shape of W_s but does not constrain W_s.sum() — a value of 0.3 or 0.9 could fit equally well if the shape is correct. α(s) is the independent physical estimate of that total fraction, derived from the long-term GNSS/MLCW velocity ratio. μ pulls W_s.sum() toward α_s, anchoring the total magnitude of W_s to the physics-based estimate. In summary: λ controls the shape of W_s (prevents depth-level oscillations); μ controls the magnitude of W_s (anchors the total to α).
- Solver: `scipy.optimize.lsq_linear`, method `'bvls'`, bounds (0, ∞), tolerance 1e-10

Each station's regression system has the same block structure as the global formulation but contains only data from that station:

| Block | Shape | Role |
|-------|-------|------|
| A_data | (n_valid_s × 60, 60) | Data fit at station s |
| A_smooth | (58, 60) | Δ² depth smoothness, scaled by √λ |
| A_edge | (2, 60) | Endpoint anchors at k=0 and k=59, scaled by √(10λ) |
| A_alpha | (1, 60) | Single α_s constraint, scaled by √μ |

The 39 regressions are independent: no spatial coupling is introduced between stations. Final output: W array of shape (39, 60), one 60-point depth profile per station.

**Previous shared-W result (lam=0.01, mu=1.0, now replaced by per-station approach):**
- W.sum() = 0.5304 — the 0–300 m zone accounted for 53% of InSAR-measured surface displacement
- Peak at depth_295m was a data artifact (13 stations with identical depth_290m and depth_295m values before PCHIP fix)
- α constraint was structurally ineffective: the 39 α penalty equations contributed ~2.5 to the objective vs. ~6.2 × 10⁶ for the data term; W.sum() was purely data-driven regardless of μ (0, 0.1, or 1.0)

**Output files (TUKU only, as of 2026-05-13):** `D:\112_PROJECT_002\output\stage1_perstation_TUKU_test\`

**Application to unobserved locations (Stage 2, pending):**
The 39 station-specific W_s vectors are spatially interpolated to all 8,577 grid points of the 500 m InSAR grid. Each depth level k is treated as an independent spatial field W[:,k] defined at the 39 MLCW station locations and interpolated (e.g., via kriging or IDW) to produce W_g[k] at every grid point g. The reconstruction at each grid point then follows:
```
d_mlcw_reconstructed(g, t, k) = W_g[k] × d_insar(g, t)
```
This approach propagates the locally-calibrated depth distribution from each MLCW station to its surrounding area, preserving the fan-scale spatial heterogeneity captured in the per-station inversion.

---

## 6. Direct Ratio Analysis — Model-Free Baseline (Completed)

**Date completed:** 2026-05-13

### 6.1 Purpose and definition

The direct ratio $f_k(i) = Y_s(i,k) / x_s(i)$ divides the MLCW displacement at depth
level $k$ by the cumulative InSAR displacement at the same epoch $i$, for every valid
epoch independently. No proportionality assumption is imposed, no regularisation is
applied, and no α constraint is used. The result is an empirical, model-free estimate
of the depth-resolved compaction fraction at each point in time, providing a baseline
against which the Stage 1 regularised $\hat{w}_k$ can be directly validated.

Key properties:
- When InSAR $x_s(i) \approx 0$ (near the reference epoch), the ratio is undefined
  (np.inf → replaced with np.nan); these epochs contribute nothing to the summary statistics
- Sign invariance: $(-Y)/(-X) = Y/X$ — negating both signals to "compaction positive"
  convention produces identical ratios, so raw signs are used throughout
- The median over all valid epochs, $\bar{f}_k = \mathrm{median}_i f_k(i)$, is the
  direct-ratio analogue of $\hat{w}_k$

### 6.2 Implementation

**Script:** `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\direct_ratio_all_stations.py`

**Data sources (same as Stage 1):**
- InSAR: `data/insar/timeseries/mlcw_interp_insar_IDW_extend.feather` (loaded once, shared)
- MLCW: `data/mlcw/regular_5m/{STATION}_5m_grid.csv` (one per station)

**Processing per station:**
1. Load MLCW 5m grid CSV; subtract 2015-01-16 row as baseline (6 stations lack this
   date → zero baseline used, flagged as WARNING in log)
2. Build YYYYMMDD integer key lookup for both InSAR and MLCW
3. Exact date matching: only epochs present in both datasets are retained
4. Drop any epoch where InSAR or any MLCW depth level contains NaN
5. Compute ratio matrix: `R[i,k] = Y_valid[i,k] / X_valid[i]` (with errstate suppress)
6. Replace non-finite values (Inf, -Inf) with NaN
7. Compute per-depth summary statistics: nanmedian, Q25, Q75, P05, P95, n_finite_epochs

**6 stations using zero baseline** (2015-01-16 not in MLCW record):
ANNAN, JINHU_XIN, JIUZHUANG, LUNFENG_XIN, NANGUANG, ZHENGMIN

### 6.3 Output structure

```
D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\results\direct_ratio\
    {STATION}/
        {STATION}_direct_ratio_stats.csv   — 60 rows × 7 cols:
                                             depth_m, f_median, f_q25, f_q75,
                                             f_p05, f_p95, n_finite_epochs
        {STATION}_direct_ratio_all.npy     — full (n_valid, 60) ratio matrix R
        {STATION}_direct_ratio_profile.png — depth profile: IQR band + 5–95 band +
                                             median line; Stage 1 ŵ_k overlay if available
        {STATION}_direct_ratio_heatmap.png — RdBu_r heatmap: rows=epochs, cols=depths,
                                             colour clipped to ±98th pct of |R|
```

Stage 1 $\hat{w}_k$ overlay is shown only where the file
`D:\112_PROJECT_002\output\stage1_perstation_{station}_test/{station}_B_point_estimate.csv`
exists (currently only TUKU).

### 6.4 Full 39-station results

Batch run completed in 44 seconds. All 39 stations processed successfully.
`median_sum` = $\sum_k \bar{f}_k$; `n_neg_depths` = number of depth levels where
$\bar{f}_k < 0$; `Pearson_r` = correlation of $\bar{f}_k$ with Stage 1 $\hat{w}_k$
(available only for TUKU).

| Station | n_valid | median_sum | n_neg_depths | Pearson_r |
|---------|---------|-----------|-------------|----------|
| ANHE | 444 | 0.4459 | 14 | N/A |
| ANNAN* | 217 | 0.1495 | 12 | N/A |
| BEICHEN | 771 | 0.7345 | 1 | N/A |
| CANLIN | 490 | 0.6355 | 2 | N/A |
| DONGGUANG | 489 | 0.5500 | 2 | N/A |
| DONGSHI | 443 | 0.3457 | 4 | N/A |
| ERLUN | 489 | 0.5152 | 4 | N/A |
| FENGAN | 489 | 0.5019 | 8 | N/A |
| FENGRONG | 489 | 0.5784 | 6 | N/A |
| GUANGFU | 771 | 0.4139 | 5 | N/A |
| HAIFENG | 489 | 0.1562 | 5 | N/A |
| HONGLUN | 771 | 0.5895 | 1 | N/A |
| HUNAN | 771 | 0.6309 | 0 | N/A |
| HUWEI | 693 | 0.4988 | 2 | N/A |
| JIANYANG | 489 | 0.2660 | 1 | N/A |
| JIAXING | 771 | 0.5978 | 8 | N/A |
| JINHU_XIN* | 419 | 0.3894 | 5 | N/A |
| JIUZHUANG* | 371 | 0.3839 | 1 | N/A |
| KECUO | 771 | 0.5635 | 0 | N/A |
| LONGYAN | 489 | 0.5015 | 5 | N/A |
| LUNFENG_XIN* | 294 | 0.2196 | 1 | N/A |
| NANGUANG* | 237 | 0.1436 | 7 | N/A |
| NEILIAO | 771 | 0.6360 | 0 | N/A |
| QIAOYI | 771 | 0.3683 | 7 | N/A |
| TANQIFENXIAO | 761 | 0.4476 | 13 | N/A |
| TUKU | 771 | 0.4888 | 3 | 0.9843 |
| XIGANG | 489 | 0.3609 | 15 | N/A |
| XINGHUA | 489 | 0.5365 | 2 | N/A |
| XINJIE | 489 | 0.1890 | 19 | N/A |
| XINPI | 444 | 0.6243 | 13 | N/A |
| XINSHENG | 759 | 0.5745 | 1 | N/A |
| XINXING | 489 | 0.4439 | 2 | N/A |
| XIUTAN | 771 | 0.6028 | 1 | N/A |
| XIZHOU | 771 | 0.2976 | 8 | N/A |
| YIWU | 771 | 0.5349 | 0 | N/A |
| YUANCHANG | 754 | 0.6094 | 2 | N/A |
| ZHENGMIN* | 556 | 0.3388 | 0 | N/A |
| ZHENNAN | 489 | 0.8601 | 12 | N/A |
| ZHUTANG | 489 | 0.5395 | 3 | N/A |

\* Zero baseline used (2015-01-16 not in MLCW record). `median_sum` values for these
stations are expressed relative to the instrument's own zero, not the InSAR baseline
date, and may therefore be systematically shifted relative to the α_insar estimates.

### 6.5 Key findings and interpretation

**Profile shape validation (TUKU).**
The Pearson correlation between the direct ratio median profile $\bar{f}_k$ and the
Stage 1 regularised point estimate $\hat{w}_k$ is $r = 0.984$ ($K = 60$ depths).
This near-perfect agreement between a model-free estimate and a heavily regularised
inversion confirms that the depth profile *shape* recovered by Stage 1 is data-driven,
not an artefact of the smoothness penalty or α constraint. The main difference between
the two is in total magnitude: $\sum \bar{f}_k = 0.4888$ vs. $\alpha_s = 0.5580$ for
TUKU, indicating the α constraint pulls $\hat{w}_k$ toward a slightly higher total.

**Spatial heterogeneity in median_sum.**
$\sum_k \bar{f}_k$ ranges from 0.14 (NANGUANG) to 0.86 (ZHENNAN) across the 39
stations — a factor of 6. This range is larger than the uncertainty within any single
station's temporal variation, confirming that spatial heterogeneity in compaction
fraction is the dominant challenge for Stage 2 gap-filling, not temporal variation
within a station.

Grouping by median_sum:
- **High (> 0.65):** BEICHEN (0.73), ZHENNAN (0.86) — deep alluvial sequences,
  likely thick fine-grained deposits
- **Mid-range (0.45–0.65):** most of the 39 stations cluster here, consistent with
  α_insar values in the same range
- **Low (< 0.30):** ANNAN (0.15), HAIFENG (0.16), NANGUANG (0.14), XINJIE (0.19),
  JIANYANG (0.27), XIZHOU (0.30) — some are zero-baseline stations (biased); others
  (HAIFENG, XIZHOU) have genuine low compaction fractions consistent with α_insar

**Negative depth medians (n_neg_depths).**
A depth level $k$ with $\bar{f}_k < 0$ means that layer's displacement is
systematically anti-correlated with total InSAR at the surface. Three physical causes
have been identified:

1. **Near-surface (depth 5–10 m):** unsaturated zone elastic rebound; soil moisture
   fluctuations drive seasonal expansion that is out of phase with the compaction signal
   dominating InSAR
2. **Deep confined aquifer (depth 295 m):** artesian recharge in some years causes
   this layer to expand when shallower aquifers are compacting; the deepest MLCW ring
   may also carry anchor measurement noise
3. **Formation boundary depths (e.g., 180 m, 275 m):** layers straddling aquifer/
   aquitard contacts exhibit mixed elastic/inelastic behaviour with opposite-sign
   responses to the same head change

Stations with n_neg_depths = 0 — **HUNAN, KECUO, NEILIAO, YIWU, ZHENGMIN** — have
all depth medians positive: every depth level compacts proportionally with InSAR at
every epoch. These are the cleanest candidates for validating the proportionality
assumption and for anchoring the Stage 2 spatial interpolation.

Stations with n_neg_depths ≥ 12 — XINJIE (19), XIGANG (15), ANHE (14),
TANQIFENXIAO (13), XINPI (13), ZHENNAN (12), ANNAN (12) — have complex depth
distributions where Stage 1's non-negativity constraint will zero out many depth
levels, potentially masking physically meaningful signals.

**n_valid and record length.**
Stations with n_valid < 500 either have short MLCW records (ANNAN, LUNFENG_XIN,
NANGUANG, JIUZHUANG starting after 2015) or accumulated gaps from the zero-baseline
issue. The 12 stations with n_valid = 771 have complete concurrent records (full
785 InSAR epochs minus 14 unmatched dates at start/end of record).

---

## 7. In-Sample Validation and Seasonal Misfit Metrics — All 39 Stations

**Date completed:** 2026-05-14

### 7.1 Validation setup

Script: `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\validate_all_stations.py`

The proxy Ŷ(i,k) = f̄_k × x(i) is evaluated against the MLCW observations at the
same epochs used to compute f̄_k (in-sample validation). Metrics per station:
RMSE, |bias|, R² (per depth), totalR² (total column), coverage (P05–P95 band), and
five new seasonal misfit metrics (see §7.2).

Output: `results/direct_ratio/all_stations_validation_summary.{csv,json}`

### 7.2 Seasonal misfit metrics

Five metrics computed from the residual resid[i,k] = Y[i,k] − Ŷ[i,k] at each depth:

| Symbol | Physical meaning |
|--------|-----------------|
| `seasAmp` (mm) | Annual harmonic amplitude in the residual — how large is the annual cycle the proxy is missing? |
| `ampRatio` | MLCW annual swing / Ŷ annual swing — ratio > 1 means InSAR underestimates seasonal amplitude |
| `rDT_ma` | Pearson r after removing 1-year centred moving average — tests seasonal tracking, not just trend |
| `rDT_poly` | Same with 3rd-order polynomial detrend (per-depth CSV only) |
| `ac1yr` | 1-year lag autocorrelation of residual — high value = systematic annual error, not noise |

### 7.3 Cross-station summary (all 39 stations)

| Station      | n   | RMSE(mm) | R²     | totR² | seasAmp | ampRatio | rDT_ma | ac1yr |
|--------------|-----|----------|--------|-------|---------|----------|--------|-------|
| ANHE         | 444 | 0.542    | 0.251  | 0.946 | 0.203   | 3.874    | 0.360  | 0.217 |
| ANNAN        | 217 | 0.386    | 0.180  | 0.279 | 0.181   | 5.302    | 0.190  | 0.588 |
| BEICHEN      | 771 | 0.591    | 0.646  | 0.952 | 0.214   | 1.573    | 0.368  | 0.199 |
| CANLIN       | 490 | 0.497    | 0.687  | 0.926 | 0.261   | 1.738    | 0.674  | 0.297 |
| DONGGUANG    | 489 | 0.704    | 0.643  | 0.896 | 0.342   | 2.080    | 0.388  | 0.352 |
| DONGSHI      | 443 | 0.268    | 0.383  | 0.830 | 0.157   | 2.569    | 0.373  | 0.424 |
| ERLUN        | 489 | 0.261    | 0.402  | 0.898 | 0.100   | 1.504    | 0.172  | 0.107 |
| FENGAN       | 489 | 0.320    | 0.182  | 0.814 | 0.092   | 1.344    | 0.048  | 0.577 |
| FENGRONG     | 489 | 0.404    | 0.546  | 0.945 | 0.172   | 2.216    | 0.229  | 0.187 |
| GUANGFU      | 771 | 0.576    | 0.618  | 0.960 | 0.171   | 1.592    | 0.253  | 0.359 |
| HAIFENG      | 489 | 0.178    | 0.447  | 0.650 | 0.040   | 1.669    | 0.126  | 0.350 |
| HONGLUN      | 771 | 0.515    | 0.819  | 0.978 | 0.202   | 1.766    | 0.411  | 0.456 |
| HUNAN        | 771 | 0.409    | 0.848  | 0.935 | 0.097   | 1.306    | 0.057  | 0.636 |
| HUWEI        | 693 | 0.558    | 0.585  | 0.953 | 0.168   | 2.296    | 0.249  | 0.261 |
| JIANYANG     | 489 | 0.248    | 0.594  | 0.681 | 0.057   | 1.221    | 0.207  | 0.800 |
| JIAXING      | 771 | 0.415    | 0.234  | 0.929 | 0.185   | 2.030    | 0.545  | 0.400 |
| JINHU_XIN    | 419 | 1.591    | 0.347  | 0.287 | 0.401   | 3.525    | 0.088  | 0.995 |
| JIUZHUANG    | 371 | 1.536    | 0.322  | 0.485 | 0.584   | 4.330    | 0.304  | 0.784 |
| KECUO        | 771 | 0.606    | 0.837  | 0.980 | 0.193   | 1.652    | 0.435  | 0.504 |
| LONGYAN      | 489 | 0.483    | 0.577  | 0.949 | 0.186   | 1.554    | 0.359  | 0.149 |
| LUNFENG_XIN  | 294 | 0.437    | 0.180  | 0.472 | 0.221   | 7.979    | 0.228  | 0.266 |
| NANGUANG     | 237 | 0.571    | 0.160  | 0.274 | 0.283   | 7.674    | 0.406  | 0.675 |
| NEILIAO      | 771 | 0.535    | 0.912  | 0.991 | 0.231   | 1.718    | 0.530  | 0.241 |
| QIAOYI       | 771 | 0.355    | 0.573  | 0.989 | 0.102   | 2.656    | 0.106  | 0.279 |
| TANQIFENXIAO | 761 | 0.843    | 0.271  | 0.961 | 0.382   | 3.311    | 0.185  | 0.418 |
| TUKU         | 771 | 0.665    | 0.647  | 0.966 | 0.188   | 1.909    | 0.409  | 0.572 |
| XIGANG       | 489 | 0.271    | 0.306  | 0.817 | 0.108   | 2.747    | 0.206  | 0.570 |
| XINGHUA      | 489 | 0.350    | 0.602  | 0.974 | 0.170   | 2.244    | 0.013  | 0.226 |
| XINJIE       | 489 | 0.280    | −0.017 | 0.856 | 0.088   | 2.385    | 0.176  | 0.526 |
| XINPI        | 444 | 0.357    | 0.105  | 0.743 | 0.184   | 2.825    | 0.244  | 0.060 |
| XINSHENG     | 759 | 0.456    | 0.681  | 0.964 | 0.113   | 2.678    | 0.119  | 0.383 |
| XINXING      | 489 | 0.235    | 0.614  | 0.936 | 0.087   | 1.933    | 0.129  | 0.589 |
| XIUTAN       | 771 | 0.757    | 0.811  | 0.985 | 0.215   | 1.682    | 0.483  | 0.499 |
| XIZHOU       | 771 | 0.323    | 0.588  | 0.986 | 0.094   | 2.032    | −0.008 | 0.235 |
| YIWU         | 771 | 0.381    | 0.730  | 0.881 | 0.233   | 1.980    | 0.659  | 0.625 |
| YUANCHANG    | 754 | 1.274    | 0.619  | 0.902 | 0.295   | 3.474    | 0.331  | 0.420 |
| ZHENGMIN     | 556 | 0.523    | 0.709  | 0.789 | 0.170   | 2.660    | 0.428  | 0.675 |
| ZHENNAN      | 489 | 0.258    | −0.132 | 0.772 | 0.156   | 1.181    | 0.402  | 0.247 |
| ZHUTANG      | 489 | 0.352    | 0.593  | 0.965 | 0.101   | 1.346    | 0.075  | 0.189 |

Coverage (P05–P95 band) is uniformly 0.898–0.900 across all stations — self-consistent
by construction (the band was defined from the same epoch distribution).

### 7.4 Three-tier seasonal misfit classification

**Tier 1 — Severe (ampRatio > 3.5):**
LUNFENG_XIN (7.98), NANGUANG (7.67), ANNAN (5.30), JIUZHUANG (4.33), ANHE (3.87),
JINHU_XIN (3.53). MLCW seasonal swing 4–8× larger than InSAR implies. ac1yr at
JINHU_XIN = 0.995 (year-on-year systematic), JIUZHUANG = 0.784. High RMSE (> 1 mm)
at JINHU_XIN and JIUZHUANG confirms structured seasonal error, not noise. These stations
likely sit above lithological units that respond much more strongly to seasonal
groundwater recharge/discharge than the InSAR-integrated column suggests.

**Tier 2 — Moderate (ampRatio 1.5–3.5, most stations):**
The majority of the 39 stations. Proxy tracks trend reliably (totR² = 0.85–0.99) but
tracks seasonal oscillations weakly (rDT_ma 0.1–0.5 vs. raw R² 0.4–0.9). The gap
between raw R² and rDT_ma confirms the proxy is a good trend follower but a poor
seasonal tracker. Exception: CANLIN (rDT_ma=0.674) — InSAR and MLCW share both
trend and seasonal structure at this station.

**Tier 3 — Minor (ampRatio < 1.5):**
ERLUN (1.50), JIANYANG (1.22), FENGAN (1.34), ZHENNAN (1.18), ZHUTANG (1.35).
Small absolute seasAmp (0.06–0.16 mm); proxy adequate for both trend and seasonal.

### 7.5 Implications for Stage 2 and the manuscript

- **Manuscript:** stations with ampRatio > 3 should be flagged as "limited seasonal
  validity." Report rDT_ma alongside raw R² to make the trend-vs-seasonal distinction
  explicit to reviewers.
- **Uncertainty:** P05–P95 band is conservative for trend-dominated errors but may be
  biased in phase for high-ac1yr stations (systematic seasonal errors are not centred
  at the right time of year).
- **No model change at this stage.** LOO-CV results (not yet run) will determine whether
  IDW interpolation of f̄_k suppresses or inherits station-level seasonal misfits.
- **Full discussion:** `D:\112_PROJECT_002\discussions\discussion_20260514.md`

---

## 8. Results and Interpretation: What the Analysis Revealed

### 8.1 Why We Need a Compaction Fraction

Before we could estimate how much each underground layer contributes to surface subsidence, we needed to answer a simpler question first: of all the downward displacement that InSAR measures at the surface, how much of it actually comes from the 0–300 m depth range that our MLCW wells monitor?

This matters because InSAR sees the total surface displacement — from all sources, at all depths, including elastic deformation of the shallow unsaturated soil and any compaction occurring below 300 m where our borehole instruments cannot reach. If we skip this step and assume that 100% of the InSAR signal comes from our monitored column, we will overestimate how much each depth layer is responsible for. We call this corrective factor the compaction fraction $\alpha$. It is a single number per station, between 0 and 1, telling us what fraction of the InSAR surface displacement can be attributed to compaction within the 0–300 m monitoring column.

Three approaches to estimating $\alpha$ were evaluated, all completed. The three approaches build on each other: the GNSS method provides the first estimate, InSAR provides an independent check, and kriging resolves the disagreements.

The $\alpha$ values also carry physical meaning about local geology. Stations with $\alpha < 0.5$ (DONGSHI, HAIFENG, QIAOYI, XIZHOU, ZHENNAN) imply that more than half of the InSAR surface signal originates from below 300 m — likely from deep consolidated sediments not instrumented by the MLCW network. Stations with $\alpha > 1.0$ after epoch alignment (JINHU\_XIN at 2.371, JIUZHUANG at 1.358) indicate instrument-specific issues or local geology anomalies and were replaced by kriging values.

### 8.2 From Total Fraction to Depth Profile: The Direct Ratio $\bar{f}_k$

Knowing $\alpha$ tells us *how much* of the InSAR signal comes from the monitoring column. The next question is harder: *which layers* inside that column are responsible, and in what proportions? This is where the depth-stratified compaction fraction $\bar{f}_k$ comes in.

For each station $s$, each depth level $k$ (one of 60 levels at 5 m intervals from 0 to 295 m), and each observation epoch $i$, the fraction of InSAR displacement attributable to that depth layer is simply the MLCW displacement at that depth divided by the InSAR surface displacement at the same moment:

$$f_k(i) = \frac{Y_s(i,\, k)}{x_s(i)}$$

Here, $Y_s(i, k)$ is the compaction measured by the MLCW at depth $k$ and epoch $i$ (in metres), and $x_s(i)$ is the InSAR cumulative displacement at the same station and epoch (also in metres). The ratio is dimensionless — it is the fraction of the total surface signal that comes from this particular 5 m layer at this moment in time.

Because this ratio fluctuates epoch to epoch (pumping varies, seasons change), we take the median over all valid epochs to get a stable long-term estimate:

$$\bar{f}_k = \text{median}_i \left[ f_k(i) \right]$$

This median profile $\bar{f}_k$ — one value per depth per station — is the primary product of the analysis. Once we have it, we can reconstruct the expected MLCW displacement at any epoch from InSAR alone:

$$\hat{Y}(i,k) = \bar{f}_k \cdot x(i)$$

**A detour we tried first — Stage 1 regularised regression:** Before settling on the direct ratio, we formulated a more complex approach. For each station $s$, a 60-element weight vector $\mathbf{W}_s$ was estimated by minimising a regularised least-squares objective:

$$\min_{\mathbf{W}_s} \left\| \mathbf{Y}_s - \mathbf{W}_s \cdot \mathbf{x}_s \right\|^2 + \lambda \left\| \mathbf{D}^2 \mathbf{W}_s \right\|^2 \quad \text{subject to} \quad \sum_k W_{s,k} \approx \alpha_s$$

This was tested at TUKU, the station with the longest record (771 overlapping epochs). The Pearson correlation between the Stage 1 estimate $\hat{w}_k$ and the direct ratio $\bar{f}_k$ at TUKU was $r = 0.984$ — both approaches recovered the same depth profile shape. Stage 1 was then replaced by the direct ratio for three reasons: it requires two hyperparameters ($\lambda$ and $\mu$) that must be tuned per station; the direct ratio achieves the same depth profile with no solver and no hyperparameter choices; and the structural limitation that affects Stage 1 — systematic underestimation of seasonal amplitude — is equally present in the direct ratio, meaning it is a physical constraint of the scalar representation, not a solver deficiency. Stage 1 remains available as a sensitivity check; its outputs at TUKU are archived but not used in the primary spatial reconstruction.

### 8.3 What the 39-Station Batch Revealed

Running the direct ratio across all 39 stations produced a network-wide picture of how compaction is distributed with depth. The results were striking in their spatial range.

The sum of $\bar{f}_k$ across all 60 depth levels ranges from 0.14 at NANGUANG to 0.86 at ZHENNAN — a 6-fold difference across the fan. This reflects the proximal-to-distal stratigraphic gradient: at proximal sites near the mountains, thin alluvium over bedrock means most InSAR displacement comes from sources outside the 0–300 m column; at distal coastal sites, thick fine-grained lacustrine deposits mean the monitored column accounts for most of the surface signal. This is geological heterogeneity, not temporal drift, and it is the dominant challenge for the spatial interpolation step that follows.

Eighteen stations show negative $\bar{f}_k$ medians at depths of 0–15 m. This is not an error. During wet epochs, soil moisture recharge causes upward displacement in the shallow unsaturated zone — the ground expands slightly as water fills the pores near the surface. This upward movement partially offsets the downward compaction signal from deeper layers, producing a negative ratio at shallow depths. The reversal is real and physically expected.

At TUKU, $\sum \bar{f}_k = 0.49$ while $\alpha_{\text{insar}} = 0.558$. The 14% gap arises from three effects: the $\bar{f}_k$ at 10 m depth is negative (elastic rebound at individual epochs reduces the epoch-level sum); $\alpha$ is derived from secular velocity only, which emphasises the multi-year trend and suppresses short-term elastic contributions; and the two quantities use different methods of averaging over time.

### 8.4 Validating the Proxy at TUKU

With $\bar{f}_k$ in hand, we evaluated the proxy $\hat{Y}(i,k) = \bar{f}_k \cdot x(i)$ against observed MLCW displacement at all 60 depths and 771 epochs at TUKU, the focal station used for all single-station diagnostics.

**Overall statistics:** mean RMSE = 0.665 mm, mean $R^2$ = 0.647, mean |bias| = 0.107 mm.

**Depth-zone performance:**

| Zone | Depths | RMSE (mm) | $R^2$ | Interpretation |
|------|--------|-----------|-------|----------------|
| Core compressible | 25–115 m, 145–215 m | 0.18–0.54 | 0.82–0.98 | Proxy reliable |
| Shallow unconfined | 0–20 m | 0.9–1.4 | < 0 | Elastic rebound dominates; proxy structurally wrong |
| Boundary transitions | 130–140 m, 225–295 m | 0.6–1.5 | 0.11–0.76 | Stratigraphically complex |

Best single depth: 85 m (RMSE = 0.179 mm, $R^2$ = 0.977) — the F2 aquifer fine-grained unit. Worst single depth: 180 m (RMSE = 1.92 mm, $R^2$ = 0.360) — the F3/F4 transitional boundary with short-term sign-reversing displacement.

**Uncertainty calibration:** The P05–P95 band from the epoch distribution of $f_k(i)$ was propagated as the uncertainty range. Coverage at TUKU = 0.899 (target 0.90) — confirming that the 5th–95th percentile range is a reliable uncertainty representation. The proxy correctly captures the 2019 and 2024 short-term acceleration events.

### 8.5 Seasonal Misfit: The Proxy's Structural Limitation

The overall $R^2$ values look reassuring, but they are dominated by the long-term trend. To understand how well the proxy captures seasonal variation, five additional metrics were computed per station (defined in §7.2).

The results revealed a systematic problem. The direct ratio $\bar{f}_k$ is a reliable trend estimator — totR² ranges from 0.85 to 0.99 at all 39 stations. However, it systematically underestimates seasonal amplitude. 36 of 39 stations have ampRatio > 1.5, meaning the MLCW seasonal swing is at least 1.5× larger than the proxy predicts.

Three-tier classification by severity (see §7.4 for station lists):
- **Tier 1 — Severe (ampRatio > 3.5):** 6 stations, including JINHU_XIN (ac1yr = 0.995) confirming a perfectly reproducible, structurally driven seasonal error
- **Tier 2 — Moderate (ampRatio 1.5–3.5):** 30 stations; proxy is a good trend follower but poor seasonal tracker
- **Tier 3 — Minor (ampRatio < 1.5):** 5 stations; proxy adequate for both trend and seasonal

### 8.6 Four Physical Reasons for the Seasonal Misfit

The seasonal misfit was diagnosed from the data and cross-checked against the literature (Smith et al. 2021 on California's Colusa Basin; Jiang et al. 2025). Four mechanisms were identified.

**Mechanism 1 — The InSAR surface signal is a mixture from many depths.** InSAR measures the total surface movement — the combined result of compaction happening simultaneously at all depth layers. Shallow F1/F2 aquifers (19–107 m) respond to seasonal pumping within weeks. Deep F3/F4 aquifers (140–300 m) respond over months to years because pore pressure changes must diffuse slowly through the clay layers above them (time lag $\tau$ estimated at 100–200+ days for F3/F4 at TUKU). A single time-invariant scalar $\bar{f}_k$ cannot separate these signals when different depth layers peak at different times of year.

**Mechanism 2 — Shallow and deep aquifers are pumped in opposite seasons.** F2 (35–107 m) is pumped primarily for summer irrigation, so its seasonal compaction maximum occurs in summer. F3/F4 (140–300 m) are used for winter industrial and aquacultural supply, so their seasonal compaction maximum may occur in winter. These out-of-phase signals partially cancel in the surface InSAR measurement. The static scalar $\bar{f}_k$ cannot assign the correct seasonal phase to each depth independently.

**Mechanism 3 — Elastic rebound in the shallow zone works against the proxy.** During the wet season (May–October), shallow soil moisture recharge causes upward displacement at 0–20 m depth. This opposes downward compaction signals from deeper layers. The surface InSAR measurement records the combined total of all these signals, which reduces the apparent seasonal amplitude. The proxy $\bar{f}_k \cdot x(i)$ propagates this reduction to all depths, even at depths where elastic rebound is absent.

**Mechanism 4 — The InSAR and MLCW models use different time scales.** The InSAR reconstruction used harmonics at 1 yr, 0.5 yr, 5 yr, and 10 yr, plus piecewise velocity breakpoints. The MLCW reconstruction used only 1 yr and 0.5 yr harmonics. Long-period InSAR terms (5 yr, 10 yr) have no MLCW counterpart. Residuals that appear seasonal may partly be multi-year oscillations incorrectly assigned to the annual band.

### 8.7 Hydrogeological Zones and Why TUKU Is a Special Case

A concurrent study of the CRAF (Azeriansyah et al. 2025) using a 35-station MLCW subset classified the fan into four hydrogeological zones by the degree of inter-layer vertical hydraulic connectivity:

| Zone | Region | Vertical connectivity | Examples |
|------|--------|----------------------|---------|
| I | Northern Changhua | Low | Isolated layers with strong vertical barriers |
| II | Southern Changhua | Moderate | Transitional |
| III | Northern Yunlin | High | TUKU ("big sponge") |
| IV | Southern Yunlin (Puzih) | High | YIWU — most interconnected |

TUKU (Zone III) has high inter-layer vertical connectivity across 0–200 m depth. Seasonal groundwater fluctuations propagate together through many depth layers at the same time, rather than selectively affecting individual aquifer units. This is the reason TUKU single-station tests showed minimal gain from seasonal correction — the "big sponge" behaviour ensures that no single depth layer responds differently from its neighbours at seasonal timescales. Zones I and II (Changhua), with lower connectivity, allow individual depth layers to respond selectively to seasonal forcing. Seasonal corrections are physically expected to help at these stations, and the batch results confirmed this prediction.

### 8.8 Three Approaches to Reduce the Seasonal Misfit

Three strategies were evaluated to address the seasonal underestimation.

**Option A — Wet/dry split:** Two separate $\bar{f}_k$ profiles were computed from epoch subsets — wet season (May–October) and dry season (November–April) — and applied accordingly. Tested at TUKU.

*Result:* The wet and dry profiles were nearly identical. Mean absolute difference = 0.000447 across 60 depths; RMSE change = −0.3% (negligible). Only 6 of 60 depths exceeded 20% relative difference, none at known aquifer boundaries. Decision: Option A ruled out at Zone III stations. Wet/dry batch across all 39 stations: `wetdry_recommended = True` at 5 stations (> 2% RMSE improvement): LONGYAN (+2.89%), LUNFENG_XIN (+2.76%), ANNAN (+2.31%), DONGSHI (+2.20%), JIUZHUANG (+2.09%).

**Option B — Harmonic decomposition:** Both InSAR and MLCW time series were decomposed into a trend component (1-year moving average) and a seasonal residual. Separate scalars were estimated: $f_{\text{trend},k}$ for the trend component and $f_{\text{seas},k}$ for the seasonal component. Tested at TUKU.

*Result:* Overall RMSE improvement = +0.4% — effectively the same as Option A. Per-depth analysis revealed that $f_{\text{seas},k}$ improves performance at 0–125 m (best: 80 m, +7.0%; 85 m, +8.1%) but degrades it below 130 m (worst: 245 m, −14.4%), where time-lag contamination from the moving-average decomposition corrupts $f_{\text{seas},k}$.

*Adopted hybrid:* $f_{\text{seas},k}$ is used for 0–125 m (F1/F2 aquifer zone); the scalar $\bar{f}_k$ is retained for 130–295 m (F3/F4 zone, time-lag-contaminated).

Harmonic batch across all 39 stations: `harmonic_recommended = True` at 13 stations:

| Station | RMSE improvement |
|---------|-----------------|
| NANGUANG | +15.79% |
| ANNAN | +8.69% |
| LUNFENG_XIN | +7.11% |
| TANQIFENXIAO | +5.38% |
| JIUZHUANG | +4.51% |
| XINGHUA | +3.32% |
| ERLUN | +3.05% |
| XIUTAN | +2.98% |
| YIWU | +2.83% |
| QIAOYI | +2.57% |
| XIGANG | +2.57% |
| XINPI | +2.57% |
| JIAXING | +2.47% |

TUKU confirmed at +0.38% (Zone III physical ceiling). GUANGFU at −6.43% — harmonic decomposition degrades at this station because insufficient InSAR seasonal amplitude prevents reliable estimation of $f_{\text{seas},k}$.

**Option C — Rolling-window $\bar{f}_k(t)$:** A temporal moving median over a ±1-year window was computed to detect multi-year drift in the compaction fraction. This diagnostic was computed but not deployed as a production estimator: it requires careful endpoint handling and its leave-one-out cross-validation (LOO-CV) implementation would require per-station window optimisation.

**Adopted strategy:** The static $\bar{f}_k$ is the primary estimator at all stations. A supplementary hybrid field — harmonic decomposition at 0–125 m for the 13 flagged stations, scalar $\bar{f}_k$ elsewhere — is assigned to Stage F of the kriging pipeline, allowing quantification of the seasonal attribution error introduced by the scalar-only assumption.

---

## 9. Spatial Interpolation: From IDW Baseline to Kriging

### 9.1 IDW Baseline (Complete)

Inverse-distance weighting (IDW, $1/d^2$) was applied to interpolate the 39-station f̄_k profiles to the 8,577-point 500 m grid. Eight nearest neighbours were used with no maximum distance cutoff.

**Outputs (all complete):**

| File | Description |
|------|-------------|
| `stage2_output/stage2_fbar_grid.nc` | f̄_k at 8,577 grid points, 60 depths (CF-1.8 NetCDF4) |
| `stage2_output/stage2_compaction_central.nc` | 3D compaction field: f̄_k(g) × InSAR(g,t), central estimate |
| `stage2_output/stage2_compaction_lo.nc` | Lower uncertainty bound (P05 band) |
| `stage2_output/stage2_compaction_hi.nc` | Upper uncertainty bound (P95 band) |

**LOO-CV results:** Leave-one-out cross-validation was run holding out each of the 39 stations in turn and predicting its f̄_k from the remaining 38. Results were stored in `stage2_loocv_results.csv` (39 × 60 = 2,340 rows). Absolute threshold reanalysis (threshold = 0.005, physically interpretable as 0.5% depth misattribution) identified 8 stations with >90% of predictions exceeding the absolute threshold:

| Station | Fraction exceeding 0.005 |
|---------|--------------------------|
| NANGUANG | 0.983 |
| XIZHOU | 0.983 |
| HUNAN | 0.900 |
| QIAOYI | 0.900 |
| ZHENGMIN | 0.900 |
| ANHE | 0.867 |
| FENGAN | 0.867 |
| GUANGFU | 0.867 |

Typical absolute LOO-CV RMSE values across the network are 0.003–0.006 mm — within the measurement precision of the MLCW extensometers (~±0.5 mm). The `large_error` flag reflects genuine spatial heterogeneity of the geological substrate, not a failure of the IDW algorithm. IDW predictions at isolated stations are smooth averages from geologically different neighbours.

### 9.2 The Spatial Heterogeneity Problem

The dominant challenge for Stage 2 is that the spatial distribution of f̄_k is controlled by geological stratigraphy — not by the monitoring network, and not primarily by temporal variability. Sum(f̄_k) ranges from 0.14 (NANGUANG, proximal, thin alluvium) to 0.86 (ZHENNAN, distal, thick fine-grained deposits). IDW cannot resolve this gradient accurately where MLCW stations are sparse or where the gradient is steep.

The November 2021 network shutdown makes this problem worse. Twenty of 39 stations ceased operation:

**Shutdown stations (20):** ANHE, ANNAN, CANLIN, DONGGUANG, DONGSHI, ERLUN, FENGAN, FENGRONG, HAIFENG, JIANYANG, LONGYAN, LUNFENG_XIN, NANGUANG, XINJIE, XIGANG, XINGHUA, XINXING, XINPI, ZHENNAN, ZHUTANG

**Active stations (19):** BEICHEN, GUANGFU, HONGLUN, HUNAN, HUWEI, JIAXING, JIUZHUANG, JINHU_XIN, KECUO, NEILIAO, QIAOYI, TANQIFENXIAO, TUKU, XIUTAN, XIZHOU, XINSHENG, YIWU, YUANCHANG, ZHENGMIN

The f̄_k profiles for the 20 shutdown stations were calibrated from pre-2021 data and are held constant for 2022–2025 InSAR epochs. This assumption is reasonable for the trend component (long-term clay consolidation is geologically stable) but is less reliable for the elastic seasonal component, which may have shifted as pumping patterns changed during the 2021–2024 drought recovery.

### 9.3 Why Kriging Was Adopted

IDW treats spatial correlation as a pure function of distance. It learns nothing about the underlying geological structure of the fan. Kriging fits an explicit variogram model — nugget, sill, range, and potentially anisotropy direction — to the observed spatial covariance of f̄_k across the 39 stations at each depth level. The variogram encodes geological continuity: how similar are f̄_k values at two stations as a function of their separation distance and direction.

The critical methodological insight is that geological continuity is a property of the sedimentary system, not the monitoring network. The variogram fitted from the dense 2015–2021 39-station period describes the fan's stratigraphy. That stratigraphy does not change on decadal timescales. Therefore the variogram is transferable to the sparser 2021–2025 19-station period without requiring that the 19 active stations collectively span the same geological gradients as the full 39.

Kriging also produces a spatially explicit uncertainty map, called kriging variance. This uncertainty is largest at locations farthest from any monitoring station — the prediction is less certain where the interpolation must span greater distances.

Once the baseline ordinary-kriging variogram is established, additional spatial information can be incorporated as external drift covariates. The 306-well GWL network provides a spatially dense constraint on groundwater pressure gradients, which are physically related to f̄_k through the compressibility of the sediment under changing water pressure. Kriging with external drift (KED) using GWL trend as covariate was evaluated (proposal P3, `opus_research_ideas_20250515.md`) and recommended for deployment if the diagnostic gate is passed: R² > 0.4 from regression of depth-summed f̄ on GWL trend at 21 MLCW–GWL overlap stations.

### 9.4 Kriging Stages A–F: Class III Baseline Reference

Kriging variogram transfer (Stages B–D) was planned as the primary spatial method before the project objective was reframed as predictive inference in May 2026. Under the predictive objective, kriging variogram transfer is a **Class III method** (see §1 for the definition): it produces a static spatial field that cannot update itself from new observations once the calibration window closes. It is therefore not the primary method under the revised objective.

Stages B–F remain in scope for a different purpose: they define the **best possible static baseline** against which the Class I and II predictive candidates (Terzaghi+GP, LSTM, GP in depth×space×time; see `opus_research_ideas_predictive_20250515.md`) are compared in the network-degradation experiment. The IDW–kriging comparison (Stage E) and the LOO-CV results (Stage A, complete) together define this performance floor.

| Stage | Description | Class | Status |
|-------|-------------|-------|--------|
| A | LOO-CV absolute threshold reanalysis (0.005 threshold) | III — diagnostic | Complete — 8 outlier stations identified |
| B | Spherical variogram fitting, 39 stations × 60 depths | III — baseline | Not yet executed |
| C | Ordinary kriging to 8,577 grid points | III — baseline | Not yet executed |
| D | Variogram transferability test — 19 active stations, post-2021 epochs | III — baseline | Not yet executed |
| E | IDW vs. kriging comparison maps for manuscript | III — comparison | Not yet executed |
| F | Hybrid harmonic integration (supplementary, 13 stations) | III — comparison | Not yet executed |

Decision rule for Stage D: median |residual| < 0.005 at all depths confirms temporal stability (one kriging field covers the full 2015–2025 period); any station with |residual| > 0.010 at any depth is flagged for a local kriging update.

Two diagnostic gates that follow Stage C inform the Class I/II candidate evaluation, not the Class III baseline:
- **KED with GWL (P3):** If R² > 0.4 from regression of depth-summed f̄ on GWL trend at 21 overlap stations, KED qualifies as a **Class II** method and is added to the candidate comparison
- **Terzaghi S_sk inversion at TUKU (P6):** 4-day single-station test; RMSE < 0.5 mm/epoch is the acceptance criterion for **Candidate A (Class I)**; screen-depth confirmation from WRA is required before this test can run

---

## 10. Completed Milestones and Current Status

| Item | Status | Key output |
|------|--------|-----------|
| MLCW preprocessing (decompose, reconstruct, 5 m regularise) | Complete — 39 stations | `data/mlcw/regular_5m/{STATION}_5m_grid.csv` |
| α estimation (GNSS, InSAR, kriging-refined) | Complete | `alpha_comparison_all_stations_v3.csv` |
| Direct ratio f̄_k (39 stations, full record) | Complete — primary Stage 2 input | `{STATION}_direct_ratio_stats.csv` |
| In-sample validation metrics (39 stations, 6 metrics) | Complete | Per-station table (seasAmp, ampRatio, rDT_ma, rDT_poly, ac1yr, totR²) |
| Wet/dry batch (39 stations) | Complete — 5 stations `wetdry_recommended = True` | `wetdry_allstations_summary.csv` |
| Harmonic batch (39 stations) | Complete — 13 stations `harmonic_recommended = True` | `harmonic_allstations_summary.csv` |
| Stage 2 IDW spatial field (baseline) | Complete | `stage2_fbar_grid.nc` |
| Stage 2 3D compaction NetCDF4 — central, lo, hi | Complete — baseline only | `stage2_compaction_central/lo/hi.nc` |
| Stage 2 LOO-CV (absolute threshold reanalysis) | Complete — 8 stations flagged | `stage2_loocv_absolute_summary.csv` |
| GWL dataset inspection | Complete — 306 wells, 21/39 MLCW overlap confirmed | `gwl_allwells_flat.xlsx`, `gwl_inspection_report.json` |
| WRA yearbook extraction (Well_Info_2024.pdf) | Complete 2026-05-17 — 387 wells, 43 markdown files | `well_info_combined.xlsx`, `well_info_screen_comparison.xlsx` |
| GWL JSON patch (8 `json_missing` wells) | Complete 2026-05-17 — screen strings written to JSON | `gwl_inspection_report.json` |
| BME stratigraphy → MLCW hydrofacies (Task P3) | Complete 2026-05-16 | `mlcw_hydrofacies_5m.csv` |
| Screen depth parsing into `gwl_allwells_flat` (Task P1) | Complete 2026-05-15 — `screen_top_m`, `screen_bot_m` added | `gwl_allwells_flat.xlsx` |
| ARX walk-forward validation (39 stations, 4 folds 2022–2025) | Complete 2026-05-17 | `results/arx/arx_allstations_summary.csv` |
| ARX ablation study — anchor vs full ARX decomposition | Complete 2026-05-17 — anchor-only is production method | `results/arx/ablation/ablation_allstations.csv` |
| Prophet pilot at TUKU (14 depths, 4-fold walk-forward) | Complete 2026-05-18 — ARX superior; Prophet only helps at ≥100 m | `prophet_tuku/` |
| Borehole integration discussion (Task P3 encoding options) | Complete 2026-05-18 | `D:\112_PROJECT_002\discussions\discussion_20260518.md` |
| **— Class III static baseline (comparison reference — see §9) —** | | |
| Kriging variogram fitting (Stage B) | Not yet executed — Class III baseline | — |
| Kriging spatial field to 8,577 grid points (Stage C) | Not yet executed — Class III baseline | — |
| Variogram transferability test — 19-station post-2021 (Stage D) | Not yet executed — Class III baseline | — |
| IDW vs. kriging comparison maps for manuscript (Stage E) | Not yet executed — Class III comparison | — |
| Hybrid harmonic integration — 13 stations (Stage F) | Not yet executed — Class III comparison | — |
| **— Class I/II predictive candidates (primary method; see `opus_research_ideas_predictive_20250515.md`) —** | | |
| KED with GWL diagnostic (P3 — gates Class II KED candidate) | Deferred — pending Stage B variogram | — |
| Terzaghi S_sk diagnostic at TUKU (P6 — gates Class I Candidate A) | Deferred — screen-depth confirmation pending | — |
| GWL seasonal amplitude correlation vs. f̄_k | Deferred — diagnostic gate: R² > 0.4 at 21 MLCW–GWL overlap stations qualifies KED as Class II candidate; run after Stage C variogram is established | — |
| **— Phase 5: Temporal Gap-fill (Stage 3 — not yet designed) —** | | |
| Apply f̄_k(g) to epochs where InSAR exists but MLCW does not (e.g., 2022 network blackout) | Not yet designed | — |

Stages B–F are Class III static baseline methods. Execution detail will be written when these stages are scheduled for the baseline comparison study under the predictive inference objective (see `opus_research_ideas_predictive_20250515.md`).

---

## 11. Stage 0 Data Preparation — Completion Record (2026-05-15 to 2026-05-17)

Three data preparation tasks were identified before analysis can proceed. All have been resolved.

### Task P1 — Parse GWL well screen depths (Complete, 2026-05-15)

**What was done:** `well_screen_str` in `gwl_allwells_flat.xlsx` was parsed into numeric `screen_top_m` and `screen_bot_m` columns (via PowerShell one-liner, 2026-05-15). Separately, 8 wells had `well_screen_str = "nan"` or `""` in `gwl_inspection_report.json` even though valid screen depths existed in `Well_Info_2024.pdf`; these were patched using `patch_json_and_export_csv.py` (now in `D:\112_PROJECT_002\legacy\scripts\`).

**Result:** 183/306 wells in `gwl_allwells_flat.xlsx` have valid `screen_top_m` / `screen_bot_m`. The remaining 123 are genuinely absent from the HDF5 source — some of their screen depths may be found in `well_info_combined.xlsx`.

### Task P2 — Station-by-station lithology from borehole logs (Deferred)

**Problem:** Detailed per-station borehole lithology would allow each MLCW station's depth profile to be classified into Aquifer F1/F2/F3/F4 or aquitard materials at exactly the stations' locations — better than the BME grid lookup used in Task P3.

**Decision:** Deferred. Borehole logs are not digitally available from WRA. Task P3 (BME regional model) provides a pragmatic alternative at adequate spatial resolution (500 m BME grid vs. station spacing of 2–20 km).

### Task P3 — BME stratigraphy → MLCW hydrofacies (Complete, 2026-05-16)

**What was done:** Material type at each 5 m depth level was assigned to each MLCW station by nearest-cell lookup into the regional BME (Bayesian Maximum Entropy) lithostratigraphy model (500 m grid).

**Script:** `BASE\mlcw_hydrofacies_5m.py` — takes the BME voxel table (`D:\1000_SCRIPTS\MyPlayGround\20260510_temp\112_BME_CRAF.csv`, 2.58 million rows, 1 m resolution), finds the nearest grid cell to each MLCW station, bins to 5 m intervals using modal material code, and writes the output.

**Output:** `BASE\mlcw_hydrofacies_5m.csv`
- 2,340 rows (39 stations × 60 depth levels from 0 to 295 m)
- Columns: `station`, `x_twd97`, `y_twd97`, `depth_m`, `nearest_bme_dist_m`, `material_code`, `material_class`
- Material codes: 1 = Clay, 2 = Mud, 3 = Silt, 4–5 = Fine Sand, 6 = Medium Sand, 7 = Coarse Sand, 8–11 = Gravel, 13 = Bedrock, 14–15 = Fill
- Max nearest-cell distance: ~707 m (500 m grid diagonal) — acceptable given station spacing

---

## 12. Folder and File Reference for New Team Members

This chapter lists the key directories and files a newcomer needs to find their way around the project. All paths are absolute Windows paths.

### 12.1 Base Working Directory

**`BASE` = `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\`**

Everything computed for this project lives here unless noted otherwise. Subfolders:

| Subfolder | Contents |
|-----------|----------|
| `data\mlcw\raw_timeseries\` | Raw MLCW ring-by-ring CSV files (39 stations) |
| `data\mlcw\decomposed\` | Per-ring parametric decomposition JSON files |
| `data\mlcw\reconstructed\` | Reconstructed ring-by-ring timeseries (regular dates) |
| `data\mlcw\regular_5m\` | **Primary MLCW input.** 5 m depth-regularised, one CSV per station |
| `archive\mlcw_5m_regular_2015\` | Same, trimmed to 2015 start date |
| `data\insar\timeseries\` | **Primary InSAR input.** Feather files at MLCW locations + 500 m grid |
| `gwl_inspection\` | GWL flat table, JSON inspection report, well info xlsx/gpkg |
| `gwl_inspection\well_info_deepseek\` | 43 markdown tables extracted from Well_Info_2024.pdf via DeepSeek |
| `gwl_inspection\well_info_output\` | Same 43 pages, regex-only fallback extraction (lower quality) |
| `results\direct_ratio\` | Per-station direct ratio CSVs + batch validation summaries |
| `stage2_output\` | IDW spatial fields (NetCDF4): f̄_k grid, 3D compaction field |
| `scripts_2026_Apr_May\` | InSAR processing scripts A1–K2 (MintPy → feather pipeline) |
| `GroundwaterWells_MaterialAssign\` | Per-well material assignment .txt and .png files (95 wells) |
| `studyarea_SHP\` | Shapefiles: MLCW stations, 500 m grid, study area boundary |

### 12.2 Analysis and Discussion Directory

**`D:\112_PROJECT_002\`** — inversion code, discussion documents, dataset summary

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Instruction file for Claude Code AI assistant; contains full project architecture, data conventions, and physics-first rules |
| `main.py` | Orchestrator for Stage 1 B-vector regression pipeline |
| `src\` | Python modules: `loader.py`, `system.py`, `solvers_temporal.py`, `postprocess.py`, `reporting.py`, `visualization.py` |
| `configs\` | `inversion_config.ini` — reference λ, μ, σ defaults |
| `output\stage1\` | Per-μ-variant Stage 1 results |
| `my_dataset_summary.md` | **Living data inventory.** Full table of every prepared dataset with file paths, dimensions, format, and status. Read this first when looking for a file. |
| `opus_research_ideas_predictive_20250515.md` | Research roadmap for the three Class I/II predictive method candidates |
| `discussion_YYYYMMDD.md` | Per-session analysis discussion documents |
| `legacy\` | Superseded one-shot scripts (task_p1, task_well_info_merge_check, patch_json, list_no_screen, etc.) and old version archives |

### 12.3 Long-Term Memory Directory

**`D:\110_PROJECT_002\`** — persistent project memory

| File | Purpose |
|------|---------|
| `discussion_memory.md` | This file. Narrative record of all work done, methods, results, and data pipeline. |
| `resources\study_area.md` | Geomorphological and hydrogeological reference for the CRAF |
| `resources\mlcw_info.md` | MLCW network details, station list, ring depth conventions |

### 12.4 External Data Sources (Not in BASE)

| Path | Contents |
|------|----------|
| `D:\VINHTRUONG\001_STUDY_AREA\GroundwaterObservation\@DOWNLOAD_WRA_GWOB_YEARBOOK_PROJECT\Well_Info_2024.pdf` | WRA 2024 hydrological yearbook — source PDF for all well screen depths |
| `D:\1000_SCRIPTS\004_Project003\20251229_Gwater_Levels\20260108_GWL_CRFP_daily_modeled.h5` | WRA permanent GWL network: 306 wells, daily values, 2014–2025 |
| `D:\1000_SCRIPTS\MyPlayGround\20260510_temp\112_BME_CRAF.csv` | BME regional lithostratigraphy: 2.58 million voxel rows, 1 m resolution, 500 m spatial grid |

### 12.5 Python Environment

All project scripts must run in the **`fafalab`** conda environment:

```powershell
conda run -n fafalab python <script.py>
```

Or directly:

```powershell
"D:\Programs\miniconda3\Library\envs\fafalab\python.exe" <script.py>
```

The DeepSeek LLM extraction script (`extract_well_info_deepseek.py`) uses a separate environment:

```powershell
"D:\Programs\miniconda3\Library\envs\deepseek_env\python.exe" extract_well_info_deepseek.py <pdf_path> --output well_info_deepseek
```

### 12.6 Key Conventions a Newcomer Must Know

1. **Sign convention:** InSAR values are negated on load so that positive = compaction throughout. This is applied in `loader.py`. Do not add extra negations anywhere else.

2. **Units:** MLCW displacement is in mm. InSAR feather files are in metres — multiply by 1000 for mm before any ratio calculation.

3. **Depth levels:** 60 active levels at 5 m spacing (0–295 m). `depth_300m` column exists in MLCW files but is always zero — it is the borehole anchor, not a measurement. Exclude it from all analysis.

4. **Reference epoch:** Both MLCW and InSAR are expressed as cumulative displacement since 2015-01-16 (the InSAR reference epoch). Pre-2015 MLCW data is excluded from all regressions.

5. **α clamping:** α values > 0.9 are physically impossible (implies > 90% of InSAR surface signal is from the 0–300 m column — inconsistent with known geology at any CRAF station). They are clamped to 0.9 in `load_alpha_prior()`.

---

## 13. Temporal Prediction — ARX Walk-Forward, Ablation, and Prophet Results

**Date completed:** 2026-05-17 to 2026-05-18

This chapter records the first systematic attempt to improve compaction prediction beyond the static baseline `Ŷ_k(i) = f̄_k × x(i)`. Two methods were tested (ARX and Prophet), both evaluated with identical 4-fold walk-forward validation (train through year N, hold-out year N+1, for N = 2021, 2022, 2023, 2024). The baseline for all comparisons is the static direct ratio prediction `f̄_k × x(i)` using the training-window median.

---

### 13.1 The ARX model

**Definition.** For each station s and each depth level k, the ARX (autoregressive with exogenous input) model is:

```
Y_k(i) = phi_k * Y_k(i-1)  +  beta_k * x(i)  +  gamma_k * Δx(i)  +  epsilon
```

- `Y_k(i)` — MLCW compaction at depth k and epoch i (mm)
- `phi_k` — AR(1) memory coefficient: how much the previous state predicts the current one
- `beta_k` — sensitivity to the cumulative InSAR signal (analogous to f̄_k but OLS-fitted)
- `gamma_k` — sensitivity to the 5-day InSAR increment (rate sensitivity; elastic/anelastic indicator)
- `x(i)` — cumulative InSAR at epoch i (mm); `Δx(i) = x(i) − x(i−1)`

Parameters phi_k, beta_k, gamma_k are estimated by OLS regression on the training window. The model is then run recursively in the hold-out window, starting from the last observed MLCW state at the training cutoff.

**Script and outputs:**
- Script: `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\arx_all_stations.py`
- `results/arx/{STATION}_arx_params.csv` — OLS parameters: depth_m, phi_k, beta_k, gamma_k (39 files)
- `results/arx/{STATION}_arx_walkforward_rmse.csv` — per-depth walk-forward RMSE per fold (19 active stations have data; 20 shut-down stations have NaN — no hold-out ground truth)
- `results/arx/arx_allstations_summary.csv` — one row per station: RMSE_ARX, RMSE_base, improvement %
- `results/arx/arx_allstations_params.npz` — stacked (39, 60) arrays for phi, beta, gamma

**A key physical property of phi_k.** Across all stations and all depths, phi_k ≈ 1.0 (range 0.938–1.043). This near-unit-root behaviour is physically expected: cumulative compaction is a monotonically accumulating process. The soil does not spontaneously expand to its prior state after it has compacted. The AR(1) coefficient close to 1 means the model is saying "the best prediction of where the system is now is where it was at the previous epoch, adjusted by the InSAR loading." This is not a new discovery about the dynamics — it is a confirmation that compaction behaves like a random walk with drift.

---

### 13.2 The ablation study — decomposing the improvement

**Question.** The ARX model adds three things over the static baseline simultaneously: (1) the initial-state anchor, (2) the AR(1) memory term phi_k, and (3) the rate-sensitivity term gamma_k. Which one is responsible for the improvement?

**Three models compared:**

| Model | Formula | What it adds over baseline |
|-------|---------|---------------------------|
| Baseline | `f̄_k × x(i)` | — (reference) |
| Anchor-only | `Y_k(t_last) + f̄_k × (x(i) − x(t_last))` | Initial-state anchor; no OLS fitting |
| Full ARX | `phi_k × Ŷ_k(i-1) + beta_k × x(i) + gamma_k × Δx(i)` | Anchor + OLS dynamics |

The anchor-only model starts from the last observed MLCW value and predicts only the *increment* forward. It uses no OLS fitting: it reuses the already-computed f̄_k.

**Results — median across 19 active stations:**

| Metric | Median value |
|--------|-------------|
| Baseline RMSE | 0.518 mm |
| Anchor-only RMSE | 0.343 mm |
| Full ARX RMSE | 0.401 mm |
| Anchor improvement | **+22.9%** |
| ARX bonus over anchor | **−3.9%** (ARX is worse) |
| Total ARX improvement | 19.2% |

**The core finding:** the anchor-only model captures all of the improvement (22.9%), and the full ARX model is slightly worse than anchor-only (−3.9% bonus at median). The ARX model overfits the training dynamics. Anchor-only is both simpler and more accurate.

**Per-station summary (19 active stations):**

| Station | Base (mm) | Anchor (mm) | ARX (mm) | Anchor% | ARX bonus% |
|---------|-----------|-------------|----------|---------|------------|
| JINHU_XIN | 1.75 | 0.40 | 0.53 | +78.2% | −3.6% |
| ZHENGMIN | 1.04 | 0.26 | 0.21 | +71.9% | +1.5% |
| JIUZHUANG | 3.10 | 1.00 | 0.80 | +65.0% | +0.4% |
| HUNAN | 0.33 | 0.21 | 0.24 | +53.4% | +2.4% |
| YUANCHANG | 1.16 | 0.65 | 0.79 | +41.2% | −10.6% |
| KECUO | 0.58 | 0.34 | 0.36 | +31.8% | −11.3% |
| TUKU | 0.61 | 0.34 | 0.40 | +26.0% | −3.3% |
| GUANGFU | 0.48 | 0.29 | 0.29 | +23.1% | +0.2% |
| XINSHENG | 0.39 | 0.27 | 0.30 | +24.6% | −9.2% |
| HUWEI | 0.48 | 0.30 | 0.34 | +22.9% | −2.1% |
| HONGLUN | 0.45 | 0.35 | 0.39 | +20.2% | −5.9% |
| XIUTAN | 0.52 | 0.46 | 0.47 | +16.1% | −11.9% |
| YIWU | 0.36 | 0.32 | 0.30 | +11.4% | +2.1% |
| NEILIAO | 0.51 | 0.48 | 0.48 | +8.6% | −7.4% |
| JIAXING | 0.30 | 0.30 | 0.30 | +7.9% | −0.7% |
| QIAOYI | 0.22 | 0.18 | 0.22 | +7.4% | −3.9% |
| BEICHEN | 0.55 | 0.49 | 0.60 | +4.4% | −5.1% |
| XIZHOU | 0.26 | 0.25 | 0.29 | +3.0% | −8.2% |
| TANQIFENXIAO | 0.67 | 0.81 | 0.96 | −9.0% | −5.1% |

Only 4 of 19 stations show a positive ARX bonus (ZHENGMIN, JIUZHUANG, HUNAN, YIWU — all small, +0.4% to +2.4%). At 15 of 19 stations the full ARX is worse than anchor-only.

**Why the anchor helps.** The static baseline predicts absolute MLCW from cumulative InSAR: `f̄_k × x(i)`. If the ratio shifts even slightly between training and hold-out — a 0.5% drift accumulates to 1.5–2.5 mm over a 3–4 year window. The anchor model eliminates this level offset by starting from the known MLCW state and predicting only the increment, which is much smaller than the cumulative absolute value.

**Why full ARX does not add value over the anchor.** phi_k ≈ 1.0 adds nothing beyond the anchor's recursive structure. beta_k overfits training-window seasonal patterns that do not repeat identically in the hold-out. gamma_k introduces per-epoch noise (smoothness_ratio > 2.5 at TUKU), amplifying rather than reducing prediction error.

**Ablation outputs:**
- `results/arx/ablation/ablation_allstations.csv` — per-station: RMSE (base, anchor, ARX), anchor%, bonus%, total%
- `results/arx/ablation/{STATION}_ablation.csv` — per-depth ablation for each active station
- `results/arx/ablation/fig_ablation_summary.png` — stacked bar: anchor improvement vs ARX bonus
- `results/arx/ablation/fig_ablation_tuku_ts.png` — TUKU time series at 30, 60, 120, 200 m

**Note on earlier figures.** The 67–97% improvement figures reported in `discussion_20260517_arx_results.md` §3 were based on a different RMSE computation (likely short-fold or in-sample). The authoritative numbers are those above from the ablation study, which use the same walk-forward folds and the same RMSE definition throughout.

---

### 13.3 Best-performing tested method: anchor-only (station-level method selection ongoing)

**Note:** The results in this section establish anchor-only as the best-performing candidate among the methods tested to date. Final station-level method selection has not been made — this is a finding from the exploration phase, not a production decision.

The anchor-only model is the best-performing tested temporal predictor across all active stations:

```
Ŷ_k(i) = Y_k(t_last)  +  f̄_k × (x(i) − x(t_last))
```

where:
- `Y_k(t_last)` — the most recently observed MLCW value at depth k (last row of `{STATION}_5m_grid.csv` with non-NaN values)
- `f̄_k` — the training-window direct ratio median (already in `results/direct_ratio/{STATION}/{STATION}_direct_ratio_stats.csv`)
- `x(i) − x(t_last)` — the InSAR increment since the last MLCW observation

This formula requires no OLS fitting and no new parameters. It is a drift-corrected version of the static ratio that eliminates the level offset at the prediction start date.

For the 20 shut-down stations (no MLCW after 2021-11), the same formula applies with `t_last` set to the last available MLCW observation before shutdown. This is equivalent to the static baseline after `t_last` except that it removes the level offset accumulated between the InSAR reference epoch (2015-01-16) and the anchor date.

---

### 13.4 Three stations with ratio instability

At three stations — **TANQIFENXIAO** (anchor improvement = −9.0%), **XIZHOU** (+3.0%), and **BEICHEN** (+4.4%) — neither the anchor-only model nor the full ARX improves meaningfully over the static baseline. TANQIFENXIAO and BEICHEN show negative total improvement (−14.0% and −6.9% respectively). The physical explanation is **ratio instability**: the value of f̄_k computed over the 2015–2021 training window does not represent the 2022–2025 period. The ratio has shifted, so any model that uses that training-window f̄_k (whether static, anchor, or ARX) will carry the same error.

The most likely physical causes are: a new pumping well opened nearby after 2021, a change in the local aquifer pressure regime driven by the 2021–2024 drought recovery, or a geological boundary that became more active.

**Diagnostic needed:** plot the epoch-by-epoch ratio Y_k(i)/x(i) from 2015 to 2025 for these three stations. If the ratio drifts upward or downward after 2021, that confirms ratio instability is the cause.

**Candidate fix if drift is confirmed:** rolling-window re-estimation of f̄_k using the most recent 2 years of training data rather than the full 2015–2021 window. This targets the specific failure mode without adding model complexity at the other 16 stations where the training-window f̄_k is stable.

---

### 13.5 Prophet pilot at TUKU

**Motivation.** The anchor-only model captures all available information from the initial state and the cumulative InSAR trajectory. A next question is: can an additive time-series model (Prophet, as used by Hung et al. 2025 for a full-column extensometer in Taiwan) add value on top of the direct ratio?

**Setup.** Hung et al. (2025) applied Prophet univariately (trend + yearly seasonality, no external regressor) to a total-column extensometer over a 4-month hold-out. Our adaptation differs: (i) per-depth 5 m slabs, not total column; (ii) InSAR added as an exogenous regressor via `m.add_regressor('insar')`; (iii) same 4-fold walk-forward validation as the ARX comparison; (iv) hold-out window is 1 year per fold (far harder than 4 months). Fourteen representative depths were tested.

**Results by depth zone:**

| Depth zone | Prophet vs baseline | ARX vs baseline | Winner |
|------------|--------------------:|----------------:|--------|
| Shallow (0–75 m) | −62% to −218% (degrades) | mixed | Static baseline |
| Mid-range (100–225 m) | −47% to +82% (mixed) | −45% to +56% (mixed) | ARX at most depths |
| Deep (225–275 m) | +4% to +66% | +23% to +78% | ARX (modest edge) |

Prophet hurts at shallow depths because per-slab signals are small (< 0.5 mm range), and Prophet's trend component adds variance rather than removing it. The most striking improvement in Prophet is at 200 m (+82%) and 250 m (+51%), where the deep clay has high per-slab amplitude and a smooth, monotonically increasing trajectory. ARX still edges Prophet at most depths; only at 100 m and 225 m do they perform similarly.

**Practical conclusion.** Across the depth profile, ARX is superior to Prophet for this application. The static proportionality model remains optimal for 0–75 m. Below 100 m, ARX (or the simpler anchor-only formula) adds genuine value. Prophet does not provide a consistent improvement over ARX at any depth zone and adds substantially more model complexity.

**Note on 180 m.** Both models still produce large absolute errors at 180 m (Prophet: 2.25 mm, ARX: 1.0 mm). This layer shows the strongest acceleration in 2022–2025 — a genuine non-stationarity that neither a fixed-coefficient ARX nor a constant-regressor Prophet can fully track. A time-varying f̄_k or a regime-switch model would be needed here.

**Outputs:**
- Script: `prophet_tuku.py`
- All outputs at: `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\prophet_tuku\`

---

### 13.6 CLAUDE.md restructuring (2026-05-18)

Two substantive changes were made to `D:\112_PROJECT_002\CLAUDE.md` in this session:

**Unified Model Framework (new non-negotiable section).** Any proposed production method must be a single formula applied to all 39 stations. Model parameters may vary by station (that is curve-fitting, not model selection). Model structure may not vary station-by-station unless the switching criterion is pre-declared, automatic, data-derived, and written down before examining any hold-out results. This rule was added after the ablation document (§7) suggested different model choices for different station subgroups — which is valid as an internal diagnostic but not as a published scientific method.

**Nine creativity-relaxation edits.** The CLAUDE.md had accumulated rules framed as hard prohibitions ("never use X", "prefer Y instead of X"). Nine of these were converted to justification-required rules: "X is permitted if you can cite a specific failure in a saved CSV/JSON file that shows why the simpler approach is structurally insufficient." Key changes: prescriptive "prefer" table replaced with "established baselines" table; diagnostic file requirement (CSV or JSON must exist before proposing an upgrade); stage-specific validation (walk-forward for Stage 1, spatial LOO-CV for Stage 2); pilot scripts permitted before the markdown writeup; physical meaning required for any new hyperparameter.

---

### 13.7 Operational motivation for the GWL+InSAR track (2026-05-18)

**What happened in 2022.** During the 2022 drought cycle, raw MLCW measurements were entirely absent for the full year. The 2022 values in our current working dataset are a **reconstructed version** derived from all available surrounding observations — not original sensor readings. This is not a modelling assumption; it is a documented data gap. Any walk-forward fold that holds out 2022 is therefore validated against reconstructed data rather than primary sensor output.

**Why this motivates Track B.** The deeper motivation for building a GWL+InSAR prediction model (Track B) is operational resilience, not only the physics argument:

- InSAR (space agency operation) and GWL wells (national monitoring network) are maintained independently of the MLCW programme. They do not fail together.
- If further MLCW stations stop operating in the future, the Track B model continues producing per-depth compaction predictions at all 39 station locations and at all 8,577 grid points. It does not need to be retrained.
- Whatever MLCW stations remain active at that point become **live validation targets**, not calibration requirements. The framework remains scientifically testable even under network degradation.

**Implication for the walk-forward fold structure.** Within the 4-fold structure (hold-outs: 2022, 2023, 2024, 2025), fold 1 (train 2015–2021, hold-out 2022) is qualitatively the most operationally meaningful fold for the GWL model: it directly simulates the deployment scenario where MLCW is unavailable. Folds 2–4 test temporal extrapolation against genuine sensor data. Performance on fold 1 alone answers the question "how well does GWL+InSAR predict without any MLCW input?"

**Discussion document.** Full framing in `D:\112_PROJECT_002\discussions\discussion_20260518.md`, "Why use groundwater levels at all?" section, operational resilience block.

---

### 13.8 Two new methodological arguments added (2026-05-19)

**Smith et al. uncorrelated-head constraint.** Smith et al. (2021) required piezometric heads to be *uncorrelated* across depth intervals as a prerequisite for deformation apportionment — their method attributes InSAR to depths via head-timing correlations, so correlated heads = collinear signals = unresolvable depth attribution. Smith et al. found only one well in their study area that satisfied this requirement. In CRAF, confined aquifer units frequently respond synchronously during drought, which would cause Smith's method to fail at most wells. Our IHM approach (Track B) is immune: MLCW directly calibrates per-depth storage coefficients independently at each depth level — the correlation structure of head data is irrelevant to calibration quality. This is a fourth structural advantage over Smith et al., now documented in `discussion_literature_novelty_20260517.md` (§2.3) and `discussion_20260519.md` (§5.1 note).

**Three-part argument for InSAR necessity over GWL alone.** (1) GWL wells are sparse (306 wells for 8,577 grid points). (2) Only 21 of 39 MLCW stations have co-located GWL — interpolated heads are already required at 18 stations at the calibration stage. (3) InSAR native resolution is 40 m (~65,000 measurement points across CRAF per epoch, vs. 306 GWL wells) — no ground-based network approaches this spatial density. Added as an orange block to `discussion_20260518.md` Question 4 section.

---

## 14. GWL Feather Export and Linkage Diagnostic (2026-05-19)

### 14.1 Feather export

The HDF5 GWL data (`20260108_GWL_CRFP_daily_modeled.h5`, 100 stations, 306 wells) was exported to per-station feather files:

```
BASE\data\gwl\well_timeseries\{STATION}_gwl_timeseries.feather
```

100 files, one per station. Each file: `datetime` column (daily, 2000-01-01 to 2025-12-31, 9,497 rows) + one float64 column per well at that station, column name = numeric well code (e.g., `09050321`). Values in metres of piezometric head elevation. File sizes range from ~111 KB (single-well stations) to ~449 KB (8-well stations).

TUKU example: 3 wells (09050321, 09050331, 09050341), GWL range −5 to +9 m, 3,978 rows within InSAR window, 100% valid.

### 14.2 Inspection scripts

Two utility scripts were written and placed in `BASE\scripts\04_gwl_processing\`:

- **`inspect_gwl_feather.py`** — reads one station or all 100; computes per-well GWL stats in the InSAR window; saves `data\gwl\inspection_reports\gwl_feather_inspection.csv` (100-row summary)
- **`check_gwl_linkage.py`** — verifies three-way linkage (timeseries ↔ coordinates ↔ screen depths); saves `gwl_linkage_report.csv` (306-row per-well flags) and `gwl_linkage_summary.txt`

Run both with `$env:PYTHONPATH = ""; conda run -n fafalab python <script>` (PYTHONPATH contamination from `gemini_env` must be cleared first).

### 14.3 Linkage diagnostic findings

**Check A — timeseries ↔ metadata:** CLEAN. 0 orphan wells in either direction. Every feather column name is present in `gwl_allwells_flat.csv` and vice versa.

**Check B — coordinates:** 6 wells have missing/zero coordinates. None are MLCW-overlap stations; no impact on Stage 1 Track B.

**Check C — screen depths:** 120 / 306 wells (39.2%) lack screen depths. Of these, **26 are at MLCW-overlap stations** (the critical subset for Track B). Six MLCW-overlap stations have no screen depth for any of their wells: ERLUN, GUANGFU, KECUO, QIAOYI, XIUTAN, ZHENGMIN. For these six, a piezometric head timeseries exists but cannot be assigned to a specific aquifer unit without additional data. Options are: (1) use formation top depths from `gwl_material_summary.csv` as a proxy; (2) consult the original WRA borehole reports; (3) exclude these stations from Track B aquifer-unit assignment and treat their GWL as a station-level composite input.

### 14.4 Join key summary

To use feather data in analysis:

```python
import pandas as pd

# Load feather timeseries for one station
ts = pd.read_feather(r"BASE\data\gwl\well_timeseries\TUKU_gwl_timeseries.feather")
# Columns: ['datetime', '09050321', '09050331', '09050341']

# Join to metadata (coordinates, screen depths)
meta = pd.read_csv(r"BASE\data\gwl\well_info\gwl_allwells_flat.csv", dtype={"wellcode": str})
# Join key: wellcode (meta) == column name (ts)
```

The join is a single step; no multi-hop required.
