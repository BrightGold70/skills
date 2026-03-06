# Plan: HPW + CSA Unified UI

**Feature**: `hpw-csa-unified-ui`
**Phase**: Plan
**Created**: 2026-03-06
**Skills**: `hematology-paper-writer` (primary), `clinical-statistics-analyzer` (secondary)
**Depends on**: `hpw-protocol-extraction` (protocol_params.json schema)

---

## Overview

A dual Streamlit web application — HPW App (port 8501) and CSA App (port 8502) — that wraps
all CLI options of both skills into a user-friendly point-and-click interface. HPW is the
primary app organized as a project-centric manuscript tree; CSA is a standalone app that
connects to HPW projects and feeds analysis results back via `hpw_manifest.json`.

## Problem Statement

Both HPW and CSA expose their functionality exclusively through CLI commands with numerous
flags. This creates friction for clinical researchers who:
- Must memorize flag names and syntax
- Cannot easily track manuscript project state across phases
- Must manually coordinate data flow between CSA statistical analysis and HPW manuscript drafting
- Have no visual feedback during long-running operations (PubMed search, OCR, R script execution)

## Goals

### Goal 1: HPW — Project-Centric Streamlit App

A Streamlit app with a left sidebar project tree and a right main panel that renders each
HPW phase as a form with buttons and dropdowns.

**Acceptance Criteria**:
- Left sidebar: list of manuscript projects (read from Dropbox output directory)
- Each project expandable to show 11-phase status tree with completion badges
- [+ New Project] button: creates project folder, accepts protocol document upload
- Main panel: selected phase renders its CLI options as Streamlit widgets
  - Dropdowns: `--journal`, `--document-type`, `--disease`
  - Number inputs: `--max-results`, `--word-limit`
  - Toggles: `--docx`, `--import-refs`, `--verify-references`
  - Text inputs: topic, search query
- Run button → executes underlying CLI command
- Output: collapsible live log + summary card
- Header badge: "● CSA data ready" when `hpw_manifest.json` detected in project folder
- Header button: "Open CSA ↗" → opens `localhost:8502` in new tab

### Goal 2: HPW — Protocol Upload in Phase 1

Phase 1 (Topic Selection) panel includes protocol document upload as the first step.

**Acceptance Criteria**:
- File uploader (DOCX/PDF) in Phase 1 panel
- On upload: calls `hpw load-protocol` → shows extraction progress + results preview
  - Extracted: background summary, methods summary, SAP parameters, reference count
- Extracted seeds available as pre-populated text in Phase 4 (Manuscript) panel
- `protocol_params.json` written to project `data/` for CSA auto-population

### Goal 3: HPW — File Watcher for CSA Integration

HPW polls for `hpw_manifest.json` in the active project's `data/` folder and updates the UI.

**Acceptance Criteria**:
- Poll interval: 10 seconds (configurable)
- On detection: sidebar badge changes to "● CSA data ready" (green)
- Phase 4 panel shows "Import CSA results" button → loads manifest into Statistical Methods fields
- Manual file picker as fallback ("Import from file...")

### Goal 4: CSA — Standalone Streamlit App with HPW Project Integration

A separate Streamlit app with a project selector and three tabs.

**Acceptance Criteria**:
- Header: `Select HPW Project` dropdown (reads HPW Dropbox project folders)
- On project select: auto-loads `protocol_params.json` (I/E criteria, endpoints, sample size)
- Three tabs: Documents, CRF Pipeline, Analysis Scripts

### Goal 5: CSA — Tab 1: Documents

Three upload zones for study documents.

**Acceptance Criteria**:
- **Zone A — Protocol**: read-only display of protocol loaded from HPW project (`docs/protocol/`)
  - Shows extracted parameters: endpoints, sample size, I/E criteria (from `protocol_params.json`)
- **Zone B — CRF Form**: file uploader (DOCX/Excel); parse field schema on upload
  - Schema preview table: field | type | valid values
- **Zone C — Patient CRFs**: batch file uploader (PDF/DOCX, multiple)
  - Per-file status row: filename | format | status (queued/OCR/parsed/validated/error)
  - PDF → OCR extraction; DOCX → direct parse
  - Each record validated against CRF Form schema
  - Summary: N patients loaded, M validation errors

### Goal 6: CSA — Tab 2: CRF Pipeline

Wraps the existing CSA CRF pipeline CLI into a step-by-step UI.

**Acceptance Criteria**:
- Input: consolidated dataset from Tab 1 (auto-loaded when Tab 1 complete)
- Pipeline steps shown as checklist: Validate → Transform → Export
- Each step has Run button → live log + step result
- Final export: writes clean dataset to project `data/` folder

### Goal 7: CSA — Tab 3: Analysis Scripts

Wraps CSA R analysis scripts into a selectable, parameterized UI.

