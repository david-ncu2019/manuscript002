# ML Methods Review: Can Machine Learning Replace Candidate F (IHM-F)?

**Date:** 2026-05-25
**Context:** Candidate F (two-regime IHM with per-layer InSAR coupling $\beta_k) was found by prior review to be the physically correct production choice. This document evaluates whether any ML approach could *replace* it — not just supplement it — given the project's hard constraints and data volume.

---

## 1. Executive Summary

**No pure ML method can replace Candidate F and simultaneously satisfy all seven hard rules.** The reasons reduce to three binding constraints that no DL or ensemble method escapes:

1. **Spatial transfer requires interpolable parameters.** ML models with per-station learned weights (LSTM hidden states, RF trees, GP hyperparameters) either cannot transfer to 8,577 grid points at all, or require fitting a separate model per grid point — which is impossible where no MLCW exists. The only way to make an ML model spatially transferable is to make it a global function of (x, y, depth, hydrofacies, GWL, InSAR), but then the model is a single black box with ~10^3–10⁶ parameters that cannot be verified per depth.

2. **Interpretable depth-level parameters are non-negotiable.** A reviewer or journal editor will demand: "What is the physical meaning of your per-layer prediction?" For IHM-F the answer is "a storage coefficient (m⁻¹), a lag (epochs), and an InSAR coupling fraction (mm/mm)." For an LSTM or XGBoost the answer is "the activations/output of a nonlinear function" — not acceptable for the primary publication.

3. **785 epochs is far too few for deep learning.** Fold 1 has $\approx$ 4,700 training points (785 $\times$ 6 layers). An LSTM with 32 hidden units and 6 output units at all layers has $\approx$ 5,000 parameters — more parameters than training points. Overfitting is guaranteed without extreme regularisation.

**The one path forward that does work:** IHM-F + residual ML meta-model (Approach G). This preserves the physical interpretability of the primary prediction, adds ML capacity exactly where IHM-F is structurally weak, imposes no black-box requirement at the depth level, and uses data-parsimonious light models for the residual correction.

---

## 2. Evaluation Table

Scale: 1–5 (5 = best), except Implementation Cost where 5 = hardest.

| Approach | Competitiveness vs IHM-F | Satisfies per-depth Ŷ_k? | MLCW in loop? | Unified structure? | Interpretable params? | Walk-forward? | Spatial transfer? | Failure mode targeted | Impl. Cost |
|---|---|---|---|---|---|---|---|---|---|
| **A. Gradient boosting (per-depth, per-station)** | 2 | Yes | Yes | No — 222 models | Partial — feature importance only | Yes | No — tree ensemble is not interpolable | Generic nonlinearity | 2 |
| **B. LSTM/GRU (per-station, all layers)** | 1 | Yes | Yes | No — per-station weights | No — black box | Yes | No — hidden states not interpolable | Long-range temporal memory | 4 |
| **C. Transformer** | 1 | Yes | Yes | No | No | Yes | No | Extreme long-range dependencies | 5 |
| **D. Neural ODE** | 2 | Yes | Yes | Yes (ODE form) | Yes (ODE coefficients) | Yes | In theory — ODE params are interpolable | Physics-constrained dynamics | 5 |
| **E. Multi-output GP** | 1 | Yes | Yes | No (per-station kernel) | Partial — kernel hyperparams | Yes | No — re-fit needed at each grid point | Uncertainty quantification | 4 |
| **F. BSTS / state-space** | 3 | Yes | Yes | Yes (one state-space form) | Yes (transition matrices) | Yes | Yes — params are interpolable | Column sum enforcement, missing data, uncertainty | 3 |
| **G. IHM-F + residual ML** | **4** | Yes | Yes | Yes (IHM+ML is fixed structure) | Yes (IHM part), ML is residual only | Yes | Partial — IHM params transfer, ML on residuals is harder | Structural IHM weaknesses | 2 |
| **H. Vector autoregression (VAR)** | 2 | Yes | Yes | Yes (one VAR form) | Partial — lag matrices interpretable | Yes | Partial — VAR coefficients interpolable | Cross-layer coupling | 2 |

