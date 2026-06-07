"""
01_seasonal_harmonic_analysis.py
---------------------------------
Seasonal harmonic characterisation of per-layer MLCW compaction using InSAR.
Three-station pilot: TUKU, XIUTAN, YUANCHANG.

Physical motivation
-------------------
Taiwan has two rice-growing seasons (Jan-May and Jun-Oct), producing a bimodal
groundwater pumping cycle ~182 days apart — the physical basis for the semi-annual
(T = 182.5 d) harmonic. The annual harmonic captures the overall wet/dry envelope.
Maximum compaction in M23 confined-aquifer zones occurs in March-April, when
piezometric head reaches its seasonal minimum after the dry-season pumping peak.

Steps run sequentially (each gates the next):
  0 — Detrend method comparison on F2  (linear vs MA-365 vs MA-730)
  1 — Harmonic decomposition adequacy on all layers
  2 — InSAR harmonic decomposition + atmosphere sanity check
  3 — Per-year harmonic stability table (feasibility gate)
  4 — Temporal holdout on seasonal component (runs only if Step 3 passes)

Usage
-----
  $env:PYTHONPATH = ""; conda run -n fafalab python scripts/13_seasonal_insar/01_seasonal_harmonic_analysis.py --station TUKU
  $env:PYTHONPATH = ""; conda run -n fafalab python scripts/13_seasonal_insar/01_seasonal_harmonic_analysis.py --station XIUTAN
  $env:PYTHONPATH = ""; conda run -n fafalab python scripts/13_seasonal_insar/01_seasonal_harmonic_analysis.py --station YUANCHANG

Outputs (under results/seasonal_insar_harmonic/{STATION}/ and figures/seasonal_insar_harmonic/{STATION}/)
  step0_detrend_comparison_F2.csv
  step1_harmonic_decomposition_all_layers.csv
  step2_insar_harmonic_decomposition.csv
  step3_peryear_harmonic_stability.csv
  step3_phase_stability_summary.csv
  step4_temporal_holdout.csv            (only if Step 3 gate passes)
  figures: step0, step3_phase, step3_amplitude
"""

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ── Constants ─────────────────────────────────────────────────────────────────
ANNUAL_T       = 365.25         # days
SEMI_T         = 182.625        # days (semi-annual period)
MA_WINDOWS     = [365, 730]     # moving-average window sizes tested in Step 0
LAYERS         = ['F1', 'T1', 'F2', 'T2', 'F3', 'F4']

# Step 3 gate thresholds
PHASE_STAB_THRESHOLD_DAYS = 45  # std(phase offset) < 45 d → PASS
MIN_AMPLITUDE_MM          = 0.5 # mean annual amplitude > 0.5 mm → PASS
MIN_EPOCHS_PER_YEAR       = 50  # require ≥50 valid epochs to fit a yearly harmonic

# Physical sanity window: InSAR annual harmonic minimum (most compaction) expected
# in March-April → DOY 60-120.  Outside this range → flag possible tropospheric signal.
PHYSICAL_MIN_DOY_LO = 60
PHYSICAL_MIN_DOY_HI = 120

# Walk-forward split
TRAIN_YEARS   = list(range(2015, 2022))   # 2015-2021
HOLDOUT_YEARS = [2022, 2023, 2024, 2025]
MLCW_RECONSTRUCTED_YEAR = 2022            # MLCW sensor data absent this year (reconstructed)

ANALYSIS_START = '2015-01-01'
ANALYSIS_END   = '2025-12-31'


# ── Path helpers ──────────────────────────────────────────────────────────────
def find_project_root() -> Path:
    """Walk up from this script's location to find the repo root."""
    candidate = Path(__file__).resolve().parent
    for _ in range(4):
        candidate = candidate.parent
        if (candidate / 'data' / 'mlcw').exists():
            return candidate
    raise RuntimeError(
        "Cannot locate project root. Expected data/mlcw/ directory. "
        "Run from within D:\\1000_SCRIPTS\\...\\20260427_InSAR_MLCW_v2."
    )


def make_dirs(root: Path, station: str):
    """Create output directories."""
    (root / 'results' / 'seasonal_insar_harmonic' / station).mkdir(parents=True, exist_ok=True)
    (root / 'figures' / 'seasonal_insar_harmonic' / station).mkdir(parents=True, exist_ok=True)


# ── Data loading ──────────────────────────────────────────────────────────────
def load_mlcw(station: str, root: Path) -> pd.DataFrame:
    """Load layer-grouped MLCW timeseries, filtered to analysis window."""
    path = root / 'data' / 'mlcw' / 'group_byLayer_reconstr' / f'{station}_reconst_grouped.csv'
    if not path.exists():
        raise FileNotFoundError(f"MLCW file not found: {path}")
    df = pd.read_csv(path, parse_dates=['datetime'])
    df = df.sort_values('datetime').reset_index(drop=True)
    mask = (df['datetime'] >= ANALYSIS_START) & (df['datetime'] <= ANALYSIS_END)
    df = df[mask].reset_index(drop=True)
    # Keep only the layer columns that are present
    available_layers = [L for L in LAYERS if L in df.columns]
    return df[['datetime'] + available_layers]


