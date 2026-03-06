"""
PipelineTab: wraps CSA CRF pipeline CLI as a step-by-step UI.

Steps: validate → run (transform+export) using the CSA pipeline CLI.
"""

import sys
from pathlib import Path

import streamlit as st

from components.log_stream import run_with_log as run_with_log_csa

# CSA CRF pipeline CLI — resolved relative to skill root
# ui/components/csa/ → parents[4] = skill root
_CSA_PIPELINE_CLI = (
    Path(__file__).parents[4]
    / "clinical-statistics-analyzer"
    / "scripts"
    / "crf_pipeline"
    / "cli.py"
)


def _build_pipeline_cmd(step: str, project_dir: str) -> list[str]:
    """Build CLI command for a pipeline step."""
    data_dir = str(Path(project_dir) / "data")
    crf_csv = str(Path(project_dir) / "data" / "crf_consolidated.csv")

    if step == "validate":
        return [
            sys.executable, str(_CSA_PIPELINE_CLI),
            "validate",
            "--data-path", crf_csv,
        ]
    elif step == "run":
        return [
            sys.executable, str(_CSA_PIPELINE_CLI),
            "run",
            "--input-dir", data_dir,
            "--output-dir", data_dir,
            "--skip-validation",
        ]
    return []


class PipelineTab:
    """Step-by-step CRF pipeline runner."""

    STEPS = [
        ("validate", "Validate CRF data"),
        ("run",      "Run pipeline (transform + export)"),
    ]

    def __init__(self, project_dir: str):
        self.project_dir = project_dir

    def render(self) -> None:
        crf_csv = Path(self.project_dir) / "data" / "crf_consolidated.csv"

        if not crf_csv.exists():
            st.warning(
                "No `crf_consolidated.csv` found. "
                "Upload and process patient CRFs in the **Documents** tab first."
            )
            return

        st.success(f"CRF data ready: `{crf_csv.name}` ({crf_csv.stat().st_size // 1024 + 1} KB)")
        st.markdown("Run the pipeline steps in order:")

        for step_id, step_label in self.STEPS:
            st.markdown(f"##### {step_label}")
            status_key = f"csa_pipeline_{step_id}_done"
            done = st.session_state.get(status_key, False)

            col_status, col_btn = st.columns([3, 1])
            col_status.markdown("✅ Done" if done else "⏳ Not run")

            if col_btn.button(f"▶ Run", key=f"pipeline_run_{step_id}", use_container_width=True):
                cmd = _build_pipeline_cmd(step_id, self.project_dir)
                result = run_with_log_csa(
                    cmd=cmd,
                    key=f"pipeline_{step_id}",
                    cwd=self.project_dir,
                )
                if result and result.returncode == 0:
                    st.session_state[status_key] = True
                    st.rerun()

            st.markdown("---")
