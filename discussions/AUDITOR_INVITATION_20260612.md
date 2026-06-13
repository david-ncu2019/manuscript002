# Independent Auditor Invitation — TUKU Pilot Results Verification

**Date:** 2026-06-12
**Station:** TUKU (土庫), Yunlin County, Taiwan
**Project:** InSAR-MLCW Compaction Gap-Fill and Prediction

---

## 0. What We Are Asking You To Do

We have produced a set of results at TUKU station: a GPS-carrier model that apportions surface displacement into six subsurface layer compactions, and a sequential walk-forward rehearsal that tests how well the model predicts future compaction when in-situ visits are sparse.

**We are not asking you to trust our numbers.** We are asking you to write your own verification code that reads the same input data we used, recomputes key quantities independently, and checks whether our claims hold up. The two folders you will inspect are:

- **Folder ABC:** `tau_demo_TUKU/results/` — the primary results produced by the previous team (reconstruction CSVs, storage parameters, sequential rehearsal outputs, and all evaluation metrics).
- **Folder XYZ:** `tau_demo_TUKU/results/auditor_diagnostics/` — machine-readable diagnostic exports we generated on 2026-06-12 from the same results. These files flag sign errors, regime mismatches, drift events, and cross-layer inconsistencies. We want you to verify whether these flags are real or artifacts of our diagnostic code.

You should treat every number, every file format claim, and every sign convention statement in this document as **unverified until you confirm it yourself.**

---

## 1. Project Objective (Restated for Auditor)

The Water Resources Agency (WRA) of Taiwan monitors land subsidence using Multi-Layer Compaction Wells (MLCW) at 39 stations across the Choushui River Alluvial Fan (CRAF). In November 2021, 20 stations were shut down due to budget cuts. The remaining 19 face further reductions.

Each MLCW station measures compaction at 6 depth layers (F1, T1, F2, T2, F3, F4 — spanning 0–300 m). The layers F1–F4 are aquifers; T1–T2 are aquitards (Taiwan CGS convention).

**The objective at TUKU:** Develop a method that reconstructs per-layer compaction timeseries using continuously-available GPS surface displacement and groundwater level (GWL) data — and test whether the method can predict future compaction when in-situ MLCW visits are reduced from monthly to annual or semiannual cadence.

**The method selected:** A GPS carrier model:
```
b_k(t) = a_k × d_GPS(t) + d_k × u_k(t) + c_k
```
where `b_k` is cumulative compaction of layer k, `d_GPS` is the GPS surface displacement at a nearby station, `u_k` is a GWL residual term (adopted only for F1, T1, F2, T2; rejected for F3, F4), and `a_k ≥ 0`, `d_k ≥ 0`, `c_k` are fitted parameters. The model does NOT enforce column closure (Σ a_k may differ from 1.0; the fitted sum at TUKU is 0.637).

---

## 2. Sign Conventions (Non-Negotiable — Verify These First)

Every quantity you read from the files below uses these conventions. A sign error in your verification code will produce physically wrong conclusions.

| Quantity | File column | Units | Convention |
|----------|-------------|-------|------------|
| MLCW compaction | `b_observed_mm`, `b_model_mm`, `obs_inc_mm` | mm | **negative = compaction** (surface sinks) |
| GWL piezometric head | `H_zero_ref_m`, `head_m_msl` | metres above MSL | higher = rising head; **never negate** |
| InSAR displacement | `d_surface_mm` (in reconstruction CSVs) | mm | negative = subsidence |
| Storage coefficients | `S_ke`, `S_kv`, `S_ske`, `S_skv` | mm/m or m⁻¹ | always ≥ 0 |
| Residual = pred − obs | `residual_mm` | mm | positive = model underpredicts compaction |
| Virgin term V(t) | `V_m` | metres | negative = head below historical minimum (inelastic) |

**Critical:** The MLCW `b_observed_mm` column is **cumulative** in the reconstruction CSVs (`reconstruction/*.csv`) and **incremental** in the per-epoch residuals file (`auditor_diagnostics/per_epoch_residuals.csv` column `obs_inc_mm`). Confirm which domain you are working in before computing any statistic.

---

## 2.5. Study Area Background — Read These First

Before inspecting our results, you need context on the Choushui River Alluvial Fan (CRAF) and how other scientists have approached subsidence problems in this basin and elsewhere. We do not expect you to read every paper — but at minimum, scan the documents flagged as **required**.

### Required Reading (short, directly relevant)

| Document | Path | What you need from it |
|----------|------|----------------------|
| **CRAF regional background** | `docs/choushui_background_search.md` | Hydrogeology, pumping rates, subsidence history, monitoring network. The one document that explains the physical setting. |
| **Skeletal storage tables** | `docs/choushui_skeletal_storage_coeffs.md` and `docs/s_ske_skv_tables.md` | Per-station, per-layer $S_{ske}$ values from Hung et al. (2021) and multi-year dry-period analysis. These are the literature values our fitted parameters are compared against. |
| **Tran et al. (2024) summary** | `docs/s40623-024-02019-2_summary.md` | Deep displacement mechanism — hydraulic expansion/contraction in low-permeability aquitards explains why deep layers can be out-of-phase with shallow head. Directly relevant to F3 phase paradox. |
| **Physics safeguards audit** | `discussions/PHYSICS_SAFEGUARDS.md` | The independent audit that found 9 errors across 6 AI-generated documents, including a factor-of-10 distal $S_{skv}$ error. Establishes the mandatory halt rules our guardrails enforce. |

### Recommended Reading (papers — understand competing methods)

