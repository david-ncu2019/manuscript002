"""
Compute MAE and RMSE between observed MLCW and v2 model predictions for TUKU.
Saves results/ihmf/v2/TUKU_v2_metrics.csv.
Also diagnoses the vertical shift (intercept handling).
"""
import json
import sys
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ihmf_io import load_and_align
from ihmf_detrend import detrend_signal, load_fbar_layer

CONFIG_PATH = ROOT / "data" / "ihmf_config.json"
OUT_DIR     = ROOT / "results" / "ihmf" / "v2"
INSAR_CSV   = ROOT / "data" / "insar" / "InSAR_measures_at_MLCW.csv"

cfg = json.load(open(CONFIG_PATH))
entries = {(e["station"], e["layer"]): e for e in cfg["entries"]}

rows = []

for layer in ["F1", "T1", "F2", "T2", "F3", "F4"]:
    json_path = OUT_DIR / f"TUKU_{layer}_v2_ihmf_results.json"
    if not json_path.exists():
        print(f"  missing JSON: {layer}")
        continue

    result = json.load(open(json_path))
    entry  = entries[("TUKU", layer)]

    # Load raw signals
    merged, meta = load_and_align(entry, ROOT, INSAR_CSV)
    t_days = (merged["datetime"] - merged["datetime"].iloc[0]).dt.days.values.astype(float)
    y_raw  = merged["mlcw_mm"].values
    h_raw  = merged["head_m"].values
    dh_raw = h_raw - h_raw[0]
    x_raw  = merged["insar_mm"].values
    n      = len(y_raw)

    # Detrend full record (same as fit_ihm_f_v2.py)
    y_d,  _,      _       = detrend_signal(t_days, y_raw)
    dh_d, dh_coef, _      = detrend_signal(t_days, dh_raw)
    x_d,  x_coef,  x_trend = detrend_signal(t_days, x_raw)

    tau      = result["tau_opt"]
    gamma_k  = result["gamma_k_mm_per_m"]
    beta_k   = result["beta_k_mm_per_mm"]
    intercept = result["intercept_mm"]
    f_bar_k  = result["f_bar_k"]

    # Dynamic component (detrended band)
    m = n - tau
    dh_d_lag = dh_d[tau:]
    x_d_lag  = x_d[:m]
    y_dynamic = intercept + gamma_k * dh_d_lag + beta_k * x_d_lag

    # Trend component: incremental InSAR from epoch 0, anchored to y_raw[0]
    x_inc        = x_raw[:m] - x_raw[0]
    y_trend_pred = y_raw[0] + f_bar_k * x_inc

    # Full prediction
    y_pred = y_trend_pred + y_dynamic

    # Observed (aligned to same window)
    y_obs = y_raw[:m]

    # Metrics — full record
    mae_full  = float(np.mean(np.abs(y_obs - y_pred)))
    rmse_full = float(np.sqrt(np.mean((y_obs - y_pred) ** 2)))
    bias_full = float(np.mean(y_pred - y_obs))   # + = prediction too high

    # Metrics — validation period (2022+) only
    dates = merged["datetime"].values[:m]
    yr    = pd.to_datetime(dates).year
    val_mask = yr >= 2022
    if val_mask.sum() > 0:
        mae_val  = float(np.mean(np.abs(y_obs[val_mask] - y_pred[val_mask])))
        rmse_val = float(np.sqrt(np.mean((y_obs[val_mask] - y_pred[val_mask]) ** 2)))
        bias_val = float(np.mean(y_pred[val_mask] - y_obs[val_mask]))
        n_val    = int(val_mask.sum())
    else:
        mae_val = rmse_val = bias_val = None
        n_val = 0

    print(f"TUKU {layer}:")
    print(f"  intercept = {intercept:+.3f} mm  f_bar_k = {f_bar_k:.4f}")
    print(f"  gamma_k   = {gamma_k:.4e} mm/m   beta_k = {beta_k:.4e}")
    print(f"  Full record  — MAE={mae_full:.3f}  RMSE={rmse_full:.3f}  bias={bias_full:+.3f} mm")
    if n_val > 0:
        print(f"  Val (2022+)  — MAE={mae_val:.3f}  RMSE={rmse_val:.3f}  bias={bias_val:+.3f} mm  n={n_val}")
    print()

    rows.append({
        "station":        "TUKU",
        "layer":          layer,
        "n_total":        m,
        "n_val":          n_val,
        "tau_opt":        tau,
        "intercept_mm":   round(intercept, 4),
        "f_bar_k":        round(f_bar_k, 4),
        "gamma_k":        round(gamma_k, 6),
        "beta_k":         round(beta_k, 6),
        "r2_insample":    round(result["r2"], 4),
        "rmse_full":      round(rmse_full, 4),
        "mae_full":       round(mae_full, 4),
        "bias_full":      round(bias_full, 4),
        "rmse_val":       round(rmse_val, 4) if n_val > 0 else None,
        "mae_val":        round(mae_val, 4)  if n_val > 0 else None,
        "bias_val":       round(bias_val, 4) if n_val > 0 else None,
    })

out_csv = OUT_DIR / "TUKU_v2_metrics.csv"
pd.DataFrame(rows).to_csv(out_csv, index=False)
print(f"Saved: {out_csv}")
