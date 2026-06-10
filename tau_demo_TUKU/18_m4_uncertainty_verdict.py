"""
18_m4_uncertainty_verdict.py — MILESTONE M4 (super_plan_2026-06-10.md).

Task 4.1: block-bootstrap 90% prediction intervals for each layer's ADOPTED model.
Task 4.2: apex-goal verdict table (layer x design x {MAE, RMSE, threshold, PASS/FAIL}).

Reuses the M3 machinery EXACTLY (no refit done differently):
  - build_aligned_arrays + build_extra_regressors (M1-corrected lag loader, Script 17/13)
  - candidate_regressors / fit_candidate / predict_candidate / design_indices (Script 17)
The adopted model id per layer is read from the authoritative registry
(hybrid_model_registry.json -> adoption_map.<layer>.adopted_model). For each holdout
design we refit the adopted candidate on that design's TRAINING epochs (identical to how
M3 produced its held-out RMSE) and evaluate on the GAP (held-out) epochs only.

Block bootstrap (Task 4.1.1): calibration residuals r = b_obs - b_pred on TRAINING
epochs (contiguous, finite); resample contiguous blocks of 73 epochs (then 146 if
coverage fails) with replacement to build 1,000 residual paths of length n_gap; add each
to the point prediction over held-out epochs; 5th/95th percentile per epoch = 90% band.

Coverage (4.1.2): fraction of held-out OBSERVED inside band must be >= 0.85, else widen
to block 146; if still < 0.85, label "calibrated to X%" (never silently relabel).

Outputs:
  tau_demo_TUKU/results/m4_uncertainty_verdict.json
  tau_demo_TUKU/results/m4_apex_verdict_table.csv

Usage:
  PYTHONPATH="" conda run -n fafalab2 python tau_demo_TUKU/18_m4_uncertainty_verdict.py
"""
from __future__ import annotations

import json, sys, csv, importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "10_ihmf"))
sys.path.insert(0, str(ROOT / "tau_demo_TUKU"))

# Import Script 17 (M3) as a module — reuse its fitting/prediction machinery verbatim.
_spec = importlib.util.spec_from_file_location(
    "hybrid17", str(ROOT / "tau_demo_TUKU" / "17_hybrid_model_m3.py"))
_m3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m3)

REGISTRY = ROOT / "tau_demo_TUKU" / "results" / "hybrid_model_registry.json"
OUT_JSON = ROOT / "tau_demo_TUKU" / "results" / "m4_uncertainty_verdict.json"
OUT_CSV  = ROOT / "tau_demo_TUKU" / "results" / "m4_apex_verdict_table.csv"

LAYERS_ORDER = ["F1", "T1", "F2", "T2", "F3", "F4"]
DESIGNS = ["middle", "end", "tail"]

# Level-1 thresholds (super_plan_2026-06-10 LEVEL 1 table / Task 4.2.2).
THIN_LAYERS  = {"F1", "T1", "T2", "F4"}        # MAE < 5, RMSE < 10 mm
THICK_LAYERS = {"F2", "F3"}                    # MAE < 10, RMSE < 20 mm
THRESHOLDS = {
    "thin":  {"MAE": 5.0,  "RMSE": 10.0},
    "thick": {"MAE": 10.0, "RMSE": 20.0},
}

# Observed per-layer cumulative range (mm) for the band-width red-flag check.
# (task brief: F1,T1,T2,F4 thin 14.6-25.1; F2,F3 thick 144.8-216.2). Computed live below
# from the loaded b_cum; the brief values are the cross-check.

N_BOOT = 1000
BLOCK_PRIMARY = 73
BLOCK_WIDE = 146
COVERAGE_TARGET = 0.85
RNG_SEED = 20260610


def layer_class(layer: str) -> str:
    return "thin" if layer in THIN_LAYERS else "thick"


def block_bootstrap_band(resid: np.ndarray, point_pred: np.ndarray,
                          block_len: int, n_boot: int, rng: np.random.Generator):
    """Build a 90% band by adding contiguous-block-resampled residual paths to the
    point prediction over the held-out epochs.

    resid       : 1-D calibration residuals (training epochs, contiguous, finite)
    point_pred  : point prediction over the n_gap held-out epochs
    Returns (lo, hi) arrays length n_gap (5th, 95th percentile per epoch).
    """
    n_gap = len(point_pred)
    R = len(resid)
    if R < block_len or n_gap == 0:
        return None, None
    n_blocks = int(np.ceil(n_gap / block_len))
    max_start = R - block_len  # inclusive
    paths = np.empty((n_boot, n_gap), dtype=float)
    for b in range(n_boot):
        starts = rng.integers(0, max_start + 1, size=n_blocks)
        path = np.concatenate([resid[s:s + block_len] for s in starts])[:n_gap]
        paths[b] = point_pred + path
    lo = np.percentile(paths, 5, axis=0)
    hi = np.percentile(paths, 95, axis=0)
    return lo, hi


