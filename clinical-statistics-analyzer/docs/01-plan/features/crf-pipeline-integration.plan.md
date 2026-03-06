# CRF Pipeline Integration Plan

> **Summary**: Consolidate `CRF_Extractor/`, `crf_pipeline/`, and scripts 01/06-09 into a single `scripts/crf_pipeline/` package with a `parsers/` submodule. Clean break — no backward-compatible wrappers.
>
> **Project**: clinical-statistics-analyzer
> **Author**: kimhawk
> **Date**: 2026-03-03
> **Status**: Draft
> **Depends on**: `crf-pipeline-overhaul` (completed, 98.9% match)

---

## 1. Overview

### 1.1 Purpose

The `crf-pipeline-overhaul` feature built a unified `crf_pipeline/` package at the repo root, merging the best of `CRF_Extractor/` and the old scripts. This integration plan completes the consolidation by:

1. Moving `crf_pipeline/` under `scripts/` (collocating with R scripts)
2. Absorbing scripts 01, 06-09 into a new `parsers/` submodule
3. Deleting `CRF_Extractor/` and old standalone scripts
4. Updating SKILL.md, CLAUDE.md, and requirements.txt

### 1.2 Current State

```
clinical-statistics-analyzer/
├── CRF_Extractor/          # ← DELETE (superseded by crf_pipeline)
│   ├── main.py
│   ├── src/ (7 modules)
│   └── config/ (field_mapping.json, validation_rules.json)
├── crf_pipeline/           # ← MOVE to scripts/crf_pipeline/
│   ├── cli.py, pipeline.py
│   ├── config/, models/, processors/, extractors/, validators/, exporters/, utils/
├── scripts/
│   ├── 01_parse_crf.py     # ← ABSORB into scripts/crf_pipeline/parsers/
│   ├── 06_parse_protocol.py # ← ABSORB
│   ├── 07_parse_crf_spec.py # ← ABSORB
│   ├── 08_parse_data.py     # ← ABSORB
│   ├── 09_validate.py       # ← ABSORB
│   ├── 02_table1.R          # Unchanged
│   └── ... (R scripts)      # Unchanged
```

### 1.3 Target State

```
clinical-statistics-analyzer/
├── scripts/
│   ├── crf_pipeline/                    # Unified Python package
│   │   ├── __init__.py                  # v3.0.0
│   │   ├── cli.py                       # Unified CLI with subcommands
│   │   ├── pipeline.py                  # Main orchestrator
│   │   ├── config/                      # Layered config system
│   │   │   ├── loader.py
│   │   │   ├── common_fields.json
│   │   │   ├── aml_fields.json
│   │   │   ├── cml_fields.json
│   │   │   ├── mds_fields.json
│   │   │   ├── hct_fields.json
│   │   │   ├── validation_rules.json
│   │   │   └── ocr_cleanup_rules.json
│   │   ├── parsers/                     # NEW: Absorbed from scripts 01/06-09
│   │   │   ├── __init__.py
│   │   │   ├── crf_parser.py            # ← from 01_parse_crf.py
│   │   │   ├── protocol_parser.py       # ← from 06_parse_protocol.py
│   │   │   ├── crf_spec_parser.py       # ← from 07_parse_crf_spec.py
│   │   │   └── data_parser.py           # ← from 08_parse_data.py
│   │   ├── models/                      # Typed dataclasses
│   │   ├── processors/                  # Document I/O (PDF/DOCX)
│   │   ├── extractors/                  # Field extraction chain
│   │   ├── validators/                  # Rule + temporal + schema validation
│   │   │   ├── rule_validator.py        # Enhanced with 09_validate.py logic
│   │   │   ├── temporal_validator.py    # NEW: from 09_validate.py temporal checks
│   │   │   ├── schema_validator.py
│   │   │   └── quality_reporter.py
│   │   ├── exporters/                   # CSV/Excel/SPSS/JSON
│   │   └── utils/                       # Logging, encoding, SPSS mapping, fuzzy
│   │       └── fuzzy_matching.py        # NEW: from 01_parse_crf.py
│   ├── 02_table1.R                      # Unchanged
│   ├── 03_efficacy.R                    # Unchanged
│   ├── 04_survival.R                    # Unchanged
│   ├── 05_safety.R                      # Unchanged
│   ├── 10_sample_size.R                 # Unchanged
│   ├── 11_phase1_dose_finding.R         # Unchanged
│   ├── 12_phase2_simon.R               # Unchanged
│   ├── 14_forest_plot.R                 # Unchanged
│   ├── 15_swimmer_plot.R               # Unchanged
│   └── 16_sankey.R                      # Unchanged
```

