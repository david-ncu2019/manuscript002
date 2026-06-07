"""
plot_stress_strain.py — Visualize stress-strain hysteresis curves.

Produces two figures per station:
1. Multi-panel (one per layer): stress-strain scatter with elastic/inelastic coloring
2. Multi-panel: time series of stress and strain side-by-side

Usage:
    python scripts/12_stress_strain/plot_stress_strain.py --station TUKU
    python scripts/12_stress_strain/plot_stress_strain.py --station TUKU --layer F2

Output: results/stress_strain/{STATION}/
"""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "results" / "stress_strain"


def plot_station(station: str, layer: str = None):
    """Plot stress-strain curves for a station."""
    station_dir = DATA_DIR / station
    if not station_dir.exists():
        raise SystemExit(f"No stress-strain data for '{station}'. Run prepare_stress_strain.py first.")

    csvs = sorted(station_dir.glob(f"{station}_*_stress_strain.csv"))
    if layer:
        csvs = [c for c in csvs if f"_{layer}_" in c.name]
        if not csvs:
            raise SystemExit(f"No data for layer '{layer}' at '{station}'.")

    n = len(csvs)
    fig_hyst, axes_hyst = plt.subplots(n, 1, figsize=(8, 4 * n), squeeze=False)
    fig_ts, axes_ts = plt.subplots(2, 1, figsize=(10, 7))

    for idx, csv_path in enumerate(csvs):
        df = pd.read_csv(csv_path, parse_dates=["datetime"])
        layer_code = csv_path.stem.replace(f"{station}_", "").replace("_stress_strain", "")

        stress = df["stress_kpa"].values
        strain = df["strain_mm_m"].values
        is_elastic = df["is_elastic"].values
        datetime = pd.to_datetime(df["datetime"])

        # Plot stress-strain hysteresis (one subplot per layer)
        ax = axes_hyst[idx][0]

        # Sort by time to show hysteresis path
        valid = np.isfinite(stress) & np.isfinite(strain)
        s, e, d = stress[valid], strain[valid], datetime[valid]
        mask_e = is_elastic[valid]

        # Elastic (blue) and inelastic (red) points
        ax.scatter(s[mask_e], e[mask_e], c="steelblue", s=8, alpha=0.5, label="elastic", zorder=2)
        ax.scatter(s[~mask_e], e[~mask_e], c="crimson", s=8, alpha=0.5, label="inelastic", zorder=3)

        # Connect with a thin grey line to show hysteresis path
        ax.plot(s, e, color="grey", linewidth=0.5, alpha=0.6, zorder=1)

        ax.set_xlabel("Effective stress change Δσ' (kPa)")
        ax.set_ylabel("Vertical strain ε (mm/m)")
        ax.set_title(f"{station} {layer_code}")
        ax.axhline(0, color="grey", linewidth=0.5, linestyle="--")
        ax.axvline(0, color="grey", linewidth=0.5, linestyle="--")
        ax.legend(loc="best", fontsize=8)
        ax.grid(True, alpha=0.3)

        # Annotate single-ring
        if df["single_ring"].iloc[0]:
            ax.text(0.95, 0.05, "SINGLE RING", transform=ax.transAxes,
                    fontsize=10, ha="right", va="bottom", color="orange", style="italic")

        # Time series (stacked)
        ax_stress = axes_ts[0]
        ax_stress.plot(datetime[valid], s, linewidth=0.8, label=layer_code)
        ax_stress.set_ylabel("Δσ' (kPa)")
        ax_stress.legend(loc="best", fontsize=7, ncol=3)
        ax_stress.grid(True, alpha=0.3)

        ax_strain = axes_ts[1]
        ax_strain.plot(datetime[valid], e, linewidth=0.8, label=layer_code)
        ax_strain.set_ylabel("ε (mm/m)")
        ax_strain.legend(loc="best", fontsize=7, ncol=3)
        ax_strain.grid(True, alpha=0.3)

    axes_ts[0].set_title(f"{station} — Stress and strain time series")
    axes_ts[1].set_xlabel("Date")

    fig_hyst.tight_layout()
    fig_ts.tight_layout()

    # Save
    hyst_path = DATA_DIR / station / f"{station}_stress_strain_hysteresis.png"
    ts_path = DATA_DIR / station / f"{station}_stress_strain_timeseries.png"
    fig_hyst.savefig(hyst_path, dpi=150, bbox_inches="tight")
    fig_ts.savefig(ts_path, dpi=150, bbox_inches="tight")
    plt.close(fig_hyst)
    plt.close(fig_ts)

    print(f"  Hysteresis:    {hyst_path}")
    print(f"  Time series:   {ts_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Plot stress-strain hysteresis curves.")
    parser.add_argument("--station", type=str, required=True, help="Station name (e.g. TUKU)")
    parser.add_argument("--layer", type=str, default=None, help="Layer code (F1/T1/F2/T2/F3/F4). All by default.")
    args = parser.parse_args()

    print(f"Plotting stress-strain curves for {args.station}" +
          (f" layer {args.layer}" if args.layer else " (all layers)"))
    plot_station(args.station, args.layer)
    print("Done.")


if __name__ == "__main__":
    main()
