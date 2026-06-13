#!/usr/bin/env python3
"""
build_station_file_map.py — Build per-station file path mapping for M5 deployment.

Reads: MLCW_GPS_pairs.csv, ihmf_config.json, gwl_to_mlcw_layer_assignment_v4.csv,
       group_byLayer_reconstr/, borehole_materials/, gps/modeled/
Writes: m5_deployment/station_file_map.json
"""

import json
import os
import pandas as pd
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent  # repo root

# ── 1. Load GPS pairs ─────────────────────────────────────────────────────────
gps_pairs = pd.read_csv(ROOT / "data/mlcw/MLCW_GPS_pairs.csv")
gps_lookup = {}
for _, row in gps_pairs.iterrows():
    gps_lookup[row["Ename"]] = {
        "code": row["Code"],
        "gps_station": row["station_co"],
        "gps_distance_m": round(float(row["distance"]), 1),
    }

# ── 2. Load IHM-F config ──────────────────────────────────────────────────────
with open(ROOT / "data/ihmf_config.json") as f:
    config = json.load(f)

# Group entries by station
station_entries = defaultdict(list)
for entry in config["entries"]:
    station_entries[entry["station"]].append(entry)

# ── 3. Load layer assignment v4 ───────────────────────────────────────────────
assign_df = pd.read_csv(ROOT / "data/gwl/gwl_to_mlcw_layer_assignment_v4.csv")
assign_lookup = defaultdict(dict)
for _, row in assign_df.iterrows():
    assign_lookup[row["station"]][row["layer"]] = {
        "assigned_wellcode": str(row["assigned_wellcode"]),
        "assignment_method": row.get("assignment_method", ""),
        "xcorr_max": round(float(row.get("xcorr_max", 0) or 0), 3) if pd.notna(row.get("xcorr_max")) else None,
        "xcorr_lag_days": int(row.get("xcorr_lag_days", 0)) if pd.notna(row.get("xcorr_lag_days")) else None,
        "coverage_2015_2022": int(row.get("coverage_2015_2022", 0)) if pd.notna(row.get("coverage_2015_2022")) else None,
        "coverage_2023_2025": int(row.get("coverage_2023_2025", 0)) if pd.notna(row.get("coverage_2023_2025")) else None,
    }

# ── 4. MLCW reconstruction files ──────────────────────────────────────────────
recon_dir = ROOT / "data/mlcw/group_byLayer_reconstr"
recon_csvs = set(f.name for f in recon_dir.glob("*_reconst_grouped.csv"))
classify_csvs = set(f.name for f in recon_dir.glob("*_classify_table.csv"))

# ── 5. Borehole materials ─────────────────────────────────────────────────────
borehole_dir = ROOT / "data/mlcw/borehole_materials"
borehole_files = {}
if borehole_dir.exists():
    for f in borehole_dir.iterdir():
        if f.suffix == ".xlsx":
            # Filename contains station English name — extract it
            borehole_files[f.stem] = str(f.relative_to(ROOT))

def find_borehole(station_name):
    """Match borehole file by station English name in filename."""
    name_upper = station_name.upper()
    for stem, relpath in borehole_files.items():
        if name_upper in stem.upper():
            return relpath
    return None

# ── 6. GPS modeled files ──────────────────────────────────────────────────────
gps_dir = ROOT / "data/gps/modeled"
gps_modeled = set()
if gps_dir.exists():
    for f in gps_dir.glob("*_model.csv"):
        gps_modeled.add(f.stem.replace("_model", ""))

