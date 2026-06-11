"""
21_f1t1_hypotheses.py — Task 6.2: F1/T1 τ-sensitivity and elastic-dominated test.

Physical story: F1 and T1 (shallow layers, HONGLUN well) have inelastic/elastic bulk
ratios of 1.64 and 2.03 — well below the physical floor of ~3 (inelastic storage should
substantially exceed elastic in these partially fine-grained units). Prior analysis
(f1t1_below_floor.json, hypothesis a) confirmed the virgin term V IS active: head dropped
~3.36 m below preconsolidation head h_c on ~48% of epochs. This script tests:

  (b) Is τ unidentifiable for these layers? Flat SSE vs τ → τ cannot be pinned.
  (c) Does adding the inelastic V term actually improve out-of-sample prediction?
      If RMSE_elastic ≈ RMSE_full, these layers respond near-elastically post-2015
      regardless of the V signal being formally present.

Usage:
    $env:PYTHONPATH=""; conda run -n fafalab2 python tau_demo_TUKU/21_f1t1_hypotheses.py

Outputs:
    tau_demo_TUKU/results/characterization/f1t1_hypotheses.json
    tau_demo_TUKU/plots/characterization/F1_tau_sse.png
    tau_demo_TUKU/plots/characterization/T1_tau_sse.png

Reference: super_plan_2026-06-09 Task 6.2 / PART1_FINDINGS_20260610.md
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import lsq_linear

warnings.filterwarnings("ignore", category=UserWarning)

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
TAU_DEMO = ROOT / "tau_demo_TUKU"
sys.path.insert(0, str(TAU_DEMO))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "10_ihmf"))

from gap_aware_cumsum import gap_aware_cumulative, census

INC_DIR = TAU_DEMO / "data" / "incremental_data"
DATA_DIR = TAU_DEMO / "data"
OUT_JSON_DIR = TAU_DEMO / "results" / "characterization"
OUT_PLOT_DIR = TAU_DEMO / "plots" / "characterization"
OUT_JSON_DIR.mkdir(parents=True, exist_ok=True)
OUT_PLOT_DIR.mkdir(parents=True, exist_ok=True)

# Production τ source
RESULT_JSON = ROOT / "results" / "ihmf" / "v3" / "verification_20260609_intercept" / "TUKU_gps_v3_results.json"
BELOW_FLOOR_JSON = OUT_JSON_DIR / "f1t1_below_floor.json"

# Config
REF_DATE = pd.Timestamp("2015-01-16")
DENSE_ERA_END = pd.Timestamp("2018-12-31")
TAU_MAX = 120

WELL_CONFIG = {
    "F1": ("HONGLUN_gwl_timeseries.feather", "09050111"),
    "T1": ("HONGLUN_gwl_timeseries.feather", "09050111"),
}

# ── Physical constants (from CLAUDE.md / TUKU borehole) ──────────────────────
LAYER_THICKNESS = {
    "F1": {"total_m": 41.577, "clay_m": 16.577},
    "T1": {"total_m":  8.729, "clay_m":  7.423},
}


# ── Helper: bounded bilinear fit [1, u, V] ───────────────────────────────────

def fit_bilinear_bounded(u: np.ndarray, V: np.ndarray, b: np.ndarray):
    """Fit b = c + S_ke*u + delta*V via lsq_linear.

    Bounds enforce S_ke >= 0 and delta >= 0 (=> S_kv = S_ke + delta >= S_ke).
    Intercept c is unconstrained.

    Returns (c, S_ke, S_kv, delta, b_pred, resid)
    """
    n = len(b)
    X = np.column_stack([np.ones(n), u, V])
    # Bounds: c in (-inf, inf), S_ke in [0, inf), delta in [0, inf)
    lb = [-np.inf, 0.0, 0.0]
    ub = [np.inf, np.inf, np.inf]
    res = lsq_linear(X, b, bounds=(lb, ub), method="bvls", max_iter=10000)
    c, S_ke, delta = res.x
    S_kv = S_ke + delta
    b_pred = X @ res.x
    resid = b - b_pred
    return float(c), float(S_ke), float(S_kv), float(delta), b_pred, resid


def fit_elastic_bounded(u: np.ndarray, b: np.ndarray):
    """Fit elastic-only b = c + S_ke*u via lsq_linear.

    Bounds: S_ke >= 0; c unconstrained.
    Returns (c, S_ke, b_pred, resid)
    """
    n = len(b)
    X = np.column_stack([np.ones(n), u])
    lb = [-np.inf, 0.0]
    ub = [np.inf, np.inf]
    res = lsq_linear(X, b, bounds=(lb, ub), method="bvls", max_iter=10000)
    c, S_ke = res.x
    b_pred = X @ res.x
    resid = b - b_pred
    return float(c), float(S_ke), b_pred, resid


# ── Main loading logic (replicates Script 15 lines 110–158) ─────────────────

def load_layer_arrays(layer: str, mlcw_inc: pd.DataFrame, master: pd.DataFrame):
    """Load and align GWL + cumulative MLCW for one layer.

    Replicates Script 15's inline recipe exactly:
    - Reads GWL feather, computes ref_val and h_c_abs from pre-REF_DATE data.
    - Aligns GWL to master timeline via merge_asof (3-day tolerance).
    - Returns full arrays H_abs_full and b_cum_full (not yet τ-lagged).
    """
    fname, wellcode = WELL_CONFIG[layer]
    gwl = pd.read_feather(DATA_DIR / fname)
    gwl["datetime"] = pd.to_datetime(gwl["datetime"]).astype("datetime64[ns]")
    gwl = gwl[["datetime", wellcode]].dropna(subset=[wellcode])
    gwl = gwl.sort_values("datetime").reset_index(drop=True)

    gwl_indexed = gwl.set_index("datetime")[wellcode]
    avail = gwl_indexed.dropna()
    pre_ref = avail.index[avail.index <= REF_DATE]
    if len(pre_ref) == 0:
        raise RuntimeError(f"Layer {layer}: no pre-REF_DATE GWL — cannot compute ref_val")
    ref_val = float(avail.loc[pre_ref[-1]])

    # h_c_abs from Script 15 lines 129–130
    pre_ref_vals = gwl[gwl["datetime"] < REF_DATE][wellcode].dropna()
    h_c_abs = float(pre_ref_vals.min()) if len(pre_ref_vals) >= 10 else float(gwl[wellcode].dropna().min())

    # Align GWL to master timeline
    gwl_aligned = pd.merge_asof(master, gwl, on="datetime",
                                direction="nearest", tolerance=pd.Timedelta("3D"))
    H_abs_full = gwl_aligned[wellcode].values.astype(float)
    b_cum_full = mlcw_inc[f"_cum_{layer}"].values.astype(float)

    return H_abs_full, b_cum_full, ref_val, h_c_abs


def apply_tau_lag(H_abs_full: np.ndarray, b_cum_full: np.ndarray, tau: int,
                  dates_full: np.ndarray | None = None):
    """Apply τ-lag pairing invariant and mask non-finite values.

    Driver  : H_abs_full[0 : N-τ]
    Response: b_cum_full[τ : N]

    Returns H_lag, b, valid_mask, dates_lag (if dates provided).
    """
    N = len(H_abs_full)
    if tau == 0:
        H_lag = H_abs_full.copy()
        b_arr = b_cum_full.copy()
        dates_lag = dates_full.copy() if dates_full is not None else None
    else:
        H_lag = H_abs_full[:N - tau]
        b_arr = b_cum_full[tau:]
        dates_lag = dates_full[tau:] if dates_full is not None else None

    valid = np.isfinite(H_lag) & np.isfinite(b_arr)
    return H_lag, b_arr, valid, dates_lag


def build_u_V(H_lag: np.ndarray, ref_val: float, h_c_abs: float):
    """Build zero-referenced head u and virgin term V.

    u = H_lag - ref_val   (never negate; negative = head fell)
    V = min(0, running_min(H_lag) - h_c_abs)   (running on DRIVER axis, <= 0)
    """
    u = H_lag - ref_val
    V = np.minimum(0.0, np.minimum.accumulate(H_lag) - h_c_abs)
    return u, V


# ── Hypothesis (b): τ-sensitivity via SSE grid search ───────────────────────

def hyp_b_tau_sensitivity(layer: str, H_abs_full: np.ndarray, b_cum_full: np.ndarray,
                           dates_full: np.ndarray, ref_val: float, h_c_abs: float,
                           tau_production: int, dense_era_end: pd.Timestamp):
    """Test whether SSE is flat across τ = 0..120.

    Restricts to dense era (date <= dense_era_end) for the τ grid search.
    Returns dict with tau_best, sse_flatness, sse_curve, verdict_b.
    """
    sse_list = []
    n_list = []

    for tau in range(TAU_MAX + 1):
        H_lag, b_arr, valid, dates_lag = apply_tau_lag(H_abs_full, b_cum_full, tau, dates_full)

        # Dense-era mask
        if dates_lag is not None:
            dense_mask = dates_lag <= dense_era_end
            valid = valid & dense_mask

        idx = np.where(valid)[0]
        if len(idx) < 10:
            sse_list.append(np.nan)
            n_list.append(0)
            continue

        H_v = H_lag[idx]
        b_v = b_arr[idx]
        u_v, V_v = build_u_V(H_v, ref_val, h_c_abs)

        _, _, _, _, _, resid = fit_bilinear_bounded(u_v, V_v, b_v)
        sse = float(np.sum(resid ** 2))
        sse_list.append(sse)
        n_list.append(len(idx))

    sse_arr = np.array(sse_list, dtype=float)
    valid_sse = np.isfinite(sse_arr)

    if not valid_sse.any():
        return {
            "tau_production": tau_production,
            "tau_best": None,
            "sse_flatness": None,
            "sse_curve": {"tau": list(range(TAU_MAX + 1)), "sse": sse_list, "n": n_list},
            "verdict_b": "insufficient data — SSE curve undefined",
        }

    tau_best = int(np.nanargmin(sse_arr))
    sse_min = float(np.nanmin(sse_arr))
    sse_max = float(np.nanmax(sse_arr))
    sse_flatness = float((sse_max - sse_min) / sse_min) if sse_min > 0 else 0.0

    if sse_flatness < 0.05:
        verdict_b = "tau unidentifiable (flat SSE curve, range < 5%)"
    elif abs(tau_best - tau_production) > 6:
        verdict_b = f"tau possibly mis-set (best tau differs from production by >{abs(tau_best - tau_production)} epochs)"
    else:
        verdict_b = "tau consistent"

    return {
        "tau_production": tau_production,
        "tau_best": tau_best,
        "sse_flatness": round(sse_flatness, 6),
        "sse_curve": {
            "tau": list(range(TAU_MAX + 1)),
            "sse": [round(v, 4) if np.isfinite(v) else None for v in sse_list],
            "n": n_list,
        },
        "verdict_b": verdict_b,
    }


# ── Hypothesis (c): elastic-dominated out-of-sample test ─────────────────────

def hyp_c_elastic_test(layer: str, H_abs_full: np.ndarray, b_cum_full: np.ndarray,
                        dates_full: np.ndarray, ref_val: float, h_c_abs: float,
                        tau_production: int, dense_era_end: pd.Timestamp):
    """Test whether elastic-only model matches full bilinear out-of-sample.

    Dense era <= 2018-12-31, using production τ. Chronological split:
    first 70% of valid epochs = train, last 30% = holdout.

    Returns dict with rmse_full, rmse_elastic, ratio, verdicts.
    """
    H_lag, b_arr, valid, dates_lag = apply_tau_lag(
        H_abs_full, b_cum_full, tau_production, dates_full)

    if dates_lag is not None:
        dense_mask = dates_lag <= dense_era_end
        valid = valid & dense_mask

    idx = np.where(valid)[0]
    n_valid = len(idx)

    if n_valid < 10:
        return "insufficient data - result is undefined"

    # Chronological 70/30 split
    n_train = max(1, int(np.floor(n_valid * 0.70)))
    n_holdout = n_valid - n_train

    if n_holdout < 10:
        return "insufficient data - result is undefined"

    train_idx = idx[:n_train]
    hold_idx = idx[n_train:]

    H_train = H_lag[train_idx]
    b_train = b_arr[train_idx]
    u_train, V_train = build_u_V(H_train, ref_val, h_c_abs)

    H_hold = H_lag[hold_idx]
    b_hold = b_arr[hold_idx]
    u_hold, V_hold = build_u_V(H_hold, ref_val, h_c_abs)

    # --- Full bilinear fit on train ---
    c_full, S_ke_full, S_kv_full, delta_full, _, _ = fit_bilinear_bounded(
        u_train, V_train, b_train)
    b_pred_full = c_full + S_ke_full * u_hold + delta_full * V_hold
    rmse_full = float(np.sqrt(np.mean((b_hold - b_pred_full) ** 2)))

    # --- Elastic-only fit on train ---
    c_el, S_ke_el, _, _ = fit_elastic_bounded(u_train, b_train)
    b_pred_el = c_el + S_ke_el * u_hold
    rmse_elastic = float(np.sqrt(np.mean((b_hold - b_pred_el) ** 2)))

    ratio_rmse = float(rmse_elastic / rmse_full) if rmse_full > 0 else float("inf")

    if rmse_elastic <= rmse_full * 1.05:
        verdict_c = "elastic-dominated regime, S_kv not excited"
    else:
        verdict_c = "inelastic term improves out-of-sample (S_kv genuinely excited)"

    # Holdout date range
    if dates_lag is not None:
        hold_dates = dates_lag[hold_idx]
        hdr_start = str(pd.Timestamp(hold_dates[0]).date())
        hdr_end = str(pd.Timestamp(hold_dates[-1]).date())
    else:
        hdr_start = hdr_end = "unknown"

    return {
        "rmse_full_mm": round(rmse_full, 4),
        "rmse_elastic_mm": round(rmse_elastic, 4),
        "ratio_elastic_over_full": round(ratio_rmse, 4),
        "n_train": n_train,
        "n_holdout": n_holdout,
        "S_ke_mm_per_m": round(S_ke_full, 5),
        "S_kv_mm_per_m": round(S_kv_full, 5),
        "holdout_date_range": [hdr_start, hdr_end],
        "verdict_c": verdict_c,
    }


# ── SSE plot ─────────────────────────────────────────────────────────────────

def plot_sse_curve(layer: str, hyp_b_result: dict, out_path: Path):
    """Export SSE vs τ curve PNG.

    Standards: font >= 14 pt, axis labels with units, grid on, tight layout,
    300 dpi, tab:blue for the curve.
    """
    tau_list = hyp_b_result["sse_curve"]["tau"]
    sse_list = hyp_b_result["sse_curve"]["sse"]
    tau_prod = hyp_b_result["tau_production"]
    tau_best = hyp_b_result["tau_best"]

    # Convert τ (epochs) to days (1 epoch = 5 days)
    days_list = [t * 5 for t in tau_list]
    sse_arr = np.array([v if v is not None else np.nan for v in sse_list], dtype=float)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(days_list, sse_arr, color="tab:blue", linewidth=1.8, label="SSE(τ)")

    if tau_best is not None:
        ax.axvline(tau_best * 5, color="tab:orange", linewidth=1.5, linestyle="--",
                   label=f"τ_best = {tau_best} ep ({tau_best * 5} days)")
    ax.axvline(tau_prod * 5, color="tab:red", linewidth=1.5, linestyle=":",
               label=f"τ_production = {tau_prod} ep ({tau_prod * 5} days)")

    ax.set_xlabel("τ (days)", fontsize=14)
    ax.set_ylabel("SSE (mm²)", fontsize=14)
    ax.set_title(f"Layer {layer} — SSE vs τ (dense era ≤ 2018-12-31)", fontsize=15)
    ax.tick_params(labelsize=13)
    ax.legend(fontsize=13)
    ax.grid(True, alpha=0.4)

    # Flatness annotation
    if hyp_b_result["sse_flatness"] is not None:
        ax.text(0.98, 0.96,
                f"flatness = {hyp_b_result['sse_flatness']:.4f}\n{hyp_b_result['verdict_b']}",
                transform=ax.transAxes, ha="right", va="top",
                fontsize=11, bbox=dict(boxstyle="round", fc="white", alpha=0.75))

    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"    PNG: {out_path}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 75)
    print("Task 6.2 — F1/T1 Hypotheses (b) τ-sensitivity + (c) elastic-dominated")
    print("=" * 75)

    # 1. Load production τ values
    with open(RESULT_JSON) as f:
        prod = json.load(f)
    tau_prod_dict = {lyr: prod["layers"][lyr]["tau_opt"] for lyr in prod["layers"]}
    print(f"\n  Production τ from: {RESULT_JSON.name}")
    print(f"  F1 tau_opt = {tau_prod_dict['F1']}   T1 tau_opt = {tau_prod_dict['T1']}")

    # Cross-check against TUKU_storage_params.json
    sp_path = OUT_JSON_DIR / "TUKU_storage_params.json"
    with open(sp_path) as f:
        sp = json.load(f)
    for lyr in ["F1", "T1"]:
        tau_sp = sp["per_layer"][lyr]["tau_opt"]
        tau_gv = tau_prod_dict[lyr]
        match = "OK" if tau_sp == tau_gv else f"MISMATCH (storage_params={tau_sp})"
        print(f"    {lyr}: tau_opt={tau_gv} cross-check={match}")

    # Load hypothesis (a) reference
    with open(BELOW_FLOOR_JSON) as f:
        hyp_a = json.load(f)

    # 2. Load MLCW increments (gap-aware cumulative, census guard)
    mlcw_inc = pd.read_feather(INC_DIR / "mlcw_diff_cleaned.feather")
    mlcw_inc["datetime"] = pd.to_datetime(mlcw_inc["datetime"]).astype("datetime64[ns]")
    mlcw_inc = mlcw_inc.sort_values("datetime").reset_index(drop=True)
    for col in [c for c in mlcw_inc.columns if c != "datetime"]:
        census(mlcw_inc[col].values, layer=col, enforce_guard=True)
        mlcw_inc[f"_cum_{col}"] = gap_aware_cumulative(mlcw_inc[col].values)
    master = pd.DataFrame({"datetime": mlcw_inc["datetime"].copy()})
    dates_full = mlcw_inc["datetime"].values  # numpy datetime64 array

    # 3. Process each layer
    output_layers = {}
    for layer in ["F1", "T1"]:
        print(f"\n{'─'*60}")
        print(f"  Layer {layer}")
        tau_production = tau_prod_dict[layer]

        # Load arrays
        H_abs_full, b_cum_full, ref_val, h_c_abs = load_layer_arrays(
            layer, mlcw_inc, master)

        print(f"  ref_val={ref_val:.4f} m  h_c_abs={h_c_abs:.4f} m")

        # --- Hypothesis (b): τ-sensitivity ---
        print(f"  Running hypothesis (b): τ grid 0..{TAU_MAX} ...")
        hyp_b = hyp_b_tau_sensitivity(
            layer, H_abs_full, b_cum_full, dates_full,
            ref_val, h_c_abs, tau_production, DENSE_ERA_END)

        print(f"    tau_production={hyp_b['tau_production']}  "
              f"tau_best={hyp_b['tau_best']}  "
              f"sse_flatness={hyp_b['sse_flatness']}")
        print(f"    Verdict (b): {hyp_b['verdict_b']}")

        # Plot
        png_path = OUT_PLOT_DIR / f"{layer}_tau_sse.png"
        plot_sse_curve(layer, hyp_b, png_path)

        # --- Hypothesis (c): elastic-dominated test ---
        print(f"  Running hypothesis (c): elastic-dominated test (prod τ={tau_production}) ...")
        hyp_c = hyp_c_elastic_test(
            layer, H_abs_full, b_cum_full, dates_full,
            ref_val, h_c_abs, tau_production, DENSE_ERA_END)

        if isinstance(hyp_c, str):
            print(f"    {hyp_c}")
        else:
            print(f"    n_train={hyp_c['n_train']}  n_holdout={hyp_c['n_holdout']}")
            print(f"    RMSE_full={hyp_c['rmse_full_mm']:.4f} mm  "
                  f"RMSE_elastic={hyp_c['rmse_elastic_mm']:.4f} mm  "
                  f"ratio={hyp_c['ratio_elastic_over_full']:.4f}")
            print(f"    S_ke={hyp_c['S_ke_mm_per_m']:.5f}  S_kv={hyp_c['S_kv_mm_per_m']:.5f}")
            print(f"    Holdout: {hyp_c['holdout_date_range']}")
            print(f"    Verdict (c): {hyp_c['verdict_c']}")

        output_layers[layer] = {
            "hypothesis_b": hyp_b,
            "hypothesis_c": hyp_c,
        }

    # 4. Assemble and write JSON
    output = {
        "metadata": {
            "date": "2026-06-11",
            "task": "6.2",
            "dense_era_end": "2018-12-31",
            "tau_source": str(RESULT_JSON),
            "references": [
                "f1t1_below_floor.json hypothesis (a): V active, head 3.36 m below h_c on ~48% epochs",
                "TUKU_storage_params.json: F1 bulk_ratio=1.64, T1 bulk_ratio=2.03 (below floor ~3)",
            ],
            "physical_question": (
                "F1 and T1 have inelastic/elastic bulk ratios below the physical floor of ~3. "
                "Hypothesis (a) confirmed V is active (head drops to h_c on ~48% of epochs). "
                "This script tests (b) whether tau is unidentifiable and (c) whether V actually "
                "improves out-of-sample prediction — i.e., whether the low ratio reflects "
                "genuine near-elastic behavior rather than model mis-specification."
            ),
        },
        "layers": output_layers,
    }

    out_path = OUT_JSON_DIR / "f1t1_hypotheses.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n{'='*75}")
    print(f"  Written: {out_path}")

    # 5. Compact summary table
    print(f"\n{'─'*75}")
    print(f"{'SUMMARY TABLE':^75}")
    print(f"{'─'*75}")
    print(f"{'Layer':<6} | {'tau_prod':>8} | {'tau_best':>8} | {'sse_flat':>8} | "
          f"{'verdict_b':<45}")
    print(f"{'─'*75}")
    for lyr in ["F1", "T1"]:
        hb = output_layers[lyr]["hypothesis_b"]
        print(f"{lyr:<6} | {hb['tau_production']:>8} | "
              f"{str(hb['tau_best']):>8} | "
              f"{str(hb['sse_flatness']):>8} | "
              f"{hb['verdict_b']:<45}")
    print(f"{'─'*75}")
    print(f"{'Layer':<6} | {'RMSE_full':>10} | {'RMSE_elast':>10} | {'ratio':>6} | "
          f"{'verdict_c':<40}")
    print(f"{'─'*75}")
    for lyr in ["F1", "T1"]:
        hc = output_layers[lyr]["hypothesis_c"]
        if isinstance(hc, str):
            print(f"{lyr:<6} | {'—':>10} | {'—':>10} | {'—':>6} | {hc:<40}")
        else:
            print(f"{lyr:<6} | {hc['rmse_full_mm']:>10.4f} | "
                  f"{hc['rmse_elastic_mm']:>10.4f} | "
                  f"{hc['ratio_elastic_over_full']:>6.3f} | "
                  f"{hc['verdict_c']:<40}")
    print(f"{'─'*75}")

    # 6. Re-read JSON and verify
    print(f"\n  RE-READ verification:")
    with open(out_path) as f:
        persisted = json.load(f)
    for lyr in ["F1", "T1"]:
        hb_p = persisted["layers"][lyr]["hypothesis_b"]
        hc_p = persisted["layers"][lyr]["hypothesis_c"]
        hb_c = output_layers[lyr]["hypothesis_b"]
        hc_c = output_layers[lyr]["hypothesis_c"]

        # Check hypothesis_b key values
        tau_match = hb_p["tau_best"] == hb_c["tau_best"]
        flat_match = hb_p["sse_flatness"] == hb_c["sse_flatness"]
        if isinstance(hc_c, str):
            rmse_match = (hc_p == hc_c)
        else:
            rmse_match = (
                abs(hc_p["rmse_full_mm"] - hc_c["rmse_full_mm"]) < 1e-6
                and abs(hc_p["rmse_elastic_mm"] - hc_c["rmse_elastic_mm"]) < 1e-6
            )
        ok = tau_match and flat_match and rmse_match
        print(f"    {lyr}: tau_match={tau_match}, flatness_match={flat_match}, "
              f"rmse_match={rmse_match} => {'VERIFIED' if ok else 'MISMATCH'}")

    print(f"\n  PNGs:")
    for lyr in ["F1", "T1"]:
        p = OUT_PLOT_DIR / f"{lyr}_tau_sse.png"
        print(f"    {'EXISTS' if p.exists() else 'MISSING'}: {p}")


if __name__ == "__main__":
    main()
