# Section 3.4.3 Revision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task by task. Stop after the Figure 6 preview and obtain author approval before inserting the figure or revising the manuscript.

**Goal:** Rewrite Section 3.4.3 so that readers can follow the fit-once evaluation, distinguish monthly error from cumulative deformation error, and understand how posterior predictive uncertainty is treated when no subsequent MLCW measurements are available.

**Architecture:** Preserve the analytical design implemented by the frozen TUKU P0/level1a permanent-stoppage pipeline. First create and review a standalone Figure 6 preview. After author approval, replace only Section 3.4.3 in `sections/methods005.tex`, insert the approved figure, and compile the manuscript.

**Tech Stack:** LaTeX, TikZ, MiKTeX `pdflatex`, existing Bayesian ridge regression notation.

## Global Constraints

- Work only in `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1` on branch `reduced_v1`.
- Modify only Section 3.4.3 of `sections/methods005.tex` after author approval of the prose and Figure 6 preview.
- Do not modify `sections/dataset003.tex`, `sections/results_discussion_draft.tex`, Figure 4, or Figure 5.
- Apply `david-writing-styles`, including known-to-new progression, one controlling point per paragraph, no first-person pronouns, no em dashes, and no unsupported claims.
- Preserve the implemented design: separate models by depth section, 3-, 5-, and 8-year initial calibration records, no subsequent MLCW input or refitting, monthly GWL and cGNSS predictors continuing after calibration, and retrospective evaluation against withheld monthly MLCW observations.
- Preserve the frozen output facts: prediction horizons of 140, 116, and 80 months and a common comparison horizon of 80 months.
- Use `K` for elapsed months after the initial calibration record, consistent with `k` for a monthly epoch.
- Put every complete formula in a display equation.
- Do not insert numerical Results values into Methods.
- Create Figure 6 as a standalone preview first. Do not insert it into `methods005.tex` until the author approves the rendered preview.

---

### Task 1: Create the Figure 6 Preview

**Files:**
- Create: `trash/figure6_review_previews/figure6_no_subsequent_mlcw_preview.tex`
- Generate: `trash/figure6_review_previews/figure6_no_subsequent_mlcw_preview.pdf`
- Generate: `trash/figure6_review_previews/figure6_no_subsequent_mlcw_preview.png`

**Interfaces:**
- Consumes: the visual vocabulary already used by Figures 4 and 5 in `sections/methods005.tex`.
- Produces: a standalone TikZ preview for author review.

- [ ] **Step 1: Build a two-phase timeline**

  Use equal-width phases titled `Initial historical records` and `Estimation period`. Retain the three physical-quantity rows `Deformation by depth interval`, `Hydraulic head`, and `Vertical surface displacement`.

- [ ] **Step 2: Encode data availability without adding a third conceptual layer**

  Show filled blue markers for the initial historical records. Continue filled blue markers for hydraulic head and vertical surface displacement during the estimation period. Show open gray markers for monthly deformation estimates after the initial record. Do not draw withheld monthly ground truth, orange endpoint observations, an update arrow, or a next-cycle loop.

- [ ] **Step 3: Encode model actions**

  Place `Calibrate model` below the initial record and `Estimate $\widehat{\Delta d}_{s,k}$` below the estimation period. Connect the two boxes with one forward arrow. Add `No recalibration` as a short black annotation below the estimation period. Retain the upward predictor arrow used in Figures 4 and 5.

