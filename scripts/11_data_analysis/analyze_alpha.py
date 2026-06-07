"""
Estimate the station-level alpha (α) coefficient from observed InSAR and MLCW data.

Physical meaning:
    α · x_i = y_i
    where x_i = InSAR cumulative surface displacement at epoch i (mm, positive = compaction)
          y_i = sum of observed MLCW compaction across all hydrogeological layers at epoch i (mm)
    α captures the fraction of surface displacement explained by the shallow aquifer column.

Why the cumulative domain:
    InSAR incremental noise (~4 mm/epoch) >> MLCW signal (~0.5 mm/epoch), so EIV attenuation
    is ~1.5% in the incremental domain.  In the cumulative domain the signal grows linearly
    while noise grows as sqrt(N), so SNR ∝ sqrt(N) and α becomes identifiable.

Estimator (OLS through origin on zero-referenced cumulative series):
    α_ols = dot(Y_cum, X_cum) / dot(X_cum, X_cum)

Usage:
    python scripts/11_data_analysis/analyze_alpha.py            # all 37 stations
    python scripts/11_data_analysis/analyze_alpha.py --station TUKU

Output: results/data_analysis/alpha_estimates.csv
        results/data_analysis/alpha_scatter_{STATION}.png  (one per station)
        results/data_analysis/alpha_barplot_all_stations.png
        results/data_analysis/alpha_ols_vs_existing.png
"""

import argparse
import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUT_DIR = PROJECT_ROOT / "figures" / "prestage_data_analysis"
OUT_DIR.mkdir(parents=True, exist_ok=True)

INSAR_FEATHER = PROJECT_ROOT / "data/insar/timeseries/mlcw_interp_insar_IDW_extend.feather"
MLCW_DIR      = PROJECT_ROOT / "data/mlcw/group_byLayer_reconstr"
ALPHA_CSV     = PROJECT_ROOT / "gis/alpha/alpha_comparison_all_stations_v3.csv"

# Calibration window for α fitting
CAL_START = pd.Timestamp("2015-01-01")
CAL_END   = pd.Timestamp("2021-12-31")

MERGE_TOL = pd.Timedelta("3d")  # critical: prevents post-shutdown MLCW freeze


def discover_stations():
    """Return sorted list of station names with a group_byLayer_reconstr CSV."""
    paths = sorted(MLCW_DIR.glob("*_reconst_grouped.csv"))
    return [p.stem.replace("_reconst_grouped", "") for p in paths]


def load_insar(insar_df, station):
    """Extract InSAR cumulative series for one station as a DataFrame (date, insar_mm)."""
    row = insar_df[insar_df["Ename"] == station]
    if row.empty:
        return None
    row = row.iloc[0]
    epoch_cols = [c for c in insar_df.columns if c.startswith("D")]
    dates = pd.to_datetime([c[1:] for c in epoch_cols])
    values_mm = row[epoch_cols].values.astype(float) * 1000.0  # metres → mm; positive = subsidence
    df = pd.DataFrame({"date": dates, "insar_mm": values_mm})
    return df.sort_values("date").reset_index(drop=True)


def load_mlcw(station):
    """Load MLCW grouped CSV, sum all layer columns → total cumulative compaction (mm)."""
    path = MLCW_DIR / f"{station}_reconst_grouped.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, parse_dates=["datetime"])
    df = df.rename(columns={"datetime": "date"})
    layer_cols = [c for c in df.columns if c != "date"]
    df["mlcw_mm"] = df[layer_cols].sum(axis=1)
    return df[["date", "mlcw_mm"]].sort_values("date").reset_index(drop=True)


def align_series(insar_df, mlcw_df):
    """
    Align MLCW to InSAR 5-day grid via merge_asof with 3-day tolerance.
    Returns merged DataFrame with columns: date, insar_mm, mlcw_mm.
    The tolerance=3d prevents post-shutdown freeze where merge_asof would
    propagate the last MLCW value forward, artificially depressing α.
    """
    merged = pd.merge_asof(
        insar_df.sort_values("date"),
        mlcw_df.sort_values("date"),
        on="date",
        direction="nearest",
        tolerance=MERGE_TOL,
    )
    return merged.dropna(subset=["insar_mm", "mlcw_mm"]).reset_index(drop=True)


