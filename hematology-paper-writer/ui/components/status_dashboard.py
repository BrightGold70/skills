"""
StatusDashboard Component
Real-time progress tracking and status visualization.
"""

from pathlib import Path

import streamlit as st


class StatusDashboard:
    """Displays real-time status and progress across all phases."""

    def __init__(self, config: dict | None = None) -> None:
        self._config = config or {}

    def render(self) -> None:
        """Render status dashboard."""
        st.subheader("📊 Project Status")
        self._render_overall_progress()

        st.divider()

        current_phase = st.session_state.current_phase
        st.subheader(f"🎯 Phase {current_phase} Status")
        self._render_phase_details(current_phase)

        st.divider()

        st.subheader("📚 Reference Libraries")
        self._render_notebooklm_status()

    def _render_overall_progress(self) -> None:
        """Render overall project progress."""
        phase_status = st.session_state.phase_status

        total_phases = len(phase_status)
        completed = sum(1 for p in phase_status.values() if p["status"] == "completed")
        in_progress = sum(
            1 for p in phase_status.values() if p["status"] == "in_progress"
        )
        not_started = sum(
            1 for p in phase_status.values() if p["status"] == "not_started"
        )
        overall_progress = (completed / total_phases) * 100

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Completed", f"{completed}/{total_phases}")
        with col2:
            st.metric("In Progress", in_progress)
        with col3:
            st.metric("Not Started", not_started)
        with col4:
            st.metric("Overall", f"{overall_progress:.0f}%")

        st.progress(overall_progress / 100)

    def _render_phase_details(self, phase_num: int) -> None:
        """Render details for specific phase."""
        phase_info = st.session_state.phase_status[phase_num]

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Status:** {phase_info['status'].replace('_', ' ').title()}")
            st.markdown(f"**Progress:** {phase_info['progress']}%")

        with col2:
            current_status = phase_info["status"]
            if current_status == "not_started":
                if st.button("▶️ Start Phase", use_container_width=True):
                    st.session_state.phase_status[phase_num]["status"] = "in_progress"
                    st.rerun()
            elif current_status == "in_progress":
                if st.button("✅ Mark Complete", use_container_width=True):
                    st.session_state.phase_status[phase_num]["status"] = "completed"
                    st.session_state.phase_status[phase_num]["progress"] = 100
                    st.rerun()
            elif current_status == "completed":
                if st.button("🔄 Reopen", use_container_width=True):
                    st.session_state.phase_status[phase_num]["status"] = "in_progress"
                    st.session_state.phase_status[phase_num]["progress"] = 50
                    st.rerun()

    def _render_notebooklm_status(self) -> None:
        """Render NotebookLM library status."""
        base_dir = self._config.get("hpw_base_dir", "")
        ref_path = str(Path(base_dir) / "References") if base_dir else ""

        if not ref_path:
            st.caption("Reference library path not configured in ui_config.json.")
            return

        libraries = {
            "Classification": {
                "sources": ["WHO_2022.pdf", "ICC_2022.pdf"],
                "icon": "📊",
            },
            "GVHD": {
                "sources": ["NIH_cGVHD_I.pdf", "NIH_cGVHD_II.pdf", "NIH_cGVHD_III.pdf"],
                "icon": "🏥",
            },
            "Therapeutic": {
                "sources": ["ELN_AML_2022.pdf", "ELN_CML_2025.pdf"],
                "icon": "💊",
            },
            "Nomenclature": {
                "sources": ["ISCN 2024.pdf", "HGVS Nomenclature 2024.pdf"],
                "icon": "🧬",
            },
        }

        cols = st.columns(len(libraries))
        for col, (name, info) in zip(cols, libraries.items()):
            with col:
                st.markdown(f"**{info['icon']} {name}**")
                all_exist = all(
                    (Path(ref_path) / src).exists() for src in info["sources"]
                )
                if all_exist:
                    st.success("✅ Ready")
                else:
                    st.error("❌ Missing")
                st.caption(f"{len(info['sources'])} sources")
