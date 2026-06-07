# Modeling aquifer-system compaction and predicting land subsidence in central Taiwan

Wei-Chia Hung^a, Cheinway Hwang^b,*, Jyh-Chau Liou^a, Yan-Syun Lin^a, Hsiu-Lung Yang^a

^a Green Energy and Environment Research Laboratories, Industrial Technology Research Institute, Bldg. 24, 195 Sec. 4, Chung Hsing Rd., Chutung, Hsin chu 310, Taiwan

^b Department of Civil Engineering, National Chiao Tung University, 1001 Ta Hsueh Rd., Hsinchu 300, Taiwan

* Corresponding author at: Department of Civil Engineering, National Chiao Tung University, 1001 Ta Hsueh Road, Hsinchu 300, Taiwan.
   E-mail address: cheinway@mail.nctu.edu.tw (C. Hwang).

> **Abstract**
>
> Changhua is a county in central Taiwan that will house several major economic development projects. Extracting groundwater has caused large-scale land subsidence in Changhua, with the largest cumulative subsidence being 210 cm over 1992 –2010. A multi-sensor monitoring system consisting of continuous GPS stations, a leveling network, multi-layer compaction monitoring wells and groundwater wells is deployed to monitor land subsidence and its mechanism in Changhua. Data from the monitoring well CGSG in Dacheng Township of Changhua show a cumulative compaction of 110.6 cm over 1997 –2010, occurring mainly at two aquifers and one aquitard. A novel combination of GPS and monitoring well data was used to determine the stress –strain relations. The stratum compaction turns from plasticity to elastoplasticity after a long-term compaction at the second aquifer below the surface. Four hydrogeological parameters of the three sediment layers in Dacheng, vertical hydraulic conductivity, elastic skeletal specific storage, inelastic skeletal specific storage, and the initial maximum preconsolidation stress, in the one‐dimensional compaction model COMPAC, are estimated using the genetic algorithm. With the parameters, COMPAC predicts compactions to an accuracy consistent with in situ measurements, and the mean absolute percentage errors of prediction are below 10%. The result provides a key reference for water management in central Taiwan.

---

## 1. Introduction

In many parts of the world, large consumptions of water due to population and industry growths demand the use of groundwater to supplement surface water. Existing studies suggest that over-withdrawing of groundwater will cause land subsidence. Examples of groundwater-induced subsidence are in Mexico (Carreón-Freyre and Cerca, 2006; Lopez-Quiroz et al., 2009), United States (Galloway and Hoffmann, 2007; Burbey, 2008), Japan (Munekane et al., 2008), Italy (Ferronato et al., 2004; Teatini et al., 2005), mainland China (Hu et al., 2009; Wu et al., 2010), and Taiwan (Hu et al., 2006; Hung et al., 2010). In general, land subsidence occurs over regions with sediment stratums formed by rivers, lakes, sloughs and structural basins, where groundwater decline can easily cause stratum compaction.

Taiwan is an island surrounded by oceans, with an average annual rainfall over 2,000 mm. However, the rainfalls are distributed unevenly throughout the year. Due to a large topographic relief, limited spaces and natural hazards, storing surface water in Taiwan is difficult. Most man-made reservoirs in Taiwan are prone to sediment by typhoons, making water storage even more challenging. Therefore, in many parts of Taiwan, groundwater becomes the major source of water, especially during dry seasons. Because groundwater is not effectively replenished during wet seasons, the long-term groundwater of Taiwan level has been declining. Also, recent climate anomalies (extreme dry and wet weathers) make it more difficult to allocate available water resources (Hsu et al., 2007).

Changhua County (Figure 1) is located north of the Choushui River Alluvial Fan in central Taiwan, and is an area with abundant groundwater. During the 1970s, the agriculture and aquaculture in this area grew dramatically. Due to lack of sufficient surface water, massive amount of groundwater has been withdrawn, resulting in severe land subsidence, especially in coastal areas. Hundreds of square kilometers in Changhua County have been affected by land subsidence, which also caused failures and deformations of man-made structures such as houses and rail (Hung and Liou, 2009). Changhua will house many major economic development projects, with funds drawn from Taiwan and international investors. For example, Dacheng Township of Changhua County was the proposed site of the Kuokuang Petrochemical Development Project, which was initiated in 2005 with a total investment of about USD 30 billions. Despite the importance of this project on the long-term economic development of Taiwan, this project is suspended because of concerns about land subsidence, large water consumption and damage to sustainable development. Local people of Dacheng fear that this petrochemical project will deteriorate the already serious land subsidence problem here due to extensive water consumptions of the proposed petrochemical plants.

Land subsidence is a consequence of stratum compaction, which may vary in extent over different seasons and can be affected by changes in climate and groundwater level (Amelung et al., 1999; Hoffmann et al., 2001; Buckley et al., 2003; Schmidt and Burgmann, 2003). It has been demonstrated that the effect of groundwater level change on land subsidence can be modeled based on a stress –strain relationship considering the elastic or inelastic skeletal specific storage of the underlying stratum (Hanson, 1989; Sneed and Galloway, 2000; Burbey, 2001; Pavelko, 2004; Liu and Helm, 2008a,b). For example, Larson et al. (2001) used the MODFLOW model of groundwater flow (McDonald and Harbaugh, 1988) and the IBS model of land subsidence (Leake and Prudic, 1991) to determine the stratum compaction coefficients and to estimate the groundwater safe yield in Los Banos-Kettleman City, California. Hoffmann et al. (2003b) used MODFLOW-2000, SUB (Hoffmann et al., 2003a) and UCODE to model groundwater flow and land subsidence, and estimate the compaction coefficients in Antelope Valley, California. With the stratum compaction coefficients estimated, it is possible to forecast land subsidence and develop an optimal groundwater management strategy.

