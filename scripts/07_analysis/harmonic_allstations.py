"""
Option B Harmonic Decomposition — All 39 Stations
==================================================

Refactored from optionB_harmonic_TUKU.py.

For each station:
  - Decomposes InSAR x(i) and MLCW Y(i,k) into trend (±182-day centred MA)
    and seasonal residual
  - Fits one scalar ratio per depth per component:
        f_trend_k = nanmedian( Y_trend(i,k) / x_trend(i) )
        f_seas_k  = nanmedian( Y_seas(i,k)  / x_seas(i)  )  [near-zero x_seas masked]
  - Reconstructs: Ŷ_harmonic(i,k) = f_trend_k * x_trend(i) + f_seas_k * x_seas(i)
  - Compares against scalar baseline: Ŷ_scalar(i,k) = f̄_k * x(i)
  - Writes extended summary JSON, per-depth CSVs, and three diagnostic plots

Cross-station outputs (after all stations complete):
  harmonic_allstations_summary.csv   — 39 rows × ~40 metric columns
  harmonic_allstations_summary.json
  harmonic_skipped.json              — stations that failed (may be empty)

TUKU verification benchmarks:
  overall_improvement_pct ≈ +0.38%
  n_edge_epochs_excluded  = 2
  n_seas_epochs_masked    = 234
"""

import sys
import json
import traceback
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
from scipy.stats import pearsonr

# Add appgeopy to path (provides evaluate_model_fit — not called here but kept for
# downstream compatibility; the analysis.py in appgeopy is not used in the batch loop)
sys.path.insert(0, r'D:\VENV_PYTHON\appgeopy')

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(r'D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2')
MLCW_DIR   = BASE_DIR / 'MLCW_5m_regular'
INSAR_FILE = BASE_DIR / 'InSAR_timeries' / 'mlcw_interp_insar_IDW_extend.feather'
DR_DIR     = BASE_DIR / 'direct_ratio_MLCW_InSAR'

MLCW_REF_DATE = datetime(2015, 1, 16)
DEPTH_GRID    = np.arange(0, 300, 5, dtype=float)    # 0, 5, …, 295  (60 levels)
N_DEPTHS      = 60
ACTIVE_COLS   = [f'depth_{int(d):03d}m' for d in DEPTH_GRID]

SEAS_THRESH_SIGMA = 0.5   # mask |x_seas| < k * std(x_seas)
MA_HALF_DAYS      = 182   # ±182 days ≈ ±6 months centred window

# Aquifer boundaries
AQUIFER_BOUNDS = [
    ('F1',  19, 103, '#d6eaf8'),
    ('F2',  35, 107, '#d5f5e3'),
    ('F3', 140, 275, '#fdebd0'),
    ('F4', 238, 300, '#fadbd8'),
]


# ── Discover station list from directory names ─────────────────────────────────
def get_station_list():
    return sorted([
        p.name for p in DR_DIR.iterdir()
        if p.is_dir() and (p / f'{p.name}_direct_ratio_all.npy').exists()
    ])


# ── Load InSAR feather once ───────────────────────────────────────────────────
def load_insar_feather():
    print('Loading InSAR feather ...')
    df        = pd.read_feather(INSAR_FILE)
    date_cols = sorted([c for c in df.columns if c.startswith('D2')])
    dates     = [datetime.strptime(c[1:], '%Y%m%d') for c in date_cols]
    return df, date_cols, dates


def get_insar_lookup(df_insar, date_cols, insar_dates, station):
    row = df_insar[df_insar['Ename'] == station]
    if row.empty:
        raise ValueError(f'Station {station} not found in InSAR feather')
    vals = row.iloc[0][date_cols].values.astype(float) * 1000.0   # m → mm
    return {
        d.year * 10000 + d.month * 100 + d.day: v
        for d, v in zip(insar_dates, vals)
    }


# ── Load matched epochs ───────────────────────────────────────────────────────
def load_matched_data(station, insar_lookup, insar_dates):
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


# ── Date-based centred moving average ─────────────────────────────────────────
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


# ── Decomposition ─────────────────────────────────────────────────────────────
def decompose(X_valid, Y_valid, dates_valid):
    x_trend = _centred_date_ma(X_valid, dates_valid)
    x_seas  = X_valid - x_trend

    Y_trend = np.full_like(Y_valid, np.nan)
    for k in range(N_DEPTHS):
        Y_trend[:, k] = _centred_date_ma(Y_valid[:, k], dates_valid)
    Y_seas = Y_valid - Y_trend

    n_edge = int(np.sum(np.isnan(x_trend)))
    return x_trend, x_seas, Y_trend, Y_seas, n_edge


