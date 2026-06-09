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

    # Drop epochs where any layer has NaN head_m or mlcw_mm (caused by GWL/MLCW
    # record ending before InSAR record ends).  All layers use the same valid mask
    # so the shared-timeline invariant is preserved after filtering.
    valid_mask = np.ones(len(insar_mm), dtype=bool)
    for lyr, df in layer_dfs.items():
        valid_mask &= df["head_m"].notna().values
        valid_mask &= df["mlcw_mm"].notna().values
    valid_mask &= np.isfinite(insar_mm)

    if not valid_mask.all():
        n_dropped = int((~valid_mask).sum())
        print(f"  [io] {station}: dropping {n_dropped} NaN epoch(s) — "
              f"keeping {valid_mask.sum()} of {len(insar_mm)}")
        for lyr in layer_dfs:
            layer_dfs[lyr] = layer_dfs[lyr].iloc[valid_mask].reset_index(drop=True)
        insar_mm = insar_mm[valid_mask]

    return layer_dfs, layer_metas, insar_mm


_REF_DATE = pd.Timestamp("2015-01-16")


def load_all_layers_gps(
    station: str,
    config_entries: list[dict],
    project_root: Path,
    tau_demo_dir: Path,
) -> tuple[dict, dict, np.ndarray]:
    """
    GPS-mode loader for the TUKU pilot (5-day cadence).

    Uses feathers from tau_demo_dir exclusively. Master timeline = 5-day MLCW
    feather epochs. GPS vertical displacement (mm, negative=subsidence) replaces
    InSAR as the Step-2 calibration signal returned as 'insar_mm'.

    Parameters
    ----------
    station : str
        Station name (currently only 'TUKU' is supported).
    config_entries : list[dict]
        All entries from ihmf_config.json['entries'] (unfiltered).
    project_root : Path
        Repo root (used only to look up config entries; data comes from tau_demo_dir).
    tau_demo_dir : Path
        Path to tau_demo_TUKU/data/ directory.

    Returns
    -------
    layer_dfs : dict[str, pd.DataFrame]
        Same schema as load_all_layers: datetime, t_days, insar_mm, head_m, mlcw_mm.
        'insar_mm' holds GPS cumulative vertical displacement (mm).
    layer_metas : dict[str, dict]
    gps_mm : np.ndarray, shape (T,)
        GPS cumulative displacement on the shared 5-day timeline (mm).
    """
    station_entries = [e for e in config_entries if e["station"] == station]
    if not station_entries:
        raise ValueError(f"No config entries found for station '{station}'")

    inc_dir = tau_demo_dir / "incremental_data"

    # ── 1. Master timeline + cumulative MLCW for all layers ───────────────
    mlcw_inc = pd.read_feather(inc_dir / "mlcw_diff_cleaned.feather")
    mlcw_inc["datetime"] = pd.to_datetime(mlcw_inc["datetime"]).astype("datetime64[ns]")
    mlcw_inc = mlcw_inc.sort_values("datetime").reset_index(drop=True)

    # Integrate incremental → cumulative per layer column (start from 0 at first epoch)
    layer_cols = [c for c in mlcw_inc.columns if c != "datetime"]
    for col in layer_cols:
        mlcw_inc[f"_cum_{col}"] = mlcw_inc[col].fillna(0.0).cumsum()

    master_frame = pd.DataFrame({"datetime": mlcw_inc["datetime"].copy()})

    # ── 2. GPS: daily cumulative → align to 5-day master ─────────────────
    gps_raw = pd.read_feather(tau_demo_dir / "TUKU_GPS_timeseries.feather")
    gps_raw.rename(columns={gps_raw.columns[0]: "datetime"}, inplace=True)
    gps_raw["datetime"] = pd.to_datetime(gps_raw["datetime"]).astype("datetime64[ns]")
    # 'modeled' is already in mm (range ≈ −127 to −788 mm). Do NOT multiply by 1000.
    gps_raw = gps_raw[["datetime", "modeled"]].rename(columns={"modeled": "insar_mm"})
    gps_raw = gps_raw.sort_values("datetime").reset_index(drop=True)

    gps_aligned = pd.merge_asof(
        master_frame, gps_raw, on="datetime",
        direction="nearest", tolerance=pd.Timedelta("3D"))
    gps_mm_series = gps_aligned["insar_mm"].values.astype(float)  # shape (T,)

    # ── 3. Per-layer GWL alignment and h_c ───────────────────────────────
    layer_dfs:   dict[str, pd.DataFrame] = {}
    layer_metas: dict[str, dict]         = {}

    for entry in station_entries:
        layer       = entry["layer"]
        wellcode    = str(entry["assigned_wellcode"]).zfill(8)
        well_elev_m = entry["well_elev_m"]

        # Feather filename is the last component of the config gwl_feather path
        gwl_fname   = Path(entry["gwl_feather"]).name
        gwl_feather = tau_demo_dir / gwl_fname

        gwl_raw = pd.read_feather(gwl_feather)
        gwl_raw["datetime"] = pd.to_datetime(gwl_raw["datetime"]).astype("datetime64[ns]")
        gwl_raw = gwl_raw[["datetime", wellcode]].dropna(subset=[wellcode])
        gwl_raw = gwl_raw.rename(columns={wellcode: "head_m"})
        gwl_raw = gwl_raw.sort_values("datetime").reset_index(drop=True)

        # ── Zero-reference head to REF_DATE (R1 fix) ────────────────────────
        # Mirror Script 12 load_gwl_absolute() L172–180. Use the RAW daily
        # series (before merge_asof) so the reference value is not distorted
        # by nearest-neighbour alignment across a data gap.
        avail_raw = gwl_raw.set_index("datetime")["head_m"].dropna()
        pre_ref_idx = avail_raw.index[avail_raw.index <= _REF_DATE]
        if len(pre_ref_idx) == 0:
            raise ValueError(
                f"No GWL data on or before REF_DATE ({_REF_DATE.date()}) "
                f"for wellcode {wellcode}"
            )
        head_ref_m = float(avail_raw.loc[pre_ref_idx[-1]])

        gwl_aligned = pd.merge_asof(
            master_frame, gwl_raw, on="datetime",
            direction="nearest", tolerance=pd.Timedelta("3D"))

        cum_col = f"_cum_{layer}"
        if cum_col not in mlcw_inc.columns:
            raise KeyError(
                f"Layer '{layer}' not found in mlcw_diff_cleaned.feather. "
                f"Available: {layer_cols}"
            )

        df = master_frame.copy()
        df["insar_mm"] = gps_mm_series
        df["head_m"]   = gwl_aligned["head_m"].values            # absolute (m MSL)
        df["head_m_zeroed"] = df["head_m"] - head_ref_m          # zero-ref for elastic term
        df["mlcw_mm"]  = mlcw_inc[cum_col].values

        t0 = df["datetime"].iloc[0]
        df["t_days"] = (df["datetime"] - t0).dt.days.astype(float)

        # h_c: lowest GWL before REF_DATE (Bug F fix, R2: also zero-reference)
        pre_ref = gwl_raw[gwl_raw["datetime"] < _REF_DATE]
        if len(pre_ref.dropna(subset=["head_m"])) >= 10:
            h_c_head = float(pre_ref["head_m"].dropna().min())
        else:
            h_c_head = float(gwl_raw["head_m"].dropna().min())
            print(f"  [io-gps] WARN: <10 pre-REF_DATE points for {wellcode} "
                  f"layer {layer} — h_c fallback to full-record minimum")
        h_c_zeroed = h_c_head - head_ref_m                        # R2: shift to zero-ref frame
        h_c_depth = well_elev_m - h_c_head

        layer_dfs[layer]   = df
        layer_metas[layer] = {
            "station":          station,
            "layer":            layer,
            "wellcode":         wellcode,
            "well_elev_m":      well_elev_m,
            "gwl_feather_name": gwl_fname,
            "head_ref_m":       head_ref_m,         # R1: ref value for zero-referencing
            "h_c_head_m":       h_c_head,           # absolute, kept for reference
            "h_c_zeroed":       h_c_zeroed,         # R2: zero-referenced for V computation
            "h_c_depth_m":      h_c_depth,
            "n_epochs":         len(df),
        }

    # ── 4. Step 1 NaN mask (GWL + MLCW only — GPS tracked separately) ──────
    # GPS starts ~2010 and contains NaN for 2003-2010. Intersecting GPS in the
    # validity gate drops the heavy-pumping inelastic era, leaving too few
    # inelastic events to calibrate S_kv. Step 1 trains on the full GWL+MLCW
    # record. GPS NaN appears in the returned gps_mm_series but is harmless:
    # Step 2 OLS is bypassed when an external alpha is supplied via --alpha.
    step1_mask = np.ones(len(gps_mm_series), dtype=bool)
    for lyr, df in layer_dfs.items():
        step1_mask &= df["head_m"].notna().values
        step1_mask &= df["mlcw_mm"].notna().values
    # NOTE: gps_mm_series NaN is NOT intersected here — see docstring above.

    if not step1_mask.all():
        n_dropped = int((~step1_mask).sum())
        print(f"  [io-gps] {station}: dropping {n_dropped} NaN epoch(s) — "
              f"keeping {step1_mask.sum()} of {len(gps_mm_series)}")
        for lyr in layer_dfs:
            layer_dfs[lyr] = layer_dfs[lyr].iloc[step1_mask].reset_index(drop=True)
        gps_mm_series = gps_mm_series[step1_mask]

    return layer_dfs, layer_metas, gps_mm_series


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