Due to the great societal, economic and political impacts of land subsidence in Changhua County, in this paper we conduct an extensive study to collect in situ monitoring data and then to model land subsidence in Changhua using a method that is proved to be efficient in the literature. Specifically, we first collect data from continuous GPS, precision leveling, multi-layer compaction monitoring wells and groundwater wells, and then use a one-dimensional compaction model to estimate four important hydrogeological parameters. Such hydrogeological parameters will refine the previous estimates of soil properties such as time constant of consolidation, and will be also used to predict land subsidence. The result from this paper will serve as an important reference for the water resource management in central Taiwan.

## 2. Land subsidence from geodetic and geotechnical measurements

To effectively monitor the land subsidence in Changhua, since 1992 we have deployed a leveling network and installed continuous GPS stations, multi-layer compaction monitoring wells and groundwater monitoring wells here. The total length of the leveling routes is about 400 km. There are 2 continuous GPS stations, 7 compaction monitoring and 40 groundwater monitoring wells (Hung and Liou, 2009) in Changhua. Fig. 2 shows the distribution of the leveling benchmarks and monitoring sensors. Sample pictures of the benchmarks and sensors are illustrated in Fig. 3. Fig. 4 shows the cumulative subsidence over 1992 –2009. The maximum subsidence occurs in Dacheng Township and is about 210 cm.

> *Figure 1.* Geographical location of Changhua County. The boundaries of the townships in the county are also given.

> *Figure 2.* Distributions of leveling benchmarks, monitoring wells and continuous GPS station around Changhua County. Data from the co-located GPS and monitoring well station CGSG at Dacheng are used for COMPAC.

> *Figure 3.* Sample pictures of monitoring sensors.

> *Figure 4.* Cumulative subsidence in Changhua County from 1992 to 2010.

The Central Geological Survey (CGS, 1997) has published a hydrogeology model over Dacheng, and the model suggests that there are four aquifers and three aquitards. In this paper, the hydrogeological drilling data in 1997 from our borehole (made by ITRI, affiliated with the lead author) (Figure 5) is used to identify the boundary and thickness of each aquifer and aquitard based on the a priori knowledge of CGS. The thicknesses of aquifers 2 and 3 are about 100 m, and are relatively large compared to the aquifer thicknesses over other regions of Taiwan. Most of the soil formation over Dacheng contains fine sand and clay, with occasional sizable layers of coarse sand. Because the soil formation in Changhua is complicated, a land subsidence monitoring system sensitive to the compactions of all strata is needed to gather data for clarifying the mechanism of land subsidence.

A monitoring well, named CGSG, was installed in Dacheng in 1997, and provides more than 13 years of compaction data (Figure 2). Based on the soil formation, 25 magnetic rings were deployed at the CGSG well (Table 1) to collect monthly data. The vertical dislocation of two adjacent rings is the compaction of the soil layer within the two rings. With all dislocations collected by the rings, the contribution of each layer's compaction to the surface subsidence, which can be measured by leveling or GPS, is determined. Fig. 5 shows the cumulative compactions at different depths at CGSG starting from May 1997 at nearly annual intervals to July 2010. For example, the blue curve shows the cumulative compactions up to July 2004. Table 2 shows the cumulative compactions over May 1997 to July 2010 at selected depth ranges. Table 2 suggests that the major compaction occurs over the depth range between 52 and 153 m, followed by the range between 153 and 174, and then the range between 174 and 277 m. These three layers correspond to aquifer 2, aquitard 2, and aquifer 3 defined by CGS, and the compactions here contribute approximately 96% to the total compaction.

> *Figure 5.* Layers of sediments and cumulative compactions from May 1997 to a given time at CGSG. F1 –F4 indicates the four layers of aquifer and aquitard.

> **Table 1**
> Information for the monitoring well at station CGSG.
> | No. of magnetic rings | 25 |
> |---|---|
> | Sediment types | (1) 0 –120 m: interlayers of sand and clay (2) 120 –220 m: clay with thick coarse sand interbed (3) 220 –300 m: interlayers of sand and clay |
> | Depth of major compaction (m) | 50 –200 m |
> | Cumulative compaction from July 2001 to July 2007 (cm) | 51.3 cm |

> **Table 2**
> Cumulative compactions over different depth ranges at CGSG from May 1997 to July 2010.
> | Depth range (m) | Compaction (cm) | Percentage^a(%) |
> |---|---|---|
> | Aquifer 1 (F1) 0 –32 | 3.5 | 3.2 |
> | Aquitard 1 (T1) 32 –52 | 0.9 | 0.8 |
> | Aquifer 2 (F2) 52 –153 | 63.4 | 57.3 |
> | Aquitard 2 (T2) 153 –174 | 17.8 | 16.1 |
> | Aquifer 3 (F3) 174 –277 | 24.7 | 22.3 |
> | Aquitard 3 (T3) 277 –286 | 0.3 | 0.3 |
> | Aquifer 4 (F4) 286 –299 | 0.0 | 0.0 |
> | Sum | 110.6 | 100.00 |
>
> ^a Compaction in the depth range divided by the total compaction (110.6 cm).

