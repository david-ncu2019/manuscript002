# A novel framework for spatiotemporal groundwater pumping process estimation based on data-driven approaches

Hwa-Lung Yua,∗, Hua-Ting Tsenga, Ying-Fan Lina, Chun-Hung Chenb, Ying-Chang Kuob, Yun-Ta Chengb

a Department of Bioenvironmental Systems Engineering, National Taiwan University, Taipei, Taiwan  
b Water Resources Planning Institute, Water Resource Agency, Taichung, Taiwan  

**Keywords:** Empirical orthogonal function, Hilbert–Huang transform, Pumping amount estimation, Time series data analysis, MODFLOW

## Abstract

Understanding the spatial and temporal distribution of pumping activities is crucial for effective water resource management. However, obtaining accurate pumping records is often challenging, particularly in areas without efficient groundwater withdrawal permit systems. In this study, we propose a novel approach for identifying pumping activities and estimating their associated pumping rates across space and time. Our data-driven approach integrates empirical orthogonal function (EOF) and Hilbert-Huang transform (HHT) analyses on first-differenced head data to extract high-frequency head variations that are closely related to pumping activities. The identified pumping-associated head variations are used to estimate the on-and-off times of local pumping stations and their associated pumping-rate time series. We test our approach using a hypothetical aquifer with designed pumping and real precipitation time series. Our results show that the EOF analysis is able to distinguish pumping locations where distinct temporal head variabilities are present. HHT analysis is then able to effectively remove noise from the EOF-identified pumping-associated head variations. Compared to the designed pumping data, our results demonstrate that our proposed method is able to produce accurate pumping estimates in terms of both spatial and temporal distribution and total amounts. While our approach does have limitations, such as delayed and boundary effects, our results suggest that it can be an effective tool for pumping estimation in areas with relatively abundant head observations across space and time, which is a common scenario in Taiwan.

## Notation

| Symbol | Description |
|--------|-------------|
| $\mathbf{A}$ | Semi-unitary matrix |
| $a$ | Amplitude |
| $\breve{c}$ | Pumping-like EC |
| $\mathbf{I}$ | Identity matrix |
| $m$ | Number of pumping activities |
| $Q$ | Pumping rate |
| $r$ | Trend of the time series |
| $S$ | Storage coefficient |
| $\mathbf{s}$ | Spatial location |
| $s$ | Intrinsic mode functions |
| $t$ | Time |
| $t_u$ | Time at pumping is operated |
| $t_l$ | Time at pumping is shut down |
| $\Delta t$ | Observation interval |
| $\mathbf{U}$ | Semi-unitary matrix |
| $(x,y)$ | Point in the Cartesian coordinate system |
| $\mathbf{X}$ | First-differenced series of head |
| $\mathbf{Y}$ | Time series of head |
| $z$ | Time series |
| $(\alpha,\beta)$ | Constants equal to 4 |
| $\mathbf{\Lambda}$ | Diagonal matrix |
| $\lambda$ | Singular value |
| $\mu$ | EOFs |
| $\sigma$ | Standard deviation |
| $\omega$ | Frequency |

**Acronyms**

| Acronym | Definition |
|---------|------------|
| EC | Expansion coefficient |
| EMD | Empirical mode decomposition |
| EOF | Empirical orthogonal function |
| HHT | Hilbert-Huang transform |
| HSA | Hilbert spectral analysis |
| IMF | Intrinsic mode function |
| SVD | Singular value decomposition |

## 1. Introduction

Groundwater is one of the most valuable water resources, particularly in arid and semiarid areas for various uses of water. With all Taiwan receiving abundant rainfall annually, groundwater still plays an important role in this country. It is due to the regional rainfall climate on the island showing a large spatiotemporal variability between the dry and wet seasons that causes instability in the surface water supply (Chen and Chen, 2003). The essential characteristics of groundwater resources compared to other sources are their high stability and accessibility. These often cause decentralized pumping activities, and there are no appropriate rules and permits to regulate and control groundwater extraction in many areas (Molle and Closas, 2020; Llamas and Martínez-Santos, 2005). Thence, the overexploitation of groundwater has become an issue worldwide and has caused worrying consequences, such as land subsidence and sea intrusion. Furthermore, due to the high cost and low management efficiency, pumping rate measurement is often limited or scarce compared to pumping activities in general (Ross and Martinez-Santos, 2010; Martínez-Santos and Martínez-Alfaro, 2010). The lack of knowledge about groundwater withdrawal would increase uncertainty in estimating groundwater balances and the challenges for groundwater management.

A great deal of methods have been developed to estimate groundwater withdrawals that lack direct pumping measurements. Among them, model-based inverse modeling is one of the most widely used approaches (Lin et al., 2013; Shakoor et al., 2018). Although this approach can obtain the spatiotemporal distribution of groundwater extraction, it requires estimation with multiple inputs, including hydrogeological parameters and boundary conditions, and therefore the estimated results would contain significant uncertainties. Thus, lumped hydrological models have been applied to estimate large-scale groundwater extraction to reduce parameter uncertainties; however, these would neglect the variability on the local scale. (Tsanis and Apostolaki, 2009; Martínez-Santos and Martínez-Alfaro, 2010; Wada et al., 2014). This estimation lies on water budget analyses, and its uncertainty in pumping estimation can be affected by the propagation of uncertainties in determining other hydrological components for the water budget calculation (Moon et al., 2004). In addition, surrogate approaches have been used to identify the relationships between extraction rates and physical variables associated with pumping activities. For example, land use and weather data with their identified relationship can be applied to predict groundwater pumping (Keir et al., 2019). Among the potential surrogate variables, the transformation of power demand into pumping amount can estimate the temporal variation of groundwater extraction at a specific pumping station (Hurr and Litke, 1990; Chu et al., 2020). However, the power demand is measured with lower temporal resolution in many areas. It would be challenging to characterize the time series of pumping rates. Another popular approach is to estimate the groundwater extraction rate from the temporal fluctuations of groundwater heads. This approach uses groundwater characteristics that change in water volume in a groundwater system is proportional to its associated differences in head and can be estimated using a scaling factor (i.e., storage coefficient, typically designated as $S[-]$). Due to its ease of use and relatively low-cost properties, this groundwater head fluctuation-based method has been widely applied in pumping and recharge estimations (Leduc et al., 1997; Healy and Cook, 2002; Moon et al., 2004; Maréchal et al., 2006).

