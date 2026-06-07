# Methodology Plan — Per-Layer Compaction Prediction from InSAR + GWL

**Date:** 2026-05-28
**Status:** Locked methodology, ready for downstream implementation planning
**Working directory for data and code:** `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2`

---

## 1. Research objective

Predict per-layer subsurface compaction at every location across the Choushui River Alluvial Fan — especially the 8,577 grid points without Multi-Layer Compaction-Monitoring Wells (MLCW) — and quantify each aquifer/aquitard layer's contribution to total surface subsidence.

The deliverable is, for any location g in the study area:

- A time series D̂_k(t, g) of cumulative compaction per layer k (F1, T1, F2, T2, F3, T3, F4)
- A cumulative attribution number per layer (% of 2015–2025 total subsidence)
- An annual rate attribution per layer per year

The methodology must remain operationally functional after the post-2021 MLCW shutdown reduces the active network from 39 to 19 stations.

---

## 2. Rejected earlier framings

Two earlier formulations were considered and rejected during methodology design. They are recorded here so future work does not relitigate them.

### Rejected framing 1 — "Fit MLCW to InSAR, then invert InSAR to predict MLCW"

The naive thought: find coefficients that make the sum of per-layer compaction at MLCW match InSAR, then use those coefficients to invert InSAR at grid points.

This is backwards. MLCW is the per-layer ground truth — the most information-rich measurement in the project. InSAR is a depth-integrated observation with one degree of freedom per epoch. Fitting ground truth to an integral discards information and reproduces Smith et al. (2021)'s setup, which was the right inverse problem for *their* dataset (no MLCW) but the wrong fit for ours.

### Rejected framing 2 — "InSAR drives long-term trend; GWL drives seasonal fluctuations"

The proposal: decompose total deformation into a long-term trend and a seasonal component. Fit the trend with a per-layer scalar times InSAR-trend; fit the seasonal component with a GWL-driven term.

Rejected on three grounds:

1. **Trend/seasonal is a filter choice, not a physical principle.** The cutoff between "trend" and "seasonal" depends on the filter (STL, harmonic, low-pass) — Terzaghi physics does not know about this cutoff. The two-regime physics (elastic / inelastic) does not map cleanly onto frequency bands: inelastic pulses during droughts are episodic, not low-frequency; elastic accumulation under asymmetric pumping bleeds into the trend channel.
2. **Double-counting risk.** Surface InSAR is the vertical integral of all depths. If the InSAR-trend channel already contains the deep inelastic signal, and the GWL channel also drives the inelastic regime, the same physical compaction enters the prediction twice.
3. **It is still static reweighting at heart.** A per-layer scalar times a filtered surface signal is the family CLAUDE.md flags as exhausted at 1–3%. The hard rule requires targeting a new failure mode (autoregressive memory, phase lag, state-space dynamics) — a band-split patch does not satisfy this.

---

## 3. The per-layer prediction equation

For each MLCW station, for each hydrogeological layer k $\in$ {F1, T1, F2, T2, F3, T3, F4}:

$$D_k(t) = S_{ke,k} \cdot \Delta H_k(t-\tau_k) \cdot I_{elastic}(t) + S_{kv,k} \cdot \Delta H_k(t-\tau_k) \cdot I_{inelastic}(t) + \beta_k \cdot x(t)$$

### Plain-language definition of every symbol

| Symbol | Meaning | Unit | Sign |
|---|---|---|---|
| $D_{k}$(t) | Cumulative compaction of layer k at time t | mm | Negative = compaction (downward) |
| $\Delta H$_k(t-$\tau_k) | Change in piezometric head in the aquifer assigned to layer k, evaluated at time (t-$\tau_k) | m | Positive = head rose; negative = head fell |
| $\tau_k | Per-layer time lag — how long after head change before the layer responds | days | Non-negative; deeper layers have larger $\tau_k |
| I_elastic(t) | 1 if H(t) > $h_{c}$ (water level still above preconsolidation head — reversible regime); 0 otherwise | — | — |
| I_inelastic(t) | 1 if H(t) $\le$ $h_{c}$ (water level has dropped past preconsolidation — irreversible regime); 0 otherwise | — | — |
| $h_{c}$ | Preconsolidation head: lowest head the aquifer has experienced historically. Estimated as the 10th percentile of the historical head record | m above MSL | — |
| $S_{ke}$,k | Elastic skeletal storage coefficient for layer k — compaction per unit head fall when the layer is in elastic regime | mm/m | Small |
| $S_{kv}$,k | Inelastic skeletal storage coefficient for layer k — compaction per unit head fall when the layer is in inelastic regime | mm/m | Typically 5–20$\times$ larger than $S_{ke}$,k |
| x(t) | InSAR cumulative surface displacement at the station | mm | Negative = subsidence |
| $\beta_k | Residual coupling coefficient for layer k — captures compaction from depths below 300 m and distant pressure gradients the local GWL well cannot see | dimensionless | Sign depends on physical context |

