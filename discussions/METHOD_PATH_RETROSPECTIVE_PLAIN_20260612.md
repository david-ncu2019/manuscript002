# Method-Path Retrospective (Plain-Language Version)

**This is the plain-language companion to `METHOD_PATH_RETROSPECTIVE_20260612.md`. Same content, same conclusions -- written for readers who want the story without the jargon.**

**Date:** 2026-06-12 | **Site:** TUKU pilot well | **Scope:** the whole project from 2026-04-27 to today

**The question we are answering:** "Why didn't we follow the predict-then-check approach right from the start, instead of struggling through many approaches for six weeks?"

---

## The answer in one paragraph

The approach being asked about works like this: start at an early year, use what you know (satellite data, groundwater readings) to predict the next underground measurement, then reveal the real measurement, let the model correct itself, repeat, and finally go blind for the last stretch to see if the model actually works. That sounds simple. But it is a **testing recipe, not a prediction tool.** It tells you *how to grade* a predictor. It says nothing about *what predicts*. The whole sentence "use the surface movement to predict what happens underground" hides the entire research problem inside the word *use*: what formula turns 1 surface sinking number into 6 separate squeezing numbers for 6 soil layers spread across 300 metres of sediment? Finding that formula was the six-week struggle. You cannot run a self-correcting test loop on a formula you do not have yet and do not trust enough to lock in. So the honest split is: **the formula-finding half of the work could not have been skipped** (we had to discover, by failing, what drives each layer and in what mathematical form), **but the honesty-test half -- the discipline of always predicting before peeking -- could and should have been in place from day one.** We delayed that discipline, and that delay is the part that was genuinely avoidable. It is why an independent outside review team had to catch skill scores that were inflated by roughly four times.

---

## 1. What the proposed approach actually is -- and why naming it matters

The approach being asked about stacks three things together:

1. **A growing-window prediction test.** Train on a growing chunk of past years. Always predict the next held-out point *before* you look at it. Then add that point to your training set and repeat. You never peek ahead.

2. **Self-correction when new field data arrives.** Each time a technician visits the well and takes a real reading, the model snaps its running estimate back to the truth. This is called "sequential data assimilation" in textbooks -- it just means "each time a new field measurement arrives, correct your running estimate."

3. **A blind tail.** You secretly hold back the last stretch of data and never peek at it until the very end. The model predicts it cold. You score only on that hidden stretch.

In this project's own vocabulary, that combination *is* the method we ended up building (called "M8 single-well sequential estimator" internally). **The destination was always the same.** The reason it took so long is that all three pieces above are a *wrapper* -- a testing frame. The wrapper has a hole in the middle shaped like a prediction formula, and the six weeks were spent trying and discarding formulas to fill that hole.

**Keep this distinction in mind for everything below: the testing wrapper (how you grade) versus the prediction formula (what you grade).** That is the single key that explains the whole history.

---

## 2. The path we actually took (ten phases, compressed)

The full record is in `discussions/discussion_memory.md` sections 11-12. Each phase failed or half-worked, and each failure taught us something the final method depends on.

