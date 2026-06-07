"""
Batch In-Sample Validation — All 39 MLCW Stations
Ŷ(i, k) = f̄_k × x(i)   residual = Y − Ŷ

Per-station outputs → direct_ratio_MLCW_InSAR/{STATION}/validation/
    {STATION}_ts_fig1.png   depths   0–95 m  (20 subplots: MLCW vs Ŷ time series)
    {STATION}_ts_fig2.png   depths 100–195 m
    {STATION}_ts_fig3.png   depths 200–295 m
    {STATION}_sc_fig1.png   scatter  0–95 m
    {STATION}_sc_fig2.png   scatter 100–195 m
    {STATION}_sc_fig3.png   scatter 200–295 m
    {STATION}_validation_rmse_profile.png
    {STATION}_validation_residual_heatmap.png
    {STATION}_validation_total_timeseries.png
    {STATION}_validation_coverage.png
    {STATION}_validation_stats.csv
    {STATION}_validation_report.json

Cross-station summary → direct_ratio_MLCW_InSAR/
    all_stations_validation_summary.csv
    all_stations_validation_summary.json
"""

import json
import time
import logging
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
from scipy.ndimage import uniform_filter1d

logging.basicConfig(level=logging.INFO,
                    format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────
BASE_DIR      = Path(r'D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2')
MLCW_DIR      = BASE_DIR / 'MLCW_5m_regular'
INSAR_FILE    = BASE_DIR / 'InSAR_timeries' / 'mlcw_interp_insar_IDW_extend.feather'
RATIO_ROOT    = BASE_DIR / 'direct_ratio_MLCW_InSAR'
MLCW_REF_DATE = datetime(2015, 1, 16)

DEPTH_GRID  = np.arange(0, 300, 5, dtype=float)   # [0, 5, …, 295]
N_DEPTHS    = 60
DEPTH_COLS  = [f'depth_{int(d):03d}m' for d in DEPTH_GRID]

# Layout: 5 cols × 4 rows = 20 depths per figure → 3 figures cover all 60 depths
NCOLS, NROWS = 5, 4
PER_FIG      = NCOLS * NROWS   # 20

# Depth slices for the three figures
FIG_SLICES = [
    slice(0,  20),   # depths   0–95 m
    slice(20, 40),   # depths 100–195 m
    slice(40, 60),   # depths 200–295 m
]
FIG_DEPTH_LABELS = ['0–95 m', '100–195 m', '200–295 m']


# ── Utility: year-boundary tick positions ──────────────────────────────────────
def year_ticks(dates):
    ticks, labels, cur = [], [], None
    for idx, d in enumerate(dates):
        yr = d.year
        if yr != cur:
            ticks.append(idx)
            labels.append(str(yr))
            cur = yr
    return ticks, labels


# ── Utility: safe scalar cast (handles NaN) ────────────────────────────────────
def _f(v):
    """Return float or None, never NaN-in-JSON."""
    v = float(v)
    return None if (v != v) else round(v, 6)


# ══════════════════════════════════════════════════════════════════════════════
# Seasonal misfit metrics
# ══════════════════════════════════════════════════════════════════════════════

def compute_seasonal_metrics(resid, Y_valid, Y_hat, dates_valid):
    """
    Compute per-depth seasonal misfit metrics.

    M1  — annual + semi-annual harmonic amplitude in residual (Y − Ŷ)
    M2a — detrended correlation after removing 3rd-order polynomial trend
    M2b — detrended correlation after removing 1-year moving-average trend
    M3  — fraction of residual variance explained by annual harmonic
    M4  — residual autocorrelation at 1-year lag
    M5  — ratio of MLCW annual swing to Ŷ annual swing

    Returns dict of shape-(N_DEPTHS,) arrays.
    Uses only numpy + scipy.ndimage (already imported).
    """
    t_days = np.array([(d - dates_valid[0]).days for d in dates_valid], dtype=float)
    n, K   = resid.shape

    # Harmonic design matrix: annual + semi-annual + constant  (n, 5)
    omega = 2.0 * np.pi / 365.25
    H_mat = np.column_stack([
        np.cos(omega * t_days),
        np.sin(omega * t_days),
        np.cos(2.0 * omega * t_days),
        np.sin(2.0 * omega * t_days),
        np.ones(n),
    ])

    # Polynomial trend design matrix (3rd-order, normalised)  (n, 4)
    t_norm = (t_days - t_days.mean()) / (t_days.std() + 1e-9)
    P_mat  = np.column_stack([np.ones(n), t_norm, t_norm**2, t_norm**3])

    # Moving-average window: one year worth of epochs
    dt_median = float(np.median(np.diff(t_days))) if n > 1 else 5.0
    ma_win    = max(3, int(round(365.25 / dt_median)))
    if ma_win % 2 == 0:
        ma_win += 1   # keep it odd for symmetry

    keys = [
        'seasonal_amp_ann_mm', 'seasonal_amp_semi_mm',
        'seasonal_phase_ann_days', 'seasonal_R2_resid',
        'seasonal_var_frac',
        'r_detrended_poly', 'r_detrended_ma',
        'ac1yr', 'seasonal_amp_ratio',
    ]
    out = {k: np.full(K, np.nan) for k in keys}

    for k in range(K):
        r  = resid[:, k]
        y  = Y_valid[:, k]
        yh = Y_hat[:, k]

        # ── M1: harmonic fit to residual ──────────────────────────────────────
        coef, _, _, _ = np.linalg.lstsq(H_mat, r, rcond=None)
        r_fit    = H_mat @ coef
        ss_fit   = float(np.sum(r_fit ** 2))
        ss_resid = float(np.sum(r ** 2))

        amp_ann  = float(np.sqrt(coef[0]**2 + coef[1]**2))
        amp_semi = float(np.sqrt(coef[2]**2 + coef[3]**2))
        # Phase: day-of-year at which annual component peaks
        phase_rad = np.arctan2(coef[1], coef[0])
        phase_day = float((-np.degrees(phase_rad) / 360.0 * 365.25) % 365.25)

        r2_harm = 1.0 - float(np.sum((r - r_fit)**2)) / (ss_resid + 1e-30)

        out['seasonal_amp_ann_mm'][k]     = amp_ann
        out['seasonal_amp_semi_mm'][k]    = amp_semi
        out['seasonal_phase_ann_days'][k] = phase_day
        out['seasonal_R2_resid'][k]       = float(np.clip(r2_harm, -5.0, 1.0))

        # ── M3: seasonal variance fraction ────────────────────────────────────
        out['seasonal_var_frac'][k] = float(ss_fit / (ss_resid + 1e-30))

        # ── M2a: polynomial-detrended correlation ─────────────────────────────
        cy,  _, _, _ = np.linalg.lstsq(P_mat, y,  rcond=None)
        cyh, _, _, _ = np.linalg.lstsq(P_mat, yh, rcond=None)
        y_dt_p  = y  - P_mat @ cy
        yh_dt_p = yh - P_mat @ cyh
        if y_dt_p.std() > 1e-9 and yh_dt_p.std() > 1e-9:
            out['r_detrended_poly'][k] = float(np.corrcoef(y_dt_p, yh_dt_p)[0, 1])

        # ── M2b: moving-average-detrended correlation ─────────────────────────
        y_ma  = uniform_filter1d(y,  size=ma_win, mode='nearest')
        yh_ma = uniform_filter1d(yh, size=ma_win, mode='nearest')
        y_dt_m  = y  - y_ma
        yh_dt_m = yh - yh_ma
        if y_dt_m.std() > 1e-9 and yh_dt_m.std() > 1e-9:
            out['r_detrended_ma'][k] = float(np.corrcoef(y_dt_m, yh_dt_m)[0, 1])

        # ── M4: autocorrelation at 1-year lag ─────────────────────────────────
        target   = t_days + 365.25
        lag_idx  = np.searchsorted(t_days, target).clip(0, n - 1)
        # Only keep pairs where the matched epoch is within 10 days of target
        close    = np.abs(t_days[lag_idx] - target) < 10.0
        r0 = r[close]
        r1 = r[lag_idx[close]]
        if len(r0) > 20 and r0.std() > 1e-9 and r1.std() > 1e-9:
            out['ac1yr'][k] = float(np.corrcoef(r0, r1)[0, 1])

        # ── M5: seasonal amplitude ratio Y / Ŷ ───────────────────────────────
        cy2,  _, _, _ = np.linalg.lstsq(H_mat, y,  rcond=None)
        cyh2, _, _, _ = np.linalg.lstsq(H_mat, yh, rcond=None)
        amp_y  = float(np.sqrt(cy2[0]**2  + cy2[1]**2))
        amp_yh = float(np.sqrt(cyh2[0]**2 + cyh2[1]**2))
        if amp_yh > 1e-6:
            out['seasonal_amp_ratio'][k] = amp_y / amp_yh

    return out


# ══════════════════════════════════════════════════════════════════════════════
# Core per-station validation
# ══════════════════════════════════════════════════════════════════════════════

def validate_station(station, insar_lookup, insar_dates, df_insar_row):
    """
    Run full validation for one station.
    Returns a summary dict (for cross-station report) or None if skipped.
    """
    ratio_dir = RATIO_ROOT / station
    stats_csv = ratio_dir / f'{station}_direct_ratio_stats.csv'
    if not stats_csv.exists():
        logger.warning(f'[{station}] No stats CSV — skipping')
        return None

    out_dir = ratio_dir / 'validation'
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Load ratio stats ───────────────────────────────────────────────────────
    stats_df = pd.read_csv(stats_csv)
    f_median = stats_df['f_median'].values   # (60,)
    f_p05    = stats_df['f_p05'].values
    f_p95    = stats_df['f_p95'].values

    # ── Load MLCW ─────────────────────────────────────────────────────────────
    mlcw_file = MLCW_DIR / f'{station}_5m_grid.csv'
    if not mlcw_file.exists():
        logger.warning(f'[{station}] No MLCW file — skipping')
        return None

    df_mlcw       = pd.read_csv(mlcw_file, parse_dates=['datetime'])
    mlcw_dates    = pd.to_datetime(df_mlcw['datetime'].values)
    mlcw_yyyymmdd = np.array([
        d.year * 10000 + d.month * 100 + d.day for d in mlcw_dates
    ])
    mlcw_date_idx = {v: i for i, v in enumerate(mlcw_yyyymmdd)}

    ref_key  = (MLCW_REF_DATE.year * 10000
                + MLCW_REF_DATE.month * 100
                + MLCW_REF_DATE.day)
    ref_row  = mlcw_date_idx.get(ref_key)
    ref_vals = (df_mlcw[DEPTH_COLS].iloc[ref_row].values.astype(float)
                if ref_row is not None else np.zeros(N_DEPTHS))

    # ── Date alignment ─────────────────────────────────────────────────────────
    matched_insar, matched_mlcw, matched_dates = [], [], []
    for d in insar_dates:
        key     = d.year * 10000 + d.month * 100 + d.day
        v_insar = insar_lookup.get(key)
        m_idx   = mlcw_date_idx.get(key)
        if v_insar is None or m_idx is None:
            continue
        mlcw_row = df_mlcw[DEPTH_COLS].iloc[m_idx].values.astype(float) - ref_vals
        if np.isnan(v_insar) or np.any(np.isnan(mlcw_row)):
            continue
        matched_insar.append(v_insar)
        matched_mlcw.append(mlcw_row)
        matched_dates.append(d)

    n_valid = len(matched_insar)
    if n_valid == 0:
        logger.error(f'[{station}] Zero matched epochs — skipping')
        return None

    X_valid     = np.array(matched_insar)    # (n,)
    Y_valid     = np.array(matched_mlcw)     # (n, 60)
    dates_valid = np.array(matched_dates)

    # ── Prediction and residuals ───────────────────────────────────────────────
    Y_hat = f_median[None, :] * X_valid[:, None]   # (n, 60)
    resid = Y_valid - Y_hat

    # Per-depth statistics
    rmse_per_depth = np.sqrt(np.mean(resid ** 2, axis=0))
    bias_per_depth = np.mean(resid, axis=0)
    ss_res         = np.sum(resid ** 2, axis=0)
    ss_tot         = np.sum((Y_valid - Y_valid.mean(axis=0)) ** 2, axis=0)
    r2_per_depth   = np.where(ss_tot > 0, 1.0 - ss_res / ss_tot, np.nan)

    # Band coverage (sign-aware)
    Y_band_lo = np.where(X_valid[:, None] >= 0,
                         f_p05[None, :] * X_valid[:, None],
                         f_p95[None, :] * X_valid[:, None])
    Y_band_hi = np.where(X_valid[:, None] >= 0,
                         f_p95[None, :] * X_valid[:, None],
                         f_p05[None, :] * X_valid[:, None])
    coverage = np.mean((Y_valid >= Y_band_lo) & (Y_valid <= Y_band_hi), axis=0)

    # Total column
    Y_total       = Y_valid.sum(axis=1)
    Y_hat_total   = Y_hat.sum(axis=1)
    band_lo_total = Y_band_lo.sum(axis=1)
    band_hi_total = Y_band_hi.sum(axis=1)

    # ── Seasonal misfit metrics ────────────────────────────────────────────────
    seas = compute_seasonal_metrics(resid, Y_valid, Y_hat, dates_valid)

    # ── Save per-depth CSV ─────────────────────────────────────────────────────
    df_val = pd.DataFrame({
        'depth_m':                  DEPTH_GRID,
        'rmse_mm':                  rmse_per_depth,
        'bias_mm':                  bias_per_depth,
        'r2':                       r2_per_depth,
        'coverage_p05_p95':         coverage,
        'n_epochs':                 n_valid,
        'seasonal_amp_ann_mm':      seas['seasonal_amp_ann_mm'],
        'seasonal_amp_semi_mm':     seas['seasonal_amp_semi_mm'],
        'seasonal_phase_ann_days':  seas['seasonal_phase_ann_days'],
        'seasonal_R2_resid':        seas['seasonal_R2_resid'],
        'seasonal_var_frac':        seas['seasonal_var_frac'],
        'r_detrended_poly':         seas['r_detrended_poly'],
        'r_detrended_ma':           seas['r_detrended_ma'],
        'ac1yr':                    seas['ac1yr'],
        'seasonal_amp_ratio':       seas['seasonal_amp_ratio'],
    })
    df_val.to_csv(out_dir / f'{station}_validation_stats.csv', index=False)

    # ── Summary scalars ────────────────────────────────────────────────────────
    mean_rmse     = float(np.mean(rmse_per_depth))
    mean_abs_bias = float(np.mean(np.abs(bias_per_depth)))
    mean_r2       = float(np.nanmean(r2_per_depth))
    mean_coverage = float(np.mean(coverage))
    worst_rmse_depth = float(DEPTH_GRID[np.argmax(rmse_per_depth)])
    best_r2_depth    = float(DEPTH_GRID[np.nanargmax(r2_per_depth)])
    frac_r2_pos      = float(np.nanmean(r2_per_depth > 0))
    frac_r2_08       = float(np.nanmean(r2_per_depth > 0.8))

    # Total-column RMSE and R²
    resid_total     = Y_total - Y_hat_total
    rmse_total      = float(np.sqrt(np.mean(resid_total ** 2)))
    ss_res_tot      = float(np.sum(resid_total ** 2))
    ss_tot_tot      = float(np.sum((Y_total - Y_total.mean()) ** 2))
    r2_total        = (1.0 - ss_res_tot / ss_tot_tot) if ss_tot_tot > 0 else float('nan')
    bias_total      = float(np.mean(resid_total))

    # ── Save per-depth JSON report ─────────────────────────────────────────────
    report = {
        'station':          station,
        'n_valid_epochs':   n_valid,
        'summary': {
            'mean_rmse_mm':        _f(mean_rmse),
            'mean_abs_bias_mm':    _f(mean_abs_bias),
            'mean_r2':             _f(mean_r2),
            'mean_coverage':       _f(mean_coverage),
            'frac_depths_r2_pos':  _f(frac_r2_pos),
            'frac_depths_r2_gt08': _f(frac_r2_08),
            'worst_rmse_depth_m':  _f(worst_rmse_depth),
            'best_r2_depth_m':     _f(best_r2_depth),
        },
        'total_column': {
            'rmse_mm':    _f(rmse_total),
            'bias_mm':    _f(bias_total),
            'r2':         _f(r2_total),
            'coverage':   _f(float(np.mean(
                (Y_total >= band_lo_total) & (Y_total <= band_hi_total)
            ))),
        },
        'per_depth': [
            {
                'depth_m':                  float(DEPTH_GRID[k]),
                'rmse_mm':                  _f(rmse_per_depth[k]),
                'bias_mm':                  _f(bias_per_depth[k]),
                'r2':                       _f(r2_per_depth[k]),
                'coverage_p05_p95':         _f(coverage[k]),
                'seasonal_amp_ann_mm':      _f(seas['seasonal_amp_ann_mm'][k]),
                'seasonal_amp_semi_mm':     _f(seas['seasonal_amp_semi_mm'][k]),
                'seasonal_phase_ann_days':  _f(seas['seasonal_phase_ann_days'][k]),
                'seasonal_R2_resid':        _f(seas['seasonal_R2_resid'][k]),
                'seasonal_var_frac':        _f(seas['seasonal_var_frac'][k]),
                'r_detrended_poly':         _f(seas['r_detrended_poly'][k]),
                'r_detrended_ma':           _f(seas['r_detrended_ma'][k]),
                'ac1yr':                    _f(seas['ac1yr'][k]),
                'seasonal_amp_ratio':       _f(seas['seasonal_amp_ratio'][k]),
            }
            for k in range(N_DEPTHS)
        ],
        'seasonal_metrics': {
            'summary': {
                'mean_seasonal_amp_ann_mm':   _f(float(np.nanmean(seas['seasonal_amp_ann_mm']))),
                'median_seasonal_amp_ratio':  _f(float(np.nanmedian(seas['seasonal_amp_ratio']))),
                'mean_r_detrended_poly':      _f(float(np.nanmean(seas['r_detrended_poly']))),
                'mean_r_detrended_ma':        _f(float(np.nanmean(seas['r_detrended_ma']))),
                'frac_depths_seasonal_dom':   _f(float(np.nanmean(seas['seasonal_var_frac'] > 0.3))),
                'mean_ac1yr':                 _f(float(np.nanmean(seas['ac1yr']))),
            },
        },
    }
    with open(out_dir / f'{station}_validation_report.json', 'w') as fh:
        json.dump(report, fh, indent=2)

    # ══════════════════════════════════════════════════════════════════════════
    # Figures A: Time series (3 figures, 20 subplots each)
    # ══════════════════════════════════════════════════════════════════════════
    date_axis = list(dates_valid)   # list of datetime for matplotlib

    for fig_idx, (sl, depth_label) in enumerate(zip(FIG_SLICES, FIG_DEPTH_LABELS), 1):
        depths_in_fig = DEPTH_GRID[sl]
        n_sub = len(depths_in_fig)
        n_rows_used = int(np.ceil(n_sub / NCOLS))

        fig, axes = plt.subplots(n_rows_used, NCOLS,
                                 figsize=(NCOLS * 3.5, n_rows_used * 2.8),
                                 squeeze=False)
        fig.suptitle(
            f'{station} — InSAR-derived vs. observed MLCW compaction\n'
            f'Depths {depth_label}  (n = {n_valid} epochs)',
            fontsize=11, fontweight='bold'
        )

        for sub_idx, depth in enumerate(depths_in_fig):
            k   = int(depth / 5)
            row = sub_idx // NCOLS
            col = sub_idx % NCOLS
            ax  = axes[row][col]

            y_obs  = Y_valid[:, k]
            y_pred = Y_hat[:, k]
            lo     = Y_band_lo[:, k]
            hi     = Y_band_hi[:, k]

            ax.fill_between(date_axis, lo, hi,
                            color='steelblue', alpha=0.18, linewidth=0)
            ax.plot(date_axis, y_obs,  color='black',      lw=0.9,
                    label='MLCW')
            ax.plot(date_axis, y_pred, color='steelblue',  lw=0.9,
                    linestyle='--', label='Ŷ')

            ax.set_title(f'{int(depth)} m  R²={r2_per_depth[k]:.2f}',
                         fontsize=8, pad=2)
            ax.tick_params(labelsize=6)
            ax.xaxis.set_major_locator(
                matplotlib.dates.YearLocator(2)
            )
            ax.xaxis.set_major_formatter(
                matplotlib.dates.DateFormatter('%Y')
            )
            ax.grid(True, alpha=0.25)

            if sub_idx == 0:
                ax.legend(fontsize=6, loc='lower left', framealpha=0.6)

        # Hide unused subplots in last row
        for empty in range(n_sub, n_rows_used * NCOLS):
            axes[empty // NCOLS][empty % NCOLS].set_visible(False)

        # Shared y-axis label on leftmost column
        for r in range(n_rows_used):
            axes[r][0].set_ylabel('mm', fontsize=7)

        fig.autofmt_xdate(rotation=45, ha='right')
        fig.tight_layout(rect=[0, 0, 1, 0.95])
        fig.savefig(out_dir / f'{station}_ts_fig{fig_idx}.png',
                    dpi=130, bbox_inches='tight')
        plt.close(fig)

    # ══════════════════════════════════════════════════════════════════════════
    # Figures B: Scatter plots (3 figures, 20 subplots each)
    # ══════════════════════════════════════════════════════════════════════════
    for fig_idx, (sl, depth_label) in enumerate(zip(FIG_SLICES, FIG_DEPTH_LABELS), 1):
        depths_in_fig = DEPTH_GRID[sl]
        n_sub = len(depths_in_fig)
        n_rows_used = int(np.ceil(n_sub / NCOLS))

        fig, axes = plt.subplots(n_rows_used, NCOLS,
                                 figsize=(NCOLS * 3.0, n_rows_used * 3.0),
                                 squeeze=False)
        fig.suptitle(
            f'{station} — Scatter: observed vs. predicted MLCW compaction\n'
            f'Depths {depth_label}  (n = {n_valid} epochs)',
            fontsize=11, fontweight='bold'
        )

        for sub_idx, depth in enumerate(depths_in_fig):
            k   = int(depth / 5)
            row = sub_idx // NCOLS
            col = sub_idx % NCOLS
            ax  = axes[row][col]

            y_obs  = Y_valid[:, k]
            y_pred = Y_hat[:, k]

            all_vals = np.concatenate([y_obs, y_pred])
            vmin_k = float(np.nanmin(all_vals))
            vmax_k = float(np.nanmax(all_vals))
            margin = (vmax_k - vmin_k) * 0.06
            lim = [vmin_k - margin, vmax_k + margin]

            ax.scatter(y_pred, y_obs, s=4, alpha=0.40, color='steelblue',
                       linewidths=0, rasterized=True)
            ax.plot(lim, lim, 'k--', lw=0.8)
            ax.set_xlim(lim)
            ax.set_ylim(lim)
            ax.set_aspect('equal', adjustable='box')

            r2_k   = r2_per_depth[k]
            rmse_k = rmse_per_depth[k]
            ax.set_title(
                f'{int(depth)} m\nR²={r2_k:.2f}  RMSE={rmse_k:.2f}mm',
                fontsize=7.5, pad=2
            )
            ax.tick_params(labelsize=6)
            ax.grid(True, alpha=0.25)

            if col == 0:
                ax.set_ylabel('Obs Y (mm)', fontsize=6)
            if row == n_rows_used - 1:
                ax.set_xlabel('Pred Ŷ (mm)', fontsize=6)

        for empty in range(n_sub, n_rows_used * NCOLS):
            axes[empty // NCOLS][empty % NCOLS].set_visible(False)

        fig.tight_layout(rect=[0, 0, 1, 0.94])
        fig.savefig(out_dir / f'{station}_sc_fig{fig_idx}.png',
                    dpi=130, bbox_inches='tight')
        plt.close(fig)

    # ══════════════════════════════════════════════════════════════════════════
    # Figure C: RMSE + R² depth profile
    # ══════════════════════════════════════════════════════════════════════════
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 10), sharey=True)
    ax1.plot(rmse_per_depth, DEPTH_GRID, color='steelblue', lw=2)
    ax1.axvline(0, color='k', lw=0.6, ls=':')
    ax1.set_xlabel('RMSE (mm)', fontsize=11)
    ax1.set_ylabel('Depth (m)', fontsize=11)
    ax1.set_title('In-sample RMSE', fontsize=10)
    ax1.invert_yaxis(); ax1.set_ylim(295, 0)
    ax1.grid(True, alpha=0.3)

    ax2.plot(r2_per_depth, DEPTH_GRID, color='darkorange', lw=2)
    ax2.axvline(1, color='k', lw=0.6, ls='--', alpha=0.4)
    ax2.axvline(0, color='k', lw=0.6, ls=':')
    ax2.set_xlabel('R²', fontsize=11)
    ax2.set_title('In-sample R²', fontsize=10)
    ax2.grid(True, alpha=0.3)

    fig.suptitle(f'{station} — RMSE & R² depth profile  (n = {n_valid} epochs)',
                 fontsize=12, fontweight='bold')
    fig.tight_layout()
    fig.savefig(out_dir / f'{station}_validation_rmse_profile.png',
                dpi=150, bbox_inches='tight')
    plt.close(fig)

    # ══════════════════════════════════════════════════════════════════════════
    # Figure D: Residual heatmap
    # ══════════════════════════════════════════════════════════════════════════
    abs_resid = np.abs(resid[np.isfinite(resid)])
    vmax = float(np.percentile(abs_resid, 98)) if len(abs_resid) > 0 else 1.0

    fig, ax = plt.subplots(figsize=(14, 6))
    depth_edges = np.append(DEPTH_GRID - 2.5, DEPTH_GRID[-1] + 2.5)
    pcm = ax.pcolormesh(depth_edges, np.arange(n_valid + 1), resid,
                        cmap='RdBu_r', vmin=-vmax, vmax=vmax, shading='flat')
    yticks, ylabels = year_ticks(dates_valid)
    ax.set_yticks(yticks); ax.set_yticklabels(ylabels, fontsize=8)
    ax.set_xlabel('Depth (m)', fontsize=11)
    ax.set_ylabel('Epoch (year)', fontsize=11)
    ax.set_title(f'{station} — Residual heatmap  Y − Ŷ\n'
                 f'Clipped to ±{vmax:.2f} mm (98th pct)', fontsize=10)
    fig.colorbar(pcm, ax=ax, shrink=0.85, pad=0.01).set_label('Residual (mm)', fontsize=9)
    fig.tight_layout()
    fig.savefig(out_dir / f'{station}_validation_residual_heatmap.png',
                dpi=150, bbox_inches='tight')
    plt.close(fig)

    # ══════════════════════════════════════════════════════════════════════════
    # Figure E: Total column time series
    # ══════════════════════════════════════════════════════════════════════════
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.fill_between(date_axis, band_lo_total, band_hi_total,
                    color='steelblue', alpha=0.20, label='P05–P95 band')
    ax.plot(date_axis, Y_total,     color='k',         lw=1.5, label='Actual MLCW total')
    ax.plot(date_axis, Y_hat_total, color='steelblue', lw=1.5, ls='--',
            label='Predicted Ŷ_total')
    ax.axhline(0, color='k', lw=0.5, ls=':')
    ax.set_xlabel('Date', fontsize=11)
    ax.set_ylabel('Total column compaction (mm)', fontsize=11)
    ax.set_title(f'{station} — Actual vs. predicted total column compaction\n'
                 f'R² = {r2_total:.3f}   RMSE = {rmse_total:.2f} mm', fontsize=10)
    ax.legend(fontsize=9); ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / f'{station}_validation_total_timeseries.png',
                dpi=150, bbox_inches='tight')
    plt.close(fig)

    # ══════════════════════════════════════════════════════════════════════════
    # Figure F: Band coverage per depth
    # ══════════════════════════════════════════════════════════════════════════
    fig, ax = plt.subplots(figsize=(8, 9))
    ax.barh(DEPTH_GRID, coverage, height=4.0, color='steelblue', alpha=0.7)
    ax.axvline(0.90, color='red', lw=1.5, ls='--', label='90% target')
    ax.set_xlabel('Coverage fraction', fontsize=11)
    ax.set_ylabel('Depth (m)', fontsize=11)
    ax.set_title(f'{station} — P05–P95 band coverage per depth\n'
                 f'Mean = {mean_coverage:.3f}', fontsize=10)
    ax.set_xlim(0, 1.05); ax.invert_yaxis(); ax.set_ylim(295, 0)
    ax.legend(fontsize=9); ax.grid(True, alpha=0.3, axis='x')
    fig.tight_layout()
    fig.savefig(out_dir / f'{station}_validation_coverage.png',
                dpi=150, bbox_inches='tight')
    plt.close(fig)

    mean_seas_amp      = float(np.nanmean(seas['seasonal_amp_ann_mm']))
    med_seas_ratio     = float(np.nanmedian(seas['seasonal_amp_ratio']))
    mean_r_dt_poly     = float(np.nanmean(seas['r_detrended_poly']))
    mean_r_dt_ma       = float(np.nanmean(seas['r_detrended_ma']))
    frac_seas_dom      = float(np.nanmean(seas['seasonal_var_frac'] > 0.3))
    mean_ac1yr         = float(np.nanmean(seas['ac1yr']))

    logger.info(
        f'  [{station}]  n={n_valid}  RMSE={mean_rmse:.3f}mm  '
        f'R²={mean_r2:.3f}  cov={mean_coverage:.3f}  '
        f'totalR²={r2_total:.3f}  '
        f'seasAmp={mean_seas_amp:.3f}mm  rDT_ma={mean_r_dt_ma:.3f}'
    )

    return {
        'station':                  station,
        'n_valid_epochs':           n_valid,
        'mean_rmse_mm':             _f(mean_rmse),
        'mean_abs_bias_mm':         _f(mean_abs_bias),
        'mean_r2':                  _f(mean_r2),
        'mean_coverage':            _f(mean_coverage),
        'frac_depths_r2_pos':       _f(frac_r2_pos),
        'frac_depths_r2_gt08':      _f(frac_r2_08),
        'worst_rmse_depth_m':       _f(worst_rmse_depth),
        'best_r2_depth_m':          _f(best_r2_depth),
        'total_col_rmse_mm':        _f(rmse_total),
        'total_col_bias_mm':        _f(bias_total),
        'total_col_r2':             _f(r2_total),
        'total_col_coverage':       _f(float(np.mean(
            (Y_total >= band_lo_total) & (Y_total <= band_hi_total)
        ))),
        'mean_seasonal_amp_ann_mm': _f(mean_seas_amp),
        'median_seasonal_amp_ratio':_f(med_seas_ratio),
        'mean_r_detrended_poly':    _f(mean_r_dt_poly),
        'mean_r_detrended_ma':      _f(mean_r_dt_ma),
        'frac_depths_seasonal_dom': _f(frac_seas_dom),
        'mean_ac1yr':               _f(mean_ac1yr),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════

def main():
    t0 = time.time()

    # Discover stations
    stations = sorted([
        d.name for d in RATIO_ROOT.iterdir()
        if d.is_dir() and (d / f'{d.name}_direct_ratio_stats.csv').exists()
    ])
    logger.info(f'Found {len(stations)} stations: {stations}')

    # Load InSAR feather once
    logger.info('Loading InSAR feather...')
    df_insar    = pd.read_feather(INSAR_FILE)
    d_cols      = sorted([c for c in df_insar.columns if c.startswith('D')])
    insar_dates = [datetime.strptime(c[1:], '%Y%m%d') for c in d_cols]

    insar_by_station = {}
    for _, row in df_insar.iterrows():
        stn  = row['Ename']
        vals = row[d_cols].values.astype(float) * 1000.0   # m → mm
        insar_by_station[stn] = {
            d.year * 10000 + d.month * 100 + d.day: v
            for d, v in zip(insar_dates, vals)
        }

    logger.info(f'InSAR loaded: {len(insar_dates)} epochs, {len(insar_by_station)} stations')

    # Process all stations
    summary_rows = []
    for i, station in enumerate(stations, 1):
        logger.info(f'\n[{i:2d}/{len(stations)}] {station}')
        lookup = insar_by_station.get(station, {})
        if not lookup:
            logger.error(f'  [{station}] Not in InSAR feather — skipping')
            continue
        result = validate_station(station, lookup, insar_dates, None)
        if result is not None:
            summary_rows.append(result)

    # Cross-station summary CSV
    df_summary = pd.DataFrame(summary_rows)
    summary_csv = RATIO_ROOT / 'all_stations_validation_summary.csv'
    df_summary.to_csv(summary_csv, index=False)
    logger.info(f'\nSaved {summary_csv}')

    # Cross-station summary JSON
    elapsed = time.time() - t0
    summary_json_path = RATIO_ROOT / 'all_stations_validation_summary.json'
    summary_json = {
        'run_info': {
            'script':          'validate_all_stations.py',
            'n_stations':      len(summary_rows),
            'elapsed_seconds': round(elapsed, 1),
            'run_date':        datetime.now().strftime('%Y-%m-%d %H:%M'),
        },
        'cross_station_stats': {
            'median_mean_r2':                  _f(float(np.nanmedian([r['mean_r2'] for r in summary_rows]))),
            'median_mean_rmse_mm':             _f(float(np.nanmedian([r['mean_rmse_mm'] for r in summary_rows]))),
            'median_total_col_r2':             _f(float(np.nanmedian([r['total_col_r2'] for r in summary_rows]))),
            'median_coverage':                 _f(float(np.nanmedian([r['mean_coverage'] for r in summary_rows]))),
            'best_total_col_r2':               _f(float(max(r['total_col_r2'] for r in summary_rows))),
            'worst_total_col_r2':              _f(float(min(r['total_col_r2'] for r in summary_rows))),
            'median_seasonal_amp_ann_mm':      _f(float(np.nanmedian([r['mean_seasonal_amp_ann_mm'] for r in summary_rows]))),
            'median_seasonal_amp_ratio':       _f(float(np.nanmedian([r['median_seasonal_amp_ratio'] for r in summary_rows]))),
            'median_r_detrended_poly':         _f(float(np.nanmedian([r['mean_r_detrended_poly'] for r in summary_rows]))),
            'median_r_detrended_ma':           _f(float(np.nanmedian([r['mean_r_detrended_ma'] for r in summary_rows]))),
            'median_frac_depths_seasonal_dom': _f(float(np.nanmedian([r['frac_depths_seasonal_dom'] for r in summary_rows]))),
            'median_ac1yr':                    _f(float(np.nanmedian([r['mean_ac1yr'] for r in summary_rows]))),
        },
        'stations': summary_rows,
    }
    with open(summary_json_path, 'w') as fh:
        json.dump(summary_json, fh, indent=2)
    logger.info(f'Saved {summary_json_path}')

    # Terminal table
    elapsed = time.time() - t0
    print(f'\n{"=" * 95}')
    print(f'  BATCH VALIDATION — ALL STATIONS   ({elapsed:.0f}s)')
    print(f'{"=" * 95}')
    print(f'  {"Station":<18} {"n":>5} {"RMSE":>7} {"R²":>7} '
          f'{"totR²":>7} {"seasAmp":>8} {"ampRatio":>9} {"rDT_ma":>7} {"ac1yr":>6}')
    print(f'  {"-"*18} {"-"*5} {"-"*7} {"-"*7} '
          f'{"-"*7} {"-"*8} {"-"*9} {"-"*7} {"-"*6}')
    for r in summary_rows:
        print(
            f'  {r["station"]:<18} {r["n_valid_epochs"]:>5} '
            f'{r["mean_rmse_mm"]:>7.3f} {r["mean_r2"]:>7.3f} '
            f'{r["total_col_r2"]:>7.3f} '
            f'{r["mean_seasonal_amp_ann_mm"]:>8.3f} '
            f'{r["median_seasonal_amp_ratio"] if r["median_seasonal_amp_ratio"] is not None else float("nan"):>9.3f} '
            f'{r["mean_r_detrended_ma"] if r["mean_r_detrended_ma"] is not None else float("nan"):>7.3f} '
            f'{r["mean_ac1yr"] if r["mean_ac1yr"] is not None else float("nan"):>6.3f}'
        )
    print(f'{"=" * 95}')
    print(f'  Processed: {len(summary_rows)}/{len(stations)} stations')
    print(f'  Outputs:   {RATIO_ROOT}')


if __name__ == '__main__':
    main()
