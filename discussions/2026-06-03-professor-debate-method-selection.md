# Method Selection Debate: Machine Learning vs. Physics-Based Approach
**Date:** 2026-06-03 (revised from first draft — corrected IHM-F description)
**Context:** Response to two arguments raised by the supervising professor regarding (1) the feasibility of machine learning at the well-by-well scale and (2) the non-stationarity of physical parameters in IHM-F (Candidate F of the Inelastic Head Model).

---

## What Is IHM-F? (Authoritative Description)

IHM-F (Candidate F of the Inelastic Head Model) is a two-regime, groundwater-level-driven model that predicts per-layer cumulative compaction from piezometric head change and surface displacement. One set of physical parameters is fitted per geological formation (aquifer or aquitard layer), independently for each station-layer pair. Note: "F" is the candidate letter from the A-F method enumeration (not an abbreviation of "Formational"). IHM-F is an internal working name only.

The model equation for a single layer k at observation epoch t is:

```
D_k(t) = c + S_ske · ΔH_k(t−τ) · I_e(t) + S_skv · ΔH_k(t−τ) · I_i(t) + β · x(t)
```

where:
- `D_k(t)` — cumulative MLCW compaction since the first epoch (mm, negative = compaction)
- `ΔH_k(t−τ)` — piezometric head change from the reference epoch, lagged by τ epochs (m, negative = head fell)
- `I_e(t)` — 1 when head is above the preconsolidation head h_c (elastic regime), 0 otherwise
- `I_i(t)` — 1 when head is at or below h_c (inelastic regime), 0 otherwise
- `S_ske` — elastic skeletal specific storage (mm/m): reversible compaction per metre of head drop
- `S_skv` — inelastic skeletal specific storage (mm/m): permanent compaction per metre of head drop below h_c
- `β` — InSAR coupling coefficient: fraction of total surface displacement co-explained by this layer
- `x(t)` — cumulative InSAR surface displacement (mm, negative = subsidence)
- `c` — intercept: compaction accumulated before the first observation epoch
- `τ` — hydraulic lag in epochs (1 epoch = 5 days): delay for pore pressure to diffuse into the clay layer

**Physical constraints enforced by the solver:**
- S_ske ≥ 0 (elastic compressibility cannot be negative)
- S_skv ≥ 0 (inelastic compressibility cannot be negative)
- β ≥ 0 (InSAR coupling must be non-negative)
- S_skv >> S_ske expected (inelastic regime is always more compressible; ratio 5–20× for alluvial clay)

### Two Versions of the Model

**IHM-F v2 (ihmf_model.py):** Fits a single station-layer pair at a time. InSAR appears as a co-driver regressor (column `β·x(t)` in the design matrix). The τ grid search minimises residual sum of squares (RSS) on the raw cumulative signals. The four parameters `[c, S_ske, S_skv, β]` are estimated jointly by bounded least squares (`scipy.optimize.lsq_linear`, method BVLS).

**IHM-F v3 (ihmf_model_v3.py):** Fits all layers at a station jointly. InSAR is NOT a per-layer driver — it is the total surface target for a coupling coefficient α. The model physics is:

```
Step 1:  Δb_j(t) = S_ke_j · ΔH_j(t−τ_j) · I_e  +  S_kv_j · ΔH_j(t−τ_j) · I_i    [per layer, MLCW target]
Step 2:  α · Δd_v(t) = Σ_j Δb_j(t)                                                   [total, InSAR target]
```

Step 1 fits S_ke and S_kv per layer from MLCW **increments** only. Step 2 fits α (= 1/β, β ≥ 1) as a scalar from cumulative InSAR. The τ grid search operates on **anomaly incremental signals** — the climatological monthly mean is removed before searching, preventing the annual GWL pumping cycle from masking genuine short-lag hydraulic responses.

The preconsolidation head h_c is currently estimated as a fixed percentile of the full head record (e.g. the 10th percentile), computed once before fitting.

---

## Background: The Physical Process

Land subsidence across the Choushui River Alluvial Fan (CRAF) results from decades of excessive groundwater extraction. Excessive extraction causes hydraulic head decline in confined aquifer units. Hydraulic head decline reduces pore-fluid pressure in the sediment column. Reduced pore pressure transfers the constant overburden load onto the granular aquifer skeleton, increasing effective stress on the grain contacts. When effective stress exceeds the preconsolidation stress of fine-grained aquitards and interbeds, permanent inelastic compaction initiates — grain contacts break and rearrange irreversibly. Seasonal precipitation temporarily restores pore pressure and produces minor elastic rebound, but the permanent compaction is not recoverable.

