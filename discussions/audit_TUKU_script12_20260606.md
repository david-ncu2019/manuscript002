# OODA Audit — TUKU Script 12: Two-Regressor NNLS Cumulative Fit

**Date:** 2026-06-06  
**Script audited:** `tau_demo_TUKU/12_stress_strain_per_layer.py` (568 lines)  
**Constraint:** No production code was modified during this audit. All findings trace to specific file paths and line numbers.

---

## OBSERVE — Empirical Data

### 6-Layer Results

All values read from `tau_demo_TUKU/results/stress_strain_per_layer.json`.

| Layer | $S_{ke}$ (mm/m) | $S_{kv}$ (mm/m) | Ratio | R² | obs\_min (mm) | pred\_min (mm) | Capture |
|-------|-----------------|-----------------|-------|----|---------------|----------------|---------|
| F1    | 0.883           | 3.198           | 3.62× | 0.607 | −16.245 | −12.812 | 78.9% |
| T1    | 0.834           | 2.041           | 2.45× | 0.804 | −8.283  | −8.806  | 106%  |
| F2    | 0.525           | 13.176          | 25.10× | 0.845 | −102.203 | −80.078 | 78.4% |
| T2    | 0.897           | 5.247           | 5.85× | 0.489 | −17.639  | −21.254 | 120%  |
| F3    | 0.0             | 19.712          | null  | 0.754 | −146.635 | −107.311 | 73.2% |
| F4    | 0.375           | 6.512           | 17.34× | 0.546 | −14.950 | −15.107 | 101% |

Sources: `stress_strain_per_layer.json` lines 12–15 (F1), 37–40 (T1), 62–65 (F2), 87–90 (T2), 112–115 (F3), 137–140 (F4).

**Gate result:** F2 (25.10×) and F4 (17.34×) pass the $S_{kv}/S_{ke} = 8$–$100\times$ physical gate. F1, T1, T2 fail. F3 undefined ($S_{ke} = 0$).

### Regime Diagnostics

All values from `tau_demo_TUKU/results/regime_overlay_diagnostics.json`.

| Layer | h_c (m) | frac\_inelastic\_virgin | n\_inelastic\_Hbased | collinearity\_flag |
|-------|---------|-------------------------|----------------------|--------------------|
| F1    | −2.344  | 0.929                   | 356                  | true               |
| T1    | −2.344  | 0.890                   | 326                  | true               |
| F2    | −5.086  | 0.992                   | 169                  | true               |
| T2    | −8.457  | 0.592                   | 30                   | false              |
| F3    | −4.456  | 0.991                   | 160                  | true               |
| F4    | −7.008  | 0.290                   | 18                   | false              |

Sources: `regime_overlay_diagnostics.json` lines 2–21 (F1), 23–42 (T1), 44–63 (F2), 65–84 (T2), 86–105 (F3), 107–127 (F4).

### Borehole Correction Applied 2026-06-06

Ring-based `span_m` values in `layer_thickness.csv` were replaced with borehole-derived `total_m` values from `YL_WSYL23G1_TUKU_土庫.xlsx`. `LAYER_THICKNESS` and `LAYER_COMPRESSIBLE_THICKNESS` dicts in Script 12 lines 97–116 now use borehole values. The output JSON above still reflects the old ring-based `span_m` (pre-correction run); the `S_ske_m1` values in that JSON must be recomputed on next script run.

---

## ORIENT — Line-by-Line Code Audit

### h_c Loading (lines 121–148): Correct

`h_c` is read from `tau_demo_TUKU/results/tau_results.csv` column `h_c_m` — pre-computed from raw GWL feather rows dated before REF_DATE (2015-01-16) minimum. This matches the Bug F fix in `tau_demo_TUKU/01_run_tau_search.py` lines 115–121 and the physical justification in `discussions/2026-05-29-technical-clarifications.md` Item 4.

### Tau Lag Direction (lines 151–160): Correct

`H_lag = H_series.shift(tau_epochs)` with `tau_epochs > 0` shifts GWL forward in time, creating a lagged driver at `t − τ`. The MLCW response at epoch `t` is regressed against GWL at `t − τ`. Direction is correct.

