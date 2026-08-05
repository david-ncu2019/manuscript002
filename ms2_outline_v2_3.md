# Manuscript Outline (v2.3) — Per-Section Bayesian Ridge Regression

This outline describes the intended content of each section and subsection. **Internal experiment labels (P0, P3, level1a, level1b, level1c, run_028, run_035, run_048, cross-section, own-section) must not appear in manuscript text** (see `domain.md` §Forbidden Terminology). The manuscript describes methodology and results using physical and data-oriented language only.

> **Governing decision:** Each depth section is modelled independently by its own Bayesian ridge regression. Predictors include hydraulic head changes observed at the target section's screened interval, head changes observed at other monitored depth intervals, vertical surface displacement, and seasonal terms. The manuscript reports walk-forward evaluation at the Tuku station.

---

## 🔒 Locked sections (from v2_1.md — do not edit without explicit sign-off)

- **§1 Introduction** — draft-quality placeholder; requires literature review citations before finalising.
- **§2 Study Area and Datasets (all subsections 2.1–2.2.4)** — approved and stable.
- **§3.1 Preparation of model inputs (3.1.1–3.1.3)** — approved and stable.

---

## Section-by-section content description

### 1 Introduction
🔒 *Locked (draft quality).* Establishes the monitoring problem (delayed and declining MLCW records), reviews prior data-driven compaction reconstruction studies, identifies the knowledge gap (no depth-resolved monthly estimation using contemporaneous hydraulic and surface displacement records during a known data delay), and states the study objectives.

**Status:** Requires additional literature citations before finalising. No structural changes planned.

---

### 2 Study Area and Datasets
🔒 *Locked.*

#### 2.1 Study Area Background
Describes the Choushui River Alluvial Fan, its multi-layered aquifer system, and the Tuku monitoring site. References the regional hydrogeological setting.

#### 2.2 Datasets

##### 2.2.1 Multilayer aquifer-system compaction
Describes the MLCW extensometer system, magnetic anchor ring measurement, deformation model fitting to common monthly epochs, partitioning into six standardised 50 m depth sections (S1–S6), and differencing to obtain monthly compaction increments.

##### 2.2.2 Groundwater level observations
Describes the WRA piezometric network (Aquifers 1–4), daily-to-monthly averaging, and differencing to obtain monthly hydraulic head changes.

##### 2.2.3 Vertical surface displacement
Describes the TKJS cGNSS station, deformation model fitting, and differencing to obtain monthly surface displacement increments.

##### 2.2.4 Borehole lithological profile
Describes the Tuku borehole log, aggregation of sediment types into six 50 m sections, and the resulting proportions of gravel, coarse sand, fine sand, and fine-grained deposits. States that these proportions provided physical context for the independent section models rather than serving as dynamic predictors.

**⚠ Open question (from alignment recommendations §4):** The current text no longer references the ILR transformation (§3.1.2 was removed in a prior edit). If the adopted model does use ILR balances as static predictors, §3.1.2 and the corresponding Table 2 row must be restored, and this paragraph must reference the transformation again. **Decision needed before finalising.**

---

### 3 Methodology

#### 3.1 Preparation of model inputs
🔒 *3.1.1 and deformation model content locked.*

##### 3.1.1 Deformation time series model
Presents the parametric model (linear + seasonal harmonics + step offsets) used to align MLCW and cGNSS observations to common monthly epochs.

##### 3.1.2 Isometric logratio transformation of sediment composition
🔒 *Was locked in v2_1.* **Currently removed** from the compiled manuscript. If the adopted model includes ILR balances among its predictors, this subsection must be restored.

##### 3.1.3 Assembly of monthly model inputs
🔒 *Was locked in v2_1; however, content has been updated in the current files.*

**Current content:** States that each depth section formed a separate calibration dataset and one independent regression model was developed for each section. Predictors described here are (1) current and lagged hydraulic head changes at the target section, (2) current and lagged cGNSS displacement increments, and (3) annual and semiannual seasonal terms.

**⚠ Conflict (from alignment recommendations §4):** The adopted model also includes hydraulic head changes from the *other five* monitored depth intervals as candidate predictors. These should be mentioned in the text and restored to Table 2 (predictor summary), but described neutrally as "included as candidate predictors" — not characterised as beneficial, because the comparison between models with and without these terms showed no consistent improvement.

**Table 2 (predictor summary) — intended final state:**

