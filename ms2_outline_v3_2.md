# Manuscript Outline (v3.2) — Per-Section Bayesian Ridge Regression

This outline describes the intended content of each section and subsection.
**Internal experiment labels (P0, P3, level1a, level1b, level1c, run_028, run_035, run_048, cross-section, own-section) must not appear in manuscript text.** The manuscript describes methodology and results using physical and data-oriented language only.

[NOTE: To the assistant writing the prose: Keep your sentences direct. State the conclusion first, followed by the supporting evidence. Do not use generic filler phrases like "It can be seen that" or "Generally speaking". Let the physical mechanisms drive the explanation.]

> **Governing decision:** Each depth section is modelled independently by its own Bayesian ridge regression. Predictors include hydraulic head changes observed at the target section's screened interval, head changes observed at other monitored depth intervals, vertical surface displacement, and seasonal terms. The manuscript reports walk-forward evaluation at the Tuku station.

**What changed in v3.2:** §4 Results and §5 Discussion are merged into one section, `§4 Results and Discussion`, with five subsections (4.1–4.5). Each subsection states its claim, its supporting evidence/numbers, and its physical interpretation together, in that order, in the same paragraph — interpretation never appears before the number that justifies it. This replaces v3.1's separate Results (§4) / Discussion (§5) split; no other structural change from v3.1. Conclusions is now §5, Appendix is still §A.

Two experiments still sit at equal priority as the manuscript's critical path, both unbuilt for the per-section modelling design:
1. **Blocker #1** — sensitivity to reduced MLCW measurement frequency (every 6 or 12 months), §3.3.3 / §4.3 / A.4.
2. **Blocker #2** — sensitivity to permanent monitoring stoppage: fit the model once on 3, 5, or 8 years of training data, then predict with no refit and no further MLCW input, to see how estimation error grows over that horizon. See §3.3.4 / §4.4 / A.5.

Neither blocker has a script yet under the per-section design. The closest precedent for both is the existing no-update sensitivity analysis, built for the earlier pooled design — see the note under §3.3.4 for the exact handoff document.

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

[NOTE: Not yet ready to draft with real numbers. The per-section walk-forward table for this modelling design has not been assembled yet — only unaggregated per-fold results exist. See D:\112_PROJECT_002\discussions\20260805_outline_v2_4_section_to_codebase_map.md for detail.]

##### 3.3.2 Prediction intervals
Presents the 90% Bayesian predictive interval derived from the posterior predictive variance.

##### 3.3.3 Sensitivity to less frequent MLCW measurements
Describes the experimental scenarios: observing total compaction every 6 or 12 months.

[NOTE: Explain that this sensitivity analysis directly tests an operational reality (budget-driven sampling reduction) rather than just mathematical robustness.]

