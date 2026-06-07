"""
Groundwater Level Dataset Inspection
=====================================
Deeply inspects D:\1000_SCRIPTS\004_Project003\20251229_Gwater_Levels\
20260108_GWL_CRFP_daily_modeled.h5 and produces two output files in
a new gwl_inspection\ folder:

  gwl_inspection_report.json  — consolidated report: dataset summary,
                                 per-station and per-well evaluation metrics,
                                 MLCW overlap analysis, yearly coverage table.
                                 Designed for consumption by AI agents or
                                 domain experts advising on pipeline integration.

  gwl_allwells_flat.csv       — flat table (one row per well) for Excel review.

Run with:
  D:\\Programs\\miniconda3\\Library\\envs\\fafalab\\python.exe inspect_gwater_data.py
"""

import sys
import os
import json
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, r'D:\VENV_PYTHON\appgeopy')
sys.path.insert(0, r'D:\VENV_PYTHON\py3_8\Scripts')

import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

from appgeopy import gwatertools

# ── Paths ─────────────────────────────────────────────────────────────────────
GWL_FILE   = Path(r'D:\1000_SCRIPTS\004_Project003\20251229_Gwater_Levels'
                   r'\20260108_GWL_CRFP_daily_modeled.h5')
INSAR_FILE = Path(r'D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2'
                   r'\InSAR_timeries\mlcw_interp_insar_IDW_extend.feather')
OUT_DIR    = Path(r'D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2'
                   r'\gwl_inspection')
OUT_DIR.mkdir(parents=True, exist_ok=True)

# InSAR study period (from MLCW feather column range)
INSAR_START = pd.Timestamp('2015-01-21')
INSAR_END   = pd.Timestamp('2025-12-11')
YEARS       = list(range(2014, 2026))


# ── Helpers ───────────────────────────────────────────────────────────────────
def _safe_float(x):
    """Convert numpy scalar / float to native Python float, or None if nan."""
    try:
        v = float(x)
        return None if np.isnan(v) else round(v, 6)
    except Exception:
        return None


def _safe_str(x):
    try:
        if isinstance(x, (bytes, np.bytes_)):
            return x.decode('utf-8', errors='replace')
        return str(x)
    except Exception:
        return ''


def _longest_gap_days(series: pd.Series) -> int:
    """Return length in days of the longest continuous NaN run."""
    is_nan   = series.isna()
    max_gap  = 0
    cur_gap  = 0
    for v in is_nan:
        if v:
            cur_gap += 1
            max_gap = max(max_gap, cur_gap)
        else:
            cur_gap = 0
    return max_gap


def _data_quality_label(frac: float) -> str:
    if frac >= 0.90:
        return 'good'
    elif frac >= 0.70:
        return 'moderate'
    else:
        return 'sparse'


def _build_well_researcher_notes(station, wellcode, depth_m, elev_m,
                                  frac_ov, gwl_min, gwl_max, seasonal_amp,
                                  trend, quality, has_long_gap) -> str:
    parts = [f'{station} well {wellcode}:']
    if depth_m is not None:
        parts.append(f'{depth_m:.0f} m deep well')
    if elev_m is not None:
        parts.append(f'(surface elevation {elev_m:.1f} m)')
    parts.append(f'with {frac_ov*100:.0f}% valid coverage during InSAR overlap period.')
    if gwl_min is not None and gwl_max is not None:
        parts.append(f'GWL ranges {gwl_min:.2f} to {gwl_max:.2f} m elevation.')
    if seasonal_amp is not None:
        parts.append(f'Seasonal amplitude ~{seasonal_amp:.2f} m.')
    if trend is not None:
        direction = 'rising' if trend > 0 else 'declining'
        parts.append(f'Linear trend: {direction} at {abs(trend):.3f} m/yr.')
    if has_long_gap:
        parts.append('WARNING: has at least one gap >180 days within InSAR period.')
    if quality == 'sparse':
        parts.append('Data coverage is sparse — use with caution for time-series analysis.')
    elif quality == 'moderate':
        parts.append('Moderate data coverage — check gap periods before use.')
    else:
        parts.append('Data quality is good for time-series analysis.')
    return ' '.join(parts)


def _build_station_researcher_notes(station, n_wells, depth_min, depth_max,
                                     st_quality, frac_ov_mean) -> str:
    parts = [f'{station}:']
    parts.append(f'{n_wells} monitoring well(s)')
    if depth_min is not None and depth_max is not None:
        parts.append(f'covering {depth_min:.0f}–{depth_max:.0f} m depth range.')
    parts.append(f'Mean InSAR-overlap coverage: {frac_ov_mean*100:.0f}%.')
    parts.append(f'Station overall data quality: {st_quality}.')
    return ' '.join(parts)


