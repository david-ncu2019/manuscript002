# Second Third-Party Proofreading Report

**Manuscript:** Bayesian ridge regression estimation of monthly deformation within six depth sections at the Tuku multilayer compaction monitoring well (MLCW) station, Choushui River Alluvial Fan, Taiwan.
**Worktree:** `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\` (branch `reduced_v1`)
**Purpose:** Independent, read-only, fresh-eyes second-pass proofread, focused on verifying round-1 fixes and finding anything new (including defects introduced by the round-1 fixes themselves).
**Reviewer role:** No manuscript source file or figure file was edited during this review. The only file written was this report.

---

## Post-review resolution log

**Status updated:** 2026-09-01

This log records changes made after the independent review. The original report below remains unchanged as an audit record.

| Finding | Status | Resolution or decision |
|---|---|---|
| N-1 | **Resolved** | Removed all 19 `note` fields in `writing_manu2.bib` that contained machine-generated type labels, `_eprint` links, or Semantic Scholar citation counts. Substantive bibliographic notes were preserved. The rebuilt bibliography contains none of the reported export metadata. |
| N-2 | **Resolved** | Reordered the two figure environments in `sections/dataset003.tex`. The time-series figure, cited first in the prose, is now Figure 3; the lithology and MLCW deformation figure is now Figure 4. |
| N-3 | **Resolved** | Reordered the two table environments in `sections/results004.tex`. Monthly error and posterior interval statistics, cited first, are now Table 8; cumulative error after 80 months is now Table 9. |
| N-4 | **Resolved** | Standardized Table 4 to the `MAE`-then-`RMSE` order used by the other results tables. The header and all six value pairs were moved together and checked against the `full_model` rows in `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results003_calendar_aligned_38predictors\discussion_evidence_20260821\q11_predictor_information\performance_by_configuration_and_section.csv`. |
| Figure 3 terminology | **Resolved by author decision** | Adopted `deformation` as the manuscript-wide term. The original script and PNG were preserved. A renamed script generated a new PNG with the axis label `Deformation (mm)` and no change to the data, sign convention, plotting style, or layout. Provenance is stored in `modifications/fig3_deformation/`. |

The complete `pdflatex`, `bibtex`, `pdflatex`, `pdflatex` sequence produced a 58-page PDF with no undefined references or citations. Figure 3, Figure 4, Table 4, Table 8, and Table 9 were inspected in the compiled PDF. Existing non-blocking box warnings remain outside this change set.

---

## 1. Executive summary

The manuscript still builds cleanly (58 pages, zero undefined references or citations). All eight round-1 findings logged as "Resolved" — C-1, M-1, M-2, M-3, M-5, M-6, m-4, and AD-1 — plus the Herrera-García citation-support spot-check, were verified at their cited locations and are genuinely fixed. However, two of the round-1 fixes had side effects that a fresh read caught: adding the previously-missing Figure 3/Figure 4 citations (M-2) placed them in reversed order in the prose, and a pre-existing, previously unflagged table-citation-order reversal was found in the "no subsequent MLCW measurements" subsection (Table 9 cited two pages before Table 8, which is cited immediately after and appears first). A third new issue is a table with its RMSE/MAE columns swapped relative to every other results table in the manuscript. The most consequential new finding is that round-1's M-6 fix (raw Zotero export metadata printed into one bibliography entry) addressed only the one location round 1 happened to name; the same defect class — literal tool/database-export text such as "Type: Journal Article.", "\_eprint: [url].", and "84 citations (Semantic Scholar/DOI) [2026-03-12]." — still renders visibly at the end of 14 other cited reference-list entries, confirmed directly in the compiled PDF bibliography. One new Author-decision-required item was found: Figure 3's caption says "cumulative compaction" while the adjacent Figure 4's caption and the surrounding body prose call the same type of quantity "deformation" — but Figure 3's own source image is itself axis-labeled "Compaction (mm)", so this is not a wording-only fix.

---

## 2. Pre-flight and integrity confirmation

- `git rev-parse --show-toplevel` → `D:/112_PROJECT_002/.worktrees/manuscript_reduced_v1` — matches.
- `git branch --show-current` → `reduced_v1` — matches.
- `git rev-parse HEAD` → `f99a9eff18ae02f679bc3a158b4995bda3b519a2` — matches.
- Report-path collision check: `modifications\20260901_second_third_party_proofreading_report.md` did not exist before this review. No collision.
- Active `\input` list in `main.tex` was re-parsed directly and matches the 11-text-file list given in the task exactly (`sections/abbreviations`, `sections/intro002`, `sections/studyarea002`, `sections/dataset003`, `sections/methods006`, `sections/results004`, `sections/discuss003`, `sections/conclusion002`, `sections/appendix002`, plus `main.tex` and `writing_manu2.bib`). No discrepancy to report.
- File-integrity check: `git status --short --branch` was run from the worktree root. It reports the branch as `ahead 1` of `origin/reduced_v1` with only pre-existing untracked scratch files (`.superpowers/`, `citations/`, `figures/coefdrift_preview/`, `scripts/*`, `trash/*`, stray `.ipynb_checkpoints/` directories, etc.) — none of which are among the 11 in-scope text files or the 15 in-scope figure files. No tracked file shows as modified. `main.pdf`, `main.aux`, `main.log`, `main.bbl`, `main.blg`, `main.toc`, `main.lof`, and `main.lot` are all listed in `.gitignore` (confirmed via `git check-ignore -v`) and are therefore invisible to `git status` regardless of the build; their regeneration by the required `pdflatex`/`bibtex` sequence is expected and is not a source-file change. This is independently-verifiable evidence, not just an assertion, that none of the 11 text files, the `.bib` file, or the 15 figure files were altered by this review.

---

## 3. Build results

Commands run, in order, from the worktree root:

```
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

All four steps completed with exit code 0. Result: `main.pdf`, 58 pages (identical page count to round 1).

- **Undefined references/citations:** none (`grep -i "undefined" main.log` returned no matches).
- **Bibtex:** `main.blg` reports "You've used 57 entries" with 0 warnings and 0 errors (`warning$` built-in function-call count is 0). This is one more entry than round 1's reported count of 56; the extra entry is `nguyen_quantitative_2024`, which round 1 listed as unused and which the M-5 fix newly cited for the "95 GWL monitoring stations" claim — expected, not a defect.
- **Duplicate labels:** none. One apparent duplicate hit for `\label{fig:results_reduced_frequency_6month}` was investigated and is a false positive — the second occurrence is inside a Vietnamese `% NOTE` comment in `results004.tex:212`, not an active `\label` command. `main.log` contains no "multiply defined" warnings.
- **Duplicate bibliography keys:** none.
- **Remaining warnings (non-blocking), unchanged from round 1:**
  - Underfull `\hbox` in `sections/abbreviations.tex`'s table (paragraph at lines 4–90 of that file), page 11.
  - Underfull `\hbox` (badness 1675, 1158) in `results004.tex`'s sideways Table 6, page 47 area.
  - Overfull `\hbox` (13.39pt) in `methods006.tex` Table 2 cell wrapping (lines 186–199), page ~15.
  - Overfull `\hbox` (0.5pt) at a citation line break (`methods006.tex:204–205`).
  - None of these render as visibly broken text, clipped columns, or garbled spacing in the corresponding PDF pages (checked directly for the Table 2 and abbreviations-table pages).

### PDF visual QA (pages actually opened and inspected)

Opened and visually inspected: front matter/LOF/LOT (physical pp. 1–4), Introduction p. 1–3, Study Area/Datasets pp. 3–10, Methods/Results transition pp. 42–45 (Conclusions, front-matter placeholders, start of Appendix), Appendix pp. 46–47, References pp. 47–49, and the Results tables/figures on printed pp. 28–29 and 35–37.

- No visible `\placeholder{...}` text in the body of the 8 active content sections; placeholder text is visible only in the Abstract and front matter (Acknowledgements, Author contributions, Data availability, Conflict of interest) — see Section 8, not counted as findings.
- No caption separated from its figure/table by a page break in the pages inspected; no orphaned headings found.
- Figure 4's caption (dataset003.tex:40) now correctly reads "...cumulative deformation recorded by all **magnetic** rings..." (round-1 finding C-1) — confirmed both in the printed caption on p. 10 and in the List of Figures on p. iii.
- Table 1 (p. 8) GWL well codes/screen depths (09050321/81–84 m, 09050331/176–179 m, 09050341/257–263 m) and Figure 4's caption midpoint depths (82.5, 177.5, 260.0 m) are internally consistent (each is the exact arithmetic midpoint of its screen interval).
- Reference-list pages 47–49 (physical) were opened directly and confirm the bibliography-metadata finding reported in Section 4 below (see excerpts there).
- Figure/table placement vs. first mention: two new problems found, detailed in Section 4 (New issues #1 and #2), confirmed by opening the actual pages, not just by cross-referencing labels.

---

## 4. New issues

### Major

**N-1 — Raw tool/database-export text still visible in 14 other cited bibliography entries (same defect class as round-1 M-6, different locations)**

- Error type: malformed bibliography entries (`note` field containing unedited export/tool metadata that prints verbatim into the reference list)
- File: `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\writing_manu2.bib`
- Round-1's M-6 named only `survey_project_1999` (lines 491–499 in the round-1-reviewed version) and that fix is genuine and correct (verified below in Section 6). However, a full scan of every `note = {...}` field in the `.bib` file, cross-checked against the 57 keys actually `\citep`/`\citet`'d in the 11 in-scope files, found the identical defect pattern still present and still rendering in 14 other cited entries:

  | Cite key | Entry start line | `note` field line | Rendered text (from `main.bbl` / PDF) |
  |---|---|---|---|
  | `burbey_extensometer_2020` | 42 | 52 | `Type: Journal Article.` |
  | `chang_rice-field_2020` | 56 | 66 | `Type: Journal Article.` |
  | `galloway_application_2007` | 174 | 184 | `Type: Journal Article.` |
  | `hung2015_multiple` | 266 | 275 | `Type: Journal Article.` |
  | `jasechko_rapid_2024` | 369 | 379 | `Type: Journal Article.` |
  | `liu_characterization_2004` | 383 | 393 | `Type: Journal Article.` |
  | `nicholls_global_2021` | 422 | 432 | `Type: Journal Article.` |
  | `poland_guidebook_1984` | 460 | 469 | `Type: Book.` |
  | `chaussard_over_2021` | 84 | 93 | `\_eprint: https://agupubs.onlinelibrary.wiley.com/doi/pdf/10.1029/2020JB020648.` |
  | `herrera-garcia_mapping_2021` | 212 | 221 | `\_eprint: https://www.science.org/doi/pdf/10.1126/science.abb8549.` |
  | `hung_measuring_2021` | 297 | 306 | `\_eprint: https://agupubs.onlinelibrary.wiley.com/doi/pdf/10.1029/2020WR028194.` |
  | `huning_global_2024` | 330 | 339 | `\_eprint: https://agupubs.onlinelibrary.wiley.com/doi/pdf/10.1029/2023RG000817.` |
  | `hung2012_mlcw` | 247 | 260 | `84 citations (Semantic Scholar/DOI) [2026-03-12].` |
  | `hung2025_realtime` | 312 | 324 | `0 citations (Semantic Scholar/DOI) [2026-03-12].` |

  Directly confirmed by opening the compiled `main.pdf` reference list (physical pp. 48–49): reference [7] (Burbey 2020) ends "...URL https://doi.org/10.1007/s10040-019-02060-6. **Type: Journal Article.**"; reference [9] (Chang et al. 2020) ends "...URL https://doi.org/10.3390/rs13010103. **Type: Journal Article.**"; reference [11] (Chaussard et al. 2021) ends with a line reading "**\_eprint: https://agupubs.onlinelibrary.wiley.com/doi/pdf/10.1029/2020JB020648.**"; reference [18] (Galloway and Hoffmann, 2007) ends "...URL https://doi.org/10.1007/s10040-006-0121-5. **Type: Journal Article.**" The remaining 10 entries in the table above were confirmed by inspecting the corresponding `\bibitem` block in `main.bbl` (the same text `pdflatex` typesets onto the page), using the identical verification method round 1 used for the one instance it caught.
- Minimal proposed fix: for the 8 `Type: Journal Article`/`Type: Book` entries and the 2 `citations (Semantic Scholar/DOI)` entries, delete the `note` field entirely (these are annotation-only fields with no bibliographic content). For the 4 `\_eprint:` entries, either delete the `note` field (the `url`/`doi` field already gives the reader the link) or move the value to a real `eprint`/`archivePrefix` BibTeX field pair if the journal's citation style is meant to use it — but do not leave it as free text in `note`.
- Rationale: this is the same defect round 1's M-6 already established is a real, reader-visible problem ("this text is visible to any reader of the reference list and looks like an editing artifact rather than intended bibliographic content"); it simply was not exhaustively scanned for in round 1, which only reported the one entry it had already been looking at. 14 of 57 cited references (about one in four) currently carry this artifact.

### Minor

**N-2 — Figure 4 cited before Figure 3 in body prose (side effect of the M-2 fix)**

- Error type: figure-citation order
- File: `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\dataset003.tex`
- Lines: 6 (cites `\Cref{fig:tuku_observations_b}`, i.e., Figure 4) and 28 (cites `\Cref{fig:tuku_observations_a}`, i.e., Figure 3)
- Verbatim excerpt (line 6): "The temporal variation in these records is shown in \Cref{fig:tuku_observations_b}."
- Verbatim excerpt (line 28): "The profile is shown alongside cumulative MLCW deformation in \Cref{fig:tuku_observations_a}."
- Confirmed in the compiled PDF: the sentence citing Figure 4 appears on p. 6, the sentence citing Figure 3 appears on p. 8, but Figure 3 itself is not printed until p. 9 and Figure 4 not until p. 10 (per `main.lof`, entries 3 and 4). A reader is told about Figure 4 first, then Figure 3, but encounters the figures on the page in the order 3-then-4.
- Minimal proposed fix: swap the order of the two `\begin{figure}...\end{figure}` blocks currently at `dataset003.tex:30–35` (`fig:tuku_observations_a` / `fig_composite_ms2_dataset_TUKU.png`) and `dataset003.tex:37–42` (`fig:tuku_observations_b` / `TUKU_overview_dual_axis_gwlkriged.png`), so that the figure cited first in prose (currently `tuku_observations_b`) also becomes the lower-numbered figure. Because `\Cref` is label-based, no other cross-reference needs to change.
- Rationale: this did not exist as a defect in round 1 (neither figure was cited in body prose at all, which is what M-2 reported); adding the two missing citations introduced this new, smaller ordering problem.

**N-3 — Table 9 cited before Table 8 in body prose (pre-existing, not part of any round-1 finding)**

- Error type: table-citation order
- File: `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\results004.tex`
- Lines: 215 (cites `\Cref{tab:results_no_subsequent_mlcw_interval}`, i.e., Table 9) and 219 (cites `\Cref{tab:results_no_subsequent_mlcw_h80}`, i.e., Table 8)
- Verbatim excerpt (line 215): "...average RMSE ranged from 0.36 to 0.40~mm/month (\Cref{tab:results_no_subsequent_mlcw_interval})."
- Verbatim excerpt (line 219): "By month 80, the average absolute cumulative error across the six sections was 7.39, 6.69, and 4.29~mm for the initial records of 3, 5, and 8 years, respectively (\Cref{tab:results_no_subsequent_mlcw_h80})."
- Confirmed in the compiled PDF and `main.lot`: Table 8 ("Absolute cumulative deformation error without subsequent MLCW measurements") is defined earlier in the source (`results004.tex:246–266`) and Table 9 ("Monthly error and posterior predictive interval statistics...") is defined later (`results004.tex:269–284`). The sentence citing Table 9 appears on printed p. 35, but Table 9 itself does not print until p. 37; the sentence citing Table 8 appears on p. 36 and Table 8 prints immediately on that same page — so the reader sees Table 8 (cited second) two pages before Table 9 (cited first).
- Minimal proposed fix: swap the order of the two `\begin{table}...\end{table}` blocks at `results004.tex:246–266` (h80/Table 8) and `results004.tex:269–284` (interval/Table 9), so the interval table becomes the lower-numbered table, matching the order it is first cited in prose. `\Cref` is label-based, so no other cross-reference (including the four other citations to these two tables at `discuss003.tex:67` and `70`) needs to change.
- Rationale: this instance was not caught by round 1, whose report stated a full mechanical check of table citation order had been performed with no violations found beyond the two figure findings (M-1/M-2). It is a genuine, independently pre-existing ordering defect, not introduced by any round-1 edit.

**N-4 — Table 4's RMSE/MAE column order is reversed relative to every other results table**

- Error type: table formatting inconsistency
- File: `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\results004.tex`
- Line: 64 (header row of `tab:delayed_performance_interval`, i.e., Table 4)
- Verbatim excerpt: `\multicolumn{1}{c|}{\textbf{Section}} & \multicolumn{1}{c|}{\textbf{$R^2$}} & \multicolumn{1}{c|}{\textbf{RMSE}} & \multicolumn{1}{c|}{\textbf{MAE}} & \multicolumn{1}{c|}{\textbf{Coverage (\%)}} & \multicolumn{1}{c}{\textbf{Width}} \\`
- Table 4 orders its two error-metric columns as RMSE-then-MAE. Every other table that reports both metrics — the metrics-definition Table 3 (`methods006.tex:191–192`, MAE listed before RMSE), and results Tables 5, 7, and 9 (`results004.tex:85`, `192`, `277`, all "MAE" before "RMSE") — uses the opposite order, MAE-then-RMSE. Confirmed visually identical in the compiled PDF (p. 28 for Tables 4 and 5, pp. 35 and 37 for Tables 7 and 9).
- Minimal proposed fix: in Table 4's header row (line 64), swap the "RMSE" and "MAE" column-header labels so the header reads `$R^2$ | MAE | RMSE | Coverage (\%) | Width`, matching Tables 3, 5, 7, and 9. **This requires also swapping the two corresponding data values in every one of the six data rows (lines 66–71), not just the header labels** — e.g., row S1 currently reads `0.89 & 0.21 & 0.18 & 74.6 & 0.54` (RMSE=0.21, MAE=0.18 in that column order); after the header swap it must read `0.89 & 0.18 & 0.21 & 74.6 & 0.54` (MAE=0.18 first, RMSE=0.21 second) so that each numeral stays attached to its correct metric. Doing only the header swap, or only the data swap, would silently misreport all six sections' RMSE and MAE values.
- Rationale: this is a pure column-order/formatting inconsistency across the manuscript's own tables; no scientific claim changes if the header and all six rows are swapped together, but the fix must be described precisely because a partial swap corrupts data rather than fixing formatting.

---

## 5. Round-1 fixes not yet complete

None. All eight round-1 findings logged as "Resolved" (C-1, M-1, M-2, M-3, M-5, M-6, m-4, AD-1) were verified as genuinely and correctly fixed at the exact locations round 1 cited, as was the Herrera-García citation-support spot-check. (The M-6 fix is complete and correct at its cited location; the fact that the same defect class recurs elsewhere in the bibliography is reported as a new issue, N-1, above — not as an incomplete fix of M-6, since round 1 never identified those other 14 locations.)

---

## 6. Confirmed correctly resolved

| Round-1 finding | Confirmation |
|---|---|
| C-1 | "mstationagnetic" corrected to "magnetic" in Figure 4's caption (`dataset003.tex:40`); confirmed in both the PDF caption (p. 10) and the List of Figures (p. iii). |
| M-1 | Figure 1 (`fig:studyarea_a`) is now cited in body prose at `studyarea002.tex:4`, before its first appearance on p. 4. |
| M-2 | Figures 3 and 4 (`fig:tuku_observations_a`, `fig:tuku_observations_b`) are now both cited in body prose (`dataset003.tex:6`, `28`). (A new, smaller ordering side effect of this fix is reported as N-2 above.) |
| M-3 | "compaction" replaced with "deformation" for the modeled/observed response variable in `methods006.tex:1` (two instances) and `methods006.tex:36`; Methods now uses "deformation" for this quantity throughout its own text. |
| M-5 | Both previously uncited quantitative claims now carry an adjacent citation: the 38% rice-production statement (`studyarea002.tex:8`, `\citep{chang2022_wetanddry}`) and the GWL-station count, now corrected to the sourced "95 GWL monitoring stations" with `\citep{nguyen_quantitative_2024}` (`dataset003.tex:18`). |
| M-6 | `survey_project_1999`'s `note` field now reads "Water Resources Bureau Report, 130 pp." and the author is double-braced as `{{Central Geological Survey}}` (`writing_manu2.bib:491–496`); confirmed clean in the compiled bibliography, reference [8], p. 48. |
| m-4 | The empty `noauthor_notitle_nodate` entry is gone, the stray closing brace after `gambolati_2015` is gone (entry now closes cleanly at line 700), and the `survey_project_1999` author encoding is fixed (same fix as M-6 above). |
| AD-1 | Methods prose (`methods006.tex:34`, "included...for all six depth sections"), Table 2 (`methods006.tex:50`, "for all six sections"), and the Appendix equation/prose (`appendix002.tex:9–24`) are now mutually consistent: the 18-variable profile block is 3 metrics × all 6 depth sections, section-independent, matching the equation's $k$-only subscript. |
| Citation-support spot-check 2 (Herrera-García) | `intro002.tex:1` now correctly separates the initial 19% figure ("high or very high" probability) from the separate, unquantified "projected to increase further by 2040" statement, resolving the conflation round 1 flagged. |

---

## 7. Author decision required

**New — Figure 3's caption calls the plotted quantity "cumulative compaction"; the adjacent Figure 4's caption and surrounding body prose call the same type of quantity "deformation"**

- File: `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\dataset003.tex`
- Exact contradiction, in the manuscript's own words:
  - Body prose immediately before the figure (`dataset003.tex:28`): "The profile is shown alongside **cumulative MLCW deformation** in \Cref{fig:tuku_observations_a}."
  - Figure 3's own caption (`dataset003.tex:33`): "Lithological profile and **cumulative compaction** (01/2010--12/2024) at the Tuku MLCW station..."
  - The very next figure's caption, describing the same kind of cumulative MLCW curve (`dataset003.tex:40`): "...cumulative **deformation** recorded by all magnetic rings at the Tuku MLCW station."
- This is not a simple wording slip that can be corrected by swapping one word, because the caption's word choice matches its own source image: the figure file `figures/fig_composite_ms2_dataset_TUKU.png` was opened directly and its plot panel is itself titled "MLCW Tuku station" with an x-axis literally labeled "**Compaction (mm)**". Editing only the caption text to say "deformation" would make the caption disagree with the image it describes, which Step 3 of this review explicitly requires checking for; the figure file itself is out of scope to edit.
- The manuscript's own established convention (confirmed working correctly everywhere else after the M-3 fix, and stated explicitly in the round-1 resolution log) is that "deformation" denotes the measured/modeled response quantity (which is what this cumulative MLCW curve is — the same series body prose at line 28 already calls "cumulative MLCW deformation"), while "compaction" is reserved for the physical process of permanent sediment volume loss. Figure 3's caption and source image do not follow that convention, while Figure 4's caption (describing the same type of quantity) does.
- What would need to be checked to resolve this: (1) confirm from the plotting/data-source script or `source_provenance.json` for this figure whether the y-axis in `fig_composite_ms2_dataset_TUKU.png` actually plots the same "cumulative MLCW deformation" quantity used throughout the rest of the manuscript, or a different, specifically inelastic/permanent-compaction-only quantity; (2a) if it is the same quantity, the figure would need to be regenerated with the axis relabeled "Deformation (mm)" to match the manuscript's convention and Figure 4's caption; or (2b) if a deliberate distinction is intended, the caption and body prose would need supporting text explaining why this particular panel specifically shows "compaction" rather than total "deformation." No resolution is proposed here.

(AD-1, the predictor-count discrepancy from round 1, is already resolved — see Section 6 above — and is not repeated here.)

---

## 8. Known submission placeholders

Not counted as findings. All are pre-existing, tracked, active `\placeholder{...}` stubs in `main.tex`:

- Abstract (`main.tex:81`): entire abstract body is commented out except placeholder markers for pooled R²/RMSE/MAE, the main depth-dependent result, baseline comparison, empirical coverage, interval width, and the concise operational conclusion.
- Author list (`main.tex:76`): `[AUTHOR NAMES AND AFFILIATIONS]`.
- Acknowledgements (`main.tex:122`): `[FUNDING, DATA PROVIDERS, AND CONTRIBUTOR ACKNOWLEDGEMENTS]`.
- Author contributions (`main.tex:125`): `[AUTHOR CONTRIBUTION STATEMENT]`.
- Data availability (`main.tex:128`): `[DATA AND CODE AVAILABILITY STATEMENT]`.
- Conflict of interest (`main.tex:131`): `[CONFLICT OF INTEREST STATEMENT]`.
- `pdfauthor` metadata in `main.tex:62`: `{Author names to be confirmed}`.

---

## 9. Finding-count summary

| Severity | Count | Notes |
|---|---|---|
| Critical | 0 | — |
| Major | 1 | N-1: raw tool/database-export metadata visibly rendered in 14 cited bibliography entries (same defect class as round-1 M-6, different locations) |
| Minor | 3 | N-2 (figure citation order), N-3 (table citation order), N-4 (table column-order inconsistency) |
| Author decision required | 1 | New: Figure 3 caption "compaction" vs. adjacent "deformation" convention, blocked on image-vs-caption agreement (AD-1 from round 1 is already resolved, not recounted here) |

Round-1 fixes not yet complete: 0 (see Section 5).

---

## 10. Files read

**Text files (11, treated as authoritative current manuscript prose):**
1. `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\main.tex`
2. `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\abbreviations.tex`
3. `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\intro002.tex`
4. `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\studyarea002.tex`
5. `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\dataset003.tex`
6. `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\methods006.tex`
7. `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\results004.tex`
8. `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\discuss003.tex`
9. `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\conclusion002.tex`
10. `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\appendix002.tex`
11. `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\writing_manu2.bib`

**Figure files (15, opened and visually inspected directly):**
1. `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\figures\studyarea_082026_dpi150.png`
2. `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\figures\fig1_cross_section_lowres.png`
3. `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\figures\fig_composite_ms2_dataset_TUKU.png`
4. `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\figures\TUKU_overview_dual_axis_gwlkriged.png`
5. `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\figures\fig_results_delayed_cycle_timeline.pdf`
6. `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\figures\fig_results_delayed_monthly_estimates_s1_s3.pdf`
7. `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\figures\fig_results_delayed_monthly_estimates_s4_s6.pdf`
8. `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\figures\fig_results_delayed_prediction_vs_observed.pdf`
9. `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\figures\fig_results_reduced_frequency_6month_s1_s3.pdf`
10. `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\figures\fig_results_reduced_frequency_6month_s4_s6.pdf`
11. `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\figures\fig_results_reduced_frequency_12month_s1_s3.pdf`
12. `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\figures\fig_results_reduced_frequency_12month_s4_s6.pdf`
13. `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\figures\fig_results_no_subsequent_mlcw_monthly_errors_s1_s3.pdf`
14. `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\figures\fig_results_no_subsequent_mlcw_monthly_errors_s4_s6.pdf`
15. `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\figures\fig_results_no_subsequent_mlcw_cumulative_error.pdf`

**Required-reading inputs (2):**
1. `D:\112_PROJECT_002\AGENTS.md`
2. `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\modifications\20260831_third_party_proofreading_report.md`

**Build output additionally inspected (not a source file; created by the required build step):**
`D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\main.pdf` — physical pages 1–14, 32–33, 39–41, and 46–49 were opened and visually reviewed; `main.log` and `main.bbl` were inspected in full.

SECOND_PROOFREADING_COMPLETE_20260901