# ── Ratio matrices and profile summaries ─────────────────────────────────────
def compute_ratios(x_trend, x_seas, Y_trend, Y_seas):
    thresh = SEAS_THRESH_SIGMA * np.nanstd(x_seas)

    with np.errstate(divide='ignore', invalid='ignore'):
        R_trend = Y_trend / x_trend[:, None]
        R_seas  = Y_seas  / x_seas[:, None]

    R_trend = np.where(np.isfinite(R_trend), R_trend, np.nan)
    R_seas  = np.where(np.isfinite(R_seas),  R_seas,  np.nan)

    near_zero = np.abs(x_seas) < thresh
    R_seas[near_zero, :] = np.nan
    n_seas_masked = int(np.sum(near_zero))

    def _stats(R):
        return {
            'med': np.nanmedian(R, axis=0),
            'q25': np.nanpercentile(R, 25, axis=0),
            'q75': np.nanpercentile(R, 75, axis=0),
            'p05': np.nanpercentile(R,  5, axis=0),
            'p95': np.nanpercentile(R, 95, axis=0),
            'n':   np.sum(np.isfinite(R), axis=0).astype(int),
            'iqr': np.nanpercentile(R, 75, axis=0) - np.nanpercentile(R, 25, axis=0),
        }

    return _stats(R_trend), _stats(R_seas), thresh, n_seas_masked


# ── Reconstruction and RMSE ───────────────────────────────────────────────────
def reconstruct_and_rmse(station, X_valid, Y_valid, x_trend, x_seas,
                          tr_stats, se_stats):
    stats_csv = DR_DIR / station / f'{station}_direct_ratio_stats.csv'
    f_scalar  = pd.read_csv(stats_csv)['f_median'].values   # (60,)

    Yhat_scalar   = f_scalar[None, :]   * X_valid[:, None]
    Yhat_harmonic = (tr_stats['med'][None, :] * x_trend[:, None]
                   + se_stats['med'][None, :] * x_seas[:, None])

    valid_epochs  = np.isfinite(x_trend) & np.isfinite(x_seas)
    Y_eval        = Y_valid[valid_epochs]
    Yhat_sc_eval  = Yhat_scalar[valid_epochs]
    Yhat_ha_eval  = Yhat_harmonic[valid_epochs]

    rmse_scalar   = np.sqrt(np.nanmean((Y_eval - Yhat_sc_eval)**2, axis=0))
    rmse_harmonic = np.sqrt(np.nanmean((Y_eval - Yhat_ha_eval)**2, axis=0))
    rmse_change   = rmse_scalar - rmse_harmonic   # positive = harmonic better

    overall_scalar   = float(np.nanmedian(rmse_scalar))
    overall_harmonic = float(np.nanmedian(rmse_harmonic))
    overall_improv_pct = (overall_scalar - overall_harmonic) / overall_scalar * 100

    return (f_scalar, rmse_scalar, rmse_harmonic, rmse_change,
            overall_scalar, overall_harmonic, overall_improv_pct,
            valid_epochs, Yhat_harmonic)


# ── Helper: mean RMSE in aquifer depth range ──────────────────────────────────
def mean_rmse_in_range(arr, z_lo, z_hi):
    mask = (DEPTH_GRID >= z_lo) & (DEPTH_GRID <= z_hi)
    return float(np.nanmean(arr[mask]))


