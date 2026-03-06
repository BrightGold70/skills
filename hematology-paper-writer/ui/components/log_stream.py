"""
LogStream: subprocess execution with live log streaming to Streamlit.
"""

import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional

import streamlit as st


@dataclass
class RunResult:
    returncode: int = 0
    duration_s: float = 0.0
    summary: str = ""
    output_files: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def default_summary_parser(output: str) -> RunResult:
    """Generic parser for HPW/CSA CLI stdout."""
    lines = output.strip().split("\n") if output.strip() else []
    warnings = [l.strip() for l in lines if l.strip().startswith("⚠")]
    output_files = []
    summary = "Done"

    for line in reversed(lines):
        stripped = line.strip()
        if stripped and any(
            kw in stripped for kw in ("Done in", "Completed", "saved", "written", "✓")
        ):
            summary = stripped
            break

    for line in lines:
        for ext in (".docx", ".md", ".csv", ".json", ".pdf", ".eps"):
            if ext in line and any(
                kw in line.lower() for kw in ("→", "saved", "written", "output")
            ):
                for token in line.split():
                    token = token.strip("→").strip()
                    if ext in token and not token.startswith("-"):
                        output_files.append(token)

    return RunResult(
        summary=summary,
        warnings=warnings,
        output_files=list(dict.fromkeys(output_files)),  # deduplicate
    )


def run_with_log(
    cmd: List[str],
    key: str,
    summary_parser: Optional[Callable[[str], RunResult]] = None,
    max_lines: int = 200,
    env: Optional[dict] = None,
    cwd: Optional[str] = None,
) -> Optional[RunResult]:
    """
    Run cmd as subprocess, stream stdout+stderr into a Streamlit code block.
    Returns RunResult on completion, None on launch failure.

    Uses st.empty() delta-generator for immediate WebSocket updates
    without needing a full Streamlit rerun.
    """
    if summary_parser is None:
        summary_parser = default_summary_parser

    state_key = f"log_{key}"
    st.session_state[state_key] = []

    placeholder = st.empty()
    start = time.time()

    try:
        with subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
            cwd=cwd,
        ) as proc:
            for line in proc.stdout:
                st.session_state[state_key].append(line.rstrip())
                placeholder.code(
                    "\n".join(st.session_state[state_key][-max_lines:]),
                    language="",
                )
            proc.wait()

        duration = time.time() - start
        full_output = "\n".join(st.session_state[state_key])
        result = summary_parser(full_output)
        result.duration_s = duration
        result.returncode = proc.returncode

        _render_summary_card(result, key)
        return result

    except FileNotFoundError as e:
        st.error(f"Command not found: `{cmd[0]}`\n\n{e}")
        return None


# Alias for CSA components that import run_with_log_csa by name
run_with_log_csa = run_with_log


def _render_summary_card(result: RunResult, key: str) -> None:
    """Compact status card: icon, summary, duration, warnings, download buttons."""
    icon = "✅" if result.returncode == 0 else "❌"
    col1, col2, col3 = st.columns([1, 7, 2])

    with col1:
        st.markdown(f"### {icon}")

    with col2:
        st.markdown(f"**{result.summary}** &nbsp;·&nbsp; {result.duration_s:.1f}s")
        for w in result.warnings:
            st.warning(w)

    with col3:
        for fpath in result.output_files:
            p = Path(fpath)
            if p.exists():
                with open(p, "rb") as f:
                    st.download_button(
                        label=f"⬇ {p.suffix.lstrip('.')}",
                        data=f.read(),
                        file_name=p.name,
                        key=f"dl_{key}_{p.name}",
                    )
