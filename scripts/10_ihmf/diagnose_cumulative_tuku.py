"""
diagnose_cumulative_tuku.py — Reconstruct cumulative predictions from
TUKU_gps_v3_results.json and generate per-layer timeseries + diagnostic plots.

Reproduces the exact step1_mask and common-window data path used by
joint_solve_cumulative in fit_ihm_f_v3.py.

Output: results/ihmf/v3/diagnostics/
"""

import json, sys, warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ihmf_model_v3 import compute_virgin_term, compute_r2_cumulative

warnings.filterwarnings("ignore", category=UserWarning)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# ── Config ──────────────────────────────────────────────────────────────────
RESULT_JSON = ROOT / "results" / "ihmf" / "v3" / "TUKU_gps_v3_results.json"
TAU_DEMO    = ROOT / "tau_demo_TUKU" / "data"
INC_DIR     = TAU_DEMO / "incremental_data"
OUT_DIR     = ROOT / "results" / "ihmf" / "v3" / "diagnostics"
REF_DATE    = pd.Timestamp("2015-01-16")

WELL_CONFIG = [
    ("F1", "HONGLUN_gwl_timeseries.feather", "09050111"),
    ("T1", "HONGLUN_gwl_timeseries.feather", "09050111"),
    ("F2", "TUKU_gwl_timeseries.feather",   "09050321"),
    ("T2", "LUNZI_gwl_timeseries.feather",   "09170121"),
    ("F3", "TUKU_gwl_timeseries.feather",   "09050331"),
    ("F4", "LIUZHUANG_gwl_timeseries.feather", "09080251"),
]

OUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    # ── 1. Load result ─────────────────────────────────────────────────────
    with open(RESULT_JSON) as f:
        res = json.load(f)

    # ── 2. Load MLCW master (exactly as load_all_layers_gps) ────────────────
    mlcw_inc = pd.read_feather(INC_DIR / "mlcw_diff_cleaned.feather")
    mlcw_inc["datetime"] = pd.to_datetime(mlcw_inc["datetime"]).astype("datetime64[ns]")
    mlcw_inc = mlcw_inc.sort_values("datetime").reset_index(drop=True)
    for col in [c for c in mlcw_inc.columns if c != "datetime"]:
        mlcw_inc[f"_cum_{col}"] = mlcw_inc[col].fillna(0.0).cumsum()
    master = pd.DataFrame({"datetime": mlcw_inc["datetime"].copy()})

    # GPS
    gps_raw = pd.read_feather(TAU_DEMO / "TUKU_GPS_timeseries.feather")
    gps_raw.rename(columns={gps_raw.columns[0]: "datetime"}, inplace=True)
    gps_raw["datetime"] = pd.to_datetime(gps_raw["datetime"]).astype("datetime64[ns]")
    gps_raw = gps_raw[["datetime", "modeled"]].sort_values("datetime").reset_index(drop=True)
    gps_aligned = pd.merge_asof(master, gps_raw, on="datetime",
                                 direction="nearest", tolerance=pd.Timedelta("3D"))

    # ── 3. Build per-layer head & mlcw arrays (R1/R2: zero-reference head + h_c) ──
    head_arrays = {}       # zero-referenced head (m)
    b_cum_arrays = {}      # cumulative MLCW (mm)
    h_c_zeroed_dict = {}   # zero-referenced preconsolidation head (m)

    for layer, fname, wellcode in WELL_CONFIG:
        gwl = pd.read_feather(TAU_DEMO / fname)
        gwl["datetime"] = pd.to_datetime(gwl["datetime"]).astype("datetime64[ns]")
        gwl = gwl[["datetime", wellcode]].dropna(subset=[wellcode])
        gwl = gwl.sort_values("datetime").reset_index(drop=True)

        # Zero-reference: compute ref_val = last raw head on/before REF_DATE
        # (mirrors load_all_layers_gps R1 fix)
        gwl_indexed = gwl.set_index("datetime")[wellcode]
        avail = gwl_indexed.dropna()
        pre_ref = avail.index[avail.index <= REF_DATE]
        if len(pre_ref) == 0:
            raise ValueError(f"No GWL data on/before REF_DATE for {wellcode} ({fname})")
        ref_val = float(avail.loc[pre_ref[-1]])

        # h_c: lowest absolute head before REF_DATE, then shift to zero-ref frame
        pre_ref_vals = gwl[gwl["datetime"] < REF_DATE][wellcode].dropna()
        if len(pre_ref_vals) >= 10:
            h_c_abs = float(pre_ref_vals.min())
        else:
            h_c_abs = float(gwl[wellcode].dropna().min())
            print(f"  WARN: <10 pre-REF_DATE points for {wellcode} layer {layer} — h_c fallback")
        h_c_zeroed = h_c_abs - ref_val

        gwl_aligned = pd.merge_asof(master, gwl, on="datetime",
                                     direction="nearest", tolerance=pd.Timedelta("3D"))
        head_abs_aligned = gwl_aligned[wellcode].values.astype(float)
        head_arrays[layer] = head_abs_aligned - ref_val   # zero-reference
        b_cum_arrays[layer] = mlcw_inc[f"_cum_{layer}"].values.astype(float)
        h_c_zeroed_dict[layer] = h_c_zeroed

    # ── 4. Apply step1_mask (GWL + MLCW only — EXACT same as load_all_layers_gps) ──
    T_full = len(master)
    step1_mask = np.ones(T_full, dtype=bool)
    for layer, _, _ in WELL_CONFIG:
        step1_mask &= ~np.isnan(head_arrays[layer])
        step1_mask &= ~np.isnan(b_cum_arrays[layer])

    print(f"step1_mask: {step1_mask.sum()} of {T_full} epochs kept "
          f"({int((~step1_mask).sum())} dropped)")

    # Filter all arrays
    dates_full = master["datetime"].values
    dates_filt = dates_full[step1_mask]
    for layer in dict(head_arrays):
        head_arrays[layer] = head_arrays[layer][step1_mask]
        b_cum_arrays[layer] = b_cum_arrays[layer][step1_mask]

    T_filt = len(dates_filt)

    # ── 5. Build common window (exact same as fit_ihm_f_v3.py) ──────────────
    tau_dict = {lyr: res["layers"][lyr]["tau_opt"] for lyr in res["layers"]}
    tau_max_all = max(tau_dict.values())
    win_start = tau_max_all
    win_len   = T_filt - win_start

    print(f"tau_max_all={tau_max_all}, win_start={win_start}, win_len={win_len}")

    # ── 6. Build per-layer H_lagged, b_cum, V on common window ─────────────
    # R1/R2: Head is zero-referenced to REF_DATE. V = min(0, cummin(H) - h_c)
    # uses zero-referenced values for both — datum cancels, V is invariant.
    common_data = {}
    for layer, _, _ in WELL_CONFIG:
        tau = tau_dict[layer]
        offset = tau_max_all - tau
        H_lag = head_arrays[layer][offset : offset + win_len]
        b_win = b_cum_arrays[layer][win_start : win_start + win_len]
        dates = dates_filt[win_start : win_start + win_len]
        V = compute_virgin_term(H_lag, h_c_zeroed_dict[layer])
        common_data[layer] = (H_lag, b_win, V, dates)

    # ── 7. Generate per-layer outputs ──────────────────────────────────────
    summary_rows = []
    for layer, _, _ in WELL_CONFIG:
        H_lag, b_obs_raw, V, dates = common_data[layer]
        p = res["layers"][layer]
        S_ke = p["S_ke"]
        S_kv = p["S_kv"]
        delta = S_kv - S_ke
        c_j  = p.get("c_intercept", 0.0)  # per-layer intercept (R1 fix)

        # Reconstruct prediction using zero-referenced head + intercept
        # (matches joint_solve_cumulative post-R1/R2)
        b_pred_raw = c_j + S_ke * H_lag + delta * V

        # Zero-reference both to the first OBSERVED epoch so the plot starts at 0.
        # Use the SAME reference for both to preserve residuals and R².
        ref_val = b_obs_raw[0]
        b_obs  = b_obs_raw - ref_val
        b_pred = b_pred_raw - ref_val
        regime = np.where(V < 0, "inelastic", "elastic")
        residual = b_obs - b_pred
        r2_layer = compute_r2_cumulative(b_obs, b_pred)
        rmse = float(np.sqrt(np.mean((b_obs - b_pred) ** 2)))

        # ── Timeseries CSV ──
        ts_df = pd.DataFrame({
            "datetime":     pd.to_datetime(dates),
            "observed_mm":  b_obs,
            "predicted_mm": b_pred,
            "residual_mm":  residual,
            "regime":       regime,
            "head_m":       H_lag,
            "V_m":          V,
        })
        csv_path = OUT_DIR / f"TUKU_{layer}_cumulative_timeseries.csv"
        ts_df.to_csv(csv_path, index=False, float_format="%.4f")
        print(f"  CSV:  {csv_path.name}  ({len(ts_df)} rows)")

        # ── Diagnostic plot ──
        _make_plot(layer, dates, b_obs, b_pred, V, H_lag, S_ke, S_kv, r2_layer)

        summary_rows.append({
            "layer": layer,
            "S_ke_mmpm":    round(S_ke, 6),
            "S_kv_mmpm":    round(S_kv, 6),
            "delta_mmpm":   round(delta, 6),
            "tau_epochs":   p["tau_opt"],
            "n_elastic":    int((V == 0).sum()),
            "n_inelastic":  int((V < 0).sum()),
            "R2_cum":       round(r2_layer, 6),
            "RMSE_cum_mm":  round(rmse, 4),
            "obs_range_mm": round(float(b_obs.max() - b_obs.min()), 3),
            "pred_range_mm": round(float(b_pred.max() - b_pred.min()), 3),
        })

    # ── Summary CSV ──
    sum_df = pd.DataFrame(summary_rows)
    sum_csv = OUT_DIR / "TUKU_cumulative_summary.csv"
    sum_df.to_csv(sum_csv, index=False, float_format="%.6f")
    print(f"\n  Summary: {sum_csv.name}")
    print(sum_df.to_string(index=False))

    # ── Aggregate timeseries (all layers summed, with intercept) ──
    agg_obs = None; agg_pred = None; agg_dates = None
    for layer, _, _ in WELL_CONFIG:
        H_lag, b_obs, V, dates = common_data[layer]
        p = res["layers"][layer]
        c_j = p.get("c_intercept", 0.0)
        b_pred = c_j + p["S_ke"] * H_lag + (p["S_kv"] - p["S_ke"]) * V
        if agg_obs is None:
            agg_dates = dates; agg_obs = b_obs.copy(); agg_pred = b_pred.copy()
        else:
            n = min(len(agg_obs), len(b_obs))
            agg_obs[:n] += b_obs[:n]; agg_pred[:n] += b_pred[:n]

    agg_df = pd.DataFrame({
        "datetime": pd.to_datetime(agg_dates[:len(agg_obs)]),
        "observed_mm": agg_obs, "predicted_mm": agg_pred,
        "residual_mm": agg_obs - agg_pred,
    })
    agg_path = OUT_DIR / "TUKU_aggregate_cumulative_timeseries.csv"
    agg_df.to_csv(agg_path, index=False, float_format="%.4f")
    agg_r2 = compute_r2_cumulative(agg_obs, agg_pred)
    print(f"\n  Aggregate: {agg_path.name}  |  R² = {agg_r2:.4f}")


