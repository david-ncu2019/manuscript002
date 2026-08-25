# Response to the writing assistant's Q6 (Hung et al. 2025 scope-comparison paragraph, discuss003.tex)

## Original question from the writing assistant (verbatim, Vietnamese)

> Q5 đã được chấp thuận. Phản hồi cũng đồng ý rằng bảng coefficient chỉ mô tả mức ổn định và hướng
> của các fitted relations qua 24 lần cập nhật, không phải kiểm định ý nghĩa thống kê hoặc bằng
> chứng về nguyên nhân performance. Tôi đã kiểm tra toàn văn Hung et al. (2025). Hai nghiên cứu
> không nên so sánh trực tiếp RMSE vì chúng khác response, khoảng thời gian, độ phân giải và thiết
> kế đánh giá:
> - Hung et al. dùng chuỗi extensometer tự động với tần suất 10 phút tại một số anchor depths và
>   Prophet để forecast displacement trong bốn tháng tiếp theo.
> - Manuscript hiện tại ước tính monthly deformation increments trong sáu đoạn sâu 50 m từ hydraulic
>   head, vertical surface displacement và seasonal variation khi MLCW information chưa có hoặc giảm
>   đi.
> - Nghiên cứu hiện tại dùng thông tin của tháng cần ước tính, nên đây không phải cùng bài toán
>   forecasting của Hung et al.
>
> ❓ Q6 - Cách đưa Hung et al. (2025) vào Discussion: Có chấp thuận thêm một đoạn so sánh phạm vi ở
> gần cuối Subsection 5.1 không? Đoạn này sẽ thực hiện ba việc. Trước hết, nó ghi nhận Hung et al.
> đã chứng minh khả năng forecast displacement tại selected depths bằng high-frequency extensometer
> records ở Tuku. Tiếp theo, nó phân biệt nghiên cứu hiện tại bằng mục tiêu ước tính monthly
> deformation increments trong sáu standardized depth sections khi direct MLCW information chưa có.
> Cuối cùng, nó xác định hai nghiên cứu là bổ trợ nhau về câu hỏi quan trắc, không so sánh trực tiếp
> các error metrics và không tuyên bố nghiên cứu hiện tại tốt hơn. Đoạn so sánh sẽ xuất hiện sau khi
> kết quả và cách diễn giải của nghiên cứu hiện tại đã được thiết lập, đúng trình tự present finding
> → interpretation → prior work → contribution.

---

**Scope:** Answers the proposed Hung et al. (2025) scope-comparison paragraph for the end of
`subsec:discussion_layerwise_estimation`, and confirms the current state of `sections/intro001.tex`
against the same requirement. No manuscript file is edited by this note.

**Verdict: approved for the Discussion. One requirement from the same guardrail note — the
Introduction — remains completely unmet and is now confirmed and precisely located, not just
flagged in general terms as in the original review.**

---

## The three-part paragraph structure is sound, and resolves an open question from Finding 2 of the original review

Finding 2 of `20260825_discuss003_argumentative_framework_review.md` left open whether Hung et al.
(2025)'s reported errors would turn out to be numerically comparable to this manuscript's, or whether
the paragraph would instead have to state why they are not — calling this "a factual question this
review cannot answer from the Discussion text alone... requires reading Hung et al. (2025)'s reported
error metrics." That reading has now been done. The four stated grounds for non-comparability —
different response variable (displacement at selected anchor depths vs. deformation increments in six
standardized 50 m sections), different temporal resolution (10-minute automated readings vs. monthly),
different time horizon (four-month-ahead forecast vs. contemporaneous-month estimation), and different
evaluation design (Prophet forecasting vs. this study's walk-forward design) — are not a fallback
position; given what the two studies actually measure and evaluate, direct RMSE comparison is the
wrong move, and stating why is the correct one. This closes Finding 2's open question with a
definitive answer rather than leaving it as one of two possible paths.

The three-part structure itself is well-formed against the project's own section rules. Placing it
after the S1-S4/S5-S6 finding and interpretation is established follows `sections.md` line 101-104
directly: "Explain what the results mean before broadening to prior work or wider implications...
Compare with prior work to show agreement, disagreement, or changed understanding. Do not create a
detached literature review." Declining a direct metrics comparison in favor of a complementarity
framing is also the framework-correct choice for a genuinely non-comparable design — the reviewed
15-paper framework states this explicitly (line 1778): "A design without either kind of comparator...
legitimately has no concordance paragraph — forcing one would not make the manuscript more
NHESS-like." The same logic applies here: forcing a numeric comparison Hung et al. (2025)'s own design
does not support would weaken the paragraph, not strengthen it.

The distinction as framed also does real, load-bearing work for the manuscript's most safety-critical
guardrail. `CLAUDE.md`'s novelty note requires: "Call it nowcasting (same-month predictors →
same-month output). Use forecasting only if every predictor precedes the target month." Q6's third
point — "Nghiên cứu hiện tại dùng thông tin của tháng cần ước tính, nên đây không phải cùng bài toán
forecasting của Hung et al." — states exactly this distinction, using Hung et al. (2025) as the
concrete contrast case that makes the nowcasting/forecasting line legible to a reader rather than an
abstract terminological rule. This is the paragraph earning its place beyond citation-count compliance.

