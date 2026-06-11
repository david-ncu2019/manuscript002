"""
13_holdout_method_bakeoff.py — Three-method held-out bake-off for gap-fill method selection.

Phase 0.1 of super_plan_2026-06-09.md.  Decision Point 1: which method fills gaps best?

Three methods evaluated on two holdout designs (middle gap, end gap) × 6 layers:

  M1 — InSAR/GPS carrier:   b = a * d_surface + c          (a >= 0)
  M2 — Bilinear Terzaghi:    b = c + S_ke * u + delta * V   (Phase 0.0 fitter)
  M3 — Baseline:             middle gap → linear interpolation
                             end gap    → linear trend extrapolation

Outputs:
  tau_demo_TUKU/data/holdout_split_definition.json   — split indices
  tau_demo_TUKU/results/holdout_bakeoff.json          — per-layer, per-design RMSE + winner

Usage:
  PYTHONPATH="" conda run -n fafalab2 python tau_demo_TUKU/13_holdout_method_bakeoff.py
"""

from __future__ import annotations

import datetime
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

from ihmf_model_v3 import compute_virgin_term, compute_r2_cumulative, fit_two_regressor_nnls_X
from scripts.guardrails import validate_sign_constraints, GuardrailViolation
sys.path.insert(0, str(ROOT / "tau_demo_TUKU"))
from gap_aware_cumsum import gap_aware_cumulative, census, GapFractionExceeded

warnings.filterwarnings("ignore", category=UserWarning)

# ── Config ──────────────────────────────────────────────────────────────────────
RESULT_JSON = ROOT / "results" / "ihmf" / "v3" / "verification_20260609_intercept" / "TUKU_gps_v3_results.json"
TAU_DEMO    = ROOT / "tau_demo_TUKU" / "data"
INC_DIR     = TAU_DEMO / "incremental_data"
OUT_JSON    = ROOT / "tau_demo_TUKU" / "results" / "holdout_bakeoff.json"
SPLIT_JSON  = ROOT / "tau_demo_TUKU" / "data" / "holdout_split_definition.json"
REF_DATE    = pd.Timestamp("2015-01-16")

WELL_CONFIG = [
    ("F1", "HONGLUN_gwl_timeseries.feather", "09050111"),
    ("T1", "HONGLUN_gwl_timeseries.feather", "09050111"),
    ("F2", "TUKU_gwl_timeseries.feather",   "09050321"),
    ("T2", "LUNZI_gwl_timeseries.feather",   "09170121"),
    ("F3", "TUKU_gwl_timeseries.feather",   "09050331"),
    ("F4", "LIUZHUANG_gwl_timeseries.feather", "09080251"),
]

OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
SPLIT_JSON.parent.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════════════
# Task 0.1.1 — Build aligned arrays + holdout splits
# ═══════════════════════════════════════════════════════════════════════════════════