A continuous GPS station was installed next to the CGSG well to determine the three-dimensional deformations for inter-comparison with the compactions from the well. The determination of the coordinates at this GPS station was carried out jointly with 20 other continuous GPS stations in Taiwan (Figure 6). The GPS stations in Fig. 6 were installed by various governmental agencies in Taiwan, including Central Weather Bureau (CWB), Industry Technology Research Institute (ITRI), Ministry of Interior (MOI), and Water Resource Agency (WRA).

> *Figure 6.* Distribution of 21 GPS stations established by various organizations in Taiwan (see the text for the abbreviations of the organizations).

Fig. 7(a) compares the vertical displacements from GPS and leveling with the total compactions (regarded as vertical displacements) from the monitoring well (based on Table 2 and Figure 5) at CGSG. The vertical displacements from the three sensors agree to 1 cm and that the subsidence can be attributed to compaction of strata in the interval measured by the monitoring well.
Fig. 7(a) also shows a slowdown of subsidence since July 2008. This is due to a strict regulation of groundwater consumption imposed here. To see the effect of groundwater change on subsidence, in Fig. 7(b) we compare the vertical displacements and groundwater level variations over July 2001-July 2005 at CGSG. Fig. 7(b) shows that seasonal land subsidence and uplift in some periods are highly correlated with the seasonal variation of groundwater level. For example, during January 2002 to July 2002, most of the GPS result shows an upward movement associated with the rise of groundwater level. A more in-depth analysis of the relation between groundwater and vertical displacement will be given in Section 3.

> *Figure 7.* (a) Vertical displacements from GPS, monitoring well and leveling at CGSG. (b) Groundwater level and subsidence at CGSG.

In comparison to the large vertical displacement seen in Fig. 7(a), the horizontal displacements at CGSG are small. This comparison is given in Fig. 8, which shows that the ranges of coordinate variation in the vertical and horizontal directions are about 53.9 cm and 1.0 cm, respectively. This large vertical-to-horizontal ratio suggests that the major stratum compaction at CGSG due to change of groundwater level occurs in the vertical direction. As such, it is plausible to use the one-dimensional (vertical) compaction model to describe the mechanism of subsidence at CGSG (see Section 4).

> *Figure 8.* GPS-derived coordinate variations in the north ($\Delta N$), east ($\Delta E$) and vertical ($\Delta h$) directions at CGSG.

## 3. Stress and strain at CGSG

As the first approximation, the subsidence at CGSG can be partially explained by the variation of groundwater level using the one-dimensional consolidation theory of Terzaghi (1925) as follows. First, the effective stress $\sigma_e$ of soil can be expressed as

$$
\sigma_e = \sigma_T - p_w \tag{1}
$$

where $\sigma_T$ is the total stress (the total overburden load or geostatic pressure) and $p_w$ is the fluid or pore water pressure. In a confined aquifer, the geostatic pressure changes negligibly with changes in fluid pressure in the confined aquifer, so that the change in the effective stress is due to the change in pore water pressure. That is, $\Delta \sigma_e = -\Delta p_w$, where $\Delta$ stands for change. The change in pore water pressure, $\Delta p_w$, is in turn caused by the change in groundwater level:

$$
\Delta p_w = \rho_w g \Delta h \tag{2}
$$

where
$\rho_w$ water density
$g$ gravity
$\Delta h$ change in groundwater level

Fig. 9 shows the relationship between groundwater level and strain at aquifer 2 of CGSG. A strain is defined as

$$
\tau = \frac{\Delta B}{B_0} \tag{3}
$$

where $\Delta B$ and $B_0$ are the compaction and the total thickness of aquifer 2 (101 m, Table 4). Because the vertical displacement from GPS and the total compaction from the monitoring well are consistent to 1 cm (Figure 7) and the sampling rate of GPS is higher than that of the well, a novel use of GPS data at CGSG was made in this paper. We used the parallel observations of GPS and monitoring well to compute the compaction ratios between the compaction at aquifer 2 and the displacement from GPS. For any desired epoch, this ratio was used to compute the compaction at aquifer 2 using the displacement from GPS at a much higher frequency than the monitoring well. Fig. 9 compares the in situ compactions (monitoring well) and the GPS-derived compactions at aquifer 2, which are consistent in depicting the behavior of the stratum deformation at CGSG. This suggests that, with proper auxiliary data, a high-frequency variation of the compaction at aquifer 2 can be determined using the GPS-derived displacements.

> *Figure 9.* The relationship between groundwater levels and strains over July 2001 to December 2009 from both monitoring well and GPS at aquifer 2 of CGSG. GPS-derived strains are given at 1-week interval. The red line fits the long-term inelastic trends and the three green lines fit the three elastic trends. Dates are given next to the four lines.

Fig. 9 shows that the cumulative strain increases almost linearly with decreasing groundwater level. This linear relation over the range of strain is consistent with inelastic behavior of aquifer compaction in the typical ranges of applied stresses in these aquifer systems (Leake and Prudic, 1991). At the ending session of Fig. 9, a significant rise of groundwater level (and hence a decrease in the measured effective stress) occurred (see also Figure 11 below), but the strain (compaction) remains unchanged.

The variation in the slope of groundwater level-strain is explained as follows. Without horizontal deformation (see Figure 8 for this assumption), the change in the soil volume is caused by the change in the thickness, that is, compaction. As such, the one-dimensional compressibility $\alpha$ is related to the skeletal specific storage $S_{sk}$ as

