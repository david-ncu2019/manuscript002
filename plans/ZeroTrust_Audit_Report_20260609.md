# Zero-Trust Independent Audit Report — InSAR-MLCW-GWL Subsidence Model

**Date:** 2026-06-09
**Auditor:** Claude (Opus 4.8), fresh session, zero-trust protocol
**Method:** Every number traced to a file and line. No inherited claim trusted.

---

## Context — Why This Audit Exists

The project wants to rebuild a broken measurement record. The deep-well compaction
sensors (MLCW) have stopped or slowed down because they cost too much to run. The plan
is to fill the gaps and predict future compaction using two signals that are still
recorded everywhere: satellite radar (InSAR) and groundwater level (GWL).

The team has tried several methods. The latest story in the project notes says: "the
5-day incremental solver failed, but the cumulative Script 12 succeeded." This audit
checked that story from the ground up. The short version: **the physics model is sound,
but the story about the current code is wrong. The version of the cumulative method that
is actually wired into the production script is broken, and the project's own ledger is
quoting pass/fail numbers that no longer match the files on disk.**

---

## Plain-Language Summary (read this first)

1. **The production solver and the "validated" Script 12 are two different models.** Only
   Script 12 works. The one wired into `fit_ihm_f_v3.py` fails badly. People are citing
   Script 12's good numbers as if they prove the production code works. They do not.

2. **The production solver leaves out the intercept and uses absolute head.** The
   project's own theory paper proves both choices are wrong. The result: the elastic
   coefficient collapses to exactly zero for 4 of 6 layers, and 5 of 6 layers fit worse
   than a flat line (negative R²).

3. **The headline gate numbers in the ledger are stale.** CLAUDE.md and PROGRESS.md say
   "F1=9.1× PASS, T2=9.3× PASS, F4=17.3× PASS." The live result file says F1 actually
   FAILS, and only T2 and F4 pass. The numbers 9.1 and 9.3 appear nowhere on disk.

4. **The "F2 fails at 221×" verdict is a units artifact, not physics.** It comes from
   dividing the two storage numbers by two different thicknesses.

5. **There is still no real held-out test of the cumulative method.** The walk-forward
   code still runs the old broken incremental solver, and every test fold has zero
   inelastic epochs. The project's #1 stated need — gap-fill skill on hidden data — has
   not been measured at all.

---

## 1. [Theory vs Reality] — Where the Code Leaves the Physics

### 1.1 The production model drops the intercept and uses absolute head (CRITICAL)

The project's own theory paper, `discussions/discussion_20260528_ihm_theory.md`,
Section 3.2 ("Why an intercept is necessary") and equation (11), states the model must be:

    D_k(t) = c + S_ske·ΔH_e + S_skv·ΔH_i

with two requirements:
- an **intercept c** (the layer was already compacting before recording started), and
- head measured as a **change from a reference epoch**: ΔH = H(t) − H(t_ref).

The paper warns in plain words: "Without the intercept, the OLS solver cannot match a
large non-zero mean in D_k(t) using a near-zero-mean head-change signal, and the
estimated coefficients become unreliable."

The production solver does the opposite:
- `scripts/10_ihmf/ihmf_model_v3.py` `fit_two_regressor_nnls_X` (lines 277–324) fits
  `b = S_ke·H + delta·V` with **no intercept** (it is a through-origin NNLS).
- `scripts/10_ihmf/ihmf_io_multilayer.py` line 211 sets `head_m` to the **raw absolute**
  head, and line 220 sets `h_c` to the absolute pre-2015 minimum. Head is never
  zero-referenced in GPS mode.

**The consequence is visible in the output.** `results/ihmf/v3/TUKU_gps_v3_results.json`:
- `S_ke = 0.0` for F1, F2, F3, T1 (lines 27, 36, 45, 63) — NNLS is forced to zero because
  absolute head is a big positive number and cannot fit negative compaction through the
  origin.
- Per-layer R²: F1 = −10.8, F2 = −3.1, F3 = −12.5, F4 = −18.7, T1 = −5.9, T2 = +0.71
  (lines 33, 42, 51, 60, 69, 78). Five of six layers fit worse than a flat mean.
