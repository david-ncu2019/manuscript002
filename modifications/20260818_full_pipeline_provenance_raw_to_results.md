# Provenance đầy đủ: từ dữ liệu thô đến các hình Results (results004.tex)

Mục đích: cho phép tác giả trace lại toàn bộ chuỗi xử lý — từ file dữ liệu thô
gốc nhất cho tới 3 hình/bảng trong Results (§4.1, §4.2, §4.3) — khi reviewer
tạp chí yêu cầu cung cấp scripts. Đây là bản đào sâu hơn file đã có:
`D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\modifications\20260818_results_figure_provenance.md`
(file đó dừng lại ở 3 file dữ liệu trung gian; file này đi tiếp ngược về raw data).

Quy ước viết tắt: MLCW = giếng quan trắc lún nhiều tầng (multilayer compaction
well, đo biến dạng theo độ sâu bằng cảm biến cơ học, KHÔNG phải vệ tinh).
GWL = mực nước ngầm (groundwater level, đơn vị mét trên mực nước biển trung
bình, m MSL). cGNSS = trạm định vị vệ tinh liên tục đo chuyển vị bề mặt.

---

## 1. Dữ liệu thô gốc (raw input data)

| Loại dữ liệu | Đường dẫn thô nhất tìm được | Mô tả |
|---|---|---|
| **MLCW compaction** (TUKU) | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\raw_data\01_mlcw_compaction\TUKU.csv` | Biến dạng lũy kế (cumulative) hàng tháng của 6 đoạn 50 m (cột `000_050_m` … `250_300_m`), âm = lún. Đây là bản đã được căn chỉnh (aligned) sẵn — **KHÔNG PHẢI** dữ liệu cảm biến thô từng ngày. Trong `001_data/mlcw/` (kho dữ liệu chung của toàn dự án, nằm ngoài `014_ml_nowcast`) còn có `raw_timeseries/`, `modeled/`, `reconstructed/` — các bước xử lý sâu hơn (mô hình hóa biến dạng) không được truy ngược trong ghi chú này (xem mục 4, ranh giới xác nhận). |
| **cGNSS surface displacement** (TUKU) | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\raw_data\03_gps_subsidence\TUKU.csv` | Cột `modeled`: chuyển vị bề mặt lũy kế hàng tháng, âm = lún. Tên cột `modeled` cho thấy đây cũng là sản phẩm đã qua một mô hình (không phải toạ độ GNSS thô từng epoch). Kho gốc `001_data/gps/` có `raw_timeseries/`, `decomposed/`, `modeled/` — không truy ngược sâu hơn trong ghi chú này. |
| **GWL** (TUKU, 6 đoạn) | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\raw_data\08_gwl_at_mlcw_monthly_extended\monthly\TUKU_gwl_monthly.csv` | Mực nước ngầm hàng tháng (m MSL) cho từng đoạn 50 m, đây là "GWL v5 extended" — nguồn dùng cho run_048 (xác nhận trực tiếp trong code, xem mục 2). 3 đoạn (S2, S4, S6) là quan trắc giếng thật (`source: "raw"` trong `gwl_source_manifest.json`), 3 đoạn (S1, S3, S5) là giá trị nội suy kriging (`source: "predicted"`) — xem bảng chi tiết dưới đây. |
| **GWL wellcode gán cho từng đoạn TUKU** | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\raw_data\08_gwl_at_mlcw_monthly\gwl_source_manifest.json` (khoá `"TUKU"`) | Cơ chế nguồn GWL đúng theo từng section — **đây là file quyền uy (authoritative)**, không phải `section_well_map` (legacy, theo CLAUDE.md). TUKU: S2→giếng `09050321`, S4→giếng `09050331`, S6→giếng `09050341` (đều cách MLCW 0.01 km); S1/S3/S5 là kriging, không có wellcode. |
| **Borehole lithology** (TUKU) | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\001_data\mlcw\borehole_materials\YL_WSYL23G1_TUKU_土庫.xlsx` | File Excel gốc nhất tìm được — log địa tầng (lithology log) theo độ sâu biến thiên (variable-thickness layers), do người phụ trách khoan/mô tả địa tầng cung cấp. Đây là điểm chạm raw data thô nhất cho nhánh lithology, nằm ngoài `014_ml_nowcast` (ở kho dữ liệu chung `001_data/`). |

**Lưu ý:** File GWL đầu vào của run_048 không phải là "raw" theo nghĩa số đo giếng
thô hàng ngày — nó đã là sản phẩm tổng hợp tháng (`monthly`), một phần đã qua
kriging không gian. Cấp raw hơn nữa (well-level daily) tồn tại tại
`001_data/gwl/well_timeseries/` và `001_data/gwl/kriged_timeseries_2000_2025/`,
nhưng việc truy ngược quy trình kriging cụ thể (run_017, "025_climatology_kriging")
KHÔNG được thực hiện trong ghi chú này — xem mục 4.

---

## 2. Chuỗi xử lý cho từng nhánh Results

### Điểm hội tụ chung của cả 3 nhánh (§4.1, §4.2, §4.3)

**XÁC NHẬN TRỰC TIẾP bằng code:** cả 3 script tạo ra 3 file trung gian đã biết
đều gọi cùng một hàm nạp dữ liệu, `run048_pipeline.load_snapshot()`, trỏ vào
cùng một thư mục snapshot đông cứng (immutable):

```
D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\input_data\20260718_run048_v1\
```

Cụ thể, mỗi script import và gọi:
- §4.1: `from run048_pipeline import load_snapshot` (dòng 43,
  `run048_tuku_p0_level1a_calendar_aligned_delayed_delivery.py`)
- §4.2: `import run048_pipeline as pipeline` rồi `pipeline.load_snapshot(SNAPSHOT_DIR)`
  (dòng 68, 135, `run048_tuku_p0_level1a_calendar_aligned_sparse_interval.py`)
- §4.3: `import run048_pipeline as pipeline` rồi `pipeline.load_snapshot(SNAPSHOT_DIR)`
  (dòng 65, 136, `run048_tuku_p0_level1a_calendar_aligned_permanent_stoppage.py`)

Cả 3 đều dùng `SNAPSHOT_DIR = input_data/20260718_run048_v1/` (hardcode hoặc qua
`registry.ACTIVE_DATASET_ID` = `"20260718_run048_v1"`).

**Kết luận: cả 3 nhánh KHÔNG phải 3 pipeline huấn luyện độc lập.** Chúng hội tụ
về đúng MỘT bước "chuẩn bị dữ liệu đầu vào" (bộ snapshot đông cứng
`20260718_run048_v1`), sau đó mỗi nhánh chạy một kịch bản đánh giá walk-forward
khác nhau (khác cách chia train/predict theo thời gian) trên cùng bộ dữ liệu đó.
Mô hình dùng chung là `BayesianRidge` (scikit-learn), fit riêng cho từng
(section, fold/window) — không có một "mô hình pooled cơ sở" duy nhất được
huấn luyện một lần rồi tái sử dụng cho cả 3 nhánh; mỗi nhánh tự fit lại theo
kịch bản riêng, nhưng luôn xuất phát từ cùng bảng đặc trưng (feature table) đã
đông cứng.

### Bước tạo snapshot `20260718_run048_v1` (bước hội tụ, đi ngược tiếp)

| Bước | Script (absolute path) | Input (absolute path) | Output (absolute path) |
|---|---|---|---|
| 1 | `D:\...\014_ml_nowcast\scripts\40_build_run048_snapshot.py` (CLI wrapper, gọi thẳng `main()` của bước dưới) | — | — |
| 2 | `D:\...\014_ml_nowcast\scripts\run048_snapshot.py` | Gọi `23_build_input_snapshot.py` làm "source builder" (`DEFAULT_SOURCE_BUILDER`, dòng 20) — XÁC NHẬN trực tiếp trong code (`_load_source_builder`, dòng 341) | `input_data/20260718_run048_v1/{STATION}.parquet` (+ `manifest.json`, `schema.json`, `validation_report.json`) |
| 3 | `D:\...\014_ml_nowcast\scripts\23_build_input_snapshot.py` | Đọc trực tiếp `raw_data/` (xem bảng dưới) | Bảng đặc trưng long-format (section × tháng) cho mỗi trạm, trước khi đóng gói bởi bước 2 |

**Input raw cụ thể mà `23_build_input_snapshot.py` đọc (XÁC NHẬN trực tiếp qua đọc code, các hàm `load_mlcw`, `load_gps`, `load_gwl_monthly_section`, `load_materials`, dòng 141–189):**

| Biến | Hàm đọc | File input |
|---|---|---|
| MLCW (target `y_observed` = `.diff()` của cột này) | `load_mlcw()` | `raw_data/01_mlcw_compaction/{STATION}.csv` |
| cGNSS (`dS_total` = `.diff()` của cột `modeled`) | `load_gps()` | `raw_data/03_gps_subsidence/{STATION}.csv` |
| GWL theo đoạn (`gwl_head`, sinh ra `dGWL`) | `load_gwl_monthly_section()` | `raw_data/08_gwl_at_mlcw_monthly_extended/monthly/{STATION}_gwl_monthly.csv` — **hardcode "v5 extended" cho toàn bộ snapshot run_048, không qua CLI flag** (dòng 32–35, 98 của `23_build_input_snapshot.py`: "not a CLI flag, to avoid an accidental mixed-vintage dataset") |
| Lithology (`ilr_gravel_vs_rest`, `ilr_sand_vs_clay`, `ilr_coarse_vs_fine_sand`, `depth_mid`) | `load_materials()` | `raw_data/05_borehole_materials/{STATION}/section_materials.csv` |
| Mưa (rainfall) — bị loại bỏ khỏi bộ đặc trưng cuối (`run048_snapshot.py` dòng 49: `result.drop(columns=[c for c in result.columns if c.startswith("rain")])`) | `load_rainfall()` | `raw_data/04_rainfall/{STATION}.csv` (đọc nhưng sau đó bị loại khỏi feature set active của run_048) |

### Bước tạo `section_materials.csv` (input lithology của bước 3), đi ngược tiếp

| Bước | Script (absolute path) | Input (absolute path) | Output (absolute path) |
|---|---|---|---|
| a | `D:\...\014_ml_nowcast\scripts\01_resample_borehole_0.1m.py` | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\001_data\mlcw\borehole_materials\YL_WSYL23G1_TUKU_土庫.xlsx` (auto-discover theo pattern `*_TUKU_*.xlsx`, dòng 27, 36) | `raw_data/05_borehole_materials/TUKU/borehole.csv` (3000 dòng, lát 0.1 m, từ 0–300 m) |
| b | `D:\...\014_ml_nowcast\scripts\02_compute_section_materials.py` | `raw_data/05_borehole_materials/TUKU/borehole.csv` (XÁC NHẬN — docstring dòng 6–8 ghi rõ "Input: ... (from 01_resample_borehole)") | `raw_data/05_borehole_materials/TUKU/section_materials.csv` (6 dòng, S1–S6, gồm % vật liệu và biến đổi ILR) |

