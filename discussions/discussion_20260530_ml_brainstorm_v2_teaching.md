# How to Predict Compaction Layer by Layer — A Practical Guide

**Date:** 2026-05-30  
**For:** Anyone learning this problem for the first time  
**What this document does:** Explains, in plain language, the different ways you can use machine learning to figure out how much each underground layer is compacting — and which method makes sense for your situation.

---

## 1. What Is Actually Happening Underground?

### The place

The Choushui River Alluvial Fan sits on the west coast of central Taiwan. It covers about 1,800 km^2 — roughly the size of a large city. Underneath it, the ground is not one solid block. It is a stack of seven layers, like a layer cake:

| Layer | What it is | Average thickness | Role in compaction |
|-------|-----------|-------------------|-------------------|
| F1 | Sand and gravel aquifer | 42 m | Minor |
| T1 | Clay/silt aquitard | 14 m | Barrier — stops water flow |
| **F2** | **Sand aquifer (main water source)** | **95 m** | **Dominant — most compaction happens here** |
| T2 | Clay/silt aquitard | 23 m | Barrier |
| F3 | Sand aquifer | 86 m | Second most compaction |
| T3 | Thin clay | 11 m | Minor barrier |
| F4 | Deep sand aquifer | 24 m | Least compaction |

Aquifers are layers that hold and transmit water — think of them like sponges. Aquitards are clay-rich layers that block water flow — think of them like plastic wrap between the sponges.

### The physical chain (how subsidence actually happens)

Every time someone pumps water from an aquifer for farming or drinking, a physical chain reaction starts underground:

1. **Pumping** removes water from the sand layers (F1, F2, F3, F4).
2. The water pressure in those layers drops. (This is what "groundwater level decline" means — the pressure gauge reads lower.)
3. With less water pressure pushing outward, the weight of all the rock and sediment above presses down harder on the sediment skeleton.
4. The clay and silt layers (T1, T2, T3) get squeezed. Clay is compressible — like a wet sponge with a brick on top.
5. When the squeezing exceeds what the clay has ever experienced before, the compaction becomes **permanent**. The clay grains rearrange and stay that way. This is called **inelastic compaction**.
6. That compaction at depth shows up at the surface as **land subsidence** — the ground literally sinks.

In some parts of this fan, the ground has sunk over 2 meters since the 1990s. Current rates at hotspots like Tuku reach 4–5 cm per year.

### The three measurement tools

You have three completely different ways to measure what's happening:

**MLCW (Multi-Level Compaction Monitoring Well):** Imagine a steel pipe drilled 300 meters into the ground, with magnetic rings anchored at different depths. Each ring tells you exactly how much the sediment between it and the next ring has compressed. At Tuku station, there are 6 rings, giving you:
- F1 compaction (shallow aquifer)
- T1 compaction (shallow aquitard)
- F2 compaction (main aquifer, 35–217 m deep)
- T2 compaction
- F3 compaction (second aquifer, 140–275 m)
- F4 compaction (deep aquifer)

The MLCW measures compaction to 1 mm precision. This is your **ground truth** — the only instrument that tells you compaction per layer. The catch: there are only 37 of these stations across the entire fan.

**InSAR (Interferometric Synthetic Aperture Radar):** A satellite (Sentinel-1, operated by the European Space Agency) flies over Taiwan every 12 days. It bounces a radar wave off the ground and measures exactly how long it takes to come back. By comparing two passes, it can detect whether the ground moved by as little as a few millimeters. InSAR gives you surface displacement everywhere — at 8,577 grid points spaced 500 meters apart across the entire fan. But it only tells you the **total** surface movement. It cannot see which depth the movement came from.

**GWL (Groundwater Level):** Pressure sensors in wells measure the water pressure (hydraulic head) in each aquifer. When the pressure drops, you know water is being removed. GWL is measured at about 300 wells across the fan. For each MLCW station, one nearby well is assigned to each layer.

### The surprising fact that changes everything

Here are the actual numbers from Tuku station (TUKU), the most heavily instrumented station in the fan:

