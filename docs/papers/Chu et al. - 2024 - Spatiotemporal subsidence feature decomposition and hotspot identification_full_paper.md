# Spatiotemporal subsidence feature decomposition and hotspot identification

**Hone‑Jay Chu¹ · Tatas¹,² · Sumriti Ranjan Patra¹ · Thomas J. Burbey³**  
¹ National Cheng Kung University, No.1, University Road, Tainan City 701, Taiwan  
² Institut Teknologi Sepuluh Nopember, Surabaya, Indonesia  
³ Virginia Tech, Blacksburg, VA, USA  

*Received: 15 August 2023 / Accepted: 2 January 2024 / Published online: 4 February 2024*

## Abstract

Subsidence occurs from excessive groundwater drawdown, but varies in response to underlying hydrogeologic conditions, land use factors, and variations of pumping rates. For subsidence feature decomposition, the empirical orthogonal function (EOF) is used to identify to extract the main components of the land subsidence data, such as continuous trend of subsidence and seasonal subsidence from various regions. Result shows that the major subsidence feature components contain the long-term, periodic (seasonal), and intra-seasonal ones which are related to human activities and hydrogeology from the inland, distal-fan area and coastal area in west-central Taiwan. The subsidence trend and seasonal variation at the observations can be separated from empirical mode decomposition (EMD) for validation. Moreover, subsidence and groundwater monitoring data are used to generate the stress–strain relations at the major EOFs locations. The outcome implies a strongly elastic nature, yet reveals a diverse correlation between stress and strain within the subsidence region. The decomposition and identification of subsidence features offer valuable applications for the effective management of land subsidence and groundwater resources.

**Keywords** Subsidence · Empirical orthogonal function (EOF) · Empirical mode decomposition (EMD)

## Introduction

Human activities have intensified growing global groundwater depletion and land subsidence problems (Konikow and Kendy 2005; Wada et al. 2010; Siebert et al. 2010). Developing countries are more prone to land subsidence (Dinar et al. 2021). Groundwater depletion under cities in delta regions or valleys in many countries is leading to serious land subsidence (Erban et al. 2014; Herrera-García et al. 2021). Subsidence has preferentially occurred in alluvial basins or coastal plains where urban or agricultural areas (Herrera-García et al. 2021). Understanding regional subsidence patterns is helpful for the future management of groundwater resources. Seasonal and inter-annual subsidence exhibits both spatial and temporal variations in distribution and magnitude (Chen et al. 2015). Spatio-temporal subsidence rates are mainly affected by groundwater extractions under land use (Minderhoud et al. 2018). Land use type affects water demands to lead to the evolution of land subsidence. The distribution of land use leads to different water use structures (Zhou et al. 2020). The increased groundwater pumping resulted in water-level declines (Evan et al. 2020), and resulted in higher subsidence rates. Lowest subsidence rates are found for natural and undeveloped areas, whereas highest rates for areas with high anthropogenic influence, e.g., agricultural and densely urbanized areas (Minderhoud et al. 2018). Subsidence monitoring involves the characterization of the spatial and temporal distribution of land subsidence, e.g., trend and seasonality. Monitoring generally includes leveling surveys, borehole monitoring data (extensometers, compaction well), GPS, and InSAR. Compaction monitoring wells not only provide the total subsidence at a point location but also the depth-dependent compaction rates at various intervals within a single borehole by noting the depth of individual magnetic rings that are emplaced at various depths throughout the length of the well. Vertical deformations (or strains) are related to hydraulic head change (stress) through the skeletal storage coefficient that characterizes the skeletal compressibility of the aquifer system (Chen et al. 2016; Steeb and Renner 2019). Stress‐strain diagrams or curves can be used for estimating skeletal-specific storage (Burbey 2001). The skeletal-specific storage can also be used to estimate porosity and aquifer matrix compressibility. Thus, cause and effect of subsidence is heterogeneous in aquifers.

Subsidence management, on the other hand, is a regional issue. Since aquifer characteristics tend not to be homogeneous, the challenge for water managers is to interpolate these point values to regional settings in aquifers with variable drawdown distributions and heterogeneous aquifer-system characteristics (Galloway and Burbey 2011; Du et al. 2018; Lu et al. 2020). Due to the significant impacts of subsidence in many overexploited unconsolidated aquifer systems, a systematic analysis of the spatial and temporal variations of subsidence is urgently needed for strategic management of groundwater resources. Empirical Orthogonal Function (EOF) analysis can be used to examine large-scale patterns of spatial variability and how they change with time (Dawson 2016; Chu et al. 2020). EOF analysis involves decomposing a component set of subsidence data in both temporal and spatial dimensions. In this investigation, the EOF analysis involves extracting the major spatio-temporal variations of subsidence heterogeneity. Subsidence heterogeneity is affected from meteorological conditions, pumping patterns, and the hydrogeological characteristics of the porous media. In addition, the empirical mode decomposition (EMD) (Huang et al. 1998) can adaptively represent non-stationary signals as sums of zero-mean components, and decompose the complex signal into fluctuation components. The EMD can be applied to any type of time series signal decomposition (Stallone et al. 2020). Previous studies used the EMD model to show the extent of periodic deformation fluctuations in the Beijing plain with a temporal cycle of about 1 year (Liu et al. 2020). To reveal the characteristic trend and periodical deformation process of the study area in this investigation, the EMD model was used to decompose the time-series of total land subsidence. Therefore, the EMD algorithm here was used to validate the EOF approach based on in-situ time series in the EOF hotspot area.

