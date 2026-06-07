# Head–Thickness Relation: Piezometric Head vs. Layer Compaction

*A hybrid reference: conceptual primer for the new reader, technical companion for the data analyst.*

---

## 1. What happens when groundwater is pumped?

Consider a sponge buried under a stack of bricks. The bricks represent the overburden load; the sponge is the aquifer sediment; the water filling the sponge's pores carries part of that weight. When groundwater is extracted, pore pressure drops. The water can no longer bear its share of the overburden. Load transfers from fluid to solid skeleton. The skeleton compresses. The ground surface sinks.

This sequence is formalized through Terzaghi's effective stress principle. Total overburden stress $\sigma$ divides between the sediment skeleton ($\sigma'$) and pore water pressure ($u$):

$$\sigma = \sigma' + u$$

If total stress remains constant (no new construction, no sediment accumulation), a change in piezometric head $\Delta h$ produces an equal and opposite change in effective stress:

$$\Delta \sigma' = -\rho_w g \, \Delta h$$

**Groundwater level decline cuts pore pressure. Effective stress rises. The layer compresses.**

---

## 2. From head change to thickness change

### 2.1 Skeletal compressibility

How much the skeleton compresses depends on a material property: skeletal compressibility $\alpha$, defined as the fractional thickness change per unit effective stress increase:

$$\alpha = -\frac{1}{b_0} \frac{\Delta b}{\Delta \sigma'}$$

Substituting $\Delta \sigma' = -\rho_w g \Delta h$:

$$\Delta b = -\alpha b_0 \rho_w g \, \Delta h$$

### 2.2 Skeletal specific storage

The product $\rho_w g \, \alpha$ is the **skeletal specific storage** $S_{sv}$ (units: m$^{-1}$). It measures the volume of water released per unit volume of sediment per meter of head decline:

$$S_{sv} = \rho_w g \, \alpha$$

Multiplying by the initial layer thickness $b_0$ yields the dimensionless **skeletal storage coefficient** $S_k$:

$$S_k = S_{sv} \, b_0$$

The governing equation becomes:

$$\boxed{\Delta b = -S_k \, \Delta h}$$

- $S_k$ = skeletal storage coefficient [--]
- $\Delta b$ = thickness change [L]; sign convention is detailed below
- $\Delta h$ = head change [L]; positive = rise

For millimeter-scale work in the CRAF dataset, the **production coefficient** $\beta$ (mm per m head change) replaces $S_k$:

$$\beta = S_k \times 1000$$

---

## 3. Two sign conventions

| Convention | Formula | $\Delta b$ sign | $\Delta h$ sign | Example: head drops 1 m |
|---|---|---|---|---|
| **Physical** (Smith et al. 2021, Eq. F2) | $\Delta b = \Delta h \, S_{ke}$ | $<0$ = compaction | $<0$ = decline | $\Delta b < 0$ (compaction) |
| **Operational** (CRAF code pipeline) | $\Delta b = -S_k \, \Delta h$ | $>0$ = compaction | $<0$ = decline | $\Delta b > 0$ (compaction) |

Both conventions encode identical physics. The difference is a manual sign inversion applied to $\Delta b$ in the operational pipeline so that compaction, subsidence, and head decline each produce positive values in plots and regression targets.

**Smith et al. (2021) Eq. F2** writes:

$$\Delta b_e = \Delta h \, S_{ke}$$

with compaction being negative. No minus sign. The present study inverts $\Delta b$ so that positive always means "subsidence direction" across all variables. This is purely a display and coding convention; the underlying poroelastic physics is unchanged.

**Rule of thumb for the analyst:** if a code variable named `compaction` or `delta_b` appears positive, it represents the operational sign. The physical thickness change is the negative of that value.

---

## 4. Elastic vs. inelastic compaction

### 4.1 The preconsolidation head

Every aquitard has a memory. The lowest head it has ever experienced defines the **preconsolidation head** $h_c$. When current head stays above $h_c$, effective stress remains within the historical range and compaction is **elastic** (recoverable). When head falls below $h_c$, effective stress enters new territory and compaction becomes **inelastic** (permanent, irreversible skeletal grain rearrangement).

$$S_{skv} \gg S_{ske}$$

For fine-grained CRAF aquitards, the inelastic coefficient $S_{skv}$ exceeds the elastic $S_{ske}$ by a factor of 10 to 100.

### 4.2 Two-regime formulation

Elastic, recoverable:

$$\Delta b_e = -S_{ske} \, b_0 \, \Delta h \qquad (\text{head above } h_c)$$

Inelastic, permanent:

$$\Delta b_i = -S_{skv} \, b_0 \, \Delta h \qquad (\text{head below } h_c)$$

The IHM‑F model fits both regimes simultaneously via a per‑layer production coefficient $\beta_k$ that changes value at $h_c$. In Smith et al. (2021), the study area never crossed the preconsolidation threshold, so only Eq. F2 (elastic) was used. The CRAF dataset spans multiple years of head decline; both regimes are activated.

### 4.3 Water compressibility (and why it is ignored)

The full specific storage includes water compressibility $n\beta_w$:

$$S_s = \rho_w g (\alpha + n\beta_w)$$

In low‑permeability aquitards, skeleton compression overwhelms water compression by two to three orders of magnitude. The $n\beta_w$ term is dropped in the CRAF pipeline.

---

## 5. Why compaction is not instantaneous: the time lag

### 5.1 The physics of delayed drainage

Sandy aquifer layers drain quickly. Interspersed silt and clay lenses drain slowly because their vertical hydraulic conductivity $K_v$ is orders of magnitude lower. When pumping lowers the head in the surrounding sand, the clay interior initially retains its old pore pressure. Water seeps out gradually: the pressure difference drives a transient flow that equilibrates over time. Deformation, concentrated in the compressible clay, lags behind the head change measured in the well screen.

Smith et al. (2021) quantify this lag for a clay lens of thickness $b_0$ bounded by equal head changes on both sides (Eq. F6):

$$\tau = \left( \frac{b_0}{2} \right)^2 \frac{S_s}{K_v}$$

**Key scaling:** lag grows with the **square** of clay thickness and varies **inversely** with vertical hydraulic conductivity. A 2‑m clay lens of moderate storativity may equilibrate in days. A 20‑m lens of the same material requires months.

### 5.2 Incorporating lag into the deformation model

In the Smith et al. (2021) framework and the IHM‑F framework alike, each layer $k$ receives its own lag parameter $\tau_k$. The head time series is shifted backward:

$$\Delta b_k(t) = -\beta_k \, \Delta h_k(t - \tau_k)$$

$\tau_k$ is fitted alongside $\beta_k$. For the CRAF dataset, the IHM‑F grid search probes lags from 0 to 24 epochs (0 to 10 months).

---

## 6. Measuring total surface displacement with InSAR

Smith et al. (2021) provides a compact description of the full measurement chain. The same logic underlies the CRAF pipeline.

### 6.1 From radar phase to displacement

Two SAR (Synthetic Aperture Radar) images of the same ground patch produce an interferogram: the phase difference $\delta\phi$ between the two acquisitions is proportional to the Line‑of‑Sight (LOS) displacement that occurred in the interval. The Small Baseline Subset (SBAS) algorithm chains many such pairs into a redundant temporal network (Eq. F7, F8), solving for a constant LOS deformation rate $v_c$ and a seasonal residual time series.

### 6.2 LOS‑to‑vertical projection

SAR satellites observe at an oblique angle. For Sentinel‑1 over the CRAF, the LOS unit vector has a vertical component of approximately --0.78 (Eq. F10). Assuming horizontal motion is negligible in this regional‑pumping setting, vertical displacement $d$ is recovered from LOS displacement $d_{\text{LOS}}$ by dividing by 0.78 and inverting the sign (Eq. F9):

$$d = -\frac{d_{\text{LOS}}}{0.78}$$

In the CRAF pipeline, InSAR data are further **negated on load** so that positive values denote subsidence (downward movement), aligning with the operational sign convention.

### 6.3 Summing contributions from layers

The total surface displacement is the sum of deformations from all subsurface layers (Smith et al. Eq. F11):

$$d = \sum_{k} \Delta b_k$$

This assumes independent deformation in each layer and linear superposition. The depth‑resolved decomposition is the core of the apportionment problem.

---

## 7. Apportioning deformation among layers: the inversion

### 7.1 The coupled head‑deformation equation

Substituting the lagged head into the elastic compaction law for each layer $k$ and summing yields the governing equation of the inversion (Smith et al. Eq. F12):

$$d = \sum_{k} \Delta h_k(t - \tau_k) \, S_{k}$$

In the CRAF IHM‑F notation:

$$d = \sum_{k} -\beta_k \, \Delta h_k(t - \tau_k)$$

The left side is the InSAR‑measured total vertical displacement $d$. The right side is the model prediction constructed from head data. The unknown parameters are the per‑layer storage coefficient $S_k$ (or production coefficient $\beta_k$) and the per‑layer lag $\tau_k$.

### 7.2 Parameterization and physical bounds

Smith et al. (2021) constrain $S_k$ via Eq. F13, linking it to the product of specific storage and compacting thickness:

$$S_{k} = S_{sv} \, b_0$$

Grid‑search bounds are set by combining literature values of $S_{sv}$ (e.g., $2 \times 10^{-6}$ to $2.3 \times 10^{-5}$ m$^{-1}$ for elastic, $10^{-4}$ to $10^{-2}$ m$^{-1}$ for inelastic) with geologic estimates of the total thickness of compressible material within each interval. The CRAF pipeline follows an analogous strategy, with $\beta_k$ bounds calibrated per layer classification.

Smith et al. (2021) solve for three intervals. The CRAF IHM‑F model similarly partitions by stratigraphic layer per MLCW (Multi‑Layer Compaction Monitoring Well) station, yielding independent $\beta_k$ and $\tau_k$ values for each (station, layer) pair.

### 7.3 The nonlinear inverse problem

The inversion minimizes the misfit between observed $d$ and modeled $d$ over all acquisition times. With two parameters per layer ($S_k$, $\tau_k$) and three layers, the problem size is six parameters in Smith et al. (2021). A grid search samples the plausible range and selects the combination minimizing root‑mean‑square error (RMSE). The CRAF IHM‑F implementation extends this to a 4‑fold walk‑forward validation scheme, reserving fold‑1 (2022) as an operational stress test in which MLCW data are reconstructed and no raw observations enter the loss.

---

## 8. Applying the formulas: a step‑by‑step map

| Step | Action | Relevant formula | What the analyst should see |
|---|---|---|---|
| 1. Load head data | Read GWL time series per layer | -- | Feather files indexed by station and well code |
| 2. Load subsidence data | Read InSAR cumulative displacement | Smith F9, F11 | Feather file resampled to 6 epochs/month |
| 3. Compute $\Delta h$ | $h(t) - h_{\text{ref}}$ | -- | Positive = rise, negative = decline (operational sign unchanged) |
| 4. Remove trends | Fit linear trend on calibration window | -- | Detrended GWL, MLCW, and InSAR |
| 5. Assign regime | Compare $h(t)$ to preconsolidation $h_c$ | Section 4.2 | $h_c$ = 10th percentile of calibration‑window head |
| 6. Apply lag | Evaluate $\Delta h(t - \tau_k)$ | Section 5.2, F6 | Lag ranges 0–24 epochs; controlled by clay thickness |
| 7. Compute modeled compaction | $-\beta_k \, \Delta h_k(t - \tau_k)$ | Sections 2, 7.1 | Sum across layers to get total $d$ |
| 8. Optimize | Grid‑search $\beta_k$, $\tau_k$ to minimize RMSE | Section 7.3 | Walk‑forward validation; exit criterion on fold‑1 |
| 9. Export results | Write fitted parameters and predictions | -- | CSV per (station, layer); PNG diagnostics |

---

## 9. Original thickness is not required

The analyst may never know $b_0$. The regressions estimate $S_k = S_{sv} b_0$ as a single number. Knowing $b_0$ is necessary only to recover the specific storage $S_{sv} = S_k / b_0$, which is a secondary diagnostic. For prediction, $S_k$ (or $\beta_k$) is sufficient.

---

## 10. Assumptions and limits of applicability

**Constant overburden stress.** Surface loading from construction, sedimentation, or ice cover changes $\sigma$ independently of head. The formula cannot separate head‑driven from load‑driven compaction.

**Oedometer conditions (zero lateral strain).** Three‑dimensional strain fields near faults or excavation edges reduce the fraction of volume change expressed as vertical displacement.

**Equilibrium pore pressure.** The formula computes ultimate compaction. During consolidation, actual compaction lags behind the equilibrium value by $\tau$ (Section 5). The lag parameter absorbs this effect operationally, but the physical consolidation timescale is quadratic in $b_0$.

**Constant skeletal compressibility.** Real $\alpha$ decreases as effective stress increases. The linear relation is a small‑$\Delta h$ approximation.

**No chemical volume change.** Swelling clays, organic decomposition, pyrite oxidation, and dissolution produce signals that are indistinguishable from head‑driven compaction but have no head‑related mechanism.

**Isothermal, single‑phase flow.** Thermal expansion of pore water and osmotic gradients in clay‑rich media generate pore pressure changes unrelated to head.

**Full saturation.** Above the water table, suction‑driven effective stress changes follow a different constitutive law. The formula does not hold in the vadose zone.

**Unconfined aquifers.** Smith et al. (2021) provide a correction term (Eq. F3) involving specific yield $S_y$:

$$\Delta b_e = \Delta h \left(1 - \frac{S_y}{C_0/C_1}\right) S_{ke}$$

This correction is typically small (~10%). The CRAF model treats all layers as confined, consistent with the first‑order approach in Smith et al. (2021).

---

## 11. Comparison: this study vs. Smith et al. (2021)

| Element | Smith et al. (2021) | This study (CRAF IHM‑F) |
|---|---|---|
| Formula | $\Delta b_e = \Delta h \, S_{ke}$ (Eq. F2) | $\Delta b = -S_k \, \Delta h$ |
| $\Delta b$ sign | Negative = compaction | Positive = compaction (operational) |
| $\Delta h$ sign | Negative = decline | Negative = decline |
| Regime | Elastic only ($h$ stayed above $h_c$) | Elastic and inelastic (two‑regime) |
| Layers | 3 depth intervals | Per‑station MLCW layers (3–5) |
| Lag source | Physically motivated by Eq. F6 | Fitted per layer via grid search |
| Parameterization | $S_{ke}$ bounded by Eq. F13 | $\beta_k$ bounded per layer classification |
| Inversion | Grid search, single‑fold | Grid search, 4‑fold walk‑forward |
| Head data | Nested monitoring wells | GWL timeseries + nearest‑proxy assignments |
| Subsurface validation | None (total InSAR fit only) | MLCW‑measured per‑layer compaction |
| Location | San Joaquin Valley, California | Choushui River Alluvial Fan (CRAF), Taiwan |

---

## 12. Key takeaways

1. **The core physics is linear**: $\Delta b \propto \Delta h$, proportional to a storage coefficient that captures sediment compressibility and layer thickness.
2. **The minus sign in the operational formula** is a sign convention, not a physical statement. It exists so that compaction, subsidence, and head decline all produce positive numbers in plots.
3. **Two regimes matter** when head crosses the preconsolidation threshold. Inelastic storage ($S_{skv}$) is 10–100 times larger than elastic storage ($S_{ske}$).
4. **Compaction lags head change** because clay layers drain slowly. The lag $\tau$ scales with $b_0^2$ and falls with $K_v$.
5. **Total InSAR displacement equals the sum of layer compactions**, enabling depth‑resolved parameter estimation through joint inversion.
6. **Original thickness $b_0$ is not needed** for prediction; it is embedded in the fitted storage coefficient.
