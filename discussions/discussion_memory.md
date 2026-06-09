# Discussion Memory: InSAR–MLCW–GWL Integration for Depth-Stratified Subsidence Monitoring

**Last updated: 2026-06-08**
**Current focus: Cumulative-domain solver pivot (2026-06-08); IHM-F v3 incremental solver structurally failed at TUKU; results/ reorganization complete**

---

## 1. Research Objective and Scientific Context

Taiwan's Choushui River Alluvial Fan (CRAF) has been sinking for decades. At its worst — along the coast during the 1990s aquaculture boom — the land surface was dropping more than 160 mm per year. When water leaves the pore spaces between sediment grains, the grains compact under the weight of the rock and soil above. Clay layers — the low-permeability barriers (aquitards) that separate the four main aquifer units — compress slowly and, in many cases, permanently. The land sinks. When pumping stops or slows, some sandy layers partially recover. But clay does not: the deformation is largely irreversible.

Understanding subsidence at this level of mechanism requires knowing not just that the surface moved, but which layer underground caused it — and how much. A satellite radar image can measure the total displacement of the ground surface to sub-centimetre precision. But a surface displacement of 20 mm could mean 20 mm of compaction in a single shallow aquifer, or 5 mm each from four aquifer units spread across 300 m of depth. The regulatory response differs completely between these two cases.

**The network-shrinkage reframing:** In November 2021, budget constraints led the Water Resources Agency (WRA) to shut down 20 of 39 Multi-Layer Compaction Monitoring Well (MLCW) stations. The remaining 19 continue to operate as of 2025. The budget trajectory points toward further reductions. This network shrinkage reframed the project: develop methods that produce depth-resolved compaction predictions using InSAR and groundwater level (GWL) data even after MLCW monitoring ends.

**Method exploration strategy:** We are testing multiple approaches to identify which methods are suitable for our datasets and can reach the research target. Two families of methods are under investigation:
- **Static scaling methods** — direct proportionality between InSAR surface displacement and per-layer MLCW compaction (f̄_k $\times$ InSAR). Simple, transparent, but structurally incapable of capturing sub-annual dynamics or time-lagged responses. Tested and found inadequate as a standalone predictor.
- **GWL-driven methods** — use piezometric head changes in confined aquifers as physical drivers of per-layer compaction, with InSAR providing the surface constraint. The IHM-F family (Candidate F of the Inelastic Head Model — two-regime, per-layer β_k) is the primary candidate here. Under active development; TUKU pilot run but unit-conversion bug unresolved.

Neither family has yet produced a model that clears the consistency gates required for spatial extension to the 8,577 grid points. Testing continues.

---

## 2. Study Area

The Choushui River Alluvial Fan (CRAF) encompasses approximately 1,800 km^2 in central-western Taiwan (Changhua County north, Yunlin County south). The basin exhibits a highly heterogeneous, eastward-coarsening structure:

- **Proximal fan (east):** Gravel-dominated, unconfined, minimal compaction
- **Middle fan:** Transitional, inter-bedded sand and mud
- **Distal fan (west):** Clay-rich, confined aquifers, severe compaction susceptibility

**Hydrogeological stratigraphy (upper 300 m):**
- **Aquifer F1:** Depth 19–103 m; thickness ~42 m
- **Aquifer F2:** Depth 35–217 m; thickness ~95 m (primary agricultural/industrial extraction; thickest aquifer)
- **Aquifer F3:** Depth 140–275 m; thickness ~86 m
- **Aquifer F4:** Depth 238–300 m; thickness ~24 m (deep industrial supply)

Separated by three clay-dominated aquitards (T1, T2, T3). The 39 MLCW stations measure compaction layer by layer from surface to 300 m depth; 37 stations are used for analysis (2 excluded: JINHU_XIN, LUNFENG_XIN, due to data quality).

**Seven-layer framework (depth ranges from source documents):**

| Layer | Type | Depth range (m) | Mean thickness (m) |
|-------|------|-----------------|-------------------|
| F1 | Aquifer | 0–103 | 42 |
| T1 | Aquitard | 35–129 | 14 |
| F2 | Aquifer | 35–217 | 95 |
| T2 | Aquitard | 140–223 | 23 |
| F3 | Aquifer | 140–275 | 86 |
| T3 | Aquitard | 238–293 | 11 |
| F4 | Aquifer | 238–313 | 24 |

#### Physical response zones (M13/M23) — critical for model design

The fan is divided into three zones with **opposite** GWL–surface-elevation correlations:

- **Proximal fan (M13, unconfined)**: Rising water table loads deep layers → surface *sinks*. GWL drop → surface *rises* slightly. Elastic coefficient: 0.034 cm/m (reversible). Pumping here does NOT cause subsidence.
- **Mid-fan (transitional)**: Both mechanisms operating simultaneously. Most MLCW stations are in this zone.
- **Distal fan (M23, confined)**: Rising piezometric head reduces effective stress → surface *rises*. GWL drop → surface *sinks*. Elastic: 0.176 cm/m. **Inelastic: 7.34 cm/m** (irreversible once head falls below historical minimum — the preconsolidation head).

The elastic-vs-inelastic distinction is the physical foundation for the IHM-F two-regime model. All MLCW monitoring stations are in mid-fan or distal-fan zones (M23 behavior). GWL values are raw piezometric head (m above MSL) — **never negate**; a head drop (negative $\Delta H$) drives compaction.

#### Key quantitative benchmarks (Choushui River Alluvial Fan)

- **GWL decline (1976–2010):** Ershui −40 m, Jiaxing −20 m, Beigang −22 m, Hefeng −18 m
- **Current decline rate (worst case, Yunlin zone):** −0.54 m/yr
- **Total groundwater storage loss:** 2.5 billion m^3 (1976–2011); ~70 million m^3/yr average
- **Cumulative subsidence:** Dacheng (Changhua) >210 cm; Yuanchang (Yunlin) >130 cm (1992–2009)
- **Current hotspot (Tuku–Yuanchang):** 4.2–5.2 cm/yr (2011–2022 GNSS)
- **Historical peak:** 12.2 cm/yr (2003 drought)
- **Storage coefficients:** Unconfined (F1) ~0.15; Confined (F2–F3) ~0.0019
- **Inelastic coefficient at Hefeng (distal fan):** 7.34 cm per 1 m head drop below preconsolidation level

*Sources: `docs/choushui_background_search.md`, `docs/CRAF_groundwater_pumping_electricity_report.md`, `docs/濁水溪沖積扇地下水位與地表高程互動之模式與應用_English.md` (in InSAR_MLCW_v2 repo). Background docs updated 2026-06-02 with findings from Hung et al. (2021) WRR, Chu et al. (2024) Environ Earth Sci, Hung et al. (2025) Eng Geol, Patra et al. (2025) Environ Earth Sci, Tatas & Chu (2024) Water Resour Manage, and Hsu et al. (2021) Sci Adv.*

---

## 3. Datasets

### 3.1 MLCW (Multi-Layer Compaction Monitoring Wells)

**Primary input:** `{STATION}_reconst_grouped.csv` in `data/mlcw/group_byLayer_reconstr/`
- Per-station MLCW layer-aggregated timeseries: datetime + 6 columns (F1, T1, F2, T2, F3, F4)
- Layer assignments via ring-to-hydrogeological classification (complete for 37 stations)
- Units: mm; negative = compaction

**Data quality:** 37 stations, 700+ epochs per station (2015-01 to 2025-12), ~25,900 station-epoch pairs. Values are relative to 2015-01-16 (InSAR reference epoch).

**Derived MLCW products:**
- `data/mlcw/modeled_nojump/detrended/` — 39 stations, batch detrended (intercept + linear + annual harmonic removed)
- `data/mlcw/modeled_nojump/nojump/` — 39 stations, jump-corrected
- `data/mlcw/modeled_nojump/trend_only/` — 39 stations, trend-component only
- `data/mlcw/group_byLayer_modeled/{STATION}_modeled_grouped.csv` — IHM-F model output (not an input)

### 3.2 InSAR Timeseries

**Primary input:** `mlcw_interp_insar_IDW_extend.feather`
- 39 rows (MLCW stations) $\times$ 791 columns (6 metadata + 785 epochs)
- Cumulative vertical displacement from 2015-01-16 to 2025-12-11 (5-day intervals)
- Units: metres; negative = subsidence

**Secondary input:** `gridpnt_500m_interp_insar_IDW_extend.feather`
- 8,577 rows (500 m grid points) $\times$ 790 columns
- Same temporal grid; used for Stage 2 spatial extension

### 3.3 Groundwater Level (GWL)

