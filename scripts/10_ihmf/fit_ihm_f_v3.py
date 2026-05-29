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

from ihmf_io_multilayer import load_all_layers, load_config
from ihmf_model_v3 import (
    build_regime_mask,
    tau_grid_search_per_layer,
    joint_solve_fixed_tau,
    run_walk_forward_v3,
)
from ihmf_detrend import detrend_signal

TAU_MAX = 73   # 1 year at 5-day epochs


def run_station(station: str, layer_filter: str | None = None) -> dict:
    shared_cfg, entries, insar_csv = load_config(ROOT)

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
    print(f"\n{'='*60}")
    print(f"Station: {station}  |  Layers: {layers}  |  τ_max: {TAU_MAX}")
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

        # τ grid search on incremental signals
        tau_opt, rss_curve = tau_grid_search_per_layer(inc_dH, inc_db, e_m, i_m, TAU_MAX)
        print(f"  {layer}: τ_opt = {tau_opt} epochs ({tau_opt*5} days), "
              f"RSS_min = {rss_curve[tau_opt]:.4f}")

        T = len(inc_dH) - tau_opt
        layer_data[layer] = {
            "dH_lagged":      inc_dH[tau_opt:],     # GWL increment lagged by τ
            "db":             inc_db[:T],            # MLCW increment aligned to lagged window
            "elastic_mask":   e_m[:T],
            "inelastic_mask": i_m[:T],
            "tau_opt":        tau_opt,
            "rss_curve":      [round(r, 6) for r in rss_curve],
        }

    # Joint solve using optimal τ per layer
    # InSAR must also be incremental to match the incremental MLCW/GWL signals
    inc_insar = np.diff(insar_mm)   # shape (T_full-1,)
    result = joint_solve_fixed_tau(layer_data, inc_insar)
    print(f"\n  α = {result['alpha']:.4f}  |  RMSE_InSAR = {result['rmse_insar']:.3f} mm  "
          f"|  R²_InSAR = {result['r2_insar']:.4f}")
    print(f"  RMSE_MLCW = {result['rmse_mlcw']:.3f} mm")
    for lyr, p in result["layers"].items():
        print(f"    {lyr}: S_ke={p['S_ke']:.5f}  S_kv={p['S_kv']:.5f}  τ={p['tau_opt']}")

    # Diagnostics: flag physically suspect results
    diagnostics: list[str] = []
    if not (0 < result["alpha"] <= 1):
        diagnostics.append(f"WARN: alpha={result['alpha']:.4f} outside (0,1)")
    for lyr, p in result["layers"].items():
        if p["S_kv"] == 0.0:
            diagnostics.append(f"INFO: {lyr} S_kv=0 (elastic-only layer or data-limited)")
        tau_pct = layer_data[lyr]["tau_opt"]
        if tau_pct == TAU_MAX:
            diagnostics.append(f"WARN: {lyr} τ_opt at τ_max={TAU_MAX} — consider extending search")

    # ── Walk-forward validation ────────────────────────────────────────────
    print(f"\n  Running walk-forward validation (4 folds)...")
    wf_results = run_walk_forward_v3(layer_dfs, layer_metas, inc_insar, TAU_MAX)
    for fold in wf_results:
        if fold.get("skipped"):
            print(f"    {fold['fold']}: SKIPPED — {fold.get('reason', '')}")
        else:
            print(f"    {fold['fold']}: α={fold['alpha']:.4f}  "
                  f"RMSE_InSAR={fold['rmse_insar']:.3f}  n={fold['n_test']}")

    # ── Save result ────────────────────────────────────────────────────────
    out_dir = ROOT / "results" / "ihmf" / "v3"
    out_dir.mkdir(parents=True, exist_ok=True)

    suffix = f"_{layer_filter}" if layer_filter else ""
    out_path = out_dir / f"{station}{suffix}_v3_results.json"

    output = {
        "station":       station,
        "layers_fitted": layers,
        "tau_max":       TAU_MAX,
        "alpha":         result["alpha"],
        "beta":          result["beta"],
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
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--all",   action="store_true", help="Fit all layers")
    grp.add_argument("--layer", help="Single layer code e.g. F2")
    args = parser.parse_args()

    run_station(args.station, layer_filter=None if args.all else args.layer)
