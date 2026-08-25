# Response to the writing assistant's Q8 (calibrated wording for the Hung et al. paragraph, discuss003.tex)

## Original question from the writing assistant (verbatim, Vietnamese + English proposed text)

> Q7 được chốt: đoạn so sánh Hung et al. (2025) sẽ nằm ngay trước đoạn kết của Subsection 5.1. Lập
> luận về coefficient sẽ nằm trong phần diễn giải ở giữa, không tạo thêm một đoạn độc lập. Sau khi
> viết xong, toàn subsection sẽ được rút gọn để tránh trở thành tập hợp các ý rời rạc. Có một điểm
> trong phản hồi Q7 cần chỉnh. Tôi không đề xuất dùng từ "irreplaceable" vì đây là khẳng định tuyệt
> đối, trong khi Hung et al. chỉ kết luận các hệ thống có ưu điểm bổ sung cho nhau. Các extensometer
> của họ cũng cung cấp thông tin tại một số độ sâu cố định.
>
> Q8: Có đồng ý dùng cách diễn giải thận trọng hơn sau đây không?
> > Hung et al. (2025) showed that high-frequency extensometers and MLCWs provide complementary
> > temporal and depth resolution. The present results extend this distinction by showing that
> > continuous hydraulic-head and surface-displacement observations can support monthly estimates
> > between MLCW updates, while periodic MLCW observations remain the direct basis for resolving and
> > evaluating deformation across the monitored profile.

---

**Scope:** Accepts the correction to `20260825_response_to_writing_assistant_q7.md`'s "irreplaceable"
recommendation and evaluates the proposed replacement sentence. No manuscript file is edited by this
note.

**Verdict: the correction is accepted without reservation — "irreplaceable" was an overclaim not
supported by the primary source. The proposed sentence is approved as calibrated and accurate, with
one optional precision note on the word "extend."**

---

## The correction is right: "irreplaceable" overstated what Hung et al. (2025) actually concludes, and mischaracterized their extensometer network

Checked directly against
`D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\002_docs\papers\Hung et al. - 2025 - Near real-time subsidence monitoring and AI forecasting with multi-depth extensometers_full_paper.md`,
Section 8.1's own language is explicitly relative, not absolute: "The MLCW excels in spatial
resolution... However, MLCW measurements are typically collected manually at monthly or quarterly
intervals, limiting their temporal resolution... In contrast, extensometers provide high-frequency,
automated measurements... The main limitation, however, is that each extensometer captures
displacement only at a single anchor depth." The paper's own conclusion, stated in the paragraph
immediately preceding its comparison table, is: "Given their complementary capabilities, a hybrid
monitoring strategy that combines both technologies is recommended." This is a trade-off/complementarity
claim — each instrument has a comparative advantage on one axis and a comparative limitation on the
other — not a claim that one instrument's information is impossible to obtain any other way.

The second part of the correction is also directly confirmed by the source: Hung et al.'s extensometer
network is not a single-depth, purely temporal instrument. Section 3.1 describes three extensometers
installed at 130, 300, and 400 m, providing three discrete depth-resolved displacement series, not
one integrated surface signal. This is coarser depth resolution than MLCW's own capability (up to 20
magnetic rings in one well, per Section 5.1), but it is genuine multi-depth information, not none.
Describing MLCW's depth resolution as something "neither continuous surface displacement nor
high-frequency point extensometer measurements can substitute for" — the wording recommended in the
Q7 response — collapsed two different comparator instruments (this manuscript's own cGNSS, which
truly is a single integrated surface signal with no depth information at all, and Hung et al.'s
extensometer network, which does carry coarse depth information) into one overstated claim. The
correction is accepted in full, and the earlier "irreplaceable" recommendation is withdrawn.

## The proposed sentence is approved

Checking each claim in the proposed two-sentence text against its sources:

- "Hung et al. (2025) showed that high-frequency extensometers and MLCWs provide complementary
  temporal and depth resolution" — matches Section 8.1's own stated conclusion precisely, using the
  paper's own framing (complementary capabilities) rather than an absolute claim.
