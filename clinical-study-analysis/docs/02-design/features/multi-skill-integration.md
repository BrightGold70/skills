# PDCA Design: Multi-Skill Integration for clinical-study-analysis

## 1. System Architecture

### 1.1 Overview

The multi-skill integration extends the existing `clinical-study-analysis` skill to create a unified clinical research platform. The architecture follows a **hub-and-spoke** pattern where `clinical-study-analysis` serves as the hub, coordinating specialized skills (spokes) for domain-specific tasks.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          clinical-study-analysis (HUB)                       │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        ORCHESTRATION LAYER                           │   │
│  │  • Task routing (which skill for which task)                         │   │
│  │  • Data format conversion (R ↔ Python)                               │   │
│  │  • Workflow coordination                                             │   │
│  │  • Result aggregation                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                       │
│              ┌───────────────────────┼───────────────────────┐              │
│              ▼                       ▼                       ▼              │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐     │
│  │    biopython     │    │ scikit-survival  │    │ statistical-     │     │
│  │    (SPOKE)       │    │    (SPOKE)       │    │   analysis       │     │
│  │                  │    │                  │    │    (SPOKE)       │     │
│  │ • Seq retrieval  │    │ • Cox models     │    │ • Assumption     │     │
│  │ • BLAST          │    │ • RSF/GBS        │    │   checks         │     │
│  │ • Alignment      │    │ • Competing      │    │ • Power analysis │     │
│  │ • Statistics     │    │   risks          │    │ • APA reporting  │     │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘     │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        EXISTING LAYER                                │   │
│  │  • rmcp MCP (R-based statistical computing)                          │   │
│  │  • Hematology specialization                                         │   │
│  │  • Study design taxonomy                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Integration Layers

| Layer | Responsibility | Technologies |
|-------|----------------|--------------|
| **Orchestration** | Task routing, data conversion, workflow coordination | Python, R, JSON |
| **Skill Spokes** | Domain-specific analysis | biopython, scikit-survival, statistical-analysis |
| **Existing** | R-based statistics via rmcp | R, survival, survminer |

---

## 2. Component Design

### 2.1 SKILL.md Updates

#### 2.1.1 Metadata Section (Lines 1-5)

**Current:**
```yaml
name: clinical-study-analysis
description: Comprehensive clinical study data analysis...
mcp: [rmcp]
tags: [clinical, epidemiology, biostatistics, survival-analysis, hematology, leukemia, lymphoma, oncology, r, statistics]
```

**Updated:**
```yaml
name: clinical-study-analysis
description: Comprehensive clinical study data analysis for prospective, retrospective, and epidemiological studies, with genomic integration and ML-based survival modeling. Specializes in Hematology research (AML, CML, MM, Lymphoma). Integrates rmcp MCP for R-based statistics, biopython for genomics, scikit-survival for ML survival models, and statistical-analysis for validation.
mcp: [rmcp]
tags: [clinical, epidemiology, biostatistics, survival-analysis, hematology, leukemia, lymphoma, oncology, genomics, python, r, biopython, scikit-survival, statistical-analysis]
```

#### 2.1.2 New Section: Cross-Skill Integration (After Line 511)

Insert new section after existing "Integration with Other Skills" section:

```markdown
## Cross-Skill Integration

### Task-to-Skill Mapping

| Clinical Task | Primary Skill | Supporting Skills | Tools Used |
|---------------|---------------|-------------------|------------|
| **Genomic biomarker analysis** | biopython | clinical-study-analysis | `Bio.Entrez`, `Bio.Blast` |
| **High-dimensional survival** | scikit-survival | statistical-analysis | `CoxnetSurvivalAnalysis` |
| **ML-based prognosis** | scikit-survival | clinical-study-analysis | `RandomSurvivalForest` |
| **Assumption validation** | statistical-analysis | clinical-study-analysis | `assumption_checks.py` |
| **Trial sample size** | statistical-analysis | clinical-study-analysis | Power analysis |
| **Competing risks (Python)** | scikit-survival | clinical-study-analysis | `cumulative_incidence_competing_risks` |
| **Sequence retrieval** | biopython | clinical-study-analysis | `Bio.Entrez.efetch` |

### Tool Availability Matrix

| Analysis Type | R (rmcp) | Python (scikit-survival) | Python (biopython) |
|---------------|----------|--------------------------|---------------------|
| Kaplan-Meier | ✓ `survival` | ✓ `sksurv.nonparametric` | - |
| Cox PH | ✓ `survival` | ✓ `CoxPHSurvivalAnalysis` | - |
| Penalized Cox | ✓ `glmnet` | ✓ `CoxnetSurvivalAnalysis` | - |
| Random Survival Forest | ✓ `randomForestSRC` | ✓ `RandomSurvivalForest` | - |
| Gradient Boosting | - | ✓ `GradientBoostingSurvivalAnalysis` | - |
| Competing Risks | ✓ `cmprsk` | ✓ `cumulative_incidence_competing_risks` | - |
| Sequence Retrieval | - | - | ✓ `Bio.Entrez` |
| BLAST | - | - | ✓ `Bio.Blast` |
| Multiple Alignment | - | - | ✓ `Bio.Align` |
| Assumption Checks | ✓ R scripts | ✓ `assumption_checks.py` | - |
| Power Analysis | ✓ `pwr` | ✓ `statsmodels.power` | - |

### When to Use Which Tool

#### Survival Analysis: R vs Python

| Criterion | Use R (rmcp) | Use Python (scikit-survival) |
|-----------|--------------|------------------------------|
| **Standard Cox model** | ✓ Well-established | ✓ Good |
| **High-dimensional data** | ✓ `glmnet` integration | ✓ `CoxnetSurvivalAnalysis` |
| **ML ensemble methods** | Limited | ✓ `RandomSurvivalForest`, `GradientBoosting` |
| **Large datasets** | Moderate | ✓ Better memory efficiency |
| **R ecosystem integration** | ✓ Native | Requires conversion |
| **Python ecosystem** | Requires conversion | ✓ Native |

#### Genomic Analysis: When to Use biopython

| Clinical Scenario | biopython Functions |
|-------------------|---------------------|
| Retrieve gene sequence (e.g., FLT3) | `Bio.Entrez.efetch` |
| Validate primer sequences | `Bio.Seq` operations |
| BLAST novel variants | `Bio.Blast.NCBIWWW.qblast` |
| Align tumor sequences | `Bio.Align.PairwiseAligner` |
| Calculate sequence stats | `Bio.SeqUtils` |
```

---

### 2.2 New Reference Documents

#### 2.2.1 `references/multi_skill_workflows.md`

**Purpose**: Document unified workflows combining multiple skills.

**Structure**:
```markdown
# Multi-Skill Workflows for Clinical Study Analysis

## Workflow 1: Genomic Survival Analysis

Combine biopython (sequence retrieval) with scikit-survival (survival modeling).

### Use Case
Analyze whether FLT3-ITD mutation burden affects survival in AML patients.

### Steps
1. Use biopython to retrieve FLT3 reference sequence
2. Use biopython to analyze mutation sequences
3. Combine with clinical data
4. Use scikit-survival to model survival by mutation burden

### Code Example
[Python script]

---

## Workflow 2: Validated Survival Analysis

Combine statistical-analysis (assumption checks) with scikit-survival (modeling).

### Use Case
Ensure survival model meets all assumptions before reporting.

### Steps
1. Use statistical-analysis to check proportional hazards
2. Use statistical-analysis to check censoring patterns
3. Use scikit-survival for primary model
4. Use statistical-analysis for APA reporting

### Code Example
[Python script]

---

## Workflow 3: Comprehensive Trial Analysis

Combine all three skills for complete clinical trial analysis.

### Steps
1. statistical-analysis: Power analysis for trial design
2. statistical-analysis: Assumption checks pre-analysis
3. clinical-study-analysis: Primary analysis via rmcp
4. scikit-survival: ML-based prognostic model
5. biopython: Genomic biomarker analysis (if applicable)
6. statistical-analysis: APA-style reporting

### Code Example
[Python/R script]
```

---

### 2.3 New Scripts

#### 2.3.1 `scripts/genomic_survival_analysis.py`

**Purpose**: Demonstrate biopython → scikit-survival integration.

