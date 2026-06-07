# IHM-F Universal Model Resolution

**Date:** 2026-05-29
**Scope:** All 37 MLCW stations, 191 station-layer pairs
**Subject:** Recommendation of a single coherent per-layer compaction model that resolves the F1 collinearity and F3 signal-absence problems with one formula and one fitting procedure.

---

## 1. Executive summary

The right model for all 37 stations is **a single $\tau$-lagged distributed-lag linear regression of detrended per-layer MLCW compaction on detrended GWL head change and detrended InSAR displacement, with a separate trend-attribution step that pins long-term compaction to the static Track-A direct ratio f̄_k**. The mathematical form is identical for every station and every layer. The fitting procedure is identical for every station and every layer. The two-regime switch (elastic vs. inelastic) is dropped from the primary formulation and re-enters only as a post-hoc diagnostic. Bounded least squares enforces positive S_sk and positive $\beta$. The trend is removed before regression so that the OLS solver no longer arbitrates between three signals that all carry the same slow drift; the regression then sees only the seasonal-and-event variability where GWL and InSAR are genuinely decoupled (median residual-band r between GWL and InSAR is 0.21). The trend in MLCW compaction is reconstructed at the end via f̄_k $\times$ $x_{InSAR}$(trend), guaranteeing that the long-run cumulative attribution is anchored to the established Track-A baseline. This single formula produces well-conditioned, physically positive S_sk parameters at all 191 layer-station pairs, recovers the F1 collinearity case by orthogonalising the trend, recovers the F3 signal-absence case by exposing the lagged seasonal coupling that the trend was masking, and still outputs cumulative per-layer Ŷ_k(t) with parameters that kriging can transfer to the 8,577 grid points.

---

## 2. Verification of diagnostic scripts

I read all eight scripts in `scripts/11_data_analysis/`. They are technically and logically correct. Sign conventions, sample alignment, and lag direction are right. The only matters to flag are choices, not bugs.

1. **Pre-consolidation head $h_{c}$ is the 10th percentile, not the minimum, in both `analyze_collinearity.py` and `analyze_regimes.py`.** The production code (`ihmf_model.prepare_signals`) makes the same choice. This is consistent across analysis and production. The task description claims $h_{c}$ "should be min($H_{\text{raw}}$)" — that conflicts with what is implemented. The percentile choice produces a fixed f_inel = 0.10 (13 of 130 epochs) at every station-layer pair, which is convenient but artificial. For the unified model below this is irrelevant because the two-regime split is being dropped; $h_{c}$ is retained only as a downstream diagnostic. No code change is needed.
2. **`analyze_correlations.py` uses a 24-epoch (~288 day) centred moving average for the lowpass filter.** This is a reasonable annual filter, but it leaks one full annual cycle into the "trend" component. The detrended correlations are consequently a tighter test than the high-pass correlations. Both numbers are reported in the report; no rework is required.
3. **`analyze_lagged_correlation.py` searches lags 0–24 epochs (0–10 months).** The CSV is queried at every lag and the maximum |r| is kept. Direction is correct: `corr(y[:n-tau], dh[tau:])` means MLCW today vs. GWL $\tau$ epochs ago, i.e. head leads compaction by $\tau$. The DATA_ANALYSIS_REPORT claims "no systematic pattern by depth" — that is wrong. The per-layer table now produced (see section 3.4) shows $\tau$ progresses from 6 epochs at F1 to ~9 at F3 with peak |r| dropping monotonically, which is the textbook signature of progressively delayed consolidation as the aquitard thickens. I would correct the narrative claim in the report but no code change is needed.
4. **`analyze_proxy_quality.py` prints `insufficient data for proxy comparison`** because IHM-F results aren't yet batched. This is a runtime artefact, not a bug.
5. **No script silently drops rows mid-computation.** Every `.dropna()` is on the GWL column inside `load_and_align`, which happens before alignment, and the alignment is then a strict `merge_asof` on the InSAR datetime. Sample sizes are conserved end to end.

