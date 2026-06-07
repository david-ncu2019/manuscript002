"""
Detailed ORIENT checks for problematic cases.
"""
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2")
FEATHER_DIR = BASE / "data/gwl/well_timeseries"
XCORR_DIR = BASE / "results/ring_gwl_xcorr"
DEAD_WELLS = {'09030211', '09030221', '09160111', '09190211', '09030121'}


def check_coverage(gwl_station, wellcode):
    feather_path = FEATHER_DIR / f"{gwl_station}_gwl_timeseries.feather"
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
    n15 = s.loc['2015-01-01':'2022-12-31'].notna().sum()
    n23 = s.loc['2023-01-01':'2025-12-31'].notna().sum()
    return int(n15), int(n23)


def show_all_candidates(station, layer_min, layer_max, is_t=True, label=""):
    print(f"\n=== {station} {label} candidates (lmin={layer_min}, lmax={layer_max}, is_T={is_t}) ===")
    xcorr_path = XCORR_DIR / f"{station}_ring_gwl_xcorr.parquet"
    if not xcorr_path.exists():
        print(f"  No xcorr file for {station}")
        return
    df = pd.read_parquet(xcorr_path)
    df['gwl_wellcode'] = df['gwl_wellcode'].astype(str).str.zfill(8)

    depth_tol = 20.0 if is_t else 15.0
    ring_target = (layer_min + layer_max) / 2.0

    # Show all candidates within 15km, sorted by distance
    within_15km = df[df['dist_m'] <= 15000].drop_duplicates(subset=['gwl_station', 'gwl_wellcode'])
    within_15km = within_15km.sort_values('dist_m')

    print(f"  All wells within 15km:")
    for _, row in within_15km.iterrows():
        wc = str(row['gwl_wellcode']).zfill(8)
        depth_ok = (row['screen_mid_m'] >= layer_min - depth_tol and
                    row['screen_mid_m'] <= layer_max + depth_tol)
        dead = wc in DEAD_WELLS
        n15, n23 = check_coverage(row['gwl_station'], wc)
        print(f"    {row['gwl_station']:12s} {wc} screen_mid={row['screen_mid_m']:6.1f}m "
              f"dist={row['dist_m']:7.0f}m depth_ok={depth_ok} dead={dead} "
              f"n15={n15:4d} n23={n23:4d} xcorr={row.get('xcorr_max', np.nan):.3f}")


# YIWU F1 (depth 2.37-15.472 m): Check all options within 15km
show_all_candidates('YIWU', 2.370, 15.472, is_t=False, label="F1")

# YIWU T1 (depth 32.966 m)
show_all_candidates('YIWU', 32.966, 32.966, is_t=True, label="T1")

# JIANYANG F1 (depth 14.345-25.006 m)
show_all_candidates('JIANYANG', 14.345, 25.006, is_t=False, label="F1")

# HAIFENG F1 (depth 14.026-33.794) - check current candidate quality
print("\n=== HAIFENG F1 check ===")
n15, n23 = check_coverage('FENGRONG', '09120111')
print(f"  FENGRONG 09120111 screen_mid=30m: n2015-2022={n15}, n2023-2025={n23}")
# Also check HAIFENG own station
n15b, n23b = check_coverage('HAIFENG', '09130311')
print(f"  HAIFENG 09130311 screen_mid=61m: n2015-2022={n15b}, n2023-2025={n23b}")

# ANNAN T1 detail
print("\n=== ANNAN T1 candidates ===")
xcorr_path = XCORR_DIR / "ANNAN_ring_gwl_xcorr.parquet"
df = pd.read_parquet(xcorr_path)
df['gwl_wellcode'] = df['gwl_wellcode'].astype(str).str.zfill(8)
# T1 depth 44.191, tol ±20 => 24.191 to 64.191
depth_ok = (df['screen_mid_m'] >= 44.191-20) & (df['screen_mid_m'] <= 44.191+20)
dist_ok = df['dist_m'] <= 10000
not_dead = ~df['gwl_wellcode'].isin(DEAD_WELLS)
cands = df[depth_ok & dist_ok & not_dead].drop_duplicates(subset=['gwl_station','gwl_wellcode']).sort_values('dist_m')
for _, row in cands.iterrows():
    wc = str(row['gwl_wellcode']).zfill(8)
    n15, n23 = check_coverage(row['gwl_station'], wc)
    print(f"  {row['gwl_station']:12s} {wc} screen_mid={row['screen_mid_m']:6.1f}m "
          f"dist={row['dist_m']:7.0f}m n15={n15:4d} n23={n23:4d} xcorr={row.get('xcorr_max', np.nan):.3f}")

# XINXING T1 detail - HAIFENG 09130311 at depth 61m for T1 at 31.948-41.948?
print("\n=== XINXING T1 check: depth validity ===")
lmin, lmax = 31.948, 41.948
tol = 20.0
screen_mid = 61.0
print(f"  T1 range: {lmin}-{lmax}m, tol=±{tol}m => {lmin-tol} to {lmax+tol}")
print(f"  HAIFENG 09130311 screen_mid={screen_mid}m => in range: {lmin-tol <= screen_mid <= lmax+tol}")
# Look for closer/better candidate
show_all_candidates('XINXING', lmin, lmax, is_t=True, label="T1")

# GUANGFU F1 detail: check JIULONG 09040211 depth validity
print("\n=== GUANGFU F1 check: JIULONG 09040211 depth validity ===")
lmin2, lmax2 = 28.926, 31.618
tol2 = 15.0
screen_mid2 = 14.0
print(f"  F1 range: {lmin2}-{lmax2}m, tol=±{tol2}m => {lmin2-tol2} to {lmax2+tol2}")
print(f"  JIULONG 09040211 screen_mid={screen_mid2}m => in range: {lmin2-tol2 <= screen_mid2 <= lmax2+tol2}")
# Also check FANGCAO 09030211 screen range [9-50m], the old well
print(f"  Old FANGCAO 09030211 screen_mid=29.5m => in range: {lmin2-tol2 <= 29.5 <= lmax2+tol2}")

# Also see if GUANGFU xcorr has any closer candidates
show_all_candidates('GUANGFU', lmin2, lmax2, is_t=False, label="F1")