### Physical basis

The equation rests on Terzaghi effective stress + Helm (1975) two-regime compaction:

- When piezometric head H falls, pore pressure drops, effective stress on the sediment skeleton increases, and the layer compacts.
- The proportionality constant is $S_{ke}$ during elastic (reversible) loading — when the head stays above the historical minimum $h_{c}$ — and $S_{kv}$ during inelastic (irreversible) loading — when the head drops past $h_{c}$. Clay's inelastic compressibility is much larger than its elastic compressibility, which is why $S_{kv}$ >> $S_{ke}$.
- The time lag $\tau_k arises because clay's low permeability slows pressure equilibration. Deeper or thicker clay units lag the head signal by months.

### Why the InSAR co-driver term $\beta_k $\cdot$ x(t)

Local GWL records measure heads only at specific screen depths in the well's catchment. They miss:
- Compaction from below 300 m (deeper than the MLCW range)
- Pressure gradients driven by pumping wells distant from the local GWL station
- Other physical processes that affect the MLCW layer but are not encoded in the assigned screen's head record

InSAR, by contrast, integrates the full depth column. The $\beta_k $\cdot$ x(t) term lets each layer borrow a small amount of explanatory power from the surface signal to account for these unmodeled effects. It is a residual co-driver, not the primary driver.

---

## 4. Locked methodology decisions

| Decision | Choice | Rationale |
|---|---|---|
| Primary physical driver | GWL piezometric head | Terzaghi effective stress + Helm (1975) two-regime compaction; well-established subsidence physics |
| InSAR role | Residual co-driver via $\beta_k $\cdot$ x | Captures sub-300 m compaction and distant gradients GWL cannot see; not the primary driver to avoid double-counting |
| Trend handling | Raw (un-detrended) data | Model output must include drift for direct cumulative attribution; matches 2S-TOOL coefficient convention |
| Regime switching | Two-regime at $h_{c}$ (P10 of historical head record) | Standard practice (Riley 1969, Poland 1984); $h_{c}$ is the lowest historically experienced head, defining the elastic/inelastic boundary |
| Phase lag | Per-layer $\tau_k, grid-searched in fitting | Deeper clay layers respond more slowly than shallow sand; single-$\tau$ would smear physically distinct response times |
| Per-station vs. pooled fitting | Per-station per-layer fitting | $S_{ke}$ and $S_{kv}$ genuinely vary with local lithology and depositional history; pooling washes out the signal we want to study |
| Layer geometry at grid points | BME regional material model (`data/mlcw/mlcw_hydrofacies_5m.csv`) | Every grid point inherits aquifer/aquitard layers with depth ranges; consistent across study area |
| GWL screen assignment at grid points | Material-aware logic (generalized v3 algorithm) | Same algorithm as the MLCW assignment in `gwl_to_mlcw_layer_assignment_v3.csv`; screen-depth matching + 10 km search |
| Parameter spatial extension | Spatial interpolation (kriging or IDW), per-layer | F1 to F1, F2 to F2, etc.; no material composition adjustment in initial implementation |
| Uncertainty quantification at grid | Deferred | Point estimates first; uncertainty propagation in a second pass if required |
| Internal model name | Not "IHM-F"; refer to it functionally | "IHM-F" does not appear in the literature and will not be used in publication |

---

## 5. Pipeline stages

### Stage A — Per-station calibration at 37 MLCW stations

**Inputs:**
- MLCW per-layer compaction: `data/mlcw/group_byLayer_reconstr/{STATION}_reconst_grouped.csv` (37 stations $\times$ 4–6 layers, 5-day cadence, 2003–2025)
- GWL piezometric head: `data/gwl/mlcw_gwl_timeseries/{MLCW_STATION}_{GWL_STATION}_{WELLCODE}.feather` (189 files, per station-layer)
- InSAR surface displacement at MLCW stations: `data/insar/timeseries/mlcw_interp_insar_IDW_extend.feather`
- GWL-to-MLCW layer assignment: `data/gwl/gwl_to_mlcw_layer_assignment_v3.csv`
- 2S-TOOL reference $S_{ke}$, $S_{kv}$ (warm-start values): `data/gwl/2stool_outputs/{BASENAME}/{BASENAME}_summary.json`

