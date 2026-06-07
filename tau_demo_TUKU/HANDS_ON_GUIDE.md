# tau_demo_TUKU — Hands-on Calculation Guide

**Date:** 2026-06-05
**Purpose:** Step-by-step guide to run the hydraulic lag (τ) experiment at TUKU station yourself. Each section tells you: what data goes in, what calculation happens, what comes out, and how to verify the result.

---

## Prerequisites

```powershell
# Clean environment
$env:PYTHONPATH=""
conda activate fafalab

# Working directory
cd /mnt/hgfs/1000_SCRIPTS/004_Project003/20260427_InSAR_MLCW_v2/tau_demo_TUKU
```

---

## Step 1 — Inspect the input data BEFORE running anything

### 1a. MLCW compaction data (what you are trying to predict)

**File:** `data/TUKU_reconst_grouped_cleaned.csv`
- **1,572 rows** × 7 columns: `datetime, F1, T1, F2, T2, F3, F4`
- **Units:** mm, cumulative from reference date (negative = compaction)
- **Cadence:** ~5-day intervals from 2003-12-06 to ~2025
- **Cleaned:** One spike fixed in F3 on 2021-12-06 (incremental delta went from +4.61 mm → +0.047 mm after cleaning)
- **Why this file:** The cleaned version removes one unrealistic spike. Script 01 uses this.

```python
import pandas as pd
df = pd.read_csv("data/TUKU_reconst_grouped_cleaned.csv")
print(df.shape)        # (1572, 7)
print(df.head())
print(df.describe())   # Check min/max — all negative for F1-F4, T1, T2
```

**Quick sanity check:** F3 min should be around −380 mm (NOT −550 mm or worse). If you see extreme negatives, you're reading the uncleaned file.

### 1b. GWL layer assignment (which well monitors which layer)

**File:** `data/gwl_to_mlcw_layer_assignment_v4.csv`
- **195 rows** (all stations) × 17 columns
- **For TUKU station:** 6 rows — one per layer
- **Key columns:** `station, layer, assigned_wellcode, feather_file, assignment_method, dist_to_gwl_m`

```python
import pandas as pd
assign = pd.read_csv("data/gwl_to_mlcw_layer_assignment_v4.csv")
tuku = assign[assign["station"] == "TUKU"]
print(tuku[["layer", "assigned_wellcode", "feather_file", "assignment_method", "dist_to_gwl_m"]])
```

**Expected TUKU assignments (v4):**

| Layer | Well | GWL file | Method | Distance |
|-------|------|----------|--------|----------|
| F1 | HONGLUN (09050111) | HONGLUN_gwl_timeseries.feather | DIRECT_MATCH | ~0 m |
| T1 | HONGLUN (09050121) | HONGLUN_gwl_timeseries.feather | DIRECT_MATCH | ~0 m |
| F2 | TUKU (09050321) | TUKU_gwl_timeseries.feather | DIRECT_MATCH | ~0 m |
| T2 | LUNZI (09170111) | LUNZI_gwl_timeseries.feather | NEAREST_FALLBACK | ~5 km |
| F3 | TUKU (09050331) | TUKU_gwl_timeseries.feather | DIRECT_MATCH | ~0 m |
| F4 | LIUZHUANG (09080211) | LIUZHUANG_gwl_timeseries.feather | NEAREST_FALLBACK | ~5 km |

**Red flag:** T2 and F4 use NEAREST_FALLBACK wells ~5 km away. F2 and F3 use TUKU wells with ~48% null data. This will affect result quality.

### 1c. GWL head timeseries (the driver — piezometric head)

**Four feather files in `data/`:**

| File | Wells | Rows | Null rate | Quality |
|------|-------|------|-----------|---------|
| `HONGLUN_gwl_timeseries.feather` | 09050111, 09050121 | 9,497 | ~0.01% | Excellent |
| `TUKU_gwl_timeseries.feather` | 09050321, 09050331, 09050341 | 9,497 | **~48%** | Poor — half the record is missing |
| `LIUZHUANG_gwl_timeseries.feather` | 09080211–09080251 (5 wells) | 9,497 | ~0.02% | Excellent |
| `LUNZI_gwl_timeseries.feather` | 09170111–09170122 (4 wells) | 9,497 | 5–77% | Mixed — check which wellcode is assigned |

```python
import pandas as pd

# Check TUKU well (assigned to F2, F3) — the problematic one
tuku_gwl = pd.read_feather("data/TUKU_gwl_timeseries.feather")
print(tuku_gwl.columns.tolist())  # ['datetime', '09050321', '09050331', '09050341']
for col in ['09050321', '09050331']:
    nulls = tuku_gwl[col].isna().sum()
    print(f"{col}: {nulls}/{len(tuku_gwl)} nulls ({100*nulls/len(tuku_gwl):.1f}%)")
```