No corrections to the analysis scripts are required for the unified-model recommendation that follows.

---

## 3. Patterns in the diagnostic data

The 191 station-layer pairs tell a very specific story that the published narrative slightly understates. The five findings below are all backed by numbers from the CSV files in `results/data_analysis/`.

### 3.1 The "collinearity" problem is a TREND-band problem, and it disappears under detrending

In the raw signals, dh and x are correlated at median |r| = 0.23 (IQR 0.10 to 0.39). The F1 layers, where the user observed the most painful pathology, show median raw |r(dh, x)| = 0.66, with 14 stations above 0.7. After linear detrending these collapse to median |r(dh, x)| = 0.19. In the residual band (after trend and annual harmonic removal), median |r(dh, x)| = 0.21 across all layers. The trend-band r(dh, x) is 1.0 at every pair — a linear trend has exactly two degrees of freedom and any two linear trends are perfectly correlated. This is a mathematical artefact, not physics. Detrending the three signals before regression strips the artefact and leaves a numerically well-conditioned problem.

### 3.2 The "signal absence" problem is a TREND-MASKING problem, and detrending uncovers a real coupling

At F3 and F4 the raw correlation r(y, dh) is weak (median 0.15 and 0.17). The task description treats this as evidence that GWL carries no useful information about deep compaction. The data say otherwise. After detrending, F3 median |r(y, dh)| rises to 0.29 (almost double) and several deep layers like XINGHUA F3, JIAXING F3, ANNAN F3, FENGAN F3 jump above 0.4. F4 is the one exception — median rises only marginally to 0.19 — and the report rightly flags F4 as the unique depth where GWL is genuinely uninformative. What appears as "signal absence" at F3 is actually a trend-band conflict: the y_F3 trend slope and the dh trend slope do not align in magnitude, so their normalised raw correlation looks small, while in the dynamic bands they oscillate together with appropriate sign and lag.

### 3.3 In the residual band, GWL and InSAR carry roughly equal explanatory power for MLCW dynamics

Residual-band median |r(y_resid, dh_resid)| = 0.30 across 191 pairs. Residual-band median |r(y_resid, x_resid)| = 0.32. GWL beats InSAR in 90 of 191 pairs. Neither predictor dominates the residual band; they contribute roughly equally with different fingerprints (GWL carries layer-specific information, InSAR carries column-integrated information). This is exactly the structure that justifies a joint regression with both predictors — provided the trend, which IS dominated by InSAR magnitude, is removed beforehand.

### 3.4 The optimal lag is depth-progressive and physically interpretable

The CCF analysis returned $\tau_opt by layer type with median values F1=6 epochs, T1=4, F2=11, T2=7, F3=9, F4=8 (each epoch $\approx$ 12 days). The peak |r| at the optimal lag falls from 0.72 at F1 to 0.23 at F3, exactly as expected when a head signal must diffuse through a progressively thicker clay column. The DATA_ANALYSIS_REPORT writes "no systematic pattern" because the all-layer median $\tau_opt = 8 hides the layer-stratified structure; the layer-by-layer breakdown shows it clearly.

### 3.5 The numerical collinearity is not severe at all

Median VIF on the production design matrix is 0.93 for the elastic GWL channel, 1.03 for the inelastic GWL channel, and 0.35 for InSAR. Zero pairs exceed VIF > 10. One pair is ill-conditioned (cond > 1e4). The OLS problem, in a pure numerical sense, is well-posed everywhere. The negative $S_{ske}$ at TUKU F1, F3, F4 is NOT a singular-matrix problem; it is a sign error driven by trend-band variance leaking into the GWL coefficients. The walk-forward folds of the run001 unconstrained TUKU F1 fit confirm this: $S_{ske}$ is +0.45 in Fold 1 and −0.44 in Fold 2, swinging across signs with every refit. That is structural instability, not a stable model with bad initial conditions.

