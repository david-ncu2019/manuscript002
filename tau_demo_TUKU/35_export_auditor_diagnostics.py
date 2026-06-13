#!/usr/bin/env python3
"""
35_export_auditor_diagnostics.py — Machine-readable diagnostic exports for auditor pattern detection.

Reads EXISTING persisted TUKU pilot results (no recomputation) and produces:
  - 8 machine-readable diagnostic files (CSV/JSON) for programmatic querying
  - 8 companion figures (PNG) for visual pattern triage

All outputs go to tau_demo_TUKU/results/auditor_diagnostics/

Usage:
    $env:PYTHONPATH=""; conda run -n fafalab2 python tau_demo_TUKU/35_export_auditor_diagnostics.py

Date: 2026-06-12
"""

import json
import os
import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

# ── Config ────────────────────────────────────────────────────────────────────

STATION = "TUKU"
LAYERS = ["F1", "T1", "F2", "T2", "F3", "F4"]
CADENCES = ["none", "annual", "semiannual", "quarterly", "monthly", "actual"]

# Sign-error threshold: only flag when |obs_inc| exceeds this (avoids noise flags)
SIGN_ERROR_THRESHOLD_MM = 0.1

# Drift windows in epochs (5-day cadence → 72 ≈ 1 year, 144 ≈ 2 years)
DRIFT_WINDOWS = [72, 144]

# Blind-era onset (post-2021-11 — MLCW network shutdown)
BLIND_ERA_START = pd.Timestamp("2021-11-01")

# ── Paths ─────────────────────────────────────────────────────────────────────

def resolve_paths():
    """Resolve all input and output paths relative to this script's location."""
    script_dir = Path(__file__).resolve().parent  # tau_demo_TUKU/
    results_dir = script_dir / "results"

    paths = {
        "results_dir": results_dir,
        "recon_dir": results_dir / "reconstruction",
        "timeseries_dir": results_dir / "timeseries",
        "seq_dir": results_dir / "seq",
        "provenance_mask": results_dir / "mlcw_observed_epoch_mask.csv",
        "carrier_gwl_eval": results_dir / "carrier_gwl_eval.json",
        "storage_params": results_dir / "characterization" / f"{STATION}_storage_params.json",
        "output_dir": results_dir / "auditor_diagnostics",
    }
    return paths


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1: Data Loading
# ═══════════════════════════════════════════════════════════════════════════════

def load_reconstruction_data(paths):
    """Load per-layer reconstruction CSVs. Returns dict[layer] → DataFrame."""
    recon = {}
    for layer in LAYERS:
        fp = paths["recon_dir"] / f"{STATION}_{layer}_reconstruction.csv"
        if not fp.exists():
            print(f"  WARNING: {fp} not found — skipping {layer}")
            continue
        df = pd.read_csv(fp, parse_dates=["date"])
        df["layer"] = layer
        recon[layer] = df
    print(f"  Loaded reconstruction data: {len(recon)}/{len(LAYERS)} layers")
    return recon


def load_regime_data(paths):
    """Load per-layer cumulative timeseries CSVs (contain H_zero_ref_m, V_m, b_obs_mm)."""
    regime = {}
    for layer in LAYERS:
        fp = paths["timeseries_dir"] / f"{STATION}_{layer}_cumulative_timeseries.csv"
        if not fp.exists():
            print(f"  WARNING: {fp} not found — skipping {layer}")
            continue
        df = pd.read_csv(fp, parse_dates=["datetime"])
        df = df.rename(columns={"datetime": "date"})
        df["layer"] = layer
        regime[layer] = df
    print(f"  Loaded regime/cumulative data: {len(regime)}/{len(LAYERS)} layers")
    return regime


def load_provenance_mask(paths):
    """Load per-epoch observation provenance mask."""
    fp = paths["provenance_mask"]
    if not fp.exists():
        print(f"  WARNING: {fp} not found — all epochs treated as observed")
        return None
    df = pd.read_csv(fp, parse_dates=["date"])
    print(f"  Loaded provenance mask: {len(df)} epochs")
    return df


def load_gps_surface(paths):
    """Extract GPS surface displacement from reconstruction CSVs (common to all layers)."""
    # d_surface_mm is the same across all layers — read from F1 reconstruction
    fp = paths["recon_dir"] / f"{STATION}_F1_reconstruction.csv"
    if not fp.exists():
        print(f"  WARNING: {fp} not found — cannot load GPS surface")
        return None
    df = pd.read_csv(fp, parse_dates=["date"])
    gps = df[["date", "d_surface_mm"]].copy()
    gps = gps.dropna(subset=["d_surface_mm"])
    gps = gps.set_index("date")["d_surface_mm"]
    print(f"  Loaded GPS surface: {len(gps)} epochs with data")
    return gps


def load_carrier_params(paths):
    """Load carrier model parameters (a_k, c_k, d_k) from reconstruction summary."""
    fp = paths["recon_dir"] / f"{STATION}_carrier_reconstruction_summary.json"
    if not fp.exists():
        print(f"  WARNING: {fp} not found — cannot load carrier params")
        return {}
    with open(fp) as f:
        summary = json.load(f)
    # JSON structure: {"per_layer": {"F1": {...}, "T1": {...}, ...}}
    per_layer = summary.get("per_layer", summary)
    params = {}
    for layer in LAYERS:
        ld = per_layer.get(layer, {})
        params[layer] = {
            "a_k": ld.get("a_k", np.nan),
            "c_k": ld.get("c_k", np.nan),
            "d_k": ld.get("d_k", np.nan),
        }
    n_valid = sum(1 for p in params.values() if not pd.isna(p["a_k"]))
    print(f"  Loaded carrier params: {n_valid}/{len(LAYERS)} layers with valid a_k")
    return params


def load_storage_params(paths):
    """Load IHM-F storage coefficients (h_c, S_ke, S_kv) per layer."""
    fp = paths["storage_params"]
    if not fp.exists():
        print(f"  WARNING: {fp} not found — regime diagnostics will be limited")
        return {}
    with open(fp) as f:
        storage = json.load(f)
    # JSON structure: {"per_layer": {"F1": {...}, ...}}
    per_layer = storage.get("per_layer", storage)
    print(f"  Loaded storage params: {len(per_layer)} layers")
    return per_layer


def load_gwl_adoption(paths):
    """Load GWL adoption map (which layers benefit from GWL residual term)."""
    fp = paths["carrier_gwl_eval"]
    if not fp.exists():
        print(f"  WARNING: {fp} not found — treating all layers as carrier-only")
        return {lyr: False for lyr in LAYERS}
    with open(fp) as f:
        gwl_eval = json.load(f)
    adopt_dict = gwl_eval.get("adopt_gwl", {})
    if isinstance(adopt_dict, list):
        # Old format: list of layer names
        adoption = {lyr: lyr in adopt_dict for lyr in LAYERS}
    else:
        # New format: dict of layer → bool
        adoption = {lyr: adopt_dict.get(lyr, False) for lyr in LAYERS}
    print(f"  GWL adoption: {adoption}")
    return adoption


def load_seq_data(paths):
    """Load sequential rehearsal predictions across all cadences.
    Returns dict[(cadence, layer)] → DataFrame (seq timeseries).
    """
    seq = {}
    for cadence in CADENCES:
        cadence_dir = paths["seq_dir"] / cadence
        if not cadence_dir.exists():
            print(f"  WARNING: seq/{cadence}/ not found — skipping")
            continue
        for layer in LAYERS:
            fp = cadence_dir / f"{STATION}_{layer}_seq_timeseries.csv"
            if fp.exists():
                df = pd.read_csv(fp, parse_dates=["date"])
                df["layer"] = layer
                df["cadence"] = cadence
                seq[(cadence, layer)] = df
    print(f"  Loaded seq data: {len(seq)} (cadence, layer) pairs")
    return seq


def load_transparency_data(paths):
    """Load per-layer transparency CSVs (contain obs_verified_mm at reveal dates)."""
    transp = {}
    transp_dir = paths["seq_dir"] / "transparency"
    if not transp_dir.exists():
        print(f"  WARNING: seq/transparency/ not found")
        return transp
    for layer in LAYERS:
        fp = transp_dir / f"{STATION}_{layer}_transparency_data.csv"
        if fp.exists():
            df = pd.read_csv(fp, parse_dates=["date"])
            df["layer"] = layer
            transp[layer] = df
    print(f"  Loaded transparency data: {len(transp)}/{len(LAYERS)} layers")
    return transp


def load_seq_metrics(paths):
    """Load per-cadence metrics.json (contains innovations arrays)."""
    metrics = {}
    for cadence in CADENCES:
        fp = paths["seq_dir"] / cadence / "metrics.json"
        if fp.exists():
            with open(fp) as f:
                metrics[cadence] = json.load(f)
    print(f"  Loaded seq metrics: {len(metrics)}/{len(CADENCES)} cadences")
    return metrics


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2: Diagnostic Computation
# ═══════════════════════════════════════════════════════════════════════════════

