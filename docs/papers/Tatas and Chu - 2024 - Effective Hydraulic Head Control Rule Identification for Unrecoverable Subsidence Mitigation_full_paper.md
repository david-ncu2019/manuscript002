# Effective Hydraulic Head Control Rule Identification for Unrecoverable Subsidence Mitigation

**Authors:** Tatas, Hone-Jay Chu  
**Affiliations:** 1 National Cheng Kung University, No. 1, University Road, East District, Tainan 701, Taiwan; 2 Institut Teknologi Sepuluh Nopember, Surabaya, Indonesia  
**Corresponding author:** Hone-Jay Chu, honejaychu@geomatics.ncku.edu.tw  
**Received:** 13 June 2022 / **Accepted:** 7 March 2024  
**Published in:** Water Resources Management, [https://doi.org/10.1007/s11269-024-03816-w](https://doi.org/10.1007/s11269-024-03816-w)  
© The Author(s), under exclusive licence to Springer Nature B.V. 2024

## Abstract

Land subsidence involves either elastic (recoverable) or inelastic (unrecoverable) soil compaction within an aquifer. Elastic or inelastic subsidence is tradionally identified on the basis of the relation between deformation and hydraulic head changes. This study aims to determine the statistical hydraulic head rule for inelastic subsidence mitigation in groundwater management. By focusing on Yunlin County in Taiwan as the study area, this research effectively distinguishes between unrecoverable and recoverable subsidence using the head rule with the statistical threshold, which is calibrated by an optimal linear search. Result shows that considering the head rule can obtain similar patterns of subsidence with the traditional model from the stress–strain diagram. Inelastic subsidence accounts for approximately 15% of all instances, notably occurring during the early months of each year. Inelastic subsidence usually happened in the mid-fan and distal fan. This study can rapidly identify when and where unrecoverable subsidence happens. Groundwater management within the head threshold would be implemented for unrecoverable subsidence mitigation.

**Keywords:** Elastic and Inelastic Subsidence · Hydraulic head · Statistical rule · Stress–strain

## 1 Introduction

Land subsidence (LS) is a significant issue in the management of groundwater resources in major urban areas and is particularly severe in coastal plains and river deltaic regions across the world (Bagheri-Gavkosh et al. 2021). These sinking cities include Shanghai and Beijing in China (Du et al. 2021; Su et al. 2021; Tang et al. 2021; Wu et al. 2008), as well as coastal cities in Indonesia e.g. Jakarta (Yastika et al. 2019; Husnayaen et al. 2018; Bott et al. 2021; Ng et al. 2012), cities in Taiwan (Chu et al. 2021; Tung and Hu 2012; Chen et al. 2007), and other Asian cities such as Bangkok, Tokyo, and Ho Chi Minh City (Cao et al. 2021). Subsidence monitoring with surveying approaches was designed to clarify LS hydrogeological processes (Hung et al. 2010, 2021). More than half of the global LS is attributed to groundwater extraction, primarily driven by human activities such as irrigation and industrial processes (Bagheri-Gavkosh et al. 2021; Vijai and Khan 2021; Xue et al. 2005; Foster and Chilton 2003). Slowing down subsidence poses challenges, primarily due to its sustained demand, particularly from the agricultural sector. Moreover, LS may be a precursor to subsequent hazard such as flooding (Takagi et al. 2021; Fiaschi and Wdowinski 2020; Miller and Shirzaei 2019; Navarro-Hernández et al. 2023). The considerable impact of groundwater extraction to subsidence is quantified (Minderhoud et al. 2020). Subsequently, the managers directed their attention towards the reduction in groundwater extraction and efforts to mitigate economic losses.

Groundwater extraction causes aquifer hydraulic head loss and pore pressure drop. Hydraulic head loss or pore pressure drop cause an increase in effective stress, resulting in compaction, for example, elastic or inelastic compaction (recoverable or unrecoverable subsidence). Inelastic compaction may casue unrecoverable subsidence. If the effective stress is less than the pre-consolidation stress, then the compaction is elastic. The soil returns to its original state as stress is relieved. By contrast, inelastic compaction occurs if the effective stress is larger than the pre-consolidation stress (Wang et al. 2017). Previous researches have combined groundwater and subsidence data to define elastic or inelastic compactions by using a stress–strain relationship (Hung et al. 2021; Burbey 2016). When the stress exerted on the skeleton exceeds the preconsolidation stress, it causes a reorganization of the pore structure within the fine-grained sediment’s granular matrix. This restructuring leads to a decrease in pore volume, resulting in the inelastic compaction of the aquifer system. Estimating unrecoverable LS in a basin is required to conduct groundwater and subsidence modeling or data. However, unrecoverable or recoverable subsidence is strongly related to groundwater drawdown. Inelastic subsidence occurs when hydraulic head drops below the historical lowest one. LS can be categorized as either recoverable (elastic) or unrecoverable (inelastic) for the purposes of subsidence management. This study utilizes the hydraulic head rule to differentiate between unrecoverable and recoverable LS for effective management. Groundwater drawdown management is proposed in the study area to prevent inelastic compaction (unrecoverable subsidence). Considering that aquifer characteristics tend to be heterogeneous, the challenge for managers is to consider subsidence controls in an aquifer system. The efficacy of implementing strategies for subsidence management is considered through the utilization of the head rule. The study recommends an apparent model of hydraulic head rule against LS, and outlines a prospective groundwater management strategy aimed at preventing future occurrences of subsidence.

Although subsidence management is a regional issue, stress–strain diagrams usually represent plot values of both hydraulic heads and subsidence measurements. This study aims to only apply the statistical hydraulic head rule for inelastic LS prevention. This study focuses on the relationship between hydraulic head and soil compaction, and determines the inelastic and elastic LS based on an optimal head threshold. The threshold is defined as the combination of the average and standard derivation of historical hydraulic heads for the minimal difference between the observed and estimated subsidence. Finally, the mapping of the subsidence is applied using spatial interpolation. The hydraulic head rule is used to effectively manage regional subsidence where monitoring stations of subsidence are not available.

## 2 Data and Study area

Yunlin County in Taiwan is proposed as the study area for the statistical rule. In Yunlin County, subsidence is primarily induced by the excessive extraction of groundwater, with its intensity influenced by the hydrogeological conditions of aquifers and human activities. (Ali et al. 2020; Chu et al. 2021). The subsidence is attributed to the excessive extraction of groundwater from over 100,000 pumping wells distributed throughout this area (Hung et al. 2010; Wang et al. 2015). The study region is formed by the Choshui River as an alluvial fan in Taiwan’s central west (see the inset in Fig. 1a). Figure 1a depicts the study region in Yunlin County, with the Choshui River in the north and the Beigang River in the south. This research region is directly bordered in the west by the Taiwan Strait and in the east by mountainous terrain. In the central region, the Taiwan High Speed Rail passes through the area with the serious LS in Yunlin County (Chu et al. 2021).

Most LS and groundwater monitoring stations are at the distal and mid fan (see Fig. 1a). The LS datasets are observed from twenty monitoring stations. A total of twenty groundwater monitoring stations located closest to each LS monitoring station are chosen. The groundwater monitoring stations collected historical data on hydraulic heads, and the data were associated with the time series LS dataset. Figure 1b shows the location and name of the LS monitoring stations. While the four stations (Guangfu, Jinhu, Ketsuo, and Tuku) are designated for testing purposes, the others are used as training data. The training dataset spans 72 months, while the testing dataset spans 60 months.

The study area is separated into three sections on the basis of the alluvial fan such as the proximal, mid, and distal fans, which contain gravel, coarse sand, medium-fine sand, fine sand, and inter-bedded or lens-structured clay in the layered deposits (Hung et al. 2010). Profile B-B’ and C-C’ show three aquitards (T1, T2, and T3), whose hydrogeological profiles are divided into four aquifers. T denotes that an aquitard with a thickness of about 20 to 30 m serves as a barrier between two aquifers. The aquifer depth is about 300 m, and the aquifer deposits contain gravel, coarse sand, and fine sand (see Fig. 1c and d). Notations I, II, and III refer to the first, second, and third aquifers, respectively. The thickest aquifer in the study area is the second layer. The majority of groundwater withdrawal occurs in this confined aquifer with a thickness ranging from 90 to 125 m. Hydraulic head data were collected from groundwater monitoring stations at the second aquifer.

> **Figure 1:** Study area in Yunlin County, Taiwan. (a) subsidence and hydraulic head monitoring stations in distal-fan and mid-fan areas, (b) names of LS monitoring stations, (c) cross-section along C-C’ (d) cross-section along B-B’.

## 3 Method

The model effectively classifies and quantifies elastic and inelastic subsidence by using the statistical rule based on the hydraulic head threshold that is related to the mean and standard derivation of the historical data. The model minimizes the difference of subsidence identification between the proposed rule approach and the tradional stress–strain diagram.

### 3.1 Stress–strain Relation in a Traditional Approach

This study expresses the stress–strain relationship between hydraulic head and LS (the aquifer’s deformation is the strain, whereas the hydraulic head change is the stress in LS application) to differentiate between elastic and inelastic soil compaction. The hydraulic head and LS cycle depicts the stress–strain diagram. The curve may be utilized to compute the maximum amount of LS after groundwater extraction (Burbey 2016; Ali et al. 2021). Here, the elastic and inelastic compactions are separated by the slopes of the stress–strain curve. Inelastic compaction ($C_{in}$) contains a steeper slope than elastic compaction ($C_e$). The $C_{in}$ is permanent and is caused primarily by excessive groundwater extraction, which reduces the hydraulic head below the critical head threshold (Hung et al. 2021). The soil material is compacted from the various loading processes from elastic or inelastic compaction. Elastic compaction in the soil happens when groundwater decreases within a critical head threshold. By contrast, rising hydraulic head causes the unloading process. As a result, the soil material bounces back. In Eq. 1, elastic LS ($\Delta s_e$) belongs to $C_e$, which is relatively small and frequently correlated with rainfall cycles or seasonal variations (Hung et al. 2021; Ezquerro et al. 2014; Bell et al. 2008). During inelastic compaction, inelastic LS ($\Delta s_{in}$) occurs. However, hydraulic head decline is exacerbated by low (or the absence of) groundwater recharge, particularly during the dry season as the aquifer-system loading process. Groundwater returns to the initial level in the unloading process after the loading process.

$$
\Delta s = \begin{cases}
\Delta s_{in} \in C_{in} \\
\Delta s_e \in C_e
\end{cases}
\tag{1}
$$

where $\Delta s_{in}$ and $\Delta s_e$ represent the inelastic and elastic LS in each time step; $C_{in}$ and $C_e$ represent inelastic and elastic compaction.

### 3.2 Statistical Rule Model

The proposed rule distinguishes unrecoverable and recoverable subsidence according to a specific head threshold. Recoverable subsidence (elastic compaction) occurs when the hydraulic head ($h$) is below the head threshold, whereas unrecoverable subsidence (inelastic compaction) occurs above the head threshold. In Eq. 2, the LS change ($\Delta s$) each time step is divided into unrecoverable LS ($\Delta s_{in}$) and recoverable LS changes ($\Delta s_e$) according to the head rule.

$$
\Delta s = \begin{cases}
\Delta s_{in}, & \text{if } h \leq h^* \\
\Delta s_e, & \text{if } h > h^*
\end{cases}
\tag{2}
$$

where $h$ is the hydraulic head in the well; $h^*$ is the optimal head threshold for identifying elastic and inelastic LS. The threshold is determined by the calibration process according to the statistical rule. The optimal head threshold ($h^*$) is defined as the combination of the average and standard derivation of historical hydraulic heads for the minimal difference between the accumulated estimated and observed unrecoverable subsidence, ($s_{in}$ and $s'_{in}$) in Eq. 3.

$$
\min_{\alpha_i} (s_{in,i} - s'_{in,i}) \quad | \quad h_i^* = \text{AVE}_i - \alpha_i \text{SD}_i
\tag{3}
$$

where $\text{AVE}_i$ and $\text{SD}_i$ are the average and standard derivation, respectively, of historical hydraulic heads for each observation $i$. The $\alpha_i$ is the decision variable from the linear search for each observation $i$. When unrecoverable or recoverable subsidence is classified, classification accuracy is checked by a confusion matrix.

The total amount of unrecoverable and recoverable LS in each monitoring station during total time steps ($T$) respectively follows:

$$
s_{in,i} = \sum_{t=1}^{T} (\Delta s_{in,i})_t
\tag{4}
$$

$$
s_{e,i} = \sum_{t=1}^{T} (\Delta s_{e,i})_t
\tag{5}
$$

Overall vertical deformation from unrecoverable and recoverable LS is called the total subsidence, as follows:

$$
s_{total,i} = s_{in,i} + s_{e,i}
\tag{6}
$$

### 3.3 Spatial Estimation of Elastic and Inelastic Subsidence

Spatial maps depicting recoverable and unrecoverable LS are estimated through inverse distance weighted (IDW) interpolation. IDW assumes that closer data influence interpolation more than farther data do (He et al. 2008; Huang et al. 2011; Spokas et al. 2003). Estimating subsidence $s(x,y)$ at any coordinate $(x,y)$ based on observation $s(x_i,y_i)$ at coordinate $(x_i,y_i)$ is as follows:

$$
s(x,y) = \sum_{i=1}^{n} w_i(x,y) \times s(x_i,y_i)
\tag{7}
$$

where $s(x_i,y_i)$ is the observed variable, that is, unrecoverable, recoverable, or total subsidence at coordinate $(x_i,y_i)$. $n$ is the number of observations. $s(x,y)$ is the estimated subsidence at any coordinate $(x,y)$. $w_i(x,y)$ is the weight function that is written as follows:

$$
w_i(x,y) = \frac{d_i^{-p}(x,y)}{\sum_{i=1}^{n} d_i^{-p}(x,y)}
\tag{8}
$$

where $p$ is a positive number that is the power parameter (He et al. 2008). The distance between estimation $(x,y)$ and observation $(x_i,y_i)$ is expressed as follows:

$$
d_i(x,y) = \sqrt{(x - x_i)^2 + (y - y_i)^2}
\tag{9}
$$

After the IDW estimation, the spatial map of elastic and inelastic subsidence consists of grids comprising 68 columns and 52 rows, each grid measuring 1 km² in size.

### 3.4 Validation

For accuracy assessment, this step validates the recoverable and unrecoverable subsidence classifier. Confusion matrices are a well-known tool for calculating accuracy (Düntsch and Gediga 2020), as they aid in determining a model’s performance on a dataset for which the actual values are known. The estimated and actual classifications are cross-tabulated as a matrix for analyzing accuracy, which is defined as:

$$
\text{accuracy} = \frac{(TP + TN)}{(TP + TN + FP + FN)}
\tag{10}
$$

where $TP$ represents true positives; $TN$ represents true negatives; $FP$ represents false positives; and $FN$ represents false negatives. The Pearson correlation coefficient ($r$) is also used for check. The correlation coefficient describes the correlation relationship between subsidence $s$ and $s'$ from the rule and traditional model.

$$
r = \frac{\sum_{i=1}^{n} \left( (s_i - \bar{s}) (s'_i - \bar{s'}) \right) }{ \sum_{i=1}^{n} (s_i - \bar{s}) + \sum_{i=1}^{n} (s'_i - \bar{s'}) }
\tag{11}
$$

where $s_i$ and $s'_i$ represent the subsidence from the rule and traditional models in observation $i$, respectively. $\bar{s}$ and $\bar{s'}$ represent the mean value of the datasets from the rule and traditional models.

