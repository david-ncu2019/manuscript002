# Literature Novelty Assessment
**Date: 2026-05-17**
**Purpose: Confirm originality of the InSAR–MLCW depth-stratified compaction attribution and transferability framework**

---

## 1. Summary of the Research

This project does three things that no published work currently combines:

1. **Derives a per-depth compaction fraction** `f̄_k = median(Y_k / x)` at each of 39 MLCW stations across the Choushui River Alluvial Fan (CRAF), where `Y_k` is the MLCW displacement at depth `k` and `x` is the co-located InSAR cumulative displacement.
2. **Interpolates these 60-level fraction profiles** to a dense 8,577-point grid, producing a 3D compaction field (depth $\times$ space $\times$ time) driven entirely by InSAR after calibration.
3. **Stress-tests the method under network degradation** — quantifying how prediction accuracy degrades as the active MLCW count drops from 39 to 19 to 5 to 0, with the goal of producing defensible Class I or Class II predictions after the network shrinks further.

---

## 2. Closest Prior Work and How It Differs

### 2.1 Hung et al. (2021) — Water Resources Research
**Citation:** Hung, W.-C., et al. (2021). Measuring and interpreting multilayer aquifer-system compactions for a sustainable groundwater-system development. *Water Resources Research*, 57, e2020WR028194. https://doi.org/10.1029/2020WR028194

**What they did:** Used MLCW at multiple CRAF stations (same study area) together with GPS, leveling, and InSAR to characterise elastic vs. inelastic compaction, estimate skeletal specific storage coefficients, and identify safe groundwater levels. The MLCW depth profiles were used for physical stress-strain analysis.

**How it differs from this project:**
- Hung et al. use MLCW to extract physical parameters (Ss_k, safe GWL threshold); this project uses MLCW to extract a dimensionless spatial field (`f̄_k`) that can be applied to future InSAR pixels without any groundwater level input.
- No fan-wide interpolation of depth profiles. MLCW are used at individual stations, not as a network whose spatial structure is leveraged.
- No transferability analysis. There is no concept of "what happens when stations shut down."
- InSAR appears as a validation check, not as the primary forward-predictor after calibration.

**Verdict:** Most relevant precedent for MLCW use in CRAF. This project cites Hung et al. as the closest prior work but extends it in all three dimensions listed in Section 1.

---

### 2.2 Azeriansyah, Ching et al. (2024) — Engineering Geology / SSRN preprint
**Citation:** Azeriansyah, R., Ching, K.-E., Lin, C.-W., Hsu, K.-C., Tsai, P.-C., Yeh, C.-L., & Rau, R.-J. (2024). Unraveling the heterogeneous hydrogeological characteristics in the Choushui River alluvial fan, Taiwan, through observations from the multi-layer compaction monitoring wells. *Engineering Geology*, doi:10.1016/j.enggeo.2024.107570.

