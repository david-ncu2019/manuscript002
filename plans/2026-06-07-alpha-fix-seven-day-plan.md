# Phase 1 Seven-Day Execution Plan — IHM-F v3 Gap-Fill at 37 MLCW Stations

**Goal:** Deliver validated IHM-F v3 gap-fill compaction predictions at all 37 MLCW stations by 2026-06-14.

**Architecture:** Ratio gate fixed (Day 1 done) → α artifact fix (Days 2–3) → TUKU pilot validation → batch 37 stations → gap-fill 5-day timeseries 2015–2025.

**Tech Stack:** Python 3.10 (`fafalab` env), `$env:PYTHONPATH=""; conda run -n fafalab python <script>` (PowerShell).

---

## CRITICAL: α = 0.034 Scaling Artifact — Root Cause and Executive Decision

### Root cause (confirmed 2026-06-07)

In GPS mode (`--gps`), the NaN shared-mask in `load_all_layers_gps()` (line 238 of `ihmf_io_multilayer.py`) includes GPS in the validity gate:

```python
valid_mask = np.isfinite(gps_mm_series)  # ← GPS NaN forces 2010-2024 window only
```

GPS at TUKU starts ~2010. This drops all 2003-2010 epochs — the heavy-pumping inelastic era. The 866-epoch 2010-2024 window is 96% elastic (only 36 inelastic events across all layers). Elastic oscillations cancel in cumulation: `cum_MLCW_pred ≈ −22 mm` over 14 years, while `cum_GPS = −660 mm`.

**Step 2 OLS** (`ihmf_model_v3.py` lines 342–344) fits:
```
α × cum_GPS + c = cum_MLCW_pred
α = −22 mm / −660 mm = 0.034   (physically wrong; expected 0.63)
```

**Observed R²_insar = 0.805 is misleading.** With α = 0.034, the code computes `GPS_pred = cum_MLCW_pred / 0.034 ≈ −647 mm ≈ cum_GPS (−660 mm)`. The apparent fit is a rescaling artifact: any small α makes `cum_pred/α` match GPS in magnitude. The model has not actually explained the secular trend.

**Empirical truth:** `TUKU_gps_mlcw_monthly.csv` OLS gives GPS = 1.58 × MLCW (R² = 0.991, N = 180 months) → α_physical = 1/1.58 = 0.634. The actual MLCW range is 434 mm; GPS range is 660 mm.

### What the gap-fill actually requires

For **Phase 1 (gap-fill MLCW at 37 stations)**: Step 1 ($S_{ke}$, $S_{kv}$, $\tau$ from MLCW vs GWL) is the reconstruction engine. α only matters for **Phase 2** (scale MLCW to GPS for spatial prediction). The correct validation metric for Phase 1 is $R^2_{\text{MLCW,cum}}$, NOT $R^2_{\text{insar}}$.

**However:** The current Step 1 NNLS fitted on the elastic-dominated 2010-2024 window likely underestimates $S_{kv}$ (too few inelastic events). Extending to the full 2003-2025 record (600+ inelastic events) will give better-calibrated $S_{kv}$.

### Executive decision: Pathway A-Modified

**Decision made 2026-06-07. Pathway B (data-driven with 2S-TOOL priors) rejected.**

Reason for rejecting B: 2S-TOOL Ss values are 10–300× too large at 5-day monitoring amplitude; 57/191 pairs have negative $S_{kv}$; building a new inference engine from scratch has P(success by June 14) ≈ 35%. 2S-TOOL values remain diagnostic reference only — NOT used as priors.

Pathway A-Modified: 4 code changes, full 2003-2025 Step 1 training, empirical α. P(success) ≈ 70%.

### Fix: 4 code changes + 1 new script

**Change 1 — Decouple GPS from Step 1 NaN mask (`ihmf_io_multilayer.py` line 238):**

```python
# BEFORE (locks training to GPS window 2010-2024):
valid_mask = np.isfinite(gps_mm_series)
for lyr, df in layer_dfs.items():
    valid_mask &= df["head_m"].notna().values
    valid_mask &= df["mlcw_mm"].notna().values

# AFTER (Step 1 uses full GWL+MLCW record; GPS tracked separately):
step1_mask = np.ones(len(gps_mm_series), dtype=bool)
for lyr, df in layer_dfs.items():
    step1_mask &= df["head_m"].notna().values
    step1_mask &= df["mlcw_mm"].notna().values
# GPS NaN mask applied only to the gps_mm_series array — do NOT intersect with step1_mask
```

