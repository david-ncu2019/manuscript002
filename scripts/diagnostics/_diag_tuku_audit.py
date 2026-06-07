"""
_diag_tuku_audit.py — Diagnostic audit of TUKU v3 results (5 issues).
Run: $env:PYTHONPATH=""; conda run -n fafalab python _diag_tuku_audit.py
"""
import sys, json
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2")
RESULTS_JSON = ROOT / "results" / "ihmf" / "v3" / "TUKU_v3_results.json"
MLCW_CSV     = ROOT / "data" / "mlcw" / "group_byLayer_reconstr" / "TUKU_reconst_grouped.csv"
INSAR_CSV    = ROOT / "data" / "insar" / "InSAR_measures_at_MLCW.csv"

# GWL feathers + wellcodes per layer
LAYER_GWL = {
    "F1": (ROOT / "data/gwl/well_timeseries/HONGLUN_gwl_timeseries.feather", "09050111"),
    "F2": (ROOT / "data/gwl/well_timeseries/TUKU_gwl_timeseries.feather",   "09050321"),
    "F3": (ROOT / "data/gwl/well_timeseries/TUKU_gwl_timeseries.feather",   "09050331"),
    "F4": (ROOT / "data/gwl/well_timeseries/LIUZHUANG_gwl_timeseries.feather", "09080251"),
    "T1": (ROOT / "data/gwl/well_timeseries/FANGCAO_gwl_timeseries.feather",   "09030211"),
    "T2": (ROOT / "data/gwl/well_timeseries/LUNZI_gwl_timeseries.feather",     "09170121"),
}
LAYERS = ["F1", "F2", "F3", "F4", "T1", "T2"]

# Load results
with open(RESULTS_JSON) as f:
    res = json.load(f)

print("=" * 70)
print("ISSUE 1: Step 2 Domain — cumulative vs. incremental for alpha fit")
print("=" * 70)

# --- Load InSAR ---
insar_df = pd.read_csv(INSAR_CSV, parse_dates=[0])
insar_df.columns = [c.strip() for c in insar_df.columns]
insar_df["datetime"] = pd.to_datetime(insar_df.iloc[:, 0])
insar_df = insar_df[["datetime", "TUKU"]].dropna(subset=["TUKU"])
insar_df["insar_mm"] = insar_df["TUKU"] * 1000.0
insar_mm_full = insar_df["insar_mm"].values  # cumulative

inc_insar_full = np.diff(insar_mm_full)  # incremental

# --- Load MLCW (for all layers combined) ---
mlcw_df = pd.read_csv(MLCW_CSV, parse_dates=["datetime"])
mlcw_df["datetime"] = pd.to_datetime(mlcw_df["datetime"])

# --- We need to reproduce what fit_ihm_f_v3 does:
# Build per-layer inc_db and dH_lagged on the common window
# tau_max_all = max tau across layers
tau_vals = {lyr: res["layers"][lyr]["tau_opt"] for lyr in LAYERS}
tau_max_all = max(tau_vals.values())
print(f"  tau_max_all = {tau_max_all}  (max tau across all layers = T1's tau=73)")

# Align all layers to InSAR timeline
insar_sorted = insar_df.sort_values("datetime").reset_index(drop=True)

layer_inc_db_pred = {}  # per-layer predicted incremental compaction
layer_inc_db_obs  = {}  # per-layer observed incremental compaction

T_full = len(insar_mm_full)
T_full_inc = T_full - 1   # length of incremental arrays
win_start = tau_max_all
win_len   = T_full_inc - win_start

print(f"  T_full_inc = {T_full_inc}, win_start = {win_start}, win_len = {win_len}")
print(f"  (These should match JSON 'T' = {res['T']})\n")

db_pred_all = np.zeros(win_len)

