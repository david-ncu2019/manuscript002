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

    # ── Step 2: Fit α from cumulative InSAR (with OLS intercept) ─────────
    # Fit: α · cum_insar(t) + c = cum_pred(t)
    # c absorbs displacement not driven by GWL layers. α is the scale factor.
    cum_pred  = np.cumsum(db_pred_all)
    A_step2   = np.column_stack([cum_insar, np.ones(T)])
    coeffs, _, _, _ = np.linalg.lstsq(A_step2, cum_pred, rcond=None)
    alpha = float(np.clip(coeffs[0], 1e-6, 1.0))
    beta  = 1.0 / alpha
    c_intercept = float(coeffs[1])

    # RMSE and R² in cumulative domain (subtract intercept before inverting)
    insar_pred  = (cum_pred - c_intercept) / alpha
    insar_resid = cum_insar - insar_pred
    rmse_insar  = float(np.sqrt(np.mean(insar_resid ** 2)))
    ss_res = float(np.sum(insar_resid ** 2))
    ss_tot = float(np.sum((cum_insar - cum_insar.mean()) ** 2))
    r2_insar = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else np.nan

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
        Maximum integer lag to search. Default 120.
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
        # layer_data_train : training common-window block (for S_k and α fit)
        # layer_data_test  : test window block with frozen τ (for prediction only)
        layer_data_train: dict[str, dict] = {}
        layer_data_test:  dict[str, dict] = {}
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

            # ── Training common-window block ─────────────────────────────────
            # Same τ-alignment as fit_ihm_f_v3.py full-record block:
            # tau_max_train is computed after all layers' tau_opt are known,
            # so store per-layer tau_opt and build the training block after the loop.
            layer_data_train[layer] = {
                "inc_dH_train": inc_dH_train,
                "inc_db_train": inc_db_train,
                "e_m_train":    e_m_train,
                "i_m_train":    i_m_train,
                "tau_opt":      tau_opt,
                "rss_curve":    rss_curve,
            }

            # ── Test window block (context + test, lagged by τ) ──────────────
            context_dH = inc_dH_train[-tau_opt:] if tau_opt > 0 else np.array([], dtype=float)
            context_e  = e_m_train[-tau_opt:]     if tau_opt > 0 else np.array([], dtype=bool)
            context_i  = i_m_train[-tau_opt:]     if tau_opt > 0 else np.array([], dtype=bool)

            inc_dH_test = inc_dH[test_mask]
            inc_db_test = inc_db[test_mask]
            e_m_test    = e_m_full[test_mask]
            i_m_test    = i_m_full[test_mask]

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

            layer_data_test[layer] = {
                "dH_lagged":      dH_lagged[:n],
                "db":             inc_db_test[:n],
                "elastic_mask":   e_lagged[:n],
                "inelastic_mask": i_lagged[:n],
                "tau_opt":        tau_opt,
            }
            any_valid = True

        if not any_valid or len(layer_data_test) == 0:
            fold_results.append({
                "fold": f"Fold{fold_idx+1}_test{test_year}",
                "test_year": test_year,
                "skipped": True,
                "reason": "no valid layers after lag trimming",
            })
            continue

        # ── Build training common block aligned across layers (same as full-record fit) ──
        # Align all layers in the training window to a common epoch window so
        # joint_solve_fixed_tau receives arrays of equal length.
        tau_max_train = max(
            layer_data_train[lyr]["tau_opt"]
            for lyr in layer_data_test  # only layers that have test data
        )
        n_train_full = int(train_mask.sum())
        win_start_tr = tau_max_train
        win_len_tr   = n_train_full - win_start_tr

        if win_len_tr < 4:
            fold_results.append({
                "fold": f"Fold{fold_idx+1}_test{test_year}",
                "test_year": test_year,
                "skipped": True,
                "reason": f"training common window too short ({win_len_tr} epochs)",
            })
            continue

        layer_data_train_common: dict[str, dict] = {}
        for layer in layer_data_test:  # only layers with valid test data
            d      = layer_data_train[layer]
            tau    = d["tau_opt"]
            offset = tau_max_train - tau
            dH_lag  = d["inc_dH_train"][offset : offset + win_len_tr]
            db_win  = d["inc_db_train"][win_start_tr : win_start_tr + win_len_tr]
            e_win   = d["e_m_train"][offset : offset + win_len_tr]   # driver-time regime, lag-consistent
            i_win   = d["i_m_train"][offset : offset + win_len_tr]
            layer_data_train_common[layer] = {
                "dH_lagged":      dH_lag,
                "db":             db_win,
                "elastic_mask":   e_win,
                "inelastic_mask": i_win,
                "tau_opt":        tau,
            }

        # InSAR training window (incremental — same indexing as all_years)
        insar_train = insar_mm[train_mask]
        insar_train_win = insar_train[win_start_tr : win_start_tr + win_len_tr]

        # Fit S_k and α on training window only
        train_result = joint_solve_fixed_tau(layer_data_train_common, insar_train_win)
        alpha_train = train_result["alpha"]

        # ── Predict on test window using frozen training S_k parameters ──────
        # Do NOT refit S_k on test data — only accumulate predictions.
        insar_test = insar_mm[test_mask]
        n_test = min(
            len(insar_test),
            min(len(d["db"]) for d in layer_data_test.values()),
        )

        db_pred_test_all = np.zeros(n_test)
        test_layer_params: dict[str, dict] = {}
        for layer, d in layer_data_test.items():
            S_ke = train_result["layers"][layer]["S_ke"]
            S_kv = train_result["layers"][layer]["S_kv"]
            dH   = d["dH_lagged"][:n_test]
            e_m  = d["elastic_mask"][:n_test]
            i_m  = d["inelastic_mask"][:n_test]
            db_pred_j = np.where(e_m, S_ke * dH, 0.0) + np.where(i_m, S_kv * dH, 0.0)
            db_pred_test_all += db_pred_j
            test_layer_params[layer] = {
                "S_ke": S_ke, "S_kv": S_kv,
                "tau_opt": d["tau_opt"],
                "n_elastic":   int(e_m.sum()),
                "n_inelastic": int(i_m.sum()),
            }

        # Apply training α to convert predicted compaction to InSAR space
        cum_pred_test  = np.cumsum(db_pred_test_all)
        cum_insar_test = np.cumsum(insar_test[:n_test])
        insar_pred_test  = cum_pred_test / alpha_train
        insar_resid_test = cum_insar_test - insar_pred_test
        rmse_insar_test  = float(np.sqrt(np.mean(insar_resid_test ** 2)))
        ss_res = float(np.sum(insar_resid_test ** 2))
        ss_tot = float(np.sum((cum_insar_test - cum_insar_test.mean()) ** 2))
        r2_test = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else float("nan")

        # RMSE MLCW on test window
        mlcw_resid_sq: list[float] = []
        for layer, d in layer_data_test.items():
            S_ke = test_layer_params[layer]["S_ke"]
            S_kv = test_layer_params[layer]["S_kv"]
            dH   = d["dH_lagged"][:n_test]
            db   = d["db"][:n_test]
            e_m  = d["elastic_mask"][:n_test]
            i_m  = d["inelastic_mask"][:n_test]
            db_pred_j = np.where(e_m, S_ke * dH, 0.0) + np.where(i_m, S_kv * dH, 0.0)
            mlcw_resid_sq.extend((db - db_pred_j) ** 2)
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
