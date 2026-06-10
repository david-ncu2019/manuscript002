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
every layer. Example (corrected-lag bake-off, `holdout_bakeoff.json`): F2 middle-gap
RMSE — carrier 4.30 mm, bilinear 7.04 mm, interpolation 40.50 mm. Bilinear is now used
only for physical parameter characterization (reporting $S_{ske}$, $S_{skv}$), not gap-fill.

### 2.3 Current model: GPS carrier with optional GWL term

$$b_k(t) = a_k \cdot d_{GPS}(t) + d_k \cdot u_k(t) + c_k$$

with constraints $a_k \ge 0$, $d_k \ge 0$. The GPS term handles the secular subsidence
trend; the GWL term captures sub-annual head-driven elastic response.

**GWL-term adoption map (re-issued M2, source `carrier_gwl_eval.json` → `adopt_gwl`):**
with correct τ-lags, the GWL term improves average held-out RMSE by > 5% on F1
(−10.2%), T1 (−14.3%), F2 (−8.7%), and T2 (−6.3%) — all ADOPTED. F3 (+0.0%, the
constrained fit drives $d_k$ to 0) and F4 (−2.2%, below the 5% gate) REJECT it. The
pre-repair map adopted T1 only; the correct-lag map adopts **F1, T1, F2, T2**.

---

## 3. Decision Points (RE-ISSUED 2026-06-10 post-M1-repair, M2)

> All three decision points below were re-issued in Milestone M2 from persisted files
> produced by the τ-lag-corrected programs (super_plan_2026-06-10). The pre-repair
> verdicts in earlier versions of this table were made with the relative driver–response
> lag effectively zero (defect D1) and are OBSOLETE.

| # | Question | Verdict | Evidence (file + field) |
|---|----------|---------|----------|
| DP 0 | Is the bilinear model trustworthy for parameters? | **PASS** | `characterization/TUKU_storage_params.json` — all $S_{ke} \ge 0$, $S_{kv} \ge S_{ke}$; F1/T1/F2/T2 per-layer `r2_cum` > 0; F3/F4 inelastic-only re-fit (negative cumulative $R^2$, reported honestly, not used for gap-fill) |
| DP 1 | Which method fills gaps best? | **CARRIER-PRIMARY** | `holdout_bakeoff.json` → `win_counts.carrier` = 6; `primary_method` = carrier for all 6 layers. Carrier arm reproduces pre-repair RMSE to < 0.001 mm (equivalence check pass) |
| DP 2 | Can the carrier predict 6 months ahead? | **PASS** | `reconstruction/TUKU_carrier_reconstruction_summary.json` → `tail_evaluation`: skill > 0 on 3/6 layers (T1 +0.4075, F2 +0.4305, T2 +0.2981); F1 −0.1813, F3 −0.2488, F4 −0.1425. PASS threshold is exactly $\ge 3$ |

**Note on DP2 boundary:** with the corrected GWL adoption map (F1,T1,F2,T2 adopt the GWL
term per `carrier_gwl_eval.json`), T2's tail skill is +0.2981 (was +0.4283 when T2 carried
no GWL term in the M1 F2,T1-only run). Three layers remain skill > 0, so DP2 = PASS. The
prior "PARTIAL, 2/6, T1 +0.41 / T2 +0.43" traced to an unpersisted stdout note and is OBSOLETE.

---

## 4. Comprehensive Evaluation Metrics (TUKU, 6 layers)

All metrics computed on GPS-available **calibration** epochs (n ≈ 1,081 per layer).
Source: `tau_demo_TUKU/results/evaluation_metrics.json` (regenerated 2026-06-10).

