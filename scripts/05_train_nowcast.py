#!/usr/bin/env python
"""
05_train_nowcast.py — pooled (section x month) Bayesian Ridge nowcast + conformal intervals.

Pipeline position: run AFTER 03_build_feature_table.py.

What it does
------------
- Loads ../results/feature_table.csv (one row per month x section).
- Temporal (time-block) split, NEVER random:
      train 2012-08 .. 2018-12   (fit model + scaler)
      val   2019-01 .. 2020-12   (conformal calibration)
      test  2021-01 .. 2023-02   (held-out evaluation)
- StandardScaler fit on TRAIN only -> transform val/test.
- BayesianRidge point model; split-conformal 90% intervals (04_conformal.py),
  calibrated on val residuals, applied to test.
- Metrics per-section and pooled: R2, RMSE, MAE, skill vs persistence, skill vs
  train-mean baseline, conformal coverage, mean interval width.
- Writes:
      ../results/nowcast_metrics.json
      ../results/nowcast_predictions.csv
      ../figures/pred_vs_actual_by_section.png
      ../figures/residuals.png
      ../figures/coverage.png

Physics caveat (GEMINI.md): at-well nowcasting; the rank-1 carrier forbids
interpreting per-section predictions as a decomposition of the surface signal.

Usage
-----
    cd 012_ml_nowcast
    $env:PYTHONPATH=""; conda run -n fafalab2 python scripts/05_train_nowcast.py
"""

from __future__ import annotations

import importlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.linear_model import BayesianRidge
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

# ---------------------------------------------------------------- trial wiring
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import trial_config as tc  # noqa: E402

RUN_ID = tc.parse_run_arg("Train the pooled Bayesian Ridge nowcast + conformal for a trial.")
CONFIG = tc.load_config(RUN_ID)
RESULTS_DIR = tc.results_dir(RUN_ID)
FIGURES_DIR = tc.figures_dir(RUN_ID)

# conformal helper has a digit-prefixed filename -> import via importlib
conf = importlib.import_module("04_conformal")

# ---------------------------------------------------------------- config
TRAIN = tuple(CONFIG["split"]["train"])
VAL = tuple(CONFIG["split"]["val"])
TEST = tuple(CONFIG["split"]["test"])
ALPHA = float(CONFIG["alpha"])  # 90% intervals
CONFORMAL_MODE = str(CONFIG.get("conformal_mode", "global"))
assert CONFORMAL_MODE in {"global", "per_section"}, (
    f"unknown conformal_mode: {CONFORMAL_MODE}"
)
SECTIONS = ["S1", "S2", "S3", "S4", "S5", "S6"]


def load_table() -> tuple[pd.DataFrame, list[str]]:
    meta = json.loads((RESULTS_DIR / "feature_table_meta.json").read_text(encoding="utf-8"))
    feat = meta["feature_columns"]
    df = pd.read_csv(RESULTS_DIR / "feature_table.csv", parse_dates=["datetime"])
    df = df.sort_values(["datetime", "section"]).reset_index(drop=True)
    return df, feat


def block(df: pd.DataFrame, span: tuple[str, str]) -> pd.DataFrame:
    lo, hi = pd.Timestamp(span[0]), pd.Timestamp(span[1])
    return df[(df["datetime"] >= lo) & (df["datetime"] <= hi)].copy()


def rmse(a, b) -> float:
    return float(np.sqrt(mean_squared_error(a, b)))


def regression_metrics(y_true, y_pred) -> dict:
    return {
        "n": int(len(y_true)),
        "r2": float(r2_score(y_true, y_pred)) if len(y_true) > 1 else float("nan"),
        "rmse": rmse(y_true, y_pred),
        "mae": float(mean_absolute_error(y_true, y_pred)),
    }