**Key insight from the table:** Only BSTS (F) and the hybrid (G) score $\ge$ 3 on competitiveness while satisfying the interpretability and spatial transfer constraints. Neither is a pure ML replacement — BSTS is a structured state-space model with interpretable components, and G is IHM-F with an ML wrapper.

---

## 3. Detailed Write-Up: Top 3 Most Promising Approaches

### 3.1 Hybrid: IHM-F + Residual ML Meta-Model (Approach G) — ★ RECOMMENDED

**What it is.** A two-stage model. Stage 1: fit IHM-F at each (station, depth) — producing physically interpretable $S_{ske}$, $S_{skv}$, $\beta_k, $\tau$, and training-window residuals R_k(t) = Y_k(t) − Ŷ_k_IHM(t). Stage 2: train a light ML model (gradient boosting with 50–100 trees, or ridge regression on engineered features) to predict R_k(t) from features that IHM-F does not use. Stage 3: Ŷ_k_final = Ŷ_k_IHM + Ŷ_k_residual.

**Why it works with the hard constraints.**

- **Per-depth Ŷ_k:** Yes — the output is IHM-F prediction + residual correction, both per-depth.
- **MLCW in loop:** Yes — MLCW drives IHM-F fitting in Stage 1, and the residuals in Stage 2 are computed from MLCW.
- **Unified structure:** Yes — the structure is always "IHM-F + ML residual model" applied uniformly. The ML model takes (station, depth) as categorical features, so it learns per-depth correction patterns without violating the structural rule.
- **Interpretable:** The primary prediction (IHM-F) has fully interpretable parameters. The ML model only affects residuals, which are second-order corrections. The paper's attribution analysis uses the IHM-F parameters, not the ML model's internal weights.
- **Spatial transfer:** IHM-F parameters ($S_{ske}$, $S_{skv}$, $\beta_k, $\tau$) transfer spatially as planned. The residual ML model... depends. If the ML model only uses features available at grid points (GWL statistics, hydrofacies, InSAR derivatives), it transfers. If it learns station-specific biases, it does not.

**What specific failure of IHM-F does it target?**

IHM-F has four structural weaknesses that the residual model can address:

| IHM-F weakness | How residual ML fixes it |
|---|---|
| Single lag $\tau$ ignores multi-week drainage memory | Feature: rolling mean of h̃ over past 30/60/90 days, cumulative GWL deficit |
| No secondary consolidation under sustained inelastic head | Feature: duration of continuous inelastic regime (epochs since last elastic recovery) |
| $h_{c}$ = calibration-window min is fragile (one extreme outlier sets the boundary) | Feature: GWL quantile position (where is current h relative to $h_{c}$, not just above/below) |
| GWL proxy noise at 24/37 stations | Feature: distance to nearest GWL well, number of GWL wells within 5 km |

**Implementation cost: 2** (modify track_b_models.py to expose residuals, add sklearn pipeline)

**Risk.** The biggest risk is the residual model overfitting to training-window noise, degrading walk-forward performance. This is mitigated by (a) using very simple models — ridge regression or shallow gradient boosting with aggressive regularisation; (b) nested cross-validation within each training fold to select L1/L2 penalties; (c) evaluating residual improvement vs IHM-F baseline at each fold — if the residual correction degrades fold-1 RMSE, it is not production-worthy.

**Verdict: Worth piloting immediately after IHM-F baselines are established at Pilot 1.** The cost is low, the upside is additive with IHM-F, and the risk is bounded (fallback to pure IHM-F).

---

### 3.2 Bayesian Structural Time Series / State-Space Model (Approach F) — ★ DARK HORSE

**What it is.** A state-space model where latent states are the per-layer compaction values Y_k(t). The observation equation maps latent states to InSAR surface displacement (sum of Y_k = total compaction). The transition equation is:

