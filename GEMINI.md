# Project: InSAR-MLCW Land Subsidence Research Workspace

## Project Overview

This workspace (`D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2`) is a specialized geospatial data processing and analysis environment for land subsidence research in Taiwan's Choushui River Fluvial Plain (CRFP). The primary objective has been reframed to develop a **Class I / Class II transferability method**: a deployable forward-prediction model that reconstructs 3D depth-resolved groundwater compaction fields using *only* trend-removed InSAR surface deformation and Groundwater Level (GWL) piezometric head data as co-drivers, effectively removing the reliance on ongoing MLCW observations post-calibration.

**Key Technologies and Tools:**
- **Language:** Python 3.10 (Conda environment: `fafalab`)
- **Data Formats:** HDF5 (MintPy), Feather, NetCDF4, GeoPackage, CSV, JSON
- **Core Methodology:** Physics-first modeling, layer-grouped stratigraphy, and time-series decomposition.
- **Key Libraries:** `MintPy` (InSAR), `appsigsolv`, `scipy`, `pandas`, `scikit-learn`.

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

## Building and Running

### Environment Setup
The project requires the `fafalab` Conda environment.
```powershell
# Activate environment
conda activate fafalab

# Note: For GWL scripts, clear PYTHONPATH to avoid contamination
$env:PYTHONPATH = ""; conda run -n fafalab python <script_name>
```

### Path Resolution Protocol (Mandatory)
For Windows/Linux cross-platform compatibility, strictly use `paths.py` for all file access. No hardcoded `D:\...` or `/mnt/hgfs/...` strings.
```python
from paths import SCRIPTS_ROOT, DATA_ROOT, RESULTS_ROOT, DOCS_ROOT, resolve

# Examples:
config_path = DATA_ROOT / "ihmf_config.json"
discussion = DOCS_ROOT / "discussions" / "discussion_memory.md"
```

### Current Development Focus
Two parallel tracks are currently active:
1. **IHM-F v3 (Joint Constrained Least Squares):**
   - **Complete:** `ihmf_io_multilayer.py` and `ihmf_model_v3.py` both exist and are operational.
   - **Next:** Re-run TUKU v3 pilot (existing `TUKU_v3_results.json` from 2026-06-02 is pre-fix and invalid).
2. **Seasonal Harmonic Track:**
   - **Task 1:** Following the successful 3-station pilot, execute the 37-station seasonal harmonic batch using `01_seasonal_harmonic_analysis.py` and `02_reconstruction_visualization.py`.

## Development Conventions

### 1. Physics-First Modeling
- **Layer-Grouped Target:** The prediction targets are 4–6 physically interpretable geological layers (F1, T1, F2, T2, F3, F4). Note: **F = aquifer** and **T = aquitard** (Taiwan CGS convention). Do not invert.
- **Consistent Trend-Removal:** GWL, MLCW, and InSAR data streams must consistently have their multi-year trends removed prior to fitting so that InSAR acts as the integrated proxy.
- **Detrending Rules:** Linear detrending [intercept + linear + annual harmonic] is mandatory before $\tau$ search. **NEVER use moving averages (MA)** for detrending, as they return NaN on 10-year records.
- **Model Rules (IHM-F v3):**
  - GWL is the only per-layer driver; InSAR is the total target in Step 2 only.
  - The `b_k · x` term has been removed entirely.
  - $\tau$ is always a non-negative integer (5-day epoch units); **$\tau$_max = 120** (600 days; raised from 73 on 2026-06-04).
  - Joint constrained least squares for `[S_1…S_N, β=1/α]` simultaneously.
  - **2S-TOOL values are diagnostic reference only** — not used as fixed priors.

### 2. Data & Conventions
- **Sign:** Positive = compaction (subsidence). InSAR data is inverted on load to match MLCW. Raw `dh` is strictly relative to a reference date.
- **Reference Date:** `2015-01-16` is the baseline epoch for all cumulative measurements.
- **GWL Well Codes:** All GWL well identifiers (e.g., `09050321`) must be treated as **8-digit strings with leading zeros**. Converting to integers will drop zeros and break feather column lookups.
- **GWL Input Handling:** GWL piezometric head is assigned via nearest-layer physical screen lookup. **24 of 37 MLCW stations rely on a proxy GWL station** (6 are fully blocked due to missing physical screen depths; 18 lack co-located GWL wells entirely; 2 excluded — JINHU_XIN and LUNFENG_XIN have no grouped MLCW files).
- **Data Reconciliation:** Four stations require explicit overrides to map the Excel pairing to the physical feather files: `DONGSHI` uses `10090111`, `TUKU` uses `09030211` (from FANGCAO), `XIGANG` uses `07240213`, and `ZHUTANG` uses `07250111`.

### 3. Reporting & Reproducibility
- **Headless Plots:** All scripts use `matplotlib.use('Agg')`.
- **Summary Metrics:** Every batch script must produce a cross-station CSV/JSON summary.
- **Memory Safety:** Use `gc.collect()` and `plt.close('all')` in loops over stations.

## Key Files
- `paths.py`: Runtime cross-platform path detection module.
- `CLAUDE.md`: Comprehensive guide for AI assistants (this repo, merged from docs repo 2026-06-05).
- `PROGRESS.md`: Authoritative project status and methodology locked rules (this repo, merged from docs repo 2026-06-05).
- `discussions/discussion_memory.md`: Work diary and long-term narrative record (Required reading).
- `notes/dataset/my_dataset_summary.md`: Living data inventory.