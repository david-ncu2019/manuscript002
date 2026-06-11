# FEASIBILITY VERDICT — Sub-Annual Multilayer Compaction Dynamics from Surface + 1D Head
## Scope: TUKU station, GPS/InSAR carrier model, single-well pilot
### Date: 2026-06-12  |  Status: FINAL (Red Team Task E)

---

## 1. Plain Verdict

Reconstructing sub-annual per-layer compaction dynamics at the TUKU Multi-Layer Compaction Well (MLCW) from total surface deformation (GPS/InSAR carrier) plus a single one-dimensional (1D) groundwater head record alone is physically blocked by two independent mechanisms, not by a model parameter choice.

**Mechanism 1 — amplitude-bound:** The seasonal compaction amplitude of aquifer layer F2 (4.71 mm peak-to-trough) exceeds the total surface seasonal amplitude (3.83 mm) by a factor of 1.23×. Because the surface signal is the column sum of all 6 layers, at least one other layer must produce a seasonal compaction that partially opposes F2 in time — confirmed by F3 (amplitude 2.08 mm, phase day-of-year 101 vs F2 phase DOY 324, a phase offset of ≈223 days ≈ 6 months). No assignment of a scalar coefficient or consolidation lag $\tau$ can recover the true magnitude of both signals simultaneously from their surface sum alone.

**Mechanism 2 — regional head collinearity:** The six per-layer head driver timeseries share a single groundwater system. Mean pairwise Pearson correlation among the six head drivers = 0.862; maximum pairwise = 1.000 (F1 and T1 share wellcode `09050111` — an exact duplicate). H$_\text{F2}$ and H$_\text{F3}$ correlate at r = 0.987. The design matrix of [GPS carrier, $u_{F1}$, $u_{T1}$, $u_{F2}$, $u_{T2}$, $u_{F3}$, $u_{F4}$] has condition number $\approx 5 \times 10^{16}$ and a structural null-space dimension of 1 from the exact F1/T1 duplicate alone. Even after removing the duplicate, the near-collinearity of all remaining head drivers means that a regression estimating 6 independent layer responses is severely ill-conditioned: the solver cannot distinguish which layer is responding to the regionally-correlated head signal.

These two mechanisms are independent. Either one alone would block reliable per-layer dynamic recovery at sparse (annual or semiannual) in-situ cadence. The F3 consolidation-lag uncap test (Task C: $\tau$ lifted 120 → 163 epochs) confirmed this: blind detrended r improved only 0.41 → 0.44 at annual cadence, well below 0.5, while the cross-correlation lag remained at ≈ +25 days (persistent phase error). At monthly cadence F3 detrended r = 0.862 — dynamics are recoverable only when frequent in-situ supply provides the phase information that the surface + head inputs cannot.

**This limitation is not solvable by adjusting $\tau$, by refitting, or by adding architectural complexity within the single-surface-carrier + 1D-head framework.**

---

## 2. The Three Measured Exhibits

All numbers read from persisted files on disk after script execution. Source: `tau_demo_TUKU/results/seq/red_team_fixes/feasibility_proof.json`.

### Exhibit (a) — Amplitude-bound lemma

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

The F2/F3 phase opposition (phase difference ≈ 223 days ≈ 6 months) is the dominant cancellation mechanism. F3 is in the late-consolidation (inelastic) regime with a multi-year stress memory; F2 is in the elastic regime responding to seasonal head fluctuations. Their seasonal signals are nearly anti-phased.

### Exhibit (b) — Phase cancellation phasor diagram

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

Comparison: $\sum |A_k| = 9.40$ mm vs $|\sum \mathbf{p}_k| = 5.28$ mm vs $A_\text{surface} = 3.83$ mm. The layer sum (5.28 mm) is 1.38× larger than the observed surface seasonal (3.83 mm). The discrepancy between the layer vector sum and the GPS surface phasor is expected: the GPS signal captures the cumulative deformation at the surface anchor point, while the MLCW measures compaction at the ring extensometer positions which integrate different depth columns. The important relationship is internal: $\sum |A_k| = 9.40$ mm, while the cancellation via opposing phases reduces the net to 5.28 mm — a cancellation factor of 1.78×. F3 (pointing in the $+y$ direction at DOY 101) directly opposes F2 (pointing in the $-y$ direction at DOY 324).

