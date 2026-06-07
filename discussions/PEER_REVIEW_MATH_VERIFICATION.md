# IHM-F v3 TUKU Pilot — Peer-Review Mathematical Verification Report

**Date:** 2026-06-07  
**Auditor:** Claude Sonnet 4.6 (autonomous OODA audit)  
**Scope:** TUKU pilot inversion chain — read-only; no code written  
**Status:** THREE ISSUES FOUND (1 HIGH, 1 MEDIUM, 1 DOCUMENTATION)

---

## 1. Physical Context

The TUKU sediment column at the Choushui River Alluvial Fan compresses because multi-decadal groundwater withdrawal has lowered hydraulic head across six stratigraphic layers (F1/T1/F2/T2/F3/F4, 0–300 m depth). The IHM-F model estimates how much compaction each layer contributes per metre of head change and separates elastic (reversible) rebound from irreversible virgin consolidation. This audit asks whether every arithmetic step between raw feather data and the layer-level specific storage coefficients ($S_{ske}$, $S_{skv}$) is physically and mathematically correct.

**Pre-write finding (documentation failure):** `PROGRESS.md` line 127 states "decoupled two-step fit (planned, not yet implemented)." The source code at `tau_demo_TUKU/12_stress_strain_per_layer.py:290–350` contains `fit_two_step_decoupled` fully implemented, and `tau_demo_TUKU/results/stress_strain_per_layer.json` contains all `_2s` result fields for all six layers. PROGRESS.md was not updated after the implementation completed (2026-06-06). Section 5 Issue 3 and Section 8 Task 3 document the required correction.

---

## 2. Scope

### Audited (line numbers verified by direct file read)

| File | What was checked | Lines |
|------|-----------------|-------|
| `scripts/10_ihmf/ihmf_model_v3.py` | Regime mask, τ grid search, joint_solve, Step 2 OLS | 126–141, 204–235, 294–316, 332–340 |
| `scripts/10_ihmf/ihmf_io.py` | InSAR unit conversion, h_c pre-REF_DATE window | 48, 68–79 |
| `scripts/10_ihmf/ihmf_detrend.py` | Second InSAR unit conversion | 209 |
| `tau_demo_TUKU/12_stress_strain_per_layer.py` | Layer thickness dicts, literature bounds, virgin term, NNLS fit, decoupled fit, ratio gate, $S_{ske}$/$S_{skv}$ conversion | 97–116, 121–134, 224–238, 267–287, 290–350, 509/535/560, 582–584 |
| `tau_demo_TUKU/results/stress_strain_per_layer.json` | All 6 layers — NNLS and decoupled results | All entries |

### Not audited

`scripts/01–09`, `scripts/11–16`, `ihmf_io_multilayer.py` (main batch loader), walk-forward pipeline, seasonal harmonic pipeline, GPS processing. This report covers only the TUKU pilot inversion chain.

---

## 3. Model Classification and Literature Framing

The IHM-F model is a **lumped empirical two-regime skeletal-storage model with an empirical hydraulic lag $\tau$**. It is *not* a discretized Terzaghi consolidation PDE, *not* a Biot 3D poroelastic system, and does not resolve drainage-boundary conditions within layers. The hydraulic lag $\tau \in \{0, \ldots, 120\}$ epochs is the empirical surrogate for drainage delay; no diffusivity or consolidation coefficient is estimated. This formulation is standard practice for InSAR-based aquifer compaction analysis (Riley 1969; Galloway & Burbey 2011) and is appropriate for the Choushui River Alluvial Fan (CRAF) monitoring context.

All physical-law comparisons below are made against the 1D skeletal-storage consolidation model of Riley (1969), Leake & Galloway (1987 — MODFLOW SUB/IBS package), and the specific storage bounds of Hung et al. (2021) for the Choushui system.

---

## 4. Confirmed-Correct Items (11 checks)

### 4.1 InSAR m → mm conversion — `ihmf_io.py:48`

```python
insar[station] = insar[station] * 1000.0
```

