# CRF Pipeline Overhaul Planning Document

> **Summary**: Unify and generalize the CRF data collection pipeline with cross-disease support, Claude API extraction, and per-field confidence scoring.
>
> **Project**: clinical-statistics-analyzer
> **Author**: kimhawk
> **Date**: 2026-03-03
> **Status**: Draft
> **Supersedes**: `crf-data-collection-pipeline.plan.md` (SAPPHIRE-G only)

---

## 1. Overview

### 1.1 Purpose

Transform the current fragmented CRF pipeline — split across base scripts (01, 06-09) and a SAPPHIRE-G-specific CRF_Extractor — into a single, unified pipeline that supports any hematological clinical trial (AML, CML, MDS, HCT) with intelligent extraction, per-field confidence scoring, and OpenCode skill integration.

### 1.2 Background

The current pipeline has two parallel layers with overlapping functionality:

| Layer | Components | Strengths | Weaknesses |
|-------|-----------|-----------|------------|
| **Base scripts** | `01_parse_crf.py`, `06-09_*.py` | General-purpose, any CRF format | No batch, no OCR, broken imports, rudimentary PDF |
| **CRF_Extractor** | `main.py`, `src/*.py`, `config/*.json` | OCR, batch, SPSS export, LLM fallback | Dead code, broken flags, hardcoded paths, SAPPHIRE-G only |

Critical bugs exist: `--use-llm` flag silently dropped, `extractor_v2.py` orphaned, `09_validate.py` has unfixable import path, 4/7 validation rules unimplemented.

### 1.3 Related Documents

- Previous plan: `docs/01-plan/features/crf-data-collection-pipeline.plan.md`
- Previous design: `docs/02-design/features/crf-data-collection-pipeline.design.md`
- Previous analysis: `docs/03-analysis/crf-data-collection-pipeline.analysis.md`
- Validation schemas: `schemas/crf_spec_schema.json`, `schemas/protocol_schema.json`, `schemas/validation_rules.json`

---

## 2. Scope

### 2.1 In Scope

- [x] Fix all broken features in existing codebase (Phase 1)
- [x] Unify base scripts and CRF_Extractor into single package (Phase 2)
- [x] Implement layered config system for cross-disease support (Phase 2)
- [x] Replace OpenAI GPT-4o with Claude API for LLM extraction (Phase 3)
- [x] Add disease-specific field mappings: CML, MDS, HCT (Phase 4)
- [x] Per-field confidence scoring system (Phase 5)
- [x] Programmatic JSON Schema enforcement (Phase 5)
- [x] Unit test suite (Phase 5)

### 2.2 Out of Scope

- Web UI / dashboard for extraction monitoring
- Integration with EDC systems (REDCap, Medidata)
- Non-hematological trial support
- Real-time streaming extraction
- Multi-language beyond Korean/English

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Phase | Status |
|----|-------------|----------|-------|--------|
| FR-01 | Wire `extractor_v2.py` improvements (OCR cleanup, SPSS code mapping) into main pipeline | High | 1 | Pending |
| FR-02 | Fix `--use-llm` flag to pass through to `FieldExtractor` | High | 1 | Pending |
| FR-03 | Implement CR004-CR007 date-ordering validation rules | High | 1 | Pending |
| FR-04 | Fix `09_validate.py` digit-prefixed module import | High | 1 | Pending |
| FR-05 | Add missing dependencies to `requirements.txt` | Medium | 1 | Pending |
| FR-06 | Create proper Python package with `__init__.py` | High | 2 | Pending |
| FR-07 | Remove hardcoded absolute paths, use config/env vars | High | 2 | Pending |
| FR-08 | Implement layered config: `common_fields.json` + disease overlays | High | 2 | Pending |
| FR-09 | Unified CLI entry point for all extraction operations | Medium | 2 | Pending |
| FR-10 | Replace OpenAI GPT-4o calls with Claude API | High | 3 | Pending |
| FR-11 | Expand LLM extraction to all complex/unstructured fields | High | 3 | Pending |
| FR-12 | LLM-assisted OCR error correction for Korean medical terms | Medium | 3 | Pending |
| FR-13 | CML field mapping: BCR-ABL, MMR/CCyR/DMR, TKI therapy | High | 4 | Pending |
| FR-14 | MDS field mapping: HI subtypes, transfusion independence, IPSS-R | High | 4 | Pending |
| FR-15 | HCT field mapping: engraftment, GVHD (acute/chronic), conditioning, GRFS | High | 4 | Pending |
| FR-16 | Per-field confidence scoring (regex=high, template=medium, LLM=variable) | High | 5 | Pending |
| FR-17 | Programmatic validation against JSON Schemas in `schemas/` | Medium | 5 | Pending |
| FR-18 | Log output to designated output directory | Low | 1 | Pending |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|-------------------|
| Accuracy | >95% extraction accuracy on standard fields | Manual audit of 10% random sample |
| Performance | Process single CRF in <30 seconds (excl. LLM calls) | Timing benchmark |
| Reliability | Handle corrupted/malformed PDFs without crashing | Exception handling coverage |
| Maintainability | New disease config addable without code changes | Config-only test |
| Testability | >80% code coverage on core extraction logic | pytest + coverage |
| Reproducibility | Same input → same output (deterministic for non-LLM methods) | Regression test suite |

