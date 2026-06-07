# Near real-time subsidence monitoring and AI forecasting with multi-depth extensometers

Wei-Chia Hung$^{a,d}$, Cheinway Hwang$^{a,*}$, Luigi Tosi$^{b}$, Guan-Zhong Lin$^{a,d}$, Shao-Hung Lin$^{c,d}$, Yi-An Chen$^{d}$

$^{a}$Department of Civil Engineering, National Yang Ming Chiao Tung University, 1001 Ta Hsueh Rd., Hsinchu, 300, Taiwan  
$^{b}$Institute of Geosciences and Earth Resources, National Research Council, Corso Stati Uniti 4, Padova, 35127, Italy  
$^{c}$Department of Geosciences, National Taiwan University, Taipei, 10617, Taiwan  
$^{d}$Green Environmental Engineering Consultant Co. LTD, Room 820, Building 53, 195 Sec.4, Chung-Shing Rd., Chu-Tung, Hsinchu, County, 310, Taiwan  

* Corresponding author: cheinway@nycu.edu.tw

**Keywords:** Land subsidence; Aquifer-system compaction; Extensometer; Artificial intelligence; Groundwater management

## Abstract

Land subsidence induced by excessive groundwater withdrawal poses a growing threat to infrastructure, water resources, and environmental sustainability. Developing robust early warning systems and accurate subsidence forecasts remains a significant key challenge in engineering geology. This study integrates deep, high-frequency extensometer data with AI-based prediction to improve short-term land subsidence forecasting —a novel framework particularly suited for subsidence-prone, groundwater-stressed regions. The AI-driven model enhances predictive accuracy by 35 %, effectively capturing both long-term subsidence trends and seasonal variability. We compare extensometer observations with multilayer compaction well (MLCW) data to evaluate their respective advantages. MLCWs provide millimeter-resolution compaction measurements at up to 20 discrete depths, revealing depth-dependent aquifer-system deformation. Extensometers, by contrast, offer continuous measurements at selected depths (10-min intervals), enabling near-real-time detection of vertical displacement. When combined, the two systems form a hybrid monitoring framework with enhanced spatial and temporal resolution. This integrated approach supports more accurate subsidence assessment and forecasting, informing groundwater management strategies and infrastructure risk mitigation. Our results demonstrate that coupled monitoring and AI modeling are essential tools for sustainable groundwater development in subsidence-prone regions.

## 1. Introduction

Rising global water demand —driven by population growth and economic expansion —has intensified dependence on groundwater, especially in areas lacking sufficient surface water resources. Excessive and prolonged groundwater withdrawal is the leading cause of the most severe cases of land subsidence worldwide (Herrera-García et al., 2021). Aquifer-system compaction resulting from declining groundwater levels can lead to persistent vertical ground deformation, manifesting in infrastructure damage, increased flood susceptibility, and irreversible environmental degradation —all with substantial socio-economic impacts.

In urban environments, land subsidence undermines the stability of buildings, roads, and transit systems, escalating infrastructure maintenance costs and imposing significant economic and social burdens. In low-lying coastal regions, declining land surface elevation exacerbates seawater intrusion into aquifers and promotes soil salinization, reducing freshwater availability, diminishing agricultural productivity, and devaluing land. It is estimated that approximately 19 % of the global population lives in areas vulnerable to subsidence (Herrera-García et al., 2021), with coastal plains and river deltas accounting for nearly 74 % of global subsidence occurrences (Nicholls et al., 2021). Climate change and extreme weather events further compound these risks. Notable cases of rapid land subsidence linked to intensive groundwater withdrawal have been documented in California, Mexico City, Jakarta, and the Mekong Delta (Galloway and Burbey, 2011; Faunt et al., 2016; Erban et al., 2014; Bagheri-Gavkosh et al., 2021; Wu et al., 2022).

To address the risks associated with land subsidence, there is growing adoption of advanced monitoring technologies and artificial intelligence (AI)–based prediction models aimed at improving deformation detection, forecasting subsidence trends, and supporting sustainable groundwater management (Arabameri et al., 2020; Rahmati et al., 2019). However, challenges persist in acquiring high-resolution, depth-dependent, and real-time subsidence measurements. Surface-based geodetic methods such as spirit leveling (SL), the Global Navigation Satellite System (GNSS), and interferometric synthetic aperture radar (InSAR) each have distinct limitations in spatial or temporal resolution. While SL provides high vertical accuracy, it is labor-intensive and typically performed only on an annual or semi-annual basis (Abidin et al., 2005; Fabris et al., 2014; Hung et al., 2017). GNSS offers continuous measurements at specific points but suffers from sparse spatial coverage due to the cost of installation and maintenance (Farolfi et al., 2019; Wang et al., 2022; Zhou et al., 2021; Hung et al., 2023). InSAR facilitates regional-scale monitoring with frequent revisit times, but it requires correction with ground-based GNSS to separate vertical from horizontal motions and remains sensitive to atmospheric effects and satellite orbit errors (Wu et al., 2022; Castellazzi et al., 2016; Haghighi and Motagh, 2019; Hung et al., 2023).

Subsurface deformation monitoring tools —such as multilayer compaction wells (MLCWs), fiber Bragg grating (FBG) sensors, and automated-recording extensometers (AREs) —offer valuable depth-resolved insights into aquifer-system compaction dynamics. However, each technique faces trade-offs in terms of cost, depth capability, and spatial coverage (Riley, 1969; Hoffmann et al., 2003; Liu et al., 2004; Zhang et al., 2007; Burbey, 2020; Wang, 2023). Traditional extensometers, in particular, were often limited by analog instrumentation, lower precision, and infrequent data acquisition, making them less suitable for high-frequency monitoring and short-term predictive applications. To overcome these limitations, a range of geodetic and hydrologic sensors has been deployed in Yunlin County, Taiwan, including continuous GNSS stations, precision leveling benchmarks, MLCWs, extensometers, and groundwater monitoring wells. In recognition of the area’s history of severe subsidence and its strategic importance as a transportation corridor, the Water Resources Agency (WRA) designated Tuku as a land subsidence monitoring supersite.

This study presents an innovative integrated framework that combines high-frequency, depth-specific deformation data from automated deep extensometers with AI-based predictive modeling. We first describe the installation methodology, measurement accuracy, and performance assessment of the extensometers, which are capable of capturing aquifer-system compaction at multiple depths in near real-time. A comparative evaluation follows, outlining the respective strengths and limitations of extensometers and multilayer compaction wells (MLCWs) in terms of temporal resolution, spatial detail, installation requirements, and cost-effectiveness. By fusing depth-resolved monitoring with AI-driven forecasting, this study introduces a scalable and adaptive approach for short-term subsidence prediction, offering critical support for groundwater resource management, infrastructure risk mitigation, and resilient urban development.

## 2. Study area

### 2.1. Hydrostratigraphic settings