def build_aligned_arrays():
    """Load and align all data following diagnose_cumulative_tuku.py pattern.

    Returns
    -------
    arrays : dict[layer -> dict]
        Each dict has keys: datetime, b_cum, H_abs, u, V, d_surface, h_c_abs, tau_opt
    """
    # 1. Load production results (tau_opt per layer)
    with open(RESULT_JSON) as f:
        prod = json.load(f)
    tau_dict = {lyr: prod["layers"][lyr]["tau_opt"] for lyr in prod["layers"]}

    # 2. Load MLCW master timeline
    mlcw_inc = pd.read_feather(INC_DIR / "mlcw_diff_cleaned.feather")
    mlcw_inc["datetime"] = pd.to_datetime(mlcw_inc["datetime"]).astype("datetime64[ns]")
    mlcw_inc = mlcw_inc.sort_values("datetime").reset_index(drop=True)
    # Gap-aware cumulative (D3 fix, Task 1.3): a missing increment is missing
    # knowledge, not zero movement → NaN at that epoch, never a fabricated flat value.
    # Guard (Task 1.3.3): refuse any layer with > 20% missing increments.
    for col in [c for c in mlcw_inc.columns if c != "datetime"]:
        rec = census(mlcw_inc[col].values, layer=col, enforce_guard=True)
        mlcw_inc[f"_cum_{col}"] = gap_aware_cumulative(mlcw_inc[col].values)
        print(f"  gap census {col}: {rec['n_missing']}/{rec['n_total']} missing "
              f"({100*rec['frac_missing']:.2f}%), longest gap {rec['longest_gap_epochs']} epochs")
    master = pd.DataFrame({"datetime": mlcw_inc["datetime"].copy()})

    # 3. Load GPS surface displacement
    gps_raw = pd.read_feather(TAU_DEMO / "TUKU_GPS_timeseries.feather")
    gps_raw.rename(columns={gps_raw.columns[0]: "datetime"}, inplace=True)
    gps_raw["datetime"] = pd.to_datetime(gps_raw["datetime"]).astype("datetime64[ns]")
    gps_raw = gps_raw[["datetime", "modeled"]].sort_values("datetime").reset_index(drop=True)
    gps_aligned = pd.merge_asof(master, gps_raw, on="datetime",
                                 direction="nearest", tolerance=pd.Timedelta("3D"))

    # 4. Build per-layer head + MLCW arrays (R1/R2: zero-reference)
    arrays: dict[str, dict] = {}

    for layer, fname, wellcode in WELL_CONFIG:
        # Load GWL
        gwl = pd.read_feather(TAU_DEMO / fname)
        gwl["datetime"] = pd.to_datetime(gwl["datetime"]).astype("datetime64[ns]")
        gwl = gwl[["datetime", wellcode]].dropna(subset=[wellcode])
        gwl = gwl.sort_values("datetime").reset_index(drop=True)

        # Zero-reference: compute ref_val
        gwl_indexed = gwl.set_index("datetime")[wellcode]
        avail = gwl_indexed.dropna()
        pre_ref = avail.index[avail.index <= REF_DATE]
        if len(pre_ref) == 0:
            print(f"  {layer}: SKIP — no pre-REF_DATE GWL data")
            continue
        ref_val = float(avail.loc[pre_ref[-1]])

        # h_c: lowest absolute head before REF_DATE
        pre_ref_vals = gwl[gwl["datetime"] < REF_DATE][wellcode].dropna()
        if len(pre_ref_vals) >= 10:
            h_c_abs = float(pre_ref_vals.min())
        else:
            h_c_abs = float(gwl[wellcode].dropna().min())
            print(f"  WARN: <10 pre-REF_DATE points for {wellcode} layer {layer}")

        # Align GWL to master
        gwl_aligned = pd.merge_asof(master, gwl, on="datetime",
                                     direction="nearest", tolerance=pd.Timedelta("3D"))
        H_abs_full = gwl_aligned[wellcode].values.astype(float)

        # Cumulative MLCW
        b_cum_full = mlcw_inc[f"_cum_{layer}"].values.astype(float)

        # GPS d_surface
        d_surface_full = gps_aligned["modeled"].values.astype(float)

        arrays[layer] = {
            "datetime":    master["datetime"].values.copy(),
            "H_abs":       H_abs_full,
            "b_cum":       b_cum_full,
            "d_surface":   d_surface_full,
            "h_c_abs":     h_c_abs,
            "H_ref":       ref_val,
            "tau_opt":     tau_dict.get(layer, 0),
        }

    # 5. Apply step1_mask (GWL + MLCW jointly valid — no GPS requirement)
    T_full = len(master)
    step1_mask = np.ones(T_full, dtype=bool)
    for layer in arrays:
        step1_mask &= ~np.isnan(arrays[layer]["H_abs"])
        step1_mask &= ~np.isnan(arrays[layer]["b_cum"])

    print(f"step1_mask: {step1_mask.sum()} of {T_full} epochs "
          f"({int((~step1_mask).sum())} dropped)")

    # Filter all arrays
    for layer in arrays:
        for key in ["datetime", "H_abs", "b_cum", "d_surface"]:
            arrays[layer][key] = arrays[layer][key][step1_mask]

    # 6. Build τ-lagged head u(t) = H(t-τ) - H_ref and V(t)
    #    LAG-PAIRING INVARIANT (super_plan_2026-06-10 Task 1.1, Appendix-grade):
    #    a response observed at epoch index i pairs with the head observed at index i-τ.
    #    With arrays of equal original length N:
    #        response (b, carrier d, dates) : slice [τ : N]   (length N-τ)
    #        driver   (head → u, V)         : slice [0 : N-τ] (length N-τ)
    #    The OLD code sliced BOTH arrays as [τ:], shifting them together → zero lag.
    #    V's running minimum runs over the DRIVER's time axis (the sediment remembers
    #    the deepest head it felt, delayed by the same diffusion lag).
    for layer in arrays:
        tau = arrays[layer]["tau_opt"]
        H_abs_full = arrays[layer]["H_abs"]
        h_c_abs = arrays[layer]["h_c_abs"]
        H_ref = arrays[layer]["H_ref"]
        T_filt = len(H_abs_full)
        T_lag = T_filt - tau

        # Driver slice: head at i-τ  →  H_abs_full[0 : N-τ]
        H_abs_driver = H_abs_full[:T_lag]                 # = H_abs_full[0 : N-τ]
        arrays[layer]["H_abs"] = H_abs_driver              # lagged driver abs head (for V)
        arrays[layer]["H_abs_lagged"] = H_abs_driver       # alias (lagged abs head)
        arrays[layer]["u"] = H_abs_driver - H_ref          # zero-ref lagged head (for S_ke)
        arrays[layer]["V"] = compute_virgin_term(H_abs_driver, h_c_abs)

        # Response slice: b, carrier, dates at i  →  [τ : N]
        arrays[layer]["b_cum"] = arrays[layer]["b_cum"][tau:]
        arrays[layer]["d_surface"] = arrays[layer]["d_surface"][tau:]
        arrays[layer]["datetime"] = arrays[layer]["datetime"][tau:]

    # 7. Report
    for layer in arrays:
        a = arrays[layer]
        n_valid = (~np.isnan(a["b_cum"])).sum()
        print(f"  {layer}: {n_valid} aligned epochs, τ={a['tau_opt']}, "
              f"b_range=[{np.nanmin(a['b_cum']):.1f}, {np.nanmax(a['b_cum']):.1f}] mm")

    return arrays


