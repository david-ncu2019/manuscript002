# Run Commands — InSAR-MLCW Scripts

> Project: InSAR-MLCW subsidence analysis — GWL-driven methods under exploration.
> Repo root: `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2` (Windows) / `/mnt/hgfs/1000_SCRIPTS/004_Project003/20260427_InSAR_MLCW_v2` (Linux).

## Environments

| Conda env | Python | Used for |
|-----------|--------|---------|
| `fafalab` | 3.10 | IHM-F, ceiling test, seasonal harmonic, data analysis — all active work |
| `isce_ncu3` | 3.x (scipy ≥1.17) | 2S-TOOL batch only |

**PYTHONPATH contamination rule:** `gemini_env` packages leak into `fafalab` and cause numpy `ImportError`. Always reset before `conda run`:

```powershell
# PowerShell (host)
$env:PYTHONPATH = ""; conda run -n fafalab python <script>
```

```bash
# bash / Linux VM
PYTHONPATH="" conda run -n fafalab python <script>
```

---

## IHM-F v3 Fitting (active)

```powershell
# Single station, all layers (TUKU pilot):
$env:PYTHONPATH = ""; conda run -n fafalab python scripts/10_ihmf/fit_ihm_f_v3.py --station TUKU --all

# Single station, single layer:
$env:PYTHONPATH = ""; conda run -n fafalab python scripts/10_ihmf/fit_ihm_f_v3.py --station TUKU --layer F2

# Batch (all 37 stations — only after TUKU pilot passes physical checks):
$env:PYTHONPATH = ""; conda run -n fafalab python scripts/10_ihmf/fit_ihm_f_v3.py --all
```

Output: `results/ihmf/v3/{STATION}_v3_results.json` (joint solve, all layers at once)

---

## Ceiling Test (InSAR-only prediction validation)

```powershell
# Single station walk-forward test:
$env:PYTHONPATH = ""; conda run -n fafalab python scripts/15_prediction/ceiling_test.py --station TUKU
```

Output:
- `results/ceiling_test/{STATION}_ceiling_test.csv`
- `figures/ceiling_test/{STATION}_{LAYER}_*.png` (one A4 landscape PNG per layer)

---

## Seasonal Harmonic Analysis

```powershell
# Step 1 — Fit + holdout (single station):
$env:PYTHONPATH = ""; conda run -n fafalab python scripts/13_seasonal_insar/01_seasonal_harmonic_analysis.py --station TUKU

# Step 2 — Reconstruction visualisation:
$env:PYTHONPATH = ""; conda run -n fafalab python scripts/13_seasonal_insar/02_reconstruction_visualization.py --station TUKU
```

Output: `results/seasonal_insar_harmonic/{STATION}/`

---

## Data Analysis Diagnostics

```powershell
# Aggregate 8-diagnostic summary:
$env:PYTHONPATH = ""; conda run -n fafalab python scripts/11_data_analysis/summarize_for_redesign.py

# Alpha (compressible thickness fraction) per station:
$env:PYTHONPATH = ""; conda run -n fafalab python scripts/11_data_analysis/analyze_alpha.py
```

Output: `results/data_analysis/DATA_ANALYSIS_REPORT.md`

---

## Ring Cross-Correlation

```powershell
# 39-station cross-correlation matrix (uses isce_ncu3):
conda run -n isce_ncu3 python scripts/11_data_analysis/ring_cross_correlation.py
```

Output: `results/ring_cross_correlation/{STATION}/`

---

## 2S-TOOL Batch

```powershell
# Batch run (uses isce_ncu3):
conda run -n isce_ncu3 python scripts/09_trackB/batch_run_2stool.py
```

Output: `data/gwl/2stool_outputs/2stool_results_summary.csv`

---

## Path Verification

```powershell
# Verify cross-platform path detection:
$env:PYTHONPATH = ""; conda run -n fafalab python paths.py
```

Expected output: prints resolved `SCRIPTS_ROOT`, `DATA_ROOT`, `RESULTS_ROOT`, `DOCS_ROOT` for the current platform.

---

## tau_demo_TUKU Pilot (execute in order)

```powershell
$env:PYTHONPATH = ""; conda run -n fafalab python tau_demo_TUKU/01_data_loading.py
$env:PYTHONPATH = ""; conda run -n fafalab python tau_demo_TUKU/02_tau_search.py
$env:PYTHONPATH = ""; conda run -n fafalab python tau_demo_TUKU/03_phase_consistency.py
$env:PYTHONPATH = ""; conda run -n fafalab python tau_demo_TUKU/04_reconstruction.py
$env:PYTHONPATH = ""; conda run -n fafalab python tau_demo_TUKU/05_detrended_reconstruction.py
$env:PYTHONPATH = ""; conda run -n fafalab python tau_demo_TUKU/06_physical_ss.py
$env:PYTHONPATH = ""; conda run -n fafalab python tau_demo_TUKU/07_joint_search.py
```

See `docs/tau_search_methodology.md` for methodology.
