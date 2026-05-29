"""
fit_ihm_f_v2.py — Entry point for the unified detrended IHM-F model (v2).

Replaces fit_ihm_f.py as the production entry point. fit_ihm_f.py is retained
unchanged for archival comparison with the v1 two-regime formulation.

Usage:
    python scripts/10_ihmf/fit_ihm_f_v2.py --station TUKU --all
    python scripts/10_ihmf/fit_ihm_f_v2.py --station TUKU --layer F1

Model summary:
    Detrend y (MLCW), dh (GWL Δhead), x (InSAR) with a 4-param basis
    [1, t, sin(2πt/T), cos(2πt/T)].  Fit detrended OLS with τ-lag grid search.
    Reconstruct full prediction as trend (f̄_k · x) + dynamic component.

Key differences from v1:
    - Single procedure for all 191 station-layer pairs (no Path A/B routing).
    - Two-regime elastic/inelastic switch removed from fitting.
    - τ_max = 24 epochs (not 12 — widens search for deep layers like F3).
    - f̄_k loaded at layer granularity (summed over rings), not ring granularity.
    - Walk-forward re-detrends per fold (no look-ahead contamination).
    - Output JSON uses gamma_k/beta_k (not S_ske/S_skv); S_ske alias provided
      for ihmf_plots.py backward compatibility.

Physics guarantees (enforced by construction, not post-hoc):
    - γ_k ≥ 0  (lsq_linear lower bound)
    - β_k ≥ 0  (lsq_linear lower bound)
    - GWL never negated (load_and_align contract + detrend preserves sign)
    - dh = H(t) - H(t_ref): head change sign unchanged through pipeline
    - InSAR: negative = subsidence throughout
"""

import argparse
import json
import sys
import numpy as np
import pandas as pd
from pathlib import Path

# ── Module imports (siblings in scripts/10_ihmf/) ───────────────────────────
# Add parent dir to path so imports work when run from project root
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from ihmf_io      import load_and_align
from ihmf_detrend import detrend_signal, load_fbar_layer
from ihmf_model_v2 import (grid_search_tau_v2, run_walk_forward_v2,
                            build_diagnostics_v2)
from ihmf_plots   import plot_raw_fit, plot_reconstruction

# ── Constants ────────────────────────────────────────────────────────────────
TAU_MAX     = 24          # search τ ∈ {0, …, 24} epochs (~10 months at 12-day cadence)
OUTPUT_SUBDIR = "v2"      # results/ihmf/v2/ to avoid overwriting v1 outputs

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH  = PROJECT_ROOT / "data" / "ihmf_config.json"


# ── CLI ──────────────────────────────────────────────────────────────────────

def _parse_args():
    p = argparse.ArgumentParser(
        description="Fit unified detrended IHM-F model (v2) for a station+layer.")
    p.add_argument("--station", required=True,
                   help="Station name (e.g. TUKU)")
    p.add_argument("--layer", default=None,
                   help="Layer code (F1/T1/F2/T2/F3/F4). Omit with --all.")
    p.add_argument("--all", action="store_true",
                   help="Process all layers for the given station.")
    return p.parse_args()


# ── Core fit function ────────────────────────────────────────────────────────