**Acceptance Criteria**:
- Disease module selector: AML / CML / HCT / Safety (radio buttons)
- Script picker: dropdown filtered by module
  - AML: Table 1, ELN risk, composite response, BOIN, Fine-Gray
  - CML: TFR analysis, scores, ELN milestones
  - HCT: GVHD analysis, NRM, relapse
  - Safety: CTCAE grading, SAE summary
- Parameters: auto-populated from `protocol_params.json`; user-editable
- Run button → live log stream + summary card
- "Export to HPW" button → writes `hpw_manifest.json` to project `data/`

### Goal 8: Shared Output Experience

Both apps provide consistent live log + summary card output for all long-running operations.

**Acceptance Criteria**:
- Collapsible log panel with real-time streaming (`subprocess` + `st.empty()`)
- Summary card above log: status icon, duration, key result metrics, warnings
- Copy-to-clipboard button on summary card
- Download button for output files

## Non-Goals

- Do NOT build a new backend — all operations call existing HPW/CSA CLI commands
- Do NOT implement user authentication (local tool, single user)
- Do NOT support remote/cloud deployment in v1 (localhost only)
- Do NOT replace the CLI (CLI remains primary; UI is a wrapper)
- Do NOT build mobile/responsive layout

## Architecture

```
hematology-paper-writer/
  ui/
    app.py              ← existing, extend
    components/
      project_tree.py   ← new: sidebar project navigator
      phase_panel.py    ← new: dynamic phase form renderer
      protocol_panel.py ← new: protocol upload + extraction display
      log_stream.py     ← new: live log + summary card component
      csa_badge.py      ← new: file watcher + badge

clinical-statistics-analyzer/
  csa-ui/
    app.py              ← new: CSA Streamlit app (port 8502)
    components/
      project_selector.py  ← new: HPW project dropdown
      documents_tab.py     ← new: Tab 1 upload zones
      pipeline_tab.py      ← new: Tab 2 CRF pipeline
      analysis_tab.py      ← new: Tab 3 script runner
      log_stream.py        ← new: shared with HPW (or copied)
    script_registry.json   ← new: script → parameters mapping
```

## Shared Project Folder Convention

```
{Dropbox}/Paper/Hematology_paper_writer/{Project}/
  docs/
    protocol/          ← protocol.docx (HPW owns, CSA reads)
    manuscripts/
    drafts/
  data/
    protocol_params.json    ← HPW writes (from protocol extraction)
    hpw_manifest.json       ← CSA writes, HPW watches
    crf_consolidated.csv    ← CSA pipeline output
  literature/
```

## Key Risks

| Risk | Mitigation |
|------|-----------|
| Subprocess streaming on macOS/Streamlit | Use `subprocess.Popen` with `st.empty()` polling |
| CSA R script execution in Streamlit | Run via `subprocess`; capture stdout/stderr |
| OCR speed for large CRF batches | Queue with progress; show per-file status |
| Project folder discovery (Dropbox path) | Configurable base path in `ui_config.json` |
| Port conflicts (8501/8502) | Configurable; document startup commands |

## Dependencies (new)

- `pdfplumber` — PDF text extraction (HPW: protocol parser; CSA: patient CRF)
- `pytesseract` — OCR for scanned PDFs (optional, CSA patient CRFs)
- `openpyxl` — Excel CRF form parsing (CSA)
- `watchdog` — file system watcher (HPW badge, or polling fallback)
- Existing: `streamlit`, `python-docx`, `subprocess`

## Success Metrics

- All HPW CLI commands accessible without terminal in ≤ 2 clicks
- Protocol upload + extraction preview visible in < 30 seconds
- CSA patient CRF batch processing: status visible per file in real time
- CSA → HPW manifest handoff detectable within 10 seconds
- Zero CLI knowledge required for a complete HPW Phase 1–5 workflow

## Implementation Order (Do Phase)

**HPW App**:
1. `project_tree.py` — sidebar with project CRUD
2. `log_stream.py` — reusable live log + summary card
3. `phase_panel.py` — widget renderer (dropdowns, toggles, number inputs → CLI args)
4. `protocol_panel.py` — Phase 1 upload + extraction result display
5. `csa_badge.py` — file watcher / polling + badge
6. Wire into existing `ui/app.py`

**CSA App**:
7. `csa-ui/app.py` skeleton + `project_selector.py`
8. `script_registry.json` — enumerate all CSA scripts + their parameters
9. `documents_tab.py` — Zone A (protocol read), Zone B (CRF form), Zone C (patient CRF batch)
10. `pipeline_tab.py` — CRF pipeline step UI
11. `analysis_tab.py` — script runner with auto-populated parameters
12. End-to-end integration test: protocol → CSA → manifest → HPW badge
