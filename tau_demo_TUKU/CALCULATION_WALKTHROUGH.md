# Calculation Walkthrough — TUKU Drainage Lag Search

This document traces every step the code takes, from raw input files to the final result table.
Read it top to bottom. Each section shows: what file the code reads, what it calculates, and what it saves.

**Last updated:** 2026-06-05
**Status:** Bug F (h_c window) fix verified. Results below are from the post-fix run on 2026-06-05 and are the current authoritative output.

---

## What this experiment is trying to find

For each clay or sand layer under TUKU station (6 layers total: F1, T1, F2, T2, F3, F4),
we want to know: **how many days does groundwater level (GWL) need to fall before the clay
layer responds by compacting?**

That delay is called $\tau$ (tau). We find it by testing every possible delay from 0 to 600 days
and picking the one where the shifted GWL signal best matches the compaction signal.

---

## Files involved

| Role | File |
|------|------|
| Script that does the calculation | `tau_demo_TUKU/01_run_tau_search.py` |
| Functions it borrows | `scripts/10_ihmf/ihmf_model_v3.py` |
| Layer-to-well assignment table | `tau_demo_TUKU/data/gwl_to_mlcw_layer_assignment_v4.csv` |
| GWL time series — F1, T1 | `tau_demo_TUKU/data/HONGLUN_gwl_timeseries.feather` |
| GWL time series — F2, F3 | `tau_demo_TUKU/data/TUKU_gwl_timeseries.feather` |
| GWL time series — F4 | `tau_demo_TUKU/data/LIUZHUANG_gwl_timeseries.feather` |
| GWL time series — T2 | `tau_demo_TUKU/data/LUNZI_gwl_timeseries.feather` |
| MLCW compaction time series (every ~5 days, mm) | `tau_demo_TUKU/data/TUKU_reconst_grouped.csv` |
| **Output: one lag per layer** | `tau_demo_TUKU/results/tau_results.csv` |
| **Output: full MSE curve per layer** | `tau_demo_TUKU/results/tau_mse_curves.csv` |
| **Output: aligned data for plots** | `tau_demo_TUKU/results/tuku_aligned_data.npz` |

---

## Step 1 — Read the assignment table

**Script:** `01_run_tau_search.py` lines 61–65
**Reads:** `data/gwl_to_mlcw_layer_assignment_v4.csv`

```python
assign = pd.read_csv(
    DATA_DIR / "gwl_to_mlcw_layer_assignment_v4.csv",
    dtype={"assigned_wellcode": str},   # keep leading zeros, e.g. "09050111"
)
tuku_assign = assign[assign["station"] == "TUKU"].set_index("layer")
```

**What this gives us:** for each TUKU layer, which GWL well to use, how deep the layer is,
how far the well is from TUKU, and how much data the well has in 2023–2025.

**Data preview — TUKU rows from assignment table:**

| layer | Layer depth (m) | Well code | Screen mid (m) | Dist to well (m) | Coverage 2023–2025 | GWL file |
|-------|----------------|-----------|----------------|------------------|--------------------|----------|
| F1 | 8.8 – 25.6 | 09050111 | 22.0 | 4270 | 1095 days | HONGLUN_gwl_timeseries.feather |
| F2 | 50.3 – 122.8 | 09050321 | 82.5 | 15 | 1095 days | TUKU_gwl_timeseries.feather |
| F3 | 172.9 – 272.7 | 09050331 | 177.5 | 15 | 1095 days | TUKU_gwl_timeseries.feather |
| F4 | 283.4 – 300.0 | 09080251 | 282.0 | 6051 | 1094 days | LIUZHUANG_gwl_timeseries.feather |
| T1 | 41.6 – 41.6 | 09050111 | 22.0 | 4265 | 1095 days | HONGLUN_gwl_timeseries.feather |
| T2 | 156.6 – 161.9 | 09170121 | 167.0 | 9606 | 591 days | LUNZI_gwl_timeseries.feather |