$$
\alpha = - \frac{\Delta B / B_0}{\rho_w g \Delta h} = \frac{S_{sk}}{\rho_w g} \tag{4}
$$

Eq.(4) leads to

$$
\Delta h = - \frac{\tau}{S_{sk}} \tag{5}
$$

Thus, for a constant $S_{sk}$, the strain will vary linearly with the groundwater level. Fig. 10 shows the relations between strain and groundwater level variation at three selected time spans where significant changes of groundwater level and compactions occurred. For each time span, a line is fitted to the strains and groundwater levels. The linear regressions result in correlation coefficients of about 0.86 for all cases, suggesting that the linear model fits well the relation between strain and groundwater level change.

> *Figure 10.* Fitted lines to groundwater level-strain during three time spans.

For each time span, the skeletal specific storage is the negative, inverse slope of the fitted line in Fig. 10. Table 3 shows the skeletal specific storage taken from the slopes in the three time spans. The decrease of the skeletal specific storage is related to the decrease in porosity resulting from compaction. The reduced porosity (in time) causes a reduction in compressibility and therefore a reduction in skeletal specific storage. As the compaction continues for a sufficiently long time, the stratum is slowly consolidated and the density increases with time. In the process of consolidation, the stratum turns from plasticity to elastoplasticity.

> **Table 3**
> Skeletal specific storage (in 1/m) at CGSG over three different time spans.
> | Time span | 9/2002 –12/2002 | 12/2004 –3/2005 | 12/2005 –3/2006 |
> |---|---|---|---|
> | Ske. spe. storage | 1.0$\times$10$^{-4}$ | 3.5$\times$10$^{-5}$ | 1.8$\times$10$^{-5}$ |

Being elastoplastic, the deformation is both elastic and inelastic, and eventually only a minor compaction will take place. At the final stage of consolidation, decrease in groundwater level will no longer cause stratum compaction. For example, during September 2002 to December 2002, a drop of 2 m in groundwater level results in an increase of about 0.00019 in strain. However, during December 2005 to March 2006, a 2-m groundwater level drop leads to only an increase of about 0.000034 in strain. The former (strain) is about 5.6 times larger than the latter.

The linear model in Eq. (5) can only roughly relate compaction to groundwater change. A detailed numerical model is needed to adequately account for the cause of compaction in connection to groundwater and some hydrogeological parameters. In this paper, we adopt the one-dimensional model COMPAC to model the subsidence at CGSG and the genetic algorithm is used to estimate the hydrogeological parameters in the model.

## 4. Modeling compaction by COMPAC

### 4.1. The principle

In Section 3, the compaction is only parameterized by the skeletal specific storage. Here we extend the parameterization using COMPAC (Helm, 1975) to account for (1) the elastic and immediate deformation of coarse-grained sediments (gravel or sand), and (2) the elastoplastic and delayed deformation of fine-grained sediments (clay, mud or silt). That is, the extended model is

$$
\Delta B = \Delta b + \Delta b' \tag{5}
$$

where $\Delta b$ and $\Delta b'$ are the elastic and elastoplastic parts, respectively. The elastic part is modeled as

$$
\Delta b = -S_{ske} b_0 \Delta h \tag{6}
$$

where $S_{ske}$ is the elastic skeletal specific storage of the coarse-grained sediment, $b_0$ is the total thickness and $\Delta h$ is the variation of groundwater level within the aquifer. $S_{ske}$ is about $1 \times 10^{-5} m^{-1}$ in the study area (Schwartz and Zhang, 2008). The elastoplastic part is modeled as

$$
\Delta b' = N_{equiv} \Delta b^* \tag{7}
$$

$\Delta b^*$ is the compaction of the fine-grained sediment and $N_{equiv}$ is the number of equivalent interbeds explained as follows. One aquifer may contain a large number of clay interbeds, and it may take a considerable computational time to calculate the total compaction from all interbeds. To reduce the computational time, the equivalent thickness of a single idealized aquitard was used to represent the thickness of an aquifer. The equivalent (or weighted average) thickness was estimated by Helm (1975)

$$
b^*_{equiv} = \sqrt{ \frac{1}{N} \sum_{j=1}^{N} b_j^{*2} } \tag{8}
$$

where
$N$ total number of the fine-grained interbeds (for aquitard $N=1$)
$b_j^*$ the thickness of specified interbed $j$

The number of equivalent interbeds is computed as (Liu and Helm, 2008a)

$$
N_{equiv} = \frac{1}{b^*_{equiv}} \sum_{j=1}^{N} b_j^* \tag{9}
$$

Because of the low hydraulic conductivity, the compaction of the fine-grained sediment depends on the pore pressure equilibrium to the surrounding aquifer. The vertical transient head distribution in the fine-grained sediment can be described by the diffusion equation

$$
\frac{K_z^*}{S_{sk}^*} \frac{\partial^2 h}{\partial z^2} = \frac{\partial h}{\partial t} \tag{10}
$$

where $z$ is vertical dimension, $K_z^*$ is the vertical hydraulic conductivity and $S_{sk}^*$ is the skeletal specific storage of a homogeneous aquitard. Coefficients $K_z^*$ and $S_{sk}^*$ are assumed to be time independent. Laboratory consolidation tests have indicated that the compressibility, and thus the skeletal specific storage, can vary significantly depending on whether or not the effective stress exceeds the past maximum effective stress (preconsolidation stress). When the effective stress is less than the preconsolidation stress, a change in effective stress will cause elastic deformation, compression for increases and dilation for decreases in the effective stress. When the effective stress exceeds the preconsolidation stress, the inelastic (or virgin) behavior is present. For the same change in effective stress, inelastic deformation can be one or two magnitude larger than elastic deformation. To account for the change of the skeletal specific storage, two separate values are used

