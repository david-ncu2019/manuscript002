"""
GWL proxy quality analysis: assess whether well proximity and screen-depth match
predict IHM-F model success.

Usage:
    python scripts/11_data_analysis/analyze_proxy_quality.py
    python scripts/11_data_analysis/analyze_proxy_quality.py --station TUKU

Output: results/data_analysis/gwl_proxy_quality.csv
"""

import argparse
import json
import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "data/ihmf_config.json"
ASSIGNMENT_CSV = PROJECT_ROOT / "data/gwl/gwl_to_mlcw_layer_assignment_v3.csv"
PAIRS_CSV = PROJECT_ROOT / "data/mlcw/MLCW_InSAR_GWL_pairs_all.csv"
MLCW_TIMELINE_CSV = PROJECT_ROOT / "data/mlcw/MLCW_data_timeline.csv"
OUT_DIR = PROJECT_ROOT / "results/data_analysis"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_ihmf_results(ihmf_dir):
    """Load R² values from existing IHM-F JSON results."""
    results = {}
    jdir = PROJECT_ROOT / ihmf_dir
    if not jdir.exists():
        return results
    for jf in jdir.glob("*_ihmf_results.json"):
        try:
            with open(jf) as f:
                d = json.load(f)
            key = (d["station"], d["layer"])
            results[key] = {
                "r2_ihmf": d.get("r2"),
                "rmse_mm": d.get("rmse_mm"),
                "tau_opt": d.get("tau_opt"),
                "model_path": d.get("model_path"),
                "b_k_m": d.get("b_k_m"),
            }
        except (json.JSONDecodeError, KeyError):
            pass
    return results


def main():
    parser = argparse.ArgumentParser(description="GWL proxy quality analysis")
    parser.add_argument("--station", type=str, default=None, help="Limit to one station")
    args = parser.parse_args()

    with open(CONFIG_PATH) as f:
        cfg = json.load(f)

    entries = cfg["entries"]
    if args.station:
        entries = [e for e in entries if e["station"] == args.station]
        if not entries:
            raise SystemExit(f"No entries for station '{args.station}'")

    # load assignment table for screen-depth + assignment method info
    assign = pd.read_csv(ASSIGNMENT_CSV)
    assign["key"] = assign["station"].astype(str) + "|" + assign["layer"].astype(str)
    assign_lookup = {}
    for _, row in assign.iterrows():
        assign_lookup[row["key"]] = row.to_dict()

    # load MLCW timeline for station coordinates
    mlcw_meta = pd.read_csv(MLCW_TIMELINE_CSV)
    mlcw_coords = {}
    for _, row in mlcw_meta.iterrows():
        mlcw_coords[row["Ename"]] = (row.get("lon", np.nan), row.get("lat", np.nan))

    # load IHM-F results
    ihmf_results = load_ihmf_results("results/ihmf")
    print(f"Loaded {len(ihmf_results)} IHM-F results")

    # load pairs for distance info
    pairs = pd.read_csv(PAIRS_CSV)

    rows = []
    for entry in entries:
        station, layer = entry["station"], entry["layer"]
        wellcode = entry["assigned_wellcode"]

        key = f"{station}|{layer}"
        assign_info = assign_lookup.get(key, {})

        # distance from pairs
        pair_row = pairs[pairs["Ename"] == station]
        dist_km = np.nan
        assignment_method = "UNKNOWN"
        n_candidates = np.nan
        if len(pair_row) > 0:
            pr = pair_row.iloc[0]
            dist_m = pr.get("dist_to_GWL_m", np.nan)
            dist_km = dist_m / 1000.0 if not np.isnan(dist_m) else np.nan
            assignment_method = pr.get("assignment_method", "UNKNOWN")
            # count candidates: wells listed in pairs CSV
            well_cols = [c for c in pair_row.columns if c.startswith("well_")]
            n_candidates = len([c for c in well_cols if pd.notna(pr[c])])

        # screen depth info from assignment
        screen_top = assign_info.get("screen_top_m", np.nan)
        screen_bot = assign_info.get("screen_bot_m", np.nan)
        screen_mid = (screen_top + screen_bot) / 2.0 if not (np.isnan(screen_top) or np.isnan(screen_bot)) else np.nan

        # layer depth range from classify_table
        classify_csv = PROJECT_ROOT / "data/mlcw/group_byLayer_reconstr" / f"{station}_classify_table.csv"
        layer_mid = np.nan
        if classify_csv.exists():
            ct = pd.read_csv(classify_csv)
            layer_depths = ct.loc[ct["layer"] == layer, "depth"]
            if len(layer_depths) > 0:
                layer_mid = (layer_depths.min() + layer_depths.max()) / 2.0

        depth_diff = abs(screen_mid - layer_mid) if not (np.isnan(screen_mid) or np.isnan(layer_mid)) else np.nan

        row = {
            "station": station,
            "layer": layer,
            "wellcode": wellcode,
            "dist_km": round(dist_km, 3) if not np.isnan(dist_km) else np.nan,
            "screen_top_m": screen_top,
            "screen_bot_m": screen_bot,
            "screen_mid_m": screen_mid,
            "layer_mid_m": round(layer_mid, 1) if not np.isnan(layer_mid) else np.nan,
            "depth_diff_m": round(depth_diff, 1) if not np.isnan(depth_diff) else np.nan,
            "assignment_method": assignment_method,
            "n_candidates": n_candidates,
        }

        # add IHM-F results if available
        ir = ihmf_results.get((station, layer), {})
        row.update(ir)

        rows.append(row)

    df = pd.DataFrame(rows)
    out_path = OUT_DIR / "gwl_proxy_quality.csv"
    df.to_csv(out_path, index=False, float_format="%.4f")
    print(f"Written: {out_path}  ({len(df)} station-layer pairs)")

    # summary stats
    has_r2 = df[df["r2_ihmf"].notna()]
    if len(has_r2) > 4:
        near = has_r2[has_r2["dist_km"] < 0.5]
        far = has_r2[has_r2["dist_km"] >= 0.5]
        print(f"\nProxy quality vs IHM-F R²:")
        print(f"  Near wells (<0.5 km): n={len(near)}, median R²={near['r2_ihmf'].median():.3f}")
        print(f"  Far wells  (≥0.5 km): n={len(far)}, median R²={far['r2_ihmf'].median():.3f}")
        print(f"  R² vs distance correlation: r={has_r2['r2_ihmf'].corr(has_r2['dist_km']):+.3f}")
    else:
        print(f"\n  Too few IHM-F results ({len(has_r2)}) for proxy comparison — run IHM-F batch first")


if __name__ == "__main__":
    main()