# ── Load data ─────────────────────────────────────────────────────────────────
print(f'Loading {GWL_FILE.name} ...')
gwl_data, gwl_info = gwatertools.open_HDF5(str(GWL_FILE))

raw_ts   = gwl_data.get('daily_timestamp', np.array([]))
time_arr = pd.to_datetime([ele.decode('utf-8') for ele in raw_ts])
n_total_days = len(time_arr)
print(f'  {n_total_days} daily time steps: {time_arr[0].date()} -> {time_arr[-1].date()}')

# InSAR overlap mask on time_arr
insar_mask = (time_arr >= INSAR_START) & (time_arr <= INSAR_END)
n_insar_days = int(insar_mask.sum())

# Pre-compute year array for yearly coverage (avoid O(n*n_wells) recomputation)
time_years = time_arr.year.values  # numpy int array, same length as time_arr

# Load MLCW station names from InSAR feather
print('Loading MLCW station list from InSAR feather ...')
df_insar = pd.read_feather(str(INSAR_FILE))
mlcw_stations = set(df_insar['Ename'].tolist())
print(f'  {len(mlcw_stations)} MLCW stations found')

file_size_mb = round(GWL_FILE.stat().st_size / 1e6, 2)

# ── Core loop: per station -> per well ────────────────────────────────────────
station_records = {}   # station -> well -> metrics dict
flat_rows        = []  # one per well, for CSV
gwl_stations     = set()

n_wells_total = 0
quality_counts = {'good': 0, 'moderate': 0, 'sparse': 0}

yearly_coverage = {'years': YEARS}  # will add station -> wellcode -> list

print('Processing stations and wells ...')

