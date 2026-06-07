# Background Report: Groundwater Dynamics, Pumping, Electricity Usage, and Land Subsidence in the Choushui River Alluvial Fan

**Compiled:** 2026-05-30
**Purpose:** Comprehensive reference for the InSAR-MLCW subsidence modelling project

---

## 1. Introduction

The Choushui River Alluvial Fan (濁水溪沖積扇) in central-western Taiwan is one of the most intensively studied hydrogeological regions in East Asia. Spanning approximately 1,800 km^2 across Changhua County to the north and Yunlin County to the south, this alluvial fan supports a dense population, intensive agriculture, aquaculture, and industrial activity — all sustained largely by groundwater extraction. The resulting aquifer-system compaction has produced cumulative land subsidence exceeding 2 m in some areas, threatening infrastructure including the Taiwan High-Speed Rail (THSR).

This report synthesises published research on four interconnected themes:

1. **Hydrogeological framework** — the layered aquifer-aquitard system
2. **Groundwater level fluctuations** — seasonal and long-term trends
3. **Pumping estimation from electricity consumption** — a key methodological innovation
4. **Land subsidence** — mechanisms, monitoring, and spatial patterns

---

## 2. Hydrogeological Framework

### 2.1 Physiographic setting

The Choushui River originates in the Central Mountain Range at elevations exceeding 3,000 m and flows approximately 186 km westward to the Taiwan Strait. The alluvial fan formed during the Quaternary period from fluvial deposits of the Choushui River and its tributaries. The fan is bounded by the Bagua Mountains to the north, the Douliu Hills to the south, the Central Mountain Range to the east, and the Taiwan Strait to the west.

### 2.2 Aquifer-aquitard system

From the surface downward, the hydrogeological sequence within approximately 330 m depth comprises four aquifers (F1–F4) and three aquitards (T1–T3), in alternating order (Central Geological Survey, 1999; Water Resources Agency, 2019):

**Table 1: Hydrogeological layer classification of the Choushui River Alluvial Fan**

| Layer code | Type | Depth range (m) | Thickness range (m) | Mean thickness (m) | Dominant lithology |
|:-----------:|:----:|:----------------:|:-------------------:|:------------------:|:-------------------|
| F1 | Aquifer | 0 – 103 | 19 – 103 | 42 | Gravel, coarse sand → fine sand, mud |
| T1 | Aquitard | 35 – 129 | 0 – 39 | 14 | Clay, silt, mud with minor sand |
| F2 | Aquifer | 35 – 217 | 76 – 145 | **95** | Gravel, coarse sand — **thickest aquifer** |
| T2 | Aquitard | 140 – 223 | 0 – 46 | 23 | Mud interbedded with fine sand |
| F3 | Aquifer | 140 – 275 | 42 – 122 | 86 | Gravel, coarse sand → fine sand |
| T3 | Aquitard | 238 – 293 | 0 – 28 | 11 | Mud with fine sand interbeds |
| F4 | Aquifer | 238 – 313 | 6 – 51 | 24 | Gravel, sand → fine sand |

### 2.3 Hydrogeological zonation

Three distinct zones exist across the fan (Central Geological Survey, 1999):

- **Proximal fan (扇頂)** — east of Yuanlin, Xizhou, Xiluo, and Huwei. Aquitards are absent or discontinuous. All aquifers are hydraulically connected, forming a single unconfined system. Surface water from the Choushui River recharges groundwater directly through the permeable gravel bed.
- **Mid-fan (扇央)** — central region where aquitards T1 and T2 are well-developed, creating confined aquifer conditions. This zone has the highest agricultural pumping density.
- **Distal fan (扇尾)** — coastal region where sand and gravel content decreases and silt/clay content increases. Aquifer hydraulic conductivity is lowest here.

Regional hydraulic conductivity ranges from 6 $\times$ 10⁻^2 to 6 $\times$ 10⁻⁴ m/min. Transmissivity ranges from 0.01 to 4.19 m^2/min. Hydraulic conductivity decreases from the proximal fan (best) through the mid-fan to the distal fan (poorest).

