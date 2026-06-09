"""
14_carrier_reconstruction_tuku.py — GPS-carrier gap-fill reconstruction at TUKU.

Part 1 Phase 1.1 of super_plan_2026-06-09.md. Decision Point 1 verdict: CARRIER-PRIMARY.

Physical model:
    b_k(t) = a_k * d_surface(t) + c_k        a_k >= 0

    b_k      — cumulative compaction of layer k (mm)
    d_surface — GPS vertical displacement (mm, cumulative from REF_DATE)
    a_k      — apportionment share of surface motion (dimensionless)
    c_k      — per-layer intercept (mm)

If sum(a_k) exceeds 1, shares are jointly rescaled to sum <= 1 (the layers
cannot account for more than 100% of the surface displacement).

Outputs:
    results/reconstruction/TUKU_{layer}_reconstruction.csv  — per-layer timeseries
    tau_demo_TUKU/plots/reconstruction/TUKU_reconstruction_6layer.png  — figure

Usage:
    PYTHONPATH="" conda run -n isce_ncu3 python tau_demo_TUKU/14_carrier_reconstruction_tuku.py
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import lsq_linear

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "10_ihmf"))
from ihmf_model_v3 import compute_r2_cumulative

warnings.filterwarnings("ignore", category=UserWarning)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ── Config ──────────────────────────────────────────────────────────────────────
RESULT_JSON = ROOT / "results" / "ihmf" / "v3" / "verification_20260609_intercept" / "TUKU_gps_v3_results.json"
TAU_DEMO    = ROOT / "tau_demo_TUKU" / "data"
INC_DIR     = TAU_DEMO / "incremental_data"
OUT_DIR     = ROOT / "results" / "reconstruction"
PLOT_DIR    = ROOT / "tau_demo_TUKU" / "plots" / "reconstruction"
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
PLOT_DIR.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════════════
# Data loading — same pattern as 13_holdout_method_bakeoff.py
# ═══════════════════════════════════════════════════════════════════════════════════

def load_data(gwl_layers: set | None = None) -> dict:
    """Load MLCW + GPS + GWL data for TUKU, aligned to common 5-day grid.

    Parameters
    ----------
    gwl_layers : set or None
        Layers for which tau-lagged zero-referenced GWL (u) should be computed.
        Only needed when --use-gwl is specified.

    Returns dict with keys:
        master_dates   : pd.DatetimeIndex, full timeline
        d_surface      : 1-D float array, GPS vertical displacement (mm)
        layers         : dict[layer -> dict(b_cum, H_abs, h_c_abs, tau_opt, u_lagged)]
    """
    if gwl_layers is None:
        gwl_layers = set()
    # Load production tau values
    with open(RESULT_JSON) as f:
        prod = json.load(f)
    tau_dict = {lyr: prod["layers"][lyr]["tau_opt"] for lyr in prod["layers"]}

    # MLCW master timeline (incremental → cumulative)
    mlcw_inc = pd.read_feather(INC_DIR / "mlcw_diff_cleaned.feather")
    mlcw_inc["datetime"] = pd.to_datetime(mlcw_inc["datetime"]).astype("datetime64[ns]")
    mlcw_inc = mlcw_inc.sort_values("datetime").reset_index(drop=True)
    for col in [c for c in mlcw_inc.columns if c != "datetime"]:
        mlcw_inc[f"_cum_{col}"] = mlcw_inc[col].fillna(0.0).cumsum()

    master_dates = mlcw_inc["datetime"].values.copy()
    T_full = len(master_dates)

    # GPS surface displacement
    gps_raw = pd.read_feather(TAU_DEMO / "TUKU_GPS_timeseries.feather")
    gps_raw.rename(columns={gps_raw.columns[0]: "datetime"}, inplace=True)
    gps_raw["datetime"] = pd.to_datetime(gps_raw["datetime"]).astype("datetime64[ns]")
    gps_raw = gps_raw[["datetime", "modeled"]].sort_values("datetime").reset_index(drop=True)
    gps_aligned = pd.merge_asof(
        pd.DataFrame({"datetime": master_dates}), gps_raw,
        on="datetime", direction="nearest", tolerance=pd.Timedelta("3D")
    )
    d_surface_full = gps_aligned["modeled"].values.astype(float)

    # Per-layer MLCW + GWL
    master = pd.DataFrame({"datetime": master_dates})
    layers: dict[str, dict] = {}

    for layer, fname, wellcode in WELL_CONFIG:
        # GWL (for reference, not used in carrier fit)
        gwl = pd.read_feather(TAU_DEMO / fname)
        gwl["datetime"] = pd.to_datetime(gwl["datetime"]).astype("datetime64[ns]")
        gwl = gwl[["datetime", wellcode]].dropna(subset=[wellcode])
        gwl = gwl.sort_values("datetime").reset_index(drop=True)

        gwl_indexed = gwl.set_index("datetime")[wellcode]
        avail = gwl_indexed.dropna()
        pre_ref = avail.index[avail.index <= REF_DATE]
        ref_val = float(avail.loc[pre_ref[-1]]) if len(pre_ref) > 0 else float(avail.iloc[0])

        pre_ref_vals = gwl[gwl["datetime"] < REF_DATE][wellcode].dropna()
        h_c_abs = float(pre_ref_vals.min()) if len(pre_ref_vals) >= 10 else float(gwl[wellcode].dropna().min())

        gwl_aligned = pd.merge_asof(master, gwl, on="datetime",
                                     direction="nearest", tolerance=pd.Timedelta("3D"))
        H_abs = gwl_aligned[wellcode].values.astype(float)

        # Cumulative MLCW
        b_cum = mlcw_inc[f"_cum_{layer}"].values.astype(float)

        # Tau-lagged, zero-referenced GWL for carrier+GWL model
        u_lagged = None
        if layer in gwl_layers:
            tau = tau_dict.get(layer, 0)
            u_raw = H_abs - ref_val  # zero-reference
            # Lag: u(t-τ), so first τ epochs become NaN
            u_lagged_arr = np.full(T_full, np.nan)
            u_lagged_arr[tau:] = u_raw[:T_full - tau]
            u_lagged = u_lagged_arr

        layers[layer] = {
            "b_cum":    b_cum,
            "H_abs":    H_abs,
            "h_c_abs":  h_c_abs,
            "H_ref":    ref_val,
            "tau_opt":  tau_dict.get(layer, 0),
            "u_lagged": u_lagged,
        }

    return {
        "master_dates": master_dates,
        "d_surface":    d_surface_full,
        "layers":       layers,
    }


# ═══════════════════════════════════════════════════════════════════════════════════
# Carrier fit + reconstruction
# ═══════════════════════════════════════════════════════════════════════════════════

def fit_carrier_per_layer(data: dict, gwl_layers: set | None = None) -> dict:
    """Fit b_k = a_k * d_surface + c_k (or + d_k * u for GWL layers).

    For layers in gwl_layers, fits the 3-parameter model:
        b_k = a_k * d_GPS + d_k * u + c_k    (a >= 0, d >= 0)

    Returns dict with keys: a_k, c_k, d_k, r2_cal, rmse_cal, bias, b_pred.
    """
    if gwl_layers is None:
        gwl_layers = set()

    master_dates = data["master_dates"]
    d_surface = data["d_surface"]
    layers = data["layers"]

    results = {}
    for layer in layers:
        b_cum = layers[layer]["b_cum"]
        u_lagged = layers[layer].get("u_lagged")

        use_gwl = layer in gwl_layers and u_lagged is not None

        if use_gwl:
            valid = np.isfinite(b_cum) & np.isfinite(d_surface) & np.isfinite(u_lagged)
        else:
            valid = np.isfinite(b_cum) & np.isfinite(d_surface)
        n_valid = valid.sum()

        if n_valid < 10:
            print(f"  {layer}: SKIP — only {n_valid} valid epochs")
            results[layer] = {"a_k": 0.0, "c_k": 0.0, "d_k": 0.0,
                              "r2_cal": float("nan"), "rmse_cal": float("nan"),
                              "bias": float("nan"), "b_pred": np.full_like(b_cum, np.nan)}
            continue

        b_valid = b_cum[valid]
        d_valid = d_surface[valid]

        # Zero-reference to first valid epoch
        b_ref = b_valid[0]
        d_ref = d_valid[0]
        b_zr = b_valid - b_ref
        d_zr = d_valid - d_ref

        if use_gwl:
            u_valid = u_lagged[valid]
            u_ref = u_valid[0]
            u_zr = u_valid - u_ref

            # Joint fit: b_zr = a * d_zr + d * u_zr + c'  with a >= 0, d >= 0
            A = np.column_stack([d_zr, u_zr, np.ones_like(d_zr)])
            bounds = (np.array([0, 0, -np.inf]), np.array([np.inf, np.inf, np.inf]))
            res = lsq_linear(A, b_zr, bounds=bounds)
            a_k = float(res.x[0])
            d_k = float(res.x[1])
            c_prime = float(res.x[2])
            c_k = c_prime + b_ref - a_k * d_ref - d_k * u_ref

            # Full prediction
            b_pred_full = np.full_like(b_cum, np.nan)
            pred_mask = np.isfinite(d_surface) & np.isfinite(u_lagged)
            b_pred_full[pred_mask] = a_k * d_surface[pred_mask] + d_k * u_lagged[pred_mask] + c_k

            model_str = f"a={a_k:.5f}  d={d_k:.5f}  c={c_k:.2f}"
        else:
            d_k = 0.0

            # Fit: b_zr = a * d_zr + c'  with a >= 0
            A = np.column_stack([d_zr, np.ones_like(d_zr)])
            res = lsq_linear(A, b_zr, bounds=(np.array([0, -np.inf]), np.array([np.inf, np.inf])))
            a_k = float(res.x[0])
            c_prime = float(res.x[1])
            c_k = c_prime + b_ref - a_k * d_ref

            # Full prediction
            b_pred_full = np.full_like(b_cum, np.nan)
            pred_mask = np.isfinite(d_surface)
            b_pred_full[pred_mask] = a_k * d_surface[pred_mask] + c_k

            model_str = f"a={a_k:.5f}  c={c_k:.2f}"

        # Metrics on calibration epochs
        r2_cal = compute_r2_cumulative(b_valid, b_pred_full[valid])
        rmse_cal = float(np.sqrt(np.mean((b_valid - b_pred_full[valid]) ** 2)))
        bias = float(np.mean(b_pred_full[valid] - b_valid))

        # Gap-fill epochs: GPS available but MLCW not
        gps_valid = np.isfinite(d_surface) if not use_gwl else (np.isfinite(d_surface) & np.isfinite(u_lagged))
        n_filled = int((gps_valid & ~valid).sum())

        results[layer] = {
            "a_k": a_k, "d_k": d_k, "c_k": c_k,
            "r2_cal": r2_cal, "rmse_cal": rmse_cal, "bias": bias,
            "b_pred": b_pred_full,
            "n_calib": n_valid, "n_gap_filled": n_filled,
        }
        gwl_note = f"  d={d_k:.5f}" if use_gwl else ""
        print(f"  {layer}: {model_str} mm  R²={r2_cal:.4f}  "
              f"RMSE={rmse_cal:.2f} mm  bias={bias:+.2f} mm  "
              f"n_calib={n_valid}  n_filled={n_filled}{gwl_note}")

    return results


def joint_rescale(results: dict, data: dict) -> dict:
    """If sum(a_k) > 1, rescale shares to sum <= 1 and re-fit intercepts.

    The layers cannot explain more than 100% of the surface displacement.
    Rescaling preserves relative apportionment shares.
    """
    a_sum = sum(r["a_k"] for r in results.values())
    if a_sum <= 1.0 + 1e-10:
        print(f"\n  sum(a_k) = {a_sum:.4f} <= 1 — no rescaling needed")
        return results

    print(f"\n  ⚠ sum(a_k) = {a_sum:.4f} > 1 — rescaling to sum <= 1")
    scale = 1.0 / a_sum
    for layer in results:
        results[layer]["a_k"] *= scale
        # Re-fit intercept with fixed a_k
        b_cum = data["layers"][layer]["b_cum"]
        d_surface = data["d_surface"]
        valid = np.isfinite(b_cum) & np.isfinite(d_surface)
        if valid.sum() < 2:
            continue
        a_k = results[layer]["a_k"]
        # c_k = mean(b - a*d) on valid epochs
        c_k = float(np.mean(b_cum[valid] - a_k * d_surface[valid]))
        results[layer]["c_k"] = c_k
        # Recompute prediction
        b_pred = np.full_like(b_cum, np.nan)
        gps_valid = np.isfinite(d_surface)
        b_pred[gps_valid] = a_k * d_surface[gps_valid] + c_k
        results[layer]["b_pred"] = b_pred
        # Recompute metrics
        r2 = compute_r2_cumulative(b_cum[valid], b_pred[valid])
        rmse = float(np.sqrt(np.mean((b_cum[valid] - b_pred[valid]) ** 2)))
        results[layer]["r2_cal"] = r2
        results[layer]["rmse_cal"] = rmse
        print(f"  {layer}: a={a_k:.5f} (rescaled)  c={c_k:.2f} mm  R²={r2:.4f}")

    new_sum = sum(r["a_k"] for r in results.values())
    print(f"  Rescaled sum(a_k) = {new_sum:.4f}")
    return results


# ═══════════════════════════════════════════════════════════════════════════════════
# Output CSVs + Plot
# ═══════════════════════════════════════════════════════════════════════════════════

def write_csvs(data: dict, results: dict):
    """Write per-layer reconstruction CSVs."""
    master_dates = pd.to_datetime(data["master_dates"])
    d_surface = data["d_surface"]

    for layer in data["layers"]:
        r = results[layer]
        b_obs = data["layers"][layer]["b_cum"]
        b_pred = r["b_pred"]

        df_dict = {
            "date": master_dates,
            "b_model_mm":    np.round(b_pred, 4),
            "b_observed_mm": np.round(b_obs, 4),
            "d_surface_mm":  np.round(d_surface, 4),
            "a_k":           round(r["a_k"], 6),
            "c_k":           round(r["c_k"], 4),
        }
        if r.get("d_k", 0) != 0:
            df_dict["d_k"] = round(r["d_k"], 6)
        df = pd.DataFrame(df_dict)

        # Mark gap epochs
        df["is_gap"] = np.isnan(b_obs) & np.isfinite(b_pred)
        df["is_model_only"] = np.isnan(b_obs)

        csv_path = OUT_DIR / f"TUKU_{layer}_reconstruction.csv"
        df.to_csv(csv_path, index=False, float_format="%.4f")
        print(f"  CSV: {csv_path.name}  ({len(df)} rows, "
              f"{df['is_gap'].sum()} gap-filled)")


def make_figure(data: dict, results: dict):
    """6-panel reconstruction figure."""
    master_dates = pd.to_datetime(data["master_dates"])
    layers_order = ["F1", "T1", "F2", "T2", "F3", "F4"]
    layer_titles = {
        "F1": "F1 — Aquifer 1 (0–42 m)",
        "T1": "T1 — Aquitard 1 (42–51 m)",
        "F2": "F2 — Aquifer 2 (51–157 m)",
        "T2": "T2 — Aquitard 2 (157–173 m)",
        "F3": "F3 — Aquifer 3 (173–283 m)",
        "F4": "F4 — Aquifer 4 (283–300 m, silt/mud)",
    }
    colors = plt.cm.tab10.colors

    fig, axes = plt.subplots(3, 2, figsize=(16, 18))
    axes = axes.flatten()

    for i, layer in enumerate(layers_order):
        ax = axes[i]
        r = results[layer]
        b_obs = data["layers"][layer]["b_cum"]
        b_pred = r["b_pred"]

        # Observed (dots)
        obs_mask = np.isfinite(b_obs)
        ax.scatter(master_dates[obs_mask], b_obs[obs_mask],
                   s=8, color="black", alpha=0.5, label="Observed MLCW", zorder=3)

        # Modeled (line)
        pred_mask = np.isfinite(b_pred)
        ax.plot(master_dates[pred_mask], b_pred[pred_mask],
                "-", color=colors[i % 10], lw=1.5, alpha=0.9,
                label=f"Carrier model (R²={r['r2_cal']:.3f})", zorder=2)

        # Gap shading (where model fills missing MLCW)
        gap_mask = np.isnan(b_obs) & np.isfinite(b_pred)
        if gap_mask.any():
            ch = np.diff(np.concatenate([[False], gap_mask, [False]]).astype(int))
            for s, e in zip(np.where(ch == 1)[0], np.where(ch == -1)[0]):
                ax.axvspan(master_dates[s], master_dates[min(e, len(master_dates)-1)],
                           alpha=0.15, color="orange", label="_nolegend_")
            # Add one legend entry
            from matplotlib.patches import Patch
            ax.legend(handles=ax.get_legend_handles_labels()[0] +
                      [Patch(color="orange", alpha=0.15, label=f"Gap-filled ({gap_mask.sum()} epochs)")],
                      loc="upper left", fontsize=9)

        ax.set_ylabel("Cumulative compaction [mm]", fontsize=12)
        ax.set_title(f"{layer}: {layer_titles.get(layer, layer)}  |  "
                     f"$a_k$={r['a_k']:.4f}  $R^2$={r['r2_cal']:.3f}  "
                     f"RMSE={r['rmse_cal']:.2f} mm", fontsize=11)
        ax.axhline(0, color="gray", lw=0.5, ls="--")
        ax.grid(True, alpha=0.3)
        ax.tick_params(labelsize=10)

    fig.suptitle("TUKU — GPS Carrier Gap-Fill Reconstruction (Phase 1.1)\n"
                 "$b_k(t) = a_k \\cdot d_{GPS}(t) + c_k$    $a_k \\geq 0$    "
                 "$\\sum a_k \\leq 1$",
                 fontsize=16, fontweight="bold", y=0.998)
    fig.tight_layout(rect=[0, 0.02, 1, 0.96])
    fig.text(0.5, 0.975, f"Decision Point 1: CARRIER-PRIMARY  |  "
             f"sum(a_k) = {sum(r['a_k'] for r in results.values()):.4f}  |  2026-06-09",
             fontsize=12, ha="center", fontweight="bold", color="#2ca02c",
             bbox=dict(boxstyle="round,pad=0.3", facecolor="#e8f5e9", edgecolor="#2ca02c", linewidth=1.5))

    png_path = PLOT_DIR / "TUKU_reconstruction_6layer.png"
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"\n  Figure: {png_path}")


# ═══════════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════════

def main(gwl_layers: set | None = None):
    if gwl_layers is None:
        gwl_layers = set()

    gwl_str = f" + GWL ({','.join(sorted(gwl_layers))})" if gwl_layers else ""
    print("=" * 75)
    print(f"Part 1 Phase 1.1 — GPS Carrier{gwl_str} Gap-Fill Reconstruction (TUKU)")
    print("=" * 75)

    # 1. Load data
    print(f"\n── Loading data{' (+ tau-lagged GWL for ' + ','.join(sorted(gwl_layers)) + ')' if gwl_layers else ''} ──")
    data = load_data(gwl_layers)
    print(f"  Master timeline: {len(data['master_dates'])} epochs "
          f"({data['master_dates'][0]} to {data['master_dates'][-1]})")
    gps_epochs = np.isfinite(data["d_surface"]).sum()
    print(f"  GPS coverage: {gps_epochs}/{len(data['master_dates'])} epochs "
          f"({100*gps_epochs/len(data['master_dates']):.1f}%)")

    for layer in data["layers"]:
        mlcw_epochs = np.isfinite(data["layers"][layer]["b_cum"]).sum()
        u_info = f", u_lagged={'yes' if data['layers'][layer].get('u_lagged') is not None else 'no'}"
        print(f"  {layer}: {mlcw_epochs} MLCW epochs, τ={data['layers'][layer]['tau_opt']}{u_info}")

    # 2. Fit per-layer carrier (± GWL term)
    model_desc = "b_k = a_k * d_GPS + d_k * u + c_k" if gwl_layers else "b_k = a_k * d_GPS + c_k"
    print(f"\n── Fitting: {model_desc} ──")
    results = fit_carrier_per_layer(data, gwl_layers)

    # 3. Joint rescaling (only for carrier-only model; skip for GWL layers)
    if not gwl_layers:
        print("\n── Joint rescaling check ──")
        results = joint_rescale(results, data)

    # 4. Summary table
    has_gwl = any(r.get("d_k", 0) != 0 for r in results.values())
    print(f"\n── Reconstruction quality ──")
    if has_gwl:
        print(f"  {'Layer':5s} | {'a_k':>8s} | {'d_k':>8s} | {'c_k':>8s} | {'R²':>7s} | {'RMSE':>7s} | {'Bias':>8s} | {'Gap-filled':>10s}")
        print(f"  {'-'*5} | {'-'*8} | {'-'*8} | {'-'*8} | {'-'*7} | {'-'*7} | {'-'*8} | {'-'*10}")
    else:
        print(f"  {'Layer':5s} | {'a_k':>8s} | {'c_k':>8s} | {'R²':>7s} | {'RMSE':>7s} | {'Bias':>8s} | {'Gap-filled':>10s}")
        print(f"  {'-'*5} | {'-'*8} | {'-'*8} | {'-'*7} | {'-'*7} | {'-'*8} | {'-'*10}")
    for layer in ["F1", "T1", "F2", "T2", "F3", "F4"]:
        r = results[layer]
        if has_gwl:
            print(f"  {layer:5s} | {r['a_k']:8.5f} | {r['d_k']:8.5f} | {r['c_k']:8.2f} | {r['r2_cal']:7.4f} | "
                  f"{r['rmse_cal']:7.2f} | {r['bias']:+8.2f} | {r['n_gap_filled']:10d}")
        else:
            print(f"  {layer:5s} | {r['a_k']:8.5f} | {r['c_k']:8.2f} | {r['r2_cal']:7.4f} | "
                  f"{r['rmse_cal']:7.2f} | {r['bias']:+8.2f} | {r['n_gap_filled']:10d}")

    sum_a = sum(r["a_k"] for r in results.values())
    print(f"\n  sum(a_k) = {sum_a:.4f}  {'✓ <= 1' if sum_a <= 1.0001 else '✗ > 1 — rescaling applied'}")

    # 5. Write CSVs
    print("\n── Writing per-layer CSVs ──")
    write_csvs(data, results)

    # 6. Plot
    print("\n── Generating 6-panel figure ──")
    make_figure(data, results)

    # 7. Save summary JSON
    has_gwl = any(r.get("d_k", 0) != 0 for r in results.values())
    gwl_layers_list = sorted([lyr for lyr, r in results.items() if r.get("d_k", 0) != 0])
    model_desc = "b_k(t) = a_k * d_GPS(t) + c_k, a_k >= 0"
    if has_gwl:
        model_desc = "b_k(t) = a_k * d_GPS(t) + d_k * u(t) + c_k, a_k >= 0, d_k >= 0 (for: " + ",".join(gwl_layers_list) + ")"
    summary = {
        "metadata": {
            "description": "GPS carrier gap-fill reconstruction at TUKU (Part 1 Phase 1.1)",
            "model": model_desc,
            "decision_point_1": "CARRIER-PRIMARY",
            "gwl_layers": gwl_layers_list if has_gwl else [],
            "date": "2026-06-10",
        },
        "per_layer": {},
        "sum_a_k": round(sum_a, 6),
        "sum_a_k_leq_1": bool(sum_a <= 1.0001),
    }
    for layer in ["F1", "T1", "F2", "T2", "F3", "F4"]:
        r = results[layer]
        entry = {
            "a_k": round(r["a_k"], 6),
            "c_k": round(r["c_k"], 4),
            "r2_cal": round(r["r2_cal"], 6),
            "rmse_cal_mm": round(r["rmse_cal"], 4),
            "bias_mm": round(r["bias"], 4),
            "n_calibration_epochs": int(r["n_calib"]),
            "n_gap_filled_epochs": int(r["n_gap_filled"]),
        }
        if r.get("d_k", 0) != 0:
            entry["d_k"] = round(r["d_k"], 6)
        summary["per_layer"][layer] = entry
    summary_path = OUT_DIR / "TUKU_carrier_reconstruction_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n  Summary JSON: {summary_path}")

    print(f"\n{'='*75}")
    print("Phase 1.1 complete. Outputs:")
    print(f"  6 CSVs → {OUT_DIR}/")
    print(f"  1 PNG  → {PLOT_DIR}/")
    print(f"  1 JSON → {summary_path}")
    print(f"{'='*75}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="GPS carrier gap-fill reconstruction at TUKU (Part 1 Phase 1.1)")
    parser.add_argument("--use-gwl", type=str, default=None,
                        help="Comma-separated layer codes to add GWL residual term "
                             "(e.g. --use-gwl T1,F2). Only layers validated by "
                             "14b_carrier_gwl_eval.py should be specified.")
    args = parser.parse_args()

    gwl_layers = set()
    if args.use_gwl:
        gwl_layers = set(l.strip() for l in args.use_gwl.split(","))
        valid_layers = {"F1", "T1", "F2", "T2", "F3", "F4"}
        unknown = gwl_layers - valid_layers
        if unknown:
            print(f"ERROR: Unknown layers: {unknown}. Valid: {valid_layers}")
            sys.exit(1)

    main(gwl_layers)
