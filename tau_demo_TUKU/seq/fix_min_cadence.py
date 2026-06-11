"""
fix_min_cadence.py — One-shot surgical fix for min_cadence_meeting_L1.

The field was computed with 'actual' included in the ranking ladder and
densest → sparsest traversal with keep-overwriting logic.  That makes
F2/F3/F4 land on 'actual' (the densest irregular schedule) instead of
'annual' (the sparsest regular schedule that still meets both thresholds).

Correct definition
------------------
Ladder (sparsest → densest, regular cadences only):
    ["none", "annual", "semiannual", "quarterly", "monthly"]
"blackout" and "actual" are excluded — neither is a recommended regular cadence.

min_cadence_meeting_L1[layer] = FIRST entry in the ladder for which:
    mae_mm[layer][sched]  <= MAE_threshold[layer]   AND
    rmse_mm[layer][sched] <= RMSE_threshold[layer]

If no entry in the ladder passes, the value is set to "denser_than_monthly".

This script:
    1. Loads cadence_degradation_curve.json (all curve data already correct).
    2. Recomputes min_cadence_meeting_L1 from the file's own rmse_mm/mae_mm/L1_thresholds.
    3. Rewrites the JSON in place, preserving all other fields.
    4. Prints the old vs new mapping.

Usage (PowerShell):
    $env:PYTHONPATH=""; conda run -n fafalab2 python tau_demo_TUKU/seq/fix_min_cadence.py
"""

from __future__ import annotations

import json
from pathlib import Path

_HERE = Path(__file__).resolve()
_TAU_DEMO = _HERE.parent.parent  # tau_demo_TUKU/
JSON_PATH = _TAU_DEMO / "results" / "seq" / "cadence_degradation_curve.json"

# Regular cadence ladder — sparsest first; excludes "blackout" and "actual"
REGULAR_LADDER = ["none", "annual", "semiannual", "quarterly", "monthly"]


def recompute_min_cadence(data: dict) -> dict[str, str]:
    """Return {layer: min_cadence} using the ladder defined above."""
    rmse_mm = data["rmse_mm"]
    mae_mm  = data["mae_mm"]
    thresholds = data["L1_thresholds"]
    layers = list(rmse_mm.keys())

    result: dict[str, str] = {}
    for layer in layers:
        mae_thr  = thresholds[layer]["MAE_mm"]
        rmse_thr = thresholds[layer]["RMSE_mm"]
        found: str | None = None
        for sched in REGULAR_LADDER:          # sparsest first
            mae_v  = mae_mm.get(layer, {}).get(sched)
            rmse_v = rmse_mm.get(layer, {}).get(sched)
            if mae_v is None or rmse_v is None:
                continue
            if mae_v <= mae_thr and rmse_v <= rmse_thr:
                found = sched
                break                         # first passing = sparsest
        result[layer] = found if found is not None else "denser_than_monthly"
    return result


def main() -> None:
    print(f"Loading: {JSON_PATH}")
    with open(JSON_PATH) as f:
        data = json.load(f)

    old_mapping: dict = data.get("min_cadence_meeting_L1", {})
    new_mapping = recompute_min_cadence(data)

    print("\nOLD vs NEW min_cadence_meeting_L1:")
    print(f"  {'Layer':<6}  {'OLD':<20}  {'NEW':<20}  Verification")
    print("  " + "-" * 70)
    layers = list(data["rmse_mm"].keys())
    for layer in layers:
        old_val = old_mapping.get(layer, "<missing>")
        new_val = new_mapping[layer]
        # Show the evidence for the new value
        thr_mae  = data["L1_thresholds"][layer]["MAE_mm"]
        thr_rmse = data["L1_thresholds"][layer]["RMSE_mm"]
        if new_val not in ("denser_than_monthly",):
            mae_v  = data["mae_mm"][layer].get(new_val, float("nan"))
            rmse_v = data["rmse_mm"][layer].get(new_val, float("nan"))
            evidence = (f"MAE={mae_v:.3f}<={thr_mae}, "
                        f"RMSE={rmse_v:.3f}<={thr_rmse} — PASS")
        else:
            evidence = "no ladder schedule meets both thresholds"
        changed = "CHANGED" if old_val != new_val else "unchanged"
        print(f"  {layer:<6}  {str(old_val):<20}  {str(new_val):<20}  {evidence}  [{changed}]")

    # Patch in place
    data["min_cadence_meeting_L1"] = new_mapping

    with open(JSON_PATH, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\nJSON rewritten: {JSON_PATH}")

    # Re-read to confirm
    with open(JSON_PATH) as f:
        verify = json.load(f)
    written = verify["min_cadence_meeting_L1"]
    print("\nRe-read min_cadence_meeting_L1 (on-disk):")
    for layer, val in written.items():
        print(f"  {layer}: {val}")

    assert written == new_mapping, "Re-read mismatch — write failed!"
    print("\nVerification: PASSED — on-disk matches computed mapping.")


if __name__ == "__main__":
    main()
