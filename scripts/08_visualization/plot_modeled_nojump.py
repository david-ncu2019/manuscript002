"""
plot_modeled_nojump.py — Visualize the three no-jump MLCW reconstruction variants.

Generates per-station figures for:
  - nojump/       : full model minus jumps (trend + seasonal)
  - trend_only/   : polynomial + polyline trend only
  - detrended/    : seasonal periodic signal only
  - comparison/   : 3-panel figure per station stacking all variants

Usage
-----
  # All stations
  python scripts/08_visualization/plot_modeled_nojump.py

  # Single station
  python scripts/08_visualization/plot_modeled_nojump.py --station TUKU
"""
import argparse
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPTS_ROOT = _SCRIPT_DIR.parent.parent

DATA_DIR    = SCRIPTS_ROOT / "data" / "mlcw" / "modeled_nojump"
FIGURE_ROOT = SCRIPTS_ROOT / "figures" / "modeled_nojump"

# Variant config: (subfolder_name, display_title, color)
VARIANTS = [
    ("nojump",     "No-jump (trend + seasonal)",     "#1f77b4"),
    ("trend_only", "Trend only (polynomial + polyline)", "#d62728"),
    ("detrended",  "Detrended (seasonal periodic)",   "#2ca02c"),
]

# ── Plot style ────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.labelsize": 12,
    "axes.titlesize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 9,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.1,
})

CM = 1 / 2.54  # centimetre → inch


def _depth_colormap(n_rings):
    """Return (colors, norm, cmap) for depth-coloured lines."""
    cmap = plt.cm.viridis
    norm = plt.Normalize(vmin=0, vmax=n_rings - 1)
    return cmap, norm