System forcings driven by natural or anthropogenic processes may exert very different impacts on groundwater head variation (e.g., pumping, precipitation, tidal wave, or evapotranspiration). These forcings should be especially concerned when using groundwater fluctuation to estimate recharge and extraction. Different forcings that influence groundwater can exhibit different frequencies and amplitudes and can be used to interpret complex variations of groundwater change. Thus, spectral analysis has emerged to evaluate the frequency and amplitude of head time series (Shih and Lin, 2002; Long and Konrad, 2020). Generally, groundwater head is a nonstationary variable. Its nonstationarity in the frequency domain has been used to explore the temporal patterns of the spectrum in groundwater variations and their relationships to other forcings through time–frequency analysis methods, such as the wavelet transform and Hilbert-Huang transform (HHT) (Johnson et al., 2012; Yu and Lin, 2015; Nourani et al., 2019). Apart from the methods above, unsupervised feature extractions are a powerful technique to reveal significant temporal or spatiotemporal features of head variations. Independent component analysis, one of the unsupervised feature extraction methods, has been widely used to identify the main stimuli patterns for groundwater variations (Liu et al., 2015; Hsiao et al., 2017; Tsai and Hsiao, 2020). Furthermore, empirical orthogonal function (EOF) analysis (sometimes called principal component analysis) is frequently applied to identify the spatiotemporal features of groundwater fluctuation. It is an effective method for extracting information from large data sets in spatiotemporal domains by decomposing the covariance kernel into sets of eigenfunctions. Moreover, the EOF analysis can reduce the dimension of a massive data set to a smaller dimension and accurately reconstruct the spatiotemporal variances of the original random fields (Hannachi et al., 2007). Therefore, EOF analysis has been increasingly applied to extract significant spatiotemporal signals from groundwater observations over space and time (Longuevergne et al., 2007; Yu and Chu, 2010; Page et al., 2012; Yu and Lin, 2015).

This study proposes a data-driven approach framework for estimating groundwater extraction based on the observed spatiotemporal groundwater fluctuation. The proposed approach integrates the EOF and HHT methods, revealing key spatiotemporal variations and time–frequency features of groundwater observations, respectively. Also, we validated our method by examining it in a synthetic test using MODFLOW.

## 2. Methodology

Spatiotemporal changes in the groundwater head can result from different natural and anthropogenic processes that interact with the groundwater system, such as recharge and withdrawal. Among these processes, pumping activities can often introduce more rapid variations in heads on a relatively regular basis over time and in space. This study estimated groundwater extraction by identifying pumping processes from groundwater fluctuations by transforming pumping-associated groundwater fluctuations into pumping operation time series throughout the space. Our method mainly includes three steps: 1. trend removal, 2. EOF analysis, and 3. HHT analysis.

### 2.1. Trend removal

To remove the trend, we applied the differencing approach to the time series of groundwater head observations to retrieve stationary patterns of fluctuations. Differencing approach is the widely used method for transforming original time series into their stationary counterparts (Ahn and Salas, 1997). The differenced series $\mathbf{X}(\mathbf{s},t)$ is the change between consecutive data from the original series at spatial position $\mathbf{s}$ and time $t$. Groundwater head observations, for the case of first-order differencing, are formulated as follows.

$$
\mathbf{X}(\mathbf{s},t) = \mathbf{Y}(\mathbf{s},t) - \mathbf{Y}(\mathbf{s},t-\Delta t) \tag{1}
$$

where $\mathbf{Y}(\mathbf{s},t)$ denotes the original series of groundwater head and $\Delta t$ is the observation interval. $\mathbf{X}(\mathbf{s},t)$ represents a first-differenced series and can be considered to be a detrended series with respect to $\mathbf{Y}(\mathbf{s},t)$, and therefore it comprises the high-frequency stationary part of the original process.

### 2.2. Empirical orthogonal function analysis

The major spatiotemporal patterns of the differenced series $\mathbf{X}(\mathbf{s},t)$ were revealed by the EOF method, which is used to extract significant high-frequency spatiotemporal signals from groundwater observations. EOF method decomposes a continuous spatiotemporal random field $\mathbf{X}(\mathbf{s},t)$ into the additive spatiotemporal multiplication form as follows (Pearson, 1901; Hotelling, 1933; Hannachi et al., 2007)

$$
\mathbf{X}(\mathbf{s},t) = \sum_{k=1}^{M} c_k(t) u_k(\mathbf{s}) \tag{2}
$$

where $M$ is the number of modes in orthogonal spatiotemporal random fields. The modes are formulated as an optimal set of orthogonal spatial functions $u_k(\mathbf{s})$ called EOFs, and their associated expansion functions of time $c_k(t)$ called EOF expansion coefficients (ECs), defined as the projection of $\mathbf{X}(\mathbf{s},t)$ on $u_k(\mathbf{s})$. The leading EOFs can usually explain a fair amount of observed variances of the original spatiotemporal data set. The EOF analysis is commonly performed using the singular value decomposition (SVD) method (Hannachi et al., 2007). A $p \times n$ matrix of the first-differenced spatiotemporal head series $\mathbf{X}(\mathbf{s},t)$ situated at $p$ locations and $n$ instances can be decomposed as

$$
\mathbf{X} = \mathbf{U} \mathbf{\Lambda} \mathbf{A}^{\mathsf{T}} \tag{3}
$$

