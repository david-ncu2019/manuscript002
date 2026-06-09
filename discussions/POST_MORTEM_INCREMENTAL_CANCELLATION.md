# Post-Mortem: IHM-F v3 Incremental Solver — 5-Day Cancellation Failure

**Date:** 2026-06-08
**Status:** CIRCUIT BREAKER TRIPPED — structural modeling failure, not a code bug
**Scope:** TUKU GPS pilot re-run with fixed α = 0.625 (Day 3 of 7-day plan)
**Related:** `PEER_REVIEW_MATH_VERIFICATION.md`, `INDEPENDENT_COUNTER_AUDIT_REPORT.md`, `INDEPENDENT_AUDIT_IHM_F_V3_20260607.md`, `plans/2026-06-07-alpha-fix-seven-day-plan.md`

---

## CRITICAL BREAKING POINT: 5-DAY INCREMENTAL CANCELLATION

### Executive Summary

The IHM-F v3 model's incremental formulation ($\Delta b = S_k \cdot \Delta H$) cannot reproduce the cumulative MLCW compaction at TUKU station. The model predicts 0.1–0.9 mm/yr net per-layer compaction. The MLCW sensors record 8–15 mm/yr monotonic subsidence. The ratio of observed to predicted compaction ranges from 8× to 355×, with $R^2_{\text{MLCW,cum}}$ negative or NaN for all six layers. This is a physical domain mismatch between 5-day elastic head oscillations and the multi-year secular consolidation signal — not a solver bug, not a parameter tuning problem, not a NaN-mask deficiency.

### How the Model Was Supposed to Work

The IHM-F equation in incremental form:

$$\Delta b_j(t) = S_j \cdot \Delta H_j(t - \tau_j)$$

where:

- $S_j = S_{ke}$ when the head is above the running historical minimum (elastic recovery)
- $S_j = S_{kv}$ when the head sets a new running minimum (virgin inelastic consolidation)
- $\Delta H_j$ is the 5-day head change (~0.001–0.003 m per epoch)

Over years, the per-epoch predictions accumulate:

$$b_j(T) = \sum_{t=\tau}^{T} S_j \cdot \Delta H_j(t - \tau_j) = S_j \cdot \left[H_j(T-\tau_j) - H_j(0)\right]$$

In theory, the secular head decline (e.g. −40 m over 10 years) multiplied by $S_{kv}$ (e.g. 1 mm/m) should accumulate to −40 mm of compaction.

### What Actually Happened at TUKU — The Physical Mechanism

**The short-term head oscillations cancel each other out.**

At TUKU F2 (well 09050321), the head oscillates seasonally by ±2 m/yr between recharge and pumping:

| Year | $\sum \Delta H$ (m) | $\sum \Delta b_{\text{pred}}$ (mm) | MLCW observed (mm) |
|------|---------------------|-----------------------------------|-------------------|
| 2013 | +0.29 | +0.12 | −7.8 |
| 2014 | −1.45 | −0.62 | −5.2 |
| 2015 | +1.21 | +0.52 | −10.4 |
| 2016 | +1.52 | +0.66 | −8.3 |
| 2017 | −1.94 | −0.83 | −14.2 |
| 2018 | −1.98 | −0.85 | −15.1 |
| 2019 | +1.95 | +0.84 | −11.8 |
| 2020 | −2.19 | −0.94 | −12.5 |
| 2021 | +0.13 | −0.03 | −9.7 |
| 2022 | +0.63 | +0.27 | −8.1 |
| 2023 | −1.27 | −0.55 | −6.5 |
| 2024 | −0.32 | −0.14 | −3.2 |

The head rises and falls with the monsoon — the annual net $\sum \Delta H$ is near-zero over a full year because recharge approximately balances pumping withdrawal. The model's elastic prediction follows this oscillation: expansion in wet years, slight compaction in dry years, with near-zero net over a decade.

But the MLCW tells a different story: **−8 to −15 mm every year, regardless of whether head is rising or falling.** The compaction is monotonic.

### Why the Head Oscillation Does Not Mean Soil Rebound

The MLCW sensor is embedded in a clay-aquitard column that drains slowly. When the monsoon raises the piezometric head in the adjacent aquifer by 2 metres, the water does not instantly flow back into the clay pore spaces. The clay remains compressed. The head in the aquifer rises, but the effective stress in the clay — which controls compaction — does not fully recover because:

