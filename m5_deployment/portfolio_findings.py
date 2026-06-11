"""
portfolio_findings.py — M9.2 Portfolio Survey: GPS-only carrier across 29 stations.

Computes:
  1. Holdout RMSE distribution (overall + per layer).
  2. Carrier-fail cells: detrended_corr < 0.2 AND rmse_mm > class threshold.
  3. All-layers-fail stations.
  4. GPS-distance vs RMSE scatter + Pearson correlation.
  5. Writes summary/portfolio_findings.json and summary/rmse_vs_gps_distance.png.

Usage:
    $env:PYTHONPATH=""; conda run -n fafalab2 python m5_deployment/portfolio_findings.py
"""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import pandas as pd
from scipy.stats import pearsonr

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
M5_DIR = REPO_ROOT / "m5_deployment"
SUMMARY_DIR = M5_DIR / "summary"
SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = SUMMARY_DIR / "m5_gps_deployment_summary.csv"
JSON_PATH = SUMMARY_DIR / "m5_gps_deployment_summary.json"
MAP_PATH = M5_DIR / "station_file_map.json"
OUT_PNG = SUMMARY_DIR / "rmse_vs_gps_distance.png"
OUT_JSON = SUMMARY_DIR / "portfolio_findings.json"

# ---------------------------------------------------------------------------
# Class thresholds (thin vs thick layer)
# ---------------------------------------------------------------------------
THIN_LAYERS = {"F1", "T1", "T2", "F4"}   # threshold = 10 mm
THICK_LAYERS = {"F2", "F3"}               # threshold = 20 mm

def class_threshold(layer: str) -> float:
    return 10.0 if layer in THIN_LAYERS else 20.0


# ---------------------------------------------------------------------------
# Step 1 — Load data
# ---------------------------------------------------------------------------
print("=" * 60)
print("M9.2 Portfolio Findings — GPS-Only Carrier")
print("=" * 60)

df = pd.read_csv(CSV_PATH)
print(f"\nLoaded CSV: {len(df)} rows, {df['station'].nunique()} stations")
print(f"Columns: {list(df.columns)}")

with open(JSON_PATH, encoding="utf-8") as f:
    meta = json.load(f)
print(f"\nJSON metadata: {json.dumps(meta, indent=2)}")

with open(MAP_PATH, encoding="utf-8") as f:
    smap = json.load(f)
dist_map = {s: v["gps_distance_m"] for s, v in smap["stations"].items()}
print(f"\nLoaded station_file_map: {len(dist_map)} entries")


# ---------------------------------------------------------------------------
# Step 2 — Overall RMSE distribution (148 cells)
# ---------------------------------------------------------------------------
print("\n--- Portfolio RMSE distribution (all 148 cells) ---")
rmse = df["rmse_mm"]
stats_overall = {
    "n_cells": int(len(df)),
    "median_mm": float(round(rmse.median(), 4)),
    "q1_mm": float(round(rmse.quantile(0.25), 4)),
    "q3_mm": float(round(rmse.quantile(0.75), 4)),
    "min_mm": float(round(rmse.min(), 4)),
    "max_mm": float(round(rmse.max(), 4)),
}
print(f"  n       = {stats_overall['n_cells']}")
print(f"  median  = {stats_overall['median_mm']:.3f} mm")
print(f"  Q1      = {stats_overall['q1_mm']:.3f} mm")
print(f"  Q3      = {stats_overall['q3_mm']:.3f} mm")
print(f"  min     = {stats_overall['min_mm']:.3f} mm")
print(f"  max     = {stats_overall['max_mm']:.3f} mm")

