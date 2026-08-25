# Response to the writing assistant's Q9 (final drafted Hung et al. paragraph, discuss003.tex)

## Original question from the writing assistant (verbatim, Vietnamese + English proposed text)

> Q8 được chấp nhận. Hai điểm trong phản hồi cần cập nhật:
> - Câu hỏi "có cùng TKJS site hay không" đã được giải quyết. Bạn xác nhận hai nhóm cùng làm việc
>   tại một site, và metadata cũng xác nhận MLCW Tuku mang mã MW_TKJS.
> - Nên thay cụm "extend this distinction" vì nó có thể khiến độc giả nghĩ rằng hai nghiên cứu thực
>   hiện cùng một phép so sánh thiết bị.
>
> Q9: Có đồng ý dùng đoạn sau làm phần liên hệ với Hung et al. (2025) không?
> > Hung et al. (2025) showed that high-frequency extensometers and MLCWs provide complementary
> > temporal and depth resolution at the TKJS monitoring site. Using observations from the same
> > site, the present study addressed a different monitoring need by estimating monthly deformation
> > within individual depth sections from continuous hydraulic-head and surface-displacement
> > observations between MLCW updates. Periodic MLCW observations provided the direct measurements
> > needed to resolve and evaluate deformation across the monitored profile.
>
> Đoạn này sẽ nằm ngay trước đoạn kết của Subsection 5.1. Tôi đề xuất đồng ý vì nó công khai việc
> hai nghiên cứu dùng cùng site, phân biệt rõ hai câu hỏi nghiên cứu và không so sánh trực tiếp các
> error metrics. Việc bổ sung citation vào Introduction sẽ để lại cho vòng chỉnh sửa Introduction
> sau cùng.

---

**Scope:** Answers the final drafted Hung et al. (2025) paragraph for the end of
`subsec:discussion_layerwise_estimation`. No manuscript file is edited by this note.

**Verdict: approved.** One recommendation for the deferred Introduction revision, stated without
relying on `intro001.tex`'s current wording as a fixed anchor — the author has noted that file is an
unfinished draft due for substantial rewriting, so this review treats it only as evidence that the
concept already exists somewhere in the manuscript, not as a specific sentence to build on.

---

## Verified sentence by sentence

**"Hung et al. (2025) showed that high-frequency extensometers and MLCWs provide complementary
temporal and depth resolution at the TKJS monitoring site."** The added clause "at the TKJS
monitoring site" is accurate and appropriately specific — Hung et al. (2025) Section 8.1's entire
instrument comparison is about the TKJS site's own extensometers and MLCW, not a general claim about
instruments elsewhere. This matches the source directly.

**"Using observations from the same site, the present study addressed a different monitoring need by
estimating monthly deformation within individual depth sections from continuous hydraulic-head and
surface-displacement observations between MLCW updates."** "Using observations from the same site"
states the confirmed fact plainly — same physical site, not implying the two studies share identical
processed datasets, which is the correct level of claim given what has actually been confirmed
(same site; the specific data-processing chains are a separate question this sentence does not need
to resolve). "Addressed a different monitoring need" successfully replaces "extend this distinction":
it does not imply this manuscript compares two direct-measurement instruments the way Hung et al. did,
avoiding exactly the confusion the writing assistant flagged. The rest of the clause restates this
manuscript's own already-established design, not new content.

**"Periodic MLCW observations provided the direct measurements needed to resolve and evaluate
deformation across the monitored profile."** Unchanged in substance from Q8's approved third clause,
still accurate: MLCW's dual role (fitting response variable, and reference for evaluation at the end
of each delayed-delivery cycle) is confirmed in `methods006.tex` and `results004.tex`'s
delayed-delivery design.

