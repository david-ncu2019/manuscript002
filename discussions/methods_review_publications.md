# Methodology Review: Track B Candidates for InSAR–MLCW–GWL Subsidence Prediction

**Date:** 2026-05-25
**Type:** Independent methodological audit

---

## Part 1 — Are the Current Candidates (D, E, F) Appropriate?

### 1.1 Physical plausibility

The project is pursuing what is in essence a hybrid structural / statistical approach: use physical insight to constrain the model class (IHM or DLLM), fit parameters to data, then interpolate spatially. This is the right high-level strategy. The question is whether D, E, and F are the right specific models.

**Candidate F (IHM with per-layer β_k) — most physically defensible.** The IHMs two-regime structure mirrors the Terzaghi effective-stress framework: when head is above the preconsolidation head h_c, deformation is elastic (S_ske); when head drops below h_c, inelastic (irreversible) compaction begins (S_skv). The 2S-TOOL reference values at TUKU confirm that this distinction is real and large: S_kv/S_ke ratios range from 8.6× (T1) to 57.7× (F3). A model without a regime switch cannot capture this. Per-layer β_k is also physically necessary: the surface-displacement contribution of each layer (f̄_k from the static ratio) varies substantially — β_k must also vary.

**Candidate D (IHM with depth-invariant β₀) — physically wrong.** A single β₀ shared across all layers contradicts the most basic observation in the dataset: the static ratio f̄_k varies by 10-100× across depths. At TUKU, f̄_k peaks at ~0.06 near 150-200 m and falls to ~0.002 at shallow depths. Fitting a single β₀ forces all layers to share the same InSAR coupling, which means the fit must trade off errors between layers. The 2S-TOOL values show that different layers have vastly different skeletal storage coefficients. A single β₀ will be dominated by the largest-amplitude layer and will systematically mispredict all others. Candidate D should be retired as a production candidate. It is useful only as a diagnostic: if per-layer β_k is poorly constrained (high variance), depth-invariant β₀ may serve as a regularized fallback. But it should not be the primary method.

**Candidate E (DLLM) — structurally mismatched to the physical system.** The DLLM treats compaction as a linear convolution of past head and InSAR values: Ŷ̃_k(i) = Σ w^h_j·h̃(i-j) + Σ w^x_j·x̃(i-j). This assumes the system response is linear, time-invariant, and regime-independent. None of these hold.

Specifically:
- Compaction is not regime-independent. The elastic and inelastic responses differ by 10-60×. A single linear filter cannot represent both regimes simultaneously — it will fit an average that under-predicts during inelastic episodes and over-predicts during elastic recovery.
- The response is not linear in head. Below h_c, the compaction depends on the cumulative head deficit, not just the instantaneous head. The DLLM's lagged-head formulation captures delayed drainage but not the threshold effect.
- The DLLM's 21 weights per layer (L=15, M=4) are not identifiable from geophysical first principles. There is no prior expectation for what w^h_3 vs w^h_7 should look like — the only constraint comes from the ~500 calibration epochs.

The DLLM would be appropriate for a system exhibiting linear, stationary dynamics (e.g., tidal loading of a confined aquifer). The CRAF does not meet these conditions.

**The D-vs-E decision rule using only TUKU is fragile.** TUKU is a high-subsidence station in the cone of depression. Its regime characteristics (S_kv/S_ke up to 57.7×) may not generalize. Applying a rule evaluated at one station to a binary choice applied to all 37 stations violates the project's own principle of not making station-level structural selections. The rule should use data from multiple stations, or be replaced by a default adoption of Candidate F (see Part 5).

### 1.2 Statistical identification

**Number of parameters vs. data points.** All three candidates are estimable from ~500 calibration epochs per depth/layer:
- DLLM: ~21 weights per layer (L+1 + M+1). Six layers = ~126 parameters per station. Data-to-parameter ratio ~4:1. With autocorrelated (non-i.i.d.) residuals, the effective sample size is substantially smaller. Expect overfitting.
- IHM-F: 4 parameters per layer. Six layers = ~24 parameters per station. Data-to-parameter ratio ~21:1. Better conditioned, but S_ske and S_skv may not be simultaneously identifiable if one regime dominates.
- τ (lag in IHM-F): This is not a free parameter — it is selected by grid-search minimization of training RMSE. This meta-optimization inflates the effective degrees of freedom and risks overfitting to noise. The τ selection should use a validation set, not the training set.

**Regime imbalance risk.** If only 5-10% of calibration epochs are inelastic (which is possible at stations far from pumping centers), S_skv is estimated from very few data points. Its uncertainty will be large. The IHM-F fit will then predict inelastic epochs poorly, and the regime-switching mechanism adds complexity without benefit at quiescent stations.

**Residual autocorrelation.** All three candidates use OLS on trend-removed signals. The residuals are almost certainly autocorrelated (the detrended MLCW and GWL retain temporal structure). OLS coefficient standard errors under autocorrelation are underestimated, and the predictions may be overconfident. This is not a fatal flaw — OLS coefficients remain unbiased — but the RMSE-based model comparison should be interpreted cautiously. The fold-1 RMSE (2022, full year of extrapolation) is a more honest measure than per-epoch RMSE within folds.

### 1.3 Spatial transferability

This is the binding constraint. Stage 2 requires interpolating per-station parameters to 8,577 grid points. The candidates differ fundamentally in what they produce for interpolation.

**IHM-F parameters (krigeable):**
- S_ske, S_skv (m⁻¹: physical storage coefficients correlated with lithology and hydrofacies)
- β_k (mm/mm: layer-specific InSAR coupling, dimensionless, summable across layers to α)
- τ (epochs or days: drainage lag, linked to clay layer thickness and hydraulic diffusivity)

All four have expected spatial structure. The BME hydrofacies model provides a covariate for kriging. The storage coefficients should vary systematically with lithology, which is mapped. Spatial interpolation is standard practice for hydrogeological parameters.

**DLLM weights (not krigeable):**
- 21-dimensional weight vectors per layer have no obvious spatial structure
- The physical meaning of individual weights (w^h_3 vs w^h_7) is not clear enough to guide interpolation
- One could interpolate summary statistics (total gain, mean lag, peak lag), but this discards the distributed-lag detail that is the model's only advantage

**Verdict for spatial transferability: IHM-F clearly wins.** This is a decisive advantage.

### 1.4 The GWL proxy problem

Twenty-four of 37 stations (65%) use nearest-proxy GWL. This is the single largest threat to Track B's success.

**Effect mechanism.** When a station uses proxy GWL, any mismatch between the proxy and the true local head propagates into the model as measurement error in the regressor. This causes:
- DLLM: attenuation bias (coefficients shrunk toward zero). The learned impulse response is weaker than the true response.
- IHM-F: biased regime classification if proxy h_c differs from true local h_c. If the proxy head is systematically higher than the local head, epochs may be misclassified as elastic when they are actually inelastic.

**Known failure mode at Xizhou.** Xizhou is one of the ratio-unstable stations from the ablation study (anchor-only RMSE improvement = 3.0%, near zero). It uses proxy GWL. The ratio instability at Xizhou may be caused by the proxy GWL mismatch rather than a change in the compaction ratio itself. Pilot 2's inflation check at Xizhou is diagnostic, but one station does not bound the problem across all 24 proxy stations.

