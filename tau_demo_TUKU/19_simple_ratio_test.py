#!/usr/bin/env python
"""19_simple_ratio_test.py — Detrended GPS-to-layer lag/ratio test (super_plan_2026-06-11, M7).

Idea: after removing each series' linear trend,
    detrended_b_k(t) ?= ratio_k * detrended_GPS(t - lag_k)
Per layer: cross-correlate over lags -120..+120 five-day epochs, pick the |corr|-max lag,
fit the through-origin ratio, export CSV + JSON + PNG.

Run: $env:PYTHONPATH=""; conda run -n fafalab2 python tau_demo_TUKU/19_simple_ratio_test.py
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parents[1]
MLCW_CSV = REPO / "data/mlcw/group_byLayer_reconstr/TUKU_reconst_grouped.csv"
GPS_CSV = REPO / "data/gps/modeled/TKJS_model.csv"
LAYERS = ["F1", "T1", "F2", "T2", "F3", "F4"]
MAX_LAG = 120  # five-day epochs = 600 days
plt.rcParams.update({"font.size": 14, "axes.grid": True, "figure.dpi": 100})

def detrend(t_days, y):
    m = np.isfinite(y)
    if m.sum() < 4:
        return None, None
    p = np.polyfit(t_days[m], y[m], 1)
    return y - np.polyval(p, t_days), p

def run(gps_column, res_dir, plot_dir):
    res_dir.mkdir(parents=True, exist_ok=True)
    plot_dir.mkdir(parents=True, exist_ok=True)
    mlcw = pd.read_csv(MLCW_CSV, parse_dates=["datetime"]).rename(columns={"datetime": "date"})
    gps = pd.read_csv(GPS_CSV, parse_dates=["date"])
    df = pd.merge_asof(mlcw.sort_values("date"), gps[["date", gps_column]].sort_values("date"),
                       on="date", tolerance=pd.Timedelta("2D"), direction="nearest")
    t_days = (df["date"] - df["date"].iloc[0]).dt.days.to_numpy(float)
    g_det, g_p = detrend(t_days, df[gps_column].to_numpy(float))
    summary, xcorr_curves = {}, {}
    for L in LAYERS:
        b_det, b_p = detrend(t_days, df[L].to_numpy(float))
        if b_det is None:
            print(f"{L}: insufficient data - result is undefined")
            continue
        lags = np.arange(-MAX_LAG, MAX_LAG + 1)
        corrs = np.full(lags.size, np.nan)
        for i, lag in enumerate(lags):
            g_s = pd.Series(g_det).shift(lag).to_numpy()  # lag>0: GPS leads compaction
            m = np.isfinite(b_det) & np.isfinite(g_s)
            if m.sum() >= 10:
                corrs[i] = np.corrcoef(b_det[m], g_s[m])[0, 1]
        if not np.isfinite(corrs).any():
            print(f"{L}: insufficient data - result is undefined")
            summary[L] = "insufficient data - result is undefined"
            continue
        i_best = int(np.nanargmax(np.abs(corrs)))
        lag_best, corr_best = int(lags[i_best]), float(corrs[i_best])
        g_best = pd.Series(g_det).shift(lag_best).to_numpy()
        m = np.isfinite(b_det) & np.isfinite(g_best)
        ratio = float(np.sum(g_best[m] * b_det[m]) / np.sum(g_best[m] ** 2))
        fit = ratio * g_best
        ss_res = float(np.sum((b_det[m] - fit[m]) ** 2))
        ss_tot = float(np.sum((b_det[m] - b_det[m].mean()) ** 2))
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
        summary[L] = {"lag_epochs": lag_best, "lag_days": lag_best * 5,
                      "corr_at_best_lag": corr_best, "ratio_mm_per_mm": ratio,
                      "r2_detrended": r2, "n_pairs": int(m.sum()),
                      "std_detrended_obs_mm": float(np.nanstd(b_det)),
                      "std_detrended_gps_mm": float(np.nanstd(g_det))}
        xcorr_curves[L] = {"lags": lags.tolist(),
                           "corr": [None if not np.isfinite(c) else round(float(c), 4) for c in corrs]}
        pd.DataFrame({"date": df["date"], "b_detrended_mm": b_det,
                      "gps_detrended_shifted_mm": g_best, "ratio_fit_mm": fit,
                      "residual_mm": b_det - fit}).to_csv(res_dir / f"TUKU_{L}_ratio_timeseries.csv", index=False)
        fig, ax = plt.subplots(2, 1, figsize=(12, 8))
        ax[0].plot(lags * 5, corrs, color="tab:blue")
        ax[0].axvline(lag_best * 5, color="tab:red", ls="--",
                      label=f"best lag {lag_best*5} d, r={corr_best:.3f}")
        ax[0].set_xlabel("GPS lead time (days)"); ax[0].set_ylabel("Pearson r"); ax[0].legend()
        ax[0].set_title(f"TUKU {L} - detrended cross-correlation ({gps_column})")
        ax[1].plot(df["date"], b_det, color="tab:blue", lw=0.8, label="detrended MLCW (mm)")
        ax[1].plot(df["date"], fit, color="tab:orange", lw=1.2,
                   label=f"ratio x shifted GPS (ratio={ratio:.3f})")
        ax[1].set_xlabel("Date"); ax[1].set_ylabel("Detrended compaction (mm)"); ax[1].legend()
        fig.tight_layout(); fig.savefig(plot_dir / f"TUKU_{L}_ratio_test.png", dpi=300); plt.close(fig)
    # summary outputs
    rows = {L: v for L, v in summary.items() if isinstance(v, dict)}
    pd.DataFrame(rows).T.to_csv(res_dir / "simple_ratio_summary.csv")
    (res_dir / "simple_ratio_summary.json").write_text(json.dumps({
        "metadata": {"date": "2026-06-11", "gps_source": str(GPS_CSV.name),
                     "gps_column": gps_column, "max_lag_epochs": MAX_LAG,
                     "mlcw_source": str(MLCW_CSV.name),
                     "mlcw_note": "MLCW series is the DENSE non-linear reconstruction (smooth fill); detrended correlations are an UPPER BOUND on what genuine sparse field visits would show (see mlcw_provenance_audit.json).",
                     "detrend": "linear OLS on cumulative",
                     "interpretation_rule": "|corr| < 0.5 means the GPS residual cannot supply that layer's dynamics"},
        "per_layer": summary, "xcorr_curves": xcorr_curves}, indent=2))
    fig, ax = plt.subplots(figsize=(10, 6))
    Ls = [L for L in LAYERS if isinstance(summary.get(L), dict)]
    ax.bar(Ls, [summary[L]["corr_at_best_lag"] for L in Ls], color="tab:blue")
    ax.axhline(0.5, color="tab:red", ls="--", label="information threshold 0.5")
    ax.axhline(-0.5, color="tab:red", ls="--")
    ax.set_ylabel("Pearson r at best lag"); ax.set_title(f"TUKU detrended GPS-to-layer correlation ({gps_column})")
    ax.legend(); fig.tight_layout(); fig.savefig(plot_dir / "summary_corr_per_layer.png", dpi=300); plt.close(fig)
    print(f"\n=== GPS column: {gps_column} ===")
    print(pd.DataFrame(rows).T.to_string())
    return summary

def main():
    base_res = REPO / "tau_demo_TUKU/results/simple_ratio_test"
    base_plot = REPO / "tau_demo_TUKU/plots/simple_ratio_test"
    run("modeled", base_res, base_plot)
    run("orig_nojump", base_res / "orig_nojump", base_plot / "orig_nojump")

if __name__ == "__main__":
    main()
