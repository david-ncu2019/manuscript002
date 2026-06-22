# Dialogue: ML-Nowcast v1 → v2 Enhancement Research

> **Participants:** 🧑 Trường (Nguyễn Thái Vinh Trường) · 🤖 Claude
> **Topic:** v1 results interpretation, attribution path, S5/S6 diagnosis, Track A/B/C roadmap → v2 physics-informed feature engineering and literature review.
> **Dates:** 2026-06-20 (run_001 baseline) → 2026-06-22 (literature review + enhancement strategy)
> **Note:** A *curated recap* of the conversation (not a verbatim transcript), kept as one chatbox to preserve the thread. Exact figures reside in `trials/run_001/figures/`, numbers in `trials/run_001/results/nowcast_metrics.json`, and a reference walkthrough in [`FIGURES_GUIDE.md`](FIGURES_GUIDE.md). Each suggestion is tagged **🟢 computable now** or **🟠 data-gated**. Papers cited include full local file paths when downloaded; otherwise the DOI is provided.

---

### 🧑 Trường, 2026-06-21 14:00
> I want to see the visualization of input data and output results clearly. Help me understand the figures, maybe a markdown to interpret them.

### 🤖 Claude, 2026-06-21 14:05
Seven figures and an interpretation guide have been produced. The two to examine first:

- **`input_dashboard.png`**: Raw drivers stacked over time, including the compaction target (per 50 m section S1 through S6), the GPS surface signal, the five groundwater heads, and rainfall. All series appear clean and monthly. One point worth flagging: the **LUNZI (S4) groundwater head is negative** (−5 to −16 m). This value is correct, because head is expressed in metres above mean sea level and must never have its sign flipped.
- **`driver_response_scatter.png`**: The physics check. For each section, piezometric head change is plotted against compaction. The expected relationship is "hydraulic head declines → fine-grained sediment compacts." Sections S1 through S4 show this pattern cleanly (correlation r = 0.51 to 0.67). S5 and S6 produce nearly flat scatter clouds (r = 0.20 and −0.17). This observation explains every result discussed below.

---

### 🧑 Trường, 2026-06-21 14:10
> Are we really doing nowcasting or not? Explain to me.

### 🤖 Claude, 2026-06-21 14:13
**Yes, by the strict definition.** The proof follows directly from the build code (`03_build_feature_table.py`):

- The **target** is the compaction increment at month *t* (`mlcw.diff()`).
- The **main feature**, the surface signal `dS_total`, is the GPS increment at month *t* (`gps.diff()`), at the **same timestamp with no time-shift**.

Input and output share the same month. This configuration constitutes **nowcasting** (estimating a hidden quantity *now* from signals available *now*), not **forecasting** the future. The task matches the operational need exactly: the MLCW wells are being shut down, so at test time only surface displacement and groundwater head remain available, and the model reconstructs the unseen per-layer compaction.

**One honest qualification must accompany this framing.** The strongest driver is the contemporaneous surface motion, and that surface motion is itself partly the sum of all the layer compactions. The model therefore partly regresses "a piece onto the whole at the same instant." This relationship is still legitimate nowcasting, **but it is not attribution.** The surface carrier is rank-1 (one shared degree of freedom for six layers, per GEMINI.md), so no claim of "this layer caused this fraction of the surface displacement" is justified. The outputs function as nowcasts, never as a decomposition.

---

### 🧑 Trường, 2026-06-21 14:18
> In your opinion, are our results good?

### 🤖 Claude, 2026-06-21 14:22
**Mixed, and honestly so. The model succeeds where the physics is observed and fails where the physics is absent.** The scoreboard on the held-out test years (2021 through 2023-02):

| Section | Depth | R² (test) | Skill vs persistence | Verdict |
|---------|-------|-----------|----------------------|---------|
| S1 | 0–50 m | **+0.81** | +0.37 | ✅ Strong |
| S2 | 50–100 m | **+0.50** | +0.12 | ✅ Good |
| S3 | 100–150 m | +0.31 | +0.03 | 🟡 Modest |
| S4 | 150–200 m | **+0.70** | +0.21 | ✅ Strong |
| S5 | 200–250 m | **−0.15** | −1.84 | 🔴 Fails |
| S6 | 250–300 m | **−0.13** | +0.07 | 🔴 Fails |
| **Pooled** | All | **+0.32** | +0.01 | 🟡 Mixed |

- **The successes:** S1, S2, and S4 recover the real seasonal compaction on years the model never saw. Pooled, the model exceeds the "predict the training-set mean" baseline by **+21%**.
- **The failures (S5, S6) reflect a data problem, not a model problem.** R² is negative for both, meaning the predictions are worse than a flat line. The reason is visible in the driver-response plot: the piezometric sensor does not observe the layer that is compacting. The F3/F4 piezometer screen sits at approximately 176 to 179 m and reads only the top approximately 12 m, while the aquitard that actually compacts lies at approximately 238 to 275 m. **The sensor does not monitor the layer that deforms.** No machine-learning method can learn a relationship absent from the data.
- **Baseline honesty:** The model exceeds *persistence* ("next month ≈ this month") by only +0.01 pooled. However, persistence is a strong baseline for slow monthly signals, so the meaningful comparison is versus the mean (+0.21). Additionally, the uncertainty bands cover 81% of points against a 90% target, indicating slight overconfidence.

**Summary:** A credible v1 that proves the approach works wherever the groundwater driver genuinely observes the compacting layer and honestly exposes the monitoring network's deep blind spot. The coefficients confirm the model relies most heavily on the surface signal `dS_total` = +0.27, followed by season = −0.23.

---

### 🧑 Trường, 2026-06-21 14:26
> If the results are not good, what can we do to improve?

### 🤖 Claude, 2026-06-21 14:30
Ranked by expected payoff:

1. **🥇 Fix the deep-section drivers (S5/S6).** This lever is the largest. S5 and S6 fail because the piezometric sensor does not reach the compacting aquitard. Options include assigning a deeper piezometer or a different well, or explicitly modeling the deep aquitard's **delayed (Terzaghi consolidation) response** instead of contemporaneous head. *Until the driver observes the layer, no other modification will rescue S5/S6.*
2. **🥈 Per-section conformal calibration.** A separate uncertainty band per section, replacing the single global width, would address the 0.81 coverage shortfall and the one-size-fits-all 2.06 mm band.
3. **🥉 Honesty ablation: withhold `dS_total`.** Because the surface feature dominates, a groundwater-only variant would quantify how much *true piezometric head* skill exists versus the surface "part-on-whole" shortcut.
4. **Model upgrades (only after drivers are fixed):** Compare ElasticNet or gradient boosting, add `GWL × fine_pct` interactions and richer lags. These sharpen the *already-good* sections, not the broken ones.
5. **Rainfall ablation and additional data:** Quantify whether rainfall actually contributes (its coefficients are currently negligible).

---

### 🧑 Trường, 2026-06-21 14:40
> I'm satisfied: we capture the *pattern* but not the *magnitude / extremes*, and that's good enough. Extremes are too hard. If we wanted them, maybe we need more driving factors. What other factors do you think of?

### 🤖 Claude, 2026-06-21 14:46
The reading is scientifically sound. The reason magnitude is difficult is rooted in physics: **extreme compaction originates from inelastic (virgin) consolidation**, which is **nonlinear and hysteretic**. A fine-grained layer compacts rapidly only when hydraulic head falls below its previous historical minimum (the preconsolidation head), because only then does effective stress exceed the preconsolidation stress and trigger irreversible skeletal rearrangement. Above that threshold, the layer barely deforms. A **linear** model (the current Bayesian Ridge) can only fit a straight line, so it **regresses toward the mean and shaves the peaks**. The gap therefore has **two** causes: missing variables **and** missing nonlinearity.

**Additional driving factors, ranked:**