Cumulative inelastic compaction at depth manifests as land subsidence at the surface, measured at rates of 4.2–5.2 cm/yr in mid-fan Yunlin County (2011–2022), with historical rates exceeding 12.2 cm/yr in 2003.

The project attempts to reconstruct depth-resolved compaction at 37 Multi-Layer Compaction Monitoring Well (MLCW) stations (Objective 1) and to predict that compaction at 8,577 unmonitored grid points spaced 500 m apart across the fan (Objective 2). The Water Resources Agency shut down 20 of 39 MLCW stations in 2021, removing the primary per-layer ground truth. IHM-F is the primary candidate for post-shutdown prediction.

---

## The Single Constraint That Governs Both Arguments

One constraint governs every proposed method: **the 8,577 prediction grid points carry no per-layer compaction ground truth.** No MLCW instruments exist at those locations. Any method — physics-based or machine learning — must transfer a relationship learned at 37 stations to those points. A method that cannot transfer in a physically meaningful way fails Objective 2 regardless of how well it fits at the 37 training stations.

This constraint simultaneously answers why pure black-box machine learning has limits (Question 1) and why the physics parameters must be stably estimated (Question 2).

---

## Question 1: Can Machine Learning Operate at the Well-by-Well Scale?

### At the 37 MLCW Stations: Machine Learning Is Applicable

At each MLCW station, observations of per-layer compaction exist across approximately 785 five-day epochs. Available inputs for model training include: GWL head increments per layer (from 189 MLCW-aligned well files), SBAS-InSAR surface displacement increments, day-of-year seasonal features, layer midpoint depth, and station coordinates. The prediction target is compaction increment per layer per epoch.

This is a supervised regression problem. Machine learning methods — including Long Short-Term Memory networks (LSTM), gradient-boosted trees, and neural ordinary differential equations — are applicable here. Published results on analogous alluvial systems support feasibility: Patra et al. (2025) achieved R² = 0.858–0.862 using random forests on Choushui River Fan-adjacent subsidence data, and Hung et al. (2025) demonstrated near-real-time extensometer forecasting using the Prophet framework.

**However, the effective data volume is smaller than the row count implies.** The 37 stations × 6 layers × 785 epochs produce approximately 174,000 rows, but these are 222 autocorrelated time series spanning only about 10 annual cycles. The effective independent sample size for learning a GWL-to-compaction relationship is closer to 10 seasonal repeats. This is why a large unconstrained neural network would overfit — the appropriate response is physics-constrained or strongly regularized modelling, not more model capacity.

### At the 8,577 Grid Points: The Transfer Problem Dominates

Per-layer MLCW compaction does not exist at grid points. A machine learning model trained at 37 MLCW stations cannot be applied per-layer at the grid because there is no per-layer target to anchor the prediction. Three transfer strategies exist:

**Strategy 1: Physics-parameter transfer (highest transferability).**
Estimate S_ske, S_skv, and τ at each of the 37 stations using IHM-F. Spatially interpolate those parameters to grid points using kriging with stratigraphic covariates (fan zone, layer midpoint depth, distance from the fan apex). Run the IHM-F forward equation at each grid point using interpolated parameters and kriged GWL head. Transferability is high because storage coefficients vary smoothly with lithology and depth. This is the approach IHM-F is designed to support.

**Strategy 2: Feature-based transfer (moderate transferability).**
Train a machine learning model at 37 stations using only features that also exist at grid points: InSAR displacement increments, kriged GWL head increments, day-of-year, layer depth, and coordinates. Apply the same model at grid points. Transferability is moderate — this assumes the 37 training stations represent the full spatial variation across the fan. In the stratigraphically heterogeneous distal fan, where thick clay-dominated aquitards concentrate inelastic compaction, this assumption is likely violated for deep layers.

