"""34_layer_transparency_report.py — Per-layer visual transparency for TUKU.

Physical story:
  Six sediment layers under the TUKU well each compact at their own pace as groundwater is
  pumped out and the clay slowly squeezes. This script draws ONE dedicated figure per layer so a
  human can see, at a glance, how the frozen model's predicted cumulative compaction tracks the
  genuine field visits (integer-millimetre magnetic-ring readings), how wide the 90% uncertainty
  band is, and what groundwater head actually drove that layer. It re-reads only artifacts already
  on disk — the locked calibration, the annual walk-forward predictions, the genuine MLCW visits,
  and the provenance mask — and rebuilds the lagged head driver u(t-tau) with the SAME module the
  walk-forward used. No re-fitting, no re-scoring.

Leakage manifest:
  DIAGNOSTIC-ONLY. This script performs no model fit and no predictive scoring. It reads frozen
  outputs (frozen_calibration.json, annual/*.csv, annual/metrics.json) and genuine field truth.
  The only computation is (a) a band from already-recorded half-widths and (b) a descriptive
  detrended correlation between observed compaction and the lagged head — neither feeds any model.
  No train/test split is performed here because no training happens.

Output Trinity (12 core artifacts + 1 summary JSON):
  results/seq/transparency/TUKU_{L}_transparency_data.csv      (6)
  plots/seq/transparency/TUKU_{L}_transparency_report.png      (6)
  results/seq/transparency/transparency_report_summary.json    (+1)
  results/seq/transparency/34_layer_transparency_report_run_log.txt

Usage (PowerShell):
  $env:PYTHONPATH=""; $env:CONDA_NO_PLUGINS="true"; \
    conda run -n fafalab2 python tau_demo_TUKU/seq/34_layer_transparency_report.py
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

# ── Paths ─────────────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve()
_TAU_DEMO = _HERE.parent.parent          # tau_demo_TUKU/
_ROOT = _TAU_DEMO.parent                 # repo root

for _p in [str(_TAU_DEMO), str(_ROOT), str(_ROOT / "scripts")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from tau_demo_TUKU.seq.drivers import build_layer_drivers   # noqa: E402

# Input files
FROZEN_JSON   = _TAU_DEMO / "results" / "seq" / "frozen_calibration.json"
ANNUAL_DIR    = _TAU_DEMO / "results" / "seq" / "annual"
ANNUAL_METRIC = ANNUAL_DIR / "metrics.json"
TRUTH_CSV     = _ROOT / "data" / "mlcw" / "group_byLayer_orig" / "TUKU_orig_grouped.csv"
PROV_MASK     = _TAU_DEMO / "results" / "seq" / "red_team_fixes" / "truth_provenance_mask.csv"
STATION_MAP   = _ROOT / "m5_deployment" / "station_file_map.json"
GEOMECH_JSON  = _TAU_DEMO / "results" / "seq" / "forensics" / "geomech_consistency.json"
DRIVER_PURITY = _TAU_DEMO / "results" / "seq" / "forensics" / "driver_purity.json"

# Driver-builder inputs (same constants as scripts 23/28)
GWL_ROOT  = _ROOT / "data" / "gwl" / "well_timeseries"
GPS_CSV   = _ROOT / "data" / "gps" / "modeled" / "TKJS_model.csv"
MLCW_INC  = _TAU_DEMO / "data" / "incremental_data" / "mlcw_diff_cleaned.feather"
REF_DATE  = "2015-01-16"

# Outputs
OUT_DATA  = _TAU_DEMO / "results" / "seq" / "transparency"
OUT_PLOTS = _TAU_DEMO / "plots" / "seq" / "transparency"
OUT_DATA.mkdir(parents=True, exist_ok=True)
OUT_PLOTS.mkdir(parents=True, exist_ok=True)

LAYERS = ["F1", "T1", "F2", "T2", "F3", "F4"]
BLIND_START = pd.Timestamp("2019-01-01")

# tab10 palette
C_PRED  = "#1f77b4"   # blue   — predicted compaction
C_OBS   = "#d62728"   # red    — genuine field visits
C_BAND  = "#1f77b4"   # blue   — 90% band (alpha)
C_HEAD  = "#2ca02c"   # green  — head driver
C_REVEAL = "#7f7f7f"  # grey   — reveal markers

plt.rcParams.update({
    "font.size": 14,
    "axes.titlesize": 15,
    "axes.labelsize": 14,
    "figure.dpi": 100,
    "savefig.dpi": 300,
})

# Per-layer geomechanical captions (Phase 3)
CAPTIONS = {
    "F1": "F1 (aquifer-rich, elastic-dominated, S_kv=0): driven by the SHARED well 09050111 "
          "(HONGLUN feather, also drives T1). The GPS carrier absorbs the secular trend; the "
          "head term adds only a small elastic wiggle.",
    "T1": "T1 (thin clay aquitard, elastic-dominated, S_kv=0): SHARES well 09050111 with F1. "
          "Inelastic storage did not excite at this station's head regime; the layer reads as "
          "near-elastic.",
    "F2": "F2 (primary extraction aquifer, tau=3 epochs ~15 days): the one layer where the shallow "
          "head plus carrier recover the seasonal breathing — head term supplies ~46% of observed "
          "seasonal amplitude; annual RMSE ~3.8 mm. The stable, defensible case.",
    "T2": "T2 (clay aquitard, the other inelastic layer, S_kv=3.17, tau=0): inelastic but only ~7% "
          "of epochs cross the preconsolidation head, so the virgin term fires rarely.",
    "F3": "F3 (deep Holocene clay, 77 m of 110 m is fine-grained): DEPTH MISMATCH — the driver well "
          "09050331 is screened at 176-179 m but the clay that compacts sits at 238-275 m (79 m gap, "
          "0 m overlap). The head is phase-wrong; detrended-seasonal |r|~0.10; true lag ~815 d sits "
          "at the tau=120 cap. Panel B shows a head that does not match Panel A's deep-clay motion.",
    "F4": "F4 (geologically an aquitard: 100% silt/mud despite the 'aquifer' ring label; "
          "n_inelastic=0, elastic-only): the least-constrained layer — its band is the model's "
          "honest statement of how little the surface+head can pin this deep silt.",
}


def load_json(path: Path) -> dict:
    return json.loads(io.open(path, encoding="utf-8").read())


def detrend_vs_days(dates: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Zero-reference then remove a straight line fitted against ELAPSED DAYS (anti-pattern A3/A4).

    dates : datetime64 array.  y : float array (same length).  Returns the residual.
    Requires >= 4 finite points (insufficient-data rule), else returns all-NaN.
    """
    d = pd.to_datetime(dates)
    t = (d - d[0]).days.to_numpy(dtype=float)
    finite = np.isfinite(y) & np.isfinite(t)
    if finite.sum() < 4:
        return np.full(len(y), np.nan)
    y0 = y - y[np.argmax(finite)]          # zero-reference to first finite value
    coef = np.polyfit(t[finite], y0[finite], 1)
    return y0 - np.polyval(coef, t)


