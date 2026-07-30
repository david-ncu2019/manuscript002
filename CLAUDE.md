# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

LaTeX manuscript for the PhD paper on land subsidence in the Choushui River Fluvial Plain (CRFP), Taiwan — integrating SBAS-InSAR surface deformation, GNSS, groundwater levels, and multilayer compaction monitoring wells (MLCWs: TUKU, GUANGFU, HUWEI, HONGLUN, XIUTAN). The scientific source of truth (methods, results, sign conventions, terminology) is the analysis project — see `D:\112_PROJECT_002\CLAUDE.md` and its ML-nowcasting status blocks. Numbers cited in the manuscript must trace back to that project's result files, not memory.

## Build

MiKTeX is installed. Compile from the repo root (figure paths are relative to root, not to `sections/`):

```
latexmk -pdf main.tex     # full build: pdflatex + bibtex (natbib) + reruns
latexmk -c                # clean aux files
```

`main.tex` is the only compile target. Do not compile files in `sections/` standalone (the stray `sections/dataset002.log` is leftover from doing that).

## Structure and conventions

- **Sections are versioned, not edited in place.** `sections/` holds numbered variants (`dataset001.tex`, `dataset002.tex`, `methods002.tex`, ...). `main.tex` `\input`s exactly one variant per section — check `main.tex` first to find the active file before editing anything. Superseded variants stay on disk for reference.
- **Active bibliography is `writing_manu2.bib`** (`\bibliography{writing_manu2}` in main.tex). `ref_manu2.bib` and the files under `bibtex/` are legacy imports — to cite something from them, copy the entry into `writing_manu2.bib`.
- **Citations:** natbib author-year (`plainnat`). Use `\citep{}` / `\citet{}`. Cross-references use cleveref `\Cref{}`.
- **Git ignores all binary/derived content** (`*.png`, `*.jpg`, `*.pdf`, `*.pptx`, `*.txt`, LaTeX aux files). `figures/`, `draft/*.txt`, and `main.pdf` exist only on disk — never assume git history can restore them, and back them up before destructive operations.
- **Branches:** active writing happens on `write_v1`; `master` holds milestones.

## Ongoing reframing: GWR → BRR nowcasting (read before writing prose)

The manuscript is mid-pivot from its original method (Geographically Weighted Regression, GWR) to the current method (Bayesian Ridge Regression nowcasting of per-section compaction). Markers in the source:

- `\st{...}` (soul package strikethrough) = text slated for deletion — do not build new prose on top of struck-through claims.
- `% REMOVE GWR ...` comments = legacy GWR narrative kept for manual deletion; hyperref metadata in `main.tex` carries the same markers.

New or revised text must describe the ML nowcasting framing (monthly per-50-m-section compaction from InSAR/GNSS + GWL + lithology), not GWR spatial mapping. When touching a section, prefer finishing the GWR removal in that section over leaving mixed framing.

## Writing state

`intro001` and `studyarea001` are developed prose; `results001`, `discuss001`, and the Conclusion are placeholders. `dataset002.tex` (the active dataset section) contains empty metadata tables (station coordinates, elevations, depths) awaiting real values from the analysis project. `draft/` holds plain-text pre-LaTeX drafts.
