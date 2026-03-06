# Design: csa-scientific-skills-integration

## Reference
- Plan: `docs/01-plan/features/csa-scientific-skills-integration.plan.md`
- HPW counterpart: `hematology-paper-writer/tools/skills/`

---

## 1. File Structure

```
scripts/crf_pipeline/
  skills/
    __init__.py                  # re-exports all public classes
    _base.py                     # CSASkillBase + CSASkillContext
    statistical_analyst.py       # Tier 1: pre-analysis method validation
    hypothesis_generator.py      # Tier 1: null/alternative hypothesis generation
    critical_thinker.py          # Tier 1: assumption checks pre-run
    scientific_writer.py         # Tier 1: Methods prose generation
    content_researcher.py        # Tier 1: guideline citation lookup
    r_output_interpreter.py      # Tier 2 (KEY): R CSVs → *_stats.json sidecars
    eln_guideline_mapper.py      # Tier 2: results → ELN/NIH category labels
    protocol_consistency.py      # Tier 2: outputs vs protocol endpoint validation
  skills_integration.py          # integrate_skills_pre/post_analysis() hooks

tests/
  test_skills_integration.py     # ≥ 40 tests
```

---

## 2. CSASkillContext

### 2.1 Dataclass Definition

```python
# scripts/crf_pipeline/skills/_base.py

@dataclass
class CSASkillContext:
    study_name: str
    disease: str                        # "aml" | "cml" | "mds" | "hct"

    # ── Pre-analysis ─────────────────────────────────────────────────────────
    hypotheses: list = field(default_factory=list)         # list[str]
    statistical_plan: dict = field(default_factory=dict)   # see §2.2
    assumption_warnings: list = field(default_factory=list)# list[str]

    # ── Post-analysis ────────────────────────────────────────────────────────
    # key_statistics MUST use StatValue-compatible shape (§3.1)
    # Written to data/*_stats.json; read by _write_hpw_manifest() automatically
    key_statistics: dict = field(default_factory=dict)

    interpretation_notes: list = field(default_factory=list)  # list[str]
    methods_prose: str = ""
    eln_annotations: dict = field(default_factory=dict)    # {stat_key: annotation}
    protocol_gaps: list = field(default_factory=list)      # list[str] — unmet endpoints

    # ── Tracking ─────────────────────────────────────────────────────────────
    scripts_run: list = field(default_factory=list)        # list[str] — script basenames
```

### 2.2 statistical_plan Schema

```python
{
    "study_type": str,               # "retrospective" | "rct" | "phase1" | "cohort"
    "primary_endpoint": str,
    "methods": list[str],            # e.g. ["Kaplan-Meier", "Cox PH regression"]
    "assumptions": list[str],
    "software": list[str],           # ["R (survival, cmprsk)"]
    "reporting_guideline": str,      # "STROBE" | "CONSORT 2010" | ...
    "disease_specific_methods": dict # {disease: [additional methods]}
}
```

### 2.3 Persistence

```python
# Stored at: {output_dir}/data/{study_name}.csa_skills_context.json
# Follows same fail-silent load/save pattern as HPW SkillContext

def save(self, output_dir: Path) -> None:
    path = Path(output_dir) / "data" / f"{self.study_name}.csa_skills_context.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(self), indent=2, default=str))

@classmethod
def load(cls, study_name: str, output_dir: Path) -> "CSASkillContext":
    path = Path(output_dir) / "data" / f"{study_name}.csa_skills_context.json"
    if not path.exists():
        return cls(study_name=study_name, disease="unknown")
    try:
        data = json.loads(path.read_text())
        known_keys = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known_keys})
    except Exception:
        return cls(study_name=study_name, disease="unknown")
```

---

## 3. key_statistics Schema (HPW-compatible)

### 3.1 StatValue-compatible Dict Shape

Each entry must be parseable by `StatisticalBridge.get_stat()`:

```python
# Scalar (plain numeric) — acceptable for counts
{"n_total": {"value": 120}}

# Rate (no p_value) — response rates, GVHD rates
{"orr": {"value": 0.68, "unit": "percent", "ci_lower": 0.58, "ci_upper": 0.77}}

# Time-to-event (with p_value)
{"os_median_months": {"value": 18.4, "unit": "months",
                       "ci_lower": 14.2, "ci_upper": 22.1, "p_value": 0.003}}

# Hazard ratio
{"os_hr": {"value": 0.62, "ci_lower": 0.44, "ci_upper": 0.87, "p_value": 0.006}}
```