def detrended_corr_obs_vs_head(layer: str, tau: int, wellcode: str, gwl_fname: str,
                               obs_dates: np.ndarray, obs_vals: np.ndarray) -> tuple:
    """Descriptive detrended correlation between genuine compaction and the lagged head u(t-tau).

    Matches genuine field visits to the 5-day driver grid with merge_asof <=3 days (the SAME
    convention annual/metrics.json uses to grade), detrends both series against elapsed days, and
    returns (|r|, n_pairs).  Diagnostic only — feeds no model.
    """
    df = build_layer_drivers(
        layer=layer, tau=tau, gwl_feather=GWL_ROOT / gwl_fname,
        wellcode=str(wellcode), gps_csv=GPS_CSV, mlcw_inc_feather=MLCW_INC, ref_date=REF_DATE,
    )
    grid = df[["date", "u_lag"]].copy()
    grid["date"] = pd.to_datetime(grid["date"]).astype("datetime64[ns]")
    obs = pd.DataFrame({
        "date": pd.to_datetime(obs_dates).astype("datetime64[ns]"), "obs": obs_vals,
    }).sort_values("date")
    grid = grid.sort_values("date")
    matched = pd.merge_asof(obs, grid, on="date", direction="nearest",
                            tolerance=pd.Timedelta("3D")).dropna(subset=["u_lag", "obs"])
    if len(matched) < 4:
        return float("nan"), int(len(matched))
    r_obs = detrend_vs_days(matched["date"].values, matched["obs"].values.astype(float))
    r_head = detrend_vs_days(matched["date"].values, matched["u_lag"].values.astype(float))
    ok = np.isfinite(r_obs) & np.isfinite(r_head)
    if ok.sum() < 4 or np.std(r_obs[ok]) == 0 or np.std(r_head[ok]) == 0:
        return float("nan"), int(ok.sum())
    r = float(np.corrcoef(r_obs[ok], r_head[ok])[0, 1])
    return abs(r), int(ok.sum())


