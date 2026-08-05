# Manuscript Outline (v2.3) — Per-Section Bayesian Ridge Regression

Bản dàn ý này mô tả nội dung dự kiến cho từng phần (section) và tiểu mục (subsection). 
**Quy tắc cốt lõi:** Tuyệt đối không sử dụng các thuật ngữ nội bộ (như P0, P3, level1a, level1b, level1c, run_028, run_035, run_048, cross-section, own-section) trong bài viết. Chỉ sử dụng ngôn ngữ vật lý và dữ liệu để mô tả phương pháp và kết quả.

> **Quyết định nền tảng (Governing decision):** Mỗi phân lớp độ sâu (depth section) được mô hình hóa hoàn toàn độc lập bằng thuật toán Bayesian ridge regression. Các biến dự báo (predictors) bao gồm: thay đổi mực nước ngầm tại chính phân lớp đó, thay đổi mực nước ngầm tại các phân lớp khác, chuyển vị bề mặt theo phương thẳng đứng, và các chu kỳ theo mùa. Bài báo sẽ báo cáo kết quả đánh giá theo phương pháp tịnh tiến thời gian (walk-forward) tại trạm Tuku.

---

## 🔒 Locked sections (từ v2_1.md — không được chỉnh sửa nếu không có sự cho phép rõ ràng)

- **§1 Introduction** — Đang là bản nháp; cần bổ sung trích dẫn tổng quan tài liệu trước khi hoàn thiện.
- **§2 Study Area and Datasets (từ 2.1 đến 2.2.4)** — Đã được phê duyệt và đóng băng (stable).
- **§3.1 Preparation of model inputs (từ 3.1.1 đến 3.1.3)** — Đã được phê duyệt và đóng băng.

---

## Section-by-section content description

### 1 Introduction
🔒 *Locked (draft quality).*
Mục này xác định bài toán quan trắc: dữ liệu nén lún (MLCW) thường bị trễ và mạng lưới đang suy giảm. Tiếp theo, đánh giá các nghiên cứu tái tạo dữ liệu trước đây và chỉ ra khoảng trống nghiên cứu: chưa có phương pháp nào ước lượng nén lún theo từng độ sâu theo từng tháng bằng cách sử dụng dữ liệu mực nước ngầm và chuyển vị bề mặt đồng thời trong khoảng thời gian dữ liệu MLCW bị trễ. Cuối cùng, nêu rõ mục tiêu của nghiên cứu.

**Trạng thái:** Cần bổ sung các trích dẫn tài liệu trước khi chốt. Không có thay đổi về mặt cấu trúc.

---

### 2 Study Area and Datasets
🔒 *Locked.*

#### 2.1 Study Area Background
Mô tả Quạt bồi tích sông Choshui (CRAF), hệ thống tầng ngậm nước đa lớp và trạm quan trắc Tuku. Đặt trạm Tuku vào bối cảnh địa chất thủy văn của toàn khu vực.

#### 2.2 Datasets

##### 2.2.1 Multilayer aquifer-system compaction
Mô tả hệ thống giếng quan trắc nén lún đa lớp (MLCW) và phương pháp đo vòng từ. Dữ liệu thô được khớp với các mốc thời gian hàng tháng, chia thành 6 phân lớp độ sâu chuẩn (S1–S6, mỗi lớp 50m), và tính sai phân để lấy lượng nén lún hàng tháng.

##### 2.2.2 Groundwater level observations
Mô tả mạng lưới giếng quan trắc áp âm của WRA (cho các tầng ngậm nước từ 1 đến 4). Dữ liệu được tính trung bình từ ngày sang tháng, sau đó tính sai phân để thu được sự thay đổi cột nước thủy tĩnh (hydraulic head changes) hàng tháng.

##### 2.2.3 Vertical surface displacement
Mô tả trạm cGNSS TKJS. Dữ liệu chuỗi thời gian được mô hình hóa và tính sai phân để thu được lượng thay đổi chuyển vị bề mặt hàng tháng.

