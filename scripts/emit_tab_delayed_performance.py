"""Emit the LaTeX body rows for the section 4.1 performance and interval table.

Destination: sections/results_discussion_draft.tex, table label
tab:delayed_performance_interval.

Source: the frozen run_048 result table for the delayed-data walk-forward
evaluation. The source filename carries the prefix sec4_1_ because the analysis
folder is named by an earlier outline ordering; that analysis is what the
manuscript now reports as section 4.1.

Every value is printed at exactly three decimal places, per the manuscript's
display rule. Empirical coverage is stored in the source as a fraction and is
printed here as a percentage, also at three decimals. The source file retains
full precision and is never rewritten by this script.

The interval described by the coverage and width columns is a Bayesian
posterior predictive interval, y_pred +/- 1.645 * y_std, obtained from
BayesianRidge.predict(..., return_std=True). It is not a split-conformal
interval and must never be labelled as one.

Run with, from the worktree root:

    $env:PYTHONPATH=""; conda run -n fafalab2 python scripts/emit_tab_delayed_performance.py

Paste the printed rows into the table body. Nothing is written to disk.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

SOURCE_CSV = Path(
    r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests"
    r"\014_ml_nowcast\experiments\section_pooled\run_048\supplements"
    r"\manuscript_results002\sec4_1_combined_performance_interval_table.csv"
)

SECTION_ORDER = ["S1", "S2", "S3", "S4", "S5", "S6"]
POOLED_LABEL = "All"

EXPECTED_ROWS = 7
EXPECTED_POOLED_N = 828
EXPECTED_SECTION_N = 138


def load_source() -> pd.DataFrame:
    """Read the frozen result table and check its shape before formatting."""
    frame = pd.read_csv(SOURCE_CSV)

    if len(frame) != EXPECTED_ROWS:
        raise SystemExit(
            f"Expected {EXPECTED_ROWS} rows (six sections plus the pooled row), "
            f"found {len(frame)} in {SOURCE_CSV.name}."
        )

    missing = set(SECTION_ORDER + [POOLED_LABEL]) - set(frame["section"])
    if missing:
        raise SystemExit(f"Source table is missing rows for {sorted(missing)}.")

    pooled_n = int(frame.loc[frame["section"] == POOLED_LABEL, "n"].iloc[0])
    if pooled_n != EXPECTED_POOLED_N:
        raise SystemExit(
            f"Pooled row reports n={pooled_n}, expected {EXPECTED_POOLED_N}. "
            "The source snapshot may have changed."
        )

    for section in SECTION_ORDER:
        section_n = int(frame.loc[frame["section"] == section, "n"].iloc[0])
        if section_n != EXPECTED_SECTION_N:
            raise SystemExit(
                f"Section {section} reports n={section_n}, expected "
                f"{EXPECTED_SECTION_N}."
            )

    return frame.set_index("section")


def format_row(section: str, row: pd.Series) -> str:
    """Return one LaTeX table row with every numeric field at three decimals."""
    coverage_percent = 100.0 * float(row["empirical_coverage"])
    return (
        f"    {section} & {int(row['n'])} & {float(row['r2']):.3f} & "
        f"{float(row['rmse']):.3f} & {float(row['mae']):.3f} & "
        f"{coverage_percent:.3f} & "
        f"{float(row['mean_interval_width_mm_per_month']):.3f} \\\\"
    )


def main() -> None:
    frame = load_source()

    print(f"% Emitted from {SOURCE_CSV.name} by scripts/emit_tab_delayed_performance.py")
    for section in SECTION_ORDER:
        print(format_row(section, frame.loc[section]))
    print(r"    \midrule")
    print(format_row(POOLED_LABEL, frame.loc[POOLED_LABEL]))


if __name__ == "__main__":
    main()
