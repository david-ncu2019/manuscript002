"""
05_detrended_reconstruction.py
==============================
Detrends cumulative MLCW and GWL signals, then reconstructs detrended MLCW
from detrended GWL via the same tau-search + S_ke/S_kv fitting pipeline.

Detrending uses detrend_signal from ihmf_detrend.py: removes
[intercept, linear trend, sin(2πt/365.25), cos(2πt/365.25)] via OLS.

Key differences from the standard pipeline (01/02/03):
  - Cumulative signals detrended BEFORE differencing
  - Tau search run with dates=None (skip seasonal removal — detrending handles it)
  - S_ke/S_kv fit and reconstruction on detrended signals only
  - h_c and regime masks computed from RAW head (physical threshold)

Output:
  results_detrended/
    tau_results.csv, tau_mse_curves.csv
    reconstruction_metrics.csv / .json
    reconstruction_timeseries.csv
    trend_coefficients.csv
    detrended_aligned_data.npz
  plots/results/detrended/
    reconstruction_F1.png ... F4.png   (6 per-layer, 3-panel)
    tau_mse_curves_all_layers.png
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
DATA_DIR    = DEMO_DIR / "data"
RESULTS_DIR = DEMO_DIR / "results_detrended_filtered"
RESULTS_DIR.mkdir(exist_ok=True)
PLOTS_DIR   = DEMO_DIR / "plots" / "results" / "detrended_filtered"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

# Import project functions
SCRIPTS_IHMF = DEMO_DIR.parent / "scripts" / "10_ihmf"
sys.path.insert(0, str(SCRIPTS_IHMF))
from ihmf_model_v3 import build_regime_mask, tau_grid_search_per_layer
from ihmf_detrend import detrend_signal

# ── Configuration ─────────────────────────────────────────────────────────────
STATION  = "TUKU"
TAU_MAX  = 120
REF_DATE = pd.Timestamp("2015-01-16")

COLORS = {ly: plt.cm.tab10(i) for i, ly in enumerate(["F1", "T1", "F2", "T2", "F3", "F4"])}
LAYERS_ORDERED = ["F1", "T1", "F2", "T2", "F3", "F4"]

T_START = pd.Timestamp("2015-01-01")
T_END   = pd.Timestamp("2026-01-01")

# ── Load assignment table ─────────────────────────────────────────────────────
assign = pd.read_csv(
    DATA_DIR / "gwl_to_mlcw_layer_assignment_v4.csv",
    dtype={"assigned_wellcode": str},
)
tuku_assign = assign[assign["station"] == STATION].set_index("layer")

# ── Load MLCW ─────────────────────────────────────────────────────────────────
mlcw_raw = pd.read_csv(DATA_DIR / "TUKU_reconst_grouped_cleaned.csv", parse_dates=["datetime"])
mlcw_raw = mlcw_raw.sort_values("datetime").reset_index(drop=True)
mlcw_raw = mlcw_raw[mlcw_raw["datetime"] >= REF_DATE].reset_index(drop=True)

# Zero-reference MLCW
ref_row = mlcw_raw.iloc[0]
layer_cols = [c for c in mlcw_raw.columns if c != "datetime"]
for col in layer_cols:
    mlcw_raw[col] = mlcw_raw[col] - ref_row[col]

mlcw = mlcw_raw

# ── Per-layer processing ──────────────────────────────────────────────────────
results        = []
mse_dict       = {}
raw_data       = {}
trend_records  = []       # trend coefficients per layer
all_metrics   = []
all_timeseries = []

for layer in LAYERS_ORDERED:
    if layer not in tuku_assign.index:
        print(f"  {layer}: not in assignment table — skipping")
        continue

    row      = tuku_assign.loc[layer]
    wellcode = row["assigned_wellcode"]
    feather  = Path(row["feather_file"]).name
    gwl_path = DATA_DIR / feather

    if not gwl_path.exists():
        print(f"  {layer}: GWL file {gwl_path.name} not found — skipping")
        continue

    # ── Load GWL ───────────────────────────────────────────────────────────
    gwl_raw = pd.read_feather(gwl_path)
    gwl_raw["datetime"] = pd.to_datetime(gwl_raw["datetime"])
    gwl_raw = gwl_raw[["datetime", wellcode]].dropna(subset=[wellcode])
    gwl_raw = gwl_raw.rename(columns={wellcode: "head_m"})
    gwl_raw = gwl_raw.sort_values("datetime").reset_index(drop=True)

    # Zero-reference GWL to REF_DATE
    head_ref = float(gwl_raw[gwl_raw["datetime"] <= REF_DATE]["head_m"].iloc[-1]) \
        if (gwl_raw["datetime"] <= REF_DATE).any() else float(gwl_raw["head_m"].iloc[0])
    gwl_raw["head_m"] = gwl_raw["head_m"] - head_ref

    # ── Align GWL to MLCW 5-day grid ───────────────────────────────────────
    mlcw_df = mlcw[["datetime", layer]].rename(columns={layer: "mlcw_mm"})
    aligned = pd.merge_asof(
        mlcw_df.sort_values("datetime"),
        gwl_raw.sort_values("datetime"),
        on="datetime", direction="nearest",
    )
    aligned = aligned.dropna(subset=["head_m", "mlcw_mm"]).reset_index(drop=True)

    head_m  = aligned["head_m"].values.astype(float)
    mlcw_mm = aligned["mlcw_mm"].values.astype(float)
    dates   = aligned["datetime"].values

    if len(head_m) < 10:
        print(f"  {layer}: only {len(head_m)} epochs — skipping")
        continue

    # ── Detrend cumulative signals ─────────────────────────────────────────
    t_days = (dates - dates[0]).astype("timedelta64[D]").astype(float)

    try:
        head_d, trend_coef_head, trend_head = detrend_signal(t_days, head_m)
        mlcw_d, trend_coef_mlcw, trend_mlcw = detrend_signal(t_days, mlcw_mm)
    except np.linalg.LinAlgError:
        print(f"  {layer}: detrend_signal OLS failed — skipping")
        continue

    # Physical interpretation of trend coefficients
    trend_rate_head_yr = float(trend_coef_head[1] * 365.25)       # m/yr
    trend_rate_mlcw_yr = float(trend_coef_mlcw[1] * 365.25)       # mm/yr
    annual_amp_head    = float(np.sqrt(trend_coef_head[2]**2 + trend_coef_head[3]**2))
    annual_amp_mlcw    = float(np.sqrt(trend_coef_mlcw[2]**2 + trend_coef_mlcw[3]**2))

    trend_records.append(dict(
        layer=layer,
        signal="head_m",
        c0=round(float(trend_coef_head[0]), 6),
        c1=round(float(trend_coef_head[1]), 8),
        c2=round(float(trend_coef_head[2]), 6),
        c3=round(float(trend_coef_head[3]), 6),
        trend_rate_per_year=round(trend_rate_head_yr, 4),
        annual_amplitude=round(annual_amp_head, 4),
    ))
    trend_records.append(dict(
        layer=layer,
        signal="mlcw_mm",
        c0=round(float(trend_coef_mlcw[0]), 6),
        c1=round(float(trend_coef_mlcw[1]), 8),
        c2=round(float(trend_coef_mlcw[2]), 6),
        c3=round(float(trend_coef_mlcw[3]), 6),
        trend_rate_per_year=round(trend_rate_mlcw_yr, 4),
        annual_amplitude=round(annual_amp_mlcw, 4),
    ))

    # ── Incremental from DETRENDED cumulative ──────────────────────────────
    inc_dH = np.diff(head_d)
    inc_db = np.diff(mlcw_d)
    inc_dates = dates[:-1]

    # ── h_c from RAW head (must compute BEFORE outlier filtering) ───────────
    pre_ref = aligned["datetime"] < REF_DATE
    if pre_ref.sum() >= 10:
        h_c = float(head_m[pre_ref].min())
    else:
        h_c = float(np.percentile(head_m, 10))

    # ── Regime masks from RAW head ─────────────────────────────────────────
    e_m, i_m = build_regime_mask(head_m[:-1], h_c)

    # ── Outlier filtering (MAD-based on inc_db) ────────────────────────────
    MAD_THRESH = 5.0
    med_db = np.median(inc_db)
    mad_db = np.median(np.abs(inc_db - med_db))
    if mad_db > 0:
        clean_mask = np.abs(inc_db - med_db) <= MAD_THRESH * mad_db
    else:
        clean_mask = np.ones(len(inc_db), dtype=bool)
    n_out = (~clean_mask).sum()
    if n_out > 0:
        outlier_dates = inc_dates[~clean_mask]
        outlier_vals  = inc_db[~clean_mask]
        for od, ov in zip(outlier_dates, outlier_vals):
            print(f"  {layer}: OUTLIER {pd.Timestamp(od).strftime('%Y-%m-%d')}  "
                  f"inc_db={ov:+.4f} mm/ep  ({abs(ov-med_db)/mad_db:.1f}×MAD)")
        inc_dH    = inc_dH[clean_mask]
        inc_db    = inc_db[clean_mask]
        inc_dates = inc_dates[clean_mask]
        e_m = e_m[clean_mask]
        i_m = i_m[clean_mask]

    # ── Tau grid search (NO seasonal removal — detrending handles it) ─────
    tau_opt, mse_curve, _ = tau_grid_search_per_layer(
        inc_dH, inc_db, e_m, i_m,
        tau_max=TAU_MAX, dates=None,
    )

    print(f"  {layer}: tau={tau_opt:3d} ({tau_opt*5:4d}d)  "
          f"S_ke/S_kv fitting: {e_m.sum()} elast, {i_m.sum()} inelast  "
          f"h_c={h_c:.2f}m  "
          f"trend head={trend_rate_head_yr:+.3f}m/yr  mlcw={trend_rate_mlcw_yr:+.2f}mm/yr")

    # Store tau search results
    mse_dict[layer] = mse_curve
    results.append({
        "layer": layer, "wellcode": wellcode, "gwl_file": feather,
        "h_c_m": round(h_c, 3),
        "n_elastic": int(e_m.sum()), "n_inelastic": int(i_m.sum()),
        "tau_opt": tau_opt, "tau_opt_days": tau_opt * 5,
        "mse_at_tau_opt": round(mse_curve[tau_opt], 6),
    })

    # ── Fit S_ke / S_kv on detrended incremental ──────────────────────────
    T = len(inc_dH)
    n = T - tau_opt
    if n < 4:
        print(f"  {layer}: only {n} epochs after lag — skipping reconstruction")
        raw_data[layer] = {
            "dates": dates, "head_m": head_m, "mlcw_mm": mlcw_mm,
            "head_detrended": head_d, "mlcw_detrended": mlcw_d,
            "trend_head": trend_head, "trend_mlcw": trend_mlcw,
            "trend_coef_head": trend_coef_head, "trend_coef_mlcw": trend_coef_mlcw,
            "inc_dH": inc_dH, "inc_db": inc_db, "inc_dates": inc_dates,
            "e_m": e_m, "i_m": i_m, "h_c": h_c, "tau_opt": tau_opt,
            "wellcode": wellcode,
        }
        continue

    dH_lagged = inc_dH[tau_opt:]
    db_obs    = inc_db[:n]
    e_trim    = e_m[:n]
    i_trim    = i_m[:n]
    dates_n   = inc_dates[:n]

    S_ke = 0.0
    dH_e, db_e = dH_lagged[e_trim], db_obs[e_trim]
    if e_trim.sum() >= 4 and np.dot(dH_e, dH_e) > 0:
        S_ke = max(0.0, np.dot(dH_e, db_e) / np.dot(dH_e, dH_e))

    S_kv = 0.0
    dH_i, db_i = dH_lagged[i_trim], db_obs[i_trim]
    if i_trim.sum() >= 4 and np.dot(dH_i, dH_i) > 0:
        S_kv = max(0.0, np.dot(dH_i, db_i) / np.dot(dH_i, dH_i))

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
    r_pearson = float(pearsonr(db_obs, db_pred)[0]) \
        if np.std(db_pred) > 0 and np.std(db_obs) > 0 else np.nan

    cum_obs  = np.cumsum(db_obs)
    cum_pred = np.cumsum(db_pred)

    print(f"         S_ke={S_ke:.5f}  S_kv={S_kv:.5f}  "
          f"RMSE={rmse:.5f} mm/ep  R²={r2:.4f}  r={r_pearson:.4f}  bias={bias:+.5f}")

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

    # Store full data for npz
    raw_data[layer] = {
        "dates": dates, "head_m": head_m, "mlcw_mm": mlcw_mm,
        "head_detrended": head_d, "mlcw_detrended": mlcw_d,
        "trend_head": trend_head, "trend_mlcw": trend_mlcw,
        "trend_coef_head": trend_coef_head, "trend_coef_mlcw": trend_coef_mlcw,
        "inc_dH": inc_dH, "inc_db": inc_db, "inc_dates": inc_dates,
        "e_m": e_m, "i_m": i_m, "h_c": h_c, "tau_opt": tau_opt,
        "wellcode": wellcode,
    }

# ══════════════════════════════════════════════════════════════════════════════
# Save CSVs / JSON
# ══════════════════════════════════════════════════════════════════════════════

# Tau results
results_df = pd.DataFrame(results)
results_df.to_csv(RESULTS_DIR / "tau_results.csv", index=False)
print(f"\nSaved: {RESULTS_DIR / 'tau_results.csv'}")

# MSE curves
tau_index = list(range(TAU_MAX + 1))
mse_df = pd.DataFrame({"tau_epochs": tau_index})
for layer in LAYERS_ORDERED:
    if layer in mse_dict:
        mse_df[layer] = mse_dict[layer]
mse_df.to_csv(RESULTS_DIR / "tau_mse_curves.csv", index=False)
print(f"Saved: {RESULTS_DIR / 'tau_mse_curves.csv'}")

# Trend coefficients
trend_df = pd.DataFrame(trend_records)
trend_df.to_csv(RESULTS_DIR / "trend_coefficients.csv", index=False)
print(f"Saved: {RESULTS_DIR / 'trend_coefficients.csv'}")

# Reconstruction metrics
if all_metrics:
    metrics_df = pd.DataFrame(all_metrics)
    metrics_df.to_csv(RESULTS_DIR / "reconstruction_metrics.csv", index=False)
    print(f"Saved: {RESULTS_DIR / 'reconstruction_metrics.csv'}")

    json.dump([{k: v for k, v in m.items()} for m in all_metrics],
              open(RESULTS_DIR / "reconstruction_metrics.json", "w"), indent=2, default=str)

    # Reconstruction timeseries
    ts_all = pd.concat(all_timeseries, ignore_index=True)
    ts_all.to_csv(RESULTS_DIR / "reconstruction_timeseries.csv", index=False)
    print(f"Saved: {RESULTS_DIR / 'reconstruction_timeseries.csv'}  ({len(ts_all)} rows)")

    # Evaluation summary
    json_summary = {}
    for layer_name, grp in ts_all.groupby("layer"):
        obs_v = grp["db_obs_mm_epoch"].values
        pred_v = grp["db_pred_mm_epoch"].values
        valid = np.isfinite(obs_v) & np.isfinite(pred_v)
        o, p = obs_v[valid], pred_v[valid]
        ss_r = float(np.sum((o - p)**2))
        ss_t = float(np.sum((o - o.mean())**2))
        json_summary[layer_name] = dict(
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

# NPZ
npz_path = RESULTS_DIR / "detrended_aligned_data.npz"
save_dict = {}
for layer_name, d in raw_data.items():
    for k, v in d.items():
        arr = np.array(v) if not isinstance(v, np.ndarray) else v
        save_dict[f"{layer_name}__{k}"] = arr
np.savez(npz_path, **save_dict)
print(f"Saved: {npz_path}")

# ══════════════════════════════════════════════════════════════════════════════
# Plots
# ══════════════════════════════════════════════════════════════════════════════

# ── Figure type 1: Per-layer 3-panel reconstruction ──────────────────────────
for layer in LAYERS_ORDERED:
    if layer not in raw_data:
        continue

    d         = raw_data[layer]
    color     = COLORS[layer]
    tau_opt   = int(d["tau_opt"])
    tau_days  = tau_opt * 5
    wellcode  = str(d["wellcode"])
    h_c       = float(d["h_c"])

    dates_cum   = pd.to_datetime(d["dates"])
    head_m      = d["head_m"]
    mlcw_mm     = d["mlcw_mm"]
    head_d      = d["head_detrended"]
    mlcw_d      = d["mlcw_detrended"]
    trend_head  = d["trend_head"]
    trend_mlcw  = d["trend_mlcw"]
    trend_coef_h = d["trend_coef_head"]
    trend_coef_m = d["trend_coef_mlcw"]

    # Get reconstruction timeseries if available
    ts_layer = None
    met_layer = None
    if all_metrics and all_timeseries:
        for m in all_metrics:
            if m["layer"] == layer:
                met_layer = m
                break
        ts_layer = ts_all[ts_all["layer"] == layer].copy()
        ts_layer["date"] = pd.to_datetime(ts_layer["date"])
        ts_layer = ts_layer[(ts_layer["date"] >= T_START) & (ts_layer["date"] < T_END)]

    trend_rate_h = float(trend_coef_h[1] * 365.25)
    trend_rate_m = float(trend_coef_m[1] * 365.25)

    fig, axes = plt.subplots(3, 1, figsize=(A4_PORTRAIT[0], 10.0), sharex=False)
    fig.suptitle(
        f"TUKU  |  Layer {layer}  |  GWL well {wellcode}\n"
        f"Detrended reconstruction  |  tau_opt = {tau_days} days  |  "
        f"h_c = {h_c:.2f} m MSL",
        fontsize=FONT["suptitle"], fontweight="bold", y=0.97,
    )

    # Panel 1: Trend removal — MLCW only (cleaner visual)
    ax1 = axes[0]
    mask_cum = (dates_cum >= T_START) & (dates_cum < T_END)
    ax1.plot(dates_cum[mask_cum], mlcw_mm[mask_cum], color="grey",
             linewidth=LW["data"], alpha=0.8, label="Original MLCW (cumulative)")
    ax1.plot(dates_cum[mask_cum], trend_mlcw[mask_cum], color=color,
             linewidth=LW["data"], linestyle="--", alpha=0.9,
             label=f"Fitted trend (linear {trend_rate_m:+.2f} mm/yr + annual)")
    ax1.set_ylabel("MLCW (mm)", fontsize=FONT["axis_label"])
    ax1.set_xlim(T_START, T_END)
    ax1.legend(fontsize=FONT["legend"], loc="upper left")
    ax1.set_title(
        f"Panel 1 — Trend removal  |  Head trend = {trend_rate_h:+.3f} m/yr  |  "
        f"MLCW trend = {trend_rate_m:+.2f} mm/yr",
        fontsize=FONT["title"], color=color, fontweight="bold")
    style_ax(ax1)
    ax1.grid(True, alpha=0.3)

    # Panel 2: Detrended incremental
    ax2 = axes[1]
    if ts_layer is not None:
        ax2.plot(ts_layer["date"], ts_layer["db_obs_mm_epoch"], color="grey",
                 linewidth=LW["data"], alpha=0.7, label="Observed (detrended)")
        ax2.plot(ts_layer["date"], ts_layer["db_pred_mm_epoch"], color=color,
                 linewidth=LW["data"], alpha=0.9, label="Predicted (detrended)")
        ax2.axhline(0, color="black", linewidth=LW["grid"], linestyle="-")
        ax2.set_xlim(T_START, T_END)
        ax2.legend(fontsize=FONT["legend"], loc="upper right")
        if met_layer:
            ax2.set_title(
                f"Panel 2 — Detrended incremental compaction  |  "
                f"S_ke={met_layer['S_ke']:.4f}  S_kv={met_layer['S_kv']:.4f}  "
                f"tau={tau_days}d",
                fontsize=FONT["title"], color=color, fontweight="bold")
        else:
            ax2.set_title("Panel 2 — Detrended incremental compaction",
                          fontsize=FONT["title"], color=color, fontweight="bold")
    else:
        ax2.text(0.5, 0.5, "No reconstruction (too few epochs)", transform=ax2.transAxes,
                 ha="center", va="center", fontsize=FONT["axis_label"])
    ax2.set_ylabel("db (mm/epoch)", fontsize=FONT["axis_label"])
    style_ax(ax2)
    ax2.grid(True, alpha=0.3)

    # Panel 3: Detrended cumulative
    ax3 = axes[2]
    if ts_layer is not None:
        ax3.plot(ts_layer["date"], ts_layer["cum_obs_mm"], color="grey",
                 linewidth=LW["data"], alpha=0.8, label="Observed cumul. (detrended)")
        ax3.plot(ts_layer["date"], ts_layer["cum_pred_mm"], color=color,
                 linewidth=LW["data"], alpha=0.9, label="Predicted cumul. (detrended)")
        ax3.set_xlim(T_START, T_END)
        ax3.legend(fontsize=FONT["legend"], loc="upper left")
        if met_layer:
            r_val = met_layer.get("pearson_r")
            r_str = f"{r_val:.3f}" if r_val is not None else "nan"
            ax3.set_title(
                f"Panel 3 — Detrended cumulative compaction  |  "
                f"R²={met_layer['R2']:.3f}  RMSE={met_layer['RMSE']:.4f} mm/ep  "
                f"r={r_str}",
                fontsize=FONT["title"], color=color, fontweight="bold")
        else:
            ax3.set_title("Panel 3 — Detrended cumulative compaction",
                          fontsize=FONT["title"], color=color, fontweight="bold")
    else:
        ax3.text(0.5, 0.5, "No reconstruction", transform=ax3.transAxes,
                 ha="center", va="center", fontsize=FONT["axis_label"])
    ax3.set_xlabel("Date", fontsize=FONT["axis_label"])
    ax3.set_ylabel("Cumulative db (mm)", fontsize=FONT["axis_label"])
    ax3.tick_params(axis="x", rotation=30)
    style_ax(ax3)
    ax3.grid(True, alpha=0.3)

    fig.subplots_adjust(top=0.90, hspace=0.35)
    out_path = PLOTS_DIR / f"reconstruction_{layer}.png"
    fig.savefig(out_path, dpi=DPI, pad_inches=0.15)
    plt.close(fig)
    print(f"Saved: {out_path}")

# ── Figure type 2: MSE curves 2x3 grid ───────────────────────────────────────
fig, axes = plt.subplots(2, 3, figsize=(A4_PORTRAIT[0], 6.5))
fig.suptitle(
    "TUKU — MSE curve for each layer (DETRENDED signals)\n"
    "(lower MSE = better compaction prediction with that lag)",
    fontsize=FONT["suptitle"], fontweight="bold", y=0.98,
)
axes_flat = axes.flatten()

for i, layer in enumerate(LAYERS_ORDERED):
    ax = axes_flat[i]
    if layer not in results_df["layer"].values or layer not in mse_df.columns:
        ax.set_visible(False)
        continue

    mse_vals = mse_df[layer].values.astype(float)
    tau_opt  = int(results_df[results_df["layer"] == layer]["tau_opt"].iloc[0])
    color    = COLORS[layer]
    finite   = np.isfinite(mse_vals)
    taus_arr = np.array(tau_index)

    ax.plot(taus_arr[finite], mse_vals[finite], color=color, linewidth=LW["data"],
            label=f"MSE (layer {layer})")
    ax.axvline(tau_opt, color="black", linestyle="--", linewidth=LW["reference"])
    ax.annotate(f"tau_opt = {tau_opt}\n({tau_opt*5} days)",
                xy=(tau_opt, mse_vals[tau_opt]),
                xytext=(tau_opt + 4, mse_vals[tau_opt] * 1.05 + 1e-4),
                fontsize=FONT["annotation"],
                arrowprops=dict(arrowstyle="->", color="black", lw=0.8))
    ax.set_title(f"Layer {layer} (detrended)", fontsize=FONT["title"],
                 color=color, fontweight="bold")
    ax.set_xlabel("tau (epochs)    [1 epoch ~ 5 days]", fontsize=FONT["axis_label"])
    ax.set_ylabel("MSE  [mm²/epoch²]", fontsize=FONT["axis_label"])
    ax.grid(True, alpha=0.3)
    style_ax(ax)

fig.subplots_adjust(left=0.08, right=0.97, bottom=0.10, top=0.88, hspace=0.40, wspace=0.30)
out_path = PLOTS_DIR / "tau_mse_curves_all_layers.png"
fig.savefig(out_path, dpi=DPI, pad_inches=0.15)
plt.close(fig)
print(f"Saved: {out_path}")

print("\nDone. Compare results/ vs results_detrended/")
