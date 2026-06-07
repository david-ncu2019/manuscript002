# Hand-Calculation Guide: Stress-Strain Curves from Groundwater Level and Compaction Data

## 1. Introduction

This guide walks through every calculation inside `prepare_stress_strain.py` and `plot_stress_strain.py` — two scripts that convert raw groundwater-level measurements and Multi-Layer Compaction Well (MLCW) records into **stress-strain hysteresis curves**.

### Purpose

A stress-strain curve plots **effective stress** (the force that compresses the soil skeleton) against **vertical strain** (the fractional shortening of a soil layer). For the Choushui River Alluvial Fan, these curves reveal:

- Whether compaction is **elastic** (recoverable, follows the preconsolidation stress path) or **inelastic** (permanent, new compression beyond the maximum past stress)
- The **preconsolidation stress threshold** — the stress boundary that separates reversible from irreversible deformation
- **Hysteresis loop area** — a measure of energy dissipation per loading cycle, which indicates plastic deformation

### Intended audience

This guide is for researchers and analysts who want to understand exactly what the scripts do — step by step, with real numbers — so they can verify the output, adapt the method, or debug issues. No advanced soil mechanics background is required.

---

## 2. Prerequisites

### Required inputs

| Input file | Format | Source script | Contains |
|------------|--------|---------------|----------|
| `ihmf_config.json` | JSON | `scripts/10_ihmf/...` | 191 station-layer entries, well codes, file paths |
| `{STATION}_reconst_grouped.csv` | CSV | MLCW pipeline | datetime + compaction (mm) per layer code (F1–F4, T1–T2) |
| `{STATION}_{GWL}_{WELLCODE}.feather` | Feather | GWL pipeline | datetime + head (m above MSL) per well code |
| `mlcw_interp_insar_IDW_extend.feather` | Feather | InSAR pipeline | datetime + displacement (m) per station |
| `layer_thickness.csv` | CSV | `scripts/11_data_analysis/` | station, layer, span_m (m), n_rings |

### Tools and environment

- **Python 3.10** with `numpy`, `pandas`, `matplotlib`, `scipy`
- Run inside the **`isce_ncu3`** conda environment
- Scripts live in `scripts/12_stress_strain/`
- Output directory: `results/stress_strain/{STATION}/`

### How to run

Compute stress-strain data for every layer at TUKU station:

```bash
conda run -n isce_ncu3 \
  python scripts/12_stress_strain/prepare_stress_strain.py \
  --station TUKU --all
```

Plot the results:

```bash
conda run -n isce_ncu3 \
  python scripts/12_stress_strain/plot_stress_strain.py \
  --station TUKU
```

---

## 3. Algorithm — Phase by Phase

### Phase 1: Configuration and Entry Selection

**What happens.** The script reads `data/ihmf_config.json`. This file defines 191 station-layer pairs, each with file paths and parameters. The `--station TUKU` flag filters to entries where `station` matches `"TUKU"`. The `--all` flag selects all layers (F1, T1, F2, T2, F3, F4). The script also reads the shared `insar_csv` path from the config to locate the InSAR data file.

**Example.** For TUKU, the config contains entries like:

```json
{
  "station": "TUKU",
  "layer": "F2",
  "assigned_wellcode": "09050321",
  "well_elev_m": 30.0,
  "gwl_feather": "data/gwl/mlcw_gwl_timeseries/TUKU_ERLIN_09050321.feather",
  "mlcw_reconst_csv": "data/mlcw/group_byLayer_reconstr/TUKU_reconst_grouped.csv",
  "hc_percentile": 10,
  "tau_max": 12
}
```

**Why.** The config file acts as a central registry. It avoids hard-coding file paths in every script and ensures every station-layer pair uses the correct well code, feather file, and parameters. If the config is wrong (wrong well code, wrong feather path), the script silently fails to load data, producing all-NaN columns.

---

### Phase 2: Data Loading

Three raw data sources are loaded independently, then aligned to a common timeline.

#### Step 2.1 — Load MLCW compaction