| Predictor group | Information represented | Role in the model |
|---|---|---|
| cGNSS displacement | Current and lagged vertical surface displacement increments | Described the integrated vertical response at Tuku |
| Target-section hydraulic head | Current and lagged hydraulic head changes | Described hydraulic conditions associated with the section being estimated |
| Other-section hydraulic head | Concurrent head changes in the remaining monitored depth intervals | Included as candidate predictors describing hydraulic conditions elsewhere in the monitored profile |
| Seasonal terms | Annual and semiannual variation | Represented recurring seasonal patterns |

> **Note:** "Sediment composition" and "Section and interaction terms" rows are absent. Restore "Sediment composition" only if ILR balances are confirmed as active predictors (see §3.1.2 above).

---

#### 3.2 Bayesian ridge regression
**Current content:** Explains why Bayesian ridge regression was selected (regularisation when predictors overlap), presents the likelihood and prior equations, and notes that the model describes statistical associations rather than replacing a coupled groundwater flow and compaction model.

**Intended content — no change needed.** The algorithm description follows `scikit-learn` documentation (Pedregosa et al., 2011). The rationale sentence at the beginning was updated from "single-station dataset" to "each per-section dataset" to match the independent-model design.

---

#### 3.3 Model evaluation and uncertainty

**Current content:** Introduces two evaluation conditions (delayed complete records; reduced-frequency cumulative observations) and prediction intervals.

##### 3.3.1 Evaluation with delayed MLCW data availability
Describes the walk-forward design: six-month blocks, initial calibration period, model refit at each block boundary, and performance metrics ($R^2$, RMSE, MAE). Includes the TikZ schematic of one update cycle.

**Insertable now:** `\placeholder{CONFIRM ERROR UNIT}` → **mm/month** (confirmed in alignment recommendations §7).

**Pending:** `\placeholder{INITIAL CALIBRATION START}`, `\placeholder{INITIAL CALIBRATION END}`, `\placeholder{FINAL EVALUATION MONTH}` — these depend on the final walk-forward pipeline run and cannot be filled from existing numbers.

**Content note:** The sentence "Performance was calculated by depth section and for all sections combined" should be revised. Under the independent-model design, "all sections combined" no longer has a single-model pooled interpretation. Replace with "Performance was calculated separately for each depth section" or clarify that the combined metric was computed by concatenating the six independent series for summary reporting only.

##### 3.3.2 Prediction intervals
**Current content (already rewritten):** Presents the 90% Bayesian predictive interval derived from the posterior predictive variance ($\sigma_*^2 = \alpha^{-1} + \boldsymbol{x}_*^{\mathsf{T}} \boldsymbol{\Sigma}_\beta \boldsymbol{x}_*$). Cites MacKay (1992). Discusses empirical coverage and mean interval width.

**Status:** ✅ Complete. No further changes needed.

##### 3.3.3 Sensitivity to less frequent MLCW measurements
**Current content:** Describes the six scenarios (6- or 12-month intervals × 36/60/96-month initial calibration). Explains endpoint observations, model updates, and error metrics.

**⚠ Open question (from alignment recommendations §5):** The Discussion section (§5, `discuss001.tex:33`) currently reports results from a *different* sensitivity design (Track B: single fit, zero refit over 12 months). This design answers "what happens if monitoring stops entirely" rather than "what happens if measurements continue at reduced frequency." The Track B numbers were also computed under a different model configuration. **Decision needed:** (a) re-run Track B under the adopted model, (b) add a caveat, or (c) remove the Track B passage and wait for the reduced-frequency pipeline to finish.

---

### 4 Results and discussion

**Current content:** Three subsections reporting walk-forward performance, six-month sensitivity, and twelve-month sensitivity.

##### 4.1 Monthly compaction estimation during delayed MLCW data availability
Reports the number of evaluation blocks, observed compaction range, section-level $R^2$/RMSE/MAE, and prediction interval coverage and width.

**⚠ Blocking prerequisite (from alignment recommendations §1):** No walk-forward performance table exists for the adopted model. The numbers previously in Table 3 belonged to a different model configuration. Table 3 cells are currently `\placeholder{}` — correct. **A new pipeline run is required before these can be filled.**

**Intended prose (template):**