# ── Extended metrics ───────────────────────────────────────────────────────────
def compute_extended_metrics(station, X_valid, x_seas, n_edge, n_seas_masked,
                              f_scalar, tr_stats, se_stats,
                              rmse_scalar, rmse_harmonic, rmse_change,
                              overall_scalar, overall_improv_pct,
                              n_valid):
    # Fraction of usable epochs for seasonal component
    n_usable_seas   = n_valid - n_edge - n_seas_masked
    frac_seas_usable = float(max(0.0, n_usable_seas) / max(n_valid, 1))

    # InSAR seasonal std
    x_insar_seas_std_mm = float(np.nanstd(x_seas[np.isfinite(x_seas)]))

    # Depths improved / degraded
    n_depths_improved    = int(np.sum(rmse_change > 0))
    frac_depths_improved = float(n_depths_improved / N_DEPTHS)

    rmse_impr_pct = 100.0 * rmse_change / (rmse_scalar + 1e-9)
    idx_best  = int(np.argmax(rmse_impr_pct))
    idx_worst = int(np.argmin(rmse_impr_pct))

    max_depth_improvement_pct    = float(rmse_impr_pct[idx_best])
    max_depth_improvement_depth_m = float(DEPTH_GRID[idx_best])
    max_depth_degradation_pct    = float(rmse_impr_pct[idx_worst])
    max_depth_degradation_depth_m = float(DEPTH_GRID[idx_worst])

    # Per-aquifer RMSE
    aquifer_rmse = {}
    for name, z_lo, z_hi, _ in AQUIFER_BOUNDS:
        aquifer_rmse[name] = {
            'rmse_baseline': mean_rmse_in_range(rmse_scalar,   z_lo, z_hi),
            'rmse_harmonic': mean_rmse_in_range(rmse_harmonic, z_lo, z_hi),
        }

    # Correlation between f_trend profile and scalar f̄_k
    valid_both = np.isfinite(tr_stats['med']) & np.isfinite(f_scalar)
    if valid_both.sum() > 2:
        corr_ftrend_fscalar, _ = pearsonr(tr_stats['med'][valid_both],
                                           f_scalar[valid_both])
        corr_ftrend_fscalar = float(corr_ftrend_fscalar)
    else:
        corr_ftrend_fscalar = float('nan')

    # Fraction of depths where |f_seas| > 5% of |f_trend|
    with np.errstate(divide='ignore', invalid='ignore'):
        fseas_frac_of_ftrend = np.abs(se_stats['med']) / (np.abs(tr_stats['med']) + 1e-9)
    frac_depths_fseas_gt5pct_of_ftrend = float(
        np.nanmean(fseas_frac_of_ftrend > 0.05))

    # Fraction of depths where seasonal component is "stable" (IQR / |median| < 1)
    with np.errstate(divide='ignore', invalid='ignore'):
        fseas_cv = se_stats['iqr'] / (np.abs(se_stats['med']) + 1e-9)
    fseas_stable = np.isfinite(fseas_cv) & (fseas_cv < 1.0)
    frac_fseas_stable = float(np.nanmean(fseas_stable))

    # Deepest depth where f_seas is considered stable
    stable_depths = DEPTH_GRID[fseas_stable]
    f_seas_reliable_depth_max_m = float(stable_depths.max()) if len(stable_depths) > 0 else float('nan')

    # Recommendation flags
    harmonic_recommended     = bool(overall_improv_pct > 2.0 and frac_depths_improved > 0.5)
    insufficient_seasonal_sample = bool(frac_seas_usable < 0.3)

    return {
        'frac_seas_usable':                    frac_seas_usable,
        'x_insar_seas_std_mm':                 x_insar_seas_std_mm,
        'n_depths_improved':                   n_depths_improved,
        'frac_depths_improved':                frac_depths_improved,
        'max_depth_improvement_pct':           max_depth_improvement_pct,
        'max_depth_improvement_depth_m':       max_depth_improvement_depth_m,
        'max_depth_degradation_pct':           max_depth_degradation_pct,
        'max_depth_degradation_depth_m':       max_depth_degradation_depth_m,
        'F1_rmse_baseline': aquifer_rmse['F1']['rmse_baseline'],
        'F1_rmse_harmonic': aquifer_rmse['F1']['rmse_harmonic'],
        'F2_rmse_baseline': aquifer_rmse['F2']['rmse_baseline'],
        'F2_rmse_harmonic': aquifer_rmse['F2']['rmse_harmonic'],
        'F3_rmse_baseline': aquifer_rmse['F3']['rmse_baseline'],
        'F3_rmse_harmonic': aquifer_rmse['F3']['rmse_harmonic'],
        'F4_rmse_baseline': aquifer_rmse['F4']['rmse_baseline'],
        'F4_rmse_harmonic': aquifer_rmse['F4']['rmse_harmonic'],
        'corr_ftrend_fscalar':                 corr_ftrend_fscalar,
        'frac_depths_fseas_gt5pct_of_ftrend':  frac_depths_fseas_gt5pct_of_ftrend,
        'frac_fseas_stable':                   frac_fseas_stable,
        'f_seas_reliable_depth_max_m':         f_seas_reliable_depth_max_m,
        'harmonic_recommended':                harmonic_recommended,
        'insufficient_seasonal_sample':        insufficient_seasonal_sample,
    }


