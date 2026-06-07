# Script Descriptions — InSAR-MLCW Project

Generated 2026-05-19. Each entry describes what the script does, its key inputs/outputs, and the core method it implements.

---

## 01 — InSAR Preprocessing

### `A1_run_adaptive_omt_asc.py`
Iteratively fits deformation models to an ascending-track InSAR timeseries, running the Overall Model Test (OMT) after each fit to detect poorly-modeled pixels. It analyzes residuals of rejected pixels using FFT (to find missing seasonal signals) and velocity derivatives (to detect kinematic breaks like droughts), then automatically adds the missing model components and re-fits until the rejection rate falls below a target threshold.

### `A1_run_adaptive_omt_desc.py`
Same as `A1_run_adaptive_omt_asc.py` but for the descending-track InSAR timeseries. Uses descending-specific input files and produces a separate adaptive OMT report.

### `A2_insar_omt_v3.py`
Evaluates how well a deformation model fits an InSAR residual timeseries by computing the normalized Overall Model Test (OMT = SSR/sigma^2/r, expected value 1.0 under H0). It auto-detects the number of model parameters from file attributes, estimates noise sigma from a stable-pixel mask, writes OMT and p-value maps to HDF5, optionally saves a spatial OMT map as PNG, and performs a per-date w-test to flag problematic acquisition dates.

### `B_resample_timeseries_model.py`
Generates a temporally-regularized deformation timeseries by projecting a fitted kinematic model (polynomial + periodic + polyline terms) onto a fixed schedule of dates (e.g., the 1st, 6th, 11th, 16th, 21st, and 26th of each month). It reads the original irregularly-sampled timeseries, fits the model via least squares per pixel in spatial patches, and writes a new timeseries HDF5 file with deformation values at the regular target dates.

### `C_insar_crop_to_overlap.py`
Finds the common geographic overlap between ascending and descending InSAR timeseries files and crops both to that shared region using MintPy's built-in subsetting functions. It reads spatial metadata from both files, computes the intersection of their geographic bounding boxes, converts that to pixel boxes for each track, and verifies the cropped outputs have matching dimensions and coordinates.

### `D1_insar_remove_dates.py`
Removes specific dates from a MintPy timeseries HDF5 file by loading all data into memory, filtering the time axis with a boolean mask, and writing a new file with the remaining dates and updated metadata.

### `D1_insar_remove_dates_optimized.py`
Same purpose as `D1_insar_remove_dates.py` (remove specific dates from a timeseries HDF5) but uses patch-by-patch spatial processing instead of loading the full dataset into memory, making it suitable for large files. It also handles 1D/3D perpendicular baseline (`bperp`) datasets and warns when the reference date is being removed.

### `D2_insar_mask_optimized.py`
Applies a 2D spatial mask to a MintPy HDF5 file (timeseries, velocity, geometry, etc.) by zeroing or NaN-filling masked-out pixels using patch-by-patch processing for memory efficiency. It handles both 2D and 3D datasets, automatically converting integer types to float when NaN fill is requested, and writes the masked result to a new file.

### `E1_insar_asc_desc_decompose_parallel.py`
Decomposes ascending and descending InSAR line-of-sight (LOS) displacement timeseries into horizontal and vertical components using multiprocessing over date chunks. It reads two HDF5 timeseries files, finds their spatial overlap and common dates, then calls MintPy's `asc_desc2horz_vert` in parallel across multiple CPU cores. Outputs two HDF5 files: one for the horizontal component and one for the vertical component.

### `E2_insar_asc_desc_decompose_optimized.py`
Same decomposition task (LOS to horizontal/vertical) but optimized for memory-constrained environments by processing the spatial domain in row-strip patches serially instead of parallelizing over dates. It reads only one spatial patch at a time, decomposes all dates for that patch in a single vectorized matrix operation, and writes the result immediately to HDF5. Uses a `--max-memory` flag to control patch size and avoid out-of-memory errors on very large grids.

### `F_plot_insar_vs_gps_leveling.py`
Loads CSV files comparing InSAR vertical velocities against GPS and leveling reference velocities, converts units to cm/year, and generates publication-quality scatter plots (PDF + PNG) for each comparison. Adds a 1:1 reference line and reports RMSE and R-squared statistics in an annotation box.

### `G_create_subset.py`
Reads a station grid CSV, computes a bounding box buffered by 5 km, and prints a ready-to-run command for MintPy's `subset.py` to clip an InSAR timeseries HDF5 file to that spatial extent.

