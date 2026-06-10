"""
diag_f1t1_below_floor.py — Task 2.2.4 investigation.

F1 (bulk ratio 1.64) and T1 (2.03) sit below the physical floor of 3.
Test the three hypotheses in plan order:
  (a) post-2015 head never substantially crossed below h_c → V(t) barely activates
      and S_kv is fit on weak signal (count V<0 epochs and total V excursion in m).
  (b) the tau for these layers is wrong.
  (c) the layers truly behave elastically post-2015 ("elastic-dominated regime").

Replicates the Script 15 loader exactly (lagged driver, gap-aware cumsum).
Persists results/characterization/f1t1_below_floor.json
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "10_ihmf"))
sys.path.insert(0, str(ROOT / "tau_demo_TUKU"))

from ihmf_model_v3 import compute_virgin_term
from gap_aware_cumsum import gap_aware_cumulative, census

RESULT_JSON = ROOT / "results" / "ihmf" / "v3" / "verification_20260609_intercept" / "TUKU_gps_v3_results.json"
TAU_DEMO    = ROOT / "tau_demo_TUKU" / "data"
INC_DIR     = TAU_DEMO / "incremental_data"
OUT_DIR     = ROOT / "tau_demo_TUKU" / "results" / "characterization"
REF_DATE    = pd.Timestamp("2015-01-16")

WELL_CONFIG = [
    ("F1", "HONGLUN_gwl_timeseries.feather", "09050111"),
    ("T1", "HONGLUN_gwl_timeseries.feather", "09050111"),
]

with open(RESULT_JSON) as f:
    prod = json.load(f)
tau_dict = {lyr: prod["layers"][lyr]["tau_opt"] for lyr in prod["layers"]}

mlcw_inc = pd.read_feather(INC_DIR / "mlcw_diff_cleaned.feather")
mlcw_inc["datetime"] = pd.to_datetime(mlcw_inc["datetime"]).astype("datetime64[ns]")
mlcw_inc = mlcw_inc.sort_values("datetime").reset_index(drop=True)
for col in [c for c in mlcw_inc.columns if c != "datetime"]:
    mlcw_inc[f"_cum_{col}"] = gap_aware_cumulative(mlcw_inc[col].values)
master = pd.DataFrame({"datetime": mlcw_inc["datetime"].copy()})

out = {}
for layer, fname, wellcode in WELL_CONFIG:
    gwl = pd.read_feather(TAU_DEMO / fname)
    gwl["datetime"] = pd.to_datetime(gwl["datetime"]).astype("datetime64[ns]")
    gwl = gwl[["datetime", wellcode]].dropna(subset=[wellcode])
    gwl = gwl.sort_values("datetime").reset_index(drop=True)

    pre_ref_vals = gwl[gwl["datetime"] < REF_DATE][wellcode].dropna()
    h_c_abs = float(pre_ref_vals.min()) if len(pre_ref_vals) >= 10 else float(gwl[wellcode].dropna().min())

    gwl_aligned = pd.merge_asof(master, gwl, on="datetime", direction="nearest",
                                tolerance=pd.Timedelta("3D"))
    H_abs_full = gwl_aligned[wellcode].values.astype(float)
    b_cum_full = mlcw_inc[f"_cum_{layer}"].values.astype(float)
    dt_full = master["datetime"].values

    tau = tau_dict.get(layer, 0)
    N_full = len(H_abs_full)
    H_abs_lagged = H_abs_full[: N_full - tau]
    b_cum = b_cum_full[tau:]
    dt_resp = dt_full[tau:]            # response time axis

    valid = np.isfinite(H_abs_lagged) & np.isfinite(b_cum)
    H_abs = H_abs_lagged[valid]
    b = b_cum[valid]
    dt_v = dt_resp[valid]

    V = compute_virgin_term(H_abs, h_c_abs)   # min(0, cummin(H) - h_c), <= 0

    n_total = len(V)
    n_V_neg = int((V < 0).sum())
    V_min = float(V.min())            # most-negative V = total virgin excursion (m), <=0
    total_V_excursion_m = abs(V_min)
    H_min_abs = float(np.nanmin(H_abs))
    head_below_hc_m = max(0.0, h_c_abs - H_min_abs)  # how far head dropped below h_c

    # Post-2015 activity: V increments after REF_DATE (response axis)
    post = dt_v >= np.datetime64(REF_DATE)
    n_post = int(post.sum())
    V_post = V[post]
    # how much NEW virgin excursion accrued post-2015
    if n_post > 0:
        V_post_excursion_m = float(V_post.min() - V[~post].min()) if (~post).any() else float(V_post.min())
        V_post_excursion_m = abs(min(0.0, V_post_excursion_m))
        n_V_neg_post = int((np.diff(np.concatenate([[V[~post].min() if (~post).any() else 0.0], V_post])) < 0).sum())
    else:
        V_post_excursion_m = 0.0
        n_V_neg_post = 0

    out[layer] = {
        "tau_opt": int(tau),
        "h_c_abs_m": round(h_c_abs, 4),
        "H_min_abs_m": round(H_min_abs, 4),
        "head_max_drop_below_hc_m": round(head_below_hc_m, 4),
        "n_total_epochs": n_total,
        "n_V_negative": n_V_neg,
        "frac_V_negative": round(n_V_neg / n_total, 4),
        "total_V_excursion_m": round(total_V_excursion_m, 4),
        "n_post2015_epochs": n_post,
        "post2015_new_V_excursion_m": round(V_post_excursion_m, 4),
    }
    print(f"{layer}: tau={tau}  h_c={h_c_abs:.3f} m  H_min={H_min_abs:.3f} m  "
          f"drop_below_hc={head_below_hc_m:.3f} m")
    print(f"   V<0 on {n_V_neg}/{n_total} epochs ({100*n_V_neg/n_total:.1f}%)  "
          f"total_V_excursion={total_V_excursion_m:.3f} m  "
          f"post-2015 new excursion={V_post_excursion_m:.3f} m")

OUT_DIR.mkdir(parents=True, exist_ok=True)
with open(OUT_DIR / "f1t1_below_floor.json", "w") as f:
    json.dump(out, f, indent=2)
print("\nSaved:", OUT_DIR / "f1t1_below_floor.json")