> The delayed-data analysis contained [N] monthly estimates within [N] nonoverlapping six-month blocks. Observed monthly compaction increments ranged from [MIN] mm/month to [MAX] mm/month across the six depth sections. [1–2 sentences on depth pattern].
>
> Section-level $R^2$ ranged from \placeholder{} to \placeholder{}. Section \placeholder{} attained the smallest RMSE (\placeholder{} mm/month), whereas Section \placeholder{} attained the largest RMSE (\placeholder{} mm/month). [Reference Table 3.]
>
> [S5 explanatory sentence, per alignment recommendations §6:] The 200–250 m depth section (S5) attained a near-zero or negative $R^2$, consistent with the absence of a piezometric observation well screened within the compacting fine-grained deposits at that depth. The hydraulic head changes used as predictors for this section were therefore a physically imprecise proxy for the actual pore-pressure conditions driving compaction.
>
> The 90% Bayesian predictive intervals covered \placeholder{} to \placeholder{} of the observations across sections. [Coverage-by-month and width-by-month statements.]

##### 4.2 Sensitivity to MLCW measurements collected every six months
Reports monthly and endpoint errors under the three initial calibration periods.

**Status:** All values are `\placeholder{}`. Depends on the reduced-frequency pipeline (`sparse_interval_update`), which has not produced final numbers.

##### 4.3 Sensitivity to MLCW measurements collected every twelve months
Same structure as §4.2, for the twelve-month interval.

**v2_1 note:** The user suggested merging §4.2 and §4.3 into a single subsection and expanding the Results/Discussion with additional topics. **This restructuring has not yet been implemented.**

---

### 5 Conclusions
**Current state:** `conclusion001.tex` is commented out in `main.tex`. Not compiled.

**Intended content (per v2_1):** Restate the study objective, summarise the data sources and method, report whether the approach produced usable estimates, and state the principal conclusion. Two paragraphs maximum.

---

### Discussion (currently `discuss001.tex`)
**Current state:** `discuss001.tex` is **not included** in `main.tex`. The file exists but is not compiled into the PDF.

**⚠ Structural note (from alignment recommendations §9):** The user should confirm whether Discussion and Conclusions should be re-enabled. The Discussion contains placeholder-heavy text and the Track B passage (§5 conflict above).

**⚠ Duplicate label (from alignment recommendations §9):** `\label{subsec:discussion_reduced_sampling}` appears in both `results001.tex:15` and `discuss001.tex:27`. One must be renamed to avoid ambiguous `\Cref` targets.

**⚠ Dangling reference:** `\Cref{subsec:no_update_sensitivity}` appears in `discuss001.tex:33` but no such label exists. The nearest target is `subsec:sparse_measurement_sensitivity` in `methods004.tex:118`.

---

### A Supplementary methodological details

##### A.1 Final predictor inventory
**Status:** `\placeholder{}`. Requires the frozen predictor table from the final pipeline run. Internal experiment labels will not appear.

##### A.2 Model fitting and update settings
**Status:** `\placeholder{}`. Requires verified model settings and software environment from the final run.

##### A.3 Prediction interval calibration
**Current content (already rewritten):** Describes the Bayesian posterior predictive distribution and explains why analytical intervals are available from the first evaluation block onward.

**Status:** ✅ Complete.

##### A.4 Reduced-frequency MLCW measurement settings
**Current content:** Describes the six scenarios, endpoint observation formula, and error metrics.

**Status:** `\placeholder{}` for the endpoint-constraint numerical formulation. Depends on the frozen implementation.

---

## Summary of blocking items

| Item | Blocks | Action required |
|---|---|---|
| No walk-forward table for the adopted model | Table 3, §4.1 prose, §4.1 metrics | Run the manuscript evaluation pipeline against the adopted model's checkpoints |
| ILR predictor status unconfirmed | §2.2.4, §3.1.2, Table 2 | Confirm whether ILR balances are active predictors in the adopted model |
| Other-section hydraulic head removed from Table 2 | Table 2, §3.1.3 | Restore the row with neutral language |
| Track B profile/design mismatch | §5 Discussion (discuss001.tex:33) | User decision: re-run, add caveat, or remove |
| discuss001.tex and conclusion001.tex not compiled | §5, Conclusions | User decision: re-enable or keep disabled |
| Duplicate label `subsec:discussion_reduced_sampling` | LaTeX cross-references | Rename one instance |
| Dangling `\Cref{subsec:no_update_sensitivity}` | discuss001.tex:33 | Fix target or remove reference |
| `\placeholder{CONFIRM ERROR UNIT}` | methods004.tex:78 | Insert **mm/month** (confirmed) |
