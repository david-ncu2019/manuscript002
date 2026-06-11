#!/usr/bin/env python
"""run_m5_gps_deployment.py — GPS-only carrier deployment across all mapped MLCW stations.
super_plan_2026-06-11 M9. Inputs resolved EXCLUSIVELY through station_file_map.json.
NO InSAR. NO GWL in this first pass. Carrier-only: b_k = c_k + a_k * d_GPS, a_k >= 0.
Run: $env:PYTHONPATH=""; conda run -n fafalab2 python m5_deployment/run_m5_gps_deployment.py
"""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import lsq_linear

REPO = Path(__file__).resolve().parents[1]
MAP = json.loads((REPO / "m5_deployment/station_file_map.json").read_text(encoding="utf-8"))  # UTF-8 FIX
OUT = REPO / "m5_deployment/results"
SUMM = REPO / "m5_deployment/summary"
DENSE_FRACTION = 0.70
MIN_OVERLAP = 300
plt.rcParams.update({"font.size": 14, "axes.grid": True})

SMOKE_STATION = None  # set to "TUKU" for smoke-test; None = full run
# Override via CLI: python run_m5_gps_deployment.py --smoke TUKU
if "--smoke" in sys.argv:
    _idx = sys.argv.index("--smoke")
    SMOKE_STATION = sys.argv[_idx + 1]


def fit_carrier(d, b):
    m = np.isfinite(d) & np.isfinite(b)
    X = np.column_stack([np.ones(m.sum()), d[m]])
    res = lsq_linear(X, b[m], bounds=([-np.inf, 0.0], [np.inf, np.inf]))
    return res.x[0], res.x[1]   # c, a


def metrics(obs, pred, dates):
    m = np.isfinite(obs) & np.isfinite(pred)
    if m.sum() < 10:
        return {"status": "insufficient data - result is undefined", "n": int(m.sum())}
    e = obs[m] - pred[m]
    t = (dates[m] - dates[m].iloc[0]).dt.days.to_numpy(float)
    det = lambda y: y - np.polyval(np.polyfit(t, y, 1), t)
    do, dp = det(obs[m].to_numpy()), det(pred[m].to_numpy())
    inc_o, inc_p = np.diff(obs[m].to_numpy()), np.diff(pred[m].to_numpy())
    return {"n": int(m.sum()), "mae_mm": float(np.mean(np.abs(e))),
            "rmse_mm": float(np.sqrt(np.mean(e ** 2))), "bias_mm": float(np.mean(e)),
            "amplitude_ratio_increments": float(np.std(inc_p) / np.std(inc_o)) if np.std(inc_o) > 0 else None,
            "detrended_corr": float(np.corrcoef(do, dp)[0, 1]) if do.size > 3 else None,
            "detrended_std_obs_mm": float(np.std(do)), "detrended_std_pred_mm": float(np.std(dp))}


