# Design: CRF Data Collection Pipeline

**Feature:** crf-data-collection-pipeline  
**Date:** 2026-03-03  
**Status:** Design Phase

---

## 1. Architecture Overview

The `crf-data-collection-pipeline` is integrated as a sub-module within the `clinical-statistics-analyzer` skill (at `~/.config/opencode/skill/clinical-statistics-analyzer/CRF_Extractor`). It follows a modular sequence for extracting and standardizing data from clinical trial case report forms (CRF PDFs and DOCXs). The architecture processes documents chronologically over four sequential steps:

1. **Document Processing:** Reading and parsing raw PDF/DOCX documents (both textual and scanned/OCR).
2. **Extraction:** Applying predefined field mappings (regex, structural cues, or LLMs if needed) to map raw text to structured keys.
3. **Validation:** Checking data types, valid ranges, and cross-field logic.
4. **Exporting:** Serializing the extracted/validated entities into target formats like SPSS and CSV.

## 2. Components

| Component | Responsibility |
| --- | --- |
| `main.py` | CLI entry point. Orchestrates the flow: `process_crf_directory` -> `batch_extract` -> `validate_and_report` -> `export_all`. |
| `document_processor` | Handles the ingestion of PDF and DOCX files. Converts scanned images to text via OCR if text layer is missing; parses textual PDFs and DOCXs directly. Outputs a raw string/text layer representation. |
| `extractor` / `FieldExtractor` | Consumes raw text and targets specific questions/fields using logic defined in `field_mapping.json`. Outputs structured Python dictionaries representing CRF forms. |
| `validator` / `DataValidator` | Checks data integrity using `validation_rules.json`. Generates warnings/errors for malformed values or missing data. Outputs `quality_report.md`. |
| `exporter` / `DataExporter` | Transforms structured and validated records into tabular outputs (.sav for SPSS, .csv routines). |

## 3. Data Model

The pipeline relies heavily on JSON schemas to configure and transport its data.

* **`field_mapping.json`**: Describes SPSS variable relationships. Examples: Variable Name (e.g., `DEMO01`), Regex/Search String, Data Type (Numeric, Date, Categorical).
* **`validation_rules.json`**: Describes logical constraints. Examples: `Age >= 18`, `Date_Onset <= Date_Resolution`.
* **Intermediate Representation (JSON)**: Data is passed between steps as JSON.
  * `raw_extraction.json`: Maps `{ "filename": "crf1.docx", "text_content": "..." }`
  * `extracted_data.json`: Key-value pairs per patient. Lists of `{"record_id": "001", "DEMO01": 54, ...}`

## 4. API Design / CLI Interface

No REST APIs are exposed. The interactions occur via a Command Line Interface (CLI):

```bash
python ~/.config/opencode/skill/clinical-statistics-analyzer/CRF_Extractor/main.py \
    --crf-dir <path_to_crf_pdfs_and_docxs> \
    --output-dir <path_for_outputs> \
    --config-dir <path_to_config_json_files> \
    [--use-llm] \
    [--skip-validation] \
    [--log-level INFO/DEBUG]
```

## 5. User Flow

1. **Configuration**: Clinical staff or researchers put the CRF PDFs and DOCXs into a single directory and configure `field_mapping.json` and `validation_rules.json` to match the target SPSS variables.
2. **Execution**: The user executes the `main.py` CLI script, which traverses the directory and processes each file.
3. **Review**: The user reviews the terminal logs and checks the automatically generated `quality_report.md` in the output directory to address any data entry or parsing failures.
4. **Consumption**: The user loads the final SPSS (`.sav`) and/or `.csv` files into their statistical environment (R/SPSS) for statistical analysis.