# ── Save outputs ──────────────────────────────────────────────────────────────
def save_outputs(station, out_dir, tr_stats, se_stats,
                 rmse_scalar, rmse_harmonic, rmse_change,
                 overall_scalar, overall_harmonic, overall_improv_pct,
                 n_seas_masked, n_edge, ext_metrics, n_valid):

    pd.DataFrame({
        'depth_m':      DEPTH_GRID,
        'f_trend_med':  tr_stats['med'],
        'f_trend_q25':  tr_stats['q25'],
        'f_trend_q75':  tr_stats['q75'],
        'f_trend_p05':  tr_stats['p05'],
        'f_trend_p95':  tr_stats['p95'],
        'n_trend':      tr_stats['n'],
    }).to_csv(out_dir / f'{station}_optionB_trend.csv', index=False)

    pd.DataFrame({
        'depth_m':     DEPTH_GRID,
        'f_seas_med':  se_stats['med'],
        'f_seas_q25':  se_stats['q25'],
        'f_seas_q75':  se_stats['q75'],
        'f_seas_p05':  se_stats['p05'],
        'f_seas_p95':  se_stats['p95'],
        'n_seas':      se_stats['n'],
    }).to_csv(out_dir / f'{station}_optionB_seas.csv', index=False)

    rmse_change_pct = 100.0 * rmse_change / (rmse_scalar + 1e-9)
    pd.DataFrame({
        'depth_m':          DEPTH_GRID,
        'rmse_scalar_mm':   rmse_scalar,
        'rmse_harmonic_mm': rmse_harmonic,
        'rmse_change_mm':   rmse_change,
        'rmse_change_pct':  rmse_change_pct,
    }).to_csv(out_dir / f'{station}_optionB_rmse.csv', index=False)

    summary = {
        'station':                    station,
        'n_valid_epochs':             int(n_valid),
        'overall_rmse_scalar_mm':     overall_scalar,
        'overall_rmse_harmonic_mm':   overall_harmonic,
        'overall_improvement_mm':     overall_scalar - overall_harmonic,
        'overall_improvement_pct':    overall_improv_pct,
        'n_edge_epochs_excluded':     n_edge,
        'n_seas_epochs_masked':       n_seas_masked,
        'seas_threshold_sigma':       SEAS_THRESH_SIGMA,
        'ma_half_days':               MA_HALF_DAYS,
    }
    summary.update(ext_metrics)

    with open(out_dir / f'{station}_optionB_summary.json', 'w', encoding='utf-8') as fh:
        json.dump(summary, fh, indent=2)

    return summary


# ── Plots ──────────────────────────────────────────────────────────────────────
def _shade_aquifers(ax):
    for label, top, bot, color in AQUIFER_BOUNDS:
        ax.axhspan(top, bot, color=color, alpha=0.20, zorder=0)
        ax.text(-0.03, (top + bot) / 2, label,
                transform=ax.get_yaxis_transform(),
                fontsize=7, ha='right', va='center', color='grey')


def plot_depth_profiles(station, out_dir, tr_stats, se_stats, f_scalar):
    fig, axes = plt.subplots(1, 2, figsize=(12, 10), sharey=True)

    for ax, stats, title, color in [
        (axes[0], tr_stats, 'Trend component  $f_{\\mathrm{trend},k}$', 'steelblue'),
        (axes[1], se_stats, 'Seasonal component  $f_{\\mathrm{seas},k}$', 'darkorange'),
    ]:
        _shade_aquifers(ax)
        ax.fill_betweenx(DEPTH_GRID, stats['p05'], stats['p95'],
                         color=color, alpha=0.12, label='5–95th pct')
        ax.fill_betweenx(DEPTH_GRID, stats['q25'], stats['q75'],
                         color=color, alpha=0.30, label='IQR')
        ax.plot(stats['med'], DEPTH_GRID, color=color, lw=2, label='Median')
        ax.plot(f_scalar, DEPTH_GRID, color='grey', lw=1.2,
                ls='--', label='Scalar $\\bar{f}_k$ (reference)')
        ax.axvline(0, color='k', lw=0.6, ls=':')
        ax.set_xlabel('Fraction of InSAR signal', fontsize=11)
        ax.set_title(title, fontsize=11)
        ax.invert_yaxis()
        ax.set_ylim(295, 0)
        ax.legend(fontsize=8, loc='lower right')
        ax.grid(True, alpha=0.3)

    axes[0].set_ylabel('Depth (m)', fontsize=11)
    fig.suptitle(f'{station} — Option B harmonic decomposition\n'
                 f'Centred MA ±{MA_HALF_DAYS} days, x_seas threshold = {SEAS_THRESH_SIGMA}σ',
                 fontsize=12)
    fig.tight_layout()
    fig.savefig(out_dir / f'{station}_optionB_profiles.png', dpi=150, bbox_inches='tight')
    plt.close(fig)