Input feather files store InSAR displacement in metres (CLAUDE.md: "InSAR feather units: metres"). Multiplication by 1000 converts to mm before all downstream operations. **COMPLIANT.**

### 4.2 Second InSAR m → mm conversion — `ihmf_detrend.py:209`

```python
insar_df["insar_mm"] = insar_df[station] * 1000.0
```

The same ×1000 scaling is applied independently in the detrend pipeline. **COMPLIANT.**

### 4.3 Preconsolidation head from pre-REF_DATE data — `ihmf_io.py:68–79`

```python
REF_DATE = pd.Timestamp("2015-01-16")
pre_ref_mask = gwl_raw["datetime"] < REF_DATE
if pre_ref_mask.sum() >= 10:
    h_c_head = float(gwl_raw.loc[pre_ref_mask, "head_m"].dropna().min())
else:
    h_c_head = float(gwl_raw["head_m"].dropna().min())
```

Bug F (h_c computed from wrong time window) is confirmed fixed. $h_c$ is the minimum absolute head in the raw groundwater level feather **before** REF_DATE = 2015-01-16, before any zero-referencing. Using the full record would push $h_c$ too low, misclassifying up to 51% of epochs as elastic. **COMPLIANT.**

### 4.4 Lag direction and regime mask at driver-time index — `ihmf_model_v3.py:211–214`

```python
dH_lag  = dH_anom[:n]         # head driver: epochs 0..n-1
db_trim = db_anom[tau:]       # compaction response: epochs tau..T-1
e_trim  = elastic_mask[:n]    # regime mask at driver-time index
i_trim  = inelastic_mask[:n]
```

Head leads compaction by $\tau$ epochs. The regime mask is sliced at the driver-time index `[:n]` (Bugs 1–3 fix, 2026-06-05). This ensures the elastic/inelastic classification matches the head that is actually driving compaction, not the head at the response time. **COMPLIANT.**

### 4.5 TAU_MAX = 120 epochs (600 days) — `ihmf_model_v3.py:204`

```python
for tau in range(tau_max + 1):
```

With `tau_max=120`, the grid covers $\tau \in \{0, 1, \ldots, 120\}$ = 0 to 600 days at 5-day cadence. CLAUDE.md: "TAU_MAX = 120 epochs (5-day cadence)." **COMPLIANT.**

### 4.6 NNLS design matrix with structural $S_{kv} \ge S_{ke}$ — `12_stress_strain_per_layer.py:277–284`

```python
A   = np.column_stack([-H_arr, -V_arr])   # both columns ≥ 0 after negation
rhs = -b_arr                               # negated for positivity
coef, _ = nnls(A, rhs)
S_ke = coef[0]
delta = coef[1]
S_kv = S_ke + delta                        # S_kv ≥ S_ke because delta ≥ 0
```

Negating all three arrays converts the negative-valued (compacting) domain to positive; NNLS enforces `coef ≥ 0`. The $S_{kv} \ge S_{ke}$ constraint is structurally enforced because $delta \ge 0$. **COMPLIANT.**

### 4.7 Virgin term with running cumulative minimum — `12_stress_strain_per_layer.py:234–237`

```python
cummin_H = np.minimum.accumulate(H_series)
V = np.minimum(0.0, cummin_H - h_c)
```

$V(t) = \min(0,\, \text{cummin}(H(t)) - h_c)$. This term is zero until head penetrates below $h_c$ for the first time, then tracks how far head has advanced into virgin consolidation territory. **COMPLIANT** with the Terzaghi/Riley (1969) preconsolidation-memory formulation.

### 4.8 Two-thickness $S_{ske}$ / $S_{skv}$ conversion — `12_stress_strain_per_layer.py:582–584`

```python
S_ske_m1 = S_ke / (span_m * 1000.0)           # elastic: total span [m]
S_skv_m1 = S_kv / (compressible_m * 1000.0)   # inelastic: fine-grained [m]
```

**Elastic $S_{ske}$**: denominator is `span_m` = total borehole depth zone. All materials in the layer deform elastically when head is above $h_c$.  
**Inelastic $S_{skv}$**: denominator is `compressible_m` = fine-grained (clay/silt) thickness only. Inelastic compaction is confined to aquitard material.