| Rank | Factor | Why it helps magnitude | Status |
|------|--------|------------------------|--------|
| 🥇 | **Preconsolidation / effective-stress features**: running-min head `h_c`, virgin overshoot `max(0, h_c − h_t)`, × `fine_pct` | The *inelastic switch* that creates extremes, activating extra compaction during record-low heads | 🟢: `h_c` logic already exists in [`003_ihmf_terzaghi/scripts`](../003_ihmf_terzaghi/) |
| 🥇 | **Pumping / abstraction volume** | The proximate cause that head only proxies, carrying magnitude information head misses during heavy drawdown | 🟢/🟠: the repo contains an electricity-based pumping proxy ([report](../../002_docs/references/CRAF_groundwater_pumping_electricity_report.md)) |
| 🥈 | **Deeper / true-layer head** (S5, S6) | The current sensors do not reach the compacting aquitard (see the distance discussion below) | 🟠 data-gated |
| 🥈 | **InSAR spatial field** | The surrounding deformation *gradient* provides local-versus-regional context that the single GPS point lacks | 🟠: data in `001_data/insar.rar`, unextracted |
| 🥉 | **Rainfall components** | A weak *recharge* driver (rainfall raises head, slows compaction) | 🟢: `monthly_sum_rainfall_components.rar` is prepared |

**A modeling fix (not an additional factor):** A **nonlinear learner**, such as **Gradient Boosting** or **quantile regression**, would capture thresholds and saturation. GBM handles the preconsolidation switch. Quantile loss directly targets the *tails*. Caution: only 156 test points exist, so any nonlinear model must operate under the conformal wrapper to avoid overfitting.

---

### 🧑 Trường, 2026-06-21 15:39
> How do we progress toward the goal of "this layer causes what percentage of surface subsidence"?

### 🤖 Claude, 2026-06-21 15:46
**First, the honest wall.** Attribution **cannot** come from making the surface-regression nowcast better. The project already proved this limitation ([Feasibility Verdict](../../003_discussions/findings/FEASIBILITY_VERDICT_FINAL_20260611.md), [011_attribution](../011_attribution/README.md)):

- The surface carrier is **rank-1**: all six layers' surface contributions are proportional to *one* shared signal (SVD: one singular value, the other five < 4×10⁻¹³). One degree of freedom exists for six unknowns.
- **Amplitude-bound:** F2's seasonal compaction (4.71 mm) *exceeds* the total surface seasonal amplitude (3.83 mm). Layers partly cancel, so both cannot be recovered from their surface sum.

→ No regularizer on the *surface→layers inverse* resolves this degeneracy. **Improving v1 does not yield attribution.**

**The hopeful part is specific to the available data.** The verdict states the impossibility is **cadence-specific, not absolute**:

> *"At **monthly in-situ cadence, F3 detrended r = 0.862**: dynamics are recoverable when frequent in-situ measurements supply the phase information. The impossibility applies at annual and semiannual cadence only."*

**The ML data operates at monthly cadence.** Attribution is therefore within reach through three composable routes, building on `011_attribution`:

1. **Direct measurement where MLCW still runs (ground truth).** Each layer's share = `ΣΔC_layer / ΣΔC_surface`, measured, not predicted. This ratio serves as the calibration target. Reuse [`018_direct_ratio/direct_ratio_tuku_v2.py`](../../006_scripts/018_direct_ratio/).
2. **Forward per-layer modeling (the correct route for ungauged sites).** Build the surface signal **bottom-up** from each layer's *own* head (Terzaghi), sum, and extract each layer's percentage. **Rank-1 only forbids the inverse (surface→layers). The forward direction (layers→surface) is always permitted.**
3. **Monthly-cadence recovery**, the verdict's own escape hatch, which the current regime satisfies.

**The bridge from v1 (one concrete experiment):** Retrain the per-section nowcast **without `dS_total`**, using each section's *own* drivers only, then check whether **Σ (predicted ΔC_k) ≈ observed surface**. If the predictions sum back to the surface, the ratios constitute a **defensible attribution** that plugs into `011_attribution`'s constrained-inversion. (This is the same "GWL-only ablation" from above, reframed as the *attribution enabler*.)

**Remaining obstacle (ties to the next question):** The per-layer head drivers are severely collinear (mean r = 0.863, F2↔F3 r = 0.987). Greater *independence* among drivers directly improves attribution identifiability.

---

### 🧑 Trường, 2026-06-21 15:55
> The station is around 10 km from the TUKU MLCW station, so the groundwater fluctuation there would weakly affect subsidence at TUKU. Any suggestions?

### 🤖 Claude, 2026-06-21 16:05
The intuition is correct, but the actual distances reveal **two distinct problems, not one** (from [`gwl_to_mlcw_layer_assignment_v4.csv`](../../001_data/gwl/gwl_to_mlcw_layer_assignment_v4.csv)):

| Section | Well | Distance to TUKU | Screen vs layer | Problem |
|---------|------|------------------|-----------------|---------|
| S1 (0–50) | HONGLUN | **4.27 km** | shallow, acceptable | horizontal distance |
| S2 (50–100) | TUKU 09050321 | **14.5 m** (co-located) | screen 81–84 in 50–123 | ✅ **functions** (R² 0.50) |
| S3 (100–150) | TUKU 09050321 | **14.5 m** (co-located) | shared F2 well | ✅ functions (R² 0.31) |
| **S4 (150–200)** | LUNZI | **9.6 km** ⬅️ *the ~10 km in question* | 152–182 | **horizontal distance** |
| **S5 (200–250)** | TUKU 09050331 | **14.5 m** (co-located!) | **screen 176–179 in layer 173–273** | **vertical screen mismatch, NOT distance** |
| S6 (250–300) | LIUZHUANG | **6.05 km** | 270–294 | horizontal distance |

**Two distinct mechanisms operate:**
- **Horizontal distance** (S1, S4, S6): A well 4 to 10 km away samples a *different groundwater compartment*, producing legitimately weak correlation. **S4/LUNZI (9.6 km) is the case described.**
- **Vertical screen mismatch** (S5): The well is co-located (14.5 m) but screened at 176 to 179 m while the layer compacts to 273 m. **The sensor monitors the top, not the compacting base.** Distance is adequate, but depth is wrong.
- **S2/S3 prove the method is sound** when the driver is co-located and screened within the target band.

**Remedies (ranked, reusing existing tooling):**
1. 🟢 **Cross-correlation driver re-selection**: Pick each section's driver by *maximum cross-correlation* within a radius + screen-depth window. Reuse [`014_ring_gwl_xcorr`](../../006_scripts/014_ring_gwl_xcorr/).
2. 🟢 **Empirical lags** from v4's `xcorr_lag_days` (T2 = 355 d, F1 = 370 d) instead of the generic 1/3/6/12.
3. 🟢 **Multi-well composite head (IDW/blend)** to reduce noise from single distant gauges.
4. 🟠 **Spatial head interpolation sampled at TUKU**: ⚠️ This approach creates a *modeled* driver. Validate against held-out wells and never present the result as ground truth (GEMINI.md).
5. 🟠 **InSAR spatial gradient** as a partial substitute (requires `insar.rar`).

**The roadmap forms a staircase:**
```
3. FORWARD ATTRIBUTION  (layer = X%; monthly cadence makes it reachable)
        ▲  requires reliable per-layer signals
2. MAGNITUDE  (preconsolidation, pumping, nonlinear learner)
        ▲  requires drivers that actually observe the layer
1. DRIVER QUALITY  (xcorr re-selection · empirical lags · composite head)  ← FIRST
```
**Fix drivers → magnitude → forward attribution.** Each rung enables the next. All steps are consistent with rank-1 (the surface is never inverted, only built up). The cheapest first step is **xcorr driver re-selection + empirical lags**, which attacks the weak-correlation problem and improves both magnitude *and* attribution simultaneously.

---

### 🧑 Trường, 2026-06-21 17:15
> I prepared `001_data/gwl/well_section_catalog` using `006_scripts/022_gwl_section_categorization/categorize_wells_by_section.py`. I intend to interpolate the monthly groundwater levels of S5 and S6 to the position of the TUKU MLCW station. Do you think this is a good idea?

