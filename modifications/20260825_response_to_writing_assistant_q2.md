# Response to the writing assistant's Q2 (mathematical diagnostic for S5-S6, discuss003.tex)

## Original question from the writing assistant (verbatim, Vietnamese)

> Phản hồi này chấp thuận khung Q1, đồng thời sửa đúng hai điểm: không thể dùng việc thiếu giếng
> screened tại S5 làm nguyên nhân riêng vì S1 và S3 cũng dùng hydraulic head nội suy nhưng đạt kết
> quả tốt; và hạn chế vẫn phải nằm trong subsection riêng. Tuy nhiên, nhận định rằng hệ số của một
> biến gần 0 cùng khoảng dự báo rộng đã chứng minh mô hình làm phẳng S5 là chưa đủ chặt chẽ. Hai đại
> lượng đó không trực tiếp đo mức co hẹp biên độ hoặc khả năng theo đúng chiều biến dạng.
>
> ❓ Q2 - Bằng chứng toán học cho S5–S6: Có chấp thuận thực hiện một phép chẩn đoán chỉ đọc kết quả
> Section 4.1 đã cố định, không huấn luyện lại mô hình, rồi tạo một bảng nhỏ trong Supplementary
> Materials gồm:
> - độ biến thiên của giá trị quan trắc;
> - độ biến thiên của giá trị ước tính;
> - tỷ lệ giữa hai độ biến thiên;
> - mức đồng biến giữa hai chuỗi theo thời gian;
> - tỷ lệ số tháng mà ước tính và quan trắc cùng biểu thị compaction hoặc cùng biểu thị expansion.
>
> Results chỉ cần một câu báo cáo pattern chính. Discussion sẽ dùng bảng này để phân biệt hai dạng
> sai lệch, gồm ước tính chưa tái hiện đủ biên độ và chưa theo đúng diễn biến theo thời gian. Bảng hệ
> số hiện tại vẫn được dùng để mô tả quan hệ đã học, nhưng không được dùng làm bằng chứng trực tiếp
> cho hai dạng sai lệch trên.

---

**Scope:** Answers the proposed post-hoc diagnostic (read-only against frozen Section 4.1 results, no
retraining) for `subsec:discussion_layerwise_estimation`. Builds on
`20260825_response_to_writing_assistant_q1.md`, which already conceded the writing assistant's point
that coefficient magnitude and interval width alone do not directly measure amplitude shrinkage or
timing agreement — Q2 replaces that weaker argument with a proper diagnostic. No manuscript file is
edited by this note.

**Verdict: approved, with three conditions attached to specific metrics before they enter the
Supplementary table.**

---

## Why this design is correct

The four-metric-plus-one design (observed SD, estimated SD, their ratio, temporal correlation, and a
sign-agreement rate) separates two failure modes that a single scalar like R² collapses into one
number. R² (as $1 - SS_{res}/SS_{tot}$) mixes phase error, amplitude error, and bias into one score.
The proposed SD-ratio isolates amplitude — whether the model's month-to-month swings are as large as
the observed swings — and the temporal-correlation term isolates phase — whether the model moves up
and down at the right times, independent of whether it moves by the right amount. A section with high
correlation but a low SD ratio has a phase-correct, amplitude-flattened problem; a section with both
low has a timing problem. This is the distinction `discuss003.tex` line 16 already gestures toward
("coverage and width must be interpreted together") without the tool to state it precisely for
amplitude versus timing specifically. Computing all of this by reading `predictions.parquet` — which
already holds every fold's predictions from the frozen Section 4.1 run — satisfies the no-retraining
constraint cleanly; there is no leakage risk in taking summary statistics of an already-frozen output.

---

## Condition 1: the sign-agreement metric needs a stated baseline before it can be interpreted

A raw percentage of months where estimated and observed increments carry the same sign is not
readable on its own. If the observed monthly series for a section is, say, 80% compaction months and
20% expansion months, a model that always predicts compaction would score 80% sign agreement while
having learned nothing about the section's actual timing. At an actively subsiding site like Tuku,
this kind of imbalance between compaction and expansion months is plausible and should be checked, not
assumed away. **The Supplementary table must report the observed compaction-month proportion for each
section alongside the sign-agreement rate**, or use a chance-corrected version of the statistic (for
example, comparing the observed rate against what a majority-class predictor would achieve). Without
this, a high sign-agreement number for one section and a low one for another cannot be compared
against each other or interpreted as evidence of anything.

## Condition 2: verify the sign-agreement metric is not measuring noise below the record's resolution before using it

