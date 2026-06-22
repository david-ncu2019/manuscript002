# 📊 ML-Nowcast v1 — Figure Guide & Honest Verdict

> **Plain-English walkthrough of every figure in `trials/run_001/figures/`, plus straight answers to:
> are we really nowcasting? · are the results good? · how do we improve?**
>
> **See also:** [README.md](README.md) · [CLAUDE.md](../../CLAUDE.md) · [GEMINI.md](../../GEMINI.md) (physics, sign conventions, rank-1 constraint)
> All numbers below are read directly from `trials/run_001/results/nowcast_metrics.json` (test window 2021-01 → 2023-02, 6 sections × 26 months = 156 rows).

---

## 🟢🟡🔴 TL;DR verdict

> **Is it good?** — **Mixed, but honestly so.**
> - ✅ **Works well** for the shallow/mid sections **S1, S2, S4** (R² = 0.50–0.81). The model recovers the real seasonal compaction swing on years it never saw.
> - 🔴 **Fails** for the deep sections **S5, S6** (R² negative — worse than a flat line). This is a **data limitation, not a model defect**: the groundwater sensor doesn't reach the deep clay that is actually compacting.
> - **Is it nowcasting?** ✅ **Yes** (input month *t* → compaction month *t*) — but it is **NOT** a per-layer attribution of the surface signal (physically forbidden; see Q2).

---

## 📖 How to read each figure

Each figure below gets four lines: **What it is · How to read it · What OUR result shows · Caveat.**

### A. INPUT figures (sanity-check the data before trusting any model)

#### 1. `input_dashboard.png` — the raw drivers and the target
![input dashboard](trials/run_001/figures/input_dashboard.png)

- **What it is.** Four stacked panels sharing the same time axis (2012–2023). (a) the **target** = monthly compaction increment for each 50 m section S1–S6; (b) the GPS **surface** increment (one shared signal); (c) the 5 **groundwater heads**; (d) monthly **rainfall**.
- **How to read it.** Read top-to-bottom as cause→effect. Grey band = validation years, yellow band = test years (the model is judged only on yellow). In panel (a), down = compaction.
- **What OUR result shows.** All signals are clean and monthly. The compaction target oscillates seasonally. Crucially, panel (c) shows the **LUNZI (S4) head is legitimately negative** (−5 to −16 m) — that is correct, not a bug; groundwater head is m MSL and must never be flipped.
- **Caveat.** Rainfall ends 2023-02, which is what caps our test window.

#### 2. `driver_response_scatter.png` — the physics check (most important input figure)
![driver response](trials/run_001/figures/driver_response_scatter.png)

- **What it is.** For each section: monthly head change `dGWL` (x) vs compaction increment `dC` (y), each dot a month, colored by calendar month. The straight line is the best fit; `slope` and `r` (correlation) are in each title.
- **How to read it.** Physics expectation: **water level drops → clay compacts**, so we want a clear positive slope and high `r`. A flat cloud (r ≈ 0) means the groundwater signal carries *no information* about that section's compaction.
- **What OUR result shows.** S1–S4 behave: slopes 0.52–0.61, r = 0.51–0.67 — the expected relationship is there. **S5 is weak (slope 0.08, r 0.20) and S6 is essentially flat/negative (slope −0.07, r −0.17).**
- **Caveat.** This single plot explains the whole verdict: for S5/S6, the *driver itself* is disconnected from the response — no model can learn a relationship that isn't in the data.

---

### B. RESULT figures (how well the model did)

#### 3. `skill_summary.png` — the at-a-glance scoreboard
![skill summary](trials/run_001/figures/skill_summary.png)

- **What it is.** Two bars per section: **R²** (blue) and **skill-vs-persistence** (orange), with a black zero line.
- **How to read it.** **Above 0 = good.** R² = 1 is perfect, R² = 0 means "no better than guessing the average", R² < 0 means "worse than the average". Skill-vs-persistence > 0 means we beat the naive "next month = this month" rule.
- **What OUR result shows.** S1 (+0.81), S4 (+0.70), S2 (+0.50) are strong. S3 (+0.31) is modest. **S5 (−0.15) and S6 (−0.13) dip below zero.** S5's orange bar plunges to −1.84 because persistence happens to be *very* good for that smooth deep series, so the model looks especially bad *relative to it*.
- **Caveat.** Skill-vs-persistence is a harsh yardstick for slow, smooth signals; the fairer headline is **skill-vs-mean = +0.21 pooled** (we are 21% better than guessing the average).

