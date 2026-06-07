# IHM-F v3: InSAR-MLCW Groundwater-Driven Per-Layer Compaction Model

Yunlin (Choushui River Alluvial Fan), Taiwan — active research codebase.

## Overview

This repository contains scripts for reconstructing aquifer-system compaction timeseries at 37 MLCW (Multi-Level Compaction and Water-level) stations in the Yunlin subsidence bowl, central Taiwan. The model, IHM-F (Inelastic Head Model, candidate F), is a two-regime groundwater-driven per-layer compaction model. It uses InSAR (Interferometric Synthetic Aperture Radar) and GNSS surface deformation observations together with per-layer groundwater level (GWL) feather files to estimate skeletal storage coefficients ($S_{ske}$, $S_{skv}$) and consolidation time constants ($\tau_k$) for each hydrostratigraphic layer.

## Study Area

Choushui River Alluvial Fan, Yunlin County, Taiwan. The sediment column is divided into alternating aquifer (F) and aquitard (T) layers using the Taiwan CGS (Central Geological Survey) convention. The borehole reference for the TUKU pilot station is `YL_WSYL23G1_TUKU`.

## Key Scripts

| Script | Purpose |
|--------|---------|
| `scripts/10_ihmf/fit_ihm_f_v3.py` | Main entry point — per-station and batch fitting |
| `scripts/10_ihmf/ihmf_model_v3.py` | Core model: $\tau$ grid search, walk-forward inversion, regime classification |
| `scripts/10_ihmf/ihmf_io_multilayer.py` | Active data loader for v3 (GWL + MLCW + InSAR/GPS) |
| `scripts/10_ihmf/ihmf_detrend.py` | Shared trend+harmonic removal (v1/v2/v3) |
| `tau_demo_TUKU/` | Step-by-step pilot analysis for TUKU station |
| `scripts/12_stress_strain/` | Stress-strain per-layer analysis (Script 12) |

## Run Modes

```powershell
# Reset PYTHONPATH first (avoids conda environment contamination)
$env:PYTHONPATH=""

# Single station pilot (TUKU)
conda run -n fafalab python scripts/10_ihmf/fit_ihm_f_v3.py --station TUKU --all

# GPS mode (5-day cadence feather input, --gps flag)
conda run -n fafalab python scripts/10_ihmf/fit_ihm_f_v3.py --station TUKU --all --gps

# Batch — all 37 stations (run only after TUKU pilot passes physical checks)
conda run -n fafalab python scripts/10_ihmf/fit_ihm_f_v3.py --all
```

Full command catalog: `docs/run_commands.md`

## Two Input Modes

| Mode | Cadence | Input format | Flag |
|------|---------|-------------|------|
| InSAR | Monthly (~30-day) | CSV | (default) |
| GPS/GNSS | 5-day | Feather | `--gps` |

## Environment

- Python 3.10, `fafalab` conda environment
- Key packages: `numpy`, `scipy`, `pandas`, `pyarrow`, `matplotlib`
- Path resolver: `paths.py` (repo root) — supports Windows host and Ubuntu VM via VMware shared folders

```python
from paths import SCRIPTS_ROOT, DATA_ROOT, RESULTS_ROOT, DOCS_ROOT, resolve
```

Do not hardcode `D:\...` or `/mnt/hgfs/...` paths in scripts.

## Physical Sign Conventions

| Signal | Units | Convention |
|--------|-------|------------|
| MLCW compaction | mm | negative = compaction |
| $dh$ = H(t) − H($t_{ref}$) | m MSL | negative = head fell; never negate |
| InSAR | mm | negative = subsidence |
| $S_{ske}$, $S_{skv}$ | mm/m | always $\ge$ 0 |
| $S_{skv}$ / $S_{ske}$ ratio | — | 8–100× (inelastic >> elastic) |

## Repository Structure

```
scripts/
  01_insar_preprocessing/   InSAR preprocessing chain
  02_mlcw_processing/       MLCW timeseries processing
  03_gps_processing/        GPS vertical displacement processing
  04_gwl_processing/        Groundwater level data preparation
  05_pairing/               Station-well pairing
  06_direct_ratio/          Direct scaling (static) approach
  07_analysis/              Cross-station analysis and validation
  08_visualization/         Timeseries and spatial plots
  09_trackB/                2S-TOOL batch runs
  10_ihmf/                  IHM-F model (v1, v2, v3 — v3 is active)
  11_data_analysis/         Signal decomposition and collinearity
  12_stress_strain/         Per-layer stress-strain inversion
  13_seasonal_insar/        Seasonal harmonic analysis
  14_lagged_ratio/          Lagged scaling analysis
  15_prediction/            Spatial prediction pipeline
  16_ring_gwl_xcorr/        Ring-GWL cross-correlation
tau_demo_TUKU/              Step-by-step TUKU pilot demo
discussions/                Session notes and method history
docs/                       Reference guides and run commands
notes/                      Literature and dataset notes
plans/                      Implementation plans
```

## Status

Active exploration — method selection not finalized. Read `PROGRESS.md` for the current blocking gate and next action before running any scripts.
