# Kalman Filter Formulation for the M8 Sequential Estimator: Design Analysis

**Date:** 2026-06-12 · **Station:** TUKU pilot · **Scope:** Architectural design discussion  
**Status:** Advisory reference — no code changes enacted. Findings document a design session.

---

## Abstract

The M8 sequential estimator at the TUKU Multi-Layer Compaction Monitoring Well (MLCW) station
reconstructs per-layer compaction timeseries by combining a frozen GNSS surface carrier with
groundwater-level-driven inelastic terms and sparse MLCW datum-reset visits. A prior analysis
identified four structural reasons a standard Kalman filter had not been applied: the 6-layer
carrier matrix has algebraic rank 1 (singular value $\text{SV}_1 = 7.29 \times 10^3$, with
$\text{SV}_{2\text{-}6} < 4 \times 10^{-13}$ relative), the elastic/inelastic regime switch
creates a time-varying transition matrix, the reference date was hardcoded to the InSAR data
epoch rather than derived from data overlap, and no formal covariance budget existed between
field visits. This design discussion examines each objection and resolves three of four. The
elastic/inelastic regime switch does not require an Extended Kalman Filter because the preconsolidation
head $h_c$ and its derived regime mask are computed deterministically from the groundwater level
record before any MLCW measurement arrives. A data-driven reference date defined as the first
epoch of MLCW-GNSS overlap removes the InSAR-era dependency. Collapsing the state vector to a
scalar total column compaction $z(t)$ resolves the rank-1 observability problem entirely and
reduces the Kalman gain to a scalar expression $K = P_{\text{prior}} / (P_{\text{prior}} + R)$.
The M8 level reset is shown to be the correct limit of this scalar Kalman update when $P_{\text{prior}} \gg R$.
The recommended path forward formalizes the scalar Kalman with covariance propagation — an addition
of approximately 30 lines — while retaining the existing frozen calibration coefficients and
per-layer post-decomposition.

---

## 1. Background and Motivation

Land subsidence in the Choushui River Alluvial Fan (CRAF), Taiwan, proceeds through a well-established
causal chain: excessive groundwater extraction reduces hydraulic head in confined aquifer units,
transferring overburden load to the sediment skeleton, increasing effective stress, and driving
inelastic compaction of fine-grained aquitards when effective stress exceeds the preconsolidation
stress threshold. The TUKU station, located in the distal fan zone, records this process across
six hydrogeological layers (F1, T1, F2, T2, F3, F4) via a seven-ring MLCW instrument, with field
visits at irregular intervals ranging from monthly to annual cadence. The M8 sequential estimator
predicts per-layer compaction at 5-day epochs using a frozen GNSS carrier term and layer-specific
groundwater head drivers, resetting its datum to each incoming field measurement.

A Kalman filter represents the statistically optimal linear estimator for a system with Gaussian
process noise and measurement noise. The M8 design session identified four objections to applying
a standard Kalman filter to this system. First, the GNSS carrier matrix mapping the scalar surface
displacement $d(t)$ to six layer compaction values has algebraic rank 1, making a 6-dimensional
state unobservable from a single surface measurement. Second, the elastic/inelastic transition
matrix $F(t)$ changes at every epoch depending on whether the lagged hydraulic head $H(t - \tau)$
sits above or below the preconsolidation head $h_c$, apparently precluding a single fixed $F$.
Third, the reference date `REF_DATE = 2015-01-16` was chosen to coincide with the Sentinel-1
InSAR data start rather than derived from the MLCW-GNSS data overlap, introducing an arbitrary
anchor. Fourth, M8 carries no explicit covariance $P(t)$, so the estimator cannot report how
uncertain its prediction is 18 months after the last field visit relative to 2 months after.
Sections 2 through 5 address each objection in turn.

---

## 2. Pre-Computed Elastic/Inelastic Regime Mask

### 2.1 Physical basis of the regime switch

The CRAF aquifer system at TUKU exhibits two deformation regimes. Elastic compaction occurs when
the lagged effective stress on the fine-grained skeleton remains below the preconsolidation stress,
and the resulting deformation is reversible. Inelastic compaction occurs when lagged effective
stress exceeds the preconsolidation stress, permanently rearranging the skeletal structure of
aquitards and interbeds. The boundary between regimes is the preconsolidation head $h_c$, defined
as the minimum hydraulic head recorded in the GNSS well record prior to the analysis reference
date. At TUKU, 93% of the 1,572 epochs (1,464 epochs) fall in the inelastic regime, meaning the
aquifer system has been continuously compacting beyond its historical stress maximum for the
majority of the observational record.