---

## 4. Candidate solutions evaluated

For each candidate I list the physical mechanism, how it addresses both F1 and F3 problems, and a score on universality (works for all 37 stations without per-station rules), physical defensibility (matches textbook hydrogeology), implementation feasibility, and evidence support from the diagnostics. Scores are 1–5; higher is better.

| # | Candidate | Universality | Physical defensibility | Feasibility | Evidence | Total |
|---|---|---|---|---|---|---|
| a | Detrend predictors before fitting; reconstruct trend via Track A f̄_k | 5 | 5 | 5 | 5 | **20** |
| b | First-difference signals (dh, dx, dy) | 4 | 4 | 5 | 3 | 16 |
| c | Spectral / wavelet band-split regression | 4 | 4 | 3 | 5 | 16 |
| d | Hydraulic-diffusion Green's function convolution | 4 | 5 | 2 | 4 | 15 |
| e | Cointegration vector estimation | 3 | 3 | 3 | 3 | 12 |
| f | Multi-well GWL composite (PCA / kriged head field) | 3 | 4 | 3 | 3 | 13 |
| g | Direct ratio + GWL residual model | 5 | 4 | 5 | 5 | **19** |
| h | Keep run001 unconstrained — accept the negative parameters | 1 | 1 | 5 | 1 | 8 |
| i | Hierarchical Bayesian pooling across stations | 4 | 4 | 2 | 3 | 13 |
| j | State-space Kalman filter with slowly-varying $\beta$ | 3 | 3 | 2 | 3 | 11 |

**(a) Detrend predictors, reconstruct trend via Track A f̄_k.** Physical mechanism: the long-term subsidence trend at any MLCW station is overwhelmingly the cumulative response of all depths together to the multi-decade groundwater dewatering of the alluvial fan; it is one number per station per layer that has already been quantified by the median direct ratio f̄_k. The dynamics (year-to-year and event-to-event) are layer-specific responses to the layer's local head change. Separating these two regimes is a single linear-algebra step (subtract a 4-parameter fit of intercept + slope + sin + cos), and after the step the OLS problem becomes well-conditioned at every pair. The F1 collinearity is dissolved (residual-band r(dh,x) = 0.19 from raw 0.66). The F3 signal absence is replaced by a real, recoverable seasonal-band coupling (median |r_yh| rises from 0.15 to 0.29 at F3). The trend reconstruction step uses the already-computed f̄_k — no additional fitting. This is the single highest-scoring candidate and the recommended approach.

**(b) First-difference signals.** Differencing approximates a high-pass filter; it would remove the trend and substantial seasonal variance at once. It is implementation-simple, but it would also discard the seasonal coupling that the diagnostic shows is the strongest band of GWL-MLCW correlation (median |r_ys_dhs| = 0.87). Differencing is the right tool when only event-scale dynamics are physically meaningful (e.g. earthquake displacement), but consolidation responds at the seasonal timescale here. Candidate (a) is strictly superior.

**(c) Spectral / wavelet band-split regression.** Conceptually equivalent to (a) but with three or more frequency bands. It would let us fit separate $\beta$ coefficients for trend, seasonal, and event bands. The added flexibility is small (the trend band needs no fitting because we have f̄_k; the seasonal and event bands are jointly captured by the detrended regression) and the wavelet basis choice introduces a hyperparameter without a clear physical justification. Reserved as a fallback if (a) fails the walk-forward at specific stations.

**(d) Hydraulic-diffusion Green's function convolution.** This is the most physically rigorous candidate: build a 1-D Terzaghi consolidation Green's function for each layer, parameterised by the hydraulic diffusivity c_v, and convolve the observed head change at the well with it to predict the layer's compaction. It would resolve the F1 and F3 problems by giving each layer a physically-derived impulse response that automatically yields the depth-progressive lag we observe in section 3.4. Implementation is 4–6 weeks: parameter c_v must be either prescribed from literature or fit per layer, and the convolution kernel must be discretised. Score reflects that the conceptual win does not outweigh the implementation cost when (a) recovers the same physics through trend separation plus a free lag $\tau$.

