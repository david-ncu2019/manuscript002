# Seasonal Harmonic Analysis Findings (2026-05-31)

Three-station pilot (TUKU, XIUTAN, YUANCHANG) completed. All findings below are locked.

## Detrending

- **Linear detrend wins.** Moving average (365d or 730d) returns NaN across all 3 stations due to edge effects on a 10-year record. Never use MA for detrending in this pipeline.
- **MLCW baseline anchoring is mandatory.** MLCW cumulates from ~2003 installation; InSAR starts near 0 in Jan 2015. Compute f̄_k as OLS slope of $\Delta$ MLCW ~ $\Delta$ InSAR, both anchored to first common valid epoch. Without anchoring, R^2 = −4 to −11.

## Reconstruction quality (R^2 at 3 pilot stations)

| Layer | TUKU R^2_trend | TUKU R^2_seasonal | XIUTAN R^2_trend | XIUTAN R^2_seasonal | YUANCHANG R^2_trend | YUANCHANG R^2_seasonal |
|-------|-------------|----------------|----------------|------------------|------------------|-------------------|
| F1 | 0.845 | −0.11 | 0.977 | 0.17 | 0.701 | 0.12 |
| T1 | 0.820 | 0.00 | 0.992 | 0.22 | 0.886 | 0.43 |
| **F2** | **0.985** | **0.67** | **0.972** | **0.46** | **0.957** | **0.43** |
| T2 | 0.821 | 0.00 | 0.966 | 0.00 | 0.952 | 0.20 |
| F3 | 0.955 | 0.00 | 0.934 | 0.00 | 0.939 | 0.00 |
| F4 | 0.840 | 0.00 | 0.205 | 0.00 | 0.738 | 0.00 |

R^2_trend = anchored f̄_k $\times$ InSAR (Tier 1). R^2_seasonal = seasonal component only (detrended MLCW vs InSAR seasonal prediction).

## Phase stability gate results

| Station | F2 std_dphi1 (days) | F2 PASS? | Overall gate |
|---------|-------------------|---------|-------------|
| TUKU | 29.8 | ✓ | PASS |
| XIUTAN | 41.0 | ✓ | PASS |
| YUANCHANG | 18.0 | ✓ | PASS |

Threshold: std_dphi1 < 45d AND mean_A1 > 0.5mm.

## Locked decisions

1. **F2 seasonal is reconstructable from InSAR.** Phase is stable; amplitude is noisy year-to-year.
2. **F3/F4 seasonal is NOT recoverable.** Phase std > 59d at all stations. Do not attempt.
3. **Seasonal amplitude is NOT year-predictable.** Holdout skill scores uniformly negative. The deliverable is a seasonal phase characterisation map, not year-by-year amplitude.
4. **InSAR seasonal peak: DOY 154–172 (early June).** Not March–April as initially assumed. Inelastic consolidation accumulates through May–June. The sanity-check window in the code (60–120) is too narrow; DOY 90–180 is correct.
5. **Semi-annual component (T=182.5d) below noise everywhere.** Drop it from all fits; use annual-only harmonic.

## Run commands

```powershell
# Per station (check output before next):
PYTHONPATH="" conda run -n fafalab python scripts/13_seasonal_insar/01_seasonal_harmonic_analysis.py --station TUKU
PYTHONPATH="" conda run -n fafalab python scripts/13_seasonal_insar/02_reconstruction_visualization.py --station TUKU
```