---

## 4. Success Criteria

### 4.1 Definition of Done

- [ ] All 18 functional requirements implemented and verified
- [ ] Unit tests written and passing (>80% coverage on core modules)
- [ ] Existing SAPPHIRE-G extraction produces identical results to current pipeline
- [ ] At least one non-AML disease (CML or MDS) config validated against real data
- [ ] Claude API extraction functional for ≥5 complex fields
- [ ] Documentation updated (CLAUDE.md, SKILL.md)

### 4.2 Quality Criteria

- [ ] Zero broken imports or dead code
- [ ] All 7 consistency rules (CR001-CR007) passing
- [ ] Confidence scores populated for every extracted field
- [ ] JSON Schema validation enforced on all outputs

---

## 5. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Claude API cost for high-volume extraction | Medium | Medium | Batch similar fields, cache responses, use regex/template first and LLM only as fallback |
| Breaking existing SAPPHIRE-G workflow | High | Medium | Regression test suite comparing old vs new outputs before switchover |
| Cross-disease field mapping quality | Medium | High | Collaborate with domain experts per disease; validate against published CRF standards |
| OCR accuracy on degraded scans | High | Medium | Multi-pass OCR (pytesseract → LLM correction), flag low-confidence for human review |
| Korean medical terminology extraction | Medium | Medium | Claude's multilingual capability + custom Korean medical term dictionary |
| Package restructuring breaks imports | Medium | Low | Gradual migration with backwards-compatible aliases during transition |

---

## 6. Architecture

### 6.1 Unified Package Structure

```
crf_pipeline/                    # Unified package (replaces CRF_Extractor/ + scripts/06-09)
├── __init__.py
├── cli.py                       # Unified CLI entry point
├── config/
│   ├── common_fields.json       # Shared fields: demographics, labs, dates, AEs
│   ├── aml_fields.json          # AML overlay: CR/cCR/MRD, FLT3/NPM1/IDH
│   ├── cml_fields.json          # CML overlay: MMR/CCyR, BCR-ABL, TKI
│   ├── mds_fields.json          # MDS overlay: HI, IPSS-R, transfusion
│   ├── hct_fields.json          # HCT overlay: engraftment, GVHD, GRFS
│   ├── validation_rules.json    # All 7+ consistency rules
│   └── ocr_cleanup_rules.json   # OCR noise correction patterns
├── processors/
│   ├── __init__.py
│   ├── pdf_processor.py         # From CRF_Extractor (PyMuPDF + pytesseract)
│   ├── docx_processor.py        # From CRF_Extractor + base scripts
│   ├── xlsx_processor.py        # From 08_parse_data.py
│   └── spss_processor.py        # From 08_parse_data.py
├── extractors/
│   ├── __init__.py
│   ├── regex_extractor.py       # Deterministic regex patterns
│   ├── template_extractor.py    # Coordinate-based extraction
│   ├── llm_extractor.py         # Claude API extraction (replaces OpenAI)
│   └── ocr_postprocessor.py     # From extractor_v2.py (OCR cleanup)
├── validators/
│   ├── __init__.py
│   ├── schema_validator.py      # JSON Schema enforcement
│   ├── rule_validator.py        # CR001-CR007 + disease-specific
│   └── quality_reporter.py      # Markdown/HTML quality reports
├── exporters/
│   ├── __init__.py
│   ├── csv_exporter.py
│   ├── excel_exporter.py
│   ├── spss_exporter.py         # With variable/value labels
│   └── json_exporter.py
├── models/
│   ├── __init__.py
│   ├── field.py                 # Field definition with confidence score
│   ├── extraction_result.py     # Per-field: value, confidence, method, source
│   └── config_loader.py         # Layered config resolution
└── utils/
    ├── __init__.py
    ├── encoding.py              # Korean encoding detection
    └── logging.py               # Structured logging to output dir
```

