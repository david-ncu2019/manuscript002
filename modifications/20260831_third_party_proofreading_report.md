# Third-Party Proofreading Report

**Manuscript:** Bayesian ridge regression estimation of monthly deformation within six depth sections at the Tuku multilayer compaction monitoring well (MLCW) station, Choushui River Alluvial Fan, Taiwan.
**Worktree:** `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\` (branch `reduced_v1`)
**Scope reviewed:** `main.tex`, `sections/abbreviations.tex`, `sections/intro002.tex`, `sections/studyarea002.tex`, `sections/dataset003.tex`, `sections/methods006.tex`, `sections/results004.tex`, `sections/discuss003.tex`, `sections/conclusion002.tex`, `sections/appendix002.tex`, `writing_manu2.bib`.
**Reviewer role:** independent, read-only third-party proofread. No manuscript source file was edited during this review.

---

## Post-review resolution log

**Status updated:** 2026-09-01
**Purpose:** This log records actions taken after the read-only review. The original findings below remain unchanged as an audit record.

| Finding | Status | Resolution or decision |
|---|---|---|
| C-1 | **Resolved** | Corrected `mstationagnetic` to `magnetic` in the Figure 4 caption in `sections/dataset003.tex`. |
| M-1 | **Resolved** | Added a body-text reference to Figure 1 when the study area is introduced in `sections/studyarea002.tex`. |
| M-2 | **Resolved** | Added body-text references to Figures 3 and 4 in `sections/dataset003.tex`, where the lithological profile and monthly time series are described. |
| M-3 | **Resolved** | Replaced `compaction` with `deformation` where the Methods text refers to the modeled response or its previous observations. Uses of `compaction` for the physical sediment process were preserved. |
| M-4 | **Reviewed; no change requested** | The two uses of `yielded` were inspected. The author chose to keep them because both contexts are unambiguous and the term occurs only twice in the active manuscript. |
| M-5 | **Resolved** | Added a citation for the 38\% rice-production statement. Replaced the unsupported phrase `more than 90 GWL stations` with the sourced count of 95 stations and added `\citep{nguyen_quantitative_2024}`. |
| M-6 | **Resolved** | Re-encoded the organizational author as `{{Central Geological Survey}}` and replaced the raw Zotero note with `Water Resources Bureau Report, 130 pp.` in `writing_manu2.bib`. |
| m-1 | **Reviewed; no change requested** | The author chose to preserve the two introductory participial constructions and the eight grammatical gerund subjects. |
| m-2 | **Reviewed; no change requested** | The author chose to preserve the six sentences beginning with an infinitive of purpose. |
| m-3 | **Reviewed; no change requested** | The author chose to preserve the existing `mm/month` notation rather than apply a manuscript-wide unit-formatting change. |
| m-4 | **Resolved** | Removed the empty BibTeX entry and stray closing brace, and corrected the organizational-author encoding. |
| AD-1 | **Resolved** | Verified the frozen 38-variable manifest. The Methods prose and Table 2 now distinguish 10 hydraulic-head variables for the section being estimated from 18 profile variables formed by three summaries for each of all six sections. |
| Citation-support spot-check 2 | **Resolved** | A post-review reading of Herrera-García et al. (2021) confirmed that 19\% refers to the initial assessment of 1.2 billion inhabitants in areas with high or very high potential subsidence, whereas the separate 2040 projection reaches 1.6 billion inhabitants. The Introduction now distinguishes the initial percentage from the projected increase by 2040. |

After these corrections, the complete `pdflatex`, `bibtex`, `pdflatex`, `pdflatex` sequence produced a 58-page PDF with no undefined references or citations. Existing box warnings remain non-blocking.

---

## 1. Executive summary

The manuscript builds cleanly, has zero undefined references or citations, and its numeric claims in Results, Discussion, and Conclusions are internally consistent — every range and value checked against Tables 4–9 matched exactly. The most important defect is a single garbled word ("mstationagnetic") that appears twice in the compiled PDF, once in the List of Figures and once in the actual Figure 4 caption. The next most important issue is that the Methods section uses "compaction" as a loose synonym for the modeled response variable in its opening paragraph and once more at line 36, while every other active section (Results, Discussion, Conclusions, Introduction) calls that same quantity "deformation" without exception — this is the one terminology inconsistency in an otherwise disciplined manuscript. A genuine, unresolved internal contradiction exists in how many depth sections make up the 18-variable "profile" predictor group (Methods and Table 2 say "the other five sections," Appendix and its own equation notation say "each of the six depth sections" / a section-independent subscript) — this is listed under Author decision required, not resolved here. Two figures (Figure 1 and Figures 3–4) are never cited in the body prose of `studyarea002.tex` and `dataset003.tex`, only from within other figures' captions or not at all. Two quantitative claims lack an adjacent citation. A reference-list entry contains raw Zotero export metadata printed verbatim into the bibliography. All other findings are minor style/mechanics items, most of them recurring sentence-opener patterns that are defensible scientific phrasing rather than clear errors.

---

## 2. Build results

Commands run, in order, from the worktree root:

```
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

