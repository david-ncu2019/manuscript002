# MLCW Presentation Extension Rules

**File:** `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\presentation\dataset_overview.txt`

**Document Type:** LaTeX Beamer presentation (aspectratio=169, 10pt, Madrid theme + seahorse colorscheme)

**Date Last Updated:** 2026-05-19

---

## 1. File Structure & Format Overview

### 1.1 Document Organization

```
Line Range  |  Section
------------|----------
 1–56       |  Document preamble (documentclass, packages, colors, macros, metadata)
57–66       |  Title slide + Outline (automatically generated from \section{})
68–99       |  Section 1: Study Context (2 frames)
101–125     |  Dataset Overview (1 frame, overview table)
128–454     |  Section 2: Dataset 1 — MLCW (10 frames, as of 2026-05-19)
457–491     |  Section 3: Dataset 2 — InSAR (1 frame)
494–525     |  Section 4: Dataset 3 — Groundwater Level (1 frame)
528–566     |  Section 5: Dataset 4 — Stratigraphy (1 frame)
569–602     |  Section 5: Dataset 5 — Direct Ratio (1 frame)
605–635     |  Pipeline & Status Summary (2 frames)
636–660     |  Full Processing Pipeline + Data Status table
661–675     |  Closing slide + \end{document}
```

### 1.2 Key Markers

Each major section begins and ends with a **section marker line**:
```latex
% ============================================================
\section{Dataset X: Name}
% ============================================================
```

After each `\end{frame}`, always include a blank comment line:
```latex
\end{frame}

%
```

### 1.3 Color Palette

The document defines five semantic colors (RGB values). **Always use these; do not define new colors.**

| Color Name | RGB Value | Semantic Use |
|------------|-----------|--------------|
| `insar` | 30, 90, 170 | InSAR dataset elements, InSAR-specific sections |
| `mlcw` | 0, 140, 80 | MLCW dataset elements, MLCW section frames |
| `gwl` | 200, 100, 20 | Groundwater level elements |
| `strat` | 130, 60, 160 | Stratigraphy / BME elements |
| `derived` | 170, 30, 50 | Derived products (direct ratio, aggregated metrics) |
| `ready` | 0, 150, 80 | "Complete" status indicator |
| `pending` | 180, 120, 0 | "Pending" or "Deferred" status indicator |

### 1.4 LaTeX Macros

The following macros are pre-defined and **must be used** in the appropriate contexts:

| Macro | Use | Example |
|-------|-----|---------|
| `\dsmlcw{}` | Colored MLCW text (green, bold) | `\dsmlcw{} (4/10) — ...` |
| `\dsinsar{}` | Colored InSAR text (blue, bold) | `\dsinsar{} overview` |
| `\dsgwl{}` | Colored GWL text (orange, bold) | `\dsgwl{} integration` |
| `\dsstrat{}` | Colored Stratigraphy text (purple, bold) | `\dsstrat{} classification` |
| `\fpath{...}` | File/path highlighting (monospace on light gray bg) | `\fpath{batch_process_MLCW.py}` |
| `\ready` | Ready status indicator (green checkmark) | `\ready` |
| `\pending` | Pending status indicator (orange triangle) | `\pending` |

---

## 2. MLCW Section Architecture (Frames 4–10, Lines 247–454)

### 2.1 Current MLCW Section Structure

**Location:** Lines 247–454, immediately after a set of 4 legacy frames (lines 131–245) that cover raw data and early pipeline stages.

**Current scope:** 7 active frames (numbered 4/10 through 10/10)
- Frame 4/10: Step 1 — Parametric Decomposition & Reconstruction
- Frame 5/10: Step 2 — Reconstruction at Uniform Dates
- Frame 6/10: Step 3 — PCHIP Depth Regularisation
- Frame 7/10: Baseline Alignment & 2022 Data Gap
- Frame 8/10: Direct Ratio Baseline: $\bar{f}_k$
- Frame 9/10: Network Status & Operational Outlook
- Frame 10/10: MLCW Processing Summary (table)

### 2.2 Insertion Points for New Frames

**Primary insertion point:** Immediately before the line:
```latex
% ============================================================
\section{Dataset 2: InSAR}
% ============================================================
```

This line is at **line 457** (as of 2026-05-19). All new MLCW frames must be inserted before this marker.

**Secondary insertion points (less common):**
- After frame 10/10 (line 454) and before the section marker (line 456): for late-stage summary or validation frames that logically close the MLCW section.
- Between any two existing frames: only if adding a frame that breaks down an existing topic into two parts (e.g., splitting "Direct Ratio Analysis" into "Definition" and "Results").

### 2.3 Frame Numbering When Adding New Frames

**Current state:** MLCW section has 10 frames total (4/10 through 10/10).

**If adding N new frames:**

1. **Update the denominator** in all existing MLCW frame titles.
   - If adding 3 new frames: 4/10 → 4/13, 5/10 → 5/13, ..., 10/10 → 10/13.
   - If adding 2 new frames: 4/10 → 4/12, 5/10 → 5/12, ..., 10/10 → 10/12.

