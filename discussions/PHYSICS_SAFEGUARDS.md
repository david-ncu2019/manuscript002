# Physics Safeguards — AI-Generated Document Audit

**Date written:** 2026-06-08
**Auditor:** Claude Code (claude-sonnet-4-6) with advisor review
**Files audited:** 7 discussion documents dated 2026-06-08 (see table below)
**Ground truth source:** `CLAUDE.md` (repo root), Hung et al. (2021) WRR, Bug fix history 2026-06-04 to 2026-06-07

---

## 1. Purpose

This document records every physics error, wrong sign convention, incorrect hydrogeological claim, and physically impossible parameter value found in the seven AI-generated discussion documents written on 2026-06-08. For each finding: (a) the wrong claim as written, (b) the correct physics, (c) the source establishing correctness, and (d) a halt rule the writing AI must follow in future.

Documents were written by an AI agent without direct access to primary numerical sources. All errors below are transcription, derivation, or reasoning errors by that AI — not measurement errors in the data. A future AI writing new plans, guardrails, or analysis documents for this project must read this file before writing any quantitative claim about storage parameters, sign conventions, or preconsolidation heads.

---

## 2. Audit Summary Table

| File | Errors Found | Severity | Status |
|------|-------------|----------|--------|
| `POST_MORTEM_INCREMENTAL_CANCELLATION.md` | 1 minor | Terminology | Flag only — V(t) phrasing ambiguous but not wrong |
| `20260608_PROJECT_STATUS_AND_FUTURE_PLANS.md` | 1 | Low | Stale ratio gate lower bound retained from old spec |
| `20260608_SEQUENTIAL_PREDICTION_PLAN.md` | 1 | Critical | $h_c$ labeled "[m zero-ref]" — violates Bug F |
| `20260608_HISTORICAL_AUDIT_AND_REVISED_PLAN.md` | 2 | Critical / Medium | Sign convention claim inverted; deprecated loader cited |
| `20260608_PHYSICS_GROUNDED_REVISED_PLAN.md` | 2 | Medium | Wrong ratio gate lower bound; F4 classified as elastic sand aquifer |
| `20260608_REGIONAL_GUARDRAILS_FRAMEWORK.md` | 2 | Critical | Distal $S_{skv}$ factor-of-10 error; "peaks in middle" thesis physically wrong |
| `discussion_memory.md` (2026-06-08 sections only) | 0 | — | Phase 8 and Phase 9 are correct; no errors in scope |

**Total errors in scope:** 9 findings across 6 documents.
**Clean documents (no errors):** `POST_MORTEM_INCREMENTAL_CANCELLATION.md` (core physics argument correct); `discussion_memory.md` Phase 8/9 (correct).

---

## 3. Detailed Findings by File

---

### Finding 1 — CRITICAL: Distal $S_{skv}$ factor-of-10 error and wrong spatial pattern

**File:** `20260608_REGIONAL_GUARDRAILS_FRAMEWORK.md`, Invariant 2 table (line 58) and lines 60–64

**Wrong claim:**
```
| Distal | $1.91 \times 10^{-4}$ | ~1.6× |
```
And from the "Critical finding" text (line 60): "$S_{skv}$ is NOT monotonic. It peaks in the middle fan and DECLINES toward the coast."

**Correct physics:**
From Hung et al. (2021) WRR (cited in CLAUDE.md line 139):
- Middle fan: $S_{skv} = 1.33 \times 10^{-3}$ m⁻¹, ratio ~11.6×
- Distal fan: $S_{skv} = 1.91 \times 10^{-3}$ m⁻¹, ratio ~16×

$S_{skv}$ **increases monotonically** from middle to distal fan. The distal fan has more clay, producing higher inelastic compressibility — not lower. The "peaks in middle fan" thesis is not supported by Hung et al. (2021) data. It is an inference from a misread exponent.

**Source:** CLAUDE.md "Literature Priors (Hung et al. 2021 WRR)" table, line 139. Cross-verified: ratio 16× is physically consistent with the [8–100×] gate; ratio 1.6× (from the wrong value) falls below every version of the gate (even the relaxed [3, 50] lower bound).

