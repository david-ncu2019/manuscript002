"""
ihmf_model_v3.py — Joint constrained least-squares solver for IHM-F v3.

Physics: GWL is the only per-layer driver. InSAR is the total surface target.
No b_k or beta_k*x term anywhere.

Model:
    Step 1  Δb_j(t) = S_j · ΔH_j(t − τ_j)           [per layer, MLCW target]
    Step 2  α · Δd_v(t) = Σ_j Δb_j(t)                [total, InSAR target]

Joint solve (fixed τ):
    θ = [S_ke_1, S_kv_1, ..., S_ke_N, S_kv_N, β]   β = 1/α
    Design matrix A:
      MLCW rows: pin each S_j from Δb_j observations
      InSAR rows: pin β from Δd_v observations
    Bounds: all S_j ≥ 0, β ≥ 1
    Solver: scipy.optimize.lsq_linear

τ rule: τ is always a non-negative integer (epochs). Never passed to a
continuous solver. Epoch = 5 days (MLCW cadence); τ=1 ≈ 5 days,
τ=120 = 600 days.

Seasonal aliasing fix: τ grid search operates on anomaly signals — the
climatological month mean is removed from inc_dH and inc_db before searching.
This prevents the annual GWL cycle (autocorr r≈0.8 at τ=24,48) from masking
genuine short-lag hydraulic responses. The full (non-anomaly) incremental
signals are used in the joint solve for parameter estimation.

Public API:
    remove_seasonal_cycle(signal, dates) -> (anomaly, monthly_means)
    tau_grid_search_per_layer(dH, db, regime_mask, tau_max, dates) -> (tau_opt, rss_curve)
    build_regime_mask(head_m, h_c_head_m) -> (elastic_mask, inelastic_mask)
    joint_solve_fixed_tau(layer_data, insar_mm, lam) -> result_dict
    run_walk_forward_v3(layer_dfs, layer_metas, insar_mm, tau_max, fold_years) -> list[dict]
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import lsq_linear, nnls

from ihmf_detrend import detrend_signal


# ── Seasonal cycle removal ────────────────────────────────────────────────────

def remove_seasonal_cycle(
    signal: np.ndarray,
    dates: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Remove the climatological calendar-month mean from an incremental signal.

    For each of the 12 calendar months, computes the mean of all epochs in that
    month across all years in the training window, then subtracts it. The result
    (anomaly) retains inter-annual variability and genuine hydraulic responses
    while removing the annual GWL/MLCW recharge cycle.

    This is applied only for the τ grid search. The joint parameter solve uses
    the original (non-anomaly) incremental signals so that S_k values retain
    their physical units.

    Parameters
    ----------
    signal : 1-D float array, shape (T,)
        Incremental signal (np.diff of a cumulative series).
    dates : array-like of datetime64, shape (T,)
        Epoch dates corresponding to signal[t]. Must be the same length as signal
        (i.e. dates[t] is the date at which the increment signal[t] was measured).

    Returns
    -------
    anomaly : 1-D float array, shape (T,)
        signal minus its climatological monthly mean. Mean of anomaly ≈ 0.
    monthly_means : 1-D float array, shape (12,)
        Mean value per calendar month (index 0 = January). Used in walk-forward
        to subtract training-window climatology from the test window.
    """
    months = pd.DatetimeIndex(dates).month   # 1..12
    monthly_means = np.zeros(12)
    for m in range(1, 13):
        mask = months == m
        if mask.sum() > 0:
            monthly_means[m - 1] = signal[mask].mean()

    anomaly = signal.copy()
    for m in range(1, 13):
        mask = months == m
        anomaly[mask] -= monthly_means[m - 1]

    return anomaly, monthly_means


def apply_seasonal_removal(
    signal: np.ndarray,
    dates: np.ndarray,
    monthly_means: np.ndarray,
) -> np.ndarray:
    """
    Subtract a pre-computed monthly climatology (from training window) from signal.

    Used in walk-forward validation to remove the training-window seasonal cycle
    from the test window without look-ahead contamination.

    Parameters
    ----------
    signal : 1-D float array, shape (T,)
    dates  : datetime64 array, shape (T,)
    monthly_means : float array, shape (12,) — from remove_seasonal_cycle on train window

    Returns
    -------
    anomaly : 1-D float array, shape (T,)
    """
    months = pd.DatetimeIndex(dates).month
    anomaly = signal.copy()
    for m in range(1, 13):
        mask = months == m
        anomaly[mask] -= monthly_means[m - 1]
    return anomaly


# ── Regime mask ───────────────────────────────────────────────────────────────