$$
S_{sk}^* = \begin{cases} S_{ske}^* & \text{for } \sigma_e < \sigma_{max} \\ S_{skv}^* & \text{for } \sigma_e \ge \sigma_{max} \end{cases} \tag{11}
$$

where $\sigma_e$ is defined in Eq. (1) and $\sigma_{max}$ is the previous maximum stress (or preconsolidation stress) of soil.

To compute $\Delta b^*$, COMPAC divides a single fine-grained layer into $(J-1)$ layers with an uniform spacing of $\Delta z = b_0^* / (J-1)$ at any time step $n>0$ as follows

$$
\Delta b^* = \frac{\Delta z}{2} \left[ S_{ske}^* \sum_{j=1}^{J-1} (\Delta h(e)^n_j + \Delta h(e)^n_{j+1}) - S_{skv}^* \sum_{j=1}^{J-1} (\Delta h(v)^n_j + \Delta h(v)^n_{j+1}) \right] \tag{12}
$$

where
$\Delta h(e)^n_j = (h_{prec})^n_j - h^n_j$
$\Delta h(v)^n_j = (h_{prec})^n_j - (h_{prec})^0_j$
and $h^n_j$ groundwater level at step $n$
$(h_{prec})^0_j$ initial maximum preconsolidation stress.
$(h_{prec})^n_j$ preconsolidation stress

In this paper, the value $(h_{prec})^0_j$ is assumed to be uniform in depth throughout the entire aquifer system including aquitards, that is $h_{prec0} = (h_{prec})^0_j$ for any $j$. Note COMPAC does not require that $(h_{prec})^n_j$ be a constant. The preconsolidation stress $(h_{prec})^n_j$ changes with time and depth, and it is a function of the calculated vertical migration of stress within the subsidence model.

### 4.2. Estimating the hydrogeological parameters by the genetic algorithm

In Eq. (12), the observations $\Delta b^*$ (see the monthly observations in Fig. 7(a)) are from the magnetic ring readings of the CGSG monitoring well, and the four parameters to be estimated are the vertical hydraulic conductivity ($K_z^*$), inelastic skeletal specific storage ($S_{skv}^*$), elastic skeletal specific storage ($S_{ske}^*$), and initial maximum preconsolidation stress ($h_{prec0}$). The determination of the four parameters is based on the least-squares principle that minimizes the following objective function (the RMS difference between modeled and observed values):

$$
\Phi(x) = \sqrt{ \frac{ \sum_{k=1}^{n} [U_k(x) - V_k]^2 }{ n } } \tag{13}
$$

where
$U_k(x)$ model value at epoch $k$.
$V_k$ observed compaction
$n$ total number of observations
$x$ a vector containing the four parameters

In fact, $\Phi(x)$ is the root mean squared (RMS) misfit (residual) between the observations and model values. A genetic algorithm (Davis, 1991) was used to estimate the four parameters. In comparison to the method of Newton –Raphson for parameter estimation (Liu and Helm, 2008a), the genetic algorithm uses parameter encoding, reproduction, crossover, and mutation to determine the optimal values of the four parameters by minimizing the objective function.

## 5. Result of modeling compaction

### 5.1. Estimated parameters for one-dimensional compaction

Based on the analysis in Section 3, the major stratum compaction occurs at aquifer 2 and 3. Therefore, the four hydrogeological parameters are needed for the COMPAC model at aquifers 2 and 3, and aquitard 2. The data used for parameter estimation is the stratum compaction data from January 2003 to June 2008. The searching ranges for the genetic algorithm are as follows

$K_z^*$: 0.00001 to 1 (m/year) for both aquifers 2 and 3
$S_{skv}^*$ and $S_{ske}^*$: 0.00001 to 0.1 (1/m) for both aquifers 2 and 3
$h_{prec0}$: $-15$ to 0 m for aquifer 2, $-10$ m to 5 m for aquifer 3

The number of iterations for searching is set to 50000. In fact, the objective function (RMS misfit) becomes stable after some 30000 iterations. Use of 50000 iterations is to ensure the estimated parameters are finalized and stable. Table 4 shows the estimated parameters for aquifers 2 and 3 and aquitard 2. The RMS misfits in all cases are below 0.5 cm.

> **Table 4**
> Estimated parameters for the one-dimensional compaction model at CGSG and the RMS value of residuals.
> | Layer (depth range) | $K_z^*$ (m/y) | $S_{skv}^*$ (1/m) | $S_{ske}^*$ (1/m) | $h_{prec0}$ (m) | RMS (cm) |
> |---|---|---|---|---|---|
> | Aquifer 2 (52–153 m) | 3.12$\times$10$^{-03}$ | 3.19$\times$10$^{-03}$ | 4.07$\times$10$^{-04}$ | -5.626 | 0.450 |
> | Aquitard 2 (153–174 m) | 5.29$\times$10$^{-04}$ | 2.51$\times$10$^{-02}$ | 3.13$\times$10$^{-03}$ | -1.261 | 0.193 |
> | Aquifer 3 (174–277 m) | 6.20$\times$10$^{-04}$ | 1.25$\times$10$^{-02}$ | 4.28$\times$10$^{-04}$ | -2.047 | 0.234 |

