"""
Aggregate statistics by layer type across all stations.

Reads correlation, collinearity, lag, regime, and proxy outputs to compute
layer-type medians and station-level health summaries.

Usage:
    python scripts/11_data_analysis/analyze_layer_patterns.py

Output: results/data_analysis/layer_aggregate_stats.csv
        results/data_analysis/station_layer_health.csv
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "data/ihmf_config.json"
DATA_DIR = PROJECT_ROOT / "results/data_analysis"
OUT_DIR = DATA_DIR
LAYER_ORDER = ["F1", "T1", "F2", "T2", "F3", "F4"]

# thresholds for "healthy"
WEAK_COUPLING_THRESH = 0.2
HIGH_VIF_THRESH = 10.0
DATA_POOR_INEL_THRESH = 0.10
INSAR_DOMINATED_BK = 0.001  # b_k effectively zero


def load_csv(name):
    path = DATA_DIR / name
    if path.exists():
        return pd.read_csv(path)
    return None


def load_ihmf_results():
    """Load b_k values from IHM-F JSON results."""
    ihmf_dir = PROJECT_ROOT / "results/ihmf"
    records = []
    if not ihmf_dir.exists():
        return None
    for jf in ihmf_dir.glob("*_ihmf_results.json"):
        if "run001" in str(jf):
            continue
        try:
            with open(jf) as f:
                d = json.load(f)
            records.append({
                "station": d["station"],
                "layer": d["layer"],
                "b_k_m": d.get("b_k_m"),
                "r2_ihmf": d.get("r2"),
                "rmse_mm": d.get("rmse_mm"),
                "model_path": d.get("model_path"),
            })
        except (json.JSONDecodeError, KeyError):
            pass
    if records:
        return pd.DataFrame(records)
    return None


def main():
    # load all analysis outputs
    df_corr = load_csv("correlation_matrix.csv")
    df_collin = load_csv("collinearity_diagnostics.csv")
    df_regime = load_csv("regime_characteristics.csv")
    df_ihmf = load_ihmf_results()

    if df_corr is None:
        raise SystemExit("correlation_matrix.csv not found — run analyze_correlations.py first")

    # Merge all sources
    df = df_corr.copy()
    if df_collin is not None:
        df = df.merge(df_collin[["station", "layer", "vif_dh_e", "vif_dh_i", "vif_x",
                                  "cond_num", "partial_r_y_dh_e", "partial_r_y_dh_i"]],
                       on=["station", "layer"], how="left")
    if df_regime is not None:
        df = df.merge(df_regime[["station", "layer", "f_inel", "n_inelastic", "n_inelastic_events",
                                  "mean_inelastic_duration"]],
                       on=["station", "layer"], how="left")
    if df_ihmf is not None:
        df = df.merge(df_ihmf[["station", "layer", "b_k_m", "r2_ihmf", "model_path"]],
                       on=["station", "layer"], how="left")

    # compute flags
    df["flag_weak_coupling"] = df["r_yh"].abs() < WEAK_COUPLING_THRESH
    df["flag_high_collinearity"] = (df["vif_dh_e"] > HIGH_VIF_THRESH) | (df["vif_x"] > HIGH_VIF_THRESH)
    df["flag_data_poor_inel"] = df["f_inel"] < DATA_POOR_INEL_THRESH
    df["flag_insar_dominated"] = df["b_k_m"].notna() & (df["b_k_m"] <= INSAR_DOMINATED_BK)
    df["flag_healthy"] = (
        (df["r_yh"].abs() >= 0.3) &
        (df["f_inel"] >= 0.05) &
        (~df["flag_high_collinearity"].fillna(False))
    )

    # ── Layer-aggregate stats ──
    layer_stats = []
    for layer in LAYER_ORDER:
        sub = df[df["layer"] == layer]
        if len(sub) == 0:
            continue
        stats = {"layer": layer, "n_stations": len(sub)}
        for col in ["r_yh", "r_yx", "r_hx", "r_yh_detr", "r_hx_detr", "f_inel",
                     "vif_dh_e", "vif_x", "cond_num", "partial_r_y_dh_e", "partial_r_y_dh_i"]:
            if col in sub.columns:
                s = sub[col].dropna()
                stats[f"median_{col}"] = round(s.median(), 4) if len(s) > 0 else np.nan
                stats[f"iqr_{col}"] = round(s.quantile(0.75) - s.quantile(0.25), 4) if len(s) > 2 else np.nan

        for flag, name in [("flag_weak_coupling", "frac_weak_coupling"),
                           ("flag_high_collinearity", "frac_high_collinearity"),
                           ("flag_data_poor_inel", "frac_data_poor_inel"),
                           ("flag_insar_dominated", "frac_insar_dominated")]:
            if flag in sub.columns:
                stats[name] = round(sub[flag].sum() / len(sub), 3)
        layer_stats.append(stats)

    df_layers = pd.DataFrame(layer_stats)
    layer_path = OUT_DIR / "layer_aggregate_stats.csv"
    df_layers.to_csv(layer_path, index=False, float_format="%.4f")
    print(f"Written: {layer_path}")

    # ── Station health summary ──
    station_rows = []
    for station, sub in df.groupby("station"):
        n_layers = len(sub)
        n_healthy = sub["flag_healthy"].sum() if "flag_healthy" in sub.columns else 0
        n_insar_dom = sub["flag_insar_dominated"].sum() if "flag_insar_dominated" in sub.columns else 0
        n_weak = sub["flag_weak_coupling"].sum() if "flag_weak_coupling" in sub.columns else 0
        station_rows.append({
            "station": station,
            "n_layers": n_layers,
            "n_healthy": int(n_healthy),
            "n_insar_dominated": int(n_insar_dom),
            "n_weak_coupling": int(n_weak),
            "frac_healthy": round(n_healthy / n_layers, 3) if n_layers > 0 else 0,
            "median_r_yh": round(sub["r_yh"].abs().median(), 4),
            "median_r2_ihmf": round(sub["r2_ihmf"].median(), 4) if "r2_ihmf" in sub.columns else np.nan,
        })

    df_stations = pd.DataFrame(station_rows)
    station_path = OUT_DIR / "station_layer_health.csv"
    df_stations.to_csv(station_path, index=False, float_format="%.4f")
    print(f"Written: {station_path}")

    # ── Console summary ──
    print(f"\nLayer-aggregate: median |r_yh| by layer type")
    for _, row in df_layers.iterrows():
        print(f"  {row['layer']}: n={int(row['n_stations']):3d}  "
              f"median|r_yh|={abs(row['median_r_yh']):.3f}  "
              f"detr|r_yh|={abs(row.get('median_r_yh_detr', np.nan)):.3f}  "
              f"f_inel={row.get('median_f_inel', np.nan):.3f}  "
              f"weak={row.get('frac_weak_coupling', 0):.2f}  "
              f"high_VIF={row.get('frac_high_collinearity', 0):.2f}  "
              f"inSAR_dom={row.get('frac_insar_dominated', 0):.2f}")

    print(f"\nStation health: {df_stations['n_healthy'].sum()} healthy / {df_stations['n_layers'].sum()} total")
    print(f"  0 healthy layers: {(df_stations['n_healthy'] == 0).sum()} stations")
    print(f"  All healthy: {(df_stations['n_healthy'] == df_stations['n_layers']).sum()} stations")


if __name__ == "__main__":
    main()
