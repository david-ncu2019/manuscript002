# NotebookLM Inventory — InSAR-MLCW Project

**Date:** 2026-06-08 | **Total notebooks:** 21 | **Project-relevant:** 14 / 21 (67%)

---

## Tier 1 — Directly Project-Relevant (6 notebooks)

| # | ID | Title | Owner | Sources | Purpose |
|---|-----|-------|-------|---------|---------|
| 1 | `dbcc4e4a` | **Subsidence_Papers** | Owner | 51 | InSAR subsidence literature: PS-InSAR, SBAS, GNSS fusion, deformation monitoring |
| 2 | `8c6faa4f` | **InSAR_Thesis** | Owner | 54 | ~20 PhD/Master theses: persistent scatterer, distributed scatterer, SBAS processing |
| 3 | `7ff80e8e` | **Choushui_Sub** | Shared | 57 | Primary CRAF literature: Hung et al. (2012/2021/2025), Chen et al. (2021), Chu et al. (2024), Hsu et al. (2020/2021), Patra et al. (2025), WRA reports |
| 4 | `fe2eaf50` | **Multi-Sensor Integration for Alluvial Fan Subsidence Monitoring** | Owner | 51 | Project-namesake notebook: multi-sensor InSAR + GNSS + GWL for alluvial fan subsidence |
| 5 | `1c884a3d` | **Hydrogeology_Relearn** | Owner | 18 | Aquifer consolidation, storage coefficients, groundwater dynamics |
| 6 | `f8e8b640` | **GWR_Concept** | Owner | 13 | Geographically Weighted Regression, spatial non-stationarity, MODFLOW calibration |

## Tier 2 — Technical Support (5 notebooks)

| # | ID | Title | Owner | Sources | Purpose |
|---|-----|-------|-------|---------|---------|
| 7 | `61de7fd5` | **Geostatistics** | Shared | 47 | 45 video lectures: variogram, kriging, spatial simulation — for Stage 2 spatial extension |
| 8 | `06943b15` | **Spatio-Temporal Inversion Using the Selection Kalman Model** | Owner | 58 | Tikhonov regularization, NNLS, Bayesian source apportionment, joint inversion |
| 9 | `c4bc94cd` | **TimeSeries** | Owner | 4 | Time series analysis + forecasting textbooks |
| 10 | `02ff20de` | **Relearn_GeotechEngineer** | Owner | — | Soil mechanics: Terzaghi consolidation, settlement |
| 11 | `0c468070` | **Geomorphology** | Owner | 4 | Alluvial fan morphology — CRAF depositional system context |

## Tier 3 — Background Reference (3 notebooks)

| # | ID | Title | Owner | Sources | Purpose |
|---|-----|-------|-------|---------|---------|
| 12 | `cd5f4e1c` | **USGS MODFLOW 6 Groundwater Flow Model Documentation** | Shared | 46 | MODFLOW SUB/CSUB package, FloPy, skeletal storage — reference implementation of physical model |
| 13 | `4c4d5185` | **Introduction to Statistics and Data Analysis** | Owner | 35 | Bayesian inference, MLE, hypothesis testing, bootstrapping (video lectures) |
| 14 | `2126db9b` | **Alaska Permafrost and Soil Carbon Dynamics** | Owner | — | Different study area; shared theme: InSAR + soil dynamics |

## Tier 4 — Not Project-Related (7 notebooks)

| # | ID | Title | Owner | Purpose |
|---|-----|-------|-------|---------|
| 15 | `5b8a4ab0` | WritingTechniques | Shared | Academic writing skills |
| 16 | `4e418dd5` | LaTEX_Everything | Owner | LaTeX formatting reference |
| 17 | `b801e06d` | Sieve_Analysis_Test | Owner | Soil sieve analysis (geotech lab) |
| 18 | `d2c60ee4` | Overall_Model_Test | Shared | Generic model testing |
| 19 | `26e2913e` | TeachingApproach | Owner | Teaching methodology |
| 20 | `0acd3974` | Claude_Code_Guidance | Owner | AI coding tool guidance |
| 21 | `e37893f2` | Self_Learn_Tips | Owner | Self-learning strategies |

---

## Quick Reference — NotebookLM CLI Commands

```bash
# List all notebooks
notebooklm list

# Use a specific notebook for queries
notebooklm use dbcc4e4a          # Subsidence_Papers
notebooklm use 7ff80e8e          # Choushui_Sub

# Search within a notebook
notebooklm ask "What are the S_ske and S_skv values for Choushui alluvial fan?" -n 7ff80e8e

# List sources in a notebook
notebooklm source list -n 7ff80e8e

# Generate podcast from key papers
notebooklm generate audio "Summarize the key findings on land subsidence mechanisms in the Choushui River Alluvial Fan" -n 7ff80e8e

# Generate study guide
notebooklm generate report --format study-guide -n 7ff80e8e
```