**What happens.** Read `{STATION}_reconst_grouped.csv`. Parse the `datetime` column. Extract the column matching the target layer code (e.g., `"F2"`). Rename it to `mlcw_mm`.

**Example.** For TUKU F2, the raw CSV contains columns `datetime`, `F1`, `T1`, `F2`, `T2`, `F3`, `F4`. The script extracts only `datetime` and `F2`, then renames `F2` to `mlcw_mm`. The values are cumulative compaction in millimetres. Negative means the layer is compressing (shortening).

```python
mlcw[["datetime", "F2"]].rename(columns={"F2": "mlcw_mm"})
```

| datetime | mlcw_mm |
|----------|---------|
| 2015-03-01 | −130.773 |
| 2015-04-01 | −135.270 |
| 2015-05-01 | −137.664 |

**Why.** MLCW data arrives as a wide-format table: one column per layer. The script must pick the correct column for the target layer. If the layer code does not match (e.g., requesting `F2` at a station that has only `F1` and `F3`), pandas raises a `KeyError`.

#### Step 2.2 — Load GWL head

**What happens.** Read the feather file specified by `gwl_feather` in the config. Extract the column matching `assigned_wellcode` (e.g., `"09050321"`). Rename it to `head_m`. Drop rows where head is missing (`NaN`). The values are piezometric head in **metres above mean sea level (MSL)**.

**Example.** The wellcode `09050321` is an 8-digit string. It must remain a string — converting it to an integer drops the leading zero and breaks the column lookup.

| datetime | head_m |
|----------|--------|
| 2015-03-01 | −1.14 |
| 2015-04-01 | −1.00 |
| 2015-05-01 | −1.58 |

A head of −1.14 m MSL means the water level in the well is 1.14 metres below mean sea level. This is common for deep confined aquifers that have been heavily pumped.

**Why.** GWL head is the primary driver of deformation. Higher head means higher pore-water pressure, which reduces the effective stress on the soil skeleton. The feather format is efficient for column-based time-series lookups. Converting well codes to integers is a common bug — the codes are 8-digit strings that include leading zeros.

#### Step 2.3 — Load InSAR displacement

**What happens.** Read the master InSAR CSV. Parse the first column as `datetime`. Extract the column matching the station name (e.g., `"TUKU"`). Multiple the values by 1000 to convert from **metres to millimetres**. The sign is preserved: negative = subsidence (the ground surface moves downward).

**Why.** InSAR measures total surface deformation, not per-layer compaction. The stress-strain curve uses MLCW for per-layer strain, not InSAR. The InSAR channel is available in the output for comparison but is not part of the stress-strain computation.

---

### Phase 3: Timeline Alignment

**What happens.** The three data sources have different sampling schedules. MLCW and GWL sample approximately every 5 days. InSAR samples approximately every 25 days (when a satellite passes overhead and coherence is adequate). The script aligns all data to the **InSAR timeline** because InSAR has the coarsest temporal resolution.

The alignment uses `pd.merge_asof` with `direction="nearest"`. For every InSAR epoch, the script finds the nearest GWL and MLCW measurement in time and attaches it.

**Why.** Regression and stress-strain analysis require paired observations — each stress value must correspond to a strain value at the same epoch. Without alignment, the time series have different lengths and timestamps. Merge-asof (not exact merge) is necessary because timestamps rarely match exactly across independent instruments.

**Potential issue.** If the GWL or MLCW data has large temporal gaps (e.g., instrument downtime), the nearest match may be far from the InSAR epoch, introducing a time-mismatch error. The script does not warn about large gaps.

---

### Phase 4: Preconsolidation Head (h_c)

**What happens.** Compute the preconsolidation head as the **10th percentile** of all GWL head values. The 10th percentile means 10% of historical head measurements are lower (more stressed) and 90% are higher (less stressed).

```python
h_c_head = np.percentile(gwl_raw["head_m"].dropna(), 10)
```

This is converted to a **depth** relative to the well elevation:

```python
h_c_depth = well_elev_m - h_c_head
```

**Example.** For TUKU F2: `h_c_head = −1.06 m MSL`. With `well_elev_m = 30.0 m`, the preconsolidation depth is `30.0 − (−1.06) = 31.06 m` below the ground surface.

