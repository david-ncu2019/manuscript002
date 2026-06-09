"""
tau_demo_TUKU/12_stress_strain_per_layer.py
============================================
Per-layer cumulative stress-strain regression for TUKU station.

Physical model
--------------
For each layer j independently (no total-deformation constraint):

  b_j(t) = S_ke * H_j(t) + (S_kv - S_ke) * V_j(t)

where:
  b_j(t)  = cumulative MLCW compaction [mm], zero-referenced to REF_DATE (negative = compaction)
  H_j(t)  = piezometric head [m], zero-referenced to REF_DATE (negative = head fell)
  V_j(t)  = virgin (inelastic) exceedance term [m]:
               V_j(t) = min(0, cummin(H_j(t)) - h_c_j)
             This is 0 until H_j first falls below h_c_j, then grows negative
             as head sets new historical lows.
  S_ke    = elastic bulk storage [mm/m]
  S_kv    = inelastic bulk storage [mm/m], S_kv >= S_ke physically

Fitting: scipy.optimize.nnls on [H, V] with two non-negative coefficients.
  coef[0] = S_ke, coef[1] = S_kv - S_ke
  S_kv = S_ke + coef[1]

Why cumulative (not incremental)?
  Per-epoch delta-H ~0.001-0.003 m (tiny). The secular multi-year head decline
  that drives bulk of observed compaction is fully captured in cumulative H(t).
  Per-epoch regression fits noise; cumulative regression fits the physical signal.

Why two regressors?
  A naive single regressor per regime inverts S_ke vs S_kv because late elastic
  epochs carry accumulated permanent strain. The virgin term V(t) accounts for
  permanent strain separately, allowing S_ke to reflect truly elastic recovery.

Sign convention:
  When head falls (H < 0), compaction increases (b more negative).
  Both H and b are negative in the inelastic compacting domain.
  S_ke = b / H > 0 when both negative.  Physically: S_ke >= 0, S_kv >= S_ke.

Reference:
  Hung et al. 2021 (Terzaghi consolidation approach, Choushui River Alluvial Fan)
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json
import os
from pathlib import Path
from scipy.optimize import nnls

# ============================================================
# PATHS
# ============================================================
REPO = Path(__file__).parent.parent
TUKU_DIR = REPO / 'tau_demo_TUKU'
DATA_DIR = TUKU_DIR / 'data'
RESULTS_DIR = TUKU_DIR / 'results'
PLOT_DIR = TUKU_DIR / 'plots' / 'results' / 'stress_strain'
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
PLOT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# CONSTANTS
# ============================================================
REF_DATE = pd.Timestamp('2015-01-16')
EPOCH_DAYS = 5  # 5-day cadence

# ============================================================
# LAYER CONFIGURATION (from tau_results.csv)
# ============================================================
# h_c values are already zero-referenced to REF_DATE (pre-2015 min - REF_DATE head)
# tau_opt is in 5-day epoch units
LAYERS = [
    {'layer': 'F1', 'wellcode': '09050111', 'gwl_file': 'HONGLUN_gwl_timeseries.feather',
     'h_c': -2.344, 'tau_epochs': 42},
    {'layer': 'T1', 'wellcode': '09050111', 'gwl_file': 'HONGLUN_gwl_timeseries.feather',
     'h_c': -2.344, 'tau_epochs': 72},
    {'layer': 'F2', 'wellcode': '09050321', 'gwl_file': 'TUKU_gwl_timeseries.feather',
     'h_c': -5.086, 'tau_epochs': 0},
    {'layer': 'T2', 'wellcode': '09170121', 'gwl_file': 'LUNZI_gwl_timeseries.feather',
     'h_c': -8.457, 'tau_epochs': 72},
    {'layer': 'F3', 'wellcode': '09050331', 'gwl_file': 'TUKU_gwl_timeseries.feather',
     'h_c': -4.456, 'tau_epochs': 0},
    {'layer': 'F4', 'wellcode': '09080251', 'gwl_file': 'LIUZHUANG_gwl_timeseries.feather',
     'h_c': -7.008, 'tau_epochs': 105},
]

# TUKU layer thicknesses from borehole log (YL_WSYL23G1_TUKU.xlsx), not ring-to-ring spans.
# total_m = full depth zone per layer (0 to boundary defined by classify_table ring depths).
# Use total_m for elastic S_ske conversion (all materials deform elastically above h_c).
# Use LAYER_COMPRESSIBLE_THICKNESS for inelastic S_skv conversion (fine-grained only).
# Source: compute_borehole_thickness.py; layer bounds from TUKU_classify_table.csv.
LAYER_THICKNESS = {
    'F1': 41.577,   # borehole 0–41.577 m: 25.000 m aquifer + 16.577 m aquitard
    'T1':  8.729,   # borehole 41.577–50.306 m: 1.306 m aquifer + 7.423 m aquitard
    'F2': 106.284,  # borehole 50.306–156.59 m: 94.194 m aquifer + 12.090 m aquitard
    'T2': 16.299,   # borehole 156.59–172.889 m: 6.000 m aquifer + 10.299 m aquitard
    'F3': 110.494,  # borehole 172.889–283.383 m: 33.500 m aquifer + 76.994 m aquitard
    'F4': 16.617,   # borehole 283.383–300 m: 0.000 m aquifer + 16.617 m aquitard (entirely silt/mud)
}

# Fine-grained (compressible) thickness per layer for inelastic S_skv conversion.
# WARNING — F4 aquitard_m = 16.617 m but F4 has 0.0 m aquifer material.
# F4 IHM-F elastic storage result is geomechanically invalid at TUKU.
LAYER_COMPRESSIBLE_THICKNESS = {
    'F1':  16.577,
    'T1':   7.423,
    'F2':  12.090,
    'T2':  10.299,
    'F3':  76.994,
    'F4':  16.617,
}

# Published Choushui River Alluvial Fan specific-storage bounds.
# Source: Hung et al. 2021 (WRR); values from 07_joint_search.py BOUNDS dict.
# Used for feasibility check after decoupled two-step fit.
LITERATURE_BOUNDS = {
    'F1': {'s_ske_min': 7.27e-6,  's_ske_max': 3.87e-4,
           's_skv_min': 5.90e-5,  's_skv_max': 2.20e-3},
    'T1': {'s_ske_min': 0,        's_ske_max': 0,
           's_skv_min': 0,        's_skv_max': 0},
    'F2': {'s_ske_min': 2.86e-6,  's_ske_max': 9.89e-5,
           's_skv_min': 1.60e-5,  's_skv_max': 1.20e-3},
    'T2': {'s_ske_min': 4.47e-6,  's_ske_max': 9.89e-5,
           's_skv_min': 1.60e-5,  's_skv_max': 1.00e-3},
    'F3': {'s_ske_min': 4.96e-6,  's_ske_max': 1.14e-4,
           's_skv_min': 1.53e-5,  's_skv_max': 2.00e-3},
    'F4': {'s_ske_min': 3.93e-6,  's_ske_max': 7.96e-5,
           's_skv_min': 1.78e-4,  's_skv_max': 3.00e-3},
}


def load_cumulative_mlcw():
    """
    Load cumulative MLCW from TUKU_reconst_grouped_cleaned.csv.
    Zero-reference each column to REF_DATE value.
    Returns DataFrame indexed by datetime (5-day cadence, from 2003-12-06).
    """
    fpath = DATA_DIR / 'TUKU_reconst_grouped_cleaned.csv'
    df = pd.read_csv(fpath, parse_dates=['datetime'])
    df = df.set_index('datetime')
    df.index = pd.to_datetime(df.index)

    # Zero-reference: subtract each layer's value at REF_DATE
    ref_row = df.loc[REF_DATE]
    df_zero = df - ref_row
    return df_zero  # [mm], 0 at REF_DATE, negative = compaction


def load_gwl_absolute(gwl_file, wellcode):
    """
    Load absolute daily GWL from feather, set datetime index.
    Zero-reference to REF_DATE value (subtract head on REF_DATE).
    Returns daily Series, zero-referenced [m].
    Wellcode kept as string.
    """
    fpath = DATA_DIR / gwl_file
    df = pd.read_feather(str(fpath))
    df = df.set_index('datetime')
    df.index = pd.to_datetime(df.index)

    wc = str(wellcode)  # ensure string, never int
    if wc not in df.columns:
        raise KeyError(f"Wellcode {wc} not found in {gwl_file}. Available: {df.columns.tolist()}")

    series = df[wc]

    # REF_DATE absolute head value
    avail = series.dropna()
    pre_ref = avail.index[avail.index <= REF_DATE]
    if len(pre_ref) == 0:
        raise ValueError(f"No GWL data on or before REF_DATE for wellcode {wc}")
    ref_val = avail.loc[pre_ref[-1]]

    # Zero-reference
    series_zero = series - ref_val
    return series_zero, ref_val


def apply_tau_lag(series_daily, tau_epochs):
    """
    Shift head timeseries forward in time by tau_epochs * EPOCH_DAYS days.
    This makes H(t) represent the head at time (t - tau), i.e., the driver
    of compaction observed at time t.
    """
    if tau_epochs == 0:
        return series_daily
    shift_days = int(tau_epochs * EPOCH_DAYS)
    return series_daily.shift(shift_days, freq='D')


def align_gwl_to_mlcw(mlcw_df, gwl_series_daily, layer):
    """
    Align daily GWL to 5-day MLCW grid using merge_asof (nearest, tolerance 3 days).
    Only include rows from REF_DATE onward.
    Returns aligned DataFrame with columns [H, b].
    """
    mlcw_sub = mlcw_df[[layer]].copy()
    mlcw_sub.index = pd.to_datetime(mlcw_sub.index).astype("datetime64[ns]")
    mlcw_sub = mlcw_sub[mlcw_sub.index >= REF_DATE].rename(columns={layer: 'b'})

    gwl_df = gwl_series_daily.dropna().reset_index()
    gwl_df.columns = ['datetime', 'H']
    gwl_df['datetime'] = pd.to_datetime(gwl_df['datetime']).astype("datetime64[ns]")
    gwl_df = gwl_df[gwl_df['datetime'] >= REF_DATE].sort_values('datetime')

    mlcw_reset = mlcw_sub.reset_index().sort_values('datetime')

    merged = pd.merge_asof(
        mlcw_reset,
        gwl_df,
        on='datetime',
        tolerance=pd.Timedelta('3D'),
        direction='nearest'
    ).set_index('datetime')

    merged = merged.dropna(subset=['H', 'b'])
    return merged


def compute_virgin_term(H_series, h_c):
    """
    Compute the virgin (inelastic exceedance) term V(t).
    V(t) = min(0, cummin(H(t)) - h_c)
    This is 0 until H falls below h_c for the first time, then steps down
    as H sets new historical lows below h_c.
    Physical meaning: tracks how far head has permanently penetrated into
    the inelastic regime below the preconsolidation head h_c.
    """
    H_series = np.asarray(H_series, dtype=float)
    cummin_H = np.minimum.accumulate(H_series)
    # V = 0 when cummin > h_c (head not yet in inelastic regime)
    # V < 0 when cummin < h_c (inelastic exceedance)
    V = np.minimum(0.0, cummin_H - h_c)
    return V


def fit_two_regressor_nnls(H, b):
    """
    Fit b = S_ke * H + (S_kv - S_ke) * V using NNLS.
    Design matrix columns: [H, V] where both are negative in compacting domain.
    NNLS enforces coef >= 0.
      coef[0] = S_ke
      coef[1] = S_kv - S_ke  (must be >= 0, so S_kv >= S_ke)
    Returns: S_ke, S_kv, residual_norm, predicted b
    Note: We negate b and the regressors because NNLS solves Ax=b with x>=0
    and our signals are negative. Negating both sides preserves the equation.
    """
    H = np.asarray(H, dtype=float)
    b = np.asarray(b, dtype=float)

    # Both H and b are negative in compacting domain.
    # Flip signs: -b = S_ke * (-H) + (S_kv - S_ke) * (-V)
    # Since H < 0, V <= 0, and b < 0: -H > 0, -V >= 0, -b > 0
    neg_H = -H
    neg_b = -b

    # We need V: already embedded via external call; pass directly.
    # This function expects H and V already computed, caller passes combined X.
    # Re-check: caller should pass X as 2-column array [H, V].
    raise NotImplementedError("Use fit_two_regressor_nnls_X instead")


def fit_two_regressor_nnls_X(H_arr, V_arr, b_arr):
    """
    Fit b = S_ke * H + delta * V  where delta = S_kv - S_ke >= 0.
    NNLS on negated system (all values in compacting domain are negative).
    Returns: (S_ke, S_kv, coef_delta, residuals_norm, b_pred)
    """
    H_arr = np.asarray(H_arr, dtype=float)
    V_arr = np.asarray(V_arr, dtype=float)
    b_arr = np.asarray(b_arr, dtype=float)

    # Negate everything so NNLS sees positive quantities
    A = np.column_stack([-H_arr, -V_arr])  # shape (n, 2), both cols >= 0
    rhs = -b_arr  # positive

    coef, residual_sq = nnls(A, rhs)
    S_ke = coef[0]
    delta = coef[1]
    S_kv = S_ke + delta

    b_pred = S_ke * H_arr + delta * V_arr
    return S_ke, S_kv, delta, float(residual_sq), b_pred


def fit_two_step_decoupled(H_arr, V_arr, b_arr, h_c, min_elastic_pts=10):
    """
    Decoupled two-step regression to break H-V collinearity.

    Step 1: Estimate S_ke from elastic-only epochs (V == 0, i.e. H > h_c) via
            through-origin OLS: S_ke = sum(H_e * b_e) / sum(H_e^2).
            Both H_e and b_e are negative in the compacting domain, so their
            product is positive and S_ke comes out positive.

    Step 2: Freeze S_ke. Compute residual b_resid = b - S_ke * H (pure
            inelastic). Regress b_resid against V via through-origin OLS on
            inelastic epochs (V < 0) to get delta = S_kv - S_ke >= 0.

    Falls back to simultaneous NNLS when fewer than min_elastic_pts elastic
    epochs exist (layer is fully inelastic; decoupling is impossible).

    Returns: (S_ke, S_kv, delta, b_pred, method_str, n_elastic_pts)
      method_str: 'two_step' or 'nnls_fallback'
    """
    H_arr = np.asarray(H_arr, dtype=float)
    V_arr = np.asarray(V_arr, dtype=float)
    b_arr = np.asarray(b_arr, dtype=float)

    elastic_mask = (V_arr == 0)
    n_elastic = int(elastic_mask.sum())

    if n_elastic < min_elastic_pts:
        # Layer is essentially always inelastic — fall back to simultaneous NNLS
        S_ke, S_kv, delta, _, b_pred = fit_two_regressor_nnls_X(H_arr, V_arr, b_arr)
        return S_ke, S_kv, delta, b_pred, 'nnls_fallback', n_elastic

    # Step 1: elastic-only OLS
    H_e = H_arr[elastic_mask]
    b_e = b_arr[elastic_mask]
    denom = float(np.dot(H_e, H_e))
    S_ke = float(np.dot(H_e, b_e) / denom) if denom > 0 else 0.0
    S_ke = max(0.0, S_ke)

    # Step 2: residual NNLS on inelastic epochs
    b_resid = b_arr - S_ke * H_arr
    inelastic_mask = (V_arr < 0)
    n_inelastic = int(inelastic_mask.sum())

    if n_inelastic >= 5:
        V_i = V_arr[inelastic_mask]
        b_i = b_resid[inelastic_mask]
        # Both V_i and b_i are negative; product is positive -> delta > 0
        denom_v = float(np.dot(V_i, V_i))
        delta_raw = float(np.dot(V_i, b_i) / denom_v) if denom_v > 0 else 0.0
        delta = max(0.0, delta_raw)
    else:
        delta = 0.0

    S_kv = S_ke + delta
    b_pred = S_ke * H_arr + delta * V_arr
    return S_ke, S_kv, delta, b_pred, 'two_step', n_elastic


def compute_r2(obs, pred):
    """R-squared of obs vs pred."""
    obs = np.asarray(obs)
    pred = np.asarray(pred)
    mask = np.isfinite(obs) & np.isfinite(pred)
    if mask.sum() < 2:
        return float('nan')
    ss_res = np.sum((obs[mask] - pred[mask])**2)
    ss_tot = np.sum((obs[mask] - obs[mask].mean())**2)
    if ss_tot == 0:
        return float('nan')
    return 1.0 - ss_res / ss_tot


def naive_elastic_inelastic_split(H_arr, b_arr, h_c):
    """
    Diagnostic: naive per-regime through-origin OLS.
    Returns S_ke_naive, S_kv_naive for comparison.
    This is expected to INVERT (S_ke >> S_kv) on high-compaction layers.
    """
    elastic_mask = H_arr > h_c
    inelastic_mask = H_arr <= h_c

    def ols_no_intercept(x, y):
        """S = sum(x*y) / sum(x*x), both x and y negative -> S positive."""
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        if len(x) < 2:
            return float('nan')
        denom = np.dot(x, x)
        if denom == 0:
            return float('nan')
        return np.dot(x, y) / denom

    S_ke_naive = max(0.0, ols_no_intercept(H_arr[elastic_mask], b_arr[elastic_mask]))
    S_kv_naive = max(0.0, ols_no_intercept(H_arr[inelastic_mask], b_arr[inelastic_mask]))
    n_e = int(elastic_mask.sum())
    n_i = int(inelastic_mask.sum())
    return S_ke_naive, S_kv_naive, n_e, n_i


def plot_layer(layer_name, df_aligned, h_c, S_ke, S_kv, V_arr, b_pred, out_path):
    """
    Two-panel plot per layer:
    Panel 1: Scatter H vs b colored by regime, with fitted model curve.
    Panel 2: Timeseries of cumulative obs vs pred.
    """
    H_arr = df_aligned['H'].values
    b_arr = df_aligned['b'].values
    dates = df_aligned.index

    elastic_mask = H_arr > h_c
    inelastic_mask = H_arr <= h_c

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(f'TUKU Station — Layer {layer_name} Stress-Strain Analysis', fontsize=15, fontweight='bold')

    # Panel 1: Scatter H vs b
    ax = axes[0]
    ax.scatter(H_arr[elastic_mask], b_arr[elastic_mask],
               c='steelblue', alpha=0.5, s=15, label=f'Elastic (n={elastic_mask.sum()})')
    ax.scatter(H_arr[inelastic_mask], b_arr[inelastic_mask],
               c='firebrick', alpha=0.5, s=15, label=f'Inelastic (n={inelastic_mask.sum()})')
    # Model fit line
    H_sort_idx = np.argsort(H_arr)
    ax.plot(H_arr[H_sort_idx], b_pred[H_sort_idx], 'k-', lw=1.5, alpha=0.8, label='Two-regressor fit')
    ax.axvline(h_c, color='gray', linestyle='--', lw=1, label=f'$h_c$ = {h_c:.3f} m')
    ax.axhline(0, color='gray', linestyle=':', lw=0.8)
    ax.axvline(0, color='gray', linestyle=':', lw=0.8)
    ax.set_xlabel('Head H(t) [m, zero-ref to 2015-01-16]', fontsize=13)
    ax.set_ylabel('Cumulative compaction b(t) [mm]', fontsize=13)
    ax.set_title(f'{layer_name}: S_ke={S_ke:.2f}, S_kv={S_kv:.2f} mm/m\nRatio={S_kv/S_ke:.1f}x' if S_ke > 0 else f'{layer_name}: S_ke=0 (underdetermined)', fontsize=12)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.tick_params(labelsize=12)

    # Panel 2: Timeseries
    ax2 = axes[1]
    ax2.plot(dates, b_arr, color='gray', lw=1.5, label='Observed cumulative')
    ax2.plot(dates, b_pred, color='darkorange', lw=1.5, linestyle='--', label='Predicted (two-regressor)')
    ax2.axhline(0, color='gray', linestyle=':', lw=0.8)
    ax2.set_xlabel('Date', fontsize=13)
    ax2.set_ylabel('Cumulative compaction [mm]', fontsize=13)
    ax2.set_title(f'{layer_name}: Obs range [{b_arr.min():.1f}, {b_arr.max():.1f}] mm\n'
                  f'Pred range [{b_pred.min():.1f}, {b_pred.max():.1f}] mm', fontsize=12)
    ax2.legend(fontsize=11)
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(labelsize=12)

    plt.tight_layout()
    plt.savefig(str(out_path), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Plot saved: {out_path}")


def process_layer(layer_cfg, mlcw_df):
    """
    Full pipeline for one layer.
    Returns dict with all results.
    """
    layer = layer_cfg['layer']
    wellcode = str(layer_cfg['wellcode'])  # always string
    gwl_file = layer_cfg['gwl_file']
    h_c = float(layer_cfg['h_c'])
    tau_epochs = int(layer_cfg['tau_epochs'])
    span_m = LAYER_THICKNESS.get(layer, 0.0)

    print(f"\n{'='*60}")
    print(f"Layer: {layer}  |  Wellcode: {wellcode}  |  tau={tau_epochs} epochs ({tau_epochs*EPOCH_DAYS} days)")
    print(f"  h_c = {h_c:.4f} m (zero-ref preconsolidation head)")
    print(f"  span_m = {span_m:.2f} m (layer thickness)")

    # 1. Load and zero-reference absolute GWL
    gwl_zero, gwl_ref_val = load_gwl_absolute(gwl_file, wellcode)
    print(f"  GWL REF_DATE absolute value: {gwl_ref_val:.4f} m MSL")
    print(f"  GWL post-REF_DATE range (zero-ref): {gwl_zero[gwl_zero.index >= REF_DATE].dropna().min():.4f} to {gwl_zero[gwl_zero.index >= REF_DATE].dropna().max():.4f} m")

    # 2. Apply tau lag (shift GWL forward so H(t) = head at t - tau)
    gwl_lagged = apply_tau_lag(gwl_zero, tau_epochs)
    if tau_epochs > 0:
        print(f"  Applied tau lag: {tau_epochs} epochs = {tau_epochs * EPOCH_DAYS} days")

    # 3. Align GWL to MLCW 5-day grid
    df_aligned = align_gwl_to_mlcw(mlcw_df, gwl_lagged, layer)
    n_pts = len(df_aligned)
    print(f"  Aligned points: {n_pts}  ({df_aligned.index.min().date()} to {df_aligned.index.max().date()})")

    if n_pts < 10:
        print(f"  INSUFFICIENT DATA: only {n_pts} joint points. Skipping.")
        return {
            'layer': layer, 'wellcode': wellcode, 'tau_epochs': tau_epochs,
            'n_pts': n_pts, 'error': 'insufficient_data',
            'S_ke_mmpm': None, 'S_kv_mmpm': None,
            'S_ske_m1': None, 'S_skv_m1': None, 'ratio': None, 'r2': None
        }

    H_arr = df_aligned['H'].values
    b_arr = df_aligned['b'].values

    # Physical check: is there meaningful head variation?
    H_range = np.nanmax(H_arr) - np.nanmin(H_arr)
    print(f"  H range (zero-ref): {H_arr.min():.4f} to {H_arr.max():.4f} m (range = {H_range:.4f} m)")
    print(f"  b range (cumul):    {b_arr.min():.4f} to {b_arr.max():.4f} mm")

    # 4. Compute virgin term V(t)
    V_arr = compute_virgin_term(H_arr, h_c)
    n_inelastic_virgin = int((V_arr < 0).sum())
    print(f"  Virgin term V: n_inelastic_epochs = {n_inelastic_virgin} / {n_pts}")

    # 5. Naive regime split (diagnostic only, expected to invert)
    S_ke_naive, S_kv_naive, n_e, n_i = naive_elastic_inelastic_split(H_arr, b_arr, h_c)
    ratio_naive = S_kv_naive / S_ke_naive if S_ke_naive > 0 else float('nan')
    print(f"  [DIAGNOSTIC] Naive split: S_ke={S_ke_naive:.4f}, S_kv={S_kv_naive:.4f} mm/m, ratio={ratio_naive:.2f}x (n_e={n_e}, n_i={n_i})")
    if np.isfinite(ratio_naive) and ratio_naive < 1.0:
        print(f"    => Inversion confirmed (ratio<1) — naive split mixes permanent and elastic strain.")
    elif np.isfinite(ratio_naive) and ratio_naive < 3.0:
        print(f"    => Ratio {ratio_naive:.2f}x < 3x physical minimum — likely contamination.")

    # 6. Two-regressor NNLS fit
    S_ke, S_kv, delta, resid_norm, b_pred = fit_two_regressor_nnls_X(H_arr, V_arr, b_arr)
    r2 = compute_r2(b_arr, b_pred)
    ratio_2reg = S_kv / S_ke if S_ke > 0 else float('nan')

    print(f"  [TWO-REGRESSOR NNLS]")
    print(f"    S_ke = {S_ke:.4f} mm/m  |  S_kv = {S_kv:.4f} mm/m")
    print(f"    delta (S_kv - S_ke) = {delta:.4f} mm/m")
    print(f"    S_kv / S_ke ratio = {ratio_2reg:.2f}x  (physical range: 3-50x)")
    print(f"    R2 = {r2:.4f}")
    print(f"    Obs range: [{b_arr.min():.2f}, {b_arr.max():.2f}] mm  |  Pred range: [{b_pred.min():.2f}, {b_pred.max():.2f}] mm")

    # Physical bounds check
    if S_ke < 0:
        print(f"    HALT: S_ke = {S_ke:.4f} < 0 — violates physical bounds. Layer rejected.")
    if S_kv < 0:
        print(f"    HALT: S_kv = {S_kv:.4f} < 0 — violates physical bounds. Layer rejected.")
    if np.isfinite(ratio_2reg):
        if ratio_2reg < 3.0 and S_ke > 0 and delta > 0.001:
            print(f"    FLAG: Ratio {ratio_2reg:.2f}x < 3x — outside physical range (3-50x).")
        elif ratio_2reg > 50.0:
            print(f"    FLAG: Ratio {ratio_2reg:.2f}x > 50x — outside physical range (3-50x).")
        else:
            print(f"    Physical check PASSED: ratio in [3, 50]x range.")

    # 6b. Decoupled two-step fit
    (S_ke_2s, S_kv_2s, delta_2s, b_pred_2s,
     fit_method_2s, n_elastic_pts) = fit_two_step_decoupled(H_arr, V_arr, b_arr, h_c)
    r2_2s = compute_r2(b_arr, b_pred_2s)
    ratio_2s = S_kv_2s / S_ke_2s if S_ke_2s > 0 else float('nan')

    print(f"\n  [TWO-STEP DECOUPLED ({fit_method_2s}, n_elastic={n_elastic_pts})]")
    print(f"    S_ke = {S_ke_2s:.4f} mm/m  |  S_kv = {S_kv_2s:.4f} mm/m")
    print(f"    delta (S_kv - S_ke) = {delta_2s:.4f} mm/m")
    print(f"    S_kv / S_ke ratio = {ratio_2s:.2f}x  (physical range: 3-50x)" if np.isfinite(ratio_2s) else "    S_kv / S_ke ratio = undefined (S_ke=0)")
    print(f"    R2 = {r2_2s:.4f}")
    print(f"    Pred range: [{b_pred_2s.min():.2f}, {b_pred_2s.max():.2f}] mm")

    # 6c. Feasibility check against Choushui literature bounds + ratio gate
    compressible_m = LAYER_COMPRESSIBLE_THICKNESS.get(layer, 0.0)
    bounds = LITERATURE_BOUNDS.get(layer, {})
    feasible_2s = None
    feas_notes_2s = []
    S_ske_2s_m1 = None
    S_skv_2s_m1 = None

    if S_ke_2s > 0 and span_m > 0:
        S_ske_2s_m1 = S_ke_2s / (span_m * 1000.0)
        S_skv_2s_m1 = S_kv_2s / (compressible_m * 1000.0) if compressible_m > 0 else None

        if bounds and bounds.get('s_ske_max', 0) > 0:
            in_ske = bounds['s_ske_min'] <= S_ske_2s_m1 <= bounds['s_ske_max']
            in_skv = (S_skv_2s_m1 is not None and
                      bounds['s_skv_min'] <= S_skv_2s_m1 <= bounds['s_skv_max'])
            specific_ratio_2s = (S_skv_2s_m1 / S_ske_2s_m1
                                  if S_skv_2s_m1 is not None else float('nan'))
            in_ratio = (3.0 <= specific_ratio_2s <= 50.0) if np.isfinite(specific_ratio_2s) else False
            feasible_2s = bool(in_ske and in_skv and in_ratio)
            feas_notes_2s = [
                f"S_ske: {S_ske_2s_m1:.3e} {'IN' if in_ske else 'OUT'} [{bounds['s_ske_min']:.2e}, {bounds['s_ske_max']:.2e}] m-1",
                (f"S_skv: {S_skv_2s_m1:.3e} {'IN' if in_skv else 'OUT'} [{bounds['s_skv_min']:.2e}, {bounds['s_skv_max']:.2e}] m-1"
                 if S_skv_2s_m1 is not None else "S_skv: undefined (compressible_m=0)"),
                (f"Ratio: {specific_ratio_2s:.2f}x {'IN' if in_ratio else 'OUT'} [3, 50]"
                 if np.isfinite(specific_ratio_2s) else "Ratio: undefined (S_skv undefined)"),
            ]
            print(f"    FEASIBILITY: {'PASS — all three gates clear' if feasible_2s else 'FAIL — see notes'}")
            for note in feas_notes_2s:
                print(f"      {note}")
        else:
            print(f"    FEASIBILITY: skipped (T1 pinch-out — no literature bounds defined)")
            feas_notes_2s = ['T1 pinch-out: no bounds defined']

    # 7. Convert to specific storage [m-1]
    # Elastic S_ske: divide by total borehole span (all materials deform elastically above h_c).
    # Inelastic S_skv: divide by fine-grained (compressible) thickness only.
    # Source: discussions/2026-05-29-technical-clarifications.md lines 178-182.
    S_ske_m1 = None
    S_skv_m1 = None
    compressible_m = LAYER_COMPRESSIBLE_THICKNESS.get(layer, 0.0)
    if span_m > 0 and S_ke > 0:
        S_ske_m1 = S_ke / (span_m * 1000.0)
        S_skv_m1 = S_kv / (compressible_m * 1000.0) if compressible_m > 0 else None
        print(f"    S_ske = {S_ske_m1:.4e} m-1  (total span = {span_m:.3f} m)")
        if S_skv_m1 is not None:
            print(f"    S_skv = {S_skv_m1:.4e} m-1  (fine-grained thickness = {compressible_m:.3f} m)")
        else:
            print(f"    S_skv: undefined (compressible_m = 0 for {layer})")
    elif span_m == 0:
        print(f"    S_ske/S_skv: undefined (span_m = 0 for {layer})")

    # 8. Plot
    out_plot = PLOT_DIR / f'stress_strain_{layer}.png'
    plot_layer(layer, df_aligned, h_c, S_ke, S_kv, V_arr, b_pred, out_plot)

    # 8b. Export per-epoch timeseries CSV
    ts_dir = RESULTS_DIR / 'timeseries'
    ts_dir.mkdir(parents=True, exist_ok=True)
    out_ts = ts_dir / f'TUKU_{layer}_cumulative_timeseries.csv'
    ts_df = pd.DataFrame({
        'datetime': df_aligned.index,
        'H_zero_ref_m': H_arr,
        'b_obs_mm': b_arr,
        'V_m': V_arr,
        'b_pred_nnls_mm': b_pred,
        'b_pred_2step_mm': b_pred_2s,
    })
    ts_df.to_csv(str(out_ts), index=False)
    print(f"  Timeseries saved: {out_ts}")

    # 9. Regime count based on h_c level
    elastic_mask = H_arr > h_c
    inelastic_mask = H_arr <= h_c

    result = {
        'layer': layer,
        'wellcode': wellcode,
        'tau_epochs': tau_epochs,
        'h_c_m': h_c,
        'span_m': span_m,
        'n_pts': n_pts,
        'n_elastic_Hbased': int(elastic_mask.sum()),
        'n_inelastic_Hbased': int(inelastic_mask.sum()),
        'n_inelastic_virgin': n_inelastic_virgin,
        # Two-regressor results
        'S_ke_mmpm': float(S_ke),
        'S_kv_mmpm': float(S_kv),
        'delta_mmpm': float(delta),
        'ratio_Skv_Ske': float(ratio_2reg) if np.isfinite(ratio_2reg) else None,
        'r2': float(r2) if np.isfinite(r2) else None,
        'span_m_elastic': float(span_m),           # total borehole span — denominator for S_ske
        'compressible_m': float(compressible_m),   # fine-grained thickness — denominator for S_skv
        'S_ske_m1': float(S_ske_m1) if S_ske_m1 is not None else None,
        'S_skv_m1': float(S_skv_m1) if S_skv_m1 is not None else None,
        # Naive diagnostic
        'S_ke_naive_mmpm': float(S_ke_naive),
        'S_kv_naive_mmpm': float(S_kv_naive),
        'ratio_naive': float(ratio_naive) if np.isfinite(ratio_naive) else None,
        'obs_min_mm': float(b_arr.min()),
        'obs_max_mm': float(b_arr.max()),
        'pred_min_mm': float(b_pred.min()),
        'pred_max_mm': float(b_pred.max()),
        # Two-step decoupled fit
        'S_ke_2s_mmpm': float(S_ke_2s),
        'S_kv_2s_mmpm': float(S_kv_2s),
        'delta_2s_mmpm': float(delta_2s),
        'ratio_2s': float(ratio_2s) if np.isfinite(ratio_2s) else None,
        'r2_2s': float(r2_2s) if np.isfinite(r2_2s) else None,
        'fit_method_2s': fit_method_2s,
        'n_elastic_pts': n_elastic_pts,
        'S_ske_2s_m1': float(S_ske_2s_m1) if S_ske_2s_m1 is not None else None,
        'S_skv_2s_m1': float(S_skv_2s_m1) if S_skv_2s_m1 is not None else None,
        'feasible_2s': feasible_2s,
        'feas_notes_2s': feas_notes_2s,
        'pred_2s_min_mm': float(b_pred_2s.min()),
        'pred_2s_max_mm': float(b_pred_2s.max()),
    }
    return result


def main():
    print("=" * 60)
    print("TUKU Per-Layer Stress-Strain Analysis")
    print(f"REF_DATE: {REF_DATE.date()}")
    print(f"Epoch cadence: {EPOCH_DAYS} days")
    print("=" * 60)

    # Load cumulative MLCW (zero-referenced to REF_DATE)
    mlcw_df = load_cumulative_mlcw()
    print(f"\nLoaded cumulative MLCW: {mlcw_df.shape[0]} epochs, "
          f"{mlcw_df.index.min().date()} to {mlcw_df.index.max().date()}")
    ref_check = mlcw_df.loc[REF_DATE]
    print(f"Value at REF_DATE (should be ~0 for all layers): {ref_check.to_dict()}")

    # Process each layer
    all_results = []
    for layer_cfg in LAYERS:
        try:
            result = process_layer(layer_cfg, mlcw_df)
            all_results.append(result)
        except Exception as e:
            print(f"\nERROR processing layer {layer_cfg['layer']}: {e}")
            import traceback
            traceback.print_exc()
            all_results.append({
                'layer': layer_cfg['layer'], 'wellcode': layer_cfg['wellcode'],
                'error': str(e),
                'S_ke_mmpm': None, 'S_kv_mmpm': None,
                'S_ske_m1': None, 'S_skv_m1': None, 'ratio_Skv_Ske': None, 'r2': None
            })

    # Save results
    df_results = pd.DataFrame(all_results)
    csv_path = RESULTS_DIR / 'stress_strain_per_layer.csv'
    df_results.to_csv(str(csv_path), index=False)
    print(f"\nResults saved: {csv_path}")

    json_path = RESULTS_DIR / 'stress_strain_per_layer.json'
    with open(str(json_path), 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"Results saved: {json_path}")

    # Print summary table
    print("\n" + "=" * 120)
    print("SUMMARY TABLE — TUKU Per-Layer Stress-Strain Results")
    print("  NNLS = simultaneous two-regressor NNLS  |  2STEP = decoupled elastic-first OLS + residual NNLS")
    print("=" * 120)
    print(f"{'Layer':<6} {'n_e':>5} {'NNLS_ratio':>11} {'2STEP_ratio':>12} {'R2_NNLS':>9} {'R2_2S':>7} "
          f"{'S_ske_2s':>12} {'S_skv_2s':>12} {'Feasible':>9}")
    print(f"{'':6} {'(elast)':>5} {'(x)':>11} {'(x)':>12} {'':>9} {'':>7} "
          f"{'(m-1)':>12} {'(m-1)':>12} {'':>9}")
    print("-" * 120)
    for r in all_results:
        lyr = r.get('layer', '?')
        n_e = r.get('n_elastic_pts', '?')
        rat_nnls = r.get('ratio_Skv_Ske')
        rat_2s = r.get('ratio_2s')
        r2_nnls = r.get('r2')
        r2_2s = r.get('r2_2s')
        sskea = r.get('S_ske_2s_m1')
        sskva = r.get('S_skv_2s_m1')
        feas = r.get('feasible_2s')
        rat_nnls_s = f"{rat_nnls:.1f}" if rat_nnls is not None and np.isfinite(rat_nnls) else "undef"
        rat_2s_s = f"{rat_2s:.1f}" if rat_2s is not None and np.isfinite(rat_2s) else "undef"
        r2_nnls_s = f"{r2_nnls:.3f}" if r2_nnls is not None and np.isfinite(float(r2_nnls)) else "None"
        r2_2s_s = f"{r2_2s:.3f}" if r2_2s is not None and np.isfinite(float(r2_2s)) else "None"
        sskea_s = f"{sskea:.2e}" if sskea is not None else "None"
        sskva_s = f"{sskva:.2e}" if sskva is not None else "None"
        feas_s = "PASS" if feas is True else ("FAIL" if feas is False else "N/A")
        print(f"{lyr:<6} {str(n_e):>5} {rat_nnls_s:>11} {rat_2s_s:>12} {r2_nnls_s:>9} {r2_2s_s:>7} "
              f"{sskea_s:>12} {sskva_s:>12} {feas_s:>9}")
    print("=" * 120)

    print("\nPhysical interpretation:")
    print("  NNLS ratio = simultaneous S_kv/S_ke (compressed by H-V collinearity when >90% inelastic)")
    print("  2STEP ratio = decoupled S_kv/S_ke (elastic OLS first; breaks collinearity)")
    print("  S_ske, S_skv [m-1] from 2-step: specific storage using borehole thicknesses")
    print("  Feasible: IN Choushui literature bounds (Hung 2021) AND ratio in [3, 50]x")
    print("Done.")


if __name__ == '__main__':
    main()
