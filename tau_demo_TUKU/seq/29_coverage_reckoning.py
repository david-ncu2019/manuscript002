"""
29_coverage_reckoning.py — Red Team Task D: Honest coverage reckoning.

Physical story: The split-conformal 90% prediction band around each layer forecast was
declared "UNDETERMINED" by evaluating only 2–6 toy points from 2024.  This script
recomputes coverage honestly over the full 60-point blind era (2019–2023) where band
definitions were earned by real assimilation events, and also persists the 2024
prediction timeseries that was previously missing from disk (the artifact whose absence
the Red Team flagged as F-6).

Resolves:
  F-2: honest blind-era coverage with n >= 20 minimum and Clopper-Pearson CIs
  F-6 / §2: 2024 prediction timeseries persisted to disk; all grades labelled PROVISIONAL

Usage:
    $env:PYTHONPATH=""; conda run -n fafalab2 python tau_demo_TUKU/seq/29_coverage_reckoning.py

Outputs:
    tau_demo_TUKU/results/seq/red_team_fixes/coverage_reckoning.json
    tau_demo_TUKU/results/seq/red_team_fixes/coverage_reckoning.csv
    tau_demo_TUKU/results/seq/red_team_fixes/confirmatory_2024_timeseries_<LAYER>_<sched>.csv
    tau_demo_TUKU/plots/seq/red_team_fixes/coverage_vs_cadence.png
    tau_demo_TUKU/results/seq/red_team_fixes/29_coverage_reckoning_run_log.txt
"""

from __future__ import annotations

import copy
import importlib.util as _ilu
import json
import math
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import beta as _beta_dist

warnings.filterwarnings("ignore", category=UserWarning)

# ── Paths ──────────────────────────────────────────────────────────────────────
_HERE      = Path(__file__).resolve()
_TAU_DEMO  = _HERE.parent.parent       # tau_demo_TUKU/
_ROOT      = _TAU_DEMO.parent          # repo root