1. **Drainage lag**: Water must physically flow through low-permeability clay to re-saturate the pores. This takes months to years, not 5-day epochs.
2. **Plastic strain memory**: Once clay particles have rearranged under sustained load (the pre-2012 drawdown), the fabric does not "un-rearrange" when load is briefly reduced. The deformation is structurally permanent.
3. **Cumulative stress history**: The clay compaction at time $t$ is not a function of the instantaneous head $H(t)$, but of the entire stress path $\max(H(0), H(1), \ldots, H(t))$ that the sediment has experienced.

The incremental formulation $\Delta b = S_k \cdot \Delta H$ treats every 5-day head change as an independent elastic or inelastic event. It has no mechanism to carry forward the fact that the clay was already compacted in 2012 and continues compacting regardless of short-term head recovery.

### The GWL Data Gap — Missing the Legacy Stress Era

The TUKU deep aquifer wells were installed in August 2012:

| Layer | Well code | GWL data start | Pre-2012 epochs missing |
|-------|-----------|---------------|------------------------|
| F1 | 09050111 (HONGLUN) | 2000-01-01 | 0 (full coverage) |
| T1 | 09050111 (HONGLUN) | 2000-01-01 | 0 (full coverage) |
| F2 | 09050321 (TUKU) | **2012-08-01** | 623 of 1572 |
| F3 | 09050331 (TUKU) | **2012-08-12** | 625 of 1572 |
| F4 | 09080251 (LIUZHUANG) | 2000-01-01 | 0 (full coverage) |
| T2 | 09170121 (LUNZI) | 2000-01-01 | 81 scattered |

The heavy-pumping era that drove head through the preconsolidation threshold happened before monitoring began for F2 and F3. The wells only record the post-2012 "damage-is-already-done" head trajectory — a head already deep in the inelastic zone, oscillating around a new equilibrium but no longer setting fresh running minimums. With the Riley (1969) running-minimum formulation, the model correctly classifies only 2–36 epochs per layer as inelastic at 5-day cadence.

The Day 2 GPS mask fix (decoupling GPS from the Step 1 NaN mask) could not recover these epochs because the GWL data simply does not exist before 2012 for the two most important compacting layers. The binding constraint shifted from GPS to deep GWL availability.

---

## Model Comparison: Cumulative vs Incremental Domain

### The Incremental Solver (IHM-F v3, `ihmf_model_v3.py`) — FAILED

```
Δb_j(t) = S_j · ΔH_j(t − τ_j)    [5-day increments]
b_j(T)  = Σ S_j · ΔH_j            [cumulative via summation]
```

**Why it fails:** The summation of 5-day head increments erases the stress path memory. Each year's elastic oscillations (±2 m) approximately cancel. The net head decline over 10 years is only ~2–3 m, producing ~1–2 mm of cumulative compaction prediction. The actual cumulative head decline since the pre-pumping era is ~40 m, but this decline happened before monitoring began — it is not captured in the 5-day increment record.

### The Cumulative Stress-Strain Script (Script 12, `12_stress_strain_per_layer.py`) — SUCCEEDED

```
b_j(t) = S_{ke,j} · H_j(t − τ) + (S_{kv,j} − S_{ke,j}) · V_j(t)
V_j(t) = min(0, cummin(H_j) − h_{c,j})
```

**Why it succeeds:** The virgin exceedance term $V_j(t)$ preserves the running historical minimum of head. It carries forward the memory: "head has been as low as −15 m in the past, so any compaction that happened then is permanent." When head recovers to −13 m, $V_j$ does not decrease — the clay remains compacted. The cumulative formulation separates the elastic component (proportional to current $H$) from the inelastic component (proportional to permanent drawdown below $h_c$), using the maximum-stress history as the memory mechanism.

### Head-to-Head Comparison at TUKU

| Metric | Incremental (IHM-F v3) | Cumulative (Script 12) |
|--------|----------------------|----------------------|
| Domain | $\Delta H$, $\Delta b$ (5-day diffs) | $H$, $b$ (cumulative levels) |
| Stress memory | None — each epoch independent | Running minimum via $V(t)$ |
| n_inelastic F2 | 2 epochs | 169 epochs (H-based), 766 virgin |
| $R^2$ F2 | NaN (predicts ~1 mm, obs  −102 mm) | 0.845 |
| $R^2$ F4 | −3.94 (predicts ~2 mm, obs  −15 mm) | 0.546 |
| F1 $S_{skv}/S_{ske}$ ratio | Unable to compute (n_inelastic=36) | 9.1× (PASS) |
| T2 $S_{skv}/S_{ske}$ ratio | Unable to compute (n_inelastic=12) | 9.3× (PASS) |
| F4 $S_{skv}/S_{ske}$ ratio | Unable to compute (n_inelastic=11) | 17.3× (PASS) |

