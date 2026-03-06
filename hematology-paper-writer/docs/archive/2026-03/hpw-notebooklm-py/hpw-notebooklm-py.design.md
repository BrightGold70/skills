# Design: HPW NotebookLM-py Integration

**Feature:** `hpw-notebooklm-py`
**Phase:** Design
**Created:** 2026-03-05
**Plan:** `docs/01-plan/features/hpw-notebooklm-py.plan.md`

---

## Architecture Overview

Minimal surgical replacement of the stub in `tools/notebooklm_integration.py`. Two private
methods are replaced; all public interfaces remain identical. A new async helper bridges
the synchronous HPW codebase to the async `notebooklm-py` library via `asyncio.run()`.

```
[Public API - unchanged]
  query_classification() / query_gvhd() / query_therapeutic() / query_nomenclature()
       |
       v
  _execute_query(query: ReferenceQuery)   <-- sync wrapper (CHANGED)
       |
       v  asyncio.run()
  _async_execute_query(query)             <-- NEW async helper
       |
       v
  NotebookLMClient.from_storage()         <-- notebooklm-py cached auth
       |
       v
  client.chat.ask(notebook_id, text)      <-- real Google NotebookLM call
       |
       v
  NotebookLMResponse(answer, sources, confidence)   <-- unchanged dataclass
```

---

## Components

### 1. Config Loading (`__init__`)

Load real notebook IDs from `tools/notebooklm_config.json` at initialization.
If the file is absent, fall back to `REFERENCE_NOTEBOOKS` dict values (preserving
current behavior for anyone running without config).

```python
CONFIG_PATH = Path(__file__).parent / "notebooklm_config.json"

def __init__(self, reference_path=None):
    ...
    self._load_notebook_ids()

def _load_notebook_ids(self) -> None:
    if self.CONFIG_PATH.exists():
        config = json.loads(self.CONFIG_PATH.read_text())
        for notebook_type, notebook_id in config.items():
            if notebook_type in self.REFERENCE_NOTEBOOKS:
                self.REFERENCE_NOTEBOOKS[notebook_type]["notebook_id"] = notebook_id
```

### 2. Async Query Helper (`_async_execute_query`)