for lyr in LAYERS:
    feather_path, wellcode = LAYER_GWL[lyr]
    gwl_raw = pd.read_feather(feather_path)
    gwl_raw["datetime"] = pd.to_datetime(gwl_raw["datetime"])
    gwl_raw = gwl_raw[["datetime", wellcode]].dropna(subset=[wellcode])
    gwl_raw = gwl_raw.rename(columns={wellcode: "head_m"})

    mlcw_layer = mlcw_df[["datetime", lyr]].rename(columns={lyr: "mlcw_mm"})

    gwl_aligned  = pd.merge_asof(insar_sorted[["datetime"]], gwl_raw.sort_values("datetime"),
                                  on="datetime", direction="nearest")
    mlcw_aligned = pd.merge_asof(insar_sorted[["datetime"]], mlcw_layer.sort_values("datetime"),
                                  on="datetime", direction="nearest")
    merged = insar_sorted.merge(gwl_aligned, on="datetime").merge(mlcw_aligned, on="datetime")
    merged = merged.sort_values("datetime").reset_index(drop=True)

    head_m  = merged["head_m"].values
    mlcw_mm = merged["mlcw_mm"].values

    h_c_head = float(np.percentile(gwl_raw["head_m"].dropna(), 10))

    inc_dH = np.diff(head_m)
    inc_db = np.diff(mlcw_mm)

    # Regime mask on length T_full-1
    elastic_full   = head_m[:-1] > h_c_head
    inelastic_full = ~elastic_full

    # Per-layer common window (same logic as fit_ihm_f_v3)
    tau = tau_vals[lyr]
    offset = tau_max_all - tau
    dH_lag = inc_dH[offset: offset + win_len]
    db_win = inc_db[win_start: win_start + win_len]
    e_win  = elastic_full[win_start: win_start + win_len]
    i_win  = inelastic_full[win_start: win_start + win_len]

    S_ke = res["layers"][lyr]["S_ke"]
    S_kv = res["layers"][lyr]["S_kv"]

    db_pred_j = np.where(e_win, S_ke * dH_lag, 0.0) + np.where(i_win, S_kv * dH_lag, 0.0)
    db_pred_all += db_pred_j
    layer_inc_db_pred[lyr] = db_pred_j
    layer_inc_db_obs[lyr]  = db_win

# Alpha fit — as done in code (CUMULATIVE domain)
inc_insar_win = inc_insar_full[win_start: win_start + win_len]
cum_insar = np.cumsum(inc_insar_win)
cum_pred  = np.cumsum(db_pred_all)

alpha_from_code = float(np.dot(cum_pred, cum_insar) / np.dot(cum_insar, cum_insar))
alpha_clipped   = float(np.clip(alpha_from_code, 1e-6, 1.0))
print(f"  alpha_from_code (cumulative OLS) = {alpha_from_code:.6f}")
print(f"  alpha_clipped   = {alpha_clipped:.6f}")
print(f"  alpha from JSON = {res['alpha']:.6f}")

# R² in cumulative domain (as reported in JSON)
insar_pred_cum = cum_pred / alpha_clipped
resid_cum      = cum_insar - insar_pred_cum
ss_res_cum = float(np.sum(resid_cum**2))
ss_tot_cum = float(np.sum((cum_insar - cum_insar.mean())**2))
r2_cum = 1.0 - ss_res_cum / ss_tot_cum
rmse_cum = float(np.sqrt(np.mean(resid_cum**2)))
print(f"\n  R² (cumulative, as reported) = {r2_cum:.4f}  (JSON says {res['r2_insar']:.4f})")
print(f"  RMSE (cumulative, as reported) = {rmse_cum:.3f} mm  (JSON says {res['rmse_insar']:.3f} mm)")

# R² in INCREMENTAL domain
inc_pred = db_pred_all / alpha_clipped
resid_inc = inc_insar_win - inc_pred
ss_res_inc = float(np.sum(resid_inc**2))
ss_tot_inc = float(np.sum((inc_insar_win - inc_insar_win.mean())**2))
r2_inc = 1.0 - ss_res_inc / ss_tot_inc if ss_tot_inc > 0 else np.nan
rmse_inc = float(np.sqrt(np.mean(resid_inc**2)))
print(f"\n  R² (incremental domain)       = {r2_inc:.4f}")
print(f"  RMSE (incremental domain)     = {rmse_inc:.3f} mm")
print(f"\n  Gap between cumulative R² and incremental R² = {r2_cum - r2_inc:.4f}")
print(f"  (If gap > 0.15, trend inflation suspected)")

# PHYSICAL REQUIREMENT: theory doc section 3.1 (equations 7-10) says:
# D_k(t) = S_skv * Delta_H(t) -- cumulative form (eq 10)
# But fit_ihm_f_v3 uses INCREMENTAL form in Step 1 and cumulative for alpha in Step 2
# Theory section 9.1 explicitly says: use change-from-reference (cumulative), NOT step-to-step
print(f"\n  Theory note: doc section 9.1 lines 470-478 explicitly requires CUMULATIVE")
print(f"  (change-from-reference) form, not incremental (step-to-step).")
print(f"  Code Step 2 uses cumulative for alpha fit -- consistent with theory.")
print(f"  Code Step 1 uses INCREMENTAL form for S_ke/S_kv -- INCONSISTENCY vs. theory.")


print("\n" + "=" * 70)
print("ISSUE 2: Regime mask — 10th percentile vs. running minimum")
print("=" * 70)

