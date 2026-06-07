"""
ring_gwl_xcorr.py
-----------------
Brute-force cross-correlation: every MLCW ring vs every GWL well in the study area.

Input MLCW: data/mlcw/reconstructed/ -- regular ~5-day spacing, 1,572 epochs.
Input GWL:  data/gwl/well_timeseries/ -- daily, snapped to MLCW epoch dates.

Both signals are linearly detrended using actual calendar day-numbers as the
x-axis before cross-correlation.  Lag 0 = no shift.  Positive lag k = GWL
leads MLCW by k epochs (i.e. head change came BEFORE the ring responded).

Output: one parquet file per MLCW station -> results/ring_gwl_xcorr/

Usage:
    conda run -n fafalab python scripts/16_ring_gwl_xcorr/ring_gwl_xcorr.py
    conda run -n fafalab python scripts/16_ring_gwl_xcorr/ring_gwl_xcorr.py --station TUKU
    conda run -n fafalab python scripts/16_ring_gwl_xcorr/ring_gwl_xcorr.py --lag-max 150
"""

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from paths import DATA_ROOT, RESULTS_ROOT, INSAR_FEATHER

MLCW_RECONST_DIR = DATA_ROOT / "mlcw" / "reconstructed"
GWL_TS_DIR       = DATA_ROOT / "gwl" / "well_timeseries"
GWL_WELL_INFO    = DATA_ROOT / "gwl" / "well_info" / "gwl_allwells_flat.csv"
OUT_DIR          = RESULTS_ROOT / "ring_gwl_xcorr"

LAG_MAX = 73   # epochs (~730 days at 10-day sampling)


# ---------------------------------------------------------------------------
# Detrend + cross-correlation
# ---------------------------------------------------------------------------

def _detrend_linear(arr: np.ndarray, day_numbers: np.ndarray) -> np.ndarray:
    """
    Remove a least-squares linear trend using actual elapsed day-numbers as x.
    NaNs are left in place.  day_numbers must be the same length as arr.
    """
    valid = ~np.isnan(arr)
    if valid.sum() < 4:
        return arr.copy()
    x = day_numbers[valid].astype(float)
    y = arr[valid]
    p = np.polyfit(x, y, 1)
    out = arr.copy()
    out[valid] = y - np.polyval(p, x)
    return out


def _xcorr(a: np.ndarray, b: np.ndarray, max_lag: int):
    """
    Normalised cross-correlation at integer lags -max_lag to +max_lag.

    Both arrays are z-scored over the shared valid (non-NaN) positions before
    computing the dot product, so the value at lag=0 equals the Pearson r.

    Positive lag k: b leads a by k epochs (b[:-k] is paired with a[k:]).

    Returns
    -------
    lags     : int array of shape (2*max_lag+1,)
    xcorr    : float array, values nominally in [-1, 1]
    n_valid  : int, number of jointly non-NaN points at lag=0
    """
    n = len(a)
    assert len(b) == n

    valid0 = ~(np.isnan(a) | np.isnan(b))
    n_valid = int(valid0.sum())
    lags = np.arange(-max_lag, max_lag + 1)

    if n_valid < 10:
        return lags, np.full(len(lags), np.nan), n_valid

    xcorr = np.empty(len(lags))
    for i, lag in enumerate(lags):
        if lag == 0:
            valid = valid0
            xa, xb = a[valid], b[valid]
        elif lag > 0:
            va = ~np.isnan(a[lag:])
            vb = ~np.isnan(b[:-lag])
            valid = va & vb
            xa, xb = a[lag:][valid], b[:-lag][valid]
        else:
            k = -lag
            va = ~np.isnan(a[:-k])
            vb = ~np.isnan(b[k:])
            valid = va & vb
            xa, xb = a[:-k][valid], b[k:][valid]

        nv = valid.sum()
        if nv < 5:
            xcorr[i] = np.nan
            continue

        # z-score within this lag window so the result stays in [-1, 1]
        sd_xa = xa.std()
        sd_xb = xb.std()
        if sd_xa < 1e-12 or sd_xb < 1e-12:
            xcorr[i] = np.nan
            continue
        xa = (xa - xa.mean()) / sd_xa
        xb = (xb - xb.mean()) / sd_xb
        xcorr[i] = np.dot(xa, xb) / nv

    return lags, xcorr, n_valid


# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------

def load_mlcw_station_coords() -> dict:
    """
    Return a dict: station_name (upper) -> (x_twd97, y_twd97)
    pulled from the InSAR feather, which is the authoritative spatial registry
    for the 39 MLCW benchmark locations.
    """
    df = pd.read_feather(INSAR_FEATHER, columns=["Ename", "X_TWD97", "Y_TWD97"])
    coords = {}
    for _, row in df.iterrows():
        coords[str(row["Ename"]).upper()] = (float(row["X_TWD97"]), float(row["Y_TWD97"]))
    return coords


