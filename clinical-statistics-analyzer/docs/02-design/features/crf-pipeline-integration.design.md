# CRF Pipeline Integration Design Document

> **Summary**: Technical design for consolidating `CRF_Extractor/`, root-level `crf_pipeline/`, and scripts 01/06-09 into `scripts/crf_pipeline/` with a new `parsers/` submodule and enhanced validators.
>
> **Project**: clinical-statistics-analyzer
> **Author**: kimhawk
> **Date**: 2026-03-03
> **Status**: Draft
> **Planning Doc**: [crf-pipeline-integration.plan.md](../../01-plan/features/crf-pipeline-integration.plan.md)

---

## 1. Overview

### 1.1 Design Goals

1. **Single location**: All Python CRF logic lives under `scripts/crf_pipeline/`
2. **Parsers as first-class citizens**: Scripts 01/06-09 become proper classes in `parsers/` with consistent interfaces
3. **Validator enrichment**: `09_validate.py`'s temporal logic becomes `TemporalValidator`; its completeness/range logic merges into `RuleValidator`
4. **Clean CLI**: Parser functionality exposed via subcommands alongside existing `run` command
5. **Zero R-script impact**: R scripts remain untouched numbered files in `scripts/`

### 1.2 Design Principles

- **Consistent parser interface**: All parsers share `parse(input_path) -> Dict` pattern
- **Reuse existing models**: Parsers output dicts compatible with `FieldDefinition`, `ValidationIssue`, etc.
- **No new dependencies**: Parsers use libraries already in `requirements.txt`
- **Logging over printing**: All `print()` replaced with `logging` module

---

## 2. Architecture

### 2.1 Target Package Structure

```
scripts/
├── crf_pipeline/                          # v3.0.0
│   ├── __init__.py
│   ├── cli.py                             # Enhanced with parser subcommands
│   ├── pipeline.py                        # Unchanged (CRFPipeline + PipelineResult)
│   │
│   ├── parsers/                           # NEW submodule
│   │   ├── __init__.py                    # Exports: CRFParser, ProtocolParser, CRFSpecParser, DataParser
│   │   ├── crf_parser.py                  # ← from 01_parse_crf.py
│   │   ├── protocol_parser.py             # ← from 06_parse_protocol.py (refactored)
│   │   ├── crf_spec_parser.py             # ← from 07_parse_crf_spec.py (refactored)
│   │   └── data_parser.py                 # ← from 08_parse_data.py (refactored)
│   │
│   ├── config/                            # Unchanged
│   │   ├── loader.py                      # ConfigLoader
│   │   ├── common_fields.json
│   │   ├── aml_fields.json / cml / mds / hct
│   │   ├── validation_rules.json
│   │   └── ocr_cleanup_rules.json
│   │
│   ├── models/                            # Unchanged
│   │   ├── field_definition.py            # FieldDefinition
│   │   ├── extraction_result.py           # ExtractionResult
│   │   ├── patient_record.py              # PatientRecord
│   │   └── validation_issue.py            # ValidationIssue, ValidationResult, ValidationSeverity
│   │
│   ├── processors/                        # Unchanged
│   │   ├── base.py                        # DocumentProcessor ABC
│   │   ├── pdf_processor.py
│   │   └── docx_processor.py
│   │
│   ├── extractors/                        # Unchanged
│   │   ├── base.py                        # FieldExtractorBase
│   │   ├── regex_extractor.py
│   │   ├── template_extractor.py
│   │   ├── llm_extractor.py
│   │   ├── ocr_postprocessor.py
│   │   └── extraction_chain.py
│   │
│   ├── validators/                        # Enhanced
│   │   ├── rule_validator.py              # RuleValidator (+ absorbed completeness/range from 09)
│   │   ├── temporal_validator.py          # NEW: TemporalValidator (from 09_validate.py)
│   │   ├── schema_validator.py            # SchemaValidator (unchanged)
│   │   └── quality_reporter.py            # QualityReporter (unchanged)
│   │
│   ├── exporters/                         # Unchanged
│   │   ├── base.py
│   │   ├── csv_exporter.py
│   │   ├── excel_exporter.py
│   │   ├── json_exporter.py
│   │   └── spss_exporter.py
│   │
│   └── utils/                             # Enhanced
│       ├── logging.py
│       ├── encoding.py
│       ├── spss_mapping.py
│       └── fuzzy_matching.py              # NEW: from 01_parse_crf.py
│
├── 02_table1.R                            # Unchanged
├── 03_efficacy.R ... 16_sankey.R          # Unchanged
```

