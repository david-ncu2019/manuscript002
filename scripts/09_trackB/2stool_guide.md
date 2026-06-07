# 2S-TOOL Execution Guide — GWL-Driven IHM-F (Raw Data + Monthly Sampling)

> **Python alternative available.** You can now run 2S-TOOL without MATLAB.
> See [Step 2b: Python 2S-TOOL](#step-2b-python-2stool-matlab-free) below.

## Overview

195 input files ready at: `data/gwl/2stool_inputs/2STOOL_{STATION}_{LAYER}.xlsx`

**Data pipeline (v2, corrected 2026-05-23):**
- **MLCW**: Raw ring-level cumulative displacement aggregated to layers using classification tables. Preserves seasonal elastic recovery (~29% of monthly steps show recovery, avg 2.5 mm vs only ~10% / 0.15 mm with reconstructed data).
- **GWL**: Head (masl) from monitoring wells converted to depth below surface.
- **Temporal alignment**: Both series resampled to first-of-month, merged on common dates.

Each file has a `StrainStress` sheet with:
- **Col B**: cumulative displacement (m), negative = subsidence, **oscillates with seasonal recovery**
- **Col C**: GWL depth from surface (m), positive downward

---

## Step 1: Data preparation (already done)

```bash
python scripts/09_trackB/prepare_2stool_inputs.py --all
```

195 files in `data/gwl/2stool_inputs/`. Point counts vary by station (37 to 263 monthly points).

---

## Step 2: MATLAB setup

### Step 2b: Python 2S-TOOL (MATLAB-free)

The MATLAB script has been translated to a modular Python package at
`/home/davidncu/2S-TOOL-Python/twostool_python/`. It produces identical
numerical results (verified to 17+ decimal places against MATLAB).

**Quick start — single file:**

```bash
conda activate isce_ncu3
python -m twostool_python data/gwl/2stool_inputs/2STOOL_TUKU_F3.xlsx \
    -o data/gwl/2stool_outputs/
```

**Batch — all 195 files:**

```bash
conda activate isce_ncu3
python scripts/09_trackB/batch_run_2stool.py
```

**Batch — single station:**

```bash
conda run -n isce_ncu3 python scripts/09_trackB/batch_run_2stool.py --station TUKU
```

**Output per file (6 files, all in `2stool_outputs/{basename}/`):**

| File | Format | Description |
|------|--------|-------------|
| `*_summary.json` | JSON | Single-object summary (S_kv, S_ke stats, params) |
| `*_loops.json` | JSON | Array of loop objects (NaN → null for cross-tool use) |
| `*_summary.csv` | CSV | Same summary, one row |
| `*_loops.csv` | CSV | Same loops, tabular |
| `*_sscurve.csv` | CSV | Full (x, y) stress-strain curve |
| `*_Fig02_skv_jva.png` | PNG | S_kv envelope plot |
| `*_Fig02_skv_jva_v2.png` | PNG | Peaks/troughs marked |
| `*_Fig03_ske_jva.png` | PNG | Elastic loops colored |

**Key differences from MATLAB:**

| MATLAB | Python |
|--------|--------|
| TIFF figures (LZW) | PNG figures (faster, browser-viewable) |
| Results written back to .xlsx | Output in separate subfolders, inputs untouched |
| `intervalo_y` = 20 m (dialog default) | Auto-computed as 5% of GWL range (~0.5 m for Taiwan) |
| `uigetfile` / `inputdlg` dialogs | CLI arguments + auto-parameters |
| No JSON output | JSON reports for cross-tool consumption |

**Parameters are auto-computed** from data and match the fixed MATLAB
(auto-parameters version). To override, edit `config.py` or populate the
`InputData` sheet in the input Excel file.

After processing, collect results with:

```bash
python scripts/09_trackB/collect_2stool_results.py
```

This reads JSON (preferred), CSV, or Excel — whichever is available.

## Step 2: MATLAB setup (original)

Open `A02_StressStrain_Ske_Skv_Part2.m` in MATLAB editor. Ensure:

```matlab
encadenado=0;   % standalone mode (no Part 1)
seleccion=0;    % hardcoded path (edit file/path per run)
```

Set `file` and `path` for each station you're processing. Output goes to `2stool_outputs/`.

---

## Step 3: Run TUKU pilot (6 files)

### Recommended order:

| Order | File | Layer | Disp range (m) | GWL depth range (m) | N pts | Why first |
|-------|------|-------|----------------|---------------------|-------|-----------|
| 1 | `2STOOL_TUKU_F3.xlsx` | F3 | -0.450 to -0.270 | 10.0–19.9 | 159 | Largest signal, clearest hysteresis |
| 2 | `2STOOL_TUKU_F2.xlsx` | F2 | ~ -0.228 to 0 | 10.4–22.8 | 159 | Second-largest |
| 3 | `2STOOL_TUKU_T2.xlsx` | T2 | ~ -0.021 to 0 | 10.4–22.6 | 159 | Moderate |
| 4 | `2STOOL_TUKU_F1.xlsx` | F1 | ~ -0.030 to 0 | 10.4–22.8 | 159 | Shallow |
| 5 | `2STOOL_TUKU_T1.xlsx` | T1 | ~ -0.018 to 0 | 10.4–22.8 | 159 | Small signal |
| 6 | `2STOOL_TUKU_F4.xlsx` | F4 | ~ -0.042 to 0 | 10.0–20.0 | 159 | Deepest |

### Dialog parameters (updated):

| Parameter | TUKU F3 | Notes |
|-----------|---------|-------|
| Y-axis interval | **5 m** | Min GWL depth change for loop detection |
| X-axis interval | **0.005 m** (5 mm) | Min displacement change. With 29% recovery steps at avg 2.5 mm, start small to catch loops |
| Preconsolidation depth (h_c) | **12 m** | Approximate GWL depth where inelastic begins |
| % max amplitude | **0.2** | Filter small loops. Lower to 0.1 if too few accepted |

### For each file:
1. Edit `file='2STOOL_TUKU_F3.xlsx'` in the MATLAB script
2. Run `A02_StressStrain_Ske_Skv_Part2.m`
3. Enter the 4 parameters when the dialog appears
4. MATLAB generates Figures 2 (S_kv fit) and 3 (elastic loops)
5. Results auto-save to the "Results" sheet in the same file (in `2stool_outputs/`)

---

## Step 4: Interpreting results

### S_kv (raw Δb/Δh ratio for the layer)

S_kv = 0.086 for TUKU F3 means: 86 mm compaction per 1 m GWL decline.

For **specific storage** (per meter of layer thickness):
```
S_skv = S_kv / layer_thickness
```
TUKU F3 is ~100 m thick → S_skv ≈ 8.6×10⁻⁴ m⁻¹ (within typical 10⁻⁴ to 10⁻² for alluvium).

### S_ke (elastic storage coefficient)

- Expected: 1–10% of S_skv
- Use **weighted S_ke** as primary (weighted by loop amplitude)
- With corrected data, expect more accepted elastic loops than the previous run (which had only 2/5)

### Figure interpretation

- **Figure 2**: Black dashed line = global S_kv fit through all points
- **Figure 3**: Colored segments = elastic recovery cycles. Black dashed = accepted, Red dashed = discarded

---

## Step 5: Adjusting parameters for problematic curves

| Symptom | Fix |
|---------|-----|
| No elastic loops found | Decrease **Y-axis interval** (5 → 2 m) and/or **X-axis interval** (0.005 → 0.002 m) |
| Too many tiny loops, many rejected | Increase **% max amplitude** (0.2 → 0.4) |
| Many negative S_ke loops | Decrease **X-axis interval** to catch smaller genuine loops |
| S_kv fit looks wrong | Verify displacement values are negative (subsidence) |

---

## Step 6: Edit A02 — separate I/O directories + CSV exports (one-time MATLAB edit)

Edit `/home/davidncu/2S-TOOL/A02_StressStrain_Ske_Skv_Part2.m`. Four changes in order.

### 6a — Add `outPath` immediately after the `readmatrix` line (~line 24)

Find:
```matlab
datos=readmatrix([path file],'Sheet','StrainStress','Range','B2');
```
Insert immediately after:
```matlab
% ── Separate input and output directories ──────────────────────────────
outPath = '/home/davidncu/2S-TOOL/2stool_outputs/';
if ~exist(outPath, 'dir')
    mkdir(outPath);
end
% Copy input file to output dir so Results sheet writes land there
copyfile([path file], [outPath file]);
```

### 6b — Redirect all three figure saves to `outPath`

Replace each occurrence (search for `[path file`):

| Find | Replace with |
|------|-------------|
| `linea=[path file(1:end-5) '_Fig02_skv_jva.tif'];` | `linea=[outPath file(1:end-5) '_Fig02_skv_jva.tif'];` |
| `linea=[path file(1:end-5) '_Fig02_skv_jva_v2.tif'];` | `linea=[outPath file(1:end-5) '_Fig02_skv_jva_v2.tif'];` |
| `linea=[path file(1:end-5) '_Fig03_ske_jva.tif'];` | `linea=[outPath file(1:end-5) '_Fig03_ske_jva.tif'];` |

### 6c — Redirect the three Excel `writematrix` calls to `outPath`

| Find | Replace with |
|------|-------------|
| `writematrix(temp,[path file],'Sheet','Results','Range','A3');` | `writematrix(temp,[outPath file],'Sheet','Results','Range','A3');` |
| `writematrix(temp,[path file],'Sheet','Results','Range','F10');` | `writematrix(temp,[outPath file],'Sheet','Results','Range','F10');` |
| `writematrix(temp,[path file],'Sheet','Results','Range','F3');` | `writematrix(temp,[outPath file],'Sheet','Results','Range','F3');` |

### 6d — Add CSV export block immediately before `disp ('The end of part 2');`

```matlab
%% EXPORT MACHINE-READABLE CSV FILES
disp('Writing CSV reports...')

% --- sscurve.csv: full stress-strain curve ---
sscurve_table = table((1:length(x1))', x1, y1, ...
    'VariableNames', {'index', 'disp_m', 'gwl_depth_m'});
writetable(sscurve_table, [outPath file(1:end-5) '_sscurve.csv']);

% --- loops.csv: one row per identified elastic loop ---
n_loops_total = size(AjusTramElas, 1);
loops_table = table((1:n_loops_total)', ...
    AjusTramElas(:,1), AjusTramElas(:,2), ...
    AjusTramElas(:,3), AjusTramElas(:,4), ...
    AjusTramElas(:,5), AjusTramElas(:,6), ...
    AjusTramElas(:,7), AjusTramElas(:,8), ...
    AjusTramElas(:,9), AjusTramElas(:,10), AjusTramElas(:,11), ...
    tramoselasticos(:,1), tramoselasticos(:,2), ...
    'VariableNames', {'loop_id', 'slope', 'intercept', ...
        'x_start', 'x_end', 'y_fit_start', 'y_fit_end', ...
        'delta_x_m', 'delta_y_m', 'n_pts', 'accepted', 's_ke', ...
        'start_idx', 'end_idx'});
writetable(loops_table, [outPath file(1:end-5) '_loops.csv']);

% --- summary.csv: one-row run summary ---
n_loops_accepted = sum(AjusTramElas(:,10));
if n_loops_accepted > 0
    ske_max_val = max(ske_aceptados);
    ske_min_val = min(ske_aceptados);
    ske_std_val = ske_std;
else
    ske_max_val = NaN;
    ske_min_val = NaN;
    ske_std_val = NaN;
end
summary_table = table({file}, skv, ske_max_val, ske_mean, ske_min_val, ...
    ske_ponderado, ske_std_val, n_loops_total, n_loops_accepted, ...
    intervalo_y, intervalo_x, hp_inicial, porcentaje, ...
    'VariableNames', {'file', 'skv', 'ske_max', 'ske_mean', 'ske_min', ...
        'ske_weighted', 'ske_std', 'n_loops_total', 'n_loops_accepted', ...
        'y_interval', 'x_interval', 'hc', 'pct_amplitude'});
writetable(summary_table, [outPath file(1:end-5) '_summary.csv']);

disp('CSV reports written.')
```

### Output files per run

| File | Rows | Key columns | Use |
|------|------|-------------|-----|
| `2STOOL_{ST}_{LY}.xlsx` (copy) | — | Results sheet | Input kept clean; Results written to this copy |
| `_Fig02_skv_jva.tif` | — | — | S_kv global fit (visual QC) |
| `_Fig03_ske_jva.tif` | — | — | Elastic loops (visual QC) |
| `_sscurve.csv` | N monthly pts | `index`, `disp_m`, `gwl_depth_m` | Verify S_kv in Python, recreate figures |
| `_loops.csv` | 1 per elastic loop | `loop_id`, `s_ke`, `accepted`, `delta_y_m` | Diagnose rejections, cross-station comparison |
| `_summary.csv` | 1 | `skv`, `ske_mean`, `ske_weighted`, `n_loops_accepted` | Aggregation via `collect_2stool_results.py` |

Note: `y_fit_start`/`y_fit_end` in `_loops.csv` are the fitted-line predicted values at loop boundaries, not raw GWL bounds. Use `delta_y_m` for the actual GWL depth amplitude.

---

## Step 7: Full batch

After TUKU pilot confirms the pipeline, run the remaining 189 files. Collect results with:

```bash
python scripts/09_trackB/collect_2stool_results.py
```

`collect_2stool_results.py` reads `_summary.csv` (fast path) when available, falling back to the Excel Results sheet for any files processed before the MATLAB edit. It also merges all `_loops.csv` files into `data/gwl/2stool_outputs/2stool_loops_all.csv`.

---

## Appendix A: Diff-space variant (`prepare_2stool_inputs_diff.py`)

### What it does differently

`prepare_2stool_inputs.py` writes **cumulative** displacement and **absolute** GWL depth — the standard 2S-TOOL input that builds a stress-strain trajectory over time.

`prepare_2stool_inputs_diff.py` writes **epoch-to-epoch first-differences** instead:

| Column | Cumulative script | Diff script |
|--------|-------------------|-------------|
| Col B (`StrainStress`) | Cumulative displacement (m) | Δ displacement = disp(t) − disp(t−1) (m) |
| Col C (`StrainStress`) | GWL depth from surface (m) | Δ GWL depth = depth(t) − depth(t−1) (m) |

Sign conventions in diff-space:
- **Positive Δdisp** = rebound / elastic recovery
- **Negative Δdisp** = subsidence (more compaction this month)
- **Positive Δdepth** = GWL declined (more stress on aquifer skeleton)
- **Negative Δdepth** = GWL recovered (stress relieved)

In a well-behaved confined aquifer, most monthly steps should plot in the
second quadrant (Δdepth > 0, Δdisp < 0: drawdown → subsidence) or fourth
quadrant (Δdepth < 0, Δdisp > 0: recovery → uplift). Inelastic behaviour
shows as third-quadrant points (recovery → continued subsidence).

### Why this variant was created

The cumulative stress-strain curve shows a monotonically declining displacement
trend at TUKU F3 (~165 mm total over 159 months). Elastic recovery episodes
(2–3 mm) are visible only as slight "pauses" in the cumulative plot, making it
hard to visually verify the physical relationship. The diff-space scatter makes
the epoch-level relationship explicit and is easier to inspect for sign errors
or data alignment problems.

**Critical limitation — do not run these files in 2S-TOOL MATLAB:**

The stress-strain curve is defined in the hydrogeology literature as **cumulative
compaction (strain) plotted against absolute piezometric head (stress)**
(Navarro-Hernández et al. 2025; confirmed by EGU 2024 abstract). Elastic loops
appear as geometric reversals in the cumulative trajectory. 2S-TOOL's
loop-detection algorithm detects these reversals — it cannot interpret
first-differences, where a "loop" would appear only as a sign change, not a
trajectory reversal. Furthermore:

- The pre-consolidation head `h_c` (historical stress maximum) cannot be
  identified from a series of signed differences — stress history requires the
  cumulative head record.
- The fitted slope from a diff-space run gives the epoch-by-epoch instantaneous
  storage ratio, not the long-run skeletal S_kv that MATLAB's linear fit
  extracts from the full cumulative trajectory.

**Use the diff inputs only in Python for visual QC** (scatter plot of ΔGWL_depth
vs Δdisp to verify sign agreement). The cumulative inputs (`2stool_inputs/`)
are the sole production inputs for MATLAB.

### Output directory

```
data/gwl/2stool_inputs_diff/2STOOL_{STATION}_{LAYER}.xlsx
data/gwl/2stool_inputs_diff/preparation_log_diff.csv
```

Separate from the cumulative inputs (`data/gwl/2stool_inputs/`) so MATLAB
runs can target either set without confusion.

### Running the script

```bash
# TUKU pilot only (default)
$env:PYTHONPATH = ""; conda run -n fafalab python scripts/09_trackB/prepare_2stool_inputs_diff.py

# Specific stations
$env:PYTHONPATH = ""; conda run -n fafalab python scripts/09_trackB/prepare_2stool_inputs_diff.py --stations TUKU,CHLIN

# All stations
$env:PYTHONPATH = ""; conda run -n fafalab python scripts/09_trackB/prepare_2stool_inputs_diff.py --all
```

Note: `$env:PYTHONPATH = ""` clears the gemini_env contamination that would
otherwise load the wrong numpy. Required whenever running from a shell where
the gemini environment is active.

### MATLAB parameter guidance for diff-space runs

The MATLAB dialog parameters need adjustment for diff-space data:

| Parameter | Cumulative run | Diff-space run | Why |
|-----------|---------------|----------------|-----|
| Y-axis interval | 5 m (absolute GWL depth range) | 0.5–1.0 m (monthly Δ range) | Monthly GWL changes are much smaller than the cumulative excursion |
| X-axis interval | 0.005 m | 0.001–0.002 m | Monthly Δdisp events are ~1–3 mm |
| Preconsolidation depth (h_c) | 12 m | ~0 m (or skip) | In diff-space, "exceeding h_c" has no direct analogue |
| % max amplitude | 0.2 | 0.2–0.3 | Similar |

The diff-space run output files (`_summary.csv`, `_loops.csv`) should be saved
to a separate output directory (e.g., `data/gwl/2stool_outputs_diff/`) to
avoid overwriting production results.

### Interpreting diff-space results

A clean diff-space scatter (second + fourth quadrants dominant) confirms that:
1. The GWL well is appropriately assigned to this MLCW layer
2. The head-to-depth conversion (well elevation − piezometric head) is correct
3. The monthly temporal alignment is working

If third-quadrant points dominate (GWL recovery → continued subsidence), this
indicates either (a) strong inelastic behaviour where stress history locks in
further compaction after drawdown events, or (b) a lag between head change and
deformation response that exceeds one month.

---

## TUKU reference data

| Layer | Displacement (m) | GWL depth (m) | Wellcode | Well elev (m) | Ring depths (m) |
|-------|------------------|---------------|----------|---------------|-----------------|
| F1 | ~ -0.030 to 0 | 10.4–22.8 | 09050321 | 17.30 | 8.8, 11.9, 25.6 |
| T1 | ~ -0.018 to 0 | 10.4–22.8 | 09050321 | 17.30 | 41.6 |
| F2 | ~ -0.228 to 0 | 10.4–22.8 | 09050321 | 17.30 | 50.3–122.8 |
| T2 | ~ -0.021 to 0 | 10.4–22.6 | 09050331 | 17.25 | 156.6, 161.9 |
| F3 | -0.450 to -0.270 | 10.0–19.9 | 09050341 | 17.21 | 172.9–272.7 |
| F4 | ~ -0.042 to 0 | 10.0–20.0 | 09050341 | 17.21 | 283.4–300.0 |
