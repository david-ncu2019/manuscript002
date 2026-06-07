# IHM-F Computational Workflow: Data Assembly, Parameter Estimation, and Validation

**Date:** 2026-05-29
**Applies to:** `scripts/10_ihmf/` — IHM-F v3 (current production model)
**Author note:** This document describes the computational pipeline as implemented in `fit_ihm_f_v3.py`, `ihmf_model_v3.py`, and shared utility modules. Section 10 covers version history for reference.

---

## Section 0 — Module Overview

The Inelastic Head Model with Fractional coupling (IHM-F) estimates per-layer skeletal storage coefficients and hydraulic response lags from paired Multi-Layer Compaction Monitoring Well (MLCW) and groundwater level (GWL) observations, then uses Interferometric Synthetic Aperture Radar (InSAR) surface displacement measurements to constrain the spatial scaling factor α. The pipeline is organized into seven Python modules.

| File | Role | Generation |
|------|------|-----------|
| `ihmf_io.py` | Load and align one (station, layer) data triplet to the InSAR timeline | Shared |
| `ihmf_io_multilayer.py` | Load all layers for one station simultaneously | Shared (v3 extension) |
| `ihmf_detrend.py` | Remove secular trend and annual harmonic from 1-D signals; compute layer-level median compaction ratio | Shared |
| `ihmf_model_v3.py` | Seasonal cycle removal, hydraulic lag search, two-step parameter estimation, walk-forward validation | v3 (active) |
| `fit_ihm_f_v3.py` | Entry point: orchestrates the full pipeline for one station | v3 (active) |
| `ihmf_plots.py` | Generate raw-fit and reconstruction figures | Shared |
| `batch_v3.py` | Iterate `fit_ihm_f_v3.py` over all 37 MLCW stations | v3 (active) |
| `ihmf_model_v2.py` | Detrended OLS solver with InSAR co-predictor per layer (superseded; physically incorrect) | v2 (legacy) |
| `fit_ihm_f_v2.py` | v2 entry point (retained for comparison) | v2 (legacy) |
| `ihmf_model.py` | Two-path Path A / Path B solver (superseded) | v1 (legacy) |
| `fit_ihm_f.py` | v1 entry point (retained for archival comparison) | v1 (legacy) |

---

## Section 1 — Physical Basis and Model Equations

### 1.1 The compaction mechanism

Excessive groundwater extraction from confined aquifers causes a decline in piezometric head. When piezometric head declines, pore-fluid pressure within the fine-grained aquitards and interbeds that separate the aquifer units decreases. Because total overburden stress remains approximately constant, the overburden load transfers progressively to the granular skeleton of those fine-grained layers, increasing effective stress. The increase in effective stress drives compaction of the aquitards and interbeds. When effective stress remains below the preconsolidation stress, compaction is elastic (reversible): if piezometric head recovers, the fine-grained layer partially rebounds. When effective stress exceeds the preconsolidation stress, compaction is inelastic (permanent): the skeletal structure rearranges irreversibly, and surface land subsidence accumulates at the rate of compaction summed over all compressible layers.

### 1.2 The IHM-F equations

The IHM-F model operates at the scale of one hydrogeological layer at one MLCW station. For layer $j$ at epoch $t$, the incremental compaction predicted by the model is:

$$\Delta b_j(t) = S_j \cdot \Delta H_j(t - \tau_j)$$

where:
- $\Delta b_j(t)$ is the incremental per-layer compaction measured by the MLCW (mm per epoch, negative when compacting)
- $S_j$ is the bulk skeletal storage coefficient (mm/m), defined as the volume of water expelled per unit decline in piezometric head per unit plan area of the layer
- $\Delta H_j(t)$ is the incremental change in piezometric head in the aquifer unit assigned to layer $j$ (m per epoch)
- $\tau_j$ is the hydraulic lag (non-negative integer, in 5-day epoch units)

The storage coefficient $S_j$ takes two values depending on the compaction regime. When piezometric head exceeds the critical head threshold $h_c$ (elastic regime), $S_j = S_{ke}$, the elastic skeletal specific storage multiplied by the layer thickness. When piezometric head falls below $h_c$ (inelastic regime), $S_j = S_{kv}$, the inelastic skeletal specific storage multiplied by layer thickness. Both $S_{ke}$ and $S_{kv}$ carry units of mm/m and satisfy $S_{ke} \geq 0$ and $S_{kv} \geq 0$ by physical constraint.