def load_well_info() -> pd.DataFrame:
    """Load the 300-well metadata table."""
    df = pd.read_csv(GWL_WELL_INFO, dtype={"wellcode": str})
    df["wellcode"] = df["wellcode"].str.zfill(8)
    return df


def load_all_gwl_wells() -> dict:
    """
    Read every *_gwl_timeseries.feather in GWL_TS_DIR.
    Return: {wellcode_str -> pd.Series(values, index=DatetimeIndex)}
    """
    wells = {}
    files = sorted(GWL_TS_DIR.glob("*_gwl_timeseries.feather"))
    print(f"  Reading GWL from {len(files)} station-level feather files ...")
    for fpath in files:
        try:
            df = pd.read_feather(fpath)
            df["datetime"] = pd.to_datetime(df["datetime"])
            df = df.set_index("datetime")
        except Exception as exc:
            print(f"  WARNING: skipping {fpath.name}: {exc}")
            continue
        for col in df.columns:
            wc = str(col).zfill(8)
            if wc not in wells:
                wells[wc] = df[col]
    print(f"  Loaded {len(wells)} unique wells.")
    return wells


def _align_gwl(gwl_series: pd.Series, mlcw_dates: pd.DatetimeIndex,
               tol_days: int = 20) -> np.ndarray:
    """
    Snap a (potentially daily) GWL series to the MLCW irregular epoch dates.
    Uses nearest-date matching; gaps wider than tol_days become NaN.
    """
    gwl = gwl_series.dropna()
    if gwl.empty:
        return np.full(len(mlcw_dates), np.nan)

    gwl.index = pd.to_datetime(gwl.index)
    out = np.empty(len(mlcw_dates))
    for i, d in enumerate(mlcw_dates):
        idx = gwl.index.get_indexer([d], method="nearest")[0]
        if idx < 0:
            out[i] = np.nan
        else:
            nearest = gwl.index[idx]
            out[i] = gwl.iloc[idx] if abs((nearest - d).days) <= tol_days else np.nan
    return out


def _dist_m(wx: float, wy: float, mx: float, my: float) -> float:
    """Euclidean distance in metres (TWD97 projected, already in m)."""
    if any(np.isnan(v) for v in [wx, wy, mx, my]):
        return np.nan
    return float(np.sqrt((wx - mx) ** 2 + (wy - my) ** 2))


# ---------------------------------------------------------------------------
# Per-station processing
# ---------------------------------------------------------------------------

def process_station(station: str,
                    well_info: pd.DataFrame,
                    all_gwl: dict,
                    station_coords: dict,
                    lag_max: int = LAG_MAX) -> pd.DataFrame | None:
    """
    Compute ring x GWL cross-correlations for one MLCW station.
    Returns a DataFrame with one row per (ring_depth, wellcode) pair.
    """
    mlcw_file = MLCW_RECONST_DIR / f"{station}_ringbyring_reconstructed.csv"
    if not mlcw_file.exists():
        print(f"  [SKIP] {station}: reconstructed ringbyring not found")
        return None

    mlcw = pd.read_csv(mlcw_file, parse_dates=["datetime"])
    mlcw = mlcw.sort_values("datetime").set_index("datetime")
    mlcw_dates = mlcw.index
    # elapsed days from first epoch — used as x-axis for linear detrend
    day_numbers = np.array([(d - mlcw_dates[0]).days for d in mlcw_dates], dtype=float)
    # mean spacing in days — used to convert lag epochs -> approximate days
    mean_epoch_days = float(np.diff(day_numbers).mean())
    ring_cols = list(mlcw.columns)

    mx, my = station_coords.get(station, (np.nan, np.nan))
    n_wells = len(all_gwl)
    records = []

    for ri, ring_col in enumerate(ring_cols):
        ring_depth_m = float(ring_col)
        raw_ring = mlcw[ring_col].values.astype(float)
        det_ring = _detrend_linear(raw_ring, day_numbers)

        print(f"    ring {ri+1}/{len(ring_cols)}: {ring_depth_m:.1f} m x {n_wells} wells ...",
              flush=True)

        for wc, gwl_series in all_gwl.items():
            wrow_df = well_info[well_info["wellcode"] == wc]
            if wrow_df.empty:
                gwl_station = "unknown"
                dist = np.nan
                screen_top = np.nan
                screen_bot = np.nan
                screen_mid = np.nan
            else:
                wrow = wrow_df.iloc[0]
                gwl_station = str(wrow["station"])
                wx = float(wrow.get("x_twd97", np.nan))
                wy = float(wrow.get("y_twd97", np.nan))
                dist = _dist_m(wx, wy, mx, my)
                screen_top = float(wrow.get("screen_top_m", np.nan))
                screen_bot = float(wrow.get("screen_bot_m", np.nan))
                screen_mid = (
                    round((screen_top + screen_bot) / 2, 2)
                    if not (np.isnan(screen_top) or np.isnan(screen_bot))
                    else np.nan
                )

            gwl_snapped = _align_gwl(gwl_series, mlcw_dates)
            det_gwl = _detrend_linear(gwl_snapped, day_numbers)

            lags, xcorr, n_overlap = _xcorr(det_ring, det_gwl, lag_max)

            if np.all(np.isnan(xcorr)):
                pearson = xmax = xmin = np.nan
                lag_at_max = lag_at_min = np.nan
            else:
                valid0 = ~(np.isnan(det_ring) | np.isnan(det_gwl))
                if valid0.sum() >= 5:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        pearson, _ = pearsonr(det_ring[valid0], det_gwl[valid0])
                else:
                    pearson = np.nan

                imax = int(np.nanargmax(xcorr))
                imin = int(np.nanargmin(xcorr))
                xmax = float(xcorr[imax])
                lag_at_max = int(lags[imax])
                xmin = float(xcorr[imin])
                lag_at_min = int(lags[imin])

            records.append({
                "mlcw_station":    station,
                "ring_depth_m":    ring_depth_m,
                "gwl_station":     gwl_station,
                "gwl_wellcode":    wc,
                "dist_m":          round(dist, 1) if not np.isnan(dist) else np.nan,
                "screen_top_m":    screen_top,
                "screen_bot_m":    screen_bot,
                "screen_mid_m":    screen_mid,
                "n_overlap":       n_overlap,
                "pearson_r":       round(pearson, 4) if not np.isnan(pearson) else np.nan,
                "xcorr_max":       round(xmax, 4) if not np.isnan(xmax) else np.nan,
                "lag_at_max":      lag_at_max,
                "lag_days_at_max": round(lag_at_max * mean_epoch_days) if not np.isnan(lag_at_max) else np.nan,
                "xcorr_min":       round(xmin, 4) if not np.isnan(xmin) else np.nan,
                "lag_at_min":      lag_at_min,
                "lag_days_at_min": round(lag_at_min * mean_epoch_days) if not np.isnan(lag_at_min) else np.nan,
            })

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Per-station save wrapper (skip-existing logic lives here)
# ---------------------------------------------------------------------------