## 4 Results and Discussion

### 4.1 Stress–strain Diagram as a Reference Model

Figure 2 shows the stress–strain curve in Yiwu and Neiliao over six years, from January 2015 to December 2020, in the distal and mid fan areas, respectively. The subsidence (strain) in Neiliao (see Fig. 2b) is more severe than that in Yiwu (see Fig. 2a). The curve patterns, for example, slope and loop, can be used to recognize elastic and inelastic compaction. The curve shows that the slope of elastic compaction is similar. Steep slopes are most common from January to March, with gentle slopes occurring in April to May. The stress decreases from June to October, leading to a redistribution of strain towards the initial condition. However, the stress does not exhibit an increase in December. The processes are repetitive cycles every year. The curve patterns can be used to separate inelastic compaction, which results in soil compaction being less able to recover. Moreover, groundwater level decline exceeds a value, resulting in inelastic compaction. Here, the head threshold value is about −30 m in Yiwu and −11 m in Neiliao (see Fig. 2a and b).

> **Figure 2:** Stress–strain curve between 2015 and 2020 for elastic and inelastic compaction processes, for example, in (a) Yiwu in the distal fan, and (b) Neiliao in the mid-fan.

### 4.2 Head Time Series for Subsidence Identification

Figure 3 shows the hydraulic head time series in two stations at the distal and mid fan, that is, Yiwu (Fig. 3a) and Neiliao (Fig. 3b). A comparison of the cases shows that the hydraulic head varies with season. The head variation at Yiwu is higher than that of Neiliao. Optimal head thresholds are determined in the rule model (red lines in Fig. 3). The optimal hydraulic head threshold at Yiwu (distal fan area) is lower than that at Neiliao in the mid-fan area because the distal area had been over-compacted before. For LS classification, the map of optimal head threshold is estimated using the IDW in Fig. 4. The head threshold in the distal fan is lower than that in the mid-northern fan (northwest-southeast from high to low) on the basis of the hydrogeology of alluvial fan. Figure 4 can be presented as a spatial map to help understand the spatial preconsolidation head in the area. The red area indicates lower head to trigger unrecoverable LS, whereas the yellow or green area requires higher head to trigger unrecoverable LS.

