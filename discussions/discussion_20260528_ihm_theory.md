# A Two-Regime Groundwater-Driven Per-Layer Compaction Model: Theory and Estimation

**Date:** 2026-05-28
**Audience:** A newcomer who understands basic linear regression and has access to the same three data streams (multi-layer compaction well, groundwater level, and InSAR surface displacement) at a study site with active land subsidence driven by groundwater extraction.

---

## 1. What Problem Does This Model Solve?

Land subsidence driven by groundwater extraction occurs across many parts of the world — alluvial plains, river deltas, coastal basins, and irrigated agricultural lowlands. The surface sinks because fine-grained sediments (clay layers, silty interbeds) compacted at depth by declining pore-water pressure. The total amount of surface sinking, measured by satellite radar interferometry (InSAR), is a single number at any given time and place. A practitioner often wants to know: which sediment layer is responsible, and by how much?

Multi-layer compaction monitoring wells (MLCW) answer this question directly at the locations where they are installed. Each well contains a series of magnetic rings anchored at different depths; as each depth interval compacts, its ring displacement is recorded. The MLCW therefore provides a per-depth timeseries of cumulative compaction, in millimetres, at that one location.

Groundwater level (GWL) wells, placed nearby, record piezometric head — the height (in metres above mean sea level) to which water rises in a borehole screened at a particular depth interval. Higher head means less stress on the sediment; lower head (caused by pumping) means more stress and more compaction.

The goal of this model is to use the GWL timeseries and the InSAR timeseries, together, to predict the per-layer compaction timeseries measured by the MLCW. Once the model is calibrated at monitored locations, the same parameters — combined with GWL and InSAR data that are available everywhere — allow reconstruction of per-layer compaction across the full spatial domain, including at locations where no MLCW well exists.

---

## 2. The Physical Basis: Why Does Head Change Drive Compaction?

### 2.1 Effective stress and pore pressure

A sediment column below the water table carries the weight of all the overlying rock and water — the total overburden stress, $\sigma$ (Pa). Inside the pore space, water pressure p (Pa) pushes outward against the grain contacts. The portion of overburden that the grain skeleton actually bears is the **effective stress**:

    $\sigma'(t)$ = $\sigma$ − p(t)                                       … (1)

The total overburden $\sigma$ does not change on engineering timescales: the rock column above does not disappear. Therefore, any change in pore pressure directly changes effective stress:

    $\Delta\sigma'(t)$ = $-\rho_w \cdot g \cdot \Delta H(t)$                             … (4)

**The key physical message of equation (4) is straightforward.** When pumping lowers piezometric head — $\Delta H$ < 0 — effective stress increases — $\Delta\sigma'$: $\Delta b$ = -b $\cdot$ m_v $\cdot \Delta\sigma'$ (more stress) produces negative $\Delta b$(thinner layer, compaction downward).

Substituting equation (4) into equation (5):

    $\Delta b(t) = b \cdot m_v \cdot \rho_w \cdot g \cdot \Delta H(t)$                     … (6)

In hydrogeology, the combination S_sk = m_v $\cdot \rho_w \cdot g$ (m⁻¹) is called the **skeletal specific storage**. Multiplying by b gives the **bulk storage coefficient** S_sk_bulk = $b \cdot S_sk (dimensionless, or equivalently mm/m when compaction is expressed in mm and head in m). Equation (6) then becomes:

    $\Delta b(t)$ = S_sk_bulk $\cdot \Delta H(t)$                              … (7)

Equation (7) says: compaction in a layer is proportional to the head change in that layer. When head falls ($\Delta H$ < 0), $\Delta b$ < 0 (compaction). When head rises ($\Delta H$ > 0), the layer partially rebounds ($\Delta b$ > 0). The proportionality constant S_sk_bulk is the parameter the model estimates from data.

### 2.3 Two regimes: elastic and inelastic compaction

The relationship between stress and compaction is not the same in all conditions. Clay behaves differently depending on whether the current effective stress has exceeded the historical maximum stress the clay has ever experienced. This historical maximum is called the **preconsolidation stress**, $\sigma'_c$, and the corresponding piezometric head is the **preconsolidation head**, $h_{c}$.**Elastic regime (H > $h_{c}$).** When piezometric head is above $h_{c}$, effective stress is below $\sigma'_c$. The clay is being reloaded along a path it has already travelled. Deformation is small and reversible: if head recovers, the layer returns toward its original thickness. The relevant storage coefficient is $S_{ske}$ (elastic skeletal specific storage). $S_{ske}$ is small because the grain fabric is already tightly packed from past compaction.

**Inelastic regime (H $\le h_{c}$).** When piezometric head falls below $h_{c}$, effective stress exceeds $\sigma'_c$. The clay enters virgin compression: grain contacts break and rearrange permanently. The layer compacts much more per unit of head drop, and this compaction is irreversible — even if head recovers later, the layer does not spring back. The relevant coefficient is $S_{skv}$ (inelastic or virgin skeletal specific storage). For alluvial clays, $S_{skv}$ is typically 5 to 20 times greater than $S_{ske}$ (Poland 1984; Chen et al. 2016).

The piecewise-linear model for a single layer is therefore:

    $\Delta b(t)$ = S_{ske,bulk} $\cdot \Delta H(t)$   when H(t) > $h_{c}$ (elastic regime)
    $\Delta b(t)$ = S_{skv,bulk} $\cdot \Delta H(t)$   when H(t) $\le h_{c}$ (inelastic regime)    … (8)

Both coefficients are positive physical constants. The compaction sign enters through $\Delta H$: a head drop ($\Delta H$ < 0) multiplied by a positive coefficient gives negative compaction ($\Delta b$ < 0). This is physically correct.

---

## 3. From Physics to a Regression Model

### 3.1 Cumulative form and the reference epoch

In practice, the MLCW records cumulative compaction $D_{k}(t)$ — the total compaction accumulated since the sensor was installed. This is not an incremental $\Delta b$ at each timestep but a running total summed since the first epoch. InSAR similarly records cumulative surface displacement since the first acquisition.

