# Design: HPW + CSA Unified UI

**Feature**: `hpw-csa-unified-ui`
**Phase**: Design
**Created**: 2026-03-06
**References**: [Plan](../../01-plan/features/hpw-csa-unified-ui.plan.md)
**Depends on**: `hpw-protocol-extraction` (ProtocolParser, protocol_params.json schema)

---

## Architecture Overview

```
Browser :8501 (HPW App)                Browser :8502 (CSA App)
┌──────────────────────────────┐       ┌──────────────────────────────┐
│  Sidebar: ProjectTree        │       │  Header: ProjectSelector      │
│  ┌────────────────────────┐  │       │  ┌────────────────────────┐  │
│  │ + New Project          │  │       │  │ Select HPW Project ▾   │  │
│  │ ▶ SAPPHIRE [CSA ●]    │  │       │  └────────────────────────┘  │
│  │ ▶ Asciminib CML       │  │       │                              │
│  └────────────────────────┘  │       │  Tabs: Documents | CRF | Analysis
│                              │       │  ┌──────────────────────────┐ │
│  Main: PhasePanel            │       │  │ Tab 1: DocumentsTab      │ │
│  ┌────────────────────────┐  │       │  │   Zone A: Protocol       │ │
│  │ Phase 1: Topic         │  │       │  │   Zone B: CRF Form       │ │
│  │  [ProtocolPanel]       │  │       │  │   Zone C: Patient CRFs   │ │
│  │  Form widgets          │  │       │  ├──────────────────────────┤ │
│  │  [Run ▶]               │  │       │  │ Tab 2: PipelineTab       │ │
│  │  [LogStream ▼]         │  │       │  │   Validate→Transform→Export│
│  └────────────────────────┘  │       │  ├──────────────────────────┤ │
│  Header: CSABadge            │       │  │ Tab 3: AnalysisTab       │ │
│  [● CSA data ready] [Open ↗] │       │  │   Module + Script + Run  │ │
└──────────────────────────────┘       │  │   [Export to HPW ▶]      │ │
                                       │  └──────────────────────────┘ │
                                       └──────────────────────────────┘

Shared filesystem (Dropbox project folder):
  data/protocol_params.json  ← HPW writes, CSA reads
  data/hpw_manifest.json     ← CSA writes, HPW watches
  data/crf_consolidated.csv  ← CSA pipeline output
```

---

## Shared Abstractions

### `LogStream` Component

Used in both apps for all subprocess-backed operations.

```python
# shared: hematology-paper-writer/ui/components/log_stream.py
# (CSA copies or imports from HPW)

import subprocess
import streamlit as st
import time
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class RunResult:
    returncode: int
    duration_s: float
    summary: str           # one-line human-readable result
    output_files: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def run_with_log(
    cmd: list[str],
    summary_parser: "Callable[[str], RunResult]",
    key: str,                     # unique st.session_state key
    max_lines: int = 200,
    env: Optional[dict] = None,
) -> Optional[RunResult]:
    """
    Execute cmd as subprocess, stream stdout/stderr to a collapsible
    st.expander, return RunResult when done.

    Pattern:
      1. st.empty() placeholder for live log
      2. subprocess.Popen with stdout=PIPE, stderr=STDOUT, text=True
      3. Read lines in a loop, append to session_state[key + "_log"]
      4. Update placeholder with last max_lines lines on each iteration
      5. On completion: parse summary, show SummaryCard above log
    """
    state_key = f"log_{key}"
    if state_key not in st.session_state:
        st.session_state[state_key] = []

    log_area = st.empty()
    start = time.time()

    try:
        with subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, env=env
        ) as proc:
            for line in proc.stdout:
                st.session_state[state_key].append(line.rstrip())
                log_area.code(
                    "\n".join(st.session_state[state_key][-max_lines:]),
                    language="",
                )
            proc.wait()

        duration = time.time() - start
        full_output = "\n".join(st.session_state[state_key])
        result = summary_parser(full_output)
        result.duration_s = duration
        result.returncode = proc.returncode
        _render_summary_card(result)
        return result

    except FileNotFoundError as e:
        st.error(f"Command not found: {cmd[0]}\n{e}")
        return None


def _render_summary_card(result: RunResult) -> None:
    """
    Compact status card above the log expander:
      [icon] duration  key_metric  [Copy] [Download]
    """
    icon = "✅" if result.returncode == 0 else "❌"
    col1, col2, col3 = st.columns([1, 6, 2])
    with col1:
        st.markdown(f"### {icon}")
    with col2:
        st.markdown(f"**{result.summary}** — {result.duration_s:.1f}s")
        for w in result.warnings:
            st.warning(w)
    with col3:
        st.button("Copy", key=f"copy_{id(result)}")
```