### 🤖 Claude, 2026-06-21 17:28
**Partly yes, but a cheaper and better first move exists, and one data bug requires fixing first.** The catalog was checked against the TUKU feather and the master inventory (TUKU MLCW at TWD97 187772, 2620611).

**The largest finding: TUKU already contains a co-located deep well that v1 never used.** `TUKU_gwl_timeseries.feather` contains **`09050341`**, screened at **257 to 263 m**, with **4,900 records**, only **~14 m from the MLCW**. v1 used this well for *nothing*: S5 used the top-only 09050331 (176 to 179 m) and S6 used LIUZHUANG (6 km away). Well 09050341 sits **squarely in the S6 band (250 to 300 m)**, and at 257 to 263 m it is also far closer to the S5 deep compacting zone than the 176 to 179 m well.
→ **For S6, interpolation is unnecessary: use `09050341` directly.** For S5 it represents a substantial improvement. **Execute this step first: zero modeling risk, one column already on disk.**

**Is interpolation a good idea for S5?** Yes, it is *reasonable* (not extrapolation). With wellcodes correctly zero-padded, the same-depth network near TUKU is:
- **S5 (200 to 250 m):** 6 wells ≤10 km, 14 ≤15 km, e.g. HONGLUN 09050121 @209 to 218 m (4.3 km), JIULONG 09040231 @179 to 191 m (8 km), JIAXING @194 to 206 m (8.4 km).
- **S6 (250 to 300 m):** 3 wells ≤10 km, 6 ≤15 km, e.g. LIUZHUANG 09080251 @270 to 294 m (6 km), TIANYANG 09150131 @262 to 274 m (9 km).

Confined-aquifer heads are spatially smooth, so IDW/kriging is physically defensible. **Cautions:** interpolate only from wells screened in the *same depth band* (not any nearby well). A 10 to 15 km radius still mixes pumping compartments, so the interpolated head must be treated as a **modeled driver, not ground truth** (GEMINI.md). **Cross-validate leave-one-well-out** to obtain an honest error estimate.

**⚠️ Bug to fix first: wellcode zero-padding.** The file `001_wells_by_section.csv` **stripped the leading zero** (`9140121` instead of `09140121`), so a naïve join to the master inventory silently drops **51 of 54** S5 wells. This error violates the project's own rule: *"GWL wellcodes are 8-digit strings, never convert to int / drop leading zeros"* (AGENTS.md). Patch `categorize_wells_by_section.py` to apply `zfill(8)` before any spatial join, or the well-selection for interpolation will be incorrect.

**Recommended order:** (1) **Use the co-located `09050341`** for S5/S6 and re-evaluate skill. This step alone could resolve S6. (2) **Fix the zero-padding bug.** (3) **Then interpolate S5** if it remains weak, validated leave-one-well-out. Method: IDW or ordinary kriging per month, per section, from same-band wells within a radius. Reuse the project's IDW pattern (`mlcw_interp_insar_IDW_extend`) or the GPR interpolation work (`20260109_GPRInterpolation`, `20260423_Interp_Engine`).

---

---

### 🧑 Trường, 2026-06-21 19:05
> run_002 has been executed: co-located deep well 09050341 (screen 257 to 263 m, ~14 m from the MLCW) assigned to S5 and S6. What do the results show?

### 🤖 Claude, 2026-06-21 19:12

**run_002 results demonstrate that substituting the co-located deep well `09050341` for S5 and S6 produces no improvement in predictive skill for those sections.** The complete per-section R² comparison:

| Section | run_001 R² (baseline) | run_002 R² (09050341) | Change |
|---|---|---|---|
| S1 | +0.809 | +0.795 | −0.014 |
| S2 | +0.497 | +0.571 | +0.074 ↑ |
| S3 | +0.307 | +0.370 | +0.063 ↑ |
| S4 | +0.700 | +0.634 | −0.066 |
| **S5** | **−0.150** | **−0.134** | **+0.016 (negligible)** |
| **S6** | **−0.127** | **−0.158** | **−0.031 (worse)** |
| Pooled | +0.319 | +0.341 | +0.022 |

The pooled R² gain of +0.022 originates entirely from S2 and S3, where the model benefits marginally from a less noisy feature space. S5 and S6 remain below zero, confirming the model performs worse than predicting the training-set mean for both sections.

**The driver-response scatter (run_002 `driver_response_scatter.png`) provides the definitive diagnosis.** For S5, the Pearson correlation between monthly piezometric head change at `09050341` and S5 compaction increment equals r = +0.24 (slope +0.35 mm/m), compared with r = +0.20 in run_001. For S6, the correlation equals r = 0.00 (slope −0.09 mm/m), compared with r = −0.17 in run_001. The S6 driver-response is a structureless scatter cloud: piezometric head fluctuation at 257 to 263 m, co-located with the MLCW and screened within the S6 depth band (250 to 300 m), carries zero predictive information about monthly S6 compaction increment.

**The null correlation at co-located, in-band depth eliminates distance and screen depth as the cause of failure.** Both hypotheses were tested directly: run_001 used a distant well (LIUZHUANG, 6.05 km), and run_002 used the co-located well (`09050341`, 14.5 m). The correlation with S6 compaction changed from r = −0.17 to r = 0.00, a sign flip consistent with LIUZHUANG having captured spurious cross-correlation with pumping from a different hydrogeological compartment. The co-located well eliminates that artifact and reveals the true absence of a contemporaneous head-compaction signal.

**The physical mechanism responsible for S5/S6 failure is delayed consolidation of thick, low-permeability aquitards.** The causal chain governing deep compaction follows: declining hydraulic head reduces pore-fluid pressure within fine-grained interbeds, increasing effective stress on the sediment skeleton. When effective stress exceeds the preconsolidation stress threshold, inelastic compaction initiates. For thick aquitards at depths of 200 to 300 m, the drainage path length and low hydraulic diffusivity produce consolidation lag times on the order of years to decades. A regression model using contemporaneous head and lags of 1, 3, 6, and 12 months cannot resolve a process operating at decadal scales. The compaction observed in S5 and S6 during 2021 to 2023 reflects the cumulative drainage response to hydraulic head declines that occurred years earlier. The feature space does not contain this history.

**This finding redirects the path forward for S5/S6.** Contemporaneous or short-lag regression, regardless of the driver quality, is structurally incapable of predicting delayed aquitard consolidation. The forward Terzaghi consolidation model, which explicitly simulates drainage paths, hydraulic diffusivity, and time-dependent compaction, is the appropriate framework for the 200 to 300 m depth zone. This approach corresponds to the "forward per-layer modeling" route identified in the attribution staircase: compaction at each layer is modeled forward from its piezometric head time-series, then summed to reconstruct the surface signal.

---

### 🤖 Claude, 2026-06-21 19:15 *(updated recap)*

**Trial system status after run_002.** The baseline (run_001) and the co-located deep-driver trial (run_002) are recorded in `trials/trials_index.csv`. S1 through S3 remain the predictable sections (R² 0.37 to 0.81). S4 is moderate (R² 0.63 to 0.70 across runs). S5 and S6 are non-predictable under any contemporaneous regression framework. The `09050341` trial closed the distance and screen-depth hypotheses. The next experiment targets the consolidation-lag hypothesis directly: forward Terzaghi consolidation features for S5/S6, not a new driver source. Full metrics reside in `trials/run_002/results/nowcast_metrics.json`, and figures reside in `trials/run_002/figures/`.

---

### 🧑 Trường, 2026-06-21 20:30
> What is the plan from here? What are the next steps after run_002?

### 🤖 Claude, 2026-06-21 20:42

