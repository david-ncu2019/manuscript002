"""
diagnose_seasonal_ske.py
========================
Tests whether a wet/dry season split of the elastic storage coefficient
S_ske improves IHM-F compaction prediction at TUKU.

Background
----------
The reference tables in data/s_ske_skv_tables.md (Tables 0-1 and 0-2) show
that S_ske estimated by 2S-TOOL differs between wet periods (Apr–Sep) and dry
periods (Oct–Mar), with variation factors of 2–10x at the same station-layer.
If this seasonal variation is real, the current single-S_ske IHM-F model is
biased: it will underestimate elastic compaction in dry seasons and
overestimate it in wet seasons.

Method
------
For each of TUKU's 6 layers (F1, T1, F2, T2, F3, F4):

  Baseline model (3 free parameters):
    db_pred = S_ke * dH_lag * I_elastic + S_kv * dH_lag * I_inelastic

  Seasonal model (4 free parameters):
    db_pred = S_ke_wet * dH_lag * I_elastic * W_wet
            + S_ke_dry * dH_lag * I_elastic * W_dry
            + S_kv     * dH_lag * I_inelastic

  where W_wet = 1 for epochs in Apr–Sep (months 4–9), W_dry = 1 - W_wet.

Both models use non-negative least squares (NNLS) so all coefficients ≥ 0.
The InSAR coupling term is omitted here because tuku_aligned_data.npz does
not contain InSAR data; the test is specifically targeting the S_ske question.

Also fits a sinusoidal model to allow a smooth seasonal modulation rather
than a binary wet/dry split.

Outputs
-------
  tau_demo_TUKU/results/seasonal_ske_diagnostics.csv
    layer, tau_opt, tau_opt_days,
    S_ke_baseline, S_kv_baseline, rmse_baseline, r2_baseline,
    S_ke_wet, S_ke_dry, ratio_dry_wet, S_kv_seasonal,
    rmse_seasonal, r2_seasonal, rmse_reduction_pct,
    S_ke_sin_mean, S_ke_sin_amp, S_ke_sin_phase_deg,
    rmse_sinusoidal, rmse_reduction_sin_pct,
    n_elastic_wet, n_elastic_dry, n_inelastic, n_epochs

  tau_demo_TUKU/results/seasonal_ske_reference.csv
    reference wet/dry S_ske values from data/s_ske_skv_tables.md for TUKU
    (layers 2.1, 2.2, 3, 4 in the reference notation)

Decision gate printed to console:
  PASS if rmse_reduction_pct > 5% for >= 3 of 6 layers
  FAIL otherwise (seasonal split does not help; document and move on)
"""

import sys
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import nnls, minimize
from scipy.stats import pearsonr

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_ROOT   = Path(__file__).resolve().parents[2]   # InSAR_MLCW_v2 root
DEMO_DIR    = REPO_ROOT / "tau_demo_TUKU"
RESULTS_DIR = DEMO_DIR / "results"

LAYERS_ORDERED = ["F1", "T1", "F2", "T2", "F3", "F4"]
WET_MONTHS = {4, 5, 6, 7, 8, 9}   # April–September (Taiwan wet season)

# ── Load aligned data ─────────────────────────────────────────────────────────
npz       = np.load(RESULTS_DIR / "tuku_aligned_data.npz", allow_pickle=True)
tau_info  = pd.read_csv(RESULTS_DIR / "tau_results.csv").set_index("layer")
baseline  = pd.read_csv(RESULTS_DIR / "reconstruction_metrics.csv").set_index("layer")


def load_layer(layer):
    d = {}
    for key in npz.files:
        if key.startswith(f"{layer}__"):
            d[key[len(f"{layer}__"):]] = npz[key]
    d["dates"]     = pd.to_datetime(d["dates"])
    d["inc_dates"] = pd.to_datetime(d["inc_dates"])
    return d


def rmse(y_true, y_pred):
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def r2(y_true, y_pred):
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    ss_tot = float(np.sum((y_true - y_true.mean()) ** 2))
    return float(1.0 - ss_res / ss_tot) if ss_tot > 0 else np.nan