**What they did:** Used 35 MLCWs (same CRAF network, slightly smaller set than this project's 39) plus 83 GWL monitoring wells and 4 extensometers to characterise hydrogeological heterogeneity (Yunlin vs. Changhua contrast). Proposed a seasonal-fluctuation alignment method to classify subsurface material compaction properties.

**How it differs from this project:**
- Focus is on geological classification and material characterisation, not on prediction or spatial reconstruction.
- No InSAR integration whatsoever in the analysis.
- No compaction fraction derived; no forward-prediction framework.
- No network-degradation stress test.

**Verdict:** Closest precedent for using the 35–39 station MLCW network to understand spatial heterogeneity of CRAF. This project builds on that heterogeneity insight (the fan-wide `f̄_k` field captures exactly this heterogeneity) but then does something entirely different with it: creates a predictive spatial field driven by InSAR.

---

### 2.3 Smith et al. (2021) — Hydrogeology Journal
**Citation:** Smith, R. G., Hashemi, H., Chen, J., et al. (2021). Apportioning deformation among depth intervals in an aquifer system using InSAR and head data. *Hydrogeology Journal*, 29, 2475–2486. https://doi.org/10.1007/s10040-021-02386-0

**What they did:** Integrated InSAR seasonal deformation with head measurements at multiple depth intervals (3 head-screen depths, 1 well, California) to estimate elastic skeletal storage coefficient and time delay per depth interval, then attributed total InSAR deformation to each interval.

**How it differs from this project:**
- Only 1 well, 3 depth intervals. This project has 39 stations $\times$ 60 depth levels — roughly 780$\times$ the depth-location sample count.
- Requires ongoing groundwater level head data at each depth interval to run forward. This project requires only InSAR after calibration (Class I/II objective).
- No spatial interpolation of depth profiles to unmeasured grid points.
- No network-degradation or transferability analysis.

**Verdict:** Explicitly identified in CLAUDE.md as "the floor, not the ceiling." This project exceeds Smith et al. on scale (39 vs. 1 well), resolution (60 vs. 3 depth intervals), and post-calibration independence (InSAR-only forward prediction vs. ongoing head requirement).

<div style="background-color:#e3f2fd; border-left:4px solid #1565c0; padding:10px; margin:8px 0;">

**4. Escape from the uncorrelated-head requirement (2026-05-19).**

Smith et al. explicitly required *uncorrelated* piezometric head data across depth intervals as a methodological prerequisite. The reason: their approach attributes InSAR surface deformation to specific depth intervals by matching the *timing* of head changes at each depth to surface displacement changes. If heads at two intervals are correlated (Smith's threshold: Pearson r $\ge$ 0.6), the signals are collinear and the method cannot distinguish which interval is driving how much deformation — those intervals must be merged into one. Smith et al. searched their study area for a well that met this criterion and found **only one**. In a system like CRAF, where many confined aquifer units are simultaneously depressed during drought, most wells would fail this test.

**Our method is immune to this constraint.** MLCW directly measures per-depth compaction at every epoch; depth attribution is observed, not inferred from head-timing correlations. The IHM parameters ($S_{ske}$, $S_{skv}$, $\tau$) are calibrated independently at each depth level against MLCW ground truth. Whether or not piezometric heads in adjacent aquifer units are correlated, MLCW provides a separate calibration signal at each depth — the correlation structure of head data is irrelevant to our calibration quality.

This is a fourth structural advantage over Smith et al. that should be stated explicitly in any comparison with their method.

</div>

---

### 2.4 CRAF Remote Sensing Studies (InSAR + GNSS, no MLCW depth)
**Examples:**
- Frontiers 2024 (Tsai et al.): GNSS + hydrogeological data, no MLCW depth profiles.
- MDPI Remote Sensing 2021 (multiple authors): SBAS-InSAR + GPS + leveling, no MLCW depth attribution.
- Chiayi / Yunlin monitoring studies (2008–2019 era): multi-sensor surface monitoring, MLCW used only to validate total compaction, not decomposed by depth.

**Common pattern:** InSAR used to map surface subsidence; GNSS or leveling used to validate. MLCW appears occasionally as a total-compaction validator, never as the source of a 60-level depth-fraction field.

**Verdict:** These studies confirm InSAR is routinely used in the CRAF, but none produce or spatially distribute depth-stratified compaction fractions.

---

### 2.5 Deep Learning / LSTM for InSAR Subsidence Prediction
**Examples (2023–2025):**
- *Scientific Reports* 2025: LSTM to reconstruct missing InSAR records and forecast surface subsidence trends under reduced groundwater use.
- *Scientific Reports* 2024: Modified LSTM for InSAR deformation time-series prediction.
- *GMD* 2025: CNN + PSInSAR for land subsidence interpolation in sparse data zones.
- *Frontiers Earth Science* 2024: Transformer-BiLSTM for reservoir-induced surface deformation.

**Common pattern:** All ML/DL studies predict or interpolate the InSAR **surface** time series. None predict depth-resolved compaction. None use MLCW depth profiles as training targets.

**Verdict:** The ML/DL subsidence literature has not yet addressed depth-stratified compaction prediction. The Class II LSTM architecture proposed in `opus_research_ideas_predictive_20250515.md` — which uses the MLCW 60-depth profile as the target and InSAR + GWL as inputs — would be the first such application.

---

### 2.6 Spatial Interpolation of Subsidence Parameters
**Examples:**
- Smith (2019), *WRR*: InSAR + airborne electromagnetics to estimate clay fraction at multiple locations; no interpolation of depth compaction fractions.
- Kriging of GWL fields: standard practice, but applied to head surfaces, not to compaction-fraction depth profiles.
- CNN-PSInSAR interpolation (GMD 2025): learns spatial patterns of surface subsidence; not depth-stratified.

**Verdict:** No published study interpolates a per-depth compaction fraction field (60 levels, 39 source stations) to a dense grid using any method (IDW, kriging, or ML). The variogram-transfer kriging upgrade planned for this project would be the first application of this approach.

---

## 3. Novelty Assessment

### 3.1 What is genuinely novel

| Novel element | Status in literature |
|---------------|---------------------|
| Fan-wide direct ratio `f̄_k` derived from 39 MLCW stations $\times$ 60 depth levels | Not done anywhere |
| Spatial interpolation (IDW + kriging) of the 60-level fraction profile to 8,577 grid points | Not done anywhere |
| Producing a 3D compaction field (depth $\times$ space $\times$ time) from InSAR alone after calibration | Not done anywhere |
| Network-degradation stress test (39→19→5→0 stations) with RMSE quantification | Not done anywhere |
| Class I/II/III transferability framework for depth-resolved compaction prediction | Not done anywhere |
| Walk-forward validation (2022, 2023, 2024, 2025 hold-outs) on MLCW depth profiles | Not done anywhere |

### 3.2 What builds on prior work (cite as precedent)

| Element | Prior work to cite |
|---------|--------------------|
| MLCW depth profile measurements in CRAF | Hung et al. (2021), Azeriansyah et al. (2024) |
| Depth-interval deformation apportionment using InSAR | Smith et al. (2021) — the floor |
| InSAR subsidence mapping in CRAF | Multiple CRAF RS studies (2008–2024) |
| Stress-strain characterisation, Ss estimation from MLCW | Hung et al. (2021) |
| Hydrogeological heterogeneity Yunlin vs. Changhua contrast | Azeriansyah et al. (2024) |

### 3.3 What prior work does NOT do (the gap this project fills)

The closest pair of papers is Hung et al. (2021) + Smith et al. (2021). Together they establish:
- MLCW depth profiles can characterise per-layer compaction behaviour (Hung).
- InSAR + head data can apportion surface deformation among a few depth intervals (Smith).

Neither paper, nor any combination of them, achieves:
- A model-free, data-driven compaction fraction at 60 depth levels from 39 stations.
- A spatially continuous 3D compaction field at InSAR spatial density.
- A prediction framework that operates after the MLCW network shuts down.
- A quantified degradation curve as the network shrinks.

This gap is the scientific justification for the project.

---

## 4. Overall Novelty Verdict

**The research topic is genuinely novel.** No published study has:
1. Derived depth-stratified compaction fractions from a large MLCW network (39 stations, 60 depths) via a model-free ratio method.
2. Spatially interpolated those 60-level profiles to a fan-wide grid.
3. Used the resulting field to reconstruct a 3D compaction map driven by InSAR alone.
4. Tested prediction robustness under progressive network shutdown.

The combination of scale (39 MLCW, 60 depths, 785 epochs, 8,577-point grid), the model-free direct-ratio approach, and the transferability/network-degradation stress test places this project in a position that is clearly beyond any single prior work — and beyond any direct combination of prior works.

The closest single prior work (Hung et al. 2021) is in the same study area with overlapping data, so careful differentiation in the manuscript introduction will be important. The key distinction is that Hung et al. use MLCW to extract physical parameters for groundwater management advice, while this project uses MLCW to derive a spatial predictive field that operates without MLCW after calibration.

---

## 5. Recommended Citation Strategy

**Frame Smith et al. (2021) as the methodological floor**: "Smith et al. (2021) demonstrated that InSAR can apportion surface deformation among depth intervals using co-located head data; however, their approach required 3 depth intervals at 1 well and ongoing head measurements. We extend this concept to 60 depth levels at 39 stations and eliminate the need for post-calibration head data."

**Frame Hung et al. (2021) and Azeriansyah et al. (2024) as complementary characterisation work**: "Hung et al. (2021) and Azeriansyah et al. (2024) established the hydrogeological behaviour and material properties of the CRAF MLCW network. We build on their physical understanding of the system to derive a spatially distributed, depth-resolved compaction fraction field suitable for InSAR-driven forward prediction."

**Frame CRAF InSAR studies as the spatial context**: these confirm that InSAR accurately captures CRAF surface dynamics; this project takes the next step of decomposing those dynamics vertically.

**Frame ML/DL subsidence prediction papers as the methodological parallel without depth**: "Existing deep learning approaches predict InSAR surface time series (refs); we extend this to depth-resolved compaction profiles using MLCW as training targets."

---

*This document was generated from a web literature search (2026-05-17) as a pre-submission novelty check. Formal database searches (Web of Science, Scopus) should be conducted before manuscript submission.*