**Key Functions**:
```python
# 1. Retrieve FLT3 sequence
def retrieve_flt3_sequence():
    """Retrieve FLT3 gene sequence from NCBI using biopython."""
    from Bio import Entrez, SeqIO
    Entrez.email = "your.email@example.com"
    
    handle = Entrez.efetch(
        db="nucleotide", 
        id="NM_004119.3",  # FLT3 reference
        rettype="fasta", 
        retmode="text"
    )
    record = SeqIO.read(handle, "fasta")
    handle.close()
    return record

# 2. Calculate sequence features
def calculate_mutation_features(wildtype, mutant):
    """Calculate sequence statistics for mutation analysis."""
    from Bio.SeqUtils import gc_fraction
    
    return {
        "gc_content_wt": gc_fraction(wildtype.seq),
        "gc_content_mut": gc_fraction(mutant.seq),
        "length_diff": len(mutant) - len(wildtype)
    }

# 3. Build survival model
def build_genomic_survival_model(X, y):
    """Build survival model with genomic features using scikit-survival."""
    from sksurv.ensemble import RandomSurvivalForest
    from sksurv.preprocessing import OneHotEncoder
    
    # Encode categorical variables
    X_encoded = OneHotEncoder().fit_transform(X)
    
    # Fit Random Survival Forest
    rsf = RandomSurvivalForest(
        n_estimators=100,
        min_samples_split=10,
        min_samples_leaf=5,
        random_state=42
    )
    rsf.fit(X_encoded, y)
    
    return rsf
```

#### 2.3.2 `scripts/statistical_validation.py`

**Purpose**: Demonstrate statistical-analysis → survival workflow.

**Key Functions**:
```python
# 1. Pre-model assumption checks
def check_survival_assumptions(df, time_col, event_col, group_col):
    """Check assumptions for survival analysis using statistical-analysis skill."""
    from scipy import stats
    import numpy as np
    
    results = {}
    
    # Check censoring balance
    censoring_rate = 1 - df[event_col].mean()
    results['censoring_rate'] = censoring_rate
    
    # Check sample size adequacy
    events_per_group = df.groupby(group_col)[event_col].sum()
    results['min_events'] = events_per_group.min()
    results['adequate_sample'] = results['min_events'] >= 10
    
    return results

# 2. Post-model validation
def validate_cox_model(model, X_test, y_test, y_train):
    """Validate Cox model using scikit-survival metrics."""
    from sksurv.metrics import concordance_index_ipcw, integrated_brier_score
    
    # Uno's C-index (recommended for high censoring)
    c_uno = concordance_index_ipcw(y_train, y_test, model.predict(X_test))
    
    return {
        "uno_c_index": c_uno[0],
        "interpretation": "Good" if c_uno[0] > 0.7 else "Moderate" if c_uno[0] > 0.6 else "Poor"
    }
```

#### 2.3.3 `scripts/r_python_integration.R`

**Purpose**: Demonstrate R + Python interoperability.

**Key Functions**:
```r
# Save R data for Python
save_for_python <- function(data, filename) {
  # Save as CSV for Python compatibility
  write.csv(data, filename, row.names = FALSE)
  
  # Also save metadata as JSON
  metadata <- list(
    nrow = nrow(data),
    ncol = ncol(data),
    columns = names(data),
    created = Sys.time()
  )
  jsonlite::write_json(metadata, paste0(filename, ".json"), auto_unbox = TRUE)
}

# Load Python results into R
load_python_results <- function(filename) {
  # Read CSV from Python
  results <- read.csv(filename)
  
  # Read metadata
  metadata <- jsonlite::read_json(paste0(filename, ".json"))
  
  attr(results, "python_metadata") <- metadata
  return(results)
}

# Example workflow
clinical_data <- data.frame(
  patient_id = 1:100,
  time = rexp(100, 0.1),
  event = rbinom(100, 1, 0.7),
  age = rnorm(100, 60, 10)
)

# Save for Python analysis
save_for_python(clinical_data, "clinical_data.csv")

# In Python (run separately):
# df = pd.read_csv("clinical_data.csv")
# model = RandomSurvivalForest().fit(X, y)
# predictions = model.predict(X_test)
# pd.DataFrame(predictions).to_csv("predictions.csv", index=False)

# Load back in R
# python_results <- load_python_results("predictions.csv")
```

---

## 3. Data Model / API