Understanding groundwater changes and how they change in response to pumping is important. The zero average groundwater-level change is the state for groundwater sustainability (Elshall et al. 2020). Groundwater sustainability is defined as the long-term inter-annual fluctuation in the groundwater levels that remains below a specified minimum threshold. In this study, the hydraulic head is regulated to mitigate severe subsidence risks. This groundwater-level monitoring and control serve as valuable tools to improve the sustainability of groundwater resources through effective management practices (Tsai et al. 2016). Furthermore, the sensitivity and uncertainty of the head rule such as the effect of observation data size will be further considered in the future.

> **Figure 3:** Head variations associated with the separation of unrecoverable and recoverable LS. (a) Yiwu in distal-fan and (b) Neiliao in southern mid-fan.

### 4.3 Spatial LS Maps from Models

Figure 5 shows the spatial maps during 2015–2020 of (a) unrecoverable, (b) recoverable, and (c) total subsidence by using the rule and traditional models. The maps show that the rule model can produce a similar subsidence pattern to that of the traditional model. The result shows high correlation of the maps from the statistical rule and the traditional model. The correlations are robust, and higher than 0.9 from observed points and estimation maps (see Table 1). The statistical rule and the traditional model have almost similar minimums, maximums, and standard derivations of subsidence. Elastic subsidence, $s_e$ is larger than inelastic subsidence, $s_{in}$, indicating that recoverable LS change is dominant in the study area.