where $\mathbf{U} \in \mathbb{R}^{p \times M}$ and $\mathbf{A} \in \mathbb{R}^{n \times M}$ are the semi-unitary matrix, i.e., $\mathbf{A}^{\mathsf{T}} \mathbf{A} = \mathbf{U}^{\mathsf{T}} \mathbf{U} = \mathbf{I}_r$ with $r \leq \min(n,p)$, where $\mathbf{I}_r \in \mathbb{R}^{r \times r}$ is the identity matrix. This also known as compact SVD in which $\mathbf{\Lambda} \in \mathbb{R}^{r \times r}$ is square diagonal matrix with only non-zero singular values. In Eq. (3), the columns of $\mathbf{U}$, i.e., $u_k$, are essentially EOFs as the spatial orthonormal basis of the spatiotemporal data matrix. The diagonal matrix $\mathbf{\Lambda} \in \mathbb{R}^{r \times r}$ contains the singular values $\lambda_1, \ldots, \lambda_r$ of $\mathbf{X}$ satisfying $\lambda_1 \ge \lambda_2 \ge \cdots \ge \lambda_r > 0$. On the basis of the formation of the singular value decomposition, the projections of the $k$th EOF can be estimated by $\mathbf{\Lambda}_k a_k(t)$, and the spatiotemporal decomposition of Eq. (2) by the EOF analysis can be rewritten as

$$
\mathbf{X}(\mathbf{s},t) = \sum_{k=1}^{M} \mathbf{\Lambda}_k a_k(t) u_k(\mathbf{s}) \tag{4}
$$

As mentioned above, $M$ must be less than or equal to $r$. When analyzing uneven spatiotemporal sampled data, the geometric relationship between the spatiotemporal data set should be taken into account to avoid excess variances at clustering data locations that can distort the EOF results (Karl et al., 1982). We performed a spatiotemporal estimation of groundwater heads using a geostatistical method, i.e., the Bayesian maximum entropy method, before removing the trend removal and performing the EOF analysis. The Bayesian maximum entropy method is an epistemic-based geostatistical method, which distinguishes general and specific knowledge of spatiotemporal processes and generates more informative spatiotemporal maps of variables of interest (Christakos, 1990, 2000). Furthermore, the EOF results are rescaled and rotated using the Varimax method to obtain more stable and explainable, say physical meaningful spatiotemporal patterns of groundwater head variations. The Varimax method is the most well-known and widely used rotation technique for multivariate analysis, by which an orthogonal matrix is applied to EOF rotation to simplify the EOF structure, pushing the loading coefficients of EOFs to zeros or plus and minus (Kaiser, 1958). For more details on the EOF analysis, the reader can refer to the research of Hannachi et al. (2007), Yu and Chu (2010) and Yu and Lin (2015).

### 2.3. Hilbert-Huang transform analysis

Different spatial scales can be observed in the significant spatial features of the transformed head variations. Based on the assumption that the dominant forcing for high-frequency groundwater head variations is direct infiltration or pumping activities, the spatial extent scale in each EOF can be considered as the criterion to classify the two forcings. Direct infiltration and pumping can have relatively large and local spatial scales, respectively.

Although EOF analysis can differentiate processes with distinct space–time variation patterns, in most cases, the signals from multiple contributing factors can still be contained in the associated time series of ECs. This study proposes a time series decomposition approach by using the HHT method to differentiate between the pumping activities and the variations from other sources from the pumping-like ECs (i.e., ECs associated with relatively localized EOFs). The HHT is a method for analyzing nonlinear and nonstationary signals, comprising empirical mode (EMD) and Hilbert spectral analysis (HSA). Considering a time series $z(t)$, EMD decomposes $z(t)$ into a sum of intrinsic mode functions (IMFs) $s_j(t)$ and a residual $r(t)$ as shown below.

$$
z(t) = \sum_{j=1}^{k} s_j(t) + r(t) \tag{5}
$$

where the residual $r(t)$ represents the trend of the time series; $s_j(t)$ is a well-defined Hilbert spectrum, and its complex form or analytic signal has the form of $s_j^c(t) = s_j(t) + i\mathcal{H}\{s_j(t)\} = a_j(t) e^{i \int \omega_j(t) dt}$ with the Hilbert transform $\mathcal{H}\{\cdot\}$, in which $\omega_j(t)$ and $a_j(t)$ are the time–frequency curve and the amplitude of the analytic signal, $s_j^c(t)$, respectively. The IMFs, $s_j(t)$, have two properties: one is that the numbers of extreme and zero crossings differ at most by unity; another is that the average of the upper and lower envelopes defined by the local extrema must be zero at all times (i.e., the function is symmetric concerning zero). IMFs are retrieved by a recursive sifting process using the empirical mode decomposition (EMD) method (Huang et al., 1998). EMD estimates an IMF by repeatedly removing the mean of the envelopes of local extrema from the original time series until the stopping criterion is met. Namely, the difference of the estimated IMFs in the consecutive sifting steps is negligible (Huang and Wu, 2008).

IMFs contain the separated oscillation modes of a head variation time series across different scales, and each IMF theoretically contains its specific oscillation mode of a time series. In other words, IMFs consist of the main pumping temporal modes of identified pumping-like ECs; however, IMFs estimated by the EMD approach can be noisy and can significantly distort the estimation of pumping activities. The contaminated signals are considered for parts with distinct $\omega_j(t)$, or/and $a_j(t)$, across certain IMFs of the EC using the following criteria.

$$
\begin{aligned}
|\omega_j(t) - \overline{\omega_j(t)}| &> \alpha \sigma_{\omega_j} \\
|a_j(t) \omega_j(t) - \overline{a_j(t) \omega_j(t)}| &> \beta \sigma_{a_j \omega_j}
\end{aligned} \tag{6}
$$

where the overbar represents the medians and $\sigma$ denotes the standard deviation. The constants $\alpha$ and $\beta$ are introduced to determine the outliers of $\omega_j(t)$ and $a_j(t)\omega_j(t)$, respectively. This study adopts the values of 4 for $\alpha$ and $\beta$. Moreover, we cut 400 h at early and late times, but during the iteration of the detection of contaminated signals to avoid the inevitable effect of the boundary condition. We even used the mirror extension method (Wang et al., 2019) after each iteration round to keep the time series the same length.