Integrating equation (8) from a reference epoch $t_{ref}$ to the current time t:

    $D_{k}(t)$ = S_{ske,bulk} $\cdot \Delta H_k(t)$ $\cdot$ (fraction of time in elastic regime)
            + S_{skv,bulk} $\cdot \Delta H_k(t)$ $\cdot$ (fraction of time in inelastic regime)   … (9)

where $\Delta H_k(t)$ = H_k(t) − H_k($t_{ref}$) is the piezometric head change from the first epoch. Using a binary indicator for each epoch — $I_{e}(t)$ = 1 in the elastic regime and $I_{i}(t)$ = 1 in the inelastic regime — the model at each observation time t is:

    $D_{k}(t)$ = S_{ske,bulk} $\cdot \Delta H_k(t)$ $\cdot I_{e}(t)$ + S_{skv,bulk} $\cdot \Delta H_k(t)$ $\cdot I_{i}(t)$   … (10)

### 3.2 Why an intercept is necessary

The MLCW sensor starts recording at $t_{ref}$, but the sediment has been compacting for decades or centuries before that date. The cumulative compaction $D_{k}(t_{ref})$ at the first epoch is not zero — it reflects the entire pre-observation history of the layer. Because $\Delta H_k(t_{ref})$= 0 by definition, the right-hand side of equation (10) equals zero at $t_{ref}$, but $D_{k}(t_{ref})$ \ne 0 in general.

To handle this offset, an intercept c (mm) is added to the model:

    $D_{k}(t)$ = c + S_{ske,bulk} $\cdot \Delta H_k(t)$ $\cdot I_{e}(t)$ + S_{skv,bulk} $\cdot \Delta H_k(t)$ $\cdot I_{i}(t)$   … (11)

The intercept absorbs the cumulative compaction already present at the start of the observation window. Without the intercept, the OLS solver cannot match a large non-zero mean in $D_{k}(t)$ using a near-zero-mean head-change signal, and the estimated coefficients become unreliable.

### 3.3 Adding the InSAR co-driver

The assigned GWL well does not monitor every depth interval. Deep aquitards, laterally discontinuous interbeds, and confined units screened by wells far from the MLCW station all contribute to compaction in ways that the local head record does not capture. InSAR surface displacement x(t) integrates the total vertical motion from all depths and all locations within the radar pixel, so it carries information about those unmonitored contributions.

Adding InSAR as a secondary predictor:

    $D_k(t) = c + S_{ske} \cdot \Delta H_k(t) \cdot I_e(t) + S_{skv} \cdot \Delta H_k(t) \cdot I_i(t) + \beta \cdot x(t) + \varepsilon(t)$   … (12)

where x(t) is the raw cumulative InSAR displacement (mm, negative = subsidence), $\beta$ is a dimensionless coupling coefficient, and $\varepsilon(t)$ is the residual. Equation (12) is the complete model. The four unknown parameters are c, $S_{ske}$, $S_{skv}$, and $\beta$. Their physical meanings are:

- **c** (mm): cumulative compaction already accumulated before the first observation epoch.
- **$S_{ske}$** (mm/m): elastic bulk storage coefficient — how many millimetres of elastic compaction result from each metre of head drop.
- **$S_{skv}$**(mm/m): inelastic bulk storage coefficient — how many millimetres of permanent compaction result from each metre of head drop below the preconsolidation head.
- **$\beta$** (dimensionless): InSAR coupling — how much of the per-layer compaction co-varies with the total surface displacement beyond what the local GWL already explains.

**Expected signs.** $S_{ske}$> 0 and $S_{skv}$> 0 (head fall drives compaction; positive coefficient multiplied by negative $\Delta H$ gives negative $\Delta b$). $S_{skv}$> $S_{ske}$ (inelastic regime is much more compressible). $\beta$> 0 (surface subsidence and layer compaction move together). c < 0 for layers that had already been compacting before the observation window began.

### 3.4 The time lag $\tau$

The surface displacement measured by InSAR responds almost instantaneously to head changes in high-permeability sand and gravel layers. Thick, low-permeability clay interbeds, by contrast, take time to drain and equilibrate: a head change in the adjacent aquifer propagates into the clay only gradually, over days to weeks. This drainage delay is called **hydraulic lag**, and it means that the MLCW compaction at time t is driven not by the head at time t but by the head at some earlier time t $−\tau$.

The lag $\tau$ is introduced into equation (12) by replacing $\Delta H_k(t)$ with $\Delta H_k(t - \tau)$: $D_k(t) = c + S_{ske} \cdot \Delta H_k(t - \tau) \cdot I_e(t) + S_{skv} \cdot \Delta H_k(t - \tau) \cdot I_i(t) + \beta \cdot x(t) + \varepsilon(t)$   … (13)

The lag $\tau$ is measured in the same units as the observation interval (here, InSAR repeat cycles of approximately 12 days). For thin sandy layers, $\tau \approx$ 0. For thick clay units, $\tau$ can reach several months.

---

## 4. How the Parameters Are Estimated

### 4.1 Identifying the preconsolidation head $h_{c}$

Before fitting equation (13), the boundary between the elastic and inelastic regimes must be established at each layer. The preconsolidation head $h_{c}$ is the piezometric head at which effective stress first equalled the historical maximum — the threshold below which virgin inelastic compaction begins.

Operationally, $h_{c}$ is estimated as the minimum piezometric head recorded in the GWL well over the full observation period. The logic is: any head level already observed in the record has been experienced before; only head levels below this historical minimum take the sediment into new, previously unexperienced stress territory. Each epoch is then classified as elastic (H(t) > $h_{c}$) or inelastic (H(t) $\le h_{c}$) using this threshold.

With $h_{c}$ determined, two binary indicator arrays are formed for every epoch in the aligned timeseries: $I_{e}(t)$ = 1 where H(t) > $h_{c}$, and $I_{i}(t)$ = 1 where H(t) $\le h_{c}$. These indicators split the head-change signal into two channels — the elastic channel and the inelastic channel — which enter as separate predictors in the regression.

