"""
test_gap_aware.py — Unit checks for the gap-aware cumulative builder (Task 1.3).

Proves three things and persists the result:
  (1) D3 fix: a missing increment becomes NaN at THAT epoch only, never a fabricated zero;
      the running sum continues from the next observed increment.
  (2) Census at TUKU: exactly 1 of 1,572 increments missing per layer, at index 0.
  (3) Guard (Task 1.3.3): a layer with > 20% missing increments raises GapFractionExceeded.

Usage:
    PYTHONPATH="" conda run -n fafalab2 python tau_demo_TUKU/test_gap_aware.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tau_demo_TUKU"))
from gap_aware_cumsum import (
    gap_aware_cumulative, census, longest_gap,
    GapFractionExceeded, GAP_FRACTION_LIMIT,
)

INC_FEATHER = ROOT / "tau_demo_TUKU" / "data" / "incremental_data" / "mlcw_diff_cleaned.feather"
OUT_JSON = ROOT / "tau_demo_TUKU" / "results" / "gap_aware_test.json"


def test_synthetic_nan_propagation() -> dict:
    """A NaN increment yields NaN at that epoch only; the running sum resumes after."""
    inc = np.array([1.0, np.nan, 2.0, 3.0])
    cum = gap_aware_cumulative(inc)
    # Expected: [1, NaN, 3, 6]  (1; gap; 1+0+2=3; 3+3=6)
    expected = np.array([1.0, np.nan, 3.0, 6.0])
    finite = np.isfinite(expected)
    ok_finite = bool(np.allclose(cum[finite], expected[finite]))
    ok_nan = bool(np.isnan(cum[1]) and np.isfinite(cum[0]) and np.isfinite(cum[2]))
    # Counter: the OLD fillna(0).cumsum() would give [1, 1, 3, 6] — a fabricated flat at idx 1
    old_fill = np.cumsum(np.where(np.isnan(inc), 0.0, inc))
    old_fabricates_flat = bool(old_fill[1] == 1.0 and not np.isnan(old_fill[1]))
    return {
        "cum": [None if np.isnan(x) else round(float(x), 4) for x in cum],
        "expected": [None if np.isnan(x) else round(float(x), 4) for x in expected],
        "nan_only_at_gap": ok_nan,
        "running_sum_resumes": ok_finite,
        "old_zerofill_fabricated_flat_at_gap": old_fabricates_flat,
        "passed": bool(ok_finite and ok_nan),
    }


def test_tuku_census() -> dict:
    """Exactly 1 missing increment per layer, at index 0 (measured 2026-06-10)."""
    df = pd.read_feather(INC_FEATHER)
    per_layer = {}
    all_ok = True
    for col in [c for c in df.columns if c != "datetime"]:
        rec = census(df[col].values, layer=col, enforce_guard=True)
        # gap-aware cumulative must have NaN exactly at the missing-increment indices
        cum = gap_aware_cumulative(df[col].values)
        nan_idx = list(np.where(np.isnan(cum))[0])
        ok = bool(rec["n_missing"] == 1 and rec["missing_indices"] == [0]
                  and nan_idx == [0])
        all_ok = all_ok and ok
        per_layer[col] = {
            "n_total": rec["n_total"],
            "n_missing": rec["n_missing"],
            "missing_indices": rec["missing_indices"],
            "longest_gap_epochs": rec["longest_gap_epochs"],
            "cum_nan_indices": [int(i) for i in nan_idx],
            "matches_expected_1_at_idx0": ok,
        }
    return {"per_layer": per_layer, "passed": bool(all_ok)}


def test_guard_over_20pct() -> dict:
    """A layer with > 20% missing increments must raise GapFractionExceeded."""
    n = 100
    inc = np.arange(n, dtype=float)
    inc[:30] = np.nan  # 30% missing — over the 20% limit
    raised = False
    msg = ""
    try:
        census(inc, layer="SYNTH_BAD", enforce_guard=True)
    except GapFractionExceeded as e:
        raised = True
        msg = str(e)[:120]
    # And a layer at 10% must NOT raise
    inc2 = np.arange(n, dtype=float)
    inc2[:10] = np.nan
    not_raised = True
    try:
        census(inc2, layer="SYNTH_OK", enforce_guard=True)
    except GapFractionExceeded:
        not_raised = False
    return {
        "limit_fraction": GAP_FRACTION_LIMIT,
        "over_limit_raised": raised,
        "over_limit_msg": msg,
        "under_limit_passed": not_raised,
        "passed": bool(raised and not_raised),
    }


def main():
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    print("=" * 75)
    print("Gap-aware cumulative — unit checks (Task 1.3)")
    print("=" * 75)

    t1 = test_synthetic_nan_propagation()
    print("\n── (1) NaN propagation ──")
    print(f"  cum={t1['cum']}  expected={t1['expected']}")
    print(f"  nan_only_at_gap={t1['nan_only_at_gap']}  running_sum_resumes={t1['running_sum_resumes']}")
    print(f"  old zero-fill fabricates flat at gap = {t1['old_zerofill_fabricated_flat_at_gap']}")
    print(f"  → {'PASS' if t1['passed'] else 'FAIL'}")

    t2 = test_tuku_census()
    print("\n── (2) TUKU census (1 missing per layer at idx 0) ──")
    for lyr, r in t2["per_layer"].items():
        print(f"  {lyr}: {r['n_missing']}/{r['n_total']} missing at {r['missing_indices']}, "
              f"cum NaN at {r['cum_nan_indices']}, longest gap {r['longest_gap_epochs']}  "
              f"→ {'PASS' if r['matches_expected_1_at_idx0'] else 'FAIL'}")
    print(f"  overall → {'PASS' if t2['passed'] else 'FAIL'}")

    t3 = test_guard_over_20pct()
    print("\n── (3) > 20% guard ──")
    print(f"  over-limit (30%) raised GapFractionExceeded = {t3['over_limit_raised']}")
    print(f"  under-limit (10%) passed = {t3['under_limit_passed']}")
    print(f"  → {'PASS' if t3['passed'] else 'FAIL'}")

    out = {
        "description": "Gap-aware cumulative unit checks (super_plan_2026-06-10 Task 1.3)",
        "nan_propagation": t1,
        "tuku_census": t2,
        "guard_over_20pct": t3,
        "all_passed": bool(t1["passed"] and t2["passed"] and t3["passed"]),
    }
    with open(OUT_JSON, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\n  Saved: {OUT_JSON}")
    print(f"  ALL PASSED: {out['all_passed']}")
    return out


if __name__ == "__main__":
    res = main()
    sys.exit(0 if res["all_passed"] else 1)