| Layer | Correlation between layer compaction and InSAR | Correlation between GWL change and InSAR |
|-------|-----------------------------------------------|----------------------------------------|
| F2 | **0.994** | 0.234 |
| F3 | **0.985** | 0.241 |
| F4 | **0.983** | 0.310 |

What this table says: **InSAR alone tracks per-layer compaction almost perfectly**. If you multiply the InSAR surface measurement by a fixed fraction per layer, you already get R^2 $\approx$ 0.97 — meaning you explain 97% of the layer's compaction without ever looking at groundwater levels.

And here is the catch: the groundwater level (GWL) and InSAR carry nearly the same information about what the ground is doing. The correlation between them is only ~0.24 — but because compaction correlates so strongly with both, any attempt to use both as separate predictors runs into a mathematical problem called **collinearity**. You cannot reliably separate "how much is due to GWL" from "how much is due to InSAR" when they move together this tightly.

This is not a failure of any particular method. It is a fact about the data. When two possible explanations for the same phenomenon are nearly identical, no algorithm can tell them apart.

---

## 2. Why Is This Hard? (The Two Practical Problems)

### Problem 1: 37 calibration points → 8,577 prediction points

You have MLCW data at 37 stations. Each station gives you per-layer compaction — the exact answer for that location. But you need to predict per-layer compaction at 8,577 grid points across the whole fan, most of which never had an MLCW.

This is like measuring temperature at 37 weather stations and needing a temperature map for the entire county. You need to interpolate — to guess the values in between based on what you know at the measurement points. This problem is well-understood. Many methods can do this (kriging, Gaussian processes, nearest-neighbor). It is not the hard part.

### Problem 2: One measurement, six unknowns

At any location without an MLCW, the satellite gives you ONE number: total surface subsidence. But you need to split that number into SIX parts — one for each underground layer.

```
Surface subsidence = F1 compaction + T1 compaction + F2 compaction + T2 compaction + F3 compaction + F4 compaction
```

This is one equation with six unknowns. Without additional information, it has infinitely many solutions. Any method that claims to decompose InSAR into depth layers at a new location must explain **how it breaks this deadlock**.

There are four legitimate ways:

1. **Physics:** If you know the physical law connecting groundwater level changes to compaction (compaction = storage coefficient $\times$ head change), and you have GWL measurements at that location, the physics equation provides the missing information for each layer.

2. **Spatial similarity:** Nearby locations tend to behave similarly. If F2 is the dominant compacting layer at stations A, B, and C, it probably dominates at station D too. You can learn this spatial pattern from the 37 calibration stations.

3. **Sparsity:** At most locations, only 1–2 layers are actively compacting. The other 4–5 layers contribute near zero. If you enforce sparsity (via L1 regularization), the problem becomes solvable — you are picking 1–2 active layers out of 6, not splitting one number six ways.

4. **Temporal fingerprint:** Each layer responds to surface deformation with a unique time pattern. F4 (deep, 200+ m) lags surface changes by months. F1 (shallow, 0–42 m) responds within days. If you can learn each layer's "impulse response" from the training data, the time pattern itself distinguishes the layers.

---

## 3. The Two Families of Solutions

All candidate methods fall into one of two families. The families are defined by which data source is treated as the **main driver** and which is the **correction**.

### Family 1: GWL as the main driver (physics-first)

**Core idea:** Groundwater level change is the physical cause of compaction. The physics equation is:

```
Compaction in layer k = S_ske × (elastic head change) + S_skv × (inelastic head change)
```

where $S_{ske}$ and $S_{skv}$ are storage coefficients — numbers that tell you how much the sediment compresses per meter of head drop. The job of the model is to find the right storage coefficients for each layer at each location. InSAR is used as a **supplementary check** — the sum of all layer predictions should match the InSAR surface measurement.

**Methods in this family:** Approach A (Neural IHM-F), Approach B (Multi-output GP), Approach C (Spatial-embedding Neural ODE).

**When it works best:** When GWL changes are clearly different from InSAR movements (corr($\Delta$ h, InSAR) < 0.3). In this case, GWL provides genuinely independent information that InSAR does not.

**When it struggles:** When GWL and InSAR carry nearly the same information (corr($\Delta$ h, InSAR) > 0.6). The model is asked to separate two nearly identical signals, which is mathematically ill-conditioned regardless of the solver.