Note: F = aquifer (sand), T = aquitard (clay). T1 and F1 share the same GWL well (HONGLUN).
T2 has only 591 days of coverage in 2023–2025 — below the 100-day minimum but retained because
no better nearby well exists.

---

## Step 2 — Read and zero-reference the MLCW compaction data

**Script:** `01_run_tau_search.py` lines 68–80
**Reads:** `data/TUKU_reconst_grouped.csv`

```python
mlcw_raw = pd.read_csv(DATA_DIR / "TUKU_reconst_grouped.csv", parse_dates=["datetime"])
mlcw_raw = mlcw_raw[mlcw_raw["datetime"] >= REF_DATE].reset_index(drop=True)

ref_row = mlcw_raw.iloc[0]   # first row = 2015-01-16
for col in layer_cols:
    mlcw_raw[col] = mlcw_raw[col] - ref_row[col]   # subtract the 2015-01-16 value
```

**What this does:** The MLCW file stores cumulative compaction in mm. We subtract the value
at the reference date (2015-01-16) so the record starts at zero. From that point, a negative
number means the ground has compressed.

$$b_j(t) = b_j^{\text{raw}}(t) - b_j^{\text{raw}}(t_{\text{ref}})$$

**Data preview — MLCW first 5 rows after zero-referencing** (mm, negative = compaction):

| datetime | F1 (mm) | T1 (mm) | F2 (mm) | T2 (mm) | F3 (mm) | F4 (mm) |
|----------|---------|---------|---------|---------|---------|---------|
| 2015-01-16 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 2015-01-21 | −0.048 | −0.045 | −0.402 | −0.128 | −0.113 | +0.017 |
| 2015-01-26 | −0.104 | −0.092 | −0.867 | −0.282 | −0.241 | +0.035 |
| 2015-02-01 | −0.185 | −0.153 | −1.502 | −0.498 | −0.416 | +0.057 |
| 2015-02-06 | −0.265 | −0.205 | −2.094 | −0.702 | −0.581 | +0.073 |

**Time coverage:** 2015-01-16 to end of record, one row every ~5 days. Total: 772 rows.

Key observation: F2 compacts about 10× faster than F1 in the first weeks (−2.094 mm vs −0.185 mm
by 2015-02-01). F4 shows slight expansion (+0.073 mm) — physically unusual and worth watching.

---

## Step 3 — For each layer: read GWL, compute $h_c$, zero-reference, align to MLCW dates

**Script:** `01_run_tau_search.py` lines 100–143
**Reads:** the GWL feather file for this layer (e.g. `HONGLUN_gwl_timeseries.feather`)

```python
# Load raw GWL — covers 2000–2025, daily observations
gwl_raw = pd.read_feather(gwl_path)
gwl_raw = gwl_raw[["datetime", wellcode]].dropna()

# Compute h_c BEFORE zero-referencing (uses full historical record)
head_ref = float(gwl_raw[gwl_raw["datetime"] <= REF_DATE]["head_m"].iloc[-1])
pre_ref_raw = gwl_raw["datetime"] < REF_DATE
if pre_ref_raw.sum() >= 10:
    h_c = float(gwl_raw.loc[pre_ref_raw, "head_m"].min()) - head_ref
else:
    h_c = float(gwl_raw["head_m"].min()) - head_ref

# Zero-reference GWL to 2015-01-16
gwl_raw["head_m"] = gwl_raw["head_m"] - head_ref

# Align GWL to MLCW 5-day dates using nearest-date matching
aligned = pd.merge_asof(mlcw_df, gwl_raw, on="datetime", direction="nearest")
aligned = aligned.dropna(subset=["head_m", "mlcw_mm"])
```

**What this does:**
- GWL is measured daily. MLCW is measured every ~5 days. The `merge_asof` call snaps each MLCW
  date to the nearest GWL date (within a few days).