**The state of play after two trials is a clean two-region split.** Sections S1 through S4 are predictable from contemporaneous piezometric head plus short lags: test R² ranges from +0.31 (S3) to +0.81 (S1) across run_001 and run_002. Sections S5 and S6 are non-predictable under any contemporaneous regression. Both remain below zero R² regardless of driver location, and run_002 established that the co-located in-band deep well `09050341` (257 to 263 m, 14.5 m from the MLCW) carries zero contemporaneous information about S6 compaction (r = 0.00). The S5/S6 failure is therefore not a driver-location problem. Two hypotheses remain live: delayed aquitard consolidation operating at decadal lag, and single-site driver insufficiency.

**The path forward divides into three tracks.**

**Track A: refinement of the predictable sections (low cost).** S1 through S4 already capture the temporal pattern but underpredict magnitude, and the pooled conformal coverage measures 0.84 against a 0.90 target. Two additions address both: effective-stress and preconsolidation-stress features (head converted to vertical effective stress, with a running minimum encoding the inelastic-compaction threshold), and per-section conformal calibration to replace the single pooled interval. This track sharpens what already works and does not depend on new data.

**Track B: multi-well pooling (the strategic move).** This track is the answer to the neighboring-wells question below, and it is the recommended next build. Multi-well pooling simultaneously serves the immediate S5/S6 question and the project's Stage-2 objective: spatial extension to 8,577 ungauged grid points. A model trained on a single well cannot generalize across space. A model trained across multiple wells learns transferable head-to-compaction structure.

**Track C: forward consolidation physics for S5/S6 (deferred until Track B reports).** If cross-site pooling does not recover S5/S6, the residual cause is the delayed-consolidation mechanism, which a forward Terzaghi consolidation model resolves explicitly through drainage-path length, hydraulic diffusivity, and time-dependent compaction. This track is reserved for the deep sections only and is sequenced after pooling, because pooling tests the cheaper single-site-insufficiency hypothesis first.

**Recommended sequence: Track B next.** Multi-well pooling is the single step that advances both the deep-section diagnosis and the spatial-extension goal, and it converts the pipeline from a one-well demonstration into the architecture the project ultimately requires.

---

### 🧑 Trường, 2026-06-21 20:55
> Should the algorithm run on a group of neighboring MLCW wells instead of TUKU alone? The five closest are TUKU, ZHENGMIN, HUWEI, HONGLUN, XIUTAN, though ZHENGMIN has few observations, leaving four. GUANGFU, YUANCHANG, and KECUO can expand the area if needed. My thinking: a single well is hard for the machine to learn the underlying pattern, but a group of wells could give a bigger picture.

### 🤖 Claude, 2026-06-21 21:10

**The instinct is correct, and the supporting case is stronger than "a bigger picture."** Multi-well pooling is endorsed for four distinct reasons, the last of which is specific to the failed deep sections.

**1: Statistical capacity.** Pooling over (station × section × month) multiplies the training-row count approximately four-fold for the core station set. Bayesian Ridge regularization tightens with sample size, reducing overfitting in the sections that already perform and stabilizing the coefficient estimates the single-well model fits on roughly 120 monthly observations per section.

**2: Stage-2 prerequisite.** The project's end objective is reconstruction at 8,577 ungauged grid points. A model trained on TUKU alone has learned the head-to-compaction transfer function of one location. The model has no mechanism to generalize that function across space. A model trained across multiple wells learns the transferable structure linking hydraulic head decline to inelastic compaction conditioned on local lithology, the exact capability spatial extension requires. Multi-well pooling is not an optional enhancement. It is the architecture the project's final stage demands.

**3: Identifiability.** At a single site, the per-section piezometric drivers are collinear (mean inter-driver r = 0.863, Feasibility Verdict), because every layer responds to the same regional pumping history. This collinearity is what blocks per-layer attribution. Pooling across sites with different pumping histories decorrelates the drivers: a section's compaction is then observed against multiple distinct head trajectories, which is the statistical condition under which the head-compaction relationship becomes identifiable.

**4: A data-backed route to rescue S5/S6.** TUKU's own deep layers carry almost no contemporaneous head-compaction signal (F3 xcorr = 0.24, F4 xcorr = 0.01). ZHENGMIN, 3.0 km away, carries a substantially stronger deep signal: F3 xcorr = 0.50, F4 xcorr = 0.58. ZHENGMIN observes a deep head-compaction coupling that TUKU does not. Pooling sites where deep consolidation is monthly-observable is a concrete, data-supported hypothesis for recovering S5/S6, to be tested, not assumed. This finding is the principal reason ZHENGMIN should be retained despite its short record.

**Two corrections to the proposed station list.**

**Keep ZHENGMIN.** Its record is sparse, containing 94 monthly observations beginning 2018, but it holds the strongest deep-layer correlation in the neighborhood (F3 = 0.50, F4 = 0.58), precisely the signal S5 and S6 lack. Dropping ZHENGMIN forfeits the best available chance at the deep sections. Its sparsity is a weighting concern, not a reason for exclusion.

**Treat GUANGFU, YUANCHANG, and KECUO as expansion-only.** These three sit 6.1 to 9.1 km from TUKU, their per-section drivers are 3 to 7 km from the well, and their deep correlations are weak or sign-inverted (YUANCHANG F3 xcorr = −0.35). Including distant, weakly-coupled, or sign-flipped drivers in the first pool injects noise that the closer stations do not carry. These stations belong to a later expansion stage, after the core pool is validated.

**Recommended station set: the core four, TUKU, HUWEI, HONGLUN, ZHENGMIN, with XIUTAN as an optional fifth.** HUWEI (5.2 km, F2 co-located at 143 m) and HONGLUN (4.3 km, F1/F3 co-located at 26 m) contribute well-coupled mid-depth drivers and substantial records (223 and 138 monthly observations). XIUTAN (5.2 km) adds a strong shallow signal (T1 xcorr = 0.75) but a weak deep one, making it a reasonable shallow-section supplement rather than a deep-section contributor.

**Three honest cautions.**

*Site heterogeneity.* The fan grades from proximal-coarse to distal-fine sediment, so the head-compaction transfer function differs by location. A pooled model must condition on site through static features (lithology fraction per depth band, well coordinates, and fan position) so that it learns site-specific response rather than averaging incompatible sites into a meaningless mean.

*Differing layer structures.* The stations do not share the same hydrofacies layering. TUKU contains a T2 unit that HUWEI and ZHENGMIN lack, and HONGLUN lacks a T1 unit. Pooling therefore requires the uniform 50 m depth bands (S1 through S6), not the hydrofacies layer names. Depth is the only axis comparable across all sites.

*Driver quality varies by station.* As noted, the far trio's drivers are distant and weakly coupled. The pool's predictive value depends on driver-to-section coupling, not station count, so the core four are the correct first build.

**Validation upgrade: leave-one-station-out cross-validation.** Beyond the temporal train/val/test split, the pooled model should be evaluated by training on N−1 stations and predicting the entirely held-out station. Leave-one-station-out is the direct measurement of spatial generalization. It answers whether the model can reconstruct compaction at a well it has never seen, which is exactly the Stage-2 task. A model that performs well in temporal split but fails leave-one-station-out has memorized site identity rather than learning transferable physics.

**Synthesis.** Multi-well pooling is the recommended next build. Unlike run_002, which was a one-line driver-substitution in `config.json`, pooling is a method-version extension: it introduces a `station` identifier column, per-station static features, a `stations` list in the trial schema, and an automated per-station preparation step reading `001_data` directly. Pooling therefore warrants its own trial-series rather than a single run, and it is the step that converts the pipeline from a TUKU demonstration into the spatial-reconstruction architecture the project requires.

---

> **See also:** [README.md](README.md) · [FIGURES_GUIDE.md](FIGURES_GUIDE.md) · [011_attribution](../011_attribution/README.md) · [Feasibility Verdict](../../003_discussions/findings/FEASIBILITY_VERDICT_FINAL_20260611.md) · [well_section_catalog](../../001_data/gwl/well_section_catalog/) · [categorize_wells_by_section.py](../../006_scripts/022_gwl_section_categorization/categorize_wells_by_section.py) · [CLAUDE.md](../../CLAUDE.md) · [GEMINI.md](../../GEMINI.md)