---

## 2. Scope

### 2.1 In Scope

- [ ] Create `parsers/` submodule by refactoring scripts 01, 06-09
- [ ] Extract `temporal_validator.py` from 09_validate.py's temporal logic
- [ ] Extract `fuzzy_matching.py` utility from 01_parse_crf.py
- [ ] Move `crf_pipeline/` from repo root to `scripts/crf_pipeline/`
- [ ] Update all internal imports after move
- [ ] Update `cli.py` with `parse-crf`, `parse-protocol`, `parse-data`, `validate` subcommands
- [ ] Delete `CRF_Extractor/` directory
- [ ] Delete standalone scripts: 01, 06, 07, 08, 09
- [ ] Delete root-level `crf_pipeline/` directory
- [ ] Update SKILL.md, CLAUDE.md, requirements.txt

### 2.2 Out of Scope

- New features or capabilities (this is purely structural)
- R script changes (they remain unchanged)
- Test suite creation (separate task)
- New disease config files (already handled in overhaul)

---

## 3. Implementation Phases

### Phase 1: Create `parsers/` Submodule

Refactor the 5 Python scripts into proper module classes.

| Task | Source | Target | Key Changes |
|------|--------|--------|-------------|
| 1.1 | `01_parse_crf.py` | `parsers/crf_parser.py` | Extract `CRFParser` class; move fuzzy matching to `utils/fuzzy_matching.py` |
| 1.2 | `06_parse_protocol.py` | `parsers/protocol_parser.py` | Extract `ProtocolParser` class; remove `if __name__` block |
| 1.3 | `07_parse_crf_spec.py` | `parsers/crf_spec_parser.py` | Extract `CRFSpecParser` class |
| 1.4 | `08_parse_data.py` | `parsers/data_parser.py` | Extract `DataParser` class; use existing `models/` dataclasses |
| 1.5 | `09_validate.py` | `validators/temporal_validator.py` + enhance `rule_validator.py` | Split: temporal logic → `TemporalValidator`; completeness/range → merge into `RuleValidator` |
| 1.6 | — | `parsers/__init__.py` | Public API: `CRFParser`, `ProtocolParser`, `CRFSpecParser`, `DataParser` |

**Refactoring principles**:
- Each parser becomes a class with `parse(input_path) -> dict` interface
- Reuse existing `models/` types (FieldDefinition, ValidationIssue) where applicable
- Hardcoded paths → constructor parameters with defaults from config
- `print()` statements → `logging` module
- `argparse` blocks → removed (CLI handled by `cli.py`)

### Phase 2: Move Package & Update Imports

| Task | Description |
|------|-------------|
| 2.1 | Move `crf_pipeline/` → `scripts/crf_pipeline/` |
| 2.2 | Update all internal imports (grep for `from crf_pipeline` and `import crf_pipeline`) |
| 2.3 | Update `cli.py` to add parser subcommands: `parse-crf`, `parse-protocol`, `parse-data`, `validate` |
| 2.4 | Update `pipeline.py` to integrate parsers as optional pre-extraction stages |
| 2.5 | Verify package runs: `python -m scripts.crf_pipeline --help` |

### Phase 3: Cleanup & Documentation

| Task | Description |
|------|-------------|
| 3.1 | Delete `CRF_Extractor/` directory |
| 3.2 | Delete `scripts/01_parse_crf.py` |
| 3.3 | Delete `scripts/06_parse_protocol.py`, `07_parse_crf_spec.py`, `08_parse_data.py`, `09_validate.py` |
| 3.4 | Delete root-level `crf_pipeline/` (now empty after move) |
| 3.5 | Update `SKILL.md` — replace script listing with unified pipeline description |
| 3.6 | Update `CLAUDE.md` — update architecture table and path structure |
| 3.7 | Update `requirements.txt` — consolidate all Python dependencies |
| 3.8 | Update `__init__.py` version to 3.0.0 |