for _p in [str(_TAU_DEMO), str(_ROOT), str(_ROOT / "scripts")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── Configuration ──────────────────────────────────────────────────────────────
LAYERS = ["F1", "T1", "F2", "T2", "F3", "F4"]

# Schedules in sparse-to-dense order for plotting.
# anchor_once lives in red_team_fixes/anchor_once/
STANDARD_SCHEDS = ["none", "annual", "semiannual", "quarterly", "monthly", "blackout", "actual"]

# Red Team cross-check reference (semiannual, n=27, full-set): exact values to verify against.
REDTEAM_SEMIANNUAL = {
    "F1": 0.667,
    "T1": 0.815,
    "F2": 0.852,
    "T2": 0.852,
    "F3": 0.778,
    "F4": 0.889,
}
REDTEAM_SEMIANNUAL_N = 27

# Pre-registered coverage criterion
MIN_N_FOR_VERDICT = 20
MIN_LAYERS_PASS = 5
COV_TARGET = 0.85
COV_NOMINAL = 0.90

# First genuine blind visit (drop from post-entry count).
FIRST_BLIND_VISIT_ISO = "2019-01-11T00:00:00"

SEQ_RESULTS = _TAU_DEMO / "results" / "seq"
RF_DIR      = SEQ_RESULTS / "red_team_fixes"
PLOTS_RF    = _TAU_DEMO / "plots" / "seq" / "red_team_fixes"
RF_DIR.mkdir(parents=True, exist_ok=True)
PLOTS_RF.mkdir(parents=True, exist_ok=True)

LOG_PATH = RF_DIR / "29_coverage_reckoning_run_log.txt"

# ── Logging ────────────────────────────────────────────────────────────────────
_log_lines: list[str] = []


def _log(msg: str = "") -> None:
    print(msg)
    _log_lines.append(msg)


def _flush_log() -> None:
    with open(LOG_PATH, "w", encoding="utf-8") as fh:
        fh.write("\n".join(_log_lines) + "\n")


# ── Clopper-Pearson exact binomial CI ─────────────────────────────────────────
def clopper_pearson_ci(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Return (lower, upper) 95% Clopper-Pearson CI for proportion k/n.

    Handles edge cases k=0 and k=n.
    scipy.stats.beta.ppf convention:
      lower = Beta(alpha/2; k,   n-k+1)
      upper = Beta(1-alpha/2; k+1, n-k)
    """
    if n == 0:
        return (float("nan"), float("nan"))
    lo: float = 0.0 if k == 0 else float(_beta_dist.ppf(alpha / 2, k, n - k + 1))
    hi: float = 1.0 if k == n else float(_beta_dist.ppf(1.0 - alpha / 2, k + 1, n - k))
    return (lo, hi)


# ── Load innovations + timeseries for one schedule + layer ────────────────────
def load_sched_layer(sched: str, layer: str) -> dict | None:
    """Return dict with innovations list and timeseries half_width lookup.

    Returns None if metrics.json or timeseries CSV does not exist for this
    schedule / layer combination.
    """
    if sched == "anchor_once":
        base = RF_DIR / "anchor_once"
    else:
        base = SEQ_RESULTS / sched

    mpath = base / "metrics.json"
    cpath = base / f"TUKU_{layer}_seq_timeseries.csv"

    if not mpath.exists():
        return None
    if not cpath.exists():
        return None

    with open(mpath) as fh:
        j = json.load(fh)

    if layer not in j.get("layers", {}):
        return None

    layer_data = j["layers"][layer]
    innovations = layer_data.get("innovations", [])

    # Build date → half_width lookup from timeseries CSV.
    csv_df = pd.read_csv(cpath)
    hw_lookup: dict[str, float | None] = {}
    for _, row in csv_df.iterrows():
        d = str(row["date"])
        hw_raw = row.get("half_width_mm", "")
        if hw_raw == "" or hw_raw is None:
            hw_lookup[d] = None
        else:
            try:
                v = float(hw_raw)
                hw_lookup[d] = v if math.isfinite(v) else None
            except (ValueError, TypeError):
                hw_lookup[d] = None

    return {
        "innovations":      innovations,
        "hw_lookup":        hw_lookup,
        "stored_coverage":  layer_data.get("band_coverage_fraction"),
        "stored_n_hw":      layer_data.get("n_hw_defined_visits", 0),
    }


# ── Compute per-layer coverage stats ──────────────────────────────────────────
def compute_coverage_stats(
    innovations: list[dict],
    hw_lookup: dict[str, float | None],
) -> dict:
    """Compute full-set and post-entry coverage with Clopper-Pearson CIs.

    Band-defined points: those where hw_lookup[date] is finite (cross-referenced
    from timeseries CSV).  This reproduces the stored band_coverage_fraction from
    24_walk_forward_rehearsal.py lines 580-588.

    Full-set:  all band-defined scoring points.
    Post-entry: drop the first genuine blind visit (2019-01-11) if band-defined.
    """
    # Identify band-defined points
    hw_defined = []
    for inn in innovations:
        d = inn["date"]
        hw = hw_lookup.get(d)
        if hw is not None and math.isfinite(hw):
            hw_defined.append(inn)

    n_full = len(hw_defined)
    k_full = sum(1 for r in hw_defined if r["in_band"])
    cov_full = (k_full / n_full) if n_full > 0 else float("nan")
    ci_full = clopper_pearson_ci(k_full, n_full)

    # Post-entry: drop first visit if present
    hw_defined_post = [r for r in hw_defined if r["date"] != FIRST_BLIND_VISIT_ISO]
    n_post = len(hw_defined_post)
    k_post = sum(1 for r in hw_defined_post if r["in_band"])
    cov_post = (k_post / n_post) if n_post > 0 else float("nan")
    ci_post = clopper_pearson_ci(k_post, n_post)

    return {
        "n_band_defined":       n_full,
        "k_in_band_full":       k_full,
        "coverage_full":        round(cov_full, 4) if math.isfinite(cov_full) else None,
        "CI95_low_full":        round(ci_full[0], 4),
        "CI95_high_full":       round(ci_full[1], 4),
        "n_band_defined_post":  n_post,
        "k_in_band_post":       k_post,
        "coverage_postentry":   round(cov_post, 4) if math.isfinite(cov_post) else None,
        "CI95_low_post":        round(ci_post[0], 4),
        "CI95_high_post":       round(ci_post[1], 4),
    }


# ── Cross-check against Red Team ──────────────────────────────────────────────
def cross_check_redteam(cov_stats: dict[str, dict]) -> dict[str, dict]:
    """Compare full-set semiannual coverage against Red Team reference values.

    Returns dict of {layer: {delta, pass}} where pass = abs(delta) <= 0.01.
    """
    result = {}
    all_pass = True
    for layer in LAYERS:
        if layer not in cov_stats:
            result[layer] = {"our_coverage": None, "redteam_coverage": REDTEAM_SEMIANNUAL[layer],
                             "delta": None, "pass": False}
            all_pass = False
            continue
        our = cov_stats[layer].get("coverage_full")
        rt  = REDTEAM_SEMIANNUAL[layer]
        if our is None:
            result[layer] = {"our_coverage": None, "redteam_coverage": rt, "delta": None, "pass": False}
            all_pass = False
        else:
            delta = round(abs(our - rt), 4)
            passed = (delta <= 0.01)
            result[layer] = {"our_coverage": our, "redteam_coverage": rt, "delta": delta, "pass": passed}
            if not passed:
                all_pass = False
    result["all_pass"] = all_pass
    return result


# ── Per-cadence verdict ────────────────────────────────────────────────────────
def cadence_verdict(sched: str, cov_stats: dict[str, dict]) -> dict:
    """Classify cadence as PASS / FAIL / INSUFFICIENT_N.

    Uses pre-registered criterion: coverage >= 0.85 on >= 5/6 layers,
    evaluated ONLY where n_band_defined >= 20.
    """
    n_sufficient = 0
    n_pass = 0
    layer_verdicts: dict[str, str] = {}
    for layer in LAYERS:
        stats = cov_stats.get(layer, {})
        n = stats.get("n_band_defined", 0)
        cov = stats.get("coverage_full")
        if n < MIN_N_FOR_VERDICT:
            layer_verdicts[layer] = f"INSUFFICIENT_N (n={n})"
        elif cov is None:
            layer_verdicts[layer] = "UNDEFINED"
        elif cov >= COV_TARGET:
            layer_verdicts[layer] = f"PASS ({cov:.3f})"
            n_pass += 1
            n_sufficient += 1
        else:
            layer_verdicts[layer] = f"FAIL ({cov:.3f})"
            n_sufficient += 1

    # Count how many layers had n>=20
    n_with_n = sum(1 for L in LAYERS
                   if (cov_stats.get(L, {}).get("n_band_defined", 0) >= MIN_N_FOR_VERDICT))

    if n_with_n < MIN_LAYERS_PASS:
        overall = "INSUFFICIENT_N"
        verdict_str = (
            f"INSUFFICIENT_N — fewer than {MIN_LAYERS_PASS}/6 layers reach n≥{MIN_N_FOR_VERDICT} "
            f"band-defined points (only {n_with_n}/6 qualify)."
        )
    elif n_pass >= MIN_LAYERS_PASS:
        overall = "PASS"
        verdict_str = (
            f"PASS — split-conformal as configured reaches ≥0.85 on "
            f"{n_pass}/6 layers at {sched} cadence (n≥{MIN_N_FOR_VERDICT})."
        )
    else:
        overall = "FAIL"
        verdict_str = (
            f"FAIL — split-conformal as configured is a failed uncertainty quantifier "
            f"at {sched} cadence for this record (only {n_pass}/6 layers reach 0.85 "
            f"on n≥{MIN_N_FOR_VERDICT})."
        )

    return {
        "overall_verdict": overall,
        "verdict_string":  verdict_str,
        "n_layers_pass":   n_pass,
        "n_layers_n_sufficient": n_with_n,
        "layer_verdicts":  layer_verdicts,
    }


# ── Part 1: honest blind-era coverage ─────────────────────────────────────────
def part1_coverage_reckoning() -> dict:
    """Compute coverage stats for all schedules × layers.  Returns master dict."""
    _log("=" * 72)
    _log("PART 1 — Honest blind-era coverage (resolves Red Team F-2)")
    _log("=" * 72)

    all_scheds = STANDARD_SCHEDS + ["anchor_once"]
    output: dict = {
        "schedules": {},
        "cross_check_semiannual_vs_redteam": None,
        "cadence_verdicts": {},
        "leakage_manifest": [],
    }

    for sched in all_scheds:
        _log(f"\n--- Schedule: {sched} ---")
        cov_per_layer: dict[str, dict] = {}
        leakage_this: list[str] = []

        for layer in LAYERS:
            data = load_sched_layer(sched, layer)
            if data is None:
                _log(f"  {layer}: metrics.json or timeseries CSV not found — skipping")
                continue

            stats = compute_coverage_stats(data["innovations"], data["hw_lookup"])
            cov_per_layer[layer] = stats

            # Verify stored value matches our recomputed full-set coverage
            stored = data["stored_coverage"]
            our    = stats["coverage_full"]
            if stored is not None and our is not None:
                delta_stored = abs(our - stored)
                match_str = "OK" if delta_stored < 0.002 else f"MISMATCH delta={delta_stored:.4f}"
            else:
                match_str = "stored=None" if stored is None else "our=None"

            _log(
                f"  {layer}: n_full={stats['n_band_defined']:2d}  "
                f"cov_full={our if our is not None else 'N/A':>6}  "
                f"CI=[{stats['CI95_low_full']:.3f},{stats['CI95_high_full']:.3f}]  "
                f"n_post={stats['n_band_defined_post']:2d}  "
                f"cov_post={stats['coverage_postentry'] if stats['coverage_postentry'] is not None else 'N/A'}  "
                f"stored_check={match_str}"
            )

        output["schedules"][sched] = cov_per_layer

        # Cadence verdict
        verd = cadence_verdict(sched, cov_per_layer)
        output["cadence_verdicts"][sched] = verd
        _log(f"  VERDICT [{sched}]: {verd['verdict_string']}")

        # Leakage manifest (from metrics.json)
        if sched != "anchor_once":
            mpath = (RF_DIR / "anchor_once" / "metrics.json"
                     if sched == "anchor_once"
                     else SEQ_RESULTS / sched / "metrics.json")
        else:
            mpath = RF_DIR / "anchor_once" / "metrics.json"
        if mpath.exists():
            with open(mpath) as fh:
                j = json.load(fh)
            if j.get("leakage_fired"):
                msg = f"LEAKAGE FIRED in schedule={sched}"
                leakage_this.append(msg)
                output["leakage_manifest"].append(msg)
                _log(f"  *** {msg} ***")

    # Cross-check: semiannual vs Red Team
    _log("\n--- Cross-check: semiannual full-set coverage vs Red Team ---")
    semi_cov = output["schedules"].get("semiannual", {})
    cc = cross_check_redteam(semi_cov)
    output["cross_check_semiannual_vs_redteam"] = cc

    all_pass = True
    for layer in LAYERS:
        entry = cc[layer]
        our   = entry.get("our_coverage")
        rt    = entry.get("redteam_coverage")
        delta = entry.get("delta")
        ok    = entry.get("pass", False)
        if not ok:
            all_pass = False
        _log(
            f"  {layer}: ours={our}  RedTeam={rt}  delta={delta}  "
            f"{'OK' if ok else 'MISMATCH'}"
        )

    if all_pass:
        _log("  CROSS-CHECK PASSED — all deltas ≤ 0.01")
    else:
        _log("  CROSS-CHECK FAILED — see mismatches above")
        _log("  BLOCKED: band-defined filter differs from Red Team's independent_metrics.csv")

    # Semiannual-specific required FAIL string
    semi_verd = output["cadence_verdicts"].get("semiannual", {})
    n_pass_semi = semi_verd.get("n_layers_pass", 0)
    if semi_verd.get("overall_verdict") == "FAIL":
        fail_str = (
            f"FAIL — split-conformal as configured is a failed uncertainty quantifier "
            f"at semiannual cadence for this record "
            f"(only {n_pass_semi}/6 layers reach 0.85 on n≥{MIN_N_FOR_VERDICT})."
        )
        output["coverage_verdict_semiannual"] = fail_str
    else:
        output["coverage_verdict_semiannual"] = semi_verd.get("verdict_string", "")

    _log(f"\n  semiannual official verdict: {output['coverage_verdict_semiannual']}")

    return output


# ── Part 2: 2024 confirmatory with persisted timeseries ───────────────────────
def part2_confirmatory_2024_with_timeseries() -> dict:
    """Re-run 25_confirmatory_2024.py's forward walk and persist per-layer timeseries.

    This is the fix for Red Team F-6 / §2: the 2024 prediction timeseries was
    previously absent from disk, making results unverifiable.

    Replication approach: load the same engine modules as 25_confirmatory_2024.py,
    call its run_continuous_walk() and seed_conformal_bank() functions directly.
    All 2024 grades are labelled PROVISIONAL per truth_provenance_summary.json:
    the ring source is 100% non-integer in 2024 → not field-verifiable.
    """
    _log("\n" + "=" * 72)
    _log("PART 2 — 2024 confirmatory: persist timeseries (resolves Red Team F-6/§2)")
    _log("=" * 72)

    # Load 25_confirmatory_2024.py via importlib (digit-prefixed module name)
    _conf_path = _HERE.parent / "25_confirmatory_2024.py"
    _spec = _ilu.spec_from_file_location("_conf25", _conf_path)
    _conf25 = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_conf25)

    # Engine imports re-used from 25's module namespace
    run_continuous_walk       = _conf25.run_continuous_walk
    build_2024_schedules      = _conf25.build_2024_schedules
    compute_2024_metrics      = _conf25.compute_2024_metrics
    load_genuine_truth        = _conf25.load_genuine_truth
    align_genuine_to_epoch    = _conf25.align_genuine_to_epoch
    load_frozen_models        = _conf25.load_frozen_models
    build_all_drivers         = _conf25.build_all_drivers

    # Seed function: load from 24 (25 already imported it)
    seed_conformal_bank       = _conf25.seed_conformal_bank

    # Load data (identical to 25_confirmatory_2024.py main())
    _log("\nLoading frozen models and building driver frames...")
    frozen_models = load_frozen_models()
    frames        = build_all_drivers()
    truth_df      = load_genuine_truth()

    # Align genuine truth to 5-day grid (full era 2019-2024)
    ref_frame  = frames[LAYERS[0]]
    all_epochs = ref_frame.loc[
        (ref_frame["date"] >= _conf25.BLIND_START) &
        (ref_frame["date"] <= _conf25.CONF_END),
        "date",
    ]
    truth_aligned = align_genuine_to_epoch(truth_df, all_epochs)
    _log(f"  truth_aligned rows: {len(truth_aligned)}")

    # Genuine dates 2019–2024
    genuine_dates_all = pd.DatetimeIndex(truth_aligned["model_date"].unique())
    _log(f"  Genuine aligned dates 2019–2024: {len(genuine_dates_all)}")

    # Build schedules
    schedules = build_2024_schedules(genuine_dates_all)
    _log(f"  Schedules: { {k: len(v) for k, v in schedules.items()} }")

    # Seed conformal bank (same as 25: semiannual seed schedule)
    _log("  Seeding conformal bank (2015-2018 rehearsal)...")
    # Use semiannual seed dates (mirrors 25's main)
    semi_dates_all = pd.DatetimeIndex(
        sorted(schedules["semiannual"])
    )
    bank_seed = seed_conformal_bank(
        list(semi_dates_all),
        frames,
        align_genuine_to_epoch(
            truth_df,
            ref_frame.loc[
                (ref_frame["date"] >= _conf25.SEED_START) &
                (ref_frame["date"] <= _conf25.SEED_END),
                "date",
            ],
        ),
        _conf25._rehearsal.estimate_carrier_noise(
            _conf25.GPS_CSV,
            _conf25.SEED_START,
            _conf25.SEED_END,
        ) if hasattr(_conf25, "_rehearsal") else float("nan"),
    )

    # GPS last epoch
    gps_df = pd.read_csv(_conf25.GPS_CSV)
    gps_df["date"] = pd.to_datetime(gps_df["date"])
    last_gps_epoch = str(gps_df["date"].max().date())
    _log(f"  GPS last epoch: {last_gps_epoch}")

    output: dict = {
        "task": "F-6 fix — 2024 confirmatory timeseries persisted to disk",
        "gps_last_epoch": last_gps_epoch,
        "ground_truth_2024_status": (
            "NOT field-verifiable (ring source 100% non-integer in 2024 per "
            "truth_provenance_summary.json); grades are provisional, must not be "
            "cited as blind-generalization evidence."
        ),
        "schedules": {},
    }

    reconst_csv = _conf25.RECONST_CSV
    reconst_df  = pd.read_csv(reconst_csv)
    reconst_df["datetime"] = pd.to_datetime(reconst_df["datetime"])

    for sched_name, visit_dates in schedules.items():
        _log(f"\n  Running schedule '{sched_name}'...")

        # Deep-copy bank so each schedule gets independent conformal state
        bank_this = copy.deepcopy(bank_seed)

        result = run_continuous_walk(
            schedule_name  = sched_name,
            visit_dates    = visit_dates,
            frames         = frames,
            frozen_models  = frozen_models,
            bank_seed      = bank_this,
            truth_aligned  = truth_aligned,
        )

        ts_rows_all  = result["ts_rows"]
        preq_2024    = result["preq_2024"]
        leakage      = result["leakage_fired"]

        # Persist per-layer timeseries CSV for ALL of 2024 (each 5-day epoch)
        for layer in LAYERS:
            ts_2024 = [r for r in ts_rows_all[layer] if r.get("is_2024", False)]
            if not ts_2024:
                _log(f"    {layer}: no 2024 epochs — GPS may not extend into 2024")
                continue

            # Merge in obs_if_visit from preq_2024 by date
            preq_lookup = {r["date"]: r for r in preq_2024[layer]}
            rows_out = []
            for r in ts_2024:
                d  = r["date"]
                pq = preq_lookup.get(d, {})
                rows_out.append({
                    "date":          d,
                    "pred_mm":       r.get("pred_mm"),
                    "half_width_mm": r.get("half_width_mm"),
                    "horizon_epochs": r.get("horizon_epochs"),
                    "obs_if_visit":  pq.get("obs_mm"),
                    "in_band":       pq.get("in_band"),
                    "is_scheduled_visit": pq.get("is_scheduled_visit"),
                    "grade_status":  "PROVISIONAL — ring source 100% non-integer in 2024",
                })

            out_csv = RF_DIR / f"confirmatory_2024_timeseries_{layer}_{sched_name}.csv"
            pd.DataFrame(rows_out).to_csv(out_csv, index=False)
            _log(f"    {layer}: persisted {len(rows_out)} 2024 epochs → {out_csv.name}")

        # Compute 2024 metrics
        metrics_2024 = compute_2024_metrics(
            sched_name, preq_2024, ts_rows_all, reconst_df
        )

        # Summarise per layer
        _log(f"  Metrics 2024 [{sched_name}]:")
        for layer in LAYERS:
            m = metrics_2024[layer]
            n_pts = m.get("n_2024_points", 0)
            mae   = m.get("MAE_mm")
            rmse  = m.get("RMSE_mm")
            cov   = m.get("band_coverage_fraction")
            _log(
                f"    {layer}: n={n_pts}  MAE={mae}  RMSE={rmse}  "
                f"coverage={cov}  PROVISIONAL"
            )

        output["schedules"][sched_name] = {
            "leakage_fired": leakage,
            "layers": {
                L: {
                    **metrics_2024[L],
                    "grade_status": "PROVISIONAL",
                    "ground_truth_2024_status": (
                        "NOT field-verifiable (ring source 100% non-integer in 2024 "
                        "per truth_provenance_summary.json); grades are provisional, "
                        "must not be cited as blind-generalization evidence."
                    ),
                }
                for L in LAYERS
            },
        }

    return output


# ── Plot: coverage vs cadence ──────────────────────────────────────────────────
def plot_coverage_vs_cadence(
    all_coverage: dict,
    out_path: Path,
) -> None:
    """Coverage vs cadence for all scoring schedules.

    x-axis: ordered sparse → dense: none, annual, semiannual, quarterly, monthly.
    y-axis: coverage (full-set).
    One line per layer with Clopper-Pearson CI whiskers.
    Hollow / greyed markers for n < 20.
    Horizontal lines at 0.85 (target) and 0.90 (nominal).
    300 dpi, fonts >= 14, axis labels, grid, tight, tab10.
    """
    # Order for plotting (cadence axis, sparse → dense)
    plot_scheds = ["none", "annual", "semiannual", "quarterly", "monthly"]
    x_labels    = ["none\n(0 visits)", "annual\n(~5 visits)", "semiannual\n(~11 visits)",
                   "quarterly\n(~20 visits)", "monthly\n(~60 visits)"]
    x_pos       = list(range(len(plot_scheds)))

    tab10 = matplotlib.colormaps["tab10"]
    layer_colors = {L: tab10(i) for i, L in enumerate(LAYERS)}

    fig, ax = plt.subplots(figsize=(12, 7))

    for layer in LAYERS:
        covs, ci_lows, ci_highs, xs_plot = [], [], [], []
        hollow_xs, hollow_ys = [], []

        for xi, sched in enumerate(plot_scheds):
            stats = all_coverage.get(sched, {}).get(layer, {})
            cov   = stats.get("coverage_full")
            n     = stats.get("n_band_defined", 0)
            ci_lo = stats.get("CI95_low_full",  float("nan"))
            ci_hi = stats.get("CI95_high_full", float("nan"))

            if cov is None:
                continue

            if n < MIN_N_FOR_VERDICT:
                hollow_xs.append(xi)
                hollow_ys.append(cov)
            else:
                covs.append(cov)
                ci_lows.append(ci_lo)
                ci_highs.append(ci_hi)
                xs_plot.append(xi)

        c = layer_colors[layer]

        # Solid markers for n >= 20
        if xs_plot:
            ax.errorbar(
                xs_plot, covs,
                yerr=[
                    [max(0, covs[i] - ci_lows[i]) for i in range(len(covs))],
                    [max(0, ci_highs[i] - covs[i]) for i in range(len(covs))],
                ],
                fmt="o-", color=c, label=layer, lw=1.8, ms=7,
                capsize=4, elinewidth=1.2, zorder=3,
            )

        # Hollow markers for n < 20
        if hollow_xs:
            ax.plot(
                hollow_xs, hollow_ys,
                "o", color=c, mfc="none", mec=c, ms=8, alpha=0.5, zorder=2,
            )
            for xi_h, yi_h in zip(hollow_xs, hollow_ys):
                ax.annotate(
                    "n<20", xy=(xi_h, yi_h),
                    xytext=(4, 6), textcoords="offset points",
                    fontsize=10, color="gray",
                )

    # Reference lines
    ax.axhline(COV_TARGET,  color="red",    lw=1.8, ls="--", label=f"Target ≥{COV_TARGET}")
    ax.axhline(COV_NOMINAL, color="orange", lw=1.4, ls=":",  label=f"Nominal {COV_NOMINAL}")

    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_labels, fontsize=13)
    ax.set_xlabel("Cadence (sparse → dense)", fontsize=14)
    ax.set_ylabel("Coverage (fraction within 90% band)", fontsize=14)
    ax.set_title(
        "Split-conformal band coverage vs cadence — TUKU blind era (2019–2023)\n"
        "Clopper–Pearson 95% CI shown; hollow = n<20 (excluded from criterion)",
        fontsize=14,
    )
    ax.set_ylim(-0.05, 1.10)
    ax.tick_params(labelsize=13)
    ax.legend(fontsize=12, loc="lower right")
    ax.grid(True, alpha=0.4)
    fig.tight_layout()
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    _log(f"\nPlot saved: {out_path}")


# ── Build flat CSV ─────────────────────────────────────────────────────────────
def build_flat_csv(all_coverage: dict, out_path: Path) -> None:
    """Write schedule × layer × coverage stats to flat CSV."""
    rows = []
    for sched, layer_dict in all_coverage.items():
        for layer, stats in layer_dict.items():
            rows.append({
                "schedule":           sched,
                "layer":              layer,
                "n_band_defined":     stats.get("n_band_defined"),
                "k_in_band_full":     stats.get("k_in_band_full"),
                "coverage_full":      stats.get("coverage_full"),
                "CI95_low_full":      stats.get("CI95_low_full"),
                "CI95_high_full":     stats.get("CI95_high_full"),
                "n_band_defined_post": stats.get("n_band_defined_post"),
                "k_in_band_post":     stats.get("k_in_band_post"),
                "coverage_postentry": stats.get("coverage_postentry"),
                "CI95_low_post":      stats.get("CI95_low_post"),
                "CI95_high_post":     stats.get("CI95_high_post"),
            })
    pd.DataFrame(rows).to_csv(out_path, index=False)
    _log(f"Flat CSV saved: {out_path}")


# ── JSON encoder ───────────────────────────────────────────────────────────────
class _NpEnc(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer,)):   return int(obj)
        if isinstance(obj, (np.floating,)):  return float(obj)
        if isinstance(obj, (np.bool_,)):     return bool(obj)
        if isinstance(obj, np.ndarray):      return obj.tolist()
        return super().default(obj)


# ── Main ───────────────────────────────────────────────────────────────────────
def main() -> None:
    _log("29_coverage_reckoning.py — Red Team F-2 + F-6 resolution")
    _log(f"Run date: 2026-06-12")
    _log(f"Repo root: {_ROOT}")

    # Part 1
    part1 = part1_coverage_reckoning()

    # Part 2
    part2 = part2_confirmatory_2024_with_timeseries()

    # Build combined JSON output
    out_json: dict = {
        "script":           "29_coverage_reckoning.py",
        "red_team_findings_resolved": ["F-2", "F-6"],
        "description": (
            "Part 1: honest blind-era (2019-2023) split-conformal band coverage "
            "recomputed over full n=27-60 band-defined points per layer. "
            "Part 2: 2024 prediction timeseries persisted to disk; all grades PROVISIONAL."
        ),
        # Part 1 results
        "coverage_per_schedule_per_layer": part1["schedules"],
        "cadence_verdicts": part1["cadence_verdicts"],
        "coverage_verdict_semiannual": part1["coverage_verdict_semiannual"],
        "cross_check_semiannual_vs_redteam": part1["cross_check_semiannual_vs_redteam"],
        "leakage_manifest": part1["leakage_manifest"],
        # Part 2 results
        "confirmatory_2024": part2,
    }

    out_json_path = RF_DIR / "coverage_reckoning.json"
    with open(out_json_path, "w", encoding="utf-8") as fh:
        json.dump(out_json, fh, indent=2, cls=_NpEnc)
    _log(f"\ncoverage_reckoning.json saved: {out_json_path}")

    # Flat CSV
    csv_path = RF_DIR / "coverage_reckoning.csv"
    build_flat_csv(part1["schedules"], csv_path)

    # Plot
    plot_path = PLOTS_RF / "coverage_vs_cadence.png"
    plot_coverage_vs_cadence(part1["schedules"], plot_path)

    # Final summary to log
    _log("\n" + "=" * 72)
    _log("FINAL SUMMARY")
    _log("=" * 72)
    cc_all_pass = part1["cross_check_semiannual_vs_redteam"].get("all_pass", False)
    _log(f"Cross-check semiannual vs Red Team: {'PASSED' if cc_all_pass else 'FAILED'}")
    for sched, verd in part1["cadence_verdicts"].items():
        _log(f"  {sched:12s}: {verd['overall_verdict']:20s}  n_layers_pass={verd['n_layers_pass']}")
    _log(f"\nSemiannual official verdict: {part1['coverage_verdict_semiannual']}")
    _log(f"\n2024 confirmatory status: {part2['ground_truth_2024_status']}")
    _log(f"2024 GPS last epoch: {part2['gps_last_epoch']}")
    _log("\n2024 timeseries CSVs persisted:")
    for sched_name in ["semiannual", "annual"]:
        for layer in LAYERS:
            p = RF_DIR / f"confirmatory_2024_timeseries_{layer}_{sched_name}.csv"
            if p.exists():
                _log(f"  {p.name}")

    _flush_log()
    print(f"\nLog written: {LOG_PATH}")


if __name__ == "__main__":
    main()