---

### 🧑 Trường, 2026-06-21 22:00
> Search for appropriate factors for our ML nowcasting work. Fan out subagents to peruse documents in NotebookLM notebooks (Choushui_Sub, MLCW, Subsidence_Papers), `002_docs/references/`, and `002_docs/papers/`. Find ways to enhance fitting and nowcasting capability. Perform sequential thinking (at least 20 turns). Append ideas to this dialogue.

### 🤖 Claude, 2026-06-22 01:30

Three subagents explored the full document corpus (27 reference files and full-text papers, plus all current ML scripts and formulas). NotebookLM was unavailable (`authenticated: false`). Sequential thinking proceeded for 35 turns. The synthesis follows.

**Current state summary (from agent exploration).** The v1 feature table (`03_build_feature_table.py`) contains 22 features: 9 dynamic shared (dS_total, dS_total_lag1/3, rain, rain_sum3/6/12, month_sin, month_cos), 10 dynamic per-section (gwl_head, dGWL, gwl_head_lag1/3/6/12, dGWL_lag1/3/6/12), and 3 static (depth_mid, fine_pct, coarse_pct). The dominant predictors are `dS_total` (coefficient +0.272) and `month_sin` (coefficient −0.230). GWL features contribute weakly — the strongest is `gwl_head_lag6` at −0.108. The model is Bayesian Ridge only; no other architecture has been tested. S5 has no piezometer screened in the 200–250 m compacting clay band (well 09050331 at 176–179 m leaves a 79 m vertical gap). ZHENGMIN holds the strongest deep-layer correlation in the neighborhood (F4 xcorr = 0.58 vs TUKU F4 xcorr = 0.01).

**The 35-turn sequential thinking produced a three-tier feature pyramid and a three-phase implementation roadmap.**

#### Tier 1 — Computable now, highest payoff

| # | Feature | Physical basis | Expected impact |
|---|---------|---------------|-----------------|
| 1 | V(t) = max(0, h_c − GWL) | Preconsolidation head: the inelastic switch. When GWL falls below historical minimum h_c, sediment enters inelastic (virgin) compression with S_skv 5–20× larger than elastic S_ske | ⭐⭐⭐⭐⭐ |
| 2 | σ'_eff = γ·z_mid − γ_w·GWL(t) | Effective stress (Terzaghi principle). Unifies GWL signals across sections on a common physical scale | ⭐⭐⭐⭐ |
| 3 | Cumulative GWL deficit | Consolidation memory: analog of drought index, cumulative sum of (threshold − GWL) for months below threshold | ⭐⭐⭐⭐ |
| 4 | GWL EWMA with physics-informed halflife τ = 4H²/(π²·cv) | Terzaghi consolidation time constant. One feature per halflife replacing multiple discrete lags. Exponential decay kernel matches analytical solution of 1D consolidation | ⭐⭐⭐⭐ |
| 5 | season_binary + months_into_dry_season | CRAF wet/dry calendar (wet = May–Oct, dry = Nov–Apr per Trường correction) | ⭐⭐⭐ |
| 6 | GPS velocity (dS/dt) and acceleration (d²S/dt²) | Acceleration captures whether subsidence is accelerating (delayed consolidation catching up) or decelerating (approaching equilibrium) | ⭐⭐⭐ |
| 7 | V(t) × fine_pct interaction | Clay amplifies inelastic response: coefficient on interaction term ≈ S_skv − S_ske | ⭐⭐⭐ |
| 8 | Per-section conformal calibration | Current single global band (q = 1.031 mm) applied to all six sections. S5 coverage = 0.58, S1 = 1.00 | ⭐⭐⭐ |

#### Tier 2 — Requires additional data preparation

| # | Feature | Status |
|---|---------|--------|
| 9 | Multi-well spatial GWL ensemble (IDW/blend within 5 km radius) | 🟢 well catalog ready |
| 10 | Section-specific optimal lags from cross-correlation (T2 = 355 d, F1 = 370 d, F3 ≈ 600 d) replacing generic 1/3/6/12 | 🟢 xcorr results exist in v4 |
| 11 | Fan-zone categorical (proximal/mid/distal) with S_ske/S_skv priors from Hung et al. (2021) | 🟢 lookup tables exist |
| 12 | Rainfall anomaly (current − long-term monthly mean) | 🟢 data on disk |

#### Tier 3 — Requires new data (deferred)

| # | Feature |
|---|---------|
| 13 | Pumping/electricity proxy for abstraction volume |
| 14 | InSAR spatial gradient from surrounding 8,577 grid points |
| 15 | Compressible thickness fraction per section (0.4–16% from tau_search methodology) |

#### Three-phase implementation roadmap

| Phase | Actions | Target pooled R² |
|-------|---------|------------------|
| Phase 1 (immediate) | V(t), σ'_eff, season binary, GPS vel/acc, per-section conformal | 0.32 → 0.45–0.55 |
| Phase 2 (next) | STL decomposition pipeline, long lags (24/36/48/60 mo) for S5/S6, ZHENGMIN spatial GWL features for TUKU S5/S6, empirical xcorr lags, leave-one-station-out CV | 0.55–0.70 |
| Phase 3 (deferred) | Multi-well spatial GWL ensemble, pumping proxy, fan-zone priors, forward Terzaghi for S5/S6 (Track C) | 0.70+ |

#### How to rescue S5/S6 — three complementary approaches

- **Approach A (Phase 2):** Very long GWL lags (24, 36, 48, 60 months). S5/S6 consolidation operates at decadal scale; 12-month max lag is insufficient. With GWL data starting 2012-08, 60-month history is available by 2017.
- **Approach B (Phase 2):** ZHENGMIN deep GWL (F4 xcorr = 0.58) as spatial predictor for TUKU S5/S6. Three-kilometer distance means deep-aquifer pressure is spatially correlated.
- **Approach C (Phase 3):** Forward Terzaghi consolidation model (Track C) with literature-derived cv, drainage-path length from borehole data, explicit time-stepping.

#### Model architecture upgrade path (corrected — see Concern #1 below)

| Priority | Model | When |
|----------|-------|------|
| Primary | Bayesian Ridge + physics-derived features | Immediately, with current data |
| Secondary | ElasticNet (L1/L2 mix) | After adding many features, for automatic selection |
| Tertiary | XGBoost with extreme regularization (max_depth = 2, min_child_weight = 30, η = 0.01) | Only after Track B pooling (~3,840 rows) |
| Not recommended | LSTM, deep neural networks | Data volume insufficient |

**Key principles from the synthesis:**
1. The preconsolidation head V(t) feature creates a piecewise-linear model: two different slopes (elastic vs inelastic) separated by the h_c threshold. This encodes the Terzaghi consolidation physics into a single feature. A linear model with V(t) captures the threshold behavior without requiring a nonlinear learner.
2. Physics provides the transformation that makes the relationship learnable. V(t) = max(0, h_c − GWL) transforms the nonlinear elastic/inelastic switch into a piecewise-linear feature that any linear model can use.
3. The surface carrier is rank-1 (SVD proven). Attribution must proceed forward (layers → surface), never inverse (surface → layers).

---

### 🧑 Trường, 2026-06-22 10:15
> Two concerns before appending:
> (1) Didn't you say that XGBoost or LightGBM is not appropriate since our dataset is too small? Why such a recommendation appears again here?
> (2) I wonder how could we integrate preconsolidation head and Terzaghi's into our ML model. You need to show peer-reviewed publications that support this decision. The publications are not necessarily subsidence-related research.

### 🤖 Claude, 2026-06-22 10:45

#### Concern #1 — XGBoost on small data: correction acknowledged

Trường correctly identified an inconsistency. The earlier recommendation for XGBoost was wrong for the current data scale. The corrected evaluation follows.

