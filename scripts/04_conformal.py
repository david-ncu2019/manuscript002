#!/usr/bin/env python
"""
04_conformal.py — dependency-free split (inductive) conformal prediction.

Used by 05_train_nowcast.py. MAPIE is not installed in `fafalab2`; this gives the
same marginal-coverage guarantee for a fixed point predictor.

Method (absolute-residual split conformal)
------------------------------------------
Given point predictions on a CALIBRATION set (disjoint from training) and on a
TEST set, plus calibration truths:

    scores = |y_cal - point_cal|
    level  = ceil((n+1) * (1 - alpha)) / n      # finite-sample correction
    q      = quantile(scores, level, method="higher")
    interval = [point_test - q, point_test + q]

Marginal coverage P(y in interval) >= 1 - alpha (exchangeability assumption).

Note: imported via importlib because the module filename starts with a digit:
    conf = importlib.import_module("04_conformal")
"""

from __future__ import annotations

import numpy as np


def split_conformal_predict(
    point_cal: np.ndarray,
    y_cal: np.ndarray,
    point_test: np.ndarray,
    alpha: float = 0.10,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Return (lower, upper, q) for nominal coverage 1 - alpha.

    Parameters
    ----------
    point_cal : point predictions on the calibration set.
    y_cal     : true targets on the calibration set.
    point_test: point predictions on the test set.
    alpha     : miscoverage rate (0.10 -> 90% intervals).
    """
    point_cal = np.asarray(point_cal, dtype=float)
    y_cal = np.asarray(y_cal, dtype=float)
    point_test = np.asarray(point_test, dtype=float)

    n = point_cal.shape[0]
    if n == 0:
        raise ValueError("calibration set is empty")

    scores = np.abs(y_cal - point_cal)
    level = np.ceil((n + 1) * (1.0 - alpha)) / n
    level = min(level, 1.0)  # guard tiny n
    q = float(np.quantile(scores, level, method="higher"))

    lower = point_test - q
    upper = point_test + q
    return lower, upper, q


def empirical_coverage(
    y_true: np.ndarray, lower: np.ndarray, upper: np.ndarray
) -> float:
    """Fraction of truths inside [lower, upper]."""
    y_true = np.asarray(y_true, dtype=float)
    inside = (y_true >= np.asarray(lower)) & (y_true <= np.asarray(upper))
    return float(np.mean(inside))


def per_section_split_conformal_predict(
    point_cal: np.ndarray,
    y_cal: np.ndarray,
    section_cal: np.ndarray,
    point_test: np.ndarray,
    section_test: np.ndarray,
    alpha: float = 0.10,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """Mondrian-style conformal: one quantile per section (strata).

    Each test row uses the conformal quantile estimated from its own section's
    calibration residuals. Returns:
        lower, upper : arrays aligned with point_test
        q_by_section : {section_label: q}

    Sections present in test but absent from cal fall back to the pooled q
    (computed across all calibration rows) — flagged in q_by_section under the
    section key with a marker dict.

    Caution: Singh et al. (2024) recommend jackknife+ or transductive conformal
    when per-section calibration sets fall below approximately 30 rows. With the
    012_ml_nowcast v1 split (val = 144 / 6 = 24 per section), per-section q is
    under-sampled and may produce more variable widths than the global mode.
    """
    point_cal = np.asarray(point_cal, dtype=float)
    y_cal = np.asarray(y_cal, dtype=float)
    section_cal = np.asarray(section_cal)
    point_test = np.asarray(point_test, dtype=float)
    section_test = np.asarray(section_test)

    if point_cal.size == 0:
        raise ValueError("calibration set is empty")

    # Pooled fallback q (used only for sections absent from calibration).
    _, _, q_pooled = split_conformal_predict(point_cal, y_cal, point_test, alpha)

    q_by_section: dict = {}
    lower = np.empty_like(point_test)
    upper = np.empty_like(point_test)

    for s in np.unique(section_test):
        mask_cal = (section_cal == s)
        mask_te = (section_test == s)
        if mask_cal.sum() == 0:
            q_s = q_pooled
            q_by_section[str(s)] = {
                "q": float(q_s),
                "n_cal": 0,
                "fallback": "pooled",
            }
        else:
            pc = point_cal[mask_cal]
            yc = y_cal[mask_cal]
            scores = np.abs(yc - pc)
            n = scores.shape[0]
            level = np.ceil((n + 1) * (1.0 - alpha)) / n
            level = min(level, 1.0)
            q_s = float(np.quantile(scores, level, method="higher"))
            q_by_section[str(s)] = {"q": q_s, "n_cal": int(n), "fallback": None}
        lower[mask_te] = point_test[mask_te] - q_s
        upper[mask_te] = point_test[mask_te] + q_s

    return lower, upper, q_by_section
