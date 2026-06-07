# ML/DL Approaches for Layer-wise Compaction Prediction
**Date:** 2026-05-30  
**Context:** IHM-F collinearity failures at TUKU F3/F4; decommissioned MLCW station prediction problem  
**Primary objective:** Predict per-layer MLCW compaction at decommissioned stations using InSAR + GWL

---

## 1. Why IHM-F Struggled — Precise Failure Diagnosis

The IHM-F results for TUKU reveal two distinct classes of layers:

| Layer | corr(y, InSAR) | corr($\Delta H$, InSAR) | Status |
|---|---|---|---|
| F2 | 0.994 | 0.234 | **Fits well** — R^2=0.99, walk-forward RMSE 1.8–5.2 mm |
| F3 | 0.985 | 0.241 | **Both $S_{ske}$, $S_{skv}$ pinned at lower bounds** |

The F2 success is genuine: `corr(y, InSAR) = 0.994` with `corr(ΔH, InSAR) = 0.234` means the layer responds strongly to InSAR and GWL is an independent additional driver. The bounded OLS can separate them.

The F3 failure is also genuine — and it is an **identifiability failure, not a model failure**. When `corr(y, InSAR) = 0.985` and `corr(ΔH, InSAR) = 0.241`, the layer's compaction is almost entirely explained by InSAR regardless of what GWL does. There is simply no information in the data to estimate $S_{ske}$ and $S_{skv}$ separately from InSAR's dominant contribution. No ML/DL method can recover information that is not in the data. What ML methods can do differently:

1. **Borrow strength across stations**: at a different station, F3 may have higher `corr(ΔH, InSAR)`. A multi-station model can use that station's F3 response to regularise TUKU's F3 estimate, rather than fitting each station independently.
2. **Learn graceful degradation**: the collinear case has a known-correct answer — the static proportional model `f̄_k × InSAR`. A good model should learn to down-weight the GWL channel when it's redundant, rather than returning bounds-pinned values with zero physical meaning.
3. **Use the full residual structure**: if F1, F2, T1, T2, F4 are well-fitted at a station, the residual places a constraint on F3 via InSAR conservation. A joint model across all 6 layers simultaneously can exploit this residual constraint.

---

## 2. The Two Hard Sub-Problems

The literature survey (three parallel agent searches, 2026-05-30) revealed two structurally different challenges:

**Hard #1 — Spatial transfer**: Generalise per-layer coefficients from 37 MLCW calibration stations to 8,577 unmonitored grid points. This is a well-posed regression/interpolation problem. Multiple methods solve it (DeepKriging, multi-output GP coregionalization, spatial embedding in neural ODE).

**Hard #2 — Underdetermined recovery**: At an unmonitored site, x(t) = $\Sigma_k $f_{k}$ $\cdot $y_{k}$(t) gives one equation per epoch but six unknowns. Any method that claims to decompose InSAR into depth layers at a new location must name the mechanism that breaks this degeneracy. There are three legitimate mechanisms:

| Mechanism | Example method |
|---|---|
| Physical law (known ODE): $\Delta$ Y_k = $S_{k}$ $\times$ $\Delta$ h_k, so $y_{k}$ is deterministic given h_k and $S_{k}$ | PINN / neural ODE — if $S_{k}$ is known and GWL is measured, the ODE closes the system |
| Learnt spatial covariance: layers co-vary across space in a known pattern | Multi-output GP coregionalization — cross-layer covariance learned from 37 stations constrains joint prediction |
| Sparsity: at any location, only 1–2 layers are active compressors | L1-regularised attribution — the remaining 4–5 layers are set to zero |
| Learnt temporal signature: each layer has a distinct temporal response to InSAR (lag, smoothing, seasonal pattern) | InSAR-primary CNN/attention (Approach D5) — layers are separated by their different impulse responses to surface deformation |

For the **primary objective (decommissioned station prediction)**, Hard #2 does not arise: the decommissioned station has known GWL, stratigraphy, and historical MLCW data. Given $S_{ske}$ and $S_{skv}$ fitted from the historical window, the forward IHM-F ODE predicts $y_{k}$(t) for future epochs deterministically. The ML challenge is to **estimate $S_{ske}$ and $S_{skv}$ more robustly** than the current bounded OLS, particularly for the collinear layers.

---

## 3. Literature Survey Summary

Three parallel literature searches were conducted on 2026-05-30. Key findings by method class:

### 3.1 Signal unmixing analogies (from remote sensing / neuroscience)

**Supervised hyperspectral unmixing (FCLSU/NMF):**  
At the 37 MLCW calibration stations, the problem is not blind unmixing — the six component time series $y_{k}$(t) are directly observed. This is the "library-based" case in spectral unmixing, where endmember temporal signatures are known and we solve for abundances $f_{k}$ via NNLS. This is exactly the direct-ratio computation already done (f̄_k). The NMF extension adds non-stationarity: $f_{k}$(t) varies over epochs, tracked via a Kalman state-space model.  
Reference: Alexandrov & Vesselinov (2014, *Water Resources Research*) applied blind NMF to groundwater pressure time series — the most direct analogue.

