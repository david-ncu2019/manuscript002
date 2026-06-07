"""
Alpha comparison: GNSS-derived vs InSAR-derived for all MLCW stations.

Computes per station:
  v_MLCW   : secular velocity from total MLCW column compaction (mm/yr)
  v_InSAR  : secular velocity from InSAR vertical displacement (mm/yr)
  alpha_insar = v_MLCW / v_InSAR
  alpha_gnss  : existing value from ratio_MLCW_over_GPS_RBF_interpolated.csv

Epoch alignment: both velocities are estimated over the overlapping date window
  [max(mlcw_start, insar_start), min(mlcw_end, insar_end)] only.

Output: alpha_comparison_all_stations.csv
"""

import numpy as np
import pandas as pd
from pathlib import Path

BASE = Path(r'D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2')

# ── Load InSAR feather once (all stations) ────────────────────────────────────
insar_file = BASE / 'InSAR_timeries' / 'mlcw_interp_insar_IDW_extend.feather'
df_insar = pd.read_feather(insar_file)

# Displacement columns: 'D' + 8 digits
date_cols = [c for c in df_insar.columns if c.startswith('D') and len(c) == 9]
dates_insar = pd.to_datetime([c[1:] for c in date_cols], format='%Y%m%d')
t0_insar = dates_insar[0]
t_insar_yr = (dates_insar - t0_insar).days / 365.25

insar_start = dates_insar[0].date()
insar_end = dates_insar[-1].date()
n_insar_epochs = len(dates_insar)

# ── Load GNSS alpha table once ────────────────────────────────────────────────
alpha_file = BASE / 'ratio_MLCW_over_GPS_RBF_interpolated.csv'
df_alpha = pd.read_csv(alpha_file).set_index('Ename')

# ── Process each station ──────────────────────────────────────────────────────
mlcw_dir = BASE / 'MLCW_reconstruction'
mlcw_files = sorted(mlcw_dir.glob('*_ringbyring_reconstructed.csv'))
print(f"Found {len(mlcw_files)} MLCW station files\n")

records = []