def plot_rmse_improvement(station, out_dir, rmse_scalar, rmse_harmonic, rmse_change):
    fig, axes = plt.subplots(1, 2, figsize=(13, 9), sharey=True)

    ax = axes[0]
    _shade_aquifers(ax)
    ax.barh(DEPTH_GRID, rmse_scalar,   height=4, color='grey',      alpha=0.6, label='Scalar RMSE')
    ax.barh(DEPTH_GRID, rmse_harmonic, height=4, color='steelblue', alpha=0.7, label='Harmonic RMSE')
    ax.set_xlabel('RMSE (mm)', fontsize=11)
    ax.set_title('RMSE by depth', fontsize=11)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    _shade_aquifers(ax)
    colors = ['steelblue' if v >= 0 else 'tomato' for v in rmse_change]
    ax.barh(DEPTH_GRID, rmse_change, height=4, color=colors, alpha=0.8)
    ax.axvline(0, color='k', lw=0.8, ls='--')
    ax.set_xlabel('RMSE improvement (mm)\n(positive = harmonic better)', fontsize=11)
    ax.set_title('RMSE change: scalar − harmonic', fontsize=11)
    ax.grid(True, alpha=0.3)

    for ax in axes:
        ax.invert_yaxis()
        ax.set_ylim(295, 0)
    axes[0].set_ylabel('Depth (m)', fontsize=11)

    fig.suptitle(f'{station} — Option B RMSE comparison', fontsize=12)
    fig.tight_layout()
    fig.savefig(out_dir / f'{station}_optionB_rmse_plot.png', dpi=150, bbox_inches='tight')
    plt.close(fig)


def plot_residual_heatmap(station, out_dir, Y_valid, x_trend, x_seas,
                           tr_stats, se_stats, dates_valid, valid_epochs):
    Yhat_harmonic = (tr_stats['med'][None, :] * x_trend[:, None]
                   + se_stats['med'][None, :] * x_seas[:, None])
    residual = Y_valid - Yhat_harmonic

    resid_plot = residual[valid_epochs]
    dates_plot = dates_valid[valid_epochs]
    n_plot     = resid_plot.shape[0]

    abs_vals = np.abs(resid_plot[np.isfinite(resid_plot)])
    vmax     = float(np.percentile(abs_vals, 98)) if len(abs_vals) > 0 else 1.0

    fig, ax = plt.subplots(figsize=(14, 6))
    depth_edges = np.append(DEPTH_GRID - 2.5, DEPTH_GRID[-1] + 2.5)
    epoch_edges = np.arange(n_plot + 1)

    pcm = ax.pcolormesh(depth_edges, epoch_edges, resid_plot,
                        cmap='RdBu_r', vmin=-vmax, vmax=vmax, shading='flat')

    year_ticks, year_labels, current_year = [], [], None
    for idx, d in enumerate(dates_plot):
        yr = d.year
        if yr != current_year:
            year_ticks.append(idx)
            year_labels.append(str(yr))
            current_year = yr

    ax.set_yticks(year_ticks)
    ax.set_yticklabels(year_labels, fontsize=8)
    ax.set_xlabel('Depth (m)', fontsize=11)
    ax.set_ylabel('Epoch (year)', fontsize=11)
    ax.set_title(f'{station} — Harmonic residual heatmap  Y − Ŷ_harmonic\n'
                 f'Colour clipped to ±{vmax:.3f} mm  (98th pct of |residual|)', fontsize=11)

    cbar = fig.colorbar(pcm, ax=ax, shrink=0.85, pad=0.01)
    cbar.set_label('Residual (mm)', fontsize=9)

    fig.tight_layout()
    fig.savefig(out_dir / f'{station}_optionB_residual_heatmap.png',
                dpi=150, bbox_inches='tight')
    plt.close(fig)


