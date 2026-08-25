# Response to the writing assistant's Q1 (discuss003.tex, subsec:discussion_layerwise_estimation)

## Original question from the writing assistant (verbatim, Vietnamese)

> Tôi đồng ý với nhận xét của bạn. discuss003.tex hiện chủ yếu nhắc lại các con số trong Results rồi
> kết thúc bằng caveat. Nó chưa tạo được chuỗi lập luận pattern → câu hỏi tại sao → giải thích toán
> học → diễn giải vật lý → ý nghĩa. Các giải thích về shrinkage, cách ước tính không đệ quy, và sự
> cộng hoặc triệt tiêu của sai số có dấu đã có bằng chứng. Ngược lại, nguyên nhân vật lý của kết quả
> S5–S6 chưa được kiểm chứng và chỉ có thể trình bày như những cách giải thích có thể xảy ra, được hỗ
> trợ bằng dữ liệu quan trắc và tài liệu khoa học. Bản nhận xét của người bạn nhìn chung hợp lý, nhưng
> đề xuất rải limitations vào từng đoạn xung đột với quyết định trước đây của bạn, nên limitations vẫn
> sẽ được gom vào subsection riêng. Không có file nào được sửa trong lượt kiểm tra này, và toàn bộ
> `% my note : ... %` sẽ được giữ nguyên.
>
> ❓ Q1 - Câu chuyện trung tâm của Subsection 5.1: Có chấp thuận để phần này đi theo chuỗi lập luận sau
> không?
>
> 1. Kết quả S1–S4 và S5–S6 tạo ra một câu hỏi khoa học về lý do khả năng ước tính thay đổi theo độ
>    sâu, thay vì chỉ được lặp lại như hai nhóm số liệu.
> 2. Phân tích toán học sẽ kiểm tra liệu các ước tính tại S5–S6 có bị thu hẹp biên độ và theo biến
>    động quan trắc kém hơn hay không. Các chỉ số chẩn đoán chính sẽ được đặt trong một bảng hoặc
>    figure nhỏ ở Supplementary Materials, còn Discussion chỉ diễn giải pattern.
> 3. Phần diễn giải vật lý sẽ xem xét ba yếu tố có thể liên quan, gồm cGNSS đo phản ứng tổng hợp của
>    toàn profile, hydraulic head tại một độ sâu có thể không đại diện hoàn toàn cho áp lực nước lỗ
>    rỗng trong các lớp đang biến dạng, và thành phần địa chất có thể làm phản ứng khác nhau theo độ
>    sâu. Những yếu tố này sẽ được trình bày như các giải thích có cơ sở, không phải nguyên nhân đã
>    được chứng minh.
> 4. Đoạn kết sẽ quay về contribution tích cực. Các quan trắc liên tục có thể hỗ trợ ước tính theo
>    từng đoạn độ sâu, nhưng MLCW vẫn cung cấp khả năng phân giải theo độ sâu cần thiết để nhận ra nơi
>    tín hiệu tổng hợp không còn đại diện đầy đủ.

---

**Scope:** Answers the four-step argumentative sequence proposed for `subsec:discussion_layerwise_estimation`
(`discuss003.tex` lines 4-21) in the writing assistant's question, and corrects two errors in the
prior review (`20260825_discuss003_argumentative_framework_review.md`) that the assistant's question
exposed. No manuscript file is edited by this note. Every `% my note : ... %` and `% NOTE: ... %`
marker in `discuss003.tex` stays untouched.

---

## Two corrections to the prior review, made before answering Q1

### Correction A: the "13/13 negative endings" count in Finding 1 was wrong

The prior review counted fourteen paragraphs (lines 4, 10, 13, 16, 19, 25, 28, 31, 34, 37, 43, 46,
49, 52) but wrote "thirteen out of thirteen." The correct count is 14 paragraphs. More important than
the arithmetic: **line 52, the paragraph that closes the entire Discussion section, does not end on a
negative claim.** Its final sentence is affirmative: "The bounded contribution is a common evidence
base for evaluating monthly and accumulated estimation performance as MLCW information decreases at a
well-instrumented site." The negative clause in that paragraph ("without defining an acceptable
operational error threshold...") sits mid-paragraph, not at the end.

The corrected finding: **13 of 14 paragraphs end on a negative claim; the single exception is the
paragraph that closes the section.** This is a narrower claim than the original review stated, but it
does not change the recommendation. A Discussion whose only affirmative closing sentence appears once,
in the very last paragraph, still leaves the reader with no positive anchor inside the two subsections
that do the section's main interpretive work (`subsec:discussion_layerwise_estimation` and
`subsec:discussion_reduced_mlcw_information`). The fix scope narrows to those two subsections; the
final paragraph (line 52) is already doing what Finding 1 originally asked for and needs no change.

