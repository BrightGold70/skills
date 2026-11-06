"""Tests for `h_mad_guard_census.py`.

Skill-candidates row "guard-census-from-the-diff": a `# M:` marker census cannot
see an unmarked arm, and hand-built diff censuses took two Phase 6 rounds. The
tool lists the decision lines a diff adds or changes that no mutation row
anchors. Every test drives the real CLI over a real git repository.

The first three classes pin the invariants every verdict-token gate here shares
(see `h_mad_new_gate.py`): a cannot-judge carries no count, exit 0 on any
verdict, the docs table pinned both ways. The rest pin the census itself,
including the hostile inputs: paths with spaces and glob characters, a `find`
that matches twice or not at all, a deleted file, a binary change, a source file
that is not UTF-8.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "h_mad_guard_census.py"
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from h_mad_skill_corpus import skill_text  # noqa: E402

GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
SPECS = "h-mad/tests/mutation-specs"

PY_BASE = "def f(x):\n    return x\n"
PY_HEAD = (
    "def f(x):\n"
    "    if x > 1:\n"          # 2  if
    "        y = x\n"          # 3  assign
    "    elif x < 0:\n"        # 4  elif
    "        return -x\n"      # 5  return
    "    else:\n"
    "        y = 0\n"          # 7  assign
    "    return y\n"           # 8  return
)


def git(repo: Path, *args: str) -> str:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    return subprocess.run(["git", "-C", str(repo), *args], check=True, text=True, capture_output=True,
                          env={**env, **GIT_ENV}).stdout


def write(repo: Path, files: dict[str, str | bytes]) -> None:
    for rel, body in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(body if isinstance(body, bytes) else body.encode("utf-8"))


def commit(repo: Path, files: dict[str, str | bytes], msg: str = "c", remove: tuple[str, ...] = ()) -> str:
    write(repo, files)
    for rel in remove:
        (repo / rel).unlink()
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", msg)
    return git(repo, "rev-parse", "HEAD").strip()


def spec(rows: list[dict], root: str = "../..") -> str:
    return json.dumps({"root": root, "command": ["pytest"], "mutations": rows})


def row(file: str, find: str, name: str = "m") -> dict:
    return {"name": name, "file": file, "find": find, "replace": "x", "test": "t.py::t"}


def make(tmp_path: Path, base_files: dict, head_files: dict, *, remove: tuple[str, ...] = ()) -> tuple[Path, str]:
    """A repo with a base commit and a head commit; returns (repo, base sha)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    base = commit(repo, {f"{SPECS}/keep.json": spec([]), **base_files}, "base")
    commit(repo, head_files, "head", remove)
    return repo, base


def census(repo: Path, base: str, *args: str, head: str | None = None) -> subprocess.CompletedProcess:
    argv = [sys.executable, str(SCRIPT), "--repo", str(repo), "--base", base, *args]
    if head:
        argv += ["--head", head]
    return subprocess.run(argv, capture_output=True, text=True, timeout=120)


def token(proc: subprocess.CompletedProcess) -> str:
    lines = proc.stdout.rstrip("\n").splitlines()
    assert lines, proc.stderr
    assert lines[-1].startswith("GUARD-CENSUS: "), proc.stdout + proc.stderr
    return lines[-1]


def counts(proc: subprocess.CompletedProcess) -> tuple[int, int, int]:
    m = re.fullmatch(r"GUARD-CENSUS: DONE decision=(\d+) anchored=(\d+) unanchored=(\d+)", token(proc))
    assert m, proc.stdout + proc.stderr
    return int(m[1]), int(m[2]), int(m[3])


def candidates(proc: subprocess.CompletedProcess) -> dict[str, list[str]]:
    """`file:line` -> [kind, note, text] for every candidate line."""
    out = {}
    for ln in proc.stdout.splitlines():
        parts = ln.split("\t")
        if len(parts) == 4 and re.search(r":\d+$", parts[0]):
            out[parts[0]] = parts[1:]
    return out


