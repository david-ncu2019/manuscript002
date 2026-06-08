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

    # ── Full-record fit ────────────────────────────────────────────────────
    ref_df = layer_dfs[layers[0]]
    t_days_full = ref_df["t_days"].values

    layer_data: dict[str, dict] = {}

    for layer in layers:
        df   = layer_dfs[layer]
        meta = layer_metas[layer]

        head_m  = df["head_m"].values
        mlcw_mm = df["mlcw_mm"].values

        # Use incremental (first-difference) signals — the physics equation is incremental
        # Δb_j(t) = S_j · ΔH_j(t−τ)  where Δ means epoch-to-epoch change
        inc_dH = np.diff(head_m)    # shape (T-1,), m per epoch
        inc_db = np.diff(mlcw_mm)   # shape (T-1,), mm per epoch

        # Regime mask on incremental-length array (use head at epoch t, not t+1)
        h_c = meta["h_c_head_m"]
        e_m, i_m = build_regime_mask(head_m[:-1], h_c)   # length T-1

        # Dates for incremental signal (epoch t drives the increment t→t+1)
        inc_dates = df["datetime"].values[:-1]

        # τ grid search on anomaly incremental signals (seasonal cycle removed)
        tau_opt, rss_curve, monthly_means_dH = tau_grid_search_per_layer(
            inc_dH, inc_db, e_m, i_m, tau_max, dates=inc_dates
        )
        print(f"  {layer}: τ_opt = {tau_opt} {tau_label}, "
              f"MSE_min = {rss_curve[tau_opt]:.4f}")

        layer_data[layer] = {
            "inc_dH":           inc_dH,              # full incremental head, length T_full-1
            "inc_db":           inc_db,              # full incremental compaction, length T_full-1
            "elastic_mask":     e_m,                 # full regime mask, length T_full-1
            "inelastic_mask":   i_m,
            "tau_opt":          tau_opt,
            "rss_curve":        [round(r, 6) for r in rss_curve],
            "monthly_means_dH": monthly_means_dH.tolist(),
        }

    # Build a common epoch window [tau_max, T_full-1] so every layer's lagged head
    # aligns to the same absolute epochs as InSAR and MLCW response.
    # For layer j at common epoch t: dH_lagged = inc_dH[t - tau_j], db = inc_db[t].
    tau_max_all = max(d["tau_opt"] for d in layer_data.values())
    T_full_inc  = len(insar_mm) - 1              # T_full - 1 (length of incremental signals)
    win_start   = tau_max_all                    # first epoch where all layers have lagged head
    win_len     = T_full_inc - win_start         # number of common epochs

    common_layer_data: dict[str, dict] = {}
    for layer in layers:
        d       = layer_data[layer]
        tau     = d["tau_opt"]
        offset  = tau_max_all - tau               # how far back in d["inc_dH"] to start
        # dH_lagged on common window: head at epochs (win_start-tau)..(win_start-tau+win_len-1)
        dH_lag  = d["inc_dH"][offset : offset + win_len]
        db_win  = d["inc_db"][win_start : win_start + win_len]
        e_win   = d["elastic_mask"][offset : offset + win_len]   # driver-time regime, lag-consistent
        i_win   = d["inelastic_mask"][offset : offset + win_len]
        common_layer_data[layer] = {
            "dH_lagged":        dH_lag,
            "db":               db_win,
            "elastic_mask":     e_win,
            "inelastic_mask":   i_win,
            "tau_opt":          tau,
            "rss_curve":        d["rss_curve"],
            "monthly_means_dH": d["monthly_means_dH"],
        }

    # Store the common-window layer_data for output (rss_curves, walk-forward)
    layer_data = common_layer_data

    # InSAR incremental on the same common window
    inc_insar = np.diff(insar_mm)                # shape (T_full-1,)
    inc_insar_win = inc_insar[win_start : win_start + win_len]
    result = joint_solve_fixed_tau(layer_data, inc_insar_win, alpha_external=alpha_override)
    print(f"\n  α = {result['alpha']:.4f}  |  c = {result['c_intercept']:.4f} mm  "
          f"|  RMSE_InSAR = {result['rmse_insar']:.3f} mm  |  R²_InSAR = {result['r2_insar']:.4f}")
    print(f"  RMSE_MLCW = {result['rmse_mlcw']:.3f} mm")
    for lyr, p in result["layers"].items():
        print(f"    {lyr}: S_ke={p['S_ke']:.5f}  S_kv={p['S_kv']:.5f}  τ={p['tau_opt']}"
              f"  n_elastic={p.get('n_elastic','?')}  n_inelastic={p.get('n_inelastic','?')}")

    # Diagnostics: flag physically suspect results
    diagnostics: list[str] = []
    if not (0 < result["alpha"] <= 1):
        diagnostics.append(f"WARN: alpha={result['alpha']:.4f} outside (0,1)")
    for lyr, p in result["layers"].items():
        n_inel = p.get("n_inelastic", 0)
        n_elas = p.get("n_elastic", 0)
        if n_inel < 10:
            diagnostics.append(
                f"WARN: {lyr} n_inelastic={n_inel} < 10 — S_kv undefined (insufficient data)"
            )
        if p["S_kv"] < 1e-10:
            diagnostics.append(f"INFO: {lyr} S_kv<1e-10 (elastic-only or data-limited)")
        elif p["S_ke"] < 1e-10:
            diagnostics.append(f"INFO: {lyr} S_ke<1e-10 (inelastic-only or data-limited)")
        elif p["S_kv"] / p["S_ke"] < 8.0 or p["S_kv"] / p["S_ke"] > 58.0:
            ratio = p["S_kv"] / p["S_ke"]
            diagnostics.append(
                f"WARN: {lyr} S_kv/S_ke={ratio:.2f} outside physical range 8–58×"
            )
        tau_pct = layer_data[lyr]["tau_opt"]
        if tau_pct == tau_max:
            diagnostics.append(f"WARN: {lyr} τ_opt at τ_max={tau_max} — consider extending search")

    # ── Walk-forward validation ────────────────────────────────────────────
    print(f"\n  Running walk-forward validation (4 folds)...")
    wf_results = run_walk_forward_v3(layer_dfs, layer_metas, inc_insar, tau_max,
                                      alpha_external=alpha_override)
    for fold in wf_results:
        if fold.get("skipped"):
            print(f"    {fold['fold']}: SKIPPED — {fold.get('reason', '')}")
        else:
            print(f"    {fold['fold']}: α={fold['alpha']:.4f}  "
                  f"RMSE_InSAR={fold['rmse_insar']:.3f}  n={fold['n_test']}")

    # ── Save result ────────────────────────────────────────────────────────
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
        "rmse_mlcw":     result["rmse_mlcw"],
        "rmse_insar":    result["rmse_insar"],
        "r2_insar":      result["r2_insar"],
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
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--all",   action="store_true", help="Fit all layers")
    grp.add_argument("--layer", help="Single layer code e.g. F2")
    args = parser.parse_args()

    run_station(
        args.station,
        layer_filter=None if args.all else args.layer,
        gps_mode=args.gps,
        alpha_override=args.alpha,
    )
