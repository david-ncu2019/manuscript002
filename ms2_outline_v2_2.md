# Manuscript Outline (v2.2)

> Generated: 2026-08-04 from /grill-me interview.
> Changes from v2.1: Restructured Sections 3–4 and Appendix based on the decision to switch from Split-Conformal to Bayesian Ridge native uncertainty.

---

- **1 Introduction**
  [NOTE: Draft-quality for now. Requires extensive literature review and citations. Should briefly justify the choice of Bayesian Ridge Regression as the modeling approach — the detailed algorithm explanation goes in Section 3.2.]

- **2 Study Area and Datasets** [LOCKED — do not edit]
  - 2.1 Study Area Background
  - 2.2 Datasets
    - 2.2.1 Multilayer aquifer-system compaction
    - 2.2.2 Groundwater level observations
    - 2.2.3 Vertical surface displacement
    - 2.2.4 Borehole lithological profile

- **3 Methodology**
  - 3.1 Preparation of model inputs [LOCKED — do not edit]
    - 3.1.1 Deformation time series model
    - 3.1.2 Isometric logratio transformation of sediment composition
    - 3.1.3 Assembly of monthly model inputs

  - 3.2 Bayesian ridge regression [REWRITE]
    [NOTE: Focus on explaining the algorithm clearly and accessibly, following scikit-learn documentation (Pedregosa et al., 2011) and the sklearn.linear_model.BayesianRidge API page. The opening paragraph briefly recalls why BRR was chosen (detailed justification lives in Introduction). The main body explains the model formulation: likelihood, prior, posterior update of α and λ, and the posterior mean as the point estimate.]

  - 3.3 Predictive uncertainty quantification [NEW — replaces old §3.3.2 "Prediction intervals"]
    [NOTE: Explain how BRR's posterior predictive distribution provides a standard deviation (σ_pred) for every prediction. The 90% prediction interval is ŷ ± 1.645 · σ_pred. Keep language simple and non-technical: frame it as "the model's own estimate of how uncertain each prediction is." No Split-Conformal content here — that is archived.]

  - 3.4 Experimental design [NEW — replaces old §3.3]
    [NOTE: Address the reviewer question regarding train/test/validation splitting here. Explain why a traditional random split is invalid for time-series forecasting due to future-to-past data leakage. Justify the use of Walk-Forward Validation (rolling origin) as the strictly correct, temporally consistent evaluation framework.]
    - 3.4.1 Delayed data delivery (primary evaluation)
      [NOTE: Recreates 6-month gaps where MLCW observations are temporarily unavailable. GWL and cGNSS remain available. At the end of each 6-month block, all 6 monthly MLCW records arrive and are used to evaluate and retrain. Walk-forward validation. This subsection corresponds to the existing run_048 P0/level1a pipeline.]
    - 3.4.2 Reduced measurement frequency (sensitivity analysis)
      [NOTE: Simulates MLCW measurements collected every N months (N = 6 and N = 12). Monthly GWL and cGNSS remain available. Scripts for this scenario are under development. Merge the N=6 and N=12 cases into one subsection.]

- **4 Results and discussion**
  - 4.1 Overall nowcasting performance
    [NOTE: R², RMSE, MAE by section (S1–S6). Show that the model predicts layerwise compaction from inexpensive, densely available inputs (GWL + cGNSS). Report all sections S1–S6 honestly — do not preemptively discuss S5/S6 limitations unless reviewers ask. Include a short paragraph or table showing the proportion of observations that fell within the predicted uncertainty range, using plain language (avoid jargon like "empirical coverage" or "nominal coverage").]
  - 4.2 Performance over the 6-month evaluation gap
    [NOTE: How does accuracy change from month h=1 to h=6 within each evaluation block? Critical evidence that the delayed-delivery scenario remains viable even at h=6.]
  - 4.3 Sensitivity to reduced MLCW measurement frequency
    [NOTE: Merged discussion of N=6 and N=12 scenarios in one subsection. Show whether the model remains useful when direct MLCW observations are collected less often.]
  - 4.4 Predictor group contributions
    [NOTE: Standardized coefficients grouped by predictor category (GWL lags, cGNSS displacement, seasonal harmonics, ILR composition, interactions). Uses existing run_048 coefficient bar charts. Frame as evidence that the model captures physically meaningful relationships, not a black-box fit.]

- **5 Conclusions**
  [NOTE: Recap the objective (predicting layerwise subsurface deformation from cheaper, denser data sources), summarize data and methodology used, state whether results support the framework's viability, and note key limitations and future directions.]

- **A Supplementary methodological details** [CREATE appendix002.tex — replaces old appendix001.tex]
  - A.1 Final predictor inventory
  - A.2 Model fitting and update settings
  - ~~A.3 Prediction interval calibration (Split-Conformal)~~ [ARCHIVED — moved to appendix001.tex for reference only]
  - + A.3 Bayesian predictive uncertainty derivation [NEW — details of posterior predictive variance from BayesianRidge]
  - A.4 Reduced-frequency MLCW measurement settings

---

## Source Data Inventory for Manuscript Writing

> **Base path**: `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast`
> All paths below are relative to this base.

### Documentation & Context (read first)

| File | Purpose |
|---|---|
| `README.md` | Pipeline overview, baseline history, station/section definitions |
| `RULES.md` | Naming conventions, depth section rules, data conventions |
| `docs/20260701_ML_features_v4.md` | Official feature inventory (v4 baseline) |
| `docs/20260711_ML_features_v4_extended.md` | Extended feature inventory with run_048 additions |
| `docs/20260728_run048_manuscript_evidence.md` | Manuscript evidence handoff document |
| `docs/20260802_run048_tuku_no_update_sensitivity_manuscript_handoff.md` | Sensitivity analysis handoff for manuscript |
| `docs/FIGURES_GUIDE.md` | Guide to all figure types and their generation scripts |
| `experiments/section_pooled/run_048_output_instructions_en.md` | Detailed explanation of run_048 output structure |

### Section 3.2 — Bayesian ridge regression

| File | Purpose |
|---|---|
| `scripts/05_train_nowcast.py` | Core training script — contains `BayesianRidge` fitting logic |
| `scripts/trial_config.py` | Model configuration and hyperparameter settings |
| `scripts/run048_feature_registry.py` | Feature registry defining all predictor groups |
| `scripts/brr_feature_profiles.py` | Feature profile definitions per run |

### Section 3.3 — Predictive uncertainty quantification

| File | Purpose |
|---|---|
| `scripts/05_train_nowcast.py` | Will need modification to add `predict(return_std=True)` |
| `scripts/04_conformal.py` | **ARCHIVED** — Split-Conformal implementation (reference only) |

### Section 3.4.1 — Delayed data delivery (primary evaluation)

| File | Purpose |
|---|---|
| `scripts/run048_pipeline.py` | Full-period walk-forward evaluation pipeline |
| `scripts/run048_evaluation.py` | Evaluation metrics computation |
| `scripts/run048_manuscript_results001.py` | Manuscript results extraction & conformal calibration |
| `experiments/section_pooled/run_048/checkpoints/` | Frozen checkpoint data for all profile/level combinations |
| `experiments/section_pooled/run_048/results/predictions.parquet` | All predictions across all folds |
| `experiments/section_pooled/run_048/results/fold_metrics.parquet` | Per-fold performance metrics |
| `experiments/section_pooled/run_048/results/summary_metrics.json` | Aggregated performance summary |
| `experiments/section_pooled/run_048/results/standardized_coefficients.parquet` | Coefficient values for all folds |

### Section 3.4.2 — Reduced measurement frequency (sensitivity analysis)

> **⚠️ NOT YET DEVELOPED.** No scripts or results exist for this scenario.
> This experiment simulates MLCW measurements collected every N months (N=6, N=12),
> where the model receives ONE cumulative observation at each endpoint and uses it to update.
> Scripts need to be written from scratch.

### Section 4.1 — Overall nowcasting performance

| File | Purpose |
|---|---|
| `experiments/section_pooled/run_048/supplements/manuscript_results001/results/performance_by_section.csv` | R², RMSE, MAE per section |
| `experiments/section_pooled/run_048/supplements/manuscript_results001/results/narrative_scalars.json` | Key scalar values for prose |
| `experiments/section_pooled/run_048/supplements/manuscript_results001/P0_level1a/prediction_outputs/P0_TUKU_level1a_S*_obs_vs_pred.png` | Observed-vs-predicted time series (6 sections) |
| `experiments/section_pooled/run_048/supplements/manuscript_results001/P0_level1a/prediction_outputs/P0_TUKU_level1a_S*_prediction_vs_actual.png` | Scatter plots (6 sections) |
| `experiments/section_pooled/run_048/supplements/manuscript_results001/P0_level1a/prediction_outputs/P0_TUKU_level1a_fold_timeline.png` | Fold timeline overview |
| `experiments/section_pooled/run_048/supplements/manuscript_results001/P0_level1b/figures/TUKU_section_timeseries.png` | Combined 6-section time series (single figure) |

### Section 4.2 — Performance over the 6-month gap

| File | Purpose |
|---|---|
| `experiments/section_pooled/run_048/results/fold_metrics.parquet` | Metrics grouped by h (month within block) |
| `experiments/section_pooled/run_048/supplements/tuku_no_update_sensitivity/results/metrics_per_section.parquet` | Per-section metrics at each horizon (no-update variant) |
| `experiments/section_pooled/run_048/supplements/tuku_no_update_sensitivity/results/summary_metrics.json` | H=6 vs H=12 no-refit summary |
| `experiments/section_pooled/run_048/supplements/tuku_no_update_sensitivity/results/predictions_h6.parquet` | No-refit predictions over 6-month horizon |
| `experiments/section_pooled/run_048/supplements/tuku_no_update_sensitivity/results/predictions_h12.parquet` | No-refit predictions over 12-month horizon |
| `experiments/section_pooled/run_048/supplements/tuku_no_update_sensitivity/figures/TUKU_h6_vs_h12_normalized_mae.png` | Normalized MAE: H=6 vs H=12 no-refit comparison |

### Section 4.3 — Sensitivity to reduced MLCW frequency

> **⚠️ NOT YET DEVELOPED.** Results depend on new scripts from §3.4.2.

### Section 4.4 — Predictor group contributions

| File | Purpose |
|---|---|
| `experiments/section_pooled/run_048/results/standardized_coefficients.parquet` | Raw coefficient data |
| `experiments/section_pooled/run_048/supplements/manuscript_results001/P0_level1a/model_parameters_coefficients/fitting_parameters/P0_TUKU_level1a_S*_fitting_parameters.png` | BRR α/λ evolution plots (6 sections) |
| `experiments/section_pooled/run_048/supplements/manuscript_results001/P0_level1a/model_parameters_coefficients/driving_features/P0_TUKU_level1a_S*_top_driving_features_*.png` | Top driving features bar charts (18 files: 6 sections × 3 pages) |

### Appendix A — Supplementary details

| File | Purpose |
|---|---|
| `scripts/run048_feature_registry.py` | Complete predictor list for A.1 |
| `scripts/trial_config.py` | Fitting settings for A.2 |
| `scripts/run048_tuku_no_update_sensitivity.py` | Sensitivity design parameters for A.4 |
