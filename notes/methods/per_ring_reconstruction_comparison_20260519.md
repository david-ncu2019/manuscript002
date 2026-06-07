# Per-Ring Reconstruction Comparison: Harmonic vs. Wet/Dry
**Date:** 2026-05-19  
**Script:** `compare_reconstructions_per_ring.py`  
**Purpose:** Validate harmonic decomposition and wet/dry seasonal splitting at the individual depth-ring level

---

## What Was Done

A new script (`compare_reconstructions_per_ring.py`) was written to compare three time-series predictions at each of the 60 depth levels, for all 39 MLCW stations:

1. **Observed MLCW** (black solid line) — ground truth compaction time series
2. **Scalar baseline** (blue dashed line) — simple ratio reconstruction: `Ŷ = f̄_k × InSAR`
3. **New reconstruction** — either harmonic or wet/dry seasonal split

**Output:** 6 figures per station (3 for harmonic, 3 for wet/dry), written to `direct_ratio_MLCW_InSAR/{STATION}/`

---

## Figure Layout

Each figure shows **20 subplots** (5 columns $\times$ 4 rows), each subplot representing one depth level.

**Figure 1:** Depths 0–95 m (depth indices 0–19)  
**Figure 2:** Depths 100–195 m (depth indices 20–39)  
**Figure 3:** Depths 200–295 m (depth indices 40–59)

**Filename pattern:**
```
{STATION}_harmonic_per_ring_fig1/2/3.png
{STATION}_wetdry_per_ring_fig1/2/3.png
```

---

## Subplot Annotation

Each subplot title contains two pieces of information:

| Element | Example | Meaning |
|---------|---------|---------|
| Depth in metres | `15m` | The depth level in this subplot |
| RMSE improvement | `+0.4%` | `(RMSE_scalar − RMSE_new) / RMSE_scalar × 100%` |

**Colour coding:**
- Green text = improvement (new method wins, $\Delta$% > 0)
- Red text = degradation (new method loses, $\Delta$% < 0)

---

## Harmonic Decomposition Figures

**Filename:** `{STATION}_harmonic_per_ring_fig{1,2,3}.png`

**Three lines per subplot:**
1. Black solid — observed MLCW compaction `Y(i,k)`
2. Blue dashed — scalar baseline `Ŷ_scalar = f̄_k × InSAR(i)`
3. Orange solid — harmonic reconstruction `Ŷ_harmonic = f_trend_k × x_trend(i) + f_seas_k × x_seas(i)`

**Data sources:**
- `{STATION}_optionB_trend.csv` → `f_trend_med` per depth
- `{STATION}_optionB_seas.csv` → `f_seas_med` per depth
- `{STATION}_direct_ratio_stats.csv` → `f_median` (scalar baseline)

**Reconstruction formula:**
```
x_trend(i)    = ±182-day centred moving average of InSAR(i)
x_seas(i)     = InSAR(i) − x_trend(i)
Ŷ_harmonic    = f_trend_k × x_trend(i) + f_seas_k × x_seas(i)
```

**Interpretation:**
- If harmonic line (orange) closely follows observed MLCW (black), the split is capturing depth-dependent harmonic response.
- If improvement (green) is widespread and >1%, harmonic decomposition is beneficial at this station.
- If degradation (red) is widespread, the harmonic split may be overfitting or misidentifying the seasonal signal.

---

## Wet/Dry Seasonal Split Figures

**Filename:** `{STATION}_wetdry_per_ring_fig{1,2,3}.png`

**Three lines per subplot:**
1. Black solid — observed MLCW compaction `Y(i,k)`
2. Blue dashed — scalar baseline `Ŷ_scalar = f̄_k × InSAR(i)`
3. Teal solid — wet/dry reconstruction `Ŷ_wetdry = f_split_k(month) × InSAR(i)`

**Data sources:**
- `{STATION}/wetdry_diagnostic/{STATION}_wetdry_profiles.csv` → `f_wet`, `f_dry` per depth
- `{STATION}_direct_ratio_stats.csv` → `f_median` (scalar baseline)

**Reconstruction formula:**
```
Wet season (May–Oct):    f_split_k = f_wet_k
Dry season (Nov–Apr):    f_split_k = f_dry_k
Ŷ_wetdry                 = f_split_k × InSAR(i)
```

