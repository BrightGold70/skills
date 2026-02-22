"""
PhaseSelector Component
Visual phase timeline with status indicators.
"""

import streamlit as st
from typing import Dict, Optional


class PhaseSelector:
    """Visual phase selection with timeline display."""

    PHASES = {
        0: {
            "name": "Research Intelligence",
            "icon": "🔍",
            "description": "Query references via NotebookLM",
            "color": "#3498db",
        },
        1: {
            "name": "Topic Development",
            "icon": "💡",
            "description": "Define PICO and research questions",
            "color": "#9b59b6",
        },
        2: {
            "name": "Research Design",
            "icon": "📐",
            "description": "Study methodology planning",
            "color": "#e74c3c",
        },
        3: {
            "name": "Journal Strategy",
            "icon": "📰",
            "description": "Target journal selection",
            "color": "#f39c12",
        },
        4: {
            "name": "Manuscript Drafting",
            "icon": "✍️",
            "description": "Generate manuscript sections",
            "color": "#2ecc71",
        },
        5: {
            "name": "Publication Prep",
            "icon": "✅",
            "description": "Checklist and compliance",
            "color": "#1abc9c",
        },
        6: {
            "name": "Submission",
            "icon": "📤",
            "description": "Cover letter and forms",
            "color": "#34495e",
        },
        7: {
            "name": "Peer Review",
            "icon": "👥",
            "description": "Response to reviewers",
            "color": "#16a085",
        },
        8: {
            "name": "Publication",
            "icon": "📢",
            "description": "Proofs and dissemination",
            "color": "#27ae60",
        },
        9: {
            "name": "Resubmission",
            "icon": "🔄",
            "description": "Revision for other journals",
            "color": "#8e44ad",
        },
    }

    STATUS_ICONS = {
        "not_started": "⚪",
        "in_progress": "🟡",
        "completed": "✅",
        "blocked": "🔴",
    }

    def render(self):
        """Render phase selector UI."""
        # Current phase highlight
        current = st.session_state.current_phase
        phase_info = self.PHASES[current]

        st.markdown(f"### Current: {phase_info['icon']} Phase {current}")
        st.markdown(f"**{phase_info['name']}**")
        st.caption(phase_info["description"])

        st.markdown("---")

        # Timeline display
        st.markdown("### Phase Timeline")

        for phase_num in range(10):
            phase = self.PHASES[phase_num]
            status = st.session_state.phase_status[phase_num]["status"]
            is_current = phase_num == current

            self._render_phase_row(phase_num, phase, status, is_current)

        # Phase selection
        st.markdown("---")
        selected_phase = st.selectbox(
            "Jump to Phase",
            options=list(range(10)),
            format_func=lambda x: f"Phase {x}: {self.PHASES[x]['name']}",
            index=current,
        )

        if selected_phase != current:
            if st.button("🔄 Switch Phase", use_container_width=True):
                st.session_state.current_phase = selected_phase
                st.rerun()

    def _render_phase_row(
        self, phase_num: int, phase: dict, status: str, is_current: bool
    ):
        """Render a single phase row in the timeline."""
        status_icon = self.STATUS_ICONS.get(status, "⚪")

        # Styling based on status
        if is_current:
            bg_color = phase["color"]
            text_color = "white"
            border = f"3px solid {phase['color']}"
        elif status == "completed":
            bg_color = "#ecf0f1"
            text_color = "#27ae60"
            border = "1px solid #bdc3c7"
        elif status == "in_progress":
            bg_color = "#fff9e6"
            text_color = "#f39c12"
            border = "1px solid #f39c12"
        else:
            bg_color = "white"
            text_color = "#7f8c8d"
            border = "1px solid #ecf0f1"

        # Render phase card
        st.markdown(
            f"""
        <div style="
            background-color: {bg_color};
            color: {text_color};
            border: {border};
            border-radius: 8px;
            padding: 10px;
            margin: 5px 0;
            display: flex;
            align-items: center;
            cursor: pointer;
        ">
            <span style="font-size: 20px; margin-right: 10px;">{phase["icon"]}</span>
            <div style="flex-grow: 1;">
                <strong>Phase {phase_num}</strong><br/>
                <small>{phase["name"]}</small>
            </div>
            <span style="font-size: 16px;">{status_icon}</span>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def set_phase_status(self, phase_num: int, status: str, progress: int = 0):
        """Update phase status."""
        st.session_state.phase_status[phase_num]["status"] = status
        st.session_state.phase_status[phase_num]["progress"] = progress

    def get_current_phase(self) -> int:
        """Get current phase number."""
        return st.session_state.current_phase

    def get_phase_info(self, phase_num: Optional[int] = None) -> dict:
        """Get phase information."""
        if phase_num is None:
            phase_num = self.get_current_phase()
        return self.PHASES.get(phase_num, {})
