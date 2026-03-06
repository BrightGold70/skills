# CRF Pipeline Overhaul Design Document

> **Summary**: Detailed technical design for the unified CRF data collection pipeline with module interfaces, data flows, config schemas, and extraction strategy chain.
>
> **Project**: clinical-statistics-analyzer
> **Author**: kimhawk
> **Date**: 2026-03-03
> **Status**: Draft
> **Planning Doc**: [crf-pipeline-overhaul.plan.md](../01-plan/features/crf-pipeline-overhaul.plan.md)

---

## 1. Overview

### 1.1 Design Goals

1. **Unified architecture**: Single `crf_pipeline/` package replacing both `CRF_Extractor/` and `scripts/06-09`
2. **Config-driven extensibility**: Add new diseases via JSON config only — no code changes
3. **Extraction intelligence**: Cascading strategy (regex → template → LLM) with per-field confidence
4. **Correctness**: Fix all broken features (dead code, broken flags, unimplemented rules)
5. **Testability**: Clean interfaces enabling >80% unit test coverage

### 1.2 Design Principles

- **Strategy Pattern**: Extractors are interchangeable strategies behind a common interface
- **Layered Config**: Base config + disease overlay + study overrides (deep merge)
- **Fail-safe extraction**: Never crash on a single field — log error, set confidence=0, continue
- **Data immutability**: Raw extraction results are never mutated; enrichment creates new objects

---

## 2. Architecture

### 2.1 Package Structure

```
crf_pipeline/
├── __init__.py                     # Package version, public API exports
├── cli.py                          # argparse CLI entry point
├── pipeline.py                     # Main orchestrator (replaces CRF_Extractor/main.py)
│
├── config/
│   ├── __init__.py
│   ├── loader.py                   # ConfigLoader: layered config resolution
│   ├── common_fields.json          # Demographics, labs, dates, AEs
│   ├── aml_fields.json             # AML-specific endpoints + markers
│   ├── cml_fields.json             # CML-specific endpoints + markers
│   ├── mds_fields.json             # MDS-specific endpoints + markers
│   ├── hct_fields.json             # HCT-specific endpoints + markers
│   ├── validation_rules.json       # Merged consistency + range rules
│   └── ocr_cleanup_rules.json      # OCR noise correction patterns
│
├── models/
│   ├── __init__.py
│   ├── field_definition.py         # FieldDefinition dataclass
│   ├── extraction_result.py        # ExtractionResult dataclass (per-field)
│   ├── patient_record.py           # PatientRecord (collection of ExtractionResults)
│   └── validation_issue.py         # ValidationIssue, ValidationResult (from current validator.py)
│
├── processors/
│   ├── __init__.py
│   ├── base.py                     # DocumentProcessor ABC
│   ├── pdf_processor.py            # PDFProcessor (from CRF_Extractor)
│   ├── docx_processor.py           # DocxProcessor (merged)
│   ├── xlsx_processor.py           # XlsxProcessor (from 08_parse_data.py)
│   └── spss_processor.py           # SpssProcessor (from 08_parse_data.py)
│
├── extractors/
│   ├── __init__.py
│   ├── base.py                     # FieldExtractorBase ABC
│   ├── regex_extractor.py          # RegexExtractor (deterministic)
│   ├── template_extractor.py       # TemplateExtractor (coordinate-based)
│   ├── llm_extractor.py            # LLMExtractor (Claude API)
│   ├── ocr_postprocessor.py        # OCRPostprocessor (from extractor_v2.py)
│   └── extraction_chain.py         # ExtractionChain (orchestrates strategy cascade)
│
├── validators/
│   ├── __init__.py
│   ├── schema_validator.py         # JSON Schema enforcement
│   ├── rule_validator.py           # RuleValidator: CR001-CR007 + disease-specific
│   └── quality_reporter.py         # Markdown/HTML quality reports
│
├── exporters/
│   ├── __init__.py
│   ├── base.py                     # ExporterBase ABC
│   ├── csv_exporter.py
│   ├── excel_exporter.py
│   ├── spss_exporter.py            # With variable/value labels + SPSS code mapping
│   └── json_exporter.py
│
└── utils/
    ├── __init__.py
    ├── encoding.py                 # Korean encoding detection (utf-8, cp949, euc-kr)
    ├── logging.py                  # Structured logging to output directory
    └── spss_mapping.py             # SPSS value ↔ code bidirectional mapping
```

### 2.2 Data Flow Diagram

