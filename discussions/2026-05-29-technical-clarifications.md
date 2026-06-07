# Technical Clarifications: IHM-F Workflow Questions and Corrections

**Date:** 2026-05-29  
**Relates to:** `discussions/2026-05-29-ihmf-workflow.md`  
**Purpose:** Addresses 8 technical corrections and questions raised after review of the workflow document. Each user point is restated verbatim in a coloured box, followed by the corrected or expanded answer grounded in source data and literature.

---

## Item 1 — InSAR Displacement Type

<div style="background-color:#fff3e0; border-left:5px solid #ef6c00; padding:12px; margin:12px 0;">
<strong>User correction:</strong><br>
"incremental line-of-sight surface displacement measured by InSAR → vertical displacement from InSAR (obtained by performing ascending–descending decomposition)"
</div>

The correction is accurate. The InSAR displacement values stored in `data/insar/timeseries/mlcw_interp_insar_IDW_extend.feather` and `data/insar/InSAR_measures_at_MLCW.csv` are **total vertical surface displacement**, not line-of-sight (LOS) measurements. Vertical displacement was derived by combining ascending and descending orbit InSAR stacks through orbit decomposition, implemented in `scripts/01_insar_preprocessing/E1_insar_asc_desc_decompose_parallel.py`. The decomposition resolves the east–west and vertical displacement components from the two viewing geometries, discarding the north–south component (to which near-polar orbits are insensitive). The vertical component is retained as the primary displacement observable because aquifer-system compaction produces predominantly vertical motion.

The workflow document will be corrected to read: "total vertical surface displacement derived from ascending and descending orbit decomposition" wherever it previously referred to "line-of-sight surface displacement."

---

## Item 2 — MLCW Reconstruction Method

<div style="background-color:#fff3e0; border-left:5px solid #ef6c00; padding:12px; margin:12px 0;">
<strong>User correction:</strong><br>
"data were reconstructed using Seasonal-Trend decomposition using LOESS (STL) at a 5-day regular interval → it is wrong, you need to check my_dataset_summary.md and batch_reconstruct_MLCW.py to understand it correctly."
</div>

The STL attribution was incorrect. Verification of `scripts/02_mlcw_processing/batch_reconstruct_MLCW.py` and `my_dataset_summary.md` (§1.1, processing pipeline) confirms the actual procedure:

1. Raw ring-by-ring magnetic ring measurements at approximately monthly field-campaign dates are decomposed into trend, seasonal, and residual components using the `appsigsolv` parametric signal decomposition library (`estimate_time_func`, `get_design_matrix4time_func`). This library fits a parametric time function (polynomial trend plus harmonic components) to the irregularly sampled field-campaign data.
2. The fitted parametric model is then evaluated at a custom dense grid: the 1st, 6th, 11th, 16th, 21st, and 26th day of each calendar month. This grid produces approximately one observation every 5 days (with minor variation at month boundaries) and spans from the station's first measurement to October 2025.
3. The resulting ~1,572 reconstructed rows per station constitute the `group_byLayer_reconstr/` files used as the primary Track B calibration input.

The method is therefore a **parametric time-function decomposition with custom-cadence resampling**, not STL. The workflow document will be corrected accordingly.

---

## Item 3 — Temporal Resolution of Each Dataset

<div style="background-color:#fff3e0; border-left:5px solid #ef6c00; padding:12px; margin:12px 0;">
<strong>User correction:</strong><br>
"Because both GWL and MLCW are reconstructed at 5-day intervals → only MLCW timeseries were reconstructed into 5-day interval. GWL data in data/gwl/well_timeseries/{STATION}_gwl_timeseries.feather is daily."
</div>

The correction is accurate. The three datasets used in IHM-F have different native temporal resolutions:

| Dataset | Native cadence | Date range | Rows (typical) |
|---------|---------------|------------|----------------|
| InSAR vertical displacement | ~5-day (785 epochs, median gap 5 days) | 2015-01-21 to 2025-12-11 | 785 |
| MLCW layer-grouped (reconstructed) | Custom 5-day (days 1, 6, 11, 16, 21, 26 of each month) | 2003 to 2025 | ~1,572 |
| GWL piezometric head | **Daily** | 2000-01-01 to 2025-12-31 | 9,497 |

