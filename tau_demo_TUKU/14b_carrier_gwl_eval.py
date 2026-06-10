"""
14b_carrier_gwl_eval.py — Evaluate GWL residual term for GPS carrier model.

Tests whether adding d_k * u(t) to the carrier model improves held-out gap-fill
skill.  Uses the same Phase 0.1 holdout splits (middle 40-70%, end 70-100%).

Three models per layer:
  M_carrier    : b = a * d_GPS + c                     (a >= 0)
  M_carrier_gwl: b = a * d_GPS + d * u + c             (a >= 0, d >= 0)
  M_bilinear   : b = c + S_ke * u + delta * V           (reference)

Decision rule: adopt GWL term only where average held-out RMSE improves > 5%.

Output: tau_demo_TUKU/results/carrier_gwl_eval.json

Usage:
  PYTHONPATH="" conda run -n fafalab2 python tau_demo_TUKU/14b_carrier_gwl_eval.py
"""

from __future__ import annotations

import json, sys, warnings
from pathlib import Path

import numpy as np
from scipy.optimize import lsq_linear

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "10_ihmf"))
sys.path.insert(0, str(ROOT / "tau_demo_TUKU"))

from ihmf_model_v3 import compute_r2_cumulative
from scripts.guardrails import validate_sign_constraints, GuardrailViolation

# Import build_aligned_arrays from 13_holdout_method_bakeoff.py
import importlib.util
_bakeoff_spec = importlib.util.spec_from_file_location(
    "bakeoff", str(ROOT / "tau_demo_TUKU" / "13_holdout_method_bakeoff.py")
)
_bakeoff = importlib.util.module_from_spec(_bakeoff_spec)
_bakeoff_spec.loader.exec_module(_bakeoff)
build_aligned_arrays = _bakeoff.build_aligned_arrays

warnings.filterwarnings("ignore", category=UserWarning)

OUT_JSON = ROOT / "tau_demo_TUKU" / "results" / "carrier_gwl_eval.json"
LAYERS_ORDER = ["F1", "T1", "F2", "T2", "F3", "F4"]


# ═══════════════════════════════════════════════════════════════════════════════════
# Collinearity check
# ═══════════════════════════════════════════════════════════════════════════════════

def check_collinearity(d_gps: np.ndarray, u: np.ndarray) -> dict:
    """Compute VIF and correlation between GPS and GWL regressors."""
    mask = np.isfinite(d_gps) & np.isfinite(u)
    d = d_gps[mask]; h = u[mask]
    if len(d) < 10:
        return {"vif": float("inf"), "corr": float("nan"), "n": len(d)}
    corr = float(np.corrcoef(d, h)[0, 1])
    # VIF = 1 / (1 - R²) where R² from regressing d_gps ~ u
    # Simplified: if |corr| > 0.9, collinearity is high
    vif = 1.0 / (1.0 - corr**2) if abs(corr) < 1.0 else float("inf")
    return {"vif": round(vif, 2), "corr": round(corr, 4), "n": len(d)}


# ═══════════════════════════════════════════════════════════════════════════════════
# Model fitting
# ═══════════════════════════════════════════════════════════════════════════════════

def fit_carrier(d_gps_train: np.ndarray, b_train: np.ndarray):
    """b = a * d_GPS + c, a >= 0. Returns coefficients only."""
    mask = np.isfinite(d_gps_train) & np.isfinite(b_train)
    if mask.sum() < 5:
        return None
    A = np.column_stack([d_gps_train[mask], np.ones(mask.sum())])
    res = lsq_linear(A, b_train[mask], bounds=(np.array([0, -np.inf]), np.array([np.inf, np.inf])))
    a, c = float(res.x[0]), float(res.x[1])
    b_pred_train = a * d_gps_train + c
    r2 = compute_r2_cumulative(b_train[mask], b_pred_train[mask])
    return {"a": a, "c": c, "r2_train": r2}


def fit_carrier_gwl(d_gps_train: np.ndarray, u_train: np.ndarray, b_train: np.ndarray):
    """b = a * d_GPS + d * u + c, a >= 0, d >= 0. Returns coefficients only."""
    mask = np.isfinite(d_gps_train) & np.isfinite(u_train) & np.isfinite(b_train)
    if mask.sum() < 5:
        return None
    A = np.column_stack([d_gps_train[mask], u_train[mask], np.ones(mask.sum())])
    bounds = (np.array([0, 0, -np.inf]), np.array([np.inf, np.inf, np.inf]))
    res = lsq_linear(A, b_train[mask], bounds=bounds)
    a, d, c = float(res.x[0]), float(res.x[1]), float(res.x[2])
    b_pred_train = a * d_gps_train + d * u_train + c
    r2 = compute_r2_cumulative(b_train[mask], b_pred_train[mask])
    return {"a": a, "d": d, "c": c, "r2_train": r2}