def compute_per_epoch_residuals(recon, provenance):
    """File 1: Master epoch-by-epoch residual table with sign-error flags."""
    frames = []
    for layer in LAYERS:
        if layer not in recon:
            continue
        df = recon[layer].copy()

        # Merge provenance mask
        if provenance is not None:
            prov_col = f"{layer}_observed"
            if prov_col in provenance.columns:
                df = df.merge(provenance[["date", prov_col]], on="date", how="left")
                df["is_observed"] = df[prov_col].fillna(False)
            else:
                df["is_observed"] = True
        else:
            df["is_observed"] = True

        # Ensure columns exist
        if "b_model_inc_mm" not in df.columns or "b_model_mm" not in df.columns:
            print(f"  WARNING: {layer} missing prediction columns — skipping")
            continue

        # Incremental obs/pred
        obs_inc = df["b_model_inc_mm"].copy()  # Actually this is obs — need to check
        # The reconstruction CSV has b_model_mm (cumulative model) and b_observed_mm (cumulative obs)
        # b_model_inc_mm is incremental model. We need incremental obs too.
        # Compute incremental obs from cumulative b_observed_mm
        cum_obs = df["b_observed_mm"].copy()
        obs_inc = cum_obs.diff()  # incremental observed

        pred_inc = df["b_model_inc_mm"].copy()

        residual = pred_inc - obs_inc
        abs_residual = residual.abs()

        # Sign error: signs differ when both exceed threshold
        sign_error = (np.sign(pred_inc) != np.sign(obs_inc)) & (obs_inc.abs() > SIGN_ERROR_THRESHOLD_MM)

        # Cumulative versions (zero-referenced at first valid epoch)
        cum_obs_clean = cum_obs.dropna()
        cum_pred = df["b_model_mm"].copy()
        if len(cum_obs_clean) > 0:
            ref_obs = cum_obs_clean.iloc[0]
            ref_pred = cum_pred.loc[cum_obs_clean.index[0]] if cum_obs_clean.index[0] in cum_pred.index else 0
            cum_obs_zr = cum_obs - ref_obs
            cum_pred_zr = cum_pred - ref_pred
        else:
            cum_obs_zr = cum_obs
            cum_pred_zr = cum_pred

        cum_residual = cum_pred_zr - cum_obs_zr

        out = pd.DataFrame({
            "date": df["date"],
            "layer": layer,
            "obs_inc_mm": obs_inc,
            "pred_inc_mm": pred_inc,
            "residual_mm": residual,
            "abs_residual_mm": abs_residual,
            "sign_error": sign_error,
            "is_observed": df["is_observed"],
            "is_gap_filled": df.get("is_gap_filled", False),
            "cum_obs_mm": cum_obs_zr,
            "cum_pred_mm": cum_pred_zr,
            "cum_residual_mm": cum_residual,
        })

        # Rolling drift rate (mm per epoch) over ~1 year window
        window = 72
        if len(out) > window:
            out["cum_drift_rate_mm_per_epoch"] = (
                out["cum_residual_mm"]
                .rolling(window=window, min_periods=max(10, window // 4))
                .apply(lambda x: np.polyfit(np.arange(len(x)), x, 1)[0] if len(x) >= 10 else np.nan, raw=True)
            )
        else:
            out["cum_drift_rate_mm_per_epoch"] = np.nan

        frames.append(out)

    if not frames:
        print("  ERROR: No reconstruction data to build per_epoch_residuals")
        return None

    result = pd.concat(frames, ignore_index=True)
    result = result.sort_values(["layer", "date"]).reset_index(drop=True)
    print(f"  per_epoch_residuals: {len(result)} rows, {result['sign_error'].sum()} sign errors")
    return result


def compute_sign_error_log(residuals_df):
    """File 2: Filtered log of only problematic epochs (sign errors + large residuals)."""
    if residuals_df is None:
        return None

    df = residuals_df.copy()
    df = df.dropna(subset=["obs_inc_mm", "pred_inc_mm"])

    # Direction classification
    def direction(val, thresh=SIGN_ERROR_THRESHOLD_MM):
        if pd.isna(val):
            return "unknown"
        if val < -thresh:
            return "compacting"
        elif val > thresh:
            return "rebounding"
        else:
            return "flat"

    df["obs_direction"] = df["obs_inc_mm"].apply(direction)
    df["pred_direction"] = df["pred_inc_mm"].apply(direction)

    # Error type classification
    def error_type(row):
        if pd.isna(row["obs_inc_mm"]) or pd.isna(row["pred_inc_mm"]):
            return "unknown"
        obs_abs = abs(row["obs_inc_mm"])
        pred_abs = abs(row["pred_inc_mm"])
        if obs_abs < SIGN_ERROR_THRESHOLD_MM:
            return "obs_flat"
        if row["sign_error"]:
            return "sign_reversal"
        ratio = pred_abs / max(obs_abs, 0.001)
        if ratio > 3.0:
            return "overpredict"
        elif ratio < 0.33:
            return "underpredict"
        else:
            return "correct_direction"

    df["error_type"] = df.apply(error_type, axis=1)
    df["magnitude_ratio"] = df["pred_inc_mm"].abs() / df["obs_inc_mm"].abs().clip(lower=0.001)

    # Cumulative residual just before this epoch (carried forward)
    df["cum_residual_before_mm"] = df.groupby("layer")["cum_residual_mm"].shift(1)

    # Select columns for output
    cols = [
        "date", "layer", "obs_inc_mm", "pred_inc_mm", "residual_mm",
        "obs_direction", "pred_direction", "error_type", "magnitude_ratio",
        "is_observed", "is_gap_filled", "cum_residual_before_mm",
    ]
    out = df[cols].copy()

    # Filter to only "interesting" epochs (not correct_direction, not obs_flat)
    out_interesting = out[out["error_type"] != "correct_direction"].copy()
    print(f"  sign_error_log: {len(out_interesting)} problematic epochs (out of {len(out)} total)")
    return out_interesting


def compute_regime_epochs(regime, recon, storage_params):
    """File 3: Per-epoch elastic/inelastic classification with head-compaction consistency."""
    frames = []
    for layer in LAYERS:
        if layer not in regime or layer not in recon:
            continue
        rdf = regime[layer].copy()
        rdf = rdf.rename(columns={"b_obs_mm": "cum_obs_mm_regime"})

        # Get h_c from storage params if available
        h_c = np.nan
        if layer in storage_params:
            h_c = storage_params[layer].get("h_c", storage_params[layer].get("h_c_m", np.nan))

        head_col = "H_zero_ref_m"
        if head_col not in rdf.columns:
            print(f"  WARNING: {layer} missing {head_col} — skipping regime classification")
            continue

        head_msl = rdf[head_col]
        V_m = rdf.get("V_m", pd.Series(np.nan, index=rdf.index))

        # Regime classification
        is_inelastic = V_m < 0
        regime_label = is_inelastic.map({True: "inelastic", False: "elastic"})

        # Regime transition detection
        regime_transition = is_inelastic.astype(int).diff().abs() > 0

        # Head change between consecutive epochs
        head_change = head_msl.diff()

        # Observed incremental compaction (from reconstruction)
        cum_obs = rdf["cum_obs_mm_regime"]
        obs_inc = cum_obs.diff()

        # Expected sign match: head fell → should compact; head rose → should rebound
        head_fell = head_change < -0.001  # m, ~1 mm threshold
        head_rose = head_change > 0.001
        compacting = obs_inc < -SIGN_ERROR_THRESHOLD_MM
        rebounding = obs_inc > SIGN_ERROR_THRESHOLD_MM
        flat_obs = obs_inc.abs() <= SIGN_ERROR_THRESHOLD_MM

        expected_match = (
            (head_fell & compacting) |
            (head_rose & rebounding) |
            (head_change.abs() <= 0.001) |  # stable head
            flat_obs  # negligible compaction change
        )

        out = pd.DataFrame({
            "date": rdf["date"],
            "layer": layer,
            "head_m_msl": head_msl,
            "h_c_m": h_c,
            "head_below_hc_m": head_msl - h_c if not pd.isna(h_c) else np.nan,
            "V_m": V_m,
            "regime": regime_label,
            "is_regime_transition": regime_transition,
            "obs_inc_mm": obs_inc,
            "head_change_m": head_change,
            "expected_sign_match": expected_match,
        })
        frames.append(out)

    if not frames:
        return None

    result = pd.concat(frames, ignore_index=True)
    result = result.sort_values(["layer", "date"]).reset_index(drop=True)
    n_mismatch = (~result["expected_sign_match"]).sum()
    print(f"  per_layer_regime_epochs: {len(result)} rows, {n_mismatch} head-compaction mismatches")
    return result


def compute_decomposition(recon, carrier_params, gps_surface):
    """File 4: Per-epoch prediction decomposition into carrier + GWL terms."""
    frames = []
    for layer in LAYERS:
        if layer not in recon:
            continue
        df = recon[layer].copy()

        params = carrier_params.get(layer, {})
        a_k = params.get("a_k", np.nan)
        c_k = params.get("c_k", np.nan)
        d_k = params.get("d_k", np.nan)

        # Carrier term: a_k * d_surface
        carrier_term = a_k * df["d_surface_mm"] if not pd.isna(a_k) else pd.Series(np.nan, index=df.index)

        # Intercept
        intercept = c_k if not pd.isna(c_k) else np.nan

        # Total prediction
        total_pred = df["b_model_mm"]

        # GWL term = total - carrier - intercept
        gwl_term = total_pred - carrier_term - intercept

        # Fractions
        total_for_fraction = total_pred.abs().clip(lower=0.001)
        carrier_fraction = carrier_term / total_for_fraction
        gwl_fraction = gwl_term / total_for_fraction

        # Observed
        obs = df["b_observed_mm"]

        # Surface displacement
        surface = df["d_surface_mm"]

        out = pd.DataFrame({
            "date": df["date"],
            "layer": layer,
            "carrier_term_mm": carrier_term,
            "gwl_term_mm": gwl_term,
            "intercept_mm": intercept,
            "total_pred_mm": total_pred,
            "obs_mm": obs,
            "carrier_fraction": carrier_fraction,
            "gwl_fraction": gwl_fraction,
            "surface_mm": surface,
        })
        frames.append(out)

    if not frames:
        return None

    result = pd.concat(frames, ignore_index=True)
    result = result.sort_values(["layer", "date"]).reset_index(drop=True)
    print(f"  prediction_decomposition: {len(result)} rows")
    return result


def compute_cross_layer_consistency(recon):
    """File 5: Column-sum of per-layer predictions vs GPS surface."""
    # Pivot each layer's predictions and observations to wide format
    pred_cols = {}
    obs_cols = {}
    resid_cols = {}
    common_dates = None

    for layer in LAYERS:
        if layer not in recon:
            continue
        df = recon[layer]
        pred_cols[layer] = df.set_index("date")["b_model_mm"]
        obs_cols[layer] = df.set_index("date")["b_observed_mm"]
        # Compute residual
        resid = df.set_index("date")["b_model_mm"] - df.set_index("date")["b_observed_mm"]
        # Zero-reference at first common valid date
        valid_resid = resid.dropna()
        if len(valid_resid) > 0:
            resid = resid - valid_resid.iloc[0]
        resid_cols[layer] = resid

        if common_dates is None:
            common_dates = set(df["date"].dropna())
        else:
            common_dates = common_dates & set(df["date"].dropna())

    common_dates = sorted(common_dates)

    # Build wide-format DataFrame with both cumulative AND incremental values
    rows = []
    for date in common_dates:
        row = {"date": pd.Timestamp(date)}
        sum_pred = 0.0
        sum_obs = 0.0
        f2_inc = None
        f3_inc = None

        for layer in LAYERS:
            p = float(pred_cols[layer].get(date, np.nan)) if layer in pred_cols and date in pred_cols[layer].index else np.nan
            o = float(obs_cols[layer].get(date, np.nan)) if layer in obs_cols and date in obs_cols[layer].index else np.nan
            r = float(resid_cols[layer].get(date, np.nan)) if layer in resid_cols and date in resid_cols[layer].index else np.nan

            row[f"{layer}_pred_mm"] = p
            row[f"{layer}_obs_mm"] = o
            row[f"{layer}_residual_mm"] = r

            if not pd.isna(p):
                sum_pred += p
            if not pd.isna(o):
                sum_obs += o

        row["sum_layer_pred_mm"] = sum_pred
        row["sum_layer_obs_mm"] = sum_obs
        row["column_mismatch_mm"] = sum_pred - sum_obs
        rows.append(row)

    result = pd.DataFrame(rows)
    result = result.sort_values("date").reset_index(drop=True)

    # Compute INCREMENTAL F2/F3 signs for anti-phase detection
    for layer in ["F2", "F3"]:
        col = f"{layer}_obs_mm"
        if col in result.columns:
            result[f"{layer}_inc_mm"] = result[col].diff()

    f2_inc = result.get("F2_inc_mm", pd.Series(np.nan, index=result.index))
    f3_inc = result.get("F3_inc_mm", pd.Series(np.nan, index=result.index))
    result["f2_f3_anti_phase"] = (
        (f2_inc.abs() > SIGN_ERROR_THRESHOLD_MM) &
        (f3_inc.abs() > SIGN_ERROR_THRESHOLD_MM) &
        (np.sign(f2_inc) != np.sign(f3_inc))
    )

    # Which layer contributed most (cumulative)
    for _, row in result.iterrows():
        layer_contribs = {}
        for layer in LAYERS:
            o = row.get(f"{layer}_obs_mm", np.nan)
            if not pd.isna(o):
                layer_contribs[layer] = o
        if layer_contribs:
            result.at[_, "max_positive_layer"] = max(layer_contribs, key=layer_contribs.get)
            result.at[_, "max_rebound_layer"] = min(layer_contribs, key=layer_contribs.get)
    anti_phase_rate = result["f2_f3_anti_phase"].mean() if "f2_f3_anti_phase" in result.columns else 0
    print(f"  cross_layer_consistency: {len(result)} epochs, F2/F3 anti-phase rate = {anti_phase_rate:.3f}")
    return result


def compute_drift_diagnostics(residuals_df, regime_df, windows=None):
    """File 6: Cumulative residual drift over rolling windows."""
    if residuals_df is None:
        return None
    if windows is None:
        windows = DRIFT_WINDOWS

    frames = []
    for layer in LAYERS:
        ldf = residuals_df[residuals_df["layer"] == layer].copy()
        ldf = ldf.sort_values("date").reset_index(drop=True)

        for w in windows:
            cum_resid = ldf["cum_residual_mm"].values
            n = len(cum_resid)

            drift_mm = np.full(n, np.nan)
            drift_rate_epoch = np.full(n, np.nan)

            for i in range(w, n):
                segment = cum_resid[i - w : i]
                valid = ~np.isnan(segment)
                if valid.sum() < max(10, w // 4):
                    continue
                t = np.arange(len(segment))[valid]
                y = segment[valid]
                if len(t) >= 10:
                    slope = np.polyfit(t, y, 1)[0]
                    drift_rate_epoch[i] = slope
                    drift_mm[i] = y[-1] - y[0] if len(y) >= 2 else np.nan

            # Count observed epochs in each window
            is_obs = ldf["is_observed"].values
            n_obs_in_window = np.full(n, np.nan)
            for i in range(w, n):
                n_obs_in_window[i] = is_obs[i - w : i].sum()

            # Merge regime info
            frac_inelastic = np.full(n, np.nan)
            if regime_df is not None:
                rdf = regime_df[regime_df["layer"] == layer]
                if len(rdf) > 0:
                    inelastic_arr = (rdf["regime"] == "inelastic").values
                    for i in range(w, n):
                        seg = inelastic_arr[max(0, i - w) : i]
                        if len(seg) > 0:
                            frac_inelastic[i] = seg.mean()

            temp = pd.DataFrame({
                "date": ldf["date"].values,
                "layer": layer,
                "window_size_epochs": w,
                "drift_mm": drift_mm,
                "drift_rate_mm_per_epoch": drift_rate_epoch,
                "drift_rate_mm_per_year": drift_rate_epoch * (365.25 / 5),  # 5-day cadence → annual
                "n_observed_in_window": n_obs_in_window,
                "fraction_inelastic_in_window": frac_inelastic,
            })
            frames.append(temp)

    if not frames:
        return None

    result = pd.concat(frames, ignore_index=True)
    result = result.sort_values(["layer", "window_size_epochs", "date"]).reset_index(drop=True)
    print(f"  drift_diagnostics: {len(result)} rows")
    return result


def compute_seq_innovation_detail(seq_data, transp_data, seq_metrics):
    """File 7: Signed innovation data per scoring point across all cadences."""
    rows = []
    for (cadence, layer), seq_df in seq_data.items():
        # Merge with transparency data to get obs_verified_mm
        if layer in transp_data:
            tdf = transp_data[layer][["date", "obs_verified_mm", "is_reveal"]].copy()
            merged = seq_df.merge(tdf, on="date", how="left")
        else:
            merged = seq_df.copy()
            merged["obs_verified_mm"] = np.nan
            merged["is_reveal"] = False

        # At reveal dates, obs_verified_mm is the true observation
        # pred_mm is the pre-reveal prediction
        # innovation = pred - obs (signed)
        merged["innovation_mm"] = np.where(
            merged["is_reveal"],
            merged["pred_mm"] - merged["obs_verified_mm"],
            np.nan,
        )

        # Check band coverage
        if "half_width_mm" in merged.columns and "is_reveal" in merged.columns:
            merged["band_lo"] = merged["pred_mm"] - merged["half_width_mm"]
            merged["band_hi"] = merged["pred_mm"] + merged["half_width_mm"]
            merged["in_band"] = np.where(
                merged["is_reveal"],
                (merged["obs_verified_mm"] >= merged["band_lo"]) &
                (merged["obs_verified_mm"] <= merged["band_hi"]),
                np.nan,
            )
        elif "is_reveal" in merged.columns:
            # Get in_band from metrics.json innovations
            merged["in_band"] = np.nan
            if cadence in seq_metrics:
                m = seq_metrics[cadence]
                innovations = m.get("layers", {}).get(layer, {}).get("innovations", [])
                inn_dict = {pd.Timestamp(i["date"]): i.get("in_band", np.nan) for i in innovations}
                merged["in_band"] = merged["date"].map(inn_dict)

        # Filter to scoring points only (where is_reveal or innovation exists)
        scoring = merged[merged["is_reveal"] | merged["innovation_mm"].notna()].copy()

        for _, r in scoring.iterrows():
            rows.append({
                "date": r["date"],
                "layer": layer,
                "cadence": cadence,
                "obs_mm": r.get("obs_verified_mm", np.nan),
                "pred_mm": r.get("pred_mm", np.nan),
                "innovation_mm": r.get("innovation_mm", np.nan),
                "in_band": r.get("in_band", np.nan),
                "half_width_mm": r.get("half_width_mm", np.nan),
                "horizon_epochs": r.get("horizon_epochs", np.nan),
                "is_visit": r.get("is_reveal", False),
            })

    if not rows:
        print("  WARNING: No seq innovation data found")
        return None

    result = pd.DataFrame(rows)
    result = result.sort_values(["cadence", "layer", "date"]).reset_index(drop=True)
    n_signed = result["innovation_mm"].notna().sum()
    print(f"  seq_innovation_detail: {len(result)} scoring points, {n_signed} with signed innovation")
    return result


def build_auditor_summary(residuals_df, sign_error_df, regime_df, decomp_df,
                          cross_df, drift_df, seq_innovation_df):
    """File 8: JSON anomaly registry with pre-computed flags."""
    summary = {
        "metadata": {
            "station": STATION,
            "export_date": str(pd.Timestamp.now()),
            "sign_error_threshold_mm": SIGN_ERROR_THRESHOLD_MM,
            "blind_era_start": str(BLIND_ERA_START),
        },
        "global": {},
        "per_layer": {},
        "cross_layer": {},
        "regime": {},
    }

    # ── Global stats ──
    if residuals_df is not None:
        valid = residuals_df.dropna(subset=["residual_mm"])
        summary["global"]["n_total_epochs"] = len(residuals_df)
        summary["global"]["n_sign_errors"] = int(residuals_df["sign_error"].sum())
        summary["global"]["sign_error_rate"] = float(
            residuals_df["sign_error"].sum() / max(len(valid), 1)
        )
        summary["global"]["median_abs_residual_mm"] = float(valid["abs_residual_mm"].median())
        summary["global"]["p95_abs_residual_mm"] = float(valid["abs_residual_mm"].quantile(0.95))

    if drift_df is not None:
        valid_d = drift_df.dropna(subset=["drift_rate_mm_per_year"])
        summary["global"]["median_drift_rate_mm_per_year"] = float(
            valid_d["drift_rate_mm_per_year"].median()
        )
        summary["global"]["p95_drift_rate_mm_per_year"] = float(
            valid_d["drift_rate_mm_per_year"].abs().quantile(0.95)
        )

    if cross_df is not None:
        summary["global"]["column_mismatch_p95_mm"] = float(
            cross_df["column_mismatch_mm"].abs().quantile(0.95)
        )

    # ── Per-layer stats ──
    for layer in LAYERS:
        pinfo = {
            "sign_error_rate": None,
            "median_residual_mm": None,
            "bias_mm": None,
            "drift_rate_mm_per_year": None,
            "amplitude_ratio": None,
            "n_regime_mismatch_epochs": None,
            "regime_mismatch_rate": None,
            "fraction_elastic": None,
            "fraction_inelastic": None,
            "top_10_sign_error_dates": [],
            "top_10_largest_residual_dates": [],
            "top_5_drift_events": [],
        }

        if residuals_df is not None:
            ldf = residuals_df[residuals_df["layer"] == layer].dropna(subset=["residual_mm"])
            if len(ldf) > 0:
                pinfo["sign_error_rate"] = float(ldf["sign_error"].mean())
                pinfo["median_residual_mm"] = float(ldf["residual_mm"].median())
                pinfo["bias_mm"] = float(ldf["residual_mm"].mean())

                # Top 10 by abs residual
                top10 = ldf.nlargest(10, "abs_residual_mm")
                pinfo["top_10_largest_residual_dates"] = [
                    {"date": str(d), "residual_mm": float(r), "obs_inc_mm": float(o), "pred_inc_mm": float(p)}
                    for d, r, o, p in zip(top10["date"], top10["residual_mm"],
                                          top10["obs_inc_mm"], top10["pred_inc_mm"])
                ]

            # Top 10 sign errors
            if sign_error_df is not None:
                sdf = sign_error_df[sign_error_df["layer"] == layer]
                top_s = sdf.nlargest(10, "abs_residual_mm") if "abs_residual_mm" in sdf.columns else sdf.head(10)
                pinfo["top_10_sign_error_dates"] = [
                    {"date": str(d), "error_type": e, "obs_inc_mm": float(o), "pred_inc_mm": float(p)}
                    for d, e, o, p in zip(top_s["date"], top_s["error_type"],
                                          top_s["obs_inc_mm"], top_s["pred_inc_mm"])
                ]

        if regime_df is not None:
            rdf = regime_df[regime_df["layer"] == layer]
            if len(rdf) > 0:
                pinfo["n_regime_mismatch_epochs"] = int((~rdf["expected_sign_match"]).sum())
                pinfo["regime_mismatch_rate"] = float((~rdf["expected_sign_match"]).mean())
                pinfo["fraction_elastic"] = float((rdf["regime"] == "elastic").mean())
                pinfo["fraction_inelastic"] = float((rdf["regime"] == "inelastic").mean())

        if drift_df is not None:
            ddf = drift_df[(drift_df["layer"] == layer) & (drift_df["window_size_epochs"] == 72)]
            ddf = ddf.dropna(subset=["drift_rate_mm_per_year"])
            if len(ddf) > 0:
                pinfo["drift_rate_mm_per_year"] = float(ddf["drift_rate_mm_per_year"].median())
                # Top 5 drift events
                top_d = ddf.nlargest(5, "drift_rate_mm_per_year")
                pinfo["top_5_drift_events"] = [
                    {"date": str(d), "drift_rate_mm_per_year": float(r), "direction": "underpredict" if r > 0 else "overpredict"}
                    for d, r in zip(top_d["date"], top_d["drift_rate_mm_per_year"])
                ]

        summary["per_layer"][layer] = pinfo

    # ── Cross-layer stats ──
    if cross_df is not None:
        summary["cross_layer"]["f2_f3_anti_phase_rate"] = float(
            cross_df["f2_f3_anti_phase"].mean()
        ) if "f2_f3_anti_phase" in cross_df.columns else None
        summary["cross_layer"]["column_closure_error_p95_mm"] = float(
            cross_df["column_mismatch_mm"].abs().quantile(0.95)
        )
        cross_df_abs = cross_df.copy()
        cross_df_abs["_abs_mismatch"] = cross_df_abs["column_mismatch_mm"].abs().fillna(0)
        worst = cross_df_abs.nlargest(10, "_abs_mismatch")
        summary["cross_layer"]["worst_closure_dates"] = [
            {"date": str(d), "mismatch_mm": float(m)}
            for d, m in zip(worst["date"], worst["column_mismatch_mm"])
        ]

    # ── Regime anomaly stats ──
    if regime_df is not None:
        rdf = regime_df.dropna(subset=["head_change_m", "obs_inc_mm"])
        head_fell = rdf["head_change_m"] < -0.001
        head_rose = rdf["head_change_m"] > 0.001
        compacting = rdf["obs_inc_mm"] < -SIGN_ERROR_THRESHOLD_MM
        rebounding = rdf["obs_inc_mm"] > SIGN_ERROR_THRESHOLD_MM

        fell_but_rebound = rdf[head_fell & rebounding]
        rose_but_compact = rdf[head_rose & compacting]

        summary["regime"]["epochs_with_head_fell_but_rebound"] = [
            {"date": str(d), "layer": l, "head_change_m": float(h), "obs_inc_mm": float(o)}
            for d, l, h, o in zip(fell_but_rebound["date"], fell_but_rebound["layer"],
                                  fell_but_rebound["head_change_m"], fell_but_rebound["obs_inc_mm"])
        ][:50]

        summary["regime"]["epochs_with_head_rose_but_compaction"] = [
            {"date": str(d), "layer": l, "head_change_m": float(h), "obs_inc_mm": float(o)}
            for d, l, h, o in zip(rose_but_compact["date"], rose_but_compact["layer"],
                                  rose_but_compact["head_change_m"], rose_but_compact["obs_inc_mm"])
        ][:50]

    # ── Seq coverage summary ──
    if seq_innovation_df is not None:
        coverage = {}
        for cadence in CADENCES:
            cdf = seq_innovation_df[seq_innovation_df["cadence"] == cadence]
            cov_layer = {}
            for layer in LAYERS:
                ldf = cdf[cdf["layer"] == layer]
                if len(ldf) > 0:
                    cov_layer[layer] = {
                        "n_points": len(ldf),
                        "in_band_fraction": float(ldf["in_band"].mean()) if "in_band" in ldf.columns else None,
                        "mean_signed_innovation_mm": float(ldf["innovation_mm"].mean()) if "innovation_mm" in ldf.columns else None,
                        "p95_abs_innovation_mm": float(ldf["innovation_mm"].abs().quantile(0.95)) if "innovation_mm" in ldf.columns else None,
                    }
            coverage[cadence] = cov_layer
        summary["seq_coverage"] = coverage

    print(f"  auditor_summary: built with {len(summary['per_layer'])} layers, "
          f"{len(summary.get('seq_coverage', {}))} cadences")
    return summary


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3: Figure Generation
# ═══════════════════════════════════════════════════════════════════════════════

# Shared style constants
LAYER_COLORS = {
    "F1": "#1f77b4", "T1": "#ff7f0e", "F2": "#2ca02c",
    "T2": "#d62728", "F3": "#9467bd", "F4": "#8c564b",
}
ERROR_COLORS = {"sign_reversal": "#d62728", "overpredict": "#ff7f0e",
                "underpredict": "#1f77b4", "obs_flat": "#7f7f7f", "unknown": "#7f7f7f"}
REGIME_COLORS = {"elastic": "#1f77b4", "inelastic": "#d62728"}


def _save_fig(fig, path):
    """Save figure with consistent settings, close to free memory."""
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_residuals(df, output_dir):
    """Figure 1: 6-panel per-layer obs/pred + residuals."""
    if df is None:
        return
    fig, axes = plt.subplots(6, 2, figsize=(18, 22), sharex="col",
                             gridspec_kw={"width_ratios": [3, 3], "hspace": 0.35, "wspace": 0.08})

    for i, layer in enumerate(LAYERS):
        ldf = df[df["layer"] == layer].dropna(subset=["obs_inc_mm", "pred_inc_mm"])
        if len(ldf) == 0:
            continue

        ax_top = axes[i, 0]
        ax_bot = axes[i, 1]

        # Top: obs vs pred
        dates = ldf["date"]
        ax_top.plot(dates, ldf["obs_inc_mm"], color="black", linewidth=0.6, alpha=0.8, label="Observed")
        ax_top.plot(dates, ldf["pred_inc_mm"], color=LAYER_COLORS[layer], linewidth=0.6, alpha=0.8, label="Predicted")
        ax_top.axhline(y=0, color="gray", linewidth=0.5, linestyle="--")
        ax_top.set_ylabel(f"{layer}\n[mm]", fontsize=8)
        ax_top.legend(fontsize=6, loc="upper right")
        ax_top.grid(True, alpha=0.3)

        # Shade blind era
        ax_top.axvspan(BLIND_ERA_START, ldf["date"].max(), alpha=0.08, color="red")
        ax_bot.axvspan(BLIND_ERA_START, ldf["date"].max(), alpha=0.08, color="red")

        # Bottom: residuals
        ax_bot.plot(dates, ldf["residual_mm"], color="gray", linewidth=0.4, alpha=0.6)
        # Mark sign errors
        se = ldf[ldf["sign_error"]]
        if len(se) > 0:
            ax_bot.scatter(se["date"], se["residual_mm"], color="red", s=4, alpha=0.6, zorder=5)
        ax_bot.axhline(y=0, color="black", linewidth=0.5, linestyle="-")
        ax_bot.set_ylabel(f"{layer}\nresidual [mm]", fontsize=8)
        ax_bot.grid(True, alpha=0.3)

    axes[-1, 0].set_xlabel("Date")
    axes[-1, 1].set_xlabel("Date")
    fig.suptitle("File 1: Per-Epoch Observed vs Predicted Compaction with Residuals", fontsize=11, y=1.01)
    _save_fig(fig, output_dir / "per_epoch_residuals.png")
    print("  Figure: per_epoch_residuals.png")


def fig_sign_errors(df, output_dir):
    """Figure 2: Sign-error summary bar chart + scatter plot."""
    if df is None:
        return
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    # Left: bar chart of sign-error counts per layer
    counts = {}
    for layer in LAYERS:
        ldf = df[df["layer"] == layer]
        counts[layer] = len(ldf)
        total = len(df[df["layer"] == layer]) if layer in df["layer"].values else 0

    bars = ax1.bar(LAYERS, [counts.get(l, 0) for l in LAYERS],
                   color=[LAYER_COLORS[l] for l in LAYERS], edgecolor="white")
    for bar, layer in zip(bars, LAYERS):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                 str(counts.get(layer, 0)), ha="center", fontsize=9)
    ax1.set_ylabel("Number of problematic epochs")
    ax1.set_title("Sign-error / misprediction count per layer")
    ax1.grid(True, alpha=0.3, axis="y")

    # Right: scatter of problematic epochs by date, colored by layer
    for layer in LAYERS:
        ldf = df[df["layer"] == layer]
        if len(ldf) == 0:
            continue
        is_blind = ldf["date"] >= BLIND_ERA_START
        ax2.scatter(ldf.loc[~is_blind, "date"], ldf.loc[~is_blind, "magnitude_ratio"],
                   color=LAYER_COLORS[layer], s=8, alpha=0.4, label=f"{layer} (pre-blind)")
        ax2.scatter(ldf.loc[is_blind, "date"], ldf.loc[is_blind, "magnitude_ratio"],
                   color=LAYER_COLORS[layer], s=12, alpha=0.8, edgecolors="black", linewidth=0.5,
                   label=f"{layer} (blind-era)")
    ax2.axhline(y=1.0, color="black", linewidth=0.8, linestyle="--", alpha=0.5)
    ax2.set_ylabel("Magnitude ratio |pred| / |obs|")
    ax2.set_title("Problematic epochs: magnitude ratio vs date")
    ax2.set_yscale("log")
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=7, ncol=2, loc="upper left")

    fig.suptitle("File 2: Sign-Error Log Summary", fontsize=11, y=1.01)
    _save_fig(fig, output_dir / "sign_error_log.png")
    print("  Figure: sign_error_log.png")


def fig_regime(df, output_dir):
    """Figure 3: 6-panel per-layer head + regime classification."""
    if df is None:
        return
    fig, axes = plt.subplots(6, 2, figsize=(18, 22), sharex="col",
                             gridspec_kw={"width_ratios": [3, 3], "hspace": 0.35, "wspace": 0.08})

    for i, layer in enumerate(LAYERS):
        ldf = df[df["layer"] == layer].dropna(subset=["head_m_msl"])
        if len(ldf) == 0:
            continue

        ax_top = axes[i, 0]
        ax_bot = axes[i, 1]

        dates = ldf["date"]

        # Top: head timeseries colored by regime
        elastic = ldf["regime"] == "elastic"
        inelastic = ldf["regime"] == "inelastic"

        ax_top.plot(dates[elastic], ldf.loc[elastic, "head_m_msl"],
                   color=REGIME_COLORS["elastic"], linewidth=0.6, alpha=0.8)
        ax_top.plot(dates[inelastic], ldf.loc[inelastic, "head_m_msl"],
                   color=REGIME_COLORS["inelastic"], linewidth=0.6, alpha=0.8)

        # h_c reference line
        h_c = ldf["h_c_m"].iloc[0] if not pd.isna(ldf["h_c_m"].iloc[0]) else None
        if h_c is not None:
            ax_top.axhline(y=h_c, color="red", linewidth=0.8, linestyle="--", alpha=0.5, label=f"$h_c$ = {h_c:.1f} m")
            ax_top.legend(fontsize=6)

        # Shade inelastic regions
        inel_starts = dates[inelastic & ~inelastic.shift(1).fillna(False)]
        inel_ends = dates[inelastic & ~inelastic.shift(-1).fillna(False)]
        for s, e in zip(inel_starts, inel_ends):
            ax_top.axvspan(s, e, alpha=0.06, color="red")
            ax_bot.axvspan(s, e, alpha=0.06, color="red")

        ax_top.set_ylabel(f"{layer}\nhead [m MSL]", fontsize=8)
        ax_top.grid(True, alpha=0.3)

        # Bottom: observed compaction colored by regime, with mismatch markers
        obs_inc = ldf["obs_inc_mm"]
        ax_bot.plot(dates[elastic], obs_inc[elastic], color=REGIME_COLORS["elastic"],
                   linewidth=0.4, alpha=0.6)
        ax_bot.plot(dates[inelastic], obs_inc[inelastic], color=REGIME_COLORS["inelastic"],
                   linewidth=0.4, alpha=0.6)
        ax_bot.axhline(y=0, color="gray", linewidth=0.5, linestyle="--")

        # Mismatch markers
        mismatch = ldf[~ldf["expected_sign_match"]]
        if len(mismatch) > 0:
            ax_bot.scatter(mismatch["date"], mismatch["obs_inc_mm"],
                          color="red", marker="x", s=10, alpha=0.7, zorder=5)

        ax_bot.set_ylabel(f"{layer}\nobs inc [mm]", fontsize=8)
        ax_bot.grid(True, alpha=0.3)

        # Shade blind era
        ax_top.axvspan(BLIND_ERA_START, ldf["date"].max(), alpha=0.08, color="orange")
        ax_bot.axvspan(BLIND_ERA_START, ldf["date"].max(), alpha=0.08, color="orange")

    axes[-1, 0].set_xlabel("Date")
    axes[-1, 1].set_xlabel("Date")
    fig.suptitle("File 3: Per-Layer Regime Classification & Head-Compaction Consistency", fontsize=11, y=1.01)
    _save_fig(fig, output_dir / "per_layer_regime_epochs.png")
    print("  Figure: per_layer_regime_epochs.png")


def fig_decomposition(df, output_dir):
    """Figure 4: 6-panel stacked-area decomposition of predictions."""
    if df is None:
        return
    fig, axes = plt.subplots(6, 1, figsize=(18, 22), sharex=True)

    for i, layer in enumerate(LAYERS):
        ldf = df[df["layer"] == layer].dropna(subset=["total_pred_mm"])
        if len(ldf) == 0:
            continue

        ax = axes[i]
        dates = ldf["date"]

        # Stacked area: carrier + GWL components (cumulative, zero-referenced)
        carrier = ldf["carrier_term_mm"].values
        gwl = ldf["gwl_term_mm"].values
        total = ldf["total_pred_mm"].values
        obs = ldf["obs_mm"].values

        # Zero-reference at first valid
        first_valid = np.where(~np.isnan(total))[0]
        if len(first_valid) > 0:
            idx0 = first_valid[0]
            ref_c = carrier[idx0] if not np.isnan(carrier[idx0]) else 0
            ref_g = gwl[idx0] if not np.isnan(gwl[idx0]) else 0
            ref_t = total[idx0] if not np.isnan(total[idx0]) else 0
            ref_o = obs[idx0] if not np.isnan(obs[idx0]) else 0
            carrier_zr = carrier - ref_c
            gwl_zr = gwl - ref_g
            total_zr = total - ref_t
            obs_zr = obs - ref_o
        else:
            carrier_zr = carrier
            gwl_zr = gwl
            total_zr = total
            obs_zr = obs

        # Plot carrier as area below zero, GWL as area from carrier
        ax.fill_between(dates, 0, carrier_zr, color="#1f77b4", alpha=0.5, label="Carrier (a·d_GPS)")
        ax.fill_between(dates, carrier_zr, total_zr, color="#ff7f0e", alpha=0.5, label="GWL residual (d·u)")
        ax.plot(dates, obs_zr, color="black", linewidth=1.0, label="Observed")
        ax.plot(dates, total_zr, color="#d62728", linewidth=0.5, alpha=0.7, label="Total predicted")

        ax.axhline(y=0, color="gray", linewidth=0.5, linestyle="--")
        ax.axvspan(BLIND_ERA_START, ldf["date"].max(), alpha=0.08, color="red")

        ax.set_ylabel(f"{layer}\ncum. [mm]", fontsize=8)
        ax.grid(True, alpha=0.3)

        # R² annotation
        valid_mask = ~np.isnan(obs_zr) & ~np.isnan(carrier_zr)
        if valid_mask.sum() > 10:
            r2 = np.corrcoef(obs_zr[valid_mask], carrier_zr[valid_mask])[0, 1] ** 2
            ax.text(0.02, 0.95, f"R²(carrier vs obs) = {r2:.3f}", transform=ax.transAxes,
                   fontsize=7, verticalalignment="top", bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.7))

        if i == 0:
            ax.legend(fontsize=7, ncol=4, loc="upper right")

    axes[-1].set_xlabel("Date")
    fig.suptitle("File 4: Prediction Decomposition — Carrier vs GWL Components", fontsize=11, y=1.01)
    _save_fig(fig, output_dir / "prediction_decomposition.png")
    print("  Figure: prediction_decomposition.png")