This study aims to understand the major features of regional subsidence from compaction wells using the spatiotemporal decomposition, such as EOF in an alluvial fan. The EOF identifies the major components responsible for the variability in the land subsidence pattern, and the EMD decomposes the time series for validation purposes. Subsidence feature decomposition approaches proposed here provide a reliable representation of the subsidence seasonality and trends in spite of the temporal and spatial heterogeneities responsible for producing the variable land subsidence patterns. Furthermore, the stress–strain scatter plots are obtained from subsidence and groundwater-level changes in the observations, which help us to understand the cause and effect of subsidence.

## Study area and material

Serious land subsidence has been occurring for decades along the high-speed railway in central Taiwan (Fig. 1). The study area lies within the Choushui River alluvial fan, which encompasses an area of about 1800 km² in Changhua and Yunlin Counties (Fig. 1). Changhua county lies north of the Choushui River, while Yunlin County lies to the south of the Choushui river, which flows from the highlands in the east to the Taiwan Strait at the coast in the east. The bedrock in the upper (eastern) watershed of Choushui River is composed of slate, metamorphic quartzite, shale, sandstone, and mudstone, which has created the sediments of the Choushui River alluvial fan (Liu et al. 2002; Ali et al. 2020). Excessive exploitation of groundwater in both Changhua and Yunlin counties has resulted in excessive land subsidence and is creating a potential hazard for infrastructures including the Taiwan high-speed rail system that passes through the region from the northeast to the southern part of the study area (Ali et al. 2020). Model boundary is based on minimum and maximum of longitude and latitude of compaction wells.

Two hydrogeological profiles (A–A’ and B–B’) are shown in Fig. 1. The vertical strips observed in the hydrogeological profiles A–A’ and B–B’ represent the location and depth information of the boreholes. The unconsolidated fan deposits consist of four aquifers (F1–F4) that are composed of gravel and coarse sand deposits and separated by three finer grained (but locally discontinuous) confining units composed mainly of silts and clays. These aquifers are thickest in the east and become thinner toward the coast in the west, where the aquitards tend to dominate. The aquitards are most prevalent in the distal-fan and mid-fan areas and gradually diminish in thickness toward the east. The proximal-fan represents the major recharge area of the aquifer system (Yu and Chu 2010). Geologic materials are not uniformly distributed. Clay-containing sediments are more likely to compact with head reductions than sand and gravel formations; thus, land subsidence from groundwater pumping is more prone to occur in the western part of the study area. In this study, the major aquifer (F2) are used for hydraulic head analysis.

The study area in west central Taiwan (Fig. 1) shows the locations of the 31 compaction wells used for subsidence observation. The compaction wells are based on the magnetic ring technology (Hung et al. 2012) that yields depth-dependent deformation in the various hydrogeologic units extending through the entire depth of the well. The resolution of the deformation signal in the monitoring wells is about 1 mm (Hung et al. 2012). The measurements of compaction monitoring wells provide monthly subsidence information at the stations (Fig. 1). In this investigation, 48 months of compaction well data were used from January 2015 through December 2018. Moreover, the major monthly hydraulic head data in the same period were used for the stress–strain analysis at the monitoring wells in Hishhish, Tuku, and Yiwu (from north to south), respectively (Fig. 1). The three representative groundwater monitoring wells were selected close to the hydrogeological profile making the respective and explainable stress–strain relations at these regions.

> **Figure 1:** Study area with high-speed railway, rectangle model boundary, locations of compaction wells, groundwater monitoring stations (central coast: Hishhish; central inland: Tuku; southern coast: Yiwu), and geohydrological profiles of AA’ and BB’ with boreholes.

## Methodology