### 2.2 Component Diagram

```
                          ┌──────────────────────────────────────────────┐
                          │              scripts/crf_pipeline/            │
                          │                                              │
  CLI Subcommands         │  ┌────────────────────────────────────────┐  │
  ─────────────────       │  │              cli.py                    │  │
  parse-crf ──────────────┤  │  run | parse-crf | parse-protocol     │  │
  parse-protocol ─────────┤  │  parse-data | validate                │  │
  parse-data ─────────────┤  └──────────┬───────────────┬────────────┘  │
  validate ───────────────┤             │               │               │
  run ────────────────────┤             ▼               ▼               │
                          │  ┌──────────────┐  ┌─────────────────┐      │
                          │  │   parsers/    │  │   pipeline.py   │      │
                          │  │              │  │  CRFPipeline     │      │
                          │  │ CRFParser    │  │                 │      │
                          │  │ ProtocolP.   │  │  processors/ ──┐│      │
                          │  │ CRFSpecP.    │  │  extractors/ ──┤│      │
                          │  │ DataParser   │  │  validators/ ──┤│      │
                          │  └──────┬───────┘  │  exporters/  ──┘│      │
                          │         │          └────────┬────────┘      │
                          │         │                   │               │
                          │         ▼                   ▼               │
                          │  ┌──────────────────────────────────────┐   │
                          │  │           models/ + config/           │   │
                          │  │  FieldDefinition, ExtractionResult   │   │
                          │  │  PatientRecord, ValidationIssue      │   │
                          │  │  ConfigLoader                        │   │
                          │  └──────────────────────────────────────┘   │
                          └──────────────────────────────────────────────┘
```

### 2.3 Data Flow

```
                    PARSER FLOW (new)                    EXTRACTION FLOW (existing)
                    ════════════════                     ═════════════════════════

  CRF Document ──► CRFParser.parse()                    Filled CRFs ──► CRFPipeline.run()
                       │                                                      │
                       ▼                                                      ▼
              crf_mapping.json                               processors/ (PDF/DOCX)
              validation_rules.json                               │
                       │                                          ▼
                       │                                   extractors/ (regex→template→LLM)
  Protocol ────► ProtocolParser.parse()                           │
                       │                                          ▼
                       ▼                                   PatientRecord[]
              protocol_spec.json ──────────────────────────►      │
                       │                                          ▼
  CRF Spec ────► CRFSpecParser.parse()                    validators/ (rule + temporal + schema)
                       │                                          │
                       ▼                                          ▼
              crf_spec.json ───────────────────────────────► ValidationResult
                                                                  │
  Patient Data ► DataParser.parse()                               ▼
                       │                                   exporters/ (CSV/XLSX/SPSS/JSON)
                       ▼                                          │
              data_summary.json                                   ▼
                       │                                   quality_report.md
                       ▼
              ValidationEngine.validate()
                       │
                       ▼
              validation_report.json
```

---

## 3. Module Interfaces

### 3.1 `parsers/__init__.py`

```python
from .crf_parser import CRFParser
from .protocol_parser import ProtocolParser
from .crf_spec_parser import CRFSpecParser
from .data_parser import DataParser, PatientDataParser

__all__ = [
    "CRFParser",
    "ProtocolParser",
    "CRFSpecParser",
    "DataParser",
    "PatientDataParser",
]
```

### 3.2 `parsers/crf_parser.py`

Refactored from `scripts/01_parse_crf.py`. Extracts variable **definitions** from CRF documents.

