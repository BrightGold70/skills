# CSA × HPW Statistical Bridge Design Document

> **Summary**: Defines the `hpw_manifest.json` contract, `StatisticalBridge` Python class API, PhaseManager extensions, and CLI changes enabling end-to-end flow from CSA statistical outputs to HPW manuscript generation.
>
> **Project**: hematology-paper-writer
> **Version**: v2.0.0
> **Author**: kimhawk
> **Date**: 2026-03-05
> **Status**: Draft
> **Planning Doc**: [csa-hpw-bridge.plan.md](../01-plan/features/csa-hpw-bridge.plan.md)

---

## 1. Overview

### 1.1 Design Goals

1. Define a stable, versioned JSON contract (`hpw_manifest.json`) that CSA produces and HPW consumes
2. Provide a clean `StatisticalBridge` Python class that encapsulates all manifest access and prose generation
3. Keep HPW stateless with respect to R — all computation stays in CSA; HPW only reads outputs
4. Degrade gracefully: HPW functions identically today when no manifest is present

### 1.2 Design Principles

- **Separation of concerns**: CSA owns statistics; HPW owns writing. The manifest is the only interface.
- **Template-driven, not LLM-driven**: Methods paragraph and Results prose are generated from deterministic templates filled with manifest data — no hallucination risk.
- **Additive only**: All changes to existing HPW classes are backward-compatible (optional fields, optional arguments).
- **Single source of truth**: `hpw_manifest.json` schema version is explicit; future schema changes are versioned.

---

## 2. Architecture

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│  clinical-statistics-analyzer                                   │
│                                                                 │
│  scripts/crf_pipeline/orchestrator.py                          │
│    run-analysis → [ENHANCED] → writes hpw_manifest.json        │
└──────────────────────────┬──────────────────────────────────────┘
                           │  hpw_manifest.json (file-based contract)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  hematology-paper-writer                                        │
│                                                                 │
│  tools/statistical_bridge.py          [NEW]                    │
│    StatisticalBridge                                            │
│      ├── generate_methods_paragraph()                           │
│      ├── generate_results_prose()                               │
│      ├── get_abstract_statistics()                              │
│      ├── get_table_references()                                 │
│      ├── get_figure_references()                                │
│      └── verify_manuscript_statistics()                         │
│                     │                                           │
│          ┌──────────┼──────────┐                               │
│          ▼          ▼          ▼                               │
│  ManuscriptDrafter  ProseVerifier  cli.py create-draft         │
│  [ENHANCED]         [ENHANCED]     [ENHANCED]                  │
│                                                                 │
│  phases/phase_manager.py                                        │
│    ManuscriptMetadata [ENHANCED: +3 fields]                    │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow

```
User runs: hpw create-draft "AML topic" --disease aml --data-file data.csv
    │
    ▼
cli.py: check PhaseManager for csa_output_dir
    │
    ├─ manifest present? ──YES──▶ StatisticalBridge.load(manifest_path)
    │                                    │
    └─ manifest absent? ──▶ prompt       ▼
         │                     generate_methods_paragraph()
         ├─ yes: subprocess    generate_results_prose()
         │   run-analysis      get_abstract_statistics()
         │   → manifest        get_table_references()
         │                     get_figure_references()
         └─ no: proceed             │
              without CSA           ▼
                              ManuscriptDrafter.create_draft(
                                topic, articles, bridge=bridge
                              )
                                    │
                                    ▼
                              inject at placeholders in section_templates.py
                                    │
                                    ▼
                              YYYYMMDD_HHMMSS_draft.docx
```

### 2.3 Dependencies

| Component | Depends On | Purpose |
|-----------|-----------|---------|
| `StatisticalBridge` | `hpw_manifest.json`, `json`, `pathlib`, `re`, `dataclasses` | Manifest access + prose generation |
| `ManuscriptDrafter` (enhanced) | `StatisticalBridge` (optional) | Inject bridge outputs into templates |
| `ProseVerifier` (enhanced) | `StatisticalBridge` (optional) | Numeric cross-reference |
| `cli.py create-draft` (enhanced) | `PhaseManager`, `StatisticalBridge`, `subprocess` | Auto-trigger + orchestration |
| CSA `orchestrator.py` (enhanced) | existing pipeline | Emit `hpw_manifest.json` |

