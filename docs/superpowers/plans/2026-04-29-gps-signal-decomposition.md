# GPS Signal Decomposition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `gps_decompose.py` — a single script that reads a GPS CSV, auto-detects jumps and seasonal periods, runs an OMT sigma-scan to find the statistically rigorous best-fit parametric model, and outputs decomposed component CSVs, diagnostic plots, and a model report.

**Architecture:** Five sequential stages — (1) load/preprocess, (2) jump detection via MAD+rolling-window, (3) ACF/FFT period pre-screening, (4) OMT sigma-scan with DIA loop per sigma + post-jump relaxation testing, (5) output generation. All logic lives in a single file with internal functions; OMT design matrix builders and fitting functions are imported directly from `omt_ncu/model_fit.py` and `omt_ncu/dia_logic.py`.

**Tech Stack:** Python 3.x, pandas, numpy, scipy (linalg, stats, fft, signal), matplotlib, statsmodels (acf), argparse. OMT functions imported from `omt_ncu` (path added to sys.path at import time).

---

## Paths & Imports Reference

| What | Path |
|---|---|
| Script to create | `D:/1000_SCRIPTS/004_Project003/20260427_InSAR_MLCW_v2/gps_decompose.py` |
| OMT model_fit | `D:/1000_SCRIPTS/004_Project003/20260421_Overall_Model_Test/omt_ncu/model_fit.py` |
| OMT dia_logic | `D:/1000_SCRIPTS/004_Project003/20260421_Overall_Model_Test/omt_ncu/dia_logic.py` |
| Test data | `D:/1000_SCRIPTS/004_Project003/20260427_InSAR_MLCW_v2/GPS_timeseries/TKJS_neu.csv` |
| Jump detection source | `D:/1000_SCRIPTS/003_Project002/20251111_GTWR003/1_PrepareDatasets/GPS/batch_jump_detection.py` |
| Denoise source | `D:/1000_SCRIPTS/003_Project002/20251111_GTWR003/1_PrepareDatasets/GPS/gps_denoise.py` |

The script adds the OMT directory to `sys.path` at the top:
```python
import sys
sys.path.insert(0, r"D:/1000_SCRIPTS/004_Project003/20260421_Overall_Model_Test")
from omt_ncu.model_fit import (
    estimate_time_func, get_design_matrix4time_func, datetime2years
)
from omt_ncu.dia_logic import calculate_omt, analyze_residuals
```

---

## Task 1: Script skeleton + CLI + data loading

**Files:**
- Create: `D:/1000_SCRIPTS/004_Project003/20260427_InSAR_MLCW_v2/gps_decompose.py`

- [ ] **Step 1: Create the file with imports, CLI parsing, and data loading**

```python
#!/usr/bin/env python3
"""GPS signal decomposition using OMT-based parametric modeling."""

from __future__ import annotations
import sys
import argparse
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
from scipy.stats import median_abs_deviation

sys.path.insert(0, r"D:/1000_SCRIPTS/004_Project003/20260421_Overall_Model_Test")
from omt_ncu.model_fit import estimate_time_func, get_design_matrix4time_func, datetime2years
from omt_ncu.dia_logic import calculate_omt, analyze_residuals


def parse_args():
    p = argparse.ArgumentParser(description="GPS signal decomposition via OMT")
    p.add_argument("input_csv", help="Path to GPS CSV file")
    p.add_argument("--component", default="dU",
                   help="Component(s) to process: dN | dE | dU | all (default: dU)")
    p.add_argument("--jumps", default="",
                   help="Extra jump dates YYYY-MM-DD,YYYY-MM-DD (merged with auto-detected)")
    p.add_argument("--periods", default="0.25,0.5,1.0,2.0",
                   help="Candidate periods in years (default: 0.25,0.5,1.0,2.0)")
    p.add_argument("--sigma-min", type=float, default=2.0, help="Min sigma mm (default 2.0)")
    p.add_argument("--sigma-max", type=float, default=15.0, help="Max sigma mm (default 15.0)")
    p.add_argument("--sigma-step", type=float, default=0.5, help="Sigma step mm (default 0.5)")
    p.add_argument("--alpha", type=float, default=0.05, help="OMT significance level (default 0.05)")
    p.add_argument("--max-iter", type=int, default=5, help="Max DIA iterations per sigma (default 5)")
    p.add_argument("--no-plot", action="store_true", help="Skip PNG generation")
    p.add_argument("--output-dir", default="", help="Parent dir for output folder (default: input dir)")
    return p.parse_args()


def load_and_preprocess(csv_path: str, component: str, mad_threshold: float = 4.5) -> pd.Series:
    """Load GPS CSV, remove outliers via MAD, fill gaps ≤7 days."""
    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["gpsdate"])
    df = df.set_index("date").sort_index()

    series = df[component].copy()
    series = series.groupby(series.index).median()  # deduplicate

    # MAD outlier removal
    median = series.median()
    mad = median_abs_deviation(series.dropna(), scale="normal")
    outliers = np.abs(series - median) > mad_threshold * mad
    series[outliers] = np.nan
    print(f"  [preprocess] {component}: {outliers.sum()} outliers removed")

    # Fill daily grid, interpolate gaps ≤7 days
    full_dates = pd.date_range(start=series.index.min(), end=series.index.max(), freq="D")
    series = series.reindex(full_dates)
    series = series.interpolate(method="time", limit=7).bfill().ffill()
    print(f"  [preprocess] {component}: {len(series)} daily points after gap-fill")

    return series


if __name__ == "__main__":
    args = parse_args()
    csv_path = Path(args.input_csv)
    stem = csv_path.stem  # e.g. "TKJS_neu"

    if args.output_dir:
        out_root = Path(args.output_dir) / stem
    else:
        out_root = csv_path.parent / stem
    out_root.mkdir(parents=True, exist_ok=True)

    components = ["dN", "dE", "dU"] if args.component == "all" else [args.component]
    candidate_periods = [float(p) for p in args.periods.split(",")]
    extra_jumps = [d.strip() for d in args.jumps.split(",") if d.strip()]

    for comp in components:
        print(f"\n{'='*60}\nProcessing: {comp}\n{'='*60}")
        series = load_and_preprocess(str(csv_path), comp)
        print(f"  Series loaded: {len(series)} points")
```

