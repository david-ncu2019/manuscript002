"""
23_dense_calibration.py — Task M8.2: Dense-era frozen calibration for TUKU.

Physical story: Six TUKU layers each compact at their own rate, driven by their own
groundwater head and by the GPS surface signal.  This script freezes, once and for all
on the dense 2010-2018 era, the per-layer constants (a, c, S_ke, S_kv, tau) that the
walk-forward grading (Task M8.3) will use unchanged.

Usage:
    $env:PYTHONPATH=""; conda run -n fafalab2 python tau_demo_TUKU/seq/23_dense_calibration.py

Outputs:
    tau_demo_TUKU/results/seq/frozen_calibration.json
    tau_demo_TUKU/plots/seq/{layer}_calibration.png  (6 PNGs)

Reference: super_plan_2026-06-11 Task M8.2; CLAUDE.md TAU_MAX=120; Bug-F; two-thickness rule.
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

# ── Paths ─────────────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve()
_TAU_DEMO = _HERE.parent.parent   # tau_demo_TUKU/
_ROOT = _TAU_DEMO.parent          # repo root

for _p in [str(_TAU_DEMO), str(_ROOT), str(_ROOT / "scripts")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from tau_demo_TUKU.seq.drivers import build_layer_drivers   # noqa: E402
from tau_demo_TUKU.seq.frozen_model import FrozenLayerModel  # noqa: E402
from guardrails import (                                      # noqa: E402
    validate_layer_params, TUKU_MATERIALS, print_validation_report,
)

OUT_JSON_DIR = _TAU_DEMO / "results" / "seq"
OUT_PLOT_DIR = _TAU_DEMO / "plots" / "seq"
OUT_JSON_DIR.mkdir(parents=True, exist_ok=True)
OUT_PLOT_DIR.mkdir(parents=True, exist_ok=True)

# ── Configuation ──────────────────────────────────────────────────────────────
REF_DATE = "2015-01-16"
DENSE_START = pd.Timestamp("2010-01-16")
DENSE_END   = pd.Timestamp("2018-12-31")
SPLIT_A1    = pd.Timestamp("2015-01-01")   # A1 stability split boundary
TAU_MAX     = 120                           # CLAUDE.md constraint — never exceed
TAU_EXT_F3  = 292                           # F3 extended diagnostic only (never production)

# GWL well assignment (authoritative from station_file_map.json)
GWL_ROOT = _ROOT / "data" / "gwl" / "well_timeseries"
GPS_CSV  = _ROOT / "data" / "gps" / "modeled" / "TKJS_model.csv"
MLCW_INC = _TAU_DEMO / "data" / "incremental_data" / "mlcw_diff_cleaned.feather"

WELL_CONFIG: dict[str, tuple[str, str]] = {
    "F1": ("HONGLUN_gwl_timeseries.feather", "09050111"),
    "T1": ("HONGLUN_gwl_timeseries.feather", "09050111"),
    "F2": ("TUKU_gwl_timeseries.feather",    "09050321"),
    "T2": ("LUNZI_gwl_timeseries.feather",   "09170121"),
    "F3": ("TUKU_gwl_timeseries.feather",    "09050331"),
    "F4": ("LIUZHUANG_gwl_timeseries.feather","09080251"),
}

LAYERS = ["F1", "T1", "F2", "T2", "F3", "F4"]

# Thickness dicts (from tau_demo_TUKU/12_stress_strain_per_layer.py lines 97-124)
# LAYER_THICKNESS uses total borehole span for elastic S_ske conversion.
# LAYER_COMPRESSIBLE_THICKNESS uses fine-grained thickness for inelastic S_skv conversion.
LAYER_THICKNESS = {
    "F1": 41.577, "T1": 8.729, "F2": 106.284,
    "T2": 16.299, "F3": 110.494, "F4": 16.617,
}
LAYER_COMPRESSIBLE_THICKNESS = {
    "F1": 16.577, "T1": 7.423, "F2": 12.090,
    "T2": 10.299, "F3": 76.994, "F4": 16.617,
}


# ── Utilities ─────────────────────────────────────────────────────────────────

def compute_r2(obs: np.ndarray, pred: np.ndarray) -> float:
    """R-squared of obs vs pred (valid pairs only)."""
    m = np.isfinite(obs) & np.isfinite(pred)
    if m.sum() < 2:
        return float("nan")
    ss_res = np.sum((obs[m] - pred[m]) ** 2)
    ss_tot = np.sum((obs[m] - np.mean(obs[m])) ** 2)
    if ss_tot == 0:
        return float("nan")
    return float(1.0 - ss_res / ss_tot)


def valid_dense_mask(df: pd.DataFrame) -> np.ndarray:
    """Boolean mask: row in dense era AND all required columns finite."""
    dates = pd.to_datetime(df["date"])
    in_era = (dates >= DENSE_START) & (dates <= DENSE_END)
    finite = (
        np.isfinite(df["b_cum"].values)
        & np.isfinite(df["d_gps"].values)
        & np.isfinite(df["u_lag"].values)
        & np.isfinite(df["V_lag"].values)
    )
    return in_era.values & finite


def sse_one_tau(df: pd.DataFrame, tau: int, layer: str,
                use_u: bool = True, use_V: bool = True) -> float | None:
    """Fit FrozenLayerModel at a single tau; return SSE or None if insufficient data."""
    gwl_fname, wellcode = WELL_CONFIG[layer]
    df_tau = build_layer_drivers(
        layer=layer, tau=tau,
        gwl_feather=GWL_ROOT / gwl_fname,
        wellcode=wellcode,
        gps_csv=GPS_CSV,
        mlcw_inc_feather=MLCW_INC,
        ref_date=REF_DATE,
    )
    mask = valid_dense_mask(df_tau)
    if mask.sum() < 30:
        return None

    m = FrozenLayerModel(layer=layer, use_u=use_u, use_V=use_V)
    try:
        m.fit(
            df_tau["d_gps"].values[mask],
            df_tau["u_lag"].values[mask],
            df_tau["V_lag"].values[mask],
            df_tau["b_cum"].values[mask],
        )
    except ValueError:
        return None

    pred = m.predict(
        df_tau["d_gps"].values[mask],
        df_tau["u_lag"].values[mask],
        df_tau["V_lag"].values[mask],
    )
    resid = df_tau["b_cum"].values[mask] - pred
    return float(np.sum(resid ** 2))


def tau_grid_search(layer: str, tau_max: int,
                    use_u: bool = True, use_V: bool = True) -> tuple[int, list]:
    """Run SSE grid search over tau=0..tau_max for one layer.

    Returns (tau_best, sse_list) where sse_list[i] is the SSE at tau=i (or None).
    """
    sse_list: list[float | None] = []
    gwl_fname, wellcode = WELL_CONFIG[layer]

    # Load base dataframe once (tau=0); we will rebuild per-tau inside loop
    # (drivers.py is cheap to call — it re-reads feather files)
    for tau in range(tau_max + 1):
        sse = sse_one_tau(None, tau, layer, use_u=use_u, use_V=use_V)
        sse_list.append(sse)
        if tau % 20 == 0:
            print(f"    tau={tau:3d}  SSE={sse:.4f}" if sse is not None else f"    tau={tau:3d}  SSE=None")

    valid_sse = [(t, s) for t, s in enumerate(sse_list) if s is not None]
    if not valid_sse:
        raise RuntimeError(f"{layer}: no valid tau found in [0, {tau_max}]")
    tau_best = int(min(valid_sse, key=lambda x: x[1])[0])
    return tau_best, sse_list


def seasonal_amplitude(series: np.ndarray, dates: np.ndarray) -> float:
    """Estimate annual seasonal amplitude (half peak-to-trough) of a signal.

    Detrend by subtracting a linear fit, then compute the peak-to-trough range
    of the mean annual cycle (12 months) divided by 2.
    """
    m = np.isfinite(series)
    if m.sum() < 12:
        return float("nan")
    t = np.arange(len(series), dtype=float)
    # Linear detrend
    p = np.polyfit(t[m], series[m], 1)
    detrended = series - np.polyval(p, t)
    # Build monthly mean cycle
    ts_dates = pd.to_datetime(dates)
    df_tmp = pd.DataFrame({"v": detrended, "month": ts_dates.month}, index=ts_dates)
    df_tmp = df_tmp[m]
    monthly = df_tmp.groupby("month")["v"].mean()
    if len(monthly) < 6:
        return float("nan")
    return float((monthly.max() - monthly.min()) / 2.0)


# ── Per-layer calibration ──────────────────────────────────────────────────────

def calibrate_layer(layer: str) -> dict:
    """Full calibration pipeline for one layer.

    Returns a dict with all fields required by the JSON manifest.
    """
    print(f"\n{'='*65}")
    print(f"  Layer {layer}")
    print(f"{'='*65}")

    gwl_fname, wellcode = WELL_CONFIG[layer]
    gwl_path = GWL_ROOT / gwl_fname

    # ── Step 1: tau grid search 0-120 ─────────────────────────────────────────
    print(f"  Step 1: tau grid search 0..{TAU_MAX} ...")
    tau_best, sse_list = tau_grid_search(layer, TAU_MAX)
    print(f"  -> tau_best={tau_best} epochs ({tau_best*5} days)")

    # F3 extended diagnostic (tau 0..292, NOT production)
    tau_ext_diagnostic = None
    sse_ext_list = None
    if layer == "F3":
        print(f"  Step 1b (F3 only): extended diagnostic tau 0..{TAU_EXT_F3} ...")
        tau_ext_best, sse_ext_list = tau_grid_search("F3", TAU_EXT_F3)
        tau_ext_diagnostic = {"tau_extended_best": tau_ext_best,
                               "tau_extended_max": TAU_EXT_F3,
                               "note": "diagnostic only — production tau capped at TAU_MAX=120"}
        print(f"  -> F3 extended best tau={tau_ext_best} epochs ({tau_ext_best*5} days) [diagnostic only]")

    # ── Step 2: build drivers at selected tau; get h_c ────────────────────────
    print(f"  Step 2: build drivers at tau={tau_best} ...")
    df = build_layer_drivers(
        layer=layer, tau=tau_best,
        gwl_feather=gwl_path,
        wellcode=wellcode,
        gps_csv=GPS_CSV,
        mlcw_inc_feather=MLCW_INC,
        ref_date=REF_DATE,
    )
    h_c = df.attrs["h_c"]
    ref_val = df.attrs["ref_val"]
    print(f"  h_c={h_c:.4f} m MSL (pre-REF_DATE min, Bug-F)  ref_val={ref_val:.4f} m MSL")

    # Dense-era valid mask
    mask = valid_dense_mask(df)
    n_train = int(mask.sum())
    print(f"  Dense-era valid rows: {n_train}")

    if n_train < 30:
        raise RuntimeError(f"{layer}: only {n_train} dense-era valid rows — calibration undefined.")

    d_tr = df["d_gps"].values[mask]
    u_tr = df["u_lag"].values[mask]
    V_tr = df["V_lag"].values[mask]
    b_tr = df["b_cum"].values[mask]
    dates_tr = pd.to_datetime(df["date"].values[mask])

    # ── Step 3: Identifiability check ────────────────────────────────────────
    corr_uV = float(np.corrcoef(
        u_tr[np.isfinite(u_tr) & np.isfinite(V_tr)],
        V_tr[np.isfinite(u_tr) & np.isfinite(V_tr)]
    )[0, 1]) if (np.isfinite(u_tr) & np.isfinite(V_tr)).sum() > 2 else float("nan")

    use_u = True
    use_V = True
    dropped_for_collinearity = None

    if abs(corr_uV) > 0.95:
        # Keep the term with larger standalone |corr| with b
        corr_ub = float(np.corrcoef(u_tr, b_tr)[0, 1]) if np.isfinite(u_tr).all() else 0.0
        corr_Vb = float(np.corrcoef(V_tr, b_tr)[0, 1]) if np.isfinite(V_tr).all() else 0.0
        if abs(corr_ub) >= abs(corr_Vb):
            use_V = False
            dropped_for_collinearity = "V (u retained; |corr(u,b)|>=|corr(V,b)|)"
        else:
            use_u = False
            dropped_for_collinearity = "u (V retained; |corr(V,b)|>|corr(u,b)|)"
        print(f"  COLLINEARITY: |corr(u,V)|={abs(corr_uV):.3f} > 0.95 "
              f"-> dropped {dropped_for_collinearity}")
    else:
        print(f"  Identifiability OK: |corr(u,V)|={abs(corr_uV):.3f} <= 0.95")

    # Re-run tau grid with correct use_u/use_V if collinear
    if dropped_for_collinearity is not None:
        print(f"  Re-running tau grid with reduced model ...")
        tau_best, sse_list = tau_grid_search(layer, TAU_MAX, use_u=use_u, use_V=use_V)
        df = build_layer_drivers(
            layer=layer, tau=tau_best,
            gwl_feather=gwl_path,
            wellcode=wellcode,
            gps_csv=GPS_CSV,
            mlcw_inc_feather=MLCW_INC,
            ref_date=REF_DATE,
        )
        mask = valid_dense_mask(df)
        n_train = int(mask.sum())
        d_tr = df["d_gps"].values[mask]
        u_tr = df["u_lag"].values[mask]
        V_tr = df["V_lag"].values[mask]
        b_tr = df["b_cum"].values[mask]
        dates_tr = pd.to_datetime(df["date"].values[mask])
        h_c = df.attrs["h_c"]
        ref_val = df.attrs["ref_val"]
        print(f"  -> tau_best (reduced model)={tau_best} epochs ({tau_best*5} days)")

    # ── Step 4: Fit frozen model ───────────────────────────────────────────────
    print(f"  Step 4: fitting frozen model at tau={tau_best} ...")
    model = FrozenLayerModel(layer=layer, tau=tau_best, use_u=use_u, use_V=use_V, h_c=h_c)
    model.fit(d_tr, u_tr, V_tr, b_tr)
    print(f"  a={model.a:.5f}  c={model.c:.4f}  S_ke={model.S_ke:.4f} mm/m  S_kv={model.S_kv:.4f} mm/m")

    pred_tr = model.predict(d_tr, u_tr, V_tr)
    r2_train = compute_r2(b_tr, pred_tr)
    resid = b_tr - pred_tr
    sse_train = float(np.sum(resid ** 2))
    rmse_train = float(np.sqrt(np.mean(resid ** 2)))
    print(f"  R2={r2_train:.4f}  RMSE={rmse_train:.4f} mm  SSE={sse_train:.4f} mm^2")

    # Identifiability flags post-fit
    inelastic_not_excited = (model.S_kv == 0.0 and use_V)
    elastic_not_excited   = (model.S_ke == 0.0 and use_u)
    if inelastic_not_excited:
        print(f"  NOTE: S_kv=0 after fit — inelastic term not excited by data")
    if elastic_not_excited:
        print(f"  NOTE: S_ke=0 after fit — elastic term not excited by data")

    # Count inelastic epochs: V_lag < 0
    n_inelastic = int(np.sum(V_tr < 0))

    # ── Step 5: Guardrails ────────────────────────────────────────────────────
    total_m = LAYER_THICKNESS[layer]
    clay_m  = LAYER_COMPRESSIBLE_THICKNESS[layer]
    S_ske_m1 = model.S_ke / (total_m * 1000.0) if model.S_ke > 1e-15 else None
    S_skv_m1 = model.S_kv / (clay_m  * 1000.0) if (clay_m > 0 and model.S_kv > 1e-15) else None
    print(f"  S_ske={S_ske_m1:.3e} m-1 (total_m={total_m})  "
          f"S_skv={S_skv_m1:.3e} m-1 (clay_m={clay_m})" if S_ske_m1 and S_skv_m1 else
          f"  S_ske={S_ske_m1}  S_skv={S_skv_m1}")

    # Guardrail note: FrozenLayerModel fits S_ke and S_kv as INDEPENDENT non-negative
    # coefficients (S_ke*u + S_kv*V), whereas guardrails.validate_sign_constraints
    # requires S_kv >= S_ke (the Script-12 convention where S_kv = S_ke + delta).
    # To satisfy the guardrail interface, pass S_kv_for_gr = S_ke + S_kv so the
    # ratio check is physically equivalent: if S_kv=0 then S_kv_for_gr = S_ke (ratio=1).
    S_kv_for_gr = model.S_ke + model.S_kv   # always >= S_ke by construction
    mat = TUKU_MATERIALS.get(layer)
    gr = validate_layer_params(
        S_ke=model.S_ke, S_kv=S_kv_for_gr,
        layer=layer, station="TUKU",
        fan_zone="middle",
        material=mat,
        n_total=n_train, n_inelastic=n_inelastic,
        r2=r2_train, tau=tau_best,
    )
    guardrail_report = {
        "passed": gr.passed,
        "errors": gr.errors,
        "warnings": gr.warnings,
    }
    if not gr.passed:
        print(f"  GUARDRAIL ERRORS (sign violation — must not happen with bounded solver):")
        for e in gr.errors:
            print(f"    {e}")
        raise RuntimeError(f"{layer}: guardrail sign violation — bounded solver should prevent this")
    for w in gr.warnings:
        print(f"  GUARDRAIL WARN: {w}")

    # ── Step 6: A1 stability (split-era a comparison) ─────────────────────────
    mask_a1  = mask & (pd.to_datetime(df["date"].values) < SPLIT_A1)
    mask_a2  = mask & (pd.to_datetime(df["date"].values) >= SPLIT_A1)

    def fit_a_subset(sub_mask):
        if sub_mask.sum() < 30:
            return None
        m2 = FrozenLayerModel(layer=layer, use_u=use_u, use_V=use_V)
        try:
            m2.fit(
                df["d_gps"].values[sub_mask],
                df["u_lag"].values[sub_mask],
                df["V_lag"].values[sub_mask],
                df["b_cum"].values[sub_mask],
            )
            return round(float(m2.a), 6)
        except ValueError:
            return None

    a_pre2015  = fit_a_subset(mask_a1)
    a_post2015 = fit_a_subset(mask_a2)
    a_rel_diff = None
    if a_pre2015 is not None and a_post2015 is not None and abs(model.a) > 1e-9:
        a_rel_diff = round(abs(a_pre2015 - a_post2015) / abs(model.a), 4)
    print(f"  A1 stability: a_pre2015={a_pre2015}  a_post2015={a_post2015}  "
          f"rel_diff={a_rel_diff}")

    # ── Step 7: A4 seasonal check ─────────────────────────────────────────────
    # Compare seasonal amplitude of the head-driven term vs observed detrended seasonal
    dates_arr = df["date"].values[mask]

    # Head-driven seasonal: S_ke * u_lag (elastic contribution only)
    head_term = model.S_ke * u_tr if use_u else np.zeros_like(b_tr)
    amp_head  = seasonal_amplitude(head_term, dates_arr)
    amp_obs   = seasonal_amplitude(b_tr, dates_arr)

    F2_observed_seasonal_mm = 4.52  # from PART1_FINDINGS_20260610.md
    a4_flag = None
    if layer == "F2":
        if amp_obs > 0.01 and amp_head > 0.01:
            frac = amp_head / amp_obs
            harmonic_fallback_considered = bool(frac < 0.50)
        else:
            frac = float("nan")
            harmonic_fallback_considered = True  # unknown — flag
        a4_flag = {
            "amp_head_term_mm": round(amp_head, 4) if np.isfinite(amp_head) else None,
            "amp_obs_detrended_mm": round(amp_obs, 4) if np.isfinite(amp_obs) else None,
            "F2_reference_seasonal_mm": F2_observed_seasonal_mm,
            "fraction_explained_by_head": round(float(frac), 4) if np.isfinite(frac) else None,
            "harmonic_fallback_considered": harmonic_fallback_considered,
            "note": ("harmonic term NOT added — flag only; "
                     "head term supplies <50% of observed seasonal if flagged"),
        }
        print(f"  A4 seasonal (F2): amp_head={amp_head:.3f} mm  "
              f"amp_obs={amp_obs:.3f} mm  "
              f"frac={frac:.3f}  harmonic_fallback={harmonic_fallback_considered}")
    else:
        a4_flag = {
            "amp_head_term_mm": round(amp_head, 4) if np.isfinite(amp_head) else None,
            "amp_obs_detrended_mm": round(amp_obs, 4) if np.isfinite(amp_obs) else None,
        }

    # ── Step 8: SSE curve formatting ─────────────────────────────────────────
    sse_curve = {
        "tau": list(range(TAU_MAX + 1)),
        "sse": [round(s, 4) if (s is not None and np.isfinite(s)) else None for s in sse_list],
    }

    # ── Step 9: Calibration PNG ───────────────────────────────────────────────
    png_path = OUT_PLOT_DIR / f"{layer}_calibration.png"
    _plot_calibration(layer, dates_tr, b_tr, pred_tr, r2_train, model, png_path)
    print(f"  PNG: {png_path}")

    # ── Assemble layer result dict ─────────────────────────────────────────────
    result = {
        "layer": layer,
        "a": round(float(model.a), 6),
        "c": round(float(model.c), 6),
        "S_ke": round(float(model.S_ke), 6),
        "S_kv": round(float(model.S_kv), 6),
        "tau": int(tau_best),
        "use_u": bool(use_u),
        "use_V": bool(use_V),
        "h_c": round(float(h_c), 6),
        "ref_val": round(float(ref_val), 6),
        "n_train": int(n_train),
        "n_inelastic": int(n_inelastic),
        "r2_train": round(float(r2_train), 6) if np.isfinite(r2_train) else None,
        "rmse_train_mm": round(float(rmse_train), 4),
        "sse_train_mm2": round(float(sse_train), 4),
        # Identifiability
        "corr_u_V": round(float(corr_uV), 4) if np.isfinite(corr_uV) else None,
        "dropped_for_collinearity": dropped_for_collinearity,
        "inelastic_not_excited": bool(inelastic_not_excited),
        "elastic_not_excited": bool(elastic_not_excited),
        # Converted specific storage (two-thickness rule)
        "S_ske_m1": float(S_ske_m1) if S_ske_m1 is not None else None,
        "S_skv_m1": float(S_skv_m1) if S_skv_m1 is not None else None,
        "total_m": total_m,
        "clay_m": clay_m,
        "thickness_source": "tau_demo_TUKU/12_stress_strain_per_layer.py lines 97-124",
        # Guardrails
        "guardrail_report": guardrail_report,
        # A1 stability
        "a1_stability": {
            "a_pre2015": a_pre2015,
            "a_post2015": a_post2015,
            "a_relative_diff": a_rel_diff,
        },
        # A4 seasonal
        "a4_seasonal": a4_flag,
        # SSE curve
        "sse_curve": sse_curve,
    }

    # F3 extended diagnostic
    if layer == "F3" and tau_ext_diagnostic is not None:
        result["tau_extended_diagnostic"] = tau_ext_diagnostic
        result["tau_extended_diagnostic"]["sse_ext_curve"] = {
            "tau": list(range(TAU_EXT_F3 + 1)),
            "sse": [round(s, 4) if (s is not None and np.isfinite(s)) else None
                    for s in sse_ext_list],
        }

    return result


# ── Plot helper ───────────────────────────────────────────────────────────────

def _plot_calibration(
    layer: str,
    dates: pd.DatetimeIndex,
    obs: np.ndarray,
    pred: np.ndarray,
    r2: float,
    model: FrozenLayerModel,
    out_path: Path,
) -> None:
    """Two-panel calibration figure: observed vs fitted (dense era only)."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 5))
    fig.suptitle(
        f"TUKU Layer {layer} — Dense-era calibration ({DENSE_START.year}–{DENSE_END.year})",
        fontsize=16, fontweight="bold",
    )

    # Panel 1: timeseries
    ax = axes[0]
    ax.plot(dates, obs, color="tab:blue", lw=1.8, label="Observed b_cum (mm)")
    ax.plot(dates, pred, color="tab:orange", lw=1.8, ls="--",
            label=f"Fitted (R²={r2:.3f})")
    resid = obs - pred
    ax.fill_between(dates, pred, obs, alpha=0.25, color="gray", label="Residual")
    ax.set_xlabel("Date", fontsize=14)
    ax.set_ylabel("Cumulative compaction (mm)", fontsize=14)
    ax.set_title(f"{layer}: a={model.a:.4f}, τ={model.tau} ep ({model.tau*5} d)", fontsize=14)
    ax.tick_params(labelsize=13)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.4)

    # Panel 2: scatter obs vs pred
    ax2 = axes[1]
    ax2.scatter(obs, pred, s=8, alpha=0.5, color="tab:blue", label="Dense-era points")
    mn, mx = min(obs.min(), pred.min()), max(obs.max(), pred.max())
    ax2.plot([mn, mx], [mn, mx], "k--", lw=1.2, label="1:1 line")
    ax2.set_xlabel("Observed b_cum (mm)", fontsize=14)
    ax2.set_ylabel("Fitted b_cum (mm)", fontsize=14)
    ax2.set_title(
        f"{layer}: S_ke={model.S_ke:.3f}, S_kv={model.S_kv:.3f} mm/m  "
        f"RMSE={np.sqrt(np.mean(resid**2)):.2f} mm",
        fontsize=13,
    )
    ax2.tick_params(labelsize=13)
    ax2.legend(fontsize=12)
    ax2.grid(True, alpha=0.4)

    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("Task M8.2 — Dense-era frozen calibration (TUKU, 2010–2018)")
    print("=" * 70)
    print(f"  Dense window: {DENSE_START.date()} … {DENSE_END.date()}")
    print(f"  REF_DATE: {REF_DATE}  |  TAU_MAX: {TAU_MAX}  |  GPS: TKJS")

    layer_results: dict[str, dict] = {}

    for layer in LAYERS:
        try:
            res = calibrate_layer(layer)
            layer_results[layer] = res
        except Exception as exc:
            import traceback
            print(f"\nBLOCKED on layer {layer}:")
            traceback.print_exc()
            raise

    # ── Build and write JSON ──────────────────────────────────────────────────
    sum_a_k = round(sum(layer_results[l]["a"] for l in LAYERS), 6)

    manifest = {
        "dense_start": str(DENSE_START.date()),
        "dense_end": str(DENSE_END.date()),
        "ref_date": REF_DATE,
        "gwl_well_per_layer": {l: WELL_CONFIG[l][1] for l in LAYERS},
        "gps_source": "data/gps/modeled/TKJS_model.csv  (modeled column)",
        "mlcw_source": "tau_demo_TUKU/data/incremental_data/mlcw_diff_cleaned.feather",
        "sum_a_k": sum_a_k,
        "calibration_note": (
            "Calibrated on dense reconstruction (A8 caveat: b_cum is derived from "
            "mlcw_diff_cleaned.feather, which already applies the carrier-gap-fill "
            "repair R5; results are as good as the dense-era reconstruction). "
            "Blind-era grading in M8.3 uses the 264 genuine field visits."
        ),
        "identifiability_rule": (
            "If |corr(u_lag, V_lag)| > 0.95 on dense valid rows, drop the term "
            "with smaller |corr| with b; record as dropped_for_collinearity. "
            "Post-fit: if S_kv==0 record inelastic_not_excited; if S_ke==0 record "
            "elastic_not_excited."
        ),
        "tau_max_constraint": "TAU_MAX=120 epochs (5-day cadence = 600 days) per CLAUDE.md",
        "thickness_source": "tau_demo_TUKU/12_stress_strain_per_layer.py lines 97-124",
        "layers": layer_results,
    }

    json_path = OUT_JSON_DIR / "frozen_calibration.json"
    with open(json_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\n  Written: {json_path}")

    # ── Summary table ─────────────────────────────────────────────────────────
    print(f"\n{'='*100}")
    print(f"{'SUMMARY TABLE':^100}")
    print(f"{'─'*100}")
    hdr = (f"{'Layer':<6} | {'a':>8} | {'c':>8} | {'S_ke':>8} | {'S_kv':>8} | "
           f"{'tau':>5} | {'use_u':>6} | {'use_V':>6} | {'h_c':>9} | {'n_train':>7} | "
           f"{'R2':>7} | {'RMSE':>7}")
    print(hdr)
    print(f"{'─'*100}")
    for layer in LAYERS:
        r = layer_results[layer]
        print(f"{r['layer']:<6} | {r['a']:>8.5f} | {r['c']:>8.4f} | "
              f"{r['S_ke']:>8.4f} | {r['S_kv']:>8.4f} | "
              f"{r['tau']:>5} | {str(r['use_u']):>6} | {str(r['use_V']):>6} | "
              f"{r['h_c']:>9.4f} | {r['n_train']:>7} | "
              f"{(r['r2_train'] or float('nan')):>7.4f} | "
              f"{r['rmse_train_mm']:>7.4f}")
    print(f"{'─'*100}")
    print(f"  sum_a_k = {sum_a_k:.5f}  (sanity range [0.55, 0.75])")

    print(f"\n  A1 stability (a pre/post 2015 relative difference):")
    for layer in LAYERS:
        a1 = layer_results[layer]["a1_stability"]
        print(f"    {layer}: a_pre={a1['a_pre2015']}  a_post={a1['a_post2015']}  "
              f"rel_diff={a1['a_relative_diff']}")

    print(f"\n  A4 F2 seasonal check:")
    a4 = layer_results["F2"]["a4_seasonal"]
    print(f"    amp_head={a4['amp_head_term_mm']} mm  "
          f"amp_obs={a4['amp_obs_detrended_mm']} mm  "
          f"frac={a4['fraction_explained_by_head']}  "
          f"harmonic_fallback={a4['harmonic_fallback_considered']}")

    if "tau_extended_diagnostic" in layer_results["F3"]:
        ext = layer_results["F3"]["tau_extended_diagnostic"]
        print(f"\n  F3 extended tau diagnostic:")
        print(f"    production tau={layer_results['F3']['tau']} epochs ({layer_results['F3']['tau']*5} days)")
        print(f"    extended best  tau={ext['tau_extended_best']} epochs ({ext['tau_extended_best']*5} days) [DIAGNOSTIC ONLY]")

    # ── Re-read JSON and verify ───────────────────────────────────────────────
    print(f"\n  RE-READ VERIFICATION:")
    with open(json_path) as f:
        persisted = json.load(f)

    all_verified = True
    for layer in LAYERS:
        r_mem = layer_results[layer]
        r_per = persisted["layers"][layer]
        checks = {
            "a":         abs(r_per["a"] - r_mem["a"]) < 1e-8,
            "S_ke":      abs(r_per["S_ke"] - r_mem["S_ke"]) < 1e-8,
            "S_kv":      abs(r_per["S_kv"] - r_mem["S_kv"]) < 1e-8,
            "tau":       r_per["tau"] == r_mem["tau"],
            "h_c":       abs(r_per["h_c"] - r_mem["h_c"]) < 1e-8,
            "n_train":   r_per["n_train"] == r_mem["n_train"],
            "r2_train":  (r_per["r2_train"] is None and r_mem["r2_train"] is None) or
                          abs((r_per["r2_train"] or 0) - (r_mem["r2_train"] or 0)) < 1e-8,
        }
        ok = all(checks.values())
        all_verified = all_verified and ok
        status = "VERIFIED" if ok else f"MISMATCH: {[k for k,v in checks.items() if not v]}"
        print(f"    {layer}: {status}")

    if all_verified:
        print(f"\n  ALL 6 LAYERS VERIFIED — JSON matches in-memory values.")
    else:
        print(f"\n  WARNING: some layers did not verify!")

    # Confirm PNGs
    print(f"\n  PNG existence check:")
    all_png = True
    for layer in LAYERS:
        p = OUT_PLOT_DIR / f"{layer}_calibration.png"
        exists = p.exists()
        all_png = all_png and exists
        print(f"    {'EXISTS' if exists else 'MISSING'}: {p}")
    if all_png:
        print(f"  All 6 PNGs confirmed.")

    print(f"\n  DONE — frozen_calibration.json written to {json_path}")


if __name__ == "__main__":
    main()