### 6.2 Layered Config Resolution

```
Config loading order:
1. common_fields.json           → base fields (demographics, labs, dates, AEs)
2. {disease}_fields.json        → disease-specific overlay (endpoints, treatment, markers)
3. study-specific overrides     → optional per-study tweaks (if provided)

Merge strategy: deep merge with overlay taking precedence
```

### 6.3 Extraction Strategy Chain

```
For each field:
1. regex_extractor      → confidence: 0.9 (if pattern matches)
2. template_extractor   → confidence: 0.7 (if coordinates found)
3. llm_extractor        → confidence: variable (Claude API returns confidence)
4. manual_review        → flagged if all methods < 0.5 confidence

Per-field output:
{
  "variable": "cr_achieved",
  "value": 1,
  "confidence": 0.85,
  "method": "regex",
  "source_file": "hospital_A/patient_001.pdf",
  "source_page": 3
}
```

### 6.4 Disease-Specific Field Mapping Layers

**Common layer** (all diseases):
- Demographics: age, gender, ECOG, Karnofsky
- Labs: WBC, Hb, Plt, blast%, ANC
- Dates: diagnosis, treatment start, last follow-up, death
- Adverse events: CTCAE grade, type, relatedness
- Outcomes: alive/dead, cause of death

**AML overlay**:
- Molecular: FLT3-ITD, FLT3-TKD, NPM1, CEBPA, IDH1/2, ASXL1, DNMT3A
- Response: CR, cCR, CRi, CRp, MRD status
- Treatment: induction regimen, consolidation, HCT

**CML overlay**:
- Molecular: BCR-ABL (IS%), transcript type (e13a2/e14a2)
- Response: CHR, MCyR, CCyR, MMR, MR4, MR4.5, DMR
- Treatment: TKI (imatinib/dasatinib/nilotinib/bosutinib/ponatinib), TKI switches

**MDS overlay**:
- Scoring: IPSS-R (cytogenetics, blasts, Hb, plt, ANC)
- Response: HI-E, HI-P, HI-N, transfusion independence
- Treatment: HMA (azacitidine/decitabine), ESA, lenalidomide

**HCT overlay**:
- Transplant: conditioning (MA/RIC/NMA), donor type, stem cell source
- Engraftment: ANC >500 day, platelet >20K day
- GVHD: acute (grade I-IV, organ involvement), chronic (mild/moderate/severe)
- Composite: GRFS (GVHD-free, relapse-free survival)

---

## 7. Implementation Phases

### Phase 1: Fix Broken Features (FR-01 to FR-05, FR-18)

**Goal**: All existing functionality works correctly.

| Task | Description | Files Affected |
|------|-------------|---------------|
| 1.1 | Merge `extractor_v2.py` improvements into `extractor.py` | `src/extractor.py`, `src/extractor_v2.py` |
| 1.2 | Fix `--use-llm` flag passthrough | `main.py` |
| 1.3 | Implement CR004-CR007 in `_check_consistency_rule()` | `src/validator.py` |
| 1.4 | Rename `08_parse_data.py` → `parse_data.py`, fix imports | `scripts/08_parse_data.py`, `scripts/09_validate.py` |
| 1.5 | Add missing deps to `requirements.txt` | `requirements.txt` |
| 1.6 | Fix log file output path | `main.py` |

### Phase 2: Unify Architecture (FR-06 to FR-09)

**Goal**: Single `crf_pipeline/` package with layered configs.