**Process:**
1. For each station, load the layer-grouped MLCW, the per-layer GWL, and the InSAR
2. Compute $h_{c}$ per layer = P10 of historical head record
3. Compute I_elastic, I_inelastic indicators per epoch
4. Grid-search per-layer $\tau_k over a candidate range (e.g., 0–180 days)
5. For each candidate $\tau_k, fit $S_{ke}$, $S_{kv}$, $\beta$ by OLS on raw (un-detrended) data
6. Select the $\tau_k that minimizes walk-forward hold-out RMSE on the 2022 fold (per CLAUDE.md, fold 1 is the most operationally critical because it simulates deployment under MLCW unavailability)

**Outputs:**
- Per-station-per-layer parameter table: `results/track_b/station_parameters.csv` with columns station, layer, $S_{ke}$, $S_{kv}$, tau, beta, $h_{c}$, RMSE_fold1, RMSE_fold2, RMSE_fold3, RMSE_fold4, f_inel_fold1, ..., f_inel_fold4
- Per-station-per-layer predicted vs. measured: `results/track_b/station_predictions/{STATION}_{LAYER}_predicted.csv`

### Stage B — Layer geometry at grid points

**Inputs:**
- BME regional material model: `data/mlcw/mlcw_hydrofacies_5m.csv` (2,340 rows: 39 stations $\times$ 60 depth levels)
- Source BME grid (for grid-point extraction): the same 112_BME_CRAF.csv source used to populate `mlcw_hydrofacies_5m.csv`
- Grid coordinates: `data/insar/timeseries/gridpnt_500m_interp_insar_IDW_extend.feather` (8,577 rows with coordinates)

**Process:**
1. For each of the 8,577 grid points, look up the nearest BME grid cell to get its 5 m material profile (0–295 m)
2. Apply the same layer classification rules used at MLCW stations (the rules that turn 5 m material codes into F1/T1/F2/T2/F3/T3/F4 layer labels) to produce a layer geometry per grid point
3. Output: for each grid point, a list of (layer code, depth_min, depth_max) tuples

**Outputs:**
- Per-grid-point layer geometry: `data/grid/grid_layer_geometry.csv` with columns grid_id, x_twd97, y_twd97, layer, depth_min, depth_max
- Diagnostic map of layer presence (e.g., percentage of grid points where F2 exists): `results/track_b/grid_layer_coverage.png`

### Stage C — GWL screen assignment at grid points

**Inputs:**
- Per-grid-point layer geometry: `data/grid/grid_layer_geometry.csv` (output of Stage B)
- GWL well registry: `data/gwl/well_info/gwl_allwells_flat.csv` (300 wells with screen depths, coordinates, elevations)
- GWL daily timeseries: `data/gwl/well_timeseries/{STATION}_gwl_timeseries.feather`

**Process:**
1. For each (grid_id, layer) pair, search GWL wells within 10 km of the grid point
2. Score each candidate well by screen-midpoint proximity to the layer's depth range
3. Pick the best-scoring well; record assignment method (DIRECT_MATCH or NEAREST_FALLBACK) and distance
4. Extract the well's daily head timeseries; downsample to MLCW or InSAR cadence as needed

**Outputs:**
- Per-grid-point GWL assignment: `data/grid/grid_gwl_assignment.csv` with columns grid_id, layer, assigned_wellcode, screen_top_m, screen_bot_m, screen_mid_m, assignment_method, dist_to_well_m
- Per-grid-point per-layer GWL timeseries: aggregated structure (decide format during implementation — likely one feather per grid point or one Zarr store for all grid points)

### Stage D — Parameter spatial extension

**Inputs:**
- Per-station-per-layer parameter table from Stage A: `results/track_b/station_parameters.csv`
- Per-grid-point layer geometry from Stage B: `data/grid/grid_layer_geometry.csv`

**Process:**
1. For each layer k in {F1, T1, F2, T2, F3, T3, F4}:
   a. Extract the 37 (or fewer, if a station lacks that layer) (x, y, $S_{ke}$, $S_{kv}$, $\tau_k, $\beta$, $h_{c}$) records for layer k
   b. Fit a variogram per parameter
   c. Krige (or IDW) each parameter to all grid points that have layer k
2. No material composition adjustment in initial implementation — pure spatial interpolation per layer
3. Output one parameter value per (grid_id, layer, parameter_name)

**Outputs:**
- Per-grid-point parameter table: `data/grid/grid_parameters.csv` with columns grid_id, layer, $S_{ke}$, $S_{kv}$, tau, beta, $h_{c}$
- Variograms used for kriging (diagnostic): `results/track_b/variograms_{LAYER}_{PARAM}.png`

