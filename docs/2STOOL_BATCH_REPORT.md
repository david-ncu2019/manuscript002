# 2S-TOOL Batch Results Report

**Date:** 2026-05-27
**MLCW Source:** modeled (STL-decomposed)
**hp_inicial Source:** JSON overrides (191/191 layers, `json`)
**Input Preparation:** `prepare_2stool_inputs.py --all --mlcw-source modeled`
**Pipeline:** `batch_run_2stool.py` → `twostool_python` (Navarro-Hernandez et al. 2025)

---

## 1. Executive Summary

| Metric | Value |
|--------|-------|
| Input files prepared | 195/195 (100%) |
| 2S-TOOL processed | 191/195 (97.9%) |
| Positive $S_{kv}$ (OK) | 134 layers (70.2%) |
| Negative/Zero $S_{kv}$ | 57 layers (29.8%) |
| Pipeline errors (missing) | 4 layers |
| Median $S_{kv}$ (OK layers) | 1.27 $\times$ 10⁻^2 |
| Median $S_{ke}$ (weighted, OK) | 1.21 $\times$ 10⁻^3 |
| Median $S_{kv}$ / $S_{ke}$ ratio | 11.7 |
| Mean accepted loops (OK) | 14.3 |
| Mean accepted loops (NEG) | 15.6 |

---

## 2. Processing Overview

### 2.1 Input Preparation

All 195 input files (37 stations $\times$ variable layers) were generated successfully from the **modeled** MLCW source. Data point counts per layer range from 23 (ZHENNAN_F1 — short record) to 274 (YUANCHANG_F1 — long record).

### 2.2 Batch Run Status

**4 layers** were prepared but not present in the 2S-TOOL results summary. These are pipeline errors:

| Missing Layer | Input File | Output Directory | Notes |
|:---|---:|:---|:---|
| JIANYANG_F3 | Exists | Not created | Pipeline failed before any output |
| JIAXING_F4 | Exists | Not created | Pipeline failed before any output |
| QIAOYI_F4 | Exists | Created (figures only) | Pipeline produced Fig02 then crashed |
| XINXING_F4 | Exists | Not created | Pipeline failed before any output |

These should be re-run individually with stderr capture to diagnose the exact failure.

### 2.3 hp_inicial Source

All 191 processed layers used the `json` override source (hp_inicial_overrides.json). No layers fell back to well_timeseries or data-driven hc derivation.

---

## 3. Station Classification

### 3.1 Fully Successful (all layers $S_{kv}$ > 0)

**14 stations** — every layer produced a physically meaningful positive inelastic storage coefficient.

| Station | Layers | Station | Layers |
|:---|---:|:---|---:|
| ANHE | F1, F2, F3, F4, T2 | HUWEI | F1, F2, F3, F4, T1 |
| ANNAN | F1, F2, F3, F4, T1, T2 | NANGUANG | F1, F2, F3, F4, T1, T2 |
| BEICHEN | F1, F2, F3, F4 | NEILIAO | F1, F2, F3, F4, T1, T2 |
| CANLIN | F1, F2, F3, F4 | TANQIFENXIAO | F1, F2, F3, F4, T1, T2 |
| ERLUN | F1, F2, F3, F4 | XINPI | F1, F2, F3, F4, T1 |
| GUANGFU | F1, F2, F3, F4 | XIUTAN | F1, F2, F3, F4, T1, T2 |
| HONGLUN | F1, F2, F3, F4, T2 | ZHENGMIN | F1, F2, F3, F4, T1 |

These stations have good GWL-to-MLCW layer assignment match and clear inelastic compaction signals across all monitored layers.

### 3.2 Mixed (some OK, some NEG_SKV)

**21 stations** — at least one layer returned $S_{kv}$ $\le$ 0.

