# Plan: HPW NotebookLM-py Integration

**Feature:** `hpw-notebooklm-py`
**Phase:** Plan
**Created:** 2026-03-05
**Status:** Planning

---

## 1. Overview

Replace the stub implementation in `tools/notebooklm_integration.py` with real calls to the
[`notebooklm-py`](https://github.com/teng-lin/notebooklm-py) library. The current module
has a well-designed public interface but `_execute_query()` always returns mock data.
This plan makes the module functional with zero breaking changes to callers.

**Prerequisite for:** Proposal #10 (NotebookLM cross-phase session persistence) from `hpw-improvements-batch2`.

---

## 2. Problem Statement

`NotebookLMIntegration._execute_query()` returns hardcoded mock responses. All 4 reference
notebooks (classification, gvhd, therapeutic, nomenclature) have real counterparts in Google
NotebookLM with PDFs already uploaded, but the code never calls them. The `notebook_id` fields
in `REFERENCE_NOTEBOOKS` are all the same placeholder value (`f47cebf8-...`).

As a result:
- Phase 0 (Research Intelligence) produces no real answers
- `check_nomenclature_compliance()` returns vacuous corrections
- `verify_entity_classification()` never queries WHO 2022 / ICC 2022 content
- Data Source Priority rule ("NotebookLM first") is effectively bypassed

---

## 3. Scope

### In Scope
- Replace `_execute_query()` with real async `notebooklm-py` call via `asyncio.run()`
- Replace `initialize_notebook()` stub with connection verification
- Add `tools/notebooklm_config.json` for real notebook IDs (gitignored)
- Add `notebooklm-py[browser]` to `tools/requirements.txt`
- Add `_async_execute_query()` private async helper
- Add error handling for auth failure, network error, notebook-not-found

### Out of Scope
- Cross-phase session persistence (Proposal #10 — separate feature)
- Changing any public method signatures
- Changing `ResearchIntelligenceEngine` or any phase module
- Podcast/video/quiz generation features of `notebooklm-py`

---

## 4. Requirements

### R1 — Config loading
- On `__init__`, load notebook IDs from `tools/notebooklm_config.json` if present
- Fall back to `REFERENCE_NOTEBOOKS[type]["notebook_id"]` values if config absent
- Config file format:
  ```json
  {
    "classification": "<google-notebooklm-notebook-id>",
    "gvhd": "<google-notebooklm-notebook-id>",
    "therapeutic": "<google-notebooklm-notebook-id>",
    "nomenclature": "<google-notebooklm-notebook-id>"
  }
  ```

### R2 — Real query execution
- `_execute_query(query)` calls `asyncio.run(self._async_execute_query(query))`
- `_async_execute_query(query)` uses `NotebookLMClient.from_storage()` (cached credentials)
- Calls `client.chat.ask(notebook_id, query.query_text)`
- Maps response to `NotebookLMResponse` dataclass (answer, sources, confidence)

### R3 — Error handling
- `AuthenticationError`: raise with clear message ("Run: notebooklm auth login")
- `NetworkError` / timeout: raise `RuntimeError` with fallback suggestion ("Use PubMed fallback")
- Notebook not found: raise `ValueError` with notebook_id and config file hint

### R4 — initialize_notebook() behavior
- Verify the notebook_id exists by calling `client.notebooks.get(notebook_id)`
- On success: store session marker (existing behavior preserved)
- On failure: raise `ValueError` with actionable message

### R5 — Backward compatibility
- All public method signatures unchanged
- `NotebookLMResponse`, `ReferenceQuery`, `ClassificationEntity` dataclasses unchanged
- `ResearchIntelligenceEngine` unchanged
- `get_notebook_status()`, `generate_setup_report()`, `export_query_history()` unchanged

### R6 — Dependency
- Add to `tools/requirements.txt`: `notebooklm-py[browser]>=0.1.0`
- One-time setup: `notebooklm auth login` (browser-based, caches credentials)

---

## 5. Files Changed

| File | Change |
|------|--------|
| `tools/notebooklm_integration.py` | Replace `_execute_query()` + `initialize_notebook()` bodies; add `_async_execute_query()`; add config loading in `__init__` |
| `tools/notebooklm_config.json` | New file (gitignored) — real notebook IDs |
| `tools/requirements.txt` | Add `notebooklm-py[browser]>=0.1.0` |
| `.gitignore` (root HPW) | Add `tools/notebooklm_config.json` entry if not present |

---

## 6. Implementation Order

```
Step 1: Add notebooklm-py to tools/requirements.txt
Step 2: Add notebooklm_config.json to .gitignore
Step 3: Create tools/notebooklm_config.json (user fills in real IDs)
Step 4: Add config loading to __init__
Step 5: Add _async_execute_query() with real client call + response mapping
Step 6: Replace _execute_query() body with asyncio.run() bridge
Step 7: Replace initialize_notebook() with connection verify
Step 8: Add error handling (auth, network, not-found)
Step 9: Manual test via __main__ block
```

---

## 7. Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| `notebooklm-py` uses undocumented Google APIs that may change | Medium | Pin version; monitor upstream changelog |
| `asyncio.run()` fails in nested event loop | Low | HPW CLI is fully synchronous; not a concern |
| Google rate limiting (50 queries/day free tier) | Medium | Already noted; Proposal #10 session persistence will reduce redundant queries |
| Auth credentials expire | Low | `from_storage()` handles refresh; clear error message on failure |

---

## 8. Success Criteria

| Criterion | Done When |
|-----------|-----------|
| `query_classification("AML with NPM1")` returns real NotebookLM answer | Yes |
| `query_gvhd("diagnosis", "skin")` returns NIH cGVHD criteria from PDF | Yes |
| All 4 notebooks return real answers (not "[MCP Placeholder]") | Yes |
| Calling with no `notebooklm_config.json` raises clear error with instructions | Yes |
| `ResearchIntelligenceEngine` callers work without any changes | Yes |

---

## 9. Notes

- `notebooklm-py` is an **unofficial** library using undocumented Google APIs.
  Suitable for research and personal use; monitor for breakage after Google updates.
- One-time auth setup required: `pip install "notebooklm-py[browser]" && playwright install chromium && notebooklm auth login`
- This feature is a **prerequisite** for Proposal #10 (session persistence). Do not
  implement #10 until this plan is complete and verified.