In the proposed signal cleaning process using HHT and noise identification, two criterion in Eq. (6) are performed recursively until $\omega_j(t)$ and $a_j(t)\omega_j(t)$ both satisfy the proposed criteria. In each iteration, the EC is removed at times when the contaminated signals existing in any of the IMFs are contaminated and then reconstructed using a conventional time-series interpolation method. The pump-induced head variations can have the characteristic that the local maximum and minimum of groundwater head variation are closely associated with the times of turning on and off the pumping stations, respectively. On the basis of denoised pumping-like ECs, $\breve{c}_k(t)$, their associated spatiotemporal pumping rates can be estimated as follows:

$$
Q_k(\mathbf{s},t) = S(\mathbf{s}) u_k(\mathbf{s}) \frac{\breve{c}_k(t_u) - \breve{c}_k(t_l)}{t_l - t_u}, \quad t_u \le t \le t_l \tag{7}
$$

where $Q_k(\mathbf{s},t)$ is the estimate of the pumping rates in the space–time domain associated with the $k$-th EOF feature, $\breve{c}_k(t_u)$ and $\breve{c}_k(t_l)$ represent the local maxima and minima in $k$th pumping-like ECs, respectively. As Eq. (7) indicates, $u_k(\mathbf{s})(\breve{c}_k(t_u) - \breve{c}_k(t_l))$ represents the groundwater head drawdown from $t_u$ to $t_l$ resulting from the constant pumping rate $Q_k(\mathbf{s},t)$ between $t_u$ and $t_l$. According to Eq. (2), the spatiotemporal pumping rates across the study area can be reconstructed by considering all identified pump-induced features across space and time, that is, $Q(\mathbf{s},t) = \sum_{k=1}^m Q_k(\mathbf{s},t)$ with the $m$ identified pumping activities, wherein all pumping-like ECs can have a different series of $t_u$ and $t_l$.

## 3. Performance analysis on synthetic data

### 3.1. Synthetic aquifer and head observations

For the validation of the method, we developed a two-dimensional finite-difference model for a homogeneous unconfined aquifer with a hydraulic conductivity of 0.3678 m/h and a $S$ of 0.01, which are modified from the aquifer properties of the Choushui River alluvial fan, Taiwan, using MODFLOW software. In addition, the numerical model has been verified by comparing it with the Theis solution with Jacob’s correction (Kruseman et al., 1970). Fig. 1 shows the model setup for numerical simulation. The hydraulic head was assumed to descend linearly from the right elevation of 24.5 m to the left elevation of 0.5 m. The datum of aquifer bottom is situated at −100 m. (see Fig. 1(a)). The difference in head at the left and right boundaries caused a natural leftward flow driven by the hydraulic gradient. Each finite-difference grid had a size of 500 × 500 m². Furthermore, the aquifer was described by 40 × 40 square elements. This means that the aquifer is 20 km long and 20 km wide (Fig. 1(b)). As Fig. 1(b) illustrates, the flow boundaries at $y = 0$ and 20 km were subject to the no-flow condition (a special case of the Neumann-type condition that has zero value), while the boundaries at $x = 0$ and 20 km were specified as constant-head condition (a Dirichlet-type condition) marked as black right- and left-pointing triangles. We consider the pumping rates to be in the range of 0 to −75 m³/hr with different pumping pattern and operating frequency. The analysis period is chosen in the summer season, which is usually rainy in Taiwan during June to September. We considered infiltration due to uniformly distributed precipitation on the surface of the aquifer. The infiltration time series is modified from the USGS Soil Conservation Service (SCS) curve number procedure to a real rainfall time series observed at the Zhu-Tang station from June 20 2016 to September 20 2016. In addition, we included four intermittent pumping activities labeled $W_1$, $W_2$, $W_3$, and $W_4$, respectively, located in the plane $x$−$y$ at the points (5.75 km, 14.25 km), (6.25 km, 5.75 km), (9.75 km, 10.25 km), and (14.25 km, 8.75 km) that influence the aquifer flow system. Fig. 1(c) shows that the infiltration process. Fig. 1(d) displays four sets of time series of pumping rate used in pumping wells. The total simulation time is 8640 h (360 days) for the numerical simulation.

*> **Fig. 1.** Groundwater head simulation in a synthetic unconfined aquifer with an (a) east–west cross-sectional elevation profile, (b) symbols ∙,▴,▶, and◀ representing the pumping, observation location, left head boundary, and right head boundary locations, respectively, (c) time series of direct infiltration resulting from precipitation, and (d) time series of pumping rates at the four pumping locations. The pink shaped area in (c) and (d) represents the analysis period. (For interpretation of the references to color in this figure legend, the reader is referred to the web version of this article.)*

### 3.2. Results

Fig. 2 shows the results of (a) groundwater head simulation and (b) the related first-differenced head at the four selected observation sites located at (6.25 km, 6.25 km), (5.25 km, 14.75 km), (9.75 km, 10.25 km), and (172.5 km, 7.25 km), labeled $O_1$, $O_2$, $O_3$, and $O_4$, respectively. As shown, the time series consists of the variations of multiple frequencies and amplitudes resulting from a variety of external forcings across space and time, in which the major high-frequency part of the head variation can be highly associated with the results of pumping and precipitation processes. The high-frequency variation can be more clearly identified from the first-differenced process, as shown in Fig. 2(b).

*> **Fig. 2.** The time series of (a) the observation heads, and (b) their corresponding first-differenced processes at the four selected locations.*

Fig. 3 shows the EOF results from the analysis of first-differenced head processes. The significant part of each EOF result has a different area with a distinct spatial extent. This feature can be used as an indicator to distinguish between the head variations perturbed by pumping and precipitation processes. In general, the spatial extent of a precipitation event can generally be much larger than that of the groundwater withdrawal activities at a pumping station (i.e., the EOFs showing a darker area on the whole map, like EOF1 and EOF10). As a result, we consider the EOF results with relatively spatially-localized patterns to be more associated with pumping activities (from EOF2 to EOF9 displaying the darker dots within the brighter areas). Fig. 3 exhibits that the identified localized EOFs are closely identical to the pumping locations.