def simple(tmp_path: Path, rows: list[dict], head_py: str = PY_HEAD) -> tuple[Path, str]:
    return make(tmp_path, {"h-mad/scripts/mod.py": PY_BASE},
                {"h-mad/scripts/mod.py": head_py, f"{SPECS}/mod.json": spec(rows)})


# ----------------------------------------------------------- shared invariants

class TestCannotJudgeCarriesNoCount:
    """A zero is byte-identical to "nothing was measured", and reads as clean."""

    def test_the_cannot_judge_line_has_no_count(self, tmp_path: Path) -> None:
        proc = census(tmp_path, "nonesuch")
        assert token(proc).startswith("GUARD-CENSUS: UNREADABLE reason="), proc.stdout
        assert "decision=" not in proc.stdout and "unanchored=" not in proc.stdout, proc.stdout

    def test_a_real_verdict_does_carry_its_counts(self, tmp_path: Path) -> None:
        repo, base = simple(tmp_path, [])
        assert counts(census(repo, base)) is not None


class TestExitCodes:
    def test_a_verdict_with_candidates_exits_zero(self, tmp_path: Path) -> None:
        repo, base = simple(tmp_path, [])
        proc = census(repo, base)
        assert counts(proc)[2] > 0, "the fixture must have candidates"
        assert proc.returncode == 0, "a list of candidates is a measurement, not a failure"

    def test_only_a_cannot_judge_exits_two(self, tmp_path: Path) -> None:
        assert census(tmp_path, "nonesuch").returncode == 2


class TestDocsArePinnedBothWays:
    def test_the_script_is_registered(self) -> None:
        assert "h_mad_guard_census.py" in skill_text(SKILL_DIR)

    def test_every_printed_prefix_is_documented_and_every_documented_one_exists(self) -> None:
        script = SCRIPT.read_text(encoding="utf-8")
        entry = next(ln for ln in skill_text(SKILL_DIR).split("\n") if "h_mad_guard_census.py" in ln)
        assert 'TOKEN = "GUARD-CENSUS"' in script
        printed = set(re.findall(r'f"([A-Z]+(?:-[A-Z]+)?):', script)) | {"GUARD-CENSUS"}
        documented = set(re.findall(r"`([A-Z]+(?:-[A-Z]+)?):", entry))
        assert printed == {"GUARD-CENSUS", "CENSUS-SCOPE", "SKIPPED", "ROWS", "ARMS"}, printed
        assert printed - documented == set(), f"printed with no entry: {sorted(printed - documented)}"
        assert documented - printed == set(), f"documented, never printed: {sorted(documented - printed)}"


# -------------------------------------------------------------- the census

def test_every_python_decision_line_is_listed_when_nothing_anchors_it(tmp_path: Path) -> None:
    repo, base = simple(tmp_path, [])

    proc = census(repo, base)

    got = candidates(proc)
    expected = {"h-mad/scripts/mod.py:2": "if", "h-mad/scripts/mod.py:3": "assign",
                "h-mad/scripts/mod.py:4": "elif", "h-mad/scripts/mod.py:5": "return",
                "h-mad/scripts/mod.py:7": "assign", "h-mad/scripts/mod.py:8": "return"}
    assert {k: v[0] for k, v in got.items()} == expected, proc.stdout
    assert counts(proc) == (6, 0, 6)


def test_a_row_whose_find_covers_a_line_anchors_it(tmp_path: Path) -> None:
    repo, base = simple(tmp_path, [row("scripts/mod.py", "    elif x < 0:\n")])

    proc = census(repo, base)

    assert "h-mad/scripts/mod.py:4" not in candidates(proc), proc.stdout
    assert counts(proc) == (6, 1, 5)


def test_a_marker_comment_with_no_row_anchors_nothing(tmp_path: Path) -> None:
    """The blind spot this tool exists for: `# M:` is prose, only a row's `find` anchors."""
    marked = PY_HEAD.replace("    elif x < 0:", "    elif x < 0:  # M:MARKED-BUT-NO-ROW")
    repo, base = simple(tmp_path, [], marked)

    proc = census(repo, base)

    assert "h-mad/scripts/mod.py:4" in candidates(proc), proc.stdout
    assert counts(proc)[1] == 0


