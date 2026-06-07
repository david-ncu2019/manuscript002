# Why InSAR and GPS Are Essential — Even When GWL Drives the Per-Layer Physics

**Date:** 2026-06-05
**Type:** Methodological note — internal evidence
**Question:** If we can use groundwater data to reconstruct layer-wise subsurface compaction time series, why do we still need total surface deformation from InSAR or GPS?

**Source:** Project documents, CLAUDE.md, discussion files, IHM-F model code

---

## The short answer

GWL tells you what the pressure is doing at a few discrete well screens. InSAR tells you what the entire sediment column actually did in response — including compaction from depths and locations your wells cannot see. GPS tells you whether your InSAR vertical decomposition is correct. They are not redundant; they carry partially independent information, and the model breaks without both.

---

## 1. The v3 architecture: GWL drives layers, InSAR constrains the sum

In IHM-F v3 (Candidate F of the Inelastic Head Model), the per-layer equation uses **GWL-only drivers** (from `ihmf_model_v3.py` lines 4–10):

**Step 1 (per layer, MLCW target):**

$$\Delta b_j(t) = S_j \cdot \Delta H_j(t - \tau_j)$$

**Step 2 (surface alignment, InSAR target):**

$$\alpha \cdot \Delta d_v(t) = \sum_j \Delta b_j(t)$$

No $\beta_k \cdot x(t)$ term appears in the per-layer equation. InSAR enters only in Step 2 — as the **total surface target** that the sum of per-layer predictions must match. The scalar $\alpha \in (0, 1)$ is the fraction of total InSAR displacement that the modelled 0–300 m layers explain (at TUKU, $\alpha \approx 0.45-0.55$). The remaining $1-\alpha$ represents compaction below 300 m that no GWL well monitors.

This is the critical design insight: **by removing InSAR from the per-layer equation, v3 eliminates the collinearity problem that plagued v1/v2.** GWL and InSAR no longer compete in the same fitting step. GWL drives Step 1; InSAR is the target in Step 2. But InSAR remains structurally essential — without it, Step 2 has no target, and the per-layer predictions have no column-sum anchor.

---

## 2. Five distinct roles InSAR plays (that GWL cannot)

### Role 1: Column-sum constraint

If you fit each layer independently using GWL only, nothing prevents the sum of predictions from drifting. You could predict 5 mm in F1, 8 mm in F2, and 3 mm in F3 — summing to 16 mm — while InSAR observed only 10 mm. The GWL-only model has no way to detect this over-prediction.

From `methods_review_publications.md` lines 443–445:

> Without InSAR, the sum $\Sigma \hat Y_k$ has no physical constraint. It can deviate arbitrarily from the InSAR-observed total displacement with no diagnostic signal.

The $\alpha$ scalar enforces $\Sigma \hat Y_k \approx \alpha \cdot x(t)$ at every epoch. This is not a post-hoc check — it is embedded in the joint inversion.

### Role 2: Spatial carrier to 8,577 grid points

GWL monitoring wells exist at ~100 locations across the CRAF. InSAR exists at **8,577 grid points** (500 m spacing). At any location more than a few kilometres from a well, the GWL signal is an interpolated approximation with unknown error.

From `discussion_20260519_v3.md` lines 160–163:

> The GWL network contains 306 monitoring wells across the CRAF. InSAR provides measurements at approximately 65,000 points at its native 40 m ground resolution, or at 8,577 points on the 500 m analysis grid. No feasible expansion of the GWL network can match this spatial coverage.

The spatial transfer strategy is: calibrate per-layer parameters at 37 MLCW stations, krige those parameters to grid points, then **use InSAR at every grid point** as the surface constraint. Without InSAR, you have no spatially continuous signal to drive predictions at unmonitored locations.

### Role 3: Compaction sources beyond the local GWL screen

A GWL well measures pressure at one specific depth screen — typically in an aquifer sand. It does not measure:

- **Compaction below 300 m** — the deepest MLCW rings are at ~300 m, and the deepest GWL screens are shallower still. Any compaction in deeper sediments contributes to InSAR surface displacement but has no corresponding GWL record.
- **Compaction between screened intervals** — aquitards (clay layers) between monitored aquifers compact under their own pore-pressure dynamics, which lag behind the measured aquifer pressure due to low hydraulic diffusivity.
- **Distant pumping interference** — a well pumping 5 km away creates a pressure gradient that induces compaction at the MLCW station without significantly changing the local GWL reading.

From `discussion_20260528_ihm_theory.md` lines 86–87:

> The assigned GWL well does not monitor every depth interval. Deep aquitards, laterally discontinuous interbeds, and confined units screened by wells far from the MLCW station all contribute to compaction in ways that the local head record does not capture. InSAR surface displacement integrates the total vertical motion from all depths and all locations within the radar pixel.

### Role 4: Proxy GWL correction

This is the most acute practical problem. Only 21 of 39 MLCW stations have a co-located GWL well. The remaining 18 stations — and **all 8,577 grid points** — must use the nearest GWL well within a 10 km search radius.

From `discussion_20260519_v3.md` lines 161–164:

> Only 21 of the 39 MLCW stations have a co-located GWL well. At the remaining 18 stations, GWL must be horizontally interpolated from the nearest screened wells before any IHM or DLLM fit can be performed. InSAR, by contrast, is available at every station location without interpolation. A production model that relies solely on GWL introduces interpolation error at approximately half the calibration stations before a single parameter is estimated.

A GWL well 5 km away may experience different pumping regimes, different hydraulic properties, and different seasonal head patterns than the aquifer directly beneath the MLCW station. InSAR, measured at the exact station pixel, provides a local constraint that partially compensates for proxy GWL mismatch.

### Role 5: Post-shutdown validation anchor

After MLCW stations shut down, InSAR becomes the **only measurement that can validate per-layer predictions.** GWL continues (wells keep recording), but without MLCW, there is no direct per-layer compaction ground truth. The column-sum check — does $\Sigma \hat Y_k$ match $\alpha \cdot x(t)$? — becomes the primary diagnostic that the predictions have not drifted.

This is exactly what the walk-forward Fold 1 tests: train on 2015–2021 (MLCW operational), predict 2022 (simulating MLCW shutdown). Without InSAR, you are extrapolating GWL-only predictions with no surface constraint and no way to detect drift.

---

## 3. GPS: Independent 3D validation

GPS plays a different role from InSAR — it serves as an **independent measurement technique** for validation, not as a spatial prediction carrier.

| Property | InSAR | GPS |
|----------|-------|-----|
| Coverage | 8,577 grid points | ~45 stations in CRAF |
| Temporal resolution | 5 days | Daily |
| Measurement | Line-of-sight (LOS) | True 3D (dN, dE, dU) |
| Vertical accuracy | ~3–10 mm (after LOS decomposition) | ~2–5 mm |
| Technique | Radar interferometry | GNSS positioning |

GPS provides three things InSAR cannot:

1. **True vertical displacement** — InSAR measures line-of-sight motion. Decomposing ascending + descending LOS into vertical + horizontal components introduces uncertainty. GPS dU (vertical component) provides an independent check on whether the InSAR decomposition is correct.

2. **Daily temporal resolution** — InSAR has a 5-day repeat cycle (Sentinel-1). GPS records daily. For detecting rapid compaction events (e.g., during a sudden pumping excursion), GPS provides the higher-frequency signal.

3. **Horizontal motion detection** — InSAR LOS decomposition can misattribute horizontal motion to vertical if the decomposition geometry is unfavorable. GPS dN/dE measurements catch this contamination.

97 GPS stations have been processed through the same STL decomposition pipeline as MLCW, producing modeled vertical timeseries for independent cross-validation.

---

## 4. Empirical evidence from TUKU

The TUKU pilot results demonstrate that GWL and InSAR carry **partially independent** information:

| Layer | corr(y, InSAR) | corr(ΔH, InSAR) | Interpretation |
|-------|---------------|-----------------|----------------|
| F1 | Moderate | High | GWL and InSAR both informative, somewhat collinear |
| F2 | > 0.98 | ~0.5 | InSAR dominant, GWL adds residual value |
| F3 | > 0.98 | 0.24 | InSAR dominant, GWL weakly informative |
| F4 | > 0.98 | Low | InSAR captures signals local GWL cannot see |

The key numbers:
- **InSAR alone achieves R² ≈ 0.97** at F2–F4 at TUKU — it explains nearly all per-layer compaction variance
- **corr(ΔH, InSAR) = 0.24** at F3 — GWL and InSAR are weakly correlated, so each contributes unique information
- **α ≈ 0.45–0.55** at TUKU — roughly half of InSAR displacement comes from the 0–300 m column that MLCW monitors; the other half comes from deeper or unmonitored compaction

This is why a GWL-only model would fail at F3/F4: the local GWL well simply does not capture the dominant compaction drivers at these depths. InSAR captures them, and the joint inversion distributes the InSAR total across layers via the column-sum constraint.

---

## 5. The operational scenario: what happens when MLCW shuts down

This is the core motivation. When an MLCW station closes:

| Data stream | Still available? |
|-------------|-----------------|
| MLCW per-layer compaction | **No** — station is decommissioned |
| GWL piezometric head | **Yes** — monitoring wells continue |
| InSAR surface displacement | **Yes** — satellite keeps acquiring |
| GPS surface displacement | **Yes** — continuous stations continue |

Without InSAR, the post-shutdown prediction chain is:

> GWL → per-layer compaction → **(no validation possible)**

With InSAR, the chain becomes:

> GWL → per-layer compaction → column-sum check vs. InSAR → **validated prediction**

InSAR is the only measurement that persists after MLCW shutdown AND provides a physical constraint on the total column response. Without it, per-layer predictions at shut-down stations are unverifiable extrapolations.

---

## Bottom line

GWL drives the per-layer physics — head drops, effective stress rises, compaction occurs. But GWL alone cannot tell you whether the total compaction across all layers is physically consistent, cannot carry the prediction to locations without wells, and cannot capture compaction from depths and distances your wells do not reach. InSAR fills all three gaps. GPS provides the independent check that your InSAR vertical decomposition is correct in the first place.