### `H_resample_timeseries_model.py`
Resamples an irregular InSAR timeseries onto a regular schedule (e.g., days 1, 6, 11, 16, 21, 26 of each month) by fitting a kinematic deformation model (polynomial + periodic terms) to the original data and projecting it onto the new dates. Processes the spatial domain in memory-limited patches, using least-squares fitting per pixel to generate a model-based temporally-regular output HDF5.

### `K1_interp_timeseries_insar.py`
Interpolates InSAR timeseries values from a gridded HDF5 file onto point locations (GNSS stations) using anisotropic kriging with trend removal. For each date, it detrends the InSAR data with a polynomial surface, fits a kriging model (with Optuna hyperparameter search, optionally cached), predicts at station coordinates, and adds the trend back. Uses multiprocessing across dates and a KDTree buffer to limit InSAR points.

### `K2_interp_timeseries_IDW.py`
Interpolates InSAR timeseries values from an HDF5 grid onto shapefile points using Inverse Distance Weighting (IDW) with KDTree pre-filtering for speed. For each date, it trains a `KNeighborsRegressor` with distance-based weights, predicts at the target coordinates, and applies a maximum-distance constraint to avoid extrapolation. Outputs a shapefile or GeoPackage with one column per date.

### `stage2_idw_compaction.py`
Computes a 3D aquifer compaction field by combining depth-dependent compaction fraction profiles (f_median, f_p05, f_p95) from 39 MLCW stations with InSAR timeseries at 8,577 grid points. It smooths the station profiles along depth, interpolates them to all grid points via IDW, then multiplies the interpolated fractions by the InSAR displacement at each grid point and epoch. Outputs the compaction fraction grid and three NetCDF4 compaction volumes (central, lower bound, upper bound) along with leave-one-out cross-validation results.

---

## 02 — MLCW Processing

### `batch_process_MLCW.py`
Loops over all MLCW station CSV files (one per station, containing ring-by-ring displacement time series) and runs the `appsigsolv` signal decomposition on each one, fitting seasonal (0.5- and 1-year) and long-term polynomial components. Outputs model JSON files and plots into a decomposition output directory.

### `batch_reconstruct_MLCW.py`
Loops over the decomposition results (JSON model files) from `batch_process_MLCW.py` and reconstructs each station's ring-by-ring displacement time series onto a regular date grid (custom monthly days or daily sampling). Saves a single merged CSV per station with one column per ring at the common output dates.

### `mlcw_5m_grid.py`
Takes each station's reconstructed ring-by-ring CSV, computes a bottom-up cumulative compaction profile, extrapolates to the surface via linear regression through the shallowest rings, then interpolates onto a uniform 5 m depth grid (0-300 m) using PCHIP splines. Outputs a CSV with columns `datetime, depth_000m, depth_005m, ..., depth_300m` in mm.

### `mlcw_hydrofacies_5m.py`
For each of the 39 MLCW stations, finds the nearest 112_BME hydrofacies grid cell (by Euclidean distance in TWD97 coordinates), extracts the 1 m resolution material codes, and aggregates them into 5 m bins by taking the modal material class. Produces a CSV mapping every (station, 5 m depth level) to its dominant lithologic class (clay, sand, gravel, etc.).

---

## 03 — GPS Processing

### `batch_process_GPS_dU.py`
Loops over all GPS station CSV files (with components east, north, up) and runs the `appsigsolv` signal decomposition on the vertical (dU) component only, fitting seasonal and polynomial trend components. Outputs model JSON files and plots into a GPS decomposition directory, mirroring the MLCW batch processing workflow.

---

## 04 — Groundwater Level Processing

### `extract_well_info_deepseek.py`
Splits a groundwater well information PDF page by page, sends each page's text to the DeepSeek API with a structured prompt to extract an 11-column well table (zone code, coordinates, address, elevation, casing depth, screen intervals, data period), then post-processes the model output with deterministic rules to fix coordinate swaps and merged columns. Saves one Markdown table per page.

### `extract_well_info_direct.py`
Extracts well information from the same PDF using pure regex and PyPDF2, without any LLM API. Parses each page's raw text by locating 8-character computer IDs to identify well records, then extracts coordinates, elevation, casing depth, screen intervals, and data period using pattern matching. Produces one Markdown table per page plus a combined CSV of all wells.

### `inspect_gwater_data.py`
Loads a groundwater level HDF5 dataset and evaluates every monitoring well's data quality during the InSAR study period (2015-2025), computing coverage fraction, statistics, linear trend, seasonal amplitude, and gap analysis. Produces a detailed JSON report with per-station and per-well metrics, an MLCW station overlap analysis, a yearly coverage table, and a flat CSV for spreadsheet review.

