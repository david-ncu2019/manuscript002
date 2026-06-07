# MLCW Inspector — Interactive Data Dashboard (hvPlot / Panel / Bokeh)

Interactive [Panel](https://panel.holoviz.org) dashboard for inspecting MLCW
compaction and GWL head time series at 37 monitoring stations in the
Choushui River Alluvial Fan.  Uses HoloViews Bokeh as the plotting backend
(replaces the earlier matplotlib version).

## What it shows

Three tabbed panels, one visible at a time:

- **Tab "MLCW Compaction" (~470 px):** Cumulative MLCW compaction (mm).
  Two view modes:
  - **Layers:** 5 aggregated lines (F1, F2, T2, F3, F4).
  - **Rings:** Individual magnetic-ring lines, coloured by layer assignment.
- **Tab "Groundwater Level" (~220 px):** Groundwater level head (m MSL)
  from the assigned monitoring well for each layer.
- **Tab "InSAR Displacement" (~150 px):** InSAR surface displacement (mm)
  at the station location.

Switch between tabs by clicking the tab headers above the plot. The sidebar
checkboxes and toolbar remain visible and active regardless of which tab is
selected.

## Run command

```bash
PYTHONPATH="" conda run -n isce_ncu3 python -m mlcw_inspector
```

Opens in your browser and starts a local Bokeh server (threaded).  Refresh
the page if the window does not appear automatically.

## How to use

1. **Select a station** from the dropdown — typing filters the list.
2. **Toggle Layers / Rings** with the radio button.
3. **Show / hide individual layers** by checking or unchecking boxes in the
   left sidebar.  MLCW and GWL visibility are independent.
4. **Pan, zoom, reset** with the Bokeh toolbar that appears on hover above
   each plot.
5. Close the browser tab and press Ctrl+C in the terminal to stop.

## Data sources

| Data | Path |
|------|------|
| MLCW layers (reconst) | `data/mlcw/group_byLayer_reconstr/{STATION}_reconst_grouped.csv` |
| MLCW rings (raw) | `data/mlcw/raw_timeseries/{STATION}_ringbyring.csv` |
| Ring-to-layer mapping | `data/mlcw/group_byLayer_reconstr/{STATION}_classify_table.csv` |
| GWL assignment | `data/gwl/gwl_to_mlcw_layer_assignment_v3.csv` |
| GWL timeseries | `data/gwl/well_timeseries/{STEM}_gwl_timeseries.feather` |
| InSAR displacement | `data/insar/InSAR_measures_at_MLCW.csv` |
| Config | `data/ihmf_config.json` |

## Environment

- Conda env: `isce_ncu3` (Python 3.10, hvplot 0.12.2, Panel 1.8.2,
  HoloViews 1.21.0, Bokeh 3.6.2, pandas, numpy, pyarrow)
- Rendering backend: Bokeh (in-browser interactive plots)
- Run via: `python -m mlcw_inspector` or import `MLCWInspector` in a script

## Files

| File | Role |
|------|------|
| `__init__.py` | Package marker — exports `MLCWInspector`, `DataLoader`, `DataMapper` |
| `__main__.py` | Entry point for `python -m mlcw_inspector` |
| `dashboard.py` | `MLCWInspector` class — widgets, reactive bindings, plot builders |
| `data_loader.py` | `DataLoader` — all file I/O, caching, wellcode zero-padding |
| `data_mapper.py` | `DataMapper` — station→layer→wellcode resolution, ring→layer mapping |
| `plot_styles.py` | Color palette and styling constants for Bokeh/HoloViews |

## Previous version

The earlier matplotlib-based implementation (`orchestrator.py`, `widgets.py`,
`panel_*.py`, `plot_rc.py`) has been removed after migrating to hvPlot/Panel.
