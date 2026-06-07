"""
plot_style.py — Shared matplotlib style settings for tau_demo_TUKU figures.

Import in all plotting scripts:
    from plot_style import DPI, A4_PORTRAIT, FONT, LW, style_ax, apply_style
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ── Dimensions ────────────────────────────────────────────────────────────────
DPI = 300
A4_PORTRAIT  = (8.27, 11.69)   # 210 × 297 mm
A4_LANDSCAPE = (11.69, 8.27)

# ── Font sizes ────────────────────────────────────────────────────────────────
FONT = {
    "suptitle": 16,
    "title":    13,
    "axis_label": 14,
    "tick":      12,
    "legend":    12,
    "annotation": 11,
}

# ── Line widths ───────────────────────────────────────────────────────────────
LW = {
    "data":       2.0,
    "reference":  1.2,
    "grid":       0.5,
    "spine":      1.0,
}


def style_ax(ax):
    """Remove top/right spines, set tick font size."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(LW["spine"])
    ax.spines["bottom"].set_linewidth(LW["spine"])
    ax.tick_params(labelsize=FONT["tick"])


def apply_style():
    """Set global matplotlib rcParams."""
    plt.rcParams.update({
        "font.size":        FONT["axis_label"],
        "axes.titlesize":   FONT["title"],
        "axes.labelsize":   FONT["axis_label"],
        "legend.fontsize":  FONT["legend"],
        "xtick.labelsize":  FONT["tick"],
        "ytick.labelsize":  FONT["tick"],
        "lines.linewidth":  LW["data"],
        "grid.linewidth":   LW["grid"],
        "figure.dpi":       DPI,
        "savefig.dpi":      DPI,
    })