### Family 2: InSAR as the main driver (data-first)

**Core idea:** InSAR already explains 97% of per-layer compaction at many layers. Instead of fighting this fact, embrace it. Let InSAR provide the main prediction, and use GWL only for the small correction on whatever InSAR misses:

```
Compaction in layer k = f_k × InSAR + γ_k × (head change, lagged)
                       ^_____________^   ^________________________^
                       97% of the answer    ~3% correction from GWL
```

**Methods in this family:** D1 (Static f̄_k), D2 (Kalman tracker), D3 (InSAR + GWL residual), D4 (vbICA blind separation), D5 (InSAR-to-layers direct learning).

**When it works best:** When InSAR tracks compaction tightly (corr(y, InSAR) > 0.95) and GWL is somewhat distinct from InSAR (corr($\Delta$ h, InSAR) < 0.5). At Tuku F2, F3, and F4, these conditions are met.

**When it struggles:** When a layer's compaction is NOT well-tracked by InSAR (corr(y, InSAR) < 0.80). In this case, the InSAR-first approach has no strong signal to anchor on, and GWL must be the primary driver.

### These families are complementary, not competing

The choice between them is not a matter of philosophy or preference. It is determined by a measurable quantity: **how strongly does the layer's actual compaction correlate with InSAR?** You compute this number for each (station, layer) pair from the training data. The number tells you which family to use — no guessing required.

---

## 4. The Methods — What Each One Actually Does

### D1: Static f̄_k — "InSAR times a fixed fraction"

**What problem it solves:** You need the simplest possible per-layer prediction at any location with InSAR data. No GWL needed.

**How it works:** At each MLCW station, you compute the fraction of total InSAR displacement that goes into each layer:

```
f_k = median( y_k(t) / x(t) )  across all training epochs
```

For example, if F2 accounts for 45% of the total surface subsidence at a station on average, then f_F2 = 0.45. At prediction time: predicted F2 compaction = 0.45 $\times$ InSAR(t).

At Tuku F2, this single number achieves R^2 = 0.988. It already beats many complex models.

| Need | Answer |
|------|--------|
| InSAR? | ✅ Required |
| GWL? | ❌ Not needed |
| MLCW for training? | ✅ At calibration stations only |
| BME stratigraphy? | ❌ Not needed |
| Implementation effort | Already done (`scripts/06_direct_ratio/`) |

**Limits:** $f_{k}$ is fixed over time — it cannot capture a layer transitioning from elastic to inelastic behavior. It cannot predict the response to a sudden head drop that is larger than anything in the training data. At layers where corr(y, InSAR) < 0.90, the static fraction is unreliable.

**Use when:** corr($\Delta$ h, InSAR) > 0.6 (GWL is not identifiable — accept the limit) OR you need a zero-parameter baseline.

---

### D3: InSAR + GWL residual — "InSAR does 97% of the work, GWL cleans up the rest"

**What problem it solves:** You want to use GWL information without suffering from the collinearity problem. Instead of fitting GWL and InSAR as competing predictors (which fails when they are correlated), you fit InSAR first, then fit GWL on whatever InSAR missed.

**How it works — two simple steps:**

Step 1: Subtract the InSAR-predicted part from the actual compaction:
```
residual_k(t) = actual_compaction_k(t) - f_k × InSAR(t)
```
This residual is the small amount (~3% of variance) that InSAR did not capture. Importantly, this residual is now **orthogonal to InSAR** — InSAR has been partialled out.

Step 2: Fit a simple one-parameter model on the residual:
```
residual_k(t) = γ_k × head_change_k(t - τ_k)
```
where $\gamma_k is the GWL response coefficient (how many mm of extra compaction per meter of head drop, beyond what InSAR predicted) and $\tau_k is the time lag (how long after a head drop does the compaction show up).

**Why this solves the collinearity problem:** In the original IHM-F, GWL and InSAR compete to explain the same 97% of variance. In D3, InSAR takes the 97% uncontested, and GWL only has to explain the remaining 3% — a much better-conditioned problem.