Figure 2 shows the subsidence feature component decomposition and validation processes of the study. First, the deformation data acquired from compaction wells in the study area can be interpolated to produce an areal spatiotemporal subsidence matrix. The top of the alluvial fan is out of interpolation boundary (Fig. 1). The area at the top of the alluvial fan does not suffer significant subsidence, because relative influence at the top of the alluvial fan is far less than that of the downside area of the alluvial fan. Based on the spatiotemporal deformation matrix, the major three subsidence components can then be detected by the EOF model. The EMD approach is used to decompose the deformation time series data to validate the EOF model based on the subsidence observations. In addition, the stress–strain relation between hydraulic head changes and aquifer compaction can also be identified for aquifer-system characterization.

> **Figure 2:** Subsidence feature component decomposition and validation, including (1) spatio-temporal deformation interpolation (1-km resolution) using inverse distance weighted (IDW); (2) subsidence empirical orthogonal function (Subsidence EOF) and subsidence decomposition; (3) subsidence empirical mode decomposition at observations with the EOF hotspots (subsidence EMD); and (4) stress–strain analysis.

### Spatio‑temporal interpolation using inverse distance weighted, IDW

The 1-km resolution subsidence interpolation during 48 months will be generated independently using the IDW. The general equation from the IDW is as follows in the following equation:

$$ S(l_j) = \frac{\sum_i S(l_i) d_{ij}^{-p}}{\sum_i d_{ij}^{-p}} $$

where $S(l_j)$ is the interpolated subsidence value of a grid location $j$, $S(l_i)$ is the observed subsidence at data point location $i$, and $d_{ij}$ are the distances between the grid node $j$ and observed data point $i$. The IDW estimates a weighted value of subsidence for unsampled locations using values from nearby locations (Jones et al. 2003). The weights are proportional to the proximity of the sampled points to the unsampled location and can be specified by the power coefficient, $p$. The larger the power coefficient, the greater the weight of nearby points as can be gleaned from the following equation that estimates the value at an unsampled location. In this study, the power coefficient is equal to two.

### Empirical orthogonal function, EOF

Using EOFs, the main subsidence features can be decomposed in terms of orthogonal basis functions that are determined from the data. The spatiotemporal subsidence patterns $S(l,t)$ can be separated with the EOFs and its expansion coefficients (ECs) for physical interpretation (Chu 2018):

$$ S(l,t) = \sum_{k=1}^{K} \text{EOF}_k(l) \text{EC}_k(t) $$

where $S(l,t)$ represents the subsidence at location $l$ and time $t$; $K (=3 \text{ in this study})$ is the number of signal components contained in the field using an optimal set of basis functions of space $[\text{EOF}_k(l)]$ and expansion functions of time $[\text{EC}_k(t)]$ for signal component $k$. EOFs are the eigenvectors of the covariance matrix and describe the spatial variability pattern. The associated temporal projections are the expansion coefficients (ECs), i.e., the temporal coefficients of the EOF patterns. The ECs can then be computed from the projection of regional land deformation matrix onto the EOFs. In this study, the rotated EOF analysis is applied to a series of regional land deformation data sets (Yu and Chu 2010). The covariance matrix can then be calculated from the regional land deformation data set, and the eigenvalue problem can be solved using the singular value decomposition method (Hannachi et al. 2007).

### Empirical mode decomposition, EMD

EMD represents a Hilbert spectral transform and is ideally suited for extracting essential components, which are characteristic of the underlying processes. The method is fully adaptive and generates the basis function for representing the data solely from their components (Zeiler et al. 2010). The basis function, called Intrinsic Mode Functions (IMF), represent a complete set of locally orthogonal basis functions whose amplitude and frequency may vary over time. EMD process can be expressed as (a) Identify the upper/lower envelope from the local minima and maxima. (b) Calculate the mean of these envelops and subtract it from the signal. $\text{imf}_1 = S(t) - m_1$ (c) Check if the stop criteria satisfy for IMF. If not repeat steps through a to b until satisfying the criteria (Karatoprak and Seker 2019; Barbosh et al. 2020). Assuming after $j$ iteration, the conditions are satisfied: $\text{imf}_{1j} = \text{imf}_{1j-1} - m_{1j}$; then the first IMF: $\text{IMF}_1 = \text{imf}_{1j}$.

The land deformation time series ($S(t)$) from EMDs can be portrayed as

$$ S(t) = \sum_{i=1}^{I} \text{IMF}_i(t) + r_I(t) $$

where $\text{IMF}_i(t)$ is the $i$th IMF, and $r_I(t)$ is the residual signal. $I$ is the number of IMF (two in this study). In this study, the two major IMFs, i.e., trend and seasonality and the randomness (residual) can be identified.

### Stress–strain analysis

In the aquifer system, the stress is represented by the monthly hydraulic head change and the strain is the observed or calculated monthly land deformation. A strong linear correlation exists between the stress and strain in the aquifer system with the slope representing the skeletal storage coefficient. The x-axis of the plot is the monthly head change, while the y-axis is the monthly deformation variation. Units of x-axis and of y-axis is m and cm in this study.

