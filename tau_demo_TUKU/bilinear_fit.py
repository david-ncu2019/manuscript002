"""
bilinear_fit.py — Standalone bilinear Terzaghi/Riley fitter for per-layer compaction.

Physical model:
    b(t) = c + S_ke * u(t) + (S_kv - S_ke) * V(t)

    u(t) = H(t) - H_ref        head change from reference date (m)
    V(t) = min(0, cummin(H) - h_c)   virgin inelastic exceedance (m)

    S_ke  — elastic skeletal storage coefficient (mm/m)
    S_kv  — inelastic skeletal storage coefficient (mm/m)
    c     — per-layer intercept (mm), captures compaction pre-dating the record
    H_ref — last hydraulic head on/before REF_DATE (2015-01-16)

Uses the center-then-NNLS pattern from ihmf_model_v3.py::fit_two_regressor_nnls_X
to enforce S_ke >= 0 and S_kv >= S_ke while allowing an unconstrained intercept.

Usage:
    from tau_demo_TUKU.bilinear_fit import fit_bilinear
    result = fit_bilinear(H_abs, b, h_c_abs)
    print(result["S_ke"], result["S_kv"], result["r2"])

Reference: super_plan_2026-06-09.md Phase 0.0 Step B
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Import from scripts/10_ihmf/ (same package as ihmf_model_v3)
_SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts" / "10_ihmf"
sys.path.insert(0, str(_SCRIPT_DIR))
from ihmf_model_v3 import fit_two_regressor_nnls_X, compute_virgin_term, compute_r2_cumulative

REF_DATE = pd.Timestamp("2015-01-16")


def fit_bilinear(
    H_abs: np.ndarray,
    b: np.ndarray,
    h_c_abs: float,
    ref_date: pd.Timestamp | None = None,
    with_intercept: bool = True,
) -> dict:
    """
    Fit the bilinear Terzaghi/Riley compaction model to a single layer.

    Parameters
    ----------
    H_abs : 1-D float array
        Absolute hydraulic head (m MSL) at each epoch.  Must be on a regular
        grid aligned with `b`.
    b : 1-D float array
        Cumulative MLCW compaction (mm) at each epoch.  Same length as H_abs.
    h_c_abs : float
        Preconsolidation head in absolute MSL — the lowest head experienced
        before `ref_date`.  Computed as min(H[t < ref_date]).
    ref_date : pd.Timestamp or None
        Reference date for zero-referencing.  Default: 2015-01-16.
    with_intercept : bool
        If True (default), fit a per-layer intercept via data centering
        (Frisch-Waugh-Lovell for NNLS).  Set False to force through origin.

    Returns
    -------
    dict with keys:
        S_ke           : float, elastic storage coefficient (mm/m)
        S_kv           : float, inelastic storage coefficient (mm/m)
        delta          : float, S_kv - S_ke (>= 0)
        c_intercept    : float, per-layer intercept (mm; 0 if with_intercept=False)
        ratio          : float, S_kv / S_ke (inf if S_ke == 0)
        r2             : float, cumulative R²
        rmse           : float, root-mean-square error (mm)
        b_pred         : 1-D float array, predicted cumulative compaction (mm)
        n_elastic      : int, number of elastic epochs (V == 0)
        n_inelastic    : int, number of inelastic epochs (V < 0)
        H_ref          : float, reference head at ref_date (m MSL)
        u              : 1-D float array, zero-referenced head (m)
        V              : 1-D float array, virgin term (m)
    """
    if ref_date is None:
        ref_date = REF_DATE

    H_abs = np.asarray(H_abs, dtype=float)
    b = np.asarray(b, dtype=float)

    # 1. Zero-reference head: u(t) = H(t) - H_ref
    #    H_ref = last valid head on/before ref_date
    finite_mask = np.isfinite(H_abs)
    if not finite_mask.any():
        raise ValueError("H_abs contains no finite values")
    # Find the reference value: we need the datetime index to filter by ref_date.
    # Since this function receives raw arrays (no datetime), the caller is
    # responsible for passing H_abs aligned such that the first epoch is at or
    # after ref_date.  We use the first finite value as H_ref.
    # For full datetime-aware behaviour, pass H_abs already sliced to
    # post-REF_DATE epochs and provide H_ref explicitly.
    H_ref = float(H_abs[finite_mask][0])
    u = H_abs - H_ref

    # 2. Compute virgin term V(t) = min(0, cummin(H_abs) - h_c_abs)
    #    Both H_abs and h_c_abs are in absolute MSL — datum cancels.
    V = compute_virgin_term(H_abs, h_c_abs)

    # 3. Fit two-regressor NNLS: b = c + S_ke * u + delta * V
    S_ke, S_kv, delta, c_intercept, resid_sq, b_pred = fit_two_regressor_nnls_X(
        u, V, b, with_intercept=with_intercept
    )

    # 4. Compute metrics
    ratio = S_kv / S_ke if S_ke > 1e-15 else float("inf")
    r2 = compute_r2_cumulative(b, b_pred)
    rmse = float(np.sqrt(np.mean((b - b_pred) ** 2)))
    n_elastic = int((V == 0).sum())
    n_inelastic = int((V < 0).sum())

    return {
        "S_ke": S_ke,
        "S_kv": S_kv,
        "delta": delta,
        "c_intercept": c_intercept,
        "ratio": ratio,
        "r2": r2,
        "rmse": rmse,
        "b_pred": b_pred,
        "n_elastic": n_elastic,
        "n_inelastic": n_inelastic,
        "H_ref": H_ref,
        "u": u,
        "V": V,
    }


def fit_bilinear_from_series(
    head_series: pd.Series,
    b_series: pd.Series,
    h_c_abs: float,
    ref_date: pd.Timestamp | None = None,
    with_intercept: bool = True,
) -> dict:
    """
    Datetime-aware wrapper around fit_bilinear.

    Uses the datetime index to compute H_ref correctly: the last valid head
    value on or before `ref_date`.  Then zero-references the head and calls
    fit_bilinear on the aligned arrays.

    Parameters
    ----------
    head_series : pd.Series with DatetimeIndex
        Absolute hydraulic head (m MSL).  Must be sorted ascending.
    b_series : pd.Series with same index
        Cumulative MLCW compaction (mm).
    h_c_abs : float
        Preconsolidation head in absolute MSL.
    ref_date : pd.Timestamp or None
        Reference date (default: 2015-01-16).
    with_intercept : bool
        If True, fit a per-layer intercept.

    Returns
    -------
    dict — same as fit_bilinear, plus keys:
        H_ref  : float, reference head at ref_date (m MSL)
        u      : 1-D float array, zero-referenced head (m)
        V      : 1-D float array, virgin term (m)
    """
    if ref_date is None:
        ref_date = REF_DATE

    # Align both series to common index
    common_idx = head_series.dropna().index.intersection(b_series.dropna().index)
    head_aligned = head_series.loc[common_idx]
    b_aligned = b_series.loc[common_idx]

    if len(common_idx) < 2:
        raise ValueError(f"Fewer than 2 common valid epochs (got {len(common_idx)})")

    # H_ref = last valid head on/before ref_date
    pre_ref = head_aligned[head_aligned.index <= ref_date]
    if len(pre_ref) == 0:
        raise ValueError(f"No GWL data on/before {ref_date.date()} — cannot compute H_ref")
    H_ref = float(pre_ref.iloc[-1])

    # Slice to post-ref_date epochs
    post_ref = head_aligned[head_aligned.index >= ref_date]
    b_post = b_aligned.loc[post_ref.index]

    H_abs = post_ref.values.astype(float)
    b_arr = b_post.values.astype(float)

    # Override H_ref-aware zero-referencing in fit_bilinear by passing the
    # correct reference value.  We pass H_abs as-is and patch H_ref after.
    # Actually, fit_bilinear uses H_abs[0] as H_ref — so we pre-shift here.
    u = H_abs - H_ref
    V = compute_virgin_term(H_abs, h_c_abs)

    S_ke, S_kv, delta, c_intercept, resid_sq, b_pred = fit_two_regressor_nnls_X(
        u, V, b_arr, with_intercept=with_intercept
    )

    ratio = S_kv / S_ke if S_ke > 1e-15 else float("inf")
    r2 = compute_r2_cumulative(b_arr, b_pred)
    rmse = float(np.sqrt(np.mean((b_arr - b_pred) ** 2)))
    n_elastic = int((V == 0).sum())
    n_inelastic = int((V < 0).sum())

    return {
        "S_ke": S_ke,
        "S_kv": S_kv,
        "delta": delta,
        "c_intercept": c_intercept,
        "ratio": ratio,
        "r2": r2,
        "rmse": rmse,
        "b_pred": b_pred,
        "n_elastic": n_elastic,
        "n_inelastic": n_inelastic,
        "H_ref": H_ref,
        "u": u,
        "V": V,
    }


# ── Self-test on TUKU F1 ──────────────────────────────────────────────────────
if __name__ == "__main__":
    import json

    ROOT = Path(__file__).resolve().parent
    DATA_DIR = ROOT / "data"
    INC_DIR = DATA_DIR / "incremental_data"

    WELL_CONFIG = [
        ("F1", "HONGLUN_gwl_timeseries.feather", "09050111"),
        ("T1", "HONGLUN_gwl_timeseries.feather", "09050111"),
        ("F2", "TUKU_gwl_timeseries.feather",   "09050321"),
        ("T2", "LUNZI_gwl_timeseries.feather",   "09170121"),
        ("F3", "TUKU_gwl_timeseries.feather",   "09050331"),
        ("F4", "LIUZHUANG_gwl_timeseries.feather", "09080251"),
    ]

    # Load MLCW master (same pattern as diagnose_cumulative_tuku.py)
    mlcw_inc = pd.read_feather(INC_DIR / "mlcw_diff_cleaned.feather")
    mlcw_inc["datetime"] = pd.to_datetime(mlcw_inc["datetime"]).astype("datetime64[ns]")
    mlcw_inc = mlcw_inc.sort_values("datetime").reset_index(drop=True)
    for col in [c for c in mlcw_inc.columns if c != "datetime"]:
        mlcw_inc[f"_cum_{col}"] = mlcw_inc[col].fillna(0.0).cumsum()
    master = pd.DataFrame({"datetime": mlcw_inc["datetime"].copy()})

    print("=" * 70)
    print("bilinear_fit.py — Self-test on TUKU 6 layers")
    print("=" * 70)

    for layer, fname, wellcode in WELL_CONFIG:
        # Load GWL
        gwl = pd.read_feather(DATA_DIR / fname)
        gwl["datetime"] = pd.to_datetime(gwl["datetime"]).astype("datetime64[ns]")
        gwl = gwl[["datetime", wellcode]].dropna(subset=[wellcode])
        gwl = gwl.sort_values("datetime").reset_index(drop=True)

        # Zero-reference
        gwl_indexed = gwl.set_index("datetime")[wellcode]
        avail = gwl_indexed.dropna()
        pre_ref = avail.index[avail.index <= REF_DATE]
        if len(pre_ref) == 0:
            print(f"  {layer}: SKIP — no pre-REF_DATE GWL data")
            continue
        ref_val = float(avail.loc[pre_ref[-1]])

        # h_c
        pre_ref_vals = gwl[gwl["datetime"] < REF_DATE][wellcode].dropna()
        h_c_abs = float(pre_ref_vals.min()) if len(pre_ref_vals) >= 10 else float(gwl[wellcode].dropna().min())

        # Align
        gwl_aligned = pd.merge_asof(master, gwl, on="datetime",
                                     direction="nearest", tolerance=pd.Timedelta("3D"))
        H_abs = gwl_aligned[wellcode].values.astype(float)
        b_cum = mlcw_inc[f"_cum_{layer}"].values.astype(float)

        # Mask valid
        valid = np.isfinite(H_abs) & np.isfinite(b_cum)
        H_abs = H_abs[valid]
        b_cum = b_cum[valid]

        if len(H_abs) < 10:
            print(f"  {layer}: SKIP — fewer than 10 valid epochs")
            continue

        # Fit
        result = fit_bilinear(H_abs, b_cum, h_c_abs, with_intercept=True)

        print(f"\n  {layer}: S_ke={result['S_ke']:.5f}  S_kv={result['S_kv']:.5f}  "
              f"ratio={result['ratio']:.2f}×  R²={result['r2']:.4f}  "
              f"RMSE={result['rmse']:.3f} mm  c={result['c_intercept']:.3f} mm  "
              f"n_el={result['n_elastic']}  n_inel={result['n_inelastic']}")

        # Guardrail: validate sign constraints
        if result["S_ke"] < 0:
            print(f"    FATAL: S_ke = {result['S_ke']:.6f} < 0")
        if result["S_kv"] < result["S_ke"]:
            print(f"    FATAL: S_kv < S_ke")
        if result["r2"] < 0:
            print(f"    WARN: R² < 0 — model worse than mean")

    print("\n" + "=" * 70)
    print("Self-test complete.")
