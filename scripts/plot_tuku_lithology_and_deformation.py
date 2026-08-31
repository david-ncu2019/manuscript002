"""Dataset figure: borehole lithology (panel A) + MLCW deformation (panel B).

Combines the logic of plot_borehole_lithology_ms2.py (panel A) and
plot_mlcw_ms2_v2.py (panel B) into ONE matplotlib figure, laid out on a
6-column grid:

  row 0 (~2 cm)      : title, spans all 6 columns
  row 1 (21 cm)      : panel A (cols 0:2) | panel B (cols 2:6)

Panel A and panel B share ONE literal Y-axis for Depth (m) via
matplotlib's `sharey`, which locks both axes to identical data limits.
Combined with both axes spanning the same GridSpec row height, this
guarantees an identical px-per-metre scale between the two panels, not
just a visually similar one. The shared axis sits physically between A
and B (A's right edge = B's left edge): `wspace` is set near 0.

Each panel keeps its OWN separate legend:
  - Panel A: a 4-category soil-type box legend, placed in the -15..0 m
    headroom above the lithology column (inside axA, not row 0).
  - Panel B: the date-timeline horizontal colorbar, pinned level with the
    300 m depth gridline (same technique as plot_mlcw_ms2_v2.py CELL 10).

Data / physics — unchanged from the two source scripts:
  Panel A: each 0.1 m soil layer is one horizontal bar segment at x=0,
    coloured by one of 4 merged soil categories.
  Panel B: each line is one date; x = cumulative MLCW deformation (mm,
    using the existing sign convention so compaction grows rightward); colour encodes date
    (pale = early, dark = late).

Run headlessly:
  $env:PYTHONPATH=""; conda run -n fafalab2 python scripts/plot_tuku_lithology_and_deformation.py
"""

# =============================================================================
# CELL 1 — IMPORTS + CONFIGURATION
# =============================================================================
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.transforms as mtransforms
from matplotlib.ticker import MultipleLocator
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize

# --- Panel A (borehole lithology) source data ---
BOREHOLE_CSV = Path(
    "D:/1000_SCRIPTS/004_Project003/20260427_InSAR_MLCW_v3/"
    "007_tests/014_ml_nowcast/raw_data/05_borehole_materials/TUKU/borehole.csv"
)
DEPTH_TOP_COL = "depth_top"
DEPTH_BOT_COL = "depth_bot"
CATEGORY_COL = "SOIL_CATEGORY"

BAR_WIDTH = 0.35
X_MIN_A, X_MAX_A = -0.5, 0.5
Y_MAJOR_TICK_M = 50
Y_MINOR_TICK_M = 10

USE_HATCH = False
BAR_EDGE_COLOR = "none"

SOIL_STYLE = {
    1: {"color": "#80ffff", "hatch": "O",   "label": "Gravel"},
    2: {"color": "#ffe119", "hatch": ".",   "label": "Coarse sand"},
    3: {"color": "#ffe119", "hatch": ".",   "label": "Coarse sand"},
    4: {"color": "#98FB98", "hatch": "..",  "label": "Fine sand"},
    5: {"color": "#997642", "hatch": "/..", "label": "Silt and Clay"},
    6: {"color": "#997642", "hatch": "/..", "label": "Silt and Clay"},
}
UNKNOWN_STYLE = {"color": "gray", "hatch": "", "label": "Unknown"}

# --- Panel B (MLCW compaction) source data ---
MLCW_CSV = Path(
    "D:/1000_SCRIPTS/004_Project003/20260427_InSAR_MLCW_v3/001_data/mlcw/modeled"
    "/TUKU_ringbyring.csv"
)
WINDOW_START = "2010-01-01"
WINDOW_END = "2024-12-31"
CMAP = "turbo"   # blue = earliest date, red = most recent date

MARKER = "o"
MARKER_SIZE = 5
LINE_STYLE = ":"
LINE_WIDTH = 0.8
LINE_ALPHA = 1.0

COLORBAR_DEPTH_M = 290
COLORBAR_X0_FRAC = 0.55
COLORBAR_SCALE = 1.5
COLORBAR_WIDTH_FRAC = 0.35 * COLORBAR_SCALE
COLORBAR_HEIGHT_FRAC = 0.02 * COLORBAR_SCALE
COLORBAR_NUDGE_FRAC_OF_BASE = 0.03   # smaller = colorbar shifts up (was 0.05)
DEPTH_LABEL_NEAR_X_FRAC = 0.98         # axes-fraction (0=left, 1=right of Compaction axis)

# --- Shared Y-axis (Depth, m) — set ONCE, used by both panels via sharey ---
SHARED_Y_TOP_M = -15.0      # headroom above 0 m for panel A's legend
SHARED_Y_BOTTOM_M = 320.0   # deeper than the deepest MLCW ring