### 3.1 Cross-Skill Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DATA FLOW ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐                                                        │
│  │ Clinical     │                                                        │
│  │ Data         │                                                        │
│  │ (CSV/Excel)  │                                                        │
│  └──────┬───────┘                                                        │
│         │                                                                │
│         ▼                                                                │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐            │
│  │ statistical- │────▶│ scikit-      │────▶│  rmcp        │            │
│  │ analysis     │     │ survival     │     │  (R)         │            │
│  │ (Python)     │     │ (Python)     │     │              │            │
│  └──────────────┘     └──────────────┘     └──────────────┘            │
│         │                    │                    │                     │
│         ▼                    ▼                    ▼                     │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │              UNIFIED OUTPUT (JSON/Markdown)               │          │
│  │  • Model results                                          │          │
│  │  • Visualizations                                         │          │
│  │  • Statistical reports                                    │          │
│  └──────────────────────────────────────────────────────────┘          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Data Format Standards

| Data Type | Primary Format | Conversion Tools |
|-----------|----------------|------------------|
| **Clinical data** | CSV (universal) | `pandas.read_csv()`, `read.csv()` |
| **Metadata** | JSON | `jsonlite` (R), `json` (Python) |
| **Survival outcomes** | NumPy structured array | `sksurv.util.Surv` |
| **Genomic sequences** | FASTA | `Bio.SeqIO` |
| **Model results** | JSON | Custom serialization |

### 3.3 Skill Invocation API

#### From clinical-study-analysis to biopython

```python
# Example: Retrieve gene sequence
from Bio import Entrez, SeqIO

def fetch_clinical_gene(gene_name, email):
    """Fetch gene sequence for clinical analysis."""
    Entrez.email = email
    
    # Search for gene
    search_handle = Entrez.esearch(
        db="gene",
        term=f"{gene_name}[Gene] AND Homo sapiens[Organism]"
    )
    search_results = Entrez.read(search_handle)
    search_handle.close()
    
    # Fetch sequence
    gene_id = search_results["IdList"][0]
    fetch_handle = Entrez.efetch(db="gene", id=gene_id, rettype="fasta")
    sequence = SeqIO.read(fetch_handle, "fasta")
    fetch_handle.close()
    
    return sequence
```

#### From clinical-study-analysis to scikit-survival

```python
# Example: Build ML survival model
from sksurv.ensemble import RandomSurvivalForest
from sksurv.util import Surv

def build_clinical_prognostic_model(df, time_col, event_col, feature_cols):
    """Build prognostic model using scikit-survival."""
    
    # Prepare survival outcome
    y = Surv.from_arrays(
        event=df[event_col].astype(bool),
        time=df[time_col]
    )
    
    # Features
    X = df[feature_cols]
    
    # Fit model
    model = RandomSurvivalForest(
        n_estimators=200,
        min_samples_split=15,
        min_samples_leaf=10,
        max_features="sqrt",
        random_state=42
    )
    model.fit(X, y)
    
    return model
```

#### From clinical-study-analysis to statistical-analysis

```python
# Example: Validate analysis assumptions
def validate_clinical_analysis(df, outcome_col, group_col):
    """Validate assumptions using statistical-analysis skill patterns."""
    from scipy import stats
    import numpy as np
    
    results = {}
    
    # Normality check
    for group in df[group_col].unique():
        group_data = df[df[group_col] == group][outcome_col]
        stat, p = stats.shapiro(group_data)
        results[f"normality_{group}"] = {
            "statistic": stat,
            "p_value": p,
            "normal": p > 0.05
        }
    
    # Homogeneity of variance
    groups = [df[df[group_col] == g][outcome_col] for g in df[group_col].unique()]
    stat, p = stats.levene(*groups)
    results["homogeneity"] = {
        "statistic": stat,
        "p_value": p,
        "equal_variance": p > 0.05
    }
    
    return results
```

---

## 4. UI/UX Design (Agent Interaction)

### 4.1 Agent Decision Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      AGENT INTERACTION FLOW                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  User Request                                                            │
│       │                                                                  │
│       ▼                                                                  │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │                    ANALYZE REQUEST                            │      │
│  │  • Identify analysis type                                     │      │
│  │  • Check for genomic components                               │      │
│  │  • Check for survival analysis                                │      │
│  │  • Check for validation needs                                 │      │
│  └──────────────────────────────────────────────────────────────┘      │
│       │                                                                  │
│       ▼                                                                  │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │                    ROUTE TO SKILLS                            │      │
│  │                                                                │      │
│  │  Genomic? ──────────▶ biopython                              │      │
│  │  Survival? ─────────▶ scikit-survival OR rmcp                │      │
│  │  Validation? ───────▶ statistical-analysis                   │      │
│  │  Standard? ─────────▶ rmcp (R-based)                         │      │
│  └──────────────────────────────────────────────────────────────┘      │
│       │                                                                  │
│       ▼                                                                  │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │                    COORDINATE EXECUTION                       │      │
│  │  • Pass data between skills                                   │      │
│  │  • Aggregate results                                          │      │
│  │  • Generate unified output                                    │      │
│  └──────────────────────────────────────────────────────────────┘      │
│       │                                                                  │
│       ▼                                                                  │
│  User Response (Unified Report)                                         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Agent Prompting Patterns

