import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2")
FEATHER_DIR = BASE / "data/gwl/well_timeseries"
XCORR_DIR = BASE / "results/ring_gwl_xcorr"

# Check GUANGFU xcorr for F1 layer [28.926-31.618m]
xcorr_path = XCORR_DIR / "GUANGFU_ring_gwl_xcorr.parquet"
df = pd.read_parquet(xcorr_path)
df['gwl_wellcode'] = df['gwl_wellcode'].astype(str).str.zfill(8)

lmin, lmax = 28.926, 31.618
tol = 15.0

# Check 09040211 vs 09040212
for wc in ['09040211', '09040212']:
    rows = df[df['gwl_wellcode'] == wc].sort_values('dist_m')
    if not rows.empty:
        r = rows.iloc[0]
        print(f"JIULONG {wc}: screen_mid={r['screen_mid_m']} dist={r['dist_m']:.0f}m")
        # Check coverage
        fp = FEATHER_DIR / "JIULONG_gwl_timeseries.feather"
        dff = pd.read_feather(fp)
        if 'datetime' in dff.columns:
            dff = dff.set_index('datetime')
        dff.index = pd.to_datetime(dff.index)
        if wc in dff.columns:
            s = dff[wc]
            n15 = s.loc['2015-01-01':'2022-12-31'].notna().sum()
            n23 = s.loc['2023-01-01':'2025-12-31'].notna().sum()
            print(f"  n15={n15} n23={n23}")
        depth_ok_val = (r['screen_mid_m'] >= lmin - tol) and (r['screen_mid_m'] <= lmax + tol)
        print(f"  depth_ok={depth_ok_val} (range {lmin-tol:.1f} to {lmax+tol:.1f})")
    else:
        print(f"  {wc}: not in xcorr")

# Confirm sort order in find_best_candidate: 09040211 has dist=3101, 09040212 also 3101
# But 09040211 n23=591 while 09040212 n23=1095
# The sort is by depth_ok desc, dist asc - both have same dist and depth_ok=True
# The one that appears first in the dataframe gets selected
# We need to see which appears first
depth_ok_rows = df[
    (df['screen_mid_m'] >= lmin - tol) & (df['screen_mid_m'] <= lmax + tol)
].drop_duplicates(subset=['gwl_station', 'gwl_wellcode']).sort_values(['dist_m'])
print("\nDepth-ok candidates for GUANGFU F1 (sorted by dist):")
for _, r in depth_ok_rows.iterrows():
    wc = str(r['gwl_wellcode']).zfill(8)
    gs = r['gwl_station']
    fp = FEATHER_DIR / f"{gs}_gwl_timeseries.feather"
    if fp.exists():
        dff = pd.read_feather(fp)
        if 'datetime' in dff.columns:
            dff = dff.set_index('datetime')
        dff.index = pd.to_datetime(dff.index)
        if wc in dff.columns:
            s = dff[wc]
            n23 = int(s.loc['2023-01-01':'2025-12-31'].notna().sum())
        else:
            n23 = 0
    else:
        n23 = 0
    print(f"  {gs:12s} {wc} screen_mid={r['screen_mid_m']} dist={r['dist_m']:.0f}m n23={n23}")