Apply `step1_mask` (not including GPS) to filter `layer_dfs`. Return `gps_mm_series` as-is (NaN for 2003-2010 is allowed — Step 2 will detect and handle it).

**Change 2 — Add `alpha_external` to `joint_solve_fixed_tau()` (`ihmf_model_v3.py` lines 339–367):**

```python
def joint_solve_fixed_tau(
    layer_data: dict,
    inc_insar: np.ndarray,
    alpha_external: float | None = None,   # NEW
) -> dict:
    ...
    # Step 2 block — replace current OLS:
    cum_pred = np.cumsum(db_pred_all)
    if alpha_external is not None:
        alpha = float(alpha_external)
        beta  = 1.0 / alpha
        # c: minimize |cum_pred - (alpha * cum_insar + c)|² → c = mean(cum_pred - alpha*cum_insar)
        c_intercept = float(np.mean(cum_pred - alpha * cum_insar))
    else:
        A_step2 = np.column_stack([cum_insar, np.ones(T)])
        coeffs, _, _, _ = np.linalg.lstsq(A_step2, cum_pred, rcond=None)
        alpha = float(np.clip(coeffs[0], 1e-6, 1.0))
        beta  = 1.0 / alpha
        c_intercept = float(coeffs[1])
    # R²_insar and RMSE_insar diagnostics unchanged (lines 350-355 unmodified)
```

**Change 3 — Add `alpha_external` to `run_walk_forward_v3()` (`ihmf_model_v3.py` line 372):**

```python
def run_walk_forward_v3(
    layer_dfs, layer_metas, insar_mm, tau_max=120,
    fold_years=None,
    alpha_external: float | None = None,   # NEW — pass through to joint_solve_fixed_tau
) -> list[dict]:
    ...
    # In each fold, pass alpha_external to joint_solve_fixed_tau(...)
```

**Change 4 — Add `--alpha` CLI argument (`fit_ihm_f_v3.py`):**

```python
# In run_station():
def run_station(station, layer_filter=None, gps_mode=False, alpha_override=None):
    ...
    result = joint_solve_fixed_tau(layer_data, inc_insar_win, alpha_external=alpha_override)
    wf_results = run_walk_forward_v3(layer_dfs, layer_metas, inc_insar, tau_max,
                                     alpha_external=alpha_override)

# In argparse:
parser.add_argument("--alpha", type=float, default=None,
    help="Fix alpha to this value (e.g. 0.634 for TUKU). Bypasses Step 2 OLS.")
```

**New script — `scripts/10_ihmf/compute_alpha_empirical.py`:**

For each station: OLS on monthly MLCW vs monthly InSAR (or GPS where available). Writes `results/ihmf/alpha_empirical.csv` with columns: station, alpha, r2, N, note.

TUKU anchor: α = 0.634 (R² = 0.991, N = 180 months from `TUKU_gps_mlcw_monthly.csv`).
For other stations: use `InSAR_measures_at_MLCW.csv` (monthly) vs monthly-averaged MLCW CSV.

### Expected outcome after fix (TUKU GPS re-run with `--alpha 0.634`)

| Metric | Before fix | After fix |
|--------|-----------|-----------|
| α | 0.034 | 0.634 (fixed) |
| Step 1 n_epochs | 866 (2010-2024) | ~1400 (2003-2025) |
| $n_{\text{inelastic}}$ per layer | 11–36 | 100–400 (estimated) |
| $R^2_{\text{MLCW,cum}}$ | unmeasured | target > 0.6 |
| $R^2_{\text{insar}}$ (diagnostic) | 0.805 (misleading rescaling artifact) | < 0.1 (honest) |

The $R^2_{\text{insar}}$ will drop. This is physically correct: the IHM-F model predicts only GWL-driven transient compaction. The secular trend is supplied by the fixed empirical α. Low $R^2_{\text{insar}}$ with fixed α is not a failure — it confirms the model is not falsely absorbing secular GPS trend into $S_{kv}$.

---

## Strategic Decisions (Updated 2026-06-07)

| Decision | Status | Justification |
|----------|--------|---------------|
| Phase 2 spatial extrapolation (8,577 grid pts) | **NO-GO** | Phase 1 incomplete; batch not run; no variogram; impossible in 7 days |
| Seasonal $S_{ke}$ bifurcation | **NO-GO** | F2 has only 6 elastic epochs; binary split test failed 0/6 TUKU layers |
| 2S-TOOL as fixed parameter priors for Step 1 | **NO-GO** | 10–300× too large at 5-day amplitude; 57/191 NEG_SKV; diagnostic bounds only |
| IHM-F Step 2 α from OLS (GPS mode) | **REVISED** | OLS gives α = 0.034 (artifact of elastic-dominated window). α fixed externally at 0.634 for TUKU; empirical CSV for all 37 stations. OLS result retained as diagnostic but not used as the reported α. |
| Primary validation metric | **REVISED** | $R^2_{\text{MLCW,cum}}$ replaces $R^2_{\text{insar}}$ as the gate metric. The model is NOT expected to explain GPS secular trend from GWL increments alone. |

