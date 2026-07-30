# v1

\subsection{Datasets}
\label{subsec:datasets}

Characterization of subsurface layerwise deformation require một hệ thống quan trắc có thể theo dõi được sự biến động trong thời gian của các yếu tố vật lý có mối tương quan cao với subsurface deformation. Vì vậy, nghiên cứu này sẽ integrate four primary data sources, comprising (1) depth-dependent deformation, (2) borehole lithology logs and 3D hydrogeological model, (3) groundwater level (GWL) monitoring stations, and (4) total surface deformation derived from Global Navigation Satellite System (GNSS) stations and Small Baseline Subset Interferometric Synthetic Aperture Radar (SBAS-InSAR) analysis. các chương mục dưới đây sẽ trình bày tính chất của từng lọai dữ liệu, các giá trị nó cung cấp (tại sao chúng ta cần dữ liệu này), và các bước pre-process số liệu.

\subsubsection{Depth-dependent deformation}

Depth-dependent deformation recorded by the multilayer compaction monitoring wells (MLCWs), a specialized borehole extensometer equipped with 21 to 26 magnetic rings installed along the well profile to depths of up to 300~m. These magnetic rings were anchored near major hydrostratigraphic boundaries and lithological transitions, isolating compaction within individual aquifer and aquitard units with a measurement precision of 1~mm \citep{hung_measuring_2021}.

Monthly raw observations from five MLCW stations (Guangfu, Huwei, Tuku, Honglun, and Xiutan) were collected và được partitioned into six uniform 50~m depth sections (designated as S1 through S6, spanning 0--300~m depth) to align variable anchor ring depths across boreholes. sau đó các timeseries ở từng section sẽ được fit bằng mộ deformation model, được giới thiệu chi tiết ở phần \label{subsec:parametric_deformation}, to extract long-term linear trend và primary seasonal signals. sau đó chúng ta thực hiện first-order differencing để thu được chênh lệch từng tháng của subsurface deformation cho từng sections.

Thông tin sơ bộ về các trạm quan trắc được nêu ra ở \Cref{tab:mlcw_info}.

\subsubsection{Groundwater levels}

Groundwater level fluctuations đã từ lâu được chứng minh là tác nhân chủ đạo chi phối mức độ nặng nhẹ của sụt lún \citep{galloway_land_1999, gambolati_2015, herrera-garcia_mapping_2021, bagheri_2021_global}. The regional groundwater level monitoring network operated by the Water Resources Agency (WRA) of Taiwan comprised nested observation wells screened at discrete depth intervals corresponding to Aquifers 1 through 4 \citep{survey_project_1999, liu_characterization_2004}. Daily piezometric head measurements, expressed as elevations relative to Mean Sea Level (m MSL), spanned from January 2000 to December 2025 across Yunlin County, capturing seasonal agricultural pumping drawdowns, wet-season monsoon recharge replenishment, and multi-decadal head declines \citep{chang2022_wetanddry, lu2020_crfp}. Piezometric head series were converted into monthly observation steps, with station network attributes summarized in \Cref{tab:gwl_info}. sau đó chúng ta thực first-order differencing để thu được chênh lệch từng tháng của mực nước ngầm ở từng giếng quan trắc.

\subsubsection{Borehole lithological profiles}

Borehole lithological profiles and regional stratigraphy defined the sedimentological framework controlling physical compressibility and drainage behavior within these six 50~m compaction sections. High-resolution lithological logs co-located with each MLCW recorded the vertical distribution of sedimentary facies, including gravel, coarse sand, fine sand, silt, and clay, down to 300~m depth. For unmonitored zones between boreholes, stratigraphy was complemented by the 3D hydrogeological model developed by the Geological Survey and Mining Management Agency \citep{gsmma_3d}

\subsubsection{Total surface deformation}

