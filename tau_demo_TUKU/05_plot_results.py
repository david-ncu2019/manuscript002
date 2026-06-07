"""
05_plot_results.py
==================
Generate all visualization figures from TUKU tau-search results.

Output directory: tau_demo_TUKU/plots/results/
Run from repo root:
    $env:PYTHONPATH=""; conda run -n fafalab python tau_demo_TUKU/05_plot_results.py
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.ticker import MaxNLocator

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO_DIR = os.path.join(REPO_ROOT, "tau_demo_TUKU")
RESULTS_DIR = os.path.join(DEMO_DIR, "results")
DATA_DIR = os.path.join(DEMO_DIR, "data")
PLOT_DIR = os.path.join(DEMO_DIR, "plots", "results")
os.makedirs(PLOT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
tau_results = pd.read_csv(os.path.join(RESULTS_DIR, "tau_results.csv"))
tau_mse = pd.read_csv(os.path.join(RESULTS_DIR, "tau_mse_curves.csv"))
reconst = pd.read_csv(os.path.join(DATA_DIR, "TUKU_reconst_grouped_cleaned.csv"), parse_dates=["datetime"])

npz = np.load(os.path.join(RESULTS_DIR, "tuku_aligned_data.npz"), allow_pickle=True)

LAYERS = ["F1", "T1", "F2", "T2", "F3", "F4"]
TAB10 = plt.cm.tab10.colors  # list of (R,G,B) tuples

# Colors per layer: one from tab10
LAYER_COLORS = {lay: TAB10[i] for i, lay in enumerate(LAYERS)}

# Semantic colors
C_ELASTIC   = "#4682B4"   # steelblue
C_INELASTIC = "#B22222"   # firebrick
C_HEAD      = "#4169E1"   # royalblue
C_MLCW      = "#FF8C00"   # darkorange
C_INSAR     = "#3CB371"   # mediumseagreen
C_HC        = "black"

# Well-to-color map for Fig 9
WELL_COLORS = {
    "HONGLUN":    "#4169E1",  # royalblue
    "TUKU":       "#FF8C00",  # darkorange
    "LUNZI":      "#228B22",  # green
    "LIUZHUANG":  "#800080",  # purple
}


def load_layer(layer):
    """Load one layer from the npz archive."""
    prefix = f"{layer}__"
    d = {k[len(prefix):]: npz[k] for k in npz.files if k.startswith(prefix)}
    d["dates"]     = pd.to_datetime(d["dates"])
    d["inc_dates"] = pd.to_datetime(d["inc_dates"])
    d["e_m"]       = d["e_m"].astype(bool)
    d["i_m"]       = d["i_m"].astype(bool)
    return d


def row(layer):
    """Return the tau_results row for a given layer name."""
    return tau_results[tau_results["layer"] == layer].iloc[0]


def save(fig, fname):
    path = os.path.join(PLOT_DIR, fname)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ---------------------------------------------------------------------------
# Figure 1 — MSE curves, all layers on one panel
# ---------------------------------------------------------------------------
def fig1_mse_all():
    fig, ax = plt.subplots(figsize=(10, 6))

    tau_x = tau_mse["tau_epochs"].values

    for i, layer in enumerate(LAYERS):
        r   = row(layer)
        col = TAB10[i]
        ax.plot(tau_x, tau_mse[layer].values, color=col, lw=2.0,
                label=f"{layer} (τ_opt={int(r.tau_opt)})")
        ax.axvline(r.tau_opt, color=col, lw=1.2, ls="--")
        # Annotate near the vline top
        ymax = tau_mse[layer].max()
        ax.text(r.tau_opt + 1, ymax * 0.98,
                f"{layer}: τ={int(r.tau_opt)}", color=col,
                fontsize=10, va="top", ha="left")

    ax.set_xlabel("Lag τ (5-day epochs)", fontsize=14)
    ax.set_ylabel("MSE (mm² epoch⁻²)", fontsize=14)
    ax.tick_params(labelsize=12)
    ax.set_title("TUKU — τ grid search MSE curves, all 6 layers",
                 fontsize=16, fontweight="bold")
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    save(fig, "mse_curves_all_layers.png")


# ---------------------------------------------------------------------------
# Figure 2 — MSE curves, individual panels 3×2
# ---------------------------------------------------------------------------
def fig2_mse_individual():
    fig, axes = plt.subplots(3, 2, figsize=(12, 12))
    axes = axes.flatten()

    tau_x = tau_mse["tau_epochs"].values

    for i, layer in enumerate(LAYERS):
        ax  = axes[i]
        r   = row(layer)
        col = TAB10[i]
        ax.plot(tau_x, tau_mse[layer].values, color=col, lw=2.0)
        ax.axvline(r.tau_opt, color=C_HC, lw=1.2, ls="--",
                   label=f"τ_opt={int(r.tau_opt)} epochs ({int(r.tau_opt_days)} days)")
        ax.set_xlabel("Lag τ (5-day epochs)", fontsize=13)
        ax.set_ylabel("MSE (mm² epoch⁻²)", fontsize=13)
        ax.tick_params(labelsize=11)
        ax.set_title(
            f"Layer {layer} — τ_opt = {int(r.tau_opt)} epochs ({int(r.tau_opt_days)} days)",
            fontsize=13, fontweight="bold")
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)

    fig.suptitle("TUKU — Individual τ MSE curves", fontsize=16, fontweight="bold")
    fig.tight_layout()
    save(fig, "mse_curves_individual.png")


# ---------------------------------------------------------------------------
# Figure 3 — GWL head with elastic/inelastic regime shading (6 stacked panels)
# ---------------------------------------------------------------------------
def fig3_gwl_regime():
    fig, axes = plt.subplots(6, 1, figsize=(14, 22), sharex=False)

    for i, layer in enumerate(LAYERS):
        ax = axes[i]
        r  = row(layer)
        d  = load_layer(layer)

        dates  = d["dates"]
        head   = d["head_m"]
        e_mask = d["e_m"]
        i_mask = d["i_m"]

        # Continuous head line
        ax.plot(dates, head, color=C_HEAD, lw=2.0, label="Head", zorder=3)

        # e_m / i_m are defined on incremental epochs (len 771),
        # so use inc_dates (len 771) and the matching head slice (head[:-1])
        head_inc = head[:-1]  # drop the last point to match incremental length
        inc_dates = d["inc_dates"]

        ax.scatter(inc_dates[e_mask], head_inc[e_mask], color=C_ELASTIC,
                   s=4, alpha=0.5, zorder=4, label=f"Elastic ({e_mask.sum()})")
        ax.scatter(inc_dates[i_mask], head_inc[i_mask], color=C_INELASTIC,
                   s=4, alpha=0.5, zorder=4, label=f"Inelastic ({i_mask.sum()})")

        # h_c line
        ax.axhline(r.h_c_m, color=C_HC, lw=1.2, ls="--",
                   label=f"h_c = {r.h_c_m:.2f} m")

        ax.set_ylabel("Head rel. 2015-01-16 (m)", fontsize=13)
        ax.tick_params(labelsize=11)
        ax.set_title(
            f"Layer {layer} — well {r.wellcode} — elastic: {int(r.n_elastic)}, inelastic: {int(r.n_inelastic)}",
            fontsize=13, fontweight="bold")
        ax.legend(fontsize=11, loc="upper right")
        ax.grid(True, alpha=0.3)

    axes[-1].set_xlabel("Date", fontsize=14)
    fig.suptitle("TUKU — Piezometric head with elastic/inelastic regime classification",
                 fontsize=16, fontweight="bold")
    fig.tight_layout()
    save(fig, "gwl_head_regime.png")


# ---------------------------------------------------------------------------
# Figure 4 — Cumulative MLCW compaction (6 stacked panels)
# ---------------------------------------------------------------------------
def fig4_cumulative_mlcw():
    # Zero-reference: subtract value at 2015-01-16
    ref_date = pd.Timestamp("2015-01-16")
    reconst_sorted = reconst.sort_values("datetime").reset_index(drop=True)

    fig, axes = plt.subplots(6, 1, figsize=(14, 22), sharex=False)

    for i, layer in enumerate(LAYERS):
        ax = axes[i]
        r  = row(layer)

        series = reconst_sorted[["datetime", layer]].dropna()
        # Find nearest date to reference
        idx_ref = (series["datetime"] - ref_date).abs().idxmin()
        offset  = series.loc[idx_ref, layer]
        cumul   = series[layer] - offset

        ax.plot(series["datetime"], cumul, color=C_MLCW, lw=2.0, label="Cum. compaction")
        ax.axhline(0, color="gray", lw=1.0, ls=":")

        ax.set_ylabel("Cumulative compaction (mm)", fontsize=13)
        ax.tick_params(labelsize=11)
        ax.set_title(f"Layer {layer}", fontsize=13, fontweight="bold")

        # Annotation box
        textstr = f"τ_opt = {int(r.tau_opt)} ep.\nh_c = {r.h_c_m:.2f} m"
        ax.text(0.98, 0.97, textstr, transform=ax.transAxes,
                fontsize=11, va="top", ha="right",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="wheat", alpha=0.5))

        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)

    axes[-1].set_xlabel("Date", fontsize=14)
    fig.suptitle("TUKU — Cumulative MLCW compaction (zero-referenced to 2015-01-16)",
                 fontsize=16, fontweight="bold")
    fig.tight_layout()
    save(fig, "cumulative_mlcw.png")


# ---------------------------------------------------------------------------
# Figure 5 — Incremental GWL ΔH, elastic/inelastic colored (6 stacked)
# ---------------------------------------------------------------------------
def fig5_incremental_gwl():
    fig, axes = plt.subplots(6, 1, figsize=(14, 22), sharex=False)

    for i, layer in enumerate(LAYERS):
        ax = axes[i]
        r  = row(layer)
        d  = load_layer(layer)

        inc_dates = d["inc_dates"]
        inc_dH    = d["inc_dH"]
        e_m       = d["e_m"]
        i_m       = d["i_m"]

        # The incremental arrays may be 1 shorter than head arrays
        # e_m and i_m should match inc_dates length
        # e_m, i_m, inc_dates, inc_dH all have the same length (771)
        ax.scatter(inc_dates[e_m], inc_dH[e_m], color=C_ELASTIC,
                   s=5, alpha=0.7, label=f"Elastic ({e_m.sum()})")
        ax.scatter(inc_dates[i_m], inc_dH[i_m], color=C_INELASTIC,
                   s=5, alpha=0.7, label=f"Inelastic ({i_m.sum()})")
        ax.axhline(0, color="gray", lw=1.2, ls="--")

        ax.set_ylabel("ΔHead per epoch (m epoch⁻¹)", fontsize=13)
        ax.tick_params(labelsize=11)
        ax.set_title(
            f"Layer {layer} — ΔH, elastic={int(r.n_elastic)} inelastic={int(r.n_inelastic)}",
            fontsize=13, fontweight="bold")
        ax.legend(fontsize=11, loc="upper right")
        ax.grid(True, alpha=0.3)

    axes[-1].set_xlabel("Date", fontsize=14)
    fig.suptitle("TUKU — Incremental GWL head change per 5-day epoch",
                 fontsize=16, fontweight="bold")
    fig.tight_layout()
    save(fig, "incremental_gwl_regime.png")


# ---------------------------------------------------------------------------
# Figure 6 — Incremental MLCW Δb (6 stacked panels)
# ---------------------------------------------------------------------------
def fig6_incremental_mlcw():
    fig, axes = plt.subplots(6, 1, figsize=(14, 22), sharex=False)

    for i, layer in enumerate(LAYERS):
        ax = axes[i]
        d  = load_layer(layer)

        inc_dates = d["inc_dates"]
        inc_db    = d["inc_db"]

        ax.plot(inc_dates, inc_db, color=C_MLCW, lw=2.0, label="Δcompaction")
        ax.axhline(0, color="gray", lw=1.2, ls="--")

        ax.set_ylabel("Δcompaction per epoch (mm epoch⁻¹)", fontsize=13)
        ax.tick_params(labelsize=11)
        ax.set_title(f"Layer {layer} — Δb per 5-day epoch",
                     fontsize=13, fontweight="bold")
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)

    axes[-1].set_xlabel("Date", fontsize=14)
    fig.suptitle("TUKU — Incremental MLCW compaction per 5-day epoch",
                 fontsize=16, fontweight="bold")
    fig.tight_layout()
    save(fig, "incremental_mlcw.png")


# ---------------------------------------------------------------------------
# Figure 7 — Regime summary bar chart (horizontal stacked)
# ---------------------------------------------------------------------------
def fig7_regime_bar():
    fig, ax = plt.subplots(figsize=(9, 6))

    n_e = [int(row(lay).n_elastic)   for lay in LAYERS]
    n_i = [int(row(lay).n_inelastic) for lay in LAYERS]

    y_pos = range(len(LAYERS))

    bars_e = ax.barh(list(y_pos), n_e, color=C_ELASTIC,  label="Elastic (head > h_c)")
    bars_i = ax.barh(list(y_pos), n_i, left=n_e, color=C_INELASTIC, label="Inelastic (head ≤ h_c)")

    # Annotate counts
    for j, (be, bi) in enumerate(zip(bars_e, bars_i)):
        xe = be.get_width() / 2
        ax.text(xe, j, str(n_e[j]), ha="center", va="center",
                fontsize=11, color="white", fontweight="bold")
        xi = n_e[j] + be.get_width() / 2  # midpoint of inelastic bar
        # Use bar width for inelastic
        xi = n_e[j] + n_i[j] / 2
        ax.text(xi, j, str(n_i[j]), ha="center", va="center",
                fontsize=11, color="white", fontweight="bold")

    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(LAYERS, fontsize=13)
    ax.set_xlabel("Number of 5-day epochs", fontsize=14)
    ax.set_ylabel("Layer", fontsize=14)
    ax.tick_params(labelsize=12)
    ax.set_title("TUKU — Elastic vs inelastic epoch counts per layer",
                 fontsize=16, fontweight="bold")
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3, axis="x")
    fig.tight_layout()
    save(fig, "regime_summary_bar.png")


# ---------------------------------------------------------------------------
# Figure 8 — Combined 4 signals, normalized [0,1] per layer (6 stacked)
# ---------------------------------------------------------------------------
def _norm01(arr):
    """Min-max normalize to [0, 1]. Returns arr unchanged if range is zero."""
    lo, hi = np.nanmin(arr), np.nanmax(arr)
    if hi == lo:
        return np.zeros_like(arr, dtype=float)
    return (arr - lo) / (hi - lo)


def fig8_combined_normalized():
    ref_date = pd.Timestamp("2015-01-16")
    reconst_sorted = reconst.sort_values("datetime").reset_index(drop=True)

    fig, axes = plt.subplots(6, 1, figsize=(14, 24), sharex=False)

    for i, layer in enumerate(LAYERS):
        ax = axes[i]
        d  = load_layer(layer)

        dates     = d["dates"]
        head      = d["head_m"]
        inc_dates = d["inc_dates"]
        inc_dH    = d["inc_dH"]
        inc_db    = d["inc_db"]

        # Cumulative MLCW zero-referenced
        series = reconst_sorted[["datetime", layer]].dropna()
        idx_ref = (series["datetime"] - ref_date).abs().idxmin()
        offset  = series.loc[idx_ref, layer]
        cumul   = (series[layer] - offset).values
        cumul_dates = series["datetime"].values

        # Normalize
        head_n  = _norm01(head)
        cumul_n = _norm01(cumul)
        dH_n    = _norm01(inc_dH)
        db_n    = _norm01(inc_db)

        ax.plot(dates, head_n,  color=C_HEAD,      lw=2.0, alpha=0.7,  label="GWL head")
        ax.plot(cumul_dates, cumul_n, color=C_MLCW, lw=2.0, alpha=0.85, label="Cum. MLCW")
        ax.scatter(inc_dates, dH_n, color=C_ELASTIC,   s=4, alpha=0.4, label="ΔH per epoch")
        ax.scatter(inc_dates, db_n, color=C_INELASTIC,  s=4, alpha=0.4, label="Δb per epoch")

        ax.set_ylabel("Normalized signal [0, 1]", fontsize=13)
        ax.tick_params(labelsize=11)
        ax.set_title(f"Layer {layer} — all signals normalized",
                     fontsize=13, fontweight="bold")
        ax.set_ylim(-0.05, 1.10)
        ax.legend(fontsize=11, loc="upper right", ncol=2)
        ax.grid(True, alpha=0.3)

    axes[-1].set_xlabel("Date", fontsize=14)
    fig.suptitle("TUKU — All input signals normalized [0,1] per layer",
                 fontsize=16, fontweight="bold")
    fig.tight_layout()
    save(fig, "combined_signals_normalized.png")


# ---------------------------------------------------------------------------
# Figure 9 — h_c comparison bar chart
# ---------------------------------------------------------------------------
def fig9_hc_comparison():
    fig, ax = plt.subplots(figsize=(9, 5))

    hc_vals  = []
    colors   = []
    wellcodes = []
    gwl_stations = []

    for layer in LAYERS:
        r = row(layer)
        hc_vals.append(r.h_c_m)
        wellcodes.append(str(r.wellcode))
        # Determine station name from gwl_file
        gf = str(r.gwl_file)  # e.g. "HONGLUN_gwl_timeseries.feather"
        station = gf.split("_gwl")[0]
        gwl_stations.append(station)
        colors.append(WELL_COLORS.get(station, "gray"))

    x = range(len(LAYERS))
    bars = ax.bar(list(x), hc_vals, color=colors, edgecolor="k", linewidth=0.8)

    # Annotate wellcode
    for j, (b, wc) in enumerate(zip(bars, wellcodes)):
        ypos = b.get_height()
        va   = "bottom" if ypos >= 0 else "top"
        offset = 0.05 if ypos >= 0 else -0.05
        ax.text(j, ypos + offset, wc, ha="center", va=va, fontsize=10, rotation=45)

    ax.set_xticks(list(x))
    ax.set_xticklabels(LAYERS, fontsize=13)
    ax.set_xlabel("Layer", fontsize=14)
    ax.set_ylabel("h_c — preconsolidation head threshold (m)", fontsize=13)
    ax.tick_params(labelsize=12)
    ax.set_title("TUKU — Preconsolidation head threshold h_c by layer",
                 fontsize=16, fontweight="bold")
    ax.axhline(0, color="gray", lw=1.0, ls=":")

    # Legend for wells
    legend_patches = [
        mpatches.Patch(color=WELL_COLORS[s], label=s)
        for s in ["HONGLUN", "TUKU", "LUNZI", "LIUZHUANG"]
    ]
    ax.legend(handles=legend_patches, fontsize=12, title="Assigned well")
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    save(fig, "hc_comparison.png")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Generating TUKU tau-search result figures...")
    print(f"  Output dir: {PLOT_DIR}\n")

    fig1_mse_all()
    fig2_mse_individual()
    fig3_gwl_regime()
    fig4_cumulative_mlcw()
    fig5_incremental_gwl()
    fig6_incremental_mlcw()
    fig7_regime_bar()
    fig8_combined_normalized()
    fig9_hc_comparison()

    print("\nAll figures generated successfully.")

    # List output files
    saved = sorted(os.listdir(PLOT_DIR))
    print("\nFiles in output directory:")
    for f in saved:
        print(f"  {f}")
