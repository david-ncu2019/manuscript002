"""
Generate gwl_to_mlcw_layer_assignment.csv from scratch.

For each MLCW station + layer, searches ALL GWL stations within 10 km and
picks the best well by screen-depth match quality, using 2D distance only
as a tiebreaker.  This replaces the old two-phase approach (co-located first,
then nearest-proxy fallback for blocked stations).

Inputs:
  - data/mlcw/MLCW_InSAR_GWL_pairs.xlsx          (sheet: all_pairs_10km)
  - data/mlcw/group_byLayer_reconstr/{STATION}_classify_table.csv  (37 stations)
  - data/gwl/well_info/gwl_allwells_flat.csv     (well screen depths)

Output:
  - data/gwl/gwl_to_mlcw_layer_assignment.csv   (overwritten)

Approach:
  - For each (station, layer) pair, iterate over every GWL station within 10 km.
  - Score each well at that GWL station by:
      1. DIRECT_MATCH   if screen midpoint inside layer  → score = (0, dist_2d_m)
      2. NEAREST_FALLBACK                                 → score = (depth_gap_m, dist_2d_m)
  - Pick the well with the lowest score tuple.
  - A new column `dist_to_gwl_m` records the 2D distance to the chosen GWL station.
"""

import pandas as pd
import numpy as np
import csv
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# ── Paths ──────────────────────────────────────────────────────────
ASSIGN_PATH  = PROJECT_ROOT / "data/gwl/gwl_to_mlcw_layer_assignment.csv"
# Fallback if original is locked (e.g. open in Excel on host OS)
ASSIGN_PATH_V2 = PROJECT_ROOT / "data/gwl/gwl_to_mlcw_layer_assignment_v2.csv"
ASSIGN_JSON  = PROJECT_ROOT / "data/gwl/gwl_to_mlcw_layer_assignment.json"
PAIRS_PATH   = PROJECT_ROOT / "data/mlcw/MLCW_InSAR_GWL_pairs.xlsx"
FLAT_PATH    = PROJECT_ROOT / "data/gwl/well_info/gwl_allwells_flat.csv"
CLASSIFY_DIR = PROJECT_ROOT / "data/mlcw/group_byLayer_reconstr"

FEATHER_TEMPLATE = "data/gwl/well_timeseries/{stem}_gwl_timeseries.feather"

# ── Load ───────────────────────────────────────────────────────────
pairs = pd.read_excel(PAIRS_PATH, sheet_name="all_pairs_10km")
flat  = pd.read_csv(FLAT_PATH, dtype={"wellcode": str, "station": str})

# Pre-compute screen midpoint for every well
flat = flat.dropna(subset=["screen_top_m", "screen_bot_m"]).copy()
flat["screen_mid"] = (flat["screen_top_m"] + flat["screen_bot_m"]) / 2.0

# ── Build per-MLCW candidate list from pairs ────────────────────────
# pairs columns: Code, Ename, gwl_feather_stem, n_wells, well_ids, dist_to_gwl_m, ...
# Group by MLCW station to get all candidate GWL stations with distances.
mlcw_candidates: dict[str, pd.DataFrame] = {}
for ename, grp in pairs.groupby("Ename"):
    mlcw_candidates[ename] = grp[["gwl_feather_stem", "dist_to_gwl_m", "well_ids"]].copy()

print(f"Loaded {len(mlcw_candidates)} MLCW stations with GWL candidates within 10 km")

# ── All 39 MLCW stations ───────────────────────────────────────────
all_mlcw = [
    "ANHE","ANNAN","BEICHEN","CANLIN","DONGGUANG","DONGSHI","ERLUN","FENGAN",
    "FENGRONG","GUANGFU","HAIFENG","HONGLUN","HUNAN","HUWEI","JIANYANG",
    "JIAXING","JINHU_XIN","JIUZHUANG","KECUO","LONGYAN","LUNFENG_XIN",
    "NANGUANG","NEILIAO","QIAOYI","TANQIFENXIAO","TUKU","XIGANG","XINGHUA",
    "XINJIE","XINPI","XINSHENG","XINXING","XIUTAN","XIZHOU","YIWU",
    "YUANCHANG","ZHENGMIN","ZHENNAN","ZHUTANG",
]

