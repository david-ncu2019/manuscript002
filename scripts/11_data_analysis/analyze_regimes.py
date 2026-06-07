"""
Regime characterization: elastic/inelastic epoch statistics per station-layer.

Computes f_inel, event counts/durations, h_c, yearly and monthly breakdowns.

Usage:
    python scripts/11_data_analysis/analyze_regimes.py
    python scripts/11_data_analysis/analyze_regimes.py --station TUKU

Output: results/data_analysis/regime_characteristics.csv
        results/data_analysis/regime_by_year.csv
"""

import argparse
import json
import numpy as np
import pandas as pd
from pathlib import Path

import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "10_ihmf"))
from ihmf_io import load_and_align

CONFIG_PATH = PROJECT_ROOT / "data/ihmf_config.json"
OUT_DIR = PROJECT_ROOT / "results/data_analysis"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _count_events(mask_inelastic):
    """Count distinct inelastic episodes and their durations."""
    if not mask_inelastic.any():
        return 0, 0.0, 0
    # find contiguous runs of True
    edges = np.diff(np.concatenate([[0], mask_inelastic.astype(int), [0]]))
    starts = np.where(edges == 1)[0]
    stops = np.where(edges == -1)[0]
    durations = stops - starts
    return len(durations), float(durations.mean()), int(durations.max())


def analyze_pair(merged, hc_percentile=10):
    y = merged["mlcw_mm"].values
    h_raw = merged["head_m"].values
    dh = h_raw - h_raw[0]
    h_c = float(np.percentile(h_raw, hc_percentile))
    is_elastic = h_raw > h_c
    n = len(y)
    n_elastic = int(is_elastic.sum())
    n_inelastic = n - n_elastic
    f_inel = n_inelastic / n if n > 0 else 0.0

    n_events, mean_dur, max_dur = _count_events(~is_elastic)

    dh_elastic = dh[is_elastic]
    dh_inelastic = dh[~is_elastic]

    return {
        "f_inel": f_inel,
        "n_elastic": n_elastic,
        "n_inelastic": n_inelastic,
        "n_inelastic_events": n_events,
        "mean_inelastic_duration": mean_dur,
        "max_inelastic_duration": max_dur,
        "h_c_m": round(h_c, 2),
        "h_min": round(float(h_raw.min()), 2),
        "h_max": round(float(h_raw.max()), 2),
        "h_range": round(float(h_raw.max() - h_raw.min()), 2),
        "dh_mean_elastic": round(float(dh_elastic.mean()), 4) if len(dh_elastic) > 0 else np.nan,
        "dh_std_elastic": round(float(dh_elastic.std()), 4) if len(dh_elastic) > 0 else np.nan,
        "dh_mean_inelastic": round(float(dh_inelastic.mean()), 4) if len(dh_inelastic) > 0 else np.nan,
        "dh_std_inelastic": round(float(dh_inelastic.std()), 4) if len(dh_inelastic) > 0 else np.nan,
    }


def main():
    parser = argparse.ArgumentParser(description="Regime characterization")
    parser.add_argument("--station", type=str, default=None, help="Limit to one station")
    args = parser.parse_args()

    with open(CONFIG_PATH) as f:
        cfg = json.load(f)

    entries = cfg["entries"]
    if args.station:
        entries = [e for e in entries if e["station"] == args.station]
        if not entries:
            raise SystemExit(f"No entries for station '{args.station}'")

    insar_csv = PROJECT_ROOT / cfg["shared"]["insar_csv"]
    char_rows = []
    yearly_rows = []
    skipped = 0

    for entry in entries:
        station, layer = entry["station"], entry["layer"]
        try:
            merged, _ = load_and_align(entry, PROJECT_ROOT, insar_csv)
        except Exception:
            skipped += 1
            continue

        char = analyze_pair(merged)
        char_rows.append({"station": station, "layer": layer, "n_epochs": len(merged), **char})

        # yearly breakdown
        h_raw = merged["head_m"].values
        h_c = float(np.percentile(h_raw, 10))
        yr = merged["datetime"].dt.year
        for year in sorted(yr.unique()):
            mask_yr = yr == year
            n_yr = mask_yr.sum()
            if n_yr == 0:
                continue
            n_inel_yr = int((h_raw[mask_yr] <= h_c).sum())
            yearly_rows.append({
                "station": station, "layer": layer,
                "year": int(year), "n_epochs": n_yr,
                "n_inelastic": n_inel_yr,
                "f_inel": n_inel_yr / n_yr,
            })

    df_char = pd.DataFrame(char_rows)
    df_yr = pd.DataFrame(yearly_rows)

    char_path = OUT_DIR / "regime_characteristics.csv"
    yr_path = OUT_DIR / "regime_by_year.csv"
    df_char.to_csv(char_path, index=False, float_format="%.4f")
    df_yr.to_csv(yr_path, index=False, float_format="%.4f")

    print(f"Written: {char_path}  ({len(df_char)} pairs, {skipped} skipped)")
    print(f"Written: {yr_path}  ({len(df_yr)} rows)")

    print(f"\nRegime coverage summary:")
    print(f"  Median f_inel: {df_char['f_inel'].median():.3f}")
    print(f"  Data-poor inelastic (f_inel < 0.10): {(df_char['f_inel'] < 0.10).sum()} / {len(df_char)}")
    print(f"  Zero inelastic epochs: {(df_char['n_inelastic'] == 0).sum()} / {len(df_char)}")
    print(f"  Median inelastic events: {df_char['n_inelastic_events'].median():.0f}")
    print(f"  Median event duration: {df_char['mean_inelastic_duration'].median():.1f} epochs")


if __name__ == "__main__":
    main()
