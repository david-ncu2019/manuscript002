# ZERO-TRUST AUDIT EXECUTION LOG — TUKU Pilot

**Auditor:** External Senior Auditor (Claude, zero-trust mandate)
**Execution date:** 2026-06-12/13
**Program:** `discussions/AUDITOR_SUPER_PROMPT_20260612.md` (42 steps, Phases 0–8)
**Environment:** Windows host, Git Bash, `conda run --no-capture-output -n fafalab2 python -` (heredoc stdin; `--no-capture-output` required because plain `conda run` swallows stdin on this host). Repo: `D:/1000_SCRIPTS/004_Project003/20260427_InSAR_MLCW_v2`.

---

## PHASE 0: Depth Verification

PHASE 0 STATUS: **DISCREPANCY** (data files contradict forensic-document depth claims)

EVIDENCE FOUND:
- `data/mlcw/group_byLayer_orig/TUKU_classify_table.csv` (25 data rows)
- `data/mlcw/borehole_materials/YL_WSYL23G1_TUKU_土庫.xlsx`
- `data/gwl/well_info/gwl_allwells_flat.csv` (well 09050331)
- `discussions/F3_FORENSIC_VERDICT_20260612.md` (lines 14, 29, 62, 90, 97)

INDEPENDENT CALCULATION:
- F3 ring depths span 172.889–272.728 m (10 rings). NOT 238–275 m.
- Well 09050331: depth 185.0 m, screen 176.0–179.0 m, elev 17 m MSL.
- Screen [176,179] ⊂ F3 [172.889, 272.728] → overlap = 3 m (screen fully inside F3, 3.1–6.1 m below F3 top).
- Unmonitored lower F3 = 272.728 − 185 = 87.7 m.
- Borehole at screen: 171–176 m = M (cat 5), 176–180 m = Z (cat 5) → screen sits in clay/mud.
- F3 zone (170–280 m): 15/21 intervals category 5 = 71.4%.

STEP RESULTS:
- STEP 0.1: PASS — classify_table read; F3 = 172.889–272.728 m, 25 rows, columns depth,layer.
- STEP 0.2: PASS — screen zone is SOIL_CATEGORY 5 (M/Z); F3 zone 71.4% category 5.
- STEP 0.3: PASS — well_depth 185.0 m, screen 176–179 m, elev 17 m MSL.
- STEP 0.4: PASS (assertion confirmed) — well IS within F3; prior "79 m gap, 0 m overlap" claim is FALSE by direct interval arithmetic.
- STEP 0.5: FAIL (expected outcome not reproduced) — prescribed grep pattern returned 0 matches in CLAUDE.md. Auxiliary: CLAUDE.md layer table states F3 = 140–275 m vs classify_table 172.9–272.7 m (discrepancy exists but is invisible to the prescribed regex).
- STEP 0.6: PASS (contradictions found) — F3_FORENSIC_VERDICT_20260612.md line 14 ("clay at 238–275 m, 79 m too shallow") FALSE; line 29 ("79 m gap, 0 m overlap") FALSE; lines 62/90/97 ("238–275 / 240–275 m", "no piezometer in F3 clay") MISLEADING — the assigned screen is inside F3 and inside clay; only lower F3 (185–272.7 m) is unmonitored.

AUDITOR VERDICT: The forensic document's central geometric premise is numerically false. The piezometer screen lies inside layer F3 and inside clay-category material. The defensible statement is an 87.7 m unmonitored lower-F3 interval, not "0 m overlap". Any conclusion in F3_FORENSIC_VERDICT built on "79 m gap" must be re-derived.

---

## PHASE 1: Sign Convention & Provenance Audit

PHASE 1 STATUS: **DISCREPANCY** (sign violations in 5/6 layers; provenance mask contradicts field data)

EVIDENCE FOUND:
- `tau_demo_TUKU/results/reconstruction/TUKU_{F1..F4}_reconstruction.csv`
- `tau_demo_TUKU/results/timeseries/TUKU_F1_cumulative_timeseries.csv`
- `tau_demo_TUKU/results/mlcw_observed_epoch_mask.csv`
- `data/mlcw/group_byLayer_orig/TUKU_orig_grouped.csv`