- `r2_insar = −5.03` (line 21).

This is not a "data fit" problem. It is the exact failure the theory paper predicted when
the intercept is removed and head is not referenced.

### 1.2 "Validated Script 12" ≠ "Production solver" (CRITICAL)

Everyone cites Script 12's good R² (F2 = 0.845, F3 = 0.754). But Script 12 is a different
model from the production code:

| Choice | Script 12 (`tau_demo_TUKU/12_stress_strain_per_layer.py`) | Production (`fit_ihm_f_v3.py` + `ihmf_model_v3.py`) |
|---|---|---|
| Head datum | zero-referenced to 2015 (lines 148–151, 179–181) | absolute MSL (`ihmf_io_multilayer.py` line 211) |
| Compaction datum | zero-referenced to 2015 (lines 148–151) | cumsum from 2003 epoch 0 |
| Fit method | two-step decoupled (lines 291–346) | plain NNLS, no decoupling |
| Window | post-2015 only (line 204) | full record |

Because the production code uses absolute head and no intercept, it cannot reproduce
Script 12's results — and it does not. The TRIAGE report
(`discussions/TRIAGE_AUDIT_REPORT_20260608.md` line 120) recorded that
`joint_solve_cumulative()` was **not yet wired in** and warned against wiring it without
approval. The current `fit_ihm_f_v3.py` line 138 **does** call it. So the warning was
overridden, the run was made, and it failed — but the ledger still reports success.

### 1.3 The two-regime model is good physics, but not identifiable for the deep aquifers

The model `b = S_ke·H + (S_kv−S_ke)·V` is a correct bilinear virgin-compression curve.
The elastic slope above the preconsolidation head and the steeper inelastic slope below it
join continuously at h_c. The running-minimum memory term V(t) (computed at
`ihmf_model_v3.py` lines 249–274 and `12_stress_strain_per_layer.py` lines 225–239) is the
right way to carry permanent stress memory. This part is sound.

But for the deep aquifers F2 and F3 — the layers that carry most of the compaction — the
head is below h_c almost the whole record, so the two columns H and V become nearly
identical (collinear). The elastic coefficient is then unidentifiable. The evidence:
`stress_strain_per_layer.json` shows only **6 elastic points for F2** (line 118) and
**7 for F3** (line 206). Script 12's two-step fit gives up and falls back to plain NNLS
for both (`fit_method_2s = "nnls_fallback"`). F3 returns `S_ke = 0` exactly.

So F2's celebrated R² = 0.845 is really a **one-parameter** fit of cumulative compaction
against cumulative head. It is not a validated elastic/inelastic split. The reported S_ke
and the ratio for F2/F3 are products of collinearity, not measurements.

### 1.4 A past "failure explanation" is itself wrong

`discussions/INDEPENDENT_AUDIT_IHM_F_V3_20260607.md` claim #3 says the code should use
"positive = compaction" and needs an added minus sign. This is wrong. It cites a
non-existent "GEMINI.md" rule. The real rule (CLAUDE.md sign table) is
"negative = compaction," and the code is correct. `discussions/PHYSICS_SAFEGUARDS.md`
Finding 2 already refuted this. So one document in the failure history is itself a bug,
not a record of a code bug. Do not act on its claim #3.

---

## 2. [Calculation & Data Vulnerabilities]

### 2.1 Ledger numbers do not match the files (context rot)

CLAUDE.md status block and `PROGRESS.md` line 120 state:
"F1=9.1× PASS, T2=9.3× PASS, F4=17.3× PASS; T1=2.9× FAIL; F2=221× FAIL."

The live `tau_demo_TUKU/results/stress_strain_per_layer.json` says:
- F1: specific ratio **30.36×**, `feasible_2s = false` (S_ske 6.54e-6 below the 7.27e-6
  floor) — lines 35–41. **F1 FAILS, not "9.1× PASS."**
- T2: **8.42×**, feasible TRUE (lines 163–169).
- F4: **10.76×**, feasible TRUE (lines 247–253).
- F2: **220.68×**, feasible FALSE (lines 122–126).

