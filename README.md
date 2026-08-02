# Tuku Reduced Manuscript

This folder contains the single-site manuscript draft for monthly depth-resolved aquifer-system compaction estimation at Tuku. It is independent of `../Manuscript` and does not include regional transfer, SBAS-InSAR, or the regional 3D sediment model.

## Build

Run from this directory.

```powershell
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

The draft uses one-sided A4 pages, 25 mm margins, 12 pt Times-like text, 1.5 line spacing, and line numbers for review.

## Draft Boundaries

- The evaluated scenario assumes monthly MLCW observations arrive as a batch after a six-month delay.
- GWL and cGNSS records for each target month are available when compaction is estimated.
- Reduced MLCW sampling at six- or twelve-month intervals is discussed but is not presented as a validated result.
- Yellow text marks values or claims that must be replaced after the operational run.

Use `planning/placeholder_checklist.md` when transferring final metrics and figures into the manuscript.

Before revising the manuscript's novelty claims or reduced-sampling design, consult `planning/20260802_hung2025_overlap_and_novelty_note.md`.
