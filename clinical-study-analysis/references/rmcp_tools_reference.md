# rmcp MCP Tools Reference

## Overview

rmcp (R MCP Server) provides 52 statistical analysis tools across 11 categories, leveraging 429 R packages from CRAN task views. This reference documents all available tools for clinical study analysis.

## Installation and Configuration

### Installation

```bash
pip install rmcp
```

### Configuration for OpenCode

Add to `~/.mcp.json`:
```json
{
  "mcpServers": {
    "rmcp": {
      "command": "rmcp",
      "args": ["start"]
    }
  }
}
```

### Alternative: HTTP Server (No Installation)

```
HTTP Server: https://rmcp-server-394229601724.us-central1.run.app/mcp
Interactive Docs: https://rmcp-server-394229601724.us-central1.run.app/docs
```

---

## Tool Categories

### 1. Regression & Economics

#### `linear_regression`
Linear regression with diagnostics.

```python
skill_mcp(mcp_name="rmcp", tool_name="linear_regression",
    arguments={
        "data": "dataset",
        "formula": "outcome ~ predictor1 + predictor2",
        "robust_se": True,  # Heteroskedasticity-robust SEs
        "weights": "sample_weight"  # Optional
    })
```

#### `logistic_regression`
Logistic regression for binary outcomes.

```python
skill_mcp(mcp_name="rmcp", tool_name="logistic_regression",
    arguments={
        "data": "dataset",
        "formula": "outcome ~ exposure + age + sex",
        "family": "binomial",
        "offset": "log(person_years)"  # For rate models
    })
```

#### `poisson_regression`
Poisson regression for count/rate outcomes.

```python
skill_mcp(mcp_name="rmcp", tool_name="poisson_regression",
    arguments={
        "data": "dataset",
        "formula": "count ~ exposure + offset(log(person_time))",
        "exposure": "person_years"
    })
```

#### `iv_regression`
Instrumental variables regression (2SLS).

```python
skill_mcp(mcp_name="rmcp", tool_name="iv_regression",
    arguments={
        "data": "dataset",
        "formula": "outcome ~ endogenous_var | instrument",
        "method": "2sls"
    })
```

#### `panel_regression`
Panel data models (fixed/random effects).

```python
skill_mcp(mcp_name="rmcp", tool_name="panel_regression",
    arguments={
        "data": "panel_data",
        "formula": "y ~ x1 + x2",
        "entity_var": "id",
        "time_var": "year",
        "model": "within"  # "within", "random", "between"
    })
```

---

### 2. Survival Analysis

#### `kaplan_meier`
Kaplan-Meier survival curves.

```python
skill_mcp(mcp_name="rmcp", tool_name="kaplan_meier",
    arguments={
        "data": "survival_data",
        "time_var": "follow_up_days",
        "event_var": "event",
        "stratify_by": "treatment_group",
        "conf_level": 0.95,
        "plot": True
    })
```

#### `cox_regression`
Cox proportional hazards model.

```python
skill_mcp(mcp_name="rmcp", tool_name="cox_regression",
    arguments={
        "data": "survival_data",
        "time_var": "time",
        "event_var": "event",
        "covariates": ["age", "sex", "treatment"],
        "strata": "site",  # Optional stratification
        "robust_se": True,
        "time_varying": False  # For time-varying covariates
    })
```

#### `ph_test`
Test proportional hazards assumption.

```python
skill_mcp(mcp_name="rmcp", tool_name="ph_test",
    arguments={
        "model": "cox_model",
        "method": "schoenfeld"  # Schoenfeld residuals test
    })
```

#### `competing_risks`
Competing risks analysis (Fine-Gray model).

```python
skill_mcp(mcp_name="rmcp", tool_name="competing_risks",
    arguments={
        "data": "survival_data",
        "time_var": "time",
        "event_var": "event_type",
        "event_of_interest": 1,
        "competing_event": 2,
        "covariates": ["age", "exposure"]
    })
```

#### `accelerated_failure_time`
Accelerated failure time models.

