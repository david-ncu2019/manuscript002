"""
Parse all 95 .txt files in GroundwaterWells_MaterialAssign/ and produce two output CSVs:
  1. gwl_material_summary.csv     — one row per station, up to 5 layer pairs
  2. gwl_material_aquifer_thickness.csv — aggregated thickness per station
"""

import re
import csv
from pathlib import Path

INPUT_DIR = Path(__file__).parent / "GroundwaterWells_MaterialAssign"
OUT_SUMMARY = Path(__file__).parent / "gwl_material_summary.csv"
OUT_THICKNESS = Path(__file__).parent / "gwl_material_aquifer_thickness.csv"

MLCW_STATIONS = {
    "ANHE", "ANNAN", "DONGGUANG", "DONGSHI", "ERLUN", "FENGRONG",
    "GUANGFU", "HAIFENG", "HONGLUN", "HUWEI", "JIAXING", "KECUO",
    "QIAOYI", "TUKU", "XIUTAN", "XIZHOU", "XINGHUA", "XIGANG",
    "YIWU", "ZHENGMIN", "ZHUTANG",
}

def parse_txt(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    station = path.stem.upper()

    # Line 0: source dataset (everything before the first dash-separated part if present)
    source = lines[0] if lines else ""

    # TWD97 coordinates: 位置： X , Y
    coord_match = re.search(r"位置：\s*([\d.]+)\s*,\s*([\d.]+)", text)
    x_twd97 = float(coord_match.group(1)) if coord_match else None
    y_twd97 = float(coord_match.group(2)) if coord_match else None

    # Elevation: 地表高程約為： N 公尺
    elev_match = re.search(r"地表高程約為：\s*([\d.]+)\s*公尺", text)
    elev_m = float(elev_match.group(1)) if elev_match else None

    # Total layer count: 富水層共有N層 or 無富水層
    no_layer = bool(re.search(r"無富水層", text))
    count_match = re.search(r"富水層共有\s*(\d+)\s*層", text)
    n_layers_total = 0 if no_layer else (int(count_match.group(1)) if count_match else 0)

    # Individual layers: 第 N 層： 地下約D公尺，厚度約T公尺
    layer_matches = re.findall(r"第\s*\d+\s*層：\s*地下約\s*([\d.]+)\s*公尺，厚度約\s*([\d.]+)\s*公尺", text)
    layers = [(float(m[0]), float(m[1])) for m in layer_matches]  # (top_m, thick_m)

    return {
        "station": station,
        "source_dataset": source,
        "x_twd97": x_twd97,
        "y_twd97": y_twd97,
        "elev_m": elev_m,
        "n_layers_total": n_layers_total,
        "layers": layers,  # up to 5 printed (may be fewer than n_layers_total)
        "is_mlcw_station": station in MLCW_STATIONS,
    }


def main():
    txt_files = sorted(INPUT_DIR.glob("*.txt"))
    print(f"Found {len(txt_files)} .txt files")

    records = [parse_txt(p) for p in txt_files]

    # --- Summary CSV (wide format, up to 5 layer pairs) ---
    summary_fields = ["station", "source_dataset", "x_twd97", "y_twd97", "elev_m",
                      "n_layers_total", "is_mlcw_station"]
    for i in range(1, 6):
        summary_fields += [f"layer{i}_top_m", f"layer{i}_thick_m"]

    with open(OUT_SUMMARY, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=summary_fields)
        writer.writeheader()
        for r in records:
            row = {k: r[k] for k in summary_fields if k in r}
            for i, (top, thick) in enumerate(r["layers"][:5], start=1):
                row[f"layer{i}_top_m"] = top
                row[f"layer{i}_thick_m"] = thick
            writer.writerow(row)

    print(f"Written: {OUT_SUMMARY}")

    # --- Thickness CSV (aggregated) ---
    thickness_fields = ["station", "source_dataset", "x_twd97", "y_twd97", "elev_m",
                        "n_layers_total", "n_layers_printed",
                        "total_aquifer_thickness_printed_m",
                        "cumulative_aquifer_fraction_printed",
                        "is_mlcw_station"]

    with open(OUT_THICKNESS, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=thickness_fields)
        writer.writeheader()
        for r in records:
            printed = r["layers"]
            total_thick = sum(t for _, t in printed)
            writer.writerow({
                "station": r["station"],
                "source_dataset": r["source_dataset"],
                "x_twd97": r["x_twd97"],
                "y_twd97": r["y_twd97"],
                "elev_m": r["elev_m"],
                "n_layers_total": r["n_layers_total"],
                "n_layers_printed": len(printed),
                "total_aquifer_thickness_printed_m": round(total_thick, 2),
                "cumulative_aquifer_fraction_printed": round(total_thick / 200, 4),
                "is_mlcw_station": r["is_mlcw_station"],
            })

    print(f"Written: {OUT_THICKNESS}")

    # Quick summary stats
    mlcw_overlap = [r for r in records if r["is_mlcw_station"]]
    no_aquifer = [r for r in records if r["n_layers_total"] == 0]
    print(f"\nStations: {len(records)} total, {len(mlcw_overlap)} MLCW overlap, "
          f"{len(no_aquifer)} with no aquifer layer in 0-200 m")
    print("No-aquifer stations:", [r["station"] for r in no_aquifer])


if __name__ == "__main__":
    main()
