# Plan: HPW + CSA Unified UI v2 — Single-App Tab Consolidation

**Feature**: `hpw-csa-unified-ui-v2`
**Phase**: Plan
**Created**: 2026-03-06
**Depends on**: `hpw-csa-unified-ui` (completed, 93%)

---

## Overview

Consolidate the two-app architecture (HPW port 8501 + CSA port 8502) into a single Streamlit
application. CSA functionality becomes a top-level tab within the HPW app. The standalone
`csa-ui/` app is retired.

## Problem Statement

The current dual-app setup requires:
- Users to launch and manage two separate Streamlit processes
- File-based IPC: `hpw_manifest.json` with 10s polling lag
- Mental context switching between two browser tabs/URLs
- A dedicated `CSABadge` component to watch the filesystem

## Goals

### Goal 1 — Single Entry Point

One `streamlit run` command starts the complete HPW+CSA workflow.

**Acceptance Criteria**:
- `streamlit run hematology-paper-writer/ui/app.py` exposes all HPW and CSA functionality
- `csa-ui/app.py` is retired (deleted or kept as legacy stub with deprecation notice)
- Port 8502 is no longer needed

### Goal 2 — Tab-Paged Layout

Top-level tabs in the HPW main panel:

```
[Project: MyStudy ▼]
───────────────────────────────────────
Sidebar: Phase tree (1–9)
Main:
  [ Manuscript Workflow ]  [ Statistical Analysis ]
                             └─ Documents | CRF Pipeline | Analysis Scripts
```

**Acceptance Criteria**:
- `Manuscript Workflow` tab: existing phase panel (unchanged behavior)
- `Statistical Analysis` tab: 3 sub-tabs (Documents, CRF Pipeline, Analysis Scripts)
- Active project is shared — no second project selector in CSA tab
- Switching tabs preserves widget state within each tab

### Goal 3 — Synchronous Session State Handoff

Replace file-polling IPC with direct `st.session_state` sharing.

**Acceptance Criteria**:
- `AnalysisTab._write_hpw_manifest()` writes to both `data/hpw_manifest.json` (for R scripts)
  AND sets `st.session_state["csa_manifest"]` directly
- Phase 4 (Manuscript Prep) reads `st.session_state["csa_manifest"]` — no file read needed
- `CSABadge` component simplified: checks `st.session_state.get("csa_manifest")` only
  (no `@st.cache_data(ttl=10)` filesystem poll)
- Manifest import is instantaneous (same Streamlit event loop)

### Goal 4 — CSA Component Migration

Move CSA UI components from `csa-ui/` into HPW's `ui/components/csa/`.

**Acceptance Criteria**:
- `csa-ui/components/documents_tab.py` → `ui/components/csa/documents_tab.py`
- `csa-ui/components/pipeline_tab.py` → `ui/components/csa/pipeline_tab.py`
- `csa-ui/components/analysis_tab.py` → `ui/components/csa/analysis_tab.py`
- `csa-ui/log_runner.py` merged into `ui/components/log_stream.py` (same API already)
- `csa-ui/script_registry.json` moved to `ui/script_registry.json`
- `csa-ui/config.py` logic absorbed into HPW's `ui/ui_config.json` loader
- `csa-ui/components/project_selector.py` **deleted** (project is already selected in HPW sidebar)

### Goal 5 — Retain All CSA Functionality

No regression in CSA features.

**Acceptance Criteria**:
- All 8 analysis scripts in `script_registry.json` remain accessible
- Protocol params auto-population in AnalysisTab still works
- CRF batch upload → `crf_consolidated.csv` still works
- Pipeline validate + run steps still work
- "Export to HPW" still writes `hpw_manifest.json` to project `data/`

## Non-Goals

- Do NOT change any R scripts or the CRF pipeline CLI
- Do NOT change `protocol_params.json` schema (R scripts read it from disk)
- Do NOT build a new backend or authentication
- Do NOT make `csa-ui/` a dependency — retire it cleanly

## Architecture

### Before

```
hematology-paper-writer/ui/app.py          (port 8501)
clinical-statistics-analyzer/csa-ui/app.py (port 8502)
```

### After

```
hematology-paper-writer/
  ui/
    app.py                          ← add top-level tabs; import CSA components
    components/
      csa/                          ← NEW directory
        __init__.py
        documents_tab.py            ← moved from csa-ui/
        pipeline_tab.py             ← moved from csa-ui/
        analysis_tab.py             ← moved from csa-ui/
      csa_badge.py                  ← simplified (no TTL poll)
      log_stream.py                 ← absorb log_runner.py alias
    script_registry.json            ← moved from csa-ui/
    ui_config.json                  ← absorb csa-ui/config.py defaults
```

## Session State Contract

| Key | Written by | Read by | Notes |
|-----|-----------|---------|-------|
| `csa_active_project` | Sidebar selector | All CSA components | Replaces `project_selector.py` |
| `protocol_params` | `ProjectSelector` on project switch | `AnalysisTab`, Phase 4 | No change |
| `csa_manifest` | `AnalysisTab._write_hpw_manifest()` | `CSABadge`, Phase 4 | **Now set directly, not polled** |
| `csa_last_run_results` | `AnalysisTab` after Run | Export button | No change |

## Migration Steps

1. Create `ui/components/csa/` directory with `__init__.py`
2. Copy + adapt `documents_tab.py`, `pipeline_tab.py`, `analysis_tab.py`
   - Remove `project_dir` constructor arg (read from `st.session_state["csa_active_project"]`)
   - Update imports (`from log_runner import` → `from components.log_stream import`)
3. Move `script_registry.json` to `ui/`
4. Modify `analysis_tab.py`: add `st.session_state["csa_manifest"] = manifest` after file write
5. Simplify `csa_badge.py`: remove `@st.cache_data(ttl=10)`, check session state only
6. Modify `ui/app.py`: wrap existing content in `Manuscript Workflow` tab; add `Statistical Analysis` tab
7. Update `ui_config.json` with CSA defaults (hpw_base_dir already there)
8. Delete `csa-ui/` (or add deprecation stub)

## Key Risks

| Risk | Mitigation |
|------|-----------|
| `csa-ui/` still referenced in CLAUDE.md or launch docs | Update CLAUDE.md; add deprecation notice |
| `log_runner.py` import alias breaks | Add `run_with_log_csa = run_with_log` alias in `log_stream.py` |
| `project_dir` constructor removal breaks callers | Pass via `st.session_state` — single read in `render()` |
| Tab state reset on project switch | Use `st.session_state` for tab content, not widget defaults |

## Success Metrics

- Single `streamlit run` command covers 100% of HPW+CSA functionality
- CSA manifest available in Phase 4 within the same Streamlit event cycle (0s lag)
- Zero file reads required for manifest handoff
- `csa-ui/` directory retired with no broken imports in HPW codebase

## Implementation Order

1. Create `ui/components/csa/__init__.py`
2. Migrate `documents_tab.py` → `ui/components/csa/`
3. Migrate `pipeline_tab.py` → `ui/components/csa/`
4. Migrate `analysis_tab.py` → `ui/components/csa/` + add direct session state write
5. Move `script_registry.json` to `ui/`
6. Simplify `csa_badge.py`
7. Modify `ui/app.py` to add top-level tabs
8. Delete / stub `csa-ui/`
