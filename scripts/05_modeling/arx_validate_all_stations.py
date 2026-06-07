"""
ARX Walk-Forward Validation Figures — All Stations

Raw convention throughout: negative = subsidence, positive = uplift (no negation).

Fold stitching: each hold-out year is predicted recursively starting from the
last *observed* MLCW value at the fold boundary. The four folds are then
concatenated into one continuous predicted time series with no jumps.

Per-station outputs → arx_method7/figures/{STATION}/
    {STATION}_arx_ts_fig1.png          depths   0– 95 m  (20 subplots)
    {STATION}_arx_ts_fig2.png          depths 100–195 m
    {STATION}_arx_ts_fig3.png          depths 200–295 m
    {STATION}_arx_rmse_profile.png     per-depth RMSE (ARX vs baseline)
    {STATION}_arx_residual_heatmap.png heatmap of obs − ARX
    {STATION}_arx_total_timeseries.png total column + residual panel
    {STATION}_arx_metrics.json         numeric evaluation metrics per depth

Summary → arx_method7/arx_validation_summary.json

Jump-detection metrics (in JSON):
    jump_rmse_mm        RMSE of the prediction itself (sanity check = walkforward RMSE)
    fold_boundary_jump_mm  absolute displacement at each fold seam (should be ~0 with stitching)
    n_sign_flips        count of epochs where the sign of (obs[i]-obs[i-1]) != sign of (arx[i]-arx[i-1])
    direction_agreement_frac  fraction of epochs where obs and arx move in the same direction
    max_single_step_mm  largest single-epoch step in ARX prediction (indicator of instability)
    smoothness_ratio    std(diff(ARX)) / std(diff(obs)) — >1 means ARX is noisier than observed
"""

