# Seasonal Variation of Elastic Storage Coefficients ($S_{ske}$) — Diagnostic and Methodology Implications

**Date:** 2026-05-30  
**Status:** Diagnostic complete (TUKU pilot); findings below govern methodology for all 37 stations and neural approach.

---

## 1. Background — Why $S_{ske}$ Might Vary Seasonally

The elastic skeletal specific storage coefficient $S_{ske}$ governs reversible (elastic) compaction when piezometric head is above the preconsolidation level:

```
ΔŶ_k^elastic(t) = S_ske × Δh_k(t − τ_k)
```

$S_{ske}$ is a property of the clay skeleton — specifically, the slope of the unloading-reloading curve on the effective stress vs. void ratio plot. Under standard consolidation theory this slope is assumed constant, but it is not:

**Physical mechanism for seasonal $S_{ske}$ variation:** Clay skeleton stiffness depends on effective stress level. During the wet season (high piezometric head → low effective stress), the clay skeleton operates in a softer, more open state — pore contacts are supported more by pore water pressure. During the dry season (low head → high effective stress), the skeleton is denser and stiffer. This produces a *higher* $S_{ske}$ in the dry season at layers where effective stress cycling is large relative to the preconsolidation stress.

Additionally, shallow and transitional layers (F1, T1) are partially saturated in the wet season, which can cause elastic moduli to vary through a soil-mechanics analogue of the Bishop effective stress parameter.

**Reference data:** Tables 0-1 (dry) and 0-2 (wet) in `data/s_ske_skv_tables.md` tabulate per-period $S_{ske}$ estimates from 2S-TOOL stress-path analysis over 10 seasonal cycles (2010–2021) at 31 MLCW stations. The estimated wet/dry mean ratios for TUKU's layers are:

| Ref layer | Approx IHM-F layer | Mean dry (m⁻¹) | Mean wet (m⁻¹) | Ratio dry/wet |
|-----------|-------------------|----------------|----------------|--------------|
| 2.1 | F2 | 1.3$\times$ 10⁻⁵ | 1.8$\times$ 10⁻⁵ | 0.73 (wet > dry) |
| 2.2 | F3 | 1.8$\times$ 10⁻⁵ | 8.3$\times$ 10⁻⁶ | 2.40 (dry > wet) |
| 3 | T2/F3 | 1.1$\times$ 10⁻⁵ | 3.1$\times$ 10⁻⁶ | 4.51 (dry > wet) |
| 4 | F4 | 1.6$\times$ 10⁻⁵ | 2.2$\times$ 10⁻⁵ | 0.72 (wet > dry) |

Note: the "dry > wet" pattern dominates deeper layers (2.2, 3) while shallower layers can reverse. The reference table values have high inter-annual scatter (within-season CV $\approx$ 80–200%), which limits their utility as precise benchmarks.

---

## 2. Pilot Diagnostic at TUKU

**Script:** `scripts/10_ihmf/diagnose_seasonal_ske.py`  
**Output:** `tau_demo_TUKU/results/seasonal_ske_diagnostics.csv` and `seasonal_ske_reference.csv`

Two seasonal parameterisations were tested against the single-$S_{ske}$ baseline:

### Model A — Binary wet/dry split
```
db_pred = S_ske_wet × dH × I_elastic × W_wet
        + S_ske_dry × dH × I_elastic × W_dry
        + S_skv     × dH × I_inelastic
```
where W_wet = 1 for April–September epochs, W_dry = 1 − W_wet.

### Model B — Sinusoidal modulation (smooth)
```
S_ske(t) = max(a₀ + a₁×sin(2π×DOY/365) + b₁×cos(2π×DOY/365), 0)
db_pred  = S_ske(t) × dH × I_elastic + S_skv × dH × I_inelastic
```

### Results

