"""
batch_reconstruct_nojump.py — Reconstruct MLCW timeseries without jumps.

Reads decompose JSON models (v2) + raw ring-by-ring CSVs and produces three
reconstruction variants on a custom 5-day output grid:
  - nojump/       : full model with step offsets removed (trend + periodic)
  - trend_only/   : secular trend only (polynomial + polyline, no jumps, no seasons)
  - detrended/    : periodic only (seasonal signal, no trend, no jumps)

Usage
-----
  # Single station test
  python scripts/02_mlcw_processing/batch_reconstruct_nojump.py --station TUKU

  # Full batch (all 39 stations)
  python scripts/02_mlcw_processing/batch_reconstruct_nojump.py
"""
import argparse
import copy
import glob
import os
import sys
import traceback
from pathlib import Path

import pandas as pd

# ── Path setup ─────────────────────────────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).resolve().parent
_SCRIPTS_ROOT = _SCRIPT_DIR.parent.parent  # repo root

# Add appsigsolv to path
APPSIGSOLV_PATH = _SCRIPTS_ROOT / ".." / "20260501_timeseries_signal_solver"
sys.path.insert(0, str(APPSIGSOLV_PATH.resolve()))

from appsigsolv.core.modeling import (
    estimate_time_func,
    get_design_matrix4time_func,
)
from appsigsolv.io.data_manager import load_json_config


# ── Configuration ──────────────────────────────────────────────────────────────
DECOMP_DIR  = _SCRIPTS_ROOT / "data" / "mlcw" / "decomposed"
DATA_DIR    = _SCRIPTS_ROOT / "data" / "mlcw" / "raw_timeseries"
OUTPUT_ROOT = _SCRIPTS_ROOT / "data" / "mlcw" / "modeled_nojump"

SAMPLING_RATE = "custom"
CUSTOM_DAYS   = [1, 6, 11, 16, 21, 26]
UNIT          = "mm"
DATE_COL      = "datetime"

SUBFOLDERS = ["nojump", "trend_only", "detrended"]
# ───────────────────────────────────────────────────────────────────────────────


def build_output_dates(dates, sampling_rate, custom_days=None):
    """Return a DatetimeIndex for the requested output sampling."""
    import calendar

    if sampling_rate == "daily":
        return pd.date_range(start=min(dates), end=max(dates), freq="D")

    if sampling_rate == "custom":
        if not custom_days:
            raise ValueError("CUSTOM_DAYS must be set when SAMPLING_RATE='custom'")
        result = []
        start = pd.Timestamp(min(dates).date())
        end   = pd.Timestamp(max(dates).date())
        current = start.replace(day=1)
        while current <= end:
            last_day = calendar.monthrange(current.year, current.month)[1]
            for d in sorted(custom_days):
                ts = pd.Timestamp(current.year, current.month, min(d, last_day))
                if start <= ts <= end:
                    result.append(ts)
            current = current + pd.offsets.MonthBegin(1)
        return pd.DatetimeIndex(result)

    raise ValueError(f"Unknown SAMPLING_RATE: {sampling_rate!r}")


def _forward_project(model, dates_valid, disp_ref, date_list_py):
    """Fit model to valid data and forward-project onto output dates.

    Returns
    -------
    d_out : np.ndarray
        Forward-projected displacement on *date_list_py*, in the same
        unit as *disp_ref* (typically metres, referenced to first value).
    """
    G, m_est, e2, d_hat = estimate_time_func(model, dates_valid, disp_ref)
    G_out = get_design_matrix4time_func(date_list_py, model, ref_date=dates_valid[0])
    return G_out @ m_est


