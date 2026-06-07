"""
prepare_stress_strain.py — Convert GWL head + MLCW compaction to stress-strain curves.

Physics:
    Δσ'(t) = -γ_w · [head_m(t) − h_c_head_m]    (effective stress change, kPa)
    ε(t)   = Δb(t) / b_j                          (vertical strain, mm/m)

    γ_w = 9.81 kPa/m  (unit weight of water)
    Reference head = preconsolidation head h_c  (10th percentile by default)

Output:
    {STATION}_{LAYER}_stress_strain.csv with columns:
        datetime, stress_kpa, strain_mm_m, head_m, mlcw_mm, is_elastic, span_m

Usage:
    python scripts/12_stress_strain/prepare_stress_strain.py --station TUKU --all
    python scripts/12_stress_strain/prepare_stress_strain.py --station TUKU --layer F2
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "10_ihmf"))
from ihmf_io import load_and_align

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "data/ihmf_config.json"
LAYER_THICKNESS_CSV = PROJECT_ROOT / "results/data_analysis/layer_thickness.csv"
OUT_DIR = PROJECT_ROOT / "results" / "stress_strain"

GAMMA_W = 9.81  # unit weight of water, kPa/m


def load_layer_thickness() -> dict:
    """Return {(station, layer): span_m} lookup."""
    df = pd.read_csv(LAYER_THICKNESS_CSV)
    lookup = {}
    for _, row in df.iterrows():
        lookup[(row["station"], row["layer"])] = row["span_m"]
    return lookup


def compute(entry: dict, insar_csv_path: Path, thick_lookup: dict) -> Path:
    """Compute stress-strain for one config entry. Returns output CSV path."""
    station = entry["station"]
    layer = entry["layer"]
    tau_max = entry["tau_max"]

    out_subdir = OUT_DIR / station
    out_subdir.mkdir(parents=True, exist_ok=True)
    out_path = out_subdir / f"{station}_{layer}_stress_strain.csv"

    # 1. Load and align (reuses IHM-F data loading)
    merged, meta = load_and_align(entry, PROJECT_ROOT, insar_csv_path)

    h_c_head = meta["h_c_head_m"]
    wellcode = meta["wellcode"]
    n_epochs = len(merged)

    # 2. Load layer thickness
    key = (station, layer)
    span_m = thick_lookup.get(key, np.nan)
    single_ring = bool(span_m == 0.0)
    if single_ring:
        span_m = np.nan  # cannot compute strain

    # 3. Compute stress and strain
    head_m = merged["head_m"].values
    mlcw_mm = merged["mlcw_mm"].values

    stress_kpa = -GAMMA_W * (head_m - h_c_head)
    is_elastic = head_m >= h_c_head

    if np.isfinite(span_m) and span_m > 0:
        strain_mm_m = mlcw_mm / span_m
    else:
        strain_mm_m = np.full_like(mlcw_mm, np.nan)

    # 4. Assemble output
    out = merged[["datetime", "head_m", "mlcw_mm"]].copy()
    out["insar_mm"] = merged["insar_mm"]
    out["stress_kpa"] = np.round(stress_kpa, 4)
    out["strain_mm_m"] = np.round(strain_mm_m, 6)
    out["is_elastic"] = is_elastic
    out["h_c_head_m"] = round(h_c_head, 2)
    out["span_m"] = thick_lookup.get(key, np.nan)
    out["single_ring"] = single_ring
    out["wellcode"] = wellcode
    out["tau_max"] = tau_max

    out.to_csv(out_path, index=False, float_format="%.6g")
    return out_path


def main():
    parser = argparse.ArgumentParser(
        description="Compute stress-strain curves from GWL + MLCW data.")
    parser.add_argument("--station", type=str, required=True, help="Station name (e.g. TUKU)")
    parser.add_argument("--layer", type=str, default=None,
                        help="Layer code (F1/T1/F2/T2/F3/F4). Omit with --all.")
    parser.add_argument("--all", action="store_true",
                        help="Process all layers for the given station.")
    args = parser.parse_args()

    with open(CONFIG_PATH) as f:
        cfg = json.load(f)

    shared = cfg["shared"]
    entries = cfg["entries"]
    insar_csv = PROJECT_ROOT / shared["insar_csv"]
    thick_lookup = load_layer_thickness()

    station_entries = [e for e in entries if e["station"] == args.station]
    if not station_entries:
        raise SystemExit(f"Station '{args.station}' not found in config. "
                         f"Available: {sorted(set(e['station'] for e in entries))}")

    if args.all:
        targets = station_entries
    elif args.layer:
        match = [e for e in station_entries if e["layer"] == args.layer]
        if not match:
            raise SystemExit(f"Layer '{args.layer}' not found for {args.station}. "
                             f"Available: {[e['layer'] for e in station_entries]}")
        targets = [match[0]]
    else:
        raise SystemExit("Specify --layer LAYER or --all.")

    print(f"Stress-strain computation for {args.station}: {len(targets)} layer(s)")
    print(f"  γ_w = {GAMMA_W} kPa/m")
    print(f"  Reference head = h_c (10th percentile head)")
    print()

    for entry in targets:
        try:
            out_path = compute(entry, insar_csv, thick_lookup)
            df = pd.read_csv(out_path)
            n = len(df)
            stress_range = (df["stress_kpa"].min(), df["stress_kpa"].max())
            strain_n_valid = df["strain_mm_m"].notna().sum()
            n_inel = (~df["is_elastic"]).sum()
            single = df["single_ring"].iloc[0]
            tag = " [SINGLE RING — strain=NaN]" if single else ""
            print(f"  {entry['layer']}: {n} epochs  "
                  f"stress=[{stress_range[0]:.1f}, {stress_range[1]:.1f}] kPa  "
                  f"strain={strain_n_valid} valid  "
                  f"inelastic={n_inel}{tag}")
        except Exception as exc:
            print(f"  {entry['layer']}: ERROR — {exc}")

    print(f"\nOutput: {OUT_DIR}/")
    print("Done.")


if __name__ == "__main__":
    main()
