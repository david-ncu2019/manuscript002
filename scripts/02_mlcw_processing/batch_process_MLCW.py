import os
import gc
import glob
import sys
from pathlib import Path
from argparse import Namespace

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Add appsigsolv to path
appsigsolv_path = Path(r"D:\1000_SCRIPTS\004_Project003\20260501_timeseries_signal_solver")
sys.path.insert(0, str(appsigsolv_path))

from appsigsolv.cli.cmd_decompose import run_decompose


def main():
    # Setup paths
    data_dir = r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\MLCW_timeseries"
    output_dir = r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\MLCW_decomposition"

    # Find all CSV files ending with _ringbyring.csv in the directory
    csv_files = sorted(glob.glob(os.path.join(data_dir, "*_ringbyring.csv")))

    if not csv_files:
        print(f"No CSV files found in {data_dir}")
        return

    print(f"Found {len(csv_files)} CSV files. Starting batch processing...\n")

    for i, csv_file in enumerate(csv_files, 1):
        station_name = Path(csv_file).stem.replace('_ringbyring', '')
        print(f"[{i}/{len(csv_files)}] Processing station: {station_name}")
        print("-" * 60)

        # Create args namespace with decomposition parameters
        args = Namespace(
            input_csv=csv_file,
            component="all",
            date_col="datetime",
            unit="mm",
            jumps="",
            polylines="",
            logs="",
            poly_deg=-1,
            poly_deg_min=1,       # auto-select from [1,2,3]; exclude offset-only (deg=0)
            periods="0.5, 1",
            auto_periods=4,
            sigma_min=2.0,
            sigma_max=20.0,
            sigma_step=0.5,
            alpha=0.05,
            max_iter=1000,
            irregular=True,
            no_plot=False,
            no_relax=True,
            exp_trend=None,
            force=False,
            output_dir=output_dir,
            cores=1,
        )

        try:
            run_decompose(args)
            print(f"\n[SUCCESS] Completed processing for {station_name}\n")
        except Exception as e:
            print(f"\n[ERROR] Failed processing {station_name}: {e}\n")
            import traceback
            traceback.print_exc()
        finally:
            plt.close('all')
            gc.collect()


if __name__ == "__main__":
    main()