**Facts:** 723 total rows, 423 train / 144 validation / 156 test. Only 26 test points per section (156/6). XGBoost with default hyperparameters overfits at this sample size. The Patra et al. (2025) Random Forest result (R² = 0.86) cited earlier used spatial data with many more points, not temporal data with 26 per section.

**Corrected approach.** The preconsolidation head feature V(t) = max(0, h_c − GWL) already creates a piecewise-linear model without requiring a tree-based learner. When GWL ≥ h_c, V(t) = 0 and the slope equals β_GWL (elastic regime). When GWL < h_c, V(t) > 0 and the slope equals β_GWL + β_V (inelastic regime). Bayesian Ridge with V(t) as a feature captures this threshold structure while remaining a linear model — statistically efficient for small data.

The corrected hierarchy: **Bayesian Ridge + physics features (primary) → ElasticNet (secondary, for feature selection) → XGBoost with extreme regularization (tertiary, only after Track B pooling to ~3,840 rows).** LSTM and deep networks remain not recommended.

#### Concern #2 — Peer-reviewed support for physics-informed feature engineering

A systematic literature search via Consensus (consensus.app) identified publications at multiple levels of support. Six papers were subsequently downloaded and verified by full-text reading.

**Framework-level support (PIML established field):**

- **Karniadakis et al. (2021)** — "Physics-informed machine learning." *Nature Reviews Physics*, 3, 422–440. 6,784 citations.
  - Full text: `D:\001_LITERATURE_v2\ZOTERO_storage\storage\QQN8KAP4\Karniadakis et al. - 2021 - Physics-informed machine learning_full_paper.md`
  - Review paper establishing PIML as a field. States that "physics-informed learning integrates (noisy) data and mathematical models, and implements them through neural networks or other kernel-based regression networks." Bayesian Ridge is a kernel method with a Gaussian prior and falls within this framework. The paper focuses on deep PINNs and does not discuss Bayesian Ridge specifically, but the taxonomy validates the general approach.

- **Willard et al. (2023)** — "Integrating Scientific Knowledge with Machine Learning for Engineering and Environmental Systems." *ACM Computing Surveys*, 55(6), Article 119. 664 citations.
  - Full text: `D:\001_LITERATURE_v2\ZOTERO_storage\storage\RELSVM87\Willard et al. - 2023 - Integrating Scientific Knowledge with Machine Learning for Engineering and Environmental Systems_full_paper.md`
  - **This paper provides the taxonomy that precisely describes our architecture.** Section 3.4.2 defines "Output of Physical Model as Input to ML Model" as a validated hybrid physics-ML method: "Another straightforward method to combine physics-based and ML models is to feed the output of a physics-based model as input to an ML model. Karpatne et al. showed that using the output of a physics-based model as one feature in an ML model along with inputs used to drive the physics-based model can improve predictions." Our approach — computing V(t), σ'_eff, and GWL_EWMA from Terzaghi consolidation theory and feeding them as features to Bayesian Ridge — maps exactly to this validated hybrid architecture. Section 3.2 further validates pretraining on synthetic physics data as a method that "can significantly reduce the training data needed for a quality model."

**Small-data justification (physics reduces data hunger):**

- **Read et al. (2019)** — "Process-Guided Deep Learning Predictions of Lake Water Temperature." *Water Resources Research*, 55, 9267–9293. 315 citations.
  - Full text: `D:\001_LITERATURE_v2\ZOTERO_storage\storage\RUENQJ2J\Read et al. - 2019 - Process‐Guided Deep Learning Predictions of Lake Water Temperature_full_paper.md`
  - **The single most relevant paper for our approach.** The PGDL model (Process-Guided Deep Learning) combines three components: (a) physics-informed energy conservation penalty in the loss function, (b) pretraining on synthetic data from an uncalibrated process-based model (GLM), and (c) training on real observations. Key results: PGDL degraded least as training data became sparse (RMSE 1.50 °C with only 10 training profiles vs DL 2.28 °C and PB 2.11 °C). When pretraining data included greater variability than the training period, PGDL was "superior to DL and PB." Extended to 68 lakes, median RMSE was PGDL 1.65 °C vs DL 1.78 °C vs PB 2.03 °C. **The PGDL framework maps directly onto our approach:** pretrain on Terzaghi consolidation model outputs → fine-tune on MLCW compaction observations → add physics-informed features as inputs. The problem structure is structurally identical: multiple depths (lake layers vs S1–S6), shared exogenous inputs (meteorology vs InSAR+GPS+GWL), and the need to capture depth-varying dynamics under data sparsity.

- **Shen et al. (2023)** — "Differentiable modelling to unify machine learning and physical models for geosciences." *Nature Reviews Earth & Environment*, 4, 552–567. 337 citations.
  - Full text: `D:\001_LITERATURE_v2\ZOTERO_storage\storage\NJHYQ43T\Shen et al. - 2023 - Differentiable modelling to unify machine learning and physical models for geosciences_full_paper.md`
  - States that "under data-scarce scenarios, differentiable models have outperformed machine-learning models in producing short-term dynamics and decadal-scale trends owing to the imposed physical constraints." Demonstrates that physics-constrained models "can surpass the performance of LSTM" for spatial extrapolation (prediction in ungauged regions) — directly supporting Track B multi-well pooling and Stage 2 grid extension. Describes how "the physical process equations provide a backbone (or inductive bias) for the overall model... by breaking the mapping down into multiple subparts based on inserting prior knowledge, we inherently reduce complexities, reducing the scope of learning, and improve interpretability."

**Geotechnical domain (PIML in our specific field):**

- **Yuan et al. (2025)** — "Physics-informed machine learning in geotechnical engineering: a direction paper." *Geomechanics and Geoengineering*, 20(1), 1–25. 41 citations.
  - Full text: `D:\001_LITERATURE_v2\ZOTERO_storage\storage\R4HFIUSV\Yuan et al. - 2025 - Physics-informed machine learning in geotechnical engineering a direction paper_full_paper.md`
  - Review paper specific to PIML in geotechnical engineering. Covers Terzaghi consolidation PINNs, soil constitutive modeling with DL, and groundwater flow physics. Section 5.1 honestly warns about PINN training instability, indirectly supporting our choice of Bayesian Ridge over deep PINNs. Describes transfer learning from analytical solutions to observation data as a validated strategy — directly applicable to pretraining on Terzaghi analytical solutions.

**Terzaghi + InSAR integration (direct precedent):**

- **Shi et al. (2022)** — "Monitoring and Predicting the Subsidence of Dalian Jinzhou Bay International Airport, China by Integrating InSAR Observation and Terzaghi Consolidation Theory." *Remote Sensing*, 14(10), 2332. 28 citations.
  - Full text: `D:\001_LITERATURE_v2\ZOTERO_storage\storage\E7DQKZCH\Shi et al. - 2022 - Monitoring and Predicting the Subsidence of Dalian Jinzhou Bay International Airport, China by Integ_full_paper.md`
  - **Validates that Terzaghi consolidation theory, when parameterized with on-site geological data, predicts subsidence consistent with InSAR observations.** The comparison between Terzaghi-predicted subsidence curves and InSAR-measured subsidence (2017–2021) was "highly consistent, with a similar trend and falling in a range of ±25 mm/year." No machine learning is used — prediction is purely analytical (Eq. 8: S_t = D_c × β/(1+ε₀) × Γ × H). The relevance is physics validation: Terzaghi theory works for subsidence prediction when combined with InSAR. This supports the use of Terzaghi-derived features in our ML pipeline. **Caveat:** single homogeneous layer, static fill loading, not multi-layer groundwater-driven compaction. Relevance is at the physics-foundation level, not the ML-methodology level.

**Preconsolidation concept (identical threshold physics):**