**Interpretation:** F2 (well 09050321) and F3 (well 09050331) have ~4,600 null values out of 9,497 daily records. When aligned to the ~1,572 MLCW epochs, fewer nulls will coincide — but the 48% daily null rate means the well was non-operational for roughly half the study period, which reduces the number of valid epochs for tau fitting.

---

## Step 2 — Run the core tau search (`01_run_tau_search.py`)

### What this script does, in physical terms:

For each of TUKU's 6 layers (F1, T1, F2, T2, F3, F4):

1. **Zero-reference both signals** to REF_DATE = 2015-01-16 — the InSAR reference epoch
2. **Compute preconsolidation head (h_c):** minimum raw GWL head *before* 2015-01-16, from the un-zero-referenced feather file. This is the head threshold below which compaction switches from elastic to inelastic.
3. **Align GWL to MLCW dates** using nearest-neighbor merge (`merge_asof`, tolerance = 3 days)
4. **Take first differences** of both signals → incremental head change ΔH and incremental compaction Δb
5. **Classify each epoch** as elastic (head > h_c) or inelastic (head ≤ h_c)
6. **Remove seasonal cycle** — subtract monthly climatology from both signals
7. **Grid-search τ from 0 to 120 epochs** (0 to 600 days): for each candidate lag, lag the ΔH by τ epochs, then fit S_ke (slope through elastic points) and S_kv (slope through inelastic points) via scalar OLS. Pick τ with minimum MSE.
8. **Write results** to `results/tau_results.csv` and `results/tau_mse_curves.csv`

### Run it:

```powershell
$env:PYTHONPATH=""
conda run -n fafalab python 01_run_tau_search.py
```

### What you should see:

```
Layer F1: τ_opt=42 epochs (210 days), h_c=-2.344, n_elastic=374, n_inelastic=397
Layer T1: τ_opt=72 epochs (360 days), h_c=-2.344, n_elastic=374, n_inelastic=397
Layer F2: τ_opt=0 epochs (0 days),    h_c=-5.086, n_elastic=602, n_inelastic=169
Layer T2: τ_opt=72 epochs (360 days), h_c=-8.457, n_elastic=741, n_inelastic=30
Layer F3: τ_opt=0 epochs (0 days),    h_c=-4.456, n_elastic=611, n_inelastic=160
Layer F4: τ_opt=105 epochs (525 days),h_c=-7.008, n_elastic=752, n_inelastic=19
```

### Verify the output:

```python
import pandas as pd
tau_results = pd.read_csv("results/tau_results.csv")
print(tau_results[["layer", "tau_opt", "tau_opt_days", "h_c_m", "n_elastic", "n_inelastic", "mse_at_tau_opt"]])
```

**Physical gate checks on τ results:**

| Check | How to verify | Red flag if |
|-------|--------------|-------------|
| n_inelastic ≥ 10 | Look at `n_inelastic` column | < 10 means S_kv is unreliable |
| τ not at boundary | τ_opt < 120 (not at ceiling) | τ=120 means extend search |
| h_c is pre-2015 minimum | Should be more negative than recent head values | If h_c ≈ 2022 drought low, Bug F is unfixed |
| h_c for F1=T1 (same well) | Both should have same h_c from HONGLUN well | Different values → assignment bug |

**Know what's suspicious:**
- **F2, F3: τ=0** — no lag detected. The TUKU well may not be hydraulically connected to the compacting layer, or the signal is too weak at 5-day resolution.
- **F4: τ=525d** — close to the 600-day ceiling. A longer search might find a better lag.
- **T2: n_inelastic=30** — barely above the 10-epoch threshold. S_kv estimate has high uncertainty.
- **F2, F3: TUKU well has 48% nulls** — fewer valid points than other layers.

---

## Step 3 — Evaluate reconstruction quality (`03_reconstruct_and_evaluate.py`)

### What this script does:

Using the τ_opt found in Step 2, reconstructs the full compaction timeseries and compares it to observed MLCW:

1. Lag ΔH by τ_opt epochs
2. Fit S_ke and S_kv at τ_opt (OLS through origin for each regime)
3. Predict incremental compaction: Δb̂ = S_ke × ΔH_lagged for elastic, S_kv × ΔH_lagged for inelastic
4. Cumulatively sum to get cumulative predicted compaction
5. Compute fit metrics: R², RMSE, Pearson r, bias

### Run it:

```powershell
conda run -n fafalab python 03_reconstruct_and_evaluate.py
```

### Verify the output:

```python
import pandas as pd
metrics = pd.read_csv("results/reconstruction_metrics.csv")
print(metrics[["layer", "S_ke", "S_kv", "R2", "RMSE", "pearson_r", "bias"]])
```

**Physical gate checks on reconstruction:**

| Check | Expected | Red flag if |
|-------|----------|-------------|
| S_ke > 0 | All layers | Negative → layer rejected |
| S_kv > 0 | All layers | Negative → layer rejected |
| S_kv > S_ke | All layers with both regimes | S_kv < S_ke → regime distinction not detected |
| R² > 0 | All layers | Negative → model worse than mean |
| Pearson r > 0 | All layers | Negative → anti-correlated prediction |

---

## Step 4 — Visualize the results (`05_plot_results.py`)

### What this script does:

Generates 9 publication-quality figures from the tau search results — no new calculations.

### Run it:

```powershell
conda run -n fafalab python 05_plot_results.py
```

### What each figure tells you (open `plots/results/`):

| Figure | What to look for |
|--------|-----------------|
| `mse_curves_all_layers.png` | MSE vs τ — should have a clear minimum. Flat curve = no coupling. |
| `gwl_head_regime.png` | Blue=elastic, red=inelastic. Red points should be below h_c line. |
| `cumulative_mlcw.png` | Steady negative trend = ongoing compaction. Flat = stable. |
| `regime_summary_bar.png` | F1/T1 should have many inelastic epochs (h_c is shallow). F4 should be mostly elastic (deep h_c). |
| `hc_comparison.png` | h_c should vary by layer. F1/T1 share HONGLUN h_c. |
| `reconstruction/reconstruction_F2.png` | Check if τ=0 prediction tracks observed compaction. If poor → well-screen mismatch. |

---

## Step 5 — Cross-check: compare tau results against the detrended method

Script `05_detrended_reconstruction.py` is an **alternative approach**: it detrends the cumulative signals (removes linear trend + annual harmonic) BEFORE differencing, then runs the same tau search. This tests whether the seasonal cycle is leaking into the tau estimate.

**Note:** Script 05 has been updated to use v4 assignments, cleaned MLCW, and TAU_MAX=120 (2026-06-06). Scripts 06 and 07 were also updated similarly. Run directly:

```powershell
conda run -n fafalab python 05_detrended_reconstruction.py
```

Compare the τ_opt values between detrended and non-detrended approaches. If they differ by >10 epochs (>50 days), the seasonal cycle is influencing the lag estimate — the detrended version is more reliable.

---

## Summary: what to trust, what to question

### Trust:
- **F1 (τ=210d), T1 (τ=360d):** HONGLUN well has excellent data. n_inelastic=397 is well above the 10-epoch threshold. Both layers share the same h_c (physically consistent).
- **T2 (τ=360d):** n_inelastic=30 — marginal but acceptable. LUNZI well has decent coverage for the assigned wellcode.
- **F4 (τ=525d):** LIUZHUANG well has excellent data. τ is close to the ceiling — consider extending TAU_MAX to 150 epochs (750 days) for F4 specifically.

### Question:
- **F2, F3 (τ=0):** τ=0 means "no detectable lag at 5-day resolution." This does NOT mean the layer compacts instantly — it means the TUKU well's head signal and the MLCW compaction signal are in phase at the 5-day sampling interval, OR the well is screened at a depth that does not hydraulically connect to the compacting aquitard. Check the well screen depth vs. the layer depth range.
- **TUKU well 48% nulls:** F2/F3 regression uses ~52% of the epochs that other layers use. RMSE and R² will be noisier for these layers.

### Before proceeding to IHM-F v3 pilot:
1. Confirm τ results are stable (re-run Step 2)
2. Check F2/F3 screen depth vs. compacting layer depth
3. Consider whether a different proxy well within 10 km has better data coverage for F2/F3
4. Verify h_c values are computed from pre-2015 GWL data (Bug F fixed)

---

## Quick reference: file roles

| File | Role | Used by script |
|------|------|---------------|
| `data/TUKU_reconst_grouped_cleaned.csv` | MLCW compaction (target) | 01, 03, 05 |
| `data/gwl_to_mlcw_layer_assignment_v4.csv` | Which well → which layer | 01 |
| `data/*_gwl_timeseries.feather` | Daily piezometric head (driver) | 01 |
| `results/tau_results.csv` | Optimal τ per layer | 02, 03, 04, 05 |
| `results/tau_mse_curves.csv` | MSE at every τ 0..120 | 02, 05 |
| `results/tuku_aligned_data.npz` | All aligned arrays (72 arrays) | 02, 03, 04, 05 |
| `results/reconstruction_metrics.csv` | Fit quality per layer | — (final output) |
