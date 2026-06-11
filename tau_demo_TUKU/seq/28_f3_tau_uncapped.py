"""
28_f3_tau_uncapped.py — Red Team Task C: F3 consolidation-lag uncap + phase-error test.

Physical story: The deepest clay-rich layer at TUKU (F3, ~435 of 555 mm column compaction)
has its consolidation lag frozen at τ=120 epochs (600 days) — the production cap.
The grid search wanted to go higher (guardrail warned "τ at boundary").
An extended diagnostic found best τ ≈ 163 epochs (~815 days).
This script lifts the cap for F3 only, refits, then runs the blind walk-forward to test
whether the phase error (detrended r=0.216 at annual cadence, Red Team finding F-4) closes.

Authorization: User-authorized uncap for F3 phase-error test, 2026-06-12.
Overrides CLAUDE.md TAU_MAX=120 for this labeled diagnostic only.
ALL other guardrail checks still bind (sign constraints, V monotone, h_c, etc.).

Usage:
    $env:PYTHONPATH=""; conda run -n fafalab2 python tau_demo_TUKU/seq/28_f3_tau_uncapped.py

Outputs:
    tau_demo_TUKU/results/seq/red_team_fixes/f3_uncapped_calibration.json
    tau_demo_TUKU/results/seq/red_team_fixes/f3_uncapped_walkforward_metrics.json
    tau_demo_TUKU/results/seq/red_team_fixes/f3_uncapped_<sched>_timeseries.csv (x4)
    tau_demo_TUKU/plots/seq/red_team_fixes/f3_detrended_dynamics.png
    tau_demo_TUKU/plots/seq/red_team_fixes/f3_residual_drift.png
    tau_demo_TUKU/plots/seq/red_team_fixes/f3_tau_sse_curve.png
    tau_demo_TUKU/results/seq/red_team_fixes/28_f3_tau_uncapped_run_log.txt
"""

from __future__ import annotations

import copy
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore", category=UserWarning)

# ── Paths ─────────────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve()
_TAU_DEMO = _HERE.parent.parent   # tau_demo_TUKU/
_ROOT = _TAU_DEMO.parent          # repo root

