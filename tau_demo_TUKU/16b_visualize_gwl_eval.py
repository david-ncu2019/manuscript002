"""Export CSV + bar chart from carrier_gwl_eval.json (GWL residual term eval)."""
import json
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
IN_JSON = ROOT / "tau_demo_TUKU" / "results" / "carrier_gwl_eval.json"
OUT_DIR = ROOT / "results" / "visualization"
OUT_DIR.mkdir(parents=True, exist_ok=True)

with open(IN_JSON) as f:
    data = json.load(f)

layers = ["F1","T1","F2","T2","F3","F4"]
adopt = data["adopt_gwl"]

# ── CSV ──
rows = []
for layer in layers:
    c = data["collinearity"][layer]
    rmid = data["per_layer"][layer].get("middle", {})
    rend = data["per_layer"][layer].get("end", {})
    deltas = [rmid.get("delta_pct", 0), rend.get("delta_pct", 0)]
    rows.append({
        "layer": layer,
        "VIF": c["vif"],
        "corr_GPS_vs_GWL": c["corr"],
        "delta_pct_middle": rmid.get("delta_pct"),
        "delta_pct_end": rend.get("delta_pct"),
        "delta_pct_avg": round(np.mean(deltas), 2),
        "adopt_GWL": adopt.get(layer, False),
    })
df = pd.DataFrame(rows)
csv_path = OUT_DIR / "carrier_gwl_eval_table.csv"
df.to_csv(csv_path, index=False, float_format="%.4f")
print(f"CSV: {csv_path}")

# ── PNG ──
fig, ax = plt.subplots(figsize=(12, 6))
x = np.arange(len(layers))
w = 0.35
mid_vals = [data["per_layer"][l].get("middle",{}).get("delta_pct",0) for l in layers]
end_vals = [data["per_layer"][l].get("end",{}).get("delta_pct",0) for l in layers]
mid_colors = ["#2ca02c" if adopt.get(l) else "#d62728" for l in layers]
end_colors = ["#1b9e1b" if adopt.get(l) else "#e57373" for l in layers]

b1 = ax.bar(x - w/2, mid_vals, w, color=mid_colors, alpha=0.85,
            label="Middle gap", edgecolor="white")
b2 = ax.bar(x + w/2, end_vals, w, color=end_colors, alpha=0.85,
            label="End gap", edgecolor="white")
for bar, v in zip(b1, mid_vals):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5 if v>=0 else bar.get_height()-2,
            f"{v:+.1f}%", ha="center", fontsize=9, fontweight="bold")
for bar, v in zip(b2, end_vals):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5 if v>=0 else bar.get_height()-2,
            f"{v:+.1f}%", ha="center", fontsize=9)

ax.axhline(-5, color="black", lw=1.5, ls="--", alpha=0.7, label="−5% adoption threshold")
ax.axhline(0, color="gray", lw=0.8, alpha=0.5)
ax.set_xticks(x)
ax.set_xticklabels(layers, fontsize=13)
ax.set_ylabel("Δ Held-out RMSE [%]  (negative = GWL helps)", fontsize=12)
ax.set_title("GWL Residual Term Evaluation — Carrier vs Carrier+GWL\n"
             f"Adopted: {', '.join(data['layers_adopting_gwl']) if data['layers_adopting_gwl'] else 'none'}",
             fontsize=14, fontweight="bold")
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3, axis="y")

# Adoption annotation
for i, layer in enumerate(layers):
    if adopt.get(layer):
        ax.annotate("ADOPTED ✓", (i, -8), ha="center", fontsize=10,
                    color="#2ca02c", fontweight="bold")

fig.tight_layout()
png_path = OUT_DIR / "carrier_gwl_delta_pct.png"
fig.savefig(png_path, dpi=200, bbox_inches="tight")
plt.close(fig)
print(f"PNG: {png_path}")

print(f"\nAdopted GWL: {data['layers_adopting_gwl']}")