All four steps completed with exit code 0. Result: `main.pdf`, 58 pages.

- **Undefined references:** none. `main.log` contains no "Reference ... undefined" or "Citation ... undefined" warnings after the final pass.
- **Bibtex:** `main.blg` reports 0 warnings, 0 errors. "You've used 56 entries" — matches the count of distinct `\citep`/`\citet` keys actually used in the 11 in-scope `.tex` files (confirmed by extracting all used keys and diffing against `writing_manu2.bib` entry keys; zero keys used but missing from the `.bib`, zero keys in the `.bib` and cited but somehow unresolved).
- **Remaining warnings (non-blocking):**
  - Several underfull/overfull `\hbox` warnings from `sections/abbreviations.tex`'s abbreviation table, `methods006.tex` Table 2 cells, the sideways Table 6 in `results004.tex`, and a citation line-break around `methods006.tex:204–205`.
  - Two overfull-box warnings inside `main.bbl` from the Chaussard entries' title text wrapping.
  - These are typesetting-tightness warnings only; nothing renders as visibly broken text, garbled spacing, or a clipped column in the corresponding PDF pages (checked directly).

No build failure. No missing figure files. No citation could not be resolved.

---

## 3. PDF visual QA

Checked: legibility, cropped/clipped figures, caption separated from its figure/table by a page break, orphaned headings, figure/table citation order vs. appearance order, unusual whitespace, and any visible placeholder text in the rendered output.

- **Critical:** the word "mstationagnetic" (garbled "magnetic") renders exactly as written in the source, twice: once in the List of Figures (document page iii) and once in the live Figure 4 caption (document page 10). No short-caption override exists for this figure, so both renderings inherit the typo from the single `\caption{}` command. See Finding C-1 below.
- Figures 6–8 (the large tikz experimental-design diagrams in `methods006.tex`) render at readable size with no clipping and no caption/figure page-break separation.
- Table 6 (sideways table, `results004.tex`) renders correctly rotated and fully legible; no content runs off the page edge.
- No caption is visually separated from its figure or table by a page break in any of the reviewed sections.
- No orphaned section headings (a heading alone at the bottom of a page with its first paragraph pushed to the next page) were found.
- No visible `\placeholder{...}` text appears anywhere in the rendered body of the 8 active sections. Placeholder text is visible only in the front matter (Abstract, Acknowledgements, Author contributions, Data availability, Conflict of interest) — these are known, already-tracked open items per the manuscript status table, not new findings.
- **Figure/table citation order:** checked mechanically (every `\label{fig:...}`/`\label{tab:...}` cross-referenced against every `\Cref`/`\ref` occurrence, by line number, across the 11 in-scope files). Two figures are never cited from body prose — see Findings M-1 and M-2 below. All other figures and tables are cited in prose before or at their first appearance, in ascending numeric order.

---

## 4. Findings by severity

### Critical

