"""
AnalysisTab: disease-module script runner for CSA app (unified UI).

Loads script_registry.json → disease radio → script selectbox →
auto-populated params from protocol_params → Run → Export to HPW manifest.
"""

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import streamlit as st

from components.log_stream import run_with_log as run_with_log_csa

# ui/components/csa/ → parents[2] = ui/
_REGISTRY_PATH = Path(__file__).parents[2] / "script_registry.json"

# ui/components/csa/ → parents[4] = skill root
_CSA_SCRIPTS_DIR = (
    Path(__file__).parents[4] / "clinical-statistics-analyzer" / "scripts"
)


class AnalysisTab:
    """Script runner with protocol auto-population and HPW manifest export."""

    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        self.registry = self._load_registry()

    def render(self) -> None:
        if not self.registry:
            st.error("Cannot load script_registry.json")
            return

        modules = list(self.registry.get("modules", {}).keys())
        if not modules:
            st.error("No modules found in script_registry.json")
            return

        # ── Disease module selector ───────────────────────────────────
        selected_module = st.radio(
            "Disease module",
            options=modules,
            format_func=lambda m: self.registry["modules"][m]["label"],
            horizontal=True,
            key="csa_disease_module",
        )

        module_scripts = self.registry["modules"][selected_module]["scripts"]
        script_ids = list(module_scripts.keys())

        # ── Script selector ───────────────────────────────────────────
        selected_script_id = st.selectbox(
            "Analysis script",
            options=script_ids,
            format_func=lambda s: module_scripts[s]["label"],
            key=f"csa_script_{selected_module}",
        )
        script_spec = module_scripts[selected_script_id]

        st.caption(f"Script: `{script_spec['file']}`")
        st.divider()

        # ── Parameter widgets (auto-populated from protocol_params) ───
        initial_values = self._auto_populate_params(script_spec)
        param_values = self._render_params(script_spec, initial_values)

        st.divider()

        col_run, col_export = st.columns(2)
        run_clicked = col_run.button(
            f"▶ Run {script_spec['label']}",
            key=f"csa_run_{selected_script_id}",
            type="primary",
            use_container_width=True,
        )
        export_clicked = col_export.button(
            "Export to HPW",
            key="csa_export_manifest",
            use_container_width=True,
            disabled="csa_last_run_results" not in st.session_state,
        )

        if run_clicked:
            missing = [
                p["label"]
                for p in script_spec.get("params", [])
                if p.get("required") and not param_values.get(p["key"])
            ]
            if missing:
                st.error(f"Required fields missing: {', '.join(missing)}")
            else:
                cmd = self._build_r_cmd(script_spec, param_values)
                result = run_with_log_csa(
                    cmd=cmd,
                    key=f"run_{selected_script_id}",
                    cwd=str(self.project_dir),
                )
                if result and result.returncode == 0:
                    st.session_state["csa_last_run_results"] = {
                        "script_id": selected_script_id,
                        "script_label": script_spec["label"],
                        "module": selected_module,
                        "params": param_values,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    st.rerun()

        if export_clicked:
            self._write_hpw_manifest(st.session_state["csa_last_run_results"])

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _auto_populate_params(self, script_spec: dict) -> dict:
        """Pre-fill param defaults from protocol_params session state."""
        protocol_params = st.session_state.get("protocol_params") or {}
        values = {}
        for p in script_spec.get("params", []):
            proto_key = p.get("protocol_key")
            if proto_key and proto_key in protocol_params:
                raw = protocol_params[proto_key]
                values[p["key"]] = ", ".join(raw) if isinstance(raw, list) else raw
            elif "default" in p:
                values[p["key"]] = p["default"]
        return values

    def _render_params(self, script_spec: dict, initial: dict) -> dict[str, Any]:
        """Render parameter widgets; return {key: value} dict."""
        values: dict[str, Any] = {}
        for p in script_spec.get("params", []):
            key = p["key"]
            widget_key = f"csa_param_{script_spec['file']}_{key}"
            ptype = p.get("type", "text")
            label = p.get("label", key)
            default = initial.get(key, p.get("default"))

            if ptype == "text":
                values[key] = st.text_input(label, value=str(default or ""), key=widget_key)
            elif ptype == "number":
                values[key] = st.number_input(
                    label,
                    min_value=p.get("min", 0.0),
                    max_value=p.get("max", 10000.0),
                    value=float(default or p.get("min", 0)),
                    key=widget_key,
                )
            elif ptype == "dropdown":
                options = p.get("options", [])
                idx = options.index(default) if default in options else 0
                values[key] = st.selectbox(label, options=options, index=idx, key=widget_key)
            elif ptype == "multiselect":
                options = p.get("options", [])
                defaults = default if isinstance(default, list) else ([default] if default else [])
                values[key] = st.multiselect(label, options=options, default=defaults, key=widget_key)
            elif ptype == "file_picker":
                data_dir = self.project_dir / "data"
                found = list(data_dir.glob("*.csv")) + list(data_dir.glob("*.xlsx")) if data_dir.exists() else []
                if found:
                    found_sorted = sorted(found, key=lambda f: f.stat().st_mtime, reverse=True)
                    opts = [str(f) for f in found_sorted]
                    disp = [f.name for f in found_sorted]
                    idx = st.selectbox(
                        label,
                        options=range(len(opts)),
                        format_func=lambda i: disp[i],
                        key=widget_key,
                    )
                    values[key] = opts[idx]
                else:
                    values[key] = st.text_input(label, value="", placeholder="path/to/data.csv", key=widget_key)
            else:
                values[key] = st.text_input(label, value=str(default or ""), key=widget_key)

        return values

    def _build_r_cmd(self, script_spec: dict, params: dict) -> list[str]:
        """Build Rscript command from script spec and param values."""
        script_file = _CSA_SCRIPTS_DIR / script_spec["file"]
        rscript = shutil.which("Rscript") or "Rscript"
        cmd = [rscript, str(script_file)]
        for key, val in params.items():
            if val is None or val == "" or val == []:
                continue
            if isinstance(val, list):
                cmd.append(f"--{key}={','.join(str(v) for v in val)}")
            else:
                cmd.append(f"--{key}={val}")
        return cmd

    def _write_hpw_manifest(self, run_results: dict) -> None:
        """Write hpw_manifest.json and set session state directly (0s lag)."""
        manifest = {
            "version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": "CSA Analysis Tab",
            "module": run_results.get("module"),
            "script_id": run_results.get("script_id"),
            "script_label": run_results.get("script_label"),
            "run_timestamp": run_results.get("timestamp"),
            "params": run_results.get("params", {}),
            "study_summary": (
                st.session_state.get("protocol_params", {}).get("primary_endpoint", "")
            ),
        }
        out = self.project_dir / "data" / "hpw_manifest.json"
        out.write_text(json.dumps(manifest, indent=2, default=str))

        # Direct session state write — eliminates 10s polling lag
        st.session_state["csa_manifest"] = manifest
        if manifest.get("study_summary"):
            st.session_state["preset_topic"] = manifest["study_summary"]

        st.success(f"HPW manifest written → `data/hpw_manifest.json`\nCSA badge updated instantly.")

    @staticmethod
    def _load_registry() -> dict:
        try:
            return json.loads(_REGISTRY_PATH.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
