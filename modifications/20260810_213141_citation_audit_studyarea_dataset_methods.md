# Citation Audit — studyarea002.tex, dataset003.tex, methods005.tex
Generated: 2026-08-10

**Scope note:** A prior audit pass (dated 2026-08-10 22:25, preserved in git history of this file)
already closed several gaps by adding `wang_2014`, `bevis_2014`, `theodossiou2006`,
`hoerl_1970_ridge`, and `mackay_bayesian_1992` to the relevant sentences. Confirmed present in the
current file text read for this audit. This pass re-reads the files as they stand now, so the lists
below reflect what is **still** missing or **could still be strengthened**, not a repeat of already-
fixed items.

**Forbidden-terms check:** none of the three files contain `Sentinel-1`, `InSAR`, `SBAS`, `3D model`,
`spatial transfer`, or `level1b`. No separate issue to flag on that count.

---

## 1. studyarea002.tex

### 1.1 Line 8 — effective-stress / compaction mechanism sentence
> "The resulting hydraulic head decline reduces pore-fluid pressure, transfers a greater share of
> the overburden load to the sediment skeleton, and increases effective stress. This stress increase
> compacts susceptible fine-grained aquitards and interbeds and contributes to land subsidence in
> these parts of the fan \citep{liu_characterization_2004, hung2015_multiple, gambolati_2015}."

- **Why it needs attention:** this sentence states the core physical mechanism of aquifer-system
  compaction (effective-stress principle, Terzaghi consolidation logic) as a general geomechanical
  law, not a Taiwan-specific finding. The three citations given are regional/applied papers. The
  foundational mechanism itself — effective stress transferring load to the grain skeleton and
  driving consolidation of fine-grained material — traces to Terzaghi's consolidation theory, and
  the land-subsidence-specific version of it is most commonly credited to Poland and colleagues (USGS
  subsidence work) or a land-subsidence review such as Galloway.
- **Suggested source type:** the classical consolidation-theory reference (Terzaghi 1925) or a
  foundational U.S. Geological Survey land-subsidence mechanism reference. High-confidence known
  candidates already in this project's own `writing_manu2.bib`: `poland_guidebook_1984` (Poland,
  *Guidebook to studies of land subsidence due to ground-water withdrawal*, 1984) and
  `galloway_land_1999` (Galloway, Jones & Ingebritsen, *Land Subsidence in the United States*, 1999,
  USGS Circular 1182) — both keys exist in the bib file but are **not cited anywhere in
  studyarea002.tex**. Either would be an appropriate zero-new-lookup addition to this sentence.
  `faunt_groundwater_2009` (Central Valley groundwater/subsidence synthesis) is a secondary option if
  a second regional analog is wanted.
- **Severity:** Medium — the sentence is not unsupported (three citations already appear), but the
  mechanism claim itself would be better anchored by a foundational consolidation/subsidence-theory
  citation rather than only regional Taiwan papers.

### 1.2 Line 6 — "commonly divided into proximal, middle, and distal zones"
> "Based on its hydrogeological characteristics, the fan is commonly divided into proximal, middle,
> and distal zones \citep{survey_project_1999}."

- **Why it needs attention:** "commonly divided" is a best-practice/standard-terminology claim
  (alluvial fan zonation is a broader geomorphological convention, not unique to this survey report).
  A single technical-survey citation supports the CRAF-specific zonation but not the generality of
  the term.
- **Suggested source type:** this is a minor point. If the phrase "commonly divided" is meant
  narrowly (i.e., "in prior work on this fan"), the existing citation is sufficient — flag as
  low-severity only. No specific alternate source recommended; not worth adding weight here unless a
  reviewer objects.
- **Severity:** Low.

### 1.3 Line 8 — "38% of the country's rice production" and extraction volume figures
> "The CRAF is one of Taiwan's major agricultural regions and accounts for approximately 38\% of the
> country's rice production \citep{chang2022_wetanddry}. Annual groundwater extraction has been
> estimated at 1.71--2.05 billion~m$^3$~yr$^{-1}$ \citep{tseng_estimating_2024}."

- **Why it needs attention:** not a gap — both quantitative claims already carry a specific citation
  each. Flagging only to note: verify the 38% figure is the number actually reported in
  `chang2022_wetanddry` and not from a different source that got dropped during editing (a common
  silent-error pattern when numbers move between drafts).
- **Severity:** Low / verification only, not a missing-citation issue.

### Summary for studyarea002.tex
This section is already densely and appropriately cited. The one substantive gap is the missing
foundational consolidation/subsidence-mechanism citation at line 8 (Section 1.1 above).

---

## 2. dataset003.tex

### 2.1 Line 4 — MLCW measurement-delay / data-provider workflow description
> "Deformation within individual subsurface depth intervals was measured monthly using specialized
> borehole extensometer systems known as multilayer compaction monitoring wells (MLCWs)... the data
> provider processed and checked the measurements before providing the finalized records."

- **Why it needs attention:** this describes a specific data-provider operational practice (QA/QC
  delay before release). This is inherently a provenance claim, not a general scientific claim — no
  journal article can substitute for a data-provider statement or technical documentation describing
  the QA workflow.
