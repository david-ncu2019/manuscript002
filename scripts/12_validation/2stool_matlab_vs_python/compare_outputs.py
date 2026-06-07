"""Compare MATLAB vs Python 2S-TOOL outputs.

OODA Loop — Act phase: runs on all *_matlab/*_python pairs in the outputs/ directory.
Reports per-file and aggregate statistics.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

OUTPUTS_DIR = Path(__file__).resolve().parent / "outputs"
TOL_STRICT = 1e-10       # floating-point roundoff level
TOL_ACCEPTABLE = 1e-6     # user-specified tolerance
TOL_WARN = 1e-4            # worth flagging but not a failure

SUMMARY_FIELDS = ["skv", "ske_max", "ske_mean", "ske_min", "ske_weighted", "ske_std"]
INT_FIELDS = ["n_loops_total", "n_loops_accepted"]


def compare_summaries(matlab_path: Path, python_path: Path) -> dict:
    """Compare summary CSV files. Returns a per-field result dict."""
    m = pd.read_csv(matlab_path)
    p = pd.read_csv(python_path)

    results = {"label": matlab_path.parent.name.replace("_matlab", ""), "loops_match": None}
    all_ok = True

    for field in SUMMARY_FIELDS:
        mv, pv = float(m[field].iloc[0]), float(p[field].iloc[0])
        if mv == 0 and pv == 0:
            rel = 0.0
        elif mv == 0 or pv == 0:
            rel = abs(mv - pv)
        else:
            rel = abs(mv - pv) / max(abs(mv), abs(pv))
        results[field] = {"matlab": mv, "python": pv, "rel_diff": rel}
        if rel > TOL_ACCEPTABLE:
            all_ok = False

    for field in INT_FIELDS:
        mv, pv = int(m[field].iloc[0]), int(p[field].iloc[0])
        results[field] = {"matlab": mv, "python": pv, "match": mv == pv}
        if mv != pv:
            all_ok = False

    # Compare hc separately (informational — may differ due to multi-source resolution)
    m_hc = float(m["hc"].iloc[0])
    p_hc = float(p["hc"].iloc[0])
    results["hc"] = {"matlab": m_hc, "python": p_hc, "diff_m": abs(m_hc - p_hc)}

    results["all_ok"] = all_ok
    return results


def compare_loops(matlab_path: Path, python_path: Path) -> dict:
    """Compare loops CSV files row-by-row. Returns match statistics."""
    m = pd.read_csv(matlab_path)
    p = pd.read_csv(python_path)

    if len(m) != len(p):
        return {"n_matlab": len(m), "n_python": len(p), "match": False,
                "max_rel_slope": np.inf, "max_rel_ske": np.inf}

    # Compare slope and s_ke columns (key physical outputs)
    slope_rel = np.zeros(len(m))
    ske_rel = np.zeros(len(m))
    for i in range(len(m)):
        ms, ps = float(m["slope"].iloc[i]), float(p["slope"].iloc[i])
        slope_rel[i] = abs(ms - ps) / max(abs(ms), abs(ps)) if max(abs(ms), abs(ps)) > 0 else 0

        mk, pk = float(m["s_ke"].iloc[i]), float(p["s_ke"].iloc[i])
        ske_rel[i] = abs(mk - pk) / max(abs(mk), abs(pk)) if max(abs(mk), abs(pk)) > 0 else 0

    # Check accepted flags match
    acc_match = np.all(m["accepted"].values == p["accepted"].values)

    return {
        "n_loops": len(m), "n_match": len(m),
        "accepted_flags_match": bool(acc_match),
        "max_rel_slope": float(np.max(slope_rel)),
        "max_rel_ske": float(np.max(ske_rel)),
        "slope_strict_ok": bool(np.all(slope_rel < TOL_STRICT)),
        "ske_strict_ok": bool(np.all(ske_rel < TOL_STRICT)),
        "slope_acceptable_ok": bool(np.all(slope_rel < TOL_ACCEPTABLE)),
        "ske_acceptable_ok": bool(np.all(ske_rel < TOL_ACCEPTABLE)),
    }


def main() -> int:
    matlab_dirs = sorted(OUTPUTS_DIR.glob("*_matlab"))
    if not matlab_dirs:
        print(f"ERROR: No *_matlab directories found in {OUTPUTS_DIR}")
        return 1

    n_pairs = 0
    summary_results = []
    loop_results = []

    for md in matlab_dirs:
        stem = md.name.replace("_matlab", "")
        pd_path = OUTPUTS_DIR / f"{stem}_python"
        if not pd_path.is_dir():
            print(f"SKIP {stem}: no matching _python directory")
            continue

        n_pairs += 1
        m_sum = md / f"{stem}_summary.csv"
        p_sum = pd_path / f"{stem}_summary.csv"
        m_loop = md / f"{stem}_loops.csv"
        p_loop = pd_path / f"{stem}_loops.csv"

        if not all(p.exists() for p in [m_sum, p_sum, m_loop, p_loop]):
            print(f"SKIP {stem}: missing CSV files")
            continue

        sr = compare_summaries(m_sum, p_sum)
        lr = compare_loops(m_loop, p_loop)
        summary_results.append(sr)
        loop_results.append(lr)

    # ── Print report ──────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"2S-TOOL MATLAB vs Python — Cross-Validation Report")
    print(f"{'='*70}")
    print(f"Pairs compared: {n_pairs}")
    print(f"Tolerance (strict):    {TOL_STRICT:.0e}")
    print(f"Tolerance (acceptable): {TOL_ACCEPTABLE:.0e}")
    print()

    # Summary table
    print(f"── Summary CSV comparison ──")
    header = f"{'File':<22} {'S_kv':>14} {'S_ke_w':>14} {'S_ke_mean':>14} {'loops':>10} {'hc Δ(m)':>10} {'Verdict':>10}"
    print(header)
    print("-" * len(header))

    all_summary_ok = True
    for sr in summary_results:
        skv_r = sr["skv"]["rel_diff"]
        skw_r = sr["ske_weighted"]["rel_diff"]
        skm_r = sr["ske_mean"]["rel_diff"]
        n_ok = sr["n_loops_total"]["match"] and sr["n_loops_accepted"]["match"]
        loops_str = f"{sr['n_loops_total']['matlab']}/{sr['n_loops_accepted']['matlab']}"
        hc_d = sr["hc"]["diff_m"]
        ok = sr["all_ok"] and n_ok
        if not ok:
            all_summary_ok = False
        verdict = "PASS" if ok else "FAIL"
        print(f"{sr['label']:<22} {skv_r:14.2e} {skw_r:14.2e} {skm_r:14.2e} {loops_str:>10} {hc_d:10.2e} {verdict:>10}")

    print()

    # Loops table
    print(f"── Loops CSV comparison ──")
    lheader = f"{'File':<22} {'n_loops':>8} {'max_rel_slope':>14} {'max_rel_ske':>14} {'acc_flags':>10} {'Verdict':>10}"
    print(lheader)
    print("-" * len(lheader))

    all_loops_ok = True
    for lr in loop_results:
        if "n_matlab" in lr:
            print(f"  LOOP COUNT MISMATCH: {lr['n_matlab']} vs {lr['n_python']}")
            all_loops_ok = False
        else:
            ok = lr["ske_acceptable_ok"] and lr["slope_acceptable_ok"]
            if not ok:
                all_loops_ok = False
            verdict = "PASS" if ok else "FAIL"
            print(f"{'':<22} {lr['n_loops']:>8} {lr['max_rel_slope']:14.2e} {lr['max_rel_ske']:14.2e} "
                  f"{'OK' if lr['accepted_flags_match'] else 'MISMATCH':>10} {verdict:>10}")

    print()
    print(f"{'='*70}")
    if all_summary_ok and all_loops_ok:
        print("VERDICT: ALL PASS — Python faithfully reproduces MATLAB results")
    else:
        print("VERDICT: DISCREPANCIES DETECTED — see details above")
    print(f"{'='*70}")

    return 0 if (all_summary_ok and all_loops_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
