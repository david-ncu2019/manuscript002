"""Categorize 2S-TOOL results by output quality.

Assigns each processed (station, layer) to one of 5 categories:
  ERROR     — pipeline failed (SVD, zero displacement)
  HIGH_SKV  — S_kv ≥ 0.5 (geologically extreme)
  LOW_LOOPS — n_accepted_loops < 3 (unreliable S_ke)
  NEG_SKV   — S_kv < 0 (elastic-dominated, needs review)
  OK        — physically reasonable

Categories are mutually exclusive — files are assigned to the
highest-priority matching category.

Outputs:
  data/gwl/2stool_outputs/quality/
    category_OK.csv
    category_HIGH_SKV.csv
    category_LOW_LOOPS.csv
    category_NEG_SKV.csv
    category_ERROR.csv
    quality_summary.txt

Usage:
    python scripts/09_trackB/categorize_2stool_results.py
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SUMMARY_CSV = (
    PROJECT_ROOT / "data" / "gwl" / "2stool_outputs" / "2stool_results_summary.csv"
)
OUTPUT_DIR = PROJECT_ROOT / "data" / "gwl" / "2stool_outputs" / "quality"

# ── Known pipeline failures (3 files with zero displacement → SVD error) ──

KNOWN_ERRORS = [
    {"station": "JIANYANG", "layer": "F3", "file": "2STOOL_JIANYANG_F3.xlsx",
     "reason": "SVD did not converge — all displacement values = 0"},
    {"station": "JIAXING",  "layer": "F4", "file": "2STOOL_JIAXING_F4.xlsx",
     "reason": "SVD did not converge — all displacement values = 0"},
    {"station": "XINXING",  "layer": "F4", "file": "2STOOL_XINXING_F4.xlsx",
     "reason": "SVD did not converge — all displacement values = 0"},
]

CATEGORY_PRIORITY = ["ERROR", "HIGH_SKV", "LOW_LOOPS", "NEG_SKV", "OK"]


def assign_category(row: pd.Series) -> str:
    if row["skv"] is None or np.isnan(row["skv"]):
        return "ERROR"
    if row["skv"] >= 0.5:
        return "HIGH_SKV"
    if row["n_accepted_loops"] < 3:
        return "LOW_LOOPS"
    if row["skv"] < 0:
        return "NEG_SKV"
    return "OK"


def main():
    # ── Read summary ──
    if not SUMMARY_CSV.exists():
        logger.error(f"Summary not found: {SUMMARY_CSV}")
        logger.error("Run collect_2stool_results.py first.")
        return

    df = pd.read_csv(SUMMARY_CSV)
    logger.info(f"Read {len(df)} rows from {SUMMARY_CSV}")

    # ── Assign categories ──
    df["category"] = df.apply(assign_category, axis=1)

    counts = df["category"].value_counts()
    total_classified = counts.sum()
    logger.info(f"Classified: {total_classified} / {len(df)} rows from CSV")

    # ── Append known errors not in summary CSV ──
    error_rows = df[df["category"] == "ERROR"]
    n_csv_errors = len(error_rows)
    for err in KNOWN_ERRORS:
        if not ((df["station"] == err["station"]) & (df["layer"] == err["layer"])).any():
            error_rows = pd.concat([
                error_rows,
                pd.DataFrame([{
                    "station": err["station"],
                    "layer": err["layer"],
                    "file": err["file"],
                    "category": "ERROR",
                    "skv": np.nan,
                    "ske_weighted": np.nan,
                    "n_loops": 0,
                    "n_accepted_loops": 0,
                }])
            ], ignore_index=True)

    logger.info(f"Total ERROR (CSV + known): {len(error_rows)} "
                f"({n_csv_errors} from CSV, {len(error_rows) - n_csv_errors} added)")

    # ── Write per-category CSVs ──
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    category_dfs = {cat: df[df["category"] == cat].copy() for cat in CATEGORY_PRIORITY}
    category_dfs["ERROR"] = error_rows  # use the merged version

    for cat in CATEGORY_PRIORITY:
        sub = category_dfs[cat]
        out_path = OUTPUT_DIR / f"category_{cat}.csv"
        sub.to_csv(out_path, index=False)
        logger.info(f"  {cat:12s} → {out_path.name}  ({len(sub)} rows)")

    # ── Summary text ──
    lines = [
        "2S-TOOL Results — Quality Categorization",
        "========================================",
        f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}",
        f"Source: {SUMMARY_CSV}",
        "",
        f"{'Category':<20s} {'Count':>6s}  {'Description':s}",
        f"{'-'*20} {'-'*6}  {'-'*40}",
    ]
    for cat in CATEGORY_PRIORITY:
        cnt = len(category_dfs[cat])
        desc = {
            "ERROR": "Pipeline failure (SVD, zero displacement)",
            "HIGH_SKV": f"S_kv ≥ 0.5 — geologically extreme",
            "LOW_LOOPS": f"< 3 accepted hysteresis loops — unreliable S_ke",
            "NEG_SKV": f"S_kv < 0 — elastic-dominated, needs review",
            "OK": "Physically reasonable, ready for analysis",
        }[cat]
        lines.append(f"{cat:<20s} {cnt:>6d}  {desc}")

    lines.append("")
    lines.append(f"{'TOTAL':<20s} {sum(len(category_dfs[cat]) for cat in CATEGORY_PRIORITY):>6d}")
    lines.append("")

    # ── Additional diagnostics ──
    ok = category_dfs["OK"]
    if not ok.empty:
        lines.append(f"OK files: S_kv range [{ok['skv'].min():.4e}, {ok['skv'].max():.4e}]")
        lines.append(f"  S_ke_w range [{ok['ske_weighted'].min():.4e}, {ok['ske_weighted'].max():.4e}]")
        lines.append(f"  Across {ok['station'].nunique()} stations")

    neg = category_dfs["NEG_SKV"]
    if not neg.empty:
        lines.append(f"NEG_SKV files: S_kv range [{neg['skv'].min():.4e}, {neg['skv'].max():.4e}]")
        lines.append(f"  S_kv median {neg['skv'].median():.4e}")
        lines.append(f"  S_ke_w median {neg['ske_weighted'].median():.4e}")
        lines.append(f"  Across {neg['station'].nunique()} stations")
        # Stations with ALL layers negative
        all_neg_stations = neg.groupby("station").filter(
            lambda g: len(g) >= 3 and len(g) == len(df[df["station"] == g.name])
        )["station"].unique()
        if len(all_neg_stations):
            lines.append(f"  Stations with ALL layers negative: {', '.join(sorted(all_neg_stations))}")

    summary_txt = "\n".join(lines)

    summary_path = OUTPUT_DIR / "quality_summary.txt"
    summary_path.write_text(summary_txt)
    logger.info(f"Summary → {summary_path}")

    print(f"\n{summary_txt}")


if __name__ == "__main__":
    main()