The study area is located near Tuku Township in Yunlin County, within the Choushui River Alluvial Fan (CRAF) of central Taiwan, where extensometers and other deformation monitoring sensors have been installed. The Choushui River watershed transitions from mountainous terrain in the east to a broad fan-shaped plain in the west, forming a classical alluvial depositional environment. The stratigraphy exhibits a narrow, westward-tilted arcuate distribution and is primarily composed of three geological units: modern alluvium, terrace gravel, and the deeper Toukeshan Formation gravel. These unconsolidated deposits, which can reach several hundred meters in thickness, consist mainly of alternating layers of clay, sand, and gravel.

The sand and gravel layers are highly permeable and serve as the principal aquifers in the region, providing storage and transmission pathways for groundwater. As illustrated in the hydrogeological conceptual model of the CRAF (Lai et al., 2003; Fig. 1a), the recharge zone lies at the eastern fan apex, where thick, coarse gravel deposits with minimal stratification allow for efficient vertical and lateral groundwater flow. Moving westward, the sedimentary structure becomes increasingly stratified, forming a multilayer aquifer system that includes four primary aquifers interbedded with four aquitards within the upper 330 m. These aquitards impede vertical groundwater movement, resulting in depth-dependent hydraulic behavior and differential compaction potential across the aquifer system. The vertical heterogeneity in hydrogeological properties plays a critical role in governing recharge pathways, groundwater flow, and aquifer-system compaction, which in turn influences the severity and spatial distribution of land subsidence in the region.

To characterize the subsurface structure of the Tuku region, this study employed HQ wireline core sampling in accordance with American Society for Testing and Materials (ASTM) standards. A continuous 400-m sediment core was extracted at Tuku Junior High School, enabling high-resolution stratigraphic interpretation. A total of 135 sediment samples were collected at various depths and analyzed for grain-size distribution, specific gravity, and Atterberg limits to support soil classification. Results indicate that the subsurface consists entirely of unconsolidated alluvial deposits, with the following composition (Fig. 1b): gravel (7 %), medium to coarse sand (37 %), very fine to fine sand (29 %), and fine-grained sediments (27 %). A lithological log constructed from the soil classification (Fig. 1c) reveals alternating layers of permeable and low-permeability sediments.

By integrating the lithological profile (Fig. 1c) with the hydrogeological conceptual model of the CRAF (Lai et al., 2003; Fig. 1a), four major hydrostratigraphic units were identified. Unit B1 (aquifer F1 and aquitard T1) extends from the surface to ~48.5 m, unit B2 (F2 + T2) spans ~48.5 to 162.5 m, unit B3 (F3 + T3) from ~162.5 to 250 m, and unit B4 (F4 + T4) occurs below 250 m. These hydrostratigraphic units form a vertically heterogeneous aquifer system, where fine-grained interbeds act as aquitards capable of generating delayed and inelastic compaction under long-term groundwater extraction.

### 2.2. Land subsidence history

The CRAF is one of Taiwan’s most important agricultural regions. Due to its geomorphological setting, the construction of large-scale surface reservoirs is limited, compelling local communities to rely heavily on both surface water diversion and groundwater extraction to meet domestic and agricultural demands. Historically, the region supported sugarcane cultivation, favored for its relatively low water requirements and rapid growth cycle, which allowed up to three harvests annually. However, with the evolution of land use and agricultural policy, rice cultivation became predominant, leading to the widespread implementation of double-cropping systems. This shift markedly increased irrigation demand, particularly during the dry season, intensifying groundwater withdrawals and exacerbating land subsidence across the region.

Rice cultivation is a highly water-intensive practice, requiring substantial irrigation, particularly during the initial planting stages. Due to limited surface water availability, farmers have increasingly depended on groundwater withdrawals to meet irrigation demands. Prolonged and excessive pumping has led to significant declines in groundwater levels and pore-water pressures, resulting in aquifer-system compaction and widespread land subsidence. This issue is especially acute in the southern CRAF, with Yunlin County experiencing the most severe impacts. Between 1992 and 2021, cumulative subsidence in parts of Yunlin exceeded 150 cm (Fig. 2). The most pronounced subsidence occurs within the central agricultural belt, where rapid ground deformation poses serious risks to regional infrastructure, including the Taiwan High-Speed Rail, which traverses the affected area and requires close monitoring to ensure operational safety.

## 3. Installing the extensometers

### 3.1. The three extensometers and the TKJS supersite

WRA established a land subsidence monitoring supersite in Tuku due to the area’s history of significant aquifer-system compaction (Fig. 2) and its strategic importance as a transportation corridor in Yunlin County. The Tuku Junior High School site (TKJS) was selected for its location at the intersection of the Taiwan High-Speed Rail and National Highway 78 (Fig. 3a). The TKJS supersite comprises two integrated monitoring areas. Monitoring Area A includes three deep extensometers —TKJS130m, TKJS300m, and TKJS400m —installed at depths of 130 m, 300 m, and 400 m, respectively, along with a 400-m-deep groundwater observation well. Monitoring Area B is equipped with a continuous GNSS station, a 300-m-deep MLCW, one precision leveling benchmark, and three groundwater observation wells installed at depths of 87 m, 179 m, and 263 m (Fig. 3b). This configuration enables comprehensive, multi-depth observation of vertical ground deformation and aquifer-system responses to groundwater level variations.

### 3.2. Installation of the extensometers and data quality assessment

Each of the three extensometers installed at Monitoring Area A (Fig. 3) was constructed using a nested pipe configuration within a borehole created by a rotary drilling rig. The installation begins with the placement of a steel outer casing to stabilize the borehole wall. A steel inner pipe is then inserted concentrically within the outer pipe, followed by a central fill pipe. The inner pipe is anchored to a buried concrete support platform located at the bottom of the target depth, isolating it from surface movements.

As groundwater levels decline, increased effective stress in the aquifer system causes compaction of compressible sediments. This compaction results in vertical displacement of the surface platform, which gradually settles. In contrast, the inner steel pipe —anchored to the deep foundation —remains stationary and does not deform. As a result, the inner pipe gradually protrudes above the settling surface platform. The vertical difference between the top of the inner pipe and the ground-level platform is measured to quantify vertical ground deformation. Because the inner pipe is made of rigid steel and anchored below compressible strata, it serves as a reliable reference for detecting cumulative compaction above the anchor point.

A linear variable differential transformer (LVDT) is mounted at the top of the inner pipe to continuously record the relative displacement between the inner pipe and the ground-level platform. This configuration enables precise measurement of vertical deformation, representing the cumulative compression occurring between the surface platform and the subsurface concrete support platform. For manual verification, a leveling ball is affixed to the top of the inner pipe, and a steel benchmark is embedded in the ground-level platform to facilitate periodic differential leveling. A schematic illustration of the automated extensometer monitoring station and its components is provided in Fig. 4.

The installation of the 400-m deep extensometer —representative of the deepest and most comprehensive of the three —was conducted in 10 key steps comprising 16 detailed procedures:

1. **Borehole drilling**  
   A gravity-operated rotary drilling rig (Fig. 5a) was used to bore to a depth of 410 m (Fig. 5b) with an 8-in. diameter drill rod. Soil types and depths were recorded throughout the drilling process.

