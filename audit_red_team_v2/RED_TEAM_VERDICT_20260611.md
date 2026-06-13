# RED TEAM VERDICT — TUKU Single-Well Sequential Estimator (M8/M9)

**Auditor:** Independent Red Team, zero-trust protocol, 2026-06-11
**Method:** Every metric recomputed from raw disk artifacts with fresh code
(`audit_red_team_v2/red_team_audit.py`, `probe_offset.py`). No project
evaluation code reused. Ground truth = the 264 genuine field visits in
`data/mlcw/group_byLayer_orig/TUKU_orig_grouped.csv`. Matching =
`merge_asof(direction='nearest', tolerance=3 days)`; 0 of 60 blind-era genuine
visits failed to match.

---

## 1. Physical story first

Six sediment layers at TUKU compacted a further ~72 mm (F3) and ~45 mm (F2)
during the blind 2019–2023 window while the frozen carrier+head model walked
forward with periodic bias resets at simulated field visits. The model entered
the blind era already 44.3 mm (F3) and 19.3 mm (F2) away from the true datum —
an offset accumulated during the unanchored 2015–2018 seed walk, not during
the blind era. Between resets the model tracks the secular trend tightly and
injects head-driven seasonal motion; for F2 that motion co-moves with the real
layer (detrended Pearson r = 0.61 at annual cadence), but for F3 the motion is
phase-shifted by roughly half a year (consolidation lag capped at 600 days
versus a true lag of at least 815 days), so during the single 2021–2022
drought of the record the F3 error swung from +15.9 mm to −24.2 mm before a
reveal pulled it back to zero.

---

## 2. Claimed vs independently computed (blind 2019–2023, 60 genuine visits)

Every claimed MAE, RMSE, and band-coverage value reproduced to the third
decimal. **The blind-era arithmetic is honest. No fabrication detected.**

| Sched | Layer | MAE clm | MAE ind | RMSE clm | RMSE ind | Cov clm | Cov ind (n band pts) | R² ind | Detr. r ind | Amp ratio ind |
|---|---|---|---|---|---|---|---|---|---|---|
| annual | F1 | 2.088 | 2.088 | 2.399 | 2.399 | 0.857 | 0.857 (14) | 0.155 | −0.070 | 0.62 |
| annual | T1 | 1.366 | 1.366 | 1.808 | 1.808 | 1.000 | 1.000 (14) | 0.516 | 0.542 | 1.05 |
| annual | F2 | 3.478 | 3.478 | 4.602 | 4.602 | 0.857 | 0.857 (14) | 0.909 | 0.614 | 0.82 |
| annual | T2 | 1.901 | 1.901 | 2.567 | 2.567 | 0.929 | 0.929 (14) | 0.308 | 0.363 | 1.19 |
| annual | F3 | 4.596 | 4.596 | 8.144 | 8.144 | 0.643 | 0.643 (14) | 0.857 | 0.216 | 1.15 |
| annual | F4 | 1.138 | 1.138 | 1.668 | 1.668 | 0.929 | 0.929 (14) | 0.567 | 0.075 | 0.76 |
| semiann | F1 | 2.169 | 2.169 | 2.720 | 2.720 | 0.667 | 0.667 (27) | −0.087 | 0.248 | 1.29 |
| semiann | T1 | 1.643 | 1.643 | 2.002 | 2.002 | 0.815 | 0.815 (27) | 0.407 | 0.369 | 0.97 |
| semiann | F2 | 3.322 | 3.322 | 4.800 | 4.800 | 0.852 | 0.852 (27) | 0.901 | 0.590 | 0.86 |
| semiann | T2 | 1.651 | 1.651 | 2.032 | 2.032 | 0.852 | 0.852 (27) | 0.567 | 0.475 | 0.99 |
| semiann | F3 | 5.653 | 5.653 | 9.358 | 9.358 | 0.778 | 0.778 (27) | 0.811 | 0.211 | 1.44 |
| semiann | F4 | 1.746 | 1.746 | 2.496 | 2.496 | 0.889 | 0.889 (27) | 0.031 | −0.093 | 1.40 |
| monthly | F3 | 3.067 | 3.067 | 6.532 | 6.532 | 0.867 | 0.867 (60) | 0.908 | 0.601 | 1.33 |
| none | F2 | 21.170 | 21.170 | 21.430 | 21.430 | 0.000 | 0.000 (3) | −0.981 | 0.843 | 0.68 |
| none | F3 | 43.985 | 43.985 | 44.560 | 44.560 | 0.000 | 0.000 (3) | −3.282 | −0.309 | 0.37 |