---

## 3. Data Model

### 3.1 `hpw_manifest.json` Schema (v1.0)

This is the file-based contract. CSA writes it; HPW reads it. Path: `{CSA_OUTPUT_DIR}/hpw_manifest.json`.

```json
{
  "schema_version": "1.0",
  "generated_at": "2026-03-05T10:00:00Z",
  "disease": "aml",
  "csa_skill_version": "3.0.0",
  "r_version": "4.3.1",
  "scripts_run": ["02_table1.R", "03_efficacy.R", "04_survival.R", "20_aml_eln_risk.R"],
  "r_packages": ["survival", "survminer", "cmprsk", "table1", "flextable", "officer"],

  "tables": [
    {
      "id": "table1",
      "label": "Table 1. Baseline characteristics",
      "path": "Tables/Table1.docx",
      "type": "table1",
      "source_script": "02_table1.R"
    },
    {
      "id": "table_efficacy",
      "label": "Table 2. Efficacy outcomes",
      "path": "Tables/Efficacy.docx",
      "type": "efficacy",
      "source_script": "03_efficacy.R"
    }
  ],

  "figures": [
    {
      "id": "fig_os_km",
      "label": "Figure 1. Overall survival",
      "path": "Figures/OS_KM.eps",
      "type": "km_os",
      "source_script": "04_survival.R"
    },
    {
      "id": "fig_forest",
      "label": "Figure 2. Subgroup analysis",
      "path": "Figures/Subgroup_Forest.eps",
      "type": "forest_plot",
      "source_script": "14_forest_plot.R"
    }
  ],

  "key_statistics": {
    "n_total":                  {"value": 89,   "unit": "patients"},
    "follow_up_median_months":  {"value": 18.3, "ci_lower": 14.1, "ci_upper": 22.5},
    "orr":                      {"value": 67.3, "unit": "percent", "ci_lower": 54.1, "ci_upper": 78.7, "n_events": 60, "p_value": 0.001},
    "cr_rate":                  {"value": 42.7, "unit": "percent", "ci_lower": 31.9, "ci_upper": 54.1},
    "os_median_months":         {"value": 24.5, "ci_lower": 18.2, "ci_upper": 31.0},
    "os_hr":                    {"value": 0.62, "ci_lower": 0.41, "ci_upper": 0.94, "p_value": 0.024, "reference": "control arm"},
    "pfs_median_months":        {"value": 14.2, "ci_lower": 10.8, "ci_upper": 17.6},
    "ae_grade3plus_rate":       {"value": 78.4, "unit": "percent"},
    "discontinuation_rate":     {"value": 12.4, "unit": "percent"}
  },

  "disease_specific": {
    "eln_risk_favorable":  34,
    "eln_risk_intermediate": 28,
    "eln_risk_adverse":    27,
    "cCR_rate":    {"value": 55.1, "ci_lower": 43.7, "ci_upper": 66.1},
    "mrd_negative_rate": {"value": 38.2, "ci_lower": 27.8, "ci_upper": 49.5}
  },

  "analysis_notes": {
    "survival_model": "Cox proportional hazards; PH assumption verified via cox.zph()",
    "competing_risks": "Fine-Gray subdistribution hazard model",
    "multiple_testing": "No adjustment; exploratory subgroup analysis"
  }
}
```

#### Schema Rules

| Field | Required | Type | Notes |
|-------|----------|------|-------|
| `schema_version` | Yes | string | Semver; HPW checks major version |
| `disease` | Yes | string | `"aml"` \| `"cml"` \| `"mds"` \| `"hct"` |
| `scripts_run` | Yes | string[] | Determines which prose templates apply |
| `tables` | Yes | object[] | May be empty `[]` if no table scripts ran |
| `figures` | Yes | object[] | May be empty `[]` |
| `key_statistics` | Yes | object | Mandatory keys: `n_total`; others depend on disease |
| `disease_specific` | No | object | Disease-specific stats; structure varies by disease |
| `analysis_notes` | No | object | Free-form; used in Methods paragraph |

#### Mandatory `key_statistics` Keys by Disease