```python
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..utils.fuzzy_matching import fuzzy_match

logger = logging.getLogger(__name__)


class CRFParser:
    """Extract variable definitions from CRF protocol documents (DOCX/PDF).

    Produces a variable mapping (name, expression, type, coding) and
    inferred validation rules. Optionally maps variables to Excel columns.
    """

    def __init__(
        self,
        output_dir: Optional[str] = None,
        excel_path: Optional[str] = None,
        fuzzy_threshold: int = 60,
    ) -> None:
        """
        Args:
            output_dir: Directory for saving outputs. None = return only.
            excel_path: Optional Excel file for column-to-variable mapping.
            fuzzy_threshold: Minimum fuzzy match score (0-100).
        """

    def parse(self, input_path: str) -> Dict[str, Any]:
        """Parse a CRF document and extract variable definitions.

        Args:
            input_path: Path to CRF document (.docx or .pdf).

        Returns:
            {
                "metadata": {"source_file", "parse_date", "format", "variable_count"},
                "variables": [
                    {
                        "expression": str,     # CRF label text
                        "variable_name": str,  # Inferred SPSS name
                        "coding": str | None,  # Coding instructions
                        "type": str,           # "categorical" | "numeric" | "date" | "text"
                        "excel_column": str | None,  # Matched column (if excel_path provided)
                    }
                ],
                "validation_rules": {
                    "variable_name": {
                        "type": str,
                        "required": bool,
                        "allowed_values": list | None,
                        "range": {"min": num, "max": num} | None,
                    }
                }
            }
        """

    def _parse_docx(self, file_path: Path) -> List[Dict]:
        """Extract variables from DOCX using paragraph/table iteration."""

    def _parse_pdf(self, file_path: Path) -> List[Dict]:
        """Extract variables from PDF using PyPDF2 text extraction."""

    @staticmethod
    def _extract_variable_parts(left_text: str) -> tuple:
        """Split CRF text into (expression, variable_name)."""

    @staticmethod
    def _infer_variable_type(coding_text: str, var_name: str) -> str:
        """Infer type from coding text patterns."""

    @staticmethod
    def _infer_categorical_values(coding_text: Optional[str]) -> List[str]:
        """Extract allowed values from coding text."""

    def _map_excel_columns(self, variables: List[Dict]) -> List[Dict]:
        """Match variables to Excel columns via fuzzy matching."""
```

### 3.3 `parsers/protocol_parser.py`

Refactored from `scripts/06_parse_protocol.py`. Already a class — minimal changes needed.

```python
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class ProtocolParser:
    """Parse clinical trial protocol documents to extract study metadata.

    Extracts study ID, phase, disease, endpoints, treatment arms,
    eligibility criteria, and statistical design.
    """

    def __init__(self, output_dir: Optional[str] = None) -> None:
        """
        Args:
            output_dir: Directory for saving JSON output. None = return only.
        """

    def parse(self, input_path: str) -> Dict[str, Any]:
        """Parse a protocol document.

        Args:
            input_path: Path to protocol document (.docx or .pdf).

        Returns:
            {
                "metadata": {"source_file", "parse_date", "format"},
                "study_design": {"study_id", "phase", "randomized", "blinding", ...},
                "disease_info": {"name", "category", "subtypes"},
                "endpoints": {"primary": [...], "secondary": [...], "exploratory": [...]},
                "treatment_arms": [{"name", "type", "description", "regimen"}],
                "eligibility": {"inclusion": [...], "exclusion": [...]},
                "statistics": {"sample_size", "alpha", "power", "analysis_population", ...}
            }
        """

    # Private methods preserved from 06_parse_protocol.py:
    def _parse_docx(self, file_path: Path) -> str: ...
    def _parse_pdf(self, file_path: Path) -> str: ...
    def _extract_metadata(self) -> Dict: ...
    def _extract_study_design(self) -> Dict: ...
    def _extract_disease_info(self) -> Dict: ...
    def _categorize_disease(self, disease: str) -> str: ...
    def _extract_endpoints(self) -> Dict: ...
    def _extract_treatment_arms(self) -> List[Dict]: ...
    def _classify_arm_type(self, arm_text: str) -> str: ...
    def _extract_eligibility(self) -> Dict: ...
    def _extract_statistics(self) -> Dict: ...
    def _search_pattern(self, pattern: str, text: str, group: int = 0) -> Optional[str]: ...
    def _search_patterns(self, patterns: List[str], text: str, group: int = 0) -> Optional[str]: ...
```