| Paper | Path | Why it matters for your audit |
|-------|------|------------------------------|
| **Hung et al. (2021) WRR** | `docs/papers/Hung et al. - 2021 - Measuring and Interpreting Multilayer Aquifer‑System Compactions_full_paper.md` | **Definitive CRAF reference.** Source of $S_{ske}$/$S_{skv}$ values by fan zone (proximal, middle, distal). Our fitted parameters claim to match this paper's values. Verify whether our claims are consistent with the paper's numbers. |
| **Hung et al. (2012)** | `docs/papers/Hung et al. - 2012 - Modeling aquifer-system compaction and predicting land subsidence in central Taiwan_full_paper.md` | COMPAC 1D model with GA parameter estimation. Documents 210 cm cumulative subsidence at Dacheng, F2 contributing 57.3% of compaction. Establishes the preconsolidation-head concept we use. |
| **Tsai and Hsu (2018)** | `docs/papers/Tsai and Hsu - 2018 - Identifying poromechanism and spatially varying parameters of aquifer compaction in Choushui River alluvial fan_full_paper.md` | **Different method — compare against ours.** Visco-elasto-plastic (VEP) model with 2 viscous dampers, capturing creep that our elastic/inelastic model misses. If you find systematic residual patterns in our predictions, this paper's framework may explain them. |
| **Chu et al. (2024)** | `docs/papers/Chu et al. - 2024 - Spatiotemporal subsidence feature decomposition and hotspot identification_full_paper.md` | EOF decomposition of MLCW data — 97.5% long-term trend, 1.7% seasonal, 0.4% intra-seasonal. Establishes the per-layer compaction budget our model must respect. |
| **Tatas and Chu (2024)** | `docs/papers/Tatas and Chu - 2024 - Effective Hydraulic Head Control Rule Identification for Unrecoverable Subsidence Mitigation_full_paper.md` | **Different method — purely statistical head-rule threshold.** Classifies elastic vs. inelastic without stress-strain diagrams. ~15% inelastic events. Head thresholds: −11 m MSL (mid-fan) to −30 m MSL (distal). Compare against our h_c values. |
| **Patra et al. (2025)** | `docs/papers/Patra et al. - 2025 - Employing machine learning to document trends and seasonality of groundwater-induced subsidence_full_paper.md` | **Different method — ML-based.** Random Forest on decomposed timeseries to separate trend from seasonality. No physics. Compare against our carrier+GWL decomposition. |
| **Tran et al. (2024)** | `docs/s40623-024-02019-2.pdf` and `docs/s40623-024-02019-2_formula_guide.md` | Poroelastic theory (Biot consolidation) for deep displacement. Formula guide documents F1–F6: fluid mass conservation, effective stress, Hooke's law, strain-displacement, storage coefficient, isotropic stiffness. The storage coefficient F5 is the theoretical basis for our $S_{ske}$/$S_{skv}$. |

### Key Regional Parameters (for Cross-Reference)

| Parameter | Published Value | Source | Our Claimed Range | Check |
|-----------|----------------|--------|-------------------|-------|
| Mid-fan $S_{ske}$ | $1.15 \times 10^{-4}$ m⁻¹ | Hung et al. (2021) | $6.3 \times 10^{-5}$ to $1.8 \times 10^{-4}$ | Our F1/F2 values are below literature; is this physically defensible? |
| Mid-fan $S_{skv}$ | $1.33 \times 10^{-3}$ m⁻¹ | Hung et al. (2021) | $2.6 \times 10^{-4}$ to $1.34 \times 10^{-3}$ | F2 matches (1.34e-3). Others are below. |
| Distal $S_{skv}$ | $1.91 \times 10^{-3}$ m⁻¹ | Hung et al. (2021) | — | **Warning:** An AI-generated document previously misquoted this as $1.91 \times 10^{-4}$ (factor-of-10 error). Verify any distal values you encounter. |
| $S_{skv}/S_{ske}$ ratio | ~12× (mid), ~16× (distal) | Hung et al. (2021) | [3, 50] gate | Our gate is relaxed from literature [8, 100]. Is 3× too permissive? |
| Safe GWL threshold | −11 m MSL (mid-fan), −30 m MSL (distal) | Tatas and Chu (2024) | h_c values in storage JSON | Compare our h_c against these independently-derived thresholds. |
| Cumulative subsidence | 210 cm (Dacheng, 1992–2009) | Hung et al. (2012) | TUKU cumulative ~140 mm | TUKU is less severe than the Dacheng hotspot. Is our station representative? |
| Per-layer compaction budget | F2: 57.3%, F3: 24.5%, F1: 10.2% | Chu et al. (2024) | a_k shares: F2=0.23, F3=0.31, F1=0.02 | Our a_k distribution differs from the Chu et al. per-layer budget. Investigate. |

---

## 2.6. Depth Verification — Check Authoritative Sources (CRITICAL)

**Warning:** Previous discussion documents in this project (including `discussions/F3_FORENSIC_VERDICT_20260612.md`, `discussions/FEASIBILITY_VERDICT_FINAL_20260611.md`, and `CLAUDE.md`) contain claims about layer depths and well-screen positions that were **not verified against the well manager's official classification files.** Do not repeat these claims without checking the primary sources yourself.

### The Previous Claim (Now Known to Be Wrong)

Prior documents claimed: *"F3 is at 238–275 m depth. GWL well 09050331 is screened at 176–179 m. Therefore the well is 79 m above the F3 clay with 0 m overlap — the driving head for F3 is unmeasured."*

**This claim is false.** It cherry-picked the deepest portion of F3 and ignored the upper 70 m of the layer.

### Authoritative Source Files — Read These

| File | Path | What it contains | Who provided it |
|------|------|-----------------|-----------------|
| **Ring-to-layer classification** | `data/mlcw/group_byLayer_orig/TUKU_classify_table.csv` | The official assignment of every magnetic ring depth to a hydrogeological layer (F1/T1/F2/T2/F3/F4). 25 rows covering 0–300 m. | The MLCW well manager (WRA/CGS) |
| **Borehole material log** | `data/mlcw/borehole_materials/YL_WSYL23G1_TUKU_土庫.xlsx` | Material type at every depth interval (56 segments, 0–300 m). SOIL_CATEGORY: 1=Gravel, 3=cSmS (coarse/medium sand), 5=Z/M (silt/clay/mud). Does NOT claim aquifer/aquitard separation — materials only. | The MLCW well manager |
| **GWL well metadata** | `data/gwl/well_info/gwl_allwells_flat.csv` | Screen depth, total depth, elevation for every GWL well. Well 09050331: depth=185.0 m, screen=176.0–179.0 m, field-verified 2026-05-18. | WRA groundwater monitoring network |

### Corrected Facts (Verified 2026-06-12 Against Primary Sources)