### `CLIRunner`

Thin wrapper that converts widget state to HPW/CSA CLI argument lists.

```python
# hematology-paper-writer/ui/cli_runner.py

import os
import sys

HPW_CLI = [sys.executable, "-m", "hematology_paper_writer.cli"]
CSA_CLI = [sys.executable, "-m", "clinical_statistics_analyzer.cli"]

def build_hpw_args(phase: str, widget_values: dict) -> list[str]:
    """
    Convert PhasePanel widget_values dict to CLI args.
    Skips None/False values. Handles toggle → flag mapping.

    Example:
      {"--docx": True, "--max-results": 20, "--journal": "Blood"}
      → ["generate", "--docx", "--max-results", "20", "--journal", "Blood"]
    """
    cmd = HPW_CLI + [phase]
    for key, val in widget_values.items():
        if val is None or val == "" or val is False:
            continue
        if val is True:
            cmd.append(key)
        else:
            cmd.extend([key, str(val)])
    return cmd

def build_csa_args(script_id: str, params: dict) -> list[str]:
    """
    Build CSA R script runner command.
    script_id maps to a script path in script_registry.json.
    """
    cmd = CSA_CLI + ["run-script", script_id]
    for key, val in params.items():
        if val is not None:
            cmd.extend([f"--{key}", str(val)])
    return cmd
```

---

## HPW App: Component Design

### `ui/components/project_tree.py`

```python
class ProjectTree:
    """
    Renders the sidebar project navigator.
    Reads project directories from HPW_BASE_DIR (from ui_config.json).
    """

    def __init__(self, base_dir: str): ...

    def render(self) -> Optional[str]:
        """
        Sidebar sections:
          [+ New Project] button
          For each project dir:
            st.expander(project_name, expanded=(project == active_project))
              → 11-phase status badges (read from project/.phase_status.json)
              → click → set st.session_state["active_project"]
        Returns: currently selected project directory path or None.
        """

    def _read_phase_status(self, project_dir: str) -> dict[int, str]:
        """
        Read {project_dir}/.phase_status.json.
        Returns: {1: "complete", 2: "in_progress", 3: "not_started", ...}
        """

    def _render_new_project_dialog(self) -> None:
        """
        st.dialog: project name input + protocol file uploader.
        On submit: creates directory structure, calls ProtocolPanel.handle_upload()
        """

    def _list_projects(self) -> list[str]:
        """
        List subdirs of base_dir sorted by mtime (most recent first).
        Filter: must contain docs/ and data/ subdirs.
        """
```

**Phase status badge rendering**:
```
Phase 1  Topic Selection        ✅
Phase 2  Research               🔄
Phase 3  Journal Strategy       ⏳
Phase 4  Manuscript Draft       ⏳
...
Phase 11 Submission             ⏳
```

### `ui/components/phase_panel.py`

Reads `phase_registry.json` to render dynamic forms per phase.

```python
class PhasePanel:
    """
    Main panel: renders widgets for a given HPW phase based on phase_registry.json.
    """

    def __init__(self, registry_path: str = "ui/phase_registry.json"): ...

    def render(self, phase_num: int, project_dir: str) -> None:
        """
        1. Load registry entry for phase_num
        2. Render form widgets (see _render_widget)
        3. [Run ▶] button → collect widget values → build CLI args → run_with_log()
        4. On success: update .phase_status.json
        """

    def _render_widget(self, spec: dict) -> any:
        """
        Dispatch to Streamlit widget based on spec["type"]:
          "dropdown"      → st.selectbox(spec["label"], spec["options"])
          "text"          → st.text_input(spec["label"], spec.get("default", ""))
          "number"        → st.number_input(spec["label"], min_value=..., max_value=..., value=...)
          "toggle"        → st.toggle(spec["label"], value=spec.get("default", False))
          "textarea"      → st.text_area(spec["label"], height=spec.get("height", 100))
          "file_upload"   → st.file_uploader(spec["label"], type=spec["accept"])
        Returns the widget value.
        """
```