Đây là toàn bộ nhánh lithology — file Excel `.xlsx` là raw gốc nhất tìm được
trong toàn bộ chuỗi.

### §4.1 — Delayed MLCW delivery (Figure 7–9)

| Bước | Script (absolute path) | Input (absolute path) | Output (absolute path) |
|---|---|---|---|
| 1 | (bước hội tụ — xem trên) | raw_data | `input_data/20260718_run048_v1/*.parquet` |
| 2 | `D:\...\014_ml_nowcast\scripts\run048_tuku_p0_level1a_calendar_aligned_delayed_delivery.py` | `input_data/20260718_run048_v1/` (qua `load_snapshot`) + `.../manuscript_results003_calendar_aligned_38predictors/feature_manifest.json` (danh sách 38 predictor đông cứng) | `.../manuscript_results003_calendar_aligned_38predictors/results/sec4_1/results/predictions.parquet` |
| 3 | `D:\...\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results002\build_sec4_1_visual_package.py` (vẽ hình) | `experiments\section_pooled\run_048\checkpoints\P0\level1a\predictions.parquet` — **XÁC NHẬN trực tiếp**, xem ghi chú dưới | Figure 7, 8, 9 (PDF) |

**Đính chính (mâu thuẫn đã giải quyết, đọc lại code trực tiếp):**
`build_sec4_1_visual_package.py` khai báo `CHECKPOINT_DIR = OUTPUT_DIR.parent.parent / "checkpoints" / "P0" / "level1a"`
và gọi `pd.read_parquet(CHECKPOINT_DIR / "predictions.parquet")` (dòng 36, 155).
Vậy input thật sự của Figure 7–9 là checkpoint sản xuất gốc:
`D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\checkpoints\P0\level1a\predictions.parquet`
— khớp với file provenance cũ (`20260818_results_figure_provenance.md`), **không phải**
bản rerun 38-biến ở `results003_calendar_aligned_38predictors/.../sec4_1/results/predictions.parquet`.

