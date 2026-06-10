"""
15_storage_characterization.py — Physical parameter characterization (bilinear track).

Part 1 Phase 1.4 of super_plan_2026-06-09.md.
Reports S_ske, S_skv from the bug-fixed bilinear model with guardrail validation.

Uses bilinear_fit.py (Phase 0.0 Step B) to fit the Terzaghi/Riley model:
    b(t) = c + S_ke * u(t) + (S_kv - S_ke) * V(t)

Converts lumped coefficients to specific storage:
    S_ske = S_ke / (total_span_m * 1000)   [m⁻¹]
    S_skv = S_kv / (clay_thickness_m * 1000) [m⁻¹]

Reports TWO ratios:
    ratio_bulk    = S_kv / S_ke       (same thickness, comparable to lit.)
    ratio_specific = S_skv / S_ske     (mixed thickness — NOT directly comparable)

Flags:
    thickness_artifact: span/clay > 4  (specific ratio inflated by thickness)
    S_ke_identifiable:  n_elastic >= 15

Output: results/characterization/TUKU_storage_params.json

Usage:
    PYTHONPATH="" conda run -n isce_ncu3 python tau_demo_TUKU/15_storage_characterization.py
"""

from __future__ import annotations

import json, sys, warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "10_ihmf"))
sys.path.insert(0, str(ROOT / "tau_demo_TUKU"))

from bilinear_fit import fit_bilinear
from ihmf_model_v3 import compute_virgin_term
from scripts.guardrails import validate_layer_params, GuardrailViolation

warnings.filterwarnings("ignore", category=UserWarning)

# ── Config ──────────────────────────────────────────────────────────────────────
RESULT_JSON = ROOT / "results" / "ihmf" / "v3" / "verification_20260609_intercept" / "TUKU_gps_v3_results.json"
TAU_DEMO    = ROOT / "tau_demo_TUKU" / "data"
INC_DIR     = TAU_DEMO / "incremental_data"
OUT_DIR     = ROOT / "tau_demo_TUKU" / "results" / "characterization"
REF_DATE    = pd.Timestamp("2015-01-16")

WELL_CONFIG = [
    ("F1", "HONGLUN_gwl_timeseries.feather", "09050111"),
    ("T1", "HONGLUN_gwl_timeseries.feather", "09050111"),
    ("F2", "TUKU_gwl_timeseries.feather",   "09050321"),
    ("T2", "LUNZI_gwl_timeseries.feather",   "09170121"),
    ("F3", "TUKU_gwl_timeseries.feather",   "09050331"),
    ("F4", "LIUZHUANG_gwl_timeseries.feather", "09080251"),
]

# Layer thicknesses from borehole YL_WSYL23G1_TUKU (CLAUDE.md)
# total_m = total borehole span (for elastic S_ske)
# clay_m  = fine-grained material only (for inelastic S_skv)
LAYER_THICKNESS = {
    "F1": {"total_m": 41.577, "clay_m": 16.577, "clay_pct": 39.9},
    "T1": {"total_m":  8.729, "clay_m":  7.423, "clay_pct": 85.0},
    "F2": {"total_m": 106.284, "clay_m": 12.090, "clay_pct": 11.4},
    "T2": {"total_m": 16.299, "clay_m": 10.299, "clay_pct": 63.2},
    "F3": {"total_m": 110.494, "clay_m": 76.994, "clay_pct": 69.7},
    "F4": {"total_m": 16.617, "clay_m": 16.617, "clay_pct": 100.0},
}

# Fan zone assignments (Hung et al. 2021)
FAN_ZONES = {"F1": "middle", "T1": "middle", "F2": "middle",
             "T2": "middle", "F3": "middle", "F4": "middle"}

OUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    print("=" * 75)
    print("Phase 1.4 — Bilinear Physical Parameter Characterization (TUKU)")
    print("=" * 75)

    # 1. Load production tau values
    with open(RESULT_JSON) as f:
        prod = json.load(f)
    tau_dict = {lyr: prod["layers"][lyr]["tau_opt"] for lyr in prod["layers"]}

    # 2. Load MLCW + GWL data
    mlcw_inc = pd.read_feather(INC_DIR / "mlcw_diff_cleaned.feather")
    mlcw_inc["datetime"] = pd.to_datetime(mlcw_inc["datetime"]).astype("datetime64[ns]")
    mlcw_inc = mlcw_inc.sort_values("datetime").reset_index(drop=True)
    for col in [c for c in mlcw_inc.columns if c != "datetime"]:
        mlcw_inc[f"_cum_{col}"] = mlcw_inc[col].fillna(0.0).cumsum()
    master = pd.DataFrame({"datetime": mlcw_inc["datetime"].copy()})

    # 3. Fit bilinear model per layer
    print(f"\n{'Layer':5s} | {'S_ke':>8s} | {'S_kv':>8s} | {'S_ske':>10s} | {'S_skv':>10s} | "
          f"{'ratio_bulk':>10s} | {'ratio_spec':>10s} | {'R²':>7s} | {'n_el':>5s} | {'n_inel':>6s} | Flags")
    print(f"{'='*120}")

    results = {}
    for layer, fname, wellcode in WELL_CONFIG:
        thick = LAYER_THICKNESS[layer]

        # Load GWL
        gwl = pd.read_feather(TAU_DEMO / fname)
        gwl["datetime"] = pd.to_datetime(gwl["datetime"]).astype("datetime64[ns]")
        gwl = gwl[["datetime", wellcode]].dropna(subset=[wellcode])
        gwl = gwl.sort_values("datetime").reset_index(drop=True)

        # Zero-reference
        gwl_indexed = gwl.set_index("datetime")[wellcode]
        avail = gwl_indexed.dropna()
        pre_ref = avail.index[avail.index <= REF_DATE]
        if len(pre_ref) == 0:
            print(f"  {layer}: SKIP — no pre-REF_DATE GWL")
            continue
        ref_val = float(avail.loc[pre_ref[-1]])

        # h_c
        pre_ref_vals = gwl[gwl["datetime"] < REF_DATE][wellcode].dropna()
        h_c_abs = float(pre_ref_vals.min()) if len(pre_ref_vals) >= 10 else float(gwl[wellcode].dropna().min())

        # Align
        gwl_aligned = pd.merge_asof(master, gwl, on="datetime",
                                     direction="nearest", tolerance=pd.Timedelta("3D"))
        H_abs_full = gwl_aligned[wellcode].values.astype(float)
        b_cum_full = mlcw_inc[f"_cum_{layer}"].values.astype(float)

        # Apply tau lag
        tau = tau_dict.get(layer, 0)
        H_abs_lagged = H_abs_full[tau:]
        b_cum = b_cum_full[tau:]

        # Mask valid
        valid = np.isfinite(H_abs_lagged) & np.isfinite(b_cum)
        H_abs = H_abs_lagged[valid]
        b = b_cum[valid]

        if len(b) < 10:
            print(f"  {layer}: SKIP — <10 valid epochs after τ-lag")
            continue

        # Fit bilinear model
        fit = fit_bilinear(H_abs, b, h_c_abs, with_intercept=True)

        S_ke = fit["S_ke"]
        S_kv = fit["S_kv"]
        r2 = fit["r2"]
        n_el = fit["n_elastic"]
        n_inel = fit["n_inelastic"]

        # Convert to specific storage
        S_ske = S_ke / (thick["total_m"] * 1000) if S_ke > 1e-15 else 0.0
        S_skv = S_kv / (thick["clay_m"] * 1000) if S_kv > 1e-15 else 0.0

        # Ratios
        ratio_bulk = S_kv / S_ke if S_ke > 1e-15 else float("inf")
        ratio_specific = S_skv / S_ske if S_ske > 1e-15 else float("inf")
        thickness_artifact = bool(thick["total_m"] / thick["clay_m"] > 4)
        s_ke_identifiable = bool(n_el >= 15)

        # Guardrail validation (uses specific storage)
        guardrail_msgs = []
        try:
            validate_layer_params(
                S_ske, S_skv,
                layer, "TUKU", fan_zone=FAN_ZONES.get(layer, "middle"),
                n_total=n_el + n_inel, n_inelastic=n_inel, r2=r2, tau=tau,
            )
        except GuardrailViolation as e:
            guardrail_msgs.append(f"FATAL: {e}")

        # Flags
        flags = []
        if not s_ke_identifiable:
            flags.append("S_ke_not_identifiable")
        if thickness_artifact:
            flags.append("thickness_artifact")
        if ratio_bulk < 8:
            flags.append("ratio_bulk_below_8")
        if ratio_bulk > 100:
            flags.append("ratio_bulk_above_100")
        if S_ke < 1e-10:
            flags.append("S_ke_zero")

        results[layer] = {
            "S_ke_mm_per_m": round(S_ke, 5),
            "S_kv_mm_per_m": round(S_kv, 5),
            "delta_mm_per_m": round(fit["delta"], 5),
            "c_intercept_mm": round(fit["c_intercept"], 4),
            "S_ske_m1": round(S_ske, 10) if S_ske > 0 else 0.0,
            "S_skv_m1": round(S_skv, 10) if S_skv > 0 else 0.0,
            "ratio_bulk": round(ratio_bulk, 2),
            "ratio_specific": round(ratio_specific, 2),
            "thickness_artifact": thickness_artifact,
            "S_ke_identifiable": s_ke_identifiable,
            "r2_cum": round(r2, 4),
            "rmse_mm": round(fit["rmse"], 3),
            "n_elastic": n_el,
            "n_inelastic": n_inel,
            "tau_opt": tau,
            "total_span_m": thick["total_m"],
            "clay_thickness_m": thick["clay_m"],
            "clay_pct": thick["clay_pct"],
            "flags": flags,
            "guardrail_issues": guardrail_msgs,
        }

        flag_str = ",".join(flags) if flags else "—"
        print(f"  {layer:5s} | {S_ke:8.4f} | {S_kv:8.4f} | {S_ske:10.2e} | {S_skv:10.2e} | "
              f"{ratio_bulk:10.2f} | {ratio_specific:10.2f} | {r2:7.4f} | {n_el:5d} | {n_inel:6d} | {flag_str}")

    # 4. Summary
    print(f"\n── Summary ──")
    n_identifiable = sum(1 for r in results.values() if r["S_ke_identifiable"])
    n_artifact = sum(1 for r in results.values() if r["thickness_artifact"])
    print(f"  S_ke identifiable: {n_identifiable}/{len(results)} layers (>= 15 elastic epochs)")
    print(f"  Thickness artifact: {n_artifact}/{len(results)} layers (span/clay > 4)")
    print(f"\n  NOTE: ratio_specific uses mixed thickness (total span for S_ske, clay-only for S_skv).")
    print(f"  For comparison with Hung et al. (2021), use ratio_bulk (same-thickness basis).")

    # 5. Save
    output = {
        "metadata": {
            "description": "Bilinear Terzaghi/Riley parameter characterization at TUKU",
            "model": "b = c + S_ke * u + (S_kv - S_ke) * V, with per-layer intercept",
            "phase": "Part 1 Phase 1.4 — super_plan_2026-06-09.md",
            "reference": "Hung et al. (2021) WRR — CRAF per-fan-zone S_ske, S_skv",
            "date": "2026-06-10",
            "thickness_note": "S_ske = S_ke / (total_span_m * 1000); S_skv = S_kv / (clay_thickness_m * 1000). Ratio_specific is mixed-thickness and NOT directly comparable to literature. Use ratio_bulk for elastic/inelastic contrast.",
        },
        "per_layer": results,
        "literature_priors": {
            "proximal": {"S_ske_m1": 1.18e-4, "S_skv_m1": None},
            "middle":   {"S_ske_m1": 1.15e-4, "S_skv_m1": 1.33e-3},
            "distal":   {"S_ske_m1": 1.16e-4, "S_skv_m1": 1.91e-3},
        },
    }

    out_path = OUT_DIR / "TUKU_storage_params.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Saved: {out_path}")


if __name__ == "__main__":
    main()
