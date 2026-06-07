"""
ring_cross_correlation.py — Cross-correlation matrix between magnetic ring timeseries.

For each station, analyzes three data sources independently:
  - raw_timeseries/  : original monthly ring observations
  - detrended/       : 5-day modeled periodic signal (no trend, no jumps)
  - grouped/         : layer-aggregated monthly data (F1/T1/F2/T2/F3/F4)

All series are linearly detrended before computing Pearson r with pairwise
complete observations.  Outputs per station:
  - JSON with correlation matrix + extensive metrics
  - PNG heatmap (symmetric, inverted Y-axis, diverging colourmap)

Usage
-----
  # TUKU pilot
  PYTHONPATH="" conda run -n isce_ncu3 python scripts/11_data_analysis/ring_cross_correlation.py --station TUKU

  # Full batch (all stations)
  PYTHONPATH="" conda run -n isce_ncu3 python scripts/11_data_analysis/ring_cross_correlation.py
"""

import argparse
import json
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import numpy as np
import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _SCRIPT_DIR.parent.parent

DATA_DIR   = PROJECT_ROOT / "data" / "mlcw"
RESULTS_DIR = PROJECT_ROOT / "results" / "ring_cross_correlation"
FIGURES_DIR = PROJECT_ROOT / "figures" / "ring_cross_correlation"

CM = 1 / 2.54  # centimetre → inch
MAX_LAG = 12  # max lag steps for lagged CCF (grouped data)

# ── Data source definitions ───────────────────────────────────────────────────
SOURCES = {
    "raw_timeseries": {
        "key": "raw_timeseries",
        "label": "Raw Timeseries",
        "csv_dir": DATA_DIR / "raw_timeseries",
        "csv_pattern": "{station}_ringbyring.csv",
        "col_kind": "ring_depths",
    },
    "detrended": {
        "key": "detrended",
        "label": "Detrended (Seasonal Only)",
        "csv_dir": DATA_DIR / "modeled_nojump" / "detrended",
        "csv_pattern": "{station}_ringbyring.csv",
        "col_kind": "ring_depths",
    },
    "grouped": {
        "key": "grouped",
        "label": "Layer-Reconstructed (Grouped)",
        "csv_dir": DATA_DIR / "group_byLayer_reconstr",
        "csv_pattern": "{station}_reconst_grouped.csv",
        "col_kind": "layer_names",
    },
}

# ── Plot style ────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 12,
    "axes.labelsize": 14,
    "axes.titlesize": 14,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.1,
})


# ── Utility ───────────────────────────────────────────────────────────────────