def fig_cross_layer(df, output_dir):
    """Figure 5: Column-sum vs GPS surface, plus per-layer stacked contributions."""
    if df is None:
        return
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 12), sharex=True)

    dates = df["date"]

    # Top: cumulative sum_layer_pred vs gps_surface
    sum_pred = df["sum_layer_pred_mm"].values
    sum_obs = df["sum_layer_obs_mm"].values

    # Zero-reference
    valid_idx = np.where(~np.isnan(sum_pred) & ~np.isnan(sum_obs))[0]
    if len(valid_idx) > 0:
        ref_p = sum_pred[valid_idx[0]]
        ref_o = sum_obs[valid_idx[0]]
        sum_pred_zr = sum_pred - ref_p
        sum_obs_zr = sum_obs - ref_o
    else:
        sum_pred_zr = sum_pred
        sum_obs_zr = sum_obs

    ax1.plot(dates, sum_pred_zr, color="#1f77b4", linewidth=1.0, label="Sum of 6 layer predictions")
    ax1.plot(dates, sum_obs_zr, color="black", linewidth=1.0, label="Sum of 6 layer observations")
    ax1.fill_between(dates, sum_pred_zr, sum_obs_zr, alpha=0.15, color="red")
    ax1.axhline(y=0, color="gray", linewidth=0.5, linestyle="--")
    ax1.axvspan(BLIND_ERA_START, df["date"].max(), alpha=0.08, color="red")
    ax1.set_ylabel("Cumulative sum [mm]")
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3)
    ax1.set_title("Column-sum: Σ layers vs GPS surface displacement")

    # Bottom: stacked per-layer obs contributions
    layer_data = {}
    for layer in LAYERS:
        col = f"{layer}_obs_mm"
        if col in df.columns:
            vals = df[col].values
            # Zero-reference
            v_idx = np.where(~np.isnan(vals))[0]
            if len(v_idx) > 0:
                vals = vals - vals[v_idx[0]]
            layer_data[layer] = vals

    # Plot as stacked area
    if layer_data:
        cum_bottom = np.zeros(len(df))
        for layer in LAYERS:
            if layer in layer_data:
                vals = np.nan_to_num(layer_data[layer], nan=0)
                ax2.fill_between(dates, cum_bottom, cum_bottom + vals,
                                color=LAYER_COLORS[layer], alpha=0.6, label=layer)
                cum_bottom = cum_bottom + vals

    ax2.axhline(y=0, color="gray", linewidth=0.5, linestyle="--")
    ax2.axvspan(BLIND_ERA_START, df["date"].max(), alpha=0.08, color="red")
    ax2.set_ylabel("Cumulative per-layer obs [mm]")
    ax2.set_xlabel("Date")
    ax2.legend(fontsize=8, ncol=6, loc="lower left")
    ax2.grid(True, alpha=0.3)

    # F2/F3 anti-phase rate annotation
    anti_rate = df["f2_f3_anti_phase"].mean() if "f2_f3_anti_phase" in df.columns else 0
    ax2.text(0.98, 0.95, f"F2/F3 anti-phase rate = {anti_rate:.2%}", transform=ax2.transAxes,
            fontsize=9, ha="right", va="top", bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.7))

    fig.suptitle("File 5: Cross-Layer Consistency — Column Closure & Per-Layer Contributions", fontsize=11, y=1.01)
    _save_fig(fig, output_dir / "cross_layer_consistency.png")
    print("  Figure: cross_layer_consistency.png")