def _make_plot(layer, dates, b_obs, b_pred, V, H_lag, S_ke, S_kv, r2):
    dates_dt = pd.to_datetime(dates)
    inel = V < 0
    n_inel = int(inel.sum())

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 7.5), sharex=True)

    # ── Top: cumulative compaction ──
    ax1.plot(dates_dt, b_obs,  "-", color="black", lw=1.0, alpha=0.85, label="Observed MLCW")
    ax1.plot(dates_dt, b_pred, "-", color="#d62728", lw=1.4, label=f"Predicted (R²={r2:.3f})")
    if inel.any():
        ch = np.diff(np.concatenate([[False], inel, [False]]).astype(int))
        for s, e in zip(np.where(ch == 1)[0], np.where(ch == -1)[0]):
            ax1.axvspan(dates_dt[s], dates_dt[min(e, len(dates_dt)-1)],
                        alpha=0.07, color="red")
    ax1.legend(handles=ax1.get_legend_handles_labels()[0] +
               [Patch(color="red", alpha=0.12, label=f"Inelastic (V<0, n={n_inel})")],
               loc="upper left", fontsize=8)
    ax1.set_ylabel("Cumulative compaction [mm]")
    ax1.set_title(f"TUKU — {layer}  |  $S_{{ke}}$={S_ke:.3f}  $S_{{kv}}$={S_kv:.3f}  "
                  f"$R^2$={r2:.3f}", fontsize=11)
    ax1.axhline(0, color="gray", lw=0.5, ls="--")
    ax1.grid(True, alpha=0.3)

    # ── Bottom: cumulative head + V ──
    ax2.plot(dates_dt, H_lag, "-", color="#1f77b4", lw=0.8, label="$H(t-\\tau)$ cumulative head [m]")
    ax2.axhline(0, color="gray", lw=0.5, ls="--")
    ax2.fill_between(dates_dt, 0, V, color="red", alpha=0.10, label="$V(t)$ inelastic exceedance")
    ax2.set_ylabel("Head / V [m]")
    ax2.set_xlabel("Date")
    ax2.legend(loc="upper left", fontsize=8)
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(OUT_DIR / f"TUKU_{layer}_cumulative_fit.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  Plot: TUKU_{layer}_cumulative_fit.png")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Cumulative diagnostics from IHM-F v3 results")
    parser.add_argument("--result-json", type=str, default=None,
                        help="Path to result JSON (default: results/ihmf/v3/TUKU_gps_v3_results.json)")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Output directory for CSVs and PNGs (default: results/ihmf/v3/diagnostics/)")
    args = parser.parse_args()

    if args.result_json:
        RESULT_JSON = Path(args.result_json)  # noqa: overwrites module-level default
    if args.output_dir:
        OUT_DIR = Path(args.output_dir)        # noqa: overwrites module-level default
        OUT_DIR.mkdir(parents=True, exist_ok=True)

    main()