*> **Fig. 3.** Spatial distributions of EOF1–EOF10.*

Based on the identified pumping-related EOFs, their associated ECs in Fig. 4 are used to identify pumping activities. The irregularly significant change in the amplitude variation implies that the identified pumping-associated ECs can be contaminated by other hydrological processes (i.e., precipitation). As shown in Fig. 4, the pumping signals in pumping-associated ECs are contaminated or even masked by precipitation-associated variations.

*> **Fig. 4.** Temporal distributions of EC1–EC10 obtained from the first-differenced series of head observations, in which the sub-windows show the details of the pumping-like patterns masked by the precipitation signals.*

Fig. 5 shows the time series of the EC6, the IMF1 of EC6 from HHT analysis, and the IMF1-associated time-varying instantaneous amplitude and frequency series, i.e., $a_1(t)$ and $\omega_1(t)$. According to Fig. 5(c) and (d), it shows a clear precipitation-associated variation in the pumping-related EC6 series, in which the periods with contamination can have distinct amplitude and frequency variations. Furthermore, the rises of frequency series correspond to the abrupt changes of EC series, and the product of the frequency and amplitude series has a strong correlation with the precipitation series, as shown in Fig. 5(e) and (f), respectively. Therefore, the outliers of frequency and frequency-amplitude product provides an effective indicator about the temporal locations of contamination when the temporal variation significantly deviates from the regular process identified in the specific IMF. Using the proposed denoise/outlier detection criteria, Eq. (6), the times with serious noises in EC6 can be identified for the further removal, as indicated in Fig. 5(e) and (f). After the proposed denoise procedure, all pumping-associated ECs can be retrieved, as indicated in Fig. 6.

*> **Fig. 5.** The time series of the (a) precipitation, (b) EC6, (c) the IMF1 of EC6 from HHT analysis, and the IMF1-associated time-varying (d) instantaneous amplitude and (e) frequency series, and (f) product of the frequency and amplitude series, in which the marked red points denote identified outliers. (For interpretation of the references to color in this figure legend, the reader is referred to the web version of this article.)*

*> **Fig. 6.** The denoised (solid) and original (dashed) time series of EC1–EC10.*

Because the EOF analysis is applied on the first-differenced processes, a back-transform is required to obtain the actual head variation resulting from the pumping activities at the identified pumping location. In Fig. 7, it shows the identified first-differenced EC5 and its associated head variation. The pumping activities at the identified head variation can be retrieved in terms of time series of the average head change, as shown in Fig. 7(c). Based on the estimation of the average head change, the estimated rate in space–time can be obtained by using Eq. (7). In Fig. 8, it shows the spatiotemporal pumping rate estimation across the entire study domain. Results show that our proposed approach can not only approximate the predetermined pumping location but also the temporal variation of pumping rates associated with each pumping location. As shown, the estimated pumping location is an area centered at the actual pre-defined pumping location, because the pumping activities can induce head variation at both the pumping location and its surrounding area. Table 1 shows the comparison between the pumping amount in each pre-determined well and the total pumping amount estimation in its associated area. Results show that estimated pumping amounts are close to the pre-determined pumping amounts with a total relative error of 6.6%.

*> **Fig. 7.** The time series of (a) the first-differenced head, (b) the restored head with pumping-like pattern, and (c) the estimated pattern of pumping activities.*

*> **Fig. 8.** The graphs of (a) spatial distribution of estimated total pumping amount, and (b) time series of simulated (orange lines) and estimated (blue lines) pumping rates at the four pumping wells. (For interpretation of the references to color in this figure legend, the reader is referred to the web version of this article.)*

**Table 1**  
Exact and estimated pumping amounts for four pumping wells and the total pumping amounts.

| Pumping well | Exact pumping amounts | Estimated pumping amounts | AE | RE |
|--------------|----------------------|--------------------------|----|----|
| $W_1$ | 18,979 m³ | 24,915 m³ | 5,936 m³ | 23.8% |
| $W_2$ | 25,181 m³ | 26,389 m³ | 1,208 m³ | 4.6% |
| $W_3$ | 29,316 m³ | 25,542 m³ | 3,774 m³ | 14.8% |
| $W_4$ | 26,494 m³ | 30,164 m³ | 3,670 m³ | 12.2% |
| Total | 99,970 m³ | 107,010 m³ | 7,040 m³ | 6.6% |

Note: AE and RE represent the absolute error and relative error, respectively.

## 4. Discussions

This study proposed a novel approach to estimate the space–time pumping activities from head observations. To our knowledge, this study is the first data-driven groundwater head analysis that not only identifies but also quantifies, the important space–time patterns of interest, i.e., pumping rates. Furthermore, the proposed method does not require prior knowledge of pumping locations, making it useful for estimating pumping in areas where pumping data is absent. Although a variety of pattern recognition techniques have been applied in analyzing spatiotemporal groundwater head variations; however, most of the previous data-driven approaches focused only on identifying the patterns of influential contributors without quantifying the identified patterns (Yu and Chu, 2010, 2012; Yu and Lin, 2015; Lin et al., 2015; Hsiao et al., 2016; Tsai et al., 2017; Tsai and Hsiao, 2020). Because there is no physical model used in the estimation, our data-driven pumping estimation can be considered as indirect measurements to be incorporated in the process of groundwater modeling, especially in the areas with relatively abundant space–time head observations and limited pumping measurements, for example, aquifers in Taiwan.

