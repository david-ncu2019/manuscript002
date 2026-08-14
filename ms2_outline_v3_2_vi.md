# Manuscript Outline (v3.2) — Per-Section Bayesian Ridge Regression

Bản dàn ý này mô tả nội dung dự kiến cho từng phần (section) và tiểu mục (subsection).
**Quy tắc cốt lõi:** Tuyệt đối không sử dụng các thuật ngữ nội bộ (như P0, P3, level1a, level1b, level1c, run_028, run_035, run_048, cross-section, own-section) trong bài viết. Chỉ sử dụng ngôn ngữ vật lý và dữ liệu để mô tả phương pháp và kết quả.

[NOTE: Gửi trợ lý viết bài: Hãy giữ câu văn trực diện. Nêu kết luận trước, sau đó mới đưa ra bằng chứng chứng minh. Không sử dụng các cụm từ sáo rỗng vô nghĩa như "It can be seen that" hay "Generally speaking". Hãy để các cơ chế vật lý dẫn dắt lời giải thích.]

> **Quyết định nền tảng (Governing decision):** Mỗi phân lớp độ sâu (depth section) được mô hình hóa hoàn toàn độc lập bằng thuật toán Bayesian ridge regression. Các biến dự báo (predictors) bao gồm: thay đổi mực nước ngầm tại chính phân lớp đó, thay đổi mực nước ngầm tại các phân lớp khác, chuyển vị bề mặt theo phương thẳng đứng, và các chu kỳ theo mùa. Bài báo sẽ báo cáo kết quả đánh giá theo phương pháp tịnh tiến thời gian (walk-forward) tại trạm Tuku.

**Điểm mới trong v3.2:** §4 Results và §5 Discussion được gộp thành một mục duy nhất, `§4 Results and Discussion`, với 5 tiểu mục (4.1–4.5). Mỗi tiểu mục nêu luận điểm (claim), luận cứ/số liệu hỗ trợ (evidence), và giải thích vật lý (interpretation) cùng một chỗ, theo đúng thứ tự đó, trong cùng một đoạn văn — không bao giờ đưa giải thích trước con số làm nền cho nó. Cách này thay thế cấu trúc tách rời Results (§4) / Discussion (§5) của v3.1; không có thay đổi cấu trúc nào khác so với v3.1. Conclusions giờ là §5, Phụ lục vẫn là §A.

Hai thí nghiệm vẫn giữ mức ưu tiên ngang nhau trên đường găng (critical path) của bài báo, cả hai đều chưa có script cho thiết kế mô hình theo từng phân lớp (per-section):
1. **Blocker #1** — độ nhạy khi giảm tần suất đo MLCW (mỗi 6 hoặc 12 tháng), tại §3.3.3 / §4.3 / A.4.
2. **Blocker #2** — độ nhạy khi trạm ngừng quan trắc vĩnh viễn: mô hình được hiệu chỉnh (fit) một lần duy nhất với 3, 5, hoặc 8 năm dữ liệu, sau đó dự báo tiếp mà không hiệu chỉnh lại và không có thêm dữ liệu MLCW đầu vào, để xem sai số ước lượng tăng lên như thế nào theo thời gian. Xem §3.3.4 / §4.4 / A.5.

Cả hai blocker đều chưa có script cho thiết kế theo từng phân lớp. Tiền lệ gần nhất cho cả hai là phân tích độ nhạy "không cập nhật" (no-update) hiện có, vốn được xây dựng cho thiết kế mô hình gộp (pooled) trước đây — xem ghi chú tại §3.3.4 để biết tài liệu bàn giao chính xác.

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

[NOTE: Chưa sẵn sàng để viết với số liệu thật. Bảng kết quả walk-forward theo từng phân lớp cho thiết kế mô hình này chưa được tổng hợp — hiện chỉ có kết quả thô theo từng fold, chưa gộp lại. Xem D:\112_PROJECT_002\discussions\20260805_outline_v2_4_section_to_codebase_map.md để biết chi tiết.]

##### 3.3.2 Prediction intervals
Trình bày khoảng dự báo Bayesian 90% được rút ra từ phương sai dự báo hậu nghiệm.

##### 3.3.3 Sensitivity to less frequent MLCW measurements
Mô tả các kịch bản thực nghiệm: quan sát tổng độ lún mỗi 6 hoặc 12 tháng.

