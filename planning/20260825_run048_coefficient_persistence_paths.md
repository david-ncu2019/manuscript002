# Coefficients của Bayesian Ridge sau mỗi calibration cycle — lưu ở đâu?

Ghi chú tra cứu nhanh cho 3 kịch bản trong manuscript. Kiểm chứng trực tiếp từ
code, file trên đĩa, và lần chạy lại ngày 2026-08-25. Bản đầy đủ (schema, số dòng
script, hash kiểm chứng): `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\docs\20260825_run048_coefficient_persistence_paths.md`

## Câu trả lời ngắn

| Kịch bản | Có lưu coefficients mỗi cycle? | Đường dẫn |
|---|---|---|
| Delayed measurements (sec4_1) | ✅ CÓ | `standardized_coefficients.parquet` (xem dưới) |
| Reduced 6-month (sec4_2) | ✅ CÓ (từ 2026-08-25) | 6 file `coef_hist{y}y_{mo}mo.parquet` |
| Reduced 12-month (sec4_2) | ✅ CÓ (từ 2026-08-25) | 6 file trên (tách theo tên file) |

## Nơi lưu — delayed measurements

```
D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\
experiments\section_pooled\run_048\supplements\
manuscript_results003_calendar_aligned_38predictors\results\sec4_1\results\
standardized_coefficients.parquet
```

- 5040 dòng × 9 cột: `model_id, feature, feature_type, coefficient,
  posterior_sd, posterior_p10, posterior_p90, group_id, fold_id`
- 24 `fold_id` = 24 calibration cycles; 6 `group_id` = TUKU__S1 … TUKU__S6.
- Coefficients nằm trong không gian predictor đã chuẩn hóa (z-scored) — so sánh
  được trực tiếp giữa các cycle. Có kèm posterior sd, p10, p90 cho từng trọng số.
- `scaler_state.parquet` cùng thư mục để đổi về đơn vị gốc khi cần.

## Nơi lưu — reduced 6/12-month (thêm ngày 2026-08-25)

```
...\manuscript_results003_calendar_aligned_38predictors\results\sec4_2\results\
```

6 file tách riêng theo từng trường hợp (history × tần suất đo), mỗi file chứa cả
6 tầng S1–S6:

| File | Số dòng | Số cycle |
|---|---:|---:|
| `coef_hist3y_6mo.parquet` | 2.736 | 72 |
| `coef_hist3y_12mo.parquet` | 1.368 | 36 |
| `coef_hist5y_6mo.parquet` | 2.736 | 72 |
| `coef_hist5y_12mo.parquet` | 1.368 | 36 |
| `coef_hist8y_6mo.parquet` | 2.736 | 72 |
| `coef_hist8y_12mo.parquet` | 1.368 | 36 |

- Tổng 12.312 dòng = 324 cycles × 38 features.
- 14 cột: 9 cột giống file delayed cộng thêm `measurement_interval,
  initial_history_months, section, cycle_index, field_measurement_date`.
  Hai cột scenario giữ nguyên dù không đổi trong từng file — để gộp 6 file bằng
  `pd.concat` được an toàn (đã kiểm tra).
- `fold_id` = `cycle_{NN}_{YYYYMM}` (ngày endpoint) → endpoint 12 tháng khớp
  trực tiếp với endpoint 6 tháng cùng mốc.
- Không có cột intercept (cột whitened, không so sánh được với delayed).
- Không có `scaler_state.parquet`: scaler được fit lại trên cùng cửa sổ
  calibration cố định nên không đổi trong một kịch bản — không mang thông tin
  drift (có thể thêm sau nếu cần đổi về đơn vị gốc).

## Đã thực hiện 2026-08-25

Script `run048_tuku_p0_level1a_calendar_aligned_sparse_interval.py` giờ thu gom
coefficients mỗi cycle và ghi 6 file trên (sửa thêm, không đổi logic fit). Chạy
lại toàn bộ: 4 file kết quả cũ giữ nguyên byte-by-byte (hash khớp), file
provenance chỉ đổi timestamp, local-checks 5/5 pass, determinism diff = 0.0.
Phân tích drift có thể bắt đầu ngay trên cả 3 kịch bản.

## Figure drift preview (2026-08-25)

Script vẽ figure preview: `run048_build_coef_drift_preview_figures.py` (thư mục
`scripts\` của pipeline). Script này đọc `standardized_coefficients.parquet`
sec4_1 và vẽ 11 figure preview (PNG + PDF) vào
`figures\coefdrift_preview\fig_supp_coefdrift_*.png/pdf` của worktree này
(folder có README.md ghi absolute path của script và input data) — mỗi figure một
đại lượng vật lý, mỗi subfigure một feature, 6 đường dotted với marker tròn
filled màu tầng, không vẽ uncertainty (tác giả yêu cầu), dấu × xám đánh dấu biến
bị loại, 1 y-label chung cho cả figure. Cùng script có cờ
`--case 3y6mo|3y12mo|5y6mo|5y12mo|8y6mo|8y12mo` sinh thêm 6 bộ figure reduced
(11 figure mỗi case, stem `fig_supp_coefdrift_<case>_...`, đọc từ 6 file
`coef_hist{3,5,8}y_{6,12}mo.parquet`; reduced fit đủ 38 features nên không có
dấu × loại trừ). PREVIEW-ONLY: chưa đăng ký `figure_source_manifest.json`, chưa
wire vào .tex — chờ tác giả duyệt.