def reconstruct_station_nojump(station_name, csv_file, station_dir, output_root):
    """Reconstruct three jump-free variants for one station."""

    # Discover JSON model files for this station
    json_files = sorted(
        glob.glob(os.path.join(station_dir, f"{station_name}_ringbyring_model_*.json"))
    )
    if not json_files:
        print(f"  [WARN] No JSON files found in {station_dir} — skipping.")
        return

    print(f"  Found {len(json_files)} JSON files.")

    # Load source data
    try:
        df_src = pd.read_csv(csv_file, parse_dates=[DATE_COL])
    except Exception as e:
        print(f"  [ERROR] Cannot read source CSV {csv_file}: {e}")
        return

    # Build output date axis
    dates_raw = df_src[DATE_COL].dropna().tolist()
    try:
        out_dates = build_output_dates(dates_raw, SAMPLING_RATE, CUSTOM_DAYS)
    except Exception as e:
        print(f"  [ERROR] Cannot build output dates: {e}")
        return

    date_list_py = [d.to_pydatetime() for d in out_dates]

    # Three column accumulators
    cols_nojump    = {}
    cols_trend     = {}
    cols_detrended = {}

    for json_file in json_files:
        stem = Path(json_file).stem  # e.g. TUKU_ringbyring_model_8.775
        ring_label = stem.rsplit("_model_", 1)[-1]

        if ring_label not in df_src.columns:
            print(f"    [WARN] Column '{ring_label}' not found in source CSV — skipping.")
            continue

        try:
            model_orig = load_json_config(json_file)

            # Prepare displacement series (mm → m)
            raw_vals = df_src[ring_label].values.astype(float)
            valid_mask = ~pd.isna(raw_vals)
            dates_valid = [dates_raw[i] for i, v in enumerate(valid_mask) if v]
            disp_valid = raw_vals[valid_mask] / 1000.0
            disp_ref = disp_valid - disp_valid[0]

            # ── Variant A: nojump (remove step offsets) ─────────────────────
            model_a = copy.deepcopy(model_orig)
            model_a["stepDate"] = []
            d_nojump_m = _forward_project(model_a, dates_valid, disp_ref, date_list_py)

            if UNIT == "mm":
                d_nojump = (d_nojump_m + disp_valid[0]) * 1000.0
            else:
                d_nojump = d_nojump_m + disp_valid[0]
            cols_nojump[ring_label] = d_nojump

            # ── Variant B: trend only ───────────────────────────────────────
            model_b = copy.deepcopy(model_orig)
            model_b["stepDate"] = []
            model_b["periodic"] = []
            d_trend_m = _forward_project(model_b, dates_valid, disp_ref, date_list_py)

            if UNIT == "mm":
                d_trend = (d_trend_m + disp_valid[0]) * 1000.0
            else:
                d_trend = d_trend_m + disp_valid[0]
            cols_trend[ring_label] = d_trend

            # ── Variant C: detrended (nojump - trend) ───────────────────────
            # Ensures identity: nojump ≡ trend_only + detrended
            d_detrended = d_nojump - d_trend
            cols_detrended[ring_label] = d_detrended

        except Exception as e:
            print(f"    [ERROR] Ring {ring_label}: {e}")
            traceback.print_exc()
            continue

    if not cols_nojump:
        print(f"  [WARN] No rings reconstructed for {station_name}.")
        return

    # Save all three variants
    datasets = [
        (SUBFOLDERS[0], cols_nojump),
        (SUBFOLDERS[1], cols_trend),
        (SUBFOLDERS[2], cols_detrended),
    ]

    for subfolder, columns in datasets:
        out_dir = output_root / subfolder
        os.makedirs(out_dir, exist_ok=True)
        out_file = out_dir / f"{station_name}_ringbyring.csv"

        df_out = pd.DataFrame({"datetime": out_dates}).set_index("datetime")
        for lbl, vals in columns.items():
            df_out[lbl] = vals

        # Sort columns numerically (ring depths)
        df_out = df_out[[str(ele) for ele in sorted(df_out.columns.map(lambda x: eval(x)))]]
        df_out.to_csv(out_file)
        print(f"    [SAVED] {len(df_out)} rows × {len(columns)} rings → {out_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Reconstruct MLCW timeseries without jumps (3 variants)."
    )
    parser.add_argument(
        "--station", default=None,
        help="Single station name to process (omit for full batch)."
    )
    args = parser.parse_args()

    # Discover station directories
    all_dirs = sorted(glob.glob(os.path.join(DECOMP_DIR, "*_ringbyring")))

    if args.station:
        # Only the requested station
        pattern = os.path.join(DECOMP_DIR, f"{args.station}_ringbyring")
        all_dirs = [d for d in all_dirs if d == pattern]
        if not all_dirs:
            print(f"Station '{args.station}' not found in {DECOMP_DIR}.")
            return

    if not all_dirs:
        print(f"No station directories found in {DECOMP_DIR}.")
        return

    print(f"Found {len(all_dirs)} stations.")
    print(f"Sampling: {SAMPLING_RATE}{f' — days {CUSTOM_DAYS}' if SAMPLING_RATE == 'custom' else ''}")
    print("Output variants: " + ", ".join(SUBFOLDERS))
    print("=" * 60)

    for i, station_dir in enumerate(all_dirs, 1):
        station_name = Path(station_dir).name.replace("_ringbyring", "")
        csv_file = DATA_DIR / f"{station_name}_ringbyring.csv"

        print(f"\n[{i}/{len(all_dirs)}] Station: {station_name}")
        print("-" * 60)

        if not csv_file.is_file():
            print(f"  [WARN] Source CSV not found: {csv_file} — skipping.")
            continue

        try:
            reconstruct_station_nojump(station_name, csv_file, station_dir, OUTPUT_ROOT)
        except Exception as e:
            print(f"  [ERROR] Unexpected failure for {station_name}: {e}")
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("Batch reconstruction (no-jump) complete.")


if __name__ == "__main__":
    main()