**Strategy 3: Physics-structured encoder (highest transferability + time-varying parameters).**
Train a small neural network where the inputs are (GWL state, season, layer depth) and the outputs are time-varying effective S_ske(t), S_skv(t), and τ. The encoder feeds into the IHM-F forward equation, which computes compaction increments. Weights are shared across all 37 stations and all 6 layers so that the encoder learns a fan-wide function from observable state to physical parameters. At grid points, the same encoder runs using kriged GWL head and layer depth. This approach handles time-varying parameters naturally and transfers the full per-layer decomposition mechanism — not just regression weights — to unmonitored locations.

### On the Role of Continuous GNSS at MLCW Station Locations

Continuous GNSS (CGPS) instruments at some MLCW station locations measure total vertical surface displacement at a point, with millimetre-scale accuracy per epoch. SBAS-InSAR measures the same quantity at ~500 m spatial resolution. The two signals show R² ≈ 0.3–0.4 (r ≈ 0.6) agreement in this project, indicating they carry substantial independent information due to different atmospheric error structures and spatial footprints.

However, CGPS data do not solve the core problem. The prediction target is **per-layer compaction** — not total surface displacement. Total vertical displacement at the surface is the sum of compaction increments across all layers. Neither CGPS nor SBAS-InSAR contains information about which layer contributed which fraction. Only per-layer GWL head change, multiplied by the appropriate per-layer skeletal storage coefficient, decomposes the surface signal into per-layer contributions. CGPS and InSAR are both consequences of GWL change; GWL change is the physical driver.

CGPS carries a well-defined role in IHM-F v2: the InSAR co-driver term `β·x(t)` in the v2 design matrix captures compaction contributions from unmonitored aquifer intervals that the assigned GWL well does not record. CGPS, as a more accurate surface displacement measurement at training points, can improve the quality of that co-driver signal. In v3, the equivalent is the α coupling constraint in Step 2. In both versions, the surface displacement signal constrains the total but cannot decompose the layers.

The 91 CGPS stations in this project do not cover the 8,577 prediction grid points. Spatial extension requires either physics-parameter interpolation or a feature-based encoder — not point-accurate measurements at sparse locations.

---

## Question 2: Physical Parameters Are Not Constant — How Does the Physics Approach Handle This?

### Confirming the Non-Stationarity

The professor's concern is well-founded. Evidence from this project's own data confirms parameter variation across multiple timescales:

- S_ske values in `docs/s_ske_skv_tables.md` vary by approximately one order of magnitude between dry and wet seasons across multiple wells.
- Guangfu1 shows dry-season S_ske increasing 5.8-fold over the decade 2010–2021.
- The IHM-F theory document (Section 6.2, `discussions/discussion_20260528_ihm_theory.md`) explicitly states that fold-to-fold variation in S_skv is expected when the training window contains few inelastic epochs — not because the sediment changed, but because the inelastic column of the design matrix becomes near-zero and the coefficient is poorly constrained.

**An important clarification on the sign-swapping observation:** The dramatic S_ske sign-swing (+0.45 in Fold 1, −0.44 in Fold 2 at TUKU F1) reported in earlier diagnostics came from an *unconstrained* experimental run. The production IHM-F v2 solver enforces S_ske ≥ 0 via bounded least squares. The production solver cannot produce negative S_ske — but it *can* pin S_ske at zero when the elastic channel is unidentifiable, which is functionally equivalent to the coefficient being driven to its bound rather than to a physically meaningful value.

### Two Distinct Sources of Apparent Non-Stationarity

Non-stationarity in S_ske and S_skv originates from two physically distinct causes. They require different responses.

**Cause 1: Regime aliasing (the dominant source, immediately diagnosable).**

S_ske is the elastic storage coefficient, active only when head is above h_c. S_skv is the inelastic coefficient, active when head falls below h_c. If the training window of one walk-forward fold contains many drought years (many inelastic epochs) and another fold contains mostly wet recovery years (few inelastic epochs), the apparent storage coefficients differ — not because the sediment changed, but because each fold estimated a different weighted average of the two regimes.

The IHM-F theory document states this directly (Section 6.2): "Any fold with f_inel < 0.10 is flagged as having unreliable S_skv." The fraction of inelastic epochs `f_inel` must be reported alongside every fold result to distinguish genuine non-stationarity from estimation artefacts.

The current h_c is estimated as a fixed percentile of the full head record. A physically better estimate is the **running minimum**: h_c(t) = minimum GWL head observed up to time t. The running h_c automatically updates the elastic/inelastic regime switch as new head minimums are reached, tracking the evolution of preconsolidation stress as permanent compaction accumulates. This does not require predicting future parameter values — h_c(t) is computed from the observable GWL timeseries as the model runs forward.