**Recommendation:** The inflation check should be applied to a stratified sample of 4-5 proxy stations spanning different distances to the GWL station and different hydrogeological settings. A single threshold at Xizhou may be misleadingly low or high.

### 1.5 The column sum constraint

Neither D, E, nor F enforces Σ Ŷ_k = α·x (the sum of predicted layer compaction should equal the fraction of InSAR surface displacement attributable to the 0-300 m column). This is a physical inconsistency.

**Why it matters.** The InSAR at each station measures the total surface displacement. The 60 MLCW depth slabs (or 6 hydrogeological layers) collectively represent compaction of the 0-300 m column. Compaction below 300 m is captured by InSAR but not by MLCW. The α prior (α = v_MLCW / v_InSAR ≈ 0.45-0.55 at TUKU) quantifies this fraction. If the model predicts Σ Ŷ_k ≠ α·x, either:
1. The model is over- or under-predicting the relative contribution of the shallow column; or
2. The model parameters are inconsistent with the velocity-ratio constraint.

**A simple fix exists.** After per-layer independent fitting, renormalize the InSAR coefficients:

β_k' = β_k · α / Σ β_k

This preserves the relative distribution while satisfying Σ β_k = α. The S_ske and S_skv values are unaffected. This should be applied as a default post-processing step.

---

## Part 2 — What Viable Approaches Have Been Overlooked?

### 2.1 Three-regime IHM (highest priority for piloting)

The current two-regime IHM misses an important physical distinction: when head drops below h_c and stabilizes (or recovers), the rate of inelastic compaction changes. Clay layers continue to compact slowly after the driving head gradient dissipates — this is secondary consolidation / creep, which is well-documented in CRAF sediments.

Proposed regimes:
- **Regime 1 (elastic):** h_raw > h_c. Deformation is reversible, coefficient S_ske. Compaction = S_ske · Δh. This matches the existing model.
- **Regime 2 (active inelastic):** h_raw ≤ h_c AND dh_raw/dt < 0 (head still declining). Coefficient S_skv (primary consolidation). Compaction = S_skv · Δh. This matches the existing model.
- **Regime 3 (secondary consolidation):** h_raw ≤ h_c AND dh_raw/dt ≥ 0 (head stable or recovering). Coefficient S_skv' ≤ S_skv. Compaction = S_skv' · Δh.

The S_skv' / S_skv ratio quantifies how much the compaction rate slows after head stabilizes. The 2S-TOOL value S_skv implicitly averages over regimes 2 and 3. A three-regime model would separate them.

