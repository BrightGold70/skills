"""
PhasePanel: registry-driven form renderer for HPW phases.

Loads phase_registry.json and renders the appropriate Streamlit widgets
for the selected phase, then executes the underlying CLI command.
"""

import json
from pathlib import Path
from typing import Any, Optional

import streamlit as st

from .log_stream import run_with_log
from cli_runner import build_hpw_args

_REGISTRY_PATH = Path(__file__).parent.parent / "phase_registry.json"


class PhasePanel:
    """Renders a phase form from phase_registry.json and runs the CLI command."""

    def __init__(self, registry_path: Path = _REGISTRY_PATH) -> None:
        self._registry = self._load_registry(registry_path)

    def render(self, phase_num: int, project_dir: str) -> None:
        """
        Render the form widgets and Run button for the given phase.
        On successful run, marks phase as 'completed' in .phase_status.json.
        """
        spec = self._registry.get(str(phase_num))
        if spec is None:
            st.error(f"No registry entry for phase {phase_num}.")
            return

        icon = spec.get("icon", "")
        label = spec.get("label", f"Phase {phase_num}")
        description = spec.get("description", "")
        command = spec.get("command")

        st.subheader(f"{icon} Phase {phase_num}: {label}")
        if description:
            st.caption(description)

        # Phases with no CLI command show an info panel
        if command is None:
            self._render_info_panel(phase_num, spec, project_dir)
            return

        # Show CSA badge and manifest import banner (Phase 4 only)
        if phase_num == 4:
            from .csa_badge import CSABadge
            CSABadge().render(project_dir)
            self._render_csa_manifest_banner(project_dir)

        # Render form widgets
        widget_values = self._render_widgets(spec.get("widgets", []), phase_num, project_dir)

        st.divider()
        run_key = f"run_phase_{phase_num}"

        if st.button(f"▶ Run {label}", key=run_key, type="primary", use_container_width=True):
            # Validate required fields
            missing = [
                w["label"]
                for w in spec.get("widgets", [])
                if w.get("required") and not widget_values.get(w["key"])
            ]
            if missing:
                st.error(f"Required fields missing: {', '.join(missing)}")
                return

            cmd = build_hpw_args(command, widget_values)
            st.markdown(f"**Running:** `{' '.join(cmd[2:])}`")  # hide python path

            result = run_with_log(
                cmd=cmd,
                key=f"phase_{phase_num}",
                cwd=project_dir,
            )

            if result and result.returncode == 0:
                from .project_tree import update_phase_status
                update_phase_status(project_dir, phase_num, "completed")

    # ------------------------------------------------------------------
    # Widget rendering
    # ------------------------------------------------------------------

    def _render_widgets(
        self, widget_specs: list[dict], phase_num: int, project_dir: str
    ) -> dict[str, Any]:
        """Render all widgets for a phase and return {key: value} dict."""
        values: dict[str, Any] = {}

        for spec in widget_specs:
            key = spec["key"]
            widget_key = f"phase_{phase_num}_{key}"
            value = self._render_widget(spec, widget_key, project_dir)
            values[key] = value

        return values

    def _render_widget(self, spec: dict, widget_key: str, project_dir: str) -> Any:
        """Dispatch to the correct Streamlit widget based on spec['type']."""
        wtype = spec.get("type", "text")
        label = spec.get("label", spec["key"])
        default = spec.get("default")
        placeholder = spec.get("placeholder", "")

        if wtype == "text":
            # Pre-populate from session state if CSA manifest sets it
            preset = st.session_state.get(f"preset_{spec['key']}", "")
            return st.text_input(
                label,
                value=preset or (default or ""),
                placeholder=placeholder,
                key=widget_key,
            )

        elif wtype == "textarea":
            return st.text_area(
                label,
                value=default or "",
                height=spec.get("height", 100),
                key=widget_key,
            )

        elif wtype == "number":
            return st.number_input(
                label,
                min_value=spec.get("min", 0),
                max_value=spec.get("max", 10000),
                value=int(default or spec.get("min", 0)),
                step=1,
                key=widget_key,
            )

        elif wtype == "dropdown":
            options = spec.get("options", [])
            # Check for journal preset set in Phase 3 (Journal Strategy)
            preset_key = spec["key"].lstrip("-").replace("-", "_")
            preset = st.session_state.get(f"preset_{preset_key}")
            effective_default = preset if (preset and preset in options) else default
            default_idx = options.index(effective_default) if effective_default in options else 0
            return st.selectbox(label, options=options, index=default_idx, key=widget_key)

        elif wtype == "multiselect":
            options = spec.get("options", [])
            defaults = default if isinstance(default, list) else ([default] if default else [])
            return st.multiselect(label, options=options, default=defaults, key=widget_key)

        elif wtype == "toggle":
            return st.toggle(label, value=bool(default), key=widget_key)

        elif wtype == "file_picker":
            # Scan project docs dirs for manuscript files; show as selectbox
            search_dirs = [
                Path(project_dir) / "docs" / "manuscripts",
                Path(project_dir) / "docs" / "drafts",
                Path(project_dir) / "docs" / "submissions",
                Path(project_dir) / "docs",
            ]
            extensions = spec.get("extensions", [".md", ".docx", ".txt"])
            found: list[Path] = []
            for d in search_dirs:
                if d.exists():
                    for ext in extensions:
                        found.extend(sorted(d.glob(f"*{ext}"), key=lambda p: p.stat().st_mtime, reverse=True))
            # Deduplicate preserving order
            seen: set[str] = set()
            unique_files: list[Path] = []
            for f in found:
                key_str = str(f)
                if key_str not in seen:
                    seen.add(key_str)
                    unique_files.append(f)

            if not unique_files:
                st.caption("No manuscript files found in docs/. Use Phase 4 to create a draft first.")
                return st.text_input(label, value=default or "", placeholder="path/to/manuscript.md", key=widget_key)

            options = [str(f) for f in unique_files]
            display = [f.name for f in unique_files]
            idx = st.selectbox(
                label,
                options=range(len(options)),
                format_func=lambda i: display[i],
                key=widget_key,
            )
            return options[idx]

        elif wtype == "file_upload":
            uploaded = st.file_uploader(
                label,
                type=spec.get("accept", None),
                key=widget_key,
            )
            if uploaded:
                # Save to project docs/protocol/ and return the path
                save_dir = Path(project_dir) / "docs" / "protocol"
                save_dir.mkdir(parents=True, exist_ok=True)
                dest = save_dir / uploaded.name
                dest.write_bytes(uploaded.getvalue())
                return str(dest)
            return None

        else:
            st.warning(f"Unknown widget type '{wtype}' for '{label}'")
            return None

    # ------------------------------------------------------------------
    # Info panel (phases with command: null)
    # ------------------------------------------------------------------

    def _render_info_panel(self, phase_num: int, spec: dict, project_dir: str) -> None:
        """
        For phases without a CLI command (e.g. Research Design, Journal Strategy),
        show contextual information from the project's protocol_params.json.
        """
        if phase_num == 2:  # Research Design
            from .protocol_panel import ProtocolPanel
            ProtocolPanel().render(project_dir)

        elif phase_num == 3:  # Journal Strategy
            _JOURNAL_SPECS = {
                "blood_research":  ("Blood Research",  3500, "Mid",       "Vancouver", "STROBE/CONSORT"),
                "blood":           ("Blood",           4500, "High",      "Vancouver", "CONSORT"),
                "blood_advances":  ("Blood Advances",  3500, "High",      "Vancouver", "CONSORT"),
                "jco":             ("JCO",             5000, "Very High", "Numbered",  "CONSORT"),
                "bjh":             ("BJH",             3500, "High",      "Vancouver", "STROBE"),
                "leukemia":        ("Leukemia",        4000, "High",      "Vancouver", "CONSORT"),
                "haematologica":   ("Haematologica",   3500, "High",      "Vancouver", "STROBE/CONSORT"),
            }

            current = st.session_state.get("preset_journal", "blood_research")
            if current not in _JOURNAL_SPECS:
                current = "blood_research"

            selected = st.selectbox(
                "Target journal",
                options=list(_JOURNAL_SPECS.keys()),
                format_func=lambda x: _JOURNAL_SPECS[x][0],
                index=list(_JOURNAL_SPECS.keys()).index(current),
                key="journal_strategy_selector",
            )
            st.session_state["preset_journal"] = selected
            st.success(f"✓ **{_JOURNAL_SPECS[selected][0]}** selected — journal pre-filled in Phase 1 and Phase 4.")

            name, wlimit, impact, ref_style, guidelines = _JOURNAL_SPECS[selected]
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Word limit", f"{wlimit:,}")
            col2.metric("Impact", impact)
            col3.metric("References", ref_style)
            col4.metric("Guidelines", guidelines)

            st.caption(
                "This selection pre-populates the journal dropdown in Phase 1 and Phase 4."
            )
            st.divider()
            st.markdown("**All journals at a glance:**")
            rows = "\n".join(
                f"| {v[0]} | {v[1]:,} | {v[2]} | {v[3]} |"
                for v in _JOURNAL_SPECS.values()
            )
            st.markdown(
                "| Journal | Words | Impact | Ref style |\n"
                "|---------|-------|--------|----------|\n" + rows
            )

    # ------------------------------------------------------------------
    # CSA manifest integration (Phase 4)
    # ------------------------------------------------------------------

    def _render_csa_manifest_banner(self, project_dir: str) -> None:
        """Show import banner if hpw_manifest.json is available in project."""
        manifest_file = Path(project_dir) / "data" / "hpw_manifest.json"
        if not manifest_file.exists():
            return

        st.success(
            "CSA statistical results available. "
            "Click **Import** to pre-populate the Statistical Methods section."
        )
        if st.button("Import CSA results into draft", key="import_csa_manifest"):
            try:
                manifest = json.loads(manifest_file.read_text())
                # Store for use by the topic text widget via preset key
                if "study_summary" in manifest:
                    st.session_state["preset_topic"] = manifest["study_summary"]
                st.session_state["csa_manifest"] = manifest
                st.success("CSA results imported into session.")
            except (json.JSONDecodeError, OSError) as e:
                st.error(f"Could not read hpw_manifest.json: {e}")

    # ------------------------------------------------------------------
    # Registry loading
    # ------------------------------------------------------------------

    @staticmethod
    def _load_registry(path: Path) -> dict:
        try:
            return json.loads(path.read_text()).get("phases", {})
        except (FileNotFoundError, json.JSONDecodeError) as e:
            st.error(f"Cannot load phase_registry.json: {e}")
            return {}