- [ ] **Step 2: Run script with --help to verify CLI parses**

```bash
cd "D:/1000_SCRIPTS/004_Project003/20260427_InSAR_MLCW_v2"
python gps_decompose.py --help
```
Expected: prints usage with all flags, no errors.

- [ ] **Step 3: Run script on TKJS_neu.csv to verify data loading**

```bash
python gps_decompose.py GPS_timeseries/TKJS_neu.csv --component dU
```
Expected output lines like:
```
Processing: dU
  [preprocess] dU: N outliers removed
  [preprocess] dU: 5478 daily points after gap-fill
  Series loaded: 5478 points
```

- [ ] **Step 4: Commit**

```bash
git add gps_decompose.py
git commit -m "feat: add GPS decompose script skeleton with CLI and data loading"
```

---

## Task 2: Jump detection (Stage 2)

**Files:**
- Modify: `gps_decompose.py` — add `detect_jumps()` function

- [ ] **Step 1: Add the `detect_jumps` function after `load_and_preprocess`**

```python
def detect_jumps(
    series: pd.Series,
    extra_dates: list[str],
    window_days: int = 365,
    sigma_threshold: float = 3.0,
    smooth_window: int = 30,
    adaptive_percentile: float = 99,
    min_days_apart: int = 90,
) -> list[datetime]:
    """Auto-detect jump dates via MAD rolling-window + trend validation, merged with extra_dates."""
    from scipy.ndimage import median_filter

    valid = series.interpolate(method="time")
    diffs = np.diff(valid.values)
    abs_diffs = np.abs(diffs)

    rolling_median = pd.Series(abs_diffs).rolling(window=window_days, center=True, min_periods=1).median().values
    rolling_mad = pd.Series(abs_diffs).rolling(window=window_days, center=True, min_periods=1).apply(
        lambda x: np.median(np.abs(x - np.median(x))), raw=True
    ).values
    threshold = rolling_median + sigma_threshold * 1.4826 * rolling_mad
    candidates = [(valid.index[i + 1], diffs[i]) for i in np.where(abs_diffs > threshold)[0]]

    # Adaptive threshold for validation
    raw_diffs = np.abs(np.diff(series.dropna().values))
    adaptive_thr = max(np.percentile(raw_diffs, adaptive_percentile) * 1000, 3.0)  # mm

    trend = median_filter(valid.values, size=smooth_window)
    trend_s = pd.Series(trend, index=valid.index)

    validated = []
    for date, _ in candidates:
        try:
            idx = trend_s.index.get_loc(date)
            before = np.median(trend_s.values[max(0, idx - 30):idx])
            after = np.median(trend_s.values[idx + 1:min(len(trend_s), idx + 31)])
            if abs((after - before) * 1000) >= adaptive_thr:
                validated.append(date)
        except Exception:
            continue

    # Deduplicate by min_days_apart
    validated.sort()
    filtered = []
    for d in validated:
        if not any(abs((d - f).days) < min_days_apart for f in filtered):
            filtered.append(d)

    # Merge extra user-supplied dates
    for ds in extra_dates:
        try:
            dt = pd.Timestamp(ds)
            if not any(abs((dt - f).days) < min_days_apart for f in filtered):
                filtered.append(dt)
        except Exception:
            print(f"  [jumps] Warning: could not parse date '{ds}', skipping")

    filtered.sort()
    jump_datetimes = [d.to_pydatetime() for d in filtered]
    print(f"  [jumps] Detected {len(jump_datetimes)} jump(s): {[d.strftime('%Y-%m-%d') for d in jump_datetimes]}")
    return jump_datetimes
```

- [ ] **Step 2: Wire `detect_jumps` into the main loop (inside the `for comp in components` block)**

Replace the `print(f"  Series loaded...")` line with:
```python
        print(f"  Series loaded: {len(series)} points")
        jump_dates = detect_jumps(series, extra_jumps)
```

- [ ] **Step 3: Run on TKJS_neu.csv and verify jump detection output**

```bash
python gps_decompose.py GPS_timeseries/TKJS_neu.csv --component dU
```
Expected: prints detected jump dates (if any), no errors.

- [ ] **Step 4: Commit**

