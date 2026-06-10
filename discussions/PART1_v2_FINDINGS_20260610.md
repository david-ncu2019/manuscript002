# Part 1 v2 — TUKU Reconstruction Findings (Milestone M4)

> Authoritative apex-goal verdict for the TUKU pilot, produced after the 2026-06-10
> zero-trust audit repaired the evaluation machinery (M1), re-decided every Part-1 number
> with straight rulers (M2), built the per-layer hybrid model (M3), and added prediction
> intervals plus the Level-1 verdict (M4). **Every number below cites its persisted source
> file and field.** Held-out epochs only — calibration-epoch metrics never count.
>
> **Bottom line:** GATE M4 = **PASS**. 5 of 6 layers (F1, T1, F2, T2, F4) meet their
> Level-1 error thresholds on all three holdout designs. F3 fails honestly (no waiver) and
> is reported as "physically interpreted, error-bounded only in the middle gap."
> Source: `tau_demo_TUKU/results/m4_uncertainty_verdict.json` field `gate_m4.verdict`.

---

## 1. Physical story — what each layer did, and how well we can re-tell it

The TUKU multi-layer compaction well records how six sediment layers (F1, T1, F2, T2, F3,
F4, spanning 0–300 m) squeeze as confined-aquifer head falls. The goal is to re-tell each
layer's cumulative compaction $b_k(t)$ from signals that keep being measured after the
well stops (surface GPS displacement and groundwater level). We tell the story per layer
in plain terms first; the numbers follow in §2.

- **F1 (shallow, 0.06% missing, range 15.7 mm over the modeled record):** a quiet,
  near-linear settling of about 16 mm. The carrier plus a small lagged elastic-head term
  (model H1, lag 6 epochs = 30 days) re-tells it to within 1.2–3.4 mm everywhere. We can
  re-tell F1 confidently.
- **T1 (aquitard, lag 0):** the thinnest signal, ~11 mm total. The plain carrier (H0)
  already re-tells it to within 0.1–2.1 mm. No groundwater term helped on held-out data.
  We can re-tell T1 confidently.
- **F2 (thick aquifer, lag 72 epochs = 360 days, range 112 mm):** this is the layer that
  *breathes* seasonally — monsoon recharge lifts head, dry-season pumping lowers it, and
  the aquifer rebounds and recompacts by ~4.5 mm each year on top of a 112 mm secular
  fall. The annual-harmonic hybrid (H2) captures that breathing: the detrended
  observed-vs-predicted correlation jumps from +0.16 (carrier alone) to +0.98. We can
  re-tell F2 well, including its seasonal shape.
- **T2 (aquitard, lag 72):** a mixed, weak signal, ~21 mm. The plain carrier (H0) suffices
  to within 1.8–3.3 mm. We can re-tell T2.
- **F3 (deep clay, 69.7% fine material, lag 120 epochs = 600 days, range 152 mm):** the
  hard case. F3 accelerates late in the record as drought pushes head below the historical
  preconsolidation minimum and the thick clay drains permanently and irreversibly. The
  inelastic-exceedance hybrid (H3) captures roughly half of that acceleration but not all:
  it re-tells the *middle* of the record to 5.8 mm, but the end-of-record error is −30 mm
  and the 6-month tail error is ~18 mm. **We can re-tell F3's interior, but we cannot yet
  re-tell its terminal acceleration.**
- **F4 (silt/mud aquitard, 100% fine, lag 12 epochs = 60 days, range 17 mm):** the
  inelastic-exceedance hybrid (H3) re-tells it to within 0.5–3.4 mm. We can re-tell F4.

**The honest caveat that dominates M4:** the point reconstructions are good, but the
*prediction bands* are too narrow on most held-out windows. Compaction residuals carry
long memory (consolidation has a long tail), and block-bootstrap bands built from the
calibration residuals do not cover the held-out drift on the end-gap and tail designs.
This is reported below as a coverage shortfall, not papered over. Source for all coverage
numbers: `tau_demo_TUKU/results/m4_uncertainty_verdict.json` field
`layers.<L>.designs.<design>.coverage_fraction`.

---

## 2. The apex verdict table (Level-1) — held-out epochs only

