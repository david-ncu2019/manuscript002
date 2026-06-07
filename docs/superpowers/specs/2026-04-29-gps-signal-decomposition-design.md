# GPS Signal Decomposition Script — Design Spec

**Date:** 2026-04-29  
**Author:** davidncu  
**Status:** Approved

---

## Context

The project requires decomposing GPS time series (station TKJS, 2010–2024, ~4,954 daily observations) into physically interpretable components: long-term trend, seasonal oscillations, abrupt jumps, post-seismic relaxation, and residual noise. The decomposition must be statistically rigorous — model acceptance is determined by the Overall Model Test (OMT) chi-squared goodness-of-fit framework (`omt_ncu`), which ensures the residuals are consistent with the assumed noise level. This replaces the ad-hoc STL/MSTL decomposition in `gps_denoise.py` with a fully parametric, least-squares, hypothesis-tested approach.

---

## Goal

A single self-contained script (`gps_decompose.py`) that:
1. Reads a GPS CSV file
2. Auto-detects jump dates and candidate seasonal periods
3. Runs a sigma-scan + OMT DIA loop to find the statistically appropriate model
4. Outputs decomposed component columns, a diagnostic plot (optional), and a model report

---

## Signal Model

```
signal = trend + seasonal_periods + jump + relaxation + noise
```

| Term | Type | Description |
|---|---|---|
| trend | Polynomial degree 1 + optional piecewise-linear breaks | Long-term subsidence velocity, may change over time |
| seasonal | Cosine+sine pairs at accepted periods | Annual, semi-annual, quarterly, biennial oscillations |
| jump | Heaviside step functions | Instrumental offsets or coseismic displacements |
| relaxation | Exponential decay per jump date | Post-seismic or post-instrument relaxation |
| noise | Residual = signal − model | Random measurement noise |

---

## Pipeline (5 Stages)

### Stage 1: Data Loading & Preprocessing
- Read `TKJS_neu.csv` (columns: `datetime`, `gpsdate`, `dN`, `dE`, `dU`, `sN`, `sE`, `sU`)
- Select component(s) via `--component` flag
- Outlier removal: MAD filter, threshold configurable (default: 4.5)
- Fill gaps ≤7 days via time-aware linear interpolation
- Convert `gpsdate` to datetime index

### Stage 2: Auto Jump Detection
- Algorithm: MAD + rolling-window anomaly detection (from `batch_jump_detection.py`)
  - Parameters: `window_days=365`, `sigma_threshold=3.0`, `adaptive_percentile=99`, `min_days_apart=90`
- Trend-validation filter to remove spurious candidates
- Merge with user-supplied `--jumps` dates (union, deduplication)
- Output: sorted list of jump dates for use in Stage 4

### Stage 3: ACF/FFT Period Pre-Screening
- Detrend the series (polynomial degree 2)
- Compute ACF up to 400 lags + FFT power spectrum
- Test candidate periods: `[0.25, 0.5, 1.0, 2.0]` years (default; extendable via `--periods`)
- Accept a candidate if ACF peak exists in ±10% window AND FFT power is in top 30%
- Output: ordered list of proposed periods for Stage 4

### Stage 4: OMT Sigma-Scan Search
For each `sigma_mm` in `[sigma_min, sigma_max]` step `sigma_step`:
  1. Build initial model: `polynomial=1` + accepted periods + jump step dates
  2. Run OMT DIA loop (max `max_iter` iterations):
     - Fit via least-squares using OMT design matrix builders
     - Compute chi-squared OMT statistic: `T = SSR / sigma²`, normalized by DOF
     - If `p_value >= alpha` → **accepted**, exit loop
     - Else DIA diagnoses residuals:
       - FFT → add missing period
       - Derivative analysis → add polyline breakpoint
       - No signal found → stop
  3. If accepted: test exponential relaxation after each jump date
     - Candidate relaxation times: `[30, 90, 180]` days
     - Keep if OMT p-value improves (remains accepted with lower normalized OMT)
  4. Record: `{sigma, accepted, p_value, n_params, model_spec}`

**Model selection:** Among all accepted sigma values, pick the one with the fewest parameters (most parsimonious). Ties broken by highest p-value.

### Stage 5: Output Generation
- Evaluate final model at all dates: extract each component
- Write output files to `{output_dir}/{input_stem}/`

---

## Output Files

### `{stem}_decomposed.csv`
One row per date. Columns present only if the corresponding term was accepted:

| Column | Always present | Description |
|---|---|---|
| `date` | yes | YYYY-MM-DD |
| `dU` (or `dN`/`dE`) | yes | Original observed displacement (m) |
| `dU_model` | yes | Full model fit |
| `dU_trend` | yes | Polynomial + piecewise-linear trend |
| `dU_1yr` | if detected | Annual seasonal component |
| `dU_0.5yr` | if detected | Semi-annual seasonal component |
| `dU_0.25yr` | if detected | Quarterly seasonal component |
| `dU_2yr` | if detected | Biennial seasonal component |
| `dU_jump` | if jumps exist | Sum of all step-function contributions |
| `dU_exp` | if relaxation accepted | Post-seismic exponential relaxation |
| `dU_noise` | yes | Residual (signal − model) |

### `{stem}_decomposed.png` (optional, skipped with `--no-plot`)
Multi-panel figure:
- Panel 1: Raw data + full model fit
- Panel 2: Trend component
- Panel 3: Seasonal components (each period as separate line)
- Panel 4: Jump + relaxation component (omitted if no jumps)
- Panel 5: Residual noise

### `{stem}_report.md`
- Accepted model structure
- Fitted parameter values with formal uncertainties (from least-squares covariance)
- OMT statistics: sigma_mm, normalized OMT, p-value, DOF
- Sigma-scan summary table
- Variance explained per component (%)

---

## CLI Interface

```
python gps_decompose.py <input_csv> [options]

Positional:
  input_csv              Path to GPS CSV file

Component selection:
  --component COMP       dN | dE | dU | all  (default: dU)

Jump detection:
  --jumps DATE[,DATE]    Extra/override jump dates (YYYY-MM-DD), merged with auto-detected

Period candidates:
  --periods FLOAT[,...]  Candidate periods in years (default: 0.25,0.5,1.0,2.0)

OMT settings:
  --sigma-min FLOAT      Min sigma for scan in mm (default: 2.0)
  --sigma-max FLOAT      Max sigma for scan in mm (default: 15.0)
  --sigma-step FLOAT     Sigma scan step size in mm (default: 0.5)
  --alpha FLOAT          OMT significance level (default: 0.05)
  --max-iter INT         Max DIA iterations per sigma (default: 5)

Output:
  --no-plot              Skip PNG generation
  --output-dir DIR       Parent directory for output folder (default: input_csv directory)
```

---

## Key Code Reuse (Do Not Reimpliment)

| Source file | What to reuse |
|---|---|
| `omt_ncu/main.py` | `calculate_omt()`, `estimate_time_func()`, `analyze_residuals()` |
| `omt_ncu/time_func.py` | All `get_design_matrix4*` functions |
| `omt_ncu/utils.py` | `datetime2years()` |
| `batch_jump_detection.py` | `detect_sharp_jumps()`, `validate_with_trend()` |
| `gps_denoise.py` | `remove_outliers()`, `fill_missing_days()`, `detect_annual_cycle()` (ACF+FFT logic) |

---

## Module Structure

Single script `gps_decompose.py` with internal functions (no separate modules unless reusing above):

```
gps_decompose.py
  parse_args()
  load_and_preprocess(csv_path, component, mad_threshold)
  detect_jumps(series, extra_dates)
  prescreen_periods(series, candidates)
  run_omt_sigma_scan(series, dates, jump_dates, candidate_periods, sigma_range, alpha, max_iter)
    └─ run_omt_dia_loop(series, dates, model_spec, sigma, alpha, max_iter)
  test_relaxation(series, dates, accepted_model, jump_dates)
  extract_components(series, dates, final_model)
  save_csv(components, output_dir, stem, component_name)
  save_plot(components, output_dir, stem, component_name)
  save_report(final_model, omt_stats, sigma_scan_table, output_dir, stem, component_name)
  main()
```

---

## Verification

1. Run: `python gps_decompose.py GPS_timeseries/TKJS_neu.csv --component dU`
2. Check that `TKJS_neu/TKJS_neu_decomposed.csv` exists with expected columns
3. Verify `dU_model ≈ dU` (residuals should be small, ~noise level)
4. Verify `dU_trend + dU_1yr + ... + dU_jump + dU_noise ≈ dU` (components sum to original)
5. Check `TKJS_neu_report.md` shows `p_value >= 0.05` for accepted model
6. Run with `--no-plot` and confirm no PNG is generated
7. Run with `--component all` and confirm three subfolders/files appear