**C-1 — Garbled word in figure caption, renders twice in the compiled PDF**
- Error type: typo / garbled text
- File: `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\dataset003.tex`
- Line: 40
- Verbatim excerpt: `The left axis shows cumulative vertical surface displacement from the TKJS cGNSS station and cumulative deformation recorded by all mstationagnetic rings at the Tuku MLCW station.`
- Minimal proposed fix: change `mstationagnetic` to `magnetic`.
- Rationale: this is the caption of Figure 4, a load-bearing figure showing the primary deformation and hydraulic-head time series. The typo is visible to any reader in both the List of Figures and the figure caption itself; it has no other occurrence in the manuscript, confirming it is an isolated slip rather than a naming convention.

### Major

**M-1 — Figure 1 is never cited from body prose**
- Error type: figure-citation order / missing in-text reference
- File: `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\studyarea002.tex`
- Line: label at 14 (`\label{fig:studyarea_a}`); the only `\Cref{fig:studyarea_a}` in the entire in-scope source set is inside Figure 2's own caption at line 20, not in body prose.
- Verbatim excerpt (Figure 2's caption, the only place Figure 1 is referenced): `Regional hydrogeological cross-section along the A-A$'$ transect shown in \Cref{fig:studyarea_a}, from A (west, distal fan) to A$'$ (east, proximal fan), based on lithological logs from eleven boreholes across the CRAF.`
- Minimal proposed fix: add one `\Cref{fig:studyarea_a}` citation in the body prose of Section 2 (e.g., alongside the existing sentence introducing the study area map).
- Rationale: Copernicus/NHESS and standard scientific-writing convention require every figure to be introduced in the body text before or at its first appearance; a figure that is discoverable only through another figure's caption is effectively uncited.

**M-2 — Figures 3 and 4 are never cited from body prose**
- Error type: figure-citation order / missing in-text reference
- File: `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\dataset003.tex`
- Lines: labels at 34 (`\label{fig:tuku_observations_a}`) and 41 (`\label{fig:tuku_observations_b}`)
- Verbatim excerpt: no `\Cref{fig:tuku_observations_a}` or `\Cref{fig:tuku_observations_b}` occurs anywhere in the 11 in-scope files (confirmed by exhaustive grep for both label strings). Body prose at line 44 cites only `\Cref{fig:tuku_data_workflow}` (Figure 5) and `\Cref{tab:tuku_data_sources}` (Table 1).
- Minimal proposed fix: add `\Cref{fig:tuku_observations_a}` and `\Cref{fig:tuku_observations_b}` at the appropriate points in the surrounding prose (e.g., in the "Multilayer aquifer-system deformation" and "Vertical surface displacement" subsections that describe the content each figure shows).
- Rationale: same convention as M-1; both figures currently appear in the PDF with no textual introduction pointing the reader to them.

**M-3 — Terminology drift: "compaction" used as a synonym for the modeled response variable, only in Methods**
- Error type: terminology inconsistency (pattern, 3 occurrences)
- Files/lines:
  - `sections/methods006.tex:1` (two instances): `...used them to estimate monthly compaction within each depth section, relating measured changes in hydraulic head and vertical surface displacement to the observed compaction.`
  - `sections/methods006.tex:36`: `...keeping every section's estimate independent of its own past compaction record.`
- Minimal proposed fix: replace "compaction" with "deformation" in these three instances (`monthly compaction` → `monthly deformation`; `observed compaction` → `observed deformation`; `past compaction record` → `past deformation record`).
- Rationale: confirmed by cross-file search (`\bcompaction\b`) that `results004.tex`, `discuss003.tex`, `conclusion002.tex`, and `intro002.tex` never use "compaction" for the estimated/modeled quantity — they use "deformation" exclusively and reserve "compaction" for the physical process of permanent sediment volume loss (e.g., studyarea002.tex:8, intro002.tex:5). Methods006.tex is the sole outlier, and both instances at line 1 occur in the section's opening paragraph, where a reader first learns what the model estimates.

**M-4 — Forbidden word "yielded" (pattern, 2 occurrences)**
- Error type: forbidden word
- Files/lines:
  - `sections/results004.tex:7`: `This evaluation covered 23 complete cycles from 05/2013 to 10/2024 and yielded 138 estimates for each section.`
  - `sections/methods006.tex:28`: `Corresponding differences in the cGNSS series yielded monthly vertical surface displacement increments.`
- Minimal proposed fix: replace "yielded" with "produced" or "gave" in both instances.
- Rationale: "yield" is on the project's explicit forbidden-word list (banned completely per `domain.md`).

**M-5 — Two quantitative claims lack an adjacent citation**
- Error type: unsupported quantitative claim
- File: `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\studyarea002.tex`
- Line: 8
- Verbatim excerpt: `The CRAF is one of Taiwan's major agricultural regions and accounts for approximately 38\% of the country's rice production.`
- The citation `\citep{chang2022_wetanddry, chang_rice-field_2020}` is attached to the following sentence about seasonal water demand timing, not to this sentence.
- Minimal proposed fix: attach a citation to the 38% rice-production figure, or move the existing citation to cover both sentences if the same sources support both claims.
- Rationale: a specific national-scale statistic needs a traceable source.

- File: `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\dataset003.tex`
- Line: 18
- Verbatim excerpt: `The regional monitoring network comprised more than 90 GWL stations operated by the Water Resources Agency of Taiwan.`
- The citation `\citep{survey_project_1999, liu_characterization_2004}` is attached to the following sentence about nested observation wells, not to this sentence.
- Minimal proposed fix: attach a citation to the "more than 90 GWL stations" claim, or extend the existing citation to cover it.
- Rationale: same as above — a specific count needs a traceable source.

**M-6 — Reference-list entry contains raw export metadata**
- Error type: malformed bibliography entry
- File: `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\writing_manu2.bib`
- Lines: 491–499 (`survey_project_1999` entry)
- Verbatim excerpt: `note = {Pages: 130\nPublication Title: Water Resources Bureau Report}`
- Confirmed this prints verbatim into reference [47] on the compiled PDF (document-printed page 53 / physical PDF page 57): "...Research report of Choushui River alluvial fan, 1999. Pages: 130 Publication Title: Water Resources Bureau Report."
- Minimal proposed fix: remove the `note` field or replace it with a proper `pages`/`journal` field pair; this looks like unedited Zotero-export text left in the `note` field.
- Rationale: this text is visible to any reader of the reference list and looks like an editing artifact rather than intended bibliographic content.

### Minor

**m-1 — Sentence-initial dangling/introductory participial phrases ("-ing" gerund subjects and true participial openers)**

This pattern splits into two sub-patterns of different strength, per the project's own diagnostic-flag guidance (a flag requiring inspection, not an automatic violation):

*Sub-pattern (a) — introductory participial phrase modifying the following clause's subject (closer to the banned construction):*
- `sections/studyarea002.tex:4`: `Covering $\sim$2,000~km$^2$ across Changhua and Yunlin counties, the fan is bounded by the Wu River to the north...`
- `sections/studyarea002.tex:6`: `Based on its hydrogeological characteristics, the fan is commonly divided into proximal, middle, and distal zones \citep{survey_project_1999}.`

*Sub-pattern (b) — gerund used as a grammatical subject (standard scientific-English construction, defensible):*
- `sections/dataset003.tex:4`: `Estimating deformation within individual depth intervals required observations of deformation by depth together with monthly hydraulic head and surface displacement records.`
- `sections/intro002.tex:9`: `Obtaining this information requires a dedicated borehole, investigations of subsurface materials, and repeated observations throughout MLCW operation \citep{hung_measuring_2021,hung2025_realtime}.`
- `sections/discuss003.tex:46`: `Reducing the measurement frequency did not change monthly error in the same direction across all tested scenarios.`
- `sections/discuss003.tex:50`: `Extending the initial record from 3 to 5 and then 8 years did not produce a monotonic reduction in monthly MAE.`
- `sections/discuss003.tex:95`: `Applying the framework elsewhere would require the same evaluation for each depth section...`
- `sections/results004.tex:215`: `Extending the initial record from three to eight years therefore did not consistently reduce monthly estimation error.`
- `sections/methods006.tex:325`: `Representing this observation within the monthly regression required the relation in \Cref{eq:brr_regression,eq:brr_likelihood} to be accumulated over the same interval.`
- `sections/methods006.tex:414`: `Matching the evaluated months and depth sections prevented differences in the available observations from being mistaken for effects of measurement frequency or the length of the initial record.`
- `sections/appendix002.tex:90`: `Reading $R_{\sigma,s}$ and $\rho_s$ together distinguishes estimates that reproduce the observed variability from estimates that reproduce only part of its temporal pattern.`

Approximate total occurrences: 10 (2 in sub-pattern a, 8 in sub-pattern b).
Minimal proposed fix: for sub-pattern (a), recast with an explicit subject (e.g., "The fan covers ~2,000 km²... and is bounded by..."; "The fan is commonly divided into... based on its hydrogeological characteristics."). Sub-pattern (b) is standard technical usage and is flagged here for completeness only; no fix is proposed unless the author wants uniform enforcement of the zero-"-ing"-opener rule.
Rationale: the project style guide bans "V-ing..." sentence openers; sub-pattern (a) is the clearer case of a dangling/introductory participial phrase, while sub-pattern (b) (gerund-as-subject) is common, unambiguous scientific English and does not impede comprehension.

**m-2 — Sentence-initial "To V..." infinitive-of-purpose openers (pattern, 6 occurrences)**
- `sections/studyarea002.tex:8`: `To meet this seasonal demand, annual groundwater extraction has been estimated at 1.71 to 2.05 billion~m$^3$~yr$^{-1}$ \citep{tseng_estimating_2024}...`
- `sections/dataset003.tex:20`: `To place these observations on the same monthly time scale as the MLCW measurements, daily hydraulic heads were averaged within each month.`
- `sections/results004.tex:52`: `To summarize these differences without reproducing all model coefficients, \Cref{tab:selected_coefficients} presents 14 variables...`
- `sections/methods006.tex:316`: `To represent this cumulative observation mathematically, let $s$ denote a depth section...`
- `sections/methods006.tex:354`: `To fit the cumulative observation together with the original monthly observations, both observation types were placed on the same residual variance scale.`
- `sections/methods006.tex:569`: `To account for the increasing duration of the estimation period, the absolute cumulative error was also expressed per month as`
- Minimal proposed fix: recast each opener around the sentence's main actor or result if the author wants the rule enforced uniformly; not required for comprehension in any of these six instances.
- Rationale: the project style guide bans "To V..." sentence openers. Flagged as a pattern per the severity-discipline instruction; none of these six instances is ambiguous or hard to read.

**m-3 — Unit-format inconsistency: slash notation vs. Copernicus house-style negative-exponent notation**
- Error type: house-style / internal consistency
- File: `sections/studyarea002.tex`, line 8: `annual groundwater extraction has been estimated at 1.71 to 2.05 billion~m$^3$~yr$^{-1}$` (negative-exponent form, matches Copernicus house style).
- Contrast: `mm/month` (slash form) is used 32 times across the in-scope files — `methods006.tex` (4, including Table 3's metric-unit column), `results004.tex` (18), `discuss003.tex` (6), `conclusion002.tex` (4).
- Representative examples: `methods006.tex:191–195` (Table 3 unit column), `results004.tex:41`, `discuss003.tex:13`, `conclusion002.tex:1`.
- Minimal proposed fix: standardize on one unit-formatting convention throughout (Copernicus manuscript-preparation guidance specifies negative exponents rather than slashes for compound units, which would mean changing `mm/month` to `mm~month$^{-1}$` throughout).
- Rationale: the manuscript currently mixes two different unit-formatting conventions; Copernicus/NHESS house style specifies the negative-exponent form, and `mm/month` is by far the more frequently used form in this manuscript, so the inconsistency is more visible than its single counter-example.

**m-4 — Bibliography syntax hygiene (not affecting the build)**
- File: `writing_manu2.bib`
- Line 558: an empty, malformed entry `@techreport{noauthor_notitle_nodate,\n}` with no fields at all.
- Line 705: a stray extra closing brace after the properly closed `gambolati_2015` entry (harmless — ignored by bibtex between entries — but a syntax hygiene defect).
- Line ~491 (`survey_project_1999` author field): `author = {Survey, Central Geological}` — non-standard organizational-author encoding; renders correctly as "Central Geological Survey" only by coincidence of `plainnat.bst`'s single-author "Last, First" parsing. The standard encoding for an organization as author is double-braced, `{{Central Geological Survey}}`.
- Minimal proposed fix: delete the empty `noauthor_notitle_nodate` entry (it is also unused — see bibliography inventory below); remove the stray brace at line 705; change `author = {Survey, Central Geological}` to `author = {{Central Geological Survey}}`.
- Rationale: none of these three items currently causes a visible defect in the compiled bibliography, but all three are technically malformed BibTeX and worth cleaning up before submission.

---

## Author decision required

**AD-1 — Predictor-count discrepancy: "other five sections" vs. "each of the six depth sections" for the 18-variable profile predictor group**

Two internally inconsistent descriptions exist for the same 18-variable predictor block:

- `sections/methods006.tex:34`: `Current and lagged hydraulic head changes from the target section and the other five sections were then included as candidate predictors to represent hydraulic conditions throughout the monitored profile.`
- `sections/methods006.tex:50` (Table 2, "Hydraulic head in other sections" row): `Current and lagged hydraulic head changes, other five sections` / `Hydraulic conditions in the other monitored depths`
- `sections/appendix002.tex:24`: `The remaining 18 variables described hydraulic conditions across the monitored profile using the current head change and its three- and six-month rolling means for each of the six depth sections.`

Supporting evidence from the equation notation itself, `sections/appendix002.tex:9–20` (Equation 23):
```
\boldsymbol{x}_{s,k} = [ \boldsymbol{x}^{surface}_{k}, \boldsymbol{x}^{head}_{s,k}, \boldsymbol{x}^{season}_{s,k}, \boldsymbol{x}^{profile}_{k} ] \in \mathbb{R}^{4+10+6+18} = \mathbb{R}^{38}
```
The profile block carries subscript $k$ only (no $s$), unlike the head and season blocks, which both carry $s,k$. A block that varies with which section $s$ is being modeled (i.e., a block that excludes the target section) would need to carry the $s$ subscript to know which section to exclude; a block written with $k$ only is, by the model's own notation, identical regardless of which section is being estimated. Separately, 18 = 3 variables × 6 sections is the only decomposition consistent with the stated total of 38 = 4 + 10 + 6 + 18; 3 variables × 5 sections would give 15, not 18.

This is a genuine internal contradiction between the Methods prose/Table 2 ("other five sections") and the Appendix prose/equation notation ("each of the six depth sections," section-independent indexing). No resolution is proposed here per review scope; the author should confirm which description matches the actual fitted models and correct the other two.

---

## 5. Bibliography inventory

**Unused entries (informational only, no deletion recommended):** 30 of 86 total `.bib` entries are not cited anywhere in the 11 in-scope `.tex` files:

`angelopoulos_conformal_2023, berardino_new_2002, doin_corrections_2009, egozcue_isometric_2003, fattahi_network-based_2017, faunt_groundwater_2009, ferretti_nonlinear_2000, fuhrmann_resolving_2019, geudtner_sentinel-1_2012, gsmma_3d, hanssen_radar_2001, hoaglin_hat_1978, hogenson_hybrid_2025, hung2017_chiayi, hurvich_smoothing_2002, nguyen_quantitative_2024, noauthor_notitle_nodate, oh_using_2024, pepe_extension_2006, perissin_repeat-pass_2012, rosen_insar_2012, scikit-learn, snoeij_sentinel-1_2008, torres_gmes_2012, tough_statistical_1995, wang_2014, yague-martinez_interferometric_2016, yang_surface_2019, yunjun_small_2019, zaffran_adaptive_2022`

Several of these (e.g., `angelopoulos_conformal_2023`, `zaffran_adaptive_2022`) are conformal-prediction literature — consistent with the manuscript's decision to report Bayesian posterior predictive intervals rather than conformal intervals, so their absence from the citation list is expected, not an oversight.

**Duplicate entries:** none found (checked by sorting and comparing all `doi = {...}` field values across all 86 entries; no duplicate DOI).

**Malformed entries:** see Findings M-6 and m-4 above (`survey_project_1999` note-field metadata; empty `noauthor_notitle_nodate` entry; stray brace after `gambolati_2015`; non-standard organizational-author encoding).

56 of 86 entries are cited and used; this matches BibTeX's own reported count exactly.

---

## 6. Citation-support spot-check

Sample prioritized strong/surprising claims, per review scope.

1. **`hung2025_realtime`**, cited in `discuss003.tex:38` and `intro002.tex:16` (in a sentence describing a related study that forecast short-term vertical deformation from a high-frequency extensometer record and compared results against MLCW observations at corresponding depths). Verified against the source PDF (`Hung et al. - 2025 - Near real-time subsidence monitoring and AI forecasting with multi-depth extensometers.pdf`, pages 1–3): the source paper's stated methodology and results strongly and directly support the adjacent claim. No discrepancy found.

2. **`herrera-garcia_mapping_2021`**, cited in `intro002.tex:1` for the claim "By 2040, as much as 19% of the global population may live in areas with a high probability of subsidence." No local PDF copy of this source was found in the Zotero storage library on disk (`D:\001_LITERATURE_v2\ZOTERO_storage\storage\...`, searched via filename match, no result). The 19% figure is independently referenced (without the specific "2040" qualifier) inside the already-verified `hung2025_realtime` source's own citation of the same statistic, which provides indirect secondary support for the magnitude of the number but not for the specific "by 2040" timeframe. **Support could not be independently verified for the exact "2040" qualifier** — the full text of `herrera-garcia_mapping_2021` itself was not reachable from local files during this review.

No other citation received a full-text verification pass within the scope of this review; the two above were selected as the strongest/most consequential claims among the citations checked.

---

## 7. Finding-count summary

| Severity | Count | Notes |
|---|---|---|
| Critical | 1 | Garbled word in Figure 4 caption, renders twice in PDF |
| Major | 6 | 2 uncited figures, 1 terminology-drift pattern (3 occurrences), 1 forbidden-word pattern (2 occurrences), 2 uncited quantitative claims, 1 malformed bib entry |
| Minor | 4 | 2 sentence-opener patterns (10 + 6 occurrences), 1 unit-format inconsistency (32 vs. 1 occurrence), 1 bib-syntax-hygiene group (3 items) |
| Author decision required | 1 | Predictor-count discrepancy ("other five sections" vs. "each of the six depth sections") |

Total individual findings (counting each pattern once): **12**, covering roughly 56 discrete instances across the manuscript when pattern occurrences are expanded.

---

## 8. Confirmation: no manuscript source file modified

No `.tex` or `.bib` file listed in the review scope was created, edited, deleted, moved, or renamed during this review. The following build artifacts were created in `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\` as an expected, unavoidable side effect of running the required `pdflatex`/`bibtex` build commands, and are not manuscript edits: `main.aux`, `main.log`, `main.bbl`, `main.blg`, `main.pdf`, `main.toc`, `main.lof`, `main.lot`. The only new content file written by this review is this report, at the exact path `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\modifications\20260831_third_party_proofreading_report.md`. No `% NOTE`, `% my note`, `% AUTHOR RESPONSE`, or `% AUTHOR NOTE` comment line was altered or removed in any reviewed file. No git command that changes repository state was run.

PROOFREADING_COMPLETE_20260831
