# Part 1 Findings — TUKU Single-Well Pilot (2026-06-10)

> **For auditors:** This document summarizes everything achieved in Part 1, what the
> numbers mean physically, the known limitations, and what remains open. All evidence
> cited is from result files in `tau_demo_TUKU/results/`. See `PROGRESS.md` §6 for a
> compact summary.

---

## 1. What We Set Out to Do

MLCW monitoring wells in the Choushui River Alluvial Fan have stopped operating or
reduced sampling due to cost. The problem: broken observational records. The objective
of Part 1 was to test, at a single pilot station (TUKU), whether continuously available
GPS surface displacement can substitute for lost in-situ compaction measurements.

**Success criterion:** gap-fill RMSE < RMSE of static linear interpolation baseline;
walk-forward skill score > 0 on held-out epochs.

---

## 2. Method Evolution — How We Got Here

### 2.1 Initial approach: IHM-F v3 (bilinear Terzaghi/Riley)

The original method was a groundwater-driven per-layer compaction model:

$$b(t) = c + S_{ke} \cdot u(t) + (S_{kv} - S_{ke}) \cdot V(t)$$

where $u(t)$ is zero-referenced hydraulic head and $V(t) = \min(0, \text{cummin}(H) - h_c)$
is the virgin inelastic exceedance term (Riley 1969).

**Three critical bugs were found and fixed (2026-06-09):**
- **R1 — Absolute-head datum bug:** Production solver used absolute head (m MSL) instead
  of zero-referenced head $u(t) = H(t) - H(t_{ref})$. This caused $S_{ke}$ to collapse to
  zero for all positive-head wells (HONGLUN at +8.5 m, TUKU at +3.0 m).
- **R2 — h_c coordinate-frame bug:** Preconsolidation head $h_c$ was computed in absolute
  MSL but $H(t)$ was used in a different frame, misclassifying elastic/inelastic epochs.
- **R3 — Walk-forward used deprecated incremental solver:** The incremental solver erases
  preconsolidation memory, causing n_inelastic = 0 in all walk-forward folds.

After fixes: all 6 layers have $S_{ke} \ge 0$, $S_{kv} \ge S_{ke}$, per-layer
$R^2_{cum} > 0$. The bilinear model is now physically trustworthy for parameter
characterization.

### 2.2 Held-out bake-off revealed bilinear is the worst gap-fill method

A three-method comparison (Phase 0.1) tested GPS carrier vs bilinear vs linear
interpolation on two realistic holdout designs: middle gap (40–70% of record,
simulates reduced sampling) and end gap (last 30%, simulates permanent shutdown).

**Result: GPS carrier won all 6 layers.** Bilinear was the worst gap-fill method on
every layer. Example: F2 middle-gap RMSE — carrier 4.3 mm, bilinear 8.4 mm,
interpolation 40.5 mm. Bilinear is now used only for physical parameter
characterization (reporting $S_{ske}$, $S_{skv}$), not for gap-fill.

### 2.3 Current model: GPS carrier with optional GWL term

$$b_k(t) = a_k \cdot d_{GPS}(t) + d_k \cdot u_k(t) + c_k$$

with constraints $a_k \ge 0$, $d_k \ge 0$. The GPS term handles the secular subsidence
trend; the GWL term (enabled only for T1 per held-out evaluation) captures sub-annual
head-driven elastic response.

---

## 3. Decision Points

| # | Question | Verdict | Evidence |
|---|----------|---------|----------|
| DP 0 | Is the bilinear model trustworthy for parameters? | **PASS** | All $S_{ke} \ge 0$, $S_{kv} \ge S_{ke}$, per-layer $R^2_{cum} > 0$ |
| DP 1 | Which method fills gaps best? | **CARRIER-PRIMARY** | GPS carrier wins all 6 layers by held-out RMSE |
| DP 2 | Can the carrier predict 6 months ahead? | **PARTIAL** | 2/6 layers skill > 0 (T1 +0.41, T2 +0.43); 4/6 fail |

---

## 4. Comprehensive Evaluation Metrics (TUKU, 6 layers)

All metrics computed on GPS-available calibration epochs (n ≈ 1,081 per layer).
Source: `tau_demo_TUKU/results/evaluation_metrics.json`.

### 4.1 Amplitude and Error Metrics

| Layer | obs_range (mm) | range_ratio | NRMSE% | RMSE (mm) | MAE (mm) | max_err (mm) | R² |
|-------|---------------|-------------|--------|-----------|----------|-------------|-----|
| F1 | 21.3 | 0.811 | 5.8% | 1.23 | 0.98 | 3.35 | 0.940 |
| T1 | 14.6 | 0.917 | 6.2% | 0.90 | 0.73 | 2.46 | 0.946 |
| F2 | 144.8 | 0.973 | 3.4% | 4.86 | 4.07 | 11.57 | 0.985 |
| T2 | 21.0 | 0.869 | 12.2% | 2.57 | 2.13 | 6.12 | 0.802 |
| F3 | 216.2 | 0.934 | 3.7% | 8.02 | 6.14 | 21.44 | 0.981 |
| F4 | 25.1 | 0.836 | 5.6% | 1.41 | 1.22 | 3.46 | 0.947 |

