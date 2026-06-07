"""
Evaluate an InSAR deformation model using the Overall Model Test (OMT).

Reads a pre-computed residual timeseries (output of timeseries2velocity.py
with --save-res), computes per-pixel statistics, and writes an HDF5 result.

Statistical framework
---------------------
Under H0 (the functional model is correct and residuals are white noise
with std = sigma_m):

    T_stat = SSR / sigma_m^2  ~  chi2(r)        E[T_stat | H0] = r
    omt    = T_stat / r                          E[omt    | H0] = 1.0

where SSR = sum_t e_t^2 and r = m - n (redundancy / degrees of freedom).

The normalized OMT is the primary diagnostic (analogous to the MATLAB
gnss-ppp toolbox).  Values >> 1 indicate model inadequacy or underestimated
noise.  The unnormalized chi2 variate T_stat is kept for hypothesis testing
via the p-value.

Enhancements over v2
--------------------
  T1  Auto-parse n from file attributes (mintpy.timeFunc.*). Pass --n_param
      only to override.
  T2  Empirical sigma estimation from a stable-pixel mask (--mask). When
      --mask is given and --sigma is not set, sigma is derived automatically
      from per-pixel MAD of the residuals.
  T3  Spatial OMT map PNG (--plot). Saved to the same directory as the
      output HDF5, same stem + '_omt_map.png'.
  T4  Per-date w-test. Accumulated across spatial blocks. Flagged dates
      (w_rms > 3.29) are printed; w_rms is written to the output HDF5.

Usage
-----
    conda run -n isce_ncu3 python insar_omt_v3.py \\
        1_original/asc_tsRes.h5 \\
        --mask  1_original/asc_maskTempCoh.h5 \\
        --alpha 0.05 \\
        --output 1_original/asc_omt_v3.h5 \\
        --plot \\
        --max-memory 4.0

    # Override auto-detected parameters when needed:
    conda run -n isce_ncu3 python insar_omt_v3.py \\
        1_original/asc_tsRes.h5 \\
        --n_param 13 --sigma 5.0 --alpha 0.05 \\
        --output 1_original/asc_omt_v3.h5

Parameter count for timeseries2velocity.py:
    --poly 2            -> 3 terms (intercept + t + t^2)
    --period 10 5 2 1   -> 4 x 2 = 8 terms (sin + cos each)
    Total n = 11
"""

import os
import argparse
import numpy as np
from scipy.stats import chi2
import h5py
import time

from mintpy.utils import readfile
from mintpy.objects import cluster

DATA_TYPE = np.float32


# ---------------------------------------------------------------------------
# T1 — Auto-parse n_param from file attributes
# ---------------------------------------------------------------------------

def _parse_n_param(atr: dict, n_param_override: int | None) -> tuple[int, str]:
    """
    Derive the number of model parameters from HDF5 file attributes.

    Parameters
    ----------
    atr : dict
        Attribute dictionary from readfile.read_attribute().
    n_param_override : int or None
        Value from --n_param CLI arg; overrides auto-detection when given.

    Returns
    -------
    n : int
        Total number of model parameters.
    source : str
        Human-readable description of how n was determined.

    Raises
    ------
    ValueError
        When attributes are absent and no override is provided.
    """
    if n_param_override is not None:
        return n_param_override, f"--n_param override = {n_param_override}"

    poly_raw = atr.get("mintpy.timeFunc.polynomial")
    per_raw  = atr.get("mintpy.timeFunc.periodic")

    n_poly    = None
    n_periods = None

    if poly_raw is not None:
        try:
            poly_order = int(poly_raw.strip())
            n_poly = poly_order + 1          # intercept + order terms
        except ValueError:
            pass

    if per_raw is not None:
        # Accept both space-separated "1 0.5" and bracketed "[1]" or "[1, 0.5]"
        cleaned = per_raw.strip().strip("[]").replace(",", " ")
        tokens  = [t for t in cleaned.split() if t]
        if tokens:
            n_periods = 2 * len(tokens)      # sin + cos per period

    if n_poly is None and n_periods is None:
        raise ValueError(
            "Cannot determine n_param from file attributes "
            "(mintpy.timeFunc.polynomial and mintpy.timeFunc.periodic are absent). "
            "Pass --n_param explicitly."
        )

    n_poly    = n_poly    if n_poly    is not None else 0
    n_periods = n_periods if n_periods is not None else 0
    n_total   = n_poly + n_periods

    parts = []
    if n_poly > 0:
        parts.append(f"poly_order={poly_raw.strip()} -> {n_poly} param(s)")
    if n_periods > 0:
        parts.append(
            f"periodic={per_raw.strip()} -> {n_periods} param(s) "
            f"({n_periods // 2} period(s) x 2)"
        )
    source = f"auto-parsed: {' + '.join(parts)} = {n_total}"
    return n_total, source


