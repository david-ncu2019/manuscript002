import sys
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path("scripts/10_ihmf").resolve()))
from ihmf_io_multilayer import load_config, load_all_layers

ROOT = Path("D:/1000_SCRIPTS/004_Project003/20260427_InSAR_MLCW_v2")
_, entries, insar_csv = load_config(ROOT)
dfs, metas, insar = load_all_layers("TUKU", entries, ROOT, insar_csv)
df = dfs['F2']
print(df[['datetime', 'insar_mm', 'head_m', 'mlcw_mm']].head())
print("InSAR min/max:", np.min(insar), np.max(insar))
print("MLCW F2 min/max:", np.min(df['mlcw_mm']), np.max(df['mlcw_mm']))
