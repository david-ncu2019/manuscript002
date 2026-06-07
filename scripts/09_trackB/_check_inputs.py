"""Quick inspection script for planning the prepare_2stool_inputs update."""
import pandas as pd
from pathlib import Path

BASE = Path("D:/1000_SCRIPTS/004_Project003/20260427_InSAR_MLCW_v2")
assign = pd.read_csv(BASE / "data/gwl/gwl_to_mlcw_layer_assignment_v3.csv",
                     dtype={"assigned_wellcode": str})
gts_dir = BASE / "data/gwl/mlcw_gwl_timeseries"

# Count total feather files
all_feathers = list(gts_dir.glob("*.feather"))
print(f"Total feather files in mlcw_gwl_timeseries: {len(all_feathers)}")

# Check TUKU
tuku_rows = assign[assign["station"] == "TUKU"]
print("\nTUKU rows in assignment:")
print(tuku_rows[["station", "layer", "assigned_wellcode"]].to_string())

print("\nTUKU feather resolution:")
for _, row in tuku_rows.iterrows():
    wc = str(row["assigned_wellcode"]).strip().zfill(8)
    matches = list(gts_dir.glob(f"TUKU_*_{wc}.feather"))
    layer = row["layer"]
    print(f"  layer={layer} wellcode={wc} -> {[m.name for m in matches]}")

# Check all stations - how many can be resolved
print("\nChecking all 195 assignment rows for feather resolution:")
n_found = 0
n_missing = 0
missing_list = []
for _, row in assign.iterrows():
    st = row["station"]
    wc = str(row["assigned_wellcode"]).strip().zfill(8)
    ly = row["layer"]
    matches = list(gts_dir.glob(f"{st}_*_{wc}.feather"))
    if matches:
        n_found += 1
    else:
        n_missing += 1
        missing_list.append(f"{st}_{ly} wellcode={wc}")

print(f"  Found: {n_found}, Missing: {n_missing}")
if missing_list:
    print("  Missing:")
    for m in missing_list[:20]:
        print(f"    {m}")

# Check orig_grouped files
orig_dir = BASE / "data/mlcw/group_byLayer_orig"
orig_files = list(orig_dir.glob("*_orig_grouped.csv"))
stations_with_orig = [f.stem.replace("_orig_grouped", "") for f in orig_files]
print(f"\nStations with orig_grouped: {len(stations_with_orig)}")

# Check which assignment stations have orig_grouped
assign_stations = sorted(assign["station"].unique())
missing_orig = [s for s in assign_stations if s not in stations_with_orig]
print(f"Assignment stations without orig_grouped: {missing_orig}")