**The key test at Tuku:** If $\gamma_k $\approx$ 0 (statistically indistinguishable from zero) at F2, F3, and F4, then GWL genuinely adds nothing beyond InSAR for those layers. This is a finding, not a failure — you have discovered that InSAR is sufficient. If $\gamma_k > 0, you have found a small but real GWL contribution.

| Need | Answer |
|------|--------|
| InSAR? | ✅ Required |
| GWL? | ✅ Required (for the residual correction) |
| MLCW for training? | ✅ At calibration stations |
| BME stratigraphy? | ❌ Not needed |
| Implementation effort | ~200 lines of Python |

**Limits:** $\gamma_k is not a standard storage coefficient — it is a residual response with different units and interpretation. It cannot replace $S_{ske}$/$S_{skv}$ in physical comparisons. If corr($\Delta$ h, InSAR) is actually high (>0.7), even the residual has near-zero GWL signal, and D3 gracefully degrades to D1.

**Use when:** corr(y, InSAR) > 0.95 AND corr($\Delta$ h, InSAR) < 0.5 — the sweet spot at Tuku F2–F4.

---

### D4: Blind source separation (vbICA) — "Let the data find its own patterns"

**What problem it solves:** You want to decompose InSAR into depth-related components without assuming any physics model. Pure signal processing — the data tells you what patterns exist.

**How it works:** Variational Bayesian Independent Component Analysis (vbICA) takes the InSAR time series at all 8,577 grid points and asks: "What are the statistically independent temporal patterns hidden in this data?" It finds K patterns (typically 3–6) that are maximally independent of each other. Each pattern has:
- A **temporal signature** IC_j(t): how it evolves over time (e.g., steady downward trend = deep inelastic compaction; seasonal up-and-down = shallow elastic response)
- A **spatial loading map** a_j(g): where on the map this pattern is strong

The separation is blind — the algorithm does not know about F1, F2, or GWL. It just finds mathematical patterns. Then, at the 37 MLCW stations, you learn how each pattern maps to each layer:

```
Layer_k_compaction(t) = b_{k1} × IC1(t) + b_{k2} × IC2(t) + ... + b_{kK} × ICK(t)
```

The coefficients b_{kj} are learned by simple linear regression at the 37 calibration stations. At any other grid point, you use the same ICs (they are the same everywhere) and interpolate the b_{kj} coefficients.

**Why this is powerful:** No physics assumptions means no physics mistakes. If the data says F2 and F3 have different temporal signatures, vbICA will separate them. If they have identical signatures, it will merge them — honestly reflecting the data's limits. The spatial loading maps show you WHERE each deformation mode is active — a diagnostic no other method provides.

| Need | Answer |
|------|--------|
| InSAR? | ✅ Required (at all grid points) |
| GWL? | ❌ Not needed for decomposition; optional for physical interpretation |
| MLCW for training? | ✅ At calibration stations only (to learn b_{kj}) |
| BME stratigraphy? | ❌ Not needed |
| Implementation effort | ~300 lines of Python + existing vbICA package |

**Limits:** The independent components are mathematical constructs, not physical layers. You cannot guarantee that IC1 = F2 and IC2 = F3 — the mapping may be mixed. If two layers have perfectly identical temporal behavior, they occupy the same IC and cannot be separated (this is honest — the data cannot distinguish them either). The method cannot predict the response to a head change scenario never seen in the training InSAR data.

**Use when:** You want an independent, assumption-free decomposition to validate (or challenge) the physics-based methods. Also useful for spatial mapping of deformation modes when GWL is not available.

---

### D5: InSAR-to-layers direct learning — "Teach a model to recognize each layer's time signature"

**What problem it solves:** You want to predict per-layer compaction at any grid point using InSAR alone. No physics equations, no parameter interpolation — just a learned mapping from InSAR time windows to layer outputs.

**How it works:** At the 37 MLCW stations, you have both the input (InSAR time series) and the output (per-layer compaction). You train a model — anything from simple linear regression to a small neural network — to map one to the other:

```
Input:  InSAR(t-12), InSAR(t-11), ..., InSAR(t)   (e.g., 12 past epochs = 60 days)
Output: F1(t), T1(t), F2(t), T2(t), F3(t), F4(t)  (6 numbers = compaction per layer)
```