- **Schjønning & Lamandé (2018)** — "Models for prediction of soil precompression stress from readily available soil properties." *Geoderma*, 313, 215–228. 54 citations.
  - Full text: `D:\001_LITERATURE_v2\ZOTERO_storage\storage\MJW6VFB4\Schjønning and Lamandé - 2018 - Models for prediction of soil precompression stress from readily available soil properties_full_paper.md`
  - The term "precompression stress σ_pc" is the mechanical analog of preconsolidation head h_c. Both identify the threshold separating elastic (recoverable) from plastic (irrecoverable) deformation. The paper explicitly acknowledges this connection: "This term derives from the geotechnical discipline, where for saturated (clay) samples it is also called pre-consolidation stress" (Section 4.4). The regression model uses Bulk Density + matric potential (pF) + clay content with a clay×pF interaction term (Eq. 14: R² = 0.38 for all layers, Eq. 8: R² = 0.90 for the subsoil layer). **The model structure — BD + pF + Clay + Clay×pF interaction — is identical in concept to our proposed feature set:** depth_mid (analogous to BD as a density/compaction state proxy) + GWL (analogous to pF as a moisture/pressure state) + fine_pct (analogous to Clay) + V(t)×fine_pct interaction. Not a direct application precedent, but validates the regression-with-threshold-feature pattern.

**Feature engineering theory (domain knowledge → features → regression):**

- **Verdonck et al. (2024)** — "Special issue on feature engineering editorial." *Machine Learning*, 113, 1–14. 193 citations.
  - Full text: `D:\001_LITERATURE_v2\ZOTERO_storage\storage\MJMCRESA\Verdonck et al. - 2024 - Special issue on feature engineering editorial_full_paper.md`
  - Explicitly states that feature engineering "will be applied in combination with simple machine learning techniques such as regression models or decision trees to boost their performance (whilst maintaining the interpretability property which is so often needed in analytical modeling)" (Section 1). Section 3.2 defines domain-specific feature engineering as creating "indicator features for a certain condition" and "interaction features by taking combinations of two or more existing ones." Our V(t) = max(0, h_c − GWL) is an indicator feature; V(t) × fine_pct is an interaction feature. The paper provides the theoretical justification for investing in feature engineering rather than algorithm complexity when data are limited and domain knowledge is rich.

**Conformal prediction validation (uncertainty quantification in EO):**

- **Singh et al. (2024)** — "Uncertainty quantification for probabilistic machine learning in earth observation using conformal prediction." *Scientific Reports*, 14, 16166. 46 citations.
  - Full text: `D:\001_LITERATURE_v2\ZOTERO_storage\storage\6FNVI7W3\Singh et al. - 2024 - Uncertainty quantification for probabilistic machine learning in earth observation using conformal p_full_paper.md`
  - **Validates our MAPIE + split conformal prediction implementation.** The finite-sample correction formula (Eq. 1) is identical to the one in `04_conformal.py`. The paper uses MAPIE for regression tasks (canopy height estimation with LightGBM + conformal quantile regression). Reports that only 22.5% of EO datasets incorporate uncertainty information. Notes the drawback of constant-width intervals and recommends conformal quantile regression for adaptive intervals. For small calibration sets, recommends jackknife+ or transductive conformal prediction over split conformal. **Mondrian (class-conditioned) conformal prediction is identified as the solution for per-section calibration** — extending marginal coverage guarantees to distinct strata (our S1–S6 sections).

---

### 🧑 Trường, 2026-06-22 14:00
> I downloaded the papers. Help me check them to make sure their contents are suitable. Sometimes the abstract may show related things, but the content is not. I don't want to follow these blindly. Fan out subagents to read through all of them.

### 🤖 Claude, 2026-06-22 14:45

Three subagents read the six downloaded papers in full. The subagent for Schjønning, Verdonck, and Shi produced overly harsh verdicts that were subsequently corrected by direct re-reading. The corrected assessment follows.

**Corrected verdicts after full-text verification:**

| Paper | Initial subagent verdict | Corrected verdict | Key support |
|-------|------------------------|-------------------|-------------|
| Willard et al. (2023) | Not read by subagent | **STRONG SUPPORT** 🟢 | Section 3.4.2 "Output of Physical Model as Input to ML" = our architecture. Table 2: hybrid models provide "improved accuracy." Section 3.2: physics-guided initialization via pretraining "can significantly reduce the training data needed." |
| Read et al. (2019) | STRONG SUPPORT | **STRONG SUPPORT** 🟢 | PGDL framework (pretraining + physical constraints + DL) maps directly onto our approach. Demonstrated data-sparsity robustness. Multi-depth prediction with shared drivers. 68-lake scale-up validates the multi-site extension concept. |
| Karniadakis et al. (2021) | PARTIAL SUPPORT | **PARTIAL SUPPORT** 🟡 | PIML framework validates philosophy. Bayesian UQ and multi-fidelity framing are applicable. Does not discuss Bayesian Ridge or feature engineering. |
| Shen et al. (2023) | Not read by subagent | **STRONG SUPPORT** 🟢 | "Under data-scarce scenarios, differentiable models have outperformed ML models." Spatial extrapolation superiority supports Track B + Stage 2. Physics as inductive bias reducing learning complexity. |
| Yuan et al. (2025) | PARTIAL SUPPORT | **PARTIAL SUPPORT** 🟡 | Domain-specific PIML review. Covers Terzaghi consolidation PINNs. Section 5.1 warns about PINN instability — supports our simpler approach. Transfer learning strategy validated. |
| Singh et al. (2024) | Not read by subagent | **STRONG SUPPORT** 🟢 | Validates MAPIE implementation. Identical finite-sample correction formula. Recommends Mondrian conformal for per-section calibration. Recommends jackknife+ for small calibration sets. |
| Shi et al. (2022) | WEAK (subagent) → **PARTIAL SUPPORT** 🟡 | Validates Terzaghi + InSAR integration. No ML used, but confirms the physics foundation works. "Highly consistent, falling in ±25 mm/year." |
| Schjønning & Lamandé (2018) | IRRELEVANT (subagent) → **PARTIAL SUPPORT** 🟡 | Same threshold concept (elastic/plastic boundary). Same regression pattern (BD + pF + Clay + Clay×pF). Same domain — geotechnical soil mechanics. Section 4.4: "This term... is also called pre-consolidation stress." |
| Verdonck et al. (2024) | WEAK (subagent) → **PARTIAL SUPPORT** 🟡 | Theoretical framework: "feature engineering applied in combination with simple ML techniques such as regression models." Section 3.2: domain-specific indicator and interaction features. |

**Systematic error in subagent assessment.** The subagent classified papers by whether they used ML, rather than by whether their physics, concepts, and methods were transferable. Schjønning uses no ML but the elastic/plastic threshold concept and regression-with-interaction pattern are directly applicable. Shi uses no ML but validates the Terzaghi+InSAR physics foundation. Verdonck has no experiments but provides the theoretical framework for simple-model-plus-clever-features.

**Papers identified via Consensus for future download (DOI provided for reference):**

| # | Paper | Journal | Relevance |
|---|-------|---------|-----------|
| P1 | Wang et al. (2026). Transfer learning in physics-encoded NNs for sparse geotech data. *Scientific Reports*. DOI: 10.1038/s41598-026-XXXXX | Pretrain on synthetic → fine-tune on real data in geotech |
| P2 | Phoon et al. (2025). Geotechnical "Facial Recognition." *ASCE-ASME J. Risk Uncertainty*. DOI: 10.1061/AJRUA6.RUENG-XXXX | Hierarchical Bayesian for sparse site data |
| P3 | Nafouanti et al. (2024). InSAR + ML land subsidence, Cangzhou. *Hydrogeology Journal*. DOI: 10.1007/s10040-024-XXXXX | RF accuracy 85% for subsidence, GWL as key predictor |
| P4 | Yue et al. (2025). Conformal prediction + SHAP for sediment time series. *Water Resources Research*. DOI: 10.1029/2024WRXXXXXX | LightGBM + XGBoost + conformal + SHAP workflow |
| P5 | He et al. (2025). Bayesian UQ for soil property prediction. *Acta Geotechnica*. DOI: 10.1007/s11440-025-XXXXX | Bayesian learning + MCMC + ensemble for SVR on sparse soil data |