Daily 3D position time series from continuous GNSS (cGNSS) stations co-located with or positioned near the MLCW sites \citep{IESAS_TGM_2026} provided point-based vertical displacement series from 2010 to 2024, with station coordinates and monitoring periods summarized in \Cref{tab:gnss_info}. Meanwhile, ở những điểm không có trạm GPS, total surface deformation được trích xuất từ kết quả phân tích ảnh SAR từ Sentinel-1. Nghiên cứu này  sử dụng 266 SAR images along ascending path 69 (incidence angles $32^{\circ}$ to $38^{\circ}$) and 264 SAR images along descending path 105 (incidence angles $38^{\circ}$ to $43^{\circ}$), with acquisition specifications summarized in \Cref{tab:sentinel1_info}. Small-baseline interferogram stacks generated via the HyP3 pipeline \citep{hogenson_hybrid_2025} and multitemporal phase inversion conducted using MintPy \citep{yunjun_small_2019} generated initial line-of-sight displacement measurements.Vertical surface displacements were resolved via two-dimensional vector decomposition combining ascending and descending line-of-sight time series \citep{fuhrmann_resolving_2019, hanssen_radar_2001}.
timeseries của total surface defeformation from GPS và SBAS-InSAR sau đó được fit lại bằng deformation model nhắc tới \Cref{subsec:parametric_deformation}, sau đó chuyển đổi thành monthly resampling rate. tương tự, first-order differencing được thực hiện để tính toán mức độ chênh lệch từng tháng của total surface deformation.

---

# v2

\subsection{Datasets}
\label{subsec:datasets}

This study integrated four primary data sources to characterize compaction within individual depth sections, comprising (1) multilayer compaction observations, (2) groundwater level records, (3) borehole lithological profiles, and (4) vertical surface displacement derived from Global Navigation Satellite System (GNSS) stations and Small Baseline Subset Interferometric Synthetic Aperture Radar (SBAS-InSAR) analysis. The following subsections describe each dataset, its role in the compaction analysis, and the preprocessing applied before model construction.

\subsubsection{Multilayer aquifer-system compaction}

Multilayer compaction monitoring wells (MLCWs) recorded deformation at multiple depths. These specialized borehole extensometers contained 21 to 26 magnetic rings installed along the well profile to depths of up to 300~m, allowing compaction within individual aquifer and aquitard units to be isolated with a measurement precision of 1~mm \citep{hung_measuring_2021}. Monthly raw observations from five primary MLCW stations (Guangfu, Huwei, Tuku, Honglun, and Xiutan) were collected and partitioned into six uniform 50~m depth sections (designated as S1 through S6, spanning 0--300~m depth) to account for differences in anchor ring depth among boreholes, with station coordinates and monitoring specifications summarized in \Cref{tab:mlcw_info}. Sectional time series were then fitted with a deformation model comprising linear, periodic, and step functions (\Cref{subsec:parametric_deformation}), which estimated linear velocities and annual and semiannual components. Differences between consecutive months were subsequently calculated to obtain compaction increments for each section.

\subsubsection{Groundwater level observations}

Groundwater level (GWL) observations recorded variations in hydraulic head associated with aquifer-system compaction and land subsidence in alluvial fan aquifer systems \citep{galloway_land_1999, gambolati_2015, herrera-garcia_mapping_2021, bagheri-gavkoshLandSubsidenceGlobal2021}. The regional GWL monitoring network operated by the Water Resources Agency (WRA) of Taiwan comprised nested observation wells screened at discrete depth intervals corresponding to Aquifers 1 through 4 \citep{survey_project_1999, liu_characterization_2004}. Daily piezometric head measurements, expressed as elevations relative to Mean Sea Level (m MSL), spanned from January 2000 to December 2025 across Yunlin County, capturing seasonal agricultural pumping drawdowns, monsoon recharge during the wet season, and head declines over multiple decades \citep{chang2022_wetanddry, lu2020_crfp}. Station locations, screened intervals, and monitoring periods are summarized in \Cref{tab:gwl_info}. Daily piezometric head observations were averaged to monthly values, and differences between consecutive months were calculated to obtain monthly hydraulic head changes (\Cref{subsec:hydrogeological_drivers}).

\subsubsection{Borehole lithological profiles}

Borehole lithological profiles described variations in sediment composition among the six 50~m compaction sections. Detailed logs at each MLCW recorded the vertical distribution of gravel, sand, silt, clay, and mixed fine-grained deposits to depths of 300~m. The logged materials were classified as gravel, coarse sand, fine sand, or a combined clay, silt, and mud group within each depth section. These borehole-derived compositions provided the sediment predictors used for model calibration and cross-station validation after the log ratio balance transformation described in \Cref{subsec:ilr_sbp_transformation}.

