# Design: HPW Protocol Extraction

**Feature**: `hpw-protocol-extraction`
**Phase**: Design
**Created**: 2026-03-06
**References**: [Plan](../../01-plan/features/hpw-protocol-extraction.plan.md)

---

## Architecture Overview

```
CLI: hpw load-protocol <file> --project <name>
                │
                ▼
        ProtocolParser (tools/protocol_parser.py)
         ├── DocxParser          ← python-docx
         ├── PdfParser           ← pdfplumber + pytesseract fallback
         └── SectionExtractor    ← heading detection + keyword heuristics
                │
        ┌───────┼──────────────────────┐
        ▼       ▼                      ▼
  BackgroundExtractor  MethodsExtractor  SAPExtractor
        │               │                │
        ▼               ▼                ▼
  introduction_seed.md  methods_seed.md  statistical_methods_seed.md
        │               │                │
        └───────────────┴────────────────┘
                        │
                        ▼
              protocol_extracted.json   ← human-readable extraction cache
              protocol_params.json      ← machine-readable for CSA

        ReferenceImporter
                │
                ▼
        PubMedVerifier (existing)
                │
                ▼
        references.json (verified) + unverified_refs.txt
```

---

## Module Design: `tools/protocol_parser.py`

### Public API

```python
class ProtocolParser:
    def __init__(self, project_dir: str): ...

    def load(self, file_path: str) -> "ProtocolDocument":
        """Load DOCX or PDF protocol. Returns ProtocolDocument."""

    def extract_all(self, doc: "ProtocolDocument") -> "ExtractionResult":
        """Run all extractors. Writes output files. Returns ExtractionResult."""

    def load_and_extract(self, file_path: str) -> "ExtractionResult":
        """Convenience: load + extract_all in one call."""
```

### Dataclasses

```python
@dataclass
class ProtocolDocument:
    file_path: str
    file_type: Literal["docx", "pdf"]
    raw_text: str              # full extracted text
    sections: list[Section]    # detected sections with headings

@dataclass
class Section:
    heading: str               # e.g. "4. Statistical Analysis Plan"
    heading_level: int         # 1=chapter, 2=section, 3=subsection
    text: str
    page_start: int            # PDF only; 0 for DOCX

@dataclass
class SAPParams:
    primary_endpoint: str      # e.g. "Overall Survival"
    statistical_test: str      # e.g. "log-rank test"
    sample_size_n: int | None
    power: float | None        # e.g. 0.80
    alpha: float | None        # e.g. 0.05
    dropout_rate: float | None
    secondary_endpoints: list[str]
    analysis_population: str   # e.g. "intention-to-treat"
    missing_fields: list[str]  # fields that could not be extracted

@dataclass
class ExtractionResult:
    project_dir: str
    background_seed: str       # markdown text for introduction_seed.md
    methods_seed: str          # markdown text for methods_seed.md
    statistical_methods_seed: str
    sap_params: SAPParams      # structured params for protocol_params.json
    references: list[ProtocolReference]
    warnings: list[str]        # non-fatal extraction issues
```

---

## Submodule Design

### 1. `DocxParser`

```python
class DocxParser:
    def parse(self, file_path: str) -> ProtocolDocument:
        """
        - python-docx: iterate paragraphs
        - Detect heading level from paragraph.style.name ("Heading 1", "Heading 2", etc.)
        - Fallback: ALL_CAPS short paragraph → heading level 1
        - Group paragraphs under their most recent heading → Section list
        - Extract text preserving paragraph breaks
        """
```

**Heading detection heuristics** (in priority order):
1. `paragraph.style.name` matches `r"Heading \d"` → use numeric level
2. Paragraph is bold + font size > body → infer level from size
3. Paragraph text matches `r"^\d+[\.\d]*\s+[A-Z]"` → numbered section
4. Paragraph is ALL_CAPS, len < 80 → level 1 heading

### 2. `PdfParser`

```python
class PdfParser:
    def parse(self, file_path: str) -> ProtocolDocument:
        """
        Primary: pdfplumber — extract text per page, detect headers by font size
        Fallback: if text yield < 100 chars/page average → scanned PDF → pytesseract OCR
        OCR: convert PDF pages to images (pdf2image) → tesseract → text
        """
    def _is_scanned(self, pages: list) -> bool:
        avg_chars = sum(len(p.extract_text() or "") for p in pages) / len(pages)
        return avg_chars < 100
```

**Dependencies to add to `requirements.txt`**:
```
pdfplumber>=0.10.0
pytesseract>=0.3.10   # optional; warn if not installed
pdf2image>=1.16.0     # required for OCR path
```

### 3. `SectionExtractor`

Matches sections to canonical protocol categories using keyword lists:

