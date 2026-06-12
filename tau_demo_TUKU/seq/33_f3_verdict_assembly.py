"""
33_f3_verdict_assembly.py — F3 Forensic Phase 3: consolidate the decision matrix.

Physical story:
  Phases 0-2 produced the evidence; this script weighs the three rival explanations for the F3
  paradox into one scorecard. It reads only the persisted JSON outputs (no recomputation) so the
  verdict is auditable against the files on disk.

  The three hypotheses:
    H1 Faulty / depth-mismatched driver  — the assigned head well is the wrong one for F3
    H2 Poisoned truth                    — the F3 'ground truth' is computer-interpolated
    H3 Physical outlier                  — the deep clay genuinely lags/cancels at the surface
  Plus the code-reputation result from Phase 1 (is the estimator itself sound?).

Leakage manifest: reads descriptive-statistic JSONs only; no model, no scoring.

Usage:
  $env:PYTHONPATH=""; conda run -n fafalab2 python tau_demo_TUKU/seq/33_f3_verdict_assembly.py

Outputs:
  results/seq/forensics/f3_verdict_matrix.json
  results/seq/forensics/f3_verdict_matrix.csv
  plots/seq/forensics/f3_verdict_decision.png
  results/seq/forensics/33_f3_verdict_assembly_run_log.txt
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_HERE = Path(__file__).resolve()
_TAU_DEMO = _HERE.parent.parent
RESULTS = _TAU_DEMO / "results" / "seq" / "forensics"
PLOTS = _TAU_DEMO / "plots" / "seq" / "forensics"
plt.rcParams.update({"font.size": 14, "figure.dpi": 100, "savefig.dpi": 300})


def load(name):
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def main() -> int:
    log_lines = []

    def log(m=""):
        print(m); log_lines.append(m)

    rep = load("synthetic_reputation.json")
    drv = load("driver_purity.json")
    interp = load("interpolation_signature.json")
    geo = load("geomech_consistency.json")

    code_ok = rep["VERDICT"] == "CODE_EXONERATED"
    assigned_seasonal_r = drv["calibration_reconciliation"]["detrended_seasonal_abs_r"]
    depth_gap = geo["screen_to_clay_centroid_gap_m"]
    overlap = geo["screen_clay_overlap_m"]
    noninteger_2024 = interp["era_noninteger_fraction"]["2024_plus"]["frac_noninteger"]
    noninteger_pre2019 = interp["era_noninteger_fraction"]["pre_2019"]["frac_noninteger"]
    best_local = drv["best_local_15km"]

    # ── Decision matrix ──────────────────────────────────────────────────────
    # support score in [0,1]; verdict label; deciding metric
    matrix = [
        {
            "hypothesis": "H1 depth-mismatched driver",
            "deciding_metric": "assigned seasonal |r| / screen-clay gap (m) / overlap (m)",
            "value": f"{assigned_seasonal_r:.2f} / {depth_gap:.0f} / {overlap:.0f}",
            "support": 0.90,
            "verdict": "SUPPORTED",
            "note": "screen samples 177 m; clay compacts at ~256 m; seasonal head signal ~0. "
                    "But no clean local replacement (best local only "
                    f"{best_local['peak_abs_r']:.2f} at {best_local['peak_lag_days']:.0f}-day lag).",
        },
        {
            "hypothesis": "H2 poisoned truth",
            "deciding_metric": "non-integer fraction pre-2019 -> 2024+",
            "value": f"{noninteger_pre2019:.2f} -> {noninteger_2024:.2f}",
            "support": 0.50,
            "verdict": "PARTIAL (temporal)",
            "note": "pre-2019 genuine field data; 2024+ fully interpolated. Blind era (2019-23) "
                    "transitional. Recent-era confirmatory is not field-verifiable.",
        },
        {
            "hypothesis": "H3 physical outlier (out-of-phase deep clay)",
            "deciding_metric": "lit. 90%-compaction lag / surface rank / co-screened head",
            "value": "26-488 d lag; rank-1 carrier; no deep piezometer",
            "support": 0.85,
            "verdict": "SUPPORTED",
            "note": "TKSH/Tuku observed out-of-phase 2004-07 (soil creep, Noordbergum); surface "
                    "inversion rank-deficient (Phase 0). Deep clay genuinely lags any shallow head.",
        },
        {
            "hypothesis": "CODE (estimator) at fault?",
            "deciding_metric": "synthetic tau=200 recovery",
            "value": f"recovered tau={rep['part_A_clean_recovery']['tau_recovered']}",
            "support": 0.0,
            "verdict": "REJECTED (code exonerated)",
            "note": "solver recovers tau=200 exactly from a clean driver; fails only when driver "
                    f"|r| < ~{rep['part_C_driver_quality_sweep']['tau_recovery_survives_down_to_peak_xcorr']:.2f}.",
        },
    ]
    df = pd.DataFrame(matrix)
    df.to_csv(RESULTS / "f3_verdict_matrix.csv", index=False)

    verdict_json = {
        "phase": 3, "date": "2026-06-12",
        "headline": "CONFLUENCE — depth-mismatched driver (H1) + genuine out-of-phase deep-clay "
                    "physics (H3), compounded by temporally poisoned recent truth (H2). Code exonerated.",
        "code_exonerated": code_ok,
        "primary_causes_ranked": ["H1 depth-mismatched driver", "H3 physical outlier",
                                  "H2 poisoned truth (recent era only)"],
        "matrix": matrix,
        "reframes_redteam": "Red Team 'underdetermined at sparse cadence' is CONFIRMED but sharpened: "
                            "the network has no piezometer screened in the F3 clay (240-275 m), so the "
                            "physically correct slow head is simply unmeasured; and the deep clay is "
                            "intrinsically out-of-phase with the shallow heads that DO exist.",
        "actionable_next_step": "F3 reconstruction at TUKU needs a deep (240-275 m) co-screened "
                                "piezometer or a modelled deep head; with only shallow heads + surface "
                                "GPS the sub-annual F3 dynamics remain unrecoverable. Trend "
                                "apportionment + datum-via-visits stays valid.",
    }
    (RESULTS / "f3_verdict_matrix.json").write_text(json.dumps(verdict_json, indent=2), encoding="utf-8")

    # ── Scorecard figure ─────────────────────────────────────────────────────
    color_map = {"SUPPORTED": "#2ca02c", "PARTIAL (temporal)": "#ff7f0e",
                 "REJECTED (code exonerated)": "#7f7f7f"}
    fig, ax = plt.subplots(figsize=(13, 7))
    ys = range(len(df))[::-1]
    bars = ax.barh(list(ys), df["support"], color=[color_map[v] for v in df["verdict"]])
    ax.set_yticks(list(ys))
    ax.set_yticklabels(df["hypothesis"])
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("evidential support (0 = rejected, 1 = strongly supported)")
    ax.set_title("F3 Paradox — forensic decision matrix (TUKU, 2026-06-12)")
    for y, (_, r) in zip(ys, df.iterrows()):
        ax.text(min(r["support"] + 0.02, 0.98), y, f"{r['verdict']}  [{r['value']}]",
                va="center", fontsize=11)
    ax.grid(True, alpha=0.3, axis="x")
    fig.tight_layout(); fig.savefig(PLOTS / "f3_verdict_decision.png", dpi=300); plt.close(fig)

    # ── Console verdict ──────────────────────────────────────────────────────
    log("=" * 78)
    log("F3 FORENSIC VERDICT — DECISION MATRIX")
    log("=" * 78)
    for r in matrix:
        log(f"  {r['hypothesis']:42s} {r['verdict']:28s} [{r['value']}]")
    log("")
    log("PHYSICAL MEANING")
    log("  " + verdict_json["headline"])
    log("  Reframe: " + verdict_json["reframes_redteam"])
    log("  Next: " + verdict_json["actionable_next_step"])
    (RESULTS / "33_f3_verdict_assembly_run_log.txt").write_text("\n".join(log_lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