Sediment architecture between monitoring stations was represented separately by the 3D hydrogeological model developed by the Geological Survey and Mining Management Agency \citep{gsmma_3d}. % TODO(CITATION): Find a peer-reviewed source supporting the 1 m vertical resolution and 500 m horizontal grid spacing of the 3D hydrogeological model; add its BibTeX entry to writing_manu2.bib, then insert \citep{citation_key} here.
The regional model provided continuous lithological profiles at a 1~m vertical resolution and a 500~m horizontal grid spacing. This regional product was retained to describe sediment variability between monitoring stations and did not replace the borehole-derived sediment compositions used in the reported station-based analyses.

\subsubsection{Vertical surface displacement}

Vertical surface displacement measurements recorded the integrated ground displacement resulting from compaction across all underlying depth intervals. Daily 3D position time series from continuous GNSS (cGNSS) stations located at or near the MLCW sites \citep{IESAS_TGM_2026} provided point observations of vertical displacement from 2010 to 2024, with station coordinates and monitoring periods summarized in \Cref{tab:gnss_info}. Surface locations outside GNSS coverage were monitored using Small Baseline Subset (SBAS) InSAR analysis of Sentinel-1 Synthetic Aperture Radar (SAR) imagery, comprising 266 ascending path 69 images and 264 descending path 105 images with acquisition parameters summarized in \Cref{tab:sentinel1_info} \citep{torres_gmes_2012, yague-martinez_interferometric_2016}. SBAS interferogram stacks were generated with the HyP3 pipeline \citep{hogenson_hybrid_2025}, and multitemporal phase inversion was conducted using MintPy \citep{yunjun_small_2019}. These processing steps produced initial displacement measurements along the radar line of sight. Vertical surface displacement was then resolved by vector decomposition in two dimensions \citep{fuhrmann_resolving_2019, hanssen_radar_2001}. Vertical surface displacement time series from cGNSS and SBAS-InSAR were subsequently fitted with a deformation model comprising linear, periodic, and step functions (\Cref{subsec:parametric_deformation}), resampled to a monthly interval, and differenced between consecutive months to obtain surface displacement increments.

Integration of these four preprocessed data sources produced a monthly dataset aligned in space and time. The dataset linked subsurface lithology, hydraulic head variations, and vertical surface displacement to compaction rates across the six 50~m depth intervals (\Cref{fig:preprocessing_workflow}).

---

# v2 (vietnamese)

% ===================================================================
% BẢN DỊCH TIẾNG VIỆT CỦA SECTIONS/DATASET002.TEX
% Nguồn: phiên bản tại commit 7a41a1d
% ===================================================================

\subsection{Các bộ dữ liệu}
\label{subsec:datasets}