### 2.2 Deterministic derivation of the regime mask

The preconsolidation head satisfies:

$$h_c = \min \bigl\{ H(s) \;:\; s < t_{\text{ref}} \bigr\}$$

where $H(s)$ denotes the absolute hydraulic head in metres above mean sea level (MSL) at epoch $s$,
and $t_{\text{ref}}$ is the analysis reference date. As the record extends forward in time, any
seasonal minimum that establishes a new low value updates $h_c$ permanently. The running historical
minimum at epoch $t$ is:

$$h_c(t) = \min \bigl\{ H(s) \;:\; s \le t \bigr\}$$

This quantity is computed from the groundwater level (GWL) feather record, which is available in
full before any MLCW field visit arrives. The regime indicator at epoch $t$ with lag $\tau$ is:

$$r(t) = \begin{cases} \text{inelastic} & \text{if } H(t - \tau) < h_c(t - \tau) \\ \text{elastic} & \text{otherwise} \end{cases}$$

Because $H(t)$ is observed continuously and $h_c(t)$ is its running minimum, $r(t)$ is a
deterministic binary quantity computed from observable data. The virgin consolidation term is:

$$V(t) = \min \bigl( 0,\; h_c(t) - H(t) \bigr) \le 0$$

where $V(t) = 0$ identifies elastic epochs and $V(t) < 0$ identifies inelastic epochs. The
implementation in `tau_demo_TUKU/seq/drivers.py` (lines 115–130) computes:

```python
H_for_cummin = pd.Series(H_abs_arr).ffill().values.astype(float)
cummin_full   = np.minimum.accumulate(H_for_cummin)
V_full        = np.minimum(0.0, cummin_full - h_c)
```

Forward-fill is applied before the cumulative minimum to preserve soil memory across
monitoring gaps; missing hydraulic head values do not reset the compaction history the
sediment column has already accumulated.

### 2.3 Implication for Kalman filter formulation

The objection that $F(t)$ changes every epoch applies to a stochastic hybrid system where the
regime is unknown. The TUKU system belongs instead to the class of Switched Linear Systems
(also called Jump-Linear Systems): the switching function $r(t)$ is fully observed in advance
from the GWL record, and the two possible transition matrices $F_{\text{elastic}}$ and
$F_{\text{inelastic}}$ are known constants. At each epoch, the Kalman predict step uses the
appropriate $F(t)$ selected from the precomputed mask array `V_full`. No Extended Kalman Filter,
Unscented Kalman Filter, or linearization is required. The standard Kalman equations apply
piecewise with a known switching sequence.

---

## 3. Data-Driven Reference Date and Preconsolidation Head

### 3.1 Origin of the 2015 reference date

The reference date `REF_DATE = 2015-01-16` was selected to coincide with the first available
Sentinel-1 InSAR acquisition at TUKU, establishing a common zero-reference epoch across InSAR,
GNSS, and MLCW timeseries. The M8 estimator, however, does not use InSAR data as a driver.
M8 uses only the GNSS carrier from the TKJS GPS-modeled file (`data/gps/modeled/TKJS_model.csv`)
and the layer-specific groundwater head from the assigned GWL well. Retaining 2015-01-16 as the
reference date imposes an InSAR-era constraint on a GPS-only estimator and introduces unnecessary
rigidity when deploying to the 37-station network (Objective 2), where MLCW and GNSS data overlap
dates vary by station.

### 3.2 Proposed data-driven rule

The analysis reference date should be defined as:

$$t_{\text{ref}} = \max \bigl( t_{\text{MLCW},0},\; t_{\text{GNSS},0} \bigr)$$

where $t_{\text{MLCW},0}$ denotes the first valid MLCW observation date and $t_{\text{GNSS},0}$
denotes the first valid GNSS data date at the station. The preconsolidation head is then:

$$h_c = \min \bigl\{ H(s) \;:\; s < t_{\text{ref}} \bigr\}$$

using all available GWL feather records prior to $t_{\text{ref}}$. The reference hydraulic head
value for zero-referencing is the last observed $H$ at or before $t_{\text{ref}}$. This rule
applies Bug-F compliance (preconsolidation head computed from pre-reference-date raw feather rows
before zero-referencing) identically to the current implementation, with only the anchor date
changed from a hardcoded constant to a data-derived value.

### 3.3 Implementation and multi-station implication