2. **Number new frames sequentially** after the last existing frame.
   - If inserting 2 frames before the InSAR section: they become 11/13 and 12/13 (if 3 frames are added total).

3. **Use a script or find-and-replace** to update all frame titles. Do not manually renumber.

**Example:** Adding 3 frames for "Walk-Forward Validation Results"

Before:
```latex
\begin{frame}{\dsmlcw{} (10/10) — MLCW Processing Summary}
```

After:
```latex
\begin{frame}{\dsmlcw{} (10/13) — MLCW Processing Summary}

...

\begin{frame}{\dsmlcw{} (11/13) — Walk-Forward CV: 2022 Hold-Out}
...
\end{frame}

%

\begin{frame}{\dsmlcw{} (12/13) — Walk-Forward CV: 2023–2025 Folds}
...
\end{frame}

%

\begin{frame}{\dsmlcw{} (13/13) — Fold Summary \& per-Station Diagnostics}
```

---

## 3. LaTeX Beamer Style Guidelines

### 3.1 Frame Template

All MLCW section frames **must** follow this structure:

```latex
\begin{frame}{\dsmlcw{} (N/M) — [Verb] [Object] — [Optional Subheading]}
  % Content here: blocks, columns, text, tables, etc.
\end{frame}

%
```

**Frame title rules:**
- Always start with `\dsmlcw{} (N/M)` where N is the frame number and M is the total count.
- Use an em dash (`—`) after the frame number.
- Include a concise action verb (e.g., "Step 1:", "Validation Results:", "Direct Ratio Analysis").
- Include the object or topic.
- Optionally add a subheading after a second em dash (e.g., "Expected vs. Observed Performance").

### 3.2 Column Layout

For side-by-side content, use the `columns` environment:

```latex
\begin{columns}[T]
  \begin{column}{0.48\textwidth}
    % Left column: width 0.48 or 0.50
    \begin{block}{Block Title}
      Content here
    \end{block}
  \end{column}
  \begin{column}{0.48\textwidth}
    % Right column: width 0.48 or 0.46
    \begin{block}{Block Title}
      Content here
    \end{block}
  \end{column}
\end{columns}
```

**Width guidelines:**
- For two equal columns: use `0.48\textwidth` for each (leaves 0.04 for spacing).
- For unequal columns (e.g., 52% left, 44% right): use `0.52` and `0.44`.
- Always use `[T]` to align columns at the top.

### 3.3 Block Types

| Block Type | LaTeX | Use Case |
|------------|-------|----------|
| `block` | `\begin{block}{Title}...` | Main content, standard presentation |
| `alertblock` | `\begin{alertblock}{Title}...` | Warnings, critical issues, unresolved problems |
| `exampleblock` | `\begin{exampleblock}{Title}...` | Best-case examples, clean results, reference stations |

**Example:**
```latex
\begin{alertblock}{2022 Drought Gap: Reconstructed Values}
  Raw MLCW data entirely absent during 2022. Values filled via parametric interpolation.
  Critical for testing: 2022 becomes hold-out fold in walk-forward CV.
\end{alertblock}

\begin{exampleblock}{Cleanest Stations (All-Positive Profiles)}
  HUNAN, KECUO, NEILIAO, YIWU, ZHENGMIN
\end{exampleblock}
```

### 3.4 Font Sizes

| Size | Command | Context |
|------|---------|---------|
| Normal (10 pt) | default | Frame text, block headings |
| Small (9 pt) | `\small` | Dense tables, inline documentation |
| Script (8 pt) | `\scriptsize` | Very dense content, code paths |
| Tiny (7 pt) | `\tiny` | Captions, annotations within figures |

**Best practice:** Use `\small` for summary tables; use `\scriptsize` only if absolutely necessary for space.

### 3.5 Spacing

Use `\vspace{}` to control vertical spacing:

| Distance | Command | Use Case |
|----------|---------|----------|
| 0.3 em | `\vspace{0.3em}` | Between small blocks or items |
| 0.6 em | `\vspace{0.6em}` | Between major blocks |
| 1.0 em | `\vspace{1.0em}` | Between sections within a frame |

### 3.6 End-of-Frame Syntax

Every frame **must** end with:
```latex
\end{frame}

%
```

The blank `%` line is required. It visually separates frames in the source file and prevents LaTeX compilation errors from frame-to-frame transitions.

---

## 4. Content Organization by Topic Type

### 4.1 Processing Steps (Step 1, Step 2, Step 3, etc.)

**Structure:**
1. **Left column:** Conceptual goals, constraints, physical motivation.
2. **Right column:** Key parameters, model components, output format.

**Example template:**
```latex
\begin{frame}{\dsmlcw{} (N/M) — Step K: [Process Name]}
  \begin{columns}[T]
    \begin{column}{0.50\textwidth}
      \begin{block}{Goals}
        \begin{itemize}
          \item \textbf{Goal 1:} description
          \item \textbf{Goal 2:} description
        \end{itemize}
        \medskip
        \small Script: \fpath{script_name.py}
      \end{block}
    \end{column}
    \begin{column}{0.46\textwidth}
      \begin{block}{Model Components}
        \begin{itemize}
          \item \textbf{Component A:} parameter range or formula
          \item \textbf{Component B:} parameter range or formula
        \end{itemize}
        \medskip
        \textbf{Output:} format and dimensions
      \end{block}
    \end{column}
  \end{columns}
\end{frame}
```

