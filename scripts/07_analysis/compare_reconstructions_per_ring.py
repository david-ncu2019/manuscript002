"""
Per-Ring Reconstruction Comparison: Three-Way Time-Series Overlay

For each station, creates six figures (3 for harmonic, 3 for wet/dry):
  - Compare observed MLCW, scalar baseline (f̄_k × InSAR), and new reconstruction
  - Layout: 5 cols × 4 rows = 20 subplots per figure
  - Three depth ranges: 0–95m, 100–195m, 200–295m
  - Annotation: depth label + RMSE improvement percentage per subplot

Invocation:
  python compare_reconstructions_per_ring.py                 # all 39 stations
  python compare_reconstructions_per_ring.py --station TUKU  # single station test
"""

import sys
import argparse
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

# ── Configuration ─────────────────────────────────────────────────────────────
BASE_DIR   = Path(r'D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2')
MLCW_DIR   = BASE_DIR / 'MLCW_5m_regular'
INSAR_FILE = BASE_DIR / 'InSAR_timeries' / 'mlcw_interp_insar_IDW_extend.feather'
DR_DIR     = BASE_DIR / 'direct_ratio_MLCW_InSAR'

MLCW_REF_DATE = datetime(2015, 1, 16)
DEPTH_GRID    = np.arange(0, 300, 5, dtype=float)
N_DEPTHS      = 60
ACTIVE_COLS   = [f'depth_{int(d):03d}m' for d in DEPTH_GRID]

MA_HALF_DAYS      = 182   # ±182 days centred moving average
SEAS_THRESH_SIGMA = 0.5   # mask |x_seas| < k*std

# Figure layout: 5 cols × 4 rows = 20 depths per figure
NCOLS, NROWS = 5, 4
PER_FIG      = NCOLS * NROWS

FIG_SLICES = [
    slice(0,  20),   # depths   0–95 m
    slice(20, 40),   # depths 100–195 m
    slice(40, 60),   # depths 200–295 m
]
FIG_DEPTH_LABELS = ['0–95 m', '100–195 m', '200–295 m']


# ── Utility Functions ─────────────────────────────────────────────────────────
def get_station_list():
    """Discover stations from DR_DIR subdirectories."""
    return sorted([
        p.name for p in DR_DIR.iterdir()
        if p.is_dir() and (p / f'{p.name}_direct_ratio_all.npy').exists()
    ])


def load_insar_feather():
    """Load InSAR feather once."""
    print('Loading InSAR feather ...')
    df        = pd.read_feather(INSAR_FILE)
    date_cols = sorted([c for c in df.columns if c.startswith('D2')])
    dates     = [datetime.strptime(c[1:], '%Y%m%d') for c in date_cols]
    return df, date_cols, dates


def get_insar_lookup(df_insar, date_cols, insar_dates, station):
    """Get per-station InSAR lookup dict."""
    row = df_insar[df_insar['Ename'] == station]
    if row.empty:
        raise ValueError(f'Station {station} not found in InSAR feather')
    vals = row.iloc[0][date_cols].values.astype(float) * 1000.0  # m → mm
    return {
        d.year * 10000 + d.month * 100 + d.day: v
        for d, v in zip(insar_dates, vals)
    }


