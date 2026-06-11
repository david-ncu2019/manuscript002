# Super Plan 2026-06-11 — Single-Well Sequential Estimation (TUKU): De-Leak, Re-Baseline, Rehearse Sampling Decay, Deploy GPS-Only

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to execute this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the TUKU pilot from an in-sample reconstruction demonstration into an honest, deployable single-well sequential estimator — predict, reveal a sparse observation, adjust, repeat — with guaranteed-coverage uncertainty bands and a quantified answer to "how infrequently can the well be visited and still meet the accuracy targets," then run the GPS-only first pass across all mapped stations.

**Method structure:** Frozen-structure per-layer model (carrier share + two-regime Terzaghi/Riley head response), calibrated once on the dense era, then driven forward blind with discrete bias re-anchoring at scheduled "visits," wrapped in split-conformal prediction intervals.

**Tech stack:** Python 3.12 (`fafalab2` conda env), numpy / pandas / scipy / matplotlib / pyarrow. Run template (PowerShell): `$env:PYTHONPATH=""; conda run -n fafalab2 python <script>`

> **Status:** ACTIVE. Supersedes `super_plan_2026-06-10.md` for all unfinished work. The 06-10
> plan's M1–M4 results are KEPT as evidence (verified complete on disk by the 2026-06-11 audit,
> checkboxes reconciled) but its M3 hybrid registry is FROZEN — it is superseded for deployment
> by the fixed-structure model of this plan (§2, Assumption A2), because its selection procedure
> leaked (§0, finding L2).
>
> **Audience:** a junior AI agent. Every step is written so nothing must be guessed. Where a
> number is expected, the expected number is stated. Follow steps in order. Do not skip gates.

---

## 0. Why This Plan Exists — The 2026-06-11 Audit Findings

**Physical story first.** The TUKU compaction well measures how six sediment layers (F1, T1, F2,
T2, F3, F4; 0–300 m) squeeze as confined-aquifer head falls. The mission is to keep estimating
that layer-by-layer record after the well's sampling decays from monthly toward annual. The
2026-06-10 work produced correct-looking curves, but the audit found the curves were fitted on
the very record they claim to reconstruct, the model menu was selected on the epochs it was
graded on, no experiment yet simulates the sampling decay that motivates the whole project, and
the predictions carry only a fraction of the observed sub-annual motion.

**Confirmed findings (each traced to code/files on disk on 2026-06-11; numeric evidence persisted
in `tau_demo_TUKU/results/audit_20260611_leakage_amplitude.json`):**

| # | Finding | Evidence | Consequence |
|---|---------|----------|-------------|
| L1 | **Headline reconstruction is IN-SAMPLE.** The calibration mask in `tau_demo_TUKU/14_carrier_reconstruction_tuku.py` (lines 197–199, 209–268) has no date split: `valid = isfinite(b) & isfinite(d)` selects ALL 1,081 GPS+MLCW epochs (823 for F2). The `b_model_mm` column of the six reconstruction CSVs is the full-record fit evaluated everywhere. Only the 36-epoch `tail_evaluation` block is train-only (lines 588–628). | Script 14 L197–268 | The published curve demonstrates correlation, not gap-fill ability. All headline R²/RMSE (e.g., F2 R²=0.991) are calibration wallpaper under Do-Not-Regress rule 4. |
| L2 | **M3 hybrid selection LEAKED.** `17_hybrid_model_m3.py`: per-design refits are clean (L339–341), but the adoption rule (L376–405) picks the lowest mean held-out RMSE over the three designs and reports exactly those RMSEs as the winner's skill (L409–410). No outer holdout. Final registry coefficients are refit on the FULL record (L366). | Script 17 L339–410 | The adopted-model skill numbers are optimistically biased. M4 re-scores the same leak (Script 18 L109–125 reads the leaked registry). |
| L3 | **Sampling decay is not rehearsed anywhere.** All holdouts are contiguous blocks (middle 40–70%, end 30%, 36-epoch tail). No artifact decimates MLCW to monthly/semi-annual/annual. Old Task 5.2 never ran. | Script 17 L210–225; results/ census | The project's stated mission — survive monthly→annual sampling decay (`CLAUDE.md:33`, `README.md:8`) — has zero supporting evidence. |
| P1 | **The "continuous" MLCW input is partly synthetic — RESOLVED by Task 6.5 (2026-06-11).** `data/mlcw/group_byLayer_reconstr/TUKU_reconst_grouped.csv` (1,572 rows, ZERO NaN, 5-day cadence) is a smooth **non-linear** reconstruction. The 6.5 provenance audit (`tau_demo_TUKU/results/mlcw_provenance_audit.json`) located the GENUINE source: `data/mlcw/group_byLayer_orig/TUKU_orig_grouped.csv` = **264 real field visits** at irregular dates (2003-12-03 → 2025-10-02), columns `datetime,F1,T1,F2,T2,F3,T3,F4` (T3 mostly NaN at TUKU — ignore); and the per-ring original `data/mlcw/raw_timeseries/TUKU_ringbyring.csv`. The real cadence already decays monthly→annual — the sampling-decay premise is in the data itself. | `mlcw_provenance_audit.json` verdict (i) | M8 now draws "visits" and grades against the 264 GENUINE observations, not the smooth fill. Assumption A8 is downgraded from "synthetic truth of unknown composition" to "dense fill used only as a smooth prior/visualization; truth = the 264 genuine visits." |
| A1 | **Amplitude/dynamics deficit, quantified.** Detrended model std is 26–73% of observed in every layer. Detrended obs-vs-pred Pearson r: F1 0.467, T1 0.517, F2 0.676, T2 0.418, **F3 −0.086**, F4 0.165. Increment-std ratio pred/obs: F1 0.41, T1 1.00, F2 1.01, T2 1.48, F3 1.49, F4 0.77 (T2/F3 inject head wiggle that is not the layer's wiggle; F1/F4 are too quiet). | audit JSON `per_layer` | The model misses the dynamic response. F3 — carrying 435 mm of the 555 mm column total — is essentially uncorrelated with observed sub-annual motion. Fix via §2 A2/A4 + new mandatory metrics (Rule V2). |
| V1 | **Visualization debt.** The six PNGs in `tau_demo_TUKU/results/visualization/` (12:56–13:42) predate the 18:55 lag repair and contradict the JSONs beside them. No hybrid (M3) figure or per-epoch CSV exists. `visualize_observed_vs_predicted.py` plots the carrier curve while its annotation quotes the hybrid verdicts (mislabeled). | file mtimes; Script 17 single `json.dump` L484 | Any human validator looking at the figures is looking at the wrong run. |
| G1 | **Ledger gaps from 06-10 (PARTIAL items):** 2.1.2 carrier-equivalence check not persisted as a file; 2.2.4 F1/T1 hypotheses (b) wrong-τ and (c) elastic-dominated never tested; 2.4.2 no machine-readable `decision_point_2` field; Script 13 hardcodes `metadata.date = "2026-06-09"` (L570/573). | 06-11 completion audit | Closed by M6. |

**What survives and is kept:** all five M1 repairs (lag invariant, crash, gap-aware cumsum, real
future head, identifiability); the M2 physics table (F2 $S_{skv} = 1.34 \times 10^{-3}$ m⁻¹ vs
Hung et al. $1.33 \times 10^{-3}$, fitted at correct $\tau = 72$); DP1 = CARRIER-PRIMARY (the
carrier-vs-baseline comparison was lag-free on both arms); the three-design holdout machinery
as *diagnostic* tooling; the guardrail system.

---

## 1. Feasibility Verdict (mandated deep-reasoning session A, 12 steps, 2026-06-11)

**VERDICT: estimating six-layer compaction *dynamics* from total surface deformation alone is
fundamentally impossible — not merely difficult. Estimating the six-layer *secular trend* from
surface deformation is feasible and validated. The deployable method therefore needs three
information sources, each doing the only job it can do: surface displacement carries the trend,
per-layer groundwater head carries the dynamics, sparse well visits carry the datum.**

Hydrogeological and mathematical justification (each point is a physical statement, not an
opinion):

1. **Rank deficiency.** Each epoch provides ONE observed number $d(t)$ and demands SIX unknowns
   $b_k(t)$ (plus a deep-compaction residual). The epoch-wise system has a 6-dimensional null
   space. Every regressor derived from $d(t)$ — lags, filters, harmonics of $d$ — lives in the
   one-dimensional signal space of $d$; adding them adds variance capacity, never information.
   That is the definition of overfitting, and the repo's own history (methods twice promoted on
   in-sample fit) shows it happening.
