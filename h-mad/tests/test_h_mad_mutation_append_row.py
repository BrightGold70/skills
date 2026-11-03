"""`h_mad_mutation_harness.py <spec> --append-row <row.json>` (row 2890).

Mutation rows were appended by hand-built scripts at least eight times in one
session, and three times a `json.dumps` re-dump of a spec expanded its compact
arrays or flipped its `\\u` escaping, so a one-row change showed as a rewrite of
the whole file. `--append-row` inserts the row's text before the `mutations`
array closes and touches no other byte. It refuses, leaving the spec as it was,
when the row is malformed, its name is taken, its anchor does not match exactly
once, or its named `test` id does not collect from the spec's root.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "h_mad_mutation_harness.py"

# Deliberately NOT what json.dumps would write: compact one-line arrays, a
# literal non-ASCII character AND a \\u escape, and a one-space indent.
SPEC_TEXT = (
    '{\n'
    ' "_why": "caf\\u00e9 — keeps both spellings",\n'
    ' "root": "../..",\n'
    ' "command": ["' + sys.executable + '", "-m", "pytest", "tests/test_mod.py", "-q"],\n'
    ' "target_command": ["' + sys.executable + '", "-m", "pytest", "-q"],\n'
    ' "mutations": [\n'
    '  {\n'
    '   "name": "first",\n'
    '   "file": "scripts/mod.py",\n'
    '   "find": "return 1",\n'
    '   "replace": "return 2",\n'
    '   "test": "tests/test_mod.py::test_f"\n'
    '  }\n'
    ' ]\n'
    '}\n'
)

MOD = "def f():\n    return 1\n\n\ndef g():\n    return 'g'\n"
TEST = ("import sys, pathlib\n"
        "sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))\n"
        "import mod\n\n"
        "def test_f():\n    assert mod.f() == 1\n\n"
        "def test_g():\n    assert mod.g() == 'g'\n")

GOOD_ROW = {
    "name": "second",
    "_mechanism": "g returns the wrong letter \u00e9",
    "file": "scripts/mod.py",
    "find": "return 'g'",
    "replace": "return 'h'",
    "test": "tests/test_mod.py::test_g",
}


def _tree(tmp_path: Path) -> Path:
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "mod.py").write_text(MOD)
    (tmp_path / "tests" / "mutation-specs").mkdir(parents=True)
    (tmp_path / "tests" / "test_mod.py").write_text(TEST)
    spec = tmp_path / "tests" / "mutation-specs" / "s.json"
    spec.write_text(SPEC_TEXT, encoding="utf-8")
    return spec


def _append(spec: Path, row: dict, tmp_path: Path) -> subprocess.CompletedProcess:
    row_file = tmp_path / "row.json"
    row_file.write_text(json.dumps(row), encoding="utf-8")
    return subprocess.run([sys.executable, str(SCRIPT), str(spec), "--append-row", str(row_file)],
                          capture_output=True, text=True, timeout=300)


def _last(out: str) -> str:
    return [line for line in out.splitlines() if line.strip()][-1]


def test_append_inserts_the_row_and_touches_no_other_byte(tmp_path):
    spec = _tree(tmp_path)
    r = _append(spec, GOOD_ROW, tmp_path)
    assert _last(r.stdout) == "APPEND: OK row=second mutations=2", r.stdout + r.stderr
    assert r.returncode == 0
    new = spec.read_text(encoding="utf-8")
    head, _ = SPEC_TEXT.split("  }\n ]\n}\n")
    assert new.startswith(head + "  },\n"), new          # only a comma joins the old row
    assert new.endswith("\n ]\n}\n"), new
    assert '["' + sys.executable + '", "-m", "pytest", "tests/test_mod.py", "-q"]' in new
    assert "caf\\u00e9 — keeps both spellings" in new
    data = json.loads(new)
    assert [m["name"] for m in data["mutations"]] == ["first", "second"]
    assert data["mutations"][1] == GOOD_ROW
    # The spec already holds a literal non-ASCII character, so the row's is
    # written literally too, not as a `\\u` escape.
    assert '"_mechanism": "g returns the wrong letter \u00e9"' in new, new
    # The inserted row uses the spec's own one-space indent unit.
    assert '\n  {\n   "name": "second",' in new, new


def test_appended_spec_passes_the_anchor_check(tmp_path):
    spec = _tree(tmp_path)
    assert _append(spec, GOOD_ROW, tmp_path).returncode == 0
    r = subprocess.run([sys.executable, str(SCRIPT), "--check-anchors", str(spec)],
                       capture_output=True, text=True, timeout=120)
    assert "ANCHORS_OK" in r.stdout and "mutations=2" in r.stdout, r.stdout + r.stderr


def _refused(spec: Path, row: dict, tmp_path: Path, reason: str) -> None:
    r = _append(spec, row, tmp_path)
    assert _last(r.stdout).startswith(f"APPEND: REFUSED reason={reason}"), r.stdout + r.stderr
    assert r.returncode == 2
    assert spec.read_text(encoding="utf-8") == SPEC_TEXT, "a refused append leaves the spec"


def test_a_taken_name_is_refused(tmp_path):
    _refused(_tree(tmp_path), {**GOOD_ROW, "name": "first"}, tmp_path, "duplicate-name")


def test_an_anchor_that_does_not_match_once_is_refused(tmp_path):
    spec = _tree(tmp_path)
    _refused(spec, {**GOOD_ROW, "find": "return 'zzz'"}, tmp_path, "anchor-count")
    _refused(spec, {**GOOD_ROW, "find": "return"}, tmp_path, "anchor-count")


def test_a_test_id_that_does_not_collect_is_refused(tmp_path):
    """The shifted-`targetN` case: a named id that no longer exists would make
    the row's kill unattributable."""
    _refused(_tree(tmp_path), {**GOOD_ROW, "test": "tests/test_mod.py::test_gone"},
             tmp_path, "test-not-collected")