```
                            ┌─────────────────────┐
                            │   Input Directory    │
                            │  (hospital subdirs)  │
                            └─────────┬───────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                  ▼
            ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
            │PDFProcessor  │ │DocxProcessor │ │XlsxProcessor │
            │(PyMuPDF+OCR) │ │(python-docx) │ │(openpyxl)    │
            └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
                   │                │                 │
                   └────────┬───────┘                 │
                            ▼                         │
                   ┌─────────────────┐                │
                   │ DocumentResult  │                │
                   │ {text, coords,  │                │
                   │  file, hospital}│                │
                   └────────┬────────┘                │
                            │                         │
                            ▼                         │
                   ┌─────────────────┐                │
                   │ OCRPostprocessor│                │
                   │ (clean text)    │                │
                   └────────┬────────┘                │
                            │                         │
                            ▼                         │
              ┌─────────────────────────┐             │
              │    ExtractionChain      │             │
              │  ┌───────────────────┐  │             │
              │  │ 1. RegexExtractor │  │             │
              │  │    conf: 0.90     │  │             │
              │  ├───────────────────┤  │             │
              │  │ 2. TemplateExtr.  │  │             │
              │  │    conf: 0.70     │  │             │
              │  ├───────────────────┤  │             │
              │  │ 3. LLMExtractor   │  │             │
              │  │    conf: variable │  │             │
              │  └───────────────────┘  │             │
              └────────────┬────────────┘             │
                           │                          │
                           ▼                          │
                  ┌─────────────────┐                 │
                  │ PatientRecord   │                 │
                  │ [ExtractionResult, ...]           │
                  │ {value, confidence,               │
                  │  method, source_file,             │
                  │  source_page}    │                │
                  └────────┬────────┘                 │
                           │                          │
                           ▼                          ▼
              ┌───────────────────────┐    ┌──────────────────┐
              │    Validators         │    │  (direct data    │
              │  ┌─────────────────┐  │    │   import path)   │
              │  │SchemaValidator  │  │    └──────────────────┘
              │  ├─────────────────┤  │
              │  │RuleValidator    │  │
              │  │CR001-CR007 +   │  │
              │  │disease-specific│  │
              │  └─────────────────┘  │
              └────────────┬──────────┘
                           │
                           ▼
              ┌───────────────────────┐
              │    Exporters          │
              │  CSV / Excel / SPSS  │
              │  + Quality Report     │
              └───────────────────────┘
```

### 2.3 Component Dependencies

| Component | Depends On | Purpose |
|-----------|-----------|---------|
| `pipeline.py` | `ConfigLoader`, all processors, `ExtractionChain`, validators, exporters | Orchestration |
| `ExtractionChain` | `RegexExtractor`, `TemplateExtractor`, `LLMExtractor`, `OCRPostprocessor` | Cascade strategy |
| `ConfigLoader` | `config/*.json` files | Layered config resolution |
| `RuleValidator` | `ValidationIssue`, `ValidationResult` models | Consistency checking |
| `SpssExporter` | `spss_mapping.py` utility | Value ↔ code conversion |
| `LLMExtractor` | `anthropic` SDK | Claude API calls |

---

## 3. Data Models

### 3.1 FieldDefinition

```python
@dataclass
class FieldDefinition:
    """Single CRF field definition loaded from config."""
    variable: str              # SPSS variable name (e.g., "FLT3ITD")
    crf_field: str             # Human label (e.g., "FLT3 ITD")
    field_type: str            # "string" | "numeric" | "categorical" | "date" | "text"
    extraction_method: str     # "regex" | "template" | "llm" | "ocr" | "derived"
    section: str               # Section name (e.g., "clinical_data_diagnosis")
    required: bool = False
    sps_code: bool = False     # Whether to map to SPSS numeric code
    patterns: List[str] = field(default_factory=list)
    values: List[str] = field(default_factory=list)  # Allowed categorical values
    disease: Optional[str] = None  # None = common, "aml" | "cml" | "mds" | "hct"
```

### 3.2 ExtractionResult

```python
@dataclass
class ExtractionResult:
    """Result of extracting a single field from a document."""
    variable: str              # SPSS variable name
    value: Any                 # Extracted value (typed: int, float, str, date str)
    raw_value: Optional[str]   # Original text before type conversion
    confidence: float          # 0.0 - 1.0
    method: str                # "regex" | "template" | "llm" | "ocr" | "manual"
    source_file: str           # File path
    source_page: Optional[int] # Page number (1-indexed), None for DOCX
    error: Optional[str] = None  # Error message if extraction failed

    @property
    def needs_review(self) -> bool:
        """Flag for human review if confidence < 0.5 or extraction failed."""
        return self.confidence < 0.5 or self.error is not None
```

### 3.3 PatientRecord

```python
@dataclass
class PatientRecord:
    """Collection of ExtractionResults for a single patient CRF."""
    case_no: Optional[str]
    hospital: str
    source_file: str
    disease: str               # "aml" | "cml" | "mds" | "hct"
    results: Dict[str, ExtractionResult]  # variable_name → ExtractionResult
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_flat_dict(self) -> Dict[str, Any]:
        """Convert to flat dict for export (variable → value)."""
        return {var: r.value for var, r in self.results.items()}

    def get_low_confidence_fields(self, threshold: float = 0.5) -> List[ExtractionResult]:
        """Return fields needing human review."""
        return [r for r in self.results.values() if r.confidence < threshold]

    @property
    def mean_confidence(self) -> float:
        """Average confidence across all extracted fields."""
        if not self.results:
            return 0.0
        return sum(r.confidence for r in self.results.values()) / len(self.results)
```

