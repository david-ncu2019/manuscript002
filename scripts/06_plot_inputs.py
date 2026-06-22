#!/usr/bin/env python
"""
06_plot_inputs.py — visualize the ML-nowcast INPUT data.

Run AFTER 03_build_feature_table.py (uses results/feature_table.csv for the
aligned driver-response scatter) and reads raw_data/ for the stacked dashboard.

Produces (figures/):
  - input_dashboard.png        stacked shared-x panels: MLCW target increment,
                               GPS surface increment, 5 GWL heads, rainfall.
  - driver_response_scatter.png  per-section dGWL vs compaction increment.

Style: shared viz_style (one depth palette, split shading, no twinx). English.
Sign conventions (GEMINI.md): MLCW/GPS negative = subsidence; GWL head m MSL
NEVER negated (LUNZI head legitimately negative).

Usage:
    cd 012_ml_nowcast
    $env:PYTHONPATH=""; conda run -n fafalab2 python scripts/06_plot_inputs.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import trial_config as tc  # noqa: E402
import viz_style as vs  # noqa: E402

RUN_ID = tc.parse_run_arg("Plot the ML-nowcast input data for a trial.")
CONFIG = tc.load_config(RUN_ID)
RAW_DIR = tc.RAW_DIR
RESULTS_DIR = tc.results_dir(RUN_ID)
FIGURES_DIR = tc.figures_dir(RUN_ID)

vs.apply_rcparams()

TRAIN = tuple(CONFIG["split"]["train"])
VAL = tuple(CONFIG["split"]["val"])
TEST = tuple(CONFIG["split"]["test"])
SPAN = tuple(CONFIG["span"])

MLCW_COLS = {
    "000_050_m": "S1", "050_100_m": "S2", "100_150_m": "S3",
    "150_200_m": "S4", "200_250_m": "S5", "250_300_m": "S6",
}
# GWL series to plot in the dashboard — one per DISTINCT (wellcode, filename) in the
# run's section_well map, labelled with the sections it drives. Shallow -> deep order.
def _gwl_files_from_config():
    by_file = {}  # (code, fname) -> [sections]
    for sec, (code, fname) in CONFIG["section_well"].items():
        by_file.setdefault((code, fname), []).append(sec)
    items = []
    for (code, fname), secs in by_file.items():
        label = f"{'/'.join(sorted(secs))} {fname.split('_')[-1].replace('.csv','')}"
        items.append((label, fname, code, sorted(secs)[0]))
    items.sort(key=lambda t: t[3])  # by first section (shallow->deep)
    return [(lab, fn, cd) for lab, fn, cd, _ in items]

GWL_FILES = _gwl_files_from_config()
GWL_LINE_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]


def _clip(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[SPAN[0]:SPAN[1]]


def load_inputs():
    mlcw = pd.read_csv(RAW_DIR / "monthly_mlcw_timeseries_TUKU.csv",
                       parse_dates=["datetime"]).set_index("datetime")
    mlcw = mlcw[list(MLCW_COLS)].rename(columns=MLCW_COLS).sort_index()
    mlcw_incr = _clip(mlcw.diff())

    gps = pd.read_csv(RAW_DIR / "monthly_GPS_timeseries_TUKU.csv",
                      parse_dates=["date"]).set_index("date")["modeled"].sort_index()
    gps_incr = _clip(gps.diff())

    gwl = {}
    for label, fname, code in GWL_FILES:
        s = pd.read_csv(RAW_DIR / fname)
        s["datetime"] = pd.to_datetime(s["datetime"])
        gwl[label] = _clip(s.set_index("datetime")[code].sort_index())

    rain = pd.read_csv(RAW_DIR / "monthly_sum_rainfall_TUKU.csv")
    rain["datetime"] = pd.to_datetime(rain["datetime"], format="%y/%m/%d")
    rain = _clip(rain.set_index("datetime")["values"].sort_index())

    return mlcw_incr, gps_incr, gwl, rain


def fig_dashboard(mlcw_incr, gps_incr, gwl, rain):
    fig, axes = plt.subplots(4, 1, figsize=(13, 11), sharex=True)

    # (a) MLCW increment target — 6 sections, shared y
    ax = axes[0]
    for s in vs.SECTIONS:
        ax.plot(mlcw_incr.index, mlcw_incr[s], color=vs.SECTION_COLORS[s], lw=1.1, label=s)
    ax.axhline(0, color="grey", lw=0.5)
    ax.set_ylabel("dC (mm/mo)\n(neg = compaction)")
    ax.set_title("(a) MLCW monthly compaction increment — TARGET, per 50 m section")
    ax.legend(ncol=6, fontsize=8, loc="upper right")

    # (b) GPS surface increment (shared signal)
    ax = axes[1]
    ax.plot(gps_incr.index, gps_incr.values, color="black", lw=1.1)
    ax.axhline(0, color="grey", lw=0.5)
    ax.set_ylabel("dS_total (mm/mo)")
    ax.set_title("(b) GPS surface displacement increment — shared across all sections")

    # (c) GWL heads (m MSL, never negated)
    ax = axes[2]
    for (label, _, _), col in zip(GWL_FILES, GWL_LINE_COLORS):
        ax.plot(gwl[label].index, gwl[label].values, color=col, lw=1.1, label=label)
    ax.axhline(0, color="grey", lw=0.5)
    ax.set_ylabel("GWL head (m MSL)")
    ax.set_title("(c) Groundwater head per assigned well — never negated (LUNZI legitimately < 0)")
    ax.legend(ncol=5, fontsize=8, loc="upper right")

    # (d) rainfall bars (different unit -> its own panel, not twinx)
    ax = axes[3]
    ax.bar(rain.index, rain.values, width=20, color="#4a90d9", alpha=0.8)
    ax.set_ylabel("rain (mm/mo)")
    ax.set_title("(d) Monthly rainfall (ends 2023-02)")
    ax.set_xlabel("date")

    for ax in axes:
        vs.style_ax(ax)
        vs.shade_splits(ax, TRAIN, VAL, TEST)

    fig.suptitle("ML-nowcast INPUTS — TUKU pilot (val=grey, test=yellow shading)", y=0.995)
    fig.tight_layout()
    out = FIGURES_DIR / "input_dashboard.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"wrote {out}")


def fig_driver_response():
    df = pd.read_csv(RESULTS_DIR / "feature_table.csv", parse_dates=["datetime"])
    df["month"] = df["datetime"].dt.month
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    for ax, s in zip(axes.ravel(), vs.SECTIONS):
        sub = df[df["section"] == s]
        sc = ax.scatter(sub["dGWL"], sub["y"], c=sub["month"], cmap="twilight",
                        s=16, alpha=0.7)
        # OLS guide line
        if len(sub) > 2:
            b, a = np.polyfit(sub["dGWL"], sub["y"], 1)
            xs = np.linspace(sub["dGWL"].min(), sub["dGWL"].max(), 50)
            ax.plot(xs, a + b * xs, color=vs.SECTION_COLORS[s], lw=1.6)
            r = np.corrcoef(sub["dGWL"], sub["y"])[0, 1]
            ax.set_title(f"{s}   slope={b:+.2f}  r={r:+.2f}")
        else:
            ax.set_title(s)
        ax.axhline(0, color="grey", lw=0.5)
        ax.axvline(0, color="grey", lw=0.5)
        ax.set_xlabel("dGWL (m/mo)")
        ax.set_ylabel("dC (mm/mo)")
        vs.style_ax(ax)
    cbar = fig.colorbar(sc, ax=axes, shrink=0.6, pad=0.02)
    cbar.set_label("calendar month")
    fig.suptitle("Driver-response: monthly head change vs compaction increment "
                 "(expected: head drop -> compaction)", y=1.0)
    out = FIGURES_DIR / "driver_response_scatter.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"wrote {out}")


def main():
    mlcw_incr, gps_incr, gwl, rain = load_inputs()
    fig_dashboard(mlcw_incr, gps_incr, gwl, rain)
    fig_driver_response()


if __name__ == "__main__":
    main()