File rerun 38-biến (bước 2 ở bảng trên) là một **bản kiểm tra tính bất biến
theo lịch (calendar-invariance check)**, chạy song song để xác nhận thiết kế
thực nghiệm không đổi khi chuyển từ registry sống (42 biến) sang danh sách
đông cứng (38 biến) — không phải nguồn trực tiếp của Figure 7–9. Hai file
`predictions.parquet` này là hai file khác nhau, ở hai thư mục khác nhau,
cùng tên và cùng cấu trúc cột, dễ gây nhầm lẫn nếu chỉ nhìn tên file.

### §4.2 — Reduced measurement frequency (Figure 10)

| Bước | Script (absolute path) | Input (absolute path) | Output (absolute path) |
|---|---|---|---|
| 1 | (bước hội tụ) | raw_data | `input_data/20260718_run048_v1/*.parquet` |
| 2 | `D:\...\014_ml_nowcast\scripts\run048_tuku_p0_level1a_calendar_aligned_sparse_interval.py` | `input_data/20260718_run048_v1/` (qua `pipeline.load_snapshot`, dòng 135) + `feature_manifest.json` (38 biến) — **tái sử dụng KHÔNG SỬA** các hàm `fit_interval_constrained`, `build_aggregated_row`, `predict_monthly_with_uncertainty` từ script "anh em" `run048_tuku_p0_level1a_sparse_interval_sensitivity.py` (import trực tiếp, dòng 63–67 — XÁC NHẬN) | `.../manuscript_results003_calendar_aligned_38predictors/results/sec4_2/results/sec4_2_monthly_predictions.parquet` |
| 3 | `D:\...\014_ml_nowcast\scripts\run048_build_sec4_2_preview_figures.py` (vẽ hình) | `sec4_2_monthly_predictions.parquet` (bước 2, khớp trực tiếp — path này chính là path đã ghi trong file provenance cũ, không mâu thuẫn) | Figure 10 (panel a: 6 tháng, panel b: 12 tháng) |

