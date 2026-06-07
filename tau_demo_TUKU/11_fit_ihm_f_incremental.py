"""
11_fit_ihm_f_incremental.py
===========================
IHM-F v3 fit for TUKU using 5-day incremental feather data.

Step 1: per-layer bounded lsq_linear on (dH_driver, db_response) pairs to get
        S_ke [mm/m] and S_kv [mm/m], with bounds derived from published
        Choushui River skeletal specific storage ranges and TUKU layer span_m.

        Solver: scipy.optimize.lsq_linear (replaces unconstrained no-intercept OLS).
        A-matrix: rows [dH_e, 0] for elastic epochs, [0, dH_i] for inelastic epochs.
        Bounds: [S_ske_min*b_j*1000, S_ske_max*b_j*1000] for S_ke,
                [S_skv_min*b_j*1000, S_skv_max*b_j*1000] for S_kv.
        b_j = span_m from layer_thickness.csv (MLCW ring coverage span, not
              geological thickness; compressible-fraction data unavailable, so
              span_m is used for both S_ke and S_kv bounds).
        If span_m < 1.0 m (degenerate, e.g. T1=0.0), bounds fall back to
        global Choushui range with nominal b=1.0 m; S_ske is not reported.

Step 2: regress sum of predicted per-layer compaction against GPS incremental
        surface deformation to get alpha (scaling factor).

Data sources (all 5-day cadence, 2003-12-06 to 2025-10-01):
  - GWL diffs  : tau_demo_TUKU/data/incremental_data/{site}_gwl_diff_timeseries.feather
  - MLCW diffs : tau_demo_TUKU/data/incremental_data/mlcw_diff_cleaned.feather
  - GPS target : tau_demo_TUKU/data/incremental_data/TUKU_GPS_diff_timeseries.feather
                 column "modeled", mm/epoch, negative = subsidence

Absolute head for regime mask:
  - tau_demo_TUKU/data/{site}_gwl_timeseries.feather  (daily, covers pre-2015)
  - h_c from pre-REF_DATE minimum (same as 01_run_tau_search.py lines 115-121)

Tau values (5-day epoch units) from tau_results.csv:
  F1=42, T1=72, F2=0, T2=72, F3=0, F4=105

Physical constraint: S_kv / S_ke must be in [8, 100] to be reportable.

Choushui published bounds (from docs/choushui_skeletal_storage_coeffs.md):
  S_ske: min=2.86e-6 m^-1, max=3.87e-4 m^-1  (global range across all layers)
  S_skv: min=1.53e-5 m^-1, max=3.00e-3 m^-1

Note on magnitude gap: lsq_linear forces S into the physical box but does not
close the cumulative compaction gap (cum_pred << cum_obs). That gap is
structural — per-epoch dH covariance is near zero in elastic-dominant regimes;
the secular multi-year head decline drives most of the observed cum_obs but is
not captured by per-epoch S*dH. Both cum_obs and cum_pred are reported.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import pearsonr
from scipy.optimize import lsq_linear

# ── Paths ─────────────────────────────────────────────────────────────────────
DEMO_DIR     = Path(__file__).resolve().parent
DATA_DIR     = DEMO_DIR / "data"
INC_DIR      = DATA_DIR / "incremental_data"
RESULTS_DIR  = DEMO_DIR / "results"
PLOTS_DIR    = DEMO_DIR / "plots" / "results" / "incremental_fit"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

SCRIPTS_IHMF = DEMO_DIR.parent / "scripts" / "10_ihmf"
sys.path.insert(0, str(SCRIPTS_IHMF))
from ihmf_model_v3 import build_regime_mask

# ── Constants ─────────────────────────────────────────────────────────────────
REF_DATE       = pd.Timestamp("2015-01-16")
LAYERS_ORDERED = ["F1", "T1", "F2", "T2", "F3", "F4"]

# tau in 5-day epoch units from tau_results.csv
TAU_FROM_CSV = {"F1": 42, "T1": 72, "F2": 0, "T2": 72, "F3": 0, "F4": 105}

# ── Published Choushui skeletal specific storage bounds ───────────────────────
# Source: docs/choushui_skeletal_storage_coeffs.md, Tables 3-2 and 3-4.
# Global range across all 5 layers — used as the bounding envelope.
S_SKE_MIN = 2.86e-6   # m^-1, elastic, global minimum (Fengan Layer 2.1)
S_SKE_MAX = 3.87e-4   # m^-1, elastic, global maximum (Neiliao Layer 1)
S_SKV_MIN = 1.53e-5   # m^-1, inelastic, global minimum (Layer 3 min)
S_SKV_MAX = 3.00e-3   # m^-1, inelastic, global maximum (Layer 4 max)

# ── Load TUKU layer span_m from layer_thickness.csv ──────────────────────────
# span_m = depth range covered by MLCW rings for that layer at TUKU.
# NOTE: span_m is not the geological layer thickness. The published S_ske bounds
# were estimated from geological thicknesses, so bounds applied to span_m are
# a basis mismatch; this is documented here and in output.
# NOTE: No compressible (fine-grained) fraction data exists in this repo.
# span_m is used for both S_ke (total) and S_kv (compressible) bounds.
_LT_PATH = DEMO_DIR.parent / "figures" / "prestage_data_analysis" / "layer_thickness.csv"
_lt_df   = pd.read_csv(_LT_PATH)
_tuku    = _lt_df[_lt_df["station"] == "TUKU"].set_index("layer")
TUKU_SPAN_M = {ly: float(_tuku.loc[ly, "span_m"]) if ly in _tuku.index else 0.0
               for ly in LAYERS_ORDERED}
# Degenerate rule: if span_m < 1.0 m, use nominal 1.0 m for bound scaling
# but mark the layer so S_ske is not reported (b_j_available = False).
B_NOMINAL_DEGENERATE = 1.0   # m

def _layer_bounds(layer: str) -> tuple[float, float, float, float, float, bool]:
    """
    Return (b_j_m, S_ke_lb, S_ke_ub, S_kv_lb, S_kv_ub, b_j_available).
    b_j_available=False when span_m < 1 m (degenerate); S_ske not reportable.
    Units: S_ke / S_kv in mm/m (bulk).
    """
    span = TUKU_SPAN_M.get(layer, 0.0)
    if span >= 1.0:
        b = span
        avail = True
    else:
        b = B_NOMINAL_DEGENERATE
        avail = False
    lb_ke = S_SKE_MIN * b * 1000.0
    ub_ke = S_SKE_MAX * b * 1000.0
    lb_kv = S_SKV_MIN * b * 1000.0
    ub_kv = S_SKV_MAX * b * 1000.0
    return b, lb_ke, ub_ke, lb_kv, ub_kv, avail

print("TUKU layer span_m (from layer_thickness.csv):")
for ly in LAYERS_ORDERED:
    b, lke, uke, lkv, ukv, avail = _layer_bounds(ly)
    tag = "" if avail else " [DEGENERATE — b_j unavailable, S_ske not reported]"
    print(f"  {ly}: span={TUKU_SPAN_M.get(ly, 0.0):.2f} m  "
          f"S_ke=[{lke:.4f}, {uke:.4f}] mm/m  "
          f"S_kv=[{lkv:.4f}, {ukv:.4f}] mm/m{tag}")

# Layer -> (wellcode, absolute_gwl_feather, diff_gwl_feather, diff_gwl_col)
LAYER_MAP = {
    "F1": ("09050111", "HONGLUN_gwl_timeseries.feather",   "HONGLUN_gwl_diff_timeseries.feather",   "09050111"),
    "T1": ("09050111", "HONGLUN_gwl_timeseries.feather",   "HONGLUN_gwl_diff_timeseries.feather",   "09050111"),
    "F2": ("09050321", "TUKU_gwl_timeseries.feather",      "TUKU_gwl_diff_timeseries.feather",      "09050321"),
    "T2": ("09170121", "LUNZI_gwl_timeseries.feather",     "LUNZI_gwl_diff_timeseries.feather",     "09170121"),
    "F3": ("09050331", "TUKU_gwl_timeseries.feather",      "TUKU_gwl_diff_timeseries.feather",      "09050331"),
    "F4": ("09080251", "LIUZHUANG_gwl_timeseries.feather", "LIUZHUANG_gwl_diff_timeseries.feather", "09080251"),
}

COLORS = {ly: plt.cm.tab10(i) for i, ly in enumerate(LAYERS_ORDERED)}


# ── Load GPS diff timeseries (Step 2 target) ──────────────────────────────────
gps_df = pd.read_feather(INC_DIR / "TUKU_GPS_diff_timeseries.feather")
gps_df["datetime"] = pd.to_datetime(gps_df["datetime"])
gps_df = gps_df.sort_values("datetime").reset_index(drop=True)
# Confirm sign: negative = subsidence (same as MLCW convention)
print(f"GPS diff range: [{gps_df['modeled'].min():.4f}, {gps_df['modeled'].max():.4f}] mm/epoch")
print(f"GPS window: {gps_df['datetime'].min().date()} to {gps_df['datetime'].max().date()}  ({len(gps_df)} epochs)")

# ── Load MLCW diff (all layers) ───────────────────────────────────────────────
mlcw_diff = pd.read_feather(INC_DIR / "mlcw_diff_cleaned.feather")
mlcw_diff["datetime"] = pd.to_datetime(mlcw_diff["datetime"])
mlcw_diff = mlcw_diff.sort_values("datetime").reset_index(drop=True)
print(f"\nMLCW diff: {mlcw_diff.shape}, {mlcw_diff['datetime'].min().date()} to {mlcw_diff['datetime'].max().date()}")
print(f"  columns: {mlcw_diff.columns.tolist()}")

# ── Load GPS reference dates — define the common alignment grid ───────────────
# All incremental feathers are on the same 5-day grid as MLCW (2003-12-06 to 2025-10-01).
# GPS is on the same 5-day grid, 2010-01-06 to 2024-12-26.
# We align to GPS datetimes exactly (inner join by datetime).

print("\n" + "="*60)
print("STEP 1: Per-layer bounded lsq_linear to get S_ke [mm/m], S_kv [mm/m]")
print("="*60)

all_metrics    = []
all_timeseries = []

layer_results  = {}   # store per-layer arrays for Step 2

for layer in LAYERS_ORDERED:
    wellcode, abs_feather, diff_feather, diff_col = LAYER_MAP[layer]
    tau = TAU_FROM_CSV[layer]

    # ── 1a. Load absolute head → compute h_c ──────────────────────────────
    abs_path = DATA_DIR / abs_feather
    gwl_abs  = pd.read_feather(abs_path)
    gwl_abs["datetime"] = pd.to_datetime(gwl_abs["datetime"])
    gwl_abs  = gwl_abs[["datetime", wellcode]].dropna(subset=[wellcode])
    gwl_abs  = gwl_abs.rename(columns={wellcode: "head_m"}).sort_values("datetime").reset_index(drop=True)

    # h_c: minimum head before REF_DATE (same logic as 01_run_tau_search.py)
    head_ref_val = float(
        gwl_abs.loc[gwl_abs["datetime"] <= REF_DATE, "head_m"].iloc[-1]
        if (gwl_abs["datetime"] <= REF_DATE).any()
        else gwl_abs["head_m"].iloc[0]
    )
    pre_ref_mask = gwl_abs["datetime"] < REF_DATE
    if pre_ref_mask.sum() >= 10:
        h_c = float(gwl_abs.loc[pre_ref_mask, "head_m"].min()) - head_ref_val
    else:
        h_c = float(gwl_abs["head_m"].min()) - head_ref_val

    # Zero-reference the absolute head to REF_DATE
    gwl_abs["head_m"] = gwl_abs["head_m"] - head_ref_val

    print(f"\n  {layer}: wellcode={wellcode}, h_c={h_c:.4f} m, "
          f"pre-ref epochs: {pre_ref_mask.sum()}")

    # ── 1b. Load GWL diff (incremental) ───────────────────────────────────
    diff_path = INC_DIR / diff_feather
    gwl_diff  = pd.read_feather(diff_path)
    gwl_diff["datetime"] = pd.to_datetime(gwl_diff["datetime"])
    gwl_diff  = gwl_diff[["datetime", diff_col]].dropna(subset=[diff_col])
    gwl_diff  = gwl_diff.rename(columns={diff_col: "dH"}).sort_values("datetime").reset_index(drop=True)
    # Units: m/epoch (GWL diff feathers carry head in metres, same as absolute)

    # ── 1c. Load MLCW diff for this layer ─────────────────────────────────
    if layer not in mlcw_diff.columns:
        print(f"  {layer}: column not in mlcw_diff_cleaned.feather — skipping")
        continue
    db_df = mlcw_diff[["datetime", layer]].dropna(subset=[layer]).copy()
    db_df = db_df.rename(columns={layer: "db"})

    # ── 1d. Align absolute head to the GWL diff grid by nearest date ──────
    # GWL diff grid is 5-day; absolute is daily. We want head_m at each diff epoch.
    # The regime mask needs head level AT the driver epoch (not t+1).
    # The diff feather epoch t represents the change from (t) to (t+1) in the
    # original 01_run_tau_search convention: inc_dates = dates[:-1].
    # So for diff epoch at datetime d, we want head_m at d (driver head).
    aligned_head = pd.merge_asof(
        gwl_diff[["datetime"]].sort_values("datetime"),
        gwl_abs.sort_values("datetime"),
        on="datetime",
        direction="nearest",
        tolerance=pd.Timedelta("3d"),
    )
    # Merge GWL diff and aligned head on datetime
    layer_df = gwl_diff.merge(aligned_head, on="datetime", how="inner")
    layer_df  = db_df.merge(layer_df, on="datetime", how="inner")
    layer_df  = layer_df.dropna(subset=["dH", "db", "head_m"]).reset_index(drop=True)

    if len(layer_df) < 20:
        print(f"  {layer}: only {len(layer_df)} aligned epochs — skipping")
        continue

    inc_dH    = layer_df["dH"].values.astype(float)      # m/epoch
    inc_db    = layer_df["db"].values.astype(float)       # mm/epoch
    head_abs  = layer_df["head_m"].values.astype(float)   # absolute, zero-ref to REF_DATE
    dates_all = pd.to_datetime(layer_df["datetime"].values)

    T = len(inc_dH)
    n = T - tau

    if n < 4:
        print(f"  {layer}: n={n} < 4 after lag τ={tau} — skipping")
        continue

    # ── 1e. Regime mask (level-based, at driver epoch) ────────────────────
    # head_abs[t] is the absolute head at epoch t (the driver epoch)
    # For the lagged pair: driver at epoch t, response at epoch t+tau.
    # Regime mask for the OLS fit uses head at driver epoch (t).
    # For driver index 0..(n-1), driver head = head_abs[0:n].
    e_m_full, i_m_full = build_regime_mask(head_abs, h_c)  # length T
    e_trim = e_m_full[:n]   # driver-time regime for epochs 0..n-1
    i_trim = i_m_full[:n]

    # ── 1f. Causal pairing ─────────────────────────────────────────────────
    dH_driver   = inc_dH[:n]    # head change at driver epoch, m/epoch
    db_response = inc_db[tau:]  # compaction at response epoch, mm/epoch
    dates_resp  = dates_all[tau:]

    n_elastic   = int(e_trim.sum())
    n_inelastic = int(i_trim.sum())

    # ── 1g. Bounded lsq_linear: S_ke and S_kv ────────────────────────────
    # Replaces unconstrained no-intercept OLS.
    # A-matrix: rows [dH_e, 0] for elastic epochs, [0, dH_i] for inelastic.
    # Bounds: S_ke in [lb_ke, ub_ke], S_kv in [lb_kv, ub_kv] (mm/m, bulk).
    # Note: lsq_linear with orthogonal A-blocks is mathematically equivalent
    # to two independent bounded scalar regressions, but the unified call
    # handles edge cases (n_elastic or n_inelastic < 4) cleanly.
    b_j, lb_ke, ub_ke, lb_kv, ub_kv, b_j_avail = _layer_bounds(layer)

    A_rows, b_rows = [], []
    if n_elastic >= 4:
        dH_e = dH_driver[e_trim]
        db_e = db_response[e_trim]
        A_e  = np.column_stack([dH_e, np.zeros(n_elastic)])
        A_rows.append(A_e)
        b_rows.append(db_e)
    if n_inelastic >= 4:
        dH_i = dH_driver[i_trim]
        db_i = db_response[i_trim]
        A_i  = np.column_stack([np.zeros(n_inelastic), dH_i])
        A_rows.append(A_i)
        b_rows.append(db_i)

    S_ke = lb_ke   # initialise to lower bound (used when no data rows)
    S_kv = lb_kv
    if A_rows:
        A_fit = np.vstack(A_rows)
        b_fit = np.concatenate(b_rows)
        res = lsq_linear(
            A_fit, b_fit,
            bounds=([lb_ke, lb_kv], [ub_ke, ub_kv]),
            method="bvls",
            lsq_solver="exact",
            max_iter=5000,
        )
        S_ke = float(res.x[0])
        S_kv = float(res.x[1])

    # Back-calculate specific storage (m^-1) using span_m; not reportable if b_j degenerate
    S_ske_inv = S_ke / (b_j * 1000.0) if b_j_avail else float("nan")
    S_skv_inv = S_kv / (b_j * 1000.0) if b_j_avail else float("nan")

    # ── 1i. Physical check ────────────────────────────────────────────────
    ratio_str = "undefined"
    ratio_ok  = True
    if S_ke > 1e-10 and S_kv > 1e-10:
        ratio     = S_kv / S_ke
        ratio_str = f"{ratio:.2f}x"
        ratio_ok  = (8.0 <= ratio <= 100.0)
    elif S_ke < 1e-10:
        ratio_str = "S_ke≈0"
    elif S_kv < 1e-10:
        ratio_str = "S_kv≈0"

    # ── 1j. Predicted compaction ──────────────────────────────────────────
    db_pred = np.zeros(n)
    if n_elastic >= 4:
        db_pred[e_trim] = S_ke * dH_driver[e_trim]
    if n_inelastic >= 4:
        db_pred[i_trim] = S_kv * dH_driver[i_trim]

    # ── 1k. Metrics ───────────────────────────────────────────────────────
    residuals = db_response - db_pred
    mse       = float(np.mean(residuals**2))
    rmse      = float(np.sqrt(mse))
    mae       = float(np.mean(np.abs(residuals)))
    bias      = float(np.mean(db_pred - db_response))
    ss_res    = float(np.sum(residuals**2))
    ss_tot    = float(np.sum((db_response - db_response.mean())**2))
    r2        = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else np.nan
    r_pear    = float(pearsonr(db_response, db_pred)[0]) \
                if (np.std(db_pred) > 0 and np.std(db_response) > 0) else np.nan

    cum_obs  = np.cumsum(db_response)
    cum_pred = np.cumsum(db_pred)

    ratio_flag = "" if ratio_ok else "  *** RATIO OUT OF PHYSICAL RANGE ***"
    ske_str = f"{S_ske_inv:.3e}" if b_j_avail else "unavailable (b_j=0)"
    skv_str = f"{S_skv_inv:.3e}" if b_j_avail else "unavailable (b_j=0)"
    print(
        f"  {layer}: τ={tau:3d} ({tau*5:4d}d)  b_j={b_j:.2f} m  "
        f"S_ke={S_ke:.5f} mm/m  S_kv={S_kv:.5f} mm/m  ratio={ratio_str}{ratio_flag}\n"
        f"        S_ske={ske_str} m^-1  S_skv={skv_str} m^-1\n"
        f"        n_el={n_elastic}  n_in={n_inelastic}  n_tot={n}\n"
        f"        RMSE={rmse:.5f} mm/ep  R²={r2:.4f}  r={r_pear:.4f}  bias={bias:+.5f}\n"
        f"        cum_obs: [{cum_obs.min():.2f}, {cum_obs.max():.2f}] mm"
        f"  cum_pred: [{cum_pred.min():.2f}, {cum_pred.max():.2f}] mm\n"
    )

    all_metrics.append(dict(
        layer=layer, wellcode=wellcode, tau_opt=tau, tau_opt_days=tau*5,
        h_c=round(h_c, 4),
        b_j_m=round(b_j, 3),
        b_j_available=b_j_avail,
        S_ke_mm_m=round(S_ke, 7), S_kv_mm_m=round(S_kv, 7),
        S_ske_m=round(S_ske_inv, 9) if b_j_avail else None,
        S_skv_m=round(S_skv_inv, 9) if b_j_avail else None,
        S_ke_lb_mm_m=round(lb_ke, 6), S_ke_ub_mm_m=round(ub_ke, 6),
        S_kv_lb_mm_m=round(lb_kv, 6), S_kv_ub_mm_m=round(ub_kv, 6),
        ratio_skv_ske=round(S_kv / S_ke, 3) if (S_ke > 1e-10 and S_kv > 1e-10) else None,
        ratio_physical_8_100=ratio_ok,
        n_elastic=n_elastic, n_inelastic=n_inelastic, n_epochs=n,
        RMSE=round(rmse, 7), MAE=round(mae, 7), R2=round(r2, 6),
        pearson_r=round(r_pear, 6) if not np.isnan(r_pear) else None,
        bias=round(bias, 7),
        cum_obs_range_mm=round(float(cum_obs.min()), 2),
        cum_pred_range_mm=round(float(cum_pred.min()), 2),
    ))

    all_timeseries.append(pd.DataFrame(dict(
        date=dates_resp,
        layer=layer,
        db_obs_mm=db_response.round(6),
        db_pred_mm=db_pred.round(6),
        cum_obs_mm=cum_obs.round(4),
        cum_pred_mm=cum_pred.round(4),
    )))

    # Store for Step 2: predicted compaction on the full paired window,
    # keyed by response date so we can align to GPS.
    layer_results[layer] = pd.DataFrame({
        "datetime": dates_resp,
        f"db_pred_{layer}": db_pred.round(6),
    }).set_index("datetime")

    # ── 1n. Cumulative net dH diagnostic ─────────────────────────────────
    # Shows whether the physical S bounds can even reach observed compaction.
    sum_dH_e = float(dH_driver[e_trim].sum()) if n_elastic >= 4 else 0.0
    sum_dH_i = float(dH_driver[i_trim].sum()) if n_inelastic >= 4 else 0.0
    max_pred_ke = ub_ke * sum_dH_e
    max_pred_kv = ub_kv * sum_dH_i
    print(
        f"        [Magnitude check] Σ dH_e={sum_dH_e:+.2f} m  "
        f"S_ke_max*Σ dH_e = {max_pred_ke:+.2f} mm\n"
        f"                         Σ dH_i={sum_dH_i:+.2f} m  "
        f"S_kv_max*Σ dH_i = {max_pred_kv:+.2f} mm  "
        f"cum_obs = {float(cum_obs[-1]):.2f} mm"
    )


# ── Save Step 1 metrics ───────────────────────────────────────────────────────
metrics_df = pd.DataFrame(all_metrics)
metrics_df.to_csv(RESULTS_DIR / "incremental_fit_metrics.csv", index=False)
print(f"\nSaved: {RESULTS_DIR / 'incremental_fit_metrics.csv'}")

if all_timeseries:
    ts_all = pd.concat(all_timeseries, ignore_index=True)
    ts_all.to_csv(RESULTS_DIR / "incremental_fit_timeseries.csv", index=False)
    print(f"Saved: {RESULTS_DIR / 'incremental_fit_timeseries.csv'}  ({len(ts_all)} rows)")

print("\n" + "="*60)
print("STEP 2: Regress Σ(db_pred) against GPS incremental surface deformation")
print("="*60)

# ── Build summed compaction on GPS timeline ────────────────────────────────────
# GPS diff is on the 5-day grid; align each layer's db_pred to GPS datetimes.
# Use merge_asof (tolerance 3 days) to handle any minor date rounding.
gps_aligned = gps_df[["datetime", "modeled"]].copy().set_index("datetime")

sum_df = gps_aligned.copy()
for layer, res_df in layer_results.items():
    merged = pd.merge_asof(
        sum_df.reset_index()[["datetime"]].sort_values("datetime"),
        res_df.reset_index().sort_values("datetime"),
        on="datetime",
        direction="nearest",
        tolerance=pd.Timedelta("3d"),
    ).set_index("datetime")
    sum_df = sum_df.join(merged, how="left")

sum_df = sum_df.dropna()
if sum_df.empty:
    print("ERROR: No common epochs between GPS and per-layer predictions — cannot run Step 2.")
    sys.exit(1)

pred_cols = [c for c in sum_df.columns if c.startswith("db_pred_")]
sum_db    = sum_df[pred_cols].sum(axis=1).values    # Σ db_pred, mm/epoch
gps_vals  = sum_df["modeled"].values                # GPS increment, mm/epoch

n_gps = len(gps_vals)
print(f"Common GPS-prediction epochs: {n_gps}")
print(f"  GPS range: [{gps_vals.min():.4f}, {gps_vals.max():.4f}] mm/epoch")
print(f"  Σdb_pred range: [{sum_db.min():.4f}, {sum_db.max():.4f}] mm/epoch")

# Quick diagnostic: does Σ(observed MLCW) ≈ GPS?
# Build sum of observed MLCW increments on GPS timeline too.
obs_cols = [c for c in ts_all.columns if c == "db_obs_mm"] if "all_timeseries" in dir() and all_timeseries else []
if all_timeseries:
    ts_wide = ts_all.pivot_table(index="date", columns="layer", values="db_obs_mm")
    obs_sum_df = pd.merge_asof(
        sum_df.reset_index()[["datetime"]].sort_values("datetime"),
        ts_wide.reset_index().rename(columns={"date": "datetime"}).sort_values("datetime"),
        on="datetime",
        direction="nearest",
        tolerance=pd.Timedelta("3d"),
    ).set_index("datetime")
    obs_sum_df = obs_sum_df.dropna()
    obs_layer_cols = [c for c in obs_sum_df.columns if c in LAYERS_ORDERED]
    if obs_layer_cols:
        sum_obs = obs_sum_df[obs_layer_cols].sum(axis=1).values
        if len(sum_obs) > 4 and np.std(sum_obs) > 0 and np.std(gps_vals[:len(sum_obs)]) > 0:
            r_obs = pearsonr(gps_vals[:len(sum_obs)], sum_obs)[0]
            print(f"\n  Σ(observed MLCW) vs GPS: r={r_obs:.3f} "
                  f"  Σobs range: [{sum_obs.min():.4f}, {sum_obs.max():.4f}] mm/ep")
        else:
            print(f"\n  Σ(observed MLCW): {len(sum_obs)} epochs (insufficient for correlation)")

# ── OLS for alpha: GPS = alpha * Σdb_pred ─────────────────────────────────────
# Constrained to alpha in (0, 1]: compaction cannot exceed surface subsidence.
# Simple no-intercept OLS: alpha = (GPS · Σdb_pred) / (Σdb_pred · Σdb_pred)
denom_step2 = float(np.dot(sum_db, sum_db))
if denom_step2 < 1e-20:
    print("ERROR: Σdb_pred is essentially zero — Step 2 underdetermined.")
    alpha = 0.0
    r2_gps = np.nan
    r_gps  = np.nan
else:
    alpha_raw = float(np.dot(gps_vals, sum_db) / denom_step2)
    alpha     = max(0.0, min(1.0, alpha_raw))
    if abs(alpha_raw - alpha) > 0.001:
        print(f"  NOTE: alpha_raw={alpha_raw:.4f} clipped to alpha={alpha:.4f}")

    gps_pred   = alpha * sum_db
    res_gps    = gps_vals - gps_pred
    ss_res_gps = float(np.sum(res_gps**2))
    ss_tot_gps = float(np.sum((gps_vals - gps_vals.mean())**2))
    r2_gps     = float(1.0 - ss_res_gps / ss_tot_gps) if ss_tot_gps > 0 else np.nan
    rmse_gps   = float(np.sqrt(np.mean(res_gps**2)))
    r_gps      = float(pearsonr(gps_vals, gps_pred)[0]) \
                 if (np.std(gps_pred) > 0 and np.std(gps_vals) > 0) else np.nan

    print(f"\n  alpha = {alpha:.4f}  (raw: {alpha_raw:.4f})")
    print(f"  R²_GPS = {r2_gps:.4f}   RMSE_GPS = {rmse_gps:.5f} mm/ep")
    print(f"  Pearson r = {r_gps:.4f}  n = {n_gps}")

    # Cumulative comparison
    cum_gps_obs  = np.cumsum(gps_vals)
    cum_gps_pred = np.cumsum(gps_pred)
    print(f"  cum GPS obs  range: [{cum_gps_obs.min():.2f}, {cum_gps_obs.max():.2f}] mm")
    print(f"  cum GPS pred range: [{cum_gps_pred.min():.2f}, {cum_gps_pred.max():.2f}] mm")

# ── Save Step 2 results JSON ───────────────────────────────────────────────────
output = {
    "station": "TUKU",
    "step2_target": "GPS_modeled_incremental_mm_epoch",
    "n_gps_epochs": n_gps,
    "alpha": round(alpha, 6),
    "r2_gps": round(r2_gps, 6) if not np.isnan(r2_gps) else None,
    "rmse_gps_mm": round(rmse_gps, 6) if "rmse_gps" in dir() else None,
    "pearson_r_gps": round(r_gps, 6) if (not np.isnan(r_gps) if "r_gps" in dir() else True) else None,
    "layers": {m["layer"]: {k: v for k, v in m.items() if k != "layer"} for m in all_metrics},
    "tau_source": "tau_results.csv (5-day epoch units)",
}

out_json = RESULTS_DIR / "incremental_fit_results.json"
with open(out_json, "w") as f:
    json.dump(output, f, indent=2, default=str)
print(f"\nSaved: {out_json}")


# ── Plots: per-layer incremental + cumulative ─────────────────────────────────
T_START = pd.Timestamp("2015-01-01")
T_END   = pd.Timestamp("2026-01-01")

if all_timeseries:
    ts_all["date"] = pd.to_datetime(ts_all["date"])
    for layer in LAYERS_ORDERED:
        sub = metrics_df[metrics_df["layer"] == layer]
        if sub.empty:
            continue
        row = sub.iloc[0]
        ts  = ts_all[ts_all["layer"] == layer].copy()
        ts  = ts[(ts["date"] >= T_START) & (ts["date"] < T_END)]
        if ts.empty:
            continue

        color    = COLORS[layer]
        tau_days = int(row["tau_opt_days"])

        fig, (ax_inc, ax_cum) = plt.subplots(2, 1, figsize=(11, 7.5), sharex=True)
        fig.suptitle(
            f"TUKU  |  Layer {layer}  |  IHM-F v3 incremental fit (lsq_linear, 5-day feathers)\n"
            f"τ = {tau_days} days  |  S_ke = {row['S_ke_mm_m']:.5f} mm/m  "
            f"S_kv = {row['S_kv_mm_m']:.5f} mm/m"
            f"  ratio = {row['ratio_skv_ske']}  |  R² = {row['R2']:.3f}  RMSE = {row['RMSE']:.5f} mm/ep",
            fontsize=12, fontweight="bold", y=0.98,
        )
        ax_inc.plot(ts["date"], ts["db_obs_mm"], color="grey", linewidth=1.0, alpha=0.7, label="Observed MLCW increment")
        ax_inc.plot(ts["date"], ts["db_pred_mm"], color=color, linewidth=1.0, alpha=0.9, label="Predicted increment")
        ax_inc.axhline(0, color="black", linewidth=0.6)
        ax_inc.set_ylabel("db (mm/epoch)", fontsize=12)
        ax_inc.legend(fontsize=11, loc="upper right")
        ax_inc.set_title("Incremental compaction per 5-day epoch", fontsize=11, fontweight="bold")
        ax_inc.grid(True, alpha=0.3)

        ax_cum.plot(ts["date"], ts["cum_obs_mm"], color="grey", linewidth=1.2, alpha=0.8, label="Observed (cumulative)")
        ax_cum.plot(ts["date"], ts["cum_pred_mm"], color=color, linewidth=1.2, alpha=0.9, label="Predicted (cumulative)")
        ax_cum.set_xlim(T_START, T_END)
        ax_cum.set_xlabel("Date", fontsize=12)
        ax_cum.set_ylabel("Cumulative db (mm)", fontsize=12)
        ax_cum.tick_params(axis="x", rotation=30)
        ax_cum.legend(fontsize=11, loc="upper left")
        ax_cum.set_title("Cumulative compaction", fontsize=11, fontweight="bold")
        ax_cum.grid(True, alpha=0.3)

        fig.tight_layout(rect=[0, 0, 1, 0.93])
        out_path = PLOTS_DIR / f"inc_fit_{layer}.png"
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved: {out_path}")

# ── Plot: Step 2 — GPS vs alpha*Σdb_pred (cumulative) ─────────────────────────
if "cum_gps_obs" in dir() and "cum_gps_pred" in dir():
    gps_dates = pd.to_datetime(sum_df.index)
    mask_plot = (gps_dates >= T_START) & (gps_dates < T_END)
    if mask_plot.sum() > 4:
        fig, ax = plt.subplots(figsize=(11, 5))
        ax.plot(gps_dates[mask_plot], cum_gps_obs[mask_plot], color="black", linewidth=1.4,
                label="GPS observed cumulative (mm)")
        ax.plot(gps_dates[mask_plot], cum_gps_pred[mask_plot], color="red", linewidth=1.4,
                linestyle="--", label=f"α·Σdb_pred  (α={alpha:.3f})")
        ax.set_xlabel("Date", fontsize=13)
        ax.set_ylabel("Cumulative surface deformation (mm)", fontsize=13)
        ax.set_title(f"TUKU Step 2: GPS vs model  |  R²={r2_gps:.3f}  α={alpha:.4f}",
                     fontsize=13, fontweight="bold")
        ax.legend(fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis="x", rotation=30)
        fig.tight_layout()
        out_path = PLOTS_DIR / "step2_gps_vs_model.png"
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved: {out_path}")

print("\nDone.")
