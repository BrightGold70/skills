"""Claude caller contracts for listed non-Python production writes."""
from __future__ import annotations

import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile

import pytest

from non_py_gate_support import (
    DEFAULT_AUTHOR_LINE, assert_authorship, build_fixture, claude_author_env,
    default_authorship_env, member_fixture, newline_name_fixture, run_claude,
    selection_fixture, set_test_state, skip_unless_case_insensitive, stub_tree,
    task_text, two_record_fixture, write_file,
)
from tdd_gate_support import write_plan, write_state


@pytest.fixture
def root(tmp_path):
    # Full hostile text lives in the plan; control characters in the Write
    # target itself are correctly refused before identity resolution.
    return build_fixture(tmp_path / "repo'quoted%H-MAD-MARKER", "absent")


def _expect(root, relative, expected, kind="", *, property, author=False,
            env=None, hook=None):
    env = claude_author_env() if env is None else env
    if author:
        assert_authorship(env, root, "f")
    kwargs = {} if hook is None else {"hook": hook}
    result = run_claude(root, root / relative, env, **kwargs)
    assert result.decision == expected, (
        f"{property}: expected {expected.upper()} kind={kind}, received {result!r}")
    if kind:
        assert result.kind == kind, f"{property}: expected kind={kind}, received {result!r}"
    return result


def test_claude_tmp_dot_py_denies(root):
    directory = Path(tempfile.mkdtemp(dir="/tmp"))
    try:
        target = write_file(directory, ".py")
        _expect(root, str(target), "deny", "no-test-resolved",
                property="an out-of-root dot-py file under /tmp must deny")
    finally:
        shutil.rmtree(directory)


@pytest.mark.parametrize("source,alias", [("x.py", "note.txt"), (".py", "note.txt"),
                                         ("x.py", "note.md"), ("X.PY", "note.txt")])
def test_claude_tmp_hard_link_to_python_denies(root, source, alias):
    directory = Path(tempfile.mkdtemp(dir="/tmp"))
    try:
        source_path = write_file(directory, source)
        target = directory / alias
        os.link(source_path, target)
        _expect(root, str(target), "deny", "no-test-resolved",
                property="a temporary report hard-linked to Python must deny")
    finally:
        shutil.rmtree(directory)


def test_claude_tmp_hard_link_without_python_allows(root):
    directory = Path(tempfile.mkdtemp(dir="/tmp"))
    try:
        source = write_file(directory, "other.txt")
        target = directory / "note.txt"
        os.link(source, target)
        _expect(root, str(target), "allow",
                property="a temporary report with only non-Python hard links may write")
    finally:
        shutil.rmtree(directory)


@pytest.mark.parametrize("relative", ["scripts/.py", ".py", ".PY"])
def test_claude_dot_py_unlisted_denies(root, relative):
    write_file(root, relative)
    _expect(root, relative, "deny", "no-test-resolved", author=True,
            property="an unlisted dot-py production file requires a resolved test")


@pytest.mark.parametrize("relative", ["tests/.py", "docs/.py"])
def test_claude_dot_py_exempt_allows(root, relative):
    write_file(root, relative)
    _expect(root, relative, "allow",
            property="dot-py files under tests or docs are exempt")


def test_claude_dot_py_listed_absent_test_denies(root):
    write_file(root, "scripts/.py")
    write_plan(root, "f", task_text(1, ("scripts/.py",), "tests/test_tool.py"))
    _expect(root, "scripts/.py", "deny", "test-missing", author=True,
            property="a listed dot-py production file with an absent test must deny")


def test_claude_listed_absent_test_denies(root):
    _expect(root, "scripts/tool.sh", "deny", "test-missing", author=True,
            property="listed shell write must reach listing then judge its absent test")


def test_claude_listed_passing_test_denies(root):
    set_test_state(root, "passing")
    _expect(root, "scripts/tool.sh", "deny", "test-passing", author=True,
            property="listed shell write requires RED rather than a passing test")


def test_claude_listed_extensionless_absent_test_denies(root):
    _expect(root, "bin/launch", "deny", "test-missing", author=True,
            property="listed extensionless write must judge its absent test")


def test_claude_default_authorship_refuses_a_listed_target(root, tmp_path):
    env = default_authorship_env(tmp_path / "bin")
    assert_authorship(env, root, "f", DEFAULT_AUTHOR_LINE)
    _expect(root, "scripts/tool.sh", "deny", "codex-authorship", env=env,
            property="listed code-like write must preserve Codex authorship refusal")


