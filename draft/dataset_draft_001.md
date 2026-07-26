# very first draft

\subsection{Data sets}

This study integrates four primary categories of data: (1) layerwise subsurface deformation from multilayer compaction monitoring wells (MLCWs), (2) stratigraphical and lithological profiles, (3) groundwater level observations, and (4) total surface displacement derived from GNSS stations and SBAS-InSAR processing.

The primary datasets for layerwise monitoring are obtained from multilayer compaction monitoring wells (MLCWs). An MLCW is a specialized borehole extensometer designed to capture subtle subsurface compaction by recording measurements at magnetic rings anchored at strategic hydrogeological boundaries—such as transitions between major aquifers or fine- and coarse-grained sedimentary units defined by the Geological Survey and Mining Management Agency (GSMMA). Extending to depths up to 300~m, each MLCW contains 21 to 26 magnetic rings anchored throughout the profile to provide aquifer-specific compaction measurements based on local hydrogeological properties. The installation and operational framework of these MLCWs are detailed by \citep{hung_measuring_2021}. This research utilizes data from five MLCWs, as summarized in \Cref{tab:mlcw_info}.

To complement the compaction measurements, each MLCW is accompanied by a borehole lithological profile detailing the stratigraphical distribution of materials—including gravel, coarse sand, fine sand, and clay/silt/mud—down to a depth of 300~m. For locations lacking direct MLCW coverage, stratigraphical information is supplemented by the 3D hydrogeological model from \citet{gsmma_3d}. This model provides continuous stratigraphical profiles at a 1-meter vertical interval and a spatial resolution of 500~m, forming the second dataset for this study.

For hydrological context, the third dataset consists of groundwater level observations from 25 monitoring stations located across the Yunlin area. Managed by the Water Resources Agency (WRA) of the Ministry of Economic Affairs in Taiwan, the well screens in this network span all four major aquifers of the Choushui River alluvial fan. Most stations provide continuous observation records spanning from January 1, 2000, to December 31, 2025. Details regarding these groundwater monitoring stations are listed in \Cref{tab:gwl_info}.

Regarding surface displacement, each MLCW site used in this study is co-located with a GNSS station providing daily 3D position observations (vertical, north-south, and east-west). In this work, only the vertical component—referred to hereafter as total surface deformation—is utilized. The GNSS datasets, provided by \citet{IESAS_TGM_2026}, cover the period from 2010 to 2025. Station parameters are summarized in \Cref{tab:gnss_info}.

Finally, to resolve spatial trends in total surface deformation beyond the point coverage of the GNSS network, SBAS-InSAR analysis was performed using Sentinel-1A SAR imagery. Approximately 600 SAR images spanning from January 2015 to December 2025 were processed using the `hyp3-isce2` plugin via the Hybrid Pluggable Processing Pipeline (HyP3) \citep{hogenson_hybrid_2025} and the Miami InSAR Time-series software (MintPy) \citep{yunjun_small_2019}. The parameters of the Sentinel-1A datasets are detailed in \Cref{tab:sentinel1_info}.


\begin{table}[h!]
	\centering
	\label{tab:mlcw_info}
	\begin{tabular}{|c|c|c|c|c|c|}
	\hline
	ID & Station & Lon & Lat & Elev. (m) & Bottom Depth (m) \\
	\hline
	1 & TUKU & & & & \\
	\hline
	2 & GUANGFU & & & & \\
	\hline
	3 & HUWEI & & & & \\
	\hline
	4 & HONGLUN & & & & \\
	\hline
	5 & XIUTAN & & & & \\
	\hline
	\end{tabular}
