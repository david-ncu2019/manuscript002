"""
build_mlcw_insar_gwl_pairs.py

Builds MLCW_InSAR_GWL_pairs.xlsx — pairing each of the 39 MLCW/InSAR stations
with their nearest GWL *station* (a cluster of co-located wells) from
well_info_combined_screenAvail.gpkg.

GWL station identity:
  Each well has a `well_name` like "豐榮(1)", "豐榮(2)", "豐榮(3)".
  The part before the "(n)" suffix is the Chinese station name (e.g. "豐榮").
  All wells sharing that Chinese station name are co-located at the same XY.

  The feather timeseries files in data/gwl/well_timeseries/ are named by the
  romanized station name (e.g. FENGRONG_gwl_timeseries.feather).
  Each feather file's non-datetime column headers are the computer_id values
  of the wells at that station.

  This script derives the feather stem for each well at runtime by building a
  reverse lookup: computer_id → feather_stem, from the column headers of all
  100 feather files. No manual translation table is needed.

  The output column `gwl_feather_stem` is the feather file stem
  (without "_gwl_timeseries.feather") that can be used directly to load data.

For each MLCW station:
  - Nearest single GWL station (any screen availability), with its feather stem
  - All GWL stations within 5 km radius, each with feather stem

CRS handling:
  - InSAR gpkg  : EPSG:32650 (WGS84 UTM Zone 50N)
  - GWL gpkg    : EPSG:3826  (TWD97 / TM2 Taiwan)
  Both are reprojected to a common CRS (EPSG:32650) for distance computation.

Outputs:
  data/mlcw/MLCW_InSAR_GWL_pairs.xlsx   — main pairing table (one row per MLCW station)
  data/mlcw/MLCW_InSAR_GWL_pairs_all.csv — expanded table (one row per MLCW-GWL station
                                             pair within 5 km)

Usage:
    conda run -n fafalab python scripts/05_pairing/build_mlcw_insar_gwl_pairs.py
"""

import pathlib, re
import pandas as pd
import geopandas as gpd
import numpy as np

BASE = pathlib.Path(__file__).resolve().parent.parent.parent

INSAR_GPKG   = BASE / "data/insar/timeseries/mlcw_interp_insar_IDW_extend.gpkg"
GWL_GPKG     = BASE / "data/gwl/well_info_combined_screenAvail_v3.gpkg"
FEATHER_DIR  = BASE / "data/gwl/well_timeseries"
OUT_DIR      = BASE / "data/mlcw"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RADIUS_M = 10000  # include all GWL stations within this radius in the expanded table

# ── build computer_id → feather_stem lookup from actual feather files ─────────
# Each feather file's non-datetime columns are the computer_ids of wells at that
# station. This reverse mapping is built at runtime — no manual table needed.
print("Building computer_id → feather_stem lookup from feather column headers ...")
cid_to_stem: dict[str, str] = {}
available_stems = set()
for f in sorted(FEATHER_DIR.glob("*_gwl_timeseries.feather")):
    stem = f.name.replace("_gwl_timeseries.feather", "")
    available_stems.add(stem)
    df = pd.read_feather(f)
    for col in df.columns:
        if col != "datetime":
            cid_to_stem[col] = stem
print(f"  {len(available_stems)} feather files, {len(cid_to_stem)} computer_id entries mapped")

def chinese_station_name(well_name: str) -> str:
    """Strip the trailing '(n)' suffix from well_name to get the station name."""
    return re.sub(r"\s*[\(\（][^)）]*[\)\）].*$", "", str(well_name)).strip()

# ── load data ─────────────────────────────────────────────────────────────────

print("Loading InSAR GeoPackage ...")
gdf_insar = gpd.read_file(INSAR_GPKG)
meta_cols = [c for c in gdf_insar.columns if not c.startswith("D20")]
gdf_insar = gdf_insar[meta_cols].copy()
print(f"  {len(gdf_insar)} MLCW stations  CRS: {gdf_insar.crs}")

print("Loading GWL GeoPackage ...")
gdf_gwl = gpd.read_file(GWL_GPKG)
print(f"  {len(gdf_gwl)} GWL wells  CRS: {gdf_gwl.crs}")

# ── derive station name and feather stem per well ──────────────────────────────
# v3 GPKG has 'station' (romanized) and 'wellcode' (matches feather column headers).
gdf_gwl["gwl_station_name_zh"] = gdf_gwl["station"]  # already romanized in v3
gdf_gwl["gwl_feather_stem"] = gdf_gwl["wellcode"].map(cid_to_stem)

# Report wells whose wellcode has no feather file
unmapped_wells = gdf_gwl[gdf_gwl["gwl_feather_stem"].isna()]
if len(unmapped_wells) > 0:
    print(f"\n  NOTE: {len(unmapped_wells)} wells have no feather timeseries "
          f"(their wellcode is absent from all feather column headers):")
    for _, r in unmapped_wells.iterrows():
        print(f"    {r['wellcode']:15s}  station={r['station']!r}")