**Primary input:** `mlcw_gwl_timeseries/` — 189 MLCW-timeline-aligned feather files (per MLCW station, per assigned GWL well). Daily timeseries 2000-2025, units: metres MSL (piezometric head). **Never negated.**

**Join key:** `gwl_to_mlcw_layer_assignment_v3.csv` (191 rows, 37 stations). Use v3 only; v1/v2 superseded.

**Well metadata:** `gwl_allwells_flat.csv` (306 wells) — use `elev_leveling_m` for head-to-depth conversion.

### 3.4 Storage Coefficient Reference Values (2S-TOOL)

- 191 station-layer pairs: 134 OK, 57 NEG_SKV, 6 errors
- Summary: `data/gwl/2stool_outputs/2stool_results_summary.csv`
- **Diagnostic reference only** — values over-predict by 10–300$\times$ at 5-day resolution; not used as fixed priors

### 3.5 Model Outputs and Diagnostics

**Walk-forward prediction (InSAR→MLCW, no GWL) — OBSOLETE (superseded by cumulative solver):**
- `results/prediction_v1_OBSOLETE_static_fbar/` — TUKU: static f̄_k model
- `results/prediction_v2_OBSOLETE_detrended_lag_aware/` — TUKU: detrended + lag-aware model

**Seasonal harmonic analysis (37 stations):**
- `results/seasonal_insar_harmonic/{STATION}/` — 8 files per station: phase stability summary, per-year harmonic stability, temporal holdout, reconstruction metrics, InSAR harmonic timeseries (feather)
- `figures/seasonal_insar_harmonic/{STATION}/` — 3 figures per station: full timeseries, seasonal zoom, metrics bar chart

**Ring cross-correlation (39 stations):**
- `results/ring_cross_correlation/{STATION}/` — 4 JSON files per station: raw timeseries, detrended, grouped, grouped lagged
- `figures/ring_cross_correlation/{STATION}/` — 4 heatmap PNGs per station

**Ceiling test (OBSOLETE — 2026-06-08):**
- `results/ceiling_test_OBSOLETE_insar_only/TUKU_ceiling_test.csv` — TUKU ceiling test metrics (superseded by cumulative solver)

**Results reorganization (2026-06-08):** All obsolete results were renamed with `_OBSOLETE_<reason>` suffixes rather than deleted. See PROGRESS.md §5 for the full convention table. Active outputs remain unsuffixed in `results/ihmf/v3/`, `results/stress_strain/`, `results/ring_cross_correlation/`, `results/seasonal_insar_harmonic/`, `results/gps_vs_mlcw/`, and `results/data_analysis/`.

**Tau search campaign (TUKU pilot):**
- `tau_demo_TUKU/results/` — 9 files: tau_results.csv, tau_mse_curves.csv, reconstruction_metrics.csv/json, evaluation_summary.json, reconstruction_timeseries.csv, seasonal_ske_diagnostics.csv, seasonal_ske_reference.csv, tuku_aligned_data.npz

**IHM-F model fits:**
- `results/ihmf/{STATION}_{LAYER}_ihmf_results.json` — per-layer fit output
- `results/ihmf/v3/TUKU_v3_results.json` — v3 joint inversion pilot (has known unit-conversion bug: R^2_insar=−6.48)

**Stress-strain analysis:**
- `results/stress_strain/` — preconsolidation head estimation outputs

### 3.6 Documentation and Reference

- `docs/figure_standards.md` — A4/300dpi matplotlib standards (locked 2026-05-31)
- `docs/tau_search_methodology.md` — full tau search lessons, $h_{c}$ definition, script inventory
- `docs/seasonal_harmonic_findings.md` — reconstruction tables, phase stability gate, locked decisions
- `docs/data_paths.md` — complete data file inventory
- `docs/run_commands.md` — command catalog for all active scripts
- `docs/script_inventory.md` — active script directory tree with descriptions
- `docs/choushui_background_search.md` — CRAF study area background
- `docs/choushui_skeletal_storage_coeffs.md` — $S_{ske}$/$S_{skv}$ summary by layer
- `docs/s_ske_skv_tables.md` — seasonal $S_{ske}$ wet/dry values (31 stations, 10 cycles)
- `docs/gwl_to_mlcw_layer_assign_guide.md` — GWL-to-MLCW layer assignment methodology

### 3.7 Active Script Modules

- `scripts/15_prediction/` — 10 Python files: InSAR→MLCW walk-forward prediction pipeline (main, io_loader, walkforward, spatial_kriging, reporter, paths, plot_tuku_timeseries, export_tuku_json, ceiling_test)
- `scripts/13_seasonal_insar/` — 2 Python files: InSAR→MLCW seasonal harmonic characterization + reconstruction visualization
- `scripts/10_ihmf/` — 6 Python files: IHM-F model fitting (fit_ihm_f, ihmf_model, ihmf_io, ihmf_plots, ihmf_detrend, diagnose_seasonal_ske)
- `scripts/12_stress_strain/` — 2 Python files + HAND_CALCULATION_GUIDE.md: preconsolidation head estimation
- `scripts/11_data_analysis/` — 8 diagnostic scripts + ring_cross_correlation.py
- `tau_demo_TUKU/` — 7 sequential pilot scripts + results/

---

## 4. The IHM-F Model (GWL-Driven, Under Exploration) — v3 Architecture (updated 2026-05-29)

### 4.1 Physical Formulation

The correct model follows Smith et al. (2021) and `discussions/physics_rules_research_problem.md`. **InSAR is the total surface target, not a per-layer predictor.** GWL is the only driver of per-layer compaction.

**Step 1 — Per-layer compaction (MLCW + GWL only, no InSAR):**
```
Δb_j(t) = S_j · ΔH_j(t − τ_j)

  S_j = S_ke  (elastic: ΔH_j ≥ 0)
  S_j = S_kv  (inelastic: head below pre-consolidation threshold h_c)
  τ_j = non-negative integer (5-day epoch units); τ_max = 73 (≈ 1 year)
```

**Step 2 — Surface alignment (InSAR only, $S_{j}$ and $\tau_j fixed):**
```
α · Δd_v(t) = Σ_j S_j · ΔH_j(t − τ_j)

  α ∈ (0, 1) — single scalar per station
```

Where:
- **$S_{ke}$, $S_{kv}$** — elastic and inelastic skeletal storage coefficients (mm/m, $\ge$ 0)
- **$\Delta H$_j(t)** — GWL change in the aquifer assigned to layer j (m)
- **$\tau_j** — hydraulic lag, always a non-negative integer in 5-day epoch units
- **$\alpha$** — fraction of total surface subsidence explained by the modelled layers
- **$\Delta$ d_v(t)** — InSAR surface displacement (total target)

**$\tau$ physical scale (5-day epochs):** $\tau$=1 → 5 days; $\tau$=6 → ~1 month; $\tau$=24 → ~4 months; $\tau$=73 → ~1 year.

**Epoch spacing confirmed (2026-05-29):** Both InSAR and MLCW are reconstructed at 5-day intervals (785 InSAR epochs, 1572 MLCW epochs, median gap = 5 days for both).

### 4.2 Joint Constrained Solve (Single Uniform Procedure)

Steps 1 and 2 are solved simultaneously as constrained linear least squares for each fixed $\tau$ combination:

```
θ = [S_ke,1, S_kv,1, ..., S_ke,N, S_kv,N, β]   where β = 1/α

Design matrix stacks:
  MLCW rows — pin each S_j from per-layer MLCW observations
  InSAR rows — pin β from total surface displacement (weight λ = 1/N)

Bounds: all S_j ≥ 0,  β ≥ 1
Solver: scipy.optimize.lsq_linear (already in fafalab)
```

**$\tau$ grid search:** Per-layer integer search $\tau_j $\in$ {0, 1, …, 73}. $\tau$ is never passed to a continuous solver — fractional $\tau$ is physically meaningless.

**No Path A / Path B routing.** The two-path strategy based on 2S-TOOL $S_{kv}$ sign is retired. All 191 pairs use identical procedure. 2S-TOOL values are diagnostic reference only.

### 4.3 Version History

**v1 (2026-05-28):** Used `b_k · Δx(t) + S_ske · ΔH_k(t)` per layer. InSAR as per-layer predictor — physically wrong. Result: b_k = 0 at F1, F3 (GWL–InSAR collinearity masked GWL signal).

**v2 (2026-05-29 morning):** Removed long-term trend before fitting; retained `β_k · x^d(t)` per layer — still physically wrong, InSAR still in per-layer equation.

**v3 (2026-05-29, current):** `b_k` and `β_k · x` terms removed entirely. InSAR enters only in Step 2 as total surface target. Architecture matches Smith et al. (2021) F12 and user's problem statement. $\tau_max corrected to 73.