| Phase (when) | What we tried (in plain words) | Why it didn't work | What we learned from the failure |
|---|---|---|---|
| 1 (May 30) | Searched for the best time delay between underground water levels and underground squeezing, using raw data | The search locked onto a ~365-day delay -- but that was just the shared seasonal cycle fooling the statistics, not real physics | You must remove the long-term trend and seasonal pattern before looking for time delays |
| 2 (May 30) | Removed trends, searched again, and plugged in textbook soil-squeezing numbers from a standard tool (called "2S-TOOL") | The textbook numbers over-predicted squeezing by 10 to 300 times at our 5-day measurement spacing. Only one layer (F2, the main sand/gravel layer at 35-217 m depth) showed a real connection between water level wiggles and squeezing wiggles (correlation +0.69 after removing trends) | The 2S-TOOL is useful for diagnostics only, not prediction. Most layers are dominated by the slow, decades-long sinking trend, not short-term water-level changes |
| 3 (May 31) | Tried to capture the seasonal (wet-dry cycle) squeezing pattern mathematically | For the two deepest layer groups (F3 at 140-275 m, F4 at 238-313 m), the timing of the seasonal peak wandered by more than 59 days from year to year. The seasonal wiggle size was unpredictable -- predicting next year's wiggle size on held-out data scored *worse* than guessing the average | Only the F2 layer (main sand/gravel) carries a seasonal pattern you can actually reconstruct from surface data |
| 4 (Jun 1) | Assigned each of the 6 underground layers a fixed fraction of the total surface sinking measured by InSAR (satellite radar that measures how much the ground surface moved), tested across 37 monitoring stations | A fixed fraction structurally cannot capture within-year dynamics. Prediction skill for the first test fold was +0.004 -- meaning the prediction was barely better than drawing a straight line (skill score +0.004, where 0 means "no better than the simplest guess") | A single fixed ratio cannot predict. The surface signal alone is not enough |
| 5 (Jun 1) | After removing trends, checked whether the leftover InSAR (satellite radar) wiggles could explain the leftover underground squeezing wiggles | For the deeper layers (F2, F3, F4), the leftover surface wiggles moved in the *opposite direction* from the leftover underground squeezing (negative correlation, wrong sign) | Satellite surface data alone cannot capture deep underground dynamics. **Groundwater level data is structurally necessary** -- you cannot skip it |
| 6 (Jun 6) | Switched to looking at tiny day-to-day *changes* (increments) in water level and squeezing, with physical bounds enforced | All 6 layers failed the physical reasonableness check (the ratio of permanent-to-recoverable squeezing should be 8-100 times; none passed). The day-to-day water level changes were tiny -- about 0.001 to 0.003 metres per 5-day step -- fitting noise, not signal | Looking at tiny day-to-day changes (the "incremental" approach) is noise-dominated at this measurement spacing |
| 7 (Jun 6) | Switched to looking at the *cumulative* (running total) squeezing, using a two-component formula with physical constraints (one component for recoverable squeezing, one for permanent squeezing) | Two layers passed: F2 (main sand/gravel, ratio 25.1 times) and F4 (deep silt/mud, ratio 17.3 times). The other four layers failed | The **cumulative** form of the textbook soil-mechanics formula (Terzaghi/Riley -- a formula that says: how much does soil squeeze when you change the water pressure?) is the right mathematical domain. It preserves the ground's "memory" of the heaviest load it ever felt |
| 8 (Jun 7) | Tried to jointly solve for layer thickness and squeezing coefficients at the same time | The math was degenerate: the answer depended only on the *product* of thickness times the squeezing coefficient, not on each one separately. Also, 93% of the historical record was in the permanent-squeezing regime, making two key inputs move almost identically (two inputs move so similarly that the math can't tell which one is doing the work) | This "two inputs looking the same" problem is a *physical measurement limit*, not a software bug. You cannot separate what your data does not separate |
| 9 (Jun 8) | Went back to the day-to-day change approach with a fixed surface-sinking fraction, hoping the bounds would help | The formula cancelled itself out. Predicted net squeezing: 0.1-0.9 mm/year. Observed: 8-15 mm/year. That is an **8 to 355 times gap.** Taking day-to-day differences erases the ground's "memory" of the heaviest load it ever felt -- and you cannot get that memory back | Day-to-day differencing permanently destroys the stress memory that drives most of the long-term sinking. This is irreversible. Only the cumulative (running-total) formula preserves it |
| 10 (Jun 8) | Built automated physical-law checks (guardrails) and a regional framework | This was consolidation, not a new model attempt | Physics-law checks are necessary safety rails, but passing them does not mean the model is good -- they are necessary conditions, not success criteria |

Then, on **2026-06-09**, the research objective itself was corrected (see section 3 below), and the work pivoted to the single-well sequential estimator -- the predict-then-check approach that was the original question.

---

## 3. Why we got stuck -- the real reasons, ranked

### Reasons that were hard to avoid (we had to learn these the hard way)

**R1 -- We were solving the wrong problem for six weeks.**

Until June 9, the project was framed as: "fit soil-squeezing parameters at 37 wells, then spread those parameters across 8,577 grid points to make a regional map." That is a *calibration* problem. Under that framing, the natural tool is a physics inversion (fit parameters to match observations), **not** a next-reading forecaster. The predict-and-check approach only becomes the obvious shape of the answer once you restate the goal as: "the monitoring record is breaking because well visits are getting rarer and more expensive; forecast the next reading and self-correct when a sparse visit happens." That restatement is dated June 9 in the record -- six weeks in. Before that date, the predict-and-check approach was not even the target.

**R2 -- The approach is a testing wrapper, not a prediction formula (the central reason).**

As explained in section 1: predict-check-adjust cannot start until you have a trustworthy inner prediction formula to lock in and test. The ten phases were the search for that formula. This is not a detour around the original idea; it is the prerequisite the idea silently assumes.

**R3 -- We did not know what drives each layer.**

The approach says "use the surface sinking signal." But *whether* the surface signal can drive each of the six layers was an open question with at least three candidate inputs: InSAR (satellite radar surface movement), GPS (ground-station surface movement), and GWL (groundwater level -- how high the water sits underground). The answer had to be earned: Phase 4 proved that using only InSAR with a fixed ratio is no better than a straight line (skill +0.004). Phase 5 proved that after removing trends, the surface signal actually moves *opposite* to deep underground squeezing (so it actively misleads). The physics-formula arc proved that water-level data is structurally required. Only after all of that did the final shape emerge: **GPS surface movement carries the long-term sinking trend, groundwater level provides partial seasonal dynamics, and sparse field visits anchor the running estimate.** That shape was an *output* of the experiments, not an available input.

**R4 -- We did not know the right mathematical form.**

The single most expensive lesson: the "incremental" formulation (looking at tiny day-to-day changes instead of the big cumulative picture) **cancels itself out.** At 5-day measurement spacing, the water-level change per step is only 0.001 to 0.003 metres. Taking differences turns the decades-long slow decline in water levels into a flat-looking oscillation and throws away the integration constant -- the ground's "memory" of the heaviest load it ever felt (called the preconsolidation stress maximum). The result: predicted net squeezing is 0.1-0.9 mm/year against observed 8-15 mm/year (an **8 to 355 times gap**). Only the **cumulative** form of the textbook soil-mechanics formula preserves permanent strain. This is a genuine physical discovery; it was found by building the incremental solver and watching it cancel (documented in `discussions/POST_MORTEM_INCREMENTAL_CANCELLATION.md`). No amount of planning ahead would have reliably predicted this.

**R5 -- Parts of the problem are physically unsolvable with the available instruments, and you can only learn that by trying.**

Three specific dead ends turned out to be measurement limits, not tuning failures:

- In a record where 93% of all data points are in the permanent-squeezing regime (Phase 8), two key mathematical terms become nearly identical. The math cannot tell which one is doing the work (collinearity). That is a property of the physics, not the code.
- The GPS surface movement signal is just one number (the total surface sinking), being split among six layers. There is only one real pattern being divided six ways -- not enough independent information to separate them (this is called being "rank-deficient" in mathematics -- there's only one real pattern being split among six layers, not enough independent information).
- The deep clay layer F3 (at 140-275 m depth) is being monitored by a water-level gauge (piezometer) installed at 177 m -- but the clay that actually squeezes sits at 256 m. That is a **79-metre depth gap** between where we measure water pressure and where the squeezing happens. The seasonal correlation between the gauge reading and the squeezing is only 0.10 (almost no connection). This is documented in `discussions/F3_FORENSIC_VERDICT_20260612.md`. No algorithm can fix a missing sensor.

### Reasons that were avoidable (we should have done better)

**R6 -- We delayed the honesty test. This is the real, blameable mistake.**

The *testing wrapper* half of the approach -- pretend to be blind, predict the readings you secretly hold, score only on data the model never saw -- is cheap and works with any formula. Had it been the scaffolding from week one, it would have killed the overly-optimistic results on contact. Instead:

- The headline reconstruction was fit on all ~1,081 data points with no date split (data leakage #1).
- The hybrid method was selected and scored on the *same* three holdout points it was tuned on (data leakage #2).
- The real-world scenario -- monitoring visits decaying from monthly to annual to nothing -- was never rehearsed (gap #3).
- The reported prediction skill of 0.79-0.82 was measured against a contaminated baseline and later **retracted to 0 or below for two layers (F2 and T2)** by the independent Red Team review (`audit_red_team_v2/RED_TEAM_VERDICT_20260611.md`).

Every one of these problems is an artifact of *not* testing honestly from the start. The formula-search could not have come first. **The testing discipline could have, and it did not.**

**R7 -- We did not know which of our data was real.**

For weeks the work trained and "validated" against a file (`TUKU_reconst_grouped.csv`) that contained 1,572 rows of dense, smooth, computer-generated gap-filling -- zero gaps, no missing values. The actual field measurements live in a different file (`TUKU_orig_grouped.csv`) and contain only **264 genuine field visits**. Worse, the data from 2024 onward is 100% non-integer (meaning it was interpolated by software, not read off a physical instrument -- real magnetic-ring well readings are always whole-number millimetres). A predict-and-check testing loop built on day one would have *revealed made-up numbers and corrected the model toward fiction* -- rigorous-looking, but false. So even the testing protocol needed a prerequisite (knowing which data bytes are real) that also arrived late.

**R8 -- The way the work was organized slowed progress.**

The project ran as a chain of short AI-assistant sessions that rebuild context from handoff files each time. Hard-won conclusions had to be re-derived or could be silently dropped. The repo deals with this using tracking files (PROGRESS.md, discussion_memory.md, and `_OBSOLETE_` suffixes on old outputs), but no frozen, version-controlled baseline with a leakage guard existed until the final method's TimeOracle safeguard. Each method graded itself under shifting rules -- which is exactly why an independent outside Red Team review was needed. A standing one-week deadline added pressure toward "make the fit look good on training data" over "prove it works on unseen data."

### A bit of both

**R9 -- The predict-and-check approach looks obvious only in hindsight, because its own results retired the alternatives.**

Calling predict-and-check "the most appropriate method" is a *conclusion the journey licensed*, not a fact available at the start. At the beginning, it competed with fixed ratios, seasonal-pattern reconstruction, the A-through-F physics formula candidates, time-series auto-regression, and the Prophet forecasting library (several genuinely tried). It dominates only once you accept three non-obvious premises that the phases established:

1. The goal is one-well next-reading forecasting, not a regional parameter map.
2. The surface gives the long-term trend, not the seasonal dynamics.
3. Sparse future field visits are a *correction asset*, not merely test data.

None of these three premises was settled on day one.

---

## 4. The honest what-if -- what a day-one team could and could not have skipped

**Could have skipped (the avoidable weeks):** Set up the testing discipline immediately -- strict growing-window prediction, a blind tail (a stretch of data you secretly hold back and never peek at until the very end), genuine field visits only, and the *simplest defensible predictor first* (a straight line plus a surface-trend carrier). Add groundwater-level data only where it demonstrably improves out-of-sample scores. That testing harness would have rejected the overly complex physics inversions early, based on their out-of-sample numbers, instead of letting them accumulate training-data credit for weeks. It would also have exposed the data-provenance problem the moment a computer-generated 2024 value was "revealed" to the model.

**Could not have skipped (the irreducible core):** The cumulative-domain insight (without it, even a simple trend baseline mishandles the ground's stress memory). The data-provenance correction (learning which file contains real measurements versus gap-filled fiction). The F3 deep-clay failure (the water-level gauge that drives the prediction for the compacting clay at 256 m depth is installed 79 m too shallow -- no algorithm fixes a missing sensor).

**Net:** the achievable speedup is real but bounded -- **weeks, not "from day one."** The right reading is not "we picked the wrong method and wasted six weeks." It is "we delayed the *honesty test* that would have compressed the method search, and we under-invested in knowing our own data."

---

## 5. Rules for next time (the payoff of this post-mortem)

1. **Separate the testing protocol from the prediction formula, explicitly, at the start of every research objective.** Decide *how you will grade* before arguing about *what to grade*.

2. **Stand up the testing harness first:** growing-window prediction + a blind tail + a data-leakage guard + genuine-measurements-only scoring -- *before* making the formula fancier. Make the simplest defensible predictor (a straight line, a persistence model) the baseline that every fancier formula must beat on unseen data.

3. **Lock in a version-controlled baseline before adding complexity.** No self-graded success under shifting rules. If you cannot reproduce a score from frozen inputs, it is not a score.

4. **Audit data provenance before you trust a single metric.** Know which numbers were measured by a technician in the field and which were filled in by software. Never correct toward or score against fabricated points.

5. **Reframe the objective before choosing a method.** A "fit parameters for a regional map" framing and a "forecast the next well reading" framing point at different methods. The framing error (R1) was the most expensive single mistake.

---

## 6. How to tell this story in the research paper

For the manuscript, the winding path is not an embarrassment to hide. It is the **method-elimination evidence the Discussion section needs.** The six weeks of apparent struggle are actually six weeks of proof that simpler, more obvious approaches do not work. Stated positively, the project establishes, in order and on the record:

- **Satellite surface movement alone cannot predict seasonal per-layer squeezing.** A rigorous 37-station growing-window test gives first-fold skill of +0.004 for fixed-ratio scaling (barely better than a straight line), and after removing the long-term trend, the leftover surface signal is *anti-correlated* with deep-layer squeezing (Phases 4-5). This rules out the simplest competing method with numbers, not hand-waving.

- **Groundwater level data is structurally necessary** for any layer-specific seasonal term (the physics-formula arc proved this).

- **The day-to-day-change formulation is physically wrong for long-term consolidation.** Taking day-to-day differences destroys the ground's memory of the heaviest load it ever felt (the preconsolidation stress memory -- the ground "remembers" the heaviest load it ever felt, and you cannot erase that memory by looking at tiny daily changes). This produces a predicted squeezing rate 8 to 355 times too small. The cumulative (running-total) form of the textbook soil-mechanics formula is required (Phases 6-9, post-mortem analysis).

- **Seasonal per-layer dynamics from total surface sinking plus one-dimensional water-level data are mathematically unsolvable at sparse measurement spacing** (feasibility verdict). Deep clay layers like F3 are additionally unobservable because no water-level gauge is installed in the actual compacting clay -- there is a 79-metre gap between the gauge and the clay (F3 forensic analysis). What *is* achievable and defensible is: the long-term trend split across layers (less than 1% trend error), keeping the estimate anchored through sparse field visits, and partial seasonal dynamics for the F2 layer (main sand/gravel at 35-217 m depth).

The single-well sequential estimator is then presented as the method that survives every one of these eliminations. Its practical contribution -- reducing monitoring cost at each well by replacing frequent sampling with sparse re-anchoring visits plus a frozen surface-carrier model -- is exactly what the path proved is achievable and nothing more.

---

## Evidence base

All supporting documents, for readers who want the full technical detail:

- `discussions/discussion_memory.md` (section 11: historical completions; section 12: Phases 1-10; and the 2026-06-09 objectives correction)
- `discussions/POST_MORTEM_INCREMENTAL_CANCELLATION.md` (why taking day-to-day differences kills the prediction)
- `discussions/FEASIBILITY_VERDICT_FINAL_20260611.md` (what is and is not solvable with available data)
- `discussions/SEQ_REHEARSAL_FINDINGS_20260611.md` (rehearsal of the sequential prediction approach)
- `discussions/F3_FORENSIC_VERDICT_20260612.md` (why the deep clay layer F3 cannot be predicted with current instruments)
- `audit_red_team_v2/RED_TEAM_VERDICT_20260611.md` (independent Red Team review that retracted inflated skill scores)
- Auto-memory: `tuku_repair_operation_status.md`

*Status: advisory retrospective. It changes no result and unblocks nothing on its own. It records why the path was shaped as it was, and what to do differently on the next objective.*