### 3.4 ValidationIssue / ValidationResult (preserved from current)

```python
class ValidationSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

@dataclass
class ValidationIssue:
    record_id: str
    field: str
    severity: ValidationSeverity
    message: str
    rule_id: Optional[str] = None
    actual_value: Any = None
    expected_value: Any = None

@dataclass
class ValidationResult:
    total_records: int = 0
    valid_records: int = 0
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def error_count(self) -> int
    @property
    def warning_count(self) -> int
    @property
    def completeness(self) -> float  # percentage
```

---

## 4. Module Interfaces

### 4.1 ConfigLoader

```python
class ConfigLoader:
    """Layered configuration loader with deep merge support."""

    def __init__(self, config_dir: str):
        """
        Args:
            config_dir: Path to config/ directory containing JSON files
        """

    def load(self, disease: str,
             study_overrides: Optional[Dict] = None) -> Dict:
        """
        Load merged configuration for a specific disease.

        Resolution order (later overrides earlier):
            1. common_fields.json
            2. {disease}_fields.json
            3. study_overrides (if provided)

        Args:
            disease: One of "aml", "cml", "mds", "hct"
            study_overrides: Optional dict of per-study field overrides

        Returns:
            Merged config dict with keys:
            {
                "sections": {section_name: {"fields": [FieldDefinition, ...]}},
                "spss_value_mapping": {field: {label: code}},
                "ocr_cleanup_rules": {...},
                "validation_rules": {...},
                "required_fields": [str, ...]
            }
        """

    def get_field_definitions(self, disease: str) -> List[FieldDefinition]:
        """Return flat list of all FieldDefinition objects for a disease."""

    def get_validation_rules(self) -> Dict:
        """Load validation_rules.json (shared across diseases)."""

    @staticmethod
    def deep_merge(base: Dict, overlay: Dict) -> Dict:
        """
        Recursively merge overlay into base.
        - Dict values: recursive merge
        - List values: overlay replaces base (not appended)
        - Scalar values: overlay replaces base
        """
```

### 4.2 DocumentProcessor (ABC)

```python
class DocumentProcessor(ABC):
    """Base class for document processors."""

    @abstractmethod
    def can_process(self, file_path: str) -> bool:
        """Return True if this processor handles the given file type."""

    @abstractmethod
    def process(self, file_path: str) -> DocumentResult:
        """
        Extract text and metadata from a document.

        Returns:
            DocumentResult with text, coordinates, and metadata
        """

    @abstractmethod
    def process_directory(self, input_dir: str) -> List[DocumentResult]:
        """
        Process all supported files in a directory tree.
        Subdirectories are treated as hospital identifiers.
        """

@dataclass
class DocumentResult:
    """Output from document processing."""
    file_path: str
    file_name: str
    hospital: str
    is_scanned: bool
    text: str                              # Full extracted text
    text_by_page: List[str]                # Per-page text (digital PDFs only)
    text_with_coords: List[CoordinateItem] # Coordinate-level items
    format: str                            # "pdf" | "docx" | "xlsx"
    error: Optional[str] = None

@dataclass
class CoordinateItem:
    """Text item with position information."""
    page: int           # 1-indexed
    text: str
    x: float
    y: float
    width: float
    height: float
    font: Optional[str] = None
    conf: Optional[int] = None  # OCR confidence (tesseract)
```

### 4.3 PDFProcessor (concrete)

```python
class PDFProcessor(DocumentProcessor):
    """PDF processor with auto-detection of scanned vs digital."""

    def __init__(self, ocr_lang: str = "eng+kor", ocr_dpi: int = 300):
        """
        Args:
            ocr_lang: Tesseract language string
            ocr_dpi: DPI for image conversion (scanned PDFs)
        """

    def can_process(self, file_path: str) -> bool:
        """True for .pdf files."""

    def is_scanned(self, file_path: str) -> bool:
        """True if extracted text < 100 chars (heuristic)."""

    def process(self, file_path: str) -> DocumentResult:
        """
        Process a single PDF. Routes to OCR or direct extraction
        based on is_scanned() detection.
        """

    def process_directory(self, input_dir: str) -> List[DocumentResult]:
        """
        Walk subdirectories (hospital → patient PDFs).
        Returns DocumentResult per file with hospital populated.
        """
```

### 4.4 FieldExtractorBase (ABC) and Concrete Extractors

```python
class FieldExtractorBase(ABC):
    """Base class for field extraction strategies."""

    @abstractmethod
    def extract(self, field: FieldDefinition,
                text: str,
                coords: Optional[List[CoordinateItem]] = None) -> ExtractionResult:
        """
        Extract a single field value from document content.

        Args:
            field: The field definition to extract
            text: Full document text
            coords: Optional coordinate items (for template extraction)

        Returns:
            ExtractionResult with value, confidence, and method
        """

    @abstractmethod
    def can_extract(self, field: FieldDefinition) -> bool:
        """Return True if this extractor supports the given field."""
```

