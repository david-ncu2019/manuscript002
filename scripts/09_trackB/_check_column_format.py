"""Check orig_grouped and feather column formats for a few stations."""
import pandas as pd
from pathlib import Path

BASE = Path("D:/1000_SCRIPTS/004_Project003/20260427_InSAR_MLCW_v2")
gts_dir = BASE / "data/gwl/mlcw_gwl_timeseries"
orig_dir = BASE / "data/mlcw/group_byLayer_orig"

for st in ["TUKU", "ANHE", "ANNAN"]:
    # orig grouped columns
    f = orig_dir / f"{st}_orig_grouped.csv"
    df = pd.read_csv(f, parse_dates=["datetime"])
    print(f"{st} orig_grouped: columns={df.columns.tolist()}, rows={len(df)}")
    print(f"  first date={df['datetime'].iloc[0]}, last={df['datetime'].iloc[-1]}")

    # check one feather
    feathers = list(gts_dir.glob(f"{st}_*.feather"))
    if feathers:
        gdf = pd.read_feather(feathers[0])
        print(f"  GWL feather: {feathers[0].name}, cols={gdf.columns.tolist()}, rows={len(gdf)}")
        print(f"  first date={gdf['datetime'].iloc[0]}, last={gdf['datetime'].iloc[-1]}")
    print()

# Check that dates match between orig_grouped and feather for TUKU
print("Date alignment check for TUKU F2:")
mlcw = pd.read_csv(orig_dir / "TUKU_orig_grouped.csv", parse_dates=["datetime"])
gwl = pd.read_feather(gts_dir / "TUKU_TUKU_09050321.feather")
common = set(mlcw["datetime"]).intersection(set(gwl["datetime"]))
print(f"  MLCW rows={len(mlcw)}, GWL rows={len(gwl)}, common={len(common)}")
print(f"  All MLCW dates in GWL? {set(mlcw['datetime']).issubset(set(gwl['datetime']))}")