print(f"\n  Unique station names: {gdf_gwl['gwl_station_name_zh'].nunique()}")
print(f"  Wells mapped to feather stem: {gdf_gwl['gwl_feather_stem'].notna().sum()} "
      f"/ {len(gdf_gwl)} total")

# ── dissolve GWL wells into stations ─────────────────────────────────────────
# Group by feather stem (the operational key for loading data).
# A Chinese station name may have some wells without a feather match (e.g. M-series
# or duplicate entries). Fill any NaN feather stem for a well by the feather stem
# of the other wells sharing the same Chinese station name, if any exists.
# Only if NO well in the group has a feather stem do we fall back to a sentinel.
stem_by_zh = (
    gdf_gwl.dropna(subset=["gwl_feather_stem"])
    .groupby("gwl_station_name_zh")["gwl_feather_stem"]
    .first()
)
gdf_gwl["gwl_feather_stem"] = gdf_gwl.apply(
    lambda r: r["gwl_feather_stem"]
              if pd.notna(r["gwl_feather_stem"])
              else stem_by_zh.get(r["gwl_station_name_zh"], None),
    axis=1,
)

gdf_gwl["_group_key"] = gdf_gwl["gwl_feather_stem"].fillna(
    "__no_feather__" + gdf_gwl["gwl_station_name_zh"]
)

def agg_join(s, sep="; "):
    vals = s.dropna().tolist()
    return sep.join(str(v) for v in vals) if vals else ""

gwl_station_agg = (
    gdf_gwl.groupby("_group_key", sort=False)
    .agg(
        gwl_feather_stem   = ("gwl_feather_stem",    "first"),
        gwl_station_name_zh= ("gwl_station_name_zh", "first"),
        x_twd97            = ("x_twd97",              "first"),
        y_twd97            = ("y_twd97",              "first"),
        well_elev_m        = ("well_elev_m",          "first"),
        n_wells            = ("wellcode",             "count"),
        well_ids           = ("wellcode",             lambda s: "; ".join(s.dropna())),
        screen_raw_all     = ("well_screen_str",      lambda s: "; ".join(s.dropna())),
        geometry           = ("geometry",             "first"),
    )
    .reset_index(drop=True)
)

gdf_gwl_stations = gpd.GeoDataFrame(gwl_station_agg, geometry="geometry", crs=gdf_gwl.crs)
print(f"\n  GWL dissolved to {len(gdf_gwl_stations)} stations")

# ── reproject GWL stations to match InSAR CRS (UTM50N) ───────────────────────
gdf_gwl_sta_utm = gdf_gwl_stations.to_crs(gdf_insar.crs)
print(f"  GWL stations reprojected to {gdf_insar.crs}")

# ── nearest GWL station per MLCW station ─────────────────────────────────────
print("\nComputing nearest GWL station for each MLCW station ...")

nearest = gpd.sjoin_nearest(
    gdf_insar,
    gdf_gwl_sta_utm[[
        "gwl_feather_stem", "gwl_station_name_zh",
        "x_twd97", "y_twd97", "well_elev_m",
        "n_wells", "well_ids", "screen_raw_all", "geometry"
    ]],
    how="left",
    distance_col="dist_to_nearest_gwl_m",
)
nearest = nearest.drop_duplicates(subset="Code").reset_index(drop=True)
nearest = nearest.rename(columns={"index_right": "gwl_station_index"})

# ── all GWL stations within RADIUS_M per MLCW station ────────────────────────
print(f"Computing all GWL stations within {RADIUS_M/1000:.0f} km of each MLCW station ...")

gdf_insar_buf = gdf_insar.copy()
gdf_insar_buf["geometry"] = gdf_insar_buf.geometry.buffer(RADIUS_M)

joined_all = gpd.sjoin(
    gdf_insar_buf[["Code", "Ename", "geometry"]],
    gdf_gwl_sta_utm[[
        "gwl_feather_stem", "gwl_station_name_zh",
        "n_wells", "well_ids", "screen_raw_all",
        "x_twd97", "y_twd97", "geometry"
    ]],
    how="left",
    predicate="contains",
)

# Compute exact point-to-point distances
insar_pts   = gdf_insar.set_index("Code")["geometry"]
gwl_sta_pts = gdf_gwl_sta_utm.set_index("gwl_feather_stem")["geometry"]

distances = []
for _, row in joined_all.iterrows():
    mlcw_pt = insar_pts.loc[row["Code"]]
    stem = row["gwl_feather_stem"]
    if pd.notna(stem) and stem in gwl_sta_pts.index:
        dist = mlcw_pt.distance(gwl_sta_pts.loc[stem])
    else:
        dist = np.nan
    distances.append(dist)

joined_all["dist_to_gwl_m"] = distances
joined_all = joined_all.sort_values(["Code", "dist_to_gwl_m"]).reset_index(drop=True)