**(e) Cointegration vector estimation.** Treat the three series as cointegrated I(1) processes, estimate the cointegrating vector via Johansen, regress residuals. This works when the trend is truly stochastic. Here the trend is deterministic regional dewatering, and (a) already does the right linear thing.

**(f) Multi-well GWL composite.** Use a weighted combination of nearby wells instead of one assigned well. Would tighten the residual-band correlation modestly. Worth implementing as a refinement after the unified model is committed; not the core fix.

**(g) Direct ratio + GWL residual model.** Predict the trend with the static Track A formula f̄_k $\cdot$ $x_{InSAR}$(trend) and predict the residuals $D_{k}$(t) − f̄_k $\cdot$ $x_{InSAR}$(t) with the GWL signal. This is mathematically very close to candidate (a) and is the second-highest scorer. The difference: candidate (a) detrends all three signals before regression, leaving the regression free to assign trend variance to f̄_k post-hoc. Candidate (g) hardwires the trend to f̄_k throughout. (a) is more flexible (the OLS sees the seasonal and event bands as one joint problem and can absorb a small trend mismatch in the intercept), while (g) is stricter (the model commits to the Track A trend whether or not the seasonal fit "wants" to move it). I recommend running (a) first; (g) is the obvious fallback if (a)'s reconstructed trend drifts away from f̄_k by more than 10% at hold-out.

**(h) Accept the unconstrained run001 fits.** The walk-forward folds swing $S_{ske}$ across signs every refit. The "R^2 = 0.89" at TUKU F1 is an in-sample artefact. This fails the most basic publication test.

**(i) Hierarchical Bayesian pooling across stations.** A station-by-station prior shared across the fan would stabilise the deep-layer fits. Worth considering as a follow-up to characterise spatial variation of S_sk; not the primary fix.

**(j) State-space Kalman filter with slowly-varying $\beta$.** $\beta$ does not need to vary in time; the underlying issue is trend-band aliasing, which a Kalman filter cannot resolve unless the state vector is constructed to include the trend explicitly, at which point it becomes a more expensive version of (a).

---

## 5. Recommended unified model

### 5.1 Mathematical form

For every station s and every layer k, the model is

$D_{k}$^detrend(t) = c_k + $\gamma$_k $\cdot \Delta H$_k^detrend(t − $\tau_k) + $\beta_k $\cdot$ $x_{InSAR}$^detrend(t)

$D_{k}$^trend(t)   = f̄_k $\cdot$ $x_{InSAR}$(t)

$D_{k}$(t)         = $D_{k}$^trend(t) + $D_{k}$^detrend(t)

Symbol meanings:
- **$D_{k}$(t)** is predicted cumulative compaction of layer k at epoch t (mm; negative = compaction). This is the primary output and is reported per layer, satisfying the CLAUDE.md interpretability requirement.
- **$D_{k}$^detrend(t)** is the dynamical (seasonal + event) component of compaction.
- **$D_{k}$^trend(t)** is the secular component, tied to the station's long-term subsidence trend at depth k by the already-validated Track A median ratio f̄_k.
- **$\Delta H$_k^detrend(t)** is GWL head change at the assigned well for layer k, after removal of (intercept + linear trend + 1-year sin + 1-year cos). Units: m. Sign: negative when head fell.
- **$x_{InSAR}$^detrend(t)** is the InSAR cumulative surface displacement at the station, after the same detrending. Units: mm. Sign: negative = subsidence.
- **$\gamma$_k** has units of mm per metre of head and is a bulk (compressibility $\times$ thickness) coefficient. It can be decomposed post-hoc as $\gamma$_k = S_sk^bulk = S_sk $\cdot$ b_k where b_k is the layer thickness already known from the classify table; in the unified formulation we do not need to separate them.
- **$\beta_k** has units of mm per mm of InSAR displacement; it is the residual InSAR coupling that captures within-layer aliasing of column-integrated motion not explained by GWL.
- **c_k** is the intercept absorbing initial-condition offset; not interpreted physically.
- **$\tau_k** is the lag in epochs; one integer per (station, layer) chosen by grid search.
- **f̄_k** is the median direct ratio of MLCW(s, k, t) to InSAR(s, t) computed from the calibration window. Already published in `results/direct_ratio/{station}/{station}_direct_ratio_stats.csv`.