**Why.** The preconsolidation head marks the boundary between elastic and inelastic behaviour. When head rises above h_c, the aquifer is re-pressurised along its previous loading path (elastic). When head falls below h_c, the aquifer surpasses its maximum past stress and compresses inelastically — a permanent deformation. Using the 10th percentile (rather than the absolute minimum) prevents a single outlier from defining the threshold. The threshold is configurable via `hc_percentile` in the config.

**Potential issue.** If GWL data quality is poor (many gaps, short record), the percentile estimate becomes unreliable. A 10th percentile from 2 years of data may not represent the true preconsolidation head from 50 years of pumping history.

---

### Phase 5: Layer Thickness Lookup

**What happens.** Read `results/data_analysis/layer_thickness.csv`. Find the row matching the target station and layer. Extract `span_m` — the vertical distance from the shallowest to the deepest magnetic ring within that layer.

**Example.** For TUKU F2: `span_m = 72.51 m`. This means the F2 layer spans from about 50 m to 123 m below the surface — 72.51 metres total thickness, measured by 5 magnetic rings in the MLCW borehole.

**Special case — single-ring layers.** Some layers have only one magnetic ring. These layers have `span_m = 0.0` because there is no vertical interval to measure. The script detects this and sets `span_m = NaN` (Not a Number), which means strain cannot be computed.

**Why.** Strain is compaction divided by original thickness. Without a known thickness, strain is undefined. Of 195 station-layer pairs, 28 have single-ring layers. The guide includes a note about this limitation in the output.

---

### Phase 6: Effective Stress Computation

This is the core physics step.

**What happens.** Compute the **change in effective stress** (Δσ', in kilopascals) at every epoch:

$$
\Delta\sigma'(t) = -\gamma_w \times [\text{head\_m}(t) - h_c\text{\_head\_m}]
$$

Where:
- $$\gamma_w = 9.81 \text{ kPa/m}$$ — unit weight of water
- $$\text{head\_m}(t)$$ — piezometric head at epoch t (m above MSL)
- $$h_c\text{\_head\_m}$$ — preconsolidation head (m above MSL)

The negative sign ensures that a **drop in head** (which increases effective stress on the soil skeleton) produces a **positive Δσ'**.

**Example calculations using TUKU F2 data.**

Row 1 — head is below h_c (inelastic loading):
```
head_m = −1.14 m
h_c_head_m = −1.06 m
head_m − h_c_head_m = −1.14 − (−1.06) = −0.08 m
Δσ' = −9.81 × (−0.08) = +0.78 kPa
```
Positive Δσ': effective stress increased by 0.78 kPa because head fell 0.08 m below the preconsolidation threshold.

Row 5 — head is well above h_c (elastic unloading):
```
head_m = +2.83 m
head_m − h_c_head_m = 2.83 − (−1.06) = 3.89 m
Δσ' = −9.81 × 3.89 = −38.2 kPa
```
Negative Δσ': effective stress decreased by 38.2 kPa because head rose 3.89 m above the preconsolidation threshold — the water pressure carries more of the load.

Row 8 — head at highest recorded level (lowest stress):
```
head_m = +5.37 m
Δσ' = −9.81 × (5.37 − (−1.06)) = −9.81 × 6.43 = −63.1 kPa
```

**Why.** Terzaghi's effective stress principle states that total stress (σ) is the sum of effective stress (σ') carried by the soil skeleton and pore-water pressure (u): σ = σ' + u. When GWL rises, pore pressure increases, so effective stress decreases (the water carries more load). When GWL falls, pore pressure decreases, so effective stress increases (the soil skeleton carries more load). Compaction occurs when the soil skeleton bears more load.

