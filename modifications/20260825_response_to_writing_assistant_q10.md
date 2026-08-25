# Response to the writing assistant's Q10 (dividing labor between the 2021 and 2025 Hung-group citations, discuss003.tex)

## Original question from the writing assistant (verbatim, Vietnamese + English proposed text)

> Q10: Có đồng ý giữ cả hung_measuring_2021 và hung2025_realtime, nhưng giao cho mỗi citation một
> nhiệm vụ khác nhau không? Đầu Subsection 5.1, hung_measuring_2021 sẽ giải thích sự khác biệt giữa
> tín hiệu tổng hợp và quan trắc theo độ sâu:
> > The cGNSS record represents the integrated surface response, whereas MLCW observations separate
> > deformation among monitored depth intervals. A station-scale displacement signal can therefore
> > support monthly estimation without representing each section equally well
> > \citep{hung_measuring_2021}.
>
> Gần cuối subsection, hung2025_realtime sẽ so sánh hai câu hỏi nghiên cứu tại cùng TKJS site bằng
> đoạn đã được duyệt ở Q9. Tôi đề xuất đồng ý. Cách này tránh lặp lại cùng một luận điểm: bài năm
> 2021 hỗ trợ cách diễn giải về quan trắc theo độ sâu, còn bài năm 2025 xác định vị trí của nghiên
> cứu hiện tại so với công trình gần nhất.

Source read in full for this response:
`D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\002_docs\papers\Hung et al. - 2021 - Measuring and Interpreting Multilayer Aquifer‐System Compactions for a Sustainable Groundwater‐Syste_full_paper.md`

---

**Scope:** Answers the proposed division of labor between `hung_measuring_2021` (subsection opening)
and `hung2025_realtime` (subsection close, per Q9) for `subsec:discussion_layerwise_estimation`. No
manuscript file is edited by this note.

**Verdict: approved.** The proposed opening sentence is verified accurate against the primary source.
One structural observation is offered as the review's main contribution here: the sentence's content
closely resembles an existing passage the author has already flagged as unclear, and this proposal's
real improvement is where the sentence sits, not primarily what it says.

---

## The proposed sentence is verified accurate against Hung et al. (2021)

**"The cGNSS record represents the integrated surface response, whereas MLCW observations separate
deformation among monitored depth intervals."** This closely matches the source's own Introduction
(Section 1, paragraph 2): "Such methods measure the total vertical displacement occurring below the
surface, representing the result of all vertical deformation from the land surface to the center of
the Earth, rather than depth-specific deformation... In contrast, deformation measurements below the
surface at specific depth intervals can provide clues for understanding the cause and mechanism of
land subsidence." Hung et al. (2021) groups "precision leveling, GPS, and InSAR" together as the
surface-integrated category; this manuscript's sentence narrows that to cGNSS specifically, which is
a legitimate specialization (cGNSS is a continuous GPS-based method) consistent with how this
manuscript already uses the term throughout, not a misattribution of what the source actually says.

