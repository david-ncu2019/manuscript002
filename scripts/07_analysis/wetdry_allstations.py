"""
Wet/Dry Season Diagnostic — All 39 Stations
============================================
Refactored from wetdry_diagnostic_TUKU.py.

For each station:
  - Splits the direct-ratio matrix R[i,k] into wet (May–Oct) and dry (Nov–Apr) epochs
  - Computes per-depth ratio profiles and IQR bands for each season
  - Computes RMSE: scalar baseline vs. wet/dry split reconstruction
  - Writes extended per-station summary JSON and per-depth CSV
  - Produces four diagnostic plots

Cross-station outputs (after all stations complete):
  wetdry_allstations_summary.csv   — 39 rows × ~35 metric columns
  wetdry_allstations_summary.json
  wetdry_skipped.json              — stations that failed (may be empty)
"""

import json
import traceback
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(r'D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2')
MLCW_DIR   = BASE_DIR / 'MLCW_5m_regular'
INSAR_FILE = BASE_DIR / 'InSAR_timeries' / 'mlcw_interp_insar_IDW_extend.feather'
DR_DIR     = BASE_DIR / 'direct_ratio_MLCW_InSAR'

MLCW_REF_DATE = datetime(2015, 1, 16)
DEPTH_GRID    = np.arange(0, 300, 5, dtype=float)    # 0, 5, …, 295  (60 levels)
N_DEPTHS      = 60
ACTIVE_COLS   = [f'depth_{int(d):03d}m' for d in DEPTH_GRID]

AQUIFER_BANDS = [
    ('F1',  19, 103, '#b3d9ff'),
    ('F2',  35, 107, '#80c0ff'),
    ('F3', 140, 275, '#ffcc99'),
    ('F4', 238, 300, '#ff9966'),
]


# ── Discover station list from directory names ─────────────────────────────────
def get_station_list():
    return sorted([
        p.name for p in DR_DIR.iterdir()
        if p.is_dir() and (p / f'{p.name}_direct_ratio_all.npy').exists()
    ])


# ── Load InSAR feather once; cache lookup dicts per station ──────────────────
def load_insar_feather():
    print('Loading InSAR feather ...')
    df = pd.read_feather(INSAR_FILE)
    date_cols   = sorted([c for c in df.columns if c.startswith('D2')])
    insar_dates = [datetime.strptime(c[1:], '%Y%m%d') for c in date_cols]
    return df, date_cols, insar_dates


def get_insar_lookup(df_insar, date_cols, insar_dates, station):
    row = df_insar[df_insar['Ename'] == station]
    if row.empty:
        raise ValueError(f'Station {station} not found in InSAR feather')
    vals = row.iloc[0][date_cols].values.astype(float) * 1000.0   # m → mm
    return {
        d.year * 10000 + d.month * 100 + d.day: v
        for d, v in zip(insar_dates, vals)
    }, insar_dates


# ── Load matched epochs for one station ───────────────────────────────────────
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
    ref_row = mlcw_date_idx.get(ref_key)
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


# ── Helper: mean RMSE in aquifer depth range ──────────────────────────────────
def mean_rmse_in_range(arr, z_lo, z_hi):
    mask = (DEPTH_GRID >= z_lo) & (DEPTH_GRID <= z_hi)
    return float(np.nanmean(arr[mask]))


# ── Helper: shade aquifer bands ───────────────────────────────────────────────
def shade_aquifers(ax):
    for _, z_lo, z_hi, colour in AQUIFER_BANDS:
        ax.axhspan(z_lo, z_hi, color=colour, alpha=0.10, zorder=0)


