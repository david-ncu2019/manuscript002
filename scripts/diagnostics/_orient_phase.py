"""
ORIENT phase: find replacement candidates for all coverage failures.
For each failure, search xcorr parquet for the station, filter by depth + dist rules,
check coverage, and select best replacement.
"""
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2")
V3_PATH = BASE / "data/gwl/gwl_to_mlcw_layer_assignment_v3.csv"
FEATHER_DIR = BASE / "data/gwl/well_timeseries"
XCORR_DIR = BASE / "results/ring_gwl_xcorr"

# Dead wellcodes (0 obs in 2023-2025)
DEAD_WELLS = {'09030211', '09030221', '09160111', '09190211', '09030121'}

v3 = pd.read_csv(V3_PATH, dtype={"assigned_wellcode": str})


def check_coverage(feather_path, wellcode):
    """Return (n_2015_2022, n_2023_2025) for a wellcode in a feather file."""
    if not feather_path.exists():
        return 0, 0
    df = pd.read_feather(feather_path)
    if 'datetime' in df.columns:
        df = df.set_index('datetime')
    df.index = pd.to_datetime(df.index)
    wc = str(wellcode).zfill(8)
    if wc not in df.columns:
        return 0, 0
    s = df[wc]
    n_15_22 = s.loc['2015-01-01':'2022-12-31'].notna().sum()
    n_23_25 = s.loc['2023-01-01':'2025-12-31'].notna().sum()
    return int(n_15_22), int(n_23_25)


def find_replacement(station, layer, layer_min, layer_max, is_t_layer=False):
    """
    Search xcorr parquet for station, filter by depth+dist, return best candidate.
    Returns dict with replacement info or None.
    """
    xcorr_path = XCORR_DIR / f"{station}_ring_gwl_xcorr.parquet"
    if not xcorr_path.exists():
        print(f"  No xcorr file for {station}")
        return None

    df = pd.read_parquet(xcorr_path)
    df['gwl_wellcode'] = df['gwl_wellcode'].astype(str).str.zfill(8)

    # Determine the ring depth to match (use layer midpoint)
    if layer_min == layer_max:
        ring_target = layer_min
    else:
        ring_target = (layer_min + layer_max) / 2.0

    # Filter to ring depths closest to layer midpoint
    # Use all rows but filter by screen depth
    depth_tol = 20.0 if is_t_layer else 15.0

    # Apply depth filter
    if is_t_layer:
        # T layers: single depth point, match within ±20m of layer_min (=layer_max)
        depth_ok = (
            (df['screen_mid_m'] >= layer_min - depth_tol) &
            (df['screen_mid_m'] <= layer_max + depth_tol)
        )
    else:
        depth_ok = (
            (df['screen_mid_m'] >= layer_min - depth_tol) &
            (df['screen_mid_m'] <= layer_max + depth_tol)
        )

    # Distance filter: ≤ 10000 m
    dist_ok = df['dist_m'] <= 10000.0

    # Exclude dead wells
    not_dead = ~df['gwl_wellcode'].isin(DEAD_WELLS)

    candidates = df[depth_ok & dist_ok & not_dead].copy()

    if candidates.empty:
        print(f"  {station} {layer}: No depth+dist candidates found")
        # Try nearest fallback (relax depth, keep dist ≤ 10km)
        candidates = df[dist_ok & not_dead].copy()
        if candidates.empty:
            print(f"  {station} {layer}: No candidates even with relaxed depth")
            return None
        fallback = True
    else:
        fallback = False

    # Sort by dist ascending
    candidates = candidates.sort_values('dist_m')

    # Check coverage for each candidate
    for _, cand in candidates.drop_duplicates(subset=['gwl_station', 'gwl_wellcode']).iterrows():
        gwl_station = cand['gwl_station']
        wc = str(cand['gwl_wellcode']).zfill(8)
        feather_path = FEATHER_DIR / f"{gwl_station}_gwl_timeseries.feather"
        n15, n23 = check_coverage(feather_path, wc)

        if n23 >= 100:
            # Find the xcorr row for this well at the ring depth closest to layer midpoint
            cand_rows = df[df['gwl_wellcode'] == wc].copy()
            cand_rows['ring_dist'] = abs(cand_rows['ring_depth_m'] - ring_target)
            best_xcorr_row = cand_rows.sort_values('ring_dist').iloc[0]

            method = 'NEAREST_FALLBACK' if fallback else 'DIRECT_MATCH'
            depth_in_range = (
                cand['screen_mid_m'] >= layer_min - depth_tol and
                cand['screen_mid_m'] <= layer_max + depth_tol
            )
            if not depth_in_range:
                method = 'NEAREST_FALLBACK'

            return {
                'gwl_station': gwl_station,
                'gwl_wellcode': wc,
                'screen_top_m': cand['screen_top_m'],
                'screen_bot_m': cand['screen_bot_m'],
                'screen_mid_m': cand['screen_mid_m'],
                'dist_m': cand['dist_m'],
                'feather_file': f"data/gwl/well_timeseries/{gwl_station}_gwl_timeseries.feather",
                'n_2015_2022': n15,
                'n_2023_2025': n23,
                'xcorr_max': best_xcorr_row.get('xcorr_max', np.nan),
                'xcorr_lag_days': best_xcorr_row.get('lag_days_at_max', np.nan),
                'assignment_method': method,
                'is_fallback': fallback,
            }

    # All candidates failed coverage — DATA_LIMITED: use best depth match
    candidates2 = df[depth_ok & not_dead].copy().sort_values('dist_m')
    if candidates2.empty:
        candidates2 = df[not_dead].copy().sort_values('dist_m')

    for _, cand in candidates2.drop_duplicates(subset=['gwl_station', 'gwl_wellcode']).iterrows():
        gwl_station = cand['gwl_station']
        wc = str(cand['gwl_wellcode']).zfill(8)
        feather_path = FEATHER_DIR / f"{gwl_station}_gwl_timeseries.feather"
        n15, n23 = check_coverage(feather_path, wc)
        cand_rows = df[df['gwl_wellcode'] == wc].copy()
        cand_rows['ring_dist'] = abs(cand_rows['ring_depth_m'] - ring_target)
        best_xcorr_row = cand_rows.sort_values('ring_dist').iloc[0]
        return {
            'gwl_station': gwl_station,
            'gwl_wellcode': wc,
            'screen_top_m': cand['screen_top_m'],
            'screen_bot_m': cand['screen_bot_m'],
            'screen_mid_m': cand['screen_mid_m'],
            'dist_m': cand['dist_m'],
            'feather_file': f"data/gwl/well_timeseries/{gwl_station}_gwl_timeseries.feather",
            'n_2015_2022': n15,
            'n_2023_2025': n23,
            'xcorr_max': best_xcorr_row.get('xcorr_max', np.nan),
            'xcorr_lag_days': best_xcorr_row.get('lag_days_at_max', np.nan),
            'assignment_method': 'DATA_LIMITED',
            'is_fallback': False,
        }

    return None


