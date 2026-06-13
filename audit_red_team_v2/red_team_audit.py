"""
RED TEAM ZERO-TRUST AUDIT — TUKU Single-Well Sequential Estimator (M8/M9)
==========================================================================
Independent re-computation of every blind-era metric from RAW disk artifacts.
No project code imported. No prior evaluation logic reused.

Ground truth : data/mlcw/group_byLayer_orig/TUKU_orig_grouped.csv (264 genuine visits)
Predictions  : tau_demo_TUKU/results/seq/<schedule>/TUKU_<layer>_seq_timeseries.csv
Claims       : tau_demo_TUKU/results/seq/<schedule>/metrics.json,
               tau_demo_TUKU/results/seq/confirmatory_2024.json

Definitions used by THIS auditor (stated once, used everywhere):
- Matching: pd.merge_asof(direction='nearest', tolerance=3 days), genuine visit
  dates (left) against the 5-day prediction grid (right). Unmatched visits counted.
- Residual (innovation) = obs_mm - pred_mm at the matched grid date, where pred
  is the value recorded in the CSV BEFORE assimilation at that date.
- MAE = mean(|residual|); RMSE = sqrt(mean(residual^2)).
- R^2 = 1 - SS_res / SS_tot, SS_tot about the mean of matched observations.
- Detrended correlation: zero-reference both matched series (y - y[0]); fit a
  straight line against REAL elapsed days (dates - dates[0]).days as float);
  Pearson r between the two residual series. Undefined if n < 10.
- Amplitude ratio: std(detrended pred) / std(detrended obs) on matched dates.
  Also peak-to-peak ratio of the same detrended series.
- Band coverage: fraction of matched visits with defined half_width where
  |residual| <= half_width_mm.
- Leakage probe: at each reveal date the CSV value must NOT already equal the
  observation (pre-assimilation), and the first epoch AFTER the reveal must sit
  within carrier-noise distance of the revealed observation (hard level reset).
- Flatline probe: between consecutive reveals, fit pred vs real days; report
  the std of the linear-fit residuals (mm). ~0 mm means straight line between
  bias resets.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2")
SEQ = ROOT / "tau_demo_TUKU" / "results" / "seq"
TRUTH_CSV = ROOT / "data" / "mlcw" / "group_byLayer_orig" / "TUKU_orig_grouped.csv"
OUT = ROOT / "audit_red_team_v2"
OUT.mkdir(exist_ok=True)

LAYERS = ["F1", "T1", "F2", "T2", "F3", "F4"]
SCHEDULES = ["annual", "semiannual", "monthly", "none"]
BLIND_START = pd.Timestamp("2019-01-01")
BLIND_END = pd.Timestamp("2023-12-31")
Y2024_START = pd.Timestamp("2024-01-01")
Y2024_END = pd.Timestamp("2024-12-31")
TOL = pd.Timedelta(days=3)
L1 = {"F1": (5, 10), "T1": (5, 10), "F2": (10, 20), "T2": (5, 10),
      "F3": (10, 20), "F4": (5, 10)}

plt.rcParams.update({
    "font.size": 14, "axes.titlesize": 15, "axes.labelsize": 14,
    "legend.fontsize": 12, "xtick.labelsize": 12, "ytick.labelsize": 12,
    "axes.grid": True, "grid.alpha": 0.35, "figure.dpi": 200,
})
TAB = plt.get_cmap("tab10").colors

report_lines = []


def log(msg=""):
    print(msg)
    report_lines.append(str(msg))


# ----------------------------------------------------------------------------
# 1. Load ground truth — the 264 genuine field visits
# ----------------------------------------------------------------------------
if not TRUTH_CSV.exists():
    sys.exit(f"File not found — cannot proceed: {TRUTH_CSV}")

truth = pd.read_csv(TRUTH_CSV, parse_dates=["datetime"]).sort_values("datetime")
truth = truth.reset_index(drop=True)
log(f"[truth] rows = {len(truth)} (claimed: 264 genuine visits)")
log(f"[truth] date range: {truth['datetime'].min().date()} .. "
    f"{truth['datetime'].max().date()}")

blind_truth = truth[(truth["datetime"] >= BLIND_START)
                    & (truth["datetime"] <= BLIND_END)].copy()
t2024 = truth[(truth["datetime"] >= Y2024_START)
              & (truth["datetime"] <= Y2024_END)].copy()
log(f"[truth] genuine visits in blind era 2019-2023: {len(blind_truth)}")
log(f"[truth] genuine visits in 2024: {len(t2024)} (claimed: 12)")

# Provenance probe: integer-valued rows (manual readouts) vs full-float rows
def frac_noninteger(df, cols):
    vals = df[cols].to_numpy(dtype=float).ravel()
    vals = vals[np.isfinite(vals)]
    return float(np.mean(np.abs(vals - np.round(vals)) > 1e-9))

pre19 = truth[truth["datetime"] < BLIND_START]
log(f"[truth-provenance] non-integer value fraction pre-2019: "
    f"{frac_noninteger(pre19, LAYERS):.3f}; blind era 2019-2023: "
    f"{frac_noninteger(blind_truth, LAYERS):.3f}; 2024: "
    f"{frac_noninteger(t2024, LAYERS):.3f}")

# ----------------------------------------------------------------------------
# 2. Load claims
# ----------------------------------------------------------------------------
claims = {}
for sch in SCHEDULES:
    p = SEQ / sch / "metrics.json"
    with open(p, "r", encoding="utf-8") as f:
        claims[sch] = json.load(f)

with open(SEQ / "run_manifest.json", "r", encoding="utf-8") as f:
    manifest = json.load(f)
with open(SEQ / "confirmatory_2024.json", "r", encoding="utf-8") as f:
    conf2024 = json.load(f)

# ----------------------------------------------------------------------------
# 3. Independent metric computation
# ----------------------------------------------------------------------------
def detrend_real_days(dates, y):
    """Zero-reference then remove a straight line fitted against real days."""
    y0 = np.asarray(y, dtype=float)
    y0 = y0 - y0[0]
    days = (dates - dates.iloc[0]).dt.days.to_numpy(dtype=float)
    if len(y0) < 4:
        return None, days
    coef = np.polyfit(days, y0, 1)
    return y0 - np.polyval(coef, days), days


def load_pred(schedule, layer):
    p = SEQ / schedule / f"TUKU_{layer}_seq_timeseries.csv"
    if not p.exists():
        return None
    df = pd.read_csv(p, parse_dates=["date"]).sort_values("date")
    return df.reset_index(drop=True)


def match(layer, pred_df, truth_df):
    """merge_asof genuine visits onto the prediction grid, tolerance 3 days."""
    tt = truth_df[["datetime", layer]].dropna().sort_values("datetime")
    m = pd.merge_asof(
        tt.rename(columns={"datetime": "visit_date"}),
        pred_df.rename(columns={"date": "grid_date"}),
        left_on="visit_date", right_on="grid_date",
        direction="nearest", tolerance=TOL,
    )
    n_unmatched = int(m["grid_date"].isna().sum())
    m = m.dropna(subset=["grid_date", "pred_mm"]).reset_index(drop=True)
    return m, n_unmatched


results = {}
for sch in SCHEDULES:
    results[sch] = {}
    visit_dates = pd.to_datetime(manifest["schedules"][sch]["visit_dates"])
    for layer in LAYERS:
        pred_df = load_pred(sch, layer)
        if pred_df is None:
            log(f"File not found — cannot proceed: {sch}/{layer}")
            continue
        m, n_unmatched = match(layer, pred_df, blind_truth)
        n = len(m)
        res = m[layer].to_numpy(float) - m["pred_mm"].to_numpy(float)
        mae = float(np.mean(np.abs(res)))
        rmse = float(np.sqrt(np.mean(res ** 2)))
        obs = m[layer].to_numpy(float)
        ss_tot = float(np.sum((obs - obs.mean()) ** 2))
        r2 = float(1.0 - np.sum(res ** 2) / ss_tot) if ss_tot > 0 else np.nan

        # detrended correlation + amplitude ratio (own definition)
        if n >= 10:
            d_obs, _ = detrend_real_days(m["visit_date"], obs)
            d_prd, _ = detrend_real_days(m["visit_date"], m["pred_mm"])
            r_det = float(np.corrcoef(d_obs, d_prd)[0, 1])
            amp_std = float(np.std(d_prd) / np.std(d_obs))
            amp_p2p = float((d_prd.max() - d_prd.min())
                            / (d_obs.max() - d_obs.min()))
        else:
            r_det, amp_std, amp_p2p = None, None, None  # insufficient data

        # band coverage among matched visits with defined half width
        hw = m["half_width_mm"].to_numpy(float)
        defined = np.isfinite(hw)
        n_def = int(defined.sum())
        cov = float(np.mean(np.abs(res[defined]) <= hw[defined])) if n_def else np.nan

        # RMSE excluding the very first scoring point (datum-restart artifact)
        rmse_x1 = float(np.sqrt(np.mean(res[1:] ** 2))) if n > 1 else np.nan
        mae_x1 = float(np.mean(np.abs(res[1:]))) if n > 1 else np.nan

        # leakage probe at reveal dates
        leak_flags = []
        reset_errs = []
        grid = pred_df.set_index("date")["pred_mm"]
        for vd in visit_dates:
            if vd not in grid.index:
                continue
            row = m[m["grid_date"] == vd]
            if row.empty:
                continue
            obs_v = float(row[layer].iloc[0])
            pre = float(grid.loc[vd])
            later = grid[grid.index > vd]
            if len(later) == 0:
                continue
            post = float(later.iloc[0])
            # leakage if prediction already equals truth BEFORE assimilation
            if abs(obs_v - pre) < 1e-6 and abs(res[0]) > 1e-6:
                leak_flags.append(str(vd.date()))
            reset_errs.append(abs(post - obs_v))

        # flatline probe: linear-fit residual std of pred between reveals
        seg_stds = []
        bounds = ([pred_df["date"].min()] + list(visit_dates)
                  + [pred_df["date"].max()])
        for a, b in zip(bounds[:-1], bounds[1:]):
            seg = pred_df[(pred_df["date"] > a) & (pred_df["date"] <= b)]
            if len(seg) < 8:
                continue
            days = (seg["date"] - seg["date"].iloc[0]).dt.days.to_numpy(float)
            y = seg["pred_mm"].to_numpy(float)
            y = y - y[0]
            resid = y - np.polyval(np.polyfit(days, y, 1), days)
            seg_stds.append(float(np.std(resid)))

        results[sch][layer] = dict(
            n_matched=n, n_unmatched=n_unmatched, MAE=mae, RMSE=rmse,
            MAE_excl_first=mae_x1, RMSE_excl_first=rmse_x1, R2=r2,
            detrended_r=r_det, amp_ratio_std=amp_std, amp_ratio_p2p=amp_p2p,
            n_band_defined=n_def, band_coverage=cov,
            mean_reset_err_mm=(float(np.mean(reset_errs)) if reset_errs else None),
            leak_dates=leak_flags,
            flatline_seg_resid_std_mm=(float(np.median(seg_stds))
                                       if seg_stds else None),
            matched=m,
        )

# ----------------------------------------------------------------------------
# 4. Claimed-vs-computed comparison table
# ----------------------------------------------------------------------------
log("\n" + "=" * 100)
log("CLAIMED vs INDEPENDENTLY COMPUTED — blind era 2019-2023 "
    "(scored on ALL genuine visits, pre-assimilation predictions)")
log("=" * 100)
hdr = (f"{'sched':<11}{'layer':<6}{'n':>4}{'unm':>4} | "
       f"{'MAE clm':>8}{'MAE ind':>8} | {'RMSE clm':>9}{'RMSE ind':>9} | "
       f"{'cov clm':>8}{'cov ind':>8}{'nB':>4} | {'R2':>6}{'det r':>7}"
       f"{'ampS':>6}{'flat':>6}")
log(hdr)
log("-" * len(hdr))
flagged = []
for sch in SCHEDULES:
    for layer in LAYERS:
        r = results[sch][layer]
        c = claims[sch]["layers"][layer]
        c_mae, c_rmse = c["MAE_mm"], c["RMSE_mm"]
        c_cov = c.get("band_coverage_fraction", np.nan)
        d_mae = r["MAE"] - c_mae
        d_rmse = r["RMSE"] - c_rmse
        flag = ""
        if abs(d_mae) > 0.05 or abs(d_rmse) > 0.05:
            flag = "  <<< DISCREPANCY"
            flagged.append((sch, layer, c_mae, r["MAE"], c_rmse, r["RMSE"]))
        det = f"{r['detrended_r']:.3f}" if r["detrended_r"] is not None else "undef"
        amp = f"{r['amp_ratio_std']:.2f}" if r["amp_ratio_std"] is not None else "undef"
        flt = (f"{r['flatline_seg_resid_std_mm']:.2f}"
               if r["flatline_seg_resid_std_mm"] is not None else "n/a")
        log(f"{sch:<11}{layer:<6}{r['n_matched']:>4}{r['n_unmatched']:>4} | "
            f"{c_mae:>8.3f}{r['MAE']:>8.3f} | {c_rmse:>9.3f}{r['RMSE']:>9.3f} | "
            f"{c_cov:>8.3f}{r['band_coverage']:>8.3f}{r['n_band_defined']:>4} | "
            f"{r['R2']:>6.3f}{det:>7}{amp:>6}{flt:>6}{flag}")

log("")
log("Column key: n = matched genuine visits; unm = genuine visits with no grid "
    "point within 3 days; cov ind = coverage among nB band-defined matched "
    "visits; det r = detrended Pearson r (obs vs pred, zero-ref, real-day "
    "linear detrend); ampS = detrended std ratio pred/obs; flat = median "
    "within-segment linear-residual std of the prediction (mm) — ~0 means "
    "straight line between reveals.")

if flagged:
    log("\nDISCREPANCIES FLAGGED:")
    for f in flagged:
        log(f"  {f[0]}/{f[1]}: claimed MAE {f[2]:.3f} vs mine {f[3]:.3f}; "
            f"claimed RMSE {f[4]:.3f} vs mine {f[5]:.3f}")
else:
    log("\nNo MAE/RMSE discrepancies above 0.05 mm in any schedule/layer.")

# First-point sensitivity
log("\nFirst-scoring-point sensitivity (datum restart at blind start):")
for sch in ["annual", "semiannual"]:
    for layer in ["F2", "F3"]:
        r = results[sch][layer]
        log(f"  {sch}/{layer}: RMSE all {r['RMSE']:.3f} mm -> excl. first "
            f"point {r['RMSE_excl_first']:.3f} mm "
            f"(first innovation absorbs the 2019-01-11 datum jump)")

# Leakage probe summary
log("\nLeakage probe (pred==obs before assimilation):")
any_leak = False
for sch in ["annual", "semiannual", "monthly"]:
    for layer in LAYERS:
        r = results[sch][layer]
        if r["leak_dates"]:
            any_leak = True
            log(f"  {sch}/{layer}: SUSPECT at {r['leak_dates']}")
log("  none detected" if not any_leak else "  ^^ investigate above")
log("\nMean |reset error| at first epoch after reveal (should be ~carrier "
    "noise 0.147 mm if hard reset):")
for sch in ["annual", "semiannual"]:
    for layer in ["F2", "F3"]:
        r = results[sch][layer]
        v = r["mean_reset_err_mm"]
        log(f"  {sch}/{layer}: {v:.3f} mm" if v is not None
            else f"  {sch}/{layer}: n/a")

# ----------------------------------------------------------------------------
# 5. 2024 confirmatory — can it be independently verified?
# ----------------------------------------------------------------------------
log("\n" + "=" * 100)
log("2024 CONFIRMATORY CHECK")
log("=" * 100)
max_date = max(load_pred(s, "F3")["date"].max() for s in SCHEDULES)
log(f"Latest prediction epoch persisted on disk across all schedules: "
    f"{max_date.date()}")
if max_date < Y2024_START:
    log("No 2024 prediction timeseries exists on disk. The confirmatory_2024 "
        "claims (e.g., annual F3 RMSE 6.020 mm, coverage 0/2) CANNOT be "
        "independently recomputed from persisted outputs — they exist only "
        "inside confirmatory_2024.json. File not found — cannot proceed "
        "with independent 2024 metric verification.")
log(f"Genuine 2024 visits in raw truth: {len(t2024)}; claimed "
    f"n_genuine_2024_visits = {conf2024['n_genuine_2024_visits']}")
claimed_2024 = pd.to_datetime(conf2024["genuine_2024_dates"])
raw_2024 = t2024["datetime"].tolist()
ok = []
for cd in claimed_2024:
    near = min(abs((cd - rd).days) for rd in raw_2024) if raw_2024 else 999
    ok.append(near <= 3)
log(f"Claimed 2024 grading dates matching a raw genuine visit within 3 days: "
    f"{sum(ok)}/{len(ok)}")

# ----------------------------------------------------------------------------
# 6. Visual proof — three plots each for F2 and F3 (annual + semiannual)
# ----------------------------------------------------------------------------
def plot_overlay(layer):
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), sharex=True, sharey=True)
    for ax, sch in zip(axes, ["annual", "semiannual"]):
        pred = load_pred(sch, layer)
        m = results[sch][layer]["matched"]
        visits = pd.to_datetime(manifest["schedules"][sch]["visit_dates"])
        hw = pred["half_width_mm"].to_numpy(float)
        ax.fill_between(pred["date"],
                        pred["pred_mm"] - hw, pred["pred_mm"] + hw,
                        where=np.isfinite(hw), color=TAB[0], alpha=0.25,
                        label="90% conformal band (where defined)")
        ax.plot(pred["date"], pred["pred_mm"], color=TAB[0], lw=1.8,
                label="sequential prediction (pre-assimilation)")
        ax.plot(m["visit_date"], m[layer], "*", color=TAB[3], ms=11,
                label=f"genuine field visits (n={len(m)})", zorder=5)
        for i, vd in enumerate(visits):
            ax.axvline(vd, color=TAB[2], ls="--", lw=1.2, alpha=0.8,
                       label="reveal (assimilation) date" if i == 0 else None)
        ax.set_ylabel("cumulative compaction (mm)")
        ax.set_title(f"TUKU {layer} — {sch} reveal cadence, blind 2019-2023")
        ax.legend(loc="best", framealpha=0.9)
    axes[1].set_xlabel("date")
    fig.tight_layout()
    p = OUT / f"overlay_band_{layer}.png"
    fig.savefig(p)
    plt.close(fig)
    log(f"[plot] {p}")


def plot_residual_drift(layer):
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), sharex=True, sharey=True)
    for ax, sch in zip(axes, ["annual", "semiannual"]):
        m = results[sch][layer]["matched"]
        visits = pd.to_datetime(manifest["schedules"][sch]["visit_dates"])
        res = m[layer].to_numpy(float) - m["pred_mm"].to_numpy(float)
        ax.axhline(0, color="k", lw=1)
        ax.plot(m["visit_date"], res, "o-", color=TAB[1], lw=1.5, ms=6,
                label="signed residual obs - pred (mm)")
        for i, vd in enumerate(visits):
            ax.axvline(vd, color=TAB[2], ls="--", lw=1.2, alpha=0.8,
                       label="reveal date" if i == 0 else None)
        thr = L1[layer][1]
        ax.axhline(thr, color=TAB[3], ls=":", lw=1.5,
                   label=f"L1 RMSE threshold ±{thr} mm")
        ax.axhline(-thr, color=TAB[3], ls=":", lw=1.5)
        ax.set_ylabel("residual (mm)")
        ax.set_title(f"TUKU {layer} — residual drift, {sch} cadence "
                     f"(RMSE={results[sch][layer]['RMSE']:.2f} mm, "
                     f"excl. first point {results[sch][layer]['RMSE_excl_first']:.2f} mm)")
        ax.legend(loc="best", framealpha=0.9)
    axes[1].set_xlabel("date")
    fig.tight_layout()
    p = OUT / f"residual_drift_{layer}.png"
    fig.savefig(p)
    plt.close(fig)
    log(f"[plot] {p}")


def plot_breathing(layer):
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), sharex=True, sharey=True)
    for ax, sch in zip(axes, ["annual", "semiannual"]):
        m = results[sch][layer]["matched"]
        visits = pd.to_datetime(manifest["schedules"][sch]["visit_dates"])
        d_obs, _ = detrend_real_days(m["visit_date"], m[layer].to_numpy(float))
        d_prd, _ = detrend_real_days(m["visit_date"],
                                     m["pred_mm"].to_numpy(float))
        # full continuous prediction, detrended on the same era
        pred = load_pred(sch, layer)
        d_full, _ = detrend_real_days(pred["date"],
                                      pred["pred_mm"].to_numpy(float))
        ax.plot(pred["date"], d_full, color=TAB[0], lw=1.2, alpha=0.6,
                label="prediction detrended (continuous, incl. resets)")
        ax.plot(m["visit_date"], d_prd, "s-", color=TAB[0], ms=5, lw=1.0,
                label="prediction detrended @ visits")
        ax.plot(m["visit_date"], d_obs, "*-", color=TAB[3], ms=10, lw=1.0,
                label="observed detrended @ visits")
        for i, vd in enumerate(visits):
            ax.axvline(vd, color=TAB[2], ls="--", lw=1.0, alpha=0.7,
                       label="reveal date" if i == 0 else None)
        r = results[sch][layer]
        det = f"{r['detrended_r']:.3f}" if r["detrended_r"] is not None else "undef"
        amp = f"{r['amp_ratio_std']:.2f}" if r["amp_ratio_std"] is not None else "undef"
        ax.set_ylabel("detrended compaction (mm)")
        ax.set_title(f"TUKU {layer} — sub-annual dynamics, {sch} cadence "
                     f"(detrended r={det}, amp ratio={amp}, "
                     f"within-segment resid std={r['flatline_seg_resid_std_mm']:.2f} mm)")
        ax.legend(loc="best", framealpha=0.9)
    axes[1].set_xlabel("date")
    fig.tight_layout()
    p = OUT / f"breathing_detrended_{layer}.png"
    fig.savefig(p)
    plt.close(fig)
    log(f"[plot] {p}")


log("\n" + "=" * 100)
log("VISUAL PROOFS")
log("=" * 100)
for layer in ["F2", "F3"]:
    plot_overlay(layer)
    plot_residual_drift(layer)
    plot_breathing(layer)

# ----------------------------------------------------------------------------
# 7. Persist independent metrics
# ----------------------------------------------------------------------------
rows = []
for sch in SCHEDULES:
    for layer in LAYERS:
        r = {k: v for k, v in results[sch][layer].items() if k != "matched"}
        r["schedule"] = sch
        r["layer"] = layer
        c = claims[sch]["layers"][layer]
        r["claimed_MAE"] = c["MAE_mm"]
        r["claimed_RMSE"] = c["RMSE_mm"]
        r["claimed_coverage"] = c.get("band_coverage_fraction")
        rows.append(r)
pd.DataFrame(rows).to_csv(OUT / "independent_metrics.csv", index=False)
log(f"\n[out] {OUT / 'independent_metrics.csv'}")

with open(OUT / "audit_console_log.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines))
log(f"[out] {OUT / 'audit_console_log.txt'}")
log("\nAUDIT SCRIPT COMPLETE")