Time series of groundwater head observations can commonly exhibit trends with a variety of time scales, such as multiyear and seasonal trends, which can generally be associated with the large-scale natural processes of the groundwater system (e.g., recharge or discharge processes). In other words, the trends in time series can generally present greater spatiotemporal variation that can possibly mask the variability introduced from local activities such as pumping. To identify pumping activities hidden in water fluctuations, trend removal is essential before applying spatiotemporal pattern recognition methods. In time series analysis, differencing has been widely used to stabilize the mean of a time series by removing the changes of the head of a time series, i.e., eliminating or reducing trend and seasonality. The differencing is an effective approach to make time series stationary. Although higher-order differencing can better stabilize a nonstationary time series, this study found that first-order differencing works sufficiently in our cases. In real-case applications, it is useful to perform the proposed first-differencing analysis for the data set during a prespecific period, since pumping activities can commonly depend on spatiotemporal patterns of water demand that are associated with factors such as irrigation schedules and farming operation habits. In other words, first-order differencing can generally be effective since groundwater fluctuation can be relatively stationary during a specific period with temporal lengths of about weeks to months, depending on the characteristics of the water demand (e.g., crop water demand patterns).

Multiple significant pumping patterns can exhibit nearby a specific pumping location with EOF analysis. Since pumping activity is completely derived from head variations, observation wells closer to pumping locations can have a faster hydraulic response than those farther away from pumping stations. It implies that the temporal variation of pumping rates at locations away from the pumping stations can have a time delay from the actual pumping activity. Although some of the pumping rates can have certain time shifts to their real counterpart, because some part of flow requires more time to propagate from the observed locations to the pumping wells, this study demonstrated that our approach can still possibly characterize the pumping rates at the identified pumping locations. As shown in Fig. 2, two EOFs can be identified at similar locations due to the delayed temporal patterns resulting from the head drawdown propagating from the pumping location. In Fig. 8, the identified pumping areas are centered at the pre-determined pumping locations; similarly, in the temporal estimation, some delayed pumping rate estimations can also be observed. Despite the observed difference between the actual and identified space–time pumping distribution, Fig. 8 and Table 1 show that our results can mostly retrieve the simulated pumping distribution across space and time.

Pumping estimation directly from groundwater head drawdown can also be influenced by other factors. As observed in this study, the relative errors between the actual and estimated pumping amounts were caused not only by the delayed effect but also by the boundary conditions of the aquifer (i.e., constant-head and no-flow conditions). The constant-head condition would continue to charge the water to the pumping well due to the tremendous water resources, while the no-flow condition would play the role of a barrier to block groundwater flowing toward the pumping wells. Thus, in other words, if the pumping well is adjacent to a stream or is installed in a leaky aquifer, the majority of the pumped water would be recharged from other sources, e.g., river water, which may give rise to an underestimation of the pumping amounts due to the stream depletion. If the pumping well is installed close to the no-flow boundary, the additional head drawdown can cause the overestimation of pumping amount by the proposed approach. It implies that the knowledge of pumping locations and their surrounding environment is important for assessing the uncertainty of the estimation from the proposed method.

Understanding the spatiotemporal variations in groundwater levels is essential for using the proposed method in pumping rate estimation. In order to identify the changes in groundwater levels caused by pumping extraction, the observation temporal frequency of groundwater levels needs to be higher than the frequency of pumping activities. On the other hand, the pumping locations can only be detected while the monitoring wells are located within their pumping impact radius which is associated with hydrogeological parameters and pumping duration. If the pumping and monitoring wells are far apart, estimates may be less accurate due to reduced sensitivity of groundwater levels to pumping perturbations. The spatial and temporal resolutions of groundwater observations can affect the estimation quality of spatiotemporal groundwater level variation, which is crucial to the performance of the proposed method for pumping rate estimation. In cases where temporal high-frequency data is only available recently in a short period, the proposed method can be applied during periods with no rainfall or irrigation activity. In this case, Eq. (7) can be directly applied to estimate the time-varying pumping rates based on the groundwater level changes solely caused by pumping.

The knowledge of hydrogeological parameters also plays an important role in space–time pumping estimation. The primary idea of this study is to retrieve the pumping activities with respect to the beginning of the groundwater head drawdown and recovery. The proposed approach requires the storage coefficient, $S$, to transform the identified groundwater level change into the change in water amount in the aquifer. Due to the spatial heterogeneity, the observations of hydrogeological parameters are commonly limited to estimate the spatial distribution of hydrogeological parameters. In the case of storage coefficients, they are commonly more scarce than hydraulic conductivities, because their observations require multiple wells in regular pumping test techniques. Recent studies have shown that an advanced geostatistical method has been proposed to improve the estimation confidence in hydrogeological parameters with limited observations. More studies will be required to assess the application of the advanced space–time geostatistical or machine learning estimation method for parameter estimation in the groundwater system and its impact on pumping estimation.

## 5. Conclusions

This study proposes a data-driven approach to estimate spatiotemporal pumping rate distribution from groundwater head observations across space and time. We applied our proposed approach to a synthetic groundwater level simulation with space–time varying pumping activities and infiltration with actual precipitation. The results show that EOF analysis can effectively classify the space–time patterns of high-frequency head variations, and HHT analysis helps to retrieve the target pumping signals by differentiating the processes with distinct time–frequency characteristics. The integration of EOF and HHT analyses can reveal the pumping-related signals from the first differenced head observations and their corresponding pumping rates. This study shows that the proposed approach can provide informative groundwater withdrawal estimation with the knowledge of groundwater level variation. Although pumping estimation uncertainties can be introduced from factors including storage coefficient and groundwater level estimation, the proposed approach suggests an efficient way in areas without effective groundwater withdrawal management; however, with systematic groundwater level monitoring, and therefore the results can be valuable references to improve understanding of the groundwater system and groundwater management.

## CRediT authorship contribution statement

**Hwa-Lung Yu:** Conceptualization, Methodology, Supervision, Writing – review & editing, Project administration, Validation. **Hua-Ting Tseng:** Software, Writing – original draft, Visualization, Formal analysis. **Ying-Fan Lin:** Writing – original draft, Writing – review & editing, Visualization. **Chun-Hung Chen:** Methodology. **Ying-Chang Kuo:** Methodology. **Yun-Ta Cheng:** Methodology.

