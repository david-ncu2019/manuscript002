# Manuscript checkpoint before Discussion Section 5.2 restructuring

Timestamp: 2026/08/26 00:01:47 +08:00

Branch: `reduced_v1`

## Purpose

This checkpoint preserves the current manuscript immediately before restructuring Discussion Section 5.2. It provides a clear return point if the next writing pass disrupts the approved story or section flow.

## Manuscript state

- Results Sections 4.1--4.3 are present in `sections/results004.tex`.
- Discussion Section 5.1 is present in `sections/discuss003.tex` and has received a paragraph-flow review.
- Every prose paragraph currently present in `sections/discuss003.tex` has an adjacent `% NOTE : ... %` block explaining its role in the argument.
- All original author comments beginning with `% my note` remain in place.
- Methods includes the matched-calendar and cycle-resampling explanation used by the Discussion comparisons.
- Appendix and Supplementary Materials provide methodological equations and supporting tables, respectively.
- Superseded section files were removed from `sections/` after being collected in `trash/unused_section_tex_20260825_155014.zip`.

## Next approved writing step

Discussion Section 5.2 has not yet been restructured. The next pass will divide it into two linked parts:

1. `Longer intervals between depth-specific checks`
2. `Consequences without subsequent depth-specific checks`

The first sentence of each part must identify the corresponding MLCW scenario from Methods and Results. The argument must continue directly from Section 5.1: continuous observations support monthly estimation between direct MLCW checks, while the reduced-frequency and no-subsequent-measurement experiments quantify what changes as those checks become less frequent or cease.

Coverage must be interpreted as undercoverage that differs among depth sections. The text must not claim that coverage decreases systematically from one scenario to another because the reported ranges overlap and summarize different scenario sets. Detailed coverage interpretation should continue to point to `\Cref{subsec:predictive_uncertainty}`.

The planned closing statements for Section 5.2 are:

> By quantifying the monthly and cumulative consequences of longer measurement intervals, these results provide a basis for adapting MLCW monitoring schedules while preserving direct depth-specific checks.

> They do not identify a preferred measurement interval or initial-record length and do not support ending MLCW measurements.

Existing `% NOTE` and `% my note` comments must not be deleted or overwritten during this restructuring. When a previous note records a superseded decision, keep it and add a new `% AUTHOR RESPONSE` or `% NOTE` below it.

## Verification state

The full manuscript build must be rerun immediately before the checkpoint commit. Known layout warnings before that rerun were:

- an overfull box of approximately 13.39 pt in the Section 4.2 table;
- an overfull box of approximately 0.50 pt in Methods.

These warnings predate this checkpoint and should not be mistaken for regressions introduced by the next Discussion edit.

## Files intentionally outside this checkpoint

Scratch notebooks, notebook checkpoints, temporary bibliography files, local skill state, raw citation downloads, and figure-preview sandboxes are not part of the manuscript checkpoint. They remain untracked and must not be treated as approved manuscript sources.

## Recovery

The commit containing this note is tagged locally as `checkpoint-before-discussion-5-2-restructure-20260826`. To inspect the saved state, run:

```powershell
git show --stat checkpoint-before-discussion-5-2-restructure-20260826
```

Create a new branch from the tag when a rollback workspace is needed. Do not merge this worktree into another manuscript branch.