**Interpretation:**
- If wet/dry line (teal) oscillates between two regimes in phase with the calendar, the seasonal split is working.
- Large divergence between wet and dry seasons suggests compaction behaviour differs by water table position.
- If improvement (green) occurs in the wet or dry season block preferentially, the method is capturing regime-dependent response.
- If little divergence between wet/dry line and scalar baseline, the seasonal signal is weak and the split provides little benefit.

---

## Expected Cross-Station Patterns

From the prior ablation studies (`harmonic_allstations_summary.json` and `wetdry_allstations_summary.json`):

| Method | Recommended Stations | Median Improvement | Failure Rate |
|--------|---------------------|-------------------|--------------|
| Harmonic decomposition | 14/39 (36%) | +0.4 to +0.7% | 64% (25 stations with $\Delta$% $\le$ 0) |
| Wet/dry seasonal split | 5/39 (13%) | +0.3 to +0.5% | 87% (34 stations with $\Delta$% $\le$ 0) |

**Key observation:** Both methods have modest ceilings. Static reweighting (harmonic and wet/dry) have been exhausted at ~1% RMSE improvement. Widespread degradation at many stations suggests:
1. The scalar ratio `f̄_k` is robust and difficult to improve with static reweighting.
2. Deeper failure modes (autoregressive memory, phase lag, state-space dynamics) may be necessary for significant improvement.

---

## How to Explore the Figures

1. **Station-level**: Open a per-ring figure for a station of interest (e.g., TUKU, JIUN, BORI).
2. **Visual scan**: Look for where the orange/teal line pulls away from the dashed blue line.
3. **RMSE color**: Are improvements (green) clustered at certain depths or scattered?
4. **Regime signature**: For wet/dry plots, do the line colors show seasonal phase locking?

---

## Files Modified/Created

| File | Status | Count | Total Size |
|------|--------|-------|-----------|
| `compare_reconstructions_per_ring.py` | **NEW** | 1 script | — |
| `{STATION}_harmonic_per_ring_fig{1,2,3}.png` | **NEW** ✓ Complete | 117 files (39 stations $\times$ 3) | ~60 MB |
| `{STATION}_wetdry_per_ring_fig{1,2,3}.png` | **NEW** ✓ Complete | 117 files (39 stations $\times$ 3) | ~60 MB |

**Total output:** 39 stations $\times$ 6 figures/station = **234 PNG files**, **120 MB total**, **0.51 MB per file**

**Status:** ✓ All 39 stations processed successfully, batch completed 2026-05-19

---

## Running the Script

**Full batch (all 39 stations):**
```powershell
cd "D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2"
python compare_reconstructions_per_ring.py
```

**Single station (test):**
```powershell
python compare_reconstructions_per_ring.py --station TUKU
```

**Expected runtime:** ~5–10 minutes for full batch (InSAR feather load + per-station figure generation)

---

## Notes

- **Harmonic figures skipped** if `{STATION}_optionB_trend.csv` or `{STATION}_optionB_seas.csv` missing (station was not included in harmonic batch run).
- **Wet/dry figures skipped** if `{STATION}/wetdry_diagnostic/{STATION}_wetdry_profiles.csv` missing (station was not included in wet/dry batch run).
- **Script resilience**: If one station fails, processing continues to the next station; failed stations are reported to stdout.
- **Matplotlib backend:** Uses 'Agg' (non-interactive) for headless batch processing on Windows.

---

## Relationship to Prior Work

**Existing per-station validation plots** (`{STATION}_ts_fig1/2/3.png` in `validation/`):
- Created by `validate_all_stations.py`
- Show observed MLCW vs. scalar baseline only (2 lines per subplot)
- Are the primary validation metric for the direct-ratio anchor model

**NEW per-ring comparison plots** (this script):
- Show observed MLCW vs. scalar baseline vs. harmonic/wet/dry reconstruction (3 lines per subplot)
- Are diagnostic tools for evaluating whether seasonal decomposition methods improve prediction at individual depth levels
- Do NOT replace the validation plots; they complement them by adding visual clarity at the ring level

---

## Summary

The script provides a visual way to inspect whether harmonic decomposition or wet/dry seasonal splitting actually improve predictions at each individual depth, rather than just reporting aggregate statistics. The RMSE improvement percentage per depth allows quick identification of where each method wins or loses, and the three-line overlay makes it immediately clear whether the reconstruction is capturing the observed signal better than the scalar baseline.