| Key | AML | CML | MDS | HCT |
|-----|:---:|:---:|:---:|:---:|
| `n_total` | ✓ | ✓ | ✓ | ✓ |
| `orr` | ✓ | — | ✓ | — |
| `os_median_months` | ✓ | ✓ | ✓ | ✓ |
| `os_hr` | ✓ | ✓ | ✓ | ✓ |
| `ae_grade3plus_rate` | ✓ | ✓ | ✓ | ✓ |
| `mmr_rate` | — | ✓ | — | — |
| `ccyr_rate` | — | ✓ | — | — |
| `hi_rate` | — | — | ✓ | — |
| `engraftment_days_median` | — | — | — | ✓ |
| `agvhd_grade2plus_rate` | — | — | — | ✓ |

### 3.2 Python Dataclasses (HPW side)

```python
# tools/statistical_bridge.py

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

@dataclass
class TableRef:
    id: str
    label: str            # "Table 1. Baseline characteristics"
    path: Path            # absolute path to .docx
    type: str             # "table1" | "efficacy" | "safety"
    source_script: str

@dataclass
class FigureRef:
    id: str
    label: str            # "Figure 1. Overall survival"
    path: Path            # absolute path to .eps
    type: str             # "km_os" | "km_pfs" | "forest_plot" | "swimmer" | "waterfall"
    source_script: str

@dataclass
class StatValue:
    value: float | int
    unit: Optional[str] = None          # "percent" | "patients" | "months" | None
    ci_lower: Optional[float] = None
    ci_upper: Optional[float] = None
    p_value: Optional[float] = None
    n_events: Optional[int] = None
    reference: Optional[str] = None

@dataclass
class VerificationIssue:
    text_fragment: str        # the sentence containing the suspect number
    found_value: str          # numeric string found in text
    stat_key: Optional[str]   # matching key in key_statistics, or None
    expected_value: Optional[str]  # what key_statistics says
    severity: str             # "warning" | "error"
    message: str
```

### 3.3 `ManuscriptMetadata` Extension (PhaseManager)

Three new optional fields added to `phases/phase_manager.py`:

```python
@dataclass
class ManuscriptMetadata:
    # ... existing fields unchanged ...

    # NEW — CSA integration (all optional for backward compatibility)
    csa_output_dir: Optional[Path] = None    # path to CSA_OUTPUT_DIR for this project
    csa_data_file: Optional[Path] = None     # raw data file used for CSA run
    disease: Optional[str] = None            # "aml" | "cml" | "mds" | "hct"
```

Serialization: JSON-serialized alongside existing metadata in `PhaseManager`'s project state JSON.

---

## 4. API Specification

### 4.1 `StatisticalBridge` — Full Public Interface