# --- Six 50 m depth sections (S1..S6), labelled inside panel A ---
SECTION_DEPTH_BOUNDS_M = [(0, 50), (50, 100), (100, 150),
                           (150, 200), (200, 250), (250, 300)]


# --- Composite layout ---
TITLE_TEXT = "MLCW Tuku station"
TOTAL_FIG_WIDTH_CM = 31.5
ROW_C_HEIGHT_CM = 4.5
PANEL_HEIGHT_CM = 21.0
TOTAL_FIG_HEIGHT_CM = ROW_C_HEIGHT_CM + PANEL_HEIGHT_CM
WSPACE = 0.02
GRID_LEFT = 0.10
GRID_RIGHT = 0.93
GRID_TOP = 0.99
GRID_BOTTOM = 0.06

TICK_LABELSIZE_MAJOR = 14
DPI = 300

OUTPUT_PNG = Path(
    "D:/112_PROJECT_002/.worktrees/manuscript_reduced_v1/figures"
    "/fig_dataset_tuku_lithology_and_deformation.png"
)

print("STEP 0 — configuration loaded")
print(f"  borehole csv : {BOREHOLE_CSV}")
print(f"  mlcw csv     : {MLCW_CSV}")
print(f"  output png   : {OUTPUT_PNG}")


# =============================================================================
# CELL 2 — DATA LOADING FUNCTIONS
# =============================================================================
def load_borehole_df(csv_path: Path) -> pd.DataFrame:
    """Read the borehole lithology CSV and validate required columns."""
    df = pd.read_csv(csv_path)
    for col in [DEPTH_TOP_COL, DEPTH_BOT_COL, CATEGORY_COL]:
        if col not in df.columns:
            raise ValueError(f"Khong tim thay cot '{col}' trong file CSV.")
    return df


def read_mlcw_csv(csv_path: Path) -> pd.DataFrame:
    """Read the ring-by-ring MLCW CSV (rows = dates, cols = ring depth in m)."""
    df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
    df = df.dropna(axis=1, how="all")
    return df


def load_mlcw_compaction(csv_path: Path) -> tuple[pd.DataFrame, np.ndarray]:
    """Clamp to the manuscript window, re-baseline, then cumsum depth-wise.

    `depths` MUST be read from the pre-cumsum column order (shallowest to
    deepest), matching plot_mlcw_ms2_v2.py. `compaction.columns` is reversed
    (deepest to shallowest) by the cumsum step below, so `compaction.columns`
    is NOT a valid source for `depths` — using it silently pairs each row's
    values with the wrong depth (a top-to-bottom mirror of the correct plot).
    """
    df_full = read_mlcw_csv(csv_path)
    df = df_full.loc[WINDOW_START:WINDOW_END]
    if len(df) == 0:
        raise ValueError("No rows inside the window — check WINDOW_START / WINDOW_END")
    baseline_date = df.index[0]
    df = df.subtract(df.loc[baseline_date], axis=1)
    depths = df.columns.astype(float).values
    compaction = df.iloc[:, ::-1].cumsum(axis=1)
    return compaction, depths


def date_to_cmap_value(dates: pd.DatetimeIndex) -> np.ndarray:
    """Map each date linearly onto [0, 1] over the full date span.

    Uses .astype("int64") for both endpoints and the array (not the scalar
    .value attribute) to avoid a datetime64[us]-vs-nanosecond unit mismatch
    that otherwise clips every colour to the colormap's "under" colour.
    """
    epoch = dates.astype("int64")
    t0 = epoch[0]
    t1 = epoch[-1]
    return (epoch - t0) / (t1 - t0)


borehole_df = load_borehole_df(BOREHOLE_CSV)
compaction, depths = load_mlcw_compaction(MLCW_CSV)

print("STEP 1 — data loaded")
print(f"  borehole layers = {len(borehole_df)}")
print(f"  mlcw rings = {len(depths)}, dates = {len(compaction)}"
      f" ({compaction.index[0].date()} .. {compaction.index[-1].date()})")


