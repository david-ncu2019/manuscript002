# Manuscript Outline (v2.4) — Per-Section Bayesian Ridge Regression

Bản dàn ý này mô tả nội dung dự kiến cho từng phần (section) và tiểu mục (subsection). 
**Quy tắc cốt lõi:** Tuyệt đối không sử dụng các thuật ngữ nội bộ (như P0, P3, level1a, level1b, level1c, run_028, run_035, run_048, cross-section, own-section) trong bài viết. Chỉ sử dụng ngôn ngữ vật lý và dữ liệu để mô tả phương pháp và kết quả.

[NOTE: Gửi trợ lý viết bài: Hãy giữ câu văn trực diện. Nêu kết luận trước, sau đó mới đưa ra bằng chứng chứng minh. Không sử dụng các cụm từ sáo rỗng vô nghĩa như "It can be seen that" hay "Generally speaking". Hãy để các cơ chế vật lý dẫn dắt lời giải thích.]

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
Mục này xác định bài toán quan trắc: dữ liệu nén lún (MLCW) thường bị trễ và mạng lưới đang suy giảm. Tiếp theo, đánh giá các nghiên cứu tái tạo dữ liệu trước đây và chỉ ra khoảng trống nghiên cứu, từ đó nêu rõ mục tiêu của bài báo.

[NOTE: Điểm mới (novelty) chính cần định hình ở đây là "Nowcasting (Dự báo tạm thời) để vượt qua độ trễ dữ liệu trong một mạng lưới quan trắc đang suy thoái", chứ không phải "Độ phân giải theo chiều sâu".]
[ADD: Giới thiệu bài toán vận hành cụ thể tại CRAF: việc đọc dữ liệu MLCW thủ công bị trễ hoặc bị giảm tần suất làm cản trở các quyết định quản lý nước ngầm kịp thời. Định khung nghiên cứu này như một giải pháp vận hành (operational solution).]

---

### 2 Study Area and Datasets
🔒 *Locked.*

#### 2.1 Study Area Background
Mô tả Quạt bồi tích sông Choshui (CRAF), hệ thống tầng ngậm nước đa lớp và trạm quan trắc Tuku.

#### 2.2 Datasets
Mô tả 4 luồng dữ liệu: (2.2.1) Gia số nén lún MLCW, (2.2.2) Quan trắc mực nước ngầm (GWL) của WRA, (2.2.3) Chuyển vị bề mặt TKJS cGNSS, và (2.2.4) Hồ sơ địa tầng lõi khoan Tuku.

[NOTE: Đảm bảo mục §2.2.4 đề cập rằng tỷ lệ trầm tích cung cấp bối cảnh vật lý thông qua phép biến đổi ILR (Isometric Logratio), đóng vai trò làm nền tảng tĩnh (static base) chứ không phải là biến động lực.]

---

### 3 Methodology

#### 3.1 Preparation of model inputs
🔒 *Mục 3.1.1 và mô hình biến dạng đã bị khóa.*

##### 3.1.1 Deformation time series model
Trình bày mô hình tham số được dùng để đồng bộ dữ liệu MLCW và cGNSS về cùng một mốc thời gian hàng tháng.

##### 3.1.2 Isometric logratio transformation of sediment composition
Mô tả phép biến đổi ILR đối với tỷ lệ trầm tích (sỏi, cát thô, cát mịn, hạt mịn) để loại bỏ hiện tượng đa cộng tuyến trong khi vẫn giữ nguyên bối cảnh địa chất.

##### 3.1.3 Assembly of monthly model inputs
Khẳng định rằng mỗi phân lớp độ sâu sử dụng một tập dữ liệu hiệu chỉnh riêng biệt với một mô hình hồi quy độc lập.

[ADD: Trong Bảng 2, liệt kê rõ 4 nhóm biến dự báo: chuyển vị cGNSS, mực nước ngầm tại phân lớp mục tiêu, mực nước ngầm tại các phân lớp khác (đóng vai trò biến ứng viên đại diện cho điều kiện của toàn hệ thống), và các chu kỳ theo mùa.]