```bash
git add gps_decompose.py
git commit -m "feat: add jump detection stage to GPS decompose script"
```

---

## Task 3: Period pre-screening (Stage 3)

**Files:**
- Modify: `gps_decompose.py` — add `prescreen_periods()` function

- [ ] **Step 1: Add the `prescreen_periods` function (after `detect_jumps`)**

```python
def prescreen_periods(series: pd.Series, candidates_yr: list[float]) -> list[float]:
    """ACF + FFT validation of candidate seasonal periods.
    Returns subset of candidates_yr that show a peak in both ACF and FFT."""
    from statsmodels.tsa.stattools import acf
    from scipy.fft import rfft, rfftfreq

    values = series.values.copy()

    # Detrend with degree-2 polynomial
    x = np.arange(len(values))
    coeffs = np.polyfit(x, values, 2)
    detrended = values - np.polyval(coeffs, x)

    # ACF up to 400 lags (or half series length)
    max_lag = min(len(series) // 2, 400)
    acf_vals = acf(detrended, nlags=max_lag, fft=True)

    # FFT power
    fft_power = np.abs(rfft(detrended))
    freqs = rfftfreq(len(detrended), d=1.0)  # 1/days

    accepted = []
    for period_yr in candidates_yr:
        period_days = period_yr * 365.25

        # ACF: look for peak within ±10% of target period
        low_lag = int(period_days * 0.90)
        high_lag = int(period_days * 1.10)
        low_lag = max(low_lag, 1)
        high_lag = min(high_lag, max_lag)
        if low_lag >= high_lag:
            continue
        acf_window = acf_vals[low_lag:high_lag]
        has_acf_peak = acf_window.max() > 0.05  # weak positive correlation

        # FFT: power at target frequency in top 30%?
        target_freq = 1.0 / period_days
        freq_idx = np.argmin(np.abs(freqs - target_freq))
        power_threshold = np.percentile(fft_power[1:], 70)
        has_fft_peak = fft_power[freq_idx] > power_threshold

        if has_acf_peak and has_fft_peak:
            accepted.append(period_yr)
            print(f"  [periods] Accepted period: {period_yr} yr ({period_days:.0f} days)")
        else:
            print(f"  [periods] Rejected period: {period_yr} yr (acf={has_acf_peak}, fft={has_fft_peak})")

    return accepted
```

- [ ] **Step 2: Wire `prescreen_periods` into the main loop (after jump detection)**

```python
        detected_periods = prescreen_periods(series, candidate_periods)
```

- [ ] **Step 3: Run on TKJS_neu.csv and verify period screening output**

```bash
python gps_decompose.py GPS_timeseries/TKJS_neu.csv --component dU
```
Expected: prints accepted/rejected for 0.25, 0.5, 1.0, 2.0 yr, no errors.

- [ ] **Step 4: Commit**

```bash
git add gps_decompose.py
git commit -m "feat: add ACF+FFT period pre-screening stage"
```

---

## Task 4: OMT DIA loop (Stage 4, part A)

**Files:**
- Modify: `gps_decompose.py` — add `run_omt_dia_loop()` function

The OMT functions use:
- `estimate_time_func(model, date_list, dis_ts)` → `(G, m, e2, d_hat)` where `dis_ts` is in meters
- `calculate_omt(residuals, m_obs, n_param, sigma_m, alpha)` → `(T_stat, omt, p_value, K_norm)` where `sigma_m` is in meters
- `analyze_residuals(residuals, dates)` → `(adapt_type, adapt_val)`

The `model` dict has keys: `polynomial`, `periodic`, `stepDate`, `polyline`, `exp`, `log`.  
`stepDate` and `polyline` are lists of strings in `"YYYYMMDD"` format.  
`date_list` must be a list of `datetime` objects.

- [ ] **Step 1: Add the `run_omt_dia_loop` function (after `prescreen_periods`)**

```python
def run_omt_dia_loop(
    series: pd.Series,
    jump_dates: list[datetime],
    initial_periods: list[float],
    sigma_mm: float,
    alpha: float,
    max_iter: int,
) -> dict | None:
    """
    Run one OMT DIA loop for a given sigma_mm.
    Returns the accepted model dict or None if not accepted within max_iter.
    """
    date_list = [d.to_pydatetime() if hasattr(d, "to_pydatetime") else d for d in series.index]
    dis_ts = series.values.copy()  # meters
    sigma_m = sigma_mm / 1000.0   # convert mm → meters

    step_dates = [d.strftime("%Y%m%d") for d in jump_dates]

    model = {
        "polynomial": 1,
        "periodic": list(initial_periods),
        "stepDate": step_dates,
        "polyline": [],
        "exp": {},
        "log": {},
    }

    for iteration in range(max_iter):
        G, m, e2, d_hat = estimate_time_func(model, date_list, dis_ts)
        residuals = dis_ts - d_hat
        n_param = G.shape[1]
        m_obs = len(dis_ts)

        T_stat, omt, p_value, K_norm = calculate_omt(residuals, m_obs, n_param, sigma_m, alpha)

        print(f"    [sigma={sigma_mm:.1f}mm iter={iteration}] omt={omt:.3f} p={p_value:.4f} "
              f"K/r={K_norm:.3f} n_param={n_param}")

        if p_value >= alpha:
            model["_omt_stats"] = {
                "sigma_mm": sigma_mm, "omt": omt, "p_value": p_value,
                "K_norm": K_norm, "n_param": n_param, "iterations": iteration,
            }
            return model

        # DIA: diagnose residuals
        adapt_type, adapt_val = analyze_residuals(residuals, date_list)

        if adapt_type == "period":
            if adapt_val not in model["periodic"]:
                model["periodic"].append(adapt_val)
                print(f"    [DIA] Add period: {adapt_val} yr")
            else:
                print(f"    [DIA] Period {adapt_val} already in model, stopping")
                break
        elif adapt_type == "polyline":
            if adapt_val not in model["polyline"]:
                model["polyline"].append(adapt_val)
                print(f"    [DIA] Add polyline break: {adapt_val}")
            else:
                print(f"    [DIA] Polyline {adapt_val} already in model, stopping")
                break
        else:
            print(f"    [DIA] No clear signal, stopping")
            break

    return None  # not accepted
```