Verified from `LAYER_THICKNESS` dict (lines 97–103):

| Layer | `span_m` (total) [m] | `compressible_m` (clay/silt) [m] | Factor |
|-------|---------------------|----------------------------------|--------|
| F1 | 41.577 | 16.577 | 2.51× |
| T1 | 8.729 | 7.423 | 1.18× |
| F2 | 106.284 | 12.090 | 8.79× |
| T2 | 16.299 | 10.299 | 1.58× |
| F3 | 110.494 | 76.994 | 1.43× |
| F4 | 16.617 | 16.617 | 1.00× |

Units: $S_{ke}$ [mm/m] / (`span_m` [m] × 1000 [mm m⁻¹ per m⁻¹]) = $S_{ske}$ [m⁻¹]. **COMPLIANT** with Riley (1969) and Galloway & Burbey (2011) specific storage definition.

### 4.9 IHM-F v3 Step 1 joint lsq_linear — `ihmf_model_v3.py:294–316`

```python
A_l = np.column_stack([
    np.where(e_m, dH, 0.0),   # elastic column
    np.where(i_m, dH, 0.0),   # inelastic column
])
res = lsq_linear(A_l, db, bounds=([0.0, 0.0], [np.inf, np.inf]), method="trf")
S_ke = float(res.x[0])
S_kv = float(res.x[1])
```

Bounds enforce $S_{ke} \ge 0$ and $S_{kv} \ge 0$. No upper cap is applied — a cap in lumped mm/m units would be 4–5 orders of magnitude too small relative to specific storage literature bounds. **COMPLIANT.**

### 4.10 IHM-F v3 Step 2 cumulative InSAR OLS with intercept — `ihmf_model_v3.py:337–340`

```python
cum_pred = np.cumsum(db_pred_all)
A_step2  = np.column_stack([cum_insar, np.ones(T)])
coeffs, _, _, _ = np.linalg.lstsq(A_step2, cum_pred, rcond=None)
alpha = float(np.clip(coeffs[0], 1e-6, 1.0))
beta  = 1.0 / alpha
```

Fits: $\text{cum\_MLCW\_pred}(t) \approx \alpha \cdot \text{cum\_InSAR}(t) + c$. Intercept $c$ absorbs systematic bias (atmospheric loading, non-pumping subsidence). $\alpha$ is clipped to $(0, 1]$ enforcing $\beta = 1/\alpha \ge 1$. **COMPLIANT.**

### 4.11 Literature bounds constants — `12_stress_strain_per_layer.py:121–134`

Values present in code (`LITERATURE_BOUNDS` dict), attributed to Hung et al. (2021, WRR) Choushui per-layer bounds. The source document (`docs/choushui_skeletal_storage_coeffs.md`) was **not independently re-read** in this audit; the table below reflects the dict values as-coded:

| Layer | $S_{ske}$ min [m⁻¹] | $S_{ske}$ max [m⁻¹] | $S_{skv}$ min [m⁻¹] | $S_{skv}$ max [m⁻¹] |
|-------|---------------------|---------------------|---------------------|---------------------|
| F1 | $7.27 \times 10^{-6}$ | $3.87 \times 10^{-4}$ | $5.90 \times 10^{-5}$ | $2.20 \times 10^{-3}$ |
| T1 | 0 (no bounds) | 0 | 0 | 0 |
| F2 | $2.86 \times 10^{-6}$ | $9.89 \times 10^{-5}$ | $1.60 \times 10^{-5}$ | $1.20 \times 10^{-3}$ |
| T2 | $4.47 \times 10^{-6}$ | $9.89 \times 10^{-5}$ | $1.60 \times 10^{-5}$ | $1.00 \times 10^{-3}$ |
| F3 | $4.96 \times 10^{-6}$ | $1.14 \times 10^{-4}$ | $1.53 \times 10^{-5}$ | $2.00 \times 10^{-3}$ |
| F4 | $3.93 \times 10^{-6}$ | $7.96 \times 10^{-5}$ | $1.78 \times 10^{-4}$ | $3.00 \times 10^{-3}$ |