**Key elements:**
- Always cite the script name (use `\fpath{}`).
- List key parameters and their valid ranges.
- Explain why each parameter matters physically.
- State input/output dimensions.

### 4.2 Data Transformations (Alignment, Regularisation, Decomposition)

**Structure:**
1. **Left column:** Physical meaning, transformation goal, constraints.
2. **Right column:** Formula (display math), before/after dimensions, validation criteria.

**Example template:**
```latex
\begin{frame}{\dsmlcw{} (N/M) — [Transformation Name]}
  \begin{columns}[T]
    \begin{column}{0.50\textwidth}
      \begin{block}{Physical Meaning}
        \small
        Explain in plain English what is happening to the data.
      \end{block}
      \begin{block}{Method}
        \begin{enumerate}
          \item Step 1 of the algorithm
          \item Step 2 of the algorithm
          \item Step 3 of the algorithm
        \end{enumerate}
      \end{block}
    \end{column}
    \begin{column}{0.46\textwidth}
      \begin{block}{Transformation Formula}
        \[
          y = f(x)
        \]
        where $y$ = output (units), $x$ = input (units), \ldots
      \end{block}
      \begin{block}{Dimensions}
        \begin{itemize}
          \item \textbf{Input:} shape and type
          \item \textbf{Output:} shape and type
          \item \textbf{Validation:} error tolerance or check
        \end{itemize}
      \end{block}
    \end{column}
  \end{columns}
\end{frame}
```

### 4.3 Analysis Results (Direct Ratio, Validation Metrics, Statistical Summaries)

**Structure:**
1. **Left column:** Conceptual definition, methodology.
2. **Right column:** Summary statistics table or key findings.

**Example template:**
```latex
\begin{frame}{\dsmlcw{} (N/M) — [Analysis Name]: $\bar{f}_k$}
  \begin{columns}[T]
    \begin{column}{0.48\textwidth}
      \begin{block}{Definition}
        Per station $s$, depth $k$, epoch $i$:
        \[
          f_k(i) = \frac{Y_s(i, k)}{x_s(i)}
        \]
        $\bar{f}_k = \text{median}_i \{ f_k(i) \}$ is the stable depth attribution.
      \end{block}
    \end{column}
    \begin{column}{0.48\textwidth}
      \begin{block}{Key Statistics (All 39 Stations)}
        \small
        \renewcommand{\arraystretch}{1.1}
        \begin{tabular}{lc}
          \toprule
          Metric & Value \\
          \midrule
          Median $\sum_k \bar{f}_k$ & 0.52 \\
          Range of sums & 0.14–0.86 \\
          Spatial heterogeneity & $6\times$ \\
          \bottomrule
        \end{tabular}
      \end{block}
    \end{column}
  \end{columns}
\end{frame}
```

### 4.4 Network/Operational Context (Station Count, Timeline, Transferability, Status)

**Structure:**
1. **Left column:** Operational timeline, station counts, network evolution.
2. **Right column:** Implications for method design, transferability challenges.

**Example template:**
```latex
\begin{frame}{\dsmlcw{} (N/M) — Network Status \& Operational Challenges}
  \begin{columns}[T]
    \begin{column}{0.48\textwidth}
      \begin{block}{Timeline}
        \begin{itemize}
          \item \textbf{Original network:} N stations (years)
          \item \textbf{Shutdown event:} N stations shut down (date)
          \item \textbf{Current:} N stations active (date range)
          \item \textbf{Future trajectory:} expected N active by (date)
        \end{itemize}
      \end{block}
    \end{column}
    \begin{column}{0.48\textwidth}
      \begin{block}{Implications}
        \begin{itemize}
          \item \textbf{Implication 1:} How it affects method X
          \item \textbf{Implication 2:} Opportunity or challenge
          \item \textbf{Implication 3:} Design requirement
        \end{itemize}
      \end{block}
    \end{column}
  \end{columns}
\end{frame}
```

---

## 5. Visual Elements & Tables

### 5.1 Summary Statistics Tables

**Best practice template:**
```latex
\small
\renewcommand{\arraystretch}{1.15}
\begin{tabular}{ll}
  \toprule
  \textbf{Metric} & \textbf{Value} \\
  \midrule
  Median $\sum_k \bar{f}_k$ & 0.52 \\
  Range of sums & 0.14–0.86 \\
  Spatial heterogeneity & $6\times$ \\
  \bottomrule
\end{tabular}
```

**Rules:**
- Use `\toprule`, `\midrule`, `\bottomrule` from the `booktabs` package (already imported).
- Set `\renewcommand{\arraystretch}{1.15}` to increase row height for readability (standard: 1.1–1.35).
- Use `\textbf{}` for column headers.
- Keep metric labels bold; values in normal font.
- Limit to ≤12 rows per table (fit on one frame).

### 5.2 Colour in Tables