\end{table>

\begin{table}[h!]
	\centering
	\label{tab:gwl_info}
	\begin{tabular}{|c|c|c|c|c|c|}
		\hline
		ID & Station & Lon & Lat & Elev. (m) & Bottom Depth (m) \\
		\hline
		1 & TUKU & & & & \\
		\hline
		2 & GUANGFU & & & & \\
		\hline
		3 & HUWEI & & & & \\
		\hline
		4 & HONGLUN & & & & \\
		\hline
		5 & XIUTAN & & & & \\
		\hline
	\end{tabular}
\end{table>

\begin{table}[h!]
	\centering
	\label{tab:gnss_info}
	\begin{tabular}{|c|c|c|c|c|c|}
		\hline
		ID & Station & Lon & Lat & Elev. (m) & Bottom Depth (m) \\
		\hline
		1 & TUKU & & & & \\
		\hline
		2 & GUANGFU & & & & \\
		\hline
		3 & HUWEI & & & & \\
		\hline
		4 & HONGLUN & & & & \\
		\hline
		5 & XIUTAN & & & & \\
		\hline
	\end{tabular}
\end{table>

\begin{table}[H]
	\centering
	\caption{Summary of the Sentinel-1A datasets used in this study.}
	\label{tab:sentinel1_info}
	\begin{tabular}{lcc}
		\toprule
		\textbf{Parameters} & \textbf{Ascending} & \textbf{Descending} \\
		\midrule
		Relative Orbit (Path) & 69 & 105 \\
		\multicolumn{1}{l}{Acquisition Period} & \multicolumn{2}{c}{April 2016--November 2021} \\
		Number of Images & 266 & 264 \\
		\multicolumn{1}{l}{Acquisition Mode} & \multicolumn{2}{c}{Interferometric Wide (IW)} \\
		\multicolumn{1}{l}{Polarization} & \multicolumn{2}{c}{VV} \\
		Incidence Angles & $32^{\circ}$--$38^{\circ}$ & $38^{\circ}$--$43^{\circ}$ \\
		Satellite Headings & $347.63^{\circ}$ & $192.37^{\circ}$ \\
		\bottomrule
	\end{tabular}
\end{table}


---

# 2026/7/25 16:00

Flagged inconsistencies — verify before use

1. SAR image count and time span (Paragraph 6). Prose states approximately 600 images spanning January 2015 to December 2025. The same file's own \Cref{tab:sentinel1_info} table states 530 images (266 ascending, relative orbit 69, plus 264 descending, relative orbit 105) spanning April 2016 to November 2021. `sections/dataset001.tex` line 64 independently states "530 VV-polarized acquisitions collected from April 2016 to November 2021," corroborating the table, not the prose.
2. MLCW count (Paragraph 2). Prose states 5 MLCWs. `sections/dataset001.tex` lists 29 MLCWs in its table (likely an older or superseded station list; resolving which count is current is out of scope here).
3. GWL station count and location scope (Paragraph 4). Prose states 25 monitoring stations in the Yunlin area. The file's own \Cref{tab:gwl_info} table lists only 5 rows (TUKU, GUANGFU, HUWEI, HONGLUN, XIUTAN) with a "Bottom Depth" column, which matches the MLCW table structure, not a groundwater-level station list. This table appears to be a copy-paste of the MLCW table rather than actual GWL station data.
4. GNSS station table (Paragraph 5). \Cref{tab:gnss_info} appears to be the same copy-pasted 5-row MLCW-shaped table described in Item 3, not a GNSS-specific station list.
5. Study window conflict (Paragraphs 5 and 6, plus tables). The GNSS paragraph states 2010 to 2025. The SAR paragraph states January 2015 to December 2025. The SAR table states April 2016 to November 2021. Three different date ranges are asserted within one subsection.

\subsection{Data sets}

This study used multiple datasets to characterize land subsidence in the study area. These datasets consisted of layerwise deformation from multilayer compaction monitoring wells (MLCWs), total surface deformation from Global Navigation Satellite System (GNSS) stations and Small Baseline Subset Interferometric Synthetic Aperture Radar (SBAS-InSAR) analysis, groundwater level records, and lithological profiles. The following paragraphs describe each dataset in turn, beginning with the multilayer compaction monitoring wells.

The first dataset consisted of data from multilayer compaction monitoring wells (MLCWs). An MLCW is a specialized borehole extensometer that captures subsurface compaction by reading measurements at magnetic rings. Workers anchored these rings at boundaries between significant aquifers, or at transitions between fine and coarse sedimentary materials, as defined by the Geological Survey and Mining Management Agency (GSMMA). Each MLCW extends to a depth of up to 300 m, with 21 to 26 magnetic rings anchored throughout the profile. Aquifer units at each well were determined from hydrogeological properties, and each unit contained a number of corresponding magnetic rings that provided aquifer-specific compaction measurements. \citet{hung_measuring_2021} described the installation and measurement approach of the MLCWs in complete detail. This study used 5 MLCWs, shown in \Cref{tab:mlcw_info}.
% VERIFY: Prose states 5 MLCWs; sections/dataset001.tex lists 29 MLCWs in its table (see Flag 2).

Each MLCW is paired with a borehole lithological profile, which gives the distribution of stratigraphic materials, including gravel, coarse sand, fine sand, and clay, silt, or mud, along the 300 m depth. At locations without an MLCW, the three-dimensional hydrogeological model of \citet{gsmma_3d} provides the stratigraphic profile at each pixel at a 1 m depth interval, at a spatial resolution of 500 m. These lithological data formed the second dataset for this study, and the following paragraph turns to the groundwater level records that complement them.

The third dataset consisted of groundwater level records from monitoring wells located in the Yunlin area, comprising 25 monitoring stations.
% VERIFY: Prose states 25 GWL stations in Yunlin; the file's own tab:gwl_info table lists only 5 rows (TUKU, GUANGFU, HUWEI, HONGLUN, XIUTAN) with a Bottom Depth column matching the MLCW table structure, not a distinct GWL station list (see Flag 3).
Well screens were distributed across all four aquifers of the Choushui River alluvial fan. The Water Resources Agency (WRA) of the Ministry of Economic Affairs in Taiwan provided these records. Most stations contained observations spanning from January 1, 2000, to December 31, 2025. Information on the groundwater level monitoring stations is provided in \Cref{tab:gwl_info}. The next paragraph turns from groundwater level to surface deformation, measured independently by GNSS.

Each MLCW used in this study is accompanied by a GNSS station, which provides daily observations in three dimensions: up-down, north-south, and east-west. This study used only the up-down, or vertical, displacement component, referred to hereafter as total surface deformation. \citet{IESAS_TGM_2026} provided the GNSS data. GNSS observations span from 2010 to 2025.
% VERIFY: GNSS paragraph states 2010-2025; the SAR paragraph below states Jan 2015-Dec 2025, while the SAR table (tab:sentinel1_info) states Apr 2016-Nov 2021, producing three different date ranges within this subsection (see Flag 5).
Information on the GNSS stations used in this study is provided in \Cref{tab:gnss_info}.
% VERIFY: tab:gnss_info appears to be the same copy-pasted 5-row MLCW-shaped table described in Flag 4, not a GNSS-specific station list.

To estimate total surface deformation at locations where GNSS stations are unavailable, this study also used total surface deformation derived from Sentinel-1A Synthetic Aperture Radar (SAR) images through SBAS-InSAR. Approximately 600 SAR images spanning January 2015 to December 2025 were analyzed using the hyp3-isce2 plugin, part of the Hybrid Pluggable Processing Pipeline (HyP3) \citep{hogenson_hybrid_2025}, and the Miami InSAR Time-series software (MintPy) \citep{yunjun_small_2019}.
% VERIFY: Prose states ~600 images, Jan 2015-Dec 2025; the file's own tab:sentinel1_info table states 530 images (266 ascending + 264 descending), Apr 2016-Nov 2021; sections/dataset001.tex line 64 independently corroborates 530 images and the Apr 2016-Nov 2021 window (see Flag 1).
Information on the SAR images used for this study is provided in \Cref{tab:sentinel1_info}.

---

# 2026-07-25 16:53:42 (Claude v2, this one is okay)

\subsection{Data sets}

This study integrates four categories of data to characterize the land subsidence process in the study area: the monitored compaction record, the borehole lithology that controls compressibility at depth, the groundwater level changes that drive effective stress, and the surface deformation that results from compaction at all depths. Each dataset is described below, beginning with the compaction record itself.

Multilayer compaction monitoring wells (MLCWs) provide the layer-specific compaction record central to this study. An MLCW is a specialized borehole extensometer that measures subsurface compaction at magnetic rings anchored along the well profile. Workers install these rings at boundaries between aquifers and aquitards, or at transitions between coarse and fine sedimentary materials, following criteria set by the Geological Survey and Mining Management Agency (GSMMA). Each MLCW extends to a depth of up to 300 m, with [N] magnetic rings anchored throughout the profile. \citet{hung_measuring_2021} describe the installation and measurement method of the MLCWs in detail. This study uses [N] MLCW stations.

Each MLCW is paired with a borehole lithological profile describing the stratigraphic materials surrounding the well, including gravel, coarse sand, fine sand, and clay, silt, or mud, along the 300 m depth profile. This profile is treated in six 50 m depth sections (S1 through S6) spanning the full 300 m depth. At locations without an MLCW, the three-dimensional hydrogeological model of \citet{gsmma_3d} supplies the stratigraphic profile at a 1 m depth interval and a 500 m spatial resolution, extending lithological characterization beyond the borehole locations.

Groundwater level (GWL) records from monitoring wells in the Yunlin area provide the primary hydrological driver of compaction. This study uses [N] groundwater monitoring stations, with well screens distributed across all four aquifers of the Choushui River alluvial fan. The Water Resources Agency (WRA) of the Ministry of Economic Affairs in Taiwan provides these records, with observations at monthly or higher frequency over the period [START–END].

Global Navigation Satellite System (GNSS) stations provide the direct point measurement of surface deformation at each MLCW station. Each GNSS station records daily observations in three dimensions: up-down, north-south, and east-west. This study uses only the up-down, or vertical, component, referred to hereafter as total surface deformation. \citet{IESAS_TGM_2026} provides the GNSS data, spanning the period [START–END]. Small Baseline Subset Interferometric Synthetic Aperture Radar (SBAS-InSAR) analysis extends the estimate of total surface deformation to locations where GNSS stations are unavailable. This analysis is derived from [N] Sentinel-1A Synthetic Aperture Radar (SAR) images spanning [START–END], processed with the hyp3-isce2 plugin as part of the Hybrid Pluggable Processing Pipeline (HyP3) \citep{hogenson_hybrid_2025} and the Miami InSAR Time-series software (MintPy) \citep{yunjun_small_2019}.

---

# 2026-07-25 21:58:07 (ChatGPT 5.6 Sol, like shit)

\subsection{Monitoring and predictor data for section-pooled nowcasting}

The section-pooled nowcasting experiment used a multi-source monitoring dataset designed to link measured aquifer-system compaction with the hydrological, deformation, lithological, and seasonal conditions observed at the same monthly time step. The model input table was organized by station, depth section, and month. Each row paired an observed compaction increment with predictors derived from groundwater level records, surface deformation measurements, subsurface lithology, and calendar timing. This structure follows the physical interpretation of land subsidence as a time-dependent response to groundwater-level change, total surface deformation, and the compressibility of subsurface sediment.

Layer-specific compaction observations supplied the response variable. Multilayer compaction monitoring wells (MLCWs) measure vertical deformation between anchored magnetic rings installed along a borehole profile. The final dataset will include [N_MLCW] MLCW stations distributed across [STUDY_AREA_SUBREGIONS], with usable observations spanning [START_MLCW] to [END_MLCW]. For nowcasting, cumulative ring displacement was converted to monthly compaction increments for standardized depth sections S1-S6, each representing a 50 m interval from the land surface to 300 m depth. Negative values denote compaction or subsidence. The MLCW records therefore define the target variable that the section-pooled model predicts.

Groundwater level (GWL) records provided the main hydrological forcing. The final dataset will include [N_GWL] monitoring wells screened across [AQUIFER_UNITS], with observations spanning [START_GWL] to [END_GWL]. GWL values were referenced to m MSL and assigned to the corresponding station-section records before feature construction. The monthly feature table represented groundwater dynamics through first differences, second differences, absolute monthly change, short-term rolling means, and lagged changes at [LAG_SET; e.g., 1, 3, 6, 12, 24, and optional 36 months]. Section-specific and cross-section GWL terms were retained so the model could distinguish local hydraulic changes from broader aquifer-system signals.

Surface deformation records supplied an independent measure of total vertical motion at the ground surface. GNSS stations co-located with, or located near, the MLCW sites provided point-based vertical displacement observations over [START_GNSS] to [END_GNSS]. SBAS-InSAR products derived from Sentinel-1 SAR images extended the surface-deformation information across locations without continuous GNSS coverage; the final SAR inventory will include [N_SAR] images spanning [START_SAR] to [END_SAR]. The surface-deformation series was converted to monthly total-deformation change, acceleration, and short lags, represented in the model as \(dS_{total}\), \(d2S_{total}\), and lagged \(dS_{total}\) terms. These variables act as surface carriers of deformation from all depth intervals, while the MLCW target isolates the contribution from each modeled section.

Lithological information described the compressibility context of each depth section. Borehole logs and the three-dimensional hydrogeological model provide the vertical distribution of gravel, coarse sand, fine sand, silt, mud, and clay along the monitored profiles. For the nowcasting table, material proportions were aggregated within each 50 m section and transformed into isometric log-ratio coordinates, including gravel versus remaining material, sand versus clay-rich material, and coarse versus fine sand contrasts. These predictors encode stable subsurface conditions that control how a section responds to groundwater-level variation and surface-deformation loading.

Calendar-derived variables completed the model-ready dataset. Monthly sine and cosine terms, second-harmonic seasonal terms, and a dry-season indicator represented recurring seasonal timing without adding a separate climate dataset. The assembled dataset therefore joined four primary information streams--MLCW compaction, GWL dynamics, surface deformation from GNSS or SBAS-InSAR, and lithological composition--into a common monthly station-section table. All station counts, time spans, and image totals in this draft remain placeholders until the final feature inventory and manuscript tables are reconciled.

---

# 2026-07-25 22:43:34

\subsection{Data Sets}
\label{subsec_datasets}

Characterization of the multi-depth land subsidence process across the Choushui River Alluvial Fan (CRAF) requires an integrated monitoring framework bridging subsurface compaction mechanics, hydrostratigraphic architecture, hydrological drivers, and surface displacement. This study integrates four primary observational datasets, comprising (1) subsurface layerwise compaction records from multilayer compaction monitoring wells (MLCWs), (2) borehole lithology logs and 3D hydrostratigraphic modeling, (3) long-term groundwater level (GWL) observations, and (4) total surface deformation derived from Global Navigation Satellite System (GNSS) stations and Small Baseline Subset Interferometric Synthetic Aperture Radar (SBAS-InSAR) analysis.

Subsurface layerwise compaction records provide the direct target measurements for evaluating depth-dependent deformation. An MLCW is a specialized borehole extensometer that records vertical strain at magnetic rings anchored along the well profile at major hydrostratigraphic boundaries and lithological transitions \citep{hung_measuring_2021}. Extending to depths up to 300~m, each MLCW contains 21 to 26 magnetic rings configured to isolate compaction within individual aquifer and aquitard units with a measurement precision of 1~mm \citep{hung_measuring_2021}. To standardize multi-station analysis, cumulative ring displacements are converted into monthly compaction increments across six uniform 50~m depth sections, designated as S1 from 0 to 50~m, S2 from 50 to 100~m, S3 from 100 to 150~m, S4 from 150 to 200~m, S5 from 200 to 250~m, and S6 from 250 to 300~m. This study utilizes monthly records from five primary MLCW stations (TUKU, GUANGFU, HUWEI, HONGLUN, and XIUTAN) located in Yunlin County, representing the central zone of intensive land subsidence in the CRAF \citep{liu_characterization_2004}. Monitoring well parameters are summarized in \Cref{tab:mlcw_info}.

Borehole lithological profiles and regional stratigraphy define the sedimentological framework controlling subsurface compressibility and drainage behavior. High-resolution lithological logs co-located with each MLCW record the vertical distribution of sedimentary facies, including gravel, coarse sand, fine sand, silt, and clay, down to 300~m depth. Volumetric fractions of fine-grained, highly compressible materials (clay and silt) versus coarse-grained aquifer skeletal materials (gravel and sand) are aggregated within each 50~m depth section to quantify material controls on compaction. For unmonitored zones between boreholes, stratigraphy is complemented by the 3D hydrogeological model developed by the Geological Survey and Mining Management Agency \citep{gsmma_3d}. This model supplies continuous hydrostratigraphic profiles at a 1~m vertical resolution and a 500~m horizontal grid spacing, providing regional lithological constraints across the alluvial fan.

Groundwater level (GWL) observations supply the hydraulic head dynamics driving pore-fluid pressure changes and effective stress variations within the aquifer system. Managed by the Water Resources Agency (WRA) of Taiwan, the monitoring network comprises observation wells screened across all four major hydrogeological layers (Aquifers 1 through 4) of the CRAF \citep{hung_measuring_2021}. Hydraulic head measurements, referenced to meters relative to Mean Sea Level (m~MSL), span from January 2000 to December 2025 at monthly or higher observation frequencies. Stations co-located with or adjacent to the MLCW sites yield continuous time series of hydraulic head variations, capturing seasonal pumping drawdowns, wet-season recovery cycles, and long-term head declines that initiate inelastic aquitard consolidation.

Total surface deformation measurements capture the integrated ground displacement resulting from compaction across all underlying depth intervals. Daily 3D position observations from continuous GNSS stations co-located with each MLCW \citep{IESAS_TGM_2026} supply point-based vertical displacement series covering 2010 to 2025. To extend surface displacement monitoring beyond discrete GNSS stations, SBAS-InSAR analysis was performed using Sentinel-1A Synthetic Aperture Radar (SAR) imagery acquired in Interferometric Wide (IW) swath mode \citep{torres_gmes_2012,yague-martinez_interferometric_2016}. The SAR dataset contains 530 Level-1 Single-Look Complex (SLC) acquisitions collected between April 2016 and November 2021, comprising 266 VV-polarized images along ascending orbit 69 (incidence angles $32^{\circ}$ to $38^{\circ}$) and 264 images along descending orbit 105 (incidence angles $38^{\circ}$ to $43^{\circ}$). Time-series inversion executed via the HyP3 processing pipeline \citep{hogenson_hybrid_2025} and MintPy software \citep{yunjun_small_2019} yields high-density vertical velocity fields and monthly displacement series across the study domain. Parameters for the Sentinel-1A SAR datasets are summarized in \Cref{tab:sentinel1_info}.

---

# 2026-07-26 16:36:00 (my modifications)

## Comparison Table of Modifications

| Previous Version (`# 2026-07-25 22:43:34`) | Modified Version (Strong Noun Subjects, No Infinitive Openers) | Key Rationale / Rule Compliance |
| :--- | :--- | :--- |
| **Line 173 (Introductory Overview):**<br>Characterization of the multi-depth land subsidence process across the Choushui River Alluvial Fan (CRAF) requires an integrated monitoring framework bridging subsurface compaction mechanics, **hydrostratigraphic architecture**, **hydrological drivers**, and surface displacement. | **Line 173 (Introductory Overview):**<br>Characterization of the multi-depth land subsidence process across the Choushui River Alluvial Fan (CRAF) requires an integrated monitoring framework bridging subsurface compaction mechanics, the **hydrostratigraphic framework**, **hydraulic head variations**, and surface displacement. | Replaced non-standard terms `hydrostratigraphic architecture` and `hydrological drivers` with established hydrogeological domain terminology. |
| **Line 175 (MLCW Data Prep Sentence):**<br>**To standardize multi-station analysis**, cumulative ring displacements are converted into monthly compaction increments across six uniform 50~m depth sections... | **Line 175 (Strong Noun Subject Replacement):**<br>**Standardization of multi-station analysis** converted cumulative ring displacements measured at raw extensometer depths into monthly compaction increments across six uniform 50~m depth sections... | Eliminated the weak infinitive opener `To standardize...` in strict compliance with Rule 12 of `PAPER_WRITING_GUIDE.md` (Sentence Structure: Strong Subjects). |
| **Line 181 (InSAR Data Prep Sentence):**<br>**To extend surface displacement monitoring beyond discrete GNSS stations**, SBAS-InSAR analysis was performed using Sentinel-1A Synthetic Aperture Radar (SAR) imagery... | **Line 181 (Strong Noun Subject Replacement):**<br>**Spatial expansion of surface displacement monitoring beyond discrete GNSS stations** utilized SBAS-InSAR analysis applied to Sentinel-1A Synthetic Aperture Radar (SAR) imagery... | Eliminated the weak infinitive opener `To extend...` in strict compliance with Rule 12 of `PAPER_WRITING_GUIDE.md` (Sentence Structure: Strong Subjects). |
| **Section Structure:**<br>Single combined `\subsection{Data Sets}` mixing observational dataset inventory with preprocessing algorithms. | **Section Structure (Split Subsections):**<br>Split into `\subsection{Observational Data Sources}` (data inventory) and `\subsection{Data Processing and Standardization}` (preprocessing & section alignment). | Separates raw observational data streams from input feature engineering while maintaining strong noun phrase subjects throughout. |

---

## Refactored Section Text (LaTeX Format)

\subsection{Observational Data Sources}
\label{subsec_data_sources}

Characterization of the multi-depth land subsidence process across the Choushui River Alluvial Fan (CRAF) requires an integrated monitoring framework bridging subsurface compaction mechanics, the hydrostratigraphic framework, hydraulic head variations, and surface displacement. This study synthesizes four primary observational datasets, comprising (1) subsurface layerwise compaction records from multilayer compaction monitoring wells (MLCWs), (2) borehole lithology logs and 3D hydrogeological modeling, (3) long-term groundwater level (GWL) observations, and (4) total surface deformation derived from Global Navigation Satellite System (GNSS) stations and Small Baseline Subset Interferometric Synthetic Aperture Radar (SBAS-InSAR) analysis.

Subsurface layerwise compaction records provide the direct target measurements for evaluating depth-dependent deformation. An MLCW is a specialized borehole extensometer that records vertical strain at magnetic rings anchored along the well profile at major hydrostratigraphic boundaries and lithological transitions \citep{hung_measuring_2021}. Extending to depths up to 300~m, each MLCW contains 21 to 26 magnetic rings configured to isolate compaction within individual aquifer and aquitard units with a measurement precision of 1~mm \citep{hung_measuring_2021}. This study utilizes monthly records from five primary MLCW stations (TUKU, GUANGFU, HUWEI, HONGLUN, and XIUTAN) located in Yunlin County, representing the central zone of intensive land subsidence in the CRAF \citep{liu_characterization_2004}. Monitoring well parameters are summarized in \Cref{tab:mlcw_info}.

Borehole lithological profiles and regional stratigraphy define the sedimentological framework controlling subsurface compressibility and drainage behavior. High-resolution lithological logs co-located with each MLCW record the vertical distribution of sedimentary facies, including gravel, coarse sand, fine sand, silt, and clay, down to 300~m depth. For unmonitored zones between boreholes, stratigraphy is complemented by the 3D hydrogeological model developed by the Geological Survey and Mining Management Agency \citep{gsmma_3d}. This model supplies continuous hydrostratigraphic profiles at a 1~m vertical resolution and a 500~m horizontal grid spacing, providing regional lithological constraints across the alluvial fan.

Groundwater level (GWL) observations supply the hydraulic head dynamics driving pore-fluid pressure changes and effective stress variations within the aquifer system. Managed by the Water Resources Agency (WRA) of Taiwan, the monitoring network comprises observation wells screened across all four major hydrogeological layers (Aquifers 1 through 4) of the CRAF \citep{hung_measuring_2021}. Hydraulic head measurements, referenced to meters relative to Mean Sea Level (m~MSL), span from January 2000 to December 2025 at monthly or higher observation frequencies. Stations co-located with or adjacent to the MLCW sites yield continuous time series of hydraulic head variations, capturing seasonal pumping drawdowns, wet-season recovery cycles, and long-term head declines that initiate inelastic aquitard consolidation. Information regarding the groundwater level monitoring stations across Yunlin County is listed in \Cref{tab:gwl_info}.

Total surface deformation measurements capture the integrated ground displacement resulting from compaction across all underlying depth intervals. Daily 3D position observations from continuous GNSS stations co-located with each MLCW \citep{IESAS_TGM_2026} supply point-based vertical displacement series covering 2010 to 2025. Station parameters for the continuous GNSS network are provided in \Cref{tab:gnss_info}. Spatial expansion of surface displacement monitoring beyond discrete GNSS stations utilized SBAS-InSAR analysis applied to Sentinel-1A Synthetic Aperture Radar (SAR) imagery acquired in Interferometric Wide (IW) swath mode \citep{torres_gmes_2012,yague-martinez_interferometric_2016}. The SAR dataset contains 530 Level-1 Single-Look Complex (SLC) acquisitions collected between April 2016 and November 2021, comprising 266 VV-polarized images along ascending orbit 69 (incidence angles $32^{\circ}$ to $38^{\circ}$) and 264 images along descending orbit 105 (incidence angles $38^{\circ}$ to $43^{\circ}$). Time-series inversion executed via the HyP3 processing pipeline \citep{hogenson_hybrid_2025} and MintPy software \citep{yunjun_small_2019} yields high-density vertical velocity fields and monthly displacement series across the study domain. Parameters for the Sentinel-1A SAR datasets are summarized in \Cref{tab:sentinel1_info}.

\subsection{Data Processing and Standardization}
\label{subsec_data_processing}

Standardization of multi-station analysis converted cumulative ring displacements measured at raw extensometer depths into monthly compaction increments across six uniform 50~m depth sections. These standardized depth intervals are designated as S1 from 0 to 50~m, S2 from 50 to 100~m, S3 from 100 to 150~m, S4 from 150 to 200~m, S5 from 200 to 250~m, and S6 from 250 to 300~m. Conversion of cumulative ring displacements into monthly section-level increments isolates the temporal compaction response within each 50~m subsurface interval.

Subsurface material properties were aggregated to match the standardized depth sections. Volumetric fractions of fine-grained, highly compressible materials (clay and silt) versus coarse-grained aquifer skeletal materials (gravel and sand) were calculated within each 50~m depth section from logged facies profiles and 3D model extractions. This material aggregation quantifies sedimentological controls on compaction across matching depth intervals.

Temporal and spatial alignment of hydrological and surface deformation time series complemented the section-level compaction targets. Hydraulic head measurements were zero-referenced to baseline epochs and differenced at monthly steps to capture head changes driving effective stress. Continuous GNSS vertical positions and InSAR displacement series were temporally resampled to monthly intervals and spatially matched to MLCW locations, serving as surface displacement constraints for the multi-depth compaction system.

---

# 2026-07-26 19:37:52

## Citation review for `sections/dataset002.tex`

### Overall assessment

| Review item | Result | Interpretation |
|---|---|---|
| BibTeX integrity | **PASS** | All 15 citation keys used in `dataset002.tex` exist in `writing_manu2.bib`. No missing key was found. |
| Claim-to-source alignment | **NEEDS REVISION** | Several sources are relevant, but some citations support only part of the sentence placed before them. |
| Highest-priority problems | **6 issues** | The MLCW hardware description, five-station claim, GWL inventory, GNSS coverage, HyP3/MintPy roles, and conversion from InSAR line-of-sight displacement to vertical displacement require correction or stronger provenance. |
| Source file | **UNCHANGED** | This review does not modify `sections/dataset002.tex`. |

### Detailed review

| Priority | Location and claim | Current citation | Assessment | Evidence and problem | Recommended action |
|---|---|---|---|---|---|
| Low | Entire section | All citation keys | **Correct** | All 15 keys resolve in `writing_manu2.bib`. The citation syntax is valid. | Retain the keys, but revise their placement where one sentence contains multiple claims. |
| Low | Line 6: MLCW definition and magnetic-ring placement | `hung_measuring_2021` | **Direct support** | Hung et al. (2021) describes an MLCW with magnetic rings anchored according to aquifer boundaries and transitions between fine- and coarse-grained sediment. | Citation placement is appropriate. |
| **High** | Line 6: "each MLCW contains 21 to 26 magnetic rings" and extends "up to 300 m" | `hung_measuring_2021` | **Partial support and internal contradiction** | Hung et al. (2021) describes 25 measurement depths to 300 m and reports 1 mm precision and accuracy for a single-depth reading. Nguyen et al. (2024) directly states that WRA MLCWs contain 21 to 26 rings and have 1 mm measurement accuracy. The manuscript table also lists Honglun with a bottom depth of 340 m, which contradicts "up to 300 m." | Cite both `hung_measuring_2021` and `nguyen_quantitative_2024`. Revise the depth statement to distinguish the common 300 m design from the 340 m Honglun well. |
| **High** | Line 6: five selected stations "representing the central zone of intensive land subsidence" | `liu_characterization_2004`, `hung_multiple_2015`, `nguyen_quantitative_2024` | **Mixed claim** | The papers support severe subsidence in the CRAF or a Yunlin subsidence bowl, especially around Tuku and Yuanchang. They do not define the exact five-station selection used by the present study. "Central zone" is also spatially vague. | Split the sentence. State the five-station inventory as information from the present dataset and `\Cref{tab:mlcw_info}`. Place literature citations only after a separate sentence describing the documented Yunlin subsidence bowl or specific hotspots. |
| Medium | Line 8: 3D model with 1 m vertical resolution and 500 m horizontal spacing | `gsmma_3d` | **Not independently verified** | An official agency source is suitable for model provenance. However, the linked dynamic webpage did not expose the stated 1 m and 500 m specifications during this review. The BibTeX entry is also dated 2026 without a version or access date. | Retain the agency citation only after checking a versioned technical document, metadata export, or archived page that states both resolutions. Record the access date and model version. |
| Medium | Line 10: WRA observation wells cover Aquifers 1 through 4 | `survey_project_1999`, `chang2022_wetanddry` | **Partial support** | Chang et al. (2022) confirms the four-aquifer conceptual framework and WRA data provenance, but its analysis mainly uses Aquifers 1 and 2. It does not establish the present 54-station inventory across all four aquifers. The 1999 survey report is relevant but lacks a URL or DOI in the bibliography. | Use the official network report or current WRA station metadata as the main provenance source. Keep Chang et al. (2022) only for the regional aquifer framework, not as sole evidence for the current monitoring inventory. |
| **High** | Line 10: January 2000 to December 2025, monthly or higher frequency, referenced to m MSL | No citation attached to this inventory | **Needs dataset provenance** | These values describe the assembled study dataset, not a general literature fact. The current GWL table lists coordinates but does not show screen depth, observation period, datum, or sampling frequency. | Add a dataset-manifest citation or expand `tab:gwl_info` to include aquifer/screen, period, datum, and frequency. Use placeholders until the final inventory is fixed. |
| Medium | Line 10: seasonal drawdown, recovery, and long-term decline "initiate inelastic aquitard consolidation" | `poland_guidebook_1984`, `galloway_land_1999`, `lu2020_crfp` | **General support, wording too absolute** | The sources support the relationship between hydraulic-head decline, increased effective stress, aquifer-system compaction, and land subsidence. Inelastic compaction occurs only when effective stress exceeds the preconsolidation stress, so a head decline does not always initiate inelastic consolidation. | State the threshold explicitly: hydraulic-head decline reduces pore pressure and increases effective stress; inelastic compaction occurs when preconsolidation stress is exceeded. Keep the citations after this complete mechanism. |
| **High** | Line 12: daily 3D GNSS positions, co-located with each MLCW, covering 2010 to 2025 | `IESAS_TGM_2026` | **Source and table mismatch** | The TGM webpage supports a continuous GNSS data and metadata archive. It does not by itself verify the processed daily 3D series, exact station periods, or co-location. The table ends in 2024, not 2025, and the Huwei MLCW and NTUH GNSS coordinates are not co-located. | Replace "co-located with each MLCW" with "co-located with or located near the MLCW sites," after checking a distance threshold. Align the text with the final data period and cite the GNSS processing/product source in addition to TGM. |
| Low | Line 12: Sentinel-1A IW-mode SAR data | `torres_gmes_2012`, `yague-martinez_interferometric_2016` | **Direct support for sensor and mode** | These papers appropriately support the Sentinel-1 mission and the IW/TOPS acquisition and interferometric-processing characteristics. | Keep these citations for sensor and acquisition-mode descriptions. |
| Medium | Line 12: 530 SLC acquisitions, paths 69 and 105, date range, polarization, and incidence angles | No inventory citation; mission papers occur in the previous sentence | **Needs study-specific provenance** | Torres et al. and Yague-Martinez et al. describe the mission and IW/TOPS products. They cannot support the exact acquisition counts, selected paths, dates, or incidence-angle ranges assembled for this study. | Treat these numbers as the study's SAR inventory and support them with `\Cref{tab:sentinel1_info}`, an ASF/ESA query export, or a reproducible acquisition manifest. Do not imply that the mission papers contain these counts. |
| **High** | Line 12: "Time-series inversion executed via the HyP3 processing pipeline and MintPy" | `hogenson_hybrid_2025`, `yunjun_small_2019` | **Roles are conflated** | The MintPy paper directly supports weighted least-squares inversion of an interferogram stack, displacement time-series estimation, corrections, and average velocity estimation. The HyP3 citation supports the SAR processing infrastructure, but not the claim that HyP3 performed the time-series inversion. | Separate the workflow: HyP3 generated the interferometric products or stack, and MintPy performed time-series inversion and post-inversion corrections. Cite each source after its specific role. |
| **High** | Line 12: "vertical velocity fields and monthly displacement series" | `yunjun_small_2019` | **Unsupported vertical-component claim** | MintPy estimates displacement along the radar line of sight unless a separate projection or multi-geometry decomposition is applied. Neither citation, as placed, explains conversion to vertical displacement. | Use "line-of-sight displacement and velocity" unless a vertical-projection method is described. If vertical displacement was derived, state the incidence-angle assumption or ascending/descending decomposition and cite the method. |
| Low | Lines 17-21: processing performed by the present study | No citations | **Generally acceptable** | Study-specific transformations, aggregation, temporal resampling, and spatial matching do not require external citations when described reproducibly. The physical statements about sediment compressibility and effective stress are broader scientific claims. | Keep citations out of routine processing steps. Add a focused source only where a physical mechanism is asserted, or move that explanation to Study Area Background or Discussion. |

### Main conclusion

The section does not have a missing-citation-key problem. Its main weakness is that several citations are attached to compound sentences and therefore appear to support details that the cited sources do not contain. The first revision should split study-specific inventory from literature-supported interpretation, reconcile the prose with the tables, and assign HyP3, MintPy, and InSAR geometry their correct technical roles.

### Primary sources checked

| Citation key | Source used in this review | Main support |
|---|---|---|
| `hung_measuring_2021` | [Hung et al. (2021), Water Resources Research](https://doi.org/10.1029/2020WR028194) | MLCW construction, magnetic-ring placement, 25 measurement depths, 300 m depth, 1 mm single-reading precision/accuracy, and Yunlin monitoring context. |
| `nguyen_quantitative_2024` | [Nguyen et al. (2024), Remote Sensing](https://doi.org/10.3390/rs16203789) | WRA MLCWs with 21-26 rings, monthly measurements, 1 mm accuracy, and the Yunlin subsidence bowl. |
| `liu_characterization_2004` | [Liu et al. (2004), Environmental Geology](https://doi.org/10.1007/s00254-004-0983-6) | Regional CRAF subsidence, layer compression, and groundwater-level relationships. |
| `hung_multiple_2015` | [Hung et al. (2015), Proceedings of IAHS](https://doi.org/10.5194/piahs-372-385-2015) | Multi-sensor monitoring and large-scale subsidence across the CRAF. |
| `chang2022_wetanddry` | [Chang et al. (2022), Water](https://doi.org/10.3390/w14091494) | WRA groundwater data, four-aquifer conceptual framework, and analysis focused mainly on Aquifers 1 and 2. |
| `lu2020_crfp` | [Lu et al. (2020), Remote Sensing](https://doi.org/10.3390/rs12203315) | Groundwater-level and surface-displacement relationships in the CRAF. |
| `yague-martinez_interferometric_2016` | [Yague-Martinez et al. (2016), IEEE TGRS](https://doi.org/10.1109/TGRS.2015.2497902) | Sentinel-1 IW/TOPS mode and SLC interferometric processing. |
| `yunjun_small_2019` | [Yunjun et al. (2019), Computers and Geosciences](https://doi.org/10.1016/j.cageo.2019.104331) | MintPy time-series inversion, displacement estimation, corrections, and average velocity estimation. |
| `IESAS_TGM_2026` | [Taiwan Geodetic Model](https://tgm.earth.sinica.edu.tw/) | Continuous GNSS archive and station metadata, but not the complete processed-data claim in line 12. |
| `gsmma_3d` | [Taiwan Hydrogeological Information System](https://hydro.geologycloud.tw/map3d/model) | Official model provenance; the exact spatial and vertical resolutions still require a versioned supporting record. |