- "continuous hydraulic-head and surface-displacement observations can support monthly estimates
  between MLCW updates" — matches this manuscript's own established Results and Discussion content
  (`subsec:results_delayed_delivery`, `subsec:discussion_layerwise_estimation`), not new content.
- "periodic MLCW observations remain the direct basis for resolving and evaluating deformation across
  the monitored profile" — accurately describes MLCW's dual role in this manuscript's own design: it
  is the response variable used to fit each section's model (`resolving`), and it is also the
  reference value each estimate is checked against at the end of every delayed-delivery cycle
  (`evaluating`), both confirmed in `methods006.tex` and `results004.tex`'s delayed-delivery design.

No forbidden term from `domain.md` appears (`remain` is not the banned `retain/retained/retaining`).
No wording blurs the nowcasting/forecasting distinction or uses `forecast` or `real-time` for the
present study. The sentence does not cite any of Hung et al.'s numeric results (RMSE, percent
improvement), consistent with the Q6 addendum's caution that the two studies' error metrics share
units but not a comparable temporal basis and should not appear in the same sentence.

## One optional precision note on "extend this distinction" — not a correction, a possible sharpening

The word "extend" is defensible under one specific reading: Hung et al.'s underlying principle is that
no single instrument provides both temporal and depth resolution, so achieving both requires combining
instruments with complementary strengths. This manuscript's approach can be read as applying that same
principle in a different form — instead of combining two instruments that both directly measure
deformation (extensometer and MLCW), it combines indirect predictors that do not themselves measure
depth-resolved compaction (hydraulic head change, surface displacement) with periodic direct MLCW
measurements, to estimate the depth-resolved signal continuously between MLCW visits. Under this
reading, "extend" is accurate: the same underlying resolution trade-off is being addressed with a
different combination of data sources.

The one risk is that a reader unfamiliar with both papers' methods could read "extend this distinction"
as implying this manuscript also compares two direct deformation-measuring instruments the way Hung et
al. did, when the actual mechanism is closer to using one signal type to estimate another during a gap
in direct measurement — a data-fusion/estimation task, not an instrument-resolution comparison. This
is a subtle difference in kind, not merely in which instruments are involved, and the current sentence
does not make that difference explicit. This is offered as an optional sharpening, not a required
change — the sentence as proposed is not inaccurate, and adding a clarifying clause is a judgment call
for the author, not a correctness issue this review needs to insist on.

## Two items from prior exchanges that remain unaffected by Q8 and still need separate attention

- The likely shared TKJS monitoring station (Q6 addendum: `dataset003.tex`'s cGNSS station code
  "TKJS" and GWL well depths closely matching Hung et al. 2025's own TKJS site description) is not
  addressed by this sentence and does not need to be — it is a separate factual question about data
  provenance, not a resolution-comparison claim, and still requires the author's direct confirmation
  before the manuscript states or implies anything about it.
- The Introduction citation gap (`intro001.tex` line 9, confirmed still missing in the Q6 response)
  remains open and is unrelated to this Discussion-paragraph wording question.

---

## Summary

| Item | Verdict |
|---|---|
| Correction to Q7's "irreplaceable" wording | Accepted in full — confirmed against the primary source that Hung et al. (2025) frames the two instruments as complementary, not one-way irreplaceable, and that their extensometer network does provide coarse multi-depth information (130/300/400 m), not none |
| Proposed two-sentence text | Approved — every claim checked against its source (Hung et al. 2025 Section 8.1; this manuscript's own Methods/Results/Discussion) and confirmed accurate; no forbidden terms; no nowcasting/forecasting blur; no numeric comparison |
| "Extend this distinction" | Defensible and accurate under the data-fusion/estimation reading; optional sharpening available if the author wants to make explicit that this manuscript's complementarity is a different kind (indirect predictors estimating a direct measurement) than Hung et al.'s (two direct instruments with complementary resolution) |
| Same-station (TKJS) question | Unaffected by Q8, still open, still requires author confirmation separately |
| Introduction citation gap | Unaffected by Q8, still open |