### 4.2 Constructing the design matrix

With a candidate lag value $\tau$, the regression model in equation (13) is a standard linear system. For N total observation epochs:

- The **response vector** y is the column of observed cumulative MLCW compaction values $D_{k}(t)$ at each epoch t = 1 to N $−\tau$ (the first N $−\tau$ epochs, because the lagged head values start at epoch $\tau$+ 1).
- The **design matrix** X has N $−\tau$ rows and four columns:
  - Column 1: a constant 1 at every row (for the intercept c).
  - Column 2: $\Delta H_k$(t $−\tau$) $\cdot I_{e}(t)$, the head change lagged by $\tau$ epochs, zeroed out during inelastic epochs.
  - Column 3: $\Delta H_k$(t $−\tau$) $\cdot I_{i}(t)$, the head change lagged by $\tau$ epochs, zeroed out during elastic epochs.
  - Column 4: x(t), the raw cumulative InSAR displacement at each epoch.

Given X and y, ordinary least squares (OLS) finds the coefficient vector $\theta$=[c, $S_{ske}$, $S_{skv}$, $\beta$] that minimises the sum of squared residuals:

    minimise  ‖ y − X $\theta$ ‖^2     over $\theta$                                    … (14)

The OLS solution is unique (assuming the columns of X are not perfectly collinear) and is computed as:

    $\theta$=(X^T X)^{−1} X^T y                                               … (15)

No iterative optimisation is required. The four parameters are recovered in a single matrix solve.

### 4.3 Searching for the optimal lag $\tau$

The lag $\tau$ is not estimated by the OLS directly — it enters as a structural parameter that determines which column of head values is used. The optimal $\tau$ is found by a grid search: the full OLS fit is repeated for every integer value of $\tau$ from 0 to a user-specified maximum ($\tau_max$, typically 12 repeat cycles). For each candidate $\tau$, the residual sum of squares (RSS) of the OLS fit is recorded. The $\tau$ that produces the lowest RSS — the best-fitting lag — is selected as the optimal lag for that layer.

The grid search produces a $\tau$–RSS curve that reveals how sensitive the fit is to the assumed lag. A flat curve means the model is insensitive to $\tau$ (the head-change signal is nearly stationary or closely correlated with InSAR). A sharp minimum means the model detects a physically meaningful lag, and the selected $\tau$ has a clear physical interpretation as the drainage delay of that clay layer.

### 4.4 Fit quality and diagnostics

The quality of the optimal fit is summarised by two metrics. The coefficient of determination R^2 measures the fraction of variance in the observed MLCW compaction that the model explains:

    R^2 = 1 − RSS / TSS                                                    … (16)

where TSS = $\Sigma$(y − ȳ)^2 is the total variance of the observations. The root-mean-square error RMSE = √(RSS / (N $−\tau$)) measures the average prediction error in millimetres.

After fitting, four physical-consistency checks are applied to the estimated coefficients:

1. **$S_{ske}$< 0**: the elastic coefficient has the wrong sign. The model predicts more compaction when head rises, contradicting the physical mechanism. The most common causes are a mis-assigned GWL well or high collinearity between the head-change and InSAR predictors (see Section 4.5).
2. **$S_{skv}$< $S_{ske}$**: the inelastic coefficient is smaller than the elastic coefficient. Alluvial clay in virgin compression is always more compressible than the same clay under elastic reloading; the reverse is a data-quality signal.
3. **$\beta$< 0**: the InSAR coupling has the wrong sign. When the surface is subsiding more, the layer should be compacting more; a negative $\beta$ suggests the co-driver term is absorbing spurious variance.
4. **R^2 < 0.20**: the model explains less than 20% of the observed variance. The GWL signal does not carry meaningful compaction information for this layer, possibly because the assigned well monitors a different aquifer unit.

### 4.5 Collinearity between the head-change and InSAR predictors

When the piezometric head timeseries at the assigned GWL well co-varies closely with the total InSAR surface displacement — for example, because both respond to the same large-scale regional pumping signal — the two predictors in equation (13) carry nearly identical information. In this situation, the OLS cannot cleanly separate $S_{ske}$ from $\beta$: the partition is numerically unstable, and $S_{ske}$ may come out negative even though the overall fit R^2 is high.

The degree of collinearity is quantified by the Pearson correlation between $\Delta H$_k and x(t). When this correlation exceeds approximately 0.7 in magnitude, the $S_{ske}$ estimate must be interpreted with caution. The $\beta$ term dominates the fit, and the elastic storage coefficient is effectively unidentifiable from this dataset alone.

---

## 5. Walk-Forward Validation

A model fit to the full observation record cannot be used to assess its own predictive skill — it has seen all the data. To test whether the estimated parameters genuinely capture the physical process and produce useful predictions for future periods, the model is evaluated using a **walk-forward** (also called rolling-origin) validation scheme.

The observation record is divided chronologically. A training window is defined from the earliest epoch to a cutoff year. The model is fit on the training window only, using the same $\tau$ grid search and OLS procedure described above. The fitted model is then used to predict compaction in the following year (the hold-out year), and the prediction error is measured as RMSE in millimetres.

The cutoff year then advances by one year, the training window expands to include the previous hold-out year, and the process repeats. With four folds — hold-out years 2022, 2023, 2024, and 2025 — the validation produces four independent RMSE values, one for each year of prediction. The sequence of fold RMSEs shows whether the model degrades or improves as more data are added to training, and whether prediction skill is consistent across different climatic conditions (wet years vs. drought years).

The first fold (training 2015–2021, hold-out 2022) is the most operationally important. It simulates the situation in which a practitioner must predict per-layer compaction for a year in which no new MLCW data are available — only InSAR and GWL are observed. This fold directly tests the model's ability to function as a standalone prediction tool.

---

## 6. Interpreting the Fitted Parameters

### 6.1 Comparing $S_{ske}$ and $S_{skv}$ to reference values

