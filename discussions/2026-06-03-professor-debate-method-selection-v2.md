# Method Selection: Physics vs. Machine Learning
**Date:** 2026-06-03  
**Context:** Response to two arguments raised by the supervising professor.

---

## The IHM-F Model

IHM-F (Candidate F of the Inelastic Head Model) predicts per-layer cumulative compaction from piezometric head change. One parameter set is fitted per geological formation (F1, T1, F2, T2, F3, F4) per station. Note: "F" is the candidate letter from the A-F method enumeration. IHM-F is an internal working name only.

The per-layer equation:

```
Δb_k(t) = S_ke · ΔH_k(t−τ) · I_e(t)  +  S_kv · ΔH_k(t−τ) · I_i(t)
```

- `ΔH_k(t−τ)` — piezometric head increment lagged by τ epochs (m; negative = head fell)
- `I_e`, `I_i` — elastic/inelastic regime indicators (head above/below preconsolidation head h_c)
- `S_ke`, `S_kv` — elastic and inelastic skeletal specific storage (mm/m; both ≥ 0)
- `τ` — hydraulic lag (integer epochs of 5 days; τ=6 ≈ 1 month, τ=73 ≈ 1 year)

**v2** fits one station-layer at a time with InSAR as a per-layer co-driver (`β·x(t)` column in the design matrix).  
**v3** fits all layers at a station jointly. InSAR is the total surface target only:

```
Step 1:  Δb_j(t) = S_ke_j · ΔH_j(t−τ_j) · I_e  +  S_kv_j · ΔH_j(t−τ_j) · I_i   [MLCW target, per layer]
Step 2:  α · Δd_v(t) = Σ_j Δb_j(t)                                                  [InSAR target, total]
```

---

## The One Constraint Governing Both Arguments

The 8,577 prediction grid points carry no per-layer MLCW ground truth. Any method — physics-based or machine learning — must transfer a relationship learned at 37 stations to those points. A method that cannot transfer physically fails Objective 2, regardless of training fit.

---

## Q1: Can Machine Learning Work at the Well-by-Well Scale?

**At 37 MLCW stations: yes, with constraints.**  
Per-layer compaction observations span approximately 785 five-day epochs per station. Available features include GWL head increments (189 aligned well files), SBAS-InSAR displacement increments, day-of-year, layer depth, and station coordinates. Patra et al. (2025) achieved R² = 0.858 with random forests on CRAF subsidence data; Hung et al. (2025) demonstrated Prophet forecasting at TUKU with RMSE = 0.34 mm over a 4-month horizon. Machine learning is applicable here.

The effective sample size is smaller than row counts imply. The 37 stations × 6 layers × 785 epochs produce 174,000 rows from 222 autocorrelated series spanning only 10 annual cycles. Physics-constrained or strongly regularized models are appropriate; unconstrained deep networks overfit.

**At 8,577 grid points: the transfer problem dominates.**  
Per-layer MLCW compaction does not exist at grid points. Three transfer strategies are available:

| Strategy | Transferability | Mechanism |
|---|---|---|
| Physics-parameter interpolation | High | Krige S_ke, S_kv, τ with fan-zone and depth covariates; run IHM-F forward at grid points |
| Feature-based transfer | Moderate | Train on features available everywhere (InSAR, kriged GWL, depth, coordinates); may fail in distal fan where clay thickness varies |
| Physics-structured encoder | High | Neural network maps (GWL state, season, depth) → S_ke(t), S_kv(t), τ; weights shared across 37 stations; runs at grid points from kriged GWL |

**On GNSS as a substitute for InSAR:**  
Continuous GNSS (CGPS) measures total vertical surface displacement at a point. It does not decompose per-layer compaction. Neither CGPS nor SBAS-InSAR can identify which layer contributed which fraction of subsidence — only per-layer GWL head change multiplied by the per-layer skeletal storage coefficient achieves that decomposition. The 91 CGPS stations do not cover the 8,577 grid points; spatial extension still requires physics-parameter interpolation or a feature-based encoder.