**How the error propagated:** The document author (an AI) called NotebookLM's Choushui_Sub notebook and received the distal $S_{skv}$ as "$19.1 \times 10^{-5}$" — a RAG extraction artifact. The notebook stored the middle-fan column as $\times 10^{-4}$ and the distal-fan row as $\times 10^{-5}$ in error. The correct reading is $19.1 \times 10^{-4} = 1.91 \times 10^{-3}$, consistent with the middle-fan column unit. The author did not verify the ratio (1.6×) against the physical gate — if they had, the halt rule would have triggered.

**Cascading errors caused:** Invariant 2 (lines 60–64), the peaked DFA function (line 68), Invariant 4 "ratio peaks DFA 10–20 km" (line 115), and the TUKU-assessment "near expected peak" (line 203) are all built on this misread value. None of those claims are grounded in Hung et al. (2021).

**Halt rule:** Before writing any $S_{skv}$ value sourced from a notebook or summary, compute the implied $S_{skv}/S_{ske}$ ratio. If the ratio falls outside [3, 50] (relaxed gate), STOP. Report: "Ratio = [value] — below physical gate. Source value likely has exponent error. Verify against CLAUDE.md line 139 and the primary paper."

**Correction for the guardrails document:** Replace line 58 with:
```
| Distal | $1.91 \times 10^{-3}$ | ~16× |
```
Revise lines 60–64 to read: "$S_{skv}$ increases from middle to distal fan (1.33 → 1.91 ×10⁻³ m⁻¹ per Hung et al. 2021). Any guardrail that enforces a lower $S_{skv}$ ceiling at distal stations than at middle-fan stations is incorrect." Delete the peaked DFA function (line 68) and replace with a monotonically increasing function. Remove the "peaks in middle fan" claim from Invariant 2.

---

### Finding 2 — CRITICAL: Sign convention claim inverted

**File:** `20260608_HISTORICAL_AUDIT_AND_REVISED_PLAN.md`, Bottleneck 3 item 3 (line 61)

**Wrong claim:**
> "Sign convention mismatch → code keeps 'negative=subsidence' but project rules say 'positive=compaction'"

**Correct physics:**
CLAUDE.md "Sign Conventions" table (MLCW row): "negative = compaction." The code is **correct** — it keeps "negative=subsidence" which is consistent with "negative=compaction" for the MLCW signal. The document has the claim backwards.

**Source:** CLAUDE.md "Sign Conventions" table; also the same table entry for InSAR: "negative = subsidence."

**Why this is critical:** A future AI agent reading this document to audit or fix "sign convention mismatches" would conclude that the existing code needs a sign flip on MLCW data. Applying that flip would negate all compaction values and make compaction positive — introducing a systematic sign error into all downstream calculations.

**Halt rule:** Before asserting that a sign convention is wrong, read CLAUDE.md "Sign Conventions" table. MLCW: negative = compaction is the invariant. Code that stores compaction as negative numbers is CORRECT. Do not write "positive=compaction" as a project rule under any circumstances.

**Correction for the historical audit document:** Replace line 61 with:
> "Sign convention — code keeps 'negative=compaction' consistent with MLCW convention. No mismatch. The independent audit's conclusion was incorrect."

---

### Finding 3 — CRITICAL: $h_c$ values labeled as zero-referenced, violating Bug F

**File:** `20260608_SEQUENTIAL_PREDICTION_PLAN.md`, Key Data Paths table (line 188)

**Wrong claim:**
```
| h_c values | F1/T1=−2.344, F2=−5.086, T2=−8.457, F3=−4.456, F4=−7.008 [m zero-ref] |
```
The "[m zero-ref]" label means these values are in zero-referenced head coordinates (head relative to the value at REF_DATE 2015-01-16).

**Correct physics:**
Bug F (CLAUDE.md "Known Code Issues"): $h_c$ = minimum head observed from raw GWL feather rows dated **before** REF_DATE (2015-01-16), computed **before** zero-referencing. Post-alignment head values have the REF_DATE head subtracted; this shifts the entire time series, pushing the pre-2015 minimum head to a numerically lower (more negative) value. The result: $h_c$ appears to be reached later and more often → up to 51% of epochs are mis-classified as elastic when they should be inelastic.

