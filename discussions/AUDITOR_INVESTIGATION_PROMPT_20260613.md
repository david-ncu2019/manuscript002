# Independent Investigator — TUKU Pilot, 2026-06-13

**Role:** External investigator. Verify claims. Find what previous teams missed.
**Repo:** `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2`
**Environment:** `fafalab2` (conda, Python 3.12)
**Python Command:** Always use `$env:PYTHONPATH=""; conda run --no-capture-output -n fafalab2 python`
**Output folder:** `tau_demo_TUKU/results/auditor_investigation_20260613/`
**Outputs required:** JSON for numbers, CSV for timeseries, PNG for patterns. Every phase writes files.

**Available packages (ALREADY INSTALLED):**
Base: `pandas numpy matplotlib scipy json os glob`
Specialized: `statsmodels`, `filterpy`, `prophet`, `pymcr`
*Note: Do not attempt to pip install; these are verified as available in the current environment.*

**Execution Strategy:**
- You are encouraged to create temporary Python scripts (e.g., `tau_demo_TUKU/seq/tmp_investigation_phaseX.py`) to execute complex logic. 
- Do not rely on inline `python -c` for multi-step algorithms.

---

## PHASE -1: Background (read-only)

Read and understand before touching any data:
- `docs/choushui_background_search.md`
- `docs/choushui_skeletal_storage_coeffs.md`
- `docs/s_ske_skv_tables.md`
- `docs/s40623-024-02019-2_summary.md`
- `docs/notebooklm_inventory.md` (notebooks Choushui_Sub, Multi-Sensor Integration, Hydrogeology_Relearn)
- `scripts/guardrails.py`
- `discussions/PHYSICS_SAFEGUARDS.md`

---

## PHASE 0: Prerequisite Verification

Verify what previous audits claimed about depth, sign conventions, and provenance.

Key files to check:
- `data/mlcw/group_byLayer_orig/TUKU_classify_table.csv`
- `data/mlcw/borehole_materials/YL_WSYL23G1_TUKU_土庫.xlsx`
- `data/gwl/well_info/gwl_allwells_flat.csv` (well 09050331)
- `tau_demo_TUKU/results/reconstruction/TUKU_*_reconstruction.csv`
- `tau_demo_TUKU/results/mlcw_observed_epoch_mask.csv`
- `data/mlcw/group_byLayer_orig/TUKU_orig_grouped.csv`

Questions to answer:
- What is the actual F3 depth range per the well manager's classify table?
- Is well 09050331 inside or outside F3?
- Are sign conventions consistent across files? (MLCW negative=compaction, GPS negative=subsidence, head never negated)
- Does the provenance mask match the original field data?

**Export:** `phase0_prerequisite_verification.json`

---

## PHASE 1: Kalman Filter

Implement a Kalman tracker for total column compaction using `filterpy`.

Data sources:
- `tau_demo_TUKU/results/seq/frozen_calibration.json`
- `tau_demo_TUKU/results/reconstruction/TUKU_F1_reconstruction.csv` (GPS surface)
- `tau_demo_TUKU/results/reconstruction/TUKU_carrier_reconstruction_summary.json` (a_k coefficients)
- `data/mlcw/group_byLayer_orig/TUKU_orig_grouped.csv` (MLCW total column = sum of F1–F4)

Key questions:
- At annual visit cadence, is the Kalman gain essentially 1.0 (hard reset)?
- At monthly cadence, does the Kalman update differ from a hard reset?
- How fast does the prediction uncertainty grow between visits?
- Does the Kalman interval provide better uncertainty quantification than static conformal bands?

**Exports:**
- `phase1_kalman_summary.json` — parameters, gains at different cadences, uncertainty growth rates
- `phase1_kalman_timeseries.csv` — state, covariance, gain, innovation at every epoch
- `phase1_kalman_per_layer_decomposition.csv` — per-layer estimates from frozen a_k split
- `phase1_kalman_tracker.png` — state estimate with uncertainty band
- `phase1_kalman_gain_curve.png` — Kalman gain vs inter-visit gap length

---

## PHASE 2: ARX Re-Evaluation

ARX was previously rejected (phi ≈ 1, anchor-only matched it). Re-evaluate using `statsmodels`.

Data sources:
- `data/mlcw/group_byLayer_orig/TUKU_orig_grouped.csv`
- `tau_demo_TUKU/results/reconstruction/TUKU_F1_reconstruction.csv` (GPS exogenous regressor)
- `results/arx_OBSOLETE_temporal_methods/` (previous results)
- `notes/methods/discussion_20260517_arx_results.md` (previous discussion)

Key questions:
- Does ARX(1) with `statsmodels` ARIMA produce phi ≈ 1.0 for all layers?
- How does the walk-forward RMSE compare against a hold-last baseline?
- Does the anchor-only ablation still match ARX performance?
- Are the 92.1% improvement claims from the original ARX study reproducible?

**Exports:**
- `phase2_arx_results.json` — per-layer fit parameters, walk-forward metrics, comparison to baseline
- `phase2_arx_comparison.png` — RMSE comparison + phi values per layer

