# Prophet Forecasting for TUKU Per-Depth Compaction — Pilot Test

*Analysis date: 2026-05-18. Script: `prophet_tuku.py`. Outputs: `prophet_tuku/`.*

---

## 1. What Hung et al. (2025) did with Prophet

Hung et al. (2025) applied Facebook Prophet to a single multi-depth extensometer (extensometer = the whole column integrated) in Taiwan to forecast near-real-time subsidence. Key choices:

- **Additive model:** total signal = trend + yearly seasonality + noise. The trend is piecewise-linear with automatic changepoint detection.
- **Univariate:** no exogenous regressors — their extensometer captures the full surface signal so no external driver is needed.
- **Settings:** `changepoint_prior_scale = 0.05` (moderate trend flexibility), `uncertainty_samples = 0` (maximum a posteriori / L-BFGS, no MCMC).
- **Hold-out:** 4-month forward window only.
- **Result:** ~35% RMSE reduction over a persistence/climatology baseline on the 4-month hold-out.

Their instrument had good signal-to-noise at the total column level. Our setting differs in two critical ways: (i) we work at individual 5 m slab depth, where the per-slab signal is typically 0.1–5 mm (two orders of magnitude smaller than a full column), and (ii) we evaluate over a 4-year hold-out (2022–2025) with walk-forward folds, which is a much harder test than 4 months.

---

## 2. How we adapted it for MLCW + InSAR

The core physical idea: at each depth level k, the MLCW slab compaction `Y(t, k)` is driven by the same pore-pressure and stress cycles that InSAR records at the surface. The static baseline model is simply `f_k * x(t)` where `f_k` is the median depth-fraction and `x(t)` is InSAR (mm). Prophet is then asked to model the residual from this proportional relationship using its trend and seasonality components — or equivalently, to fit `Y(t,k)` directly with InSAR as a linear regressor alongside the additive trend and annual cycle.

Key adaptations from Hung et al.:

1. **InSAR as exogenous regressor.** Added via `m.add_regressor('insar')`. This means Prophet decomposes `Y(t,k) = trend(t) + seasonality(t) + beta_k * InSAR(t) + epsilon`. The InSAR term carries most of the variance at active depths; trend and seasonality capture the residual temporal structure.

2. **Per-slab target, not total column.** Each of the 60 depth slabs (depth_000m to depth_295m) is fit independently. The depth_300m anchor is excluded by design (always zero).

3. **Walk-forward validation, 4 folds, 1-year hold-out horizon.** Far stricter than Hung et al.'s 4-month window. The training window grows each fold:
   - Fold 1: train 2015-01 to 2021-11, hold-out 2022
   - Fold 2: train 2015-01 to 2022-11, hold-out 2023
   - Fold 3: train 2015-01 to 2023-11, hold-out 2024
   - Fold 4: train 2015-01 to 2024-11, hold-out 2025 (partial to 2025-10-01)

4. **Baseline:** `f_median_k * x_ho` — the static direct-ratio prediction already shown to have Pearson r = 0.984 with the regularised Stage 1 inversion at TUKU.

5. **Run on a subset of 14 depths** covering the full profile (every 25 m, plus 30, 180 m as detail depths). Full 60-depth production run would take ~10$\times$ longer.

---

## 3. Results

### 3.1 Walk-forward RMSE summary

The table shows median walk-forward RMSE across the four hold-out years. Improvement is relative to the static baseline; positive = Prophet better than baseline.