def main():
    print("=" * 88)
    print("MILESTONE M4 — Uncertainty (block bootstrap) and the Apex Verdict")
    print("=" * 88)

    with open(REGISTRY) as f:
        reg = json.load(f)
    adoption = reg["adoption_map"]

    arrays = _m3.build_aligned_arrays()
    arrays = _m3.build_extra_regressors(arrays)

    rng = np.random.default_rng(RNG_SEED)

    results = {}
    apex_rows = []  # for CSV
    observed_ranges = {}

    for layer in LAYERS_ORDER:
        a = arrays[layer]
        N = len(a["b_cum"])
        adopted = adoption[layer]["adopted_model"]
        tau = adoption[layer]["tau"]
        klass = layer_class(layer)
        thr = THRESHOLDS[klass]

        b_all = a["b_cum"]
        finite_b = b_all[np.isfinite(b_all)]
        obs_range = float(np.nanmax(finite_b) - np.nanmin(finite_b))
        observed_ranges[layer] = round(obs_range, 4)

        results[layer] = {
            "adopted_model": adopted,
            "tau": tau,
            "layer_class": klass,
            "thresholds": thr,
            "observed_range_mm": round(obs_range, 4),
            "N": N,
            "designs": {},
        }

        for design in DESIGNS:
            train_idx, gap_idx = _m3.design_indices(N, design)

            # Refit adopted candidate on this design's training epochs — IDENTICAL to M3.
            coef = _m3.fit_candidate(a, adopted, train_idx)

            # Point predictions on training and held-out (gap) epochs.
            pred_train = _m3.predict_candidate(a, adopted, coef, train_idx)
            obs_train = b_all[train_idx]
            mt = np.isfinite(pred_train) & np.isfinite(obs_train)
            resid_train = (obs_train[mt] - pred_train[mt]).astype(float)  # contiguous order

            pred_gap = _m3.predict_candidate(a, adopted, coef, gap_idx)
            obs_gap = b_all[gap_idx]
            mg = np.isfinite(pred_gap) & np.isfinite(obs_gap)
            obs_g = obs_gap[mg]
            pred_g = pred_gap[mg]
            n_gap = int(mg.sum())

            # ── Apex metrics: MAE + RMSE on held-out epochs only ──
            if n_gap == 0:
                mae = rmse = float("nan")
            else:
                err = obs_g - pred_g
                mae = float(np.mean(np.abs(err)))
                rmse = float(np.sqrt(np.mean(err ** 2)))

            mae_pass = bool(np.isfinite(mae) and mae < thr["MAE"])
            rmse_pass = bool(np.isfinite(rmse) and rmse < thr["RMSE"])
            design_pass = bool(mae_pass and rmse_pass)

            # ── Block bootstrap band ──
            block_used = BLOCK_PRIMARY
            lo, hi = block_bootstrap_band(resid_train, pred_g, BLOCK_PRIMARY, N_BOOT, rng)
            coverage = None
            cov_label = None
            if lo is not None and n_gap > 0:
                inside = (obs_g >= lo) & (obs_g <= hi)
                coverage = float(np.mean(inside))
                if coverage < COVERAGE_TARGET:
                    # widen to 2-year block and re-check
                    lo2, hi2 = block_bootstrap_band(resid_train, pred_g, BLOCK_WIDE, N_BOOT, rng)
                    if lo2 is not None:
                        inside2 = (obs_g >= lo2) & (obs_g <= hi2)
                        coverage2 = float(np.mean(inside2))
                        if coverage2 >= coverage:
                            lo, hi, coverage, block_used = lo2, hi2, coverage2, BLOCK_WIDE
                        else:
                            block_used = BLOCK_PRIMARY  # keep primary if wider did not help
                    if coverage < COVERAGE_TARGET:
                        cov_label = f"calibrated to {round(coverage * 100, 1)}%"

            # Band half-width (mean over held-out epochs); red flag if > observed range.
            half_width = None
            band_red_flag = False
            if lo is not None and n_gap > 0:
                half_width = float(np.mean((hi - lo) / 2.0))
                band_red_flag = bool(half_width > obs_range)

            results[layer]["designs"][design] = {
                "n_holdout_epochs": n_gap,
                "n_train_epochs": int(mt.sum()),
                "MAE_mm": round(mae, 4) if np.isfinite(mae) else None,
                "RMSE_mm": round(rmse, 4) if np.isfinite(rmse) else None,
                "MAE_threshold_mm": thr["MAE"],
                "RMSE_threshold_mm": thr["RMSE"],
                "MAE_pass": mae_pass,
                "RMSE_pass": rmse_pass,
                "design_pass": design_pass,
                "band_block_epochs": block_used,
                "band_mean_half_width_mm": round(half_width, 4) if half_width is not None else None,
                "coverage_fraction": round(coverage, 4) if coverage is not None else None,
                "coverage_target": COVERAGE_TARGET,
                "coverage_label": cov_label,
                "band_half_width_exceeds_range_red_flag": band_red_flag,
                "registry_rmse_for_cross_check": adoption[layer]["adopted_rmse_by_design"].get(design),
                "coef_used": coef,
            }

            apex_rows.append({
                "layer": layer, "class": klass, "adopted_model": adopted, "design": design,
                "MAE_mm": round(mae, 4) if np.isfinite(mae) else None,
                "RMSE_mm": round(rmse, 4) if np.isfinite(rmse) else None,
                "MAE_threshold": thr["MAE"], "RMSE_threshold": thr["RMSE"],
                "MAE_pass": mae_pass, "RMSE_pass": rmse_pass, "design_pass": design_pass,
            })

            print(f"  {layer} [{adopted}] {design}: MAE={mae:.3f} RMSE={rmse:.3f} "
                  f"(thr MAE<{thr['MAE']} RMSE<{thr['RMSE']}) pass={design_pass} | "
                  f"band±{half_width if half_width is None else round(half_width,2)}mm "
                  f"cov={coverage if coverage is None else round(coverage,3)} block={block_used}"
                  + (f" [{cov_label}]" if cov_label else ""))

    # ── Per-layer overall verdict + GATE M4 ──
    for layer in LAYERS_ORDER:
        d = results[layer]["designs"]
        all_pass = all(d[ds]["design_pass"] for ds in DESIGNS)
        results[layer]["layer_pass_all_designs"] = bool(all_pass)

    n_pass = sum(results[l]["layer_pass_all_designs"] for l in LAYERS_ORDER)

    # F3 waiver clause: F3 may pass with a documented waiver if it passes RMSE<20 on ALL
    # designs but misses MAE<10 on the END GAP ONLY.
    f3 = results["F3"]["designs"]
    f3_all_rmse_ok = all(f3[ds]["RMSE_pass"] for ds in DESIGNS)
    f3_mae_fail_designs = [ds for ds in DESIGNS if not f3[ds]["MAE_pass"]]
    f3_waiver_eligible = bool(f3_all_rmse_ok and f3_mae_fail_designs == ["end"])
    results["F3"]["waiver_eligible_end_gap_only"] = f3_waiver_eligible
    results["F3"]["waiver_detail"] = {
        "all_designs_rmse_under_20": f3_all_rmse_ok,
        "mae_failing_designs": f3_mae_fail_designs,
    }

    # Effective pass count with waiver: if F3 itself does not pass all designs but is
    # waiver-eligible, count it toward the >=5/6 rule via the documented waiver.
    n_pass_with_waiver = n_pass
    f3_takes_waiver = False
    if not results["F3"]["layer_pass_all_designs"] and f3_waiver_eligible:
        f3_takes_waiver = True
        n_pass_with_waiver = n_pass + 1

    gate_pass = bool(n_pass_with_waiver >= 5)
    gate_m4_verdict = "PASS" if gate_pass else "FAIL"

    summary = {
        "metadata": {
            "milestone": "M4 — Uncertainty and the Apex Verdict",
            "plan": "super_plan_2026-06-10.md",
            "source_registry": str(REGISTRY.relative_to(ROOT)),
            "machinery": "Reuses build_aligned_arrays + fit_candidate + predict_candidate + "
                         "design_indices from 17_hybrid_model_m3.py (M1-corrected lag loader).",
            "bootstrap": {"n_paths": N_BOOT, "block_primary_epochs": BLOCK_PRIMARY,
                          "block_wide_epochs": BLOCK_WIDE, "band": "5th-95th pct (90%)",
                          "rng_seed": RNG_SEED},
            "held_out_only": True,
            "thresholds": THRESHOLDS,
            "observed_ranges_mm": observed_ranges,
            "date": "2026-06-10",
        },
        "layers": results,
        "gate_m4": {
            "n_layers_passing_all_designs": int(n_pass),
            "f3_takes_waiver": f3_takes_waiver,
            "f3_waiver_eligible_end_gap_only": f3_waiver_eligible,
            "n_pass_with_waiver": int(n_pass_with_waiver),
            "rule": ">= 5 of 6 layers pass all designs (F3 may carry a documented "
                    "end-gap-only MAE waiver if RMSE<20 on all designs)",
            "verdict": gate_m4_verdict,
        },
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(summary, f, indent=2, default=_m3._json_default)

    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["layer", "class", "adopted_model", "design",
                                          "MAE_mm", "RMSE_mm", "MAE_threshold", "RMSE_threshold",
                                          "MAE_pass", "RMSE_pass", "design_pass"])
        w.writeheader()
        for r in apex_rows:
            w.writerow(r)

    print(f"\nSaved: {OUT_JSON}")
    print(f"Saved: {OUT_CSV}")
    print(f"\nLayers passing all designs (no waiver): {n_pass}/6")
    print(f"F3 takes waiver: {f3_takes_waiver} (eligible={f3_waiver_eligible})")
    print(f"Pass count with waiver: {n_pass_with_waiver}/6")
    print(f"GATE M4 VERDICT: {gate_m4_verdict}")
    return summary


if __name__ == "__main__":
    main()