for station_name, wells_dict in gwl_data.items():
    if not isinstance(wells_dict, dict):
        continue  # skip 'daily_timestamp' and any other non-dict root entries

    gwl_stations.add(station_name)
    station_meta = gwl_info.get(station_name, {})

    well_records = {}
    depth_vals   = []
    frac_ov_list = []

    # Station-level coordinates (from first well's metadata or station-level attrs)
    sta_x = _safe_float(station_meta.get('X', np.nan))
    sta_y = _safe_float(station_meta.get('Y', np.nan))

    for wellcode, arrays in wells_dict.items():
        if not isinstance(arrays, dict):
            continue

        n_wells_total += 1
        model_arr = np.array(arrays.get('model', []), dtype=float)
        has_orig  = 'original' in arrays

        well_meta  = station_meta.get(wellcode, {})
        depth_m    = _safe_float(well_meta.get('Well_Depth(m)', np.nan))
        screen_str = _safe_str(well_meta.get('Well_Screen(m)', ''))
        elev_m     = _safe_float(well_meta.get('Well_Elev(m)', np.nan))
        well_name  = _safe_str(well_meta.get('Well_Name', ''))
        w_x        = _safe_float(well_meta.get('X', np.nan)) or sta_x
        w_y        = _safe_float(well_meta.get('Y', np.nan)) or sta_y

        if depth_m is not None:
            depth_vals.append(depth_m)
        # Update station-level coords if not yet found
        if sta_x is None and w_x is not None:
            sta_x = w_x
        if sta_y is None and w_y is not None:
            sta_y = w_y

        # Build Series aligned with time_arr
        n_arr = len(model_arr)
        if n_arr == n_total_days:
            series = pd.Series(model_arr, index=time_arr)
        else:
            # Truncate or pad to match
            if n_arr > n_total_days:
                series = pd.Series(model_arr[:n_total_days], index=time_arr)
            else:
                pad   = np.full(n_total_days - n_arr, np.nan)
                series = pd.Series(np.concatenate([model_arr, pad]), index=time_arr)

        valid_mask = series.notna()
        n_valid    = int(valid_mask.sum())
        frac_valid = round(n_valid / n_total_days, 4) if n_total_days > 0 else 0.0

        first_valid = series[valid_mask].index[0].isoformat() if n_valid > 0 else None
        last_valid  = series[valid_mask].index[-1].isoformat() if n_valid > 0 else None

        # InSAR overlap subset
        series_ov  = series[insar_mask]
        valid_ov   = series_ov.notna()
        n_valid_ov = int(valid_ov.sum())
        frac_ov    = round(n_valid_ov / n_insar_days, 4) if n_insar_days > 0 else 0.0
        frac_ov_list.append(frac_ov)

        # Statistics over InSAR overlap valid values
        vals_ov = series_ov[valid_ov].values
        gwl_min    = _safe_float(np.nanmin(vals_ov))  if len(vals_ov) > 0 else None
        gwl_max    = _safe_float(np.nanmax(vals_ov))  if len(vals_ov) > 0 else None
        gwl_mean   = _safe_float(np.nanmean(vals_ov)) if len(vals_ov) > 0 else None
        gwl_std    = _safe_float(np.nanstd(vals_ov))  if len(vals_ov) > 0 else None
        gwl_median = _safe_float(np.nanmedian(vals_ov)) if len(vals_ov) > 0 else None

        # Linear trend (m/yr) over InSAR overlap period
        trend = None
        if len(vals_ov) >= 30:
            t_days  = (series_ov[valid_ov].index - INSAR_START).days.values.astype(float)
            coeffs  = np.polyfit(t_days, vals_ov, 1)
            trend   = _safe_float(coeffs[0] * 365.25)  # slope in m/day -> m/yr

        # Seasonal amplitude: std of monthly anomaly × 2
        seasonal_amp = None
        if len(vals_ov) >= 180:
            s_ov_valid = series_ov[valid_ov]
            monthly_mean = s_ov_valid.groupby(s_ov_valid.index.month).mean()
            anomaly = s_ov_valid - s_ov_valid.index.map(lambda d: monthly_mean.get(d.month, np.nan))
            seasonal_amp = _safe_float(anomaly.std() * 2)

        # Long-gap check in InSAR period
        longest_gap = _longest_gap_days(series_ov)
        has_long_gap = bool(longest_gap > 180)

        quality = _data_quality_label(frac_ov)
        quality_counts[quality] += 1

        notes = _build_well_researcher_notes(
            station_name, wellcode, depth_m, elev_m,
            frac_ov, gwl_min, gwl_max, seasonal_amp,
            trend, quality, has_long_gap)

        # Yearly coverage (valid days per year)
        if station_name not in yearly_coverage:
            yearly_coverage[station_name] = {}
        valid_arr = series.notna().values  # bool array aligned with time_arr
        yearly_coverage[station_name][wellcode] = [
            int(valid_arr[time_years == yr].sum()) for yr in YEARS
        ]

        well_rec = {
            'well_name':                 well_name,
            'well_depth_m':              depth_m,
            'well_screen_str':           screen_str,
            'well_elev_m':               elev_m,
            'x_twd97':                   w_x,
            'y_twd97':                   w_y,
            'n_total_days':              n_total_days,
            'n_valid_days':              n_valid,
            'frac_valid_total':          frac_valid,
            'date_first_valid':          first_valid,
            'date_last_valid':           last_valid,
            'date_first_total':          time_arr[0].isoformat(),
            'date_last_total':           time_arr[-1].isoformat(),
            'has_original':              has_orig,
            'n_valid_insar_overlap':     n_valid_ov,
            'frac_valid_insar_overlap':  frac_ov,
            'gwl_min_m':                 gwl_min,
            'gwl_max_m':                 gwl_max,
            'gwl_mean_m':                gwl_mean,
            'gwl_std_m':                 gwl_std,
            'gwl_median_m':              gwl_median,
            'gwl_trend_m_per_yr':        trend,
            'gwl_seasonal_amp_m':        seasonal_amp,
            'longest_gap_days_insar':    longest_gap,
            'has_long_gap_gt180d':       has_long_gap,
            'data_quality':              quality,
            'researcher_notes':          notes,
        }
        well_records[wellcode] = well_rec

        flat_row = {'station': station_name, 'wellcode': wellcode}
        flat_row.update({k: v for k, v in well_rec.items() if k != 'researcher_notes'})
        flat_rows.append(flat_row)

    # Station-level summary
    frac_ov_mean  = float(np.mean(frac_ov_list)) if frac_ov_list else 0.0
    depth_min     = _safe_float(min(depth_vals)) if depth_vals else None
    depth_max     = _safe_float(max(depth_vals)) if depth_vals else None
    st_quality    = _data_quality_label(frac_ov_mean)

    station_records[station_name] = {
        'n_wells':                  len(well_records),
        'x_twd97':                  sta_x,
        'y_twd97':                  sta_y,
        'well_depth_min_m':         depth_min,
        'well_depth_max_m':         depth_max,
        'mean_frac_valid_insar':    round(frac_ov_mean, 4),
        'station_data_quality':     st_quality,
        'station_researcher_notes': _build_station_researcher_notes(
            station_name, len(well_records),
            depth_min, depth_max, st_quality, frac_ov_mean),
        'wells': well_records,
    }

    print(f'  {station_name}: {len(well_records)} wells, quality={st_quality}, '
          f'mean_coverage={frac_ov_mean:.0%}')

# ── MLCW overlap ──────────────────────────────────────────────────────────────
in_both           = sorted(mlcw_stations & gwl_stations)
mlcw_only         = sorted(mlcw_stations - gwl_stations)
gwl_only          = sorted(gwl_stations  - mlcw_stations)