def zero_reference(merged):
    """Subtract first overlapping epoch value from both series."""
    ref_insar = merged["insar_mm"].iloc[0]
    ref_mlcw  = merged["mlcw_mm"].iloc[0]
    merged = merged.copy()
    merged["insar_mm"] = merged["insar_mm"] - ref_insar
    merged["mlcw_mm"]  = merged["mlcw_mm"]  - ref_mlcw
    return merged


def fit_alpha(merged, cal_start=CAL_START, cal_end=CAL_END):
    """
    Fit α via OLS through origin in the cumulative domain, restricted to
    the calibration window.  Also compute epoch-by-epoch ratio statistics
    and diagnostic metrics.
    Returns a dict with all results.
    """
    cal = merged[(merged["date"] >= cal_start) & (merged["date"] <= cal_end)].copy()
    n = len(cal)
    if n < 10:
        return {"flag": "insufficient_overlap", "n_epochs": n}

    X = cal["insar_mm"].values
    Y = cal["mlcw_mm"].values

    denom = float(np.dot(X, X))
    if denom == 0:
        return {"flag": "zero_insar_variance", "n_epochs": n}

    alpha_ols = float(np.dot(Y, X) / denom)

    # R² of the OLS line
    Y_pred = alpha_ols * X
    ss_res = float(np.sum((Y - Y_pred) ** 2))
    ss_tot = float(np.sum((Y - Y.mean()) ** 2))
    r2 = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else np.nan
    rmse = float(np.sqrt(np.mean((Y - Y_pred) ** 2)))

    # Epoch-by-epoch ratio (avoid division by near-zero X)
    valid_ratio = np.abs(X) > 1.0   # only epochs where InSAR signal > 1 mm
    if valid_ratio.sum() >= 5:
        ratios = Y[valid_ratio] / X[valid_ratio]
        alpha_median = float(np.median(ratios))
        alpha_q25    = float(np.percentile(ratios, 25))
        alpha_q75    = float(np.percentile(ratios, 75))
    else:
        alpha_median = alpha_q25 = alpha_q75 = np.nan

    # Flag
    if alpha_ols <= 0:
        flag = "neg_alpha"
    elif alpha_ols > 1.0:
        flag = "alpha_gt_1"
    else:
        flag = "ok"

    return {
        "n_epochs":         n,
        "alpha_ols":        round(alpha_ols, 4),
        "alpha_median_ratio": round(alpha_median, 4) if not np.isnan(alpha_median) else None,
        "alpha_q25":        round(alpha_q25, 4) if not np.isnan(alpha_q25) else None,
        "alpha_q75":        round(alpha_q75, 4) if not np.isnan(alpha_q75) else None,
        "r2_ols":           round(r2, 4) if not np.isnan(r2) else None,
        "rmse_ols_mm":      round(rmse, 3),
        "flag":             flag,
    }