#### 4. `obs_vs_pred_scatter.png` — predicted vs observed, with the 1:1 line
![obs vs pred](trials/run_001/figures/obs_vs_pred_scatter.png)

- **What it is.** Each dot is one test month; x = what actually happened, y = what the model predicted. The dashed line is perfect agreement (1:1).
- **How to read it.** Dots **hugging the dashed line** = accurate. Dots forming a tilted/offset cloud = systematic bias. A flat horizontal smear = the model is ignoring the input and predicting near-constant.
- **What OUR result shows.** S1 and S4 hug the line tightly. S5/S6 form flat smears — the model predicts a narrow range regardless of the truth, exactly what negative R² looks like.
- **Caveat.** Only 26 test points per section — small samples make single outliers visually loud.

#### 5. `pred_vs_actual_by_section.png` — the time-series view with uncertainty
![pred vs actual](trials/run_001/figures/pred_vs_actual_by_section.png)

- **What it is.** Per section over the full record: black = actual; the colored line + shaded band = the model's prediction and its **90% confidence interval**, drawn only on the **test** years (yellow band).
- **How to read it.** Good = the colored line tracks the black wiggles, and the black line stays inside the shaded band ~90% of the time.
- **What OUR result shows.** S1–S4: the prediction follows the seasonal up-down on held-out years. S5/S6: the prediction flattens while the truth keeps swinging.
- **Caveat.** The band is the same width everywhere (a single global calibration) — see figure 6.

#### 6. `coverage.png` — is the uncertainty honest?
![coverage](trials/run_001/figures/coverage.png)

- **What it is.** Left: the fraction of test points that actually fell inside the 90% band, per section (red dashed = the 0.90 target). Right: the band width per section.
- **How to read it.** Bars **at the red line** = honest uncertainty. Below = over-confident (band too narrow); the equal widths on the right show the band is the same for every section.
- **What OUR result shows.** Pooled coverage = **0.81** (target 0.90) — slightly over-confident. S1/S4 are over-covered (1.0), S5/S6 under-covered.
- **Caveat.** One global band can't be right for six sections with very different noise — a per-section calibration would fix this (improvement #2).

#### 7. `feature_coefficients.png` — what is the model leaning on?
![coefficients](trials/run_001/figures/feature_coefficients.png)

- **What it is.** Each bar = how strongly a feature pushes the prediction (standardized, so comparable). Blue = pushes one way, red = the other; longer = stronger.
- **How to read it.** The longest bars are the most influential drivers.
- **What OUR result shows.** **`dS_total` (the contemporaneous surface signal) is by far the strongest (+0.27)**, then `month_sin` (season, −0.23), then a 6-month-lagged head. Individual groundwater and rainfall features are small.
- **⚠️ Caveat (binding).** These are **associations in a pooled model, NOT a per-layer attribution** of the surface signal. The surface carrier is rank-1 (one shared degree of freedom for six layers; GEMINI.md), so the model is *not* decomposing the surface into per-layer pieces — see Q2.

#### 8. `residuals.png` *(legacy)*
A simple residual scatter auto-emitted by the training script (`05`). Superseded by figures 4–6; kept for continuity, safe to ignore.

---

## ❓ Q2 — Are we *really* doing nowcasting?

**Yes — by the strict definition — with one nuance you must keep in mind.**

- **The proof is in the data alignment.** In `03_build_feature_table.py`, the target is `mlcw.diff()` at month *t*, and the dominant feature `dS_total = gps.diff()` is **also at month *t*, with no time shift**. Input and output share the same timestamp → this is **nowcasting** (estimating the *current* hidden quantity from *currently available* signals), not **forecasting** (predicting the future). The lag features (1/3/6/12 months) are extra *past* context, not the basis of the prediction.
- **Why it's genuinely useful.** At test time we truly do **not** observe the underground layers (the wells are being shut down — that's the whole project). We only have the surface (InSAR/GPS) + groundwater. The model reconstructs the unobserved per-layer compaction from those — that is exactly the intended job.
- **🔴 The honest nuance.** The strongest driver is the *contemporaneous surface motion*, and the surface motion is itself partly the **sum** of all the layer compactions. So the model is, in part, regressing "a piece onto the whole at the same instant." That is still legitimate nowcasting, **but it is NOT attribution** — we cannot claim the six per-section outputs are a unique decomposition of the surface signal. The rank-1 carrier theorem (GEMINI.md: SVD gives one shared degree of freedom for six layers) forbids that claim. **Use the outputs as nowcasts, never as "this layer caused this much of the surface drop."**