mlcw_overlap = {
    'n_mlcw_stations':            len(mlcw_stations),
    'n_gwl_stations':             len(gwl_stations),
    'n_stations_in_both':         len(in_both),
    'stations_in_both':           in_both,
    'mlcw_stations_without_gwl':  mlcw_only,
    'gwl_stations_not_in_mlcw':   gwl_only,
    'researcher_notes': (
        f'{len(in_both)} of 39 MLCW stations have matching GWL monitoring wells '
        f'in the HDF5 file. {len(mlcw_only)} MLCW stations have no GWL data available '
        f'(these will need spatial interpolation of GWL if groundwater is incorporated '
        f'into the subsidence model). {len(gwl_only)} GWL stations exist outside the '
        f'MLCW study domain and are not directly usable for compaction attribution.'
    ),
}

# ── Dataset summary ───────────────────────────────────────────────────────────
dataset_summary = {
    'file_path':          str(GWL_FILE),
    'file_size_mb':       file_size_mb,
    'date_range_total':   {'first': time_arr[0].isoformat(),
                           'last':  time_arr[-1].isoformat()},
    'n_total_days':       n_total_days,
    'n_stations':         len(gwl_stations),
    'n_wells_total':      n_wells_total,
    'insar_overlap_period': {'start': INSAR_START.isoformat(),
                              'end':   INSAR_END.isoformat(),
                              'n_days': n_insar_days},
    'n_wells_good_quality':     quality_counts['good'],
    'n_wells_moderate_quality': quality_counts['moderate'],
    'n_wells_sparse':           quality_counts['sparse'],
    'quality_threshold_good':   'frac_valid_insar_overlap >= 0.90',
    'quality_threshold_moderate': '0.70 <= frac_valid_insar_overlap < 0.90',
    'quality_threshold_sparse': 'frac_valid_insar_overlap < 0.70',
    'purpose': (
        'Groundwater level (GWL) dataset inspection for the InSAR-MLCW '
        'subsidence attribution pipeline on the Choushui River Alluvial Fan, '
        'central-western Taiwan. GWL data are used to assess seasonal variability '
        'in compaction fraction ratios (wet vs. dry season) and may serve as an '
        'additional covariate for depth-stratified compaction modelling.'
    ),
    'researcher_notes': (
        f'The dataset contains {n_wells_total} monitoring wells across {len(gwl_stations)} '
        f'stations. Of these, {quality_counts["good"]} wells have good data coverage '
        f'(>=90% valid) during the InSAR study period 2015-2025, '
        f'{quality_counts["moderate"]} have moderate coverage (70-90%), and '
        f'{quality_counts["sparse"]} are sparse (<70%). '
        f'{len(in_both)} stations overlap with the 39 MLCW subsidence monitoring '
        f'stations. Key next step: assess whether GWL seasonal cycles correlate with '
        f'the wet/dry season compaction ratio divergence identified in the MLCW analysis.'
    ),
    'generated_at': datetime.now().isoformat(),
}

# ── Assemble and write consolidated JSON ──────────────────────────────────────
report = {
    'dataset_summary':  dataset_summary,
    'mlcw_overlap':     mlcw_overlap,
    'yearly_coverage':  yearly_coverage,
    'stations':         station_records,
}

json_path = OUT_DIR / 'gwl_inspection_report.json'
with open(json_path, 'w', encoding='utf-8') as fh:
    json.dump(report, fh, indent=2, ensure_ascii=False, default=str)
print(f'\nJSON written -> {json_path}')

# ── Write flat CSV ────────────────────────────────────────────────────────────
df_flat = pd.DataFrame(flat_rows)
csv_path = OUT_DIR / 'gwl_allwells_flat.csv'
df_flat.to_csv(csv_path, index=False, float_format='%.6f')
print(f'CSV  written -> {csv_path}')

# ── Console summary ───────────────────────────────────────────────────────────
print('\n' + '=' * 65)
print('  GROUNDWATER INSPECTION COMPLETE')
print('=' * 65)
print(f'  GWL file size       : {file_size_mb} MB')
print(f'  Time range          : {time_arr[0].date()} -> {time_arr[-1].date()}')
print(f'  Total days          : {n_total_days}')
print(f'  GWL stations        : {len(gwl_stations)}')
print(f'  Total wells         : {n_wells_total}')
print(f'  Wells quality — good: {quality_counts["good"]}  '
      f'moderate: {quality_counts["moderate"]}  sparse: {quality_counts["sparse"]}')
print(f'  MLCW overlap        : {len(in_both)} / 39 stations matched')
print(f'  MLCW no GWL data    : {mlcw_only}')
print(f'  Output folder       : {OUT_DIR}')
print('=' * 65)