def load_matched_data(station, insar_lookup, insar_dates):
    """Load MLCW and InSAR, match by date, zero-reference to 2015-01-16."""
    df_mlcw    = pd.read_csv(MLCW_DIR / f'{station}_5m_grid.csv',
                              parse_dates=['datetime'])
    mlcw_dates = pd.to_datetime(df_mlcw['datetime'].values)
    mlcw_yyyymmdd = np.array([
        d.year * 10000 + d.month * 100 + d.day for d in mlcw_dates
    ])
    mlcw_date_idx = {int(v): i for i, v in enumerate(mlcw_yyyymmdd)}

    ref_key = (MLCW_REF_DATE.year * 10000
               + MLCW_REF_DATE.month * 100
               + MLCW_REF_DATE.day)
    ref_row  = mlcw_date_idx.get(ref_key)
    ref_vals = (df_mlcw[ACTIVE_COLS].iloc[ref_row].values.astype(float)
                if ref_row is not None else np.zeros(N_DEPTHS))

    matched_insar, matched_mlcw, matched_dates = [], [], []
    for d in insar_dates:
        key     = d.year * 10000 + d.month * 100 + d.day
        v_insar = insar_lookup.get(key)
        m_idx   = mlcw_date_idx.get(key)
        if v_insar is None or m_idx is None:
            continue
        mlcw_row = df_mlcw[ACTIVE_COLS].iloc[m_idx].values.astype(float) - ref_vals
        if np.isnan(v_insar) or np.any(np.isnan(mlcw_row)):
            continue
        matched_insar.append(v_insar)
        matched_mlcw.append(mlcw_row)
        matched_dates.append(d)

    return (np.array(matched_insar),
            np.array(matched_mlcw),
            np.array(matched_dates))


def _centred_date_ma(vals: np.ndarray, dates: np.ndarray,
                     half_days: int = MA_HALF_DAYS) -> np.ndarray:
    """
    For each epoch i, averages all epochs j where |date_i - date_j| <= half_days.
    Returns NaN for edge epochs where no epochs exist strictly on both sides.
    """
    n      = len(vals)
    result = np.full(n, np.nan)
    dt_ns  = np.array([np.datetime64(d, 'ns') for d in dates])
    half_ns = np.timedelta64(int(half_days * 24 * 3600 * 1e9), 'ns')

    for i in range(n):
        mask        = np.abs(dt_ns - dt_ns[i]) <= half_ns
        window_vals = vals[mask]
        finite      = window_vals[np.isfinite(window_vals)]
        if len(finite) == 0:
            continue
        before = dt_ns[mask] < dt_ns[i]
        after  = dt_ns[mask] > dt_ns[i]
        if before.any() and after.any():
            result[i] = np.mean(finite)
    return result


def compute_rmse_improvement_pct(Y_observed, Y_hat_scalar, Y_hat_new):
    """
    Compute improvement percentage per depth:
    Δ% = (RMSE_scalar - RMSE_new) / RMSE_scalar * 100
    Positive = new method wins; negative = degraded.
    """
    resid_scalar = Y_observed - Y_hat_scalar
    resid_new    = Y_observed - Y_hat_new
    rmse_scalar  = np.sqrt(np.nanmean(resid_scalar ** 2, axis=0))
    rmse_new     = np.sqrt(np.nanmean(resid_new ** 2, axis=0))

    # Avoid division by zero
    improvement_pct = np.full(N_DEPTHS, np.nan)
    valid = rmse_scalar > 1e-6
    improvement_pct[valid] = 100.0 * (rmse_scalar[valid] - rmse_new[valid]) / rmse_scalar[valid]

    return improvement_pct


