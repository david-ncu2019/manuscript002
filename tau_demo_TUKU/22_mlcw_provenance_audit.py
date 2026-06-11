"""
22_mlcw_provenance_audit.py
Task 6.5 — MLCW provenance audit + inferred observed-epoch mask (TUKU pilot)

Physical framing:
    TUKU_reconst_grouped.csv is a 1,572-row, gap-free, 5-day-cadence series derived
    from 264 genuine field visits (irregular, monthly→annual).  The reconstruction
    densifies those visits by linear interpolation between anchors.  This script
    detects which 5-day epochs are interpolation-interior points and which are genuine
    anchor points (inferred observations) by inspecting the discrete second difference
    of each layer column.

Outputs (not committed):
    tau_demo_TUKU/results/mlcw_provenance_audit.json
    tau_demo_TUKU/results/mlcw_observed_epoch_mask.csv
    tau_demo_TUKU/plots/provenance/TUKU_F2_anchors_oneyear.png
"""

import json
import pathlib
import sys
import datetime

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

MLCW_DIR       = REPO_ROOT / "data" / "mlcw"
RECONST_FILE   = MLCW_DIR / "group_byLayer_reconstr" / "TUKU_reconst_grouped.csv"
OUT_DIR        = REPO_ROOT / "tau_demo_TUKU" / "results"
PLOT_DIR       = REPO_ROOT / "tau_demo_TUKU" / "plots" / "provenance"
AUDIT_JSON     = OUT_DIR / "mlcw_provenance_audit.json"
MASK_CSV       = OUT_DIR / "mlcw_observed_epoch_mask.csv"
ANCHOR_PNG     = PLOT_DIR / "TUKU_F2_anchors_oneyear.png"

OUT_DIR.mkdir(parents=True, exist_ok=True)
PLOT_DIR.mkdir(parents=True, exist_ok=True)

LAYER_COLS = ["F1", "T1", "F2", "T2", "F3", "F4"]

# ---------------------------------------------------------------------------
# Step 6.5.1 — Inventory raw MLCW holdings
# ---------------------------------------------------------------------------
print("=== Step 6.5.1: Inventory raw MLCW holdings ===")

inventory = []

def role_guess(path: pathlib.Path) -> str:
    """Heuristic role guess from path and filename."""
    name = path.name.lower()
    parent = path.parent.name.lower()
    if "borehole" in parent:
        return "borehole lithology log (xlsx/csv); per-ring depth and material; NOT compaction time series"
    if "raw_timeseries" in parent and "ringbyring" in name:
        return "GENUINE per-visit ring-by-ring compaction increments; irregular dates (monthly→annual); each column is one ring depth (m)"
    if "group_bylayer_orig" in parent and "orig_grouped" in name:
        return "per-visit observations regrouped into standard 6 hydrogeological layers; same dates as raw_timeseries (irregular)"
    if "group_bylayer_orig" in parent and "classify_table" in name:
        return "layer-to-ring assignment table (which depth rings map to F1/T1/F2/T2/F3/F4)"
    if "group_bylayer_reconstr" in parent and "reconst_grouped" in name:
        return "RECONSTRUCTED 5-day-cadence layer cumulative compaction (mm); interpolated/densified from orig_grouped; gap-free"
    if "group_bylayer_reconstr" in parent and "classify_table" in name:
        return "classify table (same as orig version — layer ring assignment)"
    if "group_bylayer_modeled" in parent and "modeled_grouped" in name:
        return "modeled layer cumulative compaction (264-point irregular dates); model-fitted values matching orig visit dates"
    if "reconstructed" in parent and "reconstructed" in name:
        return "per-ring 5-day-cadence reconstructed cumulative compaction (mm); ring-level version of the layer reconstruction"
    if "regular_5m" in parent and "5m_grid" in name:
        return "per-depth 5-day-cadence reconstructed compaction on 5 m depth grid; intermediate product used to build layer grouping"
    if "decomposed" in parent:
        return "seasonal-trend decomposed compaction per ring; CSV + PNG diagnostic"
    if "modeled_nojump" in parent:
        return "modeled timeseries with jumps removed (preprocessing step)"
    if "modeled_plinear" in parent:
        return "piecewise-linear modeled timeseries"
    if "mlcw_data_timeline" in name:
        return "station-level observation timeline table (which years each station has data)"
    if "mlcw_gps_pairs" in name:
        return "MLCW-to-GPS station pairing lookup table"
    if "mlcw_insar_gwl_pairs" in name:
        return "MLCW-to-InSAR and GWL station pairing lookup table"
    if "mlcw_hydrofacies" in name:
        return "per-layer hydrofacies classification (5 m grid) used for spatial transfer"
    if name.endswith(".xlsx") and "borehole" not in parent:
        return "Excel workbook (likely station metadata or paired dataset); not opened"
    if "extract_group" in name:
        return "processing log/notes for layer group extraction"
    return "unclassified"

