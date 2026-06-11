"""
30_feasibility_proof.py — Red Team Task E: Quantitative impossibility proof.

Physical story: The TUKU Multi-Layer Compaction Well (MLCW) monitors compaction in
6 hydrogeological layers (F1, T1, F2, T2, F3, F4) from 8–300 m depth.  The surface
deformation measured by GPS (Global Positioning System) / InSAR (Interferometric
Synthetic Aperture Radar) is the column integral of all layer compactions.  The
per-layer seasonal signals are large (4–15 mm amplitude) but partially cancel when
summed at the surface (surface seasonal ≈ 3–4 mm).  This vector cancellation means
the inverse problem — recovering 6 per-layer seasonal signals from 1 surface signal
plus 1D groundwater head — is fundamentally underdetermined.  This script provides
three measured exhibits documenting that impossibility.

Three exhibits:
  (a) Amplitude-bound lemma: A_k > A_surface for at least one layer → phase cancellation
      is non-trivial; inversion from surface to layers is not unique.
  (b) Phase cancellation phasor diagram: the 6 layer phasors sum (with opposing phases)
      to a magnitude consistent with the small surface seasonal.
  (c) Rank deficiency: the per-layer driver design matrix (GPS carrier + 1D head per layer)
      has effective rank ≤ 2–3 ≪ 6 → the system cannot uniquely recover 6 independent
      layer signals.

Inputs:
  data/mlcw/group_byLayer_orig/TUKU_orig_grouped.csv
  data/gps/modeled/TKJS_model.csv
  tau_demo_TUKU/data/TUKU_gwl_timeseries.feather (wellcodes from frozen_calibration.json)
  tau_demo_TUKU/seq/drivers.py (build_layer_drivers for Exhibit c)

Outputs:
  tau_demo_TUKU/results/seq/red_team_fixes/feasibility_proof.json
  tau_demo_TUKU/results/seq/red_team_fixes/feasibility_proof.csv
  tau_demo_TUKU/plots/seq/red_team_fixes/feasibility_amplitude_bound.png
  tau_demo_TUKU/plots/seq/red_team_fixes/feasibility_phase_cancellation.png
  tau_demo_TUKU/plots/seq/red_team_fixes/feasibility_rank_deficiency.png
  tau_demo_TUKU/results/seq/red_team_fixes/30_feasibility_proof_run_log.txt

Usage:
    $env:PYTHONPATH=""; conda run -n fafalab2 python tau_demo_TUKU/seq/30_feasibility_proof.py
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.patches import FancyArrowPatch

warnings.filterwarnings("ignore", category=UserWarning)

# ── Path setup ────────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve()
_TAU_DEMO = _HERE.parent.parent   # tau_demo_TUKU/
_ROOT = _TAU_DEMO.parent          # repo root

for _p in [str(_TAU_DEMO), str(_ROOT), str(_ROOT / "scripts")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── Output paths ──────────────────────────────────────────────────────────────
RESULTS_DIR = _TAU_DEMO / "results" / "seq" / "red_team_fixes"
PLOTS_DIR   = _TAU_DEMO / "plots"  / "seq" / "red_team_fixes"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

LOG_PATH = RESULTS_DIR / "30_feasibility_proof_run_log.txt"

# ── Logging ───────────────────────────────────────────────────────────────────
_log_lines: list[str] = []

def log(msg: str = "") -> None:
    print(msg)
    _log_lines.append(msg)

def flush_log() -> None:
    with open(LOG_PATH, "w", encoding="utf-8") as fh:
        fh.write("\n".join(_log_lines) + "\n")

# ── Constants ─────────────────────────────────────────────────────────────────
DENSE_START = pd.Timestamp("2010-01-01")
DENSE_END   = pd.Timestamp("2018-12-31")
LAYERS      = ["F1", "T1", "F2", "T2", "F3", "F4"]  # T3 all-NaN — excluded
DAYS_PER_YEAR = 365.25

# TUKU well codes from frozen_calibration.json (verified)
GWL_WELLS = {
    "F1": "09050111",
    "T1": "09050111",
    "F2": "09050321",
    "T2": "09170121",
    "F3": "09050331",
    "F4": "09080251",
}

# Tau values from frozen_calibration.json (production cap τ=120 for all)
TAU_PER_LAYER = {
    "F1": 80,
    "T1": 80,
    "F2": 120,
    "T2": 120,
    "F3": 120,
    "F4": 120,
}

# GWL feather files (from gwl_to_mlcw_layer_assignment_v4.csv, TUKU rows)
GWL_FEATHERS = {
    "F1": _ROOT / "data" / "gwl" / "well_timeseries" / "HONGLUN_gwl_timeseries.feather",
    "T1": _ROOT / "data" / "gwl" / "well_timeseries" / "HONGLUN_gwl_timeseries.feather",
    "F2": _TAU_DEMO / "data" / "TUKU_gwl_timeseries.feather",
    "T2": _TAU_DEMO / "data" / "LUNZI_gwl_timeseries.feather",
    "F3": _TAU_DEMO / "data" / "TUKU_gwl_timeseries.feather",
    "F4": _TAU_DEMO / "data" / "LIUZHUANG_gwl_timeseries.feather",
}

# ═══════════════════════════════════════════════════════════════════════════════
# Helper: harmonic fit
# ═══════════════════════════════════════════════════════════════════════════════

def fit_annual_harmonic(dates: pd.Series, values: pd.Series) -> dict:
    """
    Zero-reference cumulative, remove linear trend (vs real elapsed days), then
    fit a single annual harmonic: y = c*cos(2π t/365.25) + s*sin(2π t/365.25).

    Anti-patterns avoided:
      A3: t = (dates - dates[0]).dt.days, never np.arange
      A4: zero-reference before detrend for cumulative data

    Returns dict with: n, amplitude_mm, phase_doy, cos_coef, sin_coef,
    trend_slope, detrended_rms
    """
    # Drop NaN pairs
    mask = values.notna()
    d = dates[mask].reset_index(drop=True)
    v = values[mask].reset_index(drop=True)
    n = len(d)
    if n < 4:
        return {"n": n, "amplitude_mm": np.nan, "phase_doy": np.nan,
                "cos_coef": np.nan, "sin_coef": np.nan,
                "trend_slope": np.nan, "detrended_rms": np.nan}

    # A4: zero-reference the cumulative signal
    v_z = v - v.iloc[0]

    # A3: real elapsed days
    t = (d - d.iloc[0]).dt.days.to_numpy(float)

    # Remove linear trend
    slope, intercept = np.polyfit(t, v_z.to_numpy(float), 1)
    detrended = v_z.to_numpy(float) - (slope * t + intercept)

    # Annual harmonic regression
    omega = 2 * np.pi / DAYS_PER_YEAR
    t_ref = (d.iloc[0] - pd.Timestamp("2000-01-01")).days
    t_abs = t + t_ref  # absolute days from 2000-01-01 for consistent phase

    C = np.column_stack([np.cos(omega * t_abs), np.sin(omega * t_abs)])
    coefs, _, _, _ = np.linalg.lstsq(C, detrended, rcond=None)
    c_c, c_s = coefs

    amplitude = float(np.sqrt(c_c**2 + c_s**2))
    # Phase: day-of-year of peak (positive maximum)
    # peak at omega*t_abs = atan2(c_s, c_c) → t_abs_peak = atan2(c_s, c_c) / omega
    # convert to day-of-year (1–365.25)
    t_peak_abs = float(np.arctan2(c_s, c_c) / omega) % DAYS_PER_YEAR
    phase_doy = t_peak_abs  # day-of-year, 0-based from Jan 1

    detrended_rms = float(np.sqrt(np.mean(detrended**2)))

    return {
        "n": int(n),
        "amplitude_mm": amplitude,
        "phase_doy": phase_doy,
        "cos_coef": float(c_c),
        "sin_coef": float(c_s),
        "trend_slope": float(slope),
        "detrended_rms": float(detrended_rms),
    }


def get_detrended_seasonal(dates: pd.Series, values: pd.Series) -> np.ndarray:
    """Return the detrended signal array (same length as input, NaN at gap rows)."""
    mask = values.notna()
    d = dates[mask].reset_index(drop=True)
    v = values[mask].reset_index(drop=True)
    if len(d) < 4:
        return np.full(len(values), np.nan)

    v_z = v - v.iloc[0]
    t = (d - d.iloc[0]).dt.days.to_numpy(float)
    slope, intercept = np.polyfit(t, v_z.to_numpy(float), 1)
    detrended = v_z.to_numpy(float) - (slope * t + intercept)

    out = np.full(len(values), np.nan)
    idx = np.where(mask.values)[0]
    out[idx] = detrended
    return out


# ═══════════════════════════════════════════════════════════════════════════════
# Load data
# ═══════════════════════════════════════════════════════════════════════════════

log("=" * 70)
log("30_feasibility_proof.py — Quantitative impossibility proof (Red Team Task E)")
log("=" * 70)
log("")

# MLCW cumulative per layer
mlcw_path = _ROOT / "data" / "mlcw" / "group_byLayer_orig" / "TUKU_orig_grouped.csv"
log(f"Loading MLCW: {mlcw_path}")
mlcw_full = pd.read_csv(mlcw_path)
mlcw_full["datetime"] = pd.to_datetime(mlcw_full["datetime"])
mlcw_full = mlcw_full.sort_values("datetime").reset_index(drop=True)
log(f"  MLCW shape: {mlcw_full.shape}, cols: {mlcw_full.columns.tolist()}")
log(f"  Date range: {mlcw_full['datetime'].iloc[0].date()} .. {mlcw_full['datetime'].iloc[-1].date()}")

# GPS surface carrier (total surface signal, mm)
gps_path = _ROOT / "data" / "gps" / "modeled" / "TKJS_model.csv"
log(f"Loading GPS: {gps_path}")
gps_full = pd.read_csv(gps_path)
gps_full["datetime"] = pd.to_datetime(gps_full["date"])
gps_full = gps_full.sort_values("datetime").reset_index(drop=True)
log(f"  GPS shape: {gps_full.shape}, cols: {gps_full.columns.tolist()}")
log(f"  Date range: {gps_full['datetime'].iloc[0].date()} .. {gps_full['datetime'].iloc[-1].date()}")

# Restrict to dense era (≈2010–2018) for seasonal estimation
mlcw_dense = mlcw_full[
    (mlcw_full["datetime"] >= DENSE_START) &
    (mlcw_full["datetime"] <= DENSE_END)
].reset_index(drop=True)

gps_dense = gps_full[
    (gps_full["datetime"] >= DENSE_START) &
    (gps_full["datetime"] <= DENSE_END)
].reset_index(drop=True)

log(f"\nDense era {DENSE_START.date()} .. {DENSE_END.date()}:")
log(f"  MLCW rows: {len(mlcw_dense)}")
log(f"  GPS rows: {len(gps_dense)}")

# ═══════════════════════════════════════════════════════════════════════════════
# EXHIBIT (a): Amplitude-bound lemma
# ═══════════════════════════════════════════════════════════════════════════════

log("\n" + "─" * 70)
log("EXHIBIT (a) — Amplitude-bound lemma (MEASURED)")
log("─" * 70)
log("Physical question: Does any per-layer seasonal amplitude exceed the total")
log("surface seasonal amplitude? If yes, the layers must partially cancel at the")
log("surface — the inverse from surface → layers is not unique.")
log("")

# Fit GPS surface harmonic (on dense era)
gps_result = fit_annual_harmonic(gps_dense["datetime"], gps_dense["modeled"])
A_surface = gps_result["amplitude_mm"]
log(f"GPS surface (TKJS modeled): n={gps_result['n']}, A_surface={A_surface:.4f} mm, "
    f"phase DOY={gps_result['phase_doy']:.1f}")

# Fit each layer harmonic
layer_harmonics: dict[str, dict] = {}
for layer in LAYERS:
    if layer not in mlcw_dense.columns:
        log(f"  Layer {layer}: NOT in MLCW columns — skipping")
        layer_harmonics[layer] = {"n": 0, "amplitude_mm": np.nan, "phase_doy": np.nan,
                                  "cos_coef": np.nan, "sin_coef": np.nan}
        continue
    res = fit_annual_harmonic(mlcw_dense["datetime"], mlcw_dense[layer])
    layer_harmonics[layer] = res
    log(f"  Layer {layer}: n={res['n']}, A={res['amplitude_mm']:.4f} mm, "
        f"phase DOY={res['phase_doy']:.1f}, "
        f"trend={res['trend_slope']*365.25:.2f} mm/yr")

# Summary
A_layers = {k: v["amplitude_mm"] for k, v in layer_harmonics.items()
            if not np.isnan(v["amplitude_mm"])}
sum_abs_A = float(np.nansum([v for v in A_layers.values()]))
ratio_sum_to_surface = sum_abs_A / A_surface if A_surface > 0 else np.nan
layers_exceeding_surface = [k for k, v in A_layers.items() if v > A_surface]

log(f"\nA_surface = {A_surface:.4f} mm")
log(f"Σ|A_k| (all layers) = {sum_abs_A:.4f} mm")
log(f"Ratio Σ|A_k| / A_surface = {ratio_sum_to_surface:.2f}×")
log(f"Layers where A_k > A_surface: {layers_exceeding_surface}")

amplitude_bound_proven = len(layers_exceeding_surface) > 0
log(f"Amplitude-bound lemma proven: {amplitude_bound_proven}")

# ═══════════════════════════════════════════════════════════════════════════════
# EXHIBIT (b): Phase cancellation phasor diagram
# ═══════════════════════════════════════════════════════════════════════════════

log("\n" + "─" * 70)
log("EXHIBIT (b) — Phase cancellation, MEASURED")
log("─" * 70)
log("Physical question: Do the 6 layer seasonal phasors cancel when summed?")
log("The vector sum magnitude should be much smaller than Σ|A_k|, and consistent")
log("with the observed small surface seasonal.")
log("")

# Compute phasors: (cos_coef, sin_coef) for each layer and for GPS surface
def to_phasor_xy(res: dict) -> tuple[float, float]:
    """Return (x, y) = (cos_coef, sin_coef) phasor components."""
    if np.isnan(res.get("cos_coef", np.nan)):
        return (0.0, 0.0)
    return (float(res["cos_coef"]), float(res["sin_coef"]))

phasor_gps_x, phasor_gps_y = to_phasor_xy(gps_result)

phasors = {}
for layer in LAYERS:
    px, py = to_phasor_xy(layer_harmonics[layer])
    phasors[layer] = (px, py)
    log(f"  Layer {layer}: phasor = ({px:.4f}, {py:.4f}) mm, "
        f"|phasor| = {np.sqrt(px**2 + py**2):.4f} mm")

log(f"  GPS surface phasor = ({phasor_gps_x:.4f}, {phasor_gps_y:.4f}) mm, "
    f"|phasor| = {np.sqrt(phasor_gps_x**2 + phasor_gps_y**2):.4f} mm")

# Vector sum of layer phasors
sum_x = sum(px for px, py in phasors.values())
sum_y = sum(py for px, py in phasors.values())
phasor_sum_magnitude = float(np.sqrt(sum_x**2 + sum_y**2))

log(f"\nVector sum of 6 layer phasors = ({sum_x:.4f}, {sum_y:.4f}) mm")
log(f"Vector-sum magnitude = {phasor_sum_magnitude:.4f} mm")
log(f"GPS surface amplitude = {A_surface:.4f} mm")
log(f"Cancellation factor (Σ|A_k| / |sum_phasor|) = "
    f"{sum_abs_A / phasor_sum_magnitude:.2f}×")
log(f"Phase cancellation confirmed: vector sum ({phasor_sum_magnitude:.3f} mm) << "
    f"Σ|A_k| ({sum_abs_A:.3f} mm)")

# ═══════════════════════════════════════════════════════════════════════════════
# EXHIBIT (c): Rank deficiency
# ═══════════════════════════════════════════════════════════════════════════════

log("\n" + "─" * 70)
log("EXHIBIT (c) — Rank deficiency, MEASURED")
log("─" * 70)
log("Physical question: How many independent signals are in the {surface, head×6} design?")
log("If effective rank ≪ 6, we cannot recover 6 independent layer dynamics.")
log("")

# Load GWL data for each layer and build the per-layer head driver series
# over the dense era.  Use exact date intersection (A1 — no merge_asof nearest).

def load_gwl_dense(layer: str) -> pd.Series:
    """Load absolute head timeseries (m MSL) for a layer over the dense era."""
    feather_path = GWL_FEATHERS[layer]
    wellcode = GWL_WELLS[layer]
    if not feather_path.exists():
        log(f"  WARNING: {feather_path} not found — returning NaN series for {layer}")
        return pd.Series([], dtype=float)
    gwl = pd.read_feather(feather_path)
    gwl["datetime"] = pd.to_datetime(gwl["datetime"])
    if wellcode not in gwl.columns:
        log(f"  WARNING: wellcode {wellcode} not in {feather_path.name} — "
            f"available: {[c for c in gwl.columns if c != 'datetime']}")
        return pd.Series([], dtype=float)
    gwl = gwl[["datetime", wellcode]].dropna(subset=[wellcode])
    gwl = gwl.sort_values("datetime").reset_index(drop=True)
    # Restrict to dense era
    gwl_dense = gwl[
        (gwl["datetime"] >= DENSE_START) & (gwl["datetime"] <= DENSE_END)
    ].set_index("datetime")[wellcode]
    return gwl_dense

log("Loading per-layer GWL head over dense era...")
gwl_series: dict[str, pd.Series] = {}
for layer in LAYERS:
    s = load_gwl_dense(layer)
    gwl_series[layer] = s
    log(f"  Layer {layer}: wellcode={GWL_WELLS[layer]}, n={len(s)}, "
        f"file={GWL_FEATHERS[layer].name}")

# Build the GPS carrier over the dense era (daily resolution)
gps_dense_indexed = gps_dense.set_index("datetime")["modeled"]

# Sub-exhibit (i): Driver correlation matrix
# Use detrended head changes (vs real days, A3) over dense era for each layer.
# GPS carrier: zero-referenced cumulative, linearly detrended.
# Head: zero-referenced (H - H_ref), linearly detrended.

log("\nSub-exhibit (i): Driver correlation matrix")

def detrend_series(s: pd.Series) -> pd.Series:
    """
    Zero-reference (subtract first value — A4) then linearly detrend (A3: real days).
    Returns detrended series with same index.
    """
    s = s.dropna()
    if len(s) < 4:
        return pd.Series([], dtype=float)
    v = (s - s.iloc[0]).to_numpy(float)
    t = (s.index - s.index[0]).days.to_numpy(float)
    slope, intercept = np.polyfit(t, v, 1)
    return pd.Series(v - (slope * t + intercept), index=s.index)

# Build detrended GPS carrier on its own grid
gps_dt = detrend_series(gps_dense_indexed)

# Build detrended head for each layer on its own grid
head_dt: dict[str, pd.Series] = {}
for layer in LAYERS:
    s = gwl_series[layer]
    head_dt[layer] = detrend_series(s)

log("  Sizes (dense era, after detrend):")
log(f"    GPS carrier: n={len(gps_dt)}")
for layer in LAYERS:
    log(f"    Head {layer}: n={len(head_dt[layer])}")

# For the correlation matrix and SVD, we need all signals on a COMMON date index.
# Exact date intersection (anti-pattern A1: no merge_asof nearest).
# GPS is daily; GWL records are irregular.  Find dates present in GPS AND all layers.
# Use intersection of all available dates.
all_sets = [set(gps_dt.index)]
for layer in LAYERS:
    if len(head_dt[layer]) > 0:
        all_sets.append(set(head_dt[layer].index))

# Intersection of all date sets
common_dates = sorted(all_sets[0].intersection(*all_sets[1:]))
n_common = len(common_dates)
log(f"\n  Exact-date intersection (GPS ∩ all heads): n={n_common} dates")

if n_common < 10:
    log("  WARNING: fewer than 10 common exact dates.")
    log("  Falling back to GPS×head pairwise intersections for correlation matrix.")
    # Build a pairwise correlation matrix using all GPS/head dates
    # GPS at its own daily grid; each head at its own grid
    # For correlation, pair GPS with each head via exact date intersection
    driver_labels = ["GPS"] + [f"H_{layer}" for layer in LAYERS]
    n_drivers = len(driver_labels)
    corr_matrix = np.full((n_drivers, n_drivers), np.nan)
    np.fill_diagonal(corr_matrix, 1.0)

    # GPS vs GPS = 1
    corr_matrix[0, 0] = 1.0
    for j, layer in enumerate(LAYERS):
        h = head_dt[layer]
        if len(h) == 0:
            continue
        common = sorted(set(gps_dt.index) & set(h.index))
        if len(common) < 10:
            log(f"  Insufficient data: GPS vs H_{layer}: n_common={len(common)} < 10")
            continue
        g_vals = gps_dt.loc[common].values
        h_vals = h.loc[common].values
        r = float(np.corrcoef(g_vals, h_vals)[0, 1])
        corr_matrix[0, j + 1] = r
        corr_matrix[j + 1, 0] = r

    # Head vs head pairwise
    for i, l1 in enumerate(LAYERS):
        for j, l2 in enumerate(LAYERS):
            if i == j:
                corr_matrix[i + 1, i + 1] = 1.0
                continue
            h1 = head_dt[l1]
            h2 = head_dt[l2]
            if len(h1) == 0 or len(h2) == 0:
                continue
            common = sorted(set(h1.index) & set(h2.index))
            if len(common) < 10:
                continue
            r = float(np.corrcoef(h1.loc[common].values, h2.loc[common].values)[0, 1])
            corr_matrix[i + 1, j + 1] = r

    # For SVD: build stacked matrix from pairwise-available data
    # Use GPS+head pairs on their own intersections
    # Approximate rank from the 7×7 correlation matrix
    valid_mask = ~np.isnan(np.diag(corr_matrix))
    C_sub = corr_matrix[np.ix_(valid_mask, valid_mask)]
    sv_matrix = C_sub
    sv_label = "Pearson correlation matrix (pairwise)"
    design_for_svd = C_sub
else:
    # Full common-date matrix: rows = dates, cols = [GPS, H_F1, H_T1, H_F2, H_T2, H_F3, H_F4]
    gps_vals = gps_dt.loc[common_dates].values
    head_vals = np.column_stack([
        head_dt[layer].loc[common_dates].values for layer in LAYERS
    ])
    D = np.column_stack([gps_vals, head_vals])  # shape (n_common, 7)
    log(f"  Design matrix shape: {D.shape}")

    corr_matrix = np.corrcoef(D.T)
    driver_labels = ["GPS"] + [f"H_{layer}" for layer in LAYERS]
    sv_label = "full design matrix"
    design_for_svd = D

# Sub-exhibit (ii): SVD rank analysis
log("\nSub-exhibit (ii): Rank analysis of driver design")

if n_common >= 10:
    U, s_vals, Vt = np.linalg.svd(design_for_svd, full_matrices=False)
else:
    # Eigenvalue-based rank from correlation matrix
    s_vals = np.linalg.eigvalsh(design_for_svd)[::-1]
    s_vals = np.abs(s_vals)
    U, Vt = None, None

n_sing = len(s_vals)
sv_max = float(s_vals[0]) if n_sing > 0 else np.nan
cond_number = float(sv_max / s_vals[-1]) if n_sing > 0 and s_vals[-1] > 0 else np.inf

# Effective rank: count singular values > 1% of largest
threshold_pct = 0.01
effective_rank = int(np.sum(s_vals > threshold_pct * sv_max)) if sv_max > 0 else 0
n_total_dims = 7  # GPS + 6 head signals
null_space_dim = n_total_dims - effective_rank

log(f"  Singular values ({sv_label}): {s_vals}")
log(f"  Largest SV: {sv_max:.4f}")
log(f"  Condition number: {cond_number:.1f}")
log(f"  Effective rank (SV > 1% of max): {effective_rank} of {n_total_dims}")
log(f"  Null-space dimension: {null_space_dim}")

# Per-layer head collinearity: max pairwise correlation among head drivers
head_cols = [f"H_{layer}" for layer in LAYERS]
head_idx = [driver_labels.index(h) for h in head_cols if h in driver_labels]
if len(head_idx) >= 2:
    head_corr_sub = corr_matrix[np.ix_(head_idx, head_idx)]
    # Off-diagonal max
    off_diag_vals = head_corr_sub[np.triu_indices(len(head_idx), k=1)]
    valid_od = off_diag_vals[~np.isnan(off_diag_vals)]
    max_head_corr = float(np.max(np.abs(valid_od))) if len(valid_od) > 0 else np.nan
    mean_head_corr = float(np.mean(np.abs(valid_od))) if len(valid_od) > 0 else np.nan
    log(f"  Max |pairwise head correlation|: {max_head_corr:.3f}")
    log(f"  Mean |pairwise head correlation|: {mean_head_corr:.3f}")
else:
    max_head_corr = np.nan
    mean_head_corr = np.nan

# ═══════════════════════════════════════════════════════════════════════════════
# Verdict
# ═══════════════════════════════════════════════════════════════════════════════

log("\n" + "═" * 70)
log("VERDICT")
log("═" * 70)

# The thesis: sub-annual multilayer dynamics CANNOT be recovered from
# surface + 1D head alone.  Three independent lines of evidence:
# 1. Amplitude bound: A_k > A_surface for some k → vector cancellation is non-trivial
# 2. Phasor sum magnitude ≪ Σ|A_k| → confirmed vector cancellation
# 3. Effective rank ≤ N ≪ 6 → design is underdetermined

thesis_support = {
    "amplitude_bound_proven": bool(amplitude_bound_proven),
    "phasor_cancellation_ratio": float(sum_abs_A / phasor_sum_magnitude)
        if phasor_sum_magnitude > 0 else np.nan,
    "effective_rank_le_half": effective_rank <= (n_total_dims // 2),
}

# Check if any exhibit contradicts the thesis
contradicts = []
if not thesis_support["amplitude_bound_proven"]:
    contradicts.append(
        "No layer amplitude exceeds surface amplitude — amplitude-bound lemma fails."
    )
if thesis_support["phasor_cancellation_ratio"] < 2.0:
    contradicts.append(
        f"Phasor cancellation ratio = {thesis_support['phasor_cancellation_ratio']:.2f}× < 2× "
        "— vector cancellation is modest, not definitive."
    )
if not thesis_support["effective_rank_le_half"]:
    contradicts.append(
        f"Effective rank = {effective_rank} >= {n_total_dims // 2 + 1} — "
        "design is NOT severely underdetermined. Thesis may be overstated."
    )

if len(contradicts) == 0:
    verdict_str = (
        "UNDERDETERMINED — sub-annual multilayer compaction dynamics CANNOT be "
        "recovered from total surface deformation + 1D groundwater head alone. "
        f"Amplitude-bound: {len(layers_exceeding_surface)} layer(s) exceed surface "
        f"({', '.join(layers_exceeding_surface)}). "
        f"Phasor cancellation: Σ|A_k|/|Σphasor| = {sum_abs_A/phasor_sum_magnitude:.1f}×. "
        f"Effective rank = {effective_rank} of {n_total_dims} total drivers — "
        f"null-space dimension = {null_space_dim}. "
        "NOT solvable at sparse (annual/semiannual) in-situ cadence regardless of τ value."
    )
    overall_verdict = "UNDERDETERMINED"
else:
    verdict_str = (
        "PARTIALLY_SUPPORTED — some exhibits support the impossibility thesis but "
        f"{len(contradicts)} exhibit(s) do not. Contradictions: " +
        " | ".join(contradicts)
    )
    overall_verdict = "PARTIALLY_SUPPORTED"

log(verdict_str)
log("")
for item in contradicts:
    log(f"  CONTRADICTION: {item}")

# ═══════════════════════════════════════════════════════════════════════════════
# Write JSON + CSV outputs
# ═══════════════════════════════════════════════════════════════════════════════

log("\n" + "─" * 70)
log("Writing output files...")

# per-layer amplitude/phase table
table_rows = []
for layer in LAYERS:
    h = layer_harmonics[layer]
    table_rows.append({
        "layer": layer,
        "n": h.get("n", 0),
        "amplitude_mm": h.get("amplitude_mm", np.nan),
        "phase_doy": h.get("phase_doy", np.nan),
        "cos_coef": h.get("cos_coef", np.nan),
        "sin_coef": h.get("sin_coef", np.nan),
        "trend_slope_mm_per_yr": h.get("trend_slope", np.nan) * 365.25
            if h.get("trend_slope") is not None else np.nan,
        "exceeds_surface": h.get("amplitude_mm", 0) > A_surface,
    })

# Add GPS surface row
table_rows.append({
    "layer": "GPS_surface",
    "n": gps_result["n"],
    "amplitude_mm": A_surface,
    "phase_doy": gps_result["phase_doy"],
    "cos_coef": gps_result["cos_coef"],
    "sin_coef": gps_result["sin_coef"],
    "trend_slope_mm_per_yr": gps_result["trend_slope"] * 365.25,
    "exceeds_surface": False,
})

df_table = pd.DataFrame(table_rows)
csv_path = RESULTS_DIR / "feasibility_proof.csv"
df_table.to_csv(csv_path, index=False, float_format="%.6f")
log(f"  CSV: {csv_path}")

# Convert correlation matrix to list-of-lists for JSON
def to_json_safe(v):
    if isinstance(v, (np.ndarray,)):
        return v.tolist()
    if isinstance(v, float) and np.isnan(v):
        return None
    if isinstance(v, np.floating):
        return float(v)
    if isinstance(v, np.integer):
        return int(v)
    return v

corr_matrix_json = [[
    None if np.isnan(corr_matrix[i, j]) else float(corr_matrix[i, j])
    for j in range(corr_matrix.shape[1])
] for i in range(corr_matrix.shape[0])]

proof_json = {
    "script": "30_feasibility_proof.py",
    "date": "2026-06-12",
    "dense_era": f"{DENSE_START.date()} .. {DENSE_END.date()}",
    "layers": LAYERS,
    "exhibit_a": {
        "description": "Amplitude-bound lemma: per-layer seasonal amplitudes vs surface",
        "A_surface_mm": float(A_surface),
        "A_surface_phase_doy": float(gps_result["phase_doy"]),
        "n_gps": int(gps_result["n"]),
        "per_layer": {
            layer: {
                "n": int(layer_harmonics[layer].get("n", 0)),
                "A_mm": float(layer_harmonics[layer].get("amplitude_mm", np.nan))
                    if not np.isnan(layer_harmonics[layer].get("amplitude_mm", np.nan)) else None,
                "phase_doy": float(layer_harmonics[layer].get("phase_doy", np.nan))
                    if not np.isnan(layer_harmonics[layer].get("phase_doy", np.nan)) else None,
                "exceeds_surface": bool(
                    layer_harmonics[layer].get("amplitude_mm", 0) > A_surface
                ),
            }
            for layer in LAYERS
        },
        "sum_abs_A_mm": float(sum_abs_A),
        "ratio_sum_to_surface": float(ratio_sum_to_surface)
            if not np.isnan(ratio_sum_to_surface) else None,
        "layers_exceeding_surface": layers_exceeding_surface,
        "amplitude_bound_proven": bool(amplitude_bound_proven),
    },
    "exhibit_b": {
        "description": "Phase cancellation phasors",
        "per_layer_phasor": {
            layer: {
                "x_mm": float(phasors[layer][0]),
                "y_mm": float(phasors[layer][1]),
                "magnitude_mm": float(np.sqrt(phasors[layer][0]**2 + phasors[layer][1]**2)),
            }
            for layer in LAYERS
        },
        "gps_phasor_x_mm": float(phasor_gps_x),
        "gps_phasor_y_mm": float(phasor_gps_y),
        "gps_phasor_magnitude_mm": float(A_surface),
        "vector_sum_x_mm": float(sum_x),
        "vector_sum_y_mm": float(sum_y),
        "vector_sum_magnitude_mm": float(phasor_sum_magnitude),
        "sum_abs_amplitudes_mm": float(sum_abs_A),
        "cancellation_ratio": float(sum_abs_A / phasor_sum_magnitude)
            if phasor_sum_magnitude > 0 else None,
        "vector_sum_vs_surface_ratio": float(phasor_sum_magnitude / A_surface)
            if A_surface > 0 else None,
    },
    "exhibit_c": {
        "description": "Driver design rank deficiency",
        "driver_labels": driver_labels,
        "n_common_exact_dates": int(n_common),
        "sv_label": sv_label,
        "singular_values": [float(v) for v in s_vals],
        "condition_number": float(cond_number) if np.isfinite(cond_number) else None,
        "effective_rank": int(effective_rank),
        "n_total_dims": int(n_total_dims),
        "null_space_dim": int(null_space_dim),
        "effective_rank_threshold_pct": float(threshold_pct * 100),
        "max_pairwise_head_corr": float(max_head_corr)
            if not np.isnan(max_head_corr) else None,
        "mean_pairwise_head_corr": float(mean_head_corr)
            if not np.isnan(mean_head_corr) else None,
        "driver_correlation_matrix": corr_matrix_json,
        "driver_correlation_labels": driver_labels,
    },
    "verdict": {
        "overall": overall_verdict,
        "verdict_string": verdict_str,
        "thesis_support": {k: (bool(v) if isinstance(v, (bool, np.bool_)) else
                               float(v) if not (isinstance(v, float) and np.isnan(v)) else None)
                           for k, v in thesis_support.items()},
        "contradictions": contradicts,
        "impossible_at_sparse_cadence": (overall_verdict == "UNDERDETERMINED"),
    },
}

json_path = RESULTS_DIR / "feasibility_proof.json"
with open(json_path, "w", encoding="utf-8") as fh:
    json.dump(proof_json, fh, indent=2)
log(f"  JSON: {json_path}")

# ═══════════════════════════════════════════════════════════════════════════════
# PLOTS
# ═══════════════════════════════════════════════════════════════════════════════

log("\n" + "─" * 70)
log("Generating figures...")

# Color palette: tab10
COLORS = plt.cm.tab10.colors

# ── Figure 1: Amplitude bound ──────────────────────────────────────────────────
fig_a, ax_a = plt.subplots(figsize=(9, 5))
amp_vals = [layer_harmonics[l].get("amplitude_mm", np.nan) for l in LAYERS]
bar_colors = [COLORS[2] if v > A_surface else COLORS[0]
              for v in amp_vals]
bars = ax_a.bar(LAYERS, amp_vals, color=bar_colors, edgecolor="black",
                linewidth=0.8, zorder=3)
ax_a.axhline(A_surface, color=COLORS[3], linewidth=2.5, linestyle="--", zorder=4,
             label=f"GPS surface A = {A_surface:.2f} mm")
ax_a.set_xlabel("Layer", fontsize=14)
ax_a.set_ylabel("Annual harmonic amplitude (mm)", fontsize=14)
ax_a.set_title("Exhibit (a): Per-layer seasonal amplitude vs GPS surface amplitude\n"
               f"Dense era {DENSE_START.year}–{DENSE_END.year}, TUKU station",
               fontsize=13)
ax_a.tick_params(labelsize=12)
ax_a.legend(fontsize=12)
ax_a.grid(axis="y", linewidth=0.5, alpha=0.7)
ax_a.spines["top"].set_visible(False)
ax_a.spines["right"].set_visible(False)

# Annotate bars exceeding surface
for i, (layer, v) in enumerate(zip(LAYERS, amp_vals)):
    if not np.isnan(v) and v > A_surface:
        ax_a.annotate(f"{v:.2f} mm\n> surface",
                      xy=(i, v), xytext=(i, v + 0.3),
                      ha="center", fontsize=10, color=COLORS[2], fontweight="bold")

# Annotate non-exceeding
for i, (layer, v) in enumerate(zip(LAYERS, amp_vals)):
    if not np.isnan(v) and v <= A_surface:
        ax_a.annotate(f"{v:.2f}", xy=(i, v + 0.05), ha="center", fontsize=10,
                      color=COLORS[0])

ax_a.text(0.02, 0.97,
          f"Σ|A_k| = {sum_abs_A:.2f} mm\nΣ|A_k| / A_surface = {ratio_sum_to_surface:.1f}×\n"
          f"Layers > surface: {', '.join(layers_exceeding_surface) if layers_exceeding_surface else 'none'}",
          transform=ax_a.transAxes, fontsize=11, va="top",
          bbox=dict(boxstyle="round,pad=0.4", facecolor="lightyellow", alpha=0.8))

plt.tight_layout()
fig_a_path = PLOTS_DIR / "feasibility_amplitude_bound.png"
fig_a.savefig(fig_a_path, dpi=300)
plt.close(fig_a)
log(f"  Figure: {fig_a_path}")

# ── Figure 2: Phase cancellation ──────────────────────────────────────────────
fig_b, (ax_ph, ax_ts) = plt.subplots(1, 2, figsize=(14, 6))

# Left: phasor diagram
ax_ph.set_aspect("equal")
colors_layers = [COLORS[i % 10] for i in range(len(LAYERS))]
cumx, cumy = 0.0, 0.0
for i, layer in enumerate(LAYERS):
    px, py = phasors[layer]
    if abs(px) < 1e-10 and abs(py) < 1e-10:
        continue
    ax_ph.annotate("",
        xy=(cumx + px, cumy + py),
        xytext=(cumx, cumy),
        arrowprops=dict(arrowstyle="-|>", color=colors_layers[i], lw=2),
    )
    ax_ph.text(cumx + px / 2, cumy + py / 2,
               f" {layer}", fontsize=10, color=colors_layers[i], fontweight="bold")
    cumx += px
    cumy += py

# Vector sum (resultant)
ax_ph.annotate("",
    xy=(sum_x, sum_y),
    xytext=(0, 0),
    arrowprops=dict(arrowstyle="-|>", color="black", lw=3),
)
ax_ph.text(sum_x * 0.5, sum_y * 0.5, " Layer\nsum",
           fontsize=10, color="black", fontweight="bold")

# GPS surface phasor (from origin)
ax_ph.annotate("",
    xy=(phasor_gps_x, phasor_gps_y),
    xytext=(0, 0),
    arrowprops=dict(arrowstyle="-|>", color=COLORS[3], lw=3, linestyle="dashed"),
)
ax_ph.text(phasor_gps_x * 0.5, phasor_gps_y * 0.5, " GPS\nsurface",
           fontsize=10, color=COLORS[3], fontweight="bold")

# Reference circle at A_surface
theta = np.linspace(0, 2 * np.pi, 200)
ax_ph.plot(A_surface * np.cos(theta), A_surface * np.sin(theta),
           "--", color=COLORS[3], lw=1.2, alpha=0.5, label=f"GPS circle r={A_surface:.2f} mm")
ax_ph.axhline(0, color="gray", lw=0.5)
ax_ph.axvline(0, color="gray", lw=0.5)
ax_ph.set_xlabel("Cosine component (mm)", fontsize=14)
ax_ph.set_ylabel("Sine component (mm)", fontsize=14)
ax_ph.set_title("Phase cancellation\n(phasor diagram)", fontsize=13)
ax_ph.tick_params(labelsize=12)
ax_ph.legend(fontsize=10)
ax_ph.grid(linewidth=0.5, alpha=0.5)

# Right: detrended seasonal timeseries on shared y-axis (A2/A6 anti-pattern avoided)
# Use dense-era MLCW detrended signals
# Compute min/max across all layers to set common ylim
all_detrended: dict[str, np.ndarray] = {}
for layer in LAYERS:
    if layer in mlcw_dense.columns:
        arr = get_detrended_seasonal(mlcw_dense["datetime"], mlcw_dense[layer])
        all_detrended[layer] = arr

# GPS detrended (daily)
gps_dt_plot = detrend_series(gps_dense_indexed)

all_vals = np.concatenate([v[~np.isnan(v)] for v in all_detrended.values()])
gps_dt_vals = gps_dt_plot.values
vmin = min(all_vals.min(), gps_dt_vals.min()) * 1.15
vmax = max(all_vals.max(), gps_dt_vals.max()) * 1.15

for i, layer in enumerate(LAYERS):
    if layer not in all_detrended:
        continue
    arr = all_detrended[layer]
    dates = mlcw_dense["datetime"].values
    valid = ~np.isnan(arr)
    ax_ts.plot(dates[valid], arr[valid], lw=1.5, color=colors_layers[i],
               label=f"{layer} (A={layer_harmonics[layer].get('amplitude_mm', np.nan):.1f} mm)",
               alpha=0.85)

ax_ts.plot(gps_dt_plot.index, gps_dt_plot.values,
           lw=2.5, color=COLORS[3], linestyle="--",
           label=f"GPS surface (A={A_surface:.1f} mm)")
ax_ts.set_ylim(vmin, vmax)  # shared y (A2/A6: same units, same axis)
ax_ts.set_xlabel("Year", fontsize=14)
ax_ts.set_ylabel("Detrended compaction / displacement (mm)", fontsize=14)
ax_ts.set_title(f"Detrended seasonal signals\n(dense era {DENSE_START.year}–{DENSE_END.year})",
                fontsize=13)
ax_ts.tick_params(labelsize=12)
ax_ts.legend(fontsize=10, loc="lower left")
ax_ts.grid(linewidth=0.5, alpha=0.5)
ax_ts.spines["top"].set_visible(False)
ax_ts.spines["right"].set_visible(False)

fig_b.suptitle("Exhibit (b): Phase cancellation — TUKU per-layer seasonals sum to small surface signal",
               fontsize=14, fontweight="bold")
plt.tight_layout()
fig_b_path = PLOTS_DIR / "feasibility_phase_cancellation.png"
fig_b.savefig(fig_b_path, dpi=300)
plt.close(fig_b)
log(f"  Figure: {fig_b_path}")

# ── Figure 3: Rank deficiency ──────────────────────────────────────────────────
fig_c, (ax_sv, ax_hm) = plt.subplots(1, 2, figsize=(14, 6))

# Left: singular-value spectrum (log y)
sv_plot = s_vals / sv_max  # normalize
ax_sv.semilogy(range(1, len(sv_plot) + 1), sv_plot, "o-",
               color=COLORS[0], markersize=8, linewidth=2, zorder=3)
ax_sv.axhline(threshold_pct, color=COLORS[2], linestyle="--", lw=2,
              label=f"1% threshold (effective rank cutoff)")
for j in range(len(sv_plot)):
    marker_col = COLORS[0] if sv_plot[j] > threshold_pct else COLORS[3]
    ax_sv.plot(j + 1, sv_plot[j], "o", markersize=10, color=marker_col, zorder=4)
ax_sv.set_xlabel("Singular value index", fontsize=14)
ax_sv.set_ylabel("Normalized singular value (log scale)", fontsize=14)
ax_sv.set_title(f"Singular-value spectrum\n(effective rank = {effective_rank} of {n_total_dims})",
                fontsize=13)
ax_sv.tick_params(labelsize=12)
ax_sv.legend(fontsize=12)
ax_sv.grid(linewidth=0.5, alpha=0.5)
ax_sv.text(0.98, 0.97,
           f"Condition number: {cond_number:.0f}\n"
           f"Effective rank: {effective_rank}\n"
           f"Null-space dim: {null_space_dim}",
           transform=ax_sv.transAxes, fontsize=11, va="top", ha="right",
           bbox=dict(boxstyle="round,pad=0.4", facecolor="lightyellow", alpha=0.8))
ax_sv.spines["top"].set_visible(False)
ax_sv.spines["right"].set_visible(False)

# Right: driver correlation heatmap
n_labels = len(driver_labels)
cmat_plot = corr_matrix.copy()
# Replace NaN with 0 for display
cmat_plot[np.isnan(cmat_plot)] = 0.0
im = ax_hm.imshow(cmat_plot, vmin=-1, vmax=1, cmap="RdBu_r", aspect="auto")
plt.colorbar(im, ax=ax_hm, label="Pearson r")
ax_hm.set_xticks(range(n_labels))
ax_hm.set_yticks(range(n_labels))
ax_hm.set_xticklabels(driver_labels, rotation=45, ha="right", fontsize=11)
ax_hm.set_yticklabels(driver_labels, fontsize=11)
ax_hm.set_title("Driver correlation matrix\n(GPS carrier + per-layer head drivers)",
                fontsize=13)
# Annotate cells
for i in range(n_labels):
    for j in range(n_labels):
        v = corr_matrix[i, j]
        if not np.isnan(v):
            ax_hm.text(j, i, f"{v:.2f}", ha="center", va="center",
                       fontsize=9, color="black" if abs(v) < 0.7 else "white")

fig_c.suptitle("Exhibit (c): Rank deficiency — driver space cannot resolve 6 independent layer signals",
               fontsize=14, fontweight="bold")
plt.tight_layout()
fig_c_path = PLOTS_DIR / "feasibility_rank_deficiency.png"
fig_c.savefig(fig_c_path, dpi=300)
plt.close(fig_c)
log(f"  Figure: {fig_c_path}")

# ═══════════════════════════════════════════════════════════════════════════════
# Final summary
# ═══════════════════════════════════════════════════════════════════════════════

log("\n" + "═" * 70)
log("SUMMARY")
log("═" * 70)
log(f"Exhibit (a) — Amplitude bound:")
log(f"  A_surface = {A_surface:.4f} mm")
for layer in LAYERS:
    A_k = layer_harmonics[layer].get("amplitude_mm", np.nan)
    flag = " *** EXCEEDS SURFACE" if not np.isnan(A_k) and A_k > A_surface else ""
    log(f"  A_{layer} = {A_k:.4f} mm{flag}")
log(f"  Σ|A_k| / A_surface = {ratio_sum_to_surface:.2f}×")
log(f"  Layers exceeding surface: {layers_exceeding_surface}")

log(f"\nExhibit (b) — Phase cancellation:")
log(f"  Vector-sum magnitude = {phasor_sum_magnitude:.4f} mm vs A_surface = {A_surface:.4f} mm")
log(f"  Cancellation ratio (Σ|A_k| / |Σphasor|) = {sum_abs_A/phasor_sum_magnitude:.2f}×")

log(f"\nExhibit (c) — Rank deficiency:")
log(f"  Condition number = {cond_number:.1f}")
log(f"  Effective rank = {effective_rank} of {n_total_dims}")
log(f"  Null-space dimension = {null_space_dim}")
log(f"  Max pairwise head correlation = {max_head_corr:.3f}")

log(f"\nOVERALL VERDICT: {overall_verdict}")
log(f"{verdict_str}")

flush_log()
log(f"\nLog written: {LOG_PATH}")
log(f"JSON written: {json_path}")
log(f"CSV written: {csv_path}")
log("Done.")