def test_a_find_that_matches_twice_anchors_nothing_and_is_counted(tmp_path: Path) -> None:
    doubled = PY_HEAD + "def g():\n    if 1:\n        y = 0\n"
    repo, base = simple(tmp_path, [row("scripts/mod.py", "        y = 0\n")], doubled)

    proc = census(repo, base)

    assert "h-mad/scripts/mod.py:7" in candidates(proc), "an ambiguous mutant proves nothing"
    assert "ROWS: ambiguous_find=1 stale_find=0" in proc.stdout, proc.stdout


def test_a_find_that_matches_nowhere_anchors_nothing_and_is_counted(tmp_path: Path) -> None:
    repo, base = simple(tmp_path, [row("scripts/mod.py", "    elif x < 99:\n")])

    proc = census(repo, base)

    assert counts(proc)[1] == 0
    assert "ROWS: ambiguous_find=0 stale_find=1" in proc.stdout, proc.stdout


def test_a_row_for_another_file_anchors_nothing(tmp_path: Path) -> None:
    repo, base = simple(tmp_path, [row("scripts/other.py", "    elif x < 0:\n")])

    assert counts(census(repo, base))[1] == 0


def test_only_added_or_changed_lines_are_decisions(tmp_path: Path) -> None:
    base_py = "def f(x):\n    if x:\n        return 1\n    return 0\n"
    head_py = "def f(x):\n    if x:\n        return 2\n    return 0\n"
    repo, base = make(tmp_path, {"h-mad/scripts/mod.py": base_py}, {"h-mad/scripts/mod.py": head_py})

    proc = census(repo, base)

    assert list(candidates(proc)) == ["h-mad/scripts/mod.py:3"], proc.stdout
    assert counts(proc) == (1, 0, 1)


def test_imports_defs_docstrings_and_comments_are_not_decisions(tmp_path: Path) -> None:
    head_py = '"""doc"""\nimport os\n# comment\ndef f(x):\n    """doc"""\n    pass\n\nclass K:\n    pass\n'
    repo, base = make(tmp_path, {"h-mad/scripts/mod.py": PY_BASE}, {"h-mad/scripts/mod.py": head_py})

    assert counts(census(repo, base)) == (0, 0, 0)


def test_an_arm_of_an_anchored_guard_is_annotated_but_stays_a_candidate(tmp_path: Path) -> None:
    repo, base = simple(tmp_path, [row("scripts/mod.py", "    if x > 1:\n")])

    proc = census(repo, base)

    got = candidates(proc)
    assert got["h-mad/scripts/mod.py:3"][1] == "arm-of-anchored:2", proc.stdout
    assert got["h-mad/scripts/mod.py:4"][1] == "", "an elif is a decision of its own, never an arm"
    assert "ARMS: unanchored_arm_of_anchored=1" in proc.stdout, proc.stdout


def test_a_multi_line_statement_is_anchored_by_any_changed_line_of_it(tmp_path: Path) -> None:
    head_py = "def f(x):\n    return g(\n        x,\n        1,\n    )\n"
    repo, base = make(tmp_path, {"h-mad/scripts/mod.py": PY_BASE},
                      {"h-mad/scripts/mod.py": head_py,
                       f"{SPECS}/mod.json": spec([row("scripts/mod.py", "        1,\n")])})

    proc = census(repo, base)

    assert counts(proc) == (1, 1, 0), proc.stdout


def test_conditional_forms_inside_a_statement_are_named_in_its_kind(tmp_path: Path) -> None:
    head_py = "def f(x):\n    y = 1 if x else 2\n    z = [a for a in x if a]\n    return x and y\n"
    repo, base = make(tmp_path, {"h-mad/scripts/mod.py": PY_BASE}, {"h-mad/scripts/mod.py": head_py})

    got = candidates(census(repo, base))

    assert got["h-mad/scripts/mod.py:2"][0] == "assign,ifexp"
    assert got["h-mad/scripts/mod.py:3"][0] == "assign,comp-if"
    assert got["h-mad/scripts/mod.py:4"][0] == "return,boolop"


