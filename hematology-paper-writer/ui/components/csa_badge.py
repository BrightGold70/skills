"""
CSABadge: badge showing CSA connection status for active HPW project.

In the unified single-app architecture, reads directly from st.session_state
(set by AnalysisTab._write_hpw_manifest) — no filesystem polling needed.
"""

import json
from pathlib import Path
from typing import Optional

import streamlit as st


class CSABadge:
    """Badge widget showing CSA data availability and import controls."""

    def __init__(self, csa_port: int = 8502):
        self.csa_port = csa_port  # retained for config compatibility

    def render(self, project_dir: str) -> None:
        """
        Render badge in current Streamlit context.
          - Manifest in session → green "● CSA data ready" + Import button
          - Not found           → grey "○ CSA not connected"
        """
        manifest = st.session_state.get("csa_manifest")

        if manifest:
            label = manifest.get("script_label", "analysis")
            ts = str(manifest.get("run_timestamp", ""))[:10]
            st.success(f"● CSA data ready — {label} ({ts})")
            if st.button("Import results", key="csa_badge_import", use_container_width=True):
                self._load_manifest_into_session(manifest)
        else:
            st.caption("○ No CSA results yet — run analysis in Statistical Analysis tab")

    def _load_manifest_into_session(self, manifest: dict) -> None:
        """Apply manifest presets to Phase 4 session keys."""
        if manifest.get("study_summary"):
            st.session_state["preset_topic"] = manifest["study_summary"]
        st.success("CSA results applied to Phase 4.")