```python
class StatisticalBridge:
    """
    Reads hpw_manifest.json produced by CSA orchestrator.
    Provides typed access to statistical outputs and template-driven prose generation.
    All methods are pure (no file writes, no subprocess calls).
    """

    def __init__(self, manifest_path: Path) -> None:
        """Load and validate manifest. Raises ManifestError on schema mismatch."""

    @classmethod
    def from_project(cls, phase_manager: "PhaseManager") -> Optional["StatisticalBridge"]:
        """
        Convenience constructor from PhaseManager.
        Returns None if csa_output_dir not set or hpw_manifest.json not found.
        """

    @classmethod
    def from_env(cls) -> Optional["StatisticalBridge"]:
        """
        Load from $CSA_OUTPUT_DIR/hpw_manifest.json.
        Returns None if env var not set or file not found.
        """

    # ── Properties ──────────────────────────────────────────────

    @property
    def is_available(self) -> bool:
        """True if manifest loaded successfully."""

    @property
    def disease(self) -> str:
        """Disease code: 'aml' | 'cml' | 'mds' | 'hct'"""

    @property
    def schema_version(self) -> str: ...

    @property
    def scripts_run(self) -> List[str]: ...

    # ── Prose Generation ─────────────────────────────────────────

    def generate_methods_paragraph(self) -> str:
        """
        Returns publication-ready 'Statistical Analysis' paragraph for Methods section.
        Template-driven from scripts_run, r_packages, r_version, analysis_notes.

        Example output:
        'Statistical analyses were performed using R version 4.3.1
         (R Foundation for Statistical Computing). Survival outcomes
         were estimated using the Kaplan-Meier method, and differences
         between groups were assessed using the log-rank test. Multivariable
         analyses were performed using Cox proportional hazards regression;
         the proportional hazards assumption was verified using Schoenfeld
         residuals (cox.zph). Cumulative incidences in the presence of
         competing risks were estimated using the Fine-Gray subdistribution
         hazard model. All tests were two-sided; p < 0.05 was considered
         statistically significant.'
        """

    def generate_results_prose(self) -> Dict[str, str]:
        """
        Returns prose dict keyed by section.
        Only sections with available scripts_run data are populated.

        Keys: 'baseline' | 'efficacy' | 'survival' | 'safety'

        Example ('efficacy'):
        'The overall response rate (ORR) was 67.3% (95% CI 54.1–78.7%;
         p = 0.001; n = 60/89). The complete response (CR) rate was 42.7%
         (95% CI 31.9–54.1%) (Table 2).'
        """

    def get_abstract_statistics(self) -> Dict[str, Any]:
        """
        Returns the 3–5 highest-priority stats for Abstract injection.
        Priority: n_total, primary endpoint (orr/mmr/hi), os_median, os_hr, ae_grade3plus.

        Returns dict of StatValue objects keyed by stat name.
        """

    # ── Reference Access ─────────────────────────────────────────

    def get_table_references(self) -> List[TableRef]:
        """All tables in order, with absolute paths resolved from manifest dir."""

    def get_figure_references(self) -> List[FigureRef]:
        """All figures in order, with absolute paths resolved from manifest dir."""

    def get_stat(self, key: str) -> Optional[StatValue]:
        """Get a specific statistic by key_statistics key. Returns None if absent."""

    # ── Verification ─────────────────────────────────────────────

    def verify_manuscript_statistics(
        self,
        text: str,
        strictness: str = "warn",       # "off" | "warn" | "strict"
        scope: Optional[List[str]] = None,  # section names to check; None = all
    ) -> List[VerificationIssue]:
        """
        Regex-extracts all percentages, decimals, and integers from text.
        Cross-references against key_statistics values (±0.1 tolerance for rounding).
        Returns list of VerificationIssues; empty list if all verified or strictness='off'.
        """

    # ── Formatting Helpers ───────────────────────────────────────

    def format_stat(self, key: str, fmt: str = "standard") -> str:
        """
        Format a stat as a string ready for manuscript insertion.
        fmt='standard': '67.3% (95% CI 54.1–78.7%; p = 0.001)'
        fmt='short':    '67.3% (54.1–78.7%)'
        fmt='hr':       'HR 0.62 (95% CI 0.41–0.94; p = 0.024)'
        """
```

### 4.2 CSA `orchestrator.py` — Enhancement Spec

**File**: `../clinical-statistics-analyzer/scripts/crf_pipeline/orchestrator.py`

**Change**: After existing `summary.json` write, add `_write_hpw_manifest()`:

```python
def _write_hpw_manifest(
    self,
    output_dir: Path,
    disease: str,
    scripts_run: List[str],
    r_packages: List[str],
    r_version: str,
    tables: List[dict],
    figures: List[dict],
    key_statistics: dict,
    disease_specific: dict,
    analysis_notes: dict,
) -> None:
    """Write hpw_manifest.json to output_dir root."""
```

**Key extraction logic** (per script output):
- `02_table1.R` → scan `Tables/` for `Table1*.docx` → `tables[type=table1]`
- `03_efficacy.R` → scan `Tables/` for `Efficacy*.docx` + `data/efficacy_stats.json` → `key_statistics[orr, cr_rate]`
- `04_survival.R` → scan `Figures/` for `*KM*.eps` + `data/survival_stats.json` → `key_statistics[os_median_months, os_hr, pfs_median_months]`
- `05_safety.R` → scan `Tables/` for `Safety*.docx` + `data/safety_stats.json` → `key_statistics[ae_grade3plus_rate, discontinuation_rate]`
- `20_aml_eln_risk.R` → `data/eln_risk_stats.json` → `disease_specific[eln_risk_*]`

Each R script must write a companion `data/{script_name}_stats.json` for HPW to extract `key_statistics`. This is an additional CSA change.

