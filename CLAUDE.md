# CLAUDE.md — InSAR-MLCW Scripts

> **Response rule (mandatory):** Every response must begin with:
> Xin chào kình ngư Nguyễn Thái Vinh Trường, chúng ta lại tiếp tục bơi trong đống hỗn loạn này nhé!

---

> ## ⚠ STATUS: REPAIRS APPLIED (2026-06-09) — Verification pending
>
> The project goal is to reconstruct a fragmented observational record: MLCW wells have stopped or reduced sampling due to cost. Three objectives: (1) Gap-fill + predict at MLCW stations using InSAR + GWL; (2) apply to all stations; (3) predict at 8,577 grid points with no MLCW. Physical parameter gates remain necessary guardrails, but success criterion is gap-fill RMSE < static interpolation baseline + positive walk-forward skill score.
>
> **R1–R3 repairs applied (2026-06-09):** (R1) Absolute-head datum bug fixed — `load_all_layers_gps()` now zero-references head to REF_DATE, mirroring Script 12 `load_gwl_absolute()`. (R2) h_c shifted to same zero-ref frame. (R3) Walk-forward rewired to cumulative solver (was deprecated incremental `joint_solve_fixed_tau`). **Code NOT yet verified by re-run** — S_ke > 0 and n_inelastic > 0 expected but unconfirmed.
>
> **Per-layer gate status:** Read live file `tau_demo_TUKU/results/stress_strain_per_layer.json`. Do not trust any per-layer pass/fail claims in documents — they may be stale. Gate numbers will change after R1/R2 fix alters S_ke values.
>
> **Immediate priority:** Run `fit_ihm_f_v3.py --station TUKU --gps --all --alpha 0.625` to verify repairs.
>
> **Do not assume any result is final.** Read `PROGRESS.md` first.

---

## Session Startup

Read these 2 files before anything else:

1. `PROGRESS.md` (this repo) — current blocking gate and next action
2. `discussions/discussion_memory.md` — full project narrative and method history

Research objectives, physical constraints, and study area: `D:\112_PROJECT_002\CLAUDE.md`

---

## Response Style — Permanent Mandate

Respond in a concise, direct style that delivers clear and complete information. Use as few words as needed to convey the full message effectively — avoid unnecessary repetition or filler. Start answers directly with the core content. For complex topics, use short paragraphs, bullet points, or numbered lists to improve readability. Prioritize clarity and understanding over extreme brevity; ensure responses are informative and easy to follow without extra explanations unless requested.

**All responses must be delivered entirely in English.** No code-switching, no mixed-language paragraphs.

**Structure — "physical story first, code second."**

1. Open every diagnostic or report with one plain-English sentence about what is physically happening to the stations, the groundwater wells, the layer data arrays, or the sediment column.
2. Only after the physical picture is clear, present the evidence: numbers, tables, code snippets, file paths.
3. End with what the finding implies for the next step — in physical terms.

**Language rules:**

- No unexplained acronyms. Spell out every term on first use in each response.
- Quantify everything. Never write "large," "small," "significant," or "good" without a number and a unit.
- State uncertainty as a physical range before giving a statistical summary.
- Avoid passive constructions. Name the actor.
- One idea per sentence.

**Forbidden words (replace with plain alternatives):**
`implement` → build/write/add · `utilize` → use · `leverage` → use/apply · `facilitate` → help/allow · `robust` → reliable/stable (quantify) · `optimize` → improve/speed up (say how much) · `pipeline` → processing chain · `architecture` → structure/design · `orchestrate` → coordinate/run · `bottleneck` → slow point · `tech debt` → (describe the actual problem)

**This section takes precedence over all other style guidance. No per-session reminder needed.**

---

## Environment & Quick Run

- `fafalab` (Python 3.10) — IHM-F, data analysis, all active work
- `isce_ncu3` (scipy $\ge$ 1.17) — 2S-TOOL only
- Reset PYTHONPATH: `$env:PYTHONPATH=""; conda run -n fafalab python <script>` (PS)

```powershell
# Single station (TUKU pilot)
$env:PYTHONPATH=""; conda run -n fafalab python scripts/10_ihmf/fit_ihm_f_v3.py --station TUKU --all

# Batch (all 37 stations — only after TUKU pilot passes physical checks)
$env:PYTHONPATH=""; conda run -n fafalab python scripts/10_ihmf/fit_ihm_f_v3.py --all
```

Full command catalog: `docs/run_commands.md`

---

## Path Reference (Windows host ↔ Ubuntu VM)