def fig_drift(df, output_dir):
    """Figure 6: 6-panel per-layer cumulative residual drift."""
    if df is None:
        return
    fig, axes = plt.subplots(6, 1, figsize=(18, 22), sharex=True)

    for i, layer in enumerate(LAYERS):
        ax = axes[i]
        # Use 72-epoch (1-year) window
        ldf = df[(df["layer"] == layer) & (df["window_size_epochs"] == 72)]

        if len(ldf) == 0:
            continue

        dates = ldf["date"]
        drift_rate = ldf["drift_rate_mm_per_year"].values

        ax.plot(dates, drift_rate, color="black", linewidth=0.8)
        ax.axhline(y=0, color="black", linewidth=0.5, linestyle="-")
        ax.axhline(y=1, color="green", linewidth=0.5, linestyle="--", alpha=0.4)
        ax.axhline(y=-1, color="green", linewidth=0.5, linestyle="--", alpha=0.4)
        ax.axhline(y=3, color="orange", linewidth=0.5, linestyle="--", alpha=0.5)
        ax.axhline(y=-3, color="orange", linewidth=0.5, linestyle="--", alpha=0.5)
        ax.axhline(y=5, color="red", linewidth=0.5, linestyle="--", alpha=0.5)
        ax.axhline(y=-5, color="red", linewidth=0.5, linestyle="--", alpha=0.5)

        ax.axvspan(BLIND_ERA_START, dates.max(), alpha=0.08, color="red")

        # Fill between ±1, ±3, ±5 bands
        ax.fill_between(dates, -1, 1, alpha=0.05, color="green")
        ax.fill_between(dates, -3, -1, alpha=0.03, color="orange")
        ax.fill_between(dates, 1, 3, alpha=0.03, color="orange")

        p95 = np.nanpercentile(np.abs(drift_rate), 95) if len(drift_rate[~np.isnan(drift_rate)]) > 0 else 8
        ylim = max(min(p95, 20), 5)  # cap at 20, floor at 5
        if np.isnan(ylim) or np.isinf(ylim):
            ylim = 8
        ax.set_ylim(-ylim, ylim)
        ax.set_ylabel(f"{layer}\ndrift [mm/yr]", fontsize=8)
        ax.grid(True, alpha=0.3)

        # Annotate peak drift
        valid_dr = drift_rate[~np.isnan(drift_rate)]
        if len(valid_dr) > 0:
            peak_idx_global = np.nanargmax(np.abs(drift_rate))
            if not pd.isna(drift_rate[peak_idx_global]):
                ax.annotate(f"{drift_rate[peak_idx_global]:.1f} mm/yr\n{dates.iloc[peak_idx_global].strftime('%Y-%m')}",
                           xy=(dates.iloc[peak_idx_global], drift_rate[peak_idx_global]),
                           fontsize=7, ha="center",
                           arrowprops=dict(arrowstyle="->", color="red", lw=0.8))

        if i == 0:
            # Legend-like text
            ax.text(0.01, 0.98, "Green band: ±1 mm/yr (acceptable)\nOrange band: ±3 mm/yr (concerning)\nRed lines: ±5 mm/yr (critical)",
                   transform=ax.transAxes, fontsize=7, va="top",
                   bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))

    axes[-1].set_xlabel("Date")
    fig.suptitle("File 6: Drift Diagnostics — 1-Year Rolling Cumulative Residual Drift Rate", fontsize=11, y=1.01)
    _save_fig(fig, output_dir / "drift_diagnostics.png")
    print("  Figure: drift_diagnostics.png")