def _style_ax(ax):
    """Apply consistent axis styling."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, linestyle="--", alpha=0.3, color="gray")
    ax.tick_params(direction="in")


def _format_depth_label(depth_str: str) -> str:
    """Format a ring depth string for display (e.g. '8.775' → '8.8 m')."""
    try:
        val = float(depth_str)
        return f"{val:.1f} m"
    except ValueError:
        return depth_str


# ── Core functions ────────────────────────────────────────────────────────────

def linear_detrend(y: np.ndarray) -> np.ndarray:
    """Remove least-squares linear trend from y.

    Operates on non-NaN indices only, then applies the same trend to
    the full-length array (NaN gaps keep their position).
    """
    t = np.arange(len(y), dtype=float)
    mask = ~np.isnan(y)
    n_valid = mask.sum()
    if n_valid < 3:
        return y.copy()  # too few points to fit
    A = np.column_stack([np.ones(len(y)), t])
    theta, _, _, _ = np.linalg.lstsq(A[mask], y[mask], rcond=None)
    trend = A @ theta
    return y - trend


def load_csv_data(csv_path: Path, col_kind: str):
    """Load a station CSV and identify value columns.

    Parameters
    ----------
    csv_path : Path
        Full path to the CSV.
    col_kind : str
        ``"ring_depths"`` — columns whose header parses as a float (sorted by depth).
        ``"layer_names"`` — all non-datetime columns kept in file order.

    Returns
    -------
    df : pd.DataFrame
        Parsed DataFrame with DatetimeIndex.
    col_headers : list of str
        Column header strings for DataFrame access.
    col_labels : list of str
        Human-readable labels for display.
    col_values : list of float or None
        Numerical depth values for proportional axis scaling.
        ``None`` for ``layer_names`` (resolved later from classify table).
    """
    df = pd.read_csv(csv_path, parse_dates=[0], index_col=0)
    df.index.name = "datetime"

    if col_kind == "ring_depths":
        candidates = []
        for col in df.columns:
            try:
                val = float(col)
                candidates.append((val, col))
            except (ValueError, TypeError):
                continue
        candidates.sort(key=lambda x: x[0])  # ascending depth
        col_headers = [c[1] for c in candidates]
        col_labels = [_format_depth_label(c[1]) for c in candidates]
        col_values = [c[0] for c in candidates]  # float depths for pcolormesh
    elif col_kind == "layer_names":
        col_headers = list(df.columns)
        col_labels = list(df.columns)
        col_values = None  # resolved later via classify table
    else:
        raise ValueError(f"Unknown col_kind: {col_kind}")

    return df, col_headers, col_labels, col_values


def _get_layer_median_depths(station: str) -> list:
    """Return median ring depth per layer from the classify table.

    The returned list is in layer order (F1, T1, F2, T2, F3, F4) matching
    the column order of the grouped CSV.
    """
    classify_path = DATA_DIR / "group_byLayer_modeled" / f"{station}_classify_table.csv"
    try:
        ct = pd.read_csv(classify_path)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        print(f"    [WARN] classify table not found: {classify_path}")
        return None

    # Map each layer to median depth of its rings
    layer_order = ["F1", "T1", "F2", "T2", "F3", "F4"]
    median_depths = ct.groupby("layer")["depth"].median()
    depths = [float(median_depths.get(l, np.nan)) for l in layer_order]
    # Filter out NaN — keep only layers present
    result = []
    for l, d in zip(layer_order, depths):
        if not np.isnan(d):
            result.append(d)
    return result if result else None


def compute_correlation_matrix(df_detrended: pd.DataFrame, col_headers: list):
    """Compute Pearson correlation matrix with pairwise complete observations.

    Returns
    -------
    corr_matrix : np.ndarray (N x N)
        Pearson r values.  NaN where < 3 valid pairs.
    n_valid_matrix : np.ndarray (N x N, int)
        Number of valid (non-NaN) observation pairs for each entry.
    """
    N = len(col_headers)
    corr_matrix = np.ones((N, N))  # diagonal → 1.0
    n_valid_matrix = np.zeros((N, N), dtype=int)

    for i in range(N):
        for j in range(i + 1, N):
            a = df_detrended[col_headers[i]].values.astype(float)
            b = df_detrended[col_headers[j]].values.astype(float)
            mask = ~np.isnan(a) & ~np.isnan(b)
            nv = mask.sum()
            n_valid_matrix[i, j] = nv
            n_valid_matrix[j, i] = nv

            if nv < 3:
                corr_matrix[i, j] = np.nan
                corr_matrix[j, i] = np.nan
            else:
                r = float(np.corrcoef(a[mask], b[mask])[0, 1])
                corr_matrix[i, j] = r
                corr_matrix[j, i] = r

    np.fill_diagonal(corr_matrix, 1.0)
    np.fill_diagonal(n_valid_matrix, len(df_detrended))

    return corr_matrix, n_valid_matrix


def compute_lagged_ccf_matrices(df_detrended, col_headers, max_lag=MAX_LAG,
                                 min_common=20):
    """Compute maximum positive Pearson r and optimal lag for every pair.

    For each pair (i, j), shifts column i relative to column j over
    τ ∈ [-max_lag, +max_lag] and finds the lag that maximises positive r.

    Returns
    -------
    r_max_matrix : np.ndarray (N x N)
        Maximum positive r for each pair.  Stored symmetrically; 0⋅0 where
        no positive correlation exists.  Diagonal = 1⋅0.
    tau_matrix : np.ndarray (N x N, float)
        Lag τ (in time steps) at which the max positive r occurs.
        Upper-triangle entries (i < j) store the lag of i *leading* j;
        lower-triangle entries store the negative mirror.
        Diagonal = 0.
    """
    N = len(col_headers)
    r_max_matrix = np.zeros((N, N))
    tau_matrix = np.zeros((N, N), dtype=float)

    for i in range(N):
        r_max_matrix[i, i] = 1.0
        tau_matrix[i, i] = 0.0

        for j in range(i + 1, N):
            a = df_detrended[col_headers[i]].values.astype(float)
            b = df_detrended[col_headers[j]].values.astype(float)

            best_r = -2.0
            best_tau = 0

            for tau in range(-max_lag, max_lag + 1):
                if tau >= 0:
                    a_s = a[tau:]
                    b_s = b[:len(b) - tau]
                else:
                    t = -tau
                    a_s = a[:len(a) - t]
                    b_s = b[t:]

                mask = ~np.isnan(a_s) & ~np.isnan(b_s)
                nv = mask.sum()
                if nv < min_common:
                    continue
                r = float(np.corrcoef(a_s[mask], b_s[mask])[0, 1])
                if r > best_r:
                    best_r = r
                    best_tau = tau

            if best_r > 0:
                r_max_matrix[i, j] = best_r
                r_max_matrix[j, i] = best_r
                tau_matrix[i, j] = best_tau   # i leads j by this many steps
                tau_matrix[j, i] = -best_tau  # j lags i

    return r_max_matrix, tau_matrix


def compute_matrix_metrics(corr_matrix, n_valid_matrix, col_labels,
                           source_config, station, n_total):
    """Compute extensive evaluation metrics from a correlation matrix.

    Returns a JSON-serializable dict.
    """
    N = len(col_labels)
    src_key = source_config["key"]
    src_label = source_config["label"]

    # Eigenvalues  (handle NaN by replacing with identity-guaranteeing values)
    corr_filled = np.where(np.isnan(corr_matrix), 0.0, corr_matrix)
    np.fill_diagonal(corr_filled, 1.0)
    eigenvalues = np.linalg.eigvalsh(corr_filled)[::-1]  # descending
    evalues_list = [float(v) for v in eigenvalues]

    # Condition number
    if len(evalues_list) == 1:
        condition_number = 1.0
    elif eigenvalues[-1] < 1e-12:
        condition_number = "inf"
    else:
        condition_number = float(eigenvalues[0] / eigenvalues[-1])

    # Variance fractions
    total_variance = float(np.sum(eigenvalues)) if eigenvalues.sum() > 0 else 1.0
    variance_fractions = [float(v / total_variance) for v in eigenvalues]
    variance_explained_pc1 = variance_fractions[0] if variance_fractions else 0.0

    # Effective rank
    effective_rank = int(np.sum(eigenvalues > 0.01))

    # Off-diagonal statistics
    off_diag = []
    off_diag_valid = []
    nan_pairs = []
    min_pair = {}
    max_pair = {}

    for i in range(N):
        for j in range(i + 1, N):
            r = corr_matrix[i, j]
            nv = n_valid_matrix[i, j]
            if np.isnan(r):
                nan_pairs.append({
                    "col_i": col_labels[i],
                    "col_j": col_labels[j],
                    "n_valid": int(nv),
                })
            else:
                off_diag.append(r)
                off_diag_valid.append({
                    "value": float(r),
                    "col_i": col_labels[i],
                    "col_j": col_labels[j],
                })

    mean_abs_off_diag = float(np.mean(np.abs(off_diag))) if off_diag else None

    if off_diag_valid:
        min_item = min(off_diag_valid, key=lambda x: x["value"])
        max_item = max(off_diag_valid, key=lambda x: x["value"])
    else:
        min_item = None
        max_item = None

    # Pair thresholds
    n_pairs = len(off_diag)
    gt_07 = sum(1 for v in off_diag if abs(v) > 0.7)
    gt_08 = sum(1 for v in off_diag if abs(v) > 0.8)
    gt_09 = sum(1 for v in off_diag if abs(v) > 0.9)

    # NaN handling notes
    if nan_pairs:
        reasons = []
        for p in nan_pairs[:3]:
            reasons.append(
                f"{p['col_i']}–{p['col_j']} ({p['n_valid']} valid obs)"
            )
        nan_notes = (
            f"{len(nan_pairs)} pairs with < 3 valid observations. "
            f"Examples: {'; '.join(reasons)}."
        )
    else:
        nan_notes = "All pairs had >= 3 valid observations."

    # Check for constant columns
    constant_cols = []
    for idx, val in enumerate(evalues_list):
        if idx == 0:
            continue
        # A constant column gives eigenvalue near 0; check if any eigenvalue
        # is effectively machine-zero
    # More direct: check if std is near zero per column
    # (we already filled NaN, so this is approximate)

    return {
        "data_source": src_key,
        "data_label": src_label,
        "station": station,
        "n_columns": N,
        "column_labels": col_labels,
        "correlation_matrix": corr_matrix.tolist(),
        "n_valid_observations_per_pair": n_valid_matrix.tolist(),
        "eigenvalues": evalues_list,
        "condition_number": condition_number,
        "mean_abs_off_diagonal": mean_abs_off_diag,
        "min_off_diagonal": min_item,
        "max_off_diagonal": max_item,
        "pairs_abs_gt_07_count": gt_07,
        "pairs_abs_gt_08_count": gt_08,
        "pairs_abs_gt_09_count": gt_09,
        "pairs_abs_gt_07_fraction": round(gt_07 / n_pairs, 6) if n_pairs > 0 else None,
        "pairs_abs_gt_08_fraction": round(gt_08 / n_pairs, 6) if n_pairs > 0 else None,
        "pairs_abs_gt_09_fraction": round(gt_09 / n_pairs, 6) if n_pairs > 0 else None,
        "variance_explained_pc1": float(variance_explained_pc1),
        "variance_fractions": variance_fractions,
        "effective_rank": effective_rank,
        "nan_pairs_details": nan_pairs,
        "nan_handling_notes": nan_notes,
        "n_observations_total": n_total,
    }


# ── Custom colourmap ──────────────────────────────────────────────────────────

# ── Visualisation ─────────────────────────────────────────────────────────────

def _build_grid_edges(values):
    """Build pcolormesh grid edges at midpoints between adjacent depth values.

    For N data values, returns N+1 edge positions such that each data value
    sits at the centre of its cell.
    """
    vals = np.asarray(values, dtype=float)
    N = len(vals)
    if N < 2:
        # Single value — artificially pad
        half = 1.0
        return np.array([vals[0] - half, vals[0] + half])
    edges = np.empty(N + 1)
    edges[0] = vals[0] - (vals[1] - vals[0]) / 2.0
    edges[1:-1] = (vals[:-1] + vals[1:]) / 2.0
    edges[-1] = vals[-1] + (vals[-1] - vals[-2]) / 2.0
    return edges


def plot_heatmap(corr_matrix, col_labels, col_values, station_name, data_label,
                 output_path, source_key=None):
    """Generate a symmetric correlation matrix heatmap with proportional depth spacing.

    Uses ``pcolormesh`` so that cell sizes reflect the physical spacing between
    ring depths (or layer median depths).  Axes are scaled continuously by the
    actual depth values, with the shallowest ring at top-left.

    Parameters
    ----------
    corr_matrix : np.ndarray (N x N)
        Pearson correlation matrix.
    col_labels : list of str
        Human-readable labels (e.g. ``"8.8 m"``, ``"F1"``).
    col_values : list of float
        Numerical depth values for proportional axis scaling.
    station_name : str
    data_label : str
    output_path : Path
    source_key : str or None
        Used for grouped data to apply ``imshow`` fallback (categorical axes).
    """
    N = corr_matrix.shape[0]

    # ── Decide plot method ────────────────────────────────────────────────
    use_pcolormesh = (col_values is not None and N > 1)

    fig, ax = plt.subplots(figsize=(18 * CM, 18 * CM))

    if use_pcolormesh:
        # Mask upper triangle (symmetric matrix — no need to show both halves)
        mask_upper = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
        masked_corr = np.ma.array(corr_matrix, mask=mask_upper)

        # Proportional spacing via pcolormesh
        edges = _build_grid_edges(col_values)
        im = ax.pcolormesh(
            edges, edges, masked_corr,
            cmap=plt.cm.turbo_r, vmin=-1.0, vmax=1.0,
        )
        # Shallowest (smallest depth) at top
        ax.invert_yaxis()
        # Set ticks at data-point positions (not edges)
        ax.set_xticks(col_values)
        ax.set_yticks(col_values)
    else:
        # Fallback — uniform cells (single ring or grouped without depths)
        im = ax.imshow(
            corr_matrix,
            cmap=plt.cm.turbo_r, vmin=-1.0, vmax=1.0,
            interpolation="nearest", origin="upper", aspect="equal",
        )
        ax.invert_yaxis()
        ax.set_xticks(range(N))
        ax.set_yticks(range(N))

    # ── Tick labels ───────────────────────────────────────────────────────
    fontsize_labels = 9 if N > 20 else 10 if N > 8 else 11

    # Bottom x-axis labels
    ax.set_xticklabels(col_labels, rotation=90, fontsize=fontsize_labels)

    # Y-axis labels (left side only)
    ax.set_yticklabels(col_labels, fontsize=fontsize_labels)

    # ── Axis styling ──────────────────────────────────────────────────────
    ax.tick_params(direction="out", top=False, right=False)
    for spine_name in ["top", "right", "left", "bottom"]:
        ax.spines[spine_name].set_visible(True)
        ax.spines[spine_name].set_linewidth(0.5)

    # ── Colourbar ─────────────────────────────────────────────────────────
    cbar = fig.colorbar(
        im, ax=ax, shrink=0.82, pad=0.02,
        ticks=[-1.0, -0.5, 0.0, 0.5, 1.0],
    )
    cbar.set_label("Pearson r", fontsize=13)
    cbar.ax.tick_params(labelsize=10)

    # ── Title ─────────────────────────────────────────────────────────────
    ax.set_title(
        f"{station_name} — {data_label}\nRing Cross-Correlation Matrix",
        fontsize=15, fontweight="bold", pad=15,
    )

    # ── Save ──────────────────────────────────────────────────────────────
    os.makedirs(output_path.parent, exist_ok=True)
    fig.savefig(
        output_path, dpi=300, bbox_inches="tight",
        facecolor="w", edgecolor="w",
    )
    plt.close(fig)


# ── Split heatmap (lagged CCF) ───────────────────────────────────────────────

def plot_split_heatmap(r_max_matrix, tau_matrix, col_labels, col_values,
                       station_name, max_lag, output_path):
    """Split-triangle heatmap: lower = max positive r, upper = optimal lag.

    Lower triangle uses ``Reds`` colormap (0 → 1) for the maximum positive
    Pearson correlation.  Upper triangle uses ``YlOrBr`` (0 → max_lag) for
    the lag in time steps at which that maximum occurs.
    """
    N = r_max_matrix.shape[0]
    use_pcolormesh = (col_values is not None and N > 1)

    fig, ax = plt.subplots(figsize=(18 * CM, 18 * CM))

    # ── Build grid edges ───────────────────────────────────────────────────
    if use_pcolormesh:
        edges = _build_grid_edges(col_values)
        # -- Lower triangle: max positive r (Reds) --
        mask_upper_r = np.triu(np.ones_like(r_max_matrix, dtype=bool), k=1)
        r_masked = np.ma.array(r_max_matrix, mask=mask_upper_r)
        im_r = ax.pcolormesh(edges, edges, r_masked, cmap='Reds',
                              vmin=0.0, vmax=1.0, linewidth=0, alpha=1.0)

        # -- Upper triangle: lag in steps (Blues) --
        tau_display = np.abs(tau_matrix).astype(float)
        mask_lower_t = np.tril(np.ones_like(tau_display, dtype=bool), k=0)
        tau_masked = np.ma.array(tau_display, mask=mask_lower_t)
        im_t = ax.pcolormesh(edges, edges, tau_masked, cmap='Blues',
                              vmin=0, vmax=max_lag, linewidth=0, alpha=1.0)

        ax.invert_yaxis()
        ax.set_xticks(col_values)
        ax.set_yticks(col_values)
    else:
        # Fallback uniform cells
        ax.imshow(r_max_matrix, cmap='Reds', vmin=0, vmax=1,
                  interpolation='nearest', origin='upper', aspect='equal')
        ax.invert_yaxis()
        ax.set_xticks(range(N))
        ax.set_yticks(range(N))

    # ── Tick labels ────────────────────────────────────────────────────────
    fontsize_labels = 10 if N <= 8 else 9
    ax.set_xticklabels(col_labels, rotation=90, fontsize=fontsize_labels)
    ax.set_yticklabels(col_labels, fontsize=fontsize_labels)
    ax.tick_params(direction="out", top=False, right=False)
    for spine_name in ["top", "right", "left", "bottom"]:
        ax.spines[spine_name].set_visible(True)
        ax.spines[spine_name].set_linewidth(0.5)

    # ── Colorbar 1: Reds (max r) ───────────────────────────────────────────
    # Positioned on the right, slightly inset from upper-triangle area
    cax1 = ax.inset_axes([1.04, 0.55, 0.03, 0.40], transform=ax.transAxes)
    cbar_r = fig.colorbar(im_r, cax=cax1,
                           ticks=[0.0, 0.25, 0.50, 0.75, 1.0])
    cbar_r.set_label("Max positive $r$", fontsize=13)
    cbar_r.ax.tick_params(labelsize=10)

    # ── Colorbar 2: Blues (lag) ────────────────────────────────────────────
    cax2 = ax.inset_axes([1.04, 0.05, 0.03, 0.40], transform=ax.transAxes)
    tick_step = max(1, max_lag // 4)
    cbar_t = fig.colorbar(im_t, cax=cax2,
                           ticks=list(range(0, max_lag + 1, tick_step)))
    cbar_t.set_label("Optimal lag $\\tau$ (months)", fontsize=13)
    cbar_t.ax.tick_params(labelsize=10)

    # ── Title ──────────────────────────────────────────────────────────────
    ax.set_title(
        f"{station_name} — Lagged Cross-Correlation\n"
        f"Lower: max positive $r$  |  Upper: optimal lag $\\tau$",
        fontsize=15, fontweight="bold", pad=15,
    )

    # ── Save ───────────────────────────────────────────────────────────────
    os.makedirs(output_path.parent, exist_ok=True)
    fig.savefig(
        output_path, dpi=300, bbox_inches="tight",
        facecolor="w", edgecolor="w",
    )
    plt.close(fig)


# ── Station processing ────────────────────────────────────────────────────────

def process_station(station, source_key, source_config):
    """Full pipeline for one station × one data source.

    Returns the metrics dict, or None if the source file is missing.
    """
    csv_path = (
        source_config["csv_dir"]
        / source_config["csv_pattern"].format(station=station)
    )

    if not csv_path.is_file():
        print(f"  [SKIP] {source_key}: {csv_path.name} not found")
        return None

    print(f"  [{source_key}] loading {csv_path.name} ...", end="")
    try:
        df, col_headers, col_labels, col_values = load_csv_data(
            csv_path, source_config["col_kind"]
        )
    except Exception as e:
        print(f" FAILED: {e}")
        return None

    if len(col_headers) == 0:
        print(" no value columns found → skip")
        return None

    # Resolve depth values for grouped/layer data
    if col_values is None and source_config["col_kind"] == "layer_names":
        col_values = _get_layer_median_depths(station)
        if col_values is not None and len(col_values) == len(col_headers):
            print(f" (depths from classify table)")
        else:
            col_values = None  # fall back to uniform cells

    n_total = len(df)
    N = len(col_headers)
    print(f" {N} columns, {n_total} rows")

    # 1. Linear detrend each column independently
    print(f"  [{source_key}] detrending ...", end="")
    df_detrended = pd.DataFrame(index=df.index)
    for hdr in col_headers:
        df_detrended[hdr] = linear_detrend(df[hdr].values)
    print(" done")

    # 2. Correlation matrix (pairwise complete)
    is_grouped = (source_config["col_kind"] == "layer_names")

    if is_grouped:
        print(f"  [{source_key}] computing lagged cross-correlation (max_lag={MAX_LAG}) ...", end="")
        r_max_matrix, tau_matrix = compute_lagged_ccf_matrices(
            df_detrended, col_headers, max_lag=MAX_LAG,
        )
        print(" done")

        # Zero-lag matrix for standard metrics (for backward compat)
        corr_matrix, n_valid_matrix = compute_correlation_matrix(df_detrended, col_headers)
    else:
        print(f"  [{source_key}] computing correlation matrix ...", end="")
        corr_matrix, n_valid_matrix = compute_correlation_matrix(df_detrended, col_headers)
        print(" done")

    # 3. Metrics
    print(f"  [{source_key}] computing metrics ...", end="")
    metrics = compute_matrix_metrics(
        corr_matrix, n_valid_matrix, col_labels,
        source_config, station, n_total,
    )
    if is_grouped:
        # Add lagged CCF data and a summary
        metrics["r_max_matrix"] = r_max_matrix.tolist()
        metrics["tau_matrix"] = tau_matrix.tolist()
        metrics["max_lag"] = MAX_LAG
        # Summarise interesting lags
        lag_summary = []
        for i in range(N):
            for j in range(i + 1, N):
                r_val = r_max_matrix[i, j]
                t_val = tau_matrix[i, j]
                if r_val > 0:
                    lag_summary.append({
                        "col_i": col_labels[i],
                        "col_j": col_labels[j],
                        "r_max": round(float(r_val), 4),
                        "tau_steps": int(t_val),
                    })
        metrics["lag_summary"] = lag_summary
    print(" done")

    # 4. Save JSON
    json_dir = RESULTS_DIR / station
    os.makedirs(json_dir, exist_ok=True)
    json_path = json_dir / f"{source_key}_metrics.json"
    with open(json_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"  [{source_key}] JSON → {json_path}")

    # 5. Plot heatmap
    fig_dir = FIGURES_DIR / station
    os.makedirs(fig_dir, exist_ok=True)
    png_path = fig_dir / f"{source_key}_heatmap.png"

    # Regular zero-lag heatmap (all sources)
    plot_heatmap(
        corr_matrix, col_labels, col_values,
        station, source_config["label"], png_path,
    )
    print(f"  [{source_key}] PNG → {png_path}")

    # Extra lagged CCF split heatmap (grouped data only)
    if is_grouped:
        lag_png_path = fig_dir / f"{source_key}_lagged_heatmap.png"
        plot_split_heatmap(
            r_max_matrix, tau_matrix, col_labels, col_values,
            station, MAX_LAG, lag_png_path,
        )
        print(f"  [{source_key}] PNG (lagged) → {lag_png_path}")

        # Save separate lagged JSON
        lag_metrics = {
            "data_source": f"{source_key}_lagged",
            "data_label": f"{source_config['label']} (Lagged CCF)",
            "station": station,
            "n_columns": N,
            "column_labels": col_labels,
            "max_lag": MAX_LAG,
            "r_max_matrix": r_max_matrix.tolist(),
            "tau_matrix": tau_matrix.tolist(),
            "lag_summary": metrics.get("lag_summary", []),
        }
        lag_json_path = json_dir / f"{source_key}_lagged_metrics.json"
        with open(lag_json_path, "w") as f:
            json.dump(lag_metrics, f, indent=2)
        print(f"  [{source_key}] JSON (lagged) → {lag_json_path}")

    return metrics


def discover_stations():
    """Return sorted list of station names from raw_timeseries directory."""
    raw_dir = SOURCES["raw_timeseries"]["csv_dir"]
    if not raw_dir.is_dir():
        raise SystemExit(f"Raw data directory not found: {raw_dir}")
    stations = sorted(
        f.replace("_ringbyring.csv", "")
        for f in os.listdir(raw_dir)
        if f.endswith("_ringbyring.csv")
    )
    return stations


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Ring cross-correlation analysis for InSAR-MLCW stations."
    )
    parser.add_argument(
        "--station", type=str, default=None,
        help="Process single station only (e.g., TUKU).",
    )
    args = parser.parse_args()

    stations = discover_stations()
    if args.station:
        if args.station not in stations:
            raise SystemExit(
                f"Station '{args.station}' not found. "
                f"Available ({len(stations)}): {', '.join(stations[:10])}..."
            )
        stations = [args.station]

    print(f"Ring cross-correlation analysis")
    print(f"  Stations: {len(stations)} ({', '.join(stations[:5])}...)"
          if len(stations) > 1 else f"  Station: {stations[0]}")
    print(f"  Data sources: {', '.join(SOURCES)}")
    print(f"  Results: {RESULTS_DIR}")
    print(f"  Figures: {FIGURES_DIR}")
    print("=" * 60)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(FIGURES_DIR, exist_ok=True)

    counts = {"processed": 0, "skipped": 0}
    per_source = {k: {"ok": 0, "skip": 0} for k in SOURCES}

    for stn in stations:
        print(f"\n--- {stn} ---")
        station_any = False
        for src_key, src_cfg in SOURCES.items():
            try:
                result = process_station(stn, src_key, src_cfg)
                if result is None:
                    per_source[src_key]["skip"] += 1
                else:
                    per_source[src_key]["ok"] += 1
                    station_any = True
            except Exception as e:
                print(f"  [{src_key}] ERROR: {e}")
                per_source[src_key]["skip"] += 1
        if station_any:
            counts["processed"] += 1
        else:
            counts["skipped"] += 1

    # Summary
    print("\n" + "=" * 60)
    print(f"Complete. {counts['processed']} stations processed "
          f"({counts['skipped']} empty/skipped).")
    for src_key in SOURCES:
        print(f"  {src_key}: {per_source[src_key]['ok']} OK, "
              f"{per_source[src_key]['skip']} skipped")
    print(f"Results: {RESULTS_DIR}")
    print(f"Figures: {FIGURES_DIR}")


if __name__ == "__main__":
    main()
