# Design: HPW + CSA Unified UI v2

**Feature**: `hpw-csa-unified-ui-v2`
**Phase**: Design
**Created**: 2026-03-06
**Depends on**: `hpw-csa-unified-ui` (completed)

---

## 1. File Inventory

### Files to Create

| File | Purpose |
|------|---------|
| `ui/components/csa/__init__.py` | Export `DocumentsTab`, `PipelineTab`, `AnalysisTab` |

### Files to Move + Adapt

| Source | Destination | Key Changes |
|--------|-------------|-------------|
| `csa-ui/components/documents_tab.py` | `ui/components/csa/documents_tab.py` | Fix imports |
| `csa-ui/components/pipeline_tab.py` | `ui/components/csa/pipeline_tab.py` | Fix imports |
| `csa-ui/components/analysis_tab.py` | `ui/components/csa/analysis_tab.py` | Fix imports + session write |
| `csa-ui/script_registry.json` | `ui/script_registry.json` | No content change |

### Files to Modify

| File | Changes |
|------|---------|
| `ui/app.py` | Add top-level `st.tabs()`; import CSA components |
| `ui/components/csa_badge.py` | Remove `@st.cache_data(ttl=10)`; read session state only |
| `ui/components/log_stream.py` | Add `run_with_log_csa = run_with_log` alias |

### Files to Delete

| File | Reason |
|------|--------|
| `csa-ui/app.py` | Retired — functionality absorbed |
| `csa-ui/config.py` | Absorbed into HPW `ui_config.json` defaults |
| `csa-ui/log_runner.py` | Alias added to `log_stream.py` |
| `csa-ui/components/project_selector.py` | Replaced by HPW sidebar project selection |
| `csa-ui/components/__init__.py` | No longer needed |

---

## 2. Detailed Component Changes

### 2.1 `ui/components/csa/__init__.py` (NEW)

```python
from .documents_tab import DocumentsTab
from .pipeline_tab import PipelineTab
from .analysis_tab import AnalysisTab

__all__ = ["DocumentsTab", "PipelineTab", "AnalysisTab"]
```

---

### 2.2 `ui/components/csa/documents_tab.py` (MOVED + ADAPTED)

**Import changes only** — no logic changes:

```python
# Before (csa-ui/):
from log_runner import run_with_log_csa

# After (ui/components/csa/):
from components.log_stream import run_with_log as run_with_log_csa
```

**`_REGISTRY_PATH` update**:
```python
# Before:
_REGISTRY_PATH = Path(__file__).parent.parent / "script_registry.json"

# After:
_REGISTRY_PATH = Path(__file__).parent.parent.parent / "script_registry.json"
# i.e. ui/script_registry.json
```

**`project_dir` source**: No change — still passed as constructor arg from `app.py`.

---

### 2.3 `ui/components/csa/pipeline_tab.py` (MOVED + ADAPTED)

**Import changes**:
```python
# Before:
from log_runner import run_with_log_csa

# After:
from components.log_stream import run_with_log as run_with_log_csa
```

**`_CSA_PIPELINE_CLI` path**: Already correct (uses `Path(__file__)` relative) — recalculate:
```python
# Before (csa-ui/components/pipeline_tab.py):
_CSA_PIPELINE_CLI = (
    Path(__file__).parent.parent.parent  # clinical-statistics-analyzer/
    / "scripts" / "crf_pipeline" / "cli.py"
)

# After (ui/components/csa/pipeline_tab.py):
_CSA_PIPELINE_CLI = (
    Path(__file__).parent.parent.parent.parent.parent
    # ui/components/csa/ → ui/components/ → ui/ → hematology-paper-writer/ → skill root
    / "clinical-statistics-analyzer" / "scripts" / "crf_pipeline" / "cli.py"
)
```

> **Note**: This path traversal is now longer. An alternative is to resolve via an env var or
> `ui_config.json` — but the relative path is deterministic and testable.

---