```python
SECTION_KEYWORDS = {
    "background": [
        "background", "rationale", "introduction", "scientific background",
        "study rationale", "prior evidence", "unmet need"
    ],
    "objectives": [
        "objective", "aim", "purpose", "hypothesis", "endpoint",
        "primary endpoint", "secondary endpoint"
    ],
    "eligibility": [
        "eligibility", "inclusion criteria", "exclusion criteria",
        "inclusion/exclusion", "patient selection", "study population"
    ],
    "study_design": [
        "study design", "design overview", "trial design",
        "randomization", "treatment arm", "dosing"
    ],
    "assessments": [
        "assessment", "evaluation", "schedule of events",
        "response criteria", "efficacy assessment"
    ],
    "sap": [
        "statistical", "analysis plan", "sample size", "power",
        "statistical methods", "statistical analysis"
    ],
    "references": [
        "reference", "bibliography", "literature cited"
    ]
}
```

Matching: each `Section.heading` is lowercased and checked against keyword lists.
If ambiguous, use section position heuristic (references always last, SAP near end).

---

## Extractors

### BackgroundExtractor

```python
class BackgroundExtractor:
    def extract(self, sections: list[Section]) -> str:
        """
        1. Find sections matching 'background' keywords
        2. Find sections matching 'objectives' keywords
        3. Combine: Background paragraphs + Objectives paragraphs
        4. Format as markdown with ## subheadings
        5. Add placeholder citations: [TO CITE: author, year] where refs appear
        Output: markdown string for introduction_seed.md
        """
```

**Output format** (`introduction_seed.md`):
```markdown
<!-- AUTO-GENERATED FROM PROTOCOL — REVIEW BEFORE SUBMISSION -->
<!-- Source: protocol.docx | Extracted: 2026-03-06 -->

## Background

{extracted background text}

## Study Rationale

{extracted rationale}

## Study Objectives

**Primary**: {primary endpoint}
**Secondary**: {secondary endpoints}
```

### MethodsExtractor

```python
class MethodsExtractor:
    def extract(self, sections: list[Section]) -> str:
        """
        1. Study design section → "Study Design" subsection
        2. Eligibility section → parse inclusion list (numbered/bulleted) and exclusion list
           - Detect list items: lines starting with digit, bullet, dash, or "·"
        3. Treatment arms → "Treatment" subsection
        4. Assessment schedule → "Assessments" subsection
        5. Cross-reference eligibility against NomenclatureChecker for WHO/ICC terms
        6. Detect study type (RCT/observational) → set reporting_guideline flag
        """
```

**Reporting guideline detection**:
- Contains "randomiz" + "arm" → CONSORT
- Contains "cohort" or "observational" → STROBE
- Contains "case" → CARE

**Output format** (`methods_seed.md`):
```markdown
<!-- AUTO-GENERATED FROM PROTOCOL -->

## Study Design

{design text}

## Eligibility Criteria

### Inclusion Criteria
1. {criterion}
2. {criterion}

### Exclusion Criteria
1. {criterion}

## Treatment

{treatment text}

## Assessments

{assessment text}

<!-- REPORTING GUIDELINE: CONSORT 2010 -->
```

### SAPExtractor

```python
class SAPExtractor:
    # Regex patterns for common SAP elements
    SAMPLE_SIZE_PATTERN = r"(?:n\s*=\s*|sample size\s+of\s+)(\d+)"
    POWER_PATTERN = r"(\d+)%?\s*power"
    ALPHA_PATTERN = r"(?:alpha|α|significance)\s*(?:level\s*)?(?:of\s*)?([0-9.]+)"
    ENDPOINT_PATTERN = r"primary\s+endpoint[:\s]+([^\.\n]+)"

    def extract(self, sections: list[Section]) -> tuple[str, SAPParams]:
        """
        1. Find SAP sections
        2. Apply regex patterns to extract numeric parameters
        3. Extract primary endpoint name (first match of ENDPOINT_PATTERN)
        4. Extract secondary endpoints (lines starting with '-' or numbered after "Secondary")
        5. Detect statistical test ('log-rank', 'Cox', 'Fine-Gray', 'Fisher', 'chi-square')
        6. Build SAPParams; mark missing_fields for any None values
        7. Format statistical_methods_seed.md
        """
```

**`protocol_params.json` schema** (for CSA auto-population):
```json
{
  "version": "1.0",
  "extracted_at": "2026-03-06T10:30:00Z",
  "source_file": "protocol.docx",
  "primary_endpoint": "Overall Survival",
  "statistical_test": "log-rank test",
  "sample_size_n": 120,
  "power": 0.80,
  "alpha": 0.05,
  "dropout_rate": 0.10,
  "analysis_population": "intention-to-treat",
  "secondary_endpoints": ["PFS", "ORR", "CRR", "DOR"],
  "study_type": "RCT",
  "reporting_guideline": "CONSORT",
  "disease_keywords": ["AML", "venetoclax"],
  "missing_fields": []
}
```

---

## ReferenceImporter