## Results

### Subsidence feature components

Figure 3 shows three major EOF components: (1) the continuous subsidence component, (Fig. 3d), (2) the periodic component (including recovery signal) (Fig. 3e) and (3) the intra-seasonal component (from aquacultural pumping) (Fig. 3f) of subsidence from three different locations (Fig. 3a–c). The EC (Fig. 3d–f) shows the temporal variations (amplitudes) of the EOF components. The first major EOF (EOF 1) component contains 97.5%, of the variation in the data, while the second and third components represent only 1.7% and 0.4% of the variation, respectively. The large percentage variation of the first component shows that virtually all of the study area exhibits continuous subsidence. Pumping is continuous but variable throughout the year and the subsequent subsidence, therefore, continues to occur throughout virtually all of the study area (Fig. 3d). Subsidence occurs in the study area because of excessive groundwater pumping during that occurred during the entire investigation period. The EOF components varied by spatial location. Land subsidence hotspots occur in the southern inland (yellow area in the map of Fig. 3a) area associated with the first EOF. Figure 3e shows the seasonal subsidence and rebound pattern (soil layers are rebound during groundwater recharge) in the southern distal-fan area and proximal fan area (yellow area in the map of Fig. 3b) associated with the second EOF component (EOF 2). Figure 3f reveals the intra-seasonal fluctuation in subsidence pattern from aquacultural pumping in the central coastal area (yellow area in the map of Fig. 3c) associated with the third EOF component (EOF 3). Figure 4 shows spatial patterns of total subsidence from three components during these years.

> **Figure 3:** EOF maps (yellow: high; blue: low), and 48-month EC time series (x-axis: month number from Jan, 2016) for the first (a, d), second (b, e) and third component (c, f) of the EOF analysis.

> **Figure 4:** Total subsidence component maps from EOF 1, 2 and 3 from January 2015 through December 2018.

### Stress–strain analysis from observations near three EOFs

The observed subsidence is highly related changes in groundwater level. Figure 5 shows the time series associated with both surface displacements and hydraulic head changes at the monitoring stations located in Tuku (a, d), Yiwu (b, e) and Hishhish (c, f) close to the first, second and third EOFs hotspots. The variances of both series are consistent with time. In general, the surface displacement exhibits a declining trend pattern, whereas the hydraulic heads exhibit more periodic variations (up and down). The results indicate that subsidence has three significant spatial-temporal components related to groundwater level variations. In Tuku (Fig. 5d) and Yiwu (Fig. 5e), groundwater level reflects seasonal variations associated with hydrological changes during wet and dry seasons. Intra-seasonal fluctuation in the groundwater levels occur in Hishhish due to aquacultural pumping (Fig. 5f). The results (Fig. 5) show consistent variations between the groundwater level, and subsidence. The high subsidence rates occur from January to May, especially in February and March. The low groundwater levels occur in February, March and April. However, the wet season occurs from June to September.

> **Figure 5:** Time series of monthly displacement (a, b, c) (unit: cm), and hydraulic head (d, e, f) (unit: m) at the hotspots of first, second and third EOFs in Tuku (a, d), Yiwu (b, e) and Hishhish (c, f).

Figure 6 shows the stress–strain scatter plots at Tuku (a), Yiwu (b) and Hishhish (c). The subsidence can be accurately determined from the head change in this system. The three scatter plots exhibit a strong linear poroelasticity relation suggesting that the changes in pore fluid pressure of the aquifer are directly related to land subsidence of the entire aquifer system. The regression line slope in Fig. 6 represents the aquifer skeletal storage coefficients at the three locations. The fact that the slopes vary at each location indicates that the aquifer is heterogeneous (different storage coefficients), but contains similar materials. The slope in Fig. 6b (0.0026) is less steep than those in Fig. 6a, c (0.0037 and 0.0032) suggesting a smaller storage coefficient. The sensitivity in the stress–stress relation is milder due to smaller slope (0.0026 in Yiwu) in the southern coastal area (Fig. 6b). This coastal area causes a smaller amount of elastic compaction due to pumping decreasing in Yiwu (over-consolidated). However, the hysteresis of the stress–strain curve is not as evident at Tuku (Fig. 6a) and Hishhish (Fig. 6c), suggesting that inelastic response (inelastic storage) occurs at these two sites. In the areas, the fine-grained sediments tend to compact inelastically as pumping continues and heads continue to decline. From the stress–strain analysis, the aquifer contains the similar linear stress–strain relations, and a regression model is established to explore the mechanism controlling the compaction processes. Considering spatiotemporal varying pumping (driving factor) in hydrogeological structures, the pattern and process of subsidence is highly heterogeneous around the study area.

