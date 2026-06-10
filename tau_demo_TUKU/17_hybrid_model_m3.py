"""
17_hybrid_model_m3.py — MILESTONE M3 hybrid-model bake-off (super_plan_2026-06-10).

Fits the FIXED candidate menu H0-H4 per layer, runs the collinearity (VIF) guard
BEFORE fitting, selects strictly by held-out skill on three holdout designs
(middle gap, end gap, 6-month tail), and persists the per-layer adoption map
(the single authoritative TUKU model registry).

Candidate menu (Task 3.1 — nothing else):
  H0 incumbent          : b = a*d(t) + c
  H1 elastic head       : b = a*d(t) + d_h*u(t-tau) + c          (a, d_h >= 0)
  H2 annual harmonic    : b = a*d(t) + e*sin(2pi t/Ta) + f*cos(2pi t/Ta) + c  (Ta=73)
  H3 inelastic exceedance: b = a*d(t) + g*V(t-tau) + c            (g >= 0; sign verified)
  H4 InSAR-augmented    : b = a*d(t) + p*S_insar(t) + c          (p unconstrained)
                          S_insar = persisted InSAR seasonal-harmonic series

Reuses build_aligned_arrays() from 13_holdout_method_bakeoff.py — the M1-corrected
loader with proven tau-lag pairing (lag_alignment_test.json gate=true). u and V are
already driver-time-sliced and length-matched to the response b/d/datetime.

Output: tau_demo_TUKU/results/hybrid_model_registry.json

Usage:
  PYTHONPATH="" conda run -n fafalab2 python tau_demo_TUKU/17_hybrid_model_m3.py
"""
from __future__ import annotations

import json, sys, warnings, importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import lsq_linear

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "10_ihmf"))
sys.path.insert(0, str(ROOT / "tau_demo_TUKU"))

warnings.filterwarnings("ignore", category=UserWarning)

# Import the M1-corrected loader (proven lag pairing) from script 13.
_spec = importlib.util.spec_from_file_location(
    "bakeoff13", str(ROOT / "tau_demo_TUKU" / "13_holdout_method_bakeoff.py"))
_bk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bk)
build_aligned_arrays = _bk.build_aligned_arrays

OUT_JSON = ROOT / "tau_demo_TUKU" / "results" / "hybrid_model_registry.json"
HARMONIC_FEATHER = ROOT / "results" / "seasonal_insar_harmonic" / "TUKU" / "insar_harmonic_timeseries.feather"
LAYERS_ORDER = ["F1", "T1", "F2", "T2", "F3", "F4"]
T_A = 73.0           # annual period in 5-day epochs (365 d)
EPOCH_DAYS = 5.0

# ── DP2 / 3.2.3 baselines (from persisted files, for the report) ──────────────
F2_BASE_MID_RMSE = 4.2975     # carrier_gwl_eval.json F2.middle.rmse_carrier_mm
F3_BASE_END_RMSE = 16.9673    # carrier_gwl_eval.json F3.end.rmse_carrier_mm
TAIL_N = 36                   # 6-month tail (TUKU_carrier_reconstruction_summary.json tail_evaluation n_tail)


# ═══════════════════════════════════════════════════════════════════════════════
# Regressor construction (harmonic + InSAR), aligned to each layer's response time
# ═══════════════════════════════════════════════════════════════════════════════