# ── Reference S_ske values from data/s_ske_skv_tables.md (TUKU rows) ─────────
# Extracted from Tables 0-1 (dry) and 0-2 (wet).
# Layer mapping: ref "2.1" ≈ IHM-F F2; "2.2" ≈ F3; "3" ≈ T2/F3 boundary; "4" ≈ F4
# Values are m⁻¹. "-" entries excluded from mean.
REF_DRY = {
    "2.1": [2.16e-05, 6.05e-06, 8.65e-06, 1.96e-05, 1.76e-05, 1.63e-05, 1.48e-06],
    "2.2": [1.97e-05, 1.08e-05, 1.67e-05, 1.85e-05, 1.46e-05, 1.71e-05, 2.99e-05],
    "3":   [1.87e-05, 1.75e-05, 1.27e-05, 7.88e-06, 9.83e-06, 6.23e-06, 6.17e-06],
    "4":   [8.76e-06, 1.41e-05, 1.29e-05, 1.62e-05, 1.20e-06, 3.76e-05, 2.07e-05],
}
REF_WET = {
    "2.1": [1.30e-05, 2.44e-05, 1.67e-05, 1.54e-05, 2.60e-05, 2.95e-05, 2.76e-06, 1.44e-05],
    "2.2": [8.80e-06, 8.31e-06, 1.36e-05, 1.05e-05, 2.01e-06, 4.61e-06, 5.26e-06],  # 1.30E-04 outlier removed
    "3":   [1.72e-06, 9.31e-07, 1.90e-06, 2.20e-06, 2.09e-06, 8.10e-06, 5.99e-07],  # 1.36E-04 outlier removed
    "4":   [5.29e-05, 1.85e-05, 5.12e-05, 1.30e-05, 2.59e-05, 8.29e-06, 5.05e-06, 3.29e-06],
}


def ref_stats(layer_key):
    dry_vals = np.array(REF_DRY.get(layer_key, []))
    wet_vals = np.array(REF_WET.get(layer_key, []))
    dry_vals = dry_vals[dry_vals > 0]
    wet_vals = wet_vals[wet_vals > 0]
    mean_dry = float(np.mean(dry_vals)) if len(dry_vals) > 0 else np.nan
    mean_wet = float(np.mean(wet_vals)) if len(wet_vals) > 0 else np.nan
    ratio    = mean_dry / mean_wet if mean_wet > 0 else np.nan
    return mean_dry, mean_wet, ratio


# Save reference table as CSV
ref_rows = []
for key, ihm_layer in [("2.1", "F2"), ("2.2", "F3"), ("3", "T2/F3"), ("4", "F4")]:
    d, w, r = ref_stats(key)
    ref_rows.append(dict(
        ref_layer=key, ihm_layer_approx=ihm_layer,
        mean_dry_m_inv=round(d, 7) if not np.isnan(d) else None,
        mean_wet_m_inv=round(w, 7) if not np.isnan(w) else None,
        ratio_dry_wet=round(r, 3) if not np.isnan(r) else None,
        n_dry=len([x for x in REF_DRY.get(key, []) if x > 0]),
        n_wet=len([x for x in REF_WET.get(key, []) if x > 0]),
    ))
ref_df = pd.DataFrame(ref_rows)
ref_csv = RESULTS_DIR / "seasonal_ske_reference.csv"
ref_df.to_csv(ref_csv, index=False)
print(f"Saved reference values: {ref_csv}")
print(ref_df.to_string(index=False))
print()


# ── Main diagnostic loop ──────────────────────────────────────────────────────
all_rows = []