def test_test_files_are_not_census_targets(tmp_path: Path) -> None:
    repo, base = make(tmp_path, {"h-mad/scripts/mod.py": PY_BASE},
                      {"h-mad/tests/test_mod.py": PY_HEAD, "h-mad/tests/conftest.py": PY_HEAD,
                       "h-mad/scripts/test_inline.py": PY_HEAD, "h-mad/scripts/mod_test.py": PY_HEAD})

    assert counts(census(repo, base)) == (0, 0, 0)


def test_path_limits_the_diff(tmp_path: Path) -> None:
    repo, base = make(tmp_path, {"h-mad/scripts/mod.py": PY_BASE},
                      {"h-mad/scripts/mod.py": PY_HEAD, "other/mod2.py": PY_HEAD})

    assert counts(census(repo, base, "--path", "other"))[0] == 6
    assert counts(census(repo, base))[0] == 12


def test_the_spec_dir_option_and_its_default_are_read_from_the_head_tree(tmp_path: Path) -> None:
    rows = [row("h-mad/scripts/mod.py", "    elif x < 0:\n")]
    repo, base = make(tmp_path, {"h-mad/scripts/mod.py": PY_BASE},
                      {"h-mad/scripts/mod.py": PY_HEAD, "elsewhere/mod.json": spec(rows, "..")})

    default = census(repo, base)
    custom = census(repo, base, "--spec-dir", "elsewhere")

    assert counts(default)[1] == 0
    assert counts(custom)[1] == 1, custom.stdout


def test_a_spec_that_is_only_in_the_working_tree_does_not_anchor(tmp_path: Path) -> None:
    repo, base = simple(tmp_path, [])
    write(repo, {f"{SPECS}/mod.json": spec([row("scripts/mod.py", "    elif x < 0:\n")])})

    assert counts(census(repo, base))[1] == 0, "specs are read at --head, not from the working tree"


def test_head_defaults_to_HEAD_and_can_name_an_earlier_commit(tmp_path: Path) -> None:
    repo, base = simple(tmp_path, [])
    first = git(repo, "rev-parse", "HEAD").strip()
    commit(repo, {"h-mad/scripts/mod.py": PY_HEAD + "    z = 1\n"}, "later")

    assert counts(census(repo, base))[0] == 7
    assert counts(census(repo, base, head=first))[0] == 6


# ------------------------------------------------------------ hostile inputs

HOSTILE = ["dir with space/m od.py", "glob[1]/*.py", "\u03a9mega/caf\u00e9.py"]


@pytest.mark.parametrize("rel", HOSTILE)
def test_hostile_paths_are_listed_and_anchored_by_their_literal_name(tmp_path: Path, rel: str) -> None:
    repo, base = make(tmp_path, {rel: PY_BASE},
                      {rel: PY_HEAD, f"{SPECS}/h.json": spec([row(rel, "    elif x < 0:\n")], "../../..")})

    proc = census(repo, base)

    assert f"{rel}:2" in candidates(proc), proc.stdout
    assert f"{rel}:4" not in candidates(proc), "the row anchored the literal path"
    assert counts(proc) == (6, 1, 5)


def test_a_deleted_file_is_skipped_and_counted(tmp_path: Path) -> None:
    repo, base = make(tmp_path, {"h-mad/scripts/gone.py": PY_HEAD}, {}, remove=("h-mad/scripts/gone.py",))

    proc = census(repo, base)

    assert counts(proc) == (0, 0, 0)
    assert "SKIPPED: deleted=1" in proc.stdout, proc.stdout


def test_a_binary_change_is_skipped_and_counted(tmp_path: Path) -> None:
    repo, base = make(tmp_path, {"h-mad/scripts/blob.py": b"\x00\x01"}, {"h-mad/scripts/blob.py": b"\x00\x02\x00"})

    proc = census(repo, base)

    assert counts(proc) == (0, 0, 0)
    assert "binary=1" in proc.stdout, proc.stdout