# ═══════════════════════════════════════════════════════════════════════════════════
# Task 0.1.1 continued — Define holdout splits
# ═══════════════════════════════════════════════════════════════════════════════════

def define_holdout_splits(arrays: dict) -> dict:
    """Define middle-gap (40-70%) and end-gap (last 30%) holdout designs.

    Splits are computed per-layer because each layer has different length
    after τ-lagging (different τ_opt values).

    Returns dict suitable for JSON serialization.
    """
    splits = {
        "description": "Holdout splits for TUKU bake-off (Phase 0.1)",
        "design": "40%-70% middle gap + last 30% end gap",
        "per_layer": {},
    }

    for layer in arrays:
        N = len(arrays[layer]["b_cum"])
        mid_start = int(N * 0.40)
        mid_end   = int(N * 0.70)
        end_start = int(N * 0.70)

        splits["per_layer"][layer] = {
            "N_total": N,
            "tau_opt": arrays[layer]["tau_opt"],
            "middle_gap": {
                "gap_start": mid_start,
                "gap_end": mid_end,
                "n_gap": mid_end - mid_start,
                "n_train": mid_start + (N - mid_end),
            },
            "end_gap": {
                "gap_start": end_start,
                "gap_end": N,
                "n_gap": N - end_start,
                "n_train": end_start,
            },
        }

    # Print summary for the first layer
    first = list(arrays.keys())[0]
    print(f"\nHoldout splits (per-layer, shown for {first}):")
    for design_key in ["middle_gap", "end_gap"]:
        d = splits["per_layer"][first][design_key]
        print(f"  {design_key}: gap=[{d['gap_start']}, {d['gap_end']}) = {d['n_gap']} epochs, "
              f"train={d['n_train']} epochs")

    return splits