- [ ] **Step 4: Add the preview caption**

  Use this draft caption:

  ```latex
  \caption{Monthly deformation estimation without subsequent MLCW measurements. Filled blue markers indicate observations available during the initial calibration period. Hydraulic head and vertical surface displacement remained available during the subsequent estimation period, whereas open gray markers indicate monthly deformation estimates. The fitted model and predictor scaling remained unchanged throughout this period. Marker counts and spacing are illustrative rather than exact.}
  ```

  Use this complete standalone preview source:

  ```latex
  \documentclass[tikz,border=8pt]{standalone}
  \usepackage{newtxtext,newtxmath}
  \usetikzlibrary{arrows.meta,positioning,shapes.arrows}

  \begin{document}
  \begin{tikzpicture}[
    x=1.12cm,
    y=1cm,
    font=\small,
    dataset/.style={anchor=east,align=right,font=\small\bfseries,text=black!75},
    phase/.style={font=\small\bfseries,text=black!75,align=center},
    available/.style={circle,draw=blue!60!black,fill=blue!60!black,minimum size=6.3pt,inner sep=0pt},
    estimate/.style={circle,draw=black!55,fill=white,line width=1.0pt,minimum size=7.2pt,inner sep=0pt},
    historyline/.style={draw=blue!55!black,line width=1.1pt},
    estimateline/.style={draw=black!50,densely dashed,line width=0.9pt},
    divider/.style={draw=black!35,densely dashed,line width=0.7pt},
    flow/.style={-{Stealth[length=2.5mm]},draw=black!65,line width=0.8pt},
    fadedarrow/.style={
      single arrow,
      draw=none,
      fill={rgb,255:red,34;green,139;blue,34},
      fill opacity=0.2,
      shape border rotate=90,
      minimum height=1.5cm,
      minimum width=1.0cm,
      single arrow head extend=0.8mm,
      inner sep=1pt
    },
    action/.style={draw=black!65,fill=green!8,rounded corners=2pt,align=center,minimum height=0.85cm,text width=3.05cm,font=\small\bfseries}
  ]
    \node[phase] at (2.00,3.70) {Initial historical records};
    \node[phase] at (6.20,3.70) {Estimation period};

    \node[dataset] at (-0.45,2.55) {Deformation by\\depth interval};
    \node[dataset] at (-0.45,1.55) {Hydraulic head};
    \node[dataset] at (-0.45,0.55) {Vertical surface\\displacement};

    \node[fadedarrow] at (6.20,1.55) {};

    \foreach \y in {1.55,0.55} {
      \draw[historyline] (0.40,\y) -- (8.00,\y);
    }
    \draw[historyline] (0.40,2.55) -- (3.90,2.55);
    \draw[estimateline] (3.90,2.55) -- (8.00,2.55);

    \foreach \y in {2.55,1.55,0.55} {
      \foreach \x in {0.40,1.10,1.80,3.20,3.90} {
        \node[available] at (\x,\y) {};
      }
      \node[fill=white,inner xsep=2pt,text=blue!60!black] at (2.50,\y) {$\cdots$};
    }

    \foreach \y in {1.55,0.55} {
      \foreach \x in {4.60,5.30,7.30,8.00} {
        \node[available] at (\x,\y) {};
      }
      \node[fill=white,inner xsep=2pt,text=blue!60!black] at (6.30,\y) {$\cdots$};
    }
    \foreach \x in {4.60,5.30,7.30,8.00} {
      \node[estimate] at (\x,2.55) {};
    }
    \node[fill=white,inner xsep=2pt,text=black!55] at (6.30,2.55) {$\cdots$};

    \draw[divider] (4.25,-0.2) -- (4.25,4.15);

    \node[action] (calibrate) at (2.00,-0.75) {Calibrate\\model};
    \node[action] (estimatebox) at (6.20,-0.75) {Estimate\\$\widehat{\Delta d}_{s,k}$};
    \draw[flow] (calibrate.east) -- (estimatebox.west);
    \node[font=\small,text=black!70] at (6.20,-1.55) {No recalibration};
  \end{tikzpicture}
  \end{document}
  ```

- [ ] **Step 5: Compile and render the preview**

  Run from `trash/figure6_review_previews/`:

  ```powershell
  pdflatex -interaction=nonstopmode -halt-on-error figure6_no_subsequent_mlcw_preview.tex
  pdftoppm -singlefile -png -r 180 figure6_no_subsequent_mlcw_preview.pdf figure6_no_subsequent_mlcw_preview
  ```

  Expected result: both commands exit with code 0, the two phases have equal widths, labels do not overlap, and no symbol suggests that MLCW observations became available after calibration.

- [ ] **Step 6: Stop for author review**

  Show the PNG preview. Do not continue to Task 2 until the author approves the layout, labels, colors, and caption.

### Task 2: Replace the Section 3.4.3 Prose

**Files:**
- Modify: `sections/methods005.tex`, only `\subsubsection{Sensitivity to permanent monitoring stoppage}` through the paragraph before `\FloatBarrier`.

**Interfaces:**
- Consumes: `\Cref{subsec:predictive_uncertainty}`, `\Cref{subsec:sparse_measurement_sensitivity}`, and `\Cref{eq:sparse_monthly_error}`.
- Produces: a self-contained method description with five error definitions and one Figure 6 cross-reference.

- [ ] **Step 1: Replace the subsection title and opening**

  Change the title to:

  ```latex
  \subsubsection{Sensitivity to the absence of subsequent MLCW measurements}
  ```

  Keep the existing label `subsec:permanent_stoppage_sensitivity` to avoid breaking cross-references. Open by distinguishing this design from the periodic reduced-frequency design. State that the model was calibrated once from 3, 5, or 8 years of monthly observations, after which GWL and cGNSS predictors continued but no later MLCW observation was used for model updating.

- [ ] **Step 2: Explain the retrospective evaluation before defining metrics**

  State that the remaining historical monthly MLCW observations were withheld from fitting and retained only to evaluate the estimates. Refer to the monthly error already defined in `\Cref{eq:sparse_monthly_error}` rather than repeating that equation.