def test_a_non_utf8_python_file_is_UNREADABLE_not_zero(tmp_path: Path) -> None:
    repo, base = make(tmp_path, {"h-mad/scripts/mod.py": PY_BASE},
                      {"h-mad/scripts/mod.py": b"def f(x):\n    return '\xff\xfe'\n"})

    proc = census(repo, base)

    assert token(proc) == "GUARD-CENSUS: UNREADABLE reason=unreadable-file", proc.stdout
    assert proc.returncode == 2


def test_a_declared_non_utf8_encoding_is_read_with_that_encoding(tmp_path: Path) -> None:
    head = "# -*- coding: latin-1 -*-\ndef f(x):\n    return '\u00e9'\n".encode("latin-1")
    repo, base = make(tmp_path, {"h-mad/scripts/mod.py": PY_BASE}, {"h-mad/scripts/mod.py": head})

    assert counts(census(repo, base)) == (1, 0, 1)


def test_a_python_file_that_does_not_parse_is_UNREADABLE(tmp_path: Path) -> None:
    repo, base = make(tmp_path, {"h-mad/scripts/mod.py": PY_BASE}, {"h-mad/scripts/mod.py": "def f(:\n"})

    assert token(census(repo, base)) == "GUARD-CENSUS: UNREADABLE reason=unreadable-file"


def test_crlf_files_keep_git_line_numbers(tmp_path: Path) -> None:
    crlf = PY_HEAD.replace("\n", "\r\n")
    repo, base = make(tmp_path, {"h-mad/scripts/mod.py": PY_BASE}, {"h-mad/scripts/mod.py": crlf})

    assert "h-mad/scripts/mod.py:4" in candidates(census(repo, base))


# ------------------------------------------------------------ cannot-judge

def test_an_unknown_base_is_UNREADABLE(tmp_path: Path) -> None:
    repo, _ = simple(tmp_path, [])
    assert token(census(repo, "no-such-ref")) == "GUARD-CENSUS: UNREADABLE reason=bad-ref"


def test_an_unknown_head_is_UNREADABLE(tmp_path: Path) -> None:
    repo, base = simple(tmp_path, [])
    assert token(census(repo, base, head="no-such-ref")) == "GUARD-CENSUS: UNREADABLE reason=bad-ref"


def test_a_directory_that_is_not_a_repository_is_UNREADABLE(tmp_path: Path) -> None:
    plain = tmp_path / "plain"
    plain.mkdir()
    assert token(census(plain, "main")) == "GUARD-CENSUS: UNREADABLE reason=git"


def test_a_missing_repo_directory_is_UNREADABLE(tmp_path: Path) -> None:
    assert token(census(tmp_path / "absent", "main")) == "GUARD-CENSUS: UNREADABLE reason=git"


def test_a_missing_spec_directory_is_UNREADABLE_not_zero_anchors(tmp_path: Path) -> None:
    repo, base = simple(tmp_path, [])
    assert token(census(repo, base, "--spec-dir", "no/such")) == "GUARD-CENSUS: UNREADABLE reason=spec-dir"


def test_a_spec_directory_outside_the_repository_is_UNREADABLE(tmp_path: Path) -> None:
    repo, base = simple(tmp_path, [])
    outside = tmp_path / "outside"
    outside.mkdir()
    assert token(census(repo, base, "--spec-dir", str(outside))) == "GUARD-CENSUS: UNREADABLE reason=spec-dir"


@pytest.mark.parametrize("body", [b"{not json", b'{"mutations": [{"file": "a.py"}]}',
                                  b'{"mutations": [{"file": 1, "find": "x"}]}', b"\xff\xfe"])
def test_an_unreadable_spec_is_UNREADABLE(tmp_path: Path, body: bytes) -> None:
    repo, base = make(tmp_path, {"h-mad/scripts/mod.py": PY_BASE},
                      {"h-mad/scripts/mod.py": PY_HEAD, f"{SPECS}/bad.json": body})

    proc = census(repo, base)

    assert token(proc) == "GUARD-CENSUS: UNREADABLE reason=spec-unreadable", proc.stdout
    assert proc.returncode == 2


