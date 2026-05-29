"""
ihmf_detrend.py — Signal detrending and layer-level f̄_k loading for IHM-F v2.

Public API:
    detrend_signal(t_days, y, T=365.25)
        -> (y_detrended, trend_coef, trend_values)
        Remove intercept + linear trend + annual harmonic from any 1-D signal.
        Exact reconstruction: y_detrended + trend_values == y to floating-point precision.

    reconstruct_trend(trend_coef, t_days, T=365.25)
        -> trend_values
        Evaluate the 4-parameter trend model at arbitrary time points.

    load_fbar_layer(station, layer, project_root)
        -> float
        Return the layer-level median direct ratio f̄_k by summing ring-level
        f_median values over all rings classified to `layer`.

Design constraints:
    - detrend_signal and reconstruct_trend: pure numpy, no pandas, no file I/O.
    - load_fbar_layer: uses pandas for CSV reading only; no side effects.
    - No global state. All inputs are explicit arguments.

Physical guarantees:
    - Detrending preserves signal sign: detrended residuals oscillate around zero
      with the same units as the input.
    - GWL is never negated here. The caller passes dh = H(t) - H(t_ref); the
      detrend step removes the trend from dh without altering its sign convention.
    - f̄_k is a SUM (not average) of ring-level ratios × ring span, matching the
      MLCW layer-grouped aggregation convention (layer compaction = sum of rings).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path


# ── Trend basis ───────────────────────────────────────────────────────────────

def _trend_basis(t_days: np.ndarray, T: float = 365.25) -> np.ndarray:
    """
    Build the 4-column trend basis matrix for time array t_days.

    Columns: [1,  t,  sin(2π·t/T),  cos(2π·t/T)]
    T defaults to 365.25 days (one tropical year).
    """
    omega = 2.0 * np.pi / T
    return np.column_stack([
        np.ones(len(t_days)),
        t_days,
        np.sin(omega * t_days),
        np.cos(omega * t_days),
    ])


# ── Public API ────────────────────────────────────────────────────────────────

def detrend_signal(
    t_days: np.ndarray,
    y: np.ndarray,
    T: float = 365.25,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Remove intercept + linear trend + annual harmonic from signal y.

    Parameters
    ----------
    t_days : 1-D float array
        Time in days from an arbitrary reference epoch (e.g. first InSAR epoch).
    y : 1-D float array, same length as t_days
        Signal to detrend (MLCW mm, GWL Δhead m, or InSAR mm).
    T : float
        Period of the annual harmonic in days. Default 365.25.

    Returns
    -------
    y_detrended : ndarray
        Residual after removing the fitted trend. Same units as y.
        Satisfies: y_detrended + trend_values == y exactly.
    trend_coef : ndarray, shape (4,)
        OLS coefficients [c0, c1, c2, c3] for [1, t, sin, cos].
    trend_values : ndarray
        Fitted trend evaluated at t_days. Same units as y.

    Physical note
    -------------
    The basis [1, t, sin, cos] captures:
      - c0: initial-condition offset
      - c1 * t: long-term secular trend (regional dewatering)
      - c2, c3: annual seasonal cycle amplitude and phase
    After removal, y_detrended contains only sub-annual and inter-annual
    dynamics where GWL and InSAR are genuinely decoupled.
    """
    t_days = np.asarray(t_days, dtype=float)
    y = np.asarray(y, dtype=float)
    B = _trend_basis(t_days, T)
    trend_coef, _, _, _ = np.linalg.lstsq(B, y, rcond=None)
    trend_values = B @ trend_coef
    y_detrended = y - trend_values
    return y_detrended, trend_coef, trend_values


def reconstruct_trend(
    trend_coef: np.ndarray,
    t_days: np.ndarray,
    T: float = 365.25,
) -> np.ndarray:
    """
    Evaluate the 4-parameter trend model at arbitrary time points.

    Parameters
    ----------
    trend_coef : array-like, shape (4,)
        Coefficients from detrend_signal: [c0, c1, c2, c3].
    t_days : 1-D float array
        Time points at which to evaluate the trend (need not match training points).
    T : float
        Same period used in detrend_signal. Default 365.25.

    Returns
    -------
    trend_values : ndarray
        Trend evaluated at t_days. Same units as the original signal.

    Use case
    --------
    During walk-forward prediction, the test-year trend is reconstructed from
    the training-window trend_coef and the test-year t_days values. This avoids
    look-ahead contamination (fitting on test data).
    """
    B = _trend_basis(np.asarray(t_days, dtype=float), T)
    return B @ np.asarray(trend_coef, dtype=float)


