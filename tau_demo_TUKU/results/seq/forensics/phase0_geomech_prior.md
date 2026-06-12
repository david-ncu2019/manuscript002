# Phase 0 — Geomechanical Prior (NotebookLM research)

**Date:** 2026-06-12 | **Source:** NotebookLM CLI queries, 4 project notebooks (live, not fallback).
**Purpose:** ground the F3 forensic triage in CRAF literature before any code.

---

## The physical picture in one paragraph

The deep clay-rich layer at Tuku (F3, ~238–275 m, 69.7% fine-grained) is exactly the kind of
sediment the literature says should breathe *out of phase* with the seasonal groundwater cycle. Thick
clay aquitards in the Choushui River Alluvial Fan (CRAF) dissipate pore pressure slowly (hydrodynamic
lag) and keep compacting by soil creep (secondary compression) even when the head recovers. The very
well the literature names — TKSH at Tuku — was observed compacting steadily from 2004–2007 while the
seasonal groundwater level was *rising*. So a phase-wrong F3 prediction is, on its face, physically
plausible — but that is precisely why the forensic triage must rule out a faulty driver and a
poisoned truth before crediting "physical outlier."

---

## 1. Storage coefficients (S_ske, S_skv) — Hung et al., via Choushui_Sub (`7ff80e8e`)

| Zone | S_ske (m⁻¹) | S_skv (m⁻¹) | Ratio | Note |
|------|-------------|-------------|-------|------|
| Middle fan | 11.5×10⁻⁵ (1.15e-4) | 13.3×10⁻⁴ (1.33e-3) | ~11.6× | matches CLAUDE.md guardrail prior |
| Distal fan | 11.6×10⁻⁵ (1.16e-4) | **see note** | — | NotebookLM rendered "19.1×10⁻⁵"; CLAUDE.md guardrail says 1.91e-3. 10× discrepancy — treat CLAUDE.md (1.91e-3) as authoritative; flag. |
| Coastal Dacheng (numerical) | — | aquifer-2 3.19×10⁻³; aquitard-2 2.51×10⁻² | — | deep coastal end-member |

Inelastic exceeds elastic by ≥ 1 order of magnitude → permanent settlement when head declines.

## 2. Consolidation lag τ — TKSH well, Tuku (Choushui_Sub)

- TKSH (Tuku) records **time constants for 90% compaction of 26–488 days** at depths **220–300 m**
  (F3's interval). In our 5-day epoch units: 488 days ≈ **98 epochs**.
- **Cross-check against our diagnosis:** the Red Team / Script 28 diagnosed F3 best τ ≈ 163 epochs
  (815 days). That **exceeds the literature 90%-compaction upper bound (98 epochs)** — F3's fitted lag
  is longer than the documented physical lag for this depth. This is a yellow flag worth carrying into
  the verdict: either the fit is reaching for a lag the physics does not support (driver/truth
  problem), or residual/creep compaction stretches the effective lag beyond the 90% time.

## 3. Deep-clay behavior vs Central Valley — Subsidence_Papers (`dbcc4e4a`)

- **Soil creep (secondary compression):** clays are visco-elasto-plastic — they keep compressing at
  constant effective stress; pores collapse irreversibly; minimal rebound.
- **Out-of-phase with seasonal GWL:** sandy aquifers respond near-instantly; clay lenses lag. At TKSH
  (Tuku) compaction continued 2004–2007 *out of phase* with seasonal GWL rises.
- **Noordbergum–Rhade effect:** at pumping onset, aquitard pore pressure can momentarily *rise* →
  initial clay extension (uplift) → desynchronizes aquitard deformation from aquifer head drop.
- Same masking seen in CRAF and California Central Valley: little seasonal uplift during recovery,
  then accelerated consolidation when drawdown resumes.

## 4. Surface-to-layer identifiability — InSAR_Thesis (`8c6faa4f`)

- Surface geodesy (InSAR/GNSS) has **no depth resolution**; it measures the integrated column strain.
- **Deep-layer signals can be masked/canceled at the surface by phase opposition** between layers
  (shallow expansion vs deep compaction destructively interfere).
- Surface-only inversion is **rank-deficient and underdetermined** — infinitely many per-layer
  combinations sum to the same surface displacement. Requires depth-resolved auxiliary data
  (multi-depth piezometers) or strong a-priori regularization. (Corroborates Red Team feasibility
  proof: carrier rank-1, amplitude-bound.)

## 5. MLCW data precision — MLCW notebook (`fe2eaf50`)

- Magnetic-ring extensometers have **1 mm precision/accuracy**, read **monthly**.
- Sources do not document a CRAF MLCW interpolation convention, BUT the 1 mm instrument precision
  means **genuine raw readings should be integer millimetres**. Non-integer values are a fingerprint
  of post-processing / interpolation (validates the Phase 2.2 second-difference + integer-fraction
  test and the Red Team F-6 flag: 15.5% non-integer pre-2019 → 100% in 2024).

---

## Named physical traps to test against (carried into Phases 2–3)

1. **Hydrodynamic lag / residual compaction** — F3 may genuinely lag head by months.
2. **Soil creep (secondary compression)** — trend-like compaction decoupled from seasonal head.
3. **Noordbergum–Rhade reversal** — short-lived inverse-sign clay response at drawdown onset.
4. **Phase-opposition masking** — deep F3 seasonal cancels against shallow layers at the surface.

## Priors for the synthetic test (Phase 1)

- S_ske ∈ [1.1e-4, 1.2e-4] m⁻¹; S_skv ∈ [1.3e-3, 1.9e-3] m⁻¹ (middle→distal); ratio 8–20×.
- τ physical range for 220–300 m: up to ~98 epochs (90% time); we inject τ=200 deliberately to test
  recovery *beyond* the physical range (a stress test of the solver, not a physical claim).
