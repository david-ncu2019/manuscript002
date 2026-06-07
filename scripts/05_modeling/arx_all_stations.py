"""
Method 7: Per-station ARX (AutoRegressive with eXogenous InSAR) model.

Model per depth k at station s:
  Y_s(i,k) = phi_k * Y_s(i-1,k) + beta_k * x_s(i) + gamma_k * dx_s(i) + eps_k

where:
  Y_s(i,k)  = MLCW cumulative displacement, negative = subsidence (mm, raw convention)
  x_s(i)    = InSAR cumulative displacement, negative = subsidence (mm, raw convention)
  dx_s(i)   = x_s(i) - x_s(i-1) = InSAR 5-day increment (mm)
  phi_k     = AR(1) memory coefficient at depth k
  beta_k    = proportional InSAR loading (analogous to f_median in static model)
  gamma_k   = elastic-vs-inelastic indicator (response to InSAR rate)

Estimated by OLS (no intercept -- zero-baseline convention).
Walk-forward validation: 4 folds with hold-out years 2022, 2023, 2024, 2025.
Baseline comparison: static direct ratio Y_hat_base = f_median_k * x_s(i).

Outputs written to:
  D:\\1000_SCRIPTS\\004_Project003\\20260427_InSAR_MLCW_v2\\arx_method7\\
"""

import numpy as np
import pandas as pd
from pathlib import Path
from scipy import linalg