- [ ] **Step 2: Run a quick smoke test by calling the function once in main (temporarily, after period screening)**

Add temporarily to the main loop body (after `detected_periods = prescreen_periods(...)`):
```python
        sigma_mm = 5.0
        result = run_omt_dia_loop(series, jump_dates, detected_periods, sigma_mm, args.alpha, args.max_iter)
        print(f"  Smoke test sigma={sigma_mm}: accepted={result is not None}")
```

- [ ] **Step 3: Run on TKJS_neu.csv and verify DIA loop output**

```bash
python gps_decompose.py GPS_timeseries/TKJS_neu.csv --component dU
```
Expected: prints per-iteration omt/p-value lines, DIA actions, final "accepted=True/False".

- [ ] **Step 4: Remove the temporary smoke test code** (the 3 lines added in Step 2)

- [ ] **Step 5: Commit**

```bash
git add gps_decompose.py
git commit -m "feat: add OMT DIA loop function"
```

---

## Task 5: Sigma scan + relaxation testing (Stage 4, part B)

**Files:**
- Modify: `gps_decompose.py` — add `test_relaxation()` and `run_omt_sigma_scan()` functions

- [ ] **Step 1: Add `test_relaxation` function (after `run_omt_dia_loop`)**

```python
def test_relaxation(
    series: pd.Series,
    jump_dates: list[datetime],
    accepted_model: dict,
    alpha: float,
) -> dict:
    """
    For each jump date, test exponential relaxation with tau=[30,90,180] days.
    Keeps the tau that lowers the normalized OMT while keeping p_value >= alpha.
    Returns updated model dict.
    """
    if not jump_dates:
        return accepted_model

    date_list = [d.to_pydatetime() if hasattr(d, "to_pydatetime") else d for d in series.index]
    dis_ts = series.values.copy()
    sigma_mm = accepted_model["_omt_stats"]["sigma_mm"]
    sigma_m = sigma_mm / 1000.0

    model = {k: v for k, v in accepted_model.items() if not k.startswith("_")}
    model["exp"] = {}

    current_stats = accepted_model["_omt_stats"]
    best_omt = current_stats["omt"]

    for jump_dt in jump_dates:
        jump_str = jump_dt.strftime("%Y%m%d")
        best_tau = None

        for tau_days in [30, 90, 180]:
            trial_model = {k: (list(v) if isinstance(v, list) else v) for k, v in model.items()}
            trial_exp = {k: list(v) for k, v in model["exp"].items()}
            trial_exp[jump_str] = [tau_days]
            trial_model["exp"] = trial_exp

            G, m, e2, d_hat = estimate_time_func(trial_model, date_list, dis_ts)
            residuals = dis_ts - d_hat
            n_param = G.shape[1]
            _, omt, p_value, _ = calculate_omt(residuals, len(dis_ts), n_param, sigma_m, alpha)

            if p_value >= alpha and omt < best_omt:
                best_omt = omt
                best_tau = tau_days
                print(f"    [relax] Jump {jump_str}: tau={tau_days}d improves omt to {omt:.4f}")

        if best_tau is not None:
            if jump_str not in model["exp"]:
                model["exp"][jump_str] = []
            model["exp"][jump_str] = [best_tau]

    # Recompute final stats
    G, m, e2, d_hat = estimate_time_func(model, date_list, dis_ts)
    residuals = dis_ts - d_hat
    n_param = G.shape[1]
    T_stat, omt, p_value, K_norm = calculate_omt(residuals, len(dis_ts), n_param, sigma_m, alpha)
    model["_omt_stats"] = {
        "sigma_mm": sigma_mm, "omt": omt, "p_value": p_value,
        "K_norm": K_norm, "n_param": n_param, "iterations": current_stats["iterations"],
    }
    return model
```

- [ ] **Step 2: Add `run_omt_sigma_scan` function (after `test_relaxation`)**