def main() -> int:
    log_lines: list[str] = []

    def log(m: str = "") -> None:
        print(m)
        log_lines.append(m)

    # ── Load shared inputs ────────────────────────────────────────────────────
    frozen = load_json(FROZEN_JSON)
    metrics = load_json(ANNUAL_METRIC)
    station = load_json(STATION_MAP)
    tuku = station["stations"]["TUKU"]
    gwl_wells = tuku["gwl_wells"]

    geomech = load_json(GEOMECH_JSON)        # F3-only depth geometry
    purity = load_json(DRIVER_PURITY)        # F3-only detrended seasonal r

    truth = pd.read_csv(TRUTH_CSV)
    truth["datetime"] = pd.to_datetime(truth["datetime"])

    prov = pd.read_csv(PROV_MASK)
    prov["date"] = pd.to_datetime(prov["date"])

    visit_dates = [pd.Timestamp(d) for d in metrics["visit_dates"]]

    log("=" * 78)
    log("TUKU LAYER TRANSPARENCY REPORT — 6 layers, two panels each")
    log("=" * 78)
    log("DIAGNOSTIC-ONLY: no model fit, no predictive scoring. Reads frozen outputs + genuine")
    log("field visits only. Predictions = annual walk-forward (recorded BEFORE assimilation).")
    log(f"Reveal/visit dates (annual cadence, n={len(visit_dates)}): "
        f"{[d.date().isoformat() for d in visit_dates]}")
    log("")

    summary: dict = {
        "station": "TUKU",
        "generated_by": "tau_demo_TUKU/seq/34_layer_transparency_report.py",
        "prediction_source": "tau_demo_TUKU/results/seq/annual/ (annual cadence)",
        "datum_note": "pred_mm and genuine MLCW share one cumulative-compaction datum (mm, "
                      "negative=compaction); overlaid directly, no re-referencing.",
        "detrended_corr_method": "obs vs lagged head u(t-tau), matched merge_asof<=3d, "
                                 "detrended vs elapsed days; diagnostic only.",
        "layers": {},
    }
    artifacts: list[str] = []

    # ── Per-layer loop ────────────────────────────────────────────────────────
    for L in LAYERS:
        fc = frozen["layers"][L]
        lm = metrics["layers"][L]
        well = gwl_wells[L]
        wellcode = str(well["wellcode"])
        gwl_fname = Path(well["gwl_feather"]).name
        xcorr_max = float(well.get("xcorr_max", float("nan")))
        tau = int(fc["tau"])

        # Predictions + band
        pred = pd.read_csv(ANNUAL_DIR / f"TUKU_{L}_seq_timeseries.csv")
        pred["date"] = pd.to_datetime(pred["date"]).astype("datetime64[ns]")
        pred = pred.sort_values("date").reset_index(drop=True)
        x0, x1 = pred["date"].min(), pred["date"].max()
        hw = pred["half_width_mm"].to_numpy(float)
        band_lo = pred["pred_mm"].to_numpy(float) - hw
        band_hi = pred["pred_mm"].to_numpy(float) + hw

        # Genuine VERIFIED_RAW observed visits for this layer, within the prediction window
        pm = prov[(prov["layer"] == L) & (prov["class"] == "VERIFIED_RAW")].copy()
        pm = pm[(pm["date"] >= x0) & (pm["date"] <= x1)].sort_values("date")
        obs_dates = pm["date"].to_numpy()
        obs_vals = pm["value_mm"].to_numpy(float)
        n_verified = int(len(pm))

        # Head driver u(t-tau) over the full grid, clipped to window for plotting
        drv = build_layer_drivers(
            layer=L, tau=tau, gwl_feather=GWL_ROOT / gwl_fname, wellcode=wellcode,
            gps_csv=GPS_CSV, mlcw_inc_feather=MLCW_INC, ref_date=REF_DATE,
        )
        drv["date"] = pd.to_datetime(drv["date"]).astype("datetime64[ns]")
        drv_win = drv[(drv["date"] >= x0) & (drv["date"] <= x1)][["date", "u_lag"]].copy()

        # Detrended correlation (consistent in-script computation for all six layers).
        # Use full genuine record (not just window) for a stable seasonal estimate.
        gcol = truth[["datetime", L]].dropna()
        det_r, det_n = detrended_corr_obs_vs_head(
            L, tau, wellcode, gwl_fname, gcol["datetime"].to_numpy(), gcol[L].to_numpy(float)
        )

        # F3 depth geometry / forensic seasonal r
        if L == "F3":
            screen_iv = f"{geomech['screen_top_m']:.0f}-{geomech['screen_bot_m']:.0f}"
            clay_iv = f"{geomech['f3_clay_zone_top_m']:.0f}-{geomech['f3_clay_zone_bot_m']:.0f}"
            depth_gap = float(geomech["screen_to_clay_centroid_gap_m"])
            forensic_seasonal_r = float(purity["calibration_reconciliation"]
                                        ["detrended_seasonal_abs_r"])
        else:
            screen_iv = "not audited"
            clay_iv = "not audited"
            depth_gap = None
            forensic_seasonal_r = None

        # ── Write per-layer CSV ───────────────────────────────────────────────
        out = pred[["date", "pred_mm", "half_width_mm"]].copy()
        out["band_lo_mm"] = band_lo
        out["band_hi_mm"] = band_hi
        out = out.merge(drv_win, on="date", how="left").rename(columns={"u_lag": "u_lag_m"})
        # observed (sparse) joined on exact date where present
        obs_df = pd.DataFrame({"date": pd.to_datetime(obs_dates).astype("datetime64[ns]"),
                               "obs_verified_mm": obs_vals})
        out = out.merge(obs_df, on="date", how="left")
        out["is_reveal"] = out["date"].isin(visit_dates)
        csv_path = OUT_DATA / f"TUKU_{L}_transparency_data.csv"
        out.to_csv(csv_path, index=False)
        artifacts.append(str(csv_path.resolve()))

        # ── Figure: two stacked panels, shared x ──────────────────────────────
        fig, (axA, axB) = plt.subplots(
            2, 1, figsize=(13, 10), sharex=True,
            gridspec_kw={"height_ratios": [2.0, 1.0]},
        )

        # Panel A — cumulative compaction (mm)
        axA.fill_between(pred["date"], band_lo, band_hi, color=C_BAND, alpha=0.18,
                         label="90% conformal band")
        axA.plot(pred["date"], pred["pred_mm"], color=C_PRED, lw=2.0, label="Predicted (annual)")
        if n_verified > 0:
            axA.scatter(obs_dates, obs_vals, color=C_OBS, s=42, zorder=5, edgecolor="k",
                        linewidth=0.4, label=f"Observed VERIFIED_RAW (n={n_verified})")
        for vd in visit_dates:
            axA.axvline(vd, color=C_REVEAL, ls="--", lw=1.0, alpha=0.7)
        axA.set_ylabel("Cumulative compaction (mm)\nnegative = compaction")
        axA.grid(True, alpha=0.3)
        axA.set_title(
            f"TUKU {L} — transparency report   "
            f"(well {wellcode}, tau={tau} ep [{tau*5} d])"
        )
        # reveal marker proxy for legend
        handlesA, labelsA = axA.get_legend_handles_labels()
        handlesA.append(Line2D([0], [0], color=C_REVEAL, ls="--", lw=1.0))
        labelsA.append("Reveal (assimilation) date")
        axA.legend(handlesA, labelsA, loc="best", fontsize=11, framealpha=0.9)

        # Technical box
        skv = fc["S_kv"]
        ske = fc["S_ke"]
        det_r_str = f"{det_r:.3f}" if np.isfinite(det_r) else "insufficient data"
        box = (
            f"wellcode: {wellcode}   xcorr_max(v4): {xcorr_max:.3f}\n"
            f"a={fc['a']:.4f}   S_ke={ske:.4f}   S_kv={skv:.4f}   tau={tau} ep\n"
            f"r2_train={fc['r2_train']:.3f}   RMSE_train={fc['rmse_train_mm']:.2f} mm\n"
            f"annual RMSE={lm['RMSE_mm']:.2f} mm   coverage={lm['band_coverage_fraction']:.2f}   "
            f"skill={lm['skill_vs_baseline']:+.2f}\n"
            f"detrended |r| (obs vs u_lag, n={det_n}): {det_r_str}"
        )
        if L == "F3":
            box += (f"\nscreen {screen_iv} m vs clay {clay_iv} m  ->  GAP {depth_gap:.0f} m, "
                    f"overlap 0 m\nforensic detrended-seasonal |r| = {forensic_seasonal_r:.2f}")
        else:
            box += f"\nscreen vs layer: {screen_iv}"
        axA.text(0.015, 0.04, box, transform=axA.transAxes, fontsize=10.5, va="bottom",
                 ha="left", family="monospace",
                 bbox=dict(boxstyle="round", facecolor="#fff7e6", edgecolor="#999", alpha=0.95))

        # Panel B — head driver u(t-tau)
        axB.plot(drv_win["date"], drv_win["u_lag"], color=C_HEAD, lw=1.6,
                 label=f"u(t-tau) head driver  [well {wellcode}, lag {tau*5} d]")
        axB.axhline(0.0, color="k", lw=0.8, alpha=0.5)
        for vd in visit_dates:
            axB.axvline(vd, color=C_REVEAL, ls="--", lw=1.0, alpha=0.7)
        axB.set_ylabel("Lagged head u(t-tau)\n(m, zero-ref)")
        axB.set_xlabel("Date")
        axB.grid(True, alpha=0.3)
        axB.legend(loc="best", fontsize=11, framealpha=0.9)
        axB.set_xlim(x0 - pd.Timedelta("30D"), x1 + pd.Timedelta("30D"))

        fig.tight_layout()
        png_path = OUT_PLOTS / f"TUKU_{L}_transparency_report.png"
        fig.savefig(png_path, dpi=300)
        plt.close(fig)
        artifacts.append(str(png_path.resolve()))

        # ── Summary entry ─────────────────────────────────────────────────────
        summary["layers"][L] = {
            "wellcode": wellcode,
            "gwl_feather": gwl_fname,
            "tau_epochs": tau,
            "tau_days": tau * 5,
            "a": fc["a"],
            "S_ke": ske,
            "S_kv": skv,
            "r2_train": fc["r2_train"],
            "rmse_train_mm": fc["rmse_train_mm"],
            "annual_RMSE_mm": lm["RMSE_mm"],
            "band_coverage_fraction": lm["band_coverage_fraction"],
            "skill_vs_baseline": lm["skill_vs_baseline"],
            "xcorr_max_v4": xcorr_max,
            "detrended_abs_r_obs_vs_head": None if not np.isfinite(det_r) else round(det_r, 4),
            "detrended_n_pairs": det_n,
            "forensic_detrended_seasonal_abs_r": forensic_seasonal_r,
            "screen_interval_m": screen_iv,
            "clay_zone_m": clay_iv,
            "depth_gap_m": depth_gap,
            "n_verified_visits_in_window": n_verified,
            "caption": CAPTIONS[L],
        }

        log(f"[{L}] well {wellcode} tau={tau}ep  annual RMSE={lm['RMSE_mm']:.2f}mm  "
            f"cov={lm['band_coverage_fraction']:.2f}  skill={lm['skill_vs_baseline']:+.2f}  "
            f"detrended|r|={det_r:.3f} (n={det_n})  verified_dots={n_verified}")

    # ── Write summary JSON ────────────────────────────────────────────────────
    summary_path = OUT_DATA / "transparency_report_summary.json"
    io.open(summary_path, "w", encoding="utf-8").write(json.dumps(summary, indent=2))

    # ── Physical Meaning + manifest ───────────────────────────────────────────
    log("")
    log("PHYSICAL MEANING")
    log("  Each figure shows one sediment layer's predicted cumulative squeeze (Panel A, blue) "
        "with its 90% uncertainty band, the genuine integer-mm field visits (red dots, "
        "VERIFIED_RAW only — fabricated 2024+ rows are excluded by the provenance mask), and the "
        "groundwater head that drove it (Panel B, green).")
    log("  F2 is the defensible case: shallow head + carrier recover the seasonal breathing. F3 is "
        "the failure made visible: its head (Panel B) is screened 79 m above the compacting clay, "
        "so it is phase-wrong for the deep layer in Panel A. F1/T1 share one well and read as "
        "elastic; T2 is weakly inelastic; F4 is an elastic-only silt with the widest band.")
    log("  Implication: the report lets a reviewer accept F2's reconstruction and see, layer by "
        "layer, exactly where and why the deep-clay (F3/F4) dynamics cannot be trusted without a "
        "deep co-screened piezometer.")
    log("")
    log("LEAKAGE MANIFEST: no fit, no scoring, no train/test split performed in this script. "
        "All predictions and metrics were read verbatim from frozen artifacts; band = recorded "
        "half-widths; observed = genuine VERIFIED_RAW field visits.")
    log("")
    log(f"Artifacts written ({len(artifacts)} core + 1 summary JSON):")
    for a in artifacts:
        log(f"  {a}")
    log(f"  {summary_path.resolve()}")

    run_log = OUT_DATA / "34_layer_transparency_report_run_log.txt"
    io.open(run_log, "w", encoding="utf-8").write("\n".join(log_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