---

## ❓ Q3 — Are the results good?

**Mixed — "good where the physics is observed, fails where it isn't."**

| Section | Depth | R² (test) | Skill vs persistence | Verdict |
|---------|-------|-----------|----------------------|---------|
| S1 | 0–50 m | **+0.81** | +0.37 | ✅ Strong |
| S2 | 50–100 m | **+0.50** | +0.12 | ✅ Good |
| S3 | 100–150 m | +0.31 | +0.03 | 🟡 Modest |
| S4 | 150–200 m | **+0.70** | +0.21 | ✅ Strong |
| S5 | 200–250 m | **−0.15** | −1.84 | 🔴 Fails |
| S6 | 250–300 m | **−0.13** | +0.07 | 🔴 Fails |
| **Pooled** | — | **+0.32** | +0.01 | 🟡 Mixed |

- **The good (S1, S2, S4):** the model recovers the real seasonal compaction on held-out years; pooled it beats the "just guess the average" baseline by **+21%**.
- **The failures (S5, S6) are a DATA problem, not a model problem.** Figure 2 shows the groundwater driver has essentially zero relationship with deep compaction (r ≈ 0.20 / −0.17). The reason is physical: the F3/F4 piezometer screen sits at ~176–179 m and only senses the *top ~12 m* of the deep package, while the clay that actually compacts is at ~238–275 m. **The sensor isn't watching the layer that moves.** No machine-learning method can fix a missing driver.
- **Honesty on baselines.** Beating *persistence* by only +0.01 sounds weak, but persistence ("next month ≈ this month") is a strong baseline for slow monthly signals. The meaningful win is vs the mean (+0.21). Coverage 0.81 < 0.90 means the uncertainty bands are slightly too confident.

**Bottom line:** This is a credible v1 — it proves the approach works wherever the groundwater driver genuinely observes the compacting layer, and it honestly exposes where the monitoring network has a blind spot.

---

## ❓ Q4 — How can we improve? (ranked by expected payoff)

1. **🥇 Fix the deep-section drivers (S5/S6) — biggest payoff.** They fail because the groundwater sensor doesn't reach the compacting clay. Options: assign a deeper piezometer / different well, or explicitly model the deep clay's **delayed (Terzaghi consolidation) response** instead of contemporaneous head. *Until the driver observes the layer, no model can rescue S5/S6.*
2. **🥈 Per-section conformal calibration.** Use a separate interval width per section instead of one global band → fixes the 0.81 coverage and the one-size-fits-all 2.06 mm band.
3. **🥉 Honesty ablation — withhold `dS_total`.** Since the surface feature dominates, run a GWL-only variant to measure how much *true groundwater* skill exists vs surface-leaning. This guards against the "part-on-whole" shortcut.
4. **Model upgrades (only after drivers are fixed):** compare ElasticNet / gradient boosting, add `GWL × fine_pct` interactions and richer lags. These sharpen the *already-good* sections, not the broken ones.
5. **More data / rainfall ablation:** quantify whether rainfall actually helps (its coefficients are currently tiny) and extend the test window if more GPS/rainfall arrives.

---

## 📚 Glossary (for quick reference)

| Term | Plain meaning |
|------|---------------|
| **Nowcasting** | Estimating something happening *right now* that you can't directly see, from signals you *can* see at the same time. (≠ forecasting the future.) |
| **Increment vs cumulative** | Cumulative = total sinking since the start; increment = how much it changed *this month* (`.diff()`). We model the increment. |
| **R²** | How much of the real variation the model explains. 1 = perfect, 0 = no better than the average, <0 = worse than the average. |
| **Persistence baseline** | The lazy guess "this month = last month." A model must beat it to be useful. |
| **Skill** | `1 − (model error / baseline error)`. >0 = better than the baseline. |
| **Conformal interval** | An honest 90% uncertainty band: ~90% of true values should land inside it. |
| **Compaction (nén lún)** | The clay layer squeezing thinner as water leaves → negative values here. |

---

*Generated for ML-nowcast v1 (TUKU pilot). Figures in `trials/run_001/figures/`, numbers in `trials/run_001/results/nowcast_metrics.json`.*