[NOTE: Not yet ready to draft with real numbers. **Blocker #1.** No reduced-frequency run exists yet for this modelling design — only a full-monitoring-stoppage analysis exists, and it was built for a different (pooled) modelling design. See D:\112_PROJECT_002\discussions\20260805_outline_v2_4_section_to_codebase_map.md for detail.]

##### 3.3.4 Sensitivity to permanent monitoring stoppage
Describes a second experimental scenario, distinct from §3.3.3: the model is fit once, using 3, 5, or 8 years of training data, and then generates predictions with no refit and no further MLCW input for the remainder of the record. This tests what happens if a station stops reporting MLCW measurements permanently, rather than on a fixed reduced schedule.

[NOTE: Explain that this scenario answers a different operational question than §3.3.3. §3.3.3 asks "how much can sampling be thinned while still checking in periodically?" §3.3.4 asks "if a station goes dark for good after 3, 5, or 8 years, how far does the estimate drift before it becomes unusable?"]

[NOTE: Not yet ready to draft with real numbers. **Blocker #2**, equal priority to Blocker #1 above. No script exists yet for this scenario under the per-section modelling design. Follow the same experimental precedent as the existing no-update sensitivity handoff at `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\docs\20260802_run048_tuku_no_update_sensitivity_manuscript_handoff.md` — that document's design (fit once, predict a fixed horizon with no refit, measure cumulative endpoint error) was built for the pooled model at 6- and 12-month horizons. This scenario needs the equivalent design built for the per-section BRR model, extended to 3-, 5-, and 8-year horizons. See D:\112_PROJECT_002\discussions\20260805_outline_v2_4_section_to_codebase_map.md for further detail.]

---

### 4 Results and Discussion
*(Proposed content: merged into results002.tex; discuss002.tex retired from this section's build)*

[NOTE: The writing tone here must be that of an operational advisor. Acknowledge that the physical monitoring network is degrading, and explain how the model helps decision-makers navigate this limitation without covering up physical gaps. Every claim below states its number first, then its physical interpretation immediately after, in the same paragraph — never interpretation before the number that justifies it.]

##### 4.1 Overall nowcasting performance and depth-dependence
**Claim:** the per-section model nowcasts monthly compaction with section-level accuracy that varies systematically with depth, and its 90% Bayesian predictive interval gives decision-makers a usable, quantified measure of uncertainty without requiring a separately archived historical test set.

**Evidence:** the evaluation blocks, observed compaction range, and section-level metrics ($R^2$, RMSE, MAE) for all six depth sections (S1–S6). Report the metrics fairly for every section, including the near-zero or negative $R^2$ at S5 (200–250 m) stated plainly alongside the other five sections. Alongside the performance metrics, report the empirical coverage and width of the posterior predictive interval, per section.

**Interpretation (same subsection, immediately following the numbers):** S5's weak performance traces to a physical observability gap, not a modelling failure. No piezometer is screened within its compacting fine-grained deposits, so the head-change predictor available for that section is an imprecise proxy for the pore-pressure conditions actually driving compaction there. Frame this as a "Network Warning": machine learning cannot invent physics if observability is strictly zero. If decision-makers remove sensors from actively compacting layers, the ability to nowcast is permanently lost. For the prediction intervals, frame their availability as "from day one" of deployment at a new or resumed station, in contrast to methods that need an accumulated error archive before they can quantify uncertainty at all.

[NOTE: State the S5 physical explanation exactly once. Do not restate the S5 reasoning a second time elsewhere in this subsection or in §4.5 Limitations.]
[NOTE: Also state, where the numbers support it, that the primary value of the model is bridging the data-release delay: timely monthly estimates allow regulators to implement pumping restrictions before irreversible inelastic compaction accumulates. Distinguish this explicitly from long-term forecasting — the model relies on contemporaneous, same-month drivers.]
[NOTE: Not yet ready to draft with final numbers. Table 3 cannot be filled until §3.3.1's per-section walk-forward table exists; the direction of the weakest section (S5, strongly negative) is already known, but the full six-section table is not. See D:\112_PROJECT_002\discussions\20260805_outline_v2_4_section_to_codebase_map.md for detail.]

##### 4.2 Coefficients of driving factors at each section
**Claim:** the predictors that drive the nowcast differ by depth section, and identifying which factor dominates where explains the physical mechanism behind each section's compaction behavior.

**Evidence:** Bayesian ridge regression coefficients (posterior mean plus credible interval) for every predictor, per depth section (S1–S6) — cGNSS displacement, target-section hydraulic head, other-section hydraulic head, and seasonal terms. Report which predictor group dominates at each section, alongside a table or figure ranking driving factors by their standardized coefficient magnitude.

**Interpretation (same subsection):** explain which physical mechanism each dominant predictor represents at each section (e.g., a section whose compaction is driven mainly by its own hydraulic head behaves differently from one driven mainly by cross-section head changes or by seasonal terms), and connect this to the depth-dependent performance pattern already established in §4.1.

##### 4.3 Sensitivity to reduced-frequency measurements
**Claim:** reducing MLCW check-in frequency from monthly to every 6 or 12 months is an operationally real trade-off, not just a mathematical robustness test.

**Evidence:** monthly and endpoint errors under the 6-month and 12-month interval scenarios, consolidated into one table comparing endpoint errors between the two schedules, per depth section and combined across the profile.

**Interpretation (same subsection):** present the data as a trade-off curve between field-visit cost and estimation uncertainty. Synthesize directly into the operational framing: this is a tool for the Water Resources Agency (WRA) to decide how much they can safely reduce sampling frequency without blinding themselves to critical subsidence events.

[NOTE: Not yet ready to draft with real numbers. **Depends on Blocker #1** (§3.3.3), which has no scenario runs yet for this modelling design. See D:\112_PROJECT_002\discussions\20260805_outline_v2_4_section_to_codebase_map.md for detail.]

##### 4.4 Sensitivity to permanent monitoring stoppage
**Claim:** this asks a different operational question than §4.3. §4.3 asks "how thin can periodic sampling go while still checking in?" This subsection asks "if a station goes dark for good, how far does the estimate drift before it stops being usable?"

**Evidence:** cumulative estimation error growth over the 3-, 5-, and 8-year no-refit horizons, per depth section and for the complete monitored profile. Report cumulative endpoint error (MAE, RMSE, bias, in mm) at each horizon, plus horizon-normalized error (mm/month) reported alongside — never in place of — the absolute cumulative error.

**Interpretation (same subsection):** state plainly whether the model degrades gracefully or fails sharply past some horizon, once the numbers exist, framed as a WRA decision-support question: how long can this station go unmonitored before its estimate can no longer support a pumping-restriction decision?

[NOTE: The physically relevant quantity for an operator deciding how long a station can go unread is the absolute cumulative endpoint error, not the horizon-normalized rate — the normalized rate can fall even as absolute error grows, from partial cancellation, per the same caution documented in the no-update sensitivity handoff. Never report the normalized rate as a standalone headline number.]
[NOTE: Not yet ready to draft with real numbers. **Depends on Blocker #2** (§3.3.4), equal priority to Blocker #1. No script exists yet under the per-section modelling design. The closest precedent is the no-update sensitivity handoff built for the pooled model at 6-/12-month horizons (`D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\docs\20260802_run048_tuku_no_update_sensitivity_manuscript_handoff.md`), which needs the equivalent built for the per-section BRR model, extended to 3-/5-/8-year horizons. See D:\112_PROJECT_002\discussions\20260805_outline_v2_4_section_to_codebase_map.md for detail.]

##### 4.5 Limitations and practical scope
**Claim:** the fitted model is strictly local to Tuku's specific lithology, well configuration, and stress history; only the methodology, not the fitted coefficients, is transferable.

**Interpretation only (no new evidence introduced here):** prevents overclaiming. State explicitly that while the methodology is fully transferable, the specific fitted coefficients cannot be copy-pasted to another station.

---

### 5 Conclusions

Restate the operational objective (nowcasting layer-specific compaction under delayed/degraded data delivery). Summarize the data sources and the Bayesian method.

[ADD: Deliver the principal conclusion: The approach successfully bridges temporal data gaps in well-monitored sections, offering an operational trade-off for budget-constrained networks, but it cannot overcome fundamental physical blind spots where sensors are missing.]

[NOTE: Match the prose STYLE (not the content or methodology) of the following papers when drafting this conclusion:
- Hung et al. (2025), "Near real-time subsidence monitoring and AI forecasting with multi-depth extensometers" — `D:\001_LITERATURE_v2\ZOTERO_storage\storage\GFDMNS9S\`
- Liu et al. (2025), "Deep learning time-series modeling for assessing land subsidence under reduced groundwater use" — `D:\001_LITERATURE_v2\ZOTERO_storage\storage\LAML2LM8\`
- Liu et al. (2023), "Reconstructing missing time-varying land subsidence data using back propagation neural network" — `D:\001_LITERATURE_v2\ZOTERO_storage\storage\6TYF2YLR\`
- Wang et al. (2025), "A case study on the application of a data-driven (XGBoost) approach on the environmental and socio-economic..." — `D:\001_LITERATURE_v2\ZOTERO_storage\storage\BNZ9BUGJ\`
- Nguyen et al. (2024), "Quantitative Evaluations of Pumping-Induced Land Subsidence and Mitigation Strategies" — `D:\001_LITERATURE_v2\ZOTERO_storage\storage\LMTIPY87\`]

---

### A Supplementary methodological details

##### A.1 Final predictor inventory
[NOTE: A clean table of the final frozen predictors from the pipeline run. No internal experiment tags.]
[NOTE: Partially ready. The predictor list can be generated on demand from the existing pipeline logic, but no static table has been exported yet. See D:\112_PROJECT_002\discussions\20260805_outline_v2_4_section_to_codebase_map.md for detail.]

##### A.2 Model fitting and update settings
[NOTE: Record the technical configuration to guarantee reproducibility.]

##### A.3 Prediction interval calibration
[NOTE: Mathematical proof of the posterior predictive distribution, explaining why it works without an accumulated error archive.]

##### A.4 Reduced-frequency MLCW measurement settings
[NOTE: Provide the exact endpoint constraint numerical formulation used in the 6- and 12-month sparse-sampling sensitivity scenarios (§3.3.3).]
[NOTE: Not yet ready to draft with real numbers. The constraint formulation is designed but has not been run for this modelling design yet — same dependency as §3.3.3/§4.3 (Blocker #1). See D:\112_PROJECT_002\discussions\20260805_outline_v2_4_section_to_codebase_map.md for detail.]

##### A.5 Permanent-stoppage scenario settings
[NOTE: Provide the exact numerical formulation used in the 3-, 5-, and 8-year no-refit sensitivity scenarios (§3.3.4): training window lengths, horizon lengths, and the no-refit constraint.]
[NOTE: Not yet ready to draft with real numbers. No script exists for this scenario yet — same dependency as §3.3.4/§4.4 (Blocker #2). See D:\112_PROJECT_002\discussions\20260805_outline_v2_4_section_to_codebase_map.md for detail.]