**What this changes.** One additional parameter per layer (S_skv'). Minimum code change from IHM-F. The regime test requires adding dh/dt to function signatures. The parameter estimation may be more robust because S_skv' is estimated from a distinct subset of epochs.

**Pilot trigger condition.** If Pilot 1 shows: (a) significant inelastic activity (>20% of epochs at >50% of layers), AND (b) hold-out RMSE at F3/F4 (deep clay-rich layers) is >2× the shallow-layer RMSE, then the single S_skv is not capturing the full inelastic response correctly. The three-regime extension should be piloted.

### 2.2 Hierarchical Bayesian per-station model (medium priority)

The current approach fits parameters independently per station, then kriges the results in a separate Stage 2. This two-stage approach discards information: stations with well-constrained parameters contribute equally to the kriged map as stations with poorly constrained parameters.

A hierarchical Bayesian model would share statistical strength across stations:
```
Level 1 (regional):  θ_k(x,y) ~ GP(μ_k, Σ_k)   # storage coefficients vary spatially
Level 2 (station):   θ_{s,k} ~ N(θ_k(x_s,y_s), σ²_s)  # station draws from regional field
Level 3 (epoch):     Ỹ_{s,k}(t) = f(h̃_s, x̃_s; θ_{s,k}) + ε   # per-epoch prediction
```

This framework:
- Naturally handles the 24 proxy-GWL stations by treating true local GWL as a latent variable with a prior derived from the proxy station, with uncertainty proportional to distance
- Produces posterior uncertainty for each station's parameters, which propagates to spatial predictions
- Enables the unified formula requirement (same model structure, station-specific draws)
- Eliminates the separate Stage 2 interpolation — interpolation is built into the hierarchy

**Feasibility.** For 6 layers × 37 stations = 222 parameter sets, with 4 parameters each = 888 scalar latent variables. Plus regional GP parameters. This is a moderate-dimensional inference problem — doable with HMC (NumPyro, PyMC) or variational inference (Pyro).

**Why not start here.** Hierarchical modeling is a significant engineering investment. The simpler per-station OLS approach should be evaluated first to understand the parameter distributions. If the parameters are well-behaved (smooth spatial variation, physically plausible values), the two-stage approach is adequate. If the parameters are noisy or have non-trivial spatial structure, hierarchical Bayesian modeling would add genuine value.

### 2.3 Multi-output Gaussian Process (MOGP) for the full depth profile (medium priority)

The current approach fits each layer independently. But the 6-layer profile is a correlated multivariate output — compaction in F2 and F3 respond to the same pumping stress. A MOGP models:

Ỹ(x, t, z) ~ GP(m(x, t, z), K((x,t,z), (x',t',z')))

with a separable kernel: K = K_spatial ⊗ K_temporal ⊗ K_depth. This captures cross-depth, cross-time, and cross-location correlations in a single model.

For the 6-layer representation (6 outputs × 500 epochs × 37 stations ≈ 111,000 observations), exact MOGP inference is expensive but tractable with sparse GP approximations (SVGP, 500 inducing points).

**Advantages.** The GP naturally handles missing data (stations without GWL), provides calibrated prediction uncertainty, and the depth kernel directly captures the physical constraint that adjacent layers compact similarly. The sum constraint is trivially enforced: posterior samples from the GP can be summed post-hoc.

**Why not start here.** The GP treats the relationship between GWL/InSAR and compaction as a smooth function learned from data — it is a data-driven method, not a physics-based one. This violates the "interpretable parameters" constraint if the kernel hyperparameters are treated as opaque. Additionally, the non-stationary behavior (regime change at h_c) is difficult to encode in a GP kernel.

### 2.4 Other approaches evaluated and set aside

**Full Terzaghi consolidation equation (one-dimensional).** Requires information not available: drainage path length, vertical hydraulic conductivity (or consolidation coefficient c_v) for each clay layer, and the initial excess pore pressure distribution. The IHM approximates this with a scalar lag τ. A full PDE solver would require substantially more hydrogeological characterization than currently exists in the dataset. Not recommended for this project stage.

**Neural network / ensemble methods (Random Forest, Gradient Boosting, LSTM).** These are permitted under the project's May 2026 rule change, but they violate the "interpretable parameters" constraint. A neural network's hidden units do not have physical units (mm/mm, days, m⁻¹). Attention weights and SHAP values are post-hoc attribution, not primary outputs. A model whose primary outputs are per-depth Ŷ_k but whose internal parameters are uninterpretable would still be acceptable for the prediction task, but the requirement that "depth-level parameters must be interpretable in physically meaningful units" rules out black-box models for the primary publication method. Keep as long-term research target.

**Joint inversion with spatial smoothness prior.** This is the most natural extension of the existing Stage 1 inversion framework. It solves for all stations simultaneously with a penalty on spatial roughness of β_k, S_ske, S_skv. The cost function is non-convex (regime switch introduces a hard threshold). Solvable with gradient-based optimization and relaxed regime indicators (e.g., sigmoid transition around h_c). Worth considering after per-station fits are available and the parameter spatial structure is understood.

---

## Part 3 — Critical Assessment of the IHM's Regime-Switching Logic

### 3.1 h_c from the calibration-window minimum

The plan uses h_c(k) = min_{t in calib} h_raw(k, t). This has three problems:

**Problem 1: Extrapolation below the calibration minimum.** The 2022 drought may push heads below any level observed in 2015-2021. Below the calibration minimum, the model has no data — S_skv applies unconditionally. But the physical compaction response may change at unprecedented low heads: the virgin compression curve may steepen (increased inelastic rate) or the clay layer may be fully drained (reduced rate). Either way, the model cannot know because it has never seen heads this low.

The current plan implicitly assumes the S_skv estimated from the calibration window (which contains some inelastic epochs but not necessarily the most extreme ones) applies universally. This is only valid if the inelastic compressibility is constant over the stress range — a strong assumption that contradicts soil mechanics (compression index C_c is stress-dependent).

**Fix:** After Pilot 1, examine whether hold-out heads (2022-2025) at TUKU go below the calibration minimum. If they do, compare the model's error during those extreme epochs vs. during moderate inelastic epochs. If errors are systematically larger at extreme heads, add a "deep virgin" regime: for h < h_c - δ, use S_skv' (estimated if enough data exists) or a multiplicative factor.

**Problem 2: Minimum is fragile.** A single anomalously low reading (data artifact, measurement error, reconstruction artifact) would set h_c too low and misclassify many epochs as elastic. The minimum is the least robust order statistic.

**Fix:** Use the 5th percentile of calibration-window head instead of the minimum. This is still a simple scalar per layer, is robust to outliers, and is physically defensible (the preconsolidation head is not a sharp threshold in real sediments — it is a transition zone). Document this choice explicitly.

**Problem 3: The regime test uses raw h(t), not detrended h̃(t).** This is correct physically (the sediment responds to absolute head, not head anomaly). But it creates a subtle inconsistency: the regression target is Ỹ(k) (detrended MLCW), and the GWL driver is h̃(t-τ) (detrended head), yet the regime switch uses raw h(t). The detrending of head and the regime test are on different GWL scales. This is acceptable if the trend is small relative to the seasonal amplitude, but should be flagged.

### 3.2 Is S_skv the right coefficient for all h < h_c?

The IHM applies S_skv for EVERY epoch where h(t) < h_c, regardless of:
- How long the head has been below h_c (immediately after the threshold crossing vs. years into the inelastic regime)
- The rate of head decline (rapid drawdown vs. slow seasonal decline)
- Whether the clay layer has fully drained

In Terzaghi consolidation theory, the compaction of a clay layer after a step increase in effective stress follows a time-dependent drainage curve: approximately 50% completion at t = 0.197·H²/c_v (where H = drainage path length, c_v = consolidation coefficient). For a 10 m clay layer with c_v = 10⁻⁷ m²/s, this is ~230 days. The 5-day epoch spacing is much shorter than the clay drainage time.

This means: **the current IHM's S_skv conflates primary consolidation with the ongoing drainage process.** The grid-search τ absorbs some of this delay (τ ≈ 3-30 epochs ≈ 15-150 days), but the constant S_skv does not capture the time-dependent decay of the consolidation rate.

**Practical consequence.** At deep clay layers (F3, F4 at TUKU, where S_kv/S_ke = 57.7× and 43.0×), the hold-out RMSE may be worse than at shallow layers because the time-dependent consolidation is not captured by a constant S_skv. If Pilot 1 shows depth-dependent RMSE increasing below 150 m, this mechanism is the likely cause.

### 3.3 Duration threshold

Should the IHM require a minimum duration below h_c before switching to inelastic? Physically, a brief excursion below h_c (one 5-day epoch) does not trigger significant inelastic compaction because the clay drainage time exceeds the excursion duration.

A minimum duration requirement — say, 30 consecutive days below h_c — would prevent the model from overreacting to short head dips. This adds one hyperparameter (the duration threshold) and requires tracking regime history rather than per-epoch tests.

**Recommendation:** Do not implement this in the initial pilot. The 5-day InSAR cadence means a single epoch excursion is a 5-day minimum. With MLCW data reconstructed at ~12-day cadence, adjacent epochs are already smoothed. If Pilot 1 shows that the IHM overpredicts inelastic compaction during intermittent head dips (visible as RMSE spikes at specific epochs), add the duration threshold as a refinement. Save the diagnostic first.

---

## Part 4 — The Trend-Removal Approach

### 4.1 Is linear trend removal sufficient? — No, but it may be adequate

The signals (MLCW Y_k, InSAR x, GWL h_k) all contain multi-year nonlinear trends:
- Subsidence rates accelerate during drought years and decelerate during wet years
- GWL shows step changes from management interventions and pumping cycles
- The MLCW parametric model already removed long-period harmonics (5-year, 10-year), but nonlinear secular trends remain

Linear detrending over the 2015-2021 calibration window captures only the mean rate. The residuals contain:
1. Deceleration/acceleration patterns (the nonlinear component of the trend)
2. The 2022 drought anomaly (which is partially trend, partially seasonal)
3. Interannual variability that the model should predict

For Fold 1 (2022), the linear trend extrapolation will be wrong if 2022 heads behave differently from the 2015-2021 average. This is why fold-1 RMSE is expected to be worse.

**Specific concern for GWL.** Linear detrending of GWL removes the long-term trajectory, which is precisely the signal that drives inelastic compaction. After detrending, h̃(t) captures only the short-term head fluctuations. The IHM then predicts compaction as a function of h̃(t), but the inelastic compaction is driven by the cumulative head deficit — which is a trend-like quantity. This tension is inherent in any detrend-then-predict approach applied to systems with memory.

### 4.2 How are predictions on the original scale recovered? — Design gap

The implementation plan does not specify how to back-transform predictions from trend-removed space to the original scale. The required sequence is:

1. Fit trend on calibration window: Y_k(t) = a_k·t + b_k + Ỹ_k(t) (and similarly for h_k, x)
2. Remove trends → Ỹ_k(t), h̃_k(t), x̃(t)
3. Fit model: Ŷ̃_k = f(h̃, x̃)
4. Predict in hold-out → Ŷ̃_k (trend-removed prediction)
5. Add back trend: Ŷ_k(t) = a_k·t + b_k + Ŷ̃_k(t)

This works only if the trend slopes a_k are consistent across Y_k, h_k, and x through the model relationship. For the IHM, the relationship is nonlinear (regime-dependent), so the trend-back transformation does not perfectly recover the original-scale prediction unless the trends are physically consistent.

**Inconsistency example.** If MLCW Y_k has a negative linear trend (-5 mm/yr), InSAR x has a negative trend (-10 mm/yr), and GWL h_k has a flat trend (0 m/yr), the model predicts compaction from h̃. The predicted trend-removed compaction Ŷ̃_k may be near-zero (no head anomalies), but the original-scale prediction must add back -5 mm/yr from the MLCW trend. This means the prediction inherits the calibration-window MLCW trend even when heads are unchanged — a physically questionable extrapolation.

**Recommended fix.** After trend-removing all streams, do NOT add back the MLCW trend for hold-out predictions. Instead, let the InSAR and GWL trends propagate through the model to determine the predicted trend in compaction. This is more physically consistent: the predicted trend in compaction comes from the drivers (InSAR and GWL), not from the calibration-window average. Formally: use the InSAR and GWL trends to back-transform, not the MLCW trend.

### 4.3 Does trend removal mask the target signal? — Yes, partially

The long-term inelastic compaction is a trend-like signal. Removing the linear trend means the model only predicts deviations from the calibration-window average trajectory. The long-term acceleration or deceleration of subsidence — which is the most policy-relevant quantity (is subsidence getting worse?) — is not predicted by the model. It is absorbed into the intercept and slope of the trend, which are extrapolated unchanged.

For a production system deployed when MLCW monitoring stops, this means:
- The model can predict seasonal and interannual deviations from the trend (short-term)
- The model cannot predict whether the long-term subsidence rate is increasing or decreasing (long-term)
- The long-term prediction is just the calibration-window trend extrapolated indefinitely

**Alternative.** Instead of detrending, include the trend explicitly in the model. For example, the IHM could include a linear time term:

Ŷ_k = S_ske · h̃(t-τ) + S_skv · h̃(t-τ) · I(h<h_c) + β_k · x̃(t) + γ_k · t + c

The γ_k term captures residual secular drift not explained by head and InSAR variations. This keeps the trend in the model and allows it to be influenced by the drivers. This adds one interpretable parameter (γ_k, mm/day) per layer.

**Recommendation.** Add a linear time term to the IHM-F as a default. This is a one-parameter increase per layer (from 4 to 5). It solves the trend-back problem (the model operates on the original scale directly) and ensures the secular drift is not silently discarded.

---

## Part 5 — Recommendations

### 5.1 Candidate selection

**Adopt IHM-F (Candidate F) as the production method by default.** Retire Candidate D (depth-invariant β₀) as a production candidate — keep it only as a regularization diagnostic. Keep DLLM (Candidate E) as a comparison benchmark only.

Rationale for not using the D-vs-E decision rule:
- TUKU alone does not represent all 37 stations
- The IHM's two-regime structure is physically required given the 10-60× S_kv/S_ke ratios already documented
- IHM-F parameters are krigeable; DLLM weights are not
- 4 parameters per layer (IHM-F) is better conditioned than 21 weights (DLLM)

The decision rule should be replaced with a regime-activity diagnostic table for all stations (not just TUKU), saved to CSV. This informs the choice between two-regime vs. three-regime IHM (see below), not the choice between IHM and DLLM.

### 5.2 Immediate refinements to IHM-F (before Pilot 3)

**1. Use 5th percentile h_c instead of minimum.** More robust. Same implementation cost.

**2. Add column sum constraint.** Post-fit renormalize β_k' = β_k · α / Σ β_k. This is a 5-line addition.

**3. Add linear time term γ_k·t to the model.** This eliminates the trend-back ambiguity and allows the model to operate on original-scale (or at least consistently detrended) data. The γ_k captures residual secular drift.

**4. Revise the D-vs-E decision to a three-way diagnostic.** After Pilot 1, produce a table showing regime activity (fraction inelastic) at ALL stations with co-located GWL. If inelastic fraction exceeds a threshold (20%) at most stations, the two-regime IHM is justified. The decision is about two- vs. three-regime IHM, not IHM vs. DLLM.

### 5.3 What to pilot first (in order)

**Pilot 1a (immediate, from current state):** IHM-F at TUKU with the four refinements above. Use 5th-percentile h_c, add γ_k·t, add post-fit β_k normalization. Compare against the unmodified IHM-F to see if these refinements improve fold-1 RMSE.

**Pilot 1b (contingent, if Pilot 1a shows depth-dependent error at F3/F4):** Three-regime IHM at TUKU. Add the head-rate criterion (dh/dt ≥ 0 → S_skv'). Compare RMSE at F3/F4 layers against standard IHM-F. If improvement >10% at the worst layer, carry forward.

**Pilot 2a (revised scope):** Instead of only Xizhou, test proxy-GWL inflation at 4-5 stations spanning the range of distances and settings (one close <500 m, one moderate 500-2000 m, one far >2000 m, one fully blocked). This bounds the proxy problem. Use the refined IHM-F from Pilot 1a.

### 5.4 What to deprioritize

**DLLM (Candidate E).** It should not be the production method. Its non-transferable weight vectors make it unsuitable for Stage 2. Use it only as a reference comparison (how much worse is a regime-free linear filter?) in the published benchmark table.

**Full ARX with ϕ_k.** The ablation study already showed it is worse than anchor-only at 15/19 stations. ϕ_k ≈ 1.0 adds nothing over the anchor. Do not invest further.

### 5.5 The GWL proxy problem — long-term strategy

Twenty-four of 37 stations use proxy GWL. No amount of model sophistication can recover information that is not in the data. The proxy GWL is a fundamentally weaker signal than co-located GWL.

**Acceptable framing for publication.** The 13 co-located stations form the validation set for Track B. The 24 proxy stations demonstrate operational performance under realistic monitoring conditions (GWL available regionally but not co-located). The fold-1 results at the 13 co-located stations should be reported as the primary validation metric. The proxy-station results quantify the performance degradation from horizontal GWL interpolation, which is a known physical limitation of the study design — not a model failure.

**Stage 2 spatial transferability.** At grid points (8,577 locations), the GWL from the nearest monitoring well is the only available input — this is identical to the proxy scenario. If IHM-F works at proxy stations (even with inflated RMSE compared to co-located stations), it will transfer to grid points. If it fails at proxy stations, the spatial extension plan needs re-evaluation. This makes Pilot 2a (multi-station proxy inflation) the single most informative experiment before Stage 2.

### 5.6 Summary of changes to the existing plan

| Current approach | Recommended change | Priority |
|---|---|---|
| h_c = calibration-window minimum | h_c = 5th percentile of calibration window | High (before Pilot 1) |
| β_k fitted independently per layer | Post-fit renormalize: β_k' = β_k · α / Σ β_k | High (before Pilot 3) |
| Trend-remove then predict then add back | Add γ_k·t term; model operates on consistently detrended data | High (before Pilot 3) |
| D-vs-E decision on TUKU alone | Default adopt IHM-F; drop decision rule | High (before Pilot 3) |
| DLLM as production candidate | Demote to comparison benchmark only | Medium |
| Two-regime IHM only | Pilot three-regime extension if F3/F4 RMSE > 2× shallow | Medium (contingent) |
| Xizhou as single proxy test | Stratified proxy test at 4-5 stations | High (before Stage 2) |
| 2S-TOOL reference values used for decision | Use regime-activity table from actual data at all stations | Ongoing |

---

*This review was prepared by an independent research consultant. It reflects the physical understanding of the Choushui River Alluvial Fan, the data available, and the project's stated requirements. All recommendations are actionable within the existing codebase with minimal additions to the current implementation plan.*

---

## Appendix A — Supporting Literature for the IHM-F Approach

This appendix lists the publications that provide the methodological, physical, and empirical foundation for Candidate F (the two-regime Inelastic Head Model with per-layer InSAR coupling β_k). The papers are grouped by their role in the argument chain.

### A.1 Foundational framework: skeletal storage coefficients and the elastic/inelastic distinction

The IHM-F's central idea — that aquifer-system compaction separates into an elastic (recoverable) regime above the preconsolidation head and an inelastic (irreversible) regime below it — is grounded in a half-century of hydrogeological theory and observation.

**Helm, D. C. (1975).** One-dimensional simulation of aquifer system compaction near Pixley, California: 1. Constant parameters. *Water Resources Research*, 11(3), 465–478. https://doi.org/10.1029/WR011i003p00465

**Helm, D. C. (1976).** One-dimensional simulation of aquifer system compaction near Pixley, California: 2. Stress-dependent parameters. *Water Resources Research*, 12(3), 375–391. https://doi.org/10.1029/WR012i003p00375

> Helm established the numerical framework for simulating aquifer-system compaction with separate elastic and inelastic skeletal storage coefficients (S_ske and S_skv). The Helm model is the direct mathematical ancestor of the IHM-F: it solves a one-dimensional consolidation equation in which the storage coefficient switches between S_ske and S_skv depending on whether the effective stress exceeds the preconsolidation stress. The IHM-F in this project collapses Helm's spatial PDE to a lumped-parameter per-layer OLS formulation, retaining the essential regime-switching logic while making it estimable from MLCW time series without a full numerical model.

**Riley, F. S. (1969).** Analysis of borehole extensometer data from central California. In *Land Subsidence*, vol. 2, pp. 423–431. UNESCO. https://unesdoc.unesco.org/ark:/48223/pf0000014816

> Riley's borehole extensometer analysis in the San Joaquin Valley provided the first direct field evidence that aquifer-system compaction separates into elastic and inelastic components. Riley showed that compaction measured by borehole extensometers follows different stress-strain slopes during water-level recovery (elastic) versus decline (inelastic), with the ratio between the two slopes typically ranging from 5× to 100× in clay-rich sediments. The 2S-TOOL results at TUKU (S_kv/S_ke ranging from 8.6× to 57.7× across six layers) are a direct replication of Riley's finding in the CRAF setting.

**Poland, J. F. (1984).** *Guidebook to studies of land subsidence due to ground-water withdrawal*. Studies and Reports in Hydrology, vol. 40. UNESCO. https://unesdoc.unesco.org/ark:/48223/pf0000065167

> The UNESCO Guidebook remains the comprehensive reference for the conceptual model underlying IHM-F: the effective-stress framework for compaction, the definition of skeletal specific storage, the distinction between elastic storage (recoverable) and virgin-compression storage (irreversible), and the role of the preconsolidation stress threshold. It codifies the standard practice that this project follows.

**Poland, J. F., & Ireland, R. L. (1977).** Land subsidence due to groundwater withdrawal in the United States. *Journal of the Irrigation and Drainage Division*, 103(1), 37–51.

> Poland and Ireland documented the spatial extent and magnitude of subsidence across multiple U.S. aquifer systems, establishing the empirical link between groundwater level decline, clay-layer thickness, and irreversible compaction. Their observation that "subsidence is essentially permanent because the compaction of clay layers is largely inelastic" is the physical justification for treating S_skv as the primary parameter for drought-year compaction prediction.

### A.2 InSAR integration with hydrogeology

**Galloway, D. L., & Hoffmann, J. (2007).** The application of satellite differential SAR interferometry-derived ground displacements in hydrogeology. *Hydrogeology Journal*, 15(1), 133–154. https://doi.org/10.1007/s10040-006-0121-5

> Galloway and Hoffmann established the template for using InSAR-derived surface displacement to infer subsurface hydrogeological processes. They demonstrated that InSAR can resolve elastic (seasonal) and inelastic (secular) components of aquifer-system compaction, that the ratio of seasonal amplitude to secular trend constrains the elastic-to-inelastic storage ratio, and that InSAR-derived time series can be compared directly to borehole extensometer and well data. The IHM-F's co-use of InSAR (as the spatial co-driver x̃) and GWL (as the depth-resolved hydraulic driver h̃) follows directly from the framework Galloway and Hoffmann articulated.

**Galloway, D. L., & Burbey, T. J. (2011).** Review: Regional land subsidence accompanying groundwater extraction. *Hydrogeology Journal*, 19(8), 1459–1486. https://doi.org/10.1007/s10040-011-0775-5

> This review provides the most comprehensive treatment of the mechanisms, measurement methods, and modelling approaches for regional subsidence. It validates the IHM-F approach on multiple counts: (1) it confirms that the S_ske/S_skv framework is the standard approach for modelling aquifer-system compaction at the regional scale; (2) it documents that inelastic storage coefficients are typically one to three orders of magnitude larger than elastic values — consistent with the TUKU 2S-TOOL ratios; (3) it identifies the estimation of S_skv as the single most important parameter for predicting future subsidence under continued head decline; and (4) it recommends InSAR as the primary observational constraint for calibrating regional compaction models.

**Hoffmann, J., Zebker, H. A., Galloway, D. L., & Amelung, F. (2001).** Seasonal subsidence and rebound in Las Vegas Valley, Nevada, observed by synthetic aperture radar interferometry. *Water Resources Research*, 37(6), 1551–1566. https://doi.org/10.1029/2000WR900404

> Hoffmann et al. used InSAR to map seasonal (elastic) and secular (inelastic) subsidence in Las Vegas Valley, showing that the two components can be separated from the InSAR time series alone and that their ratio is spatially variable. This directly motivates the per-layer InSAR coupling fraction β_k in IHM-F: if the elastic/inelastic ratio varies spatially at the surface, it must also vary vertically across depth layers. The paper also demonstrated that InSAR-derived seasonal amplitude correlates with the thickness of compressible fine-grained sediments, which is the same physical relationship that the hydrofacies covariate in the CRAF dataset captures.

**Reeves, J. A., Knight, R., & Zebker, H. A. (2011).** A method to estimate the temporal evolution of land subsidence from InSAR and well data. *Water Resources Research*, 47(12), W12503. https://doi.org/10.1029/2011WR010713

> Reeves et al. developed a method to jointly invert InSAR and well data for the temporal evolution of compaction, treating the contribution of each well-screened interval as an unknown to be estimated. Their approach is the closest published methodological precedent to IHM-F: they solve for per-interval compaction from InSAR surface displacement and head observations, using a forward model that explicitly separates elastic and inelastic responses. IHM-F extends this approach by using MLCW as the training target (instead of inverting for compaction from InSAR alone), adding per-layer GWL assignment by depth-range matching, and replacing the full inversion with a per-layer OLS formulation that is simpler and more robust with the CRAF dataset.

### A.3 Lag and delay in aquifer-system response

**Chen, J., Knight, R., & Zebker, H. A. (2016).** The temporal and spatial variability of the confined aquifer head and the delay in the response of the aquifer system to groundwater pumping. *Water Resources Research*, 52(5), 3673–3694. https://doi.org/10.1002/2015WR017592

> Chen et al. quantified the time delay τ between head change and aquifer-system compaction across multiple wells in the San Joaquin Valley, finding values ranging from 0 to approximately 140 days for elastic deformation. They also showed that τ increases with clay-layer thickness and is systematically larger for inelastic deformation. The IHM-F's grid search over τ (0 to 50 epochs ≈ 0 to 250 days) follows Chen et al.'s methodology of treating τ as an estimated parameter rather than a prescribed constant. The paper also demonstrates that ignoring τ (setting τ = 0 in all layers) inflates RMSE by 15–30% at wells with thick clay sequences, which motivates IHM-F's τ parameter for the clay-rich F3 and F4 layers at TUKU.

### A.4 Depth-interval deformation apportionment with InSAR

**Smith, R. G., Hashemi, H., Chen, J., et al. (2021).** Apportioning deformation among depth intervals in an aquifer system using InSAR and head data. *Hydrogeology Journal*, 29, 2475–2486. https://doi.org/10.1007/s10040-021-02386-0

> Smith et al. is explicitly treated in this project as "the floor, not the ceiling" (CLAUDE.md). Their method apportions InSAR surface deformation among three depth intervals at a single well using a purely elastic model with per-interval S_ke and τ. IHM-F improves on Smith et al. along five dimensions: (1) resolves 60 depth levels (or 6 hydrogeological layers) instead of 3; (2) uses 39 MLCW stations instead of 1 well; (3) adds the inelastic regime (S_skv) that Smith et al. explicitly assumed was unnecessary at their site; (4) adds the InSAR coupling term β_k, which Smith et al.'s equation (8) lacks; and (5) is deployable at unmonitored locations using only InSAR + GWL after calibration, whereas Smith et al.'s method requires ongoing head data at every interval to re-solve the inversion at each epoch. The project also avoids Smith et al.'s uncorrelated-head constraint (see §A.5, novelty assessment): because MLCW directly measures per-depth compaction at every epoch, the IHM-F does not rely on head-timing correlations to attribute deformation to specific depths.

### A.5 CRAF-specific studies

**Hung, W.-C., et al. (2021).** Measuring and interpreting multilayer aquifer-system compactions for a sustainable groundwater-system development. *Water Resources Research*, 57, e2020WR028194. https://doi.org/10.1029/2020WR028194

> Hung et al. used the same CRAF MLCW network (fewer stations than this project's 39) to characterise elastic and inelastic compaction behaviour, estimate skeletal specific storage coefficients from stress-strain analysis, and identify safe groundwater levels for each aquifer unit. They found that (a) the majority of irreversible compaction occurs in the F3 aquifer (the same unit where TUKU's 2S-TOOL shows S_kv/S_ke = 57.7×), (b) elastic storage coefficients at CRAF stations range from 10⁻⁵ to 10⁻⁴ m⁻¹, and (c) inelastic coefficients range from 10⁻⁴ to 10⁻² m⁻¹, consistent with the TUKU 2S-TOOL values. Hung et al. provide the physical parameter bounds that IHM-F's OLS estimates should fall within, and their spatial map of S_ske and S_skv values across the CRAF is the natural target for IHM-F's Stage 2 spatial interpolation validation.

**Azeriansyah, R., Ching, K.-E., Lin, C.-W., Hsu, K.-C., Tsai, P.-C., Yeh, C.-L., & Rau, R.-J. (2024).** Unraveling the heterogeneous hydrogeological characteristics in the Choushui River alluvial fan, Taiwan, through observations from the multi-layer compaction monitoring wells. *Engineering Geology*, 341, 107570. https://doi.org/10.1016/j.enggeo.2024.107570

> Azeriansyah et al. analysed 35 CRAF MLCW stations to characterise the hydrogeological heterogeneity across the fan, proposing a seasonal-fluctuation alignment method to classify subsurface material compaction properties. Their key finding — that the Yunlin and Changhua sub-basins exhibit distinct compaction signatures — motivates IHM-F's per-station parameter estimation rather than a pooled model. The heterogeneous S_ske and S_skv values they report across the fan provide empirical confirmation that per-layer parameters must be fitted individually at each station; a single set of values would not capture the spatial variability.

### A.6 The column-sum consistency constraint

**Sneed, M. (2001).** Hydraulic and mechanical properties affecting ground-water flow and aquifer-system compaction, San Joaquin Valley, California. USGS Open-File Report 01-35. https://pubs.usgs.gov/publication/ofr0135

> Sneed's comprehensive compilation of elastic and inelastic skeletal specific storage coefficients from field and laboratory studies (cited in Smith et al. 2021 as the source for their S_ke search bounds) provides the physical reference range for S_ske (2.0 × 10⁻⁶ to 2.3 × 10⁻⁵ m⁻¹ in the literature reviewed, though Hung et al. 2021 report higher values for CRAF sediments). The IHM-F's β_k renormalization (β_k' = β_k · α / Σ β_k) — which enforces the column-sum consistency Σ β_k = α — ensures that the per-layer InSAR coupling fractions sum to the independently measured MLCW-to-InSAR displacement ratio reported in Sneed-style analyses. This is a physical closure condition that the raw IHM-F estimates will not satisfy automatically, and its enforcement makes the β_k values directly comparable to the compaction-fraction estimates from 2S-TOOL-derived storage coefficients.

### A.7 Summary: what the literature supports

The IHM-F approach rests on a foundation of physical theory, field observation, and methodological precedent:

| Claim | Supporting references |
|---|---|
| Compaction separates into elastic (S_ske) and inelastic (S_skv) regimes | Helm (1975, 1976), Riley (1969), Poland (1984) |
| The elastic/inelastic ratio is 10–100× in clay-rich sediments | Riley (1969), Galloway & Burbey (2011), TUKU 2S-TOOL results |
| InSAR can resolve the seasonal and secular components of compaction | Galloway & Hoffmann (2007), Hoffmann et al. (2001) |
| Time lag τ between head change and compaction is estimable and depth-dependent | Chen et al. (2016), Smith et al. (2021) |
| Per-interval compaction can be apportioned from InSAR + head data | Smith et al. (2021), Reeves et al. (2011) |
| CRAF-specific S_ske/S_skv values and spatial heterogeneity are documented | Hung et al. (2021), Azeriansyah et al. (2024) |
| The column-sum constraint (Σ β_k = α) is a physical closure condition | Sneed (2001), velocity-ratio prior from CRAF GNSS/InSAR comparison |

**Gap the literature does not fill — and IHM-F does:** No prior study combines (1) a two-regime IHM with explicit InSAR coupling, (2) calibrated at 37 stations × ~6 layers against MLCW ground truth, (3) using walk-forward validation through a network-shrinkage stress test, (4) with parameters designed for spatial interpolation to thousands of unmonitored grid points. The IHM-F approach is structurally novel in its integration of these four elements, even though each individual element has published precedent.

---

## Appendix B — The Roles of InSAR and GWL in the IHM-F

This appendix answers two questions for each dataset: (1) what physical role does it play in the IHM-F formula, and (2) what degrades if it is removed. The answers are essential for writing the paper's methods section and for designing ablation experiments.

### B.1 Recap: where each dataset appears in the formula

The IHM-F prediction for layer k at epoch t is:

```
Elastic regime (h_raw(t) > h_c(k)):
  Ŷ̃_k(t) = S_ske(k) · h̃_k(t − τ_k) + β_k · x̃(t)

Inelastic regime (h_raw(t) ≤ h_c(k)):
  Ŷ̃_k(t) = S_skv(k) · h̃_k(t − τ_k) + β_k · x̃(t)
```

where tilde ( ̃ ) denotes linear trend removed over the calibration window. The three input streams appear in distinct roles:

- **GWL** provides h̃_k(t − τ_k) — the depth-resolved hydraulic driver, with regime-dependent coefficient S_ske or S_skv, delayed by τ_k
- **InSAR** provides x̃(t) — the surface displacement co-driver, multiplied by per-layer coupling fraction β_k
- **MLCW** provides the training target Ỹ_k(t) — the ground-truth per-layer compaction that the model learns to predict

The following sections trace what happens when each input stream is removed.

---
### B.2 InSAR: the spatial constraint and gap-filler

**B.2.1 What InSAR contributes physically**

In the IHM-F, InSAR enters only through the β_k · x̃(t) term. This term has three distinct physical roles:

**Role 1 — Depth-integrated constraint (the column sum).** InSAR measures the total surface displacement at each epoch. This total equals the sum of compaction across all depth layers below that point, including material below the 300 m MLCW anchor. If the model's per-layer predictions sum to less than the InSAR displacement, the deficit represents compaction from depths the model does not resolve (below 300 m or between screened intervals). The column-sum constraint Σ β_k = α (enforced by post-fit renormalisation) ensures the model's InSAR-attributed predictions are consistent with the independently measured MLCW-to-InSAR displacement ratio. Without InSAR, there is no physical target for the sum of layer predictions — the model could systematically over- or under-predict total subsidence without any way to detect the error.

**Role 2 — Unmeasured stress compensation (the gap-filler).** GWL screens exist only at 2–5 discrete depth intervals per station. The intervening sediment — aquitards (T1, T2), unscreened aquifer intervals, and material below the deepest screen — experiences hydraulic stress changes that the GWL record does not capture. InSAR captures the integrated compaction of these unscreened intervals. The β_k coefficient at each layer quantifies how much of that layer's compaction is attributable to stress sources NOT represented by the co-located GWL screen. At layers well-served by a GWL screen, β_k ≈ 0; at layers distant from any screen, β_k absorbs the residual.

**Role 3 — Spatial transfer vehicle (the deployment enabler).** At the 8,577 grid points targeted for Stage 2 spatial reconstruction, InSAR is measured everywhere at every epoch (after IDW interpolation from the native 40 m grid). GWL is measured at only 306 well locations — approximately 100 station clusters. At any grid point more than a few kilometres from the nearest GWL station, the GWL signal is an interpolated approximation. The IHM-F's β_k · x̃(t) term means that even where GWL quality degrades, the InSAR signal continues to drive per-layer predictions at every grid point. This is what makes IHM-F a Class I/II method rather than a Class III method: after calibration, it produces per-layer predictions using only InSAR and the (potentially interpolated) GWL that is available everywhere.

**B.2.2 What degrades if InSAR is removed (GWL-only model)**

Removing InSAR collapses the IHM-F to a pure head-driven model:

```
Ŷ̃_k(t) = S_ske(k) · h̃_k(t − τ_k)    (elastic)
Ŷ̃_k(t) = S_skv(k) · h̃_k(t − τ_k)    (inelastic)
```

This is structurally equivalent to the Smith elastic model (Smith et al., 2021) extended with an inelastic regime, but without any surface-displacement constraint. The specific degradations are:

**Degradation 1 — No column-sum anchor.** The sum Σ Ŷ_k has no physical constraint. It can deviate arbitrarily from the InSAR-observed total displacement with no diagnostic signal. At stations where the GWL screens cover only a subset of layers, the missing-layer compaction is simply not predicted — the model output is incomplete by construction.

**Degradation 2 — Proxy-station predictions lose all spatial context.** At the 24 stations using nearest-proxy GWL, the head signal is already an approximation: the true local head differs from the proxy by an unknown amount. Without InSAR, the model has zero local surface-displacement information at these stations. The only observable is the proxy GWL, whose errors propagate directly into Ŷ̃_k without any correction term. The RMSE inflation at Xizhou (already the worst-performing station in the ablation study) would increase further, and there is no way to diagnose whether the error comes from the proxy GWL or from the model structure.

**Degradation 3 — No column-sum diagnostic α.** The ratio α = v_MLCW / v_InSAR (approximately 0.45–0.55 at TUKU) quantifies what fraction of surface displacement originates in the 0–300 m column. This ratio is used to renormalise β_k (Appendix A.6). Without InSAR, α cannot be computed, β_k cannot be renormalised, and the per-layer coupling fractions have no closed-loop consistency check.

**Degradation 4 — Inelastic regime identification is weaker.** The S_ske/S_skv contrast is identified from the MLCW training signal, which is present regardless of InSAR. However, without InSAR, the model cannot distinguish whether a given MLCW compaction epoch is typical (consistent with the total surface displacement) or anomalous (representing layer-specific behaviour not reflected in the total). This diagnostic role — flagging epochs where a layer behaves differently from the column average — is lost.

**Degradation 5 — F3 and F4 layers lose the slow-drainage correction.** The deep clay-rich layers (F3 at TUKU, S_kv/S_ke = 57.7×) have the longest drainage times and the weakest GWL signal (few deep screens). Their compaction includes a component from stress transferred from overlying aquifer units — a signal that GWL in the deep screen does not capture. The InSAR term β_k · x̃ absorbs this stress-transfer component. Without InSAR, the deep layers' predictions are driven entirely by their own (weak) GWL signal, missing the stress contribution from shallower pumping. The result is systematic underprediction at F3 and F4.

**Summary:** Without InSAR, the model retains depth-resolved, regime-aware predictions wherever GWL is available, but loses the spatial constraint (column sum), the proxy-station correction term, and the deep-layer stress-transfer component. The model reverts to a well-by-well approach that cannot produce spatially consistent predictions and cannot be transferred to unmonitored grid points.

---
### B.3 GWL: the depth-resolved hydraulic driver and regime detector

**B.3.1 What GWL contributes physically**

In the IHM-F, GWL enters in two distinct forms:
- **h̃_k(t − τ_k)** — trend-removed head, the regression driver for per-layer compaction
- **h_raw(t)** — raw (non-detrended) head, used only for the regime test: h_raw(t) > h_c → elastic, h_raw(t) ≤ h_c → inelastic

These give GWL four physical roles:

**Role 1 — Depth-resolved causal driver.** This is the most fundamental contribution. InSAR measures the integrated effect (compaction), MLCW measures it layer by layer, but neither measures the cause. GWL measures the piezometric head at specific depth intervals — the hydraulic stress that drives compaction through the effective-stress mechanism. The term S_ske · h̃ or S_skv · h̃ represents the causal relationship: head change → effective stress change → layer compaction. Without GWL, the model can correlate InSAR with MLCW but cannot establish why a given layer compacts at a given time. This causal structure is what makes the IHM-F parameters physically interpretable rather than purely statistical.

**Role 2 — Regime detection (elastic vs. inelastic).** The regime switch is the IHM-F's central innovation over the Smith elastic model. The preconsolidation head h_c(k) = 5th-percentile of raw h_k over the calibration window. At each epoch, h_raw(t) is compared to h_c(k) to determine whether the sediment is in the elastic regime (recoverable, S_ske) or the inelastic regime (irreversible, S_skv). This distinction is invisible to InSAR: a surface displacement of 10 mm could be entirely elastic (if heads are recovering from a seasonal low) or entirely inelastic (if heads are breaking a new historical low). Only GWL tells us which. The 10–60× ratio between S_skv and S_ske (confirmed by 2S-TOOL at TUKU) means that misclassifying the regime leads to order-of-magnitude prediction errors at individual epochs.

**Role 3 — τ identification (lag structure).** The time lag τ_k between head change and compaction at layer k is estimated from the cross-correlation structure of h̃_k(t) and Ỹ_k(t). Without GWL, τ cannot be estimated — the InSAR signal x̃(t) is contemporaneous with compaction, not a leading indicator. A model without τ (i.e., τ = 0 assumed) predicts instantaneous compaction when a head change occurs, but clay layers take weeks to months to drain. The Chen et al. (2016) finding that ignoring τ inflates RMSE by 15–30% at wells with thick clay is directly applicable to TUKU's F3 and F4 layers.

**Role 4 — Policy-relevant attribution.** The elastic/inelastic distinction is not just a modelling convenience; it is the most policy-relevant output the model produces. Regulators need to know: "If we reduce pumping and heads recover, how much of the observed subsidence will reverse (elastic rebound) and how much is permanent (inelastic)?". Without GWL, the model cannot answer this question — it predicts total compaction from InSAR but cannot decompose it into recoverable and permanent components.

**B.3.2 What degrades if GWL is removed (InSAR-only model)**

Removing GWL collapses the IHM-F to a single-term model:

```
Ŷ̃_k(t) = β_k · x̃(t)
```

This is structurally identical to Candidate A (static proportionality). The β_k coefficients become time-invariant compaction fractions — the same across all epochs regardless of hydraulic conditions. The specific degradations are:

**Degradation 1 — Regime blindness.** Without GWL, there is no h_c, no S_ske, no S_skv. The model cannot distinguish elastic from inelastic compaction. During the 2022 drought year (fold 1), when heads drop below preconsolidation levels and inelastic compaction dominates, the static β_k systematically underpredicts because it represents an average over both regimes from the calibration window. The fold-1 RMSE inflation would be largest at clay-rich layers (F3, F4) where the S_kv/S_ke contrast is greatest.

**Degradation 2 — Loss of temporal dynamics.** The model has no lag structure. It predicts compaction synchronously with InSAR displacement. The delayed drainage of clay layers (230-day timescale for a 10 m layer) is invisible to the model. Without GWL timing, there is no phase reference to identify whether F3 compaction at epoch t is caused by head change at epoch t − 10 or t − 30. The causal relationship collapses to a contemporaneous correlation.

**Degradation 3 — β_k becomes a black box.** In the full IHM-F, β_k has a clear physical interpretation: "the fraction of this layer's compaction attributable to stress sources not captured by the co-located GWL screen." Without GWL, β_k absorbs everything — head-driven compaction, non-head-driven compaction, elastic, inelastic, lagged, instantaneous. The parameter loses its physical meaning and becomes a purely statistical calibration factor. The 2S-TOOL cross-check (comparing S_ske/S_skv from IHM-F against independently estimated values) becomes impossible because S_ske and S_skv no longer exist in the model.

**Degradation 4 — Seasonal cycle misattribution.** The InSAR signal at TUKU shows a clear seasonal cycle (∼10 mm amplitude): the surface subsides faster during dry seasons and slower (or rebounds) during wet seasons. Without GWL, the model cannot tell whether this seasonal cycle comes from elastic compaction in shallow layers (F1, responding to seasonal recharge) or from rate changes in deep inelastic compaction (F3, responding to seasonal pumping intensity). The β_k coefficients would absorb the seasonal cycle into whichever layers happen to correlate best with the total InSAR signal, producing a seasonally biased attribution that has no physical basis.

**Degradation 5 — No 2S-TOOL cross-validation.** The independent physical check on the IHM-F parameter estimates disappears. The 2S-TOOL pipeline estimates S_ske and S_skv directly from stress-strain curves without using InSAR. If the IHM-F's S_ske/S_skv estimates agree with 2S-TOOL values, the parameters are physically validated. If they disagree, the model structure or data quality needs investigation. Without GWL, there are no S_ske/S_skv parameters to cross-validate — the model produces only β_k, which has no independent reference.

**Degradation 6 — Transfer reduces to the Track A floor.** At unmonitored grid points, the GWL-free model runs on InSAR alone: Ŷ_k(g, t) = β_k(g) · x(g, t). This is exactly the Track A static proportionality formula, which this project has already shown has a ∼1–3% RMSE improvement ceiling over the direct ratio. The Class I/II transferability claim collapses to Class III — the spatial interpolation of β_k(g) from 37 stations is the same as interpolating f̄_k(g), which was already done in the IDW baseline.

**Summary:** Without GWL, the model loses regime awareness, causal direction, temporal dynamics, parameter interpretability, independent validation (2S-TOOL), and the ability to distinguish recoverable from permanent compaction. The production model reverts to the Track A static proportionality floor.

---
### B.3 Summary: the synergy table

| Capability | With both InSAR and GWL | InSAR only (no GWL) | GWL only (no InSAR) |
|---|---|---|---|
| Per-layer predictions | Yes (IHM-F) | Static proportion (Candidate A) | Head-driven (Smith + inelastic) |
| Regime detection | Yes (h_raw vs h_c) | No | Yes (same GWL-based regime) |
| Lag estimation | Yes (τ from h̃ vs Ỹ) | No | Yes (same τ) |
| Column-sum constraint | Yes (Σ β_k = α from InSAR) | Not needed (single β_k per layer) | No (no total to constrain against) |
| Proxy-station correction | Yes (β_k · x̃ fills GWL gaps) | Not applicable (no GWL) | No (proxy GWL errors uncorrected) |
| Spatial transfer to grid | Yes (InSAR everywhere + interpolated GWL) | Yes (InSAR everywhere) | No (GWL only at 306 wells) |
| 2S-TOOL cross-validation | Yes (S_ske/S_skv from IHM vs 2S-TOOL) | No (no S_ske/S_skv in model) | Yes (same S_ske/S_skv) |
| Elastic vs inelastic attribution | Yes (regime-specific) | No (static ratio only, mixed regime) | Yes (regime-specific) |
| Deep-layer stress transfer | Captured by β_k · x̃ | Captured by β_k but indistinguishable | Missed (GWL only at screened depth) |

The two data streams are structurally complementary: **GWL provides the causal mechanism and regime information at depth; InSAR provides the spatial total and corrects for incomplete GWL coverage.** Neither alone can deliver the project's primary claim — a Class I/II method that produces per-layer compaction predictions at unmonitored locations using only remotely sensed or regionally monitored inputs.