# Per-layer distribution
print("\n--- Per-layer RMSE distribution ---")
layer_stats = {}
for layer, grp in df.groupby("layer"):
    r = grp["rmse_mm"]
    layer_stats[layer] = {
        "n_cells": int(len(grp)),
        "median_mm": float(round(r.median(), 4)),
        "q1_mm": float(round(r.quantile(0.25), 4)),
        "q3_mm": float(round(r.quantile(0.75), 4)),
        "min_mm": float(round(r.min(), 4)),
        "max_mm": float(round(r.max(), 4)),
    }
    print(
        f"  {layer:4s}: n={layer_stats[layer]['n_cells']:3d}, "
        f"median={layer_stats[layer]['median_mm']:.2f} mm, "
        f"Q1={layer_stats[layer]['q1_mm']:.2f}, Q3={layer_stats[layer]['q3_mm']:.2f} mm"
    )


# ---------------------------------------------------------------------------
# Step 3 — Carrier-fail cells
# ---------------------------------------------------------------------------
print("\n--- Carrier-fail cell analysis ---")

# Flag corr < 0.2
df["low_corr"] = df["detrended_corr"] < 0.2
df["threshold_mm"] = df["layer"].apply(class_threshold)
df["over_threshold"] = df["rmse_mm"] > df["threshold_mm"]
df["is_fail"] = df["low_corr"] & df["over_threshold"]

n_low_corr = int(df["low_corr"].sum())
n_fail = int(df["is_fail"].sum())
print(f"  Cells with detrended_corr < 0.2: {n_low_corr} / {len(df)}")
print(f"  True fail cells (corr<0.2 AND rmse>threshold): {n_fail} / {len(df)}")

fail_cells = df[df["is_fail"]][["station", "layer", "rmse_mm", "detrended_corr", "threshold_mm"]].copy()
fail_cells = fail_cells.sort_values(["station", "layer"])
print("\n  Fail cells:")
for _, row in fail_cells.iterrows():
    print(
        f"    {row['station']:15s} {row['layer']:3s}  "
        f"rmse={row['rmse_mm']:.2f} mm  corr={row['detrended_corr']:.3f}  "
        f"thresh={row['threshold_mm']:.0f} mm"
    )

# All-layers-fail stations: every layer at that station is a fail
station_fail_counts = df.groupby("station")["is_fail"].sum()
station_layer_counts = df.groupby("station")["layer"].count()
all_fail_stations = station_fail_counts[
    station_fail_counts == station_layer_counts
].index.tolist()
print(f"\n  All-layers-fail stations: {all_fail_stations}")

fail_cell_list = fail_cells[["station", "layer", "rmse_mm", "detrended_corr"]].to_dict("records")
for r in fail_cell_list:
    r["rmse_mm"] = round(r["rmse_mm"], 4)
    r["detrended_corr"] = round(r["detrended_corr"], 4)


# ---------------------------------------------------------------------------
# Step 4 — GPS-distance effect
# ---------------------------------------------------------------------------
print("\n--- GPS-distance vs RMSE ---")

# Join distance to df
df["gps_distance_m"] = df["station"].map(dist_map)
missing_dist = df[df["gps_distance_m"].isna()]["station"].unique().tolist()
if missing_dist:
    print(f"  WARNING: no distance for stations: {missing_dist}")

df_dist = df.dropna(subset=["gps_distance_m"]).copy()
n_dist = len(df_dist)
print(f"  Cells with distance data: {n_dist}")

r_val, p_val = pearsonr(df_dist["gps_distance_m"], df_dist["rmse_mm"])
print(f"  Pearson r (distance vs RMSE) = {r_val:.4f}  (p = {p_val:.4f}, n = {n_dist})")

# Scatter plot
matplotlib.rcParams.update({"font.size": 14})
tab10 = plt.cm.tab10
layer_order = sorted(df_dist["layer"].unique())
layer_colors = {l: tab10(i / max(len(layer_order) - 1, 1)) for i, l in enumerate(layer_order)}

