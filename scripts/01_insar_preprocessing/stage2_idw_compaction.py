"""
Stage 2 — IDW Spatial Gap-Fill and 3D Compaction Field
=======================================================

Reads per-station compaction fraction profiles (f_median, f_p05, f_p95)
from 39 MLCW stations and interpolates them to 8,577 grid points using
Inverse Distance Weighting (IDW, n=8 neighbours).  Then multiplies by
the InSAR time-series at each grid point to produce a 3D compaction field:

    compaction(g, t, k) = f̄_k(g) × InSAR(g, t)

All outputs are written to stage2_output/ as NetCDF4 (CF conventions).

Pipeline
--------
1. Load 39-station f_median/f_p05/f_p95 profiles (60 depths each)
2. Apply 5-point moving average along depth axis per station
3. IDW interpolation: 39 stations → 8,577 grid points, per depth level
4. LOO-CV validation: hold each station out; predict from 38 remaining
5. Load InSAR time-series at grid points (8,577 × 785 epochs)
6. Compute central/lo/hi compaction fields (3D: grid × epoch × depth)
7. Write NetCDF4 outputs

Output files (in stage2_output/)
----------------------------------
  stage2_fbar_grid.nc           — f̄_k, f_p05, f_p95 at 8,577 grid points
  stage2_compaction_central.nc  — central compaction estimate
  stage2_compaction_lo.nc       — P05 lower bound
  stage2_compaction_hi.nc       — P95 upper bound
  stage2_loocv_results.csv      — LOO-CV per station per depth
"""

import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import numpy as np
import pandas as pd
import geopandas as gpd
import netCDF4 as nc
from scipy.ndimage import uniform_filter1d
from sklearn.neighbors import KNeighborsRegressor
from pathlib import Path
from datetime import datetime, timezone

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(r'D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2')
DR_DIR     = BASE_DIR / 'direct_ratio_MLCW_InSAR'
SHP_STA    = BASE_DIR / 'studyarea_SHP' / 'mlcw_station_utm50n.shp'
INSAR_GRID = BASE_DIR / 'InSAR_timeries' / 'gridpnt_500m_interp_insar_IDW_extend.feather'
OUT_DIR    = BASE_DIR / 'scripts_2026_Apr_May' / 'stage2_output'

OUT_DIR.mkdir(parents=True, exist_ok=True)

DEPTH_GRID = np.arange(0, 300, 5, dtype=np.float32)   # 60 depths: 0, 5, …, 295
N_DEPTHS   = 60
N_GRID     = 8577
N_NEIGH    = 8     # IDW neighbours (confirmed by user)
MA_SIZE    = 5     # depth-axis moving average window


# ── Step 1 — Load per-station f profiles ─────────────────────────────────────
def load_station_profiles():
    print('Loading station shapefile ...')
    gdf = gpd.read_file(SHP_STA)
    sta_order = sorted(gdf['Ename'].tolist())

    F_median = np.full((len(sta_order), N_DEPTHS), np.nan, dtype=np.float32)
    F_p05    = np.full((len(sta_order), N_DEPTHS), np.nan, dtype=np.float32)
    F_p95    = np.full((len(sta_order), N_DEPTHS), np.nan, dtype=np.float32)
    sta_xy   = np.zeros((len(sta_order), 2), dtype=np.float64)

    for i, sta in enumerate(sta_order):
        stats_csv = DR_DIR / sta / f'{sta}_direct_ratio_stats.csv'
        if not stats_csv.exists():
            print(f'  WARNING: {sta} — stats CSV not found, skipping')
            continue
        df  = pd.read_csv(stats_csv)
        F_median[i] = df['f_median'].values.astype(np.float32)
        F_p05[i]    = df['f_p05'].values.astype(np.float32)
        F_p95[i]    = df['f_p95'].values.astype(np.float32)

        row = gdf[gdf['Ename'] == sta].iloc[0]
        sta_xy[i, 0] = float(row['X_UTM50N'])
        sta_xy[i, 1] = float(row['Y_UTM50N'])
        print(f'  {sta}: f_median sum = {df["f_median"].sum():.4f}')

    # Drop stations where the CSV was missing (all-NaN rows)
    valid = np.all(np.isfinite(F_median), axis=1)
    n_invalid = int((~valid).sum())
    if n_invalid > 0:
        missing = [sta_order[i] for i in range(len(sta_order)) if not valid[i]]
        print(f'  WARNING: {n_invalid} stations with missing data dropped: {missing}')
    sta_order = [s for s, v in zip(sta_order, valid) if v]
    F_median  = F_median[valid]
    F_p05     = F_p05[valid]
    F_p95     = F_p95[valid]
    sta_xy    = sta_xy[valid]

    print(f'Loaded {len(sta_order)} stations with complete profiles.')
    return sta_order, sta_xy, F_median, F_p05, F_p95


