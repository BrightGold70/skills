"""
Hematology Paper Writer - Streamlit UI Application
Main entry point. Layout: sidebar project tree + phase panel main area.
"""

import json
import sys
from pathlib import Path

import streamlit as st

# Add parent directory to path so components can import from tools/
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.project_tree import ProjectTree
from components.phase_panel import PhasePanel
from components.status_dashboard import StatusDashboard
from components.csa import DocumentsTab, PipelineTab, AnalysisTab

# ── Configuration ────────────────────────────────────────────────────────────
_CONFIG_PATH = Path(__file__).parent / "ui_config.json"

_FONTS_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=DM+Serif+Display&"
    "family=Source+Sans+3:wght@400;600&"
    "family=JetBrains+Mono:wght@400;500&"
    "display=swap"
)

_CSS = """
<style>
:root {
  --hpw-navy:        #0a1628;
  --hpw-navy-mid:    #152342;
  --hpw-navy-light:  #1e3356;
  --hpw-offwhite:    #f8f6f2;
  --hpw-red:         #c1121f;
  --hpw-red-dark:    #9b0e18;
  --hpw-text:        #1a1a2e;
  --hpw-muted:       #6b7280;
  --hpw-border:      #e5e0d8;
}

/* ── Sidebar ──────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
  background-color: var(--hpw-navy) !important;
  border-right: 1px solid var(--hpw-navy-light);
}
section[data-testid="stSidebar"] * {
  color: #e8e4dc !important;
}
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
  font-family: 'DM Serif Display', serif !important;
  color: #ffffff !important;
  letter-spacing: 0.01em;
}
section[data-testid="stSidebar"] button {
  background: var(--hpw-navy-mid) !important;
  border: 1px solid var(--hpw-navy-light) !important;
  color: #e8e4dc !important;
}
section[data-testid="stSidebar"] button:hover {
  background: var(--hpw-navy-light) !important;
}

/* ── Main area ────────────────────────────────────────────── */
.main .block-container {
  background-color: var(--hpw-offwhite);
  font-family: 'Source Sans 3', sans-serif;
}
h1, h2, h3, h4 {
  font-family: 'DM Serif Display', serif !important;
  color: var(--hpw-navy) !important;
}

/* ── Primary button (Run Phase) ───────────────────────────── */
div.stButton > button[kind="primary"] {
  background-color: var(--hpw-red) !important;
  border-color: var(--hpw-red) !important;
  color: #ffffff !important;
  font-family: 'Source Sans 3', sans-serif !important;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  font-size: 0.82rem;
}
div.stButton > button[kind="primary"]:hover {
  background-color: var(--hpw-red-dark) !important;
  border-color: var(--hpw-red-dark) !important;
}

/* ── Log / code output ────────────────────────────────────── */
.stCode code, pre, code {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 0.76rem !important;
  line-height: 1.55 !important;
}

/* ── Phase stepper status pills ───────────────────────────── */
.hpw-badge-completed   { background:#dcfce7; color:#166534; padding:1px 7px; border-radius:10px; font-size:0.68rem; font-weight:700; display:inline-block; }
.hpw-badge-in_progress { background:#fef9c3; color:#92400e; padding:1px 7px; border-radius:10px; font-size:0.68rem; font-weight:700; display:inline-block; }
.hpw-badge-not_started { background:#f3f4f6; color:#6b7280; padding:1px 7px; border-radius:10px; font-size:0.68rem; font-weight:700; display:inline-block; }
.hpw-badge-blocked     { background:#fee2e2; color:#991b1b; padding:1px 7px; border-radius:10px; font-size:0.68rem; font-weight:700; display:inline-block; }

/* ── Tab strip ────────────────────────────────────────────── */
button[data-baseweb="tab"] {
  font-family: 'Source Sans 3', sans-serif !important;
  font-weight: 600 !important;
  font-size: 0.88rem !important;
  letter-spacing: 0.02em;
}
</style>
"""


def _load_config() -> dict:
    try:
        return json.loads(_CONFIG_PATH.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "hpw_base_dir": "/Users/kimhawk/Library/CloudStorage/Dropbox/Paper/Hematology_paper_writer",
            "csa_port": 8502,
        }


