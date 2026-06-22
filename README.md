# 012_ml_nowcast — At-Well ML Nowcasting of Per-Section Compaction

> **See also:** [CLAUDE.md](../../CLAUDE.md) (folder rules · hub) · [GEMINI.md](../../GEMINI.md) (physics, sign conventions, rank-1 constraint) · [AGENTS.md](../../AGENTS.md) (runtime)

## Purpose

Predict each depth-section's **monthly incremental compaction** from that section's own
drivers (groundwater head + lags) plus the **shared surface signal** (GPS) and
rainfall/seasonal/static-geology features. Pooled **(section × month)** regression with
**Bayesian Ridge** + **split-conformal 90% intervals**.

This is **at-well nowcasting**: features at month *t* → compaction at month *t*. It is
**NOT** forecasting, and **NOT** a per-layer decomposition of the surface signal.

> ⚠️ **Rank-1 disclaimer.** The surface carrier is rank-1 (one shared DOF for six layers;
> SVD SV2–6 < 4e-13, see GEMINI.md). A model **cannot** uniquely attribute the surface
> signal to individual layers (amplitude-bound lemma: F2 seasonal 4.71 mm > surface
> 3.83 mm). Per-section predictions here are nowcasts driven by each section's *own*
> groundwater head — not a surface decomposition.

## Pilot

TUKU well only (v1). Uniform **50 m depth bands S1–S6** (S1 0–50 m … S6 250–300 m).

## Run order (scripts numbered by sequence)

```powershell
# 01 + 02 already ran — they produced input_data/TUKU_section_materials.csv
# 03: assemble the pooled feature table for a trial (default run_001 = baseline)
$env:PYTHONPATH=""; conda run -n fafalab2 python scripts/03_build_feature_table.py --run run_001
# 05: train + evaluate (imports 04_conformal.py)
$env:PYTHONPATH=""; conda run -n fafalab2 python scripts/05_train_nowcast.py --run run_001
# 06/07: input + result figures for that run
$env:PYTHONPATH=""; conda run -n fafalab2 python scripts/06_plot_inputs.py --run run_001
$env:PYTHONPATH=""; conda run -n fafalab2 python scripts/07_plot_results.py --run run_001
```

| # | Script | Role |
|---|--------|------|
| 01 | `01_resample_borehole_0.1m.py` | borehole xlsx → 0.1 m soil log (`raw_data/TUKU_borehole_0.1m.csv`) |
| 02 | `02_compute_section_materials.py` | 0.1 m log → per-section materials (`input_data/TUKU_section_materials.csv`) |
| 03 | `03_build_feature_table.py` | raw monthly CSVs → pooled long feature table (`results/feature_table.csv`) |
| 04 | `04_conformal.py` | dependency-free split-conformal helper (imported by 05; MAPIE not installed) |
| 05 | `05_train_nowcast.py` | split → scale → Bayesian Ridge → conformal → metrics + figures |

## Modeling span & split

Overlap of all inputs (MLCW + GPS + 5 GWL wells + rainfall): **2012-08 → 2023-02** (rainfall ends 2023-02).
Temporal split (never random): **train 2012-08–2018-12 · val/calib 2019–2020 · test 2021–2023-02.**

## Section → GWL well (v4 depth overlap)

From `001_data/gwl/gwl_to_mlcw_layer_assignment_v4.csv` (TUKU rows), mapped onto the 50 m bands by depth:

| Section | Depth (m) | v4 layer(s) | Well | Code |
|---------|-----------|-------------|------|------|
| S1 | 0–50 | F1, T1 | HONGLUN | 09050111 |
| S2 | 50–100 | F2 | TUKU | 09050321 |
| S3 | 100–150 | F2 | TUKU | 09050321 |
| S4 | 150–200 | T2, F3 | LUNZI | 09170121 |
| S5 | 200–250 | F3 | TUKU | 09050331 |
| S6 | 250–300 | F3, F4 | LIUZHUANG | 09080251 |

**Notes / caveats:**
- **GWL head is m MSL — never negated.** LUNZI (S4) head is legitimately negative.
- **S2/S3 share** the F2 well 09050321; **S4** = T2 driver LUNZI (deep-clay mass below the screen has no piezometer — a known driver-quality limit, expect weaker S4 skill).
- MLCW source resampled with `.last()` on the cumulative series (correct for cumulative).

## Trials (multi-run structure)

Each experiment is a self-contained **`trials/run_NNN/`** folder holding its own `results/` + `figures/` + a `config.json` recording exactly what it used. No more top-level `results/`/`figures/`.

```
trials/
├── run_001/              # v1 baseline (v4 driver assignment)
│   ├── config.json       # driver map, span, lags, split, model, alpha
│   ├── results/          # feature_table.csv, *_meta.json, nowcast_metrics.json, nowcast_predictions.csv
│   └── figures/          # the 8 PNGs
├── run_002/              # 09050341 deep co-located driver for S5+S6 (config only — not yet run)
│   └── config.json
└── trials_index.csv      # one row per run: pooled R², per-section R², coverage
```

- **Run a trial:** `... python scripts/03_build_feature_table.py --run run_002` then `05`, `06`, `07` with the same `--run`. Scripts read `trials/<run>/config.json` (falling back to the v1 baseline for any unset key) and write everything under that run's folder.
- **Define a new trial:** create `trials/run_NNN/config.json` overriding any of: `section_well`, `span`, `gwl_lags`, `ds_lags`, `rain_windows`, `split`, `model`, `alpha`, `label`. Shared machinery: `scripts/trial_config.py`.
- **Compare runs:** `trials_index.csv` (auto-appended by `05`).

## Outputs (per run)

`trials/<run>/results/`: `feature_table.csv`, `feature_table_meta.json`, `nowcast_metrics.json`, `nowcast_predictions.csv`, `config.json`.
`trials/<run>/figures/`: `input_dashboard.png`, `driver_response_scatter.png`, `skill_summary.png`, `obs_vs_pred_scatter.png`, `feature_coefficients.png`, `pred_vs_actual_by_section.png`, `coverage.png`, `residuals.png`.

## Deferred to v2

ElasticNet comparison; rainfall ablation; MLCW `.last()` source-regeneration audit; Stage-2 multi-well / Stage-3 grid extension; real MAPIE if a heavier conformal scheme is wanted.