# ── Step 2 — 5-point moving average along depth axis ─────────────────────────
def smooth_profiles(F_median, F_p05, F_p95):
    print('Applying 5-point moving average along depth axis ...')
    F_med_s = uniform_filter1d(F_median, size=MA_SIZE, axis=1, mode='nearest').astype(np.float32)
    F_p05_s = uniform_filter1d(F_p05,    size=MA_SIZE, axis=1, mode='nearest').astype(np.float32)
    F_p95_s = uniform_filter1d(F_p95,    size=MA_SIZE, axis=1, mode='nearest').astype(np.float32)
    return F_med_s, F_p05_s, F_p95_s


# ── Step 3 — IDW: 39 stations → 8,577 grid points ────────────────────────────
def idw_to_grid(sta_xy, F_med_s, F_p05_s, F_p95_s, grid_xy):
    print(f'IDW interpolation: {len(sta_xy)} stations → {len(grid_xy)} grid points '
          f'(n_neighbours={N_NEIGH}) ...')

    f_bar_grid = np.zeros((N_GRID, N_DEPTHS), dtype=np.float32)
    f_p05_grid = np.zeros((N_GRID, N_DEPTHS), dtype=np.float32)
    f_p95_grid = np.zeros((N_GRID, N_DEPTHS), dtype=np.float32)

    for k in range(N_DEPTHS):
        knn = KNeighborsRegressor(
            n_neighbors=min(N_NEIGH, len(sta_xy)),
            weights='distance', p=2, metric='minkowski')

        knn.fit(sta_xy, F_med_s[:, k])
        f_bar_grid[:, k] = knn.predict(grid_xy).astype(np.float32)

        knn.fit(sta_xy, F_p05_s[:, k])
        f_p05_grid[:, k] = knn.predict(grid_xy).astype(np.float32)

        knn.fit(sta_xy, F_p95_s[:, k])
        f_p95_grid[:, k] = knn.predict(grid_xy).astype(np.float32)

        if (k + 1) % 10 == 0:
            print(f'  Depth {k+1}/{N_DEPTHS} done ({DEPTH_GRID[k]:.0f} m)')

    print('IDW interpolation complete.')
    return f_bar_grid, f_p05_grid, f_p95_grid


