"""
Synthesize all data analysis outputs into a single actionable JSON for model redesign.

Reads all 7 prior analysis CSVs and produces a consolidated machine-readable summary
with global statistics, layer-type breakdowns, worst/best layers, collinearity severity,
proxy impact, frequency-band findings, and auto-generated recommendations.

Usage:
    python scripts/11_data_analysis/summarize_for_redesign.py

Output: results/data_analysis/redesign_input.json
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "data/ihmf_config.json"
DATA_DIR = PROJECT_ROOT / "results/data_analysis"
OUT_PATH = DATA_DIR / "redesign_input.json"


def load(name):
    path = DATA_DIR / name
    if path.exists():
        return pd.read_csv(path)
    print(f"  WARNING: {name} not found")
    return None


def safe_median(s):
    return round(float(s.median()), 4) if len(s.dropna()) > 0 else None


def safe_count(s, condition_fn):
    return int(sum(1 for v in s.dropna() if condition_fn(v)))


def main():
    print("Loading analysis outputs...")
    df_corr = load("correlation_matrix.csv")
    df_lag = load("lagged_correlation_summary.csv")
    df_collin = load("collinearity_diagnostics.csv")
    df_regime = load("regime_characteristics.csv")
    df_proxy = load("gwl_proxy_quality.csv")
    df_signal = load("signal_decomposition.csv")

    if df_corr is None:
        raise SystemExit("correlation_matrix.csv required — run analyze_correlations.py first")

    # Merge all sources
    df = df_corr.copy()
    for other, cols in [
        (df_lag, ["tau_opt_ccf", "r_yh_at_opt", "ccf_peak_sharpness"]),
        (df_collin, ["vif_dh_e", "vif_dh_i", "vif_x", "cond_num",
                      "partial_r_y_dh_e", "partial_r_y_dh_i", "partial_r_y_x",
                      "eigval_1", "eigval_2", "eigval_3"]),
        (df_regime, ["f_inel", "n_inelastic", "n_inelastic_events",
                      "mean_inelastic_duration", "h_c_m", "h_min", "h_max"]),
        (df_signal, ["r_yt_dht", "r_ys_dhs", "r_yr_dhr", "r_yt_xt", "r_ys_xs", "r_yr_xr"]),
    ]:
        if other is not None:
            other_cols = [c for c in cols if c in other.columns]
            if other_cols:
                df = df.merge(other[["station", "layer"] + other_cols],
                              on=["station", "layer"], how="left")

    # Load IHM-F results for model comparison
    ihmf_records = []
    ihmf_dir = PROJECT_ROOT / "results/ihmf"
    if ihmf_dir.exists():
        for jf in ihmf_dir.glob("*_ihmf_results.json"):
            if "run001" in str(jf):
                continue
            try:
                with open(jf) as f:
                    d = json.load(f)
                ihmf_records.append({
                    "station": d["station"], "layer": d["layer"],
                    "r2_ihmf": d.get("r2"), "rmse_mm": d.get("rmse_mm"),
                    "b_k_m": d.get("b_k_m"), "model_path": d.get("model_path"),
                })
            except (json.JSONDecodeError, KeyError):
                pass
    if ihmf_records:
        df_ihmf = pd.DataFrame(ihmf_records)
        df = df.merge(df_ihmf, on=["station", "layer"], how="left")
    else:
        df["r2_ihmf"] = np.nan
        df["b_k_m"] = np.nan
        df["model_path"] = None

    n_total = len(df)
    n_stations = df["station"].nunique()

    # ── Global summary ──
    weak_coupling = (df["r_yh"].abs() < 0.2).sum()
    high_collin_dhx = (df["r_hx"].abs() > 0.7).sum()
    data_poor_inel = (df["f_inel"] < 0.10).sum() if "f_inel" in df.columns else 0
    insar_dominated = (df["b_k_m"].notna() & (df["b_k_m"] <= 0.001)).sum() if "b_k_m" in df.columns else 0

    # Healthy: decent GWL coupling, enough inelastic data, not purely InSAR-driven
    healthy_mask = (
        (df["r_yh"].abs() >= 0.3) &
        (df.get("f_inel", pd.Series([0.5] * n_total)).fillna(0) >= 0.05) &
        (~(df.get("r_hx", pd.Series([0] * n_total)).abs() > 0.85))
    )
    n_healthy = healthy_mask.sum()

    global_summary = {
        "n_stations": int(n_stations),
        "n_layers_total": int(n_total),
        "n_healthy": int(n_healthy),
        "n_insar_dominated": int(insar_dominated),
        "n_weak_gwl_coupling": int(weak_coupling),
        "n_high_gwl_insar_collinearity": int(high_collin_dhx),
        "n_data_poor_inelastic": int(data_poor_inel),
        "median_r_yh": safe_median(df["r_yh"]),
        "median_r_yx": safe_median(df["r_yx"]),
        "median_r_hx": safe_median(df["r_hx"]),
        "median_r_yh_detrended": safe_median(df["r_yh_detr"]),
        "median_r2_ihmf": safe_median(df["r2_ihmf"]) if "r2_ihmf" in df.columns else None,
    }

    # ── Layer-type breakdown ──
    layer_order = ["F1", "T1", "F2", "T2", "F3", "F4"]
    by_layer = {}
    for layer in layer_order:
        sub = df[df["layer"] == layer]
        if len(sub) == 0:
            continue
        d = {"n": len(sub)}
        for col in ["r_yh", "r_yx", "r_hx", "r_yh_detr", "r_hx_detr", "f_inel",
                     "r_yt_dht", "r_ys_dhs", "r_yr_dhr",
                     "vif_dh_e", "vif_x", "cond_num",
                     "partial_r_y_dh_e", "partial_r_y_dh_i", "partial_r_y_x"]:
            if col in sub.columns:
                s = sub[col].dropna()
                d[f"median_{col}"] = round(float(s.median()), 4) if len(s) > 0 else None
                q25 = s.quantile(0.25)
                q75 = s.quantile(0.75)
                d[f"iqr_{col}"] = round(float(q75 - q25), 4) if len(s) > 2 else None
        if "r2_ihmf" in sub.columns:
            s = sub["r2_ihmf"].dropna()
            d["median_r2_ihmf"] = round(float(s.median()), 4) if len(s) > 0 else None
        by_layer[layer] = d

    # ── Worst & best layers ──
    # worst: lowest |r_yh|
    df["_abs_r_yh"] = df["r_yh"].abs()
    worst = df.nsmallest(20, "_abs_r_yh")[["station", "layer", "r_yh", "r_yx", "r_hx",
                                              "r_yh_detr", "f_inel"]].to_dict("records")
    df.drop(columns=["_abs_r_yh"], inplace=True)
    for r in worst:
        for k, v in r.items():
            if isinstance(v, (np.floating, float)) and np.isnan(v):
                r[k] = None
            elif isinstance(v, np.floating):
                r[k] = round(float(v), 4)

    # best: highest |r_yh| AND f_inel > 0.10
    if "f_inel" in df.columns:
        best_pool = df[df["f_inel"] > 0.10]
    else:
        best_pool = df
    best_pool["_abs_r_yh"] = best_pool["r_yh"].abs()
    best = best_pool.nlargest(20, "_abs_r_yh")[["station", "layer", "r_yh", "r_yx", "r_hx",
                                                  "r_yh_detr", "f_inel", "r2_ihmf"]].to_dict("records")
    best_pool.drop(columns=["_abs_r_yh"], inplace=True, errors="ignore")
    for r in best:
        for k, v in r.items():
            if isinstance(v, (np.floating, float)) and np.isnan(v):
                r[k] = None
            elif isinstance(v, np.floating):
                r[k] = round(float(v), 4)

    # ── Collinearity severity ──
    if df_collin is not None:
        high_vif = ((df_collin["vif_dh_e"] > 10) | (df_collin["vif_dh_i"] > 10) | (df_collin["vif_x"] > 10)).sum()
        ill_cond = (df_collin["cond_num"] > 1e4).sum()
        collin_severity = {
            "n_high_vif": int(high_vif),
            "n_ill_conditioned": int(ill_cond),
            "median_cond_num": round(float(df_collin["cond_num"].median()), 1),
            "median_vif_dh_e": round(float(df_collin["vif_dh_e"].median()), 2),
            "median_vif_x": round(float(df_collin["vif_x"].median()), 2),
        }
    else:
        collin_severity = None

    # ── Proxy impact ──
    if df_proxy is not None and "dist_km" in df_proxy.columns and "r2_ihmf" in df_proxy.columns:
        has_dist = df_proxy[df_proxy["dist_km"].notna() & df_proxy["r2_ihmf"].notna()]
        if len(has_dist) > 4:
            proxy_impact = {
                "n_with_dist": len(has_dist),
                "r_r2_vs_dist": round(float(has_dist["r2_ihmf"].corr(has_dist["dist_km"])), 4),
            }
        else:
            proxy_impact = {"note": "insufficient data for proxy comparison"}
    else:
        proxy_impact = {"note": "proxy quality data not available"}

    # ── Frequency-band findings ──
    if df_signal is not None:
        band_cols = {"trend": "r_yt_dht", "seasonal": "r_ys_dhs", "residual": "r_yr_dhr"}
        band_medians = {}
        for band, col in band_cols.items():
            if col in df_signal.columns:
                s = df_signal[col].dropna()
                band_medians[f"{band}_band_median_abs_r_yh"] = round(float(s.abs().median()), 4) if len(s) > 0 else None
        abs_meds = {k: v for k, v in band_medians.items() if v is not None}
        dominant = max(abs_meds, key=abs_meds.get) if abs_meds else "unknown"
        frequency_band_findings = {
            **band_medians,
            "dominant_band": dominant.replace("_band_median_abs_r_yh", ""),
        }
    else:
        frequency_band_findings = None

    # ── Auto-generated recommendations ──
    recommendations = []
    if weak_coupling / n_total > 0.4:
        recommendations.append(
            f"{weak_coupling}/{n_total} layers have |r(y,dh)| < 0.2. "
            "The GWL signal is fundamentally weak for a large fraction of layers. "
            "Consider: (1) frequency-dependent coupling (seasonal vs trend), "
            "(2) regional rather than local GWL wells, or (3) a pure InSAR proxy for these layers.")
    if high_collin_dhx / n_total > 0.3:
        recommendations.append(
            f"{high_collin_dhx}/{n_total} layers have |r(dh,x)| > 0.7 — GWL and InSAR are highly collinear. "
            "For these layers, S_ke and beta cannot be separately identified. "
            "Consider: dropping the dh predictor and using a b_k model with InSAR alone, "
            "or using only the inelastic channel (which may be less collinear).")
    if n_healthy < n_total * 0.5:
        recommendations.append(
            f"Only {n_healthy}/{n_total} layers meet the 'healthy' threshold. "
            "A universal IHM-F fit will fail at the majority of layers. "
            "Consider: a two-tier model — (Tier 1) GWL-driven IHM for layers with strong coupling, "
            "(Tier 2) InSAR-driven scalar baseline for weak-coupling layers.")
    if df_signal is not None and "r_yr_dhr" in df_signal.columns:
        resid_med = df_signal["r_yr_dhr"].abs().median()
        trend_med = df_signal["r_yt_dht"].abs().median() if "r_yt_dht" in df_signal.columns else 1.0
        if resid_med < 0.15 and trend_med > 0.8:
            recommendations.append(
                f"GWL-MLCW coupling is confined to trend+seasonal bands (median |r_resid| = {resid_med:.3f}). "
                "Raw-signal OLS regresses on shared trends rather than physical coupling. "
                "Consider: detrended fitting for dynamics + separate trend attribution, "
                "or frequency-band-specific coefficients.")

    # ── Assemble output ──
    output = {
        "generated": pd.Timestamp.now().isoformat(),
        "data_sources": {
            "correlation_matrix": "correlation_matrix.csv",
            "lagged_correlation": "lagged_correlation_summary.csv",
            "collinearity": "collinearity_diagnostics.csv",
            "regime": "regime_characteristics.csv",
            "proxy_quality": "gwl_proxy_quality.csv",
            "signal_decomposition": "signal_decomposition.csv",
            "ihmf_results": "results/ihmf/*_ihmf_results.json",
        },
        "global_summary": global_summary,
        "by_layer_type": by_layer,
        "worst_20_layers": worst,
        "best_20_layers": best,
        "collinearity_severity": collin_severity,
        "proxy_impact": proxy_impact,
        "frequency_band_findings": frequency_band_findings,
        "recommendations": recommendations,
    }

    with open(OUT_PATH, "w") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"Written: {OUT_PATH}")
    print(f"\n{'='*60}")
    print(f"Global summary:")
    print(f"  {n_total} layers across {n_stations} stations")
    print(f"  Healthy (|r_yh|≥0.3, f_inel≥0.05, not collinear): {n_healthy}")
    print(f"  Weak GWL coupling: {weak_coupling}")
    print(f"  High GWL-InSAR collinearity: {high_collin_dhx}")
    print(f"  Data-poor inelastic: {data_poor_inel}")
    print(f"  InSAR-dominated (b_k≈0): {insar_dominated}")
    if global_summary["median_r_yh_detrended"] is not None:
        print(f"\n  Raw median |r(y,dh)|:    {global_summary['median_r_yh']}")
        print(f"  Detrended median |r(y,dh)|: {global_summary['median_r_yh_detrended']}")
    print(f"\n  Recommendations ({len(recommendations)}):")
    for i, rec in enumerate(recommendations, 1):
        print(f"    {i}. {rec}")


if __name__ == "__main__":
    main()