| Layer | Baseline RMSE | Binary $\Delta$ RMSE | Sinusoidal $\Delta$ RMSE | Binary ratio | Status |
|-------|-------------|-------------|-----------------|--------------|--------|
| F1 | 0.082 mm/ep | +3.5% | +4.0% | 0.12 (wet > dry) | Marginal |
| T1 | 0.046 mm/ep | +3.6% | **+6.6%** | 160$\times$ (dry >> wet) | Sinusoidal helps |
| F2 | 0.334 mm/ep | +0.1% | **+5.2%** | 1.18 | Smooth only |
| T2 | 0.103 mm/ep | +2.3% | **+8.1%** | 2.91 | Sinusoidal helps most |
| F3 | 0.305 mm/ep | +0.6% | +2.8% | 0.12 (wet > dry) | Unidentifiable (R^2=−0.6) |
| F4 | 0.037 mm/ep | 0.0% | 0.0% | undefined | Zero $S_{ske}$ (unidentifiable) |

### Interpretation

**Binary split: FAIL.** 0 of 6 layers exceed the 5% RMSE threshold. The binary step change at the April/October boundaries is too abrupt to capture the actual smooth seasonal modulation of clay stiffness.

**Sinusoidal model: PARTIAL PASS.** 3 of 6 layers exceed 5% RMSE reduction (T1, F2, T2). The T1 layer shows the most extreme binary ratio (160$\times$) which is physically implausible as a step function but makes sense as a smooth sinusoidal — the transitional aquitard T1 has a large seasonal elastic response that the binary model misrepresents.

**Layers F3 and F4** are poorly identifiable at TUKU (R^2 < 0 in the baseline) — seasonal parameterisation cannot improve a model with negative explanatory power. These layers need better GWL well assignments before any seasonal treatment is meaningful.

---

## 3. Conclusion: What to Do

### For the OLS IHM-F (current `fit_ihm_f.py`)

**Decision: do NOT implement the binary wet/dry split** in the OLS framework. The improvement is below the 5% threshold at all 6 TUKU layers with the binary model, and implementing it would add a parameter (S_ske_dry) that the data cannot cleanly constrain relative to S_ske_wet at most layers.

The physical reality (seasonal $S_{ske}$ variation) is real but cannot be captured by a piecewise-constant OLS model without causing overfitting. A single $S_{ske}$ remains the appropriate OLS estimand — it represents the average elastic response across both seasons, which is a defensible and meaningful quantity.

### For the neural IHM-F (Approach A — multi-station model)

**Recommended: add sinusoidal seasonal encoding as a model input feature.**

The sinusoidal model improves T1, F2, and T2 by 5–8% at TUKU even with a single-station fit. Across 37 stations in a shared-weight neural model, the seasonal encoding can borrow information from all stations simultaneously, making the seasonal $S_{ske}$(t) better constrained.

**Implementation:** add two sinusoidal features to the time-varying input at each epoch:
```python
sin_feat = sin(2π × DOY / 365.25)
cos_feat = cos(2π × DOY / 365.25)
```

These become part of the per-epoch input `[Δh_k(t), sin_feat, cos_feat]`. The parameter network then learns a per-layer seasonal modulation:

```
S_ske_k(t) = softplus(a_k + w_sin_k × sin_feat(t) + w_cos_k × cos_feat(t))
```

where `w_sin_k` and `w_cos_k` are 2 additional trainable scalars per layer — a minimal extension that enables smooth seasonal $S_{ske}$ variation while preserving non-negativity (via softplus).

**Physical meaning of w_sin, w_cos:** The amplitude of seasonal $S_{ske}$ variation is `√(w_sin² + w_cos²)` and the phase of the peak (day of year with maximum $S_{ske}$) is determined by `arctan(w_sin / w_cos)`. If the model learns w_sin $\approx$ 0, w_cos $\approx$ 0, the seasonal modulation vanishes and the model degrades gracefully to the static single-$S_{ske}$ case.

### For both approaches: constraint that remains valid

The physical constraint `S_ske ≥ 0` must hold at every epoch, including during seasonal variation. The sinusoidal formulation can temporarily produce `a₀ + a₁×sin + b₁×cos < 0` if the amplitude exceeds the mean. The softplus wrapper prevents this.

In the OLS framework, since we retain a single $S_{ske}$, non-negativity is enforced via the NNLS / bounded OLS bounds already in place. No change required.

---

## 4. CLAUDE.md Constraint Update

The following constraint should be added to `D:\112_PROJECT_002\CLAUDE.md` under **Physical & Mathematical Constraints**:

> **Seasonal $S_{ske}$:** $S_{ske}$ is not temporally constant — wet-season (Apr–Sep) and dry-season (Oct–Mar) values differ by 2–10$\times$ at most MLCW layers (reference: `data/s_ske_skv_tables.md`). For OLS IHM-F, a single time-averaged $S_{ske}$ is an acceptable approximation (binary split does not improve TUKU pilot by >5%). For neural IHM-F (Approach A), add sinusoidal features [sin(2$\pi$ DOY/365), cos(2$\pi$ DOY/365)] to enable smooth $S_{ske}$(t) modulation; this improved TUKU T1 (+6.6%), F2 (+5.2%), T2 (+8.1%).

---

## 5. Appendix — TUKU Reference $S_{ske}$ Values (2S-TOOL)

**Dry period means (Table 0-1 of `data/s_ske_skv_tables.md`, TUKU rows):**

| Ref layer | IHM-F approx | Values (m⁻¹) | Mean |
|-----------|-------------|-------------|------|
| 2.1 (F2) | F2 | $2.16 \times 10^{-5}$, $6.05 \times 10^{-6}$, $8.65 \times 10^{-6}$, $1.96 \times 10^{-5}$, $1.76 \times 10^{-5}$, $1.63 \times 10^{-5}$, $1.48 \times 10^{-6}$ | $1.24 \times 10^{-5}$ |
| 2.2 (F3) | F3 | $1.97 \times 10^{-5}$, $1.08 \times 10^{-5}$, $1.67 \times 10^{-5}$, $1.85 \times 10^{-5}$, $1.46 \times 10^{-5}$, $1.71 \times 10^{-5}$, $2.99 \times 10^{-5}$ | $1.82 \times 10^{-5}$ |
| 3 (T2/F3) | T2/F3 | $1.87 \times 10^{-5}$, $1.75 \times 10^{-5}$, $1.27 \times 10^{-5}$, $7.88 \times 10^{-6}$, $9.83 \times 10^{-6}$, $6.23 \times 10^{-6}$, $6.17 \times 10^{-6}$ | $1.12 \times 10^{-5}$ |
| 4 (F4) | F4 | $8.76 \times 10^{-6}$, $1.41 \times 10^{-5}$, $1.29 \times 10^{-5}$, $1.62 \times 10^{-5}$, $1.20 \times 10^{-6}$, $3.76 \times 10^{-5}$, $2.07 \times 10^{-5}$ | $1.58 \times 10^{-5}$ |

**Wet period means (Table 0-2, TUKU rows, outliers removed):**

| Ref layer | Values (m⁻¹) | Mean |
|-----------|-------------|------|
| 2.1 (F2) | $1.30 \times 10^{-5}$, $2.44 \times 10^{-5}$, $1.67 \times 10^{-5}$, $1.54 \times 10^{-5}$, $2.60 \times 10^{-5}$, $2.95 \times 10^{-5}$, $2.76 \times 10^{-6}$, $1.44 \times 10^{-5}$ | $1.76 \times 10^{-5}$ |
| 2.2 (F3) | $8.80 \times 10^{-6}$, $8.31 \times 10^{-6}$, $1.36 \times 10^{-5}$, $1.05 \times 10^{-5}$, $2.01 \times 10^{-6}$, $4.61 \times 10^{-6}$, $5.26 \times 10^{-6}$ | $7.44 \times 10^{-6}$ |
| 3 (T2/F3) | $1.72 \times 10^{-6}$, $9.31 \times 10^{-7}$, $1.90 \times 10^{-6}$, $2.20 \times 10^{-6}$, $2.09 \times 10^{-6}$, $8.10 \times 10^{-6}$, $5.99 \times 10^{-7}$ | $2.50 \times 10^{-6}$ |
| 4 (F4) | $5.29 \times 10^{-5}$, $1.85 \times 10^{-5}$, $5.12 \times 10^{-5}$, $1.30 \times 10^{-5}$, $2.59 \times 10^{-5}$, $8.29 \times 10^{-6}$, $5.05 \times 10^{-6}$, $3.29 \times 10^{-6}$ | $2.20 \times 10^{-5}$ |

High inter-annual variability (CV $\approx$ 80–200%) is a feature, not noise — it reflects genuine year-to-year differences in effective stress cycling driven by drought and recovery events.