```python
class RegexExtractor(FieldExtractorBase):
    """Deterministic regex-based extraction. Confidence: 0.90 on match."""

    def __init__(self, spss_mapping: Optional[Dict] = None):
        """
        Args:
            spss_mapping: Optional SPSS value mapping for code conversion
        """

    def extract(self, field, text, coords=None) -> ExtractionResult:
        """
        Try field.patterns in order, then auto-generated bilingual patterns.
        Confidence: 0.90 if pattern matches, 0.0 if no match.
        """

    def can_extract(self, field) -> bool:
        """True for all fields (always attempted as first strategy)."""
```

```python
class TemplateExtractor(FieldExtractorBase):
    """Coordinate-based extraction using label proximity. Confidence: 0.70."""

    def extract(self, field, text, coords=None) -> ExtractionResult:
        """
        Find field label in coordinates, read adjacent text items.
        Confidence: 0.70 if label found and value extracted.
        Requires coords; returns confidence 0.0 if coords is None.
        """

    def can_extract(self, field) -> bool:
        """True if extraction_method is 'template' and coords available."""
```

```python
class LLMExtractor(FieldExtractorBase):
    """Claude API-based extraction for complex/unstructured fields."""

    def __init__(self, api_key: Optional[str] = None,
                 model: str = "claude-sonnet-4-5-20250514",
                 max_context_chars: int = 4000):
        """
        Args:
            api_key: Anthropic API key (falls back to ANTHROPIC_API_KEY env var)
            model: Claude model ID
            max_context_chars: Max chars of document text to send per field
        """

    def extract(self, field, text, coords=None) -> ExtractionResult:
        """
        Send field definition + document text to Claude API.
        Returns structured response with value and self-assessed confidence.
        Confidence: from Claude's response (typically 0.6-0.95).
        """

    def extract_batch(self, fields: List[FieldDefinition],
                      text: str) -> List[ExtractionResult]:
        """
        Extract multiple fields in a single API call for cost efficiency.
        Groups related fields (same section) into batch prompts.
        """

    def can_extract(self, field) -> bool:
        """True if API key is configured."""
```

### 4.5 ExtractionChain

```python
class ExtractionChain:
    """Orchestrates cascading extraction strategy across multiple extractors."""

    def __init__(self, extractors: List[FieldExtractorBase],
                 ocr_postprocessor: Optional[OCRPostprocessor] = None,
                 min_confidence: float = 0.5):
        """
        Args:
            extractors: Ordered list of extractors (tried in sequence)
            ocr_postprocessor: Optional OCR text cleanup (applied before extraction)
            min_confidence: Minimum confidence to accept a result
        """

    def extract_field(self, field: FieldDefinition,
                      doc_result: DocumentResult) -> ExtractionResult:
        """
        Try each extractor in order until one returns confidence >= min_confidence.
        If all extractors fail or return low confidence, returns the best result
        (highest confidence) with needs_review=True.
        """

    def extract_all(self, fields: List[FieldDefinition],
                    doc_result: DocumentResult) -> List[ExtractionResult]:
        """
        Extract all fields from a document.
        LLM fields are batched for cost efficiency.
        Returns one ExtractionResult per field.
        """
```

### 4.6 OCRPostprocessor

```python
class OCRPostprocessor:
    """OCR text cleanup (from extractor_v2.py improvements)."""

    def __init__(self, cleanup_rules: Dict):
        """
        Args:
            cleanup_rules: Dict with keys:
                "remove_chars": List[str]
                "replace_pairs": List[List[str]]  # [[from, to], ...]
                "normalize_whitespace": bool
        """

    def clean(self, text: str) -> str:
        """
        Apply OCR noise correction:
        1. Remove noise characters
        2. Apply character substitution pairs (O→0, l→1, etc.)
        3. Normalize whitespace
        """
```

### 4.7 RuleValidator

```python
class RuleValidator:
    """Validates extracted records against consistency and range rules."""

    def __init__(self, validation_rules: Dict):
        """
        Args:
            validation_rules: Dict with keys:
                "range_checks": {field: {min, max, unit}}
                "consistency_rules": [{id, description, condition, require, severity}]
                "required_fields": [str]
                "categorical_values": {field: [allowed_values]}
        """

    def validate_record(self, record: PatientRecord) -> List[ValidationIssue]:
        """
        Run all validation checks on a single patient record.
        Check order: required → range → categorical → consistency (CR001-CR007).
        """

    def validate_dataset(self, records: List[PatientRecord]) -> ValidationResult:
        """Validate all records, aggregate results."""

    def _check_consistency_rule(self, rule: Dict,
                                 record: Dict) -> Optional[ValidationIssue]:
        """
        Dispatch consistency rules by rule_id.
        IMPLEMENTS ALL 7 RULES:
            CR001: CR achieved → CR date required
            CR002: Dead → death date required
            CR003: Age < 18 → pediatric warning
            CR004: Death date >= diagnosis date
            CR005: CR date >= induction date
            CR006: HCT date >= CR date
            CR007: Relapse date >= CR date
        """
```

