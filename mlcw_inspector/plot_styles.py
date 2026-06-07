"""
plot_styles.py — Color palette and line-styling constants
for the MLCW Inspector dashboard (hvPlot / Bokeh backend).
"""

# Layer color palette (colorblind-friendly)
LAYER_COLORS = {
    "F1": "#1f77b4",   # blue
    "F2": "#ff7f0e",   # orange
    "T2": "#d62728",   # red
    "F3": "#2ca02c",   # green
    "F4": "#9467bd",   # purple
    "T1": "#7f7f7f",   # gray (aquitard, less common in reconst)
}

# Line for unknown / unclassified data
FALLBACK_COLOR = "#999999"

# Ring styling (many thin lines, same-layer colours with alpha)
RING_ALPHA = 0.50
RING_LINEWIDTH = 0.7

# InSAR panel
INSAR_COLOR = "#222222"


def get_layer_color(layer: str) -> str:
    """Return hex colour for a named layer. Falls back to gray."""
    return LAYER_COLORS.get(layer, FALLBACK_COLOR)