def run_station(name, st):
    mlcw = pd.read_csv(REPO / st["files"]["mlcw_reconst_csv"], parse_dates=["datetime"]
                       ).rename(columns={"datetime": "date"})
    gps = pd.read_csv(REPO / st["files"]["gps_modeled_csv"], parse_dates=["date"])
    df = pd.merge_asof(mlcw.sort_values("date"), gps[["date", "modeled"]].sort_values("date"),
                       on="date", tolerance=pd.Timedelta("2D"), direction="nearest")
    overlap = df["modeled"].notna()
    if overlap.sum() < MIN_OVERLAP:
        return {"excluded": True, "reason": f"GPS-MLCW overlap {int(overlap.sum())} < {MIN_OVERLAP}"}
    idx = np.flatnonzero(overlap.to_numpy())
    cut = idx[int(len(idx) * DENSE_FRACTION)]
    train = df.index <= cut
    d = df["modeled"].to_numpy(float)
    res = {"excluded": False, "n_overlap": int(overlap.sum()),
           "train_end": str(df.loc[cut, "date"].date()), "layers": {}}
    sdir = OUT / name
    sdir.mkdir(parents=True, exist_ok=True)
    layers = [L for L in st["layers"] if L in df.columns]   # ROBUSTNESS: only layers present as columns
    fig, axes = plt.subplots(len(layers), 1, figsize=(12, 2.6 * len(layers)),
                             sharex=True, squeeze=False)
    for ax, L in zip(axes.ravel(), layers):
        b = df[L].to_numpy(float)
        c, a = fit_carrier(d[train], b[train])
        pred = c + a * d
        hold = ~train & overlap.to_numpy()
        res["layers"][L] = {"a_k": float(a), "c_k": float(c),
                            "holdout": metrics(df[L][hold], pd.Series(pred)[hold], df["date"][hold]),
                            "calibration_diagnostic": metrics(df[L][train & overlap.to_numpy()],
                                                              pd.Series(pred)[train & overlap.to_numpy()],
                                                              df["date"][train & overlap.to_numpy()])}
        pd.DataFrame({"date": df["date"], "b_observed_mm": b, "b_predicted_mm": pred,
                      "residual_mm": b - pred, "is_holdout": hold}
                     ).to_csv(sdir / f"{name}_{L}_reconstruction.csv", index=False)
        ax.plot(df["date"], b, lw=0.8, color="tab:blue", label="observed")
        ax.plot(df["date"], pred, lw=1.2, color="tab:orange", label="GPS carrier")
        ax.axvline(df.loc[cut, "date"], color="tab:red", ls="--")
        ax.set_ylabel(f"{L} (mm)"); ax.legend(loc="lower left", fontsize=10)
    axes.ravel()[-1].set_xlabel("Date")
    fig.suptitle(f"{name} - GPS-only carrier (train left of red line)")
    fig.tight_layout(); fig.savefig(sdir / f"{name}_6layer.png", dpi=300); plt.close(fig)
    (sdir / f"{name}_metrics.json").write_text(json.dumps(res, indent=2))
    return res


def main():
    SUMM.mkdir(parents=True, exist_ok=True)
    rows, exclusions = [], {}
    stations_to_run = MAP["stations"]
    if SMOKE_STATION:
        stations_to_run = {SMOKE_STATION: MAP["stations"][SMOKE_STATION]}
    for name, st in stations_to_run.items():
        if not st.get("has_gps_modeled") or not st["files"].get("gps_modeled_csv"):
            exclusions[name] = "no paired GPS modeled series"
            continue
        try:
            r = run_station(name, st)
        except FileNotFoundError as ex:
            exclusions[name] = f"file not found - cannot proceed: {ex}"
            continue
        if r.get("excluded"):
            exclusions[name] = r["reason"]
            continue
        for L, v in r["layers"].items():
            h = v["holdout"]
            rows.append({"station": name, "layer": L, "a_k": v["a_k"],
                         "n_holdout": h.get("n"), "rmse_mm": h.get("rmse_mm"),
                         "mae_mm": h.get("mae_mm"),
                         "amplitude_ratio": h.get("amplitude_ratio_increments"),
                         "detrended_corr": h.get("detrended_corr")})
    summary = pd.DataFrame(rows)
    summary.to_csv(SUMM / "m5_gps_deployment_summary.csv", index=False)
    (SUMM / "m5_gps_deployment_summary.json").write_text(json.dumps(
        {"metadata": {"date": "2026-06-11", "recipe": "GPS-only carrier, chronological 70/30",
                      "insar_used": False, "gwl_used": False},
         "n_stations_run": int(summary["station"].nunique()) if len(summary) else 0,
         "exclusions": exclusions,
         "portfolio_median_rmse_mm": float(summary["rmse_mm"].median()) if len(summary) else None},
        indent=2))
    (SUMM / "exclusion_report.json").write_text(json.dumps(exclusions, indent=2))
    if len(summary):
        fig, ax = plt.subplots(figsize=(14, 6))
        piv = summary.pivot_table(index="station", columns="layer", values="rmse_mm")
        piv.plot(kind="bar", ax=ax, colormap="tab10")
        ax.set_ylabel("Holdout RMSE (mm)"); ax.set_title("M9 GPS-only carrier - holdout RMSE by station/layer")
        fig.tight_layout(); fig.savefig(SUMM / "portfolio_rmse.png", dpi=300)
        plt.close(fig)
    print(summary.to_string() if len(summary) else "no stations ran")
    print("exclusions:", json.dumps(exclusions, indent=2))


if __name__ == "__main__":
    main()
