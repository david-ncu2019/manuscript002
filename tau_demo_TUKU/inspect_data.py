"""Quick inspection of incremental_data feathers."""
import pandas as pd
from pathlib import Path

base = Path("tau_demo_TUKU/data/incremental_data")

for fname in sorted(base.glob("*.feather")):
    df = pd.read_feather(fname)
    print(f"\n=== {fname.name} ===")
    print(f"  shape: {df.shape}")
    print(f"  columns: {df.columns.tolist()}")
    dt = df["datetime"] if "datetime" in df.columns else None
    if dt is not None:
        print(f"  date range: {dt.min().date()} to {dt.max().date()}")
    print(df.head(3).to_string())