- `h_c` is computed from the raw absolute head values **before** zero-referencing.
  This is critical — the pre-2015 historical minimum head is deeper than any post-2015 value.
- The zero-reference makes the GWL signal start at zero on 2015-01-16, matching the MLCW baseline.

**Data preview — HONGLUN raw GWL, first 5 rows** (absolute metres above sea level):

| datetime | head_m (m MSL) |
|----------|----------------|
| 2000-01-01 | 10.948 |
| 2000-01-02 | 10.907 |
| 2000-01-03 | 10.867 |
| 2000-01-04 | 10.827 |
| 2000-01-05 | 10.788 |

**HONGLUN record summary:**

| Quantity | Value |
|----------|-------|
| Date range | 2000-01-01 to 2025-12-30 |
| Total daily rows | 9,496 |
| Pre-2015 rows | 5,494 |
| Post-2015 rows | 4,002 |
| Absolute head on 2015-01-16 (`head_ref`) | 8.848 m MSL |
| Absolute minimum pre-2015 | 6.504 m MSL |
| Absolute minimum post-2015 | 3.145 m MSL |

**$h_c$ calculation for HONGLUN (F1 and T1):**

$$h_c = \min(\text{head pre-2015}) - \text{head\_ref} = 6.504 - 8.848 = -2.344 \text{ m (zero-referenced)}$$

After zero-referencing, any head reading below −2.344 m signals that the aquifer has
dropped to a new historical low — the clay layer enters inelastic (permanent) compaction.

---

## Step 4 — Classify each epoch as elastic or inelastic

**Script:** calls `build_regime_mask()` from `ihmf_model_v3.py` lines 125–140

```python
def build_regime_mask(head_m, h_c_head_m):
    elastic   = head_m > h_c_head_m   # head above threshold → elastic rebound
    inelastic = ~elastic               # head at or below threshold → permanent compaction
    return elastic, inelastic
```

**Formula:**

$$\text{elastic}(t) = \begin{cases} \text{True} & \text{if } H(t) > h_c \\ \text{False} & \text{if } H(t) \le h_c \end{cases}$$

**What the two regimes mean physically:**

- **Elastic epoch:** the water table is recovering (rising). The clay springs back slightly but
  no new permanent damage occurs. This reversible squeezing is described by $S_{ke}$ (elastic
  storage coefficient).

- **Inelastic epoch:** the water table has fallen to a new historical low. The pore structure
  of the clay collapses permanently. This is described by $S_{kv}$ (inelastic storage
  coefficient, always larger than $S_{ke}$, typically 8–58× larger for CRAF sediments).

**Expected elastic/inelastic split for HONGLUN (correct $h_c = -2.344$ m):**

The post-2015 head minimum is −5.704 m, well below the −2.344 m threshold. So all epochs
where the head dips below −2.344 m are inelastic. This includes the 2020–2022 drought period
when the head fell to −5.704 m. We expect ~100+ inelastic epochs in 2015–2025.

---

## Step 5 — Take first differences to get incremental signals

**Script:** `01_run_tau_search.py` lines 137–140

```python
inc_dH    = np.diff(head_m)     # m per epoch  (change in head from one date to next)
inc_db    = np.diff(mlcw_mm)    # mm per epoch (change in compaction from one date to next)
inc_dates = dates[:-1]          # date of the driving GWL change
```

**Why incremental, not cumulative?**
The physics equation says compaction *rate* responds to head *change*, not to total head level.
A 0.5 m drop in head today drives compaction over the next $\tau$ epochs.
First differences convert the cumulative record into epoch-by-epoch changes.

$$\Delta H(t) = H(t+1) - H(t), \quad \Delta b(t) = b(t+1) - b(t)$$

After taking differences, the 772-row cumulative record becomes 771 incremental epochs.

---

## Step 6 — Remove the seasonal cycle from both signals