| Task | Description |
|------|-------------|
| 2.1 | Create `crf_pipeline/` package structure with `__init__.py` |
| 2.2 | Migrate processors from CRF_Extractor + base scripts |
| 2.3 | Implement `config_loader.py` with layered config resolution |
| 2.4 | Create `common_fields.json` from shared fields in current `field_mapping.json` |
| 2.5 | Extract AML-specific fields into `aml_fields.json` |
| 2.6 | Create unified `cli.py` entry point |
| 2.7 | Replace hardcoded paths with env vars / config |
| 2.8 | Backwards-compatible wrapper for `scripts/01_parse_crf.py` |

### Phase 3: Claude API Integration (FR-10 to FR-12)

**Goal**: Claude replaces GPT-4o for all LLM extraction.

| Task | Description |
|------|-------------|
| 3.1 | Implement `llm_extractor.py` with Anthropic SDK |
| 3.2 | Structured output: Claude returns JSON with value + confidence |
| 3.3 | Expand LLM extraction to infections, antibiotics, cause of death, free-text fields |
| 3.4 | LLM-assisted OCR correction for Korean medical terminology |
| 3.5 | Cost optimization: batch fields, regex-first strategy |

### Phase 4: Cross-Disease Field Mappings (FR-13 to FR-15)

**Goal**: CML, MDS, HCT disease configs validated.

| Task | Description |
|------|-------------|
| 4.1 | Create `cml_fields.json` with BCR-ABL, TKI, response criteria |
| 4.2 | Create `mds_fields.json` with IPSS-R, HI subtypes, HMA |
| 4.3 | Create `hct_fields.json` with engraftment, GVHD, conditioning |
| 4.4 | Add disease-specific validation rules |
| 4.5 | Validate each config against sample CRF documents |

### Phase 5: Quality & Testing (FR-16 to FR-17)

**Goal**: Confidence scoring, schema enforcement, test suite.

| Task | Description |
|------|-------------|
| 5.1 | Implement `ExtractionResult` model with confidence, method, source |
| 5.2 | Integrate confidence scoring into all extractors |
| 5.3 | Implement `schema_validator.py` using `schemas/*.json` |
| 5.4 | Write unit tests for extractors, validators, config loader |
| 5.5 | Regression test: SAPPHIRE-G output matches current pipeline |

---

## 8. Key Architectural Decisions

| Decision | Options Considered | Selected | Rationale |
|----------|-------------------|----------|-----------|
| Pipeline unification | Keep separate / Unify | **Unify** | Eliminate code duplication, single maintenance surface |
| Config system | Single JSON / Per-disease / Layered | **Layered** | DRY (common base) + flexible (disease overlays) |
| LLM provider | OpenAI GPT-4o / Claude API / Configurable / Local | **Claude API** | Better structured output, ecosystem alignment |
| Execution model | CLI only / Skill only / Both | **Skill-integrated** | AI-orchestrated with programmatic access |
| Quality tracking | Pass/fail / Confidence / Full provenance | **Per-field confidence** | Actionable quality without excessive overhead |
| Package structure | Flat scripts / Monolithic / Modular | **Modular** | Clear separation: processors, extractors, validators, exporters |

---

## 9. Dependencies

### Python Packages (required)

| Package | Purpose | Currently Used |
|---------|---------|:--------------:|
| `anthropic` | Claude API for LLM extraction | New |
| `PyMuPDF` (fitz) | Digital PDF text extraction | Yes (CRF_Extractor) |
| `pytesseract` | OCR for scanned PDFs | Yes (CRF_Extractor) |
| `pdf2image` | PDF to image conversion for OCR | Yes (CRF_Extractor) |
| `python-docx` | DOCX parsing | Yes (missing from requirements.txt) |
| `pdfplumber` | PDF table extraction | Yes (scripts/06) |
| `openpyxl` | Excel read/write | Yes |
| `pyreadstat` | SPSS .sav read/write | Yes |
| `pandas` | Data manipulation | Yes |
| `jsonschema` | JSON Schema validation | New |
| `fuzzywuzzy` | Fuzzy string matching | Yes (optional) |

### External Services

| Service | Purpose | Credential |
|---------|---------|-----------|
| Claude API (Anthropic) | LLM field extraction | `ANTHROPIC_API_KEY` env var |

---

## 10. Next Steps

1. [ ] Review and approve this plan document
2. [ ] Create design document (`crf-pipeline-overhaul.design.md`)
3. [ ] Begin Phase 1 implementation (fix broken features)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-03-03 | Initial draft from brainstorming session | kimhawk |