---

## Known Structural Limits at TUKU (Not Bugs — Accept and Proceed)

| Layer | Issue | Root cause |
|-------|-------|------------|
| T1 | $S_{ke,2s} = 0$ | 85 elastic epochs; elastic signal not identifiable in nearly-all-clay layer |
| F2 | Specific ratio 220.7× > 100 | H and V near-collinear; $S_{kv}$ absorbs all variance |
| F3 | $S_{ke} = 0$ | Only 7 elastic epochs; NNLS fallback with collinear regressors |
| F1 | $S_{ske}$ 10% below literature min | Borderline; check Hung 2021 lower bound before flagging FAIL |

---

## Critical Files

| File | Lines | Change |
|------|-------|--------|
| `scripts/10_ihmf/ihmf_io_multilayer.py` | 238–249 | Decouple GPS from Step 1 NaN mask |
| `scripts/10_ihmf/ihmf_model_v3.py` | 339–367 | Add `alpha_external` param to `joint_solve_fixed_tau` |
| `scripts/10_ihmf/ihmf_model_v3.py` | 372–420 | Add `alpha_external` param to `run_walk_forward_v3` |
| `scripts/10_ihmf/fit_ihm_f_v3.py` | 35–50, 180, 250 | Add `alpha_override` to `run_station`; `--alpha` argparse |
| `scripts/10_ihmf/compute_alpha_empirical.py` | NEW | Per-station empirical α from monthly MLCW vs InSAR/GPS OLS |
| `tau_demo_TUKU/12_stress_strain_per_layer.py` | 524-527, 560 | **DONE (2026-06-07)** — ratio gate bulk→specific storage |
| `PROGRESS.md` | 108–141 | Update after TUKU re-run with fixed α |

---

## 7-Day Execution Timeline

### Day 1 — 2026-06-07: Ratio gate fix ✅ DONE
- [x] Edit `12_stress_strain_per_layer.py` lines 524-527 and 560
- [x] Re-run Script 12; confirm T2 feasible_2s=true, F2 feasible_2s=false
- [x] Updated PROGRESS.md gate status (corrected specific-storage ratio table)

### Day 2 — 2026-06-08: α artifact fix (code changes 1–4 above)

- [ ] **2a.** Modify `ihmf_io_multilayer.py` lines 238–249: decouple GPS from Step 1 NaN mask (Change 1).
- [ ] **2b.** Modify `ihmf_model_v3.py` `joint_solve_fixed_tau()`: add `alpha_external` parameter (Change 2). When provided, skip OLS; set `c_intercept = mean(cum_pred − α × cum_insar)`; keep $R^2_{\text{insar}}$ diagnostic unchanged.
- [ ] **2c.** Modify `ihmf_model_v3.py` `run_walk_forward_v3()`: add `alpha_external` parameter (Change 3); pass through to each fold's `joint_solve_fixed_tau()` call.
- [ ] **2d.** Modify `fit_ihm_f_v3.py`: add `alpha_override` to `run_station()`; add `--alpha` argparse argument; pass through (Change 4).
- [ ] **2e.** Write `scripts/10_ihmf/compute_alpha_empirical.py`: OLS monthly MLCW vs InSAR/GPS for each of 37 stations; write `results/ihmf/alpha_empirical.csv`. TUKU anchor = 0.634.
- [ ] **2f.** Dry-run import check: `$env:PYTHONPATH=""; conda run -n fafalab python -c "import sys; sys.path.insert(0, 'scripts/10_ihmf'); from ihmf_model_v3 import joint_solve_fixed_tau"`

### Day 3 — 2026-06-09: TUKU GPS pilot re-run + validation

- [ ] **3a.** Run:
  ```powershell
  $env:PYTHONPATH=""; conda run -n fafalab python scripts/10_ihmf/fit_ihm_f_v3.py --station TUKU --gps --alpha 0.634 --all
  ```
- [ ] **3b.** Verify `results/ihmf/v3/TUKU_gps_v3_results.json`:
  - `alpha` = 0.634 exactly
  - `n_inelastic` per layer: all ≥ 50 (target 100–400)
  - No layer with $S_{ke} < 0$ or $S_{kv} < 0$
  - `r2_insar` will be low — expected, not a failure