INDEPENDENT CALCULATION:
- Positive `b_observed_mm` counts (convention says ≤ 0 always): F1=35, T1=0, F2=5, T2=215, F3=19, F4=25 of 1571 epochs each. Example magnitudes sub-mm (T2 +0.254 mm, F3 +0.751 mm).
- GPS surface (F1 file): 1081 epochs, range [−788.36, −127.77] mm, 0 positive.
- Head zero-ref range: [−5.70, +0.92] m.
- Provenance mask: 1571–1572 epochs marked observed per layer; 1479–1480 are false positives (mask date not in original field file); 172 original dates missing from mask. Only ~92 mask dates match genuine field dates.
- Post-2024 field file: 22 values/layer, 100% non-integer.

STEP RESULTS:
- STEP 1.1: FAIL — positive b_observed_mm in 5/6 layers (T2 worst: 215/1571 = 13.7% positive epochs). Program expected 0.
- STEP 1.2: PASS — GPS all negative (0 positive of 1081).
- STEP 1.3: PASS — head within [−50, +50] m; no negation signature.
- STEP 1.4: FAIL — false_positives ≈ 1479 per layer (expected ≤ 0). The "observed epoch mask" marks ~94% of marked epochs on dates absent from the original field file. Either the mask is not a genuine-observation marker, or its dates were re-gridded; in both cases it cannot serve as provenance evidence as-is.
- STEP 1.5: PASS — post-2024 data 100% non-integer (provenance warning confirmed: computer-smoothed, not raw ring readings).

AUDITOR VERDICT: The reconstruction CSVs' "observed" column is not raw field data — it contains positive (uplift) values that genuine compaction convention forbids, and the observed-epoch mask flags 17x more epochs than exist in the field file. "b_observed_mm" is an interpolated/processed series masquerading as observation. Sign violations are small in magnitude (sub-mm) but the provenance chain is broken.

---

## PHASE 2: Core Metric Verification

PHASE 2 STATUS: **DISCREPANCY** (anti-phase rate 23.5% file vs 39.6% recomputed; otherwise core metrics reproduce)

EVIDENCE FOUND:
- `tau_demo_TUKU/results/reconstruction/TUKU_carrier_reconstruction_summary.json`
- `tau_demo_TUKU/results/reconstruction/TUKU_{F1..F4}_reconstruction.csv`
- `tau_demo_TUKU/results/auditor_diagnostics/sign_error_log.csv`
- `tau_demo_TUKU/results/auditor_diagnostics/cross_layer_consistency.csv`
- `tau_demo_TUKU/results/characterization/TUKU_storage_params.json`

