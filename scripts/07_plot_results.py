#!/usr/bin/env python
"""
07_plot_results.py — visualize the ML-nowcast RESULTS.

Pure plotting from saved artifacts (no re-training). Run AFTER 05_train_nowcast.py.

Reads:
  results/feature_table.csv, results/nowcast_predictions.csv, results/nowcast_metrics.json
Produces (figures/):
  - skill_summary.png            per-section R2 + skill-vs-persistence bars
  - obs_vs_pred_scatter.png      observed vs predicted, 1:1 line, per section + pooled
  - feature_coefficients.png     standardized coefficients (with rank-1 caveat)
  - pred_vs_actual_by_section.png  (enriched: train/val/test shading)
  - coverage.png                 (enriched: interval-width annotation)

Style: shared viz_style. English.

Usage:
    cd 012_ml_nowcast
    $env:PYTHONPATH=""; conda run -n fafalab2 python scripts/07_plot_results.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import trial_config as tc  # noqa: E402
import viz_style as vs  # noqa: E402

RUN_ID = tc.parse_run_arg("Plot the ML-nowcast results for a trial.")
CONFIG = tc.load_config(RUN_ID)
RESULTS_DIR = tc.results_dir(RUN_ID)
FIGURES_DIR = tc.figures_dir(RUN_ID)

vs.apply_rcparams()

TRAIN = tuple(CONFIG["split"]["train"])
VAL = tuple(CONFIG["split"]["val"])
TEST = tuple(CONFIG["split"]["test"])


def load():
    meta = json.loads((RESULTS_DIR / "nowcast_metrics.json").read_text(encoding="utf-8"))
    preds = pd.read_csv(RESULTS_DIR / "nowcast_predictions.csv", parse_dates=["datetime"])
    return meta, preds


# ---------------------------------------------------------------- skill bars
def fig_skill(meta):
    secs = vs.SECTIONS
    r2 = [meta["per_section"][s].get("r2", np.nan) for s in secs]
    skill = [meta["per_section"][s].get("skill_vs_persistence", np.nan) for s in secs]

    x = np.arange(len(secs))
    w = 0.38
    fig, ax = plt.subplots(figsize=(10, 5.5))
    b1 = ax.bar(x - w / 2, r2, w, label="R²", color="#1f77b4", alpha=0.9)
    b2 = ax.bar(x + w / 2, skill, w, label="skill vs persistence",
                color="#ff7f0e", alpha=0.9)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(secs)
    ax.set_ylabel("score (test)")
    ax.set_ylim(min(-1.0, min(skill + r2) - 0.2), 1.05)
    ax.set_title("Per-section skill — pooled R²(test)="
                 f"{meta['pooled']['r2']:.2f}, skill_vs_persistence="
                 f"{meta['pooled']['skill_vs_persistence']:.2f}")
    for bars in (b1, b2):
        for rect in bars:
            h = rect.get_height()
            ax.annotate(f"{h:+.2f}", (rect.get_x() + rect.get_width() / 2, h),
                        ha="center", va="bottom" if h >= 0 else "top", fontsize=7)
    ax.legend()
    vs.style_ax(ax)
    out = FIGURES_DIR / "skill_summary.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"wrote {out}")


# ---------------------------------------------------------------- 1:1 scatter
def fig_obs_vs_pred(preds):
    test = preds[preds["set"] == "test"].dropna(subset=["y_pred"])
    fig, axes = plt.subplots(2, 4, figsize=(17, 8))
    axes = axes.ravel()
    # per section
    for ax, s in zip(axes[:6], vs.SECTIONS):
        sub = test[test["section"] == s]
        ax.scatter(sub["y_true"], sub["y_pred"], color=vs.SECTION_COLORS[s],
                   s=22, alpha=0.7)
        lim = _sym_lim(sub["y_true"], sub["y_pred"])
        ax.plot(lim, lim, "k--", lw=0.8)
        ax.set_xlim(lim); ax.set_ylim(lim)
        r2 = _r2(sub["y_true"], sub["y_pred"])
        ax.set_title(f"{s}  R²={r2:+.2f}")
        ax.set_xlabel("observed dC"); ax.set_ylabel("predicted dC")
        vs.style_ax(ax)
    # pooled
    axp = axes[6]
    for s in vs.SECTIONS:
        sub = test[test["section"] == s]
        axp.scatter(sub["y_true"], sub["y_pred"], color=vs.SECTION_COLORS[s],
                    s=18, alpha=0.6, label=s)
    lim = _sym_lim(test["y_true"], test["y_pred"])
    axp.plot(lim, lim, "k--", lw=0.8)
    axp.set_xlim(lim); axp.set_ylim(lim)
    axp.set_title(f"POOLED  R²={_r2(test['y_true'], test['y_pred']):+.2f}")
    axp.set_xlabel("observed dC"); axp.set_ylabel("predicted dC")
    axp.legend(fontsize=7, ncol=2)
    vs.style_ax(axp)
    axes[7].axis("off")
    fig.suptitle("Observed vs predicted compaction increment (test set, 1:1 dashed)", y=1.0)
    fig.tight_layout()
    out = FIGURES_DIR / "obs_vs_pred_scatter.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"wrote {out}")


# ---------------------------------------------------------------- coefficients
def fig_coefficients(meta):
    coef = meta["coefficients"]
    names = coef["feature_names"]
    vals = np.array(coef["coef"])
    order = np.argsort(np.abs(vals))  # ascending, biggest at top after barh
    names = [names[i] for i in order]
    vals = vals[order]
    colors = [vs.POS_COLOR if v >= 0 else vs.NEG_COLOR for v in vals]

    fig, ax = plt.subplots(figsize=(9, 9))
    ax.barh(range(len(vals)), vals, color=colors, alpha=0.9)
    ax.set_yticks(range(len(vals)))
    ax.set_yticklabels(names, fontsize=8)
    ax.axvline(0, color="k", lw=0.8)
    ax.set_xlabel("standardized coefficient")
    ax.set_title("Bayesian Ridge standardized coefficients")
    ax.text(0.5, -0.07,
            "Pooled associations — NOT a per-layer attribution of the surface "
            "signal (carrier rank-1, GEMINI.md).",
            transform=ax.transAxes, ha="center", va="top", fontsize=8,
            style="italic", color="#555555")
    vs.style_ax(ax)
    fig.tight_layout()
    out = FIGURES_DIR / "feature_coefficients.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"wrote {out}")


# ---------------------------------------------------------------- enriched pred-vs-actual
def fig_pred_vs_actual(preds):
    fig, axes = plt.subplots(2, 3, figsize=(15, 8), sharex=True)
    for ax, s in zip(axes.ravel(), vs.SECTIONS):
        sub = preds[(preds["section"] == s)].sort_values("datetime")
        # full actual line (all sets)
        ax.plot(sub["datetime"], sub["y_true"], color="k", lw=1.2, label="actual")
        # test predictions + band
        te = sub[sub["set"] == "test"].dropna(subset=["y_pred"])
        ax.fill_between(te["datetime"], te["lower"], te["upper"],
                        color=vs.SECTION_COLORS[s], alpha=0.2, label="90% conformal")
        ax.plot(te["datetime"], te["y_pred"], color=vs.SECTION_COLORS[s], lw=1.3,
                label="predicted")
        ax.axhline(0, color="grey", lw=0.5)
        ax.set_title(s)
        vs.style_ax(ax)
        vs.shade_splits(ax, TRAIN, VAL, TEST)
    axes.ravel()[0].legend(fontsize=7)
    fig.suptitle("Nowcast vs actual — full series; predictions on TEST (yellow). "
                 "val=grey", y=1.0)
    fig.supylabel("dC (mm/mo, neg = compaction)")
    fig.tight_layout()
    out = FIGURES_DIR / "pred_vs_actual_by_section.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"wrote {out}")


# ---------------------------------------------------------------- coverage
def fig_coverage(meta):
    secs = [s for s in vs.SECTIONS if meta["per_section"][s].get("n", 0) > 0]
    cov = [meta["per_section"][s]["conformal_coverage"] for s in secs]
    width = [meta["per_section"][s]["mean_interval_width"] for s in secs]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    ax1.bar(secs, cov, color=[vs.SECTION_COLORS[s] for s in secs], alpha=0.85)
    ax1.axhline(1 - meta["alpha"], color="tab:red", ls="--",
                label=f"target {1-meta['alpha']:.2f}")
    ax1.axhline(meta["pooled"]["conformal_coverage"], color="k", ls=":",
                label=f"pooled {meta['pooled']['conformal_coverage']:.2f}")
    ax1.set_ylim(0, 1.05)
    ax1.set_ylabel("empirical coverage (test)")
    ax1.set_title("Conformal 90% coverage per section")
    ax1.legend(fontsize=8)
    vs.style_ax(ax1)

    ax2.bar(secs, width, color=[vs.SECTION_COLORS[s] for s in secs], alpha=0.85)
    ax2.axhline(meta["pooled"]["mean_interval_width"], color="k", ls=":",
                label=f"pooled {meta['pooled']['mean_interval_width']:.2f}")
    ax2.set_ylabel("mean interval width (mm/mo)")
    ax2.set_title("Interval sharpness per section")
    ax2.legend(fontsize=8)
    vs.style_ax(ax2)
    fig.tight_layout()
    out = FIGURES_DIR / "coverage.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"wrote {out}")


# ---------------------------------------------------------------- helpers
def _r2(yt, yp):
    yt, yp = np.asarray(yt, float), np.asarray(yp, float)
    ss_res = np.sum((yt - yp) ** 2)
    ss_tot = np.sum((yt - yt.mean()) ** 2)
    return 1 - ss_res / ss_tot if ss_tot > 0 else np.nan


def _sym_lim(a, b):
    lo = min(np.min(a), np.min(b))
    hi = max(np.max(a), np.max(b))
    pad = 0.05 * (hi - lo or 1)
    return [lo - pad, hi + pad]


def main():
    meta, preds = load()
    fig_skill(meta)
    fig_obs_vs_pred(preds)
    fig_coefficients(meta)
    fig_pred_vs_actual(preds)
    fig_coverage(meta)


if __name__ == "__main__":
    main()
