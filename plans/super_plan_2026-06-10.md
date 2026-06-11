# Super Plan 2026-06-10 — Repair, Re-Validate, Extend (TUKU Pilot)

> **Status:** SUPERSEDED (2026-06-11) by `super_plan_2026-06-11.md` for all unfinished work.
> **2026-06-11 completion audit:** M2/M3/M4 verified COMPLETE from persisted files (checkboxes
> reconciled below). PARTIAL: 2.1.2, 2.2.4, 2.4.2 — migrated to the 06-11 plan (Tasks 6.1, 6.2).
> M5 NOT STARTED — reworked GPS-only as 06-11 Milestones M8/M9. The audit also found that the
> M2–M4 headline products are in-sample / selection-leaked — see `super_plan_2026-06-11.md` §0.
>
> This plan SUPERSEDED `super_plan_2026-06-09.md` for all unfinished work.
> The 06-09 plan's strategy (two tracks: carrier for gap-fill, bilinear for physics) is KEPT.
> Its executed results are NOT kept as trusted, because the 2026-06-10 zero-trust audit found
> that the evaluation machinery itself was defective (see "Why this plan exists" below).
>
> **Audience:** a junior AI agent. Every step is written so that nothing must be guessed.
> Where a number is expected, the expected number is stated. Where a formula is needed,
> the formula is written out. Follow the steps in order. Do not skip decision gates.
>
> **Scope limitation honored:** this plan describes hydrogeology, mathematics, and logical
> data flow only. Program names are used as logical identifiers (e.g., "the bake-off
> evaluator", "Script 13") — file paths, directories, and Python environment setup are
> deliberately out of scope. One precondition is noted anyway because nothing can run
> without it: **the mandated numerical environment is `fafalab2` (Python 3.12), confirmed
> functional on 2026-06-10. See CLAUDE.md "Environment & Quick Run" for command template.**

---

## 0. Why This Plan Exists (2026-06-10 Zero-Trust Audit Findings)

The physical situation: the TUKU multi-layer compaction well measures how six sediment
layers (F1, T1, F2, T2, F3, F4, spanning 0–300 m depth) squeeze as confined-aquifer head
falls. The project reconstructs that layer-by-layer record from signals that keep being
measured after the well stops: surface displacement (GPS, InSAR) and groundwater level
(GWL). Part 1 declared this working. The audit found that three of the four programs that
produced Part 1's evidence contain the **same alignment defect**, so the evidence must be
regenerated before it is believed.

**Confirmed defects (each traced to code on disk on 2026-06-10):**

| # | Defect | Physical consequence | Affected results |
|---|--------|---------------------|------------------|
| D1 | **τ-lag nullification.** The bake-off evaluator (Script 13), the storage characterization fitter (Script 15), and the GWL-term evaluator (14b, which imports Script 13's loader) slice the head array as `H[τ:]` and the compaction array as `b[τ:]`. Both arrays shift together, so the relative lag between driver and response is **zero**, not τ. Only the carrier reconstruction program (Script 14) lags correctly (`u(t) = H(t−τ)`). | Compaction responds to head with a delay (Terzaghi consolidation: pore-pressure diffusion through aquitards takes weeks to years; fitted τ values are 6–120 five-day epochs = 30–600 days). Fitting with zero lag misattributes head-driven variance and biases $S_{ke}$, $S_{kv}$. | ALL storage parameters in the characterization result file (including the headline "F2 $S_{skv} = 1.41 \times 10^{-3}$ m⁻¹ matches Hung et al."); the bilinear arm of Decision Point 1; the GWL-term rejection verdicts for F2, T2, F3 (T1 has τ=0 and is unaffected). |
| D2 | **Crash before output.** The carrier reconstruction program references an undefined variable in its summary-writing step, so any fresh run halts with a `NameError` before the summary file is written. Corroborated: the persisted summary file contains `tail_evaluation: null`. | The Decision Point 2 skill numbers quoted in the findings document (T1 +0.41, T2 +0.43) trace to **no file on disk**. They are unverified. | Decision Point 2 (PARTIAL verdict); the self-recalibration outputs. |
| D3 | **Zero-filled cumulative sum.** Cumulative compaction is built as `cumsum(fillna(increments, 0))`. A missing increment becomes "zero compaction," silently flattening the cumulative record through any real gap, and making every epoch look observed (the gap flag can never be true). | At TUKU only 1 of 1,572 increments is missing, so the damage is negligible **here**. At the 37 Part-2 stations with real multi-year gaps this fabricates flat observations inside gaps and corrupts both calibration and evaluation. | Part-2 readiness; the `is_gap` accounting in all reconstruction CSVs. |
| D4 | **Future head set to zero.** In forward-prediction mode, layers with an adopted GWL term receive $u = 0$ for all future epochs. Groundwater level monitoring **continues** after MLCW wells stop — that is the premise of the whole project — so discarding the future head and inserting zero creates an artificial jump of $d_k \cdot u_{\text{last}}$ at the forecast boundary. | Forward predictions for GWL-adopting layers (currently T1) are discontinuous at the last MLCW epoch. | Phase 1.2 forward predictions. |
| D5 | **Identifiability flag wrong.** The characterization output marks F3's elastic coefficient as identifiable (`S_ke_identifiable: true`) even though its bulk ratio is 1286 (physically absurd; sediment cannot be 1286× more compressible inelastically) and the findings document itself says F3's $S_{ke}$ is unidentifiable. The flag tests only `n_elastic ≥ 15`, not collinearity. | A meaningless elastic coefficient ($S_{ske} = 1.7 \times 10^{-7}$ m⁻¹) can be quoted as a measurement. | Physical parameter table; manuscript risk. |
| D6 | **Ledger–disk divergence (recurring failure mode, 3rd occurrence).** The findings document quotes Decision Point 2 numbers that exist in no persisted file (D2) and an F3 identifiability verdict that contradicts the live JSON (D5). | Same disease as the June "9.1×/9.3× phantom gate numbers." | Trust in all documents. |

**Verified data facts (computed directly from the data on 2026-06-10, not inherited):**

- GPS at TUKU ("modeled" series, daily, 2010-01-02 to 2024-12-31, n = 5,478): linear fit
  $R^2 = 0.9960$, trend $-43.0$ mm/yr, residual standard deviation 11.7 mm (range −22.7 to
  +31.4 mm — mostly multi-year curvature, since a quadratic raises $R^2$ only to 0.9976),
  annual seasonal amplitude **3.7 mm**.
- Observed MLCW seasonal amplitude (detrended cumulative, annual harmonic): F1 0.71 mm,
  T1 0.68 mm, **F2 4.52 mm**, T2 0.69 mm, F3 1.92 mm, F4 0.35 mm. Detrended residual
  standard deviation: F1 1.43, T1 1.06, F2 4.48, T2 2.81, **F3 20.73**, F4 1.47 mm.
- Arithmetic consequence: F2's 4.5 mm seasonal cycle cannot be recovered from a 3.7 mm
  total surface seasonal signal multiplied by F2's 0.21 share (yields 0.8 mm). The GPS
  "modeled" series is a smoothed model output; the raw GNSS daily solutions and the
  per-station InSAR seasonal-harmonic series exist on disk and are unused by the carrier.
- GPS ends 2024-12-31; MLCW continues to 2025-10-01. The last ~9 months of the record
  cannot be reconstructed from this GPS series at all. InSAR may cover them.
- MLCW master timeline: 1,572 five-day epochs, 2003-12-06 to 2025-10-01; GPS overlaps
  1,081 of them (68.8%).

**What survives the audit unchanged:** the carrier model's *carrier-vs-baseline* comparison
(the carrier arm uses no lag, and the interpolation/trend baselines use no lag), the R1/R2/R3
datum repairs, the holdout protocol design (middle gap + end gap), the guardrail system,
and the physical reasoning that surface displacement is the depth-integral of layer
compaction. CARRIER-PRIMARY is *expected* to survive re-evaluation; it is not *assumed* to.

---

## LEVEL 1 — THE APEX GOAL

**Reconstruct layer-wise cumulative compaction $b_k(t)$ at TUKU for all six instrumented
layers, with held-out Mean Absolute Error and Root Mean Square Error below the following
thresholds, evaluated on epochs the model never saw:**

| Layer class | Layers | Observed range (mm) | MAE target | RMSE target |
|-------------|--------|--------------------:|-----------:|------------:|
| Thin layers | F1, T1, T2, F4 | 14.6 – 25.1 | < 5 mm | < 10 mm |
| Thick aquifers | F2, F3 | 144.8 – 216.2 | < 10 mm | < 20 mm |

**Binding rules for the goal:**

1. **Held-out only.** MAE and RMSE count toward the goal only when computed on held-out
   epochs (middle gap, end gap, or 6-month tail). Calibration-epoch metrics are diagnostic
   wallpaper and never satisfy the goal. (This rule exists because the project has twice
   promoted methods on in-sample fit.)
2. **All three holdout designs must pass.** Middle gap (40–70% of record masked: simulates
   reduced sampling), end gap (last 30% masked: simulates permanent shutdown), and 6-month
   tail (prediction mode). The goal is met per layer only when that layer passes its
   thresholds in all three designs.
3. **Every number traceable.** A metric counts only if it is read from a persisted result
   file written by a re-runnable program. Numbers that exist only in documents do not exist.
4. **Physics gates still bind.** Reported storage parameters must satisfy $S_{ke} \ge 0$,
   $S_{kv} \ge S_{ke}$, $V(t)$ monotonically non-increasing, and the identifiability rules
   of Task 1.5. A reconstruction that hits the error targets with unphysical parameters is
   reported as "empirically adequate, physically uninterpreted" — never as physics.

**Current distance to the goal (pre-repair numbers, to be regenerated):** middle-gap RMSE
already ranges 1.1–7.3 mm (all layers inside targets); end-gap RMSE ranges 2.2–17.0 mm
(F3 at 16.97 mm is inside the 20 mm bound but fragile); the 6-month tail fails on 4 of 6
layers against a trend baseline. The goal is therefore *near*, and the plan's effort goes
to (a) making the numbers trustworthy and (b) the two genuine weaknesses: sub-annual
dynamics and end-of-record acceleration (F3 end error −19.2 mm).

---

## LEVEL 2 — MILESTONES

| Milestone | Name | Physical purpose | Gate |
|-----------|------|------------------|------|
| **M1** | Repair the evaluation machinery | No ruler may be bent: fix the lag, the crash, the gap handling, the future-head handling, the identifiability logic | All five repairs verified by unit checks |
| **M2** | Re-run and re-decide | Regenerate every Part-1 number with straight rulers; re-issue Decision Points 0, 1, 2 from persisted files | DP1 and DP2 re-issued |
| **M3** | Hybrid model — recover sub-annual dynamics and acceleration | The carrier reproduces the trend; physics (lagged elastic head, inelastic exceedance, annual harmonic, InSAR seasonal) must supply what the trend cannot | Per-layer adoption map decided by held-out skill |
| **M4** | Uncertainty and the apex verdict | A reconstruction without an error bar is not a measurement | Apex-goal verdict table persisted |
| **M5** | Deployment rehearsal — gate to Part 2 | Part 2 stations have no co-located GPS and have real MLCW gaps; rehearse the InSAR carrier and gap robustness at TUKU where ground truth exists | Part-2 go/no-go decision |

**Hard stop after M5.** Part 2 (37 stations) and Part 3 (8,577 grid points) are out of
scope for this plan and remain blocked until the human validates M1–M5.

---

## LEVEL 3 / LEVEL 4 — TASKS AND MICRO-STEPS

### MILESTONE M1 — Repair the Evaluation Machinery

**Physical narrative:** compaction lags head because pore pressure must diffuse through
low-permeability clay before effective stress changes inside an aquitard (Terzaghi, 1925;
the fitted lags at TUKU are 30–600 days). Three of four evaluation programs currently
erase that lag. Until they are fixed and proven fixed, every downstream number — storage
coefficients, decision points, gate verdicts — is a measurement made with a bent ruler.

#### TASK 1.1 — Fix the τ-lag alignment defect (D1) — THE BLOCKING REPAIR

**The invariant (memorize this; it is the single most-violated rule in this project's
history):** for a response observed at epoch index $i$, the driver is the head observed at
epoch index $i - \tau$:

$$b(t_i) \;\text{ pairs with }\; u(t_{i-\tau}) = H(t_{i-\tau}) - H_{\text{ref}}, \qquad i = \tau, \dots, N-1$$

In array form, with arrays of equal original length $N$:

- **response slice:** `b[τ : N]` (length $N-\tau$)
- **driver slice:** `H[0 : N−τ]` (length $N-\tau$)

The wrong pattern — found in Script 13 and Script 15 — slices **both** arrays as `[τ:]`,
which shifts them together and produces an effective lag of zero.

The virgin (inelastic) term must use the same lagged head sequence:

$$V(t_i) = \min\!\big(0,\; \min_{s \le i-\tau} H(t_s) \;-\; h_c\big)$$

(the running minimum runs over the *driver's* time axis, so the sediment "remembers" the
deepest head it has felt, delayed by the same diffusion lag).

- [x] **1.1.1** Write a synthetic alignment test before touching any fitting code.
  Construct $N = 500$ epochs; head $H(t) = \sin(2\pi t / 73)$ (a clean annual cycle in
  5-day units); response $b(t) = 2.0 \cdot H(t - 10)$ for $t \ge 10$. Fit a single-regressor
  least squares of the response slice against the driver slice using the invariant above
  with $\tau = 10$.
  - Success check: recovered coefficient = 2.000 ± 0.001 and $R^2 > 0.999$.
  - Counter-check: repeat with the WRONG slicing (`H[10:]` vs `b[10:]`); the recovered
    coefficient must differ from 2.0 and $R^2$ must drop substantially (for a sinusoid
    lagged by 10 of 73 samples, the attenuation factor is $\cos(2\pi \cdot 10/73) \approx 0.65$).
    If the wrong slicing also recovers 2.0, the test itself is broken — stop and re-derive.
- [x] **1.1.2** Apply the invariant to the bake-off evaluator (Script 13): in its
  array-building step, replace the joint `[τ:]` slicing with response `b[τ:]`, driver
  `H[0:N−τ]`, GPS carrier `d[τ:]` (the carrier is contemporaneous with the response — GPS
  measures today's surface, which contains today's compaction), and dates `dates[τ:]`
  (the timeline belongs to the response).
- [x] **1.1.3** Apply the same correction to the storage characterization fitter (Script 15)
  and confirm the GWL-term evaluator (14b) picks the correction up automatically (it
  imports Script 13's loader — verify by reading its import, not by assumption).
- [x] **1.1.4** Confirm the carrier reconstruction program (Script 14) already satisfies the
  invariant (it builds `u_lagged[τ:] = u_raw[0:N−τ]`, which is correct) — read the code and
  record the line numbers in the M1 completion note. Do not "fix" correct code.
  VERIFIED CORRECT, NOT MODIFIED: `14_carrier_reconstruction_tuku.py` lines 142–147:
  `u_lagged_arr[tau:] = u_raw[:T_full - tau]` — response index i pairs with u_raw[i-τ]. Correct.
- [x] **1.1.5** Run the synthetic test of 1.1.1 through each corrected program's fitting
  entry point (not just standalone) to prove the correction is live in situ.
  Proof in `tau_demo_TUKU/results/lag_alignment_test.json`: Proof A (synthetic through the
  corrected loader slicing) recovers coef=2.0000 at τ=10/72/120 where zero-lag would give
  1.3038/1.9926/−1.2373; Proof B (live Script-13 loader) confirms u==driver−ref for all 6
  layers (max|Δ|=0). GATE=PASS.

#### TASK 1.2 — Fix the summary-writing crash and persist Decision Point 2 (D2)

**Physical meaning:** the project's verify-before-stating rule requires every decision to
trace to a file. The 6-month-tail skill numbers — the entire basis of Decision Point 2 —
currently trace to nothing.

- [x] **1.2.1** In the carrier reconstruction program's summary-writing step, the output
  filename is built from a variable that does not exist in that scope (the suffix variable
  was renamed during the recalibration refactor). Align the name. A fresh run must complete
  end-to-end without a `NameError`.
  FIX: `14_carrier_reconstruction_tuku.py` L811 `suffix` → `output_suffix`. Fresh
  `--eval-tail` run completed end-to-end, no NameError.
- [x] **1.2.2** Ensure the tail-holdout evaluation result (per layer: model RMSE, trend
  RMSE, skill, number of training and tail epochs) is written INTO the persisted summary —
  `tail_evaluation` must never be null when the tail evaluation ran.
  CONFIRMED: summary already writes `tail_evaluation: tail_eval` (L795); now non-null.
- [x] **1.2.3** Re-run with tail evaluation enabled and confirm by reading the file back:
  the persisted skills exist and the printed table equals the persisted values.
  PERSISTED (regenerated 2026-06-10, run `--use-gwl F2,T1 --eval-tail`):
  `tau_demo_TUKU/results/reconstruction/TUKU_carrier_reconstruction_summary.json`.
  `tail_evaluation` non-null, all 6 layers × 5 fields. Printed vs persisted match exactly:
  T1 +0.4075, T2 +0.4283, F2 +0.4305 (skill>0); F1 −0.1659, F3 −0.2488, F4 −0.1425 (skill≤0).
  DP2 implied count = skill>0 on 3/6 (T1, T2, F2). (Formal DP2 re-issue is M2 Task 2.4.)
  Note: the previous note here read "T1 +0.250 ... F2 −1.7035" — that traced to no persisted
  file (a stale non-tail run had left tail_evaluation:null); corrected to the now-persisted values.

#### TASK 1.3 — Gap-aware cumulative compaction (D3)

**Physical meaning:** a missing increment is missing knowledge, not zero movement. Layers
keep compacting during instrument gaps; writing 0 mm into the record fabricates a flat
spot that the model is then trained and graded on.

- [x] **1.3.1** Define the accumulation rule: cumulative compaction is the running sum of
  *observed* increments; any epoch whose increment is missing gets $b = \text{NaN}$, and —
  because a cumulative series loses its datum across a gap — all epochs AFTER a gap remain
  on the same datum only if the increments are genuinely 5-day differences of a continuous
  instrument (true for MLCW). Adopt: NaN increments propagate NaN for that epoch only;
  the running sum continues from the next observed increment; record per layer the count
  of NaN epochs and the longest gap.
  - Caveat to record: across a *multi-epoch* gap the post-gap cumulative carries unknown
    accumulated compaction. For TUKU (one missing increment) this is negligible; for Part 2
    the per-station gap census of Task 5.2 decides where the carrier datum must be re-anchored.
- [x] **1.3.2** Re-verify at TUKU: exactly 1 of 1,572 increments is missing per layer (this
  was measured on 2026-06-10); after the change, each layer's $b$ must contain exactly the
  corresponding NaN epochs, and the gap flag in the reconstruction output must be true
  exactly there.
  VERIFIED in `tau_demo_TUKU/results/gap_aware_test.json` (census: 1/1572 missing at idx 0,
  cum NaN at idx 0, all 6 layers) and in the reconstruction CSVs (`is_increment_missing` /
  `is_model_only` True at exactly idx 0, n=1 per layer; `b_observed_mm` NaN there). Note:
  `is_gap_filled` is False at idx 0 because there is no GPS in 2003 to fill with (GPS starts
  2010) — honest, not a defect; the missing-observation flag is `is_increment_missing`.
- [x] **1.3.3** Add a guard that refuses to run on any station where more than 20% of
  increments are missing, printing the gap census instead (protects Part 2 from silent
  fabrication).
  BUILT in `tau_demo_TUKU/gap_aware_cumsum.py` (`census(..., enforce_guard=True)` raises
  `GapFractionExceeded` > 20%). Unit-proven: 30% missing raises, 10% passes
  (`gap_aware_test.json`). Wired into Scripts 13, 14, 15.

#### TASK 1.4 — Future head uses real head (D4)

**Physical meaning:** groundwater wells keep reporting after the compaction well stops —
that is the entire premise. The forecast must drive the GWL term with the actual head.

- [x] **1.4.1** In forward-prediction mode, for layers with an adopted GWL term, look up
  the real zero-referenced lagged head $u(t-\tau)$ for forecast epochs. The lag works in
  the forecast's favor: with $\tau$ epochs of lag, the first $\tau$ forecast epochs need
  only *already-observed* head.
  FIX in `14_carrier_reconstruction_tuku.py` `extend_prediction` (~L488–520): future epoch
  N+j now uses u_raw[N+j−τ] from H_abs−H_ref. Verified: F2 (τ=72) forecast of 49 epochs uses
  49 REAL lagged heads, 0 frozen.
- [x] **1.4.2** Where head is genuinely unavailable beyond the well record, hold the last
  observed $u$ constant (a "head freezes" scenario) and flag those epochs — never insert 0.
  BUILT: `u_future_frozen` flag set where src index runs past the record; held at u_last.
  Verified: T1 (τ=0) freezes all 49 (held at u_last=−3.223 m). OLD code inserted d_k·0 — removed.
- [x] **1.4.3** Verify continuity: the predicted $b_k$ series must have no jump exceeding
  the typical 5-day increment (≈ 0.5 mm) at the calibration/forecast boundary.
  PERSISTED: `tau_demo_TUKU/results/forecast_continuity_test.json`. Max single-epoch increment
  within the contiguous 49-epoch forecast region: F1 0.015, T1 0.011, F2 0.511, T2 0.016,
  F3 0.180, F4 0.019 mm — all continuous. F2's 0.511 mm is smooth seasonal head breathing
  (profile −0.25..+0.26), not a step. (The 2025 GPS-absence gap is a known data-coverage
  gap, not a D4 discontinuity.)

#### TASK 1.5 — Honest identifiability logic (D5)

**Physical meaning:** when head sits below the preconsolidation threshold almost the whole
record, the elastic column $u$ and inelastic column $V$ move together and the regression
cannot separate stiffness from plasticity. Declaring such an $S_{ke}$ "identifiable"
manufactures a material property out of collinearity.

- [x] **1.5.1** Define: $S_{ke}$ is identifiable for a layer only if ALL hold:
  (a) $n_{\text{elastic}} \ge 15$ (epochs with $V$ unchanged);
  (b) the variance inflation factor between the $u$ and $V$ regressors (after each is
  centered) is below 10;
  (c) the fitted $S_{ke} > 0$;
  (d) the bulk ratio $S_{kv}/S_{ke} \le 100$ (a ratio above 100 means the elastic
  coefficient is numerically indistinct from zero — Riley 1969 and Hung et al. 2021 place
  the physical contrast at 8–50×).
- [x] **1.5.2** When unidentifiable, re-fit the inelastic-only model $b = c + S_{kv} V$ and
  report $S_{ke}$ as "not determined," with no ratio. Expected outcome at TUKU: F3 and F4
  go inelastic-only; F4's $S_{ke} = 0$ is *physically correct* (100% silt/mud per the
  borehole log) and should be labeled so, not flagged as a defect.
  BUILT in `15_storage_characterization.py`: 4-condition rule + inelastic-only re-fit
  (NNLS, S_kv>=0), `S_ke_status="not determined"`, ratios suppressed. Outcome matches:
  F3 + F4 went inelastic-only (S_ke=0). NOTE for M2: the inelastic-only re-fit gives
  negative cumulative R² (F3 −2.79, F4 −1.41) — a real finding to surface in M2, not a bug.
- [x] **1.5.3** Re-emit the characterization file and confirm no layer carries a ratio
  above 100 with an "identifiable" label.
  PERSISTED: `tau_demo_TUKU/results/characterization/TUKU_storage_params.json`. AUDIT 1.5.3 =
  PASS (NONE). Verified per layer: F1/T1/F2/T2 identifiable (bulk ratios 1.64/2.03/14.67/16.06,
  VIF 3.09/3.10/1.17/1.08); F3/F4 not determined. Old F3 ratio-1286 "identifiable" verdict
  is gone.

> **GATE M1:** all five repairs have passing checks (1.1.1/1.1.5 synthetic lag test;
> 1.2.3 persisted tail; 1.3.2 gap census; 1.4.3 continuity; 1.5.3 flag audit).
> Do not proceed to M2 with any box unchecked.
>
> **GATE M1 STATUS (2026-06-10): PASSED.** All five repair boxes checked, each traceable to
> a persisted file produced by a re-runnable program:
> - D1 τ-lag → `tau_demo_TUKU/results/lag_alignment_test.json` (synthetic + in-situ, GATE=PASS).
>   Code: Script 13 `build_aligned_arrays` §6 (driver `H[0:N-τ]`, response/carrier/dates `[τ:]`);
>   Script 15 fit loop (driver `H_abs_full[:N-τ]`). Script 14 confirmed already-correct (L142-147), unmodified.
>   Equivalence check (M2-relevant, noted clean): carrier arm reproduces pre-repair RMSE to <0.001 mm,
>   well inside <0.1 mm bound; DP1 stays CARRIER-PRIMARY (6/6). No escalation triggered.
> - D2 crash → `tau_demo_TUKU/results/reconstruction/TUKU_carrier_reconstruction_summary.json`
>   (`tail_evaluation` non-null, 6 layers × 5 fields, regenerated 2026-06-10 with `--eval-tail`;
>   Script 14 L819 `suffix`→`output_suffix`). No further code change needed — null was a stale
>   non-tail run, not a code defect; `tail_eval` is correctly written at L850.
> - D3 gap → `tau_demo_TUKU/results/gap_aware_test.json` + `gap_aware_cumsum.py`
>   (NaN-not-zero, census 1/1572 at idx 0, >20% guard). Wired into Scripts 13/14/15.
> - D4 future head → `tau_demo_TUKU/results/forecast_continuity_test.json` (real lagged head /
>   frozen-and-flagged, never zero; forecast continuous). Script 14 `extend_prediction`.
> - D5 identifiability → `tau_demo_TUKU/results/characterization/TUKU_storage_params.json`
>   (4-condition rule; F3/F4 inelastic-only; AUDIT 1.5.3 = NONE). Script 15.
>
> New/changed files: `tau_demo_TUKU/test_lag_alignment.py`, `tau_demo_TUKU/test_gap_aware.py`,
> `tau_demo_TUKU/gap_aware_cumsum.py` (new); Scripts 13, 14, 15 (repaired). Script 14b and
> Script 14 carrier-lag logic unchanged (already correct).

---

### MILESTONE M2 — Re-Run and Re-Decide

**Physical narrative:** with straight rulers, re-measure everything Part 1 claimed. The
carrier's win over baselines is expected to survive (its arm was lag-free); the bilinear
parameters and the GWL-term verdicts are expected to CHANGE, because for F2 (τ = 72 epochs
= 360 days) and F3 (τ = 120 epochs = 600 days) the head signal was previously paired with
the wrong year of compaction.

#### TASK 2.1 — Re-run the three-method bake-off → re-issue Decision Point 1

- [x] **2.1.1** *(audit 2026-06-11: COMPLETE — `holdout_bakeoff.json`, 36 RMSE + skills)* Run the corrected bake-off (middle gap and end gap, all six layers, three
  methods). Persist all 36 RMSE values plus per-method skill against the baseline.
- [ ] **2.1.2** Compare against the pre-repair table (F1 1.64/2.54, T1 1.06/2.24,
  F2 4.30/7.13, T2 2.03/3.91, F3 7.30/16.97, F4 1.64/3.80 mm carrier middle/end). The
  carrier arm should reproduce within numerical noise (< 0.1 mm) — if it does not, the
  loader changed more than the lag; stop and diagnose.
  The bilinear arm WILL change; record old vs new side by side.
- [x] **2.1.3** *(audit 2026-06-11: COMPLETE — `metadata.verdict = CARRIER-PRIMARY`, `win_counts.carrier = 6`)* Re-issue Decision Point 1 from the persisted file: CARRIER-PRIMARY if the
  carrier wins or ties ≥ 4 of 6 layers on average across both designs; MIXED otherwise
  (adopt per-layer winners). Update the ledger with the new table and an OBSOLETE mark on
  the old one.

#### TASK 2.2 — Re-run storage characterization → corrected physics table

- [x] **2.2.1** *(audit 2026-06-11: COMPLETE — `TUKU_storage_params.json`)* Run the corrected characterization with proper lags. Convert to specific
  storage with the two-thickness rule: $S_{ske} = S_{ke} / (\text{total span} \times 1000)$,
  $S_{skv} = S_{kv} / (\text{clay thickness} \times 1000)$ (units: $S_{ke}$, $S_{kv}$ in
  mm per m of head change; spans in m; result in m⁻¹).
- [x] **2.2.2** *(audit 2026-06-11: COMPLETE — ratio_bulk + thickness_artifact flags persisted)* Gate on the **bulk ratio** $S_{kv}/S_{ke}$ (same-thickness, comparable to
  the 8–100× literature contrast; relaxed bound [3, 50] warns, outside [1, 100] fails).
  Report the specific-storage ratio only with the mixed-thickness caveat and a
  thickness-artifact flag where span/clay > 4. Never fail a layer on the mixed ratio alone.
- [x] **2.2.3** *(audit 2026-06-11: COMPLETE — F2 S_skv 1.3422e-3 vs prior 1.33e-3, claim survives)* Compare to Hung et al. (2021) priors (middle fan: $S_{ske} = 1.15 \times
  10^{-4}$, $S_{skv} = 1.33 \times 10^{-3}$ m⁻¹). Record whether the pre-repair "F2
  matches literature" claim survives the lag correction. If it does not, say so plainly in
  the ledger — the claim was made with τ effectively 0 and was never entitled to confidence.
- [ ] **2.2.4** Re-examine the two physically anomalous shallow layers: F1 (bulk ratio
  1.76) and T1 (2.02) sit BELOW the physical floor of 3 — inelastic storage should exceed
  elastic by at least several-fold in CRAF sediments. Hypotheses to test, in order:
  (a) post-2015 head at these wells never substantially crossed below $h_c$, so $V(t)$
  barely activates and $S_{kv}$ is fit on weak signal (check: count epochs with $V < 0$ and
  the total $V$ excursion in m); (b) the τ for these layers is wrong; (c) the layers truly
  behave elastically post-2015 (then report "elastic-dominated regime, $S_{kv}$ not
  excited," not a failed gate).

#### TASK 2.3 — Re-run the GWL-term evaluation → corrected adoption map

- [x] **2.3.1** *(audit 2026-06-11: COMPLETE — `carrier_gwl_eval.json`, dated 2026-06-10)* With correct lags, re-evaluate the 3-parameter model
  $b_k = a_k d_{\text{GPS}} + d_k u_k(t-\tau_k) + c_k$ ($a_k, d_k \ge 0$) against the pure
  carrier on both holdout designs. Adoption rule unchanged: adopt the GWL term only where
  average held-out RMSE improves by more than 5%.
- [x] **2.3.2** *(audit 2026-06-11: COMPLETE — `adopt_gwl` = F1/T1/F2/T2 true, F3/F4 false)* Expected: T1 (τ=0) keeps its −14.3% adoption; F2/T2/F3 verdicts are OPEN
  (previously tested at wrong lag). Record the new per-layer adoption map in the ledger.

#### TASK 2.4 — Re-run the tail holdout → re-issue Decision Point 2

- [x] **2.4.1** *(audit 2026-06-11: COMPLETE — `tail_evaluation` 6 layers × 5 fields, gwl_layers = M2.3 map)* Run the 6-month (36-epoch) tail holdout with the corrected programs and the
  M2.3 adoption map. Persist per-layer model RMSE, trend-baseline RMSE, and skill.
- [ ] **2.4.2** Re-issue Decision Point 2 from the persisted file: PASS if skill > 0 on
  ≥ 3 layers; PARTIAL 1–2; FAIL 0. Replace the unpersisted "T1 +0.41 / T2 +0.43" claims.

#### TASK 2.5 — Ledger reconciliation

- [x] **2.5.1** *(audit 2026-06-11: COMPLETE — PART1_FINDINGS OBSOLETE marks L77/88/150/180, D5/D6 resolved L202–204)* Update the findings document and the progress ledger so that every number
  quotes its source file and field. Delete or OBSOLETE-mark every number that traces to
  nothing. The F3 identifiability contradiction (D5/D6) must be resolved in writing.

> **GATE M2:** Decision Points 1 and 2 re-issued from persisted files. If DP1 flips away
> from CARRIER-PRIMARY (not expected), stop and escalate to the human before M3 — the
> hybrid design below assumes the carrier is the backbone.

---

### MILESTONE M3 — Hybrid Model: Sub-Annual Dynamics and Acceleration

**Physical narrative:** the carrier is a scaled copy of a nearly linear surface signal.
What it misses is exactly what groundwater physics provides: (1) the *seasonal elastic
breathing* of aquifers as monsoon recharge raises head and dry-season pumping lowers it
(reversible, proportional to $u$, lagged by τ); (2) the *irreversible acceleration* when
drought pushes head below the historical preconsolidation minimum and clay drains
permanently (the $V(t)$ exceedance term — Riley 1969); (3) the *seasonal surface signal*
that the smoothed GPS series suppresses but InSAR retains. M3 adds these terms one at a
time, per layer, and keeps each only where held-out data rewards it.

**The signal budget (measured 2026-06-10, the targets M3 is shooting at):**

| Layer | Detrended residual std (mm) | Seasonal amplitude (mm) | Dominant missing component |
|-------|---------------------------:|------------------------:|----------------------------|
| F1 | 1.43 | 0.71 | little to gain — already near noise |
| T1 | 1.06 | 0.68 | already adopted GWL term |
| F2 | 4.48 | 4.52 | **seasonal** (head-driven elastic) |
| T2 | 2.81 | 0.69 | mixed, weak |
| F3 | 20.73 | 1.92 | **interannual acceleration** (inelastic $V$) |
| F4 | 1.47 | 0.35 | little to gain |

Effort allocation follows the budget: F2 and F3 carry 90% of the recoverable error; do not
gold-plate the four thin layers that already sit at 1–3 mm.

#### TASK 3.1 — Candidate model set (fixed menu, no improvisation)

The junior agent fits exactly these four candidates per layer — nothing else:

- **H0 (incumbent):** $b_k = a_k d(t) + c_k$
- **H1 (elastic head):** $b_k = a_k d(t) + d_k u_k(t-\tau_k) + c_k$, $a_k, d_k \ge 0$
- **H2 (annual harmonic):** $b_k = a_k d(t) + e_k \sin(2\pi t/T_a) + f_k \cos(2\pi t/T_a) + c_k$,
  with $T_a$ = 73 five-day epochs (365 days); $e_k, f_k$ unconstrained (phase is free)
- **H3 (inelastic exceedance):** $b_k = a_k d(t) + g_k V_k(t-\tau_k) + c_k$, $g_k \ge 0$
  (sign: $V \le 0$ by construction and compaction is negative, so a positive $g_k$ maps
  head exceedance below $h_c$ into additional downward movement — verify the sign on real
  data before constraining, and document the verification)

and one carrier-source variant:

- **H4 (InSAR-augmented carrier):** replace or augment $d(t)$ with the InSAR vertical
  series and/or the persisted InSAR seasonal-harmonic series for TUKU (these exist on
  disk from the 2026-06-01 seasonal campaign, 37/37 stations). InSAR is vertical
  displacement (ascending–descending decomposed, NOT line-of-sight) and its native unit
  is metres — multiply by 1000 for mm.

- [x] **3.1.1** *(audit 2026-06-11: COMPLETE — registry `vif_guard`, max 1.336, none rejected)* Before any fitting, compute the collinearity guard for every candidate:
  variance inflation factor between each pair of regressors after removing each one's
  linear trend. If VIF > 5 for a pair, the candidate is fit but flagged; if VIF > 10, the
  candidate is rejected for that layer without fitting (the data cannot separate the
  terms; adding them would shuffle variance arbitrarily). Note: at TUKU the detrended
  head-to-GPS correlation is known to be high for the HONGLUN well (F1/T1, corr ≈ 0.84) —
  expect H1 to be flagged there.
- [x] **3.1.2** *(audit 2026-06-11: COMPLETE — 6 layers × 5 candidates `coef_full` persisted)* Fit all admissible candidates per layer on calibration epochs with the
  bounded least squares described above.

#### TASK 3.2 — Selection strictly by held-out skill

- [x] **3.2.1** *(audit 2026-06-11: COMPLETE — per-design refits, `coef_by_design` distinct. CAVEAT: selection later leaked, see 06-11 plan §0 L2)* Evaluate every fitted candidate on all three holdout designs (middle, end,
  tail), refitting on the corresponding training epochs only — the candidate must never
  see the held-out compaction. The carrier/GWL/InSAR/harmonic regressors remain available
  during gaps (that is their virtue).
- [x] **3.2.2** *(audit 2026-06-11: COMPLETE — `adoption_map.decisions` with 5%/10% rule fields)* Adoption rule per layer: adopt the candidate with the lowest mean held-out
  RMSE across designs IF it beats H0 by more than 5% AND it never degrades any single
  design by more than 10%. Ties go to the simpler model (fewer parameters).
- [x] **3.2.3** *(audit 2026-06-11: COMPLETE — F2 PASS 3.5939/0.9834; F3 FAIL 15.66 / −30.0, recorded honestly)* Specific targets the hybrid must hit (else record FAIL honestly):
  - F2: middle-gap RMSE ≤ 4.0 mm (from 4.30) and detrended correlation between observed
    and predicted residuals ≥ 0.4 (from +0.16) — the seasonal cycle must visibly appear
    in the prediction.
  - F3: end-gap RMSE ≤ 12 mm (from 16.97) and end-of-record error magnitude ≤ 10 mm
    (from −19.2 mm) — the acceleration must be at least half-captured.
  - Tail (DP2 re-test with adopted hybrids): skill > 0 on ≥ 3 of 6 layers.
- [x] **3.2.4** *(audit 2026-06-11: COMPLETE — `hybrid_model_registry.json`; FROZEN-EVIDENCE per 06-11 plan M6.4)* Persist the per-layer adoption map (model id, coefficients, τ, held-out
  RMSE per design) as the single authoritative model registry for TUKU.

> **GATE M3 (Decision Point H):**
> - **PASS:** 3.2.3 targets met for at least F2 OR F3, and DP2 re-test reaches ≥ 3 layers.
> - **PARTIAL:** improvements exist but targets missed — adopt what won, document the
>   honest ceiling ("sub-annual dynamics at TUKU are bounded by carrier-input information
>   content"), and proceed to M4 with H-map as is.
> - **FAIL:** no candidate beats H0 anywhere — the deliverable for sub-annual dynamics is
>   "trend with uncertainty," stated plainly. Proceed to M4; never manufacture skill.

---

### MILESTONE M4 — Uncertainty and the Apex Verdict

**Physical narrative:** the reconstruction will be used to say "layer F3 compacted X mm
during the gap." Without an interval, X invites false precision; compaction residuals are
strongly autocorrelated (consolidation has memory), so naive ±2σ bands are too narrow.

#### TASK 4.1 — Prediction intervals by block bootstrap

- [x] **4.1.1** *(audit 2026-06-11: COMPLETE — m4 metadata: 1000 paths, block 73/146, seed 20260610)* For each layer's adopted model: compute calibration residuals
  $r(t) = b_{\text{obs}} - b_{\text{pred}}$; resample them in contiguous blocks of 73
  epochs (≈ 1 year, preserving seasonal and consolidation autocorrelation) with
  replacement to build 1,000 alternative residual paths; add each path to the point
  prediction over the held-out epochs; take the 5th and 95th percentiles per epoch as the
  90% band.
- [x] **4.1.2** *(audit 2026-06-11: COMPLETE — coverage persisted; only 5/18 cells ≥ 0.85, 13 honestly labeled "calibrated to X%")* Coverage check: on each holdout design, the fraction of held-out observed
  values inside the 90% band must be ≥ 0.85. If coverage is below 0.85, widen via block
  length 146 (2 years) and re-check; if still failing, report the band as "calibrated to
  X%" — never silently re-label.
- [x] **4.1.3** *(audit 2026-06-11: COMPLETE — half-widths persisted, max 8.93 mm, no red flag)* Persist per-layer band widths (mean half-width in mm) alongside the RMSE
  table. A band half-width that exceeds the layer's observed range is a red flag — flag it.

#### TASK 4.2 — The apex-goal verdict table

- [x] **4.2.1** *(audit 2026-06-11: COMPLETE — `m4_apex_verdict_table.csv`, 18 rows)* Build and persist the final table: layer × design × {MAE, RMSE, threshold,
  PASS/FAIL}, using held-out epochs only, from the adopted M3 models. This single table IS
  the Level-1 verdict.
- [x] **4.2.2** *(audit 2026-06-11: COMPLETE — 5/6 pass; F3 fails MAE end+tail, not waiver-eligible)* Apply the Level-1 thresholds (thin: MAE < 5, RMSE < 10; thick: MAE < 10,
  RMSE < 20). Record the verdict per layer and overall. Expected risk concentrations:
  F3 end-gap and the tail design.
- [x] **4.2.3** *(audit 2026-06-11: COMPLETE — `PART1_v2_FINDINGS_20260610.md`, 5 sampled numbers all trace)* Write the Part-1-v2 findings document: physical story first (what each
  layer did and how well we can re-tell it), then the verdict table, then the corrected
  physics table (M2.2), then limitations. Every number cites file + field.

> **GATE M4 (the Level-1 verdict):** apex table persisted and every claim traceable.
> PASS requires ≥ 5 of 6 layers passing all designs; F3 may carry a documented waiver if
> it passes RMSE < 20 mm but misses MAE < 10 mm on the end gap only.

---

### MILESTONE M5 — Deployment Rehearsal (Gate to Part 2)

**Physical narrative:** of the 37 Part-2 stations, most have no co-located GPS — the
carrier there must be InSAR, with ~6-day cadence, more noise, and 500-m spatial averaging.
And unlike TUKU's continuous record, Part-2 MLCW records contain real multi-year gaps.
Validating GPS-carrier at TUKU and then shipping InSAR-carrier to 36 stations would be
testing one instrument and deploying another. Rehearse the deployment configuration at
TUKU, where the ground truth still exists.

#### TASK 5.1 — InSAR-carrier rehearsal at TUKU

- [ ] **5.1.1** Build the InSAR vertical displacement series for the TUKU cell (cumulative
  mm; remember the ×1000 metre→millimetre conversion) on the MLCW 5-day timeline, plus the
  persisted InSAR seasonal-harmonic series.
- [ ] **5.1.2** Re-run the full bake-off and the adopted M3 hybrid with InSAR replacing
  GPS as the carrier. Persist the side-by-side table: GPS-carrier vs InSAR-carrier
  held-out RMSE per layer per design.
- [ ] **5.1.3** Decision rule: if InSAR-carrier RMSE ≤ 1.5 × GPS-carrier RMSE per layer
  on the middle gap, Part 2's carrier is viable as-is; if worse, Part 2 needs per-station
  carrier smoothing or the seasonal-harmonic augmentation — record which.
- [ ] **5.1.4** Bonus coverage check: InSAR should cover the 2025 epochs that GPS
  (ending 2024-12-31) cannot. Quantify how many of TUKU's 1,572 epochs each carrier covers.

#### TASK 5.2 — Synthetic sparse-sampling stress test

- [ ] **5.2.1** Simulate the real-world failure modes on TUKU's continuous record by
  masking MLCW observations: (a) monthly sampling, (b) semi-annual, (c) annual,
  (d) a 2-year total blackout mid-record. Fit the adopted models on the masked record,
  evaluate on the masked-out epochs.
- [ ] **5.2.2** Persist the degradation curve: RMSE per layer vs sampling regime. The
  physically expected shape: thin elastic layers degrade slowly (their signal is trend +
  small breathing); F3 degrades fastest after blackouts that span a drought (the model
  cannot re-anchor the inelastic datum).
- [ ] **5.2.3** From the curve, state the minimum sampling cadence at which each layer
  still meets its Level-1 thresholds — this is the project's actionable recommendation to
  the well operators, and the cadence at which self-recalibration must run.

#### TASK 5.3 — Self-recalibration benefit (the never-executed Decision Point 3)

- [ ] **5.3.1** Scenario: fit through 2021-12-31; predict forward; then "receive" one new
  MLCW observation per layer at 2022-06-30; re-fit including it; measure 6-month-ahead
  RMSE before vs after the update.
  - Success: post-recalibration RMSE ≤ pre-recalibration RMSE for ≥ 4 of 6 layers.
- [ ] **5.3.2** Persist the result and issue Decision Point 3 (PASS: include
  recalibration in Part 2; FAIL: investigate whether the new point is an outlier or a
  regime change before trusting recalibration).

> **GATE M5 (Part-2 go/no-go):** all three rehearsal tasks persisted. GO requires:
> InSAR-carrier viable per 5.1.3 at ≥ 4 layers; degradation curve exists; DP3 issued.
> On GO, hand to the human for Part-2 authorization. **This plan ends here.**

---

## Appendix A — Canonical Equations and Symbols

| Symbol | Meaning | Units | Constraint |
|--------|---------|-------|------------|
| $b_k(t)$ | cumulative compaction of layer $k$ | mm | negative = compaction |
| $d(t)$ | surface displacement (GPS or InSAR carrier) | mm | negative = subsidence |
| $H(t)$ | absolute hydraulic head | m MSL | plausible range [−100, +200] |
| $u(t)$ | zero-referenced head $H(t) - H(t_{\text{ref}})$, $t_{\text{ref}}$ = 2015-01-16 | m | **never negate** |
| $h_c$ | preconsolidation head = min of pre-reference raw head | m MSL | Bug-F window rule |
| $V(t)$ | virgin exceedance $\min(0, \text{cummin}\,H - h_c)$ | m | monotonically non-increasing |
| $\tau_k$ | consolidation lag, integer 5-day epochs | epochs | $0 \le \tau \le 120$ (= 600 days) |
| $a_k$ | carrier apportionment share | — | $a_k \ge 0$, $\sum_k a_k \le 1$ |
| $S_{ke}, S_{kv}$ | bulk elastic / inelastic storage slopes | mm/m | $0 \le S_{ke} \le S_{kv}$ |
| $S_{ske}, S_{skv}$ | specific storage (per-thickness) | m⁻¹ | two-thickness rule (Task 2.2.1) |
| skill | $1 - \text{RMSE}_{\text{model}} / \text{RMSE}_{\text{baseline}}$ | — | counts only on held-out epochs |

**The lag-pairing invariant (Appendix-grade, because it has now been violated in four
separate programs across the project's history):** response `b[τ:N]` pairs with driver
`H[0:N−τ]`. Any code that slices both arrays identically has zero effective lag.

## Appendix B — Do-Not-Regress List (encodes all audits to date)

1. Head enters elastic terms zero-referenced, with an intercept (R1; theory §3.2).
2. $h_c$ lives in the same coordinate frame as the head it is compared against (R2).
3. Walk-forward / holdout evaluation runs in the cumulative domain — first-differencing
   erases Riley preconsolidation memory (incremental post-mortem).
4. Never promote a method on calibration-epoch metrics (pooled-R² illusion, 2026-06-09).
5. Never quote a number that does not trace to a persisted file (phantom 9.1×/9.3×
   gates, 2026-06-09; unpersisted DP2 skills, 2026-06-10).
6. The τ-lag pairing invariant (D1, 2026-06-10).
7. Missing increments are missing knowledge, never zero compaction (D3, 2026-06-10).
8. Future head is real head; the wells are still being read (D4, 2026-06-10).
9. A ratio computed from collinear columns is not a material property (D5, 2026-06-10).
10. MLCW negative = compaction; $dh$ never negated; F = aquifer, T = aquitard; wellcodes
    are 8-digit strings; InSAR metres × 1000 = mm.

---

*Plan written 2026-06-10 by the zero-trust audit session. Supersedes
`super_plan_2026-06-09.md`. No production code was modified by this plan.*