The hydraulic head rule accounts for approximately 15% of inelastic subsidence of all subsidence events, especially in early months of each year. For the rule and traditional models, the percentage of inelastic subsidence in total is very close. The most significant inelastic subsidence occurs within the mid-southern region of the mid-fan area, represented by yellow spots with values of around 13.4 and 13.9 cm in the rule-based and traditional models for these years (see Fig. 5a). For subsidence management, an expanse of approximately 63 km² exhibits unrecoverable subsidence exceeding 11 cm over these years. The southern area in Fig. 5c contains high total subsidence during the six years. The maximum value in these years is about 43 cm in the southern area, but the minimum one is 9 cm in the northern area. Figure 6 shows the annual subsidence maps of recoverable and unrecoverable subsidence. Most LS in Yunlin is recoverable rather than unrecoverable. The mid-fan area experiences a more severe annual unrecoverable subsidence of around 2.5 cm, while the total annual subsidence amounts to approximately 6.5 cm. The region experiencing significant compaction consists primarily of fine-grained soils, which are prone to compression. Persistent LS is largely related to lowering hydraulic head, and deformations are strongly correlated to the hydraulic head fluctuations with seasonal changes and a long-term decreasing trend (Chen et al. 2021).

> **Figure 5:** Spatial accumulation maps between 2015–2020 for (a) unrecoverable LS, (b) recoverable LS, and (c) total LS under the (i) hydraulic head rule and (ii) the traditional model.