def test_a_malformed_row_is_refused(tmp_path):
    spec = _tree(tmp_path)
    row = dict(GOOD_ROW)
    del row["replace"]
    _refused(spec, row, tmp_path, "bad-row")


def test_the_insert_is_exact_on_every_committed_spec():
    """The fixture above is one layout; the corpus has many (indent 1 and 2,
    one-line rows, escaped and literal non-ASCII). For each committed spec the
    rendered insert must parse to the old rows plus one, with every other key
    unchanged and no old byte moved."""
    sys.path.insert(0, str(SCRIPT.parent))
    import h_mad_mutation_harness as harness

    repo = SCRIPT.resolve().parents[2]
    listed = subprocess.run(["git", "-C", str(repo), "ls-files", "-z", "*/mutation-specs/*.json"],
                            capture_output=True, check=True).stdout.split(b"\0")
    specs = [repo / p.decode() for p in listed if p]
    assert len(specs) >= 150, len(specs)
    row = {"name": "zz-appended", "file": "x.py", "find": "a", "replace": "b",
           "test": "t.py::t", "_mechanism": "café"}
    for spec in specs:
        text = spec.read_text(encoding="utf-8")
        old = json.loads(text)
        if not isinstance(old, dict) or not old.get("mutations"):
            continue
        bounds = harness._mutations_bounds(text)
        assert bounds is not None, spec
        at, inserted = harness._render_row(text, *bounds, row)
        new = text[:at] + inserted + text[at:]
        data = json.loads(new)
        assert data["mutations"] == old["mutations"] + [row], spec
        assert {k: v for k, v in data.items() if k != "mutations"} == \
            {k: v for k, v in old.items() if k != "mutations"}, spec


def test_an_insert_at_the_wrong_bracket_is_refused_by_the_verify_step(tmp_path, monkeypatch, capsys):
    """Positive control for the verify step: point the insert at the `command`
    array instead of `mutations`. The result is valid JSON with the wrong
    meaning, which only the structural comparison can catch."""
    sys.path.insert(0, str(SCRIPT.parent))
    import h_mad_mutation_harness as harness

    spec = _tree(tmp_path)
    row_file = tmp_path / "row.json"
    row_file.write_text(json.dumps(GOOD_ROW), encoding="utf-8")
    text = SPEC_TEXT
    command_open = text.index('"command": [') + len('"command": ')
    command_close = text.index("]", command_open)
    monkeypatch.setattr(harness, "_mutations_bounds", lambda _text: (command_open, command_close))
    assert harness.append_row(spec, row_file) == 2
    assert capsys.readouterr().out.strip().splitlines()[-1].startswith(
        "APPEND: REFUSED reason=verify-failed")
    assert spec.read_text(encoding="utf-8") == SPEC_TEXT


def test_a_one_line_row_layout_gets_a_one_line_row():
    sys.path.insert(0, str(SCRIPT.parent))
    import h_mad_mutation_harness as harness

    text = ('{"command": ["x"], "mutations": [\n'
            '  {"name": "a", "file": "f", "find": "p", "replace": "q"}\n'
            ']}\n')
    at, inserted = harness._render_row(text, *harness._mutations_bounds(text), {"name": "b"})
    new = text[:at] + inserted + text[at:]
    assert new == ('{"command": ["x"], "mutations": [\n'
                   '  {"name": "a", "file": "f", "find": "p", "replace": "q"},\n'
                   '  {"name": "b"}\n'
                   ']}\n'), new


def test_a_test_id_collects_when_pytest_rootdir_is_above_the_spec_root(tmp_path):
    """In this repository `pytest.ini` sits at the top while spec roots are
    `h-mad/` or `handoff/`, so pytest prints collected ids relative to the
    rootdir (`h-mad/tests/…`) while a spec names them relative to its root
    (`tests/…`). Found by building this feature's own spec with `--append-row`:
    every real id was refused as not collected, with rc=0."""
    (tmp_path / "pytest.ini").write_text("[pytest]\n")
    sub = tmp_path / "sub"
    sub.mkdir()
    spec = _tree(sub)
    r = _append(spec, GOOD_ROW, tmp_path)
    assert _last(r.stdout) == "APPEND: OK row=second mutations=2", r.stdout + r.stderr