### Virgin Exceedance Term (lines 191–205): Correct

`V_arr = np.minimum(0.0, np.minimum.accumulate(H_lag_arr) - h_c)`. The `cummin` correctly tracks the running minimum of lagged head, not instantaneous head. The virgin term activates only when lagged head sets a new historical low below $h_c$. This matches the physical model definition.

### NNLS Setup (lines 234–253): Correct Mechanics, Collinearity Mechanism Explained

```python
X = np.column_stack([-H_arr, -V_arr])  # negated for compaction-positive
b_neg = -b_arr
coef, _ = nnls(X, b_neg)
S_ke, delta = coef[0], coef[1]
S_kv = S_ke + delta
```

The negation is correct: compaction is negative in MLCW convention; negating both sides makes all quantities positive for NNLS. No intercept is included — zero-referencing at REF_DATE is assumed to eliminate mean offsets (this assumption is stated as a model design choice, not verified independently).

**Collinearity mechanism (mathematical):** When `frac_inelastic_virgin > 0.8`, the virgin term is active for over 80% of epochs. During these epochs, `V(t) ≈ cummin(H(t)) − h_c`. Because `cummin(H(t))` evolves monotonically downward while `H(t)` fluctuates around it, `V(t) = H(t) − h_c + ε` where `ε` is the residual between current head and the running minimum. When `ε → 0` (i.e., each new head value is also the minimum), `V(t)` and `H(t)` become nearly collinear. NNLS cannot separate $S_{ke}$ from $S_{kv}$ and compresses the ratio toward unity.