- [ ] **3c.** Compute $R^2_{\text{MLCW,cum}}$: compare cumulative MLCW_pred to measured MLCW feather cumsum. Write `scripts/10_ihmf/diagnose_mlcw_r2.py` if needed. Target ≥ 0.5 for ≥ 3 of 6 layers.
- [ ] **3d.** Gate: if n_inelastic rises AND physical-law checks clean → proceed to Day 4. If Step 1 is still near-zero inelastic → halt and inspect GWL coverage pre-2015.
- [ ] **3e.** Check `docs/choushui_skeletal_storage_coeffs.md`: confirm F1 $S_{ske} = 6.54 \times 10^{-6}$ m⁻¹ vs Hung 2021 lower bound $7.27 \times 10^{-6}$ m⁻¹.

### Day 4 — 2026-06-10: Batch run — all 37 stations (InSAR monthly mode)

- [ ] Run `compute_alpha_empirical.py`; confirm TUKU row = 0.634 in `alpha_empirical.csv`
- [ ] Write (if absent) `scripts/10_ihmf/batch_run_ihmf_v3.py`: reads `ihmf_config.json`, groups by station, calls `run_station()` with per-station α from CSV
- [ ] Run batch:
  ```powershell
  $env:PYTHONPATH=""; conda run -n fafalab python scripts/10_ihmf/batch_run_ihmf_v3.py
  ```
- [ ] Physical-law screen: flag any station with $S_{ke} < 0$, $S_{kv} < 0$, α < 0, $n_{\text{inelastic}} < 10$
- [ ] Summary: how many of 191 station-layer pairs pass ratio gate [8, 100]×?

### Day 5 — 2026-06-11: Batch walk-forward + gap-fill timeseries

- [ ] Verify `walk_forward` array in each station JSON (already generated inside `run_station()`)
- [ ] Generate gap-fill predictions: 37 stations × 5-day cadence × 2015-2025
- [ ] Compute $R^2_{\text{MLCW,cum}}$ per station per layer via `diagnose_mlcw_r2.py`
- [ ] Record RMSE vs trend-only baseline per layer per fold

### Day 6 — 2026-06-12: Diagnostic plots + α stability screen

- [ ] Per-station diagnostic figures (TUKU, YUANCHANG, XIUTAN + 5 worst $R^2_{\text{MLCW}}$ stations)
- [ ] Flag stations where std(α across 4 folds) > 0.15
- [ ] Summary table: per-station valid-layer count, α_empirical, $R^2_{\text{MLCW,cum}}$, RMSE vs baseline

### Day 7 — 2026-06-14: Final deliverable consolidation

- [ ] Consolidate 37-station gap-fill predictions (5-day, 2015-2025)
- [ ] Compile parameters ($S_{ke}$, $S_{kv}$, τ, α_empirical) + validation metrics (4-fold RMSE, $R^2_{\text{MLCW,cum}}$)
- [ ] Phase 2 readiness gate: GO if ≥ 25/37 stations have ≥ 3/6 layers with $R^2_{\text{MLCW,cum}} > 0.5$ AND α_empirical ∈ [0.3, 0.9]
- [ ] Final PROGRESS.md update

**Final deliverable:** Validated IHM-F v3 MLCW gap-fill at 37 stations. Per-layer $S_{ke}$, $S_{kv}$, τ. Empirical α per station. 4-fold walk-forward RMSE. Phase 2 readiness decision.

---

## Verification (End-of-Day-3 Gate)

1. `TUKU_gps_v3_results.json`: `alpha = 0.634`, no negative storage parameters
2. `n_inelastic` per layer: all ≥ 50
3. $R^2_{\text{MLCW,cum}}$ ≥ 0.5 for at least 3 of 6 layers
4. PROGRESS.md updated: α fix recorded, TUKU pilot result recorded

---

## Notes

- Day 1 ratio gate fix: complete. T2 feasible_2s=true (8.42×), F2 feasible_2s=false (220.68×), F4 unchanged (10.76×).
- If $R^2_{\text{MLCW,cum}}$ is universally < 0.3 after full-record extension (Riley model cannot capture secular MLCW trend), escalate to user before Day 5 — do not silently proceed to batch.
- Walk-forward α stability flag threshold: std > 0.15 across 4 folds.
- Phase 2 partial (methodology + 1 synthetic prototype point): allowed only after Day 3 gate passes. Max 0.5 days.