#### 3.2 Bayesian ridge regression
Giải thích lý do chọn Bayesian ridge regression nhờ tính năng điều chuẩn (regularization) khi xử lý các biến dự báo chồng chéo.

[NOTE: Làm rõ rằng mô hình này chỉ ánh xạ các mối liên hệ thống kê chứ không thay thế cho các phương trình dòng chảy ngầm tất định (deterministic groundwater flow equations).]

#### 3.3 Model evaluation and uncertainty

##### 3.3.1 Evaluation with delayed MLCW data availability
Mô tả thiết kế đánh giá tịnh tiến (walk-forward): các khối 6 tháng, hiệu chỉnh ban đầu, và tự động cập nhật lại mô hình.

##### 3.3.2 Prediction intervals
Trình bày khoảng dự báo Bayesian 90% được rút ra từ phương sai dự báo hậu nghiệm.

##### 3.3.3 Sensitivity to less frequent MLCW measurements
Mô tả các kịch bản thực nghiệm: quan sát tổng độ lún mỗi 6 hoặc 12 tháng.

[NOTE: Giải thích rằng phân tích độ nhạy này trực tiếp kiểm tra một thực tế vận hành (cắt giảm lấy mẫu do ngân sách) chứ không chỉ đơn thuần là kiểm tra độ bền vững toán học.]

---

### 4 Results

*(Lưu ý: Phần Thảo luận (Discussion) hiện đã được tách hoàn toàn sang Mục 5. Mục 4 chỉ chứa các báo cáo khách quan, trung tính về các chỉ số đo lường.)*

##### 4.1 Monthly compaction estimation during delayed MLCW data availability
Báo cáo các khối đánh giá, biên độ nén lún quan trắc được, và các chỉ số cấp phân lớp ($R^2$, RMSE, MAE).

[ADD: Báo cáo công bằng các chỉ số cho tất cả các phân lớp (S1-S6). Nêu rõ (explicitly state) mức $R^2$ tiệm cận 0 hoặc âm của phân lớp 200–250 m (S5). Không cần biện minh ở đây; chỉ cần nêu đúng kết quả số liệu.]
[NOTE: Đảm bảo Bảng 3 được cập nhật với các chỉ số từ lần chạy pipeline cuối cùng khi có số liệu.]

##### 4.2 Sensitivity to reduced-frequency MLCW measurements
Báo cáo sai số hàng tháng và sai số tại điểm cuối (endpoint errors) trong các kịch bản chu kỳ 6 tháng và 12 tháng.

[ADD: Gộp các tiểu mục 4.2 và 4.3 trước đây thành mục duy nhất này. So sánh sai số tại điểm cuối giữa hai lịch trình đo đạc.]
[NOTE: Trình bày dữ liệu này như một "đường cong đánh đổi" (trade-off curve) giữa chi phí đi thực địa và độ không chắc chắn của ước lượng.]

---

### 5 Discussion
*(Nội dung đề xuất: discuss002.tex)*

[NOTE: Giọng văn ở phần này phải là của một Cố vấn Vận hành (operational advisor). Thừa nhận rằng mạng lưới quan trắc vật lý đang suy thoái, và giải thích cách mô hình giúp người ra quyết định điều hướng hạn chế này mà không che đậy các điểm mù vật lý.]

##### 5.1 Temporary completion of delayed monitoring records
[ADD: Lập luận rằng giá trị chính của mô hình là "nowcasting" để vượt qua độ trễ 6 tháng khi phát hành dữ liệu. Các ước lượng hàng tháng kịp thời cho phép nhà quản lý áp dụng các lệnh hạn chế bơm hút trước khi nén lún không đàn hồi (irreversible inelastic compaction) tích lũy.]
[NOTE: Phân biệt rõ ràng điều này với dự báo dài hạn (long-term forecasting). Nhấn mạnh rằng mô hình dựa trên các yếu tố dẫn động (drivers) xảy ra cùng thời điểm trong cùng tháng đó.]