##### 2.2.4 Borehole lithological profile
Mô tả lõi khoan địa chất tại Tuku. Dữ liệu các loại trầm tích được tổng hợp lại cho khớp với 6 phân lớp 50m, từ đó tính ra tỷ lệ phần trăm của sỏi, cát thô, cát mịn, và hạt mịn. Các tỷ lệ này đóng vai trò cung cấp bối cảnh vật lý (đã qua phép biến đổi ILR) cho các mô hình độc lập, thay vì làm biến động lực theo thời gian.

---

### 3 Methodology

#### 3.1 Preparation of model inputs
🔒 *Mục 3.1.1 và mô hình biến dạng đã bị khóa.*

##### 3.1.1 Deformation time series model
Trình bày mô hình tham số (tuyến tính + dao động mùa + các bước nhảy offsets) được dùng để đồng bộ dữ liệu MLCW và cGNSS về cùng một mốc thời gian hàng tháng.

##### 3.1.2 Isometric logratio transformation of sediment composition
Mô tả phép biến đổi logarit tỷ lệ đẳng cự (ILR). Các tỷ lệ trầm tích (luôn cộng lại bằng 100%) được biến đổi thành 3 tọa độ ILR độc lập tuyến tính để loại bỏ hiện tượng đa cộng tuyến. Việc này giúp mô hình giữ nguyên đặc tính thạch học của từng phân lớp mà không cần gán ghép các tính chất cơ lý không đo đạc được.

##### 3.1.3 Assembly of monthly model inputs
Khẳng định rằng mỗi phân lớp độ sâu sử dụng một tập dữ liệu hiệu chỉnh (calibration dataset) riêng biệt và được xây dựng một mô hình hồi quy hoàn toàn độc lập.

**Bảng 2 (Tóm tắt biến dự báo):**
- **cGNSS displacement:** Đại diện cho tổng phản ứng biến dạng theo phương thẳng đứng tại Tuku.
- **Target-section hydraulic head:** Mô tả điều kiện thủy lực liên kết trực tiếp với phân lớp đang được dự báo.
- **Other-section hydraulic head:** Các biến dự báo mô tả điều kiện thủy lực ở các vị trí khác trong cùng mặt cắt.
- **Seasonal terms:** Biểu diễn các chu kỳ lặp lại hàng năm và nửa năm.

#### 3.2 Bayesian ridge regression
Giải thích lý do chọn thuật toán Bayesian ridge regression (tính năng điều chuẩn - regularization - hữu ích khi các biến dự báo có sự chồng chéo thông tin). Trình bày phương trình likelihood và phân phối tiên nghiệm, đồng thời làm rõ rằng mô hình này chỉ tìm kiếm mối liên hệ thống kê (statistical associations) chứ không thay thế cho các mô hình vật lý dòng chảy ngầm.

#### 3.3 Model evaluation and uncertainty

##### 3.3.1 Evaluation with delayed MLCW data availability
Mô tả thiết kế đánh giá tịnh tiến (walk-forward): chia dữ liệu thành các khối 6 tháng, sử dụng một khoảng thời gian hiệu chỉnh ban đầu, và tự động cập nhật lại mô hình tại ranh giới mỗi khối. Các thước đo hiệu năng bao gồm $R^2$, RMSE, MAE (đơn vị: mm/tháng). Sẽ có kèm sơ đồ TikZ mô tả chu kỳ cập nhật này.

##### 3.3.2 Prediction intervals
Trình bày khoảng dự báo Bayesian 90%, được tính toán từ phương sai dự báo hậu nghiệm. Phương pháp này cung cấp khoảng tin cậy (uncertainty bounds) bằng công thức giải tích cho mỗi dự báo ngay từ tháng đánh giá đầu tiên.

##### 3.3.3 Sensitivity to less frequent MLCW measurements
Mô tả 6 kịch bản giả định (chu kỳ đo đạc 6 hoặc 12 tháng × khoảng hiệu chỉnh ban đầu 36/60/96 tháng). Trình bày công thức tính nén lún quan trắc tích lũy tại điểm cuối (endpoint observations) và cách đánh giá sai số.

---

### 4 Results and discussion