| Station | OK | NEG | Failed Layers | Notes |
|:---|---:|:---|:---|:---|
| XINSHENG | 1 | 5 | F2, F3, F4, T1, T2 | F1 only OK — severe all-layer NEG |
| XINJIE | 1 | 5 | F1, F2, F3, F4, T2 | T1 only OK |
| JIUZHUANG | 1 | 5 | F1, F2, F3, F4, T1 | T2 only OK |
| XINGHUA | 2 | 4 | F2, F3, F4, T2 | F1, T1 OK — aquifer layers fail |
| XIGANG | 1 | 4 | F2, F3, F4, T2 | F1 only OK |
| ZHUTANG | 3 | 3 | F2, F3, F4 | Aquifer layers fail |
| XINXING | 2 | 3 | F2, F3, T1 | F1, T2 OK — 1 missing (F4) |
| YUANCHANG | 4 | 2 | F3, F4 | Deepest layers fail |
| FENGAN | 2 | 2 | F2, F3 | Shallow OK, deep NEG |
| JIANYANG | 2 | 2 | F1, T1 | F2, T2 OK — 1 missing (F3) |
| YIWU | 4 | 2 | F1, T1 | F2, F3, F4, T2 OK |
| HUNAN | 3 | 2 | F3, F4 | Deepest fail |
| LONGYAN | 3 | 2 | F3, F4 | Deepest fail |
| DONGGUANG | 5 | 1 | F4 | |
| FENGRONG | 3 | 1 | F3 | |
| JIAXING | 4 | 1 | T1 | |
| KECUO | 5 | 1 | F4 | |
| QIAOYI | 4 | 1 | T1 | 1 missing (F4) |
| TUKU | 5 | 1 | F4 | Consistent with previous runs |
| XIZHOU | 3 | 1 | F4 | |
| ZHENNAN | 5 | 1 | T2 | |

### 3.3 All-Layer NEG_SKV (pure elastic regime)

**2 stations** — every layer shows $S_{kv}$ $\le$ 0.

| Station | Layers | Mean $S_{kv}$ |
|:---|---:|---:|
| DONGSHI | F1, F2, F3, F4 | −2.04 $\times$ 10⁻^2 |
| HAIFENG | F1, F2, F3, T2 | −1.95 $\times$ 10⁻^2 |

These stations show no detectable inelastic compaction signal. Possible causes:
- GWL well assignment may not capture the compaction-driving aquifer
- The well may be screened in a different depth zone than the MLCW layer
- These stations may be in areas where heads never drop below the preconsolidation threshold during the monitoring period
- DONGSHI also has anomalously high $S_{ke}$ variance (F2: $\pm$ 0.017), suggesting unstable loop fitting

---

## 4. Layer-Level Patterns

| Layer | Count | $S_{kv}$ > 0 | $S_{kv}$ $\le$ 0 | % OK | Median $S_{kv}$ (OK) | NEG_SKV Stations |
|:---|:---:|:---:|:---:|:---:|:---|:---|
| F1 | 37 | 31 | 6 | 83.8% | 8.62 $\times$ 10⁻^3 | DONGSHI, HAIFENG, JIANYANG, JIUZHUANG, XINJIE, YIWU |
| F2 | 37 | 27 | 10 | 73.0% | 1.66 $\times$ 10⁻^2 | DONGSHI, FENGAN, HAIFENG, JIUZHUANG, XIGANG, XINGHUA, XINJIE, XINSHENG, XINXING, ZHUTANG |
| F3 | 36 | 22 | 14 | 61.1% | 6.27 $\times$ 10⁻^3 | DONGSHI, FENGAN, FENGRONG, HAIFENG, HUNAN, JIUZHUANG, LONGYAN, XIGANG, XINGHUA, XINJIE, XINSHENG, XINXING, YUANCHANG, ZHUTANG |
| F4 | 32 | 18 | 14 | 56.3% | 1.65 $\times$ 10⁻^3 | DONGGUANG, DONGSHI, HUNAN, JIUZHUANG, KECUO, LONGYAN, TUKU, XIGANG, XINGHUA, XINJIE, XINSHENG, XIZHOU, YUANCHANG, ZHUTANG |
| T1 | 25 | 18 | 7 | 72.0% | 4.50 $\times$ 10⁻^3 | JIANYANG, JIAXING, JIUZHUANG, QIAOYI, XINSHENG, XINXING, YIWU |
| T2 | 24 | 18 | 6 | 75.0% | 3.12 $\times$ 10⁻^3 | HAIFENG, XIGANG, XINGHUA, XINJIE, XINSHENG, ZHENNAN |

**Key insight:** NEG_SKV rate increases monotonically with depth: F1 (16%) < F2 (27%) < F3 (39%) < F4 (44%). This is physically consistent with:
- Decreasing compaction signal amplitude at depth (longer lever arm, smaller strain)
- Weaker GWL-compaction coupling in deeper aquifers
- Possible well assignment degradation at depth