```python
def run_omt_sigma_scan(
    series: pd.Series,
    jump_dates: list[datetime],
    candidate_periods: list[float],
    sigma_min: float,
    sigma_max: float,
    sigma_step: float,
    alpha: float,
    max_iter: int,
) -> tuple[dict | None, list[dict]]:
    """
    Scan sigma values and run the OMT DIA loop for each.
    Returns (best_model_or_None, scan_table).
    Best model is the most parsimonious accepted model (fewest params, then highest p-value).
    """
    sigmas = np.arange(sigma_min, sigma_max + sigma_step * 0.5, sigma_step)
    scan_results = []
    scan_table = []  # list of dicts: {sigma_mm, accepted, p_value, n_param, n_periods, n_polylines}

    for sigma_mm in sigmas:
        print(f"\n  [scan] sigma={sigma_mm:.1f} mm")
        result = run_omt_dia_loop(series, jump_dates, candidate_periods, sigma_mm, alpha, max_iter)
        if result is not None:
            scan_results.append(result)
            s = result["_omt_stats"]
            scan_table.append({"sigma_mm": sigma_mm, "accepted": True, "p_value": s["p_value"],
                                "n_param": s["n_param"],
                                "n_periods": len(result.get("periodic", [])),
                                "n_polylines": len(result.get("polyline", []))})
        else:
            scan_table.append({"sigma_mm": sigma_mm, "accepted": False,
                                "p_value": None, "n_param": None,
                                "n_periods": None, "n_polylines": None})

    if not scan_results:
        print("  [scan] No accepted model found across sigma range.")
        return None, scan_table

    # Select most parsimonious: fewest params, ties by highest p-value
    best = min(scan_results, key=lambda m: (m["_omt_stats"]["n_param"], -m["_omt_stats"]["p_value"]))
    stats = best["_omt_stats"]
    print(f"\n  [scan] Best model: sigma={stats['sigma_mm']:.1f}mm "
          f"n_param={stats['n_param']} p={stats['p_value']:.4f}")

    # Test relaxation on best model
    best = test_relaxation(series, jump_dates, best, alpha)
    return best, scan_table
```

- [ ] **Step 3: Wire `run_omt_sigma_scan` into main loop (replacing the temporary sigma test)**

In the main `for comp in components:` loop, after `detected_periods = prescreen_periods(...)`, add:
```python
        best_model = run_omt_sigma_scan(
            series, jump_dates, detected_periods,
            args.sigma_min, args.sigma_max, args.sigma_step,
            args.alpha, args.max_iter,
        )
        if best_model is None:
            print(f"  WARNING: No accepted model found for {comp}. Skipping output.")
            continue
```

- [ ] **Step 4: Run on TKJS_neu.csv and verify sigma scan completes**

```bash
python gps_decompose.py GPS_timeseries/TKJS_neu.csv --component dU --sigma-min 3.0 --sigma-max 8.0 --sigma-step 1.0
```
Expected: prints per-sigma DIA iterations, identifies a best model, prints its params.

- [ ] **Step 5: Commit**

```bash
git add gps_decompose.py
git commit -m "feat: add sigma scan and relaxation testing"
```

---

## Task 6: Component extraction (Stage 5, part A)

**Files:**
- Modify: `gps_decompose.py` — add `extract_components()` function

The model dict keys: `polynomial` (int), `periodic` (list of floats in yr), `stepDate` (list of YYYYMMDD strings), `polyline` (list of YYYYMMDD strings), `exp` (dict YYYYMMDD → [tau_days]).

After `estimate_time_func`, parameters `m` are ordered as:
1. `poly_deg+1` polynomial coefficients (deg 0, 1, ... poly_deg)
2. 2 × len(periodic) cosine/sine pairs
3. len(stepDate) step amplitudes
4. len(polyline) polyline slopes
5. exp terms (one per tau per onset date)

Each design-matrix block contribution = `A_block @ m_block`.

- [ ] **Step 1: Add `extract_components` function (after `run_omt_sigma_scan`)**

```python
def _period_label(period_yr: float) -> str:
    """Convert period in years to a short label string, e.g. 1.0 → '1yr', 0.5 → '0.5yr'."""
    val = period_yr
    if val == int(val):
        return f"{int(val)}yr"
    return f"{val}yr"


def extract_components(
    series: pd.Series,
    best_model: dict,
    comp: str,
) -> dict[str, pd.Series]:
    """
    Extract individual signal components from the fitted model.
    Returns dict of {column_name: pd.Series}.
    """
    date_list = [d.to_pydatetime() if hasattr(d, "to_pydatetime") else d for d in series.index]
    dis_ts = series.values.copy()

    model = {k: v for k, v in best_model.items() if not k.startswith("_")}
    G, m, e2, d_hat = estimate_time_func(model, date_list, dis_ts)

    poly_deg   = model.get("polynomial", 0)
    periods    = model.get("periodic", [])
    steps      = model.get("stepDate", [])
    polylines  = model.get("polyline", [])
    exps       = model.get("exp", {})

    components = {}
    idx = series.index

    # --- Trend: polynomial + polyline contributions ---
    c0 = 0
    c1 = c0 + poly_deg + 1
    trend_val = G[:, c0:c1] @ m[c0:c1]
    c0 = c1
    # Skip periodic block to reach polyline
    c0 += 2 * len(periods)  # periodic block
    c0 += len(steps)         # step block
    # polyline block
    c1 = c0 + len(polylines)
    if len(polylines) > 0:
        trend_val = trend_val + G[:, c0:c1] @ m[c0:c1]
    c0 = c1

    components[f"{comp}_trend"] = pd.Series(trend_val, index=idx)

    # --- Periodic blocks ---
    c0 = poly_deg + 1
    for period_yr in periods:
        label = _period_label(period_yr)
        c1 = c0 + 2
        seasonal_val = G[:, c0:c1] @ m[c0:c1]
        components[f"{comp}_{label}"] = pd.Series(seasonal_val, index=idx)
        c0 = c1

    # --- Jump (step) block ---
    if steps:
        c1 = c0 + len(steps)
        jump_val = G[:, c0:c1] @ m[c0:c1]
        components[f"{comp}_jump"] = pd.Series(jump_val, index=idx)
        c0 = c1
    else:
        c0 += 0

    # Skip polyline (already in trend)
    c0 += len(polylines)

    # --- Exponential relaxation block ---
    n_exp = sum(len(v) for v in exps.values())
    if n_exp > 0:
        c1 = c0 + n_exp
        exp_val = G[:, c0:c1] @ m[c0:c1]
        components[f"{comp}_exp"] = pd.Series(exp_val, index=idx)
        c0 = c1

    # --- Full model and noise ---
    components[f"{comp}_model"] = pd.Series(d_hat, index=idx)
    components[f"{comp}_noise"] = pd.Series(dis_ts - d_hat, index=idx)

    return components
```