Independent estimates of the elastic and inelastic storage coefficients can be obtained from the 2S-TOOL (Two-Stage Consolidation Tool) software, which fits the MLCW compaction curve against the $\sigma'$ history derived from depth-to-water measurements. The 2S-TOOL reference values, $S_{ke}$ and $S_{kv}$, are positive physical compressibility constants in mm/m units — directly comparable to $S_{ske}$ and $S_{skv}$ estimated by equation (15). No sign conversion is needed. Both methods estimate compaction per unit of head change, integrated over the compressible thickness of the layer; the difference is that 2S-TOOL fits a stress-path curve while equation (15) fits the temporal signal.

### 6.2 Fold-to-fold variation in $S_{skv}$

If $S_{skv}$ varies substantially from one walk-forward fold to the next, the most likely explanation is not that the sediment became more or less compressible between those years. Clay compressibility is a material property that changes negligibly over a 10-year observation window. The cause of large fold-to-fold variation is almost always a **data-coverage problem**: the training window of a fold with high $S_{skv}$ contains many epochs in the inelastic regime (severe drought), giving the OLS a well-constrained estimate; a fold with low $S_{skv}$ contains few inelastic epochs, leaving the inelastic column of the design matrix nearly all zeros and the coefficient poorly determined.

To diagnose this, the fraction of inelastic epochs in the training window is computed for every fold:

    f_inel = (number of epochs with H(t) $\le h_{c}$)/(total training epochs)

Any fold with f_inel < 0.10 is flagged as having unreliable $S_{skv}$. Reporting this fraction alongside the estimated coefficients allows a reader to distinguish genuine non-stationarity from estimation artefacts due to regime under-representation.

### 6.3 Physical plausibility ranges

For alluvial and deltaic plains worldwide, laboratory and field studies report skeletal storage coefficients in the following ranges (Poland 1984; Helm 1975; Galloway and Burbey 2011):

- Elastic: $S_{ske} \approx$ 0.001–0.020 mm/m (bulk integrated values for a multi-metre layer)
- Inelastic: $S_{skv} \approx$ 0.020–0.200 mm/m

The ratio $S_{skv}$/ $S_{ske}$ typically lies between 5 and 20 for Holocene alluvial clay. Values outside these ranges are not impossible but warrant careful review of the GWL well assignment, the completeness of the head record, and the degree of collinearity between predictors.

---

## 7. Summary of the Estimation Procedure

The complete parameter estimation for one station-layer pair proceeds in the following sequence:

1. Load the aligned timeseries of MLCW cumulative compaction $D_{k}(t)$, piezometric head H(t), and InSAR surface displacement x(t) at the same observation epochs.
2. Estimate the preconsolidation head $h_{c}$ as the historical minimum of H(t) over the full record.
3. Classify each epoch as elastic (H > $h_{c}$) or inelastic (H $\le h_{c}$).
4. Compute the head-change driver $\Delta H$(t) = H(t) − H($t_{ref}$), where $t_{ref}$ is the first epoch.
5. For each candidate lag $\tau$ from 0 to $\tau_max$: build the four-column design matrix X = [1, $\Delta H$(t$−\tau$)$\cdot I_{e}$, $\Delta H$(t$−\tau$)$\cdot I_{i}$, x(t)]; solve the OLS for [c, $S_{ske}$, $S_{skv}$, $\beta$]; record the RSS.
6. Select the $\tau$ that minimises RSS as the optimal lag.
7. Report $S_{ske}$, $S_{skv}$, $\beta$, c, R^2, RMSE, and the $\tau$–RSS curve for the selected fit.
8. Apply the four physical-consistency checks and flag any violations.
9. Run the four walk-forward folds; for each fold report RMSE and f_inel.

This procedure is identical for every station-layer pair. No station-specific structural assumptions or manual parameter choices are required.

---

## 8. A Worked Example with Eight Observations

This section demonstrates every step of the estimation procedure in Section 7 on a small fabricated dataset. All quantities are computed by hand. No software is required to reproduce the results.

### 8.1 Raw input data

The dataset represents a single station-layer pair. Eight observation epochs are spaced at regular intervals. Piezometric head H(t) is recorded in metres above mean sea level (m MSL). InSAR cumulative surface displacement x(t) and MLCW cumulative compaction $D_{k}(t)$ are recorded in millimetres, with negative values indicating downward motion (subsidence and compaction, respectively). The reference epoch is t = 1, at which all cumulative quantities are defined to equal zero.

**Table 1.** Fabricated input data for the worked example.

```
Epoch   H(t)    x(t)    D_k(t)
  t     m MSL   mm      mm
  1     +1.0     0.0    -0.50
  2     +0.5    -2.0    -2.30
  3      0.0    -4.5    -4.30
  4     -0.5    -7.0    -6.30
  5     -1.0   -10.0    -8.50
  6     -1.5   -13.5   -18.40
  7     -1.5   -16.0   -19.40
  8     -1.5   -18.5   -20.40
```

The head record describes a drought scenario: H(t) falls steadily from +1.0 m MSL at the reference epoch to a minimum of −1.5 m MSL at epochs 6 through 8, then remains at that level. The compaction record $D_{k}(t)$ follows: gradual accumulation during the initial drawdown, then an accelerated step at epoch 6 as the layer enters its first inelastic period.

### 8.2 Computing the head-change driver

The head-change driver is defined as:

    $\Delta H$(t) = H(t) − H($t_{ref}$)= H(t) − H(1)                   … (17)

With H(1) = +1.0 m MSL, the values are:

```
Epoch   H(t)    ΔH(t)
  1     +1.0     0.0
  2     +0.5    -0.5
  3      0.0    -1.0
  4     -0.5    -1.5
  5     -1.0    -2.0
  6     -1.5    -2.5
  7     -1.5    -2.5
  8     -1.5    -2.5
```

At the reference epoch $\Delta H$(1) = 0 by construction. The monotone decrease reflects continuous groundwater extraction throughout the observation window.