```python
class ReferenceImporter:
    # Supports Vancouver (numbered), author-year, DOI-only patterns
    VANCOUVER_PATTERN = r"^\s*\d+\.\s+(.+)"
    AUTHOR_YEAR_PATTERN = r"^([A-Z][a-z]+\s+[A-Z]{1,3}(?:,\s*[A-Z][a-z]+\s+[A-Z]{1,3})*)\s*\.\s*(.+?)\s*[\.\;]\s*(\d{4})"

    def extract_references(self, sections: list[Section]) -> list[ProtocolReference]:
        """
        1. Find reference section (last section matching 'references' keywords)
        2. Split into individual reference strings (by numbered list or double newline)
        3. Parse each: authors, title, journal, year, volume, pages
        4. Attempt DOI extraction (r'doi:\s*10\.\d{4}')
        """

    def verify_with_pubmed(self, refs: list[ProtocolReference]) -> list[ProtocolReference]:
        """
        For each ref: call PubMedVerifier.search(title=..., authors=..., year=...)
        Mark as verified (PMID assigned) or unverified
        """
```

---

## CLI Command Design

### New command: `hpw load-protocol`

```python
# cli.py additions

subparsers.add_parser("load-protocol", help="Load and extract protocol document")
# Arguments:
#   file_path (positional): path to protocol DOCX or PDF
#   --project: project name (required; creates project dir if not exists)
#   --no-refs: skip reference import
#   --output-dir: override default project dir
```

**Usage**:
```bash
hpw load-protocol protocol.docx --project "Asciminib CML Review"
hpw load-protocol protocol.pdf --project "SAPPHIRE" --no-refs
```

**Output**:
```
Loading protocol: protocol.docx
  ✓ Parsed 48 sections (DOCX)
  ✓ Background extracted → docs/drafts/introduction_seed.md
  ✓ Methods extracted   → docs/drafts/methods_seed.md
  ✓ SAP extracted       → docs/drafts/statistical_methods_seed.md
  ✓ Parameters saved    → data/protocol_params.json
  ✓ 43 references found → verifying with PubMed...
    38 verified (PMID assigned)
    5 unverified → literature/unverified_refs.txt
  ⚠ Missing SAP fields: [dropout_rate]
Done in 18.3s
```

---

## Phase 1 Integration

**File**: `phases/phase1_topic/topic_development.py`

Add `load_protocol()` method to `TopicDevelopmentManager`:

```python
def load_protocol(self, protocol_path: str) -> dict:
    """
    Called when user provides a protocol document at project init.
    1. Run ProtocolParser.load_and_extract()
    2. Auto-populate PICO fields from extraction:
       - Population: from eligibility criteria
       - Intervention: from treatment arm
       - Outcome: from primary endpoint
    3. Set self.study_type from protocol_params.json 'study_type'
    4. Return extraction summary for display
    """
```

---

## File Output Map

```
{project_dir}/
  docs/
    protocol/
      protocol.docx               ← original file (copied here)
    drafts/
      introduction_seed.md        ← Background + Objectives
      methods_seed.md             ← Design + Eligibility + Treatment + Assessments
      statistical_methods_seed.md ← SAP content
  data/
    protocol_extracted.json       ← full extraction cache (human-readable)
    protocol_params.json          ← structured params for CSA
  literature/
    references.json               ← PubMed-verified refs with PMIDs
    unverified_refs.txt           ← refs that failed PubMed lookup
```

---

## Error Handling

| Condition | Behavior |
|-----------|---------|
| Unsupported file type | Raise `ValueError` with supported formats list |
| PDF: text extraction fails | Attempt OCR; warn if pytesseract not installed |
| Section not found | Log warning; write empty seed section with `[NOT FOUND IN PROTOCOL]` |
| SAP: regex matches nothing | Set field to `None`; add to `missing_fields` |
| PubMed rate limit | Retry with exponential backoff (max 3 attempts); skip on failure |
| Project dir not writable | Raise `PermissionError` with path |

---

## Dependencies to Add

```
# requirements.txt additions
pdfplumber>=0.10.0
pdf2image>=1.16.0
pytesseract>=0.3.10   # optional; OCR for scanned PDFs
```

`pytesseract` requires system-level `tesseract-ocr`. Document in README:
```bash
# macOS
brew install tesseract
# Install to requirements as optional: pip install pytesseract
```

---

## Implementation Order (Do Phase)

1. `DocxParser` — section extraction from DOCX (python-docx)
2. `SectionExtractor` — keyword-based section categorization
3. `BackgroundExtractor` → `introduction_seed.md`
4. `MethodsExtractor` → `methods_seed.md` + reporting guideline detection
5. `SAPExtractor` → `statistical_methods_seed.md` + `protocol_params.json`
6. `PdfParser` — pdfplumber path + OCR fallback
7. `ReferenceImporter` → PubMed verification + `references.json`
8. `ProtocolParser` public API wrapper
9. CLI `load-protocol` command in `cli.py`
10. `TopicDevelopmentManager.load_protocol()` in phase1
11. `tools/__init__.py` — export `ProtocolParser`