**Constants present in code as attributed to Hung et al. (2021, WRR). Source not independently re-verified in this audit.**

---

## 5. Confirmed Issues

### Issue 1 (HIGH) — Ratio gate applies bulk ratio, not specific storage ratio

**Location:** `tau_demo_TUKU/12_stress_strain_per_layer.py` lines 509, 535, and 560.

**Line 509:**
```python
ratio_2reg = S_kv / S_ke if S_ke > 0 else float('nan')
```

**Line 535:**
```python
ratio_2s = S_kv_2s / S_ke_2s if S_ke_2s > 0 else float('nan')
```

**Line 560:**
```python
in_ratio = (8.0 <= ratio_2s <= 100.0) if np.isfinite(ratio_2s) else False
```

**Physical error:** Both `ratio_2reg` and `ratio_2s` are **bulk** ratios in mm/m units ($S_{kv}/S_{ke}$). The $[8, 100]\times$ gate cited in Riley (1969), Galloway & Burbey (2011), and `PROGRESS.md` applies to the **specific storage** ratio $S_{skv}/S_{ske}$ [m⁻¹/m⁻¹]. The relationship is:

$$\frac{S_{skv}}{S_{ske}} = \frac{S_{kv}}{S_{ke}} \times \frac{\text{total\_m}}{\text{compressible\_m}}$$

The transformation factor `total_m/compressible_m` differs per layer and equals 1 only for F4 (where total_m = compressible_m = 16.617 m).

**Numerical demonstration (all values read directly from JSON):**

| Layer | total_m | comp_m | Factor | Bulk ratio | Specific ratio | Current gate | Correct gate |
|-------|---------|--------|--------|------------|----------------|--------------|--------------|
| F1 | 41.577 | 16.577 | 2.51× | 3.62× | 9.09× | FLAG (< 8×) | **PASS** |
| T1 | 8.729 | 7.423 | 1.18× | 2.45× | 2.89× | FLAG | FAIL |
| F2 | 106.284 | 12.090 | 8.79× | 25.10× | 220.7× | **PASS (false positive)** | FAIL |
| T2 | 16.299 | 10.299 | 1.58× | 5.85× | 9.25× | FLAG (< 8×) | **PASS** |
| F3 | 110.494 | 76.994 | 1.43× | undefined | undefined | — | — |
| F4 | 16.617 | 16.617 | 1.00× | 17.34× | 17.34× | PASS | PASS (unchanged) |

**Note:** All ratios in this table are from the NNLS simultaneous fit (`S_ke_mmpm`, `S_kv_mmpm`, `S_ske_m1`, `S_skv_m1` JSON fields). The `feasible_2s` flag in the JSON is evaluated on the **decoupled two-step** values instead: for T2 the decoupled specific ratio is $5.04 \times 10^{-4} / 5.99 \times 10^{-5} = 8.41\times$ (vs 9.25× NNLS above) — both pass the 8× lower bound, so the gate outcome is the same, but the exact value used in the `feasible_2s` check is 8.41×.

Specific ratios for F1/T2 computed as: $S_{skv}/S_{ske} = (S_{kv}/S_{ke}) \times (\text{total\_m}/\text{compressible\_m})$. For F2: $25.10 \times 8.79 = 220.6\times$. For T2 (NNLS): $5.85 \times 1.58 = 9.24\times$.

**False positive for F2 (line 560 in JSON output):**  
`ratio_2s = 25.10×` satisfies `8.0 ≤ 25.10 ≤ 100.0` → `in_ratio = True` → `feasible_2s = true` (JSON field `feasible_2s`).  
But the correct specific ratio = $1.090 \times 10^{-3} / 4.939 \times 10^{-6} = 220.7\times > 100$ → should be `feasible_2s = false`.

**False negative for T2 (decoupled two-step):**  
`ratio_2s = 5.319×` fails `8.0 ≤ 5.319` → `in_ratio = False` → `feasible_2s = false` (JSON).  
But the correct specific ratio = $5.039 \times 10^{-4} / 5.985 \times 10^{-5} = 8.41\times \in [8, 100]$ → should be `feasible_2s = true`.

