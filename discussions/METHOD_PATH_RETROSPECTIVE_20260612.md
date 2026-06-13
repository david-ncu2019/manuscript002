# Method-Path Retrospective — Why the predict-and-reveal walk-forward was not the starting point

**Date:** 2026-06-12 · **Station:** TUKU pilot · **Scope:** the whole project from 2026-04-27 to today
**Question (verbatim intent):** "Why didn't we follow [the predict → reveal → self-adjust → blind-tail-score]
approach right from the start, instead of struggling through many approaches?"

---

## The answer in one paragraph

The thing you describe — start at an early year, predict the next well reading from the surface signal, reveal the
true reading, let the model re-anchor to it, repeat, then go blind for the tail and score — is a **measuring
harness, not a model.** It tells you *how to test and update* a predictor; it says nothing about *what predicts*.
The whole sentence "use the total surface deformation to predict the next compaction value" hides the entire
research problem inside the word *use*: what function turns 1 surface displacement number into 6 per-layer
compaction numbers spread across 300 m of sediment? Finding that function was the six-week struggle. You cannot run
a self-recalibrating walk-forward on a model you do not yet have and do not yet trust enough to freeze. So the
honest split is this: **the model half of your approach could not have been built first** (we had to discover, by
failing, what drives each layer and in what mathematical domain), **but the protocol half — the blind walk-forward
discipline itself — could and should have been imposed from day one.** We delayed the discipline, and that delay,
not the model search, is the part that was genuinely avoidable. It is why an outside Red Team had to catch skill
scores that were inflated by a factor of roughly four.

---

## 1. What your approach actually is — and why naming it matters

Your loop is three things stacked together:

1. **An expanding-window walk-forward** — train on a growing prefix of years, always predict the next held-out point
   before you look at it.
2. **Sequential data assimilation** — at each "reveal," reset the model's level/state to the new truth (a
   Kalman-filter-/Bayesian-style update), so the model self-corrects as sparse field visits arrive.
3. **A blind tail** — stop revealing for the final stretch you secretly hold, predict it cold, and score there.

In this project's own vocabulary that combination *is* the **M8 single-well sequential estimator** (the TimeOracle
leak-guard, the frozen calibration, the level reset at each visit, the cadence-degradation curve). You did not
abandon your idea and stumble onto something else — **you arrived at exactly your idea.** The reason it took so long
is that all three pieces above are a *wrapper*. The wrapper has a hole in the middle shaped like a model, and the
six weeks were spent casting and recasting the part that fills the hole.

**Keep this distinction in mind for everything below: protocol (the wrapper) vs model (the filler).** It is the
single key that explains the whole history.

---

## 2. The path we actually took (ten phases, compressed)

The full record is in `discussions/discussion_memory.md` §11–§12. Each phase failed or half-worked, and each
failure *licensed* a specific truth the final method depends on. The "struggle" is the chain of evidence.