Use `\rowcolor{}` to group related rows by semantic meaning:

```latex
\begin{tabular}{p{2.8cm} p{3.8cm} p{3.9cm}}
  \toprule
  \textbf{Stage} & \textbf{Key Task} & \textbf{Output Dimensions} \\
  \midrule
  \rowcolor{mlcw!10}
  Raw Input & 39 stations, custom depths & 39 $\times$ variable \\
  \rowcolor{mlcw!10}
  Step 1 & Parametric decomposition & 39 $\times$ JSON models \\
  \rowcolor{derived!10}
  Direct Ratio $\bar{f}_k$ & Median epoch-wise fraction & 39 $\times$ 60 depths \\
  \bottomrule
\end{tabular}
```

**Colour scheme:**
- Use `mlcw!10` for MLCW processing stages.
- Use `insar!10` for InSAR processing stages.
- Use `gwl!10` for GWL processing stages.
- Use `derived!10` for derived/analysis outputs.
- The `!10` suffix (10% opacity) ensures light background without overwhelming text.

### 5.3 Equations

**Display math (standalone, full-line):**
```latex
\[
  f_k(i) = \frac{Y_s(i, k)}{x_s(i)}
\]
```

**Inline math (within text):**
```latex
The ratio $\bar{f}_k = \text{median}_i \{ f_k(i) \}$ is stable.
```

**Rules:**
- Always explain the physical meaning of each symbol before or immediately after the equation.
- Example:
  ```latex
  \[
    \hat{d}(t) = P(t) + S(t) + J(t)
  \]
  where $P(t)$ is trend (polynomial), $S(t)$ is seasonal, $J(t)$ is jump function.
  ```

### 5.4 File/Script Path References

Always use `\fpath{...}` for any file or script path:

```latex
\fpath{batch_process_MLCW.py}
\fpath{MLCW_5m_regular/TUKU_5m_grid.csv}
\fpath{direct_ratio_all_stations.py}
\fpath{mlcw_interp_insar_IDW_extend.feather}
```

**Why:** This ensures consistent formatting, makes paths searchable in the PDF, and maintains the light-gray background highlight for clarity.

### 5.5 Emphasis Formatting

| Command | Use | Example |
|---------|-----|---------|
| `\textbf{}` | Key concepts, important terms | `\textbf{Anchor-only model}` |
| `\textit{}` | Physical quantities, variable names | `$\textit{x}_s(i)$ is InSAR displacement` |
| `\texttt{}` | Code, variable names in code context | `\texttt{no\_relax=True}` |
| `\emph{}` | Emphasis within prose | The goal is to \emph{maximize} coverage. |

---

## 6. Cross-References & Data Accuracy

### 6.1 Primary Data Sources

**Always cite these files; never invent numbers:**

| Information | Source File | Location |
|-------------|-------------|----------|
| Station count (39), active count (19), shutdown date | `D:\110_PROJECT_002\discussion_memory.md` | Section "Project Overview" |
| Depth levels (60), spacing (5 m), range (0–295 m) | `D:\110_PROJECT_002\CLAUDE.md` | Section "Code Architecture" |
| InSAR epoch count (785), date range (2015-01-21 to 2025-12-11) | `D:\110_PROJECT_002\MEMORY.md` | "InSAR Data Structure" |
| Direct ratio median sum (0.52), range (0.14–0.86), 6× heterogeneity | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\direct_ratio_MLCW_InSAR\*_direct_ratio_stats.csv` | Batch statistics |
| α values (GNSS-derived and InSAR-derived) | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\alpha_comparison_all_stations_v3.csv` | All 39 stations |
| Anchor-only, ARX, Prophet results | `D:\110_PROJECT_002\discussion_memory.md` | Section 9 (Validation Results) |
| GWL co-location (21 of 39 stations), screen depths | `D:\110_PROJECT_002\CLAUDE.md` | "Data-Priority Rule" |

### 6.2 Citation Style

When citing results, use this format:

```latex
\textbf{Key result:} Median $\sum_k \bar{f}_k = 0.52$ across all 39 stations.
See \fpath{direct_ratio_all_stations.py} and associated CSV batch output.
```

Or, in a block:
```latex
\begin{block}{Validation Reference}
  \small
  Direct ratio analysis complete for all 39 stations.\\
  Citation: \fpath{direct_ratio_MLCW_InSAR/} directory.\\
  See also \fpath{discussion_memory.md} Section 8.1.
\end{block}
```

### 6.3 Script Citations