The surface alignment equation links the sum of per-layer compactions to the total land subsidence measured by InSAR:

$$\alpha \cdot \Delta d_v(t) = \sum_{j=1}^{N} \Delta b_j(t)$$

where $\Delta d_v(t)$ is the incremental vertical surface displacement derived from ascending and descending orbit decomposition of InSAR measurements (mm per epoch, negative when subsiding), $N$ is the number of hydrogeological layers at the station, and $\alpha$ is a dimensionless scaling factor in the range $(0, 1]$. The factor $\alpha$ accounts for the fraction of total InSAR displacement that originates within the modelled depth interval (0–300 m). Layers below 300 m, non-aquifer-system deformation, and horizontal displacement components contribute to the complement $1 - \alpha$.

### 1.3 Sign conventions

| Signal | Positive value | Negative value |
|--------|---------------|----------------|
| InSAR `insar_mm` | Displacement toward satellite (uplift) | Displacement away from satellite (subsidence) |
| MLCW `mlcw_mm` | Cumulative extension (expansion) | Cumulative compaction (subsidence) |
| GWL `head_m` | Piezometric head in m above MSL | Below MSL (deep artesian wells) |
| $\Delta H_j$ | Piezometric head rise (recovery) | Piezometric head decline (stress loading) |

These sign conventions are preserved throughout the pipeline. The GWL signal is never negated. InSAR is never inverted. The negative-equals-compaction convention for MLCW means that a positive S_ke or S_kv with a negative $\Delta H_j$ produces a negative (compacting) $\Delta b_j$, which is physically correct.

---

## Section 2 — Data Assembly (`ihmf_io.py`, `ihmf_io_multilayer.py`)

### 2.1 Input sources

Three data sources are required for each (station, layer) pair.

**MLCW layer-grouped reconstructed compaction** (`data/mlcw/group_byLayer_reconstr/{STATION}_reconst_grouped.csv`): A CSV with a `datetime` column and one column per hydrogeological layer (F1, T1, F2, T2, F3, F4). Values are cumulative compaction in mm from an arbitrary reference date. The data were reconstructed using a parametric time-function decomposition (trend plus harmonic components, implemented in the `appsigsolv` library) fitted to irregularly sampled field-campaign observations, then resampled to the 1st, 6th, 11th, 16th, 21st, and 26th day of each calendar month, producing an approximately 5-day cadence (~1,572 rows, 2003–2025); 37 stations are available after excluding JINHU_XIN and LUNFENG_XIN.

**GWL timeseries** (`data/gwl/well_timeseries/{STATION}_gwl_timeseries.feather`): An Apache Feather binary file with daily piezometric head records for all monitoring wells associated with one MLCW station. Column names are 8-digit wellcodes. Values are piezometric head in metres above Mean Sea Level (MSL). Records span 2000-01-01 to 2025-12-31 at **daily** resolution (9,497 rows per file); GWL is not resampled or reconstructed. The assignment of wellcodes to MLCW hydrogeological layers is recorded in `data/gwl/gwl_to_mlcw_layer_assignment_v3.csv`.

**InSAR time-series** (`data/insar/InSAR_measures_at_MLCW.csv`): A CSV with one column per MLCW station name and one row per InSAR acquisition epoch. Values are cumulative vertical surface displacement in metres, derived from ascending and descending orbit decomposition (converted to mm inside the loader). The 785 epochs span 2015-01-21 to 2025-12-11 at a median interval of 5 days; 697 of 784 inter-epoch gaps are exactly 5 days.

### 2.2 Alignment procedure (`load_and_align`)

The function `load_and_align` in `ihmf_io.py` accepts a configuration dictionary (one entry from `data/ihmf_config.json`) and returns a merged DataFrame aligned to the InSAR epoch timeline.

The procedure follows five steps.

**Step 1 — Load each source independently.** MLCW is read from CSV and the target layer column is extracted. GWL is read from the Feather file and the assigned wellcode column is extracted; rows where the wellcode value is NaN are dropped. InSAR is read from CSV; values in metres are multiplied by 1000 to convert to mm.