### 4.8 SchemaValidator

```python
class SchemaValidator:
    """Validates data against JSON Schema definitions."""

    def __init__(self, schema_dir: str):
        """
        Args:
            schema_dir: Path to schemas/ directory
        """

    def validate_extraction_output(self, records: List[Dict],
                                    disease: str) -> List[ValidationIssue]:
        """
        Validate extracted data against crf_spec_schema.json.
        Returns list of schema violations as ValidationIssues.
        """

    def validate_config(self, config: Dict) -> List[str]:
        """Validate a field mapping config against expected structure."""
```

### 4.9 Exporters

```python
class ExporterBase(ABC):
    """Base class for data exporters."""

    @abstractmethod
    def export(self, records: List[PatientRecord],
               output_path: str, **kwargs) -> str:
        """Export records to file. Returns output path."""

class CsvExporter(ExporterBase):
    def export(self, records, output_path, encoding="utf-8") -> str

class ExcelExporter(ExporterBase):
    def export(self, records, output_path) -> str

class SpssExporter(ExporterBase):
    def __init__(self, field_definitions: List[FieldDefinition],
                 spss_mapping: Dict):
        """
        Args:
            field_definitions: For variable labels and column ordering
            spss_mapping: Bidirectional value ↔ code mapping
        """

    def export(self, records, output_path,
               variable_labels: Optional[Dict] = None,
               value_labels: Optional[Dict] = None) -> str:
        """
        Export to .sav with:
        - Column order matching field_definitions sequence
        - Variable labels from crf_field names
        - Value labels from spss_mapping
        - Automatic value-to-code conversion for sps_code fields
        """

class JsonExporter(ExporterBase):
    def export(self, records, output_path, include_confidence=True) -> str:
        """
        Export with full ExtractionResult metadata (confidence, method, source).
        """
```

### 4.10 Pipeline Orchestrator

```python
class CRFPipeline:
    """Main pipeline orchestrator (replaces CRF_Extractor/main.py)."""

    def __init__(self, config_dir: str,
                 disease: str,
                 output_dir: str,
                 use_llm: bool = False,
                 anthropic_api_key: Optional[str] = None,
                 study_overrides: Optional[Dict] = None):
        """
        Args:
            config_dir: Path to config/ directory
            disease: Disease type ("aml", "cml", "mds", "hct")
            output_dir: Output directory for all generated files
            use_llm: Enable Claude API extraction
            anthropic_api_key: API key (falls back to env var)
            study_overrides: Optional per-study config overrides
        """

    def run(self, input_dir: str,
            skip_validation: bool = False) -> PipelineResult:
        """
        Execute full extraction pipeline.

        Steps:
            1. Load layered config (common + disease overlay)
            2. Process documents (PDF/DOCX/XLSX auto-detection)
            3. Extract fields via ExtractionChain
            4. Validate records (schema + rules)
            5. Export (CSV, Excel, SPSS, JSON)
            6. Generate quality report

        Returns:
            PipelineResult with all outputs and statistics
        """

@dataclass
class PipelineResult:
    """Output from a complete pipeline run."""
    status: str                        # "success" | "partial" | "error"
    records_processed: int             # Documents found
    records_extracted: int             # Successfully extracted
    elapsed_time: float                # Seconds
    mean_confidence: float             # Average across all fields
    low_confidence_count: int          # Fields needing review
    outputs: Dict[str, str]            # {"csv": path, "excel": path, ...}
    validation: Optional[Dict] = None  # {total, valid, errors, warnings}
    errors: List[str] = field(default_factory=list)  # Non-fatal errors
```

---

## 5. Config Schemas

### 5.1 common_fields.json Structure

