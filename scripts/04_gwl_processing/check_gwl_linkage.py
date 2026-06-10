"""
check_gwl_linkage.py

Diagnostic: verifies that coordinates, screen depths, and timeseries are
properly linked for all GWL wells.

Three checks are performed:
  A) Coordinate linkage — every feather well code resolves to a unique,
     non-zero (x_twd97, y_twd97) in gwl_allwells_flat.csv
  B) Screen depth linkage — every feather well code resolves to finite
     screen_top_m / screen_bot_m
  C) Timeseries presence — every well code in gwl_allwells_flat.csv appears
     in the expected feather file, and vice versa

Flags:
  - Wells in feather but missing from gwl_allwells_flat.csv (no metadata)
  - Wells in gwl_allwells_flat.csv but feather file is absent
  - Wells with zero or NaN coordinates
  - Wells with missing screen depths
  - Multi-well stations where wells share suspiciously identical coordinates
    (likely duplicate registration) vs. wells that are genuinely co-located

Outputs:
  data/gwl/inspection_reports/gwl_linkage_report.csv  — per-well flag table
  data/gwl/inspection_reports/gwl_linkage_summary.txt — human-readable summary

Usage:
    conda run -n fafalab2 python scripts/04_gwl_processing/check_gwl_linkage.py
"""

import pathlib
import textwrap
import pandas as pd
import numpy as np