def main() -> None:
    df, FEAT = load_table()

    tr, va, te = block(df, TRAIN), block(df, VAL), block(df, TEST)

    # Split-ordering guards.
    assert tr["datetime"].max() < va["datetime"].min(), "train/val overlap"
    assert va["datetime"].max() < te["datetime"].min(), "val/test overlap"
    for name, blk in (("train", tr), ("val", va), ("test", te)):
        assert len(blk) > 0, f"{name} block empty"

    # Scale on TRAIN only.
    scaler = StandardScaler().fit(tr[FEAT].values)
    Xtr = scaler.transform(tr[FEAT].values)
    Xva = scaler.transform(va[FEAT].values)
    Xte = scaler.transform(te[FEAT].values)
    ytr, yva, yte = tr["y"].values, va["y"].values, te["y"].values

    # Point model.
    model = BayesianRidge(fit_intercept=True)
    model.fit(Xtr, ytr)
    pred_va = model.predict(Xva)
    pred_te = model.predict(Xte)

    # Split-conformal 90% intervals (calibrate on val, apply to test).
    # Mode: "global" uses a single q for all sections (v1 default); "per_section"
    # uses one q per section (Mondrian-style, requires sufficient cal n per section).
    if CONFORMAL_MODE == "per_section":
        lower, upper, q_by_section = conf.per_section_split_conformal_predict(
            pred_va, yva, va["section"].values,
            pred_te, te["section"].values,
            alpha=ALPHA,
        )
        # For metrics provenance: pooled-mode q if we had used global, plus per-section dict.
        _, _, q_pooled_equivalent = conf.split_conformal_predict(
            pred_va, yva, pred_te, alpha=ALPHA
        )
        q = q_pooled_equivalent  # reported only for reference; not applied
    else:
        lower, upper, q = conf.split_conformal_predict(pred_va, yva, pred_te, alpha=ALPHA)
        q_by_section = None
    coverage_pooled = conf.empirical_coverage(yte, lower, upper)
    width_pooled = float(np.mean(upper - lower))

    # Baselines on test, computed per section to keep the time series contiguous.
    te = te.copy()
    te["y_pred"] = pred_te
    te["lower"] = lower
    te["upper"] = upper
    te["in_interval"] = (yte >= lower) & (yte <= upper)

    train_mean_by_section = tr.groupby("section")["y"].mean().to_dict()

    # ---------- metrics ----------
    metrics = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "model": "BayesianRidge",
        "alpha": ALPHA,
        "conformal_mode": CONFORMAL_MODE,
        "conformal_q": q,
        "conformal_q_by_section": q_by_section,
        "splits": {"train": TRAIN, "val": VAL, "test": TEST},
        "n": {"train": int(len(tr)), "val": int(len(va)), "test": int(len(te))},
        # Coefficients of BayesianRidge fit on StandardScaler'd X -> already
        # standardized, directly comparable. NOTE: pooled associations, NOT a
        # per-layer attribution of the surface signal (carrier rank-1, GEMINI.md).
        "coefficients": {
            "feature_names": list(FEAT),
            "coef": [float(c) for c in model.coef_],
            "intercept": float(model.intercept_),
            "note": "standardized association in a pooled model; not per-layer attribution",
        },
        "pooled": {},
        "per_section": {},
    }

    # pooled
    pooled = regression_metrics(yte, pred_te)
    # pooled baselines
    persist_pred_pooled, persist_true_pooled = [], []
    mean_pred_pooled = []
    for s in SECTIONS:
        sub = te[te["section"] == s].sort_values("datetime")
        if len(sub) == 0:
            continue
        yp = sub["y"].shift(1)  # persistence within section
        valid = yp.notna()
        persist_pred_pooled.append(yp[valid].values)
        persist_true_pooled.append(sub["y"][valid].values)
        mean_pred_pooled.append(np.full(len(sub), train_mean_by_section.get(s, np.nan)))
    persist_pred_pooled = np.concatenate(persist_pred_pooled) if persist_pred_pooled else np.array([])
    persist_true_pooled = np.concatenate(persist_true_pooled) if persist_true_pooled else np.array([])
    mean_pred_pooled = np.concatenate(mean_pred_pooled) if mean_pred_pooled else np.array([])

    rmse_persist = rmse(persist_true_pooled, persist_pred_pooled) if len(persist_true_pooled) else float("nan")
    rmse_mean = rmse(yte, mean_pred_pooled) if len(mean_pred_pooled) else float("nan")
    # model rmse restricted to the persistence-valid rows, for a fair skill comparison
    metrics["pooled"] = {
        **pooled,
        "skill_vs_persistence": float(1 - pooled["rmse"] / rmse_persist) if rmse_persist and not np.isnan(rmse_persist) else float("nan"),
        "skill_vs_mean": float(1 - pooled["rmse"] / rmse_mean) if rmse_mean and not np.isnan(rmse_mean) else float("nan"),
        "rmse_persistence": rmse_persist,
        "rmse_mean_baseline": rmse_mean,
        "conformal_coverage": coverage_pooled,
        "mean_interval_width": width_pooled,
    }

    # per section
    for s in SECTIONS:
        sub = te[te["section"] == s].sort_values("datetime")
        if len(sub) == 0:
            metrics["per_section"][s] = {"n": 0}
            continue
        yt = sub["y"].values
        yp = sub["y_pred"].values
        m = regression_metrics(yt, yp)

        persist = sub["y"].shift(1)
        pv = persist.notna()
        rp = rmse(sub["y"][pv].values, persist[pv].values) if pv.sum() else float("nan")
        rm = rmse(yt, np.full(len(sub), train_mean_by_section.get(s, np.nan)))
        m["skill_vs_persistence"] = float(1 - m["rmse"] / rp) if rp and not np.isnan(rp) else float("nan")
        m["skill_vs_mean"] = float(1 - m["rmse"] / rm) if rm else float("nan")
        m["conformal_coverage"] = conf.empirical_coverage(yt, sub["lower"].values, sub["upper"].values)
        m["mean_interval_width"] = float(np.mean(sub["upper"].values - sub["lower"].values))
        metrics["per_section"][s] = m

    # ---------- write predictions ----------
    out = df[["datetime", "section", "y"]].copy().rename(columns={"y": "y_true"})

    def label_set(d: pd.Timestamp) -> str:
        if pd.Timestamp(TRAIN[0]) <= d <= pd.Timestamp(TRAIN[1]):
            return "train"
        if pd.Timestamp(VAL[0]) <= d <= pd.Timestamp(VAL[1]):
            return "val"
        if pd.Timestamp(TEST[0]) <= d <= pd.Timestamp(TEST[1]):
            return "test"
        return "out"
    out["set"] = out["datetime"].apply(label_set)
    # attach test predictions/intervals
    te_idx = te.set_index(["datetime", "section"])
    out = out.set_index(["datetime", "section"])
    out["y_pred"] = te_idx["y_pred"]
    out["lower"] = te_idx["lower"]
    out["upper"] = te_idx["upper"]
    out["in_interval"] = te_idx["in_interval"]
    out = out.reset_index().sort_values(["datetime", "section"])
    out.to_csv(RESULTS_DIR / "nowcast_predictions.csv", index=False)

    metrics["run_id"] = RUN_ID
    metrics["label"] = CONFIG.get("label", "")
    (RESULTS_DIR / "nowcast_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    tc.append_index(RUN_ID, CONFIG.get("label", ""), metrics)

    # ---------- figures ----------
    _fig_pred_vs_actual(te)
    _fig_residuals(te)
    _fig_coverage(metrics)

    # ---------- console ----------
    print(f"[{RUN_ID}] {CONFIG.get('label','')}")
    print(f"n: train={len(tr)} val={len(va)} test={len(te)}")
    print(f"POOLED test: R2={pooled['r2']:.3f}  RMSE={pooled['rmse']:.3f}  MAE={pooled['mae']:.3f}")
    print(f"  skill vs persistence={metrics['pooled']['skill_vs_persistence']:.3f}  "
          f"vs mean={metrics['pooled']['skill_vs_mean']:.3f}")
    print(f"  conformal coverage={coverage_pooled:.3f} (target {1-ALPHA:.2f})  "
          f"mean width={width_pooled:.3f}  mode={CONFORMAL_MODE}")
    if CONFORMAL_MODE == "per_section" and q_by_section is not None:
        for s, info in q_by_section.items():
            print(f"    {s} q={info['q']:.3f}  n_cal={info['n_cal']}")
    print("Per-section test R2 / skill_persist / coverage:")
    for s in SECTIONS:
        m = metrics["per_section"][s]
        if m.get("n", 0) == 0:
            print(f"  {s}: (no test rows)")
            continue
        print(f"  {s}: R2={m['r2']:+.3f}  skill={m['skill_vs_persistence']:+.3f}  cov={m['conformal_coverage']:.2f}")

    # soft coverage warning
    if not (0.85 <= coverage_pooled <= 0.95):
        print(f"WARNING: pooled coverage {coverage_pooled:.3f} outside [0.85,0.95] (small-n variance).")


def _fig_pred_vs_actual(te: pd.DataFrame) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(15, 8), sharex=True)
    for ax, s in zip(axes.ravel(), SECTIONS):
        sub = te[te["section"] == s].sort_values("datetime")
        if len(sub) == 0:
            ax.set_title(f"{s} (no test rows)")
            continue
        ax.fill_between(sub["datetime"], sub["lower"], sub["upper"],
                        color="tab:blue", alpha=0.2, label="90% conformal")
        ax.plot(sub["datetime"], sub["y"], "k-", lw=1.4, label="actual")
        ax.plot(sub["datetime"], sub["y_pred"], "tab:red", lw=1.2, label="predicted")
        ax.set_title(s)
        ax.axhline(0, color="grey", lw=0.5)
    axes.ravel()[0].legend(fontsize=8)
    fig.suptitle("Test nowcast: monthly compaction increment (mm/month) — per section")
    fig.supylabel("dC (mm/month, negative = compaction)")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "pred_vs_actual_by_section.png", dpi=130)
    plt.close(fig)


