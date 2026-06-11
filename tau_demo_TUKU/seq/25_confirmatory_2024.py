"""
25_confirmatory_2024.py — Task M8.4: Confirmatory 2024 grading (held-back exam).

Physical story: The TUKU compacting sediment column has been compressing continuously
since 2019 under ongoing groundwater extraction.  This script walks the frozen
2010-2018 model continuously from DENSE_END (2018-12-31) through all of 2024,
assimilating genuine field visits under two operationally realistic cadences
(semiannual, annual).  The 2024 visits are revealed only once; scores are recorded
prequentially (before each reveal).  This is the held-back exam — graded once,
result stands as measured regardless of outcome.

Usage:
    $env:PYTHONPATH=""; conda run -n fafalab2 python tau_demo_TUKU/seq/25_confirmatory_2024.py

Outputs:
    tau_demo_TUKU/results/seq/confirmatory_2024.json
    tau_demo_TUKU/plots/seq/confirmatory_2024.png

Hard rule (Task 8.4): The walk-forward engine (24_walk_forward_rehearsal.py) and the
frozen calibration (results/seq/frozen_calibration.json) are FROZEN.  This script
imports/reuses — never edits — the engine modules.  If a post-freeze edit was forced,
it is recorded under JSON field "post_freeze_edits".

GPS-ends-2024 note: GPS data ends 2024-12-31, so 2024 is the last reachable year.
The walk cannot extend beyond 2024-12-31.
"""

from __future__ import annotations

import copy
import json
import sys
import warnings
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore", category=UserWarning)

# ── Paths ─────────────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve()
_TAU_DEMO = _HERE.parent.parent    # tau_demo_TUKU/
_ROOT = _TAU_DEMO.parent           # repo root

for _p in [str(_TAU_DEMO), str(_ROOT), str(_ROOT / "scripts")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Reuse engine modules (do NOT edit them — Task 8.4 hard rule)
from tau_demo_TUKU.seq.drivers import build_layer_drivers      # noqa: E402
from tau_demo_TUKU.seq.frozen_model import FrozenLayerModel    # noqa: E402
from tau_demo_TUKU.seq.time_oracle import TimeOracle, LeakageError  # noqa: E402
from tau_demo_TUKU.seq.conformal import ConformalBank          # noqa: E402

# Import seed_conformal_bank and _epochs_between from the rehearsal script
# (module name starts with a digit so use importlib.util).
import importlib.util as _ilu
_rehearsal_path = _HERE.parent / "24_walk_forward_rehearsal.py"
_spec = _ilu.spec_from_file_location("_rehearsal", _rehearsal_path)
_rehearsal = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_rehearsal)

seed_conformal_bank  = _rehearsal.seed_conformal_bank
_epochs_between      = _rehearsal._epochs_between
align_genuine_to_epoch = _rehearsal.align_genuine_to_epoch

# ── Configuration ─────────────────────────────────────────────────────────────
LAYERS = ["F1", "T1", "F2", "T2", "F3", "F4"]

DENSE_END      = pd.Timestamp("2018-12-31")
BLIND_START    = pd.Timestamp("2019-01-01")
CONF_END       = pd.Timestamp("2024-12-31")   # GPS ends here — last reachable year
YEAR_2024_START = pd.Timestamp("2024-01-01")
YEAR_2024_END   = pd.Timestamp("2024-12-31")

# Conformal bank seeding window (mirrors 24_walk_forward_rehearsal.py exactly)
SEED_START       = pd.Timestamp("2015-01-01")
SEED_END         = pd.Timestamp("2018-12-31")
SEED_FIT_START   = pd.Timestamp("2010-01-16")
SEED_FIT_END     = pd.Timestamp("2014-12-31")

REF_DATE = "2015-01-16"

# Data paths (identical to 24_walk_forward_rehearsal.py)
GWL_ROOT   = _ROOT / "data" / "gwl" / "well_timeseries"
GPS_CSV    = _ROOT / "data" / "gps" / "modeled" / "TKJS_model.csv"
MLCW_INC   = _TAU_DEMO / "data" / "incremental_data" / "mlcw_diff_cleaned.feather"
ORIG_CSV   = _ROOT / "data" / "mlcw" / "group_byLayer_orig" / "TUKU_orig_grouped.csv"
RECONST_CSV = _TAU_DEMO / "data" / "TUKU_reconst_grouped.csv"
FROZEN_JSON = _TAU_DEMO / "results" / "seq" / "frozen_calibration.json"

WELL_CONFIG: dict[str, tuple[str, str]] = {
    "F1": ("HONGLUN_gwl_timeseries.feather", "09050111"),
    "T1": ("HONGLUN_gwl_timeseries.feather", "09050111"),
    "F2": ("TUKU_gwl_timeseries.feather",    "09050321"),
    "T2": ("LUNZI_gwl_timeseries.feather",   "09170121"),
    "F3": ("TUKU_gwl_timeseries.feather",    "09050331"),
    "F4": ("LIUZHUANG_gwl_timeseries.feather","09080251"),
}

