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

Public API:
    tau_grid_search_per_layer(dH, db, regime_mask, tau_max) -> (tau_opt, rss_curve)
    build_regime_mask(head_m, h_c_head_m) -> (elastic_mask, inelastic_mask)
    joint_solve_fixed_tau(layer_data, insar_mm, lam) -> result_dict
    run_walk_forward_v3(layer_dfs, layer_metas, insar_mm, tau_max, fold_years) -> list[dict]
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import lsq_linear

from ihmf_detrend import detrend_signal


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
) -> tuple[int, list[float]]:
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

    Returns
    -------
    tau_opt : int
        Lag with minimum RSS. Always an integer.
    rss_curve : list of float, length tau_max+1
        RSS at each candidate τ ∈ {0, …, tau_max}.
    """
    T = len(dH)
    rss_curve: list[float] = []

    for tau in range(tau_max + 1):
        n = T - tau
        if n < 4:
            rss_curve.append(np.inf)
            continue

        dH_lag  = dH[tau:]            # GWL lagged by τ epochs
        db_trim = db[:n]              # MLCW aligned to lagged window
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

        rss = float(np.sum((db_trim - db_pred) ** 2))
        rss_curve.append(rss)

    tau_opt = int(np.argmin(rss_curve))
    return tau_opt, rss_curve


# ── Joint solve ───────────────────────────────────────────────────────────────

def joint_solve_fixed_tau(
    layer_data: dict[str, dict],
    insar_mm: np.ndarray,
    lam: float | None = None,
) -> dict:
    """
    Solve for [S_ke_j, S_kv_j for all j, β=1/α] jointly using lsq_linear.

    Parameters
    ----------
    layer_data : dict[layer_code -> dict]
        Each entry must have:
          'dH_lagged'     : 1-D float array, shape (T,) — ΔH lagged by tau_opt epochs
          'db'            : 1-D float array, shape (T,) — MLCW compaction
          'elastic_mask'  : bool array, shape (T,)
          'inelastic_mask': bool array, shape (T,)
        All arrays must have the same length T (trimmed to shortest layer window).
    insar_mm : 1-D float array, shape (T_full,)
        InSAR displacement. Trimmed inside this function to match T.
    lam : float or None
        Weight of the InSAR term relative to MLCW. None → 1/N where N = number of layers.

    Returns
    -------
    dict with keys:
        layers      : dict[layer_code -> {S_ke, S_kv, tau_opt}]
        alpha       : float in (0, 1]
        beta        : float = 1/alpha
        rmse_mlcw   : float — per-epoch RMSE across all layers (mm)
        rmse_insar  : float — RMSE of reconstructed sum vs InSAR (mm)
        r2_insar    : float
    """
    layers = list(layer_data.keys())
    N = len(layers)
    if lam is None:
        lam = 1.0 / N

    # Determine T from the shortest lagged window
    T = min(len(d["dH_lagged"]) for d in layer_data.values())
    insar_trim = insar_mm[:T]

    # Build design matrix rows and RHS
    # Columns: [S_ke_0, S_kv_0, S_ke_1, S_kv_1, ..., β]
    n_params = 2 * N + 1  # 2 per layer + beta

    A_rows: list[np.ndarray] = []
    b_rows: list[float] = []

    for j, layer in enumerate(layers):
        d = layer_data[layer]
        dH   = d["dH_lagged"][:T]
        db   = d["db"][:T]
        e_m  = d["elastic_mask"][:T]
        i_m  = d["inelastic_mask"][:T]

        for t in range(T):
            row = np.zeros(n_params)
            # S_ke column (elastic epochs only)
            if e_m[t]:
                row[2 * j] = dH[t]
            # S_kv column (inelastic epochs only)
            if i_m[t]:
                row[2 * j + 1] = dH[t]
            # β column: 0 in MLCW rows
            A_rows.append(row)
            b_rows.append(float(db[t]))

    # InSAR rows: Σ_j S_j · ΔH_j(t) / β = Δd_v(t)
    # Rearranged: Σ_j S_j · ΔH_j(t) - β · Δd_v(t) = 0
    # With weight √λ on both sides
    sqrt_lam = np.sqrt(lam)
    for t in range(T):
        row = np.zeros(n_params)
        for j, layer in enumerate(layers):
            d = layer_data[layer]
            dH = d["dH_lagged"][:T]
            e_m = d["elastic_mask"][:T]
            i_m = d["inelastic_mask"][:T]
            if e_m[t]:
                row[2 * j] = sqrt_lam * dH[t]
            if i_m[t]:
                row[2 * j + 1] = sqrt_lam * dH[t]
        row[-1] = -sqrt_lam * insar_trim[t]   # β coefficient
        A_rows.append(row)
        b_rows.append(0.0)

    A = np.array(A_rows)
    b = np.array(b_rows)

    # Bounds: all S_j >= 0, β >= 1
    lb = np.zeros(n_params)
    lb[-1] = 1.0
    ub = np.full(n_params, np.inf)

    result = lsq_linear(A, b, bounds=(lb, ub), method="trf", max_iter=2000)
    theta = result.x

    # Unpack
    layer_params: dict[str, dict] = {}
    db_pred_all = np.zeros(T)
    for j, layer in enumerate(layers):
        S_ke = float(theta[2 * j])
        S_kv = float(theta[2 * j + 1])
        tau  = layer_data[layer].get("tau_opt", 0)
        layer_params[layer] = {"S_ke": S_ke, "S_kv": S_kv, "tau_opt": tau}

        d   = layer_data[layer]
        dH  = d["dH_lagged"][:T]
        e_m = d["elastic_mask"][:T]
        i_m = d["inelastic_mask"][:T]
        db_pred_j = np.where(e_m, S_ke * dH, 0.0) + np.where(i_m, S_kv * dH, 0.0)
        db_pred_all += db_pred_j

    beta  = float(theta[-1])
    alpha = 1.0 / beta if beta > 0 else np.nan

    # RMSE MLCW (average over all layer-epoch pairs)
    mlcw_resid_sq: list[float] = []
    for j, layer in enumerate(layers):
        d   = layer_data[layer]
        dH  = d["dH_lagged"][:T]
        db  = d["db"][:T]
        e_m = d["elastic_mask"][:T]
        i_m = d["inelastic_mask"][:T]
        S_ke = layer_params[layer]["S_ke"]
        S_kv = layer_params[layer]["S_kv"]
        db_pred_j = np.where(e_m, S_ke * dH, 0.0) + np.where(i_m, S_kv * dH, 0.0)
        mlcw_resid_sq.extend((db - db_pred_j) ** 2)
    rmse_mlcw = float(np.sqrt(np.mean(mlcw_resid_sq)))

    # RMSE InSAR
    insar_pred = db_pred_all / beta
    insar_resid = insar_trim - insar_pred
    rmse_insar = float(np.sqrt(np.mean(insar_resid ** 2)))
    ss_res = np.sum(insar_resid ** 2)
    ss_tot = np.sum((insar_trim - insar_trim.mean()) ** 2)
    r2_insar = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else np.nan

    return {
        "layers":     layer_params,
        "alpha":      alpha,
        "beta":       beta,
        "rmse_mlcw":  rmse_mlcw,
        "rmse_insar": rmse_insar,
        "r2_insar":   r2_insar,
        "T":          T,
        "lam":        lam,
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

            effective_tau_max = min(tau_max, len(inc_dH_train) - 4)
            if effective_tau_max < 0:
                continue

            tau_opt, rss_curve = tau_grid_search_per_layer(
                inc_dH_train, inc_db_train, e_m_train, i_m_train, effective_tau_max
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