# ── Harmonic Reconstruction ──────────────────────────────────────────────────
def make_harmonic_figures(station, X_valid, Y_valid, dates_valid, output_dir):
    """
    Create three harmonic per-ring comparison figures.

    Reads: {station}_optionB_trend.csv and {station}_optionB_seas.csv
    Reconstructs: Ŷ_harmonic = f_trend_k * x_trend + f_seas_k * x_seas
    Compares: Y_observed vs scalar baseline vs harmonic reconstruction
    """
    station_dr_dir = DR_DIR / station
    trend_file = station_dr_dir / f'{station}_optionB_trend.csv'
    seas_file  = station_dr_dir / f'{station}_optionB_seas.csv'

    # Check if harmonic files exist
    if not trend_file.exists() or not seas_file.exists():
        print(f"  Harmonic files missing for {station}; skipping harmonic figures.")
        return

    # Load harmonic profiles
    df_trend = pd.read_csv(trend_file)
    df_seas  = pd.read_csv(seas_file)
    f_trend_k = df_trend['f_trend_med'].values
    f_seas_k  = df_seas['f_seas_med'].values

    # Load scalar baseline
    ratio_file = station_dr_dir / f'{station}_direct_ratio_stats.csv'
    df_ratio = pd.read_csv(ratio_file)
    f_scalar_k = df_ratio['f_median'].values

    # Decompose InSAR
    x_trend = _centred_date_ma(X_valid, dates_valid)
    x_seas  = X_valid - x_trend

    # Reconstruct
    Y_hat_scalar = X_valid[:, None] * f_scalar_k[None, :]
    Y_hat_harmonic = (f_trend_k[None, :] * x_trend[:, None] +
                      f_seas_k[None, :] * x_seas[:, None])

    # Compute improvement per depth
    improvement_pct = compute_rmse_improvement_pct(Y_valid, Y_hat_scalar, Y_hat_harmonic)

    # Create figures for each depth range
    for fig_idx, (depth_slice, depth_label) in enumerate(
            zip(FIG_SLICES, FIG_DEPTH_LABELS)):

        fig, axes = plt.subplots(NROWS, NCOLS, figsize=(18, 12), constrained_layout=True)
        fig.suptitle(f'{station} — Harmonic Decomposition per Ring ({depth_label})',
                     fontsize=14, fontweight='bold')
        axes = axes.flatten()

        subplot_idx = 0
        for depth_idx in range(depth_slice.start, depth_slice.stop):
            ax = axes[subplot_idx]
            depth_m = DEPTH_GRID[depth_idx]

            # Plot three lines
            ax.plot(dates_valid, Y_valid[:, depth_idx], 'k-', linewidth=1.5, label='Observed MLCW')
            ax.plot(dates_valid, Y_hat_scalar[:, depth_idx], 'b--', linewidth=1.2, label='Scalar baseline')
            ax.plot(dates_valid, Y_hat_harmonic[:, depth_idx], color='#FF8C00', linewidth=1.2,
                   label='Harmonic recon.')

            # Annotation: depth + RMSE improvement
            improv = improvement_pct[depth_idx]
            improv_txt = f'{improv:+.1f}%' if np.isfinite(improv) else 'NaN'
            text_color = 'green' if (np.isfinite(improv) and improv > 0) else 'red'
            ax.set_title(f'{depth_m:.0f}m  {improv_txt}', fontsize=9, color=text_color, fontweight='bold')

            ax.grid(True, alpha=0.3)
            ax.tick_params(labelsize=7)

            if subplot_idx == 0:
                ax.legend(loc='upper left', fontsize=8)

            subplot_idx += 1

        # Hide unused subplots
        for idx in range(subplot_idx, len(axes)):
            axes[idx].set_visible(False)

        # Save
        out_file = output_dir / f'{station}_harmonic_per_ring_fig{fig_idx+1}.png'
        plt.savefig(out_file, dpi=120, bbox_inches='tight')
        print(f"  Saved: {out_file}")
        plt.close()


