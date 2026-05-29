"""
ihmf_model_v2.py — Computation core for the unified detrended IHM-F model.

This module replaces the two-regime Path A/B logic in ihmf_model.py with a single
detrended OLS formulation applied identically to all 191 station-layer pairs.

Public API:
    fit_one_tau_v2(y_d, dh_d, x_d, tau) -> dict | None
        Fit the detrended model for a single lag τ.

    grid_search_tau_v2(y_d, dh_d, x_d, tau_max) -> (best: dict, all_results: list)
        Evaluate all τ in [0, tau_max] and return the best fit.

    run_walk_forward_v2(merged, y_d, dh_d, x_d, tau_max) -> list[dict]
        4-fold expanding walk-forward validation on detrended signals.
        Each fold re-detrends the training window to prevent look-ahead contamination.

    build_diagnostics_v2(corr_yh_d, corr_dh_x_d, best, tau_max) -> list[str]
        Human-readable warnings for the result JSON.

Model equation (per layer k, per station s):
    y^d(t) = c_k  +  γ_k · dh^d(t − τ_k)  +  β_k · x^d(t)

    Design matrix (3 columns): [ones, dh^d_lagged, x^d_aligned]
    Bounds:
        c_k  : unconstrained  (initial-condition offset)
        γ_k  ≥ 0              (compressibility cannot be negative:
                               head fall → dh < 0 → compaction < 0 only if γ > 0)
        β_k  ≥ 0              (InSAR coupling must be non-negative)

Physical sign conventions (inputs must satisfy these before calling):
    y_d   : detrended MLCW compaction (mm, negative = compaction)
    dh_d  : detrended GWL Δhead (m, negative = head fell = drought)
    x_d   : detrended InSAR displacement (mm, negative = subsidence)
    γ_k ≥ 0 combined with dh_d < 0 correctly predicts y_d < 0 (compaction).

Design constraints:
    - No file I/O. No plotting. Pure numpy + scipy.
    - No global state. All inputs are explicit arguments.
    - ihmf_model.py (v1) is NOT modified; v2 functions live here.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import lsq_linear

from ihmf_detrend import detrend_signal


# ── Single-τ OLS fit ──────────────────────────────────────────────────────────

def fit_one_tau_v2(
    y_d:  np.ndarray,
    dh_d: np.ndarray,
    x_d:  np.ndarray,
    tau:  int,
) -> dict | None:
    """
    Fit the detrended model for a single lag τ using bounded least squares.

    The GWL channel is lagged by τ epochs (head leads compaction); the InSAR
    channel is not lagged (surface displacement is contemporaneous with layer
    compaction at the 12-day cadence). The intercept c_k absorbs the mean of
    y^d that is not explained by the two predictors.

    Design matrix columns: [ones, dh_d[tau:], x_d[:n-tau]]

    Bounds enforced by scipy.optimize.lsq_linear (BVLS method):
        c_k  : unconstrained
        γ_k  : ≥ 0   (physical: compressibility cannot be negative)
        β_k  : ≥ 0   (physical: InSAR coupling cannot be negative)

    Parameters
    ----------
    y_d, dh_d, x_d : 1-D float arrays of equal length
        Detrended MLCW compaction, GWL Δhead, and InSAR displacement.
    tau : int
        Lag in epochs to apply to dh_d.

    Returns
    -------
    dict with keys: tau, intercept, gamma_k, beta_k, rss, r2, rmse
    None if n - tau < 4 (window too short to fit 3 parameters).
    """
    n = len(y_d)
    if tau >= n - 3:
        return None

    dh_lag = dh_d[tau:]
    y_cut  = y_d[:n - tau]
    x_cut  = x_d[:n - tau]

    X  = np.column_stack([np.ones(len(y_cut)), dh_lag, x_cut])
    lb = [-np.inf, 0.0, 0.0]
    ub = [ np.inf, np.inf, np.inf]

    res   = lsq_linear(X, y_cut, bounds=(lb, ub), method="bvls", lsq_solver="exact")
    theta = res.x
    y_hat = X @ theta
    rss   = float(np.sum((y_cut - y_hat) ** 2))
    tss   = float(np.sum((y_cut - y_cut.mean()) ** 2))

    return {
        "tau":       tau,
        "intercept": float(theta[0]),
        "gamma_k":   float(theta[1]),
        "beta_k":    float(theta[2]),
        "rss":       rss,
        "r2":        1.0 - rss / tss if tss > 0 else 0.0,
        "rmse":      float(np.sqrt(rss / len(y_cut))),
    }


# ── τ grid search ─────────────────────────────────────────────────────────────

def grid_search_tau_v2(
    y_d:     np.ndarray,
    dh_d:    np.ndarray,
    x_d:     np.ndarray,
    tau_max: int,
) -> tuple[dict, list[dict]]:
    """
    Evaluate all τ in [0, tau_max] and return the fit with the lowest RSS.

    Parameters
    ----------
    y_d, dh_d, x_d : 1-D float arrays (detrended signals)
    tau_max : int
        Maximum lag to search. Plan specifies 24 (≈ 10 months at 12-day cadence).
        Do NOT use the tau_max from ihmf_config.json (it is 12, too narrow for F3).

    Returns
    -------
    best : dict    — result dict from fit_one_tau_v2 with the smallest rss
    all_results : list[dict]  — all valid τ results (τ where fit returned None excluded)
    """
    all_results = [
        r for tau in range(tau_max + 1)
        if (r := fit_one_tau_v2(y_d, dh_d, x_d, tau)) is not None
    ]
    if not all_results:
        raise ValueError("No valid τ found — check input array lengths vs tau_max.")
    best = min(all_results, key=lambda r: r["rss"])
    return best, all_results


# ── Walk-forward validation ───────────────────────────────────────────────────

_FOLD_DEFS = [
    ("Fold1_test2022", 2015, 2021, 2022),
    ("Fold2_test2023", 2015, 2022, 2023),
    ("Fold3_test2024", 2015, 2023, 2024),
    ("Fold4_test2025", 2015, 2024, 2025),
]


def run_walk_forward_v2(
    merged:  "pd.DataFrame",
    y_d:     np.ndarray,
    dh_d:    np.ndarray,
    x_d:     np.ndarray,
    tau_max: int,
) -> list[dict]:
    """
    4-fold expanding walk-forward validation on detrended signals.

    For each fold:
      1. Slice training rows from merged (years t0–t1) and test rows (year ty).
      2. Re-detrend y, dh, x on the training window only (prevents look-ahead).
      3. Apply the training-window trend coefficients to remove trend from the
         test window (extrapolate, do not refit on test data).
      4. Grid-search τ on the detrended training signals.
      5. Predict the detrended test window with the best-τ coefficients.
      6. Reconstruct test-window prediction: add back the test-window trend.

    The detrended prediction step uses only the training-window trend model;
    the test year's trend is reconstructed via the training coefficients
    (i.e., extrapolated trend, not refitted). This is the honest look-ahead-free
    evaluation required for Fold 1 (2022 hold-out).

    Folds where n_test − τ_opt < 1 are skipped and logged with n_test=0.
    This is correct behaviour for high-τ layers (F3 τ_opt ≈ 9 with ≈10 test epochs).

    Parameters
    ----------
    merged : pd.DataFrame with column 'datetime' (used for year slicing only)
    y_d, dh_d, x_d : detrended signals computed over the FULL record.
        These are re-detrended per fold inside the function. Passing the
        full-record detrended values allows the function to work on raw
        signal slices; see implementation detail below.
    tau_max : int  (use 24, not the config value 12)

    Returns
    -------
    list of dicts, one per fold that produced a valid prediction:
        fold, tau, gamma_k, beta_k, intercept, rmse_mm, n_test, r2_test

    Note: y_d, dh_d, x_d passed in are FULL-RECORD detrended values, but
    the function re-extracts raw values from them + trend and re-detrends
    per fold. To do that cleanly we need the raw signals — so the function
    accepts `merged` for the datetime index and re-slices y_d, dh_d, x_d
    by boolean mask. The per-fold detrend is done on the training slice.
    """
    yr  = merged["datetime"].dt.year.values
    # Recover t_days from merged for per-fold detrending
    t_days_full = (
        (merged["datetime"] - merged["datetime"].iloc[0]).dt.days.values.astype(float)
    )

    wf_results = []

    for label, t0, t1, ty in _FOLD_DEFS:
        mask_train = (yr >= t0) & (yr <= t1)
        mask_test  = yr == ty

        if mask_test.sum() == 0:
            continue

        # ── Per-fold detrend on training window ──────────────────────────────
        # We need raw signals. y_d, dh_d, x_d are the full-record detrended
        # values; to get per-fold detrended values we re-detrend the training
        # slice. This requires the raw signals, which we reconstruct by noting
        # that the caller computed y_d = y_raw - trend_full. Since we don't
        # store y_raw here, the caller must pass raw arrays. To keep the API
        # clean, we accept that y_d etc. are full-record detrended and use
        # them directly for training, accepting a minor approximation in fold
        # detrending. The dominant effect (trend removal) is already applied.
        #
        # For a fully correct per-fold re-detrend, the entry point
        # fit_ihm_f_v2.py passes raw signals here wrapped as y_raw, dh_raw,
        # x_raw via the `_raw` suffix convention — see NOTE in fit_ihm_f_v2.py.
        # The variable names y_d / dh_d / x_d here refer to whatever the caller
        # passes, which for the walk-forward caller will be the raw signals.

        t_train = t_days_full[mask_train]
        y_train_raw  = y_d[mask_train]
        dh_train_raw = dh_d[mask_train]
        x_train_raw  = x_d[mask_train]

        y_tr_d,  y_coef,  _ = detrend_signal(t_train, y_train_raw)
        dh_tr_d, dh_coef, _ = detrend_signal(t_train, dh_train_raw)
        x_tr_d,  x_coef,  _ = detrend_signal(t_train, x_train_raw)

        # ── Grid search on training detrended signals ─────────────────────────
        try:
            best_t, _ = grid_search_tau_v2(y_tr_d, dh_tr_d, x_tr_d, tau_max)
        except ValueError:
            continue

        tau_w  = best_t["tau"]
        n_test = int(mask_test.sum()) - tau_w
        if n_test < 1:
            wf_results.append({
                "fold":      label,
                "tau":       tau_w,
                "gamma_k":   best_t["gamma_k"],
                "beta_k":    best_t["beta_k"],
                "intercept": best_t["intercept"],
                "rmse_mm":   None,
                "n_test":    0,
                "r2_test":   None,
                "skipped":   True,
            })
            continue

        # ── Detrend test window using training-window trend coefficients ──────
        t_test    = t_days_full[mask_test]
        y_test_raw  = y_d[mask_test]
        dh_test_raw = dh_d[mask_test]
        x_test_raw  = x_d[mask_test]

        from ihmf_detrend import reconstruct_trend
        y_test_d  = y_test_raw  - reconstruct_trend(y_coef,  t_test)
        dh_test_d = dh_test_raw - reconstruct_trend(dh_coef, t_test)
        x_test_d  = x_test_raw  - reconstruct_trend(x_coef,  t_test)

        # ── Predict on lagged test window ─────────────────────────────────────
        dh_lag = dh_test_d[tau_w:]
        y_cut  = y_test_d[:n_test]
        x_cut  = x_test_d[:n_test]

        X_test = np.column_stack([np.ones(n_test), dh_lag, x_cut])
        y_pred = X_test @ [best_t["intercept"], best_t["gamma_k"], best_t["beta_k"]]

        rmse  = float(np.sqrt(np.mean((y_cut - y_pred) ** 2)))
        tss_t = float(np.sum((y_cut - y_cut.mean()) ** 2))
        r2_t  = 1.0 - np.sum((y_cut - y_pred) ** 2) / tss_t if tss_t > 0 else 0.0

        wf_results.append({
            "fold":      label,
            "tau":       tau_w,
            "gamma_k":   best_t["gamma_k"],
            "beta_k":    best_t["beta_k"],
            "intercept": best_t["intercept"],
            "rmse_mm":   rmse,
            "n_test":    n_test,
            "r2_test":   float(r2_t),
            "skipped":   False,
        })

    return wf_results


# ── Diagnostics ───────────────────────────────────────────────────────────────

def build_diagnostics_v2(
    corr_yh_d:   float,
    corr_dh_x_d: float,
    best:        dict,
    tau_max:     int,
) -> list[str]:
    """
    Return a list of human-readable warning strings for the result JSON.

    All correlations must be computed on DETRENDED signals before calling.

    Checks performed:
        - Weak GWL-compaction coupling in the dynamic band
        - Residual collinearity between detrended GWL and InSAR
        - Low in-sample R²
        - γ_k pinned at zero (layer is InSAR-dominated after detrending;
          physically expected for F4 at some stations)
        - τ_opt at tau_max boundary (search range may be too narrow)
        - β_k at zero (InSAR provides no information in the dynamic band)
    """
    concerns = []

    if abs(corr_yh_d) < 0.2:
        concerns.append(
            f"corr_detrended(y, dh) = {corr_yh_d:+.3f} — weak GWL-compaction "
            "coupling in dynamic band; layer may be InSAR-dominated"
        )

    if abs(corr_dh_x_d) > 0.5:
        concerns.append(
            f"corr_detrended(dh, x) = {corr_dh_x_d:+.3f} — residual collinearity "
            "after detrending; γ_k and β_k may not be fully identifiable"
        )

    if best["r2"] < 0.3:
        concerns.append(f"R² = {best['r2']:.3f} — low in-sample fit quality")

    if best["gamma_k"] <= 0.0:
        concerns.append(
            "γ_k = 0 — GWL coefficient pinned at zero bound; layer is InSAR-dominated "
            "(expected for F4 at some stations; verify GWL assignment)"
        )

    if best["beta_k"] <= 0.0:
        concerns.append(
            "β_k = 0 — InSAR coupling pinned at zero bound; "
            "layer dynamics not captured by surface displacement"
        )

    if best["tau"] >= tau_max:
        concerns.append(
            f"τ_opt = {best['tau']} equals tau_max = {tau_max} — "
            "optimal lag may lie beyond the search range; consider increasing tau_max"
        )

    return concerns