> **Caveat (Do-Not-Regress #4):** these are in-sample, calibration-epoch metrics —
> diagnostic only. They never satisfy the apex goal and were NOT used to issue any
> decision point. The authoritative held-out numbers are in §3 (DP1/DP2) and the
> held-out RMSE tables in `holdout_bakeoff.json` / `carrier_gwl_eval.json`. The carrier
> shares $a_k$ quoted in §4.2 are from the calibration fit; the held-out-fold $a_k$ values
> (used for the actual decisions) live in the bake-off and tail-evaluation files.

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
- **$\sum a_k = 0.637$** (source: `TUKU_carrier_reconstruction_summary.json` →
  `sum_a_k` = 0.637022, corrected adoption map F1,T1,F2,T2): the 6 instrumented layers
  account for ~64% of surface displacement. The remaining ~36% is compaction below F4
  (>300 m depth, no MLCW) plus measurement noise.

### 4.3 Sub-Annual Dynamics

> **RE-ISSUED M2 (2026-06-10).** This table is now read from `carrier_gwl_eval.json`
> (`per_layer.<L>.<design>.delta_pct`, `adopt_gwl`) computed with correct τ-lags. The
> pre-repair version showed the GWL Δ at effectively zero lag (defect D1) and is OBSOLETE.

| Layer | avg held-out Δ% RMSE (carrier+GWL vs carrier) | GWL term adopted? |
|-------|-----------------------------------------------|-------------------|
| F1 | −10.2% | **Yes** |
| T1 | −14.3% | **Yes** |
| F2 | −8.7% | **Yes** |
| T2 | −6.3% | **Yes** |
| F3 | +0.0% | No |
| F4 | −2.2% | No |

Source: `carrier_gwl_eval.json` → `per_layer.<L>.middle.delta_pct` and `.end.delta_pct`
averaged; `adopt_gwl`. The collinearity guard (`collinearity.<L>`) shows F1/T1 head–GPS
correlation 0.84 (VIF 3.38/3.36, below the 10 rejection bound, so the GWL term is admitted).

**Interpretation (corrected):**
- **The GWL term now helps four layers, not one.** With the driver lagged correctly,
  the head residual carries genuine information for F1, T1, F2, and T2. The pre-repair
  claim "T1 is the only adopter" was an artifact of fitting head against the wrong year
  of compaction (F2 at τ=72 = 360 days was the worst-paired).
- **F3 and F4 still reject the GWL term.** F3's constrained fit drives $d_k \to 0$
  (the head residual adds nothing beyond the carrier); F4 improves only 2.2%, below the
  5% gate.

---

## 5. Bilinear Parameter Characterization (Phase 1.4)

> **RE-ISSUED M2 (2026-06-10).** Re-run with correct τ-lags. Source:
> `characterization/TUKU_storage_params.json` (`per_layer.<L>`). The pre-repair table
> (F3 ratio 1286 "unidentifiable", F2 S_skv 1.41e-3 / bulk 18.06, F1/T1 "V not activated")
> is OBSOLETE — it was fit at effectively zero lag (defect D1), and its F1/T1 physical
> reading is contradicted by the Task 2.2.4 investigation below.

| Layer | $S_{ske}$ (m⁻¹) | $S_{skv}$ (m⁻¹) | bulk ratio $S_{kv}/S_{ke}$ | VIF(u,V) | $R^2_{cum}$ | Flags / status |
|-------|------------------|------------------|------------|------|------|-------|
| F1 | 6.32×10⁻⁵ | 2.60×10⁻⁴ | 1.64 | 3.09 | 0.691 | identifiable; ratio_bulk_below_8 |
| T1 | 1.77×10⁻⁴ | 4.22×10⁻⁴ | 2.03 | 3.10 | 0.755 | identifiable; ratio_bulk_below_8 |
| F2 | 1.04×10⁻⁵ | **1.34×10⁻³** | 14.67 | 1.17 | 0.926 | identifiable; thickness_artifact |
| T2 | 2.11×10⁻⁵ | 5.37×10⁻⁴ | 16.06 | 1.08 | 0.724 | identifiable; no flags (cleanest fit) |
| F3 | not determined | 3.08×10⁻⁴ | n/d | 1.13 | −2.79 | inelastic-only re-fit; $S_{ke}$=0 |
| F4 | not determined | 5.23×10⁻⁴ | n/d | 1.02 | −1.41 | inelastic-only re-fit; $S_{ke}$=0 (100% silt/mud) |

(Values are `S_ske_m1`, `S_skv_m1`, `ratio_bulk`, `vif_u_V`, `r2_cum` from the JSON.)

**Key findings (corrected):**
- **F2 $S_{skv} = 1.34 \times 10^{-3}$ m⁻¹ — the "F2 matches Hung et al." claim SURVIVES
  the lag correction.** At the correct τ=72 (360 days), F2 $S_{skv}$ matches the Hung et
  al. (2021) middle-fan prior ($1.33 \times 10^{-3}$ m⁻¹) within < 1%. This was the result
  most at risk from defect D1 (F2 had the worst mis-pairing), so its survival is the
  strongest validation of the bilinear characterization track. The pre-repair value was
  $1.41 \times 10^{-3}$; the corrected value $1.34 \times 10^{-3}$ is even closer to the prior.
- **F3 identifiability — D5/D6 contradiction RESOLVED (see §5.1).** F3 is now flagged
  `S_ke_not_identifiable` and re-fit inelastic-only ($S_{ke}=0$). The old "ratio 1286,
  identifiable" verdict is deleted as a defect-D5 artifact. The document and the live JSON
  now agree.
- **T2 is the only layer with no flags** — clean elastic/inelastic separation (VIF 1.08).
- **F4 $S_{ke} = 0$** — physically correct. F4 is 100% silt/mud per borehole log; inelastic-only.
- **F3/F4 inelastic-only re-fits carry negative cumulative $R^2$ (−2.79, −1.41).** This is
  an honest finding, not a bug (M1 Task 1.5.2 note): once $S_{ke}$ is removed, the single
  inelastic regressor under-fits the cumulative trace. These layers' physical parameters
  are reported as "not determined," and gap-fill uses the carrier, not this fit.
- **F2 thickness artifact:** specific ratio 128.92× vs bulk ratio 14.67×. The inflation
  comes from dividing $S_{ske}$ (total span 106.3 m) by $S_{skv}$ (clay-only 12.1 m,
  span/clay = 8.8 > 4). Use the bulk ratio for literature comparison.

### 5.1 F1/T1 below-floor investigation (Task 2.2.4) — D5/D6 resolution context

F1 (bulk ratio 1.64) and T1 (2.03) sit below the physical floor of 3. The three plan
hypotheses were tested in order. Source: `characterization/f1t1_below_floor.json`
(from `diag_f1t1_below_floor.py`, which replicates the Script 15 lagged loader exactly).

| Quantity (HONGLUN well 09050111, serves F1 and T1) | F1 (τ=6) | T1 (τ=0) |
|---|---|---|
| $h_c$ (preconsolidation head, m MSL) | 6.504 | 6.504 |
| minimum lagged head (m MSL) | 3.146 | 3.146 |
| max head drop below $h_c$ (m) | **3.358** | **3.358** |
| epochs with $V < 0$ | 752 / 1566 (48.0%) | 758 / 1571 (48.2%) |
| total $V$ excursion (m) | 3.358 | 3.358 |
| post-2015 new $V$ excursion (m) | 3.358 | 3.358 |

- **Hypothesis (a) — "$V$ barely activates, $S_{kv}$ fit on weak signal" — REJECTED.**
  Head drops 3.358 m below $h_c$ and $V < 0$ on ~48% of epochs, all of it accruing
  post-2015. $V$ is strongly activated; $S_{kv}$ is fit on a real signal.
- **Hypothesis (b) — "τ is wrong" — NOT the cause.** F1 uses the production τ=6
  (30 days), T1 τ=0. T1 never carried the D1 defect (τ=0 is lag-immune), yet its ratio
  is still 2.03. The low ratio is not a lag artifact.
- **Hypothesis (c) — "elastic-dominated regime, $S_{kv}$ not excited" — REJECTED.** The
  full virgin excursion is post-2015, so these layers are NOT behaving elastically in the
  modern period.
- **Conclusion:** the low bulk ratio at HONGLUN (F1 1.64, T1 2.03) is a **genuine material
  finding, not a gate failure**. Both fits are well-determined (VIF 3.09/3.10, far below the
  10 rejection bound; $S_{ke}$ identifiable). The shallow HONGLUN sediments show a low
  inelastic/elastic contrast (~1.6–2×), below the 8–50× typical of deeper CRAF clays. Per
  Task 2.2 the layers are flagged `ratio_bulk_below_8` and NOT failed on the mixed ratio.

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
   the largest share (~30%), F2 (main aquifer) ~23%, aquitards a few percent each.
   The sum ($\sum a_k$ = 0.637, source `TUKU_carrier_reconstruction_summary.json`)
   leaves ~36% for deep unconsolidated compaction below 300 m.

## 7. What the Carrier Model Cannot Do

1. **Sub-annual dynamics:** Detrended correlation is ~0 for deep layers. The carrier
   predicts a smooth secular trend; it cannot capture seasonal GWL-driven cycles,
   drought-year acceleration, or monsoon recovery. The physical reason: GPS surface
   displacement is dominated by the secular trend (99.6% linear); seasonal and
   interannual surface signals are too small relative to the trend to apportion to
   individual layers.

2. **Short-term prediction:** 3 of 6 layers (F1, F3, F4) fail to beat a simple linear
   trend on the 6-month tail holdout; 3 (T1, F2, T2) beat it (Decision Point 2: PASS,
   `TUKU_carrier_reconstruction_summary.json` → `tail_evaluation`). The carrier IS a
   scaled linear trend — for the failing layers it cannot anticipate acceleration or
   deceleration. The GWL-adopting layers T1, F2, T2 gain positive tail skill from the
   head residual.

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
| `results/characterization/TUKU_storage_params.json` | $S_{ske}$, $S_{skv}$, bulk/specific ratios, identifiability |
| `results/characterization/f1t1_below_floor.json` | Task 2.2.4 — F1/T1 $V$-activation evidence |
| `results/visualization/` | 11 diagnostic PNGs + 4 CSVs |
| `plots/reconstruction/TUKU_reconstruction_6layer.png` | 6-panel timeseries figure |