Source: `tau_demo_TUKU/results/m4_uncertainty_verdict.json` field
`layers.<L>.designs.<design>` (fields `MAE_mm`, `RMSE_mm`, `design_pass`); also
`tau_demo_TUKU/results/m4_apex_verdict_table.csv`. Thresholds (field `metadata.thresholds`):
thin layers (F1, T1, T2, F4) MAE < 5, RMSE < 10 mm; thick aquifers (F2, F3) MAE < 10,
RMSE < 20 mm. RMSE reproduces the M3 registry exactly (field
`registry_rmse_for_cross_check` == `RMSE_mm` for every cell).

| Layer | Model | Design | MAE (mm) | RMSE (mm) | MAE thr | RMSE thr | Verdict |
|-------|:-----:|--------|---------:|----------:|--------:|---------:|:-------:|
| F1 | H1 | middle | 1.18 | 1.46 | <5 | <10 | PASS |
| F1 | H1 | end    | 1.80 | 2.29 | <5 | <10 | PASS |
| F1 | H1 | tail   | 3.37 | 3.40 | <5 | <10 | PASS |
| T1 | H0 | middle | 0.91 | 1.06 | <5 | <10 | PASS |
| T1 | H0 | end    | 2.13 | 2.24 | <5 | <10 | PASS |
| T1 | H0 | tail   | 0.12 | 0.15 | <5 | <10 | PASS |
| F2 | H2 | middle | 3.46 | 3.59 | <10 | <20 | PASS |
| F2 | H2 | end    | 6.45 | 6.79 | <10 | <20 | PASS |
| F2 | H2 | tail   | 1.77 | 1.87 | <10 | <20 | PASS |
| T2 | H0 | middle | 1.76 | 2.03 | <5 | <10 | PASS |
| T2 | H0 | end    | 3.31 | 3.91 | <5 | <10 | PASS |
| T2 | H0 | tail   | 2.54 | 2.59 | <5 | <10 | PASS |
| **F3** | H3 | middle | 5.80 | 6.89 | <10 | <20 | PASS |
| **F3** | H3 | **end** | **12.15** | 15.66 | <10 | <20 | **FAIL (MAE)** |
| **F3** | H3 | **tail** | **17.75** | 17.90 | <10 | <20 | **FAIL (MAE)** |
| F4 | H3 | middle | 0.47 | 0.61 | <5 | <10 | PASS |
| F4 | H3 | end    | 3.16 | 3.80 | <5 | <10 | PASS |
| F4 | H3 | tail   | 3.43 | 3.47 | <5 | <10 | PASS |

**Per-layer verdict** (field `layers.<L>.layer_pass_all_designs`): F1 PASS, T1 PASS,
F2 PASS, T2 PASS, F3 **FAIL**, F4 PASS → **5 of 6 layers pass all designs**.

**F3 waiver:** the plan allows F3 a documented waiver only if it misses MAE < 10 on the
**end gap ONLY** while keeping RMSE < 20 on all designs. F3 misses MAE on **both** end
(12.15 mm) and tail (17.75 mm). Source: field `layers.F3.waiver_detail.mae_failing_designs`
= `["end","tail"]`; `layers.F3.waiver_eligible_end_gap_only` = `false`. **F3 therefore
takes NO waiver.** It does keep RMSE < 20 on all three designs (15.66, 17.90, 6.89), so the
failure is an MAE (bias) failure, not a variance failure — F3 systematically under-predicts
the terminal drainage.

**GATE M4** (field `gate_m4`): 5/6 layers pass all designs without any waiver
(`n_layers_passing_all_designs` = 5; `f3_takes_waiver` = false). The ≥5/6 rule is met by
the five clean layers alone. **Verdict: PASS** (`gate_m4.verdict`).

---

## 3. Prediction intervals (Task 4.1) — block bootstrap, 90% band

Method (field `metadata.bootstrap`): calibration residuals $r = b_{obs} - b_{pred}$ on the
training epochs of each design; 1,000 residual paths built by resampling contiguous blocks
of 73 epochs (≈1 year) with replacement; added to the point prediction over held-out
epochs; 5th/95th percentile per epoch = 90% band. Where coverage < 0.85 the block was
widened to 146 epochs (2 years) and re-checked; where still < 0.85 the band is labeled
"calibrated to X%" — never silently relabeled (field `coverage_label`).