def load_insar(station: str, root: Path) -> pd.Series:
    """
    Load InSAR cumulative displacement timeseries for one station.
    Returns a pd.Series with DatetimeIndex, values in mm (negative = subsidence).
    Tries the feather file first, falls back to any companion CSV.
    """
    feather_path = root / 'data' / 'insar' / 'timeseries' / 'mlcw_interp_insar_IDW_extend.feather'

    if feather_path.exists():
        df = pd.read_feather(feather_path)

        # Station identifier column is 'Ename' (e.g., 'TUKU', 'XIUTAN')
        # Epoch columns are named 'D20150121', 'D20150126', ... (prefix 'D' + YYYYMMDD)
        station_col = None
        for col in ['Ename', 'station', 'Station', 'STATION', 'name', 'Name', 'site']:
            if col in df.columns and station in df[col].values:
                station_col = col
                break

        if station_col is None:
            text_cols = [c for c in df.columns if df[c].dtype == object]
            raise KeyError(
                f"Station '{station}' not found in InSAR feather. "
                f"Available text columns: {text_cols[:10]}"
            )

        row = df[df[station_col] == station]
        if len(row) != 1:
            raise ValueError(f"Expected exactly 1 row for station '{station}', got {len(row)}.")

        # Epoch columns: 'D' prefix + YYYYMMDD date string
        epoch_cols, epoch_dates = [], []
        for c in df.columns:
            if isinstance(c, str) and c.startswith('D') and len(c) == 9:
                try:
                    d = pd.to_datetime(c[1:], format='%Y%m%d')
                    epoch_cols.append(c)
                    epoch_dates.append(d)
                except Exception:
                    pass

        # Fallback: try parsing all columns as dates without prefix
        if not epoch_cols:
            for c in df.columns:
                try:
                    d = pd.to_datetime(str(c))
                    epoch_cols.append(c)
                    epoch_dates.append(d)
                except Exception:
                    pass

        if not epoch_cols:
            raise ValueError("No epoch columns found in InSAR feather.")

        values = row[epoch_cols].values.flatten().astype(float)
        # Values in metres → convert to mm if magnitude is sub-millimetre
        if np.nanmedian(np.abs(values[~np.isnan(values)])) < 1.0:
            values = values * 1000.0

        series = pd.Series(values, index=pd.DatetimeIndex(epoch_dates), name='insar_mm')
        series = series.sort_index()
        mask = (series.index >= ANALYSIS_START) & (series.index <= ANALYSIS_END)
        return series[mask]

    raise FileNotFoundError(f"InSAR feather not found: {feather_path}")


# ── Detrending ────────────────────────────────────────────────────────────────
def t_days_from_dates(dates: pd.DatetimeIndex, ref: pd.Timestamp = None) -> np.ndarray:
    """
    True elapsed days from a reference date (default: first date in series).
    Uses actual calendar days, NOT row index — important for non-uniform 5-day grid.
    """
    if ref is None:
        ref = dates[0]
    return (dates - ref).total_seconds().values / 86400.0


def detrend_linear(t: np.ndarray, y: np.ndarray):
    """Remove linear trend. Returns (y_detrended, y_trend, coef)."""
    valid = ~np.isnan(y)
    A = np.column_stack([np.ones(valid.sum()), t[valid]])
    coef, _, _, _ = np.linalg.lstsq(A, y[valid], rcond=None)
    y_trend = np.full_like(y, np.nan)
    y_trend = coef[0] + coef[1] * t
    return y - y_trend, y_trend, coef


def detrend_ma(dates: pd.DatetimeIndex, y: np.ndarray, window_days: int):
    """
    Remove trend estimated by a centered moving average of width window_days.
    Returns (y_detrended, y_trend).
    NaNs appear at edges where the window cannot be filled to min_periods.
    """
    series = pd.Series(y, index=dates)
    min_p = window_days // 2
    y_trend = series.rolling(f'{window_days}D', center=True, min_periods=min_p).mean().values
    return y - y_trend, y_trend


# ── Harmonic fitting ──────────────────────────────────────────────────────────
def harmonic_basis(t: np.ndarray, include_semiannual: bool = True) -> np.ndarray:
    """Build harmonic design matrix [sin1, cos1, sin2, cos2] using true elapsed days."""
    omega1 = 2 * np.pi / ANNUAL_T
    cols = [np.sin(omega1 * t), np.cos(omega1 * t)]
    if include_semiannual:
        omega2 = 2 * np.pi / SEMI_T
        cols += [np.sin(omega2 * t), np.cos(omega2 * t)]
    return np.column_stack(cols)


def fit_harmonic(t: np.ndarray, y: np.ndarray, include_semiannual: bool = True):
    """
    Fit annual (+ optional semi-annual) harmonic model to (t, y).
    Returns dict with amplitudes, phases, R2, residuals.
    Phase convention: phi_doy is DOY of harmonic MAXIMUM (most positive value).
    For MLCW/InSAR (negative = compaction), the compaction peak is at phi_min_doy.
    """
    valid = ~np.isnan(y)
    if valid.sum() < 10:
        return None

    H = harmonic_basis(t[valid], include_semiannual)
    coef, _, _, _ = np.linalg.lstsq(H, y[valid], rcond=None)
    y_hat_valid = H @ coef

    # Reconstruct on full grid (including NaNs)
    H_full = harmonic_basis(t, include_semiannual)
    y_hat = H_full @ coef

    # Annual component: c[0]*sin + c[1]*cos = R*sin(omega*t + phi)
    # R = sqrt(c0^2 + c1^2), phi = atan2(c1, c0)
    # Maximum of sin(omega*t + phi) at t_max = (pi/2 - phi) / omega
    c0, c1 = coef[0], coef[1]
    A1 = float(np.sqrt(c0**2 + c1**2))
    phi1_rad = float(np.arctan2(c1, c0))
    # DOY of maximum (most positive)
    phi1_max_doy = float(((-phi1_rad + np.pi / 2) / (2 * np.pi) * ANNUAL_T) % ANNUAL_T)
    # DOY of minimum (most compaction = most negative for InSAR/MLCW sign convention)
    phi1_min_doy = float((phi1_max_doy + ANNUAL_T / 2) % ANNUAL_T)

    result = {
        'A1_mm':         A1,
        'phi1_max_doy':  phi1_max_doy,
        'phi1_min_doy':  phi1_min_doy,
        'phi1_rad':      phi1_rad,
        'coef_sin1':     float(c0),
        'coef_cos1':     float(c1),
    }

    if include_semiannual and len(coef) >= 4:
        c2, c3 = coef[2], coef[3]
        A2 = float(np.sqrt(c2**2 + c3**2))
        phi2_rad = float(np.arctan2(c3, c2))
        phi2_max_doy = float(((-phi2_rad + np.pi / 2) / (2 * np.pi) * SEMI_T) % SEMI_T)
        result.update({
            'A2_mm':         A2,
            'phi2_max_doy':  phi2_max_doy,
            'phi2_rad':      phi2_rad,
            'coef_sin2':     float(c2),
            'coef_cos2':     float(c3),
        })

    # R² (only on valid points)
    residuals = y[valid] - y_hat_valid
    ss_res = float(np.sum(residuals**2))
    ss_tot = float(np.sum((y[valid] - np.nanmean(y[valid]))**2))
    result['R2'] = float(1 - ss_res / ss_tot) if ss_tot > 0 else np.nan
    result['RMSE_mm'] = float(np.sqrt(np.mean(residuals**2)))
    result['y_hat'] = y_hat
    result['n_valid'] = int(valid.sum())
    return result