def fig_seq_innovation(df, output_dir):
    """Figure 7: 6-panel signed innovation scatter across cadences."""
    if df is None:
        return
    n_cadences = len(df["cadence"].unique()) if "cadence" in df.columns else 0
    if n_cadences == 0:
        return

    cadences_present = [c for c in CADENCES if c in df["cadence"].values]
    fig, axes = plt.subplots(len(cadences_present), 1, figsize=(16, 4 * len(cadences_present)), sharex=True)
    if len(cadences_present) == 1:
        axes = [axes]

    for ax, cadence in zip(axes, cadences_present):
        cdf = df[df["cadence"] == cadence].dropna(subset=["innovation_mm"])

        for layer in LAYERS:
            ldf = cdf[cdf["layer"] == layer]
            if len(ldf) == 0:
                continue
            ax.scatter(ldf["date"], ldf["innovation_mm"], color=LAYER_COLORS[layer],
                      s=12, alpha=0.7, label=layer, edgecolors="white", linewidth=0.3)

            # Connect F3 and F4 for drift visibility
            if layer in ["F3", "F4"] and len(ldf) > 2:
                ldf_sorted = ldf.sort_values("date")
                ax.plot(ldf_sorted["date"], ldf_sorted["innovation_mm"],
                       color=LAYER_COLORS[layer], linewidth=0.4, alpha=0.3)

        ax.axhline(y=0, color="black", linewidth=0.5, linestyle="-")
        ax.axvspan(BLIND_ERA_START, df["date"].max(), alpha=0.08, color="red")

        # Band annotation
        p95_hw = cdf["half_width_mm"].quantile(0.95) if "half_width_mm" in cdf.columns else np.nan
        if not pd.isna(p95_hw):
            ax.axhline(y=p95_hw, color="gray", linewidth=0.5, linestyle="--", alpha=0.4)
            ax.axhline(y=-p95_hw, color="gray", linewidth=0.5, linestyle="--", alpha=0.4)

        # Stats annotation
        in_band_frac = cdf["in_band"].mean() if "in_band" in cdf.columns else np.nan
        mean_innov = cdf["innovation_mm"].mean()
        p95_innov = cdf["innovation_mm"].abs().quantile(0.95)
        ax.text(0.99, 0.95,
                f"{cadence}: coverage={in_band_frac:.1%}, μ={mean_innov:+.2f} mm, p95|innov|={p95_innov:.2f} mm",
                transform=ax.transAxes, fontsize=8, ha="right", va="top",
                bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))

        ax.set_ylabel(f"{cadence}\ninnovation [mm]")
        ax.grid(True, alpha=0.3)
        if cadence == cadences_present[0]:
            ax.legend(fontsize=7, ncol=6, loc="upper right")

    axes[-1].set_xlabel("Date")
    fig.suptitle("File 7: Sequential Rehearsal — Signed Innovation per Cadence", fontsize=11, y=1.01)
    _save_fig(fig, output_dir / "seq_innovation_detail.png")
    print("  Figure: seq_innovation_detail.png")


