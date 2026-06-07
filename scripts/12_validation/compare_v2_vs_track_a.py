"""
compare_v2_vs_track_a.py — Fold-by-fold RMSE comparison: Track B v2 vs Track A anchor.

For each (station, layer) in v2_summary.csv, computes the Track A anchor-only
RMSE on each walk-forward fold and compares it to the Track B v2 RMSE.

Track A anchor formula (static proportionality):
    ŷ_anchor(t) = f̄_k · x_InSAR(t)

This is the simplest physically meaningful baseline: it attributes a fixed
fraction f̄_k of the surface InSAR displacement to layer k, with no GWL input.
Any improvement in Track B v2 RMSE over this baseline is the measurable
contribution of GWL as a co-driver, per CLAUDE.md requirement.

Output:
    results/track_b_vs_a_comparison.csv

    Columns:
        station, layer, fold,
        n_test,
        rmse_v2, rmse_track_a,
        delta_rmse (v2 − track_a; negative = v2 better),
        pct_improvement (100 × (track_a − v2) / track_a; positive = v2 better),
        gamma_k_zero (bool — True: GWL contributed nothing; improvement expected to be ~0)

Usage:
    python scripts/12_validation/compare_v2_vs_track_a.py

Requirements:
    results/ihmf/v2/v2_summary.csv must exist (run batch_v2.py first).
    results/ihmf/v2/{STATION}_{LAYER}_v2_ihmf_results.json per entry (for fold details).
    data/insar/InSAR_measures_at_MLCW.csv (InSAR timeseries).
    data/mlcw/group_byLayer_reconstr/{STATION}_reconst_grouped.csv (MLCW timeseries).
    data/ihmf_config.json (file path registry).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ── Path setup ───────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
_IHMF = _HERE.parent / "10_ihmf"
if str(_IHMF) not in sys.path:
    sys.path.insert(0, str(_IHMF))

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH  = PROJECT_ROOT / "data" / "ihmf_config.json"
SUMMARY_CSV  = PROJECT_ROOT / "results" / "ihmf" / "v2" / "v2_summary.csv"
OUT_CSV      = PROJECT_ROOT / "results" / "track_b_vs_a_comparison.csv"

# Fold label → (train_end_year, test_year)
_FOLD_TEST_YEARS = {
    "Fold1_test2022": 2022,
    "Fold2_test2023": 2023,
    "Fold3_test2024": 2024,
    "Fold4_test2025": 2025,
}


# ── Data loaders ──────────────────────────────────────────────────────────────

def _load_insar(project_root: Path) -> pd.DataFrame:
    """Load InSAR CSV once; return wide-format DataFrame with datetime index."""
    path = project_root / "data" / "insar" / "InSAR_measures_at_MLCW.csv"
    df = pd.read_csv(path, parse_dates=[0])
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={df.columns[0]: "datetime"})
    df["datetime"] = pd.to_datetime(df["datetime"])
    return df


def _load_mlcw(station: str, layer: str, project_root: Path) -> pd.DataFrame:
    """Load layer-grouped MLCW CSV for one station; return datetime + layer column."""
    path = (project_root / "data" / "mlcw" / "group_byLayer_reconstr"
            / f"{station}_reconst_grouped.csv")
    df = pd.read_csv(path, parse_dates=["datetime"])
    df["datetime"] = pd.to_datetime(df["datetime"])
    return df[["datetime", layer]].rename(columns={layer: "mlcw_mm"})


def _align_to_insar(insar_df: pd.DataFrame, station: str,
                    mlcw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Align MLCW to InSAR timeline via merge_asof (nearest).
    Returns DataFrame with columns: datetime, insar_mm (m→mm), mlcw_mm.
    InSAR values are already in mm after *1000 conversion (kept as-is from CSV unit check).
    """
    insar_station = insar_df[["datetime", station]].dropna(subset=[station]).copy()
    # InSAR CSV values are in metres; convert to mm
    insar_station[station] = insar_station[station] * 1000.0
    insar_station = insar_station.rename(columns={station: "insar_mm"})
    insar_sorted = insar_station.sort_values("datetime").reset_index(drop=True)

    mlcw_aligned = pd.merge_asof(
        insar_sorted[["datetime"]],
        mlcw_df.sort_values("datetime"),
        on="datetime", direction="nearest"
    )
    merged = insar_sorted.merge(mlcw_aligned, on="datetime")
    return merged.sort_values("datetime").reset_index(drop=True)


# ── Track A anchor RMSE per fold ──────────────────────────────────────────────