# Level-1 apex thresholds (from 24_walk_forward_rehearsal.py)
THIN_LAYERS  = {"F1", "T1", "T2", "F4"}   # MAE < 5 mm, RMSE < 10 mm
THICK_LAYERS = {"F2", "F3"}               # MAE < 10 mm, RMSE < 20 mm
MAE_THRESH   = {"F1": 5, "T1": 5, "T2": 5, "F4": 5, "F2": 10, "F3": 10}
RMSE_THRESH  = {"F1": 10, "T1": 10, "T2": 10, "F4": 10, "F2": 20, "F3": 20}

OUT_RESULTS = _TAU_DEMO / "results" / "seq"
OUT_PLOTS   = _TAU_DEMO / "plots"   / "seq"


# ── JSON encoder ──────────────────────────────────────────────────────────────
class _NpEnc(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer,)):  return int(obj)
        if isinstance(obj, (np.floating,)): return float(obj)
        if isinstance(obj, (np.bool_,)):    return bool(obj)
        if isinstance(obj, np.ndarray):     return obj.tolist()
        return super().default(obj)


# ── Data loaders ──────────────────────────────────────────────────────────────
def load_frozen_models() -> dict[str, FrozenLayerModel]:
    with open(FROZEN_JSON) as f:
        calib = json.load(f)
    models = {}
    for L in LAYERS:
        d = calib["layers"][L]
        m = FrozenLayerModel(
            layer=L, a=d["a"], c=d["c"],
            S_ke=d["S_ke"], S_kv=d["S_kv"],
            tau=d["tau"], use_u=d["use_u"], use_V=d["use_V"],
            beta=0.0, h_c=d["h_c"],
        )
        models[L] = m
    return models


def build_all_drivers() -> dict[str, pd.DataFrame]:
    """Build full-timeline (through GPS end = 2024-12-31) driver frames."""
    frames: dict[str, pd.DataFrame] = {}
    with open(FROZEN_JSON) as f:
        calib = json.load(f)
    for L in LAYERS:
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
    return frames


def load_genuine_truth() -> pd.DataFrame:
    df = pd.read_csv(ORIG_CSV)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime").reset_index(drop=True)
    return df   # columns: datetime, F1, T1, F2, T2, F3, T3, F4


# ── Schedule builder for 2024 ─────────────────────────────────────────────────
def build_2024_schedules(
    genuine_dates_all: pd.DatetimeIndex,
) -> dict[str, list[pd.Timestamp]]:
    """Build semiannual and annual schedules for the CONTINUOUS walk 2019→2024.

    The schedules cover the ENTIRE walk from BLIND_START through CONF_END so
    the conformal bank accumulates continuously.  2024 scoring is extracted
    as a subset of the full walk.

    genuine_dates_all: all aligned genuine visit dates from 2019 onward
    (through 2024-12-31).
    """
    dates_sorted = sorted(genuine_dates_all.dropna().unique())

    def nearest_genuine(target: pd.Timestamp, tol_days: int = 45) -> Optional[pd.Timestamp]:
        min_gap = pd.Timedelta(days=999)
        best = None
        for d in dates_sorted:
            gap = abs(d - target)
            if gap < min_gap:
                min_gap = gap
                best = d
        if min_gap > pd.Timedelta(days=tol_days):
            return None
        return best

    def subsample(spacing_days: int) -> list[pd.Timestamp]:
        result = []
        anchor = pd.Timestamp("2019-01-01")
        used: set = set()
        t = anchor
        end = CONF_END + pd.Timedelta(days=spacing_days)
        while t <= end:
            nd = nearest_genuine(t)
            if nd is not None and nd not in used:
                used.add(nd)
                result.append(nd)
            t += pd.Timedelta(days=spacing_days)
        return sorted(result)

    return {
        "semiannual": subsample(180),
        "annual":     subsample(365),
    }