**Per-zone groundwater and compaction parameters** were quantified by Hung et al. (2021) from stress-strain analysis at three representative MLCW stations. In the **proximal fan** (JNES/Huxi station, F2 depth 51–158 m), GWL is stable or rising (F1: +0.02 m/yr, F2: +0.21 m/yr) with seasonal amplitudes of 0.68 m (F1) and 1.52 m (F2). No inelastic compaction is detected: $S_{ske}$ = 1.8 $\times$ 10⁻⁵ m⁻¹, and total compaction is <1 cm across all F1–F4 layers (excluding the 0–10 m construction zone). In the **mid-fan** (STES station), GWL declines at −0.18 m/yr (F1) and −0.07 m/yr (F2), with seasonal amplitudes 1.07 m (F1) and 3.35 m (F2). $S_{ske}$ = 1.5 $\times$ 10⁻⁵ m⁻¹, $S_{skv}$ = 3.3 $\times$ 10⁻⁴ m⁻¹ — the inelastic coefficient exceeds the elastic by an order of magnitude. The safe GWL (the lowest head at which compaction remains fully elastic) is −8 m relative to MSL; heads dropped to −12 m in the dry seasons of 2015, 2017, and 2018. In the **distal fan** (YWJS station), GWL declines are steeper: F2: −0.36 m/yr, F3: −0.50 m/yr. Seasonal amplitudes reach 5.98 m (F2) and 6.06 m (F3). $S_{ske}$ = 1.6 $\times$ 10⁻⁵ m⁻¹, $S_{skv}$ = 9.1 $\times$ 10⁻⁵ m⁻¹. The safe GWL is −28 m MSL; heads dropped to −34 m in May 2015 and 2018. The largest compaction occurs in F2, followed by F3, F4, and F1.

---

## 3. Groundwater Level Dynamics

### 3.1 Long-term trends

Historical records from monitoring wells show substantial groundwater-level declines since the 1970s. The Water Resources Agency (2019) reports that annual mean groundwater levels at four representative stations declined as follows:

**Table 2: Long-term groundwater level decline at selected stations**

| Station | Original level (m MSL) | Current level (m MSL) | Decline (m) | Period |
|:-------:|:--------------------:|:--------------------:|:----------:|:------:|
| Ershui (二水) | +80 | +40 | 40 | 1976–2010 |
| Jiaxing (嘉興) | +25 | +5 | 20 | 1976–2010 |
| Beigang (北港) | +8 | −14 | 22 | 1976–2010 |
| Hefeng (和豐) | +3 | −15 | 18 | 1976–2010 |

The total groundwater storage loss over 35 years is estimated at 2.5 billion cubic metres, or approximately 70 million cubic metres per year.

### 3.2 Seasonal fluctuations

Groundwater levels exhibit strong seasonal cycles driven by the East Asian monsoon. The wet season (May–September) delivers approximately 80% of annual rainfall (~1,500–2,000 mm/yr). Groundwater levels typically rise 2–8 m during the wet season and fall during the dry season. The seasonal amplitude is largest in the proximal fan (unconfined conditions, rapid recharge) and smallest in the distal fan (confined conditions, slower pressure transmission). At the regional scale, Hsu et al. (2021) estimated the mean annual water thickness change across Taiwan at 0.53 $\pm$ 0.17 m from GNSS loading data, with the largest seasonal change — up to 0.91 m — occurring in southwestern Taiwan where the CRAF is located. The associated elastic loading stress perturbation from the monsoon cycle is approximately 3–5 kPa.

### 3.3 Spatial patterns

Zhang et al. (2017) applied the Standardised Groundwater Level Index (SGI365) to 2007–2015 monitoring data. The mid-fan region showed the highest proportion of negative SGI values (sustained below-average groundwater levels), which correlated strongly with subsidence rates. This spatial pattern confirms that the mid-fan is the most groundwater-stressed region, consistent with the highest density of agricultural pumping wells.

---

## 4. Groundwater Pumping and Electricity Consumption

### 4.1 The unmetered pumping problem

Groundwater extraction in Taiwan is largely unmetered. Agricultural pumping, which accounts for approximately 70% of total groundwater use in the Choushui fan, is not subject to individual well metering. This creates a fundamental data gap for water resource management and subsidence modelling. To address this gap, researchers have developed methodologies to estimate pumping volumes from electricity consumption data.

### 4.2 The electricity-consumption methodology

Tatas, Chu, Burbey, and Lin (2023) published the seminal paper linking electricity consumption to groundwater extraction in the Choushui alluvial fan. The key relationship is:

```
Pumping volume ∝ Electricity consumption × Pump efficiency
```

The methodology uses:
- **Electricity power consumption records** from Taiwan Power Company (Taipower) — available at the township level
- **Irrigation well density** — spatial distribution of agricultural wells
- **Crop water demand** — based on land-use classification
- **Temporal weighting** — seasonal pumping patterns aligned with irrigation cycles

The spatial regression model achieved a root-mean-square error (RMSE) of 0.65 cm/yr for annual subsidence estimation from electricity-derived pumping volumes.

**Critical finding:** The spatial correlation between pumping volumes and subsidence is weak. Locations of maximum subsidence do not always coincide with locations of maximum pumping or maximum water-level drawdown. This is attributed to the heterogeneous distribution of compressible fine-grained sediments (aquitard materials), which control where compaction actually occurs.

### 4.3 Recent developments

Liu, Ku, and Ni (2025) at the National Taiwan Ocean University applied LSTM deep learning models to project future subsidence under different pumping scenarios. Their model used electricity consumption data as a proxy for groundwater extraction volume. Key results:

- An LSTM model achieved RMSE < 0.4 cm and R^2 $\approx$ 0.8 for monthly subsidence prediction
- Under CMIP6 climate scenarios (SSP245, SSP585), subsidence rates could accelerate by 1.5–2 cm/yr in agricultural areas
- A **10–20% reduction in groundwater extraction** (i.e., reduced electricity consumption) could reduce compaction by **16–50%**
- At the Xiutan monitoring well, the subsidence rate dropped from 2.23 cm/yr to 1.34 cm/yr under reduced pumping scenarios

### 4.4 Pumping volume estimates

The Water Resources Agency (2019) and National Chiao Tung University (2009) report the following regional water budget:

**Table 3: Annual water budget of the Choushui River Alluvial Fan**

| Component | Volume (10⁸ m^3/yr) | Source |
|:----------|:------------------:|:-------|
| Mean total recharge | 8.12 | NCTU (2009) |
| Shallow aquifer pumping | 4.36 | NCTU, 2017–2020 avg |
| Deep aquifer pumping | 8.11 | NCTU, 2017–2020 avg |
| Total pumping (Changhua) | 4.44 | NCTU (2008) |
| Total pumping (Yunlin) | 5.66 | NCTU (2008) |
| Overdraft (Changhua) | 0.62 | NCTU (2008) |
| Overdraft (Yunlin) | 1.36 | NCTU (2008) |
| Net storage change | −0.59 | NCTU, 2017–2020 avg |

Note that deep aquifer pumping (8.11 $\times$ 10⁸ m^3/yr) far exceeds shallow aquifer pumping (4.36 $\times$ 10⁸ m^3/yr), yet the shallow pumping has disproportionate effects on deep aquifer compaction through leaky aquitard connectivity (Sung, 2019).

---

## 5. Land Subsidence

### 5.1 Mechanisms

Land subsidence in the Choushui River alluvial fan is primarily caused by the compaction of fine-grained aquitard materials (clay, silt) in response to groundwater-level decline. This follows Terzaghi's effective stress principle: as groundwater levels decline, pore-water pressure decreases and effective stress on the soil skeleton increases, causing compression.

Two regimes exist:
- **Elastic deformation** — recoverable compression during normal seasonal water-level fluctuations (storage coefficient $S_{ke}$)
- **Inelastic deformation** — permanent, irreversible compaction when water levels fall below the previous minimum (preconsolidation head), governed by the inelastic storage coefficient $S_{kv}$

Research by the Water Resources Agency (2022) found that the dominant subsidence-causing soils are fine-grained materials (silt and clay), not the aquifer sands and gravels.

### 5.2 Historical subsidence

Between 1992 and 2009, maximum cumulative subsidence reached:

- **Dacheng Township (Changhua):** > 210 cm
- **Yuanchang Township (Yunlin):** > 130 cm

The subsidence centre has migrated over time. In the early period (1970s–1990s), maximum subsidence was concentrated in coastal areas (distal fan). Since approximately 2000, the subsidence centre has shifted inland to the mid-fan region, particularly in Yunlin County (NCKU, 2019).

### 5.3 Monitoring methods

Multiple monitoring technologies are employed:

| Method | Spatial coverage | Temporal resolution | Accuracy |
|:-------|:----------------:|:------------------:|:--------:|
| Precision leveling | Point (benchmarks) | Annual | $\pm$ 1–2 mm |
| GPS continuous stations | Point (~50 stations) | Daily | $\pm$ 3–5 mm |
| InSAR time series | Areal (entire fan) | ~25-day repeat | $\pm$ 5–10 mm |
| Multi-layer compaction wells (MLCW) | Point (37 stations) | ~5-day | $\pm$ 0.1 mm per ring |
| Fibre-optic TDR | Point (new) | Real-time | $\pm$ 0.01 mm |

The 2022 "Cutting-Edge Integrated Land Subsidence Prevention Technology" project (WRA/NSTC) completed InSAR deformation analysis along the THSR corridor and developed multi-depth fibre-optic TDR real-time monitoring systems.

### 5.4 Spatial subsidence patterns

Key findings from monitoring and modelling:

- The second and third aquifers (F2, F3) show persistent subsidence (NCKU, 2019)
- The greatest inelastic compaction potential is in **southern inland areas** of the fan (Chu et al., 2021)
- **Elastic compaction** dominates the northern and proximal fan areas (Chu et al., 2021)
- Satellite InSAR data fusion with leveling and compaction-well data identified seasonal subsidence hotspots: **coastal areas in winter** (aquaculture pumping) shifting **inland to Yunlin in spring** (agricultural irrigation) (Chu et al., 2021)
- Shallow agricultural pumping contributes 56.1% of deep aquifer subsidence at a shallow:deep pumping ratio of 3.65:1 (Sung, 2019)

### 5.5 InSAR-derived groundwater estimation

Ali et al. (2021; 2022) demonstrated two important remote-sensing relationships:

- GPS-derived deformation can estimate monthly groundwater levels with a correlation of r = 0.95 between observed and estimated levels
- InSAR-derived subsidence can estimate annual groundwater storage changes
- The largest cone of depression in the distal fan does not spatially coincide with the subsidence bowl, which is located farther inland — confirming the complex, non-linear relationship between drawdown and compaction that is governed by aquitard distribution

### 5.6 Per-layer compaction budget

Chu et al. (2024) applied empirical orthogonal function (EOF) decomposition to monthly compaction data from 31 MLCW stations across the CRAF (January 2015 – December 2018). They identified three distinct spatial modes of subsidence:

- **EOF1 (97.5% of variance):** continuous long-term subsidence concentrated in the southern inland mid-fan — the dominant subsidence pattern, driven by sustained agricultural pumping.
- **EOF2 (1.7% of variance):** seasonal subsidence and rebound affecting the southern distal fan and proximal fan — elastic response to the wet–dry cycle.
- **EOF3 (0.4% of variance):** intra-seasonal fluctuations along the central coast — linked to aquaculture pumping cycles for fish-pond water temperature control.

Using the same dataset, the paper presents a per-layer compaction budget for nine representative wells in the central Yunlin subsidence hotspot, sourced from the WRA (2021) report:

| Layer unit | Average contribution to total subsidence (%) |
|:----------:|:--------------------------------------------:|
| F1 (Aquifer 1) | 8 |
| T1 (Aquitard 1) | 7 |
| F2 (Aquifer 2) | **23** |
| T2 (Aquitard 2) | 4 |
| F3 (Aquifer 3) | 13 |
| T3 (Aquitard 3) | 5 |
| F4 + T4 + below 300 m | **40** |

Two results stand out. First, deep compaction **below 300 m** — beyond the standard F1–F4 / T1–T3 framework — dominates the budget at ~40% of total subsidence. This means a substantial fraction of subsidence originates in sediments deeper than the 300 m monitoring range. Second, **aquifer F2** contributes 23%, consistent with its role as the most heavily exploited unit. Aquitards contribute only 4–7% each, indicating that compaction is concentrated in aquifer bodies and deep sediments rather than in the clay confining layers themselves. The remaining variance is distributed across seven wells with minor site-specific deviations from this average.

Stress-strain analysis at three EOF hotspot locations provides storage coefficient values expressed as dimensionless slopes (strain per unit head change): Tuku (mid-fan) = 0.0037, Yiwu (south-coast distal fan) = 0.0026, Hishhish (central coast) = 0.0032. Hysteresis at Tuku and Hishhish signals inelastic compaction, while the Yiwu response is primarily elastic (over-consolidated sediments).