import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
from scipy import linalg as la

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE      = Path(r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2")
MLCW_DIR  = BASE / "MLCW_5m_regular"
INSAR_F   = BASE / "InSAR_timeries" / "mlcw_interp_insar_IDW_extend.feather"
RATIO_DIR = BASE / "direct_ratio_MLCW_InSAR"
ARX_DIR   = BASE / "arx_method7"
FIG_ROOT  = ARX_DIR / "figures"
FIG_ROOT.mkdir(exist_ok=True)

# ── Constants ──────────────────────────────────────────────────────────────────
DEPTHS_M   = list(range(0, 300, 5))
DEPTH_COLS = [f"depth_{d:03d}m" for d in DEPTHS_M]
N_DEPTHS   = 60
NCOLS, NROWS = 5, 4
FIG_SLICES = [slice(0, 20), slice(20, 40), slice(40, 60)]
FIG_DEPTH_LABELS = ["0–95 m", "100–195 m", "200–295 m"]

FOLD_ENDS  = ["2021-11-30", "2022-11-30", "2023-11-30", "2024-11-30"]
FOLD_NAMES = ["2022", "2023", "2024", "2025"]
HOLDOUT_START = pd.Timestamp("2022-01-01")

C_OBS  = "black"
C_ARX  = "#1f77b4"
C_BASE = "#d62728"


# ── Data loading (raw convention, no negation) ─────────────────────────────────

def load_insar():
    df = pd.read_feather(INSAR_F)
    epoch_cols = [c for c in df.columns if str(c).startswith("D20")]
    dates = pd.to_datetime([str(c).lstrip("D") for c in epoch_cols], format="%Y%m%d")
    name_col = "Ename" if "Ename" in df.columns else "station"
    result = {}
    for _, row in df.iterrows():
        st = row[name_col]
        vals = row[epoch_cols].values.astype(float) * 1000.0   # m → mm
        result[st] = {"dates": dates, "values": vals}   # raw: negative = subsidence
    return result


def load_mlcw(station):
    path = MLCW_DIR / f"{station}_5m_grid.csv"
    df = pd.read_csv(path, parse_dates=["datetime"]).set_index("datetime").sort_index()
    cols = [c for c in DEPTH_COLS if c in df.columns]
    Y = df[cols].values.astype(float)   # raw: negative = subsidence
    return df.index.to_numpy(), Y


def load_ratio_profile(station):
    path = RATIO_DIR / station / f"{station}_direct_ratio_stats.csv"
    if not path.exists():
        return np.zeros(N_DEPTHS)
    return pd.read_csv(path)["f_median"].values.astype(float)


def align(insar_dates, insar_vals, mlcw_dates, mlcw_Y):
    s = pd.Series(insar_vals, index=pd.DatetimeIndex(insar_dates))
    m = pd.DataFrame(mlcw_Y, index=pd.DatetimeIndex(mlcw_dates))
    common = s.index.intersection(m.index)
    if len(common) < 10:
        return None, None, None
    x = s.loc[common].values
    Y = m.loc[common].values
    # Baseline-align to first common epoch so both series start at 0
    # (MLCW is cumulative from ~2003 install; InSAR from 2015-01-16)
    x = x - x[0]
    Y = Y - Y[0, :]
    return common, x, Y


# ── OLS and recursive prediction ───────────────────────────────────────────────

def fit_arx_ols(Y_k, x, dx):
    A = np.column_stack([Y_k[:-1], x[1:], dx[1:]])
    b = Y_k[1:]
    params, _, _, _ = la.lstsq(A, b, check_finite=False)
    return params   # phi, beta, gamma


def predict_recursive(phi, beta, gamma, x_ho, dx_ho, Y0):
    n = len(x_ho)
    Y_hat = np.empty(n)
    yp = Y0
    for i in range(n):
        Y_hat[i] = phi * yp + beta * x_ho[i] + gamma * dx_ho[i]
        yp = Y_hat[i]
    return Y_hat


# ── Stitched fold prediction ───────────────────────────────────────────────────

def build_stitched_predictions(common_dates, x, Y, f_median):
    """
    For each fold, fit OLS on training window, then predict hold-out recursively
    anchored to the last *observed* MLCW at the fold boundary.
    Concatenate all folds into one continuous hold-out prediction.

    Returns:
        ho_dates  : DatetimeIndex of all hold-out epochs
        Y_ho_obs  : (n_ho, 60) observed MLCW
        Y_ho_arx  : (n_ho, 60) ARX stitched prediction
        Y_ho_base : (n_ho, 60) static baseline prediction
    """
    common_dt = pd.DatetimeIndex(common_dates)
    dx = np.concatenate([[0.0], np.diff(x)])

    arx_by_idx  = {}
    base_by_idx = {}

    for fi, fold_end_str in enumerate(FOLD_ENDS):
        fold_end = pd.Timestamp(fold_end_str)
        train_mask = common_dt <= fold_end
        if fi + 1 < len(FOLD_ENDS):
            next_end = pd.Timestamp(FOLD_ENDS[fi + 1])
            ho_mask = (common_dt > fold_end) & (common_dt <= next_end)
        else:
            ho_mask = common_dt > fold_end

        n_train = train_mask.sum()
        n_ho    = ho_mask.sum()
        if n_train < 50 or n_ho < 3:
            continue

        x_train  = x[train_mask]
        dx_train = dx[train_mask]
        x_ho     = x[ho_mask]
        dx_ho    = dx[ho_mask]
        ho_idx   = np.where(ho_mask)[0]

        for k in range(N_DEPTHS):
            Y_k_train = Y[train_mask, k]
            if not np.all(np.isfinite(Y_k_train)) or len(Y_k_train) < 4:
                continue
            try:
                params = fit_arx_ols(Y_k_train, x_train, dx_train)
            except Exception:
                continue
            phi_k, beta_k, gamma_k = params
            # Anchor: last *observed* MLCW at training window end
            Y0 = Y_k_train[-1]
            y_hat  = predict_recursive(phi_k, beta_k, gamma_k, x_ho, dx_ho, Y0)
            y_base = f_median[k] * x_ho

            for j, idx in enumerate(ho_idx):
                if idx not in arx_by_idx:
                    arx_by_idx[idx]  = np.full(N_DEPTHS, np.nan)
                    base_by_idx[idx] = np.full(N_DEPTHS, np.nan)
                arx_by_idx[idx][k]  = y_hat[j]
                base_by_idx[idx][k] = y_base[j]

    if not arx_by_idx:
        return None, None, None, None

    ho_indices = sorted(arx_by_idx.keys())
    ho_dates   = common_dt[ho_indices]
    Y_ho_obs   = Y[ho_indices, :]
    Y_ho_arx   = np.stack([arx_by_idx[i]  for i in ho_indices])
    Y_ho_base  = np.stack([base_by_idx[i] for i in ho_indices])
    return ho_dates, Y_ho_obs, Y_ho_arx, Y_ho_base


# ── Numeric metrics ────────────────────────────────────────────────────────────

def compute_metrics(ho_dates, Y_obs, Y_arx, Y_base):
    """
    Compute per-depth evaluation metrics. Returns a dict of lists (length 60).

    Metrics:
        rmse_arx_mm          RMSE of ARX prediction
        rmse_base_mm         RMSE of static baseline
        improvement_pct      (rmse_base - rmse_arx) / rmse_base * 100
        bias_arx_mm          mean(obs - arx)
        r2_arx               coefficient of determination (ARX vs obs)
        direction_agreement  fraction of epochs where obs and ARX move same direction
        smoothness_ratio     std(diff(arx)) / std(diff(obs)) — >1 means ARX noisier
        max_single_step_mm   largest single-epoch step in ARX (instability indicator)
        fold_boundary_jump_mm  |ARX(fold_start) - OBS(fold_start-1)| at each fold boundary
    """
    n = len(ho_dates)
    metrics = {
        "depth_m": DEPTHS_M,
        "rmse_arx_mm":           [],
        "rmse_base_mm":          [],
        "improvement_pct":       [],
        "bias_arx_mm":           [],
        "r2_arx":                [],
        "direction_agreement":   [],
        "smoothness_ratio":      [],
        "max_single_step_mm":    [],
    }

    for k in range(N_DEPTHS):
        obs  = Y_obs[:, k]
        arx  = Y_arx[:, k]
        base = Y_base[:, k]
        valid = np.isfinite(obs) & np.isfinite(arx)

        if valid.sum() < 5:
            for key in metrics:
                if key != "depth_m":
                    metrics[key].append(None)
            continue

        obs_v  = obs[valid]
        arx_v  = arx[valid]
        base_v = base[valid]

        rmse_a = float(np.sqrt(np.mean((obs_v - arx_v)**2)))
        rmse_b = float(np.sqrt(np.mean((obs_v - base_v)**2)))
        impr   = float(100.0 * (rmse_b - rmse_a) / (rmse_b + 1e-9))
        bias   = float(np.mean(obs_v - arx_v))
        ss_res = float(np.sum((obs_v - arx_v)**2))
        ss_tot = float(np.sum((obs_v - obs_v.mean())**2))
        r2     = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else None

        # Direction agreement: do obs and ARX move in the same direction epoch→epoch?
        d_obs = np.diff(obs_v)
        d_arx = np.diff(arx_v)
        agree = float(np.mean(np.sign(d_obs) == np.sign(d_arx)))

        # Smoothness: is ARX noisier than observed?
        std_d_obs = float(np.std(d_obs))
        std_d_arx = float(np.std(d_arx))
        smooth = float(std_d_arx / std_d_obs) if std_d_obs > 1e-9 else None

        # Maximum single-epoch step in ARX
        max_step = float(np.max(np.abs(d_arx))) if len(d_arx) > 0 else None

        metrics["rmse_arx_mm"].append(round(rmse_a, 4))
        metrics["rmse_base_mm"].append(round(rmse_b, 4))
        metrics["improvement_pct"].append(round(impr, 2))
        metrics["bias_arx_mm"].append(round(bias, 4))
        metrics["r2_arx"].append(round(r2, 4) if r2 is not None else None)
        metrics["direction_agreement"].append(round(agree, 4))
        metrics["smoothness_ratio"].append(round(smooth, 4) if smooth is not None else None)
        metrics["max_single_step_mm"].append(round(max_step, 4) if max_step is not None else None)

    # Fold boundary jump magnitudes: |ARX(first epoch of fold) - OBS(last epoch of training)|
    # With stitching these should equal 0 by construction; we keep the check as a sanity test.
    fold_jumps = {}
    for fi, fold_end_str in enumerate(FOLD_ENDS):
        fold_end = pd.Timestamp(fold_end_str)
        # last training epoch index
        before_fold = ho_dates <= fold_end
        after_fold  = ho_dates > fold_end
        if before_fold.sum() == 0 or after_fold.sum() == 0:
            continue
        last_train_arx  = Y_arx[before_fold][-1]    # last ARX value before fold boundary
        first_ho_arx    = Y_arx[after_fold][0]       # first ARX value after fold boundary
        jump_per_depth  = np.abs(first_ho_arx - last_train_arx)
        fold_jumps[FOLD_NAMES[fi]] = {
            "mean_abs_jump_mm": round(float(np.nanmean(jump_per_depth)), 4),
            "max_abs_jump_mm":  round(float(np.nanmax(jump_per_depth)), 4),
        }

    # Summary scalars
    rmse_arr = [v for v in metrics["rmse_arx_mm"] if v is not None]
    impr_arr = [v for v in metrics["improvement_pct"] if v is not None]
    smth_arr = [v for v in metrics["smoothness_ratio"] if v is not None]
    dagr_arr = [v for v in metrics["direction_agreement"] if v is not None]

    summary = {
        "median_rmse_arx_mm":          round(float(np.nanmedian(rmse_arr)), 4) if rmse_arr else None,
        "median_improvement_pct":      round(float(np.nanmedian(impr_arr)), 2) if impr_arr else None,
        "median_smoothness_ratio":     round(float(np.nanmedian(smth_arr)), 4) if smth_arr else None,
        "median_direction_agreement":  round(float(np.nanmedian(dagr_arr)), 4) if dagr_arr else None,
        "pct_depths_improved":         round(100.0 * sum(1 for v in impr_arr if v > 0) / len(impr_arr), 1) if impr_arr else None,
        "pct_depths_smooth_ratio_gt1": round(100.0 * sum(1 for v in smth_arr if v > 1.0) / len(smth_arr), 1) if smth_arr else None,
        "fold_boundary_jumps":         fold_jumps,
    }

    return metrics, summary


# ── Figures ────────────────────────────────────────────────────────────────────

def plot_ts_figures(station, out_dir, ho_dates, Y_obs, Y_arx, Y_base,
                    rmse_arx, rmse_base):
    date_axis = list(ho_dates.to_pydatetime())
    n_ho = len(date_axis)

    for fig_idx, (sl, depth_label) in enumerate(zip(FIG_SLICES, FIG_DEPTH_LABELS), 1):
        depths_in_fig = [DEPTHS_M[i] for i in range(*sl.indices(N_DEPTHS))]
        n_sub = len(depths_in_fig)
        n_rows_used = int(np.ceil(n_sub / NCOLS))

        fig, axes = plt.subplots(n_rows_used, NCOLS,
                                 figsize=(NCOLS * 3.5, n_rows_used * 2.8),
                                 squeeze=False)
        fig.suptitle(
            f"{station} — ARX walk-forward vs. observed MLCW  (hold-out 2022–2025)\n"
            f"Depths {depth_label}   n = {n_ho} epochs   |   negative = subsidence",
            fontsize=11, fontweight="bold"
        )

        for sub_idx, depth in enumerate(depths_in_fig):
            k   = depth // 5
            row = sub_idx // NCOLS
            col = sub_idx % NCOLS
            ax  = axes[row][col]

            y_obs  = Y_obs[:, k]
            y_arx  = Y_arx[:, k]
            y_base = Y_base[:, k]

            ax.plot(date_axis, y_obs,  color=C_OBS,  lw=1.0, label="MLCW obs")
            ax.plot(date_axis, y_arx,  color=C_ARX,  lw=1.0, label="ARX")
            ax.plot(date_axis, y_base, color=C_BASE, lw=0.8, linestyle="--",
                    label="Baseline")
            ax.axhline(0, color="k", lw=0.4, ls=":", alpha=0.5)

            r_arx  = rmse_arx[k]
            r_base = rmse_base[k]
            ax.set_title(f"{depth} m  A={r_arx:.2f} B={r_base:.2f} mm",
                         fontsize=7.5, pad=2)
            ax.tick_params(labelsize=6)
            ax.xaxis.set_major_locator(mdates.YearLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
            ax.grid(True, alpha=0.25)

            if sub_idx == 0:
                ax.legend(fontsize=5.5, loc="lower left", framealpha=0.6)

        for empty in range(n_sub, n_rows_used * NCOLS):
            axes[empty // NCOLS][empty % NCOLS].set_visible(False)

        for r in range(n_rows_used):
            axes[r][0].set_ylabel("mm", fontsize=7)

        fig.autofmt_xdate(rotation=45, ha="right")
        fig.tight_layout(rect=[0, 0, 1, 0.94])
        fig.savefig(out_dir / f"{station}_arx_ts_fig{fig_idx}.png",
                    dpi=130, bbox_inches="tight")
        plt.close(fig)


def plot_rmse_profile(station, out_dir, rmse_arx, rmse_base):
    fig, ax = plt.subplots(figsize=(8, 10))
    depths = np.array(DEPTHS_M, dtype=float)
    ax.plot(rmse_base, depths, color=C_BASE, lw=1.8, label="Baseline (static ratio)")
    ax.plot(rmse_arx,  depths, color=C_ARX,  lw=1.8, label="ARX (walk-forward)")
    ax.fill_betweenx(depths, rmse_arx, rmse_base,
                     where=(rmse_base > rmse_arx),
                     color=C_ARX, alpha=0.15, label="ARX improvement region")
    ax.axvline(0, color="k", lw=0.6, ls=":")
    ax.invert_yaxis()
    ax.set_ylim(295, 0)
    ax.set_xlabel("Hold-out RMSE (mm)", fontsize=11)
    ax.set_ylabel("Depth (m)", fontsize=11)
    med_impr = 100.0 * np.nanmedian(
        (rmse_base - rmse_arx) / (rmse_base + 1e-9)
    )
    ax.set_title(
        f"{station} — Per-depth RMSE  (hold-out 2022–2025)\n"
        f"Median improvement: {med_impr:.1f}%",
        fontsize=11, fontweight="bold"
    )
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / f"{station}_arx_rmse_profile.png",
                dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_residual_heatmap(station, out_dir, ho_dates, Y_obs, Y_arx):
    resid = Y_obs - Y_arx
    abs_r = np.abs(resid[np.isfinite(resid)])
    vmax  = float(np.percentile(abs_r, 98)) if len(abs_r) > 0 else 1.0

    n_ho = len(ho_dates)
    depths = np.array(DEPTHS_M, dtype=float)
    depth_edges = np.append(depths - 2.5, depths[-1] + 2.5)

    fig, ax = plt.subplots(figsize=(14, 6))
    pcm = ax.pcolormesh(depth_edges, np.arange(n_ho + 1), resid,
                        cmap="RdBu_r", vmin=-vmax, vmax=vmax, shading="flat")
    yticks, ylabels, cur = [], [], None
    for idx, d in enumerate(ho_dates.to_pydatetime()):
        yr = d.year
        if yr != cur:
            yticks.append(idx)
            ylabels.append(str(yr))
            cur = yr
    ax.set_yticks(yticks)
    ax.set_yticklabels(ylabels, fontsize=9)
    ax.set_xlabel("Depth (m)", fontsize=11)
    ax.set_ylabel("Epoch (year)", fontsize=11)
    ax.set_title(
        f"{station} — ARX residual heatmap  (obs − ARX)\n"
        f"Hold-out 2022–2025  |  clipped to ±{vmax:.2f} mm (98th pct)",
        fontsize=10
    )
    fig.colorbar(pcm, ax=ax, shrink=0.85, pad=0.01).set_label("Residual (mm)", fontsize=9)
    fig.tight_layout()
    fig.savefig(out_dir / f"{station}_arx_residual_heatmap.png",
                dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_total_timeseries(station, out_dir, ho_dates, Y_obs, Y_arx, Y_base):
    total_obs  = np.nansum(Y_obs,  axis=1)
    total_arx  = np.nansum(Y_arx,  axis=1)
    total_base = np.nansum(Y_base, axis=1)
    date_axis  = list(ho_dates.to_pydatetime())

    res_arx  = total_obs - total_arx
    res_base = total_obs - total_base
    rmse_arx  = float(np.sqrt(np.mean(res_arx**2)))
    rmse_base = float(np.sqrt(np.mean(res_base**2)))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

    ax1.plot(date_axis, total_obs,  color=C_OBS,  lw=1.5, label="MLCW obs (total column)")
    ax1.plot(date_axis, total_arx,  color=C_ARX,  lw=1.5,
             label=f"ARX  (RMSE={rmse_arx:.2f} mm)")
    ax1.plot(date_axis, total_base, color=C_BASE, lw=1.0, linestyle="--",
             label=f"Baseline  (RMSE={rmse_base:.2f} mm)")
    ax1.axhline(0, color="k", lw=0.5, ls=":")
    ax1.set_ylabel("Total column displacement (mm)", fontsize=10)
    ax1.set_title(
        f"{station} — Total column displacement  (hold-out 2022–2025)\n"
        f"Negative = subsidence",
        fontsize=11, fontweight="bold"
    )
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)

    ax2.plot(date_axis, res_arx,  color=C_ARX,  lw=1.0, label="ARX residual (obs−ARX)")
    ax2.plot(date_axis, res_base, color=C_BASE, lw=0.8, linestyle="--",
             label="Baseline residual")
    ax2.axhline(0, color="k", lw=0.8)
    ax2.set_ylabel("Residual (mm)", fontsize=10)
    ax2.set_xlabel("Date", fontsize=10)
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_locator(mdates.YearLocator())
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    fig.autofmt_xdate(rotation=30, ha="right")
    fig.tight_layout()
    fig.savefig(out_dir / f"{station}_arx_total_timeseries.png",
                dpi=150, bbox_inches="tight")
    plt.close(fig)


# ── Per-station driver ─────────────────────────────────────────────────────────

def process_station(station, insar_data):
    print(f"  {station}...", end=" ", flush=True)

    if station not in insar_data:
        print("no InSAR — skip")
        return None

    try:
        mlcw_dates, mlcw_Y = load_mlcw(station)
    except FileNotFoundError:
        print("no MLCW — skip")
        return None

    common_dates, x, Y = align(
        insar_data[station]["dates"],
        insar_data[station]["values"],
        mlcw_dates, mlcw_Y,
    )
    if common_dates is None:
        print("insufficient overlap — skip")
        return None

    if (pd.DatetimeIndex(common_dates) > HOLDOUT_START).sum() < 10:
        print("no hold-out data (shut-down) — skip")
        return None

    f_median = load_ratio_profile(station)

    ho_dates, Y_ho_obs, Y_ho_arx, Y_ho_base = build_stitched_predictions(
        common_dates, x, Y, f_median
    )
    if ho_dates is None:
        print("prediction failed — skip")
        return None

    # Per-depth RMSE
    rmse_arx  = np.array([
        float(np.sqrt(np.mean((Y_ho_obs[:, k] - Y_ho_arx[:, k])**2)))
        if np.isfinite(Y_ho_obs[:, k]).sum() >= 3 else np.nan
        for k in range(N_DEPTHS)
    ])
    rmse_base = np.array([
        float(np.sqrt(np.mean((Y_ho_obs[:, k] - Y_ho_base[:, k])**2)))
        if np.isfinite(Y_ho_obs[:, k]).sum() >= 3 else np.nan
        for k in range(N_DEPTHS)
    ])

    # Numeric metrics + JSON export
    metrics, summary = compute_metrics(ho_dates, Y_ho_obs, Y_ho_arx, Y_ho_base)

    out_dir = FIG_ROOT / station
    out_dir.mkdir(exist_ok=True)

    json_out = {
        "station": station,
        "n_holdout_epochs": int(len(ho_dates)),
        "holdout_start": str(ho_dates[0].date()),
        "holdout_end":   str(ho_dates[-1].date()),
        "summary": summary,
        "per_depth": [
            {k: (metrics[k][i] if k != "depth_m" else metrics["depth_m"][i])
             for k in metrics}
            for i in range(N_DEPTHS)
        ]
    }
    with open(out_dir / f"{station}_arx_metrics.json", "w") as fh:
        json.dump(json_out, fh, indent=2)

    # Figures
    plot_ts_figures(station, out_dir, ho_dates, Y_ho_obs, Y_ho_arx, Y_ho_base,
                    rmse_arx, rmse_base)
    plot_rmse_profile(station, out_dir, rmse_arx, rmse_base)
    plot_residual_heatmap(station, out_dir, ho_dates, Y_ho_obs, Y_ho_arx)
    plot_total_timeseries(station, out_dir, ho_dates, Y_ho_obs, Y_ho_arx, Y_ho_base)

    med_impr = summary["median_improvement_pct"]
    med_smth = summary["median_smoothness_ratio"]
    med_dagr = summary["median_direction_agreement"]
    n_ho = len(ho_dates)
    print(f"done  n={n_ho}  impr={med_impr:.1f}%  smooth={med_smth:.2f}  dir_agree={med_dagr:.2f}")

    return {
        "station": station,
        "n_holdout_epochs": int(n_ho),
        **summary,
    }


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("Loading InSAR feather...")
    insar_data = load_insar()
    print(f"  {len(insar_data)} stations")

    stations = sorted([p.stem.replace("_5m_grid", "")
                       for p in MLCW_DIR.glob("*_5m_grid.csv")])
    print(f"  {len(stations)} MLCW stations\n")

    all_summaries = []
    for station in stations:
        result = process_station(station, insar_data)
        if result is not None:
            all_summaries.append(result)

    # Cross-station summary JSON
    summary_path = ARX_DIR / "arx_validation_summary.json"
    with open(summary_path, "w") as fh:
        json.dump({
            "n_stations_processed": len(all_summaries),
            "stations": all_summaries,
        }, fh, indent=2)
    print(f"\nSummary JSON saved: {summary_path}")

    # Console table
    print(f"\n{'Station':<18} {'n_ho':>5} {'impr%':>7} {'smooth':>7} {'dir_ag':>7} {'smooth>1%':>9}")
    print("-" * 58)
    for s in all_summaries:
        print(f"{s['station']:<18} {s['n_holdout_epochs']:>5} "
              f"{s['median_improvement_pct'] or 0:>7.1f} "
              f"{s['median_smoothness_ratio'] or 0:>7.2f} "
              f"{s['median_direction_agreement'] or 0:>7.2f} "
              f"{s['pct_depths_smooth_ratio_gt1'] or 0:>9.1f}%")
    print(f"\nDone. Figures: {FIG_ROOT}")


if __name__ == "__main__":
    main()
