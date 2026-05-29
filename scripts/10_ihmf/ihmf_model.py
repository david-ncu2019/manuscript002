"""
ihmf_model.py — Computation core for the two-regime GWL-driven per-layer compaction model.

Public API:
    prepare_signals(merged, hc_percentile)
        -> (t_days, y_raw, x_raw, dh_raw, h_raw, is_elastic,
            h_c_eff, corr_yh, corr_yx, corr_hx)

    -- Path B: bounded OLS (NEG_SKV layers or fallback) --

    fit_one_tau(y_raw, dh_raw, x_raw, is_elastic, tau,
                lb_ske=0.0, lb_skv=0.0) -> dict | None

    grid_search_tau(y_raw, dh_raw, x_raw, is_elastic, tau_max,
                    lb_ske=0.0, lb_skv=0.0)
        -> (best: dict, all_results: list[dict])

    run_walk_forward(merged, y_raw, dh_raw, x_raw, is_elastic, tau_max,
                     lb_ske=0.0, lb_skv=0.0)
        -> list[dict]

    -- Path A: b_k fitting (OK layers with valid 2S-TOOL S_ke/S_kv) --

    fit_one_tau_bk(y_raw, dh_raw, x_raw, is_elastic, tau,
                   ske_fixed, skv_fixed, layer_span_m) -> dict | None

    grid_search_tau_bk(y_raw, dh_raw, x_raw, is_elastic, tau_max,
                       ske_fixed, skv_fixed, layer_span_m)
        -> (best: dict, all_results: list[dict])

    run_walk_forward_bk(merged, y_raw, dh_raw, x_raw, is_elastic, tau_max,
                        ske_fixed, skv_fixed, layer_span_m)
        -> list[dict]

    build_diagnostics(corr_yh, best, n_inelastic,
                      lb_ske=0.0, lb_skv=0.0) -> list[str]

Sign convention (raw data, no detrending):
    y_raw  — raw cumulative MLCW compaction (mm, negative = compaction)
    dh_raw — ΔH from first epoch (m, negative = head fell = drought)
    x_raw  — raw cumulative InSAR displacement (mm, negative = subsidence)
    S_ske, S_skv — physical compressibility coefficients, POSITIVE in bounded fit.
                   S_ke · dh · I_e = (+) · (−) = (−) correctly gives compaction.

Physical constraints enforced by bounded least squares (scipy.optimize.lsq_linear):
    S_ske ≥ lb_ske ≥ 0  (elastic compressibility cannot be negative)
    S_skv ≥ lb_skv ≥ 0  (inelastic compressibility cannot be negative)
    β     ≥ 0            (InSAR coupling must be non-negative)
    c     unconstrained  (intercept absorbs pre-observation compaction history)

Lower bounds lb_ske and lb_skv come from the caller (fit_ihm_f.py) and are derived
as 0.1 × the 2S-TOOL reference values, falling back to 0.0 for NEG_SKV layers.
"""

import numpy as np
import pandas as pd
from scipy.optimize import lsq_linear


# ── Signal preparation ────────────────────────────────────────────────────────

def prepare_signals(merged: "pd.DataFrame", hc_percentile: int):
    """
    Extract raw signals and classify elastic/inelastic regime.

    Uses un-detrended data throughout so that model output D_k(t) is directly
    the cumulative compaction — needed for cumulative attribution at grid points.

    dh_raw = H(t) - H(t_ref) is the GWL driver: negative when head fell (drought),
    which correctly multiplied by positive S_ke/S_kv gives negative (compaction).

    Returns a flat tuple consumed by the fitting functions below.
    """
    t_days = (merged["datetime"] - merged["datetime"].min()).dt.days.values.astype(float)
    y_raw  = merged["mlcw_mm"].values          # raw cumulative compaction (negative = compaction)
    x_raw  = merged["insar_mm"].values         # raw cumulative InSAR (negative = subsidence)
    h_raw  = merged["head_m"].values           # piezometric head (m above MSL, higher = rising)
    dh_raw = h_raw - h_raw[0]                  # ΔH from first epoch; negative = head fell

    corr_yh = float(np.corrcoef(y_raw, dh_raw)[0, 1])
    corr_yx = float(np.corrcoef(y_raw, x_raw)[0, 1])
    corr_hx = float(np.corrcoef(dh_raw, x_raw)[0, 1])

    h_c_eff    = float(np.percentile(h_raw, hc_percentile))
    is_elastic = h_raw > h_c_eff

    return (t_days, y_raw, x_raw, dh_raw, h_raw, is_elastic,
            h_c_eff, corr_yh, corr_yx, corr_hx)