| Layer | Design | mean half-width (mm) | block (epochs) | coverage | label |
|-------|--------|---------------------:|---------------:|---------:|-------|
| F1 | middle | 1.57 | 146 | 0.678 | calibrated to 67.8% |
| F1 | end    | 1.65 | 146 | 0.624 | calibrated to 62.4% |
| F1 | tail   | 1.45 | 146 | 0.000 | calibrated to 0.0% |
| T1 | middle | 1.81 | 73  | 0.946 | — (≥0.85) |
| T1 | end    | 1.62 | 146 | 0.204 | calibrated to 20.4% |
| T1 | tail   | 1.82 | 73  | 1.000 | — (≥0.85) |
| F2 | middle | 2.55 | 146 | 0.214 | calibrated to 21.4% |
| F2 | end    | 1.84 | 146 | 0.000 | calibrated to 0.0% |
| F2 | tail   | 3.41 | 73  | 1.000 | — (≥0.85) |
| T2 | middle | 2.78 | 73  | 0.706 | calibrated to 70.6% |
| T2 | end    | 1.65 | 146 | 0.264 | calibrated to 26.4% |
| T2 | tail   | 3.10 | 73  | 0.611 | calibrated to 61.1% |
| F3 | middle | 8.93 | 73  | 0.866 | — (≥0.85) |
| F3 | end    | 4.79 | 73  | 0.299 | calibrated to 29.9% |
| F3 | tail   | 6.33 | 146 | 0.000 | calibrated to 0.0% |
| F4 | middle | 1.99 | 73  | 1.000 | — (≥0.85) |
| F4 | end    | 0.84 | 146 | 0.086 | calibrated to 8.6% |
| F4 | tail   | 1.21 | 146 | 0.000 | calibrated to 0.0% |

Source: field `layers.<L>.designs.<design>` (`band_mean_half_width_mm`,
`band_block_epochs`, `coverage_fraction`, `coverage_label`).

**Coverage result, stated plainly:** the 90% band reaches its ≥0.85 target on only 5 of 18
layer×design cells (T1 middle 0.946, T1 tail 1.000, F2 tail 1.000, F3 middle 0.866,
F4 middle 1.000). On the **end** and **tail** designs the band is far too narrow — it
covers 0% of held-out points for F1/F2/F3/F4 tail and F2 end. **Physical reason:** the
training residuals on these designs are small and stationary inside the calibration window,
but the held-out window sits in the future where the secular drift and the late-record
acceleration leave the band. A residual-only bootstrap cannot manufacture the missing
*trend* uncertainty; it only resamples the in-sample wiggle. **This is an honest finding,
labeled, not hidden** — every short band carries its "calibrated to X%" tag. Widening from
73 to 146 epochs was applied wherever 73-block coverage fell short (10 of 18 cells now use
the 146-epoch block, field `band_block_epochs` = 146); it raised coverage slightly but did
not rescue the end/tail bands.

**Band-width red flags (Task 4.1.3):** a half-width exceeding the layer's observed range is
the red-flag condition. **None triggered** — every `band_half_width_exceeds_range_red_flag`
= `false` (largest half-width is F3 middle 8.93 mm against a 151.6 mm observed range).
Source: field `layers.<L>.designs.<design>.band_half_width_exceeds_range_red_flag`;
observed ranges in field `metadata.observed_ranges_mm`.

> **Escalation note (not improvised):** the coverage shortfall on end/tail designs is a
> genuine limitation of residual-block bootstrapping for a trending, long-memory series.
> Per M4 standing rule 5, it is reported with evidence and the bands are labeled — not
> relabeled to look adequate. A trend-aware interval (e.g. propagating coefficient
> uncertainty or a parametric drift term) is the candidate fix; that is an M5-or-later
> design decision and was NOT undertaken here (hard stop at GATE M4).

---

## 4. Corrected physics table (from M2.2)

Source: `tau_demo_TUKU/results/characterization/TUKU_storage_params.json` field
`per_layer.<L>`. Bulk slopes $S_{ke}, S_{kv}$ in mm per m of head change; specific storage
$S_{ske}, S_{skv}$ in m⁻¹ (two-thickness rule). These were re-fit with the M1-corrected
τ-lag, so they supersede every pre-repair storage number.

