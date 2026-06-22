#!/usr/bin/env python
"""
Compute coarse/fine material percentages per uniform 50 m section.

Input:  ../raw_data/TUKU_borehole_0.1m.csv
        3000 rows, each 0.1 m thick, columns:
          depth_top, depth_bot, depth_mid, SOIL_CATEGORY, SOIL_TYPE

Output: ../results/TUKU_section_materials.csv
        6 rows (S1–S6), columns:
          section, depth_top, depth_bot, n_total, n_coarse, n_fine,
          coarse_pct, fine_pct

Classification (per 002_docs/references/borehole_soil_classification.md):
    Coarse (sand + gravel): SOIL_CATEGORY ∈ {1, 2, 3, 4}
    Fine   (silt + clay):   SOIL_CATEGORY ∈ {5, 6}

Usage:
    cd 012_ml_nowcast
    conda run -n fafalab2 python scripts/02_compute_section_materials.py
"""

from pathlib import Path
import pandas as pd

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
METHOD_DIR = SCRIPT_DIR.parent
RESULTS_DIR = METHOD_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

INPUT = METHOD_DIR / "raw_data" / "TUKU_borehole_0.1m.csv"
OUTPUT = RESULTS_DIR / "TUKU_section_materials.csv"

# Load borehole
bore = pd.read_csv(INPUT)
print(f"Loaded borehole data: {len(bore)} rows")
print(f"Columns: {list(bore.columns)}")

# Define sections
sections = [
    ("S1", 0, 50),
    ("S2", 50, 100),
    ("S3", 100, 150),
    ("S4", 150, 200),
    ("S5", 200, 250),
    ("S6", 250, 300),
]

# Coarse = categories 1–4, Fine = categories 5–6
COARSE = {1, 2, 3, 4}
FINE = {5, 6}

records = []
for name, top, bot in sections:
    mask = (bore["depth_mid"] >= top) & (bore["depth_mid"] < bot)
    subset = bore.loc[mask]
    n_total = len(subset)
    n_coarse = subset["SOIL_CATEGORY"].isin(COARSE).sum()
    n_fine = subset["SOIL_CATEGORY"].isin(FINE).sum()

    records.append(
        {
            "section": name,
            "depth_top": top,
            "depth_bot": bot,
            "n_total": n_total,
            "n_coarse": n_coarse,
            "n_fine": n_fine,
            "coarse_pct": round(n_coarse / n_total, 4),
            "fine_pct": round(n_fine / n_total, 4),
        }
    )

out = pd.DataFrame(records)
out["sand_pct"] = out["coarse_pct"]  # alias for readability
out["clay_pct"] = out["fine_pct"]    # alias: fine-grained = clay + silt

out.to_csv(OUTPUT, index=False)
print(f"\nWrote {len(out)} rows to {OUTPUT}\n")
print(out[["section", "depth_top", "depth_bot", "n_coarse", "n_fine", "sand_pct", "clay_pct"]].to_string(index=False))