#### Pattern 1: Genomic Survival Analysis

**User Request**: "Analyze FLT3 mutation impact on AML survival"

**Agent Response**:
```markdown
I'll analyze FLT3 mutation impact on survival by combining genomic and survival analysis:

**Step 1**: Retrieve FLT3 reference sequence using biopython
**Step 2**: Analyze mutation data from your clinical dataset
**Step 3**: Build survival model using scikit-survival
**Step 4**: Validate assumptions using statistical-analysis

Starting with Step 1...
```

#### Pattern 2: ML Prognostic Model

**User Request**: "Build a prognostic model for my transplant data"

**Agent Response**:
```markdown
I'll build an ML-based prognostic model for transplant outcomes:

**Recommendation**: Use scikit-survival's RandomSurvivalForest for:
- Handling non-linear relationships
- Automatic feature importance
- Robust to missing data

**Validation**: Will use statistical-analysis for assumption checks

Shall I proceed with this approach?
```

### 4.3 Error Handling

| Error Type | Skill | Recovery Action |
|------------|-------|-----------------|
| **NCBI rate limit** | biopython | Wait and retry, use API key |
| **Convergence failure** | scikit-survival | Simplify model, increase iterations |
| **Assumption violation** | statistical-analysis | Suggest alternative tests |
| **Data format mismatch** | All | Convert format, report error |

---

## 5. Security & Performance

### 5.1 Security Considerations

| Concern | Mitigation |
|---------|------------|
| **Patient data privacy** | Emphasize HIPAA compliance, de-identification |
| **NCBI API access** | Require email, recommend API key |
| **Data persistence** | Use temporary files, clean up after analysis |
| **External dependencies** | Document version requirements |

### 5.2 Performance Optimization

| Scenario | Optimization |
|----------|--------------|
| **Large datasets** | Use Python (better memory) over R |
| **High-dimensional genomics** | Use scikit-survival's penalized models |
| **BLAST searches** | Cache results, use local BLAST for batch |
| **Model comparison** | Parallel execution with joblib |

### 5.3 Resource Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **RAM** | 8 GB | 16+ GB |
| **Python** | 3.8+ | 3.11+ |
| **R** | 4.0+ | 4.3+ |
| **Storage** | 1 GB | 5+ GB |

---

## 6. Implementation Checklist

### Phase 1: SKILL.md Updates
- [ ] Update metadata (tags, description)
- [ ] Add Cross-Skill Integration section
- [ ] Add Task-to-Skill mapping table
- [ ] Add Tool Availability matrix
- [ ] Add "When to Use Which Tool" guide

### Phase 2: Reference Documents
- [ ] Create `references/multi_skill_workflows.md`
- [ ] Document Workflow 1: Genomic Survival
- [ ] Document Workflow 2: Validated Survival
- [ ] Document Workflow 3: Comprehensive Trial

### Phase 3: Scripts
- [ ] Create `scripts/genomic_survival_analysis.py`
- [ ] Create `scripts/statistical_validation.py`
- [ ] Create `scripts/r_python_integration.R`
- [ ] Add inline documentation

### Phase 4: Testing
- [ ] Test biopython integration
- [ ] Test scikit-survival integration
- [ ] Test statistical-analysis integration
- [ ] Test R ↔ Python data exchange
- [ ] Verify all imports work

---

## 7. Dependencies

### Python Packages

```txt
# requirements.txt additions
biopython>=1.85
scikit-survival>=0.22.0
scipy>=1.10.0
statsmodels>=0.14.0
pingouin>=0.5.0
pandas>=2.0.0
numpy>=1.24.0
joblib>=1.3.0
```

### R Packages

```r
# Existing (via rmcp)
# survival, survminer, cmprsk, mstate, glmnet

# For integration
install.packages(c("jsonlite", "reticulate"))
```
