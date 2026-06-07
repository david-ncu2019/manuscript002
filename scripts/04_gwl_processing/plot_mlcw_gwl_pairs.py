"""
Plot MLCW compaction timeseries alongside matched GWL timeseries for each
(aquifer/aquitard, station) pair.

One dual-axis figure per (station, layer) — MLCW displacement on the left y-axis,
groundwater level on the right y-axis, both rendered as markers + dotted lines
against a shared datetime x-axis.

Styles follow 2S-TOOL-Python conventions:
  - Agg backend, OO API only
  - 190 x 140 mm figure, 100 dpi construction, 600 dpi output
  - Journal style: top/right spines hidden, 70-degree x-tick rotation
  - tight_layout before save, plt.close after

Inputs:
  - data/gwl/gwl_to_mlcw_layer_assignment_v3.csv
  - data/mlcw/group_byLayer_orig/{STATION}_orig_grouped.csv
  - data/gwl/mlcw_gwl_timeseries/{STATION}_{GWL}_{WELLCODE}.feather

Output:
  - figures/mlcw_gwater_pairs/{STATION}/{STATION}_{LAYER}.png
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT = SCRIPT_DIR.parent.parent
ASSIGN_PATH = PROJECT / "data/gwl/gwl_to_mlcw_layer_assignment_v3.csv"
MLCW_DIR = PROJECT / "data/mlcw/group_byLayer_modeled"
GWL_DIR = PROJECT / "data/gwl/mlcw_gwl_timeseries"
OUT_DIR = PROJECT / "figures/mlcw_gwater_pairs"

# ── 2S-TOOL figure constants ─────────────────────────────────────────────
FIG_W = 190 / 25.4   # mm → inches
FIG_H = 140 / 25.4
CONSTRUCTION_DPI = 100
OUTPUT_DPI = 600
FIG_FONT_SIZE = 8

# Colour palette
MLCW_COLOR = "#2166ac"   # blue — compaction
GWL_COLOR = "#b2182b"    # red — water level
GRID_COLOR = "#cccccc"
ANNOT_BG = "white"
ANNOT_EDGE = "black"

# ── Load assignment ──────────────────────────────────────────────────────
assign = pd.read_csv(ASSIGN_PATH, dtype={"assigned_wellcode": str, "station": str})
assign["gwl_station"] = assign["feather_file"].apply(
    lambda x: Path(x).stem.replace("_gwl_timeseries", "") if pd.notna(x) and x != "" else ""
)

# ── Journal-style helper (adapted from 2S-TOOL) ───────────────────────────
def _journal_style(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="x", rotation=70)


def _save_and_close(fig, stem: Path):
    stem.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(str(stem) + ".png", dpi=OUTPUT_DPI)
    plt.close(fig)


# ── Per-layer plot ───────────────────────────────────────────────────────
def plot_layer(mlcw_station: str, layer: str, mlcw_series: pd.Series,
               gwl_series: pd.Series, gwl_name: str,
               assign_method: str, screen_str: str, screen_mid: float,
               dist_m: float):
    fig, ax1 = plt.subplots(figsize=(FIG_W, FIG_H), dpi=CONSTRUCTION_DPI)
    _journal_style(ax1)

    dates = mlcw_series.index
    gwl_dates = gwl_series.index

    # ── Left axis: MLCW compaction ──
    ax1.plot(dates, mlcw_series.values, color=MLCW_COLOR, linestyle=":",
             linewidth=0.8, marker="o", markersize=3, markerfacecolor=MLCW_COLOR,
             markeredgewidth=0, label=f"MLCW {layer}")
    ax1.set_ylabel("Cumulative compaction (mm)", color=MLCW_COLOR, fontsize=FIG_FONT_SIZE)
    ax1.tick_params(axis="y", labelcolor=MLCW_COLOR, labelsize=FIG_FONT_SIZE)
    ax1.tick_params(axis="x", labelsize=FIG_FONT_SIZE)
    ax1.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda v, _: f"{v:.0f}" if abs(v) < 100 else f"{v:.0f}")
    )

    # ── Right axis: GWL ──
    ax2 = ax1.twinx()
    ax2.plot(gwl_dates, gwl_series.values, color=GWL_COLOR, linestyle=":",
             linewidth=0.8, marker="s", markersize=3, markerfacecolor=GWL_COLOR,
             markeredgewidth=0, label=f"GWL {gwl_name}")
    ax2.set_ylabel("Groundwater level (m)", color=GWL_COLOR, fontsize=FIG_FONT_SIZE)
    ax2.tick_params(axis="y", labelcolor=GWL_COLOR, labelsize=FIG_FONT_SIZE)
    ax2.spines["top"].set_visible(False)

    # ── X-axis date formatting ──
    span_days = (dates.max() - dates.min()).days
    if span_days > 365 * 10:
        ax1.xaxis.set_major_locator(mdates.YearLocator(2))
    elif span_days > 365 * 4:
        ax1.xaxis.set_major_locator(mdates.YearLocator(1))
    else:
        ax1.xaxis.set_major_locator(mdates.YearLocator(1))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax1.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=[1, 7]))

    # ── Grid ──
    ax1.grid(True, color=GRID_COLOR, linewidth=0.4, linestyle="-", alpha=0.7)
    ax1.set_axisbelow(True)

    # ── Title ──
    title = f"{mlcw_station} — Layer {layer}"
    ax1.set_title(title, fontsize=FIG_FONT_SIZE + 1, loc="left", fontweight="bold",
                  color="#333333")

    # ── Legend ──
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(handles1 + handles2, labels1 + labels2,
               loc="upper right", frameon=True, fontsize=FIG_FONT_SIZE - 1)

    # ── Info annotation ──
    lines = [
        f"Method: {assign_method}",
        f"Screen: {screen_str}",
        f"Screen mid: {screen_mid:.1f} m",
        f"Dist to GWL: {dist_m:.0f} m",
    ]
    text_str = "\n".join(lines)
    ax1.text(0.25, 0.04, text_str, transform=ax1.transAxes,
             ha="right", va="bottom", fontsize=FIG_FONT_SIZE - 1,
             bbox={"boxstyle": "square", "facecolor": ANNOT_BG,
                   "edgecolor": ANNOT_EDGE, "linewidth": 0.5, "pad": 1},
             family="monospace")

    # ── Save ──
    stem = OUT_DIR / mlcw_station / f"{mlcw_station}_{layer}"
    _save_and_close(fig, stem)


# ── Main ──────────────────────────────────────────────────────────────────
def main():
    stations = sorted(assign["station"].unique())
    total_plots = 0

    for mlcw_st in stations:
        # mlcw_path = MLCW_DIR / f"{mlcw_st}_orig_grouped.csv"
        mlcw_path = MLCW_DIR / f"{mlcw_st}_modeled_grouped.csv"
        if not mlcw_path.exists():
            print(f"  SKIP {mlcw_st}: no modeled_grouped.csv")
            continue

        mlcw = pd.read_csv(mlcw_path, parse_dates=["datetime"])
        mlcw = mlcw.set_index("datetime").sort_index()

        st_assign = assign[assign["station"] == mlcw_st]

        for _, row in st_assign.iterrows():
            layer = row["layer"]

            # Skip layers not in MLCW data or entirely NaN
            if layer not in mlcw.columns:
                print(f"  SKIP {mlcw_st}/{layer}: layer column not found in MLCW CSV")
                continue
            mlcw_series = mlcw[layer].dropna()
            if len(mlcw_series) == 0:
                print(f"  SKIP {mlcw_st}/{layer}: all NaN in MLCW data")
                continue

            # Build feather filename and load GWL
            gwl_station = row["gwl_station"]
            wellcode = str(row["assigned_wellcode"])
            feather_name = f"{mlcw_st}_{gwl_station}_{wellcode}"
            feather_path = GWL_DIR / f"{feather_name}.feather"

            if not feather_path.exists():
                print(f"  SKIP {mlcw_st}/{layer}: missing {feather_name}.feather")
                continue

            gwl = pd.read_feather(feather_path)
            gwl = gwl.set_index("datetime").sort_index()
            gwl_col = [c for c in gwl.columns if c != "datetime"][0]
            gwl_series = gwl[gwl_col].dropna()
            if len(gwl_series) == 0:
                print(f"  SKIP {mlcw_st}/{layer}: all NaN in GWL data")
                continue

            # Plot
            plot_layer(
                mlcw_station=mlcw_st,
                layer=layer,
                mlcw_series=mlcw_series,
                gwl_series=gwl_series,
                gwl_name=gwl_col,
                assign_method=row["assignment_method"],
                screen_str=str(row["screen_str"]),
                screen_mid=float(row["screen_mid_m"]),
                dist_m=float(row["dist_to_gwl_m"]),
            )
            total_plots += 1

        print(f"  {mlcw_st}: done")

    print(f"\nTotal plots generated: {total_plots}")


if __name__ == "__main__":
    main()
