# Plan: NLM Enrichment — `_enrich_with_nlm()` via open-notebook REST API

**Feature**: `nlm-enrichment`
**Date**: 2026-03-05
**Status**: Plan
**Skill Affected**: hematology-paper-writer (HPW)
**Parent Feature**: csa-hpw-stats-pipeline (FR-09, previously deferred)

---

## Problem Statement

`StatisticalBridge.generate_results_prose()` produces disease-specific sentences that cite raw
statistics but lack guideline context. For example:

> "The ELN 2022 adverse-risk group comprised 29.6% of patients."

A guideline-enriched version would read:

> "The ELN 2022 adverse-risk group (TP53/RUNX1/ASXL1 mutations or complex karyotype)
> comprised 29.6% of patients."

`tools/notebooklm_integration.py` is currently a stub. Google NotebookLM has no public API
(Enterprise only). The open-notebook project provides a self-hosted alternative with a full
REST API at `:5055`.

---

## Goals

- Wire `_enrich_with_nlm(disease, stat_key)` to open-notebook REST API
- One-command bootstrap creates the Hematology Guidelines notebook and ingests source documents
- All enrichment is silent/optional — no exception ever propagates to the caller
- Enrichment appends a short parenthetical (≤80 chars) per prose sentence where a query template exists

---

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Notebook model | Code-managed bootstrap (`bootstrap_notebooks.py`) | Reproducible across machines; user runs once |
| Query strategy | Stateless `POST /api/search/ask/simple`, single notebook | Independent per-stat queries; no session overhead |
| Notebook scope | Single comprehensive Hematology Guidelines notebook | All guidelines (ELN, WHO, NIH, BOIN) in one notebook; vector search finds the right chunk |
| Question templates | `_ENRICHMENT_QUERIES` dict — `(disease, stat_key)` → question string | Finite, auditable, unit-testable |

---

## Functional Requirements

### FR-01: `bootstrap_notebooks.py` — one-time notebook setup

Runnable as `python bootstrap_notebooks.py`:

1. Reads `notebooklm_config.json` if it exists (skip if `notebook_id` already set and valid)
2. Creates a notebook via `POST /api/notebooks` with name "Hematology Guidelines"
3. Ingests curated guideline sources via `POST /api/sources`:
   - ELN 2022 AML risk stratification (public DOI URL or local PDF if present)
   - ELN 2020 CML recommendations
   - WHO 2022 haematological tumours (public URL)
   - NIH 2014 aGVHD/cGVHD consensus (public URL)
   - BOIN design paper (Liu & Yuan 2015)
4. Writes `notebooklm_config.json`:
   ```json
   {
     "base_url": "http://localhost:5055",
     "notebook_id": "<created_id>"
   }
   ```
5. Prints confirmation and source ingestion status

`notebooklm_config.json` is gitignored (user-specific; depends on local open-notebook instance).

### FR-02: `_ENRICHMENT_QUERIES` dict in `statistical_bridge.py`

Class-level dict mapping `(disease, stat_key)` → question string:

```python
_ENRICHMENT_QUERIES: Dict[Tuple[str, str], str] = {
    # AML
    ("aml", "eln_favorable_pct"): "What defines ELN 2022 favorable risk in AML?",
    ("aml", "eln_intermediate_pct"): "What defines ELN 2022 intermediate risk in AML?",
    ("aml", "eln_adverse_pct"): "What defines ELN 2022 adverse risk in AML?",
    ("aml", "ccr_rate"):  "What is composite complete response (cCR) per ELN 2022 in AML?",
    ("aml", "cr_rate"):   "What is complete remission (CR) definition in AML per ELN 2022?",
    ("aml", "cri_rate"):  "What is CRi definition per ELN 2022?",
    ("aml", "target_dlt_rate"): "What is the target DLT rate in BOIN dose-finding design?",
    # CML
    ("cml", "mmr_12mo"):  "What is major molecular response (MMR) per ELN 2020 in CML?",
    ("cml", "tfr_12mo"):  "What is treatment-free remission (TFR) per ELN 2020 in CML?",
    ("cml", "tfr_24mo"):  "What is the 24-month TFR milestone per ELN 2020?",
    ("cml", "sokal_high_pct"): "How is Sokal high-risk score defined in CML?",
    # HCT
    ("hct", "agvhd_grade2_4_rate"): "How is grade 2-4 acute GVHD graded per NIH 2014?",
    ("hct", "cgvhd_moderate_severe_rate"): "How is moderate-severe chronic GVHD defined per NIH 2014?",
    ("hct", "grfs_12mo"): "What is GVHD-free relapse-free survival (GRFS)?",
    # General
    ("aml", "ae_grade3plus_rate"): "How are CTCAE grade 3+ adverse events defined?",
    ("cml", "ae_grade3plus_rate"): "How are CTCAE grade 3+ adverse events defined?",
    ("hct", "ae_grade3plus_rate"): "How are CTCAE grade 3+ adverse events defined?",
}
```

