# Project: InSAR-MLCW Land Subsidence Research Workspace

## Project Overview

This workspace (`D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2`) is a specialized geospatial data processing and analysis environment for land subsidence research in Taiwan's Choushui River Fluvial Plain (CRAF). 

**Corrected Objective (Post Zero-Trust Audit, 2026-06-09):** The primary objective is **Gap-Fill and Forward Prediction**, not mere static calibration. The goal is to reconstruct broken MLCW (Multi-Layer Compaction monitoring Well) records, predict future compaction per layer, and extend spatial coverage to 8,577 unmonitored grid points. This is achieved by utilizing InSAR/GPS surface displacement, Groundwater Level (GWL), and borehole stratigraphy.

**Key Technologies and Tools:**
- **Language:** Python (Base conda environment: `fafalab` does NOT exist on the primary Windows host. Use base Python: `C:\Users\Huy\anaconda4\python.exe`)
- **Data Formats:** HDF5 (MintPy), Feather, NetCDF4, GeoPackage, CSV, JSON
- **Core Methodology:** Two-track strategy: InSAR/GPS-carrier apportionment (for gap-fill) and cumulative bilinear Terzaghi/Riley model (for physical characterization).
- **Key Libraries:** `scipy.optimize.nnls`, `scipy.optimize.lsq_linear`, `pandas 2.3.3`, `pyarrow 21.0`.

## Directory Structure

Following a reorganization on 2026-05-19, the project is structured hierarchically:

- `scripts/`: Sequential processing pipeline:
  - `01_insar_preprocessing/`: LOS decomposition, adaptive OMT fitting, interpolation (Kriging/IDW).
  - `02_mlcw_processing/`: MLCW decomposition and hydrofacies alignment.
  - `03_gps_processing/`: GPS vertical displacement decomposition.
  - `04_gwl_processing/`: GWL data extraction (feather-format conversion) and linkage inspection.
  - `05_modeling/` to `08_visualization/`: Early modeling methods, analysis, and plotting.
  - `09_trackB/`: GWL-driven IHM-F pipeline (2S-TOOL batch, IHM-F fitting).
  - `10_ihmf/`: IHM-F modeling scripts including detrending and multi-layer fitting.
  - `11_data_analysis/`: Additional diagnostic analyses.
  - `12_stress_strain/` & `12_validation/`: Validation and stress-strain relationships.
  - `13_seasonal_insar/`: Seasonal harmonic pipeline.
  - `14_lagged_ratio/` & `15_prediction/`: Prediction modules.
  - `notebooks/`: Interactive data exploration, layer-grouping (`mlcw_by_group.py`).
- `tau_demo_TUKU/`: Standalone pilot directory for the TUKU tau search campaign and seasonal $S_{ske}$ diagnostic.
- `data/`: Curated datasets:
  - `insar/`: Parametric surface displacement (trend + harmonics + breakpoints).
  - `mlcw/`: Raw timeseries, decomposed models, 5m regular grids, and **layer-grouped timeseries (F1, T1, F2, T2, F3, F4)**.
  - `gps/`: Raw and decomposed GNSS timeseries.
  - `gwl/`: Well info, material summaries, and feather-formatted timeseries (primary).
- `results/`: Model outputs, performance metrics, and logs.
- `figures/`: Generated plots organized by dataset and method.
- `gis/`: Spatial layers (shapefiles, Kriging/velocity layers).
- `docs/`: Reorganization logs, path mappings, and technical notes.

## Current Status (2026-06-13)

**BLOCKED — awaiting human review.** M6–M9 complete (2026-06-11); Red Team remediation complete (2026-06-12, scripts 26–30); DP-SEQ re-graded **PARTIAL** (accuracy PASS at annual cadence, skill ≤ 0 for F2/T2 on honest anchor-once baseline, coverage FAIL at semiannual 3/6 layers). Corrected deployable claim: **secular trend apportionment + datum maintenance by sparse visits + partial F2 seasonal dynamics**. Sub-annual multilayer dynamics at sparse cadence are mathematically underdetermined (carrier rank-1 proven by SVD; amplitude-bound lemma). F3 forensic triage verdict: CONFLUENCE — instrumentation gap (no piezometer screened in F3 clay 240–275 m), code exonerated. Do not proceed to Part 2/3 without human sign-off.

## Current Development Focus