### Correction B: the well-screen explanation for S5 in the earlier discuss002.tex draft does not survive a check against the manuscript's own coefficient table

Finding 3 of the prior review flagged, as a candidate worth the author's attention, a sentence present
in the superseded `discuss002.tex` but absent from `discuss003.tex`: that S5's near-zero R² is
"consistent with the absence of a piezometric observation well screened within the compacting
fine-grained deposits at that depth." Checking this against `methods006.tex` line 34 and
`tab:tuku_data_sources` (`dataset003.tex` line 150) shows why it cannot be used as written.

The three Tuku wells are screened at 81-84 m, 176-179 m, and 257-263 m. Mapped onto the six 50 m
sections (S1: 0-50 m, S2: 50-100 m, S3: 100-150 m, S4: 150-200 m, S5: 200-250 m, S6: 250-300 m), only
S2, S4, and S6 contain a screened well. **S1, S3, and S5 all rely on kriged, not directly measured,
hydraulic head** (`methods006.tex` line 34: "For the remaining sections, hydraulic head at Tuku was
instead estimated from the regional monitoring network using ordinary kriging"). Their reported R²
values are 0.89 (S1), 0.87 (S3), and 0.08 (S5) — two of the three kriged sections perform as well as
any section in the study, while the third performs the worst. S6, which does have a directly screened
well, has the second-lowest R² (0.34). Whether a section's head predictor is measured directly or
kriged does not track its estimation performance in either direction.

This means the well-screen sentence cannot be restored in its `discuss002.tex` form: a reviewer
familiar with `Cref{tab:tuku_data_sources}` would immediately ask why S1 and S3, also kriged, do not
show the same degradation. **Recommendation: do not reintroduce this sentence as a standalone
explanation.** If the author wants to keep kriged-versus-screened head as one candidate factor, it can
only appear paired with an explicit statement addressing the S1/S3 counterexample — for instance,
noting that kriging quality itself may vary by location relative to the regional network, which is a
separate, currently untested claim requiring the same `[AUTHOR CONFIRMATION REQUIRED]` treatment as
any new mechanism. Otherwise, drop the well-screen factor from the candidate list for S5/S6 entirely.

---

## Answering Q1: the four-step sequence for subsec:discussion_layerwise_estimation

### Step 1 (S1-S4 vs. S5-S6 as a stated scientific question) — approved as written

Framing the depth-dependent performance split as a question to be investigated, rather than two
number groups restated from Results, is exactly the lead-development structure the project's writing
rules require (`sections.md` line 101: "Explain what the results mean before broadening to prior work
or wider implications"; `style.md` line 66: "State the main point or observed pattern early... Develop
it with evidence, explanation, qualification, or detail"). It also directly answers the question the
author raised in `results004.tex` line 44 and repeated as an unmet requirement in `discuss003.tex`
line 23's `% my note`. No open issue.

### Step 2 (mathematical check: did S5-S6 estimates shrink toward the mean and undertrack variability?) — approved, with one scope check before adding new material

The proposed diagnostic is sound and answers a mathematical question with mathematical evidence, kept
separate from physical interpretation — the correct order per `sections.md` line 125 ("Present enough
evidence before interpretation"). Before creating a new Supplementary figure or table, check whether
`tab:selected_coefficients` and `tab:delayed_performance_interval`, both already in the manuscript,
already establish the shrinkage pattern the diagnostic is meant to show. S5's "Current surface
displacement increment" coefficient is 0.01 with a 10th-90th percentile range of [-0.07, 0.03] —
statistically indistinguishable from zero — versus 0.21, 0.52, 0.48, and 0.24 for S1-S4. S5's R² is
0.08 and its posterior predictive interval width is 1.85 mm/month, the widest of all six sections.
Together these three already-reported numbers describe a model that could not find a usable
relationship for S5 and compensated with wide, low-informative intervals — which is the shrinkage-and-
undertracking pattern Step 2 asks to test. If a new diagnostic would only reproduce this same
conclusion in a different display, it is worth confirming with the author that the existing tables
do not already close Step 2, given the 2026-08-23 deadline has passed and every added display carries
review and layout cost. If Step 2 is intended to test something the existing coefficients do not show
(for instance, a formal shrinkage-toward-the-mean statistic rather than a wide-interval symptom), that
distinction should be stated explicitly before drafting the new figure.

### Step 3 (three physical candidates: cGNSS integration, hydraulic head representativeness, geological composition) — approved in principle, conditional on removing or fixing the well-screen sub-claim

Two of the three candidates are sound as stated and already have support elsewhere in the manuscript:
cGNSS integrating the full profile's response is stated directly in `dataset003.tex` line 18 and
already appears in `discuss003.tex` line 46 ("cGNSS represents vertical deformation integrated over
the underlying aquifer system, including deformation below the approximately 300 m MLCW monitored
depth"); it can be extended into Step 1's finding without introducing new scientific content, since it
is manuscript-grounded per `style.md` line 112. Lithological composition varying by depth is
established in the study area description and is a legitimate attributed-mechanism candidate provided
it stays hedged as a possible contributor, consistent with `discuss003.tex` line 47's existing
statement that lithology "provides context for interpreting the depth sections but was not a model
input."

The third candidate — hydraulic head at one depth not fully representing pore pressure in the
compacting layers — is the generalized, section-agnostic form of the well-screen sentence addressed in
Correction B above. Stated generally (measurement depth versus compaction depth, without singling out
S5's specific screen gap), it survives the S1/S3 counterexample, because it is a statement about a
structural limitation of point head measurements in general, not a claim that explains why S5
specifically underperforms while S1 and S3 do not. If the paragraph is drafted to name this factor as
a general limitation of the predictor design, that is consistent with the existing evidence. If it is
drafted to explain why S5 specifically is the worst-performing section, it needs the S1/S3 rival-
hypothesis check described in Correction B before it can be defended, following the framework's C1
pattern (rival-hypothesis elimination) referenced in the prior review. Recommend the author decide
which of these two forms is intended before the paragraph is drafted.

All three candidates should carry the attributed, hedged framing the writing assistant already
proposes ("presented as grounded explanations, not demonstrated causes") — this matches
`sections.md` line 103 exactly: "Mark explanations of unexpected patterns as interpretations. A
plausible explanation may be useful, but it must not be presented as an observation or a demonstrated
mechanism."

### Step 4 (closing paragraph returns to the positive contribution) — approved, and this is the correct fix for Finding 1's Correction A

This step directly implements what Finding 1 of the prior review was asking for, scoped correctly to
this subsection. Ending on "continuous observations can support depth-section estimation, but MLCW
still provides the depth resolution needed to see where an aggregate signal no longer represents the
profile" gives the reader the positive statement Finding 1 found missing from lines 4-21, without
touching `subsec:discussion_limitations` (`§5.3`) or moving any limitation out of its current location.

---

## On the limitations-placement disagreement: the writing assistant is right, and the prior review should not have implied otherwise

The prior review's Finding 1 cited pattern A4a (local limitation placement, observed in 14 of 15
NHESS papers) approvingly, which reads as endorsing caveats scattered through
`subsec:discussion_layerwise_estimation` and `subsec:discussion_reduced_mlcw_information` rather than
gathered in `subsec:discussion_limitations`. That reading is fair, and the underlying project rule
settles it against the framework document. `.claude/skills/david-writing-styles/rules/sections.md`
states directly, twice (lines 106 and 129): "Place limitations in a dedicated subsection. Do not
scatter them through result-analysis paragraphs." Under this project's own authority hierarchy
(`style.md` lines 5-11), explicit project writing rules rank above the 15-paper framework document,
which is planning material, not a rule file. `subsec:discussion_limitations` (`§5.3`) stays exactly
where it is, with exactly the content it already has.

What Finding 1 actually asked for, and what Q1's Step 4 correctly delivers, is narrower than "add or
relocate limitations": **reorder existing sentences within already-caveated paragraphs so the
paragraph's positive finding leads and the existing caveat follows**, not moving any caveat out of its
current paragraph or into `§5.3`, and not adding any new caveat anywhere. No paragraph gains or loses
a limitation under this fix; only the internal sentence order changes in `subsec:discussion_layerwise_estimation`
and `subsec:discussion_reduced_mlcw_information`.

---

## Summary

| Item | Verdict |
|---|---|
| Q1 Step 1 (frame S1-S4 vs. S5-S6 as a question) | Approved as written |
| Q1 Step 2 (mathematical shrinkage/variability check) | Approved; confirm with author whether `tab:selected_coefficients` + `tab:delayed_performance_interval` already establish this before adding a new Supplementary display |
| Q1 Step 3 (three physical candidates) | Approved for cGNSS-integration and lithology candidates; hydraulic-head-representativeness candidate must be stated as a general limitation, not as an S5-specific explanation, unless paired with the S1/S3 counterexample |
| Q1 Step 4 (positive closing) | Approved; this is the correct, correctly-scoped fix for the prior review's Finding 1 |
| Limitations placement | Writing assistant is correct: `§5.3` stays as the single dedicated subsection, per `sections.md` lines 106 and 129. Prior review's Finding 1 is corrected to mean sentence-order-within-paragraph, not caveat relocation |
| Prior review Finding 1 count | Corrected from "13/13" to "13/14"; line 52 (the section's closing paragraph) already ends affirmatively and needs no change |
| Prior review Finding 3's well-screen candidate | The `discuss002.tex`-era explanation for S5 fails against S1/S3 (also kriged, R²=0.89/0.87). Do not restore it unmodified; restate as a general predictor-design limitation or pair with the counterexample |
