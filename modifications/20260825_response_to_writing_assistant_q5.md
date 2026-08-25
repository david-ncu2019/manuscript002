# Response to the writing assistant's Q5 (coefficient-variation-by-depth argument, discuss003.tex)

## Original question from the writing assistant (verbatim, Vietnamese)

> Q4 chấp thuận cách diễn giải hai lớp, nhưng phản hồi mới có hai suy luận cần sửa trước khi viết:
> - Khoảng phân vị 10–90% của một hệ số cắt qua 0 không phải khoảng tin cậy thống kê. Vì vậy, không
>   thể gọi hệ số cGNSS của S5 là "không khác 0 về mặt thống kê". Nó chỉ cho thấy hướng của hệ số này
>   không ổn định qua các lần cập nhật mô hình.
> - Các hệ số mùa vụ của S6 khác dấu với các section khác không giải thích được vì sao $R^2$ của S6
>   thấp. Đây là một association cần diễn giải, không phải nguyên nhân của performance thấp. Do đó,
>   không nên gán một cơ chế riêng cho S5 và một cơ chế khác cho S6 chỉ từ bảng coefficients.
>
> ❓ Q5 - Cách thảo luận coefficient thay đổi theo độ sâu: Có chấp thuận dùng bảng coefficient hiện
> có để xây dựng một argument ngắn như sau không?
>
> Mỗi depth section được ước tính bằng một mô hình riêng, nên các hệ số có thể khác nhau khi quan hệ
> giữa deformation, hydraulic head, surface displacement và mùa vụ thay đổi theo độ sâu. Đồng thời,
> nhiều biến đầu vào chứa thông tin thời gian chồng lặp. Bayesian ridge regression phân chia ảnh hưởng
> giữa các biến tương quan trong khi thu nhỏ những hệ số ít được dữ liệu hỗ trợ. Vì vậy, dấu hoặc độ
> lớn của một hệ số riêng lẻ có thể thay đổi giữa các section và giữa các lần cập nhật, ngay cả khi
> nhiều biến cùng mô tả một phần của tín hiệu. Sự khác nhau của coefficients cho thấy các fitted
> relations phụ thuộc vào độ sâu, nhưng không xác định mức đóng góp độc lập hoặc cơ chế vật lý của
> từng predictor. Phần này sẽ dùng `tab:selected_coefficients` làm bằng chứng và không cần thêm
> figure hoặc table mới. Các coefficient của S5 và S6 chỉ được dùng như ví dụ về sự khác nhau giữa
> section, không được dùng để chứng minh nguyên nhân của performance thấp.

---

**Scope:** Accepts both corrections to `20260825_response_to_writing_assistant_q4.md` and answers the
proposed coefficient-variation argument for `results004.tex` line 50. No manuscript file is edited by
this note.

**Verdict: both corrections accepted without reservation. Q5 approved as proposed, with one drafting
note about overlap with existing text.**

---

## Correction 1 accepted: "statistically indistinguishable from zero" was the wrong statistical claim for this interval

`tab:selected_coefficients`'s caption (`results004.tex` line 100) states plainly what the reported
range is: "Each cell reports the median and 10th-90th percentile range," computed by "summariz[ing]"
the coefficient "across 24 model updates." This is confirmed directly from the table caption, not
recalled from memory. The 24 values being summarized are 24 separate walk-forward refits of the same
section's model over time — the range describes how much the fitted coefficient moved from one refit
to the next, not the posterior uncertainty within a single fit. These are different statistical
objects. A credible interval crossing zero, from one posterior, licenses a statement like "this
coefficient is not well separated from zero given the model's uncertainty." A 10th-90th percentile
range of 24 point estimates crossing zero licenses a different statement: "this coefficient's sign was
not consistent across refits." The prior review's Q4 note used the first kind of language
("statistically indistinguishable from zero") to describe the second kind of quantity, which
overstates what the interval supports.

The directional observation underneath this error still holds and does not need to be withdrawn: S5's
range for "Current surface displacement increment," [-0.07, 0.03], is the only one among the six
sections that spans zero for this predictor — S1 through S4 and S6 all show ranges entirely on the
positive side (0.14-0.23, 0.44-0.57, 0.07-0.81, 0.19-0.33, 0.12-0.23 respectively). What changes is
only the label for this fact. Going forward, this should read as "S5's median coefficient for this
predictor was 0.01, and its sign varied across the 24 model updates (10th-90th percentile range
[-0.07, 0.03]), unlike every other section, where the range for this predictor stayed entirely
positive" — a claim about refit-to-refit instability, not about within-fit statistical significance.

## Correction 2 accepted: co-occurrence of a sign reversal and low R² is an association, not an explanation, and should not be used to split S5 and S6 into two separate mechanism threads

