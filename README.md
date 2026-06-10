# InSAR–MLCW Gap-Fill and Subsidence Prediction — Choushui River Alluvial Fan, Taiwan

> **⚠️ Status (2026-06-10): Method exploration — not finalized.**
> Part 1 (TUKU pilot) is complete but awaiting manual validation. Part 2 (multi-well extension to 37 stations) and Parts 3–5 are **BLOCKED** until validation passes. Read `PROGRESS.md` for the current gate and `plans/super_plan_2026-06-09.md` for the full plan.

## The Problem

MLCW (Multi-Level Compaction monitoring Well) instruments in the Choushui River Alluvial Fan (CRAF), Yunlin County, Taiwan have stopped operating or reduced sampling from monthly to semi-annual/annual due to maintenance costs. The observational record is broken. InSAR and GPS surface displacement, together with groundwater level (GWL) data, are continuously available and must substitute for the lost in-situ measurements.

## Research Objectives

1. **Obj 1 — Well-scale gap-fill and prediction:** At each MLCW station, reconstruct historical compaction where data is missing and predict future per-layer compaction using continuously available surface displacement (InSAR/GPS) plus GWL.
2. **Obj 2 — Multi-well extension:** Apply the validated method to all 37 MLCW stations.
3. **Obj 3 — Regional grid prediction:** Extend spatial coverage to 8,577 unmonitored grid points.

**Success criterion (Obj 1):** Gap-fill RMSE < RMSE of static linear interpolation baseline; walk-forward skill score > 0 on held-out epochs.

## Method (Two-Track, Decided by Held-Out Evidence)

The project uses a **two-track approach**, separated by purpose:

### Track 1 — Gap-Fill Engine (PRIMARY): GPS/InSAR Carrier Apportionment

$$b_k(t) = a_k \cdot d_{surface}(t) + c_k \quad (a_k \ge 0)$$

The surface displacement $d_{surface}$ is the sum of all layer compactions — it carries the compaction signal directly. Each layer's share $a_k$ is fit where MLCW exists, then used to reconstruct $b_k(t)$ during gaps. An optional GWL residual term $d_k \cdot u(t)$ captures sub-annual head-driven fluctuations for layers where it improves held-out skill.

**Status:** Selected as primary method at Decision Point 1 (held-out bake-off, 2026-06-09). GPS carrier won all 6 TUKU layers by held-out RMSE over bilinear and interpolation baselines.

### Track 2 — Physical Characterization (SECONDARY): Bilinear Terzaghi/Riley

$$b(t) = c + S_{ke} \cdot u(t) + (S_{kv} - S_{ke}) \cdot V(t)$$

$$V(t) = \min(0, \text{cummin}(H) - h_c)$$

The correct physics for reporting per-layer elastic ($S_{ske}$) and inelastic ($S_{skv}$) skeletal specific storage. Used to characterize sediment compressibility — **not** for gap-fill (held-out tests show it is the worst gap-fill method on every layer).

**Status:** Bug-fixed and verified (Phase 0.0, 2026-06-09). All TUKU layers: $S_{ke} \ge 0$, $S_{kv} \ge S_{ke}$, per-layer $R^2_{cum} > 0$.

## Current State (2026-06-10)

| Milestone | Status |
|-----------|--------|
| Part 0 — Bug fixes + method bake-off | ✅ Complete — Decision Point 1: CARRIER-PRIMARY |
| Part 1 — TUKU pilot (carrier reconstruction + prediction + characterization) | ✅ Complete — awaiting validation |
| Part 2 — Multi-well extension (37 stations) | ⏸️ BLOCKED |
| Part 3 — Regional grid prediction (8,577 points) | ⏸️ BLOCKED |
| Part 4 — Guardrails wiring | ⏸️ BLOCKED |
| Part 5 — Publication outputs | ⏸️ BLOCKED |

### Decision Points

| # | Question | Verdict |
|---|----------|---------|
| DP 0 | Is the bilinear model trustworthy for parameters? | **PASS** — All $S_{ke} \ge 0$, $S_{kv} \ge S_{ke}$, per-layer $R^2_{cum} > 0$ |
| DP 1 | Which method fills gaps best? | **CARRIER-PRIMARY** — GPS carrier wins all 6 TUKU layers |
| DP 2 | Can the carrier predict 6 months ahead? | **PARTIAL** — T1/T2 pass (skill +0.41/+0.43), aquifers fail |

## Key Scripts

### Part 1 — TUKU Pilot (active)