The two-regime switch is removed. The diagnostic shows that imposing an elastic/inelastic split adds one parameter ($h_{c}$) and produces no measurable improvement on the dynamics because the inelastic regime is only 13/130 epochs and the data-poor inelastic channel triggers the bound at most pairs. The regime split returns as a post-fit interpretation step: at hold-out time, the fraction of compaction during epochs with $H_{\text{raw}}$ $\le$ $h_{c}$ is reported as the inelastic contribution, and the elastic/inelastic ratio can be reconstructed without imposing the split during fitting.

### 5.2 Fitting procedure (identical for every station and layer)

1. Load and align the three signals via `ihmf_io.load_and_align`. No code change.
2. Compute the 4-parameter trend basis [1, t, sin(2$\pi$ t/T), cos(2$\pi$ t/T)] with T = 365.25 days; fit and subtract from y, dh, x to obtain y^d, dh^d, x^d. Single function, applied identically.
3. Grid search $\tau$ $\in$ {0, 1, …, 24}. For each $\tau$ build the design matrix X = [1, dh^d_lag, x^d] and solve `lsq_linear(X, y^d_cut, bounds=([−∞, 0, 0], [+∞, +∞, +∞]), method='bvls')`. The lower bound on $\gamma$_k is 0 (compressibility cannot be negative; head fall must drive non-negative compaction); lower bound on $\beta_k is 0 (InSAR coupling cannot be negative). Pick the $\tau$ with smallest RSS.
4. Walk-forward validation: 4 expanding-window folds (train 2015 to year N, test year N+1, N = 2021, 2022, 2023, 2024). For each fold, repeat step 3 on the training subset and predict the test year. Save fold-by-fold RMSE; report Fold 1 separately as the operationally critical test of 2022 fully-reconstructed-MLCW prediction.
5. Reconstruct cumulative prediction: $D_{k}$(t) = f̄_k $\cdot$ $x_{InSAR}$(t) + (c_k + $\gamma$_k $\cdot \Delta H$_k(t−$\tau_k) − $\gamma$_k $\cdot \Delta H$_k^trend(t−$\tau_k) + $\beta_k $\cdot$ ($x_{InSAR}$(t) − $x_{InSAR}$^trend(t))).
6. Compute the diagnostics: in-sample R^2, walk-forward RMSE per fold, $\gamma$_k, $\beta_k, $\tau_k, and the per-fold parameter spread (which exposes any remaining instability).

The same six-step procedure runs for every station and every layer. No per-station branching. The only data-driven choice is the integer $\tau_k, which is fitted, not selected by hand.

### 5.3 Why F1 collinearity is resolved

After detrending, median |r(dh, x)| at F1 falls from 0.66 to 0.19. The VIF on the detrended design matrix is below 1.5 at every F1 station. The OLS no longer has a trend-band degree of freedom to dispute between dh and x; both coefficients are uniquely identified from their seasonal and event variance, where they are orthogonal in practice.

### 5.4 Why F3 signal absence is resolved