def load_fbar_layer(
    station: str,
    layer: str,
    project_root: Path,
    insar_csv_path: Path | None = None,
) -> float:
    """
    Return the layer-level median direct ratio f̄_k for (station, layer).

    Computation method
    ------------------
    f̄_k = median( y_layer(t) / x_InSAR(t) ) over all valid epochs,

    where y_layer is the layer-grouped reconstructed MLCW compaction (mm) and
    x_InSAR is the cumulative InSAR surface displacement (mm) at the same station.
    Both are loaded from the same source files used by load_and_align, ensuring
    the ratio is consistent with the data seen by the model.

    This is computed directly from the layer-grouped MLCW — NOT from ring-level
    direct_ratio_stats.csv, which stores per-ring ratios that cannot be correctly
    aggregated to the layer-grouped scale (the layer-grouped MLCW includes signal
    reconstruction that changes the magnitude relative to raw ring sums).

    Physical sign clamping
    ----------------------
    f̄_k is clamped to max(0, f̄_k). A negative median ratio means noise or
    data artefacts dominate the layer; the trend term contributes nothing and
    the dynamic component (γ_k, β_k) carries the full prediction.

    Parameters
    ----------
    station : str
        Station name (e.g. 'TUKU').
    layer : str
        Layer code (e.g. 'F1', 'T1', 'F2', 'T2', 'F3', 'F4').
    project_root : Path
        Root of the scripts/data repository.
    insar_csv_path : Path, optional
        Path to InSAR_measures_at_MLCW.csv. Defaults to
        project_root/data/insar/InSAR_measures_at_MLCW.csv.

    Returns
    -------
    f_bar_k : float
        max(0, median(y_layer / x_InSAR)) over calibration epochs.
        Returns 0.0 if no valid epochs exist.

    Raises
    ------
    FileNotFoundError
        If MLCW or InSAR CSV is missing.
    """
    if insar_csv_path is None:
        insar_csv_path = project_root / "data" / "insar" / "InSAR_measures_at_MLCW.csv"

    mlcw_csv = (project_root / "data" / "mlcw" / "group_byLayer_reconstr"
                / f"{station}_reconst_grouped.csv")

    # Load layer-grouped MLCW
    mlcw_df = pd.read_csv(mlcw_csv, parse_dates=["datetime"])
    mlcw_df["datetime"] = pd.to_datetime(mlcw_df["datetime"])
    if layer not in mlcw_df.columns:
        return 0.0
    mlcw_df = mlcw_df[["datetime", layer]].rename(columns={layer: "mlcw_mm"})

    # Load InSAR for this station
    insar_df = pd.read_csv(insar_csv_path, parse_dates=[0])
    insar_df.columns = [c.strip() for c in insar_df.columns]
    insar_df = insar_df.rename(columns={insar_df.columns[0]: "datetime"})
    if station not in insar_df.columns:
        return 0.0
    insar_df = insar_df[["datetime", station]].dropna(subset=[station])
    insar_df["insar_mm"] = insar_df[station] * 1000.0

    # Align MLCW to InSAR timeline
    insar_sorted = insar_df.sort_values("datetime").reset_index(drop=True)
    mlcw_aligned = pd.merge_asof(
        insar_sorted[["datetime"]], mlcw_df.sort_values("datetime"),
        on="datetime", direction="nearest"
    )
    merged = insar_sorted[["datetime", "insar_mm"]].merge(mlcw_aligned, on="datetime")
    merged = merged.dropna(subset=["mlcw_mm", "insar_mm"])

    # Compute f̄_k from INCREMENTAL changes from the first epoch.
    # Both MLCW and InSAR are cumulative signals from an arbitrary reference date;
    # we subtract the first-epoch value so both start at zero.
    # f̄_k = median( Δy_layer(t) / Δx_InSAR(t) ) where Δ = change from epoch 0.
    # This is the quantity that appears in the trend formula:
    #     y_trend(t) = y(t0) + f̄_k · Δx(t)
    # Exclude the first epoch (ratio undefined, 0/0) and epochs where ΔInSAR < 0.1 mm.
    y0 = float(merged["mlcw_mm"].iloc[0])
    x0 = float(merged["insar_mm"].iloc[0])
    dy = merged["mlcw_mm"] - y0   # incremental MLCW from epoch 0
    dx = merged["insar_mm"] - x0  # incremental InSAR from epoch 0

    mask = dx.abs() > 0.5          # exclude near-zero incremental InSAR
    ratios = dy[mask] / dx[mask]
    ratios = ratios.replace([float("inf"), float("-inf")], float("nan")).dropna()

    if len(ratios) == 0:
        return 0.0

    f_bar_k = float(ratios.median())
    return max(0.0, f_bar_k)