```python
skill_mcp(mcp_name="rmcp", tool_name="accelerated_failure_time",
    arguments={
        "data": "survival_data",
        "time_var": "time",
        "event_var": "event",
        "distribution": "weibull",  # "weibull", "exponential", "lognormal"
        "covariates": ["x1", "x2"]
    })
```

---

### 3. Hypothesis Testing

#### `t_test`
Student's t-test (independent or paired).

```python
skill_mcp(mcp_name="rmcp", tool_name="t_test",
    arguments={
        "data": "dataset",
        "var": "outcome",
        "group_var": "group",
        "paired": False,
        "var_equal": False,  # Welch's t-test
        "alternative": "two.sided"  # "two.sided", "less", "greater"
    })
```

#### `anova`
Analysis of variance.

```python
skill_mcp(mcp_name="rmcp", tool_name="anova",
    arguments={
        "data": "dataset",
        "formula": "outcome ~ group",
        "type": 2,  # Type II SS
        "post_hoc": "tukey"  # Tukey HSD
    })
```

#### `chi_square`
Chi-square test of independence.

```python
skill_mcp(mcp_name="rmcp", tool_name="chi_square",
    arguments={
        "data": "dataset",
        "var1": "exposure",
        "var2": "outcome",
        "correct": True  # Yates' continuity correction
    })
```

#### `fisher_exact`
Fisher's exact test.

```python
skill_mcp(mcp_name="rmcp", tool_name="fisher_exact",
    arguments={
        "data": "dataset",
        "var1": "exposure",
        "var2": "outcome"
    })
```

#### `mann_whitney`
Mann-Whitney U test (Wilcoxon rank-sum).

```python
skill_mcp(mcp_name="rmcp", tool_name="mann_whitney",
    arguments={
        "data": "dataset",
        "var": "outcome",
        "group_var": "group"
    })
```

#### `kruskal_wallis`
Kruskal-Wallis test.

```python
skill_mcp(mcp_name="rmcp", tool_name="kruskal_wallis",
    arguments={
        "data": "dataset",
        "var": "outcome",
        "group_var": "group"
    })
```

---

### 4. Missing Data

#### `missing_pattern`
Analyze missing data patterns.

```python
skill_mcp(mcp_name="rmcp", tool_name="missing_pattern",
    arguments={
        "data": "dataset",
        "plot": True
    })
```

#### `mice_imputation`
Multiple imputation by chained equations.

```python
skill_mcp(mcp_name="rmcp", tool_name="mice_imputation",
    arguments={
        "data": "dataset",
        "m": 20,  # Number of imputations
        "method": "pmm",  # Predictive mean matching
        "maxit": 10,  # Iterations
        "predictor_matrix": "auto"
    })
```

#### `pool_results`
Pool results from multiply imputed datasets.

```python
skill_mcp(mcp_name="rmcp", tool_name="pool_results",
    arguments={
        "models": "imputed_models",
        "method": "rubin"  # Rubin's rules
    })
```

---

### 5. Causal Inference

#### `propensity_match`
Propensity score matching.

```python
skill_mcp(mcp_name="rmcp", tool_name="propensity_match",
    arguments={
        "data": "dataset",
        "treatment": "exposure",
        "covariates": ["age", "sex", "comorbidity1"],
        "method": "nearest",  # "nearest", "optimal", "full"
        "caliper": 0.2,
        "ratio": 1  # 1:1 matching
    })
```

#### `propensity_weight`
Inverse probability of treatment weighting (IPTW).

```python
skill_mcp(mcp_name="rmcp", tool_name="propensity_weight",
    arguments={
        "data": "dataset",
        "treatment": "exposure",
        "outcome": "outcome",
        "covariates": ["age", "sex"],
        "stabilized": True
    })
```

#### `evalue`
Calculate E-value for unmeasured confounding.

```python
skill_mcp(mcp_name="rmcp", tool_name="evalue",
    arguments={
        "estimate": 2.5,
        "ci_lower": 1.8,
        "estimate_type": "OR"  # "OR", "RR", "HR", "SMD"
    })
```

#### `mediation_analysis`
Causal mediation analysis.

```python
skill_mcp(mcp_name="rmcp", tool_name="mediation_analysis",
    arguments={
        "data": "dataset",
        "treatment": "exposure",
        "mediator": "mediator_var",
        "outcome": "outcome",
        "covariates": ["age", "sex"],
        "boot": 1000  # Bootstrap samples
    })
```