# ═══════════════════════════════════════════════════════════════════════════════════
# Task 0.1.2 — Three-method evaluator
# ═══════════════════════════════════════════════════════════════════════════════════

def evaluate_methods(arrays: dict, splits: dict) -> dict:
    """Run all three methods on both holdout designs for all layers.

    Split indices are computed per-layer because each layer has different length
    after τ-lagging (different τ_opt values).

    Returns bake-off results dict.
    """
    layers = list(arrays.keys())
    results: dict[str, dict] = {}

    for layer in layers:
        a = arrays[layer]
        b_all = a["b_cum"]
        u_all = a["u"]
        V_all = a["V"]
        d_all = a["d_surface"]

        # Per-layer split indices (each layer has different N after τ-lagging)
        N = len(b_all)
        mid_start = int(N * 0.40)
        mid_end   = int(N * 0.70)
        end_start = int(N * 0.70)

        for design_key in ["middle_gap", "end_gap"]:
            if design_key == "middle_gap":
                train_idx = np.array(list(range(0, mid_start)) + list(range(mid_end, N)))
                gap_idx   = np.array(list(range(mid_start, mid_end)))
            else:
                train_idx = np.array(list(range(0, end_start)))
                gap_idx   = np.array(list(range(end_start, N)))

            # Skip if insufficient data
            train_valid = np.isfinite(b_all[train_idx])
            gap_valid   = np.isfinite(b_all[gap_idx])
            if train_valid.sum() < 10:
                print(f"  {layer}/{design_key}: SKIP — <10 valid training epochs")
                continue

            b_train = b_all[train_idx].copy()
            b_gap_obs = b_all[gap_idx].copy()

            # ── M1: GPS carrier ──
            rmse_m1, _ = _eval_carrier(d_all, b_all, train_idx, gap_idx)

            # ── M2: Bilinear Terzaghi ──
            rmse_m2, m2_params = _eval_bilinear(
                u_all, V_all, b_all, a["h_c_abs"], a["H_ref"],
                train_idx, gap_idx, layer
            )

            # ── M3: Baseline ──
            if design_key == "middle_gap":
                rmse_m3 = _eval_interpolation(b_all, train_idx, gap_idx)
            else:
                rmse_m3 = _eval_trend_extrapolation(b_all, train_idx, gap_idx)

            # Compute skill scores
            skill_m1 = 1.0 - rmse_m1 / rmse_m3 if rmse_m3 > 1e-10 else 0.0
            skill_m2 = 1.0 - rmse_m2 / rmse_m3 if rmse_m3 > 1e-10 else 0.0

            if layer not in results:
                results[layer] = {}

            results[layer][design_key] = {
                "rmse_carrier_mm":    round(rmse_m1, 4),
                "rmse_bilinear_mm":   round(rmse_m2, 4),
                "rmse_baseline_mm":   round(rmse_m3, 4),
                "skill_carrier":      round(skill_m1, 4),
                "skill_bilinear":     round(skill_m2, 4),
                "n_train":            len(train_idx),
                "n_gap":              len(gap_idx),
            }
            if m2_params:
                results[layer][design_key]["bilinear_S_ke"] = round(m2_params["S_ke"], 5)
                results[layer][design_key]["bilinear_S_kv"] = round(m2_params["S_kv"], 5)
                results[layer][design_key]["bilinear_r2"]   = round(m2_params["r2"], 4)

            # Print per-layer result
            winner = min(
                ("carrier", rmse_m1), ("bilinear", rmse_m2), ("baseline", rmse_m3),
                key=lambda x: x[1]
            )[0]
            print(f"  {layer:3s} {design_key:11s} | carrier={rmse_m1:7.3f}  "
                  f"bilinear={rmse_m2:7.3f}  baseline={rmse_m3:7.3f} mm  → {winner}")

    return results