### `parse_gwl_materials.py`
Parses 95 text files from a groundwater well material assignment dataset, extracting station coordinates, elevation, total aquifer layer count, and individual layer depths and thicknesses using regex. Outputs two CSVs: a wide-format summary with up to 5 layer pairs per station, and an aggregated thickness table with total aquifer thickness and fraction of the 200 m column.

### `verify_gwl_output.py`
Reads the two CSVs produced by `parse_gwl_materials.py` and prints summary statistics, lists the MLCW-overlap stations with their aquifer thickness values, identifies stations with no aquifer layers, and reports the min/max/mean thickness and fraction across all 95 stations. Serves as a quick verification script for the material parsing output.

---

## 05 — Modeling

### `arx_ablation.py`
Decomposes the RMSE improvement of the ARX model over the static baseline into two parts: the gain from initial-state anchoring alone and the additional gain from the full ARX recursive terms. Runs a 4-fold walk-forward validation across 19 active MLCW stations and outputs per-depth CSV tables plus summary figures.

### `arx_all_stations.py`
Fits an ARX model (auto-regressive with exogenous InSAR input) at each depth for every MLCW station, using OLS to estimate phi (memory), beta (proportional loading), and gamma (rate response) coefficients. Performs 4-fold walk-forward validation against a static direct-ratio baseline and writes per-station parameter CSVs, fold-wise RMSE tables, and a stacked NPZ file of all parameters.

### `arx_validate_all_stations.py`
Generates validation figures and numeric metrics for the ARX walk-forward predictions across all active MLCW stations. Produces per-station time-series panels, RMSE depth profiles, residual heatmaps, total-column plots, and a cross-station summary JSON that reports RMSE improvement, smoothness ratio, and direction agreement.

### `arx_visualize.py`
Creates five summary figures for the ARX Method 7 results across all stations: a bar chart comparing ARX vs baseline RMSE, a depth-by-station RMSE improvement heatmap, phi coefficient depth profiles for all 39 stations, and TUKU-specific time series and per-fold RMSE panels.

### `arx_visualize_shutdown.py`
Validates the ARX model on the 20 MLCW stations that stopped recording around 2021, using a within-window holdout (training up to 2020-11-30, holdout from 2020-12-01 to station end). Generates per-station time-series figures, RMSE profiles, a summary heatmap across all shutdown stations, and a summary CSV.

### `fit_exponential.py`
Fits an exponential decay model (y = a * (exp(-b * x) - 1)) to a single-station displacement time series from a CSV file to estimate ultimate subsidence and decay rate. Reads date and displacement columns, fits via scipy.optimize.curve_fit, and saves a plot of the observed data with the fitted curve.

### `prophet_tuku.py`
Applies Facebook Prophet with InSAR as an exogenous regressor to forecast MLCW compaction at TUKU station across 60 depth levels. Runs 4-fold walk-forward validation, compares Prophet RMSE against the static direct-ratio baseline and ARX, and produces bar charts, 4-depth time-series panels, and an improvement comparison figure.

---

## 06 — Direct Ratio

### `direct_ratio_all_stations.py`
Runs the direct ratio analysis (f_k = MLCW / InSAR at each depth) for all 39 MLCW stations in batch. Loads the InSAR feather file once, aligns each station's MLCW by date, computes per-depth ratio statistics (median, quartiles, percentiles), and saves CSV results, ratio matrices, depth-profile plots, and heatmaps to per-station output folders.

### `direct_ratio_tuku.py`
Computes the direct ratio f_k = MLCW / InSAR at each depth for TUKU station only, using data from a project-level loader with sign reversal (positive = compaction). Saves the per-depth ratio statistics as CSV, the full ratio matrix as NPY, and generates a depth-profile figure overlaid with Stage 1 w_k estimates and a ratio heatmap over time.

### `direct_ratio_tuku_v2.py`
Repeats the direct ratio analysis for TUKU station but uses the raw sign convention (negative = subsidence, no negation) and loads data directly from source files instead of the project loader. Produces v2 CSV, NPY, profile, and heatmap outputs, and creates a side-by-side comparison figure showing how the ratio profile differs from the v1 (negated) version.

---

## 07 — Analysis

### `alpha_insar_test.py`
Computes alpha = v_MLCW / v_InSAR for each MLCW station by fitting linear slopes to both time series over their overlapping date window, then compares the result against existing GNSS-derived alpha values. Outputs a CSV with per-station velocity and alpha comparison metrics sorted by discrepancy.

