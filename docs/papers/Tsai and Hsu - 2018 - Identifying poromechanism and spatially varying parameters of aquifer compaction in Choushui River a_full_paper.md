# Identifying poromechanism and spatially varying parameters of aquifer compaction in Choushui River alluvial fan, Taiwan

Ming-Shiou Tsai, Kuo-Chin Hsu\*

Department of Resources Engineering, National Cheng Kung University, No. 1 University Road, Tainan 70101, Taiwan

\*Corresponding author.

E-mail addresses: dandandanz@hotmail.com.tw (M.-S. Tsai), kchsu@mail.ncku.edu.tw (K.-C. Hsu).

---

**Keywords:** Subsidence; Aquifer compaction; Visco-elasto-plastic model; Poromechanics; Choushui River alluvial fan

## Abstract

Subsidence occurs in many alluvial depositional environments, causing substantial socio-economic losses. Thick aquifers with interbedding or lens-structured clay can contribute significantly to compaction. The poromechanism of aquifer compaction is usually complicated, and its spatial variation is poorly understood, inhibiting our ability to fully explain the region-wide nature of groundwater-exploitation-induced land subsidence. In this study, we explore the poromechanism of aquifer deformation in the Choushui River alluvial fan, Taiwan. Groundwater level and multi-layer compaction data were collected for analyses. Elastic, plastic, and viscous characteristics all appear in the deformation data to various extents. A visco-elasto-plastic (VEP) model composed of a visco-elastic set and a visco-plastic set in series, which are associated with different viscous dampers, is proposed to model the deformation. Compared with existing models, the proposed model is superior in terms of simulating compaction as well as its applicability and versatility. The proposed VEP model is applied to observation wells in the proximal, middle, and distal fans of the Choushui River alluvial fan to explore the spatial variation in the poromechanical properties. The results show that the Young's modulus of the elastic spring increases with depth and with the distance from the distal fan to the proximal fan. The Young's modulus of the plastic element decreases with depth. The system response factor of the visco-plastic set decreases with depth and with the distance from the distal fan to the proximal fan. Aquifer recovery incapability increases with depth. Both the trend and dynamic fluctuations in compaction for the Choushui River alluvial fan are well captured by the proposed VEP model, which is essential for assessing long-term land and water resource management and evaluating potential short-term threats to infrastructure caused by seasonal subsidence.

## 1. Introduction

Land subsidence refers to the motion of the Earth's surface as it shifts downward relative to a datum. It can be caused naturally or anthropogenically. Natural subsidence may be due to the dissolution of limestone in karst terrains (Amin and Bankher, 1997), changes in geological structure caused by volcanic eruptions (Abidin et al., 2009), earthquakes (Chini et al., 2008), or fault activity (Rubin, 1992). Anthropogenic subsidence may be caused by the collapse of abandoned mines (Oh and Lee, 2010), deformation of the soil structure caused by surface or underground construction (Liu and Du, 2014; Shen et al., 2006), or extraction of subsurface fluids, such as water, gas, and oil (Jacob, 1940). Subsidence induced by groundwater exploitation is the most common and has a huge social cost.

Groundwater has long been used as an alternative fresh water source. Dramatic increases in water demand have been caused by rapid population growth, substantial expansion of cultivation, and rapid development of industry. Groundwater has become increasingly used due to its high reliability. However, the overpumping of groundwater has led to subsidence in many alluvial depositional environments worldwide, as reviewed by Hu et al. (2004), including those in Taiwan (Hung et al., 2010).

The most serious land subsidence in Taiwan is in the Choushui River alluvial fan (CSRAF). The area of land with significant subsidence (> 3 cm/year in 2015) is 309.1 km² (Water Resources Agency, 2015). Land subsidence is accompanied by seawater encroachment, inundation, soil salinity, infrastructure damage, and a reduction in the fresh water supply, all of which have caused serious property damage and economic losses (Hsu et al., 2015). Public concern about the safety of infrastructures affected by subsidence has increased in Taiwan, especially because the high-speed railway passes through an area with serious subsidence.

Monitoring systems for aquifer compaction, land subsidence, and groundwater level variation have been installed in the CSRAF. Leveling surveys are routinely performed. GPS stations, multi-depth compaction monitoring wells, and groundwater monitoring wells have been installed. The leveling survey and GPS station data are used to monitor the total subsidence from the land surface, and the multi-depth compaction monitoring well provides compaction data at various depths. However, despite extensive data collection, subsidence mitigation and prevention are still a challenge due to a lack of an understanding of the subsidence mechanism.

The compaction of a geological formation due to groundwater extraction can be explained by the fluid flow and poromechanism in porous media. The theory of fluid flow in porous media has evolved from the macroscopic averaged model (Bear, 1972) to the two-phase mass flow model (Vazquez, 2007; Pudasaini, 2016). Research on solid–fluid interaction has developed from the decoupled model (Terzghi, 1923) to coupled models (Verruijt, 1969; Wang, 2000; Coussy, 2004; Cheng, 2016). Subsidence can be modeled with groundwater flow using coupled or decoupled hydro-mechanical modeling. In decoupled modeling, flow is modeled first, and then deformation is calculated. A mechanical model is needed in the modeling to link the change in pore water pressure and deformation. Terzghi (1923) considered the change in pore structure as the only source of deformation. The concept of effective stress states that total stress is composed of the effective stress of the soil skeleton and the pore water pressure. Deformation can be modeled using a poromechanism that links the effective stress and deformation. In coupled modeling, flow and deformation are modeled simultaneously. Biot's poroelastic theory (Biot, 1955) is commonly used for such modeling. A constitutive model for the effective stress and deformation is also needed in the modeling. Therefore, a physics-based and site-specific constitutive model is essential for both coupled and decoupled modeling to acquire accurate deformation estimation. Since horizontal displacement is usually not as significant as vertical displacement in most subsidence areas, a model with three-dimensional flow and one-dimensional (vertical) deformation is commonly considered for subsidence to simplify analysis (Wu et al., 2010; Lin et al., 2015).