def fig_dashboard(summary, residuals_df, sign_error_df, regime_df, drift_df,
                  seq_innovation_df, output_dir):
    """Figure 8: 6-panel auditor dashboard summary."""
    fig = plt.figure(figsize=(20, 16))
    gs = fig.add_gridspec(3, 3, hspace=0.35, wspace=0.30)

    # Panel 1: Sign-error heatmap (layers × years)
    ax1 = fig.add_subplot(gs[0, 0])
    if residuals_df is not None and sign_error_df is not None:
        residuals_df_copy = residuals_df.copy()
        residuals_df_copy["year"] = residuals_df_copy["date"].dt.year
        heatmap_data = {}
        for layer in LAYERS:
            ldf = residuals_df_copy[residuals_df_copy["layer"] == layer]
            yearly_rate = ldf.groupby("year")["sign_error"].mean()
            heatmap_data[layer] = yearly_rate
        if heatmap_data:
            hm_df = pd.DataFrame(heatmap_data).T
            hm_df = hm_df.reindex(columns=sorted(hm_df.columns))
            im = ax1.imshow(hm_df.values, aspect="auto", cmap="YlOrRd", vmin=0, vmax=0.5)
            ax1.set_xticks(range(len(hm_df.columns)))
            ax1.set_xticklabels(hm_df.columns, rotation=45, fontsize=7)
            ax1.set_yticks(range(len(LAYERS)))
            ax1.set_yticklabels(LAYERS, fontsize=8)
            plt.colorbar(im, ax=ax1, shrink=0.8, label="Sign-error rate")
            ax1.set_title("Sign-error rate by layer × year")

    # Panel 2: Residual distribution (violin)
    ax2 = fig.add_subplot(gs[0, 1])
    if residuals_df is not None:
        violin_data = []
        violin_labels = []
        for layer in LAYERS:
            vals = residuals_df[residuals_df["layer"] == layer]["residual_mm"].dropna()
            if len(vals) > 0:
                # Clip extreme outliers for visualization
                clipped = vals.clip(vals.quantile(0.01), vals.quantile(0.99))
                violin_data.append(clipped.values)
                violin_labels.append(layer)
        if violin_data:
            parts = ax2.violinplot(violin_data, showmeans=True, showmedians=True)
            ax2.set_xticks(range(1, len(violin_labels) + 1))
            ax2.set_xticklabels(violin_labels, fontsize=8)
            ax2.axhline(y=0, color="black", linewidth=0.5, linestyle="--")
            ax2.set_ylabel("Residual [mm]")
            ax2.set_title("Residual distribution per layer")
            ax2.grid(True, alpha=0.3, axis="y")

    # Panel 3: Drift-rate bar chart
    ax3 = fig.add_subplot(gs[0, 2])
    if drift_df is not None:
        drift_means = []
        drift_stds = []
        for layer in LAYERS:
            ldf = drift_df[(drift_df["layer"] == layer) & (drift_df["window_size_epochs"] == 72)]
            rates = ldf["drift_rate_mm_per_year"].dropna()
            drift_means.append(rates.median() if len(rates) > 0 else 0)
            drift_stds.append(rates.std() if len(rates) > 0 else 0)
        bars = ax3.bar(LAYERS, drift_means, color=[LAYER_COLORS[l] for l in LAYERS],
                       yerr=drift_stds, capsize=4, edgecolor="white")
        ax3.axhline(y=0, color="black", linewidth=0.5)
        ax3.set_ylabel("Median drift rate [mm/yr]")
        ax3.set_title("Annual drift rate per layer (±1σ)")
        ax3.grid(True, alpha=0.3, axis="y")

    # Panel 4: Regime mismatch bar chart
    ax4 = fig.add_subplot(gs[1, 0])
    if regime_df is not None:
        mismatch_counts = []
        for layer in LAYERS:
            ldf = regime_df[regime_df["layer"] == layer]
            mismatch_counts.append((~ldf["expected_sign_match"]).sum() if len(ldf) > 0 else 0)
        ax4.bar(LAYERS, mismatch_counts, color=[LAYER_COLORS[l] for l in LAYERS], edgecolor="white")
        ax4.set_ylabel("Count of mismatched epochs")
        ax4.set_title("Head-compaction inconsistency count per layer")
        ax4.grid(True, alpha=0.3, axis="y")

    # Panel 5: Coverage scorecard (layers × cadences)
    ax5 = fig.add_subplot(gs[1, 1])
    if seq_innovation_df is not None:
        cov_data = {}
        cadences_present = [c for c in CADENCES if c in seq_innovation_df["cadence"].values]
        for layer in LAYERS:
            cov_data[layer] = {}
            for cadence in cadences_present:
                ldf = seq_innovation_df[(seq_innovation_df["layer"] == layer) &
                                        (seq_innovation_df["cadence"] == cadence)]
                cov_data[layer][cadence] = ldf["in_band"].mean() if "in_band" in ldf.columns and len(ldf) > 0 else np.nan
        if cov_data:
            cov_df = pd.DataFrame(cov_data).T
            cov_df = cov_df.reindex(columns=cadences_present)
            im = ax5.imshow(cov_df.values, aspect="auto", cmap="RdYlGn", vmin=0, vmax=1)
            ax5.set_xticks(range(len(cov_df.columns)))
            ax5.set_xticklabels(cov_df.columns, rotation=45, fontsize=7)
            ax5.set_yticks(range(len(LAYERS)))
            ax5.set_yticklabels(LAYERS, fontsize=8)
            for i in range(len(LAYERS)):
                for j in range(len(cadences_present)):
                    val = cov_df.values[i, j]
                    color = "white" if (not pd.isna(val) and val < 0.7) else "black"
                    if not pd.isna(val):
                        ax5.text(j, i, f"{val:.0%}", ha="center", va="center", fontsize=7, color=color)
            plt.colorbar(im, ax=ax5, shrink=0.8, label="In-band fraction")
            ax5.set_title("Coverage scorecard: in-band fraction")

    # Panel 6: Top-10 anomaly table as text
    ax6 = fig.add_subplot(gs[1, 2])
    ax6.axis("off")
    if sign_error_df is not None and len(sign_error_df) > 0:
        top10 = sign_error_df.nlargest(10, "abs_residual_mm") if "abs_residual_mm" in sign_error_df.columns else sign_error_df.head(10)
        table_text = "Top 10 anomalies (by |residual|):\n\n"
        for _, row in top10.iterrows():
            d = row["date"]
            if hasattr(d, "strftime"):
                d = d.strftime("%Y-%m-%d")
            table_text += (
                f"{d} | {row['layer']} | "
                f"obs={row['obs_inc_mm']:+.2f} pred={row['pred_inc_mm']:+.2f} | "
                f"res={row['residual_mm']:+.2f} | {row['error_type']}\n"
            )
        ax6.text(0, 1, table_text, transform=ax6.transAxes, fontsize=7, va="top",
                fontfamily="monospace", bbox=dict(boxstyle="round", facecolor="white", alpha=0.9))
        ax6.set_title("Top-10 anomaly table")

    # Bottom row: key metrics summary
    ax7 = fig.add_subplot(gs[2, :])
    ax7.axis("off")
    summary_text = "GLOBAL METRICS\n" + "=" * 80 + "\n"
    g = summary.get("global", {})
    summary_text += (
        f"Sign-error rate: {g.get('sign_error_rate', 0):.2%}  |  "
        f"Median |residual|: {g.get('median_abs_residual_mm', 0):.3f} mm  |  "
        f"p95 |residual|: {g.get('p95_abs_residual_mm', 0):.3f} mm  |  "
        f"Median drift: {g.get('median_drift_rate_mm_per_year', 0):.2f} mm/yr  |  "
        f"p95 column mismatch: {g.get('column_mismatch_p95_mm', 0):.3f} mm\n\n"
    )
    summary_text += "PER-LAYER SUMMARY\n" + "-" * 80 + "\n"
    for layer in LAYERS:
        p = summary.get("per_layer", {}).get(layer, {})
        drift_val = p.get('drift_rate_mm_per_year', None)
        drift_str = f"{drift_val:+.2f}" if drift_val is not None else "N/A"
        bias_val = p.get('bias_mm', None)
        bias_str = f"{bias_val:+.3f}" if bias_val is not None else "N/A"
        summary_text += (
            f"{layer:3s}: sign_err={p.get('sign_error_rate', 0):.1%}  "
            f"bias={bias_str} mm  "
            f"drift={drift_str} mm/yr  "
            f"regime_mismatch={p.get('regime_mismatch_rate', 0):.1%}  "
            f"elastic={p.get('fraction_elastic', 0):.0%}  "
            f"inelastic={p.get('fraction_inelastic', 0):.0%}\n"
        )
    cl = summary.get("cross_layer", {})
    summary_text += (
        f"\nF2/F3 anti-phase rate: {cl.get('f2_f3_anti_phase_rate', 0):.1%}  |  "
        f"Column closure p95 error: {cl.get('column_closure_error_p95_mm', 0):.3f} mm\n"
    )
    ax7.text(0, 1, summary_text, transform=ax7.transAxes, fontsize=7.5, va="top",
            fontfamily="monospace")

    fig.suptitle("File 8: Auditor Dashboard — Anomaly Registry Summary", fontsize=13, y=1.01)
    _save_fig(fig, output_dir / "auditor_dashboard.png")
    print("  Figure: auditor_dashboard.png")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4: Main Orchestrator
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("35_export_auditor_diagnostics.py — Auditor Diagnostic Export")
    print(f"Station: {STATION}  |  Date: {pd.Timestamp.now()}")
    print("=" * 70)

    paths = resolve_paths()
    output_dir = paths["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nOutput directory: {output_dir}")

    # ── Load all data ──
    print("\n── Loading data ──")
    recon = load_reconstruction_data(paths)
    regime = load_regime_data(paths)
    provenance = load_provenance_mask(paths)
    gps_surface = load_gps_surface(paths)
    carrier_params = load_carrier_params(paths)
    storage_params = load_storage_params(paths)
    gwl_adoption = load_gwl_adoption(paths)
    seq_data = load_seq_data(paths)
    transp_data = load_transparency_data(paths)
    seq_metrics = load_seq_metrics(paths)

    # ── Compute diagnostics ──
    print("\n── Computing diagnostics ──")
    residuals_df = compute_per_epoch_residuals(recon, provenance)
    sign_error_df = compute_sign_error_log(residuals_df)
    regime_df = compute_regime_epochs(regime, recon, storage_params)
    decomp_df = compute_decomposition(recon, carrier_params, gps_surface)
    cross_df = compute_cross_layer_consistency(recon)
    drift_df = compute_drift_diagnostics(residuals_df, regime_df)
    seq_innovation_df = compute_seq_innovation_detail(seq_data, transp_data, seq_metrics)
    auditor_summary = build_auditor_summary(
        residuals_df, sign_error_df, regime_df, decomp_df,
        cross_df, drift_df, seq_innovation_df,
    )

    # ── Write CSV/JSON files ──
    print("\n── Writing CSV/JSON files ──")
    file_writes = [
        ("per_epoch_residuals.csv", residuals_df),
        ("sign_error_log.csv", sign_error_df),
        ("per_layer_regime_epochs.csv", regime_df),
        ("prediction_decomposition.csv", decomp_df),
        ("cross_layer_consistency.csv", cross_df),
        ("drift_diagnostics.csv", drift_df),
        ("seq_innovation_detail.csv", seq_innovation_df),
    ]

    for fname, df in file_writes:
        if df is not None:
            fp = output_dir / fname
            df.to_csv(fp, index=False)
            print(f"  Wrote: {fp} ({len(df)} rows)")
        else:
            print(f"  SKIPPED: {fname} (no data)")

    # Write JSON
    if auditor_summary is not None:
        fp = output_dir / "auditor_summary.json"
        with open(fp, "w") as f:
            json.dump(auditor_summary, f, indent=2, default=str)
        print(f"  Wrote: {fp}")

    # ── Generate figures ──
    print("\n── Generating figures ──")
    fig_residuals(residuals_df, output_dir)
    fig_sign_errors(sign_error_df, output_dir)
    fig_regime(regime_df, output_dir)
    fig_decomposition(decomp_df, output_dir)
    fig_cross_layer(cross_df, output_dir)
    fig_drift(drift_df, output_dir)
    fig_seq_innovation(seq_innovation_df, output_dir)
    fig_dashboard(auditor_summary, residuals_df, sign_error_df, regime_df,
                  drift_df, seq_innovation_df, output_dir)

    # ── Print summary ──
    print("\n── Summary ──")
    g = auditor_summary.get("global", {})
    print(f"  Sign-error rate:       {g.get('sign_error_rate', 0):.2%}")
    print(f"  Median |residual|:      {g.get('median_abs_residual_mm', 0):.3f} mm")
    print(f"  p95 |residual|:         {g.get('p95_abs_residual_mm', 0):.3f} mm")
    print(f"  Median drift rate:      {g.get('median_drift_rate_mm_per_year', 0):.3f} mm/yr")
    print(f"  p95 drift rate:         {g.get('p95_drift_rate_mm_per_year', 0):.3f} mm/yr")
    print(f"  p95 column mismatch:    {g.get('column_mismatch_p95_mm', 0):.3f} mm")

    print(f"\n  Per-layer bias (mm):")
    for layer in LAYERS:
        p = auditor_summary.get("per_layer", {}).get(layer, {})
        bias_v = p.get('bias_mm', None)
        drift_v = p.get('drift_rate_mm_per_year', None)
        bias_s = f"{bias_v:+.4f}" if bias_v is not None else "N/A"
        drift_s = f"{drift_v:+.3f}" if drift_v is not None else "N/A"
        print(f"    {layer}: bias={bias_s}, "
              f"sign_err={p.get('sign_error_rate', 0):.1%}, "
              f"drift={drift_s} mm/yr")

    print(f"\n  Cross-layer: F2/F3 anti-phase rate = {auditor_summary.get('cross_layer', {}).get('f2_f3_anti_phase_rate', 0):.1%}")

    # Count output files
    n_files = len(list(output_dir.glob("*")))
    print(f"\n{'=' * 70}")
    print(f"Done. {n_files} files written to {output_dir}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