# ── Core harmonic diagnostic for one station ──────────────────────────────────
def run_harmonic(station, insar_lookup, insar_dates):
    out_dir = DR_DIR / station
    out_dir.mkdir(parents=True, exist_ok=True)

    X_valid, Y_valid, dates_valid = load_matched_data(station, insar_lookup, insar_dates)
    n_valid = len(X_valid)
    if n_valid < 30:
        raise ValueError(f'Too few matched epochs ({n_valid}) for {station}')

    print(f'  Decomposing ({n_valid} epochs) ...')
    x_trend, x_seas, Y_trend, Y_seas, n_edge = decompose(X_valid, Y_valid, dates_valid)

    tr_stats, se_stats, thresh, n_seas_masked = compute_ratios(
        x_trend, x_seas, Y_trend, Y_seas)

    (f_scalar, rmse_scalar, rmse_harmonic, rmse_change,
     overall_scalar, overall_harmonic, overall_improv_pct,
     valid_epochs, Yhat_harmonic) = reconstruct_and_rmse(
        station, X_valid, Y_valid, x_trend, x_seas, tr_stats, se_stats)

    ext = compute_extended_metrics(
        station, X_valid, x_seas, n_edge, n_seas_masked,
        f_scalar, tr_stats, se_stats,
        rmse_scalar, rmse_harmonic, rmse_change,
        overall_scalar, overall_improv_pct, n_valid)

    summary = save_outputs(
        station, out_dir, tr_stats, se_stats,
        rmse_scalar, rmse_harmonic, rmse_change,
        overall_scalar, overall_harmonic, overall_improv_pct,
        n_seas_masked, n_edge, ext, n_valid)

    plot_depth_profiles(station, out_dir, tr_stats, se_stats, f_scalar)
    plot_rmse_improvement(station, out_dir, rmse_scalar, rmse_harmonic, rmse_change)
    plot_residual_heatmap(station, out_dir, Y_valid, x_trend, x_seas,
                          tr_stats, se_stats, dates_valid, valid_epochs)

    return summary


# ── Main batch loop ───────────────────────────────────────────────────────────
def main():
    stations = get_station_list()
    print(f'Found {len(stations)} stations: {stations}')

    df_insar, date_cols, insar_dates = load_insar_feather()

    all_summaries = []
    skipped       = []

    for i, station in enumerate(stations, 1):
        print(f'\n[{i:02d}/{len(stations)}] {station}')
        try:
            insar_lookup = get_insar_lookup(df_insar, date_cols, insar_dates, station)
            summary      = run_harmonic(station, insar_lookup, insar_dates)
            all_summaries.append(summary)
            print(f'  OK — RMSE improvement: {summary["overall_improvement_pct"]:+.2f}%  '
                  f'harmonic_recommended={summary["harmonic_recommended"]}  '
                  f'insufficient_seasonal_sample={summary["insufficient_seasonal_sample"]}')
        except Exception as exc:
            print(f'  SKIPPED: {exc}')
            skipped.append({'station': station, 'reason': str(exc),
                            'traceback': traceback.format_exc()})

    # -- Cross-station summary CSV (flatten nested dicts to flat columns)
    flat_rows = []
    for s in all_summaries:
        flat_rows.append({k: v for k, v in s.items()})

    df_summary = pd.DataFrame(flat_rows)
    df_summary.to_csv(DR_DIR / 'harmonic_allstations_summary.csv',
                      index=False, float_format='%.6f')
    with open(DR_DIR / 'harmonic_allstations_summary.json', 'w', encoding='utf-8') as fh:
        json.dump(all_summaries, fh, indent=2)
    with open(DR_DIR / 'harmonic_skipped.json', 'w', encoding='utf-8') as fh:
        json.dump(skipped, fh, indent=2)

    print(f'\n{"="*60}')
    print(f'  HARMONIC BATCH COMPLETE')
    print(f'  Processed: {len(all_summaries)}  |  Skipped: {len(skipped)}')
    if all_summaries:
        rec  = [s['station'] for s in all_summaries if s['harmonic_recommended']]
        insuf = [s['station'] for s in all_summaries if s['insufficient_seasonal_sample']]
        print(f'  harmonic_recommended=True : {rec  if rec   else "none"}')
        print(f'  insufficient_seasonal_sample=True: {insuf if insuf else "none"}')
    print(f'  Output: {DR_DIR}')
    print('='*60)


if __name__ == '__main__':
    main()