To appropriately estimate land subsidence in the CSRAF, the mechanical features of the aquifer system must be clarified. This can be accomplished using laboratory tests on soil specimens. However, the results of small-scale laboratory tests may not represent the field-scale mechanical features (Zhang et al., 2007). Therefore, the poromechanical features should be analyzed using field data. Poland et al. (1975), Helm (1976), Burbey (2001), and Liu et al. (2004) analyzed the relationship between changes in groundwater level and compression variation based on field data to clarify the stress-strain behavior of aquifer systems.

Studies show that soil deformation may be complicated in situ. Xue et al. (2005) and Shi et al. (2008) indicated that different geological units with the same hydrostratigraphy may exhibit different mechanical features. In addition, a single geological unit may exhibit elasticity, elasto-plasticity, or visco-elasto-plasticity in different periods (Zhang et al., 2012). Because the stress-strain relationship may be complicated in a stratum, the use of the classical elastic model alone for field data is questionable. More sophisticated poromechanical constitutive models have thus been proposed. Gambolati and Freeze (1973) and Neuman et al. (1982) developed an elasto-plastic model that has two compressibilities to represent over-consolidated and normally consolidated soils, respectively. The status of consolidation is determined based on whether the effective stress exceeds the preconsolidation stress. As a result of the breakdown of soil structure, the deformation of soil may display time-dependent features. Wu et al. (2010) proposed visco-elasto-plastic (VEP) models that consider elasticity, plasticity, and viscosity in the deformation of a stratum.

Poromechanical characterization of the CSRAF has been attempted (Liu et al., 2004; Hung et al., 2012). Tsai (2009) analyzed the effect of viscosity on the aquifer system. Tsai (2015) proposed a coupled one-dimensional VEP model with two viscous dampers with the same viscosity for aquitard consolidation. The model clearly characterized the deformation of the tested soil. Hung et al. (2012) analyzed the relationship between groundwater level and strain for soil deformation in the CSRAF. Long-term inelastic trends and temporary elastic behavior were found. Previous research has shown that modeling is applicable to the evaluation of subsidence in the CSRAF. However, the spatial characteristics of the poromechanical properties of the CSRAF have not been systematically explored, which hinders the understanding of the subsidence mechanism and prevents improvements in regional-scale subsidence modeling. The purpose of the present study is to explore the poromechanism in the CSRAF using field data. Based on field observations, a VEP model is proposed to model the deformation in situ. The modeling results are compared to those obtained using existing poromechanical models.

## 2. Methodology

Deformation is caused by a change in the effective stress applied to the soil skeleton. Based on the principle of effective stress, a decrease in pore water pressure results in an increase in effective stress, and vice versa, for an unchanged or slightly changed level of total stress (overburden pressure). The variations in groundwater level $\Delta h$ responses to changes in pore water pressure $\Delta p$ can be expressed as $\Delta p = \rho g \Delta h$ for constant density and gravity. Therefore, a change in the groundwater level (pore water pressure) of a formation reflects a corresponding change in effective stress and can be related to deformation through a poromechanism.

A poromechanism can be described with a constitutive equation, which is a mathematical relation between stress and strain. To define such mathematical relations, coefficients that are specific to a material or to a composite material, known as material constants, are required. Commonly used poromechanical models are introduced below.

### 2.1. Elastic model

The elastic (EL) model is the simplest and most popular model for describing a stress and strain relation that follows Hooke's law (Truesdell, 1960; Cheng, 2016). The EL model has the following constitutive equation:

$$\sigma = E \varepsilon, \tag{1}$$

where $\sigma$ is the effective stress, $\varepsilon$ is the strain, and $E$ is Young's modulus or the modulus of elasticity. The EL model can be described as an elastic spring.

### 2.2. Elasto-plastic model

The elasto-plastic (EP) model accounts for rebound and permanent deformation when loading is removed. The geological medium undergoes normal consolidation when the effective stress is greater than the maximum effective stress experienced by soil in the past, i.e., the preconsolidation stress, $\sigma_p$, and undergoes over-consolidation when the effective stress is less than $\sigma_p$. The EP model can be described as a single nonlinear spring with different elastic moduli for normal consolidation and over-consolidation (Neuman et al., 1982; Shi et al., 2008). The EP model can also be constructed using spring and plastic elements (Zhang et al., 2012). The EP model consists of one spring element and one plastic unit in series, as shown in Fig. 1(a). The plastic unit comprises a plastic spring and a bypass in parallel, and the loop is controlled by a single-pole double-throw (SPDT) switch. The spring element and plastic element are denoted as $S$ and $P$, with elastic modulus $E_e$ and plastic modulus $E_p$, respectively.

The total strain of the EP model, $\varepsilon_{\text{total}}$, is the sum of the elastic strain, $\varepsilon_e$, and the plastic strain, $\varepsilon_p$, from the elastic spring and plastic unit, respectively. When the effective stress is smaller than $\sigma_p$, the plastic element is bypassed. When the effective stress is greater than $\sigma_p$, the plastic spring is active. The constitutive law for normal consolidation can be written as:

$$\text{If } \sigma > \sigma_p, \quad \varepsilon_{\text{total}} = \frac{\sigma}{E_e} + \frac{\sigma - \sigma_p}{E_p} \tag{2}$$

The lumped modulus for normal consolidation is:

$$E_{\text{nor}} = \frac{E_e E_p}{E_e + E_p} \tag{3}$$

The constitutive law for over-consolidation is:

$$\text{If } \sigma < \sigma_p, \quad \varepsilon_{\text{total}} = \frac{\sigma}{E_e} \tag{4}$$

The lumped modulus for over-consolidation is:

$$E_{\text{over}} = E_e \tag{5}$$