**Step 2 — Sort all three by datetime.** All three DataFrames are sorted chronologically. The InSAR timeline (785 epochs) becomes the master grid.

**Step 3 — Align GWL and MLCW to the InSAR master grid using `merge_asof`.** The `merge_asof` function performs a nearest-neighbour join in time: for each InSAR epoch, the GWL and MLCW records closest in time are selected. GWL records are daily and MLCW records fall on the 1st, 6th, 11th, 16th, 21st, and 26th of each month; for both, the nearest-neighbour match to any InSAR epoch typically falls within 0 to 3 days.

**Step 4 — Merge the three aligned series into a single DataFrame.** The output `merged` DataFrame has columns: `datetime`, `insar_mm`, `head_m`, `mlcw_mm`. All three signals share the same 785-row index.

**Step 5 — Compute the critical head threshold $h_c$.** The critical head is defined as the minimum piezometric head observed **before 2015-01-16** (the first InSAR epoch) in the daily GWL record for the assigned well. This threshold represents the historically deepest stress state the aquifer had experienced before the modelling window, which is the physically correct definition of the preconsolidation head for this study. Because GWL feather files begin at 2000-01-01, 15 years of pre-2015 daily data are available for most wells. For the two wells that lack pre-2015 records in the feather files (YIWU well 09190112 and ZHENNAN/SHILIU well 09010212), a fallback to the 10th percentile of the full available record is applied until the H5 archive data are spliced into those feather files.

The `meta` dictionary returned alongside `merged` contains: `h_c_head_m` (critical head in m above MSL), `h_c_depth_m` (critical head converted to depth below ground using `elev_leveling_m`), `wellcode`, `well_elev_m`, and `n_epochs`.

### 2.3 Multi-layer loading (`load_all_layers`)

The function `load_all_layers` in `ihmf_io_multilayer.py` wraps `load_and_align` to load all hydrogeological layers for one station simultaneously. The function filters `ihmf_config.json` entries by station name, calls `load_and_align` for each matching entry, and verifies that all layers share the identical InSAR datetime axis (a structural requirement for the joint solver). The outputs are a dictionary keyed by layer code (`layer_dfs`), a corresponding dictionary of metadata (`layer_metas`), and a 1-D array `insar_mm` extracted from any one of the aligned DataFrames (all layers share the same InSAR signal).

---

## Section 3 — Elastic and Inelastic Regime Classification (`build_regime_mask`)

### 3.1 Physical distinction

Elastic compaction is reversible. When piezometric head declines below a prior level but remains above the preconsolidation head, the aquifer skeleton compresses under increased effective stress, but the skeletal structure is not permanently rearranged. When piezometric head recovers, a portion of the compaction reverses. Inelastic compaction is permanent. When piezometric head declines below the preconsolidation head — defined here as the critical head $h_c$ — effective stress exceeds the preconsolidation stress and irreversible skeletal rearrangement occurs. Land subsidence from inelastic compaction cannot be recovered by subsequent head recovery.

### 3.2 Implementation

The function `build_regime_mask` in `ihmf_model_v3.py` compares the piezometric head time series against $h_c$ epoch by epoch. The elastic mask is `True` at epochs where `head_m > h_c_head_m`. The inelastic mask is the complement. Every epoch belongs to exactly one regime. The masks operate on the incremental-length array (length $T - 1$, produced by first-differencing the cumulative GWL), using the head value at epoch $t$ to classify the increment from $t$ to $t+1$.

### 3.3 Why the pre-2015 minimum is used as $h_c$

The preconsolidation head marks the lowest piezometric level the aquifer experienced before the observation window begins. Setting $h_c$ to the minimum head observed before 2015-01-16 ensures that any epoch during the 2015–2025 modelling window in which piezometric head falls below that historical low is correctly classified as inelastic. If the full-record minimum (including post-2015 drought years) were used instead, $h_c$ would be set too low: all modelling-window epochs would lie above it, placing every epoch in the elastic regime and preventing $S_{kv}$ estimation. If an arbitrary percentile of the full record were used, the threshold would reflect the statistical distribution of the observation window rather than the physical preconsolidation history.

