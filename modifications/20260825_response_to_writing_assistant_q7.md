# Response to the writing assistant's Q7 (paragraph ordering, discuss003.tex subsec:discussion_layerwise_estimation)

## Original question from the writing assistant (verbatim, Vietnamese)

> Q7: Có đồng ý đặt đoạn so sánh với Hung et al. (2025) ngay trước đoạn kết của Subsection 5.1
> không?
>
> Mạch văn sẽ là:
>
> Kết quả chính → diễn giải → liên hệ Hung et al. → kết thúc bằng đóng góp của nghiên cứu hiện tại.

---

**Scope:** Answers the ordering question left open at the end of
`20260825_response_to_writing_assistant_q6.md` — whether the Hung et al. (2025) comparison paragraph
sits before or after Q1 Step 4's already-approved positive-contribution closing paragraph. No
manuscript file is edited by this note.

**Verdict: approved. This ordering is not merely acceptable — it is the stronger choice, and the
primary-source read behind the Q6 addendum shows why.**

---

## Why this order is the stronger choice, not just a defensible one

Placing the Hung et al. (2025) paragraph immediately before the closing contribution paragraph means
Q1 Step 4's closing claim — that continuous observations can support depth-section estimation, but
MLCW still provides the depth resolution needed to see where an aggregate signal no longer represents
the profile — is the true last word of the subsection, exactly as Step 4 intended. But this ordering
does more than preserve that closing move; it strengthens it.

The Q6 addendum's full-text read of
`D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\002_docs\papers\Hung et al. - 2025 - Near real-time subsidence monitoring and AI forecasting with multi-depth extensometers_full_paper.md`
found that Hung et al. (2025) reaches the same conclusion about MLCW's core value independently.
Their Table 3 and Section 8.1 state plainly: "The MLCW excels in spatial resolution... [while]
extensometers provide high-frequency, automated measurements... Each system offers distinct
advantages." This is Hung et al.'s own assessment that MLCW's comparative strength is depth
resolution — the same claim Step 4 makes about this manuscript's own findings. Placed directly before
Step 4's close, the Hung et al. paragraph lets the closing paragraph's claim land with independent,
textually verifiable support from the closest comparable prior study, rather than resting on this
manuscript's own results alone. This only works in the order Q7 proposes: Hung et al. paragraph, then
the contribution close. Reversing the order would leave this connection unmade.

This is a legitimate, safe use of Hung et al. (2025) — it is a qualitative agreement about MLCW's role
(depth-resolved measurement has value no continuous point or surface-integrated instrument can
replace), not a numeric comparison of error metrics. It does not touch the RMSE-unit-mismatch risk
flagged in the Q6 addendum (0.34-0.52 mm over Hung et al.'s four-month window versus this
manuscript's 0.21-0.66 mm/month), and it does not contradict Q6's decision to decline direct metric
comparison. Recommend the drafted paragraph state this agreement explicitly — for instance, that both
studies independently identify MLCW's depth resolution as a capability neither continuous surface
displacement nor high-frequency point extensometer measurements can substitute for — since it is the
paragraph's strongest available support and is not yet used in Q6's three-part structure as approved.

## One redundancy risk to check before drafting

`discuss003.tex` line 12 already cites a different Hung-group paper (`hung_measuring_2021`) for a
related point, near the opening of this same subsection: "Vertical surface displacement represents
the integrated response of the monitored profile, whereas multilayer measurements distinguish
deformation among depth sections, as demonstrated by \citet{hung_measuring_2021}. MLCW measurements
can therefore show where a station-level signal does not describe the profile uniformly." That
sentence itself carries an unresolved `% my note %` from the author stating the point is unclear and
its connection to the surrounding Results and Discussion is not obvious — worth keeping in mind, since
it signals this opening framing may need its own revision independent of Q7.

The two citations serve different rhetorical jobs (the 2021 paper establishes, early in the
subsection, why depth-resolved measurement matters at all; the 2025 paper distinguishes this study
from the closest comparable prior work, late in the subsection, and — per this response's
recommendation above — corroborates the closing claim). Different jobs, but adjacent subject matter
("MLCW resolves what integrated measurements cannot") appearing twice in one subsection risks reading
as repetitive if the wording is not kept visibly distinct. Recommend checking, once both passages are
drafted, that the opening citation (2021) and the closing-adjacent citation (2025) do not restate the
same sentence-level claim in near-identical language.

## Confirming where Q5's coefficient-variation argument sits in this sequence

Q7's stated sequence — "Kết quả chính → diễn giải → liên hệ Hung et al. → kết thúc" — does not
explicitly place the coefficient-variation-by-depth argument approved in Q5 (answering
`results004.tex` line 50). The Q5 response recommended that content extend the existing shrinkage
passage at `discuss003.tex` line 13 rather than form a new, separate paragraph. Read together with
Q7, this suggests the coefficient-variation content sits within the "diễn giải" (interpretation) stage
of Q7's sequence, not as its own late-subsection step alongside the Hung et al. paragraph. Recommend
confirming this placement explicitly when the paragraphs are assembled, since Q7's four-step
description does not name it directly and a fifth interpretation-stage item is easy to lose track of
across seven separate exchanges.

## An aggregate observation across Q1-Q7, not a Q7-specific concern

`subsec:discussion_layerwise_estimation` has now accumulated, across seven exchanges, a substantial
paragraph sequence: the S1-S4/S5-S6 question (Q1 Step 1), the SD-ratio/correlation diagnostic (Q1 Step
2, refined in Q2-Q3), the physical-interpretation layers for S5 specifically with the S6 explanation
left open (Q1 Step 3, corrected in Q4-Q5), the coefficient-variation-by-depth argument for line 50
(Q5), the Hung et al. (2025) comparison (Q6), and the closing contribution (Q1 Step 4). This is not a
defect — each piece individually answers a real, author-flagged question and was approved on its own
merits — but it is worth a length and pacing check once all pieces are drafted together, to confirm
the subsection still reads as one coherent argument rather than a sequence of individually-justified
additions. This is offered as an observation for the eventual full-draft review, not a condition on
Q7 itself.

---

## Summary

| Item | Verdict |
|---|---|
| Hung et al. (2025) paragraph placed before the closing contribution paragraph | Approved — and stronger than the reverse order, because it lets the closing claim draw independent support from Hung et al.'s own stated conclusion about MLCW's depth-resolution value |
| Recommended addition to the drafted paragraph | State explicitly that both studies independently identify MLCW's depth resolution as irreplaceable — a qualitative agreement, not a metric comparison, and consistent with Q6's decision to decline RMSE comparison |
| Redundancy with the existing `hung_measuring_2021` citation at line 12 | Check wording once both passages are drafted; the two citations serve different jobs but cover adjacent subject matter, and line 12's own passage carries an unresolved author note about unclear framing |
| Placement of Q5's coefficient-variation argument (line 50) | Recommend confirming it sits within the "diễn giải" stage of Q7's sequence, not as a separate late-subsection step |
| Subsection length/pacing across Q1-Q7 | Not a Q7-specific issue — flagged for a length check once the full subsection is drafted, given how many individually-approved pieces have accumulated |