- [ ] **Step 2: Wire `extract_components` into main loop (after `best_model` is obtained)**

```python
        components = extract_components(series, best_model, comp)
        print(f"  [extract] Components: {list(components.keys())}")
```

- [ ] **Step 3: Run and verify component keys are printed correctly**

```bash
python gps_decompose.py GPS_timeseries/TKJS_neu.csv --component dU --sigma-min 3.0 --sigma-max 8.0 --sigma-step 1.0
```
Expected: prints list like `['dU_trend', 'dU_1yr', 'dU_jump', 'dU_model', 'dU_noise']`

- [ ] **Step 4: Commit**

```bash
git add gps_decompose.py
git commit -m "feat: add component extraction from fitted model parameters"
```

---

## Task 7: CSV output (Stage 5, part B)

**Files:**
- Modify: `gps_decompose.py` — add `save_csv()` and wire into main

- [ ] **Step 1: Add `save_csv` function (after `extract_components`)**

```python
def save_csv(
    series: pd.Series,
    components: dict[str, pd.Series],
    comp: str,
    out_root: Path,
    stem: str,
) -> Path:
    """Save decomposed components to CSV."""
    df = pd.DataFrame({"date": series.index, comp: series.values})
    df = df.set_index("date")
    for col, s in components.items():
        df[col] = s.values
    csv_path = out_root / f"{stem}_decomposed_{comp}.csv"
    df.to_csv(csv_path, float_format="%.6f")
    print(f"  [output] CSV saved: {csv_path}")
    return csv_path
```

- [ ] **Step 2: Wire `save_csv` into main loop (after `extract_components`)**

```python
        save_csv(series, components, comp, out_root, stem)
```

- [ ] **Step 3: Run and verify CSV is created**

```bash
python gps_decompose.py GPS_timeseries/TKJS_neu.csv --component dU --sigma-min 3.0 --sigma-max 8.0 --sigma-step 1.0
```
Expected: `TKJS_neu/TKJS_neu_decomposed_dU.csv` exists with columns `dU`, `dU_trend`, `dU_model`, `dU_noise`, etc.

- [ ] **Step 4: Quick sanity check — components sum to original**

```bash
python -c "
import pandas as pd, numpy as np
df = pd.read_csv('TKJS_neu/TKJS_neu_decomposed_dU.csv', index_col=0)
# sum all component columns (exclude model and noise)
comp_cols = [c for c in df.columns if c not in ('dU_model', 'dU_noise', 'dU')]
recon = df[comp_cols].sum(axis=1)
diff = np.abs(df['dU'] - df['dU_noise'] - recon)
print('Max reconstruction error (m):', diff.max())
"
```
Expected: max error < 1e-6 m (floating point only).

- [ ] **Step 5: Commit**

```bash
git add gps_decompose.py
git commit -m "feat: add CSV output with decomposed components"
```

---

## Task 8: Diagnostic plot (Stage 5, part C)

**Files:**
- Modify: `gps_decompose.py` — add `save_plot()` and wire into main

- [ ] **Step 1: Add `save_plot` function (after `save_csv`)**