Definitions: residual = obs − pred (pre-assimilation, verified); detrended r =
zero-reference both matched series, remove straight line versus real elapsed
days, Pearson r; amplitude ratio = detrended std(pred)/std(obs) at matched
dates. Full table for all 24 schedule×layer cells:
`audit_red_team_v2/independent_metrics.csv`.

**2024 confirmatory: UNVERIFIABLE.** No 2024 prediction timeseries exists on
disk (latest persisted epoch = 2023-12-26 across all schedules). The
confirmatory claims (annual F3 RMSE 6.020 mm, coverage 0/2, etc.) exist only
inside `confirmatory_2024.json` and cannot be recomputed from persisted
outputs. The 12 claimed 2024 grading dates do all match raw genuine visits
within 3 days (12/12), so the grading set is real even if the grades are not
reproducible.

---

## 3. Red-team findings beyond the arithmetic

**F-1 — Skill scores are inflated by a contaminated baseline.** The
"persistence/none" baseline (F3 = 44.56 mm, F2 = 21.43 mm RMSE) is dominated
by a datum offset inherited at the blind-era start: F3 residual was already
−44.3 mm at the FIRST blind visit (2019-01-09) and grew to only −54.8 mm by
2023-12 (incremental no-visit drift ≈ 10.5 mm over 5 years, ≈ 2.1 mm/yr); F2
went −19.3 mm → −21.9 mm (incremental drift ≈ 2.6 mm over 5 years). A fair
"anchor-once-then-carrier" baseline scores ≈ 7.1 mm RMSE (F3) and ≈ 3.8 mm
(F2). Against that, the annual-cadence model (8.14 mm; 5.85 mm excluding the
first point) gives honest skill ≈ 0.32 for F3 and ≈ 0.0 for F2 — not the
claimed 0.82/0.79. **The assimilation machinery adds little beyond fixing the
datum once.**

**F-2 — "Coverage UNDETERMINED" is contradicted by the authors' own blind-era
sample.** §5 of `SEQ_REHEARSAL_FINDINGS_20260611.md` evaluates coverage only
on the 2024 toy sample (6 and 2 points) and declares it undetermined for want
of 20 samples. But the blind-era runs contain 27 band-defined scoring points
per layer at semiannual cadence (≥ their own 20-sample minimum) and 60 at
monthly. On those samples: semiannual coverage = F1 0.667, T1 0.815, F2 0.852,
T2 0.852, F3 0.778, F4 0.889 → only 3/6 layers reach the 0.85 target (criterion
demands ≥5/6) → **coverage FAILS at semiannual**, with F1's 0.667 (n=27, 95%
binomial CI ≈ [0.48, 0.81]) statistically below 0.85. At monthly (n=60) 5/6
layers pass (F1 again fails at 0.783). The honest statement was available and
is worse than "undetermined."

**F-3 — The cadence-degradation headline conflates pre-blind drift with
blind-era drift.** "F3 drifts to 44.6 mm without visits" reads as 5-year
blind-era divergence; ~77% of it (44.3 mm of the ~54.8 mm endpoint error) was
present on day one. One single visit at deployment start removes it. The
deployment-relevant no-visit drift rates inside the blind era are ≈ 2 mm/yr
(F2) and ≈ 2 mm/yr secular plus ±16–24 mm drought excursions (F3).

**F-4 — F3 dynamics are phase-wrong, not absent.** Within-segment prediction
curvature is real (median linear-residual std 1.20 mm annual F3, 2.22 mm
F2 — not a flatline), and amplitude is roughly right (ratio 1.15 F3 annual).
But detrended r = 0.216 (annual) means the injected motion shares only 4.7% of
variance with the real layer. The breathing plot shows the model's drought
response arriving roughly half a year out of phase — consistent with τ capped
at 120 epochs (600 d) versus the diagnosed 163 epochs (815 d). The findings
doc sells the 2022-03-01 "drought detection" as a success; it is the same
phase error that produced the record's largest post-anchor residuals (+15.9 →
−24.2 mm). Three semiannual scoring points exceeded 20 mm pointwise.

**F-5 — L1 "ACCURACY PASSED 6/6" is mostly a property of the thresholds.**
With ZERO visits and the carrier alone, F1/T1/T2 already pass L1 (none-run
RMSE 3.2/1.9/2.4 mm < 10 mm), and semiannual F1 has R² = −0.087 — worse than
predicting the constant mean — yet "passes." Only F2/F3/F4 are non-trivial
tests, and they pass because reveals fix the datum (F-1).