| Phase (date) | What we tried | Why it failed / half-worked | Truth it licensed |
|---|---|---|---|
| 1 (05-30) | Raw GWL→MLCW lag search, MSE | Latched on τ≈365 d — the shared annual cycle aliasing, not physics | Detrend before any lag analysis |
| 2 (05-30) | Detrended τ search + literature storage coeffs | 2S-TOOL coeffs over-predict 10–300× at 5-day cadence; only F2 has genuine coupling (detrended r=+0.69) | 2S-TOOL is diagnostic-only; F1/F3/F4 are trend-dominated |
| 3 (05-31) | Seasonal harmonic characterization | F3/F4 seasonal phase unstable (std >59 d); seasonal amplitude not year-predictable (negative holdout skill) | Only F2 carries a reconstructable seasonal from the surface |
| 4 (06-01) | Walk-forward static f̄·InSAR, 37 stations | Structurally can't make sub-annual dynamics; fold-1 median skill **+0.004** (≈ a straight line) | A single static ratio cannot predict; the surface alone is not enough |
| 5 (06-01) | Detrended + lag-aware InSAR residual | F2/F3/F4 residual InSAR **anti-correlated** with residual MLCW (α<0, sign wrong) | InSAR alone cannot do deep dynamics; **GWL is structurally necessary** |
| 6 (06-06) | Incremental (ΔH) IHM-F with bounds | All 6 layers fail the 8–100× gate; ΔH≈0.001–0.003 m/epoch fits noise | The per-epoch *increment* domain is noise-dominated |
| 7 (06-06) | Cumulative two-regressor NNLS (Script 12) | F2 (25.1×) and F4 (17.3×) **pass**; F1/T1/T2/F3 fail | The **cumulative** Terzaghi/Riley form carries stress memory; it is the right domain |
| 8 (06-07) | Joint inversion over thickness + storage | Degenerate (RMSE depends only on thickness×S product); 93%-inelastic record makes V≈H collinear | Collinearity is a *physical identifiability limit*, not a bug |
| 9 (06-08) | α-fixed incremental re-run | Cancellation: model nets 0.1–0.9 mm/yr vs observed 8–15 mm/yr; **8–355× gap** | First-difference erases preconsolidation memory — irreversibly |
| 10 (06-08) | Guardrails + regional framework | (consolidation, not a model attempt) | Physics-law checks as necessary conditions, not the success metric |

Then, on **2026-06-09**, the objective itself was corrected (see §3), and the work pivoted to the single-well
sequential estimator (M8, 2026-06-11) — i.e. to your approach.

---

## 3. The root causes, ranked

### Structural — mostly unavoidable (the model half)

**R1 — We were solving a different problem than the one your method fits.**
Until 2026-06-09 the project was framed as *calibration + spatial extrapolation*: fit per-layer storage coefficients
at 37 wells, then krige them to 8,577 grid points. The whole "Expected Final Deliverables" list
(`discussion_memory.md` §9.5) is parameter maps, attribution percentages, and NetCDF fields — a calibration
mindset. Under that framing the natural method is a physics inversion (the IHM-F family), **not** a next-observation
forecaster. Your predict-and-reveal loop only becomes the obvious shape of the answer once the goal is restated as
*"the monitoring record is breaking; forecast and gap-fill one well's next reading and self-correct when a sparse
visit arrives."* That restatement is dated 2026-06-09 in the record — six weeks in. Before it, your method was not
even the target.

**R2 — The method is a harness, not a model (the central reason).**
As in §1: predict-reveal-adjust cannot start until a trustworthy inner predictor exists to freeze. The ten phases
were the search for that predictor. This is not a detour around your idea; it is the prerequisite your idea silently
assumes.

**R3 — We did not yet know what drives each layer.**
Your loop says "use the surface deformation." But whether the surface *can* drive each layer was an open question
with at least three candidate signals (InSAR, GPS, GWL head). The answer had to be *earned*: Phase 4 proved
InSAR-only static scaling is no better than a straight line (skill +0.004); Phase 5 proved the detrended surface is
*anti-correlated* with deep MLCW residuals (so it actively misleads on dynamics); the IHM-F arc proved head is
structurally required. Only after all that did the final shape emerge — **surface carrier = secular trend, GWL head
= partial sub-annual dynamics, sparse visits = datum.** That shape was an *output* of the experiments, not an
available input.

**R4 — We did not yet know the mathematical domain.**
The single most expensive lesson: the *incremental* (first-difference) formulation **cancels**. At 5-day cadence
ΔH is 0.001–0.003 m; differencing turns the decades-long secular head decline into a stationary oscillation and
throws away the integration constant — the preconsolidation stress maximum — so predicted net compaction is
0.1–0.9 mm/yr against observed 8–15 mm/yr (an 8–355× gap). Only the **cumulative** Terzaghi/Riley term
V(t)=min(0, cummin(H)−h_c) preserves permanent strain. This is a genuine physical-identifiability discovery; it was
found by building the incremental solver and watching it cancel (`discussions/POST_MORTEM_INCREMENTAL_CANCELLATION.md`).
No amount of a-priori cleverness reliably anticipates it.

