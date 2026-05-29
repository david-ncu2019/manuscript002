"""
batch_v2.py — Batch runner for the unified detrended IHM-F model (v2).

Iterates over all 191 entries in data/ihmf_config.json, calls
fit_ihm_f_v2.run_one() for each, and aggregates results to a summary CSV.

Output:
    results/ihmf/v2/v2_summary.csv

    Columns:
        station, layer, tau_opt, gamma_k_mm_per_m, beta_k_mm_per_mm,
        f_bar_k, r2, rmse_mm,
        fold1_rmse, fold2_rmse, fold3_rmse, fold4_rmse,
        n_folds_produced, gamma_k_zero, beta_k_zero, diagnostics

    gamma_k_zero = True: layer is InSAR-dominated after detrending
                         (expected for F4 at some stations; not a failure)
    beta_k_zero  = True: InSAR provides no information in the dynamic band
    n_folds_produced: number of walk-forward folds with n_test ≥ 1

Usage:
    python scripts/10_ihmf/batch_v2.py [--dry-run] [--station STATION]

    --dry-run : print entries without fitting (verify config parsing)
    --station : run only a single station (for partial re-runs)

Error handling:
    Failed entries are logged to results/ihmf/v2/v2_errors.csv and skipped;
    the batch continues to completion.
"""

import argparse
import json
import traceback
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ── Path setup ───────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH  = PROJECT_ROOT / "data" / "ihmf_config.json"
OUT_DIR      = PROJECT_ROOT / "results" / "ihmf" / "v2"

from fit_ihm_f_v2 import run_one


# ── Result → flat row ─────────────────────────────────────────────────────────

def _extract_fold_rmse(wf_results: list, fold_label: str) -> float | None:
    """Return RMSE for a specific fold label, or None if skipped/missing."""
    for w in wf_results:
        if w["fold"] == fold_label and not w.get("skipped", False):
            return w["rmse_mm"]
    return None


def result_to_row(r: dict) -> dict:
    """Flatten a run_one result dict to a single-row dict for the CSV."""
    wf = r.get("walk_forward", [])
    n_folds = sum(1 for w in wf if not w.get("skipped", False))
    return {
        "station":           r["station"],
        "layer":             r["layer"],
        "tau_opt":           r["tau_opt"],
        "gamma_k_mm_per_m":  r["gamma_k_mm_per_m"],
        "beta_k_mm_per_mm":  r["beta_k_mm_per_mm"],
        "f_bar_k":           r["f_bar_k"],
        "r2":                r["r2"],
        "rmse_mm":           r["rmse_mm"],
        "fold1_rmse":        _extract_fold_rmse(wf, "Fold1_test2022"),
        "fold2_rmse":        _extract_fold_rmse(wf, "Fold2_test2023"),
        "fold3_rmse":        _extract_fold_rmse(wf, "Fold3_test2024"),
        "fold4_rmse":        _extract_fold_rmse(wf, "Fold4_test2025"),
        "n_folds_produced":  n_folds,
        "gamma_k_zero":      r["gamma_k_mm_per_m"] <= 0.0,
        "beta_k_zero":       r["beta_k_mm_per_mm"] <= 0.0,
        "corr_y_dh_detrended": r.get("corr_y_dh_detrended"),
        "corr_dh_x_detrended": r.get("corr_dh_x_detrended"),
        "diagnostics":       "; ".join(r.get("diagnostics", [])),
    }


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Batch IHM-F v2 fit for all 191 entries.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print entries without fitting.")
    parser.add_argument("--station", default=None,
                        help="Limit batch to a single station.")
    args = parser.parse_args()

    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    entries = cfg["entries"]

    if args.station:
        entries = [e for e in entries if e["station"] == args.station]
        if not entries:
            raise SystemExit(f"No entries for station '{args.station}' in config.")

    print(f"Config: {CONFIG_PATH}")
    print(f"Entries to process: {len(entries)}")
    print(f"Output directory: {OUT_DIR}")

    if args.dry_run:
        for e in entries:
            print(f"  {e['station']:20s}  {e['layer']}")
        print("Dry run complete — no fitting performed.")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows   = []
    errors = []

    for i, entry in enumerate(entries, 1):
        label = f"{entry['station']} {entry['layer']}"
        print(f"\n[{i:3d}/{len(entries)}] {label}")
        try:
            result = run_one(entry, project_root=PROJECT_ROOT)
            rows.append(result_to_row(result))
        except Exception as exc:
            tb = traceback.format_exc()
            print(f"  ERROR: {exc}")
            errors.append({
                "station": entry["station"],
                "layer":   entry["layer"],
                "error":   str(exc),
                "traceback": tb,
            })

    # ── Write summary CSV ─────────────────────────────────────────────────────
    if rows:
        summary_df = pd.DataFrame(rows)
        summary_path = OUT_DIR / "v2_summary.csv"
        summary_df.to_csv(summary_path, index=False)
        print(f"\nSummary written: {summary_path.relative_to(PROJECT_ROOT)}")
        print(f"  Total rows:       {len(summary_df)}")
        print(f"  gamma_k = 0:      {summary_df['gamma_k_zero'].sum()}")
        print(f"  beta_k  = 0:      {summary_df['beta_k_zero'].sum()}")
        print(f"  0 folds produced: {(summary_df['n_folds_produced'] == 0).sum()}")
        if "fold1_rmse" in summary_df:
            n_fold1 = summary_df["fold1_rmse"].notna().sum()
            print(f"  Fold 1 available: {n_fold1} / {len(summary_df)}")

    # ── Write errors CSV ──────────────────────────────────────────────────────
    if errors:
        err_df = pd.DataFrame(errors)
        err_path = OUT_DIR / "v2_errors.csv"
        err_df[["station", "layer", "error"]].to_csv(err_path, index=False)
        print(f"\nErrors ({len(errors)}) written: {err_path.relative_to(PROJECT_ROOT)}")
        for e in errors:
            print(f"  FAILED: {e['station']} {e['layer']} — {e['error']}")

    print(f"\nBatch complete: {len(rows)} succeeded, {len(errors)} failed.")


if __name__ == "__main__":
    main()