The GWL feather files (`data/gwl/well_timeseries/{STATION}_gwl_timeseries.feather`) contain one row per calendar day from 2000 to 2025. No reconstruction or resampling is applied to the GWL data. The `load_and_align` function in `ihmf_io.py` aligns GWL daily records to the InSAR epoch timeline using `merge_asof` with `direction="nearest"`, which selects the GWL observation closest in time to each InSAR acquisition. Because InSAR epochs are spaced ~5 days apart and GWL is observed daily, the nearest-match offset is at most 2–3 days.

---

## Item 4 — Choice of Preconsolidation Head Threshold

<div style="background-color:#e8f5e9; border-left:5px solid #2e7d32; padding:12px; margin:12px 0;">
<strong>User question:</strong><br>
"Actually, I'm somewhat uncertain about the choice of preconsolidation head value in this study. Instead of using the 10th percentile, do you think we should use the minimum value from the time period before the first InSAR observation? From a physical standpoint, our data only becomes usable from 2015 onwards, and we have no information about the preceding period. Therefore, the minimum value from the pre-2015 period could serve as a reasonable reference point. What do you think?"
</div>

The pre-2015 minimum is physically better justified than the 10th percentile of the full record, for three reasons.

**Reason 1 — Physical meaning of the preconsolidation head.** The preconsolidation head $h_c$ marks the lowest piezometric head level the aquifer has ever experienced prior to the current observation window. When head declines below $h_c$, effective stress exceeds the historical maximum effective stress (the preconsolidation stress), and inelastic consolidation begins. For the modelling window (2015–2025), the relevant preconsolidation head is the minimum head observed before 2015-01-16 (the first InSAR epoch), because that minimum defines the stress state the aquifer entered the observation window having already experienced.

**Reason 2 — Avoiding contamination from post-2015 drought lows.** The 10th percentile of the full (2000–2025) record may be set by severe post-2015 drought years that produced new historical lows. If a post-2015 minimum is used as $h_c$, then epochs before that new minimum are misclassified as elastic when they may already be inelastic. The pre-2015 minimum isolates the threshold that was pre-existing at the start of the observation window.

**Reason 3 — Data availability.** GWL feather files cover 2000-01-01 to 2025-12-31 at daily resolution. Pre-2015 records are therefore available for most wells (15 years of daily data). For the two wells that lack pre-2015 data in the feather files (YIWU well 09190112 and ZHENNAN/SHILIU well 09010212), pre-2015 GWL is available from `D:\1000_SCRIPTS\004_Project003\20251229_Gwater_Levels\20240828_GWL_CRFP_model.h5`, which covers 2001-01-01 to 2024-12-31.

**Recommended implementation.** Replace the current 10th-percentile calculation in `ihmf_io.py` with:

```python
pre2015_mask = gwl_raw["datetime"] < pd.Timestamp("2015-01-16")
if pre2015_mask.sum() >= 10:
    h_c_head = float(gwl_raw.loc[pre2015_mask, "head_m"].dropna().min())
else:
    # Fallback for wells with no pre-2015 records
    h_c_head = float(gwl_raw["head_m"].dropna().quantile(0.10))
```

The fallback handles the two problem wells where pre-2015 H5 data has not yet been spliced into the feather file. Once those are spliced, the fallback will never activate.

---

## Item 5 — Temporal Resolution and Pre-2015 GWL Availability

<div style="background-color:#e8f5e9; border-left:5px solid #2e7d32; padding:12px; margin:12px 0;">
<strong>User question:</strong><br>
"In this formula Δb_j(t) = b_j(t) − b_j(t−1) and ΔH_j(t) = H_j(t) − H_j(t−1), does both datasets share the same 5-day interval temporal resolution? Does the groundwater dataset contain values before year 2015?"
</div>

**On temporal resolution.** The two incremental signals do not share the same native cadence. InSAR and MLCW both operate on an approximately 5-day grid after reconstruction and alignment, but the GWL increment $\Delta H_j(t)$ as computed in `fit_ihm_f_v3.py` uses daily GWL data aligned to the InSAR timeline. The first-difference $\Delta H_j(t) = H_j(t) - H_j(t-1)$ therefore measures the head change between consecutive InSAR epochs (~5 days), not between consecutive calendar days. The magnitude of $\Delta H_j$ is therefore ~5 times larger than a single calendar-day increment would be.

**On pre-2015 GWL data.** Yes — the GWL feather files (`data/gwl/well_timeseries/{STATION}_gwl_timeseries.feather`) contain daily piezometric head records from 2000-01-01 to 2025-12-31, spanning 15 years of pre-2015 data for most wells. This pre-2015 window is used in Item 4 above to compute the preconsolidation head threshold. It is also used in the GWL lag extension: when a hydraulic lag $\tau_{opt}$ requires GWL values from before 2015-01-16, those values are available from the existing feather files for 193 of 195 station-layer assignments. The two exceptions (YIWU F2 / well 09190112 and ZHENNAN F1 / well 09010212) require data from the H5 archive.