2. **Installation of outer casing**  
   After reaching 410 m, the drill rod was removed. Steel pipes (6 m in length, 140 mm outer diameter, 5 mm thickness) were used for the lower 378 m, and stainless steel pipes of the same dimensions for the upper 24 m. These were lowered to the bottom of the borehole (Fig. 5c), welded at joints for integrity, and backfilled with fine sand to stabilize the outer casing (Fig. 5d).

3. **Inner pipe assembly**  
   Steel pipes (89 mm outer diameter) were used for the lower 366 m, with stainless steel pipes for the upper 48 m. Spacers were placed every 12 m to prevent contact between the inner and outer pipes. The inner pipe was lowered until its base reached 408 m (Fig. 5e).

4. **Jet cleaning**  
   Steel pipes (40 mm outer diameter, 4 m length) were inserted to jet-clean the base of the borehole (408 –410 m) (Fig. 5f).

5. **Grouting**  
   A 1:1 cement-water slurry was injected under high pressure to create a solid foundation at 408–410 m. After 2–3 days of curing, a second injection filled the interior of the inner pipe from 0 to 408 m (Fig. 5g).

6. **Reference marker**  
   A protective cap and stainless steel leveling ball were welded to the top of the inner pipe to serve as a reference point for future elevation measurements (Fig. 5h).

7. **Corrosion protection**  
   Emulsified asphalt was filled between the inner and outer casings. Its buoyancy above the water table prevents air contact with the steel, reducing corrosion risk (Fig. 5i).

8. **Wellhead construction**  
   The working area was backfilled and leveled. A protective wellhead platform was then installed (Fig. 5j).

9. **Instrumentation setup**  
   The automated measurement system was installed, including an LVDT sensor, data logger, moisture-proof casing, and analysis software (Fig. 5k).

10. **Elevation verification**  
    Leveling surveys were conducted to record the elevations of the stainless steel reference ball and wellhead benchmark (Fig. 5l).

The automated measurement system used for the extensometers comprises a LVDT and an integrated data logger housed within a weatherproof instrument enclosure. The displacement sensor employed is the CDP-100 M model. The LVDT is mounted at the top of the inner pipe (Fig. 6) and continuously measures the relative vertical displacement between the ground-level platform and the anchored inner pipe. This differential displacement represents the cumulative compression occurring in the sediment column between the surface and the support platform at depth, providing a direct measure of aquifer-system compaction above the anchoring point.

During the installation of the electronic displacement sensor, a custom-designed mounting fixture equipped with two specialized clamps is used to secure both the steel reference rod and the LVDT, allowing for precise positioning and future vertical adjustments (Fig. 6a, b). Following installation, a tubular spirit level is employed to verify the vertical alignment of the LVDT to ensure measurement accuracy (Fig. 6c). The data logger used in this study is the CR1000X model, which provides high-resolution, time-stamped recordings of displacement data. An internal view of the data logger and its configuration is shown in Fig. 6d.

After installation, the data logger is programmed to continuously transmit three types of data: (1) extensometer displacement measurements, (2) field voltage readings, and (3) ambient temperature. In addition to capturing real-time ground deformation, this multi-parameter output provides essential diagnostics on system performance, including power supply stability and environmental conditions at the monitoring site.

To evaluate the accuracy and stability of the automated extensometer measurement system, a calibration test was performed using precision shims under controlled conditions. The test employed shims with a nominal thickness of 2.0 mm, each independently verified using a high-resolution vernier caliper. The shims were sequentially inserted beneath the LVDT sensor installed on the TKJS 400 m extensometer, and displacement readings were recorded at one-minute intervals. Measured LVDT displacements were then compared against caliper-based measurements to assess system precision.

As summarized in Table 1, the root mean square error (RMSE) between the LVDT readings and reference measurements was 0.015 mm, confirming the high measurement accuracy and stability of the automated monitoring system.

> **Table 1**  
> Accuracy test of the LVDT sensor used in the TKJS 400 m extensometer.
> 
> | Test Sequence | LVDT Measurement (mm) | Caliper Measurement (mm) | Difference (mm) | Remarks |
> |---------------|------------------------|--------------------------|----------------|---------|
> | 0             | 0.0                    | 0.000                    | 0              | 0 shim  |
> | 1             | 2.029                  | 2.000                    | 0.029          | 1 shim  |
> | 2             | 4.023                  | 4.000                    | 0.023          | 2 shims |
> | 3             | 5.596                  | 6.000                    | 0.000          | 3 shims |
> | RMSE          | —                      | —                        | 0.015          | —       |

## 4. Method for AI-based subsidence prediction using extensometer observations

To enhance the accuracy and responsiveness of land subsidence forecasting, this study integrates high-frequency extensometer observations with an artificial intelligence (AI)–based predictive model. The Prophet model, developed by Facebook’s Core Data Science team, is adopted to analyze temporal trends in subsurface deformation and to forecast short-term variations in vertical displacement. Input data are derived from automated extensometers installed at depths of 130, 300, and 400 m at the TKJS monitoring site, providing continuous, real-time records of aquifer-system compaction.

This high-resolution dataset allows the Prophet model to effectively capture both gradual trends and short-term fluctuations in subsurface deformation, reflecting the dynamic responses of compressible sediments to groundwater level changes. The resulting forecasts offer valuable decision-support tools for groundwater management, early warning systems, and land subsidence risk mitigation.

Prophet, an open-source time series forecasting tool developed by Facebook’s Core Data Science team, is designed to handle datasets exhibiting long-term trends, seasonality, and external influences (Taylor and Letham, 2018). Its strength lies in decomposing time series into interpretable components, making it well-suited for modeling the complex and dynamic nature of land subsidence. We selected Prophet over deep learning alternatives (e.g., LSTM) due to its interpretability, low risk of overfitting on moderate datasets, and ability to explicitly decompose trends and seasonality. Comparative experiments showed that Prophet slightly outperformed an LSTM model in accuracy and training efficiency.

Prophet is an open-source tool designed to model datasets that exhibit long-term trends, seasonal effects, and external influences (Taylor and Letham, 2018). Its strength lies in decomposing complex time series into interpretable components, making it particularly well-suited for capturing the nonlinear and dynamic behavior of land subsidence.

Prior to modeling, the extensometer time series is pre-processed to remove outliers, normalize values, and detect underlying trends. The cleaned dataset is then divided into training and validation subsets—enabling historical data to inform the predictive model while reserving recent observations for performance evaluation. Prophet models the time series using an additive framework:

$$
y(t) = g(t) + s(t) + h(t) + \epsilon_t \tag{1}
$$

where $g(t)$ captures the trend, $s(t)$ represents seasonality, $h(t)$ accounts for known external regressors (e.g., rainfall or pumping policy changes), and $\epsilon_t$ is the error term. The trend component $g(t)$ is modeled using a piecewise linear formulation with automatic changepoint detection (Taylor and Letham, 2018):

$$
g(t) = (k + \mathbf{a}(t)^T \boldsymbol{\delta}) t + (m + b(t)) \tag{2}
$$