- **Suggested source type:** data-availability statement, provider technical documentation, or a
  footnote citing the responsible Taiwan agency (e.g., Central Geological Survey / Water Resources
  Agency) rather than a peer-reviewed paper. Not a literature-search task — a provenance/documentation
  task instead.
- **Severity:** Medium (methodologically important for reproducibility, but not fixable via
  literature search).

### 2.2 Line 10 — MLCW instrumentation description (magnetic anchor rings, 1 mm precision)
> "The MLCW recorded relative vertical displacement at multiple depths through magnetic anchor rings
> installed along the borehole to a depth of approximately 300~m. Relative displacement between
> adjacent rings represented compaction within the corresponding ring intervals, with a measurement
> precision of 1~mm \citep{hung_measuring_2021}."

- **Why it needs attention:** this is a claim about instrument design (magnetic-ring extensometer
  technology) attributed to one paper. The MLCW/magnetic-extensometer design as used in Taiwan has an
  older instrumentation lineage than Hung et al. (2021) alone.
- **Suggested source type:** a citation candidate already exists in this project's own bib file and
  is currently **unused** in this section: `hung2012_mlcw`. Given the naming, this is very likely the
  earlier Hung et al. (2012) paper describing MLCW instrumentation/design specifically, which would
  pair naturally with `hung_measuring_2021` here (design paper + measurement-interpretation paper).
  This is the single clearest "citation exists in bib but is missing from the sentence" gap found in
  this section.
- **Severity:** High — a directly relevant, already-available key is not used here.

### 2.3 Line 14 — GWL network aquifer nomenclature ("Aquifers 1 through 4")
> "These stations generally consisted of nested observation wells screened at discrete depths to
> monitor hydraulic head in Aquifers 1 through 4 \citep{survey_project_1999, liu_characterization_2004}."

- **Why it needs attention:** not a true gap — already double-cited. Flagging only because the
  "Aquifer 1–4" naming convention is a specific regional stratigraphic nomenclature (Central
  Geological Survey convention); if a reader unfamiliar with Taiwan hydrostratigraphy needs to trace
  this scheme, a citation to the original aquifer-numbering scheme (likely inside
  `survey_project_1999` already) should be confirmed as the correct source, not merely assumed.
- **Severity:** Low / verification only.

### 2.4 Line 18 — cGNSS provenance and comparison to MLCW depth limit
> "Whereas the Tuku MLCW recorded deformation only to its deepest magnetic ring, installed at a depth
> of approximately 300~m, surface displacement also included deformation below this monitored depth
> \citep{hung_measuring_2021, wang_2014}."

- **Why it needs attention:** already adequately cited (both a design paper and a
  borehole-vs-GPS-depth-support paper). No action needed. Noted only for completeness.
- **Severity:** None — adequately supported.

### 2.5 Line 18 — cGNSS daily position time series source
> "Daily three-dimensional position time series from the adjacent TKJS cGNSS station provided the
> surface displacement observations used at Tuku \citep{IESAS_TGM_2026}."

- **Why it needs attention:** `IESAS_TGM_2026` supports data provenance (who supplied the cGNSS
  series), but the daily-position **processing** itself (how raw GNSS observations become a daily 3-D
  position time series) is a distinct methodological claim with its own literature. The bib file
  already contains `bock_physical_2016`, a plausible GNSS-processing/physical-reduction reference,
  which is not cited anywhere in this section.
- **Suggested source type:** if `bock_physical_2016` indeed concerns GNSS position time-series
  processing (title suggests "physical" corrections to GPS/GNSS coordinate time series), add it
  alongside `IESAS_TGM_2026` to distinguish "who provided the data" from "how the daily positions were
  derived."
- **Severity:** Medium — worth checking bock_physical_2016's actual title/abstract before adding, since
  the audit did not verify its content beyond the key name.

### 2.6 Line 22 — Borehole lithological profile / classification method
> "The source log identified the upper and lower boundaries of each logged interval and its
> corresponding sediment type... Sediment composition within each standardized section was then
> expressed as the proportions of gravel, coarse sand, fine sand, and fine-grained deposits comprising
> clay, silt, and mud."

- **Why it needs attention:** zero citations in this entire paragraph. Two distinct claims are made:
  (1) provenance of the borehole log itself (whose log, what agency/driller produced it), and (2) the
  grain-size classification scheme used to bin sediment into gravel/coarse sand/fine sand/fine-grained
  categories, which follows a standard geotechnical or sedimentological grain-size classification
  (e.g., Wentworth scale or a national geotechnical standard) that should be named and cited if a
  specific scheme was used.
- **Suggested source type:** (1) data-provenance citation for the borehole log (same
  agency/documentation category as item 2.1); (2) a grain-size classification standard reference if a
  named scheme (USCS, Wentworth, or a Taiwan CGS soil classification standard) was actually applied —
  only add this if the underlying scripts/methods indeed use a named standard; otherwise state
  explicitly that categories were assigned by the data provider's own log labels, needing no
  classification-standard citation.