---

## Item 6 — Two Seasonal Removal Functions

<div style="background-color:#e8f5e9; border-left:5px solid #2e7d32; padding:12px; margin:12px 0;">
<strong>User question:</strong><br>
"I don't understand why we have remove_seasonal_cycle and apply_seasonal_removal."
</div>

The two functions serve different roles in the walk-forward validation and are necessary to prevent look-ahead contamination.

**`remove_seasonal_cycle(signal, dates)`** is called on the **training window only**. It computes the climatological mean of the incremental signal for each of the 12 calendar months — for example, the mean January GWL increment across all January observations in the training years. It then subtracts that mean from every training-window epoch of that month. The function returns two outputs: the anomaly signal and the 12 stored monthly mean values.

**`apply_seasonal_removal(signal, dates, monthly_means)`** is called on the **test window**, using the monthly means computed from the training window. It subtracts the training-window climatology from each test epoch by month. The test window's own seasonal pattern is never used.

**Why not use a single function on the combined data?** If both training and test data were passed to a single function, the 12 monthly means would be computed from the full record including the test year. Those test-year data points would then influence the seasonal correction applied to those same test-year predictions. This constitutes look-ahead: information from the future (the test year) enters the model fitting step. The consequence is an optimistic estimate of forecast skill. By storing the training-window climatology and applying it to the test window, the seasonal correction applied to test data is fully determined by training data alone, preserving the integrity of the temporal hold-out.

A practical example: if 2022 (a drought year and Fold 1 hold-out) had unusually deep summer GWL, the seasonal mean for summer months would shift downward if the full-record climatology were used. The anomaly for 2022 summer epochs would then be smaller than their true anomaly, reducing the apparent signal and making the τ search and parameter estimation appear more accurate than they would be in a genuine future deployment.

---

## Item 7 — Why Grid Search τ Instead of Simultaneous Optimisation

<div style="background-color:#e8f5e9; border-left:5px solid #2e7d32; padding:12px; margin:12px 0;">
<strong>User question:</strong><br>
"Why do we do grid search in advance? Why don't we solve everything at the same time?"
</div>

The τ grid search is necessary because **τ must be a non-negative integer**, and integers cannot be included in a linear least-squares solver.

The parameter estimation step (Section 6 of the workflow document) uses `scipy.optimize.lsq_linear`, which minimises $\|A\theta - b\|^2$ over a continuous vector $\theta$. Storage coefficients $S_{ke}$ and $S_{kv}$ are real-valued and bounded below by zero — they fit naturally into this framework. The lag $\tau$, however, is a discrete epoch index. An InSAR acquisition exists at epoch $t$, epoch $t-1$, epoch $t-2$, and so on; there is no observation at epoch $t - 1.5$. A lag of 1.5 epochs would require interpolating between two observations, which introduces values that were never measured. The physical interpretation of $\tau$ as the number of 5-day periods by which the aquifer response lags behind the head change requires $\tau$ to be an integer.

The correct approach for a mixed integer-continuous optimisation of this kind is a **conditional linear solve**: enumerate all candidate integer values of $\tau$ (the grid), and for each fixed $\tau$ solve the remaining continuous-valued problem exactly. This is also the approach used by Smith et al. (2021), who describe a "grid-search approach that samples plausible parameter ranges" before applying the least-squares inversion.

If a continuous solver (e.g., PyTorch gradient descent) were used and $\tau$ were relaxed to real values, the solver might converge to $\tau = 6.3$ epochs. This value is mathematically convenient but physically meaningless: it cannot be mapped to any actual observation in the dataset, and no valid lagged GWL array can be constructed from it without interpolation that assumes a smoother signal than actually exists between discrete acquisitions.

---

## Item 8 — Workflow Phasing: Full Timeseries First

<div style="background-color:#e8f5e9; border-left:5px solid #2e7d32; padding:12px; margin:12px 0;">
<strong>User suggestion:</strong><br>
"We can temporarily use entire timeseries to get the right workflow first, then perform walk-forward validation later."
</div>

This suggestion is adopted. The immediate priority is to verify that the full-record fit produces physically interpretable results — non-negative $S_{ke}$ and $S_{kv}$, an α in the range $(0, 1]$, and per-layer τ values consistent with known hydraulic lag times for the Choushui aquifer system. Walk-forward validation adds the additional complexity of re-fitting the model on each training fold, and diagnosing failures in that structure requires first having confidence that the full-record fit is correct.