##### 5.2 Differences in performance with depth
[ADD: Giải thích lý do vật lý cho điểm mù ở S5: không có giếng quan trắc áp âm nào được đặt ở tầng trầm tích hạt mịn đang lún tại độ sâu 200–250 m. Do đó, dữ liệu GWL hiện có là một thước đo vật lý không chính xác (imprecise proxy).]
[NOTE: Định khung vấn đề này thành một "Lời cảnh báo mạng lưới" (Network Warning). Machine learning không thể tự bịa ra tính chất vật lý nếu khả năng quan trắc hoàn toàn bằng không. Nếu người ra quyết định gỡ bỏ cảm biến khỏi các tầng đang lún mạnh, khả năng nowcast sẽ vĩnh viễn bị mất.]

##### 5.3 Value of updating models and prediction intervals
[ADD: Thảo luận về độ bao phủ thực tế (empirical coverage) và độ rộng của các khoảng dự báo Bayesian 90%.]
[NOTE: Nhấn mạnh rằng các khoảng này cung cấp cho người ra quyết định một thước đo định lượng về độ không chắc chắn ngay từ ngày đầu tiên, mà không cần phải có một tập dữ liệu kiểm tra lịch sử lưu trữ riêng.]

##### 5.4 Implications of reduced measurement frequency
[ADD: Tổng hợp các phát hiện từ mục §4.2. Giải thích rằng mặc dù việc lấy mẫu thưa hơn (ví dụ: 12 tháng thay vì 6 tháng) giúp giảm chi phí vận hành, nó lại làm nới rộng độ không chắc chắn của các ước lượng hàng tháng nằm xen kẽ.]
[NOTE: Định khung đây là một công cụ cho phép Cục Tài nguyên Nước (WRA) quyết định xem họ có thể giảm tần suất lấy mẫu an toàn đến mức nào mà không tự làm mù mình trước các sự kiện lún nghiêm trọng.]

##### 5.5 Limitations and practical scope
[ADD: Khẳng định rằng các thông số của mô hình mang tính cục bộ nghiêm ngặt (strictly local) đối với đặc thù thạch học, cấu hình giếng và lịch sử ứng suất của trạm Tuku.]
[NOTE: Ngăn chặn việc thổi phồng kết quả. Giải thích rằng mặc dù phương pháp luận có thể chuyển giao hoàn toàn, các hệ số hồi quy cụ thể không thể được sao chép/dán trực tiếp sang một trạm khác.]

---

### 6 Conclusions

Nhắc lại mục tiêu vận hành (nowcasting độ lún từng lớp trong điều kiện dữ liệu bị trễ/suy thoái). Tóm tắt các nguồn dữ liệu và phương pháp Bayesian.

[ADD: Đưa ra kết luận chính: Phương pháp này đã thành công trong việc kết nối các khoảng trống dữ liệu thời gian tại các phân lớp được quan trắc tốt, cung cấp một sự đánh đổi vận hành (operational trade-off) cho các mạng lưới bị thâm hụt ngân sách, nhưng nó không thể vượt qua các điểm mù vật lý cơ bản tại những nơi vắng bóng cảm biến đo đạc.]

---

### A Supplementary methodological details

##### A.1 Final predictor inventory
[NOTE: Lập một bảng sạch sẽ các biến dự báo cuối cùng đã được đóng băng từ lần chạy pipeline. Không chứa các thẻ thí nghiệm nội bộ.]

##### A.2 Model fitting and update settings
[NOTE: Ghi lại cấu hình kỹ thuật để đảm bảo khả năng tái tạo.]

##### A.3 Prediction interval calibration
[NOTE: Cung cấp chứng minh toán học của phân phối dự báo hậu nghiệm, giải thích lý do tại sao nó hoạt động được mà không cần kho lưu trữ sai số tích lũy.]

##### A.4 Reduced-frequency MLCW measurement settings
[NOTE: Cung cấp công thức toán học chi tiết về điều kiện ràng buộc điểm cuối (endpoint constraint) dùng trong các kịch bản đo đạc thưa thớt.]
