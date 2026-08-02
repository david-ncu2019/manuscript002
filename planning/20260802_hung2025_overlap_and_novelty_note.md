# Hung et al. (2025): Overlap and Novelty Note

**Recorded:** 2026-08-02 00:04:17 +08:00  
**Purpose:** Preserve the distinction between Hung et al. (2025) and the reduced Tuku manuscript during later drafting and analysis.

## Overall Assessment

The two studies overlap substantially in study location, monitoring context, and broad operational motivation, but they do not address the same prediction problem. The manuscript is not a duplicate of Hung et al. (2025), although the overlap may appear strong if its contribution is described only as AI-based or near-real-time subsidence forecasting.

## Closest Prior Study

Hung et al. (2025), *Near real-time subsidence monitoring and AI forecasting with multi-depth extensometers*, studied the Tuku area in the Choushui River Alluvial Fan. The study used high-frequency automated extensometer records at selected depths as the main forecasting data, applied Prophet to forecast short-term displacement, and used MLCW, GNSS, groundwater level, and leveling observations as supporting information.

## Distinction of This Manuscript

The reduced manuscript estimates monthly compaction within six standardized 50 m depth sections at one MLCW station. MLCW compaction increments are the response used for calibration and evaluation. Groundwater level changes, cGNSS vertical displacement, and borehole lithological composition provide the predictor information; previous MLCW measurements are not model inputs. Bayesian ridge regression is used to estimate section-level compaction rather than to forecast the future value of an extensometer series.

The intended scientific question is:

> Can monthly compaction within individual depth sections be estimated from hydraulic head changes, vertical surface displacement, and lithological information when direct MLCW observations become less frequent?

## Framing Requirements

- Cite Hung et al. (2025) as the closest site-specific prior study and state the distinction directly.
- Avoid presenting the manuscript broadly as "near-real-time AI forecasting."
- Use **monthly compaction estimation** or **nowcasting** when predictors from the target month are used. Use **forecasting** only when all predictors precede the target month.
- Emphasize depth-resolved MLCW compaction as the target and the absence of direct compaction measurements from the predictor set.
- Do not claim reliability under reduced MLCW sampling solely from aggregated errors produced by the existing monthly-update model.
- Support the reduced-sampling claim with a no-update sensitivity analysis in which the model predicts continuously for 6 or 12 months without receiving MLCW observations or being refitted within the evaluation window.
- Keep the reduced-sampling analysis separate from statistical confidence or prediction-interval coverage unless each quantity is evaluated explicitly.

## Draft Consistency Check

The current `sections/dataset003.tex` and `sections/methods004.tex` describe an approximately six-month delay in MLCW data delivery. This wording does not represent the later study direction in which direct MLCW sampling is reduced to once every 6 or 12 months. Revise both sections after the reduced-sampling experiment and evaluation protocol are frozen.

## Source Files

- Closest paper: `D:\001_LITERATURE_v2\ZOTERO_storage\storage\GFDMNS9S\Hung et al. - 2025 - Near real-time subsidence monitoring and AI forecasting with multi-depth extensometers_full_paper.md`
- Dataset draft: `D:\112_PROJECT_002\Manuscript_reduced\sections\dataset003.tex`
- Methods draft: `D:\112_PROJECT_002\Manuscript_reduced\sections\methods004.tex`

