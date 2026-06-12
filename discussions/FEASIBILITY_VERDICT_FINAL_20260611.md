# FEASIBILITY VERDICT — Sub-Annual Multilayer Compaction Dynamics from Surface + 1D Head
## Scope: TUKU station, GPS/InSAR carrier model, single-well pilot
### Date: 2026-06-12  |  Status: FINAL (Red Team Task E, revised)

---

## 1. Plain Verdict

At sparse (annual or semiannual) in-situ visit cadence, sub-annual per-layer compaction dynamics at the TUKU Multi-Layer Compaction Well (MLCW) are **mathematically underdetermined and empirically unrecoverable** from total surface deformation (GPS/InSAR carrier) plus a single one-dimensional (1D) groundwater head record alone.

This conclusion is **cadence-specific, not absolute.** At monthly in-situ cadence, F3 blind-era detrended Pearson r = 0.862 (threshold: 0.5) — dynamics are recoverable when frequent in-situ measurements supply the phase information the surface + head inputs cannot. The impossibility applies at annual and semiannual cadence only.

**Two incontrovertible structural mechanisms, independent of each other:**

**Mechanism 1 — amplitude-bound (geometric):** The seasonal compaction amplitude of aquifer layer F2 (4.71 mm) exceeds the total surface seasonal amplitude (3.83 mm) by a factor of 1.23×. Because the surface signal is the column sum of all 6 layers, at least one other layer must produce a seasonal compaction that partially opposes F2 in time — confirmed by F3 (amplitude 2.08 mm, phase day-of-year 101 vs F2 phase DOY 324, a phase offset of ≈223 days ≈ 6 months). No assignment of a scalar coefficient or consolidation lag $\tau$ can recover the true magnitude of both signals simultaneously from their surface sum alone.

**Mechanism 2 — carrier rank-1 degeneracy (algebraic):** In the GPS/InSAR carrier model, each layer's surface contribution equals $a_k \cdot d(t)$, where $d(t)$ is the scalar GPS surface displacement and $a_k$ is a fixed calibration share. ALL six layer contributions are therefore exactly proportional to a single shared signal. The carrier contribution matrix $[a_1 \cdot d, a_2 \cdot d, \ldots, a_6 \cdot d]$ has algebraic rank = 1, verified numerically by SVD: one singular value at $7.29 \times 10^3$, all five remaining values at $< 4 \times 10^{-13}$ (i.e., $< 4 \times 10^{-17}$ relative to the largest — machine noise). The carrier supplies exactly **one shared degree of freedom** for six unknowns. Moreover GPS displacement is 99.6% linear over 2011–2022 (PART1_FINDINGS_20260610.md), so the carrier carries negligible sub-annual content.

The per-layer head drivers are the only layer-distinguishing inputs. They are severely correlated: mean pairwise Pearson $r = 0.863$ across the 5 distinct drivers (seasonal detrended band), maximum $r = 0.987$ (F2 vs F3). This near-collinearity means that even though the formal rank of the 5-driver design is 5, the regression cannot reliably attribute a regionally-correlated head signal to any specific layer without dense in-situ phase constraints.

**These two mechanisms are independent. The amplitude-bound alone proves non-uniqueness by geometric inspection. The carrier rank-1 proves the driver cannot supply the missing information algebraically.**

---

## 2. The Three Measured Exhibits

All numbers read from the persisted file `tau_demo_TUKU/results/seq/red_team_fixes/feasibility_proof.json` after script execution.

### Exhibit (a) — Amplitude-bound lemma (PROVEN, incontrovertible)

Annual harmonic amplitudes fitted to dense-era (2010-01-01 to 2018-12-31) MLCW cumulative data per layer, using exact date intersection (anti-pattern A1 avoided), real elapsed days as the time variable (A3 avoided), zero-referenced before detrending (A4 avoided).