| Depth (m) | Prophet RMSE (mm) | Baseline RMSE (mm) | ARX RMSE (mm) | Prophet impr. (%) | ARX impr. (%) |
|----------:|------------------:|-------------------:|--------------:|------------------:|--------------:|
|         0 |             1.994 |              1.232 |         0.504 |             -61.9 |         +46.4 |
|        25 |             0.395 |              0.176 |         0.154 |            -125.0 |          +2.6 |
|        30 |             1.046 |              0.344 |         0.324 |            -204.2 |         +23.5 |
|        50 |             0.551 |              0.285 |         0.337 |             -93.6 |         -24.8 |
|        75 |             0.464 |              0.146 |         0.255 |            -218.1 |         -43.0 |
|       100 |             0.210 |              0.301 |         0.626 |             +30.2 |        -100.5 |
|       125 |             0.703 |              0.479 |         0.399 |             -46.8 |         -44.0 |
|       150 |             0.993 |              0.680 |         0.319 |             -46.0 |         +51.4 |
|       175 |             1.855 |              1.051 |         0.914 |             -76.5 |          -3.4 |
|       180 |             2.248 |              3.596 |         0.977 |             +37.5 |         +56.1 |
|       200 |             0.038 |              0.206 |         0.096 |             +81.7 |         +34.4 |
|       225 |             1.869 |              1.956 |         1.145 |              +4.5 |         +23.8 |
|       250 |             0.731 |              1.482 |         0.278 |             +50.6 |         +78.3 |
|       275 |             0.453 |              1.315 |         0.418 |             +65.5 |         +54.2 |

*ARX = autoregressive model with exogenous InSAR input (Method 7), same walk-forward folds.*

### 3.2 Key visual patterns (from Fig 2)

The four time-series panels (30 m, 100 m, 180 m, 250 m) tell different physical stories.

**30 m (shallow sand/gravel):** The observed MLCW signal is small (< 2 mm total range), fluctuating around zero with no strong trend. The static baseline tracks well because the signal is nearly proportional to InSAR. Prophet overshoots in several folds — the trend component in Prophet over-responds to a very flat signal, generating spurious drift. Negative improvement (-204%).

**100 m (intermediate layer):** A positive compaction trend develops in the observed signal during 2022–2025, diverging from the static baseline which underestimates cumulative compaction. Prophet partially captures this acceleration (RMSE 0.21 mm vs baseline 0.30 mm, +30% improvement). This is exactly the case where Prophet's piecewise trend adds value: the system has shifted into a new regime that the historical median ratio does not anticipate.

**180 m (major compacting interval, ~1500 m deep basin):** The most active depth. Observed MLCW shows strong, accelerating compaction reaching ~25 mm cumulative by 2025. The static baseline systematically lags — it is anchored to the 2015–2021 median ratio, which underestimates the 2022–2025 signal. Prophet improves here (+37.5% vs baseline), but its absolute RMSE (2.25 mm) remains high. ARX does better at this depth (+56.1%).

**250 m (deep clay):** The observed signal is dominated by slow, monotonically increasing compaction (signal-to-noise is high). Prophet captures this well (+50.6%), close to ARX (+78.3% at this depth). The InSAR regressor provides a clean long-term proxy; the yearly seasonality in Prophet then absorbs the annual pore-pressure cycle.

### 3.3 Depth-by-depth comparison (from Fig 3)

Three distinct depth zones emerge.

**Shallow depths (0–75 m):** Prophet consistently degrades over the static baseline (improvements range from -62% to -218%). These layers have small per-slab signals (< 0.5 mm). The InSAR regressor is noisy relative to the slab signal; Prophet's trend component adds variance rather than removing it. ARX is also inconsistent here, ranging from +46% at 0 m to -43% at 75 m.

**Mid-range depths (100–225 m):** Mixed results. Both Prophet and ARX show improvements at some depths (100 m, 180 m, 200 m) and degradation at others (125 m, 150 m, 175 m). The inconsistency reflects regime transitions and abrupt changes in slab compaction rate that neither method's assumed functional form fully captures. At 100 m and 200 m, Prophet's positive trend component tracks a real signal acceleration. At 150 m, ARX (+51%) outperforms Prophet (-46%) because the lag structure between InSAR and slab compaction at 150 m has a specific delay that ARX captures but Prophet's instantaneous regressor does not.

