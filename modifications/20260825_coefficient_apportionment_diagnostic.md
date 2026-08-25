# Diagnostic finding: apportionment claim in discuss003.tex line 22 is section-specific, not general

**Scope:** `sections/discuss003.tex` (`subsec:discussion_layerwise_estimation`, line 22),
`sections/results004.tex` (`tab:selected_coefficients`, line 22's open author note at line 24).
**Compared against:** `standardized_coefficients.parquet` (run_048,
`manuscript_results003_calendar_aligned_38predictors/results/sec4_1/results/`) — the confirmed
source of `tab:selected_coefficients` (reproduced its published S5/`dS_total` cell: median 0.01,
10th–90th percentile [-0.07, 0.03], using all 24 folds with none excluded).
**New script (read-only, no manuscript file edited):**
`D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\diagnostics\scripts\diag_29_coef_apportionment.py`,
output CSV and figure alongside it (`diag_29_coef_apportionment_output.csv`,
`diag_29_coef_apportionment.png` — **internal-review figure, not manuscript-style**, 6-panel grid
one per section).
**Verdict:** Line 22's claim is not wrong, but it is stated more generally than the data supports.
The finding below is a **statistical/model-mechanics result only** — it says nothing about depth,
geology, or hydrogeology, and must not be described that way in any drafted prose (per author
instruction, 2026-08-25: coefficient explanations in §4.1/§5.1 stay mathematical/statistical, not
physical).

---

## Finding: the apportionment signature appears in 2 of 6 section models, not generally

**Where:** `discuss003.tex` line 22 — "Bayesian ridge regression therefore apportioned their shared
contribution among coefficients and moderated coefficient changes when the observations provided
less support for a stable relation \citep{dormann_collinearity_2013, hastie_elements_2009,
mackay_bayesian_1992}." This sentence is supported only by citation, not by any number computed
from this study's own coefficients.

**What the diagnostic shows:** The four surface-displacement predictors (`dS_total`, `d2S_total`,
`dS_total_lag1`, `dS_total_lag3`) are collinear by construction — they describe the same surface
signal at adjacent time offsets. If BRR apportions a shared signal among collinear members, the
members should trade off against each other within a fit: when one's weight rises, another's should
fall, i.e. a **negative** pairwise correlation of their per-cycle coefficient values across the 24
recalibration cycles. A **positive** correlation means the opposite — the members move together
rather than trading off.

Computed separately per section (6 independent regression models), first-differenced across cycles
to remove each series' own time trend before correlating (raw-level correlation is contaminated by
shared drift and is reported in the CSV only for reference — see the script's docstring for why),
and cross-checked with the first calibration cycle (burn-in) excluded to confirm the result is not
an artifact of that single fold:

| Section | Current-vs-3-month-lag correlation | Stable after excluding burn-in fold? |
|---|---:|---|
| S1 | +0.32 | — (positive, not a trade-off) |
| S2 | −0.69 | Yes (−0.83 with burn-in excluded) |
| S3 | −0.995 | Yes (−0.996 with burn-in excluded) |
| S4 | +0.66 | — (positive, not a trade-off) |
| S5 | +0.995 (raw) → +0.95 (burn-in excluded) | Unstable — see note below |
| S6 | +0.36 | — (positive, not a trade-off) |

Only S2 and S3 show the negative-correlation trade-off signature, and it survives removing the
burn-in fold in both. In S1, S4, and S6, the same pair of variables moves together (positive
correlation) — the opposite of a trade-off. This lines up with an independent piece of evidence
already in the manuscript: S2 and S3 are the only two sections where `tab:selected_coefficients`
already reports the 3-month-lag coefficient with the opposite sign from the current-increment
coefficient. Two independently computed things (a sign difference in the published table, and a
negative cross-cycle correlation in the new per-cycle diagnostic) point at the same two sections —
this is a coherent statistical pattern, not a coincidence, but it is still only 2 of 6 section
models and should be described with that scope, not generalized to "Bayesian ridge regression" as
a blanket behavior.

**S5 note (the section with the open author question at `discuss003.tex:24`):** the raw
correlation for S5 is very high (near +1) mainly because of the burn-in fold (the first
calibration cycle, fitted on the initial record alone, is a large outlier relative to the other 23
cycles). Once that fold is excluded, S5's pairwise correlations become inconsistent across
variable pairs (e.g., current-increment vs. change-in-increment drops from +0.97 to +0.14, and
current-increment vs. 1-month-lag stays high at +0.91). **S5 does not currently give a clear
answer either way** — this diagnostic does not resolve the open note about S5's near-zero
current-increment coefficient, and no claim should be drafted from it for S5 specifically.

**What this does and does not prove:** This confirms that BRR's coefficient behavior under
collinearity is not uniform across the six independently fitted section models at Tuku — in 2 of 6
models there is a measurable trade-off between two specific predictors; in the other 4, there is
not. It does **not** identify why S2 and S3 differ from the other four sections in this respect.
With only 6 section models, 2 matching a pattern is not enough on its own to rule out coincidence,
and no depth-related, geological, or hydrogeological explanation is supported by this diagnostic —
none was tested, and none should be inferred from it.

**Recommendation:** If this is drafted into `discuss003.tex` line 22, narrow the sentence's scope
instead of leaving it general: state that the apportionment behavior is observed specifically in
the S2 and S3 models (naming the negative correlation and its consistency with the sign pattern
already in `tab:selected_coefficients`), and state plainly that the other four section models do
not show it. Do not extend this into a statement about why S2/S3 differ — that would be new,
unsupported content requiring separate justification the current diagnostic does not provide. Any
drafted sentence should stay in mathematical/statistical language (collinearity, coefficient
trade-off, cross-cycle correlation) and avoid physical-sounding framing ("this reflects...",
"because this section...", "which suggests a mechanism..."), per the author's explicit instruction
this session.

**Figure status:** `diag_29_coef_apportionment.png` exists for internal review only (6-panel grid,
all sections, diagnostic styling — not built to the manuscript's figure conventions). If this
finding is approved for the manuscript, a separate, narrower figure would need to be built to
manuscript style (likely showing only the two relevant variables for S2/S3, or S2/S3 next to one
non-trade-off section for contrast) — not yet done, out of scope until the wording above is
approved.

**Severity:** Low-to-medium — does not contradict anything currently in the manuscript, but the
existing sentence is broader than the evidence; leaving it as-is is not a factual error, only an
unverified generalization now that verification has been attempted and come back partial.

---

## Summary

| Item | Verdict |
|---|---|
| discuss003.tex line 22 ("apportioned their shared contribution") | Supported in S2/S3 only (negative, burn-in-robust cross-cycle correlation between current-increment and 3-month-lag coefficients); not supported in S1/S4/S6 (positive correlation, no trade-off); inconclusive in S5 (result driven by the burn-in fold, unstable once removed) |
| Cross-check with `tab:selected_coefficients` | S2 and S3 are also the only two sections where the published table already shows the 3-month-lag coefficient with the opposite sign from the current-increment coefficient — consistent with, not contradicting, the new diagnostic |
| S5 open note (`discuss003.tex:24`) | Not resolved by this diagnostic — no claim should be drafted for S5 from this data |
| Framing constraint | Any prose drafted from this finding must stay mathematical/statistical (collinearity, coefficient trade-off) — no physical/geological interpretation, per author instruction 2026-08-25 |
| Figure | Internal-review figure exists (`diag_29_coef_apportionment.png`); a manuscript-style figure is not yet built and is a separate, later step if this finding is approved |
| Manuscript files edited | None — diagnostic only, script and outputs live entirely under `007_tests/014_ml_nowcast/diagnostics/scripts/` |