def compute_track_a_rmse(
    merged:   pd.DataFrame,
    f_bar_k:  float,
    test_year: int,
) -> tuple[float | None, int]:
    """
    Compute the Track A anchor-only RMSE for a given test year.

    Track A prediction: ŷ_anchor(t) = f̄_k · x_InSAR(t)
    This is the simplest physically grounded baseline: no GWL, no lag.

    Returns (rmse, n_test). Returns (None, 0) if no test-year rows exist.

    Physical note: f̄_k is the median ratio of MLCW compaction to InSAR
    displacement, computed over the calibration window. Multiplying by the
    current InSAR value gives the expected layer compaction under the
    assumption that the depth-attribution fraction is stable in time.
    """
    mask = merged["datetime"].dt.year == test_year
    test = merged.loc[mask]
    if len(test) == 0:
        return None, 0

    y_obs   = test["mlcw_mm"].values
    y_anchor = f_bar_k * test["insar_mm"].values

    rmse = float(np.sqrt(np.mean((y_obs - y_anchor) ** 2)))
    return rmse, len(test)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    if not SUMMARY_CSV.exists():
        raise SystemExit(
            f"Summary CSV not found: {SUMMARY_CSV}\n"
            "Run scripts/10_ihmf/batch_v2.py first."
        )

    summary = pd.read_csv(SUMMARY_CSV)
    print(f"Loaded v2 summary: {len(summary)} rows")

    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    config_index = {(e["station"], e["layer"]): e for e in cfg["entries"]}

    insar_df = _load_insar(PROJECT_ROOT)
    print("InSAR data loaded.")

    rows = []

    for _, srow in summary.iterrows():
        station  = srow["station"]
        layer    = srow["layer"]
        f_bar_k  = srow["f_bar_k"]
        gamma_zero = bool(srow["gamma_k_zero"])

        # Load per-entry JSON for fold-level details
        json_path = (PROJECT_ROOT / "results" / "ihmf" / "v2"
                     / f"{station}_{layer}_v2_ihmf_results.json")
        if not json_path.exists():
            print(f"  SKIP (no JSON): {station} {layer}")
            continue

        with open(json_path) as f:
            result = json.load(f)

        # Load MLCW and align
        try:
            mlcw_df = _load_mlcw(station, layer, PROJECT_ROOT)
        except (FileNotFoundError, KeyError) as e:
            print(f"  SKIP (MLCW load error): {station} {layer} — {e}")
            continue

        merged = _align_to_insar(insar_df, station, mlcw_df)

        # Build a lookup of v2 fold RMSEs from the JSON
        v2_fold_lookup: dict[str, dict] = {}
        for wf in result.get("walk_forward", []):
            if not wf.get("skipped", False) and wf["rmse_mm"] is not None:
                v2_fold_lookup[wf["fold"]] = wf

        for fold_label, test_year in _FOLD_TEST_YEARS.items():
            # Track A anchor RMSE
            rmse_a, n_test = compute_track_a_rmse(merged, f_bar_k, test_year)
            if rmse_a is None:
                continue  # no test-year data

            # Track B v2 RMSE (from JSON walk-forward)
            v2_entry = v2_fold_lookup.get(fold_label)
            rmse_v2  = v2_entry["rmse_mm"] if v2_entry is not None else None

            delta = (rmse_v2 - rmse_a) if rmse_v2 is not None else None
            pct   = (100.0 * (rmse_a - rmse_v2) / rmse_a
                     if (rmse_v2 is not None and rmse_a > 0) else None)

            rows.append({
                "station":         station,
                "layer":           layer,
                "fold":            fold_label,
                "test_year":       test_year,
                "n_test":          n_test,
                "rmse_v2":         round(rmse_v2, 4) if rmse_v2 is not None else None,
                "rmse_track_a":    round(rmse_a,  4),
                "delta_rmse":      round(delta, 4) if delta is not None else None,
                "pct_improvement": round(pct,   2) if pct   is not None else None,
                "gamma_k_zero":    gamma_zero,
                "v2_fold_present": v2_entry is not None,
            })

    if not rows:
        raise SystemExit("No comparison rows produced — check that v2 JSON files exist.")

    out_df = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT_CSV, index=False)
    print(f"\nComparison CSV written: {OUT_CSV.relative_to(PROJECT_ROOT)}")
    print(f"  Total rows:        {len(out_df)}")

    # ── Summary statistics ────────────────────────────────────────────────────
    valid = out_df.dropna(subset=["rmse_v2", "rmse_track_a"])
    if len(valid) > 0:
        improved = (valid["delta_rmse"] < 0).sum()
        degraded = (valid["delta_rmse"] > 0).sum()
        median_pct = valid["pct_improvement"].median()
        print(f"  Pairs with v2 RMSE: {len(valid)}")
        print(f"  v2 better (delta<0): {improved}  |  v2 worse: {degraded}")
        print(f"  Median % improvement: {median_pct:.1f}%")

        fold1 = valid[valid["fold"] == "Fold1_test2022"]
        if len(fold1) > 0:
            f1_med = fold1["pct_improvement"].median()
            f1_imp = (fold1["delta_rmse"] < 0).sum()
            print(f"  Fold 1 (2022, critical): {len(fold1)} pairs, "
                  f"median improvement {f1_med:.1f}%, "
                  f"{f1_imp}/{len(fold1)} improved")

    print("\nDone.")


if __name__ == "__main__":
    main()
