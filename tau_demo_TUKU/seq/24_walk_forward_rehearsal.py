"""
24_walk_forward_rehearsal.py — Task M8.3: Walk-forward rehearsal across 7 visiting cadences.

Physical story: The TUKU well went on a budget diet on 2019-01-01.  The frozen 2010-2018
model walks forward blind, driven only by continuous GPS and groundwater-head signals.  At
each scheduled field visit the crew reads the well once, the model hard-resets its level
bias, and accumulates the innovation into conformal bands bucketed by forecast horizon.
Seven cadences rehearse how often the operator needs to visit to keep forward error bounded.

Usage:
    $env:PYTHONPATH=""; conda run -n fafalab2 python tau_demo_TUKU/seq/24_walk_forward_rehearsal.py

Outputs (per schedule S):
    tau_demo_TUKU/results/seq/{S}/TUKU_{layer}_seq_timeseries.csv
    tau_demo_TUKU/results/seq/{S}/metrics.json
    tau_demo_TUKU/plots/seq/{S}/TUKU_seq_6layer.png
Plus:
    tau_demo_TUKU/results/seq/run_manifest.json
    tau_demo_TUKU/results/seq/cadence_degradation_curve.csv  (RMSE table)
    tau_demo_TUKU/results/seq/cadence_degradation_curve.json  (RMSE + MAE tables)
    tau_demo_TUKU/plots/seq/cadence_curve.png
"""

from __future__ import annotations

import copy
import json
import sys
import warnings
from dataclasses import dataclass, field
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

from tau_demo_TUKU.seq.drivers import build_layer_drivers      # noqa: E402
from tau_demo_TUKU.seq.frozen_model import FrozenLayerModel    # noqa: E402
from tau_demo_TUKU.seq.time_oracle import TimeOracle, LeakageError  # noqa: E402
from tau_demo_TUKU.seq.conformal import ConformalBank          # noqa: E402

# ── Configuration ─────────────────────────────────────────────────────────────
LAYERS = ["F1", "T1", "F2", "T2", "F3", "F4"]   # T3 instrumented but always NaN — skip

DENSE_END   = pd.Timestamp("2018-12-31")
BLIND_START = pd.Timestamp("2019-01-01")
BLIND_END   = pd.Timestamp("2023-12-31")
SEED_START  = pd.Timestamp("2015-01-01")
SEED_END    = pd.Timestamp("2018-12-31")
SEED_FIT_START = pd.Timestamp("2010-01-16")
SEED_FIT_END   = pd.Timestamp("2014-12-31")

REF_DATE = "2015-01-16"

# GWL well assignment (from 23_dense_calibration.py, authoritative)
GWL_ROOT = _ROOT / "data" / "gwl" / "well_timeseries"
GPS_CSV  = _ROOT / "data" / "gps" / "modeled" / "TKJS_model.csv"
MLCW_INC = _TAU_DEMO / "data" / "incremental_data" / "mlcw_diff_cleaned.feather"
ORIG_CSV = _ROOT / "data" / "mlcw" / "group_byLayer_orig" / "TUKU_orig_grouped.csv"
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

# Level-1 success thresholds
THIN_LAYERS = {"F1", "T1", "T2", "F4"}   # MAE<5 mm, RMSE<10 mm
THICK_LAYERS = {"F2", "F3"}              # MAE<10 mm, RMSE<20 mm
MAE_THRESH = {"F1": 5, "T1": 5, "T2": 5, "F4": 5, "F2": 10, "F3": 10}
RMSE_THRESH = {"F1": 10, "T1": 10, "T2": 10, "F4": 10, "F2": 20, "F3": 20}

OUT_RESULTS = _TAU_DEMO / "results" / "seq"
OUT_PLOTS   = _TAU_DEMO / "plots" / "seq"


# ── Load frozen calibration ────────────────────────────────────────────────────
def load_frozen_models() -> dict[str, FrozenLayerModel]:
    """Load the frozen 2010-2018 models from JSON."""
    with open(FROZEN_JSON) as f:
        calib = json.load(f)
    models = {}
    for L in LAYERS:
        d = calib["layers"][L]
        m = FrozenLayerModel(
            layer=L,
            a=d["a"],
            c=d["c"],
            S_ke=d["S_ke"],
            S_kv=d["S_kv"],
            tau=d["tau"],
            use_u=d["use_u"],
            use_V=d["use_V"],
            beta=0.0,
            h_c=d["h_c"],
        )
        models[L] = m
    return models


# ── Build full driver frames (once, reused across all schedules) ───────────────
def build_all_drivers() -> dict[str, pd.DataFrame]:
    """Call build_layer_drivers for each layer; returns full-timeline frames."""
    frames: dict[str, pd.DataFrame] = {}
    for L in LAYERS:
        gwl_fname, wellcode = WELL_CONFIG[L]
        with open(FROZEN_JSON) as f:
            calib = json.load(f)
        tau = calib["layers"][L]["tau"]
        df = build_layer_drivers(
            layer=L,
            tau=tau,
            gwl_feather=GWL_ROOT / gwl_fname,
            wellcode=wellcode,
            gps_csv=GPS_CSV,
            mlcw_inc_feather=MLCW_INC,
            ref_date=REF_DATE,
        )
        df["date"] = pd.to_datetime(df["date"])
        frames[L] = df
    return frames


# ── Genuine truth loader ───────────────────────────────────────────────────────
def load_genuine_truth() -> pd.DataFrame:
    """Load TUKU_orig_grouped.csv. Returns df indexed by datetime with layer columns."""
    df = pd.read_csv(ORIG_CSV)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime").reset_index(drop=True)
    return df   # columns: datetime, F1, T1, F2, T2, F3, T3, F4


def align_genuine_to_epoch(
    truth_df: pd.DataFrame,
    model_dates: pd.Series,
    tolerance_days: int = 3,
) -> pd.DataFrame:
    """Merge genuine visits to the nearest 5-day model epoch (tolerance <= 3 days).

    Returns a DataFrame with 'model_date' and per-layer columns.
    """
    tol = pd.Timedelta(days=tolerance_days)
    # Normalize to ns to avoid dtype mismatch between CSV-parsed us and feather-sourced ns
    model_dt = pd.DataFrame({"model_date": pd.to_datetime(model_dates).astype("datetime64[ns]")})
    model_dt = model_dt.sort_values("model_date").reset_index(drop=True)

    truth_sorted = truth_df.copy()
    truth_sorted["datetime"] = pd.to_datetime(truth_sorted["datetime"]).astype("datetime64[ns]")
    truth_sorted = truth_sorted.sort_values("datetime").reset_index(drop=True)

    merged = pd.merge_asof(
        truth_sorted.rename(columns={"datetime": "model_date"}),
        model_dt.assign(model_date_epoch=model_dt["model_date"]),
        on="model_date",
        direction="nearest",
        tolerance=tol,
    )
    # Keep rows where we found a matching epoch
    merged = merged.dropna(subset=["model_date_epoch"])
    # Replace model_date with the exact epoch date
    merged["model_date"] = merged["model_date_epoch"]
    merged = merged.drop(columns=["model_date_epoch"])
    return merged.reset_index(drop=True)