The timing of maximum subsidence follows a repeatable calendar: **January–May**, peaking in **February and March**, coinciding with the first rice-planting season when agricultural demand is highest and monsoon recharge has not yet arrived. The wet season runs June–September. This seasonal cycle is resolved in detail by the EOF decomposition: maximum subsidence precedes the minimum groundwater level by approximately one month.

### 5.7 Elastic/inelastic partitioning and head thresholds

Tatas and Chu (2024) developed a statistical method to classify subsidence as elastic (recoverable) or inelastic (unrecoverable) using only hydraulic head data, bypassing the need for simultaneous stress-strain measurements. The classification is controlled by a head threshold:

```
h* = AVE − α · SD
```

where AVE and SD are the mean and standard deviation of the historical head record, and $\alpha$ is calibrated to minimise disagreement with the traditional stress-strain classification. When head h $\le$ h*, subsidence is inelastic; when h > h*, it is elastic.

Applying this rule to 20 monitoring stations across the mid-fan and distal fan (2015–2020) produced the following findings:

- **Inelastic proportion**: only ~15% of all monthly subsidence events are inelastic — the remainder is recoverable elastic deformation. Inelastic events occur predominantly in the **early months of each year** (January–March), the spring planting period with peak groundwater extraction.
- **Head thresholds** vary systematically across the fan: at Neiliao (mid-fan) the threshold is approximately **−11 m MSL**; at Yiwu (distal fan) it is approximately **−30 m MSL**. The distal fan has a lower (more negative) threshold because it has already undergone significant historical inelastic compaction, permanently lowering the preconsolidation head.
- **Six-year cumulative subsidence (2015–2020)**: total maximum ~43 cm (southern area), minimum ~9 cm (northern). Inelastic maximum = 13.4–13.9 cm (both rule-based and traditional classification agree); recoverable maximum = 29.5–30.8 cm. The mean inelastic component is ~7.3 cm, mean recoverable ~18.2 cm. The spatial extent of >11 cm unrecoverable subsidence is ~63 km^2.
- **Annual rates**: maximum unrecoverable subsidence ~2.5 cm/yr, maximum total subsidence ~6.5 cm/yr, both in the mid-fan central hotspot.
- **Spatial pattern of preconsolidation head**: the head threshold follows a **northwest–southeast gradient** — higher (less negative) in the northwest, lower (more negative) in the southeast — reflecting the combined influence of fan zonation (coarser sediments in the northwest) and cumulative compaction history (greater past compaction in the southeast lowers the threshold for new inelastic deformation).

The key operational insight: inelastic subsidence in the CRAF is concentrated in the mid-fan central hotspot during the first three months of the year, which gives a clear target for seasonal groundwater management.

---

## 6. Groundwater–Surface Elevation Interaction Models

### 6.1 The M13 and M23 models

A conceptual framework developed by Taiwanese researchers (documented in 濁水溪沖積扇地下水位與地表高程互動之模式與應用) classifies land-surface response into two end-member models based on the dominant control mechanism:

**Model M13 — Weight-controlled zone (負相關區):**
- Dominant in the **proximal fan and terraces**
- Unconfined or shallow aquifer with high storage coefficient (~0.15)
- During wet season: water level rises → pore pressure increases → effective stress decreases (expansion). BUT the weight of added water compresses deeper layers. The deeper-layer compression exceeds the shallow expansion → net subsidence.
- **Groundwater level and surface elevation change in opposite directions** (negative correlation)
- For Pingding station: water level drop of 1 m → surface rise of 0.034 cm (reversible elastic response)

**Model M23 — Pressure-controlled zone (正相關區):**
- Dominant in the **mid-fan and distal fan**
- Confined aquifer with low storage coefficient (~0.0019)
- During wet season: water level rises → pore pressure increases → effective stress decreases → ground surface rises
- **Groundwater level and surface elevation change in the same direction** (positive correlation)
- For Hefeng station: water level drop of 1 m → surface drop of 0.176 cm

### 6.2 Implications for management

The M13 and M23 framework has direct management implications:
- **In M13 zones (proximal fan):** pumping causes surface rise (or reduced subsidence), making these areas suitable for relocated extraction
- **In M23 zones (mid/distal fan):** pumping exacerbates subsidence, making these areas targets for pumping reduction
- The Mingzhu Basin (名竹盆地) east of the fan is proposed as a strategic groundwater reservoir: pumping from its unconfined aquifer would not cause local subsidence and could reduce extraction from the vulnerable confined aquifers downstream

