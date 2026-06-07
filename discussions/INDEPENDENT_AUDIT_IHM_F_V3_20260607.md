# Independent Audit Report: IHM-F v3 Consolidation Theory and Data Execution

**Date:** 2026-06-07  
**Target:** `scripts/10_ihmf/ihmf_model_v3.py`, `scripts/10_ihmf/fit_ihm_f_v3.py`, `scripts/10_ihmf/ihmf_io.py`  
**Status:** 🚨 CRITICAL FAILURES DETECTED  

A hyper-strict OODA loop audit was executed against the IHM-F v3 codebase and its inputs. The diagnostic revealed that the "NaN outputs" and heavily underperforming models are not simply a matter of poor data fit, but rather a cascading failure stemming from three fundamental programmatic and structural flaws.

---

## 1. Silent NaN Propagation (Programmatic Array Bug)
**Location:** `scripts/10_ihmf/ihmf_io.py` (Line ~53), `scripts/10_ihmf/ihmf_model_v3.py` (Line ~165)

**Observation:**  
The `ihmf_io.py` script aligns MLCW, GWL, and InSAR arrays using `pd.merge_asof`. However, it fails to perform a `dropna()` after the final merge operation. Diagnostic execution on the TUKU station arrays reveals that missing entries naturally trigger `NaN` propagation (e.g., TUKU F1–F4 all contain 2 NaNs in the `mlcw_mm` column).

**The Mathematical Collapse:**  
In `ihmf_model_v3.py`, the $\tau$ grid search operates on incremental signals (`np.diff`). The NaN values propagate into these increments. During the scalar OLS estimation:
```python
S_ke = max(0.0, np.dot(dH_e, db_e) / np.dot(dH_e, dH_e))
```
The `np.dot` operation over an array containing NaNs silently evaluates to `NaN`. The built-in `max(0.0, NaN)` returns `NaN`. This immediately poisons $S_{ke}$ and $S_{kv}$, resulting in `MSE_min = nan`, `alpha = nan`, and total execution failure across all walk-forward folds.

---

## 2. Violation of Detrending Rules (Structural Mathematical Flaw)
**Location:** `scripts/10_ihmf/fit_ihm_f_v3.py` (Lines ~58-59), `scripts/10_ihmf/ihmf_model_v3.py` (Lines ~37-56)

**Observation:**  
The `GEMINI.md` mandates strictly: *"Linear detrending [intercept + linear + annual harmonic] is mandatory before $\tau$ search."* The codebase provides a rigorous implementation of this in `ihmf_detrend.py`. 

**The Failure:**  
Although `fit_ihm_f_v3.py` explicitly imports `detrend_signal` from `ihmf_detrend.py` (Line 20), it is **never used**. Instead, `tau_grid_search_per_layer` invokes a local, naive `remove_seasonal_cycle()` function which merely subtracts the calendar-month climatological mean. The long-term linear (secular) trend remains embedded in the data. Consequently, the $\tau$ grid search attempts to align non-stationary secular trends rather than physical hydro-mechanical lag responses, structurally corrupting the delay optimization.

---

## 3. The "Double Negative" Sign Convention Mask (Physical Model Flaw)
**Location:** `scripts/10_ihmf/ihmf_io.py` (Lines ~42, 45) vs `docs/physics_rules_research_problem.md`

**Observation:**  
`GEMINI.md` strictly enforces the geomechanical sign convention: *"Positive = compaction (subsidence). InSAR data is inverted on load to match MLCW."*  
However, `ihmf_io.py` explicitly ignores this mandate:
```python
# Keep original sign: negative = subsidence (do NOT negate).
```

**The Hidden Collapse:**  
This I/O violation is currently the only reason the physical equation $\Delta b = S_k \cdot \Delta H$ yields mathematically "valid" (positive) storage values. 
- If water levels rise ($\Delta H > 0$), the aquifer physically *expands*. 
- Under the "negative = subsidence" scheme, expansion means $\Delta b > 0$. Therefore, $\Delta H$ and $\Delta b$ carry the same sign, yielding a positive dot product and a positive $S_k$.
- If the project's official rule ("positive = compaction") were enforced, expansion would mean $\Delta b < 0$. The signs would oppose, yielding a negative dot product. The clamping function `max(0.0, ...)` would then force $S_k$ to exactly `0.0`. 

**Conclusion:** The governing mathematical formulation lacks the physical minus sign ($\Delta b = -S_k \cdot \Delta H$) necessary to honor the project's sign conventions. The model is currently surviving purely because a data-loading bug cancels out a structural physics bug.

---

### Recommended Remediation Sequence (DECIDE & ACT phase prep)
1. Inject `.dropna()` in `ihmf_io.py` post-merge to halt NaN propagation.
2. Strip `remove_seasonal_cycle()` and correctly invoke `detrend_signal(T=365.25)` in the $\tau$ pipeline to honor the secular detrending physics rule.
3. Align the I/O sign convention with `GEMINI.md` and explicitly introduce the minus sign into the $\Delta b$ scalar OLS estimators in `ihmf_model_v3.py`.