# ── Single-τ OLS fit ──────────────────────────────────────────────────────────

def fit_one_tau(y_raw: np.ndarray, dh_raw: np.ndarray,
                x_raw: np.ndarray, is_elastic: np.ndarray,
                tau: int,
                lb_ske: float = 0.0, lb_skv: float = 0.0) -> dict | None:
    """
    Fit the two-regime model for a single lag τ using bounded least squares.

    Design matrix: [ones, dh_raw·mask_e, dh_raw·mask_i, x_raw].
    The intercept absorbs the initial offset D_k(t_0) — the cumulative
    compaction already present at the first epoch, which lies outside the
    observation window and is not explained by any regressor.

    Bounds enforced:
        intercept: unconstrained
        S_ske    : ≥ lb_ske  (physical: elastic compressibility ≥ 0)
        S_skv    : ≥ lb_skv  (physical: inelastic compressibility ≥ 0)
        beta     : ≥ 0       (physical: InSAR coupling non-negative)

    Returns a dict with tau, S_ske, S_skv, beta, rss, r2, rmse; or None if
    the window after lag is too short.
    """
    n = len(y_raw)
    if tau >= n - 3:
        return None
    dh_lag = dh_raw[tau:]
    y_cut  = y_raw[:n - tau]
    x_cut  = x_raw[:n - tau]
    mask_e = is_elastic[:n - tau]
    mask_i = ~mask_e
    X      = np.column_stack([np.ones(len(y_cut)), dh_lag * mask_e, dh_lag * mask_i, x_cut])
    lb = [-np.inf, lb_ske, lb_skv, 0.0]
    ub = [ np.inf,  np.inf,  np.inf, np.inf]
    res   = lsq_linear(X, y_cut, bounds=(lb, ub), method="bvls", lsq_solver="exact")
    theta = res.x
    y_hat = X @ theta
    rss   = float(np.sum((y_cut - y_hat) ** 2))
    tss   = float(np.sum((y_cut - y_cut.mean()) ** 2))
    return {
        "tau":   tau,
        "intercept": float(theta[0]),
        "S_ske": float(theta[1]),
        "S_skv": float(theta[2]),
        "beta":  float(theta[3]),
        "rss":   rss,
        "r2":    1.0 - rss / tss if tss > 0 else 0.0,
        "rmse":  float(np.sqrt(rss / len(y_cut))),
    }


# ── b_k single-τ fit (Path A — fixed S_ke/S_kv from 2S-TOOL) ─────────────────

def fit_one_tau_bk(y_raw: np.ndarray, dh_raw: np.ndarray,
                   x_raw: np.ndarray, is_elastic: np.ndarray,
                   tau: int,
                   ske_fixed: float, skv_fixed: float,
                   layer_span_m: float) -> dict | None:
    """
    Fit the b_k model for a single lag τ.

    S_ke and S_kv are fixed at their 2S-TOOL values; the free parameter is the
    compressible thickness b_k (metres). The combined GWL driver is:
        driver = dh · mask_e · ske_fixed  +  dh · mask_i · skv_fixed
    so the design matrix is [ones, driver, x_raw], and coeff[1] = b_k.

    Bounds: b_k ∈ (0, layer_span_m], β ≥ 0, intercept unconstrained.

    Returns dict with tau, b_k, S_ske (=ske_fixed×b_k), S_skv (=skv_fixed×b_k),
    intercept, beta, rss, r2, rmse; or None if window too short.
    """
    n = len(y_raw)
    if tau >= n - 3:
        return None
    dh_lag = dh_raw[tau:]
    y_cut  = y_raw[:n - tau]
    x_cut  = x_raw[:n - tau]
    mask_e = is_elastic[:n - tau]
    mask_i = ~mask_e
    driver = dh_lag * mask_e * ske_fixed + dh_lag * mask_i * skv_fixed
    X      = np.column_stack([np.ones(len(y_cut)), driver, x_cut])
    lb = [-np.inf, 0.0,          0.0]
    ub = [ np.inf, layer_span_m, np.inf]
    res   = lsq_linear(X, y_cut, bounds=(lb, ub), method="bvls", lsq_solver="exact")
    theta = res.x
    y_hat = X @ theta
    rss   = float(np.sum((y_cut - y_hat) ** 2))
    tss   = float(np.sum((y_cut - y_cut.mean()) ** 2))
    b_k   = float(theta[1])
    return {
        "tau":       tau,
        "intercept": float(theta[0]),
        "b_k":       b_k,
        "S_ske":     ske_fixed * b_k,
        "S_skv":     skv_fixed * b_k,
        "beta":      float(theta[2]),
        "rss":       rss,
        "r2":        1.0 - rss / tss if tss > 0 else 0.0,
        "rmse":      float(np.sqrt(rss / len(y_cut))),
    }


