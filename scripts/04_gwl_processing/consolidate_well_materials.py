"""
Consolidate all individual well_materials TXT files into a single CSV with
Chinese → English translation of the BME-modelled aquifer layer descriptions.

Input:  data/gwl/well_materials/*.txt   (95 files, one per GWL station)
Output: data/gwl/well_materials_summary.csv
"""

import re
import csv
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

IN_DIR = PROJECT_ROOT / "data" / "gwl" / "well_materials"
OUT_PATH = PROJECT_ROOT / "data" / "gwl" / "well_materials_summary.csv"

# Translation: replace Chinese substrings with English
TRANSLATIONS = [
    ("濁水溪沖積扇", "Choushui River Alluvial Fan"),
    ("嘉南平原", "Chianan Plain"),
    ("BME(貝式最大熵法)", "BME (Bayesian Maximum Entropy)"),
    ("_Rockwork", "_Rockwork"),   # already English, no-op (kept for clarity)
]

rows = []
files_ok = 0
files_skip = 0

for txt_path in sorted(IN_DIR.glob("*.txt")):
    station = txt_path.stem.upper()
    text = txt_path.read_text(encoding="utf-8").strip()
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    if len(lines) < 4:
        print(f"  SKIP {station}: only {len(lines)} lines")
        files_skip += 1
        continue

    # --- Line 1: region / model ---
    region_model_raw = lines[0]
    region_model_en = region_model_raw
    for cn, en in TRANSLATIONS:
        region_model_en = region_model_en.replace(cn, en)

    # --- Line 2: coordinates ---
    coord_match = re.search(r"(\d+)\s*,\s*(\d+)", lines[1])
    if not coord_match:
        print(f"  SKIP {station}: cannot parse coordinates from line 2")
        files_skip += 1
        continue
    x_twd97 = int(coord_match.group(1))
    y_twd97 = int(coord_match.group(2))

    # --- Line 3: surface elevation ---
    elev_match = re.search(r"(\d+(?:\.\d+)?)\s*公尺", lines[2])
    surface_elevation_m = float(elev_match.group(1)) if elev_match else None

    # --- Line 4: total aquifer count ---
    count_match = re.search(r"富水層共有\s*(\d+)\s*層", lines[3])
    total_aquifers = int(count_match.group(1)) if count_match else 0
    shows_all = "前5層分別為" not in lines[3]  # "前5層分別為" = "first 5 layers are:"

    # --- Lines 5+: individual layers ---
    for li in range(4, len(lines)):
        line = lines[li]

        # Pattern A: "地下約X公尺，厚度約Y公尺"  (below ground)
        match_a = re.search(
            r"第\s*(\d+)\s*層[：:]\s*地下約\s*(\d+(?:\.\d+)?)\s*公尺[，,]\s*厚度約\s*(\d+(?:\.\d+)?)\s*公尺",
            line,
        )
        # Pattern B: "地表，厚度約Y公尺"  (ground surface, depth = 0)
        match_b = re.search(
            r"第\s*(\d+)\s*層[：:]\s*地表[，,]\s*厚度約\s*(\d+(?:\.\d+)?)\s*公尺",
            line,
        )

        if match_a:
            layer_num = int(match_a.group(1))
            layer_depth_m = float(match_a.group(2))
            layer_thickness_m = float(match_a.group(3))
        elif match_b:
            layer_num = int(match_b.group(1))
            layer_depth_m = 0.0
            layer_thickness_m = float(match_b.group(2))
        else:
            continue

        rows.append({
            "station": station,
            "region_model_en": region_model_en,
            "region_model_zh": region_model_raw,
            "x_twd97": x_twd97,
            "y_twd97": y_twd97,
            "surface_elevation_m": surface_elevation_m,
            "total_aquifers_within_200m": total_aquifers,
            "shows_all_layers": shows_all,
            "layer_number": layer_num,
            "layer_depth_m": layer_depth_m,
            "layer_thickness_m": layer_thickness_m,
        })

    files_ok += 1

# Write CSV
fieldnames = [
    "station", "region_model_en", "region_model_zh",
    "x_twd97", "y_twd97", "surface_elevation_m",
    "total_aquifers_within_200m", "shows_all_layers",
    "layer_number", "layer_depth_m", "layer_thickness_m",
]

with open(OUT_PATH, "w", newline="", encoding="utf-8") as fh:
    writer = csv.DictWriter(fh, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

# Summary
n_stations = len(set(r["station"] for r in rows))
n_layers = len(rows)
print(f"Files processed : {files_ok} ok, {files_skip} skipped")
print(f"Output stations : {n_stations}")
print(f"Output rows     : {n_layers}")
print(f"Output path     : {OUT_PATH}")
