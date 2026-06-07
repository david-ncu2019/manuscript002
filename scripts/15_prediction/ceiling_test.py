"""
ceiling_test.py — Ceiling test for the two-observer model at TUKU.

Target model:
    MLCW_k(t) = a_k * InSAR_trend(t)          [Term 1: shared secular trend]
              + b_k * InSAR_detrended(t - tau_k)  [Term 2: lagged InSAR wiggle]
              + c_k * GWL_detrended(t - phi_k)    [Term 3: lagged GWL wiggle, NEW]

Term 1: trend reconstruction (shared secular sinking)
Term 2: dynamic reconstruction (lagged detrended InSAR wiggle)
Term 3: layer-specific GWL correction (lagged detrended GWL head change)

Walk-forward validation: 4 folds (hold-outs 2022, 2023, 2024, 2025).
All parameters (a_k, b_k, tau_k, c_k, phi_k) are re-estimated from the TRAINING
window only per fold (no leakage from test-period data).

GWL is loaded from the v3 layer assignment; PHI_MAX=73 epochs (~365 days) to
capture F2's ~70-epoch coupling peak identified in ring cross-correlation.

Outputs:
    results/ceiling_test/TUKU_ceiling_test.csv

Decision gate:
    term2_adds_skill = (skill > 0 in >= 2 of 4 holdout years) [InSAR-only]
    term3_adds_skill = (skill3 > 0 in >= 2 of 4 holdout years) [GWL adds to term1+2]
    If term3 rescues F2 → "InSAR+GWL recovers main aquifer compaction" is defensible
    If neither term2 nor term3 work → deliverable is term-1 trend only

Usage:
    $env:PYTHONPATH = ""; conda run -n fafalab python scripts/15_prediction/ceiling_test.py
    $env:PYTHONPATH = ""; conda run -n fafalab python scripts/15_prediction/ceiling_test.py --station TUKU
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ── Path setup ────────────────────────────────────────────────────────────────
_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO))
from paths import SCRIPTS_ROOT, DATA_ROOT, RESULTS_ROOT, MLCW_RECONST_DIR, INSAR_FEATHER

# v3 assignment CSV (paths.py GWL_ASSIGNMENT points to v1 which doesn't exist; v3 is the authoritative file)
GWL_ASSIGNMENT = DATA_ROOT / 'gwl' / 'gwl_to_mlcw_layer_assignment_v3.csv'

LAYERS = ['F1', 'T1', 'F2', 'T2', 'F3', 'F4']
CONFINED_LAYERS = {'F2', 'F3'}  # tau=0 on these is a known aliasing artifact

# Walk-forward folds: (train_end_year, test_year)
FOLDS = [
    (2021, 2022),
    (2022, 2023),
    (2023, 2024),
    (2024, 2025),
]

TAU_MAX = 48   # max InSAR lag in 5-day epochs (~240 days = 8 months)
PHI_MAX = 73   # max GWL lag in 5-day epochs (~365 days); captures F2's ~70-epoch peak
MIN_TRAIN_N = 40  # minimum training samples required to fit


# ── Data loading ──────────────────────────────────────────────────────────────

def load_mlcw(station: str) -> pd.DataFrame:
    path = MLCW_RECONST_DIR / f'{station}_reconst_grouped.csv'
    df = pd.read_csv(path, parse_dates=['datetime'])
    return df.sort_values('datetime').reset_index(drop=True)


def load_insar(station: str) -> pd.Series:
    df = pd.read_feather(INSAR_FEATHER)
    row = df[df['Ename'] == station]
    if len(row) != 1:
        raise ValueError(f"Station '{station}' not found in InSAR feather.")
    epoch_cols, epoch_dates = [], []
    for c in df.columns:
        if isinstance(c, str) and c.startswith('D') and len(c) == 9:
            try:
                epoch_cols.append(c)
                epoch_dates.append(pd.to_datetime(c[1:], format='%Y%m%d'))
            except Exception:
                pass
    vals = row[epoch_cols].values.flatten().astype(float)
    # Convert to mm if values appear to be in metres
    if np.nanmedian(np.abs(vals[~np.isnan(vals)])) < 1.0:
        vals *= 1000.0
    return pd.Series(vals, index=pd.DatetimeIndex(epoch_dates), name='insar_mm').sort_index()


def align_data(station: str):
    """Load and align MLCW + InSAR to a common 5-day timeline."""
    mlcw_df = load_mlcw(station)
    insar_s = load_insar(station)

    insar_tmp = insar_s.reset_index()
    insar_tmp.columns = ['datetime', 'insar_mm']

    # Align InSAR to MLCW timestamps (tolerance 10 days — MLCW is ~monthly)
    merged = pd.merge_asof(
        mlcw_df.sort_values('datetime'),
        insar_tmp.sort_values('datetime'),
        on='datetime',
        direction='nearest',
        tolerance=pd.Timedelta('10D'),
    ).sort_values('datetime').reset_index(drop=True)

    merged['t_days'] = (merged['datetime'] - merged['datetime'].iloc[0]).dt.total_seconds() / 86400.0
    return merged


def load_gwl(station: str, layer: str) -> pd.Series | None:
    """
    Load the head timeseries for the v3-assigned well for (station, layer).
    Returns a pd.Series of head values (m MSL) indexed by date, or None if unavailable.
    Merges to MLCW timeline with tolerance=10D to avoid stale-endpoint injection.
    Sign convention: dh_raw = H(t) - H(t_ref), negative = head fell (never negate).
    """
    try:
        asgn = pd.read_csv(GWL_ASSIGNMENT, dtype={'assigned_wellcode': str})
    except Exception as e:
        print(f"    [GWL] Cannot read assignment CSV: {e}")
        return None

    row = asgn[(asgn['station'] == station) & (asgn['layer'] == layer)]
    if len(row) == 0:
        print(f"    [GWL] No v3 assignment for {station}/{layer}")
        return None

    feather_rel = row.iloc[0].get('feather_file', '')
    if not feather_rel or pd.isna(feather_rel):
        print(f"    [GWL] No feather_file in assignment for {station}/{layer}")
        return None

    feather_path = SCRIPTS_ROOT / feather_rel
    if not feather_path.exists():
        # Try MLCW-paired feather as fallback
        wellcode = str(row.iloc[0]['assigned_wellcode'])
        well_station = Path(feather_rel).stem.replace('_gwl_timeseries', '')
        alt = SCRIPTS_ROOT / 'data' / 'gwl' / 'mlcw_gwl_timeseries' / f'{station}_{well_station}_{wellcode}.feather'
        if alt.exists():
            feather_path = alt
        else:
            print(f"    [GWL] Feather not found: {feather_path}")
            return None

    try:
        gwl_df = pd.read_feather(feather_path)
    except Exception as e:
        print(f"    [GWL] Error reading {feather_path.name}: {e}")
        return None

    # Feather format: columns are ['datetime', wellcode1, wellcode2, ...]
    # Use the assigned wellcode as the head column
    wellcode = str(row.iloc[0]['assigned_wellcode'])
    date_col = 'datetime' if 'datetime' in gwl_df.columns else gwl_df.columns[0]

    if wellcode in gwl_df.columns:
        head_col = wellcode
    else:
        # Fallback: first numeric column that isn't the date
        num_cols = [c for c in gwl_df.columns if c != date_col and
                    (gwl_df[c].dtype in (float, int) or 'float' in str(gwl_df[c].dtype))]
        if not num_cols:
            print(f"    [GWL] Wellcode {wellcode} not found in {feather_path.name}: {list(gwl_df.columns)}")
            return None
        head_col = num_cols[0]
        print(f"    [GWL] Wellcode {wellcode} not found; using first numeric col '{head_col}'")

    gwl_df[date_col] = pd.to_datetime(gwl_df[date_col])
    gwl_s = gwl_df.set_index(date_col)[head_col].sort_index().rename('gwl_m')
    gwl_s = gwl_s[~gwl_s.index.duplicated(keep='first')]
    return gwl_s


def align_gwl(gwl_s: pd.Series, merged: pd.DataFrame) -> np.ndarray:
    """
    Align GWL series to the MLCW/InSAR merged timeline using merge_asof (tolerance=10D).
    Returns array of head values aligned to merged['datetime'], NaN where unavailable.
    """
    gwl_tmp = gwl_s.reset_index()
    gwl_tmp.columns = ['datetime', 'gwl_m']
    # Normalise both sides to ns to avoid us/ns merge mismatch
    gwl_tmp['datetime'] = pd.to_datetime(gwl_tmp['datetime']).astype('datetime64[ns]')
    ref = merged[['datetime']].copy()
    ref['datetime'] = pd.to_datetime(ref['datetime']).astype('datetime64[ns]')
    aligned = pd.merge_asof(
        ref.sort_values('datetime'),
        gwl_tmp.sort_values('datetime'),
        on='datetime',
        direction='nearest',
        tolerance=pd.Timedelta('10D'),
    )
    return aligned['gwl_m'].values.astype(float)


# ── Detrending ────────────────────────────────────────────────────────────────

def fit_linear_trend(t: np.ndarray, y: np.ndarray):
    """OLS linear trend on non-NaN values. Returns (intercept, slope)."""
    valid = ~np.isnan(y)
    if valid.sum() < 5:
        return np.nan, np.nan
    A = np.column_stack([np.ones(valid.sum()), t[valid]])
    coef, *_ = np.linalg.lstsq(A, y[valid], rcond=None)
    return float(coef[0]), float(coef[1])


def apply_trend(t: np.ndarray, intercept: float, slope: float) -> np.ndarray:
    return intercept + slope * t


# ── Per-fold fitting ──────────────────────────────────────────────────────────

def compute_fbar_ols(dy_mlcw: np.ndarray, dy_insar: np.ndarray) -> float:
    """
    OLS slope of ΔMLCW ~ ΔInSAR (both anchored to first valid epoch).
    This is the per-fold a_k estimate (Term 1 scaling factor).
    Returns slope through origin (no intercept — both deltas start at 0).
    """
    valid = ~np.isnan(dy_mlcw) & ~np.isnan(dy_insar)
    if valid.sum() < MIN_TRAIN_N:
        return np.nan
    denom = float(np.dot(dy_insar[valid], dy_insar[valid]))
    if denom < 1e-8:
        return np.nan
    return float(np.dot(dy_mlcw[valid], dy_insar[valid]) / denom)


def fit_term2(
    y_resid: np.ndarray,
    x_det: np.ndarray,
    tau: int,
) -> float:
    """
    OLS slope of residual ~ lagged detrended InSAR (through origin).
    y_resid = MLCW - term1_prediction
    x_det[tau:] aligns with y_resid[:-tau] (GWL leads MLCW by tau)
    Returns b_k or np.nan.
    """
    if tau == 0:
        x_lag = x_det
    else:
        x_lag = np.full_like(x_det, np.nan)
        x_lag[tau:] = x_det[:-tau]

    valid = ~np.isnan(y_resid) & ~np.isnan(x_lag)
    if valid.sum() < MIN_TRAIN_N:
        return np.nan
    denom = float(np.dot(x_lag[valid], x_lag[valid]))
    if denom < 1e-8:
        return np.nan
    return float(np.dot(y_resid[valid], x_lag[valid]) / denom)


def predict_term12(
    t: np.ndarray,
    y_insar: np.ndarray,
    intercept_insar: float,
    slope_insar: float,
    a_k: float,
    b_k: float,
    tau: int,
    anchor_mlcw: float,
    anchor_insar: float,
) -> np.ndarray:
    """
    Reconstruct MLCW_k(t) = anchor_mlcw + a_k*(InSAR(t)-anchor_insar) + b_k*InSAR_det(t-tau).
    """
    insar_trend = apply_trend(t, intercept_insar, slope_insar)
    y_det = y_insar - insar_trend

    if tau == 0:
        x_lag = y_det
    else:
        x_lag = np.full_like(y_det, np.nan)
        x_lag[tau:] = y_det[:-tau]

    pred = anchor_mlcw + a_k * (y_insar - anchor_insar) + b_k * x_lag
    return pred


def skill_score(y_true: np.ndarray, y_pred: np.ndarray, y_baseline: np.ndarray) -> float:
    """skill = 1 - RMSE_pred/RMSE_baseline. Positive means better than baseline."""
    valid = ~np.isnan(y_true) & ~np.isnan(y_pred) & ~np.isnan(y_baseline)
    if valid.sum() < 2:
        return np.nan
    rmse_pred = float(np.sqrt(np.mean((y_true[valid] - y_pred[valid]) ** 2)))
    rmse_base = float(np.sqrt(np.mean((y_true[valid] - y_baseline[valid]) ** 2)))
    if rmse_base < 1e-8:
        return np.nan
    return float(1.0 - rmse_pred / rmse_base)


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    valid = ~np.isnan(y_true) & ~np.isnan(y_pred)
    if valid.sum() < 2:
        return np.nan
    return float(np.sqrt(np.mean((y_true[valid] - y_pred[valid]) ** 2)))


def fit_term3(y_resid2: np.ndarray, gwl_det: np.ndarray, phi: int) -> float:
    """
    Bounded OLS for c_k in: y_resid2 = c_k * GWL_det(t - phi).
    c_k >= 0 enforced (compaction increases when head falls: negative GWL det → positive resid,
    so the sign works out with the raw series — no negation needed).
    Returns c_k >= 0 or np.nan.
    """
    if phi == 0:
        g_lag = gwl_det
    else:
        g_lag = np.full_like(gwl_det, np.nan)
        g_lag[phi:] = gwl_det[:-phi]

    valid = ~np.isnan(y_resid2) & ~np.isnan(g_lag)
    if valid.sum() < MIN_TRAIN_N:
        return np.nan
    denom = float(np.dot(g_lag[valid], g_lag[valid]))
    if denom < 1e-8:
        return np.nan
    c_k = float(np.dot(y_resid2[valid], g_lag[valid]) / denom)
    return max(0.0, c_k)   # bounded: c_k >= 0


def search_phi(y_resid2: np.ndarray, gwl_det: np.ndarray,
               phi_max: int = PHI_MAX) -> tuple[int, float]:
    """
    Grid search phi = 0..phi_max; select phi that minimises RMSE of term3 fit
    on the training window. Returns (best_phi, best_c_k).
    """
    best_phi, best_c_k, best_rmse_val = 0, 0.0, np.inf
    for phi in range(0, phi_max + 1):
        c_k = fit_term3(y_resid2, gwl_det, phi)
        if np.isnan(c_k):
            continue
        if phi == 0:
            g_lag = gwl_det
        else:
            g_lag = np.full_like(gwl_det, np.nan)
            g_lag[phi:] = gwl_det[:-phi]
        pred3 = c_k * g_lag
        valid = ~np.isnan(y_resid2) & ~np.isnan(pred3)
        if valid.sum() < MIN_TRAIN_N:
            continue
        r = float(np.sqrt(np.mean((y_resid2[valid] - pred3[valid]) ** 2)))
        if r < best_rmse_val:
            best_rmse_val = r
            best_phi = phi
            best_c_k = c_k
    return best_phi, best_c_k


# ── Main ceiling test ─────────────────────────────────────────────────────────

def run_ceiling_test(station: str, merged: pd.DataFrame = None) -> pd.DataFrame:
    print(f"\n=== Ceiling test: {station} ===")
    if merged is None:
        merged = align_data(station)
    avail_layers = [L for L in LAYERS if L in merged.columns]

    t_all = merged['t_days'].values
    x_all = merged['insar_mm'].values.astype(float)
    years = merged['datetime'].dt.year.values

    # Pre-load GWL for all layers (aligned to merged timeline)
    gwl_aligned = {}
    for layer in avail_layers:
        gwl_s = load_gwl(station, layer)
        if gwl_s is not None:
            gwl_aligned[layer] = align_gwl(gwl_s, merged)
            print(f"  [GWL] {layer}: loaded {(~np.isnan(gwl_aligned[layer])).sum()} valid epochs")
        else:
            gwl_aligned[layer] = None
            print(f"  [GWL] {layer}: unavailable — Term 3 will be skipped")

    rows = []

    for layer in avail_layers:
        y_all = merged[layer].values.astype(float)
        print(f"\n  Layer {layer}:")

        # In-sample fit (full 2015-2021 for reference)
        train_mask_full = (years <= 2021)
        t_tr = t_all[train_mask_full]
        x_tr = x_all[train_mask_full]
        y_tr = y_all[train_mask_full]

        # Full-record in-sample (informational only — not used in holdout)
        intercept_is, slope_is = fit_linear_trend(t_tr, x_tr)
        if np.isnan(intercept_is):
            print(f"    SKIP: insufficient data for InSAR trend fit")
            continue
        x_det_tr = x_tr - apply_trend(t_tr, intercept_is, slope_is)

        valid_tr = ~np.isnan(y_tr) & ~np.isnan(x_tr)
        if valid_tr.sum() < MIN_TRAIN_N:
            print(f"    SKIP: only {valid_tr.sum()} valid training epochs")
            continue

        # Anchor to first valid training epoch
        first_valid = np.where(~np.isnan(y_tr) & ~np.isnan(x_tr))[0][0]
        dy_tr = y_tr - y_tr[first_valid]
        dx_tr = x_tr - x_tr[first_valid]
        a_k_full = compute_fbar_ols(dy_tr, dx_tr)
        anchor_mlcw_full = float(y_tr[first_valid])
        anchor_insar_full = float(x_tr[first_valid])

        # Term-1 in-sample prediction
        pred1_tr = anchor_mlcw_full + a_k_full * (x_tr - anchor_insar_full)
        resid_tr = y_tr - pred1_tr
        r2_t1_insample = float(1 - np.nansum((y_tr - pred1_tr)**2) / np.nansum((y_tr - np.nanmean(y_tr))**2))

        # τ grid search in-sample (term 2)
        best_tau_is, best_r2_is, best_bk_is = 0, r2_t1_insample, 0.0
        for tau in range(0, TAU_MAX + 1):
            b_k = fit_term2(resid_tr, x_det_tr, tau)
            if np.isnan(b_k):
                continue
            # Predict with term 2 added
            if tau == 0:
                x_lag = x_det_tr
            else:
                x_lag = np.full_like(x_det_tr, np.nan)
                x_lag[tau:] = x_det_tr[:-tau]
            pred12 = pred1_tr + b_k * x_lag
            valid = ~np.isnan(y_tr) & ~np.isnan(pred12)
            if valid.sum() < MIN_TRAIN_N:
                continue
            ss_res = np.sum((y_tr[valid] - pred12[valid])**2)
            ss_tot = np.sum((y_tr[valid] - np.mean(y_tr[valid]))**2)
            r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else np.nan
            if not np.isnan(r2) and r2 > best_r2_is:
                best_r2_is = r2
                best_tau_is = tau
                best_bk_is = b_k

        r2_t12_insample = best_r2_is
        delta_r2_insample = r2_t12_insample - r2_t1_insample
        print(f"    In-sample  R2_term1={r2_t1_insample:.4f}  R2_term12={r2_t12_insample:.4f}  "
              f"dR2={delta_r2_insample:+.4f}  tau_opt={best_tau_is} epochs")

        # ── Walk-forward folds ────────────────────────────────────────────────
        fold_skills  = {}
        fold_rmses   = {}
        fold_aks     = {}
        fold_bks     = {}
        fold_taus    = {}
        fold_cks     = {}
        fold_phis    = {}
        fold_skill3s = {}
        fold_rmse3s  = {}

        gwl_layer = gwl_aligned.get(layer)  # None if unavailable

        for (train_end_yr, test_yr) in FOLDS:
            fold_name = f"skill_{test_yr}"
            tr_mask = (years <= train_end_yr)
            te_mask = (years == test_yr)

            t_fold_tr = t_all[tr_mask]
            x_fold_tr = x_all[tr_mask]
            y_fold_tr = y_all[tr_mask]
            t_fold_te = t_all[te_mask]
            x_fold_te = x_all[te_mask]
            y_fold_te = y_all[te_mask]

            def _nan_fold():
                fold_skills[fold_name] = np.nan
                fold_rmses[f'rmse_{test_yr}'] = np.nan
                fold_aks[f'a_k_{test_yr}'] = np.nan
                fold_bks[f'b_k_{test_yr}'] = np.nan
                fold_taus[f'tau_{test_yr}'] = np.nan
                fold_cks[f'c_k_{test_yr}'] = np.nan
                fold_phis[f'phi_{test_yr}'] = np.nan
                fold_skill3s[f'skill3_{test_yr}'] = np.nan
                fold_rmse3s[f'rmse3_{test_yr}'] = np.nan

            if te_mask.sum() < 2 or (~np.isnan(y_fold_te) & ~np.isnan(x_fold_te)).sum() < 2:
                _nan_fold(); continue

            # Estimate InSAR trend from TRAINING window only
            intercept_fold, slope_fold = fit_linear_trend(t_fold_tr, x_fold_tr)
            if np.isnan(intercept_fold):
                _nan_fold(); continue

            x_det_fold_tr = x_fold_tr - apply_trend(t_fold_tr, intercept_fold, slope_fold)

            # Anchor to first valid training epoch
            valid_fold_tr = ~np.isnan(y_fold_tr) & ~np.isnan(x_fold_tr)
            if valid_fold_tr.sum() < MIN_TRAIN_N:
                _nan_fold(); continue

            first_fold = np.where(valid_fold_tr)[0][0]
            anchor_mlcw = float(y_fold_tr[first_fold])
            anchor_insar = float(x_fold_tr[first_fold])
            dy_fold = y_fold_tr - anchor_mlcw
            dx_fold = x_fold_tr - anchor_insar

            # Fit a_k (Term 1) from training window
            a_k = compute_fbar_ols(dy_fold, dx_fold)
            if np.isnan(a_k):
                _nan_fold(); continue

            # Term-1 residual (training)
            pred1_fold = anchor_mlcw + a_k * (x_fold_tr - anchor_insar)
            resid_fold = y_fold_tr - pred1_fold

            # τ grid search on training window to find best (tau, b_k)
            best_tau, best_val, best_bk = 0, -np.inf, 0.0
            for tau in range(0, TAU_MAX + 1):
                b_k_cand = fit_term2(resid_fold, x_det_fold_tr, tau)
                if np.isnan(b_k_cand):
                    continue
                # Score: R² of term1+term2 on training
                if tau == 0:
                    x_lag_tr = x_det_fold_tr
                else:
                    x_lag_tr = np.full_like(x_det_fold_tr, np.nan)
                    x_lag_tr[tau:] = x_det_fold_tr[:-tau]
                pred12_tr = pred1_fold + b_k_cand * x_lag_tr
                valid_sc = ~np.isnan(y_fold_tr) & ~np.isnan(pred12_tr)
                if valid_sc.sum() < MIN_TRAIN_N:
                    continue
                ss_r = np.sum((y_fold_tr[valid_sc] - pred12_tr[valid_sc])**2)
                ss_t = np.sum((y_fold_tr[valid_sc] - np.mean(y_fold_tr[valid_sc]))**2)
                r2_cand = float(1 - ss_r / ss_t) if ss_t > 0 else np.nan
                if not np.isnan(r2_cand) and r2_cand > best_val:
                    best_val = r2_cand
                    best_tau = tau
                    best_bk = b_k_cand

            # Predict test year using training-estimated parameters
            x_det_te = x_fold_te - apply_trend(t_fold_te, intercept_fold, slope_fold)
            if best_tau == 0:
                x_lag_te = x_det_te
            else:
                # For test year, lagged detrended InSAR requires the last tau epochs of training
                # Concatenate tail of training x_det with test x_det, then slice
                tail_tr = x_det_fold_tr[-best_tau:]
                x_det_combined = np.concatenate([tail_tr, x_det_te])
                x_lag_te = x_det_combined[best_tau:]  # aligns with test window

            pred1_te = anchor_mlcw + a_k * (x_fold_te - anchor_insar)
            pred12_te = pred1_te + best_bk * x_lag_te

            # Skill: term1+2 vs term1-only as baseline
            sk = skill_score(y_fold_te, pred12_te, pred1_te)
            rms = rmse(y_fold_te, pred12_te)

            fold_skills[fold_name] = sk
            fold_rmses[f'rmse_{test_yr}'] = rms
            fold_aks[f'a_k_{test_yr}'] = a_k
            fold_bks[f'b_k_{test_yr}'] = best_bk
            fold_taus[f'tau_{test_yr}'] = best_tau

            # ── Term 3: GWL detrended lag search ─────────────────────────────
            best_phi, best_ck = np.nan, np.nan
            sk3, rms3 = np.nan, np.nan

            if gwl_layer is not None:
                gwl_fold_tr = gwl_layer[tr_mask].astype(float)
                gwl_fold_te = gwl_layer[te_mask].astype(float)

                # Detrend GWL from training window (linear)
                valid_gwl_tr = ~np.isnan(gwl_fold_tr)
                if valid_gwl_tr.sum() >= MIN_TRAIN_N:
                    gwl_int, gwl_slp = fit_linear_trend(t_fold_tr, gwl_fold_tr)
                    if not np.isnan(gwl_int):
                        gwl_det_tr = gwl_fold_tr - apply_trend(t_fold_tr, gwl_int, gwl_slp)
                        gwl_det_te = gwl_fold_te - apply_trend(t_fold_te, gwl_int, gwl_slp)

                        # y_resid2 = MLCW_obs_train - term1 - term2 (on training window)
                        pred12_tr_for_resid = pred1_fold + best_bk * (
                            x_det_fold_tr if best_tau == 0
                            else np.concatenate([[np.nan] * best_tau,
                                                 x_det_fold_tr[:-best_tau]])
                        )
                        y_resid2_tr = y_fold_tr - pred12_tr_for_resid

                        best_phi, best_ck = search_phi(y_resid2_tr, gwl_det_tr)

                        # Apply to test window
                        if best_phi == 0:
                            gwl_lag_te = gwl_det_te
                        else:
                            tail_gwl = gwl_det_tr[-best_phi:]
                            gwl_combined = np.concatenate([tail_gwl, gwl_det_te])
                            gwl_lag_te = gwl_combined[best_phi:]

                        pred123_te = pred12_te + best_ck * gwl_lag_te
                        sk3 = skill_score(y_fold_te, pred123_te, pred12_te)
                        rms3 = rmse(y_fold_te, pred123_te)

            fold_cks[f'c_k_{test_yr}'] = best_ck
            fold_phis[f'phi_{test_yr}'] = best_phi
            fold_skill3s[f'skill3_{test_yr}'] = sk3
            fold_rmse3s[f'rmse3_{test_yr}'] = rms3

            status = "PASS" if (not np.isnan(sk) and sk > 0) else "FAIL"
            gwl_str = ""
            if not np.isnan(sk3):
                gwl_str = (f"  | GWL: c_k={best_ck:.4f} phi={int(best_phi)}ep "
                           f"skill3={sk3:+.3f} rmse3={rms3:.1f}mm "
                           f"[{'PASS' if sk3 > 0 else 'FAIL'}]")
            print(f"    Fold {test_yr}: skill={sk:+.3f} rmse={rms:.2f}mm  "
                  f"a_k={a_k:.4f}  b_k={best_bk:.4f}  tau={best_tau}  [{status}]{gwl_str}")

        # Summarize term2: > 0 in >= 2 of 4 years
        skill_vals = [v for v in fold_skills.values() if not np.isnan(v)]
        n_positive = sum(1 for v in skill_vals if v > 0)
        term2_adds_skill = n_positive >= 2

        # Summarize term3 (GWL incremental): skill3 > 0 in >= 2 of 4 years,
        # c_k non-negative across all folds (sign stability)
        skill3_vals = [v for v in fold_skill3s.values() if not np.isnan(v)]
        n_positive3 = sum(1 for v in skill3_vals if v > 0)
        ck_vals = [v for v in fold_cks.values() if not np.isnan(v)]
        ck_stable = all(v >= 0 for v in ck_vals)   # c_k >= 0 is already enforced by fit_term3
        gwl_available = gwl_layer is not None
        term3_adds_skill = (n_positive3 >= 2) and gwl_available and ck_stable

        # τ boundary flag
        tau_at_boundary = any(
            (not np.isnan(v) and int(v) >= TAU_MAX)
            for v in fold_taus.values()
        )
        tau_zero_confined = (layer in CONFINED_LAYERS) and any(
            (not np.isnan(v) and int(v) == 0)
            for v in fold_taus.values()
        )

        row = dict(
            station=station,
            layer=layer,
            R2_insample_term1=round(r2_t1_insample, 5),
            R2_insample_term12=round(r2_t12_insample, 5),
            delta_R2_insample=round(delta_r2_insample, 5),
            tau_opt_insample=best_tau_is,
            b_k_insample=round(best_bk_is, 6),
            n_folds_positive_skill=n_positive,
            term2_adds_skill=term2_adds_skill,
            tau_at_boundary=tau_at_boundary,
            tau_zero_confined=tau_zero_confined,
            gwl_available=gwl_available,
            n_folds_gwl_positive_skill=n_positive3,
            term3_adds_skill=term3_adds_skill,
        )
        row.update(fold_skills)
        row.update(fold_rmses)
        row.update(fold_aks)
        row.update(fold_bks)
        row.update(fold_taus)
        row.update(fold_cks)
        row.update(fold_phis)
        row.update(fold_skill3s)
        row.update(fold_rmse3s)
        rows.append(row)

        verdict = "TERM2 HELPS" if term2_adds_skill else "TERM1 ONLY"
        gwl_verdict = (f"GWL (term3): {'ADDS SKILL' if term3_adds_skill else 'NO SKILL'} "
                       f"({n_positive3}/{len(skill3_vals)} folds)")
        print(f"    => {verdict}  ({n_positive}/{len(skill_vals)} folds positive)  |  {gwl_verdict}")
        if tau_at_boundary:
            print(f"    WARNING: tau_opt hit boundary ({TAU_MAX}) in at least one fold - consider raising TAU_MAX")
        if tau_zero_confined:
            print(f"    WARNING: tau=0 on confined layer {layer} - possible aliasing artifact")
        if not gwl_available:
            print(f"    INFO: GWL not available for {layer} - term3 skipped")

    return pd.DataFrame(rows)


# A4 landscape
A4_W = 11.7
A4_H = 8.3
DPI  = 300

HOLDOUT_YEARS  = [2022, 2023, 2024, 2025]
HOLDOUT_COLORS = ['#e8e8e8', '#fffbe6', '#e8e8e8', '#fffbe6']

# Verbose layer descriptions for informative filenames and titles
LAYER_DESC = {
    'F1': 'aquifer-F1_shallow',
    'T1': 'aquitard-T1',
    'F2': 'aquifer-F2_main',
    'T2': 'aquitard-T2',
    'F3': 'aquifer-F3_deep',
    'F4': 'aquifer-F4_deepest',
}


def _shade_holdouts(ax, dates):
    for yr, col in zip(HOLDOUT_YEARS, HOLDOUT_COLORS):
        ax.axvspan(pd.Timestamp(f'{yr}-01-01'), pd.Timestamp(f'{yr}-12-31'),
                   color=col, alpha=0.7, zorder=0)


def _annotate_skills(ax, row):
    y_min, y_max = ax.get_ylim()
    y_txt = y_min + 0.97 * (y_max - y_min)
    for yr in HOLDOUT_YEARS:
        sk = row.get(f'skill_{yr}', np.nan)
        if isinstance(sk, float) and np.isnan(sk):
            continue
        color = '#1a7f1a' if sk > 0 else '#cc1111'
        ax.text(pd.Timestamp(f'{yr}-07-01'), y_txt,
                f'{yr}\nskill={sk:+.2f}',
                ha='center', va='top', fontsize=7, color=color,
                bbox=dict(boxstyle='round,pad=0.15', fc='white', alpha=0.7, ec='none'))


def plot_ceiling_test(station: str, merged: pd.DataFrame, results_df: pd.DataFrame,
                      fig_dir: Path) -> None:
    """
    One A4-landscape PNG per layer, named informatively.
    Left panel:  full cumulative timeseries (observed vs term-1 vs term-1+2 vs term-1+2+3)
    Right panel: detrended residuals (MLCW−term1 vs term-2 wiggle vs term-2+3 combined)
    Uses fold-4 parameters (trained on 2015-2024, tested on 2025).
    GWL term (term3) plotted in green when available.
    """
    fig_dir.mkdir(parents=True, exist_ok=True)

    t_all = merged['t_days'].values
    x_all = merged['insar_mm'].values.astype(float)
    years = merged['datetime'].dt.year.values
    dates = pd.DatetimeIndex(merged['datetime'])

    # Fit InSAR trend from fold-4 training window (≤ 2024)
    tr_mask = years <= 2024
    intercept_f4, slope_f4 = fit_linear_trend(t_all[tr_mask], x_all[tr_mask])
    if np.isnan(intercept_f4):
        print("  [plot] Could not fit InSAR trend for fold-4; skipping figures.")
        return
    x_det_all = x_all - apply_trend(t_all, intercept_f4, slope_f4)

    avail_layers = [L for L in LAYERS if L in merged.columns]

    for layer in avail_layers:
        row_mask = results_df['layer'] == layer
        if not row_mask.any():
            continue
        row = results_df[row_mask].iloc[0]

        a_k = row.get('a_k_2025', np.nan)
        b_k = row.get('b_k_2025', np.nan)
        tau = int(row.get('tau_2025', 0)) if not np.isnan(row.get('tau_2025', np.nan)) else 0
        c_k = row.get('c_k_2025', np.nan)
        phi = int(row.get('phi_2025', 0)) if not np.isnan(row.get('phi_2025', np.nan)) else 0

        y_all = merged[layer].values.astype(float)

        if np.isnan(a_k):
            print(f"  [plot] {layer}: no fold-4 parameters, skipping.")
            continue

        # Anchor to first valid training epoch
        tr_y = y_all[tr_mask]
        tr_x = x_all[tr_mask]
        valid_tr = ~np.isnan(tr_y) & ~np.isnan(tr_x)
        if valid_tr.sum() < 5:
            print(f"  [plot] {layer}: insufficient training data, skipping.")
            continue
        first = np.where(valid_tr)[0][0]
        anchor_mlcw  = float(tr_y[first])
        anchor_insar = float(tr_x[first])

        # InSAR predictions over full record
        pred1_all = anchor_mlcw + a_k * (x_all - anchor_insar)
        if tau == 0:
            x_lag_all = x_det_all.copy()
        else:
            x_lag_all = np.full_like(x_det_all, np.nan)
            x_lag_all[tau:] = x_det_all[:-tau]
        pred12_all = pred1_all + b_k * x_lag_all
        resid_obs  = y_all - pred1_all
        term2_pred = b_k * x_lag_all

        # GWL term over full record (fold-4 c_k, phi)
        term3_pred = np.full(len(y_all), np.nan)
        gwl_str_short = ""
        has_gwl = (not np.isnan(c_k)) and row.get('gwl_available', False)
        if has_gwl:
            gwl_s = load_gwl(station, layer)
            if gwl_s is not None:
                gwl_arr = align_gwl(gwl_s, merged).astype(float)
                # Detrend GWL using fold-4 training window
                gwl_tr = gwl_arr[tr_mask]
                gwl_int, gwl_slp = fit_linear_trend(t_all[tr_mask], gwl_tr)
                if not np.isnan(gwl_int):
                    gwl_det_all = gwl_arr - apply_trend(t_all, gwl_int, gwl_slp)
                    if phi == 0:
                        gwl_lag_all = gwl_det_all
                    else:
                        gwl_lag_all = np.full_like(gwl_det_all, np.nan)
                        gwl_lag_all[phi:] = gwl_det_all[:-phi]
                    term3_pred = c_k * gwl_lag_all
                    gwl_str_short = f"c_k={c_k:.4f}  φ={phi}ep"

        pred123_all = pred12_all + np.where(np.isnan(term3_pred), 0.0, term3_pred)
        pred123_all[np.isnan(pred12_all)] = np.nan
        term23_pred = term2_pred + np.where(np.isnan(term3_pred), 0.0, term3_pred)
        term23_pred[np.isnan(term2_pred)] = np.nan

        # ── Build informative metadata strings ────────────────────────────
        t2_verdict = "TERM2 OK" if row.get('term2_adds_skill', False) else "TERM1 ONLY"
        t3_verdict = "GWL OK" if row.get('term3_adds_skill', False) else "GWL NO"
        n_pos  = int(row.get('n_folds_positive_skill', 0))
        n_pos3 = int(row.get('n_folds_gwl_positive_skill', 0))
        tau_flag = " ⚠ τ=0 confined" if row.get('tau_zero_confined') else (
                   " ⚠ τ@max" if row.get('tau_at_boundary') else "")
        layer_long = LAYER_DESC.get(layer, layer)

        # Per-fold summary for bottom text
        rmse_str_parts = []
        for yr in HOLDOUT_YEARS:
            rms_v = row.get(f'rmse_{yr}', np.nan)
            sk_v  = row.get(f'skill_{yr}', np.nan)
            sk3_v = row.get(f'skill3_{yr}', np.nan)
            if not np.isnan(rms_v):
                gwl_part = f" gwl_sk3={sk3_v:+.2f}" if not np.isnan(sk3_v) else ""
                rmse_str_parts.append(f"{yr}: RMSE={rms_v:.1f}mm sk2={sk_v:+.2f}{gwl_part}")
        rmse_str = "  ".join(rmse_str_parts)

        # ── Figure: 1 row × 2 columns, A4 landscape ───────────────────────
        fig, (ax_ts, ax_det) = plt.subplots(1, 2, figsize=(A4_W, A4_H), dpi=DPI)

        suptitle = (
            f"{station}  |  Layer {layer} ({layer_long})  |  "
            f"Model: MLCW = a_k·InSAR_trend + b_k·InSAR_det(τ) + c_k·GWL_det(φ)\n"
            f"Fold-4 (trained 2015–2024):  a_k={a_k:.4f}  b_k={b_k:.4f}  τ={tau}ep  "
            f"{gwl_str_short}  |  "
            f"{t2_verdict} ({n_pos}/4)  {t3_verdict} ({n_pos3}/4){tau_flag}"
        )
        fig.suptitle(suptitle, fontsize=9, y=1.01)

        # ── Left panel: full cumulative timeseries ─────────────────────────
        _shade_holdouts(ax_ts, dates)
        valid_obs = ~np.isnan(y_all)
        ax_ts.plot(dates[valid_obs], y_all[valid_obs], color='black', lw=1.4,
                   label='Observed MLCW', zorder=3)
        valid_t1 = ~np.isnan(pred1_all)
        ax_ts.plot(dates[valid_t1], pred1_all[valid_t1], color='steelblue', lw=1.1,
                   ls='--', label='Term-1  a_k·InSAR_trend', zorder=4)
        valid_t12 = ~np.isnan(pred12_all)
        ax_ts.plot(dates[valid_t12], pred12_all[valid_t12], color='darkorange', lw=1.1,
                   label=f'Term-1+2  +b_k·InSAR_det(τ={tau}ep)', zorder=4)
        if has_gwl:
            valid_t123 = ~np.isnan(pred123_all)
            ax_ts.plot(dates[valid_t123], pred123_all[valid_t123], color='forestgreen', lw=1.1,
                       ls=':', label=f'Term-1+2+3  +c_k·GWL_det(φ={phi}ep)', zorder=5)
        ax_ts.set_xlabel('Year', fontsize=8)
        ax_ts.set_ylabel('Cumulative compaction (mm)', fontsize=8)
        ax_ts.set_title('Cumulative timeseries — observed vs predicted', fontsize=9)
        ax_ts.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax_ts.tick_params(labelsize=8)
        ax_ts.legend(fontsize=7, loc='lower left')
        _annotate_skills(ax_ts, row)

        # ── Right panel: detrended residuals ──────────────────────────────
        _shade_holdouts(ax_det, dates)
        ax_det.axhline(0, color='grey', lw=0.7, zorder=1)
        valid_res = ~np.isnan(resid_obs)
        ax_det.plot(dates[valid_res], resid_obs[valid_res], color='black', lw=1.1,
                    label='Observed residual  (MLCW − Term-1)', zorder=3)
        valid_t2 = ~np.isnan(term2_pred)
        ax_det.plot(dates[valid_t2], term2_pred[valid_t2], color='darkorange', lw=1.0,
                    label=f'Term-2 InSAR  b_k·InSAR_det(τ={tau}ep)', zorder=4)
        if has_gwl:
            valid_t23 = ~np.isnan(term23_pred)
            ax_det.plot(dates[valid_t23], term23_pred[valid_t23], color='forestgreen', lw=1.1,
                        ls=':', label=f'Term-2+3  +c_k·GWL_det(φ={phi}ep)', zorder=5)
        ax_det.set_xlabel('Year', fontsize=8)
        ax_det.set_ylabel('Residual (mm)', fontsize=8)
        ax_det.set_title('Detrended residual — InSAR (orange) + GWL (green) vs observed (black)', fontsize=9)
        ax_det.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax_det.tick_params(labelsize=8)
        ax_det.legend(fontsize=7, loc='upper left')
        _annotate_skills(ax_det, row)

        # Per-fold summary text
        fig.text(0.5, -0.02, rmse_str, ha='center', fontsize=7, color='#333333',
                 style='italic')

        fig.tight_layout()

        # Informative filename: station_layer_t2verdict_t3verdict_nfolds.png
        fname = (
            f"{station}_{layer}_{layer_long}_"
            f"{'t2ok' if row.get('term2_adds_skill') else 't1only'}_"
            f"{'gwlok' if row.get('term3_adds_skill') else 'gwlno'}_"
            f"{n_pos}of4.png"
        )
        out = fig_dir / fname
        fig.savefig(out, dpi=DPI, bbox_inches='tight', format='png')
        plt.close(fig)
        print(f"  Saved: {out.name}")


def print_summary(df: pd.DataFrame):
    print("\n" + "="*90)
    print("CEILING TEST SUMMARY — Two-observer model (InSAR + GWL)")
    print("="*90)
    print(f"{'Layer':<6}  {'sk_22':>7}  {'sk_23':>7}  {'sk_24':>7}  {'sk_25':>7}  "
          f"{'T2 verdict':<14}  {'sk3_22':>7}  {'sk3_23':>7}  {'sk3_24':>7}  {'sk3_25':>7}  {'T3 GWL'}")
    print("-"*90)
    for _, r in df.iterrows():
        def fmt(v):
            return f"{v:+.3f}" if not (isinstance(v, float) and np.isnan(v)) else "    nan"
        t2_verdict = "TERM2 OK" if r.get('term2_adds_skill', False) else "TERM1 ONLY"
        t3_verdict = "GWL OK" if r.get('term3_adds_skill', False) else ("GWL NO" if r.get('gwl_available', False) else "GWL N/A")
        flags = ""
        if r.get('tau_at_boundary', False):
            flags += "[tau@max]"
        if r.get('tau_zero_confined', False):
            flags += "[tau=0!]"
        n3 = int(r.get('n_folds_gwl_positive_skill', 0))
        print(
            f"{r['layer']:<6}  "
            f"{fmt(r.get('skill_2022', np.nan)):>7}  "
            f"{fmt(r.get('skill_2023', np.nan)):>7}  "
            f"{fmt(r.get('skill_2024', np.nan)):>7}  "
            f"{fmt(r.get('skill_2025', np.nan)):>7}  "
            f"{t2_verdict+flags:<14}  "
            f"{fmt(r.get('skill3_2022', np.nan)):>7}  "
            f"{fmt(r.get('skill3_2023', np.nan)):>7}  "
            f"{fmt(r.get('skill3_2024', np.nan)):>7}  "
            f"{fmt(r.get('skill3_2025', np.nan)):>7}  "
            f"{t3_verdict} ({n3}/4)"
        )
    print("="*90)

    any_t2 = df['term2_adds_skill'].any() if 'term2_adds_skill' in df.columns else False
    any_t3 = df['term3_adds_skill'].any() if 'term3_adds_skill' in df.columns else False
    f2_t3  = (df[df['layer'] == 'F2']['term3_adds_skill'].any()
              if ('term3_adds_skill' in df.columns and 'F2' in df['layer'].values)
              else False)

    print("\nDECISION GATE:")
    if f2_t3:
        layers_ok3 = df[df.get('term3_adds_skill', False)]['layer'].tolist() if any_t3 else []
        print(f"  GWL (term3) rescues F2! Layers with GWL skill: {layers_ok3}")
        print("  => 'InSAR+GWL recovers main aquifer compaction at TUKU' is peer-reviewable.")
        print("     Next: run at XIUTAN and YUANCHANG to test generalizability.")
    elif any_t3:
        layers_ok3 = df[df['term3_adds_skill']]['layer'].tolist()
        print(f"  GWL adds skill at: {layers_ok3} (but not F2)")
        print("  => PROCEED with GWL correction for validated layers only.")
    elif any_t2:
        layers_ok2 = df[df['term2_adds_skill']]['layer'].tolist()
        print(f"  InSAR (term2) adds skill at: {layers_ok2}")
        print("  => PROCEED with InSAR-only pipeline for these layers.")
        print("     GWL did not add incremental skill — investigate GWL assignment quality.")
    else:
        print("  Neither InSAR term2 nor GWL term3 adds skill for any layer.")
        print("  => DELIVERABLE: Term-1 trend reconstruction only.")
        print("     Both observers insufficient at 5-day epoch resolution for seasonal dynamics.")
        print("     F3/F4 deep layers: temporal resolution limit is the binding constraint.")

    print()


def main():
    parser = argparse.ArgumentParser(description="Ceiling test: MLCW = a*InSAR_trend + b*InSAR_det(t-tau)")
    parser.add_argument('--station', default='TUKU', help='Station name (default: TUKU)')
    args = parser.parse_args()

    out_dir = RESULTS_ROOT / 'ceiling_test'
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir = SCRIPTS_ROOT / 'figures' / 'ceiling_test'

    # Load data once — reused for both numeric results and figures
    merged = align_data(args.station)

    df = run_ceiling_test(args.station, merged)

    if df.empty:
        print("No results produced.")
        return

    print_summary(df)

    out_path = out_dir / f'{args.station}_ceiling_test.csv'
    df.to_csv(out_path, index=False)
    print(f"Results written to: {out_path}")

    print("\nGenerating figures...")
    plot_ceiling_test(args.station, merged, df, fig_dir)
    print("Done.")


if __name__ == '__main__':
    main()