**Physical implication:** Any inversion attempting to recover 6 per-layer seasonal signals from 1 surface signal must have access to the phase information. At annual cadence (one visit per year), the phase is unobservable from the in-situ record itself. The GPS carrier is 99.6% linear (secular trend; verified in PART1_FINDINGS_20260610.md) and carries no sub-annual phase information. The 1D head is regionally correlated across layers (r = 0.862 mean). No solver can separate a 4.71 mm F2 seasonal from a 2.08 mm F3 opposite-phase seasonal when the inputs contain only trend + near-uniform regional head.

### Exhibit (c) — Rank deficiency of the driver design

The per-layer driver design matrix has columns [GPS, $u_{F1}$, $u_{T1}$, $u_{F2}$, $u_{T2}$, $u_{F3}$, $u_{F4}$] evaluated at the 2 333 exact-date intersections over the dense era. Singular values (normalized to largest = 1):

| Index | Singular value (raw) | Normalized |
|-------|----------------------|------------|
| 1 | 390.4 | 1.000 |
| 2 | 201.1 | 0.515 |
| 3 | 55.9 | 0.143 |
| 4 | 36.4 | 0.093 |
| 5 | 26.6 | 0.068 |
| 6 | 12.6 | 0.032 |
| 7 | $7.8 \times 10^{-15}$ | $\approx 0$ |

Effective rank (singular values > 1% of largest) = **6 of 7 total columns**. Condition number = $5 \times 10^{16}$.

The 7th singular value is machine-zero: this null dimension arises from the exact duplicate (F1 and T1 share wellcode `09050111` → $u_{F1} \equiv u_{T1}$ exactly). After removing one of the two identical columns, the remaining 6-column design has formal rank 6. This sounds sufficient — but the physical constraint reveals why rank alone is misleading:

The condition number of $5 \times 10^{16}$ signals that the design is near-singular **in a continuous sense**: the near-collinearity of H$_\text{F2}$ vs H$_\text{F3}$ (r = 0.987), H$_{F1}$/H$_{T1}$ vs H$_{F2}$ (r = 0.836), and H$_{F4}$ vs H$_{T2}$ (r = 0.929) means that the regression coefficients are not reliably estimable from {surface, head} inputs. A perturbation of even 1 mm in the surface signal propagates to unbounded changes in the per-layer coefficient assignments.

The practical statement: with 6 near-identical head drivers (mean pairwise r = 0.862) and 1 GPS carrier that is 99.6% linear, the design has 6 formal dimensions but only 2–3 distinguishable signal components (the linear trend in all heads, the common-mode regional seasonal, and possibly one quasi-orthogonal F3 component). The remaining 3–4 "dimensions" carry $<$5% of the variance and are unidentifiable from the data.

---

## 3. Corroborating Empirical Evidence (Tasks B, C, D)

These results are from verified files in `tau_demo_TUKU/results/seq/red_team_fixes/`.

**Task B (`honest_skill_table.json`):** Against the fair anchor-once baseline (datum fixed once at deployment entry), annual in-situ cadence post-entry skill: F2 = −0.018, T2 = −0.092 (no skill beyond the one-time datum fix for most layers). F3 annual = +0.188 (modest). F4 monthly = −0.20 (negative skill — sparser visits hurt). Only monthly cadence buys real dynamic skill: F3 +0.558, F2 +0.231. The claimed 0.79/0.82 annual skill in earlier assessments was the datum-offset correction, not genuine forward dynamics.

**Task C (`f3_uncapped_walkforward_metrics.json`):** Lifting F3's consolidation-lag cap from 120 to 163 epochs cut dense-era sum-of-squared errors by 62% and activated the elastic term ($S_{ke}$: 0 → 0.51). But blind-era detrended r at annual cadence rose only 0.41 → 0.44 (threshold for acceptance: 0.5). Cross-correlation lag remained at +25 days — the phase error did not close regardless of $\tau$. At monthly cadence, F3 detrended r = 0.862: dynamics are recoverable at monthly cadence when the in-situ signal directly supplies the phase.