def test_claude_selection_s2_denies(tmp_path):
    root = selection_fixture(tmp_path / "repo", "S2")
    result = _expect(root, "scripts/tool.sh", "deny", "test-missing", author=True,
                     property="S2 must judge least listed basename hard.sh with its absent test")
    assert "scripts/hard.sh" in result.reason, "S2 must select hard.sh rather than tool.sh"
    assert "tests/test_hard.py" in result.reason, "S2 must resolve the selected Task's test"


def test_claude_symlink_alias_denies(root):
    (root / "scripts/alias.sh").symlink_to("tool.sh")
    _expect(root, "scripts/alias.sh", "deny", "test-missing", author=True,
            property="symlink alias must judge its listed referent")


def test_claude_case_fold_spelling_denies(root):
    skip_unless_case_insensitive(root)
    _expect(root, "scripts/TOOL.SH", "deny", "test-missing", author=True,
            property="existing target case variant must retain its listing")


def test_claude_hard_link_denies(root):
    os.link(root / "scripts/tool.sh", root / "scripts/hard.sh")
    _expect(root, "scripts/hard.sh", "deny", "test-missing", author=True,
            property="same-directory hard link must resolve the listed identity")


def test_claude_unreadable_plan_is_judge_error(root):
    write_plan(root, "f", "").write_bytes(b"\xff\xfe")
    result = _expect(root, "scripts/other.sh", "deny", "judge-error",
                     property="unreadable active plan makes code-like listing undecidable")
    assert "listing is undecidable" in result.reason, (
        f"unreadable plan must use listing-specific refusal: {result!r}")


@pytest.mark.parametrize("target", ["scripts/tool.sh", "scripts/other.sh"])
def test_claude_unreadable_state_is_judge_error(root, target):
    (root / "docs/.bkit-memory.json").write_bytes(b"\xff\xfe")
    result = _expect(root, target, "deny", "judge-error",
                     property="unreadable governing state makes code-like listing undecidable")
    assert "listing is undecidable" in result.reason, (
        f"unreadable listing state must use listing-specific refusal: {result!r}")


def test_claude_listed_beside_unreadable_absent_test_denies(tmp_path):
    root = two_record_fixture(tmp_path / "repo", listed=True)
    _expect(root, "scripts/hard.sh", "deny", "test-missing", author=True,
            property="readable listing outranks unreadable sibling and judges its absent test")


def test_claude_unlisted_beside_unreadable_is_judge_error(tmp_path):
    root = two_record_fixture(tmp_path / "repo", listed=False)
    result = _expect(root, "scripts/hard.sh", "deny", "judge-error",
                     property="unmatched target beside unreadable sibling is undecidable")
    assert "listing is undecidable" in result.reason, (
        f"unreadable sibling must use listing-specific refusal: {result!r}")


@pytest.mark.parametrize("test_state", ["absent", "failing"])
def test_claude_listed_symlink_to_a_newline_name(tmp_path, test_state):
    root = newline_name_fixture(tmp_path / "repo", test_state)
    _expect(root, "scripts/alias.sh", "deny" if test_state == "absent" else "allow",
            "test-missing" if test_state == "absent" else "", author=True,
            property="listed symlink must retain the referent's trailing newline through listing decode")


@pytest.mark.parametrize("member", ["a.bash", "Makefile", "Dockerfile", ".gitignore",
                                    ".dockerignore", "x.md.sh", "x.mdx"])
def test_claude_excluded_member_denies(tmp_path, member):
    relative = f"scripts/{member}" if member == "a.bash" else member
    entry = f"./{member}" if member in {"Makefile", "Dockerfile"} else relative
    root = member_fixture(tmp_path / "repo", entry, entry)
    _expect(root, relative, "deny", "test-missing", author=True,
            property=f"listed {member} is outside the doc/data suffixes and requires RED")


def test_claude_mixed_hard_links_deny(root):
    write_file(root, "x.sh")
    os.link(root / "x.sh", root / "x.md")
    write_plan(root, "f", task_text(1, ("x.sh",), "tests/test_tool.py"))
    _expect(root, "x.md", "deny", "test-missing", author=True,
            property="one doc/data name cannot exempt a listed code-like hard-link identity")


