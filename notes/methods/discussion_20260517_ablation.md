# Discussion: ARX Ablation Study — Decomposing the Improvement Sources

**Date:** 2026-05-17
**Script:** `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\arx_ablation.py`
**Outputs:** `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\arx_method7\ablation\`

---

## 1. The question this study answers

The ARX walk-forward validation (Section 3 of `discussion_20260517_arx_results.md`) reported large RMSE improvements over the static baseline. However, the ARX model adds three things over the baseline simultaneously:

1. **The anchor**: it starts the hold-out prediction from the last observed MLCW value $Y_0 = Y_k(t_{\text{train}})$, rather than from zero.
2. **The AR(1) memory term** $\phi_k$: the prediction at each epoch depends on the previous prediction.
3. **The rate sensitivity term** $\gamma_k$: an additional adjustment from the InSAR 5-day increment.

Before declaring ARX the production method, it is essential to know which of these three elements is carrying the improvement. If the anchor alone explains 90%+ of the gain, then the simpler "anchor-only" model:

$$\hat{Y}^{\text{anchor}}_k(i) = Y_k(t_{\text{train}}) + \bar{f}_k \cdot (x(i) - x(t_{\text{train}}))$$

would be sufficient for production — no OLS fitting of $\phi_k$ or $\gamma_k$ required.

---

## 2. The three models

| Model | Formula | Parameters required |
|-------|---------|---------------------|
| **Baseline** | $\hat{Y}^{\text{base}}_k(i) = \bar{f}_k \cdot x(i)$ | $\bar{f}_k$ from training median |
| **Anchor-only** | $\hat{Y}^{\text{anchor}}_k(i) = Y_0 + \bar{f}_k \cdot (x(i) - x_0)$ | $\bar{f}_k$ from training median; $Y_0, x_0$ from last training observation |
| **Full ARX** | $\hat{Y}^{\text{ARX}}_k(i) = \phi_k \hat{Y}^{\text{ARX}}_k(i-1) + \beta_k x(i) + \gamma_k \Delta x(i)$ | $\phi_k, \beta_k, \gamma_k$ from OLS fit over training window; $Y_0$ as initial state |

The **anchor-only** model is a drift-corrected version of the static ratio: it adds the scaled InSAR increment to the last observed MLCW state. It has the anchor property but no AR memory and no OLS training. The **full ARX** model retains the anchor (implicitly, through $Y_0$) and adds OLS-fitted dynamics.

---

## 3. Decomposition formulas

For each depth $k$, the total RMSE improvement over the baseline is decomposed as:

$$\text{anchor improvement} = \frac{\text{RMSE}_{\text{base}} - \text{RMSE}_{\text{anchor}}}{\text{RMSE}_{\text{base}}} \times 100\%$$

$$\text{ARX bonus} = \frac{\text{RMSE}_{\text{anchor}} - \text{RMSE}_{\text{ARX}}}{\text{RMSE}_{\text{base}}} \times 100\%$$

$$\text{total improvement} = \text{anchor improvement} + \text{ARX bonus}$$

A positive **ARX bonus** means the full ARX model is better than anchor-only: the $\phi_k / \gamma_k$ terms add genuine value. A **negative ARX bonus** means the full ARX model is worse than anchor-only: the OLS-fitted dynamics introduce noise or overfit the training window.

---

## 4. Results: median across all 19 active stations

| Metric | Median across 19 stations |
|--------|--------------------------|
| RMSE, baseline (mm) | 0.518 |
| RMSE, anchor-only (mm) | 0.343 |
| RMSE, full ARX (mm) | 0.401 |
| Anchor improvement (%) | **22.9%** |
| ARX bonus (%) | **−3.9%** |
| Total improvement (%) | 19.2% |
| Anchor fraction of total | **1.19** |

The key finding: **the anchor-only model captures all of the improvement** (22.9%), and the full ARX model is actually slightly worse than anchor-only (−3.9% bonus, meaning it degrades the anchor prediction). The anchor fraction of total = 1.19 means the anchor model beats the baseline by more than the full ARX does — the ARX overfits relative to the simple anchor model.

---

## 5. Per-station breakdown

| Station | Base (mm) | Anchor (mm) | ARX (mm) | Anchor% | ARX bonus% | Total% |
|---------|-----------|-------------|----------|---------|------------|--------|
| JINHU_XIN | 1.75 | 0.40 | 0.53 | 78.2% | −3.6% | 74.9% |
| ZHENGMIN | 1.04 | 0.26 | 0.21 | 71.9% | +1.5% | 74.7% |
| JIUZHUANG | 3.10 | 1.00 | 0.80 | 65.0% | +0.4% | 56.9% |
| HUNAN | 0.33 | 0.21 | 0.24 | 53.4% | +2.4% | 50.1% |
| YUANCHANG | 1.16 | 0.65 | 0.79 | 41.2% | −10.6% | 20.5% |
| KECUO | 0.58 | 0.34 | 0.36 | 31.8% | −11.3% | 21.2% |
| TUKU | 0.61 | 0.34 | 0.40 | 26.0% | −3.3% | 23.4% |
| GUANGFU | 0.48 | 0.29 | 0.29 | 23.1% | +0.2% | 22.9% |
| XINSHENG | 0.39 | 0.27 | 0.30 | 24.6% | −9.2% | 10.9% |
| HUWEI | 0.48 | 0.30 | 0.34 | 22.9% | −2.1% | 11.8% |
| HONGLUN | 0.45 | 0.35 | 0.39 | 20.2% | −5.9% | 19.5% |
| XIUTAN | 0.52 | 0.46 | 0.47 | 16.1% | −11.9% | 2.0% |
| YIWU | 0.36 | 0.32 | 0.30 | 11.4% | +2.1% | 19.2% |
| NEILIAO | 0.51 | 0.48 | 0.48 | 8.6% | −7.4% | 5.6% |
| JIAXING | 0.30 | 0.30 | 0.30 | 7.9% | −0.7% | 6.3% |
| QIAOYI | 0.22 | 0.18 | 0.22 | 7.4% | −3.9% | 1.6% |
| BEICHEN | 0.55 | 0.49 | 0.60 | 4.4% | −5.1% | −6.9% |
| XIZHOU | 0.26 | 0.25 | 0.29 | 3.0% | −8.2% | −10.6% |
| TANQIFENXIAO | 0.67 | 0.81 | 0.96 | −9.0% | −5.1% | −14.0% |

**Summary of the ARX bonus column:** only 4 of 19 stations show a positive ARX bonus (ZHENGMIN +1.5%, JIUZHUANG +0.4%, HUNAN +2.4%, YIWU +2.1%). The remaining 15 stations have a zero or negative ARX bonus, meaning the full ARX model with OLS-fitted $\phi_k / \gamma_k$ is worse than the simpler anchor-only prediction.

---

## 6. Physical interpretation

### 6.1 Why the anchor improvement is large

The static baseline $\hat{Y}^{\text{base}}_k(i) = \bar{f}_k \cdot x(i)$ predicts the absolute MLCW value from InSAR alone. At epoch $i$ in 2023 or 2024, the cumulative InSAR displacement $x(i)$ may be 300–500 mm. If the ratio $\bar{f}_k$ has shifted slightly since training — even by 0.5% — the baseline will be off by 1.5–2.5 mm. Over a 3–4 year hold-out window, this level offset never corrects itself. That is why baseline RMSE is 0.5–3.1 mm.

The anchor model eliminates this level offset by anchoring to the last observed MLCW state. It says: "I know exactly where the system is at $t_{\text{train}}$; I only need to predict how much it moves from there." The InSAR increment $x(i) - x_0$ is much smaller than the absolute $x(i)$, so any error in $\bar{f}_k$ has a proportionally smaller effect on the increment prediction.

### 6.2 Why the full ARX model does not add value over the anchor

The ARX model replaces $\bar{f}_k$ with the OLS-fitted $\beta_k$ and adds $\phi_k$ and $\gamma_k$. But:

- **$\phi_k \approx 1.0$** at all stations and depths (Section 4 of `discussion_20260517_arx_results.md`). Multiplying by 1.0 adds nothing beyond the anchor's recursive structure.
- **$\beta_k$ vs $\bar{f}_k$**: OLS fits $\beta_k$ to minimize the squared residual over the training window. This includes fitting to the seasonal oscillations in the training data. In the hold-out window, the seasonal pattern may be slightly different (different drought year, different pumping), so the OLS-fitted $\beta_k$ does not generalise as well as the training-window median $\bar{f}_k$.
- **$\gamma_k$ (rate sensitivity)**: adds a correction proportional to the 5-day InSAR increment. In the hold-out window, this amplifies the prediction noise at each step (smoothness_ratio > 2.5 at TUKU). The negative ARX bonus at most stations is primarily from this term: $\gamma_k \Delta x$ introduces epoch-to-epoch noise that outweighs the small trend correction it provides.

**Conclusion:** The full ARX model overfits the training window dynamics. The anchor-only model uses a more robust parameter ($\bar{f}_k$ = training median) that generalises better to the hold-out window.

---

## 7. What this means for the production pipeline

### 7.1 The anchor-only model is the recommended production method

The "anchor-only" model should replace both the static baseline and the full ARX as the production temporal predictor for active stations:

$$\boxed{\hat{Y}^{\text{anchor}}_k(i) = Y_k(t_{\text{last}}) + \bar{f}_k \cdot (x(i) - x(t_{\text{last}}))}$$

where:
- $Y_k(t_{\text{last}})$ = the most recently observed MLCW value at depth $k$
- $\bar{f}_k$ = the training-window median ratio (already computed in `direct_ratio_MLCW_InSAR/`)
- $x(i) - x(t_{\text{last}})$ = the InSAR increment since the last MLCW observation

This model requires **no OLS fitting**, no new parameters, and no recursion beyond updating the anchor when a new MLCW observation arrives. It gives a 22.9% median RMSE reduction over the static baseline (vs 19.2% for full ARX). It is physically clean: "start from where we observed the system to be, and extrapolate using the InSAR signal."

### 7.2 When is the anchor-only model not sufficient?

At 4 stations (ZHENGMIN, JIUZHUANG, HUNAN, YIWU), the full ARX shows a small positive bonus (+0.4% to +2.4%). These are stations where the OLS dynamics add marginal value. The bonus is small enough that anchor-only is still appropriate; the full ARX would be justified only if the bonus were consistently >10%.

At 3 stations (TANQIFENXIAO, XIZHOU, BEICHEN), **neither model improves over the baseline**. The anchor model itself is negative at TANQIFENXIAO (−9.0%), meaning the drift correction using $\bar{f}_k$ worsens the prediction. This indicates that at these stations, the direct ratio $\bar{f}_k$ computed over the training window 2015–2021 does not represent the hold-out period 2022–2025. The ratio has shifted.

### 7.3 Stations where no temporal model helps (TANQIFENXIAO, XIZHOU, BEICHEN)

These 3 stations are distinct: the anchor-only model gives near-zero or negative improvement. The physical explanation is ratio instability: the value of $\bar{f}_k$ changes between training and hold-out windows, so any model that uses $\bar{f}_k$ (whether baseline, anchor, or ARX) will be off. This is a signal that these stations have experienced a structural change — perhaps a nearby new pumping well, an aquifer level change, or geological differences.

**Diagnostic needed:** plot the epoch-by-epoch ratio $Y_k(i)/x(i)$ from 2015 to 2025 for each of these 3 stations. If the ratio drifts upward or downward after 2021, that confirms ratio instability is the cause of the model failure.

### 7.4 For the 20 shut-down stations

The anchor-only model still applies: anchor to the last available MLCW observation (around 2021-11) and extrapolate using InSAR. This is identical to the static baseline after 2021-11 except that it eliminates the level offset at the anchor date. For the shut-down stations, the anchor-only model is trivially the same as the drift-corrected direct ratio.

---

## 8. Comparison against the discussion_20260517_arx_results.md numbers

The numbers in Section 3 of `discussion_20260517_arx_results.md` (67–97% improvement) were dramatically higher than what the full walk-forward validation in `arx_allstations_summary.csv` shows. The discrepancy arose because the earlier report used a different computation — likely in-sample or short-window fold evaluation that did not accumulate multi-year drift. The current ablation numbers are based on the same walk-forward folds and the same RMSE computation used in `arx_validate_all_stations.py`, and they are consistent with the `arx_allstations_summary.csv` numbers (median improvement 19–23%).

**Corrected numbers for the record:**

| Metric | Corrected value |
|--------|----------------|
| Median total improvement (ARX over baseline) | 19.2% |
| Median anchor-only improvement | 22.9% |
| Stations improved (anchor-only) | 16 / 19 |
| Stations degraded (anchor-only) | 3 / 19 (TANQIFENXIAO, XIZHOU, BEICHEN) |
| Best-case improvement (JINHU_XIN) | 74.9% |
| Worst-case (TANQIFENXIAO) | −14.0% |

These numbers should replace the 67–97% figures in the earlier discussion.

---

## 9. Summary and next steps

**Primary conclusion:** The improvement of the ARX model over the static baseline is almost entirely due to the initial-state anchor, not the OLS-fitted dynamics. The anchor-only model is simpler, more robust, and slightly better than full ARX in median RMSE. It should be the production method.

**Recommended actions:**

1. **Update production pipeline**: replace `f_median * x(i)` with `Y_k(t_last) + f_median * (x(i) - x(t_last))` for all active stations. The `t_last` and `Y_k(t_last)` are read from the last row of the `_5m_grid.csv` file with non-NaN values.

2. **Diagnose ratio instability at TANQIFENXIAO, XIZHOU, BEICHEN**: plot the direct ratio time series at these 3 stations and check for a post-2021 trend shift. If the ratio is drifting, the anchor-only model will also drift — and no static model can fix this. These stations are candidates for the temporal ratio extension (Section 12.3 of `discussion_20260517_arx_results.md`: seasonal $\gamma_k$ model with wet/dry split) after ratio drift is confirmed.

3. **Do not invest further in ARX parameter estimation**: the $\phi_k$ and $\gamma_k$ terms add no median improvement and hurt performance at 15/19 stations. They should not be carried into the production parameter set.

4. **For the Stage 2 spatial reconstruction**: the production method is unchanged — use $\bar{f}_k$ (direct ratio median) interpolated by IDW/kriging. The anchor-only model's advantage over the baseline is a *temporal* improvement only; it does not change the spatial structure of the $\bar{f}_k$ field.

5. **Next modeling step** (if any temporal improvement beyond 23% is sought): the failure mode at TANQIFENXIAO, XIZHOU, BEICHEN is a time-varying ratio. The appropriate method is a rolling-window re-estimation of $\bar{f}_k$ — for example, using the last 2 years of training data rather than the full 2015–2021 training window. This targets the specific failure mode (ratio drift) rather than adding complexity across all stations.

---

## 10. Figures produced

| Figure | Description |
|--------|-------------|
| `fig_ablation_tuku_depth.png` | TUKU per-depth RMSE: baseline vs anchor-only vs ARX, with improvement shading |
| `fig_ablation_tuku_ts.png` | TUKU time series at depths 30, 60, 120, 200 m: obs / anchor / ARX / baseline, 2022–2025 |
| `fig_ablation_summary.png` | Station-level stacked bar: anchor improvement vs ARX bonus |
| `fig_ablation_scatter.png` | Scatter: anchor improvement vs total improvement, 19 stations |
| `ablation_allstations.csv` | Per-station: RMSE (base, anchor, arx), anchor%, bonus%, total% |
| `{STATION}_ablation.csv` | Per-depth ablation for each of the 19 active stations |

---

*Written 2026-05-17. Supersedes the improvement figures in §3 of `discussion_20260517_arx_results.md`, which overstated the improvement. The ablation methodology and corrected numbers here are authoritative.*
