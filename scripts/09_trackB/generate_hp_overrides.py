"""Generate hp_inicial_overrides.json from full 2000-2025 GWL timeseries.

Computes the true preconsolidation head (max GWL depth) for each 2STOOL input file
by using the full daily piezometric head record converted to depth via well elevation.

Usage:
    conda run -n isce_ncu3 python scripts/09_trackB/generate_hp_overrides.py
"""
import json
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
INPUT_DIR = PROJECT_ROOT / "data" / "gwl" / "2stool_inputs"
FLAT_CSV = PROJECT_ROOT / "data" / "gwl" / "well_info" / "gwl_allwells_flat.csv"
ASSIGNMENT_CSV = PROJECT_ROOT / "data" / "gwl" / "gwl_to_mlcw_layer_assignment.csv"
OUTPUT_JSON = INPUT_DIR / "hp_inicial_overrides.json"


def main():
    flat = pd.read_csv(FLAT_CSV, dtype={"wellcode": str})
    assignment = pd.read_csv(ASSIGNMENT_CSV, dtype={"assigned_wellcode": str})

    # Build mapping: wellcode → elevation
    elev_map = {}
    for _, row in flat.iterrows():
        wc = str(row["wellcode"])
        elev = row.get("elev_leveling_m")
        if pd.notna(elev):
            elev_map[wc] = float(elev)

    # Build mapping: (station, layer) → (assigned_wellcode, ts_file)
    layer_well = {}
    for _, row in assignment.iterrows():
        key = (row["station"], row["layer"])
        feather_path = row.get("feather_file", "")
        if pd.isna(feather_path) or not feather_path:
            feather_path = f"data/gwl/well_timeseries/{row['station']}_gwl_timeseries.feather"
        ts_file = PROJECT_ROOT / str(feather_path)
        layer_well[key] = (str(row["assigned_wellcode"]), ts_file)

    overrides = {}
    ts_files_loaded = {}

    # Find all 2STOOL input files
    for xlsx_path in sorted(INPUT_DIR.glob("2STOOL_*.xlsx")):
        stem = xlsx_path.stem  # e.g. "2STOOL_TUKU_F1"
        parts = stem.split("_", 2)
        if len(parts) != 3:
            continue
        station, layer = parts[1], parts[2]

        # Find the assigned wellcode and ts_file for this station+layer
        lw_key = (station, layer)
        lw_info = layer_well.get(lw_key)
        if lw_info is None:
            continue
        wellcode, ts_file = lw_info

        elev = elev_map.get(wellcode)
        if elev is None:
            continue

        # Load timeseries (cached — handles proxy stations)
        if ts_file not in ts_files_loaded:
            if ts_file.exists():
                df = pd.read_feather(ts_file)
                ts_files_loaded[ts_file] = df
            else:
                continue
        df = ts_files_loaded[ts_file]

        if wellcode not in df.columns:
            continue

        # Convert piezometric head (m elevation) → GWL depth (m below surface)
        gwl_depth = elev - df[wellcode]
        hp = float(gwl_depth.max())
        overrides[stem] = round(hp, 3)

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w") as f:
        json.dump(overrides, f, indent=2)

    n_inputs = len(list(INPUT_DIR.glob("2STOOL_*.xlsx")))
    print(f"Generated {len(overrides)}/{n_inputs} overrides → {OUTPUT_JSON}")
    if overrides:
        sample = list(overrides.items())[0]
        print(f"  e.g. {sample[0]}: hp_inicial = {sample[1]} m")


if __name__ == "__main__":
    main()