# ── Core diagnostic for one station ──────────────────────────────────────────
def run_wetdry(station, insar_lookup, insar_dates):
    station_dr_dir = DR_DIR / station
    out_dir        = station_dr_dir / 'wetdry_diagnostic'
    out_dir.mkdir(parents=True, exist_ok=True)

    # -- Load data
    X_valid, Y_valid, dates_valid = load_matched_data(
        station, insar_lookup, insar_dates)
    n_valid = len(X_valid)
    if n_valid < 30:
        raise ValueError(f'Too few matched epochs ({n_valid}) for {station}')

    R = np.load(station_dr_dir / f'{station}_direct_ratio_all.npy')
    assert R.shape == (n_valid, N_DEPTHS), \
        f'Shape mismatch: R={R.shape}, expected ({n_valid}, {N_DEPTHS})'

    # -- Season masks
    months   = np.array([d.month for d in dates_valid])
    wet_mask = np.isin(months, [5, 6, 7, 8, 9, 10])
    dry_mask = ~wet_mask
    n_wet    = int(wet_mask.sum())
    n_dry    = int(dry_mask.sum())

    # -- Ratio profiles
    f_all = np.nanmedian(R,              axis=0)
    f_wet = np.nanmedian(R[wet_mask, :], axis=0)
    f_dry = np.nanmedian(R[dry_mask, :], axis=0)

    q25_all = np.nanpercentile(R,              25, axis=0)
    q75_all = np.nanpercentile(R,              75, axis=0)
    q25_wet = np.nanpercentile(R[wet_mask, :], 25, axis=0)
    q75_wet = np.nanpercentile(R[wet_mask, :], 75, axis=0)
    q25_dry = np.nanpercentile(R[dry_mask, :], 25, axis=0)
    q75_dry = np.nanpercentile(R[dry_mask, :], 75, axis=0)
    p05_wet = np.nanpercentile(R[wet_mask, :],  5, axis=0)
    p95_wet = np.nanpercentile(R[wet_mask, :], 95, axis=0)
    p05_dry = np.nanpercentile(R[dry_mask, :],  5, axis=0)
    p95_dry = np.nanpercentile(R[dry_mask, :], 95, axis=0)

    n_wet_per_depth = np.sum(np.isfinite(R[wet_mask, :]), axis=0).astype(int)
    n_dry_per_depth = np.sum(np.isfinite(R[dry_mask, :]), axis=0).astype(int)

    # -- Difference metrics
    abs_diff = np.abs(f_wet - f_dry)
    rel_diff = abs_diff / (np.abs(f_all) + 1e-9)

    # -- RMSE: scalar vs. wet/dry split
    Y_hat_scalar = X_valid[:, None] * f_all[None, :]
    f_split      = np.where(wet_mask[:, None], f_wet[None, :], f_dry[None, :])
    Y_hat_split  = X_valid[:, None] * f_split

    resid_scalar  = Y_valid - Y_hat_scalar
    resid_split   = Y_valid - Y_hat_split
    rmse_scalar   = np.sqrt(np.nanmean(resid_scalar ** 2, axis=0))
    rmse_split    = np.sqrt(np.nanmean(resid_split  ** 2, axis=0))
    rmse_improve  = rmse_scalar - rmse_split
    rmse_impr_pct = 100.0 * rmse_improve / (rmse_scalar + 1e-9)

    rmse_wet_scalar = np.sqrt(np.nanmean(resid_scalar[wet_mask, :] ** 2, axis=0))
    rmse_dry_scalar = np.sqrt(np.nanmean(resid_scalar[dry_mask, :] ** 2, axis=0))
    rmse_wet_split  = np.sqrt(np.nanmean(resid_split [wet_mask, :] ** 2, axis=0))
    rmse_dry_split  = np.sqrt(np.nanmean(resid_split [dry_mask, :] ** 2, axis=0))

    total_rmse_scalar = float(np.sqrt(np.nanmean(resid_scalar ** 2)))
    total_rmse_split  = float(np.sqrt(np.nanmean(resid_split  ** 2)))
    total_improv_mm   = total_rmse_scalar - total_rmse_split
    total_improv_pct  = 100.0 * total_improv_mm / (total_rmse_scalar + 1e-9)

    # -- Extended metrics
    n_depths_improved    = int(np.sum(rmse_improve > 0))
    frac_depths_improved = float(n_depths_improved / N_DEPTHS)
    idx_best = int(np.argmax(rmse_impr_pct))
    idx_worst= int(np.argmin(rmse_impr_pct))

    x_insar_mean_mm   = float(np.nanmean(np.abs(X_valid)))
    # Estimate seasonal std: std of (X - trend) where trend is a 1-yr median
    # Simple proxy: std of X itself minus its mean
    x_insar_seas_std_mm = float(np.nanstd(X_valid - np.nanmean(X_valid)))

    def aquifer_rel_diff(z_lo, z_hi):
        mask = (DEPTH_GRID >= z_lo) & (DEPTH_GRID <= z_hi)
        return float(np.nanmean(rel_diff[mask]))

    wetdry_recommended = bool(
        (np.sum(rel_diff > 0.10) >= 5) and (total_improv_pct > 2.0)
    )

    # -- Save per-depth CSV
    pd.DataFrame({
        'depth_m':          DEPTH_GRID,
        'f_all':            f_all,
        'f_wet':            f_wet,
        'f_dry':            f_dry,
        'q25_all':          q25_all,
        'q75_all':          q75_all,
        'q25_wet':          q25_wet,
        'q75_wet':          q75_wet,
        'q25_dry':          q25_dry,
        'q75_dry':          q75_dry,
        'p05_wet':          p05_wet,
        'p95_wet':          p95_wet,
        'p05_dry':          p05_dry,
        'p95_dry':          p95_dry,
        'abs_diff':         abs_diff,
        'rel_diff':         rel_diff,
        'n_wet':            n_wet_per_depth,
        'n_dry':            n_dry_per_depth,
        'rmse_scalar':      rmse_scalar,
        'rmse_split':       rmse_split,
        'rmse_wet_scalar':  rmse_wet_scalar,
        'rmse_dry_scalar':  rmse_dry_scalar,
        'rmse_wet_split':   rmse_wet_split,
        'rmse_dry_split':   rmse_dry_split,
        'rmse_improvement': rmse_improve,
        'rmse_improv_pct':  rmse_impr_pct,
    }).to_csv(out_dir / f'{station}_wetdry_profiles.csv', index=False, float_format='%.6f')

    # -- Build summary dict
    summary = {
        'station':                         station,
        'n_valid_epochs':                  int(n_valid),
        'n_wet_epochs':                    n_wet,
        'n_dry_epochs':                    n_dry,
        'wet_months':                      [5, 6, 7, 8, 9, 10],
        'dry_months':                      [11, 12, 1, 2, 3, 4],
        'x_insar_mean_mm':                 x_insar_mean_mm,
        'x_insar_seas_std_mm':             x_insar_seas_std_mm,
        'total_rmse_scalar_mm':            total_rmse_scalar,
        'total_rmse_split_mm':             total_rmse_split,
        'total_rmse_improvement_mm':       round(total_improv_mm, 6),
        'total_rmse_improv_pct':           round(total_improv_pct, 3),
        'mean_abs_diff_f':                 float(np.nanmean(abs_diff)),
        'mean_rel_diff_f':                 float(np.nanmean(rel_diff)),
        'max_abs_diff_f':                  float(np.nanmax(abs_diff)),
        'max_abs_diff_depth_m':            float(DEPTH_GRID[np.nanargmax(abs_diff)]),
        'max_rel_diff_f':                  float(np.nanmax(rel_diff)),
        'max_rel_diff_depth_m':            float(DEPTH_GRID[np.nanargmax(rel_diff)]),
        'depths_with_rel_diff_gt20pct':    int(np.sum(rel_diff > 0.20)),
        'depths_with_rel_diff_gt10pct':    int(np.sum(rel_diff > 0.10)),
        'sum_f_all':                       float(np.nansum(f_all)),
        'sum_f_wet':                       float(np.nansum(f_wet)),
        'sum_f_dry':                       float(np.nansum(f_dry)),
        'n_depths_improved':               n_depths_improved,
        'frac_depths_improved':            frac_depths_improved,
        'max_depth_improvement_pct':       float(rmse_impr_pct[idx_best]),
        'max_depth_improvement_depth_m':   float(DEPTH_GRID[idx_best]),
        'max_depth_degradation_pct':       float(rmse_impr_pct[idx_worst]),
        'max_depth_degradation_depth_m':   float(DEPTH_GRID[idx_worst]),
        'F1_mean_rel_diff':                aquifer_rel_diff( 19, 103),
        'F2_mean_rel_diff':                aquifer_rel_diff( 35, 107),
        'F3_mean_rel_diff':                aquifer_rel_diff(140, 275),
        'F4_mean_rel_diff':                aquifer_rel_diff(238, 300),
        'rmse_by_aquifer': {
            'F1': {'scalar': mean_rmse_in_range(rmse_scalar,  19, 103),
                   'split':  mean_rmse_in_range(rmse_split,   19, 103)},
            'F2': {'scalar': mean_rmse_in_range(rmse_scalar,  35, 107),
                   'split':  mean_rmse_in_range(rmse_split,   35, 107)},
            'F3': {'scalar': mean_rmse_in_range(rmse_scalar, 140, 275),
                   'split':  mean_rmse_in_range(rmse_split,  140, 275)},
            'F4': {'scalar': mean_rmse_in_range(rmse_scalar, 238, 300),
                   'split':  mean_rmse_in_range(rmse_split,  238, 300)},
        },
        'wetdry_recommended': wetdry_recommended,
        'profiles_distinguishable': bool(np.sum(rel_diff > 0.20) >= 5),
    }

    with open(out_dir / f'{station}_wetdry_summary.json', 'w', encoding='utf-8') as fh:
        json.dump(summary, fh, indent=2)

    # -- Plots
    _plot_profiles(station, out_dir, DEPTH_GRID,
                   f_all, f_wet, f_dry,
                   q25_all, q75_all, q25_wet, q75_wet, q25_dry, q75_dry,
                   abs_diff, rel_diff)

    _plot_rmse(station, out_dir, DEPTH_GRID,
               rmse_scalar, rmse_split, rmse_impr_pct)

    _plot_epoch_count(station, out_dir, dates_valid, wet_mask, dry_mask)

    _plot_ratio_heatmap(station, out_dir, R, dates_valid, wet_mask, dry_mask)

    return summary