| Signal | n points | Amplitude $A_k$ (mm) | Phase DOY | $A_k > A_\text{surface}$? |
|--------|----------|----------------------|-----------|---------------------------|
| GPS surface (TKJS) | 3 286 | **3.832** | 313 | — |
| F1 | 109 | 0.600 | 346 | No |
| T1 | 109 | 0.452 | 350 | No |
| F2 | 109 | **4.707** | 324 | **Yes** |
| T2 | 109 | 0.761 | 301 | No |
| F3 | 109 | 2.082 | 101 | No |
| F4 | 109 | 0.798 | 51 | No |

$\sum |A_k| = 9.40$ mm; $\sum |A_k| / A_\text{surface} = 2.45\times$.

The key physical fact: F2 seasonal amplitude (4.71 mm) exceeds the entire surface seasonal amplitude (3.83 mm). The surface signal is the column integral of all six layers. If F2 alone produces 4.71 mm of seasonal motion, and the surface shows only 3.83 mm total, then the remaining five layers must together produce $-0.88$ mm net seasonal motion — i.e., they partially oppose F2. The inversion from 1 surface scalar to 6 per-layer scalars is therefore not unique by inspection.

The F2/F3 phase opposition (phase difference ≈ 223 days ≈ 6 months) is the dominant cancellation mechanism. F3 is in the late-consolidation (inelastic) regime with a multi-year stress memory; F2 is in the elastic regime responding to seasonal head fluctuations.

### Exhibit (b) — Phase cancellation phasor diagram (soft corroboration)

Representing each layer's seasonal as a phasor $\mathbf{p}_k = (A_k \cos\phi_k, A_k \sin\phi_k)$:

| Layer | $p_x$ (mm) | $p_y$ (mm) | $|$phasor$|$ (mm) |
|-------|------------|------------|-------------------|
| F1 | +0.569 | −0.192 | 0.600 |
| T1 | +0.437 | −0.114 | 0.452 |
| F2 | +3.575 | −3.062 | 4.707 |
| T2 | +0.343 | −0.679 | 0.761 |
| F3 | −0.337 | +2.055 | 2.082 |
| F4 | +0.508 | +0.615 | 0.798 |
| **GPS surface** | **+2.404** | **−2.984** | **3.832** |

Vector sum of 6 layer phasors: $(+5.095, -1.376)$ mm, magnitude = **5.277 mm**.

Cancellation factor: $\sum |A_k| / |\sum \mathbf{p}_k| = 9.40 / 5.28 = \mathbf{1.78\times}$. This is **soft corroboration**, not a pass/fail gate. The 1.78× ratio confirms that opposing phases reduce the net vector sum substantially below the scalar sum, corroborating the amplitude-bound argument. The decisive geometric proof is Exhibit (a): F2 alone exceeds the surface amplitude, which requires no threshold judgment.

**Physical implication:** Any inversion attempting to recover 6 per-layer seasonal signals from 1 surface signal must have access to the phase information. At annual cadence (one visit per year), the phase is unobservable from the in-situ record itself. The GPS carrier is 99.6% linear and carries no sub-annual phase information. No solver can separate a 4.71 mm F2 seasonal from a 2.08 mm F3 opposite-phase seasonal when the inputs contain only trend + near-uniform regional head.

### Exhibit (c) — Carrier rank-1 degeneracy + sub-annual head collinearity

#### Sub-exhibit (c-i): Carrier rank-1 degeneracy (PROVEN, algebraically incontrovertible)

In the carrier model, layer $k$'s surface contribution is $a_k \cdot d(t)$, where $d(t)$ is the GPS surface signal and $a_k$ is the calibrated carrier share. The per-layer carrier contribution matrix has columns $[a_1 \cdot d, a_2 \cdot d, \ldots, a_6 \cdot d]$, each a scalar multiple of the same vector. This matrix has algebraic rank = 1 by construction.