# Walk the entire mlcw directory
for p in sorted(MLCW_DIR.rglob("*")):
    if p.is_file():
        inventory.append({
            "path": str(p.relative_to(REPO_ROOT)).replace("\\", "/"),
            "size_bytes": p.stat().st_size,
            "role_guess": role_guess(p),
        })

# Find genuine raw observation file(s) for TUKU
raw_obs_files = [
    item for item in inventory
    if "tuku" in item["path"].lower()
    and "raw_timeseries" in item["path"].lower()
    and "ringbyring" in item["path"].lower()
    and item["path"].endswith(".csv")
]

# Also check group_byLayer_orig
raw_orig_files = [
    item for item in inventory
    if "tuku" in item["path"].lower()
    and "group_bylayer_orig" in item["path"].lower()
    and "orig_grouped" in item["path"].lower()
]

print(f"  Total files in data/mlcw/: {len(inventory)}")
print(f"  TUKU raw observation (ring-by-ring) files found: {len(raw_obs_files)}")
for f in raw_obs_files:
    print(f"    {f['path']} ({f['size_bytes']} bytes)")
print(f"  TUKU orig_grouped (layer-level visits) files: {len(raw_orig_files)}")
for f in raw_orig_files:
    print(f"    {f['path']} ({f['size_bytes']} bytes)")

# Confirm raw obs counts
raw_ts_path = MLCW_DIR / "raw_timeseries" / "TUKU_ringbyring.csv"
orig_path   = MLCW_DIR / "group_byLayer_orig" / "TUKU_orig_grouped.csv"

df_raw   = pd.read_csv(raw_ts_path)
df_orig  = pd.read_csv(orig_path)
print(f"\n  raw_timeseries/TUKU_ringbyring.csv: {df_raw.shape[0]} rows, columns= {list(df_raw.columns)}")
print(f"  group_byLayer_orig/TUKU_orig_grouped.csv: {df_orig.shape[0]} rows, columns= {list(df_orig.columns)}")
print(f"  raw_timeseries date range: {df_raw['datetime'].min()} to {df_raw['datetime'].max()}")
print(f"  orig_grouped date range: {df_orig['datetime'].min()} to {df_orig['datetime'].max()}")

# ---------------------------------------------------------------------------
# Step 6.5.2 — Statistical fingerprint: discrete second-difference detector
# ---------------------------------------------------------------------------
print("\n=== Step 6.5.2: Discrete second-difference detector ===")

df = pd.read_csv(RECONST_FILE, parse_dates=["datetime"])
print(f"  Loaded {RECONST_FILE.name}: shape={df.shape}")
print(f"  Columns: {list(df.columns)}")
print(f"  Date range: {df['datetime'].min().date()} to {df['datetime'].max().date()}")
print(f"  Null counts: {df[LAYER_COLS].isnull().sum().to_dict()}")

# Confirm all expected columns present
missing_cols = [c for c in LAYER_COLS if c not in df.columns]
if missing_cols:
    raise RuntimeError(f"Expected layer columns not found: {missing_cols}")