---

## 5. Static Scaling Baseline (Direct Proportionality)

**Method:** Direct ratio f̄_k = median[Y_k(i) / x(i)] across all epochs
- No solver, no hyperparameters
- Computed for all stations
- Batch results show substantial spatial heterogeneity across the fan
- High correlation between f̄_k and regularised depth-profile estimate at the pilot station

**Use case:** Diagnostic comparison floor. These results serve as the baseline that GWL-driven methods must demonstrably beat.

---

## 6. Walk-Forward Validation Structure

**Four folds (expanding window):**
1. Train: 2015-01 to 2021-11 (500 epochs) | Test: 2022 hold-out (100 epochs)
2. Train: 2015-01 to 2022-12 | Test: 2023 hold-out (100 epochs)
3. Train: 2015-01 to 2023-12 | Test: 2024 hold-out (100 epochs)
4. Train: 2015-01 to 2024-12 | Test: 2025 hold-out (100 epochs)

**Fold 1 is operationally critical:**
- MLCW 2022 data are entirely reconstructed (no raw sensors)
- Tests deployment when MLCW is unavailable
- Simulates future use case: predict per-layer compaction from InSAR + GWL only

**Primary metric:** RMSE per (station, layer, fold). Secondary: Pearson r (temporal tracking). Tertiary: P05–P95 uncertainty band coverage.

**Final production model:** Train on full 2015–2025 window after validation confirms no degradation from additional data.

---

## 7. Spatial Extension to Grid (Stage 2, Pending)

**Objective:** Extend per-layer $S_{ke}$, $S_{kv}$, $\tau_j and per-station $\alpha$ from 37 MLCW stations to 8,577 grid points (500 m spacing). Note: spatial extension is deferred until single-station v3 pilot is validated.

**Method (planned):** Kriging with external drift (KED)
- Covariate: GWL trend at each grid point (from 306-well network)
- Physical rationale: GWL gradient drives compaction; similar GWL trends should produce similar compaction parameters
- Variogram fitted from 2015–2021 full-station period; transferable to 2021–2025 sparser period if validation confirms temporal stability

**Contingency:** If kriging fails or KED covariate insufficiently correlates, fall back to ordinary kriging (no covariate).

---

## 8. Collinearity Diagnosis — Resolved by v3 Architecture (updated 2026-05-29)

**Problem (identified 2026-05-28):**
- F1 raw Pearson r($\Delta H$, x) = 0.66 (collinear; solver in v1/v2 assigned credit to InSAR via b_k)
- F3 raw r(y, $\Delta H$) = 0.15 (GWL coupling masked by shared long-term trend)
- Post-detrending: F1 r = 0.19, F3 r = 0.29 (GWL signal emerges)

**Resolution (v3 architecture, 2026-05-29):**
The collinearity problem is resolved structurally — not by detrending as a preprocessing step, but by removing InSAR from the per-layer equation entirely. In v3, GWL and InSAR no longer compete in the same fitting step. GWL drives Step 1 (per-layer); InSAR is the target in Step 2 (surface alignment only). The `b_k · x` term that created the collinearity problem does not exist in v3.

---

## 9. Files and Quick Reference

### Critical Cross-Repo Paths (Windows + Linux HGFS)

| File | Windows | Linux (VM) |
|------|---------|-----------|
| PROGRESS.md (status) | `D:\112_PROJECT_002\PROGRESS.md` | `/mnt/hgfs/112_PROJECT_002/PROGRESS.md` |
| IHM-F config | `D:\1000_SCRIPTS\.../data/ihmf_config.json` | `/mnt/hgfs/1000_SCRIPTS/.../data/ihmf_config.json` |
| MLCW input | `D:\1000_SCRIPTS\.../data/mlcw/group_byLayer_reconstr/` | `/mnt/hgfs/1000_SCRIPTS/.../data/mlcw/group_byLayer_reconstr/` |
| GWL timeseries | `D:\1000_SCRIPTS\.../data/gwl/mlcw_gwl_timeseries/` | `/mnt/hgfs/1000_SCRIPTS/.../data/gwl/mlcw_gwl_timeseries/` |
| 2S-TOOL results | `D:\1000_SCRIPTS\.../results/2stool/` | `/mnt/hgfs/1000_SCRIPTS/.../results/2stool/` |
| path resolver | `D:\1000_SCRIPTS\.../paths.py` | `/mnt/hgfs/1000_SCRIPTS/.../paths.py` |

### Key Data Files

- **`gwl_to_mlcw_layer_assignment.csv`** — 195 rows; join key mapping each MLCW layer to GWL well code
- **`gwl_allwells_flat.csv`** — 306 wells; master reference for screen depths, coordinates, statistics
- **`ihmf_config.json`** — 191 entries; per-layer-pair configuration ($\tau_max, warmstart values, feather file paths)
- **`2stool_results_summary.csv`** — 191 rows; $S_{kv}$, $S_{ke}$ reference values; status flags (OK/NEG_SKV/ERROR)

---

## 9.5 Expected Final Deliverables

### Per-Station Results (GWL-Driven Methods, all stations)

For each MLCW station, the final output will be:

1. **Per-layer compaction timeseries (2015–2025):**
   - 6 layer-grouped compaction predictions: F1, T1, F2, T2, F3, F4
   - Expressed as cumulative displacement from 2015-01-16 (mm)
   - Uncertainty bounds: P05–P95 range per layer per epoch
   - File format: CSV with datetime + 6 layers + 6 uncertainty columns

2. **Per-layer model parameters:**
   - $S_{ke}$, $S_{kv}$ (elastic and inelastic skeletal storage coefficients, mm/m, $\ge$ 0) — per layer
   - $\tau_j (hydraulic lag, non-negative integer in 5-day epochs) — per layer
   - $\alpha$ (surface alignment scalar, 0 < $\alpha$ < 1) — per station
   - File format: JSON with per-station coefficient table (layers nested inside)

3. **Walk-forward validation metrics (4 folds):**
   - Fold 1 (2022 hold-out) reported separately — operationally critical
   - Per-fold RMSE, Pearson r, bias, coverage for each layer
   - Comparison to static scaling baseline: absolute and percentage improvement
   - File format: CSV with fold $\times$ layer $\times$ metric grid

### Spatial Grid Results (8,577 grid points, 500 m spacing)

4. **3D compaction field reconstructed (2015–2025):**
   - At each grid point and epoch: predicted compaction per layer
   - Via kriging-interpolated parameters applied to InSAR surface displacement
   - Central estimate (best guess) + uncertainty bounds (P05–P95)
   - File format: NetCDF4 (lat/lon $\times$ depth $\times$ time)
   - Enables regulatory questions: "Which aquifer is compacting most in this region? At what depth? In which years?"

5. **Depth-resolved attribution maps:**
   - Per-layer compaction contribution to total surface subsidence (%$f_{k}$)
   - Spatial field showing which layers dominate at each location
   - Enables prioritisation of groundwater management by depth and region
   - File format: GeoTIFF (lat/lon $\times$ layer) for GIS integration

### Validation Against Independent Data

6. **GWL-driven vs static scaling comparison:**
   - RMSE improvement across all stations and folds
   - Quantified benefit of adding GWL as co-driver beyond InSAR+MLCW alone
   - Station-by-station breakdown (where does GWL help most?)
   - Summary statistics: median improvement, outlier flagging

7. **Fold 1 zero-MLCW demonstration:**
   - Explicit evidence that IHM-F predictions are viable when MLCW is unavailable
   - RMSE at each station when trained on 2015–2021 MLCW but predicted on 2022 InSAR+GWL only
   - Demonstrates operational readiness for post-MLCW deployment

### Uncertainty Characterisation

8. **P05–P95 uncertainty bands:**
   - Per-layer uncertainty envelope from fold-to-fold variability and residual distribution
   - Propagated through spatial kriging to grid points
   - Uncertainty maps showing confidence in predictions (high confidence near monitoring stations; lower far away)
   - Enables risk-aware decision-making for infrastructure planning

### Interpretable Physical Output

9. **Attribution statements (per location, per layer, per year):**
   - "In 2024, Layer F2 at grid point X contributed 45% of total surface subsidence; elastic storage dominated."
   - "Between 2022–2023, Layer F4 transitioned from elastic to inelastic response when head fell below pre-consolidation threshold."
   - Derived directly from model structure; no secondary decomposition needed
   - Supports regulatory communication and scientific interpretation

---

## 10. Implementation Pipeline (as of 2026-05-29)

