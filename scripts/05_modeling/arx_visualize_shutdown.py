"""
ARX Validation — Shut-Down MLCW Stations
=========================================
20 stations whose observations end around 2021.

Validation design (within-window holdout):
  Training window : first common epoch → 2020-11-30
  Hold-out window : 2020-12-01 → station last epoch (~2021 Mar–Nov)

For each station:
  - Fit ARX on training window only (fresh fit, not the full-window params)
  - Predict hold-out recursively, anchored to last observed value at 2020-11-30
  - Baseline: f_median * x_aligned (static direct ratio)

Outputs → arx_method7/figures/shutdown_validation/
  {STATION}_shutdown_ts.png       4-panel full-window time series
  {STATION}_shutdown_rmse.png     per-depth RMSE profile (hold-out only)
  shutdown_summary_heatmap.png    20-station improvement heatmap
  ../arx_shutdown_summary.csv     one row per station
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import TwoSlopeNorm
from pathlib import Path
from scipy import linalg as la

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE      = Path(r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2")
MLCW_DIR  = BASE / "MLCW_5m_regular"
INSAR_F   = BASE / "InSAR_timeries" / "mlcw_interp_insar_IDW_extend.feather"
RATIO_DIR = BASE / "direct_ratio_MLCW_InSAR"
ARX_DIR   = BASE / "arx_method7"
FIG_ROOT  = ARX_DIR / "figures" / "shutdown_validation"
FIG_ROOT.mkdir(parents=True, exist_ok=True)

# ── Constants ──────────────────────────────────────────────────────────────────
DEPTHS_M   = list(range(0, 300, 5))
DEPTH_COLS = [f"depth_{d:03d}m" for d in DEPTHS_M]
N_DEPTHS   = 60

TRAIN_END   = pd.Timestamp("2020-11-30")
HOLDOUT_START = pd.Timestamp("2020-12-01")

SHUTDOWN_STATIONS = [
    "ANHE", "ANNAN", "CANLIN", "DONGGUANG", "DONGSHI", "ERLUN", "FENGAN",
    "FENGRONG", "HAIFENG", "JIANYANG", "LONGYAN", "LUNFENG_XIN", "NANGUANG",
    "XIGANG", "XINGHUA", "XINJIE", "XINPI", "XINXING", "ZHENNAN", "ZHUTANG",
]

# Representative depths for 4-panel per-station figure
REP_DEPTHS = [30, 100, 180, 250]

C_OBS  = "black"
C_ARX  = "#1f77b4"
C_BASE = "#d62728"
SHADE  = "#cce5ff"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.labelsize": 10, "axes.titlesize": 10,
    "xtick.labelsize": 8, "ytick.labelsize": 8,
    "figure.dpi": 150,
})


# ── Data loading ───────────────────────────────────────────────────────────────

def load_insar():
    df = pd.read_feather(INSAR_F)
    epoch_cols = [c for c in df.columns if str(c).startswith("D20")]
    dates = pd.to_datetime([str(c).lstrip("D") for c in epoch_cols], format="%Y%m%d")
    name_col = "Ename" if "Ename" in df.columns else "station"
    result = {}
    for _, row in df.iterrows():
        st = row[name_col]
        vals = row[epoch_cols].values.astype(float) * 1000.0   # m → mm
        result[st] = {"dates": dates, "values": vals}
    return result


def load_mlcw(station):
    path = MLCW_DIR / f"{station}_5m_grid.csv"
    df = pd.read_csv(path, parse_dates=["datetime"]).set_index("datetime").sort_index()
    cols = [c for c in DEPTH_COLS if c in df.columns]
    return df.index.to_numpy(), df[cols].values.astype(float)


def load_ratio(station):
    path = RATIO_DIR / station / f"{station}_direct_ratio_stats.csv"
    if not path.exists():
        return np.zeros(N_DEPTHS)
    return pd.read_csv(path)["f_median"].values.astype(float)


def align(insar_dates, insar_vals, mlcw_dates, mlcw_Y):
    s = pd.Series(insar_vals, index=pd.DatetimeIndex(insar_dates))
    m = pd.DataFrame(mlcw_Y, index=pd.DatetimeIndex(mlcw_dates))
    common = s.index.intersection(m.index)
    if len(common) < 30:
        return None, None, None
    x = s.loc[common].values
    Y = m.loc[common].values
    x = x - x[0]
    Y = Y - Y[0, :]
    return common, x, Y


# ── ARX fitting & prediction ───────────────────────────────────────────────────

def fit_arx_ols(Y_k, x, dx):
    A = np.column_stack([Y_k[:-1], x[1:], dx[1:]])
    b = Y_k[1:]
    params, _, _, _ = la.lstsq(A, b, check_finite=False)
    return params


def predict_recursive(phi, beta, gamma, x_ho, dx_ho, Y0):
    n = len(x_ho)
    Y_hat = np.empty(n)
    yp = Y0
    for i in range(n):
        Y_hat[i] = phi * yp + beta * x_ho[i] + gamma * dx_ho[i]
        yp = Y_hat[i]
    return Y_hat


def rmse(obs, pred):
    mask = np.isfinite(obs) & np.isfinite(pred)
    if mask.sum() < 3:
        return np.nan
    return float(np.sqrt(np.mean((obs[mask] - pred[mask]) ** 2)))


# ── Per-station processing ─────────────────────────────────────────────────────

def process_station(station, insar_data):
    if station not in insar_data:
        print(f"  {station}: no InSAR — skip")
        return None

    try:
        mlcw_dates, mlcw_Y = load_mlcw(station)
    except FileNotFoundError:
        print(f"  {station}: no MLCW — skip")
        return None

    common_dates, x, Y = align(
        insar_data[station]["dates"], insar_data[station]["values"],
        mlcw_dates, mlcw_Y,
    )
    if common_dates is None:
        print(f"  {station}: insufficient overlap — skip")
        return None

    common_dt = pd.DatetimeIndex(common_dates)
    train_mask = common_dt <= TRAIN_END
    ho_mask    = common_dt > TRAIN_END

    n_train = train_mask.sum()
    n_ho    = ho_mask.sum()

    if n_train < 50:
        print(f"  {station}: training too short ({n_train} epochs) — skip")
        return None
    if n_ho < 5:
        print(f"  {station}: hold-out too short ({n_ho} epochs) — skip")
        return None

    f_median = load_ratio(station)

    x_train  = x[train_mask]
    dx_train = np.concatenate([[0.0], np.diff(x_train)])
    x_ho     = x[ho_mask]
    dx_ho    = np.concatenate([[x_ho[0] - x_train[-1]], np.diff(x_ho)])

    # Per-depth fit + prediction
    rmse_arx_arr  = np.full(N_DEPTHS, np.nan)
    rmse_base_arr = np.full(N_DEPTHS, np.nan)
    Y_ho_arx      = np.full((n_ho, N_DEPTHS), np.nan)
    Y_ho_base     = np.full((n_ho, N_DEPTHS), np.nan)

    for k in range(N_DEPTHS):
        Y_k_train = Y[train_mask, k]
        Y_k_ho    = Y[ho_mask, k]

        if not np.all(np.isfinite(Y_k_train)) or len(Y_k_train) < 4:
            continue
        try:
            params = fit_arx_ols(Y_k_train, x_train, dx_train)
        except Exception:
            continue

        phi_k, beta_k, gamma_k = params
        Y0 = Y_k_train[-1]
        y_hat  = predict_recursive(phi_k, beta_k, gamma_k, x_ho, dx_ho, Y0)
        y_base = f_median[k] * x_ho

        Y_ho_arx[:, k]  = y_hat
        Y_ho_base[:, k] = y_base
        rmse_arx_arr[k]  = rmse(Y_k_ho, y_hat)
        rmse_base_arr[k] = rmse(Y_k_ho, y_base)

    med_arx  = float(np.nanmedian(rmse_arx_arr))
    med_base = float(np.nanmedian(rmse_base_arr))
    impr_pct = 100.0 * (med_base - med_arx) / (med_base + 1e-9)
    arx_wins = float(np.nanmean(rmse_arx_arr < rmse_base_arr))

    print(f"  {station}: n_train={n_train}  n_ho={n_ho}  "
          f"RMSE arx={med_arx:.3f}  base={med_base:.3f}  impr={impr_pct:.1f}%")

    return {
        "station":        station,
        "common_dates":   common_dates,
        "x":              x,
        "Y":              Y,
        "train_mask":     train_mask,
        "ho_mask":        ho_mask,
        "Y_ho_arx":       Y_ho_arx,
        "Y_ho_base":      Y_ho_base,
        "rmse_arx":       rmse_arx_arr,
        "rmse_base":      rmse_base_arr,
        "med_arx_mm":     round(med_arx, 4),
        "med_base_mm":    round(med_base, 4),
        "impr_pct":       round(impr_pct, 2),
        "arx_wins_frac":  round(arx_wins, 3),
        "n_train":        int(n_train),
        "n_holdout":      int(n_ho),
    }


# ── Figures ────────────────────────────────────────────────────────────────────

def plot_ts_4panel(res):
    """Full-window 4-panel time series for representative depths."""
    station     = res["station"]
    common_dt   = pd.DatetimeIndex(res["common_dates"])
    x           = res["x"]
    Y           = res["Y"]
    train_mask  = res["train_mask"]
    ho_mask     = res["ho_mask"]
    Y_ho_arx    = res["Y_ho_arx"]
    Y_ho_base   = res["Y_ho_base"]
    rmse_arx    = res["rmse_arx"]
    rmse_base   = res["rmse_base"]

    ho_dates   = common_dt[ho_mask]
    all_dates  = common_dt.to_pydatetime()
    ho_dates_py = ho_dates.to_pydatetime()

    fig, axes = plt.subplots(len(REP_DEPTHS), 1, figsize=(14, 10), sharex=False)
    fig.suptitle(
        f"{station} — ARX vs Observed MLCW (shut-down station)\n"
        f"Training: 2015–2020  |  Hold-out: {str(ho_dates[0].date())} → {str(ho_dates[-1].date())}  "
        f"|  n_ho={res['n_holdout']}  |  Negative = subsidence",
        fontsize=10, fontweight="bold",
    )

    for ax, depth in zip(axes, REP_DEPTHS):
        k = depth // 5
        y_obs_full = Y[:, k]

        # full observed trace (training window)
        ax.plot(all_dates, y_obs_full, color=C_OBS, lw=1.2, label="Observed (MLCW)", zorder=3)

        # shaded hold-out region
        ax.axvspan(ho_dates_py[0], ho_dates_py[-1], alpha=0.12, color="steelblue", zorder=0)

        # ARX and baseline in hold-out
        y_obs_ho = Y[ho_mask, k]
        y_arx_ho  = Y_ho_arx[:, k]
        y_base_ho = Y_ho_base[:, k]

        r_arx  = rmse_arx[k]
        r_base = rmse_base[k]
        impr   = 100.0 * (r_base - r_arx) / (r_base + 1e-9) if np.isfinite(r_base) else np.nan

        ax.plot(ho_dates_py, y_arx_ho,  color=C_ARX,  lw=1.4, label=f"ARX pred  RMSE={r_arx:.2f} mm", zorder=2)
        ax.plot(ho_dates_py, y_base_ho, color=C_BASE, lw=1.0, ls="--",
                label=f"Baseline  RMSE={r_base:.2f} mm", zorder=1)

        impr_str = f"{impr:+.1f}%" if np.isfinite(impr) else "n/a"
        ax.set_title(f"Depth {depth} m  |  improvement = {impr_str}", fontsize=9)
        ax.set_ylabel("mm", fontsize=8)
        ax.axhline(0, color="k", lw=0.4, ls=":", alpha=0.5)
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.grid(True, alpha=0.2)

        if depth == REP_DEPTHS[0]:
            ax.legend(fontsize=8, loc="lower left", framealpha=0.7)

    axes[-1].set_xlabel("Date", fontsize=9)
    fig.autofmt_xdate(rotation=30, ha="right")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    out = FIG_ROOT / f"{station}_shutdown_ts.png"
    fig.savefig(out, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"    saved {out.name}")


def plot_rmse_profile(res):
    station   = res["station"]
    depths    = np.array(DEPTHS_M, dtype=float)
    rmse_arx  = res["rmse_arx"]
    rmse_base = res["rmse_base"]

    fig, ax = plt.subplots(figsize=(7, 9))
    ax.plot(rmse_base, depths, color=C_BASE, lw=1.8, ls="--", label="Baseline (static ratio)")
    ax.plot(rmse_arx,  depths, color=C_ARX,  lw=1.8, label="ARX (hold-out 2021)")
    ax.fill_betweenx(depths, rmse_arx, rmse_base,
                     where=(np.isfinite(rmse_arx) & np.isfinite(rmse_base) & (rmse_base > rmse_arx)),
                     color=C_ARX, alpha=0.15, label="ARX improvement")
    ax.invert_yaxis()
    ax.set_ylim(295, 0)
    ax.set_xlabel("Hold-out RMSE (mm)", fontsize=11)
    ax.set_ylabel("Depth (m)", fontsize=11)
    ax.set_title(
        f"{station} — Per-depth RMSE  (hold-out: Dec 2020 → last obs)\n"
        f"Median improvement: {res['impr_pct']:.1f}%",
        fontsize=10, fontweight="bold",
    )
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    out = FIG_ROOT / f"{station}_shutdown_rmse.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_summary_heatmap(all_results):
    stations  = [r["station"] for r in all_results]
    impr_mat  = np.full((len(stations), N_DEPTHS), np.nan)

    for i, res in enumerate(all_results):
        ra = res["rmse_arx"]
        rb = res["rmse_base"]
        valid = np.isfinite(ra) & np.isfinite(rb) & (rb > 1e-9)
        impr_mat[i, valid] = 100.0 * (rb[valid] - ra[valid]) / rb[valid]

    dep_arr = np.array(DEPTHS_M, dtype=float)

    fig, ax = plt.subplots(figsize=(14, 8))
    vmax = 100.0
    vmin = max(-100.0, float(np.nanpercentile(impr_mat, 2)))
    norm = TwoSlopeNorm(vmin=vmin, vcenter=0, vmax=vmax)
    im = ax.imshow(
        impr_mat, aspect="auto", origin="upper", cmap="RdYlGn",
        extent=[dep_arr[0], dep_arr[-1], len(stations) - 0.5, -0.5],
        norm=norm,
    )
    ax.set_yticks(np.arange(len(stations)))
    ax.set_yticklabels(stations, fontsize=9)
    ax.set_xlabel("Depth (m)", fontsize=11)
    ax.set_title(
        "ARX RMSE Improvement over Static Baseline — Shut-Down Stations\n"
        "(hold-out: Dec 2020 → last observation ~2021)   Green = ARX wins",
        fontsize=11, fontweight="bold",
    )
    cb = fig.colorbar(im, ax=ax, shrink=0.85, pad=0.01)
    cb.set_label("RMSE improvement (%)", fontsize=10)

    # annotate median improvement per station
    for i, res in enumerate(all_results):
        ax.text(dep_arr[-1] + 3, i, f"{res['impr_pct']:+.0f}%",
                va="center", ha="left", fontsize=7.5, color="#333333")

    fig.tight_layout()
    out = FIG_ROOT / "shutdown_summary_heatmap.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Summary heatmap saved: {out}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("Loading InSAR feather...")
    insar_data = load_insar()

    all_results = []
    for station in SHUTDOWN_STATIONS:
        print(f"Processing {station}...")
        res = process_station(station, insar_data)
        if res is None:
            continue
        plot_ts_4panel(res)
        plot_rmse_profile(res)
        all_results.append(res)

    if not all_results:
        print("No results.")
        return

    # Summary heatmap
    plot_summary_heatmap(all_results)

    # Summary CSV
    rows = [{
        "station":       r["station"],
        "n_train":       r["n_train"],
        "n_holdout":     r["n_holdout"],
        "rmse_arx_mm":   r["med_arx_mm"],
        "rmse_base_mm":  r["med_base_mm"],
        "impr_pct":      r["impr_pct"],
        "arx_wins_frac": r["arx_wins_frac"],
    } for r in all_results]
    csv_path = ARX_DIR / "arx_shutdown_summary.csv"
    pd.DataFrame(rows).sort_values("impr_pct", ascending=False).to_csv(csv_path, index=False)
    print(f"\nSummary CSV: {csv_path}")

    # Console summary
    print(f"\n{'Station':<16} {'n_ho':>5} {'arx_mm':>8} {'base_mm':>8} {'impr%':>7} {'wins':>6}")
    print("-" * 57)
    for r in sorted(all_results, key=lambda x: -x["impr_pct"]):
        print(f"{r['station']:<16} {r['n_holdout']:>5} "
              f"{r['med_arx_mm']:>8.3f} {r['med_base_mm']:>8.3f} "
              f"{r['impr_pct']:>7.1f} {r['arx_wins_frac']:>6.2f}")

    print(f"\nFigures saved to: {FIG_ROOT}")


if __name__ == "__main__":
    main()