def _style_ax(ax):
    """Apply consistent axis styling."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, linestyle="--", alpha=0.3, color="gray")
    ax.tick_params(direction="in")


def plot_variant_v2(station_name, csv_path, out_dir, variant_name, variant_title, color_hint):
    """Plot all ring timeseries for one variant, colored by depth.

    Saves: {out_dir}/{STATION}_ringbyring.png
    """
    df = pd.read_csv(csv_path, parse_dates=[0], index_col=0)
    ring_cols = [c for c in df.columns if c.replace(".", "", 1).isdigit()]
    ring_depths = sorted(float(c) for c in ring_cols)

    if not ring_depths:
        return

    # Downsample for display if >20 rings — show every Nth
    step = max(1, len(ring_depths) // 20)
    shown = ring_depths[::step]

    cmap = plt.cm.viridis
    norm = plt.Normalize(vmin=min(ring_depths), vmax=max(ring_depths))

    fig, ax = plt.subplots(figsize=(18 * CM, 12 * CM))

    for rd in shown:
        col = str(rd)
        color = cmap(norm(rd))
        ax.plot(df.index, df[col], color=color, lw=1.2, alpha=0.8)

    # Colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, orientation="vertical", pad=0.02)
    cbar.set_label("Depth (m)", fontsize=10)

    _style_ax(ax)
    ax.set_xlabel("Date")
    ax.set_ylabel("Displacement (mm, negative = compaction)")
    ax.set_title(f"{station_name} — {variant_title}", fontweight="bold")

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{station_name}_ringbyring.png")
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def plot_comparison(station_name, base_dir, out_dir):
    """3-panel comparison figure: nojump (top), trend_only (mid), detrended (bottom).

    Y-axis limits are shared between nojump and trend_only for direct comparison.
    """
    # Load all three
    dfs = {}
    ring_cols = None
    for folder, title, _ in VARIANTS:
        path = os.path.join(base_dir, folder, f"{station_name}_ringbyring.csv")
        if not os.path.isfile(path):
            print(f"    [WARN] Missing: {path}")
            return
        df = pd.read_csv(path, parse_dates=[0], index_col=0)
        cols = [c for c in df.columns if c.replace(".", "", 1).isdigit()]
        dfs[folder] = df
        if ring_cols is None:
            ring_cols = sorted(float(c) for c in cols)
        else:
            # Use intersection
            cur = set(float(c) for c in cols)
            ring_cols = sorted(set(ring_cols) & cur)

    if not ring_cols:
        return

    # Choose representative rings for clarity (shallow, mid, deep)
    n_repr = min(5, len(ring_cols))
    idx = np.linspace(0, len(ring_cols) - 1, n_repr, dtype=int)
    repr_depths = [ring_cols[i] for i in idx]

    cmap = plt.cm.tab10
    norm = plt.Normalize(vmin=0, vmax=len(repr_depths) - 1)

    fig, axes = plt.subplots(3, 1, figsize=(22 * CM, 20 * CM), sharex=True)

    # Determine shared y-lim for nojump + trend_only
    all_vals = []
    for folder in ["nojump", "trend_only"]:
        df = dfs[folder]
        for rd in repr_depths:
            all_vals.extend(df[str(rd)].dropna().values)
    y_lim = (np.nanmin(all_vals), np.nanmax(all_vals)) if all_vals else (None, None)
    y_pad = (y_lim[1] - y_lim[0]) * 0.05 if y_lim[0] is not None and y_lim[1] is not None else 0

    for i, (folder, title, _) in enumerate(VARIANTS):
        ax = axes[i]
        df = dfs[folder]
        for j, rd in enumerate(repr_depths):
            color = cmap(j / max(len(repr_depths) - 1, 1))
            label = f"{rd:.1f} m"
            ax.plot(df.index, df[str(rd)], color=color, lw=1.5, alpha=0.9, label=label)

        if i == 0:
            # Legend on top panel
            ax.legend(loc="upper right", framealpha=0.8, ncol=min(n_repr, 3))

        _style_ax(ax)
        ax.set_ylabel("Disp. (mm)", fontsize=11)

        if i < 2:
            ax.set_ylim(y_lim[0] - y_pad, y_lim[1] + y_pad)

        # Bold label in the panel
        ax.text(0.02, 0.95, title, transform=ax.transAxes,
                fontsize=10, fontweight="bold", va="top",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))

    axes[-1].set_xlabel("Date")
    fig.suptitle(f"{station_name} — Decomposition comparison", fontweight="bold", fontsize=13, y=1.01)

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{station_name}_comparison.png")
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def main():
    parser = argparse.ArgumentParser(
        description="Visualize MLCW no-jump reconstruction variants."
    )
    parser.add_argument("--station", default=None, help="Process single station only.")
    args = parser.parse_args()

    # Discover stations from the nojump folder
    nojump_dir = DATA_DIR / "nojump"
    if not nojump_dir.is_dir():
        print(f"Data directory not found: {nojump_dir}")
        return

    stations = sorted(
        f.replace("_ringbyring.csv", "")
        for f in os.listdir(nojump_dir)
        if f.endswith("_ringbyring.csv")
    )
    if args.station:
        stations = [s for s in stations if s == args.station]
        if not stations:
            print(f"Station '{args.station}' not found.")
            return

    print(f"Found {len(stations)} stations.")
    print(f"Figure output: {FIGURE_ROOT}")
    print("=" * 60)

    # ── Per-variant plots ─────────────────────────────────────────────────
    for folder, title, color in VARIANTS:
        out_subdir = FIGURE_ROOT / f"{folder}_rings"
        print(f"\n--- {title} → {out_subdir} ---")

        for i, station in enumerate(stations, 1):
            csv_path = DATA_DIR / folder / f"{station}_ringbyring.csv"
            if not csv_path.is_file():
                continue
            out = plot_variant_v2(station, csv_path, out_subdir, folder, title, color)
            if i <= 3 or i == len(stations):
                print(f"  [{i}/{len(stations)}] {station} → {out}")

    # ── Comparison plots ──────────────────────────────────────────────────
    comp_dir = FIGURE_ROOT / "comparison"
    print(f"\n--- Comparison (3-panel) → {comp_dir} ---")
    for i, station in enumerate(stations, 1):
        out = plot_comparison(station, DATA_DIR, comp_dir)
        if i <= 3 or i == len(stations):
            print(f"  [{i}/{len(stations)}] {station} → {out}")

    print("\n" + "=" * 60)
    print("All figures generated.")


if __name__ == "__main__":
    main()