| Stage | Task | Status |
|-------|------|--------|
| 0 | Data assembly & QC | Complete |
| 1a | IHM-F module architecture (v1/v2, archived) | Complete |
| 1b | TUKU pilot v1/v2 (collinearity diagnosis) | Complete — revealed b_k=0 at F1/F3 |
| **1c** | **IHM-F v3 architecture (joint solve, $\tau_max=73, no $\beta_k$\cdot$ x)** | **Complete — 2026-05-29** |
| **1d** | **Multi-layer assembler + joint solver (v3 modules)** | **Pending — next step** |
| **1e** | **TUKU pilot v3** | **Pending** |
| **1f** | **Batch run (37 stations)** | **Blocked — pilot must pass** |
| 2 | Walk-forward validation (4 folds) | Pending |
| 3 | Spatial extension via kriging | Pending |
| 4 | Final production model & uncertainty maps | Pending |
| 5 | Manuscript & results dissemination | Pending |

---

## 11. Historical Completions (Reference)

The following are complete and archived; not active but valuable for understanding what was tried:

- **Direct ratio analysis (f̄_k)** — model-free baseline, 39 stations, complete
- **Stage 1 regularised regression** — deprecated in favour of direct ratio; TUKU outputs archived
- **ARX walk-forward & Prophet ablation** — explored temporal methods; anchor-only proved superior; both superseded by IHM-F
- **IDW spatial interpolation (Stage 2 baseline)** — complete; serves as comparison floor for kriging
- **2S-TOOL reference values** — 191 layers; used for Path A parameter initialization
- **$\alpha$ (compaction fraction) estimation** — GNSS, InSAR, kriging-refined; complete for all 37 stations
- **GWL feather export & linkage diagnostic** — 189 files, 100 stations; complete and QC'd (2026-05-19)
- **MLCW layer aggregation** — ring-to-hydrogeological classification complete for 37 stations
- **Stage 0 data prep** (P1–P3) — screen depth parsing, BME hydrofacies lookup; all complete

---

---

## 12. Iterative Experimental Campaign — InSAR→MLCW Prediction (2026-05-30 → 2026-06-02)

What follows is a chronological account of our attempts to predict per-layer MLCW compaction from InSAR surface displacement. Each phase describes what we tried, what failed, and what we learned — and how that failure directly motivated the next attempt. The narrative is intentionally written as a record of unresolved problems, not completed achievements.

---

### 2026-06-02 — IHM-F v3 audit, epoch alignment fix, TUKU pilot

**Bugs fixed:**
- Bug 1 (reversed lag): `dh_lag = dh_raw[:n-tau]` paired with `y_cut = y_raw[tau:]` — head drives future compaction. After fix: F2 $\tau$=11 epochs (55 days).
- Bug 4 (epoch alignment): `fit_ihm_f_v3.py` now builds common epoch window `[tau_max_all, T_full-1]`. All layers and InSAR on identical absolute axis. RMSE_InSAR dropped from 1,909,688 mm to 42.6 mm; R^2 from −823M to 0.543.

**TUKU v3 results (results/ihmf/v3/TUKU_v3_results.json):**
- $\alpha$=0.0197 | RMSE_InSAR=42.6 mm | R^2_InSAR=0.543 | RMSE_MLCW=1.186 mm
- F4: $S_{ke}$=0.029, $S_{kv}$=0.173, $\tau$=75d ✓ physical
- T1: $\tau$=365d AT TAU_MAX BOUNDARY — increase TAU_MAX to 120 epochs before batch
- Walk-forward $\alpha$ rising (0.023→0.163); walk-forward R^2_InSAR all negative (parameter overfitting)

**Strategic gate:**
- Paper headline confirmed: per-layer InSAR + MLCW depth attribution (not head-threshold rule)
- Tatas & Chu (2024) uses same study area but total subsidence, no MLCW, no InSAR — not a duplication
- Next: raise TAU_MAX, investigate regularization for cross-fold stability, then batch run

---

### Phase 1 — Raw lag search between GWL and MLCW (2026-05-30)

**What we tried:** We ran a grid search for the optimal hydraulic lag $\tau$ between groundwater level changes and MLCW compaction increments, using mean squared error as the objective function. Seven scripts in `tau_demo_TUKU/` implemented this at TUKU station.

**What failed:** The MSE grid search latched onto $\tau$ $\approx$ 365 days for most layers. This was not a real hydraulic lag — it was the shared annual cycle in GWL and MLCW aliasing into the cross-correlation. Both signals rise and fall with the seasons, so any lag near one year produces a spurious correlation peak. The MSE curves were flat or monotone, indicating the objective function could not distinguish genuine coupling from seasonal coincidence.

**What we learned:** Detrending is mandatory before any lag analysis. Without removing the annual harmonic, the $\tau$ search recovers the calendar, not the physics.

*Scripts: `tau_demo_TUKU/01_run_tau_search.py`, `02_plot_timeseries.py`*

---

### Phase 2 — Detrended tau search with physical constraints (2026-05-30)

**What we tried:** We added 4-parameter detrending (intercept + linear trend + annual harmonic via OLS) to both GWL and MLCW signals before the $\tau$ grid search. We then tested two approaches: (a) free OLS fitting of elastic and inelastic storage coefficients at each candidate $\tau$, and (b) a joint 4-parameter grid search ($\tau$, $S_{ske}$, $S_{skv}$, compressible thickness b) with physically bounded parameter ranges from the literature. We also introduced a constrained cross-correlation approach — selecting $\tau$ by maximizing |r| only among lags where the OLS slope was non-negative (physically valid).

**What partially worked:** After detrending, $\tau$ values dropped from 300–350 days to 15–160 days for most layers. The constrained CCF produced more stable and interpretable $\tau$ estimates than raw MSE minimization. Outlier filtering (5$\times$ MAD on incremental MLCW) removed physically impossible spikes and improved F3 RMSE by 39%.

**What failed:** The 2S-TOOL-derived storage coefficients, when held fixed, over-predicted compaction by 10–300$\times$ at 5-day resolution — producing negative R^2 for all layers. These coefficients capture multiannual skeletal compaction; they are fundamentally different quantities from what a 5-day incremental model requires. The joint search found that compressible thickness b was only 0.4–16% of the classified layer span — meaning only a thin active zone within each layer compacts at the 5-day timescale.

**What we learned:** (1) 2S-TOOL values are diagnostic reference only — never use as fixed priors. (2) F2 is the only TUKU layer with genuine multiscale GWL–MLCW coupling (detrended r=+0.69). F1, F3, F4 are trend-dominated (detrended r<0.07). (3) The T1 aquitard is effectively a pinchout at TUKU (b_max=0); T2 has only 5.29 m classified span. (4) Preconsolidation head $h_{c}$ = historical minimum groundwater level (前期最低地下水位), not a fixed offset — the "15 m above current" rule has no literature basis.

*Scripts: `tau_demo_TUKU/05_detrended_reconstruction.py`, `06_physical_ss.py`, `07_joint_search.py`*

---

### Phase 3 — Seasonal harmonic characterization of InSAR and MLCW (2026-05-31)

**What we tried:** Having established that the annual cycle dominates raw correlations, we systematically characterized the seasonal harmonic components of both InSAR and MLCW at three pilot stations (TUKU, XIUTAN, YUANCHANG). A 4-step pipeline tested: (Step 0) detrend method selection, (Step 1) harmonic decomposition adequacy per layer, (Step 2) InSAR harmonic characterization, (Step 3) per-year phase stability analysis with a formal pass/fail gate, and (Step 4) temporal holdout prediction of the seasonal component.

**What worked:** F2 seasonal phase is stable across years at all three stations (std_dphi1 = 18–41 days, below the 45-day threshold). Trend reconstruction via anchored f̄_k $\times$ InSAR achieves R^2_trend > 0.82 across all layers at all three stations. Linear detrending consistently outperforms moving-average methods (MA returns NaN on a 10-year record due to edge effects).

**What failed:** F3 and F4 seasonal components are not recoverable from InSAR — phase standard deviation exceeds 59 days at all three stations, meaning the timing of peak compaction jumps unpredictably year-to-year. The semi-annual component (182.5-day period) is below noise at all stations and was dropped from the model. Seasonal amplitude is not year-predictable — holdout skill scores are uniformly negative, meaning the mean training-period amplitude ratio predicts future years worse than simply guessing zero seasonal signal. The InSAR seasonal peak occurs at DOY 154–172 (early June), not March–April as initially assumed.

**What we learned:** The seasonal harmonic deliverable is a phase characterization map, not a year-by-year amplitude forecast. Only F2 carries a reconstructable seasonal signal from InSAR. Four bugs were identified and fixed during the 37-station batch run: the phase stability gate now requires positive amplitude correlation (corr_A1>0), layers with R^2_seasonal$\le$ 0 are correctly excluded from Tier 2, the InSAR harmonic timeseries feather file was added as a required export, and the ring cross-correlation script's data source was corrected from modeled to observed data.