The operational sequence going forward is therefore: (1) verify the full-record fit at TUKU, applying the corrections from Items 1–7 and 9–10 below; (2) once the full-record results are physically sensible, add the walk-forward validation layer on top of the confirmed full-record workflow.

---

## Item 9 — Choushui River Alluvial Fan Storage Coefficient Bounds

<div style="background-color:#e8f5e9; border-left:5px solid #2e7d32; padding:12px; margin:12px 0;">
<strong>User suggestion:</strong><br>
"We have a range of S_ske and S_skv in Choushui River Alluvial Fan here. Maybe you can use them as constraints for our work."
</div>

The Choushui reference data in `data/choushui_skeletal_storage_coeffs.md` (Tables 3-2 through 3-5) provide published specific storage coefficients from stress-strain analyses across 29 MLCW stations. These values are in specific form ($m^{-1}$, per unit thickness) and are directly applicable as bounds on the IHM-F solver after conversion to bulk form.

**Published ranges from Choushui (specific form, $m^{-1}$):**

| Parameter | Minimum | Maximum | Typical range |
|-----------|---------|---------|---------------|
| $S_{ske}$ (elastic) | $2.86 \times 10^{-6}$ | $3.87 \times 10^{-4}$ | $10^{-5}$ to $10^{-4}$ |
| $S_{skv}$ (inelastic) | $1.53 \times 10^{-5}$ | $3.00 \times 10^{-3}$ | $10^{-4}$ to $10^{-3}$ |

**Conversion to bulk form for IHM-F.** The IHM-F model fits $S_j$ (bulk, dimensionless or mm/m depending on sign convention) via:

$$S_{ke,j} = S_{ske} \times b_j \qquad S_{kv,j} = S_{skv} \times b_j$$

where $b_j$ is the thickness of layer $j$ in metres, obtained by summing the ring spans in `{STATION}_classify_table.csv` for all rings assigned to that layer.

For example, at TUKU, layer F2 spans rings from 50.31 m to 122.82 m depth (total thickness $b_{F2} = 72.51$ m from `layer_thickness.csv`). The corresponding bulk storage bounds are:

$$S_{ke,F2} \in [2.86 \times 10^{-6} \times 72.51,\ 3.87 \times 10^{-4} \times 72.51] = [2.1 \times 10^{-4},\ 2.8 \times 10^{-2}]$$

These bounds will replace the current unbounded upper limit $[0, \infty]$ in the `lsq_linear` call. The lower bound remains zero (physical non-negativity). In the code, layer thickness $b_j$ is computed from `classify_table.csv` at runtime, so bounds are station-specific and layer-specific.

**Which thickness — total or compressible?** Published convention (Hung et al. 2012; COMPAC model; Parowan Valley 2023):

- **Elastic regime ($S_{ske}$):** Use **total layer thickness** including all materials (sand + clay). At TUKU F2, $b_{0e} = 72.51$ m. All granular materials contribute to elastic deformation when head is above $h_c$.
- **Inelastic regime ($S_{skv}$):** Use **aggregate compressible fine-grained thickness** only (clay/silt interbeds). Permanent porosity loss occurs almost exclusively in fine-grained materials. At TUKU F2, the fine-grained fraction may be only 40-60% of the total 72.51 m span.
- The v3 production code does NOT distinguish these two thicknesses — it fits lumped $S_{ke}/S_{kv}$ (mm/m) directly from MLCW data without thickness normalization. The per-station `span_m` from `layer_thickness.csv` is the TOTAL vertical span of all rings assigned to that layer (sum of individual ring span lengths). If $S_{skv}$ (1/m specific form) is needed, divide the fitted $S_{kv}$ (mm/m) by (compressible_thickness × 1000), not by (total_span × 1000).

**Important:** The $S_{skv} / S_{ske}$ ratio in the Choushui data ranges from approximately 5 to over 100, with a median near 10–20. The solver should be checked that fitted $S_{kv}$ values exceed $S_{ke}$ by at least this factor for layers where both are non-zero. Layers where $S_{kv} < S_{ke}$ indicate a physically impossible result (inelastic storage smaller than elastic storage) and should be flagged as a diagnostic warning.

---

## Item 10 — Smith ($S_{ke}$) versus Hung ($S_{ske}$): Which Parameter to Use