The model learns that F4 (deep layer) responds to InSAR with a different lag and smoothing than F1 (shallow layer). These different **temporal fingerprints** are what allow the model to split one InSAR number into six layer outputs.

**Model options from simplest to most complex:**
1. **Ridge regression:** Each layer gets its own set of weights on past InSAR values. Equivalent to a distributed-lag model. ~150 parameters total, virtually no overfitting risk.
2. **1D CNN:** A small convolutional network (3–5 layers) that learns temporal patterns shared across layers. ~5,000 parameters.
3. **Attention:** The model learns to pay attention to different past epochs for different layers — F4 attention peaks at t−8 epochs, F1 attention peaks at t−1.

**The key assumption:** The temporal relationship between InSAR and each layer's compaction is spatially stationary. F3 at station A responds to InSAR with the same time pattern as F3 at station B (even if the amount of compaction differs). This is testable: you can compute the cross-correlation lag function at each of the 37 stations and check consistency.

| Need | Answer |
|------|--------|
| InSAR? | ✅ Required |
| GWL? | ❌ Not needed at prediction time |
| MLCW for training? | ✅ At calibration stations |
| BME stratigraphy? | ❌ Not needed (optional improvement) |
| Implementation effort | ~400 lines PyTorch (CNN variant) or ~100 lines scikit-learn (Ridge variant) |

**Limits:** Black box — no physical parameters are recovered. Cannot generalize to head-change scenarios not represented in the training InSAR data (e.g., an unprecedented drought). The learned mapping is statistical, not causal — if InSAR correlates with compaction for non-GWL reasons (tectonic motion, surface loading), the model will still use it for prediction. Training data is limited to ~37 stations $\times$ ~700 epochs $\approx$ 25,900 samples — adequate for ridge regression or a light CNN, but insufficient for deep architectures.

**Use when:** You need an operational prediction model at many grid points where GWL is unavailable. Start with ridge regression as a sanity check; add complexity only if it improves walk-forward RMSE.

---

### A: Neural IHM-F — "Fit the physics equation with a neural network, sharing across stations"

**What problem it solves:** You want to estimate physical storage coefficients ($S_{ske}$, $S_{skv}$) that are comparable to published reference values and have clear physical meaning. The current IHM-F fits each station independently — this version fits all 37 stations jointly, using information from well-behaved stations to regularize problematic ones.

**How it works:** The physics is the same as the original IHM-F:

```
Compaction in layer k = S_ske × (elastic head change) + S_skv × (inelastic head change)
```

But instead of fitting each station separately with bounded least squares, all 37 stations feed into a shared neural network. Each station has its own per-layer parameters (S_ske_k, S_skv_k, $\tau_k), but they are constrained to be physically plausible via softplus parameterization:
- $S_{ske}$ = softplus(a) → guaranteed > 0
- $S_{skv}$ = $S_{ske}$ + softplus(b) → guaranteed > $S_{ske}$ > 0

The loss function has two parts: (1) fit the MLCW compaction at each layer, and (2) ensure the sum of all layer predictions matches the InSAR surface measurement.

**How it handles collinear layers:** At a station where F3 is collinear with InSAR, the station's own data provides almost no information about $S_{ske}$ and $S_{skv}$ for F3. But the shared training means the model has seen F3 at other stations where it IS identifiable. The shared physics backbone regularizes the collinear case toward a physically consistent value — "borrowing strength" from stations where the data is informative.

| Need | Answer |
|------|--------|
| InSAR? | ✅ Required (for consistency loss) |
| GWL? | ✅ Required (primary per-layer driver) |
| MLCW for training? | ✅ At calibration stations |
| BME stratigraphy? | ❌ Not needed for station-level; needed only for spatial embedding variant (Approach C) |
| Implementation effort | ~400–600 lines PyTorch + torchdiffeq |

**Limits:** More complex to implement than single-station bounded OLS. Training stability at elastic/inelastic regime transitions is a known challenge. If corr($\Delta$ h, InSAR) is high at ALL stations for a given layer, the shared backbone has no informative station to borrow from — the layer remains unidentifiable.

