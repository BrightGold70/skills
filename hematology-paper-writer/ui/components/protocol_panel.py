"""
ProtocolPanel: protocol document upload and extraction preview for Phase 2.

Wraps `hpw load-protocol` CLI call and renders protocol_params.json contents.
Extracted from phase_panel.py to keep PhasePanel lean.
"""

import json
from pathlib import Path
from typing import Optional

import streamlit as st


class ProtocolPanel:
    """Full Phase 2 protocol management: upload, re-parse, delete, preview."""

    def render(self, project_dir: str) -> None:
        """
        Renders the complete Phase 2 protocol section:
          1. Existing protocol files (Re-parse / Delete)
          2. New protocol file uploader
          3. Extraction preview from protocol_params.json
        """
        from .log_stream import run_with_log
        from cli_runner import build_hpw_args

        protocol_dir = Path(project_dir) / "docs" / "protocol"
        params_file = Path(project_dir) / "data" / "protocol_params.json"
        project_name = Path(project_dir).name

        # ── Existing protocol files ───────────────────────────────────
        existing = self._list_protocols(protocol_dir)
        if existing:
            st.markdown("#### Existing Protocol Files")
            for proto_file in existing:
                col_name, col_reparse, col_del = st.columns([3, 1, 1])
                col_name.markdown(f"`{proto_file.name}`")

                if col_reparse.button("Re-parse", key=f"reparse_{proto_file.name}"):
                    cmd = build_hpw_args(
                        "load-protocol",
                        {"file_path": str(proto_file), "--project": project_name},
                    )
                    st.markdown("**Re-parsing protocol…**")
                    run_with_log(cmd=cmd, key="reparse_protocol", cwd=project_dir)
                    st.rerun()

                if col_del.button("🗑 Delete", key=f"delete_{proto_file.name}"):
                    st.session_state[f"confirm_delete_{proto_file.name}"] = True

                if st.session_state.get(f"confirm_delete_{proto_file.name}"):
                    st.warning(f"Delete `{proto_file.name}`?")
                    c1, c2 = st.columns(2)
                    if c1.button("Yes, delete", key=f"confirm_yes_{proto_file.name}", type="primary"):
                        proto_file.unlink()
                        st.session_state.pop(f"confirm_delete_{proto_file.name}", None)
                        st.rerun()
                    if c2.button("Cancel", key=f"confirm_no_{proto_file.name}"):
                        st.session_state.pop(f"confirm_delete_{proto_file.name}", None)
                        st.rerun()
            st.divider()

        # ── Upload new protocol ───────────────────────────────────────
        st.markdown("#### Upload New Protocol Document")
        uploaded = st.file_uploader(
            "Protocol (DOCX or PDF)",
            type=["docx", "pdf"],
            key="phase2_protocol_upload",
        )
        if uploaded:
            dest = self._save_upload(uploaded, protocol_dir)
            st.success(f"Saved: `{dest}`")
            cmd = build_hpw_args(
                "load-protocol",
                {"file_path": str(dest), "--project": project_name},
            )
            st.markdown("**Extracting protocol parameters…**")
            run_with_log(cmd=cmd, key="load_protocol", cwd=project_dir)

        # ── Extraction preview ────────────────────────────────────────
        if params_file.exists():
            try:
                params = json.loads(params_file.read_text())
                st.divider()
                self._render_extraction_preview(params, params_file)
            except (json.JSONDecodeError, OSError):
                pass
        elif not existing and not uploaded:
            st.caption("No protocol_params.json yet — upload a protocol above.")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _list_protocols(self, protocol_dir: Path) -> list[Path]:
        """Return .docx and .pdf files in protocol_dir, newest first."""
        if not protocol_dir.exists():
            return []
        files = list(protocol_dir.glob("*.docx")) + list(protocol_dir.glob("*.pdf"))
        return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)

    def _save_upload(self, uploaded_file, protocol_dir: Path) -> Path:
        """Save UploadedFile to protocol_dir. Returns saved path."""
        protocol_dir.mkdir(parents=True, exist_ok=True)
        dest = protocol_dir / uploaded_file.name
        dest.write_bytes(uploaded_file.getvalue())
        return dest

    def _render_extraction_preview(self, params: dict, params_file: Path) -> None:
        """Compact metrics card for extracted protocol parameters."""
        st.markdown("#### Extracted Parameters")
        cols = st.columns(3)
        cols[0].metric("Study type", params.get("study_type") or "—")
        cols[1].metric("Sample size (N)", params.get("sample_size_n") or "—")
        cols[2].metric("Primary endpoint", params.get("primary_endpoint") or "—")

        if params.get("secondary_endpoints"):
            st.caption("Secondary endpoints: " + ", ".join(params["secondary_endpoints"]))
        if params.get("reporting_guideline"):
            st.caption(f"Reporting guideline: **{params['reporting_guideline']}**")

        if params.get("missing_fields"):
            st.warning("Missing protocol fields: " + ", ".join(params["missing_fields"]))
            self._render_missing_fields_form(params, params_file)

    def _render_missing_fields_form(self, params: dict, params_file: Path) -> None:
        """Inline form to fill in missing protocol fields and save back."""
        st.markdown("**Fill in missing fields manually:**")
        updated = False
        for field in list(params.get("missing_fields", [])):
            field_label = field.replace("_", " ").title()
            if field in ("sample_size_n",):
                val = st.number_input(
                    field_label, min_value=0, value=0, key=f"missing_{field}"
                )
                if val > 0:
                    params[field] = val
                    updated = True
            elif field in ("power", "alpha", "dropout_rate"):
                val = st.number_input(
                    field_label, min_value=0.0, max_value=1.0,
                    value=0.0, step=0.01, format="%.2f", key=f"missing_{field}",
                )
                if val > 0.0:
                    params[field] = val
                    updated = True
            else:
                val = st.text_input(field_label, value="", key=f"missing_{field}")
                if val.strip():
                    params[field] = val.strip()
                    updated = True

        if updated and st.button("Save missing fields", key="save_missing_fields"):
            params["missing_fields"] = [
                f for f in params["missing_fields"] if not params.get(f)
            ]
            params_file.write_text(json.dumps(params, indent=2, default=str))
            st.success("Saved to protocol_params.json")
            st.rerun()