```python
def save_plot(
    series: pd.Series,
    components: dict[str, pd.Series],
    best_model: dict,
    comp: str,
    out_root: Path,
    stem: str,
) -> Path:
    """Save multi-panel diagnostic PNG."""
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    periodic_cols = [c for c in components if c.endswith("yr")]
    has_jump = f"{comp}_jump" in components
    has_exp = f"{comp}_exp" in components

    n_panels = 2 + (1 if periodic_cols else 0) + (1 if has_jump or has_exp else 0) + 1
    fig, axes = plt.subplots(n_panels, 1, figsize=(14, 3 * n_panels), sharex=True)
    axes = np.atleast_1d(axes)

    idx = series.index
    ax_i = 0

    # Panel 1: raw + model
    axes[ax_i].plot(idx, series.values * 1000, "o", ms=1, alpha=0.3, color="#95a5a6", label="Observed")
    axes[ax_i].plot(idx, components[f"{comp}_model"].values * 1000, "-", lw=1.5, color="#e74c3c", label="Model")
    stats = best_model["_omt_stats"]
    axes[ax_i].set_title(
        f"{stem} {comp} — σ={stats['sigma_mm']:.1f}mm p={stats['p_value']:.4f} n_param={stats['n_param']}",
        fontsize=10,
    )
    axes[ax_i].set_ylabel("mm")
    axes[ax_i].legend(loc="best", fontsize=7)
    axes[ax_i].grid(True, ls=":", alpha=0.4)
    ax_i += 1

    # Panel 2: trend
    axes[ax_i].plot(idx, components[f"{comp}_trend"].values * 1000, "-", lw=1.5, color="#2c3e50")
    axes[ax_i].set_ylabel("Trend (mm)")
    axes[ax_i].grid(True, ls=":", alpha=0.4)
    ax_i += 1

    # Panel 3: seasonal components (if any)
    if periodic_cols:
        for col in periodic_cols:
            label = col.replace(f"{comp}_", "")
            axes[ax_i].plot(idx, components[col].values * 1000, lw=1, label=label)
        axes[ax_i].axhline(0, color="black", lw=0.5, ls="--")
        axes[ax_i].set_ylabel("Seasonal (mm)")
        axes[ax_i].legend(loc="best", fontsize=7)
        axes[ax_i].grid(True, ls=":", alpha=0.4)
        ax_i += 1

    # Panel 4: jump + exp (if any)
    if has_jump or has_exp:
        if has_jump:
            axes[ax_i].plot(idx, components[f"{comp}_jump"].values * 1000, "-", lw=1.5,
                            color="#9b59b6", label="Jump")
        if has_exp:
            axes[ax_i].plot(idx, components[f"{comp}_exp"].values * 1000, "--", lw=1.5,
                            color="#e67e22", label="Exp relax")
        axes[ax_i].axhline(0, color="black", lw=0.5, ls="--")
        axes[ax_i].set_ylabel("Jump/Relax (mm)")
        axes[ax_i].legend(loc="best", fontsize=7)
        axes[ax_i].grid(True, ls=":", alpha=0.4)
        ax_i += 1

    # Last panel: noise
    axes[ax_i].plot(idx, components[f"{comp}_noise"].values * 1000, "o", ms=1, alpha=0.4, color="#3498db")
    axes[ax_i].axhline(0, color="black", lw=0.5, ls="--")
    axes[ax_i].set_ylabel("Residual (mm)")
    axes[ax_i].grid(True, ls=":", alpha=0.4)
    axes[ax_i].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    fig.autofmt_xdate()
    plt.tight_layout()
    png_path = out_root / f"{stem}_decomposed_{comp}.png"
    plt.savefig(png_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [output] Plot saved: {png_path}")
    return png_path
```

- [ ] **Step 2: Wire `save_plot` into main loop (after `save_csv`, conditional on `--no-plot`)**

```python
        if not args.no_plot:
            save_plot(series, components, best_model, comp, out_root, stem)
```

- [ ] **Step 3: Run and verify PNG is created**

```bash
python gps_decompose.py GPS_timeseries/TKJS_neu.csv --component dU --sigma-min 3.0 --sigma-max 8.0 --sigma-step 1.0
```
Expected: `TKJS_neu/TKJS_neu_decomposed_dU.png` exists.

- [ ] **Step 4: Run with --no-plot and verify no PNG created**

```bash
python gps_decompose.py GPS_timeseries/TKJS_neu.csv --component dU --no-plot --sigma-min 3.0 --sigma-max 8.0 --sigma-step 1.0
```
Expected: no PNG file in output folder.

- [ ] **Step 5: Commit**

```bash
git add gps_decompose.py
git commit -m "feat: add optional diagnostic plot output"
```

---

## Task 9: Model report (Stage 5, part D)

**Files:**
- Modify: `gps_decompose.py` — add `save_report()` and sigma scan table tracking

- [ ] **Step 1: Note — `run_omt_sigma_scan` already returns `(best_model, scan_table)` as defined in Task 5.**

No changes needed to `run_omt_sigma_scan` in this task. Proceed directly to adding `save_report`.

- [ ] **Step 2: Update the main loop to unpack the new return value**

```python
        best_model, scan_table = run_omt_sigma_scan(
            series, jump_dates, detected_periods,
            args.sigma_min, args.sigma_max, args.sigma_step,
            args.alpha, args.max_iter,
        )
        if best_model is None:
            print(f"  WARNING: No accepted model found for {comp}. Skipping output.")
            continue
```

- [ ] **Step 3: Add `save_report` function (after `save_plot`)**