# ── Helper ──────────────────────────────────────────────────────────
def feather_path(stem: str) -> str:
    return FEATHER_TEMPLATE.format(stem=stem)


def score_well_for_layer(screen_mid: float, l_min: float, l_max: float,
                          dist_2d: float, is_own_station: bool):
    """
    Return a sortable score tuple for one well relative to one layer.

    Lower is better.  Primary key = depth match quality (0 = perfect),
    secondary = 2D distance.  Own-station wells get a small distance
    bonus so co-located data wins when depth match is equivalent.
    """
    if l_min <= screen_mid <= l_max:
        depth_score = 0.0          # DIRECT_MATCH
    else:
        depth_score = min(abs(screen_mid - l_min), abs(screen_mid - l_max))

    dist_bonus = dist_2d if is_own_station else dist_2d + 1.0
    return (depth_score, dist_bonus)


def find_best_well(mlcw_station: str, l_min: float, l_max: float):
    """
    Search all GWL stations within 10 km of *mlcw_station* and return the
    single best well for layer [l_min, l_max].  Returns a dict with all
    columns needed for one output row, or None if no candidate has valid
    screen depths.
    """
    candidates = mlcw_candidates.get(mlcw_station)
    if candidates is None or candidates.empty:
        return None

    best_score = (float("inf"), float("inf"))
    best = None

    for _, cand in candidates.iterrows():
        stem = cand["gwl_feather_stem"]
        dist_2d = cand["dist_to_gwl_m"]
        if pd.isna(stem) or pd.isna(dist_2d):
            continue

        # Get all wells at this GWL station
        station_wells = flat[flat["station"].str.upper() == str(stem).upper()]
        if station_wells.empty:
            continue

        is_own = (str(stem).upper() == mlcw_station.upper())

        for _, w in station_wells.iterrows():
            smid = w["screen_mid"]
            if pd.isna(smid) or smid == 0.0:
                # smid==0.0 means screen_top_m and screen_bot_m are both 0
                # (i.e. no valid screen depth data — skip)
                continue
            sc = score_well_for_layer(smid, l_min, l_max, dist_2d, is_own)
            if sc < best_score:
                best_score = sc
                depth_gap = sc[0]
                method = "DIRECT_MATCH" if depth_gap == 0.0 else "NEAREST_FALLBACK"
                if method == "DIRECT_MATCH":
                    note = (f"Screen mid {smid:.1f}m inside layer "
                            f"[{l_min:.0f}-{l_max:.0f}m]")
                else:
                    note = (f"No screen in layer range; nearest at {smid:.1f}m "
                            f"(dist={depth_gap:.1f}m)")
                best = {
                    "assigned_wellcode": str(w["wellcode"]).zfill(8),
                    "screen_top_m": w["screen_top_m"],
                    "screen_bot_m": w["screen_bot_m"],
                    "screen_mid_m": smid,
                    "screen_str": str(w.get("well_screen_str", "")),
                    "well_depth_m": w.get("well_depth_m", np.nan),
                    "assignment_method": method,
                    "note": note,
                    "gwl_feather_stem": stem,
                    "dist_to_gwl_m": dist_2d,
                }

    return best


# ── Build assignment rows ──────────────────────────────────────────
rows = []
blocked_stations = []

