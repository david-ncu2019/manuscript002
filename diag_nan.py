"""Quick NaN diagnostic for TUKU IHM-F v3 data loading."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "scripts" / "10_ihmf"))

import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent
cfg = json.load(open(ROOT / "data" / "ihmf_config.json"))
shared = cfg["shared"]
tuku_entries = [e for e in cfg["entries"] if e["station"] == "TUKU"]

insar_csv = ROOT / shared["insar_csv"]
insar = pd.read_csv(insar_csv, parse_dates=[0])
insar.columns = [c.strip() for c in insar.columns]
insar["datetime"] = pd.to_datetime(insar.iloc[:, 0]).astype("datetime64[ns]")
insar = insar[["datetime", "TUKU"]].dropna(subset=["TUKU"])
insar["TUKU"] = insar["TUKU"] * 1000.0
print(f"InSAR epochs: {len(insar)} | {insar.datetime.min().date()} to {insar.datetime.max().date()}")

for e in tuku_entries:
    layer = e["layer"]
    wc = str(e["assigned_wellcode"]).zfill(8)
    gwl_path = ROOT / e["gwl_feather"]
    gwl_raw = pd.read_feather(gwl_path)
    gwl_raw["datetime"] = pd.to_datetime(gwl_raw["datetime"]).astype("datetime64[ns]")
    if wc not in gwl_raw.columns:
        print(f"  {layer} well {wc}: COLUMN MISSING in {gwl_path.name}")
        continue
    gwl = gwl_raw[["datetime", wc]].dropna(subset=[wc]).sort_values("datetime")
    print(f"  {layer} well {wc}: gwl_rows={len(gwl)} | {gwl.datetime.min().date()} to {gwl.datetime.max().date()}")
    al = pd.merge_asof(
        insar[["datetime"]].sort_values("datetime"), gwl,
        on="datetime", direction="nearest", tolerance=pd.Timedelta("3D")
    )
    nan_count = al[wc].isna().sum()
    print(f"    -> nan after merge_asof(3D): {nan_count} of {len(al)}")