# ─────────────── paths ───────────────
BASE   = Path(r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2")
MLCW   = BASE / "MLCW_5m_regular"
INSAR  = BASE / "InSAR_timeries" / "mlcw_interp_insar_IDW_extend.feather"
RATIO  = BASE / "direct_ratio_MLCW_InSAR"
OUTDIR = BASE / "arx_method7"
OUTDIR.mkdir(exist_ok=True)

DEPTHS_M   = list(range(0, 300, 5))  # 60 levels: 0, 5, 10, ..., 295
DEPTH_COLS = [f"depth_{d:03d}m" for d in DEPTHS_M]

# Walk-forward split dates (end of training for each fold)
FOLD_ENDS  = ["2021-11-30", "2022-11-30", "2023-11-30", "2024-11-30"]
FOLD_NAMES = ["2022", "2023", "2024", "2025"]


def load_insar(feather_path):
    """
    Return dict: station_name -> {"values": np.array, "dates": DatetimeIndex}.
    Values are negated so positive = compaction (matches MLCW convention).
    Epoch columns are named "D20XXXXXX" (D-prefix + YYYYMMDD).
    """
    df = pd.read_feather(feather_path)
    # Epoch columns have D-prefix: D20150121, D20150126, ...
    epoch_cols = [c for c in df.columns if str(c).startswith("D20")]
    if not epoch_cols:
        # Fallback: try plain date strings
        epoch_cols = [c for c in df.columns if str(c).startswith("20")]
    # Parse dates by stripping the leading "D"
    dates = pd.to_datetime([str(c).lstrip("D") for c in epoch_cols], format="%Y%m%d")
    # Station name column
    name_col = "Ename" if "Ename" in df.columns else "station"
    result = {}
    for _, row in df.iterrows():
        st = row[name_col]
        vals = row[epoch_cols].values.astype(float) * 1000.0   # m → mm
        # Raw feather: negative = subsidence. Keep raw convention (no negation).
        result[st] = {
            "values": vals,
            "dates":  dates,
        }
    return result


def load_mlcw(station, mlcw_dir):
    """
    Return (dates np.array, Y array shape (n_epochs, 60)) for station.
    Values are negated so positive = compaction. depth_300m excluded.
    """
    path = mlcw_dir / f"{station}_5m_grid.csv"
    df = pd.read_csv(path, parse_dates=["datetime"])
    df = df.set_index("datetime").sort_index()
    cols_present = [c for c in DEPTH_COLS if c in df.columns]
    Y = df[cols_present].values.astype(float)   # negative = subsidence (raw convention)
    dates = df.index.to_numpy()
    return dates, Y


def load_ratio_profile(station, ratio_dir):
    """Return f_median array of shape (60,) from direct_ratio_stats.csv."""
    path = ratio_dir / station / f"{station}_direct_ratio_stats.csv"
    df = pd.read_csv(path)
    return df["f_median"].values.astype(float)


def align_timeseries(insar_dates, insar_vals, mlcw_dates, mlcw_Y):
    """
    Align InSAR and MLCW to common dates (inner join).
    Returns (common_dates DatetimeIndex, x 1-D array, Y 2-D array (n, 60)).
    Returns (None, None, None) if fewer than 50 common dates.
    """
    insar_s = pd.Series(insar_vals, index=pd.DatetimeIndex(insar_dates))
    mlcw_df = pd.DataFrame(mlcw_Y, index=pd.DatetimeIndex(mlcw_dates))
    common = insar_s.index.intersection(mlcw_df.index)
    if len(common) < 50:
        return None, None, None
    x = insar_s.loc[common].values       # shape (n,)
    Y = mlcw_df.loc[common].values       # shape (n, 60)
    # Baseline-align to first common epoch so both series start at 0
    # (MLCW is cumulative from ~2003 install; InSAR from 2015-01-16)
    x = x - x[0]
    Y = Y - Y[0, :]
    return common, x, Y


def fit_arx_ols(Y_k, x, dx):
    """
    Fit Y_k(i) = phi*Y_k(i-1) + beta*x(i) + gamma*dx(i) by OLS.
    Y_k, x, dx: 1-D arrays of length n; uses observations i=1..n-1.
    Returns (phi, beta, gamma).
    """
    # Design matrix: rows for i = 1, ..., n-1
    A = np.column_stack([Y_k[:-1], x[1:], dx[1:]])   # (n-1, 3)
    b = Y_k[1:]
    params, _, _, _ = linalg.lstsq(A, b, check_finite=False)
    return params   # (phi, beta, gamma)


def predict_recursive(phi, beta, gamma, x_ho, dx_ho, Y0):
    """
    Multi-step recursive prediction over the hold-out window.
    phi, beta, gamma: scalar OLS coefficients
    x_ho, dx_ho: hold-out InSAR arrays (length n_pred)
    Y0: last observed MLCW value at end of training window (initial state)
    Returns Y_hat of length n_pred.
    """
    n_pred = len(x_ho)
    Y_hat = np.empty(n_pred)
    Y_prev = Y0
    for i in range(n_pred):
        Y_hat[i] = phi * Y_prev + beta * x_ho[i] + gamma * dx_ho[i]
        Y_prev = Y_hat[i]
    return Y_hat


def rmse(obs, pred):
    mask = np.isfinite(obs) & np.isfinite(pred)
    if mask.sum() < 3:
        return np.nan
    return np.sqrt(np.mean((obs[mask] - pred[mask]) ** 2))


def process_station(station, insar_data, mlcw_dir, ratio_dir):
    """Process one station. Returns result dict or None."""
    if station not in insar_data:
        print(f"  {station}: no InSAR data — skipping")
        return None

    try:
        mlcw_dates, mlcw_Y = load_mlcw(station, mlcw_dir)
    except FileNotFoundError:
        print(f"  {station}: MLCW file not found — skipping")
        return None

    common_dates, x, Y = align_timeseries(
        insar_data[station]["dates"],
        insar_data[station]["values"],
        mlcw_dates, mlcw_Y,
    )
    if common_dates is None:
        print(f"  {station}: insufficient overlap — skipping")
        return None

    try:
        f_median = load_ratio_profile(station, ratio_dir)
    except FileNotFoundError:
        f_median = np.zeros(60)

    # InSAR 5-day increment (dx[0] = 0 by construction)
    dx = np.concatenate([[0.0], np.diff(x)])

    n_epochs = len(common_dates)
    n_depths = Y.shape[1]

    # ── Walk-forward: 4 folds ──────────────────────────────────────────────────
    fold_rmse_arx  = np.full((n_depths, len(FOLD_ENDS)), np.nan)
    fold_rmse_base = np.full((n_depths, len(FOLD_ENDS)), np.nan)

    common_dt = pd.DatetimeIndex(common_dates)

    for fi, fold_end_str in enumerate(FOLD_ENDS):
        fold_end = pd.Timestamp(fold_end_str)
        train_mask = common_dt <= fold_end

        # Hold-out: from fold_end to next fold_end (or end of data)
        if fi + 1 < len(FOLD_ENDS):
            next_end = pd.Timestamp(FOLD_ENDS[fi + 1])
            ho_mask = (common_dt > fold_end) & (common_dt <= next_end)
        else:
            ho_mask = common_dt > fold_end

        n_train = train_mask.sum()
        n_ho    = ho_mask.sum()

        if n_train < 50 or n_ho < 5:
            continue

        x_train  = x[train_mask]
        dx_train = dx[train_mask]
        x_ho     = x[ho_mask]
        dx_ho    = dx[ho_mask]

        for k in range(n_depths):
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
            Y_hat_arx  = predict_recursive(phi_k, beta_k, gamma_k, x_ho, dx_ho, Y0)
            Y_hat_base = f_median[k] * x_ho

            fold_rmse_arx[k, fi]  = rmse(Y_k_ho, Y_hat_arx)
            fold_rmse_base[k, fi] = rmse(Y_k_ho, Y_hat_base)

    # ── Full fit (2015–2025) for production parameters ─────────────────────────
    full_params = np.full((n_depths, 3), np.nan)
    for k in range(n_depths):
        Y_k = Y[:, k]
        if not np.all(np.isfinite(Y_k)) or len(Y_k) < 4:
            continue
        try:
            params = fit_arx_ols(Y_k, x, dx)
        except Exception:
            continue
        full_params[k] = params

    return {
        "station":       station,
        "full_params":   full_params,        # (60, 3): phi, beta, gamma
        "fold_rmse_arx": fold_rmse_arx,      # (60, 4)
        "fold_rmse_base":fold_rmse_base,     # (60, 4)
        "f_median":      f_median,
    }


def write_station_outputs(res, outdir):
    station = res["station"]

    # 1. Parameter CSV (full 2015-2025 fit)
    df_params = pd.DataFrame({
        "depth_m": DEPTHS_M,
        "phi_k":   res["full_params"][:, 0],
        "beta_k":  res["full_params"][:, 1],
        "gamma_k": res["full_params"][:, 2],
    })
    df_params.to_csv(outdir / f"{station}_arx_params.csv", index=False)

    # 2. Walk-forward RMSE CSV
    rmse_arx  = res["fold_rmse_arx"]
    rmse_base = res["fold_rmse_base"]
    df_rmse = pd.DataFrame({"depth_m": DEPTHS_M})
    for fi, fn in enumerate(FOLD_NAMES):
        df_rmse[f"rmse_arx_{fn}"]  = rmse_arx[:, fi]
        df_rmse[f"rmse_base_{fn}"] = rmse_base[:, fi]
    df_rmse.to_csv(outdir / f"{station}_arx_walkforward_rmse.csv", index=False)


def main():
    print("Loading InSAR feather...")
    insar_data = load_insar(INSAR)
    print(f"  {len(insar_data)} stations in InSAR feather")

    stations = sorted([p.stem.replace("_5m_grid", "")
                       for p in MLCW.glob("*_5m_grid.csv")])
    print(f"  {len(stations)} MLCW stations found")

    all_results = []
    for station in stations:
        print(f"Processing {station}...")
        res = process_station(station, insar_data, MLCW, RATIO)
        if res is None:
            continue
        write_station_outputs(res, OUTDIR)
        phi_vals = res["full_params"][:, 0]
        print(f"  phi range: {np.nanmin(phi_vals):.3f} to {np.nanmax(phi_vals):.3f} "
              f"(median {np.nanmedian(phi_vals):.3f})")
        all_results.append(res)

    if not all_results:
        print("No results produced. Check data paths.")
        return

    # ── All-stations summary CSV ───────────────────────────────────────────────
    summary_rows = []
    for res in all_results:
        station   = res["station"]
        med_arx   = np.nanmedian(res["fold_rmse_arx"])
        med_base  = np.nanmedian(res["fold_rmse_base"])
        impr_pct  = 100.0 * (med_base - med_arx) / (med_base + 1e-9)
        # Fraction of (depth, fold) cells where ARX beats baseline
        arx_wins  = np.nanmean(res["fold_rmse_arx"] < res["fold_rmse_base"])
        med_phi   = np.nanmedian(res["full_params"][:, 0])
        summary_rows.append({
            "station":          station,
            "rmse_arx_med_mm":  round(float(med_arx), 4),
            "rmse_base_med_mm": round(float(med_base), 4),
            "impr_pct":         round(float(impr_pct), 2),
            "arx_wins_frac":    round(float(arx_wins), 3),
            "median_phi":       round(float(med_phi), 3),
            "arx_recommended":  bool((impr_pct > 1.0) and (arx_wins > 0.55)),
        })

    df_summary = pd.DataFrame(summary_rows).sort_values("impr_pct", ascending=False)
    df_summary.to_csv(OUTDIR / "arx_allstations_summary.csv", index=False)

    # ── NPZ stacked parameter arrays for spatial analysis ─────────────────────
    phi_stack   = np.stack([r["full_params"][:, 0] for r in all_results])
    beta_stack  = np.stack([r["full_params"][:, 1] for r in all_results])
    gamma_stack = np.stack([r["full_params"][:, 2] for r in all_results])
    np.savez(OUTDIR / "arx_allstations_params.npz",
             stations=np.array([r["station"] for r in all_results]),
             phi=phi_stack,
             beta=beta_stack,
             gamma=gamma_stack,
             depths=np.array(DEPTHS_M))

    # ── Console summary ────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("ARX walk-forward validation — all-stations summary")
    print("=" * 70)
    pd.set_option("display.max_rows", 50)
    print(df_summary[["station", "rmse_arx_med_mm", "rmse_base_med_mm",
                       "impr_pct", "median_phi", "arx_recommended"]].to_string(index=False))
    n_rec   = df_summary["arx_recommended"].sum()
    n_impr  = (df_summary["impr_pct"] > 0).sum()
    n_deg   = (df_summary["impr_pct"] < 0).sum()
    med_imp = df_summary["impr_pct"].median()
    print(f"\nStations recommended (ARX): {n_rec} / {len(df_summary)}")
    print(f"Median RMSE improvement:    {med_imp:.2f}%")
    print(f"Stations improved:          {n_impr} / {len(df_summary)}")
    print(f"Stations degraded:          {n_deg} / {len(df_summary)}")
    print(f"\nOutputs written to: {OUTDIR}")


if __name__ == "__main__":
    main()
