"""
07_joint_search.py
==================
Joint 4-parameter grid search with DETRENDING — cumulative MLCW and GWL are
detrended (intercept + linear + annual harmonic removed) before differencing.

Model: Δb_j(t) = b_j × [S_ske × ΔH_e(t−τ) + S_skv × ΔH_i(t−τ)] × 1000

All parameters bounded by physical reference ranges.
h_c and regime masks from RAW head (physical threshold).
Outlier filtering (5×MAD) retained.

Output:
  results_joint_search_detrended/
  plots/results/joint_search_detrended/
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
RESULTS_DIR = DEMO_DIR / "results_joint_search_detrended"
RESULTS_DIR.mkdir(exist_ok=True)
PLOTS_DIR   = DEMO_DIR / "plots" / "results" / "joint_search_detrended"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

SCRIPTS_IHMF = DEMO_DIR.parent / "scripts" / "10_ihmf"
sys.path.insert(0, str(SCRIPTS_IHMF))
from ihmf_model_v3 import build_regime_mask
from ihmf_detrend import detrend_signal

# ── Configuration ─────────────────────────────────────────────────────────────
STATION    = "TUKU"
TAU_MAX    = 120
REF_DATE   = pd.Timestamp("2015-01-16")
MAD_THRESH = 5.0
N_SS       = 15          # grid points per S_ske / S_skv dimension

COLORS = {ly: plt.cm.tab10(i) for i, ly in enumerate(["F1", "T1", "F2", "T2", "F3", "F4"])}
LAYERS_ORDERED = ["F1", "T1", "F2", "T2", "F3", "F4"]
T_START = pd.Timestamp("2015-01-01")
T_END   = pd.Timestamp("2026-01-01")

# ══════════════════════════════════════════════════════════════════════════════
# 1. Physical bounds per MLCW layer
# ══════════════════════════════════════════════════════════════════════════════

# Layer thickness from layer_thickness.csv
thickness_csv = DEMO_DIR.parent / "figures" / "prestage_data_analysis" / "layer_thickness.csv"
th_df = pd.read_csv(thickness_csv)
th_df = th_df[th_df["station"] == STATION].set_index("layer")
SPAN_M = {ly: float(th_df.loc[ly, "span_m"]) for ly in LAYERS_ORDERED if ly in th_df.index}

# S_ske / S_skv ranges from choushui_skeletal_storage_coeffs.md Table 3-2 & 3-4
# Mapped from hydrogeological layers to MLCW layers:
#   F1 → Layer 1              (shallow aquifer, 16.83m)
#   F2 → Layer 2.1 + 2.2      (union of ranges, 72.51m)
#   T2 → Layer 2.2            (sandy interbed, 5.29m)
#   F3 → Layer 3              (deep aquifer, 99.84m)
#   F4 → Layer 4              (deepest aquifer, 16.62m)
#   T1 → SKIP (span_m = 0)

BOUNDS = {
    "F1": {"s_ske_min": 7.27e-6,  "s_ske_max": 3.87e-4,
           "s_skv_min": 5.90e-5,  "s_skv_max": 2.20e-3,
           "b_max": SPAN_M.get("F1", 41.577), "source": "Layer 1"},
    "T1": {"s_ske_min": 0, "s_ske_max": 0, "s_skv_min": 0, "s_skv_max": 0,
           "b_max": 0.0, "source": "SKIP — pinch-out"},
    "F2": {"s_ske_min": 2.86e-6,  "s_ske_max": 9.89e-5,
           "s_skv_min": 1.60e-5,  "s_skv_max": 1.20e-3,
           "b_max": SPAN_M.get("F2", 106.284), "source": "Layer 2.1+2.2 union"},
    "T2": {"s_ske_min": 4.47e-6,  "s_ske_max": 9.89e-5,
           "s_skv_min": 1.60e-5,  "s_skv_max": 1.00e-3,
           "b_max": SPAN_M.get("T2", 16.299), "source": "Layer 2.2"},
    "F3": {"s_ske_min": 4.96e-6,  "s_ske_max": 1.14e-4,
           "s_skv_min": 1.53e-5,  "s_skv_max": 2.00e-3,
           "b_max": SPAN_M.get("F3", 110.494), "source": "Layer 3"},
    "F4": {"s_ske_min": 3.93e-6,  "s_ske_max": 7.96e-5,
           "s_skv_min": 1.78e-4,  "s_skv_max": 3.00e-3,
           "b_max": SPAN_M.get("F4", 16.617), "source": "Layer 4"},
}

print("=== Joint Search Bounds (TUKU) ===")
print(f"{'Layer':<5s} {'b_max(m)':>9s} {'S_ske_min':>12s} {'S_ske_max':>12s} "
      f"{'S_skv_min':>12s} {'S_skv_max':>12s}  Source")
print("-" * 85)
for ly in LAYERS_ORDERED:
    b = BOUNDS[ly]
    print(f"{ly:<5s} {b['b_max']:9.2f} {b['s_ske_min']:12.2e} {b['s_ske_max']:12.2e} "
          f"{b['s_skv_min']:12.2e} {b['s_skv_max']:12.2e}  {b['source']}")
print()

# ══════════════════════════════════════════════════════════════════════════════
# 2. Load data
# ══════════════════════════════════════════════════════════════════════════════

assign = pd.read_csv(
    DATA_DIR / "gwl_to_mlcw_layer_assignment_v4.csv",
    dtype={"assigned_wellcode": str},
)
tuku_assign = assign[assign["station"] == STATION].set_index("layer")

mlcw_raw = pd.read_csv(DATA_DIR / "TUKU_reconst_grouped_cleaned.csv", parse_dates=["datetime"])
mlcw_raw = mlcw_raw.sort_values("datetime").reset_index(drop=True)
mlcw_raw = mlcw_raw[mlcw_raw["datetime"] >= REF_DATE].reset_index(drop=True)
ref_row = mlcw_raw.iloc[0]
for col in [c for c in mlcw_raw.columns if c != "datetime"]:
    mlcw_raw[col] = mlcw_raw[col] - ref_row[col]
mlcw = mlcw_raw

# ══════════════════════════════════════════════════════════════════════════════
# 3. Per-layer joint search
# ══════════════════════════════════════════════════════════════════════════════

joint_results  = []
free_results   = []
all_metrics    = []
all_timeseries = []
raw_data_store = {}

for layer in LAYERS_ORDERED:
    bnd = BOUNDS[layer]
    if bnd["b_max"] == 0.0:
        print(f"  {layer}: b_max=0 — skipping")
        continue
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

    # ── Load + align GWL ────────────────────────────────────────────────────
    gwl_raw = pd.read_feather(gwl_path)
    gwl_raw["datetime"] = pd.to_datetime(gwl_raw["datetime"])
    gwl_raw = gwl_raw[["datetime", wellcode]].dropna(subset=[wellcode])
    gwl_raw = gwl_raw.rename(columns={wellcode: "head_m"})
    gwl_raw = gwl_raw.sort_values("datetime").reset_index(drop=True)
    head_ref = float(gwl_raw[gwl_raw["datetime"] <= REF_DATE]["head_m"].iloc[-1]) \
        if (gwl_raw["datetime"] <= REF_DATE).any() else float(gwl_raw["head_m"].iloc[0])
    gwl_raw["head_m"] = gwl_raw["head_m"] - head_ref

    mlcw_df = mlcw[["datetime", layer]].rename(columns={layer: "mlcw_mm"})
    aligned = pd.merge_asof(mlcw_df.sort_values("datetime"),
                            gwl_raw.sort_values("datetime"),
                            on="datetime", direction="nearest")
    aligned = aligned.dropna(subset=["head_m", "mlcw_mm"]).reset_index(drop=True)

    head_m  = aligned["head_m"].values.astype(float)
    mlcw_mm = aligned["mlcw_mm"].values.astype(float)
    dates   = aligned["datetime"].values

    if len(head_m) < 10:
        print(f"  {layer}: only {len(head_m)} epochs — skipping")
        continue

    # ── h_c from RAW head (before detrending) ───────────────────────────────
    pre_ref = aligned["datetime"] < REF_DATE
    h_c = float(head_m[pre_ref].min()) if pre_ref.sum() >= 10 else float(np.percentile(head_m, 10))

    # ── Detrend cumulative signals ──────────────────────────────────────────
    t_days = (dates - dates[0]).astype("timedelta64[D]").astype(float)
    head_d, _, _ = detrend_signal(t_days, head_m)
    mlcw_d, _, _ = detrend_signal(t_days, mlcw_mm)

    # ── Incremental from DETRENDED, regime from RAW ─────────────────────────
    inc_dH    = np.diff(head_d)
    inc_db    = np.diff(mlcw_d)
    inc_dates = dates[:-1]
    e_m, i_m  = build_regime_mask(head_m[:-1], h_c)

    # ── Outlier filtering ───────────────────────────────────────────────────
    med_db = np.median(inc_db)
    mad_db = np.median(np.abs(inc_db - med_db))
    clean_mask = np.abs(inc_db - med_db) <= MAD_THRESH * mad_db if mad_db > 0 else np.ones(len(inc_db), dtype=bool)
    n_out = (~clean_mask).sum()
    if n_out > 0:
        for idx in np.where(~clean_mask)[0]:
            print(f"  {layer}: OUTLIER {pd.Timestamp(inc_dates[idx]).strftime('%Y-%m-%d')}  "
                  f"inc_db={inc_db[idx]:+.4f}  ({abs(inc_db[idx]-med_db)/mad_db:.1f}×MAD)")
        inc_dH, inc_db, inc_dates = inc_dH[clean_mask], inc_db[clean_mask], inc_dates[clean_mask]
        e_m, i_m = e_m[clean_mask], i_m[clean_mask]

    T = len(inc_dH)

    # ── Build S_ske / S_skv grids (log-spaced) ──────────────────────────────
    ske_grid = np.logspace(np.log10(bnd["s_ske_min"]), np.log10(bnd["s_ske_max"]), N_SS)
    skv_grid = np.logspace(np.log10(bnd["s_skv_min"]), np.log10(bnd["s_skv_max"]), N_SS)
    b_max    = bnd["b_max"]

    print(f"  {layer}: {T} epochs  elastic={e_m.sum()}  inelastic={i_m.sum()}  "
          f"h_c={h_c:.2f}m  b_max={b_max:.1f}m")
    print(f"         S_ske grid: [{ske_grid[0]:.2e}, {ske_grid[-1]:.2e}]  "
          f"S_skv grid: [{skv_grid[0]:.2e}, {skv_grid[-1]:.2e}]")

    # ── Step 1: Cross-correlation with physical constraint ─────────────────
    # Only consider taus where OLS gives non-negative S_ke and S_kv (physical).
    ccf_curve = []
    for tau in range(TAU_MAX + 1):
        n = T - tau
        if n < 10:
            ccf_curve.append(np.nan)
            continue
        dH_lag = inc_dH[tau:]
        db_obs = inc_db[:n]
        e_tr = e_m[:n]; i_tr = i_m[:n]
        # Check physical sign: OLS slopes must be >= 0
        dH_e = dH_lag[e_tr]; db_e = db_obs[e_tr]
        dH_i = dH_lag[i_tr]; db_i = db_obs[i_tr]
        ske_ok = (e_tr.sum() < 4) or (np.dot(dH_e, dH_e) > 0 and np.dot(dH_e, db_e) >= 0)
        skv_ok = (i_tr.sum() < 4) or (np.dot(dH_i, dH_i) > 0 and np.dot(dH_i, db_i) >= 0)
        if not (ske_ok and skv_ok):
            ccf_curve.append(np.nan)   # physically invalid tau
            continue
        sd_h, sd_b = np.std(dH_lag), np.std(db_obs)
        if sd_h > 0 and sd_b > 0:
            r_val = float(np.corrcoef(dH_lag, db_obs)[0, 1])
        else:
            r_val = np.nan
        ccf_curve.append(r_val)

    # τ_opt = argmax |r| among physically-valid lags
    valid_ccf = [(i, abs(v)) for i, v in enumerate(ccf_curve) if not np.isnan(v)]
    if not valid_ccf:
        print(f"  {layer}: no physically-valid CCF lags — falling back to MSE")
        # Fallback: use MSE-based tau from free OLS
        best_free_fb = {"tau": 0, "mse": np.inf}
        for tau in range(TAU_MAX + 1):
            n = T - tau
            if n < 4: continue
            dH_lag = inc_dH[tau:]; db_obs = inc_db[:n]
            e_tr = e_m[:n]; i_tr = i_m[:n]
            S_ke_f, S_kv_f = 0.0, 0.0
            dH_e2, db_e2 = dH_lag[e_tr], db_obs[e_tr]
            if e_tr.sum() >= 4 and np.dot(dH_e2, dH_e2) > 0:
                S_ke_f = max(0.0, np.dot(dH_e2, db_e2) / np.dot(dH_e2, dH_e2))
            dH_i2, db_i2 = dH_lag[i_tr], db_obs[i_tr]
            if i_tr.sum() >= 4 and np.dot(dH_i2, dH_i2) > 0:
                S_kv_f = max(0.0, np.dot(dH_i2, db_i2) / np.dot(dH_i2, dH_i2))
            db_pred_f = np.where(e_tr, S_ke_f*dH_lag, 0.0) + np.where(i_tr, S_kv_f*dH_lag, 0.0)
            mse_f = float(np.mean((db_obs - db_pred_f)**2))
            if mse_f < best_free_fb["mse"]:
                best_free_fb = {"tau": tau, "mse": mse_f}
        tau_ccf = best_free_fb["tau"]
        r_at_opt = np.nan
    else:
        tau_ccf = max(valid_ccf, key=lambda x: x[1])[0]
        r_at_opt = ccf_curve[tau_ccf]

    # Also compute FREE OLS at CCF tau for comparison
    n_ccf = T - tau_ccf
    dH_lag_ccf = inc_dH[tau_ccf:]
    db_obs_ccf = inc_db[:n_ccf]
    e_trim_ccf = e_m[:n_ccf]
    i_trim_ccf = i_m[:n_ccf]

    S_ke_free, S_kv_free = 0.0, 0.0
    dH_e, db_e = dH_lag_ccf[e_trim_ccf], db_obs_ccf[e_trim_ccf]
    if e_trim_ccf.sum() >= 4 and np.dot(dH_e, dH_e) > 0:
        S_ke_free = max(0.0, np.dot(dH_e, db_e) / np.dot(dH_e, dH_e))
    dH_i, db_i = dH_lag_ccf[i_trim_ccf], db_obs_ccf[i_trim_ccf]
    if i_trim_ccf.sum() >= 4 and np.dot(dH_i, dH_i) > 0:
        S_kv_free = max(0.0, np.dot(dH_i, db_i) / np.dot(dH_i, dH_i))

    # ── Step 2: S_ske / S_skv grid search at τ_ccf only ──────────────────
    best_joint = {"tau": tau_ccf, "S_ske": 0.0, "S_skv": 0.0, "b": 0.0, "mse": np.inf}

    for ske in ske_grid:
        for skv in skv_grid:
            s = np.zeros(n_ccf)
            s[e_trim_ccf] = 1000.0 * ske * dH_lag_ccf[e_trim_ccf]
            s[i_trim_ccf] = 1000.0 * skv * dH_lag_ccf[i_trim_ccf]
            ss = float(np.dot(s, s))
            if ss < 1e-20:
                continue
            b_opt = float(np.dot(db_obs_ccf, s)) / ss
            b_opt = max(0.0, min(b_max, b_opt))
            if b_opt < 0.01:
                continue
            db_pred = b_opt * s
            mse_j = float(np.mean((db_obs_ccf - db_pred) ** 2))
            if mse_j < best_joint["mse"]:
                best_joint = {"tau": tau_ccf, "S_ske": ske, "S_skv": skv,
                              "b": b_opt, "mse": mse_j}

    # Also run free OLS at MSE-optimal tau for comparison
    best_free = {"tau": 0, "S_ke": 0.0, "S_kv": 0.0, "mse": np.inf}
    for tau in range(TAU_MAX + 1):
        n = T - tau
        if n < 4:
            continue
        dH_lag = inc_dH[tau:]
        db_obs = inc_db[:n]
        e_trim = e_m[:n]; i_trim = i_m[:n]
        S_ke_f, S_kv_f = 0.0, 0.0
        dH_e2, db_e2 = dH_lag[e_trim], db_obs[e_trim]
        if e_trim.sum() >= 4 and np.dot(dH_e2, dH_e2) > 0:
            S_ke_f = max(0.0, np.dot(dH_e2, db_e2) / np.dot(dH_e2, dH_e2))
        dH_i2, db_i2 = dH_lag[i_trim], db_obs[i_trim]
        if i_trim.sum() >= 4 and np.dot(dH_i2, dH_i2) > 0:
            S_kv_f = max(0.0, np.dot(dH_i2, db_i2) / np.dot(dH_i2, dH_i2))
        db_pred_f = np.where(e_trim, S_ke_f * dH_lag, 0.0) + np.where(i_trim, S_kv_f * dH_lag, 0.0)
        mse_f = float(np.mean((db_obs - db_pred_f) ** 2))
        if mse_f < best_free["mse"]:
            best_free = {"tau": tau, "S_ke": S_ke_f, "S_kv": S_kv_f, "mse": mse_f}

    # ── Compute metrics ─────────────────────────────────────────────────────
    tau_j = best_joint["tau"]
    tau_f = best_free["tau"]

    def r2_mse(mse_val, db, tau_val):
        n = len(db) - tau_val
        if n < 2: return np.nan
        ss_tot = float(np.sum((db[:n] - db[:n].mean()) ** 2))
        return float(1.0 - mse_val * n / ss_tot) if ss_tot > 0 else np.nan

    r2_j = r2_mse(best_joint["mse"], inc_db, tau_j)
    r2_f = r2_mse(best_free["mse"], inc_db, tau_f)

    S_ke_joint = best_joint["S_ske"] * best_joint["b"] * 1000  # mm/m
    S_kv_joint = best_joint["S_skv"] * best_joint["b"] * 1000

    print(f"         CCF τ_opt = {tau_ccf} epochs ({tau_ccf*5} days)  r = {r_at_opt:+.4f}  "
          f"(from {len(valid_ccf)} valid lags, max |r|)")
    print(f"         {'':<8s} {'tau':>4s} {'days':>6s} {'S_ke(mm/m)':>11s} "
          f"{'S_kv(mm/m)':>11s} {'b(m)':>8s} {'S_ske(1/m)':>11s} {'S_skv(1/m)':>11s} "
          f"{'MSE':>10s} {'R²':>8s}")
    print(f"         {'JOINT':<8s} {tau_j:4d} {tau_j*5:6d} {S_ke_joint:11.4f} "
          f"{S_kv_joint:11.4f} {best_joint['b']:8.2f} {best_joint['S_ske']:11.2e} "
          f"{best_joint['S_skv']:11.2e} {best_joint['mse']:10.6f} {r2_j:+8.4f}")
    print(f"         {'FREE':<8s} {tau_f:4d} {tau_f*5:6d} {best_free['S_ke']:11.4f} "
          f"{best_free['S_kv']:11.4f} {'—':>8s} {'—':>11s} {'—':>11s} "
          f"{best_free['mse']:10.6f} {r2_f:+8.4f}")

    # Check if joint solution hit bounds
    flags = []
    if best_joint["b"] >= b_max * 0.99:
        flags.append("b_at_upper")
    if best_joint["b"] <= 0.01:
        flags.append("b_at_zero")
    if best_joint["S_ske"] >= bnd["s_ske_max"] * 0.95:
        flags.append("ske_at_upper")
    if best_joint["S_skv"] >= bnd["s_skv_max"] * 0.95:
        flags.append("skv_at_upper")
    if flags:
        print(f"         ⚠ bounds hit: {', '.join(flags)}")

    joint_results.append(dict(
        layer=layer, b_max=b_max,
        tau_ccf=tau_ccf, tau_ccf_days=tau_ccf*5, r_ccf=round(r_at_opt, 6),
        tau_joint=tau_j, tau_joint_days=tau_j*5,
        S_ske=best_joint["S_ske"], S_skv=best_joint["S_skv"], b_m=round(best_joint["b"], 3),
        S_ke_bulk=round(S_ke_joint, 6), S_kv_bulk=round(S_kv_joint, 6),
        mse_joint=round(best_joint["mse"], 8), r2_joint=round(r2_j, 6),
        tau_free=tau_f, tau_free_days=tau_f*5,
        S_ke_free=round(best_free["S_ke"], 6), S_kv_free=round(best_free["S_kv"], 6),
        mse_free=round(best_free["mse"], 8), r2_free=round(r2_f, 6),
        bounds_hit=";".join(flags) if flags else "none",
    ))

    # ── Full reconstruction (best joint) ────────────────────────────────────
    n = T - tau_j
    dH_lag  = inc_dH[tau_j:]
    db_obs  = inc_db[:n]
    e_trim  = e_m[:n]; i_trim = i_m[:n]
    dates_n = inc_dates[:n]

    s = np.zeros(n)
    s[e_trim] = 1000.0 * best_joint["S_ske"] * dH_lag[e_trim]
    s[i_trim] = 1000.0 * best_joint["S_skv"] * dH_lag[i_trim]
    db_pred = best_joint["b"] * s

    residuals = db_obs - db_pred
    rmse = float(np.sqrt(np.mean(residuals**2)))
    mae  = float(np.mean(np.abs(residuals)))
    bias = float(np.mean(db_pred - db_obs))
    ss_res = float(np.sum(residuals**2))
    ss_tot = float(np.sum((db_obs - db_obs.mean())**2))
    r2_val = float(1.0 - ss_res/ss_tot) if ss_tot > 0 else np.nan
    r_val  = float(pearsonr(db_obs, db_pred)[0]) if np.std(db_pred)>0 and np.std(db_obs)>0 else np.nan

    all_metrics.append(dict(
        layer=layer, tau_opt=tau_j, tau_opt_days=tau_j*5,
        S_ske=best_joint["S_ske"], S_skv=best_joint["S_skv"], b_m=round(best_joint["b"],3),
        S_ke_bulk=S_ke_joint, S_kv_bulk=S_kv_joint,
        n_elastic=int(e_trim.sum()), n_inelastic=int(i_trim.sum()), n_epochs=n,
        MSE=round(best_joint["mse"],7), RMSE=round(rmse,7), MAE=round(mae,7),
        R2=round(r2_val,6),
        pearson_r=round(r_val,6) if not np.isnan(r_val) else None, bias=round(bias,7),
    ))

    all_timeseries.append(pd.DataFrame(dict(
        date=dates_n, layer=layer,
        db_obs_mm_epoch=db_obs.round(6), db_pred_mm_epoch=db_pred.round(6),
        cum_obs_mm=np.cumsum(db_obs).round(4), cum_pred_mm=np.cumsum(db_pred).round(4),
    )))

    raw_data_store[layer] = {
        "dates": dates, "head_m": head_m, "mlcw_mm": mlcw_mm,
        "inc_dH": inc_dH, "inc_db": inc_db, "inc_dates": inc_dates,
        "e_m": e_m, "i_m": i_m, "h_c": h_c, "span_m": b_max,
        "wellcode": wellcode, "tau_opt": tau_j,
        "S_ske": best_joint["S_ske"], "S_skv": best_joint["S_skv"], "b_m": best_joint["b"],
        "ccf_curve": ccf_curve, "tau_ccf": tau_ccf, "r_ccf": r_at_opt,
    }

# ══════════════════════════════════════════════════════════════════════════════
# 4. Save CSVs
# ══════════════════════════════════════════════════════════════════════════════

joint_df = pd.DataFrame(joint_results)
joint_df.to_csv(RESULTS_DIR / "joint_results.csv", index=False)
print(f"\nSaved: {RESULTS_DIR / 'joint_results.csv'}")

if all_metrics:
    pd.DataFrame(all_metrics).to_csv(RESULTS_DIR / "reconstruction_metrics.csv", index=False)
    ts_all = pd.concat(all_timeseries, ignore_index=True)
    ts_all.to_csv(RESULTS_DIR / "reconstruction_timeseries.csv", index=False)

# Comparison
comp = joint_df[["layer","b_max","tau_joint","tau_joint_days","S_ske","S_skv","b_m",
                  "S_ke_bulk","S_kv_bulk","r2_joint","tau_free","S_ke_free","S_kv_free",
                  "r2_free","bounds_hit"]].copy()
comp.to_csv(RESULTS_DIR / "comparison.csv", index=False)
print(f"Saved: {RESULTS_DIR / 'comparison.csv'}")

# ══════════════════════════════════════════════════════════════════════════════
# 5. Plots
# ══════════════════════════════════════════════════════════════════════════════

for layer in LAYERS_ORDERED:
    if layer not in raw_data_store:
        continue

    d        = raw_data_store[layer]
    color    = COLORS[layer]
    tau_opt  = int(d["tau_opt"])
    wellcode = str(d["wellcode"])
    h_c      = float(d["h_c"])
    b_max    = float(d["span_m"])
    b_fit    = float(d["b_m"])
    S_ske    = float(d["S_ske"])
    S_skv    = float(d["S_skv"])

    met = None
    for m in all_metrics:
        if m["layer"] == layer: met = m; break
    ts_layer = ts_all[ts_all["layer"] == layer].copy()
    ts_layer["date"] = pd.to_datetime(ts_layer["date"])
    ts_layer = ts_layer[(ts_layer["date"] >= T_START) & (ts_layer["date"] < T_END)]

    dates_cum = pd.to_datetime(d["dates"])
    mlcw_mm   = d["mlcw_mm"]

    fig, axes = plt.subplots(3, 1, figsize=(A4_PORTRAIT[0], 10.0))
    fig.suptitle(
        f"TUKU  |  Layer {layer}  |  Joint search  |  GWL well {wellcode}\n"
        f"τ={tau_opt*5}d  |  S_ske={S_ske:.2e}  S_skv={S_skv:.2e}  (1/m)  |  "
        f"b={b_fit:.1f}m (max={b_max:.1f}m)  |  h_c={h_c:.2f}m",
        fontsize=FONT["suptitle"], fontweight="bold", y=0.97)

    # Panel 1: Cumulative MLCW
    ax1 = axes[0]
    mask = (dates_cum >= T_START) & (dates_cum < T_END)
    ax1.plot(dates_cum[mask], mlcw_mm[mask], color=color, linewidth=LW["data"],
             label=f"MLCW cumulative (span={b_max:.1f}m)")
    ax1.set_ylabel("MLCW (mm)", fontsize=FONT["axis_label"])
    ax1.set_xlim(T_START, T_END)
    ax1.legend(fontsize=FONT["legend"], loc="upper left")
    ax1.set_title("Panel 1 — Cumulative MLCW compaction (non-detrended)",
                  fontsize=FONT["title"], fontweight="bold")
    style_ax(ax1); ax1.grid(True, alpha=0.3)

    # Panel 2: Incremental
    ax2 = axes[1]
    if ts_layer is not None and met is not None:
        ax2.plot(ts_layer["date"], ts_layer["db_obs_mm_epoch"], color="grey",
                 linewidth=LW["data"], alpha=0.7, label="Observed")
        ax2.plot(ts_layer["date"], ts_layer["db_pred_mm_epoch"], color=color,
                 linewidth=LW["data"], alpha=0.9, label="Predicted (joint)")
        ax2.axhline(0, color="black", linewidth=LW["grid"], linestyle="-")
        ax2.set_xlim(T_START, T_END)
        ax2.legend(fontsize=FONT["legend"], loc="upper right")
        ax2.set_title(
            f"Panel 2 — Incremental  |  S_ke={met['S_ke_bulk']:.4f}  "
            f"S_kv={met['S_kv_bulk']:.4f}  mm/m  |  R²={met['R2']:.3f}  "
            f"RMSE={met['RMSE']:.4f}",
            fontsize=FONT["title"], color=color, fontweight="bold")
    ax2.set_ylabel("db (mm/epoch)", fontsize=FONT["axis_label"])
    style_ax(ax2); ax2.grid(True, alpha=0.3)

    # Panel 3: Cumulative
    ax3 = axes[2]
    if ts_layer is not None:
        ax3.plot(ts_layer["date"], ts_layer["cum_obs_mm"], color="grey",
                 linewidth=LW["data"], alpha=0.8, label="Observed cumulative")
        ax3.plot(ts_layer["date"], ts_layer["cum_pred_mm"], color=color,
                 linewidth=LW["data"], alpha=0.9, label="Predicted cumulative")
        ax3.set_xlim(T_START, T_END)
        ax3.legend(fontsize=FONT["legend"], loc="upper left")
        ax3.set_title(
            f"Panel 3 — Cumulative  |  b={b_fit:.1f}m of {b_max:.1f}m classified  |  "
            f"S_ske={S_ske:.2e}  S_skv={S_skv:.2e}  (1/m)",
            fontsize=FONT["title"], color=color, fontweight="bold")
    ax3.set_xlabel("Date", fontsize=FONT["axis_label"])
    ax3.set_ylabel("Cumulative db (mm)", fontsize=FONT["axis_label"])
    ax3.tick_params(axis="x", rotation=30)
    style_ax(ax3); ax3.grid(True, alpha=0.3)

    fig.subplots_adjust(top=0.90, hspace=0.35)
    out_path = PLOTS_DIR / f"reconstruction_{layer}.png"
    fig.savefig(out_path, dpi=DPI, pad_inches=0.15)
    plt.close(fig)
    print(f"Saved: {out_path}")

# ── Cross-correlation curves grid ────────────────────────────────────────────
fig, axes = plt.subplots(2, 3, figsize=(A4_PORTRAIT[0], 6.5))
fig.suptitle("TUKU — Cross-correlation: r(ΔH(t−τ), Δb(t))  (detrended)",
             fontsize=FONT["suptitle"], fontweight="bold", y=0.98)
axes_flat = axes.flatten()
tau_axis = np.arange(TAU_MAX + 1)

for i, layer in enumerate(LAYERS_ORDERED):
    ax = axes_flat[i]
    if layer not in raw_data_store:
        ax.set_visible(False); continue

    d = raw_data_store[layer]
    ccf = np.array(d["ccf_curve"])
    tau_opt_ccf = int(d["tau_ccf"])
    r_opt = float(d["r_ccf"])
    color = COLORS[layer]
    span_m = float(d["span_m"])
    valid = ~np.isnan(ccf)

    ax.plot(tau_axis[valid] * 5, ccf[valid], color=color, linewidth=LW["data"],
            label=f"CCF (layer {layer})")
    ax.axvline(tau_opt_ccf * 5, color="black", linestyle="--", linewidth=LW["reference"])
    ax.axhline(0, color="grey", linewidth=LW["grid"], linestyle="-")
    ax.annotate(f"τ={tau_opt_ccf*5}d\nr={r_opt:+.3f}",
                xy=(tau_opt_ccf * 5, r_opt),
                xytext=(tau_opt_ccf * 5 + 20, r_opt * 0.85),
                fontsize=FONT["annotation"],
                arrowprops=dict(arrowstyle="->", color="black", lw=0.8))
    ax.set_title(f"Layer {layer}  (span={span_m:.1f}m)",
                 fontsize=FONT["title"], color=color, fontweight="bold")
    ax.set_xlabel("Lag τ (days)", fontsize=FONT["axis_label"])
    ax.set_ylabel("Pearson r", fontsize=FONT["axis_label"])
    ax.grid(True, alpha=0.3)
    style_ax(ax)

fig.subplots_adjust(left=0.08, right=0.97, bottom=0.10, top=0.88, hspace=0.40, wspace=0.30)
out_path = PLOTS_DIR / "ccf_curves_all_layers.png"
fig.savefig(out_path, dpi=DPI, pad_inches=0.15)
plt.close(fig)
print(f"Saved: {out_path}")

print("\nDone. Compare results_joint_search/ against results_physical_ss/")