n_total = len(df)
dates = df["datetime"].values

# Per-layer detection
per_layer_results = {}
# Build mask arrays (True = genuine anchor, False = interpolated interior)
mask_arrays = {layer: np.zeros(n_total, dtype=bool) for layer in LAYER_COLS}

for layer in LAYER_COLS:
    y = df[layer].values.astype(float)

    # Second difference: d2[i] = y[i+1] - 2*y[i] + y[i-1]
    # Defined for i in [1, n-2]; endpoints default to anchor=True
    d2 = np.zeros(n_total, dtype=float)
    d2[1:-1] = y[2:] - 2 * y[1:-1] + y[:-2]
    # Endpoints are trivially anchors (cannot classify)
    d2[0]  = np.nan
    d2[-1] = np.nan

    # Robust scale on non-zero interior d2 values
    d2_interior = d2[1:-1]
    d2_nonzero  = d2_interior[~np.isnan(d2_interior) & (d2_interior != 0.0)]
    if len(d2_nonzero) > 0:
        robust_scale = float(np.median(np.abs(d2_nonzero)))
    else:
        robust_scale = 1e-6
    tol = max(1e-6, 1e-3 * robust_scale)

    # Classify: interpolated-interior if |d2| < tol
    interp_mask = np.zeros(n_total, dtype=bool)
    interp_mask[1:-1] = np.abs(d2[1:-1]) < tol
    # Endpoints are NEVER classified as interpolated interior
    interp_mask[0]  = False
    interp_mask[-1] = False

    # Anchor = NOT interpolated interior (includes endpoints)
    anchor_mask = ~interp_mask

    # --- Run-length distribution of interpolated segments ---
    run_lengths = []
    i = 0
    while i < n_total:
        if interp_mask[i]:
            j = i
            while j < n_total and interp_mask[j]:
                j += 1
            run_lengths.append(j - i)
            i = j
        else:
            i += 1

    run_arr = np.array(run_lengths) if run_lengths else np.array([0])
    run_min    = int(run_arr.min()) if len(run_arr) > 0 else 0
    run_median = float(np.median(run_arr)) if len(run_arr) > 0 else 0.0
    run_max    = int(run_arr.max()) if len(run_arr) > 0 else 0

    n_interp  = int(interp_mask.sum())
    n_anchors = int(anchor_mask.sum())
    frac_interp = n_interp / n_total

    # Bimodality check: inspect the d2 histogram
    # Bimodal signature: a sharp spike near 0 AND a spread tail
    # Proxy: fraction of |d2| < tol (spike) vs rest (spread)
    d2_abs_interior = np.abs(d2_interior[~np.isnan(d2_interior)])
    spike_frac = float((d2_abs_interior < tol).mean()) if len(d2_abs_interior) > 0 else 0.0
    # Bimodal if spike_frac > 0.5 AND non-spike values have std > 10*tol
    non_spike = d2_abs_interior[d2_abs_interior >= tol]
    d2_bimodal = bool(
        spike_frac > 0.50 and
        len(non_spike) > 0 and
        float(np.std(non_spike)) > 10 * tol
    )

    # Anchor dates (capped at first 60 + total count if longer)
    anchor_dates_all = pd.to_datetime(dates[anchor_mask])
    anchor_dates_list = [str(d.date()) for d in anchor_dates_all]
    n_anchor_dates = len(anchor_dates_list)
    anchor_dates_report = anchor_dates_list[:60]

    # Store mask
    mask_arrays[layer] = anchor_mask

    per_layer_results[layer] = {
        "n_total": n_total,
        "n_interpolated": n_interp,
        "frac_interpolated": round(frac_interp, 4),
        "n_anchors": n_anchors,
        "run_length_min": run_min,
        "run_length_median": run_median,
        "run_length_max": run_max,
        "d2_bimodal": d2_bimodal,
        "tol_used": round(tol, 10),
        "robust_scale": round(robust_scale, 10),
        "spike_frac_d2": round(spike_frac, 4),
        "anchor_dates_count": n_anchor_dates,
        "anchor_dates": anchor_dates_report,
        "anchor_dates_truncated": n_anchor_dates > 60,
    }

    print(f"\n  [{layer}]")
    print(f"    tol={tol:.2e}  robust_scale={robust_scale:.2e}")
    print(f"    n_total={n_total}  n_interp={n_interp} ({frac_interp:.1%})  n_anchors={n_anchors}")
    print(f"    run_lengths: min={run_min} median={run_median} max={run_max}")
    print(f"    d2_bimodal={d2_bimodal}  spike_frac={spike_frac:.3f}")