# Define coverage failures from OBSERVE phase
failures = [
    # (station, layer, layer_min, layer_max, is_T)
    ('ANNAN',     'T1', 44.191, 44.191, True),
    ('GUANGFU',   'F1', 28.926, 31.618, False),
    ('HAIFENG',   'F1', 14.026, 33.794, False),
    ('JIANYANG',  'F1', 14.345, 25.006, False),
    ('JIANYANG',  'T1', 34.098, 34.098, True),
    ('LONGYAN',   'T1', 28.780, 49.737, True),
    ('TUKU',      'T1', 41.577, 41.577, True),
    ('XINXING',   'T1', 31.948, 41.948, True),
    ('XIUTAN',    'T1', 35.303, 51.297, True),
    ('YIWU',      'F1',  2.370, 15.472, False),
    ('YIWU',      'T1', 32.966, 32.966, True),
    ('YUANCHANG', 'T1', 44.226, 44.226, True),
    ('ZHENGMIN',  'F2', 76.604, 141.830, False),
]

print("=== ORIENT phase: finding replacements ===\n")
results = {}
for station, layer, lmin, lmax, is_t in failures:
    print(f"--- {station} {layer} (depth {lmin}–{lmax} m, is_T={is_t}) ---")
    r = find_replacement(station, layer, lmin, lmax, is_t)
    if r:
        print(f"  -> SELECTED: {r['gwl_station']} {r['gwl_wellcode']} "
              f"screen_mid={r['screen_mid_m']} dist={r['dist_m']:.0f}m "
              f"method={r['assignment_method']} "
              f"cov2015-22={r['n_2015_2022']} cov2023-25={r['n_2023_2025']} "
              f"xcorr={r['xcorr_max']:.3f} lag_days={r['xcorr_lag_days']:.0f}")
    else:
        print(f"  -> NO REPLACEMENT FOUND")
    results[(station, layer)] = r
    print()
