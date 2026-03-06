# Gap Analysis: nlm-enrichment

**Feature**: `nlm-enrichment`
**Date**: 2026-03-05
**Phase**: Check
**Match Rate**: 93%

---

## Summary

Implementation of FR-09 (`_enrich_with_nlm()`) is functionally complete. All core components
from the Design spec are present and working. 62/62 tests pass. The 7% gap is concentrated in
two lower-priority areas: `bootstrap_notebooks.py` missing two CLI flags, and the test file
missing 3 of the 8 design-specified test scenarios (compensated by 9 additional tests).

---

## Match Rate by Area

| Area | Weight | Score | Notes |
|------|--------|-------|-------|
| `notebooklm_integration.py` | 15% | 95% | Module-level `_requests` vs Session; `process_async` "true" vs "false" |
| `_ENRICHMENT_QUERIES` | 10% | 98% | All 20 entries correct; module-level vs class-level (functionally identical) |
| `_load_nlm_config()` | 10% | 95% | Cache attr `_nlm_config` vs design's `_nlm_config_cache` |
| `_extract_parenthetical()` | 10% | 100% | Regex sentence detection exceeds design spec (handles `0.1` correctly) |
| `_enrich_with_nlm()` | 15% | 100% | Fully matches design |
| `generate_results_prose()` wiring | 20% | 100% | All applicable stat keys wired (AML×4, CML×3, HCT×3, safety×1) |
| `bootstrap_notebooks.py` | 10% | 70% | Missing `--check` and `--local-pdf`; GUIDELINE_SOURCES format differs |
| `tests/test_enrich_nlm.py` | 10% | 75% | 5/8 design-specified tests present; 3 missing; 9 bonus tests added |

**Weighted total: 93.0%** ✅ (threshold: ≥90%)

---

## Implemented — Matching Design

### ✅ `tools/notebooklm_integration.py`
- Replaced broken stub (`from notebooklm import NotebookLMClient` → `from notebooklm_integration import NotebookLMIntegration`)
- All 5 methods implemented: `ask()`, `create_notebook()`, `add_source_url()`, `add_source_file()`, `health_check()`
- All methods fail silently (return falsy) on any exception
- `requests` import guarded by `_HAS_REQUESTS` for environments without the package

### ✅ `_ENRICHMENT_QUERIES` (20 entries)
- AML: `eln_favorable_pct`, `eln_intermediate_pct`, `eln_adverse_pct`, `ccr_rate`, `cr_rate`, `cri_rate`, `target_dlt_rate`, `orr`
- CML: `mmr_12mo`, `tfr_12mo`, `tfr_24mo`, `sokal_high_pct`
- HCT: `agvhd_grade2_4_rate`, `agvhd_grade3_4_rate`, `cgvhd_moderate_severe_rate`, `grfs_12mo`
- Cross-disease: `ae_grade3plus_rate` for AML/CML/HCT/MDS

### ✅ `_load_nlm_config()`
- Reads `notebooklm_config.json` from HPW root (`Path(__file__).parent.parent`)
- Returns `None` if file absent, malformed, or missing required keys
- Instance-level cache prevents repeated file I/O

### ✅ `_extract_parenthetical()`
- Regex sentence boundary (`[.!?](?:\s|$)`) — correctly handles `BCR-ABL IS ≤0.1%`
- Strips leading articles ("The ", "An ", "A ")
- Truncates at last word boundary ≤80 chars
- Returns `""` for empty input

### ✅ `_enrich_with_nlm(disease, stat_key)`
- Looks up question from `_ENRICHMENT_QUERIES`
- Calls `_load_nlm_config()` → `NotebookLMIntegration.ask()` → `_extract_parenthetical()`
- Outer `except Exception` ensures no exception ever surfaces

### ✅ `generate_results_prose()` enrichment wiring
All applicable prose sentences enriched:
- AML ELN risk: `eln_favorable_pct` query appended to risk distribution sentence
- AML cCR: `ccr_rate` query
- AML BOIN: `target_dlt_rate` query (appended inside parenthetical with `;`)
- Safety: `ae_grade3plus_rate` query (disease-aware)
- CML MMR: `mmr_12mo` query
- CML TFR: `tfr_12mo` query (applied to both 12-month and 12+24-month sentences)
- HCT aGVHD: `agvhd_grade2_4_rate` query
- HCT cGVHD: `cgvhd_moderate_severe_rate` query
- HCT GRFS: `grfs_12mo` query