def _process_and_save(station, well_info, all_gwl, station_coords, lag_max, force=False):
    out_path = OUT_DIR / f"{station}_ring_gwl_xcorr.parquet"
    if out_path.exists() and not force:
        print(f"  [SKIP] {station}: output already exists ({out_path.name}). Use --force to overwrite.")
        return
    print(f"=== {station} ===", flush=True)
    df = process_station(station, well_info, all_gwl, station_coords, lag_max)
    if df is None or df.empty:
        print(f"  No output for {station}.\n", flush=True)
        return
    df.to_parquet(out_path, index=False)
    print(f"  => {len(df)} rows saved to {out_path.name}\n", flush=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Brute-force ring x GWL cross-correlation for all MLCW stations"
    )
    parser.add_argument("--station", type=str, default=None,
                        help="Process a single station (e.g. TUKU). Default: all 39.")
    parser.add_argument("--lag-max", type=int, default=LAG_MAX,
                        help=f"Max cross-correlation lag in epochs (default {LAG_MAX}).")
    parser.add_argument("--cores", type=int, default=1,
                        help="Number of parallel worker processes (default 1 = serial).")
    parser.add_argument("--force", action="store_true",
                        help="Re-process stations even if output parquet already exists.")
    args = parser.parse_args()
    lag_max = args.lag_max

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading MLCW station coordinates from InSAR feather ...")
    station_coords = load_mlcw_station_coords()

    print("Loading well metadata ...")
    well_info = load_well_info()

    print("Loading all GWL well timeseries ...")
    all_gwl = load_all_gwl_wells()

    if args.station:
        stations = [args.station.upper()]
    else:
        stations = sorted(
            f.stem.replace("_ringbyring_reconstructed", "")
            for f in MLCW_RECONST_DIR.glob("*_ringbyring_reconstructed.csv")
        )

    print(f"\nProcessing {len(stations)} station(s) with lag_max={lag_max} epochs ...\n")

    from concurrent.futures import ProcessPoolExecutor, as_completed
    import functools

    force = getattr(args, "force", False)

    if args.cores == 1:
        for station in stations:
            _process_and_save(station, well_info, all_gwl, station_coords, lag_max, force=force)
    else:
        with ProcessPoolExecutor(max_workers=args.cores) as pool:
            futures = {
                pool.submit(_process_and_save, s, well_info, all_gwl,
                            station_coords, lag_max, force): s
                for s in stations
            }
            for fut in as_completed(futures):
                try:
                    fut.result()
                except Exception as exc:
                    st = futures[fut]
                    print(f"  [ERROR] {st} raised: {exc}", flush=True)

    print("All done.")


if __name__ == "__main__":
    main()