def test_a_json_file_that_is_not_a_spec_is_skipped_and_counted(tmp_path: Path) -> None:
    repo, base = make(tmp_path, {"h-mad/scripts/mod.py": PY_BASE},
                      {"h-mad/scripts/mod.py": PY_HEAD, f"{SPECS}/data.json": '{"rows": []}'})

    proc = census(repo, base)

    assert counts(proc)[0] == 6
    assert "nonspec_json=1" in proc.stdout, proc.stdout


def test_a_spec_with_an_absolute_root_outside_the_repo_is_counted_not_trusted(tmp_path: Path) -> None:
    repo, base = simple(tmp_path, [])
    commit(repo, {f"{SPECS}/abs.json": spec([row("scripts/mod.py", "    elif x < 0:\n")], "/nonexistent/root")})

    proc = census(repo, base)

    assert counts(proc)[1] == 0
    assert "outside_repo_specs=1" in proc.stdout, proc.stdout


# --------------------------------------------------------------------- shell

SH_BASE = "#!/bin/bash\necho hi\n"
SH_HEAD = """#!/bin/bash
# if [ -n "$x" ] || return 1
_allow_all() {
  local want=$1
  if [ "$want" = yes ]; then
    _allow
  elif [[ $want == no ]]; then
    _refuse judge-error "no"
  fi
  case "$want" in "a") X=1 ;; "b") X=2 ;; *) X=3 ;; esac
  [ -n "$X" ] || return 1
  for n in "${NAMES[@]}"; do LARGS[${#LARGS[@]}]=$n; done
  echo plain
  _read_listing
}
"""


def sh_repo(tmp_path: Path, rows: list[dict] | None = None, body: str = SH_HEAD,
            name: str = "h-mad/hooks/gate.sh") -> tuple[Path, str]:
    files = {name: body}
    if rows is not None:
        files[f"{SPECS}/gate.json"] = spec(rows)
    return make(tmp_path, {name: SH_BASE}, files)


def test_shell_decision_lines_follow_the_documented_rule(tmp_path: Path) -> None:
    repo, base = sh_repo(tmp_path)

    got = candidates(census(repo, base))

    kinds = {k.rsplit(":", 1)[1]: v[0] for k, v in got.items()}
    assert kinds == {"4": "assign", "5": "control,test", "6": "verdict", "7": "control,test",
                     "8": "verdict", "10": "control,arm", "11": "test,andor,jump",
                     "12": "control"}, kinds
    # not decisions: the shebang, a comment that looks like code, the function header, `fi`, `}`, a plain echo, a plain call
    assert not {"1", "2", "3", "9", "13", "14", "15"} & set(kinds), kinds


def test_a_row_anchors_a_shell_line_by_its_find(tmp_path: Path) -> None:
    repo, base = sh_repo(tmp_path, [row("hooks/gate.sh", '[ -n "$X" ] || return 1\n')])

    proc = census(repo, base)

    assert "h-mad/hooks/gate.sh:11" not in candidates(proc)
    assert counts(proc)[1] == 1


def test_a_shell_case_line_needs_every_arm_anchored(tmp_path: Path) -> None:
    one_arm = [row("hooks/gate.sh", '*) X=3 ;; esac')]
    all_arms = [row("hooks/gate.sh", '"a") X=1 ;;', "a"), row("hooks/gate.sh", '"b") X=2 ;;', "b"),
                row("hooks/gate.sh", '*) X=3 ;;', "c")]
    repo, base = sh_repo(tmp_path, one_arm)
    partial = census(repo, base)
    assert candidates(partial)["h-mad/hooks/gate.sh:10"][1] == "arms-not-all-anchored", partial.stdout

    repo2 = tmp_path / "two"
    repo2.mkdir()
    repo2, base2 = sh_repo(repo2, all_arms)
    assert "h-mad/hooks/gate.sh:10" not in candidates(census(repo2, base2))


def test_a_suffixless_file_with_a_shell_shebang_is_a_shell_target(tmp_path: Path) -> None:
    repo, base = sh_repo(tmp_path, None, SH_HEAD, "h-mad/bin/launch")

    assert counts(census(repo, base))[0] == 8