- [ ] **Step 3: Define cumulative signed and absolute cumulative error**

  Insert:

  ```latex
  \begin{equation}
  E_{s,K}
  =
  \sum_{k=1}^{K} e_{s,k},
  \label{eq:stoppage_cumulative_signed_error}
  \end{equation}
  ```

  followed by:

  ```latex
  \begin{equation}
  A_{s,K}
  =
  \left|E_{s,K}\right|.
  \label{eq:stoppage_absolute_cumulative_error}
  \end{equation}
  ```

  Define $K$ as the number of elapsed months after the initial calibration record. Explain that $E_{s,K}$ preserves the direction of accumulated error, whereas $A_{s,K}$ describes the magnitude of the difference between estimated and observed cumulative deformation.

- [ ] **Step 4: Define running monthly MAE and RMSE**

  Insert:

  ```latex
  \begin{equation}
  \operatorname{MAE}_{s,K}
  =
  \frac{1}{K}
  \sum_{k=1}^{K}
  \left|e_{s,k}\right|,
  \label{eq:stoppage_running_mae}
  \end{equation}
  ```

  and:

  ```latex
  \begin{equation}
  \operatorname{RMSE}_{s,K}
  =
  \sqrt{
  \frac{1}{K}
  \sum_{k=1}^{K}
  e_{s,k}^{2}
  }.
  \label{eq:stoppage_running_rmse}
  \end{equation}
  ```

  Explain that these quantities summarize monthly estimation errors accumulated up to horizon $K$. Do not call RMSE a `cumulative RMSE`.

- [ ] **Step 5: Define the secondary horizon-normalized error rate**

  Insert:

  ```latex
  \begin{equation}
  R_{s,K}
  =
  \frac{A_{s,K}}{K}.
  \label{eq:stoppage_horizon_normalized_error}
  \end{equation}
  ```

  State that $R_{s,K}$ expresses absolute cumulative error per elapsed month and was interpreted together with $A_{s,K}$. Explain that signed monthly errors may partly cancel within $E_{s,K}$, so a decreasing $R_{s,K}$ does not by itself imply that cumulative error has stopped growing.

- [ ] **Step 6: Connect monthly posterior uncertainty to the long-horizon design**

  Explain that each monthly estimate retained the posterior predictive interval defined in `\Cref{subsec:predictive_uncertainty}` because the frozen Bayesian ridge model continued to provide a predictive distribution for each monthly predictor row. Clarify that these intervals applied to individual monthly increments. No uncertainty band was constructed for $E_{s,K}$ or $A_{s,K}$ because the dependence among errors from successive months was not modeled in the cumulative calculation.

- [ ] **Step 7: Explain the common comparison horizon and introduce Figure 6**

  State that the 3-, 5-, and 8-year calibration records left 140, 116, and 80 months for evaluation. Compare all three scenarios over their shared 80-month horizon, while treating later months in the shorter-calibration scenarios as scenario-specific extensions. End by referring to the approved Figure 6.

- [ ] **Step 8: Insert the approved Figure 6**

  Copy the approved TikZ block into `sections/methods005.tex` immediately before `\FloatBarrier`. Use:

  ```latex
  \label{fig:no_subsequent_mlcw_design}
  ```

  Do not change Figures 4 or 5.

#### Proposed Section 3.4.3 prose for author review

Use the following block as the complete prose target. Do not insert it into `methods005.tex` until the author approves the wording and the Figure 6 preview.