## Confirmed: the Introduction still needs the same distinction, at a specific, identifiable location

`CLAUDE.md`'s guardrail states the citation and distinction are required "wherever the two studies
could be confused (Introduction, Discussion)" — both sections by name. Q6 addresses only the
Discussion. Reading `sections/intro001.tex` directly (not from memory) confirms the Introduction gap
is real and precisely locatable: line 9 reads, "Previous studies in central Taiwan combined
groundwater levels, geodetic measurements, and multilayer compaction records to examine subsidence
processes or simulate aquifer-system compaction \citep{hung2012_mlcw, hung_measuring_2021}. Data-driven
analyses have also reconstructed missing compaction records from hydrogeological, environmental, and
land-use variables \citep{liu_reconstructing_2023}. A recent single-site study used deep learning to
reconstruct cumulative compaction and examine groundwater-management scenarios \citep{liu_deep_2025}.
However, the available studies did not test monthly compaction estimates for standardized depth
sections under repeated, temporally ordered delays in the availability of the response observations."

Hung et al. (2025) belongs in this exact sentence, and arguably more directly than the two Liu studies
already cited there — it is the same site (Tuku), the same instrument family (MLCW/extensometer), and
it is a forecasting study rather than a test of estimation under delayed-delivery conditions, which is
precisely the gap this sentence already claims. Recommend adding `\citep{hung2025_realtime}` to this
sentence (or an adjacent clause naming it explicitly, matching the Discussion's fuller treatment) as a
short addition — this does not need the same three-part paragraph treatment as the Discussion, since
the Introduction's job here is gap-establishment, not full scope-comparison, but the citation itself is
not optional per the guardrail's explicit wording.

## One ordering question for the author: how does this paragraph sit relative to Q1 Step 4's closing paragraph

`20260825_response_to_writing_assistant_q1.md` approved a closing move for this same subsection (Step
4): return to the positive contribution — "continuous observations can support depth-section
estimation, but MLCW still provides the depth resolution needed to see where an aggregate signal no
longer represents the profile." If Q6's Hung et al. paragraph is added after that closing paragraph, it
becomes the subsection's new final paragraph, and Step 4's contribution statement is no longer the last
word. If added before it, the subsection still ends on Step 4's contribution note. Both orders are
defensible — the Hung et al. paragraph's complementarity framing is itself a form of contribution
statement, and could plausibly be merged with or placed immediately adjacent to Step 4's closing rather
than treated as a fully separate paragraph. Recommend the author confirm the intended final order
before drafting, since Q6's text specifies where the paragraph sits relative to the S1-S4/S5-S6
finding but not relative to the already-approved closing paragraph.

## One drafting caution: keep this study's framing vocabulary visibly separate from Hung et al.'s in the same paragraph

The bibliography entry's own title contains "Near real-time subsidence monitoring and AI forecasting."
`CLAUDE.md` forbids describing this manuscript's own work as "near-real-time AI forecasting" — that
prohibition governs how this study describes itself, not whether another paper's title can be cited
accurately, so citing Hung et al. (2025) by its real title is not itself a violation. The risk is
adjacency: if the drafted paragraph places Hung et al.'s descriptors (real-time, forecasting,
high-frequency) close to this study's own descriptors (nowcasting, monthly, contemporaneous) without a
clear sentence-level separation, a reader skimming the paragraph could come away with the two framings
blurred. Recommend keeping one sentence exclusively describing Hung et al. in its own terms and a
separate sentence exclusively describing the current study in its own terms, rather than a single
sentence that mixes both studies' vocabulary.

## This paragraph does not need the same author-confirmation gate as Q1/Q4's physical candidates

