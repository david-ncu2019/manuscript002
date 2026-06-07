# TUKU τ (Tau) Demonstration

Self-contained folder showing how the hydraulic lag τ is calculated for TUKU station.

## What τ means physically

τ is the number of 5-day epochs by which a change in piezometric head leads
the resulting compaction in the aquitard. Thick clay layers drain slowly, so
their compaction lags behind the head change that triggered it.

## Files

| File | Purpose |
|------|---------|
| `data/` | Copied input data — only what is needed for TUKU |
| `01_run_tau_search.py` | Runs the τ grid search for all 6 layers; saves results |
| `02_plot_timeseries.py` | Produces all figures from the saved results |
| `results/tau_results.csv` | τ_opt per layer (after running script 01) |
| `results/tau_mse_curves.csv` | Full MSE curve (τ = 0…73) for each layer |
| `plots/tau_gwl_timeseries_{LAYER}.png` | 3-panel timeseries figure per layer |
| `plots/tau_mse_curves_all_layers.png` | 6-panel MSE curve summary |

## How to run

```powershell
cd D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2
$env:PYTHONPATH = ""; conda run -n fafalab python tau_demo_TUKU/01_run_tau_search.py
$env:PYTHONPATH = ""; conda run -n fafalab python tau_demo_TUKU/02_plot_timeseries.py
```

## What the plots show

**tau_gwl_timeseries_{LAYER}.png (3 panels):**
- Panel 1: Raw daily piezometric head. Blue background = elastic regime
  (head above h_c). Red background = inelastic (head below preconsolidation).
- Panel 2: Incremental GWL anomaly after removing the seasonal monthly mean.
  This is the exact signal the τ search operates on.
- Panel 3: Original anomaly (grey) vs the same signal shifted right by τ_opt
  epochs (coloured). The coloured curve is what the model says was driving
  compaction *now*. The shift is τ_opt × 5 days.

**tau_mse_curves_all_layers.png:**
- Shows the MSE at every candidate τ. The minimum is τ_opt.
- A genuine hydraulic lag shows a clear dip; a flat or monotone curve
  indicates weak GWL–compaction coupling at that layer.