### 2.4 `ui/components/csa/analysis_tab.py` (MOVED + ADAPTED)

**Import changes**:
```python
# Before:
from log_runner import run_with_log_csa

# After:
from components.log_stream import run_with_log as run_with_log_csa
```

**`_REGISTRY_PATH` update**:
```python
# Before:
_REGISTRY_PATH = Path(__file__).parent.parent / "script_registry.json"

# After:
_REGISTRY_PATH = Path(__file__).parent.parent.parent / "script_registry.json"
# ui/script_registry.json
```

**`_CSA_SCRIPTS_DIR` update**:
```python
# Before:
_CSA_SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"
# csa-ui/components/ → csa-ui/ → clinical-statistics-analyzer/ → scripts/

# After:
_CSA_SCRIPTS_DIR = (
    Path(__file__).parent.parent.parent.parent.parent
    / "clinical-statistics-analyzer" / "scripts"
)
```

**Key addition — direct session state write in `_write_hpw_manifest()`**:
```python
def _write_hpw_manifest(self, run_results: dict) -> None:
    manifest = { ... }  # existing manifest dict construction
    out = self.project_dir / "data" / "hpw_manifest.json"
    out.write_text(json.dumps(manifest, indent=2, default=str))

    # NEW: set session state directly — eliminates 10s polling lag
    st.session_state["csa_manifest"] = manifest

    st.success(f"HPW manifest written → `data/hpw_manifest.json`\nCSA badge updated instantly.")
```

---

### 2.5 `ui/components/log_stream.py` (MODIFIED — alias only)

Add one line at the end of the file:

```python
# Alias for CSA components that import run_with_log_csa by name
run_with_log_csa = run_with_log
```

---

### 2.6 `ui/components/csa_badge.py` (SIMPLIFIED)

**Before** (polls filesystem with TTL cache):
```python
@st.cache_data(ttl=10)
def _check_manifest(manifest_path: str) -> Optional[dict]:
    p = Path(manifest_path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return None
```

**After** (reads session state directly):
```python
def _check_manifest(self) -> Optional[dict]:
    """Return manifest from session state (set by AnalysisTab._write_hpw_manifest)."""
    return st.session_state.get("csa_manifest")
```

The `render()` method changes from:
```python
manifest = _check_manifest(str(manifest_file))
```
to:
```python
manifest = self._check_manifest()
```

The `manifest_file` existence check is also removed — no longer needed for badge display.
The "Open CSA ↗" link is removed (no separate app at port 8502).

New simplified badge render:
```python
def render(self, project_dir: str) -> None:
    manifest = self._check_manifest()
    if not manifest:
        return  # no badge when no manifest

    col_badge, col_btn = st.columns([3, 1])
    col_badge.success(
        f"CSA data ready — {manifest.get('script_label', 'analysis')} "
        f"({manifest.get('run_timestamp', '')[:10]})"
    )
    if col_btn.button("Import results", key="import_csa_manifest"):
        self._load_manifest_into_session(manifest)
```

---

### 2.7 `ui/app.py` (MODIFIED — tab layout)

**Current structure** (simplified):
```python
# sidebar: project tree
# main: phase panel + csa badge stub
```

**New structure**:
```python
from components.csa import DocumentsTab, PipelineTab, AnalysisTab

# ... existing sidebar/project selection ...

if active_project:
    tab_manuscript, tab_csa = st.tabs(["Manuscript Workflow", "Statistical Analysis"])

    with tab_manuscript:
        CSABadge(config.get("csa_port", 8502)).render(active_project)
        # existing phase panel rendering
        phase_panel.render(selected_phase, active_project)

    with tab_csa:
        sub_docs, sub_pipeline, sub_analysis = st.tabs([
            "Documents", "CRF Pipeline", "Analysis Scripts"
        ])
        with sub_docs:
            DocumentsTab(active_project).render()
        with sub_pipeline:
            PipelineTab(active_project).render()
        with sub_analysis:
            AnalysisTab(active_project).render()
```