*Scripts: `scripts/13_seasonal_insar/01_seasonal_harmonic_analysis.py`, `02_reconstruction_visualization.py`*

---

### Phase 4 — Walk-forward prediction pipeline with static f̄_k (2026-06-01)

**What we tried:** We built an 8-module prediction pipeline (`scripts/15_prediction/`) to test whether InSAR alone can predict MLCW compaction in a rigorous walk-forward setting. The model was a static proportionality: MLCW_pred(t) = anchor + f̄_k $\times$ (InSAR(t) − anchor), with f̄_k re-estimated per fold from training-window data only (no leakage). A Tier 2 variant added a phase-shifted seasonal harmonic for layers where the seasonal quality gate passed. Four-fold validation (hold-outs: 2022, 2023, 2024, 2025) was run on all 37 stations.

**What worked:** The pipeline ran without errors on all 37 stations (387 rows in the output). Per-fold f̄_k estimation successfully prevented data leakage — the full-record f̄_k from `reconstruction_metrics.csv` was quarantined as diagnostic-only. The 4-fold walk-forward structure, per-epoch prediction CSV, per-layer timeseries figures, and JSON evaluation export all functioned correctly.

**What failed:** The static f̄_k model is structurally incapable of capturing sub-annual MLCW dynamics. At TUKU, F2 Tier 1 skill vs. trend extrapolation was −0.53 (the InSAR-based prediction was 53% worse than simply drawing a straight line through the training data). F2 Tier 2 (seasonal correction) degraded all four folds — median RMSE increased from 4.59 mm to 5.97 mm. F3 RMSE was non-stationary across folds: 4.7 mm (2022) → 23.4 mm (2024), indicating the InSAR–MLCW ratio for deep layers drifts over time. The fold-1 median skill across all layers was +0.004 — near zero, meaning InSAR alone is only marginally better than linear trend extrapolation at the system level.

**What we learned:** The direct_ratio failure was replicated and quantified in a rigorous walk-forward framework. A single static coefficient cannot capture the InSAR→MLCW relationship. The prediction lines in the figures do not fluctuate — they are scaled xeroxes of InSAR, unable to lead, lag, or differ in shape from the surface displacement. This result independently validates the need for GWL data as a physical driver.

*Scripts: `scripts/15_prediction/main.py`, `walkforward.py`, `plot_tuku_timeseries.py`, `export_tuku_json.py`*

---

### 2026-06-09 — Objectives Correction: Gap-Fill + Prediction, Not Calibration

The project framing was corrected on 2026-06-09. Prior summaries described Objective 1 as "reconstruct per-layer compaction at MLCW stations (calibration problem)" — this was wrong.

The actual problem is a broken observational record: MLCW wells have stopped operating or reduced sampling from monthly to semi-annual/annual due to maintenance costs. The research is not about calibrating a physical model against MLCW measurements — it is about using InSAR and GWL to fill gaps in, and predict forward, a deteriorating monitoring network.

Objective 1 (well-scale): Use InSAR timeseries + GWL timeseries + borehole stratigraphy at each MLCW station to (a) reconstruct historical compaction time series where MLCW data is missing or sparse, (b) learn a predictive rule for next-month MLCW value, and (c) self-recalibrate when new sparse in-situ measurements become available. Success criterion: gap-fill RMSE below static interpolation baseline, positive walk-forward skill score.

Objective 2: Apply the method validated at one well to all remaining MLCW wells.

Objective 3: Predict subsurface compaction at 8,577 regional grid points with no MLCW stations, using InSAR + regionally-interpolated GWL + open-source hydrofacies model (1 km × 1 km resolution). Key open question: which hydrofacies product covers the CRAF, and are facies-to-parameter relationships validated in CRAF literature? This transfer pathway is unresolved.

Physical guardrail checks ($S_{skv}$/$S_{ske}$ ratio gates, sign constraints, Hung et al. 2021 bounds) remain valid as necessary conditions preventing impossible outputs — they are not the primary success criterion under the corrected framing.

Terzaghi consolidation theory formulated as a cumulative two-regressor NNLS (Script 12) is the leading candidate method for Obj 1. It has not yet been tested on held-out data. The immediate priority is a held-out gap-fill evaluation at TUKU before committing to this method. The one-week time constraint means this evaluation must happen before any further code development.

Current phase: method review. No method is finalized. Alternatives (simpler regression, data-driven) remain open if Terzaghi evaluation fails on gap-fill skill.

---

### Phase 5 — Detrended + lag-aware Tier 1 model (2026-06-01)

**What we tried:** We replaced the static f̄_k model with a two-component prediction: MLCW_pred(t) = [anchor + f̄_k $\times$ $\Delta$ InSAR(t)] + $\alpha$ $\times$ InSAR_detrended(t−$\tau$). The first term preserves the trend component (which works: R^2_trend > 0.82). The second term adds a lagged, scaled version of the detrended InSAR residual — capturing sub-annual dynamics that the static ratio misses. The procedure per fold: (1) detrend both signals via 4-parameter OLS on training data, (2) grid-search $\tau$ $\in$ [0, 73] epochs to maximize |correlation| between detrended residuals, (3) compute $\alpha$ as the OLS slope at optimal $\tau$, (4) extrapolate the training trend to the hold-out year and add $\alpha$ $\times$ InSAR_detrended(t−$\tau$). An $\alpha$ $\ge$ 0 constraint was enforced — negative $\alpha$ (anti-correlated residuals) triggers fallback to trend-only.

**What worked:** For F1 and T2, the detrended InSAR residual carries genuine predictive signal. F1 fold-2022 RMSE improved from 0.55 mm to 0.35 mm (−37%). T2 fold-2025 RMSE improved from 2.40 mm to 0.95 mm (−60%). These are the shallowest layers where surface InSAR is most directly coupled to subsurface deformation. The $\alpha$ $\ge$ 0 gate correctly prevents anti-correlated residuals from degrading predictions.

**What failed:** For F2, F3, and F4 — the main compacting aquifers — the detrended InSAR and detrended MLCW are anti-correlated. After removing trend + annual cycle, the residual InSAR signal moves in the opposite direction from the residual MLCW signal ($\alpha$ negative for all folds). The $\alpha$ $\ge$ 0 constraint forces fallback to trend-only, meaning the detrended component contributes nothing for these layers. The detrended correlation magnitude is moderate (|r| = 0.29–0.63), but the sign is physically wrong — InSAR shows subsidence while MLCW shows expansion in the residuals.

**What we learned:** This is the clearest evidence yet that InSAR alone cannot predict sub-annual dynamics in the deep productive aquifers. The residual anti-correlation is physically consistent with different response timescales: InSAR at the surface may capture elastic rebound while deep MLCW compaction continues inelastically. The InSAR-only ceiling is now quantified: trend works (f̄_k $\times$ InSAR, R^2 > 0.82), but sub-annual dynamics in F2/F3/F4 require a physical driver that InSAR cannot provide. GWL data is not optional for these layers — it is structurally necessary.

---

### Current Bottleneck (2026-06-01)

**The primary research objective has not yet been met.** After five experimental phases spanning two days, no method tested to date can predict per-layer MLCW compaction with sufficient accuracy to justify spatial extension to the 8,577 grid points.

**Unresolved failures:**
1. **InSAR-only prediction is structurally inadequate for F2/F3/F4.** The static ratio fails at sub-annual timescales (Phase 4). The detrended + lag-aware model cannot help because residual InSAR and residual MLCW are anti-correlated in these layers (Phase 5). Trend reconstruction works (R^2 > 0.82), but trend alone does not constitute a dynamic prediction.

2. **F2 seasonal correction degrades prediction in all folds.** The phase-shifted harmonic term built from training-year mean parameters is counterproductive when applied to hold-out years. The misalignment between the cumulative MLCW signal and the sinusoidal seasonal addend has not been resolved.

3. **F3 compaction ratio is non-stationary.** The InSAR–MLCW scaling factor drifts systematically across fold years (4.7 mm RMSE in 2022 → 23.4 mm in 2024). Deep-layer compaction may be governed by multi-year consolidation processes that 5-day InSAR sampling cannot resolve.

4. **Consistency gates for spatial interpolation are not cleared.** The walk-forward evaluation at TUKU does not meet the threshold for proceeding to kriging-based spatial extension.

