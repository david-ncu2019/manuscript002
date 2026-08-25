# Citation Recommendations for Section 3.2: Bayesian Ridge Regression

- **Date:** 2026-08-18 (Updated with snake_case citation keys aligned with `writing_manu2.bib`)
- **Target File:** [`sections/methods006.tex`](file:///D:/112_PROJECT_002/.worktrees/manuscript_reduced_v1/sections/methods006.tex)
- **Target Subsection:** `\subsection{Bayesian ridge regression}` (`\label{subsec:bayesian_ridge}`)
- **Target Bibliography:** [`writing_manu2.bib`](file:///D:/112_PROJECT_002/.worktrees/manuscript_reduced_v1/writing_manu2.bib)

---

## 1. Citation Key Mapping (from `temp.bib` CamelCase to `writing_manu2.bib` snake_case)

| Zotero / `temp.bib` Key | `writing_manu2.bib` Key (snake_case) | Reference | Note |
| :--- | :--- | :--- | :--- |
| `dormannCollinearityReviewMethods2013` | **`dormann_collinearity_2013`** | Dormann et al. (2013, *Ecography*) | Multicollinearity in environmental modeling |
| `hastieElementsStatisticalLearning2009` | **`hastie_elements_2009`** | Hastie et al. (2009, Springer) | Ridge regression & variance inflation |
| `PatternRecognitionMachine2007` *(defective)* | **`bishop_pattern_2006`** | Bishop (2006, Springer) | Bayesian linear regression & Evidence framework |
| `gelmanBayesianDataAnalysis2013` | **`gelman_bayesian_2013`** | Gelman et al. (2013, CRC Press) | Posterior predictive distribution & UQ |
| `tarantolaInverseProblemTheory2005` | **`tarantola_inverse_2005`** | Tarantola (2005, SIAM) | Geophysical inversion & Gaussian priors |
| `gallowayRegionalLandSubsidence2011` *(missing)* | **`galloway_review_2011`** | Galloway & Burbey (2011, *Hydrogeol J*) | Physical coupled groundwater-compaction models |
| `hoerlRidgeRegressionBiased1970` | **`hoerl_1970_ridge`** | Hoerl & Kennard (1970, *Technometrics*) | *Already in `writing_manu2.bib`* |
| `mackayBayesianInterpolation1992` | **`mackay_bayesian_1992`** | MacKay (1992, *Neural Computation*) | *Already in `writing_manu2.bib`* |
| `burbeyExtensometerForensicsWhat2020` | **`burbey_extensometer_2020`** | Burbey (2020, *Hydrogeol J*) | *Already in `writing_manu2.bib`* |

---

## 2. Proposed LaTeX Text Revision for `sections/methods006.tex`

```latex
\subsection{Bayesian ridge regression}
\label{subsec:bayesian_ridge}

Bayesian ridge regression was used as a probabilistic linear regression model to estimate monthly deformation increments independently for each depth section. The predictors included current and lagged changes in hydraulic head and vertical surface displacement, together with seasonal terms. Several of these predictors described related temporal variations and therefore contained overlapping information. Under these conditions, ordinary least squares may produce regression coefficients that change markedly in response to small changes in the calibration data due to variance inflation from multicollinearity \citep{dormann_collinearity_2013, hastie_elements_2009}. Ridge regression limits this sensitivity by shrinking weakly supported coefficients toward zero through an $L_2$ penalty \citep{hoerl_1970_ridge, hastie_elements_2009}.

The Bayesian formulation applies the same coefficient shrinkage while explicitly representing parameter and predictive uncertainty \citep{mackay_bayesian_1992, bishop_pattern_2006, gelman_bayesian_2013}. For $n$ calibration observations and $p$ standardized predictors, the regression model was

\begin{equation}
\Delta\boldsymbol{d}_s
=
\beta_{0,s}\boldsymbol{1}
+
\boldsymbol{X}_s\boldsymbol{\beta}_s
+
\boldsymbol{\varepsilon}_s,
\label{eq:brr_regression}
\end{equation}

\noindent with residual errors described by

\begin{equation}
\boldsymbol{\varepsilon}_s
\sim
\mathcal{N}
\left(
\boldsymbol{0},
\alpha_s^{-1}\boldsymbol{I}
\right).
\label{eq:brr_likelihood}
\end{equation}

\noindent Here, $\Delta\boldsymbol{d}_s$ contains the observed monthly deformation increments for section $s$, $\beta_{0,s}$ is the intercept, $\boldsymbol{X}_s$ contains the standardized predictors, and $\boldsymbol{\beta}_s$ contains their regression coefficients. The residual term $\boldsymbol{\varepsilon}_s$ represents variation in monthly deformation that was not explained by the predictors. The parameter $\alpha_s$ describes the precision of this residual variation. A larger value of $\alpha_s$ corresponds to less unexplained variation around the fitted relation.

Coefficient shrinkage was introduced by assigning a zero-centered Gaussian prior to the regression coefficients \citep{bishop_pattern_2006},

\begin{equation}
\boldsymbol{\beta}_s
\sim
\mathcal{N}
\left(
\boldsymbol{0},
\lambda_s^{-1}\boldsymbol{I}
\right),
\label{eq:brr_prior}
\end{equation}

\noindent where $\lambda_s$ controls the strength of the shrinkage for section $s$. A larger value of $\lambda_s$ pulls weakly supported coefficients more strongly toward zero, whereas predictors that are consistently related to monthly deformation retain non-zero contributions. The hyperparameters $\alpha_s$ and $\lambda_s$ were estimated directly from the calibration data by maximizing the marginal likelihood (the evidence framework) via empirical Bayes \citep{mackay_bayesian_1992, bishop_pattern_2006}. In practical terms, this procedure allowed the observed record to determine both the unexplained noise level and the optimal degree of regularizing shrinkage without requiring manual penalty tuning.

Conventional ridge regression generally provides a single deterministic point estimate of coefficients for a chosen penalty. In contrast, Bayesian ridge regression yields a full posterior distribution over the model parameters, which is subsequently propagated to quantify predictive uncertainty in monthly estimates \citep{bishop_pattern_2006, gelman_bayesian_2013, tarantola_inverse_2005}.

A separate model was fitted for each depth section. Thus, the regression coefficients for a section were estimated only from its own MLCW deformation record, although its predictors could include hydraulic head changes from other sections of the monitored profile. The fitted relations were interpreted as empirical statistical associations within the Tuku monitoring record and not as a substitute for physically coupled groundwater flow and hydro-mechanical compaction models \citep{galloway_review_2011, burbey_extensometer_2020}.
```

---

## 3. Ready-to-Append BibTeX Entries for `writing_manu2.bib`

```bibtex
---
@article{dormann_collinearity_2013,
	title = {Collinearity: a review of methods to deal with it and a simulation study evaluating their performance},
	volume = {36},
	issn = {1600-0587},
	url = {https://doi.org/10.1111/j.1600-0587.2012.07348.x},
	doi = {10.1111/j.1600-0587.2012.07348.x},
	number = {1},
	journal = {Ecography},
	author = {Dormann, Carsten F. and Elith, Jane and Bacher, Sven and Buchmann, Carsten M. and Carl, Gudrun and Carr{\'e}, Gabriel and Garc{\'i}a M{\'a}rquez, Jaime Ricardo and Gruber, Bernd and Lafourcade, Bruno and Leit{\~a}o, Pedro J. and M{\"u}nkem{\"u}ller, Tamara and McClean, Colin J. and Osborne, Patrick E. and Reineking, Bj{\"o}rn and Schr{\"o}der, Boris and Skidmore, Andrew K. and Zurell, Damaris and Lautenbach, Sven},
	year = {2013},
	pages = {27--46},
}
---
@book{hastie_elements_2009,
	edition = {2nd},
	title = {The Elements of Statistical Learning: Data Mining, Inference, and Prediction},
	isbn = {978-0-387-84857-0},
	url = {https://doi.org/10.1007/978-0-387-84858-7},
	doi = {10.1007/978-0-387-84858-7},
	publisher = {Springer},
	author = {Hastie, Trevor and Tibshirani, Robert and Friedman, Jerome},
	year = {2009},
	address = {New York, NY},
}
---
@book{bishop_pattern_2006,
	title = {Pattern Recognition and Machine Learning},
	isbn = {978-0-387-31073-2},
	publisher = {Springer},
	author = {Bishop, Christopher M.},
	year = {2006},
	address = {New York, NY},
}
---
@book{gelman_bayesian_2013,
	edition = {3rd},
	title = {Bayesian Data Analysis},
	isbn = {978-1-4398-4095-5},
	url = {https://doi.org/10.1201/b16018},
	doi = {10.1201/b16018},
	publisher = {CRC Press},
	author = {Gelman, Andrew and Carlin, John B. and Stern, Hal S. and Dunson, David B. and Vehtari, Aki and Rubin, Donald B.},
	year = {2013},
	address = {Boca Raton, FL},
}
---
@book{tarantola_inverse_2005,
	title = {Inverse Problem Theory and Methods for Model Parameter Estimation},
	isbn = {978-0-89871-572-9},
	url = {https://doi.org/10.1137/1.9780898717921},
	doi = {10.1137/1.9780898717921},
	publisher = {SIAM: Society for Industrial and Applied Mathematics},
	author = {Tarantola, Albert},
	year = {2005},
	address = {Philadelphia, PA},
}
---
@article{galloway_review_2011,
	title = {Review: Regional land subsidence accompanying groundwater extraction},
	volume = {19},
	issn = {1431-2174, 1435-0157},
	url = {https://doi.org/10.1007/s10040-011-0775-5},
	doi = {10.1007/s10040-011-0775-5},
	number = {8},
	journal = {Hydrogeology Journal},
	author = {Galloway, Devin L. and Burbey, Thomas J.},
	year = {2011},
	pages = {1459--1486},
}
```