---

## PHASE 3: Prophet Re-Evaluation

Prophet was previously tested on TUKU at 14 depth slices and rejected (deep depths improved 50–66%, shallow degraded). Re-evaluate using the `prophet` package on per-layer data.

Data sources:
- `data/mlcw/group_byLayer_orig/TUKU_orig_grouped.csv`
- `results/prophet_OBSOLETE_ablation/` (previous results)
- `notes/methods/discussion_20260517_prophet_tuku.md` (previous discussion)

Key questions:
- Does Prophet's seasonal decomposition capture dynamics the carrier model misses?
- At which layers does Prophet outperform a linear trend baseline?
- How does Prophet compare to the carrier+GWL model on F2 and F3?

**Exports:**
- `phase3_prophet_results.json` — per-layer fit summary, trend/seasonality decomposition, RMSE vs baselines
- `phase3_prophet_F2_forecast.csv`, `phase3_prophet_F3_forecast.csv` — forecast timeseries with components
- `phase3_prophet_forecast.png` — forecast with components and intervals for F2 and F3

---

## PHASE 4: MCR-AR Analysis

Multivariate Curve Resolution has never been tested on this data. Apply `pymcr` to the per-layer compaction matrix.

Data sources:
- `tau_demo_TUKU/results/reconstruction/TUKU_*_reconstruction.csv` (all 6 layers, observed values)

Key questions:
- How many meaningful components exist in the 6-layer compaction matrix? (SVD eigenvalue ratio > 0.1)
- Does MCR-AR separate F2 and F3 into distinct components, or does the rank-1 degeneracy persist?
- How does MCR-AR reconstruction R² compare to the carrier model?
- Can MCR-AR identify components that correspond to physical processes (e.g., shallow pumping vs deep clay creep)?

**Exports:**
- `phase4_mcr_ar_results.json` — SVD spectrum, component count, per-layer R², carrier comparison
- `phase4_mcr_ar_components.csv` — component concentration timeseries
- `phase4_mcr_ar_analysis.png` — scree plot + R² comparison bar chart
- `phase4_mcr_ar_components.png` — component timeseries (if multiple components found)

---

## PHASE 5: Sequential Rehearsal Reconciliation

Previous audit found metrics.json RMSEs could not be reproduced from transparency files. Reconcile.

Data sources:
- `tau_demo_TUKU/results/seq/{cadence}/TUKU_*_seq_timeseries.csv` (all cadences)
- `tau_demo_TUKU/results/seq/{cadence}/metrics.json`
- `tau_demo_TUKU/results/seq/transparency/TUKU_*_transparency_data.csv`
- `tau_demo_TUKU/results/seq/red_team_fixes/honest_skill_table.json`

Key questions:
- Can the claimed per-layer RMSEs be reproduced by matching seq predictions to transparency obs at reveal dates?
- What coverage fractions (in_band) are actually achieved at each cadence?
- Does the honest skill table (anchor-once baseline) confirm that annual skill ≤ 0 for F2/T2?

**Exports:**
- `phase5_seq_reconciled.json` — per-cadence per-layer RMSE, MAE, bias, coverage (all recomputed)
- `phase5_seq_coverage_heatmap.png` — dual heatmap: coverage + RMSE

---

## PHASE 6: Final Assembly

Merge all phase findings. Answer the bottom-line questions.

Data sources: all phase JSONs in the output folder.

Key questions:
- Are the F3 depth claims in forensic documents (238–275 m, 79 m gap) contradicted by authoritative source files?
- Does the Kalman filter add value beyond the M8 level-reset at current visit cadence?
- Does ARX re-evaluation confirm, refute, or qualify the previous rejection?
- Is MCR-AR a viable alternative to the carrier model for per-layer decomposition?
- Are any of the coverage claims from the sequential rehearsal defensible?
- Is the project ready for Part 2 (37 stations)? If not, what specific blockers remain?

**Exports:**
- `phase6_final_report.json` — all phase summaries merged with bottom-line verdict
- `phase6_investigator_dashboard.png` — one-page summary with key figures from all phases

---

## Output Checklist

After all phases, these files must exist in `tau_demo_TUKU/results/auditor_investigation_20260613/`:

```
phase0_prerequisite_verification.json
phase1_kalman_summary.json
phase1_kalman_timeseries.csv
phase1_kalman_per_layer_decomposition.csv
phase1_kalman_tracker.png
phase1_kalman_gain_curve.png
phase2_arx_results.json
phase2_arx_comparison.png
phase3_prophet_results.json
phase3_prophet_F2_forecast.csv
phase3_prophet_F3_forecast.csv
phase3_prophet_forecast.png
phase4_mcr_ar_results.json
phase4_mcr_ar_components.csv
phase4_mcr_ar_analysis.png
phase4_mcr_ar_components.png
phase5_seq_reconciled.json
phase5_seq_coverage_heatmap.png
phase6_final_report.json
phase6_investigator_dashboard.png
```

Minimum 20 files. If a package fails to install, implement the method manually. Do not skip phases.

**Begin.**