def _fig_residuals(te: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    for s in SECTIONS:
        sub = te[te["section"] == s]
        if len(sub) == 0:
            continue
        resid = sub["y"].values - sub["y_pred"].values
        ax.scatter(sub["y_pred"].values, resid, s=18, alpha=0.6, label=s)
    ax.axhline(0, color="k", lw=0.7)
    ax.set_xlabel("predicted dC (mm/month)")
    ax.set_ylabel("residual (actual - predicted)")
    ax.set_title("Test residuals vs predicted")
    ax.legend(fontsize=8, ncol=3)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "residuals.png", dpi=130)
    plt.close(fig)


def _fig_coverage(metrics: dict) -> None:
    secs = [s for s in SECTIONS if metrics["per_section"][s].get("n", 0) > 0]
    cov = [metrics["per_section"][s]["conformal_coverage"] for s in secs]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(secs, cov, color="tab:blue", alpha=0.8)
    ax.axhline(1 - metrics["alpha"], color="tab:red", ls="--", label=f"target {1-metrics['alpha']:.2f}")
    ax.axhline(metrics["pooled"]["conformal_coverage"], color="k", ls=":",
               label=f"pooled {metrics['pooled']['conformal_coverage']:.2f}")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("empirical coverage (test)")
    ax.set_title("Conformal 90% interval coverage per section")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "coverage.png", dpi=130)
    plt.close(fig)


if __name__ == "__main__":
    main()