# ── GPS carrier noise estimate ─────────────────────────────────────────────────
def estimate_carrier_noise(gps_csv: Path, start: pd.Timestamp, end: pd.Timestamp) -> float:
    """Std of 5-day GPS increments in the dense era — used for step-flag threshold."""
    gps = pd.read_csv(gps_csv)
    gps["datetime"] = pd.to_datetime(gps["date"])
    gps = gps.sort_values("datetime").reset_index(drop=True)
    mask = (gps["datetime"] >= start) & (gps["datetime"] <= end)
    d = gps.loc[mask, "modeled"].values.astype(float)
    if len(d) < 5:
        return float("nan")
    increments = np.diff(d)
    return float(np.nanstd(increments))


# ── Schedule builder ──────────────────────────────────────────────────────────
def build_schedules(
    blind_genuine_dates: pd.DatetimeIndex,
) -> dict[str, list[pd.Timestamp]]:
    """Build the 7 visit schedules from genuine blind-era dates.

    Each schedule subsamples the genuine dates to a target spacing.
    'actual' uses all genuine dates as-is.
    'none' uses no dates.
    'blackout' uses no visits before 2021-01-01, then annual thereafter.
    """
    dates_sorted = sorted(blind_genuine_dates.dropna().unique())

    def nearest_genuine(target: pd.Timestamp) -> Optional[pd.Timestamp]:
        """Return the genuine date closest to target (within 45 days), or None."""
        min_gap = pd.Timedelta(days=999)
        best = None
        for d in dates_sorted:
            gap = abs(d - target)
            if gap < min_gap:
                min_gap = gap
                best = d
        if min_gap > pd.Timedelta(days=45):
            return None
        return best

    def subsample(spacing_days: int) -> list[pd.Timestamp]:
        """Pick genuine visits nearest to each target interval."""
        result = []
        anchor = pd.Timestamp("2019-01-01")
        used = set()
        t = anchor
        while t <= BLIND_END + pd.Timedelta(days=spacing_days):
            nd = nearest_genuine(t)
            if nd is not None and nd not in used:
                used.add(nd)
                result.append(nd)
            t += pd.Timedelta(days=spacing_days)
        return sorted(result)

    monthly    = subsample(30)
    quarterly  = subsample(90)
    semiannual = subsample(180)
    annual     = subsample(365)
    actual     = sorted(dates_sorted)
    none_sched: list[pd.Timestamp] = []

    # blackout: no visits before 2021-01-01, then annual
    blackout_annual = [d for d in annual if d >= pd.Timestamp("2021-01-01")]

    return {
        "monthly":    monthly,
        "quarterly":  quarterly,
        "semiannual": semiannual,
        "annual":     annual,
        "none":       none_sched,
        "blackout":   blackout_annual,
        "actual":     actual,
    }


# ── Conformal bank seeding (2015-2018 out-of-window rehearsal) ─────────────────
def seed_conformal_bank(
    seed_schedule_dates: list[pd.Timestamp],
    frames: dict[str, pd.DataFrame],
    truth_aligned: pd.DataFrame,  # aligned to model epochs
    carrier_noise: float,
) -> ConformalBank:
    """Pre-fill the conformal bank by rehearsing the same schedule over 2015-2018.

    Models are RE-FIT on 2010-2014 only (keeping frozen tau, use_u, use_V, h_c from JSON).
    The seed walk 2015→2018 generates out-of-window forward errors.
    """
    print("  Seeding conformal bank (2015-2018 rehearsal, fit on 2010-2014)...")
    bank = ConformalBank(alpha=0.10)

    with open(FROZEN_JSON) as f:
        calib = json.load(f)

    # Re-fit models on 2010-2014 only
    seed_models: dict[str, FrozenLayerModel] = {}
    for L in LAYERS:
        d = calib["layers"][L]
        m = FrozenLayerModel(
            layer=L,
            a=d["a"], c=d["c"],
            S_ke=d["S_ke"], S_kv=d["S_kv"],
            tau=d["tau"],
            use_u=d["use_u"], use_V=d["use_V"],
            beta=0.0, h_c=d["h_c"],
        )
        df = frames[L]
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
                print(f"    {L}: re-fit on 2010-2014 ({n_fit} rows) → "
                      f"a={m.a:.4f} c={m.c:.3f} S_ke={m.S_ke:.4f} S_kv={m.S_kv:.4f}")
            except ValueError as e:
                print(f"    {L}: re-fit FAILED ({e}) — using frozen params")
        else:
            print(f"    {L}: only {n_fit} rows in 2010-2014 — using frozen params")
        seed_models[L] = m

    # Seed walk: 2015-2018
    seed_epochs = sorted(
        frames[LAYERS[0]].loc[
            (frames[LAYERS[0]]["date"] >= SEED_START) &
            (frames[LAYERS[0]]["date"] <= SEED_END),
            "date",
        ].tolist()
    )
    if not seed_epochs:
        print("  WARNING: no seed epochs found in 2015-2018; conformal bank unseeded.")
        return bank

    # Build truth lookup for seed era (genuine visits only)
    truth_seed = truth_aligned[
        (truth_aligned["model_date"] >= SEED_START) &
        (truth_aligned["model_date"] <= SEED_END)
    ].copy()

    # Track per-layer last-visit epoch in seed era
    last_visit_seed: dict[str, pd.Timestamp] = {L: SEED_START for L in LAYERS}
    # Seed schedule: use the same target spacing as the actual blind schedule
    # (use the seed_schedule_dates passed in, filtered to seed era)
    seed_visit_set = set(seed_schedule_dates)

    leakage_fired = False
    seed_oracle = TimeOracle(SEED_START - pd.Timedelta(days=1))

    for epoch_date in seed_epochs:
        try:
            seed_oracle.advance(epoch_date)
        except LeakageError as e:
            print(f"  SEED LeakageError (should not happen): {e}")
            leakage_fired = True
            continue

        for L, m in seed_models.items():
            df = frames[L]
            row_mask = df["date"] == epoch_date
            if not row_mask.any():
                continue
            row = df[row_mask].iloc[0]
            d_val   = float(row["d_gps"])
            u_lag   = float(row["u_lag"])
            V_lag   = float(row["V_lag"])
            if not (np.isfinite(d_val) and np.isfinite(u_lag) and np.isfinite(V_lag)):
                continue
            pred = m.predict(d_val, u_lag, V_lag)

            # Visit in seed era?
            if epoch_date in seed_visit_set:
                # Find genuine truth for this epoch and layer
                truth_row = truth_seed[truth_seed["model_date"] == epoch_date]
                if len(truth_row) > 0:
                    obs_val = float(truth_row.iloc[0].get(L, float("nan")))
                    if np.isfinite(obs_val):
                        horizon = _epochs_between(last_visit_seed[L], epoch_date, seed_epochs)
                        abs_err = abs(obs_val - pred)
                        bank.add(L, horizon, abs_err)
                        innovation = obs_val - pred
                        m.assimilate(innovation)
                        last_visit_seed[L] = epoch_date

    print(f"  Bank census after seeding: {bank.census()}")
    return bank