Confirmed by Hydrogeology_Relearn notebook query: "h_c physically represents the historical minimum groundwater elevation that the aquifer system has ever experienced... Because h_c represents an absolute physical stress threshold embedded in the geological history of the deposit, it is fundamentally tied to this absolute datum." Using zero-referenced values loses the absolute datum.

**Risk:** If these five h_c values were derived from post-alignment data, the elastic/inelastic regime classification for the sequential prediction models will be wrong, with up to 51% of epochs mis-labeled. V(t) will be computed from incorrect h_c values, corrupting M3 and M4.

**Halt rule:** $h_c$ must always be expressed in m MSL (or the absolute head unit of the feather files), never in zero-referenced coordinates. Before using any tabulated $h_c$ value, verify it was computed from raw feather rows with `date < REF_DATE` (2015-01-16), before calling `zero_reference_head()` or any equivalent function. If a $h_c$ value is labeled "[m zero-ref]," it is UNVERIFIED and must be recomputed.

**Action required:** Verify the five $h_c$ values against `tau_demo_TUKU/01_run_tau_search.py` lines 115–121 (the Bug F fix). If they match values from that script's pre-REF_DATE window, they may be correct despite the label. If they come from post-alignment data, recompute and update the sequential prediction script.

---

### Finding 4 — Medium: Wrong lower bound for ratio gate

**File:** `20260608_PHYSICS_GROUNDED_REVISED_PLAN.md`, Day 1 gate (line 137)

**Wrong claim:**
> "Gate: Regularized fit produces $S_{skv}/S_{ske} \in [5, 50]$ for ≥ 3/6 layers (relaxed from [8, 100])"

**Correct physics:**
CLAUDE.md guardrails table, Check 3: "$S_{skv}/S_{ske} \in [3, 50]$ (relaxed from [8, 100])." The lower bound is **3×**, not 5×. Using 5× would incorrectly flag T1 (which has a fitted ratio of 2.9× — already on the boundary) as failing even after successful regularization.

**Secondary instance:** `20260608_PROJECT_STATUS_AND_FUTURE_PLANS.md`, line 263, states the gate as "8–100×" — the OLD gate, before the relaxation to [3, 50].

**Source:** CLAUDE.md "Automated Guardrails" table, Check 3, and the STATUS block (line 9): "Corrected gate (2026-06-07): Gate applies to specific-storage ratio... relaxed from [8, 100]."

**Halt rule:** The ratio gate is $[3, 50]$. Never write [5, 50] or [8, 100]. When a document says "relaxed gate," the current values are lower=3×, upper=50×. Check CLAUDE.md Check 3 before writing any gate criterion.

---

### Finding 5 — Medium: F4 grouped as "sand aquifer" — elastic characterization incorrect

**File:** `20260608_PHYSICS_GROUNDED_REVISED_PLAN.md`, Gap 3 (lines 36–45)

**Wrong claim:**
> "Sand (aquifers F1-F4): Lower porosity (25-50%), high permeability → immediate drainage → mostly ELASTIC, recoverable"

F4 is listed as an aquifer in this characterization.

**Correct physics:**
CLAUDE.md "Known Code Issues": "F4 at TUKU is geologically an aquitard despite being labeled 'aquifer' by ring position. F4 IHM-F elastic storage coefficients cannot be physically interpreted as aquifer $S_{ske}$." The TUKU borehole log (YL_WSYL23G1_TUKU.xlsx) shows the 283–300 m zone is entirely silt/mud (Z/M) with 0.0 m of gravel or coarse sand. `LAYER_COMPRESSIBLE_THICKNESS['F4'] = 16.617` m (entire span is compressible fine-grained material).

The document partially self-corrects in the same section (line 43: "F4 at TUKU is geologically an aquitard, not an aquifer"), but the blanket F1-F4 elastic characterization in lines 36–38 is not retracted and would be read first.

**Source:** CLAUDE.md "Known Code Issues" F4 entry; borehole data summary in CLAUDE.md guardrails table.

**Halt rule:** When characterizing aquifer layers F1–F4, always except F4 at TUKU explicitly. Do not apply "sand aquifer, elastic behavior" to F4. F4 at TUKU behaves as an aquitard. Any script treating F4 $S_{ke}$ as classic aquifer elastic storage is physically incorrect.