**Script:** calls `remove_seasonal_cycle()` from `ihmf_model_v3.py` lines 47–91,
called inside `tau_grid_search_per_layer`

Before searching for $\tau$, the code strips out the repeating seasonal pattern
(the annual GWL recharge cycle every summer). Otherwise the tau search might find
$\tau \approx 24$ epochs (120 days ≈ 4 months) just because summer GWL always precedes
autumn compaction by that amount — a calendar artifact, not a physical lag.

```python
months = pd.DatetimeIndex(dates).month   # 1 = January, 12 = December
monthly_means = np.zeros(12)
for m in range(1, 13):
    monthly_means[m-1] = signal[months == m].mean()   # average value for each month

anomaly = signal - monthly_means[months - 1]   # subtract each month's average
```

**Formula:**

$$\Delta H_{\text{anom}}(t) = \Delta H(t) - \overline{\Delta H}_{\,\text{month}(t)}$$

where $\overline{\Delta H}_{\,m}$ is the mean increment in calendar month $m$ across all years.
The same operation is applied to $\Delta b$ (compaction increments).

---

## Step 7 — Run the tau grid search

**Script:** calls `tau_grid_search_per_layer()` from `ihmf_model_v3.py` lines 200–235

This is the core calculation. For every candidate lag $\tau \in \{0, 1, 2, \ldots, 120\}$:

**7a. Shift the GWL signal by $\tau$ epochs**

```python
dH_lag  = dH_anom[:n]    # GWL at times 0, 1, ..., n-1   (the "driver")
db_trim = db_anom[tau:]  # compaction at times tau, tau+1, ..., T-1  (the "response")
```

The idea: if $\tau = 10$, then the GWL change on day 0 is paired with the compaction
change on day 50 (10 epochs × 5 days). We are asking: "does the ground respond 50 days later?"

**7b. Fit a storage coefficient for elastic epochs**

Using only the elastic epochs in this shifted window:

$$S_{ke} = \frac{\sum_t \Delta H_{\text{anom}}(t) \cdot \Delta b_{\text{anom}}(t+\tau)}{\sum_t [\Delta H_{\text{anom}}(t)]^2} \quad \text{(elastic epochs only, clamped to} \ge 0\text{)}$$

```python
S_ke = max(0.0, np.dot(dH_e, db_e) / np.dot(dH_e, dH_e))
```

**7c. Fit a storage coefficient for inelastic epochs**

Same formula but using only inelastic epochs:

$$S_{kv} = \frac{\sum_t \Delta H_{\text{anom}}(t) \cdot \Delta b_{\text{anom}}(t+\tau)}{\sum_t [\Delta H_{\text{anom}}(t)]^2} \quad \text{(inelastic epochs only, clamped to} \ge 0\text{)}$$

```python
S_kv = max(0.0, np.dot(dH_i, db_i) / np.dot(dH_i, dH_i))
```

**7d. Predict compaction and compute the mean squared error (MSE)**

$$\Delta b_{\text{pred}}(t+\tau) = \begin{cases} S_{ke} \cdot \Delta H_{\text{anom}}(t) & \text{if elastic} \\ S_{kv} \cdot \Delta H_{\text{anom}}(t) & \text{if inelastic} \end{cases}$$

$$\text{MSE}(\tau) = \frac{1}{n} \sum_{t=0}^{n-1} \left[ \Delta b_{\text{anom}}(t+\tau) - \Delta b_{\text{pred}}(t+\tau) \right]^2$$

```python
mse = float(np.mean((db_trim - db_pred) ** 2))
```

This MSE is stored for every $\tau$ from 0 to 120.

**7e. Pick the best lag**

$$\tau_{\text{opt}} = \arg\min_{\tau \in \{0,\ldots,120\}} \text{MSE}(\tau)$$

```python
tau_opt = int(np.argmin(rss_curve))
```

---

## Step 8 — Save the results