INDEPENDENT CALCULATION:
- Σ a_k = 0.6370 (file claims 0.637022) ≤ 1.0. Confirmed.
- Identity a_k·d_GPS + c_k = b_model: max dev F3 = 1.44e-4 mm, F4 = 2.98e-4 mm (consistent with 4-decimal CSV rounding; program's "<1e-6" threshold technically not met but identity holds at file precision).
- GWL component std: F1 0.28, T1 0.52, F2 1.49 (largest, range [−5.99,+2.05] mm), T2 1.16 mm.
- Tail skill (top-level `tail_evaluation` key — program code looked per-layer and got None): F1 −0.1813, T1 +0.4075, F2 +0.4305, T2 +0.2981, F3 −0.2488, F4 −0.1425. n_tail=36 epochs each. 4/6 layers ≤ 0 incl. F1.
- F3 sign-reversal: 220/560 = 39.3% (exact match to claim). Worst 5 reversals: 2023-06-01/06/11/16/21, obs ≈ −0.5 mm vs pred ≈ +0.21 mm.
- F2/F3 anti-phase: file column mean = 23.5% (matches claim); independent recomputation from reconstruction CSVs (sign of increments, |inc| > 0.1 mm) = 39.6%. 16.1 pp discrepancy.
- Storage: F2 S_skv = 1.34e-3 m⁻¹ (ratio 1.01 vs Hung 2021 middle fan 1.33e-3; within 10%). F3: S_ke=0, S_kv=23.693, r2_cum=−2.794, τ=120 (at boundary). F4: S_ke=0, S_kv=8.695, r2_cum=−1.409.

STEP RESULTS:
- STEP 2.1: PASS — Σ a_k = 0.6370 ≤ 1.0; file value agrees.
- STEP 2.2: PASS — identity holds to 3e-4 mm (CSV rounding); strict <1e-6 expectation overtight.
- STEP 2.3: PASS — non-zero GWL terms, F2 largest.
- STEP 2.4: PASS (with code-structure caveat) — program's per-layer lookup returned None; actual top-level values confirm T1/F2/T2 > 0, F1/F3/F4 < 0.
- STEP 2.5: PASS — 39.3% reproduced exactly; June 2023 clustering confirmed.
- STEP 2.6: FAIL/DISCREPANCY — 23.5% (stored) vs 39.6% (recomputed). The stored anti-phase flag and the program's prescribed recomputation do not agree; definitions differ or stored flag is wrong.
- STEP 2.7: PASS — F2 S_skv within 1% of literature; F3/F4 inelastic-only confirmed; F3/F4 negative cumulative R² recorded.

AUDITOR VERDICT: Headline numbers (Σa_k, 39.3% F3 sign reversal, F2 S_skv) reproduce exactly from data. Two problems: (1) the anti-phase metric is definition-unstable — 23.5% vs 39.6% depending on computation, so any narrative built on "23.5%" is fragile; (2) tail skill shows 3/6 layers positive, 3/6 negative (incl. F1) — the "4/6 layers fail 6-month tail" phrasing in CLAUDE.md status is consistent with F1, F3, F4 < 0 plus one more only if T2 (+0.30) is miscounted; data says exactly 3/6 fail, not 4/6. DISCREPANCY with CLAUDE.md claim "4/6 layers fail 6-month tail prediction".

---

## PHASE 3: Guardrails Code Audit

PHASE 3 STATUS: **DISCREPANCY** (G1, G3, G4, G5 confirmed; G2-style warning loss NOT demonstrated; G7 REFUTED)

EVIDENCE FOUND:
- `scripts/guardrails.py` (functions exercised live in fafalab2)
- Call sites: `tau_demo_TUKU/15_storage_characterization.py:241` (NO material=), `tau_demo_TUKU/seq/23_dense_calibration.py:348` (material= passed), `tau_demo_TUKU/seq/28_f3_tau_uncapped.py:331` (material= passed)

INDEPENDENT CALCULATION:
- 3.2: F1 test vector (S_ke=2.626, S_kv=4.315): with material → 0 errors/0 warnings; without material → 0/0. Warnings lost = 0.
- 3.3: validate_ratio_gate(S_ske_m1=1e-15, S_skv_m1=2e-8) → warning "S_skv/S_ske = 20000000.0x > 50x — inelastic storage implausibly large". False alarm for S_ske≈0 confirmed.
- 3.4: validate_clay_layer_behavior(S_ke=0, clay) → [] (silent).
- 3.5: validate_literature_bounds(proximal, S_skv=5e-4) → [] (silent).
- 3.6: validate_virgin_term([0,−0.1,−0.2,NaN,NaN,−0.5,−0.4]) → RAISED "V(t) increases at 1 epochs".

STEP RESULTS:
- STEP 3.1: PASS — 15_storage_characterization.py:241 omits material= (G1 confirmed); seq/23 and seq/28 pass it.
- STEP 3.2: FAIL (expected warning-loss not reproduced) — material makes no difference for the prescribed test vector.
- STEP 3.3: PASS — G3 confirmed (false "implausibly large" warning when elastic storage ≈ 0).
- STEP 3.4: PASS — G4 confirmed (clay/S_ke=0 check silently bypassed).
- STEP 3.5: PASS — G5 confirmed (proximal-fan inelastic silently accepted).
- STEP 3.6: FAIL (G7 REFUTED) — NaN block does NOT hide the V(t) increase; GuardrailViolation raised correctly.

AUDITOR VERDICT: Guardrails have real blind spots (G3 misdiagnoses zero-elastic layers, G4/G5 are silent on physically suspicious cases, and the production characterization script bypasses material-dependent checks entirely), but two of the alleged gaps (G2-style warning loss, G7 NaN invisibility) are not real. The guardrail suite is weaker than documented in some places and stronger in others — its documentation does not match its behavior in either direction.

---

## PHASE 4: Kalman Filter Feasibility

PHASE 4 STATUS: **PASS**

EVIDENCE FOUND:
- `tau_demo_TUKU/results/reconstruction/TUKU_{F1..F4}_reconstruction.csv` (d_surface_mm columns)
- `tau_demo_TUKU/results/seq/frozen_calibration.json` (a_total = 0.559188)
- `tau_demo_TUKU/results/reconstruction/TUKU_carrier_reconstruction_summary.json`

INDEPENDENT CALCULATION:
- SVD of 6-layer carrier matrix: SV1 = 4.15e4, SV2/SV1 = 1.76e-16 → exact rank-1 (all six layer carriers are the same GPS signal).
- Kalman gain, annual cadence (Q=9, R=4, n_gap=73): P_prior = 657 mm², K = 0.9939 (> 0.99) → M8 hard level-reset ≈ optimal Kalman at annual cadence.
- Monthly cadence (n_gap=6): P_prior = 54 mm², K = 0.9310 (< 0.99) → Kalman materially differs from hard reset at monthly cadence.
- Predict-only scalar Kalman: final z = −368.8 mm, final P = 9724 mm², 90% half-width = 162.2 mm — uncertainty grows without bound between visits, unlike static conformal bands.
- Per-layer split: F1 3.9%, T1 2.8%, F2 36.1%, T2 4.2%, F3 48.0%, F4 5.0%; fractions sum = 1.0000.

STEP RESULTS:
- STEP 4.1: PASS — rank-1 degeneracy confirmed (SV2/SV1 = 1.76e-16 < 1e-15).
- STEP 4.2: PASS — K = 0.9939 at annual cadence.
- STEP 4.3: PASS — K = 0.9310 at monthly cadence.
- STEP 4.4: PASS — tracker runs; interval growth confirmed (162.2 mm at series end with no updates).
- STEP 4.5: PASS — fractions sum to 1.0; F3 largest at 48.0%.

AUDITOR VERDICT: The Kalman math holds. At annual visit cadence the Kalman update is numerically indistinguishable from the existing M8 hard reset (K = 0.994), so a Kalman filter adds value only at monthly-or-denser cadence (K = 0.93) or through its honest, growing uncertainty band. The rank-1 SVD also proves the per-layer "reconstruction" carries zero independent layer information beyond the fixed a_k split of one GPS curve.

---

## PHASE 5: ARX / Prophet / MCR-AR Re-Evaluation

PHASE 5 STATUS: **DISCREPANCY** (ARX result contradicts the program's own expectation; Prophet SKIP; MCR-AR adds no value)

EVIDENCE FOUND:
- `results/arx_OBSOLETE_temporal_methods/` (84 files, exists)
- `notes/methods/discussion_20260517_arx_results.md` (92.1% claim, anchor-only, phi_k present)
- `results/prophet_OBSOLETE_ablation/` (3 entries) + `notes/methods/discussion_20260517_prophet_tuku.md`
- `data/mlcw/group_byLayer_orig/TUKU_orig_grouped.csv`, `tau_demo_TUKU/results/reconstruction/TUKU_F1/F2/F3_reconstruction.csv`

INDEPENDENT CALCULATION:
- ARX(1) refit on current field data: phi = 0.9767 (≈1.0 confirmed), beta = 0.0153. Walk-forward RMSE 5.53 mm vs hold-last baseline 70.45 mm → 92.2% improvement. This REPRODUCES the documented 92.1% median but CONTRADICTS the program's expectation "improvement < 5%". The "<5%" expectation conflated the hold-last baseline with the anchor-only (anchor+carrier) baseline. Code disclosure: added a minimal length-truncation guard before column_stack to prevent shape mismatch; mask logic unchanged.
- Prophet: not installed in fafalab2 → SKIP per rules.
- MCR-AR (F2/F3 observed, 1571 epochs): SV = [4745.4, 418.9], SV2/SV1 = 0.0883 < 0.1 → only ONE meaningful component by the program's own criterion (rank-degeneracy confirmed from a second angle). MCR-AR R²: F2 = 0.4665, F3 = 0.4767. Prescribed carrier comparison produced NaN (b_model_mm NaNs inside obs-valid epochs). AUDITOR SUPPLEMENT (jointly valid epochs): carrier R² F2 = 0.9913 (n=823), F3 = 0.9806 (n=1081). MCR-AR is far inferior; delta ≈ −0.52/−0.50. Code disclosure: added S_new transpose for shape orientation (square 2×2 — no numeric effect on convergence path verified by convergence at iter 41).

STEP RESULTS:
- STEP 5.1: PASS — ARX artifacts exist; 92.1% claim, anchor-only ablation, phi_k model all present in discussion file.
- STEP 5.2: PASS — Prophet artifacts exist; deep improvement (+50–66% at 225–275 m) and shallow degradation (−62% to −218% at 0–75 m) claims found; "ARX generally superior" confirmed in text.
- STEP 5.3: FAIL of program expectation / PASS of historical claim — ARX improvement 92.2% vs hold-last (program expected < 5%). phi ≈ 1.0 confirmed.
- STEP 5.4: SKIP — Prophet not installed in fafalab2.
- STEP 5.5: PASS (degeneracy confirmed) — SV2/SV1 = 0.088 < 0.1 → one component; MCR-AR R² ≈ 0.47 << carrier R² ≈ 0.98–0.99. MCR-AR adds no value.

AUDITOR VERDICT: The historical ARX rejection narrative needs precision: ARX beats a naive hold-last baseline by 92% (real), and the original docs rejected it only because an anchor-only model did equally well — meaning phi≈1 ARX is just an anchor + carrier in disguise, not because ARX fails. MCR-AR is a dead end: the F2/F3 observed pair is effectively one component (SV2/SV1 = 0.088) and MCR-AR reconstructs less than half the variance the carrier already explains.

---

## PHASE 6: Sequential Rehearsal Verification

PHASE 6 STATUS: **FAIL/DISCREPANCY** (RMSE cross-check fails all 6 layers; coverage file contradicts all coverage claims)

EVIDENCE FOUND:
- `tau_demo_TUKU/results/seq/semiannual/metrics.json` + `TUKU_{layer}_seq_timeseries.csv`
- `tau_demo_TUKU/results/seq/transparency/TUKU_{layer}_transparency_data.csv`
- `tau_demo_TUKU/results/auditor_diagnostics/auditor_summary.json`
- `tau_demo_TUKU/results/seq/red_team_fixes/honest_skill_table.json` (located by the program's own glob; prescribed path `red_team_fixes/anchor_once/...` does not exist)
- `tau_demo_TUKU/seq/time_oracle.py` via grep of seq scripts 24/25/28

INDEPENDENT CALCULATION:
- Semiannual RMSE, claimed (metrics.json) vs recomputed (pred at is_reveal epochs vs obs_verified): F1 2.720/2.092, T1 2.002/2.145, F2 4.800/6.544, T2 2.032/3.353, F3 9.358/1.753, F4 2.496/0.308 mm. ZERO matches at 0.01 mm tolerance. The reveal set used by metrics.json is not the transparency file's is_reveal set.
- Coverage (auditor_summary.json seq_coverage): in_band_fraction = 0.0–33.3% across ALL layers and ALL cadences (T2 = 0% everywhere; best = 33.3% F3/F4). 0/6 layers pass 0.85 at semiannual (Red Team said 3/6 fail; this file says 6/6 fail). Program expectation "monthly 5/6 pass" also contradicted (0/6). NOTE: fractions quantized at 1/6 and 2/6 suggest n=6 scoring points per cell — the coverage metric in this file may be computed on a 6-point subset, which is itself a red flag (insufficient n for a coverage claim).
- Honest skill (post-entry, vs anchor-once): annual F2 = −0.0176, T2 = −0.0921, F3 = +0.1882; monthly F2 = +0.2308, F3 = +0.5581, F4 = −0.2029. Red Team numbers reproduced (probe F3 7.1 vs file 7.2011; F2 3.8 vs 3.8302).
- TimeOracle: class exists (`tau_demo_TUKU/seq/time_oracle.py`), imported and armed in 24_walk_forward_rehearsal.py, 25_confirmatory_2024.py, 28_f3_tau_uncapped.py; "backward advance raises LeakageError".

STEP RESULTS:
- STEP 6.1: FAIL — 0/6 layers reproduce claimed RMSE from the prescribed reveal definition. Largest: F3 claimed 9.358 vs recomputed 1.753 mm (5.3x); F4 claimed 2.496 vs 0.308 mm (8.1x).
- STEP 6.2: FAIL — all coverage values 0–33.3%; no cadence achieves 0.85 anywhere. Both the Red Team "3/6" claim and the "monthly 5/6 pass" expectation are contradicted by the data file.
- STEP 6.3: PASS — honest skill table confirms Red Team: annual F2/T2 ≤ 0, F3 = +0.19 (file at red_team_fixes/ root, not anchor_once/ subdir).
- STEP 6.4: PASS — TimeOracle leakage guard exists and is wired into the walk-forward scripts.

AUDITOR VERDICT: The sequential-rehearsal bookkeeping cannot currently be reconciled with itself. Claimed per-layer RMSEs come from a scoring set that the transparency files do not reproduce, and the stored coverage fractions (0–33%, quantized at n=6) are irreconcilable with any "85% coverage" narrative. The honest-skill remediation, by contrast, checks out exactly. Until metrics.json, transparency CSVs, and auditor_summary coverage are regenerated from one consistent scoring set, no sequential-rehearsal performance claim should be cited.

---

## PHASE 7: Cross-Layer & Regime Diagnostics

PHASE 7 STATUS: **PASS** (with two precision corrections)

EVIDENCE FOUND:
- `tau_demo_TUKU/results/auditor_diagnostics/per_layer_regime_epochs.csv`
- `tau_demo_TUKU/results/auditor_diagnostics/cross_layer_consistency.csv`

INDEPENDENT CALCULATION:
- Regime fractions (inelastic): F1 92.9%, T1 89.0%, F2 99.2%, T2 59.2%, F3 99.1%, F4 29.0%.
- F3 head-compaction mismatches by month (n=276): Jun 53 (19.2%), Aug 41, May 36, Jul 33, Sep 29 — wet season May–Sep = 192/276 = 70%.
- Column closure: p50 22.54 mm, p95 256.46 mm, max 712.44 mm, mean signed +76.77 mm.

STEP RESULTS:
- STEP 7.1: PASS (minor deviation) — F3 = 99.1% inelastic, not the claimed ≈97% (2.1 pp); F2 99.2% and F4 29.0% match claims.
- STEP 7.2: PASS (claim precision corrected) — June is the modal month (53/276 = 19.2%) but does not "dominate"; the wet season May–Sep accounts for 70%.
- STEP 7.3: PASS — p95 = 256.46 mm, within 0.2% of the 256 mm claim.

AUDITOR VERDICT: The diagnostics files are internally consistent and the closure-error claim reproduces exactly. The physically damning number stands: the six per-layer reconstructions miss column closure by up to 712 mm with a median 23 mm — confirming the carrier "decomposition" does not conserve the column. The seasonal mismatch story should say "wet-season clustering (70% May–Sep)", not "June".

---

## PHASE 8: Final Verdict Assembly

PHASE 8 STATUS: **COMPLETE**

### Step 8.1 — Full 42-step table

| Phase | Step | Status | Evidence |
|-------|------|--------|----------|
| 0 | 0.1 | PASS | F3 = 172.889–272.728 m per classify_table (25 rows) |
| 0 | 0.2 | PASS | Screen 176–179 m in M/Z (cat 5); F3 zone 71.4% cat 5 |
| 0 | 0.3 | PASS | Well 09050331: depth 185 m, screen 176–179 m, elev 17 m MSL |
| 0 | 0.4 | PASS | Screen ⊂ F3; 87.7 m lower F3 unmonitored; "79 m gap, 0 m overlap" FALSE |
| 0 | 0.5 | FAIL | Prescribed grep: 0 matches in CLAUDE.md (expectation not reproduced); F3 "140–275 m" table entry mismatches classify_table but is invisible to the regex |
| 0 | 0.6 | PASS | Forensic doc lines 14/29 FALSE, lines 62/90/97 MISLEADING vs data |
| 1 | 1.1 | FAIL | Positive b_observed_mm: F1 35, F2 5, T2 215, F3 19, F4 25 (expected 0) |
| 1 | 1.2 | PASS | GPS 1081 epochs, [−788.36, −127.77] mm, 0 positive |
| 1 | 1.3 | PASS | Head [−5.70, +0.92] m, no negation |
| 1 | 1.4 | FAIL | ~1479 false-positive "observed" epochs per layer (expected ≤ 0) |
| 1 | 1.5 | PASS | Post-2024: 22 values/layer, 100% non-integer (smoothed) |
| 2 | 2.1 | PASS | Σa_k = 0.6370 = file claim, ≤ 1.0 |
| 2 | 2.2 | PASS | Identity max dev 3e-4 mm (CSV rounding); <1e-6 expectation overtight |
| 2 | 2.3 | PASS | GWL component non-zero; F2 largest (std 1.49 mm) |
| 2 | 2.4 | PASS* | tail_evaluation is top-level, not per-layer (program code bug); T1 +0.41, F2 +0.43, T2 +0.30; F1 −0.18, F3 −0.25, F4 −0.14 |
| 2 | 2.5 | PASS | F3 sign-reversal 220/560 = 39.3% exact; worst 5 in June 2023 |
| 2 | 2.6 | FAIL | Anti-phase: stored 23.5% vs recomputed 39.6% (16.1 pp gap) |
| 2 | 2.7 | PASS | F2 S_skv = 1.34e-3 m⁻¹ (ratio 1.01 vs Hung); F3 r2_cum = −2.794 |
| 3 | 3.1 | PASS | 15_storage_characterization.py:241 omits material= (G1) |
| 3 | 3.2 | FAIL | No warning difference with/without material (0 vs 0) — G2 loss not demonstrated |
| 3 | 3.3 | PASS | G3 confirmed: false "implausibly large" (2e7×) when S_ske≈0 |
| 3 | 3.4 | PASS | G4 confirmed: clay + S_ke=0 → silent |
| 3 | 3.5 | PASS | G5 confirmed: proximal inelastic → silent |
| 3 | 3.6 | FAIL | G7 REFUTED: NaN does not hide V(t) increase; violation raised |
| 4 | 4.1 | PASS | SV2/SV1 = 1.76e-16 → exact rank-1 |
| 4 | 4.2 | PASS | K = 0.9939 (annual) ≈ hard reset |
| 4 | 4.3 | PASS | K = 0.9310 (monthly) ≠ hard reset |
| 4 | 4.4 | PASS | a = 0.5592; predict-only 90% half-width 162.2 mm at end |
| 4 | 4.5 | PASS | Fractions sum 1.0; F3 = 48.0% of column |
| 5 | 5.1 | PASS | ARX dir (84 files); 92.1% claim + anchor-only + phi_k in doc |
| 5 | 5.2 | PASS | Prophet dir (3 entries); deep +50–66% / shallow −62 to −218% claims found |
| 5 | 5.3 | FAIL† | ARX improvement 92.2% vs hold-last (program expected <5%); φ = 0.9767; reproduces historical 92.1% |
| 5 | 5.4 | SKIP | Prophet not installed in fafalab2 |
| 5 | 5.5 | PASS | SV2/SV1 = 0.0883 < 0.1 → one component; MCR-AR R² 0.47 << carrier 0.98–0.99 |
| 6 | 6.1 | FAIL | 0/6 RMSE claims reproduce (F3 9.358 vs 1.753; F4 2.496 vs 0.308 mm) |
| 6 | 6.2 | FAIL | Coverage 0–33.3% everywhere; 0/6 ≥ 0.85 at every cadence |
| 6 | 6.3 | PASS | Honest annual skill F2 −0.0176, T2 −0.0921, F3 +0.1882 (Red Team confirmed); file at red_team_fixes/ root |
| 6 | 6.4 | PASS | TimeOracle + LeakageError wired in seq/24, 25, 28 |
| 7 | 7.1 | PASS | F3 99.1% inelastic (claim ≈97%, 2.1 pp off); F2 99.2%, F4 29.0% |
| 7 | 7.2 | PASS | June modal (53/276 = 19.2%); wet season May–Sep = 70% — "dominance" overstated |
| 7 | 7.3 | PASS | Closure p95 = 256.46 mm (claim 256); max 712.44 mm |
| 8 | 8.1 | PASS | This table |

\* PASS after correcting the program's per-layer key lookup. † FAIL of the program's expectation; the historical claim itself reproduced.

### Final assertions

1. **Depth claims contradicted by authoritative files? YES.** F3_FORENSIC_VERDICT: "clay 238–275 m, 79 m gap, 0 m overlap" vs classify_table F3 = 172.889–272.728 m and screen 176–179 m INSIDE F3 (3 m overlap, in clay). CLAUDE.md table "F3 140–275 m" also disagrees with the classify_table.
2. **Sign conventions hold? NO.** b_observed_mm > 0 at F1 35, F2 5, T2 215, F3 19, F4 25 epochs (sub-mm magnitudes). GPS (0 positive) and head ([−5.70, +0.92] m) clean.
3. **Σa_k constraint satisfied? YES.** 0.6370 ≤ 1.0, matches file (0.637022).
4. **39.3% and 23.5% reproduced? SPLIT.** Sign-reversal: YES — 220/560 = 39.3% exact. Anti-phase: NO — stored 23.5% vs independent recomputation 39.6%.
5. **Guardrail gaps G1–G7:** G1 CONFIRMED (material omitted at 15_storage_characterization.py:241). G2-style warning loss NOT DEMONSTRATED (0 warnings either way). G3 CONFIRMED. G4 CONFIRMED. G5 CONFIRMED. G6 NOT TESTED (no step exercised it). G7 REFUTED (violation raised despite NaN block).
6. **Kalman viable replacement for M8? NO at current cadence.** K = 0.9939 at annual visits — numerically the same as the M8 hard reset. It only differs at monthly cadence (K = 0.9310) and adds honest growing uncertainty (162 mm half-width after the full unanchored span). Complement, not replacement.
7. **ARX/Prophet rejection confirmed? PARTIALLY.** ARX re-fit: φ = 0.9767 ≈ 1, 92.2% improvement over naive hold-last — reproducing the historical 92.1% and consistent with ARX ≈ anchor + carrier (its skill is the anchor, not the AR dynamics). Prophet untestable (not installed). No evidence overturning the rejection; the program's own "<5%" expectation was wrong.
8. **MCR-AR adds value? NO.** F2/F3 observed matrix has SV2/SV1 = 0.0883 (< 0.1 → effectively one component); MCR-AR R² 0.467/0.477 vs carrier 0.9913/0.9806 on jointly valid epochs.
9. **Sequential coverage claims hold? NO.** auditor_summary.json: in_band 0–33.3% for every layer at every cadence (0/6 ≥ 0.85); and metrics.json RMSEs fail the transparency-file cross-check 6/6.
10. **Ready for Part 2? NO.** Blockers: (a) F3 forensic geometric premise false — re-derive the driver-mismatch story with correct geometry; (b) seq metrics.json / transparency CSVs / coverage summary mutually irreconcilable — regenerate from one scoring set; (c) provenance mask marks ~17× more "observed" epochs than the field file contains; (d) anti-phase metric definition-unstable (23.5% vs 39.6%); (e) column closure error up to 712 mm (p95 256 mm); (f) tail skill < 0 for F1, F3, F4 (3/6 layers, not the documented 4/6).

### CERTIFICATE

**FEASIBILITY DEATH CERTIFICATE — per-layer carrier reconstruction at sparse cadence (TUKU pilot, as currently validated).**

Decisive numeric facts:
1. **SV2/SV1 = 1.76e-16** — the six "per-layer" reconstructions are one GPS curve split by fixed constants; they contain zero independent layer information.
2. **Honest post-entry annual skill: F2 = −0.018, T2 = −0.092** (and tail skill < 0 for F1/F3/F4) — at realistic annual visit cadence, half the column is predicted no better than an anchor-once straight line.
3. **Coverage 0.0–33.3% for all 6 layers at all 6 cadences** (auditor_summary.json) and **0/6 claimed seq RMSEs reproducible** from the transparency files — the validation bookkeeping does not support any reliability claim.
4. **Column closure error p95 = 256 mm, max = 712 mm** — the layer split does not conserve the physical column.
5. **F3 sign-reversal rate 39.3%** (220/560) with 70% of head-compaction mismatches in the May–Sep wet season — the dominant layer (48% of the column) has no working sub-annual physics under this model.

Scope and what survives: this certificate kills the claim "per-layer compaction can be reconstructed and predicted at TUKU from GPS/InSAR + GWL at sparse revisit cadence, as validated." It does NOT kill: (i) the column-total anchored tracker (monthly honest skill +0.23 to +0.56; F3 annual +0.19), (ii) the F2 storage characterization (S_skv within 1% of Hung et al. 2021), (iii) the Red Team remediation integrity (honest_skill_table reproduces its claims to 0.1 mm). Part 2 (37 stations) must remain BLOCKED.

Audit executed 2026-06-12/13, env fafalab2 via `conda run --no-capture-output`, all numbers from files on disk listed per phase above.
