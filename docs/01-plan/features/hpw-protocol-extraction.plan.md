# Plan: HPW Protocol Extraction

**Feature**: `hpw-protocol-extraction`
**Phase**: Plan
**Created**: 2026-03-06
**Skill**: `hematology-paper-writer`

---

## Overview

Enable the Hematology Paper Writer to ingest a clinical study protocol document (DOCX or PDF)
and automatically extract structured content that seeds the manuscript draft — background,
methods, statistical analysis plan, and reference list — reducing the time from protocol to
first draft and ensuring the manuscript accurately reflects the protocol design.

## Problem Statement

HPW currently generates manuscript drafts from scratch using PubMed search + NotebookLM
guidelines. When a clinical study protocol exists, it already contains:

- **Background**: rationale, prior evidence, study hypothesis
- **Methods**: study design, eligibility criteria, treatment arms, assessments
- **Statistical Analysis Plan (SAP)**: primary/secondary endpoints, sample size justification,
  analysis methods (OS, PFS, ORR, etc.)
- **Reference list**: protocol-cited papers (often 30–60 references)

Ignoring this document forces the user to manually re-enter all of this into the manuscript,
creating transcription errors and inconsistencies between protocol and paper.

## Goals

### Goal 1: Protocol Document Ingestion

Accept a protocol document at HPW project setup (Phase 1) and store it in the project folder.

**Acceptance Criteria**:
- Supported formats: DOCX (direct parse), PDF (text extraction via `pdfplumber`; scanned PDF falls back to OCR via `pytesseract`)
- Protocol stored at `{project_dir}/docs/protocol/protocol.{ext}`
- CLI command: `hpw load-protocol "protocol.docx" --project "Asciminib CML"`
- Extraction runs automatically on upload; results cached as `protocol_extracted.json`

### Goal 2: Background Extraction → Introduction Seed

Extract the protocol's rationale and prior evidence sections to seed the manuscript Introduction.

**Acceptance Criteria**:
- Identifies: study background/rationale section (keyword heuristics + section heading detection)
- Output: `introduction_seed.md` in `docs/drafts/` — structured paragraphs, not raw text
- Existing PubMed-sourced draft enhanced with protocol background, not replaced
- Extracted text cited as "(Protocol Section X)" placeholder until PubMed refs verified

### Goal 3: Methods Extraction → Methods Section Seed

Extract study design, eligibility criteria, treatment arms, and assessment schedule.

**Acceptance Criteria**:
- Identifies: study design (phase, randomization, blinding), I/E criteria (inclusion/exclusion lists),
  treatment regimen (doses, schedules), assessments (response criteria, timepoints)
- Output: `methods_seed.md` with IMRaD-compliant subsections pre-populated
- WHO/ICC diagnostic criteria cross-referenced via `NomenclatureChecker`
- Reporting guideline flags set: CONSORT if RCT, STROBE if observational

### Goal 4: SAP Extraction → Statistical Methods Seed

Extract the statistical analysis plan content for the Statistical Methods subsection.

**Acceptance Criteria**:
- Extracts: primary endpoint (OS/PFS/ORR/CR), statistical test (log-rank, Cox, Fine-Gray),
  sample size (N, power, alpha, dropout assumption), secondary endpoints
- Output: `statistical_methods_seed.md`
- Extracted parameters stored in `protocol_params.json` for CSA auto-population
- Missing parameters flagged with `[TO FILL]` markers

### Goal 5: Reference Import

Import the protocol reference list as starting citations for the manuscript.

**Acceptance Criteria**:
- Parses reference list from protocol (Vancouver / numbered / author-year formats)
- Attempts PubMed verification for each reference via `PubMedVerifier`
- Verified refs added to `references.json` with PMID
- Unverified refs flagged for manual review
- CLI: `hpw load-protocol ... --import-refs` (default: on)

## Non-Goals

- Do NOT perform LLM summarization — extraction is rule-based/structural
- Do NOT modify the protocol document
- Do NOT replace full manuscript generation — seeds only; full draft still uses `create-draft`
- Do NOT handle protocol formats other than DOCX and PDF (v1)
- Do NOT support multi-file protocols (single document only in v1)

## Architecture Concept

```
protocol.docx / protocol.pdf
        │
        ▼
ProtocolParser (tools/protocol_parser.py)
  ├── DocxParser (python-docx)
  ├── PdfParser (pdfplumber + pytesseract fallback)
  └── SectionExtractor (heading detection + keyword heuristics)
        │
        ├── background_text → IntroductionSeeder
        ├── methods_text    → MethodsSeeder
        ├── sap_text        → StatisticalMethodsSeeder
        └── references      → ReferenceImporter → PubMedVerifier
              │
              ▼
        protocol_extracted.json
        protocol_params.json      ← CSA reads this
        docs/drafts/introduction_seed.md
        docs/drafts/methods_seed.md
        docs/drafts/statistical_methods_seed.md
```

## Files to Create / Modify

| File | Action | Purpose |
|------|--------|---------|
| `tools/protocol_parser.py` | **Create** | Core extraction engine |
| `tools/__init__.py` | **Modify** | Export `ProtocolParser` |
| `phases/phase1_topic/topic_development.py` | **Modify** | Accept protocol on project init |
| `cli.py` | **Modify** | Add `load-protocol` command |
| `hematology-journal-specs/protocol-sections.yaml` | **Create** | Section heading patterns per document type |

## Key Risks

| Risk | Mitigation |
|------|-----------|
| Section heading variations across institutions | Keyword heuristic fallback + user-editable section map |
| Scanned PDF quality too low for OCR | Warn user; allow manual seed text paste |
| Reference format inconsistency | Best-effort parse; unrecognized refs flagged |
| Protocol language ≠ manuscript language | Seeds are starting points; `edit-manuscript` polishes |

## Dependencies

- `python-docx` (existing in HPW)
- `pdfplumber` (add to `requirements.txt`)
- `pytesseract` (optional, for scanned PDF fallback)
- `PubMedVerifier` (existing in `tools/pubmed_verifier.py`)
- `NomenclatureChecker` (existing in `tools/nomenclature_checker.py`)

## Success Metrics

- Protocol load + full extraction completes in < 30 seconds for a typical 50-page protocol
- ≥ 80% of SAP parameters auto-extracted without manual intervention
- ≥ 70% of protocol references successfully PubMed-verified
- Introduction + Methods seeds require ≤ 30% manual editing before submission quality

## Implementation Order (Do Phase)

1. `ProtocolParser` — DOCX parser (section heading detection, text extraction)
2. `ProtocolParser` — PDF parser (pdfplumber + pytesseract fallback)
3. `SectionExtractor` — Background, Methods, SAP extraction logic
4. `ReferenceImporter` — Reference list parsing + PubMed verification
5. `protocol_params.json` schema — for CSA integration
6. Seed file writers — `introduction_seed.md`, `methods_seed.md`, `statistical_methods_seed.md`
7. CLI `load-protocol` command
8. Phase 1 integration (`TopicDevelopmentManager`)