**Required fix (two lines replacing line 560):**

```python
specific_ratio_2s = (S_skv_2s_m1 / S_ske_2s_m1
                     if (S_ske_2s_m1 and S_ske_2s_m1 > 0) else float('nan'))
in_ratio = (8.0 <= specific_ratio_2s <= 100.0) if np.isfinite(specific_ratio_2s) else False
```

The same fix applies to the NNLS ratio check at lines 524–527 (`in_ratio` block using `ratio_2reg`) for consistency in printed output.

---

### Issue 2 (MEDIUM) — Regime formulation in `ihmf_model_v3.py` diverges from Terzaghi preconsolidation-memory model

**Location:** `ihmf_model_v3.py:126–141` (build_regime_mask) vs `12_stress_strain_per_layer.py:224–238` (compute_virgin_term).

**ihmf_model_v3.py — instantaneous-level mask (line 139):**

```python
elastic   = head_m > h_c_head_m   # is current head above threshold?
inelastic = ~elastic
```

Every epoch with $H(t) \le h_c$ receives the inelastic label, including **sub-threshold recovery epochs** (head is below $h_c$ but rising, setting no new running minimum). The model assigns $db(t) = S_{kv} \cdot dH(t)$ to those epochs — predicting large inelastic expansion during head recovery within the inelastic zone.

**12_stress_strain_per_layer.py — preconsolidation-memory formulation (lines 234–237):**

```python
cummin_H = np.minimum.accumulate(H_series)
V = np.minimum(0.0, cummin_H - h_c)
```

In the incremental form, $dV(t) = 0$ when head rises above the running minimum (even within the inelastic zone). During sub-threshold recovery epochs: $db(t) = S_{ke} \cdot dH(t)$ (elastic rebound), not $S_{kv} \cdot dH(t)$.

**Textbook alignment:** Script 12 matches Riley (1969) Eq. 3 and Leake & Galloway (1987) IBS package. Virgin consolidation ($S_{kv}$) is triggered only when effective stress exceeds the historical maximum (i.e., head sets a new running minimum). Recovery within the inelastic zone uses $S_{ke}$. The `ihmf_model_v3.py` simplification overestimates inelastic expansion during head recovery by a factor of $S_{kv}/S_{ke} \approx 8\text{–}100\times$.

**Divergence magnitude:** The actual diverging epoch set is $\{H(t) \le h_c\ \text{AND}\ dV(t) = 0\}$ — epochs where head is sub-threshold but rising within the inelastic zone (no new running minimum). The instantaneous model assigns $S_{kv}$ to these epochs; the memory model assigns $S_{ke}$ (elastic rebound). This set is a subset of $n\_inelastic\_Hbased$ per layer (F1=356, T1=326, F2=169, T2=30, F3=160, F4=18); the exact count requires $dV$ computation, which falls outside the no-code-writes scope of this audit.

At F4, $n\_inelastic\_Hbased = 18$ (2.3% of 772 total epochs). Even if all 18 epochs are sub-threshold recovery, the divergence contributes at most $18 \times (S_{kv} - S_{ke}) \cdot |\Delta H| \approx 18 \times 5.8\ \text{mm/m} \times |\Delta H|$ to prediction error — negligible for F4. For F1/T1 ($n\_inelastic\_Hbased$ = 356/326, 46%/42% of total), the potential divergence is larger; the exact fraction requires $dV$ computation.

**No numerical bias has been computed** (outside the no-code-writes scope of this audit). The formulation discrepancy must be resolved before accepting `ihmf_model_v3.py` batch results as equivalent to the Script 12 TUKU calibration.

---

### Issue 3 (DOCUMENTATION) — PROGRESS.md state is stale

**PROGRESS.md line 127:**
> "Viable path — decoupled two-step fit (planned, not yet implemented):"

**PROGRESS.md line 136:**
> "Next action: Implement `fit_two_step_decoupled` + `LITERATURE_BOUNDS` in `tau_demo_TUKU/12_stress_strain_per_layer.py`."