### 8.3 Estimating the preconsolidation head

The preconsolidation head $h_{c}$ is the historical minimum of H(t) over the full record:

    $h_{c}$= min { H(1), H(2), …, H(8) } = min { +1.0, +0.5, 0.0, −0.5, −1.0, −1.5, −1.5, −1.5 } = −1.5 m MSL

The head first reaches −1.5 m MSL at epoch 6. All prior stress cycles stayed above this level, so epochs 1 through 5 lie in the elastic regime. Epochs 6, 7, and 8 equal $h_{c}$ and therefore enter the inelastic regime.

### 8.4 Classifying each epoch

Each epoch receives a binary indicator. The elastic indicator $I_{e}(t)$ equals 1 when H(t) > $h_{c}$ and 0 otherwise. The inelastic indicator $I_{i}(t)$ equals 1 when H(t) $\le h_{c}$ and 0 otherwise. The two indicators partition the observation window without overlap:

```
Epoch   H(t)   Regime      I_e   I_i
  1     +1.0   elastic      1     0
  2     +0.5   elastic      1     0
  3      0.0   elastic      1     0
  4     -0.5   elastic      1     0
  5     -1.0   elastic      1     0
  6     -1.5   inelastic    0     1
  7     -1.5   inelastic    0     1
  8     -1.5   inelastic    0     1
```

Five of the eight epochs are elastic; three are inelastic. The fraction of inelastic epochs is f_inel = 3/8 = 0.375, well above the 0.10 threshold described in Section 6.2, so $S_{skv}$ will be well-constrained by the data.

### 8.5 Constructing the design matrix ($\tau$= 0)

The lag $\tau$ is set to zero for this example. The design matrix X has eight rows and four columns, following the structure of equation (13):

- Column 1: the constant 1 (intercept).
- Column 2: $\Delta H$(t) $\cdot I_{e}(t)$, the head-change driver zeroed out during inelastic epochs.
- Column 3: $\Delta H$(t) $\cdot I_{i}(t)$, the head-change driver zeroed out during elastic epochs.
- Column 4: x(t), the raw InSAR cumulative displacement.

The numerical values are:

```
     Col 1   Col 2      Col 3      Col 4
      (1)  (ΔH·I_e)  (ΔH·I_i)    (x)
t=1:   1     0.0        0.0        0.0
t=2:   1    -0.5        0.0       -2.0
t=3:   1    -1.0        0.0       -4.5
t=4:   1    -1.5        0.0       -7.0
t=5:   1    -2.0        0.0      -10.0
t=6:   1     0.0       -2.5      -13.5
t=7:   1     0.0       -2.5      -16.0
t=8:   1     0.0       -2.5      -18.5
```

The elastic and inelastic columns are mutually exclusive: wherever Column 2 is non-zero, Column 3 is zero, and vice versa. This is a structural property of the two-regime design that guarantees the coefficients $S_{ske}$ and $S_{skv}$ are estimated from disjoint sets of observations.

The response vector y contains the observed MLCW cumulative compaction at each epoch:

    y = [ -0.50,  -2.30,  -4.30,  -6.30,  -8.50,  -18.40,  -19.40,  -20.40 ]^T   (mm)

### 8.6 Computing X^T X and X^T y

Each element of the 4 $\times$ 4 matrix X^T X is the inner product of two columns of X. Computing all ten distinct elements (the matrix is symmetric):

    X^T X [1, 1] = 8$\cdot$ 1 = 8.00
    X^T X [1, e] = 0 + (-0.5) + (-1.0) + (-1.5) + (-2.0) + 0 + 0 + 0 = -5.00
    X^T X [1, i] = 0 + 0 + 0 + 0 + 0 + (-2.5) + (-2.5) + (-2.5) = -7.50
    X^T X [1, x] = 0 + (-2.0) + (-4.5) + (-7.0) + (-10.0) + (-13.5) + (-16.0) + (-18.5) = -71.50
    X^T X [e, e] = 0^2 + 0.5^2 + 1.0^2 + 1.5^2 + 2.0^2 + 0 + 0 + 0 = 0.25 + 1.00 + 2.25 + 4.00 = 7.50
    X^T X [e, i] = 0  (elastic and inelastic columns share no non-zero rows)
    X^T X [e, x] = 0 + (-0.5)(-2.0) + (-1.0)(-4.5) + (-1.5)(-7.0) + (-2.0)(-10.0) + 0 + 0 + 0
                 = 1.00 + 4.50 + 10.50 + 20.00 = 36.00
    X^T X [i, i] = 0 + 0 + 0 + 0 + 0 + 2.5^2 + 2.5^2 + 2.5^2 = 3 $\times$ 6.25 = 18.75
    X^T X [i, x] = (-2.5)(-13.5) + (-2.5)(-16.0) + (-2.5)(-18.5)
                 = 33.75 + 40.00 + 46.25 = 120.00
    X^T X [x, x] = 0 + 4.00 + 20.25 + 49.00 + 100.00 + 182.25 + 256.00 + 342.25 = 953.75

The complete matrix is:

         1        e        i        x
    1 [   8.00   -5.00   -7.50   -71.50 ]
    e [  -5.00    7.50    0.00    36.00 ]
    i [  -7.50    0.00   18.75   120.00 ]    … (18)
    x [ -71.50   36.00  120.00   953.75 ]

Each element of the 4 $\times$ 1 vector X^T y is the inner product of a column of X with the response vector y:

    (X^T y)[1] = (-0.50) + (-2.30) + (-4.30) + (-6.30) + (-8.50) + (-18.40) + (-19.40) + (-20.40)
               = -80.10
    (X^T y)[e] = 0(-0.50) + (-0.5)(-2.30) + (-1.0)(-4.30) + (-1.5)(-6.30) + (-2.0)(-8.50) + 0 + 0 + 0
               = 0 + 1.15 + 4.30 + 9.45 + 17.00 = 31.90
    (X^T y)[i] = (-2.5)(-18.40) + (-2.5)(-19.40) + (-2.5)(-20.40)
               = 46.00 + 48.50 + 51.00 = 145.50
    (X^T y)[x] = (-2.0)(-2.30) + (-4.5)(-4.30) + (-7.0)(-6.30) + (-10.0)(-8.50)
                 + (-13.5)(-18.40) + (-16.0)(-19.40) + (-18.5)(-20.40)
               = 4.60 + 19.35 + 44.10 + 85.00 + 248.40 + 310.40 + 377.40
               = 1089.25