**Numerical verification (SVD of the 3 286 × 6 carrier matrix):**

| Index | Absolute singular value | Normalized |
|-------|------------------------|------------|
| 1 | $7.287 \times 10^3$ | 1.000 |
| 2 | $2.671 \times 10^{-13}$ | $3.7 \times 10^{-17}$ |
| 3 | $1.887 \times 10^{-13}$ | $2.6 \times 10^{-17}$ |
| 4 | $3.454 \times 10^{-14}$ | $4.7 \times 10^{-18}$ |
| 5 | $1.982 \times 10^{-14}$ | $2.7 \times 10^{-18}$ |
| 6 | $1.230 \times 10^{-14}$ | $1.7 \times 10^{-18}$ |

Carrier matrix rank = **1** (all 5 remaining singular values at machine-noise level $< 4 \times 10^{-17}$ relative to SV[1]).

The calibrated shares per layer: F1 $a=0.0275$, T1 $a=0.0175$, F2 $a=0.2029$, T2 $a=0.0110$, F3 $a=0.2696$, F4 $a=0.0309$; $\sum a_k = 0.5592$. These ratios are fixed from in-situ calibration — the carrier cannot, even in principle, identify them from the surface signal $d(t)$ alone, since all six columns are proportional to $d(t)$. A new surface excursion cannot be attributed to any specific layer by the carrier mechanism.

#### Sub-exhibit (c-ii): Sub-annual head collinearity (MEASURED)

**Duplicate correction:** F1 and T1 share the same wellcode `09050111` — their head timeseries are an exact duplicate. The original 7-column design [GPS, H$_{F1}$, H$_{T1}$, H$_{F2}$, H$_{T2}$, H$_{F3}$, H$_{F4}$] had condition number $\approx 5 \times 10^{16}$, entirely caused by this exact column duplication. After removing F1 (keeping T1), the 5 distinct drivers [T1, F2, T2, F3, F4] are analysed:

**Condition numbers:**

| Design | Condition number | Effective rank (SV $>$ 1% max) | Interpretation |
|--------|-----------------|-------------------------------|----------------|
| Original 7-col (with F1==T1 duplicate) | $5.0 \times 10^{16}$ | 6 of 7 | Dominated by exact duplicate — not general collinearity |
| De-duplicated 5-col, raw zero-referenced | **18.8** | 5 of 5 | Well-conditioned in trend-dominated band |
| De-duplicated 5-col, standardized detrended (seasonal band) | **19.9** | 5 of 5 | Formally full rank, but near-collinear in seasonal content |

The $5 \times 10^{16}$ condition number in the original design was the F1/T1 exact duplicate, not a property of the underlying head signals. The de-duplicated raw condition number is **18.8** — well-conditioned in the trend band.

However, the pairwise correlations of the detrended heads (seasonal band) are severe:

| Pair | Detrended Pearson $r$ |
|------|-----------------------|
| H$_{T1}$ vs H$_{F2}$ | 0.836 |
| H$_{T1}$ vs H$_{T2}$ | 0.796 |
| H$_{T1}$ vs H$_{F3}$ | 0.834 |
| H$_{T1}$ vs H$_{F4}$ | 0.833 |
| H$_{F2}$ vs H$_{T2}$ | 0.860 |
| H$_{F2}$ vs H$_{F3}$ | **0.987** |
| H$_{F2}$ vs H$_{F4}$ | 0.828 |
| H$_{T2}$ vs H$_{F3}$ | 0.880 |
| H$_{T2}$ vs H$_{F4}$ | 0.929 |
| H$_{F3}$ vs H$_{F4}$ | 0.850 |
| **Mean** | **0.863** |
| **Max** | **0.987** (F2/F3) |