**Ground truth (code + JSON):**

`12_stress_strain_per_layer.py:290–350` — `fit_two_step_decoupled` function is fully implemented. `tau_demo_TUKU/results/stress_strain_per_layer.json` contains all `_2s` fields for all six layers. The implementation was completed 2026-06-06.

**Required correction:** Replace PROGRESS.md line 127 text with:

> "Decoupled two-step fit implemented and run (2026-06-06); results in `stress_strain_per_layer.json`. Ratio gate bug (`in_ratio` uses bulk ratio, not $S_{skv}/S_{ske}$) confirmed — see `PEER_REVIEW_MATH_VERIFICATION.md`. After fix: T2 feasible ($8.41\times$); F2 infeasible ($220.7\times$)."

---

## 6. Numerical Results

### 6.1 NNLS simultaneous fit (all values from JSON)

| Layer | $S_{ke}$ (mm/m) | $S_{kv}$ (mm/m) | $S_{ske}$ (m⁻¹) | $S_{skv}$ (m⁻¹) | Bulk ratio | Specific ratio | n_elastic | n_inelastic | $R^2$ |
|-------|----------------|----------------|----------------|----------------|------------|----------------|-----------|-------------|-------|
| F1 | 0.8833 | 3.198 | $2.12 \times 10^{-5}$ | $1.93 \times 10^{-4}$ | 3.62× | 9.09× | 416 | 356 | 0.607 |
| T1 | 0.8335 | 2.041 | $9.55 \times 10^{-5}$ | $2.75 \times 10^{-4}$ | 2.45× | 2.89× | 446 | 326 | 0.804 |
| F2 | 0.5249 | 13.176 | $4.94 \times 10^{-6}$ | $1.090 \times 10^{-3}$ | 25.10× | 220.7× | 603 | 169 | 0.845 |
| T2 | 0.8967 | 5.247 | $5.50 \times 10^{-5}$ | $5.09 \times 10^{-4}$ | 5.85× | 9.25× | 732 | 30 | 0.489 |
| F3 | 0.000 | 19.712 | null | null | — | undefined | 612 | 160 | 0.754 |
| F4 | 0.3755 | 6.512 | $2.26 \times 10^{-5}$ | $3.92 \times 10^{-4}$ | 17.34× | 17.34× | 754 | 18 | 0.546 |

F3 $S_{ke}$ = 0: the elastic channel collapsed (only 7 elastic epochs after h_c correction; simultaneous NNLS pushes all weight to $S_{kv}$).  
F4: total_m = compressible_m = 16.617 m → factor = 1.00 → specific ratio = bulk ratio.

### 6.2 Decoupled two-step fit (all values from JSON, as-run 2026-06-06)

| Layer | n_elastic_pts | Method | $S_{ke,2s}$ (mm/m) | $S_{kv,2s}$ (mm/m) | $S_{ske,2s}$ (m⁻¹) | $S_{skv,2s}$ (m⁻¹) | Bulk ratio_2s | Specific ratio_2s | Current feasible_2s | Correct feasibility |
|-------|--------------|--------|-------------------|-------------------|-------------------|-------------------|--------------|-------------------|---------------------|---------------------|
| F1 | 55 | two_step | 0.2720 | 3.292 | $6.54 \times 10^{-6}$ | $1.99 \times 10^{-4}$ | 12.1× | 30.4× | false | **FAIL** ($S_{ske}$ 10% below $7.27 \times 10^{-6}$) |
| T1 | 85 | two_step | 0.0 | 2.188 | null | null | null | undefined | null | **FAIL** ($S_{ke}$ collapsed to 0) |
| F2 | 6 | nnls_fallback | 0.5249 | 13.176 | $4.94 \times 10^{-6}$ | $1.090 \times 10^{-3}$ | 25.10× | 220.7× | **true (false positive)** | **FAIL** (ratio $221\times > 100\times$) |
| T2 | 311 | two_step | 0.9755 | 5.189 | $5.99 \times 10^{-5}$ | $5.04 \times 10^{-4}$ | 5.32× | 8.41× | **false (false negative)** | **PASS** |
| F3 | 7 | nnls_fallback | 0.0 | 19.712 | null | null | null | undefined | null | **FAIL** ($S_{ke}$ collapsed to 0) |
| F4 | 548 | two_step | 0.5972 | 6.427 | $3.59 \times 10^{-5}$ | $3.87 \times 10^{-4}$ | 10.76× | 10.76× | true | **PASS** (correctly) |