for layer in LAYERS_ORDERED:
    if layer not in tau_info.index:
        print(f"  {layer}: not in tau_results — skipping")
        continue

    d       = load_layer(layer)
    tau_opt = int(tau_info.loc[layer, "tau_opt"])
    inc_dH  = d["inc_dH"].astype(float)
    inc_db  = d["inc_db"].astype(float)
    inc_dates = d["inc_dates"]
    e_m     = d["e_m"].astype(bool)
    i_m     = d["i_m"].astype(bool)

    T = len(inc_dH)
    n = T - tau_opt
    if n < 10:
        print(f"  {layer}: only {n} epochs after lag — skipping")
        continue

    dH_lag  = inc_dH[tau_opt:]
    db_obs  = inc_db[:n]
    e_trim  = e_m[:n]
    i_trim  = i_m[:n]
    dates_n = inc_dates[:n]

    # Wet mask for trimmed epochs
    wet     = np.array([d.month in WET_MONTHS for d in dates_n])
    dry     = ~wet

    n_elastic_wet  = int(np.sum(e_trim & wet))
    n_elastic_dry  = int(np.sum(e_trim & dry))
    n_inelastic    = int(np.sum(i_trim))

    # ── Baseline model (no seasonal split) ───────────────────────────────────
    # NNLS with 3 predictors: [dH*e, dH*i] — no intercept to match tau_demo logic
    A_base = np.column_stack([
        dH_lag * e_trim,
        dH_lag * i_trim,
    ])
    coef_base, _ = nnls(A_base, db_obs)
    S_ke_base, S_kv_base = coef_base
    db_base = A_base @ coef_base
    rmse_base = rmse(db_obs, db_base)
    r2_base   = r2(db_obs, db_base)

    # ── Seasonal model (wet/dry S_ske split) ──────────────────────────────────
    # NNLS with 3 predictors: [dH*e*wet, dH*e*dry, dH*i]
    A_seas = np.column_stack([
        dH_lag * e_trim * wet,
        dH_lag * e_trim * dry,
        dH_lag * i_trim,
    ])
    coef_seas, _ = nnls(A_seas, db_obs)
    S_ke_wet, S_ke_dry, S_kv_seas = coef_seas
    db_seas = A_seas @ coef_seas
    rmse_seas = rmse(db_obs, db_seas)
    r2_seas   = r2(db_obs, db_seas)

    # Compute dry/wet ratio (avoid division by zero)
    if S_ke_wet > 0:
        ratio_dry_wet = round(S_ke_dry / S_ke_wet, 3)
    else:
        ratio_dry_wet = np.nan

    rmse_reduction_pct = round(100.0 * (rmse_base - rmse_seas) / rmse_base, 2) if rmse_base > 0 else 0.0

    # ── Sinusoidal model (smooth S_ske(t) = S_ke_mean * (1 + A*sin(2π*t/T + φ))) ──
    # Use DOY (day-of-year) as the seasonal index.
    doy = np.array([d.timetuple().tm_yday for d in dates_n], dtype=float)
    sin_term = np.sin(2 * np.pi * doy / 365.25)
    cos_term = np.cos(2 * np.pi * doy / 365.25)

    # Sinusoidal design: S_ke(t) = a0 + a1*sin + b1*cos (applied only to elastic epochs)
    # Predictors: [dH*e*(a0), dH*e*(a1*sin), dH*e*(b1*cos), dH*i]
    # This is linear in parameters [a0, a1, b1, S_kv] — fit via NNLS is not directly
    # applicable because a1 and b1 can be negative. Use scipy.optimize.minimize instead.
    def loss_sin(params):
        a0, a1, b1, skv = params
        ske_t = a0 + a1 * sin_term + b1 * cos_term
        ske_t = np.maximum(ske_t, 0.0)   # enforce non-negativity pointwise
        pred = dH_lag * e_trim * ske_t + dH_lag * i_trim * skv
        return float(np.sum((db_obs - pred) ** 2))

    # Initial guess from baseline
    x0 = [S_ke_base, 0.0, 0.0, S_kv_base]
    bounds_sin = [(0, None), (None, None), (None, None), (0, None)]
    res_sin = minimize(loss_sin, x0, method="L-BFGS-B", bounds=bounds_sin,
                       options={"maxiter": 500, "ftol": 1e-14})

    a0_sin, a1_sin, b1_sin, S_kv_sin = res_sin.x
    ske_t_opt = np.maximum(a0_sin + a1_sin * sin_term + b1_sin * cos_term, 0.0)
    db_sin = dH_lag * e_trim * ske_t_opt + dH_lag * i_trim * S_kv_sin
    rmse_sin = rmse(db_obs, db_sin)
    rmse_red_sin = round(100.0 * (rmse_base - rmse_sin) / rmse_base, 2) if rmse_base > 0 else 0.0

    # Amplitude and phase of sinusoidal S_ske modulation
    amp_sin   = float(np.sqrt(a1_sin**2 + b1_sin**2))
    phase_deg = float(np.degrees(np.arctan2(a1_sin, b1_sin)))   # peak at doy where sin term maxes

    print(
        f"  {layer:3s}: tau={tau_opt:2d} "
        f"| baseline RMSE={rmse_base:.5f}  R²={r2_base:.3f}"
        f"  S_ke={S_ke_base:.4f}  S_kv={S_kv_base:.4f}"
        f"\n        seasonal RMSE={rmse_seas:.5f}  R²={r2_seas:.3f}"
        f"  S_ke_wet={S_ke_wet:.4f}  S_ke_dry={S_ke_dry:.4f}  ratio={ratio_dry_wet}"
        f"  ΔRMSE={rmse_reduction_pct:+.1f}%"
        f"\n       sinusoidal RMSE={rmse_sin:.5f}  ΔRMSE={rmse_red_sin:+.1f}%"
        f"  amp={amp_sin:.4f}"
    )

    # Get baseline from reconstruction_metrics.csv if available
    rmse_prev = float(baseline.loc[layer, "RMSE"]) if layer in baseline.index else np.nan

    all_rows.append(dict(
        layer=layer,
        tau_opt=tau_opt,
        tau_opt_days=tau_opt * 5,
        # Baseline
        S_ke_baseline=round(S_ke_base, 7),
        S_kv_baseline=round(S_kv_base, 7),
        rmse_baseline=round(rmse_base, 7),
        r2_baseline=round(r2_base, 5),
        rmse_prev_reconstruction=round(rmse_prev, 7) if not np.isnan(rmse_prev) else None,
        # Seasonal split
        S_ke_wet=round(S_ke_wet, 7),
        S_ke_dry=round(S_ke_dry, 7),
        ratio_dry_wet=ratio_dry_wet,
        S_kv_seasonal=round(S_kv_seas, 7),
        rmse_seasonal=round(rmse_seas, 7),
        r2_seasonal=round(r2_seas, 5),
        rmse_reduction_pct=rmse_reduction_pct,
        # Sinusoidal model
        S_ke_sin_mean=round(a0_sin, 7),
        S_ke_sin_amp=round(amp_sin, 7),
        S_ke_sin_phase_deg=round(phase_deg, 1),
        S_kv_sinusoidal=round(S_kv_sin, 7),
        rmse_sinusoidal=round(rmse_sin, 7),
        rmse_reduction_sin_pct=rmse_red_sin,
        # Epoch counts
        n_elastic_wet=n_elastic_wet,
        n_elastic_dry=n_elastic_dry,
        n_inelastic=n_inelastic,
        n_epochs=n,
    ))

