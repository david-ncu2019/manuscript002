# Figure 3 Deformation Label Provenance

## Purpose

Figure 3 was regenerated on 2026-09-01 so that the horizontal axis uses the manuscript-wide term `Deformation (mm)` instead of `Compaction (mm)`. The plotted data, sign convention, lithology categories, colors, layout, dimensions, and plotting parameters were not changed.

## Active Assets

- Manuscript source: `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\sections\dataset003.tex`
- Generating script: `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\scripts\plot_tuku_lithology_and_deformation.py`
- Generated figure: `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\figures\fig_dataset_tuku_lithology_and_deformation.png`

The previous script and figure were preserved without modification:

- `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\scripts\plot_composite_ms2.py`
- `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\figures\fig_composite_ms2_dataset_TUKU.png`

## Data Sources

- Borehole lithology: `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\raw_data\05_borehole_materials\TUKU\borehole.csv`
- Ring-by-ring MLCW series: `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\001_data\mlcw\modeled\TUKU_ringbyring.csv`

## Controlled Change

The new script is a copy of the previous script with only four classes of edits:

1. The module description identifies panel B as MLCW deformation.
2. The documented run command uses the new script name.
3. The output path uses the new figure name.
4. The horizontal axis label is `Deformation (mm)`.

The internal compaction-positive sign convention remains unchanged. No data preparation, numerical transformation, plotting style, or panel geometry was modified.

## Reproduction

Run from `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1`:

```powershell
$env:PYTHONPATH=""
$env:MPLBACKEND="Agg"
conda run -n fafalab2 python scripts/plot_tuku_lithology_and_deformation.py
```

The run completed successfully with 3,000 borehole layers, 23 MLCW rings, and 181 observation dates from 2010-01-19 through 2024-12-04. Both the old and new figures have dimensions of 3,720 by 3,011 pixels. File hashes and the generation timestamp are recorded in `manifest.json`.

## Verification

- The new figure was inspected at its original resolution.
- The horizontal axis reads `Deformation (mm)`.
- The lithology panel, MLCW curves, timeline color scale, ring-depth labels, six section labels, and shared depth axis remain present and correctly framed.
- The previous script and figure remain available at their original paths.
- The manuscript build and final page-level inspection are recorded in the proofreading resolution log after completion.
