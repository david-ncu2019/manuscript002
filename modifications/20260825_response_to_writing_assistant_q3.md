# Response to the writing assistant's Q3 (reduce the diagnostic to four metrics, discuss003.tex)

## Original question from the writing assistant (verbatim, Vietnamese)

> Q2 đã được chấp thuận. Phản hồi cũng xác định đúng rằng tỷ lệ cùng dấu cần thêm hai phép kiểm tra
> mới, gồm mức mất cân bằng giữa số tháng compaction và expansion, cùng độ tin cậy của dấu khi biến
> dạng tháng nhỏ hơn độ phân giải hiệu dụng của chuỗi MLCW. Hai vấn đề này không cần thiết để trả lời
> câu hỏi chính về S5–S6.
>
> ❓ Q3 - Có giữ tỷ lệ cùng dấu hay không: Có chấp thuận thu gọn phép chẩn đoán còn bốn đại lượng
> không?
> - độ lệch chuẩn của deformation quan trắc;
> - độ lệch chuẩn của deformation ước tính;
> - tỷ lệ giữa hai độ lệch chuẩn;
> - hệ số tương quan theo thời gian giữa hai chuỗi.
>
> Tỷ lệ nhỏ hơn 1 cho biết biên độ ước tính hẹp hơn biên độ quan trắc. Hệ số tương quan thấp cho biết
> các giá trị ước tính chưa theo sát thời điểm biến dạng tăng hoặc giảm. Hai đại lượng này trả lời
> trực tiếp câu hỏi về biên độ và diễn biến theo thời gian mà không cần diễn giải dấu của những
> monthly increments gần giới hạn đo. Các định nghĩa ngắn sẽ được đặt trong appendix002.tex. Bảng sáu
> depth sections sẽ nằm trong Supplementary Materials. Results chỉ báo cáo pattern cần thiết, còn
> Discussion giải thích ý nghĩa của pattern đó.

---

**Scope:** Answers the proposal to drop the sign-agreement metric from the Q2 diagnostic and keep
only observed SD, estimated SD, their ratio, and temporal correlation. Builds on
`20260825_response_to_writing_assistant_q2.md`. No manuscript file is edited by this note.

**Verdict: approved as proposed, no further conditions attached.**

---

## Why dropping the sign-agreement metric resolves both of Q2's conditions, not just one

Conditions 1 and 2 attached to Q2's approval (baseline reporting for the compaction/expansion split;
verifying effective monthly-increment noise stays below the 1 mm MLCW measurement precision before
trusting a month's sign) existed only because the sign-agreement metric existed. Removing that metric
removes both conditions at once — there is nothing left in the four-metric design that depends on a
single month's sign being individually meaningful.

This is not a loss of information. The SD ratio and temporal correlation already answer the two
questions the sign-agreement metric was a coarser attempt to answer. Sign agreement compresses each
month's estimated and observed value down to a binary same-direction/different-direction judgment,
discarding the value's magnitude — exactly the information the correlation coefficient keeps. A
temporal correlation coefficient is sensitive to timing in the same way sign agreement is, without
requiring a value to clear the instrument's precision floor before it can be scored. The four-metric
design keeps the diagnostic's purpose (separating an amplitude problem from a timing problem) while
removing the one component that needed a noise-floor argument that could not be settled from
manuscript prose alone.

## The one condition that carries over from Q2 and still needs action

Q2's third condition — that the metrics need a stated definition location, and that the definition
must include the sentence connecting the numbers to the amplitude/timing distinction — still applies
and is only partly addressed by this proposal. Placing the short definitions in `appendix002.tex` is
the correct location, consistent with `sections.md` line 66 ("every reported analysis needs a
described method") and parallel to the existing `app:paired_mae_comparisons` subsection. What remains
unconfirmed is whether that appendix text will include the interpretive sentence itself: that a low SD
ratio paired with high correlation indicates amplitude flattening (the model tracks timing correctly
but understates magnitude), while low correlation indicates a timing problem regardless of the SD
ratio. Without that sentence written into the appendix definition, four numbers in a Supplementary
table still require the reader to work out on their own what a given combination means — the appendix
text is what turns the table into the argument `discuss003.tex` needs.

## One addition worth stating explicitly before the numbers are computed

The proposal states what an SD ratio below 1 means (estimated amplitude narrower than observed). It
does not state what a ratio above 1 would mean (estimated amplitude wider than observed, i.e., the
model overshoots the true month-to-month swings). Both outcomes are possible and neither is ruled out
in advance for S5, which has both the lowest R² (0.08) and the widest posterior predictive interval
(1.85 mm/month) of the six sections — a section with that combination could plausibly show either
pattern once the ratio is actually computed. Writing the appendix definition to cover both directions
now avoids having to revise the definition after the numbers come back, and keeps the definition
symmetric and complete rather than implicitly assuming the direction of the result.

---

## Two items still open, now flagged for direct assignment rather than a repeated general reminder

Three consecutive exchanges (Q1, Q2, Q3) have converged on a single, well-scoped, buildable diagnostic
for the S5-S6 performance question. Two separate items raised in the original review have not been
picked up by any of the three and are not addressed by this diagnostic either:

- **`results004.tex` line 50** — why the fitted coefficients vary by depth section — is a distinct
  question from the S5-S6 magnitude/timing diagnostic just approved. It needs its own
  attributed-mechanism paragraph (per Finding 3,
  `20260825_discuss003_argumentative_framework_review.md`) and has not been part of Q1, Q2, or Q3.
- **The Hung et al. (2025) citation** (Finding 2 of the same review, severity High) remains completely
  unaddressed. This is a direct requirement stated in `CLAUDE.md`'s novelty/framing guardrails, not a
  style preference open to scheduling around — the manuscript's own governing instructions name it as
  mandatory content for the Discussion (and Introduction) specifically. With the 2026-08-23 deadline
  already passed, this item should be assigned and drafted independently of the S5-S6 diagnostic work,
  rather than carried forward as a general reminder a fourth time.

---

## Summary

| Item | Verdict |
|---|---|
| Drop sign-agreement metric, keep the four-metric design | Approved, no conditions |
| Q2's conditions 1-2 (baseline, noise-floor check) | Resolved — no longer applicable once the metric they qualified is removed |
| Q2's condition 3 (definition location, `appendix002.tex`) | Still applies — confirm the interpretive sentence connecting SD ratio and correlation to amplitude versus timing is written into the appendix text, not left implicit |
| SD ratio direction | Define both directions (ratio < 1 = narrower estimated amplitude; ratio > 1 = wider) before computing, since S5's low R² and wide interval do not rule out either outcome in advance |
| `results004.tex` line 50 (coefficient variation by depth) | Still open, untouched by Q1-Q3 — needs separate assignment |
| Hung et al. (2025) citation | Still open, High severity, mandatory per `CLAUDE.md` — recommend assigning independently of the diagnostic work now that three exchanges have passed without picking it up |