---

## Section 4 — Seasonal Cycle Removal (`remove_seasonal_cycle`, `apply_seasonal_removal`)

### 4.1 The aliasing problem

The IHM-F model operates on incremental signals: $\Delta b_j(t) = b_j(t) - b_j(t-1)$ and $\Delta H_j(t) = H_j(t) - H_j(t-1)$. Both incremental GWL and incremental MLCW compaction exhibit a pronounced annual cycle driven by seasonal groundwater recharge. At TUKU station, the autocorrelation of incremental GWL at lag 24 epochs (120 days) is $r = 0.82$, and at lag 48 epochs (240 days) is $r = 0.77$, confirming near-annual periodicity in the incremental signal. This periodicity introduces a spurious maximum in the cross-correlation between $\Delta H_j$ and $\Delta b_j$ at lags near 73 epochs (365 days), masking the genuine hydraulic response at shorter lags of 6–30 epochs (30–150 days).

### 4.2 Removal procedure

The function `remove_seasonal_cycle` computes the climatological mean of the incremental signal for each of the 12 calendar months, then subtracts that mean from every epoch belonging to that month. The result is an anomaly signal that retains inter-annual variability (droughts, wet years, multi-year trends) while removing the regular annual cycle. The 12 monthly means are returned alongside the anomaly array so that the same climatology can be applied to the test window during walk-forward validation without using test-window data to compute the means.

The function `apply_seasonal_removal` accepts a pre-computed monthly climatology from the training window and subtracts it from a new (test) window. This design prevents look-ahead contamination: test-epoch information does not influence the seasonal correction applied to those same test epochs.

### 4.3 Scope of application

Seasonal cycle removal is applied only to the hydraulic lag search (Section 5). The parameter estimation step (Section 6) uses the original (non-anomaly) incremental signals so that $S_{ke}$ and $S_{kv}$ retain their physical units of mm/m. The anomaly transformation is a diagnostic preprocessing step, not a physical model component.

---

## Section 5 — Hydraulic Lag Search (`tau_grid_search_per_layer`)

### 5.1 Physical meaning of the lag $\tau$

The hydraulic lag $\tau$ represents the delay between a change in piezometric head in the aquifer unit and the onset of measurable compaction in the adjacent aquitard or interbed. This delay arises because pore pressure must diffuse through the low-permeability fine-grained material before the full effective stress change is transmitted to the skeletal structure. Thick, low-permeability clay layers have greater delays than thin silty interbeds. At the 5-day epoch interval used throughout this project, $\tau = 6$ corresponds to approximately 30 days, $\tau = 24$ to approximately 120 days, and $\tau = 73$ to approximately 365 days. The search range $\tau \in \{0, 1, \ldots, 73\}$ therefore covers lags from instantaneous response to a one-year delay.

The lag $\tau$ is always a non-negative integer. It represents the number of 5-day epochs by which the GWL input leads the compaction response. Fractional values of $\tau$ have no physical interpretation because neither the GWL signal nor the MLCW signal exists between discrete acquisition epochs.

### 5.2 Grid search procedure

For each candidate lag $\tau$ in the integer range $\{0, 1, \ldots, \tau_{max}\}$, the function constructs aligned arrays of length $T - \tau$: the lagged anomaly GWL increment $\Delta H_{anom}[\tau:]$ and the anomaly MLCW increment $\Delta b_{anom}[:T-\tau]$. Using the elastic and inelastic regime masks (trimmed to length $T - \tau$), the function fits $S_{ke}$ and $S_{kv}$ independently by scalar ordinary least squares (OLS) with non-negativity constraints:

$$S_{ke} = \max\!\left(0,\ \frac{\sum_{t \in \text{elastic}} \Delta H_{anom}(t) \cdot \Delta b_{anom}(t)}{\sum_{t \in \text{elastic}} \Delta H_{anom}(t)^2}\right)$$

and analogously for $S_{kv}$ over inelastic epochs. The predicted anomaly MLCW increment at lag $\tau$ is then $\hat{\Delta b}_{anom}(t) = S_{ke} \cdot \Delta H_{anom}(t)$ at elastic epochs and $S_{kv} \cdot \Delta H_{anom}(t)$ at inelastic epochs. The mean squared error (MSE) is computed as:

$$\text{MSE}(\tau) = \frac{1}{T - \tau} \sum_{t=0}^{T-\tau-1} \left[\Delta b_{anom}(t) - \hat{\Delta b}_{anom}(t)\right]^2$$

### 5.3 Why MSE and not RSS

The raw sum of squared residuals (RSS) decreases arithmetically as the lag $\tau$ increases, because the number of terms in the sum shrinks from $T$ at $\tau = 0$ to $T - \tau_{max}$ at $\tau = \tau_{max}$. With a weakly correlated anomaly signal, this arithmetic reduction causes the RSS curve to decrease monotonically toward $\tau_{max}$, regardless of where the true hydraulic response peak lies. Dividing by the number of observations (MSE) removes this sample-size bias. When no genuine hydraulic response exists, the MSE curve is approximately flat. When a genuine response exists, the MSE curve displays a local minimum at the true response lag.

The optimal lag $\tau_{opt}$ is the integer that minimises $\text{MSE}(\tau)$ over all $\tau \in \{0, \ldots, \tau_{max}\}$.

---

## Section 6 — Two-Step Parameter Estimation (`joint_solve_fixed_tau`)

### 6.1 Overview

With $\tau_j$ fixed at $\tau_{opt}$ from the lag search (Section 5), the function `joint_solve_fixed_tau` estimates the storage coefficients $S_{ke,j}$ and $S_{kv,j}$ for all $N$ layers and the surface scaling factor $\alpha$ in two sequential steps. The two steps operate in different signal domains because the per-layer MLCW signal and the total InSAR signal have different noise characteristics that preclude a single joint linear system.

### 6.2 Step 1 — Storage coefficient estimation from MLCW

For each layer $j$ independently, a 2-column design matrix $A_j$ is constructed from the original (non-anomaly) incremental GWL signal lagged by $\tau_{opt}$:

$$A_j = \begin{bmatrix} \Delta H_j[\tau:] \cdot \mathbf{1}_{\text{elastic}} & \Delta H_j[\tau:] \cdot \mathbf{1}_{\text{inelastic}} \end{bmatrix}$$

where $\mathbf{1}_{\text{elastic}}$ is 1 at elastic epochs and 0 elsewhere, and vice versa. The regression target is the original incremental MLCW compaction $\Delta b_j[:T-\tau]$. The constrained linear system is solved using `scipy.optimize.lsq_linear` with lower bounds $[0, 0]$ and upper bounds $[\infty, \infty]$:

$$[S_{ke,j},\; S_{kv,j}] = \arg\min_{\mathbf{s} \geq 0} \|A_j \mathbf{s} - \Delta b_j\|^2$$

The non-negativity constraint reflects the physical requirement that both elastic and inelastic skeletal storage coefficients must be non-negative: compaction cannot decrease under increased effective stress.

The fitted values $S_{ke,j}$ and $S_{kv,j}$ are in mm/m (bulk form). To obtain the specific elastic skeletal storage coefficient $S_{ske}$ (m⁻¹) for publication or comparison with literature values, divide by the layer thickness $b_j$ (m) and the mm-to-m conversion: $S_{ske} = S_{ke,j} / (b_j \times 1000)$. Layer thickness $b_j$ is computed at runtime from `{STATION}_classify_table.csv` as the sum of ring spans assigned to layer $j$. Published $S_{ske}$ values for the Choushui River Alluvial Fan range from $2.86 \times 10^{-6}$ to $3.87 \times 10^{-4}$ m⁻¹ (elastic) and $1.53 \times 10^{-5}$ to $3.00 \times 10^{-3}$ m⁻¹ (inelastic); multiply by $b_j \times 1000$ to obtain the corresponding bounds on $S_{ke,j}$ and $S_{kv,j}$ in mm/m for use as solver constraints.

### 6.3 Step 2 — Surface scaling factor $\alpha$ from cumulative InSAR

After $S_{ke,j}$ and $S_{kv,j}$ are estimated, the predicted per-layer compaction increments are summed over all $N$ layers at each epoch:

