"""
Analyze pairwise correlations between MLCW compaction, GWL head, and InSAR.

Computes Pearson r and Spearman rho for:
  - raw signals
  - detrended residuals
  - 12-month lowpass (moving average)
  - highpass residuals (original - lowpass)

Usage:
    python scripts/11_data_analysis/analyze_correlations.py
    python scripts/11_data_analysis/analyze_correlations.py --station TUKU

Output: results/data_analysis/correlation_matrix.csv
"""

import argparse
import json
import sys
import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "10_ihmf"))
from ihmf_io import load_and_align


def _spearmanr(x, y):
    """Spearman rank correlation (numpy-only, avoids scipy dependency)."""
    def _rank(a):
        return np.argsort(np.argsort(a)).astype(float) + 1
    rx = _rank(x)
    ry = _rank(y)
    return float(np.corrcoef(rx, ry)[0, 1])

CONFIG_PATH = PROJECT_ROOT / "data/ihmf_config.json"
OUT_DIR = PROJECT_ROOT / "results/data_analysis"
OUT_DIR.mkdir(parents=True, exist_ok=True)

LOWPASS_WINDOW = 24  # ~12 months at 12-day cadence (24 epochs ≈ 288 days)


def _detrend(y):
    t = np.arange(len(y), dtype=float)
    A = np.column_stack([np.ones_like(t), t])
    theta, _, _, _ = np.linalg.lstsq(A, y, rcond=None)
    return y - (A @ theta)


def _lowpass(y, window=LOWPASS_WINDOW):
    s = pd.Series(y)
    return s.rolling(window=window, center=True, min_periods=window // 2).mean().values


def compute_correlations(y, dh, x):
    results = {}

    # -- raw signals --
    results["r_yh"] = float(np.corrcoef(y, dh)[0, 1]) if len(y) > 2 else np.nan
    results["r_yx"] = float(np.corrcoef(y, x)[0, 1]) if len(y) > 2 else np.nan
    results["r_hx"] = float(np.corrcoef(dh, x)[0, 1]) if len(y) > 2 else np.nan

    if len(y) > 2:
        results["rho_yh"] = float(_spearmanr(y, dh))
        results["rho_yx"] = float(_spearmanr(y, x))
        results["rho_hx"] = float(_spearmanr(dh, x))
    else:
        results["rho_yh"] = results["rho_yx"] = results["rho_hx"] = np.nan

    # -- detrended --
    yd = _detrend(y)
    dhd = _detrend(dh)
    xd = _detrend(x)
    results["r_yh_detr"] = float(np.corrcoef(yd, dhd)[0, 1]) if len(y) > 2 else np.nan
    results["r_yx_detr"] = float(np.corrcoef(yd, xd)[0, 1]) if len(y) > 2 else np.nan
    results["r_hx_detr"] = float(np.corrcoef(dhd, xd)[0, 1]) if len(y) > 2 else np.nan
    if len(y) > 2:
        results["rho_yh_detr"] = float(_spearmanr(yd, dhd))
        results["rho_yx_detr"] = float(_spearmanr(yd, xd))
        results["rho_hx_detr"] = float(_spearmanr(dhd, xd))
    else:
        results["rho_yh_detr"] = results["rho_yx_detr"] = results["rho_hx_detr"] = np.nan

    # -- lowpass --
    y_lp = _lowpass(y)
    dh_lp = _lowpass(dh)
    x_lp = _lowpass(x)
    mask = ~(np.isnan(y_lp) | np.isnan(dh_lp) | np.isnan(x_lp))
    if mask.sum() > 2:
        results["r_yh_lp"] = float(np.corrcoef(y_lp[mask], dh_lp[mask])[0, 1])
        results["r_yx_lp"] = float(np.corrcoef(y_lp[mask], x_lp[mask])[0, 1])
        results["r_hx_lp"] = float(np.corrcoef(dh_lp[mask], x_lp[mask])[0, 1])
    else:
        results["r_yh_lp"] = results["r_yx_lp"] = results["r_hx_lp"] = np.nan

    # -- highpass --
    y_hp = y - y_lp
    dh_hp = dh - dh_lp
    x_hp = x - x_lp
    if mask.sum() > 2:
        results["r_yh_hp"] = float(np.corrcoef(y_hp[mask], dh_hp[mask])[0, 1])
        results["r_yx_hp"] = float(np.corrcoef(y_hp[mask], x_hp[mask])[0, 1])
        results["r_hx_hp"] = float(np.corrcoef(dh_hp[mask], x_hp[mask])[0, 1])
    else:
        results["r_yh_hp"] = results["r_yx_hp"] = results["r_hx_hp"] = np.nan

    return results


def main():
    parser = argparse.ArgumentParser(description="Pairwise correlation analysis")
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
            y = merged["mlcw_mm"].values
            h_raw = merged["head_m"].values
            x = merged["insar_mm"].values
            dh = h_raw - h_raw[0]
        except Exception:
            skipped += 1
            continue

        corrs = compute_correlations(y, dh, x)
        rows.append({
            "station": station,
            "layer": layer,
            "n_epochs": len(y),
            **corrs,
        })

    df = pd.DataFrame(rows)
    out_path = OUT_DIR / "correlation_matrix.csv"
    df.to_csv(out_path, index=False, float_format="%.6f")

    print(f"Written: {out_path}  ({len(df)} station-layer pairs, {skipped} skipped)")

    # Quick summary to stdout
    print(f"\nGlobal medians (raw):")
    print(f"  r(y,dh)  = {df['r_yh'].median():+.3f}  [IQR {df['r_yh'].quantile(0.25):+.3f} to {df['r_yh'].quantile(0.75):+.3f}]")
    print(f"  r(y,x)   = {df['r_yx'].median():+.3f}  [IQR {df['r_yx'].quantile(0.25):+.3f} to {df['r_yx'].quantile(0.75):+.3f}]")
    print(f"  r(dh,x)  = {df['r_hx'].median():+.3f}  [IQR {df['r_hx'].quantile(0.25):+.3f} to {df['r_hx'].quantile(0.75):+.3f}]")
    print(f"\nWeak coupling (|r_yh| < 0.2): { (df['r_yh'].abs() < 0.2).sum() } / {len(df)}")
    print(f"High collinearity dh-x (|r_hx| > 0.7): { (df['r_hx'].abs() > 0.7).sum() } / {len(df)}")


if __name__ == "__main__":
    main()