The function `build_layer_drivers()` in `tau_demo_TUKU/seq/drivers.py` already accepts
`ref_date` as a string parameter. Replacing the hardcoded string with the computed overlap date
requires reading `t_{\text{MLCW},0}$ from the MLCW feather index and $t_{\text{GNSS},0}$ from
the GNSS CSV index, then passing `max(t_MLCW_0, t_GNSS_0).strftime('%Y-%m-%d')` to the function.
No other structural change is needed. For stations where the MLCW record begins well after 2015,
the longer pre-reference GWL history expands the window over which $h_c$ is estimated, reducing
the risk of missing a true historical minimum. For stations where the GNSS record begins after
the MLCW record, the overlap rule automatically delays the reference date to the GNSS start,
consistent with the physical requirement that the carrier driver must exist at time zero.

---

## 4. Single-State Scalar Kalman Formulation

### 4.1 Rank-1 observability and the six-layer inversion problem

The M8 frozen calibration maps the scalar GNSS surface displacement $d(t)$ (mm) to six
per-layer compaction contributions through layer-specific carrier coefficients $a_k$:

$$c_k^{\text{carrier}}(t) = a_k \cdot d(t)$$

The carrier matrix $\mathbf{A} \in \mathbb{R}^{6 \times 1}$ with entries $(a_{F1}, a_{T1}, a_{F2},
a_{T2}, a_{F3}, a_{F4})^{\top}$ has algebraic rank 1 by construction. Singular value decomposition
(SVD) of the carrier block over the 1,081-epoch training window confirms this analytically:
$\text{SV}_1 = 7.29 \times 10^{3}$, with $\text{SV}_{2}$ through $\text{SV}_{6}$ below
$4 \times 10^{-13}$ relative to $\text{SV}_1$. A 6-dimensional Kalman state updated exclusively
from this rank-1 surface signal is unobservable: infinitely many state vectors produce identical
predicted measurements. The amplitude-bound lemma provides a concrete illustration: the seasonal
amplitude of the F2 aquifer compaction timeseries (4.71 mm) exceeds the total surface seasonal
amplitude (3.83 mm), proving geometrically that at least one other layer must partially cancel F2
at the surface. The F2/F3 hydraulic head correlation in the seasonal frequency band reaches
$r = 0.987$, confirming that the two dominant contributors cannot be separated from the combined
surface signal. Per-layer inversion from one surface observation is therefore non-unique, regardless
of filter architecture.

### 4.2 Scalar state formulation

Defining the state as total column compaction $z(t)$ (mm) eliminates the observability problem.
The scalar state satisfies:

$$z(t) = \sum_{k} c_k(t)$$

where the sum runs over all six layers. The frozen total carrier coefficient is:

$$a = \sum_{k} a_k = 0.559$$

as recorded in `tau_demo_TUKU/results/seq/frozen_calibration.json`. The state transition model is:

$$z(t) = z(t-1) + a \cdot \Delta d(t) + S_{\text{col}} \cdot V_{\text{lag}}(t) + w(t)$$

where $\Delta d(t) = d(t) - d(t-1)$ is the GNSS surface displacement increment (mm), $V_{\text{lag}}(t)$
is the column-level virgin consolidation term (the signed sum of per-layer $V_k$ terms weighted by
compressible thickness), $S_{\text{col}}$ is an aggregate inelastic skeletal storage parameter
(m$^{-1}$ per unit layer thickness), and $w(t) \sim \mathcal{N}(0, Q)$ is process noise with
empirically estimated variance $Q \approx (2\text{–}3\;\text{mm})^2$ per 5-day epoch, derived from
GNSS carrier residuals.

The measurement model at each MLCW field visit epoch $t_j$ is:

$$z_{\text{obs}}(t_j) = z(t_j) + v_j, \quad v_j \sim \mathcal{N}(0, R)$$

where $R \approx (1\text{–}2\;\text{mm})^2$, consistent with the 1 mm integer-ring precision of
magnetic-extensometer MLCW readings. The Kalman gain at each visit is the scalar:

$$K = \frac{P_{\text{prior}}}{P_{\text{prior}} + R}$$

and the covariance update is $P_{\text{post}} = (1 - K)\, P_{\text{prior}}$. Between visits,
$P(t) = P(t-1) + Q$ at every 5-day epoch.

### 4.3 Three formulation options

**Option A (recommended): Scalar total column $z(t)$.** The state is the full cumulative column
compaction. The transition model uses $\sum_k a_k = 0.559$ directly. No retraining is required;
the existing frozen calibration supplies all coefficients. Per-layer decomposition is recovered
as a post-processing step (Section 5.2). This option is deployable immediately to all 37 stations
that have a frozen calibration file.

**Option B: Detrended residual $z_{\text{res}}(t)$.** The GNSS carrier trend is subtracted first:
$z_{\text{res}}(t) = z(t) - a \cdot d(t)$. The state then tracks only the groundwater-head-driven
oscillation, which has amplitude approximately 10–30 mm over the record compared to the 300–500 mm
total column. This formulation reduces process noise variance and may improve numerical conditioning,
but requires careful handling of the secular drift component during the MLCW datum-reset step.

**Option C: Hierarchical global-plus-layer-offsets.** The scalar $z(t)$ is tracked by the Kalman
filter as in Option A, while per-layer perturbations $\epsilon_k(t) = c_k(t) - a_k \cdot z(t) /a$
are regularized toward zero via a ridge-type prior. This option produces per-layer uncertainty
bands directly from the Kalman covariance structure, at the cost of expanding the state to a
$(6+1)$-dimensional system and requiring a block-diagonal covariance matrix. The observability of
the perturbations $\epsilon_k$ is not guaranteed from MLCW column measurements alone.

### 4.4 What the scalar formulation gains and loses

The scalar formulation gains: formal, time-varying uncertainty quantification with $P(t)$ growing
at rate $Q$ between visits and contracting by factor $(1-K)$ at each visit; closed-form Kalman gain
requiring no matrix inversion; and a fully observable system from the MLCW column total measurement.
The scalar formulation loses: the ability to directly constrain per-layer compaction individually
without post-decomposition. The per-layer decomposition (Section 5.2) can recover individual layer
estimates but cannot independently propagate per-layer uncertainty tighter than the column total.
For stations where the primary deliverable is the total column budget rather than per-layer
attribution, Option A provides a complete solution. For stations where per-layer attribution is
required at publication quality, Option C or independent per-layer piezometer data are needed.

---

## 5. M8 as an Implicit Scalar Kalman Filter

### 5.1 The level-reset step as the Kalman update limit

The M8 estimator resets its per-layer compaction prediction to each incoming MLCW field value at
the visit epoch. This reset is operationally equivalent to setting the Kalman gain $K = 1$ and
assigning the full posterior state to the observation:

$$z_{\text{post}}(t_j) = z_{\text{obs}}(t_j)$$

The Kalman gain $K = P_{\text{prior}} / (P_{\text{prior}} + R)$ equals 1 in the limit
$P_{\text{prior}} \gg R$. This limit arises naturally when the estimator runs many epochs without
an observation: $P_{\text{prior}} = P_0 + n_{\text{gap}} \cdot Q$, which grows without bound as
the gap length $n_{\text{gap}}$ increases. For a typical annual cadence with $n_{\text{gap}} \approx 73$
epochs (365 days at 5-day spacing) and $Q \approx 9\;\text{mm}^2$, $P_{\text{prior}} \approx 657\;\text{mm}^2$,
which exceeds $R \approx 4\;\text{mm}^2$ by a factor of 164. At that ratio, $K = 0.994$, confirming
that the hard reset is the numerically correct behavior for annual-cadence updates. The M8 level
reset is therefore not an ad hoc engineering choice but the statistically optimal Kalman update
for a long-gap sparse-observation system.

### 5.2 The missing covariance propagation

M8 does not propagate a covariance $P(t)$. The consequence is that the estimator cannot report
how uncertain its prediction is as a function of time since the last MLCW visit. The conformal
prediction bands computed in M8 are empirically derived from historical residuals and remain
constant regardless of visit cadence. Adding explicit covariance propagation requires:

1. Initializing $P_0$ at the first calibration epoch (e.g., $P_0 = R$, fully anchored to the datum).
2. At every 5-day epoch without an MLCW observation: $P(t) \leftarrow P(t-1) + Q$.
3. At every MLCW visit epoch $t_j$: compute $K = P(t_j^-) / (P(t_j^-) + R)$, update
   $z_{\text{post}} \leftarrow z(t_j^-) + K(z_{\text{obs}} - z(t_j^-))$, set
   $P_{\text{post}} \leftarrow (1 - K)\, P(t_j^-)$.
4. Report the 90% prediction interval as $z_{\text{post}} \pm 1.645\,\sqrt{P(t)}$.

This implementation requires approximately 30 lines and does not alter the predicted mean $z(t)$
for the hard-reset (annual-cadence) regime. The modification adds formally correct, time-varying
uncertainty bounds that grow with inter-visit gap length.

### 5.3 Per-layer decomposition as post-processing

Once the scalar state $z(t)$ is tracked by the Kalman filter, per-layer compaction estimates
are recovered by the frozen proportional allocation:

$$\hat{c}_k(t) = \frac{a_k}{a} \cdot z(t) + S_{skv,k} \cdot V_{\text{lag},k}(t) \cdot b_k$$

where $a_k / a$ is the frozen GPS carrier share (F2: $0.203 / 0.559 = 0.363$; F3: $0.270 / 0.559 =
0.483$; etc.), $S_{skv,k}$ is the frozen inelastic skeletal specific storage coefficient
(m$^{-1}$) for layer $k$, $V_{\text{lag},k}(t)$ is the layer-specific lagged virgin consolidation
term, and $b_k$ is the compressible thickness of layer $k$ (m). The per-layer uncertainty is
bounded below by the column total uncertainty: $\sigma_{c_k} \ge (a_k / a) \cdot \sqrt{P(t)}$.

---

## 6. Summary and Recommended Path Forward

### 6.1 Resolution of the four original objections

| Objection | Status | Resolution |
|---|---|---|
| Carrier matrix rank = 1; 6-state unobservable | Resolved | Collapse to scalar state $z(t) = \sum_k c_k(t)$; rank-1 state is fully observable from scalar MLCW total |
| $F(t)$ changes every epoch (elastic/inelastic switch) | Resolved | $F(t)$ is precomputed from GWL record via $V_{\text{full}}$; Switched Linear System with fully observed switching requires no EKF |
| Reference date 2015-01-16 is an InSAR-era artifact | Resolved | Replace with $t_{\text{ref}} = \max(t_{\text{MLCW},0}, t_{\text{GNSS},0})$; no structural code change needed |
| No formal covariance $P(t)$; uncertainty is static | Partially resolved (design) | Add scalar $P(t)$ propagation (${\sim}$30 lines); M8 level reset is proven to be the correct Kalman limit |

### 6.2 Recommended implementation sequence

Four steps achieve the full Kalman formalization with no new calibration:

1. **Replace `REF_DATE`**: in `tau_demo_TUKU/seq/drivers.py`, compute `ref_date` as
   `max(first_MLCW_date, first_GPS_date)` from the station's data files.

2. **Add scalar Kalman tracker**: in the M8 sequential estimator
   (`tau_demo_TUKU/seq/`), add a `KalmanTracker` class with scalar state $z$, scalar covariance
   $P$, process noise $Q \approx 9\;\text{mm}^2$, and measurement noise $R \approx 4\;\text{mm}^2$.
   The predict step runs at every 5-day epoch; the update step runs only at MLCW visit epochs.

3. **Replace conformal prediction bands with Kalman prediction intervals**: the 90%
   prediction interval $z(t) \pm 1.645\,\sqrt{P(t)}$ replaces the static empirical conformal
   bands for total-column uncertainty reporting. The conformal bands remain valid for per-layer
   reporting until Option C is implemented.

4. **Post-decompose to layers**: apply the frozen proportional allocation
   $\hat{c}_k(t) = (a_k / a) \cdot z(t) + S_{skv,k} \cdot V_{\text{lag},k}(t) \cdot b_k$
   to produce per-layer estimates from the scalar Kalman output.

### 6.3 Scope and constraints

These four steps apply to the TUKU pilot station immediately. Extension to all stations in
Objective 2 requires a frozen calibration file for each station (currently available for 29 of
37 stations per `m5_deployment/station_file_map.json`). Stations with fewer than 300 epochs
of MLCW-GNSS overlap were excluded from calibration and remain outside the deployable set.
The F3 aquitard at TUKU warrants a separate caveat: the assigned GWL well (`09050331`, screen
depth 176–179 m) is 79 m shallower than the compacting clay interval (238–275 m), and the
detrended seasonal cross-correlation reaches only $|r| = 0.10$. The scalar Kalman tracker correctly
absorbs F3 uncertainty into the column total, but the per-layer F3 decomposition carries
unquantifiable error until a co-screened piezometer at depth 240–275 m is installed or a modeled
deep hydraulic head product (e.g., MODFLOW-CSUB) is available.

---

## Evidence Base

`tau_demo_TUKU/results/seq/frozen_calibration.json` (carrier coefficients and layer calibration)  
`tau_demo_TUKU/seq/drivers.py` (V_full regime mask, lines 115–130)  
`discussions/FEASIBILITY_VERDICT_FINAL_20260611.md` (SVD rank-1 proof, amplitude-bound lemma)  
`discussions/SEQ_REHEARSAL_FINDINGS_20260611.md` (M8 sequential estimator findings)  
`discussions/F3_FORENSIC_VERDICT_20260612.md` (F3 screen-depth mismatch and driver quality)  
`audit_red_team_v2/RED_TEAM_VERDICT_20260611.md` (level reset as datum-only correction)

*Status: design reference only. No code modified. Implementation blocked pending Objective 1 validation gate.*
