# Completion Report: HPW + CSA Unified UI

**Feature**: `hpw-csa-unified-ui`
**Phase**: Completed
**Date**: 2026-03-06
**Match Rate**: 93%

---

## Executive Summary

```
[Plan] ✅ → [Design] ✅ → [Do] ✅ → [Check] ✅ → [Act] ✅ → [Report] ✅
```

The `hpw-csa-unified-ui` feature delivered a dual Streamlit web application — HPW App (port 8501)
and CSA App (port 8502) — that wraps all CLI functionality of both the Hematology Paper Writer
and Clinical Statistics Analyzer skills into a point-and-click interface.

All 17 planned files were implemented. All 8 goals from the Plan document were met. Two minor
structural gaps (GAP-02: `build_csa_args` alias, GAP-03: manual manifest import) remain as
deferred improvements with no runtime impact.

---

## Goals vs. Outcomes

| Goal | Description | Status |
|------|-------------|--------|
| 1 | HPW project-centric Streamlit app (sidebar + phase panel) | ✅ Delivered |
| 2 | Protocol upload in Phase 2 (Research Design) | ✅ Delivered |
| 3 | CSA badge file watcher (10s TTL poll) | ✅ Delivered |
| 4 | CSA standalone app with HPW project selector | ✅ Delivered |
| 5 | CSA Tab 1: Documents (protocol/CRF form/patient CRFs) | ✅ Delivered |
| 6 | CSA Tab 2: CRF Pipeline (validate + run steps) | ✅ Delivered |
| 7 | CSA Tab 3: Analysis Scripts (disease module → R script runner) | ✅ Delivered |
| 8 | Shared live log + summary card output experience | ✅ Delivered |

---

## Implementation Summary

### HPW App (`hematology-paper-writer/ui/`)

**17 files implemented** across two apps. Key HPW components:

| File | Purpose | Key Design |
|------|---------|------------|
| `ui/app.py` | Entry point; project selector + CSABadge integration | Replaced stub with real CSABadge |
| `ui/components/project_tree.py` | Sidebar project CRUD + phase status tree | `update_phase_status()` JSON persistence |
| `ui/components/log_stream.py` | Live subprocess log + summary card | `subprocess.Popen` + `st.empty()` streaming; `st.download_button` for log export |
| `ui/components/phase_panel.py` | Registry-driven form renderer | 7 widget types: text, textarea, number, dropdown, multiselect, toggle, file_picker |
| `ui/components/protocol_panel.py` | Phase 2 protocol upload + extraction display | Existing file listing, Re-parse, Delete; missing fields form |
| `ui/components/csa_badge.py` | CSA manifest watcher + import button | `@st.cache_data(ttl=10)` polling |
| `ui/phase_registry.json` | All 9 HPW phases → widget specs | `file_picker` type for manuscript phases 5–8 |
| `ui/cli_runner.py` | `build_hpw_args(command, widget_values)` | Maps widget values → CLI flag list |

### CSA App (`clinical-statistics-analyzer/csa-ui/`)

| File | Purpose | Key Design |
|------|---------|------------|
| `csa-ui/app.py` | Port 8502 entry point; 3-tab layout | `sys.path.insert` for relative imports |
| `csa-ui/config.py` | `load_csa_config()` | Reads HPW `ui_config.json`; falls back to defaults |
| `csa-ui/log_runner.py` | `run_with_log_csa()` | Same API as HPW `run_with_log`; `RunResult` dataclass |
| `csa-ui/script_registry.json` | AML/CML/HCT/Safety → R scripts + params | 8 scripts; multiselect support for CML scores |
| `csa-ui/components/project_selector.py` | HPW project dropdown | Loads `protocol_params.json` into session on select |
| `csa-ui/components/documents_tab.py` | Zone A/B/C document ingestion | CRF form schema preview; batch patient CRF → `crf_consolidated.csv` |
| `csa-ui/components/pipeline_tab.py` | CRF pipeline validate + run steps | Direct `cli.py` script invocation via `sys.executable` |
| `csa-ui/components/analysis_tab.py` | Script runner + HPW manifest export | Auto-populates params from `protocol_params.json`; `_write_hpw_manifest()` |

---

## Key Technical Decisions

### 1. Registry-Driven UI (`phase_registry.json` / `script_registry.json`)

Rather than hard-coding phase forms, all widget specs are externalized to JSON registries.
Adding a new HPW phase or CSA script requires only a JSON entry — no Python changes.