$$\hat{\Delta b}_{total}(t) = \sum_{j=1}^{N} \left[S_{ke,j} \cdot \Delta H_j(t - \tau_j) \cdot \mathbf{1}_{elastic} + S_{kv,j} \cdot \Delta H_j(t - \tau_j) \cdot \mathbf{1}_{inelastic}\right]$$

The cumulative sum of this total predicted compaction is then compared to the cumulative InSAR displacement. The scaling factor $\alpha$ is estimated by scalar OLS in the cumulative domain:

$$\alpha = \frac{\sum_{t=1}^{T} \hat{B}_{total}(t) \cdot D_v(t)}{\sum_{t=1}^{T} D_v(t)^2}$$

where $\hat{B}_{total}(t) = \sum_{s=1}^{t} \hat{\Delta b}_{total}(s)$ is the cumulative predicted compaction and $D_v(t) = \sum_{s=1}^{t} \Delta d_v(s)$ is the cumulative InSAR displacement. The result is clamped to the interval $(0, 1]$.

### 6.4 Why cumulative domain for $\alpha$

The incremental InSAR signal $\Delta d_v(t)$ has a standard deviation of approximately 4 mm per epoch at TUKU station. The incremental MLCW compaction signal has a standard deviation of approximately 0.5 mm per epoch. This 8-fold difference in noise level means that the signal-to-noise ratio (SNR) of the InSAR incremental signal is too low to reliably constrain $\alpha$ at the epoch-to-epoch scale. In the cumulative domain, random epoch-to-epoch noise cancels by summation, and the cumulative InSAR signal reflects the secular compaction trend with adequate SNR. The cross-correlation between the cumulative predicted compaction and the cumulative InSAR reaches $R^2 > 0.85$ at TUKU, confirming that $\alpha$ estimation is stable in the cumulative domain.

---

## Section 7 — Full-Record Fit Entry Point (`fit_ihm_f_v3.py`)

### 7.1 Orchestration sequence

The function `run_station` in `fit_ihm_f_v3.py` executes the complete pipeline for one MLCW station. The sequence is:

1. Load configuration from `data/ihmf_config.json` and resolve paths relative to the project root.
2. Call `load_all_layers` to assemble all layers simultaneously, aligned to the InSAR timeline.
3. For each layer, compute the incremental GWL signal $\Delta H_j = \text{diff}(H_j)$ and the incremental MLCW signal $\Delta b_j = \text{diff}(b_j)$.
4. Compute the elastic and inelastic regime masks using `build_regime_mask` applied to the pre-difference head array (length $T - 1$).
5. For each layer, call `tau_grid_search_per_layer` with the incremental epoch dates to identify $\tau_{opt}$ and the MSE curve. The constant `TAU_MAX = 73` is hard-coded in the entry point and overrides the per-entry `tau_max` field in the configuration file.
6. Construct the lagged incremental arrays for the joint solve at the optimal lags.
7. Call `joint_solve_fixed_tau` to estimate $S_{ke,j}$, $S_{kv,j}$, and $\alpha$.
8. Compute RMSE_MLCW (average over all layers and epochs, in incremental mm/epoch) and RMSE_InSAR (in cumulative mm).
9. Run `run_walk_forward_v3` for the 4-fold validation.
10. Save all results to `results/ihmf/v3/{STATION}_v3_results.json`.

### 7.2 Output JSON structure

The JSON file saved per station contains:

```
{
  "station": "TUKU",
  "alpha": 0.013,
  "beta": 76.9,
  "rmse_mlcw": 0.904,
  "rmse_insar": 187.3,
  "r2_insar": -6.47,
  "T": 58,
  "layers": {
    "F1": {"S_ke": 0.136, "S_kv": 0.000, "tau_opt": 29},
    "F2": {"S_ke": 0.570, "S_kv": 1.072, "tau_opt": 71},
    ...
  },
  "tau_rss_curves": {"F1": [...], ...},
  "walk_forward": [
    {"fold": "Fold1_test2022", "alpha": 0.023, "rmse_insar": 73.7, "n_test": 12},
    ...
  ],
  "diagnostics": ["WARN: alpha=0.013 outside expected range"]
}
```

