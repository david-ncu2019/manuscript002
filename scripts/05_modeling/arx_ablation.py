# Path fix: remove contaminating gemini_env from sys.path before any imports
import sys as _sys
_sys.path = [p for p in _sys.path if "gemini_env" not in p and "VENV_PYTHON" not in p]

"""
ARX Ablation Study — Decomposing the Improvement Sources
=========================================================

Question from discussion_20260517_arx_results.md §8.2:

  How much of the RMSE improvement over the static baseline comes from:
    (A) Initial-state anchoring alone ("anchor-only" model)?
    (B) Full ARX model (phi_k, beta_k, gamma_k)?

The three models being compared per depth k in the 2022–2025 hold-out window:

  Baseline  : Y_hat_base(i)   = f_median_k * x(i)
                               (static direct ratio, no memory, no anchor)

  Anchor    : Y_hat_anchor(i) = Y_obs(t0) + f_median_k * (x(i) - x(t0))
                               (anchor to last observed MLCW, then scale InSAR increment)
                               — no phi_k term, no gamma_k term, beta_k replaced by f_median_k

  ARX       : Y_hat_arx(i)    = phi_k * Y_hat_arx(i-1) + beta_k * x(i) + gamma_k * dx(i)
                               (full ARX recursive, anchored to Y_obs(t0))

Where t0 = last epoch of training window (2021-11-30 for fold 1).

Walk-forward validation: 4 folds (2022, 2023, 2024, 2025).
For each fold: fit ARX OLS on training window; predict hold-out with all 3 models.
Anchor and ARX both use the last observed MLCW value as the initial condition.

Decomposition:
  anchor_improvement = (RMSE_base - RMSE_anchor) / RMSE_base * 100%
  arx_bonus          = (RMSE_anchor - RMSE_arx)  / RMSE_base * 100%
  total_improvement  = (RMSE_base - RMSE_arx)    / RMSE_base * 100%

So: total = anchor_improvement + arx_bonus

Station scope: all 19 active MLCW stations (same set as arx_validate_all_stations.py).

Outputs → arx_method7/ablation/
  {STATION}_ablation.csv        per-depth RMSE (base, anchor, arx) + decomposition
  ablation_allstations.csv      one row per station (median across depths)
  fig_ablation_tuku_depth.png   4-panel: base/anchor/arx RMSE vs depth, for TUKU
  fig_ablation_tuku_ts.png      4 depths × 2022-2025 time series: obs / anchor / arx
  fig_ablation_summary.png      station-level bar: anchor vs arx bonus
  fig_ablation_scatter.png      scatter: anchor_improvement vs total_improvement (all stations)
"""

import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
from scipy import linalg as la