# ── Continuous walk-forward 2019→2024 ─────────────────────────────────────────
def run_continuous_walk(
    schedule_name: str,
    visit_dates: list[pd.Timestamp],
    frames: dict[str, pd.DataFrame],
    frozen_models: dict[str, FrozenLayerModel],
    bank_seed: ConformalBank,
    truth_aligned: pd.DataFrame,   # aligned to 5-day grid, all years
) -> dict:
    """Walk continuously from DENSE_END through CONF_END (2024-12-31).

    The walk assimilates genuine visits from 2019 onward per the given schedule.
    This is the key invariant: the 2024 state is the GENUINE continuation of the
    2019-2023 walk, not a fresh start.

    Scoring: only 2024 genuine visits are counted in the grade.
    Prequential: score is recorded BEFORE assimilation at each visit.

    Returns a results dict with separate 2024-only metrics.
    """
    print(f"\n  Schedule '{schedule_name}': {len(visit_dates)} visits (2019–2024)")

    models: dict[str, FrozenLayerModel] = {
        L: copy.deepcopy(frozen_models[L]) for L in LAYERS
    }
    bank = copy.deepcopy(bank_seed)

    # Full epoch list from BLIND_START to CONF_END (F1 frame as reference grid)
    ref_df = frames[LAYERS[0]]
    all_epochs = sorted(
        ref_df.loc[
            (ref_df["date"] >= BLIND_START) & (ref_df["date"] <= CONF_END),
            "date",
        ].tolist()
    )
    if not all_epochs:
        raise RuntimeError("No epochs found in 2019-2024 driver frame.")

    visit_set = set(visit_dates)
    # All genuine visits 2019–2024 (for scoring set — not just 2024)
    truth_all_era = truth_aligned[
        (truth_aligned["model_date"] >= BLIND_START) &
        (truth_aligned["model_date"] <= CONF_END)
    ]

    last_visit: dict[str, pd.Timestamp] = {L: DENSE_END for L in LAYERS}
    prev_d_gps: dict[str, float]        = {L: float("nan") for L in LAYERS}

    # Per-layer timeseries (full 2019-2024)
    ts_rows: dict[str, list[dict]] = {L: [] for L in LAYERS}
    # Per-layer prequential innovations at genuine 2024 visits only
    preq_2024: dict[str, list[dict]] = {L: [] for L in LAYERS}

    oracle = TimeOracle(DENSE_END)
    leakage_fired = False

    for epoch_date in all_epochs:
        try:
            oracle.advance(epoch_date)
        except LeakageError as e:
            print(f"  LEAKAGE ERROR: {e}")
            leakage_fired = True
            break

        is_2024 = (epoch_date >= YEAR_2024_START) and (epoch_date <= YEAR_2024_END)

        for L, m in models.items():
            df = frames[L]
            row_mask = df["date"] == epoch_date
            if not row_mask.any():
                continue
            row    = df[row_mask].iloc[0]
            d_val  = float(row["d_gps"])
            u_lag  = float(row["u_lag"])
            V_lag  = float(row["V_lag"])

            # Predict
            pred = float("nan")
            if np.isfinite(d_val) and np.isfinite(u_lag) and np.isfinite(V_lag):
                pred = float(m.predict(d_val, u_lag, V_lag))

            horizon = _epochs_between(last_visit[L], epoch_date, all_epochs)
            hw = bank.half_width(L, horizon)

            ts_rows[L].append({
                "date":            epoch_date.isoformat(),
                "pred_mm":         round(pred, 4) if np.isfinite(pred) else None,
                "half_width_mm":   round(hw, 4)   if np.isfinite(hw)   else None,
                "horizon_epochs":  horizon,
                "is_2024":         is_2024,
            })

            # Is this a genuine-visit scoring date?
            truth_row = truth_all_era[truth_all_era["model_date"] == epoch_date]
            obs_val = float("nan")
            if len(truth_row) > 0:
                obs_val = float(truth_row.iloc[0].get(L, float("nan")))

            is_visit = (epoch_date in visit_set)
            has_obs  = np.isfinite(obs_val) and np.isfinite(pred)

            if has_obs:
                innovation = obs_val - pred
                in_band = bool(np.isfinite(hw) and abs(innovation) <= hw)

                # Prequential score: record ONLY if 2024 genuine visit
                if is_2024:
                    preq_2024[L].append({
                        "date":             epoch_date.isoformat(),
                        "obs_mm":           round(obs_val, 4),
                        "pred_mm":          round(pred, 4),
                        "innovation_mm":    round(innovation, 4),
                        "half_width_mm":    round(hw, 4) if np.isfinite(hw) else None,
                        "in_band":          in_band,
                        "horizon_epochs":   horizon,
                        "is_scheduled_visit": is_visit,
                    })

                # Assimilate: only at scheduled visits
                if is_visit:
                    bank.add(L, horizon, abs(innovation))
                    m.assimilate(innovation)
                    last_visit[L] = epoch_date

    return {
        "schedule_name": schedule_name,
        "ts_rows":     ts_rows,
        "preq_2024":   preq_2024,
        "leakage_fired": leakage_fired,
    }


