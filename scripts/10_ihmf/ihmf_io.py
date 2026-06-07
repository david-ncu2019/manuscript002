"""
ihmf_io.py — Data loading and alignment for IHM-F.

Public API:
    load_and_align(entry, project_root, insar_csv_path) -> (merged, meta)

    merged : pd.DataFrame with columns datetime, insar_mm, head_m, mlcw_mm
             insar_mm is in mm, original sign (negative = subsidence).
             head_m   is piezometric head in m above MSL (higher = GWL rises).
             mlcw_mm  is cumulative compaction in mm (negative = compaction).

    meta   : dict with h_c_depth_m, h_c_head_m, well_elev_m, wellcode,
                       gwl_feather_name, n_epochs
"""

import numpy as np
import pandas as pd
from pathlib import Path


def load_and_align(entry: dict, project_root: Path, insar_csv_path: Path) -> tuple:
    """Load MLCW CSV, GWL feather, and InSAR CSV then align all to the InSAR timeline."""
    station      = entry["station"]
    layer        = entry["layer"]
    wellcode     = str(entry["assigned_wellcode"]).zfill(8)  # 8-digit string — guard against CSV int truncation
    well_elev_m  = entry["well_elev_m"]
    hc_pct       = entry.get("hc_percentile", 10)   # default 10th percentile
    gwl_feather  = project_root / entry["gwl_feather"]
    mlcw_csv     = project_root / entry["mlcw_reconst_csv"]

    # ── MLCW ─────────────────────────────────────────────────────────────
    mlcw = pd.read_csv(mlcw_csv, parse_dates=["datetime"])
    mlcw["datetime"] = pd.to_datetime(mlcw["datetime"]).astype("datetime64[ns]")
    mlcw = mlcw[["datetime", layer]].rename(columns={layer: "mlcw_mm"})

    # ── GWL ──────────────────────────────────────────────────────────────
    gwl_raw = pd.read_feather(gwl_feather)
    gwl_raw["datetime"] = pd.to_datetime(gwl_raw["datetime"]).astype("datetime64[ns]")
    gwl_raw = gwl_raw[["datetime", wellcode]].dropna(subset=[wellcode])
    gwl_raw = gwl_raw.rename(columns={wellcode: "head_m"})

    # ── InSAR ─────────────────────────────────────────────────────────────
    # Keep original sign: negative = subsidence (do NOT negate).
    insar = pd.read_csv(insar_csv_path, parse_dates=[0])
    insar.columns = [c.strip() for c in insar.columns]
    insar["datetime"] = pd.to_datetime(insar.iloc[:, 0]).astype("datetime64[ns]")
    insar = insar[["datetime", station]].dropna(subset=[station])
    insar[station] = insar[station] * 1000.0
    insar = insar.rename(columns={station: "insar_mm"})

    # ── Align to InSAR timeline via merge_asof ────────────────────────────
    insar_sorted = insar.sort_values("datetime").reset_index(drop=True)
    gwl_aligned  = pd.merge_asof(
        insar_sorted[["datetime"]], gwl_raw.sort_values("datetime"),
        on="datetime", direction="nearest", tolerance=pd.Timedelta("3D"))
    mlcw_aligned = pd.merge_asof(
        insar_sorted[["datetime"]], mlcw.sort_values("datetime"),
        on="datetime", direction="nearest", tolerance=pd.Timedelta("3D"))

    merged = (insar_sorted
              .merge(gwl_aligned,  on="datetime")
              .merge(mlcw_aligned, on="datetime")
              .sort_values("datetime").reset_index(drop=True))
    for dup in ["insar_mm_x", "insar_mm_y"]:
        if dup in merged.columns:
            merged = merged.drop(columns=[dup])

    # ── Pre-consolidation head: lowest GWL before InSAR series starts ────────
    # Bug F fix: h_c must be computed from raw GWL rows dated BEFORE REF_DATE
    # (2015-01-16), before the InSAR record begins.  Using the full record
    # includes post-2015 drought lows that push h_c below the study-period range,
    # misclassifying up to ~51% of epochs as elastic (head > h_c when it should not).
    REF_DATE = pd.Timestamp("2015-01-16")
    pre_ref_mask = gwl_raw["datetime"] < REF_DATE
    if pre_ref_mask.sum() >= 10:
        h_c_head = float(gwl_raw.loc[pre_ref_mask, "head_m"].dropna().min())
    else:
        h_c_head = float(gwl_raw["head_m"].dropna().min())
    h_c_depth = well_elev_m - h_c_head

    meta = {
        "station":          station,
        "layer":            layer,
        "wellcode":         wellcode,
        "well_elev_m":      well_elev_m,
        "gwl_feather_name": gwl_feather.name,
        "h_c_head_m":       h_c_head,
        "h_c_depth_m":      h_c_depth,
        "n_epochs":         len(merged),
    }
    return merged, meta