### 4.3 CLI Changes — `hpw create-draft`

**New flags:**

| Flag | Type | Description |
|------|------|-------------|
| `--disease {aml\|cml\|mds\|hct}` | string | Disease type for CSA |
| `--data-file PATH` | path | Raw patient data file (triggers CSA auto-run) |
| `--csa-output PATH` | path | Override project's `csa_output_dir` |
| `--skip-csa` | flag | Skip CSA auto-trigger even if manifest absent |

**Auto-trigger logic:**

```python
def _resolve_statistical_bridge(args, phase_manager):
    """Returns StatisticalBridge if available, None otherwise."""
    csa_dir = args.csa_output or phase_manager.metadata.csa_output_dir
    if csa_dir and (csa_dir / "hpw_manifest.json").exists():
        return StatisticalBridge(csa_dir / "hpw_manifest.json")
    if args.data_file and not args.skip_csa:
        if _prompt_run_csa():
            _run_csa_subprocess(args.data_file, args.disease, csa_dir)
            return StatisticalBridge(csa_dir / "hpw_manifest.json")
    return None  # proceed without CSA
```

**Subprocess call:**

```python
def _run_csa_subprocess(data_file: Path, disease: str, output_dir: Path) -> int:
    """
    Runs CSA run-analysis. Requires CSA_SKILL_DIR env var.
    Returns exit code: 0=success, 1=partial, 2=failure.
    """
    csa_skill_dir = Path(os.environ["CSA_SKILL_DIR"])
    cmd = [
        sys.executable, "-m", "scripts.crf_pipeline", "run-analysis",
        str(data_file), "-d", disease, "-o", str(output_dir)
    ]
    return subprocess.run(cmd, cwd=csa_skill_dir).returncode
```

---

## 5. Template Placeholders

New placeholder tokens in `tools/draft_generator/section_templates.py`:

| Token | Injected By | Content |
|-------|-------------|---------|
| `{{STATISTICAL_METHODS}}` | `generate_methods_paragraph()` | Full Statistical Analysis paragraph |
| `{{RESULTS_BASELINE}}` | `generate_results_prose()['baseline']` | Table 1 prose narrative |
| `{{RESULTS_EFFICACY}}` | `generate_results_prose()['efficacy']` | Efficacy outcomes narrative |
| `{{RESULTS_SURVIVAL}}` | `generate_results_prose()['survival']` | Survival analysis narrative |
| `{{RESULTS_SAFETY}}` | `generate_results_prose()['safety']` | Safety/AE narrative |
| `{{ABSTRACT_STATS}}` | `get_abstract_statistics()` | Key stats for structured abstract |

**Fallback**: If `bridge` is `None` or a section key is absent, placeholder is replaced with `[PENDING — run statistical analysis]`.

---

## 6. Error Handling

| Scenario | Behavior |
|----------|----------|
| `hpw_manifest.json` not found | `StatisticalBridge.from_project()` returns `None`; HPW proceeds normally |
| `schema_version` major mismatch | Raise `ManifestVersionError` with helpful message |
| Required `key_statistics` key missing | Log warning; `get_stat()` returns `None`; prose template uses `[DATA UNAVAILABLE]` |
| CSA subprocess returns exit code 1 (partial) | Warn user; attempt to load partial manifest |
| CSA subprocess returns exit code 2 (failure) | Error; do not attempt manifest load; proceed without CSA |
| CSA subprocess times out (>5 min) | Kill subprocess; warn; proceed without CSA |
| `$CSA_SKILL_DIR` not set when auto-trigger needed | Prompt user for path; store in `PhaseManager` |

---

## 7. Test Plan

### 7.1 Test Scope

| Type | Target | Tool |
|------|--------|------|
| Unit | `StatisticalBridge` with mock manifest JSON | `pytest` |
| Unit | `generate_methods_paragraph()` templates per disease | `pytest` |
| Unit | `verify_manuscript_statistics()` regex + matching | `pytest` |
| Unit | `ManuscriptMetadata` serialization/deserialization | `pytest` |
| Integration | `create-draft --data-file` with mock CSA subprocess | `pytest` + mock |
| Integration | Full `create-draft` with real manifest produces `.docx` with injected stats | manual |