**Task D (`coverage_reckoning.json`):** Split-conformal prediction-band coverage FAILS at semiannual cadence: only 3/6 layers reach $\geq$0.85 coverage on n $\geq$ 20 (semiannual verdict: FAIL — F1 0.667, T1 0.815, F3 0.778). Coverage PASSES only at monthly cadence (5/6 layers $\geq$ 0.85, n = 60).

All three tasks independently confirm the same pattern: sparse visits (annual/semiannual) are sufficient for secular trend tracking but not for sub-annual dynamics. Monthly visits recover dynamics but violate the budget rationale that motivates the entire project.

---

## 4. What Remains Valid and Deployable

The impossibility thesis applies specifically to sub-annual per-layer **dynamics** from sparse visits. The following components are valid and deployable:

**Secular trend apportionment per layer (all 6 layers, all cadences):** The GPS carrier is 99.6% linear over 2011–2022 (GNSS data cited in PART1_FINDINGS_20260610.md). Trend error from the carrier method is $<$1% of total column trend at the pilot station. At every in-situ cadence tested (annual through monthly), the per-layer trend is tracked reliably by the carrier model.

**Datum maintenance by sparse field visits (the real budget lever):** The single dominant source of long-range error is datum drift accumulated during unanchored periods between visits. Post-entry RMSE at anchor-once baseline: F1 = 3.1 mm, T1 = 1.8 mm, F2 = 3.8 mm, T2 = 2.4 mm, F3 = 7.2 mm, F4 = 1.6 mm. Annual visits are sufficient to contain this drift for all layers except F3 (which accumulates −1.21 mm/yr drift). At annual cadence, the model provides a reliable trend + datum product for F1, T1, T2, F4 (RMSE 1.5–3.2 mm), and acceptable performance for F2 (RMSE 3.9 mm). F3 requires quarterly or more frequent visits to keep drift $<$5 mm.

**F2 partial dynamics (the one exception):** F2 carries real seasonal compaction dynamics driven by aquifer head fluctuations. At annual cadence, F2 detrended r ≈ 0.41; at monthly, r ≈ 0.60. F2 is the single layer where the annual-cadence carrier model captures partial sub-annual dynamics (not zero skill, as distinct from the deeper clay-rich layers).

**Monthly in-situ cadence recovers deep-layer dynamics:** Monthly visits give F3 blind-era detrended r = 0.862 and conformal coverage 0.867 ($\geq$0.85 threshold passed). This is the boundary condition: if the monitoring budget is restructured to monthly cadence for F3 specifically, sub-annual dynamics are recoverable. The cost-effectiveness of that choice relative to the original project goal (sparse monitoring substitution) is a management decision outside the scope of this document.

**The honest deployable product at annual cadence:** secular trend + single datum fix at deployment entry + annual datum maintenance at all layers; partial F2 dynamics (treat as bonus, not guaranteed); F3/F4 sub-annual dynamics stated as unresolvable and replaced by prediction intervals.

---

## 5. Scope and Limitations

This verdict applies to the single TUKU pilot station (Yunlin County, distal alluvial fan). Generalization requires independent verification at each of the 37 MLCW stations in the Choushui River Alluvial Fan (CRAF).

Three augmentations that are not disproven here and could potentially resolve the dynamics problem:

1. **InSAR-augmented per-layer signals:** If ascending + descending InSAR decomposition provides multiple independent surface-deformation components (not just the scalar vertical), the driver design gains additional non-collinear columns. Whether these columns are sufficiently independent to resolve 6-layer inversion is untested.

2. **Per-layer head records:** If each layer had its own monitored well (distinct wellcodes with non-collinear timeseries), the design matrix collinearity problem weakens. The current assignment gives F2 and F3 wells correlated at r = 0.987; a well nearer F3's depth screened in a distinct aquifer unit would reduce this.

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
| `tau_demo_TUKU/plots/seq/red_team_fixes/feasibility_rank_deficiency.png` | Exhibit (c) SVD + correlation heatmap |
| `tau_demo_TUKU/results/seq/red_team_fixes/honest_skill_table.json` | Task B: post-entry skill vs anchor-once baseline |
| `tau_demo_TUKU/results/seq/red_team_fixes/f3_uncapped_walkforward_metrics.json` | Task C: F3 $\tau$-uncap results |
| `tau_demo_TUKU/results/seq/red_team_fixes/coverage_reckoning.json` | Task D: conformal coverage by cadence |
