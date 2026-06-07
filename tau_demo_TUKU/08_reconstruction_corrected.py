"""
08_reconstruction_corrected.py
==============================
Reconstructs per-layer compaction at TUKU using the physical model:

    Δb_j(t) = S_ke · ΔH_j(t)          if elastic regime at driver time t
    Δb_j(t) = S_kv · ΔH_j(t)          if inelastic regime at driver time t

where compaction at epoch (t + τ) is driven by head at epoch t.

CAUSAL LAG CONVENTION (matches tau_grid_search_per_layer in ihmf_model_v3.py):
  - dH_driver  = inc_dH[:n]      — head epochs 0..n-1  (driver, earlier)
  - db_response= inc_db[tau:]    — compaction epochs tau..T-1  (response, later)
  - e_trim     = e_m[:n]         — regime mask at driver-time head (lag-consistent)

This is the OPPOSITE of script 03_reconstruct_and_evaluate.py which used
  dH_lagged = inc_dH[tau:] paired with db_obs = inc_db[:n]  (anti-causal).

Regime classification uses absolute head level from the npz aligned data
(build_regime_mask logic: elastic = head_m > h_c).

Outputs:
  results/reconstruction_corrected_metrics.csv / .json
  results/reconstruction_corrected_timeseries.csv
  plots/results/reconstruction_corrected/reconstruction_corrected_<layer>.png
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

# ── Paths ─────────────────────────────────────────────────────────────────────
DEMO_DIR    = Path(__file__).resolve().parent
RESULTS_DIR = DEMO_DIR / "results"
PLOTS_DIR   = DEMO_DIR / "plots" / "results" / "reconstruction_corrected"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

LAYERS_ORDERED = ["F1", "T1", "F2", "T2", "F3", "F4"]
T_START = pd.Timestamp("2015-01-01")
T_END   = pd.Timestamp("2026-01-01")
COLORS  = {ly: plt.cm.tab10(i) for i, ly in enumerate(LAYERS_ORDERED)}

# ── Load aligned data (produced by 01_run_tau_search.py) ─────────────────────
npz = np.load(RESULTS_DIR / "tuku_aligned_data.npz", allow_pickle=True)

def load_layer(layer):
    """Extract all arrays for one layer from the npz."""
    d = {}
    prefix = f"{layer}__"
    for key in npz.files:
        if key.startswith(prefix):
            d[key[len(prefix):]] = npz[key]
    d["dates"]     = pd.to_datetime(d["dates"])
    d["inc_dates"] = pd.to_datetime(d["inc_dates"])
    d["tau_opt"]   = int(d["tau_opt"])
    d["h_c"]       = float(d["h_c"])
    return d


# ── Reconstruction loop ───────────────────────────────────────────────────────
all_metrics    = []
all_timeseries = []

for layer in LAYERS_ORDERED:
    try:
        d = load_layer(layer)
    except Exception as exc:
        print(f"  {layer}: could not load — {exc}")
        continue

    tau      = d["tau_opt"]
    inc_dH   = d["inc_dH"].astype(float)   # m/epoch
    inc_db   = d["inc_db"].astype(float)   # mm/epoch
    inc_dates= d["inc_dates"]
    e_m      = d["e_m"].astype(bool)       # elastic at driver time (length T-1)
    i_m      = d["i_m"].astype(bool)
    h_c      = d["h_c"]
    wellcode = str(d["wellcode"])

    T = len(inc_dH)          # length of incremental arrays (= n_aligned - 1)
    n = T - tau              # number of usable (driver, response) pairs

    if n < 4:
        print(f"  {layer}: only {n} paired epochs after lag τ={tau} — skipping")
        continue

    # ── CAUSAL PAIRING ─────────────────────────────────────────────────────
    # Head at epochs 0..n-1 drives compaction at epochs tau..T-1
    dH_driver   = inc_dH[:n]      # GWL increment at driver time
    db_response = inc_db[tau:]    # MLCW increment at response time (n epochs)
    e_trim      = e_m[:n]         # regime at driver time (lag-consistent)
    i_trim      = i_m[:n]
    # Response dates correspond to tau..T-1 in inc_dates
    dates_response = inc_dates[tau:]

    # ── OLS: S_ke (elastic regime) ─────────────────────────────────────────
    S_ke = 0.0
    n_elastic = int(e_trim.sum())
    dH_e = dH_driver[e_trim]
    db_e = db_response[e_trim]
    if n_elastic >= 4 and np.dot(dH_e, dH_e) > 0:
        S_ke = max(0.0, float(np.dot(dH_e, db_e) / np.dot(dH_e, dH_e)))

    # ── OLS: S_kv (inelastic regime) ───────────────────────────────────────
    S_kv = 0.0
    n_inelastic = int(i_trim.sum())
    dH_i = dH_driver[i_trim]
    db_i = db_response[i_trim]
    if n_inelastic >= 4 and np.dot(dH_i, dH_i) > 0:
        S_kv = max(0.0, float(np.dot(dH_i, db_i) / np.dot(dH_i, dH_i)))

    # ── Physical law check: S_ke, S_kv >= 0 (guaranteed by max(0.0, ...) above) ──
    # Check S_kv / S_ke ratio
    ratio_str = "undefined (S_ke=0)"
    ratio_ok  = True
    if S_ke > 0 and S_kv > 0:
        ratio = S_kv / S_ke
        ratio_str = f"{ratio:.2f}x"
        ratio_ok  = 8.0 <= ratio <= 100.0

    # ── Predict ────────────────────────────────────────────────────────────
    db_pred = np.zeros(n)
    if n_elastic >= 4:
        db_pred[e_trim] = S_ke * dH_driver[e_trim]
    if n_inelastic >= 4:
        db_pred[i_trim] = S_kv * dH_driver[i_trim]

    # ── Metrics ────────────────────────────────────────────────────────────
    residuals = db_response - db_pred
    mse   = float(np.mean(residuals**2))
    rmse  = float(np.sqrt(mse))
    mae   = float(np.mean(np.abs(residuals)))
    bias  = float(np.mean(db_pred - db_response))
    ss_res = float(np.sum(residuals**2))
    ss_tot = float(np.sum((db_response - db_response.mean())**2))
    r2    = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else np.nan
    r_pear = float(pearsonr(db_response, db_pred)[0]) \
             if (np.std(db_pred) > 0 and np.std(db_response) > 0) else np.nan

    # ── Cumulative reconstruction ───────────────────────────────────────────
    cum_obs  = np.cumsum(db_response)
    cum_pred = np.cumsum(db_pred)

    # ── Console report ─────────────────────────────────────────────────────
    ratio_flag = "" if ratio_ok else "  *** RATIO OUT OF RANGE ***"
    print(
        f"  {layer}: τ={tau:3d} ({tau*5:4d}d)  "
        f"S_ke={S_ke:.5f}  S_kv={S_kv:.5f}  ratio={ratio_str}"
        f"{ratio_flag}\n"
        f"        n_el={n_elastic}  n_in={n_inelastic}  n_tot={n}\n"
        f"        RMSE={rmse:.5f} mm/ep  R²={r2:.4f}  r={r_pear:.4f}  bias={bias:+.5f}\n"
        f"        cum_obs: [{cum_obs.min():.2f}, {cum_obs.max():.2f}] mm"
        f"  cum_pred: [{cum_pred.min():.2f}, {cum_pred.max():.2f}] mm\n"
    )

    all_metrics.append(dict(
        layer=layer, wellcode=wellcode, tau_opt=tau, tau_opt_days=tau*5,
        h_c=round(h_c, 4),
        S_ke=round(S_ke, 7), S_kv=round(S_kv, 7),
        ratio_skv_ske=round(S_kv/S_ke, 3) if S_ke > 0 else None,
        ratio_physical_8_100=ratio_ok,
        n_elastic=n_elastic, n_inelastic=n_inelastic, n_epochs=n,
        MSE=round(mse, 7), RMSE=round(rmse, 7), MAE=round(mae, 7),
        R2=round(r2, 6),
        pearson_r=round(r_pear, 6) if not np.isnan(r_pear) else None,
        bias=round(bias, 7),
        cum_obs_min_mm=round(float(cum_obs.min()), 4),
        cum_obs_max_mm=round(float(cum_obs.max()), 4),
        cum_pred_min_mm=round(float(cum_pred.min()), 4),
        cum_pred_max_mm=round(float(cum_pred.max()), 4),
    ))

    all_timeseries.append(pd.DataFrame(dict(
        date=dates_response,
        layer=layer,
        db_obs_mm_epoch=db_response.round(6),
        db_pred_mm_epoch=db_pred.round(6),
        cum_obs_mm=cum_obs.round(4),
        cum_pred_mm=cum_pred.round(4),
    )))


# ── Save results ──────────────────────────────────────────────────────────────
metrics_df = pd.DataFrame(all_metrics)
metrics_df.to_csv(RESULTS_DIR / "reconstruction_corrected_metrics.csv", index=False)
print(f"\nSaved: {RESULTS_DIR / 'reconstruction_corrected_metrics.csv'}")

ts_all = pd.concat(all_timeseries, ignore_index=True)
ts_all.to_csv(RESULTS_DIR / "reconstruction_corrected_timeseries.csv", index=False)
print(f"Saved: {RESULTS_DIR / 'reconstruction_corrected_timeseries.csv'}  ({len(ts_all)} rows)")

json.dump(
    all_metrics,
    open(RESULTS_DIR / "reconstruction_corrected_metrics.json", "w"),
    indent=2, default=str,
)
print(f"Saved: {RESULTS_DIR / 'reconstruction_corrected_metrics.json'}")


# ── Plot: one figure per layer ─────────────────────────────────────────────────
for layer in LAYERS_ORDERED:
    sub = metrics_df[metrics_df["layer"] == layer]
    if sub.empty:
        continue
    row = sub.iloc[0]
    ts  = ts_all[ts_all["layer"] == layer].copy()
    ts["date"] = pd.to_datetime(ts["date"])
    ts = ts[(ts["date"] >= T_START) & (ts["date"] < T_END)]

    color    = COLORS[layer]
    tau_days = int(row["tau_opt_days"])
    R2_val   = float(row["R2"])
    RMSE_val = float(row["RMSE"])
    S_ke_val = float(row["S_ke"])
    S_kv_val = float(row["S_kv"])
    r_val    = row["pearson_r"]
    ratio_val= row["ratio_skv_ske"]

    fig, (ax_inc, ax_cum) = plt.subplots(2, 1, figsize=(11, 7.5), sharex=True)
    fig.suptitle(
        f"TUKU  |  Layer {layer}  |  Corrected reconstruction (causal lag)\n"
        f"τ = {tau_days} days  |  S_ke = {S_ke_val:.5f}  S_kv = {S_kv_val:.5f}"
        f"  ratio = {ratio_val}  |  R² = {R2_val:.3f}  RMSE = {RMSE_val:.4f} mm/ep",
        fontsize=12, fontweight="bold", y=0.98,
    )

    ax_inc.plot(ts["date"], ts["db_obs_mm_epoch"], color="grey",
                linewidth=1.0, alpha=0.7, label="Observed MLCW increment")
    ax_inc.plot(ts["date"], ts["db_pred_mm_epoch"], color=color,
                linewidth=1.0, alpha=0.9, label="Predicted increment")
    ax_inc.axhline(0, color="black", linewidth=0.6)
    ax_inc.set_ylabel("db (mm/epoch)", fontsize=12)
    ax_inc.legend(fontsize=11, loc="upper right")
    ax_inc.set_title("Incremental compaction per 5-day epoch", fontsize=11, fontweight="bold")
    ax_inc.grid(True, alpha=0.3)

    ax_cum.plot(ts["date"], ts["cum_obs_mm"], color="grey",
                linewidth=1.2, alpha=0.8, label="Observed (cumulative)")
    ax_cum.plot(ts["date"], ts["cum_pred_mm"], color=color,
                linewidth=1.2, alpha=0.9, label="Predicted (cumulative)")
    ax_cum.set_xlim(T_START, T_END)
    ax_cum.set_xlabel("Date", fontsize=12)
    ax_cum.set_ylabel("Cumulative db (mm)", fontsize=12)
    ax_cum.tick_params(axis="x", rotation=30)
    ax_cum.legend(fontsize=11, loc="upper left")
    ax_cum.set_title("Cumulative compaction", fontsize=11, fontweight="bold")
    ax_cum.grid(True, alpha=0.3)

    fig.tight_layout(rect=[0, 0, 1, 0.93])
    out_path = PLOTS_DIR / f"reconstruction_corrected_{layer}.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")

print("\nDone.")