where $k$ is the base rate of change, $\mathbf{a}(t)$ is a binary indicator vector for changepoint occurrences, $\boldsymbol{\delta}$ is a vector of rate adjustments at those changepoints, $m$ is the offset parameter, and $b(t)$ ensures continuity at changepoints. This structure allows the model to flexibly adapt to abrupt changes in subsidence rates, enabling the detection of episodic deformation events driven by hydrological or anthropogenic factors.

Parameter estimation in Prophet is conducted using either maximum a posteriori (MAP) estimation or Markov Chain Monte Carlo (MCMC) sampling within a Bayesian framework. The underlying probabilistic model is expressed as:

$$
p(\theta | y) \propto p(y | \theta) p(\theta) \tag{3}
$$

where $\theta$ is the vector of model parameters, $p(y | \theta)$ is the likelihood of the observed data, and $p(\theta)$ represents the prior distribution of parameters. These computations are executed by the Stan engine, which serves as the numerical backend of Prophet, enabling efficient statistical inference and robust parameter estimation.

The training and forecasting workflow employed in this study is illustrated in Fig. 7. Time series preprocessing and post-modeling analyses were performed in a Python environment, while Stan handled the core Bayesian computations. The Prophet model effectively captured both long-term trends and seasonal variability in the high-frequency extensometer data, enabling accurate predictions of subsurface deformation.

These forecasts provide important insights into aquifer-system compaction behavior and are directly applicable to groundwater resource management, subsidence risk mitigation, and infrastructure protection in vulnerable regions.

## 5. Supporting sensor data for the analysis of extensometer observations

To strengthen the interpretation of extensometer-derived deformation data and improve the reliability of AI-based subsidence forecasts, this study integrates supporting observations from a multi-sensor monitoring network. These include MLCWs, spirit leveling benchmarks, GNSS stations, and groundwater level records. Collectively, these complementary datasets provide essential spatial and temporal context for the high-frequency extensometer measurements. The additional data enable cross-validation of deformation signals, support the characterization of depth-specific compaction behavior, and help establish causal relationships between groundwater level changes and aquifer-system deformation. By integrating multiple observation types, the study enhances confidence in the performance of the automated extensometer system and facilitates refinement of the AI-based predictive model.

### 5.1. Multi-layer compaction monitoring well (MLCW)

The MLCW is designed to measure depth-resolved subsurface compaction by pre-installing magnetic rings at multiple intervals along the borehole column —typically allowing for the placement of up to 20 magnetic markers within a single well. A magnetic sensing probe is periodically lowered into the well to detect the position of each magnetic ring relative to a surface reference point. By tracking temporal changes in the vertical position of each ring, the cumulative compaction of specific sediment layers can be determined, thereby identifying the principal compressible strata within the aquifer system (Hung et al., 2021).

Key advantages of the MLCW system include its ability to monitor multiple stratigraphic layers simultaneously, flexibility in measurement depth configuration, high positional accuracy and repeatability, and long-term durability. These features make MLCWs particularly well-suited for assessing the vertical distribution of compaction in layered alluvial systems undergoing groundwater-induced subsidence.

### 5.2. Spirit leveling

A high-precision spirit leveling network covering approximately 1000 km has been established across the Choushui River Alluvial Fan (CRAF) to monitor vertical ground displacement and assess long-term land subsidence trends. To ensure data quality and consistency, the Water Resources Agency (WRA) has implemented standardized operating procedures for leveling-based subsidence monitoring (Water Resource Agency (WRA), 2019). These standards include:

- The allowable closure error per survey line or loop must be less than $3 \text{ mm} \sqrt{K}$, where $K$ is the distance between adjacent benchmarks (in kilometers).
- Foresight and backsight distances must be approximately equal at each station.
- The maximum sight length must not exceed 50 m.
- The difference between foresight and backsight distances at any setup must be within 1 m.
- The cumulative difference in foresight and backsight distances for any individual survey section must be less than 5 m.
- After network adjustment, residuals must follow a normal distribution and pass the 95 % TAU outlier detection test.

Spirit leveling is widely regarded as the most accurate method for measuring vertical displacements and remains a critical tool for validating other monitoring techniques. However, its labor-intensive nature and the need for clear line-of-sight restrict its temporal resolution. In practice, leveling surveys are typically conducted once per year, limiting their ability to capture short-term or transient deformation.

### 5.3. GNSS

To monitor land subsidence across the CRAF, WRA has established 24 continuous GNSS stations. These are integrated with 26 additional continuous stations operated by other agencies, forming the CRAF GNSS_NET —a regional monitoring network consisting of 50 GNSS stations (Fig. 2).

This study utilizes GNSS data from station TJHS, spanning January 2011 to December 2022. Daily coordinate solutions were derived using KMNM as the reference station. Vertical displacement at each station was extracted and presented as a time series, and a curve-fitting method was applied to estimate long-term subsidence trends and seasonal variations.

GNSS offers high-precision, continuous monitoring capabilities, making it well-suited for analyzing long-term ground deformation and identifying secular trends in land subsidence. However, due to the relatively high cost of installation and maintenance, GNSS networks often have limited spatial resolution. As such, GNSS is frequently used in conjunction with complementary methods such as spirit leveling, InSAR, and MLCWs to provide a more complete assessment of surface and subsurface deformation.

### 5.4. Groundwater monitoring wells

Monitoring groundwater levels is essential for understanding the relationship between aquifer depletion and land subsidence. Groundwater-level fluctuations reflect changes in pore-water pressure and effective stress within compressible sediments —key drivers of aquifer-system compaction. As part of its groundwater resource management strategy, WRA has progressively established a network of 223 groundwater observation wells throughout the CRAF. These wells support long-term hydrologic monitoring and inform subsidence mitigation policies.

The observation wells are distributed across four primary aquifers: 73 wells in the first aquifer, 87 in the second, 47 in the third, and 17 in the fourth (Fig. 2). This stratified network enables depth-specific monitoring of groundwater level variations and provides a critical dataset for evaluating temporal and spatial correlations between groundwater drawdown and measured land subsidence. When analyzed in conjunction with extensometer, MLCW, and GNSS data, the groundwater records enhance our understanding of aquifer-system dynamics and support integrated subsidence risk assessment.

## 6. Monitoring results

### 6.1. Extensometer observations

This section presents vertical deformation data from the automated deep extensometers installed at the TKJS monitoring site in Tuku, within the central CRAF. The site includes three extensometers anchored at depths of 130, 300, and 400 m, enabling multi-depth analysis of aquifer-system compaction and rebound behavior. Fig. 8 presents a schematic diagram of compression at different depths, derived from the comparative analysis of data collected by multiple deep borehole extensometers. To ensure consistency, the analysis focuses on the overlapping observation period among the three instruments (Fig. 9).