**Why the negative sign?** It aligns the signs intuitively: downward head movement (+Δσ') causes compaction (negative ε). Both analysts and the hysteresis plot benefit from this consistency.

**Potential issue.** This formula assumes instantaneous equilibrium between head change and effective stress change. In low-permeability aquitards (T layers), the pore pressure response may be delayed by months or years (the `τ` parameter in the IHM-F model). The stress-strain curve may show "butterfly" loops if the effective stress change computed from head is not synchronised with the actual mechanical loading.

---

### Phase 7: Vertical Strain Computation

**What happens.** Compute the **vertical strain** (ε, in millimetres per metre) at every epoch:

$$
\epsilon(t) = \frac{\Delta b_j(t)}{b_j}
$$

Where:
- $$\Delta b_j(t)$$ — cumulative compaction of layer j at epoch t (mm, negative = compression)
- $$b_j$$ — layer thickness, span_m (m)

**Example calculation using TUKU F2 data.**

First epoch:
```
mlcw_mm = −130.773 mm
span_m = 72.51 m
ε = −130.773 / 72.51 = −1.8035 mm/m
```
Negative ε: the layer has shortened by 1.80 mm for every metre of its original thickness.

Since the start of monitoring, the total compaction of this 72.5-metre layer is 130.8 mm. This strain represents the cumulative deformation — not the strain at each epoch, but the total strain from time zero.

**Why.** Strain normalises compaction by layer thickness. A 10 mm compaction in a 10 m layer (ε = 1.0 mm/m) is mechanically significant. The same 10 mm in a 100 m layer (ε = 0.1 mm/m) is trivial. Without normalisation, thick layers always show larger compaction values and comparisons across layers are meaningless.

**Special case — single-ring layers.**
```python
if single_ring:
    strain_mm_m = NaN
```
When `span_m = 0`, the script cannot compute strain (division by zero). All 28 single-ring layers in the dataset produce NaN strain values. The output CSV flags these with `single_ring = True`.

**Potential issues.** The strain formula uses the total classified thickness, which may not be the true compressible thickness. If the magnetic rings capture only part of the hydrogeologic layer, the strain is over-estimated (denominator too small). If the rings extend beyond the active compaction zone, the strain is under-estimated (denominator too large).

---

### Phase 8: Regime Classification

**What happens.** Classify each epoch as elastic or inelastic:

```python
is_elastic = head_m >= h_c_head_m
```

- **Elastic** (True): head is at or above the preconsolidation threshold. Deformation is recoverable. The aquifer follows the re-loading curve.
- **Inelastic** (False): head is below the preconsolidation threshold. The aquifer experiences new, permanent compaction.

**Example.** For TUKU F2: `h_c_head_m = −1.06 m MSL`.

| Date | head_m | Below h_c? | is_elastic |
|------|--------|:----------:|:----------:|
| 2015-03-01 | −1.14 | Yes (lower head) | False |
| 2015-04-01 | −1.00 | No (higher head) | True |
| 2015-05-01 | −1.58 | Yes | False |

The first measurement is inelastic because the head is below the preconsolidation threshold. As head fluctuates seasonally, the layer alternates between elastic unloading (head rises) and inelastic loading (head falls below h_c).

**Why.** The elastic/inelastic distinction is fundamental to subsidence mechanics. Elastic deformation reflects the normal response of a confined aquifer to seasonal pumping and recharge — the layer compresses and recovers each year. Inelastic deformation is permanent: once the pore space is destroyed, it cannot be recovered. The hysteresis plot colours these two regimes differently to make the deformation type visually apparent.

**Potential issue.** The regime boundary depends on h_c, which comes from the 10th percentile of all historical head measurements. If the monitoring period includes only wet years, the 10th percentile may be too high, classifying some elastic loading as inelastic. If it includes only dry years, the opposite problem occurs.

---

### Phase 9: Output Assembly

**What happens.** Combine all computed columns into a single DataFrame and write to `results/stress_strain/{STATION}/{STATION}_{LAYER}_stress_strain.csv`.

The output CSV contains these columns:

| Column | Description | Units | Example (TUKU F2) |
|--------|-------------|-------|--------------------|
| `datetime` | Observation date | ISO date | 2015-03-01 |
| `head_m` | Piezometric head | m above MSL | −1.14 |
| `mlcw_mm` | Cumulative layer compaction | mm | −130.77 |
| `insar_mm` | InSAR surface displacement | mm | −10.03 |
| `stress_kpa` | Effective stress change Δσ' | kPa | +0.78 |
| `strain_mm_m` | Vertical strain ε | mm/m | −1.804 |
| `is_elastic` | Elastic regime flag | True/False | False |
| `h_c_head_m` | Preconsolidation head | m above MSL | −1.06 |
| `span_m` | Layer thickness | m | 72.51 |
| `single_ring` | Single-ring flag | True/False | False |
| `wellcode` | GWL well code | 8-digit string | 09050321 |
| `tau_max` | Maximum delay parameter | epochs | 12 |

**Why.** The CSV is a machine-readable record of every intermediate and final value for every epoch. Downstream scripts (the plotter, model comparison, statistical analysis) read this file instead of re-running the full computation.

**Potential issue.** The file is overwritten each time the script runs for the same station and layer. There is no versioning. If the config changes between runs, old results are lost.

---

### Phase 10: Visualization

**What happens.** `plot_stress_strain.py` reads the stress-strain CSVs and produces two figures per station.

#### Figure 1: Hysteresis plot (stress-strain diagram)

One subplot per layer. Each subplot shows:

- **X-axis**: effective stress change Δσ' (kPa)
- **Y-axis**: vertical strain ε (mm/m)
- **Blue points**: elastic epochs (recoverable deformation)
- **Red points**: inelastic epochs (permanent deformation)
- **Grey line**: connects consecutive epochs in time order, showing the hysteresis loop direction
- **Dashed axes**: zero lines for reference

The hysteresis loop reads like a clock:
- **Loading phase** (stress increasing, strain becoming more compressive): the curve moves down-and-right
- **Unloading phase** (stress decreasing, strain becoming less compressive): the curve moves up-and-left
- **Loop area**: the separation between loading and unloading paths indicates the energy dissipated by inelastic deformation

#### Figure 2: Time series

A stacked figure with two panels:
- **Upper panel**: Δσ' over time, one line per layer
- **Lower panel**: ε over time, one line per layer

**Why.** The hysteresis plot is the core diagnostic. A large loop area indicates significant inelastic deformation. A narrow or absent loop indicates purely elastic, recoverable deformation. The time series helps identify which events (drought years, pumping seasons) drive the largest stress excursions.

---

## 4. Complete Worked Example — TUKU F2

This section walks through every calculation for a single row, from raw data to final output.

**Config entry:**
```json
{
  "station": "TUKU",
  "layer": "F2",
  "assigned_wellcode": "09050321",
  "well_elev_m": 30.0,
  "gwl_feather": "data/gwl/mlcw_gwl_timeseries/TUKU_ERLIN_09050321.feather",
  "mlcw_reconst_csv": "data/mlcw/group_byLayer_reconstr/TUKU_reconst_grouped.csv",
  "hc_percentile": 10
}
```

**Step 1 — Preconsolidation head.** All GWL head values for this well are collected. The 10th percentile is −1.06 m MSL.

**Step 2 — Layer thickness.** `layer_thickness.csv` contains `TUKU, F2, 72.51, 5, 50.31, 122.82`. span_m = 72.51 m.

**Step 3 — Stress and strain for 2015-03-01.**

```
head_m = −1.14 m MSL    (measured)
Δh = head_m − h_c_head_m = −1.14 − (−1.06) = −0.08 m
Δσ' = −9.81 × (−0.08) = +0.78 kPa

mlcw_mm = −130.77 mm    (measured)
ε = −130.77 / 72.51 = −1.80 mm/m
```

Check signs: Δσ' is positive (effective stress increased because head dropped), ε is negative (layer compressed). This is physically consistent: loading → compaction.

**Step 4 — Regime.** `head_m = −1.14 < h_c_head_m = −1.06`, so this epoch is **inelastic** (`is_elastic = False`). The head is below the 10th-percentile threshold. The aquifer is experiencing new, permanent compaction.

**Step 5 — CSV row.**

```
2015-03-01, −1.14, −130.77, −10.03, 0.78, −1.80, False, −1.06, 72.51, False, 09050321, 12
```

---

## 5. Verification Checklist

Use these checks to confirm the output is physically and numerically correct before plotting.

### Sign checks

| Check | Expected | If wrong |
|-------|----------|----------|
| `head_m` rising → `stress_kpa` decreasing | Negative Δσ' | Check the negative sign in the formula |
| `head_m` falling → `stress_kpa` increasing | Positive Δσ' | Check the negative sign in the formula |
| `mlcw_mm` becoming more negative → `strain_mm_m` more negative | Same sign | Strain just scales compaction; cannot have opposite sign |
| Most epochs should be elastic | `is_elastic = True` for >80% | h_c percentile may be too low |

### Range checks

| Quantity | Typical range | If outside |
|----------|---------------|------------|
| Δσ' (F2 layer) | −100 to +100 kPa | Head range is unusually large (>20 m swing) |
| ε (F2 layer) | −3 to 0 mm/m | Compaction exceeds plausible bounds for the thickness |
| Δσ' (shallow layer F1) | −50 to +30 kPa | Smaller range than deep layers (less confinement) |
| ε (single-ring layer) | NaN | Expected; cannot compute strain without thickness |

### Data completeness checks

- All output CSVs have the same number of rows (should match InSAR epoch count, typically 130 for TUKU)
- `strain_mm_m` is all-NaN for single-ring layers only
- `h_c_head_m` is consistent across all layers at the same station (depends only on well, not layer)

### Plot sanity checks

- Hysteresis loops should be oriented **clockwise**: loading along the lower path, unloading along the upper path
- Inelastic points (red) cluster at the **rightmost** extreme of stress (where head is lowest)
- Time series should show seasonal cycles in both stress and strain

---

## 6. Common Errors and Troubleshooting

| Error | Likely cause | Fix |
|-------|-------------|-----|
| `KeyError: 'F2'` in MLCW load | Station has no layer F2 | Check available layers in the config entry |
| All-NaN stress column | GWL feather file has wrong wellcode | Verify wellcode is 8-digit string, not int |
| All layers show single-ring=false | `layer_thickness.csv` not found | Run `layer_thickness` analysis first |
| Strain values are extremely large (e.g., −50 mm/m) | Layer thickness is very small | Check classify_table; may be a genuine thin layer |
| Plot shows no red (inelastic) points | h_c is set too low (e.g., 0th percentile) | Check `hc_percentile` in config; default should be 10 |

---

## 7. Conclusion

### What the algorithm produces

Running `prepare_stress_strain.py` for a station produces one CSV per layer with columns for stress, strain, head, compaction, and regime classification. Running `plot_stress_strain.py` produces two figures: a multi-panel hysteresis diagram and a stress-strain time series.

### What the outputs mean

- **Δσ' (effective stress change)** tells you how hard the soil skeleton is being loaded by groundwater level changes. Positive = loading, negative = unloading.
- **ε (vertical strain)** tells you how much the layer has compressed per metre of thickness. Negative = compression, positive = expansion (unlikely in a compacting aquifer).
- **is_elastic** tells you whether the current state is on the re-loading curve (recoverable) or beyond the maximum past stress (permanent).

### How to verify

Every new dataset should pass the sign and range checks in Section 5. The hysteresis plot should show the characteristic clockwise loop of poroelastic compaction: loading along the lower branch during dry seasons, unloading along the upper branch during wet seasons, with loop area proportional to inelastic deformation.

---

## Appendix: Derivation of the Stress Formula

The change in effective stress is derived from Terzaghi's principle:

$$ \sigma = \sigma' + u $$

Where σ = total stress (constant, overburden), σ' = effective stress (carried by soil skeleton), u = pore-water pressure.

Pore-water pressure is related to hydraulic head:

$$ u = \gamma_w \times h $$

Where h = piezometric head above a datum.

Taking differences from a reference state (the preconsolidation head h_c):

$$ \Delta\sigma' = -\gamma_w \times (\Delta h) = -\gamma_w \times (h - h_c) $$

The negative sign reflects the inverse relationship: when head rises (Δh positive), pore pressure increases and effective stress decreases. When head falls (Δh negative), pore pressure decreases and effective stress increases.