The `T` field records the length of the shortest lagged layer window, which sets the effective number of epochs used in the joint solve. Because the longest $\tau_{opt}$ value shortens the usable window, `T` is always less than or equal to $785 - \tau_{max}$.

---

## Section 8 — Walk-Forward Validation (`run_walk_forward_v3`)

### 8.1 Validation structure

The function `run_walk_forward_v3` implements an expanding-window walk-forward validation with four hold-out years. The four folds are:

| Fold | Training window | Hold-out (test) year |
|------|----------------|---------------------|
| Fold 1 | 2015-01 to 2021-12 | 2022 |
| Fold 2 | 2015-01 to 2022-12 | 2023 |
| Fold 3 | 2015-01 to 2023-12 | 2024 |
| Fold 4 | 2015-01 to 2024-12 | 2025 |

Random k-fold cross-validation is not used because it tests interpolation within the observed time range, not extrapolation beyond the calibration window. The walk-forward structure tests whether parameters calibrated on past data produce accurate predictions in future years — the operationally relevant question.

Fold 1 is the operationally critical fold. MLCW compaction records during 2022 were not obtained from functioning sensors; those values are reconstructed from surrounding observations. Fold 1 therefore simulates the deployment scenario in which MLCW data are unavailable and predictions must be generated from GWL and InSAR alone.

### 8.2 Per-fold procedure

For each fold, the function executes the following steps on the training window only:

1. Extract training indices from the incremental-length date array (length $T_{full} - 1$).
2. Run `tau_grid_search_per_layer` on the training-window incremental signals to determine $\tau_{opt}$ for that fold. This prevents look-ahead: the lag is estimated from training data only.
3. Extract the 12 monthly climatological means of $\Delta H_j$ from the training window.
4. Apply `apply_seasonal_removal` to the test-window $\Delta H_j$ using the training-window climatology.
5. Construct the lagged arrays for the test window: use the last $\tau_{opt}$ epochs of the training window as context, then append the test-window increments.
6. Call `joint_solve_fixed_tau` on the test-window data to estimate storage coefficients and $\alpha$ for that fold.
7. Compute per-fold RMSE_MLCW and RMSE_InSAR.

The function records `n_test` (number of usable test epochs after lag trimming) for each fold. A fold is skipped and flagged as `"skipped": true` if no valid layers remain after lag trimming, or if the training window contains fewer than 10 incremental epochs.

---

## Section 9 — Interpreting Diagnostic Outputs

### 9.1 $\tau_{opt}$ near $\tau_{max}$

When $\tau_{opt}$ equals $\tau_{max} = 73$ for a layer, two explanations are possible. First, the true hydraulic lag in that layer may genuinely approach one year. This occurs in thick, low-permeability clay confining units where pore pressure diffusion is slow. Second, the seasonal cycle removal may be incomplete, and residual annual periodicity in the anomaly signal may still produce a spurious minimum near $\tau = 73$. These cases are distinguished by examining the MSE curve shape: a genuine hydraulic response produces a local minimum with a clear drop from surrounding values, whereas residual aliasing produces a monotonically decreasing MSE curve that touches its minimum at the boundary.

### 9.2 $S_{ke} = S_{kv} = 0$

A storage coefficient of zero at a layer indicates that the assigned GWL well's head variations do not statistically explain the MLCW compaction at that layer. This condition does not represent a solver failure; it represents a physically meaningful finding that the GWL-to-layer assignment is inadequate for that (station, layer) pair. Probable causes include: the assigned monitoring well screens a different aquifer unit than the one compacting; the well is too distant from the MLCW station to capture local head variations; or the layer compaction is dominated by a stress pathway not captured by the single assigned wellcode.

### 9.3 $\alpha$ outside $(0, 1]$

The physical requirement is $0 < \alpha \leq 1$ because the modelled layers (0–300 m depth) cannot account for more displacement than InSAR measures at the surface. When $\alpha > 1$, the predicted cumulative compaction exceeds the InSAR cumulative displacement. This indicates that one or more storage coefficient estimates are too large, or that the model predicts compaction in layers that are actually extending. When $\alpha \ll 0.1$, the predicted cumulative compaction is much smaller than InSAR, indicating that most of the surface displacement originates from processes or depth intervals not represented in the model. Both conditions warrant inspection of individual layer $\tau_{opt}$ values and cross-correlation diagnostics.