The numbers 9.1 and 9.3 appear nowhere on disk. Only F2 (~221) and the F4 bulk number
17.3 roughly match. **The ledger's "3 layers pass" headline is really "2 layers pass,"
and F1's status is inverted.** Any plan built on the ledger numbers is built on sand.

### 2.2 The specific-storage ratio gate is a mixed-thickness artifact

S_ske is divided by the **total** layer span; S_skv is divided by the **clay-only**
thickness:
- `scripts/guardrails.py` lines 492–495.
- `tau_demo_TUKU/12_stress_strain_per_layer.py` lines 586–588.

So the specific ratio = (bulk mm/m ratio) × (total span ÷ clay thickness). For F2,
106.284 ÷ 12.090 = 8.79. That turns a bulk ratio of 25.1× into a specific ratio of 220.7×.
The Hung et al. (2021) gate of [3, 50] is a **same-thickness** material ratio. Comparing
the mixed-thickness ratio to it is apples-to-oranges. **F2's "221× fail" is a units
artifact, not a physical failure.** The project already half-suspected this (TRIAGE Open
Question 1). This audit confirms it.

### 2.3 The aggregate R²_MLCW_cum = 0.65 is a pooling illusion

`fit_ihm_f_v3.py` lines 441–448 build one R² by concatenating all six layers. Because the
layers have very different magnitudes (F3 ≈ −147 mm vs F1 ≈ −16 mm), the between-layer
spread inflates R² to 0.65 (`TUKU_gps_v3_results.json` line 18) even though every
per-layer R² is negative except T2. **Do not cite the 0.65 figure.**

### 2.4 The walk-forward test proves nothing yet

- It still calls the **deprecated incremental solver**: `run_walk_forward_v3` calls
  `joint_solve_fixed_tau` (`ihmf_model_v3.py` line 871), not the cumulative solver.
- Every fold has **n_inelastic = 0** for all layers (`TUKU_gps_v3_results.json`
  lines 830–980). The held-out test never exercises the inelastic coefficient.
- The reported `rmse_mlcw_mean ≈ 0.2 mm` is tiny only because 5-day increments are tiny.
  It is not gap-fill skill.

**There is no held-out evaluation of the cumulative method.** That is the project's stated
#1 requirement (`PROGRESS.md` lines 18, 275), and it does not exist.

### 2.5 Fragile h_c handling

- Script 12 hardcodes zero-referenced h_c from `tau_results.csv` (lines 77–90) but
  zero-references the runtime GWL using the last pre-2015 value (lines 173–181). If those
  two reference values ever differ, the virgin term V(t) is silently corrupted. They look
  consistent today, but nothing enforces it.
- The GPS loader fallback (`ihmf_io_multilayer.py` line 222) uses the **full-record**
  minimum when fewer than 10 pre-2015 points exist. For F2/F3 wells installed in
  August 2012 this risks a Bug-F regression (h_c pulled too low by post-2015 lows).

### 2.6 The authoritative post-mortem is in the trash

`PROGRESS.md` lines 7 and 167 cite `discussions/POST_MORTEM_INCREMENTAL_CANCELLATION.md`
as the root-cause document. The file is actually at
`trash/POST_MORTEM_INCREMENTAL_CANCELLATION.md`. The ledger points at a path that no
longer exists.

### 2.7 Data-linkage script — mostly clean, two minor risks

`scripts/05_pairing/build_mlcw_insar_gwl_pairs.py`:
- CRS reprojection is correct: GWL (EPSG:3826) is reprojected to InSAR CRS before any
  distance math (line 152). No coordinate bug.
- No timezone bug. `merge_asof` uses naive datetimes with a 3-day tolerance.
- Risk 1: `RADIUS_M = 10000` (line 56) but the docstring and comments say "5 km"
  (lines 27, 36). Documentation contradicts code.
- Risk 2: the wellcode→feather map (line 92) depends on the wellcode staying an 8-digit
  **string**. If the GeoPackage loads it as an integer, leading zeros drop and the join
  silently produces NaN. CLAUDE.md already warns about this class of bug.

### 2.8 The real binding constraint is missing data, not code

