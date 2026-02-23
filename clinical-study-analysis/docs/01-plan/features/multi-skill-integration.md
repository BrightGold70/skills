# PDCA Plan: Multi-Skill Integration for clinical-study-analysis

## 1. Goal Description

Enhance the `clinical-study-analysis` skill by integrating **biopython**, **scikit-survival**, and **statistical-analysis** skills to create a comprehensive clinical study analysis platform that combines genomic analysis, survival modeling, and statistical validation in a unified workflow.

## 2. Background

The current `clinical-study-analysis` skill focuses on clinical trial and epidemiological analysis using R-based statistics via `rmcp`. However, clinical research increasingly requires:

- **Genomic integration**: Biomarker discovery, molecular classification (e.g., FLT3 mutations in AML, TP53 in MDS)
- **Python ML survival models**: Random Survival Forests, Gradient Boosting for clinical prognostication
- **Comprehensive statistical validation**: Formal assumption checking, power analysis, APA-style reporting

Existing skill references are documented but not deeply integrated. This upgrade creates seamless cross-skill workflows.

## 3. Features

### 3.1 Biopython Integration (Genomic Analysis)

| Feature | Description | Clinical Use Case |
|---------|-------------|-------------------|
| Sequence Retrieval | Fetch gene sequences from NCBI via Biopython | Retrieve FLT3, NPM1, TP53 sequences for primer design |
| BLAST Analysis | Run BLAST searches for variant annotation | Identify similar sequences to novel variants |
| Sequence Statistics | GC content, molecular weight, translation | Quality control for genomic data |
| Multiple Alignment | Align gene sequences across patients | Phylogenetic analysis of tumor clones |

### 3.2 Scikit-Survival Integration (ML Survival Analysis)

| Feature | Description | Clinical Use Case |
|---------|-------------|-------------------|
| Cox Models | Standard and penalized (L1/L2/Elastic Net) | High-dimensional genomic survival models |
| Random Survival Forests | Non-parametric ensemble | Capture non-linear relationships |
| Evaluation Metrics | Uno's C-index, Integrated Brier Score | Robust model validation with high censoring |
| Competing Risks | Cumulative incidence, Fine-Gray model | CIR vs NRM in transplant studies |

### 3.3 Statistical-Analysis Integration (Validation Pipeline)

| Feature | Description | Clinical Use Case |
|---------|-------------|-------------------|
| Assumption Checking | Normality, homogeneity, linearity | Pre-model validation |
| Power Analysis | A priori sample size calculation | Trial design |
| Effect Sizes | Cohen's d, η², with CIs | Clinical significance reporting |
| APA Reporting | Formal statistical write-ups | Manuscript preparation |

### 3.4 Unified Workflow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CLINICAL STUDY ANALYSIS PIPELINE                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐             │
│  │   DATA       │───▶│  STATISTICAL │───▶│   SURVIVAL  │             │
│  │   INGESTION  │    │  ANALYSIS    │    │   MODELING  │             │
│  └──────────────┘    └──────────────┘    └──────────────┘             │
│         │                   │                    │                     │
│         ▼                   ▼                    ▼                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐             │
│  │  BIOPYTHON   │    │  ASSUMPTION  │    │   SCIKIT-   │             │
│  │  (Genomic)   │    │   CHECKS     │    │  SURVIVAL   │             │
│  └──────────────┘    └──────────────┘    └──────────────┘             │
│         │                   │                    │                     │
│         └───────────────────┴────────────────────┘                     │
│                             ▼                                           │
│                    ┌──────────────┐                                      │
│                    │   REPORT    │                                      │
│                    │  GENERATION │                                      │
│                    └──────────────┘                                      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## 4. Integration Architecture

### 4.1 Skill Metadata Updates

Update `SKILL.md` metadata to include new tags:
```yaml
tags: [clinical, epidemiology, biostatistics, survival-analysis, 
       hematology, genomics, python, r, biopython, scikit-survival, 
       statistical-analysis]
```

### 4.2 Cross-Skill Reference Section

Add new section "Cross-Skill Integration" with:
- Task-to-skill mapping table
- Sequential workflow examples
- Tool availability matrix

### 4.3 Workflow Scripts

Create example scripts demonstrating:
- `scripts/genomic_survival_analysis.py`: Biopython → scikit-survival pipeline
- `scripts/statistical_validation.py`: statistical-analysis → survival workflow
- `scripts/unified_clinical_analysis.R`: R + Python integration

## 5. Success Criteria

- [ ] SKILL.md updated with all three skill integrations documented
- [ ] Cross-skill workflow examples added (minimum 3)
- [ ] New reference document created: `references/multi_skill_workflows.md`
- [ ] Example scripts added demonstrating integration (minimum 3)
- [ ] Tag metadata updated in SKILL.md
- [ ] PDCA Design document created
- [ ] Implementation verified with test cases

## 6. Risks and Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Skill version conflicts | Medium | Use virtual environments, document version requirements |
| Data transfer between R/Python | Medium | Use common formats (CSV, JSON), document conversion steps |
| Complexity overload | High | Provide simple "get started" workflows before advanced features |

## 7. Timeline Estimate

- **Plan**: This document
- **Design**: 1 day
- **Implementation**: 2-3 days  
- **Check/Verification**: 1 day
- **Total**: ~5 days