**Use when:** corr(y, InSAR) < 0.80 for the layer (InSAR alone is insufficient — you need the physics equation) OR you need $S_{ske}$/$S_{skv}$ in standard physical units comparable to published values.

---

### B: Multi-output Gaussian Process — "Nearby stations behave similarly"

**What problem it solves:** You want a statistically principled way to predict per-layer compaction at unmonitored locations, with honest uncertainty bounds. No physics assumptions — purely spatial statistics.

**How it works:** A Gaussian Process (GP) models the 6 layer compaction time series as correlated outputs. The coregionalization matrix B (6$\times$ Q, typically Q=2–3) captures how the six layers co-vary: if F2 is high at a station, is F3 also high? Is T1 anti-correlated with F2? These relationships are learned from the 37 calibration stations.

At a new grid point, the GP predicts all 6 layers simultaneously using the learned spatial covariance. The prediction comes with an uncertainty estimate — the GP tells you "layer F2 is predicted at 12.3 $\pm$ 2.1 mm" rather than just "12.3 mm."

| Need | Answer |
|------|--------|
| InSAR? | ✅ As a spatial covariate (optional) |
| GWL? | ❌ Not required |
| MLCW for training? | ✅ At calibration stations |
| BME stratigraphy? | ❌ Not needed (uses X,Y coordinates only) |
| Implementation effort | ~200 lines Python with GPy or GPflow |

**Limits:** Does not produce $S_{ske}$ or $S_{skv}$ in physical units. The coregionalization matrix encodes cross-layer correlation, not storage coefficients. Less interpretable for the MLCW prediction task. Computational cost scales as O(N^3) with the number of stations — with 37 stations this is negligible, with 8,577 grid points it requires sparse approximations.

**Use when:** You need principled uncertainty quantification, or as a complementary spatial interpolation method for the $S_{ske}$/$S_{skv}$ parameters estimated by Approach A.

---

## 5. What the Choushui Fan Itself Tells Us (Empirical Constraints)

Any method you choose must respect the following facts about this specific study area. These are not assumptions — they are measured numbers from published studies.

### The M13/M23 boundary — a sign reversal you cannot ignore

The fan has two mechanically distinct zones:

- **M13 zone (proximal fan, east):** Unconfined aquifer conditions. When groundwater level drops, the land surface actually **rises** slightly (or subsides less). Measured at Pingding: 1 m head drop → 0.034 cm surface rise. This is a poroelastic effect — the reduced pore pressure causes the aquifer skeleton to expand slightly.

- **M23 zone (mid/distal fan, west):** Confined aquifer conditions. When groundwater level drops, the surface **subsides**. Measured at Hefeng: 1 m head drop → 0.176 cm elastic subsidence, and up to 7.34 cm of permanent subsidence if the head drops below its historical minimum.

**All 37 MLCW stations are in the M23 zone.** Any spatial interpolation that crosses the M13/M23 boundary without accounting for this sign reversal will produce physically impossible results — predicting subsidence where uplift occurs, or vice versa.

### Storage coefficient ranges — hard bounds from published tables

The published values in `choushui_skeletal_storage_coeffs.md` give you hard bounds. Any predicted $S_{ske}$ or $S_{skv}$ outside these ranges contradicts the regional literature:

| Parameter | Minimum | Maximum | Typical |
|-----------|---------|---------|---------|
| $S_{ske}$ (elastic) | 2.86 $\times$ 10⁻⁶ m⁻¹ | 3.87 $\times$ 10⁻⁴ m⁻¹ | ~2 $\times$ 10⁻⁵ m⁻¹ |
| $S_{skv}$ (inelastic) | 1.53 $\times$ 10⁻⁵ m⁻¹ | 3.00 $\times$ 10⁻^3 m⁻¹ | ~5 $\times$ 10⁻⁴ m⁻¹ |

A prediction of $S_{skv}$ = 5 $\times$ 10⁻^3 m⁻¹ is not "surprisingly large" — it is physically impossible for this fan, because no published measurement exceeds 3.00 $\times$ 10⁻^3 m⁻¹.

