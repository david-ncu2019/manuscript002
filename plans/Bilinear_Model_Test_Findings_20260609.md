# Bilinear Terzaghi/Riley Model — Test Findings (2026-06-09)

**What was tested:** a standalone re-implementation of the cumulative bilinear model,
run directly on `tau_demo_TUKU/data`, with no project code imported. Three test scripts
live in the repo root: `tmp_audit_test.py`, `tmp_audit_test2.py`, `tmp_audit_test3.py`.
Python: `C:\Users\Huy\anaconda4\python.exe` (base env, pandas 2.3.3, scipy 1.16.3).

The model (correct, zero-referenced form):

    b(t) = c + S_ke·u(t) + (S_kv − S_ke)·V(t)
    u(t) = H(t) − H(t_ref)              (head change from 2015-01-16)
    V(t) = min(0, cummin(H) − h_c)      (virgin/inelastic exceedance, ≤ 0)

I derived this form from first principles (Terzaghi effective stress + Riley
preconsolidation memory). **The formula is correct.** The problems are in the program and
in the choice of model for the gap-fill objective.

---

## Finding 1 — The production solver's `S_ke` is set by the well's sea-level datum (a bug)

The model multiplies head by S_ke. The physics needs the **head change** u(t)=H−H_ref.
The production GPS path uses the **absolute** head H instead, with no intercept. Because
the fit is forced through the origin, the elastic coefficient is decided by the arbitrary
absolute datum of each well, not by physics. Proof from the data:

| Layer | Well | Absolute head (median) | Production `S_ke` |
|---|---|---|---|
| F1, T1 | HONGLUN | +8.5 m (always positive) | **0.0** |
| F2, F3 | TUKU | +3.0 m | 0.0 (full record) |
| F4 | LIUZHUANG | −1.2 m (mixed) | 1.90 |
| T2 | LUNZI | −8.2 m (always negative) | 0.72 (only one that "works") |

The single layer whose elastic coefficient survives is the one well with negative absolute
head. That is the bug, demonstrated: `Test 1` column B\* reproduces the S_ke=0 collapse.

Fixes: (1) use zero-referenced head u(t), not absolute H; (2) add the intercept c. With
both, every layer's R² improves (F1 0.61→0.77, T2 0.49→0.77, F2 0.85→0.89). `Test 1`
column A (zero-ref, no intercept) reproduces Script 12's published numbers exactly,
confirming the re-implementation is faithful.

---

## Finding 2 — Even the corrected model fails the gap-fill objective

Three hold-out designs were run. Numbers are RMSE in mm (lower = better).

**End-gap, GWL model vs naive baselines (`Test 1`/Test 2):** skill vs linear trend is
negative for 5 of 6 layers; F2 is 5× worse than a straight line.

**Middle-gap, three methods (`tmp_audit_test2.py`):**

| Layer | GWL bilinear | GPS carrier | linear interp | best |
|---|---|---|---|---|
| F1 | 1.50 | 1.88 | **1.28** | interp |
| T1 | 1.88 | **0.89** | 1.13 | GPS |
| F2 | 10.95 | **3.06** | 4.60 | GPS |
| T2 | 3.24 | **1.84** | 2.18 | GPS |
| F3 | 18.21 | 10.67 | **4.60** | interp |
| F4 | 2.79 | 2.02 | **0.63** | interp |

**End-gap "well stops", three methods (`tmp_audit_test3.py`):**

| Layer | GWL bilinear | GPS carrier | linear trend | best |
|---|---|---|---|---|
| F1 | **2.22** | 3.03 | 3.10 | GWL (tie) |
| T1 | 9.32 | **1.01** | 1.17 | GPS |
| F2 | 12.51 | **4.39** | 4.66 | GPS |
| T2 | 7.79 | **3.08** | 3.34 | GPS |
| F3 | 32.68 | 20.93 | **19.00** | trend |
| F4 | 8.71 | 3.96 | **3.86** | trend |

**Conclusions:**
- The GWL bilinear model is the **worst** method in almost every cell. It is catastrophic
  for the deep aquifers F2/F3, exactly where head and the virgin term are collinear.
- The **InSAR/GPS carrier** never blows up and is best or tied-best for the well-coupled
  layers (T1, F2, T2), with modest positive skill over a naive trend.
- For smooth deep layers (F3, F4), a plain **linear trend / interpolation** is hard to
  beat. The project's own success bar ("beat static linear interpolation") is therefore a
  demanding bar.

---

## Implication

The GWL-driven bilinear model is useful for **estimating physical parameters**
(S_ke, S_kv for characterization), but it is **not** the right engine for gap-fill or
prediction. Surface deformation (InSAR/GPS) is the integral of layer compaction, so it
carries the compaction signal far more directly than groundwater head does. The gap-fill
method should be built on the InSAR/GPS carrier, with GWL as a secondary covariate.