### FR-03: `_enrich_with_nlm(disease, stat_key)` method

```python
def _enrich_with_nlm(self, disease: str, stat_key: str) -> str:
    """Return short guideline parenthetical (≤80 chars) or '' on any failure."""
```

Logic:
1. Look up `(disease, stat_key)` in `_ENRICHMENT_QUERIES` — return `""` if absent
2. Load `notebooklm_config.json` — return `""` if file absent
3. `POST /api/search/ask/simple` with `{"query": question, "notebook_id": id}`, timeout=5s
4. Extract answer text → `_extract_parenthetical(answer)` (first sentence ≤80 chars)
5. Return extracted phrase or `""` on any exception

### FR-04: `_load_nlm_config()` helper

Reads and caches `notebooklm_config.json`. Returns `None` if file absent or malformed.
Config path resolution: `Path(__file__).parent.parent / "notebooklm_config.json"`.

### FR-05: `_extract_parenthetical(answer)` helper

Extracts the most concise guideline phrase from the open-notebook answer:
- Take first sentence of answer
- Truncate to 80 chars at word boundary
- Strip leading articles ("The ", "A ", "An ")

### FR-06: Integration in `generate_results_prose()`

After each disease-specific prose sentence:
```python
phrase = self._enrich_with_nlm(disease, stat_key)
sentence = f"...({phrase})" if phrase else "..."
```

Only applied to sentences where a stat key maps to `_ENRICHMENT_QUERIES`.

### FR-07: Update `tools/notebooklm_integration.py`

Replace stub with thin wrapper around open-notebook REST API:
- `NotebookLMIntegration.ask(question, notebook_id)` → `str`
- Used internally by `_enrich_with_nlm()`; can also be used standalone

### FR-08: Tests (`tests/test_enrich_nlm.py`)

- `test_enrich_returns_empty_when_no_config` — config file absent → `""`
- `test_enrich_returns_empty_when_key_absent` — stat key not in `_ENRICHMENT_QUERIES` → `""`
- `test_enrich_returns_parenthetical_on_success` — mock HTTP 200 → phrase extracted
- `test_enrich_silent_on_timeout` — mock timeout → `""` (no exception)
- `test_enrich_silent_on_http_error` — mock 500 → `""` (no exception)
- `test_extract_parenthetical_truncates` — long answer → ≤80 chars
- `test_extract_parenthetical_strips_articles` — "The ELN..." → "ELN..."
- `test_prose_uses_enrichment_when_available` — integration: prose sentence includes parenthetical

---

## Implementation Phases

| Phase | Scope | Files |
|-------|-------|-------|
| 1 | Config + bootstrap | `bootstrap_notebooks.py`, `notebooklm_config.json` (gitignore) |
| 2 | Core enrichment logic | `tools/statistical_bridge.py`, `tools/notebooklm_integration.py` |
| 3 | Prose integration | `tools/statistical_bridge.py` — `generate_results_prose()` |
| 4 | Tests | `tests/test_enrich_nlm.py` |

---

## Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-1 | `python bootstrap_notebooks.py` creates notebook + writes `notebooklm_config.json` |
| AC-2 | `_enrich_with_nlm("aml", "eln_adverse_pct")` returns non-empty string when open-notebook running |
| AC-3 | Same call returns `""` when `notebooklm_config.json` absent (no exception) |
| AC-4 | Same call returns `""` on HTTP timeout (no exception) |
| AC-5 | AML prose sentence for `eln_adverse_pct` includes parenthetical when enrichment available |
| AC-6 | AML prose sentence for `eln_adverse_pct` is still valid when enrichment absent |
| AC-7 | All 8 tests in `test_enrich_nlm.py` pass |
| AC-8 | All 50 existing `test_statistical_bridge.py` tests still pass |

---

## Out of Scope

- Multi-notebook routing (single notebook covers all diseases)
- Streaming responses from open-notebook
- Caching enrichment results to disk
- Auto-starting open-notebook Docker stack

---

## Files Changed

| File | Change |
|------|--------|
| `bootstrap_notebooks.py` | New — one-time notebook setup script |
| `notebooklm_config.json` | New (gitignored) — written by bootstrap |
| `.gitignore` | Add `notebooklm_config.json` |
| `tools/statistical_bridge.py` | Add `_ENRICHMENT_QUERIES`, `_enrich_with_nlm()`, `_load_nlm_config()`, `_extract_parenthetical()`; update `generate_results_prose()` |
| `tools/notebooklm_integration.py` | Replace stub with open-notebook REST wrapper |
| `tests/test_enrich_nlm.py` | New — 8 unit tests |

---

## Dependencies

- open-notebook running at `http://localhost:5055` (Docker Compose)
- `requests` library (already in HPW `requirements.txt`)
- No new Python packages required