# ── τ grid search ─────────────────────────────────────────────────────────────

def grid_search_tau(y_raw, dh_raw, x_raw, is_elastic,
                    tau_max: int,
                    lb_ske: float = 0.0, lb_skv: float = 0.0) -> tuple:
    """Evaluate all τ in [0, tau_max] with physical bounds. Returns (best_result, all_results)."""
    all_results = [r for tau in range(tau_max + 1)
                   if (r := fit_one_tau(y_raw, dh_raw, x_raw, is_elastic, tau,
                                        lb_ske=lb_ske, lb_skv=lb_skv))
                   is not None]
    best = min(all_results, key=lambda r: r["rss"])
    return best, all_results


def grid_search_tau_bk(y_raw, dh_raw, x_raw, is_elastic,
                       tau_max: int,
                       ske_fixed: float, skv_fixed: float,
                       layer_span_m: float) -> tuple:
    """Evaluate all τ in [0, tau_max] for the b_k model. Returns (best_result, all_results)."""
    all_results = [r for tau in range(tau_max + 1)
                   if (r := fit_one_tau_bk(y_raw, dh_raw, x_raw, is_elastic, tau,
                                           ske_fixed=ske_fixed, skv_fixed=skv_fixed,
                                           layer_span_m=layer_span_m))
                   is not None]
    best = min(all_results, key=lambda r: r["rss"])
    return best, all_results


# ── Walk-forward validation ────────────────────────────────────────────────────

def run_walk_forward(merged: "pd.DataFrame", y_raw: np.ndarray,
                     dh_raw: np.ndarray, x_raw: np.ndarray,
                     is_elastic: np.ndarray, tau_max: int,
                     lb_ske: float = 0.0, lb_skv: float = 0.0) -> list:
    """
    4-fold expanding-window walk-forward validation with physical bounds.
    Returns list of fold dicts (fold, tau, S_ske, S_skv, beta, rmse_mm, n_test).
    """
    fold_defs = [
        ("Fold1_test2022", 2015, 2021, 2022),
        ("Fold2_test2023", 2015, 2022, 2023),
        ("Fold3_test2024", 2015, 2023, 2024),
        ("Fold4_test2025", 2015, 2024, 2025),
    ]
    wf_results = []
    yr = merged["datetime"].dt.year

    for label, t0, t1, ty in fold_defs:
        train = (yr >= t0) & (yr <= t1)
        test  = yr == ty
        if test.sum() == 0:
            continue
        best_t, _ = grid_search_tau(y_raw[train], dh_raw[train],
                                    x_raw[train], is_elastic[train], tau_max,
                                    lb_ske=lb_ske, lb_skv=lb_skv)
        tau_w  = best_t["tau"]
        n_test = test.sum() - tau_w
        if n_test < 1:
            continue
        dh_test = dh_raw[test][tau_w:]
        y_test  = y_raw[test][:n_test]
        x_test  = x_raw[test][:n_test]
        m_test  = is_elastic[test][:n_test]
        X = np.column_stack([np.ones(n_test), dh_test * m_test, dh_test * (~m_test), x_test])
        y_pred = X @ [best_t["intercept"], best_t["S_ske"], best_t["S_skv"], best_t["beta"]]
        rmse   = float(np.sqrt(np.mean((y_test - y_pred) ** 2)))
        wf_results.append({
            "fold":    label,
            "tau":     best_t["tau"],
            "S_ske":   best_t["S_ske"],
            "S_skv":   best_t["S_skv"],
            "beta":    best_t["beta"],
            "rmse_mm": rmse,
            "n_test":  str(n_test),
        })
    return wf_results


