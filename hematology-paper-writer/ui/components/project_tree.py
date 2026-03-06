"""
ProjectTree: sidebar project navigator for HPW.

Lists manuscript projects from the HPW Dropbox base directory,
shows 10-phase completion status per project, and handles new project creation.
"""

import json
from pathlib import Path
from typing import Optional

import streamlit as st

# Phase labels matching phase_selector.py's PHASES dict (0-indexed)
_PHASE_LABELS = {
    0: ("🔍", "Research Intelligence"),
    1: ("💡", "Topic Development"),
    2: ("📐", "Research Design"),
    3: ("📰", "Journal Strategy"),
    4: ("✍️", "Manuscript Drafting"),
    5: ("✅", "Publication Prep"),
    6: ("📤", "Submission"),
    7: ("👥", "Peer Review"),
    8: ("📢", "Publication"),
    9: ("🔄", "Resubmission"),
}

_STATUS_BADGE = {
    "completed": "✅",
    "in_progress": "🟡",
    "not_started": "⚪",
    "blocked": "🔴",
}

_REQUIRED_SUBDIRS = ("docs", "data")


class ProjectTree:
    """Sidebar project navigator."""

    def __init__(self, base_dir: str) -> None:
        self.base_dir = Path(base_dir).expanduser()

    def render(self) -> Optional[str]:
        """
        Render sidebar project list. Returns the active project directory path,
        or None if no project is selected.
        """
        st.markdown("### Projects")

        if not self.base_dir.exists():
            st.error(
                f"HPW base directory not found:\n`{self.base_dir}`\n\n"
                "Check `ui/ui_config.json`."
            )
            return None

        if st.button("＋ New Project", use_container_width=True):
            st.session_state["show_new_project_form"] = True

        if st.session_state.get("show_new_project_form"):
            self._render_new_project_form()

        projects = self._list_projects()
        if not projects:
            st.caption("No projects found. Create one above.")
            return None

        active = st.session_state.get("active_project")

        for project_dir in projects:
            name = project_dir.name
            is_active = str(project_dir) == active
            phase_status = self._read_phase_status(project_dir)
            completed = sum(1 for s in phase_status.values() if s == "completed")

            with st.expander(
                f"{'▶ ' if is_active else ''}{name}  ({completed}/10)",
                expanded=is_active,
            ):
                # Phase progress mini-list
                for phase_num in range(10):
                    icon, label = _PHASE_LABELS[phase_num]
                    badge = _STATUS_BADGE.get(
                        phase_status.get(phase_num, "not_started"), "⚪"
                    )
                    st.markdown(
                        f"<small>{badge} {icon} {label}</small>",
                        unsafe_allow_html=True,
                    )

                if st.button("Open project", key=f"open_{name}", use_container_width=True):
                    st.session_state["active_project"] = str(project_dir)
                    st.session_state["active_phase"] = 0
                    st.rerun()

        return active

    def render_phase_stepper(self, active_phase: int, project_dir: str) -> int:
        """
        Render a vertical phase stepper with status badges.
        Each phase shows icon, name, and a colored status pill.
        Returns the newly selected phase number (unchanged if no click).
        """
        phase_status = self._read_phase_status(Path(project_dir))
        selected = active_phase

        for phase_num, (icon, label) in _PHASE_LABELS.items():
            status = phase_status.get(phase_num, "not_started")
            is_active = phase_num == active_phase
            active_bg = (
                "background:#1e3356;border-radius:6px;padding:3px 8px;"
                if is_active
                else "padding:3px 8px;"
            )
            badge_text = status.replace("_", " ")
            st.markdown(
                f'<div style="{active_bg}margin-bottom:2px;">'
                f'<span style="font-size:0.82rem;">{icon} {label}</span>&nbsp;'
                f'<span class="hpw-badge-{status}">{badge_text}</span>'
                f"</div>",
                unsafe_allow_html=True,
            )
            if st.button(
                "●" if is_active else "○",
                key=f"pnav_{phase_num}",
                help=f"Switch to {label}",
            ):
                selected = phase_num

        return selected

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _list_projects(self) -> list[Path]:
        """Return subdirs of base_dir that look like HPW projects, newest first."""
        projects = []
        try:
            for d in self.base_dir.iterdir():
                if d.is_dir() and not d.name.startswith("."):
                    if all((d / sub).exists() for sub in _REQUIRED_SUBDIRS):
                        projects.append(d)
        except PermissionError:
            st.warning(f"Cannot read `{self.base_dir}` — check permissions.")
        return sorted(projects, key=lambda p: p.stat().st_mtime, reverse=True)

    def _read_phase_status(self, project_dir: Path) -> dict[int, str]:
        """
        Read {project_dir}/.phase_status.json.
        Returns dict mapping phase number (int) → status string.
        Defaults all phases to 'not_started' if file absent.
        """
        status_file = project_dir / ".phase_status.json"
        base = {i: "not_started" for i in range(10)}
        if status_file.exists():
            try:
                data = json.loads(status_file.read_text())
                for k, v in data.items():
                    try:
                        base[int(k)] = v
                    except (ValueError, KeyError):
                        pass
            except (json.JSONDecodeError, OSError):
                pass
        return base

    def _render_new_project_form(self) -> None:
        """Inline form for creating a new project folder."""
        with st.form("new_project_form", clear_on_submit=True):
            name = st.text_input(
                "Project name",
                placeholder="e.g. Asciminib_CML_Review_2026",
            )
            submitted = st.form_submit_button("Create")
            if submitted:
                if not name.strip():
                    st.error("Project name cannot be empty.")
                else:
                    project_dir = self._create_project(name.strip())
                    if project_dir:
                        st.session_state["active_project"] = str(project_dir)
                        st.session_state["active_phase"] = 0
                        st.session_state["show_new_project_form"] = False
                        st.success(f"Created: {name}")
                        st.rerun()

    def _create_project(self, name: str) -> Optional[Path]:
        """Create the standard HPW project directory structure."""
        project_dir = self.base_dir / name
        try:
            for subdir in (
                "docs/submissions",
                "docs/manuscripts",
                "docs/drafts",
                "docs/protocol",
                "literature",
                "data",
            ):
                (project_dir / subdir).mkdir(parents=True, exist_ok=True)

            # Write initial phase status
            status_file = project_dir / ".phase_status.json"
            status_file.write_text(
                json.dumps({str(i): "not_started" for i in range(10)}, indent=2)
            )
            return project_dir
        except OSError as e:
            st.error(f"Could not create project directory:\n{e}")
            return None


def update_phase_status(project_dir: str, phase_num: int, status: str) -> None:
    """
    Update a single phase's status in the project's .phase_status.json.
    Called by PhasePanel after a successful run.
    """
    status_file = Path(project_dir) / ".phase_status.json"
    data = {str(i): "not_started" for i in range(10)}
    if status_file.exists():
        try:
            data = json.loads(status_file.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    data[str(phase_num)] = status
    status_file.write_text(json.dumps(data, indent=2))