# ── Paths ───────────────────────────────────────────────────────────────────────
BASE      = Path(r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2")
MLCW_DIR  = BASE / "MLCW_5m_regular"
INSAR_F   = BASE / "InSAR_timeries" / "mlcw_interp_insar_IDW_extend.feather"
RATIO_DIR = BASE / "direct_ratio_MLCW_InSAR"
ARX_DIR   = BASE / "arx_method7"
OUT_DIR   = ARX_DIR / "ablation"
OUT_DIR.mkdir(exist_ok=True)

# ── Constants ───────────────────────────────────────────────────────────────────
DEPTHS_M   = list(range(0, 300, 5))   # 60 levels
DEPTH_COLS = [f"depth_{d:03d}m" for d in DEPTHS_M]
N_DEPTHS   = 60

FOLD_ENDS  = ["2021-11-30", "2022-11-30", "2023-11-30", "2024-11-30"]
FOLD_NAMES = ["2022", "2023", "2024", "2025"]
HOLDOUT_START = pd.Timestamp("2022-01-01")

C_BASE   = "#d62728"
C_ANCHOR = "#ff7f0e"
C_ARX    = "#1f77b4"
C_OBS    = "black"

# ── Data loading ─────────────────────────────────────────────────────────────────

def load_insar():
    df = pd.read_feather(INSAR_F)
    epoch_cols = [c for c in df.columns if str(c).startswith("D20")]
    dates = pd.to_datetime([str(c).lstrip("D") for c in epoch_cols], format="%Y%m%d")
    name_col = "Ename" if "Ename" in df.columns else "station"
    result = {}
    for _, row in df.iterrows():
        st = row[name_col]
        vals = row[epoch_cols].values.astype(float) * 1000.0   # m → mm, raw: negative=subsidence
        result[st] = {"dates": dates, "values": vals}
    return result


def load_mlcw(station):
    path = MLCW_DIR / f"{station}_5m_grid.csv"
    df = pd.read_csv(path, parse_dates=["datetime"]).set_index("datetime").sort_index()
    cols = [c for c in DEPTH_COLS if c in df.columns]
    return df.index.to_numpy(), df[cols].values.astype(float)


def load_f_median(station):
    path = RATIO_DIR / station / f"{station}_direct_ratio_stats.csv"
    if not path.exists():
        return np.zeros(N_DEPTHS)
    return pd.read_csv(path)["f_median"].values.astype(float)


def align(insar_dates, insar_vals, mlcw_dates, mlcw_Y):
    s = pd.Series(insar_vals, index=pd.DatetimeIndex(insar_dates))
    m = pd.DataFrame(mlcw_Y, index=pd.DatetimeIndex(mlcw_dates))
    common = s.index.intersection(m.index)
    if len(common) < 50:
        return None, None, None
    x = s.loc[common].values
    Y = m.loc[common].values
    # Baseline-align: both start at 0 at first common epoch
    x = x - x[0]
    Y = Y - Y[0, :]
    return common, x, Y

# ── Model fits ──────────────────────────────────────────────────────────────────

def fit_arx(Y_k_train, x_train, dx_train):
    A = np.column_stack([Y_k_train[:-1], x_train[1:], dx_train[1:]])
    b = Y_k_train[1:]
    params, _, _, _ = la.lstsq(A, b, check_finite=False)
    return params  # phi, beta, gamma


def predict_arx(phi, beta, gamma, x_ho, dx_ho, Y0):
    n = len(x_ho)
    Y_hat = np.empty(n)
    yp = Y0
    for i in range(n):
        Y_hat[i] = phi * yp + beta * x_ho[i] + gamma * dx_ho[i]
        yp = Y_hat[i]
    return Y_hat


def predict_anchor(f_med_k, x_ho, x0, Y0):
    """Y0 + f_med_k * (x(i) - x0) — drift-corrected static ratio"""
    return Y0 + f_med_k * (x_ho - x0)


def predict_base(f_med_k, x_ho):
    """f_med_k * x(i) — static direct ratio"""
    return f_med_k * x_ho


def rmse(obs, pred):
    mask = np.isfinite(obs) & np.isfinite(pred)
    if mask.sum() < 3:
        return np.nan
    return float(np.sqrt(np.mean((obs[mask] - pred[mask])**2)))

# ── Per-station ablation ─────────────────────────────────────────────────────────

def process_station(station, insar_data):
    if station not in insar_data:
        return None

    try:
        mlcw_dates, mlcw_Y = load_mlcw(station)
    except FileNotFoundError:
        return None

    common_dates, x, Y = align(
        insar_data[station]["dates"],
        insar_data[station]["values"],
        mlcw_dates, mlcw_Y,
    )
    if common_dates is None:
        return None

    common_dt = pd.DatetimeIndex(common_dates)
    if (common_dt >= HOLDOUT_START).sum() < 10:
        return None   # shut-down station, no 2022+ data

    f_median = load_f_median(station)
    dx = np.concatenate([[0.0], np.diff(x)])

    # Storage: (60, 4) for each fold
    rmse_base   = np.full((N_DEPTHS, 4), np.nan)
    rmse_anchor = np.full((N_DEPTHS, 4), np.nan)
    rmse_arx    = np.full((N_DEPTHS, 4), np.nan)

    # Also store stitched hold-out arrays for plotting
    fold_ho_data = []   # list of dicts per fold

    for fi, fold_end_str in enumerate(FOLD_ENDS):
        fold_end = pd.Timestamp(fold_end_str)
        train_mask = common_dt <= fold_end
        if fi + 1 < len(FOLD_ENDS):
            ho_mask = (common_dt > fold_end) & (common_dt <= pd.Timestamp(FOLD_ENDS[fi + 1]))
        else:
            ho_mask = common_dt > fold_end

        n_train = train_mask.sum()
        n_ho    = ho_mask.sum()
        if n_train < 50 or n_ho < 3:
            fold_ho_data.append(None)
            continue

        x_train  = x[train_mask]
        dx_train = dx[train_mask]
        x_ho     = x[ho_mask]
        dx_ho    = dx[ho_mask]
        Y_ho     = Y[ho_mask, :]      # observed in hold-out
        ho_dates = common_dt[ho_mask]

        x0  = x_train[-1]   # InSAR value at training-window end
        Y0_vec = Y[train_mask, :][-1, :]   # last observed MLCW per depth

        fold_arx    = np.full((n_ho, N_DEPTHS), np.nan)
        fold_anchor = np.full((n_ho, N_DEPTHS), np.nan)
        fold_base   = np.full((n_ho, N_DEPTHS), np.nan)

        for k in range(N_DEPTHS):
            Y_k_train = Y[train_mask, k]
            Y_k_ho    = Y_ho[:, k]
            if not np.all(np.isfinite(Y_k_train)) or len(Y_k_train) < 4:
                continue

            # ARX params
            try:
                params = fit_arx(Y_k_train, x_train, dx_train)
            except Exception:
                continue
            phi_k, beta_k, gamma_k = params
            Y0_k = float(Y0_vec[k])

            y_arx    = predict_arx(phi_k, beta_k, gamma_k, x_ho, dx_ho, Y0_k)
            y_anchor = predict_anchor(f_median[k], x_ho, x0, Y0_k)
            y_base   = predict_base(f_median[k], x_ho)

            rmse_arx[k, fi]    = rmse(Y_k_ho, y_arx)
            rmse_anchor[k, fi] = rmse(Y_k_ho, y_anchor)
            rmse_base[k, fi]   = rmse(Y_k_ho, y_base)

            fold_arx[:, k]    = y_arx
            fold_anchor[:, k] = y_anchor
            fold_base[:, k]   = y_base

        fold_ho_data.append({
            "dates": ho_dates,
            "Y_obs": Y_ho,
            "Y_arx": fold_arx,
            "Y_anchor": fold_anchor,
            "Y_base": fold_base,
        })

    # ── Per-depth medians across folds ──────────────────────────────────────────
    rmse_base_med   = np.nanmedian(rmse_base,   axis=1)
    rmse_anchor_med = np.nanmedian(rmse_anchor, axis=1)
    rmse_arx_med    = np.nanmedian(rmse_arx,    axis=1)

    anchor_impr = 100.0 * (rmse_base_med - rmse_anchor_med) / (rmse_base_med + 1e-9)
    arx_bonus   = 100.0 * (rmse_anchor_med - rmse_arx_med)  / (rmse_base_med + 1e-9)
    total_impr  = 100.0 * (rmse_base_med - rmse_arx_med)    / (rmse_base_med + 1e-9)

    # ── Per-depth CSV ────────────────────────────────────────────────────────────
    per_depth_df = pd.DataFrame({
        "depth_m":         DEPTHS_M,
        "rmse_base_mm":    rmse_base_med,
        "rmse_anchor_mm":  rmse_anchor_med,
        "rmse_arx_mm":     rmse_arx_med,
        "anchor_impr_pct": anchor_impr,
        "arx_bonus_pct":   arx_bonus,
        "total_impr_pct":  total_impr,
    })
    per_depth_df.to_csv(OUT_DIR / f"{station}_ablation.csv", index=False)

    # ── Station summary ──────────────────────────────────────────────────────────
    valid = np.isfinite(rmse_base_med) & (rmse_base_med > 0.05)
    station_summary = {
        "station":               station,
        "n_valid_depths":        int(valid.sum()),
        "rmse_base_med_mm":      float(np.nanmedian(rmse_base_med[valid])),
        "rmse_anchor_med_mm":    float(np.nanmedian(rmse_anchor_med[valid])),
        "rmse_arx_med_mm":       float(np.nanmedian(rmse_arx_med[valid])),
        "anchor_impr_pct":       float(np.nanmedian(anchor_impr[valid])),
        "arx_bonus_pct":         float(np.nanmedian(arx_bonus[valid])),
        "total_impr_pct":        float(np.nanmedian(total_impr[valid])),
        "anchor_fraction_of_total": float(
            np.nanmedian(anchor_impr[valid]) /
            (np.nanmedian(total_impr[valid]) + 1e-9)
        ) if np.nanmedian(total_impr[valid]) > 0 else None,
    }

    return {
        "station_summary": station_summary,
        "per_depth_df":    per_depth_df,
        "fold_ho_data":    fold_ho_data,
        "rmse_base_med":   rmse_base_med,
        "rmse_anchor_med": rmse_anchor_med,
        "rmse_arx_med":    rmse_arx_med,
    }


# ── Figures ──────────────────────────────────────────────────────────────────────

def plot_tuku_depth(station, per_depth_df):
    """Per-depth RMSE profile: base / anchor / arx."""
    depths = per_depth_df["depth_m"].values
    rb = per_depth_df["rmse_base_mm"].values
    ra = per_depth_df["rmse_anchor_mm"].values
    rx = per_depth_df["rmse_arx_mm"].values

    fig, ax = plt.subplots(figsize=(8, 10))
    ax.plot(rb, depths, color=C_BASE,   lw=2.0, label=f"Baseline (f̄·x)")
    ax.plot(ra, depths, color=C_ANCHOR, lw=2.0, label=f"Anchor-only (Y0 + f̄·Δx)")
    ax.plot(rx, depths, color=C_ARX,   lw=2.0, label=f"Full ARX (phi, beta, gamma)")
    ax.fill_betweenx(depths, ra, rb, where=(rb > ra), alpha=0.12, color=C_ANCHOR,
                     label="Anchor gain")
    ax.fill_betweenx(depths, rx, ra, where=(ra > rx), alpha=0.12, color=C_ARX,
                     label="ARX bonus")
    ax.axvline(0, color="k", lw=0.5, ls=":")
    ax.set_ylim(295, 0)
    ax.set_xlabel("Hold-out RMSE (mm, median over 2022–2025 folds)")
    ax.set_ylabel("Depth (m)")
    ax.set_title(
        f"{station} — Ablation: Baseline vs Anchor-Only vs Full ARX\n"
        f"Anchor improvement = {np.nanmedian(per_depth_df['anchor_impr_pct']):.1f}%   "
        f"ARX bonus = {np.nanmedian(per_depth_df['arx_bonus_pct']):.1f}%   "
        f"Total = {np.nanmedian(per_depth_df['total_impr_pct']):.1f}%"
    )
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / f"fig_ablation_{station.lower()}_depth.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved fig_ablation_{station.lower()}_depth.png")