- **Severity:** Medium-High — this is the largest citation-free paragraph making a semi-technical
  classification claim.

- **Important scope correction relative to task instructions:** the task prompt asked me to watch for
  ILR (isometric logratio) / Martín-Fernández zero-replacement / compositional-data-analysis
  citations, since lithology is expressed as proportions. **Neither dataset003.tex nor methods005.tex
  applies an ILR transform or any compositional-data closure method to these proportions** — the text
  only describes raw gravel/sand/fine-grained proportions used descriptively ("provided geological
  context for interpreting differences... among sections"), not as model inputs subjected to
  log-ratio transformation. No ILR/Aitchison/Martín-Fernández citation is needed here. Flagging this
  explicitly so the gap is not manufactured where none exists — if a later revision does add an ILR
  step (methods005.tex does not appear to at present), the Aitchison (1986) and Martín-Fernández et
  al. (2003) citations would become necessary at that point.

### Summary for dataset003.tex
One clear "citation exists but is unused" gap (2.2, `hung2012_mlcw`), one genuinely uncited paragraph
making a classification-adjacent claim (2.6), and two provenance-only gaps (2.1, 2.5) that need
documentation rather than literature citations.

---

## 3. methods005.tex

### 3.1 Line 1 — opening summary sentence (no citation, likely fine)
> "Separate Bayesian ridge regression models then related each section's monthly deformation
> increments to hydraulic head changes, vertical surface displacement, and seasonal variation."

- **Why flagged:** this is a scene-setting summary sentence restating the section's own method; the
  actual Bayesian ridge regression citations appear later (§3.3, confirmed present:
  `hoerl_1970_ridge`, `mackay_bayesian_1992`). No separate citation needed here — noted only to
  confirm it was checked, not a real gap.
- **Severity:** None.

### 3.2 Line 34 — kriging citation strength
> "For the remaining sections, hydraulic head at Tuku was estimated from the regional monitoring
> network using ordinary kriging \citep{theodossiou2006}."

- **Why it needs attention:** `theodossiou2006` is confirmed present (an applied groundwater-network
  kriging paper, per the prior audit's citation check). This is an applied paper, not the foundational
  geostatistics reference for ordinary kriging itself (e.g., Matheron's original formulation, or a
  standard geostatistics textbook such as Cressie 1993 or Goovaerts 1997).
- **Suggested source type:** optional — a foundational geostatistics text citation (Cressie 1993,
  *Statistics for Spatial Data*, or Goovaerts 1997, *Geostatistics for Natural Resources Evaluation*)
  alongside the applied paper, if the target journal expects the method's origin rather than only an
  application example. Not urgent since an applied citation already exists.
- **Severity:** Low — nice-to-have, not a hard gap.

### 3.3 Line 59, sklearn / scikit-learn implementation citation — genuinely missing
> "Ridge regression limits this sensitivity by reducing the magnitude of coefficients that are weakly
> supported by the observations \citep{hoerl_1970_ridge}." ... (§3.3 more broadly describes fitting
> via marginal-likelihood hyperparameter estimation, consistent with the standard
> `BayesianRidge` implementation pattern.)

- **Why it needs attention:** the bib file already contains a `scikit-learn` key (the standard
  Pedregosa et al. 2011 JMLR software citation), but **it is not cited anywhere in methods005.tex**.
  If the actual Bayesian ridge regression was fitted using scikit-learn's `BayesianRidge` class (the
  hyperparameter estimation procedure described — maximizing marginal likelihood for $\alpha_s$ and
  $\lambda_s$ — matches sklearn's documented algorithm almost exactly), software-citation convention
  requires citing the toolkit used, separate from citing the statistical method (Hoerl & Kennard;
  MacKay).
- **Suggested source type:** the existing `scikit-learn` bib key — add `\citep{scikit-learn}` at the
  point where the Bayesian ridge regression is first introduced (§3.3 opening) or in a
  software/implementation statement, **only if scikit-learn was in fact the implementation used**
  (verify against the actual analysis scripts before adding — do not cite a toolkit that was not
  used).
- **Severity:** High if scikit-learn was used (likely, given the project's Python/NumPy/SciPy stack
  noted elsewhere in this repository) — currently an unused, directly relevant key sitting in the bib
  file.

### 3.4 Line 178 — interval width vs. coverage trade-off
> "Both measures were examined because a wider interval may enclose more observations while providing
> less precise information \citep{singh_uncertainty_2024}."

- **Why it needs attention:** already cited; flagged only to note that this general
  sharpness-vs-coverage trade-off is also the subject of a well-known, frequently-cited proper-scoring
  literature (e.g., Gneiting & Raftery on proper scoring rules, or Gneiting, Balabdaoui & Raftery 2007
  on probabilistic forecast calibration and sharpness). Consider whether `singh_uncertainty_2024`
  alone is sufficiently authoritative for this general statistical principle, or whether the target
  journal's reviewers will expect the foundational calibration/sharpness reference alongside it.
- **Suggested source type:** Gneiting & Raftery (2007), *Strictly Proper Scoring Rules, Prediction,
  and Estimation*, JASA — a well-known, high-confidence real reference for calibration/sharpness, if
  a second citation is wanted. Optional, not a hard requirement.
- **Severity:** Low.

### 3.5 §3.4 (lines 180+) — temporally-ordered evaluation design, NOT cross-validation
> "All three evaluation designs preserved the temporal order of the monitoring records. For each
> period being estimated, the model used only MLCW observations that would have been available before
> that period..."

- **CORRECTED FRAMING (2026-08-10, second pass):** the first pass of this item wrongly called §3.4's
  design "walk-forward / expanding-window time-series cross-validation." That labeling is wrong and
  is corrected here. The manuscript's evaluation design is explicitly **not** k-fold cross-validation
  of any kind, walk-forward or otherwise:
  - Temporal order is always preserved — later observations never influence earlier estimates
    (confirmed directly at methods005.tex line 183: "This design prevented later MLCW observations
    from influencing earlier estimates").
  - §3.4.1 ("Delayed data delivery") recalibrates the model periodically in an expanding-window
    manner (line 190: "the model was recalibrated for the next cycle... gradually expanded the
    calibration record") — this is closer to expanding-window rolling recalibration than to
    fold-based CV.
  - §3.4.3 ("Sensitivity to the absence of subsequent MLCW measurements," lines 488+) fits the model
    **once**, from an initial 3/5/8-year record, and never refits afterward ("coefficients and
    predictor scaling therefore remained fixed throughout the subsequent estimation period") — this
    is the opposite of cross-validation, which by definition refits on every fold.
  - So no single "cross-validation" label covers all three designs; §3.4.1 is periodic recalibration,
    §3.4.3 is single-fit-no-refit, and §3.4.2 (reduced MLCW frequency, own derivation, see 3.6) sits
    between them.
- **Why it needs attention:** what actually needs a citation here is not a citation that calls this
  design "cross-validation" — it is a methodological reference justifying **why standard random or
  k-fold cross-validation would be invalid for this temporally dependent data, and why a temporally-
  ordered evaluation scheme was used instead**. Random/k-fold splitting would let later months leak
  information into earlier estimates through shared model fitting; that is precisely the temporal-
  leakage problem the manuscript's design avoids by construction. No citation appears anywhere in
  §3.4, §3.4.1, §3.4.2, or §3.4.3 to support this design choice, even though it anchors all three
  experimental designs in this section.
- **Verified suggested source:** Bergmeir & Benítez (2012), *On the use of cross-validation for time
  series predictor evaluation*, Information Sciences, vol. 191, pp. 192–213, DOI
  `10.1016/j.ins.2011.12.028` — confirmed real via a live Crossref lookup in this pass (see §7 below
  for full verification detail). Cite it specifically as support for "why we did not use standard
  cross-validation, and why temporal ordering was preserved instead" — phrase the manuscript sentence
  accordingly, e.g. "Standard k-fold cross-validation was not used because random splitting would
  allow later observations to inform earlier estimates \citep{bergmeir_2012}; instead, all three
  designs preserved temporal order..." Do **not** phrase it as "this walk-forward cross-validation
  design follows \citep{bergmeir_2012}" — that would misrepresent both the citation and the design.
  This key is not currently in `writing_manu2.bib`; a new entry is needed (suggested key:
  `bergmeir_2012_cv`).
- **Severity:** High — this design-justification gap anchors the entire Experimental Design
  subsection and has zero citation support currently. Severity is about the missing justification for
  avoiding cross-validation, not about mislabeling our own design as cross-validation.

### 3.6 §3.4.2 (lines 284–363) — cumulative/aggregated-observation regression scaling (own derivation)
> The √H_I scaling of the cumulative regression equation (Eqs. 12–16) and its treatment of summed
> residual variance.

- **Why NOT flagged:** this is presented as the authors' own mathematical derivation specific to this
  study's reduced-measurement-frequency design, built directly from the paper's own Eq. 3–4 residual
  model. It does not read as an adopted method from prior literature, and inventing a citation here
  would misattribute original work. No citation needed — explicitly noted so this is not mistaken for
  an overlooked gap.
- **Severity:** None (correctly uncited).

### 3.7 §3.4.1 and §3.4.3 — no citation for the "why not cross-validation" justification, repeated per subsection
- Same underlying gap as 3.5 (corrected framing above); not counted twice in the summary table below,
  but note that once the Bergmeir & Benítez (2012) citation is added at the first mention (§3.4
  opening, justifying temporally-ordered evaluation over random/k-fold cross-validation), it does not
  need repeating in §3.4.1–§3.4.3 individually. Do not let any of the three subsections independently
  acquire wording that calls its own design "cross-validation" — §3.4.1 is periodic/expanding-window
  recalibration and §3.4.3 is single-fit-no-refit; neither is fold-based.

### Summary for methods005.tex
Two clear "citation exists in bib but unused" gaps (3.3 scikit-learn — confirmed high severity, see
§7 below: `sklearn.linear_model.BayesianRidge` is directly confirmed in the run_048 pipeline scripts;
and optionally 3.2's foundational kriging text), one genuine literature gap needing a new lookup (3.5,
corrected: justification for temporally-ordered evaluation over cross-validation, not a citation for
calling the design "cross-validation" — high severity), and one own-derivation section correctly left
uncited (3.6).

---

## 4. Available citation-search tools and recommended workflow

### Tool inventory

| Tool | Best for | Notes |
|---|---|---|
| `/claude-scientific-writer:research-lookup` | General-purpose first pass across Google Scholar, PubMed, arXiv, bioRxiv, Semantic Scholar | Good default starting point for any single citation need in this audit. |
| `/claude-scientific-writer:literature-search-openalex` | Rich metadata: DOI, citation counts, h-index, open-access PDF links | Needs OpenAlex query syntax (not free text) — better for confirming a specific known candidate (e.g., verifying `bock_physical_2016`'s real title/venue) than for open-ended discovery. |
| `/claude-scientific-writer:citation-management` | Validating citations already in the draft, harvesting missing ones, DOI→BibTeX conversion, `.bib` deduplication | Directly useful here: run it against `writing_manu2.bib` to catch duplicate keys and missing DOIs (the prior audit already flagged `mackay_bayesian_1992` missing its DOI). |
| `/claude-scientific-writer:parallel-web` | Exhaustive multi-source synthesis | Overkill for confirming a single citation; reserve for the temporally-ordered-evaluation-vs-CV lookup (3.5) if a first pass with `research-lookup` is inconclusive. |
| `/claude-scientific-writer:scientific-writing` | Writing workflow with `\cite{}` integration | Use once specific citations are chosen, to insert them into the .tex files correctly (note: audit itself must NOT edit the manuscript). |
| `mcp__paper-search-mcp__search_semantic` (Semantic Scholar) | Confirming author/year/venue for known candidates (Bergmeir & Benítez 2012, Gneiting & Raftery 2007, Poland 1984) | Fast, structured, good first stop for confirming a specific known paper exists as described. |
| `mcp__paper-search-mcp__search_openalex` / `search_crossref` | DOI resolution, metadata cross-check before adding a BibTeX entry | Use to get a clean DOI for any newly added reference (e.g., the Bergmeir \& Benítez temporal-evaluation-justification paper) before writing the `.bib` entry. |
| `mcp__paper-search-mcp__search_google_scholar` | Broad sanity check, citation-count context | Useful to confirm a candidate is the "standard" citation for a concept (e.g., confirming Hoerl & Kennard 1970 remains the standard ridge-regression citation, already true here). |
| `mcp__paper-search-mcp__get_crossref_paper_by_doi` | Once a DOI is known, pull full structured metadata for the `.bib` entry | Use right before writing a new `.bib` entry to avoid hand-typing metadata. |
| `mcp__claude_ai_Consensus__search` | Biomedical/clinical focus | Not suited to hydrogeology/geoscience citations — skip for this manuscript (confirmed also by the prior audit pass, which reported failed Consensus calls). |

### Recommended workflow per open item in this audit

1. **§2.2 `hung2012_mlcw` (dataset003, MLCW instrumentation):** no search needed — key already exists
   in `writing_manu2.bib`. Just confirm its title/content matches "MLCW instrumentation/design" via
   `mcp__paper-search-mcp__read_semantic_paper` or by opening the existing `.bib` entry directly, then
   add `\citep{hung2012_mlcw}` alongside `hung_measuring_2021`.

2. **§2.5 `bock_physical_2016` (dataset003, cGNSS processing):** same — check the existing `.bib`
   entry's title first (fastest: read the `.bib` file directly); only run
   `mcp__paper-search-mcp__search_semantic` if the title is ambiguous about whether it covers daily
   GNSS position time-series derivation.

3. **§3.3 `scikit-learn` (methods005, Bayesian ridge implementation):** CONFIRMED in this pass —
   `sklearn.linear_model.BayesianRidge` / `sklearn` imports are directly present in the run_048
   pipeline scripts under
   `007_tests/014_ml_nowcast/scripts/run048_tuku_p0_level1a_sparse_interval_sensitivity.py` and
   related run_048 files (checked via grep across the ml_nowcast pipeline folder). Add
   `\citep{scikit-learn}` at the Bayesian ridge regression's first introduction in §3.3.

4. **§3.5 temporally-ordered-evaluation-vs-cross-validation citation (methods005, genuinely new
   lookup, CORRECTED FRAMING — see 3.5 above):** verified in this pass via
   `mcp__paper-search-mcp__search_crossref` (query: "On the use of cross-validation for time series
   predictor evaluation Bergmeir Benitez") and `mcp__paper-search-mcp__get_crossref_paper_by_doi`
   (DOI `10.1016/j.ins.2011.12.028`). Full details in §7. Add via
   `/claude-scientific-writer:citation-management` to avoid duplicate-key collisions with the existing
   `.bib` file — use this citation to support "why cross-validation was not used," never to relabel
   our own design as cross-validation.

5. **§1.1 `poland_guidebook_1984` / `galloway_land_1999` (studyarea002, consolidation mechanism):** no
   search needed — both keys already exist in `writing_manu2.bib`. Just add
   `\citep{poland_guidebook_1984}` (or `galloway_land_1999`) to the effective-stress sentence.

6. **§3.4 optional Gneiting & Raftery 2007 (methods005, coverage/sharpness):** low priority; if
   pursued, `mcp__paper-search-mcp__search_google_scholar` with query "Gneiting Raftery strictly
   proper scoring rules prediction estimation 2007" is sufficient to confirm details before adding.

7. **After any new `.bib` entries are added:** run `/claude-scientific-writer:citation-management` once
   over the whole bibliography to deduplicate and validate all cite keys used across `main.tex`'s
   `\input` chain (the prior audit noted the standard validator does not follow `\input{}`, so use the
   citation-management skill's harvesting mode rather than a bare grep-based validator).

---

## 5. Summary table

| File | Line / section | Claim | Status | Suggested source type |
|---|---|---|---|---|
| studyarea002.tex | Line 8 | Effective stress / load transfer drives fine-grained compaction and subsidence | Cited (3 refs) but missing foundational mechanism ref | `poland_guidebook_1984` or `galloway_land_1999` (already in bib, unused here) |
| studyarea002.tex | Line 6 | "Commonly divided into proximal, middle, distal zones" | Low-severity, optional | No action needed unless reviewer objects |
| studyarea002.tex | Line 8 | 38% rice production figure | Verification only | Confirm number matches `chang2022_wetanddry` |
| dataset003.tex | Line 4 | Data-provider QA delay before release | Uncited, provenance claim | Data-provider documentation / data-availability statement, not a journal paper |
| dataset003.tex | Line 10 | MLCW magnetic-ring instrumentation, 1 mm precision | Cited (1 ref) but a second directly relevant key is unused | `hung2012_mlcw` (already in bib, unused) |
| dataset003.tex | Line 14 | "Aquifers 1–4" nomenclature | Verification only | Confirm `survey_project_1999` is the correct nomenclature source |
| dataset003.tex | Line 18 | cGNSS daily position time-series derivation | Provenance cited, processing method uncited | `bock_physical_2016` (already in bib, unused; verify content first) |
| dataset003.tex | Line 22 | Borehole log provenance + grain-size classification into gravel/sand/fine-grained bins | Fully uncited paragraph | Data-provenance source; Folk (1954) or Blair \& McPherson (1999) — MEDIUM confidence, see §7; verified real, but the underlying grouping is the provider's own SOIL\_TYPE letter codes, not a formal application of either scheme |
| dataset003.tex | (task-flagged, not applicable) | ILR / compositional-data transform | No gap — ILR is not used in these files | None needed; explicitly confirmed absent |
| methods005.tex | Line 34 | Ordinary kriging | Cited (applied paper) but foundational geostatistics text optional | Cressie 1993 or Goovaerts 1997 (optional) |
| methods005.tex | Line 59 / §3.3 | Bayesian ridge regression fitted via marginal-likelihood hyperparameter estimation | Method cited; software/toolkit citation missing | `scikit-learn` (already in bib, unused) — CONFIRMED sklearn `BayesianRidge` is the actual implementation (run_048 scripts) |
| methods005.tex | Line 178 | Interval width vs. coverage trade-off | Cited; optional second reference | Gneiting & Raftery (2007), proper scoring rules (optional, not tool-verified this pass) |
| methods005.tex | §3.4 (lines 180+) | Design justification for temporally-ordered (non-cross-validated) evaluation — CORRECTED framing, was mislabeled "walk-forward CV" | Fully uncited across §3.4, §3.4.1–§3.4.3 | Bergmeir \& Benítez (2012), *Information Sciences* 191:192–213, DOI 10.1016/j.ins.2011.12.028 — VERIFIED via Crossref; cite as justification for avoiding standard CV, not as a label for our design |
| methods005.tex | §3.4.2 (lines 284–363) | √H_I cumulative-observation regression scaling | Correctly uncited — own derivation | None needed |

---

## 6. Citation Norms — When to Cite vs. Not

Grounded in Purdue OWL's common-knowledge guidance, MDPI/Elsevier author-guideline language on
methods sections, and scikit-learn's own citation request (all retrieved via WebSearch, 2026-08-10).

**Cite when:**
- A statement is a specific factual claim not verifiable by "common knowledge" — Purdue OWL defines
  common knowledge as undocumented-but-findable in 5+ credible sources, or found in a general
  encyclopedia; anything narrower (a specific percentage, rate, instrument spec) needs a source.
- A named method, algorithm, or software toolkit is used (Bayesian ridge, ordinary kriging,
  scikit-learn) — cite the originating paper/toolkit, separately from citing an applied example of it.
- The claim compares directly to, or draws on, prior published work (e.g., stating why a design
  differs from Hung et al. 2025's approach).
- Data provenance is described — whose data, which agency, what QA process (a documentation citation,
  not necessarily a peer-reviewed paper).
- Quoting a previously published method's exact wording — MDPI/Elsevier guides require quotation
  marks plus the citation in that case, not paraphrase-without-attribution.

**Do NOT cite when:**
- The claim is the authors' own mathematical derivation built from the paper's own preceding
  equations (methods005.tex §3.4.2's √H_I scaling — confirmed correctly uncited in §3.6 above).
- Reporting the authors' own results generated by their own processing chain (e.g., run_048 output
  numbers) — these are evidence, not literature claims.
- The fact is genuinely field-common-knowledge for the target audience — but note Purdue OWL's caveat
  that "common knowledge" is audience- and discipline-dependent; a hydrogeology-journal reviewer's
  bar for "well known" is narrower than a general reader's.
- Something already cited earlier in the same section/paragraph is restated without a new claim
  attached — repeat citations are not required at every sentence, only where a new claim appears.

**Discipline-specific note:** no geoscience- or Bayesian-statistics-specific style guide surfaced
beyond the general MDPI/Elsevier "methods already published must be indicated by a reference"
convention and scikit-learn's own explicit request to cite Pedregosa et al. (2011) "in scientific
publications" using its algorithms. When genuinely uncertain, Purdue OWL's practical rule applies:
"When in doubt, just cite."

---

## 7. Newly Verified Citation Candidates (real tool calls, this pass)

All entries below were confirmed via a live tool call in this session; none are invented. Tool calls
and raw identifiers are given so the coordinator can re-run and verify independently.

### 7.1 Bergmeir & Benítez (2012) — temporally-ordered evaluation vs. cross-validation (methods005 §3.4)
- **Full citation:** Bergmeir, Christoph, and José M. Benítez. "On the use of cross-validation for
  time series predictor evaluation." *Information Sciences* 191 (2012): 192–213.
  DOI: `10.1016/j.ins.2011.12.028`.
- **Tool calls used:**
  `mcp__paper-search-mcp__search_crossref` (query: "On the use of cross-validation for time series
  predictor evaluation Bergmeir Benitez") — returned title, authors, DOI, journal, volume, pages
  exactly matching the candidate.
  `mcp__paper-search-mcp__get_crossref_paper_by_doi` (doi: `10.1016/j.ins.2011.12.028`) — confirmed
  same record directly by DOI lookup (Elsevier BV, *Information Sciences*, vol. 191, pp. 192–213,
  published 2012-05-01, 1074 citations recorded by Crossref at query time).
- **Supports which claim:** the design-justification gap in §3.4 (corrected framing, §3.5 above) —
  why standard random/k-fold cross-validation was not used, and why a temporally-ordered evaluation
  scheme (expanding-window recalibration in §3.4.1; single-fit-no-refit in §3.4.3) was used instead.
- **Confidence: HIGH.** This is the standard, heavily-cited (1074 citations) reference specifically
  about temporal leakage in cross-validating time-series predictors — squarely on-topic for the
  justification needed, and not for relabeling the manuscript's own design.
- **Not currently in `writing_manu2.bib`** (confirmed by reading the full 886-line file; no key
  resembling `bergmeir` exists). Suggested new key: `bergmeir_2012_cv`.
- **Suggested BibTeX (not written to the .bib file — suggestion only):**
  ```bibtex
  @article{bergmeir_2012_cv,
    title   = {On the use of cross-validation for time series predictor evaluation},
    author  = {Bergmeir, Christoph and Ben{\'i}tez, Jos{\'e} M.},
    journal = {Information Sciences},
    volume  = {191},
    pages   = {192--213},
    year    = {2012},
    doi     = {10.1016/j.ins.2011.12.028},
    issn    = {0020-0255},
    publisher = {Elsevier}
  }
  ```

### 7.2 Folk (1954) — grain-size/lithology classification candidate (dataset003 §2.6)
- **Full citation:** Folk, Robert L. "The Distinction between Grain Size and Mineral Composition in
  Sedimentary-Rock Nomenclature." *The Journal of Geology* 62, no. 4 (1954): 344–359.
  DOI: `10.1086/626171`.
- **Tool call used:** `mcp__paper-search-mcp__search_crossref` (query: "Folk 1954 distinction between
  grain size and mineral composition sedimentary rock nomenclature") — returned exact title, author,
  journal, volume/issue/pages, DOI; 1081 citations recorded by Crossref.
- **Supports which claim:** dataset003.tex line 22's grain-size-category description ("gravel, coarse
  sand, fine sand, and fine-grained deposits comprising clay, silt, and mud").
- **Confidence: MEDIUM.** Real and highly-cited, and it is the canonical grain-size/composition
  nomenclature paper in sedimentology — but the pipeline evidence (see below) shows the manuscript's
  four categories come from the data provider's own SOIL_TYPE letter grammar (a bespoke grouping
  documented as "authoritative — set by the user" in
  `007_tests/014_ml_nowcast/scripts/02_compute_section_materials.py` lines 36–46: capitals G/S/M/Z/C
  for material, lowercase c/m/f/v for grain-size modifier), not a direct, stated application of Folk's
  or any other named scheme. Citing Folk (1954) here would overstate methodological rigor unless the
  manuscript text is changed to explicitly say a named classification standard was applied. The
  audit's original conditional recommendation stands: cite a classification-standard reference **only
  if** the text is revised to state a named scheme was used; otherwise state plainly that categories
  follow the data provider's own log labels, which needs a provenance citation, not a classification-
  standard one.

### 7.3 Blair & McPherson (1999) — secondary grain-size classification candidate (dataset003 §2.6)
- **Full citation:** Blair, Terence C., and John G. McPherson. "Grain-size and textural classification
  of coarse sedimentary particles." *Journal of Sedimentary Research* 69, no. 1 (1999): 6–19.
  DOI: `10.2110/jsr.69.6` (canonical; a duplicate/legacy Crossref record also exists under
  `10.1306/d426894b-2b26-11d7-8648000102c1865d` with far fewer indexed citations — use the
  `10.2110/jsr.69.6` DOI).
- **Tool call used:** `mcp__paper-search-mcp__search_crossref` (query: "Blair McPherson Grain size and
  textural classification of coarse sedimentary particles") — returned full abstract, DOI, journal,
  volume/issue/pages; 393 citations recorded by Crossref under the canonical DOI.
- **Supports which claim:** same sentence as 7.2, specifically the "gravel" fraction, since this paper
  is about extending grain-size grades on the coarse (gravel/boulder) end of the Udden-Wentworth
  scale, which the paper's own abstract calls "the standard for objective description of sediment."
- **Confidence: MEDIUM**, same caveat as 7.2 — the manuscript's four bins are provider log labels, not
  a stated application of Udden-Wentworth/Blair-McPherson grades. Useful only as a secondary citation
  alongside Folk (1954) if the manuscript is revised to name a formal scheme.
- **Note on Wentworth (1922) itself:** the original Udden-Wentworth grade-scale paper was NOT returned
  directly by any search in this pass (search terms tried: "Wentworth 1922 grade scale grain size
  classification sediments" via `mcp__paper-search-mcp__search_semantic`) — only secondary papers
  that reference or extend it (Blair & McPherson, Terry & Goff). Do not cite "Wentworth 1922" as a
  verified candidate from this audit; if it is wanted, a separate targeted lookup is still needed.

### 7.4 Existing-but-unused bib keys re-confirmed present (no new lookup needed)
Read directly from `writing_manu2.bib` (886 lines, read in full this pass):
- `hung2012_mlcw` — confirmed present (line 247), Hung et al. 2012, *Engineering Geology* 147-148,
  "Modeling aquifer-system compaction and predicting land subsidence in central Taiwan." Confirms the
  audit's §2.2 claim exactly — this is an MLCW/compaction-well modeling paper, appropriate alongside
  `hung_measuring_2021` for instrumentation continuity, though note its title is about modeling
  compaction/subsidence rather than instrument hardware design specifically; still the best-available
  already-in-bib option.
- `poland_guidebook_1984` — confirmed present (line 460), Poland 1984, UNESCO guidebook. Matches
  audit's §1.1 claim.
- `galloway_land_1999` — confirmed present (line 165), Galloway, Jones & Ingebritsen 1999, USGS
  Circular 1182. Matches audit's §1.1 claim.
- `scikit-learn` — confirmed present (line 792), Pedregosa et al. 2011, JMLR. Matches audit's §3.3
  claim. **Additionally confirmed this pass:** `sklearn.linear_model.BayesianRidge` is directly used
  in the run_048 pipeline (grep hit in
  `007_tests/014_ml_nowcast/scripts/run048_tuku_p0_level1a_sparse_interval_sensitivity.py` and related
  run_048 scripts under `007_tests/014_ml_nowcast/`), upgrading this from "verify before adding" to
  "confirmed — add the citation."
- `bock_physical_2016` — confirmed present (line 16), Bock & Melgar 2016, *Reports on Progress in
  Physics*, "Physical applications of GPS geodesy: a review." Title independently confirms it plausibly
  covers GNSS position time-series processing physics, supporting the audit's §2.5 suggestion; content
  was not read beyond title/metadata in this pass.

### 7.5 Searches that returned nothing useful (reported per instructions, not fabricated)
- `mcp__paper-search-mcp__search_semantic` for "borehole lithology classification grain size sediment
  gravel sand fine-grained geotechnical" returned only tangential regional grain-size studies (Wadi
  Fatima, Leipzig floodplain, Taedong River) — none suited as a foundational classification-standard
  citation; Folk (1954) and Blair & McPherson (1999) were found instead via targeted Crossref queries
  once the semantic search's tangential hits suggested "grain-size classification" as the right
  keyword frame.
- `mcp__paper-search-mcp__search_semantic` for "Unified Soil Classification System USCS geotechnical
  borehole log lithology description standard" returned an empty result set (`{"result":[]}`) — no
  USCS-specific paper surfaced; if USCS is the scheme actually intended, a targeted search using the
  ASTM standard designation (e.g., "ASTM D2487") rather than free text would be the next step, not
  attempted in this pass since the pipeline evidence (§7.2) indicates a bespoke provider scheme, not
  USCS, is what is actually used.
- `mcp__paper-search-mcp__search_semantic` for "Wentworth 1922 grade scale grain size classification
  sediments" did not return the original Wentworth (1922) paper itself (see 7.3 note).