def plot_scatter(merged, station, alpha_ols, r2, out_path):
    """Cumulative scatter: InSAR (x) vs MLCW total (y), coloured by year.

    Plotted points are thinned to monthly cadence (first epoch of each month)
    for readability; the α fit is computed on the full dataset upstream.
    """
    fig, ax = plt.subplots(figsize=(7, 5))

    # Thin to monthly: keep first available epoch in each calendar month
    plot_df = merged.set_index("date").resample("MS").first().reset_index()
    plot_df = plot_df.dropna(subset=["insar_mm", "mlcw_mm"])

    years = plot_df["date"].dt.year.values
    norm  = plt.Normalize(2015, 2026)
    cmap  = cm.viridis

    # Hollow markers: omit c= to avoid fill-override conflict; use edgecolors only.
    # Colorbar is built from a ScalarMappable so it does not require the PathCollection.
    ax.scatter(
        plot_df["insar_mm"], plot_df["mlcw_mm"],
        s=20,
        facecolors="none",
        edgecolors=cmap(norm(years)),
        linewidths=0.8,
        zorder=2,
    )
    sm = cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cb = plt.colorbar(sm, ax=ax, label="Year")
    cb.set_ticks(range(2015, 2027))
    cb.set_ticklabels([str(y) for y in range(2015, 2027)])

    # OLS line (use full merged extent for the line, not just monthly points)
    x_range = np.array([merged["insar_mm"].min(), merged["insar_mm"].max()])
    ax.plot(x_range, alpha_ols * x_range, color="red", linewidth=1.5,
            label=f"α = {alpha_ols:.3f}  (R² = {r2:.3f})")
    ax.axhline(0, color="grey", linewidth=0.5)
    ax.axvline(0, color="grey", linewidth=0.5)

    ax.set_xlabel("Cumulative InSAR displacement (mm, zero-referenced)", fontsize=10)
    ax.set_ylabel("Cumulative MLCW total compaction (mm, zero-referenced)", fontsize=10)
    ax.set_title(f"{station} — α estimation: InSAR vs MLCW total compaction", fontsize=11)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_barplot(rows, out_path):
    """Bar chart of α_ols per station with Q25–Q75 error bars."""
    df = pd.DataFrame(rows).dropna(subset=["alpha_ols"])
    df = df.sort_values("alpha_ols").reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(14, 5))

    x = np.arange(len(df))
    colors = ["#d62728" if f != "ok" else "#1f77b4" for f in df["flag"]]
    ax.bar(x, df["alpha_ols"], color=colors, alpha=0.8, zorder=2)

    # Error bars from Q25/Q75
    q25 = df["alpha_q25"].fillna(df["alpha_ols"])
    q75 = df["alpha_q75"].fillna(df["alpha_ols"])
    yerr_low  = (df["alpha_ols"] - q25).clip(lower=0)
    yerr_high = (q75 - df["alpha_ols"]).clip(lower=0)
    ax.errorbar(x, df["alpha_ols"],
                yerr=[yerr_low, yerr_high],
                fmt="none", color="black", linewidth=0.8, capsize=3, zorder=3)

    # Reference lines from existing α
    if "alpha_existing_gnss" in df.columns:
        for i, row in df.iterrows():
            if pd.notna(row.get("alpha_existing_gnss")):
                ax.scatter(i, row["alpha_existing_gnss"], marker="^", color="orange",
                           s=25, zorder=4)
    if "alpha_existing_insar" in df.columns:
        for i, row in df.iterrows():
            if pd.notna(row.get("alpha_existing_insar")):
                ax.scatter(i, row["alpha_existing_insar"], marker="s", color="green",
                           s=25, zorder=4)

    ax.set_xticks(x)
    ax.set_xticklabels(df["station"], rotation=45, ha="right", fontsize=7)
    ax.set_ylabel("α (InSAR-to-MLCW fraction)", fontsize=10)
    ax.set_title("Station-level α estimates — OLS (blue=ok, red=flagged)\n"
                 "Error bars: Q25–Q75 of epoch-by-epoch ratio  "
                 "△ = existing GNSS-derived α  □ = existing InSAR-derived α", fontsize=9)
    ax.axhline(1.0, color="black", linewidth=0.8, linestyle="--", alpha=0.5)
    ax.set_ylim(bottom=0)
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_ols_vs_existing(rows, out_path):
    """Scatter: α_ols (y) vs α_existing_gnss (x) with 1:1 line."""
    df = pd.DataFrame(rows).dropna(subset=["alpha_ols", "alpha_existing_gnss"])
    if df.empty:
        return

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(df["alpha_existing_gnss"], df["alpha_ols"], s=40, alpha=0.8, zorder=2)

    # Label each point
    for _, row in df.iterrows():
        ax.annotate(row["station"], (row["alpha_existing_gnss"], row["alpha_ols"]),
                    fontsize=6, xytext=(3, 3), textcoords="offset points")

    # 1:1 line
    lim = [
        min(df["alpha_existing_gnss"].min(), df["alpha_ols"].min()) - 0.05,
        max(df["alpha_existing_gnss"].max(), df["alpha_ols"].max()) + 0.05,
    ]
    ax.plot(lim, lim, color="grey", linewidth=1.0, linestyle="--", label="1:1 line")
    ax.set_xlim(lim)
    ax.set_ylim(lim)

    ax.set_xlabel("α_existing_gnss (from velocity ratio)", fontsize=10)
    ax.set_ylabel("α_ols (from InSAR × MLCW cumulative)", fontsize=10)
    ax.set_title("Cross-check: OLS-derived α vs GNSS-derived α", fontsize=11)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def process_station(station, insar_df, alpha_existing_df):
    """Full pipeline for one station. Returns result dict."""
    insar_s = load_insar(insar_df, station)
    mlcw_s  = load_mlcw(station)

    result = {"station": station}

    # Merge existing α for cross-check
    ex = alpha_existing_df[alpha_existing_df["Ename"] == station]
    result["alpha_existing_gnss"]  = float(ex["alpha_gnss"].iloc[0])  if not ex.empty and pd.notna(ex["alpha_gnss"].iloc[0])  else None
    result["alpha_existing_insar"] = float(ex["alpha_insar"].iloc[0]) if not ex.empty and pd.notna(ex["alpha_insar"].iloc[0]) else None

    if insar_s is None:
        result.update({"flag": "no_insar", "n_epochs": 0})
        return result, None
    if mlcw_s is None:
        result.update({"flag": "no_mlcw", "n_epochs": 0})
        return result, None

    merged = align_series(insar_s, mlcw_s)
    if len(merged) < 10:
        result.update({"flag": "insufficient_overlap", "n_epochs": len(merged)})
        return result, None

    merged = zero_reference(merged)
    fit = fit_alpha(merged)
    result.update(fit)

    return result, merged