# ── Step 4 — LOO-CV validation ────────────────────────────────────────────────
def loocv(sta_order, sta_xy, F_med_s, F_p05_s, F_p95_s):
    print('LOO-CV validation ...')
    records = []
    n_sta = len(sta_order)

    for hold in range(n_sta):
        train_mask = np.ones(n_sta, dtype=bool)
        train_mask[hold] = False

        knn = KNeighborsRegressor(
            n_neighbors=min(N_NEIGH, n_sta - 1),
            weights='distance', p=2, metric='minkowski')

        for k in range(N_DEPTHS):
            knn.fit(sta_xy[train_mask], F_med_s[train_mask, k])
            f_pred = float(knn.predict(sta_xy[hold:hold+1, :])[0])
            f_act  = float(F_med_s[hold, k])
            iqr    = float(F_p95_s[hold, k] - F_p05_s[hold, k])
            records.append({
                'station':   sta_order[hold],
                'depth_m':   float(DEPTH_GRID[k]),
                'f_pred':    f_pred,
                'f_actual':  f_act,
                'error':     f_pred - f_act,
                'abs_error': abs(f_pred - f_act),
                'iqr_range': iqr,
                'large_error': bool(iqr > 1e-6 and abs(f_pred - f_act) > 0.1 * iqr),
            })
        print(f'  [{hold+1:02d}/{n_sta}] {sta_order[hold]} — held out')

    df_loocv = pd.DataFrame(records)
    df_loocv.to_csv(OUT_DIR / 'stage2_loocv_results.csv', index=False, float_format='%.6f')

    mae_all = float(df_loocv['abs_error'].mean())
    n_large = int(df_loocv['large_error'].sum())
    print(f'LOO-CV MAE (all stations, all depths): {mae_all:.6f}')
    print(f'Depth-station pairs with |error| > 10% of IQR range: {n_large}')
    return df_loocv


# ── Step 5 — Load InSAR grid time-series ─────────────────────────────────────
def load_insar_grid():
    print('Loading InSAR grid feather ...')
    df        = pd.read_feather(INSAR_GRID)
    date_cols = sorted([c for c in df.columns if c.startswith('D2')])
    epochs    = [datetime.strptime(c[1:], '%Y%m%d') for c in date_cols]
    n_epochs  = len(epochs)

    insar_mm  = df[date_cols].values.astype(np.float32) * 1000.0   # m → mm
    # shape: (8577, n_epochs)

    grid_xy = df[['POINT_X', 'POINT_Y']].values.astype(np.float64)
    point_keys = df['PointKey'].values

    print(f'InSAR grid: {insar_mm.shape[0]} points × {n_epochs} epochs')
    print(f'  Date range: {epochs[0].date()} → {epochs[-1].date()}')
    return insar_mm, epochs, grid_xy, point_keys


# ── Step 6 — Compute 3D compaction field ──────────────────────────────────────
def compute_and_write_compaction(f_bar_grid, f_p05_grid, f_p95_grid,
                                  insar_mm, epochs):
    """
    compaction_central[g, t, k] = f_bar_grid[g, k] * InSAR[g, t]

    For lo/hi bounds, when InSAR < 0 (subsidence), the p05 fraction gives
    MORE compaction (lower bound) and p95 gives LESS (upper bound).
    When InSAR > 0, the relationship inverts.  We compute both and take
    the appropriate bound per sign.
    """
    n_epochs = insar_mm.shape[1]
    print(f'Computing 3D compaction field: {N_GRID} × {n_epochs} × {N_DEPTHS} ...')

    # Central: chunked write directly into the NetCDF files
    nc_c = _open_compaction_nc('stage2_compaction_central.nc', epochs,
                                'compaction_central',
                                'Central compaction estimate (f_bar * InSAR)',
                                'mm')
    nc_l = _open_compaction_nc('stage2_compaction_lo.nc', epochs,
                                'compaction_lo',
                                'P05 lower bound compaction (f_p05 or f_p95 per InSAR sign)',
                                'mm')
    nc_h = _open_compaction_nc('stage2_compaction_hi.nc', epochs,
                                'compaction_hi',
                                'P95 upper bound compaction (f_p05 or f_p95 per InSAR sign)',
                                'mm')

    CHUNK_G = 500
    for g_start in range(0, N_GRID, CHUNK_G):
        g_end = min(g_start + CHUNK_G, N_GRID)
        ins   = insar_mm[g_start:g_end, :]          # (chunk, n_epochs)
        fbar  = f_bar_grid[g_start:g_end, :]        # (chunk, 60)
        fp05  = f_p05_grid[g_start:g_end, :]        # (chunk, 60)
        fp95  = f_p95_grid[g_start:g_end, :]        # (chunk, 60)

        # (chunk, n_epochs, 60)
        comp_c = ins[:, :, None] * fbar[:, None, :]

        # For lo/hi: InSAR sign determines which fraction bound applies
        ins_neg = ins < 0                            # (chunk, n_epochs)
        fp_lo   = np.where(ins_neg[:, :, None], fp95[:, None, :], fp05[:, None, :])
        fp_hi   = np.where(ins_neg[:, :, None], fp05[:, None, :], fp95[:, None, :])
        comp_l  = ins[:, :, None] * fp_lo
        comp_h  = ins[:, :, None] * fp_hi

        nc_c['compaction_central'][g_start:g_end, :, :] = comp_c.astype(np.float32)
        nc_l['compaction_lo'][g_start:g_end, :, :] = comp_l.astype(np.float32)
        nc_h['compaction_hi'][g_start:g_end, :, :] = comp_h.astype(np.float32)

        print(f'  Chunk {g_start}–{g_end} written')

    nc_c.close()
    nc_l.close()
    nc_h.close()
    print('Compaction NetCDF4 files written.')


