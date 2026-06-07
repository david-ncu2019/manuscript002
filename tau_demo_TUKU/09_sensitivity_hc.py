"""
09_sensitivity_hc.py
====================
Sensitivity test: how does the preconsolidation head threshold (h_c) affect
the S_ke / S_kv ratio at TUKU?

Physical question: the current regime mask marks an epoch as inelastic whenever
head <= h_c (the historical minimum before 2015-01-16). This test checks whether
requiring ALSO that head is falling (dH < 0, a true loading increment) changes
the estimated S_kv / S_ke ratio toward the physically required 8-100x range.

Six settings tested per layer
------------------------------
1. original     — current mask: head[:n] <= h_c
2. p50          — head[:n] <= percentile(head_driver, 50)
3. p75          — head[:n] <= percentile(head_driver, 75)
4. p90          — head[:n] <= percentile(head_driver, 90)
5. bugfix       — (head[:n] <= h_c) AND (inc_dH[:n] < 0)
6. bugfix_deseas— same condition but on seasonal-removed inc_dH and inc_db

Lag-consistent convention (matches 08_reconstruction_corrected.py):
  - driver window  : indices [0 : n]       (head and inc_dH)
  - response window: indices [tau : tau+n] (inc_db)
  where  n = T - tau_opt,  T = len(inc_dH)

OLS (non-negative) for each regime independently:
  S = dot(dH, db) / dot(dH, dH)   clamped >= 0
  Unclamped slope is also reported so negative fits are visible.

R² is computed on CUMULATIVE compaction (cumsum of increments), not per-epoch,
because the user cares whether the reconstructed total uplift/subsidence tracks.

Outputs:
  results/sensitivity_hc_results.csv
  results/sensitivity_hc_results.json
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────────
DEMO_DIR    = Path(__file__).resolve().parent
RESULTS_DIR = DEMO_DIR / "results"

LAYERS_ORDERED = ["F1", "T1", "F2", "T2", "F3", "F4"]

SETTINGS = ["original", "p50", "p75", "p90", "bugfix", "bugfix_deseas"]

# ── Load npz ──────────────────────────────────────────────────────────────────
npz_path = RESULTS_DIR / "tuku_aligned_data.npz"
if not npz_path.exists():
    sys.exit(f"File not found — cannot proceed: {npz_path}")

npz = np.load(npz_path, allow_pickle=True)


def load_layer(layer: str) -> dict:
    """Extract all arrays for one layer from the npz archive."""
    d = {}
    prefix = f"{layer}__"
    for key in npz.files:
        if key.startswith(prefix):
            d[key[len(prefix):]] = npz[key]
    d["dates"]        = pd.to_datetime(d["dates"])
    d["inc_dates"]    = pd.to_datetime(d["inc_dates"])
    d["tau_opt"]      = int(d["tau_opt"])
    d["h_c"]          = float(d["h_c"])
    # monthly_means: shape (12,) — per-month mean of incremental signal
    # stored as float array; index 0 = January mean, index 11 = December mean
    d["monthly_means"] = np.array(d["monthly_means"], dtype=float)
    return d


def remove_seasonal(signal: np.ndarray, dates: pd.DatetimeIndex) -> np.ndarray:
    """
    Remove per-month mean from incremental signal.
    Computes monthly means directly from the window slice (independent of stored
    monthly_means) to avoid any indexing mismatch with the driver window.
    """
    months = dates.month
    anom   = signal.copy()
    for m in range(1, 13):
        mask = months == m
        if mask.sum() >= 1:
            anom[mask] -= anom[mask].mean()
    return anom


def ols_raw(dH: np.ndarray, db: np.ndarray) -> float:
    """OLS slope (unclamped): S = dot(dH,db)/dot(dH,dH)."""
    denom = float(np.dot(dH, dH))
    if denom == 0:
        return 0.0
    return float(np.dot(dH, db) / denom)


def ols_nonneg(dH: np.ndarray, db: np.ndarray) -> float:
    """OLS slope clamped to >= 0."""
    return max(0.0, ols_raw(dH, db))


def r2_cumulative(db_obs: np.ndarray, db_pred: np.ndarray) -> float:
    """
    R² on CUMULATIVE compaction (cumsum of increments).
    This measures whether the total subsidence trajectory is reproduced.
    """
    cum_obs  = np.cumsum(db_obs)
    cum_pred = np.cumsum(db_pred)
    ss_res = float(np.sum((cum_obs - cum_pred) ** 2))
    ss_tot = float(np.sum((cum_obs - cum_obs.mean()) ** 2))
    if ss_tot == 0:
        return float("nan")
    return float(1.0 - ss_res / ss_tot)


# ── Main loop ─────────────────────────────────────────────────────────────────
all_rows = []

print(f"\n{'='*88}")
print("TUKU  h_c SENSITIVITY TEST — 09_sensitivity_hc.py")
print(f"{'='*88}\n")

for layer in LAYERS_ORDERED:
    try:
        d = load_layer(layer)
    except Exception as exc:
        print(f"  {layer}: could not load — {exc}")
        continue

    tau           = d["tau_opt"]
    inc_dH        = d["inc_dH"].astype(float)      # m/epoch,  length T
    inc_db        = d["inc_db"].astype(float)      # mm/epoch, length T
    head_m        = d["head_m"].astype(float)      # absolute head (aligned), length T+1
    inc_dates_all = d["inc_dates"]                 # DatetimeIndex, length T
    h_c           = d["h_c"]
    wellcode      = str(d["wellcode"])

    T = len(inc_dH)          # number of incremental epochs
    n = T - tau              # usable (driver, response) pairs

    if n < 4:
        print(f"  {layer}: only {n} usable epochs after tau={tau} — skipping\n")
        continue

    # Driver window
    head_driver   = head_m[:n]           # absolute head at driver epochs 0..n-1
    dH_driver     = inc_dH[:n]          # head increment at driver epochs 0..n-1
    db_response   = inc_db[tau:]        # MLCW increment at response epochs tau..T-1
    dates_driver  = pd.DatetimeIndex(inc_dates_all[:n])

    # Seasonal-removed versions of driver and response windows
    dH_driver_ds  = remove_seasonal(dH_driver,  dates_driver)
    db_response_ds = remove_seasonal(db_response, pd.DatetimeIndex(inc_dates_all[tau:]))

    assert len(head_driver)   == n
    assert len(dH_driver)     == n
    assert len(db_response)   == n

    print(f"  {layer}  tau={tau} ({tau*5}d)  h_c={h_c:.4f} m  n={n}  wellcode={wellcode}")
    print(f"  {'setting':<16s} {'n_in':>5s} {'n_in%':>6s}  "
          f"{'S_ke(raw)':>11s}  {'S_kv(raw)':>11s}  {'S_ke':>10s}  {'S_kv':>10s}  "
          f"{'ratio':>10s}  {'R2_cum':>7s}  flag")
    print(f"  {'-'*16} {'-'*5} {'-'*6}  {'-'*11}  {'-'*11}  {'-'*10}  {'-'*10}  "
          f"{'-'*10}  {'-'*7}  {'-'*25}")

    for setting in SETTINGS:
        # ── Select driver/response arrays ──────────────────────────────────
        if setting == "bugfix_deseas":
            dH_use = dH_driver_ds
            db_use = db_response_ds
        else:
            dH_use = dH_driver
            db_use = db_response

        # ── Build inelastic mask ───────────────────────────────────────────
        if setting == "original":
            inelastic = head_driver <= h_c

        elif setting == "p50":
            thresh    = float(np.percentile(head_driver, 50))
            inelastic = head_driver <= thresh

        elif setting == "p75":
            thresh    = float(np.percentile(head_driver, 75))
            inelastic = head_driver <= thresh

        elif setting == "p90":
            thresh    = float(np.percentile(head_driver, 90))
            inelastic = head_driver <= thresh

        elif setting in ("bugfix", "bugfix_deseas"):
            # Physically correct: head below preconsolidation AND head is falling
            inelastic = (head_driver <= h_c) & (dH_driver < 0)

        else:
            raise ValueError(f"Unknown setting: {setting}")

        elastic = ~inelastic

        n_elastic      = int(elastic.sum())
        n_inelastic    = int(inelastic.sum())
        n_inelastic_pct = 100.0 * n_inelastic / n

        # ── OLS fits — raw and clamped ─────────────────────────────────────
        S_ke_raw = 0.0
        S_ke     = 0.0
        if n_elastic >= 4:
            S_ke_raw = ols_raw(dH_use[elastic],   db_use[elastic])
            S_ke     = max(0.0, S_ke_raw)

        S_kv_raw = 0.0
        S_kv     = 0.0
        if n_inelastic >= 4:
            S_kv_raw = ols_raw(dH_use[inelastic], db_use[inelastic])
            S_kv     = max(0.0, S_kv_raw)

        clamped_flag = ""
        if S_ke_raw < 0 or S_kv_raw < 0:
            clamped_flag = f"(clamped: ke_raw={S_ke_raw:.4f} kv_raw={S_kv_raw:.4f})"

        # ── Ratio ─────────────────────────────────────────────────────────
        if S_ke > 0 and S_kv > 0:
            ratio     = S_kv / S_ke
            ratio_str = f"{ratio:.2f}x"
            ratio_ok  = 8.0 <= ratio <= 100.0
        elif n_inelastic < 4:
            ratio     = None
            ratio_str = "n<4"
            ratio_ok  = False
        elif S_ke == 0 and S_kv > 0:
            ratio     = None
            ratio_str = "undef(ke=0)"
            ratio_ok  = False
        else:
            ratio     = None
            ratio_str = "undef"
            ratio_ok  = False

        # ── Prediction and cumulative R² ──────────────────────────────────
        db_pred = np.zeros(n)
        if n_elastic >= 4:
            db_pred[elastic]   = S_ke * dH_use[elastic]
        if n_inelastic >= 4:
            db_pred[inelastic] = S_kv * dH_use[inelastic]

        r2_val = r2_cumulative(db_response, db_pred)   # always on raw increments

        # Cumulative range
        cum_pred = np.cumsum(db_pred)
        cum_obs  = np.cumsum(db_response)

        # ── Physical law flag ─────────────────────────────────────────────
        if ratio is not None and ratio_ok:
            phys_flag = "[OK]"
        elif ratio is not None and not ratio_ok:
            phys_flag = "RATIO OUT OF RANGE"
        else:
            phys_flag = ""
        if clamped_flag:
            phys_flag += "  " + clamped_flag

        print(
            f"  {setting:<16s} {n_inelastic:>5d} {n_inelastic_pct:>6.1f}%  "
            f"{S_ke_raw:>11.6f}  {S_kv_raw:>11.6f}  "
            f"{S_ke:>10.6f}  {S_kv:>10.6f}  "
            f"{ratio_str:>10s}  {r2_val:>7.4f}  {phys_flag}"
        )

        all_rows.append(dict(
            layer=layer,
            wellcode=wellcode,
            tau_opt=tau,
            tau_opt_days=tau * 5,
            h_c=round(h_c, 6),
            setting=setting,
            n_epochs=n,
            n_elastic=n_elastic,
            n_inelastic=n_inelastic,
            n_inelastic_pct=round(n_inelastic_pct, 2),
            S_ke_raw=round(S_ke_raw, 8),
            S_kv_raw=round(S_kv_raw, 8),
            S_ke=round(S_ke, 8),
            S_kv=round(S_kv, 8),
            ratio_skv_ske=round(ratio, 4) if ratio is not None else None,
            ratio_in_8_100=ratio_ok,
            R2_cumulative=round(r2_val, 6) if not np.isnan(r2_val) else None,
            cum_pred_min_mm=round(float(cum_pred.min()), 4),
            cum_pred_max_mm=round(float(cum_pred.max()), 4),
            cum_obs_min_mm=round(float(cum_obs.min()), 4),
            cum_obs_max_mm=round(float(cum_obs.max()), 4),
        ))

    print()

# ── Save results ──────────────────────────────────────────────────────────────
out_csv  = RESULTS_DIR / "sensitivity_hc_results.csv"
out_json = RESULTS_DIR / "sensitivity_hc_results.json"

results_df = pd.DataFrame(all_rows)
results_df.to_csv(out_csv, index=False)
print(f"Saved: {out_csv}")

json.dump(all_rows, open(out_json, "w"), indent=2, default=str)
print(f"Saved: {out_json}")

# ── Summary pivot: ratio ───────────────────────────────────────────────────────
print(f"\n{'='*88}")
print("SUMMARY — S_kv/S_ke ratio by layer and setting")
print(f"{'='*88}")
pivot = results_df.pivot_table(
    index="layer", columns="setting", values="ratio_skv_ske", aggfunc="first"
)
cols_order = [c for c in SETTINGS if c in pivot.columns]
pivot = pivot[cols_order]
print(pivot.to_string(float_format=lambda x: f"{x:.2f}"))

print(f"\n{'='*88}")
print("SUMMARY — n_inelastic_pct by layer and setting")
print(f"{'='*88}")
pivot2 = results_df.pivot_table(
    index="layer", columns="setting", values="n_inelastic_pct", aggfunc="first"
)
pivot2 = pivot2[[c for c in SETTINGS if c in pivot2.columns]]
print(pivot2.to_string(float_format=lambda x: f"{x:.1f}"))

print(f"\n{'='*88}")
print("SUMMARY — cumulative R² by layer and setting")
print(f"{'='*88}")
pivot3 = results_df.pivot_table(
    index="layer", columns="setting", values="R2_cumulative", aggfunc="first"
)
pivot3 = pivot3[[c for c in SETTINGS if c in pivot3.columns]]
print(pivot3.to_string(float_format=lambda x: f"{x:.4f}"))

print("\nDone.")