**Changes from original**:
- Remove `__init__(self, file_path)` constructor pattern → `parse(input_path)` method pattern
- Remove `save_json()` method (output handled by CLI or caller)
- Remove `main()` function
- Replace `print()` with `logger`

### 3.4 `parsers/crf_spec_parser.py`

Refactored from `scripts/07_parse_crf_spec.py`.

```python
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class CRFSpecParser:
    """Parse CRF specification documents to extract variable definitions.

    Handles both DOCX (document format) and XLSX (tabular format).
    """

    def __init__(self, output_dir: Optional[str] = None) -> None: ...

    def parse(self, input_path: str) -> Dict[str, Any]:
        """Parse a CRF specification document.

        Returns:
            {
                "metadata": {"source_file", "parse_date", "format", "variable_count"},
                "variables": [
                    {
                        "variable_name": str,
                        "label": str,
                        "section": str,
                        "category": str | None,
                        "data_type": str,       # "numeric" | "categorical" | "date" | ...
                        "format": str,
                        "valid_range": str,
                        "unit": str,
                        "required": bool,
                        "notes": str
                    }
                ],
                "sections": {"section_name": [variable_dicts]}
            }
        """

    # Private methods preserved from 07_parse_crf_spec.py:
    def _parse_docx(self, file_path: Path) -> None: ...
    def _parse_xlsx(self, file_path: Path) -> None: ...
    def _is_section_header(self, text: str) -> bool: ...
    def _is_category_header(self, text: str) -> bool: ...
    def _parse_variable_from_text(self, text: str, section: str, category: str) -> Optional[Dict]: ...
    def _parse_variable_from_table(self, cells: List[str], section: str) -> Optional[Dict]: ...
    def _extract_metadata(self) -> Dict: ...
    def _organize_by_section(self) -> Dict: ...
```

**Changes from original**:
- Same constructor/method pattern shift as `ProtocolParser`
- Remove `save_json()`, `save_csv()`, `main()`

### 3.5 `parsers/data_parser.py`

Refactored from `scripts/08_parse_data.py`.

```python
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

import pandas as pd

logger = logging.getLogger(__name__)


class DataParser:
    """Parse patient data files (XLSX/CSV/SPSS/JSON) for structure analysis.

    Produces data summaries including variable statistics, missing patterns,
    and type detection. Does NOT extract individual field values (that's
    the extraction pipeline's job).
    """

    def __init__(self, output_dir: Optional[str] = None) -> None: ...

    def parse(self, input_path: str) -> Dict[str, Any]:
        """Parse a data file and produce structural summary.

        Returns:
            {
                "metadata": {"source_file", "parse_date", "format", "rows", "columns"},
                "variables": [
                    {
                        "name": str,
                        "label": str,
                        "data_type": str,
                        "missing_count": int,
                        "missing_pct": float,
                        "unique_values": int,
                        "sample_values": list
                    }
                ],
                "summary": {
                    "total_records": int,
                    "total_variables": int,
                    "completeness": float,
                    "date_columns": list,
                    "id_candidates": list
                }
            }
        """

    def get_dataframe(self, input_path: str) -> pd.DataFrame:
        """Return parsed data as a pandas DataFrame."""

    # Private methods:
    def _parse_xlsx(self, file_path: Path) -> pd.DataFrame: ...
    def _parse_csv(self, file_path: Path) -> pd.DataFrame: ...
    def _parse_spss(self, file_path: Path) -> pd.DataFrame: ...
    def _parse_json(self, file_path: Path) -> pd.DataFrame: ...
    def _extract_variables(self, df: pd.DataFrame) -> List[Dict]: ...
    def _calculate_summary(self, df: pd.DataFrame) -> Dict: ...


class PatientDataParser(DataParser):
    """Extended DataParser that identifies patient ID columns."""

    def identify_patient_column(self, df: pd.DataFrame) -> Optional[str]:
        """Heuristically identify the patient ID column."""

    def parse(self, input_path: str) -> Dict[str, Any]:
        """Parse with patient ID detection.

        Adds to base output:
            "patient_id_column": str | None
        """
```