| Layer | $S_{ke}$ (mm/m) | $S_{kv}$ (mm/m) | $S_{ske}$ (m⁻¹) | $S_{skv}$ (m⁻¹) | bulk ratio | $S_{ke}$ status |
|-------|----------------:|----------------:|----------------:|----------------:|-----------:|-----------------|
| F1 | 2.626 | 4.315 | — | — | 1.64 | determined |
| T1 | 1.545 | 3.134 | — | — | 2.03 | determined |
| F2 | 1.107 | 16.228 | $1.04\times10^{-5}$ | $1.34\times10^{-3}$ | 14.67 | determined (thickness-artifact flag on specific ratio) |
| T2 | 0.345 | 5.533 | — | — | 16.06 | determined |
| F3 | 0.0 | 23.693 | 0.0 | $3.08\times10^{-4}$ | — | **not determined (inelastic-only re-fit)** |
| F4 | 0.0 | 8.695 | 0.0 | — | — | **not determined (inelastic-only re-fit)** |

Notes (all from `per_layer.<L>`):
- **F2** specific-storage $S_{skv} = 1.34\times10^{-3}$ m⁻¹ sits at the Hung et al. (2021)
  middle-fan prior ($1.33\times10^{-3}$ m⁻¹). The bulk ratio 14.67 is inside the physical
  8–100× contrast; the *specific* ratio 128.92 carries a `thickness_artifact` flag
  (`flags` = `["thickness_artifact"]`, span/clay = 106.3/12.1 ≈ 8.8) and must not be read
  as a material ratio.
- **F1, T1** bulk ratios (1.64, 2.03) sit BELOW the physical floor of 3 — an M2.2 finding,
  not an M4 defect: post-2015 head at these shallow wells barely crosses below $h_c$, so
  the inelastic term is fit on weak signal (elastic-dominated regime).
- **F3, F4** went inelastic-only (the D5 identifiability repair): $S_{ke} = 0$, no ratio.
  For F4 this is physically correct (100% silt/mud, field `clay_pct` = 100.0;
  `flags` includes `S_ke_zero`). The inelastic-only re-fit gives negative cumulative R²
  (F3 `r2_cum` = −2.79, F4 reported similarly) — a real finding: a single inelastic slope
  cannot reproduce the cumulative shape of these clays. F3's storage is "physically
  labeled, not a clean measurement."

---

## 5. Limitations

1. **Prediction bands under-cover on end/tail designs.** Only 5 of 18 layer×design cells
   reach the 0.85 coverage target. The residual-block bootstrap captures in-sample wiggle,
   not out-of-sample trend drift. All deficient bands are labeled "calibrated to X%"
   (field `coverage_label`). A trend-aware interval is deferred (post-M4).
2. **F3 terminal acceleration is unresolved.** F3 keeps RMSE < 20 on all designs but misses
   MAE < 10 on both end (12.15 mm) and tail (17.75 mm), with a −30 mm end-of-record error
   (M3 registry `adoption_map.F3.adopted_extra_by_design.end.end_error_mm`). The
   inelastic-exceedance term captures about half the drainage; the deep clay's full
   irreversible consolidation is not yet re-told. F3 takes **no** waiver.
3. **F3/F4 storage is not a clean measurement.** Both are inelastic-only with negative
   cumulative R²; their $S_{kv}$ is "empirically adequate, physically uninterpreted."
4. **GPS carrier ends 2024-12-31; MLCW continues to 2025-10-01.** The last ~9 months
   cannot be re-told from this GPS series; InSAR coverage of that window is an M5 question
   (out of scope here).
5. **Single station.** All of the above is the TUKU pilot only. Part 2 (37 stations) and
   Part 3 (8,577 grid points) remain blocked.

---

## 6. GATE M4 verdict

**PASS.** Apex table persisted (`tau_demo_TUKU/results/m4_apex_verdict_table.csv` and
`m4_uncertainty_verdict.json`). 5 of 6 layers (F1, T1, F2, T2, F4) pass MAE and RMSE on all
three holdout designs; this meets the ≥5/6 rule without invoking any waiver. F3 fails
honestly on MAE for the end and tail designs and is **not** waiver-eligible (waiver is
end-gap-only). Every number in this document cites its persisted file and field. Generator:
`tau_demo_TUKU/18_m4_uncertainty_verdict.py` (re-runnable). **Hard stop at GATE M4 — M5 not
entered.**