**R5 — Parts of the problem are physically underdetermined, and you can only learn that by trying.**
The V/H collinearity in a 93%-inelastic record (Phase 8), the surface carrier being rank-1 (all layers ∝ the same
displacement), and the deep-clay F3 being watched by a piezometer screened 79 m too shallow
(`F3_FORENSIC_VERDICT_20260612.md`) are all *identifiability limits*, not tuning failures. The feasibility proof
(`FEASIBILITY_VERDICT_FINAL_20260611.md`) shows sub-annual multilayer dynamics from surface + 1-D head are
underdetermined at sparse cadence — provable only after the machinery existed to prove it.

### Process — largely avoidable (the protocol half)

**R6 — We deferred the validation discipline. This is the real, blameable lapse.**
Your *protocol* half — pretend to be blind, predict the tail you actually hold, score out-of-sample — is cheap and
model-agnostic. Had it been the scaffolding from week one, it would have killed the in-sample illusions on contact.
Instead, the headline reconstruction was fit on all ~1,081 epochs with no date split (leak L1); the hybrid was
selected and scored on the *same* three holdouts (leak L2); the monthly→annual sampling decay that is the project's
entire premise was never rehearsed (gap L3); and the reported skill of 0.79–0.82 was measured against a contaminated
baseline and later **retracted to ≤0 for F2/T2** by the independent Red Team
(`audit_red_team_v2/RED_TEAM_VERDICT_20260611.md`). Every one of these is an artifact of *not* walk-forward-testing
early. The model could not come first; **the protocol could have, and didn't.**

**R7 — Data-provenance fog made early validation untrustworthy anyway.**
For weeks the work trained and "validated" against `TUKU_reconst_grouped.csv` — a dense, smooth, computer-generated
fill (1,572 rows, zero gaps) — instead of the **264 genuine field visits** in `TUKU_orig_grouped.csv`. Worse, the
2024+ rows are 100% non-integer (interpolated, not field-verifiable), while real magnetic-ring readings are integer
millimetres. A predict-and-reveal harness built on day one would have *revealed fabricated numbers and assimilated
fiction* — rigorous-looking, but false. So even the protocol needed a prerequisite (knowing which bytes are real)
that also arrived late.

**R8 — How the work was organized slowed convergence.**
The project ran as a chain of short AI-agent sessions that rebuild context from handoff files each time, so hard-won
conclusions had to be re-derived or could be silently dropped (the repo institutionalizes this with PROGRESS.md,
discussion_memory.md, and `_OBSOLETE_` suffixes). No frozen, version-controlled baseline with a leak-guard existed
until M8's TimeOracle, so each method was self-graded under shifting rules — which is exactly why an outside Red Team
was needed. A standing one-week deadline added pressure toward "make the fit look good" (in-sample reconstruction)
over "prove it generalizes" (walk-forward).

### Cross-cutting

**R9 — Hindsight bias: the loop looks obvious only because its own results retired the alternatives.**
Calling predict-and-reveal "the most appropriate method" is a *conclusion the journey licensed*, not a fact
available at the start. Ex ante it competed with static ratios, harmonic reconstruction, the IHM-F A–F physics
candidates, ARX, and Prophet (several genuinely tried). It dominates only once you accept three non-obvious
premises that the phases established: (1) the goal is one-well next-observation forecasting, not a parameter field;
(2) the surface gives trend, not dynamics; (3) sparse future visits are a re-anchoring *asset*, not merely test
data. None of the three was settled on day one.

---

## 4. The honest counterfactual — what a day-one team could and could not have skipped