```json
{
  "version": "2.0",
  "description": "Common fields shared across all hematological trials",
  "sections": {
    "demographics": {
      "fields": [
        {
          "crf_field": "Case Number",
          "variable": "case_no",
          "type": "string",
          "extraction_method": "regex",
          "required": true,
          "patterns": ["[Cc]ase\\s*[Nn]o\\.?\\s*:?\\s*(\\w+-\\d+)", "증례번호\\s*:?\\s*(\\S+)"]
        },
        {
          "crf_field": "Age",
          "variable": "age",
          "type": "numeric",
          "extraction_method": "regex",
          "required": true,
          "patterns": ["[Aa]ge\\s*:?\\s*(\\d+)", "나이\\s*:?\\s*(\\d+)"]
        },
        {
          "crf_field": "Gender",
          "variable": "gender",
          "type": "categorical",
          "extraction_method": "regex",
          "sps_code": true,
          "values": ["Male", "Female", "남성", "여성", "M", "F"],
          "patterns": ["[Gg]ender\\s*:?\\s*(Male|Female|M|F|남성|여성)", "성별\\s*:?\\s*(남|여|남성|여성)"]
        }
      ]
    },
    "laboratory": {
      "fields": [
        {
          "crf_field": "WBC",
          "variable": "wbc1",
          "type": "numeric",
          "extraction_method": "regex",
          "patterns": ["WBC\\s*:?\\s*([\\d.]+)", "백혈구\\s*:?\\s*([\\d.]+)"]
        }
      ]
    },
    "dates": {
      "fields": [
        {
          "crf_field": "Date of Diagnosis",
          "variable": "diag_date",
          "type": "date",
          "extraction_method": "regex",
          "patterns": ["[Dd]iagnosis\\s*[Dd]ate\\s*:?\\s*(\\d{4}[-/.](\\d{1,2})[-/.](\\d{1,2}))"]
        }
      ]
    },
    "adverse_events": {
      "fields": []
    },
    "outcomes": {
      "fields": [
        {
          "crf_field": "Alive/Dead",
          "variable": "alive",
          "type": "categorical",
          "extraction_method": "regex",
          "required": true,
          "sps_code": true,
          "values": ["Alive", "Dead", "생존", "사망", "A", "D"]
        }
      ]
    }
  },
  "spss_value_mapping": {
    "gender": {"Male": 1, "Female": 2, "남성": 1, "여성": 2, "M": 1, "F": 2, "1": "Male", "2": "Female"},
    "alive": {"Alive": 1, "Dead": 2, "생존": 1, "사망": 2, "A": 1, "D": 2, "1": "Alive", "2": "Dead"}
  },
  "required_fields": ["case_no", "age", "gender", "alive"],
  "ocr_cleanup_rules": {
    "remove_chars": ["_", "!", "@", "#", "$", "%", "^", "&", "*", "~", "`"],
    "replace_pairs": [["O", "0"], ["l", "1"], ["I", "1"]],
    "normalize_whitespace": true
  }
}
```

### 5.2 Disease Overlay Structure (aml_fields.json example)

```json
{
  "version": "2.0",
  "disease": "aml",
  "description": "AML-specific fields overlaying common_fields",
  "sections": {
    "molecular_markers": {
      "fields": [
        {
          "crf_field": "FLT3 ITD",
          "variable": "FLT3ITD",
          "type": "categorical",
          "extraction_method": "template",
          "sps_code": true,
          "values": ["Positive", "Negative", "양성", "음성"],
          "patterns": ["FLT3[- ]?ITD\\s*:?\\s*(Positive|Negative|양성|음성|\\+|\\-)"]
        },
        {
          "crf_field": "NPM1",
          "variable": "NPM1",
          "type": "categorical",
          "extraction_method": "template",
          "sps_code": true,
          "values": ["Positive", "Negative", "양성", "음성"]
        }
      ]
    },
    "response": {
      "fields": [
        {
          "crf_field": "CR Achieved",
          "variable": "cr_achieved",
          "type": "categorical",
          "extraction_method": "regex",
          "sps_code": true,
          "values": ["Yes", "No", "CR", "CRi", "PR", "NR"]
        },
        {
          "crf_field": "MRD Status",
          "variable": "mrd_status",
          "type": "categorical",
          "extraction_method": "llm",
          "values": ["Positive", "Negative", "Not assessed"]
        }
      ]
    },
    "treatment": {
      "fields": [
        {
          "crf_field": "Induction Chemotherapy",
          "variable": "induction_ct",
          "type": "categorical",
          "extraction_method": "llm",
          "sps_code": true
        }
      ]
    }
  },
  "spss_value_mapping": {
    "FLT3ITD": {"Positive": 1, "Negative": 2, "양성": 1, "음성": 2, "1": "Positive", "2": "Negative"},
    "cr_achieved": {"Yes": 1, "No": 2, "CR": 1, "CRi": 3, "PR": 4, "NR": 5}
  }
}
```

### 5.3 Config Merge Example

```
common_fields.json:
  sections.demographics.fields = [case_no, age, gender, ...]
  sections.laboratory.fields = [wbc1, hb1, plt1, ...]
  spss_value_mapping = {gender: {...}, alive: {...}}

+ aml_fields.json:
  sections.molecular_markers.fields = [FLT3ITD, NPM1, IDH, ...]  # NEW section
  sections.response.fields = [cr_achieved, mrd_status, ...]       # NEW section
  sections.treatment.fields = [induction_ct, ...]                  # NEW section
  spss_value_mapping = {FLT3ITD: {...}, cr_achieved: {...}}        # MERGED into base

= merged config:
  sections = demographics + laboratory + dates + adverse_events + outcomes
             + molecular_markers + response + treatment
  spss_value_mapping = gender + alive + FLT3ITD + cr_achieved + ...
