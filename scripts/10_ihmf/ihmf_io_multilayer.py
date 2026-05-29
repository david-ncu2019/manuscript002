"""
ihmf_io_multilayer.py — Load all layers for one station simultaneously.

Public API:
    load_all_layers(station, config_entries, project_root, insar_csv_path)
        -> (layer_dfs, layer_metas, insar_mm)

    layer_dfs   : dict[layer_code -> pd.DataFrame]
                  Each DataFrame has columns: datetime, t_days, insar_mm, head_m, mlcw_mm
                  All DataFrames are aligned to the same InSAR epoch timeline.

    layer_metas : dict[layer_code -> meta dict]
                  Same meta as load_and_align: h_c_head_m, h_c_depth_m, wellcode, etc.

    insar_mm    : 1-D np.ndarray, shape (T,)
                  InSAR cumulative displacement (mm) on the shared timeline.
                  Sign convention: negative = subsidence (unchanged from ihmf_io.py).
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path

from ihmf_io import load_and_align


def load_all_layers(
    station: str,
    config_entries: list[dict],
    project_root: Path,
    insar_csv_path: Path,
) -> tuple[dict, dict, np.ndarray]:
    """
    Load all layers for one station, all aligned to the InSAR epoch timeline.

    Parameters
    ----------
    station : str
        Station name (e.g. 'TUKU').
    config_entries : list[dict]
        All entries from ihmf_config.json['entries'] (unfiltered — function selects
        the subset matching station).
    project_root : Path
        Root of the scripts/data repository (Windows or Linux path).
    insar_csv_path : Path
        Path to InSAR_measures_at_MLCW.csv.

    Returns
    -------
    layer_dfs : dict[str, pd.DataFrame]
        Keys are layer codes (e.g. 'F1', 'T1', ...).
        Each DataFrame: datetime, t_days, insar_mm, head_m, mlcw_mm.
        t_days is float days from the first InSAR epoch.
    layer_metas : dict[str, dict]
        Keys are layer codes. Values are meta dicts from load_and_align.
    insar_mm : np.ndarray, shape (T,)
        InSAR displacement on the shared timeline (mm, negative = subsidence).
    """
    station_entries = [e for e in config_entries if e["station"] == station]
    if not station_entries:
        raise ValueError(f"No config entries found for station '{station}'")

    layer_dfs: dict[str, pd.DataFrame] = {}
    layer_metas: dict[str, dict] = {}

    for entry in station_entries:
        layer = entry["layer"]
        merged, meta = load_and_align(entry, project_root, insar_csv_path)

        # Add t_days column (float days from first epoch) for detrending
        t0 = merged["datetime"].iloc[0]
        merged = merged.copy()
        merged["t_days"] = (merged["datetime"] - t0).dt.days.astype(float)

        layer_dfs[layer] = merged
        layer_metas[layer] = meta

    # Verify all layers share the same InSAR timeline (they must — same station)
    layers = list(layer_dfs.keys())
    ref_dates = layer_dfs[layers[0]]["datetime"].values
    for lyr in layers[1:]:
        other_dates = layer_dfs[lyr]["datetime"].values
        if len(other_dates) != len(ref_dates) or not (other_dates == ref_dates).all():
            raise ValueError(
                f"Layer {lyr} has a different InSAR timeline than {layers[0]} "
                f"at station {station}. Check ihmf_io.py alignment."
            )

    insar_mm = layer_dfs[layers[0]]["insar_mm"].values.astype(float)

    return layer_dfs, layer_metas, insar_mm


def load_config(project_root: Path) -> tuple[dict, list[dict], Path]:
    """
    Load ihmf_config.json and return (shared_cfg, entries, insar_csv_path).
    Resolves project_root to override the Linux path stored in config.
    """
    config_path = project_root / "data" / "ihmf_config.json"
    with open(config_path) as f:
        cfg = json.load(f)

    entries = cfg["entries"]
    insar_csv = project_root / cfg["shared"]["insar_csv"]

    # Fix paths in entries to use the runtime project_root
    for entry in entries:
        for key in ("gwl_feather", "mlcw_reconst_csv"):
            if key in entry:
                entry[key] = str(Path(entry[key]))  # keep relative; load_and_align prepends root

    return cfg["shared"], entries, insar_csv