for lyr in LAYERS:
    feather_path, wellcode = LAYER_GWL[lyr]
    gwl_raw = pd.read_feather(feather_path)
    gwl_raw["datetime"] = pd.to_datetime(gwl_raw["datetime"])
    gwl_raw = gwl_raw[["datetime", wellcode]].dropna(subset=[wellcode])

    head_full = gwl_raw[wellcode].values
    head_dates = gwl_raw["datetime"].values

    # h_c current (10th percentile)
    h_c_current = float(np.percentile(head_full, 10))
    h_c_min     = float(np.min(head_full))

    # Now on MLCW-aligned epochs (aligned to InSAR timeline, T_full epochs)
    # Regenerate aligned head
    insar_sorted2 = insar_df.sort_values("datetime").reset_index(drop=True)
    gwl_aligned2  = pd.merge_asof(insar_sorted2[["datetime"]], gwl_raw.sort_values("datetime"),
                                   on="datetime", direction="nearest")
    head_aligned = gwl_aligned2[wellcode].values  # length T_full
    head_inc     = head_aligned[:-1]              # length T_full-1 (for incremental mask)

    # Current code: inelastic = head_inc <= h_c_current
    inel_current = head_inc <= h_c_current
    elas_current = ~inel_current
    n_inel_current = int(inel_current.sum())
    n_total_inc    = len(head_inc)

    # Fraction of "inelastic" epochs that have RISING head (dH > 0)
    inc_dH_aligned = np.diff(head_aligned)  # length T_full-1
    n_rising_inel = int((inel_current & (inc_dH_aligned > 0)).sum())
    frac_rising_inel = n_rising_inel / n_inel_current if n_inel_current > 0 else np.nan

    # Correct method: running minimum (expanding window, EXCLUDING current epoch)
    # True inelastic at epoch t: head[t] < min(head[0..t-1])
    # i.e., head[t] is a new all-time low relative to everything BEFORE it
    head_series = pd.Series(head_aligned)
    running_min_excl = head_series.expanding().min().shift(1).values  # min of prior epochs; NaN at t=0
    # For inc arrays (length T_full-1), use head_inc = head_aligned[:-1]
    # Compare head_inc[t] against running_min_excl[t] = min(head[0..t-1])
    running_min_inc_excl = running_min_excl[:-1]  # align to inc length
    valid_mask = ~np.isnan(running_min_inc_excl)
    inel_correct = valid_mask & (head_inc < running_min_inc_excl)
    n_inel_correct = int(inel_correct.sum())

    print(f"\n  Layer {lyr} (wellcode {wellcode}):")
    print(f"    h_c (10th pct, current code) = {h_c_current:.3f} m  |  h_c (min) = {h_c_min:.3f} m")
    print(f"    Inelastic count (current code, 10th pct): {n_inel_current} / {n_total_inc} = {n_inel_current/n_total_inc*100:.1f}%")
    print(f"    Of those 'inelastic': {n_rising_inel} have rising head = {frac_rising_inel*100:.1f}% are physically elastic")
    print(f"    True inelastic (running min criterion):  {n_inel_correct} / {n_total_inc} = {n_inel_correct/n_total_inc*100:.1f}%")


print("\n" + "=" * 70)
print("ISSUE 3: Data continuity — MLCW and GWL in 2022-2025")
print("=" * 70)

mlcw_df2 = pd.read_csv(MLCW_CSV, parse_dates=["datetime"])
mlcw_df2["datetime"] = pd.to_datetime(mlcw_df2["datetime"])
mlcw_df2["year"] = mlcw_df2["datetime"].dt.year

for lyr in LAYERS:
    if lyr not in mlcw_df2.columns:
        print(f"\n  Layer {lyr}: COLUMN NOT FOUND in MLCW CSV")
        continue
    print(f"\n  Layer {lyr} MLCW non-NaN counts by year:")
    for yr in [2022, 2023, 2024, 2025]:
        sub = mlcw_df2[mlcw_df2["year"] == yr][lyr]
        n_valid = int(sub.notna().sum())
        n_total = len(sub)
        if n_valid == 0:
            print(f"    {yr}: {n_valid}/{n_total}  <== ZERO real values — FLAG")
        else:
            print(f"    {yr}: {n_valid}/{n_total}")

# GWL for T1 (FANGCAO, wellcode 09030211)
print(f"\n  GWL for TUKU T1 (FANGCAO, wellcode 09030211):")
fangcao_feather = ROOT / "data/gwl/well_timeseries/FANGCAO_gwl_timeseries.feather"
fangcao = pd.read_feather(fangcao_feather)
fangcao["datetime"] = pd.to_datetime(fangcao["datetime"])
fangcao["year"] = fangcao["datetime"].dt.year
wellcode_t1 = "09030211"
for yr in [2022, 2023, 2024, 2025]:
    sub = fangcao[fangcao["year"] == yr][wellcode_t1]
    n_valid = int(sub.notna().sum())
    n_total = len(sub)
    if n_valid == 0:
        print(f"    {yr}: {n_valid}/{n_total}  <== ZERO — FLAG")
    else:
        print(f"    {yr}: {n_valid}/{n_total}")


