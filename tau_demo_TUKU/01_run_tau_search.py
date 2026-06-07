"""
01_run_tau_search.py
====================
Self-contained script that calculates the optimal hydraulic lag τ for every
TUKU layer (F1, T1, F2, T2, F3, F4).

What this script does, step by step:
  1. Reads the GWL-to-MLCW layer assignment table to find which GWL well
     is assigned to each TUKU layer.
  2. For each layer:
     a. Loads the assigned well's piezometric head (daily, 2000–2025).
     b. Loads the TUKU MLCW reconstructed compaction for that layer (5-day).
     c. Aligns both to the MLCW 5-day grid using nearest-date matching.
     d. Takes first differences to get incremental signals (Δhead, Δcompaction).
     e. Determines the critical head h_c = min(head before 2015-01-16).
     f. Classifies every epoch as elastic (head > h_c) or inelastic (head ≤ h_c).
     g. Runs the τ grid search: for τ = 0, 1, …, 73 epochs tries shifting
        the GWL signal forward in time and measures how well it then predicts
        the compaction. The τ with the lowest MSE is τ_opt.

Outputs (saved to results/):
  - tau_results.csv   : one row per layer; tau_opt, days, wellcode, h_c
  - tau_mse_curves.csv: MSE at every τ for every layer (74 rows × 7 cols)
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────────
DEMO_DIR    = Path(__file__).resolve().parent
DATA_DIR    = DEMO_DIR / "data"
RESULTS_DIR = DEMO_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# Import τ-search functions from the project's scripts/10_ihmf/
SCRIPTS_IHMF = DEMO_DIR.parent / "scripts" / "10_ihmf"
sys.path.insert(0, str(SCRIPTS_IHMF))
from ihmf_model_v3 import build_regime_mask, remove_seasonal_cycle, tau_grid_search_per_layer

# ── Configuration ─────────────────────────────────────────────────────────────
STATION  = "TUKU"
TAU_MAX  = 120         # 120 epochs × 5 days = 600 days ≈ 1.6 years
# InSAR reference date — zero displacement, all measurements referenced to this date
REF_DATE = pd.Timestamp("2015-01-16")

# Layer colours used in plots (also referenced by 02_plot_timeseries.py)
LAYER_COLORS = {
    "F1": "#1f77b4",   # blue
    "T1": "#17becf",   # cyan
    "F2": "#ff7f0e",   # orange
    "T2": "#bcbd22",   # gold-green
    "F3": "#2ca02c",   # green
    "F4": "#9467bd",   # purple
}

# ── Load assignment table ──────────────────────────────────────────────────────
assign = pd.read_csv(
    DATA_DIR / "gwl_to_mlcw_layer_assignment_v4.csv",
    dtype={"assigned_wellcode": str},
)
tuku_assign = assign[assign["station"] == STATION].set_index("layer")

# ── Load MLCW (all layers in one file) ────────────────────────────────────────
mlcw_raw = pd.read_csv(DATA_DIR / "TUKU_reconst_grouped_cleaned.csv", parse_dates=["datetime"])
mlcw_raw = mlcw_raw.sort_values("datetime").reset_index(drop=True)

# Filter to InSAR reference date (2015-01-16) onward
mlcw_raw = mlcw_raw[mlcw_raw["datetime"] >= REF_DATE].reset_index(drop=True)

# Zero-reference: subtract the first row (obs_i - obs_ref)
ref_row = mlcw_raw.iloc[0]
layer_cols = [c for c in mlcw_raw.columns if c != "datetime"]
for col in layer_cols:
    mlcw_raw[col] = mlcw_raw[col] - ref_row[col]

mlcw = mlcw_raw
mlcw_dates = mlcw["datetime"].values

# ── Run τ search for each layer ───────────────────────────────────────────────
results   = []          # summary row per layer
mse_dict  = {}          # MSE curve per layer
raw_data  = {}          # store aligned data for plotting script

layers_ordered = ["F1", "T1", "F2", "T2", "F3", "F4"]

for layer in layers_ordered:
    if layer not in tuku_assign.index:
        print(f"  {layer}: not in assignment table — skipping")
        continue

    row      = tuku_assign.loc[layer]
    wellcode = row["assigned_wellcode"]
    feather  = Path(row["feather_file"]).name   # just the filename stem
    gwl_path = DATA_DIR / feather

    # ── Load GWL ──────────────────────────────────────────────────────────
    if not gwl_path.exists():
        print(f"  {layer}: GWL file {gwl_path.name} not found — skipping")
        continue

    gwl_raw = pd.read_feather(gwl_path)
    gwl_raw["datetime"] = pd.to_datetime(gwl_raw["datetime"])
    gwl_raw = gwl_raw[["datetime", wellcode]].dropna(subset=[wellcode])
    gwl_raw = gwl_raw.rename(columns={wellcode: "head_m"})
    gwl_raw = gwl_raw.sort_values("datetime").reset_index(drop=True)

    # ── Compute h_c from raw absolute head (before zero-referencing) ──────
    # The aligned table starts at REF_DATE — no pre-2015 rows survive merge_asof.
    # Use the raw feather record (covers ~2000–2025) to find the true historical
    # minimum head, which sets the preconsolidation stress level.
    head_ref = float(gwl_raw[gwl_raw["datetime"] <= REF_DATE]["head_m"].iloc[-1]) \
        if (gwl_raw["datetime"] <= REF_DATE).any() else float(gwl_raw["head_m"].iloc[0])
    pre_ref_raw = gwl_raw["datetime"] < REF_DATE
    if pre_ref_raw.sum() >= 10:
        h_c = float(gwl_raw.loc[pre_ref_raw, "head_m"].min()) - head_ref
    else:
        h_c = float(gwl_raw["head_m"].min()) - head_ref

    # ── Zero-reference GWL head to REF_DATE ────────────────────────────────
    gwl_raw["head_m"] = gwl_raw["head_m"] - head_ref

    # ── Align GWL to MLCW 5-day grid via nearest-date match ───────────────
    mlcw_df = mlcw[["datetime", layer]].rename(columns={layer: "mlcw_mm"})
    aligned = pd.merge_asof(
        mlcw_df.sort_values("datetime"),
        gwl_raw.sort_values("datetime"),
        on="datetime",
        direction="nearest",
    )
    aligned = aligned.dropna(subset=["head_m", "mlcw_mm"]).reset_index(drop=True)

    head_m  = aligned["head_m"].values.astype(float)
    mlcw_mm = aligned["mlcw_mm"].values.astype(float)
    dates   = aligned["datetime"].values


    # ── Incremental signals (first differences) ───────────────────────────
    inc_dH    = np.diff(head_m)     # m per epoch
    inc_db    = np.diff(mlcw_mm)    # mm per epoch
    inc_dates = dates[:-1]          # dates[t] drives the increment from t to t+1

    # ── Regime masks (elastic / inelastic) ────────────────────────────────
    e_m, i_m = build_regime_mask(head_m[:-1], h_c)

    # ── τ grid search ─────────────────────────────────────────────────────
    tau_opt, mse_curve, monthly_means = tau_grid_search_per_layer(
        inc_dH, inc_db, e_m, i_m,
        tau_max=TAU_MAX,
        dates=inc_dates,
    )

    print(f"  {layer}: τ_opt = {tau_opt:3d} epochs = {tau_opt*5:4d} days  "
          f"(well {wellcode}, h_c = {h_c:.2f} m, "
          f"elastic={e_m.sum()}, inelastic={i_m.sum()})")

    # Store for output
    mse_dict[layer] = mse_curve
    results.append({
        "layer":         layer,
        "wellcode":      wellcode,
        "gwl_file":      feather,
        "h_c_m":         round(h_c, 3),
        "n_elastic":     int(e_m.sum()),
        "n_inelastic":   int(i_m.sum()),
        "tau_opt":       tau_opt,
        "tau_opt_days":  tau_opt * 5,
        "mse_at_tau_opt": round(mse_curve[tau_opt], 6),
    })

    # Store full aligned data so 02_plot_timeseries.py can reuse it
    raw_data[layer] = {
        "dates":         aligned["datetime"].values,
        "head_m":        head_m,
        "mlcw_mm":       mlcw_mm,
        "inc_dH":        inc_dH,
        "inc_db":        inc_db,
        "inc_dates":     inc_dates,
        "e_m":           e_m,
        "i_m":           i_m,
        "h_c":           h_c,
        "tau_opt":       tau_opt,
        "monthly_means": monthly_means,
        "wellcode":      wellcode,
    }

# ── Save tau_results.csv ───────────────────────────────────────────────────────
results_df = pd.DataFrame(results)
results_df.to_csv(RESULTS_DIR / "tau_results.csv", index=False)
print(f"\nSaved: {RESULTS_DIR / 'tau_results.csv'}")
print(results_df[["layer", "tau_opt", "tau_opt_days", "wellcode", "h_c_m"]].to_string(index=False))

# ── Save tau_mse_curves.csv ───────────────────────────────────────────────────
tau_index = list(range(TAU_MAX + 1))
mse_df = pd.DataFrame({"tau_epochs": tau_index})
for layer in layers_ordered:
    if layer in mse_dict:
        mse_df[layer] = mse_dict[layer]
mse_df.to_csv(RESULTS_DIR / "tau_mse_curves.csv", index=False)
print(f"Saved: {RESULTS_DIR / 'tau_mse_curves.csv'}")

# ── Save aligned raw data as numpy npz (used by plotting script) ───────────────
npz_path = RESULTS_DIR / "tuku_aligned_data.npz"
save_dict = {}
for layer, d in raw_data.items():
    for k, v in d.items():
        arr = np.array(v) if not isinstance(v, np.ndarray) else v
        save_dict[f"{layer}__{k}"] = arr
np.savez(npz_path, **save_dict)
print(f"Saved: {npz_path}")
print("\nDone. Run 02_plot_timeseries.py to generate figures.")