# ── Dynamics diagnostic (V2, vs dense fill) ───────────────────────────────────
def compute_dynamics_diagnostic(
    ts_rows: list[dict],
    reconst_df: pd.DataFrame,
    layer: str,
) -> dict:
    """Amplitude ratio and detrended correlation of model increments vs dense fill.

    Uses 2024 model predictions aligned against the dense reconstruction for
    the same year.
    """
    pred_series = pd.Series(
        {pd.Timestamp(r["date"]): r["pred_mm"]
         for r in ts_rows
         if r["pred_mm"] is not None and r["is_2024"]}
    ).sort_index()

    rc = reconst_df[["datetime", layer]].dropna(subset=[layer]).copy()
    rc["datetime"] = pd.to_datetime(rc["datetime"])
    rc_2024 = rc[(rc["datetime"] >= YEAR_2024_START) & (rc["datetime"] <= YEAR_2024_END)]
    obs_series = pd.Series(
        {pd.Timestamp(r["datetime"]): float(r[layer])
         for _, r in rc_2024.iterrows()
         if np.isfinite(float(r[layer]))}
    ).sort_index()

    amp_ratio    = float("nan")
    detrended_corr = float("nan")

    if len(pred_series) < 5 or len(obs_series) < 5:
        return {
            "amplitude_ratio_increments": None,
            "detrended_corr":             None,
            "note": "insufficient data for 2024 dynamics diagnostic",
        }

    # Amplitude ratio via increment std
    d_pred = np.diff(pred_series.values.astype(float))
    d_obs  = np.diff(obs_series.values.astype(float))
    std_pred = np.std(d_pred) if len(d_pred) > 2 else float("nan")
    std_obs  = np.std(d_obs)  if len(d_obs)  > 2 else float("nan")
    if np.isfinite(std_pred) and np.isfinite(std_obs) and std_obs > 1e-9:
        amp_ratio = float(std_pred / std_obs)

    # Detrended correlation (align by nearest date)
    combined = pd.merge_asof(
        obs_series.reset_index().rename(columns={"index": "date", 0: "obs"}),
        pred_series.reset_index().rename(columns={"index": "date", 0: "pred"}),
        on="date",
        direction="nearest",
        tolerance=pd.Timedelta("5D"),
    ).dropna()

    if len(combined) >= 5:
        t = np.arange(len(combined), dtype=float)
        p_o = np.polyfit(t, combined["obs"].values, 1)
        p_p = np.polyfit(t, combined["pred"].values, 1)
        o_dt = combined["obs"].values  - np.polyval(p_o, t)
        p_dt = combined["pred"].values - np.polyval(p_p, t)
        if np.std(o_dt) > 1e-9 and np.std(p_dt) > 1e-9:
            detrended_corr = float(np.corrcoef(o_dt, p_dt)[0, 1])

    return {
        "amplitude_ratio_increments": round(amp_ratio,    4) if np.isfinite(amp_ratio)    else None,
        "detrended_corr":             round(detrended_corr, 4) if np.isfinite(detrended_corr) else None,
        "note": "2024 model vs dense reconstruction, detrended",
    }


# ── Per-layer metrics for 2024 ────────────────────────────────────────────────
def compute_2024_metrics(
    schedule_name: str,
    preq_2024: dict[str, list[dict]],
    ts_rows: dict[str, list[dict]],
    reconst_df: pd.DataFrame,
) -> dict:
    """Compute 2024-only prequential metrics per layer."""
    layers_out = {}

    for L in LAYERS:
        rows = preq_2024[L]
        n = len(rows)

        mae_mm  = float("nan")
        rmse_mm = float("nan")

        if n > 0:
            errs = [abs(r["innovation_mm"]) for r in rows]
            mae_mm  = float(np.mean(errs))
            rmse_mm = float(np.sqrt(np.mean([e**2 for e in errs])))

        # Band coverage: fraction of 2024 prequential points where hw is defined
        # and |innovation| <= hw.
        hw_defined = [r for r in rows if r["half_width_mm"] is not None
                      and np.isfinite(r["half_width_mm"])]
        n_hw = len(hw_defined)
        n_in_band = sum(1 for r in hw_defined if r["in_band"])

        if n_hw > 0:
            coverage = float(n_in_band / n_hw)
        else:
            coverage = None   # NEVER fabricate — see Task 8.4 step 3

        # Mean half-width over all 2024 epochs where hw is defined
        hw_vals_all = [r["half_width_mm"] for r in ts_rows[L]
                       if r.get("is_2024") and r["half_width_mm"] is not None]
        mean_hw = float(np.mean(hw_vals_all)) if hw_vals_all else None

        # Dynamics diagnostic
        dyn = compute_dynamics_diagnostic(ts_rows[L], reconst_df, L)

        # Level-1 threshold check
        meets_thresh = (
            np.isfinite(mae_mm) and np.isfinite(rmse_mm) and
            mae_mm  <= MAE_THRESH[L] and
            rmse_mm <= RMSE_THRESH[L]
        )

        # Coverage check
        if coverage is None:
            coverage_ok = "undetermined"
            cov_note = (
                f"Band undefined for all {n_hw} 2024 prequential points — "
                "conformal bank has too few samples in the relevant horizon bucket "
                "at this sparse cadence.  Coverage cannot be measured."
            )
        else:
            coverage_ok = bool(coverage >= 0.85)
            cov_note = f"{n_in_band}/{n_hw} 2024 points within 90% conformal band."

        layers_out[L] = {
            "n_2024_points":              n,
            "MAE_mm":                     round(mae_mm,  3) if np.isfinite(mae_mm)  else None,
            "RMSE_mm":                    round(rmse_mm, 3) if np.isfinite(rmse_mm) else None,
            "band_coverage_fraction":     round(coverage, 3) if coverage is not None else None,
            "n_points_with_defined_band": n_hw,
            "mean_half_width_mm":         round(mean_hw, 2) if mean_hw is not None else None,
            "dynamics_vs_densefill_diagnostic": dyn,
            "meets_L1_threshold":         meets_thresh,
            "L1_thresholds":              {"MAE_mm": MAE_THRESH[L], "RMSE_mm": RMSE_THRESH[L]},
            "verdict": {
                "meets_threshold": meets_thresh,
                "coverage_ok":     coverage_ok,
                "coverage_value":  round(coverage, 3) if coverage is not None else None,
                "note":            cov_note,
            },
        }

    return layers_out


