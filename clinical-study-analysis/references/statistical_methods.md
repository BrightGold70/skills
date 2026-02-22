# Statistical Methods for Clinical Studies

## Overview

This reference provides detailed statistical method guidance organized by study design.

---

## 1. Randomized Controlled Trials (RCTs)

### Primary Analysis

#### Continuous Outcomes

**Linear Regression / ANCOVA**
- Compare means between treatment groups
- Adjust for baseline values (ANCOVA increases power)
- Report: mean difference, 95% CI, p-value, effect size (Cohen's d)

```
Model: Y_post = β0 + β1*treatment + β2*Y_baseline + ε
β1 = adjusted mean difference
```

**Assumptions**:
- Normality of residuals
- Homogeneity of variance
- Linearity

**When violated**: Use robust standard errors, bootstrap, or non-parametric tests

#### Binary Outcomes

**Logistic Regression**
- Compare proportions between treatment groups
- Report: risk ratio (preferred) or odds ratio, 95% CI, p-value

```
Model: logit(P(Y=1)) = β0 + β1*treatment + β2*covariates
RR = P(treatment)/P(control)
```

**Risk Ratio vs Odds Ratio**:
- RR is more interpretable for clinical trials
- OR approximates RR when outcome is rare (<10%)
- Report both absolute risk difference and relative effect

#### Time-to-Event Outcomes

**Cox Proportional Hazards Model**
- Compare survival between treatment groups
- Report: hazard ratio, 95% CI, p-value, median survival times

```
Model: h(t|X) = h0(t) * exp(β1*treatment + β2*covariates)
HR = exp(β1)
```

**Assumptions**:
- Proportional hazards (test with Schoenfeld residuals)
- Independent censoring

**When PH violated**: Use stratified Cox, time-varying coefficients, or accelerated failure time models

### Secondary Analyses

#### Subgroup Analysis
- Pre-specify subgroups in protocol
- Test for interaction (treatment × subgroup)
- Report with forest plot
- Interpret cautiously (exploratory)

#### Per-Protocol Analysis
- Include only participants who adhered to protocol
- Compare with ITT results
- Discuss discrepancies

#### Intention-to-Treat vs Per-Protocol

| Aspect | ITT | Per-Protocol |
|--------|-----|--------------|
| Principle | Analyze as randomized | Analyze as treated |
| Preserves randomization | Yes | No |
| Real-world effectiveness | Yes | No |
| Internal validity | High | Lower |
| Primary analysis | Recommended | Sensitivity |

---

## 2. Prospective Cohort Studies

### Incidence Rate Calculation

```
Incidence Rate = Number of new cases / Person-time at risk

Person-time = Σ(follow-up time for each participant)
```

**95% CI for Incidence Rate**:
```
IR ± 1.96 × √(cases) / person-time
```

### Rate Ratio (Incidence Rate Ratio)

```
IRR = IR(exposed) / IR(unexposed)

Poisson Regression:
log(E[cases]) = β0 + β1*exposure + log(person-time)
IRR = exp(β1)
```

### Risk Ratio (Relative Risk)

```
RR = Cumulative Incidence(exposed) / Cumulative Incidence(unexposed)
RR = (a/(a+b)) / (c/(c+d))
```

**95% CI for RR**:
```
log(RR) ± 1.96 × √(1/a - 1/(a+b) + 1/c - 1/(c+d))
```

### Cox Proportional Hazards Model

**Standard Model**:
```
h(t|X) = h0(t) × exp(β1*exposure + Σβi*covariates)
HR = exp(β1)
```

**With Time-Varying Covariates**:
```
h(t|X) = h0(t) × exp(β1*exposure(t) + Σβi*covariates(t))
```

**Proportional Hazards Test**:
1. Schoenfeld residuals test
2. Log-log survival plots
3. Time × covariate interaction

**When PH Violated**:
1. Stratified Cox model
2. Time-dependent coefficients
3. Accelerated failure time models
4. Competing risks models

### Competing Risks

When multiple mutually exclusive event types exist:

**Cumulative Incidence Function (CIF)**:
```
CIF_k(t) = ∫₀ᵗ h_k(s) × S(s) ds

where S(s) = overall survival
```

**Fine-Gray Model**:
```
Subdistribution HR for cause k:
h_k^SD(t) = h_k^SD(t) × exp(β*X)
```

**Interpretation**: Subdistribution HR accounts for competing events

---

## 3. Case-Control Studies

### Odds Ratio

```
Unmatched OR:
OR = (a×d) / (b×c)
   = (cases exposed/cases unexposed) / (controls exposed/controls unexposed)

95% CI for OR:
log(OR) ± 1.96 × √(1/a + 1/b + 1/c + 1/d)
```

### Matched Analysis

**Conditional Logistic Regression**:
```
For matched sets, condition on the set:
L = Πᵢ [exp(βXᵢᶜᵃˢᵉ) / Σⱼ exp(βXᵢⱼ)]
```

**Mantel-Haenszel OR**:
```
OR_MH = Σ(aᵢdᵢ/Nᵢ) / Σ(bᵢcᵢ/Nᵢ)

where each i is a matched stratum
```

### Why OR in Case-Control Studies

| Reason | Explanation |
|--------|-------------|
| Cannot calculate RR | Denominator (exposed/unexposed population) unknown |
| OR estimates RR | When disease is rare (OR ≈ RR) |
| OR is valid | Regardless of sampling design |

**When OR ≠ RR**:
- Common outcome (>10%)
- Need to report that OR overestimates RR
- Consider prevalence OR as approximation

### Control Selection

| Strategy | Description | Advantage |
|----------|-------------|-----------|
| Population-based | Random sample from source population | Best generalizability |
| Hospital-based | From same facilities as cases | Feasible, similar healthcare access |
| Friend controls | Nominated by cases | Similar SES |
| Registry-based | From disease registries | Complete capture |

---

## 4. Cross-Sectional Studies

### Prevalence

```
Point Prevalence = Number of cases at time T / Population at risk at T
Period Prevalence = (Existing + New cases) / Population at risk
```

### Prevalence Ratio

```
PR = Prevalence(exposed) / Prevalence(unexposed)
PR = (a/(a+b)) / (c/(c+d))
```

**Estimating PR**:
- Log-binomial regression (preferred)
- Poisson regression with robust SE
- Logistic regression (yields OR, not PR)

### Survey-Weighted Analysis

For complex survey designs:

```
Weight = 1 / (Probability of selection × Response rate)

Weighted prevalence = Σ(wᵢ × yᵢ) / Σwᵢ
```

---

## 5. Confounding Control Methods

### Stratification

**Mantel-Haenszel Method**:
```
Pooled OR_MH = Σ(aᵢdᵢ/Nᵢ) / Σ(bᵢcᵢ/Nᵢ)

Test for homogeneity: Breslow-Day test
```

### Regression Adjustment

**Outcome Regression**:
```
Y = β0 + β1*exposure + β2*confounders + ε
β1 = adjusted effect of exposure
```

### Propensity Score Methods

**Propensity Score**: P(exposure=1 | covariates)

**Matching**:
1. Estimate PS using logistic regression
2. Match exposed to unexposed (1:1, 1:k, optimal)
3. Compare outcomes in matched sample

**Weighting (IPTW)**:
```
Weight = 1/PS for exposed, 1/(1-PS) for unexposed

Stabilized weight:
W_exposed = P(E=1) / PS
W_unexposed = (1-P(E=1)) / (1-PS)
```

**Stratification**:
- Stratify by PS quintiles
- Estimate effect within each stratum
- Pool across strata

### Instrumental Variables

**Conditions for Valid IV**:
1. Associated with exposure (relevance)
2. Not associated with confounders (exclusion)
3. Affects outcome only through exposure (exclusion restriction)

**Two-Stage Least Squares**:
```
Stage 1: Exposure = γ0 + γ1*IV + γ2*covariates + ε
Stage 2: Outcome = β0 + β1*Exposurê + β2*covariates + ε
```

**Interpretation**: LATE (Local Average Treatment Effect) for compliers

---

## 6. Missing Data Methods

### Types of Missing Data

| Mechanism | Description | Method |
|-----------|-------------|--------|
| MCAR | Missing completely at random | Complete case analysis valid |
| MAR | Missing at random (given observed data) | Multiple imputation, IPW |
| MNAR | Missing not at random | Sensitivity analysis, selection models |

### Multiple Imputation (MICE)

**Steps**:
1. Create m copies of dataset (m = 20-50)
2. Impute missing values using predictive models
3. Analyze each complete dataset
4. Pool results using Rubin's rules

**Rubin's Rules**:
```
Pooled estimate: Q̄ = (1/m) ΣQ̂ᵢ

Between-imputation variance: B = (1/(m-1)) Σ(Q̂ᵢ - Q̄)²

Within-imputation variance: W̄ = (1/m) ΣVᵢ

Total variance: T = W̄ + (1 + 1/m)×B

95% CI: Q̄ ± t_df × √T
```

---

## 7. Sensitivity Analyses

### E-value (Unmeasured Confounding)

```
For risk ratio RR > 1:
E-value = RR + √(RR × (RR - 1))

Interpretation: Minimum strength of association that unmeasured confounder 
would need with both exposure and outcome to fully explain observed effect
```

### Quantitative Bias Analysis

```
Bias-adjusted OR = Observed OR / Bias factor

where Bias factor depends on:
- Confounder-prevalence in unexposed
- Confounder-outcome association
- Confounder-exposure association
```

---

## 8. Sample Size Formulas

### RCT (Continuous Outcome)

```
n per group = 2 × (z_α/2 + z_β)² × σ² / Δ²

where:
σ = standard deviation
Δ = clinically meaningful difference
z_α/2 = 1.96 for α=0.05
z_β = 0.84 for 80% power
```

### RCT (Binary Outcome)

```
n per group = (z_α/2 + z_β)² × [p₁(1-p₁) + p₀(1-p₀)] / (p₁-p₀)²

where p₁, p₀ = expected proportions in each group
```

### Cohort Study

```
n per group = (z_α/2 + z_β)² × [p₁(1-p₁)/k + p₀(1-p₀)] / (p₁-p₀)²

where:
p₀ = outcome proportion in unexposed
p₁ = p₀ × RR
k = ratio of unexposed to exposed
```

### Case-Control Study

```
n per group = (z_α/2 + z_β)² × [p₁(1-p₁) + p₀(1-p₀)] / (p₁-p₀)²

where:
p₀ = exposure proportion in controls
p₁ = (OR × p₀) / (1 - p₀ + OR × p₀)
```

---

## 9. Effect Size Interpretation

### Cohen's d (Continuous)

| d | Interpretation |
|---|----------------|
| 0.2 | Small |
| 0.5 | Medium |
| 0.8 | Large |

### Risk Ratio / Hazard Ratio

| RR/HR | Interpretation |
|-------|----------------|
| 0.9-1.1 | Negligible |
| 0.7-0.9 or 1.1-1.3 | Small |
| 0.5-0.7 or 1.3-1.7 | Medium |
| <0.5 or >1.7 | Large |

### Odds Ratio

| OR | Interpretation |
|----|----------------|
| 1.0-1.5 | Weak |
| 1.5-3.0 | Moderate |
| >3.0 | Strong |

**Note**: OR interpretation depends on outcome prevalence

---

## 10. Reporting Guidelines

### Key Reporting Elements

1. **Effect estimate**: Point estimate (HR, RR, OR, mean difference)
2. **Precision**: 95% confidence interval
3. **Statistical significance**: p-value
4. **Clinical significance**: Absolute risk, NNT
5. **Model diagnostics**: Assumption checks
6. **Sensitivity analyses**: Robustness of findings

### Forest Plot Elements

- Study identifier
- Effect estimate and CI for each study
- Pooled estimate
- Heterogeneity statistic (I²)
- Weights
- Reference line (null effect)