Xác nhận: đây là bản "calendar-fair" (mốc hiệu chỉnh chung 2018-05-01, mốc kết
thúc đánh giá chung 2024-05-01), thay thế bản cũ hơn không calendar-fair
(`run048_tuku_p0_level1a_sparse_interval_sensitivity.py`, gọi là "sibling
script" trong docstring, common-START thay vì common-END).

### §4.3 — No subsequent MLCW measurements (Figure 11)

| Bước | Script (absolute path) | Input (absolute path) | Output (absolute path) |
|---|---|---|---|
| 1 | (bước hội tụ) | raw_data | `input_data/20260718_run048_v1/*.parquet` |
| 2 | `D:\...\014_ml_nowcast\scripts\run048_tuku_p0_level1a_calendar_aligned_permanent_stoppage.py` | `input_data/20260718_run048_v1/` (qua `pipeline.load_snapshot`, dòng 136) + `feature_manifest.json` (38 biến) | `.../manuscript_results003_calendar_aligned_38predictors/results/sec4_3/results/sec4_3_permanent_stoppage_summary.csv` |
| 3 | `D:\...\014_ml_nowcast\scripts\run048_build_sec4_3_preview_figures.py` (vẽ hình) | `sec4_3_permanent_stoppage_summary.csv` (bước 2, khớp trực tiếp) | Figure 11 |

Thiết kế: huấn luyện (fit) đúng một lần trên cửa sổ 3/5/8 năm kết thúc tại
2018-05-01 (không refit), sau đó dự đoán liên tục 80 tháng (2018-05 đến
2024-12) không có thêm MLCW input nào — đúng như yêu cầu "no refit inside each
N-month window" trong CLAUDE.md.

### Bước kiểm tra chéo (không phải bước tạo dữ liệu, chỉ đọc lại để xác nhận)

`D:\...\014_ml_nowcast\scripts\run048_calendar_aligned_full_validation_suite.py`
đọc cả 3 file trung gian trên (predictions.parquet của sec4_1, sec4_2_monthly_predictions.parquet,
sec4_3_permanent_stoppage_summary.csv, tất cả trong cùng thư mục
`results003_calendar_aligned_38predictors/results/`) để đối chiếu ngày tháng
và mốc hiệu chỉnh chung — đây LÀ BẰNG CHỨNG TRỰC TIẾP xác nhận cả 3 file nằm
cùng một cây thư mục kết quả (`results003_calendar_aligned_38predictors`),
củng cố kết luận về điểm hội tụ chung ở mục 2.

---

## 3. Bảng tổng hợp: file trung gian được script vẽ hình đọc trực tiếp

| Nhánh | Script vẽ hình (absolute path) | File trung gian đọc trực tiếp (absolute path) | Trạng thái |
|---|---|---|---|
| §4.1 | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results002\build_sec4_1_visual_package.py` | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\checkpoints\P0\level1a\predictions.parquet` | XÁC NHẬN trực tiếp (đọc code `CHECKPOINT_DIR` + `pd.read_parquet`, dòng 36, 155) |
| §4.2 | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\run048_build_sec4_2_preview_figures.py` | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results003_calendar_aligned_38predictors\results\sec4_2\results\sec4_2_monthly_predictions.parquet` | XÁC NHẬN (file provenance cũ + đường dẫn khớp với script tạo dữ liệu tìm thấy trong lượt này) |
| §4.3 | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\run048_build_sec4_3_preview_figures.py` | `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results003_calendar_aligned_38predictors\results\sec4_3\results\sec4_3_permanent_stoppage_summary.csv` | XÁC NHẬN (file provenance cũ + đường dẫn khớp với script tạo dữ liệu tìm thấy trong lượt này) |

---

## 4. Ghi chú về độ tin cậy

### Đã XÁC NHẬN trực tiếp (đọc thấy code thật sự đọc/ghi đúng file đó)

- 3 script tạo file trung gian (`run048_tuku_p0_level1a_calendar_aligned_delayed_delivery.py`,
  `..._sparse_interval.py`, `..._permanent_stoppage.py`) đều gọi `load_snapshot()`
  trỏ vào `input_data/20260718_run048_v1/` — đọc trực tiếp mã nguồn.
- `run048_snapshot.py` dùng `23_build_input_snapshot.py` làm "source builder"
  (biến `DEFAULT_SOURCE_BUILDER`, hàm `_load_source_builder`).
- `23_build_input_snapshot.py` đọc trực tiếp 5 loại file trong `raw_data/`
  (MLCW, GPS, GWL v5 extended monthly, borehole materials, rainfall) — đọc
  trực tiếp các hàm `load_mlcw`, `load_gps`, `load_gwl_monthly_section`,
  `load_materials`, `load_rainfall`.
- `02_compute_section_materials.py` đọc `borehole.csv` do
  `01_resample_borehole_0.1m.py` tạo ra (đọc trực tiếp docstring + code cả
  hai file).
- `01_resample_borehole_0.1m.py` đọc file Excel gốc
  `001_data/mlcw/borehole_materials/*_TUKU_*.xlsx` — đọc trực tiếp code
  (biến `BOREHOLE_DIR`, `candidates = sorted(BOREHOLE_DIR.glob(...))`) và xác
  nhận file `YL_WSYL23G1_TUKU_土庫.xlsx` thực sự tồn tại trên đĩa.
  qua lệnh `find`.
- Nguồn GWL theo từng đoạn TUKU (raw giếng thật vs. kriging nội suy) —
  đọc trực tiếp `gwl_source_manifest.json`, khớp với script audit lineage
  `05_audit_upstream_source_lineage.py` (đã tự phân loại các thành phần thành
  `VERIFIED_CAUSAL_WITHIN_SNAPSHOT`, `NOT_CERTIFIED_UPSTREAM`,
  `HISTORICAL_CAUSALITY_NOT_ESTABLISHED` — chính script đó cũng thừa nhận biên
  giới xác nhận của nó).
- §4.2 và §4.3 dùng chung thư mục kết quả gốc
  `manuscript_results003_calendar_aligned_38predictors/results/` — xác nhận
  qua `run048_calendar_aligned_full_validation_suite.py`, script đọc cả 3 file
  trung gian từ đúng cây thư mục đó để đối chiếu chéo.
- **§4.1 — đường dẫn `predictions.parquet` của Figure 7–9, đính chính sau khi
  đọc lại trực tiếp:** `build_sec4_1_visual_package.py` khai báo
  `CHECKPOINT_DIR = OUTPUT_DIR.parent.parent / "checkpoints" / "P0" / "level1a"`
  và gọi `pd.read_parquet(CHECKPOINT_DIR / "predictions.parquet")` (dòng 36,
  155) — xác nhận input thật sự là checkpoint sản xuất gốc
  (`checkpoints/P0/level1a/predictions.parquet`), khớp với file provenance cũ.
  Bản rerun 38-biến ở `results003_calendar_aligned_38predictors/.../sec4_1/`
  chỉ là bản kiểm tra bất biến lịch song song, không phải nguồn hình.

### SUY LUẬN, CHƯA XÁC NHẬN TRỰC TIẾP trong lượt làm việc này

- Việc MLCW `raw_data/01_mlcw_compaction/TUKU.csv` và cGNSS
  `raw_data/03_gps_subsidence/TUKU.csv` (cột `modeled`) được tính ra từ dữ liệu
  cảm biến/vệ tinh thô hơn thế nào (script cụ thể nào biến `raw_timeseries` →
  `modeled`/`reconstructed` trong `001_data/mlcw/` và `001_data/gps/`) —
  **KHÔNG được truy ngược trong ghi chú này.** Đây là ranh giới cố ý: các bước
  đó thuộc các pipeline khác (2S-TOOL, IHM-F cho MLCW; xử lý GNSS riêng cho
  cGNSS), đã đóng hoặc nằm ngoài phạm vi `014_ml_nowcast`, và CLAUDE.md ghi rõ
  không cần mở lại IHM-F trừ khi có yêu cầu tường minh.
- Việc GWL kriging (3 đoạn S1/S3/S5 của TUKU, `source: "predicted"`) được tính
  ra sao từ số liệu giếng thô — **KHÔNG được truy ngược trong ghi chú này.**
  Tài liệu tham chiếu đúng là
  `002_docs/references/pipeline/gwl_kriging_architecture.md` và công việc
  "025_climatology_kriging run_017" (nhắc tới trong
  `05_audit_upstream_source_lineage.py` nhưng không đọc lại script run_017
  trong lượt này).
- Việc cột "GWL v5 extended" (`08_gwl_at_mlcw_monthly_extended/monthly/`)
  được tạo ra từ `08_gwl_at_mlcw_monthly_extended/krige_daily/` (thư mục anh
  em cùng cấp, tên gợi ý là dữ liệu kriging hàng ngày) — nhìn thấy thư mục này
  tồn tại qua lệnh liệt kê file, nhưng **chưa đọc script nào xác nhận** đây
  đúng là bước sinh ra file monthly. Đây là suy luận theo cấu trúc thư mục,
  chưa xác nhận bằng code.
- File `feature_manifest.json` (38 predictor, tại
  `.../manuscript_results003_calendar_aligned_38predictors/feature_manifest.json`)
  được đề cập tới trong ghi chú của nhiệm vụ nhưng **chưa được mở đọc trong
  lượt làm việc này** — nội dung chi tiết 38 biến (bao gồm việc liệt kê rõ
  gốc GWL/cGNSS/MLCW nào) chưa được xác nhận trực tiếp, chỉ biết chắc từ code
  rằng file này tồn tại và được 3 script tạo dữ liệu đọc như "frozen feature
  list" (qua hàm `load_frozen_feature_list`).

### Khuyến nghị hành động tiếp theo cho tác giả

1. Nếu reviewer yêu cầu truy ngược sâu hơn tới cảm biến MLCW/GNSS thô, cần mở
   lại tài liệu 2S-TOOL/IHM-F và pipeline xử lý GNSS riêng (ngoài phạm vi
   `014_ml_nowcast`) — không nằm trong ghi chú này.
2. Nếu cần xác nhận chính xác cách GWL kriging (S1/S3/S5) hoặc "GWL v5
   extended" được tính, đọc `002_docs/references/pipeline/gwl_kriging_architecture.md`
   và script run_017 ("025_climatology_kriging") — chưa mở trong ghi chú này.