for mlcw_st in all_mlcw:
    classify_path = CLASSIFY_DIR / f"{mlcw_st}_classify_table.csv"
    if not classify_path.exists():
        print(f"  SKIP {mlcw_st}: no classify table")
        continue

    classify = pd.read_csv(classify_path)
    layers = classify.groupby("layer")["depth"].agg(["min", "max"])
    layers.columns = ["depth_min", "depth_max"]

    for layer_name, lr in layers.iterrows():
        l_min, l_max = lr["depth_min"], lr["depth_max"]

        best = find_best_well(mlcw_st, l_min, l_max)

        if best is None:
            rows.append({
                "station": mlcw_st,
                "layer": layer_name,
                "layer_depth_min_m": round(l_min, 3),
                "layer_depth_max_m": round(l_max, 3),
                "assigned_wellcode": "",
                "screen_top_m": np.nan,
                "screen_bot_m": np.nan,
                "screen_mid_m": np.nan,
                "screen_str": "",
                "well_depth_m": np.nan,
                "assignment_method": "FULLY_BLOCKED",
                "note": "No GWL station with valid screen depths within 10 km",
                "feather_file": "",
                "dist_to_gwl_m": np.nan,
            })
            if mlcw_st not in blocked_stations:
                blocked_stations.append(mlcw_st)
        else:
            stem = best.pop("gwl_feather_stem")
            rows.append({
                "station": mlcw_st,
                "layer": layer_name,
                "layer_depth_min_m": round(l_min, 3),
                "layer_depth_max_m": round(l_max, 3),
                "assigned_wellcode": best["assigned_wellcode"],
                "screen_top_m": best["screen_top_m"],
                "screen_bot_m": best["screen_bot_m"],
                "screen_mid_m": best["screen_mid_m"],
                "screen_str": best["screen_str"],
                "well_depth_m": best["well_depth_m"],
                "assignment_method": best["assignment_method"],
                "note": best["note"],
                "feather_file": feather_path(stem),
                "dist_to_gwl_m": round(best["dist_to_gwl_m"], 1),
            })

# ── Assemble DataFrame ─────────────────────────────────────────────
col_order = [
    "station", "layer", "layer_depth_min_m", "layer_depth_max_m",
    "assigned_wellcode", "screen_top_m", "screen_bot_m", "screen_mid_m",
    "screen_str", "well_depth_m", "assignment_method", "note",
    "feather_file", "dist_to_gwl_m",
]
df = pd.DataFrame(rows)[col_order]

# ── Guarantee 8-digit wellcodes in output (leading zeros survive CSV round-trip) ──
df["assigned_wellcode"] = df["assigned_wellcode"].apply(
    lambda x: str(x).zfill(8) if pd.notna(x) and x != "" else x
)

try:
    df.to_csv(ASSIGN_PATH, index=False)
    saved_to = ASSIGN_PATH
except PermissionError:
    df.to_csv(ASSIGN_PATH_V2, index=False)
    saved_to = ASSIGN_PATH_V2
    print("\n*** NOTE: primary path is locked (file open in Excel?). "
          "Saved to _v2 path instead. ***")

print(f"\nFinal output: {df.shape[0]} rows, {df['station'].nunique()} stations")
print(f"Saved to: {saved_to}")

# ── Save type-safe JSON sidecar (wellcodes survive intact in JSON) ──
json_cols = [
    "station", "layer", "assigned_wellcode", "feather_file",
    "assignment_method", "dist_to_gwl_m", "screen_mid_m",
    "layer_depth_min_m", "layer_depth_max_m",
]
df[json_cols].to_json(ASSIGN_JSON, orient="records", indent=2)
print(f"JSON sidecar saved to: {ASSIGN_JSON}")

# ── Summary ────────────────────────────────────────────────────────
print(f"\n=== Method counts ===")
print(df["assignment_method"].value_counts().to_string())

if blocked_stations:
    print(f"\nFULLY_BLOCKED stations ({len(blocked_stations)}): {blocked_stations}")

print(f"\n=== Per-row feather file diversity (stations using >1 feather) ===")
feather_counts = df.groupby("station")["feather_file"].nunique()
multi = feather_counts[feather_counts > 1]
if len(multi) > 0:
    for st, n in multi.items():
        files = df[df["station"] == st]["feather_file"].unique()
        print(f"  {st}: {n} feathers -> {[Path(f).stem for f in files]}")
else:
    print("  (all stations use a single feather file)")

print(f"\n=== Distance summary (dist_to_gwl_m) ===")
valid_dist = df["dist_to_gwl_m"].dropna()
print(f"  Min   : {valid_dist.min():.1f} m")
print(f"  Median: {valid_dist.median():.1f} m")
print(f"  Max   : {valid_dist.max():.1f} m")
far = df[df["dist_to_gwl_m"] > 5000]
if len(far) > 0:
    print(f"  Rows with dist > 5 km: {len(far)}")
    print(far[["station", "layer", "dist_to_gwl_m", "assigned_wellcode"]].to_string(index=False))