### Stage E — Grid-point prediction

**Inputs:**
- Per-grid-point parameter table from Stage D: `data/grid/grid_parameters.csv`
- Per-grid-point per-layer GWL timeseries from Stage C
- InSAR at grid points: `data/insar/timeseries/gridpnt_500m_interp_insar_IDW_extend.feather`

**Process:**
For each (grid_id, layer) pair and each time t in the InSAR epoch grid:
1. Compute $\Delta H$_k(t - $\tau_k) from the assigned GWL timeseries
2. Compute I_elastic, I_inelastic from H(t) vs. $h_{c}$
3. Apply the prediction equation: D̂_k(t, g) = $S_{ke}$,k $\cdot$ $\Delta H$_k $\cdot$ I_elastic + $S_{kv}$,k $\cdot$ $\Delta H$_k $\cdot$ I_inelastic + $\beta_k $\cdot$ x(t, g)

**Outputs:**
- Per-grid-point per-layer compaction predictions: `results/track_b/grid_predictions/D_{LAYER}.feather` (one file per layer; columns are grid_id $\times$ InSAR epochs)
- Cumulative compaction per layer per grid point at t_end (2025-12-11): `results/track_b/grid_cumulative_{LAYER}.csv`

### Stage F — Attribution computation

**Inputs:**
- Per-grid-point per-layer compaction predictions from Stage E

**Process:**
- Cumulative attribution per (grid_id, layer):
  - Attr_k^cum(g) = (D̂_k(t_end, g) - D̂_k(t_start, g)) / $\Sigma$_j (D̂_j(t_end, g) - D̂_j(t_start, g)) $\times$ 100%
- Annual rate attribution per (grid_id, layer, year):
  - For each year, fit a linear slope to D̂_k(t, g) restricted to that year
  - Attr_k^rate(g, year) = slope_k / $\Sigma$_j slope_j $\times$ 100%

**Outputs:**
- Cumulative attribution table: `results/track_b/attribution_cumulative.csv` with columns grid_id, x, y, F1_pct, T1_pct, F2_pct, T2_pct, F3_pct, T3_pct, F4_pct, dominant_layer
- Annual rate attribution table: `results/track_b/attribution_annual.csv` with columns grid_id, year, layer, pct, slope_mm_per_year
- Pie-chart-per-location figures and dominant-layer map: `results/track_b/figures/`

### Stage G — Validation

**Three levels of validation, each producing CSVs that quantify model performance.**

**Level 1 — At 37 MLCW stations (ground truth available):**
- Walk-forward 4-fold cross-validation (2022, 2023, 2024, 2025 hold-outs); train on years up to N, predict year N+1, compare to measured
- Compute per-fold RMSE per station per layer
- Compute f_inel = count(I_inelastic) / N_train per fold; flag folds with f_inel < 0.10 as "$S_{kv}$ poorly identified"
- Output: `results/track_b/validation_level1.csv` with columns station, layer, fold, rmse_mm, r2, f_inel, n_train, n_test

**Level 2 — Leave-one-station-out cross-validation (simulates grid-point deployment):**
- Hold out each MLCW station in turn
- Re-fit parameters at the remaining 36 stations
- Spatially interpolate {$S_{ke}$, $S_{kv}$, $\tau_k, $\beta$, $h_{c}$} to the held-out station's location
- Predict per-layer compaction at the held-out station using interpolated parameters + actual GWL
- Compare to measured MLCW
- Output: `results/track_b/validation_level2_loocv.csv` with columns held_out_station, layer, rmse_mm, attr_predicted_cum, attr_measured_cum, attr_error_cum

**Level 3 — At 8,577 grid points (no ground truth):**
- Integral consistency: $\Sigma$_k D̂_k(t, g) compared to $\alpha$(g) $\cdot$ d_InSAR(t, g)
- Spatial smoothness check on attribution maps (no checkerboard patterns)
- Output: `results/track_b/validation_level3.csv` with columns grid_id, sum_D_predicted, alpha_times_insar, residual, residual_pct

---

## 6. Critical files to be created or modified

The downstream implementation plan should produce:

- New scripts under `scripts/10_track_b/`:
  - `track_b_station_calibration.py` (Stage A)
  - `track_b_grid_layer_geometry.py` (Stage B)
  - `track_b_grid_gwl_assignment.py` (Stage C)
  - `track_b_parameter_kriging.py` (Stage D)
  - `track_b_grid_prediction.py` (Stage E)
  - `track_b_attribution.py` (Stage F)
  - `track_b_validation_l1.py` / `track_b_validation_l2.py` / `track_b_validation_l3.py` (Stage G)