**"A station-scale displacement signal can therefore support monthly estimation without representing
each section equally well \citep{hung_measuring_2021}."** The word "therefore" marks this as this
manuscript's own inference drawn from the first sentence's cited premise, not a separate claim
requiring its own external support — Hung et al. (2021) does not discuss monthly estimation from
cGNSS/GWL predictors at all (that is this manuscript's own contribution). This is a standard and
appropriate citation pattern: cite the established general fact, then draw the paper's own conclusion
from it. No misattribution.

No forbidden term from `domain.md` appears in the proposed sentence.

## The two-citation division of labor is well-motivated and non-redundant

Hung et al. (2021) is a general MLCW-methodology and network paper: Section 4.2.1 states 22 MLCWs were
installed across Yunlin County, and Figure 8's discussion separately confirms Tuku is one of the two
townships with the most severe subsidence in that network ("Tuku and Yuanchang are two townships that
experience the most severe land subsidence, with rates exceeding 5 cm/year"), though the paper's three
detailed case-study sites (Section 5: JNES, STES, YWJS) are not Tuku/TKJS specifically. Hung et al.
(2025), by contrast, is the site-specific TKJS paper (confirmed in the Q6/Q9 exchanges to share this
manuscript's own physical monitoring station). Using the 2021 paper for a general, network-wide
methodological point at the subsection's opening, and the 2025 paper for a site-specific novelty
comparison at the subsection's close, matches the actual scope of each source and avoids the
redundancy risk flagged in the Q7 response. This is approved as proposed.

## The review's main observation: this is substantially the existing sentence, repositioned — check whether repositioning alone resolves the author's original confusion

`discuss003.tex` line 12 currently reads: "MLCW measurements can therefore show where a station-level
signal does not describe the profile uniformly, and a station-wide average cannot represent every
depth section equally." That exact sentence carries an unresolved author note: "bạn viết đoạn này là
có ý gì, tui chưa hiểu lắm, tui không hiểu bạn muốn truyền tải điều gì ở đây, nó có kết nối gì với
phần results, và nó sẽ mở ra điều gì cho các phần thảo luận bên dưới?" Q10's proposed replacement —
"A station-scale displacement signal can therefore support monthly estimation without representing
each section equally well" — makes largely the same logical move: a station-scale signal is useful,
but does not represent every section equally. The wording has changed; the underlying claim has not.

What has changed, and what likely does the real work of resolving the original confusion, is
placement. The existing sentence currently sits mid-paragraph, after the R²/RMSE numbers are already
reported, where it reads as an afterthought with no clear job. Q10 proposes placing this content at
the subsection's true opening instead. Positioned there, the sentence can do something the current
placement cannot: motivate, before any numbers appear, why the S1-S4-versus-S5-S6 question (Q1 Step 1)
is worth asking at all — a station-scale signal being usable but imperfect is exactly the premise that
makes uneven performance across depth sections an expected, explicable possibility rather than a
surprising anomaly. This matches `sections.md`'s own principle for opening content (line 101, applied
by analogy: state the framing before the specific comparison that depends on it).

Recommend treating this as the working hypothesis to check once the subsection is actually drafted,
not as a settled fact: read the assembled opening in context and confirm it answers the author's three
original questions (what is the point; how does it connect to Results; what does it open up for the
Discussion that follows). **The author has asked that every `% my note : ... %` marker in
`discuss003.tex` be kept permanently as a historical record, regardless of whether the passage it
annotates is later revised, moved, or resolved — none of these markers should be deleted at any
point.** If the repositioned sentence still leaves the same confusion once drafted, the fix needed is
not further rewording of this specific claim but a different explanatory move entirely — that would be
a genuinely new finding, not something this review can resolve in advance of seeing the drafted
result.

---

## Summary

| Item | Verdict |
|---|---|
| Two-citation division of labor (2021 for opening, 2025 for closing) | Approved — well-motivated, matches each source's actual scope, avoids the redundancy risk flagged in the Q7 response |
| Proposed opening sentence, claim 1 (cGNSS integrated vs. MLCW depth-specific) | Verified accurate against Hung et al. (2021) Section 1 — near-verbatim match |
| Proposed opening sentence, claim 2 (station-scale signal supports estimation, imperfectly) | Correctly framed as this manuscript's own inference from the cited premise, not a separate claim needing its own support — no misattribution |
| Forbidden terminology | None present |
| Content vs. wording relative to the existing (confusing) line 12 sentence | Largely the same underlying claim, reworded — the likely source of improvement is repositioning to the subsection's opening, not the wording change alone |
| Recommended check on whether the confusion is resolved | Confirm, once drafted in its new opening position, that it actually answers the author's three original questions (point, connection to Results, what it opens up) — do not assume repositioning alone resolves it without checking the drafted result |
| `% my note %` markers in `discuss003.tex` | **Author has asked these be kept permanently as historical records — never delete any of them, regardless of whether the annotated passage is later revised, moved, or resolved** |