def build_extra_regressors(arrays: dict) -> dict:
    """Add H2 analytic annual harmonic and H4 InSAR seasonal-harmonic series to
    each layer dict, aligned to that layer's RESPONSE datetime axis.

    The response datetime (arrays[layer]['datetime']) is already tau-sliced [tau:]
    by build_aligned_arrays, so harmonic/InSAR terms pair with the response epoch
    (they are surface/seasonal carriers evaluated at observation time t, NOT lagged).
    """
    # Load persisted InSAR seasonal-harmonic feather (mm).
    if not HARMONIC_FEATHER.exists():
        raise FileNotFoundError(f"InSAR harmonic feather not found: {HARMONIC_FEATHER}")
    h = pd.read_feather(HARMONIC_FEATHER)
    h["datetime"] = pd.to_datetime(h["datetime"]).astype("datetime64[ns]")
    h = h.sort_values("datetime").reset_index(drop=True)

    for layer in arrays:
        dt = pd.to_datetime(arrays[layer]["datetime"])
        # Continuous epoch index t (5-day units) from first response date — exact Ta=73.
        t_days = (dt - dt[0]).total_seconds() / 86400.0
        t_epoch = t_days / EPOCH_DAYS
        omega = 2 * np.pi / T_A
        arrays[layer]["sin_a"] = np.sin(omega * t_epoch.values)
        arrays[layer]["cos_a"] = np.cos(omega * t_epoch.values)

        # InSAR seasonal-harmonic: merge_asof onto response datetime (nearest, 3-day tol)
        resp = pd.DataFrame({"datetime": dt.values})
        merged = pd.merge_asof(resp, h[["datetime", "A1_x_seasonal", "A1_x_annual_model"]],
                               on="datetime", direction="nearest",
                               tolerance=pd.Timedelta("3D"))
        arrays[layer]["insar_seasonal"] = merged["A1_x_seasonal"].values.astype(float)
        arrays[layer]["insar_annual"] = merged["A1_x_annual_model"].values.astype(float)
    return arrays


# ═══════════════════════════════════════════════════════════════════════════════
# Collinearity guard (Task 3.1.1) — VIF on detrended regressor pairs
# ═══════════════════════════════════════════════════════════════════════════════

def _detrend(x: np.ndarray) -> np.ndarray:
    t = np.arange(len(x), dtype=float)
    m = np.isfinite(x)
    if m.sum() < 3:
        return x - np.nanmean(x)
    coef = np.polyfit(t[m], x[m], 1)
    return x - (coef[0] * t + coef[1])


def pairwise_vif(regs: dict) -> dict:
    """VIF between each pair of regressors after removing each one's linear trend.
    VIF = 1/(1-r^2) on the detrended pair. Returns {('A','B'): vif}.
    """
    names = list(regs.keys())
    out = {}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a = _detrend(regs[names[i]])
            b = _detrend(regs[names[j]])
            m = np.isfinite(a) & np.isfinite(b)
            if m.sum() < 10 or np.std(a[m]) < 1e-12 or np.std(b[m]) < 1e-12:
                vif = float("nan")
            else:
                r = np.corrcoef(a[m], b[m])[0, 1]
                vif = float("inf") if abs(r) >= 1.0 else 1.0 / (1.0 - r * r)
            out[f"{names[i]}|{names[j]}"] = round(vif, 3) if np.isfinite(vif) else vif
    return out


def candidate_regressors(a: dict, cand: str):
    """Return ordered dict of regressor name -> array for a candidate (excluding intercept)."""
    d = a["d_surface"]
    if cand == "H0":
        return {"d": d}
    if cand == "H1":
        return {"d": d, "u": a["u"]}
    if cand == "H2":
        return {"d": d, "sin_a": a["sin_a"], "cos_a": a["cos_a"]}
    if cand == "H3":
        return {"d": d, "V": a["V"]}
    if cand == "H4":
        return {"d": d, "insar_seasonal": a["insar_seasonal"]}
    raise ValueError(cand)


# ═══════════════════════════════════════════════════════════════════════════════
# Fitting (bounded least squares per candidate) and prediction
# ═══════════════════════════════════════════════════════════════════════════════

def _bounds_for(cand: str):
    """Lower/upper bounds for [regressors..., intercept]."""
    if cand == "H0":
        lo, hi = [0.0], [np.inf]                       # a>=0
    elif cand == "H1":
        lo, hi = [0.0, 0.0], [np.inf, np.inf]          # a>=0, d_h>=0
    elif cand == "H2":
        lo, hi = [0.0, -np.inf, -np.inf], [np.inf, np.inf, np.inf]  # e,f free
    elif cand == "H3":
        lo, hi = [0.0, 0.0], [np.inf, np.inf]          # a>=0, g>=0
    elif cand == "H4":
        lo, hi = [0.0, -np.inf], [np.inf, np.inf]      # a>=0, p free
    else:
        raise ValueError(cand)
    lo = lo + [-np.inf]; hi = hi + [np.inf]            # intercept free
    return np.array(lo), np.array(hi)


