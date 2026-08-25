# Provenance của các hình trong Results (results004.tex)

Mục đích: liệt kê nguồn dữ liệu gốc và script tạo hình cho từng figure trong
Results, để dùng khi yêu cầu chỉnh sửa visualization style cho phù hợp tạp chí.

Nguồn xác nhận: `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\figure_source_manifest.json`
(chỉ ghi 3/7 hình — xem ghi chú ở mỗi mục).

---

## §4.1 — Monthly estimation with delayed MLCW records

Cả 4 hình dùng chung một script và một nguồn dữ liệu (đã đổi tên từ `fig7`/`fig8`/`fig9`
khi copy vào manuscript — xem `figure_asset_map.json`).

**Script tạo hình (dùng chung cho cả 4 hình):**
`D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results002\build_sec4_1_visual_package.py`
- Đây là script chỉ tồn tại trong working tree, **chưa commit** vào repo `014_ml_nowcast` (repo đó có thay đổi khác của người dùng không liên quan, nên script này chưa được add).

**Dữ liệu nguồn (dùng chung):**
`D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\checkpoints\P0\level1a\predictions.parquet`
- Bộ lọc: trạm TUKU, section S1-S6, predictor `bayesian_ridge`, protocol `rolling_blocked`, model_mode `local`, chỉ giữ fold có đủ 6 tháng liên tục (828 dòng, 138 dòng/section, 23 chu kỳ hoàn chỉnh)
- Snapshot pin: `20260718_run048_v1`
- Khoảng thời gian đánh giá: 2013-05-01 đến 2024-10-01
- Khoảng tin cậy: Bayesian posterior predictive, $y_{pred} \pm 1.645 \cdot y_{std}$ — **không phải split-conformal**, không được ghi nhãn khác đi
- Không refit model — dùng checkpoint đông cứng

### fig_results_delayed_cycle_timeline.pdf (Figure 7)
- **File hình (manuscript):** `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\figures\fig_results_delayed_cycle_timeline.pdf`
- **File nguồn (analysis repo, tên gốc):** `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results002\fig7_delayed_cycle_timeline.pdf`
- **\label trong LaTeX:** `fig:results_delayed_cycles`
- **Trạng thái:** XÁC NHẬN (từ `figure_asset_map.json`, sha256-tracked)

### fig_results_delayed_monthly_estimates_s1_s3.pdf + s4_s6.pdf (Figure 8, 2 panel)
- **File hình (manuscript):**
  - `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\figures\fig_results_delayed_monthly_estimates_s1_s3.pdf`
  - `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\figures\fig_results_delayed_monthly_estimates_s4_s6.pdf`
- **File nguồn (analysis repo, tên gốc):**
  - `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results002\fig8_delayed_monthly_estimates_s1_s3.pdf`
  - `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results002\fig8_delayed_monthly_estimates_s4_s6.pdf`
- **\label trong LaTeX:** `fig:results_delayed_monthly_estimates`
- **Trạng thái:** XÁC NHẬN (từ `figure_asset_map.json`, sha256-tracked)

### fig_results_delayed_prediction_vs_observed.pdf (Figure 9)
- **File hình (manuscript):** `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\figures\fig_results_delayed_prediction_vs_observed.pdf`
- **File nguồn (analysis repo, tên gốc):** `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results002\fig9_delayed_prediction_vs_observed.pdf`
- **\label trong LaTeX:** `fig:results_delayed_scatter`
- **Trạng thái:** XÁC NHẬN (từ `figure_asset_map.json`, sha256-tracked)

### Bảng liên quan (cùng script/thư mục nguồn)
- **Table 3** (`tab:delayed_performance_interval`): `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results002\sec4_1_combined_performance_interval_table.csv`
- **Table 4** (`tab:delayed_performance_by_month`): `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results002\sec4_1_performance_by_month_position.csv`