---

### Finding 6 — Medium: Deprecated loader `ihmf_io.py` cited for NaN bug fix

**File:** `20260608_HISTORICAL_AUDIT_AND_REVISED_PLAN.md`, Bottleneck 3 item 1 (line 59)

**Wrong claim:**
> "NaN propagation in `ihmf_io.py` → `merge_asof` without `dropna()`"

**Correct situation:**
CLAUDE.md "Known Code Issues": "`ihmf_io_multilayer.py` is the active loader for v3. Do not import `ihmf_io` in v3 scripts." Fixing `ihmf_io.py` would repair a deprecated loader that no v3 script imports. The NaN bug (if it exists in v3) would be in `ihmf_io_multilayer.py`, not in the deprecated file.

**Source:** CLAUDE.md "Known Code Issues" section.

**Halt rule:** Before filing a bug against a file named `ihmf_io.py`, confirm the file is imported by the script under investigation. For IHM-F v3, the active loader is `ihmf_io_multilayer.py`. Any NaN diagnosis must trace through `ihmf_io_multilayer.py` first.

---

### Finding 7 — Terminology (flag only): Ambiguous phrasing of V(t) monotonicity

**File:** `POST_MORTEM_INCREMENTAL_CANCELLATION.md`, line 25

**Ambiguous claim:**
> "V_j(t) never decreases"

**Correct interpretation:**
$V_j(t) \le 0$ always. On any epoch where the running minimum of lagged head drops below $h_c$, V becomes more negative (tracks the new minimum). On epochs where head is above $h_c$, V stays at its current value (the running minimum does not change). So "never decreases" means V never becomes less negative — the compaction accumulated through the virgin term is never reversed.

The physics is correct. The phrasing is ambiguous because "never decreases" for a quantity that is always $\le 0$ means "never becomes more negative," which is the opposite of what non-specialists expect from the word "decreases."

**Halt rule:** When describing V(t) monotonicity, use: "V(t) is monotonically non-increasing (it never becomes more negative once set; compaction tracked by V is permanent)." Never write "V never decreases" without clarifying that V ≤ 0 and the quantity being constrained is the magnitude.

---

## 4. Mandatory Physics Rules (ordered by halt severity)

The following rules govern every AI writing quantitative claims in this project. They are derived from CLAUDE.md and from the Bug Fix History (2026-06-04 to 2026-06-07). These override any claim made in planning documents, discussion files, or prior-agent outputs.

### Rule 1 — $S_{ke} \ge 0$, $S_{kv} \ge S_{ke}$ (HALT on violation)
Specific storage coefficients are physical material properties derived from compressibility. They cannot be negative. If a fit produces negative $S_{ke}$ or $S_{kv}$, the layer result is rejected. Do not save. Do not report. State: "$S_{ke}$ = [value] is negative — layer rejected."

### Rule 2 — $S_{skv}/S_{ske}$ ratio gate: [3, 50] (HALT on violation)
Ratio below 3× or above 50× indicates a degenerate fit (collinear predictors, missing stress history, or wrong h_c). Halt if outside this range. The OLD gate was [8, 100]; the RELAXED gate (current) is [3, 50]. Never write [5, 50] or [8, 100] as the active gate.

### Rule 3 — $h_c$ from pre-REF_DATE raw GWL only (HALT if wrong)
Preconsolidation head $h_c$ = minimum head from raw GWL feather rows with `date < 2015-01-16` (REF_DATE), before zero-referencing. Using post-alignment values pushes $h_c$ too low and can mis-classify up to 51% of epochs. Any $h_c$ value labeled "[m zero-ref]" is UNVERIFIED until its computation chain is traced to pre-REF_DATE raw rows.

### Rule 4 — $dh_{raw}$ sign: NEVER negate (HALT if negated)
$dh_{raw} = H(t) - H(t_{ref})$. Negative means head fell. Positive means head rose. Code must never negate this. If code contains `-dh` or `dh * -1` applied to head changes, halt and report.