def fit_annual_only(t: np.ndarray, y: np.ndarray):
    """Fit annual-only harmonic (no semi-annual). Wrapper for decomposition adequacy."""
    return fit_harmonic(t, y, include_semiannual=False)


def snr_from_fit(full_fit, annual_fit, key='A2_mm'):
    """Signal-to-noise ratio for semi-annual component."""
    if full_fit is None or annual_fit is None:
        return np.nan
    # SNR = semi-annual amplitude / std(residual after removing annual)
    residual_after_annual = annual_fit.get('y_hat')
    # Actually: SNR = A2 / std(full residual)
    A2 = full_fit.get(key, 0)
    if 'RMSE_mm' in full_fit:
        return A2 / full_fit['RMSE_mm'] if full_fit['RMSE_mm'] > 0 else np.nan
    return np.nan


# ── Circular statistics ───────────────────────────────────────────────────────
def circ_std_days(phi_rad_array: np.ndarray, period_days: float = ANNUAL_T) -> float:
    """
    Circular standard deviation of phase angles (in radians).
    Converted to days using the given period.
    """
    valid = phi_rad_array[~np.isnan(phi_rad_array)]
    if len(valid) < 2:
        return np.nan
    C = np.mean(np.cos(valid))
    S = np.mean(np.sin(valid))
    R = np.sqrt(C**2 + S**2)
    circ_std_rad = np.sqrt(-2 * np.log(np.clip(R, 1e-10, 1.0)))
    return circ_std_rad / (2 * np.pi) * period_days


def circ_mean_doy(phi_rad_array: np.ndarray, period_days: float = ANNUAL_T) -> float:
    """Circular mean of phase, returned as day-of-period."""
    valid = phi_rad_array[~np.isnan(phi_rad_array)]
    if len(valid) == 0:
        return np.nan
    C = np.mean(np.cos(valid))
    S = np.mean(np.sin(valid))
    mean_rad = np.arctan2(S, C)
    mean_doy = ((-mean_rad + np.pi / 2) / (2 * np.pi) * period_days) % period_days
    return float(mean_doy)