Taiwan’s pronounced wet (June –October) and dry (November –April) seasonal cycle provides a natural context to explore the relationship between precipitation, groundwater level changes, and vertical ground displacement. During the wet season, increased rainfall leads to partial groundwater recharge and minor surface rebound. Conversely, in the dry season, intensified groundwater withdrawal leads to pronounced subsidence. Extensometer data confirm this pattern: displacement accelerates during dry months and partially recovers during the wet season. However, the observed rebound is generally smaller, suggesting that a significant portion of the compaction is inelastic and permanent (Fig. 10).

Displacement behavior also varies by depth. The shallow zone (0–130 m), with higher porosity and greater sensitivity to pore-pressure changes, exhibits the most prominent subsidence–rebound cycles. The intermediate zone (130 –300 m) shows dampened seasonal response, while strata below 300 m experience gradual, persistent compaction with minimal short-term response to hydrologic forcing. These findings stress the importance of depth-resolved monitoring to capture the full spectrum of aquifer-system deformation and to inform more effective groundwater and land subsidence management strategies.

The results show that the shallow zone (above 130 m) is subject to greater seasonal variability, with noticeable rebound during groundwater recharge periods. In contrast, the deeper zones (300 and 400 m) exhibit slow, continuous subsidence with limited or negligible recovery (Fig. 9). These depth-dependent trends emphasize the cumulative and largely irreversible nature of deep aquifer-system compaction. To differentiate between delayed elastic and inelastic deformation, we analyzed paired groundwater–displacement time series at various depths (Fig. 11), showing persistent compaction despite partial recovery in hydraulic head, supporting the dominance of inelastic behavior.

Fig. 11 shows the extension of the 130-m extensometer at Tuku interpreted as stress, paired with the groundwater level changes at 87 m as strain. The compression between 300 m and 130 m (i.e., the extension of the 300-m extensometer minus the extension of the 130-m extensometer) is paired with the groundwater level and displacement time series at 263 m to derive the stress–strain relationship.

Fig. 11 indicates that during the dry season, groundwater levels decline due to groundwater extraction. This causes a drop in pore water pressure, leading to an increase in effective stress, which subsequently results in compression of the strata and surface subsidence. When the wet season arrives, the groundwater level begins to recover, the effective stress decreases, and the amount of compression in the strata reduces, leading to slight surface rebound. This phenomenon is mainly due to the fact that the period from January to May in the study area is the spring cultivation season for rice, which requires a substantial amount of water. As a result, groundwater extraction during this time is high, and land subsidence is more pronounced.

Such seasonal fluctuations cause the compression within the 0–130 m depth range to be more significant than that between 130 and 300 m. This is primarily because agricultural wells in Taiwan mostly tap into the second aquifer, which lies within the shallower depths.

Furthermore, the figure also shows that when groundwater levels begin to decline, subsidence occurs rapidly. However, when the groundwater level rises, the shallow strata rebound more quickly, while the deep strata rebound more slowly. This is mainly because during rainfall, groundwater recharges from shallow to deep levels. Therefore, shallow groundwater levels recover faster, leading to quicker rebound, whereas the deeper levels respond more slowly. According to the geological profile in Fig. 1, the strata below 130 m contain more compressible soils such as silt and clay, which do rebound but exhibit a certain delay effect. However, in this specific case, the delay is not particularly pronounced.

### 6.2. MLCW observations

This section presents results from the long-term monitoring of the MLCW (Fig. 12) at the TKJS site to evaluate depth-specific compaction and its association with groundwater withdrawal. As shown in Section 5.1, the MLCW extends to a depth of 300 m and is equipped with 20 magnetic induction rings. Based on sediment core analysis and the regional hydrogeological model, the local stratigraphy is divided into four major hydrostratigraphic units: B1 (0–48.5 m), B2 (48.5 –162.5 m), B3 (162.5 –250 m), and B4 (below 250 m). Between December 2014 and December 2024, the MLCW recorded a cumulative vertical displacement of approximately 25 cm. The majority of compaction occurred within two zones: a deep zone spanning 220–295 m (corresponding to Aquifers 3 and 4) and a shallower zone from the surface to 200 m (covering Aquifers 1 and 2), though compaction magnitudes in the shallower zone were comparatively lower. Fig. 13 utilizes data from the subsidence monitoring well to identify the main compression depths and magnitudes at various depths. From the figure, it is evident that significant compression occurred in the depth ranges of 50–156 m and 241–295 m.

These results indicate that land subsidence in the CRAF is primarily driven by groundwater-level decline and associated increases in effective stress, particularly in deep, sand-dominated layers interbedded with silt and clay. High-permeability sand units adjacent to fine-grained sediments are especially susceptible to compaction. Notably, compaction observed in deeper aquifer systems tends to be largely inelastic and irreversible, contributing to long-term cumulative subsidence. This underscores the critical importance of depth-resolved monitoring for characterizing the full vertical profile of aquifer-system deformation and for informing sustainable groundwater extraction practices.

### 6.3. Groundwater measurements

This section analyzes long-term groundwater level variations and their relationship with rainfall using data from four observation wells and one meteorological station in the Tuku and Hunglung areas. The groundwater level data were obtained from three nested wells at the TKJS site—Tuku 87 m, Tuku 179 m, and Tuku 263 m—and from an additional well at Hunglung (Hunglung 36 m). Rainfall data were collected from a meteorological station in Hunglung. The analysis spans a nine-year period from 2015 to 2023 and aims to identify the temporal relationship between precipitation patterns and groundwater fluctuations across different aquifer depths.

Overall, groundwater levels exhibit a long-term declining trend superimposed on seasonal oscillations, generally following the regional wet and dry season cycles (Fig. 14). The slopes and amplitudes for each aquifer are summarized in Table 2, with the following key findings:

1. Shallow aquifer (Hunglung 36 m, depth ~ 36 m):  
   This aquifer exhibits the highest long-term decline rate of approximately 0.48 m per year. Seasonal variations are relatively modest, with an annual amplitude of around 0.98 m.

2. Intermediate aquifer (Tuku 87 m and Tuku 179 m, depths ~ 87–179 m):  
   Groundwater levels in this zone show the largest seasonal fluctuations, with an annual amplitude of approximately 2.4 m. The long-term decline rate is about 0.30 m per year.

3. Deep aquifer (Tuku 263 m, depth ~ 263 m):  
   This aquifer demonstrates the most stable behavior, with a gradual decline rate of about 0.18 m per year and moderate seasonal variation, showing an annual amplitude of roughly 1.88 m.

These findings highlight the stratified hydrogeologic response to rainfall and groundwater use in the CRAF region. Shallow aquifers respond more rapidly to seasonal recharge and pumping, while deeper aquifers show delayed but persistent declines, reflecting reduced recharge and potential long-term depletion.

> **Table 2**  
> Groundwater level decline rates and annual amplitudes for four aquifers in the Tuku area (2015 –2023)
> 
> | Aquifer | Observation well | Depth (m) | Decline rate (m/yr) | Annual amplitude (m) |
> |---------|------------------|-----------|---------------------|----------------------|
> | 1       | Hunglun          | 36        | 0.48                | 0.98                 |
> | 2       | Tuku             | 87        | 0.31                | 2.44                 |
> | 3       | Tuku             | 179       | 0.31                | 2.41                 |
> | 4       | Tuku             | 263       | 0.18                | 1.88                 |