Scripts are cited from the primary working directory:
`D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\`

**Format:**
```latex
\fpath{batch_process_MLCW.py}        % from root of working directory
\fpath{src/postprocess.py}            % from a subdirectory
```

---

## 7. When to Add New Frames

### 7.1 Criteria for New Frames

**Add a frame if:**
- The topic covers a distinct processing step or algorithm (e.g., "Step 4: Temporal Smoothing").
- The topic presents analysis results with new insights (e.g., "Walk-Forward Validation: Fold 1 (2022) Diagnostics").
- The topic addresses a new data transformation or operational challenge (e.g., "GWL Screen Depth Harmonisation").
- The topic provides network context or operational implications (e.g., "Transferability to 5-Station Scenario").

**Do NOT add a frame if:**
- The topic is a minor parameter tuning detail (document in block text or a table instead).
- The topic is an intermediate debugging step (omit; use an analysis document instead).
- The topic duplicates an existing frame's content (merge or revise instead).

### 7.2 Topics That Should NOT Get Frames

- "Code optimisation for faster reconstruction" — mention in a remark block under the relevant step.
- "Sensitivity analysis of jump-detection threshold σ" — save results to CSV in an analysis document; cite in presentation.
- "Comparison of PCHIP vs. linear interpolation" — same as above.

### 7.3 Topics That SHOULD Get Frames

- "Walk-forward cross-validation: 4-fold structure and hold-out timing"
- "Anchor-only validation results: 39 stations, per-depth RMSE"
- "GWL integration: screen depth harmonisation to MLCW levels"
- "2022 Drought Gap: impact on training, role in fold 1 hold-out"
- "Network shrinkage: implications for GWL-driven (GWL+InSAR) transferability"

---

## 8. Naming Convention for New Frames

### 8.1 Frame Title Template

```latex
\begin{frame}{\dsmlcw{} (N/M) — [Verb] [Object] — [Optional Subheading]}
```

| Component | Format | Example |
|-----------|--------|---------|
| Macro | `\dsmlcw{}` or `\dsinsar{}` | — |
| Frame count | `(N/M)` | `(11/13)` |
| Separator | ` — ` (em dash) | — |
| Verb + Object | Action verb + primary noun | "Step 4: Temporal Smoothing", "Direct Ratio Analysis", "Walk-Forward Validation Results" |
| Optional subheading | Secondary detail after second em dash | "Fold 1 (2022) Diagnostics", "Expected vs. Observed Performance" |

### 8.2 Verb Guidelines

Use strong, specific verbs:

| Verb | Meaning | Example Frame |
|------|---------|-----------------|
| "Step K:" | Sequential processing step | `Step 1: Parametric Decomposition` |
| "Analysis:" | Exploratory or diagnostic analysis | `Analysis: Direct Ratio Stability Across Epochs` |
| "Validation:" | Testing, cross-validation results | `Validation Results: Anchor-Only 39-Station RMSE` |
| "Integration:" | Combining datasets or methods | `Integration: GWL Co-Location with MLCW` |
| "[Result]:" | Output or summary finding | `Direct Ratio Baseline: $\bar{f}_k$` |

### 8.3 Examples

✅ **Good frame titles:**
- `\dsmlcw{} (11/13) — Step 1: Parametric Decomposition`
- `\dsmlcw{} (12/13) — Walk-Forward Validation: 4-Fold Structure`
- `\dsmlcw{} (13/13) — Direct Ratio Results: 39-Station Summary`
- `\dsgwl{} (15/15) — GWL Integration: Screen Depth Alignment to MLCW`

❌ **Poor frame titles:**
- `\dsmlcw{} (11/13) — More Details` (vague verb)
- `\dsmlcw{} (12/13) — Results` (object too generic)
- `MLCW Analysis Results and Findings` (missing frame counter, no colored macro)

---

## 9. Example Extension Scenarios

### Scenario A: Adding Station-Level Anchor-Only Validation Results

**Goal:** Show per-station RMSE, R², and amplitude statistics for the anchor-only model on 19 active stations.

**Number of frames:** 2 (Overview + Per-Station Table)

**Frame A1: Overview (11/12)**
```latex
\begin{frame}{\dsmlcw{} (11/12) — Anchor-Only Validation: Overview}
  \begin{columns}[T]
    \begin{column}{0.50\textwidth}
      \begin{block}{Model Definition}
        \[
          \hat{Y}_s(i, k) = f_k \cdot x_s(i)
        \]
        where $f_k$ = median depth fraction, $x_s(i)$ = InSAR at epoch $i$.
        \medskip
        \begin{itemize}
          \item \textbf{Calibration window:} 2015-01 to 2021-11 (all 39 stations)
          \item \textbf{Validation window:} 2021-11 to 2025-12 (19 active stations)
          \item \textbf{Method:} Walk-forward 4-fold (2022, 2023, 2024, 2025 hold-outs)
        \end{itemize}
      \end{block}
    \end{column}
    \begin{column}{0.46\textwidth}
      \begin{block}{Key Metrics}
        \small
        \renewcommand{\arraystretch}{1.15}
        \begin{tabular}{lc}
          \toprule
          Metric & Value \\
          \midrule
          Median RMSE & X.XX mm \\
          Std. dev. RMSE & X.XX mm \\
          Median R$^2$ & 0.XX \\
          Stations (improved) & N / 19 \\
          Stations (degraded) & N / 19 \\
          \bottomrule
        \end{tabular}
      \end{block}
    \end{column}
  \end{columns}
\end{frame}