---

## 7. Key Research Papers

### 7.1 Electricity consumption and subsidence

| Reference | Focus | Key contribution |
|:----------|:------|:-----------------|
| Tatas, Chu, Burbey & Lin (2023) | Electricity → pumping → subsidence | RMSE 0.65 cm/yr spatial regression; weak spatial correlation between pumping and subsidence |
| Ali, Chu & Burbey (2021) | GPS → groundwater estimation | r = 0.95 observed vs estimated groundwater levels |
| Chu, Ali & Burbey (2021) | Spatial regression: drawdown → subsidence | RMSE $\le$ 0.76 cm/yr; mapped inelastic storage coefficient patterns |
| Chu, Ali & Burbey (2021) | Sensor data fusion (leveling + monitoring wells) | RMSE 0.52 cm; seasonal hotspots identified |

### 7.2 Deep learning and future projections

| Reference | Focus | Key contribution |
|:----------|:------|:-----------------|
| Liu, Ku & Ni (2025) | LSTM + CMIP6 for Yunlin | RMSE < 0.4 cm; 10–20% pumping reduction → 16–50% less compaction |
| Patra, Chu & Aman (2025) | LSTM under SSP245/SSP585 | 1.5–2 cm/yr acceleration in agricultural areas |

### 7.3 Numerical modelling

| Reference | Focus | Key contribution |
|:----------|:------|:-----------------|
| NCKU (2019) | HEC-RAS + MODFLOW + INTERBED | Mean recharge 1.95 $\times$ 10⁹ tons; subsidence shifting inland |
| NCTU (2009) | MODFLOW water budget | Recharge 8.12 $\times$ 10⁸ m^3/yr; overdraft quantified |
| Sung (2019) | COMSOL shallow–deep pumping interaction | 56.1% of deep subsidence from shallow pumping |

### 7.4 Hydrogeology and subsidence monitoring

| Reference | Focus | Key contribution |
|:----------|:------|:-----------------|
| CGS (1999) | Hydrogeological survey | 7-layer framework (F1–F4, T1–T3); first comprehensive characterisation |
| WRA (2019) | Groundwater yearbook | Updated layer depths, thicknesses, hydraulic properties |
| NCU TEM study (2023) | Transient EM mapping | Imaged saline/fresh water distribution; validated hydrogeological structure |
| Hung, Hwang, Sneed et al. (2021) | MLCW interpretation + stress-strain analysis | Per-zone $S_{ske}$, $S_{skv}$, safe GWLs at 3 fan zones; MLCW precision 0.6 mm field; THSR safety thresholds |
| Chu, Tatas, Patra & Burbey (2024) | EOF feature decomposition | 3 spatial modes of subsidence; per-layer compaction budget: deep >300 m = 40%, F2 = 23% |

### 7.5 Inelastic subsidence, head thresholds, and AI forecasting

| Reference | Focus | Key contribution |
|:----------|:------|:-----------------|
| Patra, Chu & Tatas (2025) | STL decomposition + ML at 18 wells | Strong seasonal correlation (r > 0.8) but weak trend correlation (r < 0.4); up to 5.16 cm/yr inelastic rate in central Yunlin (2020) |
| Tatas & Chu (2024) | Head threshold rule for elastic/inelastic classification | Statistical h* = AVE − $\alpha$$\cdot$ SD; ~15% of events inelastic; head thresholds −11 m (mid-fan) to −30 m (distal fan); 6-yr inelastic max 13.9 cm |
| Hung, Hwang, Tosi et al. (2025) | Deep extensometers + AI forecasting at TKJS supersite | 3 extensometers (130/300/400 m) at 10-min resolution; Prophet model RMSE 0.34 mm/4-mo; per-aquifer GWL decline rates (0.18–0.48 m/yr) |

---

## 8. Management and Mitigation Strategies

### 8.1 Current measures

The Water Resources Agency (WRA) and other agencies are implementing:

- **Reduction of groundwater pumping** — enforced in the THSR corridor (3 km buffer zone) and severe subsidence areas
- **Alternative water sources** — increasing surface water delivery from the Jiji Weir (集集攔河堰) and the Mingzhu Basin
- **Artificial groundwater recharge** — pilot projects in the proximal fan
- **Subsidence monitoring** — maintained network of leveling routes, GPS stations, InSAR analysis, and 37 MLCW stations