2. **Superposition destroys phase.** The layers respond to head with different consolidation
   lags (fitted: F1 $\tau=6$, T1 0, F2 72, T2 72, F3 120 epochs — F3 at the search boundary,
   so its true lag is ≥ 600 days; Terzaghi $t_{90}$ for F3's 77 m of clay is years to decades).
   The surface sums these mutually phase-shifted components; two same-frequency components
   cannot be un-added from their sum. More surface epochs do not restore the lost dimensions.
3. **The amplitude-bound lemma (measured at TUKU, 2026-06-10 verified facts).** Observed F2
   seasonal amplitude is 4.52 mm; the total surface seasonal amplitude is 3.7 mm. For any
   constant non-negative share $a_k \le 1$: amplitude$(a_k \cdot d_{seasonal}) \le 3.7$ mm
   $< 4.52$ mm. No constant apportionment can reproduce F2's seasonal cycle even in the
   noiseless limit, because shallow elastic rebound and deep lagged compaction partially cancel
   at the surface. The surface seasonal signal is a *biased* estimator of column seasonal
   activity. This lemma is publishable as the formal reason head data is necessary, not optional.
4. **Empirical confirmation.** Despite cumulative calibration R² up to 0.991, the detrended
   prediction correlates with the detrended observation at r = −0.086 for F3 (finding A1). High
   cumulative R² with zero dynamic correlation is exactly what theory predicts for a
   trend-only information channel.
5. **What the carrier provably CAN do.** At low frequency the stress regime is quasi-stationary,
   layer trends are quasi-proportional, and constant shares $a_k$ transfer the trend with < 1%
   error (Part 1, verified). Middle-gap RMSE 1.1–7.3 mm confirms trend-band transfer.
6. **What breaks the degeneracy.** Per-layer screened piezometers add up to six independent
   drivers (the actual stress on each layer) — restoring rank through physics, with 2–3
   parameters per layer (Terzaghi/Riley structure). Sparse direct MLCW observations re-anchor
   each layer's datum — one visit pins one integration constant, which is why even annual
   sampling has high value. Borehole stratigraphy fixes which layers may compact inelastically.
7. **Honest ceiling per layer (error budget between annual visits):** thin layers ±2–4 mm,
   F2 ±4–7 mm, F3 ±15–30 mm and growing with drought activity. The Level-1 thresholds are
   reachable for five layers; F3 is genuinely at risk — consistent with the M4 verdict (5/6).
   F3's remedies are physical, not statistical: longer τ search window (it saturated at the
   120-epoch cap) and drought-exceedance driving — never more free parameters.

**Decision (DP-SCOPE, issued by this plan, flagged for human ratification):** abandon the
generalized "decompose the surface into six layers" framing. The project's claim becomes:
*at a single instrumented well, surface displacement + per-layer head + sparse visits maintain
layer-wise compaction estimates within stated uncertainty at a fraction of the monitoring
budget.* Reducing the monitoring budget for even one well is the novelty contribution.

**M7 amendment (2026-06-11, GATE M7 — `simple_ratio_summary.json`, both GPS variants):** the
detrended GPS→layer cross-correlation test was run as a direct empirical check of point 4. It
CONFIRMS and STRENGTHENS the verdict. With the smooth `modeled` GPS (an upper bound, since the
MLCW series is itself a smooth non-linear fill): F1 r=0.44 @ −340 d, T1 r=0.42 @ −5 d, F3
**r=0.22 @ −600 d** (the search boundary, with negative detrended r² = −0.24 → flatly
uncorrelated), F4 r=0.30 @ −285 d. Two layers nominally cross |r|≥0.5 — F2 (r=−0.51 @ +480 d)
and T2 (r=−0.69 @ −470 d) — but BOTH at multi-year lags with WRONG-SIGN (negative) ratios. A
causal layer→surface relationship must have a lag near 0 (the surface is the contemporaneous sum
of layer compactions); a best correlation at ±1.3 years with anti-phase sign is slow secular
residual left after a single linear detrend, not sub-annual information transfer. The truer
`orig_nojump` GPS is uniformly 0.04–0.20 r-units lower (F2 0.46, T2 0.49 — both fall back below
0.5). Net: no layer's sub-annual dynamics are carried by the surface GPS at a physical lag. The
impossibility verdict stands; head data remains necessary, not optional.

---

## 2. Simplifying Assumptions (mandated deep-reasoning session B, 11 steps, 2026-06-11)

Each assumption states: the physical justification, the symptom of violation, and the test.
These go into the methods section of the manuscript verbatim.

| # | Assumption | Justification | Violation symptom | Test |
|---|------------|---------------|-------------------|------|
| A1 | **Constant apportionment shares $a_k$** over the deployment horizon (~5 yr). | Mid-fan pumping regime is structurally stable (agricultural seasonal cycle on a slow decline); one $a_k$ per layer fit 15 yr of trend with <1% error. | Monotone same-sign innovations at successive visits. | Fit $a_k$ on each half of the dense era; compare. |
| A2 | **One fixed model structure for every layer** — $b_k = c_k + a_k d(t) + S_{ke,k}\,u_k(t-\tau_k) + S_{kv,k}\,V_k(t-\tau_k)$ with $a_k, S_{ke}, S_{kv} \ge 0$; terms drop to 0 only via the M1.5 identifiability rule (a data-degeneracy report, not model shopping). | Terzaghi (1925) elastic + Riley (1969) preconsolidation exceedance — the standard model for this basin (Hung et al. 2021). Replaces the leaked M3 candidate menu and honors the project's "no per-station model selection" constraint. | Detrended residual still correlates with $u$ after fit. | VIF guard + 4-condition identifiability (built in M1.5). |
| A3 | **Frozen dynamics, live level.** After dense-era calibration, $(a_k, S_{ke}, S_{kv}, \tau_k)$ are FROZEN; only a per-layer bias $\beta_k$ updates at each visit (optional slow rate correction $\gamma_k$ after ≥3 visits, default OFF). | Storage coefficients are material constants; refitting slopes from 1–2 points is statistically meaningless (annual cadence = 1 datum/yr/layer). | Innovation sequence not zero-mean white. | One-sided CUSUM on innovations; trigger = "regime change — human review before any slope refit." |
| A4 | **Seasonality comes from head, not from a free oscillator.** The $S_{ke} u(t-\tau)$ term carries the annual cycle (head itself is seasonal). A fixed-amplitude annual harmonic is permitted ONLY if the head term demonstrably cannot reproduce the observed seasonal amplitude, and its amplitude/phase are then estimated once on the dense era and frozen. | Monsoon/irrigation forcing is annually periodic; ties the seasonal band to a measured driver instead of a fitted curve (the M3 H2 harmonic was fitted to MLCW itself — that is how the leak manufactured r=0.983). | Growing seasonal-phase mismatch at sub-annual visits. | Calibrate pre-2017, check seasonal amplitude 2017–2018. |
| A5 | **Explicit deep-residual closure:** $\sum_k a_k \le 1$; the residual share $(1-\sum a_k)\,d$ is attributed to compaction below 300 m + tectonics, reported, never decomposed. | $\sum a_k = 0.637$ fitted at TUKU; literature: ~30–40% of Yunlin subsidence originates below 300 m. Prevents shallow layers from absorbing deep signal. | $\sum a_k$ drifting to the bound 1. | Report $\sum a_k$ with its fit covariance. |
| A6 | **Measurement-error model:** MLCW reading error ~0.1–0.5 mm (ring extensometer class) ≪ model forecast error ⇒ the visit update is a hard level reset: $\beta_k \leftarrow \beta_k + e$ where $e$ = innovation. GPS daily vertical noise 3–5 mm (5-day median ⇒ ~2 mm); GWL head ~0.01 m. | Instrument specs. Kalman gain ≈ 1 for the level state collapses the filter to "reset bias at each visit" — simple enough to explain to a water-resources agency. | — | Stated, not fitted. |
| A7 | **No unmodeled steps inside an inter-visit interval.** GPS jump screening exists upstream (`orig` vs `orig_nojump` columns); flag any single-epoch carrier move > 5× carrier noise; GWL screened likewise. | Central-Taiwan coseismic offsets would otherwise be silently booked as compaction. | Step flag epoch. | Automatic flag in the walk-forward engine. |
| A8 | **The dense MLCW reconstruction is treated as truth ONLY for calibration/grading, with its synthetic-content caveat stated**, and the provenance audit (Task 6.5) must attempt to recover the genuinely-observed epoch mask. | Finding P1: `TUKU_reconst_grouped.csv` has zero NaN and no provenance flag. | — | Task 6.5; if raw epochs are unrecoverable, A8 is a permanent documented limitation. |

**Binding export rule (Rule V — applies to EVERY task in this plan that produces or evaluates a
reconstructed MLCW timeseries):** each such task must persist (1) per-epoch CSV (observed,
predicted, residual, flags), (2) a JSON with comprehensive evaluation metrics, and (3) PNG
figures. Figure standards (mandatory): font ≥ 14 pt, tab10/ColorBrewer colors, every axis
labeled with units, grid on, tight layout, 300 dpi.

**Binding metric rule (Rule V2 — the amplitude fix made permanent):** every evaluation JSON must
contain, per layer, besides MAE/RMSE/skill: `amplitude_ratio_increments` = std(Δpred)/std(Δobs)
(target band [0.7, 1.3]), `detrended_corr` (target ≥ 0.4 where the layer's detrended std
> 2 mm), `detrended_std_obs_mm`, `detrended_std_pred_mm`. A model that nails RMSE while flat-lining
the dynamics is no longer reportable as a success.

---

## 3. Level 1 — The Apex Goal (v2, pivoted scope)

**At TUKU, run the sequential protocol — calibrate dense (2010–2018), walk forward blind
(2019–2024) receiving observations only at scheduled visits — and deliver, per layer:**