def _eval_carrier(d_surface, b_all, train_idx, gap_idx):
    """M1: b = a * d_surface + c, a >= 0."""
    d_train = d_surface[train_idx]
    b_train = b_all[train_idx]
    mask = np.isfinite(d_train) & np.isfinite(b_train)
    if mask.sum() < 5:
        return float("inf"), None

    # Fit: lsq_linear with a >= 0, c unconstrained
    # b = a*d + c → design matrix [d, 1]
    A = np.column_stack([d_train[mask], np.ones(mask.sum())])
    result = lsq_linear(A, b_train[mask], bounds=(np.array([0, -np.inf]), np.array([np.inf, np.inf])))
    a, c = result.x[0], result.x[1]

    # Predict on gap
    d_gap = d_surface[gap_idx]
    gap_mask = np.isfinite(d_gap)
    if gap_mask.sum() == 0:
        return float("inf"), None
    b_pred = a * d_gap[gap_mask] + c
    b_gap_obs = b_all[gap_idx][gap_mask]
    rmse = float(np.sqrt(np.mean((b_gap_obs - b_pred) ** 2)))
    return rmse, {"a": a, "c": c}


def _eval_bilinear(u_all, V_all, b_all, h_c_abs, H_ref, train_idx, gap_idx, layer):
    """M2: b = c + S_ke * u + delta * V via fit_two_regressor_nnls_X.

    u and V are pre-computed in build_aligned_arrays: u is zero-referenced
    lagged head, V is min(0, cummin(H_abs_lagged) - h_c_abs) — datum cancels.
    """
    u_train = u_all[train_idx]
    V_train = V_all[train_idx]
    b_train = b_all[train_idx]
    mask = np.isfinite(u_train) & np.isfinite(V_train) & np.isfinite(b_train)
    if mask.sum() < 10:
        return float("inf"), None

    try:
        S_ke, S_kv, delta, c_intercept, resid_sq, b_pred_train = fit_two_regressor_nnls_X(
            u_train[mask], V_train[mask], b_train[mask], with_intercept=True
        )
        r2_train = compute_r2_cumulative(b_train[mask], b_pred_train)
    except Exception as e:
        print(f"    M2 fit error {layer}: {e}")
        return float("inf"), None

    # Guardrail: sign constraints
    try:
        validate_sign_constraints(S_ke, S_kv, layer, "TUKU")
    except GuardrailViolation as e:
        print(f"    M2 guardrail violation {layer}: {e}")
        return float("inf"), None

    # Predict on gap
    # u_gap and V_gap are computed from GWL data DURING the gap.
    # V_gap uses cummin over [training ∪ gap so far] — this correctly models
    # new inelastic consolidation if head drops below the previous minimum.
    u_gap = u_all[gap_idx]
    V_gap = V_all[gap_idx]
    gap_mask = np.isfinite(u_gap) & np.isfinite(V_gap)
    if gap_mask.sum() == 0:
        return float("inf"), None

    b_pred = c_intercept + S_ke * u_gap[gap_mask] + delta * V_gap[gap_mask]
    b_gap_obs = b_all[gap_idx][gap_mask]
    rmse = float(np.sqrt(np.mean((b_gap_obs - b_pred) ** 2)))

    fit_params = {
        "S_ke": S_ke, "S_kv": S_kv, "delta": delta,
        "c_intercept": c_intercept, "r2": r2_train,
    }
    return rmse, fit_params


