"""
06_physical_ss.py
=================
Reconstructs MLCW compaction using physically-constrained specific storage
coefficients:  Δb_j(t) = Ss_j × b_j × ΔH_j(t − τ_j)

Two variants per layer:
  A. FIXED  — S_ske, S_skv from reference tables; only τ is free
  B. BOUNDED — S fitted via OLS with upper bound = S_physical (lower bound = 0)

Uses NON-detrended signals (reference Ss values are for total, not residual).
Outlier filtering (5×MAD) is retained.

Reference sources:
  - Layer thickness: figures/prestage_data_analysis/layer_thickness.csv
  - S_ske / S_skv:   data/s_ske_skv_tables.md (per-layer values)
  - Ss range tables:  data/choushui_skeletal_storage_coeffs.md

Output:
  results_physical_ss/
    tau_results_fixed.csv, tau_results_bounded.csv
    reconstruction_metrics.csv
    comparison.csv
  plots/results/physical_ss/
    reconstruction_{layer}_{variant}.png
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
RESULTS_DIR = DEMO_DIR / "results_physical_ss"
RESULTS_DIR.mkdir(exist_ok=True)
PLOTS_DIR   = DEMO_DIR / "plots" / "results" / "physical_ss"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

SCRIPTS_IHMF = DEMO_DIR.parent / "scripts" / "10_ihmf"
sys.path.insert(0, str(SCRIPTS_IHMF))
from ihmf_model_v3 import build_regime_mask

# ── Configuration ─────────────────────────────────────────────────────────────
STATION   = "TUKU"
TAU_MAX   = 120
REF_DATE  = pd.Timestamp("2015-01-16")
MAD_THRESH = 5.0

COLORS = {ly: plt.cm.tab10(i) for i, ly in enumerate(["F1", "T1", "F2", "T2", "F3", "F4"])}
LAYERS_ORDERED = ["F1", "T1", "F2", "T2", "F3", "F4"]
T_START = pd.Timestamp("2015-01-01")
T_END   = pd.Timestamp("2026-01-01")

# ══════════════════════════════════════════════════════════════════════════════
# 1. Build Ss + thickness lookup for TUKU
# ══════════════════════════════════════════════════════════════════════════════

# Layer thickness from layer_thickness.csv
thickness_csv = DEMO_DIR.parent / "figures" / "prestage_data_analysis" / "layer_thickness.csv"
th_df = pd.read_csv(thickness_csv)
th_df = th_df[th_df["station"] == STATION].set_index("layer")
THICKNESS = {ly: float(th_df.loc[ly, "span_m"]) for ly in LAYERS_ORDERED if ly in th_df.index}

# S_ske / S_skv reference values for TUKU (from s_ske_skv_tables.md)
# Hydrogeological layers → MLCW layer mapping:
#   F1 → Layer 1 avg (no TUKU-specific data for Layer 1)
#   T1 → SKIP (span_m = 0, pinch-out)
#   F2 → thickness-weighted avg of Layer 2.1 + 2.2
#        2.1: 37m, S_ske=5.02e-5, S_skv=1.20e-3
#        2.2: 35.51m (72.51-37), S_ske=2.45e-5, S_skv=8.50e-4
#   T2 → Layer 2.2 values (sandy interbed, 5.29m)
#   F3 → Layer 3: S_ske=2.70e-5, S_skv=2.00e-3
#   F4 → Layer 4: S_ske=3.68e-5, S_skv=3.00e-3

# Layer 1 averages from range table (for F1 — no TUKU-specific Layer 1 data)
L1_S_SKE = 1.06e-4
L1_S_SKV = 6.66e-4

# F2 thickness-weighted
F2_S_SKE = (5.02e-5 * 37.0 + 2.45e-5 * 35.51) / 72.51  # = 3.76e-5
F2_S_SKV = (1.20e-3 * 37.0 + 8.50e-4 * 35.51) / 72.51  # = 1.03e-3

SS_LOOKUP = {
    "F1": {"s_ske": L1_S_SKE,  "s_skv": L1_S_SKV,  "span_m": THICKNESS.get("F1", 41.577),
           "source": "Layer 1 average (no TUKU-specific L1 data)"},
    "T1": {"s_ske": 0.0,       "s_skv": 0.0,        "span_m": 0.0,
           "source": "SKIP — pinch-out, zero thickness"},
    "F2": {"s_ske": F2_S_SKE,  "s_skv": F2_S_SKV,   "span_m": THICKNESS.get("F2", 106.284),
           "source": "Thickness-weighted avg of Layer 2.1 (37m) + 2.2 (35.5m)"},
    "T2": {"s_ske": 2.45e-5,   "s_skv": 8.50e-4,    "span_m": THICKNESS.get("T2", 16.299),
           "source": "Layer 2.2 values (sandy interbed)"},
    "F3": {"s_ske": 2.70e-5,   "s_skv": 2.00e-3,    "span_m": THICKNESS.get("F3", 110.494),
           "source": "Layer 3"},
    "F4": {"s_ske": 3.68e-5,   "s_skv": 3.00e-3,    "span_m": THICKNESS.get("F4", 16.617),
           "source": "Layer 4"},
}

print("=== Physical Ss × Thickness Lookup (TUKU) ===")
print(f"{'Layer':<5s} {'span_m':>8s} {'S_ske (1/m)':>14s} {'S_skv (1/m)':>14s} "
      f"{'S_ke (mm/m)':>12s} {'S_kv (mm/m)':>12s}  Source")
print("-" * 95)
for ly in LAYERS_ORDERED:
    s = SS_LOOKUP[ly]
    ske_bulk = s["s_ske"] * s["span_m"] * 1000
    skv_bulk = s["s_skv"] * s["span_m"] * 1000
    print(f"{ly:<5s} {s['span_m']:8.2f} {s['s_ske']:14.2e} {s['s_skv']:14.2e} "
          f"{ske_bulk:12.4f} {skv_bulk:12.4f}  {s['source']}")
print()

# ══════════════════════════════════════════════════════════════════════════════
# 2. Load assignment table + MLCW
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
layer_cols = [c for c in mlcw_raw.columns if c != "datetime"]
for col in layer_cols:
    mlcw_raw[col] = mlcw_raw[col] - ref_row[col]
mlcw = mlcw_raw

# ══════════════════════════════════════════════════════════════════════════════
# 3. Per-layer processing
# ══════════════════════════════════════════════════════════════════════════════

all_results     = []   # tau search results
all_metrics     = []   # reconstruction metrics
all_timeseries  = []
raw_data_store  = {}
mse_curves_fixed   = {}
mse_curves_bounded = {}
mse_curves_free    = {}

for layer in LAYERS_ORDERED:
    ss_info = SS_LOOKUP[layer]
    span_m  = ss_info["span_m"]

    if span_m == 0.0:
        print(f"  {layer}: span_m=0 (pinch-out) — skipping")
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

    # ── Load GWL ───────────────────────────────────────────────────────────
    gwl_raw = pd.read_feather(gwl_path)
    gwl_raw["datetime"] = pd.to_datetime(gwl_raw["datetime"])
    gwl_raw = gwl_raw[["datetime", wellcode]].dropna(subset=[wellcode])
    gwl_raw = gwl_raw.rename(columns={wellcode: "head_m"})
    gwl_raw = gwl_raw.sort_values("datetime").reset_index(drop=True)

    head_ref = float(gwl_raw[gwl_raw["datetime"] <= REF_DATE]["head_m"].iloc[-1]) \
        if (gwl_raw["datetime"] <= REF_DATE).any() else float(gwl_raw["head_m"].iloc[0])
    gwl_raw["head_m"] = gwl_raw["head_m"] - head_ref

    # ── Align GWL to MLCW ──────────────────────────────────────────────────
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

    # ── h_c from RAW head ──────────────────────────────────────────────────
    pre_ref = aligned["datetime"] < REF_DATE
    if pre_ref.sum() >= 10:
        h_c = float(head_m[pre_ref].min())
    else:
        h_c = float(np.percentile(head_m, 10))

    # ── Incremental signals (NO detrending) ────────────────────────────────
    inc_dH    = np.diff(head_m)
    inc_db    = np.diff(mlcw_mm)
    inc_dates = dates[:-1]

    # ── Regime masks ───────────────────────────────────────────────────────
    e_m, i_m = build_regime_mask(head_m[:-1], h_c)

    # ── Outlier filtering ──────────────────────────────────────────────────
    med_db = np.median(inc_db)
    mad_db = np.median(np.abs(inc_db - med_db))
    if mad_db > 0:
        clean_mask = np.abs(inc_db - med_db) <= MAD_THRESH * mad_db
    else:
        clean_mask = np.ones(len(inc_db), dtype=bool)
    n_out = (~clean_mask).sum()
    if n_out > 0:
        for idx in np.where(~clean_mask)[0]:
            print(f"  {layer}: OUTLIER {pd.Timestamp(inc_dates[idx]).strftime('%Y-%m-%d')}  "
                  f"inc_db={inc_db[idx]:+.4f} mm/ep  "
                  f"({abs(inc_db[idx]-med_db)/mad_db:.1f}×MAD)")
        inc_dH    = inc_dH[clean_mask]
        inc_db    = inc_db[clean_mask]
        inc_dates = inc_dates[clean_mask]
        e_m = e_m[clean_mask]
        i_m = i_m[clean_mask]

    T = len(inc_dH)
    print(f"  {layer}: {T} epochs  elastic={e_m.sum()}  inelastic={i_m.sum()}  "
          f"h_c={h_c:.2f}m  span={span_m:.2f}m")

    # ── Physical bulk coefficients ─────────────────────────────────────────
    S_ke_phys = ss_info["s_ske"] * span_m * 1000   # mm/m
    S_kv_phys = ss_info["s_skv"] * span_m * 1000   # mm/m

    # ── Grid search: 3 variants per tau ────────────────────────────────────
    mse_fixed   = []
    mse_bounded = []
    mse_free    = []
    best_tau_fixed   = (0, np.inf, 0.0, 0.0)  # (tau, mse, S_ke, S_kv)
    best_tau_bounded = (0, np.inf, 0.0, 0.0)
    best_tau_free    = (0, np.inf, 0.0, 0.0)

    for tau in range(TAU_MAX + 1):
        n = T - tau
        if n < 4:
            mse_fixed.append(np.inf)
            mse_bounded.append(np.inf)
            mse_free.append(np.inf)
            continue

        dH_lag  = inc_dH[tau:]
        db_trim = inc_db[:n]
        e_trim  = e_m[:n]
        i_trim  = i_m[:n]

        # --- Variant A: FIXED physical Ss ---
        db_pred_fixed = (np.where(e_trim, S_ke_phys * dH_lag, 0.0) +
                         np.where(i_trim, S_kv_phys * dH_lag, 0.0))
        mse_f = float(np.mean((db_trim - db_pred_fixed) ** 2))
        mse_fixed.append(mse_f)
        if mse_f < best_tau_fixed[1]:
            best_tau_fixed = (tau, mse_f, S_ke_phys, S_kv_phys)

        # --- Variant B: BOUNDED OLS (upper bound = S_physical) ---
        S_ke_b, S_kv_b = 0.0, 0.0
        dH_e, db_e = dH_lag[e_trim], db_trim[e_trim]
        if e_trim.sum() >= 4 and np.dot(dH_e, dH_e) > 0:
            S_ke_b = max(0.0, min(S_ke_phys, np.dot(dH_e, db_e) / np.dot(dH_e, dH_e)))
        dH_i, db_i = dH_lag[i_trim], db_trim[i_trim]
        if i_trim.sum() >= 4 and np.dot(dH_i, dH_i) > 0:
            S_kv_b = max(0.0, min(S_kv_phys, np.dot(dH_i, db_i) / np.dot(dH_i, dH_i)))
        db_pred_bounded = (np.where(e_trim, S_ke_b * dH_lag, 0.0) +
                           np.where(i_trim, S_kv_b * dH_lag, 0.0))
        mse_b = float(np.mean((db_trim - db_pred_bounded) ** 2))
        mse_bounded.append(mse_b)
        if mse_b < best_tau_bounded[1]:
            best_tau_bounded = (tau, mse_b, S_ke_b, S_kv_b)

        # --- Variant C: FREE OLS (no bounds, for comparison) ---
        S_ke_f, S_kv_f = 0.0, 0.0
        if e_trim.sum() >= 4 and np.dot(dH_e, dH_e) > 0:
            S_ke_f = max(0.0, np.dot(dH_e, db_e) / np.dot(dH_e, dH_e))
        if i_trim.sum() >= 4 and np.dot(dH_i, dH_i) > 0:
            S_kv_f = max(0.0, np.dot(dH_i, db_i) / np.dot(dH_i, dH_i))
        db_pred_free = (np.where(e_trim, S_ke_f * dH_lag, 0.0) +
                        np.where(i_trim, S_kv_f * dH_lag, 0.0))
        mse_fr = float(np.mean((db_trim - db_pred_free) ** 2))
        mse_free.append(mse_fr)
        if mse_fr < best_tau_free[1]:
            best_tau_free = (tau, mse_fr, S_ke_f, S_kv_f)

    mse_curves_fixed[layer]   = mse_fixed
    mse_curves_bounded[layer] = mse_bounded
    mse_curves_free[layer]    = mse_free

    # ── Log results ────────────────────────────────────────────────────────
    tau_f, mse_f, ske_f, skv_f = best_tau_fixed
    tau_b, mse_b, ske_b, skv_b = best_tau_bounded
    tau_r, mse_r, ske_r, skv_r = best_tau_free

    def r2_from_mse(mse_val, db):
        ss_tot = float(np.sum((db - db.mean())**2))
        n = len(db)
        return float(1.0 - mse_val * n / ss_tot) if ss_tot > 0 else np.nan

    r2_f = r2_from_mse(mse_f, inc_db[:T-tau_f])
    r2_b = r2_from_mse(mse_b, inc_db[:T-tau_b])
    r2_r = r2_from_mse(mse_r, inc_db[:T-tau_r])

    print(f"         {'Variant':<10s} {'tau':>4s} {'days':>6s} {'S_ke':>10s} {'S_kv':>10s} "
          f"{'MSE':>12s} {'R²':>8s}")
    print(f"         {'FIXED':<10s} {tau_f:4d} {tau_f*5:6d} {ske_f:10.4f} {skv_f:10.4f} "
          f"{mse_f:12.6f} {r2_f:+8.4f}")
    print(f"         {'BOUNDED':<10s} {tau_b:4d} {tau_b*5:6d} {ske_b:10.4f} {skv_b:10.4f} "
          f"{mse_b:12.6f} {r2_b:+8.4f}")
    print(f"         {'FREE':<10s} {tau_r:4d} {tau_r*5:6d} {ske_r:10.4f} {skv_r:10.4f} "
          f"{mse_r:12.6f} {r2_r:+8.4f}")
    print(f"         Physical S_ke={S_ke_phys:.4f}  S_kv={S_kv_phys:.4f}")

    all_results.append(dict(
        layer=layer, span_m=span_m,
        S_ke_phys=S_ke_phys, S_kv_phys=S_kv_phys,
        tau_fixed=tau_f, tau_fixed_days=tau_f*5,
        ske_fixed=round(ske_f,6), skv_fixed=round(skv_f,6),
        mse_fixed=round(mse_f,8), r2_fixed=round(r2_f,6),
        tau_bounded=tau_b, tau_bounded_days=tau_b*5,
        ske_bounded=round(ske_b,6), skv_bounded=round(skv_b,6),
        mse_bounded=round(mse_b,8), r2_bounded=round(r2_b,6),
        tau_free=tau_r, tau_free_days=tau_r*5,
        ske_free=round(ske_r,6), skv_free=round(skv_r,6),
        mse_free=round(mse_r,8), r2_free=round(r2_r,6),
    ))

    # ── Full reconstruction at best tau (FREE variant as reference) ────────
    n = T - tau_r
    dH_lag  = inc_dH[tau_r:]
    db_obs  = inc_db[:n]
    e_trim  = e_m[:n]
    i_trim  = i_m[:n]
    dates_n = inc_dates[:n]

    db_pred_free = (np.where(e_trim, ske_r * dH_lag, 0.0) +
                    np.where(i_trim, skv_r * dH_lag, 0.0))
    residuals = db_obs - db_pred_free
    rmse = float(np.sqrt(np.mean(residuals**2)))
    mae  = float(np.mean(np.abs(residuals)))
    bias = float(np.mean(db_pred_free - db_obs))
    ss_res = float(np.sum(residuals**2))
    ss_tot = float(np.sum((db_obs - db_obs.mean())**2))
    r2_val = float(1.0 - ss_res/ss_tot) if ss_tot > 0 else np.nan
    r_val  = float(pearsonr(db_obs, db_pred_free)[0]) \
        if np.std(db_pred_free) > 0 and np.std(db_obs) > 0 else np.nan

    all_metrics.append(dict(
        layer=layer, tau_opt=tau_r, tau_opt_days=tau_r*5,
        S_ke=ske_r, S_kv=skv_r,
        n_elastic=int(e_trim.sum()), n_inelastic=int(i_trim.sum()),
        n_epochs=n, MSE=round(mse_r,7), RMSE=round(rmse,7), MAE=round(mae,7),
        R2=round(r2_val,6),
        pearson_r=round(r_val,6) if not np.isnan(r_val) else None,
        bias=round(bias,7),
    ))

    all_timeseries.append(pd.DataFrame(dict(
        date=dates_n, layer=layer,
        db_obs_mm_epoch=db_obs.round(6),
        db_pred_mm_epoch=db_pred_free.round(6),
        cum_obs_mm=np.cumsum(db_obs).round(4),
        cum_pred_mm=np.cumsum(db_pred_free).round(4),
    )))

    # Store raw data
    raw_data_store[layer] = {
        "dates": dates, "head_m": head_m, "mlcw_mm": mlcw_mm,
        "inc_dH": inc_dH, "inc_db": inc_db, "inc_dates": inc_dates,
        "e_m": e_m, "i_m": i_m, "h_c": h_c, "span_m": span_m,
        "wellcode": wellcode, "tau_opt_free": tau_r,
    }

# ══════════════════════════════════════════════════════════════════════════════
# 4. Save CSVs
# ══════════════════════════════════════════════════════════════════════════════

results_df = pd.DataFrame(all_results)
results_df.to_csv(RESULTS_DIR / "tau_results_all_variants.csv", index=False)
print(f"\nSaved: {RESULTS_DIR / 'tau_results_all_variants.csv'}")

# Per-variant tau results
for variant, cols in [("fixed", ["tau_fixed","tau_fixed_days","ske_fixed","skv_fixed","mse_fixed","r2_fixed"]),
                       ("bounded", ["tau_bounded","tau_bounded_days","ske_bounded","skv_bounded","mse_bounded","r2_bounded"]),
                       ("free", ["tau_free","tau_free_days","ske_free","skv_free","mse_free","r2_free"])]:
    vdf = results_df[["layer","span_m","S_ke_phys","S_kv_phys"] + cols].copy()
    vdf.to_csv(RESULTS_DIR / f"tau_results_{variant}.csv", index=False)
    print(f"Saved: {RESULTS_DIR / f'tau_results_{variant}.csv'}")

# MSE curves
tau_index = list(range(TAU_MAX + 1))
for name, curves in [("fixed", mse_curves_fixed), ("bounded", mse_curves_bounded),
                      ("free", mse_curves_free)]:
    mse_df = pd.DataFrame({"tau_epochs": tau_index})
    for ly in LAYERS_ORDERED:
        if ly in curves:
            mse_df[ly] = curves[ly]
    mse_df.to_csv(RESULTS_DIR / f"tau_mse_curves_{name}.csv", index=False)

# Reconstruction metrics
if all_metrics:
    metrics_df = pd.DataFrame(all_metrics)
    metrics_df.to_csv(RESULTS_DIR / "reconstruction_metrics.csv", index=False)
    ts_all = pd.concat(all_timeseries, ignore_index=True)
    ts_all.to_csv(RESULTS_DIR / "reconstruction_timeseries.csv", index=False)
    print(f"Saved: {RESULTS_DIR / 'reconstruction_metrics.csv'}")
    print(f"Saved: {RESULTS_DIR / 'reconstruction_timeseries.csv'}  ({len(ts_all)} rows)")

# Comparison: free vs fixed vs bounded R²
comp_rows = []
for _, row in results_df.iterrows():
    comp_rows.append(dict(layer=row["layer"],
        r2_fixed=row["r2_fixed"], r2_bounded=row["r2_bounded"], r2_free=row["r2_free"],
        ske_phys=row["S_ke_phys"], skv_phys=row["S_kv_phys"],
        ske_free=row["ske_free"], skv_free=row["skv_free"],
        tau_fixed=row["tau_fixed"], tau_free=row["tau_free"]))
comp_df = pd.DataFrame(comp_rows)
comp_df.to_csv(RESULTS_DIR / "comparison.csv", index=False)
print(f"Saved: {RESULTS_DIR / 'comparison.csv'}")

# ══════════════════════════════════════════════════════════════════════════════
# 5. Plots
# ══════════════════════════════════════════════════════════════════════════════

# ── Per-layer 3-panel reconstruction ─────────────────────────────────────────
for layer in LAYERS_ORDERED:
    if layer not in raw_data_store:
        continue

    d        = raw_data_store[layer]
    color    = COLORS[layer]
    tau_opt  = int(d["tau_opt_free"])
    wellcode = str(d["wellcode"])
    h_c      = float(d["h_c"])
    span_m   = float(d["span_m"])

    # Get metrics
    met = None
    for m in all_metrics:
        if m["layer"] == layer:
            met = m; break

    ts_layer = ts_all[ts_all["layer"] == layer].copy()
    ts_layer["date"] = pd.to_datetime(ts_layer["date"])
    ts_layer = ts_layer[(ts_layer["date"] >= T_START) & (ts_layer["date"] < T_END)]

    dates_cum = pd.to_datetime(d["dates"])
    head_m    = d["head_m"]
    mlcw_mm   = d["mlcw_mm"]

    fig, axes = plt.subplots(3, 1, figsize=(A4_PORTRAIT[0], 10.0))
    fig.suptitle(
        f"TUKU  |  Layer {layer}  |  span={span_m:.1f}m  |  GWL well {wellcode}\n"
        f"Physical Ss: S_ske={SS_LOOKUP[layer]['s_ske']:.2e}  "
        f"S_skv={SS_LOOKUP[layer]['s_skv']:.2e}  (1/m)  |  "
        f"tau_opt={tau_opt*5}d  |  h_c={h_c:.2f}m",
        fontsize=FONT["suptitle"], fontweight="bold", y=0.97)

    # Panel 1: Cumulative MLCW + head with regime shading
    ax1 = axes[0]
    mask = (dates_cum >= T_START) & (dates_cum < T_END)
    ax1.plot(dates_cum[mask], mlcw_mm[mask], color=color, linewidth=LW["data"],
             label=f"MLCW cumulative (span={span_m:.1f}m)")
    ax1.set_ylabel("MLCW (mm)", fontsize=FONT["axis_label"], color=color)
    ax1.set_xlim(T_START, T_END)
    ax1.legend(fontsize=FONT["legend"], loc="upper left")
    ax1.set_title("Panel 1 — Cumulative MLCW compaction (non-detrended)",
                  fontsize=FONT["title"], fontweight="bold")
    style_ax(ax1)
    ax1.grid(True, alpha=0.3)

    # Panel 2: Incremental with predictions
    ax2 = axes[1]
    if ts_layer is not None and met is not None:
        ax2.plot(ts_layer["date"], ts_layer["db_obs_mm_epoch"], color="grey",
                 linewidth=LW["data"], alpha=0.7, label="Observed")
        ax2.plot(ts_layer["date"], ts_layer["db_pred_mm_epoch"], color=color,
                 linewidth=LW["data"], alpha=0.9, label="Predicted (free S)")
        ax2.axhline(0, color="black", linewidth=LW["grid"], linestyle="-")
        ax2.set_xlim(T_START, T_END)
        ax2.legend(fontsize=FONT["legend"], loc="upper right")
        ax2.set_title(
            f"Panel 2 — Incremental  |  S_ke={met['S_ke']:.4f}  S_kv={met['S_kv']:.4f}  "
            f"tau={tau_opt*5}d  |  R²={met['R2']:.3f}  RMSE={met['RMSE']:.4f}",
            fontsize=FONT["title"], color=color, fontweight="bold")
    ax2.set_ylabel("db (mm/epoch)", fontsize=FONT["axis_label"])
    style_ax(ax2)
    ax2.grid(True, alpha=0.3)

    # Panel 3: Cumulative reconstruction
    ax3 = axes[2]
    if ts_layer is not None:
        ax3.plot(ts_layer["date"], ts_layer["cum_obs_mm"], color="grey",
                 linewidth=LW["data"], alpha=0.8, label="Observed cumulative")
        ax3.plot(ts_layer["date"], ts_layer["cum_pred_mm"], color=color,
                 linewidth=LW["data"], alpha=0.9, label="Predicted cumulative")
        ax3.set_xlim(T_START, T_END)
        ax3.legend(fontsize=FONT["legend"], loc="upper left")
        phys_ske = SS_LOOKUP[layer]["s_ske"] * span_m * 1000
        phys_skv = SS_LOOKUP[layer]["s_skv"] * span_m * 1000
        ax3.set_title(
            f"Panel 3 — Cumulative  |  Physical ref: S_ke={phys_ske:.2f}  "
            f"S_kv={phys_skv:.2f}  mm/m",
            fontsize=FONT["title"], color=color, fontweight="bold")
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

# ── MSE curves: 3-panel comparison (one figure) ──────────────────────────────
fig, axes = plt.subplots(2, 3, figsize=(A4_PORTRAIT[0], 6.5))
fig.suptitle("TUKU — MSE curves: FIXED vs BOUNDED vs FREE S",
             fontsize=FONT["suptitle"], fontweight="bold", y=0.98)
axes_flat = axes.flatten()

for i, layer in enumerate(LAYERS_ORDERED):
    ax = axes_flat[i]
    if layer not in mse_curves_free:
        ax.set_visible(False); continue

    taus = np.array(tau_index)
    mse_f = np.array(mse_curves_fixed[layer])
    mse_b = np.array(mse_curves_bounded[layer])
    mse_r = np.array(mse_curves_free[layer])
    fin = np.isfinite(mse_f)
    bin_ = np.isfinite(mse_b)
    rin = np.isfinite(mse_r)

    ax.plot(taus[fin], mse_f[fin], color="red", linewidth=LW["data"], alpha=0.8, label="FIXED Ss")
    ax.plot(taus[bin_], mse_b[bin_], color="orange", linewidth=LW["data"], alpha=0.8, label="BOUNDED")
    ax.plot(taus[rin], mse_r[rin], color=COLORS[layer], linewidth=LW["data"], label="FREE")

    # Mark optima
    row = results_df[results_df["layer"] == layer].iloc[0]
    for tau_val, clr, lbl in [(row["tau_fixed"], "red", "fix"),
                               (row["tau_bounded"], "orange", "bnd"),
                               (row["tau_free"], COLORS[layer], "free")]:
        ax.axvline(tau_val, color=clr, linestyle="--", linewidth=LW["reference"], alpha=0.6)

    ax.set_title(f"Layer {layer}  (span={SS_LOOKUP[layer]['span_m']:.1f}m)",
                 fontsize=FONT["title"], color=COLORS[layer], fontweight="bold")
    ax.set_xlabel("tau (epochs)", fontsize=FONT["axis_label"])
    ax.set_ylabel("MSE [mm²/epoch²]", fontsize=FONT["axis_label"])
    ax.legend(fontsize=FONT["legend"]-1, loc="upper right")
    ax.grid(True, alpha=0.3)
    style_ax(ax)

fig.subplots_adjust(left=0.08, right=0.97, bottom=0.10, top=0.88, hspace=0.40, wspace=0.30)
out_path = PLOTS_DIR / "tau_mse_curves_all_layers.png"
fig.savefig(out_path, dpi=DPI, pad_inches=0.15)
plt.close(fig)
print(f"Saved: {out_path}")

print("\nDone. Compare results_physical_ss/ against results_detrended_filtered/")