### Rule 5 — MLCW sign convention: negative = compaction (HALT if inverted)
MLCW values are negative when the ground is compacting. Code storing compaction as negative is CORRECT. Any instruction to flip MLCW sign to make compaction positive is WRONG. "Project rules say positive=compaction" is a false claim.

### Rule 6 — V(t) monotonically non-increasing (HALT if V(t) recovers)
The virgin term $V_j(t) = \min(0, \text{cummin}(H_j(t - \tau_j)) - h_{c,j})$ must never become less negative once set. Compaction tracked through V is permanent (no rebound). If V(t) increases at any point, the implementation is wrong.

### Rule 7 — F = aquifer, T = aquitard; F4 at TUKU is an exception (HALT on inversion)
Taiwan CGS ring numbering: F = aquifer layer, T = aquitard layer. Never invert. Exception: F4 at TUKU is 100% silt/mud by borehole log. Its $S_{ke}$ cannot be interpreted as aquifer elastic storage. Apply aquifer characterization to F4 only after verifying borehole lithology.

### Rule 8 — $\tau \ge 0$, $\tau \le 120$ epochs (HALT on violation)
$\tau_{max}$ = 120 5-day epochs = 600 days. Any script using $\tau_{max} = 73$ is using the old value. Update to 120. $\tau$ represents the delay in 5-day units; $\tau = 1$ ≈ 5 days.

### Rule 9 — Layer assignment v4 only
GWL-to-MLCW layer assignment is version 4 (195 rows). v1, v2, v3 are superseded. Any script or document referencing `gwl_to_mlcw_layer_assignment_v3.csv` or earlier is stale.

### Rule 10 — IHM-F "F" is the candidate letter, not "Formation"
IHM-F = Inelastic Head Model, Candidate F of the A–F method enumeration. "F" is NOT an abbreviation for "Formation," "Formational," or any geological term. Do not expand "F" in publication.

### Rule 11 — Literature $S_{skv}$ values: always verify by ratio before accepting
Before accepting any $S_{skv}$ value from a notebook, summary, or discussion document, compute $S_{skv}/S_{ske}$ and check against [3, 50]. A ratio outside this range signals an exponent error in the source. This check caught the distal fan 10× exponent error in this audit. Hung et al. (2021) canonical values (CLAUDE.md line 139): Middle $S_{skv} = 1.33 \times 10^{-3}$ m⁻¹ (ratio ~11.6×); Distal $S_{skv} = 1.91 \times 10^{-3}$ m⁻¹ (ratio ~16×).

---

## 5. Scientific Context from NotebookLM

Queries were run on 2026-06-08 against three notebooks using `notebooklm` CLI (profile: default). All numerical values from notebooks were cross-checked against CLAUDE.md ground truth (see Rule 11 and Finding 1 for why this cross-check is required).

### Q1: Choushui_Sub — $S_{skv}$ spatial pattern across the fan

**Query:** "What specific storage values S_ske and S_skv did Hung et al. 2021 WRR report for the Choushui River Alluvial Fan middle and distal fan zones? Does S_skv increase or decrease from middle to distal fan?"

**Notebook response (excerpt):** "The middle fan records... $S_{skv}$ of $13.3 \times 10^{-4}$ m⁻¹ ... The distal fan yields... $S_{skv}$ of $19.1 \times 10^{-5}$ m⁻¹... the inelastic specific storage decreases from the middle fan to the distal fan."

**Critical note — notebook exponent artifact:** The notebook rendered distal $S_{skv}$ as $19.1 \times 10^{-5}$ m⁻¹. This is a RAG extraction artifact: the middle-fan value uses $\times 10^{-4}$ as the column unit; the distal row should be read in the same column as $19.1 \times 10^{-4} = 1.91 \times 10^{-3}$ m⁻¹. Cross-check: ratio $1.91 \times 10^{-3} / 1.16 \times 10^{-4}$ = **16×** (within [8–100] gate). Ratio from notebook literal: $1.91 \times 10^{-4} / 1.16 \times 10^{-4}$ = **1.6×** (below the relaxed 3× gate — physically impossible for virgin inelastic clay). The notebook's conclusion ("decreases from middle to distal") was derived from the artifact value and is incorrect.