# =============================================================================
# CELL 3 — DRAW PANEL A (borehole lithology)
# =============================================================================
def draw_borehole_panel(ax, df: pd.DataFrame) -> None:
    for _, row in df.iterrows():
        top = row[DEPTH_TOP_COL]
        thickness = row[DEPTH_BOT_COL] - top
        style = SOIL_STYLE.get(row[CATEGORY_COL], UNKNOWN_STYLE)
        ax.bar(
            x=0.0,
            height=thickness,
            bottom=top,
            width=BAR_WIDTH,
            color=style["color"],
            hatch=style["hatch"] if USE_HATCH else None,
            edgecolor=BAR_EDGE_COLOR,
            linewidth=0.3,
        )

    ax.set_xlim(X_MIN_A, X_MAX_A)
    ax.yaxis.set_major_locator(MultipleLocator(Y_MAJOR_TICK_M))
    ax.yaxis.set_minor_locator(MultipleLocator(Y_MINOR_TICK_M))
    ax.tick_params(axis="y", which="major", labelsize=TICK_LABELSIZE_MAJOR,
                    direction="out", length=10)
    ax.tick_params(axis="y", which="minor", labelsize=TICK_LABELSIZE_MAJOR,
                    direction="out", length=7)
    plt.setp(ax.get_yticklabels(), fontweight="bold")
    ax.set_xticks([])
    for side in ["right", "top", "bottom"]:
        ax.spines[side].set_visible(False)
    ax.grid(which="major", axis="y", color="darkgrey", alpha=0.3, linestyle="-")
    ax.set_axisbelow(True)
    ax.set_ylabel("Depth (m)", fontsize=15, fontweight="bold", labelpad=15)

    # S1..S6 section labels drawn directly inside panel A, at x=0.8 in
    # axes-fraction (0=left, 1=right of the X_MIN_A..X_MAX_A axis) and at
    # the midpoint depth of each 50 m section on the Y (data) axis. Uses
    # get_yaxis_transform(): x in axes-fraction, y in data coordinates.
    trans = ax.get_yaxis_transform()
    for i, (top_m, bottom_m) in enumerate(SECTION_DEPTH_BOUNDS_M, start=1):
        mid_depth_m = (top_m + bottom_m) / 2.0
        ax.text(0.8, mid_depth_m, f"S{i}", transform=trans,
                 ha="center", va="center", fontsize=14, fontweight="bold")

    legend_handles = []
    seen_labels = set()
    for code in sorted(SOIL_STYLE):
        style = SOIL_STYLE[code]
        if style["label"] in seen_labels:
            continue
        seen_labels.add(style["label"])
        legend_handles.append(
            plt.Rectangle((0, 0), 1, 1, fc=style["color"], label=style["label"])
        )
    # Legend sits in the -15..0 m headroom above the lithology column,
    # inside axA (not row 0 / title row). The Y-axis is inverted
    # (set_ylim(SHARED_Y_BOTTOM_M, SHARED_Y_TOP_M)), so axes-fraction y=1 is
    # the shallow/top end (-15 m) and y=0 is the deep/bottom end (320 m).
    # The headroom band (-15..0 m) therefore sits near fraction 1.0, not 0.0.
    ax.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.35, 1.10),
        ncol=2,
        fontsize=13,
        frameon=False,
    )