### 8.2 The Mingzhu Basin proposal

A key proposal in the M13/M23 framework is to develop the Mingzhu Basin (east of the fan, at the confluence of the Choushui and Qingshui Rivers) as a strategic groundwater reservoir:

- Estimated usable volume: 1.0–2.0 $\times$ 10⁸ m^3/yr
- Pumping from the unconfined aquifer would cause surface rise (M13 behaviour), not subsidence
- Water would be distributed via Jiji Weir north/south bank channels
- This water would replace extraction from confined aquifers in the mid/distal fan, allowing water levels to recover and subsidence to slow

### 8.3 Pumping relocation

An intermediate strategy involves shifting pumping from M23 zones (mid/distal fan) to M13 zones (proximal fan). Even without reducing total pumping, this spatial redistribution would allow water levels in the most vulnerable confined aquifers to stabilise or recover.

### 8.4 Modelled mitigation effectiveness

The LSTM-based studies (Liu et al., 2025) provide quantitative mitigation targets:

- 10% reduction in groundwater extraction → 16–30% reduction in compaction
- 20% reduction in groundwater extraction → 33–50% reduction in compaction
- Under sustained reduction, groundwater levels recover progressively over 5–10 years

---

## 9. Conclusion

The Choushui River Alluvial Fan presents a complex hydrogeological system where the interplay between groundwater dynamics, pumping, and subsidence is governed by both the layered aquifer-aquitard structure and the heterogeneous distribution of compressible fine-grained sediments. Key findings relevant to the InSAR-MLCW modelling project include:

1. **Seven-layer framework** (F1–F4 aquifers, T1–T3 aquitards) with F2 as the thickest and most important aquifer (mean 95 m) and dominant subsidence zone.

2. **Groundwater levels** have declined 18–40 m since the 1970s, with total storage loss of 2.5 $\times$ 10⁹ m^3. The mid-fan region is the most groundwater-stressed.

3. **Electricity consumption** provides a practical proxy for unmetered groundwater extraction. The pumping-subsidence relationship is spatially weak due to heterogeneous aquitard distribution.

4. **Subsidence** has exceeded 2 m (Dacheng) and 1.3 m (Yuanchang), with the subsidence centre migrating inland from coastal areas to the mid-fan since ~2000. The F2 and F3 aquifers show persistent compaction.

5. **M13/M23 models** explain the contrasting surface response to water-level changes: weight-controlled (proximal fan, negative correlation) vs pressure-controlled (mid/distal fan, positive correlation).

6. **Mitigation modelling** suggests 10–20% pumping reduction could reduce compaction by 16–50%.

7. **Per-layer compaction budget** (Chu et al., 2024) shows that deep sediments below 300 m contribute ~40% of total subsidence, while F2 contributes 23% and each aquitard contributes only 4–7% — challenging the assumption that compaction is dominated by clay aquitards.

8. **Inelastic subsidence** comprises only ~15% of all monthly subsidence events, concentrated in January–March, with a maximum annual unrecoverable rate of ~2.5 cm/yr. Head thresholds for inelastic activation vary from −11 m MSL (mid-fan) to −30 m MSL (distal fan), following a northwest–southeast gradient across the fan (Tatas & Chu, 2024).

---

## References

1. Central Geological Survey (1999). *濁水溪沖積扇水文地質調查研究總報告* (Hydrogeological Survey Report of the Choushui River Alluvial Fan). Taiwan Groundwater Monitoring Network Phase I. MOEA, Taipei.

2. Water Resources Agency (2019). *中華民國108年地下水冊* (2019 Groundwater Yearbook of Taiwan). MOEA, Taipei.

3. Tatas, Chu, H.-J., Burbey, T.J., & Lin, C.-W. (2023). Mapping regional subsidence rate from electricity consumption-based groundwater extraction. *Journal of Hydrology: Regional Studies*, 45, 101289.

4. Ali, M.Z., Chu, H.-J., & Burbey, T.J. (2021). Time-dependent spatial regression for groundwater level estimation using GPS deformation data. *Environmental Modelling & Software*, 143, 105109.

