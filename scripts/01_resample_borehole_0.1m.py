#!/usr/bin/env python
"""
Resample TUKU borehole materials from 56 variable-thickness layers
into 3000 uniform 0.1 m slices (0.0 to 300.0 m).

Input:
    ../../001_data/mlcw/borehole_materials/YL_WSYL23G1_TUKU_土庫.xlsx
Output:
    ../results/TUKU_borehole_0.1m.csv

Columns: depth_top, depth_bot, depth_mid, SOIL_CATEGORY, SOIL_TYPE
3000 rows, 0.1 m resolution.
"""

from pathlib import Path
import pandas as pd
import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
METHOD_DIR = SCRIPT_DIR.parent
RESULTS_DIR = METHOD_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

INPUT = Path(__file__).resolve().parents[3] / "001_data" / "mlcw" / "borehole_materials" / "YL_WSYL23G1_TUKU_土庫.xlsx"
OUTPUT = RESULTS_DIR / "TUKU_borehole_0.1m.csv"

# Read source layers
layers = pd.read_excel(INPUT)
print(f"Read {len(layers)} layers, total thickness {layers['THICKNESS'].sum():.1f} m")
print(f"Depth range: {layers['TOP'].min():.1f} to {layers['BOTTOM'].max():.1f} m")

# Build 0.1 m intervals
step = 0.1
depth_starts = np.arange(0.0, 300.0, step)  # 0.0, 0.1, ..., 299.9
depth_ends = depth_starts + step              # 0.1, 0.2, ..., 300.0
depth_mids = depth_starts + step / 2          # 0.05, 0.15, ..., 299.95

n = len(depth_starts)
categories = np.empty(n, dtype=int)
types = np.empty(n, dtype=object)

# Vectorize: for each depth slice, find matching layer
# Uses searchsorted on layer TOP boundaries for speed
layer_tops = layers["TOP"].values
layer_bottoms = layers["BOTTOM"].values
layer_cats = layers["SOIL_CATEGORY"].values
layer_types = layers["SOIL_TYPE"].values

# Precompute depth_starts as array for broadcasting
d = depth_starts[:, np.newaxis]  # shape (3000, 1)
inside = (d >= layer_tops) & (d < layer_bottoms)  # shape (3000, 56)

# For each depth, find the first (and only) matching layer index
match_idx = inside.argmax(axis=1)

# Check that every depth matched exactly one layer
any_match = inside.any(axis=1)
if not any_match.all():
    bad_depths = depth_starts[~any_match]
    print(f"WARNING: {len(bad_depths)} depth slices with no matching layer:")
    for bd in bad_depths[:5]:
        print(f"  {bd:.1f} m")
    raise ValueError("Coverage failure: some depths fall outside all layers")

categories = layer_cats[match_idx]
types = layer_types[match_idx]

# Build output DataFrame
out = pd.DataFrame({
    "depth_top": np.round(depth_starts, 1),
    "depth_bot": np.round(depth_ends, 1),
    "depth_mid": np.round(depth_mids, 2),
    "SOIL_CATEGORY": categories,
    "SOIL_TYPE": types,
})

out.to_csv(OUTPUT, index=False)
print(f"\nWrote {len(out)} rows to {OUTPUT}")
print(f"Columns: {list(out.columns)}")
print(f"\nMaterial distribution:")
print(out["SOIL_TYPE"].value_counts().to_string())
print(f"\nDepth range: {out['depth_top'].min():.1f} to {out['depth_bot'].max():.1f} m")
print(f"First 5 rows:\n{out.head().to_string()}")
print(f"\nLast 5 rows:\n{out.tail().to_string()}")
