# Plan: CRF Data Collection Pipeline

**Feature:** crf-data-collection-pipeline  
**Date:** 2026-03-03  
**Status:** Plan Phase

---

## 1. Problem Statement

Currently, CRF (Case Report Form) data from individual PDF and DOCX files across 8 hospitals is manually entered into the consolidated SPSS dataset. This process is:
- **Time-consuming**: 27+ files (PDF and DOCX) with 300+ fields each
- **Error-prone**: Manual data entry risks transcription errors
- **Inconsistent**: Different data entry patterns across sites

## 2. Objectives

1. **Automate data extraction** from individual PDF and DOCX CRF files
2. **Map 300+ CRF fields** to standardized variables matching existing SPSS structure
3. **Handle mixed formats**: scanned images and digital PDFs
4. **Support Korean/English** text extraction
5. **Generate validated output** in SPSS/CSV format
6. **Provide audit trail** for data provenance

---

## 3. Requirements

### Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| F01 | Extract data from PDF and DOCX files in target directories | Must |
| F02 | Map CRF form fields to SPSS variable names | Must |
| F03 | Handle scanned/image-based PDFs with OCR | Must |
| F04 | Handle digital PDFs and DOCX files with text extraction | Must |
| F05 | Support Korean text (name fields, comments) | Must |
| F06 | Export to SPSS (.sav) format | Must |
| F07 | Export to CSV format | Should |
| F08 | Validate extracted data (ranges, consistency) | Should |
| F09 | Generate data quality report | Should |
| F10 | Provide extraction audit trail | Should |

### Non-Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| NF01 | Extract >95% of standard fields automatically | Should |
| NF02 | Process each CRF in <30 seconds | Should |
| NF03 | Handle corrupted/malformed PDFs gracefully | Should |

---

## 4. Scope

### In Scope
- SAPPHIRE-G CRF PDF and DOCX files from 8 hospitals
- CRF form template version 1.1 (DOCX)
- Existing SPSS data structure (237 variables)

### Out of Scope
- Other clinical trials beyond SAPPHIRE-G
- Integration with external databases
- Real-time data collection (batch processing only)

---

## 5. Success Criteria

1. Successfully extract data from all 27+ PDF/DOCX files
2. Achieve >90% accuracy on standard fields
3. Generate valid SPSS dataset matching existing structure
4. Complete processing pipeline in <15 minutes total

---

## 6. Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Poor scan quality | High | Use advanced OCR (Google Cloud Vision) |
| Unstructured text | Medium | LLM-based extraction for complex fields |
| Missing data | Medium | Flag for manual review |
| Korean OCR errors | Medium | Use language-specific OCR models |

---

## 7. Deliverables

1. CRF field mapping document
2. Data extraction pipeline (Python scripts) integrated into the `clinical-statistics-analyzer` skill
3. Validated SPSS/CSV output file
4. Data quality report
5. User documentation

---

## 8. Timeline (Estimated)

| Phase | Duration | Activities |
|-------|----------|------------|
| Setup | 1 day | Environment, field mapping |
| Development | 3 days | OCR, extraction, validation |
| Testing | 2 days | QC, error handling |
| Deployment | 1 day | Run on all files, validate |
| **Total** | **7 days** | |