| Script | Purpose |
|--------|---------|
| `tau_demo_TUKU/bilinear_fit.py` | Standalone bilinear Terzaghi/Riley fitter with per-layer intercept |
| `tau_demo_TUKU/13_holdout_method_bakeoff.py` | Three-method held-out evaluator (Decision Point 1) |
| `tau_demo_TUKU/14_carrier_reconstruction_tuku.py` | GPS carrier reconstruction + prediction + recalibration |
| `tau_demo_TUKU/14b_carrier_gwl_eval.py` | GWL residual term held-out evaluation |
| `tau_demo_TUKU/15_storage_characterization.py` | Bilinear $S_{ske}$/$S_{skv}$ characterization (Phase 1.4) |

### Production IHM-F Solver

| Script | Purpose |
|--------|---------|
| `scripts/10_ihmf/fit_ihm_f_v3.py` | Production entry point — per-station fitting |
| `scripts/10_ihmf/ihmf_model_v3.py` | Core model: cumulative NNLS solver, τ grid search |
| `scripts/10_ihmf/ihmf_io_multilayer.py` | Data loader: GPS + GWL + MLCW with zero-referencing |
| `scripts/10_ihmf/diagnose_cumulative_tuku.py` | Per-layer cumulative diagnostics |
| `scripts/guardrails.py` | Automated physical-law validation (10 checks) |

## Quick Run (Ubuntu 22.04 VM)

```bash
# Environment
PYTHONPATH="" conda run -n isce_ncu3 python <script>

# TUKU pilot — production fit
PYTHONPATH="" conda run -n isce_ncu3 python scripts/10_ihmf/fit_ihm_f_v3.py --station TUKU --gps --all --alpha 0.625

# TUKU pilot — carrier reconstruction (default: carrier-only)
PYTHONPATH="" conda run -n isce_ncu3 python tau_demo_TUKU/14_carrier_reconstruction_tuku.py

# TUKU pilot — carrier + GWL for T1
PYTHONPATH="" conda run -n isce_ncu3 python tau_demo_TUKU/14_carrier_reconstruction_tuku.py --use-gwl T1

# Bake-off evaluation
PYTHONPATH="" conda run -n isce_ncu3 python tau_demo_TUKU/13_holdout_method_bakeoff.py

# Bilinear characterization
PYTHONPATH="" conda run -n isce_ncu3 python tau_demo_TUKU/15_storage_characterization.py
```

Full command catalog: `docs/run_commands.md`

## Environment

- Python 3.11, `isce_ncu3` conda environment (Ubuntu 22.04 VM)
- Key packages: `numpy`, `scipy` (≥ 1.17), `pandas`, `pyarrow`, `matplotlib`
- Path resolver: `paths.py` (repo root) — supports Windows host and Ubuntu VM

```python
from paths import SCRIPTS_ROOT, DATA_ROOT, RESULTS_ROOT, DOCS_ROOT, resolve
```

Do not hardcode `D:\...` or `/mnt/hgfs/...` paths in scripts.

## Physical Sign Conventions

| Signal | Units | Convention |
|--------|-------|------------|
| MLCW compaction | mm | negative = compaction |
| $dh$ = H(t) − H($t_{ref}$) | m MSL | negative = head fell; **never negate** |
| InSAR / GPS | mm | negative = subsidence |
| $S_{ske}$, $S_{skv}$ | m⁻¹ or mm/m | always $\ge$ 0 |
| $S_{skv}$ / $S_{ske}$ bulk ratio | — | 8–100× (inelastic >> elastic) |
| Head zero-referencing | m | $u(t) = H(t) - H(t_{ref})$; $t_{ref}$ = 2015-01-16 |

## Repository Structure

```
scripts/
  01_insar_preprocessing/   InSAR preprocessing chain
  02_mlcw_processing/       MLCW timeseries processing
  03_gps_processing/        GPS vertical displacement processing
  04_gwl_processing/        Groundwater level data preparation
  05_pairing/               Station-well pairing
  07_analysis/              Cross-station analysis and validation
  08_visualization/         Timeseries and spatial plots
  10_ihmf/                  IHM-F model (v3 active; v1/v2 superseded)
  12_stress_strain/         Per-layer stress-strain inversion
  13_seasonal_insar/        Seasonal harmonic analysis
  15_prediction/            Spatial prediction pipeline (pre-carrier, OBSOLETE)
tau_demo_TUKU/              TUKU pilot (Part 1): bake-off, reconstruction, characterization
discussions/                Session notes and method history
docs/                       Reference guides and run commands
plans/                      Implementation plans (super_plan_2026-06-09.md is authoritative)
results/                    Output files (gitignored — source files only in repo)
```

## Further Reading

- **Current gate + next action:** `PROGRESS.md`
- **Full implementation plan:** `plans/super_plan_2026-06-09.md`
- **Physics safeguards:** `discussions/PHYSICS_SAFEGUARDS.md`
- **Post-mortem (incremental solver failure):** `discussions/POST_MORTEM_INCREMENTAL_CANCELLATION.md`
- **Data inventory:** `notes/dataset/my_dataset_summary.md`