## 7. Near real-time AI-predicted land subsidence and accuracy

To evaluate the effectiveness of AI-based forecasting for near real-time land subsidence monitoring, this study applied the Prophet time series model to vertical displacement data recorded by the TJHS extensometer at a depth of 263 m. The training dataset spanned from October 2015 to February 2024 and included continuous, high-frequency observations of subsurface deformation. Using this model, forecasts were generated for a four-month period (July to October 2024) and subsequently compared against newly acquired measurement data not included in the training set to assess predictive performance.

The results of the prediction are illustrated in Fig. 15, which compares model outputs before and after parameter optimization. The initial model (Fig. 15a), trained with default parameters, successfully captured the general trends and inflection points in the subsidence time series. However, the optimized model (Fig. 15b), which incorporated tuned parameters for changepoint sensitivity, seasonality, and prior distributions, showed improved alignment with both the magnitude and timing of measured deformation events, particularly those associated with seasonal groundwater withdrawal and recharge.

To quantitatively assess forecast performance, the Root Mean Squared Error (RMSE) was calculated as:

$$
RMSE = \sqrt{\frac{1}{n}\sum_{i=1}^{n}(y_{pred} - y_{actual})^2} \tag{4}
$$

where $y_{pred}$ and $y_{actual}$ represent the predicted and observed displacement values, and $n$ is the number of observations over the forecast period.

For the four-month evaluation window (July to October 2024), the RMSE prior to optimization was 0.52 mm, while the optimized model achieved an RMSE of 0.34 mm, corresponding to a 35 % improvement in prediction accuracy. This reduction in error demonstrates the value of parameter tuning in enhancing the model’s ability to replicate both the long-term subsidence trend and short-term seasonal variations. To evaluate robustness, we conducted a Monte Carlo simulation by perturbing input time series with Gaussian noise reflective of sensor uncertainty. The resulting forecast RMSE varied within ±0.05 mm, affirming the model’s reliability under typical observational noise.

Overall, these results validate the potential of the Prophet model, when paired with continuous extensometer data, as a viable tool for near real-time forecasting of land subsidence. The improved model performance following parameter optimization shows the importance of customizing model settings to the geophysical characteristics of the study area. Such forecasting tools are essential for early warning systems and adaptive groundwater management, particularly in regions where infrastructure and resource planning must respond dynamically to subsidence hazards.

## 8. Discussion: integrating monitoring technologies and AI for subsidence management

### 8.1. Comparison of extensometers and MLCW systems

The monitoring results from the central Choushui River Alluvial Fan (CRAF) confirm that land subsidence is strongly correlated with long-term groundwater extraction, particularly in deeper sand layers interbedded with silt and clay. In these zones, sustained groundwater-level decline increases effective stress, leading to significant aquifer-system compaction.

To evaluate measurement consistency and explore the strengths of different monitoring approaches, displacement data from TKJS extensometers were compared with corresponding records from the multi-layer compaction well (MLCW). The comparison focused on matched depth intervals —specifically, 123 m in the MLCW and 130 m in the extensometer, and 294 m in the MLCW versus 300 m in the extensometer. In both cases, the deformation trends aligned closely, with the extensometers showing slightly higher magnitudes of compaction at similar depths (Fig. 16). The RMSE between paired observations over the same period was approximately 1.0 cm, indicating strong agreement between the two systems. The observed 1 cm RMSE between the two systems primarily arises from slight mismatches in depth alignment and accumulated offsets over long-term monitoring, rather than instrumentation noise.

Each system offers distinct advantages. The MLCW excels in spatial resolution, with the capability to install up to 20 magnetic induction rings in a single well. This allows detailed profiling of compaction across multiple stratigraphic units, making it especially valuable for identifying depth-specific zones of deformation associated with aquifer heterogeneity and differential compressibility. However, MLCW measurements are typically collected manually at monthly or quarterly intervals, limiting their temporal resolution and applicability for near real-time decision-making.

In contrast, extensometers provide high-frequency, automated measurements —typically recorded every 10 min. This capability enables the detection of short-term fluctuations and subtle deformation changes that may occur in response to daily or seasonal variations in groundwater extraction and recharge. As a result, extensometers are well-suited for applications that demand continuous monitoring, such as early warning systems and infrastructure safety assessments. The main limitation, however, is that each extensometer captures displacement only at a single anchor depth, requiring multiple installations to assess layered deformation, which increases logistical complexity and cost.

Table 3 summarizes the main features, advantages, and limitations of each system. Given their complementary capabilities, a hybrid monitoring strategy that combines both technologies is recommended to achieve comprehensive subsidence monitoring. Such integration can be applied as follows:

1. Long-term, stratified compaction analysis:  
   MLCWs are optimal for capturing the vertical distribution of compaction across aquifer systems, providing critical insight into which layers contribute most to land subsidence. This spatial information supports groundwater management decisions, particularly in the design and evaluation of mitigation strategies.

2. High-frequency monitoring for critical infrastructure:  
   Extensometers are essential for environments where real-time data are needed —such as areas near high-speed railways, highways, or densely populated urban zones. Their rapid response time enables timely detection of subsidence acceleration, informing early intervention.

By integrating MLCWs and extensometers in a coordinated monitoring framework, stakeholders can benefit from both depth-resolved spatial profiling and high-frequency temporal monitoring. This hybrid system supports more accurate, timely, and informed decisions for groundwater extraction policies, infrastructure resilience planning, and scientific studies of subsurface deformation processes.

> **Table 3**  
> Comparison of MLCW and extensometer systems.
> 
> | Parameter                     | MLCW                                    | Extensometer                                  |
> |-------------------------------|-----------------------------------------|-----------------------------------------------|
> | Monitoring depth coverage     | Multi-layer (up to 20 depths)           | Single depth (based on installed design)      |
> | Measurement frequency         | Monthly (manual operation)              | Every 10 min (automated)                      |
> | Measurement method            | Manual                                  | Automated                                     |
> | Personnel required            | Two operators per session               | None (automated data collection)              |
> | Measurement accuracy          | mm level                                | Millimeter level                              |
> | Maximum installation depth    | Up to 340 m                             | Site-specific (e.g., 130 m, 300 m, 400 m)     |
> | Instrument cost               | Low                                     | High                                          |
> | Operational cost              | Low                                     | High                                          |
> | Construction complexity/cost  | Low                                     | High                                          |

### 8.2. Role of AI in forecasting and managing land subsidence

AI–based forecasting models, when integrated with high-frequency geotechnical monitoring, represent a transformative advancement in the management of land subsidence. The application of time series forecasting tools such as Prophet to continuous displacement records from extensometers —measured at 10-min intervals —enables the real-time analysis of deformation trends and the detection of rapid responses to changes in groundwater conditions. This fusion of data and modeling allows for timely assessments of subsidence risk and supports evidence-based groundwater management strategies.