### Why the Cumulative Domain Preserves History

The key insight is in the virgin term definition:

$$V_j(t) = \min\left(0,\ \min_{\tau \le t} H_j(\tau) - h_{c,j}\right)$$

$V_j(t)$ is zero until head crosses below the preconsolidation threshold $h_c$. Once crossed, $V_j(t)$ tracks the deepest drawdown ever reached. When head recovers, $V_j$ stays at the historical minimum — it never decreases. This means:

- **Elastic response** ($S_{ke} \cdot H$): Reversible, proportional to current head. Handles seasonal oscillations correctly.
- **Inelastic response** ($(S_{kv} - S_{ke}) \cdot V$): Permanent, proportional to maximum historical drawdown. Never recovers, even when head rises.

The incremental formulation $\Delta b = S_k \cdot \Delta H$ has no equivalent to $V$. It treats every $\Delta H$ as a fresh event, asking "did this 5-day head drop cross a new low?" With only 2–36 such events in the monitoring record, there are too few inelastic increments to accumulate meaningful compaction.

---

## Formal Statement of Physical Domain Mismatch

> **The IHM-F v3 incremental solver operates on the first difference of head ($\Delta H$), which is a stationary signal dominated by seasonal oscillations. The MLCW compaction signal is a monotonic cumulative trend governed by the integral of maximum historical stress, not the derivative of current stress. The transformation from the cumulative conservation law (Terzaghi effective stress principle) to the incremental regression equation loses the integration constant — the pre-consolidation stress memory. This constant cannot be recovered from 5-day head differences, regardless of solver choice, regularization, or lag optimization.**

---

## What Was Tried (2026-06-08)

| Fix | Expected effect | Actual effect | Why insufficient |
|-----|----------------|---------------|-----------------|
| Day 1: Ratio gate bulk→specific | F2/T2 feasibility flips | T2 PASS, F2 FAIL (correct) | Gate now physically correct but model still can't pass it |
| Day 2: Decouple GPS from Step 1 NaN mask | 2003–2010 epochs recovered, n_inelastic → 100–400 | n_inelastic unchanged (11–36) | GWL data for F2/F3 starts 2012, not 2003 |
| Day 2: α_external = 0.625 bypass OLS | α fixed at empirical value | α = 0.625 preserved | Step 1 still fails regardless of Step 2 correctness |
| Day 2: NaN-resistant Step 2 OLS path | Graceful fallback for pre-GPS NaN | Works correctly | Step 1 cumulative predictions still 10–200× too small |

---

## Implications for the 7-Day Plan

1. **The IHM-F v3 incremental solver cannot proceed to batch at 37 stations.** The failure at TUKU is structural, not data-limited to one station. Every station where head oscillates seasonally around a near-stable level (the normal confined-aquifer regime) will exhibit the same cancellation.

2. **The cumulative stress-strain approach (Script 12) is the viable path.** It produced physically valid $S_{ske}$, $S_{skv}$ at TUKU for F1 (9.1×), T2 (9.3×), and F4 (17.3×). F2 and F3 failed not because the method was wrong, but because 93% of epochs are inelastic (collinear regressors) and F2/F3 GWL starts only in 2012.

3. **A tactical pivot is required.** Options:
   - **Cumulative-solver fork**: Replace `joint_solve_fixed_tau`'s per-epoch lsq_linear with the two-regressor NNLS from Script 12, operating on cumulative $H$ and $V$ arrays. The τ grid search moves from incremental MSE to cumulative domain.
   - **Per-layer approach**: Accept the Script 12 cumulative results as the calibration basis. Use the empirical α = 0.625 for surface scaling. Skip the walk-forward incremental prediction and instead forward-model cumulative compaction from cumulative head projections.
   - **Data-driven fallback**: Abandon the IHM-F inversion entirely. Use the Script 12 $S_{ske}$, $S_{skv}$ values where they pass gates (T2=8.4×, F4=10.8× at TUKU), and flag stations where they don't. Generate gap-fill as static spatial interpolation of validated parameters.

---

*This post-mortem is permanently locked in the repository as of 2026-06-08. It constitutes the formal circuit-breaker documentation required by the autonomous verification protocol. No attempt has been made to patch the incremental solver. The 8–355× prediction gap is a geomechanical domain mismatch, not a code defect.*

*Verification: `results/ihmf/v3/TUKU_gps_v3_results.json` (2026-06-08, α=0.625, n_inelastic=11–36, R²_MLCW_cum all negative/NaN).*