**Could have skipped (the avoidable weeks):** impose the protocol immediately — strict walk-forward, a blind tail,
genuine field visits only, and the *simplest defensible predictor first* (persistence/linear datum + a surface
trend carrier), adding head only where it demonstrably improves out-of-sample skill. That harness would have
rejected the over-complex inversions early, on their out-of-sample numbers, instead of letting them accumulate
in-sample credit for weeks. It would also have surfaced the provenance problem the moment a fabricated 2024 value
was "revealed."

**Could not have skipped (the irreducible core):** the cumulative-domain insight (without it even a trend baseline
mishandles stress memory), the provenance correction, and the F3 deep-clay failure (the driving head for the
compacting clay is simply unmeasured in the network). These are discovered only by trying.

**Net:** the achievable speedup is real but bounded — **weeks, not "day one."** The right reading is not "we picked
the wrong method and wasted six weeks." It is "we delayed the *honesty test* that would have compressed the method
search, and we under-invested in knowing our own data."

---

## 5. Forward rules (the post-mortem payoff)

1. **Separate protocol from model, explicitly, at the start of every objective.** Decide the validation harness
   before arguing about the model.
2. **Stand up the harness first:** walk-forward + blind tail + a leakage guard + genuine-truth-only scoring — *before*
   elaborating any model. Make the simplest defensible predictor the baseline every fancier model must beat
   out-of-sample.
3. **Freeze a version-controlled baseline before adding complexity.** No self-graded success under shifting rules;
   if you cannot reproduce a score from frozen inputs, it is not a score.
4. **Audit data provenance before you trust a single metric.** Know which numbers are field-measured and which are
   interpolated; never assimilate or score against fabricated points.
5. **Reframe the objective before choosing a method.** A calibration framing and a forecasting framing point at
   different methods; the framing error (R1) cost the most.

---

## 6. Paper-facing reading of the same path

For the manuscript, the meandering is not an embarrassment to hide — it is the **method-elimination evidence the
Discussion needs.** Stated positively, the project establishes, in order and on the record:

- **InSAR surface displacement alone cannot predict sub-annual per-layer compaction.** A rigorous 37-station
  walk-forward gives fold-1 skill +0.004 for static scaling, and the detrended surface residual is *anti-correlated*
  with deep-layer compaction (Phases 4–5). This rules out the simplest competing method quantitatively.
- **Groundwater head is structurally necessary** for any layer-wise dynamic term (the IHM-F arc).
- **The incremental formulation is physically wrong for monotonic consolidation:** first-differencing destroys the
  preconsolidation stress memory, producing an 8–355× amplitude deficit; the cumulative Terzaghi/Riley virgin term
  is required (Phases 6–9, post-mortem).
- **Sub-annual multilayer dynamics from total surface deformation + 1-D head are mathematically underdetermined at
  sparse cadence** (feasibility verdict), and deep aquitards such as F3 are additionally unobservable because no
  piezometer is screened in the compacting clay (F3 forensic). What *is* deployable and defensible is the secular
  trend apportionment (<1% trend error), datum maintenance via sparse visits, and partial F2 seasonal dynamics.

The single-well sequential estimator is then presented as the method that survives every one of these eliminations —
and the budget contribution (reducing monitoring at *one* well by replacing dense sampling with sparse re-anchoring
plus a frozen surface-carrier model) is exactly what the path proved is achievable.

---

## Evidence base

`discussions/discussion_memory.md` (§11 historical completions, §12 Phases 1–10, and the 2026-06-09 objectives
correction) · `discussions/POST_MORTEM_INCREMENTAL_CANCELLATION.md` · `discussions/FEASIBILITY_VERDICT_FINAL_20260611.md`
· `discussions/SEQ_REHEARSAL_FINDINGS_20260611.md` · `discussions/F3_FORENSIC_VERDICT_20260612.md` ·
`audit_red_team_v2/RED_TEAM_VERDICT_20260611.md` · auto-memory `tuku_repair_operation_status.md`.

*Status: advisory retrospective. It changes no result and unblocks nothing on its own; it records why the path was
shaped as it was, and what to do differently on the next objective.*
