"""
03_reconstruct_and_evaluate.py
==============================
Reconstructs predicted per-layer compaction and evaluates fit quality.

Output (plots/results/reconstruction/):
  - reconstruction_F1.png ... reconstruction_F4.png    (6 per-layer figures)
Output (results/):
  - reconstruction_metrics.csv / .json
  - reconstruction_timeseries.csv
  - evaluation_summary.json
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import pearsonr

from plot_style import DPI, A4_PORTRAIT, FONT, LW, style_ax, apply_style
apply_style()

# ── Paths ─────────────────────────────────────────────────────────────────────
DEMO_DIR    = Path(__file__).resolve().parent
RESULTS_DIR = DEMO_DIR / "results"
PLOTS_DIR   = DEMO_DIR / "plots" / "results"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)
RECON_DIR   = PLOTS_DIR / "reconstruction"
RECON_DIR.mkdir(parents=True, exist_ok=True)

COLORS = {ly: plt.cm.tab10(i) for i, ly in enumerate(["F1", "T1", "F2", "T2", "F3", "F4"])}
LAYERS_ORDERED = ["F1", "T1", "F2", "T2", "F3", "F4"]

T_START = pd.Timestamp("2015-01-01")
T_END   = pd.Timestamp("2026-01-01")

# ── Load data ─────────────────────────────────────────────────────────────────
npz      = np.load(RESULTS_DIR / "tuku_aligned_data.npz", allow_pickle=True)
tau_info = pd.read_csv(RESULTS_DIR / "tau_results.csv").set_index("layer")


def load_layer(layer):
    d = {}
    for key in npz.files:
        if key.startswith(f"{layer}__"):
            d[key[len(f"{layer}__"):]] = npz[key]
    d["dates"]     = pd.to_datetime(d["dates"])
    d["inc_dates"] = pd.to_datetime(d["inc_dates"])
    return d


# ── Reconstruction and evaluation ─────────────────────────────────────────────
all_metrics    = []
all_timeseries = []

for layer in LAYERS_ORDERED:
    if layer not in tau_info.index:
        continue

    d       = load_layer(layer)
    tau_opt = int(tau_info.loc[layer, "tau_opt"])
    inc_dH  = d["inc_dH"].astype(float)
    inc_db  = d["inc_db"].astype(float)
    inc_dates = d["inc_dates"]
    e_m     = d["e_m"].astype(bool)
    i_m     = d["i_m"].astype(bool)

    T = len(inc_dH)
    n = T - tau_opt
    if n < 4:
        print(f"  {layer}: only {n} epochs after lag — skipping")
        continue

    dH_lagged = inc_dH[tau_opt:]
    db_obs    = inc_db[:n]
    e_trim    = e_m[:n]
    i_trim    = i_m[:n]
    dates_n   = inc_dates[:n]

    # Fit S_ke (elastic)
    S_ke = 0.0
    dH_e, db_e = dH_lagged[e_trim], db_obs[e_trim]
    if e_trim.sum() >= 4 and np.dot(dH_e, dH_e) > 0:
        S_ke = max(0.0, np.dot(dH_e, db_e) / np.dot(dH_e, dH_e))

    # Fit S_kv (inelastic)
    S_kv = 0.0
    dH_i, db_i = dH_lagged[i_trim], db_obs[i_trim]
    if i_trim.sum() >= 4 and np.dot(dH_i, dH_i) > 0:
        S_kv = max(0.0, np.dot(dH_i, db_i) / np.dot(dH_i, dH_i))

    # Predict
    db_pred = (np.where(e_trim, S_ke * dH_lagged, 0.0) +
               np.where(i_trim, S_kv * dH_lagged, 0.0))

    # Metrics
    residuals = db_obs - db_pred
    mse   = float(np.mean(residuals ** 2))
    rmse  = float(np.sqrt(mse))
    mae   = float(np.mean(np.abs(residuals)))
    bias  = float(np.mean(db_pred - db_obs))
    ss_res = float(np.sum(residuals ** 2))
    ss_tot = float(np.sum((db_obs - db_obs.mean()) ** 2))
    r2 = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else np.nan
    r_pearson = float(pearsonr(db_obs, db_pred)[0]) if np.std(db_pred) > 0 and np.std(db_obs) > 0 else np.nan

    print(f"  {layer}: tau={tau_opt}  S_ke={S_ke:.5f}  S_kv={S_kv:.5f}  "
          f"RMSE={rmse:.5f} mm/ep  R2={r2:.4f}  r={r_pearson:.4f}  bias={bias:+.5f}")

    cum_obs  = np.cumsum(db_obs)
    cum_pred = np.cumsum(db_pred)

    all_metrics.append(dict(
        layer=layer, tau_opt=tau_opt, tau_opt_days=tau_opt * 5,
        S_ke=round(S_ke, 7), S_kv=round(S_kv, 7),
        n_elastic=int(e_trim.sum()), n_inelastic=int(i_trim.sum()), n_epochs=n,
        MSE=round(mse, 7), RMSE=round(rmse, 7), MAE=round(mae, 7),
        R2=round(r2, 6), pearson_r=round(r_pearson, 6) if not np.isnan(r_pearson) else None,
        bias=round(bias, 7),
    ))

    all_timeseries.append(pd.DataFrame(dict(
        date=dates_n, layer=layer,
        db_obs_mm_epoch=db_obs.round(6), db_pred_mm_epoch=db_pred.round(6),
        cum_obs_mm=cum_obs.round(4), cum_pred_mm=cum_pred.round(4),
    )))

# ── Save CSVs / JSON ──────────────────────────────────────────────────────────
metrics_df = pd.DataFrame(all_metrics)
metrics_df.to_csv(RESULTS_DIR / "reconstruction_metrics.csv", index=False)
print(f"\nSaved: {RESULTS_DIR / 'reconstruction_metrics.csv'}")

ts_all = pd.concat(all_timeseries, ignore_index=True)
ts_all.to_csv(RESULTS_DIR / "reconstruction_timeseries.csv", index=False)
print(f"Saved: {RESULTS_DIR / 'reconstruction_timeseries.csv'}  ({len(ts_all)} rows)")

json.dump([{k: v for k, v in m.items()} for m in all_metrics],
          open(RESULTS_DIR / "reconstruction_metrics.json", "w"), indent=2, default=str)
json_summary = {}
for layer, grp in ts_all.groupby("layer"):
    obs_v = grp["db_obs_mm_epoch"].values
    pred_v = grp["db_pred_mm_epoch"].values
    valid = np.isfinite(obs_v) & np.isfinite(pred_v)
    o, p = obs_v[valid], pred_v[valid]
    ss_r = float(np.sum((o - p)**2))
    ss_t = float(np.sum((o - o.mean())**2))
    json_summary[layer] = dict(
        n_epochs=len(o), mse_mm2_epoch2=float(np.mean((o-p)**2)),
        rmse_mm_epoch=float(np.sqrt(np.mean((o-p)**2))),
        mae_mm_epoch=float(np.mean(np.abs(o-p))),
        r2=float(1-ss_r/ss_t) if ss_t>0 else None,
        pearson_r=float(pearsonr(o, p)[0]) if np.std(p)>0 and np.std(o)>0 else None,
        bias_mm_epoch=float(np.mean(p-o)),
        cum_obs_min_mm=float(np.min(grp["cum_obs_mm"])),
        cum_obs_max_mm=float(np.max(grp["cum_obs_mm"])),
        cum_pred_min_mm=float(np.min(grp["cum_pred_mm"])),
        cum_pred_max_mm=float(np.max(grp["cum_pred_mm"])),
    )
json.dump(json_summary, open(RESULTS_DIR / "evaluation_summary.json", "w"), indent=2)
print(f"Saved: {RESULTS_DIR / 'evaluation_summary.json'}")

# ── Plot: one figure per layer ────────────────────────────────────────────────
for layer in LAYERS_ORDERED:
    if layer not in metrics_df["layer"].values:
        continue
    row_met = metrics_df[metrics_df["layer"] == layer].iloc[0]
    row_ts  = ts_all[ts_all["layer"] == layer].copy()
    row_ts["date"] = pd.to_datetime(row_ts["date"])
    row_ts = row_ts[(row_ts["date"] >= T_START) & (row_ts["date"] < T_END)]

    color    = COLORS[layer]
    tau_days = int(row_met["tau_opt_days"])
    R2_val   = float(row_met["R2"])
    RMSE_val = float(row_met["RMSE"])
    S_ke_val = float(row_met["S_ke"])
    S_kv_val = float(row_met["S_kv"])
    r_val    = row_met["pearson_r"]

    fig, (ax_inc, ax_cum) = plt.subplots(2, 1, figsize=(A4_PORTRAIT[0], 7.5), sharex=True)
    fig.suptitle(
        f"TUKU  |  Layer {layer}  |  Observed vs Predicted compaction\n"
        f"tau = {tau_days} days  |  S_ke = {S_ke_val:.4f}  S_kv = {S_kv_val:.4f}  |  "
        f"R² = {R2_val:.3f}  RMSE = {RMSE_val:.4f} mm/ep  r = {r_val:.3f}",
        fontsize=FONT["suptitle"], fontweight="bold", y=0.98,
    )

    # Panel 1: Incremental
    ax_inc.plot(row_ts["date"], row_ts["db_obs_mm_epoch"], color="grey",
                linewidth=LW["data"], alpha=0.7, label="Observed")
    ax_inc.plot(row_ts["date"], row_ts["db_pred_mm_epoch"], color=color,
                linewidth=LW["data"], alpha=0.9, label="Predicted")
    ax_inc.axhline(0, color="black", linewidth=LW["grid"], linestyle="-")
    ax_inc.set_ylabel("db (mm/epoch)", fontsize=FONT["axis_label"])
    ax_inc.legend(fontsize=FONT["legend"], loc="upper right")
    ax_inc.set_title("Incremental compaction per epoch", fontsize=FONT["title"],
                     fontweight="bold", color=color)
    style_ax(ax_inc)
    ax_inc.grid(True, alpha=0.3)

    # Panel 2: Cumulative
    ax_cum.plot(row_ts["date"], row_ts["cum_obs_mm"], color="grey",
                linewidth=LW["data"], alpha=0.8, label="Observed (cumulative)")
    ax_cum.plot(row_ts["date"], row_ts["cum_pred_mm"], color=color,
                linewidth=LW["data"], alpha=0.9, label="Predicted (cumulative)")
    ax_cum.set_xlim(T_START, T_END)
    ax_cum.set_xlabel("Date", fontsize=FONT["axis_label"])
    ax_cum.set_ylabel("Cumulative db (mm)", fontsize=FONT["axis_label"])
    ax_cum.tick_params(axis="x", rotation=30)
    ax_cum.legend(fontsize=FONT["legend"], loc="upper left")
    ax_cum.set_title("Cumulative compaction", fontsize=FONT["title"],
                     fontweight="bold", color=color)
    style_ax(ax_cum)
    ax_cum.grid(True, alpha=0.3)

    fig.subplots_adjust(top=0.88, hspace=0.25)
    out_path = RECON_DIR / f"reconstruction_{layer}.png"
    fig.savefig(out_path, dpi=DPI, pad_inches=0.15)
    plt.close(fig)
    print(f"Saved: {out_path}")

print("\nDone.")