> **Figure 6:** Scatter plots between displacement (unit: cm) and hydraulic head change (unit: m) in a Tuku, b Yiwu, and c Hishhish for stress–strain analysis (slope: 0.0037, 0.0026, and 0.0032 in Tuku, Yiwu and Hishhish).

### Validation using EMD near three EOFs

Figure 7 shows the EMD results of land subsidence in (a) Tuku, (b) Yiwu, and (c) Hishhish, respectively. Results indicate that land subsidence occurs continuously and seasonal signals for validation. The IMF 1 is identified for the subsidence trend. In Tuku and Hishhish, the half cycle of IMF 1 means the continuous subsidence. However, the one cycle of IMF 1 in Yiwu represents subsidence and rebound. However, the IMF 2 component shows that the cyclical or seasonal pattern of subsidence is related to land use activity (agriculture in Tuku and Yiwu; aquaculture in Hishhish). The seasonal frequency of land subsidence (IMF 2) is similar in Fig. 7a (annual change: about 4 cycles in 4 years), but the smaller intensity (amplitude) and intra-seasonal variation of IMF 2 in Fig. 7c (similar amplitude in IMF 2 and residual, within 2 cm per year) is shown. In this study, the decomposed EMD can be used to validate the EOF results. This EOF appoach can be used for subsidence hotspot area identification for water resource management purposes. The trends and seasonal frequencies of land subsidence signals are related to pumping frequency and intensity as well as hydrogeologic conditions of the aquifer system. In Tuku, for example, land subsidence continues to occur and also exhibits contains seasonal fluctuations in deformation due to pumping (continues deformation: 3.5 cm, and seasonal deformation: 2 cm per year). In Yiwu, a greater magnitude of seasonal deformation occurs but without significant long-term subsidence (between −2 and 2 cm per year). In regard to the entire study area, it appears evident that an increase in the rate of pumping causes a decrease or stabilization of water levels (Ali et al. 2020). In Hishhish, the aquacultural subsidence pattern occurs in the central coastal area, where aquaculture farmers pump water to control the temperature of their fish ponds, which can vary on an intra-seasonal basis. EMD results show that regional subsidence patterns are highly correlated with seasonal variations and human activities.

> **Figure 7:** Empirical mode decomposition (EMD) of displacement time series in a Tuku, b Yiwu and c Hishhish for validation.

## Discussion

### Subsidence feature components

The EOF was applied find the main subsidence features in regional area in mass spatio-temporal data. The major subsidence feature locations are identified from the EOF effectively, because regional subsidence features are heterogenous in the study area. Subsidence pattern is caused from natural process and human activities (Brown, and Nicholls 2015; Ziwen et al. 2019). The first three EOF represents mutually orthogonal space patterns with the first three pattern being responsible for the largest data variance in study area. The major feature components contain the long-term decline, seasonal, and intra-seasonal subsidence which are related to wet and dry cycles, human activities (agriculture and aquaculture) and hydrogeology in the study area (Chu et al. 2021a and b). The EOF helps us to understand the main cause and effect of spatiotemporal subsidence in the study area. The observed subsidence is highly related changes in groundwater level, e.g., seasonal variations associated with hydrological changes during wet and dry seasons. The EMD separates the subsidence time series with the multiple frequencies. EMD supports the viewpoint of EOF results for the long-term trend with various frequent variations, such as seasonal, and intra-seasonal subsidence, but both may have different details. Our result provides the efficient way that the periodic deformation signal components and long-term trends can be separated. The subsidence component identification, e.g., continuous subsidence, annual/seasonal deformation and higher- seasonal frequency deformation from EOF and EMD can be used to detect the source of the subsidence that relates to land use, human activities, and hydrological factors (Chu et al. 2020, 2021a, b). Subsidence signals depend on not only climate and geohydrology, but also pumping behaviors that are related to economic activities. For example, irrigated agricultural lands have the highest subsidence rates compared with land use types (Brown and Nicholls 2015).

Few researches discuss the intensity–duration–frequency relations in groundwater-driven subsidence. This study identifies the frequency and amplitude of subsidence signals in EOF hotspots. Furthermore, inappropriate sustainable water resources management, insufficient preventive strategies, and the lack of public participation resulted in serious land subsidence due to groundwater overexploitation (Golian et al. 2021).

### Subsidence source identification and mitigation

Aquifer-system deformation is elastic (recoverable) if the effective stress imposed on the skeleton is smaller than any previous effective stress. Otherwise, the subsdience is irrecoverable. In this study, the recoverable subsidence varies seasonally, whereas the irrecoverable subsidence shows a decreasing tendency with time. Time–frequency or wavelet analysis can be used for the detailed relation between groundwater change and subsidence (Miller and Shirzaei 2015). The future study is used to invert the elastic and inelastic subsidence based on the time series decompostion. Furthermore, displacements originate from many processes at large- and local-scales. The inelastic displacement process will be identified in the future.

