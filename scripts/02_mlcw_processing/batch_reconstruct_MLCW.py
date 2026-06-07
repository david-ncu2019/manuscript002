import glob
import json
import os
import sys
import traceback
from argparse import Namespace
from pathlib import Path

import pandas as pd

# Add appsigsolv to path
appsigsolv_path = Path(
    r"D:\1000_SCRIPTS\004_Project003\20260501_timeseries_signal_solver"
)
sys.path.insert(0, str(appsigsolv_path))

from appsigsolv.core.modeling import (
    estimate_time_func,
    get_design_matrix4time_func,
)
from appsigsolv.io.data_manager import (
    load_and_clean_data_for_reconstruct,
    load_json_config,
)

# ── Configuration ─────────────────────────────────────────────────────────────
DECOMP_DIR = (
    r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\MLCW_decomposition"
)
DATA_DIR = (
    r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\MLCW_timeseries"
)
OUTPUT_DIR = (
    r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\MLCW_reconstruction"
)

SAMPLING_RATE = "custom"  # "daily" | "custom"
CUSTOM_DAYS = [
    1, 6, 11, 16, 21, 26
]  # e.g. [1, 6, 11, 16, 21, 26]  — only used when SAMPLING_RATE="custom"
UNIT = "mm"
DATE_COL = "datetime"  # date column name in the source CSV
# ──────────────────────────────────────────────────────────────────────────────


def build_output_dates(dates, sampling_rate, custom_days=None):
    """Return a DatetimeIndex for the requested output sampling."""
    import calendar

    if sampling_rate == "daily":
        return pd.date_range(start=min(dates), end=max(dates), freq="D")

    if sampling_rate == "custom":
        if not custom_days:
            raise ValueError(
                "CUSTOM_DAYS must be set when SAMPLING_RATE='custom'"
            )
        result = []
        start = pd.Timestamp(min(dates).date())
        end = pd.Timestamp(max(dates).date())
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


def reconstruct_station(station_name, csv_file, station_dir, output_dir):
    """Reconstruct all ring-distance time series for one station and save a merged CSV."""

    # Discover all JSON model files for this station
    json_files = sorted(
        glob.glob(
            os.path.join(station_dir, f"{station_name}_ringbyring_model_*.json")
        )
    )
    if not json_files:
        print(f"  [WARN] No JSON files found in {station_dir} — skipping.")
        return

    print(f"  Found {len(json_files)} JSON files.")

    # Load source data once — all ring columns share the same date index
    try:
        df_src = pd.read_csv(csv_file, parse_dates=[DATE_COL])
    except Exception as e:
        print(f"  [ERROR] Cannot read source CSV {csv_file}: {e}")
        return

    # Build output date axis once (same for all rings)
    dates_raw = df_src[DATE_COL].dropna().tolist()
    try:
        out_dates = build_output_dates(dates_raw, SAMPLING_RATE, CUSTOM_DAYS)
    except Exception as e:
        print(f"  [ERROR] Cannot build output dates: {e}")
        return

    date_list_py = [d.to_pydatetime() for d in out_dates]

    # Accumulate columns: {ring_label: modeled_values}
    columns = {}

    for json_file in json_files:
        # Extract ring label from filename  e.g. "8.775" from "..._model_8.775.json"
        stem = Path(json_file).stem  # TUKU_ringbyring_model_8.775
        ring_label = stem.rsplit("_model_", 1)[-1]  # 8.775
        target_col = ring_label  # column name in source CSV

        if target_col not in df_src.columns:
            print(
                f"    [WARN] Column '{target_col}' not found in source CSV — skipping."
            )
            continue

        try:
            model = load_json_config(json_file)

            # Prepare displacement series for this ring (mm → m internally)
            raw_vals = df_src[target_col].values.astype(float)
            valid_mask = ~pd.isna(raw_vals)
            dates_valid = [dates_raw[i] for i, v in enumerate(valid_mask) if v]
            disp_valid = raw_vals[valid_mask] / 1000.0  # mm → m

            disp_ref = disp_valid - disp_valid[0]

            G, m_est, e2, d_hat = estimate_time_func(
                model, dates_valid, disp_ref
            )

            G_out = get_design_matrix4time_func(
                date_list_py, model, ref_date=dates_valid[0]
            )
            d_out = G_out @ m_est

            if UNIT == "mm":
                d_out_final = (d_out + disp_valid[0]) * 1000.0
            else:
                d_out_final = d_out + disp_valid[0]

            columns[ring_label] = d_out_final

        except Exception as e:
            print(f"    [ERROR] Ring {ring_label}: {e}")
            traceback.print_exc()
            continue

    if not columns:
        print(f"  [WARN] No rings reconstructed for {station_name}.")
        return

    # Assemble merged table: datetime index + one column per ring
    df_out = pd.DataFrame({"datetime": out_dates})
    df_out = df_out.set_index("datetime")

    for ring_label, values in columns.items():
        df_out[ring_label] = values

    df_out = df_out[
        [str(ele) for ele in sorted(df_out.columns.map(lambda x: eval(x)))]
    ]
    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(
        output_dir, f"{station_name}_ringbyring_reconstructed.csv"
    )
    df_out.to_csv(out_file)
    print(
        f"  [SUCCESS] Saved {len(df_out)} rows × {len(columns)} rings → {out_file}"
    )


def main():
    # Discover all station directories
    station_dirs = sorted(glob.glob(os.path.join(DECOMP_DIR, "*_ringbyring")))

    if not station_dirs:
        print(f"No station directories found in {DECOMP_DIR}")
        return

    print(
        f"Found {len(station_dirs)} stations. Starting batch reconstruction..."
    )
    print(
        f"Sampling: {SAMPLING_RATE}"
        + (f" — days {CUSTOM_DAYS}" if SAMPLING_RATE == "custom" else "")
    )
    print("=" * 60)

    for i, station_dir in enumerate(station_dirs[:], 1):
        station_name = Path(station_dir).name.replace("_ringbyring", "")
        csv_file = os.path.join(DATA_DIR, f"{station_name}_ringbyring.csv")

        print(f"\n[{i}/{len(station_dirs)}] Station: {station_name}")
        print("-" * 60)

        if not os.path.isfile(csv_file):
            print(f"  [WARN] Source CSV not found: {csv_file} — skipping.")
            continue

        try:
            reconstruct_station(station_name, csv_file, station_dir, OUTPUT_DIR)
        except Exception as e:
            print(f"  [ERROR] Unexpected failure for {station_name}: {e}")
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("Batch reconstruction complete.")


if __name__ == "__main__":
    main()