#!/usr/bin/env python3
"""
gps_mlcw_cross_correlation.py — Cross-correlation between GPS surface displacement
and MLCW compaction at TUKU (layer-by-layer, ring-by-ring, and total).

Tests the physical hypothesis: GPS surface displacement — the depth-integral of
subsurface compaction — should correlate strongly with TOTAL column compaction at
near-zero lag, but weakly with any single layer or ring.

Data sources
------------
  GPS:     data/gps/modeled/TKJS_model.csv          (daily, 2010–2024, 'modeled' column)
  Layers:  data/mlcw/group_byLayer_reconstr/TUKU_reconst_grouped.csv   (5-day, F1..F4)
  Rings:   data/mlcw/reconstructed/TUKU_ringbyring_reconstructed.csv   (5-day, 23 rings)

Outputs
-------
  results/gps_mlcw_xcorr/gps_mlcw_xcorr_summary.json
  figures/gps_mlcw_xcorr/gps_vs_total_xcorr.png        — xcorr-style, GPS vs total
  figures/gps_mlcw_xcorr/gps_vs_layers_ccf.png          — 6-panel per-layer CCF
  figures/gps_mlcw_xcorr/gps_vs_rings_heatmap.png       — 23 rings × lags heatmap
  figures/gps_mlcw_xcorr/gps_vs_total_timeseries.png    — GPS + total overlaid

Usage
-----
  PYTHONPATH="" conda run -n fafalab2 python scripts/11_data_analysis/gps_mlcw_cross_correlation.py
"""

import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator

import numpy as np
import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

STATION = "TUKU"
GPS_CODE = "TKJS"

GPS_PATH = PROJECT_ROOT / f"data/gps/modeled/{GPS_CODE}_model.csv"
LAYER_PATH = PROJECT_ROOT / f"data/mlcw/group_byLayer_reconstr/{STATION}_reconst_grouped.csv"
RING_PATH = PROJECT_ROOT / f"data/mlcw/reconstructed/{STATION}_ringbyring_reconstructed.csv"

RESULTS_DIR = PROJECT_ROOT / "results/gps_mlcw_xcorr"
FIGURES_DIR = PROJECT_ROOT / "figures/gps_mlcw_xcorr"

# Output naming convention: {STATION}_{content}.{ext}
RESULT_JSON = RESULTS_DIR / f"{STATION}_gps_mlcw_xcorr_summary.json"
FIG_TOTAL_XCORR    = FIGURES_DIR / f"{STATION}_gps_vs_total_xcorr.png"
FIG_LAYERS_CCF     = FIGURES_DIR / f"{STATION}_gps_vs_layers_ccf.png"
FIG_RINGS_HEATMAP  = FIGURES_DIR / f"{STATION}_gps_vs_rings_heatmap.png"
FIG_TIMESERIES     = FIGURES_DIR / f"{STATION}_gps_vs_total_timeseries.png"

MAX_LAG_EPOCHS = 120       # 5-day epochs = ±600 days
GPS_COL = "modeled"
LAYERS = ["F1", "T1", "F2", "T2", "F3", "F4"]
LAYER_CLASS = {"F1": "aquifer", "T1": "aquitard", "F2": "aquifer",
               "T2": "aquitard", "F3": "aquifer", "F4": "aquitard"}

# ── Plot style ────────────────────────────────────────────────────────────────
CM = 1 / 2.54
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 12,
    "axes.labelsize": 14,
    "axes.titlesize": 14,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.1,
    "legend.fontsize": 10,
})

COLORS = {
    "gps":      "#d73027",   # red
    "total":    "#2166ac",   # blue
    "aquifer":  "#4292c6",   # lighter blue
    "aquitard": "#f4a582",   # salmon/orange
    "best_lag": "#1a9850",   # green
    "zero_lag": "#525252",   # dark gray
}