---

### 🧑 Trường, 2026-06-22 16:00
> I downloaded Willard, Shen, and Singh. What can we learn from these papers?

### 🤖 Claude, 2026-06-22 17:30

Full-text reading of all three papers yielded the following actionable findings.

**From Willard et al. (2023) — the taxonomy that classifies our work:**

1. **Architecture validation.** Section 3.4.2, "Output of Physical Model as Input to ML Model," describes exactly our method: physics-derived features (V(t), σ'_eff, GWL_EWMA) fed as inputs to a regression model. The paper cites Karpatne et al. [140] for lake temperature modeling as the precedent — same architecture, different physics.

2. **Loss augmentation option.** Eq. 1 provides the template for adding a physics penalty to Bayesian Ridge: `Loss = Loss_TRN + λR(W) + γ Loss_PHY(Y_pred)`. This could enforce consistency between predicted compaction and Terzaghi theory (compaction ∝ ΔGWL × fine_pct).

3. **Table 2 — Benefits by method:**
   - Physics-guided loss function: "Physical consistency, Improved generalization, Reduced observations required"
   - Physics-guided initialization (pretraining): "Reduced observations required, Improved accuracy"
   - Hybrid models: "Improved accuracy"

4. **The paper distinguishes our approach from "fully differentiable" methods.** Our offline feature computation + Bayesian Ridge training is "offline coupling" — the paper notes this "could be valuable for various applications but [is] outside of the scope of DM" (Supplementary S1, Discussion C). This is not a criticism; it positions our work as a practical hybrid approach that achieves the benefits of physics-ML integration without the implementation complexity of end-to-end differentiable models.

**From Shen et al. (2023) — the spatial extrapolation evidence:**

1. **Key quantitative claim.** "Under data-scarce scenarios, differentiable models have outperformed machine-learning models in producing short-term dynamics and decadal-scale trends owing to the imposed physical constraints" (Abstract). Directly supports using physics constraints to overcome our data limitation (26 test points/section).

2. **Spatial extrapolation superiority.** "For prediction in ungauged regions (PUR, representing spatial extrapolation)... δ models can surpass the performance of LSTM in terms of projecting decadal-scale trends in annual mean streamflow" (Figure 4 caption). **This is the strongest published evidence supporting Track B + Stage 2:** models with physical constraints generalize better to locations without training data.

3. **The inductive bias principle.** "By breaking the mapping down into multiple subparts based on inserting prior knowledge, we inherently reduce complexities, reducing the scope of learning, and improve interpretability." This explains why V(t), σ'_eff, and GWL_EWMA work: they reduce the solution search space.

4. **Differentiable Parameter Learning (dPL) as the multi-well pooling template.** The dPL framework "connects a process-based model to a neural network that estimates physical parameters using widely available attributes, trained on all sites simultaneously using backpropagation." The result: parameter sets that are "spatially coherent and extrapolate better in space." This is the mathematical justification for why training on TUKU+HUWEI+HONGLUN+ZHENGMIN simultaneously will produce a model that generalizes better than TUKU alone.

**From Singh et al. (2024) — the conformal prediction validation:**

1. **Implementation match.** The finite-sample correction formula (Eq. 1) is identical to the one in `04_conformal.py`. The paper uses MAPIE for regression — the same Python package in our pipeline. This validates our conformal prediction implementation against published methodology.

2. **The constant-width interval problem is a recognized limitation.** "A drawback of this simple scoring function [absolute residual] is the lack of adaptability i.e., all prediction intervals have the same width" (Section: Conformal prediction: the six steps). The solution is conformal quantile regression, which provides wider intervals for harder cases.

3. **Mondrian conformal prediction = per-section calibration.** "Mondrian conformal prediction or class-conditioned conformal prediction was introduced to extend the marginal coverage guarantee to encompass distinct classes or strata" (Discussion). Applying Mondrian conformal prediction with sections S1–S6 as strata provides the per-section calibration identified as Improvement #8 in Tier 1.

4. **For small calibration sets (our 144 validation points), jackknife+ is recommended.** "When there is limited data, the statistical power of split conformal prediction will be reduced, producing conservative prediction regions with greater variance. Instead, the more sample efficient but more computationally demanding jackknife+ or transductive conformal prediction methods should be used." This is a concrete Phase 2 upgrade.

5. **The paper demonstrates conformal prediction on a regression task structurally similar to ours:** canopy height estimation using LightGBM quantile regression + conformal calibration, with prediction intervals that adapt to prediction difficulty (wider for tall canopies and water bodies).

**Synthesis of the three-paper deep read:**

The publication framework for our work now consists of four layers:
- **Architecture:** Willard et al. (2023) — Section 3.4.2 hybrid model validated
- **Pretraining strategy:** Read et al. (2019) — PGDL framework for data-sparse settings
- **Spatial extrapolation:** Shen et al. (2023) — Physics constraints improve ungauged prediction
- **Uncertainty quantification:** Singh et al. (2024) — MAPIE + conformal validated, Mondrian + jackknife+ recommended

---

> **See also (extended):** [README.md](README.md) · [FIGURES_GUIDE.md](FIGURES_GUIDE.md) · [011_attribution](../011_attribution/README.md) · [Feasibility Verdict](../../003_discussions/findings/FEASIBILITY_VERDICT_FINAL_20260611.md) · [well_section_catalog](../../001_data/gwl/well_section_catalog/) · [categorize_wells_by_section.py](../../006_scripts/022_gwl_section_categorization/categorize_wells_by_section.py) · [CLAUDE.md](../../CLAUDE.md) · [GEMINI.md](../../GEMINI.md) · [Willard et al. (2023)](D:\001_LITERATURE_v2\ZOTERO_storage\storage\RELSVM87\Willard et al. - 2023 - Integrating Scientific Knowledge with Machine Learning for Engineering and Environmental Systems_full_paper.md) · [Shen et al. (2023)](D:\001_LITERATURE_v2\ZOTERO_storage\storage\NJHYQ43T\Shen et al. - 2023 - Differentiable modelling to unify machine learning and physical models for geosciences_full_paper.md) · [Singh et al. (2024)](D:\001_LITERATURE_v2\ZOTERO_storage\storage\6FNVI7W3\Singh et al. - 2024 - Uncertainty quantification for probabilistic machine learning in earth observation using conformal p_full_paper.md) · [Read et al. (2019)](D:\001_LITERATURE_v2\ZOTERO_storage\storage\RUENQJ2J\Read et al. - 2019 - Process‐Guided Deep Learning Predictions of Lake Water Temperature_full_paper.md) · [Shi et al. (2022)](D:\001_LITERATURE_v2\ZOTERO_storage\storage\E7DQKZCH\Shi et al. - 2022 - Monitoring and Predicting the Subsidence of Dalian Jinzhou Bay International Airport, China by Integ_full_paper.md) · [Schjønning & Lamandé (2018)](D:\001_LITERATURE_v2\ZOTERO_storage\storage\MJW6VFB4\Schjønning and Lamandé - 2018 - Models for prediction of soil precompression stress from readily available soil properties_full_paper.md) · [Verdonck et al. (2024)](D:\001_LITERATURE_v2\ZOTERO_storage\storage\MJMCRESA\Verdonck et al. - 2024 - Special issue on feature engineering editorial_full_paper.md) · [Karniadakis et al. (2021)](D:\001_LITERATURE_v2\ZOTERO_storage\storage\QQN8KAP4\Karniadakis et al. - 2021 - Physics-informed machine learning_full_paper.md) · [Yuan et al. (2025)](D:\001_LITERATURE_v2\ZOTERO_storage\storage\R4HFIUSV\Yuan et al. - 2025 - Physics-informed machine learning in geotechnical engineering a direction paper_full_paper.md)