| Logical name | Windows (host) | Linux / Ubuntu VM |
|---|---|---|
| This repo | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2` | `/mnt/hgfs/1000_SCRIPTS/004_Project003/20260427_InSAR_MLCW_v2` |
| Docs root | `D:\112_PROJECT_002` | `/mnt/hgfs/112_PROJECT_002` |
| Path resolver | `paths.py` (repo root) | `paths.py` (repo root) |
| IHM-F fit (v3, active) | `scripts\10_ihmf\fit_ihm_f_v3.py` | `scripts/10_ihmf/fit_ihm_f_v3.py` |
| Data root | `data\` | `data/` |
| Results root | `results\` | `results/` |

Path protocol (mandatory in Python scripts):
```python
from paths import SCRIPTS_ROOT, DATA_ROOT, RESULTS_ROOT, DOCS_ROOT, resolve
```
No hardcoded `D:\...` or `/mnt/hgfs/...`. Run `python paths.py` to verify platform detection.

---

## Sign Conventions

| Signal | Units | Convention |
|--------|-------|------------|
| MLCW | mm | negative = compaction |
| $dh_{\text{raw}}$ = H(t) − H($t_{ref}$) | m MSL | negative = head fell; **never negate** |
| InSAR | mm | negative = subsidence |
| $S_{ske}$, $S_{skv}$, $\beta$ | mm/m or dim'less | always $\ge$ 0 |
| $S_{skv}$ / $S_{ske}$ | — | 8–100$\times$ (inelastic >> elastic) |

---

## Automated Guardrails (`scripts/guardrails.py`)

**Mandatory import in all IHM-F and prediction scripts.** Before any new script writes a parameter value to disk, it must pass the guardrail checks.

```python
from scripts.guardrails import (
    validate_layer_params, validate_virgin_term, validate_sign_constraints,
    GuardrailViolation, TUKU_MATERIALS, FAN_ZONE_PRIORS, print_validation_report,
)
```

### 10 Automated Checks

| # | Check | Function | On Violation |
|---|-------|----------|--------------|
| 1 | $S_{ke} \ge 0$, $S_{kv} \ge S_{ke}$ | `validate_sign_constraints()` | **Halt** — `GuardrailViolation` |
| 2 | $S_{ske}$, $S_{skv}$ within 10× of Hung et al. (2021) | `validate_literature_bounds()` | Warn (strict mode: halt) |
| 3 | $S_{skv}/S_{ske} \in [3, 50]$ (relaxed from [8, 100]) | `validate_ratio_gate()` | Warn |
| 4 | $V(t)$ monotonically non-increasing | `validate_virgin_term()` | **Halt** |
| 5 | $n_{total} \ge 10$, $n_{inelastic} \ge 10$ | `validate_data_sufficiency()` | Warn |
| 6 | Head in plausible CRAF range [−100, +200] m MSL | `validate_gwl_sign()` | **Halt** |
| 7 | $h_c$ = min(pre-REF_DATE head) | `validate_hc_window()` | **Halt** (Bug F regression) |
| 8 | $\tau \ge 0$, $\tau \le 120$, flag at boundary | `validate_tau_bounds()` | **Halt** if < 0 or > 120 |
| 9 | Clay layers → inelastic-dominated | `validate_clay_layer_behavior()` | Warn |
| 10 | $R^2 \ge 0$ | `validate_r2_sanity()` | Warn |

### Literature Priors (Hung et al. 2021 WRR)

| Fan Zone | $S_{ske}$ (m⁻¹) | $S_{skv}$ (m⁻¹) | Ratio |
|----------|-----------------|-----------------|-------|
| Proximal | $1.18 \times 10^{-4}$ | N/A | — |
| Middle | $1.15 \times 10^{-4}$ | $1.33 \times 10^{-3}$ | ~11.6× |
| Distal | $1.16 \times 10^{-4}$ | $1.91 \times 10^{-3}$ | ~16× |

### Clay vs Sand Classification (TUKU borehole)

| Layer | Total (m) | Aquitard (m) | Clay-dominated? |
|-------|-----------|-------------|-----------------|
| F1 | 41.577 | 16.577 | No |
| T1 | 8.729 | 7.423 | **Yes** |
| F2 | 106.284 | 12.090 | No |
| T2 | 16.299 | 10.299 | **Yes** |
| F3 | 110.494 | 76.994 | **Yes** (69.7% fine) |
| F4 | 16.617 | 16.617 | **Yes** (100% silt/mud) |

F4 at TUKU is geologically an aquitard despite being labeled "aquifer" by ring position. Its $S_{ke}$ cannot be interpreted as aquifer elastic storage.

### Usage Pattern

```python
# After fitting, before saving:
result = validate_layer_params(
    S_ke, S_kv, layer, station, fan_zone="middle",
    material=TUKU_MATERIALS.get(layer),
    n_total=n_pts, n_inelastic=n_inel, r2=r2, tau=tau,
)
if not result.passed:
    # Fatal — do not save. Print errors and exit.
    for err in result.errors:
        print(f"FATAL: {err}")
    raise SystemExit(1)