**Changes from original**:
- `__init__(file_path)` → `__init__(output_dir)` + `parse(input_path)`
- `get_dataframe()` now takes `input_path` parameter (not stored in constructor)
- Remove `save_json()`, `export_csv()`, `main()`

### 3.6 `utils/fuzzy_matching.py` (NEW)

Extracted from `01_parse_crf.py`.

```python
"""Fuzzy string matching utilities for CRF variable name resolution."""

from typing import List, Optional, Tuple

try:
    from fuzzywuzzy import fuzz
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False


def fuzzy_match(
    value: str,
    choices: List[str],
    threshold: int = 60
) -> Tuple[Optional[str], int]:
    """Find the best fuzzy match for a value among choices.

    Args:
        value: String to match.
        choices: Candidate strings.
        threshold: Minimum score (0-100) to accept a match.

    Returns:
        (best_match, score) or (None, 0) if no match above threshold.
    """


def is_available() -> bool:
    """Check if fuzzywuzzy is installed."""
    return FUZZY_AVAILABLE
```

### 3.7 `validators/temporal_validator.py` (NEW)

Extracted from `09_validate.py`'s `_validate_temporal_logic()` and `_validate_date_sequence()`.

```python
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

import pandas as pd

from ..models.validation_issue import ValidationIssue, ValidationSeverity

logger = logging.getLogger(__name__)


class TemporalValidator:
    """Validate temporal logic and date ordering in patient data.

    Checks date sequences (diagnosis < treatment < response < death),
    visit ordering, and age/DOB consistency.
    """

    # Standard hematology date sequences
    DEFAULT_DATE_SEQUENCES = [
        ("diagnosis_date", "treatment_start_date", "Diagnosis must precede treatment"),
        ("treatment_start_date", "response_date", "Treatment must precede response"),
        ("response_date", "relapse_date", "Response must precede relapse"),
        ("diagnosis_date", "death_date", "Diagnosis must precede death"),
        ("treatment_start_date", "death_date", "Treatment must precede death"),
    ]

    def __init__(
        self,
        date_sequences: Optional[List[tuple]] = None,
        protocol_spec: Optional[Dict] = None,
    ) -> None:
        """
        Args:
            date_sequences: Custom date ordering rules. Uses DEFAULT_DATE_SEQUENCES if None.
            protocol_spec: Optional protocol spec to derive date expectations.
        """

    def validate(self, data: pd.DataFrame) -> List[ValidationIssue]:
        """Run all temporal validations on a DataFrame.

        Returns list of ValidationIssue for each violation found.
        """

    def validate_date_sequence(
        self,
        data: pd.DataFrame,
        earlier_col: str,
        later_col: str,
        description: str,
    ) -> List[ValidationIssue]:
        """Check that earlier_col date <= later_col date for all rows."""

    def validate_visit_order(
        self,
        data: pd.DataFrame,
        visit_col: str,
    ) -> List[ValidationIssue]:
        """Validate visit sequence ordering per patient."""

    @staticmethod
    def _find_column(
        columns: pd.Index,
        patterns: List[str],
    ) -> Optional[str]:
        """Find a column matching any of the given regex patterns."""

    @staticmethod
    def _parse_date(value: Any) -> Optional[datetime]:
        """Parse various date formats to datetime."""
```

---

## 4. CLI Design

### 4.1 Updated `cli.py` Subcommand Structure