### Ghi chú quan trọng
- File cũ `figures/fig_results_delayed_performance.pdf` (nếu còn tồn tại trong repo manuscript) **không còn được dùng** — giữ lại chỉ để phục hồi nếu cần, không tham chiếu trong bản thảo hiện tại.
- Không có phần tử nào trong 4 hình này chứa nhãn nội bộ (profile/level identifier) — đã kiểm bằng `pdftotext`, theo `figure_asset_map.json`.
- Nguồn provenance đầy đủ, máy đọc được: `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\figures\figure_asset_map.json`

---

## §4.2 — Sensitivity to less frequent MLCW field measurements

### fig_results_reduced_frequency_3yr_panel_a.pdf (6-month schedule)
- **File hình (manuscript):** `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\figures\fig_results_reduced_frequency_3yr_panel_a.pdf`
- **Script tạo hình:** `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\run048_build_sec4_2_preview_figures.py`
- **Dữ liệu nguồn:** `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results003_calendar_aligned_38predictors\results\sec4_2\results\sec4_2_monthly_predictions.parquet`
  - Bộ lọc dùng: `measurement_interval=6`, `initial_history_months=36`, `record_role=evaluation`
- **Ngày tạo:** 2026-08-17T10:35:51+08:00
- **Trạng thái:** XÁC NHẬN (từ `figure_source_manifest.json`)

### fig_results_reduced_frequency_3yr_panel_b.pdf (12-month schedule)
- **File hình (manuscript):** `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\figures\fig_results_reduced_frequency_3yr_panel_b.pdf`
- **Script tạo hình:** `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\run048_build_sec4_2_preview_figures.py`
- **Dữ liệu nguồn:** `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results003_calendar_aligned_38predictors\results\sec4_2\results\sec4_2_monthly_predictions.parquet`
  - Bộ lọc dùng: `measurement_interval=12`, `initial_history_months=36`, `record_role=evaluation`
- **Ngày tạo:** 2026-08-17T10:35:54+08:00
- **Trạng thái:** XÁC NHẬN (từ `figure_source_manifest.json`)

---

## §4.3 — Sensitivity without subsequent MLCW field measurements

### fig_results_no_subsequent_mlcw_cumulative_error.pdf
- **File hình (manuscript):** `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\figures\fig_results_no_subsequent_mlcw_cumulative_error.pdf`
- **Script tạo hình:** `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\scripts\run048_build_sec4_3_preview_figures.py`
- **Dữ liệu nguồn:** `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results003_calendar_aligned_38predictors\results\sec4_3\results\sec4_3_permanent_stoppage_summary.csv`
  - Bộ lọc dùng: `training_window_years=[3, 5, 8]`, cột giá trị `cum_abs_error_mm`, trục X `months_since_common_end`
- **Ngày tạo:** 2026-08-17T13:47:14+08:00
- **Trạng thái:** XÁC NHẬN (từ `figure_source_manifest.json`)
- **Ghi chú:** Tiêu đề hình đã được đổi từ "after MLCW measurements cease" sang "without subsequent MLCW measurements" ngày 2026-08-17 để tránh gây hiểu lầm là việc đo đạc thực sự đã dừng tại Tuku. Chỉ dòng suptitle thay đổi, dữ liệu và bộ lọc không đổi.

---

## Thông tin dùng chung (common provenance, từ manifest)

- **Dataset ID:** `20260718_run048_v1`
- **Feature manifest:** `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v3\007_tests\014_ml_nowcast\experiments\section_pooled\run_048\supplements\manuscript_results003_calendar_aligned_38predictors\feature_manifest.json`
- **Mốc hiệu chỉnh chung (common calibration end):** 2018-05-01
- **Trạm:** TUKU

---

## Thư mục chứa hình trong manuscript

`D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\figures\`

## File manifest gốc (tham chiếu đầy đủ, machine-readable)

- §4.1 (Figure 7-9): `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\figures\figure_asset_map.json`
- §4.2, §4.3 (Figure 10-11): `D:\112_PROJECT_002\.worktrees\manuscript_reduced_v1\figure_source_manifest.json`
