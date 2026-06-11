#!/usr/bin/env python3
"""
visualize_observed_vs_predicted.py — 6-panel timeseries of observed vs predicted
MLCW compaction at TUKU, with holdout regions shaded.

Evidence for: m4_apex_verdict_table.csv + holdout_bakeoff.json
Output: plots/reconstruction/TUKU_observed_vs_predicted_holdout.png
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

from plot_style import DPI, A4_LANDSCAPE, FONT, LW, style_ax, apply_style

# ── Paths ──────────────────────────────────────────────────────────────────────
RESULTS = Path("tau_demo_TUKU/results")
RECON_DIR = RESULTS / "reconstruction"
OUT_DIR = Path("tau_demo_TUKU/plots/reconstruction")
OUT_DIR.mkdir(parents=True, exist_ok=True)

LAYERS = ["F1", "T1", "F2", "T2", "F3", "F4"]
LAYER_TITLES = {
    "F1": "F1 (shallow aquifer, 0–103 m)",
    "T1": "T1 (aquitard, 35–129 m)",
    "F2": "F2 (main aquifer, 35–217 m)",
    "T2": "T2 (aquitard, 140–223 m)",
    "F3": "F3 (deep aquifer, 140–275 m)",
    "F4": "F4 (silt/mud aquitard, 238–300 m)",
}
LAYER_CLASS = {"F1": "thin", "T1": "thin", "F2": "thick", "T2": "thin",
               "F3": "thick", "F4": "thin"}

# ── Load result files ──────────────────────────────────────────────────────────
bakeoff = json.load(open(RESULTS / "holdout_bakeoff.json"))
carrier_summary = json.load(open(RESULTS / "reconstruction" / "TUKU_carrier_reconstruction_summary.json"))
tail_eval = carrier_summary["tail_evaluation"]
splits = bakeoff["holdout_splits"]["per_layer"]

# ── Plot ───────────────────────────────────────────────────────────────────────
apply_style()
fig, axes = plt.subplots(3, 2, figsize=A4_LANDSCAPE, sharex=False)
fig.subplots_adjust(hspace=0.45, wspace=0.12, top=0.93, bottom=0.07,
                    left=0.07, right=0.97)

COLORS = {
    "observed": "#2166ac",      # blue
    "predicted": "#d73027",     # red
    "middle_gap": "#d9d9d9",    # light gray
    "end_gap": "#bdbdbd",       # darker gray
    "tail_line": "#525252",     # dark gray dashed
}

TAIL_EPOCHS = 36

for idx, layer in enumerate(LAYERS):
    ax = axes.flat[idx]

    # ── Load reconstruction CSV ────────────────────────────────────────────
    csv_path = RECON_DIR / f"TUKU_{layer}_reconstruction.csv"
    df = pd.read_csv(csv_path, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)

    # Model prediction exists only for GPS-era epochs
    model_mask = df["b_model_mm"].notna()
    obs_mask = df["b_observed_mm"].notna()

    # Get model-era subset for holdout shading
    model_df = df[model_mask].copy()
    model_dates = model_df["date"].values
    n_model = len(model_dates)

    if n_model == 0:
        ax.text(0.5, 0.5, "No model data", transform=ax.transAxes, ha="center")
        style_ax(ax)
        continue

    # ── Holdout date ranges (from bakeoff proportions, date-based) ─────────
    # Middle gap: 40–70% of model-era dates
    # End gap: last 30% of model-era dates
    t_start = model_dates[0]
    t_end = model_dates[-1]
    t_range = (pd.Timestamp(t_end) - pd.Timestamp(t_start)).days

    middle_start = t_start + pd.Timedelta(days=int(0.40 * t_range))
    middle_end = t_start + pd.Timedelta(days=int(0.70 * t_range))
    end_start = t_start + pd.Timedelta(days=int(0.70 * t_range))
    end_end = t_end

    # Tail: last TAIL_EPOCHS model epochs
    if n_model >= TAIL_EPOCHS:
        tail_start = model_dates[-TAIL_EPOCHS]
    else:
        tail_start = t_end

    # ── Plot observed (solid blue) ─────────────────────────────────────────
    ax.plot(df["date"], df["b_observed_mm"],
            color=COLORS["observed"], linewidth=LW["data"], alpha=0.85,
            label="Observed MLCW")

    # ── Plot predicted (solid red) ─────────────────────────────────────────
    ax.plot(df["date"], df["b_model_mm"],
            color=COLORS["predicted"], linewidth=LW["data"], alpha=0.85,
            label="Predicted (carrier)")

    # ── Shade middle gap (40–70%) ─────────────────────────────────────────
    ax.axvspan(middle_start, middle_end, color=COLORS["middle_gap"],
               alpha=0.55, zorder=0, label="Middle holdout (40–70%)")

    # ── Shade end gap (last 30%) ──────────────────────────────────────────
    ax.axvspan(end_start, end_end, color=COLORS["end_gap"],
               alpha=0.45, zorder=0, label="End holdout (last 30%)")

    # ── Tail boundary line ─────────────────────────────────────────────────
    ax.axvline(tail_start, color=COLORS["tail_line"], linestyle="--",
               linewidth=LW["reference"], alpha=0.7, label="Tail start (6 mo)")

    # ── Annotation box ─────────────────────────────────────────────────────
    bakeoff_rmse = bakeoff["per_layer"][layer]

    mid_rmse = bakeoff_rmse["middle_gap"]["rmse_carrier_mm"]
    end_rmse = bakeoff_rmse["end_gap"]["rmse_carrier_mm"]
    t = tail_eval[layer]
    tail_rmse = t["rmse_model_mm"]
    tail_skill = t["skill"]
    textstr = (
        f"Model: carrier+GWL (Script 14)  |  τ={splits[layer]['tau_opt']}"
        f"\nMiddle: RMSE={mid_rmse:.2f} mm"
        f"\nEnd:    RMSE={end_rmse:.2f} mm"
        f"\nTail:   RMSE={tail_rmse:.2f} mm  skill={tail_skill:+.3f}"
    )
    props = dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.85,
                 edgecolor="gray", linewidth=0.8)
    ax.text(0.02, 0.05, textstr, transform=ax.transAxes,
            fontsize=FONT["annotation"], verticalalignment="bottom",
            bbox=props, family="monospace")

    # ── Axis labels and styling ────────────────────────────────────────────
    ax.set_title(LAYER_TITLES[layer], fontsize=FONT["title"], fontweight="bold")
    ax.set_ylabel("Cumulative compaction (mm)")
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.tick_params(axis="x", rotation=0)

    style_ax(ax)
    ax.grid(True, alpha=0.3, linewidth=LW["grid"])

    # Only show legend on first panel
    if idx == 0:
        ax.legend(loc="upper left", fontsize=8, framealpha=0.9,
                  ncol=2, columnspacing=0.5)

# ── Suptitle ────────────────────────────────────────────────────────────────────
fig.suptitle(
    "TUKU — Observed vs Predicted Per-Layer MLCW Compaction\n"
    "Gray bands = held-out epochs (model never saw these during training)",
    fontsize=FONT["suptitle"], fontweight="bold", y=0.98)

# ── Save ────────────────────────────────────────────────────────────────────────
out_path = OUT_DIR / "TUKU_observed_vs_predicted_holdout.png"
fig.savefig(out_path, dpi=DPI, bbox_inches="tight", facecolor="white")
plt.close(fig)

print(f"Saved: {out_path}")
print("Done.")
