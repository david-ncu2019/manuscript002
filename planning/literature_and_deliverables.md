# Tuku Manuscript Positioning

## Scientific Focus

The paper evaluates whether contemporaneous groundwater-level and cGNSS observations can provide provisional monthly estimates of compaction in six depth sections while Tuku MLCW observations are delivered six months late. The model receives all six delayed monthly responses at the end of each block and is then updated. This is monthly estimation under delayed target observations, not six-month-ahead forecasting.

## Research Questions

1. Can monthly compaction in S1 through S6 be estimated during a six-month delay in MLCW data delivery?
2. How does performance vary with depth and with the number of months since the latest model update?
3. Does periodic updating improve performance relative to a frozen model, last-observation persistence, and seasonal persistence?

## Position Relative to Prior Work

- [Hung et al. (2012)](https://doi.org/10.1016/j.enggeo.2012.07.018) established the physical and observational relation among groundwater levels, MLCW compaction, and surface displacement in central Taiwan.
- [Liu et al. (2023)](https://doi.org/10.1038/s41598-023-44642-1) reconstructed missing MLCW records from multiple environmental variables, but used randomly divided available records rather than repeated temporally ordered delivery gaps.
- [Liu et al. (2025)](https://doi.org/10.1038/s41598-025-16454-y) used a single MLCW site for deep-learning reconstruction and groundwater-management scenarios. The proposed paper instead evaluates monthly increments in six standardized depth sections under delayed labels.
- [Ali et al. (2021)](https://doi.org/10.1016/j.envsoft.2021.105123) demonstrated that surface deformation can support estimation of groundwater changes when direct observations are sparse. The target direction differs, but the study supports integration of geodetic and hydraulic monitoring.
- [Investigation of Land Subsidence due to Fluid Withdrawal](https://ascelibrary.org/doi/book/10.1061/9780784415702) and [Land Subsidence and its Mitigation](https://gw-project.org/books/land-subsidence-and-its-mitigation/) provide reference terminology for aquifer-system mechanics and extensometer monitoring.

## Defensible Contribution

The manuscript presents a local operational proof of concept. Its contribution is the temporally ordered assessment of depth-resolved monthly compaction during a known delay in target observations. It does not claim causal inference, regional mapping, spatial transfer, or validation of reduced-frequency field sampling.

## Required Deliverables

1. Tuku site and monitoring-configuration figure.
2. Data integration and six-month delayed-observation workflow.
3. Six-panel observed-versus-estimated compaction figure for S1 through S6.
4. Performance figure by section and months since update.
5. Data-source and predictor-group tables.
6. Section-level and pooled metrics for the updated model and valid baselines.
7. Empirical interval coverage and mean interval width.
8. A limitations paragraph distinguishing delayed delivery from reduced sampling.

## Journal Framing

`Water` is the natural first framing if the completed paper emphasizes continuity of groundwater-monitoring information and operational model updating. `Environmental Earth Sciences` is the stronger framing if the clearest contribution is depth-dependent aquifer-system response and the limits imposed by the local monitoring configuration. The neutral LaTeX draft can be moved to either journal template after the figures and principal findings are frozen.