**`ui/phase_registry.json` schema**:

```json
{
  "phases": {
    "1": {
      "label": "Topic Selection",
      "command": "topic",
      "widgets": [
        {"key": "topic",     "type": "text",     "label": "Research topic",     "cli_arg": "--topic"},
        {"key": "disease",   "type": "dropdown", "label": "Disease",            "cli_arg": "--disease",
         "options": ["AML", "CML", "MDS", "HCT", "ALL", "NHL", "MM"]},
        {"key": "doc_type",  "type": "dropdown", "label": "Document type",      "cli_arg": "--document-type",
         "options": ["original", "review", "meta-analysis", "case-report", "letter"]},
        {"key": "protocol",  "type": "file_upload", "label": "Protocol document (optional)",
         "accept": ["docx", "pdf"], "cli_arg": null, "handler": "protocol_upload"}
      ]
    },
    "2": {
      "label": "Research",
      "command": "research",
      "widgets": [
        {"key": "query",       "type": "text",    "label": "Search query",       "cli_arg": "--query"},
        {"key": "max_results", "type": "number",  "label": "Max results",        "cli_arg": "--max-results",
         "min": 5, "max": 200, "default": 50},
        {"key": "import_refs", "type": "toggle",  "label": "Import references",  "cli_arg": "--import-refs",
         "default": true}
      ]
    },
    "4": {
      "label": "Manuscript Draft",
      "command": "draft",
      "widgets": [
        {"key": "journal",    "type": "dropdown", "label": "Target journal",     "cli_arg": "--journal",
         "options": ["Blood", "Blood Research", "JCO", "Leukemia", "Haematologica",
                     "NEJM", "Lancet", "Lancet Haematology", "BMT", "Bone Marrow Transplant"]},
        {"key": "word_limit", "type": "number",   "label": "Word limit",         "cli_arg": "--word-limit",
         "min": 1000, "max": 8000, "default": 3500},
        {"key": "docx",       "type": "toggle",   "label": "Export DOCX",        "cli_arg": "--docx",
         "default": true},
        {"key": "verify_refs","type": "toggle",   "label": "Verify references",  "cli_arg": "--verify-references",
         "default": false}
      ]
    }
  }
}
```

(Remaining phases 3, 5–11 follow the same pattern.)

### `ui/components/protocol_panel.py`

```python
class ProtocolPanel:
    """
    Protocol upload widget used in Phase 1 panel.
    Wraps `hpw load-protocol` CLI command.
    """

    def render(self, project_dir: str) -> Optional[dict]:
        """
        1. st.file_uploader(type=["docx","pdf"])
        2. On upload: save to temp file → run `hpw load-protocol <path> --project <name>`
           via run_with_log()
        3. On success: display ExtractionPreview
        4. Return extraction summary dict or None
        """

    def _render_extraction_preview(self, params: dict) -> None:
        """
        Show protocol_params.json contents in a compact card:
          Primary endpoint | Study type | Sample size (N=X) | Power | Alpha
          Secondary endpoints (list)
          Missing fields (warning if any)
        """

    def _save_upload(self, uploaded_file, project_dir: str) -> str:
        """
        Save st.UploadedFile to {project_dir}/docs/protocol/{filename}.
        Returns saved path.
        """

    def _parse_summary(self, output: str) -> "RunResult":
        """
        Parse `hpw load-protocol` stdout:
          Look for lines: '✓ X sections', '✓ parameters saved', '⚠ Missing SAP fields'
        """
```

### `ui/components/csa_badge.py`