def main():
    parser = argparse.ArgumentParser(description="Estimate α from InSAR + MLCW data")
    parser.add_argument("--station", default=None,
                        help="Single station name (e.g. TUKU). Omit to process all.")
    args = parser.parse_args()

    # Load shared data once
    print("Loading InSAR feather ...")
    insar_df = pd.read_feather(INSAR_FEATHER)

    print("Loading existing α CSV ...")
    alpha_existing_df = pd.read_csv(ALPHA_CSV) if ALPHA_CSV.exists() else pd.DataFrame()

    stations = [args.station] if args.station else discover_stations()
    print(f"Processing {len(stations)} station(s) ...")

    all_results = []
    all_merged  = {}   # station → merged df (for plots)

    for station in stations:
        result, merged = process_station(station, insar_df, alpha_existing_df)
        all_results.append(result)
        if merged is not None:
            all_merged[station] = merged

        flag = result.get("flag", "?")
        alpha_val = result.get("alpha_ols", "n/a")
        r2_val    = result.get("r2_ols", "n/a")
        print(f"  {station:20s}  flag={flag:25s}  α_ols={alpha_val}  R²={r2_val}")

        # Per-station scatter plot
        if merged is not None and result.get("alpha_ols") is not None:
            scatter_path = OUT_DIR / f"alpha_scatter_{station}.png"
            plot_scatter(merged, station,
                         result["alpha_ols"], result.get("r2_ols", 0.0),
                         scatter_path)

    # Save CSV
    csv_path = OUT_DIR / "alpha_estimates.csv"
    col_order = [
        "station", "n_epochs", "alpha_ols", "alpha_median_ratio",
        "alpha_q25", "alpha_q75", "r2_ols", "rmse_ols_mm",
        "alpha_existing_gnss", "alpha_existing_insar", "flag",
    ]
    results_df = pd.DataFrame(all_results)
    for col in col_order:
        if col not in results_df.columns:
            results_df[col] = None
    results_df = results_df[col_order]
    results_df.to_csv(csv_path, index=False)
    print(f"\nSaved: {csv_path}  ({len(results_df)} rows)")

    # Summary table
    ok_rows = results_df[results_df["flag"] == "ok"]
    if not ok_rows.empty:
        print(f"\n--- α summary (flag=ok, n={len(ok_rows)}) ---")
        print(ok_rows[["station", "alpha_ols", "r2_ols", "alpha_existing_gnss"]].to_string(index=False))

    # Multi-station figures (only when processing all stations)
    if len(stations) > 1 and len(all_results) > 1:
        barplot_path = OUT_DIR / "alpha_barplot_all_stations.png"
        plot_barplot(all_results, barplot_path)
        print(f"Saved: {barplot_path}")

        crosscheck_path = OUT_DIR / "alpha_ols_vs_existing.png"
        plot_ols_vs_existing(all_results, crosscheck_path)
        print(f"Saved: {crosscheck_path}")

    print("\nDone.")


if __name__ == "__main__":
    main()