1. Out-of-sample MAE and RMSE per visit cadence (monthly, quarterly, semi-annual, annual,
   none, 2-yr-blackout-then-annual) against the thresholds: thin layers (F1, T1, T2, F4)
   MAE < 5 mm, RMSE < 10 mm; thick aquifers (F2, F3) MAE < 10 mm, RMSE < 20 mm.
2. The **minimum cadence** at which each layer still meets its thresholds — the budget
   recommendation to the well operator.
3. 90% conformal prediction bands whose empirical coverage on the untouched confirmatory year
   (2024) is ≥ 0.85.
4. Dynamics fidelity per Rule V2.

**Binding rules:** held-out only (calibration metrics never satisfy the goal); every number
traceable to a persisted file; physics gates bind ($S_{ke}, S_{kv} \ge 0$, $V$ monotone
non-increasing, identifiability rules); the 2024 confirmatory year is graded exactly once,
after all development ends.

---

## Level 2 — Milestones

| Milestone | Name | Purpose | Gate |
|-----------|------|---------|------|
| **M6** | Close out the 06-10 ledger | Persist the 3 PARTIAL items, clear the visualization debt, audit MLCW provenance | All G1/V1/P1 items persisted |
| **M7** | Simple ratio test + carrier information audit | The user's detrend→xcorr→shift→ratio idea, executed as the formal measurement of how much layer dynamics the GPS contains | Results persisted; feasibility §1 confirmed or amended |
| **M8** | Sequential assimilation rehearsal at TUKU | The pivot: predict→reveal→adjust at six cadences; conformal uncertainty; cadence-degradation curve; confirmatory 2024 | DP-SEQ issued from persisted files |
| **M9** | GPS-only multi-station deployment (M5 reborn) | Run the deployable carrier method at every mapped station via `m5_deployment/station_file_map.json`; **GPS only, NO InSAR** | Portfolio summary persisted |

**Hard stop after M9.** The InSAR-carrier rehearsal (old Task 5.1) is PARKED: the routing file
maps `data/insar/mlcw_interp_insar_IDW_extend.feather`, but the human has mandated GPS-only for
this phase; do not load any InSAR file in any M6–M9 task.

---

## Level 3/4 — Tasks and Micro-Steps

### MILESTONE M6 — Close Out the 06-10 Ledger

**Physical narrative:** before building anything new, finish the bookkeeping the 06-10 session
left open, so that every decision traces to a machine-readable field and every figure on disk
shows the repaired run, not the bent-ruler run.

#### TASK 6.1 — Persist the equivalence check and the decision-point fields (closes 2.1.2 + 2.4.2)

**Files:**
- Create: `tau_demo_TUKU/20_m2_closeout.py`
- Modify: `tau_demo_TUKU/13_holdout_method_bakeoff.py` (metadata lines ~570–573 only)
- Output: `tau_demo_TUKU/results/m2_closeout.json`

- [x] **6.1.1** Archive the stale pre-repair visualization table BEFORE it gets regenerated
  (it is the only persisted copy of the pre-repair carrier numbers):

```powershell
Copy-Item tau_demo_TUKU\results\visualization\holdout_bakeoff_table.csv `
          tau_demo_TUKU\results\visualization\holdout_bakeoff_table_OBSOLETE_prerepair_20260610.csv
```

- [x] **6.1.2** Write `tau_demo_TUKU/20_m2_closeout.py`:

```python
#!/usr/bin/env python
"""20_m2_closeout.py — persist the M2 equivalence check + machine-readable DP1/DP2 fields.
Closes super_plan_2026-06-10 items 2.1.2 and 2.4.2. Read-only on inputs; writes one JSON.
Run: $env:PYTHONPATH=""; conda run -n fafalab2 python tau_demo_TUKU/20_m2_closeout.py
"""
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent / "results"
bake = json.loads((ROOT / "holdout_bakeoff.json").read_text())
old = pd.read_csv(ROOT / "visualization" / "holdout_bakeoff_table_OBSOLETE_prerepair_20260610.csv")
summ = json.loads((ROOT / "reconstruction" / "TUKU_carrier_reconstruction_summary.json").read_text())

layers = ["F1", "T1", "F2", "T2", "F3", "F4"]
equiv, bilinear_change = {}, {}
for L in layers:
    for design in ("middle_gap", "end_gap"):
        new_c = bake["per_layer"][L][design]["rmse_carrier_mm"]
        new_b = bake["per_layer"][L][design]["rmse_bilinear_mm"]
        row = old[(old["layer"] == L) & (old["design"] == design)]
        # column names in the archived CSV: verify on first run; adjust the two names below
        # to the actual header if they differ, and record the mapping in the JSON metadata.
        old_c = float(row["rmse_carrier_mm"].iloc[0])
        old_b = float(row["rmse_bilinear_mm"].iloc[0])
        equiv[f"{L}.{design}"] = {"old": old_c, "new": new_c, "abs_delta_mm": abs(new_c - old_c)}
        bilinear_change[f"{L}.{design}"] = {"old": old_b, "new": new_b}