**Falsification of decoupled-OLS as a universal fix:** F2 has `frac_inelastic_virgin = 0.992` (higher than F1's 0.929) yet passes the physical gate at 25.10×. The failure of F1 is not caused by high `frac_inelastic_virgin` alone — it requires high collinearity AND low signal amplitude ($-16.245$ mm vs. $-102.203$ mm for F2). Decoupling would not repair F1 if signal amplitude is intrinsically small.

### Specific Storage Conversion (lines 441–448): Division-by-Zero for T1

```python
S_ske_m1 = S_ke / (span_m * 1000.0)
S_skv_m1 = S_kv / (span_m * 1000.0)
```

With the old `span_m = 0.0` for T1, these expressions are `S_ke / 0.0` — Python float division returns `inf` for non-zero numerator and `nan` for `0/0`. The output JSON records `"S_ske_m1": null, "S_skv_m1": null` for T1 (`stress_strain_per_layer.json` lines 42–43), confirming the result was caught and serialized as `null`. T1 specific storage values in the output JSON are physically undefined and must not be used.

**After borehole correction:** `LAYER_THICKNESS['T1'] = 8.729` m (borehole 41.577–50.306 m; source `YL_WSYL23G1_TUKU_土庫.xlsx`). The division-by-zero will be eliminated on next script run. The correct elastic-regime thickness for $S_{ske}$ conversion is `total_m = 8.729` m. The correct inelastic-regime thickness for $S_{skv}$ conversion is `aquitard_m = 7.423` m (see `LAYER_COMPRESSIBLE_THICKNESS` in Script 12 lines 109–116).

### Main Loop (lines 506–518): Silent Exception Swallowing

```python
try:
    result = process_layer(layer_cfg, mlcw, gwl_data)
    results.append(result)
except Exception as e:
    print(f"  ERROR {layer_cfg['layer']}: {e}")
```

All 6 layers ran successfully in the production run; no failure was masked. The architecture is a future liability because a silent failure would produce an incomplete results list with no halting behavior.

---

## DECIDE — Root-Cause Classification

Four distinct root-cause categories explain all 6 layers:

### Category 1: Collinearity + Low Signal Amplitude — F1 (3.62×), T1 (2.45×)

The HONGLUN well (09050111) feeds both F1 and T1 with $h_c = -2.344$ m. GWL has been below this threshold for 92.9% of F1 epochs and 89.0% of T1 epochs (`regime_overlay_diagnostics.json` lines 10, 31). The virgin term $V(t)$ is nearly collinear with $H(t)$ in both layers, compressing the NNLS ratio.

F1's total observed compaction range is $16.245$ mm over the study window — a small signal that amplifies any estimation noise. T1's range is $8.283$ mm. By contrast, F2 passes at 25.10× despite higher `frac_inelastic_virgin = 0.992` because its compaction range is $102.203$ mm — 6× larger.

**Root cause: Collinearity + intrinsically small compaction signal. Not a code bug.**

### Category 2: Data Insufficiency — T2 (5.85×)

The LUNZI well (09170121) for T2 has $h_c = -8.457$ m. Only 30 of 762 epochs (3.94%) drop below $h_c$ (`regime_overlay_diagnostics.json` lines 70–71). $S_{kv}$ is estimated from 30 data points — the solver is severely underdetermined for the inelastic parameter. T2's R² = 0.489 and the model over-predicts compaction ($-21.254$ mm predicted vs. $-17.639$ mm observed, 120% capture).

**Root cause: Insufficient inelastic epochs (30 points). Not a model bug.**

### Category 3: Permanently Inelastic Regime — F3 ($S_{ke} = 0$)

The TUKU well (09050331) for F3 has $h_c = -4.456$ m. The virgin term is active for 99.1% of epochs (`regime_overlay_diagnostics.json` line 94). The elastic design column $H(t) \cdot \mathbb{1}[V(t) = 0]$ has near-zero values across the entire time series. NNLS returns $S_{ke} = 0$ exactly, making the ratio undefined.

**Borehole confirmation:** F3 at TUKU spans 172.889–283.383 m. The borehole shows 76.994 m fine-grained material (mud/silt) out of 110.494 m total — 69.7% fine-grained. The dominant fine-grained fraction is physically consistent with permanently-inelastic behavior: this stratum has been compacting irreversibly through the entire study window with no elastic recovery episodes.

**Root cause: Permanently inelastic regime — two-regressor model structurally inapplicable to F3 at TUKU. Not a code bug.**

### Category 4: Code Bug — T1 Division-by-Zero in Specific Storage Conversion

The old `LAYER_THICKNESS['T1'] = 0.0` caused `S_ske_m1 = S_ke / (0.0 × 1000)` at Script 12 lines 441–448. Python returned `inf` for non-zero numerator, serialized as `null` in JSON (`stress_strain_per_layer.json` lines 42–43).

**Status: Fixed 2026-06-06.** `LAYER_THICKNESS['T1']` corrected to 8.729 m (borehole total span). `LAYER_COMPRESSIBLE_THICKNESS['T1']` = 7.423 m (fine-grained material only) added for inelastic $S_{skv}$ conversion. Division-by-zero eliminated on next script run.

---

## ACT — Recommendations

### Recommendation 1 (Fixed): T1 Specific Storage Conversion

**Status: Applied 2026-06-06.** Both `LAYER_THICKNESS` and `LAYER_COMPRESSIBLE_THICKNESS` dicts updated in Script 12 lines 97–116. T1 elastic conversion uses `total_m = 8.729` m; T1 inelastic conversion should use `LAYER_COMPRESSIBLE_THICKNESS['T1'] = 7.423` m. Script 12's conversion block at lines 441–448 currently uses `LAYER_THICKNESS` for both — a follow-up edit should split the conversion:

```python
S_ske_m1 = S_ke / (LAYER_THICKNESS[lyr] * 1000.0)          # elastic: total span
S_skv_m1 = S_kv / (LAYER_COMPRESSIBLE_THICKNESS[lyr] * 1000.0)  # inelastic: fine-grained only
```

This one-line change is the correct physical conversion per `discussions/2026-05-29-technical-clarifications.md` lines 178–182. It does not affect the NNLS fitting.

### Recommendation 2 (Not yet applied): Add tolerance to merge_asof

`scripts/10_ihmf/ihmf_io.py` lines 53–58 call `merge_asof(direction="nearest")` with no `tolerance` argument. A GWL data gap could silently match a stale observation from weeks earlier. Add `tolerance=pd.Timedelta('3D')` to limit maximum match distance to 3 days (safe for daily GWL cadence).

### Recommendation 3: T2 Well Reassignment

T2's 30 inelastic epochs reflect the LUNZI well's historically shallow drawdown ($H_{min} = -11.06$ m vs. $h_c = -8.457$ m). The 2.6 m maximum exceedance below $h_c$ is modest. A candidate well with deeper drawdown history would increase the inelastic epoch count and improve $S_{kv}$ estimation. Check `data/gwl/gwl_to_mlcw_layer_assignment_v4.csv` for alternative T2-depth wells at or near TUKU.

### Recommendation 4: F3 Single-Regressor Fit

F3 is permanently inelastic at TUKU for the 2015–2022 study window. The two-regressor model is structurally inapplicable. Fit a single-regressor model $b(t) = S_{kv} \cdot V(t)$ to estimate $S_{kv}$ directly. The resulting $S_{ske}$ is physically undefined (no elastic recovery observed); report as "not determined" rather than zero.

### Recommendation 5: Amplitude-Capture Metric

Add `amplitude_capture = pred_min_mm / obs_min_mm` to the output JSON as a standard diagnostic field. The 73–80% capture in F1/F2/F3 (vs. 101% in F4) directly quantifies the collinearity compression effect and should be tracked as a standard model quality indicator.

### Recommendation 6: Zero-Span Guard (Now Superseded by Fix)

The original recommendation was: add `if span_m == 0.0: record NaN, skip conversion`. This guard is now unnecessary because `LAYER_THICKNESS['T1'] = 8.729 m` eliminates the zero. However, a general guard remains good practice to prevent silent NaN propagation for any future zero-thickness edge case.

---

## F4 Geological Warning (New Finding — 2026-06-06)

The borehole log shows F4 at TUKU (283.383–300 m) is **entirely silt/mud** — 0.0 m aquifer material out of 16.617 m total. The four magnetic rings placed in this zone are assigned to "F4 aquifer" by ring-position convention, but the borehole material is Cat 5 (Z/M). The F4 ratio of 17.34× passes the physical gate, and the cumulative fit captures 101% of observed compaction amplitude, but these results describe fine-grained compaction, not aquifer elastic storage.

F4 $S_{ke}$ at TUKU cannot be interpreted as aquifer elastic skeletal storage — it is consolidation of fine-grained sediment responding to piezometric drawdown in the overlying F3 zone. Any spatial transfer of F4 $S_{ke}$ to grid points that genuinely have coarse aquifer material at 283–300 m will be physically invalid.

Source: `figures/prestage_data_analysis/layer_thickness_borehole_TUKU.csv` line 7 (`F4,16.617,0.000,16.617,0.0`). Documented in `CLAUDE.md` Known Code Issues section.

---

## Summary Table

| Finding | Layer(s) | Root cause | Code bug? | Action status |
|---------|----------|-----------|-----------|---------------|
| T2 predicts uplift (+3.12 mm) | T2 | Linear model allows positive prediction | No | Flag; add clamp if needed |
| 21–27% amplitude underestimation | F1, F2, F3 | Collinearity-induced NNLS compression | No | Document; use capture metric |
| F1/T1 ratio failure (3.62×, 2.45×) | F1, T1 | High collinearity + small signal | No | Consider well reassignment |
| T2 ratio failure (5.85×) | T2 | Only 30 inelastic epochs | No | Well reassignment |
| F3 S_ke = 0 | F3 | Permanently inelastic regime | No | Single-regressor fit |
| F2/F3 tau_opt = 0 | F2, F3 | Possible well mismatch | No | Investigate well coupling |
| F4 tau_opt = 105 with 18 inelastic epochs | F4 | Thin inelastic dataset | No | Flag result as provisional |
| No intercept | All | Model design choice | No | Document assumption |
| Silent exception swallowing | All | Code hygiene | No | Add re-raise after logging |
| T1 span_m = 0 → div/zero | T1 | Wrong span source (ring-based) | **Yes** | **Fixed 2026-06-06** |
| merge_asof no tolerance | All | Latent match-distance risk | Latent | Add 3D tolerance |
| F4 zero aquifer material | F4 | Geological mismatch | N/A | Documented; do not transfer $S_{ke}$ |