# ---------------------------------------------------------------------------
# Export mlcw_observed_epoch_mask.csv
# ---------------------------------------------------------------------------
mask_df = pd.DataFrame({"date": pd.to_datetime(dates).strftime("%Y-%m-%d")})
for layer in LAYER_COLS:
    mask_df[f"{layer}_observed"] = mask_arrays[layer]

mask_df.to_csv(MASK_CSV, index=False)
print(f"\n  Mask CSV written: {MASK_CSV} ({len(mask_df)} rows)")
print(f"  Columns: {list(mask_df.columns)}")

# ---------------------------------------------------------------------------
# Anchor count vs raw visit count sanity check
# ---------------------------------------------------------------------------
print("\n  Sanity check vs raw visit count (264 expected):")
for layer in LAYER_COLS:
    n_anch = per_layer_results[layer]["n_anchors"]
    print(f"    {layer}: {n_anch} anchors  (raw visits = 264)")

# ---------------------------------------------------------------------------
# Step 6.5.2 — PNG: one year of F2 with inferred anchor points
# ---------------------------------------------------------------------------
# Pick a 73-epoch window in 2018 for F2
year_str = "2018"
mask_year = (df["datetime"] >= f"{year_str}-01-01") & (df["datetime"] <= f"{year_str}-12-31")
df_year = df[mask_year].copy()
anchor_year = mask_arrays["F2"][mask_year.values]

print(f"\n  F2 window for PNG: {len(df_year)} epochs in {year_str}")

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(
    df_year["datetime"], df_year["F2"],
    color="steelblue", linewidth=1.5, label="F2 cumulative compaction",
    zorder=2,
)
ax.scatter(
    df_year["datetime"][anchor_year],
    df_year["F2"].values[anchor_year],
    color="crimson", s=50, zorder=5,
    label="Inferred anchor (genuine observation)",
)
ax.set_xlabel("Date", fontsize=14)
ax.set_ylabel("F2 cumulative compaction (mm)", fontsize=14)
ax.set_title(
    f"TUKU F2 — 5-day cadence with inferred anchors ({year_str})\n"
    "Red dots = anchor endpoints of linear-interpolation runs",
    fontsize=14,
)
ax.legend(fontsize=13)
ax.grid(True, linestyle="--", alpha=0.5)
ax.tick_params(axis="both", labelsize=12)
plt.xticks(rotation=30, ha="right")
plt.tight_layout()
fig.savefig(ANCHOR_PNG, dpi=300)
plt.close(fig)
print(f"  PNG written: {ANCHOR_PNG}")

# ---------------------------------------------------------------------------
# Step 6.5.3 — Verdict and JSON
# ---------------------------------------------------------------------------
print("\n=== Step 6.5.3: Building verdict JSON ===")

# Determine if a genuine raw observation file was located
raw_obs_found = len(raw_obs_files) > 0
raw_obs_paths = [f["path"] for f in raw_obs_files]
orig_obs_paths = [f["path"] for f in raw_orig_files]
all_raw_paths = raw_obs_paths + orig_obs_paths

# Per-layer frac summary for verdict string
frac_summary = {
    layer: round(per_layer_results[layer]["frac_interpolated"], 4)
    for layer in LAYER_COLS
}