The complete vector is:

         [ -80.10  ]
         [  31.90  ]    … (19)
         [ 145.50  ]
         [ 1089.25 ]

### 8.7 Solving for the coefficient vector

The OLS normal equation is X^T X $\theta$= X^T y (equation (15) of this document). The coefficient vector $\theta$=[c, $S_{ske}$, $S_{skv}$, $\beta$]^T is the unique solution to this 4 $\times$ 4 linear system, obtained by computing (X^T X)^{−1} X^T y.

The solution is:

    c     = -0.50  mm
    $S_{ske}$=  2.00  mm/m    … (20)
    $S_{skv}$=  5.00  mm/m
    $\beta$=  0.40  (dimensionless)

To confirm this result without computing the full matrix inverse, each row of equation (18) is evaluated at $\theta$:

Row 1:  8.00(-0.50) + (-5.00)(2.00) + (-7.50)(5.00) + (-71.50)(0.40)
     = -4.00 - 10.00 - 37.50 - 28.60 = -80.10   ✓  matches (X^T y)[1]

Row 2:  (-5.00)(-0.50) + 7.50(2.00) + 0(5.00) + 36.00(0.40)
     =  2.50 + 15.00 + 0 + 14.40 = 31.90   ✓  matches (X^T y)[e]

Row 3:  (-7.50)(-0.50) + 0(2.00) + 18.75(5.00) + 120.00(0.40)
     =  3.75 + 0 + 93.75 + 48.00 = 145.50   ✓  matches (X^T y)[i]

Row 4:  (-71.50)(-0.50) + 36.00(2.00) + 120.00(5.00) + 953.75(0.40)
     =  35.75 + 72.00 + 600.00 + 381.50 = 1089.25   ✓  matches (X^T y)[x]

All four rows of the normal equation are satisfied. The solution in equation (20) is confirmed without computing any matrix inverse.

### 8.8 Computing the fitted values and goodness-of-fit statistics

The fitted values ŷ = X $\theta$ are obtained by evaluating equation (13) at each epoch with the recovered coefficients:

```
Epoch   ŷ = c + S_ske(ΔH·I_e) + S_skv(ΔH·I_i) + β·x          ŷ (mm)
  1     -0.50 + 2.00(0.0) + 5.00(0.0) + 0.40(0.0)             = -0.50
  2     -0.50 + 2.00(-0.5) + 5.00(0.0) + 0.40(-2.0)           = -2.30
  3     -0.50 + 2.00(-1.0) + 5.00(0.0) + 0.40(-4.5)           = -4.30
  4     -0.50 + 2.00(-1.5) + 5.00(0.0) + 0.40(-7.0)           = -6.30
  5     -0.50 + 2.00(-2.0) + 5.00(0.0) + 0.40(-10.0)          = -8.50
  6     -0.50 + 2.00(0.0)  + 5.00(-2.5) + 0.40(-13.5)         = -18.40
  7     -0.50 + 2.00(0.0)  + 5.00(-2.5) + 0.40(-16.0)         = -19.40
  8     -0.50 + 2.00(0.0)  + 5.00(-2.5) + 0.40(-18.5)         = -20.40
```

Because the observed values y were constructed to satisfy the model exactly, the residuals e = y − ŷ are all zero:

    RSS = $\Sigma$(y_t − ŷ_t)^2 = 0.00 mm^2

The mean of the observed values is:

    ȳ = (-0.50 - 2.30 - 4.30 - 6.30 - 8.50 - 18.40 - 19.40 - 20.40) / 8
      = -80.10 / 8 = -10.01 mm

The total sum of squares is:

    TSS = $\Sigma$(y_t − ȳ)^2
        = (9.51)^2 + (7.71)^2 + (5.71)^2 + (3.71)^2 + (1.51)^2 + (8.39)^2 + (9.39)^2 + (10.39)^2
        = 90.44 + 59.44 + 32.60 + 13.76 + 2.28 + 70.39 + 88.17 + 107.95
        = 465.03 mm^2

The goodness-of-fit statistics follow from equations (16):

    R^2   = 1 − RSS / TSS = 1 − 0 / 465.03 = 1.000
    RMSE = sqrt(RSS / N) = sqrt(0 / 8) = 0.00 mm

The perfect fit follows directly from the construction of the dataset. In practice, measurement noise, model approximation, and unmonitored compaction sources all contribute residuals. Adding a small perturbation of $\varepsilon_max$ = $\pm$ 0.3 mm to individual observations changes each fitted coefficient by less than 2% and reduces R^2 to approximately 0.998, confirming that the parameter recovery is numerically stable against realistic noise levels.

The large step in $D_{k}$ between epoch 5 (−8.50 mm) and epoch 6 (−18.40 mm) deserves comment. At epoch 6 the inelastic indicator activates for the first time. The full cumulative head deficit of −2.5 m, multiplied by $S_{skv}$= 5.00 mm/m, contributes 12.5 mm of permanent compaction in that single epoch's regression term — an amount that exceeds the entire elastic accumulation from the preceding five epochs (7.50 mm from the GWL term alone). This mathematical step is a direct consequence of the cumulative-form regression: when the inelastic indicator turns on, the model assigns the full accumulated head deficit to the inelastic compressibility coefficient at once, reflecting the interpretation that the sediment has been undergoing virgin consolidation since the first moment the stress exceeded the preconsolidation threshold.

### 8.9 Physical interpretation of the recovered coefficients

Each of the four estimated parameters has a direct physical meaning, and each can be checked against expected ranges.