The prior Q4 note treated S6's reversed seasonal coefficients (dry-season indicator, annual sine,
annual cosine all opposite in sign from S1-S5) as a plausible thread explaining why S6's R² is low
(0.34). This does not follow from the coefficient table alone. A reversed or unusually large seasonal
coefficient is not inherently associated with worse model fit — S2 has one of the largest-magnitude
seasonal coefficients in the table (annual sine -0.54) and the best R² of all six sections (0.98). So
large or unusual seasonal-coefficient values do not track with poor fit in general; S6 having both a
sign reversal and a low R² could be coincidence, could share an unmeasured upstream cause, or could be
connected in a way this single-section, single-table comparison cannot distinguish. Proposing "Layer 1
(cGNSS integration) explains S5; the seasonal-sign-reversal explains S6" builds two separate causal
narratives from one coefficient table and one section each — a post-hoc explanation fitted to a single
data point per thread, which is exactly the kind of unverified mechanism claim `style.md` line 103
("Mark explanations of unexpected patterns as interpretations... must not be presented as... a
demonstrated mechanism") warns against. The corrected framing keeps S6's seasonal-sign reversal as an
observation worth stating on its own terms — matching what `results004.tex` line 50 already asks for
— without asserting it accounts for S6's R².

What remains valid from the prior note, under this correction: the caution that Layer 1 (cGNSS
integration) is not equally well-supported for S5 and S6 stays correct, because it rests on comparing
each section's own surface-displacement coefficient (S5's sign-unstable, S6's stably positive at
0.18), not on linking S6's performance to any specific alternative mechanism. Recommend the Discussion
state only that Layer 1's supporting coefficient evidence is specific to S5, without proposing what
(if anything) explains S6's separate underperformance — leaving that, honestly, as unresolved rather
than filled with an under-supported seasonal-sign narrative.

---

## Answering Q5: the proposed coefficient-variation argument

**Approved.** The argument is well-scoped for three reasons.

First, it answers `results004.tex` line 50 directly, using only structural facts already established
in Methods: each depth section is fit as a separate model (`methods006.tex`), so the true relationship
between deformation and its predictors is permitted to differ by depth without requiring any new
physical claim — this is a fact about the modeling design, not a proposed mechanism, and needs no
`[AUTHOR CONFIRMATION REQUIRED]` tag on that basis.

Second, it stays at a safer evidentiary level than the physical candidates in Q1/Q4's Layer 2. Ridge
shrinkage under correlated predictors is a well-established statistical property, already cited with
support in the manuscript (`discuss003.tex` line 13: "coefficient shrinkage limits changes in
coefficients with limited observational support and helps stabilize estimation," citing Dormann et
al. 2013, Hastie et al. 2009, MacKay 1992). Q5 extends this same, already-approved statistical
machinery to explain depth-dependence specifically, rather than introducing a new physical claim about
sediment or hydraulic properties.

Third, it correctly keeps two separate questions separate: why coefficients vary by depth (a
statistical/design fact, line 50) versus why R² is low in specific sections (a performance question,
line 44, addressed by the Q1-Q4 diagnostic and physical-interpretation work). Explicitly restricting
S5/S6 coefficients to illustrative use only, not as proof of a performance cause, is exactly the
guardrail Correction 2 above requires, and Q5 states this guardrail itself before this review had to
ask for it.

## One drafting note: check for overlap with the existing shrinkage passage before drafting

`discuss003.tex` line 13 already states the shrinkage mechanism, cites its statistical support, and
already ends with "Coefficient signs and magnitudes nevertheless describe statistical associations in
the Tuku record rather than physical causes" — close in substance to Q5's closing point ("sự khác nhau
của coefficients cho thấy các fitted relations phụ thuộc vào độ sâu, nhưng không xác định mức đóng góp
độc lập hoặc cơ chế vật lý"). Q5's genuinely new content is narrower than the whole proposed argument:
specifically, the separate-model-per-section framing that connects shrinkage to the line-50 question
about depth-dependence. Recommend drafting this as an extension of the existing line 13 passage — for
instance, opening line 13's paragraph with the separate-model-per-section point before its current
shrinkage sentence — rather than as a new, separate paragraph placed nearby, which risks restating the
same shrinkage-and-association-not-cause conclusion twice in close proximity.

---

## Items still open, unchanged

- **Hung et al. (2025) citation** (Finding 2 of the original review, severity High, mandatory per
  `CLAUDE.md`) — unaddressed across five consecutive exchanges (Q1-Q5), all of which have focused on
  `subsec:discussion_layerwise_estimation`. This item sits in a different part of the Discussion
  (concordance with prior work) and will not be resolved by continuing to refine this subsection;
  recommend it be assigned as an independent task now.
- **S6's own performance question** (why R² = 0.34 despite a normal cGNSS coefficient) is now
  correctly left open rather than answered with an under-supported seasonal-sign narrative. This is
  the honest state of the evidence, not a gap to close before submission — `discuss003.tex`'s existing
  guardrail language (line 16: "does not identify a physical mechanism") already covers leaving this
  unresolved.

---

## Summary

| Item | Verdict |
|---|---|
| Correction 1 (percentile range ≠ confidence interval; "not statistically different from zero" was wrong) | Accepted. Corrected description: S5's coefficient sign varied across the 24 model updates, unlike every other section for this predictor — a refit-to-refit instability claim, not a within-fit significance claim |
| Correction 2 (S6's seasonal sign reversal is an association, not an explanation for low R²; no separate S5/S6 mechanism split from the coefficient table alone) | Accepted. S6's low R² remains unexplained; do not attribute it to the seasonal-sign reversal without independent support |
| Q5's coefficient-variation argument for line 50 | Approved — uses only existing evidence (`tab:selected_coefficients`), extends already-cited shrinkage machinery, correctly separates the depth-dependence question from the S5/S6 performance question, and explicitly restricts S5/S6 coefficients to illustrative use |
| Drafting note | Check for overlap with `discuss003.tex` line 13's existing shrinkage/association-not-cause sentence; consider extending that passage rather than adding a new adjacent one |
| Hung et al. (2025) citation | Still open, High severity, unaddressed across five exchanges — recommend independent assignment |