> **Figure 6:** Annual subsidence maps for (a) unrecoverable and (b) recoverable LS under hydraulic head rule.

**Table 1** Statistical parameters of estimated subsidence maps and correlation between two models for 2015–2020

| Model | Subsidence (cm) - Mean | Subsidence (cm) - Max | Subsidence (cm) - Min | Subsidence (cm) - SD | Correlation by maps | Correlation by points |
|-------|------------------------|----------------------|----------------------|---------------------|--------------------|----------------------|
| Rule model | $s_{in}$: 7.3, $s_e$: 18.2 | $s_{in}$: 13.4, $s_e$: 29.5 | $s_{in}$: 2.2, $s_e$: 6.5 | $s_{in}$: 1.9, $s_e$: 4.5 | $s_{in}$: 0.98, $s_e$: 0.99 | $s_{in}$: 0.97, $s_e$: 0.99 |
| Traditional model | $s_{in}$: 7.2, $s_e$: 18.2 | $s_{in}$: 13.9, $s_e$: 30.8 | $s_{in}$: 2.3, $s_e$: 6.4 | $s_{in}$: 1.8, $s_e$: 4.5 | – | – |

*Note: SD = standard derivation.*

### 4.4 Validation for Subsidence Classification

Figure 7a and b depict the classification accuracy for the training and testing datasets. The average classification accuracy of unrecoverable and recoverable subsidence is high, that is, 0.92 and 0.95 for training and testing data, respectively. The result for all stations shows good performance above 0.9. Figure 8 compares the unrecoverable and recoverable subsidence in the $\Delta s - \Delta h$ diagram in Yiwu (Fig. 8a, b) and Neiliao (Fig. 8c, d) for the statistical rule and the traditional model. The scattered red points indicate unrecoverable LS, whereas the blue points indicate recoverable LS. The statistical groundwater rule model shows a slight difference from that of the traditional model. The graphs demonstrate a strong linear poroelasticity correlation, indicating that alterations in pore fluid pressure within the aquifer directly correspond to the subsidence of the entire aquifer system. Generally, unrecoverable subsidence occurs during the spring season. To mitigate this, it is advisable to regulate groundwater extraction in the initial months of each year to prevent unrecoverable subsidence (Chu et al. 2021).