def run_one(entry: dict, project_root: Path = PROJECT_ROOT) -> dict:
    """
    Fit the v2 model for a single config entry. Returns the result dict.

    Pipeline:
        1. Load and align MLCW + GWL + InSAR via ihmf_io.load_and_align.
        2. Extract raw signals: y (MLCW mm), dh (GWL Δhead m), x (InSAR mm).
        3. Detrend all three signals over the full record.
        4. Grid-search τ ∈ [0, TAU_MAX] on detrended signals.
        5. Walk-forward validation (4 folds), re-detrending per fold.
        6. Load f̄_k (layer-level, summed from ring-level direct ratio).
        7. Reconstruct full prediction: trend + dynamic component.
        8. Compute detrended-signal correlations for diagnostics.
        9. Build diagnostic warnings.
       10. Save plots (aliasing gamma_k → S_ske for ihmf_plots.py compatibility).
       11. Save JSON result.

    Parameters
    ----------
    entry : dict — one entry from ihmf_config.json
    project_root : Path — root of the scripts/data repository

    Returns
    -------
    result : dict — all fitted parameters, walk-forward results, diagnostics
    """
    station = entry["station"]
    layer   = entry["layer"]

    insar_csv = project_root / "data" / "insar" / "InSAR_measures_at_MLCW.csv"
    out_dir   = project_root / entry["output_dir"] / OUTPUT_SUBDIR
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── 1. Load and align ────────────────────────────────────────────────────
    merged, meta = load_and_align(entry, project_root, insar_csv)
    n_epochs = meta["n_epochs"]

    # ── 2. Extract raw signals ───────────────────────────────────────────────
    t_days = (
        (merged["datetime"] - merged["datetime"].iloc[0]).dt.days.values.astype(float)
    )
    y_raw  = merged["mlcw_mm"].values        # mm, negative = compaction
    h_raw  = merged["head_m"].values         # m MSL, higher = rising (NEVER negated)
    dh_raw = h_raw - h_raw[0]               # Δhead from first epoch; negative = fell
    x_raw  = merged["insar_mm"].values       # mm, negative = subsidence

    # ── 3. Detrend all three signals (full record) ───────────────────────────
    y_d,  y_coef,  y_trend  = detrend_signal(t_days, y_raw)
    dh_d, dh_coef, dh_trend = detrend_signal(t_days, dh_raw)
    x_d,  x_coef,  x_trend  = detrend_signal(t_days, x_raw)

    # ── 4. Grid search τ on full-record detrended signals ────────────────────
    best, tau_curve = grid_search_tau_v2(y_d, dh_d, x_d, TAU_MAX)
    tau_opt = best["tau"]

    # ── 5. Walk-forward validation (raw signals; re-detrend per fold inside) ──
    # Pass RAW arrays so run_walk_forward_v2 can re-detrend per training window.
    wf_results = run_walk_forward_v2(merged, y_raw, dh_raw, x_raw, TAU_MAX)

    # ── 6. Load layer-level f̄_k ──────────────────────────────────────────────
    f_bar_k = load_fbar_layer(station, layer, project_root)

    # ── 7. Reconstruct full prediction ───────────────────────────────────────
    n = n_epochs
    m = n - tau_opt

    # Dynamic component on the lagged window (detrended band only)
    dh_d_lag = dh_d[tau_opt:]
    x_d_lag  = x_d[:m]
    y_dynamic = (best["intercept"]
                 + best["gamma_k"] * dh_d_lag
                 + best["beta_k"]  * x_d_lag)

    # Trend component: f̄_k × incremental InSAR change from the reference epoch.
    # IMPORTANT: use (x_raw - x_raw[0]), not x_raw directly.
    # x_raw is cumulative from the InSAR reference date (large negative value);
    # y_raw is referenced to the first epoch (starts near zero).
    # Anchoring to x_raw[0] keeps both signals on the same reference.
    # Add y_raw[0] so the prediction starts at the observed initial condition.
    x_inc         = x_raw[:m] - x_raw[0]    # incremental InSAR from epoch 0
    y_trend_pred  = y_raw[0] + f_bar_k * x_inc

    y_pred_full = y_trend_pred + y_dynamic  # full reconstructed prediction (mm)

    # ── 8. Detrended correlations for diagnostics ─────────────────────────────
    corr_yh_d   = float(np.corrcoef(y_d, dh_d)[0, 1])
    corr_yx_d   = float(np.corrcoef(y_d, x_d)[0, 1])
    corr_dh_x_d = float(np.corrcoef(dh_d, x_d)[0, 1])

    # Raw correlations for reference (not used in diagnostics)
    corr_yh_raw   = float(np.corrcoef(y_raw, dh_raw)[0, 1])
    corr_yx_raw   = float(np.corrcoef(y_raw, x_raw)[0, 1])
    corr_dh_x_raw = float(np.corrcoef(dh_raw, x_raw)[0, 1])

    # ── 9. Diagnostic warnings ────────────────────────────────────────────────
    concerns = build_diagnostics_v2(corr_yh_d, corr_dh_x_d, best, TAU_MAX)

    # ── Console summary ───────────────────────────────────────────────────────
    n_folds_ok = sum(1 for w in wf_results if not w.get("skipped", False))
    wf_rmse_str = " | ".join(
        f"{w['rmse_mm']:.2f}" if w["rmse_mm"] is not None else "skip"
        for w in wf_results
    )
    print(f"\n{'─' * 62}")
    print(f"  {station} {layer}  |  n={n_epochs}  "
          f"|  well={meta['wellcode']}  elev={meta['well_elev_m']:.0f}m")
    print(f"{'─' * 62}")
    print(f"  corr_d(y,dh)={corr_yh_d:+.3f}  corr_d(y,x)={corr_yx_d:+.3f}  "
          f"corr_d(dh,x)={corr_dh_x_d:+.3f}")
    print(f"  [raw]  corr(y,dh)={corr_yh_raw:+.3f}  "
          f"corr(dh,x)={corr_dh_x_raw:+.3f}")
    print(f"  tau={tau_opt}  R²={best['r2']:.3f}  RMSE={best['rmse']:.3f} mm")
    print(f"  gamma_k={best['gamma_k']:.4e} mm/m  "
          f"beta_k={best['beta_k']:.4e} mm/mm  "
          f"f_bar_k={f_bar_k:.4f}")
    print(f"  Walk-forward ({n_folds_ok} folds): {wf_rmse_str} mm")
    for c in concerns:
        print(f"  WARNING: {c}")

    # ── 10. Plots (alias gamma_k → S_ske for ihmf_plots.py compatibility) ────
    # ihmf_plots.py accesses best['S_ske'] and best['S_skv'] in panel titles.
    # We alias: S_ske = gamma_k, S_skv = 0.0 (no inelastic split in v2).
    # No changes to ihmf_plots.py required.
    best_aliased = {
        **best,
        "S_ske": best["gamma_k"],
        "S_skv": 0.0,
    }
    mask_i_empty = np.zeros(n - tau_opt, dtype=bool)  # no regime mask in v2

    dates_pred = merged["datetime"].iloc[:n - tau_opt].values

    plot_raw_fit(
        dates=dates_pred,
        y_obs_raw=y_raw[:n - tau_opt],
        y_pred_raw=y_pred_full,
        dh_lag=dh_raw[tau_opt:],     # show raw ΔH in diagnostic plot
        x_raw_lag=x_raw[:n - tau_opt],
        mask_i=mask_i_empty,
        best=best_aliased,
        station=station,
        layer=layer,
        out_dir=out_dir,
    )

    plot_reconstruction(
        dates=dates_pred,
        y_obs_cum=merged["mlcw_mm"].values[:n - tau_opt],
        y_pred_cum=y_pred_full,
        h_raw_lag=h_raw[tau_opt:],   # raw GWL head (m MSL, never negated)
        insar_raw=x_raw[:n - tau_opt],
        best=best_aliased,
        station=station,
        layer=layer,
        out_dir=out_dir,
    )

    # ── 11. Save JSON result ──────────────────────────────────────────────────
    result = {
        "station":         station,
        "layer":           layer,
        "model_version":   "v2_detrended",
        "wellcode":        meta["wellcode"],
        "well_elev_m":     meta["well_elev_m"],
        "gwl_feather":     meta["gwl_feather_name"],
        "n_epochs":        n_epochs,
        "tau_max_used":    TAU_MAX,
        "tau_opt":         tau_opt,
        # v2 parameters (primary)
        "gamma_k_mm_per_m":  round(best["gamma_k"],  6),
        "beta_k_mm_per_mm":  round(best["beta_k"],   6),
        "intercept_mm":      round(best["intercept"], 6),
        "f_bar_k":           round(f_bar_k,           6),
        # Fit quality
        "r2":      round(best["r2"],   4),
        "rmse_mm": round(best["rmse"], 4),
        # Detrended correlations
        "corr_y_dh_detrended":  round(corr_yh_d,   4),
        "corr_y_x_detrended":   round(corr_yx_d,   4),
        "corr_dh_x_detrended":  round(corr_dh_x_d, 4),
        # Raw correlations (reference only)
        "corr_y_dh_raw":  round(corr_yh_raw,   4),
        "corr_dh_x_raw":  round(corr_dh_x_raw, 4),
        # Walk-forward
        "walk_forward": [
            {k: (round(v, 4) if isinstance(v, float) else v)
             for k, v in w.items()}
            for w in wf_results
        ],
        # τ–RSS curve for diagnostics
        "tau_rss_curve": [
            {"tau": r["tau"], "rss": round(r["rss"], 4), "r2": round(r["r2"], 4)}
            for r in sorted(tau_curve, key=lambda r: r["tau"])
        ],
        "diagnostics": concerns,
    }

    json_path = out_dir / f"{station}_{layer}_v2_ihmf_results.json"
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2, default=str)

    print(f"  -> saved: {json_path.relative_to(project_root)}")
    return result


