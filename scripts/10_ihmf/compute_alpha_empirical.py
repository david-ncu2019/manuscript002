"""
compute_alpha_empirical.py — Empirical α from monthly MLCW vs GPS/InSAR OLS.

Physical rationale:
    The Step 2 equation α · d_v(t) = Σ_j S_j · ΔH_j(t−τ_j) defines α as the
    fraction of total surface displacement explained by modelled layer compaction.
    When the GPS record starts after the main inelastic consolidation period, the
    OLS fit in Step 2 recovers a spuriously small α (≈ 0.034 at TUKU) because
    elastic-only oscillations cancel in cumulation.

    The empirical α bypasses this artifact: monthly-total MLCW (sum of all 6
    layers, the quantity Step 1 models) is regressed against monthly-total GPS
    (or InSAR) over their common record.  The slope is the observed proportionality
    between surface displacement and subsurface compaction, free of GWL-model
    assumptions.  α_empirical = 1 / slope.

    For TUKU (GPS available): GPS = 1.58 × MLCW, R² = 0.991, N = 180 months
                             → α = 1 / 1.58 = 0.634.

    For other stations (InSAR only): use monthly-averaged InSAR from the
    MLCW-aligned InSAR feather file.  These stations lack independent GPS, so
    the empirical α is based on the InSAR–MLCW monthly relationship.

Output: results/ihmf/alpha_empirical.csv
    Columns: station, alpha, r2, N_months, source
    TUKU row: TUKU, 0.634, 0.991, 180, GPS

Usage:
    python scripts/10_ihmf/compute_alpha_empirical.py
    python scripts/10_ihmf/compute_alpha_empirical.py --station TUKU
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))


def compute_alpha_gps(station: str, tau_demo_dir: Path) -> dict | None:
    """
    Compute α from monthly GPS vs MLCW CSV (e.g. TUKU).

    CSV format: datetime, GPS_modeled_monthly, MLCW_totalcompact_monthly
    Returns dict with keys: station, alpha, r2, N_months, source, slope, intercept
    Returns None if CSV not found.
    """
    csv_path = tau_demo_dir / "data" / f"{station}_gps_mlcw_monthly.csv"
    if not csv_path.exists():
        return None

    df = pd.read_csv(csv_path)
    gps = df["GPS_modeled_monthly"].values.astype(float)   # mm, negative = subsidence
    mlcw = df["MLCW_totalcompact_monthly"].values.astype(float)  # mm, negative = compaction

    finite = np.isfinite(gps) & np.isfinite(mlcw)
    gps, mlcw = gps[finite], mlcw[finite]
    n = len(gps)

    if n < 12:
        print(f"  [alpha-gps] {station}: only {n} valid months — insufficient (need ≥ 12)")
        return None

    # OLS: GPS = slope * MLCW + intercept (through-origin regression on cumulative
    # displacement — no intercept because both are zero-referenced to REF_DATE)
    slope = float(np.dot(mlcw, gps) / np.dot(mlcw, mlcw))
    gps_pred = slope * mlcw
    ss_res = float(np.sum((gps - gps_pred) ** 2))
    ss_tot = float(np.sum((gps - gps.mean()) ** 2))
    r2 = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else np.nan

    # α = 1/slope: fraction of total displacement explained by modelled compaction
    # When GPS = 1.58 × MLCW, the modelled compaction is 63.4% of total displacement
    alpha = float(1.0 / slope) if slope != 0 else np.nan

    print(f"  [alpha-gps] {station}: GPS = {slope:.3f} × MLCW, "
          f"α = {alpha:.4f}, R² = {r2:.4f}, N = {n} months")

    return {
        "station": station, "alpha": alpha, "r2": r2, "N_months": n,
        "source": "GPS", "slope": slope, "intercept": 0.0,
    }


def compute_alpha_insar_monthly(
    station: str,
    mlcw_dir: Path,
    insar_feather_path: Path | None,
) -> dict | None:
    """
    Compute α from monthly-averaged MLCW vs monthly-averaged InSAR.

    Reads: {STATION}_reconst_grouped.csv from mlcw_dir for MLCW.
    Reads: InSAR from feather file (station × epoch wide format).

    Returns dict or None if data unavailable.
    """
    # 1. Load MLCW monthly
    mlcw_csv = mlcw_dir / f"{station}_reconst_grouped.csv"
    if not mlcw_csv.exists():
        print(f"  [alpha-insar] {station}: MLCW CSV not found — skip")
        return None

    mlcw_df = pd.read_csv(mlcw_csv)
    mlcw_df["datetime"] = pd.to_datetime(mlcw_df["datetime"])
    mlcw_df = mlcw_df.set_index("datetime").sort_index()

    # Sum all 6 layer columns to get total compaction
    layer_cols = [c for c in mlcw_df.columns if c in ("F1", "T1", "F2", "T2", "F3", "F4")]
    if not layer_cols:
        print(f"  [alpha-insar] {station}: no layer columns in MLCW CSV — skip")
        return None
    mlcw_total = mlcw_df[layer_cols].sum(axis=1)

    # Resample to month-end mean (MLCW is 5-day cadence)
    mlcw_monthly = mlcw_total.resample("ME").mean()

    # 2. Load InSAR monthly (try feather, fall back to CSV)
    insar_series = None

    if insar_feather_path and insar_feather_path.exists():
        try:
            insar_feather = pd.read_feather(insar_feather_path)
            # Feather is wide: one row per station, columns are epoch datetimes + metadata
            # Find the row for this station
            station_col = [c for c in insar_feather.columns
                          if c.lower() in ("station", "name", "id")][:1]
            if station_col:
                mask = insar_feather[station_col[0]].str.strip() == station
                if mask.any():
                    idx = mask[mask].index[0]
                    # Convert epoch columns (date strings) to Series
                    meta_cols = station_col + ["lon", "lat", "elev", "percent"]
                    epoch_cols = [c for c in insar_feather.columns if c not in meta_cols]
                    insar_series = insar_feather.loc[idx, epoch_cols].astype(float)
                    insar_series.index = pd.to_datetime(insar_series.index)
                    insar_series = insar_series.sort_index()
        except Exception as e:
            print(f"  [alpha-insar] {station}: feather read error — {e}")

    if insar_series is None:
        print(f"  [alpha-insar] {station}: no InSAR data source available — skip")
        return None

    # Resample InSAR to month-end mean
    insar_monthly = insar_series.resample("ME").mean()

    # Align on common months
    common = mlcw_monthly.index.intersection(insar_monthly.index)
    if len(common) < 12:
        print(f"  [alpha-insar] {station}: only {len(common)} common months — insufficient")
        return None

    insar_aligned = insar_monthly[common].values.astype(float)
    mlcw_aligned = mlcw_monthly[common].values.astype(float)

    finite = np.isfinite(insar_aligned) & np.isfinite(mlcw_aligned)
    insar_aligned, mlcw_aligned = insar_aligned[finite], mlcw_aligned[finite]
    n = len(insar_aligned)

    if n < 12:
        print(f"  [alpha-insar] {station}: only {n} finite months — insufficient")
        return None

    # OLS: InSAR = slope * MLCW (through origin — both zero-referenced)
    slope = float(np.dot(mlcw_aligned, insar_aligned) / np.dot(mlcw_aligned, mlcw_aligned))
    insar_pred = slope * mlcw_aligned
    ss_res = float(np.sum((insar_aligned - insar_pred) ** 2))
    ss_tot = float(np.sum((insar_aligned - insar_aligned.mean()) ** 2))
    r2 = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else np.nan

    alpha = float(1.0 / slope) if slope != 0 else np.nan

    print(f"  [alpha-insar] {station}: InSAR = {slope:.3f} × MLCW, "
          f"α = {alpha:.4f}, R² = {r2:.4f}, N = {n} months")

    return {
        "station": station, "alpha": alpha, "r2": r2, "N_months": n,
        "source": "InSAR", "slope": slope, "intercept": 0.0,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Compute empirical α = 1/slope from monthly MLCW vs GPS/InSAR OLS"
    )
    parser.add_argument("--station", default=None,
                       help="Compute for a single station (default: all 37)")
    args = parser.parse_args()

    tau_demo_dir = ROOT / "tau_demo_TUKU"
    mlcw_dir = ROOT / "data" / "mlcw" / "group_byLayer_reconstr"
    insar_feather = ROOT / "data" / "insar" / "mlcw_interp_insar_IDW_extend.feather"

    # Collect all 37 stations from MLCW directory
    all_stations = sorted(
        f.replace("_reconst_grouped.csv", "")
        for f in [p.name for p in mlcw_dir.glob("*_reconst_grouped.csv")]
    )

    stations = [args.station] if args.station else all_stations

    if not stations:
        print("No stations found. Check data/mlcw/group_byLayer_reconstr/")
        return

    results: list[dict] = []

    for station in stations:
        # Try GPS first (only TUKU currently has GPS monthly CSV)
        result = compute_alpha_gps(station, tau_demo_dir)

        # Fall back to InSAR
        if result is None:
            result = compute_alpha_insar_monthly(station, mlcw_dir, insar_feather)

        if result is not None:
            results.append(result)

    if not results:
        print("No α values computed. Check data availability.")
        return

    # Write CSV
    out_dir = ROOT / "results" / "ihmf"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "alpha_empirical.csv"

    df_out = pd.DataFrame(results)
    cols = ["station", "alpha", "r2", "N_months", "source", "slope", "intercept"]
    df_out = df_out[cols]
    df_out.to_csv(out_path, index=False, float_format="%.6f")

    print(f"\n  Wrote {len(results)} station(s) to: {out_path}")

    # Validate TUKU anchor
    tuku_rows = df_out[df_out["station"] == "TUKU"]
    if not tuku_rows.empty:
        alpha_tuku = tuku_rows["alpha"].values[0]
        if abs(alpha_tuku - 0.634) > 0.01:
            print(f"  WARNING: TUKU α = {alpha_tuku:.4f} differs from anchor 0.634!")
        else:
            print(f"  TUKU anchor verified: α = {alpha_tuku:.4f} ✓")


if __name__ == "__main__":
    main()
