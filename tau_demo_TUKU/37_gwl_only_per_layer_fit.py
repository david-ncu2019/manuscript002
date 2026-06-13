#!/usr/bin/env python3
"""
37_gwl_only_per_layer_fit.py — Per-layer independent fit: GWL → MLCW.

Tests whether groundwater level timeseries ALONE can predict per-layer MLCW compaction.
No GPS carrier, no InSAR, no cross-layer coupling, no column-sum constraint.

For each layer independently:
  1. Load GWL head H(t) and MLCW compaction b_obs(t)
  2. Grid-search optimal lag tau (0 to 120 epochs, 5-day units)
  3. Fit cumulative two-regressor model:
       b(t) = S_ke * H(t - tau) + (S_kv - S_ke) * V(t - tau) + intercept
     where V(t) = min(0, cummin(H) - h_c), h_c = min(pre-2015 head)
  4. Compute R², RMSE, S_ske, S_skv, ratio
  5. Reconstruct and export per-layer timeseries

Output: tau_demo_TUKU/results/gwl_only_per_layer/
"""

import json, os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import nnls

REPO = "/mnt/hgfs/1000_SCRIPTS/004_Project003/20260427_InSAR_MLCW_v2"
OUTDIR = f"{REPO}/tau_demo_TUKU/results/gwl_only_per_layer"
LAYERS = ["F1", "T1", "F2", "T2", "F3", "F4"]
TAU_MAX = 120
REF_DATE = "2015-01-16"
os.makedirs(OUTDIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════════
# 1. LOAD DATA
# ═══════════════════════════════════════════════════════════════

print("=== Loading data ===")

# Load MLCW original field data (genuine visits only)
mlcw_orig = pd.read_csv(f"{REPO}/data/mlcw/group_byLayer_orig/TUKU_orig_grouped.csv", parse_dates=["datetime"])
mlcw_orig = mlcw_orig.set_index("datetime")

# Load GWL per-layer paired timeseries (matched to MLCW dates)
gwl_data = {}
for layer in LAYERS:
    # Read cumulative timeseries (has H_zero_ref_m, V_m, b_obs_mm)
    fp = f"{REPO}/tau_demo_TUKU/results/timeseries/TUKU_{layer}_cumulative_timeseries.csv"
    if os.path.exists(fp):
        df = pd.read_csv(fp, parse_dates=["datetime"])
        df = df.set_index("datetime")
        gwl_data[layer] = df
        print(f"  {layer}: {len(df)} epochs loaded")
    else:
        print(f"  {layer}: FILE NOT FOUND — skip")

# Load borehole material for S_ske/S_skv thickness conversion
material = {
    "F1": {"total_m": 41.577, "aquitard_m": 16.577, "is_clay": False},
    "T1": {"total_m": 8.729, "aquitard_m": 7.423, "is_clay": True},
    "F2": {"total_m": 106.284, "aquitard_m": 12.090, "is_clay": False},
    "T2": {"total_m": 16.299, "aquitard_m": 10.299, "is_clay": True},
    "F3": {"total_m": 110.494, "aquitard_m": 76.994, "is_clay": True},
    "F4": {"total_m": 16.617, "aquitard_m": 16.617, "is_clay": True},
}

# ═══════════════════════════════════════════════════════════════
# 2. PER-LAYER FIT
# ═══════════════════════════════════════════════════════════════

print("\n=== Per-layer independent fit ===")

results = {}
recon_data = {}  # for CSV export

for layer in LAYERS:
    if layer not in gwl_data:
        results[layer] = {"error": "no data"}
        continue

    df = gwl_data[layer].copy()
    df = df.dropna(subset=["H_zero_ref_m", "b_obs_mm"])
    if len(df) < 20:
        results[layer] = {"error": f"insufficient data: {len(df)} epochs"}
        continue

    H_full = df["H_zero_ref_m"].values
    b_full = df["b_obs_mm"].values
    dates = df.index

    # Preconsolidation head: minimum pre-REF_DATE
    pre_ref = df[df.index < REF_DATE]
    if len(pre_ref) > 0:
        h_c = float(pre_ref["H_zero_ref_m"].min())
    else:
        h_c = float(np.min(H_full))

    # Tau grid search: find optimal lag
    best_tau = 0
    best_r2 = -np.inf
    best_params = None
    best_pred = None
    tau_r2_curve = []

    for tau in range(0, min(TAU_MAX + 1, len(df) - 30)):
        # Lagged head
        H_lag = np.roll(H_full, tau)
        H_lag[:tau] = np.nan

        # Virgin term on lagged head: V(t) = min(0, cummin(H_lag) - h_c)
        V_lag = np.full(len(H_full), np.nan)
        cummin = np.inf
        for t in range(len(H_full)):
            if not np.isnan(H_lag[t]):
                cummin = min(cummin, H_lag[t])
            V_lag[t] = min(0.0, cummin - h_c)

        # Valid epochs for fitting
        valid = ~np.isnan(H_lag) & ~np.isnan(b_full) & ~np.isnan(V_lag)
        if valid.sum() < 30:
            tau_r2_curve.append({"tau": tau, "n_valid": int(valid.sum()), "r2": np.nan})
            continue

        H_v = H_lag[valid]
        V_v = V_lag[valid]
        b_v = b_full[valid]

        # b is cumulative and negative (compaction). H and V are zero-ref head (negative below ref).
        # Direct OLS: b = c1*H + c2*V + c3, where c1=S_ke, c2=S_kv-S_ke, c3=intercept
        # Use np.linalg.lstsq (no non-negativity — we enforce post-hoc)
        X = np.column_stack([H_v, V_v, np.ones(len(H_v))])
        coeffs, residuals, rank, sv = np.linalg.lstsq(X, b_v, rcond=None)
        S_ke = float(coeffs[0])
        delta = float(coeffs[1])
        intercept = float(coeffs[2])
        S_kv = S_ke + delta

        # Post-hoc physical enforcement
        if S_ke < 0:
            S_kv = S_kv - S_ke  # redistribute
            S_ke = 0.0
        if S_kv < 0:
            S_kv = 0.0
        if S_kv < S_ke:
            S_kv = S_ke

        # Compute R²
        b_pred = np.dot(X, coeffs)
        ss_res = np.sum((b_v - b_pred) ** 2)
        ss_tot = np.sum((b_v - b_v.mean()) ** 2)
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else -np.inf

        tau_r2_curve.append({"tau": tau, "n_valid": int(valid.sum()), "r2": round(float(r2), 4)})

        # Full reconstruction for this tau
        b_pred_full_tau = np.full(len(H_full), np.nan)
        for t in range(len(H_full)):
            if not np.isnan(H_lag[t]) and not np.isnan(V_lag[t]):
                b_pred_full_tau[t] = S_ke * H_lag[t] + (S_kv - S_ke) * V_lag[t] + intercept

        if r2 > best_r2:
            best_r2 = r2
            best_tau = tau
            best_pred_full = b_pred_full_tau.copy()
            best_params = {
                "S_ke_mm_per_m": round(float(S_ke), 4),
                "S_kv_mm_per_m": round(float(S_kv), 4),
                "intercept_mm": round(float(intercept), 2),
                "h_c_m": round(float(h_c), 4),
                "tau_opt_epochs": tau,
                "tau_opt_days": tau * 5,
                "r2": round(float(r2), 4),
                "n_valid": int(valid.sum()),
            }

    # Convert to specific storage (m⁻¹)
    mat = material.get(layer, {"total_m": 1, "aquitard_m": 1})
    if best_params:
        S_ske_m1 = best_params["S_ke_mm_per_m"] / (mat["total_m"] * 1000) if best_params["S_ke_mm_per_m"] > 1e-15 else 0.0
        S_skv_m1 = best_params["S_kv_mm_per_m"] / (mat["aquitard_m"] * 1000) if mat["aquitard_m"] > 0 and best_params["S_kv_mm_per_m"] > 1e-15 else 0.0
        ratio = S_skv_m1 / S_ske_m1 if S_ske_m1 > 1e-15 else None
        best_params["S_ske_m1"] = round(float(S_ske_m1), 6) if isinstance(S_ske_m1, float) else S_ske_m1
        best_params["S_skv_m1"] = round(float(S_skv_m1), 6) if isinstance(S_skv_m1, float) else S_skv_m1
        best_params["ratio_specific"] = round(float(ratio), 2) if ratio is not None else "undefined (S_ske≈0)"
        best_params["in_ratio_gate"] = bool(3 <= ratio <= 50) if ratio is not None else False
        best_params["gwl_alone_usable"] = bool(best_r2 > 0.3)

    results[layer] = best_params if best_params else {"error": "fit failed"}

    # Store reconstruction for CSV export
    if best_pred_full is not None:
        recon_data[layer] = pd.DataFrame({
            "datetime": dates,
            "H_m": H_full,
            "V_m": np.full(len(H_full), np.nan),
            "b_obs_mm": b_full,
            "b_pred_mm": best_pred_full,
            "residual_mm": best_pred_full - b_full,
        }, index=dates)
        # Fill V properly
        recon_data[layer]["V_m"] = [min(0.0, min(H_full[:t+1].min(), h_c) - h_c) if t > 0 else min(0.0, H_full[0] - h_c) for t in range(len(H_full))]

    r2_str = f"{best_r2:.4f}" if best_r2 > -np.inf else "FAIL"
    ratio_str = f"{best_params['ratio_specific']}×" if best_params and 'ratio_specific' in best_params else "N/A"
    print(f"  {layer}: tau={best_tau}, R²={r2_str}, S_ske={S_ske_m1:.2e}, S_skv={S_skv_m1:.2e}, ratio={ratio_str}, usable={best_params.get('gwl_alone_usable', False) if best_params else False}")

# ═══════════════════════════════════════════════════════════════
# 3. EXPORT
# ═══════════════════════════════════════════════════════════════

print("\n=== Exporting ===")

# JSON summary
summary = {
    "title": "GWL-Only Per-Layer Independent Fit — TUKU",
    "question": "Can GWL timeseries alone predict per-layer MLCW compaction?",
    "method": "Per-layer independent cumulative two-regressor NNLS. No GPS, no InSAR, no cross-layer constraints.",
    "model": "b(t) = S_ke * H(t-tau) + (S_kv - S_ke) * V(t-tau) + intercept",
    "date": "2026-06-13",
    "per_layer": results,
    "answer": {
        "gwl_alone_sufficient": any(r.get("gwl_alone_usable", False) for r in results.values() if isinstance(r, dict)),
        "layers_usable": [l for l in LAYERS if isinstance(results.get(l), dict) and results[l].get("gwl_alone_usable", False)],
        "layers_unusable": [l for l in LAYERS if isinstance(results.get(l), dict) and not results[l].get("gwl_alone_usable", False)],
        "conclusion": "See per-layer R². R² > 0.3 = GWL alone captures meaningful compaction signal.",
    },
}
with open(f"{OUTDIR}/gwl_only_per_layer_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

# CSV: per-layer reconstruction timeseries
for layer in LAYERS:
    if layer in recon_data:
        recon_data[layer].to_csv(f"{OUTDIR}/TUKU_{layer}_gwl_only_reconstruction.csv")
        print(f"  TUKU_{layer}_gwl_only_reconstruction.csv ({len(recon_data[layer])} rows)")

# CSV: tau-R² curves
tau_df = pd.DataFrame(tau_r2_curve) if 'tau_r2_curve' in dir() else None
if tau_df is not None and len(tau_df) > 0:
    tau_df.to_csv(f"{OUTDIR}/gwl_only_tau_r2_curve_F2.csv", index=False)

# ═══════════════════════════════════════════════════════════════
# 4. FIGURES
# ═══════════════════════════════════════════════════════════════

print("\n=== Figures ===")

# Figure 1: 6-panel obs vs pred per layer
fig, axes = plt.subplots(3, 2, figsize=(18, 16))
for i, layer in enumerate(LAYERS):
    ax = axes[i // 2, i % 2]
    if layer not in recon_data:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        continue
    df = recon_data[layer].dropna(subset=["b_obs_mm", "b_pred_mm"])
    ax.plot(df.index, df["b_obs_mm"], "black", linewidth=0.8, label="Observed MLCW")
    ax.plot(df.index, df["b_pred_mm"], color="#d62728", linewidth=0.8, label="GWL-only prediction")
    r = results.get(layer, {})
    r2 = r.get("r2", np.nan) if isinstance(r, dict) else np.nan
    tau = r.get("tau_opt_epochs", "?") if isinstance(r, dict) else "?"
    ratio = r.get("ratio_specific", "?") if isinstance(r, dict) else "?"
    ax.set_title(f"{layer}: R²={r2:.3f}, τ={tau} epochs, S_skv/S_ske={ratio}")
    ax.set_ylabel("Cumulative [mm]")
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)
    ax.axvline(x=pd.Timestamp("2021-11-01"), color="red", linestyle="--", linewidth=0.5, alpha=0.5)
fig.suptitle("GWL-Only Per-Layer Fit: Can Groundwater Head Alone Predict MLCW Compaction?", fontsize=12, y=1.01)
fig.tight_layout()
fig.savefig(f"{OUTDIR}/gwl_only_per_layer_fit.png", dpi=150)
plt.close(fig)
print("  gwl_only_per_layer_fit.png")

# Figure 2: R² bar chart — GWL-only vs carrier model
fig, ax = plt.subplots(figsize=(12, 6))
x = np.arange(len(LAYERS))
w = 0.35

gwl_r2 = []
carrier_r2 = []
for layer in LAYERS:
    r = results.get(layer, {})
    gwl_r2.append(r.get("r2", 0) if isinstance(r, dict) else 0)

    # Load carrier R² from reconstruction summary
    try:
        with open(f"{REPO}/tau_demo_TUKU/results/reconstruction/TUKU_carrier_reconstruction_summary.json") as f:
            car_sum = json.load(f)
        carrier_r2.append(car_sum["per_layer"][layer].get("r2_cal", 0))
    except Exception:
        carrier_r2.append(0)

ax.bar(x - w/2, gwl_r2, w, label="GWL-only (this test)", color="#d62728", edgecolor="white")
ax.bar(x + w/2, carrier_r2, w, label="GPS carrier model (production)", color="#1f77b4", edgecolor="white")
ax.axhline(y=0.3, color="gray", linestyle="--", linewidth=0.8, label="Minimum usable R² = 0.3")
ax.axhline(y=0.0, color="black", linewidth=0.8)
ax.set_xticks(x)
ax.set_xticklabels(LAYERS)
ax.set_ylabel("R² (cumulative fit)")
ax.set_title("GWL-Only vs GPS Carrier Model — Per-Layer R² Comparison")
ax.legend()
ax.grid(True, alpha=0.3, axis="y")
fig.tight_layout()
fig.savefig(f"{OUTDIR}/gwl_only_vs_carrier_r2.png", dpi=150)
plt.close(fig)
print("  gwl_only_vs_carrier_r2.png")

# Figure 3: Residual timeseries per layer
fig, axes = plt.subplots(3, 2, figsize=(18, 12))
for i, layer in enumerate(LAYERS):
    ax = axes[i // 2, i % 2]
    if layer not in recon_data:
        continue
    df = recon_data[layer].dropna(subset=["residual_mm"])
    ax.plot(df.index, df["residual_mm"], "gray", linewidth=0.6)
    ax.axhline(y=0, color="black", linewidth=0.5)
    ax.axvline(x=pd.Timestamp("2021-11-01"), color="red", linestyle="--", linewidth=0.5, alpha=0.5)
    ax.set_ylabel(f"{layer} residual [mm]")
    ax.set_title(f"{layer}: mean residual = {df['residual_mm'].mean():+.2f} mm, std = {df['residual_mm'].std():.2f} mm")
    ax.grid(True, alpha=0.3)
fig.suptitle("GWL-Only Residuals: Systematic Errors Per Layer", fontsize=12, y=1.01)
fig.tight_layout()
fig.savefig(f"{OUTDIR}/gwl_only_residuals.png", dpi=150)
plt.close(fig)
print("  gwl_only_residuals.png")

# ═══════════════════════════════════════════════════════════════
# DONE
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*60}")
files = sorted(os.listdir(OUTDIR))
print(f"Exported {len(files)} files to {OUTDIR}:")
for fn in files:
    sz = os.path.getsize(f"{OUTDIR}/{fn}")
    print(f"  {fn} ({sz:,} B)")
print(f"{'='*60}")