**Active path forward:** The IHM-F v3 model (`scripts/10_ihmf/ihmf_model_v3.py`) — which uses GWL as the primary per-layer driver with InSAR providing only the surface constraint — has been designed and a TUKU pilot has been run. However, the pilot has a known unit-conversion bug (R^2_insar = −6.48, suggesting metre→mm conversion error). Fixing this bug and re-running the TUKU v3 pilot with detrending enabled is the immediate next step. The multi-layer data assembler (`ihmf_io_multilayer.py`) and the detrending module (`ihmf_detrend.py`) are complete and waiting to be wired in.

---

## 5. GWL Replacement-Well Gap Filling (2026-06-04)

### Physical context

When a monitoring well is damaged or reaches the end of its service life, the WRA drills a replacement at the same borehole location, in the same depth layer. The new well gets a code whose last digit increments: the original ends in `1`, the first replacement ends in `2`. The replacement has no record of the pre-installation head levels — but the original well, sitting in the same sediment layer a few metres away, measured them for years.

The piezometric head at the same depth layer in the same aquifer should not jump discontinuously between two wells. If both wells are open to the same screen interval, the head difference at any shared date reflects only measurement noise — it should be near-zero. That makes the original well's record a physically defensible proxy for the replacement well's missing early data.

### What was done

We filled missing pre-2020 values in every `2`-ending well in `data/gwl/well_timeseries/` using data from the matching `1`-ending well (same first 7 digits: 6-digit station ID + 1-digit layer code), taken from the same current timeseries file. The `old_twell_timeseries/` directory turned out to be unnecessary — every current file already contained the complete original well record.

### Scope

| Metric | Count |
|--------|-------|
| Stations modified | 15 |
| Wells filled | 34 |
| Pre-2020 values copied | ~248,000 (all pre-2020 gaps filled to 7305/7305 per well) |
| Unfillable wells | 9 across 5 stations |
| Verification | Random spot checks (3 stations): 100% match between w2 and w1 values |

### Unfillable — no original well record exists

- **CHENGUANG** 09060212 — w1 and w2 NaN in identical positions; old w1 also has no data for those dates
- **DOULIU** 090111M2 — 1675-day gap (2015–2019); old 090111M1 has only 285 days in 2005, no overlap
- **GANYUANXIN** 07260112, 07260122 — no w1 anywhere in current or old files
- **HUAQIAO** 07080122, 07080132 — no w1 anywhere in current or old files
- **SHILIU** 09010212 — no w1 (09010211) anywhere
- **YIWU** 09190112, 09190122 — no w1 anywhere

### Implication

The `well_timeseries/` files are now the canonical source of GWL records for all stations where a `1`-ending original well exists. The `old_well_timeseries/` directory is a historical snapshot with no additional information beyond what the current files already contain — it can be retired.

---

### Phase 6 — Per-epoch incremental regression with lsq_linear and Choushui bounds (2026-06-06)

**What we tried:** After diagnosing that the per-epoch incremental approach (Script 11: `tau_demo_TUKU/11_fit_ihm_f_incremental.py`) produced ~1× S_kv/S_ke ratios with plain OLS, we replaced OLS with `scipy.optimize.lsq_linear` and applied Choushui River Alluvial Fan literature bounds on S_ske [2.86×10⁻⁶, 3.87×10⁻⁴] m⁻¹ and S_skv [1.53×10⁻⁵, 3.00×10⁻³] m⁻¹ (Hung et al. 2021). We also moved from bulk mm/m coefficients to specific m⁻¹ coefficients, incorporating layer thickness b_j from `figures/prestage_data_analysis/layer_thickness.csv`. GPS diff timeseries (`TUKU_GPS_diff_timeseries.feather`) was used as the Step 2 target instead of InSAR.

**What failed:** All 6 layers failed the 8–100× S_kv/S_ke physical gate. Results from `tau_demo_TUKU/results/incremental_fit_results.json`:

| Layer | b_j (m) | S_kv/S_ke | n_elastic | n_inelastic | cum_obs (mm) | cum_pred (mm) |
|-------|---------|-----------|-----------|-------------|-------------|--------------|
| F1 | 16.83 | 5.35× | 1173 | 356 | −28.6 | −1.2 |
| T1 | 0.0 (null) | 1.12× | 1173 | 326 | −16.6 | −1.1 |
| F2 | 72.51 | 2.84× | 779 | 169 | −126.3 | −11.7 |
| T2 | 5.29 | 0.88× (impossible) | 1387 | 30 | −19.2 | −0.9 |
| F3 | 99.84 | 5.35× | 785 | 160 | −173.2 | −13.6 |
| F4 | 16.62 | 5.35× | 1447 | 19 | −33.0 | −0.7 |

F1/F3/F4 pinned at lower bounds (S_ske = 2.86×10⁻⁶ m⁻¹ minimum). T2 ratio < 1 is physically impossible — only 30 inelastic epochs, severely underdetermined. Global α_raw = 1.81 (clipped to 1.0); GPS cumulative = −501 mm vs model cumulative = −10 mm.

**Root cause confirmed (structural, not a code bug):** At 5-day cadence, ΔH per epoch ≈ 0.001–0.003 m. The secular multi-year head decline that drives bulk compaction produces these tiny per-epoch increments spread across ~1500 epochs. Per-epoch OLS/lsq_linear fits noise, not the secular consolidation signal. The cumulative magnitude gap (10–200×) is structural — not a bounds problem, not a regime mask problem, not a lag problem.

**What we also confirmed (NotebookLM validation, 2026-06-06):** All IHM-F Formulas 1–8 are mathematically correct. Formula 6 had a notation typo (s→t). Verification A from NotebookLM suggests testing the regime indicator keyed to lagged head H_j(t−τ) for large-τ layers — not yet tested.

*Script: `tau_demo_TUKU/11_fit_ihm_f_incremental.py`, results: `tau_demo_TUKU/results/incremental_fit_results.json`*

---

### Phase 7 — Single-layer cumulative stress-strain approach (directed 2026-06-06, COMPLETE)

**Physical rationale:** The per-epoch incremental domain is noise-dominated ($\Delta H$ ≈ 0.001–0.003 m per epoch; secular consolidation only visible in cumulative H(t)). The Terzaghi / Hung et al. (2021) two-regressor NNLS approach works on cumulative quantities:

$$b_j(t) = S_{ke,j} \cdot H_j(t-\tau) + (S_{kv,j}-S_{ke,j}) \cdot V_j(t)$$

where $V_j(t) = \min(0,\ \text{cummin}(H_j) - h_{c,j})$ is the virgin exceedance term — grows negative only when cumulative minimum head descends below $h_c$; zero during elastic recovery. Both $b_j$ and $H_j$ are zero-referenced to REF_DATE = 2015-01-16. NNLS enforces $S_{ke} \ge 0$, $S_{kv}-S_{ke} \ge 0$.

**Script:** `tau_demo_TUKU/12_stress_strain_per_layer.py`
**Results:** `tau_demo_TUKU/results/stress_strain_per_layer.{json,csv}`; 6 PNG plots in `tau_demo_TUKU/plots/results/stress_strain/`

**Per-layer results (REF_DATE=2015-01-16, 5-day cadence, TUKU pilot):**

| Layer | $b_j$ (m) | $S_{ke}$ (mm/m) | $S_{kv}$ (mm/m) | $S_{kv}/S_{ke}$ | R² | n_inelastic | Gate |
|-------|-----------|-----------------|-----------------|-----------------|-----|-------------|------|
| F1 | 16.83 | 0.883 | 3.198 | 3.6× | 0.607 | 356 (H-based) | FAIL |
| T1 | 0.0 (null) | 0.834 | 2.041 | 2.4× | 0.804 | 326 | FAIL |
| F2 | 72.51 | 0.525 | 13.176 | **25.1×** | 0.845 | 169 | **PASS** |
| T2 | 5.29 | 0.897 | 5.247 | 5.9× | 0.489 | 30 | FAIL |
| F3 | 99.84 | **0.0** | 19.712 | undefined | 0.754 | 160 | inelastic-only |
| F4 | 16.62 | 0.376 | 6.512 | **17.3×** | 0.546 | 18 | **PASS** |

$S_{ske}$ [m⁻¹] for passing layers: F2 = $7.2 \times 10^{-6}$, F4 = $2.3 \times 10^{-5}$ (both within Choushui bounds [$2.86 \times 10^{-6}$, $3.87 \times 10^{-4}$]).

