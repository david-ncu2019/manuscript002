"""
gap_aware_cumsum.py — Gap-aware cumulative compaction (super_plan_2026-06-10 Task 1.3 / D3).

Physical story: a missing 5-day increment is missing KNOWLEDGE, not zero movement. Layers
keep compacting during an instrument gap. The defective pattern `cumsum(fillna(inc, 0))`
writes 0 mm into the record at every missing epoch, which (a) fabricates a flat spot the
model is then trained and graded on, and (b) makes the gap flag impossible to raise because
every epoch looks observed.

The rule (Task 1.3.1):
  - cumulative compaction is the running sum of OBSERVED increments;
  - an epoch whose increment is missing gets b = NaN for THAT epoch only;
  - the running sum continues from the next observed increment (MLCW increments are
    genuine 5-day differences of a continuous instrument, so the datum survives a gap);
  - across a MULTI-epoch gap the post-gap cumulative carries unknown accumulated
    compaction — recorded as a caveat in the census, handled at the carrier-datum level
    by the Part-2 gap census (Task 5.2). For TUKU (1 missing increment at index 0) this
    is negligible.

The guard (Task 1.3.3): refuse to build on any layer where > 20% of increments are
missing; print the census instead. Protects Part 2 from silent fabrication.
"""

from __future__ import annotations

import numpy as np


GAP_FRACTION_LIMIT = 0.20  # Task 1.3.3 — refuse if > 20% of increments missing


class GapFractionExceeded(Exception):
    """Raised when a layer has more missing increments than GAP_FRACTION_LIMIT allows."""


def gap_aware_cumulative(increments: np.ndarray) -> np.ndarray:
    """Running sum of observed increments; NaN increment → NaN at that epoch only.

    The running sum continues across the gap from the next observed increment, i.e.
    the cumulative datum is carried forward (the missing increment contributes 0 to the
    SUM that resumes, but the gap epoch itself is reported as NaN, never as a flat value).

    Parameters
    ----------
    increments : 1-D float array
        5-day MLCW increments (mm), NaN where the increment is missing.

    Returns
    -------
    cum : 1-D float array, same length
        Cumulative compaction. NaN exactly at epochs whose increment was missing;
        observed epochs carry the running sum of observed increments up to and
        including that epoch.
    """
    inc = np.asarray(increments, dtype=float)
    missing = np.isnan(inc)
    # Running sum over observed increments only (missing treated as 0 for the SUM,
    # so the datum is carried forward), then mask the gap epochs back to NaN so they
    # are never reported as a flat observation.
    inc_for_sum = np.where(missing, 0.0, inc)
    cum = np.cumsum(inc_for_sum)
    cum[missing] = np.nan
    return cum


def longest_gap(missing_mask: np.ndarray) -> int:
    """Longest run of consecutive missing (True) increments."""
    m = np.asarray(missing_mask, dtype=bool)
    best = run = 0
    for v in m:
        run = run + 1 if v else 0
        best = max(best, run)
    return int(best)


def census(increments: np.ndarray, layer: str = "", enforce_guard: bool = True) -> dict:
    """Per-layer gap census + optional > 20% guard.

    Returns dict with n_total, n_missing, frac_missing, longest_gap_epochs,
    missing_indices (first 20). Raises GapFractionExceeded if enforce_guard and
    frac_missing > GAP_FRACTION_LIMIT.
    """
    inc = np.asarray(increments, dtype=float)
    missing = np.isnan(inc)
    n_total = int(len(inc))
    n_missing = int(missing.sum())
    frac = n_missing / n_total if n_total else 0.0
    rec = {
        "layer": layer,
        "n_total": n_total,
        "n_missing": n_missing,
        "frac_missing": round(frac, 6),
        "longest_gap_epochs": longest_gap(missing),
        "missing_indices": [int(i) for i in np.where(missing)[0][:20]],
    }
    if enforce_guard and frac > GAP_FRACTION_LIMIT:
        raise GapFractionExceeded(
            f"layer {layer!r}: {n_missing}/{n_total} increments missing "
            f"({100*frac:.1f}%) exceeds {100*GAP_FRACTION_LIMIT:.0f}% limit. "
            f"Census={rec}. Refusing to build cumulative — see Task 1.3.3."
        )
    return rec
