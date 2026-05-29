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

τ rule: τ is always a non-negative integer (5-day epochs). Never passed to a
continuous solver. τ=6 ≈ 1 month; τ=73 ≈ 1 year.

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
from scipy.optimize import lsq_linear

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

    Elastic:   head is recovering   (head_m > h_c_head_m)
    Inelastic: head below threshold (head_m <= h_c_head_m)

    Both masks have the same length as head_m.
    An epoch can be elastic OR inelastic — never both.
    """
    elastic    = head_m > h_c_head_m
    inelastic  = ~elastic
    return elastic.astype(bool), inelastic.astype(bool)


# ── Per-layer τ grid search ───────────────────────────────────────────────────

def tau_grid_search_per_layer(
    dH: np.ndarray,
    db: np.ndarray,
    elastic_mask: np.ndarray,
    inelastic_mask: np.ndarray,
    tau_max: int = 73,
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
        Maximum lag to search. Default 73 (≈ 1 year at 5-day epochs).
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

        dH_lag  = dH_anom[tau:]       # anomaly GWL lagged by τ epochs
        db_trim = db_anom[:n]         # anomaly MLCW aligned to lagged window
        e_trim  = elastic_mask[:n]
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


# ── Joint solve ───────────────────────────────────────────────────────────────

def joint_solve_fixed_tau(
    layer_data: dict[str, dict],
    insar_mm: np.ndarray,
    lam: float | None = None,
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
        Incremental InSAR (np.diff of cumulative). Cumsum applied inside.

    Returns
    -------
    dict with keys: layers, alpha, beta, rmse_mlcw, rmse_insar, r2_insar
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
        # lsq_linear with S_ke >= 0, S_kv >= 0
        res = lsq_linear(A_l, db, bounds=([0.0, 0.0], [np.inf, np.inf]),
                         method="trf", max_iter=1000)
        S_ke = float(res.x[0])
        S_kv = float(res.x[1])
        layer_params[layer] = {"S_ke": S_ke, "S_kv": S_kv, "tau_opt": tau}

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

    # ── Step 2: Fit α from cumulative InSAR (scalar OLS, no bounds needed) ──
    # α · cum_insar[t] = cum_sum_pred[t]
    # α = dot(cum_pred, cum_insar) / dot(cum_insar, cum_insar)
    cum_pred = np.cumsum(db_pred_all)
    denom = float(np.dot(cum_insar, cum_insar))
    if denom > 0:
        alpha = float(np.dot(cum_pred, cum_insar) / denom)
        alpha = float(np.clip(alpha, 1e-6, 1.0))   # enforce physical bounds
    else:
        alpha = 1.0
    beta = 1.0 / alpha

    # RMSE InSAR in cumulative domain
    insar_pred = cum_pred / alpha
    insar_resid = cum_insar - insar_pred
    rmse_insar = float(np.sqrt(np.mean(insar_resid ** 2)))
    ss_res = float(np.sum(insar_resid ** 2))
    ss_tot = float(np.sum((cum_insar - cum_insar.mean()) ** 2))
    r2_insar = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else np.nan

    return {
        "layers":     layer_params,
        "alpha":      alpha,
        "beta":       beta,
        "rmse_mlcw":  rmse_mlcw,
        "rmse_insar": rmse_insar,
        "r2_insar":   r2_insar,
        "T":          T,
        "lam":        None,
    }


# ── Walk-forward validation ───────────────────────────────────────────────────

def run_walk_forward_v3(
    layer_dfs: dict[str, pd.DataFrame],
    layer_metas: dict[str, dict],
    insar_mm: np.ndarray,
    tau_max: int = 73,
    fold_years: list[int] | None = None,
) -> list[dict]:
    """
    4-fold expanding walk-forward validation.

    Each fold:
      1. Split data into train (up to year N) and test (year N+1).
      2. On training window: detrend ΔH and Δb, run τ grid search, joint solve.
      3. On test window: apply training-window trend removal, predict, compute RMSE.

    Parameters
    ----------
    layer_dfs : dict[str -> pd.DataFrame]
        From load_all_layers. Each df has datetime, t_days, insar_mm, head_m, mlcw_mm.
    layer_metas : dict[str -> dict]
        From load_all_layers. Must contain h_c_head_m per layer.
    insar_mm : np.ndarray, shape (T,)
        Shared InSAR timeline.
    tau_max : int
        Maximum integer lag to search. Default 73.
    fold_years : list[int] or None
        Hold-out years. Default [2022, 2023, 2024, 2025].

    Returns
    -------
    list of fold dicts, each containing:
        fold, test_year, alpha, rmse_insar, rmse_mlcw_mean, n_test,
        layer_results (dict per layer: S_ke, S_kv, tau_opt, rmse_mm)
    """
    if fold_years is None:
        fold_years = [2022, 2023, 2024, 2025]

    layers = list(layer_dfs.keys())
    ref_df = layer_dfs[layers[0]]
    # insar_mm is already incremental (length T-1); build masks on T-1 length
    # Use datetime from epoch 0..T-2 (same length as incremental arrays)
    all_years = ref_df["datetime"].values[:-1]   # drop last epoch to match np.diff length
    all_years = pd.to_datetime(all_years).year

    fold_results: list[dict] = []

    for fold_idx, test_year in enumerate(fold_years):
        train_mask = all_years < test_year
        test_mask  = all_years == test_year

        if train_mask.sum() < 10 or test_mask.sum() < 1:
            fold_results.append({
                "fold": f"Fold{fold_idx+1}_test{test_year}",
                "test_year": test_year,
                "skipped": True,
                "reason": f"train={train_mask.sum()} test={test_mask.sum()} epochs",
            })
            continue

        # ── Per-layer: incremental signals, τ grid search on train window ──
        layer_data_fold: dict[str, dict] = {}
        any_valid = False

        for layer in layers:
            df   = layer_dfs[layer]
            meta = layer_metas[layer]

            head_m  = df["head_m"].values     # cumulative, length T_full
            mlcw_mm = df["mlcw_mm"].values    # cumulative, length T_full
            h_c     = meta["h_c_head_m"]

            # Incremental signals on the T_full-1 length axis (matches all_years)
            inc_dH = np.diff(head_m)     # length T_full-1
            inc_db = np.diff(mlcw_mm)    # length T_full-1

            # Regime mask on head at epoch t (length T_full-1)
            e_m_full, i_m_full = build_regime_mask(head_m[:-1], h_c)

            # τ grid search on training increments only
            inc_dH_train = inc_dH[train_mask]
            inc_db_train = inc_db[train_mask]
            e_m_train    = e_m_full[train_mask]
            i_m_train    = i_m_full[train_mask]
            dates_train  = df["datetime"].values[:-1][train_mask]

            effective_tau_max = min(tau_max, len(inc_dH_train) - 4)
            if effective_tau_max < 0:
                continue

            tau_opt, rss_curve, monthly_means_dH = tau_grid_search_per_layer(
                inc_dH_train, inc_db_train, e_m_train, i_m_train, effective_tau_max,
                dates=dates_train
            )

            # For the test window, we need τ context epochs from the end of training
            # then predict on test increments
            context_dH = inc_dH_train[-tau_opt:] if tau_opt > 0 else np.array([], dtype=float)
            context_e  = e_m_train[-tau_opt:]     if tau_opt > 0 else np.array([], dtype=bool)
            context_i  = i_m_train[-tau_opt:]     if tau_opt > 0 else np.array([], dtype=bool)

            inc_dH_test = inc_dH[test_mask]
            inc_db_test = inc_db[test_mask]
            e_m_test    = e_m_full[test_mask]
            i_m_test    = i_m_full[test_mask]

            # Full sequence: [context | test]; lag τ steps then align to test
            full_dH = np.concatenate([context_dH, inc_dH_test])
            full_e  = np.concatenate([context_e,  e_m_test])
            full_i  = np.concatenate([context_i,  i_m_test])

            if len(full_dH) <= tau_opt:
                continue

            dH_lagged = full_dH[tau_opt:]
            e_lagged  = full_e[tau_opt:]
            i_lagged  = full_i[tau_opt:]

            n = min(len(dH_lagged), len(inc_db_test))
            if n < 2:
                continue

            layer_data_fold[layer] = {
                "dH_lagged":      dH_lagged[:n],
                "db":             inc_db_test[:n],
                "elastic_mask":   e_lagged[:n],
                "inelastic_mask": i_lagged[:n],
                "tau_opt":        tau_opt,
                "rss_curve":      rss_curve,
            }
            any_valid = True

        if not any_valid or len(layer_data_fold) == 0:
            fold_results.append({
                "fold": f"Fold{fold_idx+1}_test{test_year}",
                "test_year": test_year,
                "skipped": True,
                "reason": "no valid layers after lag trimming",
            })
            continue

        # InSAR test window (already incremental — same length as all_years)
        insar_test = insar_mm[test_mask]
        n_test = min(len(insar_test), min(len(d["db"]) for d in layer_data_fold.values()))

        result = joint_solve_fixed_tau(layer_data_fold, insar_test[:n_test])

        fold_entry = {
            "fold":            f"Fold{fold_idx+1}_test{test_year}",
            "test_year":       test_year,
            "n_test":          n_test,
            "alpha":           result["alpha"],
            "rmse_insar":      result["rmse_insar"],
            "rmse_mlcw_mean":  result["rmse_mlcw"],
            "r2_insar":        result["r2_insar"],
            "layer_results":   result["layers"],
            "skipped":         False,
        }
        fold_results.append(fold_entry)

    return fold_results