> **Figure 7:** LS classification accuracy of (a) the training dataset: 16 LS stations from 2015–2020, and (b) the testing dataset: 4 LS stations from 2015–2020 using the rule model.

> **Figure 8:** Scatter diagram of unrecoverable (red dots) and recoverable (blue dots) LS with the $\Delta s-\Delta h$ relation at (a) Yiwu for the rule model, (b) Yiwu for the traditional model, (c) Neiliao for the rule model, and (d) Neiliao for the traditional model.

## 5 Conclusion

This study aims to determine the statistical rule of hydraulic head for inelastic LS mitigation in groundwater management. The statistical rule can be effectively used to identify elastic and inelastic subsidence. Subsidence classifications consider the hydraulic head rule, which is highly correlated to the results of the stress–strain relationship.

Using the hydraulic head rule can clearly identify elastic and inelastic LS without the need for LS information. This hydraulic head rule can help identify when inelastic subsidence events occur. Specifically, unrecoverable subsidence, which occurs in the early months of each year, constitutes roughly 15% of all occurrences. The frequency of unrecoverable subsidence is less than that of recoverable subsidence in Yunlin County. However, the subsidence is severe when unrecoverable subsidence happens. Hence, groundwater drawdown should be controlled as a preventive approach to mitigate unrecoverable LS. The spatial map of head threshold (northwest-southeast from high to low) is provided for groundwater management to prevent unrecoverable LS. This rule model will be utilized to manage land subsidence in other regions lacking monitoring data of land subsidence.

## Acknowledgements

We are very grateful for the financial assistance from our Ministry of Science and Technology (109-2621-M-006 -003 -), and data provider from Water Resources Agency, Taiwan.

## Author contribution

Conceptualization, H.J. Chu; methodology, Tatas; validation, Tatas; formal analysis, Tatas; writing—original draft preparation, Tatas; writing—review and editing, H.J Chu; supervision, H.J. Chu.

## Funding

This work was supported by Ministry of Science and Technology (Grant numbers: 109-2621-M-006 -003 -).

## Data Availability

The datasets generated during and/or analysed during the current study are available from the corresponding author on reasonable request.

## Declarations

**Ethical Approval** Disclosure of potential conflicts of interest. The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

**Consent to Participate** Not applicable.

**Consent to Publish** Not applicable.

**Competing Interests** The authors have no relevant financial or non-financial interests to disclose.

## References

Ali MZ, Chu HJ, Burbey TJ (2020) Mapping and predicting subsidence from spatio-temporal regression models of groundwater-drawdown and subsidence observations. Hydrogeol J 28(8)

Ali MZ, Chu HJ, Burbey TJ (2021) Spatio-temporal estimation of monthly groundwater levels from GPS-based land deformation. Environment Model Software 143:105123

Bagheri-Gavkosh M, Hosseini SM, Ataie-Ashtiani B, Sohani Y, Ebrahimian H, Morovat F, Ashrafi S (2021) Land subsidence: a global challenge. Sci Total Environ 778. https://doi.org/10.1016/j.scitotenv.2021.146193

Bell JW, Amelung F, Ferretti A, Bianchi M, Novali F (2008) Permanent scatterer InSAR reveals seasonal and long-term aquifer-system response to groundwater pumping and artificial recharge. Water Resour Res 44:1–18. https://doi.org/10.1029/2007WR006152