# ── Plotting helpers ──────────────────────────────────────────────────────────
def save_fig(fig, path: Path, dpi: int = 120):
    fig.savefig(path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    print(f"  Figure saved → {path.name}")


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 0 — Detrend method selection on F2
# ═══════════════════════════════════════════════════════════════════════════════
def step0_detrend_comparison(station: str, mlcw_df: pd.DataFrame, insar_s: pd.Series,
                             root: Path) -> str:
    """
    Compare linear vs MA-365 vs MA-730 detrending on F2.
    Returns the winning method label ('linear', 'MA_365', or 'MA_730').
    """
    print("\n── Step 0: Detrend method comparison (F2) ──")
    out_dir = root / 'results' / 'seasonal_insar_harmonic' / station
    fig_dir = root / 'figures' / 'seasonal_insar_harmonic' / station

    if 'F2' not in mlcw_df.columns:
        print("  WARNING: F2 not present at this station. Using first available layer.")
        ref_layer = [c for c in LAYERS if c in mlcw_df.columns][0]
    else:
        ref_layer = 'F2'

    # Align MLCW and InSAR to a common timeline
    # Use MLCW dates as reference; snap InSAR to nearest MLCW epoch
    mlcw_dates = mlcw_df['datetime']
    t_ref = mlcw_dates.iloc[0]
    t_mlcw = t_days_from_dates(pd.DatetimeIndex(mlcw_dates), t_ref)
    y_mlcw = mlcw_df[ref_layer].values.astype(float)

    # Align InSAR to MLCW timeline via merge_asof
    insar_df_tmp = insar_s.reset_index()
    insar_df_tmp.columns = ['datetime', 'insar_mm']
    merged = pd.merge_asof(mlcw_df[['datetime']].copy().sort_values('datetime'),
                           insar_df_tmp.sort_values('datetime'),
                           on='datetime', direction='nearest',
                           tolerance=pd.Timedelta('10D'))
    y_insar = merged['insar_mm'].values.astype(float)
    # Recompute t_days on the merged timeline
    t_merged = t_days_from_dates(pd.DatetimeIndex(merged['datetime']), t_ref)

    rows = []
    detrend_methods = {
        'linear': lambda: detrend_linear(t_mlcw, y_mlcw),
    }
    for W in MA_WINDOWS:
        label = f'MA_{W}'
        detrend_methods[label] = (lambda w=W: detrend_ma(pd.DatetimeIndex(mlcw_dates), y_mlcw, w))

    # Also detrend InSAR for sanity check
    insar_detrend_methods = {
        'linear': lambda: detrend_linear(t_merged, y_insar),
    }
    for W in MA_WINDOWS:
        label = f'MA_{W}'
        insar_detrend_methods[label] = (lambda w=W: detrend_ma(pd.DatetimeIndex(merged['datetime']), y_insar, w))

    fig, axes = plt.subplots(len(detrend_methods), 2, figsize=(14, 4 * len(detrend_methods)),
                             sharex=True)
    if len(detrend_methods) == 1:
        axes = axes[np.newaxis, :]

    for idx, (method_label, detrend_fn) in enumerate(detrend_methods.items()):
        y_det, y_tr, *_ = detrend_fn()
        y_insar_det, _, *_ = insar_detrend_methods[method_label]()

        fit_mlcw  = fit_harmonic(t_mlcw,  y_det,       include_semiannual=True)
        fit_insar = fit_harmonic(t_merged, y_insar_det, include_semiannual=True)

        R2_mlcw  = fit_mlcw['R2']   if fit_mlcw  else np.nan
        A1_mlcw  = fit_mlcw['A1_mm'] if fit_mlcw  else np.nan
        A2_mlcw  = fit_mlcw.get('A2_mm', np.nan) if fit_mlcw else np.nan
        phi1_min_mlcw = fit_mlcw['phi1_min_doy'] if fit_mlcw else np.nan
        phi1_min_insar = fit_insar['phi1_min_doy'] if fit_insar else np.nan
        A1_insar = fit_insar['A1_mm'] if fit_insar else np.nan

        insar_phase_physical = (PHYSICAL_MIN_DOY_LO <= phi1_min_insar <= PHYSICAL_MIN_DOY_HI
                                if not np.isnan(phi1_min_insar) else False)

        W_val = int(method_label.split('_')[1]) if method_label.startswith('MA') else 0
        rows.append({
            'method':              method_label,
            'W_days':              W_val,
            'F2_R2_harmonic':      round(float(R2_mlcw), 4),
            'F2_A1_mm':            round(float(A1_mlcw), 3),
            'F2_phi1_min_doy':     round(float(phi1_min_mlcw), 1),
            'F2_A2_mm':            round(float(A2_mlcw), 3),
            'InSAR_phi1_min_doy':  round(float(phi1_min_insar), 1),
            'InSAR_A1_mm':         round(float(A1_insar), 3),
            'insar_phase_physical': insar_phase_physical,
        })

        # Plot
        ax0, ax1 = axes[idx, 0], axes[idx, 1]
        ax0.plot(mlcw_dates, y_det, color='steelblue', lw=0.8, alpha=0.7, label=f'{ref_layer} detrended')
        if fit_mlcw:
            ax0.plot(mlcw_dates, fit_mlcw['y_hat'], color='red', lw=1.5, label=f'Harmonic fit (R²={R2_mlcw:.3f})')
        ax0.set_title(f'{method_label}: {ref_layer} MLCW detrended')
        ax0.set_ylabel('mm'); ax0.legend(fontsize=7)

        ax1.plot(merged['datetime'], y_insar_det, color='darkorange', lw=0.8, alpha=0.7, label='InSAR detrended')
        if fit_insar:
            ax1.plot(merged['datetime'], fit_insar['y_hat'], color='red', lw=1.5,
                     label=f'Harmonic fit (R²={fit_insar["R2"]:.3f})\nMin DOY={phi1_min_insar:.0f} {"✓" if insar_phase_physical else "⚠ATM?"}')
        ax1.set_title(f'{method_label}: InSAR detrended at {station}')
        ax1.set_ylabel('mm'); ax1.legend(fontsize=7)

    fig.suptitle(f'{station} — Step 0: Detrend method comparison on {ref_layer}', fontsize=11)
    fig.tight_layout()
    save_fig(fig, fig_dir / 'step0_detrend_comparison_F2.png')

    df_out = pd.DataFrame(rows)
    df_out.to_csv(out_dir / 'step0_detrend_comparison_F2.csv', index=False)
    print(f"  Saved → step0_detrend_comparison_F2.csv")
    print(df_out[['method', 'F2_R2_harmonic', 'F2_A1_mm', 'F2_phi1_min_doy',
                  'InSAR_phi1_min_doy', 'insar_phase_physical']].to_string(index=False))

    # Select winning method
    # Rule 1: highest R2 on F2 MLCW
    best_idx = df_out['F2_R2_harmonic'].idxmax()
    winner = df_out.loc[best_idx, 'method']

    # Rule 2: prefer linear if MA_365 wins but its A1 is >20% lower than linear
    linear_A1 = df_out.loc[df_out['method'] == 'linear', 'F2_A1_mm'].values
    winner_A1 = df_out.loc[best_idx, 'F2_A1_mm']
    if winner == 'MA_365' and len(linear_A1) > 0:
        if winner_A1 < linear_A1[0] * 0.80:
            winner = 'linear'
            print(f"  NOTE: MA_365 A1 < 80% of linear A1 → reverting to linear.")

    print(f"\n  ► Winning detrend method: {winner}")

    if df_out['F2_R2_harmonic'].max() < 0.05:
        print(f"  WARNING: No method achieves R² > 0.05 on {ref_layer}. Low seasonal signal at {station}.")

    return winner


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Harmonic decomposition adequacy (all layers)
# ═══════════════════════════════════════════════════════════════════════════════
def step1_decomposition_adequacy(station: str, mlcw_df: pd.DataFrame, winner: str,
                                 root: Path) -> pd.DataFrame:
    """
    Fit annual + semi-annual harmonic to all available layers using the winning
    detrend method. Report R², amplitudes, phases, and flag weak semi-annual.
    """
    print("\n── Step 1: Harmonic decomposition adequacy (all layers) ──")
    out_dir = root / 'results' / 'seasonal_insar_harmonic' / station

    mlcw_dates = pd.DatetimeIndex(mlcw_df['datetime'])
    t_ref = mlcw_dates[0]
    t = t_days_from_dates(mlcw_dates, t_ref)
    available_layers = [L for L in LAYERS if L in mlcw_df.columns]

    rows = []
    for layer in available_layers:
        y = mlcw_df[layer].values.astype(float)

        if winner == 'linear':
            y_det, _, _ = detrend_linear(t, y)
        else:
            W = int(winner.split('_')[1])
            y_det, _ = detrend_ma(mlcw_dates, y, W)

        fit_annual = fit_annual_only(t, y_det)
        fit_full   = fit_harmonic(t, y_det, include_semiannual=True)

        if fit_full is None:
            rows.append({'layer': layer, 'note': 'insufficient data'})
            continue

        A1 = fit_full['A1_mm']
        A2 = fit_full.get('A2_mm', np.nan)
        R2_annual = fit_annual['R2'] if fit_annual else np.nan
        R2_full   = fit_full['R2']

        # Semi-annual SNR: A2 / RMSE of full fit (residual std)
        snr_semi = A2 / fit_full['RMSE_mm'] if (fit_full['RMSE_mm'] > 0 and not np.isnan(A2)) else np.nan

        # Flag semi-annual for dropping if weak
        semi_flag = (
            (not np.isnan(A2) and A2 < 0.2) or
            (not np.isnan(snr_semi) and snr_semi < 1.5) or
            (not np.isnan(A1) and A1 > 0 and not np.isnan(A2) and A2 / A1 < 0.1)
        )

        rows.append({
            'layer':           layer,
            'R2_annual':       round(float(R2_annual), 4),
            'R2_full':         round(float(R2_full), 4),
            'A1_mm':           round(float(A1), 3),
            'phi1_min_doy':    round(float(fit_full['phi1_min_doy']), 1),
            'A2_mm':           round(float(A2), 3) if not np.isnan(A2) else np.nan,
            'phi2_max_doy':    round(float(fit_full.get('phi2_max_doy', np.nan)), 1),
            'SNR_annual':      round(float(A1 / fit_full['RMSE_mm']), 2) if fit_full['RMSE_mm'] > 0 else np.nan,
            'SNR_semi':        round(float(snr_semi), 2) if not np.isnan(snr_semi) else np.nan,
            'semi_annual_flag': 'drop' if semi_flag else 'keep',
            'n_valid_epochs':  fit_full['n_valid'],
        })
        print(f"  {layer}: R2_annual={R2_annual:.3f}, A1={A1:.2f}mm, phi1_min={fit_full['phi1_min_doy']:.0f}d, "
              f"A2={A2:.2f}mm, SNR_semi={snr_semi:.1f}, semi_flag={'drop' if semi_flag else 'keep'}")

    df_out = pd.DataFrame(rows)
    df_out.to_csv(out_dir / 'step1_harmonic_decomposition_all_layers.csv', index=False)
    print(f"  Saved → step1_harmonic_decomposition_all_layers.csv")

    # Sanity checks against known priors (TUKU-specific)
    if station == 'TUKU' and 'F2' in df_out['layer'].values:
        f2 = df_out[df_out['layer'] == 'F2'].iloc[0]
        if f2['R2_annual'] < 0.05:
            print(f"  WARNING: TUKU F2 R2_annual={f2['R2_annual']:.3f} — expected > 0.05 (prior: tau campaign r=0.69).")
        for layer in ['F3', 'F4']:
            row = df_out[df_out['layer'] == layer]
            if len(row) and row.iloc[0]['R2_annual'] > 0.3:
                print(f"  WARNING: {layer} R2_annual={row.iloc[0]['R2_annual']:.3f} > 0.3 — possible artifact (prior: trend-dominated).")

    return df_out


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2 — InSAR harmonic decomposition + atmosphere sanity check
# ═══════════════════════════════════════════════════════════════════════════════
def step2_insar_decomposition(station: str, mlcw_df: pd.DataFrame, insar_s: pd.Series,
                               winner: str, root: Path) -> dict:
    """
    Apply winning detrend method and harmonic fit to InSAR.
    Returns dict of InSAR harmonic parameters.
    """
    print("\n── Step 2: InSAR harmonic decomposition ──")
    out_dir = root / 'results' / 'seasonal_insar_harmonic' / station

    # Align InSAR to MLCW timeline
    insar_df_tmp = insar_s.reset_index()
    insar_df_tmp.columns = ['datetime', 'insar_mm']
    merged = pd.merge_asof(mlcw_df[['datetime']].copy().sort_values('datetime'),
                           insar_df_tmp.sort_values('datetime'),
                           on='datetime', direction='nearest',
                           tolerance=pd.Timedelta('10D'))
    merged = merged.sort_values('datetime').reset_index(drop=True)

    dates_merged = pd.DatetimeIndex(merged['datetime'])
    t_ref = dates_merged[0]
    t = t_days_from_dates(dates_merged, t_ref)
    y_insar = merged['insar_mm'].values.astype(float)

    if winner == 'linear':
        y_det, _, _ = detrend_linear(t, y_insar)
    else:
        W = int(winner.split('_')[1])
        y_det, _ = detrend_ma(dates_merged, y_insar, W)

    fit = fit_harmonic(t, y_det, include_semiannual=True)
    if fit is None:
        print("  ERROR: InSAR harmonic fit failed.")
        return {}

    phi1_min_doy = fit['phi1_min_doy']
    atm_flag = not (PHYSICAL_MIN_DOY_LO <= phi1_min_doy <= PHYSICAL_MIN_DOY_HI)

    result = {
        'A1_x_mm':          round(float(fit['A1_mm']), 3),
        'phi1_x_min_doy':   round(float(phi1_min_doy), 1),
        'A2_x_mm':          round(float(fit.get('A2_mm', np.nan)), 3),
        'phi2_x_max_doy':   round(float(fit.get('phi2_max_doy', np.nan)), 1),
        'R2_insar_full':    round(float(fit['R2']), 4),
        'atm_flag':         atm_flag,
        'InSAR_phi1_min_doy': round(float(phi1_min_doy), 1),
        'phi1_x_rad':       float(fit['phi1_rad']),
        'phi2_x_rad':       float(fit.get('phi2_rad', np.nan)),
        # Store detrended values for use in Step 3
        '_t':               t,
        '_dates':           dates_merged,
        '_y_det':           y_det,
        '_fit':             fit,
    }

    print(f"  InSAR: A1={result['A1_x_mm']:.2f}mm, phi1_min_doy={result['phi1_x_min_doy']:.0f}, "
          f"A2={result['A2_x_mm']:.2f}mm, R2={result['R2_insar_full']:.3f}")
    if atm_flag:
        print(f"  ⚠ ATM FLAG: InSAR phi1_min_doy={phi1_min_doy:.0f} outside expected "
              f"range ({PHYSICAL_MIN_DOY_LO}–{PHYSICAL_MIN_DOY_HI}). "
              f"Possible tropospheric annual cycle contamination.")
    else:
        print(f"  ✓ InSAR phase physically consistent (DOY {phi1_min_doy:.0f} in March–April window).")

    # Save CSV (without internal arrays)
    row_save = {k: v for k, v in result.items() if not k.startswith('_')}
    pd.DataFrame([row_save]).to_csv(out_dir / 'step2_insar_harmonic_decomposition.csv', index=False)
    print(f"  Saved → step2_insar_harmonic_decomposition.csv")

    # Export InSAR harmonic timeseries for use in prediction pipeline (Tier 2 seasonal term)
    omega = 2 * np.pi / ANNUAL_T
    sin1 = np.sin(omega * t)
    cos1 = np.cos(omega * t)
    insar_annual_component = fit['coef_sin1'] * sin1 + fit['coef_cos1'] * cos1
    df_insar_ts = pd.DataFrame({
        'datetime':           pd.Series(dates_merged),
        'A1_x_seasonal':      y_det,
        'A1_x_annual_model':  insar_annual_component,
    })
    ts_path = out_dir / 'insar_harmonic_timeseries.feather'
    df_insar_ts.to_feather(ts_path)
    print(f"  Saved → insar_harmonic_timeseries.feather  ({len(df_insar_ts)} rows)")

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Per-year harmonic stability table
# ═══════════════════════════════════════════════════════════════════════════════
def step3_peryear_stability(station: str, mlcw_df: pd.DataFrame, insar_info: dict,
                             winner: str, root: Path) -> tuple:
    """
    Fit harmonic year-by-year to globally-detrended signals.
    Returns (df_peryear, df_summary, gate_passed).
    """
    print("\n── Step 3: Per-year harmonic stability ──")
    out_dir = root / 'results' / 'seasonal_insar_harmonic' / station
    fig_dir = root / 'figures' / 'seasonal_insar_harmonic' / station

    if not insar_info:
        print("  SKIP: No InSAR info from Step 2.")
        return None, None, False

    available_layers = [L for L in LAYERS if L in mlcw_df.columns]

    # Global detrend on full window for all layers and InSAR
    mlcw_dates = pd.DatetimeIndex(mlcw_df['datetime'])
    t_ref = mlcw_dates[0]
    t_mlcw = t_days_from_dates(mlcw_dates, t_ref)

    insar_dates = insar_info['_dates']
    t_insar     = insar_info['_t']

    detrended_mlcw = {}
    for layer in available_layers:
        y = mlcw_df[layer].values.astype(float)
        if winner == 'linear':
            y_det, _, _ = detrend_linear(t_mlcw, y)
        else:
            W = int(winner.split('_')[1])
            y_det, _ = detrend_ma(mlcw_dates, y, W)
        detrended_mlcw[layer] = y_det

    y_insar_det = insar_info['_y_det']

    peryear_rows = []
    for year in range(2015, 2026):
        # InSAR mask for this year
        mask_insar = (insar_dates.year == year) & ~np.isnan(y_insar_det)
        if mask_insar.sum() < MIN_EPOCHS_PER_YEAR:
            continue
        t_i = t_insar[mask_insar]
        y_i = y_insar_det[mask_insar]
        fit_insar_yr = fit_harmonic(t_i, y_i, include_semiannual=True)
        if fit_insar_yr is None:
            continue
        A1_x_yr  = fit_insar_yr['A1_mm']
        phi1_x_yr = fit_insar_yr['phi1_rad']
        A2_x_yr  = fit_insar_yr.get('A2_mm', np.nan)
        phi2_x_yr = fit_insar_yr.get('phi2_rad', np.nan)

        for layer in available_layers:
            # Align: find MLCW dates that fall in this year
            mask_mlcw = (mlcw_dates.year == year) & ~np.isnan(detrended_mlcw[layer])
            if mask_mlcw.sum() < MIN_EPOCHS_PER_YEAR:
                continue
            t_m  = t_mlcw[mask_mlcw]
            y_m  = detrended_mlcw[layer][mask_mlcw]
            fit_yr = fit_harmonic(t_m, y_m, include_semiannual=True)
            if fit_yr is None:
                continue

            A1_k_yr  = fit_yr['A1_mm']
            phi1_k_yr = fit_yr['phi1_rad']
            A2_k_yr  = fit_yr.get('A2_mm', np.nan)
            phi2_k_yr = fit_yr.get('phi2_rad', np.nan)

            # Amplitude ratios (guard divide-by-zero)
            r1_k_yr = A1_k_yr / A1_x_yr if A1_x_yr > 1e-6 else np.nan
            r2_k_yr = (A2_k_yr / A2_x_yr
                       if (not np.isnan(A2_k_yr) and not np.isnan(A2_x_yr) and A2_x_yr > 1e-6)
                       else np.nan)

            # Phase offsets (circular difference: [-pi, pi])
            dphi1 = float(((phi1_k_yr - phi1_x_yr) + np.pi) % (2 * np.pi) - np.pi)
            dphi2 = (float(((phi2_k_yr - phi2_x_yr) + np.pi) % (2 * np.pi) - np.pi)
                     if not np.isnan(phi2_k_yr) and not np.isnan(phi2_x_yr) else np.nan)

            # Convert phase offset to days
            dphi1_days = dphi1 / (2 * np.pi) * ANNUAL_T
            dphi2_days = dphi2 / (2 * np.pi) * SEMI_T if not np.isnan(dphi2) else np.nan

            peryear_rows.append({
                'station':           station,
                'layer':             layer,
                'year':              year,
                'A1_k_mm':           round(float(A1_k_yr), 3),
                'phi1_k_doy':        round(float(fit_yr['phi1_min_doy']), 1),
                'phi1_k_rad':        float(phi1_k_yr),
                'A2_k_mm':           round(float(A2_k_yr), 3) if not np.isnan(A2_k_yr) else np.nan,
                'phi2_k_doy':        round(float(fit_yr.get('phi2_max_doy', np.nan)), 1),
                'A1_x_mm':           round(float(A1_x_yr), 3),
                'phi1_x_doy':        round(float(fit_insar_yr['phi1_min_doy']), 1),
                'phi1_x_rad':        float(phi1_x_yr),
                'A2_x_mm':           round(float(A2_x_yr), 3) if not np.isnan(A2_x_yr) else np.nan,
                'r1_k':              round(float(r1_k_yr), 4) if not np.isnan(r1_k_yr) else np.nan,
                'dphi1_k_days':      round(float(dphi1_days), 1),
                'r2_k':              round(float(r2_k_yr), 4) if not np.isnan(r2_k_yr) else np.nan,
                'dphi2_k_days':      round(float(dphi2_days), 1) if not np.isnan(dphi2_days) else np.nan,
                'mlcw_reconstructed': (year == MLCW_RECONSTRUCTED_YEAR),
                'n_epochs_mlcw':     int(mask_mlcw.sum()),
                'n_epochs_insar':    int(mask_insar.sum()),
            })

    df_peryear = pd.DataFrame(peryear_rows)
    if df_peryear.empty:
        print("  ERROR: No per-year rows computed. Check data availability.")
        return df_peryear, None, False

    df_peryear.to_csv(out_dir / 'step3_peryear_harmonic_stability.csv', index=False)
    print(f"  Saved → step3_peryear_harmonic_stability.csv  ({len(df_peryear)} rows)")

    # Summary statistics per layer
    summary_rows = []
    gate_passed = False
    for layer in available_layers:
        sub = df_peryear[df_peryear['layer'] == layer]
        if sub.empty:
            continue
        phi1_rads = sub['phi1_k_rad'].values
        dphi1_rads = sub['dphi1_k_days'].values / ANNUAL_T * 2 * np.pi
        A1_vals = sub['A1_k_mm'].values
        r1_vals = sub['r1_k'].dropna().values

        std_phi1_d  = circ_std_days(phi1_rads, ANNUAL_T)
        mean_phi1_d = circ_mean_doy(phi1_rads, ANNUAL_T)
        std_dphi1_d = circ_std_days(dphi1_rads, ANNUAL_T)
        mean_dphi1_d = float(np.nanmean(sub['dphi1_k_days'].values))
        mean_A1  = float(np.nanmean(A1_vals))
        mean_r1  = float(np.nanmean(r1_vals)) if len(r1_vals) else np.nan
        std_r1   = float(np.nanstd(r1_vals))  if len(r1_vals) else np.nan
        corr_A1  = float(np.corrcoef(sub['A1_k_mm'].values, sub['A1_x_mm'].values)[0, 1]
                         if len(sub) >= 3 else np.nan)

        passed = (not np.isnan(std_dphi1_d) and
                  std_dphi1_d < PHASE_STAB_THRESHOLD_DAYS and
                  mean_A1 > MIN_AMPLITUDE_MM and
                  corr_A1 > 0.0)
        if passed:
            gate_passed = True

        summary_rows.append({
            'station':          station,
            'layer':            layer,
            'mean_phi1_doy':    round(float(mean_phi1_d), 1),
            'std_phi1_days':    round(float(std_phi1_d), 1),
            'mean_dphi1_days':  round(float(mean_dphi1_d), 1),
            'std_dphi1_days':   round(float(std_dphi1_d), 1),
            'mean_r1':          round(float(mean_r1), 4),
            'std_r1':           round(float(std_r1), 4),
            'corr_A1k_A1x':     round(float(corr_A1), 3),
            'A1_mm_mean':       round(float(mean_A1), 3),
            'n_years':          len(sub),
            'annual_PASS':      passed,
        })
        status = "✓ PASS" if passed else "✗ fail"
        print(f"  {layer}: std_dphi1={std_dphi1_d:.1f}d, mean_A1={mean_A1:.2f}mm, "
              f"mean_r1={mean_r1:.3f}, corr_A1={corr_A1:.3f}  → {status}")

    df_summary = pd.DataFrame(summary_rows)
    df_summary.to_csv(out_dir / 'step3_phase_stability_summary.csv', index=False)
    print(f"  Saved → step3_phase_stability_summary.csv")
    print(f"\n  ► Gate result: {'PASS ✓ — proceed to Step 4' if gate_passed else 'FAIL ✗ — seasonal phase not stable'}")

    # Figures
    _plot_peryear_phase(station, df_peryear, available_layers, fig_dir)
    _plot_peryear_amplitude_ratio(station, df_peryear, available_layers, fig_dir)

    return df_peryear, df_summary, gate_passed


def _plot_peryear_phase(station, df, layers, fig_dir):
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = plt.cm.tab10(np.linspace(0, 1, len(layers)))
    for layer, color in zip(layers, colors):
        sub = df[df['layer'] == layer].sort_values('year')
        if sub.empty:
            continue
        ax.plot(sub['year'], sub['phi1_k_doy'], 'o-', label=layer, color=color, lw=1.5, ms=5)
        # Highlight 2022 (reconstructed)
        r = sub[sub['mlcw_reconstructed']]
        if not r.empty:
            ax.plot(r['year'], r['phi1_k_doy'], 's', color=color, ms=8, mec='red', mew=2)
    ax.axhspan(PHYSICAL_MIN_DOY_LO, PHYSICAL_MIN_DOY_HI, color='lightgreen', alpha=0.3,
               label='Expected range (Mar–Apr)')
    ax.set_xlabel('Year'); ax.set_ylabel('Annual compaction peak DOY')
    ax.set_title(f'{station} — Per-year annual phase (MLCW compaction min DOY)\n'
                 f'Square = 2022 reconstructed; green band = physical expectation')
    ax.legend(fontsize=8); ax.grid(True, alpha=0.3)
    save_fig(fig, fig_dir / 'step3_peryear_phase_per_layer.png')


def _plot_peryear_amplitude_ratio(station, df, layers, fig_dir):
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = plt.cm.tab10(np.linspace(0, 1, len(layers)))
    for layer, color in zip(layers, colors):
        sub = df[df['layer'] == layer].sort_values('year').dropna(subset=['r1_k'])
        if sub.empty:
            continue
        ax.plot(sub['year'], sub['r1_k'], 'o-', label=layer, color=color, lw=1.5, ms=5)
    ax.axhline(0, color='grey', lw=0.8, ls='--')
    ax.set_xlabel('Year'); ax.set_ylabel('r1_k = A1_MLCW / A1_InSAR')
    ax.set_title(f'{station} — Per-year annual amplitude ratio r1_k\n'
                 f'High variability confirms amplitude is not stable (expected from prior CSV)')
    ax.legend(fontsize=8); ax.grid(True, alpha=0.3)
    save_fig(fig, fig_dir / 'step3_peryear_amplitude_ratio.png')


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Temporal holdout on seasonal component
# ═══════════════════════════════════════════════════════════════════════════════
def step4_temporal_holdout(station: str, mlcw_df: pd.DataFrame, insar_info: dict,
                            df_summary: pd.DataFrame, winner: str, root: Path):
    """
    Fit mean (r̄1, Δφ̄1) on training years 2015-2021.
    Predict seasonal MLCW for 2022-2025. Score on detrended (seasonal-only) component.
    """
    print("\n── Step 4: Temporal holdout on seasonal component ──")
    out_dir = root / 'results' / 'seasonal_insar_harmonic' / station
    if df_summary is None or insar_info is None:
        print("  SKIP.")
        return

    available_layers = [L for L in LAYERS if L in mlcw_df.columns]
    mlcw_dates = pd.DatetimeIndex(mlcw_df['datetime'])
    t_ref = mlcw_dates[0]
    t_mlcw = t_days_from_dates(mlcw_dates, t_ref)

    insar_dates = insar_info['_dates']
    t_insar     = insar_info['_t']
    y_insar_det = insar_info['_y_det']

    # Global detrend
    detrended_mlcw = {}
    for layer in available_layers:
        y = mlcw_df[layer].values.astype(float)
        if winner == 'linear':
            y_det, _, _ = detrend_linear(t_mlcw, y)
        else:
            W = int(winner.split('_')[1])
            y_det, _ = detrend_ma(mlcw_dates, y, W)
        detrended_mlcw[layer] = y_det

    # Compute mean r̄1, Δφ̄1 from training years
    # Reload peryear stability CSV (easier than recomputing)
    peryear_path = out_dir / 'step3_peryear_harmonic_stability.csv'
    df_py = pd.read_csv(peryear_path)
    df_train = df_py[df_py['year'].isin(TRAIN_YEARS)]

    rows = []
    for layer in available_layers:
        sub_train = df_train[df_train['layer'] == layer].dropna(subset=['r1_k', 'dphi1_k_days'])
        if sub_train.empty:
            continue
        r1_bar   = float(sub_train['r1_k'].mean())
        dphi1_bar_days = float(sub_train['dphi1_k_days'].mean())
        dphi1_bar_rad  = dphi1_bar_days / ANNUAL_T * 2 * np.pi

        for year in HOLDOUT_YEARS:
            # InSAR harmonic for this hold-out year
            mask_insar = (insar_dates.year == year) & ~np.isnan(y_insar_det)
            if mask_insar.sum() < MIN_EPOCHS_PER_YEAR:
                continue
            fit_ix = fit_harmonic(t_insar[mask_insar], y_insar_det[mask_insar], include_semiannual=True)
            if fit_ix is None:
                continue
            A1_x = fit_ix['A1_mm']
            phi1_x_rad = fit_ix['phi1_rad']

            # Predicted seasonal for MLCW layer in this year
            mask_mlcw = (mlcw_dates.year == year)
            if mask_mlcw.sum() < MIN_EPOCHS_PER_YEAR:
                continue
            t_yr   = t_mlcw[mask_mlcw]
            y_obs  = detrended_mlcw[layer][mask_mlcw]
            valid  = ~np.isnan(y_obs)
            if valid.sum() < MIN_EPOCHS_PER_YEAR:
                continue

            # Predicted phase for layer k = InSAR phase + mean offset
            phi1_k_pred_rad = phi1_x_rad + dphi1_bar_rad
            y_pred = r1_bar * A1_x * np.sin(2 * np.pi * t_yr / ANNUAL_T + phi1_k_pred_rad
                                            + np.pi / 2)  # +pi/2 converts sin(+phi) convention

            rmse_pred = float(np.sqrt(np.nanmean((y_obs[valid] - y_pred[valid])**2)))
            rmse_base = float(np.nanstd(y_obs[valid]))  # baseline = predict zero seasonal
            skill = float(1 - rmse_pred / rmse_base) if rmse_base > 0 else np.nan

            rows.append({
                'station':           station,
                'layer':             layer,
                'year':              year,
                'rmse_predicted_mm': round(rmse_pred, 3),
                'rmse_baseline_mm':  round(rmse_base, 3),
                'skill_score':       round(float(skill), 3),
                'r1_bar_used':       round(float(r1_bar), 4),
                'dphi1_bar_days':    round(float(dphi1_bar_days), 1),
                'mlcw_reconstructed': (year == MLCW_RECONSTRUCTED_YEAR),
            })
            print(f"  {layer} {year}: RMSE_pred={rmse_pred:.2f}mm, RMSE_base={rmse_base:.2f}mm, "
                  f"skill={skill:+.3f} {'(reconstructed)' if year==MLCW_RECONSTRUCTED_YEAR else ''}")

    if rows:
        pd.DataFrame(rows).to_csv(out_dir / 'step4_temporal_holdout.csv', index=False)
        print(f"  Saved → step4_temporal_holdout.csv")
    else:
        print("  No holdout rows computed (insufficient data).")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main(station: str):
    print(f"\n{'='*60}")
    print(f"  Seasonal Harmonic Analysis — Station: {station}")
    print(f"{'='*60}")

    root = find_project_root()
    print(f"  Project root: {root}")
    make_dirs(root, station)

    # Load data
    print(f"\n  Loading MLCW ({ANALYSIS_START} → {ANALYSIS_END})...")
    mlcw_df = load_mlcw(station, root)
    available_layers = [L for L in LAYERS if L in mlcw_df.columns]
    print(f"  MLCW: {len(mlcw_df)} epochs, layers: {available_layers}")

    print(f"  Loading InSAR...")
    insar_s = load_insar(station, root)
    print(f"  InSAR: {len(insar_s)} epochs, range {insar_s.index.min().date()} → {insar_s.index.max().date()}")

    # Step 0 — choose detrend method
    winner = step0_detrend_comparison(station, mlcw_df, insar_s, root)

    # Step 1 — decomposition adequacy
    step1_decomposition_adequacy(station, mlcw_df, winner, root)

    # Step 2 — InSAR decomposition
    insar_info = step2_insar_decomposition(station, mlcw_df, insar_s, winner, root)

    # Step 3 — per-year stability (feasibility gate)
    df_peryear, df_summary, gate_passed = step3_peryear_stability(
        station, mlcw_df, insar_info, winner, root)

    # Step 4 — temporal holdout (only if gate passed)
    if gate_passed:
        step4_temporal_holdout(station, mlcw_df, insar_info, df_summary, winner, root)
    else:
        print("\n  Step 4 skipped (Step 3 gate did not pass).")

    print(f"\n{'='*60}")
    print(f"  Done: {station}. Results in results/seasonal_insar_harmonic/{station}/")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Seasonal harmonic pilot analysis.')
    parser.add_argument('--station', required=True,
                        help='Station to analyse (any station name from group_byLayer_reconstr/).')
    args = parser.parse_args()
    warnings.filterwarnings('ignore', category=RuntimeWarning)
    main(args.station)