The constructed EP model is equal to the nonlinear spring model, with $E_{\text{over}}$ being greater than $E_{\text{nor}}$, which is consistent with the experimental result where the compression index is larger than the swelling index (Neuman et al., 1982). The model is slightly different from that of Zhang et al. (2012), in that when $\sigma > \sigma_p$, $\sigma$ and $\sigma - \sigma_p$ are applied to the plastic element for the present model and that of Zhang et al. (2012), respectively.

### 2.3. Visco-elastic model

The visco-elastic (VE) model combines the elastic model and the viscous model (Terzopoulos and Fleischer, 1988; Roylance, 2001) to include the creep effect. The characteristics of the VE model can be described using elastic springs and viscous dampers. The elastic spring exhibits a linear relationship between stress and strain (Hooke's law), and the viscous damper obeys a linear relationship between stress and the rate of strain (Ferry, 1980):

$$\sigma = \eta \frac{d\varepsilon}{dt} \tag{6}$$

where $\eta$ is the viscosity of the viscous damper. When the stress is removed, the EL model immediately rebounds to its original state, whereas the VE model exhibits prolonged strain.

Constitutive equations for VE models with springs and dampers arranged in various forms have been proposed. The Kelvin-Voigt model has been shown to be appropriate for describing the creep of soil (Vincent, 2012). This model and its modified versions have been applied to model subsidence (Tsai, 2009).

The Kelvin-Voigt model is composed of an elastic spring with an elastic modulus $E$ and a damper with viscosity $\eta$ in parallel. The total excess stress $\sigma_{\text{total}}$ is the sum of the stress applied to the elastic spring and that applied to the viscous damper. The constitutive equation of the Kelvin-Voigt model for a constant loading $\sigma_0$ is:

$$\varepsilon(t) = \frac{\sigma_0}{E} \left[1 - \exp\left(-\frac{E}{\eta} t\right)\right] \tag{7}$$

The maximum strain of the VE model is constrained by the elastic spring. The strain reaches its asymptotic value with a rate that depends on the ratio of the Young's modulus of the spring and the viscosity of the damper $\frac{E}{\eta}$, which is defined as the system response factor (SRF). A greater SRF indicates a faster response of strain to its asymptotic value, $\frac{\sigma_0}{E}$.

When the constant stress is removed at time $t_1$, strain recovers as:

$$\varepsilon(t) = \varepsilon(t_1) \exp\left[-\frac{E}{\eta} (t - t_1)\right] \quad \text{for } t \geq t_1 \tag{8}$$

### 2.4. Visco-elasto-plastic model

The visco-elasto-plastic (VEP) model is composed of elastic springs, plastic springs, and viscous dampers. There are various forms of the VEP model. Tsai (2015) constructed a VEP model composed of an elastic-plastic unit and a viscous damper in parallel to simulate the land subsidence of an aquifer-aquitard system in Taiwan. This model is referred to as VEP1 in a later comparison. VEP1, shown in Fig. 1(b), has a total of three elements: one spring, one plastic element, and one damper.

The Merchant model (referred to as VEP2) is composed of two poromechanical sets in series, as shown in Fig. 1(c). The first set (set A) is an elasto-plastic unit composed of an elastic spring and a plastic element in series. The second set is composed of an elasto-plastic unit and a viscous damper in parallel. VEP2 has a total of five elements: two springs, two plastic elements, and one damper. The VEP2 model has been applied to simulate land subsidence in the Yangtse Delta (Wu et al., 2010; Shi et al., 2008; Ye et al., 2012). Since VEP2 is more complicated than VEP1 and is more difficult to apply in practice, only VEP1 is used in the model comparison.

### 2.5. Proposed VEP model

To account for the elasticity, plasticity, and short- and long-term damper effects in the compaction of the CSRAF (see Section 3.2), a new VEP model is proposed here. The proposed model considers two poromechanical sets in series, as shown in Fig. 1(d). The first set is a visco-elastic model composed of an elastic spring and a viscous damper in parallel. The second set is a visco-plastic model composed of a plastic element and a viscous damper in parallel. The dampers in the visco-elastic set and the visco-plastic set are associated with different viscosities. The SPDT switch controls whether the second set is bypassed.

* **Fig. 1.** Schematic diagrams of (a) elasto-plastic model, (b) VEP1 model, (c) VEP2 model, and (d) proposed VEP model.*

The total strain, $\varepsilon_{\text{total}}$, is the sum of the strain of the visco-elastic set and that of the visco-plastic set. For a constant loading stress $\sigma_0$ in the creep test, the stress-strain-time relation of the proposed VEP model can be expressed as:

$$\text{If } \sigma > \sigma_p, \quad \varepsilon(t) = \frac{\sigma_0}{E_e} \left[1 - \exp\left(-\frac{E_e}{\eta_e} t\right)\right] + \frac{\sigma_0}{E_p} \left[1 - \exp\left(-\frac{E_p}{\eta_p} t\right)\right] \tag{9a}$$

$$\text{If } \sigma < \sigma_p, \quad \varepsilon(t) = \frac{\sigma_0}{E_e} \left[1 - \exp\left(-\frac{E_e}{\eta_e} t\right)\right] \tag{9b}$$

where $E_e$ and $E_p$ are the elastic and plastic moduli of the elastic spring and plastic element, respectively. $\eta_e$ and $\eta_p$ are the viscosities of the damper associated with the visco-elastic and visco-plastic sets, respectively.

When the constant stress is removed at time $t_1$, the strain is the sum of recoverable visco-elastic strain and irrecoverable visco-plastic strain:

$$\varepsilon(t) = \varepsilon(t_1) \exp\left[-\frac{E_e}{\eta_e} (t - t_1)\right] + \frac{\sigma_0}{E_p} \left[1 - \exp\left(-\frac{E_p}{\eta_p} t_1\right)\right] \quad \text{for } t \geq t_1 \tag{10}$$

when the viscosity of the damper is set to be infinitely small, the function of the damper is inactive in both the visco-elastic set and the visco-plastic set. The elastic and plastic deformation functions become inactive if the viscosity of the damper is set to be very large. Therefore, elastic, elasto-plastic, visco-elastic, visco-plastic and visco-elasto-plastic deformation can be modeled using the proposed VEP model.

### 2.6. Convolution

The strain at time $t$ due to a time-varying stress is the sum of the strain caused by individual stresses that occurred prior to the observation time, as obtained by convolution:

$$\varepsilon(t) = \int_0^t C(t - \tau) \dot{\sigma}(\tau) d\tau, \tag{11}$$

where $C(t)$ is the constitutive function of the used poromechanical model with $\sigma_0 = 1$, and $\dot{\sigma}(\tau)$ is the rate of the applied time-varying stress function. By applying the concept of effective stress, $\sigma(\tau)$ is the change in pore water pressure $\rho g \Delta h$ for a constant total stress.

## 3. Study area and data

### 3.1. Study area

The CSRAF is located in central Taiwan, as shown in Fig. 2. The elevation of the alluvial fan changes from 0 to 100 m within 40 km from the coast to the foothills. The Wu River is in the north and the Beigang River is in the south. The Baguashan Tableland and Douliou Hill are in the east. The area is approximately 1800 km².

The CSRAF consists of Holocene unconsolidated sediments composed of gravel, sand, silt, and clay (Chiang et al., 1999). The porosity of the stratum is great, and the skeleton is loose (Liu and Du, 2014). The hydrogeology of cross section A-A' is shown in Fig. 3. Four aquifers and three aquitards are recognized in the alluvial fan. Interbedding clay and lens-structured mud or clay in these aquifers are common (Liu et al., 2004). Each aquifer is treated as a lumped homogeneous system with representative poromechanical properties.

In the 1970s, water consumption rapidly increased in Taiwan with the growth of aquaculture, agriculture, and industrial development. Since surface water cannot satisfy the water demand due to water pollution, groundwater has become the most important alternative fresh water source. However, over-extraction of groundwater has resulted in a large area with severe land subsidence. To mitigate this problem, restrictions on groundwater exploitation are enforced in the subsidence area. The cultivation of drought-resistant crops and brackish water aquaculture are encouraged. The yearly changes in severe-subsidence areas (subsidence rate > 3 cm/year) in Yunlin and Changhua counties for the period 1993–2014 are shown in Fig. 4. Land subsidence in Changhua County seems to be under control but that in Yunlin County continues and becomes severe in drought years.

### 3.2. Deformation characteristics of CSRAF

The CSRAF is a clastic sedimentary depositional system that includes three aquitards and four aquifers. An aquitard is primarily composed of fine grains with high compressibility and is commonly considered to contribute more to strata deformation than an aquifer does (Leaks and Galloway, 2010). However, interbedding or lens-structured clay in the thick aquifer unit is common in the CSRAF, making these aquifers contribute more to subsidence (Liu et al., 2004).

* **Table 1:** Cumulative compaction in period 1995–2014 at Boltz Station.*

The contributions of aquifers 2–2 and 3 to the total cumulative compaction are 40.2% and 28.4%, respectively (Table 1), which indicates that the subsidence in the CSRAF is mainly due to the deformation of the aquifers.

The groundwater level and land subsidence data for the CSRAF do not seem to show a simple elastic response, in which the changes in stress and strain vary synchronously (Galloway et al., 1999; Burbey, 2006). Fig. 5(a) and (b) show time variations in the groundwater level and cumulative compression, respectively, from 1995 to 2014 for the observation interval 116–146 m at aquifer 2–2, which is between 80 and 149.9 m above seawater level at Boltz Station. Fig. 5(c) plots the groundwater level versus cumulative compaction. The rises and falls in the groundwater level are marked by symbols. Deformation features can be seen in Fig. 5. First, similar slopes with a slight delay in the cumulative compaction for the periodic groundwater level fall following a rise are shown in Fig. 5(c). This indicates that elastic and viscous effects must be considered for the short-term compaction mechanism. Second, although the groundwater level oscillates and recovers annually in the 20-year record, permanent deformation continues to evolve, and the strain never recovers to its initial value, as shown in Fig. 5(c). The deformation did not recover even when the two highest groundwater levels were reached (points A and B in Fig. 5(c)). This prolonged, unrecovered deformation indicates that the plastic and creep behavior must be considered in the long-term compaction mechanism. The deformation of aquifer 2–2 at Boltz Station is thus complicated. Elasticity, plasticity, and viscosity all appear in the data. Different creep effects are associated with both elastic and inelastic responses.

### 3.3. Data used for analysis

Groundwater level and settlement data were collected. Pairs comprising a groundwater monitoring well and a multi-layer compaction monitoring well at a given location were chosen. The Boltz, Tianyang, and Huwei groundwater monitoring wells were used to represent the distal, middle, and proximal fans, respectively. The corresponding multi-layer compaction monitoring stations are located at Jianyang Elementary School, Longyan Elementary School, and Huwei Elementary School, respectively. The locations of the groundwater level monitoring wells and multiple-layer compaction stations are shown in Fig. 2.

Groundwater level data are available for aquifer 1 (F1), aquifer 2 (F2), and aquifer 3 (F3) at Boltz Station, for F1, F2, and aquifer 4 (F4) at Tianyang Station, and for F2 only at Huwei Station. Groundwater level variations for January 1, 1995, to June 31, 2015, are shown in Fig. 6(a), (b), and (c), for the Boltz, Tianyang, and Huwei stations, respectively. At Boltz Station, almost no time lag appears in the groundwater level variation time series for the three aquifers. The variation in the groundwater level at shallow layer F1 is smaller than those at F2 and F3, which are very similar. This may be explained by the fact that F1 is replenished by natural recharge from precipitation and thus has smaller variations. There is a weak aquitard between F2 and F3, leading to the simultaneous responses of F2 and F3. At Tianyang Station, the groundwater level variation at F1 is minimal. The variation in the groundwater level at F4 is slightly slower and smaller than that at F2. There is only one observation well at Huwei Station. The annual variation is clear. Very low groundwater levels appear in 2011 and 2015 due to severe droughts. Compaction data corresponding to the Boltz, Tianyang, and Huwei groundwater wells from the multi-layer compaction monitoring stations at the elementary schools (see above) are shown in Fig. 7(a), (b), and (c), respectively. The compaction data are missing for the period from March 2012 to March, 2014 for all stations. In the distal fan (Jianyang Elementary School), increasing trends are shown for the F1, F2, and F3 aquifers. The compaction of F1 ceases to increase after 2002 whereas those for F2 and F3 continuously increase even when the groundwater level recovers. The compaction rates of F2 and F3 are similar. In the middle fan (Longyan Elementary School), compaction does not significantly increase for F1, whereas those for F2 and F4 continue to increase even when the groundwater level recovers. The compaction in F2 is greater than that in F4. In the proximal fan (Huwei Elementary School), compaction continues to increase for F2.

For model construction, the first half of the cumulative deformation data is used to calibrate the poromechanical parameters. The other half is used to verify the models. The calibration period and the verification period for the different stations are shown in Table 2. The optimization toolbox in Matrix Laboratory software (Matlab R2015a) is applied to estimate the poromechanical parameters using the `lsqcurvefit` model, which utilizes the trust region method (Coleman and Li, 1996) to solve nonlinear curve-fitting problems by comparing least-square errors. For the proposed VEP model, $\sigma_p$, $E_e$, $E_p$, $\eta_e$, and $\eta_p$ are the target parameters to be inversed.

* **Table 2:** Data periods for model calibration and verification.*

## 4. Results and discussion

### 4.1. Model comparison at Boltz station

Boltz Station is selected to compare the effectiveness of different models because the observation period at Boltz Station is the longest among the three stations, allowing for long-term historical compaction variations. In addition, the groundwater wells at Boltz Station provide groundwater pressure for three different aquifers. Also, using the compaction data from nearby Jianyang Elementary School and the groundwater level at Boltz Station facilitates the analysis of aquifer compaction induced by groundwater extraction.

Comparisons of the observed and simulated cumulative deformations for five models, the EL model, the EP model, the VE model, the VEP1 model, and the proposed VEP model, for aquifer 1 at Boltz Station are shown in Fig. 8(a). The measured cumulative deformation of aquifer 1 gradually increases in the period 1999–2004. After 2004, the cumulative deformation appears to fluctuate and does not significantly increase. The cumulative deformation of the EL model oscillates with variations in groundwater level but cannot simulate the gradual increase in deformation. The cumulative deformation of the EP model significantly increases when the groundwater level is lower than the historically lowest point, corresponding to the stress being larger than the preconsolidation stress. The lowest groundwater level appears on May 14, 2002; this resulted in the maximum cumulative deformation in the EP model. The cumulative deformation becomes stable and slightly oscillates with variations in the groundwater level after May 14, 2002. For the VE model, the cumulative deformation smoothly rises from 1999 to 2003. After 2003, the deformation partially recovers due to the recovery of the groundwater level. For the VEP1 model, cumulative subsidence smoothly increases from 1999 to 2003, which is similar to the results for the VE model. After 2003, the deformation does not recover because of plastic behavior. The proposed VEP model further improves the results. It captures not only the trend, but also the dynamic fluctuations. The cumulative deformation shows dynamic fluctuation with variations in groundwater for the entire modeling period, and a gradually increasing trend occurs before 2004. The groundwater level rises after 2004, but the cumulative deformation ceases to increase; dynamic fluctuations in deformation follow the groundwater variations. The visco-elastic set clearly captures the dynamic and recoverable fluctuations in deformation while the visco-plastic set can simulate irrecoverable and creep deformation. The average relative error (ARE) is used to quantify the deviation of the model results from the observed data. ARE is calculated as:

$$\text{ARE} = \frac{1}{n} \sum_{i=1}^{n} \left| \frac{s_i - \hat{s}_i}{s_i} \right|, \tag{12}$$

where $n$ is total number of monitoring points, and $s_i$ and $\hat{s}_i$ are the simulated and monitored cumulative compaction values, respectively, at data point $i$. The ARE values for the considered models are shown in Table 3. The proposed VEP model is superior to the other models, having the lowest ARE values (10.42% and 9.73% in model calibration and verification, respectively).

For aquifer 2 at Boltz Station, the monitored total cumulative deformation is significant, up to approximately 7 cm, from 1999 to 2014, as shown in Fig. 8(b). The time series of cumulative deformation shows an upward tendency, reaching an asymptotic value in about 2014. The EL and EP models do not capture this trend. The VE and VEP1 models capture this trend very well, showing smoothly increasing deformation. This can be attributed to the inclusion of a damper in these models. Unlike the VE and VEP1 models, the proposed VEP model not only captures the long-term trend of permanent deformation but also simulates the short-period fluctuation of recoverable deformation. The proposed VEP model has the smallest ARE (Table 3), thus outperforming the other models.

Fig. 8(c) shows the observed and simulated cumulative deformations versus time for aquifer 3 at Boltz Station. The deformation of aquifer 3 shows an increasing trend in the observed data. The total cumulative deformation is 5 cm from 1999 to 2014. The EL model only shows the oscillation of the seasonal deformation. The EP model shows significant deformation when the groundwater level is lower than the historically lowest point. The VE and VEP1 models clearly capture the gradually increasing trend. The proposed VEP model captures both the seasonal variation and the increasing trend in deformation. Table 3 shows that the proposed VEP model has the smallest ARE among the considered models for both calibration and verification.

The results indicate that the EL and EP models cannot properly simulate creep deformation. The VE and VEP1 models with one damper can simulate the long-term trend in compaction but not the instantaneous elastic deformation. The visco-elastic set of the proposed VEP model captures the dynamic and recoverable fluctuation well while the visco-plastic set can simulate long-term irrecoverable deformation. The proposed VEP model thus best simulates the measurement data for Boltz Station.

* **Table 3:** ARE values at Boltz Station for various models.*

### 4.2. Spatial distribution of poromechanical properties in CSRAF

The hydrogeological properties vary spatially and are heterogeneous on various scales. The spatial variations in the poromechanical properties in the CSRAF are poorly constrained, inhibiting our ability to simulate subsidence in the fan. Although laboratory tests on mechanical features have been attempted (Liu and Du, 2014), their representation at the field scale is questionable because the geometric size of laboratory samples is much smaller than that at field scale. To characterize the field-scale poromechanical properties, the groundwater level and deformation data are analyzed using the proposed VEP model, which was shown to be the best model in the previous section. The Boltz, Tianyang, and Huwei stations are used for the distal, mid, and proximal areas of the CSRAF, respectively.

The observed and simulated cumulative deformations of aquifer 1 at Tianyang Station (mid fan) are shown in Fig. 9(a). There is a minor increase in compaction, and the cumulative compaction is < 0.4 cm from 2006 to 2015. The proposed VEP model captures the increasing trend but with a smaller variation in deformation. The average absolute errors are 0.057 and 0.072 cm for calibration and verification, respectively. The ARE values are shown in Table 4. The small observed compaction in the denomerator results in a large ARE. The observed and simulated cumulative deformations for aquifer 2 are shown in Fig. 9(b). The deformation shows an increasing trend. The total cumulative deformation reaches 4 cm in the period 2006–2015. The proposed VEP model captures the dynamic and long-term creeping deformation well. From Table 4, the ARE values of deformation are 19.0% and 3.4% for calibration and verification, respectively. Fig. 9(c) shows the cumulative deformation of aquifer 4 at Tianyang Station. The total cumulative deformation is approximately 1.8 cm in the period 2006–2015. Long-term irrecoverable deformation is well modeled. The ARE values of deformation are 8.38% and 9.79% for calibration and verification, respectively. The proposed VEP model can thus simulate the variations in deformation at Tianyang Station.

The cumulative deformation of aquifer 2 at Huwei Station (proximal fan) is shown in Fig. 10. An increasing trend appears in the cumulative deformation. Both the dynamic fluctuation and the deformation trend are captured by the proposed VEP model. The average absolute errors are small; 0.089 and 0.073 cm for calibration and verification, respectively. The ARE values are 27.68% and 7.69%, respectively, as shown in Table 4.

* **Table 4:** ARE values at Tianyang and Huwei stations for proposed VEP model.*

The Young's modulus values of the elastic and plastic models at the Boltz, Tianyang, and Huwei stations are compiled in Table 5. The Young's modulus estimated using the proposed VEP model is between 205 and 663 MPa. Obrzud and Truty (2012) showed that the typical value of Young's modulus for dense well-graded gravel or sand is 320 MPa, and Tsai (2015) found that the in situ Young's modulus of the CSRAF can be > 100 MPa. The results of the proposed VEP model are within the same order of magnitude of both experimental and field data. A high Young's modulus indicates a stiff material (more gravel or less clay), and a low value indicates a soft material (more clay). Table 5 shows that the Young's modulus of the elastic spring, $E_e$, decreases from the proximal fan (Huwei Station) to the distal fan (Boltz Station) in aquifer 2. The largest Young's modulus of the plastic spring, $E_p$, appears in the proximal fan. Both $E_e$ and $E_p$ decrease from the proximal fan to the mid fan for aquifer 2 and increase from the mid fan to the distal fan for aquifer 1.

Young's moduli at various depths of the distal fan (Boltz station) and the middle fan (Tianyang station) are also shown in Table 5. A deeper stratum is associated with a larger $E_e$, i.e., a denser material. In contrast, $E_p$ decreases with depth. This may be associated with the historical development of subsidence, where the upper layer deforms earlier and consolidates more, while the deep layer deforms later and has less consolidation.

* **Table 5:** Poromechanical parameters of proposed VEP model for Boltz, Tianyang, and Huwei stations.*

### 4.3. System responses to external loading

The system response factors of elasticity ($\text{SRF}_e$) and plasticity ($\text{SRF}_p$) indicate how fast the system responds to external loading for the elastic spring and the plastic spring, respectively. They are defined as:

$$\text{SRF}_e = \frac{E_e}{\eta_e}, \tag{13a}$$

$$\text{SRF}_p = \frac{E_p}{\eta_p}. \tag{13b}$$

A larger SRF is associated with a larger Young's modulus and a smaller damper viscosity. A large SRF results in a quick deformation response (i.e., the ultimate condition is quickly reached). The results show that $\text{SRF}_e$ is much larger than $\text{SRF}_p$. The viscous effect is less significant in the visco-elastic set for aquifers 1 and 3 at Boltz Station and aquifers 2 and 4 at Tianyang Station. It is more significant for aquifer 2 at Boltz Station, aquifer 1 at Tianyang Station, and aquifer 2 at Huwei Station. The visco-plastic set is the main contributor to the long-term increasing deformation trend. The poromechanical properties are not uniform and vary spatially.

Systematic change was found for $\text{SRF}_p$ but not for $\text{SRF}_e$. Generally, deeper aquifers have larger $\text{SRF}_e$. $\text{SRF}_p$ decreases with depth, as shown in Table 5. This indicates that a deeper aquifer has a faster elastic response to external loading while a shallow aquifer has a faster plastic response. This may be explained by the shallow aquifer (F1) having evolved to the plastic compaction more due to its longer groundwater use history. Pumping of the deeper aquifer started more recently, and thus the formation is in the early stages of compaction, showing elastic behavior caused by a variation in the groundwater level. The deep stratum has high potential for permanent compaction and thus will take a long time to complete the compaction process. Table 5 also shows that $\text{SRF}_p$ increases from the proximal fan (Huwei station) to the distal fan (Boltz Station) in aquifer 2.

### 4.4. Recovery incapabilities of aquifers

A ratio $m$ of the Young's modulus of over-consolidated soil to that of normally consolidated soil defines the recovery incapability of an aquifer:

$$m = \frac{E_{\text{over}}}{E_{\text{nor}}} = \frac{E_e + E_p}{E_p}. \tag{14}$$

A larger $m$ indicates more difficult compaction recovery. Table 5 shows that the $m$ value increases with depth; i.e., it is more difficult for a deeper aquifer to recover from being compacted. Therefore, compaction that occurs in a deep stratum recovers less, leading to permanent deformation.

### 4.5. Strengths and limitations of the proposed model

Different models are applied to model aquifer compaction caused by the change in pore water pressure in the CSRAF, Taiwan. A total of four poromechanical parameters are required in the proposed VEP model, making it simpler than the Merchant model (VEP2) but slightly more complicated than the VEP1 model. Neither VEP1 nor VEP2 models simple elastic deformation. The VEP1 model has been shown to be able to capture long-term subsidence characteristics well but not the dynamic fluctuations in compaction in the CSRAF. The VEP2 model has more parameters and thus requires more data, making it more difficult to apply in practice. The proposed VEP model is flexible and versatile in terms of modeling both long- and short-term compaction. This is important not only for assessments of long-term land and water resource use but also for potential short-term threats to infrastructure caused by seasonal subsidence.

## 5. Conclusion

A visco-elastic-plastic poromechanical model was proposed in this study. The model is composed of a visco-elastic set and a visco-plastic set in series. The two sets have elastic and plastic springs, respectively, and a damper in parallel. The visco-elastic set simulates dynamic and recoverable fluctuations in deformation while the visco-plastic set models long-term irrecoverable deformations. The proposed model was applied to Boltz Station in the CSRAF, Taiwan, and the results were compared to those obtained using existing poromechanical models. The proposed VEP model outperformed the other models in terms of ARE at all three aquifers. Both the trend and dynamic fluctuations in compaction were captured well using the proposed VEP model.

The proposed VEP model was then applied to stations at the proximal, mid, and distal fans of the CSRAF. In the distal fan (Boltz Station) and mid fan (Tianyang Station), the Young's modulus for the elastic spring $E_e$ increased and that for the plastic spring $E_p$ decreased with increasing stratum depth. $E_e$ decreased from the proximal fan to the distal fan in aquifer 2, showing that the stratum is more rigid in the proximal fan than in the distal fan. In the CSRAF, the system response factor of elasticity, $\text{SRF}_e$, is generally larger than that of plasticity, $\text{SRF}_p$, which indicates a smaller viscous effect in the visco-elastic set compared to that in the visco-plastic set in the proposed VEP model. $\text{SRF}_p$ was found to decrease with depth and to increase from the proximal fan to the distal fan. The recovery incapability of an aquifer ($m$) increases with depth. These results indicate a potentially permanent deformation and a longer response time at the proximal fan and in deeper aquifers. The hydrogeology of the CSRAF is complicated. The poromechanism in the CSRAF is essential for assessing long-term land and water resource management and evaluating potential short-term threats to infrastructure caused by seasonal subsidence.

## Acknowledgments

This research was supported in part by grants 105-2923-M-006-004-MY3, 105-2221-E-009-054-MY3, and 105-2116-M-006-015 from the Ministry of Science and Technology, R.O.C. The authors appreciate the assistance of Mr. Min-Hung Sung in preparing the figures. The authors gratefully acknowledge the constructive comments of the anonymous reviewers and the handling editor.

## References

Abidin, H.Z., Davies, R.J., Kusuma, M.A., Andreas, H., Deguchi, T., 2009. Subsidence and uplift of Sidoarjo (East Java) due to the eruption of the Lusi mud volcano (2006–present). Environ. Geol. 57 (4), 833–844.

Amin, A.A., Bankher, K.A., 1997. Karst hazard assessment of eastern Saudi Arabia. Nat. Hazards 15, 21–30.

Bear, J., 1972. Dynamics of Fluids in Porous Media. American Elsevier Publishing Company.

Biot, M.A., 1955. Theory of elasticity and consolidation for a porous anisotropic solid. J. Appl. Phys. 26, 182–185.

Burbey, T.J., 2001. Stress-strain analyses for aquifer-system characterization. Ground Water 39 (1), 128–136.

Burbey, T.J., 2006. Three-dimensional and strain induced by municipal pumping. Part 2: numerical analysis. J. Hydrol. 330, 422–424.

Cheng, A.H.-D., 2016. Poroelasticity. Springer.

Chiang, C.J., Lai, T.C., Lai, T.H., Hung, C.C., Fei, L.Y., Hou, C.S., Chen, J.E., Chen, L.C., Lu, S.Y., Chou, S.C., 1999. Hydrogeological Survey Report of Chosui River Watershed. Central Geological Survey, Taipei, Taiwan, pp. 129.

Chini, M., Bignami, C., Stramondo, S., Pierdicca, N., 2008. Uplift and subsidence due to the 26 December 2004 Indonesian earthquake detected by SAR data. Int. J. Remote Sens. 29 (13), 3891–3910.

Coleman, T.F., Li, Y., 1996. An interior, Trust Region approach for nonlinear minimization subject to bounds. SIAM J. Optimization 6, 418–445.

Coussy, O., 2004. Poromechanics. John Wiley & Sons.

Ferry, J.D., 1980. Viscoelastic Properties of Polymers, 3rd Edition. Wiley.

Galloway, D.L., Jones, D.R., Ingebritsen, S.E., 1999. Land subsidence in the United States. In: U.S. Geological Survey Circular. 1182. pp. 117.

Gambolati, G., Freeze, R.A., 1973. Mathematical simulation of the subsidence of Venice I theory. Water Resour. Res. 9, 721–733.

Helm, D.C., 1976. One-dimensional simulation of the aquifer-system compaction near Pixley, California, 2. Stress-dependent parameters. Water Resour. Res. 12, 375–391.

Hsu, W.C., Chang, H.C., Chang, K.T., Lin, E.K., Liu, J.K., Liou, Y.A., 2015. Observing land subsidence and revealing the factors that influence it using a multi-sensor approach in Yunlin county, Taiwan. Remote Sens. 7, 8202–8223.

Hu, R.L., Yue, Z.Q., Wang, L.C., Wang, S.J., 2004. Review on current status and challenging issues of land subsidence in China. Eng. Geol. 76 (1–2), 65–77.

Hung, W.C., Hwang, C.W., Chang, C.P., Yen, J.Y., Liu, C.H., Yang, W.H., 2010. Monitoring severe subsidence in Taiwan by multi-sensors: Yinlin, the south Choushui River Alluvial Fan. Earth Sci. Geol. 59, 1535–1548.

Hung, W.C., Hwang, C.W., Liou, J.C., Lin, Y.S., Yang, H.L., 2012. Modeling-aquifer-system compaction and predicting land subsidence in central Taiwan. Eng. Geol. 147-148, 78–90.

Jacob, C.E., 1940. On the flow of water in elastic artesian aquifer. Trans. AGU 21 (2), 574–586.

Leaks, S.A., Galloway, D.L., 2010. Use of the SUB-WT Package for Mud flow to Simulate Aquifer-System Compaction in Antelope Valley. 339. IAHS Publ, California, USA, pp. 61–67.

Lin, P.-L., Hsu, K.-C., Lin, C.-W., Hwung, H.-H., 2015. Modeling compaction of multi-layer-aquifer system due to groundwater withdrawal. Eng. Geol. 187, 143–155.

Liu, C.H., Du, F.L., 2014. The land subsidence behaviors and mechanisms in Taiwan. Sino-Geotech. Res. 139.

Liu, C.H., Pan, Y.W., Liao, J.J., Huang, C.T., Shoung, O., 2004. Characterization of land subsidence in the Choshui River alluvial fan, Taiwan. Environ. Geol. 45, 1154–1166.

Neuman, S.P., Preller, C., Narasimhan, T.N., 1982. Adaptive explicit-implicit quasi three-dimensional finite element model of flow and subsidence in multiaquifer system. Water Resour. Res. 18, 1151–1561.

Obrzud, R., Truty, A., 2012. The hardening soil model – a practical guidebook Z soil. In: PC 100701 report.

Oh, H.J., Lee, S., 2010. Assessment of ground subsidence using GIS and the weights-of-evidence model. Eng. Geol. 115, 36–48.

Poland, J.F., Lofgren, B.E., Ireland, R.L., Pugh, R.G., 1975. Land subsidence in the San Joaquin Valley as of 1972. In: USGS Professional Paper, 437-H.

Pudasaini, S.P., 2016. A novel description of fluid flow in porous and debris materials. Eng. Geol. 202, 62–73.

Roylance, D., 2001. Engineering viscoelasticity, Cambridge.

Rubin, A.M., 1992. Dike-induced faulting and Graben subsidence in volcanic rift zones. J. Geophys. Res. 97 (B2), 1839–1858.

Shi, X.Q., Wu, J.C., Ye, S.J., Zhang, Y., Xue, Y.Q., Wei, Z.X., Li, Q.F., Yu, J., 2008. Regional land subsidence simulation in Su-Xi-Chang area and shanghai City, China. Eng. Geol. 100, 27–42.

Terzghi, K., 1923. Die berechnung durchlassigkeitsziffer des tones aus dem verlauf der hydrodynamischen spannungserscheinungen. Sitzungsber. Akad. Wiss. Wien Math. Naturwiss. Kl 132 (Abt.2A), 125–138.

Terzopoulos, D., Fleischer, K., 1988. Modeling inelastic deformation viscoelasticity, plasticity, fracture. Comput. Graph. 22 (4), 269–278.

Truesdell, C., 1960. The rational mechanics of flexible of elastic bodies. In: Orell Fulssli.

Tsai, T.L., 2009. Viscosity effect on consolidation of poroelastic soil due to groundwater table depression. Environ. Geol. 57, 1055–1064.

Tsai, T.L., 2015. A coupled one-dimensional viscoelastic-plastic model for aquitard consolidation caused by hydraulic head variations in aquifers. Hydrol. Process. 29, 4779–4793.

Vazquez, J.L., 2007. The Porous Medium Equation. Mathematical Theory. Oxford Univ. Press.

Verruijt, A., 1969. Elastic storage of aquifers. In: DeWiest, R.J.M. (Ed.), Flow through Porous Media. Academic, New York, pp. 331–376.

Vincent, J., 2012. Structural Biomaterials, third ed. Princeton University Press.

Wang, H.F., 2000. Theory of Linear Poroelasticity — With Applications to Geomechanics and Hydrogeology. Princeton University Press.

Water Resources Agency, 2015. Changhua and Yunlin subsidence monitoring and analysis interim report 2015 year. In: Report of Water Resources Agency, Taipei, (in Chinese, with English abstract).

Wu, J.H., Shi, X.Q., Ye, S.J., Xue, Y.Q., Zhang, Y., Wei, Z.X., Fang, Z., 2010. Numerical simulation of viscoelastoplastic land subsidence due to groundwater overdrafting in Shanghai, China. J. Hydrol. Eng. 15 (3), 223–236.

Xue, Y.-Q., Zhang, Y., Ye, S.-J., Wu, J.-C., Li, Q.-F., 2005. Land subsidence in China. Environ. Geol. 48, 713–720.

Ye, S.J., Xue, Y.Q., Wu, J.C., Li, Q.F., 2012. Modeling visco-elastic-plastic deformation of soil with modified Merchant model. Environ. Earth 66, 1497–1504.

Zhang, Y., Xue, Y.Q., Wu, J.C., Ye, S.J., Wei, Z.X., Li, Q.F., Yu, J., 2007. Characteristics of aquifer system deformation in the southern Yangtse Delta, China. Eng. Geol. 90, 160–173.

Zhang, Y., Xue, Y.Q., Wu, J.C., Wang, H.M., He, J.J., 2012. Mechanical modeling of aquifer sands under long-term groundwater withdrawal. Eng. Geol. 125, 74–80.