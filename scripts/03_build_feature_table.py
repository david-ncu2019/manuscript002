#!/usr/bin/env python
"""
03_build_feature_table.py — assemble the pooled (section x month) ML feature table.

Pipeline position: run AFTER 01_resample_borehole / 02_compute_section_materials
(which produced input_data/TUKU_section_materials.csv). Run BEFORE 05_train_nowcast.

What it does
------------
Loads the hand-prepared monthly CSVs in ../raw_data/, converts the cumulative
MLCW (target) and GPS (shared surface signal) series to monthly INCREMENTS via
.diff(), attaches each depth-section's assigned GWL well (v4 depth-overlap map),
builds lag / rolling / seasonal / static features, and melts everything into a
long table: one row per (month, section). Writes:

    ../results/feature_table.csv
    ../results/feature_table_meta.json

Sign conventions (GEMINI.md)
----------------------------
- MLCW: negative = compaction. Target y = monthly increment (mostly <= 0).
- GPS:  negative = subsidence. dS_total = monthly increment.
- GWL:  piezometric head in m MSL. NEVER negate (LUNZI head is legitimately
        negative; that is correct).

Physics caveat (rank-1 carrier, GEMINI.md): this is at-well NOWCASTING, not a
per-layer decomposition of the surface signal.

Usage
-----
    cd 012_ml_nowcast
    $env:PYTHONPATH=""; conda run -n fafalab2 python scripts/03_build_feature_table.py --run run_001
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------- trial wiring
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import trial_config as tc  # noqa: E402

RUN_ID = tc.parse_run_arg("Build the pooled (section x month) feature table for a trial.")
CONFIG = tc.load_config(RUN_ID)
RAW_DIR = tc.RAW_DIR
INPUT_DIR = tc.INPUT_DIR
RESULTS_DIR = tc.results_dir(RUN_ID)

# ---------------------------------------------------------------- config-driven constants
SPAN = tuple(CONFIG["span"])

# Cumulative MLCW column  ->  uniform 50 m depth section. (Fixed — input format.)
MLCW_COLS = {
    "000_050_m": "S1",
    "050_100_m": "S2",
    "100_150_m": "S3",
    "150_200_m": "S4",
    "200_250_m": "S5",
    "250_300_m": "S6",
}

# Section -> (wellcode, raw_data filename), from the run config (default = v1 baseline).
SECTION_WELL = {s: tuple(v) for s, v in CONFIG["section_well"].items()}

GWL_LAGS = list(CONFIG["gwl_lags"])
DS_LAGS = list(CONFIG["ds_lags"])
RAIN_WINDOWS = list(CONFIG["rain_windows"])

# Tier 1 physics-informed features (opt-in via run config).
# Recognized names: "V_t", "sigma_eff", "V_t_x_fine_pct".
# When empty (DEFAULT_CONFIG), the feature table is identical to the v1 baseline.
TIER1_FEATURES = list(CONFIG.get("tier1_features", []))
TIER1_ALLOWED = {"V_t", "sigma_eff", "V_t_x_fine_pct"}
_unknown = [t for t in TIER1_FEATURES if t not in TIER1_ALLOWED]
assert not _unknown, f"Unknown tier1 feature(s) in config: {_unknown}"

# Effective stress constants.
# Choushui aquifer-system sediment: mean saturated unit weight gamma = 18 kN/m^3.
# Water unit weight gamma_w = 9.81 kN/m^3. See Yuan et al. (2025), Schjonning &
# Lamande (2018) for the threshold physics; Shi et al. (2022) for the Terzaghi
# vertical-stress form used here.
GAMMA = 18.0
GAMMA_W = 9.81

TARGET = "y"
ID_COLS = ["datetime", "section"]
FEATURE_COLS = (
    ["dS_total"]
    + [f"dS_total_lag{l}" for l in DS_LAGS]
    + ["gwl_head", "dGWL"]
    + [f"gwl_head_lag{l}" for l in GWL_LAGS]
    + [f"dGWL_lag{l}" for l in GWL_LAGS]
    + ["rain"]
    + [f"rain_sum{w}" for w in RAIN_WINDOWS]
    + ["month_sin", "month_cos"]
    + ["depth_mid", "fine_pct", "coarse_pct"]
    + list(TIER1_FEATURES)  # preserves config-defined order
)


# ---------------------------------------------------------------- loaders
def load_mlcw(path: Path) -> pd.DataFrame:
    """Cumulative MLCW, 6 columns renamed to S1..S6. Monthly DatetimeIndex. No diff here."""
    df = pd.read_csv(path, parse_dates=["datetime"]).set_index("datetime")
    df = df[list(MLCW_COLS.keys())].rename(columns=MLCW_COLS)
    return df.sort_index()


def load_gps(path: Path) -> pd.Series:
    """Cumulative surface displacement ('modeled'), monthly. No diff here."""
    df = pd.read_csv(path, parse_dates=["date"]).set_index("date")
    s = df["modeled"].sort_index()
    s.index.name = "datetime"
    return s


def load_gwl(path: Path, code: str) -> pd.Series:
    """One GWL well; head level in m MSL. NEVER negate. Column name == 8-digit code (string)."""
    df = pd.read_csv(path, dtype={code: float})
    df["datetime"] = pd.to_datetime(df["datetime"])
    s = df.set_index("datetime")[code].sort_index()
    return s


def load_rainfall(path: Path) -> pd.Series:
    """Monthly rainfall sum (mm). Date format 'YY/M/01' (92->1992 ... 23->2023)."""
    df = pd.read_csv(path)
    df["datetime"] = pd.to_datetime(df["datetime"], format="%y/%m/%d")
    s = df.set_index("datetime")["values"].astype(float).sort_index()
    s.name = "rain"
    return s


def load_materials(path: Path) -> pd.DataFrame:
    """Static per-section materials. Adds depth_mid. Indexed by section (S1..S6)."""
    df = pd.read_csv(path)
    df["depth_mid"] = (df["depth_top"] + df["depth_bot"]) / 2.0
    return df.set_index("section")[["depth_mid", "fine_pct", "coarse_pct"]]


# ---------------------------------------------------------------- helpers
def add_lags(s: pd.Series, lags: list[int], name: str) -> pd.DataFrame:
    """Past-only lags via shift(L>0)."""
    return pd.DataFrame({f"{name}_lag{l}": s.shift(l) for l in lags})


def trailing_sum(s: pd.Series, windows: list[int], name: str) -> pd.DataFrame:
    """Trailing (current + past W-1) rolling sums; no future leakage."""
    return pd.DataFrame(
        {f"{name}_sum{w}": s.rolling(w, min_periods=w).sum() for w in windows}
    )


# ---------------------------------------------------------------- build
def build() -> tuple[pd.DataFrame, dict]:
    mlcw = load_mlcw(RAW_DIR / "monthly_mlcw_timeseries_TUKU.csv")
    gps = load_gps(RAW_DIR / "monthly_GPS_timeseries_TUKU.csv")
    rain = load_rainfall(RAW_DIR / "monthly_sum_rainfall_TUKU.csv")
    materials = load_materials(INPUT_DIR / "TUKU_section_materials.csv")

    # Increments of the cumulative series.
    mlcw_delta = mlcw.diff()                       # target per section
    dS_total = gps.diff().rename("dS_total")       # shared surface signal

    # Shared (section-independent) dynamic features, computed once.
    shared = pd.DataFrame(index=dS_total.index)
    shared["dS_total"] = dS_total
    shared = shared.join(add_lags(dS_total, DS_LAGS, "dS_total"))
    shared["rain"] = rain
    shared = shared.join(trailing_sum(rain, RAIN_WINDOWS, "rain"))
    shared["month_sin"] = np.sin(2 * np.pi * shared.index.month / 12.0)
    shared["month_cos"] = np.cos(2 * np.pi * shared.index.month / 12.0)

    per_section_counts = {}
    frames = []
    for section, (code, fname) in SECTION_WELL.items():
        head = load_gwl(RAW_DIR / fname, code).rename("gwl_head")
        dGWL = head.diff().rename("dGWL")

        sec = pd.DataFrame(index=mlcw_delta.index)
        sec["y"] = mlcw_delta[section]
        sec = sec.join(shared, how="left")
        sec["gwl_head"] = head
        sec["dGWL"] = dGWL
        sec = sec.join(add_lags(head, GWL_LAGS, "gwl_head"))
        sec = sec.join(add_lags(dGWL, GWL_LAGS, "dGWL"))

        # static
        for col in ("depth_mid", "fine_pct", "coarse_pct"):
            sec[col] = materials.loc[section, col]

        # Tier 1 physics-informed features (gated by config).
        # Computed on the full per-section head series so the causal expanding-min
        # for h_c uses the same anchor as later inference.
        if TIER1_FEATURES:
            # h_c(t) = causal expanding-window minimum of head up to time t.
            # No look-ahead: a row at time t never sees head at t+1 or later.
            h_c = head.expanding(min_periods=1).min()
            V_t = (h_c - head).clip(lower=0.0)  # max(0, h_c - GWL); both in m MSL
            if "V_t" in TIER1_FEATURES:
                sec["V_t"] = V_t
            if "sigma_eff" in TIER1_FEATURES:
                # sigma'_eff = gamma * z_mid - gamma_w * GWL(t)
                # Convention note: gwl_head is m MSL and the project standard treats
                # it directly as the head term in the Terzaghi form (GEMINI.md
                # baseline; LUNZI legitimately negative). Resulting units: kN/m^2.
                z_mid = float(materials.loc[section, "depth_mid"])
                sec["sigma_eff"] = GAMMA * z_mid - GAMMA_W * head
            if "V_t_x_fine_pct" in TIER1_FEATURES:
                fine_pct = float(materials.loc[section, "fine_pct"])
                sec["V_t_x_fine_pct"] = V_t * fine_pct

        sec = sec.loc[SPAN[0]:SPAN[1]].copy()
        sec.insert(0, "section", section)
        sec.index.name = "datetime"
        sec = sec.reset_index()

        # Drop rows with NaN target or any NaN feature (lag burn-in, gaps).
        before = len(sec)
        sec = sec.dropna(subset=[TARGET] + FEATURE_COLS)
        per_section_counts[section] = {"kept": int(len(sec)), "dropped": int(before - len(sec))}
        frames.append(sec)

    table = pd.concat(frames, ignore_index=True)
    table = table.sort_values(["datetime", "section"]).reset_index(drop=True)
    table = table[ID_COLS + [TARGET] + FEATURE_COLS]

    # dS_total identical across sections within a month (shared-surface invariant).
    ds_per_month = table.groupby("datetime")["dS_total"].nunique()
    ds_identical = bool((ds_per_month <= 1).all())

    meta = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "span": SPAN,
        "n_rows": int(len(table)),
        "n_sections": int(table["section"].nunique()),
        "date_min": str(table["datetime"].min().date()),
        "date_max": str(table["datetime"].max().date()),
        "per_section_counts": per_section_counts,
        "target_col": TARGET,
        "feature_columns": FEATURE_COLS,
        "id_columns": ID_COLS,
        "section_well_map": {s: c for s, (c, _) in SECTION_WELL.items()},
        "dS_identical_per_month": ds_identical,
        "gwl_sign_note": "head in m MSL, never negated; LUNZI head legitimately negative",
        "mlcw_resample_note": "source resampled with .last() on cumulative series (user-fixed)",
        "rainfall_end": "2023-02",
        "tier1_features": list(TIER1_FEATURES),
        "tier1_constants": (
            {"gamma_kN_per_m3": GAMMA, "gamma_w_kN_per_m3": GAMMA_W}
            if TIER1_FEATURES else {}
        ),
    }
    return table, meta


def main() -> None:
    tc.write_config(RUN_ID, CONFIG)  # persist provenance into the run dir
    table, meta = build()
    meta["run_id"] = RUN_ID
    meta["label"] = CONFIG.get("label", "")
    out_csv = RESULTS_DIR / "feature_table.csv"
    out_meta = RESULTS_DIR / "feature_table_meta.json"
    table.to_csv(out_csv, index=False)
    with open(out_meta, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)

    print(f"[{RUN_ID}] {CONFIG.get('label','')}")
    print(f"Wrote {len(table)} rows x {table.shape[1]} cols -> {out_csv}")
    print(f"Span: {meta['date_min']} -> {meta['date_max']}")
    print(f"dS_total identical per month: {meta['dS_identical_per_month']}")
    print("Per-section kept/dropped:")
    for s, c in meta["per_section_counts"].items():
        print(f"  {s}: kept={c['kept']:3d}  dropped={c['dropped']:3d}")

    # Hard checks.
    assert table[TARGET].notna().all(), "NaN in target"
    assert table[FEATURE_COLS].notna().all().all(), "NaN in features"
    assert meta["dS_identical_per_month"], "dS_total not identical per month"
    print("Checks passed: no NaN in target/features; surface signal shared per month.")


if __name__ == "__main__":
    main()