### F2 is the dominant compacting layer

F2 (35–217 m depth, 95 m average thickness) is the most heavily exploited aquifer. It accounts for the largest share of compaction at almost every station. Any method that predicts F4 compaction exceeding F2 compaction at a mid-fan station is suspicious — check your inputs before trusting the output.

### The elastic/inelastic threshold matters

Preconsolidation head $h_{c}$ separates elastic from inelastic behavior. This threshold varies per station and per layer. Methods that merge $S_{ke}$ and $S_{kv}$ into a single "storage coefficient" lose this distinction and cannot correctly predict behavior when the head crosses the preconsolidation threshold.

### Weak spatial correlation between pumping and subsidence

Maximum subsidence does not occur at the location of maximum pumping (Tatas et al. 2023). The spatial pattern of subsidence is controlled by the distribution of compressible fine-grained sediments (clay and silt), not just by where water is extracted. This is why BME stratigraphy could improve spatial interpolation — but it is also why coordinate-only interpolation can miss structure that the BME would capture.

---

## 6. Which Method Should You Use When?

Here is a practical decision guide. The answers come from computing two numbers at each (station, layer) pair from the training data:

```
c1 = corr( y_k, InSAR )        ← how well does InSAR track this layer's compaction?
c2 = corr( Δh_k, InSAR )       ← how redundant are GWL and InSAR?
```

| Your situation | c1 (y vs InSAR) | c2 ($\Delta$ h vs InSAR) | Recommended method | Why |
|---------------|-----------------|-------------------|-------------------|-----|
| Layer weakly correlated with InSAR | < 0.80 | Any | **A (Neural IHM-F)** | InSAR alone is insufficient. You need the physics equation with GWL as the main driver. |
| GWL and InSAR too similar | > 0.80 | > 0.6 | **D1 (static f̄_k)** | GWL is unidentifiable. Accept the identifiability limit. The static proportional model is the honest answer. |
| InSAR-dominant, GWL adds value | > 0.95 | 0.3–0.5 | **D3 (InSAR + GWL residual)** | InSAR provides 97%, GWL provides a small but real correction. Best-conditioned use of both data sources. |
| Moderate InSAR correlation | 0.80–0.95 | < 0.5 | **D2 (Kalman) or D3** | Test both. D2 if GWL is sparse; D3 if GWL is available. |
| No GWL at prediction location | Any | N/A | **D4 (vbICA) or D5 (CNN)** | InSAR-only methods. D4 for interpretable spatial modes; D5 for operational prediction. |
| Need physical parameters ($S_{ske}$, $S_{skv}$) | < 0.80 | < 0.3 | **A (Neural IHM-F)** | Only the physics-based methods produce storage coefficients in mm/m units. |
| Need uncertainty bounds | Any | Any | **B (Multi-output GP)** | GP gives principled posterior uncertainty. Use as complement to A or D methods. |

### The TUKU case study

At Tuku station, the correlations are:
- **F2:** c1 = 0.994, c2 = 0.234 → **D3** (InSAR-dominant, GWL adds on residual)
- **F3:** c1 = 0.985, c2 = 0.241 → **D3** 
- **F4:** c1 = 0.983, c2 = 0.310 → **D3**
- **F1, T1, T2:** Compute c1 from the data. If c1 < 0.80 for any of these, use Approach A for that layer.

The decision is not one-size-fits-all. Different layers at the same station can use different methods. This is a feature, not a bug — you are matching the method to the data structure.

---

## 7. What to Do Next (Practical Steps, in Order)

### Step 1: Use what already works
D1 (static f̄_k) is already computed for all 37 stations. Check `results/direct_ratio/TUKU/TUKU_direct_ratio_stats.csv`. For F2, F3, F4 at TUKU, D1 gives R^2 $\approx$ 0.97. This is your baseline — every other method must beat these numbers on walk-forward RMSE.

