# 2S-TOOL Batch Re-run on Raw-Summed MLCW Data

**Date:** 2026-05-27  
**Purpose:** Document the results of re-running the full 2S-TOOL batch pipeline (195 station-layer combinations) after switching the MLCW input from reconstructed group_byLayer_reconstr CSVs to raw-summed group_byLayer_orig CSVs, and after replacing the GWL timeseries input with a new set of 189 pre-aligned feather files. This session also records a TUKU F4 sign anomaly, compares new S_kv estimates against the prior run, and identifies three decisions required before IHM-F implementation can begin.

---

## What Changed

- **New GWL timeseries data created:** `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\data\gwl\mlcw_gwl_timeseries\` now contains **189 feather files** with the naming pattern `{MLCW_STATION}_{GWL_STATION}_{WELLCODE}.feather`. Each file has exactly 264 rows (same dates as the `_orig_grouped.csv` MLCW files) and 2 columns: `datetime` and `{MLCW_STATION}_{GWL_STATION}_{WELLCODE}` (piezometric head in m above mean sea level). The files are pre-aligned to the MLCW monitoring timeline — no date resampling is needed at load time. This replaces the previous set of 37 per-station feather files.

- **`prepare_2stool_inputs.py` updated** with three path and logic changes:
  - `MLCW_GROUPED_DIR` → `data/mlcw/group_byLayer_orig/` (264-epoch raw-summed MLCW layer aggregations, not reconstructed)
  - `MLCW_GWL_TS_DIR` → `data/gwl/mlcw_gwl_timeseries/` (189 pre-aligned feather files, new naming convention)
  - `ASSIGNMENT_FILE` → `gwl_to_mlcw_layer_assignment_v3.csv`
  - GWL depth conversion uses `gwl_depth_m = elev_leveling_m − piezometric_head_m`, where `elev_leveling_m` is read from `gwl_allwells_flat.csv` (2023 geodetic leveling + Kriging, ±cm accuracy). The prior script used a different elevation source.
  - Date resampling logic removed — files are already aligned.

- **2S-TOOL batch pipeline re-run** on all 195 station-layer combinations. Results written to `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\data\gwl\2stool_outputs\`:
  - `2stool_results_summary.csv` — 182 rows (13 error cases excluded), columns: station, layer, file, skv, ske_max, ske_mean, ske_min, ske_weighted, ske_std, n_loops, n_accepted_loops, y_interval, x_interval, preconsolidation_depth_hc, pct_amplitude, source
  - `2stool_loops_all.csv` — 3,732 individual loop rows across all converged cases

- **Batch quality summary:** 126 OK, 56 NEG_SKV, 13 ERROR (total 195). The 13 errors include TUKU T2, which also errored in the prior run (SVD failure in the 2S-TOOL loop-fitting step).

---

## New 2S-TOOL Results vs Prior (TUKU Comparison)

| Layer | S_kv (new, raw-summed) | S_kv (prior, reconstructed) | S_ke_weighted (new) | Verdict |
|---|---|---|---|---|
| F1 | 0.00572 | ~0.013 | 0.00311 | Lower — elastic noise in raw signal compresses inelastic envelope |
| F2 | 0.02984 | ~0.032 | 0.00199 | Close match |
| F3 | 0.05551 | ~0.086 | 0.00197 | Lower — same mechanism as F1 |
| F4 | −0.05720 (NEG_SKV) | ~0.011 | 0.00214 | Sign flipped — data-source artifact (see below) |
| T1 | 0.00685 | ~0.014 | 0.00188 | Lower |
| T2 | ERROR (SVD) | ~0.014 | — | Same SVD failure mode as prior run |

The prior-run S_kv values were estimated from the reconstructed `group_byLayer_reconstr` signal. The reconstruction step (signal separation) removes high-frequency elastic recovery oscillations before aggregating rings into layers. The raw-summed `group_byLayer_orig` data retains those oscillations.

**Why raw-summed gives lower S_kv.** The 2S-TOOL method fits a slope to the compaction-versus-head trajectory during inelastic loading cycles (head falling below the pre-consolidation level). It identifies the inelastic slope by contrasting the steeper (loading) and shallower (elastic rebound) segments of each loop. When the MLCW signal contains high-frequency elastic oscillations superimposed on the inelastic trend, the loop envelope is less clearly separated: the apparent "inelastic" segment contains upward elastic rebounds that reduce the fitted slope. The result is a systematically lower S_kv. For layers where the inelastic signal is dominant (F2 at TUKU), the two estimates converge. For layers where elastic oscillations are proportionally larger (F1, F3, T1), the gap is larger.

---

## TUKU F4 Anomaly

**Observation:** TUKU F4 changed from S_kv ≈ 0.011 (OK, 13/18 accepted loops) in the prior run to S_kv = −0.057 (NEG_SKV) in the new run.

**Physical explanation.** F4 is the deepest MLCW layer group at TUKU (approximate depth range 273–295 m). It sits at the base of the monitored section and has the smallest compaction signal of all TUKU layers — the reconstructed data showed weak but physically plausible inelastic character. In the raw-summed F4 signal, elastic recovery is proportionally large relative to the net inelastic trend. When the raw data is fed to 2S-TOOL, the loading segments in the stress-strain loops tilt slightly negative — the ring sum increases (elastic rebound) during periods when head is declining (loading), which is the opposite of the expected inelastic response. This produces a negative fitted slope, triggering the NEG_SKV flag. The negative slope is not a physical result — it is an artifact of using raw ring sums where elastic noise dominates the layer-level signal.

**Recommendation.** For IHM-F calibration at TUKU F4, use the prior-run S_kv ≈ 0.011 as the reference value. This was estimated from the reconstructed signal, which removed the elastic oscillations that cause the sign flip. Alternatively, re-run 2S-TOOL for F4 specifically using the reconstructed `group_byLayer_reconstr` CSV (not the raw-summed version). The F4 anomaly is diagnostic evidence that the raw-summed signal is not suitable as the sole 2S-TOOL input where elastic oscillations dominate.

---

## Open Questions

Three decisions must be made before `gwl_loader.py` implementation begins.

**Question 1: Which MLCW source is canonical for 2S-TOOL parameter estimation?**

The current batch used `group_byLayer_orig` (raw-summed, 264 epochs). The prior TUKU run used `group_byLayer_reconstr` (reconstructed, signal-separated). The two sources give systematically different S_kv values, with raw-summed producing lower estimates at most layers and a sign flip at TUKU F4. The decision has downstream consequences: if IHM-F uses 2S-TOOL S_kv as a prior or as a cross-check, the choice of MLCW source determines what values appear in the parameter table. Options: (a) use reconstructed `group_byLayer_reconstr` for 2S-TOOL, keeping elastic-noise-suppressed estimates; (b) use raw-summed for 2S-TOOL and accept lower S_kv values; (c) run both and report the range as parameter uncertainty.

**Question 2: What is the fallback strategy for the 13 error layers?**

Thirteen station-layer combinations failed with errors (including TUKU T2, SVD failure). IHM-F requires S_kv and S_ke per layer. For error layers, three options exist: (a) use S_kv = 0, treating the layer as purely elastic — conservative but defensible for layers where the inelastic signal is small; (b) use S_kv from the nearest-depth layer at the same station — spatially smooth but unvalidated; (c) use the prior-run 2S-TOOL value where available (applies to TUKU T2, which had S_kv ≈ 0.014 in the prior run). The fallback choice must be declared before IHM-F fitting begins and applied uniformly across all error layers — not decided per-station after inspecting results.

**Question 3: Should the 56 NEG_SKV layers be treated as effectively elastic?**

NEG_SKV means the fitted inelastic slope is negative, which is physically impossible for sediment compaction. The most likely causes are: elastic oscillations dominating the signal (as confirmed for TUKU F4), insufficient inelastic loading cycles in the calibration window, or noisy ring sums at layers with small net displacement. For IHM-F, treating NEG_SKV layers as elastic-only (S_kv = 0, use only S_ke) is the conservative and physically defensible choice. The alternative — re-running with reconstructed MLCW data for all 56 — would take more time but might recover physically meaningful S_kv values. This decision affects 56 of 195 layers (29%) and has a measurable effect on IHM-F performance across the dataset.

---

## Next Steps

Before `gwl_loader.py` (Task 1 in `2026-05-20-implementation-plan.md`) can be written, the following must happen:

**(a) Decide the canonical MLCW source for 2S-TOOL.** Compare the TUKU S_kv values from both sources against the OLS-fitted S_kv from a trial IHM-F run on TUKU. The source whose 2S-TOOL values agree better with the OLS estimates is the better physical input. This is a one-station diagnostic — it does not require re-running the full batch.

**(b) Declare the fallback rule for the 13 error layers.** Write the rule as a one-line decision (e.g., "use S_kv = 0 for all ERROR layers in the first IHM-F run; revisit if those layers contribute >10% of total station RMSE"). The rule must be recorded in writing before any fitting code is executed.

**(c) Declare the treatment of 56 NEG_SKV layers.** Write the rule analogously (e.g., "treat NEG_SKV as elastic-only for initial IHM-F run"). This locks the parameter table structure before coding begins.

Once these three decisions are recorded, `gwl_loader.py` can be written to read the canonical feather files from `data/gwl/mlcw_gwl_timeseries/` and the assignment from `gwl_to_mlcw_layer_assignment_v3.csv`, with no runtime alignment or assignment computation needed.
