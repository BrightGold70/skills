# Sample Size and Power Calculations

## Overview

Sample size calculation is essential for study planning. Inadequate sample size leads to underpowered studies that cannot detect meaningful effects, while excessive sample size wastes resources.

---

## Key Concepts

### Power Analysis Components

| Component | Symbol | Typical Value |
|-----------|--------|---------------|
| Significance level (Type I error) | α | 0.05 |
| Power (1 - Type II error) | 1-β | 0.80-0.90 |
| Effect size | d, RR, OR | Based on clinical significance |
| Variability | σ | From pilot data or literature |

### Type I and Type II Errors

| | Reality: No Effect | Reality: Effect Exists |
|---|-------------------|----------------------|
| **Study: Significant** | Type I error (α) | Correct (1-β) |
| **Study: Not Significant** | Correct (1-α) | Type II error (β) |

---

## 1. RCT Sample Size

### Continuous Outcome (Two-Group Comparison)

**Formula**:
```
n per group = 2 × (z_α/2 + z_β)² × σ² / Δ²
```

**Parameters**:
- σ = pooled standard deviation
- Δ = clinically meaningful difference
- z_α/2 = 1.96 (two-sided α = 0.05)
- z_β = 0.84 (80% power) or 1.28 (90% power)

**Example**:
```
Expected mean difference = 5 units
Expected SD = 15 units
α = 0.05, power = 80%

n = 2 × (1.96 + 0.84)² × 15² / 5²
n = 2 × 7.84 × 225 / 25
n = 141 per group
Total N = 282
```

**Using rmcp**:
```python
skill_mcp(mcp_name="rmcp", tool_name="power_rct",
    arguments={
        "alpha": 0.05,
        "power": 0.80,
        "effect_size": 0.33,  # d = 5/15
        "outcome_type": "continuous"
    })
```

### Binary Outcome (Two-Group Comparison)

**Formula**:
```
n per group = (z_α/2 + z_β)² × [p₁(1-p₁) + p₀(1-p₀)] / (p₁-p₀)²
```

**Parameters**:
- p₀ = expected proportion in control group
- p₁ = expected proportion in treatment group

**Example**:
```
Control event rate = 20%
Treatment event rate = 30%
α = 0.05, power = 80%

n = (1.96 + 0.84)² × [0.30×0.70 + 0.20×0.80] / (0.30-0.20)²
n = 7.84 × [0.21 + 0.16] / 0.01
n = 7.84 × 37
n = 290 per group
Total N = 580
```

### Time-to-Event Outcome

**Formula**:
```
Number of events required:
E = (z_α/2 + z_β)² × (1 + r)² / [r × log(HR)]²

Total sample size:
N = E / [S_control + r × S_treatment]
```

**Parameters**:
- r = allocation ratio
- HR = hazard ratio to detect
- S = proportion surviving without event

**Example**:
```
Control 2-year survival = 70%
Treatment 2-year survival = 80% (HR ≈ 0.63)
α = 0.05, power = 80%, r = 1

Events required:
E = (1.96 + 0.84)² × 4 / [1 × log(0.63)]²
E = 7.84 × 4 / 0.218
E = 144 events

Assuming 70% and 80% survival:
N = 144 / [(1-0.70) + (1-0.80)]
N = 144 / 0.5
N = 288 total
```

### Cluster RCT

**Formula**:
```
n_cluster = n_individual × [1 + (m-1)×ICC]

where:
m = average cluster size
ICC = intraclass correlation coefficient
```

**Example**:
```
Individual-level n = 100 per group
Cluster size m = 20
ICC = 0.05

DEFF = 1 + (20-1) × 0.05 = 1.95
Adjusted n = 100 × 1.95 = 195 per group
Number of clusters = 195/20 ≈ 10 clusters per group
```

---

## 2. Cohort Study Sample Size

### Incidence Rate Comparison

**Formula**:
```
Person-time required:
PT = (z_α/2 + z_β)² × (1/r_IR + 1) / [log(IRR)]²

where:
r_IR = IR_unexposed / IR_exposed
IRR = IR_ratio to detect
```

### Risk Ratio (Cumulative Incidence)

**Formula**:
```
n per group = (z_α/2 + z_β)² × [p₁(1-p₁) + p₀(1-p₀)] / (p₁-p₀)²

where:
p₀ = outcome proportion in unexposed
p₁ = p₀ × RR (expected RR)
```

**Example**:
```
Outcome in unexposed = 10%
Expected RR = 1.5
Exposure prevalence = 30%
Power = 80%, α = 0.05

p₀ = 0.10
p₁ = 0.10 × 1.5 = 0.15

n_unexposed = 7.84 × [0.15×0.85 + 0.10×0.90] / (0.05)²
n_unexposed = 7.84 × 0.2175 / 0.0025
n_unexposed = 682

Total sample (with 30% exposed):
N = n_unexposed / (1 - exposure_prevalence)
N = 682 / 0.70 = 974 total
```

**Using rmcp**:
```python
skill_mcp(mcp_name="rmcp", tool_name="power_cohort",
    arguments={
        "alpha": 0.05,
        "power": 0.80,
        "exposure_prevalence": 0.30,
        "expected_rr": 1.5,
        "outcome_prevalence_unexposed": 0.10
    })
```

---

## 3. Case-Control Study Sample Size

### Unmatched Design

**Formula**:
```
n per group = (z_α/2 + z_β)² × [p₁(1-p₁) + p₀(1-p₀)] / (p₁-p₀)²

where:
p₀ = exposure prevalence in controls
p₁ = (OR × p₀) / (1 - p₀ + OR × p₀)
```

