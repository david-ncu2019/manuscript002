"""
02_plot_timeseries.py
=====================
Produces per-layer GWL timeseries and MSE curves from tau search results.

Output (plots/results/):
  - tau_gwl_timeseries_{layer}.png   (6 per-layer 3-panel)
  - tau_mse_curves_all_layers.png
"""

from pathlib import Path
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from plot_style import DPI, A4_PORTRAIT, FONT, LW, style_ax, apply_style
apply_style()

# ── Paths ─────────────────────────────────────────────────────────────────────
DEMO_DIR    = Path(__file__).resolve().parent
RESULTS_DIR = DEMO_DIR / "results"
PLOTS_DIR   = DEMO_DIR / "plots" / "results"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

SCRIPTS_IHMF = DEMO_DIR.parent / "scripts" / "10_ihmf"
sys.path.insert(0, str(SCRIPTS_IHMF))
from ihmf_model_v3 import remove_seasonal_cycle

# ── Colours (tab10 via cmap) ──────────────────────────────────────────────────
COLORS = {ly: plt.cm.tab10(i) for i, ly in enumerate(["F1", "T1", "F2", "T2", "F3", "F4"])}
LAYERS_ORDERED = ["F1", "T1", "F2", "T2", "F3", "F4"]

T_START = pd.Timestamp("2015-01-01")
T_END   = pd.Timestamp("2026-01-01")

# ── Load data ─────────────────────────────────────────────────────────────────
tau_results = pd.read_csv(RESULTS_DIR / "tau_results.csv").set_index("layer")
mse_df      = pd.read_csv(RESULTS_DIR / "tau_mse_curves.csv")
tau_epochs  = mse_df["tau_epochs"].values
npz         = np.load(RESULTS_DIR / "tuku_aligned_data.npz", allow_pickle=True)


def load_layer(layer):
    d = {}
    for key in npz.files:
        if key.startswith(f"{layer}__"):
            d[key[len(f"{layer}__"):]] = npz[key]
    d["dates"]     = pd.to_datetime(d["dates"])
    d["inc_dates"] = pd.to_datetime(d["inc_dates"])
    return d


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE TYPE 1: Per-layer 3-panel timeseries (6 figures)
# ══════════════════════════════════════════════════════════════════════════════

for layer in LAYERS_ORDERED:
    if layer not in tau_results.index:
        continue

    d       = load_layer(layer)
    tau_opt = int(tau_results.loc[layer, "tau_opt"])
    h_c     = float(tau_results.loc[layer, "h_c_m"])
    wellcode = str(tau_results.loc[layer, "wellcode"])
    color   = COLORS[layer]

    dates     = d["dates"]
    head_m    = d["head_m"].astype(float)
    inc_dates = d["inc_dates"]
    inc_dH    = d["inc_dH"].astype(float)

    # Restrict to 2015+
    mask_cum = (dates >= T_START) & (dates < T_END)
    mask_inc = (inc_dates >= T_START) & (inc_dates < T_END)

    dates_plot    = pd.Series(dates[mask_cum]).reset_index(drop=True)
    head_plot     = head_m[mask_cum]
    inc_dates_plot = inc_dates[mask_inc]
    inc_dH_plot    = inc_dH[mask_inc]

    # Seasonal anomaly
    monthly_means = d["monthly_means"].astype(float)
    inc_dH_anom = inc_dH_plot.copy()
    months = inc_dates_plot.month
    for m in range(1, 13):
        inc_dH_anom[months == m] -= monthly_means[m - 1]

    # Lagged anomaly
    if tau_opt > 0 and tau_opt < len(inc_dH_anom):
        inc_dH_lagged = inc_dH_anom[tau_opt:]
        lag_dates     = inc_dates_plot[tau_opt:]
    else:
        inc_dH_lagged = inc_dH_anom.copy()
        lag_dates     = inc_dates_plot.copy()

    # ── Build figure ──────────────────────────────────────────────────────────
    fig, axes = plt.subplots(3, 1, figsize=(A4_PORTRAIT[0], 10.0), sharex=False)
    fig.suptitle(
        f"TUKU  |  Layer {layer}  |  GWL well {wellcode}\n"
        f"tau_opt = {tau_opt} epochs = {tau_opt * 5} days  |  "
        f"h_c = {h_c:.2f} m above MSL",
        fontsize=FONT["suptitle"], fontweight="bold", y=0.97,
    )

    # Panel 1: Cumulative GWL
    ax1 = axes[0]
    ax1.plot(dates_plot, head_plot, color=color, linewidth=LW["data"],
             label="Piezometric head")
    ax1.axhline(h_c, color="black", linestyle="--", linewidth=LW["reference"],
                label=f"h_c = {h_c:.2f} m")
    e_mask = head_plot > h_c
    for i in range(len(dates_plot) - 1):
        ax1.axvspan(dates_plot.iloc[i], dates_plot.iloc[i + 1],
                    alpha=0.2, color="#d0e8ff" if e_mask[i] else "#ffd0d0", linewidth=0)
    ax1.set_ylabel("Piezometric head (m MSL)", fontsize=FONT["axis_label"])
    ax1.set_xlim(T_START, T_END)
    elastic_patch   = mpatches.Patch(color="#d0e8ff", alpha=0.4, label="Elastic (head > h_c)")
    inelastic_patch = mpatches.Patch(color="#ffd0d0", alpha=0.4, label="Inelastic")
    ax1.legend(handles=[ax1.get_lines()[0], ax1.get_lines()[1], elastic_patch,
                         inelastic_patch], fontsize=FONT["legend"], loc="upper right")
    ax1.set_title("Panel 1 — Original piezometric head (daily GWL)", fontsize=FONT["title"])
    style_ax(ax1)

    # Panel 2: Incremental GWL anomaly
    ax2 = axes[1]
    ax2.plot(inc_dates_plot, inc_dH_anom, color=color, linewidth=LW["data"], alpha=0.9,
             label="Delta-head anomaly (seasonal mean removed)")
    ax2.axhline(0, color="grey", linewidth=LW["reference"], linestyle="-")
    ax2.set_ylabel("Delta-head anomaly (m/epoch)", fontsize=FONT["axis_label"])
    ax2.set_xlim(T_START, T_END)
    ax2.legend(fontsize=FONT["legend"], loc="upper right")
    ax2.set_title("Panel 2 — Incremental GWL anomaly — signal used in tau search",
                  fontsize=FONT["title"])
    style_ax(ax2)

    # Panel 3: Lagged vs original
    ax3 = axes[2]
    n_common = len(lag_dates)
    orig_trimmed = inc_dH_anom[:n_common]
    orig_dates_trimmed = inc_dates_plot[:n_common]
    ax3.plot(orig_dates_trimmed, orig_trimmed, color="grey", linewidth=LW["data"],
             alpha=0.6, label="Delta-head anomaly (original, tau=0)")
    ax3.plot(lag_dates, inc_dH_lagged, color=color, linewidth=LW["data"],
             label=f"Delta-head anomaly (lagged tau={tau_opt} epochs = {tau_opt*5} days)")
    ax3.axhline(0, color="grey", linewidth=LW["reference"], linestyle="-")
    ax3.set_ylim(ax2.get_ylim())
    ax3.set_ylabel("Delta-head anomaly (m/epoch)", fontsize=FONT["axis_label"])
    ax3.set_xlim(T_START, T_END)
    ax3.legend(fontsize=FONT["legend"], loc="upper right")
    ax3.set_title(f"Panel 3 — Lagged vs original anomaly GWL  (shifted {tau_opt*5} days)",
                  fontsize=FONT["title"])
    ax3.set_xlabel("Date", fontsize=FONT["axis_label"])
    style_ax(ax3)

    fig.subplots_adjust(top=0.90, hspace=0.40)
    out_path = PLOTS_DIR / f"tau_gwl_timeseries_{layer}.png"
    fig.savefig(out_path, dpi=DPI, pad_inches=0.15)
    plt.close(fig)
    print(f"Saved: {out_path}")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE TYPE 2: MSE curves 2x3 grid
