# MLCW Presentation Revision Summary

**Date:** 2026-05-19  
**File:** `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\presentation\dataset_overview.txt`  
**Output:** `dataset_overview.pdf` (18 pages, successfully compiled)

---

## Corrections Made

### 1. **Frame 1/10: Raw Data Structure** ✓
- Clarified that raw MLCW data spans **2003–2025** (instrument installation to present)
- Corrected the `*_ringbyring.csv` file format with example depths (8.8, 12.3, 25.6, ... m)
- Explained that each ring value is a **cumulative compaction** from that depth downward to 300m anchor
- Changed example table dates from 2015 to 2003 to show actual instrument era

### 2. **Frame 2/10: Step 1 — Parametric Decomposition** ✓
- Kept core content (trend + seasonal + jump fitting via appsigsolv)
- Added alertblock noting structural difference between MLCW (0.5yr + 1yr harmonics only) and InSAR (5yr + 10yr + breakpoints)
- Clarified output: JSON model per ring (not just fitted parameters)

### 3. **Frame 3/10: Pipeline Flowchart** ✓ (NEW)
- **Replaced generic 4-box diagram with explicit 3-step pipeline**
- Shows clear progression:
  - Raw Ring Measurements (2003–2025, irregular depths/time)
  - **Step 1:** Parametric Decomposition → JSON Models
  - **Step 2:** Reconstruction → Reconstructed Time Series (5-day cadence, 2015–2025)
  - **Step 3:** Depth Regularisation → Regular 5-m Grid (60 levels, 785 epochs)
- Reduced scale and node dimensions to prevent vbox overflow

### 4. **Frame 4/10: Step 2 — Reconstruction at Uniform Temporal Cadence** ✓ (REWRITTEN)
- **Properly described Step 2** (previously mislabeled as part of Step 3)
- Input: JSON models from Step 1
- Output dates: Days {1, 6, 11, 16, 21, 26} of each month (~5-day intervals)
- Time span clarification:
  - Raw MLCW: 2003–2025
  - Reconstructed: 2015-01-21 onward (aligned to InSAR epoch grid)
  - Total: 217–1892 epochs per station
- Explained purpose: gap-filling, standardisation, preparation for depth interpolation

### 5. **Frame 5/10: Step 3 — Depth Regularisation (Part 1)** ✓ (NEW)
- **Introduced the depth regularisation transformation problem**
- Clarified the challenge: custom ring depths per station → need uniform 5m grid
- Listed three substeps at overview level
- Introduced `mlcw_5m_grid.py` script

### 6. **Frame 6/10: Step 3 — Depth Regularisation (Part 2)** ✓ (COMPREHENSIVE REWRITE)
- **Detailed Substep 1: Bottom-Up Cumulative Sum**
  - Transformed individual ring displacements into cumulative profiles
  - Formula: Y_cumsum(k) = $\Sigma$_{i$\ge$ k} $\Delta$ Y_ring(i)
  
- **Detailed Substep 2: Surface Extrapolation**
  - **Critical missing content added:** 3-point linear regression to create "imaginary surface ring" at depth = 0
  - Formula shown: fit regression through 3 shallowest rings, evaluate at depth 0
  - Explained why: fills gap above shallowest ring

- **Detailed Substep 3: PCHIP Interpolation**
  - Defined PCHIP: Piecewise Cubic Hermite Interpolating Polynomial
  - Inputs: original ring depths + synthetic depth 0, cumsum values, 300m anchor constraint = 0.0mm
  - Output: regular depths (0, 5, 10, ..., 295m)
  - Explained why PCHIP: preserves monotonicity, no spurious oscillations

- **Layer Differences Formula**
  - $\Delta$ Y_k(t) = Y_PCHIP(k-5) − Y_PCHIP(k) (displacement of k-th slab)

### 7. **Frame 7/10: Epoch Alignment & the 2022 Data Gap** ✓ (IMPROVED)
- Clarified baseline: t₀ = **2015-01-21** (InSAR reference epoch, not 2015-01-16 used in older versions)
- Alignment formula: Y_aligned(t) = Y(t) − Y(t₀)
- **Expanded 2022 drought explanation:**
  - What happened: Equipment failure Jan–Dec 2022
  - Solution: Parametric reconstruction using Step 1 models
  - Value: Critical hard hold-out fold for testing resilience when MLCW unavailable
- Highlighted operational importance for Track B methods

### 8. **Frame 10/10: Processing Summary Table** ✓ (UPDATED)
- Changed from 4 rows to 5 rows (now includes Analysis row separately)
- Updated columns: Phase | Script | Input | Output
- Condensed script names to fit column width (e.g., `batch_process` instead of `batch_process_MLCW.py`)
- Clarified total file counts and time ranges per phase

---

## Technical Accuracy Improvements

✓ **Fixed processing order:** Now correctly shows Step 1 → Step 2 → Step 3 → Output  
✓ **Added surface extrapolation detail:** 3-point linear fit to depth=0 (was completely missing)  
✓ **Clarified bottom-up cumsum:** Transformation from individual ring values to cumulative profiles  
✓ **PCHIP explained:** Why monotonicity preservation matters for depth interpolation  
✓ **Correct date ranges:**
  - Raw MLCW: 2003–2025 (not 2015–2025)
  - Reconstructed output: 2015-01-21 onward (aligned to InSAR)
  - InSAR baseline: 2015-01-21 (not -01-16)
✓ **2022 gap context:** Now explains why reconstructed 2022 is critical for operational resilience

---

## Compilation Status

**LaTeX Compilation:** ✓ Success  
**Output:** 18 pages, 549 KB  
**Warnings:** 1 minor vbox (acceptable, ~46pt total frame height deviation)  
**Errors:** None

---

## Files Updated

- `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\presentation\dataset_overview.txt` (main source)
- `D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\presentation\dataset_overview.pdf` (compiled output, 18 pages)