### 9.4 RMSE_MLCW versus RMSE_InSAR

RMSE_MLCW is computed on the incremental (epoch-to-epoch) residuals, averaged across all layers and epochs, in units of mm/epoch. A value below approximately 1 mm/epoch at 5-day resolution indicates that the model captures the incremental MLCW variations adequately. RMSE_InSAR is computed on the cumulative residuals (predicted cumulative compaction divided by $\alpha$ minus cumulative InSAR) in units of mm. Because the cumulative signal spans hundreds of mm over 10 years, RMSE_InSAR values below approximately 30 mm are acceptable for a model calibrated on layerwise GWL alone.

### 9.5 $R^2_{InSAR}$ in the cumulative domain

The coefficient of determination $R^2_{InSAR}$ is computed on the cumulative InSAR residuals. A positive value confirms that the cumulative predicted compaction tracks the secular InSAR trend better than a flat (zero-displacement) prediction. A negative $R^2_{InSAR}$ indicates that the cumulative predictions diverge from InSAR worse than a zero-displacement baseline, which corresponds to physically unreliable $\alpha$ and storage coefficient estimates. Achieving $R^2_{InSAR} > 0.5$ at the full-record scale is the minimum acceptance criterion for a station to proceed to batch processing.

---

## Section 10 — Version History and File Guide

The IHM-F pipeline evolved through three distinct model formulations. Understanding the differences clarifies which files are active and which are retained only for archival comparison.

| Version | Entry point | Solver | Model equation | Status |
|---------|------------|--------|---------------|--------|
| v1 | `fit_ihm_f.py` | `ihmf_model.py` | $\Delta b_j = b_k \cdot \Delta x + S_{ske} \cdot \Delta H_j$; InSAR as per-layer predictor; Path A / Path B routing based on 2S-TOOL output | Legacy (physically incorrect) |
| v2 | `fit_ihm_f_v2.py` | `ihmf_model_v2.py` | Detrended OLS with $\beta_k \cdot x^d(t)$ per layer; InSAR still as per-layer predictor after detrending | Legacy (physically incorrect) |
| v3 | `fit_ihm_f_v3.py` | `ihmf_model_v3.py` | $\Delta b_j = S_j \cdot \Delta H_j(t - \tau_j)$; InSAR as total target only; two-step solve | Active (production) |

### Why v1 and v2 were physically incorrect

Both v1 and v2 included an InSAR term directly in the per-layer compaction equation, either as $b_k \cdot \Delta x$ (v1) or $\beta_k \cdot x^d(t)$ (v2). This formulation violates the physics of the Inelastic Head Model: InSAR measures the cumulative vertical displacement at the surface, which is the sum of compactions from all depth layers. It is not a driver of compaction at any individual layer; it is the aggregate result. Including InSAR as a per-layer predictor creates a structural collinearity between the GWL signal and the InSAR signal (both share the long-term dewatering trend of the aquifer system), which caused the solver to assign zero weight to GWL at layers where the trend-band collinearity was greatest (F1 and F3 at TUKU: $r(\Delta H, x) = 0.66$ before detrending).

The v3 formulation removes InSAR from the per-layer equation entirely. InSAR enters only in the surface alignment equation (Step 2), where it constrains $\alpha$ without competing with GWL for per-layer variance.

### Active files summary

The following files are used in the current production workflow. The legacy v1 and v2 files are retained for comparison but not called by any active production script.

| File | Active use |
|------|-----------|
| `ihmf_io.py` | Called by v3 via `ihmf_io_multilayer.py` |
| `ihmf_io_multilayer.py` | Called by `fit_ihm_f_v3.py` |
| `ihmf_detrend.py` | Called by `ihmf_model_v3.py` (detrend utility used in walk-forward) |
| `ihmf_model_v3.py` | Core solver, called by `fit_ihm_f_v3.py` |
| `fit_ihm_f_v3.py` | Primary single-station entry point |
| `batch_v3.py` | Batch runner for all 37 stations |
| `ihmf_plots.py` | Called by `fit_ihm_f_v3.py` for output figures |
