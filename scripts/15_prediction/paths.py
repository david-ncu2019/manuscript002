"""
Centralised path constants for the prediction pipeline.
All paths are absolute, derived from this file's location.
No logic, no computation.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]   # InSAR_MLCW_v2 root

# ── Inputs ────────────────────────────────────────────────────────────────────
INSAR_STATIONS_FEATHER = ROOT / "data/insar/timeseries/mlcw_interp_insar_IDW_extend.feather"
INSAR_GRID_FEATHER     = ROOT / "data/insar/timeseries/gridpnt_500m_interp_insar_IDW_extend.feather"
MLCW_GROUPED_DIR       = ROOT / "data/mlcw/group_byLayer_reconstr"
HARMONIC_DIR           = ROOT / "results/seasonal_insar_harmonic"
DIRECT_RATIO_DIR       = ROOT / "results/direct_ratio"

# ── Outputs ───────────────────────────────────────────────────────────────────
OUTPUT_DIR = ROOT / "results/prediction_v1"

# ── Note on coordinates ───────────────────────────────────────────────────────
# INSAR_STATIONS_FEATHER: has both X_UTM50N and X_TWD97 columns.
# INSAR_GRID_FEATHER:     has ONLY X_TWD97/Y_TWD97 — no UTM columns.
# All spatial kriging must use TWD97 for consistency.
