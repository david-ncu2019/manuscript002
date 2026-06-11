"""drivers.py — Continuous per-layer driver builder for TUKU frozen-model pipeline.

V-continuity guarantee: the virgin term V(t) = min(0, cummin_full(H) - h_c) is computed
over the ENTIRE available head history before any sub-window is selected.  Both calibration
(23_dense_calibration.py) and walk-forward (23_walk_forward.py) import this module and read
the SAME running-minimum V, ensuring there is no regime-reset artifact at the dense/blind
boundary.

NaN handling in running-minimum V:
  Head records have gaps (missing GWL observations).  We handle them as follows:
  1. Merge GWL to the 5-day MLCW grid with merge_asof (3-day tolerance).
  2. Forward-fill any remaining NaN gaps in H_abs ONLY for the purpose of computing the
     running minimum (we do NOT forward-fill for the u_lag term or the output column).
  3. Compute cummin on the forward-filled series, then apply it back to the original
     (un-filled) grid so that epochs with missing head still carry NaN in u_lag and
     the forward-fill leaks no fabricated signal into the regression.
  Rationale: the running minimum is a memory quantity (it captures the historical lowest
  head ever reached).  A gap in the record does not reset the physical soil memory; the
  cummin at the epoch after the gap is at most equal to the cummin at the epoch before
  the gap.  Forward-filling for the purpose of the cummin preserves this physics.
  The actual head values at gap epochs remain NaN in H_abs and u_lag, so these epochs are
  masked out of the regression by the finite-value filter in FrozenLayerModel.fit().

Usage:
    from tau_demo_TUKU.seq.drivers import build_layer_drivers

    df = build_layer_drivers(
        layer="F2", tau=72,
        gwl_feather="data/gwl/well_timeseries/TUKU_gwl_timeseries.feather",
        wellcode="09050321",
        gps_csv="data/gps/modeled/TKJS_model.csv",
        mlcw_inc_feather="tau_demo_TUKU/data/incremental_data/mlcw_diff_cleaned.feather",
        ref_date="2015-01-16",
    )
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ── Path resolution ───────────────────────────────────────────────────────────
# This file lives in tau_demo_TUKU/seq/.  The gap_aware_cumsum module lives in
# tau_demo_TUKU/.
_HERE = Path(__file__).resolve()
_TAU_DEMO = _HERE.parent.parent          # tau_demo_TUKU/
_ROOT = _TAU_DEMO.parent                 # repo root

if str(_TAU_DEMO) not in sys.path:
    sys.path.insert(0, str(_TAU_DEMO))
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from gap_aware_cumsum import gap_aware_cumulative, census  # noqa: E402

# ── Constants ─────────────────────────────────────────────────────────────────
_MERGE_TOL_GPS = pd.Timedelta("2D")
_MERGE_TOL_GWL = pd.Timedelta("3D")


def build_layer_drivers(
    layer: str,
    tau: int,
    gwl_feather: str | Path,
    wellcode: str,
    gps_csv: str | Path,
    mlcw_inc_feather: str | Path,
    ref_date: str = "2015-01-16",
) -> pd.DataFrame:
    """Build the full continuous per-layer driver frame over the 5-day MLCW grid.

    Parameters
    ----------
    layer : str
        Layer name (e.g. "F2").  Used for gap_aware_cumulative labelling.
    tau : int
        Consolidation lag in 5-day epoch units.  tau=72 means 360 days.
    gwl_feather : path
        Absolute path to the GWL timeseries feather file.
    wellcode : str
        8-digit string wellcode (NEVER convert to int — leading zeros drop).
    gps_csv : path
        Absolute path to TKJS_model.csv (GPS modeled column).
    mlcw_inc_feather : path
        Absolute path to mlcw_diff_cleaned.feather (incremental MLCW data).
    ref_date : str
        ISO date string for the reference epoch (default "2015-01-16").

    Returns
    -------
    pd.DataFrame
        Indexed 0..N-1, with columns:
          date      — numpy datetime64[ns], the response-epoch date
          d_gps     — GPS modeled displacement (mm); NaN where GPS not available
          H_abs     — absolute GWL head (m MSL); NaN at gap epochs
          u_lag     — zero-referenced lagged head: H_abs[i-tau] - ref_val (m)
          V_lag     — lagged virgin term: V_full[i-tau] (m, <= 0)
          b_cum     — gap-aware cumulative MLCW for this layer (mm)

    Notes
    -----
    - Row i: response b_cum[i] is paired with driver head at epoch i-tau.
      The first tau rows have NaN in u_lag and V_lag (no driver yet available).
    - V_full is computed over the ENTIRE head timeline before any sub-window.
    - h_c = min(pre-ref_date head) — Bug-F compliance.
    - ref_val = last pre-ref_date head value (same convention as Script 21).
    """
    REF_DATE = pd.Timestamp(ref_date)
    wellcode = str(wellcode)  # ensure 8-digit string; never convert to int

    # ── 1. Load MLCW increments → cumulative ──────────────────────────────────
    mlcw_inc = pd.read_feather(Path(mlcw_inc_feather))
    mlcw_inc["datetime"] = pd.to_datetime(mlcw_inc["datetime"]).astype("datetime64[ns]")
    mlcw_inc = mlcw_inc.sort_values("datetime").reset_index(drop=True)

    if layer not in mlcw_inc.columns:
        raise KeyError(f"Layer column '{layer}' not found in MLCW increments. "
                       f"Available: {[c for c in mlcw_inc.columns if c != 'datetime']}")

    # Gap-aware census guard, then cumulate
    census(mlcw_inc[layer].values, layer=layer, enforce_guard=True)
    b_cum_arr = gap_aware_cumulative(mlcw_inc[layer].values)

    # Master 5-day grid
    dates_full = mlcw_inc["datetime"].values.astype("datetime64[ns]")
    N = len(dates_full)
    master = pd.DataFrame({"datetime": dates_full})

    # ── 2. GPS d(t): merge_asof nearest <= 2 days ─────────────────────────────
    gps_df = pd.read_csv(Path(gps_csv))
    # GPS file has a 'date' column and 'modeled' column
    gps_df["datetime"] = pd.to_datetime(gps_df["date"]).astype("datetime64[ns]")
    gps_df = gps_df[["datetime", "modeled"]].sort_values("datetime").reset_index(drop=True)

    merged_gps = pd.merge_asof(
        master, gps_df,
        on="datetime",
        direction="nearest",
        tolerance=_MERGE_TOL_GPS,
    )
    d_gps_arr = merged_gps["modeled"].values.astype(float)  # mm

    # ── 3. GWL head: load, keep absolute (m MSL), merge_asof nearest <= 3 days ─
    gwl = pd.read_feather(Path(gwl_feather))
    gwl["datetime"] = pd.to_datetime(gwl["datetime"]).astype("datetime64[ns]")

    if wellcode not in gwl.columns:
        raise KeyError(f"Wellcode '{wellcode}' not found in {gwl_feather}. "
                       f"Available columns: {gwl.columns.tolist()}")

    gwl = gwl[["datetime", wellcode]].dropna(subset=[wellcode])
    gwl = gwl.sort_values("datetime").reset_index(drop=True)

    # Bug-F: h_c from pre-REF_DATE rows only (raw feather, before any zero-ref)
    pre_ref_mask = gwl["datetime"] < REF_DATE
    pre_ref_vals = gwl.loc[pre_ref_mask, wellcode].dropna()
    if len(pre_ref_vals) < 10:
        # Fallback: use entire available pre-REF record even if sparse
        if len(pre_ref_vals) == 0:
            raise RuntimeError(
                f"Layer {layer} / wellcode {wellcode}: "
                f"no pre-REF_DATE ({ref_date}) GWL — cannot compute h_c (Bug-F)."
            )
    h_c = float(pre_ref_vals.min())  # absolute m MSL

    # ref_val: last observed head on or before REF_DATE
    gwl_indexed = gwl.set_index("datetime")[wellcode]
    avail = gwl_indexed.dropna()
    pre_ref_idx = avail.index[avail.index <= REF_DATE]
    if len(pre_ref_idx) == 0:
        raise RuntimeError(
            f"Layer {layer}: no GWL on or before REF_DATE — cannot compute ref_val."
        )
    ref_val = float(avail.loc[pre_ref_idx[-1]])  # absolute m MSL

    # Merge GWL to master grid: H_abs stays absolute (m MSL), no zero-ref here
    merged_gwl = pd.merge_asof(
        master, gwl,
        on="datetime",
        direction="nearest",
        tolerance=_MERGE_TOL_GWL,
    )
    H_abs_arr = merged_gwl[wellcode].values.astype(float)  # m MSL, NaN at gaps

    # ── 4. Compute V_full over ENTIRE head timeline (NaN-safe running minimum) ─
    # Forward-fill H_abs ONLY for the running-minimum computation (preserves soil
    # memory across instrument gaps — the soil does not "forget" a low head just
    # because the gauge was offline).
    H_for_cummin = pd.Series(H_abs_arr).ffill().values.astype(float)
    # If the series starts with NaN (no pre-record), back-fill once so cummin
    # does not begin with NaN, then apply cummin.
    H_for_cummin = pd.Series(H_for_cummin).bfill().values.astype(float)

    # cummin of absolute head, then virgin term V = min(0, cummin - h_c)
    # np.fmin.accumulate treats NaN as the other operand (skip), but since we have
    # forward-filled above there are no remaining NaN to skip.
    cummin_full = np.minimum.accumulate(H_for_cummin)
    V_full = np.minimum(0.0, cummin_full - h_c)  # <= 0 always; 0 when elastic

    # ── 5. Apply tau lag via the Script-21 invariant ──────────────────────────
    # Driver at epoch i: H_abs[i - tau], V_full[i - tau]
    # Response at epoch i: b_cum[i]
    # First tau rows: no driver yet → NaN
    if tau == 0:
        u_lag = H_abs_arr - ref_val
        V_lag = V_full.copy()
    else:
        u_lag = np.full(N, np.nan)
        V_lag = np.full(N, np.nan)
        # H_abs[0:N-tau] drives response b_cum[tau:N]
        u_lag[tau:] = H_abs_arr[:N - tau] - ref_val
        V_lag[tau:] = V_full[:N - tau]

    # ── 6. Assemble output DataFrame ──────────────────────────────────────────
    df = pd.DataFrame({
        "date": dates_full,
        "d_gps": d_gps_arr,
        "H_abs": H_abs_arr,
        "u_lag": u_lag,
        "V_lag": V_lag,
        "b_cum": b_cum_arr,
    })

    # Attach metadata as attributes (used by calibration script for JSON)
    df.attrs["h_c"] = h_c
    df.attrs["ref_val"] = ref_val
    df.attrs["layer"] = layer
    df.attrs["wellcode"] = wellcode
    df.attrs["tau"] = tau

    return df