%
```

**Frame A2: Per-Station Results (12/12)**
```latex
\begin{frame}{\dsmlcw{} (12/12) — Anchor-Only: Per-Station RMSE Heatmap}
  \small
  Stations ranked by RMSE (ascending); colors indicate performance category.
  
  % Insert a table or figure here showing:
  % - 19 rows (active stations)
  % - Columns: Station, RMSE (mm), R², Seasonal Amplitude (factor), Status
  % - Color-code: green for RMSE < median; orange for RMSE > median
  
  \begin{block}{Interpretation}
    \begin{itemize}
      \item \textbf{Best performers:} TUKU, HUNAN, KECUO (RMSE $<$ 2 mm)
      \item \textbf{Problematic stations:} [List any with negative anchor improvement] — investigate ratio drift.
    \end{itemize}
  \end{block}
\end{frame}

%
```

**Data sources to cite:**
- `D:\110_PROJECT_002\discussion_memory.md` Section 7.3 (anchor-only results)
- Per-station output CSV: `output/stage1/anchor_only_validation_19stations.csv` (after computation)

---

### Scenario B: Adding Walk-Forward Cross-Validation Fold Results

**Goal:** Explain the 4-fold structure, show fold-by-fold RMSE evolution, highlight fold 1 (2022) as operationally critical.

**Number of frames:** 2 (Structure + Results)

**Frame B1: Structure and Timeline (13/14)**
```latex
\begin{frame}{\dsmlcw{} (13/14) — Walk-Forward CV: 4-Fold Structure}
  \begin{center}
  \small
  \renewcommand{\arraystretch}{1.2}
  \begin{tabular}{cccc}
    \toprule
    \textbf{Fold} & \textbf{Calibration Window} & \textbf{Hold-Out Year} & \textbf{Critical Notes} \\
    \midrule
    \rowcolor{mlcw!10}
    Fold 1 & 2015-01 — 2021-11 & 2022 & \textbf{Reconstructed MLCW} \\
    \rowcolor{mlcw!10}
    Fold 2 & 2015-01 — 2022-12 & 2023 & Observed MLCW \\
    \rowcolor{mlcw!10}
    Fold 3 & 2015-01 — 2023-12 & 2024 & Observed MLCW \\
    \rowcolor{mlcw!10}
    Fold 4 & 2015-01 — 2024-12 & 2025 & Observed MLCW (partial) \\
    \bottomrule
  \end{tabular}
  \end{center}
  \vspace{0.6em}
  
  \begin{alertblock}{Fold 1 is Operationally Critical}
    Raw MLCW entirely absent during 2022 (drought). Fold 1 tests performance when MLCW unavailable — 
    simulates operational resilience for GWL-driven (GWL+InSAR) methods.
  \end{alertblock}
\end{frame}

%
```

**Frame B2: Fold-by-Fold Results (14/14)**
```latex
\begin{frame}{\dsmlcw{} (14/14) — Fold-by-Fold RMSE Evolution}
  \begin{columns}[T]
    \begin{column}{0.50\textwidth}
      \begin{block}{Median RMSE by Fold}
        \small
        \renewcommand{\arraystretch}{1.2}
        \begin{tabular}{lcc}
          \toprule
          Fold & Hold-Out Year & RMSE (mm) \\
          \midrule
          \rowcolor{derived!10}
          Fold 1 & 2022 & X.XX \\
          \rowcolor{mlcw!10}
          Fold 2 & 2023 & X.XX \\
          \rowcolor{mlcw!10}
          Fold 3 & 2024 & X.XX \\
          \rowcolor{mlcw!10}
          Fold 4 & 2025 & X.XX \\
          \bottomrule
        \end{tabular}
      \end{block}
    \end{column}
    \begin{column}{0.46\textwidth}
      \begin{block}{Interpretation}
        \begin{itemize}
          \small
          \item Fold 1 RMSE slightly elevated (reconstructed MLCW).
          \item Folds 2–4 show stable RMSE (observed MLCW).
          \item Trend: RMSE improves as calibration window grows.
        \end{itemize}
      \end{block}
    \end{column}
  \end{columns}
\end{frame}

%
```

**Data sources to cite:**
- Results CSV: `output/stage1/walk_forward_cv_summary.csv` (after computation)
- Fold-specific per-station files: `output/stage1/fold_*.csv`

---

### Scenario C: Adding GWL Integration for GWL-Driven Models

**Goal:** Show GWL data availability, co-location with MLCW, screen depth mapping to MLCW levels.

**Number of frames:** 2 (Data Availability + Depth Harmonisation)

**Frame C1: GWL Co-Location Map (15/16)**
```latex
\begin{frame}{\dsgwl{} (15/16) — GWL Data Availability \& Co-Location}
  \begin{columns}[T]
    \begin{column}{0.50\textwidth}
      \begin{block}{Well Inventory}
        \begin{itemize}
          \item \textbf{Total wells inspected:} 306 (Quality flags assigned)
          \item \textbf{Wells with screen depths:} 183 / 306
          \item \textbf{Co-located with MLCW:} 21 / 39 stations
          \item \textbf{Unique screen depths:} [TBD after parsing]
        \end{itemize}
        \medskip
        \small Source: \fpath{gwl\_allwells\_flat.xlsx}
      \end{block}
    \end{column}
    \begin{column}{0.46\textwidth}
      \begin{block}{Spatial Coverage}
        [INSERT MAP FIGURE: GWL wells as dots; 21 overlaid on MLCW stations in green]
        \medskip
        \small
        Green: GWL + MLCW co-location (21 stations)\\
        Red: MLCW only (18 stations)\\
        Blue: GWL only (162 wells without MLCW)
      \end{block}
    \end{column}
  \end{columns}