Unlike the cGNSS-integration and hydraulic-head-representativeness candidates in Q1/Q4, which proposed
mechanisms requiring `[AUTHOR CONFIRMATION REQUIRED]` tagging per `style.md` line 115, this paragraph's
content is source-attributed (what Hung et al. 2025 did, verified by the author's own full-text
reading), manuscript-grounded (this study's own stated goal), and a direct logical consequence of the
comparability analysis just performed — closer to `style.md`'s "logical bridge" category (line 111)
than to new scientific content. The confirmation this kind of content needs has already happened: the
author read the source directly rather than relying on an abstract or a secondary summary, which is
exactly what `style.md` line 131 requires before citing what a source supports.

---

## Summary

| Item | Verdict |
|---|---|
| Three-part paragraph structure (acknowledge, distinguish, frame as complementary) | Approved |
| Placement after the S1-S4/S5-S6 finding and interpretation | Approved — matches `sections.md` line 101-104 |
| Declining direct RMSE comparison | Approved — the four-dimensional incomparability is real, not a fallback; matches the framework's own contingency for when a concordance paragraph should be omitted |
| Nowcasting-vs-forecasting distinction using Hung et al. as the contrast case | Approved — this is the paragraph's strongest justification, directly enforcing `CLAUDE.md`'s most safety-critical framing rule |
| Introduction citation (`intro001.tex` line 9) | Confirmed still missing by direct read of the current file. Recommend adding `\citep{hung2025_realtime}` to the existing gap-statement sentence — required by the same `CLAUDE.md` guardrail, not optional |
| Ordering relative to Q1 Step 4's closing paragraph | Needs author confirmation — recommend either merging the two closing moves or explicitly placing Hung et al.'s paragraph before Step 4's contribution statement so the subsection still ends on the positive-contribution note |
| Wording adjacency (real-time/forecasting vs. nowcasting/monthly) | Keep each study's descriptors in separate sentences to avoid blurring this manuscript's required framing |
| Author-confirmation requirement | Not needed at the same level as Q1/Q4's physical candidates — this content is source-verified and manuscript-grounded, not a proposed new mechanism |

---

## Addendum: verified directly against the primary source

**Source read in full:**
`D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\002_docs\papers\Hung et al. - 2025 - Near real-time subsidence monitoring and AI forecasting with multi-depth extensometers_full_paper.md`

The verdict above was written after accepting the writing assistant's own summary of Hung et al.
(2025) at face value. The author has since pointed to the primary source directly, and this addendum
reports what a direct, full-text read confirms, corrects, and adds — so the writing assistant can
verify every claim below against the same file rather than a second-hand summary.

### Confirmed exactly as stated in Q6

- 10-minute automated measurement frequency for the extensometers (source Table 3: "Measurement
  frequency: Every 10 min (automated)").
- Prophet used for forecasting (source Section 4, citing Taylor and Letham, 2018).
- Four-month forecast horizon (source Section 7: training through February 2024, forecast for
  July-October 2024).
- The paper does not compare its own RMSE against any other study's monthly-increment estimation —
  its own comparisons (Section 8.1) are between its extensometers and its own MLCW, not against any
  external nowcasting or forecasting study.

### Correction: the AI forecast demonstration used one depth series, not "selected depths" plural

Q6's own text (both the writing assistant's question and this review's prior verdict) describes Hung
et al. (2025) as forecasting "displacement tại selected depths" (plural). The extensometer *network*
does cover three depths (130, 300, and 400 m — source Section 3.1, Section 8.1 Table 3), but the
specific Prophet forecasting result reported in Section 7 (RMSE 0.52 mm before optimization, 0.34 mm
after, a 35% improvement) was computed for one displacement series only, not for all three depths
together. Recommend the manuscript's comparison paragraph describe the forecasting demonstration as
single-series ("a displacement time series at one monitored depth"), reserving "multiple depths" for
the extensometer network's monitoring capability in general (Section 6.1), not for the specific
forecasting result being distinguished from.

### Flag, not a correction: an internal depth-labeling inconsistency in the source paper itself

Section 7 names the forecasted series "the TJHS extensometer at a depth of 263 m." This does not match
either of two things stated elsewhere in the same source paper: Section 3.1 lists the three
extensometer depths as 130, 300, and 400 m (263 m is not among them), and Section 3.1 separately lists
263 m as the depth of one of the *groundwater observation wells*, not an extensometer. Section 7 also
switches from "TKJS" (used everywhere else in the paper, including the site name itself, "TKJS
supersite") to "TJHS." This looks like an internal inconsistency in Hung et al. (2025), not something
this review can resolve. **Recommend the manuscript's comparison paragraph avoid citing a specific
depth for the forecasting demonstration**, describing it only as "a displacement series from the TKJS
site" — accurate regardless of which specific depth Section 7 actually meant.

### Addition: the distinction is sharper than "same-month vs. four-month-ahead" — the two studies solve different classes of problem

Q6 already states the correct nowcasting-vs-forecasting distinction. The primary source supports a
sharper version. Hung et al. (2025)'s Prophet model (source Equation 1: $y(t) = g(t) + s(t) + h(t) +
\epsilon_t$) forecasts the extensometer series from its own trend and seasonality components; the
source describes $h(t)$ as capable of incorporating external regressors "e.g., rainfall or pumping
policy changes" as a general Prophet feature, but nowhere states that groundwater level or GNSS data
were actually supplied as regressors in this study's implementation. The Section 7 forecast reads as a
univariate self-extrapolation of the displacement series' own history. This manuscript's approach uses
contemporaneous, multi-source predictors (hydraulic head change, cGNSS displacement, seasonal terms)
for the same month being estimated, with no extrapolation from the response variable's own past values
as a predictor. These are two different problem classes — univariate future extrapolation versus
same-month multi-variable regression — not only two different time horizons. This strengthens, and can
sharpen, the distinction paragraph beyond what Q6 already proposes, if the author wants to state it
this precisely.

### Confirmed: the same physical monitoring station, not merely a similar one nearby

Cross-checking station identifiers between the two documents: `dataset003.tex` line 18 states the
manuscript's cGNSS observations come from "the adjacent TKJS cGNSS station." Hung et al. (2025)
Section 3.1 names its entire monitoring supersite "TKJS" (Tuku Junior High School) and describes,
within it, a 300 m MLCW and three groundwater wells at 87, 179, and 263 m. `dataset003.tex` line 14
and the data-source table (line 150) list this manuscript's own GWL wells at 81-84 m, 176-179 m, and
257-263 m — close enough to Hung et al.'s 87/179/263 m to plausibly be the same three wells reported
with different rounding or a slightly different reference point, not three different wells that
happen to be nearby. The MLCW depth (300 m, precision 1 mm) also matches exactly between the two
documents.

**Confirmed by the author directly (2026-08-25): this is the same physical monitoring site.** The
author stated explicitly: "trạm của tui và trạm trong bài Hung et al 2025 là một đó, chúng tui đang
làm chung một site, chỉ là mục đích nghiên cứu là khác nhau" (the two stations are the same site; only
the research purpose differs). This is no longer a finding requiring confirmation — it is an
established fact this review can build on directly.

This changes what the comparison paragraph must do. The relationship between this manuscript and Hung
et al. (2025) is not "the closest comparable prior study at a similar site" — it is two analyses of
the same TKJS monitoring infrastructure (MLCW, GWL wells, cGNSS station), built for two different
research purposes: Hung et al. (2025) forecasts a single extensometer displacement series forward in
time using its own history; this manuscript estimates depth-resolved MLCW compaction for the current
month using contemporaneous hydraulic head and cGNSS observations. Given this, the citation is not
optional guardrail compliance — omitting it would leave a reviewer familiar with either paper to
wonder why a shared-site prior study is not acknowledged at all. **Recommend the comparison paragraph
state the shared site directly** (for example, "using extensometer, MLCW, groundwater, and cGNSS
records from the same TKJS monitoring station" or equivalent phrasing), rather than describing Hung et
al. (2025) only as a nearby or comparable prior study. This also strengthens the complementarity
framing already approved in Q6/Q7/Q8: two independent analyses of the same instrumented site, addressing
different questions, is a more precise and more defensible claim than two studies happening to share
a general location.

### A concrete reason to keep the two studies' RMSE values out of the same sentence

Hung et al. (2025)'s reported RMSE (0.34-0.52 mm) is computed over the full four-month forecast window
at the displacement series' native temporal resolution, not per month. This manuscript's RMSE
(0.21-0.66 mm/month, `tab:delayed_performance_interval`) is explicitly a monthly figure. Both are
reported in millimeters, which creates a real risk that a reader skimming a paragraph containing both
numbers could visually compare 0.34-0.52 mm against 0.21-0.66 mm/month and perceive rough
equivalence, when the two quantities are not on the same temporal basis and are not comparable at all.
This is a concrete illustration of why Q6 is right to decline a direct RMSE comparison — not a
hypothetical risk, but one visible the moment both numbers are read side by side.

### Updated summary for this addendum

| Item | Verdict |
|---|---|
| 10-minute frequency, Prophet, 4-month horizon | Confirmed exactly as stated in Q6, verified against primary source |
| "Forecast displacement at selected depths" | Correct only for the extensometer network's general monitoring; the specific Prophet forecast result (Section 7) covers one displacement series only — recommend rewording |
| Depth of the forecast series (263 m / TJHS) | Internally inconsistent in the source paper itself — recommend the manuscript avoid citing a specific depth for this demonstration |
| Nowcasting vs. forecasting distinction | Confirmed and sharpened: same-month multi-source regression vs. univariate self-extrapolation forecast, not only a difference in time horizon |
| Same physical monitoring station (TKJS) | **Confirmed directly by the author (2026-08-25).** Raises the citation from guardrail compliance to shared-data-source disclosure — the comparison paragraph should state the shared site explicitly, not imply general proximity |
| RMSE values in the same sentence | Concrete risk, not hypothetical — the two figures share units (mm) but not a temporal basis (per-month vs. per-four-month-window); keep them in separate sentences or omit Hung et al.'s specific number entirely |