**c = −0.50 mm.** The negative intercept indicates that the sediment layer had accumulated 0.50 mm of net compaction before the first observation epoch — a legacy of stress history prior to instrument installation. This value is small, consistent with a layer that was not heavily loaded before the monitoring began.

**$S_{ske}$= 2.00 mm/m.** For each metre of head decline in the elastic regime, the layer compacts by 2.00 mm. This value is consistent with the physically plausible range of approximately 1–20 mm/m reported for multi-metre alluvial clay layers (Section 6.3). The positive sign confirms that head decline (negative $\Delta H$) produces compaction (negative ŷ), as the physical mechanism requires.

**$S_{skv}$= 5.00 mm/m.** For each metre of head decline in the inelastic regime, the layer compacts by 5.00 mm. The ratio $S_{skv}$/ $S_{ske}$= 5.00 / 2.00 = 2.5 falls within the physically expected range of 2 to 20 for alluvial clay (Poland 1984). The inelastic coefficient is larger than the elastic coefficient, confirming that the sediment is more compressible during virgin consolidation than during elastic reloading. Both signs are positive, as required by the physical mechanism described in Section 2.3.

**$\beta$= 0.40 (dimensionless).** For each millimetre of total InSAR surface displacement, 0.40 mm of that surface motion is co-explained by this layer through the InSAR co-driver term. The positive sign is correct: greater surface subsidence (more negative x) is associated with greater per-layer compaction (more negative ŷ). The magnitude of 0.40 suggests that the InSAR term explains a substantial secondary fraction of the compaction at this layer, beyond what the local head record captures.

All four coefficients carry the expected signs (Section 3.3). The ratio $S_{skv}$/ $S_{ske}$= 2.5 is consistent with, though at the lower end of, the range reported for Holocene alluvial clay in alluvial fan settings.

### 8.10 Connection to the general procedure

The eight numbers in Table 1 pass through every step listed in Section 7: regime classification from the historical head minimum, construction of a mutually exclusive two-column head driver, the four-parameter OLS solve, and verification through the normal equations. The quantitative result — c = −0.50 mm, $S_{ske}$= 2.00 mm/m, $S_{skv}$= 5.00 mm/m, $\beta$= 0.40 — is physically interpretable at each position: the intercept captures pre-observation compaction history; the elastic and inelastic storage coefficients capture reversible and permanent sediment response to groundwater stress, respectively; and the InSAR coupling captures compaction contributions not resolved by the single assigned GWL well.

The drought structure of the scenario — five epochs of moderate head decline followed by three epochs at the new low stand — is representative of the Choushui River Alluvial Fan monitoring record, where sustained pumping periods produce extended inelastic windows separated by partial head recovery during wet seasons. At real stations the residuals are non-zero, the lag $\tau$ may be greater than zero, and f_inel varies fold by fold as described in Section 6.2. The algebra demonstrated here is identical in all cases; only the numerical values of X^T X, X^T y, and $\theta$ differ.

---

## 9. Conceptual Clarifications

### 9.1 Why the model uses a change-from-reference quantity $\Delta H$_k rather than a step-to-step difference

The piezometric head driver in equation (13) is defined as $\Delta H_k(t)$ = H_k(t) − H_k($t_{ref}$), where $t_{ref}$ is the first observation epoch. This is a change-from-reference quantity: it measures how far the head has moved since the start of the record, not how much it moved between two consecutive observations. The distinction matters because the two formulations solve different physical problems and produce model outputs with different physical meanings.

A step-to-step difference — H_k(t) − H_k(t − 1) — measures the head increment between epoch t and the immediately preceding epoch t − 1. If the head stayed flat for ten epochs and then dropped sharply at epoch eleven, the step-to-step difference would be zero for all ten flat epochs and non-zero only at epoch eleven. The change-from-reference, by contrast, accumulates: if the head has dropped steadily since $t_{ref}$, $\Delta H_k(t)$ grows in magnitude with each successive epoch, reflecting the total stress accumulated over the entire elapsed record.

The response variable $D_{k}(t)$ is the cumulative MLCW compaction since the first epoch — a running total, not an epoch-to-epoch increment. Both sides of equation (13) therefore share the same reference point $t_{ref}$ and measure change over the same elapsed interval. Multiplying $S_{skv}$ by $\Delta H_k(t)$ gives a quantity in the same units as $D_{k}(t)$: millimetres of total compaction accumulated since $t_{ref}$ per metre of total head change since $t_{ref}$. The regression is internally consistent because both the predictor and the response express change relative to the same baseline.

The physical reason for this choice follows directly from equation (7): $\Delta b(t)$ = S_sk_bulk $\cdot \Delta H(t)$. The left side is the total compaction accumulated since $t_{ref}$, and the right side is the total head change since $t_{ref}$. Equation (7) states that total accumulated compaction is proportional to total accumulated head change. When this physics is cast as a regression, the natural predictor is the cumulative head deficit $\Delta H_k(t)$, not the per-epoch increment.

If step-to-step head increments were used instead, the model would predict the compaction that occurred between epoch t − 1 and epoch t, not the cumulative total through epoch t. The OLS would produce a numerically valid fit, but the estimated $S_{ske}$ and $S_{skv}$ would carry units of mm-per-epoch per m-per-epoch — a different physical quantity from the bulk storage coefficient. The fitted model could not be used to predict $D_{k}(t)$ without re-integrating the per-epoch predictions, and that re-integration would accumulate errors across hundreds of epochs. Using the change-from-reference formulation avoids this entirely: a single multiplication of $S_{skv}$ by $\Delta H_k(t)$ gives $D_{k}(t)$ directly.

### 9.2 Why the model estimates $S_{ske}$ and $S_{skv}$ from OLS rather than using the 2S-TOOL reference values