**Cause 2: Material property evolution (genuine non-stationarity, harder).**

As inelastic compaction accumulates over years and decades, clay layers move down the virgin compression curve. The inelastic coefficient S_skv is the slope of that curve. In principle, S_skv itself can decline as effective stress accumulates. The running h_c fixes *where* the regime switch sits; it does not fix the *slope* inside the inelastic regime.

However, the IHM-F theory document (Section 6.2) makes an important claim: "Clay compressibility is a material property that changes negligibly over a 10-year observation window." The apparent decadal S_ske drift observed in the storage coefficient tables is more likely driven by the seasonal regime-aliasing mechanism than by genuine material change, though this cannot be assumed without testing.

A discriminating test is available within the existing walk-forward structure: fit S_skv separately using only inelastic-regime epochs from 2015–2018 versus 2022–2025. If S_skv remains stable once the regime is correctly isolated (f_inel is comparable across both windows), the decadal drift was regime aliasing. If S_skv continues to drift even in regime-isolated windows, material evolution is occurring and a stress-history term is warranted: S_skv(t) = S_skv,0 · exp(−λ · cumulative inelastic compaction up to t). This adds one feedback loop per layer — not a separate independent prediction problem.

### Does Predicting Future S_ske and S_skv Add Complexity?

For the regime-aliasing component: **no additional complexity.** The elastic/inelastic regime at any future epoch is determined by whether future GWL head exceeds h_c. Future GWL head is already the required external input to any IHM-F forward prediction. With a running h_c, the regime switch updates from the same GWL stream. No additional parameters need to be predicted.

For the material-evolution component of S_skv: **one feedback term per layer**, not an independent prediction. If S_skv declines with cumulative inelastic strain, the forward model computes cumulative inelastic compaction as it runs and updates S_skv from that internal state. This is a feedback within the running model, analogous to how a reservoir model updates aquifer storage as water is withdrawn.

**Critical observation about machine learning:** An LSTM or gradient-boosted tree trained on 2015–2021 data implicitly encodes whatever S_skv prevailed during that period. If S_skv changes over 2025–2030, the machine learning model's implicit parameters are equally outdated. Non-stationarity affects both approaches identically. The difference is that the physics-based approach makes the source of error explicit — parameter bounds, regime flags, f_inel diagnostics — while a black-box machine learning model fails silently with no signal that a physical mechanism has drifted.

---

## Evaluation Summary

| Issue | Machine Learning | IHM-F Physics | Physics-Structured Encoder (Hybrid) |
|---|---|---|---|
| Training at 37 MLCW stations | Applicable; data-thin (~10 annual cycles); needs regularization | Applicable; structured by Terzaghi consolidation equation | Strongest: physical structure + learned state-to-parameter mapping |
| Transfer to 8,577 grid points | Moderate; feature-based transfer may fail in distal fan | High; physics parameters interpolated with stratigraphic covariates | High; encoder inputs (GWL, depth) exist at every grid point |
| Seasonal S_ske variation | Absorbed implicitly; no diagnostic signal | Diagnosed via f_inel flag; fixed by correct regime switch + running h_c | Handled naturally; encoder maps GWL state to effective parameters |
| Decadal S_skv material drift | Silent degradation | Detectable via regime-stratified walk-forward test | Detectable; same stress-history feedback applies |
| Physical interpretability | Low; cannot identify which layer compacts or why | High; S_ske, S_skv, τ, β are physically interpretable | High; same physical interpretability |
| Deployability after MLCW shutdown | Limited; no per-layer target at grid points for retraining | Yes; parameters from 37 stations transferred via interpolation | Yes; encoder runs on observable inputs (GWL, depth) everywhere |

---

## Recommended Path Forward (7-Day Deadline Plan)

The following is what the project can realistically achieve before the submission deadline. It is scoped to what the code already does, with two targeted fixes that unblock the batch run. The longer-horizon items (running preconsolidation head, ridge regularization, physics-structured encoder) are deferred: they are scientifically sound but not needed to answer the professor’s two questions with the data in hand.

**Days 1–2 — Two code fixes that unblock the batch run:**