max_delta = max(v["abs_delta_mm"] for v in equiv.values())
tail = summ["tail_evaluation"]
n_pos = sum(1 for L in layers if tail[L]["skill"] > 0)
out = {
    "metadata": {"date": "2026-06-11", "closes": ["2.1.2", "2.4.2"],
                 "sources": ["holdout_bakeoff.json",
                             "visualization/holdout_bakeoff_table_OBSOLETE_prerepair_20260610.csv",
                             "reconstruction/TUKU_carrier_reconstruction_summary.json"]},
    "carrier_equivalence": {"per_cell": equiv, "max_abs_delta_mm": max_delta,
                            "pass_lt_0p1mm": max_delta < 0.1},
    "bilinear_old_vs_new": bilinear_change,
    "decision_point_1": {"verdict": bake["metadata"]["verdict"],
                         "rule": "carrier wins/ties >= 4 of 6 layers across both designs",
                         "win_counts": bake["win_counts"]},
    "decision_point_2": {"verdict": "PASS" if n_pos >= 3 else ("PARTIAL" if n_pos >= 1 else "FAIL"),
                         "rule": "skill > 0 on >= 3 layers (tail holdout)",
                         "skills": {L: tail[L]["skill"] for L in layers}, "n_positive": n_pos},
}
(ROOT / "m2_closeout.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out["carrier_equivalence"]["per_cell"], indent=2))
print("max |carrier delta| =", max_delta, "mm; DP1 =", out["decision_point_1"]["verdict"],
      "; DP2 =", out["decision_point_2"]["verdict"])
```

- [x] **6.1.3** Run it; expected: `max |carrier delta| < 0.1 mm` (the 06-11 audit already saw
  agreement to 4 decimals), `DP1 = CARRIER-PRIMARY`, `DP2 = PASS` with skills T1 +0.4075,
  F2 +0.4305, T2 +0.2981, F1 −0.1813, F3 −0.2488, F4 −0.1425. Re-read `m2_closeout.json` and
  confirm printed = persisted.
- [x] **6.1.4** In `13_holdout_method_bakeoff.py` (~L570–573), replace the hardcoded
  `"2026-06-09"` metadata date with `datetime.date.today().isoformat()` and the stale plan
  reference with `"super_plan_2026-06-11.md"`. No logic changes.
- [x] **6.1.5** Commit: `git add tau_demo_TUKU/20_m2_closeout.py tau_demo_TUKU/13_holdout_method_bakeoff.py tau_demo_TUKU/results/m2_closeout.json` then `git commit -m "M6.1: persist M2 equivalence check + DP1/DP2 machine-readable fields"`

#### TASK 6.2 — F1/T1 hypotheses (b) and (c) (closes 2.2.4)

**Physical question:** F1/T1 bulk ratios (1.64/2.03) sit below the physical floor of 3 even
though head fell 3.36 m below $h_c$ on ~48% of epochs. Is the fitted τ wrong (hypothesis b), or
do these shallow layers truly respond near-elastically post-2015 (hypothesis c)?

**Files:**
- Create: `tau_demo_TUKU/21_f1t1_hypotheses.py`
- Output: `tau_demo_TUKU/results/characterization/f1t1_hypotheses.json`, PNG in `tau_demo_TUKU/plots/characterization/`

- [x] **6.2.1** Write the script. It must reuse the corrected loader from Script 15 (import its
  data-building functions; do NOT re-write slicing code — the lag invariant lives there).
  For each of F1 and T1: (hyp b) re-run the τ grid 0–120 on the dense era only, persist the
  SSE-vs-τ curve and the flatness measure (SSE range / SSE min); a flat curve (< 5% relative
  range) means τ is unidentifiable, not wrong. (hyp c) fit the A2 structure twice on epochs
  through 2018 — once with $S_{kv}$ free, once with $S_{kv} = 0$ — and compare end-gap
  (2019–2024-style last-30%) held-out RMSE; if the $S_{kv}=0$ fit is within 5%, the verdict
  field is `"elastic-dominated regime, S_kv not excited"`.
- [x] **6.2.2** Run; persist JSON with explicit `verdict` per layer + the SSE curves; export the
  two SSE-vs-τ PNGs (Rule V standards). Re-read the JSON to confirm.
- [x] **6.2.3** Commit: `git commit -m "M6.2: F1/T1 hypotheses (b) tau-sensitivity and (c) elastic-dominated test persisted"`

#### TASK 6.3 — Regenerate the stale visualizations from the repaired JSONs (closes V1)

- [x] **6.3.1** Re-run, in order, with fafalab2: `16a_visualize_bakeoff.py`,
  `16b_visualize_gwl_eval.py`, `16c_visualize_storage_params.py`,
  `16d_visualize_reconstruction_diagnostics.py`. Verify each PNG/CSV in
  `tau_demo_TUKU/results/visualization/` now has a 2026-06-11 mtime and that
  `holdout_bakeoff_table.csv` bilinear column equals `holdout_bakeoff.json` values.
- [x] **6.3.2** Fix `visualize_observed_vs_predicted.py`: the annotation must state the model
  actually plotted (carrier+GWL from Script 14) — change the annotation source (~L125 area) so
  it quotes the tail skills from `TUKU_carrier_reconstruction_summary.json::tail_evaluation`
  instead of M4 adopted-hybrid verdicts. Re-run, regenerate the 6-panel PNG.
- [x] **6.3.3** Commit: `git commit -m "M6.3: regenerate post-repair visualizations; fix mislabeled observed-vs-predicted annotation"`

#### TASK 6.4 — Freeze the M3 hybrid registry as evidence

- [x] **6.4.1** Add a `"status"` note to a NEW file `tau_demo_TUKU/results/hybrid_model_registry_STATUS.json`
  (do not edit the original): `{"status": "FROZEN-EVIDENCE", "reason": "selection leakage (audit 2026-06-11, finding L2): same holdouts used for selection and reporting; superseded for deployment by the fixed A2 structure of super_plan_2026-06-11", "date": "2026-06-11"}`.
- [x] **6.4.2** Commit: `git commit -m "M6.4: freeze M3 hybrid registry as evidence (selection leakage)"`

#### TASK 6.5 — MLCW provenance audit (P1 / Assumption A8)

**Files:**
- Create: `tau_demo_TUKU/22_mlcw_provenance_audit.py`
- Output: `tau_demo_TUKU/results/mlcw_provenance_audit.json`, candidate observed-epoch mask CSV `tau_demo_TUKU/results/mlcw_observed_epoch_mask.csv`, 1 PNG

- [x] **6.5.1** Inventory the raw MLCW holdings: `Glob data/mlcw/**` (list every file, no
  loading). Report whether any file looks like raw per-visit observations (irregular dates,
  per-ring readings) as opposed to the regular 5-day reconstruction.
- [x] **6.5.2** Statistical fingerprint of `TUKU_reconst_grouped.csv`: per layer, compute the
  run-lengths of constant second differences (a linear-interpolation segment has zero second
  difference); persist the fraction of epochs inside runs ≥ 3 (likely-interpolated) vs outside
  (likely-observed anchor points), and the inferred anchor-date list. Export the mask CSV
  (`date, layer, likely_observed` — one row per epoch per layer) and a PNG showing one year of
  F2 with inferred anchors marked.
- [x] **6.5.3** Write the JSON verdict: either (i) raw observation files found → name them and
  state the next step (use their dates as the visit-sampling frame in M8), or (ii) not found →
  `"A8 caveat permanent: synthetic-content fraction per layer = <numbers>"`. Never guess.
- [x] **6.5.4** Commit: `git commit -m "M6.5: MLCW provenance audit + likely-observed epoch mask"`

> **GATE M6:** [x] `m2_closeout.json`, `f1t1_hypotheses.json`, regenerated visualizations,
> `hybrid_model_registry_STATUS.json`, `mlcw_provenance_audit.json` all on disk and re-read.
> Also: reconcile the 06-10 plan's checkboxes (done 2026-06-11 by the auditor session).

---

### MILESTONE M7 — The Simple Ratio Test (user Phase 5) + Carrier Information Audit

**Physical narrative:** strip the linear trend from the GPS series and from each layer's
compaction record, and ask the simplest possible question: is the leftover layer motion a
lagged, scaled copy of the leftover surface motion? The answer measures — in one number per
layer — how much dynamic information the surface actually carries, and it either confirms or
amends the §1 feasibility verdict with TUKU's own data.

#### TASK 7.1 — Build and run `19_simple_ratio_test.py`

**Files:**
- Create: `tau_demo_TUKU/19_simple_ratio_test.py`
- Output dir (new, tidy, mirrors existing structure): `tau_demo_TUKU/results/simple_ratio_test/` (CSV + JSON) and `tau_demo_TUKU/plots/simple_ratio_test/` (PNG)

- [x] **7.1.1** Write the script exactly as specified:

```python
#!/usr/bin/env python
"""19_simple_ratio_test.py — Detrended GPS-to-layer lag/ratio test (super_plan_2026-06-11, M7).

Idea: after removing each series' linear trend,
    detrended_b_k(t) ?= ratio_k * detrended_GPS(t - lag_k)
Per layer: cross-correlate over lags -120..+120 five-day epochs, pick the |corr|-max lag,
fit the through-origin ratio, export CSV + JSON + PNG.

Run: $env:PYTHONPATH=""; conda run -n fafalab2 python tau_demo_TUKU/19_simple_ratio_test.py
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parents[1]
MLCW_CSV = REPO / "data/mlcw/group_byLayer_reconstr/TUKU_reconst_grouped.csv"
GPS_CSV = REPO / "data/gps/modeled/TKJS_model.csv"
RES = REPO / "tau_demo_TUKU/results/simple_ratio_test"
PLOTS = REPO / "tau_demo_TUKU/plots/simple_ratio_test"
LAYERS = ["F1", "T1", "F2", "T2", "F3", "F4"]
MAX_LAG = 120  # five-day epochs = 600 days
plt.rcParams.update({"font.size": 14, "axes.grid": True, "figure.dpi": 100})

def detrend(t_days, y):
    m = np.isfinite(y)
    if m.sum() < 4:
        return None, None
    p = np.polyfit(t_days[m], y[m], 1)
    return y - np.polyval(p, t_days), p

def main():
    RES.mkdir(parents=True, exist_ok=True)
    PLOTS.mkdir(parents=True, exist_ok=True)
    mlcw = pd.read_csv(MLCW_CSV, parse_dates=["datetime"]).rename(columns={"datetime": "date"})
    gps = pd.read_csv(GPS_CSV, parse_dates=["date"])
    df = pd.merge_asof(mlcw.sort_values("date"), gps[["date", "modeled"]].sort_values("date"),
                       on="date", tolerance=pd.Timedelta("2D"), direction="nearest")
    t_days = (df["date"] - df["date"].iloc[0]).dt.days.to_numpy(float)
    g_det, g_p = detrend(t_days, df["modeled"].to_numpy(float))
    summary, xcorr_curves = {}, {}
    for L in LAYERS:
        b_det, b_p = detrend(t_days, df[L].to_numpy(float))
        if b_det is None:
            print(f"{L}: insufficient data - result is undefined")
            continue
        lags = np.arange(-MAX_LAG, MAX_LAG + 1)
        corrs = np.full(lags.size, np.nan)
        for i, lag in enumerate(lags):
            g_s = pd.Series(g_det).shift(lag).to_numpy()  # lag>0: GPS leads compaction
            m = np.isfinite(b_det) & np.isfinite(g_s)
            if m.sum() >= 10:
                corrs[i] = np.corrcoef(b_det[m], g_s[m])[0, 1]
        if not np.isfinite(corrs).any():
            print(f"{L}: insufficient data - result is undefined")
            continue
        i_best = int(np.nanargmax(np.abs(corrs)))
        lag_best, corr_best = int(lags[i_best]), float(corrs[i_best])
        g_best = pd.Series(g_det).shift(lag_best).to_numpy()
        m = np.isfinite(b_det) & np.isfinite(g_best)
        ratio = float(np.sum(g_best[m] * b_det[m]) / np.sum(g_best[m] ** 2))
        fit = ratio * g_best
        ss_res = float(np.sum((b_det[m] - fit[m]) ** 2))
        ss_tot = float(np.sum((b_det[m] - b_det[m].mean()) ** 2))
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
        summary[L] = {"lag_epochs": lag_best, "lag_days": lag_best * 5,
                      "corr_at_best_lag": corr_best, "ratio_mm_per_mm": ratio,
                      "r2_detrended": r2, "n_pairs": int(m.sum()),
                      "std_detrended_obs_mm": float(np.nanstd(b_det)),
                      "std_detrended_gps_mm": float(np.nanstd(g_det))}
        xcorr_curves[L] = {"lags": lags.tolist(), "corr": [None if not np.isfinite(c) else round(float(c), 4) for c in corrs]}
        pd.DataFrame({"date": df["date"], "b_detrended_mm": b_det,
                      "gps_detrended_shifted_mm": g_best, "ratio_fit_mm": fit,
                      "residual_mm": b_det - fit}).to_csv(RES / f"TUKU_{L}_ratio_timeseries.csv", index=False)
        fig, ax = plt.subplots(2, 1, figsize=(12, 8))
        ax[0].plot(lags * 5, corrs, color="tab:blue")
        ax[0].axvline(lag_best * 5, color="tab:red", ls="--",
                      label=f"best lag {lag_best*5} d, r={corr_best:.3f}")
        ax[0].set_xlabel("GPS lead time (days)"); ax[0].set_ylabel("Pearson r"); ax[0].legend()
        ax[0].set_title(f"TUKU {L} - detrended cross-correlation")
        ax[1].plot(df["date"], b_det, color="tab:blue", lw=0.8, label="detrended MLCW (mm)")
        ax[1].plot(df["date"], fit, color="tab:orange", lw=1.2,
                   label=f"ratio x shifted GPS (ratio={ratio:.3f})")
        ax[1].set_xlabel("Date"); ax[1].set_ylabel("Detrended compaction (mm)"); ax[1].legend()
        fig.tight_layout(); fig.savefig(PLOTS / f"TUKU_{L}_ratio_test.png", dpi=300); plt.close(fig)
    pd.DataFrame(summary).T.to_csv(RES / "simple_ratio_summary.csv")
    (RES / "simple_ratio_summary.json").write_text(json.dumps({
        "metadata": {"date": "2026-06-11", "gps_source": str(GPS_CSV.name),
                     "gps_column": "modeled", "max_lag_epochs": MAX_LAG,
                     "detrend": "linear OLS on cumulative",
                     "interpretation_rule": "|corr| < 0.5 means the GPS residual cannot supply that layer's dynamics"},
        "per_layer": summary, "xcorr_curves": xcorr_curves}, indent=2))
    fig, ax = plt.subplots(figsize=(10, 6))
    Ls = list(summary)
    ax.bar(Ls, [summary[L]["corr_at_best_lag"] for L in Ls], color="tab:blue")
    ax.axhline(0.5, color="tab:red", ls="--", label="information threshold 0.5")
    ax.axhline(-0.5, color="tab:red", ls="--")
    ax.set_ylabel("Pearson r at best lag"); ax.set_title("TUKU detrended GPS-to-layer correlation")
    ax.legend(); fig.tight_layout(); fig.savefig(PLOTS / "summary_corr_per_layer.png", dpi=300)
    print(pd.DataFrame(summary).T.to_string())

if __name__ == "__main__":
    main()
```

- [x] **7.1.2** Run it. **Expected outcome (state honestly in the findings):** correlations
  roughly 0.4–0.7 for F1/T1/F2/T2, near zero for F3 (the 06-11 audit measured −0.086 against
  the carrier fit) and weak for F4 (~0.17). Ratios are small. If any layer surprises (e.g.,
  F3 |corr| > 0.5 at some long lag), that AMENDS the §1 verdict — report it prominently, do not
  bury it.
- [x] **7.1.3** Repeat once with the `orig_nojump` GPS column instead of `modeled` (one-line
  change via a `GPS_COLUMN` constant; write outputs to `simple_ratio_test/orig_nojump/`).
  This measures how much sub-annual content the upstream smoothing removed. Record both in the
  JSON metadata.
- [x] **7.1.4** Commit: `git commit -m "M7: simple detrended GPS-to-layer lag/ratio test, both GPS variants"`

> **GATE M7 (informational, no stop):** [x] `simple_ratio_summary.json` persisted for both GPS
> variants. If max |corr| across layers ≥ 0.5 for a layer where §1 predicted < 0.5, append an
> amendment note to §1's verdict in the findings document of M8.

---

### MILESTONE M8 — Sequential Assimilation Rehearsal at TUKU (the pivot)

**Physical narrative:** pretend the well went on a budget diet on 2019-01-01. The model — frozen
on the dense 2010–2018 era — walks forward driven only by the living GPS and GWL signals. At
each scheduled "visit" the field crew reads the well once; the model compares its forecast to
the reading (the innovation), resets its level, and widens or narrows its error bands from the
accumulated forward-error history. Six visiting cadences are rehearsed. The output is the
degradation curve: accuracy as a function of visit frequency — the number the operator needs.

> **Truth source (set by Task 6.5, 2026-06-11):** the genuine MLCW observations are the **264
> real field visits** in `data/mlcw/group_byLayer_orig/TUKU_orig_grouped.csv` (irregular dates,
> already monthly→annual; columns `datetime,F1,T1,F2,T2,F3,T3,F4` — use the 6 instrumented
> layers, T3 is NaN at TUKU). These are the ONLY values used for the "reveal" step and for
> grading. The dense 5-day `TUKU_reconst_grouped.csv` is a smooth non-linear fill — usable as a
> continuous diagnostic overlay and for plotting, but it is NOT graded against and NOT revealed
> as truth. The genuine series carries its OWN cumulative datum per visit; align by `merge_asof`
> to the 5-day model grid with a tight tolerance (≤ 3 days) so each genuine visit maps to one
> model epoch. This removes most of Assumption A8's force.

**Anti-leakage requirements (non-negotiable, they encode audit findings L1/L2):**
1. A single `TimeOracle` object owns "now"; every data accessor filters by it; access to a
   future row raises `LeakageError`. Leakage becomes a crash, not a review finding.
2. All frozen constants ($\tau_k$, $h_c$, coefficients, seasonal constants) computed from the
   dense era only.
3. NO model selection anywhere in the blind era (structure fixed by A2).
4. 2024 is the confirmatory year: graded once, after all development, by a separate script.
5. Every run writes a manifest JSON recording the exact cutoffs used.

#### TASK 8.1 — Core modules + unit tests (TDD)

**Files:**
- Create: `tau_demo_TUKU/seq/__init__.py` (empty), `tau_demo_TUKU/seq/time_oracle.py`,
  `tau_demo_TUKU/seq/conformal.py`, `tau_demo_TUKU/seq/test_seq_core.py`

- [ ] **8.1.1** Write the failing tests first (`tau_demo_TUKU/seq/test_seq_core.py`):

```python
"""Unit tests for the sequential-rehearsal core. Run:
$env:PYTHONPATH=""; conda run -n fafalab2 python -m pytest tau_demo_TUKU/seq/test_seq_core.py -v
"""
import numpy as np
import pandas as pd
import pytest
from time_oracle import TimeOracle, LeakageError
from conformal import ConformalBank

def _df():
    d = pd.date_range("2020-01-01", periods=100, freq="5D")
    return pd.DataFrame({"date": d, "v": np.arange(100.0)})

def test_oracle_blocks_future():
    df = _df()
    o = TimeOracle(pd.Timestamp("2020-03-01"))
    assert o.view(df)["date"].max() <= pd.Timestamp("2020-03-01")

def test_oracle_strict_raises():
    df = _df()
    o = TimeOracle(pd.Timestamp("2020-03-01"))
    with pytest.raises(LeakageError):
        o.assert_no_future(df.iloc[[-1]])

def test_oracle_no_backward():
    o = TimeOracle(pd.Timestamp("2020-03-01"))
    with pytest.raises(LeakageError):
        o.advance(pd.Timestamp("2020-01-01"))

def test_conformal_coverage_synthetic():
    rng = np.random.default_rng(0)
    bank = ConformalBank(alpha=0.10)
    for _ in range(500):
        bank.add("F1", horizon=10, abs_err=abs(rng.normal(0, 2.0)))
    hw = bank.half_width("F1", horizon=10)
    fresh = np.abs(rng.normal(0, 2.0, 5000))
    cov = float((fresh <= hw).mean())
    assert 0.85 <= cov <= 0.95   # 90% nominal

def test_conformal_insufficient_is_nan():
    bank = ConformalBank(alpha=0.10)
    bank.add("F1", horizon=10, abs_err=1.0)
    assert np.isnan(bank.half_width("F1", horizon=10))
```

- [ ] **8.1.2** Run: expected FAIL (`ModuleNotFoundError`). Then write the two modules:

`tau_demo_TUKU/seq/time_oracle.py`:
```python
"""TimeOracle — single owner of 'now'. Encodes Do-Not-Regress rule 11 (no temporal leakage)."""
import pandas as pd

class LeakageError(RuntimeError):
    pass

class TimeOracle:
    def __init__(self, now: pd.Timestamp):
        self.now = pd.Timestamp(now)

    def advance(self, to) -> None:
        to = pd.Timestamp(to)
        if to < self.now:
            raise LeakageError(f"time cannot run backward: {self.now} -> {to}")
        self.now = to

    def view(self, df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
        return df[df[date_col] <= self.now]

    def assert_no_future(self, df: pd.DataFrame, date_col: str = "date") -> None:
        if (df[date_col] > self.now).any():
            raise LeakageError(f"future rows present past {self.now}")
```

`tau_demo_TUKU/seq/conformal.py`:
```python
"""Split-conformal interval bank on absolute forward errors, bucketed by forecast horizon.
half_width(layer, horizon) = (1-alpha) empirical quantile of past |errors| in the bucket.
Finite-sample marginal coverage holds without distributional assumptions (Vovk et al.).
"""
from collections import defaultdict
import numpy as np

HORIZON_BUCKETS = [(1, 18), (19, 36), (37, 73), (74, 146), (147, 10**9)]  # five-day epochs
MIN_SAMPLES = 20

def bucket_of(horizon: int):
    for lo, hi in HORIZON_BUCKETS:
        if lo <= horizon <= hi:
            return (lo, hi)
    return HORIZON_BUCKETS[-1]

class ConformalBank:
    def __init__(self, alpha: float = 0.10):
        self.alpha = alpha
        self.errors = defaultdict(list)

    def add(self, layer: str, horizon: int, abs_err: float) -> None:
        if np.isfinite(abs_err):
            self.errors[(layer, bucket_of(int(horizon)))].append(float(abs_err))

    def half_width(self, layer: str, horizon: int) -> float:
        errs = self.errors[(layer, bucket_of(int(horizon)))]
        if len(errs) < MIN_SAMPLES:
            return float("nan")  # insufficient data - interval undefined, never guessed
        return float(np.quantile(errs, 1.0 - self.alpha))

    def census(self):
        return {f"{k[0]}|{k[1][0]}-{k[1][1]}": len(v) for k, v in self.errors.items()}
```

- [ ] **8.1.3** Run the tests again: expected 5 passed.
- [ ] **8.1.4** Commit: `git commit -m "M8.1: TimeOracle + conformal bank with unit tests (leakage is now a crash)"`

#### TASK 8.2 — Dense-era frozen calibration

**Files:**
- Create: `tau_demo_TUKU/seq/frozen_model.py`, `tau_demo_TUKU/seq/23_dense_calibration.py`
- Output: `tau_demo_TUKU/results/seq/frozen_calibration.json`, per-layer PNG in `tau_demo_TUKU/plots/seq/`

- [ ] **8.2.1** `frozen_model.py` — the A2 structure, one class, no alternatives:

```python
"""FrozenLayerModel — fixed two-regime structure (Assumption A2), per-layer.
b_k(t) = c + a*d(t) + S_ke*u(t-tau) + S_kv*V(t-tau) + beta(live bias)
Signs: b negative = compaction; u = H - H_ref (never negated); V = min(0, cummin(H) - h_c) <= 0.
Units: b, d in mm; u, V in m; S_ke, S_kv in mm/m; a dimensionless.
"""
from dataclasses import dataclass, field
import numpy as np
from scipy.optimize import lsq_linear

@dataclass
class FrozenLayerModel:
    layer: str
    a: float = 0.0
    c: float = 0.0
    S_ke: float = 0.0
    S_kv: float = 0.0
    tau: int = 0
    use_u: bool = True
    use_V: bool = True
    beta: float = 0.0          # the only live parameter after freezing
    h_c: float = float("nan")

    def design(self, d, u_lag, V_lag):
        cols = [np.ones_like(d), d]
        if self.use_u:
            cols.append(u_lag)
        if self.use_V:
            cols.append(V_lag)
        return np.column_stack(cols)

    def fit(self, d, u_lag, V_lag, b):
        m = np.isfinite(b) & np.isfinite(d)
        if self.use_u:
            m &= np.isfinite(u_lag)
        if self.use_V:
            m &= np.isfinite(V_lag)
        if m.sum() < 30:
            raise ValueError(f"{self.layer}: insufficient data - fit is undefined (n={m.sum()})")
        X, y = self.design(d, u_lag, V_lag)[m], b[m]
        lo = [-np.inf, 0.0] + ([0.0] if self.use_u else []) + ([0.0] if self.use_V else [])
        res = lsq_linear(X, y, bounds=(lo, [np.inf] * X.shape[1]))
        coef = list(res.x)
        self.c, self.a = coef[0], coef[1]
        i = 2
        if self.use_u:
            self.S_ke = coef[i]; i += 1
        if self.use_V:
            self.S_kv = coef[i]
        return self

    def predict(self, d, u_lag, V_lag):
        y = self.c + self.beta + self.a * d
        if self.use_u:
            y = y + self.S_ke * u_lag
        if self.use_V:
            y = y + self.S_kv * V_lag
        return y

    def assimilate(self, innovation_mm: float):
        """Visit update (Assumption A6): hard level reset."""
        self.beta += float(innovation_mm)
```

- [ ] **8.2.2** `23_dense_calibration.py` — calibrate every layer on 2010-01-16…2018-12-31 ONLY:
  - Load via the SAME loaders Script 14 uses (import its data-building functions — they carry
    the verified lag invariant and gap-aware cumsum; do not re-write them).
  - $h_c$ per layer from raw pre-REF_DATE (2015-01-16) GWL feather rows (Bug-F rule).
  - $\tau_k$ per layer by grid search 0–120 on the dense era only (minimize SSE of the A2 fit).
    **F3 sandbox exception:** additionally record (diagnostic only, clearly labeled
    `tau_extended_diagnostic`) the SSE curve out to τ=292 (4 yr), because F3 saturated at the
    120 cap; production τ stays ≤ 120 until the human approves a TAU_MAX change (CLAUDE.md
    constraint).
  - Identifiability: apply the M1.5 4-condition rule; layers failing it drop the $u$ term
    (set `use_u=False`) and/or fit inelastic-only — exactly the Script-15 logic, imported not
    re-written.
  - Guardrails: `from scripts.guardrails import validate_layer_params` — validate before
    writing; halt on fatal.
  - A1 stability check: fit $a_k$ on 2010–2014 and on 2015–2018 separately; persist both and
    the relative difference.
  - A4 check: compare the fitted seasonal amplitude of the $S_{ke} u(t-\tau)$ term against the
    observed detrended seasonal amplitude per layer (F2 target: head term supplies ≥ 50% of the
    4.52 mm, else record `harmonic_fallback_considered: true` with the frozen-harmonic fit as a
    SEPARATE labeled entry — never silently swapped in).
  - Persist `frozen_calibration.json`: per layer {a, c, S_ke, S_kv, tau, use_u, use_V, h_c,
    n_train, identifiability fields, A1 split-fit, A4 seasonal check, guardrail report} +
    manifest {dense_start, dense_end, gwl_well per layer, REF_DATE}.
  - Export per-layer calibration PNG (observed vs fitted, dense era only, Rule V standards).
- [ ] **8.2.3** Run; re-read JSON; confirm every persisted number equals the printed table.
  Expected magnitudes (sanity, not gates): $a_{F2} \approx 0.23$, $a_{F3} \approx 0.31$,
  $\sum a_k \in [0.55, 0.75]$, $\tau_{F2}$ near 72.
- [ ] **8.2.4** Commit: `git commit -m "M8.2: dense-era frozen calibration (A2 structure, guardrails, A1/A4 checks)"`

#### TASK 8.3 — The walk-forward engine (predict → reveal → adjust)

**Files:**
- Create: `tau_demo_TUKU/seq/24_walk_forward_rehearsal.py`
- Output per schedule S ∈ {monthly, quarterly, semiannual, annual, none, blackout}:
  `tau_demo_TUKU/results/seq/{S}/TUKU_{layer}_seq_timeseries.csv`,
  `tau_demo_TUKU/results/seq/{S}/metrics.json`,
  `tau_demo_TUKU/plots/seq/{S}/TUKU_seq_6layer.png`;
  plus `tau_demo_TUKU/results/seq/run_manifest.json`

- [ ] **8.3.1** Define the schedules. **Visits are real field visits, not synthetic epochs:**
  start from the genuine visit dates in `TUKU_orig_grouped.csv` that fall inside the blind era
  (2019-01-01…2023-12-31; 2024 reserved). Build each cadence by SUBSAMPLING the genuine visit
  list to the target spacing (keep the genuine date nearest each target interval):
  - `monthly` ≈ 30-day spacing; `quarterly` ≈ 90-day; `semiannual` ≈ 180-day; `annual` ≈ 365-day;
  - `none`: no visits; `blackout`: no visits before 2021-01-01, then annual.
  - `actual`: a seventh schedule using the genuine visit cadence as-is (no subsampling) — this is
    the real-world baseline the operator already lives with.
  Record, per schedule, the exact genuine visit dates used in the manifest. If the blind era
  contains fewer genuine visits than a cadence would imply (e.g. the well already went sparse),
  use what exists and record the true count — never invent a visit date.
- [ ] **8.3.2** Engine main loop (the heart — write exactly this logic):

```python
# inside 24_walk_forward_rehearsal.py (sketch of the core loop; full file assembles
# loaders from Script 14, FrozenLayerModel from frozen_calibration.json, TimeOracle, ConformalBank)
oracle = TimeOracle(DENSE_END)                      # 2018-12-31
bank = seed_bank(models, dense_df, schedule)        # rehearse same schedule inside 2015-2018,
                                                    # calibrating on 2010-2014, to pre-fill errors
rows = {L: [] for L in LAYERS}
last_visit = {L: DENSE_END for L in LAYERS}
for date in blind_epochs:                           # 2019-01-01 .. 2023-12-31, 5-day grid
    oracle.advance(date)
    view = oracle.view(drivers_df)                  # GPS d(t), GWL u/V up to 'now' only
    for L, mdl in models.items():
        d, u_lag, V_lag = drivers_at(view, L, date, mdl.tau)   # u(t-tau) needs only past head
        pred = mdl.predict(d, u_lag, V_lag)
        horizon = epochs_between(last_visit[L], date)
        hw = bank.half_width(L, horizon)            # NaN if insufficient history
        rows[L].append((date, pred, hw, horizon))
    if date in visit_dates:
        for L, mdl in models.items():
            obs = reveal(mlcw_truth, L, date)       # the ONLY read of truth in the loop
            pred = rows[L][-1][1]
            innovation = obs - pred
            bank.add(L, rows[L][-1][3], abs(innovation))
            mdl.assimilate(innovation)              # hard level reset (A6)
            record_innovation(L, date, innovation, bank.half_width(L, rows[L][-1][3]))
            last_visit[L] = date
```

  Step screening (A7): before predicting, flag any epoch where |Δd| > 5 × carrier noise
  (carrier noise = std of dense-era 5-day GPS increments); flagged epochs get
  `step_flag=True` in the CSV.
- [ ] **8.3.3** Metrics per schedule per layer. **Grade against the genuine field visits**
  (`TUKU_orig_grouped.csv`), never the dense fill. Primary metric = PREQUENTIAL error: at each
  genuine blind-era visit, score the model's prediction for that visit BEFORE it is revealed
  (works for every schedule including `actual`). For sparse schedules also report error at the
  genuine visits that fall BETWEEN reveals (held-out genuine visits). Report the model-vs-dense-fill
  continuous RMSE only as a labeled secondary diagnostic. Compute: MAE, RMSE, skill vs the frozen-trend baseline
  (carrier-only, no visits), `amplitude_ratio_increments`, `detrended_corr`,
  `detrended_std_obs_mm`, `detrended_std_pred_mm` (Rule V2), empirical band coverage (fraction
  of epochs with |obs − pred| ≤ half-width, over epochs where the band is defined), mean band
  half-width, innovation list {date, value, in_band}, `converged` flag (3 consecutive in-band
  innovations), and for F3: `drought_2021_detection_date` (first visit in 2021+ with
  |innovation| > half-width).
- [ ] **8.3.4** Per-schedule 6-panel PNG: observed (thin line), predicted (thick), 90% band
  (shaded), visit dates (vertical ticks), innovations (markers). Rule V standards.
- [ ] **8.3.5** Cadence-degradation curve: assemble
  `tau_demo_TUKU/results/seq/cadence_degradation_curve.csv` (+ `.json` + PNG
  `plots/seq/cadence_curve.png`): rows = layer, columns = schedule, values = blind-era RMSE;
  second table for MAE; mark per layer the minimum cadence meeting its Level-1 thresholds.
- [ ] **8.3.6** Run all six schedules; verify every output file exists and re-read `metrics.json`
  values against the printed tables. Commit:
  `git commit -m "M8.3: walk-forward rehearsal, 6 cadences, conformal bands, degradation curve"`

#### TASK 8.4 — Confirmatory year (graded once)

**Files:**
- Create: `tau_demo_TUKU/seq/25_confirmatory_2024.py`
- Output: `tau_demo_TUKU/results/seq/confirmatory_2024.json`, PNG

- [ ] **8.4.1** ONLY after 8.3 is finalized and committed (no further engine edits permitted):
  run the engine over 2024-01-01…2024-12-31 with the two operationally relevant schedules
  (semiannual, annual), starting from the 2023-12-31 model state of each. Persist per layer:
  MAE, RMSE, band coverage, Rule V2 metrics.
- [ ] **8.4.2** Apply the apex criteria (§3): thresholds per layer class + coverage ≥ 0.85.
  Persist the verdict table. If the engine must be edited to make 2024 run at all (a crash),
  record the edit in the JSON under `post_freeze_edits` — the grade then carries an asterisk.
- [ ] **8.4.3** Commit: `git commit -m "M8.4: confirmatory 2024 grading (run once)"`

#### TASK 8.5 — Findings document

- [ ] **8.5.1** Write `discussions/SEQ_REHEARSAL_FINDINGS_20260611.md`: physical story first
  (what each layer did 2019–2024 and how well the blind model re-told it at each cadence), then
  the degradation curve, the confirmatory table, the F3 honest status, the M7 ratio-test
  confirmation/amendment of §1, limitations (A8 provenance, GPS ends 2024-12-31 so 2025 is
  out of reach for the GPS-only configuration). Every number cites file + field.

> **GATE M8 (Decision Point SEQ — the new DP3):**
> - **PASS:** ≥ 5 of 6 layers meet their Level-1 thresholds on the blind era at quarterly
>   cadence or sparser, AND confirmatory-2024 band coverage ≥ 0.85 on ≥ 5 layers, AND the
>   minimum-cadence recommendation is persisted per layer.
> - **PARTIAL:** thresholds met at monthly only — recalibration helps but the budget case is
>   weak; report honestly.
> - **FAIL:** visits do not improve over the no-visit run — escalate to the human; do NOT
>   proceed to M9 deployment claims (M9 may still run as a descriptive survey).
> Expected risk concentration: F3 (it failed M4 honestly; its inelastic memory is the hardest
> thing to carry across sparse visits).

---

### MILESTONE M9 — GPS-Only Multi-Station Deployment (user Phase 6; M5 reborn)

**Physical narrative:** the routing file `m5_deployment/station_file_map.json` maps 37 MLCW
stations to their inputs; 36 have a paired GPS station (ERLUN does not — skip it and say so).
Run the deployable GPS-carrier configuration at every mapped station to produce the first
portfolio-wide picture of where the method works. **GPS data only — no InSAR file may be
opened in this milestone** (`shared_files.insar_*` entries exist in the map; ignore them).
GWL augmentation across the portfolio is DEFERRED until the human ratifies it — this first
pass is carrier-only so that every station is scored by the identical minimal recipe.

#### TASK 9.1 — The deployment runner

**Files:**
- Create: `m5_deployment/run_m5_gps_deployment.py`
- Output: `m5_deployment/results/{STATION}/{STATION}_{layer}_reconstruction.csv`,
  `m5_deployment/results/{STATION}/{STATION}_metrics.json`,
  `m5_deployment/results/{STATION}/{STATION}_6layer.png` (panel count = that station's n_layers),
  `m5_deployment/summary/m5_gps_deployment_summary.csv` + `.json`,
  `m5_deployment/summary/portfolio_rmse.png`, `m5_deployment/summary/exclusion_report.json`

- [ ] **9.1.1** Write the runner:

```python
#!/usr/bin/env python
"""run_m5_gps_deployment.py — GPS-only carrier deployment across all mapped MLCW stations.
super_plan_2026-06-11 M9. Inputs resolved EXCLUSIVELY through station_file_map.json.
NO InSAR. NO GWL in this first pass. Carrier-only: b_k = c_k + a_k * d_GPS, a_k >= 0.
Run: $env:PYTHONPATH=""; conda run -n fafalab2 python m5_deployment/run_m5_gps_deployment.py
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import lsq_linear

REPO = Path(__file__).resolve().parents[1]
MAP = json.loads((REPO / "m5_deployment/station_file_map.json").read_text())
OUT = REPO / "m5_deployment/results"
SUMM = REPO / "m5_deployment/summary"
DENSE_FRACTION = 0.70           # chronological split: first 70% of overlap = train
MIN_OVERLAP = 300               # epochs; below this the station is excluded, not guessed
plt.rcParams.update({"font.size": 14, "axes.grid": True})

def fit_carrier(d, b):
    m = np.isfinite(d) & np.isfinite(b)
    X = np.column_stack([np.ones(m.sum()), d[m]])
    res = lsq_linear(X, b[m], bounds=([-np.inf, 0.0], [np.inf, np.inf]))
    return res.x[0], res.x[1]   # c, a

def metrics(obs, pred, dates):
    m = np.isfinite(obs) & np.isfinite(pred)
    if m.sum() < 10:
        return {"status": "insufficient data - result is undefined", "n": int(m.sum())}
    e = obs[m] - pred[m]
    t = (dates[m] - dates[m].iloc[0]).dt.days.to_numpy(float)
    det = lambda y: y - np.polyval(np.polyfit(t, y, 1), t)
    do, dp = det(obs[m].to_numpy()), det(pred[m].to_numpy())
    inc_o, inc_p = np.diff(obs[m].to_numpy()), np.diff(pred[m].to_numpy())
    return {"n": int(m.sum()), "mae_mm": float(np.mean(np.abs(e))),
            "rmse_mm": float(np.sqrt(np.mean(e ** 2))), "bias_mm": float(np.mean(e)),
            "amplitude_ratio_increments": float(np.std(inc_p) / np.std(inc_o)) if np.std(inc_o) > 0 else None,
            "detrended_corr": float(np.corrcoef(do, dp)[0, 1]) if do.size > 3 else None,
            "detrended_std_obs_mm": float(np.std(do)), "detrended_std_pred_mm": float(np.std(dp))}

def run_station(name, st):
    mlcw = pd.read_csv(REPO / st["files"]["mlcw_reconst_csv"], parse_dates=["datetime"]
                       ).rename(columns={"datetime": "date"})
    gps = pd.read_csv(REPO / st["files"]["gps_modeled_csv"], parse_dates=["date"])
    df = pd.merge_asof(mlcw.sort_values("date"), gps[["date", "modeled"]].sort_values("date"),
                       on="date", tolerance=pd.Timedelta("2D"), direction="nearest")
    overlap = df["modeled"].notna()
    if overlap.sum() < MIN_OVERLAP:
        return {"excluded": True, "reason": f"GPS-MLCW overlap {int(overlap.sum())} < {MIN_OVERLAP}"}
    idx = np.flatnonzero(overlap.to_numpy())
    cut = idx[int(len(idx) * DENSE_FRACTION)]
    train = df.index <= cut
    d = df["modeled"].to_numpy(float)
    res = {"excluded": False, "n_overlap": int(overlap.sum()),
           "train_end": str(df.loc[cut, "date"].date()), "layers": {}}
    sdir = OUT / name
    sdir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(len(st["layers"]), 1, figsize=(12, 2.6 * len(st["layers"])),
                             sharex=True, squeeze=False)
    for ax, L in zip(axes.ravel(), st["layers"]):
        b = df[L].to_numpy(float)
        c, a = fit_carrier(d[train], b[train])
        pred = c + a * d
        hold = ~train & overlap.to_numpy()
        res["layers"][L] = {"a_k": float(a), "c_k": float(c),
                            "holdout": metrics(df[L][hold], pd.Series(pred)[hold], df["date"][hold]),
                            "calibration_diagnostic": metrics(df[L][train & overlap.to_numpy()],
                                                              pd.Series(pred)[train & overlap.to_numpy()],
                                                              df["date"][train & overlap.to_numpy()])}
        pd.DataFrame({"date": df["date"], "b_observed_mm": b, "b_predicted_mm": pred,
                      "residual_mm": b - pred, "is_holdout": hold}
                     ).to_csv(sdir / f"{name}_{L}_reconstruction.csv", index=False)
        ax.plot(df["date"], b, lw=0.8, color="tab:blue", label="observed")
        ax.plot(df["date"], pred, lw=1.2, color="tab:orange", label="GPS carrier")
        ax.axvline(df.loc[cut, "date"], color="tab:red", ls="--")
        ax.set_ylabel(f"{L} (mm)"); ax.legend(loc="lower left", fontsize=10)
    axes.ravel()[-1].set_xlabel("Date")
    fig.suptitle(f"{name} - GPS-only carrier (train left of red line)")
    fig.tight_layout(); fig.savefig(sdir / f"{name}_6layer.png", dpi=300); plt.close(fig)
    (sdir / f"{name}_metrics.json").write_text(json.dumps(res, indent=2))
    return res

def main():
    SUMM.mkdir(parents=True, exist_ok=True)
    rows, exclusions = [], {}
    for name, st in MAP["stations"].items():
        if not st.get("has_gps_modeled") or not st["files"].get("gps_modeled_csv"):
            exclusions[name] = "no paired GPS modeled series"
            continue
        try:
            r = run_station(name, st)
        except FileNotFoundError as ex:
            exclusions[name] = f"file not found - cannot proceed: {ex}"
            continue
        if r.get("excluded"):
            exclusions[name] = r["reason"]
            continue
        for L, v in r["layers"].items():
            h = v["holdout"]
            rows.append({"station": name, "layer": L, "a_k": v["a_k"],
                         "n_holdout": h.get("n"), "rmse_mm": h.get("rmse_mm"),
                         "mae_mm": h.get("mae_mm"),
                         "amplitude_ratio": h.get("amplitude_ratio_increments"),
                         "detrended_corr": h.get("detrended_corr")})
    summary = pd.DataFrame(rows)
    summary.to_csv(SUMM / "m5_gps_deployment_summary.csv", index=False)
    (SUMM / "m5_gps_deployment_summary.json").write_text(json.dumps(
        {"metadata": {"date": "2026-06-11", "recipe": "GPS-only carrier, chronological 70/30",
                      "insar_used": False, "gwl_used": False},
         "n_stations_run": int(summary["station"].nunique()) if len(summary) else 0,
         "exclusions": exclusions,
         "portfolio_median_rmse_mm": float(summary["rmse_mm"].median()) if len(summary) else None},
        indent=2))
    (SUMM / "exclusion_report.json").write_text(json.dumps(exclusions, indent=2))
    if len(summary):
        fig, ax = plt.subplots(figsize=(14, 6))
        piv = summary.pivot_table(index="station", columns="layer", values="rmse_mm")
        piv.plot(kind="bar", ax=ax, colormap="tab10")
        ax.set_ylabel("Holdout RMSE (mm)"); ax.set_title("M9 GPS-only carrier - holdout RMSE by station/layer")
        fig.tight_layout(); fig.savefig(SUMM / "portfolio_rmse.png", dpi=300)
    print(summary.to_string() if len(summary) else "no stations ran")
    print("exclusions:", json.dumps(exclusions, indent=2))

if __name__ == "__main__":
    main()
```

- [ ] **9.1.2** Smoke-test on TUKU first: temporarily filter the loop to `name == "TUKU"`;
  expected: $a_{F2}$ within ~0.05 of 0.23 (the TUKU value; the 70/30 split differs from the
  dense-era split so exact equality is not expected), holdout RMSE same order as the 06-10
  end-gap numbers. Then remove the filter.
- [ ] **9.1.3** Full run (36 stations). Expected exclusions: ERLUN (`has_gps_modeled: false`);
  possibly stations whose GPS-MLCW overlap < 300 epochs — every exclusion must appear in
  `exclusion_report.json` with its reason. Runtime estimate: < 10 min total (linear fits only).
- [ ] **9.1.4** Verify: count result folders == stations run; re-read summary JSON; spot-check
  two stations' CSVs for NaN handling (rows before GPS start must have `b_predicted_mm` present
  — the carrier extends backward — but `is_holdout=False`).
- [ ] **9.1.5** Commit: `git commit -m "M9: GPS-only carrier deployment across mapped stations + portfolio summary"`

#### TASK 9.2 — Portfolio findings note

- [ ] **9.2.1** Append a section to `discussions/SEQ_REHEARSAL_FINDINGS_20260611.md`: portfolio
  RMSE distribution (median, quartiles), the stations where the carrier clearly fails
  (detrended_corr < 0.2 AND rmse above class threshold — these are the stations where GWL
  augmentation or the M8 protocol matters most), GPS-distance effect (the map carries
  `gps_distance_m` per station — scatter RMSE vs distance, one PNG into `m5_deployment/summary/`).

> **GATE M9:** summary + exclusion report persisted; portfolio figure exists; findings appended.
> **This plan ends here.** Part 2 batch physics (per-station storage parameters) and Part 3
> (8,577 grid points) remain blocked pending human review of GATE M8 + M9 outputs.

---

## Appendix A — Canonical Equations and Symbols (unchanged physics, new protocol terms)

| Symbol | Meaning | Units | Constraint |
|--------|---------|-------|------------|
| $b_k(t)$ | cumulative compaction, layer $k$ | mm | negative = compaction |
| $d(t)$ | GPS surface displacement (carrier) | mm | negative = subsidence |
| $u_k(t)$ | zero-referenced head $H - H_{ref}$, ref 2015-01-16 | m | **never negate** |
| $V_k(t)$ | virgin exceedance $\min(0, \mathrm{cummin}\,H - h_c)$ | m | monotone non-increasing |
| $\tau_k$ | consolidation lag | 5-day epochs | $0 \le \tau \le 120$ production; F3 diagnostic to 292 |
| $a_k$ | carrier share | — | $a_k \ge 0$, $\sum a_k \le 1$ |
| $\beta_k$ | live level bias (visit-updated) | mm | reset at visits (A6) |
| innovation $e$ | observed − predicted at a visit | mm | persisted, every visit |
| half-width | conformal $(1-\alpha)$ quantile of past \|forward errors\| per horizon bucket | mm | undefined (NaN) below 20 samples |
| cadence | visit interval | epochs | {6, 18, 36, 73, none, blackout} |

**The lag-pairing invariant (still rule #1):** response `b[τ:N]` pairs with driver `H[0:N−τ]`.

## Appendix B — Do-Not-Regress List (extended; items 1–10 inherited from the 06-10 plan)

1–10. *(unchanged — see `super_plan_2026-06-10.md` Appendix B.)*
11. **No temporal leakage:** every blind-era data access goes through `TimeOracle`; reading a
    future row is a crash, not a finding (L1, 2026-06-11).
12. **Selection and reporting use disjoint data:** any procedure that chooses between models
    must be graded on epochs it never touched; the confirmatory segment is graded once (L2,
    2026-06-11).
13. **The mission metric is cadence degradation:** no deployment claim without the
    sparse-visit rehearsal behind it (L3, 2026-06-11).
14. **Dynamics fidelity is mandatory reporting:** `amplitude_ratio_increments` and
    `detrended_corr` in every evaluation JSON (A1, 2026-06-11). High cumulative R² alone is
    wallpaper.
15. **Provenance before truth:** a training/grading series of unknown observed-vs-interpolated
    composition carries the A8 caveat in every product built on it (P1, 2026-06-11).
16. **Free oscillators are last resort:** seasonal terms come from head; a fitted harmonic
    enters only with a persisted demonstration that the head term cannot supply the amplitude
    (A4, 2026-06-11).

---

*Plan written 2026-06-11 by the independent audit session (Phases 1–6 of the user mandate:
plan migration, leakage critique, amplitude critique, feasibility + assumptions + pivot,
simple ratio test, GPS-only M5 deployment). Supersedes `super_plan_2026-06-10.md` for all
unfinished work. No production code was modified by this plan.*
