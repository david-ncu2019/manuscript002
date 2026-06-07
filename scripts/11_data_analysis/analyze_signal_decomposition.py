"""
Signal decomposition: trend, seasonal, residual components and their cross-correlations.

For each station-layer pair, decomposes MLCW, GWL, and InSAR into:
  - Linear trend
  - Annual harmonic (1-yr sine + cosine)
  - Residual
Then computes cross-correlations within each frequency band.

Usage:
    python scripts/11_data_analysis/analyze_signal_decomposition.py
    python scripts/11_data_analysis/analyze_signal_decomposition.py --station TUKU

Output: results/data_analysis/signal_decomposition.csv
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


def decompose_signal(t_days, y, period_days=365.25):
    """
    Decompose y into trend + annual harmonic + residual.
    Returns dict with components and their statistics.
    """
    n = len(y)
    if n < 10:
        return {"y_trend": np.full(n, np.nan), "y_seasonal": np.full(n, np.nan),
                "y_residual": np.full(n, np.nan), "y_trend_slope": np.nan,
                "y_seas_amp": np.nan, "y_seas_phase": np.nan,
                "y_resid_std": np.nan}

    t = t_days.astype(float)
    omega = 2 * np.pi / period_days
    A = np.column_stack([np.ones(n), t, np.sin(omega * t), np.cos(omega * t)])
    try:
        theta, _, _, _ = np.linalg.lstsq(A, y, rcond=None)
    except np.linalg.LinAlgError:
        theta = np.zeros(4)

    # trend: linear component
    y_trend = A[:, :2] @ theta[:2]
    slope_per_day = float(theta[1])
    slope_per_year = slope_per_day * 365.25

    # seasonal: harmonic component
    y_seasonal_raw = A[:, 2:] @ theta[2:]
    sin_amp, cos_amp = float(theta[2]), float(theta[3])
    amp = np.sqrt(sin_amp ** 2 + cos_amp ** 2)
    phase = np.arctan2(cos_amp, sin_amp)

    # residual
    y_residual = y - y_trend - y_seasonal_raw

    return {
        "y_trend": y_trend,
        "y_seasonal": y_seasonal_raw,
        "y_residual": y_residual,
        "y_trend_slope_pyr": slope_per_year,
        "y_seas_amp": amp,
        "y_seas_phase": phase,
        "y_resid_std": float(np.std(y_residual)),
    }


def analyze_pair(merged):
    t = (merged["datetime"] - merged["datetime"].min()).dt.days.values.astype(float)
    y = merged["mlcw_mm"].values
    h_raw = merged["head_m"].values
    x = merged["insar_mm"].values
    dh = h_raw - h_raw[0]

    dec_y = decompose_signal(t, y)
    dec_dh = decompose_signal(t, dh)
    dec_x = decompose_signal(t, x)

    # cross-correlations within bands
    def safe_r(a, b):
        mask = ~(np.isnan(a) | np.isnan(b))
        if mask.sum() < 3:
            return np.nan
        return float(np.corrcoef(a[mask], b[mask])[0, 1])

    return {
        # trend slopes
        "y_trend_mmpyr": dec_y["y_trend_slope_pyr"],
        "dh_trend_mpyr": dec_dh["y_trend_slope_pyr"],
        "x_trend_mmpyr": dec_x["y_trend_slope_pyr"],
        # seasonal amplitudes
        "y_seas_amp": dec_y["y_seas_amp"],
        "dh_seas_amp": dec_dh["y_seas_amp"],
        "x_seas_amp": dec_x["y_seas_amp"],
        # residual std
        "y_resid_std": dec_y["y_resid_std"],
        "dh_resid_std": dec_dh["y_resid_std"],
        "x_resid_std": dec_x["y_resid_std"],
        # trend-band correlations
        "r_yt_dht": safe_r(dec_y["y_trend"], dec_dh["y_trend"]),
        "r_yt_xt": safe_r(dec_y["y_trend"], dec_x["y_trend"]),
        "r_dht_xt": safe_r(dec_dh["y_trend"], dec_x["y_trend"]),
        # seasonal-band correlations
        "r_ys_dhs": safe_r(dec_y["y_seasonal"], dec_dh["y_seasonal"]),
        "r_ys_xs": safe_r(dec_y["y_seasonal"], dec_x["y_seasonal"]),
        "r_dhs_xs": safe_r(dec_dh["y_seasonal"], dec_x["y_seasonal"]),
        # residual-band correlations
        "r_yr_dhr": safe_r(dec_y["y_residual"], dec_dh["y_residual"]),
        "r_yr_xr": safe_r(dec_y["y_residual"], dec_x["y_residual"]),
        "r_dhr_xr": safe_r(dec_dh["y_residual"], dec_x["y_residual"]),
    }


def main():
    parser = argparse.ArgumentParser(description="Signal decomposition analysis")
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
    rows = []
    skipped = 0

    for entry in entries:
        station, layer = entry["station"], entry["layer"]
        try:
            merged, _ = load_and_align(entry, PROJECT_ROOT, insar_csv)
        except Exception:
            skipped += 1
            continue

        dec = analyze_pair(merged)
        rows.append({"station": station, "layer": layer, "n_epochs": len(merged), **dec})

    df = pd.DataFrame(rows)
    out_path = OUT_DIR / "signal_decomposition.csv"
    df.to_csv(out_path, index=False, float_format="%.6f")
    print(f"Written: {out_path}  ({len(df)} pairs, {skipped} skipped)")

    print(f"\nFrequency-band MLCW-GWL correlations (medians):")
    print(f"  Trend band:    r(yt, dht) = {df['r_yt_dht'].median():+.3f}")
    print(f"  Seasonal band: r(ys, dhs) = {df['r_ys_dhs'].median():+.3f}")
    print(f"  Residual band: r(yr, dhr) = {df['r_yr_dhr'].median():+.3f}")

    # which band dominates?
    bands = ["trend", "seasonal", "residual"]
    cols = ["r_yt_dht", "r_ys_dhs", "r_yr_dhr"]
    abs_medians = [df[c].abs().median() for c in cols]
    dominant = bands[np.argmax(abs_medians)]
    print(f"  Dominant band (highest median |r|): {dominant}")


if __name__ == "__main__":
    main()