### 7.2 Key Test Cases

- [ ] Bridge loads valid manifest → `is_available = True`
- [ ] Bridge with missing manifest → `is_available = False`, no exception
- [ ] `generate_methods_paragraph()` for AML contains "cox.zph" when survival script ran
- [ ] `generate_methods_paragraph()` does NOT mention Fine-Gray if `04_survival.R` not in `scripts_run`
- [ ] `generate_results_prose()['efficacy']` contains exact value from `key_statistics.orr.value`
- [ ] `format_stat('os_hr', fmt='hr')` → `"HR 0.62 (95% CI 0.41–0.94; p = 0.024)"`
- [ ] `verify_manuscript_statistics()` detects "68.3%" when manifest has `orr.value = 67.3`
- [ ] `verify_manuscript_statistics(strictness='off')` returns empty list regardless
- [ ] `ManuscriptMetadata` round-trips `csa_output_dir` through JSON serialization
- [ ] Auto-trigger skipped when `--skip-csa` flag present

---

## 8. Implementation Order

### Phase A — Foundation (implement first, unblocks all)

```
1. CSA: Add data/{script}_stats.json output to each R script
2. CSA: orchestrator.py → _write_hpw_manifest()
3. HPW: tools/statistical_bridge.py (StatisticalBridge class, read-only)
4. HPW: phases/phase_manager.py → ManuscriptMetadata + 3 fields
5. HPW: tools/__init__.py → export StatisticalBridge
```

### Phase B — Writing Automation

```
6. HPW: StatisticalBridge.generate_methods_paragraph() — templates per disease
7. HPW: StatisticalBridge.generate_results_prose() — 4 section templates
8. HPW: StatisticalBridge.get_abstract_statistics()
9. HPW: tools/draft_generator/section_templates.py → add {{...}} placeholders
10. HPW: tools/draft_generator/manuscript_drafter.py → accept bridge param, inject
```

### Phase C — End-to-End Trigger

```
11. HPW: cli.py create-draft → --disease, --data-file, --csa-output, --skip-csa flags
12. HPW: cli.py → _resolve_statistical_bridge() + _run_csa_subprocess()
13. HPW: cli.py → prompt logic, $CSA_SKILL_DIR resolution
```

### Phase D — Quality Gate

```
14. HPW: StatisticalBridge.verify_manuscript_statistics()
15. HPW: StatisticalBridge.format_stat()
16. HPW: phases/phase4_7_prose/prose_verifier.py → verify_against_csa()
17. HPW: cli.py check-quality → load bridge if manifest present, run verify
```

### File Change Summary

| File | Skill | Change Type | Phase |
|------|-------|-------------|-------|
| `scripts/crf_pipeline/orchestrator.py` | CSA | Enhanced | A |
| `scripts/02_table1.R` … `scripts/25_*.R` | CSA | Enhanced (stats JSON output) | A |
| `tools/statistical_bridge.py` | HPW | **New** | A |
| `phases/phase_manager.py` | HPW | Enhanced | A |
| `tools/__init__.py` | HPW | Enhanced (export) | A |
| `tools/draft_generator/section_templates.py` | HPW | Enhanced (placeholders) | B |
| `tools/draft_generator/manuscript_drafter.py` | HPW | Enhanced | B |
| `cli.py` | HPW | Enhanced | C |
| `phases/phase4_7_prose/prose_verifier.py` | HPW | Enhanced | D |

---

## 9. Coding Conventions

All new HPW code follows existing project conventions:

| Item | Convention |
|------|------------|
| Module names | `snake_case.py` |
| Class names | `PascalCase` |
| Public methods | `snake_case()` |
| Constants | `UPPER_SNAKE_CASE` |
| Type hints | Full annotations on all public methods |
| Dataclasses | `@dataclass` with `Optional` for nullable fields |
| Import order | stdlib → third-party → internal |

New environment variable:

| Variable | Purpose | Owner | Required |
|----------|---------|-------|----------|
| `CSA_SKILL_DIR` | Absolute path to CSA skill root (for subprocess) | User | Only for auto-trigger |

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-03-05 | Initial design — manifest schema, StatisticalBridge API, PhaseManager extension, CLI spec | kimhawk |