```python
class CSABadge:
    """
    Detects hpw_manifest.json in active project and renders header badge.
    Uses st.cache_data(ttl=10) for 10-second poll without background threads.
    """

    @staticmethod
    @st.cache_data(ttl=10)
    def _check_manifest(project_dir: str) -> tuple[bool, Optional[float]]:
        """
        Check if {project_dir}/data/hpw_manifest.json exists.
        Returns: (exists, mtime_or_None)
        Cached with 10s TTL — Streamlit re-evaluates on cache expiry.
        """
        path = Path(project_dir) / "data" / "hpw_manifest.json"
        if path.exists():
            return True, path.stat().st_mtime
        return False, None

    def render(self, project_dir: str) -> None:
        """
        Renders in st.sidebar header:
          If manifest found: green "● CSA data ready" badge + "Open CSA ↗" button
          Else: grey "○ CSA not connected" badge
        [Open CSA ↗] opens localhost:8502 via st.markdown with target="_blank"
        [Import CSA results] button → _load_manifest_into_session()
        [Import from file...] manual file picker fallback
        """

    def _load_manifest_into_session(self, project_dir: str) -> None:
        """
        Read hpw_manifest.json → st.session_state["csa_manifest"].
        PhasePanel (Phase 4) checks session_state["csa_manifest"] to pre-populate
        Statistical Methods fields.
        """
```

### `ui/app.py` Extension

```python
# Additions to existing ui/app.py

from components.project_tree import ProjectTree
from components.phase_panel import PhasePanel
from components.csa_badge import CSABadge
from config import load_ui_config

def main():
    config = load_ui_config()           # reads ui/ui_config.json
    st.set_page_config(layout="wide", page_title="HPW — Hematology Paper Writer")

    tree = ProjectTree(config["hpw_base_dir"])
    with st.sidebar:
        active_project = tree.render()  # returns selected project dir

    if active_project:
        badge = CSABadge()
        badge.render(active_project)    # renders in sidebar header

        phase_num = st.session_state.get("active_phase", 1)
        panel = PhasePanel()
        panel.render(phase_num, active_project)
    else:
        st.info("Select or create a project in the sidebar to begin.")
```

---

## CSA App: Component Design

### `csa-ui/app.py`

```python
# clinical-statistics-analyzer/csa-ui/app.py

import streamlit as st
from components.project_selector import ProjectSelector
from components.documents_tab import DocumentsTab
from components.pipeline_tab import PipelineTab
from components.analysis_tab import AnalysisTab
from config import load_csa_config

def main():
    config = load_csa_config()
    st.set_page_config(layout="wide", page_title="CSA — Clinical Statistics Analyzer")

    selector = ProjectSelector(config["hpw_base_dir"])
    project_dir = selector.render()     # header dropdown

    if not project_dir:
        st.info("Select an HPW project to begin.")
        return

    tab1, tab2, tab3 = st.tabs(["Documents", "CRF Pipeline", "Analysis Scripts"])
    with tab1:
        DocumentsTab(project_dir).render()
    with tab2:
        PipelineTab(project_dir).render()
    with tab3:
        AnalysisTab(project_dir).render()
```

### `csa-ui/components/project_selector.py`

```python
class ProjectSelector:
    """
    Header-level HPW project dropdown.
    Reads same HPW_BASE_DIR as HPW app.
    """

    def __init__(self, hpw_base_dir: str): ...

    def render(self) -> Optional[str]:
        """
        st.selectbox("Select HPW Project", project_names)
        On change: clear session state, load protocol_params.json into
          st.session_state["protocol_params"]
        Returns: selected project_dir or None
        """

    def _load_protocol_params(self, project_dir: str) -> Optional[dict]:
        """
        Read {project_dir}/data/protocol_params.json.
        Returns dict or None (graceful if file missing).
        Sets st.session_state["protocol_params"].
        """
```

### `csa-ui/components/documents_tab.py`

