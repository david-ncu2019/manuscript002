#!/usr/bin/env python
"""
viz_style.py — shared visual style for the 012_ml_nowcast figures.

Single source of truth for the depth palette, rcParams, axis styling, and the
train/val/test shading convention, so 06_plot_inputs.py and 07_plot_results.py
look identical. Library module (no digit prefix) — import normally:

    import viz_style as vs

Style choices (see plan / AGENTS.md working method):
- ONE depth palette S1..S6 reused everywhere (Tab10 layer order, shallow->deep).
- Diverging norm centered at 0 for signed fields.
- Shared-y within a unit group; never twinx() for same units.
- A reused train/val/test shading convention.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

DPI = 140

# Depth sections shallow (S1) -> deep (S6). Tab10 order matches the repo's
# de-facto LAYER_COLORS convention (F1 blue ... F4 brown), extended to 6 bands.
SECTION_COLORS = {
    "S1": "#1f77b4",  # blue   (0-50 m, shallowest)
    "S2": "#ff7f0e",  # orange (50-100)
    "S3": "#2ca02c",  # green  (100-150)
    "S4": "#d62728",  # red    (150-200)
    "S5": "#9467bd",  # purple (200-250)
    "S6": "#8c564b",  # brown  (250-300, deepest)
}
SECTIONS = list(SECTION_COLORS.keys())

# Train/val/test shading convention (learned once, reused on every time axis).
SPLIT_SHADE = {
    "train": (None, 0.0),          # left clear
    "val": ("#9e9e9e", 0.12),      # light grey
    "test": ("#fdd835", 0.14),     # light yellow
}

# Set colors for scatter (observed-vs-predicted etc.)
SET_COLORS = {"train": "#9e9e9e", "val": "#1f77b4", "test": "#d62728"}

# Sign colors for diverging bars (coefficients, signed magnitudes).
POS_COLOR = "#2166ac"  # blue  (+)
NEG_COLOR = "#b2182b"  # red   (-)


def apply_rcparams() -> None:
    """Project-consistent matplotlib defaults."""
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 11,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 8,
            "figure.dpi": 100,
            "savefig.dpi": DPI,
            "savefig.bbox": "tight",
        }
    )


def style_ax(ax) -> None:
    """Hide top/right spines, add a faint dashed grid."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, linestyle="--", alpha=0.3, color="gray")


def shade_splits(ax, train, val, test) -> None:
    """Shade val/test date ranges on a time axis. Each arg is (start, end) str/Timestamp."""
    import pandas as pd

    for name, span in (("val", val), ("test", test)):
        color, alpha = SPLIT_SHADE[name]
        if color is None:
            continue
        ax.axvspan(pd.Timestamp(span[0]), pd.Timestamp(span[1]),
                   color=color, alpha=alpha, lw=0, zorder=0)


def diverging_norm(vmax: float) -> TwoSlopeNorm:
    """Symmetric blue-white-red norm centered at 0 for signed fields."""
    vmax = abs(float(vmax)) or 1.0
    return TwoSlopeNorm(vmin=-vmax, vcenter=0.0, vmax=vmax)


def section_color(section: str) -> str:
    return SECTION_COLORS.get(section, "#333333")