For cross validation, we also used the method of Riley (1969) to estimate $S_{skv}$. Fig. 9 shows a long-term inelastic trend and several episodic elastic trends. We fitted a line to the long-term inelastic trend (red line in Figure 9), which gives $S_{skv} = 1.33 \times 10^{-3} m^{-1}$ (red line). However, Fig. 9 shows the total compaction of aquifer 2 that includes the effects of coarse-grained sediments and fine-grained sediments. However, in this paper, COMPAC models only the effect of the fine-grained sediments. Therefore, we need to adjust the value of $S_{skv}$ based on the actual thickness of aquifer 2. In aquifer 2, the total thickness is 101 m and the thickness of fine-grained sediments is 61 m. With Eq. (5), the adjusted $S_{skv}$ value is $2.22 \times 10^{-3} m^{-1}$, which is close to the model value ($S_{skv}$) of $3.19 \times 10^{-3} m^{-1}$ given in Table 4.

With the estimated parameters in Table 4, we determined the time constant needed to complete 93% compaction for each layer. The time constant, $t$, is defined as (Terzaghi et al., 1996)

$$
t = \frac{T_v H^2}{4 C_v} \tag{14}
$$

with

$$
C_v = \frac{K_z^*}{S_{skv}^*} \tag{15}
$$

where $C_v$ is coefficient of compaction, $H$ is thickness, and $T_v$ is set to 1. In Eq. (14), it is assumed that $H$ is equal to $b_{equiv}^*$. The time constant is also the time for a confining unit to equilibrate to the head of the surrounding aquifer. Table 5 shows the thicknesses and time constants of the three layers. For each layer, the equivalent thickness is smaller than the depth range given in Table 4, because the former contains only the fine-grained sediments in the layer while the latter is simply the difference in depths. Table 5 shows that aquifer 2 takes the least time to complete the compaction, followed by aquifer 3, and then aquitard 2. This suggests that aquifer 2 responds to groundwater change (either rise or drop) faster than the other two layers. Aquitard 2 takes the longest time to consolidate, and this is also consistent with the result in Table 4, which shows that the initial maximum preconsolidation stress ($h_{prec0}$) of aquitard 2 is larger than the $h_{prec0}$ values in the other two layers.

> **Table 5**
> Equivalent thickness and time constant for the three layers at CGSG.
> | Layer | Equivalent thickness (m) | Time constant (years) |
> |---|---|---|
> | Aquifer 2 | 30.54 | 238.3 |
> | Aquitard 2 | 21.00 | 5221.6 |
> | Aquifer 3 | 14.81 | 1106.3 |

### 5.2. Model validation and compaction prediction

The parameters in Table 4 are estimated from the observations over January 2003 to June 2008 in the COMPAC model. Here we use such parameters to predict compactions over June 2008 to June 2010, which are then compared with the monthly observations over this period. This is to investigate the possibility of predicting compaction based on the COMPAC model with appropriate hydrogeological parameters. Table 6 shows the cumulative compactions over January 2003 to June 2010 from the observations and from the model values of COMPAC (based on the parameters from Table 3). The RMS values of the monthly differences between the observation and model values, and the mean absolute percentage errors (MAPEs) over June 2008 to June 2010 are also given in Table 6. MAPE is the mean value of the absolute relative differences between model and observation. In all layers, the RMS differences are below 0.5 cm, and the MAPE are below 10%. These MAPEs are classified as good according to Lewis (1982a,b). This suggests that COMPAC is able to predict compactions to an accuracy consistent with the accuracy in the estimation of the four hydrogeological parameters.

> **Table 6**
> Cumulative compactions over January 2003 to June 2010 from observation and model, and RMS of monthly differences.
> | Layer | Obs. total compaction (cm) | Pred. total compaction (cm) | RMS diff. (cm) | MAPE |
> |---|---|---|---|---|
> | Aquifer 2 (52–153 m) | -14.3 | -15.0 | 0.484 | 8% |
> | Aquitard 2 (153–174 m) | -6.6 | -7.2 | 0.250 | 7% |
> | Aquifer 3 (174–277 m) | -14.6 | -14.6 | 0.210 | 5% |

> *Figure 11.* Comparison between observed and predicted compactions in three layers of CGSG.

Fig. 11 shows the monthly compactions from the observations and from the predictions of COMPAC in the three layers. The model values are in good agreement with the observations. Relatively large deviations between model and observation at aquifer 2 and aquitard 2 occurred over August 2008 to December 2008, when aquifer 2 experienced a rebound due to the increase of groundwater by about 6 m in this layer. During this period, no rebound at aquifer 3 occurred, and this is probably due to the relatively small increase of ground water (1.5 m) here. Based on Fig. 5, there are more thin layers of fine sediment at aquifer 2, and this type of stratum allows change in the water level in a short time period. That is, when the groundwater level rises significantly, aquifer 2 will quickly rebound, but aquifer 3 will continue to descend.

## 6. Discussion and conclusions

The long-term (more than 10 years) geodetic and geotechnical observations collected in this paper are complementary with each other in explaining land subsidence in Dacheng. Continuous GPS records from July 2001 to June 2010 show a cumulative vertical displacement of 53.9 cm and a horizontal displacement of 1 cm in Dacheng. This suggests that the major deformation caused by stratum compaction occurs in the vertical direction. The observations also depict some seasonal variations of land subsidence and uplift associated with groundwater variations. With a proper transformation from GPS coordinate variation to stratum compaction, the compactions at aquifer 2 were determined at a weekly frequency. The long-term skeletal storage coefficients estimated from the strains and groundwater levels suggest that the property of compaction has turned from plasticity into elastoplasticity.