def _epochs_between(
    last_visit: pd.Timestamp,
    current: pd.Timestamp,
    epoch_list: list[pd.Timestamp],
) -> int:
    """Count 5-day epochs between last_visit and current (exclusive of last_visit)."""
    idx_last = None
    idx_curr = None
    for i, e in enumerate(epoch_list):
        if e == last_visit:
            idx_last = i
        if e == current:
            idx_curr = i
    if idx_last is None or idx_curr is None:
        # Fall back to approximate calculation
        return max(1, int((current - last_visit).days // 5))
    return max(1, idx_curr - idx_last)


# ── Core walk-forward loop ─────────────────────────────────────────────────────
def run_schedule(
    schedule_name: str,
    visit_dates: list[pd.Timestamp],
    frames: dict[str, pd.DataFrame],
    frozen_models: dict[str, FrozenLayerModel],
    bank_seed: ConformalBank,
    truth_aligned: pd.DataFrame,
    truth_df: pd.DataFrame,
    carrier_noise: float,
    reconst_df: pd.DataFrame,
    all_genuine_dates: Optional[set] = None,
) -> dict:
    """Run the blind walk-forward for one schedule.  Returns results dict.

    Parameters
    ----------
    all_genuine_dates : set of Timestamps
        Full set of genuine blind-era dates.  ALL schedules are scored on this
        fixed set so that RMSE values are comparable across cadences.
        At each genuine date the model prediction is recorded BEFORE any
        assimilation at that date (prequential scoring).  Assimilation only
        happens at dates that are also in visit_dates.
    """
    print(f"\n  Schedule '{schedule_name}': {len(visit_dates)} visits")

    # Deep-copy models so each schedule starts fresh from frozen state
    models: dict[str, FrozenLayerModel] = {L: copy.deepcopy(frozen_models[L]) for L in LAYERS}
    # Deep-copy bank so each schedule starts from the same seeded state
    bank = copy.deepcopy(bank_seed)

    # Blind epoch list (from F1 frame as reference grid)
    blind_df = frames[LAYERS[0]]
    blind_epochs = sorted(
        blind_df.loc[
            (blind_df["date"] >= BLIND_START) & (blind_df["date"] <= BLIND_END),
            "date",
        ].tolist()
    )
    if not blind_epochs:
        raise RuntimeError("No blind-era epochs found in driver frame.")

    # Step-flag threshold: |Δd| > 5 * carrier_noise
    step_threshold = 5.0 * carrier_noise if np.isfinite(carrier_noise) else float("inf")

    visit_set = set(visit_dates)
    # FIX (M8.3): score EVERY schedule on the SAME full genuine-visit set.
    # score_set: where we record prequential error (ALL genuine blind-era dates).
    # assimilate_set: where we actually update the model bias (visit dates only).
    # For 'none', assimilate_set is empty — model never updates.
    score_set = all_genuine_dates if all_genuine_dates else visit_set
    assimilate_set = visit_set   # always empty for 'none'

    # Tracking per layer
    last_visit: dict[str, pd.Timestamp] = {L: DENSE_END for L in LAYERS}
    last_pred:  dict[str, float]        = {L: float("nan") for L in LAYERS}
    prev_d_gps: dict[str, float]        = {L: float("nan") for L in LAYERS}

    # Per-layer timeseries rows: list of dicts
    ts_rows: dict[str, list[dict]] = {L: [] for L in LAYERS}
    # Per-layer prequential (graded-before-reveal) innovations at genuine visits
    preq_rows: dict[str, list[dict]] = {L: [] for L in LAYERS}

    oracle = TimeOracle(DENSE_END)
    leakage_fired = False

    for epoch_date in blind_epochs:
        try:
            oracle.advance(epoch_date)
        except LeakageError as e:
            print(f"  LEAKAGE ERROR (must not happen): {e}")
            leakage_fired = True
            break

        for L, m in models.items():
            df = frames[L]
            row_mask = df["date"] == epoch_date
            if not row_mask.any():
                continue
            row = df[row_mask].iloc[0]
            d_val   = float(row["d_gps"])
            u_lag   = float(row["u_lag"])
            V_lag   = float(row["V_lag"])

            # Step flag: |Δd| > 5 * carrier_noise
            step_flag = False
            if np.isfinite(d_val) and np.isfinite(prev_d_gps[L]):
                delta_d = abs(d_val - prev_d_gps[L])
                step_flag = bool(delta_d > step_threshold)
            if np.isfinite(d_val):
                prev_d_gps[L] = d_val

            # Predict (skip if any required driver is NaN)
            pred = float("nan")
            if np.isfinite(d_val) and np.isfinite(u_lag) and np.isfinite(V_lag):
                pred = float(m.predict(d_val, u_lag, V_lag))
                last_pred[L] = pred

            horizon = _epochs_between(last_visit[L], epoch_date, blind_epochs)
            hw = bank.half_width(L, horizon)

            ts_rows[L].append({
                "date": epoch_date.isoformat(),
                "pred_mm": round(pred, 4) if np.isfinite(pred) else None,
                "half_width_mm": round(hw, 4) if np.isfinite(hw) else None,
                "horizon_epochs": horizon,
                "step_flag": step_flag,
            })

            # Score prequential: at every date in score_set (visits + genuine for 'none')
            is_score_date = (epoch_date in score_set)
            is_assimilate = (epoch_date in assimilate_set)

            if is_score_date:
                # Find nearest genuine truth for this epoch
                truth_row = truth_aligned[truth_aligned["model_date"] == epoch_date]
                obs_val = float("nan")
                if len(truth_row) > 0:
                    obs_val = float(truth_row.iloc[0].get(L, float("nan")))

                in_band = False
                if np.isfinite(obs_val) and np.isfinite(pred) and np.isfinite(hw):
                    in_band = bool(abs(obs_val - pred) <= hw)

                if np.isfinite(obs_val) and np.isfinite(pred):
                    innovation = obs_val - pred
                    # Record prequential innovation (before assimilation)
                    preq_rows[L].append({
                        "date": epoch_date.isoformat(),
                        "obs_mm": round(obs_val, 4),
                        "pred_mm": round(pred, 4),
                        "innovation_mm": round(innovation, 4),
                        "in_band": in_band,
                        "horizon_epochs": horizon,
                    })
                    # Feed error into bank AFTER scoring (only at assimilate dates)
                    if is_assimilate:
                        bank.add(L, horizon, abs(innovation))
                        # Hard-reset bias (A6)
                        m.assimilate(innovation)
                        last_visit[L] = epoch_date

    # ── Compute metrics per layer ─────────────────────────────────────────────
    # n_scoring_points is the same for every schedule (full genuine-visit set).
    n_scoring_points = len(score_set) if score_set else 0
    metrics: dict = {
        "schedule": schedule_name,
        "n_visits_used": len(visit_dates),
        "n_scoring_points": n_scoring_points,
        "scoring_note": (
            "All schedules graded on the SAME full genuine-visit scoring set "
            "(all ~60 blind-era genuine dates, merge_asof ≤3 days to 5-day grid). "
            "Prediction recorded BEFORE assimilation at each scoring date. "
            "Assimilation (hard level reset) only at reveal dates for this schedule."
        ),
        "visit_dates": [d.isoformat() for d in visit_dates],
        "leakage_fired": leakage_fired,
        "layers": {},
    }

    # For the 'none' baseline (carrier-only, beta frozen at 0):
    # we just need to score the same genuine visits without any assimilation.
    # Compute baseline separately below.

    for L in LAYERS:
        preq = preq_rows[L]
        n_preq = len(preq)
        mae_mm = float("nan")
        rmse_mm = float("nan")

        if n_preq > 0:
            errs = [abs(r["innovation_mm"]) for r in preq]
            mae_mm = float(np.mean(errs))
            rmse_mm = float(np.sqrt(np.mean([e**2 for e in errs])))

        # Band coverage: fraction of prequential points where |inn| <= hw (hw defined)
        band_pts = [r for r in preq if np.isfinite(r["in_band"])]
        cov_pts = [r for r in band_pts]   # all have hw defined implicitly
        # Actually in_band is only True when hw is finite (set to False otherwise)
        # Re-check: in_band is False when hw=nan; need to filter to points WITH hw
        hw_defined_pts = [r for r in preq
                          if np.isfinite(float(next(
                              (row["half_width_mm"] for row in ts_rows[L]
                               if row["date"] == r["date"]),
                              float("nan")
                          ) or float("nan")))]
        n_hw = len(hw_defined_pts)
        n_in_band = sum(1 for r in hw_defined_pts if r["in_band"])
        coverage = (n_in_band / n_hw) if n_hw > 0 else float("nan")

        # Mean half-width over all blind epochs where hw is defined
        hw_vals = [row["half_width_mm"] for row in ts_rows[L]
                   if row["half_width_mm"] is not None]
        mean_hw = float(np.mean(hw_vals)) if hw_vals else float("nan")

        # Converged: 3 consecutive prequential innovations in-band
        converged = False
        if len(preq) >= 3:
            for i in range(len(preq) - 2):
                if preq[i]["in_band"] and preq[i+1]["in_band"] and preq[i+2]["in_band"]:
                    converged = True
                    break

        # V2 dynamics fidelity (vs dense fill)
        reconst_L = reconst_df[["datetime", L]].dropna(subset=[L]).copy()
        reconst_L["datetime"] = pd.to_datetime(reconst_L["datetime"])
        reconst_blind = reconst_L[
            (reconst_L["datetime"] >= BLIND_START) & (reconst_L["datetime"] <= BLIND_END)
        ]
        amp_ratio = float("nan")
        detrended_corr = float("nan")
        detrended_std_obs = float("nan")
        detrended_std_pred = float("nan")

        pred_series = pd.Series(
            {pd.Timestamp(r["date"]): r["pred_mm"] for r in ts_rows[L]
             if r["pred_mm"] is not None}
        )
        obs_series = pd.Series(
            {pd.Timestamp(r["datetime"]): float(r[L]) for _, r in reconst_blind.iterrows()
             if np.isfinite(float(r[L]))}
        )

        if len(pred_series) > 20 and len(obs_series) > 20:
            # Detrend both
            pred_arr = pred_series.values.astype(float)
            obs_arr = obs_series.values.astype(float)
            t_pred = np.arange(len(pred_arr), dtype=float)
            t_obs  = np.arange(len(obs_arr), dtype=float)
            p_pred = np.polyfit(t_pred, pred_arr, 1)
            p_obs  = np.polyfit(t_obs, obs_arr, 1)
            pred_detr = pred_arr - np.polyval(p_pred, t_pred)
            obs_detr  = obs_arr  - np.polyval(p_obs, t_obs)

            # Increments for amplitude ratio
            d_pred = np.diff(pred_arr)
            d_obs  = np.diff(obs_arr)
            std_d_pred = np.std(d_pred) if len(d_pred) > 2 else float("nan")
            std_d_obs  = np.std(d_obs)  if len(d_obs)  > 2 else float("nan")
            amp_ratio = float(std_d_pred / std_d_obs) if std_d_obs > 1e-9 else float("nan")
            detrended_std_pred = float(np.std(pred_detr))
            detrended_std_obs  = float(np.std(obs_detr))

            # Align by nearest-date for correlation
            pred_indexed = pred_series.sort_index()
            obs_indexed  = obs_series.sort_index()
            combined = pd.merge_asof(
                obs_indexed.reset_index().rename(columns={"index": "date", 0: "obs"}),
                pred_indexed.reset_index().rename(columns={"index": "date", 0: "pred"}),
                on="date",
                direction="nearest",
                tolerance=pd.Timedelta("5D"),
            ).dropna()
            if len(combined) > 10:
                t_com = np.arange(len(combined), dtype=float)
                p_o = np.polyfit(t_com, combined["obs"].values, 1)
                p_p = np.polyfit(t_com, combined["pred"].values, 1)
                o_dt = combined["obs"].values  - np.polyval(p_o, t_com)
                p_dt = combined["pred"].values - np.polyval(p_p, t_com)
                if np.std(o_dt) > 1e-9 and np.std(p_dt) > 1e-9:
                    detrended_corr = float(np.corrcoef(o_dt, p_dt)[0, 1])

        # F3 drought-2021 detection
        drought_detection = None
        if L == "F3":
            for r in preq:
                if pd.Timestamp(r["date"]).year >= 2021:
                    row_hw = next(
                        (row["half_width_mm"] for row in ts_rows[L]
                         if row["date"] == r["date"]), None
                    )
                    if row_hw is not None and np.isfinite(row_hw):
                        if abs(r["innovation_mm"]) > row_hw:
                            drought_detection = r["date"]
                            break

        # Meets Level-1 threshold?
        meets_L1 = (
            np.isfinite(mae_mm) and np.isfinite(rmse_mm) and
            mae_mm <= MAE_THRESH[L] and rmse_mm <= RMSE_THRESH[L]
        )

        metrics["layers"][L] = {
            "n_prequential_visits": n_preq,   # actual finite-obs count (may be < n_scoring_points if NaN obs)
            "n_scoring_points": n_scoring_points,  # identical across all schedules
            "MAE_mm": round(mae_mm, 3) if np.isfinite(mae_mm) else None,
            "RMSE_mm": round(rmse_mm, 3) if np.isfinite(rmse_mm) else None,
            "skill_vs_baseline": None,   # filled in after baseline run
            "band_coverage_fraction": round(coverage, 3) if np.isfinite(coverage) else None,
            "n_hw_defined_visits": n_hw,
            "mean_half_width_mm": round(mean_hw, 2) if np.isfinite(mean_hw) else None,
            "converged": converged,
            "innovations": [
                {
                    "date": r["date"],
                    "value": r["innovation_mm"],
                    "in_band": r["in_band"],
                }
                for r in preq
            ],
            "drought_2021_detection_date": drought_detection,
            "dynamics_vs_densefill_diagnostic": {
                "amplitude_ratio_increments": round(amp_ratio, 4) if np.isfinite(amp_ratio) else None,
                "detrended_corr": round(detrended_corr, 4) if np.isfinite(detrended_corr) else None,
                "detrended_std_obs_mm": round(detrended_std_obs, 3) if np.isfinite(detrended_std_obs) else None,
                "detrended_std_pred_mm": round(detrended_std_pred, 3) if np.isfinite(detrended_std_pred) else None,
            },
            "meets_L1_threshold": meets_L1,
            "L1_thresholds": {"MAE_mm": MAE_THRESH[L], "RMSE_mm": RMSE_THRESH[L]},
        }

    return {
        "schedule_name": schedule_name,
        "ts_rows": ts_rows,
        "preq_rows": preq_rows,
        "metrics": metrics,
    }


# ── Baseline: no-visit carrier-only run ──────────────────────────────────────
def run_baseline(
    frames: dict[str, pd.DataFrame],
    frozen_models: dict[str, FrozenLayerModel],
    truth_aligned: pd.DataFrame,
) -> dict[str, float]:
    """Run with no visits; return {layer: RMSE_mm} scored on genuine blind visits."""
    blind_genuine = truth_aligned[
        (truth_aligned["model_date"] >= BLIND_START) &
        (truth_aligned["model_date"] <= BLIND_END)
    ]
    rmse_baseline: dict[str, float] = {}

    for L in LAYERS:
        m = copy.deepcopy(frozen_models[L])
        # beta stays 0; no assimilation
        df = frames[L]
        errors = []
        for _, tr in blind_genuine.iterrows():
            epoch_date = tr["model_date"]
            obs_val = float(tr.get(L, float("nan")))
            if not np.isfinite(obs_val):
                continue
            row_mask = df["date"] == epoch_date
            if not row_mask.any():
                continue
            row = df[row_mask].iloc[0]
            d_val  = float(row["d_gps"])
            u_lag  = float(row["u_lag"])
            V_lag  = float(row["V_lag"])
            if not (np.isfinite(d_val) and np.isfinite(u_lag) and np.isfinite(V_lag)):
                continue
            pred = float(m.predict(d_val, u_lag, V_lag))
            errors.append(obs_val - pred)

        rmse_baseline[L] = float(np.sqrt(np.mean([e**2 for e in errors]))) if errors else float("nan")

    return rmse_baseline


# ── Output writers ─────────────────────────────────────────────────────────────
def write_timeseries_csv(
    schedule_name: str,
    layer: str,
    ts_rows: list[dict],
    out_dir: Path,
) -> Path:
    df = pd.DataFrame(ts_rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"TUKU_{layer}_seq_timeseries.csv"
    df.to_csv(path, index=False)
    return path


class _NumpyEncoder(json.JSONEncoder):
    """Convert numpy scalars to native Python types for JSON serialization."""
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def write_metrics_json(
    schedule_name: str,
    metrics: dict,
    out_dir: Path,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "metrics.json"
    with open(path, "w") as f:
        json.dump(metrics, f, indent=2, cls=_NumpyEncoder)
    return path


def plot_schedule(
    schedule_name: str,
    ts_rows: dict[str, list[dict]],
    visit_dates: list[pd.Timestamp],
    truth_aligned: pd.DataFrame,
    reconst_df: pd.DataFrame,
    out_path: Path,
) -> None:
    """6-panel plot: genuine observations (markers), model prediction (line),
    90% band (shaded), visit dates (vertical ticks), dense fill (faint line).
    """
    fig, axes = plt.subplots(3, 2, figsize=(18, 16), sharex=False)
    axes = axes.flatten()
    visit_set = set(visit_dates)

    # Dense reconstruction: reindex to the same datetime
    reconst_copy = reconst_df.copy()
    reconst_copy["datetime"] = pd.to_datetime(reconst_copy["datetime"])

    for i, L in enumerate(LAYERS):
        ax = axes[i]
        rows = ts_rows[L]
        if not rows:
            ax.set_title(f"{L} — no data", fontsize=14)
            continue

        dates_pred = [pd.Timestamp(r["date"]) for r in rows]
        pred_vals  = [r["pred_mm"] if r["pred_mm"] is not None else float("nan") for r in rows]
        hw_vals    = [r["half_width_mm"] if r["half_width_mm"] is not None else float("nan") for r in rows]
        pred_arr   = np.array(pred_vals, dtype=float)
        hw_arr     = np.array(hw_vals, dtype=float)

        # Dense fill (faint background line)
        rc = reconst_copy[["datetime", L]].dropna(subset=[L])
        rc_blind = rc[(rc["datetime"] >= BLIND_START) & (rc["datetime"] <= BLIND_END)]
        ax.plot(rc_blind["datetime"], rc_blind[L].values,
                color="gray", lw=0.8, alpha=0.4, label="Dense fill (reconstruction)", zorder=1)

        # Prediction line
        ax.plot(dates_pred, pred_arr, color="tab:blue", lw=1.8, label="Model prediction", zorder=3)

        # 90% conformal band (only where hw is defined)
        hw_finite = np.isfinite(hw_arr)
        if hw_finite.any():
            dates_hw = np.array(dates_pred)[hw_finite]
            p_hw = pred_arr[hw_finite]
            h_hw = hw_arr[hw_finite]
            ax.fill_between(dates_hw, p_hw - h_hw, p_hw + h_hw,
                            color="tab:blue", alpha=0.15, label="90% conformal band", zorder=2)

        # Genuine observations at visit dates (markers)
        visit_truth = truth_aligned[
            (truth_aligned["model_date"] >= BLIND_START) &
            (truth_aligned["model_date"] <= BLIND_END) &
            (truth_aligned["model_date"].isin(visit_set))
        ]
        obs_dates = [pd.Timestamp(d) for d in visit_truth["model_date"].tolist()]
        obs_vals = [float(visit_truth.loc[visit_truth["model_date"] == d, L].values[0])
                    if L in visit_truth.columns and
                       not pd.isna(float(visit_truth.loc[visit_truth["model_date"] == d, L].values[0]))
                    else float("nan")
                    for d in obs_dates]
        valid_obs = [(d, v) for d, v in zip(obs_dates, obs_vals) if np.isfinite(v)]
        if valid_obs:
            od, ov = zip(*valid_obs)
            ax.scatter(od, ov, color="tab:red", s=50, zorder=5, label="Field visit (genuine)", marker="o")

        # All genuine blind-era observations (smaller gray markers)
        all_truth = truth_aligned[
            (truth_aligned["model_date"] >= BLIND_START) &
            (truth_aligned["model_date"] <= BLIND_END)
        ]
        all_obs_dates = [pd.Timestamp(d) for d in all_truth["model_date"].tolist()]
        all_obs_vals = [float(all_truth.loc[all_truth["model_date"] == d, L].values[0])
                        if L in all_truth.columns and
                           not pd.isna(float(all_truth.loc[all_truth["model_date"] == d, L].values[0]))
                        else float("nan")
                        for d in all_obs_dates]
        valid_all = [(d, v) for d, v in zip(all_obs_dates, all_obs_vals) if np.isfinite(v)]
        if valid_all:
            od2, ov2 = zip(*valid_all)
            ax.scatter(od2, ov2, color="darkgray", s=20, zorder=4,
                       label="Genuine obs (not visited)", marker="x", alpha=0.6)

        # Visit date vertical ticks
        for vd in visit_dates:
            if BLIND_START <= vd <= BLIND_END:
                ax.axvline(x=vd, color="tab:green", lw=0.6, alpha=0.5, ls="--", zorder=1)

        ax.set_xlabel("Date", fontsize=13)
        ax.set_ylabel("Cumulative compaction (mm)", fontsize=13)
        ax.set_title(f"{L} — {schedule_name}", fontsize=14, fontweight="bold")
        ax.tick_params(labelsize=12)
        ax.grid(True, alpha=0.35)
        ax.legend(fontsize=11, loc="lower left")

    fig.suptitle(f"TUKU — Sequential walk-forward ({schedule_name}), blind era 2019–2023",
                 fontsize=16, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"    PNG: {out_path}")


def plot_cadence_curve(
    rmse_table: dict[str, dict[str, float]],
    mae_table: dict[str, dict[str, float]],
    schedule_order: list[str],
    out_path: Path,
) -> None:
    """x=cadence (ordered monthly→…→none), y=RMSE, one line per layer, threshold lines."""
    x_labels = [s for s in schedule_order if s in list(rmse_table.values())[0]]
    # For the x-axis, use the schedule_order but only schedules with data
    x_pos = list(range(len(x_labels)))

    fig, ax = plt.subplots(figsize=(14, 8))

    colors = plt.cm.tab10.colors
    for i, L in enumerate(LAYERS):
        y_vals = [rmse_table[L].get(s, float("nan")) for s in x_labels]
        ax.plot(x_pos, y_vals, marker="o", lw=2, color=colors[i], label=L, markersize=7)

    # Threshold lines
    ax.axhline(y=10, color="tab:red", ls="--", lw=1.2, alpha=0.6,
               label="RMSE thresh (thin: 10 mm)")
    ax.axhline(y=20, color="tab:orange", ls="--", lw=1.2, alpha=0.6,
               label="RMSE thresh (thick: 20 mm)")

    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_labels, fontsize=13, rotation=15)
    ax.set_ylabel("Blind prequential RMSE (mm)", fontsize=14)
    ax.set_xlabel("Visiting cadence", fontsize=14)
    ax.set_title("TUKU — Cadence-degradation curve (blind era 2019–2023)", fontsize=15, fontweight="bold")
    ax.tick_params(labelsize=12)
    ax.grid(True, alpha=0.35)
    ax.legend(fontsize=12, loc="upper left")
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Cadence curve PNG: {out_path}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 75)
    print("Task M8.3 — Walk-forward rehearsal, 7 cadences, TUKU 2019–2023")
    print("=" * 75)

    # ── 1. Load data ─────────────────────────────────────────────────────────
    print("\nLoading data...")
    frozen_models = load_frozen_models()
    print(f"  Loaded {len(frozen_models)} frozen models.")

    frames = build_all_drivers()
    print(f"  Built driver frames for {len(frames)} layers.")

    truth_df = load_genuine_truth()
    print(f"  Genuine truth: {len(truth_df)} rows, "
          f"{truth_df['datetime'].min().date()} — {truth_df['datetime'].max().date()}")

    reconst_df = pd.read_csv(RECONST_CSV)
    reconst_df["datetime"] = pd.to_datetime(reconst_df["datetime"])
    print(f"  Dense reconstruction: {len(reconst_df)} rows.")

    # ── 2. Align genuine truth to 5-day epochs ──────────────────────────────
    ref_dates = frames[LAYERS[0]]["date"]
    truth_aligned = align_genuine_to_epoch(truth_df, ref_dates, tolerance_days=3)
    # Filter to blind era for visit counting
    truth_blind = truth_aligned[
        (truth_aligned["model_date"] >= BLIND_START) &
        (truth_aligned["model_date"] <= BLIND_END)
    ].copy()
    blind_genuine_dates = pd.DatetimeIndex(truth_blind["model_date"].unique())
    print(f"  Genuine blind-era visits aligned: {len(blind_genuine_dates)}")

    # ── 3. Carrier noise ────────────────────────────────────────────────────
    carrier_noise = estimate_carrier_noise(GPS_CSV, BLIND_START, BLIND_END)
    print(f"  Carrier noise (std of 5-day GPS increments, blind era): {carrier_noise:.4f} mm")
    step_threshold = 5.0 * carrier_noise
    print(f"  Step-flag threshold (5×noise): {step_threshold:.4f} mm")

    # ── 4. Build schedules ───────────────────────────────────────────────────
    schedules = build_schedules(blind_genuine_dates)
    print("\nSchedule summary:")
    for s_name, s_dates in schedules.items():
        print(f"  {s_name:<12} : {len(s_dates):3d} visits")

    # ── 5. Seed conformal bank ───────────────────────────────────────────────
    # Use the monthly seed schedule (densest) for seeding
    seed_genuine = truth_aligned[
        (truth_aligned["model_date"] >= SEED_START) &
        (truth_aligned["model_date"] <= SEED_END)
    ]
    seed_genuine_dates = sorted(seed_genuine["model_date"].unique().tolist())
    print(f"\nSeeding conformal bank with {len(seed_genuine_dates)} genuine visits in 2015-2018...")

    bank_seeded = seed_conformal_bank(
        seed_schedule_dates=seed_genuine_dates,
        frames=frames,
        truth_aligned=truth_aligned,
        carrier_noise=carrier_noise,
    )

    # ── 6. Run baseline (no-visit) ───────────────────────────────────────────
    print("\nRunning baseline (no-visit, carrier-only, beta=0)...")
    rmse_baseline = run_baseline(frames, frozen_models, truth_aligned)
    print("  Baseline RMSE per layer:", {L: f"{v:.2f}" for L, v in rmse_baseline.items()})

    # ── 7. Run all 7 schedules ───────────────────────────────────────────────
    schedule_order = ["monthly", "quarterly", "semiannual", "annual", "blackout", "none", "actual"]
    all_results: dict[str, dict] = {}

    # Genuine blind-era dates as a set (for 'none' schedule scoring)
    all_blind_genuine_set: set = set(blind_genuine_dates.tolist())

    for s_name in schedule_order:
        s_dates = schedules[s_name]
        print(f"\n{'─'*60}")
        result = run_schedule(
            schedule_name=s_name,
            visit_dates=s_dates,
            frames=frames,
            frozen_models=frozen_models,
            bank_seed=bank_seeded,
            truth_aligned=truth_aligned,
            truth_df=truth_df,
            carrier_noise=carrier_noise,
            reconst_df=reconst_df,
            all_genuine_dates=all_blind_genuine_set,
        )
        # Fill in skill_vs_baseline
        for L in LAYERS:
            rmse_sched = result["metrics"]["layers"][L]["RMSE_mm"]
            rmse_base  = rmse_baseline.get(L, float("nan"))
            if rmse_sched is not None and np.isfinite(rmse_base) and rmse_base > 1e-9:
                skill = 1.0 - rmse_sched / rmse_base
                result["metrics"]["layers"][L]["skill_vs_baseline"] = round(float(skill), 4)
        all_results[s_name] = result

    # ── 8. Write per-schedule outputs ────────────────────────────────────────
    print(f"\n{'='*60}")
    print("Writing per-schedule outputs...")

    for s_name, result in all_results.items():
        s_dir = OUT_RESULTS / s_name
        p_dir = OUT_PLOTS / s_name
        s_dir.mkdir(parents=True, exist_ok=True)
        p_dir.mkdir(parents=True, exist_ok=True)

        for L in LAYERS:
            csv_path = write_timeseries_csv(s_name, L, result["ts_rows"][L], s_dir)
            print(f"  Written: {csv_path}")

        metrics_path = write_metrics_json(s_name, result["metrics"], s_dir)
        print(f"  Written: {metrics_path}")

        png_path = p_dir / "TUKU_seq_6layer.png"
        plot_schedule(
            schedule_name=s_name,
            ts_rows=result["ts_rows"],
            visit_dates=schedules[s_name],
            truth_aligned=truth_aligned,
            reconst_df=reconst_df,
            out_path=png_path,
        )

    # ── 9. Build cadence-degradation tables ──────────────────────────────────
    rmse_table: dict[str, dict[str, float]] = {L: {} for L in LAYERS}
    mae_table:  dict[str, dict[str, float]] = {L: {} for L in LAYERS}

    for s_name, result in all_results.items():
        for L in LAYERS:
            m = result["metrics"]["layers"][L]
            rmse_table[L][s_name] = m["RMSE_mm"] if m["RMSE_mm"] is not None else float("nan")
            mae_table[L][s_name]  = m["MAE_mm"]  if m["MAE_mm"]  is not None else float("nan")

    # Minimum cadence meeting L1 per layer.
    # Ladder ordered sparsest → densest; 'blackout' and 'actual' excluded because
    # neither is a recommended regular cadence (blackout = special scenario,
    # actual = irregular baseline).  Stop at the FIRST (sparsest) schedule that
    # passes both thresholds.
    min_cadence_L1: dict[str, Optional[str]] = {}
    cadence_ladder = ["none", "annual", "semiannual", "quarterly", "monthly"]
    for L in LAYERS:
        found = None
        for s_name in cadence_ladder:          # sparsest first
            mae_v  = mae_table[L].get(s_name, float("nan"))
            rmse_v = rmse_table[L].get(s_name, float("nan"))
            if np.isfinite(mae_v) and np.isfinite(rmse_v):
                if mae_v <= MAE_THRESH[L] and rmse_v <= RMSE_THRESH[L]:
                    found = s_name
                    break                      # first passing = sparsest → done
        min_cadence_L1[L] = found if found is not None else "denser_than_monthly"

    # Write CSV: rows=layers, cols=schedules
    rows_csv = []
    for L in LAYERS:
        row = {"layer": L}
        for s in schedule_order:
            row[s] = rmse_table[L].get(s, float("nan"))
        rows_csv.append(row)
    df_csv = pd.DataFrame(rows_csv).set_index("layer")
    deg_csv_path = OUT_RESULTS / "cadence_degradation_curve.csv"
    df_csv.to_csv(deg_csv_path)
    print(f"\n  Written: {deg_csv_path}")

    # Write JSON: RMSE + MAE tables
    deg_json = {
        "description": "Blind prequential RMSE and MAE per layer per schedule, 2019-2023",
        "rmse_mm": {L: {s: (round(v, 3) if np.isfinite(v) else None)
                        for s, v in rmse_table[L].items()} for L in LAYERS},
        "mae_mm":  {L: {s: (round(v, 3) if np.isfinite(v) else None)
                        for s, v in mae_table[L].items()} for L in LAYERS},
        "min_cadence_meeting_L1": min_cadence_L1,
        "L1_thresholds": {L: {"MAE_mm": MAE_THRESH[L], "RMSE_mm": RMSE_THRESH[L]} for L in LAYERS},
        "schedule_order": schedule_order,
    }
    deg_json_path = OUT_RESULTS / "cadence_degradation_curve.json"
    with open(deg_json_path, "w") as f:
        json.dump(deg_json, f, indent=2)
    print(f"  Written: {deg_json_path}")

    # Plot cadence curve
    cadence_png = OUT_PLOTS / "cadence_curve.png"
    plot_cadence_curve(rmse_table, mae_table, schedule_order, cadence_png)

    # ── 10. Run manifest ──────────────────────────────────────────────────────
    manifest = {
        "blind_start": BLIND_START.isoformat(),
        "blind_end": BLIND_END.isoformat(),
        "dense_end": DENSE_END.isoformat(),
        "seed_fit_window": f"{SEED_FIT_START.date()} — {SEED_FIT_END.date()}",
        "seed_walk_window": f"{SEED_START.date()} — {SEED_END.date()}",
        "seed_design_note": (
            "Conformal bank seeded by rehearsing the same cadence over 2015-2018. "
            "Per-layer models RE-FIT on 2010-2014 only (frozen tau, use_u, use_V, h_c from JSON; "
            "a, c, S_ke, S_kv re-estimated). Walk 2015→2018 with genuine visit dates generates "
            "out-of-window forward errors so half_width reflects genuine forecast uncertainty."
        ),
        "truth_source": str(ORIG_CSV),
        "truth_note": "264 genuine field visits (TUKU_orig_grouped.csv); grading against these only.",
        "dense_fill_role": "Overlay in plots (faint line, labeled); never graded.",
        "leakage_guard": "TimeOracle — backward advance raises LeakageError",
        "carrier_noise_mm": round(carrier_noise, 5) if np.isfinite(carrier_noise) else None,
        "step_flag_threshold_mm": round(step_threshold, 5) if np.isfinite(step_threshold) else None,
        "conformal_alpha": 0.10,
        "conformal_min_samples": 20,
        "schedules": {
            s_name: {
                "n_visits": len(schedules[s_name]),
                "visit_dates": [d.isoformat() for d in schedules[s_name]],
            }
            for s_name in schedule_order
        },
        "baseline_rmse_mm": {L: (round(v, 3) if np.isfinite(v) else None)
                              for L, v in rmse_baseline.items()},
        "leakage_fired_any": any(
            all_results[s]["metrics"]["leakage_fired"] for s in schedule_order
        ),
    }
    manifest_path = OUT_RESULTS / "run_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"  Written: {manifest_path}")

    # ── 11. Print summary table ───────────────────────────────────────────────
    print(f"\n{'='*80}")
    print("CADENCE-DEGRADATION RMSE TABLE (mm) — blind prequential, 2019–2023")
    print(f"{'─'*80}")
    hdr = f"{'Layer':<6}" + "".join(f"  {s:>11}" for s in schedule_order)
    print(hdr)
    print(f"{'─'*80}")
    for L in LAYERS:
        row_str = f"{L:<6}"
        for s in schedule_order:
            v = rmse_table[L].get(s, float("nan"))
            row_str += f"  {v:>11.2f}" if np.isfinite(v) else f"  {'nan':>11}"
        print(row_str)
    print(f"{'─'*80}")

    print(f"\n{'='*80}")
    print("SPARSEST CADENCE MEETING LEVEL-1 THRESHOLDS (MAE<thresh, RMSE<thresh)")
    for L in LAYERS:
        print(f"  {L}: {min_cadence_L1[L] or 'NO cadence meets L1'} "
              f"(MAE<{MAE_THRESH[L]}, RMSE<{RMSE_THRESH[L]} mm)")

    print(f"\n{'='*80}")
    print("F2 and F3 skill comparison (none vs annual vs monthly):")
    for L in ["F2", "F3"]:
        for s in ["none", "annual", "monthly"]:
            sk = all_results[s]["metrics"]["layers"][L].get("skill_vs_baseline")
            rmse = all_results[s]["metrics"]["layers"][L].get("RMSE_mm")
            print(f"  {L} [{s:>10}]: RMSE={rmse} mm  skill={sk}")

    print(f"\n{'='*80}")
    print("Band coverage at annual cadence per layer:")
    for L in LAYERS:
        cov = all_results["annual"]["metrics"]["layers"][L].get("band_coverage_fraction")
        hw  = all_results["annual"]["metrics"]["layers"][L].get("mean_half_width_mm")
        print(f"  {L}: coverage={cov}  mean_hw={hw} mm")

    print(f"\n{'='*80}")
    f3_drought = all_results["annual"]["metrics"]["layers"]["F3"].get("drought_2021_detection_date")
    print(f"F3 drought-2021 detection date (annual schedule): {f3_drought}")

    print(f"\n{'='*80}")
    print(f"Leakage fired in any schedule: "
          f"{any(all_results[s]['metrics']['leakage_fired'] for s in schedule_order)}")

    # ── 12. Re-read verification ──────────────────────────────────────────────
    print(f"\n{'='*80}")
    print("RE-READ VERIFICATION:")

    def verify_metrics(s_name: str):
        path = OUT_RESULTS / s_name / "metrics.json"
        with open(path) as f:
            on_disk = json.load(f)
        in_mem = all_results[s_name]["metrics"]
        ok = True
        for L in LAYERS:
            d_rmse = on_disk["layers"][L]["RMSE_mm"]
            m_rmse = in_mem["layers"][L]["RMSE_mm"]
            match = (d_rmse == m_rmse) or (d_rmse is None and m_rmse is None)
            if not match:
                print(f"  MISMATCH {s_name}/{L}: disk={d_rmse}  mem={m_rmse}")
                ok = False
            # Verify n_scoring_points is recorded and matches the top-level field
            d_nsp = on_disk["layers"][L].get("n_scoring_points")
            top_nsp = on_disk.get("n_scoring_points")
            if d_nsp is None or top_nsp is None or d_nsp != top_nsp:
                print(f"  n_scoring_points MISMATCH {s_name}/{L}: layer={d_nsp}  top-level={top_nsp}")
                ok = False
        return ok

    # Verify n_scoring_points identical across all schedules
    nsp_values = {}
    for s_name in schedule_order:
        p = OUT_RESULTS / s_name / "metrics.json"
        with open(p) as f:
            m = json.load(f)
        nsp_values[s_name] = m.get("n_scoring_points")
    all_nsp = list(nsp_values.values())
    if len(set(v for v in all_nsp if v is not None)) == 1:
        print(f"  n_scoring_points IDENTICAL across all schedules: {all_nsp[0]}")
    else:
        print(f"  n_scoring_points MISMATCH across schedules: {nsp_values}")

    for s_name in ["monthly", "annual", "none"]:
        ok = verify_metrics(s_name)
        print(f"  {s_name}: {'VERIFIED' if ok else 'MISMATCH — check above'}")

    # Verify cadence CSV
    df_verify = pd.read_csv(deg_csv_path, index_col=0)
    verified_csv = True
    for L in LAYERS:
        for s in schedule_order:
            v_disk = df_verify.loc[L, s] if s in df_verify.columns else float("nan")
            v_mem  = rmse_table[L].get(s, float("nan"))
            if not (np.isnan(v_disk) and np.isnan(v_mem)) and abs(float(v_disk) - float(v_mem)) > 1e-3:
                print(f"  CSV MISMATCH {L}/{s}: disk={v_disk}  mem={v_mem}")
                verified_csv = False
    print(f"  cadence_degradation_curve.csv: {'VERIFIED' if verified_csv else 'MISMATCH'}")

    print(f"\n  DONE — all outputs in {OUT_RESULTS} and {OUT_PLOTS}")


if __name__ == "__main__":
    main()