New private async method. Creates a fresh `NotebookLMClient` per call (stateless;
session persistence is deferred to Proposal #10).

```python
async def _async_execute_query(self, query: ReferenceQuery) -> NotebookLMResponse:
    notebook_id = self.REFERENCE_NOTEBOOKS[query.notebook_type]["notebook_id"]
    async with await NotebookLMClient.from_storage() as client:
        result = await client.chat.ask(notebook_id, query.query_text)
    return NotebookLMResponse(
        answer=result.answer,
        sources=[{"source": s.title or s.url or "N/A", "page": "N/A"}
                 for s in (result.sources or [])],
        confidence="high",
        session_id=self.active_sessions.get(query.notebook_type),
    )
```

### 3. Sync Wrapper (`_execute_query`)

Replace mock body with `asyncio.run()` bridge + error handling:

```python
def _execute_query(self, query: ReferenceQuery) -> NotebookLMResponse:
    try:
        response = asyncio.run(self._async_execute_query(query))
    except Exception as e:
        error_msg = str(e)
        if "auth" in error_msg.lower() or "credential" in error_msg.lower():
            raise RuntimeError(
                "NotebookLM authentication failed. Run: notebooklm auth login"
            ) from e
        elif "not found" in error_msg.lower() or "404" in error_msg:
            notebook_id = self.REFERENCE_NOTEBOOKS[query.notebook_type]["notebook_id"]
            raise ValueError(
                f"Notebook not found: {notebook_id}\n"
                f"Check tools/notebooklm_config.json for correct IDs."
            ) from e
        else:
            raise RuntimeError(
                f"NotebookLM query failed: {error_msg}\n"
                f"Fallback: use PubMedSearcher for '{query.query_text}'"
            ) from e
    # Log query (existing behavior preserved)
    self.query_history.append({
        "timestamp": datetime.now().isoformat(),
        "query": query.to_dict(),
        "response": response.to_dict(),
    })
    return response
```

### 4. Connection Verify (`initialize_notebook`)

Replace fake session simulation with real notebook existence check:

```python
def initialize_notebook(self, notebook_type: str) -> bool:
    if notebook_type not in self.REFERENCE_NOTEBOOKS:
        raise ValueError(f"Unknown notebook type: {notebook_type}")
    config = self.REFERENCE_NOTEBOOKS[notebook_type]
    notebook_id = config["notebook_id"]

    async def _verify():
        async with await NotebookLMClient.from_storage() as client:
            await client.notebooks.get(notebook_id)

    try:
        asyncio.run(_verify())
    except Exception as e:
        raise ValueError(
            f"Cannot initialize '{config['name']}' (id={notebook_id}): {e}\n"
            f"Verify the ID in tools/notebooklm_config.json"
        ) from e

    session_id = f"session_{notebook_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    self.active_sessions[notebook_type] = session_id
    print(f"Initialized '{config['name']}' notebook: {session_id}")
    return True
```

---

## Data Models

No changes to existing dataclasses. The `notebooklm-py` response fields map as:

| `notebooklm-py` result field | `NotebookLMResponse` field | Notes |
|------------------------------|---------------------------|-------|
| `result.answer` | `answer` | Direct mapping |
| `result.sources[].title` or `.url` | `sources[].source` | First non-None value |
| hardcoded `"high"` | `confidence` | Library provides no confidence score |
| from `active_sessions` | `session_id` | Unchanged behavior |

---

## New Files

### `tools/notebooklm_config.json` (gitignored)

```json
{
  "classification": "REPLACE_WITH_REAL_NOTEBOOK_ID",
  "gvhd": "REPLACE_WITH_REAL_NOTEBOOK_ID",
  "therapeutic": "REPLACE_WITH_REAL_NOTEBOOK_ID",
  "nomenclature": "REPLACE_WITH_REAL_NOTEBOOK_ID"
}
```

User fills in real Google NotebookLM notebook IDs before first run.

---

## Dependency Changes

### `tools/requirements.txt`
Add one line:
```
notebooklm-py[browser]>=0.1.0
```

### `.gitignore` (HPW root, create if absent)
Add:
```
tools/notebooklm_config.json
```

### One-time setup (user runs once):
```bash
pip install "notebooklm-py[browser]"
playwright install chromium
notebooklm auth login   # opens browser for Google auth
```

---

## Error Handling

| Scenario | Exception raised | Message |
|----------|-----------------|---------|
| Not authenticated | `RuntimeError` | "Run: notebooklm auth login" |
| Notebook ID wrong / not found | `ValueError` | "Check tools/notebooklm_config.json" |
| Network / timeout | `RuntimeError` | "Fallback: use PubMedSearcher" |
| Unknown notebook_type | `ValueError` | (existing behavior, unchanged) |
| Config file missing | Silent fallback | Uses placeholder IDs from REFERENCE_NOTEBOOKS |

---

## Testing Strategy

**Manual verification** (via existing `__main__` block):
```bash
cd hematology-paper-writer
python tools/notebooklm_integration.py
# Expected: real answer from NotebookLM, not "[MCP Placeholder]"
```

**Regression check** (no breaking changes):
- `ResearchIntelligenceEngine().validate_research_topic("AML", "classification")` — must not raise
- `get_quick_reference("classification", "AML with NPM1")` — must return non-placeholder string
- `get_notebook_status()` — must still return dict with 4 keys

**Error path check**:
- Rename config file → must print warning and not crash on import
- Wrong notebook ID in config → `initialize_notebook()` must raise `ValueError` with clear message

---

## Implementation Order

```
1. tools/requirements.txt       — add notebooklm-py[browser]
2. .gitignore                   — add tools/notebooklm_config.json
3. tools/notebooklm_config.json — create with placeholder values
4. notebooklm_integration.py    — add import: asyncio, NotebookLMClient
5. notebooklm_integration.py    — add _load_notebook_ids() + call in __init__
6. notebooklm_integration.py    — add _async_execute_query()
7. notebooklm_integration.py    — replace _execute_query() body
8. notebooklm_integration.py    — replace initialize_notebook() body
9. Manual test via __main__
```
