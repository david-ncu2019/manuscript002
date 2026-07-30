# Kho đường dẫn: mô hình Bayesian Ridge cho ML Nowcasting (run_048)

**Ngày tạo:** 2026-07-28
**Repo gốc:** `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3`
**Mục đích:** liệt kê các folder và file liên quan tới mô hình Bayesian Ridge, các bước xử lý số liệu, cách chia driving features (biến điều khiển đưa vào mô hình), và các kết quả đủ tiêu chuẩn để đưa vào bài báo. Mọi đường dẫn dưới đây là đường dẫn tuyệt đối (absolute path), đã được kiểm tra tồn tại trên đĩa vào ngày tạo file này.

Bối cảnh vật lý một câu: mô hình này dự đoán độ lún đất (compaction) hàng tháng cho từng lớp đất sâu 50 m (S1 đến S6) tại 5 trạm quan trắc MLCW ở đồng bằng phù sa Choushui, dùng biến động mực nước ngầm và biến dạng bề mặt InSAR/GPS làm đầu vào.

---

## 1. Tài liệu tổng quan bắt buộc đọc trước

Đọc các file này trước để hiểu bối cảnh và trạng thái hiện tại của dự án:

| File | Nội dung |
|---|---|
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\PROGRESS.md` | Trạng thái hiện tại, cổng chặn (gate) đang mở, việc cần làm tiếp theo |
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\README.md` | Điểm vào của toàn bộ pipeline ML nowcasting |
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\RULES.md` | Quy tắc bắt buộc khi làm việc trong thư mục này |
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\STATUS.md` | Trạng thái chi tiết của từng run |
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\docs\20260728_run048_manuscript_evidence.md` | Bảng bằng chứng cho bài báo: P3/P7/P_XS_LAG/P8, đủ R², RMSE, MAE, khoảng tin cậy, kiểm định ý nghĩa thực tế |
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\diagnostics\ROOT_CAUSE_REPORT.md` | Vì sao không phải ô (trạm, lớp đất) nào cũng đạt R² ≥ 0.6 |
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\002_docs\references\pipeline\gwl_kriging_architecture.md` | Cơ chế nội suy Kriging cho mực nước ngầm — nguồn gốc dữ liệu GWL đưa vào mô hình |

---

## 2. Mô hình Bayesian Ridge — script chạy chính

Mô hình sản xuất hiện tại là **BayesianRidge regression** (hồi quy tuyến tính có điều chuẩn kiểu Bayes), áp dụng cho từng (trạm, lớp đất, tháng) như một hàng dữ liệu gộp chung (pooled).

### 2.1. Script huấn luyện và đánh giá mô hình (thư mục `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\`)

| File | Vai trò |
|---|---|
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\run048_pipeline.py` | Điều phối toàn bộ pipeline: nạp snapshot dữ liệu, chạy đánh giá, ghi checkpoint |
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\run048_evaluation.py` | Nơi thực sự gọi `BayesianRidge().fit()` — hàm `fit_bayesian_fold()` là lõi huấn luyện mô hình |
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\run048_feature_registry.py` | Định nghĩa các "profile" đặc trưng (feature) — tức là các bộ biến điều khiển khác nhau đưa vào mô hình (P0, P3, P7, P8, P_XS_LAG...) |
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\run048_diagnostics.py` | Kiểm tra chất lượng số liệu trước khi fit: cột phương sai bằng 0, cột trùng lặp, hạng ma trận (rank), số điều kiện (condition number) |
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\run048_snapshot.py` | Xây dựng bảng đặc trưng (feature table) từ dữ liệu thô — đây là bước xử lý số liệu chính |
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\run048_stage_finalize.py` | Ra quyết định GO/STOP dựa trên khoảng tin cậy bootstrap của ΔR² so với mô hình gốc |
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\run048_summaries.py` | Tính chênh lệch (delta) RMSE/MAE/R² giữa các profile, kèm khoảng tin cậy bootstrap |
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\run048_figures.py` | Vẽ hình: hệ số hồi quy, dự đoán so với quan sát |

### 2.2. Kết quả huấn luyện đã đóng băng (frozen, dùng được cho bài báo)

Thư mục kết quả gốc, đã qua kiểm định và khóa bằng SHA-256:

```
D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\results\
```

Các file quan trọng trong đó:

| File | Nội dung |
|---|---|
| `predictions.parquet` | Toàn bộ giá trị dự đoán so với giá trị quan sát thực tế |
| `standardized_coefficients.parquet` | Hệ số hồi quy đã chuẩn hóa — dùng để vẽ hình hệ số cho bài báo |
| `fold_metrics.parquet` | RMSE, MAE, R² cho từng fold (từng lần huấn luyện/kiểm tra) |
| `paired_deltas.json` | Chênh lệch hiệu năng giữa các profile, kèm khoảng tin cậy 95% |
| `summary_metrics.json` | Tóm tắt chỉ số hiệu năng toàn cục |
| `run_provenance.json` | Ghi lại mã nguồn, phiên bản thư viện đã dùng để tạo ra kết quả này (để tái lập) |
| `artifact_manifest.json` | Danh sách toàn bộ file kết quả kèm mã băm SHA-256 (bằng chứng chống sửa đổi) |

---

## 3. Các bước xử lý số liệu (data processing)

### 3.1. Dữ liệu thô (raw data), thư mục `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\raw_data\`

| Thư mục con | Nội dung |
|---|---|
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\raw_data\01_mlcw_compaction\` | Số liệu lún đất đo bằng vòng từ (magnetic ring) tại giếng MLCW — đây là biến mục tiêu (target) của mô hình |
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\raw_data\02_gwl_wells_raw\` | Mực nước ngầm thô từ các giếng quan trắc |
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\raw_data\03_gps_subsidence\` | Biến dạng bề mặt đo bằng GPS |
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\raw_data\04_rainfall\` | Lượng mưa theo trạm |
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\raw_data\05_borehole_materials\` | Địa chất giếng khoan (sỏi, cát, sét) — dùng để tính đặc trưng ILR (tỷ lệ vật liệu) |
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\raw_data\07_section_well_assignment\` | Quy tắc gán giếng quan trắc mực nước ngầm cho từng lớp đất (section) của từng trạm |
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\raw_data\08_gwl_at_mlcw_monthly\` | Mực nước ngầm hàng tháng đã nội suy Kriging — phiên bản gốc (run_017, 2010–2025) |
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\raw_data\08_gwl_at_mlcw_monthly_extended\` | Mực nước ngầm hàng tháng phiên bản mở rộng (v5/run_021, 2000–2025, quy tắc gán giếng chặt hơn) |

### 3.2. Bảng đặc trưng đã xây dựng (snapshot), thư mục `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\input_data\`

Đây là kết quả sau khi xử lý xong dữ liệu thô — bảng này mới thực sự được đưa vào huấn luyện mô hình:

| Thư mục | Số đặc trưng | Ghi chú |
|---|---|---|
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\input_data\20260718_run048_v1\` | 72 (P0, cơ sở) | Bảng gốc chưa thêm đặc trưng thử nghiệm |
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\input_data\20260724_run048_stage_a\` | +thêm cột P7 | Thử nghiệm: tương tác mực nước ngầm × vật liệu cùng lớp đất |
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\input_data\20260724_run048_stage_b\` | 203 | Thử nghiệm: mực nước ngầm trễ thời gian (lagged) từ các lớp đất khác |
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\input_data\20260724_run048_stage_c\` | 239 | Thử nghiệm: tương tác mực nước ngầm chéo lớp × mùa mưa/khô |

Mỗi thư mục snapshot có `manifest.json` (mô tả số cột, số hàng theo trạm) và `schema.json` (kiểu dữ liệu từng cột).

### 3.3. Script xử lý số liệu, thư mục `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\`

| File | Bước xử lý |
|---|---|
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\run048_snapshot.py` | Gộp dữ liệu thô thành bảng đặc trưng theo (trạm, lớp đất, tháng); tính các cột GWL biến thiên (dGWL), GWL trễ thời gian, đặc trưng theo mùa |
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\run048_feature_registry.py` | Định nghĩa chính xác tên và công thức của từng cột đặc trưng |

---

## 4. Cách chia driving features (biến điều khiển đưa vào mô hình)

"Driving features" ở đây là các nhóm biến vật lý dùng để dự đoán độ lún. Cách chia được định nghĩa trong `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\run048_feature_registry.py` và mô tả lại bằng tiếng Anh trong `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\CLAUDE.md` (mục "Feature schema").

| Nhóm đặc trưng | Ví dụ cột | Ý nghĩa vật lý |
|---|---|---|
| Biến động chung (shared dynamic) | `dS_total`, `d2S_total`, `rain_sum3/6/12` | Biến dạng bề mặt tổng và gia tốc của nó; lượng mưa tích lũy |
| Mực nước ngầm cùng lớp (own-section GWL) | `dGWL`, `dGWL_lag1...36` | Biến động mực nước ngầm tại chính lớp đất đang dự đoán, có độ trễ tới 36 tháng |
| Mực nước ngầm chéo lớp (cross-section GWL) | `xs_S1_dGWL`...`xs_S6_dGWL` | Mực nước ngầm của MỘT lớp đất khác — cho mô hình "nhìn thấy" áp lực từ các lớp lân cận |
| Địa chất tĩnh (ILR material) | `ilr_gravel_vs_rest`, `ilr_sand_vs_clay` | Tỷ lệ sỏi/cát/sét từ log giếng khoan, biến đổi theo phép biến đổi ILR để tránh cộng tuyến |
| Tương tác mùa (dry season) | `is_dry_season`, `*_x_dry_season` | Mùa khô (tháng 11–4) có làm thay đổi phản ứng của mô hình với mực nước ngầm không |
| Tương tác theo lớp đất | 6 lớp × 5 biến điều khiển | Cho phép mỗi lớp đất có độ nhạy riêng với từng biến điều khiển |

Việc phân tách các profile (P0, P3, P7, P_XS_LAG, P8, P9) chính là các phép "cắt lát" khác nhau của các nhóm đặc trưng trên — mỗi profile thêm hoặc bớt một nhóm biến điều khiển để kiểm tra xem nhóm đó có thực sự cải thiện dự đoán hay không. Chi tiết định nghĩa từng profile nằm ở `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\run048_feature_registry.py`, phần khai báo `P0`, `P3`, `P7`, `P_XS_LAG`, `P8`, `P9`.

---

## 5. Kết quả đủ tiêu chuẩn đưa vào bài báo

### 5.1. File tổng hợp chính — dùng file này làm nguồn chính khi viết bài báo

```
D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\docs\20260728_run048_manuscript_evidence.md
```

File này chứa:
- Bảng bằng chứng chính: P3 (mô hình được giữ lại), P7, P_XS_LAG, P8 (các mô hình thử nghiệm bị loại) — mỗi mô hình có câu hỏi vật lý, ΔR² kèm khoảng tin cậy 95%, thay đổi RMSE/MAE tuyệt đối và tương đối, hành vi jackknife theo trạm, quyết định thăng cấp (promotion verdict).
- Kiểm định ý nghĩa thực tế (practical-significance audit): so sánh chênh lệch giữa các mô hình (khoảng 0.001–0.015 mm/tháng) với độ chính xác thiết bị MLCW (1 mm, theo Hung et al. 2021).
- Đoạn văn kết quả (Results) và bàn luận (Discussion) đã viết sẵn theo văn phong khoa học, có thể đưa thẳng vào bản thảo.
- Bảng phụ lục (supplementary) cho các mô hình không được thăng cấp.

### 5.2. Các file bằng chứng gốc hỗ trợ (đã đóng băng, có mã băm SHA-256)

| Đường dẫn | Nội dung |
|---|---|
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\results\` | Kết quả mô hình P0/P3 gốc (baseline) |
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\stage_a\results\` | Kết quả thử nghiệm P7 |
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\stage_b\results\` | Kết quả thử nghiệm P_XS_LAG |
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\stage_c\results\` | Kết quả thử nghiệm P8 |

### 5.3. Hình ảnh (figures) cho bài báo

```
D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\figures\
D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\model_diagnostics\
```

**Lưu ý quan trọng trước khi dùng hình cho bài báo:** có 2 bài kiểm tra hình ảnh đang thất bại (kích thước file PNG sai hoặc hình bị trắng), được ghi lại tại:

```
D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\plans\20260728_figure_qa_task.md
```

Phải sửa xong 2 lỗi này trước khi xuất hình cuối cùng cho bài báo.

### 5.4. Tài liệu nền tảng khác

| File | Nội dung |
|---|---|
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\docs\20260701_ML_features_v4.md` | Bảng kê đầy đủ đặc trưng của mô hình cơ sở (baseline) |
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\docs\20260702_report_after_feature_refine.md` | Kết quả sau vòng tinh chỉnh đặc trưng đầu tiên |
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\CHANGE_NOTES\20260724_run048_stageA_season_material.md` | Ghi chú thay đổi cho thử nghiệm P7 |
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\CHANGE_NOTES\20260724_run048_stageB_xs_lag_control.md` | Ghi chú thay đổi cho thử nghiệm P_XS_LAG |
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\CHANGE_NOTES\20260728_run048_stageC_season_material.md` | Ghi chú thay đổi cho thử nghiệm P8 |
| `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\plans\20260728_P9_readiness_memo.md` | Lý do vì sao thử nghiệm P9 chưa chạy (quyết định chủ động, không phải bỏ sót) |

---

## 6. Tóm tắt một câu cho mỗi mục

- **Mô hình:** BayesianRidge, chạy trong `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\run048_evaluation.py`, cấu hình đặc trưng định nghĩa ở `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\run048_feature_registry.py`.
- **Xử lý số liệu:** dữ liệu thô ở `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\raw_data\`, bảng đặc trưng đã xây ở `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\input_data\`, script xây dựng là `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\run048_snapshot.py`.
- **Chia biến điều khiển:** 6 nhóm đặc trưng vật lý, tổ hợp thành các profile P0/P3/P7/P_XS_LAG/P8/P9, định nghĩa ở `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\run048_feature_registry.py`.
- **Kết quả cho bài báo:** dùng `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\docs\20260728_run048_manuscript_evidence.md` làm nguồn chính; các file `.parquet`/`.json` trong `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\results\` và các thư mục `supplements\*\results\` tương ứng là bằng chứng gốc đã đóng băng.
