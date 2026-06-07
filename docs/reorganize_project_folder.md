# Proposed Directory Reorganization — InSAR–MLCW Subsidence Analysis

## Design Principles

1. **Separate code, data, results, and figures** — never mix scripts with outputs.
2. **Group by function first, then by station** — a reader can find everything about "ARX modeling" in one place.
3. **Number pipeline stages** — mirrors the `A1→K2` convention already used in `scripts_2026_Apr_May/`.
4. **One canonical version, archive the rest** — reduce duplication; old/alternate versions go into `archive/`.

## Proposed Tree

```
20260427_InSAR_MLCW_v2/
│
├── README.md
├── project.code-workspace
├── schema.ini
│
├── scripts/                              # All executable code
│   ├── 01_insar_preprocessing/           # InSAR OMT, ASC/DESC, interpolation
│   │   ├── A1_run_adaptive_omt_asc.py
│   │   ├── A1_run_adaptive_omt_desc.py
│   │   ├── A2_insar_omt_v3.py
│   │   ├── B_resample_timeseries_model.py
│   │   ├── C_insar_crop_to_overlap.py
│   │   ├── D1_insar_remove_dates.py
│   │   ├── D1_insar_remove_dates_optimized.py
│   │   ├── D2_insar_mask_optimized.py
│   │   ├── E1_insar_asc_desc_decompose_parallel.py
│   │   ├── E2_insar_asc_desc_decompose_optimized.py
│   │   ├── F_plot_insar_vs_gps_leveling.py
│   │   ├── G_create_subset.py
│   │   ├── H_resample_timeseries_model.py
│   │   ├── K1_interp_timeseries_insar.py
│   │   ├── K2_interp_timeseries_IDW.py
│   │   ├── stage2_idw_compaction.py
│   │   └── merge_tseries_notes.md
│   │
│   ├── 02_mlcw_processing/              # MLCW batch ops, reconstruction, 5m grid
│   │   ├── batch_process_MLCW.py
│   │   ├── batch_reconstruct_MLCW.py
│   │   ├── mlcw_5m_grid.py
│   │   └── mlcw_hydrofacies_5m.py
│   │
│   ├── 03_gps_processing/               # GPS signal decomposition
│   │   └── batch_process_GPS_dU.py
│   │
│   ├── 04_gwl_processing/               # Groundwater well data
│   │   ├── inspect_gwater_data.py
│   │   ├── parse_gwl_materials.py
│   │   ├── verify_gwl_output.py
│   │   ├── extract_well_info_deepseek.py
│   │   └── extract_well_info_direct.py
│   │
│   ├── 05_modeling/                     # ARX, Prophet, exponential fitting
│   │   ├── arx_all_stations.py
│   │   ├── arx_ablation.py
│   │   ├── arx_validate_all_stations.py
│   │   ├── arx_visualize.py
│   │   ├── arx_visualize_shutdown.py
│   │   ├── prophet_tuku.py
│   │   └── fit_exponential.py
│   │
│   ├── 06_direct_ratio/                 # Direct ratio computation
│   │   ├── direct_ratio_all_stations.py
│   │   ├── direct_ratio_tuku.py
│   │   └── direct_ratio_tuku_v2.py
│   │
│   ├── 07_analysis/                     # Harmonic, wet/dry, alpha, validation
│   │   ├── harmonic_allstations.py
│   │   ├── optionB_harmonic_TUKU.py
│   │   ├── wetdry_allstations.py
│   │   ├── wetdry_diagnostic_TUKU.py
│   │   ├── alpha_insar_test.py
│   │   ├── validate_all_stations.py
│   │   ├── validate_insar_proxy_tuku.py
│   │   └── summarize_allstations.py
│   │
│   ├── 08_visualization/                # Plotting and inspection
│   │   ├── plot_mlcw.py
│   │   ├── timeseries_check.py
│   │   └── inspect_insar_feather.py
│   │
│   └── notebooks/                       # Jupyter notebooks (if any remain)
│       └── *.ipynb
│
├── data/                                # Raw & lightly processed input data
│   ├── mlcw/
│   │   ├── raw_timeseries/              # from MLCW_timeseries/
│   │   │   └── {STATION}_ringbyring.csv   (39 files)
│   │   ├── decomposed/                  # from MLCW_decomposition/
│   │   │   └── {STATION}_ringbyring/      (39 dirs, CSV+PNG per ring)
│   │   ├── modeled/                     # from MLCW_modeled/
│   │   │   └── {STATION}_ringbyring.csv   (39 files)
│   │   ├── reconstructed/               # from MLCW_reconstruction/
│   │   │   └── {STATION}_ringbyring_reconstructed.csv (39 files)
│   │   └── regular_5m/                  # from MLCW_5m_regular/
│   │       └── {STATION}_5m_grid.csv     (39 files)
│   │
│   ├── insar/
│   │   └── timeseries/                  # from InSAR_timeries/
│   │       ├── mlcw_interp_insar_IDW_extend.feather
│   │       ├── mlcw_interp_insar_IDW_extend.gpkg
│   │       ├── gridpnt_500m_interp_insar_IDW_extend.feather
│   │       └── gridpnt_500m_interp_insar_IDW_extend.gpkg
│   │
│   ├── gps/
│   │   ├── raw_timeseries/              # from GPS_timeseries/
│   │   │   ├── patch_1/{STATION}_neu.csv  (31 files)
│   │   │   └── patch_2/{STATION}_neu.csv  (28 files)
│   │   ├── decomposed/                  # from GPS_decomposition/
│   │   │   └── {STATION}_neu/            (per-station dirs)
│   │   └── modeled/                     # from GPS_modeled/
│   │       └── {STATION}_model.csv       (59 files)
│   │
│   └── gwl/
│       ├── well_materials/              # from GroundwaterWells_MaterialAssign/
│       │   └── {WELL}.png + {WELL}.txt   (~117 pairs)
│       ├── well_info/                   # from gwl_inspection/
│       │   ├── gwl_allwells_flat.csv
│       │   ├── gwl_allwells_flat.xlsx
│       │   ├── well_info_combined.csv
│       │   ├── well_info_combined.xlsx
│       │   ├── well_info_combined.gpkg
│       │   └── well_info_deepseek/       (43 Markdown tables)
│       └── inspection_reports/          # JSON reports
│           ├── gwl_inspection_report.json
│           └── gwl_inspection_report_v1.json
│
├── results/                             # Analysis outputs (not raw data)
│   ├── direct_ratio/                    # from direct_ratio_MLCW_InSAR/
│   │   └── {STATION}/                    (39 dirs with .npy, .png, .csv, .json)
│   ├── direct_ratio_tuku/               # from direct_ratio_TUKU/ + _v2/
│   ├── arx/                             # from arx_method7/
│   │   ├── per_station/                 # {STATION}_arx_params.csv, _rmse.csv
│   │   ├── ablation/                    # Ablation study outputs
│   │   └── figures/                     # Per-station ARX figures
│   ├── prophet/                         # from prophet_tuku/
│   ├── gps_vs_mlcw/                     # from MLCW_GPS_figs/
│   │   ├── {STATION}_mlcw_gps.png        (39 files)
│   │   └── {STATION}_slope_ratio.json    (39 files)
│   ├── validation_summary/              # Top-level summary CSVs
│   │   ├── all_stations_validation_summary.csv
│   │   └── all_stations_validation_summary.json
│   └── stage2_output/                   # from scripts_2026_Apr_May/stage2_output/
│       ├── stage2_compaction_central.nc
│       ├── stage2_compaction_hi.nc
│       ├── stage2_compaction_lo.nc
│       ├── stage2_fbar_grid.nc
│       └── stage2_loocv_results.csv
│
├── figures/                             # Aggregated publication-quality figures
│   ├── gps_decomposition/               # from output_figs/GPS_dU_model_v*/
│   ├── mlcw_compaction/                 # from output_figs/MLCW_compaction_figs/
│   ├── mlcw_reconstruction/             # from output_figs/MLCW_reconstructed_*/
│   ├── mlcw_model_comparison/           # from output_figs/MLCW_orig_model_compare/
│   └── ratio/                           # from output_figs/ratio/
│
├── gis/                                 # Spatial data layers
│   ├── study_area/                      # from studyarea_SHP/
│   │   ├── gridpnt_crfp_500m_utm50.*
│   │   ├── GWL_unique_wells_2026.*
│   │   └── mlcw_station_utm50n.*
│   ├── velocity/                        # from GPS_data/ velocity layers
│   │   ├── GPS_avgvelocity_mmyr.shp
│   │   ├── GPS_avgvelocity_mmyr_TWD97.shp
│   │   ├── MLCW_avgvelocity_mmyr_TWD97.shp
│   │   └── MLCW_GPS_velocity_TWD97.shp
│   ├── alpha/                           # from GPS_data/ alpha layers
│   │   ├── alpha_insar_v2.*
│   │   └── alpha_comparison_all_stations_v2.gpkg
│   └── kriging/                         # Kriging layer files (.lyr)
│
├── presentation/                        # LaTeX Beamer slides
│   ├── dataset_overview.tex
│   ├── dataset_overview.pdf
│   ├── figures/                         # Figures embedded in slides
│   └── archive/                         # Older slide versions
│
├── docs/                                # Planning & design documents
│   └── superpowers/
│       ├── plans/
│       └── specs/
│
├── archive/                             # Deprecated or superseded versions
│   ├── mlcw_5m_regular_2015/            # Superseded by MLCW_5m_regular/
│   ├── v1_rar_snapshots/                # v1.rar, v2.rar, fix_old_colnames.rar
│   ├── direct_ratio_tuku_v1/            # Superseded by v2
│   └── output_figs_v1/                  # Older figure versions
│
└── .claude/                             # Claude Code config (keep as-is)
    └── settings.local.json
```

