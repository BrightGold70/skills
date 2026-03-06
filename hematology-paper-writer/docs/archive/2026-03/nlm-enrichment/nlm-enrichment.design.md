# Design: NLM Enrichment — `_enrich_with_nlm()` via open-notebook REST API

**Feature**: `nlm-enrichment`
**Date**: 2026-03-05
**Status**: Design
**Plan**: `docs/01-plan/features/nlm-enrichment.plan.md`

---

## Architecture Overview

```
StatisticalBridge.generate_results_prose()
  │
  ├─ build prose sentence (existing)
  │
  └─ _enrich_with_nlm(disease, stat_key)
       │
       ├─ lookup _ENRICHMENT_QUERIES[(disease, stat_key)] → question
       ├─ _load_nlm_config() → {base_url, notebook_id} | None
       ├─ NotebookLMIntegration.ask(question, notebook_id) → answer
       └─ _extract_parenthetical(answer) → ≤80 char phrase
            │
            └─ POST /api/search/ask/simple (open-notebook REST)
```

Failure at any step → return `""` silently. No exception ever surfaces to caller.

---

## Module Interfaces

### 1. `tools/notebooklm_integration.py` — Replace stub

**Replaces**: stub that imports `from notebooklm import NotebookLMClient` (not installed)

```python
"""
NotebookLM Integration — open-notebook REST API backend.
Replaces the notebooklm-py stub with a thin HTTP wrapper.
"""

import requests
from typing import Optional


class NotebookLMIntegration:
    """
    Thin wrapper around the open-notebook REST API.
    Requires open-notebook running at base_url (default: http://localhost:5055).
    All methods return empty string / None on any failure (never raise).
    """

    def __init__(self, base_url: str = "http://localhost:5055"):
        self.base_url = base_url.rstrip("/")
        self._session = requests.Session()

    def ask(self, question: str, notebook_id: str, timeout: int = 5) -> str:
        """
        POST /api/search/ask/simple
        Returns the answer string, or "" on any failure.
        """
        try:
            resp = self._session.post(
                f"{self.base_url}/api/search/ask/simple",
                json={"query": question, "notebook_id": notebook_id},
                timeout=timeout,
            )
            resp.raise_for_status()
            return resp.json().get("answer", "")
        except Exception:
            return ""

    def create_notebook(self, name: str, description: str = "") -> Optional[str]:
        """
        POST /api/notebooks
        Returns notebook_id string, or None on failure.
        """
        try:
            resp = self._session.post(
                f"{self.base_url}/api/notebooks",
                json={"name": name, "description": description},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json().get("id")
        except Exception:
            return None

    def add_source_url(self, notebook_id: str, url: str) -> bool:
        """
        POST /api/sources (URL ingestion)
        Returns True on success, False on failure.
        """
        try:
            resp = self._session.post(
                f"{self.base_url}/api/sources",
                data={"url": url, "notebook_id": notebook_id, "process_async": "false"},
                timeout=30,
            )
            resp.raise_for_status()
            return True
        except Exception:
            return False

    def add_source_file(self, notebook_id: str, file_path: str) -> bool:
        """
        POST /api/sources (file upload)
        Returns True on success, False on failure.
        """
        try:
            with open(file_path, "rb") as f:
                resp = self._session.post(
                    f"{self.base_url}/api/sources",
                    data={"notebook_id": notebook_id},
                    files={"file": (file_path, f, "application/pdf")},
                    timeout=60,
                )
            resp.raise_for_status()
            return True
        except Exception:
            return False

    def health_check(self) -> bool:
        """Returns True if open-notebook API is reachable."""
        try:
            resp = self._session.get(f"{self.base_url}/api/notebooks", timeout=3)
            return resp.status_code < 500
        except Exception:
            return False
```

**Removed from stub**: `ReferenceQuery`, `NotebookLMResponse`, `ClassificationEntity`, all async methods, all multi-notebook routing logic, `notebooklm-py` import.

---

### 2. `tools/statistical_bridge.py` — Additions

#### 2a. `_ENRICHMENT_QUERIES` (class-level constant)