```python
"""Unified CLI for CRF pipeline operations."""

import argparse
import sys

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="crf_pipeline",
        description="CRF data extraction and validation pipeline",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- Existing: run ---
    run_parser = subparsers.add_parser("run", help="Run full extraction pipeline")
    run_parser.add_argument("input_dir")
    run_parser.add_argument("-d", "--disease", default="aml", choices=["aml", "cml", "mds", "hct"])
    run_parser.add_argument("-o", "--output-dir")
    run_parser.add_argument("--use-llm", action="store_true")
    run_parser.add_argument("--skip-validation", action="store_true")
    run_parser.add_argument("--overrides", type=str, help="JSON string of study overrides")

    # --- NEW: parse-crf ---
    crf_parser = subparsers.add_parser("parse-crf", help="Extract variable definitions from CRF document")
    crf_parser.add_argument("input_path", help="CRF document (.docx or .pdf)")
    crf_parser.add_argument("-o", "--output", help="Output JSON path")
    crf_parser.add_argument("--excel", help="Optional Excel file for column mapping")
    crf_parser.add_argument("--fuzzy-threshold", type=int, default=60)

    # --- NEW: parse-protocol ---
    proto_parser = subparsers.add_parser("parse-protocol", help="Parse clinical trial protocol")
    proto_parser.add_argument("input_path", help="Protocol document (.docx or .pdf)")
    proto_parser.add_argument("-o", "--output", help="Output JSON path")

    # --- NEW: parse-data ---
    data_parser = subparsers.add_parser("parse-data", help="Parse patient data file")
    data_parser.add_argument("input_path", help="Data file (.xlsx, .csv, .sav, .json)")
    data_parser.add_argument("-o", "--output", help="Output JSON path")
    data_parser.add_argument("--patient-mode", action="store_true", help="Enable patient ID detection")

    # --- NEW: validate ---
    val_parser = subparsers.add_parser("validate", help="Validate data against specs")
    val_parser.add_argument("data_path", help="Patient data file")
    val_parser.add_argument("--protocol", help="Protocol spec JSON (from parse-protocol)")
    val_parser.add_argument("--crf-spec", help="CRF spec JSON (from parse-crf-spec)")
    val_parser.add_argument("--rules", help="Custom validation rules JSON")
    val_parser.add_argument("-o", "--output", help="Output report path")
    val_parser.add_argument("--format", choices=["json", "html", "md"], default="json")

    args = parser.parse_args()
    # Dispatch to handler...
```

### 4.2 Invocation Examples

```bash
# Full extraction pipeline (existing)
python -m scripts.crf_pipeline run /path/to/crfs --disease aml --use-llm

# Parse CRF variable definitions (replaces 01_parse_crf.py)
python -m scripts.crf_pipeline parse-crf /path/to/crf.docx -o crf_mapping.json

# Parse protocol (replaces 06_parse_protocol.py)
python -m scripts.crf_pipeline parse-protocol /path/to/protocol.pdf -o protocol.json

# Parse data summary (replaces 08_parse_data.py)
python -m scripts.crf_pipeline parse-data /path/to/data.xlsx --patient-mode -o summary.json

# Validate (replaces 09_validate.py)
python -m scripts.crf_pipeline validate /path/to/data.xlsx \
    --protocol protocol.json --crf-spec crf_spec.json --format md -o report.md
```

---

## 5. Refactoring Details

### 5.1 Constructor Pattern Change

All parsers shift from **file-in-constructor** to **file-in-method**:

```python
# BEFORE (scripts/06_parse_protocol.py)
parser = ProtocolParser("/path/to/protocol.pdf")
result = parser.parse()
parser.save_json("/path/to/output.json")

# AFTER (parsers/protocol_parser.py)
parser = ProtocolParser(output_dir="/path/to/output")
result = parser.parse("/path/to/protocol.pdf")
# Output handled by CLI or caller; parser is stateless per-call
```

**Rationale**: Enables reusing a single parser instance for multiple files without re-instantiation.

### 5.2 Output Handling

Parsers return dicts. Serialization is handled by CLI dispatch:

```python
# In cli.py handler
def handle_parse_protocol(args):
    parser = ProtocolParser()
    result = parser.parse(args.input_path)

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        logger.info(f"Saved to {args.output}")
    else:
        json.dump(result, sys.stdout, indent=2, default=str)
```

### 5.3 Validator Merge Strategy