### 3.2 Required Keys per Disease (_REQUIRED_STATS)

| Disease | Required Keys (must be non-None) |
|---------|----------------------------------|
| AML | `n_total`, `orr`, `os_median_months`, `ae_grade3plus_rate` |
| CML | `n_total`, `mmr_12mo`, `os_median_months`, `ae_grade3plus_rate` |
| MDS | `n_total`, `orr`, `os_median_months`, `ae_grade3plus_rate` |
| HCT | `n_total`, `agvhd_grade2_4_rate`, `os_median_months`, `ae_grade3plus_rate` |

### 3.3 Full Target Key Set (_ENRICHMENT_QUERIES)

Skills should populate as many of these 20 keys as the R outputs support:

| Disease | Key | R Source |
|---------|-----|----------|
| AML | `eln_favorable_pct` | `20_aml_eln_risk.R` → docx |
| AML | `eln_intermediate_pct` | `20_aml_eln_risk.R` → docx |
| AML | `eln_adverse_pct` | `20_aml_eln_risk.R` → docx |
| AML | `ccr_rate` | `21_aml_composite_response.R` → docx |
| AML | `cr_rate` | `21_aml_composite_response.R` → docx |
| AML | `cri_rate` | `21_aml_composite_response.R` → docx |
| AML | `target_dlt_rate` | `25_aml_phase1_boin.R` → docx |
| AML | `orr` | `03_efficacy.R` → docx |
| CML | `mmr_12mo` | `22_cml_tfr_analysis.R` → docx |
| CML | `tfr_12mo` | `22_cml_tfr_analysis.R` → docx |
| CML | `tfr_24mo` | `22_cml_tfr_analysis.R` → docx |
| CML | `sokal_high_pct` | `23_cml_scores.R` → docx |
| HCT | `agvhd_grade2_4_rate` | `24_hct_gvhd_analysis.R` → docx |
| HCT | `agvhd_grade3_4_rate` | `24_hct_gvhd_analysis.R` → docx |
| HCT | `cgvhd_moderate_severe_rate` | `24_hct_gvhd_analysis.R` → docx |
| HCT | `grfs_12mo` | `24_hct_gvhd_analysis.R` → docx |
| All | `ae_grade3plus_rate` | `05_safety.R` → docx |
| All | `os_median_months` | `04_survival.R` → `Cox_*_Analysis.csv` |
| All | `os_hr` | `04_survival.R` → `Cox_*_Analysis.csv` |
| All | `n_total` | `02_table1.R` → docx OR `10_sample_size.R` → csv |

---

## 4. ROutputInterpreter (Tier 2 — KEY Skill)

### 4.1 Purpose

Reads R-generated CSV outputs post-run, extracts `StatValue`-shaped dicts,
writes `data/{script_basename}_stats.json`. Existing `_write_hpw_manifest()`
reads these automatically — zero orchestrator modification.

### 4.2 CSV Column Mapping

#### `Cox_*_Analysis.csv` (from `04_survival.R`)
```
Expected columns: variable, hr, hr_lower, hr_upper, p_value, n_events
Extraction logic:
  - Find row where variable matches "OS" or "PFS"
  - os_hr: {"value": hr, "ci_lower": hr_lower, "ci_upper": hr_upper, "p_value": p_value}
  - os_median_months: read from separate "median_survival" table if present
```

#### `FineGray_*.csv` (from `04_survival.R`)
```
Expected columns: cause, shr, shr_lower, shr_upper, p_value
Extraction:
  - grfs_event_rate from GRFS row: {"value": shr, ci_lower, ci_upper, p_value}
```

#### `SampleSize_*.csv` (from `10_sample_size.R`)
```
Expected columns: parameter, value
Extraction:
  - n_total: row where parameter == "n_per_arm" or "n_total" → {"value": int(value)}
```

#### Docx extraction (fallback, regex-based)
```
Pattern: "(\d+\.?\d*)\s*(months?|%|patients?)"
Used for: scripts that produce only .docx (20, 21, 22, 23, 24, 25)
Targets per script:
  - 20_aml_eln_risk: match "Favorable: XX.X%", "Adverse: XX.X%"
  - 21_aml_composite_response: match "CR: XX.X%", "CRi: XX.X%", "cCR: XX.X%"
  - 22_cml_tfr_analysis: match "MMR at 12 months: XX.X%", "TFR: XX.X%"
  - 23_cml_scores: match "Sokal high: XX.X%"
  - 24_hct_gvhd_analysis: match "aGVHD grade 2-4: XX.X%", "GRFS: XX.X%"
```