# ---------------------------------------------------------------------------
# T2 — Empirical sigma estimation from stable-pixel mask
# ---------------------------------------------------------------------------

def _estimate_sigma(residual_file: str, mask_file: str, atr: dict) -> float:
    """
    Estimate noise sigma from the MAD of residuals at stable pixels.

    Parameters
    ----------
    residual_file : str
        Path to residual timeseries HDF5.
    mask_file : str
        Path to mask HDF5. Tries dataset names: 'mask',
        'temporalCoherence' (threshold > 0.7), 'velocity' (nonzero).
    atr : dict
        Attribute dictionary for unit detection.

    Returns
    -------
    sigma_empirical : float
        Estimated noise standard deviation in metres.
    """
    # --- read mask ---
    mask_2d = None
    with h5py.File(mask_file, "r") as mf:
        for ds_name in ("mask", "temporalCoherence", "velocity"):
            if ds_name not in mf:
                continue
            data = mf[ds_name][()]
            if ds_name == "temporalCoherence":
                mask_2d = data > 0.7
            elif ds_name == "velocity":
                mask_2d = data != 0
            else:
                mask_2d = data.astype(bool)
            print(f"  [sigma] mask dataset '{ds_name}' -> "
                  f"{mask_2d.sum():,} stable pixels")
            break

    if mask_2d is None:
        raise ValueError(
            f"No usable dataset found in mask file: {mask_file}. "
            "Expected 'mask', 'temporalCoherence', or 'velocity'."
        )

    # --- read residuals for masked pixels (chunked by row) ---
    with h5py.File(residual_file, "r") as rf:
        ts = rf["timeseries"]           # (m, height, width)
        m, height, width = ts.shape

        # Safety: only load valid columns
        flat_mask = mask_2d.ravel()
        n_stable  = int(flat_mask.sum())
        if n_stable == 0:
            raise ValueError("Stable-pixel mask is empty — cannot estimate sigma.")

        # Read row by row to stay memory-efficient
        chunk = np.empty((m, n_stable), dtype=np.float64)
        col_offset = 0
        for row in range(height):
            row_data = ts[:, row, :]                      # (m, width)
            row_mask = mask_2d[row, :]                    # (width,)
            n_row    = int(row_mask.sum())
            if n_row == 0:
                continue
            chunk[:, col_offset:col_offset + n_row] = row_data[:, row_mask]
            col_offset += n_row

    # Unit conversion
    if atr.get("UNIT", "m") == "mm":
        chunk = chunk * 0.001

    # --- per-pixel MAD -> sigma ---
    med_px   = np.median(chunk, axis=0)                   # (n_stable,)
    mad_px   = np.median(np.abs(chunk - med_px[None, :]), axis=0)  # (n_stable,)
    sigma_empirical = float(np.median(mad_px)) / 0.6745   # MAD -> 1-sigma

    return sigma_empirical


# ---------------------------------------------------------------------------
# Core statistic
# ---------------------------------------------------------------------------

