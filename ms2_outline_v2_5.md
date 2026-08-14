# Manuscript Outline (v2.4) — Per-Section Bayesian Ridge Regression

This outline describes the intended content of each section and subsection. 
**Internal experiment labels (P0, P3, level1a, level1b, level1c, run_028, run_035, run_048, cross-section, own-section) must not appear in manuscript text.** The manuscript describes methodology and results using physical and data-oriented language only.

[NOTE: To the assistant writing the prose: Keep your sentences direct. State the conclusion first, followed by the supporting evidence. Do not use generic filler phrases like "It can be seen that" or "Generally speaking". Let the physical mechanisms drive the explanation.]

> **Governing decision:** Each depth section is modelled independently by its own Bayesian ridge regression. Predictors include hydraulic head changes observed at the target section's screened interval, head changes observed at other monitored depth intervals, vertical surface displacement, and seasonal terms. The manuscript reports walk-forward evaluation at the Tuku station.

---

## 🔒 Locked sections (from v2_1.md — do not edit without explicit sign-off)

- **§1 Introduction** — draft-quality placeholder; requires literature review citations before finalising.
- **§2 Study Area and Datasets (all subsections 2.1–2.2.4)** — approved and stable.
- **§3.1 Preparation of model inputs (3.1.1–3.1.3)** — approved and stable.

---

## Section-by-section content description

### 1 Introduction
🔒 *Locked (draft quality).* 
Establishes the monitoring problem (delayed and declining MLCW records), reviews prior data-driven compaction reconstruction studies, identifies the knowledge gap, and states the study objectives.

[NOTE: The primary novelty to frame here is "Nowcasting to bridge data delays in a degrading monitoring network", not "Depth resolution".]
[ADD: Introduce the specific operational problem at CRAF: delayed or reduced manual MLCW readings prevent timely groundwater management decisions. Frame the research as an operational solution.]

---

### 2 Study Area and Datasets
🔒 *Locked.*

#### 2.1 Study Area Background
Describes the Choushui River Alluvial Fan, its multi-layered aquifer system, and the Tuku monitoring site. 

#### 2.2 Datasets
Describes the four data streams: (2.2.1) MLCW compaction increments, (2.2.2) WRA groundwater level (GWL) observations, (2.2.3) TKJS cGNSS surface displacement, and (2.2.4) Tuku borehole lithological profile.

[NOTE: Ensure §2.2.4 mentions that sediment proportions provided physical context via the Isometric Logratio (ILR) transformation, acting as a static base rather than dynamic predictors.]

---

### 3 Methodology

#### 3.1 Preparation of model inputs
🔒 *3.1.1 and deformation model content locked.*

##### 3.1.1 Deformation time series model
Presents the parametric model used to align MLCW and cGNSS observations to common monthly epochs.

##### 3.1.2 Isometric logratio transformation of sediment composition
Describes the ILR transformation of sediment proportions (gravel, coarse sand, fine sand, fine-grained deposits) to eliminate collinearity while preserving lithological context.

##### 3.1.3 Assembly of monthly model inputs
States that each depth section formed a separate calibration dataset with an independent regression model. 

[ADD: In Table 2, list the four predictor groups clearly: cGNSS displacement, Target-section hydraulic head, Other-section hydraulic head (as candidate predictors representing system-wide conditions), and Seasonal terms.]

#### 3.2 Bayesian ridge regression
Explains the selection of Bayesian ridge regression for its regularization properties when handling overlapping predictors. 

[NOTE: Clarify that the model maps statistical associations rather than replacing deterministic groundwater flow equations.]

#### 3.3 Model evaluation and uncertainty

##### 3.3.1 Evaluation with delayed MLCW data availability
Describes the walk-forward evaluation design: six-month blocks, initial calibration, and automatic refitting.

[NOTE: Not yet ready to draft with real numbers. The per-section walk-forward table for this modelling design has not been assembled yet — only unaggregated per-fold results exist. See discussions/20260805_outline_v2_4_section_to_codebase_map.md for detail.]

##### 3.3.2 Prediction intervals
Presents the 90% Bayesian predictive interval derived from the posterior predictive variance.

##### 3.3.3 Sensitivity to less frequent MLCW measurements
Describes the experimental scenarios: observing total compaction every 6 or 12 months.

[NOTE: Explain that this sensitivity analysis directly tests an operational reality (budget-driven sampling reduction) rather than just mathematical robustness.]

[NOTE: Not yet ready to draft with real numbers. No reduced-frequency run exists yet for this modelling design — only a full-monitoring-stoppage analysis exists, and it was built for a different (pooled) modelling design. See discussions/20260805_outline_v2_4_section_to_codebase_map.md for detail.]

---

### 4 Results & Discussions

1. how good nowcasting is?
2. coefficients of driving factors at each section and explain
3. if reduce sampling rate, how bad the estimation will be in different scenarios in case we refit the model with new sparse-interval observations?
4. should we try another scenario: fit the model with 3, 5, and 8 years and do not refit, how bad the estimation will be? this is for the case a station will stop sampling permanently
5. limitations and future works

---

### 6 Conclusions

sử dụng văn phong được sử dụng ở các bài dưới đây để viết kết luận. xin nhớ là sử dụng văn phong chứ không phải là sử dụng nội dung hay phương pháp:
- "D:\001_LITERATURE_v2\ZOTERO_storage\storage\GFDMNS9S\Hung et al. - 2025 - Near real-time subsidence monitoring and AI forecasting with multi-depth extensometers_full_paper.md"
- "D:\001_LITERATURE_v2\ZOTERO_storage\storage\LAML2LM8\Liu et al. - 2025 - Deep learning time-series modeling for assessing land subsidence under reduced groundwater use_full_paper.md"
- "D:\001_LITERATURE_v2\ZOTERO_storage\storage\6TYF2YLR\Liu et al. - 2023 - Reconstructing missing time-varying land subsidence data using back propagation neural network with.md"
- "D:\001_LITERATURE_v2\ZOTERO_storage\storage\BNZ9BUGJ\Wang et al. - 2025 - A case study on the application of a data-driven (XGBoost) approach on the environmental and socio-e.md"
- "D:\001_LITERATURE_v2\ZOTERO_storage\storage\LMTIPY87\Nguyen et al. - 2024 - Quantitative Evaluations of Pumping-Induced Land Subsidence and Mitigation Strategies by Integrated_full_paper.md"