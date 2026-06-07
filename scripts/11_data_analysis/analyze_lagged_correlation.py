"""
Lagged cross-correlation between MLCW compaction and GWL head / InSAR.

Computes CCF for lags 0-24 and identifies optimal lag per station-layer.

Usage:
    python scripts/11_data_analysis/analyze_lagged_correlation.py
    python scripts/11_data_analysis/analyze_lagged_correlation.py --station TUKU

Output: results/data_analysis/lagged_correlation.csv (full)
        results/data_analysis/lagged_correlation_summary.csv (one row per pair)
"""

import argparse
import json
import numpy as np
import pandas as pd
from pathlib import Path

import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "10_ihmf"))
from ihmf_io import load_and_align

CONFIG_PATH = PROJECT_ROOT / "data/ihmf_config.json"
OUT_DIR = PROJECT_ROOT / "results/data_analysis"
OUT_DIR.mkdir(parents=True, exist_ok=True)
MAX_LAG = 24


def ccf_at_lag(y, driver, lag):
    """Cross-correlation r(y(t), driver(t - lag)) for lag >= 0."""
    if lag >= len(y) - 3:
        return np.nan
    driver_lag = driver[lag:]
    y_cut = y[:len(y) - lag]
    return float(np.corrcoef(y_cut, driver_lag)[0, 1])


def analyze_pair(merged):
    y = merged["mlcw_mm"].values
    h_raw = merged["head_m"].values
    x = merged["insar_mm"].values
    dh = h_raw - h_raw[0]
    n = len(y)

    full_rows = []
    for tau in range(0, min(MAX_LAG + 1, n - 3)):
        r_yh = ccf_at_lag(y, dh, tau)
        r_yx = ccf_at_lag(y, x, tau)
        full_rows.append({"tau": tau, "r_yh_lag": r_yh, "r_yx_lag": r_yx})

    # optimal lag: max |r_yh|
    valid = [r for r in full_rows if not np.isnan(r["r_yh_lag"])]
    if valid:
        best = max(valid, key=lambda r: abs(r["r_yh_lag"]))
        tau_opt = best["tau"]
        r_at_opt = best["r_yh_lag"]
        # sharpness: r_at_opt - mean of other lags
        others = [r["r_yh_lag"] for r in valid if r["tau"] != tau_opt]
        sharpness = abs(r_at_opt) - np.mean(np.abs(others)) if others else 0.0
    else:
        tau_opt = np.nan
        r_at_opt = np.nan
        sharpness = np.nan

    return full_rows, {
        "tau_opt_ccf": tau_opt,
        "r_yh_at_opt": r_at_opt,
        "ccf_peak_sharpness": sharpness,
    }


def main():
    parser = argparse.ArgumentParser(description="Lagged cross-correlation analysis")
    parser.add_argument("--station", type=str, default=None, help="Limit to one station")
    args = parser.parse_args()

    with open(CONFIG_PATH) as f:
        cfg = json.load(f)

    entries = cfg["entries"]
    if args.station:
        entries = [e for e in entries if e["station"] == args.station]
        if not entries:
            raise SystemExit(f"No entries for station '{args.station}'")

    insar_csv = PROJECT_ROOT / cfg["shared"]["insar_csv"]
    full_rows = []
    summary_rows = []
    skipped = 0

    for entry in entries:
        station, layer = entry["station"], entry["layer"]
        try:
            merged, _ = load_and_align(entry, PROJECT_ROOT, insar_csv)
        except Exception:
            skipped += 1
            continue

        lags, summary = analyze_pair(merged)
        for r in lags:
            full_rows.append({"station": station, "layer": layer, **r})
        summary_rows.append({"station": station, "layer": layer, **summary})

    df_full = pd.DataFrame(full_rows)
    df_summary = pd.DataFrame(summary_rows)

    full_path = OUT_DIR / "lagged_correlation.csv"
    summary_path = OUT_DIR / "lagged_correlation_summary.csv"
    df_full.to_csv(full_path, index=False, float_format="%.6f")
    df_summary.to_csv(summary_path, index=False, float_format="%.6f")

    print(f"Written: {full_path}  ({len(df_full)} rows, {skipped} skipped)")
    print(f"Written: {summary_path}  ({len(df_summary)} rows)")

    print(f"\nOptimal lag distribution:")
    for tau in sorted(df_summary["tau_opt_ccf"].dropna().unique()):
        n = (df_summary["tau_opt_ccf"] == tau).sum()
        print(f"  tau={int(tau):2d}: {n} layers")
    print(f"  NaN (too short): {df_summary['tau_opt_ccf'].isna().sum()} layers")
    print(f"\nMedian |r_yh| at optimal lag: {df_summary['r_yh_at_opt'].abs().median():.3f}")


if __name__ == "__main__":
    main()