def plot_tuku_ts(station, fold_ho_data, n_depths=N_DEPTHS):
    """Time-series comparison for 4 representative depths, stitching all folds."""
    TARGET_DEPTHS = [30, 60, 120, 200]  # depth indices
    TARGET_K      = [d // 5 for d in TARGET_DEPTHS]

    # Stitch all folds into one continuous hold-out period
    all_dates  = []
    all_obs    = {k: [] for k in TARGET_K}
    all_arx    = {k: [] for k in TARGET_K}
    all_anchor = {k: [] for k in TARGET_K}
    all_base   = {k: [] for k in TARGET_K}

    for fd in fold_ho_data:
        if fd is None:
            continue
        dates = fd["dates"].to_pydatetime()
        for k in TARGET_K:
            all_obs[k].extend(fd["Y_obs"][:, k].tolist())
            all_arx[k].extend(fd["Y_arx"][:, k].tolist())
            all_anchor[k].extend(fd["Y_anchor"][:, k].tolist())
            all_base[k].extend(fd["Y_base"][:, k].tolist())
        all_dates.extend(dates)

    if not all_dates:
        return

    fig, axes = plt.subplots(len(TARGET_DEPTHS), 1, figsize=(13, 10), sharex=True)
    fig.suptitle(
        f"{station} — Ablation time series (hold-out 2022–2025)\n"
        f"Negative = subsidence | anchor = Y0 + f̄·Δx | ARX = recursive phi/beta/gamma",
        fontsize=10, fontweight="bold"
    )

    for ax, depth, k in zip(axes, TARGET_DEPTHS, TARGET_K):
        obs    = np.array(all_obs[k])
        arx    = np.array(all_arx[k])
        anchor = np.array(all_anchor[k])
        base   = np.array(all_base[k])

        rmse_b = float(np.sqrt(np.nanmean((obs - base)**2)))
        rmse_a = float(np.sqrt(np.nanmean((obs - anchor)**2)))
        rmse_x = float(np.sqrt(np.nanmean((obs - arx)**2)))

        ax.plot(all_dates, obs,    color=C_OBS,    lw=1.5, label="MLCW obs")
        ax.plot(all_dates, anchor, color=C_ANCHOR, lw=1.2, label=f"Anchor-only (RMSE={rmse_a:.2f} mm)")
        ax.plot(all_dates, arx,    color=C_ARX,    lw=1.2, label=f"ARX (RMSE={rmse_x:.2f} mm)")
        ax.plot(all_dates, base,   color=C_BASE,   lw=0.9, linestyle="--",
                label=f"Baseline (RMSE={rmse_b:.2f} mm)")
        ax.axhline(0, color="k", lw=0.4, ls=":", alpha=0.4)
        ax.set_ylabel("mm")
        ax.set_title(f"Depth {depth} m", fontsize=9)
        ax.grid(True, alpha=0.25)
        if depth == TARGET_DEPTHS[0]:
            ax.legend(fontsize=7.5, loc="lower left")

    axes[-1].set_xlabel("Date")
    axes[-1].xaxis.set_major_locator(mdates.YearLocator())
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.autofmt_xdate(rotation=30, ha="right")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(OUT_DIR / f"fig_ablation_{station.lower()}_ts.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved fig_ablation_{station.lower()}_ts.png")


def plot_summary_bar(summaries_df):
    """Station-level stacked bar: anchor_impr_pct / arx_bonus_pct."""
    df = summaries_df.sort_values("total_impr_pct", ascending=True).copy()
    y  = np.arange(len(df))

    fig, ax = plt.subplots(figsize=(10, 7))
    bars_a = ax.barh(y, df["anchor_impr_pct"], height=0.6, color=C_ANCHOR,
                     label="Anchor gain (Y0 + f̄·Δx over baseline)")
    bars_x = ax.barh(y, df["arx_bonus_pct"],   height=0.6, color=C_ARX,
                     left=df["anchor_impr_pct"],
                     label="ARX bonus (phi + gamma over anchor)")

    ax.set_yticks(y)
    ax.set_yticklabels(df["station"], fontsize=9)
    ax.axvline(0, color="k", lw=0.8)
    ax.set_xlabel("Median % RMSE reduction vs. static baseline", fontsize=10)
    ax.set_title(
        "Ablation Study — ARX Improvement Decomposition\n19 Active Stations | Walk-Forward 2022–2025",
        fontsize=11
    )
    ax.legend(fontsize=9, loc="lower right")
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig_ablation_summary.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  saved fig_ablation_summary.png")


def plot_scatter(summaries_df):
    """Scatter: anchor_improvement vs total_improvement per station."""
    df = summaries_df.copy()
    fig, ax = plt.subplots(figsize=(7, 6))

    for _, row in df.iterrows():
        ax.scatter(row["total_impr_pct"], row["anchor_impr_pct"], s=60, zorder=3)
        ax.annotate(row["station"], (row["total_impr_pct"], row["anchor_impr_pct"]),
                    fontsize=6.5, xytext=(3, 3), textcoords="offset points")

    lims = [min(df["total_impr_pct"].min(), df["anchor_impr_pct"].min()) - 5,
            max(df["total_impr_pct"].max(), df["anchor_impr_pct"].max()) + 5]
    ax.plot(lims, lims, "k--", lw=0.8, label="y=x (anchor = full ARX)")
    ax.axhline(0, color="k", lw=0.5, ls=":")
    ax.axvline(0, color="k", lw=0.5, ls=":")
    ax.set_xlim(*lims)
    ax.set_ylim(*lims)
    ax.set_xlabel("Total ARX improvement over baseline (%)")
    ax.set_ylabel("Anchor-only improvement over baseline (%)")
    ax.set_title(
        "Anchor vs Full ARX — Improvement Decomposition\n"
        "Points above y=x: anchor captures more improvement than ARX\n"
        "Points below y=x: ARX bonus is positive (ARX adds value over anchor)"
    )
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig_ablation_scatter.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  saved fig_ablation_scatter.png")


# ── Main ──────────────────────────────────────────────────────────────────────────

def main():
    print("Loading InSAR feather...")
    insar_data = load_insar()
    print(f"  {len(insar_data)} stations found\n")

    stations = sorted([p.stem.replace("_5m_grid", "")
                       for p in MLCW_DIR.glob("*_5m_grid.csv")])
    print(f"Processing {len(stations)} MLCW stations...\n")

    all_summaries  = []
    tuku_result    = None

    for station in stations:
        print(f"  {station}...", end=" ", flush=True)
        result = process_station(station, insar_data)
        if result is None:
            print("skipped (no hold-out data)")
            continue

        ss = result["station_summary"]
        all_summaries.append(ss)

        anchor_f = ss["anchor_fraction_of_total"]
        print(
            f"base={ss['rmse_base_med_mm']:.3f}  anchor={ss['rmse_anchor_med_mm']:.3f}  "
            f"arx={ss['rmse_arx_med_mm']:.3f} mm  |  "
            f"anchor={ss['anchor_impr_pct']:.1f}%  bonus={ss['arx_bonus_pct']:.1f}%  "
            f"total={ss['total_impr_pct']:.1f}%  "
            f"(anchor_frac={anchor_f:.2f})" if anchor_f is not None else ""
        )

        if station == "TUKU":
            tuku_result = result

    print("\n--- Generating figures ---")

    if tuku_result:
        plot_tuku_depth("TUKU", tuku_result["per_depth_df"])
        plot_tuku_ts("TUKU", tuku_result["fold_ho_data"])

    summaries_df = pd.DataFrame(all_summaries)
    summaries_df.to_csv(OUT_DIR / "ablation_allstations.csv", index=False)
    print(f"  saved ablation_allstations.csv  ({len(summaries_df)} stations)")

    plot_summary_bar(summaries_df)
    plot_scatter(summaries_df)

    # ── Console summary ──────────────────────────────────────────────────────────
    print(f"\n{'Station':<18} {'base':>7} {'anchor':>8} {'arx':>7} {'anchor%':>9} {'bonus%':>8} {'total%':>8}")
    print("-" * 72)
    for _, row in summaries_df.sort_values("total_impr_pct", ascending=False).iterrows():
        print(f"{row['station']:<18} {row['rmse_base_med_mm']:>7.3f} {row['rmse_anchor_med_mm']:>8.3f} "
              f"{row['rmse_arx_med_mm']:>7.3f} {row['anchor_impr_pct']:>9.1f} "
              f"{row['arx_bonus_pct']:>8.1f} {row['total_impr_pct']:>8.1f}")

    print(f"\nMedian across stations:")
    print(f"  anchor_impr_pct : {summaries_df['anchor_impr_pct'].median():.1f}%")
    print(f"  arx_bonus_pct   : {summaries_df['arx_bonus_pct'].median():.1f}%")
    print(f"  total_impr_pct  : {summaries_df['total_impr_pct'].median():.1f}%")
    print(f"  anchor_fraction : {summaries_df['anchor_fraction_of_total'].dropna().median():.2f}")

    print(f"\nAll outputs saved to: {OUT_DIR}")


if __name__ == "__main__":
    main()
