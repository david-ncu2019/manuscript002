"""
Cross-station summary visualization for harmonic and wet/dry improvement analysis.

Reads harmonic_allstations_summary.json and wetdry_allstations_summary.json,
produces two 2-panel bar charts showing improvement percentages and depth-level
improvement fractions across all 39 stations.

Output: harmonic_summary_overview.png, wetdry_summary_overview.png
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ============================================================
# Configuration
# ============================================================

DATA_DIR = Path(r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\direct_ratio_MLCW_InSAR")
HARMONIC_JSON = DATA_DIR / "harmonic_allstations_summary.json"
WETDRY_JSON = DATA_DIR / "wetdry_allstations_summary.json"

OUTPUT_DIR = DATA_DIR
HARMONIC_OUTPUT = OUTPUT_DIR / "harmonic_summary_overview.png"
WETDRY_OUTPUT = OUTPUT_DIR / "wetdry_summary_overview.png"

DPI = 150
FIGSIZE = (16, 8)

# ============================================================
# Load JSON data
# ============================================================

def load_json(filepath):
    """Load JSON file and return as list of dicts."""
    with open(filepath, 'r') as f:
        return json.load(f)

harmonic_data = load_json(HARMONIC_JSON)
wetdry_data = load_json(WETDRY_JSON)

# Sort by station name for consistency
harmonic_data_sorted = sorted(harmonic_data, key=lambda x: x['station'])
wetdry_data_sorted = sorted(wetdry_data, key=lambda x: x['station'])

stations_harmonic = [d['station'] for d in harmonic_data_sorted]
stations_wetdry = [d['station'] for d in wetdry_data_sorted]

# ============================================================
# Harmonic visualization
# ============================================================

fig, axes = plt.subplots(2, 1, figsize=FIGSIZE)
fig.suptitle('Harmonic Decomposition: Cross-Station Improvement Summary', fontsize=14, fontweight='bold')

# Panel 1: overall_improvement_pct
improvement_pct = np.array([d['overall_improvement_pct'] for d in harmonic_data_sorted])
recommended = np.array([d['harmonic_recommended'] for d in harmonic_data_sorted])
colors = np.array(['#4CAF50' if r else '#CCCCCC' for r in recommended])

sorted_idx = np.argsort(improvement_pct)[::-1]
improvement_pct_sorted = improvement_pct[sorted_idx]
colors_sorted = colors[sorted_idx]
stations_sorted = [stations_harmonic[i] for i in sorted_idx]

axes[0].bar(range(len(improvement_pct_sorted)), improvement_pct_sorted, color=colors_sorted, width=0.8, edgecolor='black', linewidth=0.5)
axes[0].axhline(y=0, color='red', linestyle='--', linewidth=1.5, alpha=0.7)
axes[0].set_ylabel('Overall Improvement (%)', fontsize=11, fontweight='bold')
axes[0].set_xticks(range(len(stations_sorted)))
axes[0].set_xticklabels(stations_sorted, rotation=90, fontsize=7)
axes[0].grid(axis='y', alpha=0.3)

n_recommended_harmonic = int(recommended.sum())
axes[0].set_title(f'Overall RMSE Improvement (Green = recommended, N={n_recommended_harmonic}/39)', fontsize=10, fontweight='bold')

# Panel 2: frac_depths_improved
frac_depths = np.array([d['frac_depths_improved'] for d in harmonic_data_sorted])
frac_depths_sorted = frac_depths[sorted_idx]

axes[1].bar(range(len(frac_depths_sorted)), frac_depths_sorted, color=colors_sorted, width=0.8, edgecolor='black', linewidth=0.5)
axes[1].set_ylabel('Fraction of Depths Improved', fontsize=11, fontweight='bold')
axes[1].set_xlabel('Station (sorted by overall improvement)', fontsize=10)
axes[1].set_xticks(range(len(stations_sorted)))
axes[1].set_xticklabels(stations_sorted, rotation=90, fontsize=7)
axes[1].set_ylim([0, 1])
axes[1].grid(axis='y', alpha=0.3)
axes[1].set_title('Fraction of 60 Depth Levels with Improvement', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig(HARMONIC_OUTPUT, dpi=DPI, bbox_inches='tight')
print(f"Saved: {HARMONIC_OUTPUT}")
plt.close()

# ============================================================
# Wet/dry visualization
# ============================================================

fig, axes = plt.subplots(2, 1, figsize=FIGSIZE)
fig.suptitle('Wet/Dry Split: Cross-Station Improvement Summary', fontsize=14, fontweight='bold')

# Panel 1: total_rmse_improv_pct
improvement_pct_wetdry = np.array([d['total_rmse_improv_pct'] for d in wetdry_data_sorted])
recommended_wetdry = np.array([d['wetdry_recommended'] for d in wetdry_data_sorted])
colors_wetdry = np.array(['#00BCD4' if r else '#CCCCCC' for r in recommended_wetdry])

sorted_idx_wetdry = np.argsort(improvement_pct_wetdry)[::-1]
improvement_pct_wetdry_sorted = improvement_pct_wetdry[sorted_idx_wetdry]
colors_wetdry_sorted = colors_wetdry[sorted_idx_wetdry]
stations_wetdry_sorted = [stations_wetdry[i] for i in sorted_idx_wetdry]

axes[0].bar(range(len(improvement_pct_wetdry_sorted)), improvement_pct_wetdry_sorted, color=colors_wetdry_sorted, width=0.8, edgecolor='black', linewidth=0.5)
axes[0].axhline(y=0, color='red', linestyle='--', linewidth=1.5, alpha=0.7)
axes[0].set_ylabel('Total RMSE Improvement (%)', fontsize=11, fontweight='bold')
axes[0].set_xticks(range(len(stations_wetdry_sorted)))
axes[0].set_xticklabels(stations_wetdry_sorted, rotation=90, fontsize=7)
axes[0].grid(axis='y', alpha=0.3)

n_recommended_wetdry = int(recommended_wetdry.sum())
axes[0].set_title(f'Total RMSE Improvement (Teal = recommended, N={n_recommended_wetdry}/39)', fontsize=10, fontweight='bold')

# Panel 2: frac_depths_improved (wetdry)
frac_depths_wetdry = np.array([d['frac_depths_improved'] for d in wetdry_data_sorted])
frac_depths_wetdry_sorted = frac_depths_wetdry[sorted_idx_wetdry]

axes[1].bar(range(len(frac_depths_wetdry_sorted)), frac_depths_wetdry_sorted, color=colors_wetdry_sorted, width=0.8, edgecolor='black', linewidth=0.5)
axes[1].set_ylabel('Fraction of Depths Improved', fontsize=11, fontweight='bold')
axes[1].set_xlabel('Station (sorted by total RMSE improvement)', fontsize=10)
axes[1].set_xticks(range(len(stations_wetdry_sorted)))
axes[1].set_xticklabels(stations_wetdry_sorted, rotation=90, fontsize=7)
axes[1].set_ylim([0, 1])
axes[1].grid(axis='y', alpha=0.3)
axes[1].set_title('Fraction of 60 Depth Levels with Improvement', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig(WETDRY_OUTPUT, dpi=DPI, bbox_inches='tight')
print(f"Saved: {WETDRY_OUTPUT}")
plt.close()

# ============================================================
# Print summary
# ============================================================

print(f"\n{'='*60}")
print(f"Harmonic recommended: {n_recommended_harmonic}/39 stations")
print(f"Wet/dry recommended: {n_recommended_wetdry}/39 stations")
print(f"{'='*60}")