---

## 4. Source Mapping Detail

### 4.1 `01_parse_crf.py` → `parsers/crf_parser.py` + `utils/fuzzy_matching.py`

**Keep**:
- `parse_crf_document()` → `CRFParser.parse()`
- `extract_variables_from_text()` → `CRFParser._extract_variables()`
- `infer_variable_type()` → `CRFParser._infer_type()`
- Fuzzy matching logic → `utils/fuzzy_matching.py`

**Drop**:
- `argparse` CLI block
- `save_mapping()` / `save_validation_rules()` (use exporters instead)
- Hardcoded output paths

### 4.2 `06_parse_protocol.py` → `parsers/protocol_parser.py`

**Keep**:
- Protocol metadata extraction (study ID, phase, disease, endpoints)
- Treatment arm parsing
- Eligibility criteria extraction
- Sample size / alpha extraction

**Drop**:
- `argparse` CLI block
- `print()` statements → logging

### 4.3 `07_parse_crf_spec.py` → `parsers/crf_spec_parser.py`

**Keep**:
- DOCX table parsing for variable definitions
- XLSX sheet parsing for variable inventory
- Type/range/required extraction

**Drop**:
- `argparse` CLI block
- Duplicate type inference (use `models/field_definition.py`)

### 4.4 `08_parse_data.py` → `parsers/data_parser.py`

**Keep**:
- Multi-format data loading (XLSX/CSV/SPSS/JSON)
- `PatientDataParser` with patient ID detection
- Variable statistics and missing pattern analysis

**Drop**:
- `argparse` CLI block
- Standalone export logic (use exporters)

### 4.5 `09_validate.py` → Split across validators/

**To `validators/temporal_validator.py`** (NEW):
- Date sequence validation (diagnosis < treatment < response < death)
- Visit order consistency
- Age/DOB cross-check

**Merge into `validators/rule_validator.py`**:
- Completeness checks (required field validation)
- Range validation (min/max violations, outlier detection)
- Categorical value validation
- Custom endpoint rules

**Drop**:
- `argparse` CLI block
- HTML report generation (use `quality_reporter.py`)
- Broken digit-prefixed imports

---

## 5. CLI Design

### Updated `cli.py` Subcommands

```bash
# Full pipeline (existing)
python -m scripts.crf_pipeline run /path/to/crfs --disease aml

# Parser subcommands (NEW — from absorbed scripts)
python -m scripts.crf_pipeline parse-crf /path/to/crf.docx -o output.json
python -m scripts.crf_pipeline parse-protocol /path/to/protocol.pdf -o output.json
python -m scripts.crf_pipeline parse-data /path/to/data.xlsx -o output.json
python -m scripts.crf_pipeline validate /path/to/data.xlsx \
    --protocol protocol.json --crf-spec crf_spec.json

# Export (existing)
python -m scripts.crf_pipeline export /path/to/records.json --format spss
```

---

## 6. Success Criteria

- [ ] `python -m scripts.crf_pipeline --help` shows all subcommands
- [ ] `python -m scripts.crf_pipeline parse-crf` produces same output as old `01_parse_crf.py`
- [ ] `python -m scripts.crf_pipeline validate` produces same output as old `09_validate.py`
- [ ] `python -m scripts.crf_pipeline run --disease aml` works end-to-end
- [ ] No `CRF_Extractor/` directory exists
- [ ] No standalone scripts 01, 06-09 exist
- [ ] No root-level `crf_pipeline/` directory exists
- [ ] SKILL.md reflects unified pipeline
- [ ] CLAUDE.md architecture table updated
- [ ] All imports resolve (no broken imports)

---

## 7. Risks

| Risk | Mitigation |
|------|------------|
| Import path breakage after move | Grep all imports before/after; test `python -c "from scripts.crf_pipeline import ..."` |
| Loss of functionality during refactor | Verify each parser class produces equivalent output to original script |
| SKILL.md breaking OpenCode skill resolution | Test skill invocation after update |

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-03-03 | Initial draft from brainstorming session | kimhawk |