def _eval_interpolation(b_all, train_idx, gap_idx):
    """M3 middle-gap: linear interpolation between bracketing observed values."""
    b_gap_obs = b_all[gap_idx]
    mask = np.isfinite(b_gap_obs)
    if mask.sum() < 2:
        return float("inf")

    # Bracketing values: last valid before gap, first valid after gap
    b_before = b_all[train_idx]
    before_valid = np.isfinite(b_before)
    if not before_valid.any():
        return float("inf")
    b_left = b_before[before_valid][-1]

    after_idx = np.arange(gap_idx[-1] + 1, len(b_all))
    if len(after_idx) > 0:
        b_after = b_all[after_idx]
        after_valid = np.isfinite(b_after)
        b_right = b_after[after_valid][0] if after_valid.any() else b_left
    else:
        b_right = b_left  # end gap — fall back to constant

    # Linear interpolation over gap positions
    gap_len = len(gap_idx)
    interp = np.linspace(b_left, b_right, gap_len + 2)[1:-1]  # exclude endpoints
    rmse = float(np.sqrt(np.mean((b_gap_obs[mask] - interp[mask]) ** 2)))
    return rmse


def _eval_trend_extrapolation(b_all, train_idx, gap_idx):
    """M3 end-gap: linear trend extrapolation of training data."""
    b_train = b_all[train_idx]
    mask_train = np.isfinite(b_train)
    if mask_train.sum() < 5:
        return float("inf")

    # Fit linear trend: b = slope * t + intercept
    t_train = np.arange(len(train_idx), dtype=float)[mask_train]
    A = np.column_stack([t_train, np.ones_like(t_train)])
    coef, _, _, _ = np.linalg.lstsq(A, b_train[mask_train], rcond=None)
    slope, intercept = coef[0], coef[1]

    # Extrapolate to gap
    t_gap = np.arange(len(train_idx), len(train_idx) + len(gap_idx), dtype=float)
    b_pred = slope * t_gap + intercept

    b_gap_obs = b_all[gap_idx]
    mask_gap = np.isfinite(b_gap_obs)
    if mask_gap.sum() == 0:
        return float("inf")
    rmse = float(np.sqrt(np.mean((b_gap_obs[mask_gap] - b_pred[mask_gap]) ** 2)))
    return rmse


# ═══════════════════════════════════════════════════════════════════════════════════
# Task 0.1.3 — Select primary method
# ═══════════════════════════════════════════════════════════════════════════════════

def select_primary_method(bakeoff: dict) -> dict:
    """Assign primary gap-fill method per layer based on average RMSE across designs."""
    primary = {}
    for layer in bakeoff:
        # Average RMSE across both designs
        rmse_carrier = []
        rmse_bilinear = []
        rmse_baseline = []
        for design_key in ["middle_gap", "end_gap"]:
            if design_key in bakeoff[layer]:
                d = bakeoff[layer][design_key]
                rmse_carrier.append(d["rmse_carrier_mm"])
                rmse_bilinear.append(d["rmse_bilinear_mm"])
                rmse_baseline.append(d["rmse_baseline_mm"])

        if not rmse_carrier:
            primary[layer] = "none — insufficient data"
            continue

        avg_carrier  = np.mean(rmse_carrier)
        avg_bilinear = np.mean(rmse_bilinear)
        avg_baseline = np.mean(rmse_baseline)

        # Winner = lowest average RMSE
        methods = {
            "carrier":  avg_carrier,
            "bilinear": avg_bilinear,
            "baseline":   avg_baseline,
        }
        winner = min(methods, key=methods.get)
        primary[layer] = winner

        print(f"  {layer}: avg RMSE carrier={avg_carrier:.3f}  "
              f"bilinear={avg_bilinear:.3f}  baseline={avg_baseline:.3f} mm  → {winner}")

    return primary