```python
_ENRICHMENT_QUERIES: Dict[Tuple[str, str], str] = {
    # AML — ELN 2022
    ("aml", "eln_favorable_pct"):   "What defines ELN 2022 favorable risk in AML?",
    ("aml", "eln_intermediate_pct"):"What defines ELN 2022 intermediate risk in AML?",
    ("aml", "eln_adverse_pct"):     "What defines ELN 2022 adverse risk in AML?",
    ("aml", "ccr_rate"):            "What is composite complete response (cCR) per ELN 2022?",
    ("aml", "cr_rate"):             "What is complete remission (CR) per ELN 2022 in AML?",
    ("aml", "cri_rate"):            "What is CRi (CR with incomplete count recovery) per ELN 2022?",
    ("aml", "target_dlt_rate"):     "What is the target DLT rate in BOIN dose-finding?",
    ("aml", "orr"):                 "What is overall response rate definition in AML per ELN 2022?",
    # CML — ELN 2020
    ("cml", "mmr_12mo"):            "What is major molecular response (MMR) per ELN 2020 in CML?",
    ("cml", "tfr_12mo"):            "What is treatment-free remission (TFR) per ELN 2020 in CML?",
    ("cml", "tfr_24mo"):            "What is the 24-month TFR milestone per ELN 2020 in CML?",
    ("cml", "sokal_high_pct"):      "How is Sokal high-risk score defined in CML?",
    # HCT — NIH 2014
    ("hct", "agvhd_grade2_4_rate"): "How is grade 2-4 acute GVHD graded per NIH 2014 consensus?",
    ("hct", "agvhd_grade3_4_rate"): "How is grade 3-4 acute GVHD defined per NIH 2014?",
    ("hct", "cgvhd_moderate_severe_rate"): "How is moderate-severe chronic GVHD defined per NIH 2014?",
    ("hct", "grfs_12mo"):           "What is GVHD-free relapse-free survival (GRFS)?",
    # Cross-disease
    ("aml", "ae_grade3plus_rate"):  "How are CTCAE grade 3 or higher adverse events classified?",
    ("cml", "ae_grade3plus_rate"):  "How are CTCAE grade 3 or higher adverse events classified?",
    ("hct", "ae_grade3plus_rate"):  "How are CTCAE grade 3 or higher adverse events classified?",
    ("mds", "ae_grade3plus_rate"):  "How are CTCAE grade 3 or higher adverse events classified?",
}
```

#### 2b. `_load_nlm_config()` — private method

```python
def _load_nlm_config(self) -> Optional[Dict[str, str]]:
    """
    Load notebooklm_config.json from HPW root.
    Returns dict with 'base_url' and 'notebook_id', or None if absent/malformed.
    Caches result after first call.
    """
    if hasattr(self, "_nlm_config_cache"):
        return self._nlm_config_cache
    config_path = Path(__file__).parent.parent / "notebooklm_config.json"
    try:
        data = json.loads(config_path.read_text())
        if "notebook_id" in data and "base_url" in data:
            self._nlm_config_cache = data
            return data
    except Exception:
        pass
    self._nlm_config_cache = None
    return None
```

#### 2c. `_extract_parenthetical(answer)` — private static method

```python
@staticmethod
def _extract_parenthetical(answer: str) -> str:
    """
    Extract a concise guideline phrase (≤80 chars) from open-notebook answer.
    Takes first sentence, strips leading articles, truncates at word boundary.
    """
    if not answer:
        return ""
    # Take first sentence
    sentence = answer.split(".")[0].strip()
    # Strip leading articles
    for article in ("The ", "A ", "An "):
        if sentence.startswith(article):
            sentence = sentence[len(article):]
            break
    # Truncate to 80 chars at word boundary
    if len(sentence) <= 80:
        return sentence
    truncated = sentence[:80].rsplit(" ", 1)[0]
    return truncated
```

#### 2d. `_enrich_with_nlm(disease, stat_key)` — private method

```python
def _enrich_with_nlm(self, disease: str, stat_key: str) -> str:
    """
    Return a short guideline parenthetical (≤80 chars) for the given stat,
    or "" if not available (config absent, key not in queries, any HTTP error).
    Never raises an exception.
    """
    question = self._ENRICHMENT_QUERIES.get((disease, stat_key))
    if not question:
        return ""
    cfg = self._load_nlm_config()
    if not cfg:
        return ""
    try:
        nlm = NotebookLMIntegration(base_url=cfg["base_url"])
        answer = nlm.ask(question, notebook_id=cfg["notebook_id"])
        return self._extract_parenthetical(answer)
    except Exception:
        return ""
```

#### 2e. Integration in `generate_results_prose()`

For each disease-specific prose sentence that references a stat key present in `_ENRICHMENT_QUERIES`:

```python
# Example: AML ELN adverse risk sentence
phrase = self._enrich_with_nlm("aml", "eln_adverse_pct")
if phrase:
    sentences.append(
        f"ELN 2022 adverse-risk disease was identified in {pct}% of patients ({phrase})."
    )
else:
    sentences.append(
        f"ELN 2022 adverse-risk disease was identified in {pct}% of patients."
    )
```

Enrichment applied to sentences for: all `_ENRICHMENT_QUERIES` keys present in the manifest.

---

### 3. `bootstrap_notebooks.py` — New file (HPW root)