% AUTHOR-IDEA START [DATA-OVERVIEW-01]
% Ý tui muốn thêm (ý tưởng thô):
% [quan trắc subsurface layerwise deformation sẽ được lấy từ trạm quan trắc lún đa tầng multilayer compaction monitoring wells. nhưng như đã nhắc tới trước đó ở phần Intro (tui sẽ viết phần intro001.tex sau này, không phải bây giờ), các trạm quan trắc này sẽ bị shutdown bớt hoặc giảm tần suất lấy mẫu để tiết kiệm ngân sách sau này. vậy nên chúng ta sẽ sử dụng những đại lượng dễ quan trắc hơn và rẻ tiền hơn để ước chừng subsurface layerwise deformation, bao gồm total surface deformation và hydraulic head variations. dĩ nhiên chúng ta sẽ không thể lấy historical measurements của MLCW làm predictor được. và chúng ta cũng cần một đại lượng đóng vai trò cung cấp thông tin về địa tầng địa chất, để mô hình nhận diện được sự khác biệt về không gian khi thực hiện estimation, đó chính là lithological profiles.
%
% Mục đích của ý tưởng này:
% [chúng ta nên có một câu dẫn nhập để người đọc hiểu rằng lý do nào mà ta phải thu thập các dữ liệu như vậy, chứ không phải vì ngẫu nhiên mà ta chọn chúng]
% AUTHOR-IDEA END [DATA-OVERVIEW-01]

Nghiên cứu này tích hợp bốn nguồn dữ liệu chính để đặc trưng hóa lún nén trong từng đoạn chiều sâu, bao gồm (1) số liệu quan trắc lún nén nhiều lớp, (2) số liệu mực nước dưới đất, (3) mặt cắt thạch học lỗ khoan, và (4) chuyển vị thẳng đứng bề mặt được xác định từ các trạm Hệ thống vệ tinh định vị toàn cầu (GNSS) và phân tích Giao thoa radar khẩu độ tổng hợp theo tập hợp đường đáy ngắn (SBAS-InSAR). Các tiểu mục sau mô tả từng bộ dữ liệu, vai trò của chúng trong phân tích lún nén, và các bước tiền xử lý được thực hiện trước khi xây dựng mô hình.

\subsubsection{Lún nén nhiều lớp của hệ thống tầng chứa nước}

Các giếng quan trắc lún nén nhiều lớp (MLCW) ghi nhận biến dạng tại nhiều độ sâu. Mỗi thiết bị đo biến dạng lỗ khoan chuyên dụng được lắp từ 21 đến 26 vòng từ dọc theo thân giếng đến độ sâu tối đa 300~m, qua đó cho phép phân tách lún nén trong từng đơn vị tầng chứa nước và lớp cách nước với độ chính xác đo 1~mm \citep{hung_measuring_2021}. Số liệu quan trắc thô theo tháng từ năm trạm MLCW chính (Guangfu, Huwei, Tuku, Honglun và Xiutan) được thu thập và phân chia thành sáu đoạn chiều sâu đồng nhất, mỗi đoạn dày 50~m (ký hiệu S1 đến S6, trong khoảng độ sâu 0--300~m), nhằm xử lý sự khác biệt về độ sâu lắp đặt vòng neo giữa các lỗ khoan. Tọa độ trạm và thông số quan trắc được tổng hợp trong \Cref{tab:mlcw_info}. Sau đó, chuỗi thời gian của từng đoạn chiều sâu được khớp bằng mô hình biến dạng gồm các hàm tuyến tính, tuần hoàn và hàm bước (\Cref{subsec:parametric_deformation}) để ước tính vận tốc tuyến tính cùng các thành phần chu kỳ năm và nửa năm.

% AUTHOR-IDEA START [DATA-OVERVIEW-02]
% Ý tui muốn thêm (ý tưởng thô):
% [chúng ta phải fit một mô hình deformation cho từng ring là bởi vì không phải tất cả các trạm đều được đo đạc mẫu trong cùng một ngày, sự sai khác về thời gian lấy mẫu đòi hỏi chúng ta phải mô hình lại observations để đưa chúng về cùng một ngày. ngoài ra, nghiên cứu này sẽ ước tính biến động của từng tháng thay vì dự đoán giá trị tích lũy tới một thời điểm t để tránh sai số tích lũy qua thời gian]
%
% Mục đích của ý tưởng này:
% [chúng ta nên gỉai thích ngắn gọn tại sao lại phải fit một cái mô hình deformation và tính difference chứ không giữ những timeseries ở dạng cumulative timeseries]
%
% AUTHOR-IDEA END [DATA-OVERVIEW-02]

Sai phân giữa hai tháng liên tiếp được tính để thu được gia số lún nén của từng đoạn chiều sâu.

\subsubsection{Quan trắc mực nước dưới đất}

Số liệu mực nước dưới đất (GWL) ghi nhận biến động cột nước thủy lực liên quan đến lún nén hệ thống tầng chứa nước và sụt lún đất trong các hệ thống tầng chứa nước thuộc quạt bồi tích \citep{galloway_land_1999, gambolati_2015, herrera-garcia_mapping_2021, bagheri-gavkoshLandSubsidenceGlobal2021}. Mạng lưới quan trắc GWL khu vực do Cơ quan Tài nguyên nước Đài Loan (WRA) vận hành gồm các cụm giếng quan trắc nhiều độ sâu, với đoạn ống lọc được bố trí tại những khoảng độ sâu riêng biệt tương ứng với các tầng chứa nước 1 đến 4 \citep{survey_project_1999, liu_characterization_2004}. Số liệu cột nước áp lực hằng ngày, được biểu diễn dưới dạng cao độ so với mực nước biển trung bình (m MSL), kéo dài từ tháng 1 năm 2000 đến tháng 12 năm 2025 trên toàn huyện Yunlin. Chuỗi số liệu này ghi nhận hạ thấp mực nước theo mùa do khai thác nước phục vụ nông nghiệp, sự phục hồi trong mùa mưa do bổ cập gió mùa, và xu thế suy giảm cột nước trong nhiều thập kỷ \citep{chang2022_wetanddry, lu2020_crfp}. Vị trí trạm, khoảng đặt ống lọc và thời gian quan trắc được tổng hợp trong \Cref{tab:gwl_info}. Số liệu cột nước áp lực hằng ngày được lấy trung bình theo tháng, sau đó sai phân giữa hai tháng liên tiếp được tính để thu được thay đổi cột nước thủy lực theo tháng (\Cref{subsec:hydrogeological_drivers}).

\subsubsection{Mặt cắt thạch học lỗ khoan}

Mặt cắt thạch học lỗ khoan mô tả sự khác biệt về thành phần trầm tích giữa sáu đoạn chiều sâu lún nén, mỗi đoạn dày 50~m. Nhật ký thạch học chi tiết tại mỗi trạm MLCW ghi nhận phân bố theo phương thẳng đứng của sỏi, cát, bột, sét và các trầm tích hạt mịn hỗn hợp đến độ sâu 300~m. Vật liệu trong nhật ký được phân thành sỏi, cát thô, cát mịn, hoặc nhóm kết hợp gồm sét, bột và bùn trong từng đoạn chiều sâu. Thành phần trầm tích xác định từ lỗ khoan cung cấp các biến dự báo trầm tích cho quá trình hiệu chỉnh mô hình và kiểm định chuyển giao giữa các trạm sau phép biến đổi cân bằng logratio được mô tả trong \Cref{subsec:ilr_sbp_transformation}.

% AUTHOR-IDEA START [DATA-OVERVIEW-03]
% Câu văn tui muốn thay đổi:
% [These borehole-derived compositions provided the sediment predictors used for model calibration and cross-station validation after the log ratio balance transformation described in \Cref{subsec:ilr_sbp_transformation}.]
%
% Ý tui muốn thêm (ý tưởng thô):
% [chúng ta phải giải thích lý do đằng sau, tại sao chúng quyết định sửa dụng phương pháp này để biến đổi cái sediment composition. (1) là vì chúng ta cần một đại lượng static ở các vị trí khác nhau để định hình sự khác biệt về mặt vật lý và địa chất ở mỗi tầng aquifer ở các địa điểm khác nhau. (2) là ta muốn tránh bị collinearity khi tổng của 4 vật liệu sẽ là 100%]
%
% AUTHOR-IDEA END [DATA-OVERVIEW-03]

Kiến trúc trầm tích giữa các trạm quan trắc được biểu diễn riêng bằng mô hình địa chất thủy văn 3D do Cơ quan Khảo sát Địa chất và Quản lý Khai khoáng xây dựng \citep{gsmma_3d}. % TODO(CITATION): Tìm nguồn bình duyệt hỗ trợ độ phân giải đứng 1 m và khoảng cách lưới ngang 500 m của mô hình địa chất thủy văn 3D; thêm mục BibTeX vào writing_manu2.bib rồi chèn \citep{citation_key} tại đây.
Mô hình khu vực cung cấp các mặt cắt thạch học liên tục với độ phân giải đứng 1~m và khoảng cách lưới ngang 500~m. Sản phẩm khu vực này được giữ lại để mô tả biến thiên trầm tích giữa các trạm quan trắc và không thay thế thành phần trầm tích xác định từ lỗ khoan trong các phân tích theo trạm được trình bày trong nghiên cứu.

% AUTHOR-IDEA START [DATA-OVERVIEW-04]
%
% Ghi chú:
% [chúng ta nên ghi thêm trang web cho cái mô hình thủy văn này vì chắc chắn không có citation ở dạng peer-reviewed paper để lấy rồi]
%
% AUTHOR-IDEA END [DATA-OVERVIEW-04]

\subsubsection{Chuyển vị thẳng đứng bề mặt}

Số liệu chuyển vị thẳng đứng bề mặt ghi nhận chuyển vị tổng hợp của mặt đất do lún nén trong tất cả các khoảng chiều sâu bên dưới. Chuỗi tọa độ ba chiều hằng ngày từ các trạm GNSS liên tục (cGNSS) đặt tại hoặc gần các trạm MLCW \citep{IESAS_TGM_2026} cung cấp số liệu chuyển vị thẳng đứng tại điểm trong giai đoạn 2010--2024. Tọa độ trạm và thời gian quan trắc được tổng hợp trong \Cref{tab:gnss_info}. Tại các khu vực nằm ngoài phạm vi quan trắc của GNSS, chuyển động bề mặt được theo dõi bằng phân tích SBAS-InSAR từ ảnh radar khẩu độ tổng hợp (SAR) Sentinel-1. Bộ dữ liệu gồm 266 ảnh quỹ đạo đi lên thuộc path 69 và 264 ảnh quỹ đạo đi xuống thuộc path 105; các thông số thu nhận được tổng hợp trong \Cref{tab:sentinel1_info} \citep{torres_gmes_2012, yague-martinez_interferometric_2016}. Các chồng giao thoa đồ SBAS được tạo bằng quy trình HyP3 \citep{hogenson_hybrid_2025}, và phép nghịch đảo pha đa thời gian được thực hiện bằng MintPy \citep{yunjun_small_2019}. Các bước xử lý này tạo ra số liệu chuyển vị ban đầu theo hướng nhìn của radar. Sau đó, chuyển vị thẳng đứng bề mặt được xác định bằng phép phân rã vector hai chiều \citep{fuhrmann_resolving_2019, hanssen_radar_2001}. Chuỗi thời gian chuyển vị thẳng đứng bề mặt từ cGNSS và SBAS-InSAR tiếp tục được khớp bằng mô hình biến dạng gồm các hàm tuyến tính, tuần hoàn và hàm bước (\Cref{subsec:parametric_deformation}), lấy mẫu lại theo tháng, rồi tính sai phân giữa hai tháng liên tiếp để thu được gia số chuyển vị bề mặt.

Việc tích hợp bốn nguồn dữ liệu đã qua tiền xử lý tạo ra một bộ dữ liệu theo tháng được đồng bộ trong không gian và thời gian. Bộ dữ liệu này liên kết thạch học dưới bề mặt, biến động cột nước thủy lực và chuyển vị thẳng đứng bề mặt với tốc độ lún nén trong sáu khoảng chiều sâu, mỗi khoảng dày 50~m (\Cref{fig:preprocessing_workflow}).

---

# v3

Compaction within individual subsurface depth intervals was measured monthly using specialized borehole extensometers known as multilayer compaction monitoring wells (MLCWs). Operation of these instruments required dedicated installations, maintanance, and repeated field measurements, which đòi hỏi một khoản kinh phí không nhỏ để duy trì qua nhiều năm. trong tương lai các trạm MLCW sẽ giảm dần tần suất thu thập observations (có thể từ 6 tháng tới 1 năm mới đo lại, để tiết kiệm ngân sách). Do đó, nghiên cứu này muốn tìm cách để tận dụng other monitoring data for estimating monthly subsurface layer compaction để chuẩn bị cho scenario đó. (Cần phải nhắc nhở là trạm MLCW không dừng hẳn việc lấy mẫu, chỉ là tần suất lấy mẫu sẽ giảm.) Four data sources were integrated for this purpose, comprising (1) MLCW observations, (2) groundwater level (GWL) records, (3) borehole lithological profiles, and (4) vertical surface displacement derived from continuous Global Navigation Satellite System (cGNSS) stations and Small Baseline Subset Interferometric Synthetic Aperture Radar (SBAS-InSAR) analysis. The MLCW records defined the response used for model calibration and evaluation, while historical MLCW measurements were excluded from the predictor variables. Groundwater level changes and vertical surface displacement provided time-varying information, whereas the lithological profiles described differences in sediment composition among depth sections and monitoring locations. The following subsections describe each dataset, and the temporal alignment applied before model construction.