`PROGRESS.md` line 154: the F2 and F3 GWL wells start in August 2012, so the 2003–2012
inelastic compaction era has **zero** GWL data. No solver can recover a driver that was
never recorded. This is a genuine physical limit and must shape expectations.

---

## 3. [Strategic Suggestions] — A Physics-Based Path (No Black Boxes)

The objective is gap-fill plus short-horizon prediction of per-layer compaction. The
bilinear Terzaghi/Riley consolidation model is the right physics. Keep it. Fix how it is
estimated and tested.

### Step A — Make the production solver match the theory (do this first)
1. Add the **intercept c** to the cumulative fit (theory §3.2).
2. Use **zero-referenced** head ΔH = H(t) − H(t_ref), not absolute head. This one change
   stops the S_ke = 0 collapse.
3. Make `fit_ihm_f_v3.py` call the **same two-step decoupled fit** as Script 12
   (`fit_two_step_decoupled`), not plain NNLS.
4. Collapse to **one** implementation so "validated" and "production" are the same code.

### Step B — Stop over-claiming the gate
Separate two questions and never mix them again:
- Prediction skill: held-out RMSE and skill score.
- Physical plausibility: parameter ranges.
Test the elastic/inelastic contrast with the **bulk** mm/m ratio (same thickness). Report
specific storage only with matched thickness, or clearly label the mixed-thickness ratio
as not comparable to Hung et al.

### Step C — Build the held-out gap-fill test (in the cumulative domain)
Hold out blocks of MLCW epochs, fit on the rest, predict the hidden **cumulative**
compaction, and compare RMSE to the static linear-interpolation baseline (the project's
own success rule, `PROGRESS.md` lines 18, 275). Do this before any batch run. Do NOT use
the incremental walk-forward as evidence.

### Step D — Be honest about the deep aquifers
For F2/F3, where elastic epochs are essentially absent, fit a single-regressor inelastic
model b = S_kv·V and report S_ke as "not determined." Do not manufacture a ratio from two
collinear columns. (This matches the Script-12 audit's Recommendation 4.)

### Step E — Handle the missing-GWL gaps physically, not by invention
Where GWL exists, use the GWL-driven bilinear model. Where GWL is missing (2003–2012, and
grid points with no well), do not invent head. Instead gap-fill compaction using the
cumulative InSAR signal scaled by the per-layer α you already fit. This stays transparent
and avoids any black-box model. For the regional grid (Objective 3), transfer parameters
by fan zone / hydrofacies using the literature priors as bounds, and validate against
withheld MLCW stations.

### Step F — Freeze the batch run
Do not run all 191 station-layers until Steps A–C are done. The current production path
would write physically meaningless S_ke = 0 / negative-R² results for most layers and
pollute the results tree.

---

## Answers to the Three Orient Questions

- **Were past failure conclusions correct?** The incremental-cancellation post-mortem is
  essentially right: first-differencing destroys the stress memory. But the follow-on
  claim "the cumulative method succeeded" is only true for the standalone Script 12, not
  for the wired production solver, which fails for a separate reason (no intercept +
  absolute head). The project conflated two different implementations.
- **Could failures be coding bugs, not theory?** Yes — the biggest current failure is a
  coding/datum bug (missing intercept, absolute head), not a flaw in consolidation theory.
  The data linkage itself is mostly clean (CRS correct, no timezone bug); the real data
  risk is the absolute-vs-zero-referenced datum inconsistency between the two solvers.
- **Do baselines match the physics?** Effective stress and bilinear consolidation are
  stated correctly in the theory paper, and the V(t) memory term is implemented correctly.
  The deviations are the missing intercept, absolute head, mixed-thickness ratio gate, and
  in-sample-only evaluation.

---

## Verification Notes (how each finding was checked)
- Read the full code of both solvers, the loader, the guardrails, and Script 12.
- Read the live result files `stress_strain_per_layer.json` and `TUKU_gps_v3_results.json`
  and compared every number to the ledger.
- Cross-checked the theory paper, the prior audits, and the triage record.
- No code was run (plan mode). All findings trace to file + line.

AUDIT REPORT COMPLETE - AWAITING USER COMMAND.