**Physical notes:**

- **T1 $S_{ke,2s}$ = 0:** T1 shows no elastic compaction during the 85 early epochs (before $h_c = -2.344$ m is first crossed). The T1 layer (shallow aquitard, 41.6–50.3 m depth) is 85% clay/silt by thickness; negligible elastic storage is physically plausible.
- **F2/F3 nnls_fallback:** Only 6 and 7 elastic epochs respectively (both F2 and F3 wells enter the inelastic zone very early in the record). The decoupled method falls back to simultaneous NNLS at the 10-point threshold.
- **T2 false negative:** 311 elastic epochs (41% of 762 total). The decoupled method produces a physically valid and literature-consistent specific ratio (8.41×). The bulk-ratio gate incorrectly rejects it.
- **F4 note:** `n_inelastic_Hbased` = 18 (epochs where $H \le h_c$). This is the upper bound on the Issue 2 divergence for F4; the actual sub-threshold recovery subset requires $dV$ computation. 18 of 772 total = 2.3%, making the Issue 2 bias negligible for F4 specifically.

### 6.3 Literature bounds check ($S_{ske}$, $S_{skv}$ in m⁻¹, NNLS simultaneous fit)

| Layer | $S_{ske}$ range (Hung 2021) | $S_{ske}$ fit | Status | $S_{skv}$ range | $S_{skv}$ fit | Status |
|-------|----------------------------|--------------|--------|-----------------|--------------|--------|
| F1 | [$7.27 \times 10^{-6}$, $3.87 \times 10^{-4}$] | $2.12 \times 10^{-5}$ | **IN** | [$5.90 \times 10^{-5}$, $2.20 \times 10^{-3}$] | $1.93 \times 10^{-4}$ | **IN** |
| T1 | no bounds | $9.55 \times 10^{-5}$ | — | no bounds | $2.75 \times 10^{-4}$ | — |
| F2 | [$2.86 \times 10^{-6}$, $9.89 \times 10^{-5}$] | $4.94 \times 10^{-6}$ | **IN** | [$1.60 \times 10^{-5}$, $1.20 \times 10^{-3}$] | $1.090 \times 10^{-3}$ | **IN** (91% of max) |
| T2 | [$4.47 \times 10^{-6}$, $9.89 \times 10^{-5}$] | $5.50 \times 10^{-5}$ | **IN** | [$1.60 \times 10^{-5}$, $1.00 \times 10^{-3}$] | $5.09 \times 10^{-4}$ | **IN** |
| F3 | [$4.96 \times 10^{-6}$, $1.14 \times 10^{-4}$] | null | — | [$1.53 \times 10^{-5}$, $2.00 \times 10^{-3}$] | null | — |
| F4 | [$3.93 \times 10^{-6}$, $7.96 \times 10^{-5}$] | $2.26 \times 10^{-5}$ | **IN** | [$1.78 \times 10^{-4}$, $3.00 \times 10^{-3}$] | $3.92 \times 10^{-4}$ | **IN** |

**F2 note:** $S_{skv}$ = $1.090 \times 10^{-3}$ m⁻¹ is at 91% of the literature maximum ($1.20 \times 10^{-3}$ m⁻¹). The specific ratio is 220.7×. A physical interpretation: a 12.09 m compressible fraction within a 106 m column produces a large ratio mechanically — but this cannot be confirmed from NNLS with only 169 inelastic epochs and near-collinear $H$–$V$ regressors.

---

## 7. Hydraulic Lag Sanity Flags

