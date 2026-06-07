"""
Walk-forward temporal validation — pure computation, no file I/O.

DATA LEAKAGE RULE (non-negotiable):
  Every parameter used to predict hold-out year Y must be estimated exclusively
  from epochs where year < Y. Full-record parameters from reconstruction_metrics.csv
  must NOT enter this module — they contain test-period data.
"""
import numpy as np
import pandas as pd
from scipy import stats
import sys
from pathlib import Path

# Import ihmf_detrend from scripts/10_ihmf/ (one directory up)
_ihmf_dir = Path(__file__).resolve().parent.parent / '10_ihmf'
if str(_ihmf_dir) not in sys.path:
    sys.path.insert(0, str(_ihmf_dir))
from ihmf_detrend import detrend_signal, reconstruct_trend

# ── Module constants ────────────────────────────────────────────────────────────
TAU_MAX_INSAR = 73        # ~365 days at 5-day InSAR resolution
MIN_DETRENDED_R = 0.2     # |r| below this → fall back to trend-only (α=0, τ=0)

# ── Parameter estimation (per-fold, training window only) ─────────────────────

def compute_fbar_station(train_mlcw: np.ndarray, train_insar: np.ndarray):
    """
    Anchored OLS slope of ΔMLCW_k ~ ΔInSAR on training-window epochs only.
    Replicates compute_fbar_anchored from scripts/13_seasonal_insar/02_reconstruction_visualization.py:103.

    Returns (fbar, anchor_mlcw, anchor_insar).
    fbar = nan if fewer than 20 valid paired epochs.
    """
    valid = ~np.isnan(train_mlcw) & ~np.isnan(train_insar)
    if valid.sum() < 20:
        return np.nan, np.nan, np.nan
    first = int(np.where(valid)[0][0])
    dy_mlcw  = train_mlcw  - train_mlcw[first]
    dy_insar = train_insar - train_insar[first]
    v = valid.copy()
    v[first] = False
    denom = float(np.dot(dy_insar[v], dy_insar[v]))
    if denom < 1e-6:
        return np.nan, float(train_mlcw[first]), float(train_insar[first])
    fbar = float(np.dot(dy_mlcw[v], dy_insar[v]) / denom)
    return fbar, float(train_mlcw[first]), float(train_insar[first])


def compute_seasonal_params_station(peryear_df: pd.DataFrame, train_years: list[int],
                                     layer: str):
    """
    Mean r1_k and dphi1_k over training years only.
    Returns (r1_mean, dphi1_mean_days) or (nan, nan) if no training data.
    """
    sub = peryear_df[
        (peryear_df['layer'] == layer) &
        (peryear_df['year'].isin(train_years))
    ]
    if sub.empty:
        return np.nan, np.nan
    r1_vals = sub['r1_k'].dropna().values
    dphi1_vals = sub['dphi1_k_days'].dropna().values
    r1_mean    = float(np.mean(r1_vals))    if len(r1_vals) > 0    else np.nan
    dphi1_mean = float(np.mean(dphi1_vals)) if len(dphi1_vals) > 0 else np.nan
    return r1_mean, dphi1_mean


def grid_search_tau_insar(
    mlcw_detrended: np.ndarray,
    insar_detrended: np.ndarray,
    tau_max: int = TAU_MAX_INSAR,
):
    """
    Grid-search optimal lag τ between detrended InSAR (lead) and detrended MLCW (lag).

    For each τ ∈ [0, tau_max], pairs InSAR_det[i] with MLCW_det[i+τ]
    (InSAR leads MLCW by τ epochs). Returns (τ_opt, max_corr, alpha) where τ_opt
    maximises |Pearson r| and alpha is the OLS slope at τ_opt.

    Falls back to (0, 0.0, 0.0) if fewer than 6 valid pairs exist.
    """
    n = len(mlcw_detrended)
    best_tau = 0
    best_corr = 0.0
    best_alpha = 0.0

    for tau in range(min(tau_max + 1, n - 5)):
        n_pair = n - tau
        if n_pair < 6:
            continue
        y = mlcw_detrended[tau:]       # MLCW (lags behind InSAR)
        x = insar_detrended[:n_pair]   # InSAR (leads)
        valid = ~np.isnan(y) & ~np.isnan(x)
        if valid.sum() < 6:
            continue
        r, _ = stats.pearsonr(y[valid], x[valid])
        abs_r = abs(r)
        if abs_r > best_corr:
            best_corr = abs_r
            best_tau = tau
            dx = x[valid] - x[valid].mean()
            dy = y[valid] - y[valid].mean()
            denom = float(np.dot(dx, dx))
            best_alpha = float(np.dot(dy, dx) / denom) if denom > 1e-12 else 0.0

    return best_tau, best_corr, best_alpha