```latex
\subsubsection{Sensitivity to the absence of subsequent MLCW measurements}
\label{subsec:permanent_stoppage_sensitivity}

A third evaluation examined how the monthly estimates changed when no MLCW measurements became available after an initial calibration record. Separate models were calibrated from the first 3, 5, or 8 years of monthly MLCW observations. After each calibration record ended, monthly GWL and cGNSS observations continued to supply predictor values, but the fitted model and predictor scaling remained fixed. No later MLCW observation was used to update the model.

The remaining historical MLCW observations allowed this hypothetical condition to be evaluated retrospectively. These observations were withheld from model fitting and were used only to compare the observed monthly deformation increments with the estimates generated after the calibration record. The monthly error $e_{s,k}$ was calculated as defined in \Cref{eq:sparse_monthly_error}.

The accumulation of monthly errors was evaluated over the first $K$ months after calibration. The cumulative signed error for section $s$ was

\begin{equation}
E_{s,K}
=
\sum_{k=1}^{K} e_{s,k},
\label{eq:stoppage_cumulative_signed_error}
\end{equation}

and its absolute magnitude was

\begin{equation}
A_{s,K}
=
\left|E_{s,K}\right|.
\label{eq:stoppage_absolute_cumulative_error}
\end{equation}

The signed value $E_{s,K}$ indicated whether the accumulated estimates were above or below the observed cumulative deformation, whereas $A_{s,K}$ described the magnitude of this difference without regard to direction.

Monthly estimation performance through horizon $K$ was summarized separately using

\begin{equation}
\operatorname{MAE}_{s,K}
=
\frac{1}{K}
\sum_{k=1}^{K}
\left|e_{s,k}\right|,
\label{eq:stoppage_running_mae}
\end{equation}

and

\begin{equation}
\operatorname{RMSE}_{s,K}
=
\sqrt{
\frac{1}{K}
\sum_{k=1}^{K}
e_{s,k}^{2}
}.
\label{eq:stoppage_running_rmse}
\end{equation}

These measures described the typical magnitude of the monthly errors accumulated from the end of calibration to horizon $K$. They therefore complemented $A_{s,K}$, which described the difference between the estimated and observed cumulative deformation at that horizon.

To account for the increasing duration of the estimation period, the absolute cumulative error was also expressed per elapsed month as

\begin{equation}
R_{s,K}
=
\frac{A_{s,K}}{K}.
\label{eq:stoppage_horizon_normalized_error}
\end{equation}

The normalized value $R_{s,K}$ was interpreted together with $A_{s,K}$. Because positive and negative monthly errors could partly cancel within $E_{s,K}$, a decrease in $R_{s,K}$ did not necessarily indicate that the absolute cumulative error had stopped growing.

The frozen Bayesian ridge model also provided the posterior predictive interval defined in \Cref{subsec:predictive_uncertainty} for each monthly estimate. These intervals described uncertainty in individual monthly deformation increments throughout the estimation period. They were not accumulated into uncertainty bands for $E_{s,K}$ or $A_{s,K}$ because the dependence among prediction errors from successive months was not represented in the cumulative calculation.

The 3-, 5-, and 8-year calibration records left 140, 116, and 80 months for retrospective evaluation, respectively. All three scenarios were compared over their shared 80-month horizon. The additional months available after the shorter calibration records were retained as scenario-specific extensions rather than direct comparisons with the 8-year scenario. The complete fit-once evaluation is illustrated in \Cref{fig:no_subsequent_mlcw_design}.
```

### Task 3: Verify the Revised Methods Section

**Files:**
- Verify: `sections/methods005.tex`
- Verify: `main.pdf`

**Interfaces:**
- Consumes: the approved Section 3.4.3 prose and Figure 6.
- Produces: a compiled manuscript with resolved labels and unchanged adjacent sections.

- [ ] **Step 1: Run targeted consistency checks**

  Confirm that `methods005.tex` contains no remaining occurrence of `cumulative root mean square error`, `split-conformal` inside Section 3.4.3, or wording that implies GWL and cGNSS stopped with MLCW.

- [ ] **Step 2: Compile the manuscript twice**

  Run from the manuscript root:

  ```powershell
  pdflatex -interaction=nonstopmode -halt-on-error main.tex
  pdflatex -interaction=nonstopmode -halt-on-error main.tex
  ```

  Expected result: both commands exit with code 0 and `fig:no_subsequent_mlcw_design` resolves.

- [ ] **Step 3: Review the rendered subsection**

  Inspect the pages containing Section 3.4.3 and Figure 6. Confirm that equations fit within the margins, the figure remains legible at manuscript width, and paragraph transitions follow this sequence: scenario, withheld evaluation data, monthly errors, cumulative errors, uncertainty, common comparison horizon, figure.

- [ ] **Step 4: Run the scope check**

  ```powershell
  git diff --check -- sections/methods005.tex
  git status --short -- sections/methods005.tex sections/results_discussion_draft.tex sections/dataset003.tex
  ```

  Expected result: no whitespace errors; only `sections/methods005.tex` changes as part of this task; `dataset003.tex` and `results_discussion_draft.tex` remain untouched.

- [ ] **Step 5: Create a checkpoint commit only after author approval**

  ```powershell
  git add sections/methods005.tex
  git commit -m "Refine no-update sensitivity method"
  ```

  Do not stage unrelated existing changes or preview files in `trash/`.

## Self-Review

- The plan covers the subsection title, experimental sequence, retrospective evaluation, five metric definitions, posterior predictive uncertainty, comparison horizons, Figure 6 preview, LaTeX verification, and a scoped checkpoint commit.
- No Results values or changes to `results_discussion_draft.tex` are included.
- The plan preserves all frozen pipeline facts and corrects the misleading `cumulative root mean square error` wording.
- Figure 6 remains a preview until explicit author approval.