## Declaration of competing interest

The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

## Data availability

No data was used for the research described in the article.

## Acknowledgements

This research was supported by the grants from the Taiwan National Science and Technology Council (110-2621-M-002-012-MY3, 111-2221-E-002-056-MY3, 111-MOEA-M-008-001, and 112-MOEA-M-008-001), from Taiwan Water Resources Agency (109-R-12-03-01-013-01-0), and from Taiwan Higher Education Sprout Project (111L8807 and 111L890304).

## References

Ahn, H., Salas, J.D., 1997. Groundwater head sampling based on stochastic analysis. Water Resour. Res. 33 (12), 2769–2780. http://dx.doi.org/10.1029/97WR02187.

Chen, C.-S., Chen, Y.-L., 2003. The rainfall characteristics of Taiwan. Mon. Weather Rev. 131 (7), 1323–1341. http://dx.doi.org/10.1175/1520-0493(2003)131<1323:TRCOT>2.0.CO;2.

Christakos, G., 1990. A Bayesian/maximum-entropy view to the spatial estimation problem. Math. Geol. 22 (7), 763–777. http://dx.doi.org/10.1007/BF00890661.

Christakos, G., 2000. Modern Spatiotemporal Geostatistics, Vol. 6. Oxford University Press.

Chu, H.-J., Lin, C.-W., Burbey, T.J., Ali, M.Z., 2020. Spatiotemporal analysis of extracted groundwater volumes estimated from electricity consumption. Groundwater 58 (6), 962–972. http://dx.doi.org/10.1111/gwat.13008.

Hannachi, A., Jolliffe, I.T., Stephenson, D.B., 2007. Empirical orthogonal functions and related techniques in atmospheric science: A review. Int. J. Climatol. A J. R. Meteorol. Soc. 27 (9), 1119–1152. http://dx.doi.org/10.1002/joc.1499.

Healy, R.W., Cook, P.G., 2002. Using groundwater levels to estimate recharge. Hydrogeol. J. 10 (1), 91–109. http://dx.doi.org/10.1007/s10040-001-0178-0.

Hotelling, H., 1933. Analysis of a complex of statistical variables into principal components. J. Educ. Psychol. 24 (6), 417. http://dx.doi.org/10.1037/h0071325.

Hsiao, C.-T., Chang, L.-C., Tsai, J.-P., Chen, Y.-C., 2017. Features of spatiotemporal groundwater head variation using independent component analysis. J. Hydrol. 547, 623–637. http://dx.doi.org/10.1016/j.jhydrol.2017.02.021.

Hsiao, C.T., Tsai, J.P., Chen, Y.W., 2016. Independent component analysis of space-time patterns of groundwater system. In: Frontier Computing. Springer, pp. 503–514. http://dx.doi.org/10.1007/978-981-10-0539-8_50.

Huang, N.E., Shen, Z., Long, S.R., Wu, M.C., Shih, H.H., Zheng, Q., Yen, N.-C., Tung, C.C., Liu, H.H., 1998. The empirical mode decomposition and the Hilbert spectrum for nonlinear and non-stationary time series analysis. Proc. R. Soc. Lond. Ser. A Math. Phys. Eng. Sci. 454 (1971), 903–995. http://dx.doi.org/10.1098/rspa.1998.0193.

Huang, N.E., Wu, Z., 2008. A review on Hilbert-Huang transform: Method and its applications to geophysical studies. Rev. Geophys. 46 (2), http://dx.doi.org/10.1029/2007RG000228.

Hurr, R.T., Litke, D.W., 1990. Estimating Pumping Time and Ground-Water Withdrawals using Energy-Consumption Data, Vol. 89, No. 4107. Department of the Interior, US Geological Survey.

Johnson, T.C., Slater, L.D., Ntarlagiannis, D., Day-Lewis, F.D., Elwaseif, M., 2012. Monitoring groundwater-surface water interaction using time-series and time-frequency analysis of transient three-dimensional electrical resistivity changes. Water Resour. Res. 48 (7), http://dx.doi.org/10.1029/2012WR011893.

Kaiser, H.F., 1958. The varimax criterion for analytic rotation in factor analysis. Psychometrika 23 (3), 187–200. http://dx.doi.org/10.1007/BF02289233.

Karl, T.R., Koscielny, A.J., Diaz, H.F., 1982. Potential errors in the application of principal component (eigenvector) analysis to geophysical data. J. Appl. Meteorol. 21 (8), 1183–1186.

Keir, G., Bulovic, N., McIntyre, N., 2019. Stochastic modeling of groundwater extractions over a data-sparse region of Australia. Groundwater 57 (1), 97–109. http://dx.doi.org/10.1111/gwat.12658.

Kruseman, G.P., De Ridder, N.A., Verweij, J.M., 1970. Analysis and Evaluation of Pumping Test Data, Vol. 11. International Institute for Land Reclamation and Improvement Wageningen, The Netherlands.

Leduc, C., Bromley, J., Schroeter, P., 1997. Water table fluctuation and recharge in semi-arid climate: some results of the HAPEX-Sahel hydrodynamic survey (Niger). J. Hydrol. 188, 123–138. http://dx.doi.org/10.1016/S0022-1694(96)03156-3.

Lin, Y.-C., Chang, T.-J., Lu, M.-M., Yu, H.-L., 2015. A space-time typhoon trajectories analysis in the vicinity of Taiwan. Stoch. Environ. Res. Risk Assess. 29 (7), 1857–1866. http://dx.doi.org/10.1007/s00477-014-1001-5.

Lin, H.-T., Ke, K.-Y., Tan, Y.-C., Wu, S.-C., Hsu, G., Chen, P.-C., Fang, S.-T., 2013. Estimating pumping rates and identifying potential recharge zones for groundwater management in multi-aquifers system. Water Resour. Manag. 27 (9), 3293–3306. http://dx.doi.org/10.1007/s11269-013-0347-7.