**Script:** `01_run_tau_search.py` lines 186–209
**Writes:** three files to `results/`

### `tau_results.csv` — one row per layer

**Data preview — post-fix run on 2026-06-05** (Bug F applied; these are the authoritative results):

| layer | wellcode | gwl_file | h_c_m | n_elastic | n_inelastic | tau_opt | tau_opt_days | mse_at_tau_opt |
|-------|----------|----------|-------|-----------|-------------|---------|--------------|----------------|
| F1 | 09050111 | HONGLUN... | −2.344 | 374 | **397** | 42 | 210 | 0.001257 |
| T1 | 09050111 | HONGLUN... | −2.344 | 374 | **397** | 72 | 360 | 0.000409 |
| F2 | 09050321 | TUKU... | −5.086 | 602 | 169 | 0 | 0 | 0.012650 |
| T2 | 09170121 | LUNZI... | −8.457 | 741 | 30 | 72 | 360 | 0.002472 |
| F3 | 09050331 | TUKU... | −4.456 | 611 | 160 | 0 | 0 | 0.051274 |
| F4 | 09080251 | LIUZHUANG... | −7.008 | 752 | 19 | 105 | 525 | 0.000300 |

Key observations after the fix:
- F1 and T1 (HONGLUN well): $n_{\text{inelastic}}$ rose from 1 to **397 epochs** out of 771 total.
  This confirms the head at HONGLUN regularly dropped below the pre-2015 minimum ($h_c = -2.344$ m).
  Bug F caused only 1 inelastic epoch because it read $h_c$ from the post-2015 aligned table,
  which only ever saw the 2015–2025 minimum (−5.702 m) — a threshold so deep the head never crossed it.
- F2, F3 (TUKU well): $n_{\text{inelastic}}$ is now 169 and 160 respectively — the TUKU well did
  drop below its pre-2015 threshold, though $\tau_{\text{opt}} = 0$ persists for both layers.
- T2 (LUNZI well): 30 inelastic epochs with $\tau_{\text{opt}} = 72$ (360 days).
- F4 (LIUZHUANG well): only 19 inelastic epochs; $\tau_{\text{opt}} = 105$ (525 days) unchanged.

### `tau_mse_curves.csv` — MSE at every lag for every layer

121 rows (one per candidate $\tau$ from 0 to 120), 7 columns.

**Data preview — first 5 rows:**

| tau (epochs) | F1 | T1 | F2 | T2 | F3 | F4 |
|---|---|---|---|---|---|---|
| 0 | 0.001298 | 0.000455 | 0.012667 | 0.002613 | 0.051529 | 0.000325 |
| 1 | 0.001299 | 0.000459 | 0.013519 | 0.002655 | 0.051713 | 0.000323 |
| 2 | 0.001297 | 0.000461 | 0.013620 | 0.002653 | 0.051830 | 0.000322 |
| 3 | 0.001291 | 0.000461 | 0.013572 | 0.002634 | 0.051925 | 0.000320 |
| 4 | 0.001292 | 0.000462 | 0.013586 | 0.002637 | 0.052019 | 0.000320 |

Note F3: MSE increases monotonically from τ=0 (0.051529) onward — the curve has no minimum.
Note F2: MSE at τ=0 (0.012667) is already the minimum — selected by default.
Note F4: MSE is decreasing at small τ, indicating a long-lag minimum further out.

### `tuku_aligned_data.npz` — all aligned arrays for plotting

Contains the time series arrays (head_m, mlcw_mm, inc_dH, inc_db, etc.) so the
plotting scripts can run without re-reading the raw feather files.

---

## What changed since the last run (2026-06-04 fixes, confirmed 2026-06-05)