<div style="background-color:#e8f5e9; border-left:5px solid #2e7d32; padding:12px; margin:12px 0;">
<strong>User question:</strong><br>
"I don't know why Smith uses S_ke in his paper but Hung uses S_ske. I think this selection might significantly affect our work, so I need you to evaluate it one more time."
</div>

The two papers use the same physical quantity expressed at different scales. The distinction is between the **specific** form (per unit thickness, intrinsic material property) and the **bulk** form (integrated over layer thickness, observable quantity). Both are correct; they serve different purposes.

### Smith et al. (2021) — Bulk form $S_{ke}$ (dimensionless)

Smith's F2 is:

$$\Delta b_e = \Delta h \cdot S_{ke}$$

Here $\Delta b_e$ has units of length (the total thickness change of the layer), $\Delta h$ has units of length (head change), and $S_{ke}$ is therefore **dimensionless**. Physically, $S_{ke}$ is the product of the specific elastic skeletal storage coefficient and the compressible thickness: $S_{ke} = S_{ske} \times b$. Smith chose this form because the inversion directly estimates how much total thickness change a given head change produces in each depth interval — a layer-integrated quantity.

### Hung et al. (2021) — Specific form $S_{ske}$ ($m^{-1}$)

Hung's F4 is:

$$\tau = -S_{sk} \cdot \Delta h$$

Here $\tau$ is the dimensionless strain ($\Delta B / B_0$, the fractional thickness change), $\Delta h$ is in metres, and $S_{sk}$ therefore has units of $m^{-1}$. Hung reports $S_{ske}$ and $S_{skv}$ in $m^{-1}$ as intrinsic material properties independent of layer thickness. This form is appropriate for comparing properties across different thicknesses and different sites.

### Relationship between the two

$$S_{ke} = S_{ske} \times b \quad \Longleftrightarrow \quad S_{ske} = \frac{S_{ke}}{b}$$

The conversion requires knowledge of the compressible thickness $b$ of each layer.

### Which form is correct for IHM-F

The IHM-F model equation as formulated in `physics_rules_research_problem.md` is:

$$\Delta b_j(t) = S_j \cdot \Delta H_j(t - \tau_j)$$

where $\Delta b_j$ is in mm (MLCW layer-grouped compaction, not a strain) and $\Delta H_j$ is in metres. Therefore:

$$S_j\ \left[\frac{\text{mm}}{\text{m}}\right] = S_{ske}\ [m^{-1}] \times b_j\ [\text{m}] \times 1000\ \frac{\text{mm}}{\text{m}} = S_{ke}\ [\text{dimensionless}] \times 1000$$

The IHM-F solver fits $S_j$ in mm/m — this is numerically equal to $1000 \times S_{ke}$ (Smith's dimensionless bulk form), and equal to $S_{ske} \times b_j \times 1000$ (Hung's specific form multiplied by thickness and unit conversion).

**Practical consequence for this project:**

| Purpose | Parameter to use | Units | How to obtain |
|---------|-----------------|-------|---------------|
| IHM-F solver (fitting) | $S_j$ (bulk, mm/m) | mm/m | Fitted directly by `lsq_linear` |
| Publication / comparison with Hung et al. | $S_{ske}$, $S_{skv}$ | $m^{-1}$ | $S_{ske} = S_j / (b_j \times 1000)$ |
| Bounds from Choushui table | $S_{ske}$, $S_{skv}$ (Table 3-2 to 3-5) | $m^{-1}$ | Multiply by $b_j \times 1000$ to get $S_j$ bounds |
| Comparison with Smith et al. (2021) | $S_{ke}$ (bulk, dimensionless) | dimensionless | $S_{ke} = S_j / 1000$ |

**This selection matters significantly.** If $S_{ske}$ values from the Choushui table (order $10^{-5}$ $m^{-1}$) were used directly as bounds on $S_j$ (order $10^{-2}$ mm/m for a 100 m layer), the solver would be constrained to physically impossible values — four to five orders of magnitude too small. The correct procedure is to always multiply $S_{ske}$ by $b_j \times 1000$ before using the Choushui reference values as bounds in the solver.

**Recommendation:** The IHM-F code should store $S_j$ (bulk, mm/m) as the fitted parameter, compute $b_j$ from `classify_table.csv` at fit time, and derive $S_{ske} = S_j / (b_j \times 1000)$ in the output JSON for reporting. The solver bounds should be computed as $[S_{ske,min} \times b_j \times 1000,\ S_{ske,max} \times b_j \times 1000]$ using the layer-specific thickness from the classify table.