---

### 6. Machine Learning

#### `random_forest`
Random forest for prediction.

```python
skill_mcp(mcp_name="rmcp", tool_name="random_forest",
    arguments={
        "data": "dataset",
        "formula": "outcome ~ .",
        "ntree": 500,
        "mtry": "auto",
        "importance": True
    })
```

#### `gradient_boosting`
Gradient boosting machine.

```python
skill_mcp(mcp_name="rmcp", tool_name="gradient_boosting",
    arguments={
        "data": "dataset",
        "formula": "outcome ~ .",
        "n_trees": 1000,
        "learning_rate": 0.01,
        "max_depth": 3
    })
```

#### `cross_validation`
K-fold cross-validation.

```python
skill_mcp(mcp_name="rmcp", tool_name="cross_validation",
    arguments={
        "data": "dataset",
        "model": "rf_model",
        "k": 10,
        "metric": "auc"  # "auc", "accuracy", "rmse"
    })
```

---

### 7. Meta-Analysis

#### `meta_analysis`
Fixed/random effects meta-analysis.

```python
skill_mcp(mcp_name="rmcp", tool_name="meta_analysis",
    arguments={
        "data": "studies",
        "effect_sizes": "log_or",
        "standard_errors": "se",
        "method": "REML",  # "fixed", "DL", "REML", "HE"
        "plot": True
    })
```

#### `forest_plot`
Generate forest plot.

```python
skill_mcp(mcp_name="rmcp", tool_name="forest_plot",
    arguments={
        "meta_object": "meta_result",
        "study_labels": "study_names",
        "xlab": "Odds Ratio"
    })
```

#### `funnel_plot`
Funnel plot for publication bias.

```python
skill_mcp(mcp_name="rmcp", tool_name="funnel_plot",
    arguments={
        "meta_object": "meta_result",
        "contour": True
    })
```

#### `egger_test`
Egger's test for publication bias.

```python
skill_mcp(mcp_name="rmcp", tool_name="egger_test",
    arguments={
        "meta_object": "meta_result"
    })
```

---

### 8. Time Series

#### `arima`
ARIMA models.

```python
skill_mcp(mcp_name="rmcp", tool_name="arima",
    arguments={
        "data": "time_series",
        "y": "value",
        "order": [1, 1, 1],  # (p, d, q)
        "seasonal": [0, 0, 0]  # (P, D, Q, period)
    })
```

#### `forecast`
Time series forecasting.

```python
skill_mcp(mcp_name="rmcp", tool_name="forecast",
    arguments={
        "model": "arima_model",
        "h": 12  # Forecast horizon
    })
```

---

### 9. Descriptive Statistics

#### `descriptive_statistics`
Summary statistics.

```python
skill_mcp(mcp_name="rmcp", tool_name="descriptive_statistics",
    arguments={
        "data": "dataset",
        "variables": ["age", "bmi", "outcome"],
        "stratify_by": "group",
        "statistics": ["mean", "sd", "median", "iqr", "n", "missing"]
    })
```

#### `frequency_table`
Frequency tables.

```python
skill_mcp(mcp_name="rmcp", tool_name="frequency_table",
    arguments={
        "data": "dataset",
        "variables": ["sex", "treatment"],
        "percent": True
    })
```

#### `correlation_matrix`
Correlation matrix.

```python
skill_mcp(mcp_name="rmcp", tool_name="correlation_matrix",
    arguments={
        "data": "dataset",
        "variables": ["var1", "var2", "var3"],
        "method": "pearson",  # "pearson", "spearman", "kendall"
        "plot": True
    })
```

---

### 10. Data Manipulation

#### `filter_data`
Filter rows.

```python
skill_mcp(mcp_name="rmcp", tool_name="filter_data",
    arguments={
        "data": "dataset",
        "condition": "age >= 18 & outcome == 1"
    })
```

#### `select_variables`
Select columns.

```python
skill_mcp(mcp_name="rmcp", tool_name="select_variables",
    arguments={
        "data": "dataset",
        "variables": ["id", "age", "sex", "outcome"]
    })
```