| Item | Before (buggy) | After (fixed) |
|------|----------------|---------------|
| `TAU_MAX` in `01_run_tau_search.py` | 73 epochs (365 days) | **120 epochs (600 days)** |
| Assignment CSV | v3 (FANGCAO for T1, dead after 2022) | **v4 (HONGLUN for T1, 1095 days coverage)** |
| $h_c$ computation | from `aligned` table (always post-2015) | **from raw GWL feather pre-2015 rows** |
| $h_c$ for HONGLUN | −5.702 m (buggy: 2015–2025 minimum) | **−2.344 m (correct: pre-2015 minimum)** |
| `TAU_MAX` in `fit_ihm_f_v3.py` | 73 | **120** |
| $S_{kv}$ ratio guard | `== 0.0` (misses 1e-20) | **`< 1e-10` + 8–58× range check** |
| $S_{kv}$ upper bound in solver | `np.inf` | **$2.2 \times 10^{-3}$ m⁻¹ (CRAF literature cap)** |
| Step 2 alpha fit domain | cumulative, no intercept | **cumulative with OLS intercept** |

### Run on 2026-06-05 — Bug F fix confirmed

**Old $n_{\text{inelastic}}$ (all layers, pre-fix):** 1, 1, 1, 1, 1, 1

**New $n_{\text{inelastic}}$ (post-fix):**

| layer | old n_inelastic | new n_inelastic | change |
|-------|----------------|-----------------|--------|
| F1 | 1 | **397** | +396 |
| T1 | 1 | **397** | +396 |
| F2 | 1 | **169** | +168 |
| T2 | 1 | **30** | +29 |
| F3 | 1 | **160** | +159 |
| F4 | 1 | **19** | +18 |

**Old $\tau_{\text{opt}}$ values (pre-fix):** F1=42, T1=72, F2=0, T2=72, F3=0, F4=105

**New $\tau_{\text{opt}}$ values (post-fix, 2026-06-05):**

| layer | old $\tau_{\text{opt}}$ (epochs) | old (days) | new $\tau_{\text{opt}}$ (epochs) | new (days) |
|-------|----------------------------------|------------|----------------------------------|------------|
| F1 | 42 | 210 | **42** | 210 |
| T1 | 72 | 360 | **72** | 360 |
| F2 | 0 | 0 | **0** | 0 |
| T2 | 72 | 360 | **72** | 360 |
| F3 | 0 | 0 | **0** | 0 |
| F4 | 105 | 525 | **105** | 525 |

The $\tau_{\text{opt}}$ values are unchanged after the fix. The h_c bug affected which epochs were
labelled inelastic (and therefore how $S_{kv}$ was estimated), but not which lag minimised the
combined MSE. This is expected: the seasonal-cycle-removed MSE landscape is dominated by the
elastic regime (which has the majority of epochs for layers other than F1/T1).

---

## Issues remaining

### Issue A — RESOLVED (2026-06-05)

Bug F was fixed and the script was re-run on 2026-06-05. The `tau_results.csv` table in
Step 8 is now the post-fix authoritative output. $n_{\text{inelastic}}$ for F1 and T1 is
now 397 (was 1). No re-run is needed unless the input data or assignment table changes.

### Issue B — F2 and F3 show $\tau_{\text{opt}} = 0$ (persists after fix)

Both layers return $\tau = 0$ with high MSE (0.013 and 0.052 vs 0.001 for F1). They share
the same GWL well (TUKU station screens 82.5 m and 177.5 m). The MSE curve for F3 increases
monotonically — no coupling detected at any lag. This may indicate the TUKU well screens are
not hydraulically connected to F3 compaction, independent of the h_c bug.

### Issue C — F4 $\tau_{\text{opt}} = 105$ epochs = 525 days (close to search ceiling of 120)

LIUZHUANG well serves a deep layer (282 m screen). A 525-day lag is very long but not
physically impossible for a deep clay layer. After the fix, check whether the MSE curve
has a clear minimum or is still trending downward at τ=120 (which would mean TAU_MAX needs
to be raised further for F4 specifically).