for _p in [str(_TAU_DEMO), str(_ROOT), str(_ROOT / "scripts")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from tau_demo_TUKU.seq.drivers import build_layer_drivers      # noqa: E402
from tau_demo_TUKU.seq.frozen_model import FrozenLayerModel    # noqa: E402
from tau_demo_TUKU.seq.time_oracle import TimeOracle, LeakageError  # noqa: E402
from tau_demo_TUKU.seq.conformal import ConformalBank          # noqa: E402
from guardrails import (                                        # noqa: E402
    validate_layer_params, TUKU_MATERIALS, GuardrailViolation,
)

# ── Configuration ──────────────────────────────────────────────────────────────
REF_DATE     = "2015-01-16"
DENSE_START  = pd.Timestamp("2010-01-16")
DENSE_END    = pd.Timestamp("2018-12-31")
BLIND_START  = pd.Timestamp("2019-01-01")
BLIND_END    = pd.Timestamp("2023-12-31")
SEED_START   = pd.Timestamp("2015-01-01")
SEED_END     = pd.Timestamp("2018-12-31")
SEED_FIT_START = pd.Timestamp("2010-01-16")
SEED_FIT_END   = pd.Timestamp("2014-12-31")

DROUGHT_START = pd.Timestamp("2021-01-01")
DROUGHT_END   = pd.Timestamp("2022-12-31")

# F3 extended search ceiling — matches 23_dense_calibration.py TAU_EXT_F3
TAU_EXT_F3 = 292
# Normal production cap (reference only; we bypass it for F3 with explicit authorization)
TAU_MAX_PRODUCTION = 120

# F3 GWL well
LAYER     = "F3"
GWL_FNAME = "TUKU_gwl_timeseries.feather"
WELLCODE  = "09050331"
ALL_LAYERS = ["F1", "T1", "F2", "T2", "F3", "F4"]

# Thickness (from 12_stress_strain_per_layer.py lines 97-124)
LAYER_THICKNESS            = {"F1": 41.577, "T1": 8.729, "F2": 106.284, "T2": 16.299, "F3": 110.494, "F4": 16.617}
LAYER_COMPRESSIBLE_THICKNESS = {"F1": 16.577, "T1": 7.423, "F2": 12.090, "T2": 10.299, "F3": 76.994, "F4": 16.617}

WELL_CONFIG: dict[str, tuple[str, str]] = {
    "F1": ("HONGLUN_gwl_timeseries.feather", "09050111"),
    "T1": ("HONGLUN_gwl_timeseries.feather", "09050111"),
    "F2": ("TUKU_gwl_timeseries.feather",    "09050321"),
    "T2": ("LUNZI_gwl_timeseries.feather",   "09170121"),
    "F3": ("TUKU_gwl_timeseries.feather",    "09050331"),
    "F4": ("LIUZHUANG_gwl_timeseries.feather","09080251"),
}

GWL_ROOT     = _ROOT / "data" / "gwl" / "well_timeseries"
GPS_CSV      = _ROOT / "data" / "gps" / "modeled" / "TKJS_model.csv"
MLCW_INC     = _TAU_DEMO / "data" / "incremental_data" / "mlcw_diff_cleaned.feather"
ORIG_CSV     = _ROOT / "data" / "mlcw" / "group_byLayer_orig" / "TUKU_orig_grouped.csv"
RECONST_CSV  = _TAU_DEMO / "data" / "TUKU_reconst_grouped.csv"
FROZEN_JSON  = _TAU_DEMO / "results" / "seq" / "frozen_calibration.json"

OUT_DIR   = _TAU_DEMO / "results" / "seq" / "red_team_fixes"
PLOT_DIR  = _TAU_DEMO / "plots"   / "seq" / "red_team_fixes"
LOG_PATH  = OUT_DIR / "28_f3_tau_uncapped_run_log.txt"

OUT_DIR.mkdir(parents=True, exist_ok=True)
PLOT_DIR.mkdir(parents=True, exist_ok=True)

# Schedules to run for F3 uncapped (Task C requires these 4)
SCHEDULE_NAMES = ["anchor_once", "annual", "semiannual", "monthly"]


# ── Tee logger ────────────────────────────────────────────────────────────────
class _Tee:
    """Write to both stdout and a log file simultaneously."""
    def __init__(self, path: Path):
        self._file = open(path, "w", encoding="utf-8", buffering=1)
        self._stdout = sys.stdout

    def write(self, text: str) -> None:
        self._stdout.write(text)
        self._file.write(text)

    def flush(self) -> None:
        self._stdout.flush()
        self._file.flush()

    def close(self) -> None:
        sys.stdout = self._stdout
        self._file.close()


# ── Helpers ───────────────────────────────────────────────────────────────────

def compute_r2(obs: np.ndarray, pred: np.ndarray) -> float:
    m = np.isfinite(obs) & np.isfinite(pred)
    if m.sum() < 2:
        return float("nan")
    ss_res = np.sum((obs[m] - pred[m]) ** 2)
    ss_tot = np.sum((obs[m] - np.mean(obs[m])) ** 2)
    return float("nan") if ss_tot == 0 else float(1.0 - ss_res / ss_tot)


def valid_dense_mask(df: pd.DataFrame) -> np.ndarray:
    dates = pd.to_datetime(df["date"])
    in_era = (dates >= DENSE_START) & (dates <= DENSE_END)
    finite = (
        np.isfinite(df["b_cum"].values)
        & np.isfinite(df["d_gps"].values)
        & np.isfinite(df["u_lag"].values)
        & np.isfinite(df["V_lag"].values)
    )
    return in_era.values & finite


def sse_at_tau(tau: int) -> float | None:
    """SSE of FrozenLayerModel.fit on dense-era F3 at a given tau."""
    df_tau = build_layer_drivers(
        layer=LAYER, tau=tau,
        gwl_feather=GWL_ROOT / GWL_FNAME,
        wellcode=WELLCODE,
        gps_csv=GPS_CSV,
        mlcw_inc_feather=MLCW_INC,
        ref_date=REF_DATE,
    )
    mask = valid_dense_mask(df_tau)
    if mask.sum() < 30:
        return None
    m = FrozenLayerModel(layer=LAYER, use_u=True, use_V=True)
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
    return float(np.sum((df_tau["b_cum"].values[mask] - pred) ** 2))


def _epochs_between(
    last_visit: pd.Timestamp,
    current: pd.Timestamp,
    epoch_list: list[pd.Timestamp],
) -> int:
    idx_last = None
    idx_curr = None
    for i, e in enumerate(epoch_list):
        if e == last_visit:
            idx_last = i
        if e == current:
            idx_curr = i
    if idx_last is None or idx_curr is None:
        return max(1, int((current - last_visit).days // 5))
    return max(1, idx_curr - idx_last)


# ── Step 1: F3 uncapped calibration ──────────────────────────────────────────

def calibrate_f3_uncapped() -> dict:
    """Grid-search τ over 0..TAU_EXT_F3 for F3; refit at τ_best; run guardrails."""
    print(f"\n{'='*70}")
    print("  STEP 1: F3 uncapped tau grid search (0..{})".format(TAU_EXT_F3))
    print(f"{'='*70}")

    # ── 1a. Grid search ───────────────────────────────────────────────────────
    sse_list: list[float | None] = []
    for tau in range(TAU_EXT_F3 + 1):
        sse = sse_at_tau(tau)
        sse_list.append(sse)
        if tau % 30 == 0:
            print(f"    tau={tau:3d}  SSE={sse:.4f}" if sse is not None else f"    tau={tau:3d}  SSE=None")

    valid = [(t, s) for t, s in enumerate(sse_list) if s is not None]
    if not valid:
        raise RuntimeError("F3: no valid tau in [0, {}]".format(TAU_EXT_F3))

    tau_best = int(min(valid, key=lambda x: x[1])[0])
    sse_best = float(min(valid, key=lambda x: x[1])[1])
    print(f"\n  -> tau_best = {tau_best} epochs ({tau_best * 5} days)  SSE = {sse_best:.4f}")
    if tau_best == TAU_EXT_F3:
        print("  WARNING: tau_best is at the extended ceiling — true lag may be even longer.")

    # Retrieve SSE at capped tau=120 for comparison
    sse_at_cap = sse_list[TAU_MAX_PRODUCTION] if TAU_MAX_PRODUCTION < len(sse_list) else None
    sse_at_163 = sse_list[163] if 163 < len(sse_list) else None
    print(f"  SSE at tau=120 (capped): {sse_at_cap}")
    print(f"  SSE at tau=163:           {sse_at_163}")

    # ── 1b. Build drivers at tau_best ─────────────────────────────────────────
    df = build_layer_drivers(
        layer=LAYER, tau=tau_best,
        gwl_feather=GWL_ROOT / GWL_FNAME,
        wellcode=WELLCODE,
        gps_csv=GPS_CSV,
        mlcw_inc_feather=MLCW_INC,
        ref_date=REF_DATE,
    )
    h_c    = df.attrs["h_c"]
    ref_val = df.attrs["ref_val"]
    print(f"  h_c={h_c:.6f} m MSL  ref_val={ref_val:.6f} m MSL")

    mask     = valid_dense_mask(df)
    n_train  = int(mask.sum())
    print(f"  Dense-era valid rows: {n_train}")
    if n_train < 30:
        raise RuntimeError(f"F3 uncapped: only {n_train} dense-era rows — calibration undefined.")

    d_tr  = df["d_gps"].values[mask]
    u_tr  = df["u_lag"].values[mask]
    V_tr  = df["V_lag"].values[mask]
    b_tr  = df["b_cum"].values[mask]

    # ── 1c. Identifiability check ──────────────────────────────────────────────
    both_finite = np.isfinite(u_tr) & np.isfinite(V_tr)
    corr_uV = float(np.corrcoef(u_tr[both_finite], V_tr[both_finite])[0, 1]) \
              if both_finite.sum() > 2 else float("nan")
    print(f"  |corr(u_lag, V_lag)| = {abs(corr_uV):.4f} (collinearity threshold: 0.95)")
    use_u = True
    use_V = True
    dropped_for_collinearity = None
    if abs(corr_uV) > 0.95:
        corr_ub = float(np.corrcoef(u_tr, b_tr)[0, 1]) if np.isfinite(u_tr).all() else 0.0
        corr_Vb = float(np.corrcoef(V_tr, b_tr)[0, 1]) if np.isfinite(V_tr).all() else 0.0
        if abs(corr_ub) >= abs(corr_Vb):
            use_V = False
            dropped_for_collinearity = "V"
        else:
            use_u = False
            dropped_for_collinearity = "u"
        print(f"  COLLINEARITY: dropped {dropped_for_collinearity}")

    # ── 1d. Fit frozen model ───────────────────────────────────────────────────
    print(f"  Fitting FrozenLayerModel at tau={tau_best} (use_u={use_u}, use_V={use_V}) ...")
    model = FrozenLayerModel(layer=LAYER, tau=tau_best, use_u=use_u, use_V=use_V, h_c=h_c)
    model.fit(d_tr, u_tr, V_tr, b_tr)

    pred_tr   = model.predict(d_tr, u_tr, V_tr)
    r2_train  = compute_r2(b_tr, pred_tr)
    resid_tr  = b_tr - pred_tr
    sse_train = float(np.sum(resid_tr ** 2))
    rmse_train = float(np.sqrt(np.mean(resid_tr ** 2)))

    print(f"  a={model.a:.6f}  c={model.c:.6f}  S_ke={model.S_ke:.6f}  S_kv={model.S_kv:.6f}")
    print(f"  R2={r2_train:.4f}  RMSE={rmse_train:.4f} mm  SSE={sse_train:.4f} mm^2")

    n_inelastic = int(np.sum(V_tr < 0))

    # Degeneracy check
    degenerate = False
    degenerate_reason = None
    if model.S_kv < 1e-12 and use_V:
        degenerate = True
        degenerate_reason = "S_kv collapsed to 0 — inelastic term not excited at uncapped tau"
        print(f"  DEGENERATE: {degenerate_reason}")
    if tau_best == TAU_EXT_F3:
        degenerate = True
        degenerate_reason = (degenerate_reason or "") + "; tau_best at extended ceiling — true minimum not found"
        print(f"  DEGENERATE: tau_best at ceiling")

    # ── 1e. Guardrails ─────────────────────────────────────────────────────────
    # Check tau > TAU_MAX_PRODUCTION — this WILL raise GuardrailViolation.
    # CATCH this specific one: log it and continue.
    # All other violations (sign constraints, etc.) must propagate.
    print(f"\n  Running guardrails (tau={tau_best}, tau_max=production {TAU_MAX_PRODUCTION}) ...")
    total_m = LAYER_THICKNESS[LAYER]
    clay_m  = LAYER_COMPRESSIBLE_THICKNESS[LAYER]

    # Run sign constraints manually first (must NOT be caught)
    from guardrails import validate_sign_constraints
    try:
        validate_sign_constraints(model.S_ke, model.S_ke + model.S_kv, LAYER, "TUKU")
    except GuardrailViolation as e:
        print(f"  FATAL GUARDRAIL (sign) — HALT: {e}")
        raise RuntimeError(f"F3 uncapped: sign violation — BLOCKED. {e}") from e

    # Run full validate_layer_params — it will raise GuardrailViolation for tau > tau_max.
    # Intercept ONLY the tau-boundary violation; re-raise everything else.
    authorized_tau_exception = None
    try:
        gr = validate_layer_params(
            S_ke=model.S_ke,
            S_kv=model.S_ke + model.S_kv,
            layer=LAYER, station="TUKU",
            fan_zone="middle",
            material=TUKU_MATERIALS.get(LAYER),
            n_total=n_train, n_inelastic=n_inelastic,
            r2=r2_train, tau=tau_best,
        )
        guardrail_report = {"passed": gr.passed, "errors": gr.errors, "warnings": gr.warnings}
    except GuardrailViolation as e:
        err_msg = str(e)
        # ASCII-safe detection: the guardrails message for tau > tau_max contains
        # "search range exceeded". Do not rely on Unicode tau (cp1252 env may mangle it).
        is_tau_boundary = (
            "search range exceeded" in err_msg
            or (">" in err_msg and str(tau_best) in err_msg
                and ("tau_max" in err_msg.lower() or "tau" in err_msg.lower()))
        )
        if is_tau_boundary:
            # This is the expected tau-cap violation — catch and log it
            authorized_tau_exception = {
                "guardrail_exception_verbatim": err_msg,
                "authorization": (
                    "user-authorized uncap for F3 phase-error test, 2026-06-12; "
                    "overrides CLAUDE.md TAU_MAX=120 for this labeled diagnostic only"
                ),
                "tau_best": tau_best,
                "tau_production_cap": TAU_MAX_PRODUCTION,
                "note": (
                    "All other guardrail checks still bind. "
                    "This exception is logged here and must NOT be applied in any production script."
                ),
            }
            print(f"  AUTHORIZED TAU EXCEPTION: {err_msg}")
            print(f"  Logging exception; continuing with all other checks ...")

            # Re-run guardrails with the uncapped tau_max so we get full warnings/errors
            from guardrails import (
                validate_literature_bounds, validate_ratio_gate,
                validate_data_sufficiency, validate_r2_sanity,
                validate_clay_layer_behavior, LayerValidationResult,
            )
            errors: list[str] = []
            warns: list[str] = []

            S_ske_m1 = model.S_ke / (total_m * 1000.0) if model.S_ke > 1e-15 else None
            S_skv_m1 = (model.S_ke + model.S_kv) / (clay_m * 1000.0) if (clay_m > 0 and (model.S_ke + model.S_kv) > 1e-15) else None

            with np.errstate(invalid="ignore"):
                warns += validate_literature_bounds(S_ske_m1, S_skv_m1, LAYER, "TUKU", "middle", strict=False)
            warns += validate_ratio_gate(S_ske_m1, S_skv_m1, LAYER, "TUKU")
            warns += validate_data_sufficiency(n_train, n_inelastic, LAYER, "TUKU")
            warns += validate_r2_sanity(r2_train, LAYER, "TUKU")
            # tau_bounds: note the exception but don't add as error
            warns.append(
                f"TUKU/F3: τ = {tau_best} (>{TAU_MAX_PRODUCTION}) — "
                f"user-authorized uncap; see authorized_tau_exception block."
            )
            mat = TUKU_MATERIALS.get(LAYER)
            if mat is not None:
                warns += validate_clay_layer_behavior(
                    model.S_ke, model.S_ke + model.S_kv, n_inelastic, n_train,
                    LAYER, mat.is_clay_dominated, "TUKU"
                )
            guardrail_report = {"passed": len(errors) == 0, "errors": errors, "warnings": warns}
        else:
            # Non-tau violation — re-raise; this is a true physics failure
            print(f"  FATAL GUARDRAIL (non-tau) — HALT: {e}")
            raise RuntimeError(f"F3 uncapped: fatal guardrail violation — BLOCKED. {e}") from e

    if not guardrail_report["passed"]:
        print(f"  GUARDRAIL ERRORS (fatal):")
        for e in guardrail_report["errors"]:
            print(f"    {e}")
        raise RuntimeError(f"F3 uncapped: guardrail sign violation — HALT.")
    for w in guardrail_report["warnings"]:
        print(f"  GUARDRAIL WARN: {w}")

    # ── 1f. SSE curve packaging ────────────────────────────────────────────────
    sse_curve = {
        "tau": list(range(TAU_EXT_F3 + 1)),
        "sse": [round(s, 4) if (s is not None and np.isfinite(s)) else None for s in sse_list],
    }

    result = {
        "layer": LAYER,
        "tau_best_uncapped": tau_best,
        "tau_best_days": tau_best * 5,
        "tau_production_cap": TAU_MAX_PRODUCTION,
        "tau_extended_ceiling": TAU_EXT_F3,
        "tau_at_ceiling": bool(tau_best == TAU_EXT_F3),
        "a": round(float(model.a), 6),
        "c": round(float(model.c), 6),
        "S_ke": round(float(model.S_ke), 6),
        "S_kv": round(float(model.S_kv), 6),
        "S_ke_activated": bool(model.S_ke > 1e-9),
        "h_c": round(float(h_c), 6),
        "ref_val": round(float(ref_val), 6),
        "use_u": use_u,
        "use_V": use_V,
        "n_train": n_train,
        "n_inelastic": n_inelastic,
        "r2_train": round(float(r2_train), 6) if np.isfinite(r2_train) else None,
        "rmse_train_mm": round(float(rmse_train), 4),
        "sse_train_mm2": round(float(sse_train), 4),
        "sse_at_tau120_capped": round(float(sse_at_cap), 4) if sse_at_cap is not None else None,
        "sse_reduction_vs_capped": round(float(sse_at_cap - sse_best), 4)
            if sse_at_cap is not None else None,
        "corr_u_V": round(float(corr_uV), 4) if np.isfinite(corr_uV) else None,
        "dropped_for_collinearity": dropped_for_collinearity,
        "degenerate": degenerate,
        "degenerate_reason": degenerate_reason,
        "authorized_tau_exception": authorized_tau_exception,
        "guardrail_report": guardrail_report,
        "sse_curve": sse_curve,
        "calibration_window": f"{DENSE_START.date()} .. {DENSE_END.date()}",
        "leakage_manifest": (
            "Calibration ends 2018-12-31 < blind score starts 2019-01-01; "
            "all pre-assimilation — no temporal leakage in this labeled diagnostic."
        ),
    }
    return result, model


# ── Step 2: walk-forward for F3 (uncapped model) ─────────────────────────────

def load_all_models_and_frames() -> tuple[dict, dict]:
    """Load all 6 frozen models from JSON; load full-timeline driver frames."""
    with open(FROZEN_JSON) as f:
        calib = json.load(f)
    models = {}
    for L in ALL_LAYERS:
        d = calib["layers"][L]
        models[L] = FrozenLayerModel(
            layer=L, a=d["a"], c=d["c"],
            S_ke=d["S_ke"], S_kv=d["S_kv"],
            tau=d["tau"], use_u=d["use_u"], use_V=d["use_V"],
            beta=0.0, h_c=d["h_c"],
        )
    frames = {}
    for L in ALL_LAYERS:
        gwl_fname, wellcode = WELL_CONFIG[L]
        tau = calib["layers"][L]["tau"]
        df = build_layer_drivers(
            layer=L, tau=tau,
            gwl_feather=GWL_ROOT / gwl_fname,
            wellcode=wellcode,
            gps_csv=GPS_CSV,
            mlcw_inc_feather=MLCW_INC,
            ref_date=REF_DATE,
        )
        df["date"] = pd.to_datetime(df["date"])
        frames[L] = df
    return models, frames


def load_genuine_truth() -> pd.DataFrame:
    df = pd.read_csv(ORIG_CSV)
    df["datetime"] = pd.to_datetime(df["datetime"])
    return df.sort_values("datetime").reset_index(drop=True)


def align_genuine_to_epoch(
    truth_df: pd.DataFrame,
    model_dates: pd.Series,
    tolerance_days: int = 3,
) -> pd.DataFrame:
    tol = pd.Timedelta(days=tolerance_days)
    model_dt = pd.DataFrame({
        "model_date": pd.to_datetime(model_dates).astype("datetime64[ns]")
    }).sort_values("model_date").reset_index(drop=True)
    truth_sorted = truth_df.copy()
    truth_sorted["datetime"] = pd.to_datetime(truth_sorted["datetime"]).astype("datetime64[ns]")
    truth_sorted = truth_sorted.sort_values("datetime").reset_index(drop=True)
    merged = pd.merge_asof(
        truth_sorted.rename(columns={"datetime": "model_date"}),
        model_dt.assign(model_date_epoch=model_dt["model_date"]),
        on="model_date", direction="nearest", tolerance=tol,
    )
    merged = merged.dropna(subset=["model_date_epoch"])
    merged["model_date"] = merged["model_date_epoch"]
    merged = merged.drop(columns=["model_date_epoch"])
    return merged.reset_index(drop=True)


def estimate_carrier_noise() -> float:
    gps = pd.read_csv(GPS_CSV)
    gps["datetime"] = pd.to_datetime(gps["date"])
    gps = gps.sort_values("datetime").reset_index(drop=True)
    mask = (gps["datetime"] >= BLIND_START) & (gps["datetime"] <= BLIND_END)
    d = gps.loc[mask, "modeled"].values.astype(float)
    if len(d) < 5:
        return float("nan")
    return float(np.nanstd(np.diff(d)))


def build_schedules(blind_genuine_dates: pd.DatetimeIndex) -> dict[str, list[pd.Timestamp]]:
    dates_sorted = sorted(blind_genuine_dates.dropna().unique())

    def nearest_genuine(target: pd.Timestamp):
        min_gap = pd.Timedelta(days=999)
        best = None
        for d in dates_sorted:
            gap = abs(d - target)
            if gap < min_gap:
                min_gap = gap
                best = d
        return best if min_gap <= pd.Timedelta(days=45) else None

    def subsample(spacing_days: int) -> list[pd.Timestamp]:
        result = []
        anchor = pd.Timestamp("2019-01-01")
        used: set = set()
        t = anchor
        while t <= BLIND_END + pd.Timedelta(days=spacing_days):
            nd = nearest_genuine(t)
            if nd is not None and nd not in used:
                used.add(nd)
                result.append(nd)
            t += pd.Timedelta(days=spacing_days)
        return sorted(result)

    monthly    = subsample(30)
    semiannual = subsample(180)
    annual     = subsample(365)
    # anchor_once: only the first genuine blind visit
    if dates_sorted:
        first_blind = dates_sorted[0]
        anchor_once = [first_blind]
    else:
        anchor_once = []

    return {
        "anchor_once": anchor_once,
        "annual":      annual,
        "semiannual":  semiannual,
        "monthly":     monthly,
    }


def seed_conformal_bank(
    seed_schedule_dates: list[pd.Timestamp],
    frames: dict[str, pd.DataFrame],
    truth_aligned: pd.DataFrame,
    carrier_noise: float,
    uncapped_f3_model: FrozenLayerModel,
    uncapped_f3_frame: pd.DataFrame,
) -> ConformalBank:
    """Seed the conformal bank using the 2015-2018 rehearsal with F3 replaced by uncapped model."""
    print("  Seeding conformal bank (2015-2018 rehearsal, F3 uncapped) ...")
    bank = ConformalBank(alpha=0.10)

    with open(FROZEN_JSON) as f:
        calib = json.load(f)

    # Re-fit all models on 2010-2014; replace F3 with uncapped model re-fit on 2010-2014
    seed_models: dict[str, FrozenLayerModel] = {}
    seed_frames = dict(frames)  # shallow copy; we will swap F3
    seed_frames[LAYER] = uncapped_f3_frame

    for L in ALL_LAYERS:
        if L == LAYER:
            # F3: refit uncapped model on 2010-2014
            m = FrozenLayerModel(
                layer=L, a=uncapped_f3_model.a, c=uncapped_f3_model.c,
                S_ke=uncapped_f3_model.S_ke, S_kv=uncapped_f3_model.S_kv,
                tau=uncapped_f3_model.tau,
                use_u=uncapped_f3_model.use_u, use_V=uncapped_f3_model.use_V,
                beta=0.0, h_c=uncapped_f3_model.h_c,
            )
        else:
            d = calib["layers"][L]
            m = FrozenLayerModel(
                layer=L, a=d["a"], c=d["c"],
                S_ke=d["S_ke"], S_kv=d["S_kv"],
                tau=d["tau"], use_u=d["use_u"], use_V=d["use_V"],
                beta=0.0, h_c=d["h_c"],
            )
        df = seed_frames[L]
        mask_fit = (
            (df["date"] >= SEED_FIT_START) & (df["date"] <= SEED_FIT_END)
            & np.isfinite(df["b_cum"].values)
            & np.isfinite(df["d_gps"].values)
            & np.isfinite(df["u_lag"].values)
            & np.isfinite(df["V_lag"].values)
        )
        n_fit = mask_fit.sum()
        if n_fit >= 30:
            try:
                m.fit(
                    df["d_gps"].values[mask_fit],
                    df["u_lag"].values[mask_fit],
                    df["V_lag"].values[mask_fit],
                    df["b_cum"].values[mask_fit],
                )
                print(f"    {L}: re-fit on 2010-2014 ({n_fit} rows) "
                      f"a={m.a:.4f} S_ke={m.S_ke:.4f} S_kv={m.S_kv:.4f}")
            except ValueError as e:
                print(f"    {L}: re-fit FAILED ({e}) — using frozen params")
        else:
            print(f"    {L}: {n_fit} rows in 2010-2014 — using frozen params")
        seed_models[L] = m

    seed_epochs = sorted(
        seed_frames[ALL_LAYERS[0]].loc[
            (seed_frames[ALL_LAYERS[0]]["date"] >= SEED_START) &
            (seed_frames[ALL_LAYERS[0]]["date"] <= SEED_END),
            "date",
        ].tolist()
    )
    if not seed_epochs:
        print("  WARNING: no seed epochs in 2015-2018; bank unseeded.")
        return bank

    truth_seed = truth_aligned[
        (truth_aligned["model_date"] >= SEED_START) &
        (truth_aligned["model_date"] <= SEED_END)
    ].copy()

    last_visit_seed = {L: SEED_START for L in ALL_LAYERS}
    seed_visit_set = set(seed_schedule_dates)
    seed_oracle = TimeOracle(SEED_START - pd.Timedelta(days=1))

    for epoch_date in seed_epochs:
        try:
            seed_oracle.advance(epoch_date)
        except LeakageError as e:
            print(f"  SEED LeakageError (should not happen): {e}")
            continue
        for L, m in seed_models.items():
            df = seed_frames[L]
            row_mask = df["date"] == epoch_date
            if not row_mask.any():
                continue
            row = df[row_mask].iloc[0]
            d_val = float(row["d_gps"])
            u_lag = float(row["u_lag"])
            V_lag = float(row["V_lag"])
            if not (np.isfinite(d_val) and np.isfinite(u_lag) and np.isfinite(V_lag)):
                continue
            pred = float(m.predict(d_val, u_lag, V_lag))
            if epoch_date in seed_visit_set:
                truth_row = truth_seed[truth_seed["model_date"] == epoch_date]
                if len(truth_row) > 0:
                    obs_val = float(truth_row.iloc[0].get(L, float("nan")))
                    if np.isfinite(obs_val):
                        horizon = _epochs_between(last_visit_seed[L], epoch_date, seed_epochs)
                        bank.add(L, horizon, abs(obs_val - pred))
                        m.assimilate(obs_val - pred)
                        last_visit_seed[L] = epoch_date

    print(f"  Bank census after seeding: {bank.census()}")
    return bank


def run_f3_uncapped_schedule(
    schedule_name: str,
    visit_dates: list[pd.Timestamp],
    all_frames: dict[str, pd.DataFrame],
    all_frozen_models: dict[str, FrozenLayerModel],
    uncapped_f3_model: FrozenLayerModel,
    uncapped_f3_frame: pd.DataFrame,
    bank_seed: ConformalBank,
    truth_aligned: pd.DataFrame,
    all_genuine_dates: set,
) -> dict:
    """Run blind walk-forward for one schedule; return per-F3 results."""
    print(f"\n  Schedule '{schedule_name}': {len(visit_dates)} visits")

    # Build full model + frames dicts; replace F3 with uncapped
    models = {L: copy.deepcopy(all_frozen_models[L]) for L in ALL_LAYERS}
    models[LAYER] = copy.deepcopy(uncapped_f3_model)
    frames = dict(all_frames)
    frames[LAYER] = uncapped_f3_frame
    bank = copy.deepcopy(bank_seed)

    blind_epochs = sorted(
        frames[ALL_LAYERS[0]].loc[
            (frames[ALL_LAYERS[0]]["date"] >= BLIND_START) &
            (frames[ALL_LAYERS[0]]["date"] <= BLIND_END),
            "date",
        ].tolist()
    )
    if not blind_epochs:
        raise RuntimeError("No blind-era epochs found.")

    visit_set = set(visit_dates)
    score_set = all_genuine_dates

    last_visit = {L: DENSE_END for L in ALL_LAYERS}
    ts_rows:   dict[str, list[dict]] = {L: [] for L in ALL_LAYERS}
    preq_rows: dict[str, list[dict]] = {L: [] for L in ALL_LAYERS}

    oracle = TimeOracle(DENSE_END)
    leakage_fired = False

    for epoch_date in blind_epochs:
        try:
            oracle.advance(epoch_date)
        except LeakageError as e:
            print(f"  LEAKAGE ERROR: {e}")
            leakage_fired = True
            break

        for L, m in models.items():
            df = frames[L]
            row_mask = df["date"] == epoch_date
            if not row_mask.any():
                continue
            row      = df[row_mask].iloc[0]
            d_val    = float(row["d_gps"])
            u_lag_v  = float(row["u_lag"])
            V_lag_v  = float(row["V_lag"])

            pred = float("nan")
            if np.isfinite(d_val) and np.isfinite(u_lag_v) and np.isfinite(V_lag_v):
                pred = float(m.predict(d_val, u_lag_v, V_lag_v))

            horizon = _epochs_between(last_visit[L], epoch_date, blind_epochs)
            hw = bank.half_width(L, horizon)

            ts_rows[L].append({
                "date": epoch_date.isoformat(),
                "pred_mm": round(pred, 4) if np.isfinite(pred) else None,
                "half_width_mm": round(hw, 4) if np.isfinite(hw) else None,
                "horizon_epochs": horizon,
            })

            is_score  = (epoch_date in score_set)
            is_reveal = (epoch_date in visit_set)

            if is_score:
                truth_row = truth_aligned[truth_aligned["model_date"] == epoch_date]
                obs_val = float("nan")
                if len(truth_row) > 0:
                    obs_val = float(truth_row.iloc[0].get(L, float("nan")))

                if np.isfinite(obs_val) and np.isfinite(pred):
                    innovation = obs_val - pred
                    in_band = bool(abs(obs_val - pred) <= hw) if np.isfinite(hw) else False
                    preq_rows[L].append({
                        "date": epoch_date.isoformat(),
                        "obs_mm": round(obs_val, 4),
                        "pred_mm": round(pred, 4),
                        "innovation_mm": round(innovation, 4),
                        "in_band": in_band,
                        "horizon_epochs": horizon,
                    })
                    if is_reveal:
                        bank.add(L, horizon, abs(innovation))
                        m.assimilate(innovation)
                        last_visit[L] = epoch_date

    return {
        "schedule_name": schedule_name,
        "ts_rows":        ts_rows,
        "preq_rows":      preq_rows,
        "leakage_fired":  leakage_fired,
    }


# ── Step 3: metrics (decision rule) ──────────────────────────────────────────

def compute_detrended_r_amplitude(
    matched_pairs: list[tuple[pd.Timestamp, float, float]]
) -> tuple[float, float]:
    """
    Compute detrended Pearson r and amplitude ratio on matched (date, pred, obs) pairs.

    Anti-pattern compliance:
    - A3: uses real elapsed days, not np.arange
    - A4: zero-references both series BEFORE detrending
    Returns (detrended_r, amplitude_ratio = std(pred_detr)/std(obs_detr))
    """
    if len(matched_pairs) < 3:
        return float("nan"), float("nan")

    dates_ts = np.array([pd.Timestamp(d).to_datetime64() for d, _, _ in matched_pairs],
                         dtype="datetime64[D]")
    pred_raw = np.array([p for _, p, _ in matched_pairs], dtype=float)
    obs_raw  = np.array([o for _, _, o in matched_pairs], dtype=float)

    # Zero-reference BEFORE detrending (A4)
    pred_z = pred_raw - pred_raw[0]
    obs_z  = obs_raw  - obs_raw[0]

    # Real elapsed days (A3): convert timedelta64[D] to float days
    days = (dates_ts - dates_ts[0]).astype(float)

    if len(days) < 2 or days[-1] < 1:
        return float("nan"), float("nan")

    # Linear detrend against real days
    p_pred = np.polyfit(days, pred_z, 1)
    p_obs  = np.polyfit(days, obs_z,  1)
    pred_detr = pred_z - np.polyval(p_pred, days)
    obs_detr  = obs_z  - np.polyval(p_obs,  days)

    std_pred = float(np.std(pred_detr))
    std_obs  = float(np.std(obs_detr))

    if std_obs < 1e-9 or std_pred < 1e-9:
        return float("nan"), float("nan")

    r = float(np.corrcoef(pred_detr, obs_detr)[0, 1])
    amp_ratio = std_pred / std_obs
    return r, amp_ratio


def compute_cross_corr_lag(
    matched_pairs: list[tuple[pd.Timestamp, float, float]],
    max_lag_epochs: int = 146,
) -> tuple[int, float]:
    """
    Cross-correlate detrended pred vs detrended obs over lags ±max_lag_epochs.
    Returns (lag_at_peak_epochs, lag_days).
    Positive lag: pred leads obs (compaction responds before expected).
    """
    if len(matched_pairs) < 10:
        return 0, 0.0

    dates_ts = np.array([pd.Timestamp(d).to_datetime64() for d, _, _ in matched_pairs],
                         dtype="datetime64[D]")
    pred_raw = np.array([p for _, p, _ in matched_pairs], dtype=float)
    obs_raw  = np.array([o for _, _, o in matched_pairs], dtype=float)

    pred_z = pred_raw - pred_raw[0]
    obs_z  = obs_raw  - obs_raw[0]
    days   = (dates_ts - dates_ts[0]).astype(float)

    p_pred = np.polyfit(days, pred_z, 1)
    p_obs  = np.polyfit(days, obs_z,  1)
    pred_detr = pred_z - np.polyval(p_pred, days)
    obs_detr  = obs_z  - np.polyval(p_obs,  days)

    n = len(pred_detr)
    # Full cross-correlation at all lags; then restrict to ±max_lag_epochs
    xcorr = np.correlate(pred_detr - pred_detr.mean(),
                         obs_detr  - obs_detr.mean(), mode="full")
    lags = np.arange(-(n - 1), n)
    mask = (lags >= -max_lag_epochs) & (lags <= max_lag_epochs)
    lags_sub = lags[mask]
    xcorr_sub = xcorr[mask]
    best_lag = int(lags_sub[np.argmax(xcorr_sub)])
    return best_lag, float(best_lag * 5)  # epochs → days (5-day cadence)


def compute_f3_metrics_for_schedule(
    sched_name: str,
    preq_rows_f3: list[dict],
    drought_start: pd.Timestamp = DROUGHT_START,
    drought_end:   pd.Timestamp = DROUGHT_END,
) -> dict:
    """Compute the full required metrics on F3 prequential rows for one schedule."""
    n = len(preq_rows_f3)
    if n == 0:
        return {"n": 0, "note": "No prequential rows"}

    dates_all = [pd.Timestamp(r["date"]) for r in preq_rows_f3]
    obs_all   = np.array([r["obs_mm"]   for r in preq_rows_f3], dtype=float)
    pred_all  = np.array([r["pred_mm"]  for r in preq_rows_f3], dtype=float)
    err_all   = obs_all - pred_all  # signed innovation

    # Find deployment-entry anchor (first genuine blind visit)
    sorted_dates = sorted(dates_all)
    entry_date = sorted_dates[0] if sorted_dates else None

    # Post-entry (exclude first visit)
    post_mask = np.array([pd.Timestamp(r["date"]) > entry_date for r in preq_rows_f3])
    n_post = int(post_mask.sum())

    rmse_all = float(np.sqrt(np.mean(err_all ** 2)))
    mae_all  = float(np.mean(np.abs(err_all)))
    rmse_post = float(np.sqrt(np.mean(err_all[post_mask] ** 2))) if n_post > 0 else float("nan")
    mae_post  = float(np.mean(np.abs(err_all[post_mask])))       if n_post > 0 else float("nan")

    # Detrended r and amplitude ratio (all visits)
    matched_all = [(dates_all[i], float(pred_all[i]), float(obs_all[i])) for i in range(n)]
    r_all, amp_all = compute_detrended_r_amplitude(matched_all)

    # Detrended r post-entry
    post_idx = [i for i in range(n) if post_mask[i]]
    matched_post = [(dates_all[i], float(pred_all[i]), float(obs_all[i])) for i in post_idx]
    r_post, amp_post = compute_detrended_r_amplitude(matched_post)

    # Cross-corr lag (all visits, headline)
    lag_epochs, lag_days = compute_cross_corr_lag(matched_all, max_lag_epochs=146)

    # Drought-window max |error|
    drought_mask = np.array([
        drought_start <= pd.Timestamp(r["date"]) <= drought_end
        for r in preq_rows_f3
    ])
    drought_errs = np.abs(err_all[drought_mask])
    max_drought_err = float(drought_errs.max()) if drought_mask.sum() > 0 else float("nan")
    drought_n = int(drought_mask.sum())

    # Entry innovation (deployment-entry anchor)
    entry_innovation = float(preq_rows_f3[0]["innovation_mm"]) if preq_rows_f3 else float("nan")

    return {
        "n_total": n,
        "n_post_entry": n_post,
        "entry_date": entry_date.isoformat() if entry_date else None,
        "entry_innovation_mm": round(entry_innovation, 4) if np.isfinite(entry_innovation) else None,
        "RMSE_all_mm":  round(rmse_all,  4) if np.isfinite(rmse_all)  else None,
        "MAE_all_mm":   round(mae_all,   4) if np.isfinite(mae_all)   else None,
        "RMSE_post_entry_mm": round(rmse_post, 4) if np.isfinite(rmse_post) else None,
        "MAE_post_entry_mm":  round(mae_post,  4) if np.isfinite(mae_post)  else None,
        "detrended_r_all":  round(r_all,  4) if np.isfinite(r_all)  else None,
        "detrended_r_post": round(r_post, 4) if np.isfinite(r_post) else None,
        "amplitude_ratio_all":  round(amp_all,  4) if np.isfinite(amp_all)  else None,
        "amplitude_ratio_post": round(amp_post, 4) if np.isfinite(amp_post) else None,
        "cross_corr_lag_epochs": lag_epochs,
        "cross_corr_lag_days":   round(lag_days, 1),
        "drought_n":    drought_n,
        "drought_max_abs_err_mm": round(max_drought_err, 4) if np.isfinite(max_drought_err) else None,
        "headline_r":   round(r_post, 4) if np.isfinite(r_post) else round(r_all, 4),
    }


def compute_f3_capped_metrics_from_disk(
    sched_name: str,
) -> dict:
    """Read existing capped-F3 timeseries from disk and compute the same metrics."""
    # Map schedule name to existing output directories
    sched_dir_map = {
        "anchor_once": OUT_DIR / "anchor_once",
        "annual":      _TAU_DEMO / "results" / "seq" / "annual",
        "semiannual":  _TAU_DEMO / "results" / "seq" / "semiannual",
        "monthly":     _TAU_DEMO / "results" / "seq" / "monthly",
    }
    metrics_dir_map = {
        "anchor_once": OUT_DIR / "anchor_once",
        "annual":      _TAU_DEMO / "results" / "seq" / "annual",
        "semiannual":  _TAU_DEMO / "results" / "seq" / "semiannual",
        "monthly":     _TAU_DEMO / "results" / "seq" / "monthly",
    }

    sched_dir = sched_dir_map.get(sched_name)
    metrics_dir = metrics_dir_map.get(sched_name)

    if sched_dir is None or metrics_dir is None:
        return {"error": f"No path mapping for schedule '{sched_name}'"}

    metrics_path = metrics_dir / "metrics.json"
    if not metrics_path.exists():
        return {"error": f"Capped metrics not found: {metrics_path}"}

    with open(metrics_path) as f:
        m = json.load(f)

    f3_metrics = m.get("layers", {}).get("F3", {})
    innovations = f3_metrics.get("innovations", [])

    if not innovations:
        return {"n_total": 0, "note": "No innovations in capped metrics"}

    dates_all = [pd.Timestamp(r["date"]) for r in innovations]
    obs_all   = np.array([r["value"] + r.get("pred_mm", 0.0) for r in innovations], dtype=float)
    # innovations = obs - pred, so obs = innovation + pred; but pred not in innovations dict.
    # The innovations field only has "value" (= obs - pred). We need both obs and pred
    # separately for detrended correlation. Use obs_at_visit from timeseries CSV if available.
    # Fallback: read TUKU_F3_seq_timeseries.csv and join on date.
    ts_path = sched_dir / "TUKU_F3_seq_timeseries.csv"
    if not ts_path.exists():
        return {"error": f"Capped timeseries not found: {ts_path}"}

    ts_df = pd.read_csv(ts_path)
    ts_df["date_ts"] = pd.to_datetime(ts_df["date"])

    # Build matched pairs from timeseries + innovations
    matched = []
    for row in innovations:
        d = pd.Timestamp(row["date"])
        inn = float(row["value"])  # obs - pred
        ts_row = ts_df[ts_df["date_ts"] == d]
        if len(ts_row) == 0:
            continue
        pred_v = ts_row.iloc[0]["pred_mm"]
        if pd.isna(pred_v):
            continue
        pred_v = float(pred_v)
        obs_v  = pred_v + inn
        matched.append((d, pred_v, obs_v))

    if not matched:
        return {"n_total": 0, "note": "No matched capped rows"}

    n = len(matched)
    dates_m = [m[0] for m in matched]
    pred_m  = np.array([m[1] for m in matched])
    obs_m   = np.array([m[2] for m in matched])
    err_m   = obs_m - pred_m

    entry_date = sorted(dates_m)[0] if dates_m else None
    post_mask  = np.array([d > entry_date for d in dates_m]) if entry_date else np.zeros(n, bool)
    n_post = int(post_mask.sum())

    r_all,  amp_all  = compute_detrended_r_amplitude(matched)
    post_idx  = [i for i in range(n) if post_mask[i]]
    matched_post = [matched[i] for i in post_idx]
    r_post, amp_post = compute_detrended_r_amplitude(matched_post)

    lag_epochs, lag_days = compute_cross_corr_lag(matched, max_lag_epochs=146)

    drought_mask = np.array([
        DROUGHT_START <= d <= DROUGHT_END for d in dates_m
    ])
    drought_errs = np.abs(err_m[drought_mask])
    max_drought_err = float(drought_errs.max()) if drought_mask.sum() > 0 else float("nan")

    rmse_all  = float(np.sqrt(np.mean(err_m ** 2)))
    rmse_post = float(np.sqrt(np.mean(err_m[post_mask] ** 2))) if n_post > 0 else float("nan")
    mae_all   = float(np.mean(np.abs(err_m)))
    mae_post  = float(np.mean(np.abs(err_m[post_mask])))       if n_post > 0 else float("nan")

    return {
        "n_total": n,
        "n_post_entry": n_post,
        "RMSE_all_mm":  round(rmse_all,  4),
        "MAE_all_mm":   round(mae_all,   4),
        "RMSE_post_entry_mm": round(rmse_post, 4) if np.isfinite(rmse_post) else None,
        "MAE_post_entry_mm":  round(mae_post,  4) if np.isfinite(mae_post)  else None,
        "detrended_r_all":  round(r_all,  4) if np.isfinite(r_all)  else None,
        "detrended_r_post": round(r_post, 4) if np.isfinite(r_post) else None,
        "amplitude_ratio_all":  round(amp_all,  4) if np.isfinite(amp_all)  else None,
        "amplitude_ratio_post": round(amp_post, 4) if np.isfinite(amp_post) else None,
        "cross_corr_lag_epochs": lag_epochs,
        "cross_corr_lag_days":   round(lag_days, 1),
        "drought_n":    int(drought_mask.sum()),
        "drought_max_abs_err_mm": round(max_drought_err, 4) if np.isfinite(max_drought_err) else None,
        "headline_r": round(r_post, 4) if np.isfinite(r_post) else round(r_all, 4) if np.isfinite(r_all) else None,
    }


# ── Decision rule ─────────────────────────────────────────────────────────────

def apply_decision_rule(
    uncapped_metrics_by_sched: dict[str, dict],
    capped_metrics_by_sched: dict[str, dict],
) -> tuple[bool, dict]:
    """
    F3 is 'restored' iff:
      (detrended r_post >= 0.5 at ANNUAL cadence) AND
      (drought-window max|error| <= 20 mm at annual cadence).
    Report all four cadences and borderline picture.
    """
    annual_uncap = uncapped_metrics_by_sched.get("annual", {})
    r_annual_uncap = annual_uncap.get("headline_r")
    drought_annual_uncap = annual_uncap.get("drought_max_abs_err_mm")

    annual_cap = capped_metrics_by_sched.get("annual", {})
    r_annual_cap = annual_cap.get("headline_r")
    drought_annual_cap = annual_cap.get("drought_max_abs_err_mm")

    r_ok = (r_annual_uncap is not None and r_annual_uncap >= 0.5)
    drought_ok = (drought_annual_uncap is not None and drought_annual_uncap <= 20.0)
    f3_restored = bool(r_ok and drought_ok)

    r_table = {}
    drought_table = {}
    lag_table = {}
    for sched in SCHEDULE_NAMES:
        um = uncapped_metrics_by_sched.get(sched, {})
        cm = capped_metrics_by_sched.get(sched, {})
        r_table[sched]      = {"uncapped": um.get("headline_r"),
                                "capped":   cm.get("headline_r"),
                                "delta":    None if (um.get("headline_r") is None or cm.get("headline_r") is None)
                                            else round(float(um["headline_r"]) - float(cm["headline_r"]), 4)}
        drought_table[sched] = {"uncapped": um.get("drought_max_abs_err_mm"),
                                 "capped":   cm.get("drought_max_abs_err_mm")}
        lag_table[sched] = {
            "uncapped_lag_epochs": um.get("cross_corr_lag_epochs"),
            "uncapped_lag_days":   um.get("cross_corr_lag_days"),
            "capped_lag_epochs":   cm.get("cross_corr_lag_epochs"),
            "capped_lag_days":     cm.get("cross_corr_lag_days"),
        }

    verdict = {
        "f3_restored": f3_restored,
        "decision_criteria": {
            "r_annual_uncapped": r_annual_uncap,
            "r_threshold": 0.5,
            "r_passes": r_ok,
            "drought_max_abs_err_annual_mm": drought_annual_uncap,
            "drought_threshold_mm": 20.0,
            "drought_passes": drought_ok,
        },
        "r_table_per_schedule": r_table,
        "drought_table_per_schedule": drought_table,
        "cross_corr_lag_table": lag_table,
        "r_annual_capped_reference": r_annual_cap,
        "drought_annual_capped_reference": drought_annual_cap,
        "verdict_note": (
            "RESTORED" if f3_restored else
            ("NOT RESTORED — r passes but drought fails" if (r_ok and not drought_ok) else
             "NOT RESTORED — drought passes but r fails" if (not r_ok and drought_ok) else
             "NOT RESTORED — both r and drought fail")
        ),
    }
    return f3_restored, verdict


# ── Plotting ──────────────────────────────────────────────────────────────────

def plot_tau_sse_curve(
    sse_list: list[float | None],
    tau_best: int,
    out_path: Path,
) -> None:
    """SSE vs tau, vertical lines at tau=120 (cap) and tau_best."""
    taus = list(range(len(sse_list)))
    sses = [s if s is not None else float("nan") for s in sse_list]

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(taus, sses, color="tab:blue", lw=1.8, label="SSE vs τ (dense era)")
    ax.axvline(x=TAU_MAX_PRODUCTION, color="tab:red",    lw=2.0, ls="--",
               label=f"Production cap τ={TAU_MAX_PRODUCTION} ({TAU_MAX_PRODUCTION*5} d)")
    ax.axvline(x=tau_best,           color="tab:green",  lw=2.0, ls="-.",
               label=f"τ_best={tau_best} ({tau_best*5} d) — SSE={sse_list[tau_best]:.1f}")

    ax.set_xlabel("τ (5-day epoch units)", fontsize=14)
    ax.set_ylabel("SSE (mm²)", fontsize=14)
    ax.set_title(f"TUKU F3 — SSE vs τ, grid 0–{TAU_EXT_F3}. Cap lifted: best τ={tau_best} ({tau_best*5} days)", fontsize=14)
    ax.tick_params(labelsize=13)
    ax.legend(fontsize=13)
    ax.grid(True, alpha=0.35)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  PNG: {out_path}")


def plot_detrended_dynamics(
    sched_name: str,
    capped_preq: list[dict],
    uncapped_preq: list[dict],
    capped_ts_path: Path,
    uncapped_ts_rows: list[dict],
    out_path: Path,
) -> None:
    """
    Zero-referenced, real-day-detrended OBS vs CAPPED-pred vs UNCAPPED-pred (blind era).
    Annual-cadence reveals marked. Shared y-axis (anti-pattern A2 compliance).
    """
    # Build matched arrays from prequential rows (they have obs and pred at genuine visits)
    def extract(preq: list[dict]):
        dates = [pd.Timestamp(r["date"]) for r in preq]
        preds = np.array([r["pred_mm"]   for r in preq], dtype=float)
        obs   = np.array([r["obs_mm"]    for r in preq], dtype=float)
        return dates, preds, obs

    cap_dates,   cap_preds,   cap_obs   = extract(capped_preq)
    uncap_dates, uncap_preds, uncap_obs = extract(uncapped_preq)

    if not cap_dates or not uncap_dates:
        print(f"  WARNING: no data for detrended dynamics plot ({sched_name})")
        return

    # Common obs dates (same genuine visits)
    # Use uncap obs as the canonical observation series (same visits, same obs)
    # Zero-reference at first point (A4)
    def zero_ref_detrend(dates_arr, vals_arr):
        if len(vals_arr) == 0:
            return vals_arr, np.array([])
        vals_z = vals_arr - vals_arr[0]
        days   = np.array([(d - dates_arr[0]).days for d in dates_arr], dtype=float)
        if len(days) < 2 or days[-1] < 1:
            return vals_z, days
        p = np.polyfit(days, vals_z, 1)
        return vals_z - np.polyval(p, days), days

    obs_detr,   _ = zero_ref_detrend(uncap_dates, uncap_obs)
    cap_detr,   _ = zero_ref_detrend(cap_dates,   cap_preds)
    uncap_detr, _ = zero_ref_detrend(uncap_dates, uncap_preds)

    fig, ax = plt.subplots(figsize=(15, 6))

    # OBS (observed)
    ax.plot(uncap_dates, obs_detr, color="black", lw=2.0, marker="o", ms=5,
            label="Observed (genuine visits)", zorder=5)
    # Capped prediction (genuine-visit points)
    ax.plot(cap_dates, cap_detr, color="tab:red", lw=1.6, ls="--", marker="s", ms=4,
            label=f"Capped τ=120 (600 d) prediction", zorder=4)
    # Uncapped prediction
    ax.plot(uncap_dates, uncap_detr, color="tab:blue", lw=1.8, ls="-.", marker="^", ms=4,
            label=f"Uncapped τ={capped_preq[0]['pred_mm']}..." if False else
            f"Uncapped τ_best prediction", zorder=4)

    # Mark reveal dates if annual schedule
    if "annual" in sched_name:
        for d in uncap_dates:
            ax.axvline(x=d, color="tab:green", lw=0.7, alpha=0.5, ls=":")

    ax.set_xlabel("Date", fontsize=14)
    ax.set_ylabel("Detrended cumulative compaction (mm)", fontsize=14)
    ax.set_title(
        f"TUKU F3 — Detrended dynamics, {sched_name}, blind era 2019–2023\n"
        f"Shared y-axis: capped τ=120 vs uncapped τ_best; zero-ref + real-day detrend",
        fontsize=13
    )
    ax.tick_params(labelsize=13)
    ax.legend(fontsize=12, loc="upper left")
    ax.grid(True, alpha=0.35)
    # Shared y-axis (A6): set limits from all series
    all_vals = np.concatenate([obs_detr, cap_detr, uncap_detr])
    finite = all_vals[np.isfinite(all_vals)]
    if len(finite) > 0:
        margin = (finite.max() - finite.min()) * 0.05 + 1.0
        ax.set_ylim(finite.min() - margin, finite.max() + margin)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  PNG: {out_path}")


def plot_residual_drift(
    sched_name: str,
    capped_preq: list[dict],
    uncapped_preq: list[dict],
    out_path: Path,
) -> None:
    """Signed residual vs time, capped vs uncapped. Drought window 2021-2022 shaded."""
    cap_dates   = [pd.Timestamp(r["date"])   for r in capped_preq]
    cap_inn     = np.array([r["innovation_mm"] for r in capped_preq], dtype=float)
    uncap_dates = [pd.Timestamp(r["date"])   for r in uncapped_preq]
    uncap_inn   = np.array([r["innovation_mm"] for r in uncapped_preq], dtype=float)

    fig, ax = plt.subplots(figsize=(15, 6))

    ax.axhline(y=0, color="black", lw=1.0)
    ax.axhline(y=+20, color="tab:orange", lw=1.2, ls="--", alpha=0.8, label="+20 mm L1 line")
    ax.axhline(y=-20, color="tab:orange", lw=1.2, ls="--", alpha=0.8, label="-20 mm L1 line")

    # Drought shading
    ax.axvspan(DROUGHT_START, DROUGHT_END,
               color="gold", alpha=0.20, label="Drought 2021-2022")

    ax.plot(cap_dates,   cap_inn,   color="tab:red",  lw=1.8, ls="--", marker="s", ms=5,
            label=f"Capped τ=120 residual (obs - pred)")
    ax.plot(uncap_dates, uncap_inn, color="tab:blue", lw=1.8, ls="-.", marker="^", ms=5,
            label=f"Uncapped τ_best residual (obs - pred)")

    ax.set_xlabel("Date", fontsize=14)
    ax.set_ylabel("Signed residual (mm) = obs − pred", fontsize=14)
    ax.set_title(
        f"TUKU F3 — Residual drift ({sched_name}), blind era 2019–2023",
        fontsize=14
    )
    ax.tick_params(labelsize=13)
    ax.legend(fontsize=12, loc="upper left")
    ax.grid(True, alpha=0.35)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  PNG: {out_path}")


# ── JSON writer ───────────────────────────────────────────────────────────────

class _NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer,)):   return int(obj)
        if isinstance(obj, (np.floating,)):  return float(obj)
        if isinstance(obj, (np.bool_,)):     return bool(obj)
        if isinstance(obj, np.ndarray):      return obj.tolist()
        return super().default(obj)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    tee = _Tee(LOG_PATH)
    sys.stdout = tee
    try:
        _main_inner()
    finally:
        tee.close()


def _main_inner():
    print("=" * 75)
    print("28_f3_tau_uncapped.py — Red Team Task C: F3 consolidation-lag uncap")
    print("=" * 75)
    print(f"  TAU_EXT_F3={TAU_EXT_F3}  TAU_MAX_PRODUCTION={TAU_MAX_PRODUCTION}")
    print(f"  Authorization: user-authorized uncap, 2026-06-12")
    print(f"  Calibration window: {DENSE_START.date()} .. {DENSE_END.date()}")
    print(f"  Blind-era scoring:  {BLIND_START.date()} .. {BLIND_END.date()}")
    print(f"  Leakage manifest: calibration ends {DENSE_END.date()} < scoring starts {BLIND_START.date()}")

    # ── Step 1: calibration ──────────────────────────────────────────────────
    calib_result, uncapped_model = calibrate_f3_uncapped()
    tau_best = calib_result["tau_best_uncapped"]

    # Save calibration JSON immediately
    calib_json_path = OUT_DIR / "f3_uncapped_calibration.json"
    with open(calib_json_path, "w") as f:
        json.dump(calib_result, f, indent=2, cls=_NpEncoder)
    print(f"\n  Written: {calib_json_path}")

    # Plot SSE curve
    sse_list = calib_result["sse_curve"]["sse"]
    plot_tau_sse_curve(sse_list, tau_best, PLOT_DIR / "f3_tau_sse_curve.png")

    # ── Build uncapped F3 driver frame ────────────────────────────────────────
    print(f"\n  Building uncapped F3 driver frame at tau={tau_best} ...")
    uncapped_f3_frame = build_layer_drivers(
        layer=LAYER, tau=tau_best,
        gwl_feather=GWL_ROOT / GWL_FNAME,
        wellcode=WELLCODE,
        gps_csv=GPS_CSV,
        mlcw_inc_feather=MLCW_INC,
        ref_date=REF_DATE,
    )
    uncapped_f3_frame["date"] = pd.to_datetime(uncapped_f3_frame["date"])
    print(f"  Frame shape: {uncapped_f3_frame.shape}")

    # ── Step 2: load baseline frozen models and driver frames ─────────────────
    print("\n  Loading baseline (capped) frozen models and driver frames ...")
    all_frozen_models, all_frames = load_all_models_and_frames()

    # Load genuine truth
    truth_df = load_genuine_truth()
    print(f"  Genuine truth: {len(truth_df)} rows")

    ref_dates    = all_frames[ALL_LAYERS[0]]["date"]
    truth_aligned = align_genuine_to_epoch(truth_df, ref_dates, tolerance_days=3)
    truth_blind   = truth_aligned[
        (truth_aligned["model_date"] >= BLIND_START) &
        (truth_aligned["model_date"] <= BLIND_END)
    ].copy()
    blind_genuine_dates = pd.DatetimeIndex(truth_blind["model_date"].unique())
    all_blind_genuine_set: set = set(blind_genuine_dates.tolist())
    print(f"  Genuine blind-era visits aligned: {len(blind_genuine_dates)}")

    carrier_noise = estimate_carrier_noise()
    print(f"  Carrier noise: {carrier_noise:.4f} mm")

    # Build schedules
    schedules = build_schedules(blind_genuine_dates)
    print("\n  Schedule summary:")
    for sn, sd in schedules.items():
        print(f"    {sn:<12} : {len(sd):3d} visits")

    # Seed conformal bank
    seed_genuine = truth_aligned[
        (truth_aligned["model_date"] >= SEED_START) &
        (truth_aligned["model_date"] <= SEED_END)
    ]
    seed_genuine_dates = sorted(seed_genuine["model_date"].unique().tolist())
    bank_seeded = seed_conformal_bank(
        seed_schedule_dates=seed_genuine_dates,
        frames=all_frames,
        truth_aligned=truth_aligned,
        carrier_noise=carrier_noise,
        uncapped_f3_model=uncapped_model,
        uncapped_f3_frame=uncapped_f3_frame,
    )

    # ── Step 3: run schedules ─────────────────────────────────────────────────
    all_results: dict[str, dict] = {}
    for sn in SCHEDULE_NAMES:
        result = run_f3_uncapped_schedule(
            schedule_name=sn,
            visit_dates=schedules[sn],
            all_frames=all_frames,
            all_frozen_models=all_frozen_models,
            uncapped_f3_model=uncapped_model,
            uncapped_f3_frame=uncapped_f3_frame,
            bank_seed=bank_seeded,
            truth_aligned=truth_aligned,
            all_genuine_dates=all_blind_genuine_set,
        )
        all_results[sn] = result

    # Write per-schedule timeseries CSVs (F3 only)
    for sn, res in all_results.items():
        ts_data = res["ts_rows"][LAYER]
        df_ts = pd.DataFrame(ts_data)
        # Add obs_at_visit column (NaN off-visit days)
        visit_obs = {pd.Timestamp(r["date"]): r["obs_mm"]
                     for r in res["preq_rows"][LAYER]}
        df_ts["obs_at_visit_mm"] = df_ts["date"].apply(
            lambda d: visit_obs.get(pd.Timestamp(d), float("nan"))
        )
        csv_path = OUT_DIR / f"f3_uncapped_{sn}_timeseries.csv"
        df_ts.to_csv(csv_path, index=False)
        print(f"  Written: {csv_path}")

    # ── Step 4: compute metrics ───────────────────────────────────────────────
    print("\n  Computing F3 metrics (uncapped) ...")
    uncapped_metrics: dict[str, dict] = {}
    for sn in SCHEDULE_NAMES:
        preq = all_results[sn]["preq_rows"][LAYER]
        uncapped_metrics[sn] = compute_f3_metrics_for_schedule(sn, preq)
        um = uncapped_metrics[sn]
        print(f"    [{sn:<12}] n={um.get('n_total',0):3d}  "
              f"r_all={um.get('detrended_r_all'):.4f}  "
              f"r_post={um.get('detrended_r_post'):.4f}  "
              f"RMSE_post={um.get('RMSE_post_entry_mm'):.2f} mm  "
              f"drought_max={um.get('drought_max_abs_err_mm'):.1f} mm  "
              f"xcorr_lag={um.get('cross_corr_lag_epochs')} ep ({um.get('cross_corr_lag_days'):.0f} d)"
              if all(v is not None for v in [
                  um.get('detrended_r_all'), um.get('detrended_r_post'),
                  um.get('RMSE_post_entry_mm'), um.get('drought_max_abs_err_mm'),
                  um.get('cross_corr_lag_epochs')
              ]) else f"    [{sn:<12}] {um}")

    print("\n  Computing F3 metrics (capped — reading from disk) ...")
    capped_metrics: dict[str, dict] = {}
    for sn in SCHEDULE_NAMES:
        capped_metrics[sn] = compute_f3_capped_metrics_from_disk(sn)
        cm = capped_metrics[sn]
        print(f"    [{sn:<12}] r_post={cm.get('detrended_r_post')}  "
              f"drought_max={cm.get('drought_max_abs_err_mm')}  "
              f"xcorr_lag={cm.get('cross_corr_lag_epochs')}")

    # ── Step 5: decision rule ─────────────────────────────────────────────────
    f3_restored, verdict = apply_decision_rule(uncapped_metrics, capped_metrics)
    print(f"\n  {'='*60}")
    print(f"  DECISION RULE — f3_restored = {f3_restored}")
    print(f"  Verdict: {verdict['verdict_note']}")
    print(f"  r(annual, uncapped) = {verdict['decision_criteria']['r_annual_uncapped']} "
          f"(threshold=0.5, passes={verdict['decision_criteria']['r_passes']})")
    print(f"  drought max|err| annual (mm) = {verdict['decision_criteria']['drought_max_abs_err_annual_mm']} "
          f"(threshold=20 mm, passes={verdict['decision_criteria']['drought_passes']})")

    # ── Step 6: plots ─────────────────────────────────────────────────────────
    print("\n  Generating plots ...")
    # Use annual schedule for comparison plots (headline cadence)
    annual_capped_preq   = compute_f3_capped_preq_rows("annual")
    annual_uncapped_preq = all_results["annual"]["preq_rows"][LAYER]
    annual_ts_path = _TAU_DEMO / "results" / "seq" / "annual" / "TUKU_F3_seq_timeseries.csv"

    plot_detrended_dynamics(
        sched_name="annual",
        capped_preq=annual_capped_preq,
        uncapped_preq=annual_uncapped_preq,
        capped_ts_path=annual_ts_path,
        uncapped_ts_rows=all_results["annual"]["ts_rows"][LAYER],
        out_path=PLOT_DIR / "f3_detrended_dynamics.png",
    )
    plot_residual_drift(
        sched_name="annual",
        capped_preq=annual_capped_preq,
        uncapped_preq=annual_uncapped_preq,
        out_path=PLOT_DIR / "f3_residual_drift.png",
    )

    # ── Step 7: assemble and write walkforward metrics JSON ───────────────────
    wf_json = {
        "script": "28_f3_tau_uncapped.py",
        "layer":  LAYER,
        "tau_uncapped": tau_best,
        "tau_production_cap": TAU_MAX_PRODUCTION,
        "calibration_window": calib_result["calibration_window"],
        "blind_scoring_window": f"{BLIND_START.date()} .. {BLIND_END.date()}",
        "leakage_manifest": calib_result["leakage_manifest"],
        "S_ke_activated": calib_result["S_ke_activated"],
        "S_ke_at_uncapped_tau": calib_result["S_ke"],
        "S_kv_at_uncapped_tau": calib_result["S_kv"],
        "schedules": SCHEDULE_NAMES,
        "uncapped_metrics": uncapped_metrics,
        "capped_metrics":   capped_metrics,
        "decision": verdict,
        "f3_restored": f3_restored,
        "authorized_tau_exception": calib_result.get("authorized_tau_exception"),
    }
    wf_path = OUT_DIR / "f3_uncapped_walkforward_metrics.json"
    with open(wf_path, "w") as f:
        json.dump(wf_json, f, indent=2, cls=_NpEncoder)
    print(f"\n  Written: {wf_path}")

    # ── Step 8: re-read verification ──────────────────────────────────────────
    print(f"\n  RE-READ VERIFICATION:")
    with open(calib_json_path) as f:
        c_disk = json.load(f)
    calib_checks = {
        "tau_best": c_disk["tau_best_uncapped"] == tau_best,
        "S_ke":     abs(c_disk["S_ke"] - calib_result["S_ke"]) < 1e-8,
        "S_kv":     abs(c_disk["S_kv"] - calib_result["S_kv"]) < 1e-8,
        "a":        abs(c_disk["a"]    - calib_result["a"])    < 1e-8,
    }
    calib_ok = all(calib_checks.values())
    print(f"  calibration JSON: {'VERIFIED' if calib_ok else 'MISMATCH'} {calib_checks}")

    with open(wf_path) as f:
        wf_disk = json.load(f)
    wf_checks = {
        "f3_restored":        wf_disk["f3_restored"] == f3_restored,
        "tau_uncapped":       wf_disk["tau_uncapped"] == tau_best,
        "S_ke_activated":     wf_disk["S_ke_activated"] == calib_result["S_ke_activated"],
    }
    wf_ok = all(wf_checks.values())
    print(f"  walkforward JSON: {'VERIFIED' if wf_ok else 'MISMATCH'} {wf_checks}")

    # Verify CSVs
    for sn in SCHEDULE_NAMES:
        csv_path = OUT_DIR / f"f3_uncapped_{sn}_timeseries.csv"
        ok = csv_path.exists() and pd.read_csv(csv_path).shape[0] > 0
        print(f"  CSV {sn}: {'EXISTS ({} rows)'.format(pd.read_csv(csv_path).shape[0]) if ok else 'MISSING'}")

    # PNG existence check
    for png in ["f3_detrended_dynamics.png", "f3_residual_drift.png", "f3_tau_sse_curve.png"]:
        p = PLOT_DIR / png
        print(f"  PNG {'EXISTS' if p.exists() else 'MISSING'}: {p}")

    print(f"\n  {'='*75}")
    print(f"  SUMMARY")
    print(f"  {'='*75}")
    print(f"  τ_best (uncapped) = {tau_best} epochs ({tau_best * 5} days)")
    print(f"  τ production cap  = {TAU_MAX_PRODUCTION} epochs ({TAU_MAX_PRODUCTION * 5} days)")
    print(f"  S_ke = {calib_result['S_ke']} mm/m  (activated from 0: {calib_result['S_ke_activated']})")
    print(f"  S_kv = {calib_result['S_kv']} mm/m")
    print(f"  r²_train = {calib_result['r2_train']}  RMSE_train = {calib_result['rmse_train_mm']} mm")
    print(f"\n  Detrended r (capped vs uncapped):")
    for sn in SCHEDULE_NAMES:
        r_uc = uncapped_metrics[sn].get("detrended_r_post") or uncapped_metrics[sn].get("detrended_r_all")
        r_c  = capped_metrics[sn].get("detrended_r_post")   or capped_metrics[sn].get("detrended_r_all")
        print(f"    [{sn:<12}] capped={r_c}  uncapped={r_uc}  delta={round(float(r_uc or 0) - float(r_c or 0), 4) if r_uc is not None and r_c is not None else 'n/a'}")
    print(f"\n  Drought max|err| (capped vs uncapped, annual):")
    print(f"    capped   = {capped_metrics['annual'].get('drought_max_abs_err_mm')} mm")
    print(f"    uncapped = {uncapped_metrics['annual'].get('drought_max_abs_err_mm')} mm")
    print(f"\n  Cross-corr lag shift (capped vs uncapped, annual):")
    print(f"    capped lag   = {capped_metrics['annual'].get('cross_corr_lag_epochs')} epochs "
          f"({capped_metrics['annual'].get('cross_corr_lag_days')} days)")
    print(f"    uncapped lag = {uncapped_metrics['annual'].get('cross_corr_lag_epochs')} epochs "
          f"({uncapped_metrics['annual'].get('cross_corr_lag_days')} days)")
    print(f"\n  f3_restored = {f3_restored}")
    print(f"  Verdict: {verdict['verdict_note']}")
    print(f"\n  All outputs: {OUT_DIR}")
    print(f"  Log:  {LOG_PATH}")
    print(f"  DONE.")


def compute_f3_capped_preq_rows(sched_name: str) -> list[dict]:
    """Reconstruct the prequential rows for capped F3 from the metrics.json innovations."""
    sched_dir_map = {
        "anchor_once": OUT_DIR / "anchor_once",
        "annual":      _TAU_DEMO / "results" / "seq" / "annual",
        "semiannual":  _TAU_DEMO / "results" / "seq" / "semiannual",
        "monthly":     _TAU_DEMO / "results" / "seq" / "monthly",
    }
    metrics_path = sched_dir_map[sched_name] / "metrics.json"
    ts_path      = sched_dir_map[sched_name] / "TUKU_F3_seq_timeseries.csv"

    if not metrics_path.exists() or not ts_path.exists():
        return []

    with open(metrics_path) as f:
        m = json.load(f)
    innovations = m.get("layers", {}).get("F3", {}).get("innovations", [])

    ts_df = pd.read_csv(ts_path)
    ts_df["date_ts"] = pd.to_datetime(ts_df["date"])
    ts_lookup = {row["date_ts"]: row["pred_mm"] for _, row in ts_df.iterrows()
                 if pd.notna(row["pred_mm"])}

    rows = []
    for inn in innovations:
        d = pd.Timestamp(inn["date"])
        pred_v = ts_lookup.get(d)
        if pred_v is None:
            continue
        pred_v = float(pred_v)
        obs_v  = pred_v + float(inn["value"])
        rows.append({
            "date": inn["date"],
            "obs_mm":      round(obs_v,  4),
            "pred_mm":     round(pred_v, 4),
            "innovation_mm": round(float(inn["value"]), 4),
            "in_band":     inn.get("in_band", False),
        })
    return rows


if __name__ == "__main__":
    main()