**Interpretation:**
- **Range ratio 0.81–0.97:** The carrier captures 81–97% of the true compaction
  amplitude. F1 shows the most compression (19% under-predicted).
- **NRMSE 3.4–12.2%:** T2 has the largest error relative to its signal (12.2%).
  F2 and F3, the main aquifers, have the smallest (3.4%, 3.7%).
- **R² 0.80–0.99:** High values are driven by the secular trend, which dominates
  the signal variance. Do not interpret as evidence of sub-annual skill.

### 4.2 Rate and End-Point Metrics

| Layer | trend error% | end_error (mm) | end_error% | Carrier share $a_k$ |
|-------|-------------|----------------|------------|---------------------|
| F1 | 0.40% | −2.20 | −10.9% | 0.026 (2.6%) |
| T1 | 0.39% | +0.56 | +3.0% | 0.018 (1.8%) |
| F2 | 0.28% | −1.93 | −1.3% | 0.213 (21.3%) |
| T2 | 0.65% | +0.99 | +4.7% | 0.028 (2.8%) |
| F3 | 0.46% | −19.29 | −8.9% | 0.306 (30.6%) |
| F4 | 0.15% | −2.72 | −10.8% | 0.032 (3.2%) |

**Interpretation:**
- **Trend error < 1% for all layers:** The carrier captures the secular compaction
  rate almost perfectly. This is because GPS displacement itself is 99.6% linear
  ($R^2 = 0.996$ against a straight line). The carrier IS a scaled GPS trend.
- **End-point errors of 9–11% for F1, F3, F4:** The model lags at the end of the
  record. Late-stage compaction acceleration (post-2023) is not expressed in the
  GPS signal at sufficient amplitude for these layers.
- **$\sum a_k = 0.624$:** The 6 instrumented layers account for 62% of surface
  displacement. The remaining 38% is compaction below F4 (>300 m depth, no MLCW)
  plus measurement noise.

### 4.3 Sub-Annual Dynamics

| Layer | Detrended corr (obs vs pred) | GWL term adopted? | GWL Δ held-out RMSE |
|-------|------------------------------|-------------------|---------------------|
| F1 | +0.46 | No | −4.2% (marginal) |
| T1 | +0.42 | **Yes** | **−14.3%** |
| F2 | +0.16 | No | −0.8% |
| T2 | −0.08 | No | +0.4% (worse) |
| F3 | −0.09 | No | +0.2% (worse) |
| F4 | +0.16 | No | −0.0% |

**Interpretation:**
- **Detrended correlations near zero for deep layers (F2, T2, F3, F4):** Once
  the secular trend is removed, the carrier model has no predictive power for
  sub-annual fluctuations. The GPS signal does not carry seasonal head-driven
  compaction cycles at detectable amplitude.
- **T1 is the only adopter of the GWL term:** A shallow aquitard (9 m, τ=0) where
  head fluctuations directly drive elastic compaction. The GWL term reduces held-out
  RMSE by 14.3%.
- **For all other layers, adding GWL noise degrades prediction.** The secular trend
  dominates the compaction signal; adding a noisy GWL regressor increases overfitting.

---

## 5. Bilinear Parameter Characterization (Phase 1.4)

Source: `tau_demo_TUKU/results/characterization/TUKU_storage_params.json`.

| Layer | $S_{ske}$ (m⁻¹) | $S_{skv}$ (m⁻¹) | bulk ratio | Flags |
|-------|------------------|------------------|------------|-------|
| F1 | 5.93×10⁻⁵ | 2.62×10⁻⁴ | 1.76 | ratio_bulk_below_8 |
| T1 | 1.77×10⁻⁴ | 4.22×10⁻⁴ | 2.02 | ratio_bulk_below_8 |
| F2 | 8.85×10⁻⁶ | **1.41×10⁻³** | 18.06 | thickness_artifact |
| T2 | 2.00×10⁻⁵ | 5.41×10⁻⁴ | 17.09 | — (cleanest fit) |
| F3 | 1.69×10⁻⁷ | 3.12×10⁻⁴ | 1286 | S_ke unidentifiable |
| F4 | 0 | 5.21×10⁻⁴ | ∞ | S_ke=0 (100% silt/mud) |

**Key findings:**
- **F2 $S_{skv} = 1.41 \times 10^{-3}$ m⁻¹** closely matches Hung et al. (2021) middle
  fan zone prior ($1.33 \times 10^{-3}$). This is the strongest validation of the
  bilinear characterization track.
- **T2 is the only layer with no flags** — clean elastic/inelastic separation.
- **F3 $S_{ke} \approx 0$** — elastic regime unidentifiable (n_elastic = 182 but
  collinear with intercept).
- **F4 $S_{ke} = 0$** — physically correct. F4 is 100% silt/mud per borehole log;
  should be inelastic-only.
- **F1/T1 bulk ratio < 8:** These shallow layers at TUKU are in an elastic-dominated
  regime. The virgin term $V(t)$ has not been strongly activated post-2015.