# ── Wet/Dry Reconstruction ───────────────────────────────────────────────────
def make_wetdry_figures(station, X_valid, Y_valid, dates_valid, output_dir):
    """
    Create three wet/dry per-ring comparison figures.

    Reads: {station}_wetdry_profiles.csv
    Reconstructs: Ŷ_wetdry = f_split_k(month) * InSAR
    Compares: Y_observed vs scalar baseline vs wet/dry reconstruction
    """
    station_dr_dir = DR_DIR / station
    wetdry_file = station_dr_dir / 'wetdry_diagnostic' / f'{station}_wetdry_profiles.csv'

    # Check if wet/dry file exists
    if not wetdry_file.exists():
        print(f"  Wet/dry file missing for {station}; skipping wet/dry figures.")
        return

    # Load wet/dry profiles
    df_wetdry = pd.read_csv(wetdry_file)
    f_wet_k = df_wetdry['f_wet'].values
    f_dry_k = df_wetdry['f_dry'].values

    # Load scalar baseline
    ratio_file = station_dr_dir / f'{station}_direct_ratio_stats.csv'
    df_ratio = pd.read_csv(ratio_file)
    f_scalar_k = df_ratio['f_median'].values

    # Create month mask: wet = May–Oct (months 5–10)
    months = np.array([d.month for d in dates_valid])
    wet_mask = np.isin(months, [5, 6, 7, 8, 9, 10])

    # Reconstruct
    Y_hat_scalar = X_valid[:, None] * f_scalar_k[None, :]
    f_split = np.where(wet_mask[:, None], f_wet_k[None, :], f_dry_k[None, :])
    Y_hat_wetdry = X_valid[:, None] * f_split

    # Compute improvement per depth
    improvement_pct = compute_rmse_improvement_pct(Y_valid, Y_hat_scalar, Y_hat_wetdry)

    # Create figures for each depth range
    for fig_idx, (depth_slice, depth_label) in enumerate(
            zip(FIG_SLICES, FIG_DEPTH_LABELS)):

        fig, axes = plt.subplots(NROWS, NCOLS, figsize=(18, 12), constrained_layout=True)
        fig.suptitle(f'{station} — Wet/Dry Seasonal Split ({depth_label})',
                     fontsize=14, fontweight='bold')
        axes = axes.flatten()

        subplot_idx = 0
        for depth_idx in range(depth_slice.start, depth_slice.stop):
            ax = axes[subplot_idx]
            depth_m = DEPTH_GRID[depth_idx]

            # Plot three lines
            ax.plot(dates_valid, Y_valid[:, depth_idx], 'k-', linewidth=1.5, label='Observed MLCW')
            ax.plot(dates_valid, Y_hat_scalar[:, depth_idx], 'b--', linewidth=1.2, label='Scalar baseline')
            ax.plot(dates_valid, Y_hat_wetdry[:, depth_idx], color='#20B2AA', linewidth=1.2,
                   label='Wet/dry recon.')

            # Annotation: depth + RMSE improvement
            improv = improvement_pct[depth_idx]
            improv_txt = f'{improv:+.1f}%' if np.isfinite(improv) else 'NaN'
            text_color = 'green' if (np.isfinite(improv) and improv > 0) else 'red'
            ax.set_title(f'{depth_m:.0f}m  {improv_txt}', fontsize=9, color=text_color, fontweight='bold')

            ax.grid(True, alpha=0.3)
            ax.tick_params(labelsize=7)

            if subplot_idx == 0:
                ax.legend(loc='upper left', fontsize=8)

            subplot_idx += 1

        # Hide unused subplots
        for idx in range(subplot_idx, len(axes)):
            axes[idx].set_visible(False)

        # Save
        out_file = output_dir / f'{station}_wetdry_per_ring_fig{fig_idx+1}.png'
        plt.savefig(out_file, dpi=120, bbox_inches='tight')
        print(f"  Saved: {out_file}")
        plt.close()


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description='Per-ring reconstruction comparison figures')
    parser.add_argument('--station', type=str, default=None,
                       help='Single station to process (default: all)')
    args = parser.parse_args()

    # Load InSAR once
    df_insar, date_cols, insar_dates = load_insar_feather()

    # Determine station list
    if args.station:
        stations = [args.station]
    else:
        stations = get_station_list()

    print(f'Processing {len(stations)} station(s)...\n')

    for station in stations:
        print(f'Processing {station}...')

        try:
            # Get station output directory
            station_out_dir = DR_DIR / station
            station_out_dir.mkdir(parents=True, exist_ok=True)

            # Load data
            insar_lookup = get_insar_lookup(df_insar, date_cols, insar_dates, station)
            X_valid, Y_valid, dates_valid = load_matched_data(
                station, insar_lookup, insar_dates)

            if len(X_valid) < 30:
                print(f"  WARNING: Only {len(X_valid)} matched epochs; skipping.\n")
                continue

            # Create harmonic figures
            make_harmonic_figures(station, X_valid, Y_valid, dates_valid, station_out_dir)

            # Create wet/dry figures
            make_wetdry_figures(station, X_valid, Y_valid, dates_valid, station_out_dir)

            print()

        except Exception as e:
            print(f"  ERROR: {e}\n")
            import traceback
            traceback.print_exc()

    print('Done.')


if __name__ == '__main__':
    main()