```python
def save_report(
    series: pd.Series,
    components: dict[str, pd.Series],
    best_model: dict,
    scan_table: list[dict],
    comp: str,
    out_root: Path,
    stem: str,
) -> Path:
    """Save model report as Markdown."""
    stats = best_model["_omt_stats"]
    model = {k: v for k, v in best_model.items() if not k.startswith("_")}

    lines = [
        f"# GPS Decomposition Report: {stem} — {comp}",
        "",
        "## Accepted Model",
        "",
        f"| Parameter | Value |",
        f"|---|---|",
        f"| Component | {comp} |",
        f"| Sigma (mm) | {stats['sigma_mm']:.1f} |",
        f"| Polynomial degree | {model.get('polynomial', 0)} |",
        f"| Seasonal periods (yr) | {model.get('periodic', [])} |",
        f"| Jump dates | {model.get('stepDate', [])} |",
        f"| Polyline breaks | {model.get('polyline', [])} |",
        f"| Exp relaxation | {model.get('exp', {})} |",
        f"| n_params | {stats['n_param']} |",
        f"| Normalized OMT | {stats['omt']:.4f} |",
        f"| K/r threshold | {stats['K_norm']:.4f} |",
        f"| p-value | {stats['p_value']:.6f} |",
        f"| DIA iterations | {stats['iterations']} |",
        "",
        "## Variance Explained per Component (%)",
        "",
        "| Component | Std (mm) | Variance Explained (%) |",
        "|---|---|---|",
    ]

    orig_var = np.var(series.values)
    for col, s in components.items():
        if col in (f"{comp}_model", f"{comp}_noise"):
            continue
        pct = (np.var(s.values) / orig_var * 100) if orig_var > 0 else 0.0
        lines.append(f"| {col} | {np.std(s.values)*1000:.2f} | {pct:.2f} |")

    noise_std = np.std(components[f"{comp}_noise"].values) * 1000
    noise_pct = np.var(components[f"{comp}_noise"].values) / orig_var * 100 if orig_var > 0 else 0.0
    lines.append(f"| {comp}_noise | {noise_std:.2f} | {noise_pct:.2f} |")

    lines += [
        "",
        "## Sigma Scan Summary",
        "",
        "| Sigma (mm) | Accepted | p-value | n_params | n_periods | n_polylines |",
        "|---|---|---|---|---|---|",
    ]
    for row in scan_table:
        p = f"{row['p_value']:.4f}" if row["p_value"] is not None else "—"
        n = str(row["n_param"]) if row["n_param"] is not None else "—"
        np_ = str(row["n_periods"]) if row["n_periods"] is not None else "—"
        nl = str(row["n_polylines"]) if row["n_polylines"] is not None else "—"
        acc = "✓" if row["accepted"] else "✗"
        lines.append(f"| {row['sigma_mm']:.1f} | {acc} | {p} | {n} | {np_} | {nl} |")

    lines.append("")
    report_path = out_root / f"{stem}_report_{comp}.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  [output] Report saved: {report_path}")
    return report_path
```

- [ ] **Step 4: Wire `save_report` into main loop (after plot)**

```python
        save_report(series, components, best_model, scan_table, comp, out_root, stem)
```

- [ ] **Step 5: Run full pipeline and verify all three output files exist**

```bash
python gps_decompose.py GPS_timeseries/TKJS_neu.csv --component dU --sigma-min 3.0 --sigma-max 8.0 --sigma-step 1.0
```
Expected:
```
TKJS_neu/TKJS_neu_decomposed_dU.csv
TKJS_neu/TKJS_neu_decomposed_dU.png
TKJS_neu/TKJS_neu_report_dU.md
```

- [ ] **Step 6: Verify report shows p_value >= 0.05**

```bash
python -c "
content = open('TKJS_neu/TKJS_neu_report_dU.md').read()
import re
m = re.search(r'p-value.*?\| (\S+)', content)
print('p-value:', m.group(1) if m else 'not found')
"
```
Expected: p-value >= 0.05.

- [ ] **Step 7: Commit**

```bash
git add gps_decompose.py
git commit -m "feat: add model report output with sigma scan summary"
```

---

## Task 10: End-to-end verification

- [ ] **Step 1: Run with --component all**

```bash
python gps_decompose.py GPS_timeseries/TKJS_neu.csv --component all --sigma-min 3.0 --sigma-max 10.0 --sigma-step 1.0
```
Expected: three CSV + report files (one per component), plus PNGs.

- [ ] **Step 2: Run with --no-plot and verify no PNG**

```bash
python gps_decompose.py GPS_timeseries/TKJS_neu.csv --component dU --no-plot --sigma-min 3.0 --sigma-max 6.0 --sigma-step 1.0
ls TKJS_neu/
```
Expected: only CSV and report, no PNG.

- [ ] **Step 3: Test user-supplied jump override**

```bash
python gps_decompose.py GPS_timeseries/TKJS_neu.csv --component dU --jumps 2022-09-18 --sigma-min 3.0 --sigma-max 8.0 --sigma-step 1.0
```
Expected: 2022-09-18 appears in jump list in report.

- [ ] **Step 4: Verify component reconstruction identity**

```bash
python -c "
import pandas as pd, numpy as np
df = pd.read_csv('TKJS_neu/TKJS_neu_decomposed_dU.csv', index_col=0)
comp_cols = [c for c in df.columns if c not in ('dU_model', 'dU_noise', 'dU')]
recon = df[comp_cols].sum(axis=1)
diff = np.abs(df['dU'] - df['dU_noise'] - recon)
print('Max reconstruction error (m):', diff.max())
assert diff.max() < 1e-4, 'Reconstruction error too large!'
print('PASS: components sum to original - noise')
"
```

- [ ] **Step 5: Final commit**

```bash
git add gps_decompose.py
git commit -m "feat: complete GPS signal decomposition script with OMT-based parametric modeling"
```