# ── Apex verdict ──────────────────────────────────────────────────────────────
def compute_apex_verdict(
    metrics_semi: dict,
    metrics_annual: dict,
) -> dict[str, dict]:
    """Compute per-schedule dp_seq_confirmatory verdict.

    PASS: >= 5 layers meet L1 thresholds AND >= 5 layers have defined coverage >= 0.85.
    Coverage is only counted for layers where it is DEFINED.
    """
    verdicts = {}
    for sched_name, metrics in [("semiannual", metrics_semi), ("annual", metrics_annual)]:
        n_thresh  = sum(1 for L in LAYERS if metrics[L]["meets_L1_threshold"])
        # Count only layers where coverage is defined
        defined_cov = [(L, metrics[L]["verdict"]["coverage_value"])
                       for L in LAYERS
                       if metrics[L]["verdict"]["coverage_value"] is not None]
        n_cov_defined = len(defined_cov)
        n_cov_pass    = sum(1 for _, v in defined_cov if v >= 0.85)

        # Verdict logic
        if n_thresh >= 5 and n_cov_pass >= 5:
            dp = "PASS"
            reason = (f"{n_thresh}/6 layers meet L1 thresholds; "
                      f"{n_cov_pass}/{n_cov_defined} layers with defined coverage "
                      f">= 0.85 (required >= 5).")
        elif n_thresh >= 5 and n_cov_defined < 5:
            dp = "PARTIAL"
            reason = (f"{n_thresh}/6 layers meet L1 thresholds but only "
                      f"{n_cov_defined}/6 layers have a defined band coverage — "
                      f"insufficient calibration data at this cadence to assess coverage.")
        elif n_thresh < 5:
            dp = "FAIL"
            reason = (f"Only {n_thresh}/6 layers meet L1 thresholds (required >= 5).")
        else:
            dp = "PARTIAL"
            reason = (f"{n_thresh}/6 layers meet L1 thresholds; "
                      f"only {n_cov_pass}/{n_cov_defined} layers with defined coverage "
                      f">= 0.85 (required >= 5).")

        verdicts[sched_name] = {
            "dp_seq_confirmatory": dp,
            "n_layers_threshold_pass": n_thresh,
            "n_layers_coverage_ge_0p85": n_cov_pass,
            "n_layers_coverage_defined": n_cov_defined,
            "reason": reason,
        }

    return verdicts


