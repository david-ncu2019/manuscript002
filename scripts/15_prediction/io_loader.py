"""
All file I/O for the prediction pipeline.
Returns clean DataFrames or raises FileNotFoundError with a descriptive message.
No computation — reading and schema validation only.
"""
import numpy as np
import pandas as pd
from pathlib import Path
import importlib.util as _ilu
import sys as _sys
from pathlib import Path as _Path

def _load_pred_paths():
    spec = _ilu.spec_from_file_location(
        'pred_paths', _Path(__file__).resolve().parent / 'paths.py'
    )
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_P = _load_pred_paths()
INSAR_STATIONS_FEATHER = _P.INSAR_STATIONS_FEATHER
INSAR_GRID_FEATHER     = _P.INSAR_GRID_FEATHER
MLCW_GROUPED_DIR       = _P.MLCW_GROUPED_DIR
HARMONIC_DIR           = _P.HARMONIC_DIR

_EPOCH_PREFIX = 'D'   # epoch columns: D20150121, D20150126, ...


def _epoch_cols(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c.startswith(_EPOCH_PREFIX) and len(c) == 9]


def load_insar_stations(path: Path = INSAR_STATIONS_FEATHER) -> pd.DataFrame:
    """
    Load InSAR timeseries at 39 MLCW station locations.
    Epoch columns are converted from metres to mm (× 1000).
    Returns DataFrame indexed by station name (Ename).
    """
    if not path.exists():
        raise FileNotFoundError(f"InSAR stations feather not found: {path}")
    df = pd.read_feather(path)
    if 'Ename' not in df.columns:
        raise ValueError(f"'Ename' column missing in {path.name}")
    df = df.set_index('Ename')
    ecols = _epoch_cols(df)
    if not ecols:
        raise ValueError(f"No epoch columns (D{{}}) found in {path.name}")
    df[ecols] = df[ecols] * 1000.0   # metres → mm
    return df


def load_insar_grid(path: Path = INSAR_GRID_FEATHER) -> pd.DataFrame:
    """
    Load InSAR timeseries at 8,577 unmonitored grid points.
    Epoch columns converted metres → mm. Uses X_TWD97/Y_TWD97 for spatial work.
    Returns DataFrame indexed by PointKey.
    """
    if not path.exists():
        raise FileNotFoundError(f"InSAR grid feather not found: {path}")
    df = pd.read_feather(path)
    if 'PointKey' not in df.columns:
        raise FileNotFoundError(f"'PointKey' column missing in {path.name}")
    df = df.set_index('PointKey')
    ecols = _epoch_cols(df)
    if not ecols:
        raise ValueError(f"No epoch columns found in {path.name}")
    df[ecols] = df[ecols] * 1000.0
    return df


def load_mlcw_grouped(station: str, mlcw_dir: Path = MLCW_GROUPED_DIR) -> pd.DataFrame:
    """
    Load layer-grouped MLCW compaction timeseries for one station.
    Returns DataFrame with datetime column + layer columns (F1, T1, F2, ...).
    """
    path = mlcw_dir / f"{station}_reconst_grouped.csv"
    if not path.exists():
        raise FileNotFoundError(f"MLCW grouped CSV not found: {path}")
    df = pd.read_csv(path, parse_dates=['datetime'])
    if 'datetime' not in df.columns:
        raise ValueError(f"'datetime' column missing in {path.name}")
    return df.sort_values('datetime').reset_index(drop=True)


def load_fbar(station: str, harmonic_dir: Path = HARMONIC_DIR) -> pd.DataFrame:
    """
    DIAGNOSTIC USE ONLY — returns full-record fbar from reconstruction_metrics.csv.
    Do NOT pass this to run_walkforward(); it contains test-period data.
    Use for post-hoc comparison of per-fold fbar drift.
    """
    path = harmonic_dir / station / 'reconstruction_metrics.csv'
    if not path.exists():
        raise FileNotFoundError(f"reconstruction_metrics.csv not found for {station}: {path}")
    return pd.read_csv(path)


def load_seasonal_stability(station: str, harmonic_dir: Path = HARMONIC_DIR) -> pd.DataFrame:
    """
    Load per-year harmonic stability table (step3_peryear_harmonic_stability.csv).
    Used by walkforward.py to compute per-fold seasonal params from training years only.
    Columns include: station, layer, year, r1_k, dphi1_k_days, A1_k_mm, ...
    """
    path = harmonic_dir / station / 'step3_peryear_harmonic_stability.csv'
    if not path.exists():
        raise FileNotFoundError(
            f"step3_peryear_harmonic_stability.csv not found for {station}: {path}"
        )
    return pd.read_csv(path)


def load_phase_stability_summary(station: str, harmonic_dir: Path = HARMONIC_DIR) -> pd.DataFrame:
    """
    Load the per-layer phase stability summary (step3_phase_stability_summary.csv).
    Contains annual_PASS flag and corr_A1k_A1x per layer.
    """
    path = harmonic_dir / station / 'step3_phase_stability_summary.csv'
    if not path.exists():
        raise FileNotFoundError(
            f"step3_phase_stability_summary.csv not found for {station}: {path}"
        )
    return pd.read_csv(path)


def load_reconstruction_metrics(station: str, harmonic_dir: Path = HARMONIC_DIR) -> pd.DataFrame:
    """
    Load reconstruction_metrics.csv for a station.
    Contains seasonal_applied flag and full-record R2/RMSE values.
    Note: fbar column here is full-record — DIAGNOSTIC ONLY.
    """
    return load_fbar(station, harmonic_dir)


def load_insar_harmonic_ts(station: str, harmonic_dir: Path = HARMONIC_DIR) -> pd.DataFrame:
    """
    Load InSAR harmonic timeseries exported by 01_seasonal_harmonic_analysis.py.
    Columns: datetime, A1_x_seasonal (detrended InSAR), A1_x_annual_model (annual fit).
    Returns DataFrame with datetime as column (not index).
    """
    path = harmonic_dir / station / 'insar_harmonic_timeseries.feather'
    if not path.exists():
        raise FileNotFoundError(
            f"insar_harmonic_timeseries.feather not found for {station}: {path}"
        )
    df = pd.read_feather(path)
    if 'datetime' not in df.columns:
        raise ValueError(f"'datetime' column missing in {path.name}")
    df['datetime'] = pd.to_datetime(df['datetime'])
    return df.sort_values('datetime').reset_index(drop=True)


def insar_series_for_station(insar_df: pd.DataFrame, station: str) -> pd.Series:
    """
    Extract InSAR timeseries for one station from the loaded stations DataFrame.
    Returns pd.Series indexed by datetime, values in mm.
    """
    if station not in insar_df.index:
        raise KeyError(f"Station '{station}' not found in InSAR DataFrame.")
    row = insar_df.loc[station]
    ecols = [c for c in insar_df.columns if c.startswith(_EPOCH_PREFIX) and len(c) == 9]
    dates = pd.to_datetime([c[1:] for c in ecols], format='%Y%m%d')
    series = pd.Series(row[ecols].values.astype(float), index=dates, name=station)
    return series.sort_index()