```python
class DocumentsTab:
    """
    Three upload zones for study documents.
    """

    def render(self, project_dir: str) -> None:
        """
        Three vertical sections:
          [Zone A] Protocol — read-only display
          [Zone B] CRF Form — file uploader + schema preview
          [Zone C] Patient CRFs — batch uploader + per-file status
        """

    def _render_zone_a(self, project_dir: str) -> None:
        """
        Read-only display of protocol loaded from HPW project.
        Source: st.session_state["protocol_params"]
        Show: primary_endpoint, sample_size_n, power, alpha, study_type,
               secondary_endpoints (list), inclusion/exclusion count
        If not found: st.warning("Load protocol in HPW app first.")
        """

    def _render_zone_b(self, project_dir: str) -> None:
        """
        File uploader: st.file_uploader("CRF Form", type=["docx", "xlsx"])
        On upload: call _parse_crf_form_schema() → show preview table
          Columns: field | type | required | valid_values
        Schema stored in st.session_state["crf_schema"]
        """

    def _parse_crf_form_schema(self, file) -> list[dict]:
        """
        DOCX: use python-docx → find tables → first table assumed to be field definition table
          Columns detected: "Field", "Type", "Values", "Required"
        XLSX: pandas read_excel(sheet_name=0) → first row as header
        Returns list of {field, type, required, valid_values} dicts
        """

    def _render_zone_c(self, project_dir: str) -> None:
        """
        Batch file uploader: st.file_uploader("Patient CRFs", type=["pdf","docx"],
                                               accept_multiple_files=True)
        Per-file processing in sequence:
          Status: queued → parsing → validated / error
        Shows st.dataframe of per-file status rows.
        On completion: writes crf_consolidated.csv to {project_dir}/data/
        """

    def _process_patient_crf(self, file, schema: list[dict]) -> dict:
        """
        Returns {filename, status, n_fields_extracted, n_validation_errors, errors[]}
        PDF: pdfplumber text extraction → field-value parsing
             If text yield < 100 chars/page → pytesseract OCR
        DOCX: python-docx table extraction → field-value mapping
        Validation: for each extracted field, check against schema valid_values
        """
```

### `csa-ui/components/pipeline_tab.py`

```python
class PipelineTab:
    """
    Wraps CSA CRF pipeline CLI (validate → transform → export) as step UI.
    """
    STEPS = ["validate", "transform", "export"]

    def render(self, project_dir: str) -> None:
        """
        Check prerequisite: crf_consolidated.csv exists in project data/
        If not: st.warning with link to Documents tab

        For each step:
          st.subheader(step_label)
          Status badge: not_run / running / success / error
          [Run step ▶] button → run_with_log(CSA_CLI + ["pipeline", step, ...])
          Expander: step result summary
        Final: export success → st.success with output file path + download button
        """

    def _build_step_args(self, step: str, project_dir: str) -> list[str]:
        """
        validate: CSA_CLI + ["pipeline", "validate", "--input", crf_csv_path]
        transform: CSA_CLI + ["pipeline", "transform", "--input", crf_csv_path,
                               "--output", clean_csv_path]
        export:    CSA_CLI + ["pipeline", "export", "--input", clean_csv_path,
                               "--format", "csv", "--output-dir", data_dir]
        """
```

### `csa-ui/components/analysis_tab.py`

```python
class AnalysisTab:
    """
    Script runner: disease module selector → script picker → auto-populated params → run.
    """

    def __init__(self, project_dir: str):
        self.registry = self._load_registry()  # script_registry.json
        self.project_dir = project_dir

    def render(self) -> None:
        """
        1. Disease module: st.radio(["AML","CML","HCT","Safety"], horizontal=True)
        2. Script: st.selectbox() filtered by module
        3. Parameters: render from registry spec + auto-populate from protocol_params
        4. [Run ▶] → run_with_log(build_csa_args(script_id, params))
        5. [Export to HPW] → _write_hpw_manifest()
        """

    def _auto_populate_params(self, script_spec: dict) -> dict:
        """
        For each param in script_spec["params"]:
          Check if param["protocol_key"] exists in st.session_state["protocol_params"]
          If yes: use that value as default for the widget
        Returns initial values dict for widget rendering.
        """

    def _write_hpw_manifest(self, run_results: dict) -> None:
        """
        Build hpw_manifest.json from accumulated run_results.
        Write to {project_dir}/data/hpw_manifest.json.
        Triggers CSABadge update in HPW app within next 10s poll.
        """
```

**`csa-ui/script_registry.json` schema**:

```json
{
  "version": "1.0",
  "modules": {
    "AML": {
      "label": "AML (Acute Myeloid Leukemia)",
      "scripts": {
        "table1_aml": {
          "label": "Table 1 — Patient Characteristics",
          "file": "scripts/02_table1.R",
          "params": [
            {"key": "dataset",  "label": "Dataset file",     "type": "text",
             "protocol_key": null,                            "required": true},
            {"key": "disease",  "label": "Disease",          "type": "text",
             "protocol_key": "disease_keywords",             "default": "AML"}
          ]
        },
        "eln_risk": {
          "label": "ELN Risk Stratification",
          "file": "scripts/20_aml_eln_risk.R",
          "params": [
            {"key": "dataset",   "label": "Dataset file",    "type": "text",
             "protocol_key": null,                           "required": true},
            {"key": "eln_year",  "label": "ELN version",     "type": "dropdown",
             "options": ["2022", "2017", "2010"],            "default": "2022"}
          ]
        },
        "boin_design": {
          "label": "Phase I — BOIN Design",
          "file": "scripts/25_aml_phase1_boin.R",
          "params": [
            {"key": "target_tox", "label": "Target toxicity rate", "type": "number",
             "min": 0.1, "max": 0.5, "default": 0.3,        "protocol_key": null},
            {"key": "n_doses",    "label": "Number of dose levels", "type": "number",
             "min": 2, "max": 10, "default": 5,              "protocol_key": null},
            {"key": "cohort_size","label": "Cohort size",    "type": "number",
             "min": 1, "max": 6,  "default": 3,              "protocol_key": null}
          ]
        }
      }
    },
    "CML": {
      "label": "CML (Chronic Myeloid Leukemia)",
      "scripts": {
        "tfr_analysis": {
          "label": "Treatment-Free Remission Analysis",
          "file": "scripts/22_cml_tfr_analysis.R",
          "params": [
            {"key": "dataset",      "label": "Dataset file",          "type": "text",   "required": true},
            {"key": "landmark_mos", "label": "Landmark (months)",     "type": "number",
             "default": 12},
            {"key": "molecular_resp","label": "Molecular response",   "type": "dropdown",
             "options": ["MR4", "MR4.5", "CMR"],                      "default": "MR4.5"}
          ]
        },
        "cml_scores": {
          "label": "CML Risk Scores (Sokal/EUTOS/ELTS)",
          "file": "scripts/23_cml_scores.R",
          "params": [
            {"key": "dataset",  "label": "Dataset file",              "type": "text",   "required": true},
            {"key": "scores",   "label": "Score systems",             "type": "multiselect",
             "options": ["Sokal", "EUTOS", "ELTS"],                   "default": ["Sokal","ELTS"]}
          ]
        }
      }
    },
    "HCT": {
      "label": "HCT (Hematopoietic Cell Transplantation)",
      "scripts": {
        "gvhd_analysis": {
          "label": "GVHD Analysis",
          "file": "scripts/24_hct_gvhd_analysis.R",
          "params": [
            {"key": "dataset",        "label": "Dataset file",        "type": "text",   "required": true},
            {"key": "gvhd_grade_sys", "label": "Grading system",      "type": "dropdown",
             "options": ["MAGIC", "Glucksberg", "IBMTR"],             "default": "MAGIC"},
            {"key": "landmark_day",   "label": "Landmark day",        "type": "number", "default": 100}
          ]
        }
      }
    },
    "Safety": {
      "label": "Safety Analysis",
      "scripts": {
        "safety_summary": {
          "label": "Table 5 — Safety Summary",
          "file": "scripts/05_safety.R",
          "params": [
            {"key": "dataset",      "label": "Dataset file",          "type": "text",   "required": true},
            {"key": "ctcae_version","label": "CTCAE version",         "type": "dropdown",
             "options": ["5.0", "4.03"],                              "default": "5.0"}
          ]
        }
      }
    }
  }
}
```

---

## Configuration Files

### `ui/ui_config.json` (shared by both apps via environment or direct path)

```json
{
  "hpw_base_dir": "~/Dropbox/Paper/Hematology_paper_writer",
  "hpw_port": 8501,
  "csa_port": 8502,
  "manifest_poll_interval_s": 10,
  "log_max_lines": 200,
  "phase_registry": "ui/phase_registry.json"
}
```

### Startup Commands

```bash
# Run HPW app (port 8501)
streamlit run hematology-paper-writer/ui/app.py --server.port 8501

# Run CSA app (port 8502)
streamlit run clinical-statistics-analyzer/csa-ui/app.py --server.port 8502

# Both together (macOS/Linux)
streamlit run hematology-paper-writer/ui/app.py --server.port 8501 &
streamlit run clinical-statistics-analyzer/csa-ui/app.py --server.port 8502
```

---

## Data Flow: Protocol Upload → CSA Auto-populate