Liu, H.-J., Hsu, N.-S., Yeh, W.W.-G., 2015. Independent component analysis for characterization and quantification of regional groundwater pumping. J. Hydrol. 527, 505–516. http://dx.doi.org/10.1016/j.jhydrol.2015.05.013.

Llamas, M.R., Martínez-Santos, P., 2005. Intensive Groundwater Use: Silent Revolution and Potential Source of Social Conflicts. American Society of Civil Engineers.

Long, A.J., Konrad, C.P., 2020. Spectral Analysis to Quantify the Response of Groundwater Levels to Precipitation—Northwestern United States. Technical Report, US Geological Survey.

Longuevergne, L., Florsch, N., Elsass, P., 2007. Extracting coherent regional information from local measurements with Karhunen-Loève transform: Case study of an alluvial aquifer (Rhine valley, France and Germany). Water Resour. Res. 43 (4), http://dx.doi.org/10.1029/2006WR005000.

Maréchal, J.-C., Dewandel, B., Ahmed, S., Galeazzi, L., Zaidi, F.K., 2006. Combined estimation of specific yield and natural recharge in a semi-arid groundwater basin with irrigated agriculture. J. Hydrol. 329 (1–2), 281–293. http://dx.doi.org/10.1016/j.jhydrol.2006.02.022.

Martínez-Santos, P., Martínez-Alfaro, P., 2010. Estimating groundwater withdrawals in areas of intensive agricultural pumping in central Spain. Agricult. Water Manag. 98 (1), 172–181. http://dx.doi.org/10.1016/j.agwat.2010.08.011.

Molle, F., Closas, A., 2020. Groundwater licensing and its challenges. Hydrogeol. J. 28 (6), 1961–1974. http://dx.doi.org/10.1007/s10040-020-02179-x.

Moon, S.-K., Woo, N.C., Lee, K.S., 2004. Statistical analysis of hydrographs and water-table fluctuation to estimate groundwater recharge. J. Hydrol. 292 (1–4), 198–209. http://dx.doi.org/10.1016/j.jhydrol.2003.12.030.

Nourani, V., Ghasemzade, M., Mehr, A.D., Sharghi, E., 2019. Investigating the effect of hydroclimatological variables on Urmia Lake water level using wavelet coherence measure. J. Water Clim. Chang. 10 (1), 13–29. http://dx.doi.org/10.2166/wcc.2018.261.

Page, R.M., Lischeid, G., Epting, J., Huggenberger, P., 2012. Principal component analysis of time series for identifying indicator variables for riverine groundwater extraction management. J. Hydrol. 432, 137–144. http://dx.doi.org/10.1016/j.jhydrol.2012.02.025.

Pearson, K., 1901. LIII. On lines and planes of closest fit to systems of points in space. Lond. Edinb. Dubl. Philos. Mag. J. Sci. 2 (11), 559–572. http://dx.doi.org/10.1080/14786440109462720.

Ross, A., Martinez-Santos, P., 2010. The challenge of groundwater governance: case studies from Spain and Australia. Reg. Environ. Chang. 10 (4), 299–310. http://dx.doi.org/10.1007/s10113-009-0086-8.

Shakoor, A., Arshad, M., Ahmad, R., Khan, Z.M., Qamar, U., Farid, H.U., Sultan, M., Ahmad, F., 2018. Development of groundwater flow model (MODFLOW) to simulate the escalating groundwater pumping in the Punjab, Pakistan. Pakistan J. Agric. Sci. 55 (3), http://dx.doi.org/10.21162/PAKJAS/18.4909.

Shih, D.-F., Lin, G.-F., 2002. Spectral analysis of water level fluctuations in aquifers. Stoch. Environ. Res. Risk Assess. 16 (5), 374–398. http://dx.doi.org/10.1007/s00477-002-0106-4.

Tsai, J.-P., Chang, L.-C., Chang, P.-Y., Lin, Y.-C., Chen, Y.-C., Wu, M.-T., Yu, H.-L., 2017. Spatial-temporal pattern recognition of groundwater head variations for recharge zone identification. J. Hydrol. 549, 351–362. http://dx.doi.org/10.1016/j.jhydrol.2017.03.047.

Tsai, J.-P., Hsiao, C.-T., 2020. Spatiotemporal analysis of the groundwater head variation caused by natural stimuli using independent component analysis and continuous wavelet transform. J. Hydrol. 590, 125405. http://dx.doi.org/10.1016/j.jhydrol.2020.125405.

Tsanis, I., Apostolaki, M., 2009. Estimating groundwater withdrawal in poorly gauged agricultural basins. Water Resour. Manag. 23 (6), 1097–1123. http://dx.doi.org/10.1007/s11269-008-9317-x.

Wada, Y., Wisser, D., Bierkens, M.F., 2014. Global modeling of withdrawal, allocation and consumptive use of surface water and groundwater resources. Earth Syst. Dyn. 5 (1), 15–40. http://dx.doi.org/10.5194/esd-5-15-2014.

Wang, J., Liu, W., Zhang, S., 2019. An approach to eliminating end effects of EMD through mirror extension coupled with support vector machine method. Pers. Ubiquitous Comput. 23 (3), 443–452. http://dx.doi.org/10.1007/s00779-018-01198-6.

Yu, H.-L., Chu, H.-J., 2010. Understanding space–time patterns of groundwater system by empirical orthogonal functions: a case study in the Choshui River alluvial fan, Taiwan. J. Hydrol. 381 (3–4), 239–247. http://dx.doi.org/10.1016/j.jhydrol.2009.11.046.

Yu, H.-L., Chu, H.-J., 2012. Recharge signal identification based on groundwater level observations. Environ. Monit. Assess. 184 (10), 5971–5982. http://dx.doi.org/10.1007/s10661-011-2394-y.

Yu, H.-L., Lin, Y.-C., 2015. Analysis of space–time non-stationary patterns of rainfall–groundwater interactions by integrating empirical orthogonal function and cross wavelet transform methods. J. Hydrol. 525, 585–597. http://dx.doi.org/10.1016/j.jhydrol.2015.03.057.