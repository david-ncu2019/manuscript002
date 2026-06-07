import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from paths import DATA_ROOT, RESULTS_ROOT, SCRIPTS_ROOT
import pandas as pd

# Full harmonic holdout CSV
harm_path = RESULTS_ROOT / "seasonal_insar_harmonic/TUKU/step4_temporal_holdout.csv"
h = pd.read_csv(harm_path)
print('Harmonic holdout full:\n', h.to_string())

# Check InSAR epoch column format more carefully
INSAR_FEATHER = DATA_ROOT / "insar/timeseries/mlcw_interp_insar_IDW_extend.feather"
df = pd.read_feather(INSAR_FEATHER)
epoch_cols = [c for c in df.columns if c.startswith('D2')]
print('\nInSAR epoch cols example:', epoch_cols[:5], '...', epoch_cols[-3:])
print('Total epoch cols:', len(epoch_cols))