def test_a_suffixless_file_with_another_shebang_is_not_a_target(tmp_path: Path) -> None:
    repo, base = sh_repo(tmp_path, None, "#!/usr/bin/env ruby\nif x\n", "h-mad/bin/launch")

    assert counts(census(repo, base)) == (0, 0, 0)


def test_a_non_utf8_shell_file_is_UNREADABLE(tmp_path: Path) -> None:
    repo, base = make(tmp_path, {"h-mad/hooks/gate.sh": SH_BASE},
                      {"h-mad/hooks/gate.sh": b"#!/bin/bash\nX=\xff\xfe\n"})

    assert token(census(repo, base)) == "GUARD-CENSUS: UNREADABLE reason=unreadable-file"


# ------------------------------------------------------------- calibration

def test_the_gate_non_py_hand_census_is_listed_in_full() -> None:
    """Replay of analysis v3 §Census at 246531ba: the 16 lines, and v4's 2, must all be listed.

    Skipped, naming the missing object, in a clone that does not hold the commit.
    """
    repo = SKILL_DIR.parent
    for commit_id in ("3489f86b", "246531ba"):
        have = subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"{commit_id}^{{commit}}"],
                              capture_output=True).returncode == 0
        if not have:
            pytest.skip(f"commit {commit_id} is not in this clone; the calibration needs it")
    proc = subprocess.run([sys.executable, str(SCRIPT), "--repo", str(repo), "--base", "3489f86b",
                           "--head", "246531ba", "--path", "h-mad/hooks", "--path", "h-mad/scripts"],
                          capture_output=True, text=True, timeout=300)
    got = candidates(proc)
    files = {"judge": "h-mad/scripts/h_mad_tdd_judge.py", "cx": "h-mad/hooks/h-mad-codex-tdd-gate.py",
             "ag": "h-mad/hooks/h-mad-agy-tdd-gate.py", "sh": "h-mad/hooks/h-mad-tdd-gate.sh"}
    listed = ("judge:737 sh:269 judge:341 judge:335 judge:330 judge:347 judge:732 sh:198 cx:289 ag:185 "
              "cx:303 ag:202 sh:344 judge:733 cx:293 ag:188 judge:344 judge:738").split()
    missed = [n for n in listed if f"{files[n.split(':')[0]]}:{n.split(':')[1]}" not in got]
    assert not missed, f"hand-census lines the tool did not list: {missed}"
    assert counts(proc) == (170, 58, 112)


def test_an_empty_find_anchors_nothing_and_counts_as_stale(tmp_path: Path) -> None:
    repo, base = simple(tmp_path, [row("scripts/mod.py", "")])

    proc = census(repo, base)

    assert counts(proc)[1] == 0
    assert "ROWS: ambiguous_find=0 stale_find=1" in proc.stdout, proc.stdout


def test_a_symlink_and_a_submodule_are_skipped_and_counted(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    base = commit(repo, {f"{SPECS}/keep.json": spec([]), "h-mad/scripts/real.py": PY_BASE})
    (repo / "h-mad/scripts/mod.py").symlink_to("real.py")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "link")
    sha = git(repo, "rev-parse", "HEAD").strip()
    git(repo, "update-index", "--add", "--cacheinfo", f"160000,{sha},h-mad/scripts/sub.py")
    git(repo, "commit", "-q", "-m", "gitlink")

    proc = census(repo, base)

    assert counts(proc) == (0, 0, 0), proc.stdout
    assert "link=2" in proc.stdout, proc.stdout


def test_a_glob_character_name_does_not_pick_up_a_sibling_files_hunks(tmp_path: Path) -> None:
    """`x*.py` is a literal name; read as a pattern it would also own `xyz.py`'s changed lines."""
    repo, base = make(tmp_path, {"h-mad/scripts/x*.py": PY_BASE, "h-mad/scripts/xyz.py": PY_BASE},
                      {"h-mad/scripts/x*.py": PY_BASE + "# c\n", "h-mad/scripts/xyz.py": PY_HEAD})

    proc = census(repo, base)

    assert counts(proc) == (6, 0, 6), proc.stdout
    assert not [k for k in candidates(proc) if k.startswith("h-mad/scripts/x*.py")], proc.stdout