This paper uses the COMPAC model to explain the observed compactions. In the modeling, the vertical hydraulic conductivities, elastic skeletal specific storage, and inelastic skeletal specific storage at aquifer 2, 3 and aquitard 3 were estimated by the genetic algorithm. The fact that the RMS residuals in all cases are below 0.5 cm suggests that the COMPAC model fits well the observations. The estimated parameters were used to determine the times needed to consolidate the three layers. It turns out aquifer 2 needs the least time for consolidation, followed by aquifer 3 and aquitard 2. Because aquifer 2 is quick to respond to groundwater change, it may be possible to mitigate land subsidence in Dacheng by increasing groundwater of aquifer 2. On the other hand, if groundwater at aquifer 2 is depleted, a quick compaction will occur. In conclusion, a proper management of groundwater at aquifer 2 is important for land subsidence mitigation in Dacheng.

Prediction of land subsidence based on COMPAC and the four estimated hydrogeological parameters results in an average MAPE of below 10% over June 2008 to June 2010. Thus, the compaction model (with estimated parameters), along with the change of groundwater level, can be used to predict future land subsidence with a sufficient confidence in Dacheng. However, the prediction will be sufficiently accurate over a future time span (2 years in the case study of this paper) only if the hydrogeological parameters are properly calibrated. As such, continuous collection of data from the monitoring system (Section 2) is critical to the success of prediction.

Although COMPAC can model land subsidence to a high accuracy, the model itself is one-dimensional and site specific. With the data from 7 monitoring wells and 40 groundwater wells in Changhua (Section 2), it is possible to extend the current study to cover all coastal areas in Changhua and use a model based on a three-dimensional groundwater flow (USGS MODFLOW model) and the SUB package to simulate land subsidence to determine the stratum compaction coefficients and to estimate the groundwater safe yield. In addition to Dacheng, Erlin (Figure 2) is another important township: it is the planned site of a science-based industrial park, which is vital to the economic development of Taiwan. Because this industrial park will consume a large amount of water, a proper water management plan taking into account land subsidence is of great importance. According to Table 6, the calibrated parameter values predict subsidence values consistent with the observations to 0.5 cm. Therefore, the water management agency of Taiwan (Water Resource Agency, WRA) can use our model to estimate future subsidence values under different situations with good confidence. In order to prevent irreversible compaction, WRA can manage to keep the groundwater levels of the field above the corresponding past maximum preconsolidation stress around the study area. The result from this paper will provide an important reference for such a management plan.

## Acknowledgements

This study is supported by Water Resource Agency, Taiwan, ROC.

## References

Amelung, F., Galloway, D.L., Bell, J.W., Zebker, H.A., Laczniak, R.J., 1999. Sensing the ups and downs of Las Vegas: InSAR reveals structural control of land subsidence and aquifer-system deformation. Geology 27 (6), 483 –486.

Buckley, S.M., Rosen, P.A., Hensley, S., Tapley, B.D., 2003. Land subsidence in Houston, Texas, measured by radar interferometry and constrained by extensometers. Journal of Geophysical Research 108 (B11), 2542.

Burbey, T.J., 2001. Stress –strain analyses for aquifer-system characterization. Ground Water 39 (1), 128 –136.

Burbey, T.J., 2008. The influence of geologic structures on deformation due to ground water withdrawal. Ground Water 46 (2), 202 –211.

Carreón-Freyre, D.C., Cerca, M., 2006. Delineating the near-surface geometry of the fracture system affecting the Querétaro valley, Mexico: correlation of GPR signatures and physical properties of sediments, Near Surface Geophysics, 4(1). EAGE (European Assoc. of Geoscientists and Engineers), pp. 49 –55.

CGS, 1997. The investigation of hydrogeology in the Choshui River alluvial fan, Taiwan (in Chinese). Central Geological Survey of Taiwan, Taipei.

Davis, L., 1991. Handbook of genetic algorithms. Van Nostrand Reinhold, New York. 385 pp.

Ferronato, M., Gambolati, G., Teatini, P., 2004. On the role of reservoir geometry in waterdrive hydrodynamics. Journal of Petroleum Science and Engineering 44 (3–4), 205 –221.

Galloway, D.L., Hoffmann, J., 2007. The application of satellite differential SAR interferometry-derived ground displacements in hydrogeology. Hydrogeology Journal 15 (1), 133 –154.

Hanson, R.T., 1989. Aquifer-system compaction, Tucson Basin and Avra Valley, Arizona. U.S. Geological Survey Water-Resources Investigations Report 88 –4172. 69 pp.

Helm, D.C., 1975. One-dimensional simulation of aquifer system compaction near Pixley, California, (1) Constant parameters. Water Resources Research 11 (3), 465 –478.

Hoffmann, J., Zebker, H.A., Galloway, D.L., Amelung, F., 2001. Seasonal subsidence and rebound in Las Vegas Valley, Nevada, observed by synthetic aperture radar interferometry. Water Resources Research 37 (6), 1551 –1566.

Hoffmann, J., Galloway, D.L., Zebker, H.A., 2003a. Inverse modling of interbed storage parameters using land subsidence observations, Antelope Valley, California. Water Resources Research 39 (2), 1231.