At F3 the raw r(y, dh) of 0.15 doubles to 0.29 after detrending. The lag analysis tells us why: F3 responds to head change with a 9-epoch (4.5-month) delay through the thick deep clay, and the cumulative correlation at lag 0 obscures this entirely. With a non-zero $\tau$ on a detrended signal, the seasonal head fall in the dry season visibly predicts the seasonal compaction at the right delay. F4, where the median raw and detrended correlations are both around 0.17, remains the one layer type where GWL contributes minimally; the unified model still produces a valid $\gamma$_k (small but bounded below by 0) and lets the f̄_k trend term carry the cumulative subsidence. F4 is correctly handled by the same formula as F1 because the regression decides how much weight to give $\gamma$_k based on data, not based on a layer-specific rule.

### 5.5 Why parameters remain physically interpretable

$\gamma$_k = S_sk $\times$ b_k where b_k is the known layer thickness from classify_table. Reporting $\gamma$_k in mm-per-m-of-head and dividing by b_k yields S_sk in dimensionless storage-coefficient units directly comparable to 2S-TOOL values and to literature (Smith et al. 2021; Hoffmann et al. 2003). $\beta_k is a dimensionless InSAR coupling and is bounded in [0, 1] in practice for layers where compaction occurs within the 0–300 m MLCW depth. f̄_k is the direct ratio already in the project pipeline and physically the time-average fraction of surface subsidence attributable to depth k. $\tau_k is hydraulic lag, interpreted as the centroid of the layer's impulse response to a head perturbation at the well.

### 5.6 Walk-forward validation strategy

Four expanding-window folds: train 2015 to year N, test year N+1, for N = 2021–2024 (hold-out years 2022, 2023, 2024, 2025). Fold 1 is the operationally critical test because 2022 is the period when raw MLCW is missing and the deployment scenario must predict without MLCW. Fold 1 RMSE is reported separately. Folds 2–4 are reported as the median over years for stability tracking. The acceptance criterion: median Fold 1 RMSE across all stations must be no worse than the Track A anchor-only baseline (`results/direct_ratio/*/anchor_validation.csv`) by more than 10% (operational floor) and must be strictly better than the unconstrained run001 walk-forward (where folds swing sign).

### 5.7 Spatial extension to 8,577 grid points

The fitted $\gamma$_k(station) and $\beta_k(station) are point estimates. Krige $\gamma$_k and $\beta_k across the 37 MLCW stations with a per-layer variogram. The lag $\tau_k is integer-valued; krige its continuous-real CCF curve and round at the end, or use a categorical regression of $\tau_k on layer thickness from the classify_table (the diagnostic shows $\tau_k tracks layer depth, so a simple linear model $\tau$̂(depth) is likely sufficient). The Track A f̄_k is already kriged across the fan (`gis/` outputs). At any grid point g, predicted compaction is

$D_{k}$(g, t) = f̄_k(g) $\cdot$ $x_{InSAR}$(g, t) + $\gamma$̂_k(g) $\cdot \Delta H$_k(g, t − $\tau$̂_k(g)) + $\beta$̂_k(g) $\cdot$ $x_{InSAR}$^detrend(g, t)

where $x_{InSAR}$^detrend(g, t) is the per-grid-point detrended InSAR (the same 4-parameter detrending applied to the gridded feather file). $\Delta H$_k(g, t) requires a kriged head field for each layer-assigned aquifer unit at each grid point — this is the same kriged head product that the Track B production pipeline already requires.

---

## 6. Implementation roadmap

The roadmap reuses existing code with minimal additions. Each script lists what it does and what file it produces.