def _inject_theme() -> None:
    """Inject Google Fonts link and custom CSS. Must be called first in main()."""
    st.markdown(f'<link href="{_FONTS_URL}" rel="stylesheet">', unsafe_allow_html=True)
    st.markdown(_CSS, unsafe_allow_html=True)


# ── Phase navigation labels ───────────────────────────────────────────────────
_PHASE_LABELS = {
    0: "🔍 Research Intelligence",
    1: "💡 Topic Development",
    2: "📐 Research Design",
    3: "📰 Journal Strategy",
    4: "✍️  Manuscript Drafting",
    5: "✅ Publication Prep",
    6: "📤 Submission",
    7: "👥 Peer Review",
    8: "📢 Publication",
    9: "🔄 Resubmission",
}

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Hematology Paper Writer",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _init_session() -> None:
    defaults: dict = {
        "active_project": None,
        "active_phase": 0,
        "show_new_project_form": False,
        "csa_manifest": None,
        "_confirm_reset": False,
        # Legacy keys required by StatusDashboard / PhaseSelector
        "current_phase": 0,
        "phase_status": {
            i: {"name": label.split(" ", 1)[-1], "status": "not_started", "progress": 0}
            for i, label in _PHASE_LABELS.items()
        },
        "manuscript_data": {},
        "notebooklm_status": None,
        "notebooklm_integration": None,
        "uploaded_files": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _render_sidebar(config: dict) -> tuple[str | None, int]:
    """
    Render sidebar: project tree + phase stepper.
    Returns (active_project_dir, active_phase_num).
    """
    with st.sidebar:
        st.markdown("## 🩸 HPW")
        st.caption("Hematology Paper Writer")
        st.divider()

        tree = ProjectTree(config["hpw_base_dir"])
        tree.render()  # updates st.session_state["active_project"]

        active_project = st.session_state.get("active_project")

        if active_project:
            st.divider()
            st.markdown("### Phase")
            new_phase = tree.render_phase_stepper(
                st.session_state.get("active_phase", 0),
                active_project,
            )
            if new_phase != st.session_state.get("active_phase"):
                st.session_state["active_phase"] = new_phase
                st.rerun()

            st.divider()

        st.divider()

        # Two-step reset confirmation
        if not st.session_state.get("_confirm_reset"):
            if st.button("Reset session", use_container_width=True):
                st.session_state["_confirm_reset"] = True
                st.rerun()
        else:
            st.warning("Clear all session data?")
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("Yes, reset", type="primary", use_container_width=True):
                    keys = [k for k in st.session_state if k != "_confirm_reset"]
                    for k in keys:
                        del st.session_state[k]
                    st.rerun()
            with col_no:
                if st.button("Cancel", use_container_width=True):
                    st.session_state["_confirm_reset"] = False
                    st.rerun()

        st.caption("v3.0")

    return (
        st.session_state.get("active_project"),
        st.session_state.get("active_phase", 0),
    )


def _render_header(project_dir: str | None) -> None:
    col1, col2 = st.columns([4, 1])
    with col1:
        if project_dir:
            name = Path(project_dir).name
            st.title(f"🩸 {name}")
        else:
            st.title("🩸 Hematology Paper Writer")
            st.caption("Select or create a project in the sidebar to begin.")
    with col2:
        if project_dir:
            phase_label = _PHASE_LABELS.get(
                st.session_state.get("active_phase", 0), ""
            )
            st.caption(f"**{phase_label}**")


def main() -> None:
    _inject_theme()  # Must be first — injects CSS before any widget renders
    _init_session()
    config = _load_config()

    active_project, active_phase = _render_sidebar(config)
    st.session_state.current_phase = active_phase
    _render_header(active_project)

    if not active_project:
        return

    st.divider()

    tab_manuscript, tab_documents, tab_pipeline, tab_analysis, tab_status = st.tabs([
        "Manuscript", "Documents", "CRF Pipeline", "Analysis", "Status"
    ])

    with tab_manuscript:
        panel = PhasePanel()
        panel.render(active_phase, active_project)

    with tab_documents:
        DocumentsTab(active_project).render()

    with tab_pipeline:
        PipelineTab(active_project).render()

    with tab_analysis:
        AnalysisTab(active_project).render()

    with tab_status:
        StatusDashboard(config=config).render()


if __name__ == "__main__":
    main()