# ── NetCDF4 helpers ───────────────────────────────────────────────────────────
def _epoch_to_days(epochs):
    """Convert epoch list to days since 2015-01-01."""
    ref = datetime(2015, 1, 1)
    return np.array([(e - ref).days for e in epochs], dtype=np.float64)


def write_fbar_nc(f_bar_grid, f_p05_grid, f_p95_grid,
                  grid_xy, point_keys, epochs, sta_order, sta_xy,
                  F_med_s, F_p05_s, F_p95_s):
    path = OUT_DIR / 'stage2_fbar_grid.nc'
    print(f'Writing {path} ...')
    ds = nc.Dataset(str(path), 'w', format='NETCDF4')
    ds.Conventions    = 'CF-1.8'
    ds.title          = 'Stage 2 compaction fraction f̄_k at 8577 grid points'
    ds.institution    = 'InSAR-MLCW subsidence analysis'
    ds.source         = 'IDW interpolation of 39 MLCW stations, n_neighbours=8'
    ds.history        = f'Created {datetime.now(timezone.utc).isoformat()}'
    ds.depth_axis     = '60 levels: 0, 5, ..., 295 m'

    ds.createDimension('grid_point', N_GRID)
    ds.createDimension('depth', N_DEPTHS)
    ds.createDimension('station', len(sta_order))

    # Coordinates
    v = ds.createVariable('depth_m', 'f4', ('depth',))
    v.units        = 'm'
    v.long_name    = 'Depth below surface'
    v.positive     = 'down'
    v[:]           = DEPTH_GRID

    v = ds.createVariable('easting', 'f8', ('grid_point',))
    v.units        = 'm'
    v.long_name    = 'UTM 50N easting'
    v.standard_name = 'projection_x_coordinate'
    v[:]           = grid_xy[:, 0]

    v = ds.createVariable('northing', 'f8', ('grid_point',))
    v.units        = 'm'
    v.long_name    = 'UTM 50N northing'
    v.standard_name = 'projection_y_coordinate'
    v[:]           = grid_xy[:, 1]

    # f̄_k fields (grid_point × depth)
    for varname, data, desc in [
        ('f_bar',  f_bar_grid, 'Compaction fraction central estimate (f̄_k)'),
        ('f_p05',  f_p05_grid, 'Compaction fraction P05 lower bound'),
        ('f_p95',  f_p95_grid, 'Compaction fraction P95 upper bound'),
    ]:
        v = ds.createVariable(varname, 'f4', ('grid_point', 'depth'),
                              zlib=True, complevel=4)
        v.long_name = desc
        v.units     = '1'
        v[:]        = data

    # Station reference profiles
    v = ds.createVariable('sta_easting', 'f8', ('station',))
    v.units = 'm'; v.long_name = 'Station UTM 50N easting'
    v[:] = sta_xy[:, 0]

    v = ds.createVariable('sta_northing', 'f8', ('station',))
    v.units = 'm'; v.long_name = 'Station UTM 50N northing'
    v[:] = sta_xy[:, 1]

    v = ds.createVariable('sta_f_bar', 'f4', ('station', 'depth'),
                          zlib=True, complevel=4)
    v.long_name = 'Station f̄_k (smoothed, 5-pt MA)'
    v[:] = F_med_s

    ds.close()
    print(f'  {path} written.')