def fit_bilinear_ref(u_train: np.ndarray, V_train: np.ndarray, b_train: np.ndarray, layer: str):
    """b = c + S_ke * u + delta * V, with guardrails. Returns coefficients only."""
    mask = np.isfinite(u_train) & np.isfinite(V_train) & np.isfinite(b_train)
    if mask.sum() < 10:
        return None
    from ihmf_model_v3 import fit_two_regressor_nnls_X
    S_ke, S_kv, delta, c, resid, b_pred_train = fit_two_regressor_nnls_X(
        u_train[mask], V_train[mask], b_train[mask], with_intercept=True
    )
    try:
        validate_sign_constraints(S_ke, S_kv, layer, "TUKU")
    except GuardrailViolation:
        pass
    r2 = compute_r2_cumulative(b_train[mask], b_pred_train)
    return {"S_ke": S_ke, "S_kv": S_kv, "c": c, "r2_train": r2}


def predict_carrier(coef: dict, d_gps_full: np.ndarray) -> np.ndarray:
    """Full-array prediction from carrier coefficients."""
    return coef["a"] * d_gps_full + coef["c"]


def predict_carrier_gwl(coef: dict, d_gps_full: np.ndarray, u_full: np.ndarray) -> np.ndarray:
    """Full-array prediction from carrier+GWL coefficients."""
    return coef["a"] * d_gps_full + coef["d"] * u_full + coef["c"]


def predict_bilinear(coef: dict, u_full: np.ndarray, V_full: np.ndarray) -> np.ndarray:
    """Full-array prediction from bilinear coefficients."""
    return coef["c"] + coef["S_ke"] * u_full + (coef["S_kv"] - coef["S_ke"]) * V_full