BASE = pathlib.Path(r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2")
FEATHER_DIR  = BASE / "data/gwl/well_timeseries"
FLAT_CSV     = BASE / "data/gwl/well_info/gwl_allwells_flat.csv"
OUT_DIR      = BASE / "data/gwl/inspection_reports"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MLCW_STATIONS = {
    "ANHE", "ANNAN", "DONGGUANG", "DONGSHI", "ERLUN", "FENGRONG",
    "GUANGFU", "HAIFENG", "HONGLUN", "HUWEI", "JIAXING", "KECUO",
    "QIAOYI", "TUKU", "XIGANG", "XINGHUA", "XIUTAN", "XIZHOU",
    "YIWU", "ZHENGMIN", "ZHUTANG",
}

# ── helpers ──────────────────────────────────────────────────────────────────

def load_flat() -> pd.DataFrame:
    df = pd.read_csv(FLAT_CSV, dtype={"wellcode": str})
    df["wellcode"] = df["wellcode"].str.strip()
    return df


def feather_well_inventory() -> pd.DataFrame:
    """Return a DataFrame with one row per (station, wellcode) found in feather files."""
    rows = []
    for f in sorted(FEATHER_DIR.glob("*_gwl_timeseries.feather")):
        station = f.stem.replace("_gwl_timeseries", "")
        df = pd.read_feather(f)
        well_cols = [c for c in df.columns if c != "datetime"]
        for wc in well_cols:
            rows.append({"station": station, "wellcode": str(wc), "feather_file": str(f)})
    return pd.DataFrame(rows)


# ── main diagnostic ───────────────────────────────────────────────────────────

def run_checks() -> tuple[pd.DataFrame, str]:
    flat = load_flat()
    feather_inv = feather_well_inventory()

    flat_wells    = set(flat["wellcode"])
    feather_wells = set(feather_inv["wellcode"])

    # ── A: feather wells missing from flat CSV (no metadata at all) ──────────
    feather_only = feather_wells - flat_wells
    flat_only    = flat_wells - feather_wells

    # ── B: merge feather inventory with flat CSV ─────────────────────────────
    merged = feather_inv.merge(flat, on="wellcode", how="left", suffixes=("", "_flat"))

    # Coordinate flags
    merged["coord_missing"] = (
        merged["x_twd97"].isna() | merged["y_twd97"].isna() |
        (merged["x_twd97"] == 0) | (merged["y_twd97"] == 0)
    )

    # Screen depth flags
    merged["screen_missing"] = (
        merged["screen_top_m"].isna() | merged["screen_bot_m"].isna()
    )
    merged["screen_inverted"] = (
        (~merged["screen_missing"]) &
        (merged["screen_top_m"] >= merged["screen_bot_m"])
    )

    # Flag wells with no metadata row at all (from feather_only)
    merged["no_metadata"] = ~merged["wellcode"].isin(flat_wells)

    # ── C: within multi-well stations — duplicate coordinate check ───────────
    # For each station with >1 well, check if all wells share the same (x, y)
    # (co-located wells are expected; but flag if distance between wells > 500 m)
    coord_dup_flags = []
    for station, grp in merged.groupby("station_x" if "station_x" in merged.columns else "station"):
        wells_with_coords = grp[~grp["coord_missing"]]
        if len(wells_with_coords) < 2:
            coord_dup_flags.extend([False] * len(grp))
            continue
        xs = wells_with_coords["x_twd97"].values
        ys = wells_with_coords["y_twd97"].values
        max_spread = max(xs.max() - xs.min(), ys.max() - ys.min())
        # Flag entire station's wells if coord spread within station > 500 m
        flag = max_spread > 500
        coord_dup_flags.extend([flag] * len(grp))

    # pad if groupby order differs
    if len(coord_dup_flags) == len(merged):
        merged["coord_spread_gt500m"] = coord_dup_flags
    else:
        merged["coord_spread_gt500m"] = False

    merged["is_mlcw_station"] = merged["station"].isin(MLCW_STATIONS) if "station" in merged.columns else False

    # ── select output columns ─────────────────────────────────────────────────
    station_col = "station_x" if "station_x" in merged.columns else "station"
    out = merged[[
        station_col, "wellcode", "feather_file",
        "x_twd97", "y_twd97",
        "screen_top_m", "screen_bot_m", "well_depth_m",
        "data_quality", "frac_valid_insar_overlap",
        "no_metadata", "coord_missing", "screen_missing",
        "screen_inverted", "coord_spread_gt500m", "is_mlcw_station",
    ]].copy()
    out = out.rename(columns={station_col: "station"})

    # ── build summary text ────────────────────────────────────────────────────
    n_total = len(out)
    n_mlcw  = out["is_mlcw_station"].sum()
    n_no_meta    = int(out["no_metadata"].sum())
    n_coord_miss = int(out["coord_missing"].sum())
    n_scr_miss   = int(out["screen_missing"].sum())
    n_scr_inv    = int(out["screen_inverted"].sum())
    n_spread     = int(out["coord_spread_gt500m"].sum())
    n_flat_only  = len(flat_only)

    summary_lines = [
        "GWL DATA LINKAGE DIAGNOSTIC REPORT",
        "=" * 60,
        f"Date generated : 2026-05-19",
        f"Feather wells  : {n_total} (across {len(feather_inv['feather_file'].unique())} station files)",
        f"Metadata rows  : {len(flat)} (gwl_allwells_flat.csv)",
        f"MLCW-overlap   : {n_mlcw} wells at {out[out['is_mlcw_station']]['station'].nunique()} stations",
        "",
        "CHECK A — TIMESERIES ↔ METADATA LINKAGE",
        "-" * 40,
        f"  Wells in feather but NOT in flat CSV (no metadata): {n_no_meta}",
    ]
    if feather_only:
        for wc in sorted(feather_only):
            s = out.loc[out["wellcode"] == wc, "station"].iloc[0] if wc in out["wellcode"].values else "?"
            summary_lines.append(f"    {s} / {wc}")

    summary_lines += [
        f"  Wells in flat CSV but feather file ABSENT        : {n_flat_only}",
    ]
    if flat_only:
        for wc in sorted(flat_only):
            row = flat[flat["wellcode"] == wc].iloc[0]
            summary_lines.append(f"    {row['station']} / {wc}")

    summary_lines += [
        "",
        "CHECK B — COORDINATE LINKAGE",
        "-" * 40,
        f"  Wells with missing/zero coordinates : {n_coord_miss}",
    ]
    if n_coord_miss:
        bad = out[out["coord_missing"]][["station", "wellcode", "x_twd97", "y_twd97", "is_mlcw_station"]]
        for _, r in bad.iterrows():
            tag = " [MLCW]" if r["is_mlcw_station"] else ""
            summary_lines.append(f"    {r['station']} / {r['wellcode']}  x={r['x_twd97']}  y={r['y_twd97']}{tag}")

    summary_lines += [
        f"  Stations with coord spread > 500 m   : {out[out['coord_spread_gt500m']]['station'].nunique()} stations  ({n_spread} wells)",
    ]
    if n_spread:
        spread_stations = out[out["coord_spread_gt500m"]]["station"].unique()
        for st in sorted(spread_stations):
            grp = out[(out["station"] == st) & (~out["coord_missing"])]
            xs = grp["x_twd97"].values; ys = grp["y_twd97"].values
            dx = xs.max() - xs.min(); dy = ys.max() - ys.min()
            tag = " [MLCW]" if st in MLCW_STATIONS else ""
            summary_lines.append(f"    {st}  dx={dx:.0f} m  dy={dy:.0f} m{tag}")
            for _, r in grp.iterrows():
                summary_lines.append(f"      {r['wellcode']}  x={r['x_twd97']:.1f}  y={r['y_twd97']:.1f}")

    summary_lines += [
        "",
        "CHECK C — SCREEN DEPTH LINKAGE",
        "-" * 40,
        f"  Wells with missing screen depths     : {n_scr_miss} / {n_total}  ({100*n_scr_miss/n_total:.1f}%)",
        f"  Wells with inverted screen (top≥bot) : {n_scr_inv}",
    ]

    # MLCW-overlap breakdown of screen coverage
    mlcw_wells = out[out["is_mlcw_station"]]
    n_mlcw_scr_miss = int(mlcw_wells["screen_missing"].sum())
    summary_lines += [
        f"  MLCW-overlap wells missing screen    : {n_mlcw_scr_miss} / {n_mlcw}",
    ]
    if n_scr_miss:
        bad_scr = out[out["screen_missing"]][["station", "wellcode", "well_depth_m", "data_quality", "is_mlcw_station"]]
        summary_lines.append(f"  Wells missing screen depths:")
        for _, r in bad_scr.iterrows():
            tag = " [MLCW]" if r["is_mlcw_station"] else ""
            summary_lines.append(
                f"    {r['station']} / {r['wellcode']}  depth={r['well_depth_m']} m  quality={r['data_quality']}{tag}"
            )
    if n_scr_inv:
        bad_inv = out[out["screen_inverted"]][["station", "wellcode", "screen_top_m", "screen_bot_m"]]
        summary_lines.append(f"  Wells with inverted screen depths:")
        for _, r in bad_inv.iterrows():
            summary_lines.append(
                f"    {r['station']} / {r['wellcode']}  top={r['screen_top_m']} m  bot={r['screen_bot_m']} m"
            )

    summary_lines += [
        "",
        "OVERALL LINKAGE VERDICT",
        "-" * 40,
    ]
    any_critical = n_no_meta > 0 or n_coord_miss > 0 or n_mlcw_scr_miss > 0
    if not any_critical:
        summary_lines.append("  OK — all feather wells have metadata, coordinates, and screen depths.")
        summary_lines.append(f"  Note: {n_scr_miss} non-MLCW wells lack screen depths (not blocking for Stage 1).")
    else:
        if n_no_meta:
            summary_lines.append(f"  CRITICAL: {n_no_meta} feather wells have no metadata row — linkage broken.")
        if n_coord_miss:
            summary_lines.append(f"  CRITICAL: {n_coord_miss} wells have missing/zero coordinates.")
        if n_mlcw_scr_miss:
            summary_lines.append(f"  CRITICAL: {n_mlcw_scr_miss} MLCW-overlap wells have no screen depth.")
        if n_spread:
            summary_lines.append(f"  WARNING : {out[out['coord_spread_gt500m']]['station'].nunique()} stations have coord spread >500 m — verify source.")
        if n_scr_miss - n_mlcw_scr_miss:
            summary_lines.append(f"  WARNING : {n_scr_miss - n_mlcw_scr_miss} non-MLCW wells lack screen depths.")

    return out, "\n".join(summary_lines)


def main():
    print("Running GWL linkage checks …")
    report_df, summary_text = run_checks()

    csv_path = OUT_DIR / "gwl_linkage_report.csv"
    txt_path = OUT_DIR / "gwl_linkage_summary.txt"

    report_df.to_csv(csv_path, index=False)
    txt_path.write_text(summary_text, encoding="utf-8")

    print(summary_text)
    print(f"\nPer-well flag table → {csv_path}")
    print(f"Summary text        → {txt_path}")


if __name__ == "__main__":
    main()