[NOTE: Giải thích rằng phân tích độ nhạy này trực tiếp kiểm tra một thực tế vận hành (cắt giảm lấy mẫu do ngân sách) chứ không chỉ đơn thuần là kiểm tra độ bền vững toán học.]

[NOTE: Chưa sẵn sàng để viết với số liệu thật. **Blocker #1.** Chưa có lần chạy nào cho kịch bản giảm tần suất dưới thiết kế mô hình này — chỉ có một phân tích ngừng quan trắc hoàn toàn, và phân tích đó được xây dựng cho một thiết kế mô hình khác (mô hình gộp/pooled). Xem D:\112_PROJECT_002\discussions\20260805_outline_v2_4_section_to_codebase_map.md để biết chi tiết.]

##### 3.3.4 Sensitivity to permanent monitoring stoppage
Mô tả kịch bản thực nghiệm thứ hai, khác với §3.3.3: mô hình được hiệu chỉnh (fit) một lần duy nhất, sử dụng 3, 5, hoặc 8 năm dữ liệu huấn luyện, sau đó tạo ra các dự báo mà không hiệu chỉnh lại và không nhận thêm dữ liệu MLCW cho phần còn lại của chuỗi thời gian. Kịch bản này kiểm tra điều gì xảy ra nếu một trạm ngừng báo cáo dữ liệu MLCW vĩnh viễn, thay vì chỉ giảm theo lịch trình cố định.

[NOTE: Giải thích rằng kịch bản này trả lời một câu hỏi vận hành khác với §3.3.3. §3.3.3 hỏi "có thể giảm tần suất lấy mẫu đến mức nào mà vẫn còn kiểm tra định kỳ?" §3.3.4 hỏi "nếu một trạm ngừng hẳn sau 3, 5, hoặc 8 năm, ước lượng sẽ trôi đi bao xa trước khi trở nên không còn dùng được?"]

[NOTE: Chưa sẵn sàng để viết với số liệu thật. **Blocker #2**, ưu tiên ngang với Blocker #1 ở trên. Chưa có script nào cho kịch bản này dưới thiết kế mô hình theo từng phân lớp. Sử dụng cùng tiền lệ thực nghiệm với tài liệu bàn giao phân tích độ nhạy "không cập nhật" hiện có tại `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\docs\20260802_run048_tuku_no_update_sensitivity_manuscript_handoff.md` — thiết kế trong tài liệu đó (hiệu chỉnh một lần, dự báo một khoảng thời gian cố định không hiệu chỉnh lại, đo sai số tích lũy tại điểm cuối) được xây dựng cho mô hình gộp ở khoảng thời gian 6 và 12 tháng. Kịch bản này cần thiết kế tương đương được xây dựng cho mô hình BRR theo từng phân lớp, mở rộng ra các khoảng thời gian 3, 5, và 8 năm. Xem D:\112_PROJECT_002\discussions\20260805_outline_v2_4_section_to_codebase_map.md để biết thêm chi tiết.]

---

### 4 Results and Discussion
*(Nội dung đề xuất: gộp vào results002.tex; discuss002.tex không còn được biên dịch trong mục này)*

[NOTE: Giọng văn ở phần này phải là của một Cố vấn Vận hành (operational advisor). Thừa nhận rằng mạng lưới quan trắc vật lý đang suy thoái, và giải thích cách mô hình giúp người ra quyết định điều hướng hạn chế này mà không che đậy các điểm mù vật lý. Mỗi luận điểm dưới đây nêu số liệu trước, sau đó giải thích vật lý ngay sau đó, trong cùng một đoạn văn — không bao giờ đưa giải thích trước con số làm nền cho nó.]

##### 4.1 Overall nowcasting performance and depth-dependence
**Luận điểm (Claim):** mô hình theo từng phân lớp nowcast độ lún hàng tháng với độ chính xác cấp phân lớp thay đổi có hệ thống theo độ sâu.

**Luận cứ (Evidence):** các khối đánh giá, biên độ nén lún quan trắc được, và các chỉ số cấp phân lớp ($R^2$, RMSE, MAE) cho tất cả sáu phân lớp (S1–S6). Báo cáo công bằng các chỉ số cho tất cả các phân lớp, bao gồm mức $R^2$ tiệm cận 0 hoặc âm của phân lớp 200–250 m (S5), nêu ngay bên cạnh năm phân lớp khác.

**Giải thích (Interpretation, cùng tiểu mục, ngay sau số liệu):** hiệu suất yếu của S5 xuất phát từ một lỗ hổng quan trắc vật lý, không phải một thất bại của mô hình. Không có giếng quan trắc áp âm nào được đặt ở tầng trầm tích hạt mịn đang lún tại độ sâu 200–250 m, do đó biến dự báo mực nước ngầm hiện có tại phân lớp này là một thước đo không chính xác cho điều kiện áp suất lỗ rỗng thực sự đang gây nén lún ở đó. Định khung vấn đề này thành một "Lời cảnh báo mạng lưới" (Network Warning): machine learning không thể tự bịa ra tính chất vật lý nếu khả năng quan trắc hoàn toàn bằng không. Nếu người ra quyết định gỡ bỏ cảm biến khỏi các tầng đang lún mạnh, khả năng nowcast sẽ vĩnh viễn bị mất.

[NOTE: Nêu giải thích vật lý này đúng một lần. Không lặp lại lý do S5 ở nơi khác trong tiểu mục này hoặc trong §4.5 Limitations.]
[NOTE: Cũng nêu, nếu số liệu cho phép, rằng giá trị chính của mô hình là vượt qua độ trễ khi phát hành dữ liệu: các ước lượng hàng tháng kịp thời cho phép nhà quản lý áp dụng các lệnh hạn chế bơm hút trước khi nén lún không đàn hồi (irreversible inelastic compaction) tích lũy. Phân biệt rõ ràng điều này với dự báo dài hạn (long-term forecasting) — mô hình dựa trên các yếu tố dẫn động (drivers) xảy ra cùng thời điểm trong cùng tháng đó.]
[NOTE: Chưa sẵn sàng để viết với số liệu thật. Bảng 3 không thể hoàn thiện cho đến khi bảng walk-forward theo từng phân lớp của §3.3.1 tồn tại; chiều hướng của phân lớp yếu nhất (S5, âm mạnh) đã biết trước, nhưng bảng đầy đủ 6 phân lớp thì chưa có. Xem D:\112_PROJECT_002\discussions\20260805_outline_v2_4_section_to_codebase_map.md để biết chi tiết.]

##### 4.2 Value of prediction intervals
**Luận điểm (Claim):** khoảng dự báo Bayesian 90% cung cấp cho người ra quyết định một thước đo định lượng, dùng được ngay, về độ không chắc chắn, mà không cần một tập dữ liệu kiểm tra lịch sử lưu trữ riêng.

**Luận cứ (Evidence):** độ bao phủ thực tế (empirical coverage) và độ rộng của khoảng dự báo hậu nghiệm, theo từng phân lớp.

**Giải thích (Interpretation, cùng tiểu mục):** định khung điều này là có sẵn "ngay từ ngày đầu tiên" triển khai tại một trạm mới hoặc mới quan trắc lại, khác với các phương pháp cần một kho lưu trữ sai số tích lũy trước khi có thể định lượng độ không chắc chắn.

##### 4.3 Sensitivity to reduced-frequency measurements
**Luận điểm (Claim):** giảm tần suất kiểm tra MLCW từ hàng tháng xuống mỗi 6 hoặc 12 tháng là một sự đánh đổi vận hành có thật, không chỉ là một phép kiểm tra độ bền vững toán học.

**Luận cứ (Evidence):** sai số hàng tháng và sai số tại điểm cuối (endpoint errors) trong các kịch bản chu kỳ 6 tháng và 12 tháng, gộp vào một bảng duy nhất so sánh sai số tại điểm cuối giữa hai lịch trình đo đạc, theo từng phân lớp độ sâu và gộp trên toàn mặt cắt.

**Giải thích (Interpretation, cùng tiểu mục):** trình bày dữ liệu này như một "đường cong đánh đổi" (trade-off curve) giữa chi phí đi thực địa và độ không chắc chắn của ước lượng. Tổng hợp trực tiếp vào khung vận hành: đây là công cụ cho phép Cục Tài nguyên Nước (WRA) quyết định xem họ có thể giảm tần suất lấy mẫu an toàn đến mức nào mà không tự làm mù mình trước các sự kiện lún nghiêm trọng.

[NOTE: Chưa sẵn sàng để viết với số liệu thật. **Phụ thuộc vào Blocker #1** (§3.3.3), hiện chưa có lần chạy kịch bản nào cho thiết kế mô hình này. Xem D:\112_PROJECT_002\discussions\20260805_outline_v2_4_section_to_codebase_map.md để biết chi tiết.]

##### 4.4 Sensitivity to permanent monitoring stoppage
**Luận điểm (Claim):** mục này trả lời một câu hỏi vận hành khác với §4.3. §4.3 hỏi "có thể giảm tần suất lấy mẫu đến mức nào mà vẫn còn kiểm tra định kỳ?" Mục này hỏi "nếu một trạm ngừng hẳn vĩnh viễn, ước lượng sẽ trôi đi bao xa trước khi không còn dùng được?"

**Luận cứ (Evidence):** sai số ước lượng tích lũy tăng lên như thế nào theo các khoảng thời gian không hiệu chỉnh lại 3, 5, và 8 năm, theo từng phân lớp độ sâu và cho toàn bộ mặt cắt quan trắc. Báo cáo sai số tích lũy tại điểm cuối (MAE, RMSE, độ chệch/bias, đơn vị mm) tại mỗi khoảng thời gian, cộng với sai số chuẩn hóa theo khoảng thời gian (mm/tháng) báo cáo kèm theo — chứ không thay thế — sai số tích lũy tuyệt đối.

**Giải thích (Interpretation, cùng tiểu mục):** nêu rõ mô hình suy giảm dần đều hay sụp đổ đột ngột sau một mốc thời gian nào đó, khi có số liệu, định khung như một câu hỏi hỗ trợ ra quyết định cho WRA: trạm này có thể ngừng quan trắc bao lâu trước khi ước lượng không còn đáng tin cậy cho quyết định hạn chế bơm hút?

[NOTE: Đại lượng có ý nghĩa vật lý thực sự đối với người vận hành khi quyết định một trạm có thể không được đọc trong bao lâu là sai số tích lũy tuyệt đối tại điểm cuối, không phải tỷ lệ chuẩn hóa theo thời gian — tỷ lệ chuẩn hóa có thể giảm ngay cả khi sai số tuyệt đối tăng, do hiện tượng triệt tiêu một phần, theo đúng lưu ý đã ghi trong tài liệu bàn giao phân tích độ nhạy "không cập nhật". Không bao giờ báo cáo tỷ lệ chuẩn hóa như một con số tiêu đề độc lập.]
[NOTE: Chưa sẵn sàng để viết với số liệu thật. **Phụ thuộc vào Blocker #2** (§3.3.4), ưu tiên ngang với Blocker #1. Chưa có script nào cho kịch bản này dưới thiết kế mô hình theo từng phân lớp. Tiền lệ gần nhất là tài liệu bàn giao phân tích độ nhạy "không cập nhật" được xây dựng cho mô hình gộp ở khoảng thời gian 6/12 tháng (`D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\docs\20260802_run048_tuku_no_update_sensitivity_manuscript_handoff.md`), cần thiết kế tương đương được xây dựng cho mô hình BRR theo từng phân lớp, mở rộng ra các khoảng thời gian 3/5/8 năm. Xem D:\112_PROJECT_002\discussions\20260805_outline_v2_4_section_to_codebase_map.md để biết chi tiết.]

##### 4.5 Limitations and practical scope
**Luận điểm (Claim):** mô hình đã hiệu chỉnh mang tính cục bộ nghiêm ngặt (strictly local) đối với đặc thù thạch học, cấu hình giếng và lịch sử ứng suất của trạm Tuku; chỉ có phương pháp luận, không phải các hệ số đã hiệu chỉnh, là có thể chuyển giao.

**Giải thích (Interpretation, không có luận cứ mới ở đây):** ngăn chặn việc thổi phồng kết quả. Nêu rõ rằng mặc dù phương pháp luận có thể chuyển giao hoàn toàn, các hệ số hồi quy cụ thể không thể được sao chép/dán trực tiếp sang một trạm khác.

---

### 5 Conclusions

Nhắc lại mục tiêu vận hành (nowcasting độ lún từng lớp trong điều kiện dữ liệu bị trễ/suy thoái). Tóm tắt các nguồn dữ liệu và phương pháp Bayesian.

[ADD: Đưa ra kết luận chính: Phương pháp này đã thành công trong việc kết nối các khoảng trống dữ liệu thời gian tại các phân lớp được quan trắc tốt, cung cấp một sự đánh đổi vận hành (operational trade-off) cho các mạng lưới bị thâm hụt ngân sách, nhưng nó không thể vượt qua các điểm mù vật lý cơ bản tại những nơi vắng bóng cảm biến đo đạc.]

[NOTE: Khi viết kết luận này, hãy học theo VĂN PHONG (không phải nội dung hay phương pháp) của các bài báo sau đây:
- Hung et al. (2025), "Near real-time subsidence monitoring and AI forecasting with multi-depth extensometers" — `D:\001_LITERATURE_v2\ZOTERO_storage\storage\GFDMNS9S\`
- Liu et al. (2025), "Deep learning time-series modeling for assessing land subsidence under reduced groundwater use" — `D:\001_LITERATURE_v2\ZOTERO_storage\storage\LAML2LM8\`
- Liu et al. (2023), "Reconstructing missing time-varying land subsidence data using back propagation neural network" — `D:\001_LITERATURE_v2\ZOTERO_storage\storage\6TYF2YLR\`
- Wang et al. (2025), "A case study on the application of a data-driven (XGBoost) approach on the environmental and socio-economic..." — `D:\001_LITERATURE_v2\ZOTERO_storage\storage\BNZ9BUGJ\`
- Nguyen et al. (2024), "Quantitative Evaluations of Pumping-Induced Land Subsidence and Mitigation Strategies" — `D:\001_LITERATURE_v2\ZOTERO_storage\storage\LMTIPY87\`]

---

### A Supplementary methodological details

##### A.1 Final predictor inventory
[NOTE: Lập một bảng sạch sẽ các biến dự báo cuối cùng đã được đóng băng từ lần chạy pipeline. Không chứa các thẻ thí nghiệm nội bộ.]
[NOTE: Đã sẵn sàng một phần. Danh sách biến dự báo có thể được tạo theo yêu cầu từ logic pipeline hiện có, nhưng chưa xuất ra bảng tĩnh nào. Xem D:\112_PROJECT_002\discussions\20260805_outline_v2_4_section_to_codebase_map.md để biết chi tiết.]

##### A.2 Model fitting and update settings
[NOTE: Ghi lại cấu hình kỹ thuật để đảm bảo khả năng tái tạo.]

##### A.3 Prediction interval calibration
[NOTE: Cung cấp chứng minh toán học của phân phối dự báo hậu nghiệm, giải thích lý do tại sao nó hoạt động được mà không cần kho lưu trữ sai số tích lũy.]

##### A.4 Reduced-frequency MLCW measurement settings
[NOTE: Cung cấp công thức toán học chi tiết về điều kiện ràng buộc điểm cuối (endpoint constraint) dùng trong các kịch bản đo đạc thưa thớt 6 và 12 tháng (§3.3.3).]
[NOTE: Chưa sẵn sàng để viết với số liệu thật. Công thức ràng buộc đã được thiết kế nhưng chưa chạy cho thiết kế mô hình này — cùng phụ thuộc với §3.3.3/§4.3 (Blocker #1). Xem D:\112_PROJECT_002\discussions\20260805_outline_v2_4_section_to_codebase_map.md để biết chi tiết.]

##### A.5 Permanent-stoppage scenario settings
[NOTE: Cung cấp công thức toán học chi tiết dùng trong các kịch bản độ nhạy không hiệu chỉnh lại ở 3, 5, và 8 năm (§3.3.4): độ dài cửa sổ huấn luyện, độ dài khoảng thời gian dự báo, và ràng buộc không hiệu chỉnh lại.]
[NOTE: Chưa sẵn sàng để viết với số liệu thật. Chưa có script nào cho kịch bản này — cùng phụ thuộc với §3.3.4/§4.4 (Blocker #2). Xem D:\112_PROJECT_002\discussions\20260805_outline_v2_4_section_to_codebase_map.md để biết chi tiết.]
