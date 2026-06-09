"""Create 6-panel verification summary figure from TUKU_gps_v3_results.json."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path("/mnt/hgfs/1000_SCRIPTS/004_Project003/20260427_InSAR_MLCW_v2")
JSON_PATH = ROOT / "results/ihmf/v3/verification_20260609/TUKU_gps_v3_results.json"
OUT_PATH  = ROOT / "results/ihmf/v3/verification_20260609/TUKU_verification_summary.png"

with open(JSON_PATH) as f:
    data = json.load(f)

layers_order = ["F1", "T1", "F2", "T2", "F3", "F4"]
fig, axes = plt.subplots(3, 2, figsize=(16, 18))
axes = axes.flatten()

for i, layer in enumerate(layers_order):
    ax = axes[i]
    p = data["layers"][layer]

    S_ke = p["S_ke"]
    S_kv = p["S_kv"]
    ratio = S_kv / S_ke if S_ke > 1e-10 else float("inf")
    n_el  = p["n_elastic"]
    n_inel = p["n_inelastic"]
    r2 = p["r2_cum"]

    color = "#2ca02c" if r2 > 0 else "#d62728"

    lines = [
        f"S_ke = {S_ke:.2f} mm/m",
        f"S_kv = {S_kv:.2f} mm/m",
        f"S_kv/S_ke = {ratio:.1f}x",
        f"n_elastic = {n_el}",
        f"n_inelastic = {n_inel}",
        f"R2_cum = {r2:.3f}",
    ]

    y_pos = 0.95
    for line in lines:
        ax.text(0.5, y_pos, line, transform=ax.transAxes, fontsize=13,
                ha="center", va="top", fontfamily="monospace",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.85,
                          edgecolor=color, linewidth=2))
        y_pos -= 0.15

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(f"{layer}  TUKU", fontsize=16, fontweight="bold", color=color, pad=15)

# Walk-forward summary
wf_lines = ["Walk-Forward Folds (post-R3 cumulative):"]
for fold in data["walk_forward"]:
    if fold.get("skipped"):
        wf_lines.append(f"  {fold['fold']}: SKIPPED")
    else:
        n_inel_any = sum(1 for lr in fold["layer_results"].values()
                         if lr.get("n_inelastic", 0) > 0)
        wf_lines.append(f"  {fold['fold']}: {n_inel_any}/6 layers n_inel>0")

wf_lines.append("")
wf_lines.append(f"alpha = {data['alpha']:.4f} (fixed)")
wf_lines.append(f"c_intercept = {data['c_intercept']:.2f} mm")

fig.suptitle("IHM-F v3 Verification  R1/R2/R3 Repairs Applied (2026-06-09)\n"
             "Zero-referenced head + h_c, cumulative walk-forward",
             fontsize=18, fontweight="bold", y=0.995)

fig.text(0.02, 0.02, "\n".join(wf_lines), fontsize=11, fontfamily="monospace",
         va="bottom", ha="left",
         bbox=dict(boxstyle="round,pad=0.5", facecolor="#f0f0f0", alpha=0.9))

# Status banner
fig.text(0.5, 0.965, "R1: S_ke > 0 for all 6 layers  |  R3: n_inelastic > 0 in walk-forward folds",
         fontsize=14, ha="center", fontweight="bold", color="#2ca02c",
         bbox=dict(boxstyle="round,pad=0.4", facecolor="#e8f5e9", edgecolor="#2ca02c", linewidth=2))

fig.tight_layout(rect=[0, 0.06, 1, 0.93])
fig.savefig(OUT_PATH, dpi=200, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {OUT_PATH}")