# ── Plots ──────────────────────────────────────────────────────────────────────
def _plot_profiles(station, out_dir, depths,
                   f_all, f_wet, f_dry,
                   q25_all, q75_all, q25_wet, q75_wet, q25_dry, q75_dry,
                   abs_diff, rel_diff):
    fig, axes = plt.subplots(1, 3, figsize=(14, 10), sharey=True)
    fig.suptitle(f'{station} — Wet/Dry Season Direct Ratio Profiles', fontsize=13)

    ax = axes[0]
    ax.fill_betweenx(depths, q25_all, q75_all, color='grey',       alpha=0.22, label='IQR (all)')
    ax.fill_betweenx(depths, q25_wet, q75_wet, color='steelblue',  alpha=0.22, label='IQR (wet)')
    ax.fill_betweenx(depths, q25_dry, q75_dry, color='darkorange', alpha=0.22, label='IQR (dry)')
    ax.plot(f_all, depths, color='grey',       lw=2, label='f̄_k (all)')
    ax.plot(f_wet, depths, color='steelblue',  lw=2, label='f̄_k (wet)')
    ax.plot(f_dry, depths, color='darkorange', lw=2, label='f̄_k (dry)')
    ax.axvline(0, color='black', lw=0.5, ls='--')
    ax.set_ylabel('Depth (m)')
    ax.set_xlabel('Compaction fraction f_k')
    ax.set_title('Ratio profiles + IQR')
    ax.invert_yaxis()
    ax.legend(fontsize=8, loc='lower right')
    shade_aquifers(ax)

    ax = axes[1]
    diff_wd = f_wet - f_dry
    ax.barh(depths, diff_wd, height=4.5,
            color=np.where(diff_wd >= 0, 'steelblue', 'darkorange'), alpha=0.7)
    ax.axvline(0, color='black', lw=1)
    ax.set_xlabel('f̄_k_wet − f̄_k_dry')
    ax.set_title('Wet minus dry')
    shade_aquifers(ax)
    for name, z_lo, z_hi, _ in AQUIFER_BANDS:
        ax.text(0, (z_lo + z_hi) / 2, name, fontsize=7, color='dimgrey', va='center')

    ax = axes[2]
    ax.barh(depths, rel_diff * 100, height=4.5, color='purple', alpha=0.6)
    ax.axvline(20, color='red',    lw=1, ls='--', label='20%')
    ax.axvline(10, color='orange', lw=1, ls='--', label='10%')
    ax.set_xlabel('|f̄_wet − f̄_dry| / |f̄_all|  (%)')
    ax.set_title('Relative difference (%)')
    ax.legend(fontsize=8)
    shade_aquifers(ax)

    plt.tight_layout()
    fig.savefig(out_dir / f'{station}_wetdry_profile_plot.png', dpi=150)
    plt.close(fig)