**Correct conclusion from Hung et al. (2021), cross-verified by CLAUDE.md:** $S_{skv}$ increases from middle ($1.33 \times 10^{-3}$) to distal ($1.91 \times 10^{-3}$) fan. Distal clay-dominated sediment has higher inelastic compressibility, not lower. The $S_{skv}$ spatial pattern is monotonically increasing toward the coast — consistent with increasing clay fraction in the distal fan.

### Q2: Hydrogeology_Relearn — $h_c$ and zero-referencing

**Query:** "For preconsolidation head h_c in a confined aquifer system: should h_c be computed from original physical units (m MSL) or from zero-referenced head values? What is the physical meaning and what error occurs from post-alignment data?"

**Notebook response (key extract):** "The preconsolidation head $h_c$ physically represents the historical minimum groundwater elevation that the aquifer system has ever experienced... Because $h_c$ represents an absolute, physical stress threshold embedded in the geological history of the deposit, it is fundamentally tied to this absolute datum... If a numerical model uses zero-referenced data without rigorously tracking the absolute offset back to the MSL datum, the mathematical logic separating elastic specific storage from inelastic specific storage will fail."

**Physical implication:** For this project's CRAF model, $h_c$ must be extracted from raw GWL feather files using rows where `date < 2015-01-16 (REF_DATE)`, before any call to zero-reference the head series. This is what Bug F fixed in `tau_demo_TUKU/01_run_tau_search.py` lines 115–121.

---

## 6. Validation Checklist

Every new analysis document, guardrails update, or sequential prediction script must confirm all items before the document is written or the script produces output.

**Storage parameters:**
- [ ] $S_{ke} \ge 0$ for every layer fitted
- [ ] $S_{kv} \ge S_{ke}$ for every layer fitted
- [ ] $S_{skv}/S_{ske}$ ratio in [3, 50] for every layer accepted (warn if outside, halt if < 0)
- [ ] Distal fan priors use $S_{skv} = 1.91 \times 10^{-3}$ m⁻¹ (NOT $1.91 \times 10^{-4}$)
- [ ] Middle fan priors use $S_{skv} = 1.33 \times 10^{-3}$ m⁻¹

**Sign conventions:**
- [ ] MLCW: negative = compaction (never flip)
- [ ] $dh_{raw} = H(t) - H(t_{ref})$: never negated in code
- [ ] InSAR: negative = subsidence
- [ ] $S_{ke}$, $S_{kv}$, $\beta$: always $\ge 0$

**Preconsolidation head:**
- [ ] $h_c$ is in m MSL (absolute units), never labeled "[m zero-ref]"
- [ ] $h_c$ was computed from raw feather rows with `date < 2015-01-16`
- [ ] $h_c$ computation precedes zero-referencing in the script's call order

**Virgin term:**
- [ ] $V(t) \le 0$ always
- [ ] $V(t)$ is monotonically non-increasing (never recovers once more negative)
- [ ] Regime mask evaluated at driver time ($t - \tau$), not response time $t$

**Model parameters:**
- [ ] $\tau_{max}$ = 120 epochs (never 73)
- [ ] GWL wellcodes are 8-digit strings (never converted to int)
- [ ] Layer assignment version is v4 (never v3 or earlier)
- [ ] F = aquifer, T = aquitard (never inverted)
- [ ] F4 at TUKU is geologically an aquitard (exclude from "sand aquifer elastic" characterization)

**Loader and file conventions:**
- [ ] Active v3 loader is `ihmf_io_multilayer.py` (never `ihmf_io.py` in v3 scripts)
- [ ] PYTHONPATH reset before any `conda run` invocation
- [ ] Results marked `_OBSOLETE_*` are not referenced as current outputs
- [ ] InSAR feather values are in metres; multiply by 1000 for mm before use

**Ratio gate (spatial guardrails):**
- [ ] Any $S_{skv}$ value from a notebook or summary: verify ratio against [3, 50] before accepting
- [ ] Distal fan $S_{skv}$ ceiling in spatial guardrail is HIGHER than middle fan ceiling (monotonically increasing toward coast)
- [ ] No guardrail enforces a "peak at middle fan" structure for $S_{skv}$

---

*End of PHYSICS_SAFEGUARDS.md — do not modify the findings in Section 3 without tracing each change to a primary source file and line number.*