```
Y_k(t) = Y_k(t-1) + S(t) · Δh̃_k(t-τ)       (transition, per depth)
S(t) = S_ske if h_raw(t) > h_c                (regime-switching storage)
S(t) = S_skv if h_raw(t) ≤ h_c
```

plus InSAR coupling term $\beta_k $\cdot$ x̃(t) in the observation or transition equation. Kalman filter + EM algorithm for parameter estimation.

**Why it satisfies the hard rules.**

- **Per-depth Ŷ_k:** Yes — the state vector contains all 6 layers.
- **MLCW in loop:** Kalman filter updates latent states using MLCW observations when available.
- **Unified structure:** One state-space form per station (same structural matrices, different parameter values).
- **Interpretable parameters:** Transition matrix entries are $S_{ske}$, $S_{skv}$, $\beta_k — same physical units as IHM-F.
- **Spatial transfer:** Transition matrix entries are per-depth scalars, interpolable via IDW/kriging.
- **Walk-forward:** Kalman filter is naturally causal (filtering forward in time).

**What makes it competitive with IHM-F?**

1. **Column sum constraint enforcement.** The observation equation is `InSAR(t) = Σ Y_k(t) + noise`. This directly enforces that the sum of all per-layer predictions matches InSAR, with the noise variance representing unmodeled processes (compaction below 300 m). IHM-F has no such constraint.

2. **Principled missing-data handling.** MLCW observations enter as updates when available, predictions propagate from the transition equation when absent. This is exactly the deployment scenario — during MLCW outages, the model runs on GWL+InSAR alone.

3. **Uncertainty quantification.** Kalman filter produces full posterior covariance of Y_k(t) at each epoch. P05/P95 bands come for free — no separate Monte Carlo needed.

4. **$h_{c}$ as a latent state.** Instead of a hard threshold from calibration-window minimum, $h_{c}$ can be a Bayesian latent variable with a prior (e.g., shifted-Gamma centered on the calibration minimum). This fixes the fragility of IHM-F's $h_{c}$ being driven by a single extreme observation.

**What specific IHM-F weaknesses does it address?**