- Possibly reusable modules from existing IHM-F scaffolding (`scripts/10_ihmf/ihmf_model.py`, `ihmf_io.py`, `ihmf_plots.py`) — to be evaluated when writing the implementation plan; the calibration logic is largely transferable, but the InSAR sign convention and data form (raw vs. detrended) must be updated.

- New output directories under `results/track_b/`:
  - `station_parameters.csv`, `station_predictions/`, `grid_predictions/`, `figures/`, `validation_level1.csv`, `validation_level2_loocv.csv`, `validation_level3.csv`, `attribution_cumulative.csv`, `attribution_annual.csv`

---

## 7. Verification approach

End-to-end verification:

1. **Stage A verification:** Run on TUKU first (diagnostic station). Compare fitted $S_{ke}$, $S_{kv}$ magnitudes to 2S-TOOL reference values from `data/gwl/2stool_outputs/2STOOL_TUKU_*/`. Plot predicted vs. measured per layer per fold; visually inspect for systematic bias.
2. **Stage B verification:** Spot-check 10 grid points: confirm layer geometry matches the nearest MLCW station's layer geometry.
3. **Stage C verification:** For grid points within 1 km of an MLCW station, confirm GWL assignment matches the MLCW station's assignment in `gwl_to_mlcw_layer_assignment_v3.csv`.
4. **Stage D verification:** Plot kriged parameter maps per layer; look for outliers and physically implausible patterns (e.g., $S_{kv}$ values orders of magnitude outside the training range).
5. **Stage E verification:** At MLCW station locations (treated as grid points), the interpolated-parameter prediction should approximately match the directly-fit prediction.
6. **Stage F verification:** Cumulative attribution at MLCW stations should match measured attribution from real MLCW data within Level 1 RMSE bounds.
7. **Stage G verification:** Confirm walk-forward RMSE for fold 1 (2022 hold-out) is reported separately and is the most operationally critical metric.

Verification scripts should be self-contained (not require the full pipeline to be re-run) and produce a single-page PDF or PNG summary per stage.

---

## 8. Open items (for future iteration)

These were considered during methodology design but deferred to future iteration:

1. **Uncertainty quantification at grid points.** Point estimates first; kriging variance, LOO-CV-derived uncertainty maps, or bootstrap ensembles can be added in a second pass.
2. **Material composition adjustment in spatial interpolation.** Pure spatial interpolation per layer is the initial choice. If LOO-CV shows large prediction errors at locations where material composition deviates from nearby MLCW stations, consider cokriging with BME material composition (% clay, % sand) as a secondary variable.
3. **Diagnostic split of $\beta_k into $\beta_low + $\beta_high.** The user's intuition that InSAR contributes meaningfully to long-term trend can be tested as a diagnostic: fit $\beta_low $\cdot$ x_low(t) + $\beta_high $\cdot$ x_high(t) per station-layer; save coefficients to CSV; inspect whether one frequency band dominates.
4. **Alternative parameterizations.** If raw-data fitting proves unstable in walk-forward folds (especially the 2022 reconstructed-MLCW fold), revisit the Option C two-stage fit (detrended for dynamics, raw for drift) discussed during methodology design.

---

## 9. References

- Helm, D. C. (1975). One-dimensional simulation of aquifer system compaction near Pixley, California: 1. Constant parameters. *Water Resources Research*, 11(3), 465–478.
- Riley, F. S. (1969). Analysis of borehole extensometer data from central California. *IAHS Publication*, 89, 423–431.
- Poland, J. F. (Ed.). (1984). *Guidebook to studies of land subsidence due to ground-water withdrawal*. UNESCO.
- Smith, R. G., et al. (2021). Apportioning deformation among depth intervals in an aquifer system using InSAR and head data. *Journal of Geophysical Research: Solid Earth*. Path: `D:\001_LITERATURE_v2\ZOTERO_storage\storage\GJEFAZBW\`
- Hung, W. C., et al. (2021). Measuring and Interpreting Multilayer Aquifer-System Compactions for a Sustainable Groundwater-System Development. Path: `D:\001_LITERATURE_v2\ZOTERO_storage\storage\UKHSQCFQ\`
- Terzaghi, K. (1925). *Erdbaumechanik auf bodenphysikalischer Grundlage*.

The Hung et al. (2021) data is the same Choushui River Alluvial Fan MLCW network used in this project; their per-station methodology established the elastic/inelastic regime identification used here. Smith et al. (2021) is the methodological reference for InSAR-driven inversion in the absence of MLCW — their approach is rejected here because MLCW provides direct per-layer calibration.