Fix 1: Change Step 2 of `joint_solve_fixed_tau()` in `ihmf_model_v3.py` from cumulative regression to incremental regression for α. The current code regresses cumulative predicted compaction against cumulative InSAR — both are near-unit-root series that share a common drift trend regardless of physical coupling, which produces a spuriously small α (observed: α=0.0197 on the full record vs α=0.023–0.163 on shorter walk-forward windows). Three lines of code change: replace `cum_pred` and `cum_insar` with the raw incremental arrays `db_pred_all` and `insar_trim` in the dot-product formula.

Fix 2: Raise `TAU_MAX` from 73 to 120 in `fit_ihm_f_v3.py` (one line: `TAU_MAX = 120`). At the current ceiling of 73 epochs (≈ 365 days), the shallow aquitard T1 hits the boundary at every station — meaning the true pore-pressure diffusion lag for T1 is longer than one year but is not yet estimated. Raising the ceiling to 120 epochs (≈ 600 days) allows T1 to find its true minimum-RSS lag without ceiling artefacts.

Re-run the TUKU pilot after both fixes. If α rises from 0.0197 toward 0.05–0.15 (the walk-forward range already suggests it should), the α defect is confirmed and the full-record fit is physically interpretable.

**Days 3–4 — Batch run and per-station results:**

Run the fixed IHM-F v3 on all 37 stations using the existing `fit_ihm_f_v3.py --all` entry point. Collect: α per station; S_ke, S_kv, τ per layer per station; walk-forward α fold-by-fold trend; regime composition f_inel per layer. Flag any station-layer where S_ke < 0 or S_kv < 0 (physical-law halt) — these are invalid fits, not just poor fits. Flag any station-layer where f_inel < 0.10 as data-limited for S_kv estimation.

**Days 5–7 — Results interpretation for the professor:**

The two questions the professor raised can be answered directly from the batch results.

On Question 1 (can machine learning work at the well-by-well scale and transfer to grid points): The IHM-F batch run shows which station-layers have strong GWL-to-compaction coupling (high R²_MLCW, τ interior to the search window) and which do not. Layers with weak coupling are precisely where a black-box machine learning approach would also fail to learn a transferable relationship — the physical signal is absent, not a modelling choice. This concretely bounds where machine learning is and is not applicable, and confirms that physical-parameter interpolation remains the only viable path to unmonitored grid points.

On Question 2 (non-stationarity of α, S_ke, S_kv over time): The walk-forward α trend across 4 folds (already visible in the TUKU pilot as 0.023→0.074→0.107→0.163) shows how the coupling estimate evolves as the model encounters drought years. Report f_inel per fold per station. If folds with higher f_inel consistently produce higher S_kv, that is regime-aliasing non-stationarity: diagnosable and not a fundamental barrier. If S_kv drifts even within inelastic-only epochs, a stress-history feedback term may be warranted. The batch data will show which case dominates across the fan, and that is the direct empirical answer to the professor’s concern about parameter instability.

---

## Conclusion

The professor's two arguments are substantiated by evidence from this project's own data and theory documents. Machine learning at the well-by-well scale is feasible for training at 37 stations but faces a structural transferability gap at unmonitored grid points, because per-layer compaction targets are absent there and the decomposition mechanism must transfer with the model. The physics-based IHM-F approach handles this transfer via parameter interpolation but operates under a stationarity assumption that is partially violated: apparent S_ske and S_skv variation across seasons and folds is real, but the dominant source is regime aliasing — an artefact of fitting to data windows with unequal proportions of elastic and inelastic epochs — which is diagnosable via the f_inel fraction and correctable by a running preconsolidation head. A residual material-evolution component in S_skv may exist over decadal scales and is testable within the existing walk-forward structure. Predicting future parameter values independently is not required: regime-switching corrections compute from observable future GWL head, and any material-drift feedback uses cumulative model output as its state variable. Within the one-week deadline, the actionable priorities are: fix the α cumulative-regression defect in v3 Step 2, raise TAU_MAX to 120 epochs, re-run the TUKU pilot, then run the batch across all 37 stations. The results of that batch run are the direct empirical evidence the professor needs to evaluate both arguments. Longer-horizon improvements — running preconsolidation head, ridge regularization toward literature priors, and a physics-structured encoder for grid-point transfer — are validated directions for future work but are not prerequisites for answering the questions raised in this debate.
