"""
Collinearity diagnostics for the 4-column IHM-F design matrix.

Computes VIF, condition number, partial correlations, and eigenvalue spectrum.

Usage:
    python scripts/11_data_analysis/analyze_collinearity.py
    python scripts/11_data_analysis/analyze_collinearity.py --station TUKU

Output: results/data_analysis/collinearity_diagnostics.csv
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


def _vif(X):
    """Variance Inflation Factor for each column of X (excluding intercept)."""
    X1 = X[:, 1:]  # skip intercept column
    k = X1.shape[1]
    vif = np.full(k, np.nan)
    for i in range(k):
        y_i = X1[:, i]
        X_i = np.delete(X1, i, axis=1)
        if X_i.shape[1] == 0:
            continue
        try:
            theta, _, _, _ = np.linalg.lstsq(X_i, y_i, rcond=None)
            y_hat = X_i @ theta
            ss_res = np.sum((y_i - y_hat) ** 2)
            ss_tot = np.sum((y_i - y_i.mean()) ** 2)
            r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
            vif[i] = 1.0 / (1.0 - r2) if r2 < 1.0 else np.inf
        except np.linalg.LinAlgError:
            vif[i] = np.inf
    return vif


def _partial_r(y, X):
    """Partial correlation of y with each column of X, controlling for others."""
    n_cols = X.shape[1]
    partials = np.full(n_cols, np.nan)
    for i in range(n_cols):
        x_i = X[:, i]
        X_others = np.delete(X, i, axis=1)
        # residualize x_i on other columns
        theta_x, _, _, _ = np.linalg.lstsq(X_others, x_i, rcond=None)
        x_resid = x_i - X_others @ theta_x
        # residualize y on other columns
        theta_y, _, _, _ = np.linalg.lstsq(X_others, y, rcond=None)
        y_resid = y - X_others @ theta_y
        denom_x = np.std(x_resid)
        denom_y = np.std(y_resid)
        if denom_x > 0 and denom_y > 0:
            partials[i] = float(np.corrcoef(x_resid, y_resid)[0, 1])
    return partials


def analyze_pair(merged, hc_percentile=10):
    y = merged["mlcw_mm"].values
    h_raw = merged["head_m"].values
    x = merged["insar_mm"].values
    dh = h_raw - h_raw[0]

    h_c = float(np.percentile(h_raw, hc_percentile))
    is_elastic = h_raw > h_c

    # 4-column design matrix [1, dh·I_e, dh·I_i, x]
    X = np.column_stack([
        np.ones(len(y)),
        dh * is_elastic,
        dh * (~is_elastic),
        x,
    ])

    col_names = ["intercept", "dh_e", "dh_i", "x"]

    # VIF (skip intercept)
    vif_vals = _vif(X)

    # Condition number via SVD
    try:
        _, s, _ = np.linalg.svd(X, full_matrices=False)
        cond_num = float(s[0] / s[-1]) if s[-1] > 0 else np.inf
    except np.linalg.LinAlgError:
        cond_num = np.inf

    # Partial correlations
    partials = _partial_r(y, X)

    # Eigenvalues of correlation matrix of [dh_e, dh_i, x]
    X_pred = X[:, 1:]  # the 3 predictors
    valid_cols = [j for j in range(X_pred.shape[1]) if np.std(X_pred[:, j]) > 0]
    eigvals = np.full(3, np.nan)
    if len(valid_cols) >= 2:
        corr_mat = np.corrcoef(X_pred[:, valid_cols].T)
        try:
            eigvals[:len(valid_cols)] = np.sort(np.linalg.eigvalsh(corr_mat))[::-1]
        except np.linalg.LinAlgError:
            pass

    return {
        "vif_dh_e": vif_vals[0],
        "vif_dh_i": vif_vals[1],
        "vif_x": vif_vals[2],
        "cond_num": cond_num,
        "partial_r_y_dh_e": partials[1],
        "partial_r_y_dh_i": partials[2],
        "partial_r_y_x": partials[3],
        "eigval_1": eigvals[2] if len(eigvals) > 2 else np.nan,
        "eigval_2": eigvals[1] if len(eigvals) > 1 else np.nan,
        "eigval_3": eigvals[0] if len(eigvals) > 0 else np.nan,
    }


def main():
    parser = argparse.ArgumentParser(description="Collinearity diagnostics")
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

        diag = analyze_pair(merged)
        rows.append({"station": station, "layer": layer, "n_epochs": len(merged), **diag})

    df = pd.DataFrame(rows)
    out_path = OUT_DIR / "collinearity_diagnostics.csv"
    df.to_csv(out_path, index=False, float_format="%.6f")
    print(f"Written: {out_path}  ({len(df)} pairs, {skipped} skipped)")

    print(f"\nCollinearity summary:")
    print(f"  Median VIF:  dh_e={df['vif_dh_e'].median():.1f}  "
          f"dh_i={df['vif_dh_i'].median():.1f}  x={df['vif_x'].median():.1f}")
    print(f"  High VIF (>10): dh_e={(df['vif_dh_e'] > 10).sum()}  "
          f"dh_i={(df['vif_dh_i'] > 10).sum()}  x={(df['vif_x'] > 10).sum()}")
    print(f"  Median condition number: {df['cond_num'].median():.0f}")
    print(f"  Ill-conditioned (cond > 1e4): {(df['cond_num'] > 1e4).sum()}")
    print(f"  Median partial r(y, dh_e | others): {df['partial_r_y_dh_e'].median():+.3f}")
    print(f"  Median partial r(y, dh_i | others): {df['partial_r_y_dh_i'].median():+.3f}")
    print(f"  Median partial r(y, x | others):    {df['partial_r_y_x'].median():+.3f}")


if __name__ == "__main__":
    main()