**F3 layer depth (from `TUKU_classify_table.csv`, the well manager's official classification):**

| Ring depth (m) | Assigned layer |
|---------------|---------------|
| 172.889 | F3 |
| 177.694 | F3 |
| 185.386 | F3 |
| 198.421 | F3 |
| 220.335 | F3 |
| 228.408 | F3 |
| 232.852 | F3 |
| 242.032 | F3 |
| 252.265 | F3 |
| 272.728 | F3 |
| **283.383** | **F4** (F3 ends here) |

**F3 spans 172.889 – 272.728 m** (11 rings, ~100 m thick). The previous claim of "238–275 m" described only the deepest ~40% of F3 and omitted the upper 70 m entirely.

**GWL well 09050331 position (from `gwl_allwells_flat.csv`):**
- Total well depth: **185.0 m**
- Screen interval: **176.0 – 179.0 m**
- The screen IS within F3 (172.9–272.7 m), in the upper 3–6 m of the layer

**Borehole material at 176–179 m (from `YL_WSYL23G1_TUKU_土庫.xlsx`):**
- 171.0–176.0 m: M (mud/silt) — SOIL_CATEGORY 5, fine-grained
- 176.0–180.0 m: Z (clay) — SOIL_CATEGORY 5, fine-grained
- The well screen is in fine-grained material within F3, not in a sand lens

### What Is Actually True vs What Was Previously Claimed

| Previous claim | Verified fact | Verdict |
|---------------|---------------|---------|
| "F3 is at 238–275 m" | F3 is 172.9–272.7 m (100 m thick) | **FALSE.** The claim omitted the upper 70 m of F3. |
| "Well screened 79 m above F3" | Well screen at 176–179 m IS within F3 (172.9–272.7 m) | **FALSE.** The 79 m gap was calculated using wrong F3 boundaries. |
| "0 m overlap between well and F3" | Well overlaps the upper 3–6 m of F3 | **FALSE.** There is overlap in the uppermost F3. |
| "No piezometer in the F3 clay" | Well at 176–179 m is IN F3, in fine material (mud/clay) | **MISLEADING.** The well IS in F3, but only in the uppermost ~12 m that the well can physically access. |

### The Actual Instrumentation Limitation (Correct Framing)

The real problem is more nuanced than "no overlap":

1. Well 09050331 has a total depth of **185 m**. F3 extends to **272.7 m**. The well physically cannot measure head below 185 m.
2. The well monitors head in only the uppermost **~12 m** of F3 (172.9–185 m). The lower **~88 m** of F3 (185–272.7 m) has no head measurement.
3. The well screen at 176–179 m is in fine-grained material (mud/clay, SOIL_CATEGORY 5). This material has low permeability — the head measured at this screen may not be representative of head in the deeper, more permeable portions of F3 (which contain sand lenses at 218–226 m, 230–240 m, 250–255 m, 260–265 m, 266–270 m, and 275–277 m per the borehole log).
4. A single well in the uppermost fine-grained portion of a 100 m thick heterogeneous layer cannot capture the vertical head distribution throughout F3.

**What this means for the F3 forensic conclusions:** The H1 hypothesis ("depth-mismatched driver") was framed around a fabricated 79 m gap. The corrected finding is: the well IS in F3, but it only samples the uppermost portion of a thick, heterogeneous layer. Whether this upper-F3 head measurement is an adequate driver for compaction occurring throughout the full F3 thickness is a physically legitimate question — but it must be argued from the correct depth facts, not the fabricated ones.

### Auditor Requirement for This Section

1. **Read `TUKU_classify_table.csv` yourself.** Verify the F3 depth boundaries we state above. Do not trust our transcription.
2. **Read `YL_WSYL23G1_TUKU_土庫.xlsx` yourself.** Verify the material at every depth within F3. Identify all sand lenses within F3 (SOIL_CATEGORY 3) and note their depths. Consider whether a single well at 176–179 m can represent head across the full layer.
3. **Read `gwl_allwells_flat.csv` for well 09050331.** Verify the screen depth and total well depth.
4. **Re-evaluate the F3 forensic hypotheses** using the correct depth information. The three hypotheses from `discussions/F3_FORENSIC_VERDICT_20260612.md` are:
   - H1: Depth-mismatched driver — **re-evaluate using correct F3 boundaries**
   - H2: Poisoned truth (2024+ data smoothed) — unchanged, still valid
   - H3: Physical outlier (deep clay out-of-phase) — unchanged, but re-evaluate whether a well at 176–179 m in fine material can detect deep clay dynamics
5. **Check all other layer depth claims** in CLAUDE.md and discussion documents against `TUKU_classify_table.csv`. Report any discrepancies.
6. **For the 29-station portfolio:** Each station has its own `{STATION}_classify_table.csv` at `data/mlcw/group_byLayer_orig/`. Verify that layer depth claims for other stations (if any exist in discussion documents) match their respective classify tables.

---

## 3. Folder ABC — Primary Results (`tau_demo_TUKU/results/`)

### 3.1 Directory Map

```
tau_demo_TUKU/results/
├── reconstruction/          ← GPS-carrier gap-fill model (6 CSVs + 1 JSON)
├── timeseries/              ← Cumulative IHM-F NNLS fits (6 CSVs)
├── characterization/        ← Storage parameter characterization (JSON)
├── seq/                     ← Sequential walk-forward rehearsal
│   ├── actual/              ← Real historical visit cadence
│   ├── monthly/             ← 1 visit/month (57 visits)
│   ├── quarterly/           ← 1 visit/quarter (21 visits)
│   ├── semiannual/          ← 1 visit/6 months (11 visits)
│   ├── annual/              ← 1 visit/year (6 visits)
│   ├── none/                ← Zero visits (pure extrapolation)
│   ├── transparency/        ← Per-layer pred+obs at reveal dates
│   ├── forensics/           ← F3 phase-paradox investigation
│   └── red_team_fixes/      ← Red Team corrections (2026-06-11)
├── simple_ratio_test/       ← Detrended GPS/MLCW ratio analysis
├── auditor_diagnostics/     ← (This is Folder XYZ — see §4)
├── mlcw_observed_epoch_mask.csv   ← Data provenance mask
├── holdout_bakeoff.json     ← Three-method comparison verdict
├── carrier_gwl_eval.json    ← GWL adoption decision
├── evaluation_metrics.json  ← Per-layer evaluation (15 metrics × 6 layers)
└── stress_strain_per_layer.csv ← IHM-F storage coefficients
```

### 3.2 Key CSV Files — Column Reference

**Reconstruction CSVs** (`reconstruction/TUKU_{F1,F2,F3,F4,T1,T2}_reconstruction.csv`, ~130–141 KB each, 1572 rows):

| Column | Type | Description |
|--------|------|-------------|
| `date` | datetime (YYYY-MM-DD) | Epoch date, 5-day cadence |
| `b_model_mm` | float | Cumulative model prediction (gap-filled) |
| `b_observed_mm` | float | Cumulative observed MLCW (NaN where no field visit) |
| `residual_mm` | float | `b_model_mm − b_observed_mm` (NaN at non-visit epochs) |
| `d_surface_mm` | float | GPS surface displacement at this epoch (NaN before GPS start) |
| `a_k` | float | Fitted GPS carrier coefficient (same value on every row for a given layer) |
| `c_k` | float | Fitted intercept (same value on every row) |
| `d_k` | float | Fitted GWL coefficient (0.0 for F3, F4) |
| `b_model_inc_mm` | float | Incremental model prediction (diff of `b_model_mm`) |
| `is_increment_missing` | bool | True if previous epoch is missing |
| `is_gap_filled` | bool | True if this epoch has no field observation |
| `is_gap` | bool | True if this epoch is in a gap |
| `is_model_only` | bool | True if no field observation exists here |

**Cumulative Timeseries CSVs** (`timeseries/TUKU_{layer}_cumulative_timeseries.csv`, ~74–82 KB each, ~770 rows):

| Column | Type | Description |
|--------|------|-------------|
| `datetime` | datetime | Epoch date |
| `H_zero_ref_m` | float | GWL head, zero-referenced to REF_DATE (2015-01-16) |
| `b_obs_mm` | float | Cumulative observed MLCW |
| `V_m` | float | Virgin exceedance term: `min(0, cummin(H) − h_c)` |
| `b_pred_nnls_mm` | float | NNLS cumulative prediction |
| `b_pred_2step_mm` | float | Two-step decoupled cumulative prediction |

**Provenance Mask** (`mlcw_observed_epoch_mask.csv`, 65 KB, 1572 rows):

| Column | Type | Description |
|--------|------|-------------|
| `date` | datetime | Epoch date |
| `F1_observed` … `F4_observed` | bool | True = genuine field measurement; False = interpolated/dense-filled |

**Sequential Timeseries CSVs** (`seq/{cadence}/TUKU_{layer}_seq_timeseries.csv`):

| Column | Type | Description |
|--------|------|-------------|
| `date` | datetime | Epoch date |
| `pred_mm` | float | Cumulative model prediction |
| `half_width_mm` | float | Conformal prediction band half-width |
| `horizon_epochs` | int | Forecast horizon (epochs since last calibration) |
| `step_flag` | bool | True at scheduled visit dates |

### 3.3 Key JSON Files — Structure Reference

**Carrier Reconstruction Summary** (`reconstruction/TUKU_carrier_reconstruction_summary.json`):
```json
{
  "metadata": { "model": "b_k(t) = a_k * d_GPS(t) + d_k * u(t) + c_k", "gwl_layers": ["F1","F2","T1","T2"], "sum_a_k": 0.637 },
  "per_layer": {
    "F1": { "a_k": 0.02493, "c_k": -4.1811, "d_k": 0.17387, "r2_cal": 0.942, "rmse_cal_mm": 1.21, "n_calibration_epochs": 1081, "tail_evaluation": { "skill": -0.0924 } },
    "F2": { "a_k": 0.23027, "c_k": -17.6755, "d_k": 0.54647, "r2_cal": 0.991, "rmse_cal_mm": 3.02, "n_calibration_epochs": 823, "tail_evaluation": { "skill": +0.4305 } },
    "F3": { "a_k": 0.30558, "c_k": -136.379, "d_k": 0.0,     "r2_cal": 0.981, "rmse_cal_mm": 8.02, "n_calibration_epochs": 1081, "tail_evaluation": { "skill": -0.2504 } }
  }
}
```

**Characterization JSON** (`characterization/TUKU_storage_params.json`):
```json
{
  "per_layer": {
    "F2": { "S_ke_mm_per_m": 1.107, "S_kv_mm_per_m": 16.228, "tau_opt": 72, "S_ske_m1": 1.04e-5, "S_skv_m1": 1.34e-3, "r2_cum": 0.926, "ratio_specific": 128.9, "n_elastic": 6, "n_inelastic": 766, "notes": "thickness_artifact" },
    "F3": { "S_ke_mm_per_m": 0.0,   "S_kv_mm_per_m": 23.693, "tau_opt": 120, "S_ske_m1": 0.0,   "S_skv_m1": 3.08e-4, "r2_cum": -2.79, "n_elastic": 0, "n_inelastic": 765, "notes": "F3: S_ke=0 — most epochs are inelastic; elastic storage not identifiable" }
  }
}
```

**GWL Evaluation JSON** (`carrier_gwl_eval.json`):
```json
{
  "adopt_gwl": { "F1": true, "T1": true, "F2": true, "T2": true, "F3": false, "F4": false },
  "per_layer": {
    "F1": { "collinearity": { "vif": 3.38, "corr": 0.839 }, "middle": { "delta_pct": -10.5 } }
  }
}
```

---

## 4. Folder XYZ — Diagnostic Exports (`tau_demo_TUKU/results/auditor_diagnostics/`)

These 16 files (8 CSV/JSON + 8 PNG) were produced on 2026-06-12 by `tau_demo_TUKU/35_export_auditor_diagnostics.py`. They read the persisted results in Folder ABC and derive additional columns and anomaly flags. **Do not assume our derived columns are correct — recompute at least the sign-error flags, regime mismatches, and drift rates yourself.**

### 4.1 File Inventory

| File | Rows | Key columns to verify |
|------|------|-----------------------|
| `per_epoch_residuals.csv` | 9,432 (6 layers × 1,572 epochs) | `obs_inc_mm`, `pred_inc_mm`, `residual_mm`, `sign_error`, `cum_drift_rate_mm_per_epoch` |
| `sign_error_log.csv` | 4,812 (filtered: only problematic epochs) | `obs_direction`, `pred_direction`, `error_type`, `magnitude_ratio` |
| `per_layer_regime_epochs.csv` | 4,622 | `regime` (elastic/inelastic), `expected_sign_match`, `V_m` |
| `prediction_decomposition.csv` | 9,432 | `carrier_term_mm`, `gwl_term_mm`, `intercept_mm`, `carrier_fraction` |
| `cross_layer_consistency.csv` | 1,572 | `sum_layer_pred_mm`, `column_mismatch_mm`, `f2_f3_anti_phase` |
| `drift_diagnostics.csv` | 18,864 (2 windows × 9,432) | `drift_rate_mm_per_year`, `fraction_inelastic_in_window` |
| `seq_innovation_detail.csv` | 216 (scoring points × 6 cadences × 6 layers) | `innovation_mm` (signed), `in_band` |
| `auditor_summary.json` | — | `global`, `per_layer`, `cross_layer`, `regime`, `seq_coverage` |

### 4.2 Our Diagnostic Claims (Verify These)

The diagnostic exports flag the following patterns. **We want you to confirm or refute each one using your own code:**

1. **F3 sign-reversal rate = 39.3%** — 220 of 560 non-trivial-observation epochs where the model predicts rebound (+ sign) while the ground compacts (− sign). The worst cluster is June 2023 (all 10 worst sign-error epochs are F3 in May–June 2023).

2. **F3 head-compaction mismatch rate = 35.8%** — 276 epochs where the GWL head rises significantly (+0.8 to +0.9 m in 5 days, indicative of June rainy-season recharge) but the F3 layer continues to compact. This is physically inconsistent with Terzaghi effective stress if the measured head is the driver.

3. **F2/F3 anti-phase rate = 23.5%** — At 23.5% of epochs where both F2 and F3 have non-trivial incremental compaction, the signs are opposite (one compacting while the other rebounds).

4. **F2 severe underpredict at 2014-04-01** — obs = −0.843 mm/5d, pred = −0.172 mm/5d (model captured only 20% of observed compaction).

5. **Column closure p95 error = 256 mm** (cumulative) — the sum of per-layer model predictions deviates from the GPS surface observation by up to 256 mm cumulatively. The carrier model does not enforce Σ a_k = 1.0 (fitted sum = 0.637).

6. **F3 and F4 S_ke = 0.0** — The IHM-F characterization declares elastic storage unidentifiable for these layers and refits them as inelastic-only. F3 R²_cum = −2.79 (worse than a flat line).

### 4.3 Companion Figures

Each CSV has a companion PNG with the same base filename. The figures show:
- `per_epoch_residuals.png` — 6-panel obs vs pred with residual timeseries
- `sign_error_log.png` — bar chart of sign errors per layer + scatter of magnitude ratios
- `per_layer_regime_epochs.png` — head timeseries colored by regime with mismatch markers
- `prediction_decomposition.png` — stacked area of carrier vs GWL components
- `cross_layer_consistency.png` — column sum vs GPS + stacked per-layer contributions
- `drift_diagnostics.png` — rolling 1-year drift rate with acceptable/concerning/critical bands
- `seq_innovation_detail.png` — signed innovation scatter across 6 cadences
- `auditor_dashboard.png` — 6-panel summary: heatmap, violins, drift bars, coverage grid, anomaly table

---

## 5. Input Data Locations (If You Want to Start From Raw Data)

If you prefer to bypass our processed results entirely and work from the raw field measurements, these are the source files:

| Data type | Path | Format | Date range | Notes |
|-----------|------|--------|------------|-------|
| **Original MLCW** (field visits only) | `data/mlcw/group_byLayer_orig/TUKU_orig_grouped.csv` | CSV, 264 rows | 2003-12-03 to 2025-10-02 | Columns: `datetime, F1, T1, F2, T2, F3, T3, F4` (note: includes T3). Units: mm, negative = compaction |
| **Reconstructed MLCW** (gap-filled) | `data/mlcw/group_byLayer_reconstr/TUKU_reconst_grouped.csv` | CSV, 1,572 rows | 2003-12-06 to 2025-10-01 | Columns: `datetime, F1, T1, F2, T2, F3, F4` (no T3). **1572 rows vs 264 field visits — 83% are computer-interpolated.** |
| **GWL at TUKU** | `data/gwl/mlcw_gwl_timeseries/TUKU_TUKU_09050331.feather` | Feather, 264 rows | 2003-12-03 to 2025-10-02 | Column: `TUKU_TUKU_09050331` (metres MSL). Well 09050331 is screened at 176–179 m depth. |
| **GPS (nearest station)** | `data/gps/modeled/` | CSV | varies | The carrier model uses a nearby GPS station (e.g., G811 or TKJS). The exact station used at TUKU is recorded in `MLCW_GPS_pairs.csv`. |
| **Borehole log** | `data/mlcw/borehole_materials/YL_WSYL23G1_TUKU_土庫.xlsx` | Excel | static | Layer boundaries, material classification (gravel/sand/silt/mud) per depth. |
| **Layer assignment** | `data/gwl/gwl_to_mlcw_layer_assignment_v4.csv` | CSV | static | Canonical GWL-to-layer mapping for all 37 stations, 195 rows. |
| **Ring-to-layer classification** | `data/mlcw/group_byLayer_orig/TUKU_classify_table.csv` | CSV | static | **AUTHORITATIVE.** The well manager's official assignment of each ring depth to F1/T1/F2/T2/F3/F4. 25 rows, 0–300 m. Verify ALL depth claims against this file. |
| **Borehole material log** | `data/mlcw/borehole_materials/YL_WSYL23G1_TUKU_土庫.xlsx` | Excel | static | **AUTHORITATIVE.** Material type at every depth interval (56 segments). SOIL_CATEGORY: 1=Gravel, 3=Sand, 5=Silt/Clay/Mud. Does NOT claim aquifer/aquitard. |

### 5.1 Data Provenance Warning

The `TUKU_reconst_grouped.csv` file (1,572 rows) is a dense, computer-generated fill. **Only 264 rows correspond to genuine field visits** where a magnetic ring was lowered into the borehole and a physical measurement was recorded. The remaining 1,308 rows are interpolated.

The `mlcw_observed_epoch_mask.csv` in Folder ABC marks which epochs are genuine. Furthermore, **all 2024+ MLCW values are 100% non-integer**, meaning they are computer-smoothed, not raw field readings (genuine magnetic-ring readings are integer millimetres). The 2024 confirmatory grades in the sequential rehearsal are therefore PROVISIONAL — the "truth" they are scored against is not field-verifiable.

We strongly recommend you verify the provenance mask against the original `TUKU_orig_grouped.csv` before trusting any metric computed on reconstructed data.

---

## 6. Suggested Verification Tests

Below is a prioritized list of tests we suggest you perform. Write your own code for each. The list goes from cheap/simple to expensive/comprehensive.

### 6.1 Cheap Tests (Do These First — One Script Each)

**T1 — Sign convention audit.** Read `reconstruction/TUKU_F1_reconstruction.csv`. Verify that `b_observed_mm` values are ≤ 0 (all compaction is negative). Verify that `d_surface_mm` values are ≤ 0 (all surface displacement is subsidence). Report any sign violations.

**T2 — Reconstruction identity check.** For each layer, verify that `b_model_mm = a_k × d_surface_mm + c_k` (ignoring the GWL term initially) on epochs where both sides are non-NaN. Compute the maximum absolute deviation. It should be zero (or machine epsilon) for F3 and F4 (which have d_k = 0). For F1/T1/F2/T2, the deviation equals `d_k × u_k(t)`.

**T3 — Σ a_k constraint.** Verify that Σ a_k ≤ 1.0 across all 6 layers. The claimed value is 0.637. Compute it yourself from the `a_k` values in the reconstruction summary JSON or directly from the CSVs.

**T4 — Provenance cross-check.** Load `mlcw_observed_epoch_mask.csv` and `data/mlcw/group_byLayer_orig/TUKU_orig_grouped.csv`. For 10 randomly sampled dates where the mask says `F2_observed = True`, verify that the corresponding value in `TUKU_orig_grouped.csv` is non-NaN. For 10 dates where the mask says `F2_observed = False`, verify that the original CSV is NaN or the date is absent.

**T5 — Cumulative residual drift direction.** Read `per_epoch_residuals.csv`. For F3, compute the cumulative sum of `residual_mm` over the blind era (post-2021-11). Is the cumulative residual monotonically increasing (model systematically underpredicting) or decreasing (overpredicting)? Report the sign and total drift in mm.

### 6.2 Medium Tests (Core Verification)

**T6 — Independent sign-error computation.** Read `reconstruction/TUKU_F3_reconstruction.csv`. Compute incremental observed as `b_observed_mm.diff()` and incremental predicted as `b_model_inc_mm`. Flag epochs where `sign(obs_inc) ≠ sign(pred_inc)` AND `abs(obs_inc) > 0.1 mm`. Compute the sign-error rate. Compare to our claim of 39.3%. If your rate differs by more than 2 percentage points, investigate why.

**T7 — Independent regime classification.** Read `timeseries/TUKU_F3_cumulative_timeseries.csv`. Compute V(t) yourself from the definition: `V(t) = min(0, cummin(H) − h_c)` where `h_c` is the preconsolidation head from `characterization/TUKU_storage_params.json`. Compare your V(t) values to the `V_m` column. Compute the fraction of epochs where V(t) < 0 (inelastic). Compare to our claim that F3 is 97% inelastic.

**T8 — Sequential rehearsal RMSE recomputation.** Read `seq/semiannual/TUKU_F2_seq_timeseries.csv` and `seq/transparency/TUKU_F2_transparency_data.csv`. At reveal dates (where `is_reveal = True`), extract `pred_mm` from the seq file and `obs_verified_mm` from the transparency file. Compute RMSE yourself. Compare to the RMSE in `seq/semiannual/metrics.json` under `layers.F2.RMSE_mm`. They should match to within 0.01 mm.

**T9 — F2/F3 anti-phase independent verification.** For all epochs where both F2 and F3 have `abs(obs_inc) > 0.1 mm`, compute the fraction where `sign(F2_obs_inc) ≠ sign(F3_obs_inc)`. Compare to our claim of 23.5%. Note: this metric must be computed on INCREMENTAL (not cumulative) values.

### 6.3 Expensive Tests (Structural Verification)

**T10 — Walk-forward reconstruction from scratch.** Using only `TUKU_orig_grouped.csv` (264 genuine field visits), implement the carrier model `b_k(t) = a_k × d_GPS(t) + c_k` yourself. Fit `a_k` and `c_k` on the first 80% of genuine visits. Predict the last 20% (held-out). Compute RMSE on the held-out visits. Compare to the calibration RMSE in the reconstruction summary.

**T11 — Sequential rehearsal from scratch.** Implement a simplified walk-forward: (a) fit carrier model on 2010–2014 data only, (b) at each subsequent visit date, predict the next value before revealing it, update the model level, repeat, (c) score the tail. Compare your walk-forward RMSE to the `seq/semiannual/metrics.json` per-layer RMSE.

**T12 — Storage coefficient recomputation.** Read `timeseries/TUKU_F2_cumulative_timeseries.csv`. Using the cumulative two-regressor equation `b(t) = S_ke × H(t) + (S_kv − S_ke) × V(t) + c`, solve for S_ke and S_kv via constrained NNLS (S_ke ≥ 0, S_kv ≥ S_ke). Compare to the values in `characterization/TUKU_storage_params.json`.

### 6.4 Guardrails Audit — `scripts/guardrails.py`

The file `scripts/guardrails.py` (601 lines) enforces 10 automated physical-law checks derived from Hung et al. (2021) and the project's CLAUDE.md halt table. We suspect it may have problems that prevent good results from passing validation. **We ask you to audit this file specifically.**

#### 6.4.1 How guardrails.py is Supposed to Work

```
Fitted parameters (S_ke, S_kv, tau, r2, etc.)
    ↓
validate_layer_params(S_ke, S_kv, layer, station, fan_zone, material, ...)
    ↓
Runs 10 checks:
  1. Sign constraints (S_ke ≥ 0, S_kv ≥ S_ke) — HALT on failure
  2. Literature bounds (±10× from Hung et al. 2021) — WARN
  3. Ratio gate (S_skv/S_ske ∈ [3, 50]) — WARN
  4. Virgin term monotonicity — HALT
  5. Data sufficiency (n ≥ 10) — WARN
  6. GWL sign convention — HALT
  7. Preconsolidation head window (Bug F fix) — HALT
  8. Tau bounds (0 ≤ τ ≤ 120) — HALT
  9. Clay-layer behavior check — WARN
  10. R² sanity — WARN
    ↓
LayerValidationResult(passed, errors, warnings)
```

#### 6.4.2 Specific Issues We Want You To Investigate

We have identified the following potential problems. **Verify each one independently** and report whether it is real (confirm with evidence), partially real (confirm with caveats), or a false alarm (refute with evidence).

| # | Issue | Location (line) | What to check | Suspected consequence |
|---|-------|-----------------|---------------|---------------------|
| **G1** | **S_ke-to-S_ske conversion skipped when `material=None`** | L491–497 | Check `tau_demo_TUKU/15_storage_characterization.py` — does it call `validate_layer_params` without passing `material`? If so, checks 2 (literature bounds), 3 (ratio gate), and 9 (clay behavior) are silently skipped for the main parameter characterization pipeline. | **High.** The parameter characterization results in `characterization/TUKU_storage_params.json` were validated with only sign-constraint checks active. Literature-bounds and ratio-gate checks were never run on the production output. |
| **G2** | **Only TUKU has material definitions** | L77–84 | 32 borehole log files exist at `data/mlcw/borehole_materials/` but are unparsed. All 36 non-TUKU stations have `material=None`, disabling checks 2, 3, and 9 for the entire multi-station pipeline. | **High.** The full guardrail suite has never been applied to any station except TUKU. The Part 2 (37-station) pipeline will run with only sign-constraint checks active — physical-law violations at other stations will be silently accepted. |
| **G3** | **Strict inequality `S_ske_m1 < 1e-15` misses boundary** | L210 | For S_ke = 1e-10 mm/m and total_m = 100 m, S_ske_m1 = 1e-15 exactly. This fails `S_ske_m1 < 1e-15`, the ratio is computed as S_skv / S_ske → explodes past 50×, and a misleading warning fires ("inelastic storage implausibly large"). | **Medium.** False-positive ratio warning for layers with tiny-but-nonzero elastic storage. The real problem is elastic storage is effectively zero, not that inelastic is large. |
| **G4** | **F4 S_ke=0 bypasses clay-layer check** | L418–420 | F4 at TUKU is 100% fine-grained (`is_clay_dominated=True`). The clay check fires only when `S_ke > 1e-10`. When S_ke = 0 (as for F4), the guard skips the check entirely, and F4 passes without warning. | **Medium.** False negative. A 100% clay layer with zero elastic storage should at minimum trigger a diagnostic note, not silent acceptance. |
| **G5** | **Proximal fan S_skv silently accepted** | L45, 173 | Proximal fan prior has `S_skv_m1=None` (no inelastic expected for gravel-dominated zones). The literature check skips S_skv for proximal stations. A proximal station producing large S_kv would pass with no warning from the literature-bounds function. | **Medium.** Only the ratio gate could catch this (if material is provided and S_ke is non-zero). With G1 and G2 both active (material not provided), this becomes a silent false negative. |
| **G6** | **β (delta) never explicitly checked or named** | L113, 126–130 | CLAUDE.md lists β ≥ 0 as a co-equal halt rule alongside S_ske ≥ 0. The code enforces it implicitly via S_kv ≥ S_ke (which implies δ = S_kv − S_ke ≥ 0), but the error message says "S_kv < S_ke" — it never mentions beta or delta. Someone scanning reports for "beta" will miss violations. | **Low.** The check works but is invisible in reports. |
| **G7** | **NaN in V(t) invisible to monotonicity check** | L250, 256 | `validate_virgin_term` checks `np.any(V_arr > 1e-10)` and `np.any(diffs > 1e-10)`. NaN comparisons always return False in numpy — positive V(t) values or increasing diffs at NaN positions are silently invisible. | **Medium.** If data gaps produce NaN in the virgin term array, violations at those positions are not detected. |
| **G8** | **`np.errstate(invalid="ignore")` has no effect** | L503 | The context manager wraps pure-Python float operations (ratios of Python floats). NumPy error state settings do not affect Python float arithmetic. A future code change adding unprotected numpy operations inside this block would have errors silently suppressed. | **Low.** Currently a no-op, but masks future bugs. |
| **G9** | **Docstring says S_ske, parameter is S_ke** | L113–118 | The error message reports "S_ke = [value] is NEGATIVE" in unspecified units (mm/m). CLAUDE.md halt table specifies the format: "S_ske = [value] is negative — layer rejected" (in m⁻¹). The output does not match the specification. | **Low.** Confusion during debugging but no functional impact. |
| **G10** | **Hardcoded CRAF-specific values not parameterized** | L315, 336, 363 | Head range [−100, +200] m MSL, REF_DATE=2015-01-16, TAU_MAX=120 are hardcoded. Wrong for other basins. | **Low.** Acceptable for CRAF-only use, but undocumented as basin-specific. |

#### 6.4.3 Guardrails Verification Tests

**G-T1 — Reproduce the material=None skip.** Write a test script that calls `validate_layer_params` with and without `material=TUKU_MATERIALS.get("F2")`. With material: confirm that `validate_literature_bounds` and `validate_ratio_gate` appear in the warnings list. Without material: confirm they are absent. Report the exact warnings emitted in each case.

**G-T2 — Reproduce the ratio explosion.** Set S_ke = 1e-10 mm/m, S_kv = 1e-3 mm/m, total_m = 100 m, aquitard_m = 50 m. Compute S_ske_m1 = 1e-15. Call `validate_ratio_gate(S_ske_m1=1e-15, S_skv_m1=2e-8)`. Confirm whether it falsely warns about "inelastic storage implausibly large."

**G-T3 — Test F4 with S_ke=0 against clay check.** Call `validate_clay_layer_behavior(S_ke=0.0, S_kv=8.695, n_inelastic=224, n_total=772, layer="F4", is_clay_dominated=True)`. Confirm whether any warning is emitted. You should expect at minimum an informational note that a 100% clay layer has zero elastic storage.

**G-T4 — Scan for callers that omit material.** Grep the codebase for `validate_layer_params` calls. List every file that calls it, and whether `material=` is passed. The finding from our preliminary scan: `tau_demo_TUKU/15_storage_characterization.py` (the main parameter characterization) calls it without material. Verify and report any others.

**G-T5 — Check non-TUKU station coverage.** Count how many stations have material definitions in the codebase (hint: only TUKU). Count how many borehole log files exist at `data/mlcw/borehole_materials/`. Report the gap. This is a scalability bug — the guardrail is effectively TUKU-only.

**G-T6 — V(t) NaN sensitivity.** Construct a V_arr containing [0, −0.1, −0.2, NaN, NaN, −0.5, −0.4] where the jump from −0.5 to −0.4 is an increase (violation). Call `validate_virgin_term`. Confirm whether the NaN-block hides the violation.

### 6.5 Comparative Methods Check

Our model is a GPS surface carrier with an optional GWL residual term. It is simple by design — simplicity survived where complexity failed. But simplicity also means we may be missing dynamics that a different model class would capture. **Compare our results against at least one structurally different method from the literature.**

| Method | Paper | Key difference from ours | What to test |
|--------|-------|-------------------------|--------------|
| **Visco-elasto-plastic (VEP)** | Tsai and Hsu (2018) | Includes viscous creep dampers — captures time-dependent delayed compaction that our instantaneous elastic/inelastic misses | Check if our F3/F4 residual shows a creep-like pattern (monotonic drift without seasonal structure). If so, VEP may be the right model for deep clay. |
| **Statistical head-rule** | Tatas and Chu (2024) | Classifies elastic/inelastic by a statistical threshold ($h^* = \text{AVE} - \alpha \cdot \text{SD}$) rather than the running-minimum preconsolidation head our method uses | Compute the Tatas-Chu h* threshold for TUKU using the GWL data in `data/gwl/mlcw_gwl_timeseries/TUKU_TUKU_09050331.feather`. Compare to our h_c values in `characterization/TUKU_storage_params.json`. Do they agree? |
| **ML decomposition (Random Forest)** | Patra et al. (2025) | ML-based trend/seasonality separation without any physics equations | Compare our carrier-model seasonal amplitude against a simple STL decomposition of the MLCW data. Does our model capture the seasonal component at the right phase? |
| **EOF decomposition** | Chu et al. (2024) | Data-driven spatial modes — 97.5% trend, 1.7% seasonal, 0.4% intra-seasonal variance | Compare our per-layer a_k values to the Chu et al. per-layer compaction budget. Our a_k sum to 0.637 (not 1.0) and F3 gets the largest share (0.306) while literature says F2 dominates (57.3%). Investigate whether our a_k distribution is physically defensible or indicates a structural model error. |

**Minimum deliverable for this section:** Pick one of the four comparisons above, implement it in code, and report whether our model's behavior is consistent with or contradicted by the independent method. If you find a contradiction, state which method you believe is correct and why.

---

## 7. What We Do NOT Want You To Do

1. **Do not trust our diagnostic CSV columns without verification.** The `sign_error`, `expected_sign_match`, `regime`, and `error_type` columns in Folder XYZ were computed by our script. They may contain bugs. Recompute at least one of them independently.

2. **Do not score against dense-filled data without checking provenance.** The `TUKU_reconst_grouped.csv` (1,572 rows) is 83% interpolated. If you fit and score on this file without filtering to genuine visits only, your metrics will be inflated.

3. **Do not use random k-fold cross-validation.** The temporal structure matters. Always use forward-chronological splits (train on early years, test on later years). The earliest hold-out year must be reported separately.

4. **Do not negate the GWL head.** `dh_raw = H(t) − H(t_ref)`. If head fell, this value is negative. Do not multiply by −1.

5. **Do not accept the 2024 confirmatory grades as ground truth.** All 2024 MLCW values in the dense-filled files are non-integer (computer-smoothed). Genuine magnetic-ring readings are integer millimetres.

6. **Do not trust the guardrails to have caught everything.** `scripts/guardrails.py` has known gaps (see §6.4). In particular, the `material` parameter was not passed by the main parameter characterization script, disabling 3 of 10 checks. If you find a physically implausible parameter value, check whether guardrails would have caught it — and whether it did.

7. **Do not repeat depth claims from discussion documents without verification.** The claim "F3 is at 238–275 m, well screened 79 m above" in `discussions/F3_FORENSIC_VERDICT_20260612.md` and `CLAUDE.md` was NOT verified against the well manager's `TUKU_classify_table.csv`. The correct F3 range is 172.9–272.7 m. See §2.6 for the full correction. Any depth claim you encounter in a `.md` file must be cross-checked against the classify table and borehole log before you treat it as fact.

---

## 8. How To Report Your Findings

We request a structured report with these sections:

1. **Tests passed without modification** — which of our claims you verified and confirmed (from T1–T12, G-T1–G-T6, and the comparative methods check).
2. **Tests passed with minor corrections** — claims that hold after fixing a sign error, off-by-one, or unit conversion.
3. **Tests failed** — claims that do NOT hold. Include the code snippet that demonstrates the failure, the specific file and row numbers, and the corrected value.
4. **Guardrails audit findings** — for each of the 10 issues listed in §6.4.2, state: CONFIRMED (with evidence), PARTIAL (with caveats), or REFUTED (with evidence). For any NEW guardrails issues you discover beyond our list, describe them with line numbers and severity.
5. **Comparative methods findings** — which alternative method you tested against ours, and whether our model's behavior is consistent with or contradicted by the independent method.
6. **New anomalies discovered** — patterns you found that are NOT flagged in our diagnostic exports.
7. **Data quality issues** — any problems with the input data itself (inconsistent dates, missing values, suspect measurements).

We value false-positive reports (our diagnostic flagged something that is actually fine) equally with false-negative reports (our diagnostic missed something real).

---

## 9. Quick-Start Script Template

```python
"""Minimal auditor verification script — adapt and extend freely."""
import pandas as pd
import numpy as np
import json
from pathlib import Path

RESULTS = Path("tau_demo_TUKU/results")
DATA = Path("data/mlcw/group_byLayer_orig")
LAYERS = ["F1", "T1", "F2", "T2", "F3", "F4"]

# --- T1: Sign convention check ---
df = pd.read_csv(RESULTS / "reconstruction/TUKU_F1_reconstruction.csv", parse_dates=["date"])
assert (df["b_observed_mm"].dropna() <= 0).all(), "F1 b_observed_mm has positive values!"
assert (df["b_model_mm"].dropna() <= 0).all(), "F1 b_model_mm has positive values!"
print("T1 PASS: F1 sign conventions hold")

# --- T2: Reconstruction identity ---
carrier_summary = json.load(open(RESULTS / "reconstruction/TUKU_carrier_reconstruction_summary.json"))
for layer in LAYERS:
    ld = carrier_summary["per_layer"][layer]
    a_k, c_k = ld["a_k"], ld["c_k"]
    df = pd.read_csv(RESULTS / f"reconstruction/TUKU_{layer}_reconstruction.csv", parse_dates=["date"])
    valid = df["d_surface_mm"].notna() & df["b_model_mm"].notna()
    predicted = a_k * df.loc[valid, "d_surface_mm"] + c_k
    actual = df.loc[valid, "b_model_mm"]
    deviation = (predicted - actual).abs()
    print(f"T2 {layer}: max |a_k·d_GPS + c_k − b_model| = {deviation.max():.6f} mm")

# --- T3: Sum a_k ---
sum_a = sum(carrier_summary["per_layer"][l]["a_k"] for l in LAYERS)
print(f"T3: Σ a_k = {sum_a:.4f} (claimed 0.637, ≤ 1.0: {sum_a <= 1.0})")

# --- T6: Independent sign-error rate for F3 ---
df3 = pd.read_csv(RESULTS / "reconstruction/TUKU_F3_reconstruction.csv", parse_dates=["date"])
obs_inc = df3["b_observed_mm"].diff()
pred_inc = df3["b_model_inc_mm"]
sign_err = (np.sign(obs_inc) != np.sign(pred_inc)) & (obs_inc.abs() > 0.1)
rate = sign_err.sum() / max(sign_err.notna().sum(), 1)
print(f"T6 F3: sign-error rate = {rate:.1%} (our claim: 39.3%)")

print("\nAudit template complete. Extend with T4–T12 as needed.")
```

Save this as your starting point. Modify, extend, and add adversarial checks freely.

---

## 10. Contact and Context

This project is at a decision gate (2026-06-12). Part 1 (TUKU pilot) is technically complete, but three strategic decisions are blocked pending human review. Your independent audit will directly inform whether we:

- (a) Restrict the deployable claim to trend + datum + partial F2 dynamics
- (b) Move F3/F4 to a separate track requiring monthly-cadence in-situ visits
- (c) Authorize Part 2 (37-station extension) and Part 3 (8,577 grid point prediction)

Full project context: `PROGRESS.md`, `CLAUDE.md`, and the discussions cited in the file headers of Folder ABC's JSON outputs.