Hoffmann, J., Leake, S.A., Galloway, D.L., Wilson, A.M., 2003b. MODFLOW-2000 groundwater model-User guide to the subsidence and aquifer-system compaction (SUB) package. U.S. Geological Survey Techniques of Water-Resources Investigations, Open-File Report 03 –233. 46 pp.

Hsu, K.C., Wang, C.H., Chen, K.C., Chen, C.T., Ma, K.W., 2007. Climate-induced hydrological impacts on the groundwater system of the Pingtung Plain, Taiwan. Hydrogeology Journal 15 (5), 903 –913.

Hu, B.B., Zhou, J., Wang, J., Chen, Z.L., Wang, D.Q., Xu, S.Y., 2009. Risk assessment of land subsidence at Tianjin coastal area in China. Environmental Earth Sciences 59 (2), 269 –276.

Hu, J.C., Chu, H.T., Hou, C.S., Lai, T.H., Chen, R.F., Nien, P.F., 2006. The contribution to tectonic subsidence by groundwater abstraction in the Pingtung area, southwestern Taiwan as determined by GPS measurements. Quaternary International 147, 62 –69.

Hung, W.C., Liou, J.C., 2009. Fundamental Data Survey and Cross Analysis of Land Subsidence in Taipei Basin, Chahwa and Yunlin Area. Report of Industrial Technology Research Institute (ITRI), Hsinchu. 349 pp. (in Chinese).

Hung, W.C., Hwang, C., Chang, C.P., Yen, J.Y., Liu, C.H., Yang, W.H., 2010. Monitoring severe subsidence in Taiwan by multi-sensors: Yunlin, the southern Choushui River Alluvial Fan. Earth Science Geology 59, 1535 –1548.

Larson, K.J., Başağaoğlu, H., Mariño, M.A., 2001. Prediction of optimal safe ground water yield and land subsidence in the Los Banos-Kettleman City area, California, using a calibrated numerical simulation model. Journal of Hydrology 242, 79 –102.

Leake, S.A., Prudic, D.E., 1991. Documentation of a computer program to simulate aquifer-system compaction using the modular finite-difference ground water flow model. US Geological Survey Technique of Water Resources Investigation, 6 (A2). 68 pp.

Lewis, C.D., 1982a. Industrial and Business Forecasting Methods. Butterworths, London. 158 pp.

Lewis, C.D., 1982b. Industrial and Business Forecasting Methods. Butterworths, London. 158 pp.

Liu, Y., Helm, D.C., 2008a. Inverse procedure for calibrating parameters that control land subsidence caused by subsidence fluid withdrawal: 1. Methods. Water Resources Research 44, W07423.

Liu, Y., Helm, D.C., 2008b. Inverse procedure for calibrating parameters that control land subsidence caused by subsidence fluid withdrawal: 2. Field application. Water Resources Research 44, W07424.

Lopez-Quiroz, P., Doin, M.P., Tupin, F., Briole, P., Nicolas, J.M., 2009. Time series analysis of Mexico City subsidence constrained by radar interferometry. Journal of Applied Geophysics 69 (1), 1 –15.

McDonald, M.G., Harbaugh, A.W., 1988. A modular three-dimensional finite-difference groundwater flow model. US Geological Survey Technique of Water Resources Investigation, 6 (A1). 586 pp.

Munekane, H., Kuroishi, Y., Hatanaka, Y., Yarai, H., 2008. Spurious annual vertical deformations over Japan due to mismodelling of tropospheric delays. Geophysical Journal International 175 (3), 831 –836.

Pavelko, M.T., 2004. Estimates of hydraulic properties from a one-dimensional numerical model of vertical aquifer-system deformation, Lorenzi Site, Las Vegas, Nevada. U.S. Geological Survey Water-Resources Investigations Report 03 –4083. 35 pp.

Riley, F.S., 1969. Analysis of borehole extensometer data from central California. 2nd International Symposium on Land Subsidence, Tokyo (2), 423 –432.

Schmidt, D.A., Burgmann, R., 2003. Time-dependent land uplift and subsidence in the Santa Clara valley, California, from a large interferometric synthetic aperture radar data set. Journal of Geophysical Research 108 (B9), 2416.

Schwartz, F.W., Zhang, H., 2008. The fundamentals of ground water. John Wiley and Sons, Danvers. 592 pp.

Sneed, Michelle, Galloway, D.L., 2000. Aquifer-system compaction and land subsidence: measurements, analyses, and simulations? the Holly site, Edwards Air Force Base, Antelope Valley, California. U.S. Geological Survey Water-Resources Investigations Report 00 –4015 65 pp.

Teatini, P., Ferronato, M., Gambolati, G., Bertoni, W., Gonella, M., 2005. A century of land subsidence in Ravenna, Italy. Environmental Geology 47 (6), 831 –846.

Terzaghi, K., 1925. Principles of soil mechanics: IV, Settlement and consolidation of clay. McGraw-Hill, New York. 95 pp.

Terzaghi, K., Peck, R.B., Mesri, G., 1996. Soil Mechanics in Engineering Practice. Wiley, New York. 592 pp.

Wu, J.C., Shi, X.Q., Ye, S.J., Xue, Y.Q., Zhang, Y., Wei, Z.X., Fang, Z., 2010. Numerical simulation of viscoelastoplastic land subsidence due to groundwater overdrafting in Shanghai, China. Journal of Hydrologic Engineering 15 (3), 223 –236.