# ── Entry point ──────────────────────────────────────────────────────────────

def main():
    args = _parse_args()

    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    entries = cfg["entries"]

    station_entries = [e for e in entries if e["station"] == args.station]
    if not station_entries:
        available = sorted(set(e["station"] for e in entries))
        raise SystemExit(
            f"Station '{args.station}' not found in config.\n"
            f"Available: {available}"
        )

    if args.all:
        targets = station_entries
    elif args.layer:
        match = [e for e in station_entries if e["layer"] == args.layer]
        if not match:
            available_layers = [e["layer"] for e in station_entries]
            raise SystemExit(
                f"Layer '{args.layer}' not found for {args.station}.\n"
                f"Available: {available_layers}"
            )
        targets = [match[0]]
    else:
        raise SystemExit("Specify --layer LAYER or --all.")

    print(f"Config: {CONFIG_PATH}  ({len(entries)} entries total)")
    print(f"Targets: {len(targets)} layer(s) for {args.station}  [tau_max={TAU_MAX}]")

    results = []
    for entry in targets:
        try:
            results.append(run_one(entry))
        except Exception as exc:
            print(f"\n  {entry['station']} {entry['layer']}: ERROR — {exc}")
            raise  # re-raise during pilot to surface full traceback

    print(f"\nDone. {len(results)}/{len(targets)} layers fitted successfully.")


if __name__ == "__main__":
    main()