Stress–strain plots usually represent point values as both the water levels and subsidence measurements are coincident. The spatio-temporal relations between groundwater level change and subsidence can be identified (Ali et al. 2021; Chu et al. 2021b). The model will contribute to a better understanding of the spatial distributions and temporal patterns of subsidence. Result matched that the high subsidence rates occur in February and March with the lowest rainfall and highest pumping rate. Pumping based on variations in seasonal demand increases the potential for subsidence during dry seasons (Galloway and Burbey 2011). To prevent this subsidence problem, the most effective way is to identify the subsidence sources. Reducing the impacts of land subsidence in the current study area is to decrease pumping during dry seasons from January to May. In this study, we have considered the compaction observation only at the depth of 300 m to assess cumulative subsidence. To identify the contribution ratio of subsidence each layer, we found the information which the overall deformation was observed at four aquifers, i.e., F1, F2, F3, and F4, and aquitards, i.e., T1, T2, T3 and T4. Based on the layer deformation provided in Table A1 (WRA 2021), it can be inferred that the highest deformation occurs under 300 m which contributes the most to the total compaction occurring in the area, which contributes by almost 40% of the total compaction observed across the nine representative locations (Fig. 1) located in the subsidence hotspot of Central Yunlin area. The second highest compaction occurs in the confined aquifer (F2) which accounts for about 23% of the total subsidence. This is closely aligned with the fact that this aquifer is mainly exploited for groundwater abstraction due to its large spatial extent and high storage capacity that has high presence of gravel and sandy material with high porosity. In addition, the average contributions from the aquitards remain minor and only account between 4 and 7%.

The rapid subsidence is occurring in Southeast, South and East Asian cities, where feature high water demand and population pressure. These global subsidence problems largely result from local human activities, especially groundwater withdrawal. Understanding the causes of their subsidence is required to mitigate and minimize subsidence consequences. Besides spatio-temporal decompostion, machine learning or artificial intelligence methods will be applied for the identification and classification of subsidence patterns, for the prediction of time-series and formulation of decision-making rules (Sahoo et al. 2017).

## Conclusions

Land subsidence is primarily affected by factors, such as seasonal variations, intensive pumping during periods of high demand, geohydrological conditions, and land use patterns. The heterogenous underlying signals of land deformation can be effectively identified through feature decomposition analysis, i.e., empirical orthogonal functions (EOFs). This approach allows for the identification of both the seasonal patterns and long-term trends associated with land subsidence in the study area.

The EOF determines the major various components from spatio-temporal subsidence patterns, and the empirical mode decomposition (EMD) decomposes the subsidence observations to validate from major components. Result shows that the approaches can identify seriously continuous subsidence for EOF 1 in the mid-fan areas, annual/seasonal deformation for EOF 2 in the distal-fan area, and higher- seasonal frequency aquacultural deformation for EOF 3 in the coastal area. A diverse spatio-temporal subsidence pattern is evident in the study area, with serious compaction observed in the southern inland region. The identification of subsidence hotspots is facilitated through the analysis of the first EOF. Moreover, the EMD is an effective way for detecting and quantifying subsidence trends and variances after the EOF analysis. The first IMF is identified for the subsidence trend, whereas the second IMF is identified for the seasonal variation of subsidence.

The proposed method can identify the trend and warning signals of subsidence with continuous pumping signals. This approach will be a substantial step toward an effective regional subsidence management and control. In addition, a comprehensive assessment on the contribution of aquitard over the total subsidence occurring in this area will be considered for future work once more comprehensive data set is acquired.

## Software availability

The models included in this paper are using Matlab. The code can be found at: https://mybox.ncku.edu.tw/navigate/s/2AE7BDB927C34FE082760E6CD0D79C82GSY. After estimated data are prepared, the main.m in EOF_model is the main function in the code for data loading, EOF, and visualization. Validation is shown from the folder IMF_validation. Model output from the system is implemented.

## Appendix

> **Table 1:** Subsidence contribution ratio (%) for each layer.

| Well ID in Fig. 1 | F1 | T1 | F2 | T2 | F3 | T3 | F4, T4, and under 300 m |
|-------------------|----|----|----|----|----|----|---------------------------|
| 1                 | 7  | 4  | 18 | 2  | 19 | 5  | 45                        |
| 2                 | 6  | 2  | 26 | 2  | 17 | 5  | 43                        |
| 3                 | 2  | 4  | 26 | 1  | 22 | 3  | 42                        |
| 4                 | 4  | 5  | 20 | 4  | 11 | 14 | 43                        |
| 5                 | 13 | 18 | 22 | 7  | 8  | 5  | 27                        |
| 6                 | 6  | 6  | 21 | 4  | 7  | 6  | 51                        |
| 7                 | 8  | 2  | 22 | 9  | 9  | 3  | 47                        |
| 8                 | 11 | 10 | 29 | 5  | 17 | 3  | 25                        |
| 9                 | 12 | 11 | 22 | 2  | 10 | 3  | 39                        |
| **Average percentage** | 8  | 7  | 23 | 4  | 13 | 5  | 40                        |

