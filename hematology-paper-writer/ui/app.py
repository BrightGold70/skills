"""
Hematology Paper Writer - Streamlit UI Application
Main entry point for the user-friendly web interface.
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.file_manager import FileManager
from components.phase_selector import PhaseSelector
from components.status_dashboard import StatusDashboard
from components.action_panel import ActionPanel


# Page configuration
st.set_page_config(
    page_title="Hematology Paper Writer",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="expanded",
)


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "current_phase" not in st.session_state:
        st.session_state.current_phase = 0

    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files = []

    if "phase_status" not in st.session_state:
        st.session_state.phase_status = {
            0: {
                "name": "Research Intelligence",
                "status": "not_started",
                "progress": 0,
            },
            1: {"name": "Topic Development", "status": "not_started", "progress": 0},
            2: {"name": "Research Design", "status": "not_started", "progress": 0},
            3: {"name": "Journal Strategy", "status": "not_started", "progress": 0},
            4: {"name": "Manuscript Drafting", "status": "not_started", "progress": 0},
            5: {"name": "Publication Prep", "status": "not_started", "progress": 0},
            6: {"name": "Submission", "status": "not_started", "progress": 0},
            7: {"name": "Peer Review", "status": "not_started", "progress": 0},
            8: {"name": "Publication", "status": "not_started", "progress": 0},
            9: {"name": "Resubmission", "status": "not_started", "progress": 0},
        }

    if "notebooklm_status" not in st.session_state:
        st.session_state.notebooklm_status = None

    if "notebooklm_integration" not in st.session_state:
        st.session_state.notebooklm_integration = None

    if "manuscript_data" not in st.session_state:
        st.session_state.manuscript_data = {}


def render_sidebar():
    """Render the sidebar with navigation and settings."""
    with st.sidebar:
        st.title("🩸 HPW")
        st.markdown("*Hematology Paper Writer*")
        st.divider()

        # Quick navigation
        st.subheader("Quick Actions")

        if st.button("📚 Initialize Notebooks", use_container_width=True):
            st.session_state.notebooklm_status = "initializing"
            st.rerun()

        if st.button("🔄 Reset Session", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        st.divider()

        # Reference status
        st.subheader("Reference Libraries")
        ref_path = "/Users/kimhawk/Library/CloudStorage/Dropbox/Paper/Hematology_paper_writer/References"
        ref_exists = Path(ref_path).exists()

        if ref_exists:
            st.success("✅ References mounted")
        else:
            st.error("❌ References not found")
            st.info("Mount LaCie drive at:\n`{}`".format(ref_path))

        st.divider()

        # About
        st.markdown("---")
        st.markdown("**v3.0** | Rebuild in Progress")


def render_header():
    """Render the main header."""
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        st.title("Hematology Paper Writer")
        st.markdown("*AI-powered manuscript preparation for hematology research*")

    with col2:
        st.metric("Current Phase", f"Phase {st.session_state.current_phase}")

    with col3:
        total_progress = (
            sum(p["progress"] for p in st.session_state.phase_status.values()) / 10
        )
        st.metric("Overall Progress", f"{total_progress:.0f}%")


def main():
    """Main application entry point."""
    initialize_session_state()
    render_sidebar()
    render_header()

    st.divider()

    # Create three-column layout
    col1, col2 = st.columns([1, 2])

    with col1:
        # Left column: File Manager and Phase Selector
        st.subheader("📁 Reference Files")
        file_manager = FileManager()
        file_manager.render()

        st.divider()

        st.subheader("🎯 Phase Selection")
        phase_selector = PhaseSelector()
        phase_selector.render()

    with col2:
        # Right column: Status Dashboard and Action Panel
        tab1, tab2, tab3 = st.tabs(["📊 Status", "⚡ Actions", "📋 Manuscript"])

        with tab1:
            status_dashboard = StatusDashboard()
            status_dashboard.render()

        with tab2:
            action_panel = ActionPanel()
            action_panel.render()

        with tab3:
            st.subheader("Manuscript Content")
            st.info(
                "Manuscript content will appear here as you progress through phases."
            )

            if st.session_state.manuscript_data:
                for section, content in st.session_state.manuscript_data.items():
                    with st.expander(section):
                        st.text_area(
                            f"Edit {section}",
                            value=content,
                            height=200,
                            key=f"manuscript_{section}",
                        )
            else:
                st.markdown("*No manuscript content yet. Start with Phase 0 to begin.*")


if __name__ == "__main__":
    main()