def _listing_stub(root, tmp_path, stdout, rc=0, docdata=""):
    hook = stub_tree(tmp_path / "stub", stdout, rc, docdata)
    return _expect(root, "scripts/tool.sh", "deny", "judge-error", hook=hook,
                   property=f"listing/docdata transport must fail closed for {stdout!r} rc={rc}")


def test_claude_listing_zero_lines_is_judge_error(root, tmp_path):
    result = _listing_stub(root, tmp_path, "")
    assert "zero or several lines" in result.reason, "empty listing output must fail the line-count guard"


def test_claude_listing_several_lines_is_judge_error(root, tmp_path):
    result = _listing_stub(root, tmp_path, "TDD-LISTING: not-listed\nTDD-LISTING: not-listed\n")
    assert "zero or several lines" in result.reason, "multiple listing lines must fail the line-count guard"


def test_claude_listing_nonzero_exit_is_judge_error(root, tmp_path):
    result = _listing_stub(root, tmp_path, "TDD-LISTING: not-listed\n", 2)
    assert "listing verb exited rc=2" in result.reason, "listing exit status must be checked before not-listed"


def test_claude_listing_unrecognised_line_is_judge_error(root, tmp_path):
    result = _listing_stub(root, tmp_path, "TDD-LISTING: gibberish\n")
    assert "no well-formed listing line" in result.reason, "unknown listing token must reach protocol refusal"


def test_claude_listing_foreign_target_is_judge_error(root, tmp_path):
    result = _listing_stub(root, tmp_path, "TDD-LISTING: listed target=%2Felsewhere\n")
    assert "named a target it was not given" in result.reason, "listing must select only a supplied canonical name"


def test_claude_malformed_docdata_line_is_judge_error(root, tmp_path):
    result = _listing_stub(root, tmp_path, "TDD-LISTING: not-listed\n",
                           docdata=" print('docdata maybe')")
    assert "invalid docdata line" in result.reason, "malformed docdata must fail strict classification parse"


def test_claude_missing_docdata_line_is_judge_error(root, tmp_path):
    _listing_stub(root, tmp_path, "TDD-LISTING: not-listed\n", docdata=" pass")


def test_claude_listed_failing_test_allows(root):
    set_test_state(root, "failing")
    _expect(root, "scripts/tool.sh", "allow", author=True,
            property="listed code-like write with measured RED is allowed")


def test_claude_unlisted_code_like_allows(root):
    _expect(root, "scripts/other.sh", "allow", author=True,
            property="active unlisted code-like target is allowed")


def test_claude_unlisted_doc_data_allows(root):
    _expect(root, "notes.md", "allow", author=True,
            property="unlisted doc/data target is allowed")


def test_claude_default_authorship_allows_unlisted_doc_data(root, tmp_path):
    env = default_authorship_env(tmp_path / "bin")
    assert_authorship(env, root, "f", DEFAULT_AUTHOR_LINE)
    _expect(root, "notes.md", "allow", env=env,
            property="doc/data skips default Codex authorship refusal")


def test_claude_no_state_file_allows_a_listed_target(root):
    (root / "docs/.bkit-memory.json").unlink()
    _expect(root, "scripts/tool.sh", "allow", property="no state file exempts a listed code-like target")


def test_claude_inactive_record_allows_a_listed_target(root):
    write_state(root, {"f": {"phase": "step4"}})
    _expect(root, "scripts/tool.sh", "allow", property="inactive state exempts a listed code-like target")


@pytest.mark.parametrize("directory", ["tests", "fixtures", "docs"])
def test_claude_listed_exempt_location_allows(root, directory):
    target = f"{directory}/tool.sh"
    write_file(root, target)
    write_plan(root, "f", task_text(1, (target,), "tests/test_tool.py"))
    _expect(root, target, "allow", author=True,
            property=f"listed code-like target in exempt location {directory} skips judge")


def test_claude_selection_s1_allows(tmp_path):
    root = selection_fixture(tmp_path / "repo", "S1")
    _expect(root, "scripts/tool.sh", "allow", author=True,
            property="S1 selects least listed basename hard.sh and its failing test")


@pytest.mark.parametrize("case", ["plan-entry-case", "absent-leaf-case", "other-directory-hard-link"])
def test_claude_residual_spellings_allow(root, case):
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
    _expect(root, target, "allow", author=True,
            property=f"residual {case} remains outside target-side alias closure")