`09_validate.py`'s `ValidationEngine` is split as follows:

| ValidationEngine method | Target |
|------------------------|--------|
| `_validate_completeness()` | Merge into `RuleValidator._check_required()` |
| `_validate_value_ranges()` | Merge into `RuleValidator._check_ranges()` |
| `_validate_temporal_logic()` | NEW `TemporalValidator.validate()` |
| `_validate_date_sequence()` | NEW `TemporalValidator.validate_date_sequence()` |
| `_validate_visit_order()` | NEW `TemporalValidator.validate_visit_order()` |
| `_validate_custom_rules()` | Merge into `RuleValidator._check_consistency()` |
| `_validate_endpoint_rule()` | Merge into `RuleValidator._check_generic_rule()` |
| `_validate_treatment_arm_rule()` | Merge into `RuleValidator._check_generic_rule()` |
| `save_html()` | Drop (use `QualityReporter` instead) |

**Integration into pipeline.py**:

```python
# In CRFPipeline.run(), after extraction and before export:
# 1. Existing rule validation
rule_validator = RuleValidator(validation_rules, self.disease)
rule_result = rule_validator.validate_dataset(records)

# 2. NEW: Temporal validation (if DataFrame available)
temporal_validator = TemporalValidator(protocol_spec=protocol_spec)
temporal_issues = temporal_validator.validate(df)

# 3. Merge issues
all_issues = rule_result.issues + temporal_issues
```

---

## 6. Import Changes

### 6.1 Package-Level Imports After Move

All internal imports change from `crf_pipeline.X` to relative imports:

```python
# BEFORE (crf_pipeline at repo root)
from crf_pipeline.models.field_definition import FieldDefinition
from crf_pipeline.config.loader import ConfigLoader

# AFTER (scripts/crf_pipeline/)
from .models.field_definition import FieldDefinition
from .config.loader import ConfigLoader

# OR from parsers submodule:
from ..models.validation_issue import ValidationIssue
from ..utils.fuzzy_matching import fuzzy_match
```

### 6.2 Files Requiring Import Updates

| File | Import changes |
|------|----------------|
| `pipeline.py` | All `from crf_pipeline.` → `from .` |
| `cli.py` | Add parser imports: `from .parsers import CRFParser, ...` |
| `extractors/extraction_chain.py` | `from crf_pipeline.extractors.` → `from .` |
| `extractors/llm_extractor.py` | `from crf_pipeline.models.` → `from ..models.` |
| `validators/rule_validator.py` | `from crf_pipeline.models.` → `from ..models.` |
| `config/loader.py` | `from crf_pipeline.models.` → `from ..models.` |
| All `__init__.py` | Update re-exports if any |

---

## 7. Dependency Map

### 7.1 Python Dependencies (consolidated `requirements.txt`)

```
# Document processing
PyMuPDF>=1.23.0              # PDF text extraction (fitz)
python-docx>=0.8.11          # DOCX parsing
pdfplumber>=0.9.0            # PDF table extraction (protocol parser)
PyPDF2>=3.0.0                # PDF text extraction (CRF parser)
pdf2image>=1.16.0            # PDF → image for OCR
pytesseract>=0.3.10          # OCR engine

# Data processing
pandas>=2.0.0                # DataFrame operations
numpy>=1.24.0                # Numerical operations
openpyxl>=3.1.0              # Excel read/write

# Export
pyreadstat>=1.2.0            # SPSS read/write

# LLM
anthropic>=0.18.0            # Claude API for LLM extraction

# Matching
fuzzywuzzy>=0.18.0           # Fuzzy string matching (optional)
python-Levenshtein>=0.21.0   # Speed up fuzzywuzzy (optional)

# Validation
jsonschema>=4.17.0           # JSON Schema validation
```

### 7.2 Module Dependency Graph