def fit_candidate(a: dict, cand: str, train_idx: np.ndarray):
    """Fit candidate on training indices. Returns coef dict or None."""
    regs = candidate_regressors(a, cand)
    b = a["b_cum"]
    cols = [regs[k][train_idx] for k in regs]
    bt = b[train_idx]
    stack = np.column_stack(cols + [np.ones(len(train_idx))])
    m = np.all(np.isfinite(stack), axis=1) & np.isfinite(bt)
    if m.sum() < 10:
        return None
    lo, hi = _bounds_for(cand)
    res = lsq_linear(stack[m], bt[m], bounds=(lo, hi))
    names = list(regs.keys()) + ["c"]
    return {n: float(v) for n, v in zip(names, res.x)}


def predict_candidate(a: dict, cand: str, coef: dict, idx: np.ndarray) -> np.ndarray:
    regs = candidate_regressors(a, cand)
    pred = np.full(len(idx), coef["c"], dtype=float)
    for k in regs:
        pred = pred + coef[k] * regs[k][idx]
    return pred


def gap_rmse(a: dict, cand: str, coef: dict, gap_idx: np.ndarray):
    if coef is None:
        return float("inf"), None, None
    pred = predict_candidate(a, cand, coef, gap_idx)
    obs = a["b_cum"][gap_idx]
    m = np.isfinite(pred) & np.isfinite(obs)
    if m.sum() == 0:
        return float("inf"), None, None
    rmse = float(np.sqrt(np.mean((obs[m] - pred[m]) ** 2)))
    return rmse, obs[m], pred[m]


# ═══════════════════════════════════════════════════════════════════════════════
# Holdout designs
# ═══════════════════════════════════════════════════════════════════════════════

def design_indices(N: int, design: str):
    if design == "middle":
        ms, me = int(N * 0.40), int(N * 0.70)
        train = np.array(list(range(0, ms)) + list(range(me, N)))
        gap = np.array(list(range(ms, me)))
    elif design == "end":
        es = int(N * 0.70)
        train = np.array(list(range(0, es)))
        gap = np.array(list(range(es, N)))
    elif design == "tail":
        ts = max(0, N - TAIL_N)
        train = np.array(list(range(0, ts)))
        gap = np.array(list(range(ts, N)))
    else:
        raise ValueError(design)
    return train, gap


def detrended_resid_corr(obs: np.ndarray, pred: np.ndarray) -> float:
    """Correlation between detrended observed and detrended predicted over the gap.
    Measures whether the seasonal/sub-annual shape (not just trend) is captured."""
    if obs is None or len(obs) < 10:
        return float("nan")
    od = _detrend(obs); pd_ = _detrend(pred)
    if np.std(od) < 1e-12 or np.std(pd_) < 1e-12:
        return float("nan")
    return float(np.corrcoef(od, pd_)[0, 1])


# ═══════════════════════════════════════════════════════════════════════════════
# H3 sign verification (Task 3.1)
# ═══════════════════════════════════════════════════════════════════════════════

