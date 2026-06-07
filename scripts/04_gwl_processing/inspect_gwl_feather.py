"""
inspect_gwl_feather.py

Reads the GWL timeseries feather files and prints a structural summary:
- Column names, dtypes, shape
- Date range and temporal resolution
- Per-well GWL statistics (mean, min, max, fraction valid)
- Flags stations with multiple wells (multi-screen)

Usage:
    conda run -n fafalab python scripts/04_gwl_processing/inspect_gwl_feather.py
    conda run -n fafalab python scripts/04_gwl_processing/inspect_gwl_feather.py --station TUKU
    conda run -n fafalab python scripts/04_gwl_processing/inspect_gwl_feather.py --all

Outputs a CSV summary to:
    data/gwl/inspection_reports/gwl_feather_inspection.csv
"""

import argparse
import pathlib
import pandas as pd
import numpy as np

FEATHER_DIR = pathlib.Path(
    r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\data\gwl\well_timeseries"
)
OUTPUT_DIR = pathlib.Path(
    r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\data\gwl\inspection_reports"
)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 21 GWL stations co-located with MLCW subsidence stations
MLCW_OVERLAP = {
    "ANHE", "ANNAN", "DONGGUANG", "DONGSHI", "ERLUN", "FENGRONG",
    "GUANGFU", "HAIFENG", "HONGLUN", "HUWEI", "JIAXING", "KECUO",
    "QIAOYI", "TUKU", "XIGANG", "XINGHUA", "XIUTAN", "XIZHOU",
    "YIWU", "ZHENGMIN", "ZHUTANG",
}

INSAR_START = pd.Timestamp("2015-01-21")
INSAR_END   = pd.Timestamp("2025-12-11")


def inspect_one(feather_path: pathlib.Path, verbose: bool = True) -> dict:
    """Load one feather file and return a summary dict."""
    station = feather_path.stem.replace("_gwl_timeseries", "")
    df = pd.read_feather(feather_path)

    # Identify date column (first column or named 'date'/'datetime')
    date_col = df.columns[0]
    well_cols = [c for c in df.columns if c != date_col]

    dates = pd.to_datetime(df[date_col])
    n_rows = len(df)
    date_min = dates.min()
    date_max = dates.max()

    # Temporal resolution: median gap between consecutive dates
    gaps_days = dates.diff().dt.days.dropna()
    median_gap = gaps_days.median()

    # InSAR-overlap window
    mask_insar = (dates >= INSAR_START) & (dates <= INSAR_END)
    n_insar = mask_insar.sum()

    row = {
        "station": station,
        "is_mlcw_overlap": station in MLCW_OVERLAP,
        "n_wells": len(well_cols),
        "well_codes": "|".join(str(c) for c in well_cols),
        "n_rows_total": n_rows,
        "date_min": date_min.strftime("%Y-%m-%d"),
        "date_max": date_max.strftime("%Y-%m-%d"),
        "median_gap_days": median_gap,
        "n_rows_insar_window": int(n_insar),
    }

    # Per-well stats (only within InSAR window)
    df_insar = df.loc[mask_insar, well_cols]
    for wc in well_cols:
        vals = df_insar[wc].dropna().values
        frac_valid = len(vals) / n_insar if n_insar > 0 else float("nan")
        row[f"{wc}_mean_m"] = float(np.mean(vals)) if len(vals) else float("nan")
        row[f"{wc}_min_m"]  = float(np.min(vals))  if len(vals) else float("nan")
        row[f"{wc}_max_m"]  = float(np.max(vals))  if len(vals) else float("nan")
        row[f"{wc}_frac_valid"] = round(frac_valid, 4)

    if verbose:
        print(f"\n{'='*60}")
        print(f"Station : {station}  {'[MLCW overlap]' if station in MLCW_OVERLAP else ''}")
        print(f"File    : {feather_path.name}")
        print(f"Shape   : {df.shape}  (rows × cols)")
        print(f"Columns : {list(df.columns)}")
        print(f"Dtypes  :\n{df.dtypes.to_string()}")
        print(f"Date    : {date_min.date()} → {date_max.date()}  ({n_rows} rows, {median_gap:.0f}-day median gap)")
        print(f"InSAR window ({INSAR_START.date()} – {INSAR_END.date()}): {n_insar} rows")
        print(f"Wells   : {len(well_cols)}")
        for wc in well_cols:
            vals = df_insar[wc].dropna().values
            frac = len(vals) / n_insar if n_insar > 0 else float("nan")
            print(f"  {wc}: mean={np.mean(vals):.2f} m, range=[{np.min(vals):.2f}, {np.max(vals):.2f}], valid={frac:.1%}")
        print(f"\nFirst 5 rows:")
        print(df.head(5).to_string(index=False))

    return row


def inspect_all() -> pd.DataFrame:
    """Inspect all feather files and save summary CSV."""
    feather_files = sorted(FEATHER_DIR.glob("*_gwl_timeseries.feather"))
    if not feather_files:
        print(f"No feather files found in {FEATHER_DIR}")
        return pd.DataFrame()

    print(f"Found {len(feather_files)} feather files.")
    rows = []
    for f in feather_files:
        rows.append(inspect_one(f, verbose=False))

    summary = pd.DataFrame(rows)
    out_path = OUTPUT_DIR / "gwl_feather_inspection.csv"
    summary.to_csv(out_path, index=False)
    print(f"\n{'='*60}")
    print(f"Summary saved → {out_path}")
    print(f"\nOverall stats:")
    print(f"  Total stations : {len(summary)}")
    print(f"  MLCW overlap   : {summary['is_mlcw_overlap'].sum()} stations")
    print(f"  Multi-well     : {(summary['n_wells'] > 1).sum()} stations")
    print(f"  Single-well    : {(summary['n_wells'] == 1).sum()} stations")
    print(f"  Max wells/station: {summary['n_wells'].max()}")
    print(f"\n  Rows in InSAR window (median): {summary['n_rows_insar_window'].median():.0f}")

    mlcw = summary[summary["is_mlcw_overlap"]].copy()
    print(f"\nMLCW-overlap stations ({len(mlcw)}):")
    print(mlcw[["station", "n_wells", "well_codes", "n_rows_insar_window"]].to_string(index=False))

    return summary


def main():
    parser = argparse.ArgumentParser(description="Inspect GWL timeseries feather files.")
    parser.add_argument("--station", type=str, default=None, help="Single station name (e.g. TUKU)")
    parser.add_argument("--all", action="store_true", help="Inspect all stations and save CSV summary")
    args = parser.parse_args()

    if args.station:
        path = FEATHER_DIR / f"{args.station.upper()}_gwl_timeseries.feather"
        if not path.exists():
            print(f"File not found: {path}")
            return
        inspect_one(path, verbose=True)
    elif args.all:
        inspect_all()
    else:
        # Default: inspect TUKU as the diagnostic station + print summary table
        tuku = FEATHER_DIR / "TUKU_gwl_timeseries.feather"
        if tuku.exists():
            inspect_one(tuku, verbose=True)
        print("\nRun with --all to inspect all 100 stations and save CSV.")


if __name__ == "__main__":
    main()