# ══════════════════════════════════════════════════════════════════════════════

fig, axes = plt.subplots(2, 3, figsize=(A4_PORTRAIT[0], 6.5))
fig.suptitle(
    "TUKU — MSE curve for each layer\n"
    "(lower MSE = better compaction prediction with that lag)\n"
    "tau_opt is where the curve reaches its minimum",
    fontsize=FONT["suptitle"], fontweight="bold", y=0.98,
)
axes_flat = axes.flatten()

for i, layer in enumerate(LAYERS_ORDERED):
    ax = axes_flat[i]
    if layer not in tau_results.index or layer not in mse_df.columns:
        ax.set_visible(False)
        continue

    mse_vals = mse_df[layer].values.astype(float)
    tau_opt  = int(tau_results.loc[layer, "tau_opt"])
    color    = COLORS[layer]
    finite   = np.isfinite(mse_vals)

    ax.plot(tau_epochs[finite], mse_vals[finite], color=color, linewidth=LW["data"],
            label=f"MSE (layer {layer})")
    ax.axvline(tau_opt, color="black", linestyle="--", linewidth=LW["reference"])
    ax.annotate(f"tau_opt = {tau_opt}\n({tau_opt*5} days)",
                xy=(tau_opt, mse_vals[tau_opt]),
                xytext=(tau_opt + 4, mse_vals[tau_opt] * 1.05 + 1e-4),
                fontsize=FONT["annotation"], arrowprops=dict(arrowstyle="->", color="black", lw=0.8))
    ax.set_title(f"Layer {layer}", fontsize=FONT["title"], color=color, fontweight="bold")
    ax.set_xlabel("tau (epochs)    [1 epoch ~ 5 days]", fontsize=FONT["axis_label"])
    ax.set_ylabel("MSE  [mm^2/epoch^2]", fontsize=FONT["axis_label"])
    ax.grid(True, alpha=0.3)
    style_ax(ax)

fig.subplots_adjust(left=0.08, right=0.97, bottom=0.10, top=0.88, hspace=0.40, wspace=0.30)
out_path = PLOTS_DIR / "tau_mse_curves_all_layers.png"
fig.savefig(out_path, dpi=DPI, pad_inches=0.15)
plt.close(fig)
print(f"Saved: {out_path}")
print("\nAll plots complete. Check tau_demo_TUKU/plots/results/")