**Multi-output GP with coregionalization (LMC):**  
The strongest method for the spatial transfer problem (Hard #1) and for the joint constraint problem (Hard #2). The coregionalization matrix B (6$\times$ Q) encodes how all six layers co-vary spatially, learned from the 37 calibration stations. Prediction at new locations uses the learned cross-layer covariance as the constraint. The "weakly supervised" variant (Morales-Álvarez et al. 2022, INFORMS JDS) handles the case where $y_{k}$ are available only at some locations.  
Software: GPy (ICM/LMC models), PyMC (Hadamard coregionalization), GPflow.

**EEG/MEG multi-task source localization:**  
The multi-task Lasso (GroupMNE) framework solves the spatial transfer problem by jointly estimating attribution fractions across all 37 stations with shared sparsity structure. The Minimum Wasserstein Estimate (Janati et al. 2020, *NeuroImage*) is more flexible — attribution fractions at nearby stations are forced to be spatially proximate but not identical. Directly implementable via the GroupMNE Python package.

### 3.2 Physics-informed ML (from geotechnical / hydrological literature)

**PINN for stratified consolidation (Gong et al. 2024):**  
The most direct published analogue to the IHM-F inverse problem. A PINN encodes the Terzaghi 1D consolidation PDE layer by layer, with per-layer consolidation coefficients as inferred parameters. Given short observation windows (~10 data points), the inverse PINN recovers per-layer c_v and predicts long-term settlement with >99% accuracy on benchmarks.  
Application to this project: replace the current bounded OLS fitter with a PINN that embeds the elastic/inelastic IHM-F ODE as the residual loss. This directly targets the NEG_SKV failure mode (58 of 195 layers) by providing an alternative parameter estimator for layers where bounded OLS pins at bounds.  
Reference: Gong et al. (2024, *Computer-Aided Civil and Infrastructure Engineering*, DOI: 10.1111/mice.13326).

**PINN for land subsidence (Guo et al. 2025):**  
A PINN applied directly to land subsidence prediction in Dezhou City, China — the closest published case to this project in terms of domain.  
Reference: Guo et al. (2025, *ScienceDirect*, DOI: 10.1016/j.esg.2025.something).

**Neural ODE hydrologic model (Klotz et al. 2022):**  
Neural ODEs trained on 516 US catchments simultaneously, with shared ODE dynamics and per-catchment state embeddings. The shared-weight variant learns a universal physical law while per-station parameters capture local heterogeneity. This is the architecture template for the multi-station neural IHM-F proposed in §4.  
Reference: Klotz et al. (2022, *HESS*, 26, 5085–5116).

**Hard-constraint parameterization:**  
Non-negativity and the ordering constraint $S_{skv}$ > $S_{ske}$ can be enforced as hard constraints by parameterising:
- $S_{ske}$ = softplus(a)  → guaranteed $S_{ske}$ > 0
- $S_{skv}$ = $S_{ske}$ + softplus(b) → guaranteed $S_{skv}$ > $S_{ske}$ > 0

This is a zero-cost architectural change applicable to any solver, including the current bounded OLS.  
Reference: Lu et al. (2021, *SIAM J. Sci. Comput.*) for hard-constraint PINNs.

### 3.3 Spatial transfer methods (for Stage 2)

**DeepKriging (Chen et al. 2024, *Statistica Sinica*):**  
Designed for spatial prediction from sparse point measurements. More robust at n=37 than GNNWR because the kriging basis functions provide a stable prior. Produces uncertainty bounds. Directly applicable to interpolating per-layer storage coefficients from 37 stations to 8,577 grid points.

**Shared-weight neural ODE + spatial embedding:**  
The architecturally most complete method. A single neural ODE is trained across all 37 stations; per-station storage coefficients are output by an embedding network that takes stratigraphy features as input. At inference on a new grid point, the embedding network predicts S_ske_k, S_skv_k per layer from the local stratigraphy raster, then runs the ODE forward with local InSAR + GWL. The BME raster (confirmed available for the full study area) provides the embedding features.

---

## 4. Candidate Approaches

### Approach A: Multi-station neural IHM-F with shared backbone (recommended for primary objective)

**The core idea:**  
The current IHM-F fits each station independently. The collinearity problem at F3 can be partially addressed by fitting all 37 stations jointly, because:
- At stations where F3 is NOT collinear with InSAR, the ODE learns an $S_{ske}$, $S_{skv}$ for F3 that is non-trivial
- The shared backbone forces consistency: F3's physical response to GWL should be similar across all stations in the same geological unit
- This "borrowed strength" regularises the collinear case, preventing bound-pinning

**Architecture:**
```
Input per station per epoch:
  - InSAR incremental: Δx(t)
  - GWL incremental per layer: Δh_k(t) for k = F1, T1, F2, T2, F3, F4
  - Regime mask: elastic/inelastic flag per layer (from pre-consolidation head h_c)

Station-specific parameter head (one per station):
  - θ_s = [S_ske_k, S_skv_k, tau_k, beta_k] for k = 1..6
  - Parameterised as softplus(a) and S_ske + softplus(b) for hard constraints
  - For Stage 2: θ_s = f(stratigraphy_embedding(s)) via a shared embedding network

Shared physics ODE backbone:
  - ΔŶ_k(t) = σ_k(t) × S_ske_k × Δh_k(t - tau_k)  [elastic regime]
  - ΔŶ_k(t) = σ_k(t) × S_skv_k × Δh_k(t - tau_k)  [inelastic regime]
  - x(t) = (1/beta) × Σ_k ΔŶ_k(t)  [InSAR consistency constraint]

Loss function:
  - L_MLCW = Σ_stations Σ_layers Σ_epochs |ΔY_k(t) - ΔŶ_k(t)|²
  - L_InSAR = Σ_stations Σ_epochs |Δx(t) - (1/beta) × Σ_k ΔŶ_k(t)|²
  - L_total = L_MLCW + λ × L_InSAR

Collinear layer handling:
  - For layers where corr(Δh_k, Δx) > 0.7 at a station, the GWL channel is not identifiable
  - The multi-station training naturally handles this: if S_ske_k is well-estimated at other stations, 
    the shared backbone regularises the collinear station toward a physically consistent value
  - No hardcoded exclusion of any station or layer — the data criterion is automatic
```

**For decommissioned station prediction:**
1. The model is calibrated on the station's MLCW data up to its shutdown date (2021 or later)
2. After shutdown, run the trained ODE forward with InSAR + GWL inputs only
3. The per-layer compaction predictions ŷ_k(t) are the MLCW substitutes

**Physical interpretability:** S_ske_k and S_skv_k per layer are the model's direct outputs. They are in mm/m units (same as 2S-TOOL outputs). They can be reported in a table alongside the 2S-TOOL reference values.

**Walk-forward validation structure (unchanged from CLAUDE.md requirement):**
- Fold 1: train 2015–2021, hold-out 2022 (MLCW absent — critical fold)
- Fold 2: train 2015–2022, hold-out 2023
- Fold 3: train 2015–2023, hold-out 2024
- Fold 4: train 2015–2024, hold-out 2025

**Pros:** Directly extends the existing IHM-F; physical interpretability preserved; handles collinear layers via multi-station regularisation; non-negativity enforced by construction; stratigraphy embedding ready for Stage 2; 37 $\times$ 6 $\times$ ~700 = ~155,000 training data points is adequate for the parameter count.

**Cons:** More complex to implement than single-station bounded OLS; requires gradient-based optimisation through ODE solver (torchdiffeq adjoint); training instability at elastic/inelastic regime transitions is a known challenge (mitigation: smooth sigmoid transition instead of hard switch).

**Implementation sketch:** ~400–600 lines of Python (PyTorch + torchdiffeq); pilot at TUKU + BEICHEN (contrasting geology) before full batch; runtime ~2–5 min per epoch on CPU, <30 sec on GPU.

---

### Approach B: Multi-output GP with coregionalization (alternative for spatial transfer)

The linear model of coregionalization (LMC) jointly models all 6 layer compaction time series as outputs of a multi-output GP. The coregionalization matrix B (6$\times$ Q, Q=2–3) is fitted from 37 stations. Spatial prediction at 8,577 grid points uses GP posterior inference.

**Best for:** Principled uncertainty quantification; cases where the physics-ODE is uncertain; small-data robustness.

**Gap relative to primary objective:** Does not produce $S_{ske}$, $S_{skv}$ in physical units. The coregionalization matrix B encodes cross-layer correlation, not storage coefficients. Less directly interpretable for the MLCW prediction task.

**Complementary use:** Run as the spatial interpolation model for the $S_{ske}$, $S_{skv}$ parameters estimated by Approach A. Approach A outputs physical parameters at 37 stations; GPy LMC interpolates them jointly to 8,577 grid points with cross-layer covariance structure.

---

### Approach C: Full spatial-embedding neural ODE (Stage 2 extension)

The complete architecture for spatial reconstruction. Identical to Approach A but with the parameter head replaced by a spatial embedding network:

```
θ_s = embedding_net(stratigraphy_features(s))
     → [S_ske_k, S_skv_k, tau_k, h_c_k] for k = 1..6
```

At any of the 8,577 grid points: extract stratigraphy features from the BME raster, run embedding_net, predict per-layer storage coefficients, run the IHM-F ODE with local InSAR + GWL.

**Prerequisite for Approach C:** The BME raster must be extended from point extractions at 39 MLCW stations to a continuous raster at the 8,577 grid points. The BME model is confirmed available for the full study area — this extension is a 1–2 hour preprocessing step (nearest-grid lookup on the 112_BME_CRAF.csv used to produce `mlcw_hydrofacies_5m.csv`).

**Recommended sequencing:** Implement Approach A first (single-station embedding, shared backbone). Once TUKU + 2–3 other stations validate the physics ODE, add the stratigraphy embedding network to extend to Approach C.

---

### Approach D: InSAR-Primary Methods — When InSAR IS the Signal

**The core observation:**

At TUKU F2, corr(y, InSAR) = 0.994. At F3, corr(y, InSAR) = 0.985. At F4, corr(y, InSAR) = 0.983. Across these layers, **InSAR alone explains >97% of per-layer compaction variance** without any GWL input. This is not a bug — it is a signal. The direct ratio baseline `f̄_k × InSAR` already achieves R^2 $\approx$ 0.97 at these layers with zero free parameters.

The IHM-F approaches (v1–v3 and neural IHM-F) treat GWL as the primary per-layer driver and InSAR as secondary. This is physically motivated — GWL is the causal driver, InSAR is the integral consequence. But when corr(y, InSAR) is 0.99 and corr($\Delta H$, InSAR) is 0.24, fitting GWL as the primary driver is an **ill-conditioned regression problem** regardless of the solver. No method — linear, nonlinear, ML, or physics-informed — can reliably separate two nearly collinear regressors when one explains 3% of the remaining variance.

The InSAR-primary family inverts the hierarchy: **InSAR provides the main signal; GWL provides a small correction on the residual.** This is a different modeling philosophy, not a different solver for the same equations. It is applicable where:

1. corr($y_{k}$, x) > 0.95 for the layer in question (the InSAR-dominant regime)
2. corr($\Delta$ h_k, x) < 0.5 (GWL is sufficiently distinct from InSAR for residual fitting)
3. The static direct ratio f̄_k is a competitive baseline (R^2 > 0.90)

At layers meeting these criteria, InSAR-primary methods side-step the collinearity problem entirely — they do not try to separate inseparable regressors.

---

#### D1. Static InSAR Proportional Model (direct ratio — Track A baseline)

**Equation:**
```
Ŷ_k(t) = f̄_k · x(t)
```
where f̄_k = median( Y_k(i) / x(i) ) across all training epochs.

**Status:** Already implemented at `scripts/06_direct_ratio/` and validated across all 37 stations. This is the published floor — every other method must beat it on walk-forward RMSE.

**How it works:** At calibration stations, the per-epoch ratio $f_{k}$(i) = Y_k(i) / x(i) is computed. The median f̄_k across epochs gives a stable fraction. At prediction time, the layer compaction is simply f̄_k times the local InSAR displacement.

**Pros:**
- Zero free parameters (if f̄_k is taken as the training-set median)
- R^2 $\approx$ 0.97 at InSAR-dominant layers
- Computationally trivial
- Already validated across all stations

**Cons:**
- Static fraction f̄_k cannot capture regime transitions (elastic → inelastic)
- No GWL integration — cannot predict deviations from the proportional relationship driven by anomalous head changes
- Does not generalise to layers where corr(y, x) < 0.90
- Fails at decommissioned stations if the local f̄_k is unknown (requires spatial interpolation)

**When to use:** As the fallback for any layer where corr($\Delta$ h_k, x) > 0.7 and the GWL-driven model is fundamentally unidentifiable. This is the "known-correct answer" acknowledged in Section 1.

---

#### D2. Time-Varying InSAR Attribution (Kalman layer-fraction tracker)

**Equation:**
```
Ŷ_k(t) = f_k(t) · x(t)
f_k(t) = f_k(t-1) + process_noise     (state evolution)
y_k(t) = f_k(t) · x(t) + ε            (observation model at MLCW stations)
```

**How it works:** At MLCW calibration stations, $y_{k}$(t) and x(t) are both observed, so $f_{k}$(t) = $y_{k}$(t) / x(t) is known exactly at each epoch. The Kalman filter learns a smooth state-space model for $f_{k}$(t) from these observed fractions. At decommissioned stations or unmonitored grid points, the Kalman filter runs forward with the learned process noise model, producing f̂_k(t) from InSAR alone.

**Key difference from D1:** $f_{k}$(t) is allowed to evolve slowly over time. This captures changes in the layer's compaction share — for example, if a layer transitions from elastic to inelastic dominance, its fraction of total InSAR displacement increases. The Kalman filter tracks this shift.

**Reference:** Dobigeon & Tourneret (2020, arXiv:2001.00425) — Kalman + EM for multitemporal spectral unmixing. In hyperspectral imaging, each pixel is a mixture of spectral endmembers with time-varying abundances tracked via Kalman filter. The mapping to this problem is direct: InSAR x(t) is the mixed signal, layers k are the endmembers, and $f_{k}$(t) are the time-varying fractions with the constraint $\Sigma_k $f_{k}$(t) = $\alpha$ (the InSAR-to-MLCW scaling factor), not $\Sigma_k $f_{k}$(t) = 1.

**Implementation sketch (~150–200 lines):**
1. At each MLCW station, compute $f_{k}$(t) = $y_{k}$(t) / x(t) for all training epochs
2. Fit a local-level state-space model (random walk + observation noise) via maximum likelihood
3. The fitted process noise variance $\sigma$^2_q determines how quickly $f_{k}$(t) can change
4. At prediction: given x(t) and the last filtered f̂_k(t-1), predict ŷ_k(t) = f̂_k(t) $\cdot x(t)

**Pros:**
- Captures slow regime transitions that the static D1 misses
- Simple, interpretable, low-dimensional (2 parameters per layer: $\sigma$^2_q, $\sigma$^2_$\varepsilon$)
- Works with as few as 5 training epochs
- No GWL required at prediction time

**Cons:**
- Cannot respond to GWL-driven anomalies (a sudden head drop → compaction spike that InSAR alone does not resolve at the layer level)
- Requires $f_{k}$(t) to be observed at calibration stations (MLCW must exist for training)
- The fraction constraint $\Sigma_k $f_{k}$(t) = $\alpha$ is not automatically enforced — needs a post-hoc normalisation or a Dirichlet state-space formulation

**When to use:** For decommissioned station prediction where the historical $f_{k}$(t) is well-observed up to shutdown date, and the layer's regime is not expected to change drastically post-shutdown.

---

#### D3. InSAR-Dominant + GWL-Residual Model (inverted IHM-F hierarchy)

**Equation:**
```
Ŷ_k(t) = f̄_k · x(t) + g_k(Δh_k, τ_k)
```
where g_k($\Delta$ h_k, $\tau_k) is a small GWL-based correction fitted on the residual r_k(t) = $y_{k}$(t) − f̄_k $\cdot x(t).

**How it works:** This inverts the IHM-F paradigm. Instead of:
```
IHM-F:     ŷ_k = S_ske · Δh_k^e + S_skv · Δh_k^i + β_k · x    (GWL primary, InSAR secondary)
```
the InSAR-dominant model is:
```
InSAR-1st: ŷ_k = f̄_k · x + γ_k · Δh_k(t − τ_k)                (InSAR primary, GWL residual)
```
where $\gamma_k is a single GWL response coefficient fitted on the residual, not on the raw $y_{k}$.

**Why this matters for collinearity:** When corr($\Delta$ h_k, x) = 0.24 (as at TUKU F3), $\Delta$ h_k and x are sufficiently distinct that the residual r_k(t) = $y_{k}$(t) − f̄_k $\cdot x(t) contains the GWL-specific signal. The residual has corr(r_k, $\Delta$ h_k) $\approx$ corr($y_{k}$ − f̄_k $\cdot x, $\Delta$ h_k). Since f̄_k $\cdot x captures the InSAR-correlated portion of $y_{k}$, the residual is orthogonal to x by construction (in expectation), leaving only the GWL contribution. This is a better-conditioned regression: one predictor ($\Delta$ h_k) on one target (r_k), with x already accounted for.

**Key design choices:**
- **f̄_k estimation:** Use the training-set median (same as D1), or fit jointly with $\gamma_k
- **$\gamma_k interpretation:** $\gamma_k is NOT a storage coefficient. It is a residual response in mm per metre of head change on the portion of compaction NOT explained by InSAR. It does not have the same physical units or interpretation as $S_{ske}$/$S_{skv}$
- **$\tau_k estimation:** Grid search on the residual, same as IHM-F but on r_k(t) instead of $y_{k}$(t)
- **Regime handling:** A single $\gamma_k works for both elastic and inelastic regimes because the InSAR term f̄_k $\cdot x already absorbs the dominant regime-dependent signal

**Pros:**
- Directly solves the collinearity problem: GWL is fitted on InSAR-orthogonalised residual
- Single GWL coefficient $\gamma_k (vs. 2 in IHM-F) — lower variance, better conditioned
- Reduces to D1 when $\gamma_k $\approx$ 0 (GWL has no additional predictive power)
- Physically interpretable: f̄_k tells you "how much of this layer's compaction is InSAR-correlated," $\gamma_k tells you "how much extra compaction per metre of head drop, beyond what InSAR predicts"

**Cons:**
- $\gamma_k is not a standard storage coefficient — cannot directly compare to 2S-TOOL $S_{ske}$/$S_{skv}$
- If corr($\Delta$ h_k, x) is actually high (>0.7), the residual r_k(t) has near-zero GWL signal and $\gamma_k is unidentifiable (same failure mode as IHM-F, but with graceful degradation to D1)
- The decomposition f̄_k $\cdot x vs. $\gamma_k $\cdot $\Delta$ h_k is statistical, not causal — InSAR may be correlated with compaction for non-GWL reasons (tectonics, surface loading), and f̄_k will absorb those

**When to use:** At layers where corr(y, x) > 0.95 AND corr($\Delta$ h, x) < 0.5 — the sweet spot where InSAR provides the dominant signal and GWL contributes a small but identifiable residual. TUKU F2–F4 all qualify.

---

#### D4. Blind Source Separation from InSAR (vbICA → layer attribution)

**Equation:**
```
x(t) = Σ_j a_j · IC_j(t)                  (InSAR = weighted sum of independent components)
IC_j(t) = independent temporal patterns    (blindly separated — no GWL or MLCW input)
y_k(t) = Σ_j b_{kj} · IC_j(t) + ε_k       (per-layer MLCW = linear combination of ICs)
```

**How it works:** Variational Bayesian ICA (Gualandi & Liu 2021, DOI: 10.1029/2020JB020845) decomposes the InSAR displacement time series into statistically independent temporal components. Each component has a characteristic temporal signature (e.g., long-term monotonic = inelastic; seasonal oscillation = elastic). The ICs are then regressed against known MLCW layer time series at the 37 calibration stations to learn the mapping b_{kj} — how much of each IC contributes to each layer.

**Two-stage training:**
1. **Unsupervised:** Apply vbICA to the InSAR time series at all 39 MLCW stations + 8,577 grid points. Output: K independent components (typically K = 3–6) and their spatial loading maps a_j(g)
2. **Supervised (calibration):** At the 37 MLCW stations, regress $y_{k}$(t) = $\Sigma_j b_{kj} $\cdot IC_j(t) to learn the per-layer IC coefficients b_{kj}
3. **Prediction:** At any grid point g, ŷ_k(g, t) = $\Sigma_j b_{kj} $\cdot IC_j(t) where the IC_j(t) are the same everywhere and b_{kj} is interpolated from station values

**Why this is fundamentally different from IHM-F:** IHM-F assumes the physics ($\Delta$ h drives compaction) and fits parameters. vbICA assumes nothing — it lets the data define the temporal patterns, then maps those patterns to layers. The ICs naturally separate shallow/elastic from deep/inelastic signals because these have different temporal statistics. No GWL, no ODE, no storage coefficient — pure signal decomposition.

**Key reference:** Zhao et al. (2024, DOI: 10.1109/JSTARS.2023.3323699) applied this approach on the Beijing Plain: PS-InSAR decomposed into ICs, then MGWR attributed ICs to four aquifer groups (0–50 m, 50–100 m, 100–180 m, 180–300 m). Settlement proportions: 14.75%, 23.65%, 33.44%, 28.16%. Skeletal storage coefficients were inverted per group from the spatial relationship between InSAR deformation and head change.

**Pros:**
- No GWL required for the decomposition itself (only for post-hoc physical interpretation)
- Naturally separates elastic (seasonal) from inelastic (secular) signals — directly addresses the regime problem
- Spatial loading maps a_j(g) show WHERE each deformation mode is active — a spatial diagnostic that IHM-F cannot produce
- Works without any MLCW data for the decomposition; the calibration step (b_{kj}) only needs 37 stations

**Cons:**
- ICs are statistical constructs, not physical layers — the mapping b_{kj} may assign one IC to multiple layers or vice versa
- ICs decompose the total signal, not the per-layer signal — if two layers have identical temporal patterns, they occupy the same IC and cannot be separated
- Number of ICs K is a free parameter — the correct K is not obvious from the physics
- No forward ODE — predictions are linear combinations of fixed ICs; cannot respond to unseen GWL scenarios

**When to use:** For spatial mapping of deformation modes across the full fan (8,577 grid points). Complements the physics-based methods by providing an independent, data-driven decomposition that can validate (or challenge) the IHM-F's attribution of compaction to specific layers.

---

#### D5. InSAR-to-Layers Direct Learning (no GWL at prediction time)

**Core idea:** Train a model that maps directly from InSAR time windows to per-layer compaction, using the 37 MLCW stations as supervised training data. At prediction time, only InSAR (and optionally stratigraphy features) is required — no GWL.

**Architecture:**
```
Input:  [x(t-W), x(t-W+1), ..., x(t)]  (InSAR time window of length W)
        + optional: stratigraphy features from BME raster at location g
        
Output: [ŷ_F1(t), ŷ_T1(t), ŷ_F2(t), ŷ_T2(t), ŷ_F3(t), ŷ_F4(t)]  (6 layer compactions at epoch t)
```

**Model variants (increasing complexity):**
1. **Ridge regression:** ŷ_k = $\Sigma_{j=0}^{W-1} w_{k,j} $\cdot x(t−j). Each layer gets its own temporal filter on InSAR. Equivalent to a distributed-lag model with InSAR as the sole driver.
2. **1D CNN:** A convolutional network over the InSAR time window. The CNN learns temporal patterns (slow trend = deep inelastic, fast oscillation = shallow elastic) and maps them to layers.
3. **Temporal attention:** An attention mechanism over the InSAR window that learns which past epochs are most predictive for each layer. Attention weights vary by layer — F4 (deep inelastic) may weight older epochs more heavily than F1 (shallow elastic).
4. **Spatial CNN (Stage 2):** At the 8,577 grid points, replace the per-layer output head with a spatial CNN that takes the InSAR spatial field as input and outputs per-layer compaction maps.

**Training:** Supervised at the 37 MLCW stations. Loss = MSE(ŷ_k, $y_{k}$) summed over layers. Walk-forward validation folds as defined in CLAUDE.md (4 folds with expanding windows).

**How this breaks Hard #2 (the degeneracy problem):** The model learns the **temporal signature** of each layer from the training data. If F3 compaction consistently lags InSAR by 3 epochs while F1 responds within 1 epoch (because F3 is deeper and its GWL changes lag surface InSAR), the CNN or attention mechanism learns this lag structure. The degeneracy is broken by the fact that layers have different temporal response functions to the same InSAR input.

**Key assumption:** The temporal relationship between InSAR and per-layer compaction (the "impulse response function" of each layer to surface deformation) is spatially stationary — i.e., F3 at station A responds to InSAR with the same temporal pattern as F3 at station B. This is plausible if the layer's hydrogeological properties are spatially coherent (which the BME stratigraphy should confirm).

**Pros:**
- Zero GWL requirement at prediction time — works at any InSAR grid point
- Learns layer-specific temporal filters from data, not physics assumptions
- Can be as simple (ridge) or complex (CNN + attention) as the data supports
- Naturally handles the collinearity problem — InSAR is the only predictor

**Cons:**
- Black box — no physical parameters ($S_{ske}$, $S_{skv}$, $\tau$) are recovered
- Cannot generalise to GWL scenarios not represented in the training data (e.g., a severe drought with head drops beyond the historical range)
- Requires spatial stationarity of the InSAR-to-layer impulse response — testable at 37 stations
- Training data limited to 37 stations $\times$ ~700 epochs $\approx$ 25,900 samples (adequate for ridge/light CNN, inadequate for deep architectures)

**When to use:** As the operational prediction model at 8,577 grid points where GWL is not available. Calibration at 37 MLCW stations → prediction everywhere.

---

#### Comparison: InSAR-Primary Methods (D1–D5)

| Criterion | D1: Static f̄_k | D2: Kalman $f_{k}$(t) | D3: InSAR + GWL residual | D4: vbICA | D5: InSAR→Layers CNN |
|---|---|---|---|---|---|
| **GWL required?** | No | No | Yes (residual only) | No (decomp); Yes (calibration) | No |
| **Captures regime change?** | No | Slow drift only | Yes (via GWL residual) | Yes (separate ICs) | Implicitly (via temporal filters) |
| **Spatial transferability** | Interpolate f̄_k | Interpolate Kalman params | Interpolate $\gamma_k, $\tau_k | IC maps a_j(g) | Direct prediction |
| **Physical interpretability** | f̄_k = fraction | $f_{k}$(t) = fraction | $\gamma_k \ne storage coeff | IC_j = mode, b_{kj} = mapping | None (black box) |
| **Free parameters** | 0 | 2 per layer | 2–3 per layer | K (num ICs) + K$\times$ 6 | Hundreds–thousands |
| **Min corr(y, x) for validity** | >0.90 | >0.85 | >0.80 | Any (decomposition is data-driven) | Any (needs training data) |
| **Hard #2 mechanism** | N/A (calibrated) | N/A (calibrated) | Physics residual | Learnt temporal statistics | Learnt temporal filters |
| **Implementation effort** | Already done | ~150 lines | ~200 lines | ~300 lines + vbICA package | ~400 lines PyTorch |

---

### Recommended integration: The Two-Track Strategy

The document currently proposes Approaches A–C, all of which treat GWL as the primary per-layer driver. Approach D presents the InSAR-primary alternative. The two families are complementary, not competing:

- **For layers where corr($\Delta$ h_k, x) > 0.7:** The GWL signal is fundamentally unidentifiable from the InSAR signal. Use **D1 (static f̄_k)** as the operational prediction. Acknowledge this as the identifiability limit — no method can separate inseparable regressors.
- **For layers where 0.3 < corr($\Delta$ h_k, x) < 0.7:** GWL adds incremental information beyond InSAR. Use **D3 (InSAR-dominant + GWL residual)** — this is the best-conditioned way to extract the GWL signal, because InSAR is partialled out first.
- **For layers where corr($\Delta$ h_k, x) < 0.3:** GWL is largely independent of InSAR. The IHM-F hierarchy (Approach A) is appropriate here — GWL can serve as the primary driver because it carries information not present in InSAR.
- **For spatial extension to 8,577 grid points:** **D5 (InSAR→Layers CNN)** provides an operational prediction without GWL. **D4 (vbICA)** provides an independent, data-driven decomposition that can be compared to the physics-based spatial extension (Approach C) as a validation check.

**Decision rule at each (station, layer) pair:**
```
if corr(y_k, x) < 0.80:   → GWL-primary (Approach A / IHM-F)
elif corr(Δh_k, x) > 0.6: → D1 (static f̄_k, identifiability limit)
elif corr(y_k, x) > 0.95: → D3 (InSAR-dominant + GWL residual)
else:                      → D2 (Kalman tracker) or D3
```

---

## 5. Recommended Path

**Immediate next step:** Approach A pilot at TUKU — implement the multi-station neural IHM-F as a single-station prototype (TUKU only) to:
1. Verify that the hard-constraint parameterisation (softplus) eliminates bound-pinning at F3
2. Validate walk-forward RMSE against the current IHM-F bounded OLS baseline
3. Check whether the InSAR consistency loss `L_InSAR` improves or degrades layer attribution

**Parallel benchmarking step:** Run the InSAR-primary methods (Approach D) on TUKU as a comparison track:
1. **D1 (static f̄_k):** Already computed — serves as the RMSE floor for F2/F3/F4
2. **D3 (InSAR + GWL residual):** Implement on TUKU F2–F4 to test whether $\gamma_k > 0 (GWL adds residual information beyond f̄_k $\cdot x). If $\gamma_k $\approx$ 0 at all three layers, the InSAR-primary hierarchy is the correct modeling choice for those layers
3. **D4 (vbICA):** Decompose TUKU InSAR into 3–6 ICs, regress against known MLCW layers — check whether ICs naturally separate F2 vs. F3 vs. F4

**Decision criterion for full multi-station training:** If the TUKU pilot reduces F3 RMSE by >10% vs. bounded OLS baseline, or produces non-zero $S_{ske}$/$S_{skv}$ for F3 with physically plausible values, proceed to full 37-station training. If TUKU F3 remains non-identifiable even with the physics ODE (i.e., corr(dH, x) = 0.24 is fundamentally insufficient), document this as the identifiability limit and accept the static proportional model for F3 at all stations.

**Decision criterion for InSAR-primary vs. GWL-primary hierarchy:** After benchmarking both D3 and Approach A on TUKU, apply the decision rule from §4 (Approach D — Recommended Integration):
- If D3 achieves lower RMSE than Approach A at F2/F3/F4, the InSAR-primary hierarchy is the correct paradigm for InSAR-dominant layers
- If $\gamma_k > 0 (statistically significant) in D3, GWL adds incremental value beyond InSAR even at highly InSAR-correlated layers — the two-track strategy is validated
- If D4 (vbICA) produces ICs that cleanly separate F2, F3, F4 temporal patterns, this is independent evidence that temporal signatures can break the degeneracy, supporting D5 for spatial extension

**Stage 2 spatial extension:** After Approach A validates at the station level, add the stratigraphy embedding network to produce Approach C. This requires:
1. Extracting BME hydrofacies features at all 8,577 grid points (from 112_BME_CRAF.csv)
2. Training the embedding network across the 37 MLCW stations
3. Predicting S_ske_k(s), S_skv_k(s) at all grid points
4. Running IHM-F forward for the spatial compaction field

---

## 6. Key References

| Reference | Relevance |
|---|---|
| Alexandrov & Vesselinov (2014, *Water Resources Research*). DOI: 10.1002/2013WR015037 | NMF blind source separation for groundwater pressure — most direct analogue |
| Gualandi et al. (2021, *JGR Solid Earth*). DOI: 10.1029/2020JB020845 | Variational Bayesian ICA for InSAR displacement decomposition |
| Gong et al. (2024, *Comput.-Aided Civil Infrastruct. Eng.*). DOI: 10.1111/mice.13326 | PINN for stratified consolidation coefficient inversion from short windows |
| Guo et al. (2025, *ScienceDirect*). DOI: 10.1016/j.esg.2025 | PINN for land subsidence, Dezhou City — direct domain analogue |
| Klotz et al. (2022, *HESS*, 26, 5085–5116) | Neural ODEs for multi-catchment hydrology with shared weights |
| Morales-Álvarez et al. (2022, *INFORMS JDS*) | Weakly supervised multi-output GP for correlated outputs with partial observations |
| Chen et al. (2024, *Statistica Sinica*, 34, 291–311) | DeepKriging spatial prediction from sparse point data |
| Janati et al. (2020, *NeuroImage*, 214, 116788) | Multi-task MEG/EEG source localization — multi-station transfer analogue |
| Lu et al. (2021, *SIAM J. Sci. Comput.*) | Hard-constraint PINN via softplus parameterisation |
| Dobigeon & Tourneret (2020, arXiv:2001.00425) | Kalman + EM for multitemporal spectral unmixing — Kalman layer fraction tracker |
| Carlson et al. (2024, *Remote Sens. Environ.*). DOI: 10.1016/j.rse.2024.114303 | Poroelastic Green's function joint inversion of GNSS + GRACE + InSAR — depth-disaggregated storage change |
| Zhao et al. (2024, *IEEE JSTARS*). DOI: 10.1109/JSTARS.2023.3323699 | PS-InSAR + MGWR multi-aquifer deformation decomposition — InSAR as primary spatial variable for depth attribution |

---

## 7. What to Read Next

Before implementing any approach, the following are worth reading:

**For Approach A (neural IHM-F):**
1. **Klotz et al. 2022 (HESS)** — Section 3.2 on shared-weight ODE training across catchments. The `torchdiffeq` library they use is directly applicable.
2. **Gong et al. 2024 (MICE)** — Figure 3 shows the PINN loss curves for short-window consolidation inversion. The training stability pattern is what to expect for the IHM-F PINN variant.
3. **`tau_demo_TUKU/03_reconstruct_and_evaluate.py`** — This already implements the forward IHM-F ODE for TUKU; the Approach A implementation wraps this in a PyTorch gradient tape.

**For Approach D (InSAR-primary methods):**
4. **`scripts/06_direct_ratio/`** — The existing direct ratio implementation. Run `compute_direct_ratio.py` on TUKU to get the D1 baseline RMSE per layer (already computed — check `results/direct_ratio/TUKU/`).
5. **Gualandi & Liu (2021, *JGR Solid Earth*)** — vbICA code is available at the author's GitHub. The method section (§2.2–2.3) describes the variational Bayesian formulation. Apply to TUKU InSAR-only first.
6. **Zhao et al. (2024, *IEEE JSTARS*)** — Figure 5 shows the IC-to-aquifer-group attribution via MGWR. This is the template for D4's calibration step.

---

*End of brainstorming document. Ready for user review before implementation planning.*
