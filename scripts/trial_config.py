#!/usr/bin/env python
"""
trial_config.py — shared trial/run machinery for the 012_ml_nowcast pipeline.

Each "trial" is a self-contained run folder:

    trials/<run_id>/
        config.json     # what the run used (driver map, features, model, split)
        results/        # feature_table.csv, *_meta.json, nowcast_metrics.json, predictions
        figures/        # the PNGs

Scripts 03/05/06/07 import this, call `init(description=...)` to parse `--run`,
then read their parameters from the resolved config. A run with no config.json
falls back to DEFAULT_CONFIG (= the v1 baseline), so a bare run reproduces v1.

Library module (no digit prefix) — import normally:  `import trial_config as tc`.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
METHOD_DIR = SCRIPT_DIR.parent
RAW_DIR = METHOD_DIR / "raw_data"
INPUT_DIR = METHOD_DIR / "input_data"
TRIALS_DIR = METHOD_DIR / "trials"
INDEX_CSV = TRIALS_DIR / "trials_index.csv"

DEFAULT_RUN = "run_001"

# ---------------------------------------------------------------- baseline config
# The v1 baseline. A run_NNN/config.json overrides any subset of these keys.
DEFAULT_CONFIG = {
    "label": "v1 baseline (v4 driver assignment)",
    "span": ["2012-08-01", "2023-02-01"],
    "section_well": {
        "S1": ["09050111", "monthly_gwl_timeseries_HONGLUN_09050111.csv"],
        "S2": ["09050321", "monthly_gwl_timeseries_TUKU_09050321.csv"],
        "S3": ["09050321", "monthly_gwl_timeseries_TUKU_09050321.csv"],
        "S4": ["09170121", "monthly_gwl_timeseries_LUNZI_09170121.csv"],
        "S5": ["09050331", "monthly_gwl_timeseries_TUKU_09050331.csv"],
        "S6": ["09080251", "monthly_gwl_timeseries_LIUZHUANG_09080251.csv"],
    },
    "gwl_lags": [1, 3, 6, 12],
    "ds_lags": [1, 3],
    "rain_windows": [3, 6, 12],
    "split": {
        "train": ["2012-08-01", "2018-12-31"],
        "val": ["2019-01-01", "2020-12-31"],
        "test": ["2021-01-01", "2023-02-28"],
    },
    "model": "BayesianRidge",
    "alpha": 0.10,
    "tier1_features": [],
    "conformal_mode": "global",
}


# ---------------------------------------------------------------- run resolution
def parse_run_arg(description: str = "") -> str:
    """Parse `--run <id>` from the CLI. Default = run_001."""
    ap = argparse.ArgumentParser(description=description)
    ap.add_argument("--run", default=DEFAULT_RUN,
                    help="trial run id (folder under trials/), e.g. run_002")
    args, _ = ap.parse_known_args()
    return args.run


def run_dir(run_id: str) -> Path:
    return TRIALS_DIR / run_id


def results_dir(run_id: str) -> Path:
    d = run_dir(run_id) / "results"
    d.mkdir(parents=True, exist_ok=True)
    return d


def figures_dir(run_id: str) -> Path:
    d = run_dir(run_id) / "figures"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------- config I/O
def load_config(run_id: str) -> dict:
    """Return the run's config, merged onto DEFAULT_CONFIG. Missing file = baseline."""
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))  # deep copy
    path = run_dir(run_id) / "config.json"
    if path.exists():
        user = json.loads(path.read_text(encoding="utf-8"))
        cfg.update(user)  # top-level override (section_well replaced wholesale if given)
    cfg["run_id"] = run_id
    return cfg


def write_config(run_id: str, cfg: dict) -> Path:
    """Persist the resolved config into the run dir (provenance). Drops run_id key."""
    out = run_dir(run_id) / "config.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    to_save = {k: v for k, v in cfg.items() if k != "run_id"}
    to_save["_written_utc"] = datetime.now(timezone.utc).isoformat()
    out.write_text(json.dumps(to_save, indent=2), encoding="utf-8")
    return out


# ---------------------------------------------------------------- trials index
INDEX_COLS = [
    "run_id", "label", "generated_utc",
    "pooled_r2", "pooled_skill_persist", "coverage",
    "S1_r2", "S2_r2", "S3_r2", "S4_r2", "S5_r2", "S6_r2",
]


def append_index(run_id: str, label: str, metrics: dict) -> None:
    """Upsert one row per run into trials/trials_index.csv from a metrics dict."""
    TRIALS_DIR.mkdir(parents=True, exist_ok=True)
    ps = metrics.get("per_section", {})
    row = {
        "run_id": run_id,
        "label": label,
        "generated_utc": metrics.get("generated_utc", ""),
        "pooled_r2": round(metrics["pooled"]["r2"], 4),
        "pooled_skill_persist": round(metrics["pooled"]["skill_vs_persistence"], 4),
        "coverage": round(metrics["pooled"]["conformal_coverage"], 4),
    }
    for s in ["S1", "S2", "S3", "S4", "S5", "S6"]:
        row[f"{s}_r2"] = round(ps.get(s, {}).get("r2", float("nan")), 4)

    if INDEX_CSV.exists():
        df = pd.read_csv(INDEX_CSV, dtype={"run_id": str})
        df = df[df["run_id"] != run_id]  # replace existing row for this run
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])
    df = df[INDEX_COLS].sort_values("run_id").reset_index(drop=True)
    df.to_csv(INDEX_CSV, index=False)