```

---

## 6. LLM Extraction Design

### 6.1 Claude API Prompt Template

```python
EXTRACTION_PROMPT = """You are a clinical data extraction specialist. Extract the requested
field from the CRF (Case Report Form) document text below.

**Field to extract:**
- Variable name: {variable}
- Label: {crf_field}
- Expected type: {field_type}
- Allowed values: {values}  (if categorical)

**Document text (from {source_file}, page {page}):**
{text_excerpt}

Respond with ONLY a JSON object:
{{
  "value": <extracted value or null if not found>,
  "confidence": <0.0-1.0 your confidence in the extraction>,
  "reasoning": "<brief explanation of how you found this value>"
}}
"""
```

### 6.2 Batch Extraction Prompt

```python
BATCH_PROMPT = """Extract the following fields from this CRF document.

**Fields to extract:**
{fields_table}

**Document text:**
{text_excerpt}

Respond with ONLY a JSON array:
[
  {{"variable": "field1", "value": ..., "confidence": 0.85, "reasoning": "..."}},
  {{"variable": "field2", "value": ..., "confidence": 0.70, "reasoning": "..."}}
]
"""
```

### 6.3 Cost Optimization Strategy

```
For each document:
1. Run RegexExtractor on ALL fields                          (cost: $0)
2. Run TemplateExtractor on fields where regex returned null (cost: $0)
3. Batch remaining null fields into 1-2 Claude API calls     (cost: ~$0.02-0.05)

Expected distribution:
- ~60% of fields resolved by regex (high confidence)
- ~20% of fields resolved by template (medium confidence)
- ~20% of fields sent to LLM (variable confidence)
- = ~10 fields per CRF sent to Claude API (batched into 1-2 calls)
```

---

## 7. Validation Rules Design

### 7.1 All 7 Consistency Rules (CR001-CR007)

```python
# CR001: CR achieved → CR date required
if record["cr_achieved"] in ["yes", "cr", "y", "예", "complete response"]:
    assert record["cr_date"] is not None

# CR002: Dead → death date required
if record["alive"] in ["dead", "d", "사망", "no"]:
    assert record["date_death"] is not None

# CR003: Age < 18 → pediatric warning
if record["age"] is not None and record["age"] < 18:
    warn("Pediatric patient (age < 18)")

# CR004: Death date >= diagnosis date (NEW)
if record["date_death"] and record["diag_date"]:
    assert parse_date(record["date_death"]) >= parse_date(record["diag_date"])

# CR005: CR date >= induction date (NEW)
if record["cr_date"] and record["induction_date"]:
    assert parse_date(record["cr_date"]) >= parse_date(record["induction_date"])

# CR006: HCT date >= CR date (NEW)
if record["hct_date"] and record["cr_date"]:
    assert parse_date(record["hct_date"]) >= parse_date(record["cr_date"])

# CR007: Relapse date >= CR date (NEW)
if record["relapse_date"] and record["cr_date"]:
    assert parse_date(record["relapse_date"]) >= parse_date(record["cr_date"])
```

### 7.2 Disease-Specific Validation Rules

```json
{
  "aml_rules": [
    {"id": "AML-R01", "description": "Blast% required at diagnosis", "require": "blast1 is not null"},
    {"id": "AML-R02", "description": "Cytogenetic risk requires cytogenetics", "condition": "cytogenetic_risk is not null", "require": "cytogene is not null"}
  ],
  "cml_rules": [
    {"id": "CML-R01", "description": "BCR-ABL required at diagnosis", "require": "bcr_abl_baseline is not null"},
    {"id": "CML-R02", "description": "TKI therapy required", "require": "tki_first_line is not null"}
  ],
  "mds_rules": [
    {"id": "MDS-R01", "description": "IPSS-R score required", "require": "ipss_r is not null"},
    {"id": "MDS-R02", "description": "Transfusion status required", "require": "transfusion_dependent is not null"}
  ],
  "hct_rules": [
    {"id": "HCT-R01", "description": "Conditioning regimen required", "require": "conditioning is not null"},
    {"id": "HCT-R02", "description": "Donor type required", "require": "donor_type is not null"},
    {"id": "HCT-R03", "description": "Engraftment date >= HCT date", "condition": "engraft_anc_date", "require": "engraft_anc_date >= hct_date"}
  ]
}
```

---

## 8. Error Handling

### 8.1 Error Categories

| Category | Severity | Handling | Example |
|----------|----------|----------|---------|
| Document unreadable | ERROR | Skip document, log error, continue | Corrupted PDF |
| Field extraction failed | WARNING | Set confidence=0, continue to next field | No regex match |
| LLM API error | WARNING | Fall back to confidence=0, flag for review | Network timeout |
| Type conversion failed | WARNING | Keep raw string value, set confidence=0.3 | "unknown" for numeric field |
| Validation rule violation | ERROR/WARNING | Record issue, continue processing | Date ordering violation |
| Missing dependency | ERROR | Graceful degradation for optional features | pytesseract not installed |

### 8.2 Error Response Pattern

```python
# All extraction errors are captured, never crash the pipeline
try:
    result = extractor.extract(field, text, coords)