expanded = joined_all[[
    "Code", "Ename",
    "gwl_feather_stem", "gwl_station_name_zh",
    "n_wells", "well_ids", "screen_raw_all",
    "x_twd97", "y_twd97", "dist_to_gwl_m"
]].copy()

# ── compact summary column ─────────────────────────────────────────────────────
def summarise_nearby_stations(grp):
    parts = []
    for _, r in grp.iterrows():
        if pd.notna(r["gwl_feather_stem"]):
            d = f"{r['dist_to_gwl_m']:.0f}" if pd.notna(r["dist_to_gwl_m"]) else "?"
            n = int(r["n_wells"]) if pd.notna(r["n_wells"]) else "?"
            parts.append(f"{r['gwl_feather_stem']} ({d} m, {n} wells)")
    return "; ".join(parts) if parts else ""

summary_series = expanded.groupby("Code").apply(
    summarise_nearby_stations, include_groups=False
)
n_nearby = (
    expanded.groupby("Code")["gwl_feather_stem"]
    .count()
    .rename("n_gwl_stations_10km")
)

# ── assemble main sheet ────────────────────────────────────────────────────────
main = nearest[[
    "Ename", "Code", "X_UTM50N", "Y_UTM50N",
    "gwl_feather_stem", "gwl_station_name_zh",
    "gwl_x_twd97", "gwl_y_twd97",
    "gwl_elev_m", "gwl_casing_depth_m",
    "gwl_n_wells", "gwl_well_ids",
    "gwl_screen_raw_all", "gwl_data_period",
    "dist_to_nearest_gwl_m",
]].copy() if "gwl_x_twd97" in nearest.columns else nearest[[
    "Ename", "Code", "X_UTM50N", "Y_UTM50N",
    "gwl_feather_stem", "gwl_station_name_zh",
    "x_twd97", "y_twd97",
    "well_elev_m",
    "n_wells", "well_ids",
    "screen_raw_all",
    "dist_to_nearest_gwl_m",
]].rename(columns={
    "x_twd97":        "gwl_x_twd97",
    "y_twd97":        "gwl_y_twd97",
    "well_elev_m":    "gwl_elev_m",
    "n_wells":        "gwl_n_wells",
    "well_ids":       "gwl_well_ids",
    "screen_raw_all": "gwl_screen_raw_all",
}).copy()

main = main.merge(n_nearby, on="Code", how="left")
main = main.merge(summary_series.rename("gwl_stations_within_10km"), on="Code", how="left")
main = main.sort_values("Ename").reset_index(drop=True)

# ── write outputs ──────────────────────────────────────────────────────────────
xlsx_path = OUT_DIR / "MLCW_InSAR_GWL_pairs.xlsx"
csv_path  = OUT_DIR / "MLCW_InSAR_GWL_pairs_all.csv"

with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
    main.to_excel(writer, sheet_name="MLCW_InSAR_GWL_pairs", index=False)
    expanded.to_excel(writer, sheet_name="all_pairs_10km", index=False)

expanded.to_csv(csv_path, index=False, encoding="utf-8-sig")

print(f"\nMain table  ({len(main)} rows)  -> {xlsx_path}")
print(f"Expanded CSV ({len(expanded)} rows) -> {csv_path}")

# ── quick summary ──────────────────────────────────────────────────────────────
print("\n--- MAIN TABLE PREVIEW ---")
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 220)
pd.set_option("display.max_colwidth", 30)
print(main[["Ename", "Code", "gwl_feather_stem", "gwl_station_name_zh",
            "dist_to_nearest_gwl_m", "gwl_n_wells",
            "n_gwl_stations_10km"]].to_string(index=False))

print(f"\nDistance to nearest GWL station:")
print(f"  Min   : {main['dist_to_nearest_gwl_m'].min():.1f} m")
print(f"  Median: {main['dist_to_nearest_gwl_m'].median():.1f} m")
print(f"  Max   : {main['dist_to_nearest_gwl_m'].max():.1f} m")
print(f"\nMLCW with nearest GWL station < 500 m : {(main['dist_to_nearest_gwl_m'] <  500).sum()}")
print(f"MLCW with nearest GWL station < 2000 m: {(main['dist_to_nearest_gwl_m'] < 2000).sum()}")
print(f"MLCW with nearest GWL station >= 2000 m: {(main['dist_to_nearest_gwl_m'] >= 2000).sum()}")

# ── feather coverage check ─────────────────────────────────────────────────────
print("\n--- FEATHER COVERAGE ---")
for _, row in main.iterrows():
    stem = row["gwl_feather_stem"]
    if pd.isna(stem):
        print(f"  {row['Ename']:20s}  NO feather stem mapped")
    elif stem not in available_stems:
        print(f"  {row['Ename']:20s}  stem='{stem}' — FILE NOT FOUND in well_timeseries/")
    # else: OK, silent
print("  (no output above = all nearest GWL stations have matching feather files)")