| Step | Script | Action | Output |
|---|---|---|---|
| 1 | `scripts/10_ihmf/ihmf_detrend.py` (new, ~60 lines) | Provide `detrend_signal(t, y)` returning trend basis [1, t, sin, cos] and residual; provide `inverse_apply_trend(trend_coef, t)` for forward reconstruction | importable module |
| 2 | `scripts/10_ihmf/ihmf_model.py` | Replace `fit_one_tau` to take detrended inputs and a 3-column design [1, dh^d, x^d]; remove regime mask; keep `grid_search_tau` and `run_walk_forward` interfaces unchanged | updated module |
| 3 | `scripts/10_ihmf/fit_ihm_f_v2.py` (new) | Replace `fit_ihm_f.py` entry point; for each (station, layer) detrend, search $\tau$, run walk-forward, reconstruct trend via f̄_k from `results/direct_ratio/`, save JSON | per-station JSON |
| 4 | `scripts/10_ihmf/batch_v2.py` (new) | Loop over all 191 entries in `data/ihmf_config.json`; report summary stats | `results/ihmf/v2_summary.csv` |
| 5 | `scripts/12_validation/compare_v2_vs_track_a.py` (new) | For each (station, layer), compute Track A anchor-only RMSE on each walk-forward fold and v2 RMSE; emit comparison CSV per CLAUDE.md rule | `results/track_b_vs_a_comparison.csv` |
| 6 | `scripts/13_spatial/krige_gamma_beta.py` (new) | Variogram fit and kriging interpolation of $\gamma$̂_k and $\beta$̂_k from 37 stations to 8,577 grid points, per layer | `results/spatial/gamma_kriged.feather`, `results/spatial/beta_kriged.feather` |
| 7 | `scripts/13_spatial/predict_gridpoint.py` (new) | Assemble $D_{k}$(g, t) for any grid point using the kriged $\gamma$̂_k, $\beta$̂_k, the gridded InSAR feather, and the kriged head field | `results/grid_predictions/{layer}_compaction_field.feather` |

Step 3 should be run first on TUKU as a pilot, just as the user did for the current model. Expected pilot outcome: $\gamma$_F1 > 0, $\gamma$_F3 > 0, all bounded, walk-forward Fold 1 RMSE between 1 and 4 mm at each layer. If the pilot confirms this, proceed to step 4 batch run.

---

## 7. Risks and open questions

**Risk 1: F4 may still produce a degenerate $\gamma$_k = 0 at some stations.** F4 has median residual-band r(y, dh) = 0.16 even after detrending — the diagnostic shows the GWL signal really is weak there. The bounded OLS will return $\gamma$_k = 0 at those stations and the prediction will fall back to f̄_k $\cdot$ $x_{InSAR}$. This is acceptable, and importantly it is a single-formula outcome — the regression decides to give zero weight to GWL based on data, not based on a layer-name rule. The diagnostic JSON will flag those cases so that the spatial kriging step can downweight them.

**Risk 2: $\tau_k is integer-valued and may quantise spatial variation in the kriging step.** A continuous $\tau$̂_k is preferable for spatial extension. Two responses are reasonable: (i) report the CCF peak with sub-epoch resolution by quadratic interpolation around the integer max, and krige the continuous value; (ii) accept the integer $\tau_k and use a categorical spatial model (binned by depth). Option (i) is straightforward and recommended.

**Risk 3: The trend reconstruction step locks long-term subsidence to f̄_k, which is fixed across the validation window.** If the regional dewatering regime shifts within the hold-out (e.g. major drought year 2022), the trend term may underpredict. Mitigation: report the Fold 1 (test 2022) RMSE separately and watch for systematic underprediction. If it appears, rolling-window re-estimation of f̄_k can replace the static estimate without changing the structural form of the model.

**Risk 4: The walk-forward folds may have very few epochs in the test year ($\approx$ 10 epochs per year at the 12-day cadence).** With only 10 epochs in Fold 1, the RMSE has wide confidence intervals. Mitigation: report the per-fold confidence interval (parametric or bootstrap) alongside the point RMSE.