```python
#!/usr/bin/env python3
"""
bootstrap_notebooks.py — One-time setup for open-notebook Hematology Guidelines notebook.

Usage:
    python bootstrap_notebooks.py [--base-url http://localhost:5055]
    python bootstrap_notebooks.py --check   # verify existing config
"""

GUIDELINE_SOURCES = [
    # Public DOI / URL sources for guideline documents
    # Users can supplement with local PDFs (passed as --local-pdf path)
    {
        "name": "ELN 2022 AML Risk Stratification",
        "url": "https://doi.org/10.1182/blood.2022016867",
    },
    {
        "name": "ELN 2020 CML Recommendations",
        "url": "https://doi.org/10.1038/s41375-020-0776-2",
    },
    {
        "name": "NIH 2014 aGVHD Consensus",
        "url": "https://doi.org/10.1016/j.bbmt.2014.12.001",
    },
    {
        "name": "NIH 2014 cGVHD Consensus",
        "url": "https://doi.org/10.1016/j.bbmt.2014.12.010",
    },
    {
        "name": "BOIN Design — Liu & Yuan 2015",
        "url": "https://doi.org/10.1111/biom.12353",
    },
]

CONFIG_PATH = Path(__file__).parent / "notebooklm_config.json"
```

**Flow**:
1. Parse CLI args (`--base-url`, `--check`, `--local-pdf`)
2. `--check`: load config, run `health_check()`, print status
3. Create notebook via `NotebookLMIntegration.create_notebook("Hematology Guidelines")`
4. For each source in `GUIDELINE_SOURCES`: call `add_source_url()`
5. For each `--local-pdf`: call `add_source_file()`
6. Write `notebooklm_config.json`
7. Print summary table (source name, ingestion status)

---

### 4. `notebooklm_config.json` (gitignored)

```json
{
  "base_url": "http://localhost:5055",
  "notebook_id": "<uuid-from-bootstrap>"
}
```

Added to `.gitignore`: `notebooklm_config.json`

---

### 5. `tests/test_enrich_nlm.py`

Uses `unittest.mock.patch` to mock `requests.Session.post`:

| Test | Mock | Assertion |
|------|------|-----------|
| `test_enrich_no_config` | — (config file absent) | returns `""` |
| `test_enrich_key_absent` | — | returns `""` for unknown stat key |
| `test_enrich_success` | 200 + `{"answer": "ELN 2022 adverse risk includes TP53..."}` | returns ≤80 char phrase |
| `test_enrich_timeout` | raises `requests.Timeout` | returns `""` |
| `test_enrich_http_500` | raises `requests.HTTPError` | returns `""` |
| `test_extract_truncates` | — | 100-char input → ≤80 chars at word boundary |
| `test_extract_strips_article` | — | "The ELN..." → "ELN..." |
| `test_prose_with_enrichment` | 200 + answer | prose sentence contains parenthetical |

---

## Data Flow

```
notebooklm_config.json
        │
        ▼
_load_nlm_config() ──► cached Dict or None
        │
        ▼
_enrich_with_nlm(disease, stat_key)
        │
        ├─ _ENRICHMENT_QUERIES[(disease, stat_key)] → question str
        │
        ├─ NotebookLMIntegration(base_url)
        │         └─ POST /api/search/ask/simple
        │              body: {query, notebook_id}
        │              response: {answer: "..."}
        │
        └─ _extract_parenthetical(answer) → str ≤80 chars
                   └─ injected into prose sentence
```

---

## Error Handling Matrix

| Failure point | Behavior |
|---------------|----------|
| `notebooklm_config.json` absent | `_load_nlm_config()` returns `None` → `""` |
| `notebook_id` not in config | `_load_nlm_config()` returns `None` → `""` |
| open-notebook not running | `requests.ConnectionError` caught → `""` |
| HTTP timeout (>5s) | `requests.Timeout` caught → `""` |
| HTTP 4xx/5xx | `raise_for_status()` → `HTTPError` caught → `""` |
| Answer is empty string | `_extract_parenthetical("")` → `""` |
| stat_key not in `_ENRICHMENT_QUERIES` | early return `""` |
| Any unexpected exception | outer `except Exception` → `""` |

---

## Implementation Order

1. **`tools/notebooklm_integration.py`** — Replace stub (clean slate; existing imports removed)
2. **`tools/statistical_bridge.py`** — Add `_ENRICHMENT_QUERIES`, `_load_nlm_config()`, `_extract_parenthetical()`, `_enrich_with_nlm()`; add `Tuple` to imports
3. **`tools/statistical_bridge.py`** — Update `generate_results_prose()` to call `_enrich_with_nlm()` for applicable stat keys
4. **`bootstrap_notebooks.py`** — New file at HPW root
5. **`.gitignore`** — Add `notebooklm_config.json`
6. **`tests/test_enrich_nlm.py`** — 8 tests with mocked HTTP

---

## Test Strategy

All 8 `TestEnrichNlm` tests use `tmp_path` fixture to write a mock `notebooklm_config.json`
and `unittest.mock.patch("requests.Session.post")` to control HTTP responses.

No live open-notebook instance required for tests. `test_prose_with_enrichment` patches
`StatisticalBridge._enrich_with_nlm` directly to return a known phrase and asserts the
prose sentence contains it.

Existing 50 tests in `test_statistical_bridge.py` continue to pass because:
- `_load_nlm_config()` returns `None` when `notebooklm_config.json` is absent (no config in tmp_path fixtures)
- `_enrich_with_nlm()` returns `""` → prose sentences unchanged in all existing fixtures