def test_claude_absent_plan_allows(root):
    (root / "docs/01-plan/features/f.impl-plan.md").unlink()
    _expect(root, "scripts/other.sh", "allow", property="absent active plan means target is unlisted")


@pytest.mark.parametrize("case", ["plan-notes", "plan-readme", "state-notes", "state-readme"])
def test_claude_doc_data_allows_in_undecidable_states(root, case):
    source, target = case.split("-")
    if source == "plan":
        write_plan(root, "f", "").write_bytes(b"\xff\xfe")
    else:
        (root / "docs/.bkit-memory.json").write_bytes(b"\xff\xfe")
    _expect(root, "notes.md" if target == "notes" else "README.md", "allow",
            property=f"doc/data skips undecidable {source} reads")


def test_claude_listed_beside_unreadable_failing_test_allows(tmp_path):
    root = two_record_fixture(tmp_path / "repo", listed=True)
    set_test_state(root, "failing")
    _expect(root, "scripts/hard.sh", "allow", author=True,
            property="readable listing with RED outranks an unreadable sibling plan")


def test_claude_listed_doc_data_allows(root):
    _expect(root, "README.md", "allow", author=True,
            property="listed doc/data skips the absent test")


@pytest.mark.parametrize("spelling", ["on-disk", "case-variant"])
def test_claude_listed_upper_case_doc_data_allows(root, spelling):
    if spelling == "case-variant":
        skip_unless_case_insensitive(root)
    _expect(root, "CHANGES.MD" if spelling == "on-disk" else "changes.md", "allow", author=True,
            property="doc/data classification uses canonical names and ASCII case folding")


@pytest.mark.parametrize("suffix", [".md", ".yaml", ".yml", ".json", ".toml", ".txt", ".rst", ".cfg", ".ini"])
def test_claude_doc_data_member_allows(tmp_path, suffix):
    lower, upper = f"x{suffix}", f"y{suffix.upper()}"
    root = member_fixture(tmp_path / "repo", lower, upper)
    for target in (lower, upper):
        _expect(root, target, "allow", author=True,
                property=f"listed doc/data suffix {suffix} skips absent test in either case")


def test_claude_out_of_root_code_like_allows_beside_unreadable_state(root, tmp_path):
    (root / "docs/.bkit-memory.json").write_bytes(b"\xff\xfe")
    outside = build_fixture(tmp_path / "outside", "absent")
    _expect(root, outside / "scripts/tool.sh", "allow",
            property="outside-root code-like write skips unreadable project state")


def test_claude_directory_stays_judge_error_where_state_may_exist(root):
    version = subprocess.run(["/bin/bash", "--version"], capture_output=True, text=True,
                             timeout=10, check=True)
    if "version 3.2." not in version.stdout:
        pytest.skip("empty-array set -u directory residual belongs to /bin/bash 3.2")
    _expect(root, "scripts", "deny", "judge-error",
            property="directory with possible state retains bash 3.2 empty-array refusal")


def test_claude_directory_allows_where_no_state_can_exist(root):
    (root / "docs/.bkit-memory.json").unlink()
    _expect(root, "scripts", "allow", property="directory with no possible state remains allowed")


@pytest.mark.parametrize("case,expected", [("unlisted-with-state", 4),
                                          ("doc-data-with-state", 2),
                                          ("unlisted-without-state", 2)],
                         ids=["unlisted-with-state", "doc-data-with-state", "unlisted-without-state"])
def test_claude_process_count(root, tmp_path, case, expected):
    target = "notes.md" if case == "doc-data-with-state" else "scripts/other.sh"
    if case == "unlisted-without-state":
        (root / "docs/.bkit-memory.json").unlink()
    bin_dir = tmp_path / "logging-bin"
    bin_dir.mkdir()
    launches = tmp_path / "python-launches"
    shim = bin_dir / "python3"
    shim.write_text("#!/bin/sh\n"
                    f"printf '%s\\n' launch >> {shlex.quote(str(launches))}\n"
                    f"exec {shlex.quote(sys.executable)} \"$@\"\n", encoding="utf-8")
    shim.chmod(0o755)
    env = claude_author_env()
    env["PATH"] = str(bin_dir) + os.pathsep + env["PATH"]
    _expect(root, target, "allow", env=env,
            property=f"process-count scenario {case} must allow the unlisted write")
    count = len(launches.read_text(encoding="utf-8").splitlines())
    assert count == expected, (
        f"{case}: expected {expected} Python launches including two baseline launches, received {count}")
