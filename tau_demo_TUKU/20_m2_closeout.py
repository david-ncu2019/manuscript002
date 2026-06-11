#!/usr/bin/env python
"""20_m2_closeout.py — persist the M2 equivalence check + machine-readable DP1/DP2 fields.
Closes super_plan_2026-06-10 items 2.1.2 and 2.4.2. Read-only on inputs; writes one JSON.
Run: $env:PYTHONPATH=""; conda run -n fafalab2 python tau_demo_TUKU/20_m2_closeout.py
"""
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent / "results"
bake = json.loads((ROOT / "holdout_bakeoff.json").read_text())
old = pd.read_csv(ROOT / "visualization" / "holdout_bakeoff_table_OBSOLETE_prerepair_20260610.csv")
summ = json.loads((ROOT / "reconstruction" / "TUKU_carrier_reconstruction_summary.json").read_text())

# KEY ADAPTATION: CSV uses verbose design strings, not short keys.
# Actual CSV columns: layer, design, rmse_carrier_mm, rmse_bilinear_mm, rmse_baseline_mm,
#                     skill_carrier, skill_bilinear, winner
# CSV design values: "Middle gap (40-70%)" -> JSON key "middle_gap"
#                    "End gap (last 30%)"  -> JSON key "end_gap"
CSV_DESIGN_MAP = {
    "middle_gap": "Middle gap (40–70%)",   # unicode en-dash as in CSV
    "end_gap": "End gap (last 30%)",
}
# Also try ASCII hyphen variant in case the CSV used hyphen instead of en-dash
_middle_gap_variants = ["Middle gap (40–70%)", "Middle gap (40-70%)"]

# Discover actual middle_gap label from CSV
actual_middle_label = None
for candidate in _middle_gap_variants:
    if (old["design"] == candidate).any():
        actual_middle_label = candidate
        break
if actual_middle_label is None:
    raise RuntimeError(
        f"Cannot find middle_gap design label in CSV. Unique values: {old['design'].unique().tolist()}"
    )
CSV_DESIGN_MAP["middle_gap"] = actual_middle_label

key_adaptations = {
    "csv_design_column_values": {
        "middle_gap": CSV_DESIGN_MAP["middle_gap"],
        "end_gap": CSV_DESIGN_MAP["end_gap"],
        "note": (
            "CSV stores verbose design strings; script maps them to JSON short keys "
            "'middle_gap' / 'end_gap' for cross-referencing with holdout_bakeoff.json."
        ),
    }
}

layers = ["F1", "T1", "F2", "T2", "F3", "F4"]
equiv, bilinear_change = {}, {}
for L in layers:
    for design in ("middle_gap", "end_gap"):
        new_c = bake["per_layer"][L][design]["rmse_carrier_mm"]
        new_b = bake["per_layer"][L][design]["rmse_bilinear_mm"]
        csv_design = CSV_DESIGN_MAP[design]
        row = old[(old["layer"] == L) & (old["design"] == csv_design)]
        if len(row) == 0:
            raise RuntimeError(
                f"No CSV row for layer={L}, design='{csv_design}'. "
                f"Available: {old[old['layer']==L]['design'].tolist()}"
            )
        old_c = float(row["rmse_carrier_mm"].iloc[0])
        old_b = float(row["rmse_bilinear_mm"].iloc[0])
        equiv[f"{L}.{design}"] = {"old": old_c, "new": new_c, "abs_delta_mm": abs(new_c - old_c)}
        bilinear_change[f"{L}.{design}"] = {"old": old_b, "new": new_b}

max_delta = max(v["abs_delta_mm"] for v in equiv.values())
tail = summ["tail_evaluation"]
n_pos = sum(1 for L in layers if tail[L]["skill"] > 0)
out = {
    "metadata": {
        "date": "2026-06-11",
        "closes": ["2.1.2", "2.4.2"],
        "sources": [
            "holdout_bakeoff.json",
            "visualization/holdout_bakeoff_table_OBSOLETE_prerepair_20260610.csv",
            "reconstruction/TUKU_carrier_reconstruction_summary.json",
        ],
        "key_adaptations": key_adaptations,
    },
    "carrier_equivalence": {
        "per_cell": equiv,
        "max_abs_delta_mm": max_delta,
        "pass_lt_0p1mm": max_delta < 0.1,
    },
    "bilinear_old_vs_new": bilinear_change,
    "decision_point_1": {
        "verdict": bake["metadata"]["verdict"],
        "rule": "carrier wins/ties >= 4 of 6 layers across both designs",
        "win_counts": bake["win_counts"],
    },
    "decision_point_2": {
        "verdict": "PASS" if n_pos >= 3 else ("PARTIAL" if n_pos >= 1 else "FAIL"),
        "rule": "skill > 0 on >= 3 layers (tail holdout)",
        "skills": {L: tail[L]["skill"] for L in layers},
        "n_positive": n_pos,
    },
}
(ROOT / "m2_closeout.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out["carrier_equivalence"]["per_cell"], indent=2))
print("max |carrier delta| =", max_delta, "mm; DP1 =", out["decision_point_1"]["verdict"],
      "; DP2 =", out["decision_point_2"]["verdict"])