print("\n" + "=" * 70)
print("ISSUE 4: S_kv/S_ke ratio physical bounds check")
print("=" * 70)
print("  Physical constraint: S_kv/S_ke in range 8–58 (CRAF CLAUDE.md)")
print()

for lyr in LAYERS:
    S_ke = res["layers"][lyr]["S_ke"]
    S_kv = res["layers"][lyr]["S_kv"]
    tau  = res["layers"][lyr]["tau_opt"]

    # Check for near-zero / degenerate
    if S_ke < 1e-10 and S_kv < 1e-10:
        status = "DEGENERATE (both near zero)"
        ratio_str = "N/A"
    elif S_ke < 1e-10:
        status = "S_ke near zero (degenerate elastic)"
        ratio_str = "inf"
    elif S_kv < 1e-10:
        status = "S_kv near zero (elastic-only)"
        ratio_str = "~0"
    else:
        ratio = S_kv / S_ke
        ratio_str = f"{ratio:.2f}"
        if 8.0 <= ratio <= 58.0:
            status = "OK"
        else:
            status = f"VIOLATION (expected 8–58)"

    print(f"  Layer {lyr}: S_ke={S_ke:.3e}  S_kv={S_kv:.3e}  ratio={ratio_str}  => {status}")

# Check guard at line 141 of fit_ihm_f_v3.py
print(f"\n  Guard check (fit_ihm_f_v3.py line 140-141):")
print(f"    Code uses: if p['S_kv'] == 0.0")
print(f"    Test: does 1e-20 == 0.0?  =>  {1e-20 == 0.0}")
print(f"    Conclusion: The guard MISSES S_kv = 1e-20 (near-zero but not exactly zero)")


print("\n" + "=" * 70)
print("ISSUE 5: RSS curve identifiability (F1 vs F3 vs F2 vs T1)")
print("=" * 70)

for lyr in ["F1", "F2", "F3", "T1"]:
    rss = np.array(res["tau_rss_curves"][lyr])
    rss_min  = float(rss.min())
    rss_max  = float(rss.max())
    rss_range = rss_max - rss_min
    ratio_range_min = rss_range / rss_min if rss_min > 0 else np.nan
    tau_argmin = int(np.argmin(rss))

    print(f"\n  Layer {lyr}:")
    print(f"    tau_opt = {tau_argmin}  |  RSS_min = {rss_min:.6f}  |  RSS_max = {rss_max:.6f}")
    print(f"    range (max-min) = {rss_range:.6f}")
    print(f"    range/min ratio = {ratio_range_min:.4f}  ", end="")
    if ratio_range_min < 0.05:
        print("<< 0.05 — curve TOO FLAT, tau unidentifiable")
    elif ratio_range_min < 0.15:
        print("< 0.15 — weak minimum, tau weakly identified")
    else:
        print(">= 0.15 — reasonable minimum depth")

    # For F3: check if curve is monotonically increasing
    if lyr == "F3":
        diffs = np.diff(rss)
        n_pos = (diffs > 0).sum()
        n_neg = (diffs < 0).sum()
        print(f"    F3 RSS curve: {n_pos}/{len(diffs)} steps increasing, {n_neg}/{len(diffs)} decreasing")
        print(f"    => Curve is {'mostly monotone increasing' if n_pos > 0.8*len(diffs) else 'not monotone'}")
        print(f"    => tau_opt=0 is physically implausible for F3 at 140-275m depth")

    # For F1: show where actual minimum is
    if lyr == "F1":
        top5_tau = np.argsort(rss)[:5]
        print(f"    F1 top-5 lowest RSS at tau: {top5_tau.tolist()}")
        print(f"    (tau_opt in JSON = {res['layers']['F1']['tau_opt']})")

print("\n" + "=" * 70)
print("SUMMARY TABLE")
print("=" * 70)
print(f"  From JSON: alpha={res['alpha']:.4f}, R2_InSAR={res['r2_insar']:.4f}, "
      f"RMSE_InSAR={res['rmse_insar']:.2f}mm, T={res['T']}")
print(f"  S_kv near-zero layers (< 1e-10): ",
      [lyr for lyr in LAYERS if res["layers"][lyr]["S_kv"] < 1e-10])
print(f"  tau_opt == TAU_MAX (73): ",
      [lyr for lyr in LAYERS if res["layers"][lyr]["tau_opt"] == 73])
