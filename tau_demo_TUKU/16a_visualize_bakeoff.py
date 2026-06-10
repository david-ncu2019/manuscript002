"""Export CSV + bar chart from holdout_bakeoff.json (Decision Point 1)."""
import json, sys
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
IN_JSON  = ROOT / "tau_demo_TUKU" / "results" / "holdout_bakeoff.json"
OUT_DIR  = ROOT / "results" / "visualization"
OUT_DIR.mkdir(parents=True, exist_ok=True)

with open(IN_JSON) as f:
    data = json.load(f)

layers = ["F1","T1","F2","T2","F3","F4"]
methods = ["carrier","bilinear","baseline"]
designs = ["middle_gap","end_gap"]
design_labels = ["Middle gap (40–70%)", "End gap (last 30%)"]
colors = {"carrier": "#2ca02c", "bilinear": "#d62728", "baseline": "#1f77b4"}

# ── CSV ──
rows = []
for layer in layers:
    for dk, dl in zip(designs, design_labels):
        r = data["per_layer"][layer].get(dk, {})
        rows.append({
            "layer": layer, "design": dl,
            "rmse_carrier_mm": r.get("rmse_carrier_mm"),
            "rmse_bilinear_mm": r.get("rmse_bilinear_mm"),
            "rmse_baseline_mm": r.get("rmse_baseline_mm"),
            "skill_carrier": r.get("skill_carrier"),
            "skill_bilinear": r.get("skill_bilinear"),
            "winner": min(["carrier","bilinear","baseline"],
                          key=lambda m: r.get(f"rmse_{m}_mm", float("inf"))),
        })
df = pd.DataFrame(rows)
csv_path = OUT_DIR / "holdout_bakeoff_table.csv"
df.to_csv(csv_path, index=False, float_format="%.4f")
print(f"CSV: {csv_path}")

# ── PNG ──
fig, axes = plt.subplots(1, 2, figsize=(18, 7), sharey=True)
for di, (dk, dl) in enumerate(zip(designs, design_labels)):
    ax = axes[di]
    x = np.arange(len(layers))
    w = 0.25
    for mi, method in enumerate(methods):
        vals = [data["per_layer"][l].get(dk, {}).get(f"rmse_{method}_mm", 0) for l in layers]
        bars = ax.bar(x + mi*w, vals, w, color=colors[method], alpha=0.85,
                      label=method.capitalize(), edgecolor="white", linewidth=0.5)
        for bar, v in zip(bars, vals):
            if v and v < 100:
                ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5,
                        f"{v:.1f}", ha="center", va="bottom", fontsize=7, rotation=90)

    ax.set_title(dl, fontsize=14, fontweight="bold")
    ax.set_xticks(x + w)
    ax.set_xticklabels(layers, fontsize=12)
    ax.set_ylabel("Held-out RMSE [mm]", fontsize=12)
    ax.grid(True, alpha=0.3, axis="y")

axes[0].legend(fontsize=11, loc="upper left")
fig.suptitle("Decision Point 1 — Three-Method Held-Out Bake-Off (TUKU)\n"
             "GPS carrier wins all 6 layers by held-out RMSE",
             fontsize=15, fontweight="bold", y=1.01)
fig.tight_layout()
png_path = OUT_DIR / "holdout_bakeoff_rmse.png"
fig.savefig(png_path, dpi=200, bbox_inches="tight")
plt.close(fig)
print(f"PNG: {png_path}")

# ── Summary to stdout ──
print("\nPrimary method:", data["primary_method"])
print("Win counts:", data["win_counts"])
print("Verdict:", data["metadata"]["verdict"])