fig, ax = plt.subplots(figsize=(10, 7))
for layer in layer_order:
    sub = df_dist[df_dist["layer"] == layer]
    ax.scatter(
        sub["gps_distance_m"],
        sub["rmse_mm"],
        label=layer,
        color=layer_colors[layer],
        s=60,
        alpha=0.75,
        edgecolors="k",
        linewidths=0.4,
    )

# Trend line
m, b = np.polyfit(df_dist["gps_distance_m"], df_dist["rmse_mm"], 1)
x_range = np.linspace(df_dist["gps_distance_m"].min(), df_dist["gps_distance_m"].max(), 200)
ax.plot(x_range, m * x_range + b, "k--", linewidth=1.5, label=f"OLS trend (r={r_val:.3f})")

ax.set_xlabel("GPS-to-well distance (m)", fontsize=14)
ax.set_ylabel("Holdout RMSE (mm)", fontsize=14)
ax.set_title(
    f"GPS-to-well distance vs holdout RMSE\n"
    f"GPS-only carrier, 29 stations, n={n_dist} cells, Pearson r = {r_val:.3f}",
    fontsize=13,
)
ax.grid(True, alpha=0.3)
ax.legend(title="Layer", fontsize=12, title_fontsize=12, loc="upper right")
plt.tight_layout()
fig.savefig(str(OUT_PNG), dpi=300)
plt.close(fig)
print(f"\n  Saved scatter: {OUT_PNG}")


# ---------------------------------------------------------------------------
# Step 5 — Persist JSON
# ---------------------------------------------------------------------------
findings = {
    "metadata": {
        "script": "m5_deployment/portfolio_findings.py",
        "date": "2026-06-11",
        "source_csv": str(CSV_PATH.relative_to(REPO_ROOT)),
        "source_json": str(JSON_PATH.relative_to(REPO_ROOT)),
        "source_map": str(MAP_PATH.relative_to(REPO_ROOT)),
        "n_stations": int(df["station"].nunique()),
        "n_cells": int(len(df)),
    },
    "overall_rmse_distribution": stats_overall,
    "per_layer_rmse_distribution": layer_stats,
    "fail_analysis": {
        "n_low_corr_cells": n_low_corr,
        "n_true_fail_cells": n_fail,
        "fail_cell_list": fail_cell_list,
        "all_layers_fail_stations": all_fail_stations,
        "class_thresholds_mm": {"thin_F1_T1_T2_F4": 10, "thick_F2_F3": 20},
    },
    "gps_distance_effect": {
        "n_cells": n_dist,
        "pearson_r": float(round(r_val, 4)),
        "p_value": float(round(p_val, 4)),
        "ols_slope_mm_per_m": float(round(m, 6)),
        "ols_intercept_mm": float(round(b, 4)),
        "interpretation": (
            "Weak positive correlation between GPS-to-well distance and holdout RMSE. "
            "The hypothesis that closer GPS stations produce lower RMSE receives only marginal "
            "support at portfolio level; within-station layer variability dominates over "
            "the between-station distance effect."
        ),
        "scatter_png": str(OUT_PNG.relative_to(REPO_ROOT)),
    },
}

with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(findings, f, indent=2, ensure_ascii=False)
print(f"\n  Saved: {OUT_JSON}")


# ---------------------------------------------------------------------------
# Step 6 — Re-read JSON to confirm
# ---------------------------------------------------------------------------
print("\n--- Re-read confirmation ---")
with open(OUT_JSON, encoding="utf-8") as f:
    check = json.load(f)

assert check["overall_rmse_distribution"]["n_cells"] == len(df), "Cell count mismatch"
assert check["fail_analysis"]["n_true_fail_cells"] == n_fail, "Fail count mismatch"
assert check["gps_distance_effect"]["pearson_r"] == round(r_val, 4), "r mismatch"
print(f"  JSON confirmed: {len(df)} cells, {n_fail} fail cells, r = {round(r_val, 4)}")
print(f"\nDone. Portfolio findings written to {OUT_JSON}")
print(f"Scatter plot written to {OUT_PNG}")
