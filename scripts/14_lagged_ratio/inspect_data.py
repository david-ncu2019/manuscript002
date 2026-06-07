import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from paths import DATA_ROOT, RESULTS_ROOT, SCRIPTS_ROOT
import pandas as pd

# Check InSAR feather columns
INSAR_FEATHER = DATA_ROOT / "insar/timeseries/mlcw_interp_insar_IDW_extend.feather"
df = pd.read_feather(INSAR_FEATHER)
print('InSAR shape:', df.shape)
print('Columns[:10]:', list(df.columns[:10]))
print('Station/name cols:', [c for c in df.columns if any(k in c.lower() for k in ['station','name','stn','site'])])

# Find TUKU row
for col in df.columns[:10]:
    vals = df[col].astype(str).tolist()
    if 'TUKU' in vals:
        print(f"Station column: {col}")
        break

# Print first row info
print("First row metadata cols:", df.iloc[0, :8].to_dict())

# MLCW grouped
MLCW = DATA_ROOT / "mlcw/group_byLayer_reconstr/TUKU_reconst_grouped.csv"
mlcw = pd.read_csv(MLCW, nrows=5)
print('\nMLCW columns:', list(mlcw.columns))
print('MLCW head:\n', mlcw.head())

# Check seasonal harmonic results
harm_path = RESULTS_ROOT / "seasonal_insar_harmonic/TUKU/step4_temporal_holdout.csv"
print('\nHarmonic holdout exists:', harm_path.exists())
if harm_path.exists():
    h = pd.read_csv(harm_path, nrows=5)
    print('Harmonic columns:', list(h.columns))
    print('Harmonic head:\n', h.head())

print('\nSCRIPTS_ROOT:', SCRIPTS_ROOT)
print('FIGURES_ROOT in paths?', hasattr(sys.modules.get('paths', None), 'FIGURES_ROOT'))
import paths
print('paths exports:', [x for x in dir(paths) if not x.startswith('_')])
