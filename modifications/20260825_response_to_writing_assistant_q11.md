# Response to the writing assistant's Q11 (seven-paragraph outline for the whole of Subsection 5.1)

## Original question from the writing assistant (verbatim, Vietnamese)

> Q10 được chấp nhận. Hai citation sẽ giữ vai trò riêng và không lặp lại nhau. Q11: Có đồng ý chốt
> Subsection 5.1 theo outline bảy đoạn sau không?
>
> 1. Đặt vấn đề theo độ sâu. Giải thích cGNSS phản ánh chuyển dịch tổng hợp tại bề mặt, còn MLCW
>    phân tách biến dạng theo từng khoảng độ sâu. Sự khác biệt này dẫn trực tiếp đến câu hỏi vì sao
>    cùng một bộ quan trắc liên tục lại hỗ trợ S1–S4 tốt hơn S5–S6. Trích dẫn hung_measuring_2021.
> 2. Nêu pattern chính, không lặp lại toàn bộ Results. Trình bày ngắn gọn rằng S1–S4 có kết quả tốt
>    hơn. Với S5 và S6, dùng cấu trúc respectively để khai báo rõ từng giá trị. RMSE chỉ cần nói
>    rằng nó cho thấy cùng pattern, không cần lặp thêm toàn bộ số liệu.
> 3. Phân tích hành vi toán học của estimates. Sử dụng observed SD, estimated SD, tỷ số giữa hai SD
>    và temporal correlation để phân biệt hai vấn đề: estimates có tái hiện được biên độ biến đổi
>    quan sát hay không, và có thay đổi đồng thời với observations hay không. Chỉ viết claim sau khi
>    các giá trị đã được tính từ frozen Section 4.1 predictions.
> 4. Diễn giải vì sao quan hệ thay đổi theo độ sâu. Kết nối tính chất tổng hợp của cGNSS với sự khác
>    nhau giữa các section. Lồng phần coefficient vào đây để giải thích rằng mỗi section có một
>    fitted relation riêng, các predictors chia sẻ thông tin và Bayesian ridge regression điều
>    chỉnh coefficients để ổn định estimates. Không dùng coefficient để tuyên bố nguyên nhân vật lý.
>    Lithology và mức độ đại diện của hydraulic head chỉ cung cấp bối cảnh diễn giải.
> 5. Giải thích uncertainty. Phân biệt point error với posterior predictive coverage. Giải thích vì
>    sao S5 có coverage cao hơn S6 dù point error lớn hơn, dựa trên interval width. Đoạn này chỉ
>    giải thích quan hệ thống kê, không gán cơ chế vật lý.
> 6. Giải thích pattern theo vị trí tháng. Sai số không tăng đều qua các tháng vì mỗi monthly
>    estimate sử dụng quan trắc cùng tháng và không lấy estimate của tháng trước làm predictor. Vì
>    vậy, point error không được truyền đệ quy từ tháng này sang tháng kế tiếp.
> 7. Đặt kết quả trong prior work và kết thúc bằng đóng góp. Dùng đoạn Hung et al. (2025) đã duyệt
>    ở Q9 để phân biệt hai câu hỏi nghiên cứu tại cùng TKJS site. Sau đó kết thúc bằng thông điệp
>    rằng các quan trắc liên tục có thể hỗ trợ monthly layerwise estimation giữa những lần cập nhật
>    MLCW, còn MLCW cung cấp phép đo trực tiếp để phân giải và đánh giá biến dạng theo chiều sâu.
>
> Observed/estimated SD và temporal correlation sẽ được định nghĩa trong Appendix, bảng sáu
> sections sẽ nằm trong Supplementary Materials, còn Results chỉ thêm một câu mô tả pattern. Toàn bộ
> `% my note : ... %` hiện có sẽ được giữ nguyên. Tôi đề xuất đồng ý với outline này trước khi soạn
> bản thiết kế thực thi.

---

**Scope:** Answers the proposed seven-paragraph outline for the complete
`subsec:discussion_layerwise_estimation`, checked against every decision approved across Q1-Q10 and
against every author `% NOTE %`/`% my note %` in `results004.tex` tied to that Results subsection. No
manuscript file is edited by this note.