**F-6 — Ground-truth provenance red flag.** Non-integer value fraction in the
"genuine" truth file: 15.5% pre-2019, 41.7% in 2019–2023, **100% in 2024**
(e.g., F3 = −447.2990212911973). Early-era visits are integer-mm readouts; the
2024 rows passed through numeric processing of unknown kind. The 264-visit file
mixes at least two sources. Ring-by-ring verification was not performed (out of
audit scope); §8.1's caveat is understated.

**F-7 — No temporal leakage detected in M8.** Pre-assimilation predictions at
reveal dates differ from the revealed values; post-reveal resets land 0.15–0.42
mm from the revealed observation (carrier noise = 0.147 mm); errors are large
and physically structured (drought phase wave), which a leaking model would
not produce. `leakage_fired = false` corroborated.

---

## 4. Interrogation answers

**Q1 — Did the 06-09 → 06-11 pivot solve the fundamental physics?** No — it
honestly stopped pretending to. The rank-deficiency, phase-cancellation, and
amplitude-bound limits are not solved; they are bypassed by buying datum
information with field visits. That is a legitimate engineering answer, and
the de-leaking (frozen calibration, genuine-visit grading, pre-assimilation
scoring) is real progress over the in-sample-fit era (L1/L2 findings). But the
between-visit dynamic skill the pivot promised is delivered only at F2
(r ≈ 0.6); at F3 the added head physics contributes phase-wrong motion
(r ≈ 0.22) that during the only drought on record was worse than drawing a
straight line. Complex band-aid: 60% band-aid, 40% solution.

**Q2 — Overfitting/temporal leakage in M8?** None found (F-7). The honest-
looking large errors during 2022 are the strongest evidence of honesty. The
residual leak surface is the truth file itself (F-6): if some 2019–2024
"genuine" rows are interpolations of the same dense fill the calibration saw,
grading is mildly optimistic; this cannot be excluded without the ring-by-ring
record.

**Q3 — Flatline behind bias-resets?** Not a flatline — the model genuinely
oscillates between reveals (within-segment residual std 1.2–2.2 mm at F2/F3,
amplitude ratios 0.8–1.4). For F2 the oscillation is substantially the real
seasonal signal (r = 0.59–0.61 at sparse cadences, 0.77 monthly). For F3 the
amplitude problem was not fixed; it was traded for a phase problem. RMSE
stays low because the resets erase the accumulated phase error once a year —
i.e., the *accuracy* numbers are carried by the resets, the *dynamics* are
carried only at F2.

**Q4 — Is annual visiting safe for F2 and F3?** F2: yes, with stated limits —
max between-reveal error 9.9 mm against a 20 mm RMSE / 10 mm MAE threshold,
band coverage 0.857 (n=14), partial real dynamics; margin ≈ 2× in a window
containing one drought. F3: **no.** The one drought of the record consumed
80% of the annual-cadence margin (15.9 of 20 mm), breached 20 mm pointwise at
semiannual placement (−24.2 mm), and the conformal band under-covered (0.643
at annual n=14; authors' own 2024 grading: 0/2). The 2003-class drought
(12.2 cm/yr basin peak versus 4–5 cm/yr current) would plausibly breach L1
between annual visits. F3 needs quarterly visits during drought years (or a
model with the τ cap lifted to ≥163 epochs), and any deployment claim past
2024-12-31 is void until the GPS record resumes.

**DP-SEQ re-grade by this auditor:** ACCURACY = PASS but weak-bar (F-5);
COVERAGE = **FAIL at semiannual** (3/6 layers ≥ 0.85 on n=27), PASS at monthly
(5/6 on n=60), undetermined at annual (n=14 < 20); SKILL claims = overstated
(F-1). Net: PARTIAL stands, but for harsher reasons than the authors state.

---

## 5. Artifacts

- `audit_red_team_v2/red_team_audit.py` — independent metric engine (fresh code)
- `audit_red_team_v2/probe_offset.py` — datum-offset / drift probe
- `audit_red_team_v2/independent_metrics.csv` — all 24 schedule×layer cells
- `audit_red_team_v2/audit_console_log.txt` — full run log
- `audit_red_team_v2/overlay_band_F2.png`, `overlay_band_F3.png` — prediction + 90% conformal band + reveals + genuine visits (annual & semiannual, shared y)
- `audit_red_team_v2/residual_drift_F2.png`, `residual_drift_F3.png` — signed residuals vs time with reveal markers and L1 lines
- `audit_red_team_v2/breathing_detrended_F2.png`, `breathing_detrended_F3.png` — zero-referenced, real-day-detrended obs vs pred dynamics, shared y