**Recurrent problem stations** (appear in $\ge$ 3 layers' NEG lists):
- **DONGSHI** — NEG in all 4 layers (F1–F4)
- **HAIFENG** — NEG in all 4 layers (F1–F3, T2)
- **JIUZHUANG** — NEG in 5/6 layers (F1–F4, T1)
- **XINJIE** — NEG in 5/6 layers (F1–F4, T2)
- **XINSHENG** — NEG in 5/6 layers (F2–F4, T1–T2)
- **XINGHUA** — NEG in 4/6 layers (F2–F4, T2)
- **XIGANG** — NEG in 4/6 layers (F2–F4, T2)
- **ZHUTANG** — NEG in 3/6 layers (F2–F4)

---

## 5. Anomalous Cases

### 5.1 Suspiciously High $S_{kv}$ (> 0.5)

Two layers have $S_{kv}$ values that are implausibly large for clay aquitards in the CRFP:

| Station | Layer | $S_{kv}$ | $S_{ke}$(w) | Loops | y_interval |
|:---|---:|---:|---:|---:|---|
| LONGYAN | F2 | **1.30** | 4.04 $\times$ 10⁻^3 | 21 | 0.37 m |
| DONGGUANG | F1 | **0.62** | 1.20 $\times$ 10⁻^2 | 14 | 0.08 m |

$S_{kv}$ > 0.5 is unphysical for these sediments (typical range: 10⁻⁴–10⁻¹). The DONGGUANG F1 case is associated with a very narrow y_interval (0.08 m), suggesting the 2S-TOOL loop decomposition coupled a near-vertical loop segment to an erroneous inelastic slope. These two values should be flagged and the layer results visually inspected before inclusion in any synthesis.

### 5.2 Extreme Negative $S_{kv}$ (< −0.1)

| Station | Layer | $S_{kv}$ | $S_{ke}$(w) | Loops |
|:---|---:|---:|---:|---|
| HUNAN | F3 | **−1.80** | 8.76 $\times$ 10⁻^3 | 12 |
| XINSHENG | F4 | −0.53 | 5.12 $\times$ 10⁻^3 | 11 |
| FENGRONG | F3 | −0.37 | 1.72 $\times$ 10⁻^3 | 17 |

These large-magnitude negative $S_{kv}$ values likely indicate the hc threshold is set too deep, causing elastic unloading segments to be misclassified as inelastic. The DONGSHI F2 case also has very high $S_{ke}$ variance ($\pm$ 0.017), indicating unstable loop fits.

---

## 6. Data Quality Indicators

### 6.1 Data Point Counts

| Range | Layers | Stations |
|:---|---:|:---|
| > 250 pts | 37 | YUANCHANG, DONGSHI, KECUO, XIGANG, HUNAN... |
| 150–250 | 82 | Most stations |
| 50–150 | 54 | Shorter records |
| < 50 | 18 | NANGUANG (40), ANNAN (41), ZHENNAN F1 (23), ZHENGMIN F2 (60)... |

Minimum: ZHENNAN_F1 at 23 points. All layers met the $\ge$ 5-point threshold.

### 6.2 Accepted Loops

- Median accepted loops: 14 (OK layers), 13 (NEG layers)
- Layers with < 5 accepted loops (unstable): **ZHENNAN_F1** (2 loops), JIAXING_T2 (18/36 accepted)

---

## 7. Summary of Problems and Recommendations

### Problem 1: Pipeline Failures (4 layers)
- JIANYANG_F3, JIAXING_F4, QIAOYI_F4, XINXING_F4
- **Action:** Re-run individually with `--layer` filter and capture full stderr to identify crash cause.

### Problem 2: NEG_SKV in Deep Layers (F3/F4)
- 39–44% NEG_SKV rate in F3/F4 vs 16% in F1
- **Action:** Consider (a) reassigning GWL wells for deep layers, (b) verifying hc threshold depth, (c) testing with hp_inicial from well_timeseries long-term min instead of JSON override.

### Problem 3: All-Layer NEG_SKV Stations (DONGSHI, HAIFENG)
- No inelastic signal detected in any layer
- **Action:** Review well-to-MLCW assignments; check if regional GWL data shows heads consistently above hc; consider removing from inelastic analysis or treating as purely elastic.

### Problem 4: Spurious High $S_{kv}$ (LONGYAN F2, DONGGUANG F1)
- $S_{kv}$ > 0.5 is physically implausible
- **Action:** Visual inspection of hysteresis loops; consider applying $S_{kv}$ upper bound filter (e.g., 0.1) in post-processing.

### Problem 5: Very Short Records (< 50 pts)
- 18 layers have data-poor fits, notably ZHENNAN_F1 (23 pts, 2 accepted loops)
- **Action:** Flag these results as LOW confidence; consider excluding if < 5 accepted loops.

---

## 8. Quick Reference Tables

### All Stations Summary

| Station | Total Layers | OK | NEG | ERR | Status |
|:---|---:|:---:|:---:|:---:|:---|
| ANHE | 5 | 5 | 0 | 0 | ALL_OK |
| ANNAN | 6 | 6 | 0 | 0 | ALL_OK |
| BEICHEN | 4 | 4 | 0 | 0 | ALL_OK |
| CANLIN | 4 | 4 | 0 | 0 | ALL_OK |
| DONGGUANG | 6 | 5 | 1 | 0 | MIXED |
| DONGSHI | 4 | 0 | 4 | 0 | ALL_NEG |
| ERLUN | 4 | 4 | 0 | 0 | ALL_OK |
| FENGAN | 4 | 2 | 2 | 0 | MIXED |
| FENGRONG | 4 | 3 | 1 | 0 | MIXED |
| GUANGFU | 4 | 4 | 0 | 0 | ALL_OK |
| HAIFENG | 4 | 0 | 4 | 0 | ALL_NEG |
| HONGLUN | 5 | 5 | 0 | 0 | ALL_OK |
| HUNAN | 5 | 3 | 2 | 0 | MIXED |
| HUWEI | 5 | 5 | 0 | 0 | ALL_OK |
| JIANYANG | 5 | 2 | 2 | 1 | MIXED |
| JIAXING | 6 | 4 | 1 | 1 | MIXED |
| JIUZHUANG | 6 | 1 | 5 | 0 | MIXED |
| KECUO | 6 | 5 | 1 | 0 | MIXED |
| LONGYAN | 5 | 3 | 2 | 0 | MIXED |
| NANGUANG | 6 | 6 | 0 | 0 | ALL_OK |
| NEILIAO | 6 | 6 | 0 | 0 | ALL_OK |
| QIAOYI | 6 | 4 | 1 | 1 | MIXED |
| TANQIFENXIAO | 6 | 6 | 0 | 0 | ALL_OK |
| TUKU | 6 | 5 | 1 | 0 | MIXED |
| XIGANG | 5 | 1 | 4 | 0 | MIXED |
| XINGHUA | 6 | 2 | 4 | 0 | MIXED |
| XINJIE | 6 | 1 | 5 | 0 | MIXED |
| XINPI | 5 | 5 | 0 | 0 | ALL_OK |
| XINSHENG | 6 | 1 | 5 | 0 | MIXED |
| XINXING | 6 | 2 | 3 | 1 | MIXED |
| XIUTAN | 6 | 6 | 0 | 0 | ALL_OK |
| XIZHOU | 4 | 3 | 1 | 0 | MIXED |
| YIWU | 6 | 4 | 2 | 0 | MIXED |
| YUANCHANG | 6 | 4 | 2 | 0 | MIXED |
| ZHENGMIN | 5 | 5 | 0 | 0 | ALL_OK |
| ZHENNAN | 6 | 5 | 1 | 0 | MIXED |
| ZHUTANG | 6 | 3 | 3 | 0 | MIXED |

### By Success Category

| Category | Count | Stations |
|:---|---:|:---|
| **ALL_OK** | 14 | ANHE, ANNAN, BEICHEN, CANLIN, ERLUN, GUANGFU, HONGLUN, HUWEI, NANGUANG, NEILIAO, TANQIFENXIAO, XINPI, XIUTAN, ZHENGMIN |
| **MIXED** | 21 | DONGGUANG, FENGAN, FENGRONG, HUNAN, JIANYANG, JIAXING, JIUZHUANG, KECUO, LONGYAN, QIAOYI, TUKU, XIGANG, XINGHUA, XINJIE, XINSHENG, XINXING, XIZHOU, YIWU, YUANCHANG, ZHENNAN, ZHUTANG |
| **ALL_NEG** | 2 | DONGSHI, HAIFENG |
| **Has ERR** | 3 | JIANYANG, JIAXING, QIAOYI, XINXING |

---

*Generated from `2stool_results_summary.csv` (191 layers) + `preparation_log.csv` (195 inputs).*
