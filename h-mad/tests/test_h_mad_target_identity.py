"""Target identity and CANON record contract for both TDD gates."""
from __future__ import annotations

import importlib
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import quote_from_bytes

import pytest

from tdd_gate_support import assert_case_insensitive


@pytest.fixture
def identity(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    return importlib.import_module("h_mad_target_identity")


@pytest.fixture(autouse=True)
def hostile_stub_input(monkeypatch):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")


@pytest.fixture
def root(tmp_path):
    project = tmp_path / "repo"
    project.mkdir()
    return Path(os.path.realpath(project))


def _loop(root: Path) -> Path:
    src = root / "src"
    src.mkdir()
    (src / "loopa.py").symlink_to("loopb.py")
    (src / "loopb.py").symlink_to("loopa.py")
    return src / "loopa.py"


@pytest.mark.parametrize("disk,spelled", [("Case", "case"), ("Tests", "tests")],
                         ids=["m8-root", "m9-dir"])
def test_canonical_directory_returns_on_disk_spelling(identity, tmp_path, disk, spelled):
    assert_case_insensitive(tmp_path)
    (tmp_path / disk).mkdir()
    canonical = identity.canonical_directory(str(tmp_path / spelled))
    assert canonical.endswith("/" + disk), "F_GETPATH must return the on-disk directory case"


def test_hard_link_names_share_the_canonical_parent(identity, root):
    src = root / "src"
    src.mkdir()
    a, b = src / "prod.py", src / "test_prod.py"
    a.write_text("pass\n")
    os.link(a, b)
    assert os.stat(a).st_ino == os.stat(b).st_ino
    result = identity.canonicalise(str(root), "src/test_prod.py")
    assert result.names == ("prod.py", "test_prod.py")
    assert result.target == str(a)
    assert result.unresolvable is False


def test_leaf_symlink_scans_the_referent_parent(identity, root):
    src, tests = root / "src", root / "tests"
    src.mkdir()
    tests.mkdir()
    referent = tests / "t.py"
    referent.write_text("pass\n")
    os.link(referent, tests / "t_hard.py")
    (tests / "alias.py").symlink_to("t.py")
    (src / "link.py").symlink_to("../tests/t.py")
    result = identity.canonicalise(str(root), "src/link.py")
    assert result.names == ("t.py", "t_hard.py"), "scan the referent parent and omit symlinks"
    assert result.target == str(referent)


def test_symlink_chain_resolves_in_one_open(identity, root):
    src, tests = root / "src", root / "tests"
    src.mkdir()
    tests.mkdir()
    referent = tests / "t.py"
    referent.write_text("pass\n")
    (src / "mid.py").symlink_to("../tests/t.py")
    (src / "chain.py").symlink_to("mid.py")
    result = identity.canonicalise(str(root), "src/chain.py")
    assert result.target == str(referent), "the leaf symlink chain must reach the final referent"
    assert result.names == ("t.py",)
    assert os.stat(result.target).st_ino == os.stat(referent).st_ino


def test_directory_referent_has_no_names(identity, root):
    src, tests = root / "src", root / "tests"
    src.mkdir()
    tests.mkdir()
    (tests / "child.py").write_text("pass\n")
    (src / "todir").symlink_to("../tests", target_is_directory=True)
    result = identity.canonicalise(str(root), "src/todir")
    assert result.names == (), "a directory referent must not scan its children"
    assert result.unresolvable is False
    assert result.target == str(tests)


@pytest.mark.parametrize("relative", ["src/brandnew.py", "src/newpkg/mod.py"],
                         ids=["absent-leaf", "absent-parent"])
def test_absent_leaf_names_the_spelled_leaf(identity, root, relative):
    (root / "src").mkdir()
    result = identity.canonicalise(str(root), relative)
    assert result.target == str(root / relative), "absent path must retain the spelled absolute target"
    assert result.names == (Path(relative).name,)
    assert result.unresolvable is False


@pytest.mark.parametrize("relative,failed", [("src/dang.py", "src/dang.py"),
                                               ("lnk/x.py", "lnk")],
                         ids=["leaf", "intermediate"])
def test_dangling_leaf_is_arm_1(identity, root, relative, failed):
    if relative.startswith("src/"):
        (root / "src").mkdir()
        (root / "src/dang.py").symlink_to("nowhere/x.py")
    else:
        (root / "lnk").symlink_to("nowhere", target_is_directory=True)
    result = identity.canonicalise(str(root), relative)
    assert result.unresolvable is True
    assert result.arm == 1, "lstat success followed by stat failure must be arm 1"
    assert result.component == str(root / failed)
    assert result.names == ()


def test_loop_is_arm_1(identity, root):
    path = _loop(root)
    result = identity.canonicalise(str(root), "src/loopa.py")
    assert result.unresolvable is True
    assert result.arm == 1, "a symlink loop must use the stat-failure arm"
    assert result.component == str(path)


def test_loop_path_realpath_returns_without_error(root):
    path = _loop(root)
    assert os.path.realpath(path) == str(path), "realpath itself returns on a symlink loop"


@pytest.mark.parametrize("kind", ["a-absent-leaf", "b-existing-leaf"])
def test_unreadable_directory_is_arm_2(identity, root, kind):
    if kind == "a-absent-leaf":
        assert_case_insensitive(root)
        directory = root / "Tests"
        relative = "tests/newmod.py"
        # The component is reported in its on-disk spelling (operator decision
        # 2026-09-30, archreview v2 F3: the canonicaliser, not the gate, owns it).
        failed = root / "Tests"
    else:
        directory = root / "src"
        relative = "src/prod.py"
        failed = directory
    directory.mkdir()
    if kind == "b-existing-leaf":
        (directory / "prod.py").write_text("pass\n")
    directory.chmod(0o311)
    try:
        with pytest.raises(PermissionError, match="Permission denied"):
            os.listdir(directory)
        result = identity.canonicalise(str(root), relative)
    finally:
        directory.chmod(0o700)
    assert result.unresolvable is True
    assert result.arm == 2, "an opened or listed unreadable target directory must be arm 2"
    assert result.component == str(failed)
    assert result.target == ""


@pytest.mark.parametrize("mode", [0o311, 0o000], ids=["dir-0311", "dir-000"])
def test_unresolvable_component_is_reported_in_on_disk_spelling(identity, root, mode):
    root = Path(identity.canonical_directory(str(root)))
    assert_case_insensitive(root)
    directory = root / "Tests"
    directory.mkdir()
    original_mode = directory.stat().st_mode & 0o7777
    directory.chmod(mode)
    try:
        with pytest.raises(PermissionError, match="Permission denied"):
            os.listdir(directory)
        result = identity.canonicalise(str(root), "tests/newmod.py")
    finally:
        directory.chmod(original_mode)
    assert result.unresolvable is True
    assert result.component == str(directory), f"observed component: {result.component!r}"


def test_root_open_failure_is_arm_2(identity, root):
    root.chmod(0o311)
    try:
        with pytest.raises(PermissionError, match="Permission denied"):
            os.listdir(root)
        result = identity.canonicalise(str(root), "src/prod.py")
    finally:
        root.chmod(0o700)
    assert result.unresolvable is True
    assert result.arm == 2, "failure to open the root must be arm 2"
    assert (result.root, result.prefix, result.component) == (str(root),) * 3
    assert result.target == ""
    assert result.names == ()


def test_fold_py_suffix_folds_four_spellings(identity):
    assert identity.PY_SUFFIXES == (".py", ".pY", ".Py", ".PY")
    for suffix in identity.PY_SUFFIXES:
        assert identity.fold_py_suffix("StÉm" + suffix) == "StÉm.py", "fold only the suffix"
    assert identity.fold_py_suffix("prod.py ") == "prod.py "
    assert identity.fold_py_suffix("d.md") == "d.md"


def test_non_utf8_name_round_trips_through_percent_encoding(identity, capsys):
    raw = b"bad\xff.py"
    name = os.fsdecode(raw)
    record = identity.Identity("/root", "/root/file", "/root", (name,), False, 0, "")
    identity.emit_canon(record)
    encoded = capsys.readouterr().out.splitlines()[-1]
    assert encoded == "name bad%FF.py", "filesystem bytes must be percent encoded"
    assert os.fsencode(name) == raw
    with pytest.raises(UnicodeDecodeError):
        raw.decode("utf-8", errors="strict")
    with pytest.raises(UnicodeEncodeError):
        name.encode("utf-8", errors="strict")


@pytest.mark.parametrize("kind,values,expected", [
    ("file", ("/root", "/root/a.py", "/root", ("a.py", "a b%.py"), False, 0, ""),
     ["CANON 1", "root /root", "target /root/a.py", "prefix /root", "unresolvable no",
      "arm 0", "component ", "names 2", "name a.py", "name a%20b%25.py"]),
    ("directory", ("/root", "/root/tests", "/root", (), False, 0, ""),
     ["CANON 1", "root /root", "target /root/tests", "prefix /root", "unresolvable no",
      "arm 0", "component ", "names 0"]),
    ("unresolvable", ("/root", "", "/root/src", (), True, 1, "/root/src/dang.py"),
     ["CANON 1", "root /root", "target ", "prefix /root/src", "unresolvable yes",
      "arm 1", "component /root/src/dang.py", "names 0"]),
    ("empty-target", ("/root", "", "/root", (), False, 0, ""),
     ["CANON 1", "root /root", "target ", "prefix /root", "unresolvable no",
      "arm 0", "component ", "names 0"]),
    ("root-failure", ("/root", "", "/root", (), True, 2, "/root"),
     ["CANON 1", "root /root", "target ", "prefix /root", "unresolvable yes",
      "arm 2", "component /root", "names 0"]),
], ids=lambda value: value if isinstance(value, str) and value in
    {"file", "directory", "unresolvable", "empty-target", "root-failure"} else None)
def test_emit_canon_record_grammar(identity, capsys, kind, values, expected):
    record = identity.Identity(*values)
    identity.emit_canon(record)
    assert capsys.readouterr().out.splitlines() == expected, f"{kind} CANON field grammar"


def test_emit_canon_encodes_trailing_newlines(identity, capsys):
    record = identity.Identity("/r\n", "/t\n", "/p\n", ("one\n", "two\n"), False, 0, "c\n")
    identity.emit_canon(record)
    assert capsys.readouterr().out.splitlines() == [
        "CANON 1", "root /r%0A", "target /t%0A", "prefix /p%0A", "unresolvable no",
        "arm 0", "component c%0A", "names 2", "name one%0A", "name two%0A",
    ], "each trailing newline must stay inside its one physical CANON field"


def test_emit_canon_loop_record_is_unresolvable(identity, root, capsys):
    _loop(root)
    identity.emit_canon(identity.canonicalise(str(root), "src/loopa.py"))
    lines = capsys.readouterr().out.splitlines()
    assert "unresolvable yes" in lines, "loop CANON record must be unresolvable"
    assert "arm 1" in lines
    assert "names 0" in lines


def test_case_insensitive_precondition_is_asserted(tmp_path, monkeypatch, request):
    assert_case_insensitive(tmp_path)
    with monkeypatch.context() as patch:
        patch.setattr(os.path, "exists", lambda path: False)
        with pytest.raises(AssertionError, match="case-insensitive filesystem precondition"):
            assert_case_insensitive(tmp_path)
    identity = request.getfixturevalue("identity")
    assert identity.canonical_directory(str(tmp_path))


def _bash_function(source: str, name: str) -> str:
    lines = source.splitlines()
    starts = [i for i, line in enumerate(lines) if line.startswith(f"{name}() {{")]
    assert len(starts) == 1, f"missing or duplicated {name} bash function"
    start = starts[0]
    if lines[start].rstrip().endswith("}"):
        return lines[start]
    ends = [i for i in range(start + 1, len(lines)) if lines[i] == "}"]
    assert ends, f"unterminated {name} bash function"
    return "\n".join(lines[start:ends[0] + 1])


def test_canon_record_fields_survive_pct_capture(identity, capsys):
    hook = Path(__file__).resolve().parents[1] / "hooks/h-mad-tdd-gate.sh"
    source = hook.read_text(encoding="utf-8")
    functions = "\n".join(_bash_function(source, name) for name in ("_pct_decode", "_pct_capture"))
    record = identity.Identity("/r\n", "/t\n", "/p\n", ("name\n", "\n\n", "end\x01", "\x01", ""),
                               False, 0, "component\n")
    fields = [("root", record.root), ("target", record.target), ("prefix", record.prefix),
              ("component", record.component)] + [("name", name) for name in record.names]
    manual = [f"{key} {quote_from_bytes(value.encode('utf-8'), safe='/')}" for key, value in fields]
    identity.emit_canon(record)
    emitted = capsys.readouterr().out.splitlines()
    from_emit = [line for line in emitted if line.startswith(("root ", "target ", "prefix ",
                                                               "component ", "name "))]
    assert from_emit == manual, "emit_canon and the manual CANON 1 fields must agree"
    for lines in (manual, from_emit):
        for (key, expected), line in zip(fields, lines, strict=True):
            assert line.startswith(key + " ")
            encoded = line[len(key) + 1:]
            script = functions + "\nvalue=\n_pct_capture value \"$1\"\nprintf '%s\\0' \"$value\"\n"
            result = subprocess.run(["/bin/bash", "-c", script, "--", encoded],
                                    capture_output=True, check=True, timeout=10)
            assert result.stdout == expected.encode("utf-8") + b"\0", (key, expected, result.stderr)


def test_py_suffixes_match_bash_fold(identity):
    hook = Path(__file__).resolve().parents[1] / "hooks/h-mad-tdd-gate.sh"
    source = hook.read_text(encoding="utf-8")
    fold = _bash_function(source, "_fold_py")
    suffixes = tuple(dict.fromkeys(re.findall(r"\.(?:py|pY|Py|PY)\b", fold)))
    assert suffixes == identity.PY_SUFFIXES
    for marker in ("# M:H6", "*.md|*.yaml", "!= *.py"):
        site = source.find(marker)
        assert site >= 0, f"missing per-name classification site {marker}"
        preceding = source[max(0, site - 300):site]
        assert "_fold_py" in preceding, f"{marker} must read a folded name"