Bott LM, Schöne T, Illigner J, Haghshenas Haghighi M, Gisevius K, Braun B (2021) Land subsidence in Jakarta and Semarang Bay – the relationship between physical processes, risk perception, and household adaptation. Ocean Coast Manag 211. https://doi.org/10.1016/j.ocecoaman.2021.105775

Burbey TJ (2016) Stress–strain analyses for aquifer-system characterization

Cao A, Esteban M, Valenzuela VPB, Onuki M, Takagi H, Thao ND, Tsuchiya N (2021) Future of Asian deltaic megacities under sea level rise and land subsidence: current adaptation pathways for Tokyo, Jakarta, Manila, and Ho Chi Minh City. Curr Opin Environ Sustain 50:87–97

Chen CT, Hu JC, Lu CY, Lee JC, Chan YC (2007) Thirty-year land elevation change from subsidence to uplift following the termination of groundwater pumping and its geological implications in the Metropolitan Taipei Basin, Northern Taiwan. Eng Geol 95:30–47. https://doi.org/10.1016/j.enggeo.2007.09.001

Chen YA, Chang CP, Hung WC, Yen JY, Lu CH, Hwang C (2021) Space-Time evolutions of Land Subsidence in the Choushui River Alluvial Fan (Taiwan) from multiple-sensor observations. Remote Sens 13(12):2281

Chu HJ, Ali MZ, Tatas, Burbey TJ (2021) Development of spatially varying groundwater-drawdown functions for land subsidence estimation. J Hydrol Reg Stud 35:100808. https://doi.org/10.1016/j.ejrh.2021.100808

Du Z, Ge L, Ng AHM, Lian X, Zhu Q, Horgan FG, Zhang Q (2021) Analysis of the impact of the South-to-North water diversion project on water balance and land subsidence in Beijing, China between 2007 and 2020. J Hydrol 603:126990

Düntsch I, Gediga G (2020) Indices for rough set approximation and the application to confusion matrices. Int J Approx Reason 118:155–172. https://doi.org/10.1016/j.ijar.2019.12.008

Elshall AS, Arik AD, El-Kadi AI, Pierce S, Ye M, Burnett KM, Chun G (2020) Groundwater sustainability: a review of the interactions between science and policy. Environ Res Lett 15(9):093004

Ezquerro P, Herrera G, Marchamalo M, Tomás R, Béjar-Pizarro M, Martínez R (2014) A quasi-elastic aquifer deformational behavior: Madrid aquifer case study. J Hydrol 519:1192–1204

Fiaschi S, Wdowinski S (2020) Local land subsidence in Miami Beach (FL) and Norfolk (VA) and its contribution to flooding hazard in coastal communities along the U.S. Atlantic Coast. Ocean Coast Manag 187:105078. https://doi.org/10.1016/j.ocecoaman.2019.105078

Foster SSD, Chilton PJ (2003) Groundwater: the processes and global significance of aquifer degradation. Philos Trans R Soc B Biol Sci 358:1957–1972. https://doi.org/10.1098/rstb.2003.1380

He Q, Zhang Z, Yi C (2008) Spectrochim Acta - Part Mol Biomol Spectrosc 71:743–745. https://doi.org/10.1016/j.saa.2007.11.041. 3D fluorescence spectral data interpolation by using IDW

Huang F, Liu D, Tan X, Wang J, Chen Y, He B (2011) Explorations of the implementation of a parallel IDW interpolation algorithm in a Linux cluster-based parallel GIS. Comput Geosci 37:426–434. https://doi.org/10.1016/j.cageo.2010.05.024

Hung WC, Hwang C, Chang CP, Yen JY, Liu CH, Yang WH (2010) Monitoring severe aquifer-system compaction and land subsidence in Taiwan using multiple sensors: Yunlin, the southern Choushui river alluvial fan. Environ Earth Sci 59:1535–1548. https://doi.org/10.1007/s12665-009-0139-9

Hung WC, Hwang C, Sneed M, Chen YA, Chu CH, Lin SH (2021) Measuring and interpreting Multilayer Aquifer-System compactions for a Sustainable Groundwater-System Development. Water Resour Res 57. https://doi.org/10.1029/2020WR028194

Husnayaen, Rimba AB, Osawa T, Parwata INS, As-syakur AR, Kasim F, Astarini IA (2018) Physical assessment of coastal vulnerability under enhanced land subsidence in Semarang, Indonesia, using multi-sensor satellite data. Adv Sp Res 61:2159–2179. https://doi.org/10.1016/j.asr.2018.01.026