def build_regime_mask(
    head_m: np.ndarray,
    h_c_head_m: float,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Return boolean masks for elastic and inelastic epochs.

    Uses running-minimum preconsolidation memory (Riley 1969):
      running_min[t] = min(h_c, head_m[0], ..., head_m[t-1])
      Inelastic: head_m[t] < running_min[t]  (virgin consolidation — new drawdown)
      Elastic:   head_m[t] >= running_min[t] (recovery or stable above running min)

    This matches 12_stress_strain_per_layer.py (dV < 0 criterion).
    Both masks have the same length as head_m.
    An epoch is elastic OR inelastic — never both.
    """
    n = len(head_m)
    running_min = np.full(n, h_c_head_m, dtype=float)
    for t in range(1, n):
        running_min[t] = min(running_min[t - 1], head_m[t - 1])
    inelastic = head_m < running_min
    elastic   = ~inelastic
    return elastic.astype(bool), inelastic.astype(bool)


# ── Per-layer τ grid search ───────────────────────────────────────────────────

def tau_grid_search_per_layer(
    dH: np.ndarray,
    db: np.ndarray,
    elastic_mask: np.ndarray,
    inelastic_mask: np.ndarray,
    tau_max: int = 120,
    dates: np.ndarray | None = None,
) -> tuple[int, list[float], np.ndarray]:
    """
    Find the integer lag τ ∈ {0, …, tau_max} that minimises RSS for a single layer.

    Operates on INCREMENTAL signals (first differences). The physics equation
    Δb_j(t) = S_j · ΔH_j(t−τ) is defined in incremental form — not cumulative.
    Caller must pass np.diff(cumulative_signal) arrays, not the raw cumulative arrays.

    For each τ, fits S_ke and S_kv independently via scalar OLS:
        S_ke = (dH_e · db_e) / (dH_e · dH_e)   over elastic epochs
        S_kv = (dH_i · db_i) / (dH_i · dH_i)   over inelastic epochs
    Then computes RSS = ||db - (S_ke*dH_e + S_kv*dH_i)||²

    Parameters
    ----------
    dH : 1-D float array, shape (T,)
        Incremental GWL change: np.diff(head_m). Units: m per epoch.
    db : 1-D float array, shape (T,)
        Incremental MLCW compaction: np.diff(mlcw_mm). Units: mm per epoch.
    elastic_mask, inelastic_mask : bool arrays, shape (T,)
        From build_regime_mask, evaluated on the SAME incremental-length array.
    tau_max : int
        Maximum lag to search. At monthly cadence (InSAR grid), 24 = 2 years.
    dates : datetime64 array, shape (T,) or None
        Epoch dates for dH/db. When provided, the climatological calendar-month
        mean is removed from both signals before RSS computation, preventing the
        annual GWL recharge cycle from masking genuine short hydraulic lags.
        When None, raw incremental signals are used (no seasonal removal).

    Returns
    -------
    tau_opt : int
        Lag with minimum RSS. Always an integer.
    rss_curve : list of float, length tau_max+1
        RSS at each candidate τ ∈ {0, …, tau_max}.
    monthly_means_dH : 1-D float array, shape (12,)
        Climatological monthly means of dH used for seasonal removal.
        All zeros if dates is None.
    """
    # Remove seasonal cycle from both signals before τ search
    if dates is not None:
        dH_anom, monthly_means_dH = remove_seasonal_cycle(dH, dates)
        db_anom, _                = remove_seasonal_cycle(db, dates)
    else:
        dH_anom = dH
        db_anom = db
        monthly_means_dH = np.zeros(12)

    T = len(dH_anom)
    rss_curve: list[float] = []

    for tau in range(tau_max + 1):
        n = T - tau
        if n < 4:
            rss_curve.append(np.inf)
            continue

        # Head at epoch j drives compaction at epoch j+tau (head leads by tau).
        dH_lag  = dH_anom[:n]         # GWL driver epochs 0..n-1
        db_trim = db_anom[tau:]       # compaction response epochs tau..T-1
        e_trim  = elastic_mask[:n]   # regime mask uses lagged (driver-time) head so classification is lag-consistent
        i_trim  = inelastic_mask[:n]

        db_pred = np.zeros(n)

        # Elastic component
        dH_e = dH_lag[e_trim]
        db_e = db_trim[e_trim]
        if len(dH_e) >= 2 and np.dot(dH_e, dH_e) > 0:
            S_ke = max(0.0, np.dot(dH_e, db_e) / np.dot(dH_e, dH_e))
            db_pred[e_trim] = S_ke * dH_e

        # Inelastic component
        dH_i = dH_lag[i_trim]
        db_i = db_trim[i_trim]
        if len(dH_i) >= 2 and np.dot(dH_i, dH_i) > 0:
            S_kv = max(0.0, np.dot(dH_i, db_i) / np.dot(dH_i, dH_i))
            db_pred[i_trim] = S_kv * dH_i

        mse = float(np.mean((db_trim - db_pred) ** 2))   # MSE not RSS — prevents sample-size bias
        rss_curve.append(mse)

    tau_opt = int(np.argmin(rss_curve))
    return tau_opt, rss_curve, monthly_means_dH


# ── Cumulative-domain solver (2026-06-08: replaces incremental lsq_linear with ──
# ── memory-based two-regressor NNLS per Script 12) ──────────────────────────

def compute_virgin_term(H_series: np.ndarray, h_c: float) -> np.ndarray:
    """
    Compute the virgin (inelastic exceedance) term V(t).

    V(t) = min(0, cummin(H(t)) - h_c)

    V(t) is zero until head crosses below the preconsolidation threshold h_c
    for the first time, then tracks how far head has penetrated permanently
    into the inelastic regime.  When head recovers, V(t) stays at the
    historical minimum — it never decreases.  This term carries the
    preconsolidation stress memory that the incremental formulation loses.

    Parameters
    ----------
    H_series : 1-D float array, cumulative head (m, zero-referenced to REF_DATE)
    h_c : float, preconsolidation head (m, zero-referenced to REF_DATE — same frame as H_series)

    Returns
    -------
    V : 1-D float array, same length as H_series
        ≤ 0 always.  0 = fully elastic.  Negative = inelastic exceedance.
    """
    H_series = np.asarray(H_series, dtype=float)
    cummin_H = np.minimum.accumulate(H_series)
    V = np.minimum(0.0, cummin_H - h_c)
    return V


def fit_two_regressor_nnls_X(
    H_arr: np.ndarray,
    V_arr: np.ndarray,
    b_arr: np.ndarray,
    with_intercept: bool = True,
) -> tuple:
    """
    Fit b = c + S_ke * H + delta * V  where delta = S_kv - S_ke ≥ 0.

    Uses NNLS on the negated system because all signals in the compacting
    domain are negative: H ≤ 0, V ≤ 0, b ≤ 0.  Negating both sides makes
    the design matrix and rhs non-negative, satisfying NNLS requirements.

        -b = S_ke * (-H) + delta * (-V)
        A  = [-H, -V]    (both cols ≥ 0)
        rhs = -b          (≥ 0)
        NNLS(A, rhs) → [S_ke, delta]

    The constraint delta ≥ 0 is enforced structurally by NNLS, which
    guarantees S_kv = S_ke + delta ≥ S_ke (inelastic ≥ elastic storage).

    Intercept via centering (Frisch-Waugh-Lovell for NNLS):
      When with_intercept=True, the data are demeaned before NNLS to remove
      the intercept, then the intercept is recovered from the means:
        c = b̄ - S_ke·H̄ - delta·V̄.
      This is equivalent to adding an unconstrained intercept column while
      keeping the non-negativity bounds on S_ke and delta.

    Parameters
    ----------
    H_arr : 1-D float array, cumulative head (m, zero-referenced)
    V_arr : 1-D float array, virgin term (m, ≤ 0)
    b_arr : 1-D float array, cumulative compaction (mm, ≤ 0)
    with_intercept : bool
        If True (default), add a per-layer intercept via data centering.

    Returns
    -------
    S_ke : float, elastic skeletal storage coefficient (mm/m)
    S_kv : float, inelastic skeletal storage coefficient (mm/m)
    delta : float, S_kv - S_ke (≥ 0)
    c : float, intercept (mm; 0 if with_intercept=False)
    residual_sq : float, sum of squared residuals
    b_pred : 1-D float array, predicted cumulative compaction (mm)
    """
    H_arr = np.asarray(H_arr, dtype=float)
    V_arr = np.asarray(V_arr, dtype=float)
    b_arr = np.asarray(b_arr, dtype=float)

    if with_intercept:
        # Demean to remove intercept from NNLS
        H_mean = float(np.mean(H_arr))
        V_mean = float(np.mean(V_arr))
        b_mean = float(np.mean(b_arr))
        H_ctr = H_arr - H_mean
        V_ctr = V_arr - V_mean
        b_ctr = b_arr - b_mean

        # NNLS on centered data: -b̃ = S_ke·(-H̃) + delta·(-Ṽ)
        A   = np.column_stack([-H_ctr, -V_ctr])
        rhs = -b_ctr
        coef, residual_sq = nnls(A, rhs)
        S_ke  = float(coef[0])
        delta = float(coef[1])
        S_kv  = S_ke + delta

        # Recover intercept from means
        c = b_mean - S_ke * H_mean - delta * V_mean

        # Predicted values (on original, un-centered scale)
        b_pred = c + S_ke * H_arr + delta * V_arr
        return S_ke, S_kv, delta, c, float(residual_sq), b_pred
    else:
        A   = np.column_stack([-H_arr, -V_arr])
        rhs = -b_arr
        coef, residual_sq = nnls(A, rhs)
        S_ke  = float(coef[0])
        delta = float(coef[1])
        S_kv  = S_ke + delta

        b_pred = S_ke * H_arr + delta * V_arr
        return S_ke, S_kv, delta, 0.0, float(residual_sq), b_pred


def compute_r2_cumulative(obs: np.ndarray, pred: np.ndarray) -> float:
    """R² on cumulative quantities (obs vs pred). NaN-safe."""
    obs = np.asarray(obs, dtype=float)
    pred = np.asarray(pred, dtype=float)
    mask = np.isfinite(obs) & np.isfinite(pred)
    if mask.sum() < 2:
        return float("nan")
    ss_res = float(np.sum((obs[mask] - pred[mask]) ** 2))
    ss_tot = float(np.sum((obs[mask] - obs[mask].mean()) ** 2))
    if ss_tot == 0:
        return float("nan")
    return float(1.0 - ss_res / ss_tot)


# ── Joint solve (cumulative domain — active) ──────────────────────────────────

def joint_solve_cumulative(
    layer_data: dict[str, dict],
    insar_mm: np.ndarray,
    lam: float | None = None,
    alpha_external: float | None = None,
) -> dict:
    """
    Two-step cumulative-domain solve with preconsolidation memory.

    Step 1 — Per-layer two-regressor NNLS on cumulative H and V:
        b_j(t) = S_ke_j · H_j(t−τ_j) + (S_kv_j − S_ke_j) · V_j(t)

        V_j(t) = min(0, cummin(H_j(t−τ_j)) − h_c_j)

        The V term carries the permanent inelastic strain memory —
        it never decreases, even when head recovers.  No regime mask
        is needed in the design matrix; NNLS automatically separates
        elastic (S_ke · H) from inelastic (delta · V) coefficients.

    Step 2 — Surface alignment (same as incremental solver):
        α · insar(t) + c = Σ_j b_j(t)

        When alpha_external is provided, Step 2 OLS is bypassed.

    Parameters
    ----------
    layer_data : dict[layer_code -> dict]
        Each entry must have:
          'H_lagged'     : 1-D float array, cumulative head lagged by τ (m, zero-referenced to REF_DATE)
          'b_cum'        : 1-D float array, cumulative MLCW compaction (mm)
          'h_c_head_m'   : float, preconsolidation head (m, zero-referenced — same frame as H_lagged)
          'tau_opt'      : int, optimal lag in epochs
    insar_mm : 1-D float array
        Cumulative InSAR/GPS displacement (mm).  May contain NaN for
        pre-GPS epochs.
    lam : float or None
        Accepted for API compatibility; not used in this formulation.
    alpha_external : float or None
        When set, use this α directly instead of OLS fitting.

    Returns
    -------
    dict with keys: layers, alpha, beta, c_intercept,
        rmse_mlcw_cum, rmse_insar, r2_insar, T
    """
    layers = list(layer_data.keys())
    T = min(len(d["H_lagged"]) for d in layer_data.values())

    # ── Step 1: Per-layer cumulative NNLS ──────────────────────────────────
    layer_params: dict[str, dict] = {}
    b_pred_all = np.zeros(T)

    for layer in layers:
        d      = layer_data[layer]
        H      = d["H_lagged"][:T]
        b      = d["b_cum"][:T]
        h_c    = d["h_c_head_m"]
        tau    = d.get("tau_opt", 0)

        # Compute virgin term from cumulative lagged head
        V = compute_virgin_term(H, h_c)

        # Fit two-regressor NNLS: b = c + S_ke * H + (S_kv - S_ke) * V
        S_ke, S_kv, delta, c_j, resid_sq, b_pred_j = fit_two_regressor_nnls_X(
            H, V, b, with_intercept=True
        )

        n_elastic   = int((V == 0).sum())
        n_inelastic = int((V < 0).sum())
        r2_cum = compute_r2_cumulative(b, b_pred_j)

        collinearity_flag = bool(n_elastic < 10)
        if collinearity_flag:
            print(f"  [collinearity] Layer {layer}: n_elastic={n_elastic} < 10 — "
                  f"elastic regime unidentifiable; S_ke result unreliable")

        layer_params[layer] = {
            "S_ke": S_ke, "S_kv": S_kv, "delta": delta,
            "c_intercept": c_j,
            "tau_opt": tau,
            "n_elastic": n_elastic, "n_inelastic": n_inelastic,
            "r2_cum": r2_cum,
            "collinearity_flag": collinearity_flag,
        }

        b_pred_all += b_pred_j

    # ── RMSE_MLCW (cumulative, mm, with per-layer intercept) ────────────────
    mlcw_resid_sq: list[float] = []
    for layer in layers:
        d      = layer_data[layer]
        b      = d["b_cum"][:T]
        S_ke   = layer_params[layer]["S_ke"]
        S_kv   = layer_params[layer]["S_kv"]
        c_j    = layer_params[layer].get("c_intercept", 0.0)
        H      = d["H_lagged"][:T]
        V      = compute_virgin_term(H, d["h_c_head_m"])
        b_pred_j = c_j + S_ke * H + (S_kv - S_ke) * V
        mlcw_resid_sq.extend((b - b_pred_j) ** 2)
    rmse_mlcw_cum = float(np.sqrt(np.mean(mlcw_resid_sq))) if mlcw_resid_sq else float("nan")

    # Per-layer R²_cum is reported per layer (not pooled — pooled metric is
    # misleading because layers with larger magnitude dominate the concatenation).

    # ── Step 2: Surface alignment (cumulative — prediction already cumulative) ─
    cum_insar = insar_mm[:T]  # already cumulative (no cumsum needed)
    cum_pred  = b_pred_all     # already cumulative (no cumsum needed)

    if alpha_external is not None:
        alpha = float(alpha_external)
        beta  = 1.0 / alpha if alpha > 0 else float("inf")
        finite = np.isfinite(cum_insar)
        if finite.sum() > 0:
            c_intercept = float(np.mean(cum_pred[finite] - alpha * cum_insar[finite]))
        else:
            c_intercept = 0.0
    else:
        finite = np.isfinite(cum_insar)
        if finite.sum() < 10:
            alpha = float("nan")
            beta  = float("nan")
            c_intercept = 0.0
            print("  [joint_solve_cumulative] WARNING: < 10 finite GPS epochs — α set to NaN")
        else:
            A_step2   = np.column_stack([cum_insar[finite], np.ones(finite.sum())])
            coeffs, _, _, _ = np.linalg.lstsq(A_step2, cum_pred[finite], rcond=None)
            alpha = float(np.clip(coeffs[0], 1e-6, 1.0))
            beta  = 1.0 / alpha
            c_intercept = float(coeffs[1])

    # R²_insar diagnostic (on finite insar epochs)
    finite_insar = np.isfinite(cum_insar)
    n_finite = int(finite_insar.sum())
    if n_finite > 1 and not np.isnan(alpha):
        insar_pred  = np.full(T, np.nan)
        insar_pred[finite_insar] = (cum_pred[finite_insar] - c_intercept) / alpha
        insar_resid = np.where(finite_insar, cum_insar - insar_pred, np.nan)
        ss_res = float(np.nansum(insar_resid ** 2))
        ss_tot = float(np.nansum((cum_insar[finite_insar] - np.nanmean(cum_insar)) ** 2))
        rmse_insar = float(np.sqrt(np.nanmean(insar_resid ** 2)))
        r2_insar = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else np.nan
    else:
        rmse_insar = float("nan")
        r2_insar  = float("nan")

    return {
        "layers":         layer_params,
        "alpha":          alpha,
        "beta":           beta,
        "c_intercept":    c_intercept,
        "rmse_mlcw_cum":  rmse_mlcw_cum,
        "rmse_insar":     rmse_insar,
        "r2_insar":       r2_insar,
        "T":              T,
        "lam":            None,
        "solver":         "cumulative_nnls",
    }


# ── Joint solve (incremental domain — legacy, deprecated 2026-06-08) ──────────

def joint_solve_fixed_tau(
    layer_data: dict[str, dict],
    insar_mm: np.ndarray,
    lam: float | None = None,
    alpha_external: float | None = None,
) -> dict:
    """
    Two-step solve following physics_rules_research_problem.md:

    Step 1 — Fit S_ke_j, S_kv_j from MLCW increments only (no InSAR).
      Per layer j: lsq_linear on [dH_elastic, dH_inelastic] → [S_ke_j, S_kv_j]
      Bounds: S_ke_j ≥ 0, S_kv_j ≥ 0.

    Step 2 — Fit α from cumulative InSAR given fixed S_j (simple scalar OLS).
      cumsum(Σ_j db_pred_j) = α · cumsum(insar)
      α = dot(cum_sum_pred, cum_insar) / dot(cum_insar, cum_insar)
      Clamped to (0, 1].

      When alpha_external is provided, Step 2 OLS is bypassed — α is set to
      alpha_external directly and only the intercept c is fitted.

    The lam parameter is accepted for API compatibility but not used in this
    two-step formulation.

    Parameters
    ----------
    layer_data : dict[layer_code -> dict]
        Each entry must have:
          'dH_lagged'     : 1-D float array, shape (T,)
          'db'            : 1-D float array, shape (T,)
          'elastic_mask'  : bool array, shape (T,)
          'inelastic_mask': bool array, shape (T,)
    insar_mm : 1-D float array
        Incremental InSAR/GPS (np.diff of cumulative). Cumsum applied inside.
        May contain NaN for pre-GPS epochs — handled when alpha_external is set.
    alpha_external : float or None
        When not None, use this fixed α value instead of fitting via OLS.
        Used in GPS mode where the 2003-2010 pre-GPS era has no calibration
        signal and the elastic-only OLS gives a physically wrong α ≈ 0.034.

    Returns
    -------
    dict with keys: layers, alpha, beta, c_intercept, rmse_mlcw, rmse_insar, r2_insar
    """
    layers = list(layer_data.keys())
    N = len(layers)
    T = min(len(d["dH_lagged"]) for d in layer_data.values())
    insar_trim = insar_mm[:T]
    cum_insar  = np.cumsum(insar_trim)

    # ── Step 1: Fit S_ke_j, S_kv_j per layer from MLCW increments only ──────
    layer_params: dict[str, dict] = {}
    db_pred_all = np.zeros(T)

    for layer in layers:
        d   = layer_data[layer]
        dH  = d["dH_lagged"][:T]
        db  = d["db"][:T]
        e_m = d["elastic_mask"][:T]
        i_m = d["inelastic_mask"][:T]
        tau = d.get("tau_opt", 0)

        # Build 2-column design: [dH_elastic, dH_inelastic]
        A_l = np.column_stack([
            np.where(e_m, dH, 0.0),
            np.where(i_m, dH, 0.0),
        ])
        # lsq_linear with S_ke >= 0, S_kv >= 0.
        # No upper cap: the fitted parameters are LUMPED (mm compaction per m head change),
        # not specific storage (m^-1).  The Chiu 2.2e-3 m^-1 literature bound was in
        # specific-storage units; applying it directly to the lumped parameter would be
        # ~4–5 orders of magnitude too small (factor ≈ b_k × 1000).
        res = lsq_linear(A_l, db, bounds=([0.0, 0.0], [np.inf, np.inf]),
                         method="trf", max_iter=1000)
        S_ke = float(res.x[0])
        S_kv = float(res.x[1])
        n_elastic   = int(e_m.sum())
        n_inelastic = int(i_m.sum())
        layer_params[layer] = {
            "S_ke": S_ke, "S_kv": S_kv, "tau_opt": tau,
            "n_elastic": n_elastic, "n_inelastic": n_inelastic,
        }

        db_pred_j = np.where(e_m, S_ke * dH, 0.0) + np.where(i_m, S_kv * dH, 0.0)
        db_pred_all += db_pred_j

    # RMSE MLCW (incremental)
    mlcw_resid_sq: list[float] = []
    for layer in layers:
        d    = layer_data[layer]
        dH   = d["dH_lagged"][:T]
        db   = d["db"][:T]
        e_m  = d["elastic_mask"][:T]
        i_m  = d["inelastic_mask"][:T]
        S_ke = layer_params[layer]["S_ke"]
        S_kv = layer_params[layer]["S_kv"]
        db_pred_j = np.where(e_m, S_ke * dH, 0.0) + np.where(i_m, S_kv * dH, 0.0)
        mlcw_resid_sq.extend((db - db_pred_j) ** 2)
    rmse_mlcw = float(np.sqrt(np.mean(mlcw_resid_sq)))

    # ── Step 2: Fit α from cumulative InSAR (or use external empirical α) ──
    # Fit: α · cum_insar(t) + c = cum_pred(t)
    # c absorbs displacement not driven by GWL layers. α is the scale factor.
    cum_pred  = np.cumsum(db_pred_all)

    if alpha_external is not None:
        # Fixed α from external empirical calibration (e.g. monthly MLCW vs GPS
        # OLS).  Bypasses the elastic-era OLS that produces α ≈ 0.034 when the
        # GPS record starts after the main inelastic consolidation period.
        alpha = float(alpha_external)
        beta  = 1.0 / alpha if alpha > 0 else float("inf")
        # c_intercept: minimise |cum_pred - (α·cum_insar + c)|² on finite insar epochs only
        finite = np.isfinite(cum_insar)
        if finite.sum() > 0:
            c_intercept = float(np.mean(cum_pred[finite] - alpha * cum_insar[finite]))
        else:
            c_intercept = 0.0
    else:
        # Standard OLS: filter to finite insar epochs before fitting.
        # NaN in cum_insar (e.g. pre-GPS era) would crash lstsq.
        finite = np.isfinite(cum_insar)
        if finite.sum() < 10:
            alpha = float("nan")
            beta  = float("nan")
            c_intercept = 0.0
            print("  [joint_solve] WARNING: < 10 finite GPS epochs — α set to NaN")
        else:
            A_step2   = np.column_stack([cum_insar[finite], np.ones(finite.sum())])
            coeffs, _, _, _ = np.linalg.lstsq(A_step2, cum_pred[finite], rcond=None)
            alpha = float(np.clip(coeffs[0], 1e-6, 1.0))
            beta  = 1.0 / alpha
            c_intercept = float(coeffs[1])

    # RMSE and R² in cumulative domain (on finite insar epochs only)
    finite = np.isfinite(cum_insar)
    n_finite = int(finite.sum())
    if n_finite > 1:
        insar_pred  = np.full(T, np.nan)
        insar_pred[finite]  = (cum_pred[finite] - c_intercept) / alpha
        insar_resid = np.where(finite, cum_insar - insar_pred, np.nan)
        ss_res = float(np.nansum(insar_resid ** 2))
        ss_tot = float(np.nansum((cum_insar[finite] - np.nanmean(cum_insar)) ** 2))
        rmse_insar  = float(np.sqrt(np.nanmean(insar_resid ** 2)))
        r2_insar = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else np.nan
    else:
        rmse_insar = float("nan")
        r2_insar  = float("nan")

    return {
        "layers":        layer_params,
        "alpha":         alpha,
        "beta":          beta,
        "c_intercept":   c_intercept,
        "rmse_mlcw":     rmse_mlcw,
        "rmse_insar":    rmse_insar,
        "r2_insar":      r2_insar,
        "T":             T,
        "lam":           None,
    }


# ── Walk-forward validation ───────────────────────────────────────────────────

def run_walk_forward_v3(
    layer_dfs: dict[str, pd.DataFrame],
    layer_metas: dict[str, dict],
    insar_mm: np.ndarray,
    tau_max: int = 120,
    fold_years: list[int] | None = None,
    alpha_external: float | None = None,
) -> list[dict]:
    """
    4-fold expanding walk-forward validation (cumulative domain — R3 fix).

    Each fold:
      1. Split data into train (up to year N) and test (year N+1).
      2. On training window: τ grid search on incremental signals,
         then fit S_ke, S_kv via cumulative NNLS (joint_solve_cumulative).
      3. On test window: predict cumulative compaction using frozen S_k
         parameters, then diff for incremental RMSE comparison.

    R3 (2026-06-09): Switched from deprecated incremental solver
    (joint_solve_fixed_tau) to cumulative solver (joint_solve_cumulative).
    The cumulative solver carries preconsolidation memory through V(t),
    fixing the n_inelastic=0 bug in all walk-forward folds.

    Parameters
    ----------
    layer_dfs : dict[str -> pd.DataFrame]
        From load_all_layers_gps. Each df has datetime, head_m, head_m_zeroed,
        mlcw_mm (cumulative).
    layer_metas : dict[str -> dict]
        Must contain h_c_head_m (absolute), h_c_zeroed (zero-ref), head_ref_m.
    insar_mm : np.ndarray, shape (T,)
        Shared InSAR/GPS incremental timeline (length T-1, np.diff of cumulative).
        May contain NaN for pre-GPS epochs.
    tau_max : int
        Maximum integer lag to search. Default 120.
    fold_years : list[int] or None
        Hold-out years. Default [2022, 2023, 2024, 2025].
    alpha_external : float or None
        When not None, passed to joint_solve_cumulative, bypassing Step 2 OLS.

    Returns
    -------
    list of fold dicts
    """
    if fold_years is None:
        fold_years = [2022, 2023, 2024, 2025]

    layers = list(layer_dfs.keys())
    ref_df = layer_dfs[layers[0]]
    # Use cumulative-axis years for train/test split (R3).
    # Cumulative epoch t = response time; driver = t - τ.
    all_dates_cum = ref_df["datetime"].values
    all_years_cum = pd.to_datetime(all_dates_cum).year
    T_full = len(all_dates_cum)

    fold_results: list[dict] = []

    for fold_idx, test_year in enumerate(fold_years):
        train_cum_mask = all_years_cum < test_year
        test_cum_mask  = all_years_cum == test_year

        n_train_cum = int(train_cum_mask.sum())
        n_test_cum  = int(test_cum_mask.sum())

        if n_train_cum < 10 or n_test_cum < 2:
            fold_results.append({
                "fold": f"Fold{fold_idx+1}_test{test_year}",
                "test_year": test_year,
                "skipped": True,
                "reason": f"train={n_train_cum} test={n_test_cum} cumulative epochs",
            })
            continue

        # ── Per-layer: τ grid search on incremental train window ─────────────
        # τ search uses incremental signals within the training span (R3: unchanged).
        layer_tau_opts: dict[str, int] = {}
        any_valid = False

        for layer in layers:
            df   = layer_dfs[layer]
            meta = layer_metas[layer]

            head_m  = df["head_m"].values          # absolute, for regime mask
            mlcw_mm = df["mlcw_mm"].values         # cumulative
            h_c_abs = meta["h_c_head_m"]           # absolute

            # Incremental signals cover train_cum_mask[1:] (diff across train boundary)
            # Use only epochs fully within training: train_cum_mask[t] & train_cum_mask[t-1]
            inc_train_mask = train_cum_mask[1:] & train_cum_mask[:-1]
            n_inc_train = int(inc_train_mask.sum())

            if n_inc_train < 4:
                continue

            inc_dH = np.diff(head_m)
            inc_db = np.diff(mlcw_mm)
            e_m_full, i_m_full = build_regime_mask(head_m[:-1], h_c_abs)

            inc_dH_train = inc_dH[inc_train_mask]
            inc_db_train = inc_db[inc_train_mask]
            e_m_train    = e_m_full[inc_train_mask]
            i_m_train    = i_m_full[inc_train_mask]
            dates_train  = df["datetime"].values[:-1][inc_train_mask]

            effective_tau_max = min(tau_max, n_inc_train - 4)
            if effective_tau_max < 0:
                continue

            tau_opt, _rss_curve, _monthly = tau_grid_search_per_layer(
                inc_dH_train, inc_db_train, e_m_train, i_m_train, effective_tau_max,
                dates=dates_train
            )
            layer_tau_opts[layer] = tau_opt
            any_valid = True

        if not any_valid:
            fold_results.append({
                "fold": f"Fold{fold_idx+1}_test{test_year}",
                "test_year": test_year,
                "skipped": True,
                "reason": "no valid layers in τ search",
            })
            continue

        # ── Build cumulative training common block ───────────────────────────
        tau_max_train = max(layer_tau_opts.values())
        train_cum_indices = np.where(train_cum_mask)[0]  # cumulative indices in training
        # Common window: start at tau_max_train so every layer's H[t-τ] exists
        common_start = tau_max_train
        common_len   = n_train_cum - common_start

        if common_len < 4:
            fold_results.append({
                "fold": f"Fold{fold_idx+1}_test{test_year}",
                "test_year": test_year,
                "skipped": True,
                "reason": f"cumulative training common window too short ({common_len} epochs)",
            })
            continue

        layer_data_train_cum: dict[str, dict] = {}
        for layer in layers:
            df   = layer_dfs[layer]
            meta = layer_metas[layer]

            H_zeroed = df["head_m_zeroed"].values   # zero-ref cumulative (R1)
            b_cum    = df["mlcw_mm"].values          # cumulative compaction
            h_c_z    = meta["h_c_zeroed"]            # zero-ref preconsolidation (R2)
            tau      = layer_tau_opts[layer]

            # Common-window cumulative indices (response times)
            common_indices = train_cum_indices[common_start: common_start + common_len]
            # Driver indices: response - τ
            driver_indices = common_indices - tau

            H_lag = H_zeroed[driver_indices]
            b_win = b_cum[common_indices]

            n_common = min(len(H_lag), len(b_win))
            layer_data_train_cum[layer] = {
                "H_lagged":   H_lag[:n_common],
                "b_cum":      b_win[:n_common],
                "h_c_head_m": h_c_z,
                "tau_opt":    tau,
            }

        # InSAR cumulative on the same common response indices
        insar_cum_full = np.cumsum(np.nan_to_num(insar_mm, nan=0.0))
        # insar_mm is incremental (length T_full-1); cumsum gives length T_full-1.
        # Pad to match T_full cumulative epochs.
        if len(insar_cum_full) < T_full:
            insar_cum_full = np.concatenate([insar_cum_full, [insar_cum_full[-1]]])
        insar_cum_train_win = insar_cum_full[common_indices][:common_len]

        # ── Fit via cumulative solver (R3: replaces joint_solve_fixed_tau) ──
        train_result = joint_solve_cumulative(layer_data_train_cum, insar_cum_train_win,
                                              alpha_external=alpha_external)
        alpha_train = train_result["alpha"]

        # ── Predict on test window using frozen training S_k (cumulative) ────
        test_cum_indices = np.where(test_cum_mask)[0]
        n_test = len(test_cum_indices)
        if n_test < 2:
            fold_results.append({
                "fold": f"Fold{fold_idx+1}_test{test_year}",
                "test_year": test_year,
                "skipped": True,
                "reason": f"test window too short ({n_test} cumulative epochs)",
            })
            continue

        db_pred_test_all = np.zeros(n_test - 1)  # incremental predictions
        test_layer_params: dict[str, dict] = {}

        for layer in layers:
            df   = layer_dfs[layer]
            meta = layer_metas[layer]

            S_ke = train_result["layers"][layer]["S_ke"]
            S_kv = train_result["layers"][layer]["S_kv"]
            c_j  = train_result["layers"][layer].get("c_intercept", 0.0)
            tau  = layer_tau_opts[layer]

            H_zeroed = df["head_m_zeroed"].values
            b_cum    = df["mlcw_mm"].values
            h_c_z    = meta["h_c_zeroed"]

            # Build cumulative H for test window + τ context
            # Context: τ cumulative epochs before first test index
            context_start = max(0, test_cum_indices[0] - tau)
            context_end   = test_cum_indices[-1]
            all_indices = np.arange(context_start, context_end + 1)

            H_span = H_zeroed[all_indices]
            b_span = b_cum[all_indices]

            # V computed on full span (carries cummin memory from record start)
            V_span = compute_virgin_term(H_span, h_c_z)
            b_pred_span = c_j + S_ke * H_span + (S_kv - S_ke) * V_span

            # Extract test window predictions
            test_start_in_span = test_cum_indices[0] - context_start
            b_pred_test = b_pred_span[test_start_in_span:]
            b_obs_test  = b_span[test_start_in_span:]
            V_test      = V_span[test_start_in_span:]

            # Incremental for RMSE
            db_pred = np.diff(b_pred_test)
            db_obs  = np.diff(b_obs_test)
            n_common_test = min(len(db_pred), len(db_obs), n_test - 1)
            db_pred_test_all[:n_common_test] += db_pred[:n_common_test]

            # Regime counts at driver-time (epoch before response)
            n_elastic   = int((V_test[:-1][:n_common_test] == 0).sum())
            n_inelastic = int((V_test[:-1][:n_common_test] < 0).sum())

            test_layer_params[layer] = {
                "S_ke": S_ke, "S_kv": S_kv,
                "tau_opt": tau,
                "n_elastic":   n_elastic,
                "n_inelastic": n_inelastic,
            }

        # ── InSAR metrics on test window ─────────────────────────────────────
        insar_inc_test = insar_mm[np.where(test_cum_mask[:-1])[0]]  # incremental InSAR
        cum_pred_test  = np.cumsum(db_pred_test_all)
        n_common_test = min(len(insar_inc_test), len(cum_pred_test))

        if not np.isnan(alpha_train) and alpha_train > 0 and n_common_test > 1:
            insar_pred_test  = cum_pred_test[:n_common_test] / alpha_train
            # InSAR test: compare cumulative prediction with cumulative InSAR
            cum_insar_test = np.cumsum(insar_inc_test[:n_common_test])
            insar_resid_test = cum_insar_test - insar_pred_test
            rmse_insar_test  = float(np.sqrt(np.mean(insar_resid_test ** 2)))
            ss_res = float(np.sum(insar_resid_test ** 2))
            ss_tot = float(np.sum((cum_insar_test - cum_insar_test.mean()) ** 2))
            r2_test = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else float("nan")
        else:
            rmse_insar_test = float("nan")
            r2_test = float("nan")

        # RMSE MLCW on test window (incremental)
        mlcw_resid_sq: list[float] = []
        for layer in layers:
            df = layer_dfs[layer]
            meta = layer_metas[layer]
            S_ke = train_result["layers"][layer]["S_ke"]
            S_kv = train_result["layers"][layer]["S_kv"]
            c_j  = train_result["layers"][layer].get("c_intercept", 0.0)
            tau  = layer_tau_opts[layer]

            H_zeroed = df["head_m_zeroed"].values
            b_cum    = df["mlcw_mm"].values
            h_c_z    = meta["h_c_zeroed"]

            context_start = max(0, test_cum_indices[0] - tau)
            all_indices = np.arange(context_start, test_cum_indices[-1] + 1)
            H_span = H_zeroed[all_indices]
            b_span = b_cum[all_indices]

            V_span = compute_virgin_term(H_span, h_c_z)
            b_pred_span = c_j + S_ke * H_span + (S_kv - S_ke) * V_span

            test_start = test_cum_indices[0] - context_start
            b_pred_test = b_pred_span[test_start:]
            b_obs_test  = b_span[test_start:]

            db_pred = np.diff(b_pred_test)
            db_obs  = np.diff(b_obs_test)
            n_common = min(len(db_pred), len(db_obs), n_test - 1)
            mlcw_resid_sq.extend((db_obs[:n_common] - db_pred[:n_common]) ** 2)

        rmse_mlcw_test = float(np.sqrt(np.mean(mlcw_resid_sq))) if mlcw_resid_sq else float("nan")

        fold_entry = {
            "fold":            f"Fold{fold_idx+1}_test{test_year}",
            "test_year":       test_year,
            "n_test":          n_test,
            "alpha":           alpha_train,
            "rmse_insar":      rmse_insar_test,
            "rmse_mlcw_mean":  rmse_mlcw_test,
            "r2_insar":        r2_test,
            "layer_results":   test_layer_params,
            "skipped":         False,
        }
        fold_results.append(fold_entry)

    return fold_results