## Acknowledgements

The authors would like to thank Dr. C.W. Lin for providing suggestions for paper improvement. Furthermore, the study was supported by Water Resources Agency and National Science and Technology Council (NSTC), Taiwan (grant number 112-2121-M-006-007).

**Author contributions**  
Hone-Jay Chu: Conceptualization, Methodology, Writing- Original draft preparation. Tatas: Visualization, Investigation, Validation. Sumriti Ranjan Patra: Writing- Reviewing and Editing. Thomas J. Burbey: Writing- Reviewing and Editing.

**Data availability**  
The supplementary data to this article, i.e., 48-month estimated subsidence data and three time series for validation are provided at https://mybox.ncku.edu.tw/navigate/s/2AE7BDB927C34FE082760E6CD0D79C82GSY.

**Declarations**  
Conflict of interest: The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

## References

Ali MZ, Chu HJ, Burbey TJ (2021) Spatio-temporal estimation of monthly groundwater levels from GPS-based land deformation. Environ Model Softw 143:105123

Ali MZ, Chu HJ, Burbey TJ (2020) Mapping and predicting subsidence from spatio-temporal regression models of groundwater-drawdown and subsidence observations. Hydrogeol J 28(8):2865–2876

Barbosh M, Singh P, Sadhu A (2020) Empirical mode decomposition and its variants: a review with applications in structural health monitoring. Smart Mater Struct 29(9):093001

Brown S, Nicholls RJ (2015) Subsidence and human influences in mega deltas: the case of the Ganges–Brahmaputra–Meghna. Sci Total Environ 527:362–374

Burbey TJ (2001) Stress-strain analysis for aquifer-system characterization. Ground Water 39(1):128

Chen B, Gong H, Li X, Lei K, Ke Y, Duan G, Zhou C (2015) Spatial correlation between land subsidence and urbanization in Beijing. China Nat Hazards 75(3):2637–2652

Chen J, Knight R, Zebker HA, Schreüder WA (2016) Confined aquifer head measurements and storage properties in the San Luis Valley, Colorado, from spaceborne InSAR observations. Water Resour Res 52(5):3623–3636

Chu HJ (2018) Drought detection of regional nonparametric standardized groundwater index. Water Resour Manag 32(9):3119–3134

Chu HJ, Ali MZ, Burbey TJ (2021a) Development of spatially varying groundwater-drawdown functions for land subsidence estimation. J Hydrol Reg Stud 35:100808

Chu HJ, Ali MZ, Burbey TJ (2021b) Spatio-temporal data fusion for fine-resolution subsidence estimation. Environ Model Softw 137:104975

Chu HJ, Lin CW, Burbey TJ, Ali MZ (2020) Spatiotemporal analysis of extracted groundwater volumes estimated from electricity consumption. Ground Water 58(6):962–972

Dawson A (2016) eofs: a library for EOF analysis of meteorological, oceanographic, and climate data. J Open Res Softw 4(1):e14

Dinar A, Esteban E, Calvo E, Herrera G, Teatini P, Tomás R, Albiac J (2021) We lose ground: global assessment of land subsidence impact extent. Sci Total Environ 786:147415

Du Z, Ge L, Ng AHM, Zhu Q, Yang X, Li L (2018) Correlating the subsidence pattern and land use in Bandung, Indonesia with both Sentinel-1/2 and ALOS-2 satellite images. Int J Appl Earth Obs Geoinf 67:54–68

Erban LE, Gorelick SM, Zebker HA (2014) Groundwater extraction, land subsidence, and sea-level rise in the Mekong Delta. Vietnam Environ Res Lett 9(8):084010

Evans SW, Jones NL, Williams GP, Ames DP, Nelson EJ (2020) Groundwater level mapping tool: an open source web application for assessing groundwater sustainability. Environ Model Softw 131:104782

Galloway DL, Burbey TJ (2011) Regional land subsidence accompanying groundwater extraction. Hydrogeol J 19(8):1459–1486

Golian M, Saffarzadeh A, Katibeh H, Mahdad M, Saadat H, Khazaei M, Dashti Barmaki M (2021) Consequences of groundwater overexploitation on land subsidence in Fars Province of Iran and its mitigation management program. Water Environ J. https://doi.org/10.1111/wej.12688

Hannachi A, Jolliffe IT, Stephenson DB (2007) Empirical orthogonal functions and related techniques in atmospheric science: a review. Int J Climatol 27(9):1119–1152

