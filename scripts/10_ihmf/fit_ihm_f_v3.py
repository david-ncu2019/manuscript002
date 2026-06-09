"""
fit_ihm_f_v3.py — Entry point for IHM-F v3 (joint constrained inversion).

Usage:
    python scripts/10_ihmf/fit_ihm_f_v3.py --station TUKU --all
    python scripts/10_ihmf/fit_ihm_f_v3.py --station TUKU --layer F2

Output: results/ihmf/v3/{STATION}_v3_results.json
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ihmf_io_multilayer import load_all_layers, load_all_layers_gps, load_config
from ihmf_model_v3 import (
    build_regime_mask,
    tau_grid_search_per_layer,
    joint_solve_fixed_tau,
    joint_solve_cumulative,
    run_walk_forward_v3,
)
from ihmf_detrend import detrend_signal

# Cadence-specific τ_max values (both = ~600 days physical lag ceiling)
TAU_MAX_MONTHLY = 24   # monthly epochs; 24 = 720 days
TAU_MAX_5DAY    = 120  # 5-day epochs;   120 = 600 days


def run_station(
    station: str,
    layer_filter: str | None = None,
    gps_mode: bool = False,
    alpha_override: float | None = None,
    output_dir: str | None = None,
) -> dict:
    shared_cfg, entries, insar_csv = load_config(ROOT)

    if gps_mode:
        tau_max     = TAU_MAX_5DAY
        tau_label   = "5-day epochs"
        tau_demo_dir = ROOT / "tau_demo_TUKU" / "data"
        layer_dfs, layer_metas, insar_mm = load_all_layers_gps(
            station, entries, ROOT, tau_demo_dir
        )
        print(f"  [GPS mode] master timeline from tau_demo_TUKU/data feathers")
    else:
        tau_max   = TAU_MAX_MONTHLY
        tau_label = "months"
        layer_dfs, layer_metas, insar_mm = load_all_layers(
            station, entries, ROOT, insar_csv
        )

    if layer_filter:
        if layer_filter not in layer_dfs:
            raise ValueError(f"Layer '{layer_filter}' not found at station '{station}'. "
                             f"Available: {list(layer_dfs.keys())}")
        layer_dfs   = {layer_filter: layer_dfs[layer_filter]}
        layer_metas = {layer_filter: layer_metas[layer_filter]}

    layers = list(layer_dfs.keys())
    mode_str = "GPS" if gps_mode else "InSAR"
    print(f"\n{'='*60}")
    print(f"Station: {station}  |  Mode: {mode_str}  |  Layers: {layers}  |  τ_max: {tau_max} ({tau_label})")
    print(f"{'='*60}")

    # ── Full-record fit (cumulative domain) ────────────────────────────────
    ref_df = layer_dfs[layers[0]]
    t_days_full = ref_df["t_days"].values
    T_full = len(insar_mm)

    layer_data: dict[str, dict] = {}

    for layer in layers:
        df   = layer_dfs[layer]
        meta = layer_metas[layer]

        head_m         = df["head_m"].values         # absolute (m MSL), for τ search
        head_m_zeroed  = df["head_m_zeroed"].values  # zero-ref (m), for cumulative solver (R1)
        mlcw_mm = df["mlcw_mm"].values               # cumulative, length T_full
        h_c_abs = meta["h_c_head_m"]                 # absolute (m MSL), for regime mask
        h_c_zeroed = meta["h_c_zeroed"]              # zero-ref (m), for cumulative solver (R2)

        # τ grid search uses incremental signals (seasonal cycle removed)
        # — the incremental τ search uses absolute head; datum cancels in diffs.
        # Cumulative τ search is a future enhancement.
        inc_dH = np.diff(head_m)
        inc_db = np.diff(mlcw_mm)
        e_m, i_m = build_regime_mask(head_m[:-1], h_c_abs)
        inc_dates = df["datetime"].values[:-1]

        tau_opt, rss_curve, monthly_means_dH = tau_grid_search_per_layer(
            inc_dH, inc_db, e_m, i_m, tau_max, dates=inc_dates
        )
        print(f"  {layer}: τ_opt = {tau_opt} {tau_label}, "
              f"MSE_min = {rss_curve[tau_opt]:.4f}")

        layer_data[layer] = {
            "head_m":           head_m,            # absolute, for τ search / debugging
            "head_m_zeroed":    head_m_zeroed,     # zero-ref, for cumulative solver (R1)
            "mlcw_mm":          mlcw_mm,           # full cumulative compaction, length T_full
            "h_c_head_m":       h_c_abs,           # absolute, for reference
            "h_c_zeroed":       h_c_zeroed,        # zero-ref, for cumulative solver (R2)
            "tau_opt":          tau_opt,
            "rss_curve":        [round(r, 6) for r in rss_curve],
            "monthly_means_dH": monthly_means_dH.tolist(),
        }

    # Build a common epoch window [tau_max_all, T_full-1] so every layer's
    # lagged cumulative head aligns to the same absolute epochs.
    # For layer j at common epoch t: H_lagged[t] = head_m_zeroed[t - τ_j], b[t] = mlcw_mm[t].
    # R1: use zero-referenced head for the elastic regressor in cumulative solver.
    # R2: use zero-referenced h_c for the virgin term.
    tau_max_all = max(d["tau_opt"] for d in layer_data.values())
    win_start   = tau_max_all                        # first epoch where all layers align
    win_len     = T_full - win_start                 # number of common epochs

    common_layer_data: dict[str, dict] = {}
    for layer in layers:
        d       = layer_data[layer]
        tau     = d["tau_opt"]
        offset  = tau_max_all - tau                   # how far back in head_m_zeroed to start
        H_lag   = d["head_m_zeroed"][offset : offset + win_len]  # zero-ref cumulative head (R1)
        b_win   = d["mlcw_mm"][win_start : win_start + win_len]   # cumulative compaction
        common_layer_data[layer] = {
            "H_lagged":         H_lag,
            "b_cum":            b_win,
            "h_c_head_m":       d["h_c_zeroed"],     # zero-ref preconsolidation head (R2)
            "tau_opt":          tau,
            "rss_curve":        d["rss_curve"],
            "monthly_means_dH": d["monthly_means_dH"],
        }

    # Store the common-window layer_data for output
    layer_data = common_layer_data

    # InSAR/GPS cumulative on the same common window
    cum_insar_win = insar_mm[win_start : win_start + win_len]
    result = joint_solve_cumulative(layer_data, cum_insar_win, alpha_external=alpha_override)
    print(f"\n  α = {result['alpha']:.4f}  |  c = {result['c_intercept']:.4f} mm  "
          f"|  RMSE_InSAR = {result['rmse_insar']:.3f} mm  |  R²_InSAR = {result['r2_insar']:.4f}")
    print(f"  R²_MLCW_cum = {result['r2_mlcw_cum']:.4f}  |  RMSE_MLCW_cum = {result['rmse_mlcw_cum']:.3f} mm")
    for lyr, p in result["layers"].items():
        c_str = f"  c={p.get('c_intercept', 0.0):.3f}" if 'c_intercept' in p else ""
        print(f"    {lyr}: S_ke={p['S_ke']:.5f}  S_kv={p['S_kv']:.5f}  τ={p['tau_opt']}"
              f"  n_elastic={p.get('n_elastic','?')}  n_inelastic={p.get('n_inelastic','?')}"
              f"  R²_cum={p.get('r2_cum', float('nan')):.4f}{c_str}")

    # Diagnostics: flag physically suspect results
    diagnostics: list[str] = []
    if not (0 < result["alpha"] <= 1):
        diagnostics.append(f"WARN: alpha={result['alpha']:.4f} outside (0,1)")
    for lyr, p in result["layers"].items():
        n_inel = p.get("n_inelastic", 0)
        n_elas = p.get("n_elastic", 0)
        r2c = p.get("r2_cum", float("nan"))
        if n_inel < 10:
            diagnostics.append(
                f"WARN: {lyr} n_inelastic={n_inel} < 10 — S_kv unreliable (insufficient data)"
            )
        if not np.isnan(r2c) and r2c < 0:
            diagnostics.append(f"WARN: {lyr} R²_cum={r2c:.4f} < 0 — model worse than mean")
        if p["S_kv"] < 1e-10:
            diagnostics.append(f"INFO: {lyr} S_kv<1e-10 (elastic-only or data-limited)")
        elif p["S_ke"] < 1e-10:
            diagnostics.append(f"INFO: {lyr} S_ke<1e-10 (inelastic-only or data-limited)")
        elif p["S_kv"] / p["S_ke"] < 8.0 or p["S_kv"] / p["S_ke"] > 100.0:
            ratio = p["S_kv"] / p["S_ke"]
            diagnostics.append(
                f"WARN: {lyr} S_kv/S_ke={ratio:.2f} outside physical range 8–100×"
            )
        tau_pct = layer_data[lyr]["tau_opt"]
        if tau_pct == tau_max:
            diagnostics.append(f"WARN: {lyr} τ_opt at τ_max={tau_max} — consider extending search")

    # ── Walk-forward validation (legacy incremental path) ──────────────────
    print(f"\n  Running walk-forward validation (4 folds)...")
    inc_insar = np.diff(insar_mm)                # incremental for legacy walk-forward
    wf_results = run_walk_forward_v3(layer_dfs, layer_metas, inc_insar, tau_max,
                                      alpha_external=alpha_override)
    for fold in wf_results:
        if fold.get("skipped"):
            print(f"    {fold['fold']}: SKIPPED — {fold.get('reason', '')}")
        else:
            print(f"    {fold['fold']}: α={fold['alpha']:.4f}  "
                  f"RMSE_InSAR={fold['rmse_insar']:.3f}  n={fold['n_test']}")

    # ── Save result ────────────────────────────────────────────────────────
    if output_dir:
        out_dir = Path(output_dir)
    else:
        out_dir = ROOT / "results" / "ihmf" / "v3"
    out_dir.mkdir(parents=True, exist_ok=True)

    mode_suffix  = "_gps" if gps_mode else ""
    layer_suffix = f"_{layer_filter}" if layer_filter else ""
    out_path = out_dir / f"{station}{mode_suffix}{layer_suffix}_v3_results.json"

    output = {
        "station":       station,
        "mode":            "gps" if gps_mode else "insar",
        "alpha_override":  alpha_override,
        "layers_fitted":   layers,
        "tau_max":         tau_max,
        "tau_cadence":     tau_label,
        "alpha":         result["alpha"],
        "beta":          result["beta"],
        "c_intercept":   result["c_intercept"],
        "r2_mlcw_cum":   result["r2_mlcw_cum"],
        "rmse_mlcw_cum": result["rmse_mlcw_cum"],
        "rmse_insar":    result["rmse_insar"],
        "r2_insar":      result["r2_insar"],
        "solver":        result.get("solver", "incremental_lsq_linear"),
        "lam":           result["lam"],
        "T":             result["T"],
        "layers":        result["layers"],
        "tau_rss_curves": {lyr: layer_data[lyr]["rss_curve"] for lyr in layers},
        "walk_forward":  wf_results,
        "diagnostics":   diagnostics,
    }

    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=_json_default)

    print(f"\n  Saved: {out_path}")
    return output


def _json_default(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, bool):
        return bool(obj)
    raise TypeError(f"Not JSON serialisable: {type(obj)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IHM-F v3 single-station fit")
    parser.add_argument("--station", required=True, help="Station name e.g. TUKU")
    parser.add_argument(
        "--gps", action="store_true",
        help=(
            "GPS mode: use tau_demo_TUKU/data feathers (5-day cadence, τ_max=120). "
            "Replaces InSAR CSV with GPS vertical displacement as Step-2 calibration signal."
        ),
    )
    parser.add_argument(
        "--alpha", type=float, default=None,
        help=(
            "Fix alpha to this empirical value, bypassing Step 2 OLS. "
            "Required in GPS mode when the GPS record starts after the main "
            "inelastic consolidation period (e.g. --alpha 0.634 for TUKU)."
        ),
    )
    parser.add_argument(
        "--output-dir", type=str, default=None,
        help="Override output directory (default: results/ihmf/v3/). "
             "Created if it does not exist.",
    )
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--all",   action="store_true", help="Fit all layers")
    grp.add_argument("--layer", help="Single layer code e.g. F2")
    args = parser.parse_args()

    run_station(
        args.station,
        layer_filter=None if args.all else args.layer,
        gps_mode=args.gps,
        alpha_override=args.alpha,
        output_dir=args.output_dir,
    )