---

## Q2: Physical Parameters Are Not Constant — Does This Break the Physics Approach?

**Two distinct sources of apparent non-stationarity require different responses.**

**Source 1 — Regime aliasing (dominant; diagnosable now).**  
S_ke is active when piezometric head exceeds h_c; S_kv is active when head falls below h_c. A training window dominated by drought years produces a higher apparent S_kv than a window dominated by wet-season recovery — not because the sediment changed, but because the inelastic channel is better sampled. The diagnostic is f_inel, the fraction of inelastic epochs per fold. Any fold with f_inel < 0.10 produces an unreliable S_kv estimate. This is an estimation artefact, not a material property change.

**Source 2 — Material property evolution (secondary; testable).**  
In principle, S_kv declines as cumulative inelastic compaction accumulates and the clay moves down its virgin compression curve. A discriminating test: fit S_kv on inelastic-only epochs from 2015–2018 versus 2022–2025. If S_kv is stable once regime composition is matched, the apparent drift was aliasing. If S_kv continues to drift in regime-isolated windows, a stress-history feedback term is warranted — one additional parameter per layer, not a separate prediction problem.

**Does predicting future S_ke and S_kv add complexity?**  
For the aliasing component: no. The regime switch at any future epoch depends on whether future GWL head exceeds h_c. Future GWL head is already the required external input to IHM-F forward prediction. For the material-evolution component: one feedback per layer, computed from cumulative model output — not from an external source.

Machine learning is equally affected by non-stationarity. An LSTM trained on 2015–2021 data implicitly encodes the S_kv prevailing in that period. When S_kv shifts, the LSTM fails silently. The physics approach fails explicitly: the f_inel flag and parameter bounds identify the failure point.

---

## Evaluation Summary

| Issue | Machine Learning | IHM-F | Hybrid Encoder |
|---|---|---|---|
| Training at 37 stations | Applicable; needs regularization | Applicable; Terzaghi-structured | Strongest |
| Transfer to grid points | Moderate; may fail in distal fan | High; parameter interpolation | High; encoder inputs exist everywhere |
| Seasonal S_ke variation | Absorbed implicitly; no diagnostic | Diagnosed via f_inel | Handled naturally |
| Decadal S_kv drift | Silent failure | Testable; regime-stratified folds | Testable; same feedback applies |
| Physical interpretability | Low | High | High |
| Deployability post-MLCW shutdown | Limited | Yes; 37-station parameters transferable | Yes |

---

## 7-Day Action Plan

Two code fixes unblock the batch run. Everything else follows.

**Days 1–2 — Fix the code:**

1. Change the α regression in `joint_solve_fixed_tau()` (`ihmf_model_v3.py`) from cumulative to incremental. Cumulative series share a common drift trend regardless of physical coupling — this produces spurious α ≈ 0.0197 on the full record versus α = 0.023–0.163 on shorter walk-forward windows.
2. Raise `TAU_MAX` from 73 to 120 in `fit_ihm_f_v3.py`. At 73 epochs (365 days), the T1 aquitard hits the search ceiling at every station — the true lag is unknown.

Re-run TUKU after both fixes. If α rises to 0.05–0.15, the defect is confirmed and results are physically interpretable.

**Days 3–4 — Batch run (37 stations):**  
Collect α, S_ke, S_kv, τ, and f_inel per station per layer. Flag any station-layer with S_ke < 0 or S_kv < 0 as invalid. Flag any station-layer with f_inel < 0.10 as data-limited for S_kv.

**Days 5–7 — Interpret and report:**  
The batch results directly answer the professor's questions. The f_inel distribution distinguishes aliasing from material drift. The walk-forward α trend shows how coupling evolves as drought years enter training. These are the empirical answers, not theoretical arguments.

Longer-horizon work — running preconsolidation head, ridge regularization toward literature priors, physics-structured encoder — is deferred. None is required to answer the questions raised.