**Verdict: approved.** The outline is a coherent, complete synthesis of ten prior exchanges, correctly
answers every author note tied to this specific subsection's scope, and correctly resolves the
original review's central concern (Finding 1) at the subsection level. Three drafting-stage notes are
offered, none blocking, plus one scope observation about what remains for later.

---

## Paragraph-by-paragraph consistency check against Q1-Q10

**Paragraph 1** matches Q10's approved opening exactly — the cGNSS-integrated/MLCW-depth-specific
contrast, attributed to `hung_measuring_2021`, already verified against that paper's own Introduction
in the Q10 response.

**Paragraph 2** is new, targeted content not previously discussed in Q1-Q10, and directly resolves two
specific author confusions already on record in `results004.tex`: the `% my note %` at line 9
("respectively... không cần dùng cấu trúc 'from ... to ...'") and the `% my note %` at line 10
("corresponding ranges này là sao?... làm tui không hiểu ngay khi lần đầu đọc qua"). Instructing the
drafted paragraph to use "respectively" for the two-value S5/S6 comparisons and to state only that
RMSE shows the same pattern (without repeating the full range) answers both notes directly.

**Paragraph 3** matches the four-metric diagnostic finalized in Q3 (observed SD, estimated SD, their
ratio, temporal correlation — the sign-agreement metric dropped, per Q3's approval) and correctly
restates the "no retraining, read-only against frozen Section 4.1 predictions" constraint from Q2,
now extended into a drafting discipline: claims are written only after the values exist, not drafted
in advance of computing them.

**Paragraph 4** consolidates the Q5-approved coefficient-variation-by-depth argument (answering
`results004.tex` line 50) with the general form of the physical-interpretation content from Q1/Q4,
correctly downgraded per the corrections accepted in Q4 and Q5: no claim that coefficient
instability equals statistical insignificance, no attribution of S6's performance to its reversed
seasonal coefficients, and lithology/hydraulic-head-representativeness kept explicitly as
interpretive context only, not causal claims. This is a legitimate compression, not a loss of content
— Q8's own preamble already signaled the subsection would be shortened to avoid becoming "a collection
of disconnected points," and folding the coefficient argument into the same paragraph as the general
depth-dependence interpretation is a reasonable way to do that.

**Paragraph 5** and **Paragraph 6** both match content already present in the current
`discuss003.tex` draft (lines 16 and 19-20, both read directly earlier in this review) and never
challenged or revised across Q1-Q10. Paragraph 6 in particular matches the author's own already-approved
AUTHOR NOTE at `results004.tex` line 48 nearly verbatim. These two paragraphs are confirmed as
carried forward, not rewritten.

**Paragraph 7** matches the Q9-approved Hung et al. (2025) paragraph, referenced by name, followed by
the Q1 Step 4 positive-contribution closing already established. This placement (Hung et al. paragraph
immediately before the closing) matches the ordering approved in Q7, with the reasoning already given
there for why this order is the stronger choice.

## Why this outline resolves the original review's Finding 1, rather than repeating it

The very first review of `discuss003.tex` (Finding 1) observed that all of the subsection's paragraphs
ended on a negative or hedged clause, leaving no single paragraph the reader could cite as a positive
conclusion. Under this seven-paragraph plan, individual paragraphs still end on appropriately scoped
caveats where the evidence genuinely supports nothing stronger (Paragraph 4's "not a physical cause"
qualifier, Paragraph 5's "statistical relationship only" qualifier) — this is correct, local limitation
placement, not a repeat of the original problem. What resolves Finding 1 is that the subsection's
actual last paragraph, Paragraph 7, ends affirmatively: continuous observations supporting monthly
estimation between MLCW updates, and MLCW providing the direct measurement basis for resolving and
evaluating deformation. The subsection now has exactly one, clearly positioned, citable positive
conclusion at its close, while individual mid-subsection caveats remain correctly scoped to the
specific claims they qualify — matching `sections.md`'s local-limitation rule (lines 106, 129) without
reintroducing the all-paragraphs-end-negatively pattern Finding 1 originally flagged.

## Three drafting-stage notes, none blocking

1. **Paragraph 4 should still name S5's specific coefficient as an illustrative example, not remain
   purely abstract.** Q5 explicitly approved using "S5 and S6 coefficients only as an example of
   cross-section variation, not as proof of a performance cause" — this permission was never revoked,
   only conditioned on not overclaiming causally. The outline's description of Paragraph 4 is written
   at a fully general level (no section named), which is fine as an outline summary, but the drafted
   paragraph should still return concretely to the S5 coefficient example (with the Q5-corrected
   wording: "the coefficient's sign varied across the 24 model updates," not "statistically
   indistinguishable from zero") so Paragraph 4 actually closes the loop Paragraph 1 and 2 opened,
   rather than staying at a purely general statistical level.

2. **The optional Hung et al. corroboration point from the Q7 response remains available, not
   required.** The Q7 response recommended, as an optional strengthening, stating explicitly that
   Hung et al.'s own Table 3/Conclusions independently agree with this manuscript's closing claim
   about MLCW's irreplaceable-but-not-absolute depth-resolution value. This was never made a
   condition of approval in Q7 or Q9, and Q11's outline does not need to add it now — flagged here
   only so it is not mistaken for a dropped requirement.

3. **Confirm `appendix002.tex` will include the interpretive sentence connecting the four metrics to
   the amplitude-versus-timing distinction**, per the condition carried from Q2 through Q3: a low SD
   ratio paired with preserved correlation indicates amplitude flattening, while low correlation
   indicates a timing problem regardless of the SD ratio; and the SD-ratio definition should cover
   both directions (ratio below 1 and above 1), since S5's own outcome was not knowable in advance of
   computing it.

## One scope observation: Subsection 5.2 has its own unanswered author notes, entirely untouched across eleven exchanges

Checking every author `% NOTE %` in `results004.tex` against Q11's seven paragraphs confirms complete
coverage of everything tied to `subsec:results_delayed_delivery` (the Results subsection this
Discussion subsection answers): the coefficient-variation note (line 50) is Paragraph 4; the
coverage/width note (lines 41-44) is Paragraph 5; the month-position note (lines 47-48) is Paragraph 6.
Nothing from that scope is missing.

Three separate author notes belong to a different Results subsection and a different Discussion
subsection entirely, and remain fully open: `results004.tex` line 136 (why more initial-record history
does not lower monthly error), line 173 (whether a twelve-month schedule's first six months
accumulate more or less error than a complete six-month schedule), and lines 175-176 (whether
coverage below 90% is "good or bad," and what the width-versus-initial-record-length relationship
means). These belong to `subsec:discussion_reduced_mlcw_information` (Discussion §5.2), not
Subsection 5.1, and have not been addressed in any of the eleven exchanges so far, which have focused
entirely on §5.1. This is not a gap in Q11 — it is correctly out of scope for this outline — but it is
the clear, well-defined next body of work once Subsection 5.1's draft is finalized.

---

## Summary

| Item | Verdict |
|---|---|
| Seven-paragraph outline overall | Approved — coherent synthesis of Q1-Q10, framework-consistent paragraph sequence, no gaps against the author notes tied to this subsection's scope |
| Paragraph 1 (opening, Hung 2021) | Matches Q10 exactly |
| Paragraph 2 ("respectively," simplified RMSE mention) | New, directly resolves two previously-unaddressed author notes (`results004.tex` lines 9-10) |
| Paragraph 3 (four-metric diagnostic) | Matches Q3's final approved design |
| Paragraph 4 (coefficient variation + general physical context) | Matches Q5's corrected, conservative framing; consolidation is consistent with Q8's stated shortening intent |
| Paragraphs 5-6 (uncertainty, month-position) | Confirmed as existing, already-correct content carried forward unchanged |
| Paragraph 7 (Hung 2025 + closing) | Matches Q9's approved paragraph and Q7's approved ordering |
| Resolution of original Finding 1 | Achieved at the subsection level — one clear affirmative closing paragraph, appropriately scoped local caveats elsewhere |
| Drafting-stage note 1 | Paragraph 4 should still name S5's coefficient concretely, using Q5-corrected wording, not stay fully abstract |
| Drafting-stage note 2 | Q7's optional Hung et al. corroboration point remains available, not required |
| Drafting-stage note 3 | Confirm the amplitude-vs-timing interpretive sentence and both-direction SD-ratio definition land in `appendix002.tex` |
| Subsection 5.2's own unanswered author notes | Entirely untouched across all eleven exchanges (`results004.tex` lines 136, 173, 175-176) — the clear next scope once 5.1 is finalized |