Miller MM, Shirzaei M (2019) Land subsidence in Houston correlated with flooding from Hurricane Harvey. Remote Sens Environ 225:368–378. https://doi.org/10.1016/j.rse.2019.03.022

Minderhoud PSJ, Middelkoop H, Erkens G, Stouthamer E (2020) Groundwater extraction may drown mega-delta: projections of extraction-induced subsidence and elevation of the Mekong delta for the 21st century. Environ Res Commun 2(1):011005

Navarro-Hernández MI, Valdes-Abellan J, Tomás R, Tessitore S, Ezquerro P, Herrera G (2023) Analysing the impact of land subsidence on the flooding risk: evaluation through InSAR and modelling. Water Resour Manage 37(11):4363–4383

Ng AHM, Ge L, Li X, Abidin HZ, Andreas H, Zhang K (2012) Mapping land subsidence in Jakarta, Indonesia using persistent scatterer interferometry (PSI) technique with ALOS PALSAR. Int J Appl Earth Obs Geoinf 18:232–242. https://doi.org/10.1016/j.jag.2012.01.018

Spokas K, Graff C, Morcet M, Aran C (2003) Implications of the spatial variability of landfill emission rates on geospatial analyses. Waste Manag 23:599–607. https://doi.org/10.1016/S0956-053X(03)00102-8

Su G, Wu Y, Zhan W, Zheng Z, Chang L, Wang J (2021) Spatiotemporal evolution characteristics of land subsidence caused by groundwater depletion in the North China plain during the past six decades. J Hydrol 600:126678

Takagi H, Esteban M, Mikami T, Pratama MB, Valenzuela VPB, Avelino JE (2021) People’s perception of land subsidence, floods, and their connection: a note based on recent surveys in a sinking coastal community in Jakarta. Ocean Coast Manag 211:105753. https://doi.org/10.1016/j.ocecoaman.2021.105753

Tang W, Zhao X, Motagh M, Bi G, Li J, Chen M, Chen H, Liao M (2021) Land subsidence and rebound in the Taiyuan basin, northern China, in the context of inter-basin water transfer and groundwater management. Remote Sens Environ 112792. https://doi.org/10.1016/j.rse.2021.112792

Tsai WP, Chiang YM, Huang JL, Chang FJ (2016) Exploring the mechanism of surface and ground water through data-driven techniques with sensitivity analysis for water resources management. Water Resour Manage 30:4789–4806

Tung H, Hu JC (2012) Assessments of serious anthropogenic land subsidence in Yunlin County of central Taiwan from 1996 to 1999 by Persistent Scatterers InSAR. Tectonophysics 578:126–135. https://doi.org/10.1016/j.tecto.2012.08.009

Vijai K, Khan SMMN (2021) Analysis of groundwater quality for irrigation purpose in Pennagaram block of Dharmapuri District, Tamilnadu, India. Mater Today Proc. https://doi.org/10.1016/j.matpr.2021.07.330

Wang SJ, Lee CH, Hsu KC (2015) A technique for quantifying groundwater pumping and land subsidence using a nonlinear stochastic poroelastic model. Environ Earth Sci 73:8111–8124. https://doi.org/10.1007/s12665-014-3970-6

Wang G, ya, Zhu J, qi, You G, Yu J, Gong Xlong, Li W, Gou F (2017) gang, Land rebound after banning deep groundwater extraction in Changzhou, China. Eng Geol 229, 13–20. https://doi.org/10.1016/j.enggeo.2017.09.006

Wu J, Shi X, Xue Y, Zhang Y, Wei Z, Yu J (2008) The development and control of the land subsidence in the Yangtze Delta, China. Environ Geol 55:1725–1735

Xue YQ, Zhang Y, Ye SJ, Wu JC, Li QF (2005) Land subsidence in China. Environ Geol 48:713–720

Yastika PE, Shimizu N, Abidin HZ (2019) Monitoring of long-term land subsidence from 2003 to 2017 in coastal area of Semarang, Indonesia by SBAS DInSAR analyses using Envisat-ASAR, ALOS-PALSAR, and Sentinel-1A SAR data. Adv Sp Res 63:1719–1736

**Publisher’s Note** Springer Nature remains neutral with regard to jurisdictional claims in published maps and institutional affiliations.  

Springer Nature or its licensor (e.g. a society or other partner) holds exclusive rights to this article under a publishing agreement with the author(s) or other rightsholder(s); author self-archiving of the accepted manuscript version of this article is solely governed by the terms of such publishing agreement and applicable law.