def _plot_rmse(station, out_dir, depths, rmse_scalar, rmse_split, rmse_impr_pct):
    fig, axes = plt.subplots(1, 2, figsize=(12, 10), sharey=True)
    fig.suptitle(f'{station} — RMSE: Scalar vs. Wet/Dry Split', fontsize=13)

    ax = axes[0]
    ax.plot(rmse_scalar, depths, color='grey', lw=2, label='Scalar f̄_k')
    ax.plot(rmse_split,  depths, color='teal', lw=2, label='Wet/dry split')
    ax.fill_betweenx(depths, rmse_scalar, rmse_split,
                     where=(rmse_scalar > rmse_split), color='teal', alpha=0.2, label='Better')
    ax.fill_betweenx(depths, rmse_scalar, rmse_split,
                     where=(rmse_scalar <= rmse_split), color='red', alpha=0.2, label='Worse')
    ax.set_xlabel('RMSE (mm)');  ax.set_ylabel('Depth (m)')
    ax.set_title('RMSE by depth');  ax.invert_yaxis();  ax.legend(fontsize=8)
    shade_aquifers(ax)

    ax = axes[1]
    ax.barh(depths, rmse_impr_pct, height=4.5,
            color=np.where(rmse_impr_pct >= 0, 'teal', 'tomato'), alpha=0.7)
    ax.axvline(0, color='black', lw=1)
    ax.axvline(5, color='green', lw=1, ls='--', label='5% threshold')
    ax.set_xlabel('RMSE improvement (%)');  ax.set_title('RMSE reduction (%)');  ax.legend(fontsize=8)
    shade_aquifers(ax)

    plt.tight_layout()
    fig.savefig(out_dir / f'{station}_wetdry_rmse_comparison.png', dpi=150)
    plt.close(fig)


