"""
Batch Direct Ratio Analysis — All 39 MLCW Stations
f_k(i) = Y_s(i,k) / x_s(i)   (raw sign convention, no negation)

Runs the same analysis as direct_ratio_tuku_v2.py for every station found in
MLCW_5m_regular/. InSAR feather is loaded once and shared across all stations.

Output structure:
    direct_ratio_MLCW_InSAR/
        {STATION}/
            {STATION}_direct_ratio_stats.csv
            {STATION}_direct_ratio_all.npy
            {STATION}_direct_ratio_profile.png
            {STATION}_direct_ratio_heatmap.png
"""

import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
BASE_DIR      = Path(r'D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2')
MLCW_DIR      = BASE_DIR / 'MLCW_5m_regular'
INSAR_FILE    = BASE_DIR / 'InSAR_timeries' / 'mlcw_interp_insar_IDW_extend.feather'
OUTPUT_ROOT   = BASE_DIR / 'direct_ratio_MLCW_InSAR'
STAGE1_ROOT   = Path(r'D:\112_PROJECT_002\output')
MLCW_REF_DATE = datetime(2015, 1, 16)

DEPTH_GRID        = np.arange(0, 300, 5, dtype=float)   # [0, 5, ..., 295]
N_DEPTHS          = 60
ACTIVE_DEPTH_COLS = [f'depth_{int(d):03d}m' for d in DEPTH_GRID]


# ── Per-station processing ────────────────────────────────────────────────────