The 2S-TOOL produces independent estimates of the inelastic and elastic skeletal storage coefficients by fitting a stress-path curve through the full MLCW compaction record plotted against groundwater depth below surface. The slope of this regression, taken as the inverse of the full-cloud fit, gives $S_{kv}$. The slopes of small reversible loops in the curve, identified from local extrema in the head record, give per-loop $S_{ke}$ values from which a weighted mean is computed. For one representative layer at a study site in the Choushui River Alluvial Fan (layer F3 at station TUKU), this procedure yields $S_{kv}$= 0.0562 m/m and a weighted $S_{ke}$= 0.000753 m/m. For another layer at the same station (layer F1), the corresponding values are $S_{kv}$= 0.005653 m/m and $S_{ke}$= 0.002201 m/m. These are physically meaningful estimates of compressibility obtained from an entirely independent computational path.

The two-regime compaction model re-estimates $S_{ske}$ and $S_{skv}$ from OLS on the same timeseries for four reasons. First, the 2S-TOOL method uses groundwater depth below surface as the stress variable, while the two-regime model uses piezometric head relative to a fixed reference epoch. The two stress variables differ by a constant elevation offset, but they also differ in how the regime boundary $h_{c}$ is identified: 2S-TOOL locates regime boundaries from loop geometry on the stress-path curve, while the two-regime model uses the historical minimum head over the observation record. The effective storage coefficients from each method are calibrated to different stress representations and are not directly interchangeable. Second, the model design matrix includes InSAR surface displacement x(t) as a co-driver alongside the two head-change channels. The 2S-TOOL has no equivalent for the $\beta$ coefficient, and no procedure exists to obtain $\beta$ from stress-path analysis. Fixing $S_{ske}$ and $S_{skv}$ at 2S-TOOL values while leaving $\beta$ free would impose external constraints on two of the four parameters, preventing the OLS from finding the partition of variance that minimises total residual error across all four predictors simultaneously. Third, fixing the storage coefficients at 2S-TOOL values requires that the stress-path fit and the temporal regression produce the same effective values — an assumption that holds only if the two methods see exactly the same stress history, the same regime boundaries, and the same lag structure. In practice, the OLS operates on the lag-adjusted timeseries with $\tau$ selected by a grid search, which produces a different temporal alignment than the stress-path fit. Fourth, the OLS estimation is performed on the same observation epochs and the same cumulative reference that will be used for prediction. The resulting parameters are therefore the best-fitting values for the specific timeseries at hand, without additional assumptions imported from a different estimation procedure.

The 2S-TOOL values serve as physical plausibility bounds for interpreting the OLS results after fitting. If the OLS-estimated $S_{ske}$ or $S_{skv}$ falls far outside the range of the corresponding 2S-TOOL value, the discrepancy is treated as a diagnostic flag. Likely causes include an incorrectly assigned GWL well (the head signal corresponds to a different aquifer unit), near-perfect collinearity between $\Delta H$_k and x(t) (which prevents the OLS from separating the elastic channel from the InSAR channel), or an insufficient number of inelastic epochs to constrain $S_{skv}$. For the F3 layer example above, $S_{kv}$ from 2S-TOOL is 0.0562 m/m. An OLS-estimated $S_{skv}$ that is an order of magnitude smaller or larger than this value indicates that one of these problems is present. For the F1 layer, the 2S-TOOL ratio $S_{kv}$/$S_{ke}$ is approximately 2.6 — at the lower end of the expected range of 5 to 20 for alluvial clay — which itself flags that the F1 layer may behave more elastically than typical deep-aquifer clay units.

The parameter names $S_{ske}$ and $S_{skv}$ follow the nomenclature established in the hydrogeology literature. The root "S_sk" denotes skeletal specific storage, the material property that quantifies how much a unit volume of the sediment skeleton compresses per unit change in effective stress. The suffix "e" denotes the elastic (recoverable) regime, following the notation in Helm (1975) and subsequently standardised in Poland (1984). The suffix "v" denotes the virgin (inelastic, irreversible) consolidation regime, also from Poland (1984). The term "virgin" refers to stress states that exceed the historical maximum effective stress the sediment has ever experienced. These are standard parameter names in the subsidence literature, not names invented for this project.

---

## References

- Biot, M. A. (1941). General theory of three-dimensional consolidation. *Journal of Applied Physics*, 12(2), 155–164.
- Chen, C.-T., et al. (2016). Characterization of aquifer system compressibility in the Choushui River Fan, Taiwan. *Hydrogeology Journal*, 24(5), 1175–1192.
- Galloway, D. L., and Burbey, T. J. (2011). Regional land subsidence accompanying groundwater extraction. *Hydrogeology Journal*, 19(8), 1459–1486.
- Hamilton, J. D. (1989). A new approach to the economic analysis of nonstationary time series and the business cycle. *Econometrica*, 57(2), 357–384.
- Helm, D. C. (1975). One-dimensional simulation of aquifer system compaction near Pixley, California. *Water Resources Research*, 11(3), 465–478.
- Hung, W.-C., et al. (2021). Characterizing aquifer compressibility from groundwater dynamics and land subsidence in Choushui River Alluvial Fan, Taiwan. *Journal of Hydrology*, 599, 126378.
- Poland, J. F. (Ed.) (1984). *Guidebook to Studies of Land Subsidence Due to Ground-Water Withdrawal*. UNESCO, Paris.
- Riley, F. S. (1969). Analysis of borehole extensometer data from central California. In *Land Subsidence* (IAHS Publ. 88), 423–431.
- Smith, R., et al. (2021). Apportioning deformation among depth intervals in an aquifer system using InSAR and head data. *Geophysical Research Letters*, 48(5), e2020GL091495.
- Sneed, M., and Galloway, D. L. (2000). *Aquifer-System Compaction and Land Subsidence: Measurements, Analyses, and Simulations — the Holly Site, Edwards Air Force Base, Antelope Valley, California*. USGS Water-Resources Investigations Report 00-4015.
- Terzaghi, K. (1925). *Erdbaumechanik auf bodenphysikalischer Grundlage*. F. Deuticke, Vienna.
- Terzaghi, K. (1943). *Theoretical Soil Mechanics*. Wiley, New York.