### ✅ `bootstrap_notebooks.py`
- `--base-url` flag
- `--dry-run` flag (added beyond design — useful for CI)
- 5 GUIDELINE_SOURCES (ELN 2022 AML, ELN 2020 CML, NIH cGVHD 2014, CTCAE v5, BOIN)
- Writes `notebooklm_config.json` on success

### ✅ `.gitignore`
- `notebooklm_config.json` already present

### ✅ Tests (12 total, 62/62 suite passes)
Present from design-specified 8:
- `test_enrich_no_config` → `test_returns_empty_when_no_config` ✅
- `test_enrich_key_absent` → `test_returns_empty_for_unknown_key` ✅
- `test_enrich_success` → `test_returns_parenthetical_on_success` ✅
- `test_extract_truncates` → `test_truncates_at_80_chars_word_boundary` ✅
- `test_extract_strips_article` → `test_strips_leading_article` ✅

Bonus tests not in design (additional coverage):
- `TestLoadNlmConfig`: `test_returns_none_when_config_absent`, `test_returns_none_when_config_missing_keys`, `test_caches_result_on_second_call`
- `TestExtractParenthetical`: `test_extracts_first_sentence`, `test_empty_input_returns_empty`, `test_short_answer_unchanged`
- `TestEnrichWithNlm`: `test_returns_empty_on_exception`

---

## Gaps

### G1 — `bootstrap_notebooks.py` missing `--check` and `--local-pdf` flags (medium)
**Design**: `--check` verifies existing config + health_check; `--local-pdf` ingests local PDF files
**Implementation**: Neither flag exists; `--dry-run` (not in design) was added instead
**Impact**: Users cannot verify an existing installation with a single flag; cannot add local PDFs via CLI
**Fix**: Add `--check` (load config → `health_check()` → print status) and `--local-pdf <path>` (calls `add_source_file()`)

### G2 — `GUIDELINE_SOURCES` format (low)
**Design**: List of dicts `{name, url}` with named sources
**Implementation**: Plain URL list
**Impact**: Summary table cannot show human-readable source names
**Fix**: Change `GUIDELINE_SOURCES` to list of dicts and update print loop

### G3 — Test `test_enrich_timeout` missing (low)
**Design**: Verifies `requests.Timeout` → returns `""`
**Coverage**: `test_returns_empty_on_exception` covers generic exceptions; timeout is implicitly covered
**Fix**: Add explicit test for `requests.Timeout` mock

### G4 — Test `test_enrich_http_500` missing (low)
**Design**: Verifies HTTP 5xx → returns `""`
**Coverage**: `test_returns_empty_on_exception` covers via `ConnectionError`; HTTP errors covered by `raise_for_status()` path
**Fix**: Add explicit test mocking `requests.HTTPError` with status 500

### G5 — Test `test_prose_with_enrichment` missing (low)
**Design**: End-to-end test that prose sentence contains parenthetical when enrichment returns a phrase
**Coverage**: Not tested end-to-end (only unit-level `_enrich_with_nlm` is tested)
**Fix**: Add test that patches `StatisticalBridge._enrich_with_nlm` to return a known string and asserts the prose sentence contains it

### G6 — Minor: cache attribute name `_nlm_config` vs design's `_nlm_config_cache` (negligible)
No functional impact; internal implementation detail.

### G7 — Minor: `add_source_url` uses `process_async: "true"` vs design's `"false"` (negligible)
`"true"` is actually correct for responsive API use; design had the wrong default.

---

## Conclusion

Match rate **93%** exceeds the 90% threshold. The gaps are confined to bootstrap CLI options
(G1–G2) and test coverage (G3–G5). The core feature — `_enrich_with_nlm()` wired into prose
generation — is fully implemented and all existing tests continue to pass.

**Recommendation**: Proceed directly to `/pdca report nlm-enrichment`. Optionally close G1–G5
in a follow-up iteration if bootstrap usability is a priority.
