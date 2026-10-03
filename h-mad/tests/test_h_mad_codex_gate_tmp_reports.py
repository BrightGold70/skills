"""Phase 5: codex may write its report under /tmp, and nothing else outside the root.

The gate already trusts `/tmp` for `h_mad_assemble_tdd.py --report-file`, which is
the path the orchestrator then hands codex as `<REPORT_FILE_PATH>`. But every
write outside the project root was refused while Phase 5 was active, so codex could
never write the report it had been told to write, and wrote it into the repo's
`tests/` instead (HemaSuite `guideline-web-evidence-admission`, 2026-10-03).

An out-of-root write is now admitted when it resolves under `/tmp` (which covers
`/private/tmp` and the session scratchpad) and is not a Python file. Still refused:
any `.py` (in any case spelling) outside the root, so codex cannot write production
code into another checkout that happens to live under `/tmp`; and anything outside
`/tmp`, including `$TMPDIR` under `/var/folders`.
"""
import os
import shutil
import tempfile
from pathlib import Path

import pytest

from test_h_mad_codex_tdd_gate_judge import _root, _run


def _add(path: str) -> dict:
    return {"tool_name": "apply_patch", "tool_input": {
        "patch": f"*** Begin Patch\n*** Add File: {path}\n+report\n*** End Patch\n"}}


@pytest.fixture
def under_tmp():
    d = Path(tempfile.mkdtemp(prefix="hmad-gate-", dir="/tmp"))
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.mark.parametrize("name", ["report.md", "report.md.done", "sub/report.txt"])
def test_a_report_under_tmp_is_allowed(tmp_path, under_tmp, name):
    root = _root(tmp_path)
    (under_tmp / "sub").mkdir()
    verdict, reason, _ = _run(root, _add(str(under_tmp / name)))
    assert verdict == "allow", reason


def test_the_private_tmp_spelling_is_allowed(tmp_path, under_tmp):
    root = _root(tmp_path)
    private = "/private" + str(under_tmp) if not str(under_tmp).startswith("/private") else str(under_tmp)
    if not Path(private).exists():
        pytest.skip("/tmp is not /private/tmp on this platform")
    verdict, reason, _ = _run(root, _add(private + "/report.md"))
    assert verdict == "allow", reason


def test_a_write_tool_report_under_tmp_is_allowed(tmp_path, under_tmp):
    root = _root(tmp_path)
    payload = {"tool_name": "Write", "tool_input": {"file_path": str(under_tmp / "r.md")}}
    verdict, reason, _ = _run(root, payload)
    assert verdict == "allow", reason


@pytest.mark.parametrize("name", ["prod.py", "prod.PY", "pkg/prod.pY"])
def test_python_under_tmp_is_still_refused(tmp_path, under_tmp, name):
    root = _root(tmp_path)
    verdict, reason, _ = _run(root, _add(str(under_tmp / name)))
    assert verdict == "deny", reason


def test_dotdot_out_of_tmp_is_refused(tmp_path, under_tmp):
    root = _root(tmp_path)
    escape = f"{under_tmp}/../../{str(tmp_path).lstrip('/')}/elsewhere.md"
    verdict, reason, _ = _run(root, _add(escape))
    assert verdict == "deny", reason


def test_a_symlink_under_tmp_pointing_outside_is_refused(tmp_path, under_tmp):
    root = _root(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    os.symlink(outside, under_tmp / "link")
    verdict, reason, _ = _run(root, _add(str(under_tmp / "link" / "r.md")))
    assert verdict == "deny", reason


def test_tmpdir_outside_tmp_is_still_refused(tmp_path):
    # pytest's tmp_path lives under $TMPDIR (/var/folders on macOS), not /tmp.
    root = _root(tmp_path)
    other = tmp_path / "elsewhere"
    other.mkdir()
    verdict, reason, _ = _run(root, _add(str(other / "report.md")))
    assert verdict == "deny", reason


def test_a_report_named_link_to_python_under_tmp_is_refused(tmp_path, under_tmp):
    # The .py check reads the RESOLVED name: a `.md` link whose target is a `.py`
    # would otherwise pass the name check and write Python through the link.
    root = _root(tmp_path)
    (under_tmp / "pkg").mkdir()
    (under_tmp / "pkg" / "prod.py").write_text("# production\n")
    os.symlink(under_tmp / "pkg" / "prod.py", under_tmp / "notes.md")
    verdict, reason, _ = _run(root, _add(str(under_tmp / "notes.md")))
    assert verdict == "deny", reason