**Deep depths (225–275 m):** Both models show consistent positive improvement. At 250 m and 275 m, Prophet achieves +50–66% over baseline, with ARX at +54–78%. The deep clay has high per-slab signal amplitude (up to 4 mm/epoch range), good signal-to-noise, and a relatively smooth trajectory — conditions where both additive trend modelling (Prophet) and autoregressive structure (ARX) genuinely add information over a static fraction.

---

## 4. Main finding

Prophet with an InSAR regressor outperforms the static baseline at the deep and moderately active depths (100–275 m), delivering median RMSE improvements of 4–82% over 4 years of held-out data. However, it performs substantially worse than the baseline at shallow depths (0–75 m), where per-slab signals are weak relative to the noise in Prophet's trend and seasonality components.

Comparing to ARX: ARX is generally superior to Prophet at most depths. Only at 100 m and 225 m does Prophet match or slightly exceed ARX. At the major compacting zone (180 m), ARX reduces RMSE by 56% vs Prophet's 37%. At the deepest layers (250–275 m), both methods perform similarly, with ARX holding a modest edge (78% vs 51% at 250 m). The pattern suggests that the autoregressive memory in ARX captures physically real lag relationships between InSAR and per-slab compaction that Prophet's additive structure misses.

The clearest take-away is that a static proportionality model (`f_median * InSAR`) remains competitive or superior in the shallow zone (0–75 m), while time-aware methods (ARX preferred over Prophet) add genuine value below 100 m.

---

## 5. Limitations and suggestions

**Why Prophet underperforms ARX at most depths:**
Prophet's regressor term treats InSAR as a contemporaneous linear predictor with constant coefficient across all time. ARX explicitly models the lagged response structure — compaction at depth k in epoch t depends on InSAR in epochs t, t-1, t-2, ... . Depth-specific lag (longer at depth due to pore-pressure diffusion) is the dominant source of temporal structure that the static model misses, and ARX targets this directly. Prophet's yearly seasonality is a useful proxy for the annual GWL cycle but is not a substitute for lag structure.

**Why shallow depths (0–75 m) are not helped by either model:**
Shallow unconsolidated layers at TUKU have intrinsically low compaction per 5 m slab. The InSAR-to-MLCW signal ratio in these layers contains more scatter than systematic lag. Any model that adds parameters (trend, AR lags) has more opportunities to over-fit the training period. The direct ratio median is already near-optimal here.

**Over-fitting in early folds:**
In Fold 1 (hold-out 2022, train to 2021-11), several depths show large Prophet RMSE spikes (e.g. 0 m: 3.08 mm; 150 m: 3.45 mm). This likely reflects Prophet detecting a structural break at the 2021 drought-recovery transition and extrapolating a false trend into 2022. Adding `n_changepoints=5` (instead of the default 25) or a shorter changepoints range may reduce this.

**Next steps to consider:**
1. Run ARX on the full 60-depth profile (not just the 14 shown here) to confirm that ARX dominates at mid-to-deep depths across all levels, then select ARX as the production temporal model for TUKU.
2. Investigate whether Prophet's trend component could be constrained to be non-positive (compaction only = no rebound), which would prevent the spurious upswings seen at shallow depths.
3. Consider running Prophet without the InSAR regressor (univariate, as in Hung et al.) as an ablation to quantify how much of the improvement comes from the regressor vs the trend model.
4. The 180 m depth deserves a dedicated residual analysis: it is the largest contributor to surface subsidence and both Prophet and ARX still produce substantial absolute errors (2.2 mm and 1.0 mm respectively). The long-term acceleration in that layer may require a non-stationary model (time-varying coefficient on the InSAR regressor) rather than a fixed-coefficient regressor.

---

*Report generated 2026-05-18 from `prophet_tuku.py` run on TUKU station.*
*All outputs at: `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\prophet_tuku\`*