def _open_compaction_nc(filename, epochs, varname, long_name, units):
    path = OUT_DIR / filename
    print(f'Opening {path} for write ...')
    ds = nc.Dataset(str(path), 'w', format='NETCDF4')
    ds.Conventions = 'CF-1.8'
    ds.title       = long_name
    ds.history     = f'Created {datetime.now(timezone.utc).isoformat()}'

    n_ep = len(epochs)
    ds.createDimension('grid_point', N_GRID)
    ds.createDimension('epoch', n_ep)
    ds.createDimension('depth', N_DEPTHS)

    v = ds.createVariable('depth_m', 'f4', ('depth',))
    v.units = 'm'; v.long_name = 'Depth below surface'; v.positive = 'down'
    v[:] = DEPTH_GRID

    v = ds.createVariable('time', 'f8', ('epoch',))
    v.units         = 'days since 2015-01-01 00:00:00'
    v.calendar      = 'standard'
    v.long_name     = 'InSAR epoch date'
    v[:] = _epoch_to_days(epochs)

    v = ds.createVariable(varname, 'f4', ('grid_point', 'epoch', 'depth'),
                          zlib=True, complevel=4,
                          chunksizes=(min(500, N_GRID), min(100, n_ep), N_DEPTHS))
    v.units     = units
    v.long_name = long_name
    v.coordinates = 'time depth_m'
    return ds


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print('=' * 65)
    print('  Stage 2 IDW Spatial Gap-Fill')
    print('=' * 65)

    # 1. Load station profiles
    sta_order, sta_xy, F_median, F_p05, F_p95 = load_station_profiles()

    # 2. Smooth along depth axis
    F_med_s, F_p05_s, F_p95_s = smooth_profiles(F_median, F_p05, F_p95)

    # 3. Load InSAR grid (also extracts grid_xy)
    insar_mm, epochs, grid_xy, point_keys = load_insar_grid()
    assert insar_mm.shape[0] == N_GRID, \
        f'Expected {N_GRID} grid points, got {insar_mm.shape[0]}'

    # 4. IDW interpolation
    f_bar_grid, f_p05_grid, f_p95_grid = idw_to_grid(
        sta_xy, F_med_s, F_p05_s, F_p95_s, grid_xy)

    # 5. LOO-CV
    df_loocv = loocv(sta_order, sta_xy, F_med_s, F_p05_s, F_p95_s)

    # 6. Write f̄_k NetCDF4
    write_fbar_nc(f_bar_grid, f_p05_grid, f_p95_grid,
                  grid_xy, point_keys, epochs,
                  sta_order, sta_xy, F_med_s, F_p05_s, F_p95_s)

    # 7. Compute and write compaction NetCDF4 files
    compute_and_write_compaction(f_bar_grid, f_p05_grid, f_p95_grid,
                                  insar_mm, epochs)

    # Summary
    print('\n' + '=' * 65)
    print('  STAGE 2 COMPLETE')
    print('=' * 65)
    print(f'  Stations used       : {len(sta_order)}')
    print(f'  Grid points         : {N_GRID}')
    print(f'  Epochs              : {len(epochs)}')
    print(f'  Depth levels        : {N_DEPTHS}')
    print(f'  LOO-CV MAE          : {df_loocv["abs_error"].mean():.6f}')
    print(f'  Output directory    : {OUT_DIR}')
    print('=' * 65)


if __name__ == '__main__':
    main()