> **Note**: `CSABadge` remains in the `Manuscript Workflow` tab (above the phase panel),
> so Phase 4 users see the import button without switching tabs.

---

## 3. Session State Flow

```
User selects project (sidebar)
  └─ st.session_state["csa_active_project"] = project_dir
  └─ protocol_params.json read → st.session_state["protocol_params"]

User runs analysis (Statistical Analysis tab → Analysis Scripts)
  └─ AnalysisTab._write_hpw_manifest()
       ├─ writes data/hpw_manifest.json  (for R scripts that read disk)
       └─ st.session_state["csa_manifest"] = manifest  ← NEW, immediate

User switches to Manuscript Workflow tab (Phase 4)
  └─ CSABadge.render() reads st.session_state["csa_manifest"]  ← 0s lag
       └─ "Import results" button → preset_topic, csa_manifest in session
```

---

## 4. Path Resolution Reference

All paths relative to `ui/components/csa/`:

| Target | Relative Path (`Path(__file__).parents[N]`) | Result |
|--------|---------------------------------------------|--------|
| `ui/` | `parents[2]` | `hematology-paper-writer/ui/` |
| `ui/script_registry.json` | `parents[2] / "script_registry.json"` | ✅ |
| skill root | `parents[4]` | `/Users/.../skill/` |
| CSA scripts | `parents[4] / "clinical-statistics-analyzer/scripts"` | ✅ |
| CSA pipeline CLI | `parents[4] / "clinical-statistics-analyzer/scripts/crf_pipeline/cli.py"` | ✅ |

---

## 5. `ui_config.json` Additions

```json
{
  "hpw_base_dir": "...",
  "hpw_port": 8501,
  "csa_port": 8502
}
```

`csa_port` is retained in config (used only for the "Open CSA" link if ever restored).
No new keys needed — the unified app reads project_dir from session state, not config.

---

## 6. Deprecation of `csa-ui/`

After migration, `csa-ui/` is deleted. A one-line stub `csa-ui/DEPRECATED.md` is left:

```
This directory has been retired. All CSA functionality is now in:
  hematology-paper-writer/ui/ (Statistical Analysis tab)
Launch: streamlit run hematology-paper-writer/ui/app.py
```

---

## 7. Implementation Checklist (Do Phase)

- [ ] Create `ui/components/csa/__init__.py`
- [ ] Copy + adapt `documents_tab.py` (fix imports, `_REGISTRY_PATH`)
- [ ] Copy + adapt `pipeline_tab.py` (fix imports, recalculate `_CSA_PIPELINE_CLI`)
- [ ] Copy + adapt `analysis_tab.py` (fix imports, `_REGISTRY_PATH`, `_CSA_SCRIPTS_DIR`, add session write)
- [ ] Move `script_registry.json` from `csa-ui/` to `ui/`
- [ ] Add `run_with_log_csa = run_with_log` alias to `log_stream.py`
- [ ] Simplify `csa_badge.py` (remove TTL cache, read session state)
- [ ] Modify `ui/app.py` (add top-level tabs, import CSA components)
- [ ] Delete `csa-ui/` contents (keep `DEPRECATED.md`)
- [ ] Verify all imports resolve with `python -c "import ui.components.csa"`
- [ ] Manual smoke test: project select → CSA Analysis → manifest → Manuscript tab badge

---

## 8. Risk Mitigations

| Risk | Design Response |
|------|----------------|
| `_CSA_PIPELINE_CLI` path breaks | Use `parents[4]` resolution; verify with `assert path.exists()` in `__init__` |
| `_CSA_SCRIPTS_DIR` path breaks | Same `parents[4]` pattern |
| `csa_manifest` not in session on first load | `CSABadge.render()` early-returns `None` — no crash |
| Nested `st.tabs()` not supported | Streamlit ≥1.18 supports nested tabs; verify version |
| Tab state reset on project switch | All CSA components read `project_dir` from arg, not from widget state |