### 4.3 Output File Format

```python
# data/04_survival_stats.json
{
    "key_statistics": {
        "os_median_months": {"value": 18.4, "unit": "months",
                             "ci_lower": 14.2, "ci_upper": 22.1},
        "os_hr": {"value": 0.62, "unit": None,
                  "ci_lower": 0.44, "ci_upper": 0.87, "p_value": 0.006}
    },
    "disease_specific": {},
    "analysis_notes": {"source": "04_survival.R", "extracted_at": "2026-03-05T..."}
}
```

---

## 5. Pre-Analysis Skills

### 5.1 StatisticalAnalyst

Maps to `statistical-analysis` OpenCode skill.

```python
class StatisticalAnalyst(CSASkillBase):

    # Disease-specific R method catalog
    _DISEASE_METHODS = {
        "aml": {
            "primary": ["Kaplan-Meier (OS, EFS)", "Fine-Gray competing risks (CIR)"],
            "response": ["Wilson score 95% CI for binary response rates (CR, CRi, cCR)"],
            "risk_strat": ["ELN 2022 risk stratification (cytogenetic/molecular)"],
            "phase1": ["BOIN design (Liu & Yuan 2015)", "3+3 escalation"],
            "reporting": "CONSORT 2010 / STROBE"
        },
        "cml": {
            "primary": ["Kaplan-Meier (OS, TFR)", "Cox PH regression"],
            "response": ["ELN 2020 milestone assessment (3/6/12/18 mo)"],
            "scores": ["Sokal, Hasford, ELTS score calculation"],
            "reporting": "STROBE"
        },
        "mds": {
            "primary": ["Kaplan-Meier (OS, transfusion-free survival)"],
            "response": ["IWG 2006 response criteria (HI, CR, PR)"],
            "reporting": "STROBE"
        },
        "hct": {
            "primary": ["Fine-Gray competing risks (aGVHD, cGVHD, relapse)"],
            "gvhd": ["NIH 2014 aGVHD grading", "NIH 2014 cGVHD severity"],
            "survival": ["GRFS = GVHD-free relapse-free survival"],
            "reporting": "STROBE"
        }
    }

    def analyze(self, disease: str, primary_endpoint: str, study_type: str) -> dict:
        """Generate statistical_plan. Writes to self.context.statistical_plan."""
```

### 5.2 HypothesisGenerator

Maps to `hypothesis-generation` OpenCode skill.

```python
class HypothesisGenerator(CSASkillBase):

    _DISEASE_ENDPOINTS = {
        "aml": ["OS", "EFS", "CR rate", "cCR rate", "ELN risk distribution"],
        "cml": ["MMR at 12 mo", "TFR at 12/24 mo", "ELN milestone achievement"],
        "mds": ["OS", "HI rate", "transfusion independence"],
        "hct": ["OS", "GRFS", "aGVHD grade 2-4 CI", "cGVHD moderate-severe CI"]
    }

    def generate(self, disease: str, treatment: str, endpoint: str) -> list[str]:
        """
        Returns list of 3 hypotheses: null + alternative + exploratory.
        Writes to self.context.hypotheses.
        """
```

### 5.3 CriticalThinker

Maps to `scientific-critical-thinking` OpenCode skill.

```python
class CriticalThinker(CSASkillBase):

    def check_assumptions(self, disease: str, study_type: str, n: int) -> list[str]:
        """
        Returns list of assumption warning strings.
        Common checks:
          - n < 30: "Small sample — exact tests preferred over asymptotic"
          - HCT + competing risks: "Verify Fine-Gray vs cause-specific Cox"
          - Phase1: "Verify monotone dose-toxicity assumption before BOIN"
          - Survival: "cox.zph() PH test recommended — will be run in 04_survival.R"
        Writes to self.context.assumption_warnings.
        """
```

---

## 6. Post-Analysis Skills

### 6.1 ScientificWriter

Maps to `scientific-writing` OpenCode skill.