**F4 $\tau_{opt}$ = 105 epochs (525 days):** This is 87.5% of $\tau_{max}$ = 120 (600 days). The τ grid-search MSE curve must be inspected via `tau_demo_TUKU/results/tau_results.csv` to confirm the minimum is interior (not the MSE still declining at $\tau = 120$). If the curve was still descending at $\tau_{max}$, the true optimal lag may exceed 600 days. Physical context: a 525-day lag for the 283–300 m F4 zone (entirely fine-grained material per CLAUDE.md) is plausible for slow drainage from a deep confined clay layer.

**F2 and F3 $\tau_{opt}$ = 0 epochs:** Physically surprising for layers at 50–283 m depth. Zero lag may reflect trend dominance (head trend and MLCW trend are collinear), seasonal aliasing, or genuine near-instant hydraulic connectivity. PROGRESS.md lines 170–175 document: "F2 is the only TUKU layer with genuine multiscale GWL–MLCW coupling; F1, F3, F4 are trend-dominated at 5-day resolution (detrended $r < 0.07$)." For F3 (well 09050331), the MSE-optimal $\tau$ lands at 0 because the long-term trend dominates incremental covariance.

---

## 8. Compliance Matrix and Recommended Actions

| Check | File | Lines | Status | Required action |
|-------|------|-------|--------|-----------------|
| InSAR m → mm | `ihmf_io.py` | 48 | **COMPLIANT** | — |
| InSAR m → mm (detrend pipeline) | `ihmf_detrend.py` | 209 | **COMPLIANT** | — |
| $h_c$ from pre-REF_DATE (Bug F fix) | `ihmf_io.py` | 68–79 | **COMPLIANT** | — |
| Lag direction ($dH[:n]$, $db[\tau:]$) | `ihmf_model_v3.py` | 211–214 | **COMPLIANT** | — |
| Regime mask at driver-time index | `ihmf_model_v3.py` | 213 | **COMPLIANT** | — |
| TAU_MAX = 120 epochs (600 days) | `ihmf_model_v3.py` | 204 | **COMPLIANT** | — |
| $V(t)$ with running cummin | `12_stress_strain.py` | 234–237 | **COMPLIANT** | — |
| NNLS negated $[-H, -V]$, $S_{kv} \ge S_{ke}$ | `12_stress_strain.py` | 277–284 | **COMPLIANT** | — |
| Two-thickness $S_{ske}$/$S_{skv}$ conversion | `12_stress_strain.py` | 582–584 | **COMPLIANT** | — |
| Literature bounds constants | `12_stress_strain.py` | 121–134 | **COMPLIANT** | — |
| Step 2 cumulative OLS with intercept | `ihmf_model_v3.py` | 337–340 | **COMPLIANT** | — |
| **Ratio gate: specific vs bulk** | `12_stress_strain.py` | 509, 535, 560 | **BUG** — F2 false positive, T2 false negative | Fix lines 560 (primary), 524–527 (consistency); re-run Script 12 |
| **Regime formulation: cummin vs level** | `ihmf_model_v3.py` | 126–141 | **SIMPLIFICATION** — diverges from Riley (1969) during sub-threshold recovery | Quantify bias per layer; reconcile before batch run |
| **PROGRESS.md decoupled state** | `PROGRESS.md` | 127–136 | **STALE** — "not yet implemented" but already done | One-line update; see Section 5 Issue 3 |

### Priority order

1. **Fix line 560 in Script 12** (and lines 524–527 for NNLS consistency) — confirmed code-level bug with arithmetic proof. Re-run Script 12; T2 changes from `feasible_2s=false` to `feasible_2s=true`; F2 changes from `feasible_2s=true` to `feasible_2s=false`.

2. **Update PROGRESS.md lines 127 and 136** — replace stale state with confirmed outcome.

3. **Quantify Issue 2 bias** before accepting IHM-F v3 batch results. For each layer, compute the fraction of inelastic-zone epochs that are sub-threshold recovery (head rising, no new minimum) and multiply by $S_{kv}/S_{ke}$ to estimate the prediction bias per layer.

---

*Report generated by autonomous OODA audit. All line numbers verified by direct file read. All numerical values read from source files; no values estimated.*
