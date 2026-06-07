# Figure Output Standards (Locked — 2026-05-31)

**All matplotlib figures must use these parameters:**

```python
# Standard figure sizes (A4 paper proportions)
A4_LANDSCAPE_WIDTH = 11.7   # inches
A4_LANDSCAPE_HEIGHT = 8.3   # inches
A4_PORTRAIT_WIDTH = 8.3     # inches
A4_PORTRAIT_HEIGHT = 11.7   # inches
DPI_PUBLICATION = 300       # standard export DPI

# Single-page landscape layouts:
fig, axes = plt.subplots(n, 1, figsize=(A4_LANDSCAPE_WIDTH, max(A4_LANDSCAPE_HEIGHT, 2.0*n)), dpi=DPI_PUBLICATION)

# Single-page portrait layouts:
fig, axes = plt.subplots(n, 1, figsize=(A4_PORTRAIT_WIDTH, max(A4_PORTRAIT_HEIGHT, 2.5*n)), dpi=DPI_PUBLICATION)

# Multi-panel layouts (e.g., 1x2 or 2x2):
fig, axes = plt.subplots(1, 2, figsize=(A4_LANDSCAPE_WIDTH, A4_LANDSCAPE_HEIGHT), dpi=DPI_PUBLICATION)

# Save with explicit format:
fig.savefig(path, dpi=DPI_PUBLICATION, bbox_inches='tight', format='png')
```

**Rationale:**
- A4 landscape (11.7" x 8.3") fits publication paper size without rescaling
- 300 dpi is the print industry standard (crisp text, high resolution)
- Using `dpi` in `subplots()` at creation time ensures all text, lines, and markers scale correctly
- Applied across `scripts/13_seasonal_insar/02_reconstruction_visualization.py`

**Multi-layer timeseries (e.g., 6 MLCW layers):**
- Use `max(A4_LANDSCAPE_HEIGHT, 2.0*n)` to keep minimum page height at 8.3"
- If n=6 layers: height = max(8.3, 12.0) = 12.0", fits on 2 landscape pages
- If n=3 layers: height = max(8.3, 6.0) = 8.3", fits on 1 landscape page