**Example**:
```
Exposure in controls = 25%
Expected OR = 2.0
Case:control ratio = 1:1
Power = 80%, α = 0.05

p₀ = 0.25
p₁ = (2.0 × 0.25) / (1 - 0.25 + 2.0 × 0.25)
p₁ = 0.50 / 0.75 = 0.40

n = 7.84 × [0.40×0.60 + 0.25×0.75] / (0.15)²
n = 7.84 × 0.4275 / 0.0225
n = 149 per group
```

**Using rmcp**:
```python
skill_mcp(mcp_name="rmcp", tool_name="power_case_control",
    arguments={
        "alpha": 0.05,
        "power": 0.80,
        "exposure_prevalence_controls": 0.25,
        "expected_or": 2.0,
        "case_control_ratio": 1
    })
```

### Matched Design (1:1 Matching)

**Formula**:
```
n pairs = (z_α/2 + z_β)² / [log(OR)]² × [1/(p₀×(1-p₀)) + 1/(p₁×(1-p₁))]

Adjusted for discordant pairs:
n_pairs = n_unmatched / (2 × p₀ × (1-p₁) + 2 × p₁ × (1-p₀))
```

### Variable Case:Control Ratio

**Formula**:
```
With m controls per case:
n_cases = (1 + 1/m) × n_unmatched_case
n_controls = m × n_cases
```

**Efficiency**:
| Ratio | Relative Efficiency |
|-------|---------------------|
| 1:1 | 100% |
| 1:2 | 133% |
| 1:3 | 150% |
| 1:4 | 160% |
| 1:5 | 167% |

---

## 4. Cross-Sectional Study Sample Size

### Prevalence Estimation

**Formula**:
```
n = z_α/2² × p(1-p) / d²

where:
p = expected prevalence
d = desired precision (half-width of CI)
```

**Example**:
```
Expected prevalence = 25%
Desired precision = ±5%
α = 0.05

n = 1.96² × 0.25 × 0.75 / 0.05²
n = 3.84 × 0.1875 / 0.0025
n = 288
```

### Prevalence Ratio Comparison

**Same formula as cohort study for risk ratio**

---

## 5. Survival Analysis Sample Size

### Cox Regression

**Events Required**:
```
E = (z_α/2 + z_β)² / [log(HR)]² × (1 + Σpᵢβᵢ² / (p₁β₁²))

where:
HR = hazard ratio to detect
pᵢ = proportion with covariate i
βᵢ = regression coefficient for covariate i
```

**Simple Form (unadjusted)**:
```
E = 4 × (z_α/2 + z_β)² / [log(HR)]²
```

**Total Sample**:
```
N = E / (proportion with event)
```

---

## 6. Non-Inferiority Trials

### Non-Inferiority Margin

**Formula**:
```
n per group = 2 × (z_α + z_β)² × σ² / (Δ - δ)²

where:
Δ = expected difference (often 0)
δ = non-inferiority margin
```

**Example**:
```
Non-inferiority margin = 3 units
Expected true difference = 0
SD = 10 units
α = 0.025 (one-sided), power = 80%

n = 2 × (1.96 + 0.84)² × 100 / 9
n = 2 × 7.84 × 100 / 9
n = 174 per group
```

---

## 7. Cluster Sample Size Adjustments

### Design Effect

```
DEFF = 1 + (m-1) × ICC

Adjusted sample size = n_simple × DEFF
```

**Typical ICC Values**:
| Setting | ICC Range |
|---------|-----------|
| Individuals in families | 0.10-0.30 |
| Patients in clinics | 0.01-0.10 |
| Students in schools | 0.02-0.15 |
| Measurements over time | 0.30-0.60 |

---

## 8. Adjustments for Attrition

**Formula**:
```
n_adjusted = n_calculated / (1 - attrition_rate)
```

**Example**:
```
Calculated sample = 200 per group
Expected attrition = 20%

n_adjusted = 200 / 0.80 = 250 per group
```

---

## 9. Software Implementation

### R (pwr package)
```r
# Continuous outcome
pwr.t.test(d = 0.5, power = 0.80, sig.level = 0.05)

# Binary outcome
pwr.2p.test(h = ES.h(0.30, 0.20), power = 0.80)
```

### Python (statsmodels)
```python
from statsmodels.stats.power import tt_ind_solve_power

n = tt_ind_solve_power(
    effect_size=0.5,
    alpha=0.05,
    power=0.80
)
```

### G*Power

Free software for power analysis:
- Download: https://www.psychologie.hhu.de/gpower

---

## 10. Quick Reference Tables

### Continuous Outcome (Two Groups)

| Effect Size (d) | n per Group (80%) | n per Group (90%) |
|-----------------|-------------------|-------------------|
| 0.2 (small) | 394 | 527 |
| 0.3 | 176 | 235 |
| 0.5 (medium) | 64 | 86 |
| 0.8 (large) | 26 | 34 |

### Binary Outcome (Two Groups)

| p₁ - p₀ | n per Group (80%) |
|---------|-------------------|
| 0.10 | 199 |
| 0.15 | 89 |
| 0.20 | 50 |
| 0.25 | 32 |

### Survival Analysis

| HR | Events Required (80%) |
|----|----------------------|
| 0.5 | 66 |
| 0.6 | 110 |
| 0.7 | 197 |
| 0.8 | 442 |

---

## 11. Practical Considerations

1. **Conservative estimates**: Use larger sample size when uncertain
2. **Attrition**: Inflate for expected dropout
3. **Subgroup analyses**: May require larger sample
4. **Interim analyses**: Adjust for multiple looks
5. **Multiple outcomes**: Control for multiplicity
6. **Feasibility**: Balance scientific needs with resources