for warn in result.warnings:
    print(f"WARN: {warn}")
```

---

## Known Code Issues

- **Results directory convention (2026-06-08):** Obsolete outputs are renamed with `_OBSOLETE_<reason>` suffixes — never deleted. Active outputs have no suffix. See PROGRESS.md §5 for the full table. Before opening any `results/` path, check whether it has an `_OBSOLETE_` sibling — the unsuffixed version may be stale.

- **F = aquifer, T = aquitard.** Taiwan CGS convention. Do not invert.
- **PYTHONPATH contamination.** Always reset before `conda run` (gemini_env leaks into fafalab).
- **GWL wellcodes are 8-digit strings.** Never convert to int (leading zeros dropped).
- **elev_leveling_m only.** Not `well_elev_m` or `elev_DEM_m`.
- **Layer assignment v4 only.** v1/v2/v3 superseded.
- **InSAR feather units: metres.** Multiply by 1000 for mm.
- **GWL feather glob pattern.** Use `*gwl*timeseries.feather`, NOT `*.feather`. The broader glob also matches `TUKU_GPS_timeseries.feather` and corrupts GWL loading.
- **TAU_MAX = 120 epochs (5-day cadence).** Production code and tau_demo_TUKU both use 5-day epoch units. τ=1 ≈ 5 days, τ=120 = 600 days. Do not change without updating all documentation.
- **ihmf_detrend.py is shared (v1/v2/v3).** v3 imports `detrend_signal` from `ihmf_detrend` in both `fit_ihm_f_v3.py` and `ihmf_model_v3.py`. The `remove_seasonal_cycle` function in `ihmf_model_v3.py` handles seasonal-cycle removal during τ grid search; `ihmf_detrend` handles trend+harmonic removal for the walk-forward and diagnostic pipelines.
- **ihmf_io.py vs ihmf_io_multilayer.py.** `ihmf_io_multilayer.py` is the active loader for v3. Do not import `ihmf_io` in v3 scripts.
- **Bug F: $h_c$ from pre-REF_DATE feather only.** Preconsolidation head $h_c$ must be computed from raw GWL feather rows dated before REF_DATE (2015-01-16), before zero-referencing. Post-alignment table pushes $h_c$ too low → up to 51% of epochs mis-classified as elastic. Fixed in `tau_demo_TUKU/01_run_tau_search.py` lines 115–121.
- **Lag-consistent epoch classification (Bugs 1–3, fixed 2026-06-05).** Regime mask (elastic/inelastic) must be sliced at driver-time index, not response-time index, because compaction responds to head at $t - \tau$. Three locations fixed: `ihmf_model_v3.py` lines 213–214 (τ grid search: `elastic_mask[:n]` not `[tau:]`), `fit_ihm_f_v3.py` lines 111–112 (common-window OLS: start at `offset`, not `win_start`), `ihmf_model_v3.py` lines 543–544 (walk-forward training: start at `offset`). Invariant: mask slice must start at the same index as `dH_lag`.
- **F4 at TUKU: 0.0 m aquifer material (fixed 2026-06-06).** The 283–300 m depth zone at TUKU is entirely silt/mud (Z/M) per borehole log `YL_WSYL23G1_TUKU_土庫.xlsx`. F4 contains no gravel or coarse sand. The F4 ring-position assignment as an "aquifer" layer is geologically incorrect at TUKU. F4 IHM-F elastic storage coefficients cannot be physically interpreted as aquifer $S_{ske}$. `LAYER_COMPRESSIBLE_THICKNESS['F4'] = 16.617` m (entire span is compressible fine-grained material).
- **Two thickness values per layer (fixed 2026-06-06).** `LAYER_THICKNESS` (mm/m-to-$m^{-1}$ conversion for elastic $S_{ske}$) uses **total borehole span** (`total_m`). `LAYER_COMPRESSIBLE_THICKNESS` (inelastic $S_{skv}$ conversion) uses **fine-grained material thickness only** (`aquitard_m`). Both dicts are in `tau_demo_TUKU/12_stress_strain_per_layer.py` lines 94–124. Authoritative borehole breakdown: `figures/prestage_data_analysis/layer_thickness_borehole_TUKU.csv`. Source: `discussions/2026-05-29-technical-clarifications.md` lines 178–182.
- **Guardrails mandatory import (2026-06-08).** `scripts/guardrails.py` contains 10 automated physical-law checks with literature priors from Hung et al. (2021) WRR. All IHM-F and prediction scripts must import `validate_layer_params` before writing any parameter to disk. See the "Automated Guardrails" section above for the full checks table and usage pattern.
- **Physics safeguards reference (2026-06-08).** `discussions/PHYSICS_SAFEGUARDS.md` is the authoritative human-readable reference for all 11 physics rules with full source citations. Read it before writing any new guardrail code. The markdown document is authoritative — Python code is a computational expression of these rules.
- **Cumulative diagnostics (2026-06-08).** `scripts/10_ihmf/diagnose_cumulative_tuku.py` writes per-layer cumulative timeseries CSVs + fit PNGs to `results/ihmf/v3/diagnostics/`. Use for rapid visual inspection of two-regressor NNLS fits without re-running the full solver. Currently TUKU-only; generalize to all stations before batch use.
- **Borehole logging files (added 2026-06-09):** 32 MLCW borehole log files stored at `data/mlcw/borehole_materials/`. Filenames contain both CGS well identifiers (e.g., `CH_WSCH01G1`, `YL_WSYL23G1`) and English + Chinese station names. Not yet parsed by any script — available for layer geometry verification and $S_{ske}$/$S_{kv}$ physical bounds checking. Two wells (LUNFENG, JINHU) have borehole files but no entry in `gwl_to_mlcw_layer_assignment_v4.csv`.

### IHM-F Naming

- **IHM-F** = Candidate F of the Inelastic Head Model (IHM). The "F" is the candidate letter from the A-F method enumeration in `discussion_20260519_v3.md` — **not** an abbreviation of "Formational" or "Formation."
- Internal working name only. Do not use in publication. Refer to the model functionally: "two-regime groundwater-driven per-layer compaction model."
- Original definition: `discussions/methods_review_publications.md` line 14 ("Candidate F (IHM with per-layer β_k) — most physically defensible").

---

## AI Verification & Safety Protocol

**These rules govern what I must and must not do. They override conversational memory.**

### Insufficient-data rule

- Fewer than 10 jointly valid points for cross-correlation (or fewer than 4 for linear detrend): **"Insufficient data — result is undefined."**
- Fit did not converge: **"Fit did not converge — no parameter to report."**
- File missing or unreadable: state the path and **"File not found — cannot proceed."**

### Verify-before-stating rule

- Before citing any number as current truth — read the actual file on disk.
- Any layer geometry, depth range, parameter value, or result inherited from a session summary, handoff file, memory file, or prior-assistant message is UNVERIFIED until traced to a specific file path and line number. State the source explicitly before using the number analytically.
- After any script run — re-read the output file to confirm it was written and matches printed output.

### Physical-law halt rule

| Parameter | Bound | On violation |
|-----------|-------|--------------|
| $S_{ske}$ | $\ge 0$ | Halt. Report: "$S_{ske}$ = [value] is negative — layer rejected." |
| $S_{skv}$ | $\ge 0$ | Halt. Report: "$S_{skv}$ = [value] is negative — layer rejected." |
| $\beta$ | $\ge 0$ | Halt. Report: "$\beta$ = [value] is negative — layer rejected." |
| $S_{skv}$ / $S_{ske}$ ratio | 8–100$\times$ | Halt. Report: "Ratio = [value] — outside physical range." |
| Detrended head-to-InSAR corr. | < 0.7 per layer | Flag as collinear. Do not add model complexity. |
| $dh_{\text{raw}}$ sign | never negate | Halt if code negates H(t)−H($t_{ref}$). |

### Runtime-error rule

- Read the full traceback before proposing a cause. Never speculate from the error message alone.
- State the specific line number and variable that failed.
- Do not propose a complex fix until the simplest cause has been ruled out.

---

## Git State

- This repo: `.gitignore` tracks `.py`, `.ipynb`, `.md` only
- `tools/2S-TOOL-Python/`: independent repo (`github.com/david-ncu2019/twostoolspy`)
- `appsigsolv/` (`../20260501_timeseries_signal_solver/`): separate repo
- Companion repo (`D:\112_PROJECT_002`): own git — do not commit from here

---

## Math Notation Convention

All math uses LaTeX delimiters: `$...$` (inline), `$$...$$` (display).

| Correct | Wrong | Notes |
|---------|-------|-------|
| `$\tau$` | `τ` | Greek always in `$...$` |
| `$S_{ske}$` | `S_ske` | Subscripts use `_{}` |
| `$\ge 0$` | `≥ 0` | No Unicode operators |
| `$1.42 \times 10^{-5}$` | `1.42E-05` | No E-notation |
| `$\alpha \in (0, 1]$` | `α ∈ (0, 1]` | |

Conversion script: `scripts/fix_math_markdown.py` (run with `--dry-run` first).