# ═══════════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 75)
    print("Phase 0.1 — Three-Method Held-Out Bake-Off (Decision Point 1)")
    print("=" * 75)

    # Task 0.1.1
    print("\n── Task 0.1.1: Building aligned arrays ──")
    arrays = build_aligned_arrays()
    splits = define_holdout_splits(arrays)

    # Save split definition
    with open(SPLIT_JSON, "w") as f:
        json.dump(splits, f, indent=2, default=_json_default)
    print(f"  Saved: {SPLIT_JSON}")

    # Task 0.1.2
    print(f"\n── Task 0.1.2: Three-method evaluation ──")
    print(f"  {'Layer':4s} {'Design':11s} | {'carrier':>7s}  {'bilinear':>8s}  {'baseline':>8s}  → winner")
    print(f"  {'-'*4} {'-'*11} | {'-'*7}  {'-'*8}  {'-'*8}  {'-'*7}")
    bakeoff = evaluate_methods(arrays, splits)

    # Task 0.1.3
    print(f"\n── Task 0.1.3: Primary method selection ──")
    primary = select_primary_method(bakeoff)

    # Count wins
    win_counts = {}
    for layer, method in primary.items():
        win_counts[method] = win_counts.get(method, 0) + 1
    print(f"\n  Win counts: {win_counts}")

    # Decision Point 1 classification
    carrier_wins = win_counts.get("carrier", 0)
    if carrier_wins >= 3:
        verdict = "CARRIER-PRIMARY"
    elif win_counts:
        verdict = "MIXED — per-layer method map"
    else:
        verdict = "ALL-FAIL — no method beats baseline"
    print(f"  Decision Point 1: {verdict}")

    # Assemble output
    output = {
        "metadata": {
            "description": "Three-method held-out bake-off for gap-fill method selection",
            "decision_point": "Decision Point 1 — super_plan_2026-06-11.md Phase 0.1",
            "verdict": verdict,
            "station": "TUKU",
            "date": datetime.date.today().isoformat(),
        },
        "holdout_splits": splits,
        "per_layer": bakeoff,
        "primary_method": primary,
        "win_counts": win_counts,
    }

    with open(OUT_JSON, "w") as f:
        json.dump(output, f, indent=2, default=_json_default)
    print(f"\n  Saved: {OUT_JSON}")

    # Print summary table
    print(f"\n{'='*75}")
    print("Summary Table — Held-Out RMSE (mm) and Primary Method")
    print(f"{'='*75}")
    header = f"{'Layer':5s} | {'carrier_mid':>11s} | {'bilinear_mid':>12s} | {'baseline_mid':>12s} | {'carrier_end':>11s} | {'bilinear_end':>12s} | {'baseline_end':>12s} | Primary"
    print(header)
    print("-" * len(header))
    for layer in ["F1", "T1", "F2", "T2", "F3", "F4"]:
        if layer not in bakeoff:
            continue
        mid = bakeoff[layer].get("middle_gap", {})
        end = bakeoff[layer].get("end_gap", {})
        print(f"{layer:5s} | {mid.get('rmse_carrier_mm', float('nan')):11.3f} | "
              f"{mid.get('rmse_bilinear_mm', float('nan')):12.3f} | "
              f"{mid.get('rmse_baseline_mm', float('nan')):12.3f} | "
              f"{end.get('rmse_carrier_mm', float('nan')):11.3f} | "
              f"{end.get('rmse_bilinear_mm', float('nan')):12.3f} | "
              f"{end.get('rmse_baseline_mm', float('nan')):12.3f} | "
              f"{primary.get(layer, '?')}")

    print(f"\nDecision Point 1 verdict: {verdict}")
    return output


def _json_default(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, pd.Timestamp):
        return str(obj)
    raise TypeError(f"Not JSON serialisable: {type(obj)}")


if __name__ == "__main__":
    main()