# ── 7. Assemble per-station mapping ───────────────────────────────────────────
stations = {}
for station, entries in sorted(station_entries.items()):
    gps_info = gps_lookup.get(station, {})
    gps_code = gps_info.get("gps_station", "")
    has_gps = gps_code in gps_modeled

    # Layers and their order
    layer_order = ["F1", "T1", "F2", "T2", "F3", "F4"]
    layers = sorted(set(e["layer"] for e in entries),
                    key=lambda x: layer_order.index(x) if x in layer_order else 99)

    # Per-layer GWL well info
    gwl_wells = {}
    for entry in entries:
        layer = entry["layer"]
        wellcode = entry.get("assigned_wellcode", "")
        # Get extra info from assignment CSV
        assign_info = assign_lookup.get(station, {}).get(layer, {})
        gwl_wells[layer] = {
            "wellcode": str(wellcode),
            "gwl_feather": entry.get("gwl_feather", ""),
            "tau_max": entry.get("tau_max", 12),
            "warmstart_ske": round(entry.get("warmstart_ske", 0), 8) if entry.get("warmstart_ske") else None,
            "warmstart_skv": round(entry.get("warmstart_skv", 0), 8) if entry.get("warmstart_skv") else None,
            "assignment_method": assign_info.get("assignment_method", ""),
            "xcorr_max": assign_info.get("xcorr_max"),
            "coverage_2015_2022": assign_info.get("coverage_2015_2022"),
            "coverage_2023_2025": assign_info.get("coverage_2023_2025"),
        }

    # MLCW file paths
    reconst_name = f"{station}_reconst_grouped.csv"
    classify_name = f"{station}_classify_table.csv"

    # Borehole
    borehole_path = find_borehole(station)

    # GPS
    gps_csv = f"data/gps/modeled/{gps_code}_model.csv" if has_gps else None

    stations[station] = {
        "code": gps_info.get("code", ""),
        "gps_station": gps_code,
        "gps_distance_m": gps_info.get("gps_distance_m"),
        "has_gps_modeled": has_gps,
        "n_layers": len(layers),
        "layers": layers,
        "files": {
            "mlcw_reconst_csv": f"data/mlcw/group_byLayer_reconstr/{reconst_name}",
            "mlcw_classify_csv": f"data/mlcw/group_byLayer_reconstr/{classify_name}",
            "borehole_xlsx": borehole_path,
            "has_borehole": borehole_path is not None,
            "gps_modeled_csv": gps_csv,
        },
        "gwl_wells": gwl_wells,
    }

# ── 8. Assemble final JSON ────────────────────────────────────────────────────
output = {
    "metadata": {
        "description": (
            "Per-station file path mapping for M5 Deployment Rehearsal and Part 2 "
            "batch processing. All paths relative to repo root. "
            "Read this JSON to discover all input files for any MLCW station."
        ),
        "created": "2026-06-10",
        "source_csv": "data/mlcw/MLCW_GPS_pairs.csv",
        "total_stations_mapped": len(stations),
        "stations_with_gps_modeled": sum(1 for s in stations.values() if s["has_gps_modeled"]),
        "stations_with_borehole": sum(1 for s in stations.values() if s["files"]["has_borehole"]),
        "stations_missing_gps": [s for s, v in stations.items() if not v["has_gps_modeled"]],
        "stations_missing_borehole": [s for s, v in stations.items() if not v["files"]["has_borehole"]],
        "excluded_stations": {
            "LUNFENG_XIN": "no config entries — exists in pairs CSV and borehole dir only",
            "JINHU_XIN": "no config entries — exists in pairs CSV and borehole dir only",
        },
    },
    "shared_files": {
        "insar_station_feather": "data/insar/mlcw_interp_insar_IDW_extend.feather",
        "insar_grid_feather": "data/insar/gridpnt_500m_interp_insar_IDW_extend.feather",
        "layer_assignment_csv": "data/gwl/gwl_to_mlcw_layer_assignment_v4.csv",
        "ihmf_config_json": "data/ihmf_config.json",
        "gps_pairs_csv": "data/mlcw/MLCW_GPS_pairs.csv",
        "gps_modeled_dir": "data/gps/modeled/",
        "gps_modeled_pattern": "{GPS_CODE}_model.csv",
        "gps_data_timeline_csv": "data/gps/GPS_data_timeline.csv",
        "mlcw_reconst_dir": "data/mlcw/group_byLayer_reconstr/",
        "mlcw_reconst_pattern": "{STATION}_reconst_grouped.csv",
        "mlcw_classify_pattern": "{STATION}_classify_table.csv",
        "borehole_dir": "data/mlcw/borehole_materials/",
        "gwl_well_timeseries_dir": "data/gwl/well_timeseries/",
    },
    "stations": stations,
}

# ── 9. Write ───────────────────────────────────────────────────────────────────
out_path = ROOT / "m5_deployment/station_file_map.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"Written: {out_path}")
print(f"Stations mapped: {len(stations)}")
print(f"With GPS modeled: {output['metadata']['stations_with_gps_modeled']}/37")
print(f"With borehole:    {output['metadata']['stations_with_borehole']}/37")
print(f"Missing GPS:      {output['metadata']['stations_missing_gps']}")
print(f"Missing borehole: {output['metadata']['stations_missing_borehole']}")
