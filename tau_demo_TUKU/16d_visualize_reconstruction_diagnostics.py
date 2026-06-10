"""
16d_visualize_reconstruction_diagnostics.py — Residual & scatter diagnostics.

Reads the 6 reconstruction CSVs and produces two multi-panel figures:
  1. Residual timeseries (3×2) — reveals drift, seasonal misfit
  2. Observed vs predicted scatter (3×2) — reveals bias, spread

Output: results/visualization/reconstruction_residuals.png
        results/visualization/reconstruction_scatter.png
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
CSV_DIR  = ROOT / "results" / "reconstruction"
OUT_DIR  = ROOT / "results" / "visualization"
OUT_DIR.mkdir(parents=True, exist_ok=True)

LAYERS = ["F1","T1","F2","T2","F3","F4"]
TITLES = {
    "F1": "F1 — Aquifer 1 (0–42 m)",
    "T1": "T1 — Aquitard 1 (42–51 m)",
    "F2": "F2 — Aquifer 2 (51–157 m)",
    "T2": "T2 — Aquitard 2 (157–173 m)",
    "F3": "F3 — Aquifer 3 (173–283 m)",
    "F4": "F4 — Aquifer 4 (283–300 m, silt/mud)",
}
COLORS = plt.cm.tab10.colors


def load_all():
    data = {}
    for layer in LAYERS:
        df = pd.read_csv(CSV_DIR / f"TUKU_{layer}_reconstruction.csv")
        df["date"] = pd.to_datetime(df["date"])
        data[layer] = df
    return data


# ═══════════════════════════════════════════════════════════════════════════════
# Figure 1: Residual timeseries
# ═══════════════════════════════════════════════════════════════════════════════

def plot_residuals(data: dict):
    fig, axes = plt.subplots(3, 2, figsize=(18, 16))
    axes = axes.flatten()

    for i, layer in enumerate(LAYERS):
        ax = axes[i]
        df = data[layer]
        valid = df.dropna(subset=["residual_mm"])
        dates = valid["date"]
        res = valid["residual_mm"].values

        if len(res) < 2:
            ax.text(0.5, 0.5, "No data", transform=ax.transAxes, ha="center")
            continue

        std2 = 2 * np.std(res)
        r2 = np.corrcoef(valid["b_observed_mm"], valid["b_model_mm"])[0,1]**2

        # Positive residual = model under-predicts compaction (obs more negative)
        # Negative residual = model over-predicts compaction
        ax.fill_between(dates, 0, res, where=(res > 0), color="#2ca02c", alpha=0.3, label="Under-predict")
        ax.fill_between(dates, 0, res, where=(res < 0), color="#d62728", alpha=0.3, label="Over-predict")
        ax.plot(dates, res, "-", color="black", lw=0.6, alpha=0.8)
        ax.axhline(0, color="black", lw=1.0)
        ax.axhline(+std2, color="gray", lw=0.8, ls="--", alpha=0.6)
        ax.axhline(-std2, color="gray", lw=0.8, ls="--", alpha=0.6, label=f"±2σ = ±{std2:.1f} mm")

        mean_res = res.mean()
        ax.set_title(f"{layer}: {TITLES[layer].split('—')[0].strip()}  |  "
                     f"mean={mean_res:+.2f} mm  σ={res.std():.2f} mm  R²={r2:.3f}",
                     fontsize=11, fontweight="bold")
        ax.set_ylabel("Residual [mm]", fontsize=10)
        ax.legend(fontsize=7, loc="upper right", ncol=3)
        ax.grid(True, alpha=0.3)
        ax.tick_params(labelsize=9)

    fig.suptitle("TUKU — Carrier Reconstruction Residuals  (obs − pred)\n"
                 "Green = model under-predicts compaction  |  Red = model over-predicts",
                 fontsize=15, fontweight="bold", y=1.01)
    fig.tight_layout()
    path = OUT_DIR / "reconstruction_residuals.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# Figure 2: Observed vs Predicted scatter
# ═══════════════════════════════════════════════════════════════════════════════

def plot_scatter(data: dict):
    fig, axes = plt.subplots(3, 2, figsize=(14, 14))
    axes = axes.flatten()

    for i, layer in enumerate(LAYERS):
        ax = axes[i]
        df = data[layer]
        valid = df.dropna(subset=["b_observed_mm", "b_model_mm"])
        obs = valid["b_observed_mm"].values
        pred = valid["b_model_mm"].values

        if len(obs) < 2:
            ax.text(0.5, 0.5, "No data", transform=ax.transAxes, ha="center")
            continue

        r2 = np.corrcoef(obs, pred)[0,1]**2
        rmse = np.sqrt(np.mean((obs - pred)**2))
        bias = np.mean(pred - obs)

        # Color by time (blue=early, red=late)
        t_norm = np.linspace(0, 1, len(obs))
        ax.scatter(obs, pred, c=t_norm, cmap="coolwarm", s=6, alpha=0.5, edgecolors="none")

        # 1:1 line
        lo, hi = min(obs.min(), pred.min()), max(obs.max(), pred.max())
        margin = (hi - lo) * 0.05
        ax.plot([lo-margin, hi+margin], [lo-margin, hi+margin], "--", color="black", lw=1.0, alpha=0.6)
        ax.set_xlim(lo-margin, hi+margin)
        ax.set_ylim(lo-margin, hi+margin)

        ax.set_title(f"{layer}  |  R²={r2:.3f}  RMSE={rmse:.2f} mm  bias={bias:+.2f} mm",
                     fontsize=11, fontweight="bold")
        ax.set_xlabel("Observed [mm]", fontsize=9)
        ax.set_ylabel("Predicted [mm]", fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.tick_params(labelsize=8)
        ax.set_aspect("equal")

    fig.suptitle("TUKU — Observed vs Predicted Compaction (Carrier Model)\n"
                 "Blue = early epoch  |  Red = late epoch",
                 fontsize=15, fontweight="bold", y=1.01)
    fig.tight_layout()
    path = OUT_DIR / "reconstruction_scatter.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {path}")


# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    data = load_all()
    plot_residuals(data)
    plot_scatter(data)
    print("Done.")