# ═══════════════════════════════════════════════════════════════════════════════════
# Main evaluation
# ═══════════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 85)
    print("14b — GWL Residual Term Evaluation for GPS Carrier Model")
    print("=" * 85)

    # 1. Load aligned arrays (from 13_holdout_method_bakeoff.py)
    print("\n── Loading data via build_aligned_arrays() ──")
    arrays = build_aligned_arrays()

    # 2. Collinearity check
    print(f"\n── Collinearity: d_GPS vs u ──")
    print(f"  {'Layer':5s} | {'corr':>8s} | {'VIF':>7s} | {'n':>5s} | Verdict")
    print(f"  {'-'*5} | {'-'*8} | {'-'*7} | {'-'*5} | {'-'*7}")
    collin = {}
    for layer in LAYERS_ORDER:
        a = arrays[layer]
        c = check_collinearity(a["d_surface"], a["u"])
        collin[layer] = c
        verdict = "COLLINEAR ⚠" if c["vif"] > 5 else "OK"
        print(f"  {layer:5s} | {c['corr']:8.4f} | {c['vif']:7.2f} | {c['n']:5d} | {verdict}")

    # 3. Per-layer evaluation on holdout splits
    print(f"\n── Held-out evaluation (Phase 0.1 splits) ──")
    print(f"  {'Layer':5s} {'Design':8s} | {'carrier':>8s} | {'+GWL':>8s} | {'Δ%':>7s} | {'bilinear':>9s} | {'GWL helps?':>10s}")
    print(f"  {'-'*5} {'-'*8} | {'-'*8} | {'-'*8} | {'-'*7} | {'-'*9} | {'-'*10}")

    results = {}
    for layer in LAYERS_ORDER:
        a = arrays[layer]
        b_all = a["b_cum"]
        d_all = a["d_surface"]
        u_all = a["u"]
        V_all = a["V"]
        N = len(b_all)

        mid_start = int(N * 0.40)
        mid_end   = int(N * 0.70)
        end_start = int(N * 0.70)

        results[layer] = {"collinearity": collin[layer]}

        for design_key, train_idx, gap_idx in [
            ("middle", np.array(list(range(0, mid_start)) + list(range(mid_end, N))),
                       np.array(list(range(mid_start, mid_end)))),
            ("end",    np.array(list(range(0, end_start))),
                       np.array(list(range(end_start, N)))),
        ]:
            # Fit on training → coefficients
            fit_c = fit_carrier(d_all[train_idx], b_all[train_idx])
            fit_g = fit_carrier_gwl(d_all[train_idx], u_all[train_idx], b_all[train_idx])
            fit_b = fit_bilinear_ref(u_all[train_idx], V_all[train_idx], b_all[train_idx], layer)

            # Predict on full arrays, evaluate RMSE on gap only
            def gap_rmse(b_pred_full, gap_idx, b_full):
                gap_mask = np.isfinite(b_pred_full[gap_idx]) & np.isfinite(b_full[gap_idx])
                if gap_mask.sum() == 0:
                    return float("inf")
                return float(np.sqrt(np.mean((b_full[gap_idx][gap_mask] - b_pred_full[gap_idx][gap_mask])**2)))

            pred_c = predict_carrier(fit_c, d_all) if fit_c else None
            pred_g = predict_carrier_gwl(fit_g, d_all, u_all) if fit_g else None
            pred_b = predict_bilinear(fit_b, u_all, V_all) if fit_b else None

            rmse_c = gap_rmse(pred_c, gap_idx, b_all) if pred_c is not None else float("inf")
            rmse_g = gap_rmse(pred_g, gap_idx, b_all) if pred_g is not None else float("inf")
            rmse_b = gap_rmse(pred_b, gap_idx, b_all) if pred_b is not None else float("inf")

            delta_pct = (rmse_g - rmse_c) / rmse_c * 100 if rmse_c < float("inf") else 0
            helps = "YES ✓" if delta_pct < -5 else ("no" if delta_pct < 0 else "WORSE ✗")

            print(f"  {layer:5s} {design_key:8s} | {rmse_c:8.3f} | {rmse_g:8.3f} | {delta_pct:+7.1f}% | {rmse_b:9.3f} | {helps:>10s}")

            results[layer][design_key] = {
                "rmse_carrier_mm": round(rmse_c, 4),
                "rmse_carrier_gwl_mm": round(rmse_g, 4),
                "rmse_bilinear_mm": round(rmse_b, 4),
                "delta_pct": round(delta_pct, 2),
                "carrier_a": round(fit_c["a"], 6) if fit_c else None,
                "carrier_c": round(fit_c["c"], 4) if fit_c else None,
                "gwl_a": round(fit_g["a"], 6) if fit_g else None,
                "gwl_d": round(fit_g["d"], 6) if fit_g else None,
                "gwl_c": round(fit_g["c"], 4) if fit_g else None,
            }

    # 4. Per-layer adoption decision
    print(f"\n── Adoption decision (adopt if avg Δ% < -5%) ──")
    adopt = {}
    for layer in LAYERS_ORDER:
        deltas = []
        for dk in ["middle", "end"]:
            if dk in results[layer]:
                deltas.append(results[layer][dk]["delta_pct"])
        avg_delta = np.mean(deltas) if deltas else 0
        adopt[layer] = bool(avg_delta < -5)
        print(f"  {layer}: avg Δ = {avg_delta:+6.1f}%  →  {'ADOPT GWL ✓' if adopt[layer] else 'REJECT GWL — carrier-only'}")

    # 5. Save
    output = {
        "metadata": {
            "description": "GWL residual term evaluation for GPS carrier model",
            "model": "b = a * d_GPS + d * u + c, a >= 0, d >= 0",
            "decision_rule": "adopt GWL if avg held-out RMSE improves > 5%",
            "date": "2026-06-10",
        },
        "collinearity": {lyr: collin[lyr] for lyr in LAYERS_ORDER},
        "per_layer": results,
        "adopt_gwl": adopt,
        "layers_adopting_gwl": [lyr for lyr in LAYERS_ORDER if adopt[lyr]],
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Saved: {OUT_JSON}")

    # Summary
    adopting = output["layers_adopting_gwl"]
    print(f"\n{'='*85}")
    if adopting:
        print(f"GWL term adopted for: {', '.join(adopting)}")
        print(f"Next: PYTHONPATH=\"\" conda run -n fafalab2 python tau_demo_TUKU/14_carrier_reconstruction_tuku.py --use-gwl {','.join(adopting)}")
    else:
        print("GWL term not adopted for any layer — carrier-only model is sufficient.")
        print("No modification to 14_carrier_reconstruction_tuku.py needed.")
    print(f"{'='*85}")


if __name__ == "__main__":
    main()