Following the rigorous Zero-Trust Audit (2026-06-09), the incremental solver (IHM-F v3) has been officially abandoned due to structural failure (cancellation of preconsolidation stress memory). The project is now executing a **Two-Track Strategy**:

1. **Gap-Fill / Prediction Track (PRIMARY - Carrier Apportionment):** 
   - Surface displacement (InSAR/GPS) is the integral of all layer compactions. Each layer's compaction is modeled as a physically bounded share ($a_k$) of the continuously available surface signal. This method is mathematically proven to beat GWL-only models for held-out gap filling.
2. **Physical-Characterization Track (SECONDARY - Cumulative Bilinear Model):** 
   - The Terzaghi/Riley cumulative model: $b(t) = c + S_{ke} \cdot u(t) + (S_{kv} - S_{ke}) \cdot V(t)$ is used strictly to report layer compressibility ($S_{ke}$, $S_{kv}$), **NOT** to gap-fill.
   - **Critical Bug Fix:** The solver now strictly requires an intercept term ($c$) and zero-referenced head ($u = H - H_{ref}$). Absolute head is no longer used for the elastic term to prevent $S_{ke}$ from collapsing to zero.

## Development Conventions

### 1. Physics-First Modeling & Strict Guardrails
- **The Two-Regime Cumulative Model:** Deformation is split into elastic recovery and inelastic virgin consolidation. The virgin term $V(t) = \min(0, \text{cummin}(H) - h_c)$ carries permanent strain memory and must be monotonically non-increasing.
- **Head Zero-Referencing (Mandatory):** Head values must be zero-referenced ($u = H - H_{ref}$) before entering any elastic calculation. $h_c$ is the absolute pre-REF_DATE minimum (Bug F constraint).
- **Automated Guardrails (`guardrails.py`):** No parameter is written to disk without passing physical laws: $S_{ke} \ge 0$, $S_{kv} \ge S_{ke}$, and the specific-storage ratio $S_{skv} / S_{ske}$ must be evaluated using matching thicknesses (bulk vs. specific).
- **Layer-Grouped Target:** The prediction targets are 4–6 physically interpretable geological layers (F1, T1, F2, T2, F3, F4). **F = aquifer** and **T = aquitard**. Do not invert naming.

### 2. Data & Environment Conventions
- **Interpreter Rule:** Always reset the PYTHONPATH before running scripts on the Windows host to avoid library contamination: `$env:PYTHONPATH=""; & "C:\Users\Huy\anaconda4\python.exe" <script>`.
- **Sign Convention:** Positive = compaction (subsidence) for final deliverables, but internally, models use standard geomechanical signs where $H < 0$ and $b < 0$ represent compaction in the negated NNLS matrix.
- **Reference Date:** `2015-01-16` is the baseline epoch for all cumulative measurements.
- **Data Reality Check:** For deep aquifers (F2, F3), GWL data may not exist prior to 2012. Solvers cannot invent missing historical drivers. Where GWL is absent, the InSAR/GPS carrier is the only valid physical proxy.

### 3. Verification Before Promotion
- **No Promotion on In-Sample Fit:** A method may only be promoted to a gap-fill engine if it mathematically beats the "static linear interpolation" baseline on a **held-out** test set. High calibration $R^2$ is an illusion of pooling and is not sufficient.
- **Specific vs. Bulk Ratios:** Be explicitly aware of the thickness artifact. Dividing $S_{ske}$ by total span while dividing $S_{skv}$ by clay-only thickness inflates the ratio (e.g., F2's "221x failure" was an artifact). Always report the bulk ratio (same-thickness) for true elastic/inelastic contrasts.

## Path Resolution Protocol (Mandatory)
For Windows/Linux cross-platform compatibility, strictly use `paths.py` for all file access. No hardcoded `D:\...` or `E:\...` strings inside scripts.
```python
from paths import SCRIPTS_ROOT, DATA_ROOT, RESULTS_ROOT, DOCS_ROOT, resolve
```

## Key Files
- `plans/super_plan_2026-06-09.md`: The authoritative, audited execution roadmap.
- `plans/ZeroTrust_Audit_Report_20260609.md`: The architectural audit that forced the two-track pivot.
- `plans/Bilinear_Model_Test_Findings_20260609.md`: Proof of the absolute-head bug and the 3-method bake-off.
- `scripts/guardrails.py`: Mandatory physical validation gates.
- `paths.py`: Runtime cross-platform path detection module.