# ── Save CSV ──────────────────────────────────────────────────────────────────
out_csv = RESULTS_DIR / "seasonal_ske_diagnostics.csv"
diag_df = pd.DataFrame(all_rows)
diag_df.to_csv(out_csv, index=False)
print(f"\nSaved: {out_csv}")

# ── Decision gate ─────────────────────────────────────────────────────────────
n_pass_seasonal  = int((diag_df["rmse_reduction_pct"]   > 5.0).sum())
n_pass_sin       = int((diag_df["rmse_reduction_sin_pct"] > 5.0).sum())
n_layers         = len(diag_df)

print(f"\n{'='*60}")
print("DECISION GATE")
print(f"  Wet/dry split:    {n_pass_seasonal}/{n_layers} layers show >5% RMSE reduction")
print(f"  Sinusoidal model: {n_pass_sin}/{n_layers} layers show >5% RMSE reduction")

if n_pass_seasonal >= 3:
    print("  STATUS: PASS — seasonal S_ske split is beneficial at TUKU.")
    print("          Proceed to Step 2: update fit_ihm_f.py design matrix.")
else:
    print("  STATUS: FAIL — seasonal split does not improve prediction at ≥3 layers.")
    print("          Interpret: single S_ske adequate for OLS framework at TUKU.")
    print("          Next: diagnose whether this is due to inelastic dominance or")
    print("          signal-to-noise limitations, then document in discussion doc.")

print(f"\nDetailed results:")
print(diag_df[["layer", "rmse_baseline", "rmse_seasonal", "rmse_reduction_pct",
               "S_ke_wet", "S_ke_dry", "ratio_dry_wet",
               "rmse_sinusoidal", "rmse_reduction_sin_pct"]].to_string(index=False))
print(f"\nAll results saved to: {out_csv}")
print("Done.")
