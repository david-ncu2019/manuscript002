"""Export CSV + bar chart from TUKU_storage_params.json (bilinear characterization)."""
import json
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
IN_JSON = ROOT / "tau_demo_TUKU" / "results" / "characterization" / "TUKU_storage_params.json"
OUT_DIR = ROOT / "tau_demo_TUKU" / "results" / "visualization"
OUT_DIR.mkdir(parents=True, exist_ok=True)

with open(IN_JSON) as f:
    data = json.load(f)

layers = ["F1","T1","F2","T2","F3","F4"]
lit = data["literature_priors"]["middle"]  # all TUKU layers are middle fan zone

# ── CSV ──
rows = []
for layer in layers:
    p = data["per_layer"][layer]
    rows.append({
        "layer": layer,
        "S_ke_mm_per_m": p["S_ke_mm_per_m"],
        "S_kv_mm_per_m": p["S_kv_mm_per_m"],
        "S_ske_m1": p["S_ske_m1"],
        "S_skv_m1": p["S_skv_m1"],
        "ratio_bulk": p["ratio_bulk"],
        "ratio_specific": p["ratio_specific"],
        "S_ke_identifiable": p["S_ke_identifiable"],
        "thickness_artifact": p["thickness_artifact"],
        "r2_cum": p["r2_cum"],
        "rmse_mm": p["rmse_mm"],
        "n_elastic": p["n_elastic"],
        "n_inelastic": p["n_inelastic"],
        "total_span_m": p["total_span_m"],
        "clay_thickness_m": p["clay_thickness_m"],
        "flags": ",".join(p["flags"]) if p["flags"] else "",
    })
df = pd.DataFrame(rows)
csv_path = OUT_DIR / "storage_params_table.csv"
df.to_csv(csv_path, index=False, float_format="%.6f")
print(f"CSV: {csv_path}")

# ── PNG: 2-panel S_ske and S_skv vs literature ──
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

x = np.arange(len(layers))
w = 0.35
lit_ske = lit["S_ske_m1"]
lit_skv = lit["S_skv_m1"]

# Panel 1: S_ske
ske_vals = [data["per_layer"][l]["S_ske_m1"] for l in layers]
ske_colors = ["#1f77b4" if data["per_layer"][l]["S_ke_identifiable"] else "#d62728" for l in layers]
bars1 = ax1.bar(x, ske_vals, w, color=ske_colors, alpha=0.85, edgecolor="white")
ax1.axhline(lit_ske, color="black", lw=2, ls="--", alpha=0.7,
            label=f"Lit. middle fan: {lit_ske:.2e} m⁻¹")
for bar, v, layer in zip(bars1, ske_vals, layers):
    label = f"{v:.2e}" if v > 0 else "0 (unidentifiable)"
    ax1.text(bar.get_x()+bar.get_width()/2, bar.get_height()*1.05 if v>0 else 0.1e-5,
             label, ha="center", fontsize=8, rotation=90, fontweight="bold")
ax1.set_xticks(x)
ax1.set_xticklabels(layers, fontsize=12)
ax1.set_ylabel("$S_{ske}$ [m⁻¹]", fontsize=12)
ax1.set_title("Elastic Specific Storage", fontsize=13, fontweight="bold")
ax1.legend(fontsize=9)
ax1.grid(True, alpha=0.3, axis="y")
ax1.set_yscale("log")

# Panel 2: S_skv
skv_vals = [data["per_layer"][l]["S_skv_m1"] for l in layers]
skv_colors = ["#2ca02c" if not data["per_layer"][l]["thickness_artifact"] else "#ff7f0e" for l in layers]
bars2 = ax2.bar(x, skv_vals, w, color=skv_colors, alpha=0.85, edgecolor="white")
if lit_skv:
    ax2.axhline(lit_skv, color="black", lw=2, ls="--", alpha=0.7,
                label=f"Lit. middle fan: {lit_skv:.2e} m⁻¹")
for bar, v, layer in zip(bars2, skv_vals, layers):
    ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()*1.05,
             f"{v:.2e}", ha="center", fontsize=8, rotation=90, fontweight="bold")
ax2.set_xticks(x)
ax2.set_xticklabels(layers, fontsize=12)
ax2.set_ylabel("$S_{skv}$ [m⁻¹]", fontsize=12)
ax2.set_title("Inelastic Specific Storage", fontsize=13, fontweight="bold")
ax2.legend(fontsize=9)
ax2.grid(True, alpha=0.3, axis="y")
ax2.set_yscale("log")

# Flag annotations
for i, layer in enumerate(layers):
    flags = data["per_layer"][layer]["flags"]
    if flags:
        ax1.annotate("\n".join(flags), (i, 0), xytext=(i, -0.08),
                     textcoords=("data", "axes fraction"), ha="center", fontsize=6,
                     color="#d62728", fontweight="bold")

fig.suptitle("TUKU — Bilinear Parameter Characterization (Phase 1.4)\n"
             "$S_{ske}$, $S_{skv}$ vs Hung et al. (2021) Middle Fan Zone Priors",
             fontsize=15, fontweight="bold", y=1.02)
fig.tight_layout()
png_path = OUT_DIR / "storage_params_barchart.png"
fig.savefig(png_path, dpi=200, bbox_inches="tight")
plt.close(fig)
print(f"PNG: {png_path}")

# Summary
identifiable = sum(1 for l in layers if data["per_layer"][l]["S_ke_identifiable"])
artifact = sum(1 for l in layers if data["per_layer"][l]["thickness_artifact"])
print(f"\nS_ke identifiable: {identifiable}/{len(layers)}")
print(f"Thickness artifact: {artifact}/{len(layers)}")
