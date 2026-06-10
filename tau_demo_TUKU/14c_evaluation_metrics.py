"""
14c_evaluation_metrics.py — Comprehensive amplitude-aware evaluation metrics.

Reads the 6 reconstruction CSVs and computes metrics that highlight amplitude
differences between observed and predicted timeseries — not just correlation.

Metrics per layer:
  AMPLITUDE:  obs_range, pred_range, range_ratio (1.0=perfect amplitude)
  RATE:       trend_obs, trend_pred, trend_error_pct
  ERROR:      RMSE, NRMSE%, MAE, max_error, bias, end_error, end_error_pct, R²

Outputs:
  tau_demo_TUKU/results/evaluation_metrics.json
  tau_demo_TUKU/results/evaluation_metrics.csv
  tau_demo_TUKU/results/visualization/evaluation_metrics_barchart.png
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
CSV_DIR  = ROOT / "tau_demo_TUKU" / "results" / "reconstruction"
OUT_DIR  = ROOT / "tau_demo_TUKU" / "results"
VIZ_DIR  = OUT_DIR / "visualization"
VIZ_DIR.mkdir(parents=True, exist_ok=True)

LAYERS = ["F1","T1","F2","T2","F3","F4"]


def compute_metrics(obs: np.ndarray, pred: np.ndarray) -> dict:
    """Compute all evaluation metrics from observed and predicted arrays."""
    mask = np.isfinite(obs) & np.isfinite(pred)
    o, p = obs[mask], pred[mask]
    n = len(o)
    if n < 10:
        return {"error": "insufficient data", "n": n}

    residual = o - p
    obs_range = float(o.max() - o.min())
    pred_range = float(p.max() - p.min())

    # Amplitude
    range_ratio = float(pred_range / obs_range) if abs(obs_range) > 1e-10 else float("nan")

    # Error
    rmse = float(np.sqrt(np.mean(residual**2)))
    nrmse_pct = float(rmse / abs(obs_range) * 100) if abs(obs_range) > 1e-10 else float("nan")
    mae = float(np.mean(np.abs(residual)))
    max_error = float(np.max(np.abs(residual)))
    bias = float(np.mean(p - o))

    # End-point
    end_error = float(o[-1] - p[-1])
    end_error_pct = float(end_error / abs(obs_range) * 100) if abs(obs_range) > 1e-10 else float("nan")

    # Correlation
    r2 = float(np.corrcoef(o, p)[0,1]**2)

    # Trend (linear slope, mm per 5-day epoch)
    t = np.arange(n, dtype=float)
    slope_obs = float(np.polyfit(t, o, 1)[0])
    slope_pred = float(np.polyfit(t, p, 1)[0])
    trend_error_pct = float(abs(slope_obs - slope_pred) / abs(slope_obs) * 100) if abs(slope_obs) > 1e-10 else 0.0

    return {
        "n_epochs": n,
        "obs_range_mm": round(obs_range, 4),
        "pred_range_mm": round(pred_range, 4),
        "range_ratio": round(range_ratio, 4),
        "rmse_mm": round(rmse, 4),
        "nrmse_pct": round(nrmse_pct, 2),
        "mae_mm": round(mae, 4),
        "max_error_mm": round(max_error, 4),
        "bias_mm": round(bias, 4),
        "end_error_mm": round(end_error, 4),
        "end_error_pct": round(end_error_pct, 2),
        "r2": round(r2, 4),
        "trend_obs_mm_per_epoch": round(slope_obs, 6),
        "trend_pred_mm_per_epoch": round(slope_pred, 6),
        "trend_error_pct": round(trend_error_pct, 2),
    }


def main():
    results = {}
    for layer in LAYERS:
        df = pd.read_csv(CSV_DIR / f"TUKU_{layer}_reconstruction.csv")
        obs = df["b_observed_mm"].values.astype(float)
        pred = df["b_model_mm"].values.astype(float)
        results[layer] = compute_metrics(obs, pred)

    # ── Print table ──
    header = (f"{'Layer':5s} | {'obs_range':>9s} | {'pred_range':>9s} | {'range_ratio':>10s} | "
              f"{'NRMSE%':>7s} | {'RMSE':>7s} | {'MAE':>7s} | {'max_err':>7s} | "
              f"{'trend_err%':>9s} | {'end_err%':>8s} | {'R²':>6s}")
    print(header)
    print("-" * len(header))
    for layer in LAYERS:
        m = results[layer]
        print(f"{layer:5s} | {m['obs_range_mm']:9.2f} | {m['pred_range_mm']:9.2f} | "
              f"{m['range_ratio']:10.3f} | {m['nrmse_pct']:7.2f} | {m['rmse_mm']:7.2f} | "
              f"{m['mae_mm']:7.2f} | {m['max_error_mm']:7.2f} | "
              f"{m['trend_error_pct']:9.2f} | {m['end_error_pct']:8.2f} | {m['r2']:6.3f}")

    # ── Physical interpretation ──
    print(f"\n── Physical interpretation ──")
    for layer in LAYERS:
        m = results[layer]
        rr = m["range_ratio"]
        if rr < 0.5:
            amp_verdict = f"SEVERE compression — model captures only {rr*100:.0f}% of true amplitude"
        elif rr < 0.8:
            amp_verdict = f"MODERATE compression — model captures {rr*100:.0f}% of true amplitude"
        elif rr < 1.2:
            amp_verdict = f"Good amplitude fidelity ({rr*100:.0f}%)"
        else:
            amp_verdict = f"EXPANSION — model over-predicts amplitude ({rr*100:.0f}%)"
        print(f"  {layer}: {amp_verdict}  |  trend error={m['trend_error_pct']:.1f}%  |  end error={m['end_error_pct']:.1f}%")

    # ── Save JSON + CSV ──
    with open(OUT_DIR / "evaluation_metrics.json", "w") as f:
        json.dump({"metadata": {"description": "Comprehensive amplitude-aware evaluation metrics",
                                "date": "2026-06-10"},
                   "per_layer": results}, f, indent=2)
    print(f"\nJSON: {OUT_DIR / 'evaluation_metrics.json'}")

    rows = []
    for layer in LAYERS:
        r = dict(results[layer])
        r["layer"] = layer
        rows.append(r)
    pd.DataFrame(rows).to_csv(OUT_DIR / "evaluation_metrics.csv", index=False, float_format="%.6f")
    print(f"CSV:  {OUT_DIR / 'evaluation_metrics.csv'}")

    # ── Bar chart: range_ratio, NRMSE%, trend_error% ──
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.5))
    x = np.arange(len(LAYERS))

    # Panel 1: Range ratio
    ax = axes[0]
    rr_vals = [results[l]["range_ratio"] for l in LAYERS]
    colors = ["#2ca02c" if 0.8 <= v <= 1.2 else ("#ff7f0e" if 0.5 <= v < 0.8 else "#d62728") for v in rr_vals]
    bars = ax.bar(x, rr_vals, 0.5, color=colors, alpha=0.85, edgecolor="white")
    ax.axhline(1.0, color="black", lw=1.5, ls="--", alpha=0.6, label="Perfect (1.0)")
    for bar, v in zip(bars, rr_vals):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.02, f"{v:.2f}", ha="center", fontsize=9, fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(LAYERS, fontsize=11)
    ax.set_ylabel("Range Ratio", fontsize=11)
    ax.set_title("Amplitude Fidelity\n(pred_range / obs_range)", fontsize=12, fontweight="bold")
    ax.legend(fontsize=8); ax.grid(True, alpha=0.3, axis="y")
    ax.set_ylim(0, max(rr_vals)*1.3 if rr_vals else 1.5)

    # Panel 2: NRMSE %
    ax = axes[1]
    nr_vals = [results[l]["nrmse_pct"] for l in LAYERS]
    colors2 = ["#2ca02c" if v < 10 else ("#ff7f0e" if v < 25 else "#d62728") for v in nr_vals]
    bars = ax.bar(x, nr_vals, 0.5, color=colors2, alpha=0.85, edgecolor="white")
    for bar, v in zip(bars, nr_vals):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.2, f"{v:.1f}%", ha="center", fontsize=9, fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(LAYERS, fontsize=11)
    ax.set_ylabel("NRMSE [% of obs range]", fontsize=11)
    ax.set_title("Scale-Normalized Error\n(RMSE / |obs_range|)", fontsize=12, fontweight="bold")
    ax.grid(True, alpha=0.3, axis="y")

    # Panel 3: Trend error %
    ax = axes[2]
    te_vals = [results[l]["trend_error_pct"] for l in LAYERS]
    colors3 = ["#2ca02c" if v < 10 else ("#ff7f0e" if v < 25 else "#d62728") for v in te_vals]
    bars = ax.bar(x, te_vals, 0.5, color=colors3, alpha=0.85, edgecolor="white")
    for bar, v in zip(bars, te_vals):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.2, f"{v:.1f}%", ha="center", fontsize=9, fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(LAYERS, fontsize=11)
    ax.set_ylabel("Trend Error [%]", fontsize=11)
    ax.set_title("Secular Rate Bias\n(|trend_obs−trend_pred| / |trend_obs|)", fontsize=12, fontweight="bold")
    ax.grid(True, alpha=0.3, axis="y")

    fig.suptitle("TUKU — Carrier Model Evaluation Metrics (Amplitude-Aware)\n"
                 "Green = good  |  Orange = moderate  |  Red = poor",
                 fontsize=14, fontweight="bold", y=1.03)
    fig.tight_layout()
    png_path = VIZ_DIR / "evaluation_metrics_barchart.png"
    fig.savefig(png_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"PNG:  {png_path}")


if __name__ == "__main__":
    main()