The predictive capacity of AI is especially valuable in systems where subsidence is strongly coupled to groundwater dynamics. As the hydraulic head declines due to groundwater extraction, effective stress within aquifer systems increases, leading to inelastic compaction of compressible layers (Fig. 17). Conversely, when groundwater levels recover, limited elastic rebound may occur in certain layers —although typically not enough to reverse the cumulative effects of previous compaction. This behavior has been consistently observed in extensometer records across the CRAF, particularly in response to seasonal hydrologic variability.

While seasonal rebound during the wet months suggests the presence of some elastic recovery in the upper aquifer layers, the long-term trends, particularly in deeper strata, are characterized by persistent, non-recoverable displacement. The distinction between inelastic and delayed elastic compaction was inferred based on depth-specific extensometer records and their correlation with groundwater level fluctuations over multiple seasonal cycles. However, we acknowledge that delayed elastic responses occurring over decadal timescales may not be fully captured within the current observation window. Future studies incorporating longer-term monitoring and poroelastic modeling are essential to more definitively separate delayed elastic recovery from permanent compaction in thick, fine-grained sediments.

A salient example occurred during Taiwan’s historic drought in 2021, the most severe in a century. Groundwater levels dropped to record lows, and extensometer data from that year captured exceptional rates of subsurface compaction. This event highlights the severe consequences of prolonged over-extraction and underscores the importance of predictive modeling in supporting drought resilience.

Based on long-term observations, the annual subsidence pattern in the CRAF can be divided into three distinct periods:

1. Dry season (January–May):  
   This period aligns with Taiwan’s first rice planting season, when agricultural water demand peaks. With limited rainfall, farmers rely heavily on groundwater extraction, leading to rapid declines in hydraulic head and pronounced subsurface compaction. Year after year, this dry-season interval corresponds with the most severe land subsidence, as recorded by deep extensometers.

2. Wet season (June–September):  
   Typhoons and monsoonal rainfall during this period contribute to substantial groundwater recharge. As hydraulic head increases, some aquifer layers exhibit limited rebound. However, the observed rebound is consistently smaller than the compaction that occurred during the preceding dry season, confirming that a portion of the deformation is permanent.

3. Post-monsoon cropping season (September–December):  
   This interval marks Taiwan’s second cropping season, typically involving less water-intensive dry farming. With residual rainfall and lower irrigation demands, groundwater levels decline more slowly, resulting in minimal new compaction. The rate of land subsidence during this period is relatively low.

These seasonal trends—particularly the strong correlation between dry-season withdrawal and peak subsidence—reinforce the utility of AI models for short-term forecasting and proactive groundwater management. By capturing both the timing and magnitude of deformation, AI-enhanced prediction tools can inform regulatory interventions (e.g., pumping restrictions), guide infrastructure risk assessments, and support adaptive planning in areas prone to subsidence.

While the Prophet model performed effectively in the CRAF region, it is important to acknowledge that all machine learning models, including Prophet, are inherently data-driven and must be calibrated to local site conditions. The underlying subsidence behavior depends heavily on region-specific factors such as aquifer stratigraphy, sediment compressibility, groundwater extraction practices, and climatic variability. Therefore, model transferability to other geographic contexts requires re-training and validation with locally relevant data. This limitation underscores a key principle in engineering geology: AI models must be tailored to the physical and hydrogeological characteristics of the site to ensure reliable and actionable forecasting.

## 9. Conclusions

This study presents a novel integrated monitoring and forecasting framework for land subsidence by combining high-frequency extensometer observations with AI-based time series modeling. Deep extensometers—extending to 400 m—were installed at multiple depths at the TKJS supersite to provide continuous, high-resolution records of subsurface deformation. These installations represent some of the deepest reported extensometer deployments in the literature and offer rare insights into long-term compaction dynamics across aquifer systems with complex stratigraphy. When analyzed in conjunction with data from GNSS, MLCWs, spirit leveling, and groundwater monitoring wells, these observations reveal a detailed picture of depth-dependent compaction driven by seasonal groundwater fluctuations and long-term over-extraction.

The application of the Prophet forecasting model demonstrated the effectiveness of AI in predicting short-term subsidence trends. With parameter optimization, the model achieved a 35 % improvement in predictive accuracy, enabling more timely identification of critical deformation patterns. These forecasts offer actionable insights for early warning systems, infrastructure protection, and sustainable groundwater resource planning—especially in regions where over-pumping poses significant subsidence risks to transportation infrastructure, agriculture, and urban development.

The findings also show the complementary nature of extensometers and MLCW systems. Extensometers provide automated, near real-time monitoring at specific depths, while MLCWs enable stratified assessments of compaction across multiple layers. A hybrid monitoring strategy that integrates both technologies—combined with AI-based forecasting—can significantly improve the spatiotemporal resolution and reliability of subsidence monitoring systems.

This scalable, data-driven approach supports long-term groundwater sustainability and adaptive risk management. It also provides a robust foundation for broader implementation in other subsidence-prone regions and contributes to international efforts aimed at building resilience in groundwater-dependent communities.

In conclusion, our results indicate a methodological breakthrough in the integration of high-frequency geotechnical monitoring with AI-based forecasting. By demonstrating that subsidence trends and seasonal deformation can be captured with 10-min resolution using an interpretable and operationally efficient model like Prophet, this study advances the practical application of AI in geotechnical risk management. It offers a replicable framework for near real-time monitoring and forecasting, setting a new standard for precision and responsiveness in subsidence-prone regions. Rather, the findings reinforce existing knowledge on the relationship between groundwater extraction and aquifer compaction while demonstrating the practical benefits of automating subsidence forecasting.

For the field of engineering geology, it represents a significant advancement in proactive geotechnical risk management, infrastructure resilience planning, and the sustainable exploitation of multilayer aquifer systems.

## CRediT authorship contribution statement

**Wei-Chia Hung:** Writing – review & editing, Writing – original draft, Visualization, Validation, Supervision, Software, Resources, Project administration, Methodology, Investigation, Funding acquisition, Formal analysis, Data curation, Conceptualization. **Cheinway Hwang:** Writing – original draft, Validation, Supervision, Resources, Project administration, Methodology, Investigation, Funding acquisition, Formal analysis, Data curation, Conceptualization. **Luigi Tosi:** Writing – review & editing, Methodology, Investigation, Formal analysis. **Guan-Zhong Lin:** Writing – review & editing, Visualization, Validation, Software, Methodology, Formal analysis. **Shao-Hung Lin:** Visualization, Validation, Software, Methodology, Formal analysis, Data curation. **Yi-An Chen:** Visualization, Validation, Resources, Methodology, Data curation.

## Declaration of competing interest

The authors declare no conflict of interest.

## Acknowledgments

This study was supported by the Water Resources Agency, Taiwan, and the National Science and Technology Council, Taiwan, under Grant 112-2221-E-A49-025-MY3.

## Data availability

All data are available upon request from the first and corresponding authors.

## References