def calculate_omt(residuals_block: np.ndarray, m: int, n: int,
                  sigma_m: float, alpha: float = 0.05):
    """
    Compute per-pixel OMT statistics from a block of residuals.

    Parameters
    ----------
    residuals_block : np.ndarray, shape (m, N_pixels)
        Pre-computed residuals in metres.
    m : int
        Number of observations (dates).
    n : int
        Number of model parameters.
    sigma_m : float
        A-priori noise standard deviation (metres).
    alpha : float
        Significance level for the chi-squared critical value.

    Returns
    -------
    T_stat : np.ndarray, shape (N_pixels,)
        Unnormalized chi-squared variate SSR / sigma_m^2 ~ chi2(r).
    omt : np.ndarray, shape (N_pixels,)
        Normalized OMT = T_stat / r.  Expected value under H0 is 1.0.
    p_values : np.ndarray, shape (N_pixels,)
        P-value: Pr(chi2(r) > T_stat | H0).
    K : float
        Unnormalized chi-squared critical value chi2.ppf(1-alpha, r).
    K_norm : float
        Normalized critical value K / r.
    """
    r = m - n

    if r <= 0:
        n_pix = residuals_block.shape[1]
        return (np.full(n_pix, 99999.0, dtype=DATA_TYPE),
                np.full(n_pix, 99999.0, dtype=DATA_TYPE),
                np.zeros(n_pix, dtype=DATA_TYPE),
                0.0, 0.0)

    ssr      = np.sum(residuals_block ** 2, axis=0)
    T_stat   = ssr / (sigma_m ** 2)
    omt      = T_stat / r
    K        = chi2.ppf(1.0 - alpha, df=r)
    K_norm   = K / r
    p_values = 1.0 - chi2.cdf(T_stat, df=r)

    return (T_stat.astype(DATA_TYPE), omt.astype(DATA_TYPE),
            p_values.astype(DATA_TYPE), K, K_norm)


# ---------------------------------------------------------------------------
# T3 — Spatial OMT map plot
# ---------------------------------------------------------------------------