except Exception as e:
    result = ExtractionResult(
        variable=field.variable,
        value=None,
        raw_value=None,
        confidence=0.0,
        method=extractor.__class__.__name__,
        source_file=doc_result.file_path,
        source_page=None,
        error=str(e)
    )
    logger.warning(f"Extraction failed for {field.variable}: {e}")
```

---

## 9. Test Plan

### 9.1 Test Scope

| Type | Target | Tool | Coverage Target |
|------|--------|------|-----------------|
| Unit | ConfigLoader, Extractors, Validators, Models | pytest | >80% |
| Integration | ExtractionChain (regex→template→LLM cascade) | pytest + mocks | >70% |
| Regression | SAPPHIRE-G output comparison | pytest | 100% field match |
| Config | Disease overlay merge correctness | pytest | 100% |

### 9.2 Key Test Cases

**ConfigLoader:**
- [ ] Load common_fields.json alone
- [ ] Merge common + aml overlay (sections added, spss_mapping merged)
- [ ] Overlay field overrides base field with same variable name
- [ ] Study-specific override takes highest precedence
- [ ] Invalid disease name raises ValueError

**RegexExtractor:**
- [ ] Korean pattern matches ("나이: 65" → age=65)
- [ ] English pattern matches ("Age: 65" → age=65)
- [ ] Multiple patterns tried in order (first match wins)
- [ ] No match returns confidence=0.0
- [ ] Type conversion: numeric, date, categorical

**ExtractionChain:**
- [ ] Regex success → skip template and LLM
- [ ] Regex fail → template success → skip LLM
- [ ] All fail → return best result with needs_review=True
- [ ] LLM batch called only for remaining null fields

**RuleValidator:**
- [ ] CR001: CR achieved without date → error
- [ ] CR004: Death date before diagnosis → error
- [ ] CR005: CR date before induction → error
- [ ] CR003: Age < 18 → warning (not error)
- [ ] All rules pass on valid record → empty issues list

**Regression:**
- [ ] SAPPHIRE-G CRFs produce identical field values as current pipeline
- [ ] SPSS export matches existing variable structure (237 variables)

---

## 10. Implementation Order

```
Phase 1: Fix Broken Features
  1.1  Merge extractor_v2 improvements into extractor.py
  1.2  Fix --use-llm flag passthrough in main.py
  1.3  Implement CR004-CR007 in validator.py
  1.4  Rename 08_parse_data.py → parse_data.py, fix imports
  1.5  Add python-docx, jsonschema to requirements.txt
  1.6  Fix log file output path

Phase 2: Unified Architecture
  2.1  Create crf_pipeline/ package with __init__.py
  2.2  Define data models (FieldDefinition, ExtractionResult, PatientRecord)
  2.3  Implement ConfigLoader with deep_merge
  2.4  Split field_mapping.json → common_fields.json + aml_fields.json
  2.5  Migrate PDFProcessor, DocxProcessor into processors/
  2.6  Create extractor ABCs and migrate RegexExtractor, TemplateExtractor
  2.7  Implement ExtractionChain orchestrator
  2.8  Implement OCRPostprocessor (from extractor_v2 cleanup logic)
  2.9  Migrate validators and exporters
  2.10 Create unified cli.py entry point
  2.11 Create CRFPipeline orchestrator
  2.12 Remove hardcoded paths, use env vars

Phase 3: Claude API Integration
  3.1  Implement LLMExtractor with anthropic SDK
  3.2  Design extraction prompt templates
  3.3  Implement batch extraction for cost optimization
  3.4  Wire LLM into ExtractionChain as third strategy
  3.5  Add LLM-assisted OCR correction

Phase 4: Cross-Disease Field Mappings
  4.1  Create cml_fields.json
  4.2  Create mds_fields.json
  4.3  Create hct_fields.json
  4.4  Add disease-specific validation rules
  4.5  Test each config with sample documents

Phase 5: Quality & Testing
  5.1  Integrate confidence scoring into ExtractionResult pipeline
  5.2  Implement SchemaValidator using schemas/*.json
  5.3  Write unit tests (ConfigLoader, extractors, validators)
  5.4  Write regression tests (SAPPHIRE-G comparison)
  5.5  Generate quality report with confidence breakdown
```

---

## 11. Migration Strategy

### 11.1 Backwards Compatibility

During migration, maintain a thin wrapper at the old entry points:

```python
# scripts/01_parse_crf.py (preserved for backwards compatibility)
from crf_pipeline import CRFPipeline
# Delegate to new pipeline with AML defaults
```

```python
# CRF_Extractor/main.py (preserved during transition)
from crf_pipeline import CRFPipeline
# Translate DEFAULT_CONFIG to new format and delegate
```

### 11.2 Cutover Plan

1. Phase 1-2 complete → new pipeline produces identical output to old
2. Run both pipelines on SAPPHIRE-G data, compare outputs field-by-field
3. If 100% match → replace old entry points with thin wrappers
4. Phase 3-5 → new features only available through new pipeline
5. After validation → remove old CRF_Extractor/ directory

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-03-03 | Initial design from plan document | kimhawk |