#### `create_variable`
Create new variables.

```python
skill_mcp(mcp_name="rmcp", tool_name="create_variable",
    arguments={
        "data": "dataset",
        "name": "bmi_category",
        "expression": "case_when(bmi < 18.5 ~ 'underweight', bmi < 25 ~ 'normal', bmi < 30 ~ 'overweight', TRUE ~ 'obese')"
    })
```

#### `merge_datasets`
Merge datasets.

```python
skill_mcp(mcp_name="rmcp", tool_name="merge_datasets",
    arguments={
        "data1": "dataset1",
        "data2": "dataset2",
        "by": ["id"],
        "how": "left"  # "left", "right", "inner", "full"
    })
```

#### `reshape_data`
Reshape data (wide/long).

```python
skill_mcp(mcp_name="rmcp", tool_name="reshape_data",
    arguments={
        "data": "dataset",
        "direction": "long",
        "id_var": "patient_id",
        "time_var": "visit",
        "varying": ["measure1", "measure2", "measure3"]
    })
```

---

### 11. Visualization

#### `ggplot`
Create ggplot2 visualizations.

```python
skill_mcp(mcp_name="rmcp", tool_name="ggplot",
    arguments={
        "data": "dataset",
        "aes": {"x": "age", "y": "outcome", "color": "group"},
        "geom": "point",
        "facets": "~sex",
        "title": "Scatter plot by group and sex"
    })
```

#### `histogram`
Histogram.

```python
skill_mcp(mcp_name="rmcp", tool_name="histogram",
    arguments={
        "data": "dataset",
        "variable": "age",
        "bins": 30,
        "fill": "group"
    })
```

#### `boxplot`
Box plot.

```python
skill_mcp(mcp_name="rmcp", tool_name="boxplot",
    arguments={
        "data": "dataset",
        "x": "group",
        "y": "outcome",
        "fill": "sex"
    })
```

#### `bar_plot`
Bar chart.

```python
skill_mcp(mcp_name="rmcp", tool_name="bar_plot",
    arguments={
        "data": "dataset",
        "x": "category",
        "y": "count",
        "fill": "group",
        "position": "dodge"
    })
```

---

## Power Analysis Tools

#### `power_rct`
Sample size for RCT.

```python
skill_mcp(mcp_name="rmcp", tool_name="power_rct",
    arguments={
        "alpha": 0.05,
        "power": 0.80,
        "effect_size": 0.5,
        "outcome_type": "continuous",  # "continuous", "binary"
        "allocation_ratio": 1
    })
```

#### `power_cohort`
Sample size for cohort study.

```python
skill_mcp(mcp_name="rmcp", tool_name="power_cohort",
    arguments={
        "alpha": 0.05,
        "power": 0.80,
        "exposure_prevalence": 0.3,
        "expected_rr": 1.5,
        "outcome_prevalence_unexposed": 0.1
    })
```

#### `power_case_control`
Sample size for case-control study.

```python
skill_mcp(mcp_name="rmcp", tool_name="power_case_control",
    arguments={
        "alpha": 0.05,
        "power": 0.80,
        "exposure_prevalence_controls": 0.2,
        "expected_or": 2.0,
        "case_control_ratio": 1
    })
```

---

## R Packages Used

rmcp leverages the following R packages:

| Category | Packages |
|----------|----------|
| Core | stats, base |
| Regression | AER, plm, ivreg, MASS |
| Survival | survival, survminer, cmprsk |
| Missing Data | mice, Amelia, missForest |
| Causal | MatchIt, WeightIt, mediation, dagitty |
| ML | randomForest, xgboost, e1071, caret |
| Meta | meta, metafor |
| Time Series | forecast, tseries |
| Visualization | ggplot2, patchwork |
| Data | dplyr, tidyr, data.table |

---

## Additional Resources

- **rmcp GitHub**: https://github.com/finite-sample/rmcp
- **Documentation**: https://finite-sample.github.io/rmcp/
- **PyPI**: https://pypi.org/project/rmcp/
- **CRAN Task Views**: https://cran.r-project.org/web/views/