5. Chu, H.-J., Ali, M.Z., & Burbey, T.J. (2021). Spatial regression model for subsidence estimation from drawdown. *Journal of Hydrology: Regional Studies*, 35, 100822.

6. Chu, H.-J., Ali, M.Z., & Burbey, T.J. (2021). Spatio-temporal data fusion of subsidence sensors. *Environmental Modelling & Software*, 137, 104966.

7. Liu, C.-W., Ku, C.-Y., & Ni, C.-F. (2025). Deep learning time-series modeling for assessing land subsidence under reduced groundwater use. *Scientific Reports*.

8. Patra, S.R., Chu, H.-J., & Aman, M.A. (2025). LSTM-based projection of groundwater-induced land subsidence under CMIP6 climate scenarios: A case study of Yunlin, Taiwan. *Science of the Total Environment*.

9. Sung, M.-H. (2019). *Impacts of shallow agricultural pumping on deep aquifer subsidence — Choushui alluvial fan*. MSc Thesis, National Cheng Kung University, Tainan.

10. National Cheng Kung University (2019). *結合HEC-RAS與MODFLOW模式評估濁水溪沖積扇地下水位及地層下陷* (Integrated HEC-RAS and MODFLOW assessment of groundwater level and land subsidence in the Choushui alluvial fan). Tainan.

11. National Chiao Tung University (2009). *地下水補注潛勢評估與地下水模式建置* (Groundwater recharge potential assessment and groundwater model construction). Hsinchu.

12. National Yang Ming Chiao Tung University (2023). *地表補注潛勢評估與地下地質架構分析* (Surface recharge potential assessment and subsurface geological framework analysis). 3-year project report. Hsinchu.

13. National Central University (2023). Mapping hydrogeological structures using transient electromagnetic method: A case study of the Choushui River alluvial fan in Yunlin, Taiwan. *Water*, 15(9), 1703.

14. Zhang, Y.-W. et al. (2017). *以標準化地下水位指數法評估濁水溪沖積扇含水層缺水特性之研究* (Assessment of aquifer water shortage characteristics in the Choushui alluvial fan using the standardised groundwater level index method). MSc Thesis, National Cheng Kung University, Tainan.

15. Water Resources Agency (2022). *尖端地層下陷防治技術整合研究* (Cutting-edge integrated land subsidence prevention technology research). NSTC-WRA joint project. MOEA, Taipei.

16. Ali, M.Z., Burbey, T.J., et al. (2022). Estimation of annual groundwater changes from InSAR-derived land subsidence. *Water and Environment Journal*, 36(4).

17. Hung, W.-C., Hwang, C., Sneed, M., Chen, Y.-A., Chu, C.-H., & Lin, S.-H. (2021). Measuring and interpreting multilayer aquifer-system compactions for a sustainable groundwater-system development. *Water Resources Research*, 57, e2020WR028194. https://doi.org/10.1029/2020WR028194

18. Chu, H.-J., Tatas, Patra, S.R., & Burbey, T.J. (2024). Spatiotemporal subsidence feature decomposition and hotspot identification. *Environmental Earth Sciences*, 83, 124. https://doi.org/10.1007/s12665-024-11427-2

19. Hung, W.-C., Hwang, C., Tosi, L., Lin, G.-Z., Lin, S.-H., & Chen, Y.-A. (2025). Near real-time subsidence monitoring and AI forecasting with multi-depth extensometers. *Engineering Geology* (in review or press).

20. Patra, S.R., Chu, H.-J., & Tatas (2025). Employing machine learning to document trends and seasonality of groundwater-induced subsidence. *Environmental Earth Sciences*, 84.

21. Tatas & Chu, H.-J. (2024). Effective hydraulic head control rule identification for unrecoverable subsidence mitigation. *Water Resources Management*. https://doi.org/10.1007/s11269-024-03816-w

22. Hsu, Y.-J., Kao, H., Bürgmann, R., Lee, Y.-T., Huang, H.-H., Hsu, Y.-F., Wu, Y.-M., & Zhuang, J. (2021). Synchronized and asynchronous modulation of seismicity by hydrological loading: A case study in Taiwan. *Science Advances*, 7, eabf7282. https://doi.org/10.1126/sciadv.abf7282

---

*This report was compiled from web searches and published sources on 2026-05-30 and updated on 2026-06-02 with additional literature from the ZOTERO library. Numerical values and findings are attributed to their respective sources as cited above.*