**Physical interpretation of failures:**
- **F1 (3.6×, 356 inelastic epochs):** Head at HONGLUN well rarely descends below $h_c = -2.344$ m by more than 1–2 m — shallow aquifer elastic rebounds mask inelastic compaction. The two-regressor NNLS recovers a ratio above 1× (improvement over naive 1.15×) but insufficient inelastic dynamic range.
- **T2 (5.9×, only 30 inelastic epochs):** Severely underdetermined. The LUNZI well (09170121) rarely drops below $h_c = -8.457$ m; only 4.0% of epochs are inelastic. Ratio estimate is noise-dominated.
- **F3 (inelastic-only, $S_{ke}$=0):** NNLS drives $S_{ke}$ to zero because the elastic epochs in the cumulative scatter show no coherent recoverable trend with the assigned well (TUKU 09050331, r < 0.1). F3 compaction continues even during elastic head recovery — consistent with the very weak GWL–MLCW coupling identified in Phase 2.
- **F4 (17.3× vs 2S-TOOL 81.5×):** Factor-of-5 gap unexplained. Possible causes: (a) 18 inelastic epochs only (severely underdetermined for $S_{kv}$); (b) LIUZHUANG well (09080251, $\tau$=525 days) captures only attenuated head signal at depth; (c) 2S-TOOL uses a different compressible thickness definition.

**Open questions before batch run:**
1. F1: write H(t)–b(t) scatter plot colored by regime (elastic=blue, inelastic=red) — diagnose whether $h_c = -2.344$ m is too shallow, leaving most inelastic compaction misclassified as elastic.
2. F4: plot V_j(t) timeseries — with only 18 inelastic epochs, is the virgin exceedance term measurably nonzero?
3. T1: $b_j$ = 0 (T1 classified as 0 m span at TUKU) — T1 MLCW data is non-zero but span assignment is zero, causing S_ke/S_kv to represent undefined thickness; T1 results unreliable.

**Next action:** `tau_demo_TUKU/10_gwl_mlcw_overlay.py` — 3-panel (head, $h_c$, cumulative MLCW) for F1/F2/F3 to visually confirm regime classification and inelastic epoch distribution.

---

### Phase 8 — Diagnosing Script 12 ratio failures: collinearity and the joint-inversion degeneracy (2026-06-07)

**Problem:** After Script 12's two-regressor NNLS, four layers fail the 8–100× $S_{kv}/S_{ke}$ gate: F1 (3.6×), T1 (2.4×), T2 (5.9×), F3 ($S_{ke}$=0). F2 (25.1×) and F4 (17.3×) pass.

**Dead end explored — joint inversion over (thickness, $S_{ske}$, $S_{skv}$):**

The user proposed treating all uncertain parameters (total_m, aquitard_m, $S_{ske}$, $S_{skv}$) as unknown within bounded ranges and running a minimization to recover physical combinations. This was a reasonable physical intuition but turns out to be mathematically degenerate:

$$b_\text{pred}(t) = S_{ke} \cdot H(t) + (S_{kv}-S_{ke}) \cdot V(t), \quad S_{ke} = S_{ske} \times \text{total\_m} \times 1000$$

RMSE depends on $S_{ske}$ and total\_m **only through their product**. Halving total\_m and doubling $S_{ske}$ gives identical RMSE. The optimizer finds a flat ridge in (thickness × $S_{ske}$) space — every point on the ridge is equally optimal; the returned solution is arbitrary. **Thickness is best fixed at the borehole point estimate (mm precision).** The joint inversion over thickness is a dead end.

**Root cause of ratio compression confirmed — multicollinearity:**

At TUKU, 93% of the 772 epochs are inelastic (cumulative minimum GWL continuously sets new records). In this regime the virgin term $V_j(t) = \text{cummin}(H_j) - h_c$ simplifies to $V_j(t) = H_j(t) - h_c$, so $V_j$ becomes a linear shift of $H_j$. The two regressors $H$ and $V$ are nearly perfectly collinear. The simultaneous NNLS solver cannot separate elastic from inelastic deformation and compromises by inflating $S_{ke}$ and deflating $S_{kv}$, producing ratio compression.

This is a physical identifiability limit, not a code bug.

**Clarification on which ratio gate applies:**

The [8, 100]× gate is on the **specific-storage ratio** $S_{skv}/S_{ske}$ (m⁻¹ / m⁻¹), not the bulk ratio $S_{kv}/S_{ke}$ (mm/m / mm/m). After the two-thickness borehole correction (fine-grained thickness for $S_{skv}$, total span for $S_{ske}$), the specific-storage ratios are:

| Layer | $S_{ske}$ (m⁻¹) | $S_{skv}$ (m⁻¹) | Specific ratio | Bulk ratio | Gate |
|-------|-----------------|-----------------|----------------|------------|------|
| F1 | $2.12 \times 10^{-5}$ | $1.93 \times 10^{-4}$ | **9.1×** | 3.6× | PASS (specific) |
| T1 | $9.55 \times 10^{-5}$ | $2.75 \times 10^{-4}$ | 2.9× | 2.4× | FAIL |
| F2 | $4.94 \times 10^{-6}$ | $1.09 \times 10^{-3}$ | **221×** | 25.1× | FAIL (overshoot) |
| T2 | $5.50 \times 10^{-5}$ | $5.09 \times 10^{-4}$ | **9.3×** | 5.9× | PASS (specific) |
| F3 | null | null | undefined | undefined | — |
| F4 | $2.26 \times 10^{-5}$ | $3.92 \times 10^{-4}$ | **17.3×** | 17.3× | PASS |

The bulk vs. specific discrepancy is large for layers where total\_m >> compressible\_m (especially F1 and F2). **F1 and T2 actually pass the specific-storage gate.** The real failures are T1 (2.9×, undershoots 8×) and F2 (221×, overshoots 100×). The apparent bulk-ratio failures of F1 and T2 were an artifact of not converting correctly — now resolved.

**Which problem actually remains:**

- **T1 (specific ratio 2.9×):** Well `09050111` (same as F1, $h_c = -2.344$ m). The elastic-inelastic separation for T1 suffers from the same collinearity as F1. With 446 elastic epochs available, the decoupled two-step approach should recover a better $S_{ke}$ estimate, pushing the ratio above 8×.
- **F2 (specific ratio 221×):** Only 12.090 m of fine-grained material in a 106.284 m column. The $S_{skv}$ is extremely high because even small absolute inelastic compaction, normalized to 12 m, gives a large coefficient. Whether the true F2 $S_{skv}$ is physically 221× its $S_{ske}$ is debatable — F2's massive aquifer is mostly coarse sand, so inelastic deformation is concentrated in a thin clay layer. The literature upper bound for Choushui aquifer $S_{skv}$ is $1.20 \times 10^{-3}$ m⁻¹ (Script 07 BOUNDS); fitted value is $1.09 \times 10^{-3}$ m⁻¹, within literature bounds. The ratio gate failure here may reflect true physical behaviour at TUKU — not a fitting artifact.

**Viable path forward — decoupled two-step regression:**

Rather than simultaneous NNLS (which mixes collinear regressors), isolate the elastic regime first:
1. **Step 1:** OLS on elastic-only epochs ($H > h_c$, $V = 0$) to estimate $S_{ke}$ without inelastic contamination.
2. **Step 2:** Freeze $S_{ke}$; regress residuals $b(t) - S_{ke} H(t)$ against $V(t)$ via NNLS to estimate $S_{kv}$.
3. **Feasibility check:** Convert bulk coefficients to specific storage using borehole thicknesses; compare to Choushui literature bounds (from Script 07 `BOUNDS` dict) and the [8, 100]× ratio gate.

This approach is planned as an extension to `tau_demo_TUKU/12_stress_strain_per_layer.py` (new function `fit_two_step_decoupled`, new constant `LITERATURE_BOUNDS`). The existing NNLS results are preserved as comparison.

**Key locked findings from this phase:**
- Joint inversion over thickness + storage is degenerate — do not attempt.
- Specific-storage ratio $S_{skv}/S_{ske}$ is the correct gate metric, not bulk ratio.
- F1 and T2 pass the specific-storage gate already (9.1× and 9.3×).
- T1 fails (2.9×); F2 overshoots (221×); F3 undefined ($S_{ke}$=0).
- Collinearity in high-inelastic epochs is a physical identifiability limit, not a solver bug.

*Plan file: `C:\Users\FAFALAB\.claude\plans\linked-sauteeing-deer.md` (decoupled regression design)*

---

### Phase 9 — Circuit Breaker: Incremental Solver Cancellation at TUKU (2026-06-08)

**What happened:** Day 3 of the 7-day plan ran the TUKU GPS re-run with fixed α = 0.625. The incremental solver (`joint_solve_fixed_tau`) produced $R^2_{\text{MLCW,cum}}$ negative or NaN for all 6 layers. The model predicts 0.1–0.9 mm/yr net compaction; MLCW sensors record 8–15 mm/yr monotonic subsidence. The gap is 8–355× depending on layer.