def run_walk_forward_bk(merged: "pd.DataFrame", y_raw: np.ndarray,
                        dh_raw: np.ndarray, x_raw: np.ndarray,
                        is_elastic: np.ndarray, tau_max: int,
                        ske_fixed: float, skv_fixed: float,
                        layer_span_m: float) -> list:
    """
    4-fold expanding-window walk-forward validation for the b_k model.
    Returns list of fold dicts (fold, tau, b_k, S_ske, S_skv, beta, rmse_mm, n_test).
    """
    fold_defs = [
        ("Fold1_test2022", 2015, 2021, 2022),
        ("Fold2_test2023", 2015, 2022, 2023),
        ("Fold3_test2024", 2015, 2023, 2024),
        ("Fold4_test2025", 2015, 2024, 2025),
    ]
    wf_results = []
    yr = merged["datetime"].dt.year

    for label, t0, t1, ty in fold_defs:
        train = (yr >= t0) & (yr <= t1)
        test  = yr == ty
        if test.sum() == 0:
            continue
        best_t, _ = grid_search_tau_bk(y_raw[train], dh_raw[train],
                                       x_raw[train], is_elastic[train], tau_max,
                                       ske_fixed=ske_fixed, skv_fixed=skv_fixed,
                                       layer_span_m=layer_span_m)
        tau_w  = best_t["tau"]
        n_test = test.sum() - tau_w
        if n_test < 1:
            continue
        dh_test = dh_raw[test][tau_w:]
        y_test  = y_raw[test][:n_test]
        x_test  = x_raw[test][:n_test]
        m_test  = is_elastic[test][:n_test]
        driver  = dh_test * m_test * ske_fixed + dh_test * (~m_test) * skv_fixed
        X = np.column_stack([np.ones(n_test), driver, x_test])
        y_pred = X @ [best_t["intercept"], best_t["b_k"], best_t["beta"]]
        rmse   = float(np.sqrt(np.mean((y_test - y_pred) ** 2)))
        wf_results.append({
            "fold":    label,
            "tau":     best_t["tau"],
            "b_k":     best_t["b_k"],
            "S_ske":   best_t["S_ske"],
            "S_skv":   best_t["S_skv"],
            "beta":    best_t["beta"],
            "rmse_mm": rmse,
            "n_test":  str(n_test),
        })
    return wf_results


# ── Diagnostics ───────────────────────────────────────────────────────────────

_BOUND_TOL = 1.01  # coefficient within 1% of its lower bound is considered pinned


def build_diagnostics(corr_yh: float, best: dict, n_inelastic: int,
                      lb_ske: float = 0.0, lb_skv: float = 0.0) -> list:
    """Return list of human-readable warning strings for the result JSON."""
    concerns = []
    if abs(corr_yh) < 0.2:
        concerns.append(
            f"corr(y, dh) = {corr_yh:+.3f} — weak head-compaction coupling")
    if best["r2"] < 0.2:
        concerns.append(f"R2 = {best['r2']:.3f} — low")
    if n_inelastic < 10:
        concerns.append(
            f"only {n_inelastic} inelastic epochs — S_skv data-poor")
    if best["S_ske"] <= lb_ske * _BOUND_TOL and lb_ske > 0:
        concerns.append(
            f"S_ske pinned at lower bound ({lb_ske:.4e} mm/m) — "
            "collinearity likely; elastic channel cannot be cleanly separated from InSAR")
    elif best["S_ske"] <= 0:
        concerns.append(
            "S_ske at zero bound — elastic coefficient could not be positively identified "
            "(check GWL assignment or consider collinearity with InSAR)")
    if best["S_skv"] <= lb_skv * _BOUND_TOL and lb_skv > 0:
        concerns.append(
            f"S_skv pinned at lower bound ({lb_skv:.4e} mm/m) — "
            "inelastic channel constrained by 2S-TOOL prior")
    elif best["S_skv"] <= 0:
        concerns.append(
            "S_skv at zero bound — inelastic coefficient could not be positively identified")
    if best["S_skv"] < best["S_ske"] and best["S_skv"] > lb_skv * _BOUND_TOL:
        concerns.append("S_skv < S_ske — inelastic weaker than elastic (unexpected for alluvial clay)")
    return concerns