## Key Changes

| Current Location | Proposed Location | Rationale |
|---|---|---|
| 30 Python scripts at repo root | `scripts/01..08/` by pipeline stage | Single entry point for all code; stage numbers mirror data flow |
| `scripts_2026_Apr_May/` | `scripts/01_insar_preprocessing/` | The `A1→K2` naming already encodes order; move into shared scripts tree |
| `MLCW_timeseries/`, `MLCW_decomposition/`, etc. | `data/mlcw/{raw,decomposed,modeled,reconstructed,regular_5m}/` | All MLCW data under one parent; processing stage in subfolder name |
| `direct_ratio_MLCW_InSAR/` | `results/direct_ratio/` | This is an analysis output, not input data |
| `arx_method7/` | `results/arx/` | Same reasoning |
| `output_figs/` | `figures/` | Shorter name; subfolders distinguish content |
| `GPS_data/` + `studyarea_SHP/` | `gis/` | All spatial layers together |
| Top-level `.rar` files + `MLCW_5m_regular_2015/` | `archive/` | Old snapshots kept for reference but out of the way |

## Migration Order (least-disruptive first)

1. Create new directory skeleton (directories only, no file moves).
2. Move `archive/` candidates first — no scripts depend on them.
3. Move `figures/` and `presentation/` — no code references these paths.
4. Move `scripts/` — then update any hardcoded paths inside scripts.
5. Move `data/` and `results/` — update script paths accordingly.
6. Move `gis/` — update GIS layer source references.
7. Remove empty old directories.