`dataset003.tex` line 10 states MLCW measurement precision is 1 mm. The reported monthly errors are
smaller than that: MAE ranges 0.15-0.50 mm/month and RMSE ranges 0.21-0.66 mm/month across the six
sections (`tab:delayed_performance_interval`). If a given month's true observed increment is itself
smaller in magnitude than the instrument's stated precision, that month's sign is not a reliable signal
to compare against — the diagnostic would be scoring how well the model reproduces measurement noise,
not the deformation pattern.

This concern is partly addressed by the fact that the monthly MLCW increments used throughout the
manuscript are differences of a fitted deformation time series model (linear, periodic, and step
components, `subsec:deformation_model`), not raw ring-to-ring differences — model fitting can reduce
effective noise below the raw 1 mm figure, but the manuscript does not report what that residual noise
level actually is after fitting. This is a question about the underlying pipeline's fit residuals, not
something answerable from the manuscript text alone. **Before the sign-agreement metric is computed
and reported, confirm from the deformation-model fitting output (not from the manuscript prose)
whether the effective monthly-increment noise is small enough, relative to typical observed increment
magnitudes, for a month's sign to be a meaningful comparison.** If it is not confirmable, either
exclude months where the observed increment magnitude falls below a stated noise threshold from the
sign-agreement calculation, with that threshold stated in the table's defining text, or drop the
sign-agreement metric and report only the first four (SD ratio and correlation already carry the
amplitude/timing distinction Q2 is built to establish).

## Condition 3: the five new quantities need a definition location before they can be cited from Results or Discussion

Every existing table in `results004.tex` points to `\Cref{tab:evaluation_metrics}` for its metric
definitions (for example, the captions of `tab:delayed_performance_interval` and
`tab:results_reduced_frequency`). `sections.md` line 66 requires every reported analysis to have a
described method. The observed-SD, estimated-SD, SD-ratio, temporal-correlation, and sign-agreement
quantities have no such home yet. Add them either as new rows in `tab:evaluation_metrics` or as a
short subsection in `appendix002.tex`, parallel to the existing `app:paired_mae_comparisons` appendix
section that already documents the resampling procedure for the reduced-frequency comparisons. The
definition should state explicitly, in one sentence, why a high-correlation-low-SD-ratio pairing
indicates amplitude flattening while a low-correlation pairing (regardless of SD ratio) indicates a
timing problem — this sentence is what turns four numbers into the "distinguish two failure modes"
argument Q2 is meant to deliver, and it should not be left for the reader to infer from the numbers
alone.

---

## One wording note: keep "expansion," do not upgrade it to "elastic rebound" or similar

If the sign-agreement or any related text needs to describe the non-compaction sign, use a neutral,
purely descriptive term such as "expansion" (matching the sign convention already stated in
`discuss003.tex` and `results004.tex`'s figure captions: "Positive values indicate estimates above the
observations"). Terms like "elastic rebound" carry a specific reversibility claim
(`domain.md`, "Elastic Compaction" and "Residual Subsidence" entries) that neither Section 4.1's
results nor this diagnostic test. Reserve mechanism-specific vocabulary for a claim that has actually
been tested against a preconsolidation-stress or pore-pressure record, which this diagnostic does not
attempt.

---

## Two open items this diagnostic does not touch, carried forward from the prior notes

Q2 answers the `results004.tex` line 44 question (why S5-S6 underperform), continuing the work Q1
started. Two items remain open and are not addressed by this diagnostic:

- **`results004.tex` line 50** (why the fitted coefficients vary by depth section) is a separate
  question from the S5-S6 performance gap and needs its own attributed-mechanism treatment, per
  Finding 3 of `20260825_discuss003_argumentative_framework_review.md`.
- **Finding 2** of that same review (Hung et al. 2025 citation, required by `CLAUDE.md`'s novelty
  guardrail, currently absent from every section including the Discussion) remains unaddressed by Q1
  or Q2. Flagging again here so it does not get lost while attention is on the S1-S4/S5-S6 diagnostic.

---

## Summary

| Item | Verdict |
|---|---|
| Overall Q2 design (4+1 metrics, read-only against frozen predictions) | Approved — correctly separates amplitude error from timing error, which R² alone cannot |
| SD ratio, temporal correlation (metrics 1-4) | Approved as proposed |
| Sign-agreement rate (metric 5) | Approved conditional on (a) reporting the observed compaction/expansion baseline alongside it, and (b) confirming effective monthly-increment noise is below typical observed-increment magnitude before trusting a month's sign |
| Definition location for all five metrics | Add to `tab:evaluation_metrics` or a new `appendix002.tex` subsection before citing them in Results or Discussion |
| Terminology for the non-compaction sign | Use "expansion"; do not use "elastic rebound" or other reversibility-implying terms |
| Still open, not touched by Q2 | `results004.tex` line 50 (coefficient variation by depth); Hung et al. (2025) citation (High severity, `CLAUDE.md` guardrail) |