def _plot_omt_map(omt_map: np.ndarray, K_norm: float,
                  output_png: str, title_info: dict,
                  mask_2d: np.ndarray | None = None) -> None:
    """
    Save a 2-D OMT map as a PNG image.

    Parameters
    ----------
    omt_map : np.ndarray, shape (height, width)
        Normalized OMT values; zero for invalid/masked pixels.
    K_norm : float
        Normalized critical value K / r (threshold for rejection).
    output_png : str
        Absolute path for the output PNG file.
    title_info : dict
        Keys: n, r, sigma_mm, alpha, median_omt.
    mask_2d : np.ndarray of bool, shape (height, width), optional
        True = valid pixel. Pixels where mask_2d is False are set to NaN
        and rendered as transparent (white) in the output PNG.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker

    # Apply mask: set invalid/unmasked pixels to NaN so they render transparent
    plot_data = omt_map.astype(np.float32).copy()
    if mask_2d is not None:
        plot_data[~mask_2d] = np.nan
    else:
        # Fall back to the original convention: zero = no data
        plot_data[plot_data == 0] = np.nan

    valid = plot_data[np.isfinite(plot_data)]
    if valid.size == 0:
        print("  [plot] No valid OMT pixels — skipping PNG.")
        return

    vmax_candidate = min(3 * K_norm, float(valid.max()))
    vmax = max(vmax_candidate, 5.0) if K_norm < 1.5 else vmax_candidate

    cmap = plt.get_cmap("RdYlGn_r").copy()
    cmap.set_bad(color="white")   # NaN pixels render as white

    fig, ax = plt.subplots(figsize=(10, 8))
    img = ax.imshow(plot_data, cmap=cmap, vmin=0, vmax=vmax,
                    interpolation="nearest", aspect="equal")

    # Threshold contour (use NaN-masked data so contour stays within valid area)
    ax.contour(plot_data, levels=[K_norm],
               colors="black", linestyles="dashed", linewidths=1.2)
    # Dummy line for legend
    import matplotlib.lines as mlines
    threshold_line = mlines.Line2D([], [], color="black", linestyle="dashed",
                                   linewidth=1.2, label=f"K/r = {K_norm:.3f} threshold")
    ax.legend(handles=[threshold_line], loc="upper right", fontsize=9)

    cbar = fig.colorbar(img, ax=ax, fraction=0.03, pad=0.03)
    cbar.set_label(r"Normalized OMT  (H$_0$: OMT $\approx$ 1)", fontsize=10)

    ax.set_title(
        f"OMT Map  |  n={title_info['n']}  r={title_info['r']}  "
        f"sigma={title_info['sigma_mm']:.1f} mm  alpha={title_info['alpha']}",
        fontsize=11,
    )
    ax.text(0.02, 0.02,
            f"median OMT = {title_info['median_omt']:.2f}   K/r = {K_norm:.3f}",
            transform=ax.transAxes, fontsize=9,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7))

    ax.set_xlabel("Column (pixels)")
    ax.set_ylabel("Row (pixels)")

    plt.tight_layout()
    plt.savefig(output_png, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [plot] Saved OMT map -> {output_png}")


# ---------------------------------------------------------------------------
# T4 — Per-date w-test (post-block accumulation)
# ---------------------------------------------------------------------------

def _compute_wtest(wtest_ssr: np.ndarray, wtest_count: np.ndarray,
                   sigma_m: float, dates: list) -> tuple[np.ndarray, list]:
    """
    Finalize the per-date w-test from accumulated SSR and pixel counts.

    Parameters
    ----------
    wtest_ssr : np.ndarray, shape (m,)
        Accumulated sum-of-squared residuals per date.
    wtest_count : np.ndarray, shape (m,)
        Number of valid pixels contributing to each date.
    sigma_m : float
        A-priori noise sigma in metres.
    dates : list
        List of date strings (length m).

    Returns
    -------
    w_rms : np.ndarray, shape (m,)
        RMS w-statistic per date.
    flagged : list of str
        Date strings where w_rms > 3.29.
    """
    with np.errstate(divide="ignore", invalid="ignore"):
        w_rms = np.where(
            wtest_count > 0,
            np.sqrt(wtest_ssr / wtest_count) / sigma_m,
            0.0,
        ).astype(DATA_TYPE)

    flagged = [d for d, w in zip(dates, w_rms) if w > 3.29]
    return w_rms, flagged


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Evaluate deformation model fit via normalized OMT (v3).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("residual_file",
                        help="Residual timeseries HDF5 (e.g. asc_tsRes.h5)")
    # T1: now optional; auto-parsed from file attributes when absent
    parser.add_argument("--n_param", type=int, default=None,
                        help="Number of model parameters n. Auto-detected from "
                             "mintpy.timeFunc.* attributes when not given.")
    # T2: sigma becomes optional with sentinel None
    parser.add_argument("--sigma", type=float, default=None,
                        metavar="MM",
                        help="A-priori noise std in mm. Auto-estimated from "
                             "--mask pixels when not set (fallback: 5.0 mm).")
    parser.add_argument("--mask", default=None,
                        metavar="MASK_H5",
                        help="Stable-pixel mask HDF5 for empirical sigma "
                             "estimation (T2) and OMT map overlay (T3).")
    parser.add_argument("--alpha", type=float, default=0.05,
                        help="Significance level for critical value (default: 0.05)")
    parser.add_argument("--output", default="omt_from_residual.h5",
                        help="Output HDF5 filename")
    parser.add_argument("--max-memory", type=float, default=4.0,
                        metavar="GB",
                        help="Max memory per block in GB (default: 4.0)")
    # T3: plot flag
    parser.add_argument("--plot", action="store_true",
                        help="Save spatial OMT map as PNG (same dir as output)")
    args = parser.parse_args()

    # Resolve output path relative to the current working directory
    args.output = os.path.abspath(args.output)

    # ------------------------------------------------------------------
    # Load metadata
    # ------------------------------------------------------------------
    atr    = readfile.read_attribute(args.residual_file)
    length = int(atr["LENGTH"])
    width  = int(atr["WIDTH"])

    with h5py.File(args.residual_file, "r") as f:
        dates = [d.decode() if isinstance(d, bytes) else d for d in f["date"][:]]
    m = len(dates)

    # T1 — resolve n_param
    n_param, n_source = _parse_n_param(atr, args.n_param)
    r = m - n_param

    # Load mask array for plotting (reused from T2 mask file)
    plot_mask_2d = None
    if args.mask is not None:
        with h5py.File(args.mask, "r") as mf:
            for ds_name in ("mask", "temporalCoherence", "velocity"):
                if ds_name not in mf:
                    continue
                data = mf[ds_name][()]
                if ds_name == "temporalCoherence":
                    plot_mask_2d = data > 0.7
                elif ds_name == "velocity":
                    plot_mask_2d = data != 0
                else:
                    plot_mask_2d = data.astype(bool)
                break

    # T2 — resolve sigma
    sigma_source_tag = "fixed"
    sigma_empirical_mm = None

    if args.mask is not None:
        print(f"Estimating empirical sigma from mask: {args.mask} ...")
        try:
            sigma_emp_m = _estimate_sigma(args.residual_file, args.mask, atr)
            sigma_empirical_mm = sigma_emp_m * 1000.0
            print(f"  Empirical sigma = {sigma_empirical_mm:.3f} mm")
        except Exception as exc:
            print(f"  WARNING: empirical sigma estimation failed ({exc}). "
                  "Falling back to --sigma or 5.0 mm.")
            sigma_emp_m = None

        if args.sigma is None:
            if sigma_emp_m is not None:
                sigma_mm = sigma_empirical_mm
                sigma_m  = sigma_emp_m
                sigma_source_tag = "empirical"
            else:
                sigma_mm = 5.0
                sigma_m  = 5.0 / 1000.0
                sigma_source_tag = "fallback_5mm"
        else:
            sigma_mm = args.sigma
            sigma_m  = args.sigma / 1000.0
            sigma_source_tag = "user_override"
            print(f"  --sigma override: using {sigma_mm:.3f} mm "
                  f"(empirical was {sigma_empirical_mm:.3f} mm)")
    else:
        sigma_mm = args.sigma if args.sigma is not None else 5.0
        sigma_m  = sigma_mm / 1000.0
        if args.sigma is None:
            sigma_source_tag = "default_5mm"

    # ------------------------------------------------------------------
    # Startup summary
    # ------------------------------------------------------------------
    print(f"\nResidual file  : {args.residual_file}")
    print(f"Dates (m)      : {m}")
    print(f"Parameters (n) : {n_param}  [{n_source}]")
    print(f"DOF (r = m-n)  : {r}")
    print(f"Noise sigma    : {sigma_mm:.3f} mm  [{sigma_source_tag}]")
    print(f"Alpha          : {args.alpha}")
    print(f"Output         : {args.output}")

    # ------------------------------------------------------------------
    # Block processing
    # ------------------------------------------------------------------
    box_list, num_box = cluster.split_box2sub_boxes(
        box=(0, 0, width, length),
        num_split=int(np.ceil((m * length * width * 4 * 4)
                              / (args.max_memory * 1024 ** 3))),
        dimension="y",
        print_msg=True,
    )

    best_T_stat  = np.zeros((length, width), dtype=DATA_TYPE)
    best_omt     = np.zeros((length, width), dtype=DATA_TYPE)
    best_p_val   = np.zeros((length, width), dtype=DATA_TYPE)
    best_K_map   = np.zeros((length, width), dtype=DATA_TYPE)
    best_K_norm  = np.zeros((length, width), dtype=DATA_TYPE)

    # T4 — accumulators for per-date w-test
    wtest_ssr   = np.zeros(m, dtype=np.float64)
    wtest_count = np.zeros(m, dtype=np.float64)

    K_scalar      = 0.0
    K_norm_scalar = 0.0
    start_time    = time.time()

    for i, box in enumerate(box_list):
        if num_box > 1:
            print(f"  Patch {i+1}/{num_box} ...", end=" ", flush=True)

        res_data, _ = readfile.read(args.residual_file, box=box)

        # Unit conversion
        if atr.get("UNIT", "m") == "mm":
            res_data = res_data * 0.001

        box_len  = res_data.shape[1]
        box_wid  = res_data.shape[2]
        res_flat = res_data.reshape(m, -1)

        # Valid pixels: no NaNs, not all-zero (masked/nodata)
        valid_mask = (~np.any(np.isnan(res_flat), axis=0) &
                      ~np.all(res_flat == 0, axis=0))

        # T4 — accumulate w-test SSR across spatial blocks
        if np.any(valid_mask):
            res_valid_block = res_flat[:, valid_mask]
            wtest_ssr   += np.sum(res_valid_block ** 2, axis=1)
            wtest_count += valid_mask.sum()

        if not np.any(valid_mask):
            if num_box > 1:
                print("(no valid pixels)")
            continue

        res_valid = res_flat[:, valid_mask]
        T_stat, omt, p_values, K_scalar, K_norm_scalar = calculate_omt(
            res_valid, m, n_param, sigma_m, args.alpha
        )

        n_pix    = box_len * box_wid
        full_T   = np.zeros(n_pix, dtype=DATA_TYPE)
        full_omt = np.zeros(n_pix, dtype=DATA_TYPE)
        full_P   = np.zeros(n_pix, dtype=DATA_TYPE)
        full_K   = np.zeros(n_pix, dtype=DATA_TYPE)
        full_Kn  = np.zeros(n_pix, dtype=DATA_TYPE)

        full_T[valid_mask]   = T_stat
        full_omt[valid_mask] = omt
        full_P[valid_mask]   = p_values
        full_K[valid_mask]   = K_scalar
        full_Kn[valid_mask]  = K_norm_scalar

        y0, y1, x0, x1 = box[1], box[3], box[0], box[2]
        best_T_stat[y0:y1, x0:x1] = full_T.reshape(box_len, box_wid)
        best_omt[y0:y1, x0:x1]    = full_omt.reshape(box_len, box_wid)
        best_p_val[y0:y1, x0:x1]  = full_P.reshape(box_len, box_wid)
        best_K_map[y0:y1, x0:x1]  = full_K.reshape(box_len, box_wid)
        best_K_norm[y0:y1, x0:x1] = full_Kn.reshape(box_len, box_wid)

        if num_box > 1:
            print(f"omt mean={omt.mean():.3f}")

    # ------------------------------------------------------------------
    # T4 — Finalize w-test
    # ------------------------------------------------------------------
    w_rms, flagged_dates = _compute_wtest(
        wtest_ssr, wtest_count, sigma_m, dates
    )

    print(f"\nW-test (per-date, threshold 3.29):")
    if flagged_dates:
        print(f"  {'Date':<12}  {'w_rms':>8}")
        print(f"  {'-'*12}  {'-'*8}")
        for d, w in zip(dates, w_rms):
            if d in flagged_dates:
                print(f"  {d:<12}  {w:8.3f}  <-- FLAGGED")
    else:
        print("  No dates flagged (all w_rms <= 3.29).")

    # ------------------------------------------------------------------
    # Write output HDF5
    # ------------------------------------------------------------------
    with h5py.File(args.output, "w") as f:
        # File-level attributes
        for k, v in atr.items():
            f.attrs[k] = v
        f.attrs["FILE_TYPE"]    = "velocity"
        f.attrs["OMT_N_PARAM"]  = n_param
        f.attrs["OMT_DOF_R"]    = r
        f.attrs["OMT_SIGMA_MM"] = float(sigma_mm)
        f.attrs["OMT_ALPHA"]    = args.alpha
        f.attrs["OMT_K_NORM"]   = float(K_norm_scalar)
        # T2 provenance attributes
        f.attrs["OMT_SIGMA_SOURCE"] = sigma_source_tag
        if sigma_empirical_mm is not None:
            f.attrs["OMT_SIGMA_EMPIRICAL_MM"] = float(sigma_empirical_mm)

        # Backward-compatible 2-D datasets
        datasets = {
            "omt": (
                best_omt, "1",
                "Normalized OMT = SSR/sigma^2/r; expected ~1.0 under H0"
            ),
            "T_stat": (
                best_T_stat, "1",
                "Chi-squared variate SSR/sigma^2; expected ~r under H0"
            ),
            "p_value": (
                best_p_val, "1",
                "P-value: Pr(chi2(r) > T_stat | H0); reject H0 when < alpha"
            ),
            "critical_K": (
                best_K_map, "1",
                "Unnormalized chi-sq critical value chi2.ppf(1-alpha, r)"
            ),
            "omt_K": (
                best_K_norm, "1",
                "Normalized critical value K/r; omt > omt_K -> reject H0"
            ),
        }

        for name, (data, unit, desc) in datasets.items():
            ds = f.create_dataset(name, data=data, compression="gzip")
            ds.attrs["UNIT"]        = unit
            ds.attrs["DESCRIPTION"] = desc
            for k, v in atr.items():
                if k != "UNIT":
                    ds.attrs[k] = v

        # T4 — per-date w_rms (1-D) and date strings
        ds_w = f.create_dataset("w_rms", data=w_rms, compression="gzip")
        ds_w.attrs["UNIT"]        = "1"
        ds_w.attrs["DESCRIPTION"] = (
            "Per-date RMS w-statistic = sqrt(mean((e/sigma)^2)); "
            "flagged when > 3.29"
        )
        # Copy date strings for self-contained output
        date_arr = np.array([d.encode() for d in dates])
        ds_d = f.create_dataset("date", data=date_arr)
        ds_d.attrs["DESCRIPTION"] = "Acquisition dates (YYYYMMDD)"

    print(f"\nOutput HDF5    : {args.output}")

    # ------------------------------------------------------------------
    # T3 — Optional spatial OMT map plot
    # ------------------------------------------------------------------
    if args.plot:
        valid_omt = best_omt[best_omt > 0]
        median_omt = float(np.median(valid_omt)) if valid_omt.size > 0 else 0.0
        output_png = os.path.splitext(args.output)[0] + "_omt_map.png"
        _plot_omt_map(
            omt_map=best_omt,
            K_norm=K_norm_scalar,
            output_png=output_png,
            title_info={
                "n":          n_param,
                "r":          r,
                "sigma_mm":   sigma_mm,
                "alpha":      args.alpha,
                "median_omt": median_omt,
            },
            mask_2d=plot_mask_2d,
        )

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    elapsed_m, elapsed_s = divmod(time.time() - start_time, 60)
    valid_omt = best_omt[best_omt > 0]

    print(f"\nDone in {elapsed_m:02.0f}m {elapsed_s:02.1f}s")
    print(f"  Valid pixels       : {valid_omt.size:,}")
    if valid_omt.size > 0:
        print(f"  OMT (normalized)   : mean={valid_omt.mean():.3f}  "
              f"median={np.median(valid_omt):.3f}  std={valid_omt.std():.3f}")
    print(f"  K/r (threshold)    : {K_norm_scalar:.4f}  "
          f"(alpha={args.alpha}, r={r})")
    if valid_omt.size > 0:
        print(f"  Pixels > K/r       : {(valid_omt > K_norm_scalar).sum():,}  "
              f"({(valid_omt > K_norm_scalar).mean()*100:.2f}%)")
    print(f"  W-test flagged dates: {len(flagged_dates)}")


if __name__ == "__main__":
    main()