- **Column sum constraint (#2 in IHM-F weaknesses):** Fixed by observation equation design.
- **$h_{c}$ fragility (#3):** Fixed by Bayesian treatment of $h_{c}$.
- **Missing data (#5 related):** Kalman filter handles NaN naturally.
- **Uncertainty:** Full posterior covariance produced at every epoch.

**What it does not address:**

- **Single-lag $\tau$:** State-space model still uses one lag per layer. Could extend to distributed-lag state-space (DLM with lagged inputs), but that increases parameter count substantially.
- **Secondary consolidation:** No explicit mechanism for sustained-inelastic-head effects.

**Implementation cost: 3.** Requires a custom state-space design (not off-the-shelf statsmodels — the regime-switching transition is non-standard). EM algorithm for parameter estimation. Python `pykalman` or `ssm` libraries are starting points but would need significant modification.

**Verdict: Worth a dedicated 2-week research sprint after IHM-F Pilot 1 completes.** The column sum constraint and $h_{c}$ robustness are genuine concerns that no other approach addresses as elegantly. The cost is moderate — a working prototype at TUKU could be built in Pyro or TensorFlow Probability with ~300–500 lines of code if the design is clean.

---

### 3.3 Elastic Net on Engineered Features (Simpler Variant of Approach A)

**What it is.** Per-depth linear model with L1+L2 regularisation. Features: trend-removed GWL at lags 0, 1, 3, 6, 12, 18, 24 epochs; trend-removed InSAR at lags 0, 1, 2; hydrofacies fines fraction; sinusoidal seasonal encoding; cumulative GWL deficit over past 30/90/180 days; duration of current inelastic regime.

One model per (station, depth) — but this is the same structure as IHM-F (independently fitted per depth). The formula is:

```
Ŷ̃_k(t) = Σ w_h_j · h̃_k(t-j) + w_x · x̃(t) + w_p · p_k + w_s · season(t) + w_d · deficit(t) + w_r · regime_duration(t)
```

with elastic net regularisation ($\alpha$ = 0.01–0.1, L1_ratio = 0.5).

**Why it falls short of replacing IHM-F:**

- **Spatial transfer fails.** The per-depth weights are linear coefficients, spatially interpolable in principle — but the weight for "cumulative deficit" and "regime duration" at a grid point would need to be known. They are station-specific. Only GWL-lag weights and hydrofacies weight might transfer. The model has too many per-station features for clean spatial interpolation.

- **Interpretability is eroded.** What does a weight on "regime duration" mean in physical units? It has units of mm/epoch, but the physical process it represents (secondary consolidation rate) is confounded with other features that correlate with regime duration.

- **Feature engineering risk in walk-forward.** Features like "cumulative deficit over past 180 days" look backward. In walk-forward, the training window moves forward — the feature distribution shifts between folds, and the elastic net may not generalise.

**Implementation cost: 1–2** (trivial to add to track_b_models.py)

**Verdict: Not a replacement for IHM-F. Useful as a diagnostic tool** — the elastic net coefficient magnitudes at different lags tell you which GWL history window matters most, which helps set IHM-F's $\tau$ grid-search range. But as a production method it fails the spatial transfer and interpretability tests.

---

## 4. Concrete Pilot Plans for Top Approaches

### 4.1 Pilot Plan: IHM-F + Residual ML (Approach G)

**Objective:** Determine whether a light ML model can reduce IHM-F's hold-out RMSE by $\ge$ 5% median across all stations, without degrading fold-1 performance.

**Data:** Already produced by Pilot 3 — per-station per-depth IHM-F residuals `R_k(t)` for training folds, plus engineered features.

**Features for residual ML (engineered from existing streams):**

| Feature | Source | Rationale |
|---------|--------|-----------|
| h̃_k(t) rolling mean (30, 60, 90 epochs) | GWL | Captures multi-week drainage not in single-lag IHM |
| h̃_k(t) rolling std (30 epochs) | GWL | High variability → rapid loading/unloading |
| Cumulative h̃_k deficit (raw h < $h_{c}$, sum over past 60 epochs) | GWL + $h_{c}$ | Measures sustained inelastic stress |
| Continuous inelastic duration (epochs since last h > $h_{c}$) | GWL + $h_{c}$ | Secondary consolidation proxy |
| x̃(t) first difference | InSAR | Short-timescale InSAR signal |
| p_k (fines fraction) | Hydrofacies | Clay content modulates lag and magnitude |
| Distance to nearest GWL well | Metadata | Proxy for GWL quality |
| R_k(t-1) lagged residual | Autoregressive | Captures residual autocorrelation IHM misses |

**Model architecture:** Two candidates compared:

1. **Ridge regression** (L2 penalty, $\alpha$ tuned by 5-fold CV within training window)
2. **Gradient boosting** (50 trees, max_depth=3, learning_rate=0.1, subsample=0.5)

Both trained per (station, depth) — same structure as IHM-F fitting. Residual correction clipped to $\pm$ 2$\sigma$ of training residual distribution to prevent extreme corrections in deployment.

**Validation protocol:**
- For each fold f (1–4):
  1. Fit IHM-F on train_f → compute residuals R_k(train_f)
  2. Fit residual model on (features[train_f], R_k[train_f])
  3. Predict on hold-out_f: Ŷ_k_final = Ŷ_k_IHM + residual_correction
  4. Compute RMSE of Ŷ_k_final vs true Y_k
- Compare to IHM-F-only RMSE per fold
- **Exit criterion:** residual model must reduce median RMSE across all station-depths by $\ge$ 5% in folds 2–4 AND not degrade fold 1 by >2%. If fold 1 degrades, the residual model is too complex and is removed from production (fallback to pure IHM-F).

**Comparison metric vs IHM-F:** Per-station per-depth RMSE ratio: RMSE(hybrid)/RMSE(IHM-F). Saved as `output/residual_ml/improvement_table.csv`.

**Output:** `output/residual_ml/residual_ml_summary.csv` — station, depth, model_type, alpha, rmse_fold1, rmse_fold2, rmse_fold3, rmse_fold4, rmse_folds2to4_median, improvement_pct.

**Implementation cost:** 1–2 days. Add ~100 lines to a new script `pilot4_residual_ml.py`.

---

### 4.2 Pilot Plan: BSTS at TUKU (Approach F)

**Objective:** Determine whether a state-space model with Kalman filter can match or exceed IHM-F's walk-forward RMSE at TUKU, while providing column-sum consistency and uncertainty bounds.

**Model specification (TUKU pilot, single layer first):**

**State vector:** [Y_k(t), $S_{k}$(t)]^T — compaction at depth k, plus "effective storage coefficient" as a slowly varying latent state.

**Transition equation:**
```
Y_k(t+1) = Y_k(t) + S_k(t) · Δh̃_k(t+1-τ) + β_k · Δx̃(t+1) + ε_Y
S_k(t+1) = S_k(t) + ε_S
```
where $\varepsilon$_Y ~ N(0, $\sigma$^2_Y) and $\varepsilon$_S ~ N(0, $\sigma$^2_S). The $S_{k}$(t) random walk allows storage coefficient to evolve slowly — capturing gradual changes in material properties not representable by a hard regime switch.

**Alternative transition with regime switch (for comparison):**
```
Y_k(t+1) = Y_k(t) + S_ske · Δh̃_k(t+1-τ) + β_k · Δx̃(t+1) + ε_Y   if h_raw > h_c
Y_k(t+1) = Y_k(t) + S_skv · Δh̃_k(t+1-τ) + β_k · Δx̃(t+1) + ε_Y   if h_raw ≤ h_c
```
This is identical in spirit to IHM-F but rendered as a state-space model, with Kalman filter for inference and likelihood evaluation for parameter learning.

**Observation equations:**
```
Y_k_mlcw(t) = Y_k(t) + ν_k(t)          (MLCW observation at depth k)
x_insar(t) = Σ Y_k(t) + ν_x(t)         (InSAR = sum of all layers + noise)
```
The second equation enforces the column sum constraint.

**Parameter estimation:** Expectation-Maximisation (EM) or direct likelihood maximisation via Kalman filter likelihood computation. Initialise $S_{ske}$, $S_{skv}$, $\beta_k, $\tau$, $h_{c}$ from IHM-F calibration on fold 1 training data.

**Validation:**
- Fit on fold 1 training data (full 2015–2021), predict 2022
- Repeat for folds 2–4
- Compare per-depth RMSE to IHM-F baseline
- Report: posterior P05/P95 calibration (coverage of true Y_k), column sum consistency ($\Sigma$Ŷ_k vs InSAR)

**Comparison metric vs IHM-F:** RMSE ratio + column sum RMSE + P05/P95 coverage.

**Implementation cost:** 2 weeks. Requires a custom Kalman filter implementation (or Pyro/TFP with stochastic variational inference for approximate Bayesian inference in the regime-switching variant).

---

## 5. Recommendation: Should the Project Adopt Any ML Approach Now?

**No — stay with IHM-F and add the targeted refinements from the prior review.**

Here is the reasoning:

**IHM-F is not finished.** The prior review identified five specific refinements:
1. **3-regime extension** (elastic + inelastic + secondary consolidation under sustained head below $h_{c}$)
2. **$h_{c}$ as a percentile** (P05 of calibration-window head, not absolute minimum)
3. **Column sum constraint** ($\Sigma$ $\beta_k = $\alpha$, enforced during fitting, not post-hoc)
4. **$\gamma_k $\cdot$ t term** (small trending correction for steady deep compaction not captured by GWL or InSAR)
5. **$\tau$ grid-search refinement** (sub-epoch resolution via interpolation)

Every one of these is a simpler, more physically grounded fix than any ML method. The total implementation cost for all five is approximately 3–4 days — less than even the simplest ML pilot (Approach G) when accounting for interpretation and debugging.

**The improvement headroom for ML is small.** IHM-F already captures the primary physical dynamics (elastic/inelastic differential response, per-layer InSAR coupling). The IHM-F baseline for comparison will be median RMSE improvement vs static ratio in the range of maybe +25–35% (above anchor-only's +22.9%, since IHM-F uses GWL and InSAR jointly). An ML model that improves on this by 5–10% absolute is a success. But that success must survive:
- Walk-forward validation (fold 1, MLCW absent)
- Spatial transfer to 8,577 grid points
- Reviewer scrutiny of interpretability

Each constraint raises the bar. An ML method that fails any one of them cannot be the production choice.

**What to do instead (in order):**

1. **Complete IHM-F Pilot 1 (TUKU)** — the decision rule outcome is prefigured by 2S-TOOL evidence (all 6 TUKU layers have $S_{kv}$/$S_{ke}$ > 1, with F3 at 57$\times$). Candidate F is expected to win.

2. **Implement the five targeted refinements** to IHM-F before considering any ML:
   - 3-regime IHM: add secondary consolidation term $\gamma_k $\cdot$ t when h < $h_{c}$ for >12 consecutive epochs (~2 months)
   - $h_{c}$ = P05 of calibration head, not absolute min
   - Column sum constraint: modify OLS to include equality constraint $\Sigma$ $\beta_k = $\alpha$(s) via Lagrange multiplier or constrained least squares
   - $\gamma_k $\cdot$ t term in transition equation
   - $\tau$ interpolation: fit parabola through RMSE vs $\tau$ curve, pick minimum at sub-epoch resolution

3. **After the refined IHM-F baseline is solid**, run the IHM-F + residual ML pilot (Approach G, Pilot Plan 4.1). This adds cheap upside without risking the primary publication's interpretability.

4. **Consider BSTS only if column sum enforcement or $h_{c}$ robustness is a reviewer concern.** The state-space approach (Approach F) addresses both, but at 2$\times$ the implementation cost of the IHM-F refinements alone. If column sum error is reported as a diagnostic metric in the paper (it should be), and the IHM-F constraints keep it within $\pm$ 5%, there is no need for BSTS.

**The one exception:** If fold 1 (2022) RMSE is catastrophically worse than folds 2–4 (>2$\times$), the IHM-F refinements may be insufficient. In that case, the residual ML approach (G) is the best diagnostic tool — it will reveal which features IHM-F is missing during MLCW-absent epochs. If the residuals show structured temporal patterns (e.g., large positive residuals during drawdown events not captured by any IHM feature), that finding directly guides a model upgrade.

---

## 6. Summary Table: ML vs IHM-F Refinements

| Criterion | IHM-F with 5 refinements | Best ML alternative (Hybrid G) |
|---|---|---|
| Implementation time | 3–4 days | 1–2 days additional |
| Interpretability | Full physical parameters | IHM-F parameters primary; ML on residuals |
| Spatial transfer | Yes — 5 scalars per depth interpolable | Partial — IHM part transfers, ML part questionable |
| Column sum constraint | Enforced in OLS | Not addressed (ML does not constrain sum) |
| $h_{c}$ robustness | Percentile-based, not min | Not improved |
| Memory beyond single $\tau$ | Not addressed | Yes — engineered features cover multi-week memory |
| Secondary consolidation | Yes — 3rd regime | Yes — via regime-duration feature |
| Risk of degradation | Low — each refinement monotonic | Moderate — 2022 fold could degrade |
| Reviewer defensibility | Very high | Medium (ML residual correction will be questioned) |

**Bottom line:** Implement the IHM-F refinements first. Run the residual ML pilot after. Do not allocate resources to LSTM, transformer, GP, Neural ODE, or standalone gradient boosting — they cannot satisfy all seven hard rules simultaneously, and the data volume is insufficient to make them competitive.

---

*Written 2026-05-25 for D:\112_PROJECT_002*