def process_station(station, insar_lookup, insar_dates):
    """
    Run direct ratio analysis for one station.

    Parameters
    ----------
    station      : str   station name (e.g. 'TUKU')
    insar_lookup : dict  {yyyymmdd_int: value_mm} for this station
    insar_dates  : list  of datetime objects (all 785 InSAR epochs)

    Returns
    -------
    dict with summary stats, or None if station was skipped.
    """
    out_dir = OUTPUT_ROOT / station
    out_dir.mkdir(parents=True, exist_ok=True)

    mlcw_file = MLCW_DIR / f'{station}_5m_grid.csv'
    if not mlcw_file.exists():
        logger.error(f'  [{station}] MLCW file not found: {mlcw_file}')
        return None

    # ── Load MLCW ─────────────────────────────────────────────────────────────
    df_mlcw    = pd.read_csv(mlcw_file, parse_dates=['datetime'])
    mlcw_dates = pd.to_datetime(df_mlcw['datetime'].values)
    mlcw_yyyymmdd = np.array([
        d.year * 10000 + d.month * 100 + d.day for d in mlcw_dates
    ])
    mlcw_date_idx = {v: i for i, v in enumerate(mlcw_yyyymmdd)}

    # Baseline subtraction at MLCW_REF_DATE
    ref_key = (MLCW_REF_DATE.year * 10000
               + MLCW_REF_DATE.month * 100
               + MLCW_REF_DATE.day)
    ref_row = mlcw_date_idx.get(ref_key)
    if ref_row is None:
        logger.warning(f'  [{station}] Reference date {MLCW_REF_DATE.date()} '
                       f'not found — using zeros as baseline')
        ref_vals = np.zeros(N_DEPTHS)
    else:
        ref_vals = df_mlcw[ACTIVE_DEPTH_COLS].iloc[ref_row].values.astype(float)

    # ── Align InSAR and MLCW by exact date ───────────────────────────────────
    matched_insar, matched_mlcw, matched_dates = [], [], []
    for d in insar_dates:
        key     = d.year * 10000 + d.month * 100 + d.day
        v_insar = insar_lookup.get(key)
        m_idx   = mlcw_date_idx.get(key)
        if v_insar is None or m_idx is None:
            continue
        mlcw_row = df_mlcw[ACTIVE_DEPTH_COLS].iloc[m_idx].values.astype(float) - ref_vals
        if np.isnan(v_insar) or np.any(np.isnan(mlcw_row)):
            continue
        matched_insar.append(v_insar)
        matched_mlcw.append(mlcw_row)
        matched_dates.append(d)

    n_valid = len(matched_insar)
    if n_valid == 0:
        logger.error(f'  [{station}] Zero matched epochs — skipping')
        return None

    X_valid     = np.array(matched_insar)    # (n_valid,)
    Y_valid     = np.array(matched_mlcw)     # (n_valid, 60)
    dates_valid = np.array(matched_dates)

    # ── Ratio matrix ──────────────────────────────────────────────────────────
    with np.errstate(divide='ignore', invalid='ignore'):
        R = Y_valid / X_valid[:, None]       # (n_valid, 60)
    R = np.where(np.isfinite(R), R, np.nan)

    # ── Summary statistics ────────────────────────────────────────────────────
    f_median = np.nanmedian(R,           axis=0)
    f_q25    = np.nanpercentile(R,  25,  axis=0)
    f_q75    = np.nanpercentile(R,  75,  axis=0)
    f_p05    = np.nanpercentile(R,   5,  axis=0)
    f_p95    = np.nanpercentile(R,  95,  axis=0)
    n_finite = np.sum(np.isfinite(R),    axis=0)

    median_sum = float(np.nansum(f_median))

    # ── Save CSV ──────────────────────────────────────────────────────────────
    df_stats = pd.DataFrame({
        'depth_m':         DEPTH_GRID,
        'f_median':        f_median,
        'f_q25':           f_q25,
        'f_q75':           f_q75,
        'f_p05':           f_p05,
        'f_p95':           f_p95,
        'n_finite_epochs': n_finite,
    })
    df_stats.to_csv(out_dir / f'{station}_direct_ratio_stats.csv', index=False)

    # ── Save raw ratio matrix ─────────────────────────────────────────────────
    np.save(out_dir / f'{station}_direct_ratio_all.npy', R)

    # ── Load Stage 1 w_k if available ────────────────────────────────────────
    w_hat = None
    w_hat_path = (STAGE1_ROOT
                  / f'stage1_perstation_{station.lower()}_test'
                  / f'{station.lower()}_B_point_estimate.csv')
    if w_hat_path.exists():
        w_hat = pd.read_csv(w_hat_path)['B_point'].values

    # ── Figure 1: depth profile ───────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(6, 10))

    ax.fill_betweenx(DEPTH_GRID, f_p05, f_p95,
                     color='steelblue', alpha=0.15, label='5–95th pct')
    ax.fill_betweenx(DEPTH_GRID, f_q25, f_q75,
                     color='steelblue', alpha=0.35, label='IQR (Q25–Q75)')
    ax.plot(f_median, DEPTH_GRID, color='steelblue', lw=2,
            label='Median $f_k$')

    if w_hat is not None:
        ax.plot(w_hat, DEPTH_GRID, color='darkorange', lw=1.5,
                linestyle='--', label='Stage 1 $\\hat{w}_k$')

    ax.axvline(0, color='k', lw=0.6, ls=':')
    ax.set_xlabel('Fraction of InSAR signal (dimensionless)', fontsize=11)
    ax.set_ylabel('Depth (m)', fontsize=11)
    ax.set_title(f'{station} — Direct ratio $f_k = Y_s / x_s$\n'
                 f'n = {n_valid} valid epochs', fontsize=11)
    ax.invert_yaxis()
    ax.set_ylim(295, 0)
    ax.legend(fontsize=9, loc='lower right')
    ax.grid(True, alpha=0.3)
    ax.text(0.98, 0.02,
            f'Median sum = {median_sum:.4f}',
            transform=ax.transAxes, fontsize=8, ha='right', va='bottom',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))

    fig.tight_layout()
    fig.savefig(out_dir / f'{station}_direct_ratio_profile.png',
                dpi=150, bbox_inches='tight')
    plt.close(fig)

    # ── Figure 2: heatmap ─────────────────────────────────────────────────────
    abs_vals = np.abs(R[np.isfinite(R)])
    vmax = float(np.percentile(abs_vals, 98)) if len(abs_vals) > 0 else 0.05
    vmin = -vmax

    fig, ax = plt.subplots(figsize=(14, 6))
    depth_edges = np.append(DEPTH_GRID - 2.5, DEPTH_GRID[-1] + 2.5)
    epoch_edges = np.arange(n_valid + 1)

    pcm = ax.pcolormesh(depth_edges, epoch_edges, R,
                        cmap='RdBu_r', vmin=vmin, vmax=vmax, shading='flat')

    year_ticks, year_labels, current_year = [], [], None
    for idx, d in enumerate(dates_valid):
        yr = d.year
        if yr != current_year:
            year_ticks.append(idx)
            year_labels.append(str(yr))
            current_year = yr

    ax.set_yticks(year_ticks)
    ax.set_yticklabels(year_labels, fontsize=8)
    ax.set_xlabel('Depth (m)', fontsize=11)
    ax.set_ylabel('Epoch (year)', fontsize=11)
    ax.set_title(f'{station} — Ratio heatmap $f_k(i)$\n'
                 f'Colour clipped to ±{vmax:.3f}  (98th pct of |R|)', fontsize=11)

    cbar = fig.colorbar(pcm, ax=ax, shrink=0.85, pad=0.01)
    cbar.set_label('$f_k(i)$', fontsize=9)

    fig.tight_layout()
    fig.savefig(out_dir / f'{station}_direct_ratio_heatmap.png',
                dpi=150, bbox_inches='tight')
    plt.close(fig)

    # ── Pearson r vs Stage 1 w_k ──────────────────────────────────────────────
    pearson_r = np.nan
    if w_hat is not None:
        from scipy.stats import pearsonr
        valid_both = np.isfinite(f_median) & np.isfinite(w_hat)
        if valid_both.sum() > 2:
            pearson_r, _ = pearsonr(f_median[valid_both], w_hat[valid_both])

    n_neg_median = int(np.sum(f_median < 0))

    return {
        'station':    station,
        'n_valid':    n_valid,
        'median_sum': median_sum,
        'n_neg':      n_neg_median,
        'pearson_r':  pearson_r,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    t0 = time.time()

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    # Discover stations from MLCW files
    mlcw_files = sorted(MLCW_DIR.glob('*_5m_grid.csv'))
    stations   = [f.stem.replace('_5m_grid', '') for f in mlcw_files]
    logger.info(f'Found {len(stations)} MLCW stations: {stations}')

    # Load InSAR feather once
    logger.info('\nLoading InSAR feather...')
    df_insar    = pd.read_feather(INSAR_FILE)
    d_cols      = sorted([c for c in df_insar.columns if c.startswith('D')])
    insar_dates = [datetime.strptime(c[1:], '%Y%m%d') for c in d_cols]

    # Build per-station InSAR lookup: {station: {yyyymmdd: value_mm}}
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
            logger.error(f'  [{station}] Not found in InSAR feather — skipping')
            continue
        result = process_station(station, lookup, insar_dates)
        if result is not None:
            summary_rows.append(result)
            logger.info(f'  [{station}] done  n_valid={result["n_valid"]}  '
                        f'median_sum={result["median_sum"]:.4f}  '
                        f'n_neg_depths={result["n_neg"]}')

    # Final summary table
    elapsed = time.time() - t0
    print(f'\n{"=" * 75}')
    print(f'  BATCH DIRECT RATIO — ALL STATIONS   ({elapsed:.0f}s)')
    print(f'{"=" * 75}')
    print(f'  {"Station":<16}  {"n_valid":>7}  {"median_sum":>10}  '
          f'{"n_neg_depths":>12}  {"Pearson_r":>9}')
    print(f'  {"-"*16}  {"-"*7}  {"-"*10}  {"-"*12}  {"-"*9}')
    for r in summary_rows:
        pr = f'{r["pearson_r"]:.4f}' if np.isfinite(r['pearson_r']) else '   N/A'
        print(f'  {r["station"]:<16}  {r["n_valid"]:>7}  '
              f'{r["median_sum"]:>10.4f}  {r["n_neg"]:>12}  {pr:>9}')
    print(f'{"=" * 75}')
    print(f'  Processed: {len(summary_rows)}/{len(stations)} stations')
    print(f'  Outputs:   {OUTPUT_ROOT}')


if __name__ == '__main__':
    main()