### `compare_reconstructions_per_ring.py`
For each station, creates six multi-panel figures (3 depth ranges covering 0-295 m, for both harmonic and wet/dry methods) comparing observed MLCW compaction against a scalar baseline and either a harmonic decomposition or wet/dry split reconstruction. Each subplot is annotated with the RMSE improvement percentage relative to the scalar baseline.

### `harmonic_allstations.py`
Batch processes all 39 stations: decomposes InSAR and MLCW signals into trend (centred moving average) and seasonal components, fits per-depth ratio profiles for each component, reconstructs MLCW using a harmonic model, and evaluates RMSE improvement over a scalar baseline. Outputs per-station CSV/JSON/plots and cross-station summary files with recommendation flags.

### `optionB_harmonic_TUKU.py`
Single-station harmonic decomposition test for TUKU: separates InSAR and MLCW into trend and seasonal components, fits per-depth median ratios, reconstructs MLCW as f_trend x trend + f_seas x seas, and compares RMSE against the scalar baseline. Saves CSV profiles, a JSON summary, and three diagnostic plots (depth profiles, RMSE comparison, residual heatmap).

### `summarize_allstations.py`
Reads cross-station JSON summaries from harmonic_allstations and wetdry_allstations, then produces two 2-panel bar charts showing overall RMSE improvement percentage and fraction of depths improved across all stations. Highlights stations where each method is recommended.

### `validate_all_stations.py`
Batch in-sample validation for all 39 stations: predicts MLCW as f_k x InSAR, then computes RMSE, R-squared, bias, band coverage, and seasonal misfit metrics (harmonic residual amplitude, detrended correlation, autocorrelation) per depth level. Generates per-station time series, scatter, RMSE profile, residual heatmap, total-column, and coverage plots, plus a cross-station summary CSV/JSON.

### `validate_insar_proxy_tuku.py`
Single-station in-sample validation for TUKU that evaluates how well the scalar model Y_hat = f_k x InSAR reproduces observed MLCW compaction. Produces RMSE/R-squared depth profiles, a residual heatmap, scatter plots at four selected depths, a total-column time series with P05-P95 uncertainty bands, and a coverage plot.

### `wetdry_allstations.py`
Batch wet/dry season diagnostic for all 39 stations: splits the direct-ratio matrix into wet (May-Oct) and dry (Nov-Apr) epochs, computes separate per-depth ratio profiles, evaluates RMSE improvement of the wet/dry split reconstruction over the scalar baseline, and generates diagnostic plots and a cross-station summary with recommendation flags.

### `wetdry_diagnostic_TUKU.py`
Single-station wet/dry season diagnostic for TUKU: separates the ratio matrix by wet and dry seasons, computes per-depth profiles for each season, evaluates RMSE improvement of the seasonal split reconstruction, and produces four diagnostic plots plus a CSV and JSON summary with decision-tree metrics.

---

## 08 — Visualization

### `inspect_insar_feather.py`
Quick inspection script that reads the InSAR feather file and prints its shape, column types (metadata vs epoch columns), and a sample of the MLCW TUKU 5-m grid data. Used to verify data structure before downstream analysis.

### `plot_mlcw.py`
Creates a publication-quality A4 figure showing MLCW ring-by-ring compaction profiles with depth on the y-axis and cumulative compaction on the x-axis, where each time series line is coloured by date. Reads a CSV with datetime index and ring-depth columns, and saves the figure to a PNG file.

### `timeseries_check.py`
Loops through all MLCW-GPS station pairs, loads modelled time series, aligns them to mutual dates, and creates a two-panel figure showing displacement comparison (top) and MLCW/GPS ratio (bottom). Also computes linear slope velocities and saves per-station slope ratios to JSON files.

---

## 09 — Notebooks

### `20260428_prepare_datasets.ipynb`
Exports GPS, MLCW, and InSAR metadata and time series to CSV files; finds the nearest GPS neighbour for each MLCW station using spatial join; models GPS and MLCW time series with appsigsolv; computes and saves MLCW average velocity trends; converts InSAR shapefiles to feather format; and saves MLCW/GPS ratio RBF interpolation results.

### `20260506_scripts_for_plot.ipynb`
Compares original MLCW ring-by-ring time series against modelled and reconstructed versions using side-by-side and overlapping cumulative compaction profile plots across all stations. Also cleans MLCW 5-m regular CSV column names by removing the depth_ prefix and "m" suffix.

### `20260519_prepare_gwl_data.ipynb`
Notebook for preparing groundwater level data. (Minimal executable content at this time.)