# =============================================================================
# CELL 4 — DRAW PANEL B (MLCW compaction)
# =============================================================================
def draw_compaction_panel(ax, fig, compaction: pd.DataFrame, depths: np.ndarray):
    cmap = plt.get_cmap(CMAP)
    color_values = date_to_cmap_value(compaction.index)

    n_dates = len(compaction.index)
    for date, cval in zip(compaction.index, color_values):
        y_mm = compaction.loc[date].values
        ax.plot(
            -y_mm,
            depths[::-1],
            MARKER,
            ls=LINE_STYLE,
            ms=MARKER_SIZE,
            color=cmap(cval),
            lw=LINE_WIDTH,
            alpha=LINE_ALPHA,
        )

    all_x = compaction.values.ravel()
    # x_hi (near-zero, shallow-ring side) keeps only a small +2 mm buffer so
    # the "0" tick sits flush against the left edge of the axes, with no
    # blank margin before it.
    x_lo = np.floor(np.nanmin(all_x) / 10) * 10 - 10
    x_hi = np.ceil(np.nanmax(all_x) / 10) * 10 + 2
    ax.set_xlim(-x_hi, -x_lo)

    # Depth-ring labels ("8m", "11m", ...) are positioned in AXES-FRACTION
    # x (0 = left edge, 1 = right edge of the Compaction axis) via a
    # manual blended transform (ax.transAxes for x, ax.transData for y).
    # NOTE: ax.get_xaxis_transform() looked like the natural built-in for
    # this, but on this matplotlib version it returns a broken composite
    # transform here — offsets land tens of thousands of pixels off-canvas,
    # rendering the text invisible with no error. blended_transform_factory
    # is the verified-correct equivalent.
    # xlim must be set BEFORE this so DEPTH_LABEL_NEAR_X_FRAC lands at the
    # intended spot. All labels share the same x position — no near/far
    # alternation.
    trans_x = mtransforms.blended_transform_factory(ax.transAxes, ax.transData)
    for d in depths:
        ax.axhline(y=d, color="black", ls=(0, (5, 5)), lw=0.5, alpha=0.4)
        ax.text(x=DEPTH_LABEL_NEAR_X_FRAC, y=d, s=f" {int(d)} m", va="center",
                 fontsize=10, color="grey", transform=trans_x)

    ax.xaxis.set_ticks_position("top")
    ax.xaxis.set_label_position("top")
    ax.xaxis.set_major_locator(ticker.AutoLocator())
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator())

    ax.tick_params(axis="both", which="major", direction="out", length=8, width=1.2,
                    labelsize=TICK_LABELSIZE_MAJOR)
    ax.tick_params(axis="both", which="minor", direction="out", length=4, width=0.8)
    # B does not own the shared Y-axis label/ticks — A does.
    ax.tick_params(axis="y", which="both", labelleft=False)
    plt.setp(ax.get_xticklabels(), fontweight="bold")

    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)

    ax.set_xlabel("Deformation (mm)", fontsize=14, fontweight="bold", labelpad=15)

    # Horizontal timeline colorbar pinned level with COLORBAR_DEPTH_M,
    # using axes' FINAL y-limits (set via sharey before this call).
    y_bottom, y_top_lim = ax.get_ylim()
    span = y_bottom - y_top_lim
    depth_frac = (COLORBAR_DEPTH_M - y_top_lim) / span
    colorbar_y0 = 1 - depth_frac
    colorbar_x0 = COLORBAR_X0_FRAC - 0.15
    # Nudge by the same PHYSICAL depth offset used against the old span
    # (321.2 m base -> 0.05 frac, i.e. ~16.06 m), not the same fraction, so
    # the colorbar band lands at the same depth regardless of the axes'
    # span. COLORBAR_NUDGE_FRAC_OF_BASE shifts it up (smaller) or down
    # (larger) from that baseline.
    nudge_m = COLORBAR_NUDGE_FRAC_OF_BASE * 321.2
    colorbar_y0 = colorbar_y0 - (nudge_m / span)

    sm = ScalarMappable(cmap=cmap, norm=Normalize(0, 1))
    cbax = ax.inset_axes(
        [colorbar_x0, colorbar_y0, COLORBAR_WIDTH_FRAC, COLORBAR_HEIGHT_FRAC]
    )
    cbar = fig.colorbar(sm, cax=cbax, orientation="horizontal")

    ticks = np.linspace(0, 1, 6)
    date_range = pd.date_range(compaction.index[0], compaction.index[-1], freq="D")
    tick_labels = [
        date_range[int(t * (len(date_range) - 1))].strftime("%Y/%m") for t in ticks
    ]
    cbar.set_ticks(ticks)
    cbar.ax.set_xticklabels(tick_labels, fontsize=12, rotation=45, ha="right")

    print(f"  panel B colorbar placed level with {COLORBAR_DEPTH_M} m depth"
          f" (axes-fraction x0={colorbar_x0:.3f}, y0={colorbar_y0:.3f})")


# =============================================================================
# CELL 5 — FIGURE + GRIDSPEC + ASSEMBLE
# =============================================================================
cm = 1 / 2.54
fig = plt.figure(figsize=(TOTAL_FIG_WIDTH_CM * cm, TOTAL_FIG_HEIGHT_CM * cm))

height_ratios = [ROW_C_HEIGHT_CM, PANEL_HEIGHT_CM]
gs = fig.add_gridspec(
    nrows=2, ncols=6,
    height_ratios=height_ratios,
    wspace=WSPACE, hspace=0,
    left=GRID_LEFT, right=GRID_RIGHT, top=GRID_TOP, bottom=GRID_BOTTOM,
)

ax_title = fig.add_subplot(gs[0, :])
ax_title.axis("off")
ax_title.text(0.5, 0.6, TITLE_TEXT, ha="center", va="center",
              fontsize=20, fontweight="bold", transform=ax_title.transAxes)

axA = fig.add_subplot(gs[1, 0:2])
axB = fig.add_subplot(gs[1, 2:6], sharey=axA)

# Set the shared Y-limits ONCE — sharey propagates this to axB automatically.
axA.set_ylim(SHARED_Y_BOTTOM_M, SHARED_Y_TOP_M)

draw_borehole_panel(axA, borehole_df)
draw_compaction_panel(axB, fig, compaction, depths)

print("STEP 2 — panels drawn")
print(f"  shared y limits = {axA.get_ylim()}")
print(f"  axA ylim == axB ylim : {axA.get_ylim() == axB.get_ylim()}")


# =============================================================================
# CELL 6 — SAVE (no bbox_inches="tight" / tight_layout — margins are explicit
# via GridSpec left/right/top/bottom above, so the exported cm size is exact)
# =============================================================================
fig.savefig(OUTPUT_PNG, dpi=DPI, facecolor="w", edgecolor="w")
print(f"STEP 3 — saved: {OUTPUT_PNG}")
print(f"  requested size = {TOTAL_FIG_WIDTH_CM:.1f} x {TOTAL_FIG_HEIGHT_CM:.1f} cm"
      f" @ {DPI} dpi")