def _style_ax(ax):
    """Apply consistent axis styling."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, linestyle="--", alpha=0.3, color="gray")
    ax.tick_params(direction="in")


def linear_detrend(y, t_days):
    """Remove least-squares linear trend using actual datetime-derived time values.

    Parameters
    ----------
    y : np.ndarray
        Signal to detrend.
    t_days : np.ndarray
        Time axis in days since a reference date (same length as y).
        Must use real calendar time, not array index — otherwise the trend
        slope is wrong when data span years.

    Returns
    -------
    detrended : np.ndarray
    slope_per_day : float
    """
    mask = np.isfinite(y) & np.isfinite(t_days)
    n = mask.sum()
    if n < 3:
        return y.copy(), 0.0
    p = np.polyfit(t_days[mask], y[mask], 1)
    trend = np.polyval(p, t_days)
    slope = p[0]  # units: y-units per day
    return y - trend, slope


def compute_ccf(gps, target, max_lag=MAX_LAG_EPOCHS, min_pairs=10):
    """Compute cross-correlation between GPS and target for lags in [-max_lag, +max_lag].

    Positive lag = GPS LEADS target (GPS shifted earlier relative to compaction).
    Both inputs are detrended BEFORE entering this function.

    Returns
    -------
    lags : np.ndarray of int (lag in epochs)
    corrs : np.ndarray of float (Pearson r at each lag)
    best_lag : int (epochs)
    best_r : float
    r_at_zero : float
    n_pairs_zero : int (number of valid observation pairs at zero lag)
    """
    n = len(gps)
    lags = np.arange(-max_lag, max_lag + 1)
    corrs = np.full(len(lags), np.nan)
    n_pairs_arr = np.zeros(len(lags), dtype=int)

    for idx, tau in enumerate(lags):
        if tau >= 0:
            gps_s = gps[:n - tau]
            tgt_s = target[tau:]
        else:
            shift = -tau
            gps_s = gps[shift:]
            tgt_s = target[:n - shift]

        mask = np.isfinite(gps_s) & np.isfinite(tgt_s)
        nv = mask.sum()
        n_pairs_arr[idx] = nv
        if nv >= min_pairs:
            corrs[idx] = float(np.corrcoef(gps_s[mask], tgt_s[mask])[0, 1])

    # Best lag: where |r| is maximised
    valid = np.isfinite(corrs)
    if not valid.any():
        return lags, corrs, 0, float("nan"), float("nan"), 0

    best_idx = int(np.nanargmax(np.abs(corrs)))
    best_lag = int(lags[best_idx])
    best_r = float(corrs[best_idx])

    # r at zero lag + n_pairs at zero lag
    zero_idx = int(np.where(lags == 0)[0][0])
    r_zero = float(corrs[zero_idx]) if np.isfinite(corrs[zero_idx]) else float("nan")
    n_zero = int(n_pairs_arr[zero_idx])

    return lags, corrs, best_lag, best_r, r_zero, n_zero


# ── Main pipeline ─────────────────────────────────────────────────────────────

def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(FIGURES_DIR, exist_ok=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # 1. Load and align data
    # ═══════════════════════════════════════════════════════════════════════════

    print("=" * 70)
    print("GPS–MLCW Cross-Correlation Analysis")
    print("=" * 70)

    # ── GPS (daily) ────────────────────────────────────────────────────────
    gps_raw = pd.read_csv(GPS_PATH, parse_dates=["date"])
    gps_raw = gps_raw.sort_values("date").reset_index(drop=True)
    print(f"GPS loaded: {len(gps_raw)} rows, "
          f"{gps_raw['date'].iloc[0].date()} → {gps_raw['date'].iloc[-1].date()}")

    # ── MLCW layers (5-day) ────────────────────────────────────────────────
    layer_df = pd.read_csv(LAYER_PATH, parse_dates=["datetime"])
    layer_df = layer_df.rename(columns={"datetime": "date"}).sort_values("date")
    layer_df = layer_df.reset_index(drop=True)
    print(f"Layers loaded: {len(layer_df)} rows, "
          f"{layer_df['date'].iloc[0].date()} → {layer_df['date'].iloc[-1].date()}")

    # ── MLCW rings (5-day) ────────────────────────────────────────────────
    ring_df = pd.read_csv(RING_PATH, parse_dates=["datetime"])
    ring_df = ring_df.rename(columns={"datetime": "date"}).sort_values("date")
    ring_df = ring_df.reset_index(drop=True)

    # Identify ring columns (numeric headers = depth in metres)
    ring_cols = []
    for col in ring_df.columns:
        if col == "date":
            continue
        try:
            float(col)
            ring_cols.append(col)
        except (ValueError, TypeError):
            continue
    # Sort by depth (ascending)
    ring_depths = sorted(ring_cols, key=lambda x: float(x))
    print(f"Rings loaded: {len(ring_df)} rows, {len(ring_depths)} ring columns "
          f"({ring_depths[0]}–{ring_depths[-1]} m)")

    # ── Total compaction = sum of all rings ────────────────────────────────
    ring_df["Total"] = ring_df[ring_depths].sum(axis=1)
    print(f"Total compaction range: {ring_df['Total'].min():.1f} to "
          f"{ring_df['Total'].max():.1f} mm")

    # ── Align: exact date intersection (GPS is daily, covers all MLCW 5-day dates) ─
    gps_ts = gps_raw[["date", GPS_COL]].copy()
    gps_ts = gps_ts.rename(columns={GPS_COL: "gps_mm"})
    gps_ts = gps_ts.set_index("date")
    ring_df_idx = ring_df.set_index("date")

    # Intersection: dates present in BOTH GPS (daily) and MLCW (5-day)
    mutual_idx = gps_ts.index.intersection(ring_df_idx.index)
    n_overlap = len(mutual_idx)
    print(f"GPS–MLCW overlap (exact date match): {n_overlap} epochs "
          f"({mutual_idx[0].date()} → {mutual_idx[-1].date()})")

    # Build merged DataFrame from exact matches
    merged = pd.DataFrame(index=mutual_idx)
    merged.index.name = "date"
    merged["gps_mm"] = gps_ts.loc[mutual_idx, "gps_mm"]
    merged["Total"] = ring_df_idx.loc[mutual_idx, "Total"]
    for r in ring_depths:
        merged[r] = ring_df_idx.loc[mutual_idx, r]
    # Add layer columns
    layer_idx = layer_df.set_index("date")
    for L in LAYERS:
        merged[L] = layer_idx.loc[mutual_idx, L]
    merged = merged.reset_index()

    # ── Cross-validate: total ≈ sum of layers ──────────────────────────────
    layer_sum = merged[LAYERS].sum(axis=1)
    total_vs_layers_diff = (layer_sum - merged["Total"]).abs()
    print(f"|Σ(layers) − Total|: max={total_vs_layers_diff.max():.4f} mm, "
          f"mean={total_vs_layers_diff.mean():.6f} mm "
          f"(cross-validation: should be near zero)")

    # ═══════════════════════════════════════════════════════════════════════════
    # 2. Cross-correlation engine
    # ═══════════════════════════════════════════════════════════════════════════

    # Build time axis in days since first overlap date (for correct detrending)
    t_ref = merged["date"].iloc[0]
    t_days = (merged["date"] - t_ref).dt.days.to_numpy(float)

    # Zero-reference GPS: subtract first valid value so series starts at zero
    gps_overlap = merged["gps_mm"].to_numpy(float)
    gps_first = gps_overlap[0]
    gps_zeroed = gps_overlap - gps_first
    # Also pre-compute zero-referenced total for plotting
    total_raw = merged["Total"].to_numpy(float)
    total_zeroed = total_raw - total_raw[0]

    gps_det, gps_slope = linear_detrend(gps_zeroed, t_days)
    print(f"\nGPS: first={gps_first:.1f} mm, zero-ref → detrend")
    print(f"  slope={gps_slope:.6f} mm/day ({gps_slope * 365.25:.1f} mm/yr), "
          f"σ={np.nanstd(gps_det):.2f} mm")

    all_targets = {}
    # Layers
    for L in LAYERS:
        all_targets[L] = {"kind": "layer", "data": merged[L].to_numpy(float)}
    # Rings
    for r in ring_depths:
        all_targets[r] = {"kind": "ring", "data": merged[r].to_numpy(float)}
    # Total
    all_targets["Total"] = {"kind": "total", "data": merged["Total"].to_numpy(float)}

    results = {}
    print("\n--- Cross-correlation results (zero-ref → detrend → CCF) ---")
    print(f"{'Target':>10s}  {'first':>10s}  {'best_lag_d':>10s}  {'r_best':>8s}  "
          f"{'r_zero':>8s}  {'n_pairs':>8s}")
    print("-" * 66)

    for name, info in all_targets.items():
        raw = info["data"]
        tgt_first = raw[0]
        tgt_zeroed = raw - tgt_first
        tgt_det, tgt_slope = linear_detrend(tgt_zeroed, t_days)
        lags, corrs, best_lag, best_r, r_zero, n_pairs = compute_ccf(
            gps_det, tgt_det
        )
        results[name] = {
            "kind": info["kind"],
            "first_value_mm": round(float(tgt_first), 2),
            "lag_epochs": best_lag,
            "lag_days": best_lag * 5,
            "r_at_best_lag": round(best_r, 4) if np.isfinite(best_r) else None,
            "r_at_zero_lag": round(r_zero, 4) if np.isfinite(r_zero) else None,
            "n_pairs": n_pairs,
            "target_slope_mm_per_day": round(tgt_slope, 6),
        }
        # Store CCF curve for later use
        results[name]["_lags"] = lags
        results[name]["_corrs"] = corrs

        if np.isfinite(best_r):
            print(f"{name:>10s}  {tgt_first:>+10.1f}  {best_lag * 5:>+10d}  "
                  f"{best_r:>+8.4f}  {r_zero:>+8.4f}  {n_pairs:>8d}")
        else:
            print(f"{name:>10s}  {tgt_first:>+10.1f}  {'N/A':>10s}  {'N/A':>8s}  "
                  f"{'N/A':>8s}  {0:>8d}")

    # ═══════════════════════════════════════════════════════════════════════════
    # 3. Figures
    # ═══════════════════════════════════════════════════════════════════════════

    # ── Figure A: GPS vs Total (xcorr style, 3-panel) ─────────────────────
    print("\n--- Figure A: GPS vs Total Compaction (xcorr style) ---")
    fig_a, axes_a = plt.subplots(3, 1, figsize=(22 * CM, 28 * CM),
                                  gridspec_kw={"height_ratios": [1.5, 1, 1]})

    # Panel 1: Timeseries overlay (zero-referenced, shared y-axis)
    ax0 = axes_a[0]
    dates = merged["date"]
    ax0.plot(dates, gps_zeroed, color=COLORS["gps"], linewidth=1.8,
             alpha=0.85, label="GPS displacement (mm)")
    ax0.plot(dates, total_zeroed, color=COLORS["total"], linewidth=2.0,
             alpha=0.85, label="Total MLCW compaction (mm)")
    ax0.set_ylabel("Zero-referenced displacement (mm)")
    ax0.set_title(f"{STATION} — GPS vs Total Column Compaction (zero-referenced, shared axis)",
                  fontsize=15, fontweight="bold")
    ax0.legend(loc="upper left", fontsize=9)
    ax0.xaxis.set_major_locator(mdates.YearLocator(2))
    ax0.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    peak = min(gps_zeroed.min(), total_zeroed.min()) * 1.05
    ax0.set_ylim(peak, 0)
    _style_ax(ax0)

    # Panel 2: CCF curve (xcorr-style stem plot)
    ax1 = axes_a[1]
    total_res = results["Total"]
    lags_days = total_res["_lags"] * 5
    corrs = total_res["_corrs"]
    valid_c = np.isfinite(corrs)
    # Stem plot: marker on every Nth point for readability
    step = max(1, len(lags_days) // 120)  # ~120 markers
    marker_idx = np.arange(0, len(lags_days), step)
    ax1.vlines(lags_days[valid_c], 0, corrs[valid_c],
               colors="lightgray", linewidths=0.6, zorder=1)
    ax1.scatter(lags_days[marker_idx], corrs[marker_idx],
                s=12, color=COLORS["total"], zorder=3)
    ax1.axhline(0, color="black", linewidth=0.5)
    # Mark best lag and zero lag
    best_lag_d = total_res["lag_days"]
    best_r = total_res["r_at_best_lag"]
    ax1.axvline(best_lag_d, color=COLORS["best_lag"], linestyle="--", linewidth=1.5,
                label=f"Best lag: {best_lag_d:+d} d, r={best_r:+.4f}")
    ax1.axvline(0, color=COLORS["zero_lag"], linestyle=":", linewidth=1.2,
                label=f"Zero lag: r={total_res['r_at_zero_lag']:+.4f}")
    ax1.set_xlabel("GPS lead time (days) — positive = GPS leads compaction")
    ax1.set_ylabel("Pearson r (detrended)")
    ax1.set_title("Cross-Correlation Function: GPS ↔ Total Compaction",
                  fontsize=13, fontweight="bold")
    ax1.legend(loc="upper right", fontsize=9)
    _style_ax(ax1)

    # Panel 3: Detrended scatter at best lag
    ax2 = axes_a[2]
    tau = total_res["lag_epochs"]
    n = len(gps_det)
    total_det_full, _ = linear_detrend(total_zeroed, t_days)
    if tau >= 0:
        gps_s = gps_det[:n - tau]
        tgt_s = total_det_full[tau:]
    else:
        shift = -tau
        gps_s = gps_det[shift:]
        tgt_s = total_det_full[:n - shift]
    mask = np.isfinite(gps_s) & np.isfinite(tgt_s)
    ax2.scatter(gps_s[mask], tgt_s[mask], s=1, alpha=0.3, color="dimgray")
    # Fit line
    if mask.sum() > 2:
        p = np.polyfit(gps_s[mask], tgt_s[mask], 1)
        x_fit = np.linspace(gps_s[mask].min(), gps_s[mask].max(), 100)
        ax2.plot(x_fit, np.polyval(p, x_fit), color=COLORS["total"], linewidth=1.5,
                 label=f"Slope = {p[0]:.3f} mm/mm")
    ax2.set_xlabel("Detrended GPS (mm)")
    ax2.set_ylabel("Detrended total compaction (mm)")
    ax2.set_title(f"Detrended Scatter at Optimal Lag ({best_lag_d:+d} days)",
                  fontsize=13, fontweight="bold")
    ax2.legend(loc="upper left", fontsize=9)
    ax2.axhline(0, color="black", linewidth=0.5)
    ax2.axvline(0, color="black", linewidth=0.5)
    _style_ax(ax2)

    fig_a.tight_layout()
    path_a = FIG_TOTAL_XCORR
    fig_a.savefig(path_a, dpi=300, facecolor="w", edgecolor="w")
    plt.close(fig_a)
    print(f"  Saved: {path_a}")

    # ── Figure B: Per-Layer CCF (3×2) ─────────────────────────────────────
    print("--- Figure B: Per-Layer CCF ---")
    fig_b, axes_b = plt.subplots(3, 2, figsize=(28 * CM, 22 * CM))
    fig_b.subplots_adjust(hspace=0.35, wspace=0.15)

    for idx, L in enumerate(LAYERS):
        ax = axes_b.flat[idx]
        res = results[L]
        lags_d = res["_lags"] * 5
        corrs = res["_corrs"]
        cls = LAYER_CLASS[L]
        color = COLORS["aquifer"] if cls == "aquifer" else COLORS["aquitard"]

        ax.plot(lags_d, np.where(np.isfinite(corrs), corrs, np.nan),
                color=color, linewidth=1.5)
        ax.axhline(0, color="black", linewidth=0.5)
        ax.axvline(0, color=COLORS["zero_lag"], linestyle=":", linewidth=0.8,
                   alpha=0.6)
        bl = res["lag_days"]
        br = res["r_at_best_lag"]
        if br is not None:
            ax.axvline(bl, color=COLORS["best_lag"], linestyle="--", linewidth=1.2)
            ax.scatter([bl], [br], color=COLORS["best_lag"], s=40, zorder=5)
            ax.annotate(f"τ={bl:+d}d\nr={br:+.3f}",
                        xy=(bl, br), xytext=(10, 10),
                        textcoords="offset points", fontsize=8,
                        bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                                  edgecolor="gray", alpha=0.85))

        ax.set_title(f"{L} ({cls})", fontsize=13, fontweight="bold")
        ax.set_xlabel("GPS lead time (days)")
        ax.set_ylabel("Pearson r")
        ax.set_ylim(-1.05, 1.05)
        _style_ax(ax)

    fig_b.suptitle(f"{STATION} — Per-Layer GPS↔MLCW Cross-Correlation",
                   fontsize=16, fontweight="bold", y=1.01)
    path_b = FIG_LAYERS_CCF
    fig_b.savefig(path_b, dpi=300, facecolor="w", edgecolor="w")
    plt.close(fig_b)
    print(f"  Saved: {path_b}")

    # ── Figure C: Rings × Lags Heatmap ────────────────────────────────────
    print("--- Figure C: Rings × Lags Heatmap ---")
    n_rings = len(ring_depths)
    # Down-sample lags for heatmap readability
    lag_step = 4  # every 4 epochs = 20 days
    lag_idxs = np.arange(0, 2 * MAX_LAG_EPOCHS + 1, lag_step)
    lag_labels = [(int(i) - MAX_LAG_EPOCHS) * 5 for i in lag_idxs]

    heatmap = np.full((n_rings, len(lag_idxs)), np.nan)
    for ri, rd in enumerate(ring_depths):
        res = results[rd]
        full_corrs = res["_corrs"]
        for ci, li in enumerate(lag_idxs):
            if li < len(full_corrs):
                heatmap[ri, ci] = full_corrs[li]

    fig_c, ax_c = plt.subplots(figsize=(32 * CM, 18 * CM))

    # Ring depth labels
    depth_labels = [f"{float(d):.1f} m" for d in ring_depths]
    depth_values = [float(d) for d in ring_depths]

    # Build y-axis edges for proportional spacing
    dv = np.array(depth_values)
    if len(dv) > 1:
        y_edges = np.empty(len(dv) + 1)
        y_edges[0] = dv[0] - (dv[1] - dv[0]) / 2
        y_edges[1:-1] = (dv[:-1] + dv[1:]) / 2
        y_edges[-1] = dv[-1] + (dv[-1] - dv[-2]) / 2
    else:
        y_edges = np.array([dv[0] - 0.5, dv[0] + 0.5])

    x_edges = np.arange(len(lag_idxs) + 1)

    im = ax_c.pcolormesh(x_edges, y_edges, heatmap,
                          cmap="RdBu_r", vmin=-1.0, vmax=1.0)
    ax_c.invert_yaxis()
    ax_c.set_yticks(depth_values)
    ax_c.set_yticklabels(depth_labels, fontsize=9)
    ax_c.set_xticks(np.arange(len(lag_idxs)) + 0.5)
    # Show every Nth x-tick label
    xtick_step = max(1, len(lag_idxs) // 20)
    ax_c.set_xticklabels([lag_labels[i] if i % xtick_step == 0 else ""
                          for i in range(len(lag_idxs))],
                         rotation=45, fontsize=8, ha="right")
    ax_c.set_xlabel("GPS lead time (days) — positive = GPS leads", fontsize=12)
    ax_c.set_ylabel("Ring depth (m)", fontsize=12)

    # Mark total compaction best lag
    total_best_lag_d = results["Total"]["lag_days"]
    total_best_x = (total_best_lag_d // 5 + MAX_LAG_EPOCHS) / lag_step
    ax_c.axvline(total_best_x, color=COLORS["best_lag"], linestyle="--",
                 linewidth=2.5, label=f"Total best lag: {total_best_lag_d:+d} d")
    ax_c.axvline(MAX_LAG_EPOCHS // lag_step, color=COLORS["zero_lag"],
                 linestyle=":", linewidth=1.5, alpha=0.7, label="Zero lag")

    cbar = fig_c.colorbar(im, ax=ax_c, shrink=0.85, pad=0.02)
    cbar.set_label("Pearson r (detrended)", fontsize=12)
    cbar.ax.tick_params(labelsize=10)

    ax_c.set_title(f"{STATION} — GPS↔Ring Cross-Correlation by Depth and Lag",
                   fontsize=15, fontweight="bold", pad=12)
    ax_c.legend(loc="upper right", fontsize=9)

    _style_ax(ax_c)
    for spine in ["top", "right"]:
        ax_c.spines[spine].set_visible(False)

    path_c = FIG_RINGS_HEATMAP
    fig_c.savefig(path_c, dpi=300, facecolor="w", edgecolor="w")
    plt.close(fig_c)
    print(f"  Saved: {path_c}")

    # ── Figure D: GPS vs Total Timeseries ─────────────────────────────────
    print("--- Figure D: GPS vs Total Timeseries ---")
    fig_d, axes_d = plt.subplots(2, 1, figsize=(26 * CM, 20 * CM))

    # Panel 1: Zero-referenced cumulative (shared y-axis)
    ax_d0 = axes_d[0]
    ax_d0.plot(dates, gps_zeroed, color=COLORS["gps"], linewidth=1.8,
               alpha=0.85, label="GPS displacement (mm)")
    ax_d0.plot(dates, total_zeroed, color=COLORS["total"], linewidth=2.0,
               alpha=0.85, label="Total MLCW compaction (mm)")
    ax_d0.set_ylabel("Zero-referenced displacement (mm)")
    ax_d0.legend(loc="upper left", fontsize=9)
    ax_d0.set_title(f"{STATION} — GPS vs Total Column Compaction (zero-referenced, shared axis)",
                    fontsize=14, fontweight="bold")
    ax_d0.xaxis.set_major_locator(mdates.YearLocator(2))
    ax_d0.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    peak = min(gps_zeroed.min(), total_zeroed.min()) * 1.05
    ax_d0.set_ylim(peak, 0)
    _style_ax(ax_d0)

    # Panel 2: Detrended (shared y-axis)
    ax_d1 = axes_d[1]
    total_det, _ = linear_detrend(total_zeroed, t_days)
    ax_d1.plot(dates, gps_det, color=COLORS["gps"], linewidth=1.5,
               alpha=0.85, label="GPS (detrended)")
    ax_d1.plot(dates, total_det, color=COLORS["total"], linewidth=1.5,
               alpha=0.85, label="Total compaction (detrended)")
    ax_d1.set_ylabel("Detrended displacement (mm)")
    ax_d1.legend(loc="upper left", fontsize=9)
    ax_d1.set_title("Detrended — Sub-Annual Dynamics",
                    fontsize=14, fontweight="bold")
    ax_d1.xaxis.set_major_locator(mdates.YearLocator(2))
    ax_d1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    _style_ax(ax_d1)

    fig_d.tight_layout()
    path_d = FIG_TIMESERIES
    fig_d.savefig(path_d, dpi=300, facecolor="w", edgecolor="w")
    plt.close(fig_d)
    print(f"  Saved: {path_d}")

    # ═══════════════════════════════════════════════════════════════════════════
    # 4. Hypothesis test and JSON output
    # ═══════════════════════════════════════════════════════════════════════════

    total_r = abs(results["Total"]["r_at_best_lag"])
    max_layer_r = max(abs(results[L]["r_at_best_lag"]) for L in LAYERS
                      if results[L]["r_at_best_lag"] is not None)
    max_ring_r = max(abs(results[r]["r_at_best_lag"]) for r in ring_depths
                     if results[r]["r_at_best_lag"] is not None)

    layer_ratio = total_r / max_layer_r if max_layer_r > 0 else float("nan")
    ring_ratio = total_r / max_ring_r if max_ring_r > 0 else float("nan")
    hypothesis_confirmed = (total_r > max_layer_r) and (total_r > max_ring_r)

    print(f"\n{'='*50}")
    print(f"HYPOTHESIS TEST")
    print(f"  Total compaction |r| at best lag  : {total_r:.4f}")
    print(f"  Max individual layer |r|           : {max_layer_r:.4f} "
          f"(ratio total/layer = {layer_ratio:.2f})")
    print(f"  Max individual ring |r|            : {max_ring_r:.4f} "
          f"(ratio total/ring = {ring_ratio:.2f})")
    print(f"  Verdict: GPS correlates with total compaction "
          f"{'MORE STRONGLY' if hypothesis_confirmed else 'SIMILARLY TO'} "
          f"individual components.")
    print(f"  Hypothesis {'CONFIRMED ✓' if hypothesis_confirmed else 'NOT SUPPORTED ✗'}")
    print(f"{'='*50}")

    # ── Assemble output JSON (strip internal arrays) ──────────────────────
    clean_results = {}
    for name, res in results.items():
        clean = {k: v for k, v in res.items() if not k.startswith("_")}
        clean_results[name] = clean

    summary = {
        "metadata": {
            "date": "2026-06-11",
            "description": (
                "Cross-correlation between GPS surface displacement (modeled) and "
                f"MLCW compaction at {STATION} — layers, rings, and total column."
            ),
            "gps_source": str(GPS_PATH.relative_to(PROJECT_ROOT)),
            "gps_column": GPS_COL,
            "layer_source": str(LAYER_PATH.relative_to(PROJECT_ROOT)),
            "ring_source": str(RING_PATH.relative_to(PROJECT_ROOT)),
            "max_lag_epochs": MAX_LAG_EPOCHS,
            "epoch_unit": "5-day",
            "detrend": "linear OLS on cumulative series",
            "n_overlap_epochs": n_overlap,
            "date_range": f"{merged['date'].iloc[0].date()} → {merged['date'].iloc[-1].date()}",
        },
        "total_compaction": clean_results["Total"],
        "per_layer": {L: clean_results[L] for L in LAYERS},
        "per_ring": {r: clean_results[r] for r in ring_depths},
        "hypothesis_test": {
            "total_r_abs": round(total_r, 4),
            "max_layer_r_abs": round(max_layer_r, 4),
            "max_ring_r_abs": round(max_ring_r, 4),
            "total_to_max_layer_ratio": round(layer_ratio, 3),
            "total_to_max_ring_ratio": round(ring_ratio, 3),
            "total_exceeds_all_individuals": hypothesis_confirmed,
            "verdict": (
                "CONFIRMED: GPS correlates with total compaction more strongly "
                "than with any single layer or ring."
                if hypothesis_confirmed else
                "NOT SUPPORTED: GPS correlates similarly with total and individual components."
            ),
        },
    }

    json_path = RESULT_JSON
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\nJSON written: {json_path}")

    print("\nDone.")
    print(f"  Results: {RESULTS_DIR}")
    print(f"  Figures: {FIGURES_DIR}")


if __name__ == "__main__":
    main()