# ── Plot: 6-panel for 2024, showing annual schedule ───────────────────────────
def plot_2024_confirmatory(
    ts_rows_annual: dict[str, list[dict]],
    ts_rows_semi: dict[str, list[dict]],
    truth_aligned: pd.DataFrame,
    visit_dates_annual: list[pd.Timestamp],
    visit_dates_semi: list[pd.Timestamp],
    reconst_df: pd.DataFrame,
    out_path: Path,
) -> None:
    """6-panel PNG: one panel per layer, showing 2024 genuine observations,
    annual-schedule model prediction (line), 90% conformal band (shaded where defined),
    and visit ticks.  Font >= 14, axis labels + units, grid, tight, 300 dpi.

    The annual schedule is shown as the primary (conservative) case.
    """
    fig, axes = plt.subplots(3, 2, figsize=(18, 16), sharex=False)
    axes_flat = axes.flatten()

    reconst_copy = reconst_df.copy()
    reconst_copy["datetime"] = pd.to_datetime(reconst_copy["datetime"])

    visit_set_annual = set(visit_dates_annual)

    for i, L in enumerate(LAYERS):
        ax = axes_flat[i]

        # Annual-schedule timeseries (2024 only)
        rows_a = [r for r in ts_rows_annual[L] if r.get("is_2024")]
        if not rows_a:
            ax.set_title(f"{L} — no 2024 data", fontsize=14)
            continue

        dates_pred = [pd.Timestamp(r["date"]) for r in rows_a]
        pred_vals  = [r["pred_mm"] if r["pred_mm"] is not None else float("nan")
                      for r in rows_a]
        hw_vals    = [r["half_width_mm"] if r["half_width_mm"] is not None else float("nan")
                      for r in rows_a]
        pred_arr   = np.array(pred_vals, dtype=float)
        hw_arr     = np.array(hw_vals,   dtype=float)

        # Dense reconstruction (faint background, 2024 only)
        rc = reconst_copy[["datetime", L]].dropna(subset=[L])
        rc_2024 = rc[(rc["datetime"] >= YEAR_2024_START) & (rc["datetime"] <= YEAR_2024_END)]
        ax.plot(rc_2024["datetime"], rc_2024[L].values,
                color="gray", lw=0.8, alpha=0.4, label="Dense fill (reference)", zorder=1)

        # Annual model prediction line
        ax.plot(dates_pred, pred_arr, color="tab:blue", lw=1.8,
                label="Model (annual cadence)", zorder=3)

        # 90% conformal band (annual schedule, only where hw is defined)
        hw_finite = np.isfinite(hw_arr)
        if hw_finite.any():
            dh = np.array(dates_pred)[hw_finite]
            ph = pred_arr[hw_finite]
            hh = hw_arr[hw_finite]
            ax.fill_between(dh, ph - hh, ph + hh,
                            color="tab:blue", alpha=0.15,
                            label="90% conformal band (annual)", zorder=2)

        # Genuine 2024 observations (truth), shown at ALL genuine 2024 dates
        truth_2024 = truth_aligned[
            (truth_aligned["model_date"] >= YEAR_2024_START) &
            (truth_aligned["model_date"] <= YEAR_2024_END)
        ]
        all_2024_obs = [(pd.Timestamp(d), float(truth_2024.loc[truth_2024["model_date"] == d, L].values[0]))
                        for d in truth_2024["model_date"].tolist()
                        if L in truth_2024.columns
                        and not pd.isna(float(truth_2024.loc[truth_2024["model_date"] == d, L].values[0]))]
        if all_2024_obs:
            od, ov = zip(*all_2024_obs)
            ax.scatter(od, ov, color="tab:red", s=60, zorder=5,
                       label="Genuine 2024 field visits", marker="o")

        # Annual visit ticks (2024 only)
        for vd in visit_dates_annual:
            if YEAR_2024_START <= vd <= YEAR_2024_END:
                ax.axvline(x=vd, color="tab:green", lw=1.0, alpha=0.6, ls="--", zorder=1)

        # MAE / RMSE annotation on plot
        rows_preq = [r for r in ts_rows_annual[L] if r.get("is_2024") and r["pred_mm"] is not None]
        # Actually need preq_2024 for annotations — skip if n=0
        obs_pred_pairs = []
        for r in rows_a:
            td = truth_aligned[truth_aligned["model_date"] == pd.Timestamp(r["date"])]
            if len(td) > 0:
                ov_ = float(td.iloc[0].get(L, float("nan")))
                pv_ = r["pred_mm"] if r["pred_mm"] is not None else float("nan")
                if np.isfinite(ov_) and np.isfinite(pv_):
                    obs_pred_pairs.append((ov_, pv_))
        if obs_pred_pairs:
            errs_ = [abs(o - p) for o, p in obs_pred_pairs]
            mae_  = np.mean(errs_)
            rmse_ = np.sqrt(np.mean([e**2 for e in errs_]))
            thresh_str = f"(thresh MAE<{MAE_THRESH[L]}, RMSE<{RMSE_THRESH[L]})"
            ax.set_title(
                f"{L} — 2024 prequential (annual schedule)\n"
                f"MAE={mae_:.1f} mm  RMSE={rmse_:.1f} mm  {thresh_str}",
                fontsize=13, fontweight="bold",
            )
        else:
            ax.set_title(f"{L} — 2024 prequential (annual schedule)", fontsize=14, fontweight="bold")

        ax.set_xlabel("Date (2024)", fontsize=14)
        ax.set_ylabel("Cumulative compaction (mm)", fontsize=14)
        ax.tick_params(labelsize=12)
        ax.grid(True, alpha=0.35)
        ax.legend(fontsize=10, loc="lower left")

    fig.suptitle(
        "TUKU — Confirmatory 2024 grading (annual schedule shown; frozen model 2010–2018)\n"
        "GPS ends 2024-12-31 | Semiannual numbers in confirmatory_2024.json",
        fontsize=15, fontweight="bold",
    )
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  PNG: {out_path}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 75)
    print("Task M8.4 — Confirmatory 2024 grading (held-back exam, run once)")
    print("GPS ends 2024-12-31 — 2024 is the last reachable year.")
    print("=" * 75)

    # ── 1. Load data ──────────────────────────────────────────────────────────
    print("\nLoading data...")
    frozen_models = load_frozen_models()
    print(f"  Loaded {len(frozen_models)} frozen models.")

    frames = build_all_drivers()
    print(f"  Built driver frames through {frames[LAYERS[0]]['date'].max().date()}.")

    truth_df = load_genuine_truth()
    print(f"  Genuine truth: {len(truth_df)} rows, "
          f"{truth_df['datetime'].min().date()} — {truth_df['datetime'].max().date()}")

    reconst_df = pd.read_csv(RECONST_CSV)
    reconst_df["datetime"] = pd.to_datetime(reconst_df["datetime"])
    print(f"  Dense reconstruction: {len(reconst_df)} rows.")

    # ── 2. Align genuine truth to 5-day epochs ────────────────────────────────
    ref_dates = frames[LAYERS[0]]["date"]
    truth_aligned = align_genuine_to_epoch(truth_df, ref_dates, tolerance_days=3)
    print(f"  Truth aligned: {len(truth_aligned)} rows.")

    # 2024 genuine visits
    truth_2024 = truth_aligned[
        (truth_aligned["model_date"] >= YEAR_2024_START) &
        (truth_aligned["model_date"] <= YEAR_2024_END)
    ]
    n_genuine_2024 = len(truth_2024)
    genuine_2024_dates = sorted(truth_2024["model_date"].unique().tolist())
    print(f"  Genuine 2024 visits aligned to 5-day grid: {n_genuine_2024}")
    for d in genuine_2024_dates:
        print(f"    {pd.Timestamp(d).date()}")

    # ── 3. All genuine dates 2019–2024 (for schedule builder) ─────────────────
    truth_full_blind = truth_aligned[
        (truth_aligned["model_date"] >= BLIND_START) &
        (truth_aligned["model_date"] <= CONF_END)
    ]
    all_genuine_dates_idx = pd.DatetimeIndex(truth_full_blind["model_date"].unique())
    print(f"  Total genuine visits 2019–2024: {len(all_genuine_dates_idx)}")

    # ── 4. Carrier noise (from 2019-2024) ─────────────────────────────────────
    gps = pd.read_csv(GPS_CSV)
    gps["datetime"] = pd.to_datetime(gps["date"])
    gps = gps.sort_values("datetime").reset_index(drop=True)
    mask_gps = (gps["datetime"] >= BLIND_START) & (gps["datetime"] <= CONF_END)
    d_gps_vals = gps.loc[mask_gps, "modeled"].values.astype(float)
    carrier_noise = float(np.nanstd(np.diff(d_gps_vals))) if len(d_gps_vals) > 5 else float("nan")
    print(f"  Carrier noise (2019–2024 GPS increments std): {carrier_noise:.4f} mm")

    # ── 5. Build 2024-era schedules ───────────────────────────────────────────
    schedules = build_2024_schedules(all_genuine_dates_idx)
    print("\nSchedule summary (2019–2024 visits selected):")
    for s_name, s_dates in schedules.items():
        n_2024_vis = sum(1 for d in s_dates if YEAR_2024_START <= d <= YEAR_2024_END)
        print(f"  {s_name:<12}: {len(s_dates):3d} total visits, "
              f"{n_2024_vis} in 2024: {[d.date() for d in s_dates if YEAR_2024_START <= d <= YEAR_2024_END]}")

    # ── 6. Seed conformal bank (2015-2018, same as rehearsal) ─────────────────
    # Use seed_conformal_bank from the rehearsal module — faithfully replicated
    seed_genuine = truth_aligned[
        (truth_aligned["model_date"] >= SEED_START) &
        (truth_aligned["model_date"] <= SEED_END)
    ]
    seed_genuine_dates = sorted(seed_genuine["model_date"].unique().tolist())
    print(f"\nSeeding conformal bank with {len(seed_genuine_dates)} genuine visits (2015–2018)...")
    bank_seeded = seed_conformal_bank(
        seed_schedule_dates=seed_genuine_dates,
        frames=frames,
        truth_aligned=truth_aligned,
        carrier_noise=carrier_noise,
    )
    print(f"  Bank after seeding: {bank_seeded.census()}")

    # ── 7. Continuous walk 2019→2024 for each schedule ────────────────────────
    results: dict[str, dict] = {}
    for s_name in ["semiannual", "annual"]:
        result = run_continuous_walk(
            schedule_name=s_name,
            visit_dates=schedules[s_name],
            frames=frames,
            frozen_models=frozen_models,
            bank_seed=bank_seeded,
            truth_aligned=truth_aligned,
        )
        results[s_name] = result

    # ── 8. Compute 2024 metrics ───────────────────────────────────────────────
    metrics_semi   = compute_2024_metrics(
        "semiannual", results["semiannual"]["preq_2024"],
        results["semiannual"]["ts_rows"], reconst_df,
    )
    metrics_annual = compute_2024_metrics(
        "annual", results["annual"]["preq_2024"],
        results["annual"]["ts_rows"], reconst_df,
    )

    # ── 9. Apex verdict ───────────────────────────────────────────────────────
    apex = compute_apex_verdict(metrics_semi, metrics_annual)

    # ── 10. Print summary ─────────────────────────────────────────────────────
    print(f"\n{'='*75}")
    print("2024 CONFIRMATORY GRADE — PER LAYER")
    print(f"{'─'*75}")
    print(f"{'Layer':<6}  {'MAE(semi)':>10}  {'RMSE(semi)':>11}  {'MAE(ann)':>9}  {'RMSE(ann)':>10}  "
          f"{'L1 pass?':>8}  {'cov(ann)':>9}")
    print(f"{'─'*75}")
    for L in LAYERS:
        ms = metrics_semi[L]
        ma = metrics_annual[L]
        thresh_pass = ma["meets_L1_threshold"]
        cov_ann = ma["verdict"]["coverage_value"]
        print(
            f"{L:<6}  "
            f"{str(ms['MAE_mm']) if ms['MAE_mm'] else 'n/a':>10}  "
            f"{str(ms['RMSE_mm']) if ms['RMSE_mm'] else 'n/a':>11}  "
            f"{str(ma['MAE_mm']) if ma['MAE_mm'] else 'n/a':>9}  "
            f"{str(ma['RMSE_mm']) if ma['RMSE_mm'] else 'n/a':>10}  "
            f"{'PASS' if thresh_pass else 'FAIL':>8}  "
            f"{str(round(cov_ann,3)) if cov_ann is not None else 'undef':>9}"
        )

    print(f"\n{'='*75}")
    for sched_name, v in apex.items():
        print(f"dp_seq_confirmatory [{sched_name:>10}] = {v['dp_seq_confirmatory']}")
        print(f"  {v['reason']}")

    # ── 11. Build output JSON ─────────────────────────────────────────────────
    out_json = {
        "task": "M8.4 — Confirmatory 2024 grading",
        "graded_once": True,
        "gps_ends": "2024-12-31 — 2024 is the last reachable year",
        "frozen_calibration": str(FROZEN_JSON),
        "post_freeze_edits": [],
        "walk_era": {
            "start": BLIND_START.isoformat(),
            "end":   CONF_END.isoformat(),
            "note":  "Continuous walk from DENSE_END (2018-12-31) through 2024-12-31. "
                     "2024 state is genuine continuation of 2019–2023 walk.",
        },
        "seed_era": {
            "fit_window":  f"{SEED_FIT_START.date()} — {SEED_FIT_END.date()}",
            "walk_window": f"{SEED_START.date()} — {SEED_END.date()}",
        },
        "n_genuine_2024_visits": n_genuine_2024,
        "genuine_2024_dates": [d.isoformat() if hasattr(d, 'isoformat') else str(d)
                                for d in genuine_2024_dates],
        "carrier_noise_mm": round(carrier_noise, 5) if np.isfinite(carrier_noise) else None,
        "schedules": {
            sn: {
                "n_total_visits": len(schedules[sn]),
                "n_2024_visits":  sum(1 for d in schedules[sn]
                                      if YEAR_2024_START <= d <= YEAR_2024_END),
                "visit_dates_2024": [d.isoformat() for d in schedules[sn]
                                     if YEAR_2024_START <= d <= YEAR_2024_END],
                "leakage_fired": results[sn]["leakage_fired"],
                "layers": (metrics_semi if sn == "semiannual" else metrics_annual),
            }
            for sn in ["semiannual", "annual"]
        },
        "verdict_table": {
            sn: {
                L: {
                    "meets_threshold": (metrics_semi if sn == "semiannual" else metrics_annual)[L]["verdict"]["meets_threshold"],
                    "coverage_ok":     (metrics_semi if sn == "semiannual" else metrics_annual)[L]["verdict"]["coverage_ok"],
                    "coverage_value":  (metrics_semi if sn == "semiannual" else metrics_annual)[L]["verdict"]["coverage_value"],
                    "note":            (metrics_semi if sn == "semiannual" else metrics_annual)[L]["verdict"]["note"],
                }
                for L in LAYERS
            }
            for sn in ["semiannual", "annual"]
        },
        "apex": apex,
        "conformal_alpha": 0.10,
        "conformal_min_samples": 20,
    }

    # ── 12. Write JSON ────────────────────────────────────────────────────────
    OUT_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = OUT_RESULTS / "confirmatory_2024.json"
    with open(json_path, "w") as f:
        json.dump(out_json, f, indent=2, cls=_NpEnc)
    print(f"\n  Written: {json_path}")

    # ── 13. Plot ──────────────────────────────────────────────────────────────
    png_path = OUT_PLOTS / "confirmatory_2024.png"
    plot_2024_confirmatory(
        ts_rows_annual=results["annual"]["ts_rows"],
        ts_rows_semi=results["semiannual"]["ts_rows"],
        truth_aligned=truth_aligned,
        visit_dates_annual=schedules["annual"],
        visit_dates_semi=schedules["semiannual"],
        reconst_df=reconst_df,
        out_path=png_path,
    )

    # ── 14. Re-read verification ──────────────────────────────────────────────
    print(f"\n{'='*75}")
    print("RE-READ VERIFICATION:")
    with open(json_path) as f:
        on_disk = json.load(f)

    ok = True
    for sn in ["semiannual", "annual"]:
        for L in LAYERS:
            disk_mae  = on_disk["schedules"][sn]["layers"][L]["MAE_mm"]
            mem_mae   = (metrics_semi if sn == "semiannual" else metrics_annual)[L]["MAE_mm"]
            disk_rmse = on_disk["schedules"][sn]["layers"][L]["RMSE_mm"]
            mem_rmse  = (metrics_semi if sn == "semiannual" else metrics_annual)[L]["RMSE_mm"]
            match_mae  = (disk_mae  == mem_mae)  or (disk_mae  is None and mem_mae  is None)
            match_rmse = (disk_rmse == mem_rmse) or (disk_rmse is None and mem_rmse is None)
            if not match_mae or not match_rmse:
                print(f"  MISMATCH {sn}/{L}: "
                      f"disk_MAE={disk_mae} mem_MAE={mem_mae}  "
                      f"disk_RMSE={disk_rmse} mem_RMSE={mem_rmse}")
                ok = False
    print(f"  Printed == persisted: {'VERIFIED' if ok else 'MISMATCH — see above'}")

    # ── 15. Final summary ─────────────────────────────────────────────────────
    print(f"\n{'='*75}")
    print("FINAL SUMMARY")
    print(f"  Genuine 2024 visits (all layers): {n_genuine_2024}")
    print(f"  Semiannual 2024 visit dates: "
          f"{[d.date() for d in schedules['semiannual'] if YEAR_2024_START <= d <= YEAR_2024_END]}")
    print(f"  Annual 2024 visit dates:     "
          f"{[d.date() for d in schedules['annual'] if YEAR_2024_START <= d <= YEAR_2024_END]}")
    for sn, v in apex.items():
        print(f"  dp_seq_confirmatory [{sn}]: {v['dp_seq_confirmatory']} — {v['reason']}")
    print(f"\n  JSON: {json_path}")
    print(f"  PNG:  {png_path}")
    print(f"\n  DONE.")


if __name__ == "__main__":
    main()