def verify_h3_sign(arrays: dict) -> dict:
    """Fit H3 unconstrained (g free) on full data per layer; report sign of g.
    V <= 0 by construction; compaction negative; a POSITIVE g maps head exceedance
    below h_c into additional downward (negative) movement. Confirms g>=0 is correct."""
    out = {}
    for layer in LAYERS_ORDER:
        a = arrays[layer]
        d = a["d_surface"]; V = a["V"]; b = a["b_cum"]
        stack = np.column_stack([d, V, np.ones(len(b))])
        m = np.all(np.isfinite(stack), axis=1) & np.isfinite(b)
        v_min = float(np.nanmin(V[np.isfinite(V)])) if np.isfinite(V).any() else float("nan")
        v_max = float(np.nanmax(V[np.isfinite(V)])) if np.isfinite(V).any() else float("nan")
        if m.sum() < 10 or np.std(V[m]) < 1e-9:
            out[layer] = {"g_unconstrained": None, "note": "V constant or insufficient — H3 degenerate",
                          "V_min": round(v_min, 3), "V_max": round(v_max, 3)}
            continue
        # Unconstrained OLS on [d, V, 1]
        coef, *_ = np.linalg.lstsq(stack[m], b[m], rcond=None)
        g = float(coef[1])
        out[layer] = {
            "g_unconstrained": round(g, 6),
            "sign": "positive" if g > 0 else ("negative" if g < 0 else "zero"),
            "V_min": round(v_min, 3), "V_max": round(v_max, 3),
            "V_is_nonpositive": bool(v_max <= 1e-9),
        }
    return out


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 88)
    print("MILESTONE M3 — Hybrid Model Bake-Off (H0-H4), held-out selection")
    print("=" * 88)

    arrays = build_aligned_arrays()
    arrays = build_extra_regressors(arrays)

    CANDS = ["H0", "H1", "H2", "H3", "H4"]
    N_PARAMS = {"H0": 2, "H1": 3, "H2": 4, "H3": 3, "H4": 3}  # incl intercept
    DESIGNS = ["middle", "end", "tail"]

    # ── H3 sign verification ──
    print("\n── H3 sign verification (g free; V<=0 by construction) ──")
    h3sign = verify_h3_sign(arrays)
    for layer in LAYERS_ORDER:
        s = h3sign[layer]
        print(f"  {layer}: g_unconstrained={s.get('g_unconstrained')}  sign={s.get('sign','-')}  "
              f"V_max={s.get('V_min')}..{s.get('V_max')}")

    # ── VIF guard (BEFORE fitting) ──
    print("\n── Collinearity guard (VIF on detrended regressor pairs) ──")
    vif_table = {}
    admissible = {}  # layer -> {cand: 'fit'|'flag'|'reject'}
    for layer in LAYERS_ORDER:
        a = arrays[layer]
        vif_table[layer] = {}
        admissible[layer] = {}
        for cand in CANDS:
            regs = candidate_regressors(a, cand)
            if len(regs) < 2:
                vif_table[layer][cand] = {}
                admissible[layer][cand] = "fit"
                continue
            vifs = pairwise_vif(regs)
            vif_table[layer][cand] = vifs
            finite = [v for v in vifs.values() if isinstance(v, float) and np.isfinite(v)]
            maxv = max(finite) if finite else 0.0
            if any((not np.isfinite(v) if isinstance(v, float) else False) for v in vifs.values()) or maxv > 10:
                admissible[layer][cand] = "reject"
            elif maxv > 5:
                admissible[layer][cand] = "flag"
            else:
                admissible[layer][cand] = "fit"
            print(f"  {layer} {cand}: {vifs}  -> {admissible[layer][cand]}")

    # ── Fit + held-out evaluation across three designs ──
    print("\n── Held-out evaluation (middle / end / tail), refit per design ──")
    registry = {}
    for layer in LAYERS_ORDER:
        a = arrays[layer]
        N = len(a["b_cum"])
        registry[layer] = {"N": N, "tau": int(a["tau_opt"]), "candidates": {}}
        for cand in CANDS:
            status = admissible[layer][cand]
            entry = {"status": status, "n_params": N_PARAMS[cand]}
            if status == "reject":
                entry["rmse"] = {d: None for d in DESIGNS}
                registry[layer]["candidates"][cand] = entry
                continue
            rmse_by_design = {}
            coef_by_design = {}
            extra_by_design = {}
            for design in DESIGNS:
                train_idx, gap_idx = design_indices(N, design)
                coef = fit_candidate(a, cand, train_idx)
                rmse, obs, pred = gap_rmse(a, cand, coef, gap_idx)
                rmse_by_design[design] = round(rmse, 4) if np.isfinite(rmse) else None
                coef_by_design[design] = coef
                ex = {}
                if obs is not None:
                    if design == "middle":
                        ex["resid_corr"] = round(detrended_resid_corr(obs, pred), 4)
                    if design == "end":
                        ex["end_error_mm"] = round(float(obs[-1] - pred[-1]), 4)
                    if design == "tail":
                        # tail skill vs linear-trend extrapolation baseline
                        tr, tg = design_indices(N, "tail")
                        bt = a["b_cum"][tr]; mt = np.isfinite(bt)
                        if mt.sum() >= 5:
                            tt = np.arange(len(tr), dtype=float)[mt]
                            cf = np.polyfit(tt, bt[mt], 1)
                            tgx = np.arange(len(tr), len(tr) + len(tg), dtype=float)
                            trend_pred = cf[0] * tgx + cf[1]
                            ob = a["b_cum"][tg]; mm = np.isfinite(ob)
                            rmse_trend = float(np.sqrt(np.mean((ob[mm] - trend_pred[mm]) ** 2)))
                            ex["rmse_trend_mm"] = round(rmse_trend, 4)
                            ex["skill"] = round(1.0 - rmse / rmse_trend, 4) if rmse_trend > 1e-9 else None
                extra_by_design[design] = ex
            entry["rmse"] = rmse_by_design
            entry["extra"] = extra_by_design
            entry["coef_full"] = fit_candidate(a, cand, np.arange(N))
            entry["coef_by_design"] = coef_by_design
            registry[layer]["candidates"][cand] = entry

    # ── Adoption rule (Task 3.2.2) ──
    print("\n── Adoption (lowest mean held-out RMSE, >5% better than H0, no design >10% worse, ties->simpler) ──")
    adoption = {}
    for layer in LAYERS_ORDER:
        cands = registry[layer]["candidates"]
        h0 = cands["H0"]
        h0_mean = np.nanmean([v for v in h0["rmse"].values() if v is not None])
        h0_by = h0["rmse"]
        best = "H0"; best_mean = h0_mean
        decisions = {"H0": {"mean_rmse": round(float(h0_mean), 4), "eligible": True, "reason": "incumbent"}}
        for cand in ["H1", "H2", "H3", "H4"]:
            c = cands[cand]
            if c["status"] == "reject":
                decisions[cand] = {"mean_rmse": None, "eligible": False, "reason": "VIF>10 rejected"}
                continue
            vals = [v for v in c["rmse"].values() if v is not None]
            if len(vals) < len(DESIGNS):
                decisions[cand] = {"mean_rmse": None, "eligible": False, "reason": "fit failed on a design"}
                continue
            cmean = float(np.mean(vals))
            beats = (h0_mean - cmean) / h0_mean > 0.05
            # never degrade any single design by >10%
            worst_deg = max((c["rmse"][d] - h0_by[d]) / h0_by[d] for d in DESIGNS)
            no_bad = worst_deg <= 0.10
            eligible = beats and no_bad
            decisions[cand] = {
                "mean_rmse": round(cmean, 4),
                "pct_better_than_h0": round((h0_mean - cmean) / h0_mean * 100, 2),
                "worst_design_degradation_pct": round(worst_deg * 100, 2),
                "beats_h0_by_5pct": bool(beats),
                "no_design_worse_10pct": bool(no_bad),
                "eligible": bool(eligible),
            }
            if eligible and (cmean < best_mean - 1e-9 or
                             (abs(cmean - best_mean) <= 1e-9 and N_PARAMS[cand] < N_PARAMS[best])):
                best, best_mean = cand, cmean
        adoption[layer] = {
            "adopted_model": best,
            "decisions": decisions,
            "adopted_mean_rmse": round(float(best_mean), 4),
            "adopted_rmse_by_design": cands[best]["rmse"],
            "adopted_coef_full": cands[best]["coef_full"],
            "adopted_extra_by_design": cands[best].get("extra", {}),
            "tau": registry[layer]["tau"],
        }
        print(f"  {layer}: adopt {best} (mean held-out RMSE {best_mean:.3f} mm)  "
              f"H0 mean {h0_mean:.3f}")

    # ── Targets (Task 3.2.3) ──
    f2 = adoption["F2"]; f3 = adoption["F3"]
    f2_mid = f2["adopted_rmse_by_design"].get("middle")
    f2_corr = f2["adopted_extra_by_design"].get("middle", {}).get("resid_corr")
    f3_end = f3["adopted_rmse_by_design"].get("end")
    f3_enderr = f3["adopted_extra_by_design"].get("end", {}).get("end_error_mm")

    tail_skill_count = 0
    tail_skills = {}
    for layer in LAYERS_ORDER:
        ad = adoption[layer]
        sk = ad["adopted_extra_by_design"].get("tail", {}).get("skill")
        tail_skills[layer] = sk
        if sk is not None and sk > 0:
            tail_skill_count += 1

    targets = {
        "F2_middle_rmse_mm": f2_mid, "F2_middle_target_mm": 4.0,
        "F2_middle_pass": bool(f2_mid is not None and f2_mid <= 4.0),
        "F2_resid_corr": f2_corr, "F2_resid_corr_target": 0.4,
        "F2_resid_corr_pass": bool(f2_corr is not None and f2_corr >= 0.4),
        "F2_baseline_mid_rmse_mm": F2_BASE_MID_RMSE,
        "F3_end_rmse_mm": f3_end, "F3_end_target_mm": 12.0,
        "F3_end_pass": bool(f3_end is not None and f3_end <= 12.0),
        "F3_end_error_mm": f3_enderr, "F3_end_error_target_mm": 10.0,
        "F3_end_error_pass": bool(f3_enderr is not None and abs(f3_enderr) <= 10.0),
        "F3_baseline_end_rmse_mm": F3_BASE_END_RMSE,
        "tail_skill_by_layer": tail_skills,
        "tail_skill_count_gt0": tail_skill_count,
        "tail_target_layers": 3,
        "tail_pass": bool(tail_skill_count >= 3),
    }

    f2_target_met = targets["F2_middle_pass"] and targets["F2_resid_corr_pass"]
    f3_target_met = targets["F3_end_pass"] and targets["F3_end_error_pass"]
    dp2_pass = targets["tail_pass"]

    # ── GATE M3 verdict ──
    if (f2_target_met or f3_target_met) and dp2_pass:
        verdict = "PASS"
    else:
        any_adopt = any(adoption[l]["adopted_model"] != "H0" for l in LAYERS_ORDER)
        verdict = "PARTIAL" if any_adopt else "FAIL"

    output = {
        "metadata": {
            "milestone": "M3 — Hybrid Model: Sub-Annual Dynamics and Acceleration",
            "plan": "super_plan_2026-06-10.md",
            "candidate_menu": "H0-H4 (fixed); selection by held-out skill only",
            "designs": DESIGNS, "tail_n_epochs": TAIL_N, "annual_period_epochs": T_A,
            "loader": "build_aligned_arrays from 13_holdout_method_bakeoff.py (M1-corrected lag)",
            "insar_harmonic_source": str(HARMONIC_FEATHER.relative_to(ROOT)),
            "insar_vertical_raw_status": "data/insar/timeseries/mlcw_interp_insar_IDW_extend.feather ABSENT on host; "
                                         "H4 uses persisted InSAR seasonal-harmonic series only (not fabricated).",
            "date": "2026-06-10",
        },
        "h3_sign_verification": h3sign,
        "vif_guard": vif_table,
        "admissibility": admissible,
        "registry": registry,
        "adoption_map": adoption,
        "targets_3_2_3": targets,
        "gate_m3_verdict": verdict,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(output, f, indent=2, default=_json_default)
    print(f"\nSaved registry: {OUT_JSON}")

    print("\n── Targets (3.2.3) ──")
    print(f"  F2 middle RMSE {f2_mid} mm (<=4.0? {targets['F2_middle_pass']}); "
          f"resid_corr {f2_corr} (>=0.4? {targets['F2_resid_corr_pass']}) -> F2 met={f2_target_met}")
    print(f"  F3 end RMSE {f3_end} mm (<=12? {targets['F3_end_pass']}); "
          f"end_error {f3_enderr} mm (|.|<=10? {targets['F3_end_error_pass']}) -> F3 met={f3_target_met}")
    print(f"  Tail skill>0 count {tail_skill_count}/6 (>=3? {dp2_pass})  per-layer {tail_skills}")
    print(f"\nGATE M3 VERDICT: {verdict}")
    return output


def _json_default(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, pd.Timestamp):
        return str(obj)
    raise TypeError(f"Not JSON serialisable: {type(obj)}")


if __name__ == "__main__":
    main()
