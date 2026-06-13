"""tmp_audit_20260611_leakage_amplitude.py — independent audit (2026-06-11).

Q3: per-layer amplitude/dynamics mismatch from the carrier reconstruction CSVs.
Also persists Q1 leakage verdicts and the Q2(b) sparse-sampling finding as JSON fields.

Reads ONLY existing files. Writes ONE new file:
    tau_demo_TUKU/results/audit_20260611_leakage_amplitude.json
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent          # tau_demo_TUKU/
RECON = ROOT / "results" / "reconstruction"
OUT = ROOT / "results" / "audit_20260611_leakage_amplitude.json"
LAYERS = ["F1", "T1", "F2", "T2", "F3", "F4"]

result = {"audit_date": "2026-06-11",
          "source_dir": str(RECON),
          "csv_columns": None,
          "per_layer": {}}

for layer in LAYERS:
    p = RECON / f"TUKU_{layer}_reconstruction.csv"
    if not p.exists():
        result["per_layer"][layer] = {"error": f"File not found: {p}"}
        continue
    df = pd.read_csv(p, parse_dates=["date"])
    if result["csv_columns"] is None:
        result["csv_columns"] = list(df.columns)

    obs = df["b_observed_mm"].values.astype(float)
    pred = df["b_model_mm"].values.astype(float)
    dates = df["date"].values

    overlap = np.isfinite(obs) & np.isfinite(pred)
    n_overlap = int(overlap.sum())
    o = obs[overlap]
    pr = pred[overlap]
    d = dates[overlap]

    entry = {"n_rows_csv": int(len(df)),
             "n_overlap_epochs": n_overlap,
             "overlap_start": str(pd.Timestamp(d[0]).date()) if n_overlap else None,
             "overlap_end": str(pd.Timestamp(d[-1]).date()) if n_overlap else None}

    if n_overlap < 10:
        entry["error"] = "Insufficient data - result is undefined."
        result["per_layer"][layer] = entry
        continue

    # (1) 5-day increments: only consecutive overlap pairs exactly 5 days apart,
    # so diffs spanning internal gaps do not contaminate the increment statistics.
    gap_days = np.diff(d).astype("timedelta64[D]").astype(int)
    consec = gap_days == 5
    do = np.diff(o)[consec]
    dp = np.diff(pr)[consec]
    n_pairs = int(consec.sum())
    std_do = float(np.std(do, ddof=1))
    std_dp = float(np.std(dp, ddof=1))
    entry["n_consecutive_5day_pairs"] = n_pairs
    entry["std_diff_obs_mm"] = round(std_do, 4)
    entry["std_diff_pred_mm"] = round(std_dp, 4)
    entry["ratio_pred_over_obs_increment_std"] = round(std_dp / std_do, 4) if std_do > 0 else None
    # (3) max |increment|
    entry["max_abs_diff_obs_mm"] = round(float(np.max(np.abs(do))), 4)
    entry["max_abs_diff_pred_mm"] = round(float(np.max(np.abs(dp))), 4)

    # (2) detrended cumulative series on the overlap (linear fit vs epoch index)
    t = np.arange(n_overlap, dtype=float)
    co = np.polyfit(t, o, 1)
    cp = np.polyfit(t, pr, 1)
    o_dt = o - (co[0] * t + co[1])
    p_dt = pr - (cp[0] * t + cp[1])
    entry["trend_obs_mm_per_epoch"] = round(float(co[0]), 6)
    entry["trend_pred_mm_per_epoch"] = round(float(cp[0]), 6)
    entry["std_detrended_obs_mm"] = round(float(np.std(o_dt, ddof=1)), 4)
    entry["std_detrended_pred_mm"] = round(float(np.std(p_dt, ddof=1)), 4)
    entry["ratio_pred_over_obs_detrended_std"] = (
        round(float(np.std(p_dt, ddof=1) / np.std(o_dt, ddof=1)), 4)
        if np.std(o_dt, ddof=1) > 0 else None)
    if np.std(o_dt) > 1e-12 and np.std(p_dt) > 1e-12:
        entry["pearson_corr_detrended"] = round(float(np.corrcoef(o_dt, p_dt)[0, 1]), 4)
    else:
        entry["pearson_corr_detrended"] = None

    result["per_layer"][layer] = entry

# ── Q2(c) cross-check: NaN census of the MLCW input the M5 map points to ────────
reconst_csv = ROOT.parent / "data" / "mlcw" / "group_byLayer_reconstr" / "TUKU_reconst_grouped.csv"
if reconst_csv.exists():
    rg = pd.read_csv(reconst_csv, parse_dates=["datetime"])
    result["mlcw_input_census"] = {
        "path": "data/mlcw/group_byLayer_reconstr/TUKU_reconst_grouped.csv",
        "columns": list(rg.columns),
        "n_rows": int(len(rg)),
        "date_min": str(rg["datetime"].min().date()),
        "date_max": str(rg["datetime"].max().date()),
        "nan_count_per_column": {c: int(rg[c].isna().sum()) for c in rg.columns if c != "datetime"},
        "has_observed_vs_interpolated_flag": False,
    }
else:
    result["mlcw_input_census"] = {"error": f"File not found: {reconst_csv}"}

# ── Q1 verdicts (from code reading, cited in the audit report) ──────────────────
result["q1_leakage_verdicts"] = {
    "14_carrier_reconstruction_tuku.py": {
        "verdict": "IN-SAMPLE",
        "evidence": ("Calibration mask is every epoch where MLCW+GPS(+u) are finite, no date "
                     "split: lines 197-199; metrics on the same epochs: lines 255-258; "
                     "n_calib = all valid epochs: line 268. Headline b_model_mm column is the "
                     "full-record fit applied everywhere: lines 233-235 / 249-251. "
                     "tail_evaluation block alone is train-only (lines 588-614)."),
    },
    "17_hybrid_model_m3.py": {
        "verdict": "SELECTION-LEAK",
        "evidence": ("Per-design refit on train only (lines 339-341) is clean, but the same "
                     "three held-out segments both SELECT the winner (lines 376-405) and are "
                     "REPORTED as its final skill (lines 406-414, 419-449). Final coefficients "
                     "coef_full are refit on the FULL record (line 366) and stored as "
                     "adopted_coef_full (line 411)."),
    },
    "18_m4_uncertainty_verdict.py": {
        "verdict": "CLEAN-per-design / inherits SELECTION-LEAK",
        "evidence": ("Refit per design on training epochs only: line 149; MAE/RMSE on gap "
                     "epochs only: lines 157-170. But the adopted model identity is read from "
                     "the registry (lines 109-111, 125) that was selected on those identical "
                     "holdout segments, so the apex verdict inherits the selection leak."),
    },
}

# ── Q2(b) finding ───────────────────────────────────────────────────────────────
result["q2b_sampling_decay_simulated"] = {
    "finding": "NO",
    "evidence": ("No 2026-06-10 artifact decimates or sparsely masks MLCW observations. "
                 "Holdouts are contiguous blocks only (middle 40-70%, end 30%, 36-epoch tail: "
                 "17_hybrid_model_m3.py lines 210-225). The synthetic sparse-sampling stress "
                 "test exists only as unchecked plan items: plans/super_plan_2026-06-10.md "
                 "TASK 5.2 lines 543-555. No sparse/monthly/decimation output exists under "
                 "tau_demo_TUKU/results/."),
}

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w") as f:
    json.dump(result, f, indent=2)
print(f"Wrote: {OUT}")

# Console table
print("\nColumns:", result["csv_columns"])
hdr = (f"{'Layer':5s} {'n_ovl':>6s} {'std(dObs)':>10s} {'std(dPred)':>10s} {'ratio':>7s} "
       f"{'stdDT_obs':>10s} {'stdDT_pred':>10s} {'r_DT':>7s} {'max|dO|':>8s} {'max|dP|':>8s}")
print(hdr)
for layer in LAYERS:
    e = result["per_layer"][layer]
    if "error" in e:
        print(f"{layer:5s} {e['error']}")
        continue
    print(f"{layer:5s} {e['n_overlap_epochs']:6d} {e['std_diff_obs_mm']:10.4f} "
          f"{e['std_diff_pred_mm']:10.4f} {e['ratio_pred_over_obs_increment_std']:7.4f} "
          f"{e['std_detrended_obs_mm']:10.4f} {e['std_detrended_pred_mm']:10.4f} "
          f"{e['pearson_corr_detrended']:7.4f} {e['max_abs_diff_obs_mm']:8.4f} "
          f"{e['max_abs_diff_pred_mm']:8.4f}")