### Step 2: Test D3 on TUKU (~200 lines of Python)
Implement the two-step residual model for TUKU F2, F3, F4:
1. Compute residual_k(t) = $y_{k}$(t) − f̄_k $\times$ x(t)
2. Grid-search $\tau_k (0 to 12 epochs = 0 to ~60 days) that maximizes corr(residual_k, $\Delta$ h_lagged)
3. Fit $\gamma_k via OLS: residual_k(t) = $\gamma_k $\times$ $\Delta$ h_k(t − $\tau_k)
4. Compare walk-forward RMSE of D3 vs. D1

If $\gamma_k is statistically significant (p < 0.05) and D3 RMSE < D1 RMSE, GWL adds genuine value even for InSAR-dominant layers. If $\gamma_k $\approx$ 0, you have evidence that InSAR is sufficient — a publishable finding.

### Step 3: Run vbICA (D4) on TUKU InSAR (~300 lines of Python)
Apply the vbICA implementation from Gualandi & Liu (2021) — code available at the author's GitHub — to the TUKU InSAR time series alone. Decompose into K=3 to K=6 components. Regress the known MLCW layer time series against the independent components. Check:
- Do ICs naturally separate F2 vs. F3 vs. F4 temporal patterns?
- Do the spatial loading maps make geological sense?

### Step 4: Implement Approach A pilot at TUKU (~400 lines PyTorch)
Start with TUKU only, not all 37 stations. Test whether hard-constraint parameterization (softplus) eliminates bound-pinning at F3. Compare walk-forward RMSE against the current bounded OLS baseline.

### Step 5: Apply the decision framework to all 37 stations
For every (station, layer) pair, compute c1 and c2 from the training data. Assign each to D1, D3, or Approach A according to the decision guide in Section 6. This gives you a station-by-station, layer-by-layer recipe.

### What about BME stratigraphy?

**You do not need BME to start.** Every method except Approach C works without it. For methods that benefit from spatial interpolation (A, D1, D2, D3), use coordinate-based IDW or Gaussian Process interpolation on (X_TWD97, Y_TWD97). The 37 calibration stations provide adequate coverage of the M23 zone where subsidence is active.

The raw BME raster exists at `/mnt/hgfs/1000_SCRIPTS/MyPlayGround/20260510_temp/112_BME_CRAF.csv` (500 m grid, 0–300 m depth at 1 m intervals, 56 MB). Extracting features at the 8,577 grid points is a ~1–2 hour preprocessing script — not a research task. Add BME when you are ready to improve spatial interpolation, not as a prerequisite to start.

---

## Summary: The One-Page Version

**The problem:** 37 stations measure per-layer compaction. 8,577 grid points need it. The satellite gives one number per location; you need six.

**The catch:** InSAR already explains 97% of layer compaction at many layers. GWL adds information, but it is largely redundant with InSAR — creating a collinearity problem that breaks physics-first models.

**The insight:** InSAR and GWL are not competing explanations. Use InSAR for the 97% it already captures. Use GWL for the 3% residual. This inverted hierarchy solves the collinearity problem at its root.

**The methods:**
- **D1 (static f̄_k):** Already works. R^2 $\approx$ 0.97. Zero parameters. Your baseline.
- **D3 (InSAR + GWL residual):** InSAR takes the main signal; GWL cleans up. ~200 lines. Test first.
- **D4 (vbICA):** Let the data find its own patterns. No physics assumptions. Good validation tool.
- **D5 (CNN):** Learn temporal fingerprints from InSAR alone. For operational prediction everywhere.
- **A (Neural IHM-F):** Physics-first for layers where InSAR alone is insufficient.
- **B (Multi-output GP):** Spatial similarity. Principled uncertainty. Good complement.

**The decision:** Compute corr(y, InSAR) and corr($\Delta$ h, InSAR) at each layer. The numbers tell you which method.

**The constraints:** $S_{ske}$ between 2.86$\times$ 10⁻⁶ and 3.87$\times$ 10⁻⁴ m⁻¹. $S_{skv}$ between 1.53$\times$ 10⁻⁵ and 3.00$\times$ 10⁻^3 m⁻¹. M13/M23 sign reversal. F2 dominates. Respect the measured numbers.

**No BME needed to start.** Add it later as an improvement to spatial interpolation.

---

*End of teaching guide. Compare with `discussion_20260530_ml_brainstorm.md` for the full technical detail behind each method.*