### 2. `file_picker` Widget Type

A new widget type was added to scan project `docs/` subdirectories for manuscript files
(`.md`, `.docx`, `.txt`). Phases 5–8 use this to avoid requiring users to type file paths,
which eliminates a major source of user error.

### 3. CSA Pipeline CLI — Direct Script Invocation

The pipeline tab invokes `cli.py` as a script via `[sys.executable, str(cli_path), ...]`
rather than as a Python module. This avoids requiring the skill to be installed as a package
and works correctly from any working directory.

### 4. 10s TTL Manifest Polling (`csa_badge.py`)

`@st.cache_data(ttl=10)` on `_check_manifest()` provides automatic badge refresh without
a background thread. This is the recommended Streamlit approach for file-based polling.

### 5. Protocol Panel Persistence Fix

Streamlit's `file_uploader` widget does not persist between sessions. The `ProtocolPanel`
lists existing protocol files from `docs/protocol/` on disk, providing Re-parse and Delete
actions — decoupling the UI from upload widget state.

### 6. `study_type` Priority Fix (Protocol Parser)

`MethodsExtractor` now checks Phase I/II/III trial patterns **before** observational patterns.
A "prospective Phase II study" was being misclassified as observational because "prospective"
appeared before the Phase II check. Fix: reordered `if/elif` branches; verbatim extraction
from "Overall Study Design:" sentence provides the most accurate study type label.

---

## Gap Analysis Results

| Gap | Severity | Status |
|-----|----------|--------|
| GAP-01: `download_button` in `log_stream.py` | Minor | False alarm — already implemented at line 128 |
| GAP-02: `build_csa_args` in `cli_runner.py` | Low | Deferred — `_build_r_cmd()` in `analysis_tab.py` is functional equivalent |
| GAP-03: Manual manifest import in `csa_badge.py` | Minor | Deferred — auto-polling covers primary use case |
| GAP-04: `multiselect` widget in `phase_panel.py` | Medium | Fixed — added branch before `toggle` in `_render_widget()` |
| GAP-05: Pipeline CLI module path runtime failure | High | Fixed — replaced broken module path with direct `cli.py` script path |

**Final match rate: 93%** (above 90% threshold)

---

## Data Flow

```
HPW App (8501)                              CSA App (8502)
──────────────────────────────────────────────────────────
Phase 2: Upload protocol.docx
  └─ protocol_parser.py → protocol_params.json ──────────→ ProjectSelector loads params
                                                              AnalysisTab auto-populates
Phase 4: Manuscript draft                                     params from protocol_params
  └─ CSABadge polls hpw_manifest.json ←──────────────── AnalysisTab: _write_hpw_manifest()
       └─ Import button → session state                        after successful R script run
            └─ preset_topic filled in Phase 4 widget
```

---

## Runtime Configuration

| Setting | Default | Config Key |
|---------|---------|-----------|
| HPW port | 8501 | `ui_config.json → hpw_port` |
| CSA port | 8502 | `ui_config.json → csa_port` |
| HPW base dir | `~/Library/CloudStorage/Dropbox/Paper/Hematology_paper_writer` | `ui_config.json → hpw_base_dir` |
| Manifest poll TTL | 10s | `csa_badge.py @st.cache_data(ttl=10)` |

**Launch commands**:
```bash
# HPW App
streamlit run hematology-paper-writer/ui/app.py --server.port 8501

# CSA App
streamlit run clinical-statistics-analyzer/csa-ui/app.py --server.port 8502
```

---

## Deferred Work

| Item | Priority | Effort |
|------|----------|--------|
| GAP-02: `build_csa_args` alias in `cli_runner.py` | Low | 5 min |
| GAP-03: Manual "Import from file..." fallback in `csa_badge.py` | Minor | 30 min |
| OCR for scanned patient CRF PDFs (pytesseract) | Medium | 2h |
| Toast notifications on manifest import | Low | 15 min |

---

## Success Metrics Achieved

| Metric | Target | Result |
|--------|--------|--------|
| HPW CLI commands accessible without terminal | ≤ 2 clicks | ✅ Run button on each phase |
| Protocol extraction preview visible | < 30s | ✅ Immediate on Re-parse |
| CSA → HPW manifest detection | ≤ 10s | ✅ 10s TTL cache |
| Zero CLI knowledge required for Phase 1–5 | Yes | ✅ All inputs are widgets |
| CRF batch processing status | Per-file real time | ✅ Status column in documents_tab |
