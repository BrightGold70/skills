"""
StatusDashboard Component
Real-time progress tracking and status visualization.
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional


class StatusDashboard:
    """Displays real-time status and progress across all phases."""

    def render(self):
        """Render status dashboard."""
        # Overall progress
        st.subheader("📊 Project Status")
        self._render_overall_progress()

        st.divider()

        # Current phase details
        current_phase = st.session_state.current_phase
        st.subheader(f"🎯 Phase {current_phase} Status")
        self._render_phase_details(current_phase)

        st.divider()

        # NotebookLM status
        st.subheader("📚 Reference Libraries")
        self._render_notebooklm_status()

        st.divider()

        # Recent activity
        st.subheader("📝 Recent Activity")
        self._render_activity_log()

    def _render_overall_progress(self):
        """Render overall project progress."""
        phase_status = st.session_state.phase_status

        # Calculate statistics
        total_phases = len(phase_status)
        completed = sum(1 for p in phase_status.values() if p["status"] == "completed")
        in_progress = sum(
            1 for p in phase_status.values() if p["status"] == "in_progress"
        )
        not_started = sum(
            1 for p in phase_status.values() if p["status"] == "not_started"
        )

        overall_progress = (completed / total_phases) * 100

        # Progress columns
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Completed", f"{completed}/{total_phases}")
        with col2:
            st.metric("In Progress", in_progress)
        with col3:
            st.metric("Not Started", not_started)
        with col4:
            st.metric("Overall", f"{overall_progress:.0f}%")

        # Progress bar
        st.progress(overall_progress / 100)

    def _render_phase_details(self, phase_num: int):
        """Render details for specific phase."""
        phase_info = st.session_state.phase_status[phase_num]

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**Status:** {phase_info['status'].replace('_', ' ').title()}")
            st.markdown(f"**Progress:** {phase_info['progress']}%")

        with col2:
            # Status actions
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

        # Progress slider
        new_progress = st.slider(
            "Update Progress",
            min_value=0,
            max_value=100,
            value=phase_info["progress"],
            step=5,
        )

        if new_progress != phase_info["progress"]:
            st.session_state.phase_status[phase_num]["progress"] = new_progress
            if new_progress == 100:
                st.session_state.phase_status[phase_num]["status"] = "completed"
            elif new_progress > 0:
                st.session_state.phase_status[phase_num]["status"] = "in_progress"
            st.rerun()

    def _render_notebooklm_status(self):
        """Render NotebookLM library status."""
        ref_path = "/Users/kimhawk/Library/CloudStorage/Dropbox/Paper/Hematology_paper_writer/References"

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

        for idx, (col, (name, info)) in enumerate(zip(cols, libraries.items())):
            with col:
                st.markdown(f"**{info['icon']} {name}**")

                # Check if files exist
                from pathlib import Path

                all_exist = all(
                    (Path(ref_path) / src).exists() for src in info["sources"]
                )

                if all_exist:
                    st.success("✅ Ready")
                else:
                    st.error("❌ Missing")

                st.caption(f"{len(info['sources'])} sources")

    def _render_activity_log(self):
        """Render recent activity log."""
        # Placeholder for activity log
        activities = [
            {"time": "Just now", "action": "Application started"},
            {"time": "—", "action": "No recent activity"},
        ]

        for activity in activities[:5]:
            st.markdown(f"- **{activity['time']}**: {activity['action']}")

        if st.button("📝 Add Note"):
            st.text_input("Activity note", key="activity_note")