## Notebook → Project Stage Mapping

| Project Stage | Primary Notebook(s) |
|---------------|---------------------|
| Physical model design (IHM-F) | Hydrogeology_Relearn, Relearn_GeotechEngineer, MODFLOW 6 Docs |
| Literature review | Choushui_Sub, Subsidence_Papers, InSAR_Thesis |
| Method selection | Multi-Sensor Integration, GWR_Concept, Spatio-Temporal Inversion |
| Spatial extension (Stage 2) | Geostatistics, GWR_Concept |
| Manuscript writing | Choushui_Sub, Subsidence_Papers, InSAR_Thesis |

---

## Borehole Logging Files (MLCW wells) — Added 2026-06-09

32 borehole log files for multilayer compaction monitoring wells (MLCW) are stored at:
`data/mlcw/borehole_materials/`

Each file encodes both the CGS well identifier (e.g., `CH_WSCH01G1`, `YL_WSYL23G1`) and the English + Chinese station names. Files are `.xlsx` format, last modified 2023-12-19 to 2023-12-20, sizes 5.2–12 KB. Not yet parsed by any script.

| # | Filename | Station match in v4 CSV |
|---|----------|------------------------|
| 1 | CH_WSCH01G1_XINJIE_新街.xlsx | Yes |
| 2 | CH_WSCH02G1_XIGANG_西港.xlsx | Yes |
| 3 | CH_WSCH03G1_XINGHUA_興華.xlsx | Yes |
| 4 | CH_WSCH04G1_XINSHENG_新生.xlsx | Yes |
| 5 | CH_WSCH05G1_HUNAN_湖南.xlsx | Yes |
| 6 | CH_WSCH06G1_XIZHOU_溪州.xlsx | Yes |
| 7 | CH_WSCH07G1_QIAOYI_僑義.xlsx | Yes |
| 8 | CH_WSCH08G1_ZHUTANG_竹塘.xlsx | Yes |
| 9 | YL_WSYL09G1_FENGAN_豐安.xlsx | Yes |
| 10 | YL_WSYL10G1_HAIFENG_海豐.xlsx | Yes |
| 11 | YL_WSYL11G1_XINXING_新興.xlsx | Yes |
| 12 | YL_WSYL12G1_LUNFENG_崙豐.xlsx | No — LUNFENG absent from v4 CSV (37 active stations) |
| 13 | YL_WSYL13G1_JIANYANG_建陽.xlsx | Yes |
| 14 | YL_WSYL14G1_DONGGUANG_東光.xlsx | Yes |
| 15 | YL_WSYL15G1_JINHU_金湖.xlsx | No — JINHU absent from v4 CSV (37 active stations) |
| 16 | YL_WSYL16G1_YIWU_宜梧.xlsx | Yes |
| 17 | YL_WSYL17G1_CANLIN_燦林.xlsx | Yes |
| 18 | YL_WSYL18G1_ERLUN_二崙.xlsx | Yes |
| 19 | YL_WSYL19G1_FENGRONG_豐榮.xlsx | Yes |
| 20 | YL_WSYL20G1_YUANCHANG_元長.xlsx | Yes |
| 21 | YL_WSYL21G1_KECUO_客厝.xlsx | Yes |
| 22 | YL_WSYL22G1_NEILIAO_內寮.xlsx | Yes |
| 23 | YL_WSYL23G1_TUKU_土庫.xlsx | Yes |
| 24 | YL_WSYL24G1_XIUTAN_秀潭.xlsx | Yes |
| 25 | YL_WSYL25G1_HONGLUN_宏崙.xlsx | Yes |
| 26 | YL_WSYL26G1_HUWEI_虎尾.xlsx | Yes |
| 27 | YL_WSYL27G1_GUANGFU_光復.xlsx | Yes |
| 28 | YL_WSYL28G1_ZHENGMIN_拯民.xlsx | Yes |
| 29 | YL_WSYL29G1_LONGYAN_龍岩.xlsx | Yes |
| 30 | YL_WSYL30G1_ZHENNAN_鎮南.xlsx | Yes |
| 31 | YL_WSYL31G1_JIAXING_嘉興.xlsx | Yes |
| 32 | YL_WSYL32G1_BEICHEN_北辰.xlsx | Yes |

Note: LUNFENG (well 12) and JINHU (well 15) have borehole files but no entry in `gwl_to_mlcw_layer_assignment_v4.csv`. These two wells are physically present on the Choushui River Alluvial Fan but were not assigned GWL drivers under the v4 scheme — they may be inactive monitoring wells or wells excluded during the layer assignment quality-control step.