Herrera-García G, Ezquerro P, Tomás R, Béjar-Pizarro M, López-Vinielles J, Rossi M, Ye S (2021) Mapping the global threat of land subsidence. Science 371(6524):34–36

Huang NE, Shen Z, Long SR, Wu MC, Shih HH, Zheng Q, Liu HH (1998) The empirical mode decomposition and the Hilbert spectrum for nonlinear and non-stationary time series analysis. Proc Roy Soc Lond Ser A Math Phys Eng Sci 454(1971):903–995

Hung WC, Hwang C, Liou JC, Lin YS, Yang HL (2012) Modeling aquifer-system compaction and predicting land subsidence in central Taiwan. Eng Geol 147:78–90

Jones NL, Davis RJ, Sabbah W (2003) A comparison of three-dimensional interpolation techniques for plume characterization. Groundwater 41(4):411–419

Karatoprak E, Seker S (2019) An improved empirical mode decomposition method using variable window median filter for early fault detection in electric motors. Math. Probl. Eng. 2019:8015295. https://doi.org/10.1155/2019/8015295

Konikow LF, Kendy E (2005) Groundwater depletion: a global problem. Hydrogeol J 13(1):317–320

Liu CW, Jang CS, Chen SC (2002) Three-dimensional spatial variability of hydraulic conductivity in the Choushui River alluvial fan. Taiwan Environ Geol 43(1–2):48–56

Liu L, Yu J, Chen B, Wang Y (2020) Urban subsidence monitoring by SBAS-InSAR technique with multi-platform SAR images: a case study of Beijing Plain. China. Eur. J. Remote. Sens. 53(1):141–153

Lu CY, Hu JC, Chan YC, Su YF, Chang CH (2020) The relationship between surface displacement and groundwater level change and its hydrogeological implications in an Alluvial Fan: case study of the Choshui River Taiwan. Remote Sens 12(20):3315

Miller MM, Shirzaei M (2015) Spatiotemporal characterization of land subsidence and uplift in Phoenix using InSAR time series and wavelet transforms. J Geophys Res Solid Earth 120(8):5822–5842

Minderhoud PSJ, Coumou L, Erban LE, Middelkoop H, Stouthamer E, Addink EA (2018) The relation between land use and subsidence in the Vietnamese Mekong delta. Sci Total Environ 634:715–726

Sahoo S, Russo TA, Elliott J, Foster I (2017) Machine learning algorithms for modeling groundwater level changes in agricultural regions of the US. Water Resour Res 53(5):3878–3895

Siebert S, Burke J, Faures JM, Frenken K, Hoogeveen J, Döll P, Portmann FT (2010) Groundwater use for irrigation – a global inventory. Hydrol Earth Syst Sci 14(10):1863–1880

Stallone A, Cicone A, Materassi M (2020) New insights and best practices for the successful use of empirical mode decomposition, iterative filtering and derived algorithms. Sci Rep 10(1):1–15

Steeb H, Renner J (2019) Mechanics of poro-elastic media: a review with emphasis on foundational state variables. Transp Porous Media 130(2):437–461

Wada Y, Van Beek LP, Van Kempen CM, Reckman JW, Vasak S, Bierkens MF (2010) Global depletion of groundwater resources. Geophys Res Lett. https://doi.org/10.1029/2010GL044571

WRA: Water Resources Agency in Taiwan, the trend identification of land subsidence using big-data analysis. 2021.

Yu HL, Chu HJ (2010) Understanding space–time patterns of groundwater system by empirical orthogonal functions: a case study in the Choshui River alluvial fan. Taiwan J Hydrol 381(3–4):239–247

Zeiler A, Faltermeier R, Keck IR, Tomé AM, Puntonet CG, Lang EW (2010) Empirical mode decomposition – an introduction. In: The 2010 Proc. Int. Jt. Conf. Neural Netw. (IJCNN). IEEE. p 1–8.

Zhou C, Gong H, Chen B, Gao M, Cao Q, Cao J, Shi M (2020) Land subsidence response to different land use types and water resource utilization in Beijing-Tianjin-Hebei. China. Remote Sens. 12(3):457

Ziwen Z, Liu Y, Li F, Li Q, Ye W (2019) Land subsidence monitoring based on InSAR and inversion of aquifer parameters. Eurasip J Wirel Commun Netw 2019(1):1–18

**Publisher's Note** Springer Nature remains neutral with regard to jurisdictional claims in published maps and institutional affiliations. Springer Nature or its licensor (e.g. a society or other partner) holds exclusive rights to this article under a publishing agreement with the author(s) or other rightsholder(s); author self-archiving of the accepted manuscript version of this article is solely governed by the terms of such publishing agreement and applicable law.