for filepath in mlcw_files:
    station = filepath.stem.replace('_ringbyring_reconstructed', '')
    warning_parts = []

    # ── MLCW: load and clean ──────────────────────────────────────────────────
    df_mlcw = pd.read_csv(filepath)
    datetime_col = df_mlcw.columns[0]
    ring_cols = df_mlcw.columns[1:]
    valid_rings = [c for c in ring_cols if not df_mlcw[c].isna().all()]
    n_valid_rings = len(valid_rings)

    df_mlcw['datetime'] = pd.to_datetime(df_mlcw[datetime_col])
    df_mlcw = df_mlcw.dropna(subset=valid_rings, how='any').copy()
    df_mlcw['total_mm'] = df_mlcw[valid_rings].sum(axis=1)

    mlcw_start_full = df_mlcw['datetime'].iloc[0]
    mlcw_end_full   = df_mlcw['datetime'].iloc[-1]

    # ── InSAR: find station row ───────────────────────────────────────────────
    station_rows = df_insar[df_insar['Ename'] == station]

    if len(station_rows) == 0:
        warning_parts.append('station_not_in_insar')
        v_mlcw = np.nan
        v_insar = np.nan
        alpha_insar = np.nan
        overlap_start = overlap_end = pd.NaT
        n_mlcw_overlap = n_insar_overlap = 0
    else:
        # ── Compute overlapping window ────────────────────────────────────────
        overlap_start = max(mlcw_start_full, dates_insar[0])
        overlap_end   = min(mlcw_end_full,   dates_insar[-1])

        if overlap_start >= overlap_end:
            warning_parts.append('no_overlap')
            v_mlcw = np.nan
            v_insar = np.nan
            alpha_insar = np.nan
            n_mlcw_overlap = n_insar_overlap = 0
        else:
            # ── Clip MLCW to overlap window ───────────────────────────────────
            mask_mlcw = (df_mlcw['datetime'] >= overlap_start) & \
                        (df_mlcw['datetime'] <= overlap_end)
            df_mlcw_ov = df_mlcw[mask_mlcw].copy()
            n_mlcw_overlap = len(df_mlcw_ov)

            t0_ov = overlap_start
            df_mlcw_ov['t_yr'] = (df_mlcw_ov['datetime'] - t0_ov).dt.days / 365.25
            slope_mlcw, _ = np.polyfit(df_mlcw_ov['t_yr'], df_mlcw_ov['total_mm'], 1)
            v_mlcw = slope_mlcw

            # ── Clip InSAR to overlap window ──────────────────────────────────
            mask_insar = (dates_insar >= overlap_start) & (dates_insar <= overlap_end)
            dates_ov   = dates_insar[mask_insar]
            cols_ov    = [c for c, m in zip(date_cols, mask_insar) if m]
            n_insar_overlap = len(dates_ov)

            vals_insar = station_rows[cols_ov].values.flatten().astype(float) * 1000.0
            t_ov_yr = (dates_ov - t0_ov).days / 365.25
            slope_insar, _ = np.polyfit(t_ov_yr, vals_insar, 1)
            v_insar = slope_insar

            if abs(v_insar) < 1.0:
                warning_parts.append('v_InSAR~0')
                alpha_insar = np.nan
            else:
                alpha_insar = v_mlcw / v_insar

    # ── GNSS alpha ────────────────────────────────────────────────────────────
    if station in df_alpha.index:
        alpha_gnss = float(df_alpha.loc[station, 'Imputed_Ratio'])
    else:
        warning_parts.append('no_alpha_gnss')
        alpha_gnss = np.nan

    # ── Derived comparisons ───────────────────────────────────────────────────
    if np.isfinite(alpha_insar) and np.isfinite(alpha_gnss):
        alpha_diff = alpha_insar - alpha_gnss
        alpha_ratio = alpha_insar / alpha_gnss if alpha_gnss != 0 else np.nan
    else:
        alpha_diff = np.nan
        alpha_ratio = np.nan

    warning = '; '.join(warning_parts)

    records.append({
        'Ename': station,
        'v_MLCW_mmyr': round(v_mlcw, 4) if np.isfinite(v_mlcw) else np.nan,
        'v_InSAR_mmyr': round(v_insar, 4) if np.isfinite(v_insar) else np.nan,
        'alpha_insar': round(alpha_insar, 4) if np.isfinite(alpha_insar) else np.nan,
        'alpha_gnss': round(alpha_gnss, 4) if np.isfinite(alpha_gnss) else np.nan,
        'alpha_diff': round(alpha_diff, 4) if np.isfinite(alpha_diff) else np.nan,
        'alpha_ratio': round(alpha_ratio, 4) if np.isfinite(alpha_ratio) else np.nan,
        'n_valid_rings': n_valid_rings,
        'overlap_start': str(overlap_start.date()) if pd.notna(overlap_start) else '',
        'overlap_end': str(overlap_end.date()) if pd.notna(overlap_end) else '',
        'n_mlcw_overlap': n_mlcw_overlap,
        'n_insar_overlap': n_insar_overlap,
        'mlcw_full_start': str(mlcw_start_full.date()),
        'mlcw_full_end': str(mlcw_end_full.date()),
        'insar_full_start': str(dates_insar[0].date()),
        'insar_full_end': str(dates_insar[-1].date()),
        'warning': warning,
    })

    print(f"  {station:20s}  v_MLCW={v_mlcw:+7.2f}  "
          f"v_InSAR={v_insar:+7.2f}  "
          f"ai={alpha_insar:.4f}  ag={alpha_gnss:.4f}"
          if np.isfinite(alpha_insar) and np.isfinite(alpha_gnss) else
          f"  {station:20s}  v_MLCW={v_mlcw:+7.2f}  WARNING: {warning}")

# ── Save CSV ──────────────────────────────────────────────────────────────────
df_out = pd.DataFrame(records)
out_file = BASE / 'alpha_comparison_all_stations.csv'
df_out.to_csv(out_file, index=False)
print(f"\nSaved: {out_file}")
print(f"Rows: {len(df_out)}  (expect 39)\n")

# ── Console summary: sorted by |alpha_diff| descending ───────────────────────
df_valid = df_out.dropna(subset=['alpha_diff']).copy()
df_valid['abs_diff'] = df_valid['alpha_diff'].abs()
df_sorted = df_valid.sort_values('abs_diff', ascending=False)

print(f"{'=' * 75}")
print(f"  SUMMARY -- sorted by |alpha_insar - alpha_gnss| (largest discrepancy first)")
print(f"{'=' * 75}")
print(f"  {'Station':<20} {'ai':>8} {'ag':>8} {'diff':>8} {'ratio':>7}")
print(f"  {'-'*20} {'-'*8} {'-'*8} {'-'*8} {'-'*7}")
for _, row in df_sorted.iterrows():
    print(f"  {row['Ename']:<20} {row['alpha_insar']:>8.4f} {row['alpha_gnss']:>8.4f} "
          f"{row['alpha_diff']:>+8.4f} {row['alpha_ratio']:>7.4f}")

# Stations with warnings
df_warn = df_out[df_out['warning'] != '']
if len(df_warn) > 0:
    print(f"\n  Stations with warnings:")
    for _, row in df_warn.iterrows():
        print(f"    {row['Ename']}: {row['warning']}")

print(f"\n  TUKU check:")
tuku = df_out[df_out['Ename'] == 'TUKU']
if len(tuku):
    r = tuku.iloc[0]
    print(f"    v_MLCW={r['v_MLCW_mmyr']:.3f}  v_InSAR={r['v_InSAR_mmyr']:.3f}  "
          f"ai={r['alpha_insar']:.4f}  ag={r['alpha_gnss']:.4f}")
print(f"{'=' * 75}")