```
User uploads protocol.docx in HPW Phase 1
        │
        ▼
ProtocolPanel._save_upload()
  → {project}/docs/protocol/protocol.docx
        │
        ▼
hpw load-protocol → ProtocolParser.load_and_extract()
  → {project}/data/protocol_params.json   (HPW writes)
  → {project}/docs/drafts/introduction_seed.md
  → {project}/docs/drafts/methods_seed.md
        │
        ▼
CSA: ProjectSelector._load_protocol_params()
  → st.session_state["protocol_params"]
        │
        ▼
AnalysisTab._auto_populate_params()
  → Widgets pre-populated with primary_endpoint, sample_size_n, etc.
```

## Data Flow: CSA Analysis → HPW Import

```
User runs analysis scripts in CSA Tab 3
        │
        ▼
AnalysisTab._write_hpw_manifest()
  → {project}/data/hpw_manifest.json   (CSA writes)
        │
        ▼ (within 10s)
CSABadge._check_manifest() cache expires
  → badge updates to "● CSA data ready"
        │
User clicks "Import CSA results"
        │
        ▼
CSABadge._load_manifest_into_session()
  → st.session_state["csa_manifest"]
        │
        ▼
PhasePanel (Phase 4) detects session_state["csa_manifest"]
  → Pre-populates Statistical Methods fields
```

---

## Error Handling

| Condition | Component | Behavior |
|-----------|-----------|----------|
| HPW CLI not installed | CLIRunner | `st.error("HPW not found. Run: pip install -e .")` |
| Protocol parse fails | ProtocolPanel | Show partial results + warning for missing fields |
| Patient CRF OCR fails | DocumentsTab Zone C | Row status = "error"; log; continue remaining files |
| CSA R script fails | AnalysisTab | LogStream shows full stderr; red summary card |
| manifest not found | CSABadge | Grey badge; no crash |
| Dropbox base_dir missing | ProjectTree | `st.error("HPW base dir not found: {path}. Check ui_config.json.")` |
| Port 8501/8502 conflict | Startup | Document in README; `--server.port` override |

---

## Dependencies to Add

```
# hematology-paper-writer/requirements.txt additions
streamlit>=1.32.0        # st.cache_data TTL, st.dialog
watchdog>=4.0.0          # optional (fallback: cache_data polling used)
openpyxl>=3.1.0          # CRF form XLSX parsing (CSA)

# Already in requirements (via hpw-protocol-extraction):
pdfplumber>=0.10.0
pytesseract>=0.3.10      # optional
pdf2image>=1.16.0
python-docx>=1.1.0
```

No new backend, auth, or cloud dependencies (per non-goals).

---

## Implementation Order (Do Phase)

**Phase A — HPW App Foundation**
1. `ui/ui_config.json` — config file + `ui/config.py` loader
2. `ui/components/log_stream.py` — LogStream + RunResult + SummaryCard
3. `ui/cli_runner.py` — CLIRunner (build_hpw_args, build_csa_args)
4. `ui/phase_registry.json` — all 11 phases (start with phases 1, 2, 4)
5. `ui/components/project_tree.py` — sidebar navigator + phase status badges
6. `ui/components/phase_panel.py` — dynamic widget renderer from registry
7. Wire into `ui/app.py`

**Phase B — HPW Protocol & CSA Integration**

8. `ui/components/protocol_panel.py` — protocol upload + extraction preview
9. `ui/components/csa_badge.py` — manifest poll + badge + import
10. Integrate protocol_panel into Phase 1 phase_panel rendering
11. End-to-end HPW test: project create → Phase 1 → Phase 4 draft

**Phase C — CSA App**

12. `csa-ui/app.py` skeleton + `csa-ui/components/project_selector.py`
13. `csa-ui/script_registry.json` — all AML/CML/HCT/Safety scripts
14. `csa-ui/components/documents_tab.py` — Zone A + B (protocol display, CRF form parse)
15. `csa-ui/components/documents_tab.py` — Zone C (patient CRF batch, OCR path)
16. `csa-ui/components/pipeline_tab.py` — step UI
17. `csa-ui/components/analysis_tab.py` — script runner + auto-populate + export
18. End-to-end integration test: HPW protocol → CSA auto-populate → run script → manifest → HPW badge detects

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2026-03-06 | Initial design |
