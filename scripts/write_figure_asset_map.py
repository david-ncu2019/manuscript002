"""Write figures/figure_asset_map.json, the provenance record for the section 4 figures.

Every path stored is repository-relative, and every source is pinned by the
analysis-repository commit that produced it. Absolute paths are deliberately
excluded so the record stays valid on another machine.

File sizes and modification times are read from disk rather than typed, so the
record cannot drift from the files it describes.

Run with, from the worktree root:

    $env:PYTHONPATH=""; conda run -n fafalab2 python scripts/write_figure_asset_map.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

WORKTREE = Path(__file__).resolve().parent.parent
OUTPUT_JSON = WORKTREE / "figures" / "figure_asset_map.json"

ANALYSIS_REPO = "20260427_InSAR_MLCW_v3"
ANALYSIS_REPO_BRANCH = "run048-tuku-no-update-sensitivity"

# Repository-relative root of the frozen result folder inside the analysis repo.
ANALYSIS_RESULTS_ROOT = (
    "007_tests/014_ml_nowcast/experiments/section_pooled/run_048"
    "/supplements/manuscript_results002"
)
ANALYSIS_CHECKPOINT_ROOT = (
    "007_tests/014_ml_nowcast/experiments/section_pooled/run_048"
    "/checkpoints/P0/level1a"
)

FIGURES = [
    {
        "figure_number": 7,
        "latex_label": "fig:results_delayed_monthly_estimates",
        "destination": "figures/fig_results_delayed_performance.pdf",
        "subsection": "4.1 Monthly estimation during delayed MLCW data delivery",
        "subsection_label": "subsec:results_delayed_delivery",
        "mirrors_methods_subsection": "subsec:delayed_evaluation",
        "legacy_source_prefix": "sec4_1_",
        "source_stem": "fig7_delayed_monthly_estimates",
        "generator": f"{ANALYSIS_RESULTS_ROOT}/build_fig7_delayed_monthly_estimates.py",
        "generator_commit": "7ed7bc9fc37e2902d7373e18385da048168ae8db",
        "data_source": f"{ANALYSIS_CHECKPOINT_ROOT}/predictions.parquet",
        "data_filter": (
            "station TUKU, sections S1-S6, predictor bayesian_ridge, protocol "
            "rolling_blocked, model_mode local, then only fold groups carrying "
            "six distinct months; 828 rows, 138 per section, 23 complete blocks"
        ),
        "snapshot_pin": "20260718_run048_v1",
        "evaluation_span": "2013-05-01 to 2024-10-01",
        "interval_method": (
            "Bayesian posterior predictive, y_pred +/- 1.645*y_std from "
            "BayesianRidge.predict(..., return_std=True); NOT split-conformal"
        ),
        "verified_against": (
            f"{ANALYSIS_RESULTS_ROOT}/sec4_1_combined_performance_interval_table.csv; "
            "the generator asserts pooled coverage 0.7801932367149759 and mean "
            "interval width 0.9043360111248384 at full precision"
        ),
        "model_refit": False,
    }
]

OLD_TO_NEW_SUBSECTION_MAP = {
    "sec4_1_*": "4.1 delayed MLCW data delivery (Figure 7)",
    "sec4_3_*": "4.2 reduced MLCW measurement frequency (Figure 8, not yet built)",
    "sec4_4_*": "4.3 absence of subsequent MLCW measurements (Figure 9, not yet built)",
    "sec4_2_*": "4.4 coefficients of driving factors (Figure 10, not yet built)",
    "note": (
        "Source filenames follow an earlier outline ordering. The manuscript "
        "subsection order changed; this map is authoritative."
    ),
}

HARD_CONSTRAINTS = [
    "The interval in Figure 7 is a Bayesian posterior predictive interval, "
    "y_pred +/- 1.645*y_std. It is not split-conformal and must never be "
    "labelled as one.",
    "No reader-visible element in any figure contains an internal profile or "
    "level identifier. Verified with pdftotext.",
    "Figures are generated from frozen checkpoints. No model is refit.",
    "Every decimal shown in the manuscript prose, tables, and captions carries "
    "exactly three decimal places, while source files and in-code assertions "
    "retain full precision.",
]

SUPPLEMENTARY_NOT_IN_MAIN_TEXT = {
    "location": ANALYSIS_RESULTS_ROOT,
    "reason": (
        "Excluded from the main text by author decision. Retained in the "
        "analysis repository with this record describing provenance, and not "
        "force-added to the manuscript repository."
    ),
    "files": (
        [
            f"sec4_2_driving_features_S{section}_page{page}.png"
            for section in range(1, 7)
            for page in range(1, 4)
        ]
        + [f"sec4_2_fitting_parameters_S{section}.png" for section in range(1, 7)]
    ),
}


def describe(path: Path) -> dict:
    """Return size and modification time read from disk."""
    stat = path.stat()
    return {
        "size_bytes": stat.st_size,
        "mtime_utc": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(
            timespec="seconds"
        ),
    }


def main() -> None:
    entries = []
    for figure in FIGURES:
        destination = WORKTREE / figure["destination"]
        if not destination.exists():
            raise SystemExit(f"Destination file is missing: {figure['destination']}")

        entry = dict(figure)
        entry["source_pdf"] = f"{ANALYSIS_RESULTS_ROOT}/{figure['source_stem']}.pdf"
        entry["source_png"] = f"{ANALYSIS_RESULTS_ROOT}/{figure['source_stem']}.png"
        entry["source_png_dpi"] = 300
        entry["destination_file"] = describe(destination)
        entry["tracked_in_git"] = (
            "force-added; .gitignore excludes every image extension"
        )
        entries.append(entry)

    document = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "purpose": (
            "Provenance record for the manuscript section 4 figures. Maps each "
            "generated source file in the analysis repository to its destination "
            "in this manuscript worktree, pinned by the commit that produced it. "
            "Drives the rename to Figure N at final submission."
        ),
        "analysis_repository": ANALYSIS_REPO,
        "analysis_repository_branch": ANALYSIS_REPO_BRANCH,
        "path_convention": (
            "All paths are repository-relative. No \\graphicspath is declared in "
            "the manuscript, so LaTeX resolves figures/<name> from the worktree "
            "root."
        ),
        "old_to_new_subsection_map": OLD_TO_NEW_SUBSECTION_MAP,
        "hard_constraints": HARD_CONSTRAINTS,
        "figures": entries,
        "supplementary_material_not_in_main_text": SUPPLEMENTARY_NOT_IN_MAIN_TEXT,
    }

    OUTPUT_JSON.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_JSON.relative_to(WORKTREE)}")
    for entry in entries:
        print(
            f"  Figure {entry['figure_number']}: {entry['destination']} "
            f"({entry['destination_file']['size_bytes']} bytes)"
        )


if __name__ == "__main__":
    main()
