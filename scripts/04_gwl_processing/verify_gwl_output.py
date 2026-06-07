import csv
from pathlib import Path

BASE = Path(r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2")

def read_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))

s = read_csv(BASE / "gwl_material_summary.csv")
t = read_csv(BASE / "gwl_material_aquifer_thickness.csv")

print(f"Summary CSV: {len(s)} rows x {len(s[0])} cols")
print(f"Thickness CSV: {len(t)} rows x {len(t[0])} cols")

print("\n--- MLCW-overlap stations (thickness) ---")
header = ["station", "n_layers_total", "n_layers_printed", "total_aquifer_thickness_printed_m", "cumulative_aquifer_fraction_printed"]
print("  ".join(f"{h:<42}" if i == 0 else f"{h:>10}" for i, h in enumerate(header)))
for row in t:
    if row["is_mlcw_station"] == "True":
        vals = [row[h] for h in header]
        print("  ".join(f"{v:<42}" if i == 0 else f"{v:>10}" for i, v in enumerate(vals)))

print("\n--- No-aquifer stations ---")
print([row["station"] for row in t if row["n_layers_total"] == "0"])

thicknesses = [float(row["total_aquifer_thickness_printed_m"]) for row in t]
fracs = [float(row["cumulative_aquifer_fraction_printed"]) for row in t]
print(f"\nThickness (all 95): min={min(thicknesses):.1f}  max={max(thicknesses):.1f}  mean={sum(thicknesses)/len(thicknesses):.1f} m")
print(f"Fraction  (all 95): min={min(fracs):.3f}  max={max(fracs):.3f}  mean={sum(fracs)/len(fracs):.3f}")