```python
class ScientificWriter(CSASkillBase):

    _METHODS_TEMPLATES = {
        "aml": (
            "All statistical analyses were performed using R (version ≥4.3). "
            "Overall survival was estimated using the Kaplan-Meier method and compared "
            "using the log-rank test. Cox proportional hazards regression was used for "
            "multivariable analysis. Response rates were reported with 95% Wilson score "
            "confidence intervals. ELN 2022 risk stratification criteria were applied. "
            "Adverse events were graded per CTCAE v5.0. "
            "All tests were two-sided at α=0.05."
        ),
        "cml": ...,
        "mds": ...,
        "hct": (
            "Cumulative incidences of aGVHD, cGVHD, and relapse were estimated using "
            "Fine-Gray subdistribution hazard models with death as a competing risk. "
            "GVHD grading followed NIH 2014 consensus criteria. GRFS was defined as "
            "freedom from grade 3-4 aGVHD, moderate-severe cGVHD, relapse, or death."
        ),
    }

    def draft_methods(self) -> str:
        """
        Returns Methods section prose string.
        Incorporates context.statistical_plan into template.
        Writes to self.context.methods_prose.
        """
```

### 6.2 ELNGuidelineMapper

CSA-specific skill (maps to `clinical-decision-support`).

```python
class ELNGuidelineMapper(CSASkillBase):

    _ELN_ANNOTATIONS = {
        "eln_favorable_pct":       "ELN 2022: Favorable risk (expected CR >90%, OS >12mo)",
        "eln_adverse_pct":         "ELN 2022: Adverse risk (expected OS <12mo)",
        "mmr_12mo":                "ELN 2020: MMR milestone at 12 months",
        "tfr_12mo":                "ELN 2020: TFR at 12 months (deep MR required ≥2yr)",
        "agvhd_grade2_4_rate":     "NIH 2014: Grade 2-4 aGVHD cumulative incidence",
        "cgvhd_moderate_severe_rate": "NIH 2014: Moderate-severe cGVHD",
        "grfs_12mo":               "GRFS = GVHD-free relapse-free survival at 12 months",
    }

    def map(self, output_dir: Path) -> "CSASkillContext":
        """
        For each key in context.key_statistics that has an ELN annotation,
        writes annotation to context.eln_annotations[key].
        Also writes to data/{disease}_eln_annotations.json for hpw_manifest enrichment.
        """
```

### 6.3 ProtocolConsistencyChecker

CSA-specific skill (maps to `scientific-critical-thinking`).

```python
class ProtocolConsistencyChecker(CSASkillBase):

    def check(self, protocol_spec: dict) -> list[str]:
        """
        Compares protocol_spec["primary_endpoints"] against context.key_statistics keys.
        Returns list of gaps: endpoints defined in protocol but absent from key_statistics.
        Writes to context.protocol_gaps.

        protocol_spec loaded from: {output_dir}/data/protocol_spec.json
        (written by parsers/protocol_parser.py)
        """
```

---

## 7. Integration Hooks (skills_integration.py)

```python
# scripts/crf_pipeline/skills_integration.py

def integrate_skills_pre_analysis(
    study_name: str,
    disease: str,
    output_dir: Path,
    study_type: str = "retrospective",
    primary_endpoint: str = "",
    n_estimated: int = 0,
) -> CSASkillContext:
    """
    Runs before R scripts. Returns populated CSASkillContext.
    Calls: HypothesisGenerator → StatisticalAnalyst → CriticalThinker.
    Never raises — returns empty context on any failure.
    """

def integrate_skills_post_analysis(
    result: "AnalysisResult",
    output_dir: Path,
    study_name: str,
) -> None:
    """
    Runs after R scripts. Writes *_stats.json sidecars consumed by _write_hpw_manifest().
    Calls: ROutputInterpreter → ELNGuidelineMapper → ScientificWriter
           → ProtocolConsistencyChecker → ContentResearcher.
    Never raises — fail-silent throughout.
    """
```

### 7.1 Orchestrator Hook Point

Appended to end of `AnalysisOrchestrator.run()` (additive, never modifies):

```python
# In orchestrator.py — after line 666 (self._write_hpw_manifest(result))
# Added as: try/except block, fail-silent

try:
    from .skills_integration import integrate_skills_post_analysis
    integrate_skills_post_analysis(result, self.output_dir, self.study_args.get("study_name", self.disease))
except Exception as _skills_exc:
    logger.debug("Skills integration skipped: %s", _skills_exc)
```

---

## 8. CLI Additions (cli.py)

Five new subcommands added to the argparse CLI:

```python
# python -m scripts.crf_pipeline <subcommand>

hypothesis        # HypothesisGenerator.generate()
  --disease       aml|cml|mds|hct (required)
  --treatment     str
  --endpoint      str

analyze-plan      # StatisticalAnalyst.analyze() + CriticalThinker.check_assumptions()
  --data          path to CSV/SPSS (required)
  --disease       aml|cml|mds|hct (required)
  --study-type    retrospective|rct|phase1|cohort

interpret-results # ROutputInterpreter.interpret() + ELNGuidelineMapper.map()
  --output-dir    path (required, reads CSVs from there)
  --disease       aml|cml|mds|hct (required)
  --study-name    str

draft-methods     # ScientificWriter.draft_methods()
  --output-dir    path (required, loads CSASkillContext)
  --study-name    str (required)

review-assumptions # CriticalThinker.check_assumptions()
  --data          path
  --disease       aml|cml|mds|hct (required)
  --n             int (sample size)
```

---

## 9. Test Plan (test_skills_integration.py)

### 9.1 _base.py tests (10)
- CSASkillContext: save/load roundtrip
- CSASkillContext.load: non-existent path → empty context (no raise)
- CSASkillContext.load: corrupt JSON → empty context (no raise)
- CSASkillContext.load: unknown keys silently dropped
- CSASkillContext: all field defaults non-None

### 9.2 ROutputInterpreter tests (12)
- Cox CSV with OS row → `os_hr` + `os_hr` StatValue
- Cox CSV with p_value → `p_value` included
- FineGray CSV → `grfs_event_rate` extracted
- SampleSize CSV → `n_total` extracted
- Docx regex fallback: AML ELN string → `eln_favorable_pct`
- Docx regex fallback: CML MMR string → `mmr_12mo`
- Missing CSV → empty key_statistics (no raise)
- Stats JSON sidecar written to `data/` dir
- Sidecar format: valid StatValue shape
- `disease_specific` empty dict (not None)
- Multiple CSVs merged correctly
- Existing sidecar updated not duplicated

### 9.3 Pre-analysis skills tests (8)
- StatisticalAnalyst: AML → includes Fine-Gray
- StatisticalAnalyst: HCT → includes NIH 2014
- StatisticalAnalyst: unknown disease → returns non-empty plan
- HypothesisGenerator: AML → 3 hypotheses
- HypothesisGenerator: CML → includes MMR endpoint
- CriticalThinker: n<30 → warning generated
- CriticalThinker: HCT → competing risks warning
- CriticalThinker: no warnings → empty list (no raise)

### 9.4 Post-analysis skills tests (8)
- ScientificWriter: AML → methods_prose contains "Kaplan-Meier"
- ScientificWriter: HCT → methods_prose contains "Fine-Gray"
- ELNGuidelineMapper: eln_favorable_pct in key_statistics → annotation added
- ELNGuidelineMapper: no matching keys → eln_annotations empty (no raise)
- ProtocolConsistencyChecker: missing endpoint → in protocol_gaps
- ProtocolConsistencyChecker: all present → empty protocol_gaps
- ContentResearcher: returns non-empty list (no raise)
- All post-analysis skills: context persisted after call

### 9.5 Integration hook tests (6)
- integrate_skills_post_analysis: sidecar written with required keys
- integrate_skills_post_analysis: corrupt output_dir → no exception raised
- integrate_skills_post_analysis: CSASkillContext saved
- integrate_skills_pre_analysis: returns CSASkillContext (not None)
- Orchestrator: existing tests still pass (no regression)
- hpw_manifest key_statistics: non-empty after interpret-results run

---

## 10. Success Criteria

| Criterion | Verification |
|-----------|-------------|
| `StatisticalBridge.validate_stats_completeness()` returns `[]` for AML run | `test_skills_integration.py::test_hpw_manifest_required_keys` |
| `key_statistics["os_median_months"]` is `StatValue` (not None) | Same test |
| `methods_prose` contains disease-appropriate R method names | `test_scientific_writer_*` |
| All 40+ tests pass | `pytest tests/test_skills_integration.py` |
| Existing 74+ CSA tests pass (no regression) | `pytest tests/` |
| 5 CLI subcommands exit 0 with `--help` | Manual smoke test |

---

## 11. Implementation Order

1. `skills/_base.py` — CSASkillBase + CSASkillContext (all other classes depend on this)
2. `skills/r_output_interpreter.py` — highest priority; fixes key_statistics gap
3. `skills/statistical_analyst.py` + `hypothesis_generator.py` + `critical_thinker.py`
4. `skills/scientific_writer.py` + `content_researcher.py`
5. `skills/eln_guideline_mapper.py` + `protocol_consistency.py`
6. `skills/__init__.py`
7. `skills_integration.py`
8. `cli.py` additions (5 subcommands)
9. `orchestrator.py` hook (3-line try/except appended)
10. `tests/test_skills_integration.py`