1. Abidin, H.Z., Andreas, H., Gamal, M., Djaja, R., Subarya, C., Hirose, K., Rajiyowiryono, H., 2005. Monitoring land subsidence in Jakarta (Indonesia) using leveling, GPS survey, and InSAR techniques. In: A Window on the Future of Geodesy: Proceedings of the International Association of Geodesy IAG General Assembly Sapporo, Japan June 30–July 11, 2003. Springer, Berlin Heidelberg, pp. 561–566.
2. Arabameri, Alireza, et al., 2020. A novel ensemble computational intelligence approach for the spatial prediction of land subsidence susceptibility. Sci. Total Environ. 726, 138595.
3. Bagheri-Gavkosh, M., Hosseini, S.M., Ataie-Ashtiani, B., Sohani, Y., Ebrahimian, H., Morovat, F., Ashrafi, S., 2021. Land subsidence: a global challenge. Sci. Total Environ. 778, 146193.
4. Burbey, T.J., 2020. Extensometer Forensics: What Can the Data Really Tell us?
5. Castellazzi, P., Arroyo-Domínguez, N., Martel, R., Calderhead, A.I., Normand, J.C., Gárfias, J., Rivera, A., 2016. Land subsidence in major cities of Central Mexico: Interpreting InSAR-derived land subsidence mapping with hydrogeological data. Int. J. Appl. Earth Obs. Geoinf. 47, 102–111.
6. Erban, L.E., Gorelick, S.M., Zebker, H.A., 2014. Groundwater extraction, land subsidence, and sea-level rise in the Mekong Delta, Vietnam. Environ. Res. Lett. 9 (8), 084010.
7. Fabris, M., Achilli, V., Menin, A., 2014. Estimation of subsidence in Po Delta area (Northern Italy) by integration of GPS data, high-precision leveling and archival orthometric elevations. Int. J. Geosci. 5 (06), 571.
8. Farolfi, G., Del Soldato, M., Bianchini, S., Casagli, N., 2019. A procedure to use GNSS data to calibrate satellite PSI data for the study of subsidence: an example from the north-western Adriatic coast (Italy). Eur. J. Remote Sens. 52 (sup4), 54–63.
9. Faunt, C.C., Sneed, M., Traum, J., Brandt, J.T., 2016. Water availability and land subsidence in the Central Valley, California, USA. Hydrogeol. J. 24 (3), 675.
10. Galloway, D.L., Burbey, T.J., 2011. Regional land subsidence accompanying groundwater extraction. Hydrogeol. J. 19 (8), 1459.
11. Haghighi, M.H., Motagh, M., 2019. Ground surface response to continuous compaction of aquifer system in Tehran, Iran: results from a long-term multi-sensor InSAR analysis. Remote Sens. Environ. 221, 534–550.
12. Herrera-García, G., Ezquerro, P., Tomás, R., Béjar-Pizarro, M., López-Vinielles, J., Rossi, M., Mateos, R.M., Carreón-Freyre, D., Lambert, J., Teatini, P., Cabral-Cano, E., Erkens, G., Galloway, D., Hung, W.-C., Kakar, N., Sneed, M., Tosi, L., Wang, H., Ye, S., 2021. Mapping the global threat of land subsidence. Science 371 (6524), 34–36.
13. Hoffmann, J., Galloway, D.L., Zebker, H.A., 2003. Inverse modeling of interbed storage parameters using land subsidence observations, Antelope Valley, California. Water Resources Research 39 (2).
14. Hung, W.C., Hwang, C., Chen, Y.A., Zhang, L., Chen, K.H., Wei, S.H., Huang, D.R., Lin, S.H., 2017. Land subsidence in Chiayi, Taiwan, from compaction well, leveling and alos/palsar: Aquaculture-induced relative sea level rise. Remote Sens 10 (1), 40.
15. Hung, W.C., Hwang, C., Sneed, M., Chen, Y.A., Chu, C.H., Lin, S.H., 2021. Measuring and interpreting multilayer aquifer-system compactions for a sustainable groundwater-system development. Water Resour. Res. 57 (4) e2020WR028194.
16. Hung, W.C., Hwang, C., Tosi, L., Lin, S.H., Tsai, P.C., Chen, Y.A., Ge, S., 2023. Toward sustainable inland aquaculture: Coastal subsidence monitoring in Taiwan. Remote Sens. Appl.: Soc. Environ. 30, 100930.
17. Lai, D.-C., Fei, L.-Y., Chiang, C.-J., 2003. Regional characteristics of groundwater in Taiwan. In: Proceedings of the Symposium on Hydrogeological Survey and Application, pp. 1–24.
18. Liu, C.H., Pan, Y.W., Liao, J.J., Hung, W.C., 2004. Estimating coefficients of volume compressibility from compression of strata and piezometric changes in a multiaquifer system in West Taiwan. Eng. Geol. 75 (1), 33–47.
19. Nicholls, R.J., Lincke, D., Hinkel, J., Brown, S., Vafeidis, A.T., Meyssignac, B., Fang, J., 2021. A global analysis of subsidence, relative sea-level change and coastal flood exposure. Nat. Clim. Chang. 11 (4), 338–342.
20. Rahmati, O., Golkarian, A., Biggs, T., Keesstra, S., Mohammadi, F., Daliakopoulos, I.N., 2019. Land subsidence hazard modeling: machine learning to identify predictors and the role of human activities. J. Environ. Manag. 236, 466–480.
21. Riley, F.S., 1969. Analysis of borehole extensometer data from central California 2, 423–431. https://unesdoc.unesco.org/ark:/48223/pf0000014816.
22. Taylor, S.J., Letham, B., 2018. Forecasting at scale. Am. Stat. 72 (1), 37–45.
23. Wang, G., 2023. Seasonal subsidence and heave recorded by borehole extensometers in Houston. J. Surv. Eng. 149 (1), 04022018.
24. Wang, G., Greuter, A., Petersen, C.M., Turco, M.J., 2022. Houston GNSS network for subsidence and faulting monitoring: Data analysis methods and products. J. Surv. Eng. 148 (4), 04022008.
25. Water Resource Agency (WRA), 2019. Monitoring and Analyzing Land Subsidence of Taipei, Chiayi, Tainan and Pingtung Area in 2019. Report of Green Environment Engineering Consultant Co. LTD (GEEC), Hsinchu (in Chinese).
26. Wu, P.C., Wei, M., D’Hondt, S., 2022. Subsidence in coastal cities throughout the world observed by InSAR. Geophys. Res. Lett. 49 (7) e2022GL098477.
27. Zhang, Y., Xue, Y.Q., Wu, J.C., Ye, S.J., Wei, Z.X., Li, Q.F., Yu, J., 2007. Characteristics of aquifer system deformation in the Southern Yangtse Delta, China. Engineering Geology 90 (3–4), 160–173.
28. Zhou, X., Wang, G., Wang, K., Liu, H., Lyu, H., Turco, M.J., 2021. Rates of natural subsidence along the Texas coast derived from GPS and tide gauge measurements (1904 –2020). J. Surv. Eng. 147 (4), 04021020.