# ── Baselines ─────────────────────────────────────────────────────────────────

def _persistence_baseline(fbar: float, anchor_mlcw: float, anchor_insar: float,
                           insar_last_train: float,
                           holdout_len: int) -> np.ndarray:
    """Constant prediction: last training MLCW value held flat."""
    last_mlcw = anchor_mlcw + fbar * (insar_last_train - anchor_insar)
    return np.full(holdout_len, last_mlcw)


def _trend_extrap_baseline(train_mlcw: np.ndarray, train_t: np.ndarray,
                            holdout_t: np.ndarray) -> np.ndarray:
    """Linear fit to training window, extrapolated into hold-out."""
    valid = ~np.isnan(train_mlcw)
    if valid.sum() < 10:
        return np.full(len(holdout_t), np.nan)
    slope, intercept, *_ = stats.linregress(train_t[valid], train_mlcw[valid])
    return intercept + slope * holdout_t


# ── Seasonal prediction ───────────────────────────────────────────────────────

def _build_seasonal_term(holdout_dates: pd.DatetimeIndex,
                          insar_harmonic_ts: pd.DataFrame,
                          r1: float, dphi1_days: float) -> np.ndarray:
    """
    Seasonal Tier 2 addend:  r1 × A1_x_seasonal_aligned(t) × phase_shift
    Simplified form: align insar_harmonic_ts to holdout dates, scale by r1,
    and apply phase shift by circularly shifting the annual model.

    Returns array of same length as holdout_dates, or zeros if alignment fails.
    """
    if np.isnan(r1) or np.isnan(dphi1_days):
        return np.zeros(len(holdout_dates))

    # Align insar harmonic timeseries to holdout epoch dates
    ts = insar_harmonic_ts.copy()
    ts['datetime'] = pd.to_datetime(ts['datetime'])
    ts = ts.sort_values('datetime').set_index('datetime')

    # Match each holdout date to nearest insar harmonic epoch (tolerance 8 days)
    holdout_ser = pd.Series(np.nan, index=holdout_dates)
    for d in holdout_dates:
        candidates = ts.index[abs(ts.index - d) <= pd.Timedelta('8D')]
        if len(candidates) > 0:
            nearest = candidates[np.argmin(abs(candidates - d))]
            holdout_ser[d] = float(ts.loc[nearest, 'A1_x_annual_model'])

    # Phase-shift the annual model by dphi1_days
    ANNUAL_T = 365.25
    omega = 2 * np.pi / ANNUAL_T
    holdout_dti = pd.DatetimeIndex(holdout_dates)
    insar_model = holdout_ser.values.astype(float)

    # Compute amplitude from the aligned signal (sqrt of mean square)
    A1_x = float(np.sqrt(np.nanmean(insar_model**2)) * np.sqrt(2))  # RMS → amplitude

    dphi1_rad = dphi1_days / ANNUAL_T * 2 * np.pi
    t_full = (holdout_dti - pd.Timestamp('2015-01-01')).days.astype(float)
    seasonal = r1 * A1_x * np.sin(omega * t_full + dphi1_rad)

    return np.where(np.isnan(holdout_ser.values), np.nan, seasonal)


# ── Main walk-forward loop ────────────────────────────────────────────────────

