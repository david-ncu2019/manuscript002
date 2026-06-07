import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path("scripts/10_ihmf").resolve()))
from ihmf_io_multilayer import load_config, load_all_layers

ROOT = Path("D:/1000_SCRIPTS/004_Project003/20260427_InSAR_MLCW_v2")
_, entries, insar_csv = load_config(ROOT)
dfs, metas, insar = load_all_layers("TUKU", entries, ROOT, insar_csv)

for k, v in dfs.items():
    print(k, "head_m NaNs:", v['head_m'].isna().sum(), "mlcw_mm NaNs:", v['mlcw_mm'].isna().sum())
    print(k, "head_m infs:", np.isinf(v['head_m']).sum(), "mlcw_mm infs:", np.isinf(v['mlcw_mm']).sum())
