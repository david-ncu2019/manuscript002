"""
Task P3: Extract 112_BME hydrofacies model values at the 39 MLCW station locations.

Input files:
  D:\1000_SCRIPTS\MyPlayGround\20260510_temp\112_BME_CRAF.csv
      Columns: x, y, depth, material_code
      1m depth resolution, full Choushui Fan, depth range 0-300 m

  D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\alpha_comparison_all_stations_v3.csv
      Columns: Ename, ..., X_TWD97, Y_TWD97
      39 MLCW stations with TWD97 coordinates

Output file:
  D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\mlcw_hydrofacies_5m.csv
      Columns: station, x_twd97, y_twd97, depth_m, material_code, material_class
      2340 rows: 39 stations x 60 depth levels (0 to 295 m, 5 m steps)
      All depths 0-295 m have material_code populated from 112_BME model.

Method:
  1. For each MLCW station, find the nearest 112_BME grid cell by Euclidean distance
     in TWD97 (x, y). The grid step is 500 m so the maximum error is ~354 m (half-diagonal).
  2. Extract all 1m depth levels (0-299 m) for that grid cell.
  3. Aggregate to 5m bins by taking the modal material_code within each 5m window.
     Bins: depth_m=0 covers raw depths 0-4m; depth_m=5 covers 5-9m; etc.
  4. Assign material_class strings from material_code ranges.
  5. Write output CSV with one row per (station, depth_m).
"""

from pathlib import Path
from scipy.stats import mode
import numpy as np
import pandas as pd

BME_CSV   = Path(r"D:\1000_SCRIPTS\MyPlayGround\20260510_temp\112_BME_CRAF.csv")
ALPHA_CSV = Path(r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\alpha_comparison_all_stations_v3.csv")
OUT_CSV   = Path(r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\mlcw_hydrofacies_5m.csv")

MATERIAL_CLASS = {
    1: "Clay",
    2: "Mud",
    3: "Silt",
    4: "Fine Sand",
    5: "Fine Sand",
    6: "Medium Sand",
    7: "Coarse Sand",
    8: "Gravel",
    9: "Gravel",
    10: "Gravel",
    11: "Gravel",
    12: "Gravel",
    13: "Bedrock",
    14: "Fill",
    15: "Fill",
}

MLCW_DEPTHS = list(range(0, 300, 5))  # 0, 5, 10, ..., 295  (60 levels)


def classify(code):
    if pd.isna(code):
        return "No data"
    return MATERIAL_CLASS.get(int(code), f"Unknown ({int(code)})")


def modal_code(arr):
    """Return the modal integer material code in arr, or NaN if empty."""
    arr = arr[~np.isnan(arr)].astype(int)
    if len(arr) == 0:
        return np.nan
    result = mode(arr, keepdims=True)
    return int(result.mode[0])


def main():
    print("Loading 112_BME model...")
    bme = pd.read_csv(BME_CSV)
    print(f"  {len(bme):,} voxel rows; depth range {bme['depth'].min()}-{bme['depth'].max()} m")

    print("Loading MLCW station coordinates...")
    alpha = pd.read_csv(ALPHA_CSV, usecols=["Ename", "X_TWD97", "Y_TWD97"])
    alpha.columns = ["station", "x_twd97", "y_twd97"]
    print(f"  {len(alpha)} stations")

    # Unique (x, y) grid cells in the BME model
    grid_xy = bme[["x", "y"]].drop_duplicates().values

    records = []
    for _, row in alpha.iterrows():
        station = row["station"]
        sx, sy = row["x_twd97"], row["y_twd97"]

        # Nearest BME grid cell
        dist = np.sqrt((grid_xy[:, 0] - sx) ** 2 + (grid_xy[:, 1] - sy) ** 2)
        nearest_idx = np.argmin(dist)
        gx, gy = grid_xy[nearest_idx]
        nearest_dist = dist[nearest_idx]

        # Extract all 1m rows for this cell
        cell = bme[(bme["x"] == gx) & (bme["y"] == gy)].copy()

        for d in MLCW_DEPTHS:
            # 5m bin covers raw depths d, d+1, ..., d+4
            bin_rows = cell[(cell["depth"] >= d) & (cell["depth"] < d + 5)]
            code = modal_code(bin_rows["material_code"].values)
            records.append({
                "station": station,
                "x_twd97": sx,
                "y_twd97": sy,
                "depth_m": d,
                "nearest_bme_dist_m": round(nearest_dist, 1),
                "material_code": code if not np.isnan(code) else np.nan,
                "material_class": classify(code),
            })

        print(f"  {station}: nearest BME cell ({gx}, {gy}), dist={nearest_dist:.0f} m")

    out = pd.DataFrame(records)
    out.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    print(f"\nWritten: {OUT_CSV}")
    print(f"  {len(out)} rows ({len(alpha)} stations x {len(MLCW_DEPTHS)} depths)")

    # Quick check
    covered = out[out["material_code"].notna()]
    no_data = out[out["material_code"].isna()]
    print(f"  Depths with BME data: {covered['depth_m'].nunique()} levels, {len(covered)} rows")
    print(f"  Depths without BME data: {no_data['depth_m'].nunique()} levels, {len(no_data)} rows")

    # Material distribution summary
    print("\nMaterial class distribution:")
    print(covered["material_class"].value_counts().to_string())


if __name__ == "__main__":
    main()
