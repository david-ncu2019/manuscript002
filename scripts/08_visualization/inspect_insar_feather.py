import pandas as pd
from pathlib import Path

f = Path(r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\InSAR_timeries\mlcw_interp_insar_IDW_extend.feather")
df = pd.read_feather(f)
print("Shape:", df.shape)
print("Columns (first 15):", list(df.columns[:15]))
print("Columns (last 5):", list(df.columns[-5:]))
# Check column types
meta_cols = []
epoch_cols = []
for c in df.columns:
    try:
        pd.Timestamp(str(c))
        epoch_cols.append(c)
    except Exception:
        meta_cols.append(c)
print(f"\nMeta cols ({len(meta_cols)}): {meta_cols}")
print(f"Epoch cols ({len(epoch_cols)}): first={epoch_cols[0] if epoch_cols else 'NONE'}, last={epoch_cols[-1] if epoch_cols else 'NONE'}")
print(f"Total epoch cols: {len(epoch_cols)}")

# Check MLCW station dates
mlcw = pd.read_csv(r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\MLCW_5m_regular\TUKU_5m_grid.csv", nrows=3)
print("\nMLCW TUKU first rows:")
print(mlcw[["datetime"]].head())
print("MLCW columns:", list(mlcw.columns[:5]))
