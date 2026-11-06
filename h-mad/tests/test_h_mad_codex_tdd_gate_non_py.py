"""Real Codex hook verdicts for listed non-Python production identities."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import tempfile

import pytest

from non_py_gate_support import (
    BASE_PRODUCTION, build_fixture, gate_env, member_fixture, newline_name_fixture,
    run_codex, selection_fixture, set_test_state, skip_unless_case_insensitive,
    task_text, two_record_fixture, write_file,
)
from tdd_gate_support import write_plan, write_state


@pytest.fixture
def root(tmp_path):
    return build_fixture(tmp_path / 'repo "agent" % H-MAD-MARKER\nnext', "absent")


def _expect(root, relative, expected, kind="", *, property="non-Python gate contract",
            add=False):
    result = run_codex(root, relative, gate_env(CODEX_PROJECT_DIR=str(root)), add=add)
    assert result.decision == expected, (
        f"{property}: expected {expected.upper()} kind={kind}, received {result}")
    assert result.rc == 0, f"{property}: hook protocol must exit zero: {result}"
    if kind:
        assert result.kind == kind, f"{property}: expected kind={kind}, received {result}"
    return result


@pytest.fixture
def under_tmp():
    directory = Path(tempfile.mkdtemp(dir="/tmp"))
    try:
        yield directory
    finally:
        shutil.rmtree(directory)


@pytest.mark.parametrize("name", [".py", ".PY"])
def test_codex_tmp_dot_py_denies_like_x_py(root, under_tmp, name):
    control_path = write_file(under_tmp, "x.py")
    target = write_file(under_tmp, name)
    control = _expect(root, str(control_path), "deny")
    result = run_codex(root, str(target), gate_env(CODEX_PROJECT_DIR=str(root)))
    assert result.rc == 0, f"hook protocol must exit zero: {result}"
    assert (result.decision, result.kind) == (control.decision, control.kind), result


def test_codex_tmp_dot_py_note_txt_allows(root, under_tmp):
    target = write_file(under_tmp, "note.txt")
    _expect(root, str(target), "allow")


@pytest.mark.parametrize("relative", ["scripts/.py", ".py", ".PY"])
def test_codex_dot_py_unlisted_denies(root, relative):
    write_file(root, relative)
    _expect(root, relative, "deny", "no-test-resolved",
            property="an unlisted dot-py production file requires a resolved test")


@pytest.mark.parametrize("relative", ["tests/.py", "docs/.py"])
def test_codex_dot_py_exempt_allows(root, relative):
    write_file(root, relative)
    _expect(root, relative, "allow",
            property="dot-py files under tests or docs are exempt")


def test_codex_dot_py_listed_absent_test_denies(root):
    write_file(root, "scripts/.py")
    write_plan(root, "f", task_text(1, ("scripts/.py",), "tests/test_tool.py"))
    _expect(root, "scripts/.py", "deny", "test-missing",
            property="a listed dot-py production file with an absent test must deny")


def test_codex_listed_absent_test_denies(root):
    _expect(root, "scripts/tool.sh", "deny", "test-missing",
            property="listed shell target must reach the judge with its absent test")


def test_codex_listed_passing_test_denies(root):
    set_test_state(root, "passing")
    _expect(root, "scripts/tool.sh", "deny", "test-passing",
            property="a listed shell target requires RED, not a passing test")


def test_codex_multi_target_patch_denies_on_the_listed_target(root):
    result = _expect(root, "scripts/other.sh\n@@\n-x\n+y\n*** Update File: scripts/tool.sh",
                     "deny", "test-missing", property="one listed target must deny a multi-target patch")
    assert "scripts/tool.sh" in result.reason, "denial must identify the listed target"


def test_codex_selection_s2_denies(tmp_path):
    root = selection_fixture(tmp_path / "repo", "S2")
    result = _expect(root, "scripts/tool.sh", "deny", "test-missing",
                     property="S2 must judge least listed basename hard.sh with its absent test")
    assert "scripts/hard.sh" in result.reason, "S2 must select hard.sh rather than tool.sh"
    assert "tests/test_hard.py" in result.reason, "S2 must resolve the selected Task's test"


def test_codex_symlink_alias_denies(root):
    (root / "scripts/alias.sh").symlink_to("tool.sh")
    _expect(root, "scripts/alias.sh", "deny", "test-missing",
            property="symlink alias must judge its listed referent")


def test_codex_case_fold_spelling_denies(root):
    skip_unless_case_insensitive(root)
    _expect(root, "scripts/TOOL.SH", "deny", "test-missing",
            property="existing target's case-variant spelling must retain its listing")


def test_codex_hard_link_denies(root):
    os.link(root / "scripts/tool.sh", root / "scripts/hard.sh")
    _expect(root, "scripts/hard.sh", "deny", "test-missing",
            property="same-directory hard link must resolve the listed name, not the name map")


def test_codex_unreadable_plan_is_judge_error(root):
    write_plan(root, "f", "").write_bytes(b"\xff\xfe")
    result = _expect(root, "scripts/other.sh", "deny", "judge-error",
                     property="unreadable active plan makes an unlisted code-like target undecidable")
    assert "listing is undecidable" in result.reason


@pytest.mark.parametrize("target", ["scripts/tool.sh", "scripts/other.sh"])
def test_codex_unreadable_state_is_judge_error(root, target):
    (root / "docs/.bkit-memory.json").write_bytes(b"\xff\xfe")
    _expect(root, target, "deny", "judge-error",
            property="unreadable governing state must fail closed for code-like targets")


def test_codex_listed_beside_unreadable_absent_test_denies(tmp_path):
    root = two_record_fixture(tmp_path / "repo", listed=True)
    _expect(root, "scripts/hard.sh", "deny", "test-missing",
            property="readable listing outranks unreadable sibling and judges its absent test")


def test_codex_unlisted_beside_unreadable_is_judge_error(tmp_path):
    root = two_record_fixture(tmp_path / "repo", listed=False)
    _expect(root, "scripts/hard.sh", "deny", "judge-error",
            property="without a readable match an unreadable sibling makes listing undecidable")


@pytest.mark.parametrize("test_state", ["absent", "failing"])
def test_codex_listed_symlink_to_a_newline_name(tmp_path, test_state):
    root = newline_name_fixture(tmp_path / "repo", test_state)
    _expect(root, "scripts/alias.sh", "deny" if test_state == "absent" else "allow",
            "test-missing" if test_state == "absent" else "",
            property="a symlink to a newline-ending basename must preserve its listed identity")


@pytest.mark.parametrize("member", ["a.bash", "Makefile", "Dockerfile", ".gitignore",
                                    ".dockerignore", "x.md.sh", "x.mdx"])
def test_codex_excluded_member_denies(tmp_path, member):
    relative = f"scripts/{member}" if member == "a.bash" else member
    entry = f"./{member}" if member in {"Makefile", "Dockerfile"} else relative
    root = member_fixture(tmp_path / "repo", entry, entry)
    _expect(root, relative, "deny", "test-missing",
            property=f"{member} is code-like, outside the nine doc/data suffixes")


def test_codex_mixed_hard_links_deny(root):
    write_file(root, "x.sh")
    os.link(root / "x.sh", root / "x.md")
    write_plan(root, "f", task_text(1, ("x.sh",), "tests/test_tool.py"))
    _expect(root, "x.md", "deny", "test-missing",
            property="one doc/data hard-link name cannot exempt a listed code-like identity")


def test_codex_listed_failing_test_allows(root):
    set_test_state(root, "failing")
    _expect(root, "scripts/tool.sh", "allow", property="a listed target with measured RED is allowed")


def test_codex_unlisted_code_like_allows(root):
    _expect(root, "scripts/other.sh", "allow", property="active unlisted shell target is allowed")


def test_codex_unlisted_doc_data_allows(root):
    _expect(root, "notes.md", "allow", property="unlisted doc/data target is allowed")


def test_codex_add_file_doc_data_allows(root):
    _expect(root, "notes.md", "allow", add=True,
            property="an Add File of an unlisted doc/data target is allowed")


def test_codex_add_file_listed_absent_script_denies_test_missing(root):
    (root / "scripts/tool.sh").unlink()
    assert not (root / "scripts/tool.sh").exists()
    _expect(root, "scripts/tool.sh", "deny", "test-missing", add=True,
            property="an Add File of a listed script absent on disk must judge its absent test")


def test_codex_selection_s1_allows(tmp_path):
    root = selection_fixture(tmp_path / "repo", "S1")
    _expect(root, "scripts/tool.sh", "allow",
            property="S1 must judge least listed basename hard.sh with its failing test")


@pytest.mark.parametrize("case", ["plan-entry-case", "absent-leaf-case", "other-directory-hard-link"])
def test_codex_residual_spellings_allow(root, case):
    target = "scripts/tool.sh"
    if case == "plan-entry-case":
        write_plan(root, "f", task_text(1, ("scripts/TOOL.SH",), "tests/test_tool.py"))
    elif case == "absent-leaf-case":
        (root / target).unlink()
        target = "scripts/TOOL.SH"
    else:
        (root / "elsewhere").mkdir()
        os.link(root / target, root / "elsewhere/hard.sh")
        target = "elsewhere/hard.sh"
    _expect(root, target, "allow", property=f"residual {case} must remain outside target-side alias closure")


def test_codex_absent_plan_allows(root):
    (root / "docs/01-plan/features/f.impl-plan.md").unlink()
    _expect(root, "scripts/other.sh", "allow", property="absent active plan means not listed")


@pytest.mark.parametrize("case", ["plan-notes", "plan-readme", "state-notes", "state-readme"])
def test_codex_doc_data_allows_in_undecidable_states(root, case):
    source, target = case.split("-")
    if source == "plan":
        write_plan(root, "f", "").write_bytes(b"\xff\xfe")
    else:
        (root / "docs/.bkit-memory.json").write_bytes(b"\xff\xfe")
    _expect(root, "notes.md" if target == "notes" else "README.md", "allow",
            property=f"doc/data must skip {source} reads even when undecidable")


def test_codex_listed_beside_unreadable_failing_test_allows(tmp_path):
    root = two_record_fixture(tmp_path / "repo", listed=True)
    set_test_state(root, "failing")
    _expect(root, "scripts/hard.sh", "allow",
            property="readable listing with RED outranks an unreadable sibling plan")


def test_codex_listed_doc_data_allows(root):
    _expect(root, "README.md", "allow", property="listed doc/data skips an absent test")


@pytest.mark.parametrize("spelling", ["on-disk", "case-variant"])
def test_codex_listed_upper_case_doc_data_allows(root, spelling):
    if spelling == "case-variant":
        skip_unless_case_insensitive(root)
    _expect(root, "CHANGES.MD" if spelling == "on-disk" else "changes.md", "allow",
            property="doc/data recognition uses canonical names and ASCII case folding")


@pytest.mark.parametrize("suffix", [".md", ".yaml", ".yml", ".json", ".toml", ".txt", ".rst", ".cfg", ".ini"])
def test_codex_doc_data_member_allows(tmp_path, suffix):
    lower, upper = f"x{suffix}", f"y{suffix.upper()}"
    root = member_fixture(tmp_path / "repo", lower, upper)
    for target in (lower, upper):
        _expect(root, target, "allow", property=f"listed doc/data suffix {suffix} skips the judge in either case")


@pytest.mark.parametrize("directory", ["tests", "fixtures", "docs"])
def test_codex_listed_exempt_location_allows(root, directory):
    target = f"{directory}/tool.sh"
    write_file(root, target)
    write_plan(root, "f", task_text(1, (target,), "tests/test_tool.py"))
    _expect(root, target, "allow", property=f"listed target in exempt location {directory} skips the judge")


def test_codex_listed_test_shaped_python_is_skipped(root):
    target = "scripts/test_helper.py"
    write_file(root, target)
    write_plan(root, "f", task_text(1, (target,), "tests/test_tool.py"))
    _expect(root, target, "allow", property="test-shaped Python cannot enter the code-like listing path")


def test_codex_directory_target_is_skipped(root):
    _expect(root, "scripts", "allow", property="existing directory has no names and must skip before listing")


def test_codex_no_state_file_allows_a_listed_target(root):
    (root / "docs/.bkit-memory.json").unlink()
    _expect(root, "scripts/tool.sh", "allow", property="a listed target without governing state is allowed")


def test_codex_inactive_record_allows_a_listed_target(root):
    write_state(root, {"f": {"phase": "step4"}})
    _expect(root, "scripts/tool.sh", "allow", property="a listed target under an inactive record is allowed")


def test_skip_unless_case_insensitive_skips_on_a_case_sensitive_volume(tmp_path, monkeypatch):
    # Probe the volume without the helper: its own name, its own read.
    (tmp_path / "VolumeProbe").touch()
    try:
        os.stat(tmp_path / "volumeprobe")
        volume_folds_case = True
    except FileNotFoundError:
        volume_folds_case = False
    (tmp_path / "VolumeProbe").unlink()

    # Arm 1, the real volume: returns where it folds, skips where it does not.
    try:
        skip_unless_case_insensitive(tmp_path)
        skipped = False
    except pytest.skip.Exception:
        skipped = True
    if skipped == volume_folds_case:
        pytest.fail(f"volume_folds_case={volume_folds_case} but helper skipped={skipped}")

    # Arm 2, forced folding: the helper must return on any volume.
    with monkeypatch.context() as m:
        m.setattr(os.path, "exists", lambda path: True)
        try:
            skip_unless_case_insensitive(tmp_path)
        except pytest.skip.Exception:
            pytest.fail("helper skipped although the opposite-case spelling exists")

    # Arm 3, forced non-folding: the helper must skip on any volume.
    with monkeypatch.context() as m:
        m.setattr(os.path, "exists", lambda path: False)
        with pytest.raises(pytest.skip.Exception):
            skip_unless_case_insensitive(tmp_path)

    assert not (tmp_path / "a").exists()