##### 4.1 Monthly compaction estimation during delayed MLCW data availability
Báo cáo số lượng khối đánh giá, biên độ nén lún, và các chỉ số $R^2$/RMSE/MAE cho từng phân lớp.

**Nội dung cốt lõi dự kiến:**
Báo cáo sẽ chỉ ra rõ những phân lớp nào mô hình hoạt động tốt và những phân lớp nào thất bại. Ví dụ, phân lớp S5 (200–250 m) dự kiến có $R^2$ tiệm cận 0 hoặc âm. Lý luận cơ bản: không có giếng quan trắc áp âm nào được đặt ở đúng tầng trầm tích hạt mịn đang bị nén lún tại độ sâu này. Vì vậy, sự thay đổi cột nước được đưa vào mô hình là một thước đo vật lý không chính xác (imprecise proxy) so với áp lực lỗ rỗng thực tế. Phần này cũng sẽ báo cáo độ bao phủ (coverage) thực tế của khoảng dự báo 90%.

*(Lưu ý: Bảng 3 hiện đang để trống các số liệu (placeholder) cho đến khi chạy lại toàn bộ pipeline cho mô hình cuối cùng).*

##### 4.2 Sensitivity to MLCW measurements collected every six months
Báo cáo sai số hàng tháng và sai số tích lũy tại điểm cuối dưới chu kỳ đo đạc thưa 6 tháng/lần.

##### 4.3 Sensitivity to MLCW measurements collected every twelve months
Báo cáo kết quả dưới chu kỳ đo đạc 12 tháng/lần.

---

### 5 Conclusions
Nhắc lại mục tiêu nghiên cứu (dự báo tạm thời nén lún từng lớp trong điều kiện dữ liệu đo đạc bị trễ), tóm tắt nguồn dữ liệu và phương pháp Bayesian. Trình bày kết luận chính: liệu phương pháp này có khả thi để sử dụng trong thực tế nhằm thu hẹp khoảng trống dữ liệu cục bộ tại Tuku hay không, và khẳng định các giới hạn của mô hình.

---

### Discussion (discuss002.tex)
Phần thảo luận được cấu trúc lại để loại bỏ các số liệu cũ của Track B và làm rõ các cơ chế cốt lõi:
1. **§5.1:** Đánh giá tính hữu dụng của việc dự báo trong bối cảnh dữ liệu trễ 6 tháng (chống lại việc hiểu lầm đây là dự báo dài hạn vào tương lai).
2. **§5.2:** Giải thích sự khác biệt về hiệu năng giữa các độ sâu (nhấn mạnh điểm mù tại S5).
3. **§5.3:** Đánh giá giá trị của việc liên tục cập nhật mô hình khi có dữ liệu mới, và lợi thế thực tiễn của khoảng dự báo Bayesian.
4. **§5.4:** Phân tích tác động của các lịch trình đo đạc thưa thớt (kết hợp cả kịch bản 6 tháng và 12 tháng).
5. **§5.5:** Nêu rõ giới hạn ứng dụng: mô hình phản ánh đặc thù cục bộ của Tuku, không được phép chuyển giao trực tiếp bộ thông số này cho các trạm quan trắc khác.

---

### A Supplementary methodological details

##### A.1 Final predictor inventory
Liệt kê chi tiết các biến dự báo cuối cùng (không sử dụng tên thí nghiệm nội bộ).

##### A.2 Model fitting and update settings
Ghi lại các thông số kỹ thuật cấu hình và môi trường phần mềm nhằm đảm bảo tính minh bạch và khả năng tái tạo.

##### A.3 Prediction interval calibration
Làm rõ cơ sở toán học của phân phối dự báo hậu nghiệm Bayesian, chứng minh tính ưu việt ở chỗ phương pháp này không yêu cầu phải tích lũy dữ liệu sai số trong quá khứ để tính khoảng tin cậy.

##### A.4 Reduced-frequency MLCW measurement settings
Cung cấp công thức toán học chi tiết về điều kiện ràng buộc điểm cuối (endpoint constraint) dùng trong các kịch bản đo đạc thưa thớt.