def _plot_epoch_count(station, out_dir, dates_valid, wet_mask, dry_mask):
    years     = np.array([d.year for d in dates_valid])
    year_rng  = np.arange(years.min(), years.max() + 1)
    wet_by_yr = [int(np.sum(wet_mask & (years == y))) for y in year_rng]
    dry_by_yr = [int(np.sum(dry_mask & (years == y))) for y in year_rng]

    fig, ax = plt.subplots(figsize=(10, 4))
    w = 0.35
    ax.bar(year_rng - w/2, wet_by_yr, width=w, color='steelblue',  label='Wet (May–Oct)')
    ax.bar(year_rng + w/2, dry_by_yr, width=w, color='darkorange', label='Dry (Nov–Apr)')
    ax.set_xlabel('Year');  ax.set_ylabel('Epochs')
    ax.set_title(f'{station} — Epoch count by season and year')
    ax.legend();  ax.set_xticks(year_rng);  ax.set_xticklabels(year_rng, rotation=45)
    plt.tight_layout()
    fig.savefig(out_dir / f'{station}_wetdry_epoch_count.png', dpi=150)
    plt.close(fig)


def _plot_ratio_heatmap(station, out_dir, R, dates_valid, wet_mask, dry_mask):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle(f'{station} — Ratio Matrix R[i,k] by Season', fontsize=13)
    clip = np.nanpercentile(np.abs(R), 95)
    for ax, mask, label in [
        (axes[0], wet_mask, 'Wet (May–Oct)'),
        (axes[1], dry_mask, 'Dry (Nov–Apr)'),
    ]:
        R_sub  = R[mask, :]
        order  = np.argsort(dates_valid[mask])
        R_sub  = R_sub[order, :]
        im = ax.imshow(R_sub.T, aspect='auto', origin='upper',
                       extent=[0, R_sub.shape[0], 295, 0],
                       vmin=-clip, vmax=clip, cmap='RdBu_r')
        ax.set_xlabel('Epoch (chronological)');  ax.set_ylabel('Depth (m)')
        ax.set_title(f'{label}  (n={mask.sum()})')
        plt.colorbar(im, ax=ax, label='f_k(i)')
    plt.tight_layout()
    fig.savefig(out_dir / f'{station}_wetdry_ratio_heatmap.png', dpi=150)
    plt.close(fig)


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
            insar_lookup, _ = get_insar_lookup(df_insar, date_cols, insar_dates, station)
            summary = run_wetdry(station, insar_lookup, insar_dates)
            all_summaries.append(summary)
            print(f'  OK — RMSE improvement: {summary["total_rmse_improv_pct"]:+.2f}%  '
                  f'wetdry_recommended={summary["wetdry_recommended"]}')
        except Exception as exc:
            print(f'  SKIPPED: {exc}')
            skipped.append({'station': station, 'reason': str(exc),
                            'traceback': traceback.format_exc()})

    # -- Cross-station summary CSV
    flat_rows = []
    for s in all_summaries:
        row = {k: v for k, v in s.items()
               if k not in ('wet_months', 'dry_months', 'rmse_by_aquifer')}
        for unit in ('F1', 'F2', 'F3', 'F4'):
            row[f'{unit}_rmse_scalar'] = s['rmse_by_aquifer'][unit]['scalar']
            row[f'{unit}_rmse_split']  = s['rmse_by_aquifer'][unit]['split']
        flat_rows.append(row)

    df_summary = pd.DataFrame(flat_rows)
    df_summary.to_csv(DR_DIR / 'wetdry_allstations_summary.csv', index=False, float_format='%.6f')
    with open(DR_DIR / 'wetdry_allstations_summary.json', 'w', encoding='utf-8') as fh:
        json.dump(all_summaries, fh, indent=2)
    with open(DR_DIR / 'wetdry_skipped.json', 'w', encoding='utf-8') as fh:
        json.dump(skipped, fh, indent=2)

    print(f'\n{"="*60}')
    print(f'  WET/DRY BATCH COMPLETE')
    print(f'  Processed: {len(all_summaries)}  |  Skipped: {len(skipped)}')
    if all_summaries:
        rec = [s['station'] for s in all_summaries if s['wetdry_recommended']]
        print(f'  Stations with wetdry_recommended=True: {rec if rec else "none"}')
    print(f'  Output: {DR_DIR}')
    print('='*60)


if __name__ == '__main__':
    main()
