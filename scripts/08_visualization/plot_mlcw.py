"""Plot MLCW ring-by-ring compaction profiles.

Data format expected:
  - CSV with datetime index (rows) and ring depths as columns (float, metres)
  - Values: cumulative compaction in mm (negative = compaction)

Usage:
  python src/plot_mlcw.py <csv_path> [output_png]
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from scipy.interpolate import interp1d


# ── Data loading ─────────────────────────────────────────────────────────────

def load_mlcw_csv(csv_path: str | Path) -> tuple[pd.DataFrame, np.ndarray, str]:
    """Return (df, depths_m, station_name).

    df      : rows = dates (DatetimeIndex), columns = depth labels (str)
    depths_m: ring depths in metres (float array, same order as df.columns)
    """
    df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
    df = df.dropna(axis=1, how="all")          # drop fully-empty columns
    depths_m = df.columns.astype(float).values
    station_name = Path(csv_path).stem.split("_")[0].upper()
    return df, depths_m, station_name


# ── Colour mapping ────────────────────────────────────────────────────────────

def _date_to_cmap_value(dates: pd.DatetimeIndex) -> np.ndarray:
    """Map each date linearly onto [0, 1] over the full date span."""
    t0 = dates[0].value
    t1 = dates[-1].value
    return (dates.astype(np.int64) - t0) / (t1 - t0)


# ── Profile lines ─────────────────────────────────────────────────────────────

def plot_profiles(ax: plt.Axes, df: pd.DataFrame, depths_m: np.ndarray,
                  cmap_name: str = "jet") -> None:
    """Draw one depth-compaction profile per date, coloured by time."""
    cmap = plt.get_cmap(cmap_name)
    cvals = _date_to_cmap_value(df.index)

    for date, cval in zip(df.index, cvals):
        y_mm = df.loc[date].values          # compaction in mm
        color = cmap(cval)

        # scatter markers at ring positions
        ax.plot(-y_mm, -depths_m, "o", ms=4, color=color, lw=0, zorder=3)

        # smooth interpolated line
        if len(depths_m) > 2:
            f = interp1d(depths_m, y_mm, kind="linear")
            d_fine = np.linspace(depths_m.min(), depths_m.max(), len(depths_m) * 10)
            ax.plot(-f(d_fine), -d_fine, "-", lw=1.2, color=color, zorder=2)


# ── Axes styling ──────────────────────────────────────────────────────────────

def style_axes(ax: plt.Axes, df: pd.DataFrame, depths_m: np.ndarray,
               station_name: str) -> None:
    """Apply axis labels, limits, ticks, and grid."""
    # X axis at top
    ax.xaxis.set_ticks_position("top")
    ax.xaxis.set_label_position("top")
    ax.set_xlabel("Cumulative Compaction (mm)", fontsize=13, fontweight="bold", labelpad=10)
    ax.set_ylabel("Depth (m)", fontsize=13, fontweight="bold", labelpad=10)

    # X limits: bracket the data with 5 mm padding, rounded to nearest 10
    x_vals = df.values.ravel()
    x_lo = np.floor(np.nanmin(x_vals) / 10) * 10 - 5
    x_hi = np.ceil(np.nanmax(x_vals) / 10) * 10 + 5
    ax.set_xlim(-x_hi, -x_lo)

    # Y limits: depth range
    deepest = depths_m.max()
    if deepest <= 250:
        y_bot = -220
    elif deepest <= 315:
        y_bot = -320
    else:
        y_bot = -360
    ax.set_ylim(bottom=y_bot, top=5)

    # Ticks
    ax.yaxis.set_major_locator(ticker.MultipleLocator(50))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(10))
    ax.xaxis.set_major_locator(ticker.AutoLocator())
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(5))
    ax.tick_params(axis="both", which="major", direction="in", length=7, labelsize=12)
    ax.tick_params(axis="both", which="minor", direction="in", length=4)

    # Make Y tick labels positive (depths are stored as negatives on axis)
    yticks = ax.get_yticks()
    ax.yaxis.set_major_locator(ticker.FixedLocator(yticks))
    ax.set_yticklabels([str(abs(int(t))) for t in yticks])

    # Grid and spines
    ax.grid(which="major", color="grey", alpha=0.3, linestyle="--")
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.set_axisbelow(True)

    ax.set_title(station_name, fontsize=16, fontweight="bold", pad=40)


# ── Colorbar ──────────────────────────────────────────────────────────────────

def add_colorbar(fig: plt.Figure, ax: plt.Axes, df: pd.DataFrame,
                 cmap_name: str = "jet") -> None:
    """Add a vertical colorbar annotated with 6 evenly-spaced dates."""
    dates = pd.date_range(df.index[0], df.index[-1], freq="D")
    ticks = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
    tick_labels = [
        dates[int(t * (len(dates) - 1))].strftime("%Y/%m/%d")
        for t in ticks
    ]

    sm = ScalarMappable(cmap=cmap_name, norm=Normalize(0, 1))
    cbax = inset_axes(ax, width="25%", height="1.25%", loc="lower left",
                      bbox_to_anchor=(0.75, 0.05, 0.1, 20),
                      bbox_transform=ax.transAxes, borderpad=0)
    cbar = fig.colorbar(sm, cax=cbax, orientation="vertical")
    cbar.set_ticks(ticks)
    cbar.ax.set_yticklabels(tick_labels[::-1], fontsize=11)


# ── Main entry ────────────────────────────────────────────────────────────────

def plot_mlcw(csv_path: str | Path, output_png: str | Path | None = None) -> plt.Figure:
    """Create the MLCW profile figure and optionally save it."""
    df, depths_m, station_name = load_mlcw_csv(csv_path)

    cm = 1 / 2.54
    fig, ax = plt.subplots(figsize=(21 * cm, 29.7 * cm))

    plot_profiles(ax, df, depths_m)
    style_axes(ax, df, depths_m, station_name)
    add_colorbar(fig, ax, df)

    fig.subplots_adjust(top=0.92, bottom=0.05, left=0.12, right=0.96)

    if output_png:
        fig.savefig(output_png, dpi=300, bbox_inches="tight",
                    facecolor="w", edgecolor="w")
        print(f"Saved: {output_png}")

    return fig


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python plot_mlcw.py <csv_path> [output_png]")
        sys.exit(1)
    csv_file = sys.argv[1]
    out_file = sys.argv[2] if len(sys.argv) > 2 else None
    fig = plot_mlcw(csv_file, out_file)
    plt.show()