```
cli.py
├── pipeline.py
│   ├── config/loader.py
│   │   └── models/field_definition.py
│   ├── processors/ (pdf, docx)
│   ├── extractors/ (chain → regex, template, llm, ocr)
│   │   └── models/extraction_result.py
│   ├── validators/ (rule, temporal, schema, quality)
│   │   └── models/validation_issue.py
│   ├── exporters/ (csv, excel, spss, json)
│   │   └── models/patient_record.py
│   └── utils/ (logging, encoding, spss_mapping)
│
├── parsers/                    # NEW
│   ├── crf_parser.py
│   │   └── utils/fuzzy_matching.py
│   ├── protocol_parser.py
│   ├── crf_spec_parser.py
│   └── data_parser.py
│       └── (pandas, openpyxl, pyreadstat)
│
└── validators/temporal_validator.py  # NEW
    └── models/validation_issue.py
```

---

## 8. Files to Delete

| Path | Reason |
|------|--------|
| `CRF_Extractor/` (entire directory) | Superseded by `crf_pipeline/` |
| `scripts/01_parse_crf.py` | Absorbed into `parsers/crf_parser.py` |
| `scripts/06_parse_protocol.py` | Absorbed into `parsers/protocol_parser.py` |
| `scripts/07_parse_crf_spec.py` | Absorbed into `parsers/crf_spec_parser.py` |
| `scripts/08_parse_data.py` | Absorbed into `parsers/data_parser.py` |
| `scripts/09_validate.py` | Split across `validators/temporal_validator.py` + `rule_validator.py` |
| Root `crf_pipeline/` | Moved to `scripts/crf_pipeline/` |

---

## 9. Documentation Updates

### 9.1 SKILL.md Changes

Replace sections 6, 7, and 10 (CRF Recognition, Protocol/CRF Validation, Bundled Scripts) with:

```markdown
6. **CRF Data Pipeline** (`scripts/crf_pipeline/`):
   - Unified Python package for CRF document parsing, data extraction, and validation
   - **Parsers**: Extract variable definitions from CRF/protocol documents (DOCX/PDF/XLSX)
   - **Extractors**: Multi-strategy field extraction (regex → template → Claude LLM → OCR)
   - **Validators**: Rule-based, temporal, and schema validation with quality reporting
   - **Exporters**: CSV, Excel, SPSS (.sav with labels), JSON output formats
   - **Multi-disease**: Layered config for AML, CML, MDS, HCT
   - CLI: `python -m scripts.crf_pipeline [run|parse-crf|parse-protocol|parse-data|validate]`
```

### 9.2 CLAUDE.md Changes

Update the Architecture table:

```markdown
| # | Component | Language | Purpose |
|---|-----------|----------|---------|
| — | `scripts/crf_pipeline/` | Python | Unified CRF parsing, extraction, validation, export |
| 02 | `table1.R` | R | Baseline characteristics table |
| ... | ... | ... | ... |
```

Remove references to `CRF_Extractor/` and individual scripts 01/06-09.

---

## 10. Implementation Order

```
Phase 1: Create parsers/ submodule
  1.1  Create parsers/__init__.py
  1.2  Create utils/fuzzy_matching.py (extract from 01)
  1.3  Create parsers/crf_parser.py (refactor from 01)
  1.4  Create parsers/protocol_parser.py (refactor from 06)
  1.5  Create parsers/crf_spec_parser.py (refactor from 07)
  1.6  Create parsers/data_parser.py (refactor from 08)
  1.7  Create validators/temporal_validator.py (extract from 09)
  1.8  Enhance validators/rule_validator.py (merge from 09)

Phase 2: Move package & update CLI
  2.1  Move crf_pipeline/ → scripts/crf_pipeline/
  2.2  Update all internal imports to relative
  2.3  Add parser subcommands to cli.py
  2.4  Update __init__.py version to 3.0.0
  2.5  Verify: python -m scripts.crf_pipeline --help

Phase 3: Cleanup & documentation
  3.1  Delete CRF_Extractor/
  3.2  Delete scripts/01, 06, 07, 08, 09
  3.3  Delete root crf_pipeline/
  3.4  Update SKILL.md
  3.5  Update CLAUDE.md
  3.6  Update requirements.txt
```

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-03-03 | Initial draft from brainstorming session | kimhawk |