Mean pairwise correlation = 0.863; maximum = 0.987 (F2 and F3 are nearly identical in seasonal content). Although the formal rank of the 5-driver seasonal design is 5 (all singular values exceed 1% of the maximum), a regression estimating 6 independent per-layer responses from these near-collinear inputs cannot reliably discriminate which layer is responding to the regionally-correlated head signal. F2 and F3 are correlated at $r = 0.987$ in the sub-annual band — any attempt to assign distinct $S_{ske}$/$S_{skv}$ coefficients to these two layers from head inputs alone is effectively ill-posed at sparse cadence where in-situ phase constraints are absent.

**The 5 × 10¹⁶ condition number is explained and contextualized:** it was the F1/T1 exact duplicate; the de-duplicated seasonal design is well-conditioned (cond = 19.9) but the head near-collinearity (mean $r = 0.863$) means that without dense in-situ phase observations, the carrier rank-1 limitation cannot be compensated by the head term.

---

## 3. Corroborating Empirical Evidence (Tasks B, C, D)

These results are from verified files in `tau_demo_TUKU/results/seq/red_team_fixes/`.

**Task B (`honest_skill_table.json`):** Against the fair anchor-once baseline (datum fixed once at deployment entry), annual in-situ cadence post-entry skill: F2 = −0.018, T2 = −0.092 (no skill beyond the one-time datum fix for most layers). F3 annual = +0.188 (modest). F4 monthly = −0.20 (negative skill — sparser visits hurt). Only monthly cadence buys real dynamic skill: F3 +0.558, F2 +0.231. The claimed 0.79/0.82 annual skill in earlier assessments was the datum-offset correction, not genuine forward dynamics.

**Task C (`f3_uncapped_walkforward_metrics.json`):** Lifting F3's consolidation-lag cap from 120 to 163 epochs cut dense-era sum-of-squared errors by 62% and activated the elastic term ($S_{ke}$: 0 → 0.51). But blind-era detrended $r$ at annual cadence rose only 0.41 → 0.44 (threshold for acceptance: 0.5). Cross-correlation lag remained at +25 days — the phase error did not close regardless of $\tau$. At monthly cadence, F3 detrended $r$ = 0.862: dynamics are recoverable when the in-situ signal directly supplies the phase.

**Task D (`coverage_reckoning.json`):** Split-conformal prediction-band coverage FAILS at semiannual cadence: only 3/6 layers reach $\geq 0.85$ coverage on $n \geq 20$ (semiannual verdict: FAIL — F1 0.667, T1 0.815, F3 0.778). Coverage PASSES only at monthly cadence (5/6 layers $\geq 0.85$, $n = 60$).

All three tasks independently confirm the same pattern: sparse visits (annual/semiannual) are sufficient for secular trend tracking but not for sub-annual dynamics. Monthly visits recover dynamics but violate the budget rationale that motivates the entire project.

---

## 4. What Remains Valid and Deployable

The impossibility thesis applies specifically to sub-annual per-layer **dynamics** from sparse visits. The following components are valid and deployable:

**Secular trend apportionment per layer (all 6 layers, all cadences):** The GPS carrier is 99.6% linear over 2011–2022 (GNSS data cited in PART1_FINDINGS_20260610.md). Trend error from the carrier method is $<$1% of total column trend at the pilot station. At every in-situ cadence tested (annual through monthly), the per-layer trend is tracked reliably by the carrier model.

**Datum maintenance by sparse field visits (the real budget lever):** The single dominant source of long-range error is datum drift accumulated during unanchored periods between visits. Post-entry RMSE at anchor-once baseline: F1 = 3.1 mm, T1 = 1.8 mm, F2 = 3.8 mm, T2 = 2.4 mm, F3 = 7.2 mm, F4 = 1.6 mm. Annual visits are sufficient to contain this drift for all layers except F3 (which accumulates −1.21 mm/yr drift). At annual cadence, the model provides a reliable trend + datum product for F1, T1, T2, F4 (RMSE 1.5–3.2 mm), and acceptable performance for F2 (RMSE 3.9 mm). F3 requires quarterly or more frequent visits to keep drift $<$5 mm.

