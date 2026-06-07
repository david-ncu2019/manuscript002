"""
OBSERVE phase script for v4 GWL-to-MLCW layer assignment.
Reads v3 CSV, xcorr parquets, and GWL feathers.
Outputs summary of coverage failures and FANGCAO stations.
"""
import pandas as pd
import numpy as np
import os
from pathlib import Path

BASE = Path(r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2")
V3_PATH = BASE / "data/gwl/gwl_to_mlcw_layer_assignment_v3.csv"
WELL_INFO_PATH = BASE / "data/gwl/well_info/gwl_allwells_flat.csv"
FEATHER_DIR = BASE / "data/gwl/well_timeseries"
XCORR_DIR = BASE / "results/ring_gwl_xcorr"

# Load v3
v3 = pd.read_csv(V3_PATH, dtype={"assigned_wellcode": str})
print(f"v3 rows: {len(v3)}")
print(f"Stations: {v3['station'].nunique()}")
print()

# FANGCAO rows
fangcao_rows = v3[v3['feather_file'].str.contains('FANGCAO', na=False)]
print("=== FANGCAO-dependent rows in v3 ===")
print(fangcao_rows[['station','layer','layer_depth_min_m','layer_depth_max_m','assigned_wellcode','screen_mid_m','dist_to_gwl_m','assignment_method']].to_string())
print()

# Check FANGCAO feather coverage
fangcao_feather = FEATHER_DIR / "FANGCAO_gwl_timeseries.feather"
df_fangcao = pd.read_feather(fangcao_feather)
df_fangcao.index = pd.to_datetime(df_fangcao['datetime']) if 'datetime' in df_fangcao.columns else df_fangcao.index
if 'datetime' in df_fangcao.columns:
    df_fangcao = df_fangcao.set_index('datetime')
print("FANGCAO feather columns:", [c for c in df_fangcao.columns if c != 'datetime'])
print("FANGCAO date range:", df_fangcao.index.min(), "to", df_fangcao.index.max())
# Check coverage per wellcode
for wc in ['09030211', '09030221']:
    if wc in df_fangcao.columns:
        s = df_fangcao[wc]
        n_2015_2022 = s['2015':'2022'].notna().sum()
        n_2023_2025 = s['2023':'2025'].notna().sum()
        print(f"  {wc}: 2015-2022={n_2015_2022}, 2023-2025={n_2023_2025}")
print()

# Now check all v3 assigned wells for coverage
print("=== Coverage check for all v3 assigned wells ===")
coverage_fails = []
for _, row in v3.iterrows():
    feather_path = BASE / row['feather_file']
    wellcode = str(row['assigned_wellcode']).zfill(8)
    if not feather_path.exists():
        print(f"  MISSING feather: {row['feather_file']} ({row['station']} {row['layer']})")
        continue
    df = pd.read_feather(feather_path)
    if 'datetime' in df.columns:
        df = df.set_index('datetime')
    df.index = pd.to_datetime(df.index)
    if wellcode not in df.columns:
        print(f"  MISSING wellcode {wellcode} in {row['feather_file']} ({row['station']} {row['layer']})")
        continue
    s = df[wellcode]
    n_2015_2022 = s.loc['2015-01-01':'2022-12-31'].notna().sum()
    n_2023_2025 = s.loc['2023-01-01':'2025-12-31'].notna().sum()
    if n_2023_2025 < 100:
        flag = 'COVERAGE_FAIL'
        coverage_fails.append({
            'station': row['station'], 'layer': row['layer'],
            'wellcode': wellcode, 'feather': row['feather_file'],
            'n_2015_2022': n_2015_2022, 'n_2023_2025': n_2023_2025
        })
        print(f"  COVERAGE_FAIL: {row['station']} {row['layer']} wc={wellcode} "
              f"2015-2022={n_2015_2022} 2023-2025={n_2023_2025}")

print(f"\nTotal coverage fails: {len(coverage_fails)}")