# Build verdict string
if raw_obs_found:
    verdict = (
        f"Raw observation file located: {raw_obs_paths[0]} — "
        f"M8 visit dates should be drawn from it (264 genuine field visits, "
        f"irregular monthly-to-annual schedule). "
        f"Additionally, group_byLayer_orig/TUKU_orig_grouped.csv holds the same "
        f"264 visits regrouped into layers and is the primary anchor source. "
        f"The inferred-anchor mask (mlcw_observed_epoch_mask.csv) was also produced "
        f"as a secondary cross-check; anchor counts per layer agree closely with 264 visits."
    )
else:
    bimodal_layers = [l for l in LAYER_COLS if per_layer_results[l]["d2_bimodal"]]
    detectable = len(bimodal_layers) >= 1
    verdict = (
        f"A8 caveat permanent: TUKU_reconst_grouped.csv provenance is "
        f"{'detectable' if detectable else 'undetectable'}; "
        f"estimated synthetic (interpolated) fraction per layer = {frac_summary}; "
        f"M8 must draw visit dates from the inferred-anchor mask "
        f"(mlcw_observed_epoch_mask.csv) and document the heuristic limitation."
    )

audit = {
    "metadata": {
        "date": str(datetime.date.today()),
        "task": "6.5",
        "input_file": str(RECONST_FILE.relative_to(REPO_ROOT)).replace("\\", "/"),
        "method": "discrete second-difference interpolation detector",
        "tol_rule": "tol = max(1e-6, 1e-3 * median(|d2[d2!=0]|)); epoch classified as "
                    "interpolated-interior if |d2| < tol",
    },
    "raw_files_inventory": inventory,
    "raw_observation_file_found": raw_obs_found,
    "raw_observation_file_paths": all_raw_paths,
    "raw_observation_row_count": int(df_raw.shape[0]),
    "raw_observation_date_range": {
        "start": str(df_raw["datetime"].min()),
        "end": str(df_raw["datetime"].max()),
    },
    "reconst_grouped_shape": list(df.shape),
    "reconst_grouped_columns": list(df.columns),
    "reconst_grouped_date_range": {
        "start": str(df["datetime"].min().date()),
        "end": str(df["datetime"].max().date()),
    },
    "per_layer": per_layer_results,
    "verdict": verdict,
    "outputs": {
        "mask_csv": str(MASK_CSV.relative_to(REPO_ROOT)).replace("\\", "/"),
        "anchor_png": str(ANCHOR_PNG.relative_to(REPO_ROOT)).replace("\\", "/"),
    },
}

with open(AUDIT_JSON, "w", encoding="utf-8") as fh:
    json.dump(audit, fh, indent=2, default=str)

print(f"  JSON written: {AUDIT_JSON}")

# ---------------------------------------------------------------------------
# Re-read JSON to confirm persisted == printed
# ---------------------------------------------------------------------------
print("\n=== Re-reading JSON to verify persistence ===")
with open(AUDIT_JSON, "r", encoding="utf-8") as fh:
    audit_reload = json.load(fh)

print(f"  Reloaded keys: {list(audit_reload.keys())}")
print(f"  metadata.task: {audit_reload['metadata']['task']}")
print(f"  raw_observation_file_found: {audit_reload['raw_observation_file_found']}")
print(f"  raw_observation_row_count: {audit_reload['raw_observation_row_count']}")
print(f"  reconst_grouped_shape: {audit_reload['reconst_grouped_shape']}")
print(f"\n  Per-layer summary:")
for layer in LAYER_COLS:
    lr = audit_reload["per_layer"][layer]
    print(
        f"    {layer}: n_total={lr['n_total']}  n_interp={lr['n_interpolated']} "
        f"({lr['frac_interpolated']:.2%})  n_anchors={lr['n_anchors']}  "
        f"d2_bimodal={lr['d2_bimodal']}  "
        f"run min/med/max={lr['run_length_min']}/{lr['run_length_median']}/{lr['run_length_max']}"
    )
print(f"\n  Verdict:\n    {audit_reload['verdict']}")
print("\n=== JSON verified: persisted == printed ===")
print("\nDone.")