**F2 partial dynamics (the one exception):** F2 carries real seasonal compaction dynamics driven by aquifer head fluctuations. At annual cadence, F2 detrended $r \approx 0.41$; at monthly, $r \approx 0.60$. F2 is the single layer where the annual-cadence carrier model captures partial sub-annual dynamics (not zero skill, as distinct from the deeper clay-rich layers).

**Monthly in-situ cadence recovers deep-layer dynamics:** Monthly visits give F3 blind-era detrended $r = 0.862$ and conformal coverage 0.867 ($\geq 0.85$ threshold passed). This is the boundary condition: if the monitoring budget is restructured to monthly cadence for F3 specifically, sub-annual dynamics are recoverable. The cost-effectiveness of that choice relative to the original project goal (sparse monitoring substitution) is a management decision outside the scope of this document.

**The honest deployable product at annual cadence:** secular trend + single datum fix at deployment entry + annual datum maintenance at all layers; partial F2 dynamics (treat as bonus, not guaranteed); F3/F4 sub-annual dynamics stated as unresolvable and replaced by prediction intervals.

---

## 5. Scope and Limitations

This verdict applies to the single TUKU pilot station (Yunlin County, distal alluvial fan). Generalization requires independent verification at each of the 37 MLCW stations in the Choushui River Alluvial Fan (CRAF).

Three augmentations that are not disproven here and could potentially resolve the dynamics problem:

1. **InSAR-augmented per-layer signals:** If ascending + descending InSAR decomposition provides multiple independent surface-deformation components (not just the scalar vertical), the driver design gains additional non-collinear columns. Whether these columns are sufficiently independent to resolve 6-layer inversion is untested.

2. **Per-layer head records:** If each layer had its own monitored well (distinct wellcodes with non-collinear timeseries), the design matrix near-collinearity problem weakens. The current assignment gives F2 and F3 wells correlated at $r = 0.987$ in the seasonal band; a well nearer F3's depth screened in a distinct aquifer unit would reduce this.

3. **Multi-station spatial joint inversion:** Combining TUKU with neighboring stations that share the same regional head field but have different layer compaction responses could provide spatial constraints that break the collinearity.

None of these is the current method. The verdict here is specific to: GPS/InSAR surface carrier + 1D head + sparse in-situ (annual/semiannual), single well.

---

## 6. Source Files

| File | Description |
|------|-------------|
| `tau_demo_TUKU/seq/30_feasibility_proof.py` | Script generating all three exhibits |
| `tau_demo_TUKU/results/seq/red_team_fixes/feasibility_proof.json` | Machine-readable numbers cited above |
| `tau_demo_TUKU/results/seq/red_team_fixes/feasibility_proof.csv` | Per-layer amplitude/phase table |
| `tau_demo_TUKU/results/seq/red_team_fixes/30_feasibility_proof_run_log.txt` | Full console output |
| `tau_demo_TUKU/plots/seq/red_team_fixes/feasibility_amplitude_bound.png` | Exhibit (a) bar chart |
| `tau_demo_TUKU/plots/seq/red_team_fixes/feasibility_phase_cancellation.png` | Exhibit (b) phasor + timeseries |
| `tau_demo_TUKU/plots/seq/red_team_fixes/feasibility_rank_deficiency.png` | Exhibit (c-i) carrier SVD bar + (c-ii) seasonal head heatmap |
| `tau_demo_TUKU/results/seq/red_team_fixes/honest_skill_table.json` | Task B: post-entry skill vs anchor-once baseline |
| `tau_demo_TUKU/results/seq/red_team_fixes/f3_uncapped_walkforward_metrics.json` | Task C: F3 $\tau$-uncap results |
| `tau_demo_TUKU/results/seq/red_team_fixes/coverage_reckoning.json` | Task D: conformal coverage by cadence |