def run_walkforward(
    station: str,
    insar_series: pd.Series,
    mlcw_grouped: pd.DataFrame,
    metrics_df: pd.DataFrame,
    peryear_df: pd.DataFrame,
    fold_years: list[int],
    insar_harmonic_ts: pd.DataFrame = None,
) -> pd.DataFrame:
    """
    Walk-forward validation for all layers at one station.

    Parameters
    ----------
    insar_series     : pd.Series, datetime-indexed, values in mm
    mlcw_grouped     : pd.DataFrame with datetime + layer columns
    metrics_df       : reconstruction_metrics.csv (for seasonal_applied flag only —
                       NOT for fbar; fbar is re-estimated per fold)
    peryear_df       : step3_peryear_harmonic_stability.csv (for r1_k per training year)
    fold_years       : list of hold-out years, e.g. [2022, 2023, 2024, 2025]
    insar_harmonic_ts: insar_harmonic_timeseries.feather (for Tier 2 seasonal; None = Tier 1 only)

    Returns
    -------
    tuple of (summary_df, epoch_df) where summary_df has columns:
        station, layer, fold_year,
        RMSE_tier1, RMSE_tier2,
        RMSE_persistence, RMSE_trend_extrap,
        skill_tier1_vs_persistence, skill_tier1_vs_trend,
        skill_tier2_vs_persistence, skill_tier2_vs_trend,
        fbar_per_fold, r1_per_fold, tau_opt_per_fold, alpha_per_fold, detrended_corr,
        n_holdout_epochs, is_fold1, tier2_available
    and epoch_df has additional columns: datetime, mlcw_obs, insar_mm,
        tier1_pred, tier2_pred, persistence, trend_extrap, tau_opt, alpha, det_corr
    """
    # Build layer list from MLCW data
    layer_cols = [c for c in mlcw_grouped.columns if c != 'datetime']
    if not layer_cols:
        return pd.DataFrame()

    # Align InSAR to MLCW timeline
    insar_df = insar_series.reset_index()
    insar_df.columns = ['datetime', 'insar_mm']
    merged = pd.merge_asof(
        mlcw_grouped.sort_values('datetime'),
        insar_df.sort_values('datetime'),
        on='datetime', direction='nearest', tolerance=pd.Timedelta('10D')
    ).sort_values('datetime').reset_index(drop=True)

    if merged.empty or 'insar_mm' not in merged.columns:
        return pd.DataFrame()

    dates = pd.to_datetime(merged['datetime'])
    t_ref = dates.iloc[0]
    t_days_arr = (dates - t_ref).dt.days.values.astype(float)

    # Build seasonal_applied lookup from metrics_df (gate-corrected in Day 1)
    seas_applied = {}
    if metrics_df is not None and not metrics_df.empty:
        for _, row in metrics_df.iterrows():
            seas_applied[str(row['layer'])] = bool(row.get('seasonal_applied', False))

    rows = []
    epoch_rows = []

    for fold_year in fold_years:
        train_mask = dates.dt.year < fold_year
        hold_mask  = dates.dt.year == fold_year

        if train_mask.sum() < 50 or hold_mask.sum() < 5:
            continue

        train_years = sorted(dates[train_mask].dt.year.unique().tolist())
        holdout_dates = dates[hold_mask]
        t_train = t_days_arr[train_mask.values]
        t_hold  = t_days_arr[hold_mask.values]
        insar_train = merged['insar_mm'].values[train_mask.values]
        insar_hold  = merged['insar_mm'].values[hold_mask.values]
        insar_last_train = float(insar_train[~np.isnan(insar_train)][-1])

        for layer in layer_cols:
            if layer not in merged.columns:
                continue
            mlcw_all   = merged[layer].values.astype(float)
            mlcw_train = mlcw_all[train_mask.values]
            mlcw_hold  = mlcw_all[hold_mask.values]

            if np.all(np.isnan(mlcw_hold)):
                continue

            # Per-fold fbar (training window only — no leakage)
            fbar, anchor_mlcw, anchor_insar = compute_fbar_station(mlcw_train, insar_train)
            if np.isnan(fbar):
                continue

            # ── Detrended + lag-aware Tier 1 ─────────────────────────────────
            # 1. Detrend MLCW and InSAR on training window (4-param)
            # 2. Search τ on detrended residuals
            # 3. Compute detrended hold-out InSAR = raw − extrapolated trend
            # 4. Apply lag τ and scale by α
            # Fallback: if |r| < MIN_DETRENDED_R → α=0, τ=0 (trend-only)

            valid_det = ~np.isnan(mlcw_train) & ~np.isnan(insar_train)
            detrend_fallback = True
            tau_opt = 0
            alpha = 0.0
            det_corr = 0.0
            trend_coef_insar = None

            if valid_det.sum() >= 20:
                t_det_train = t_train[valid_det]
                mlcw_det_train, _, _ = detrend_signal(t_det_train, mlcw_train[valid_det])
                insar_det_train, trend_coef_insar, _ = detrend_signal(
                    t_det_train, insar_train[valid_det]
                )

                if not np.all(np.isnan(mlcw_det_train)) and not np.all(np.isnan(insar_det_train)):
                    tau_opt, det_corr, alpha = grid_search_tau_insar(
                        mlcw_det_train, insar_det_train, TAU_MAX_INSAR
                    )
                    if det_corr >= MIN_DETRENDED_R and alpha >= 0:
                        detrend_fallback = False

            if detrend_fallback:
                tau_opt = 0
                alpha = 0.0
                det_corr = 0.0

            # Detrended hold-out InSAR (extrapolate training trend, no look-ahead)
            if not detrend_fallback and trend_coef_insar is not None:
                insar_trend_hold = reconstruct_trend(trend_coef_insar, t_hold)
                insar_det_hold = insar_hold - insar_trend_hold
            else:
                insar_det_hold = np.zeros_like(insar_hold)

            # Apply lag τ: use last τ training-context values of detrended InSAR
            if tau_opt > 0 and not detrend_fallback and trend_coef_insar is not None:
                insar_det_train_full = (
                    insar_train - reconstruct_trend(trend_coef_insar, t_train)
                )
                context = insar_det_train_full[-tau_opt:]
                full_det = np.concatenate([context, insar_det_hold])
                insar_det_lagged = full_det[:len(insar_det_hold)]
            else:
                insar_det_lagged = insar_det_hold

            # Trend component (unchanged from original Tier 1)
            trend_component = anchor_mlcw + fbar * (insar_hold - anchor_insar)

            # Tier 1: trend + lagged detrended coupling
            tier1 = trend_component + alpha * insar_det_lagged

            # Per-fold seasonal params (training years only)
            has_seas = seas_applied.get(layer, False)
            tier2 = tier1.copy()
            r1_fold = np.nan
            tier2_available = False

            if has_seas and insar_harmonic_ts is not None:
                r1, dphi1 = compute_seasonal_params_station(peryear_df, train_years, layer)
                if not (np.isnan(r1) or np.isnan(dphi1)):
                    seasonal_term = _build_seasonal_term(
                        holdout_dates.reset_index(drop=True),
                        insar_harmonic_ts, r1, dphi1
                    )
                    if not np.all(np.isnan(seasonal_term)):
                        tier2 = tier1 + seasonal_term
                        r1_fold = r1
                        tier2_available = True

            # Baselines
            persist  = _persistence_baseline(fbar, anchor_mlcw, anchor_insar,
                                             insar_last_train, len(mlcw_hold))
            trend_ex = _trend_extrap_baseline(mlcw_train, t_train, t_hold)

            def rmse(pred, obs):
                v = ~np.isnan(pred) & ~np.isnan(obs)
                return float(np.sqrt(np.mean((pred[v] - obs[v])**2))) if v.sum() > 0 else np.nan

            def skill(rmse_pred, rmse_base):
                if np.isnan(rmse_pred) or np.isnan(rmse_base) or rmse_base < 1e-9:
                    return np.nan
                return float(1.0 - rmse_pred / rmse_base)

            r_t1 = rmse(tier1, mlcw_hold)
            r_t2 = rmse(tier2, mlcw_hold)
            r_ps = rmse(persist, mlcw_hold)
            r_tr = rmse(trend_ex, mlcw_hold)

            # Per-epoch time series (for figures and diagnostics)
            for k, d in enumerate(holdout_dates.values):
                epoch_rows.append({
                    'station':       station,
                    'layer':         layer,
                    'fold_year':     fold_year,
                    'datetime':      pd.Timestamp(d),
                    'mlcw_obs':      float(mlcw_hold[k]),
                    'insar_mm':      float(insar_hold[k]),
                    'tier1_pred':    float(tier1[k]),
                    'tier2_pred':    float(tier2[k]),
                    'persistence':   float(persist[k]),
                    'trend_extrap':  float(trend_ex[k]) if not np.isnan(trend_ex[k]) else np.nan,
                    'is_fold1':      (fold_year == fold_years[0]),
                    'tier2_available': tier2_available,
                    'tau_opt':       tau_opt,
                    'alpha':         round(alpha, 6),
                    'det_corr':      round(det_corr, 4),
                })

            rows.append({
                'station':                    station,
                'layer':                      layer,
                'fold_year':                  fold_year,
                'RMSE_tier1':                 round(r_t1, 4) if not np.isnan(r_t1) else np.nan,
                'RMSE_tier2':                 round(r_t2, 4) if not np.isnan(r_t2) else np.nan,
                'RMSE_persistence':           round(r_ps, 4) if not np.isnan(r_ps) else np.nan,
                'RMSE_trend_extrap':          round(r_tr, 4) if not np.isnan(r_tr) else np.nan,
                'skill_tier1_vs_persistence': round(skill(r_t1, r_ps), 4),
                'skill_tier1_vs_trend':       round(skill(r_t1, r_tr), 4),
                'skill_tier2_vs_persistence': round(skill(r_t2, r_ps), 4),
                'skill_tier2_vs_trend':       round(skill(r_t2, r_tr), 4),
                'fbar_per_fold':              round(fbar, 5),
                'r1_per_fold':                round(r1_fold, 4) if not np.isnan(r1_fold) else np.nan,
                'tau_opt_per_fold':           tau_opt,
                'alpha_per_fold':             round(alpha, 6) if not np.isnan(alpha) else np.nan,
                'detrended_corr':             round(det_corr, 4) if not np.isnan(det_corr) else np.nan,
                'n_holdout_epochs':           int(hold_mask.sum()),
                'is_fold1':                   (fold_year == fold_years[0]),
                'tier2_available':            tier2_available,
            })

    return pd.DataFrame(rows), pd.DataFrame(epoch_rows)