**Physical mechanism of the failure:** The 5-day head oscillations (±2 m/yr at F2) approximately cancel over annual cycles — recharge raises head, pumping lowers it, net $\sum\Delta H \approx 0$. The model's elastic prediction follows this oscillation: slight expansion in wet years, slight compaction in dry years. But the MLCW records monotonic compaction every year regardless of whether head is rising or falling. The clay does not rebound when head briefly recovers because the water cannot flow back into the low-permeability pores fast enough, and the particle rearrangement from the historical stress maximum is structurally permanent.

**Why the incremental domain erases stress memory:** The transformation from cumulative head $H(t)$ to incremental head $\Delta H(t) = H(t) - H(t-1)$ is a first-difference operator. It converts a monotonic secular trend (−40 m over decades) into a stationary oscillatory signal (±0.002 m per 5-day epoch). The integration constant — the pre-consolidation stress maximum — is lost in this transformation. The Riley (1969) running-minimum formulation $V(t) = \min(0, \text{cummin}(H) - h_c)$ requires the cumulative head to reconstruct the stress history, but the incremental solver never sees $H$, only $\Delta H$. The regime mask can classify epochs correctly, but with only 2–36 inelastic events (new running minimums) in the monitoring record, there are too few inelastic increments to accumulate meaningful compaction.

**GWL data gap — the binding constraint:** The Day 2 GPS mask fix (Change 1) was correct in principle but could not help because F2 and F3 GWL data only starts in August 2012. The heavy-pumping era that drove head through $h_c$ happened before these wells were installed. The data simply does not exist. The step1_mask intersection across all 6 layers means any epoch where F2 or F3 GWL is NaN drops the epoch for all layers — the training window is 2012–2024 regardless of whether GPS is included in the mask.

**Why Script 12 (cumulative) succeeded where IHM-F v3 (incremental) failed:** Script 12 operates on cumulative $H(t)$ and $b(t)$ directly. Its two-regressor NNLS:
$$b(t) = S_{ke} \cdot H(t) + \delta \cdot V(t), \quad V(t) = \min(0, \text{cummin}(H) - h_c)$$
carries the full stress history through $V(t)$ — a term that never decreases, preserving permanent strain. The incremental solver's $\Delta b = S_k \cdot \Delta H$ has no equivalent memory variable. At TUKU, Script 12 produced physically valid specific storage ratios for F1 (9.1×), T2 (9.3×), and F4 (17.3×). F2 (221×) and F3 ($S_{ke}$=0) failed due to collinearity, not domain mismatch. The IHM-F v3 incremental solver failed on all 6 layers.

**Day 2–3 results summary:**

| Metric | Before α fix | After α fix | Plan target | Met? |
|--------|------------|------------|-------------|------|
| α | 0.034 (OLS artifact) | 0.625 (empirical) | 0.625 | ✓ |
| Step 1 n_epochs | 866 | 866 | ~1400 | ✗ (GWL gap, not GPS) |
| n_inelastic F1–F4 | 11–36 | 11–36 | 100–400 | ✗ (structural) |
| $R^2_{\text{MLCW,cum}}$ | unmeasured | all negative/NaN | ≥0.5 for ≥3/6 | ✗ (structural) |
| $R^2_{\text{insar}}$ | 0.805 (misleading artifact) | 0.107 (honest) | <0.1 expected | ✓ |

**Decision required:** The 7-day plan's incremental-solver path is structurally blocked. The user must choose between a cumulative-solver fork (Option A), per-layer Script 12 calibration (Option B), or data-driven fallback (Option C). Full post-mortem at `discussions/POST_MORTEM_INCREMENTAL_CANCELLATION.md`. PROGRESS.md updated with circuit-breaker status.

*Plan file reference: `plans/2026-06-07-alpha-fix-seven-day-plan.md` (Days 1–2 complete, Day 3 halted at gate 3d).*

---

### Phase 10 — Automated guardrails, documentation consolidation, and regional framework (2026-06-08)

**What was done:** After the circuit breaker on the incremental solver, we paused code development to build permanent validation infrastructure. Three artifacts were created: (1) `scripts/guardrails.py` — 500 lines implementing 10 automated physical-law checks with literature priors from Hung et al. (2021) WRR, TUKU borehole material classification, and a `GuardrailViolation` exception class that halts on sign-constraint violations; all 9 unit tests pass. (2) `discussions/PHYSICS_SAFEGUARDS.md` — 23 KB reference documenting 11 rules with full source citations (Terzaghi 1925, Riley 1969, Hung et al. 2021, MODFLOW 6 SUB/CSUB) for use by human readers and AI agents. (3) `docs/notebooklm_inventory.md` — complete catalogue of 21 NotebookLM notebooks across 4 tiers, with CLI commands and project-stage mapping, to standardize future literature queries.

**Regional framework design:** The station-by-station guardrails were recognized as too narrow — the Choushui River Alluvial Fan is a continuous depositional system where grain size, clay fraction, compressibility, and confinement all vary as continuous functions of Distance From Fan Apex (DFA). Six regional invariants were defined from NotebookLM queries: (I1) $S_{ske}$ nearly constant at $1.2 \times 10^{-4}$ m⁻¹ across the fan; (I2) $S_{skv}$ is a peaked function of DFA — maximum ~$1.5 \times 10^{-3}$ m⁻¹ at DFA ≈ 15 km (middle fan), declining toward the coast because distal clay is drainage-limited at human timescales; (I3) grain size declines exponentially with DFA, clay fraction follows a sigmoid; (I4) confinement transitions continuously from unconfined (DFA < 5 km) to fully-confined artesian (DFA > 30 km); (I5) compaction concentrates at 50–200 m depth (F2+F3 contribute ≥60% of inelastic compaction); (I6) subsidence ≤6 cm/yr current, ≤15 cm/yr historical. Three conservation laws were defined: (C1) per-layer compaction sum ≤ total surface displacement + 5 mm; (C2) preconsolidation head $h_c$ must become more negative with depth; (C3) elastic regime must produce expansion on head recovery. The framework was designed as a markdown reference, not Python code — the user correctly noted that regional physics rules should be documented before being encoded.

**What was also completed:** `scripts/10_ihmf/diagnose_cumulative_tuku.py` writes per-layer cumulative timeseries CSVs and diagnostic PNGs to `results/ihmf/v3/diagnostics/`, enabling rapid visual inspection of the two-regressor NNLS fits without re-running the solver. The `CLAUDE.md` Automated Guardrails section was added with the 10-checks table, literature priors, TUKU material classification, and usage pattern.

**Physical implication of the regional framework:** The peaked $S_{skv}$ function explains why F2 at TUKU (DFA ≈ 14 km) can have an extreme 221× specific-storage ratio — TUKU sits near the optimal clay-sand mix where inelastic drainage is fastest. The decline of $S_{skv}$ toward the coast means a distal station with higher clay content will likely show lower fitted $S_{skv}$ at observable timescales, because drainage time $\propto b^2/K_z$ exceeds the monitoring cadence. This resolves the apparent paradox of "more clay but less measured inelastic compressibility."

**Next:** The regional guardrails framework needs implementation as `scripts/regional_guardrails.py` with continuous DFA-based bounding functions. The sequential prediction script has not been started — the 1-week deadline for Phase 1 prediction is 2026-06-15. The three tactical options (cumulative-solver fork, per-layer calibration, data-driven fallback) remain unresolved.

*Files: `scripts/guardrails.py`, `discussions/PHYSICS_SAFEGUARDS.md`, `docs/notebooklm_inventory.md`, `scripts/10_ihmf/diagnose_cumulative_tuku.py`*

---

## Notes for Future Sessions

1. **PROGRESS.md is the source of truth** for current pipeline status, data state, and blocking decisions. Update it first when status changes.
2. **discussion_memory.md is a diary of methods, not a roadmap.** Do not enforce sequential ordering from this file.
3. **GWL sign convention:** MSL elevation. Never negate. Higher = rising head. Raw in all visualisations.
4. **Path resolution:** Use `paths.py` module (auto-detects OS) in Python. Documentation tables guide agents on each OS.
5. **Mandatory pre-implementation files:** Read PROGRESS.md + CLAUDE.md GUARDRAILS section before writing code.
6. **Collinearity is NOT a solver bug** — it is a physical identifiability limit. Flag as "InSAR-dominated" and move on.
7. **Model structure is uniform across all stations** — parameters vary, structure does not. No per-station selection by inspection.
8. **Incremental cancellation is a physical domain mismatch — not a tuning problem.** The first-difference operator erases preconsolidation stress memory. Do not attempt to fix this with regularization, bounds, or lag optimization. The cumulative domain (Script 12) is the correct formulation for monotonic consolidation. See `discussions/POST_MORTEM_INCREMENTAL_CANCELLATION.md`.
