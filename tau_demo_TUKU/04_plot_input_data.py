"""
04_plot_input_data.py
=====================
Visualises raw input datasets used in the tau_demo_TUKU pipeline.

Output (plots/input/):
  - input_daily_gwl.png          raw daily GWL for all 5 wells
  - input_cumulative_mlcw.png    cumulative MLCW compaction (6 layers)
  - input_incremental_gwl.png    delta-H per epoch (6 layers)
  - input_incremental_mlcw.png   delta-b per epoch (6 layers)
  - input_all_data_combined.png  all 4 signals scaled to [0,1] per layer
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from plot_style import DPI, A4_PORTRAIT, FONT, LW, style_ax, apply_style
apply_style()

# ── Paths ─────────────────────────────────────────────────────────────────────
DEMO_DIR    = Path(__file__).resolve().parent
DATA_DIR    = DEMO_DIR / "data"
RESULTS_DIR = DEMO_DIR / "results"
PLOTS_DIR   = DEMO_DIR / "plots" / "input"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Colours ───────────────────────────────────────────────────────────────────
COLORS   = {ly: plt.cm.tab10(i) for i, ly in enumerate(["F1", "T1", "F2", "T2", "F3", "F4"])}
LAYERS   = ["F1", "T1", "F2", "T2", "F3", "F4"]
WELL_STATIONS = ["HONGLUN", "TUKU", "LUNZI", "LIUZHUANG"]
WELL_COLORS   = {s: plt.cm.tab10(i) for i, s in enumerate(WELL_STATIONS)}

T_START = pd.Timestamp("2015-01-01")
T_END   = pd.Timestamp("2026-01-01")

# ── Load data ─────────────────────────────────────────────────────────────────
npz      = np.load(RESULTS_DIR / "tuku_aligned_data.npz", allow_pickle=True)
tau_info = pd.read_csv(RESULTS_DIR / "tau_results.csv").set_index("layer")
mlcw_csv = pd.read_csv(DATA_DIR / "TUKU_reconst_grouped.csv", parse_dates=["datetime"])

feather_files = {}
layer_wells   = {}
for layer in LAYERS:
    if layer not in tau_info.index:
        continue
    wc       = str(tau_info.loc[layer, "wellcode"])
    gwl_file = str(tau_info.loc[layer, "gwl_file"])
    layer_wells[layer] = (wc, gwl_file)
    if gwl_file not in feather_files:
        fp = DATA_DIR / gwl_file
        if fp.exists():
            df = pd.read_feather(fp)
            df["datetime"] = pd.to_datetime(df["datetime"])
            feather_files[gwl_file] = df


def load_npz_layer(layer):
    d = {}
    for key in npz.files:
        if key.startswith(f"{layer}__"):
            d[key[len(f"{layer}__"):]] = npz[key]
    d["dates"]     = pd.to_datetime(d["dates"])
    d["inc_dates"] = pd.to_datetime(d["inc_dates"])
    return d


def scale_to_01(*arrays):
    out = []
    for a in arrays:
        a = np.asarray(a, dtype=float)
        finite = np.isfinite(a)
        if finite.sum() < 2:
            out.append(a); continue
        mn, mx = a[finite].min(), a[finite].max()
        out.append((a - mn) / (mx - mn) if mx - mn > 1e-12 else np.zeros_like(a))
    return out


def save(fig, name):
    fig.savefig(PLOTS_DIR / name, dpi=DPI, pad_inches=0.15)
    plt.close(fig)
    print(f"Saved: {name}")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 1: Raw daily GWL — all 5 wells
# ══════════════════════════════════════════════════════════════════════════════

fig, axes = plt.subplots(5, 1, figsize=(A4_PORTRAIT[0], 10.0), sharex=True)
fig.suptitle("TUKU — Raw daily GWL (piezometric head) for all 5 assigned wells",
             fontsize=FONT["suptitle"], fontweight="bold", y=0.97)

for idx, (gwl_file, df) in enumerate(feather_files.items()):
    ax = axes[idx]
    stem = gwl_file.replace("_gwl_timeseries.feather", "")
    df_win = df[(df["datetime"] >= T_START) & (df["datetime"] < T_END)]
    well_cols = [c for c in df_win.columns if c != "datetime"]
    for j, col in enumerate(well_cols):
        color = plt.cm.tab10(j % 10)
        ax.plot(df_win["datetime"], df_win[col], linewidth=LW["data"],
                color=color, alpha=0.85, label=f"well {col}")
    ax.set_ylabel("Head (m MSL)", fontsize=FONT["axis_label"])
    ax.legend(fontsize=FONT["legend"], loc="upper right")
    ax.set_title(f"{stem}  ({gwl_file})", fontsize=FONT["title"], fontweight="bold")
    style_ax(ax)
    ax.grid(True, alpha=0.3)

axes[-1].set_xlabel("Date", fontsize=FONT["axis_label"])
fig.subplots_adjust(top=0.92, hspace=0.35)
save(fig, "input_daily_gwl.png")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 2: Cumulative MLCW compaction — 6 layers (zero-referenced)
# ══════════════════════════════════════════════════════════════════════════════

fig, axes = plt.subplots(6, 1, figsize=(A4_PORTRAIT[0], 10.5), sharex=True)
fig.suptitle("TUKU — Cumulative MLCW compaction (zero-referenced to 2015-01-16)",
             fontsize=FONT["suptitle"], fontweight="bold", y=0.97)

for i, layer in enumerate(LAYERS):
    ax = axes[i]
    if layer not in mlcw_csv.columns:
        ax.set_visible(False); continue
    ax.plot(mlcw_csv["datetime"], mlcw_csv[layer], linewidth=LW["data"], color=COLORS[layer])
    ax.set_ylabel("Compaction (mm)", fontsize=FONT["axis_label"])
    ax.set_title(f"Layer {layer}", fontsize=FONT["title"], fontweight="bold", color=COLORS[layer])
    ax.axhline(0, color="grey", linewidth=LW["reference"], linestyle="--")
    style_ax(ax)
    ax.grid(True, alpha=0.3)

axes[-1].set_xlabel("Date", fontsize=FONT["axis_label"])
fig.subplots_adjust(top=0.93, hspace=0.40)
save(fig, "input_cumulative_mlcw.png")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 3: Incremental GWL change — 6 layers
# ══════════════════════════════════════════════════════════════════════════════

fig, axes = plt.subplots(6, 1, figsize=(A4_PORTRAIT[0], 10.5), sharex=True)
fig.suptitle("TUKU — Incremental GWL change Delta-H per epoch (input to tau search)",
             fontsize=FONT["suptitle"], fontweight="bold", y=0.97)

for i, layer in enumerate(LAYERS):
    ax = axes[i]
    if layer not in tau_info.index:
        ax.set_visible(False); continue
    d = load_npz_layer(layer)
    inc_dates = d["inc_dates"]
    inc_dH    = d["inc_dH"].astype(float)
    mask      = (inc_dates >= T_START) & (inc_dates < T_END)
    ax.plot(inc_dates[mask], inc_dH[mask], linewidth=LW["data"], color=COLORS[layer], alpha=0.9)
    ax.set_ylabel("Delta-H (m/epoch)", fontsize=FONT["axis_label"])
    ax.set_title(f"Layer {layer}  (well {d['wellcode']})", fontsize=FONT["title"],
                 fontweight="bold", color=COLORS[layer])
    ax.axhline(0, color="grey", linewidth=LW["reference"], linestyle="-")
    style_ax(ax)
    ax.grid(True, alpha=0.3)

axes[-1].set_xlabel("Date", fontsize=FONT["axis_label"])
fig.subplots_adjust(top=0.93, hspace=0.40)
save(fig, "input_incremental_gwl.png")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 4: Incremental MLCW compaction — 6 layers
# ══════════════════════════════════════════════════════════════════════════════

fig, axes = plt.subplots(6, 1, figsize=(A4_PORTRAIT[0], 10.5), sharex=True)
fig.suptitle("TUKU — Incremental MLCW compaction Delta-b per epoch (observed)",
             fontsize=FONT["suptitle"], fontweight="bold", y=0.97)

for i, layer in enumerate(LAYERS):
    ax = axes[i]
    if layer not in tau_info.index:
        ax.set_visible(False); continue
    d = load_npz_layer(layer)
    inc_dates = d["inc_dates"]
    inc_db    = d["inc_db"].astype(float)
    mask      = (inc_dates >= T_START) & (inc_dates < T_END)
    ax.plot(inc_dates[mask], inc_db[mask], linewidth=LW["data"], color=COLORS[layer], alpha=0.9)
    ax.set_ylabel("Delta-b (mm/epoch)", fontsize=FONT["axis_label"])
    ax.set_title(f"Layer {layer}", fontsize=FONT["title"], fontweight="bold", color=COLORS[layer])
    ax.axhline(0, color="grey", linewidth=LW["reference"], linestyle="-")
    style_ax(ax)
    ax.grid(True, alpha=0.3)

axes[-1].set_xlabel("Date", fontsize=FONT["axis_label"])
fig.subplots_adjust(top=0.93, hspace=0.40)
save(fig, "input_incremental_mlcw.png")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 5: Combined — all 4 signals scaled to [0,1] per layer
# ══════════════════════════════════════════════════════════════════════════════

fig, axes = plt.subplots(6, 1, figsize=(A4_PORTRAIT[0], 11.0), sharex=True)
fig.suptitle(
    "TUKU — All input signals scaled to [0,1] per layer\n"
    "Daily GWL | Cumulative MLCW | Incremental GWL (Delta-H) | Incremental MLCW (Delta-b)",
    fontsize=FONT["suptitle"], fontweight="bold", y=0.97,
)

for i, layer in enumerate(LAYERS):
    ax = axes[i]
    if layer not in tau_info.index:
        ax.set_visible(False); continue

    d  = load_npz_layer(layer)
    wc, gwl_file = layer_wells[layer]

    df_gwl  = feather_files[gwl_file]
    df_win  = df_gwl[(df_gwl["datetime"] >= T_START) & (df_gwl["datetime"] < T_END)]
    gwl_d   = df_win["datetime"]
    gwl_v   = df_win[wc].values.astype(float) if wc in df_win.columns else np.full(len(df_win), np.nan)

    cum_d = mlcw_csv["datetime"]
    cum_v = mlcw_csv[layer].values.astype(float) if layer in mlcw_csv.columns else np.full(len(mlcw_csv), np.nan)

    inc_dates = d["inc_dates"]
    inc_mask  = (inc_dates >= T_START) & (inc_dates < T_END)
    incH_win  = d["inc_dH"].astype(float)[inc_mask]
    incb_win  = d["inc_db"].astype(float)[inc_mask]
    inc_d_win = inc_dates[inc_mask]

    g_s, c_s, h_s, b_s = scale_to_01(gwl_v, cum_v, incH_win, incb_win)

    ax.plot(gwl_d, g_s, linewidth=LW["data"], color="steelblue", alpha=0.7, label="Daily GWL head")
    ax.plot(cum_d, c_s, linewidth=LW["data"], color="crimson", alpha=0.8,
            label="Cumulative MLCW compaction")
    ax.scatter(inc_d_win, h_s, s=4, color="mediumseagreen", alpha=0.3,
               label="Incremental GWL Delta-H")
    ax.scatter(inc_d_win, b_s, s=4, color="darkorange", alpha=0.3,
               label="Incremental MLCW Delta-b")
    ax.set_ylabel("Scaled [0,1]", fontsize=FONT["axis_label"])
    ax.set_title(
        f"Layer {layer}  (well {wc},  {gwl_file.replace('_gwl_timeseries.feather','')})",
        fontsize=FONT["title"], fontweight="bold", color=COLORS[layer])
    ax.legend(fontsize=FONT["legend"] - 1, loc="upper right", ncol=2)
    style_ax(ax)
    ax.grid(True, alpha=0.3)

axes[-1].set_xlabel("Date", fontsize=FONT["axis_label"])
fig.subplots_adjust(top=0.92, hspace=0.38)
save(fig, "input_all_data_combined.png")

print("\nAll input data plots complete. Check tau_demo_TUKU/plots/input/")