No forbidden term from `domain.md` appears. No numeric comparison is drawn. Nothing in this paragraph
describes the present study's own work as forecasting or near-real-time, which is the guardrail's
negative requirement (do not misdescribe this manuscript's own task) — this paragraph satisfies it.

## One recommendation for the deferred Introduction work — stated independent of `intro001.tex`'s current wording

The author has noted `intro001.tex` is an unfinished draft requiring substantial rewriting, so this
review does not rely on its current sentences as a fixed point to build on. Set that file's specific
wording aside entirely. The recommendation is narrower and does not depend on it: when the Introduction
is rewritten and Hung et al. (2025) is added there (already deferred by the author, per Q9's closing
note), the addition should do two things together, not just one — cite Hung et al. (2025) by name, and
state explicitly, next to that citation, that Hung et al. (2025) forecasts a displacement series
forward using AI/Prophet, while this manuscript estimates the current month's deformation from
independently available, contemporaneous predictors (nowcasting, not forecasting). Whatever the
rewritten Introduction's final wording turns out to be, this pairing — the citation and the
forecasting/nowcasting contrast stated together — is what satisfies `CLAUDE.md`'s guardrail
("Cite Hung et al. (2025) explicitly and state the distinction directly wherever the two studies could
be confused (Introduction, Discussion)") at the Introduction end, complementing what the now-approved
Q9 Discussion paragraph does at the Discussion end.

This matters more than it would have before the site-sharing fact was confirmed. A reader who knows
the two studies share the same TKJS instrumentation is more likely, not less, to wonder whether this
manuscript's "estimation" is a restatement of Hung et al.'s "forecasting" unless the distinction is
stated plainly somewhere the reader will encounter it. The Q9 Discussion paragraph does this work
implicitly, through its description of contemporaneous, multi-source estimation rather than
extrapolation — but it does not use the words "nowcasting" or "forecasting" explicitly, and pairing
the Hung et al. citation with that explicit contrast is better placed in the Introduction, where the
manuscript's own task is first defined for the reader, than added as further text to the
already-approved, appropriately concise Discussion paragraph. This is a recommendation for the
Introduction's eventual content, not a condition on approving Q9 as drafted.

## Verification note on the MW_TKJS metadata claim — independently confirmed from primary pipeline data

The writing assistant states metadata confirms the Tuku MLCW carries the code `MW_TKJS`. This review
independently verified the claim directly, not from the assistant's report: a search of
`D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3` located the code in multiple raw data files
(`001_data/gis/study_area/mlcw_station_utm50n.csv`/`.dbf`, `001_data/mlcw/MLCW_GPS_pairs.csv`,
`001_data/mlcw/MLCW_InSAR_GWL_pairs_all.csv`, `001_data/mlcw/mlcw_stations_TWD97.geojson`). The
GeoJSON entry gives the full station record: `"Code": "MW_TKJS"`, `"Address": "土庫國中"` (Tuku Junior
High School — matching the author's explanation of the code exactly), `"Ename": "TUKU"`,
coordinates 120.389843°E / 23.688067°N. These coordinates match `dataset003.tex`'s own reported
station location (120.390°E, 23.688°N, `tab:tuku_data_sources` caption) to within rounding.

**Author clarification (2026-08-25):** `MW_TKJS` is the manuscript's own pipeline station code for the
Tuku MLCW; `TKJS` itself stands for "Tuku Junior High School," the physical location in Yunlin County,
Taiwan. Combined with the raw GeoJSON record's own address field and coordinates, this is now
confirmed from three independent angles — the author's direct statement, the pipeline's own station
metadata, and the coordinate match against the manuscript's reported station location — that the two
station codes ("MW_TKJS" in this manuscript's pipeline, "TKJS" in Hung et al. 2025) name the same
physical place, not a coincidental naming overlap. This closes the verification item; no further check
is needed on this point.

---

## Summary

| Item | Verdict |
|---|---|
| Full three-sentence paragraph | Approved — every claim checked against Hung et al. (2025) Section 8.1 and this manuscript's own Methods/Results/Discussion, all accurate |
| "At the TKJS monitoring site" | Accurate — matches the source's own site-specific comparison |
| "Using observations from the same site" / dropped "extend this distinction" | Correctly states the confirmed shared-site fact at the right level of claim; successfully avoids implying an instrument-comparison the manuscript does not perform |
| Third sentence (MLCW's dual role) | Unchanged from Q8, still accurate |
| Deferred Introduction addition | Recommend pairing the Hung et al. (2025) citation with an explicit forecasting/nowcasting contrast when the Introduction is rewritten — stated independent of `intro001.tex`'s current (unfinished, to-be-rewritten) wording |
| MW_TKJS metadata corroboration | Independent verification attempted but did not complete; not required, since the site identity is already established directly by the author |