- **F2 thickness artifact:** specific ratio = 158.75× vs bulk ratio = 18.06×. The
  8.79× inflation comes from dividing $S_{ske}$ (total span 106.3 m) by $S_{skv}$
  (clay-only 12.1 m). Use bulk ratio for literature comparison.

---

## 6. What the Carrier Model Achieves

1. **Secular trend:** Captured almost perfectly (trend error < 1% for all layers).
   The GPS displacement trend IS the MLCW compaction trend — they share the same
   physical driver (groundwater extraction and inelastic consolidation).

2. **Amplitude fidelity:** Range ratio 0.81–0.97. The carrier slightly under-predicts
   total compaction magnitude, especially for the shallowest (F1, 81%) and deepest
   (F4, 84%) layers.

3. **Gap-fill dominance:** On held-out epochs, the carrier beats linear interpolation
   by 2–9× for the main aquifers (F2, F3). It beats the bilinear model on every layer.

4. **Layer apportionment is physically sensible:** F3 (deepest thick aquifer) takes
   the largest share (30.6%), F2 (main aquifer) takes 21.3%, aquitards take 1.8–3.2%.
   The sum (62.4%) leaves room for deep unconsolidated compaction below 300 m.

## 7. What the Carrier Model Cannot Do

1. **Sub-annual dynamics:** Detrended correlation is ~0 for deep layers. The carrier
   predicts a smooth secular trend; it cannot capture seasonal GWL-driven cycles,
   drought-year acceleration, or monsoon recovery. The physical reason: GPS surface
   displacement is dominated by the secular trend (99.6% linear); seasonal and
   interannual surface signals are too small relative to the trend to apportion to
   individual layers.

2. **Short-term prediction:** 4 of 6 layers fail to beat a simple linear trend on
   6-month tail holdout (Decision Point 2: PARTIAL). The carrier IS a scaled linear
   trend — it cannot anticipate acceleration or deceleration.

3. **End-point accuracy:** F1 (−10.9%), F3 (−8.9%), and F4 (−10.8%) show substantial
   end-of-record errors. The carrier lags behind observed compaction in the final
   epochs, likely because late-stage compaction accelerates but the GPS signal does
   not.

4. **Deep layer noise:** T2 has NRMSE = 12.2% — the worst of any layer. The thin
   aquitard signal (21 mm range) is poorly captured by the surface displacement.

## 8. Open Questions for Auditor Guidance

1. **Is the straight-line limitation acceptable for gap-fill?** If the deliverable is
   "reconstruct missing MLCW epochs between bracketing observations," the carrier's
   trend fidelity may be sufficient. If the deliverable is "predict future compaction
   with sub-annual accuracy," the carrier is inadequate.

2. **Should we invest in non-linear surface signals?** The GPS signal at TUKU is 99.6%
   linear. InSAR at other stations may carry more seasonal signal. Testing this
   requires Part 2 (multi-well extension).

3. **Should the GWL term be extended to more layers?** Only T1 cleared the 5% held-out
   RMSE gate. But F1 was marginal (−4.2%). With more data (Part 2), the GWL term may
   help at stations with stronger seasonal GWL-MLCW coupling.

4. **Is the bilinear characterization track sufficient for the physical story?** F2
   $S_{skv}$ matches the literature, T2 is clean, and the F4/F3 flags are physically
   justified. The bilinear model is trustworthy for parameter reporting. Should we
   proceed with it as-is for Part 2?

5. **Should we add a seasonal harmonic term to the carrier?** The previous seasonal
   harmonic pipeline (scripts/13_seasonal_insar/) showed that F2 seasonal amplitude
   is recoverable from InSAR. Adding an annual harmonic $e_k \cdot \sin(2\pi t/365) + f_k \cdot \cos(2\pi t/365)$
   to the carrier model may capture seasonal cycles better than the GWL term.

6. **Is Part 2 (37-station extension) the right next step?** The carrier method is
   validated at TUKU with known limitations. Extending to 37 stations would reveal
   whether the limitations are TUKU-specific or systematic across the fan.

---

## 9. Result File Index

All outputs in `tau_demo_TUKU/`:

| File | Content |
|------|---------|
| `results/holdout_bakeoff.json` | 36 RMSE values, Decision Point 1 |
| `results/reconstruction/TUKU_*_reconstruction.csv` | 6 per-layer timeseries (1,572 epochs) |
| `results/reconstruction/TUKU_carrier_reconstruction_summary.json` | Per-layer $a_k$, $d_k$, R², RMSE, tail evaluation |
| `results/carrier_gwl_eval.json` | GWL term Δ% per layer, adoption decisions |
| `results/evaluation_metrics.json` | 15 amplitude-aware metrics per layer |
| `results/characterization/TUKU_storage_params.json` | $S_{ske}$, $S_{skv}$, bulk/specific ratios |
| `results/visualization/` | 11 diagnostic PNGs + 4 CSVs |
| `plots/reconstruction/TUKU_reconstruction_6layer.png` | 6-panel timeseries figure |