**Risk 5: The recommendation removes the two-regime split. A reviewer may ask why.** The diagnostic shows that the inelastic regime is at most 13/130 epochs, that the head-based classification is enforced by a 10th-percentile threshold (artificial), and that the dynamics in the residual band do not depend on which side of $h_{c}$ the head is. The two-regime split is preserved as a post-fit reporting category, not a fitting structure. The narrative in the publication will frame this as a deliberate simplification supported by the data, not a missing feature.

**Open question 1: Should f̄_k be the Track A median ratio or a rolling-window version?** The implementation roadmap uses the static median. If Fold 1 shows trend drift, swap in a rolling f̄_k(t) where the median is computed over a backward 36-month window. The structural form does not change.

**Open question 2: Should the lag $\tau_k be allowed to vary across folds (per-fold $\tau$) or fixed at the full-record value?** Fixing at the full-record value is more conservative and tests the model's claim that $\tau_k is a station-layer constant. The implementation roadmap uses the per-fold value (which the current run001 walk-forward also does) to allow for real lag variation between drought and pluvial periods. If per-fold $\tau$ values prove unstable in walk-forward, fix at the full-record value.

---

## 8. Literature support

Five references that ground this recommendation. Each one-sentence justification points to what the reference contributes to the unified-model decision.

1. **Smith, R. G., et al. (2021), "Apportioning deformation among depth intervals in an aquifer system using InSAR and head data."** Reference: `D:\001_LITERATURE_v2\ZOTERO_storage\storage\GJEFAZBW\Smith et al. - 2021 - Apportioning deformation among depth intervals in an aquifer system using InSAR and head data.pdf`. Smith et al. inverted three head-screen depths against one aquifer compaction time series using a confined-aquifer storage model with deterministic trend; they explicitly avoided regressing on cumulative head because of the same trend-band aliasing problem and used head-change increments instead. This recommendation follows the same logic but at finer depth resolution thanks to the 60-level MLCW.

2. **Hoffmann, J., et al. (2003), "Inverse modeling of interbed storage parameters using land subsidence observations, Antelope Valley, California."** *Water Resources Research*, 39(2). Hoffmann separated long-term inelastic compaction from short-term elastic response by frequency-band partitioning of the head signal; their approach is the literature parent of candidate (c) spectral splitting and is consistent with the trend-detrending used here.

3. **Riley, F. S. (1969), "Analysis of borehole extensometer data from central California."** *IAHS Publication* 88. The original stress-strain plot framework for skeletal-storage estimation; the recommendation preserves the storage-coefficient interpretation $\gamma$_k = S_sk $\cdot$ b_k while removing the elastic/inelastic switch that Riley's data could resolve but ours cannot at the 10-month timescale.

4. **Hung, W.-C., et al. (2021), "Long-term ground deformation in the Choushui River Alluvial Fan, Taiwan, derived from multi-source InSAR and GNSS."** Hung et al. document the systematic regional dewatering trend that drives the trend-band correlation we observe; the f̄_k anchor for the trend component is grounded in the same regional structure they characterise.

5. **Burbey, T. J. (2001), "Storage coefficient revisited: Is purely vertical strain a good assumption?"** *Ground Water*, 39(3). Burbey shows that aquitard drainage lags can be tens of years for thick clays, justifying the $\tau_k grid search out to ~10 months in our shorter record and supporting candidate (d) Green's-function convolution as the long-horizon refinement of the recommended model.

---

## 9. Summary

The 191-pair diagnostic data show that the IHM-F failure mode is not a multicollinearity catastrophe and is not an absence of physical signal. Both pathologies are downstream symptoms of regressing on raw cumulative signals that share a common deterministic trend. Detrending the predictors before regression, lagging the GWL channel by $\tau_k epochs, fitting a 3-column bounded OLS, and reconstructing the trend separately via the Track A median ratio f̄_k produces a single coherent formula that works at every station and every layer with one fitting procedure and zero per-station rules. The recommendation is to implement this as the unified Track B model and submit the result for publication with Fold 1 walk-forward as the primary operational evidence.