\end{frame}

%
```

**Frame C2: Screen Depth Harmonisation (16/16)**
```latex
\begin{frame}{\dsgwl{} (16/16) — Screen Depth Mapping to MLCW Levels}
  \begin{columns}[T]
    \begin{column}{0.50\textwidth}
      \begin{block}{Problem}
        \begin{itemize}
          \item MLCW: 60 discrete levels (5 m spacing, 0–295 m)
          \item GWL screens: arbitrary depth intervals (e.g., 40–52 m, 61–79 m)
          \item \textbf{Goal:} Assign each well screen to nearest MLCW level(s)
        \end{itemize}
      \end{block}
      \begin{block}{Harmonisation Strategy}
        \begin{enumerate}
          \item Parse screen top / screen bot from well info
          \item Find MLCW levels within ±2.5 m of screen midpoint
          \item If multiple levels overlap: use weighted average GWL
          \item Document assignment in output CSV
        \end{enumerate}
      \end{block}
    \end{column}
    \begin{column}{0.46\textwidth}
      \begin{block}{Output: Well-Depth Pairs}
        \small
        \renewcommand{\arraystretch}{1.1}
        \begin{tabular}{lcc}
          \toprule
          Well & Screen (m) & MLCW Level \\
          \midrule
          GW001 & 40–52 & 45 m (assigned) \\
          GW001 & 61–79 & 65 m (assigned) \\
          GW002 & 30–40 & 35, 40 m (multiple) \\
          \bottomrule
        \end{tabular}
        \vspace{0.4em}
        \small \textbf{Output file:} \fpath{gwl\_mlcw\_depth\_mapping.csv}
      \end{block}
    \end{column}
  \end{columns}
\end{frame}

%
```

**Data sources to cite:**
- GWL well info: `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\gwl_allwells_flat.xlsx`
- MLCW station locations: `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\MLCW_5m_regular/`
- Reference: `D:\110_PROJECT_002\CLAUDE.md` "Data-Priority Rule" (GWL co-location)

---

## 10. Validation Before Committing

### 10.1 LaTeX Syntax Checklist

Before saving the presentation, verify:

- [ ] All `\begin{frame}` matched with `\end{frame}` (count opening and closing tags)
- [ ] All `\begin{columns}` matched with `\end{columns}`
- [ ] All `\begin{block}` matched with `\end{block}`
- [ ] All `\begin{tabular}` matched with `\end{tabular}`
- [ ] Blank `%` comment line after every `\end{frame}`
- [ ] All `\dsmlcw{}`, `\dsinsar{}`, `\dsgwl{}`, `\dsstrat{}` macros have closing braces
- [ ] All file paths enclosed in `\fpath{...}`
- [ ] All inline math wrapped in `$ $`; display math in `\[ \]`

**Quick check (PowerShell):**
```powershell
$file = "D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\presentation\dataset_overview.txt"
$content = Get-Content $file -Raw
$begin_frame = [regex]::Matches($content, "\\begin\{frame\}").Count
$end_frame = [regex]::Matches($content, "\\end\{frame\}").Count
Write-Host "begin{frame}: $begin_frame, end{frame}: $end_frame"
```

### 10.2 Frame Numbering Consistency Check

When adding N new frames:

1. **Count total new frame count:** old_count + N
2. **Update all frame titles** from `(K/old_count)` to `(K/new_count)`
3. **Verify sequential numbering:** 4/M, 5/M, 6/M, ..., (old_count + N)/M
4. **Use find-and-replace wisely:**
   - Find: `/10)`
   - Replace with: `/13)` (if adding 3 frames)
   - **Verify first** on 2–3 occurrences before replacing all.

### 10.3 Data Accuracy Spot-Check

Before committing new frames, verify key numbers against source files:

| Number | Source File | Acceptable Range |
|--------|-------------|-----------------|
| 39 (total stations) | `D:\110_PROJECT_002\CLAUDE.md` | Must be exactly 39 |
| 19 (active post-2021) | `D:\110_PROJECT_002\discussion_memory.md` | Must be exactly 19 |
| 60 (active depth levels) | `D:\110_PROJECT_002\CLAUDE.md` | Must be exactly 60 |
| 785 (InSAR epochs) | `D:\110_PROJECT_002\MEMORY.md` | Check feather file; 785 ± 5 acceptable |
| 0.52 (direct ratio median sum) | `*_direct_ratio_stats.csv` batch | ±0.02 acceptable (recalculate if changed) |
| 6× (spatial heterogeneity) | `*_direct_ratio_stats.csv` batch | Recalculate: max_sum / min_sum |
| $r = 0.984$ (Pearson correlation) | Regularised inversion results | Verify from actual Stage 1 output |
| 2022 Drought Gap | `discussion_memory.md` Section 4 | Confirmed event; do not modify |

**If adding validation results:**
- Do not round RMSE values. Cite to 2 decimal places (e.g., X.XX mm).
- If using median RMSE, also report Q1, Q3 (interquartile range).
- If using R², cite both in-sample and out-of-sample.

### 10.4 Insertion Point Verification

Ensure new frames are inserted:
- **Before:** The line `% ============================================================\section{Dataset 2: InSAR}`
- **After:** The last existing MLCW frame (`\end{frame}` of frame 10/10)
- **Never:** Between any two existing frames (unless explicitly splitting a topic)

### 10.5 Color Usage Verification

Verify macro usage:
- MLCW section frames start with `\dsmlcw{}`
- InSAR section frames start with `\dsinsar{}`
- GWL section frames start with `\dsgwl{}`
- Do not mix macros (e.g., use `\dsinsar{}` in an MLCW section)

---

## 11. Final Checklist Before Deployment

Use this checklist when committing new frames:

```
□ All LaTeX syntax valid (matched braces, closing tags)
□ Frame numbering updated in all titles (e.g., X/10 → X/13)
□ New frames numbered sequentially and correctly
□ Data accuracy verified (spot-check 39, 19, 60, 785, 0.52, etc.)
□ All file paths use \fpath{} macro
□ All colored dataset references use correct macros (\dsmlcw{}, etc.)
□ Equations have explanatory text after them
□ Table font sizes appropriate (\small or normal, not \scriptsize)
□ \vspace{} used to separate blocks (0.3em to 1.0em)
□ Blank % line after every \end{frame}
□ Citation format correct (script names, file paths, data sources)
□ Insertion point verified (before InSAR section marker)
□ No duplicate frame content with existing frames
□ Tone consistent with rest of presentation (physics-first, clear)
□ Visual elements (tables, equations) enhance understanding
□ Frame titles follow naming convention (N/M — Verb Object)
```

---

## 12. Quick Reference: Common Code Snippets

### Two-Column Layout with Block Titles
```latex
\begin{frame}{\dsmlcw{} (N/M) — Frame Title}
  \begin{columns}[T]
    \begin{column}{0.48\textwidth}
      \begin{block}{Left Block Title}
        Content here
      \end{block}
    \end{column}
    \begin{column}{0.48\textwidth}
      \begin{block}{Right Block Title}
        Content here
      \end{block}
    \end{column}
  \end{columns}
\end{frame}

%
```

### Summary Statistics Table
```latex
\small
\renewcommand{\arraystretch}{1.15}
\begin{tabular}{lc}
  \toprule
  \textbf{Metric} & \textbf{Value} \\
  \midrule
  Statistic 1 & Value \\
  Statistic 2 & Value \\
  \bottomrule
\end{tabular}
```

### Colour-Coded Table with Rows
```latex
\small
\renewcommand{\arraystretch}{1.2}
\begin{tabular}{p{2.8cm} p{3.8cm} p{3.9cm}}
  \toprule
  \textbf{Column 1} & \textbf{Column 2} & \textbf{Column 3} \\
  \midrule
  \rowcolor{mlcw!10}
  Row 1 & Data & Data \\
  \rowcolor{mlcw!10}
  Row 2 & Data & Data \\
  \rowcolor{derived!10}
  Row 3 & Data & Data \\
  \bottomrule
\end{tabular}
```

### Alertblock (for critical info)
```latex
\begin{alertblock}{Alert Title}
  \textbf{Key point:} Description of the issue or finding.
\end{alertblock}
```

### Math with Explanation
```latex
Per station $s$, depth $k$, epoch $i$:
\[
  f_k(i) = \frac{Y_s(i, k)}{x_s(i)}
\]
where $Y_s$ = MLCW compaction (mm), $x_s$ = InSAR displacement (mm).
```

---

## Appendix: File Locations Reference

| Item | Path |
|------|------|
| Presentation source | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\presentation\dataset_overview.txt` |
| Extension rules (this file) | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\presentation\EXTENSION_RULES.md` |
| Project memory (persistent) | `D:\110_PROJECT_002\discussion_memory.md` |
| Project instructions | `D:\112_PROJECT_002\CLAUDE.md` |
| Data scripts root | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\` |
| MLCW 5m grid (all 39 stations) | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\MLCW_5m_regular\` |
| Direct ratio (39 files) | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\direct_ratio_MLCW_InSAR\` |
| InSAR at stations (feather) | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\InSAR_timeries\mlcw_interp_insar_IDW_extend.feather` |
| InSAR at grid (feather) | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\InSAR_timeries\gridpnt_500m_interp_insar_IDW_extend.feather` |
| GWL well data | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\gwl_allwells_flat.xlsx` |
| WRA well info (yearbook) | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\well_info_combined.xlsx` |
| Hydrofacies (BME-derived) | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\mlcw_hydrofacies_5m.csv` |
| Alpha priors | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\alpha_comparison_all_stations_v3.csv` |
| Inversion code (Stage 1) | `D:\112_PROJECT_002\` |

---

**End of EXTENSION_RULES.md**
