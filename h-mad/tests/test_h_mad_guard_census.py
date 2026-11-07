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
    m = re.fullmatch(r"GUARD-CENSUS: DONE decision=(\d+) anchored=(\d+) unanchored=(\d+) removed=(\d+) unparsed_base=(\d+)",
                     token(proc))
    assert m, proc.stdout + proc.stderr
    return int(m[1]), int(m[2]), int(m[3])


def removed_count(proc: subprocess.CompletedProcess) -> int:
    m = re.fullmatch(r"GUARD-CENSUS: DONE decision=\d+ anchored=\d+ unanchored=\d+ removed=(\d+) unparsed_base=\d+", token(proc))
    assert m, proc.stdout + proc.stderr
    return int(m[1])


def removed_lines(proc: subprocess.CompletedProcess) -> list[str]:
    return [ln for ln in proc.stdout.splitlines() if ln.startswith("REMOVED: ")]


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
        assert printed == {"GUARD-CENSUS", "CENSUS-SCOPE", "SKIPPED", "ROWS", "ARMS", "UNMEASURED",
                           "REMOVED", "UNPARSED-BASE"}, printed
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

    proc = census(repo, base)

    assert counts(proc) == (0, 0, 0)
    assert "tests=4" in proc.stdout, proc.stdout


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
    assert re.search(r"CENSUS-SCOPE: .* files=1 deleted=1\b", proc.stdout), proc.stdout
    assert removed_count(proc) == 6, "a deleted file's decisions are removed guards, not nothing"


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


def test_a_suffixless_file_with_another_shebang_is_not_a_target_but_is_counted(tmp_path: Path) -> None:
    repo, base = sh_repo(tmp_path, None, "#!/usr/bin/env ruby\nif x\n", "h-mad/bin/launch")

    proc = census(repo, base)

    assert counts(proc) == (0, 0, 0)
    assert "unmeasured=1" in proc.stdout, "a changed file nobody measured must not read as a clean zero"
    assert "UNMEASURED: h-mad/bin/launch" in proc.stdout, proc.stdout


@pytest.mark.parametrize("name", ["src/app.ts", "web/check.js", "lib/x.rb", "cmd/main.go"])
def test_code_in_another_language_is_unmeasured_and_listed(tmp_path: Path, name: str) -> None:
    repo, base = make(tmp_path, {"h-mad/scripts/mod.py": PY_BASE}, {name: "if (x) { return 1 }\n"})

    proc = census(repo, base)

    assert counts(proc) == (0, 0, 0)
    assert "unmeasured=1" in proc.stdout and f"UNMEASURED: {name}" in proc.stdout, proc.stdout


def test_documents_and_data_are_not_unmeasured_code(tmp_path: Path) -> None:
    repo, base = make(tmp_path, {"h-mad/scripts/mod.py": PY_BASE},
                      {"docs/a.md": "# x\n", "data/b.json": "{}\n", "c.txt": "x\n"})

    proc = census(repo, base)

    assert "unmeasured=0" in proc.stdout and "other=3" in proc.stdout, proc.stdout


@pytest.mark.parametrize("name,body,expected", [
    ("src/hook.zsh", SH_HEAD.replace("#!/bin/bash", "#!/bin/zsh"), 8),
    ("src/nobang.zsh", SH_HEAD.replace("#!/bin/bash\n", ""), 8),
    ("h-mad/hooks/gate.v2", SH_HEAD, 8),
    ("h-mad/bin/tool", "#!/usr/bin/env python3\n" + PY_HEAD, 6),
])
def test_a_shell_or_python_script_is_measured_whatever_its_suffix(
        tmp_path: Path, name: str, body: str, expected: int) -> None:
    repo, base = make(tmp_path, {"h-mad/scripts/mod.py": PY_BASE}, {name: body})

    proc = census(repo, base)

    assert counts(proc)[0] == expected, proc.stdout
    assert "unmeasured=0" in proc.stdout, proc.stdout


def test_a_path_that_matches_no_change_is_UNREADABLE_not_zero(tmp_path: Path) -> None:
    repo, base = simple(tmp_path, [])

    proc = census(repo, base, "--path", "src/typo_nope.py")

    assert token(proc) == "GUARD-CENSUS: UNREADABLE reason=path-no-match", proc.stdout
    assert proc.returncode == 2


def test_one_unmatched_path_among_matching_ones_is_still_UNREADABLE(tmp_path: Path) -> None:
    repo, base = simple(tmp_path, [])

    proc = census(repo, base, "--path", "h-mad", "--path", "nowhere")

    assert token(proc) == "GUARD-CENSUS: UNREADABLE reason=path-no-match"


def test_a_non_utf8_shell_file_is_UNREADABLE(tmp_path: Path) -> None:
    repo, base = make(tmp_path, {"h-mad/hooks/gate.sh": SH_BASE},
                      {"h-mad/hooks/gate.sh": b"#!/bin/bash\nX=\xff\xfe\n"})

    assert token(census(repo, base)) == "GUARD-CENSUS: UNREADABLE reason=unreadable-file"


# ------------------------------------------------------------- calibration

def _calibration(head: str) -> tuple[subprocess.CompletedProcess, list[str]]:
    repo = SKILL_DIR.parent
    for commit_id in ("3489f86b", head):
        have = subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"{commit_id}^{{commit}}"],
                              capture_output=True).returncode == 0
        if not have:
            pytest.skip(f"commit {commit_id} is not in this clone; the calibration needs it")
    proc = subprocess.run([sys.executable, str(SCRIPT), "--repo", str(repo), "--base", "3489f86b",
                           "--head", head, "--path", "h-mad/hooks", "--path", "h-mad/scripts"],
                          capture_output=True, text=True, timeout=300)
    got = candidates(proc)
    files = {"judge": "h-mad/scripts/h_mad_tdd_judge.py", "cx": "h-mad/hooks/h-mad-codex-tdd-gate.py",
             "ag": "h-mad/hooks/h-mad-agy-tdd-gate.py", "sh": "h-mad/hooks/h-mad-tdd-gate.sh"}
    listed = ("judge:737 sh:269 judge:341 judge:335 judge:330 judge:347 judge:732 sh:198 cx:289 ag:185 "
              "cx:303 ag:202 sh:344 judge:733 cx:293 ag:188 judge:344 judge:738").split()
    still = [n for n in listed if f"{files[n.split(':')[0]]}:{n.split(':')[1]}" in got]
    return proc, still


def test_the_gate_non_py_hand_census_is_listed_in_full() -> None:
    """Replay of analysis v3 §Census at 246531ba: the 16 lines, and v4's 2, must all be listed.

    Skipped, naming the missing object, in a clone that does not hold the commit.
    """
    proc, still = _calibration("246531ba")
    assert len(still) == 18, f"hand-census lines the tool did not list: only {len(still)} of 18 listed"
    assert counts(proc) == (170, 58, 112)


def test_after_the_task_8_rows_exactly_three_of_the_eighteen_remain() -> None:
    """At 8a3fa99e the 16 rows closed 15 lines. Measured: judge:344, judge:738 (analysis v4's two) and
    sh:269, whose `"docdata yes"` arm still has no row (`arms-not-all-anchored`)."""
    proc, still = _calibration("8a3fa99e")
    assert sorted(still) == ["judge:344", "judge:738", "sh:269"], still
    assert counts(proc)[:3] == (170, 73, 97)


def test_the_default_spec_dirs_anchor_handoffs_lines_in_the_real_history() -> None:
    """Commit 5db87e97 over handoff/scripts: only the default's second directory holds its rows."""
    repo = SKILL_DIR.parent
    for commit_id in ("5db87e97", "5db87e97~1"):
        if subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"{commit_id}^{{commit}}"],
                          capture_output=True).returncode != 0:
            pytest.skip(f"commit {commit_id} is not in this clone; the replay needs it")
    common = [sys.executable, str(SCRIPT), "--repo", str(repo), "--base", "5db87e97~1", "--head", "5db87e97",
              "--path", "handoff/scripts"]
    default = subprocess.run(common, capture_output=True, text=True, timeout=300)
    h_mad_only = subprocess.run(common + ["--spec-dir", "h-mad/tests/mutation-specs"],
                                capture_output=True, text=True, timeout=300)
    assert counts(default)[1] == 7, default.stdout
    assert counts(h_mad_only)[1] == 0, h_mad_only.stdout


def test_the_default_spec_dirs_anchor_handoffs_lines_in_the_real_history() -> None:
    """Commit 5db87e97 over handoff/scripts: only the default's second directory holds its rows."""
    repo = SKILL_DIR.parent
    for commit_id in ("5db87e97", "5db87e97~1"):
        if subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"{commit_id}^{{commit}}"],
                          capture_output=True).returncode != 0:
            pytest.skip(f"commit {commit_id} is not in this clone; the replay needs it")
    common = [sys.executable, str(SCRIPT), "--repo", str(repo), "--base", "5db87e97~1", "--head", "5db87e97",
              "--path", "handoff/scripts"]
    default = subprocess.run(common, capture_output=True, text=True, timeout=300)
    h_mad_only = subprocess.run(common + ["--spec-dir", "h-mad/tests/mutation-specs"],
                                capture_output=True, text=True, timeout=300)
    assert counts(default)[1] == 7, default.stdout
    assert counts(h_mad_only)[1] == 0, h_mad_only.stdout


# ------------------------------------------------------------ removed guards

GUARDED = "def g(x):\n    if x:\n        raise ValueError\n    return x\n"
UNGUARDED = "def g(x):\n    return x\n"


def test_a_guard_deleted_inside_a_modified_file_is_listed_as_removed(tmp_path: Path) -> None:
    repo, base = make(tmp_path, {"h-mad/scripts/mod.py": GUARDED}, {"h-mad/scripts/mod.py": UNGUARDED})

    proc = census(repo, base)

    assert counts(proc) == (0, 0, 0), "nothing was added"
    assert removed_lines(proc) == ['REMOVED: h-mad/scripts/mod.py:2 if "if x:"',
                                   'REMOVED: h-mad/scripts/mod.py:3 raise "raise ValueError"'], proc.stdout
    assert token(proc) == "GUARD-CENSUS: DONE decision=0 anchored=0 unanchored=0 removed=2 unparsed_base=0"


def test_a_modified_decision_line_is_both_a_candidate_and_removed(tmp_path: Path) -> None:
    head = GUARDED.replace("if x:", "if x > 1:")
    repo, base = make(tmp_path, {"h-mad/scripts/mod.py": GUARDED}, {"h-mad/scripts/mod.py": head})

    proc = census(repo, base)

    assert list(candidates(proc)) == ["h-mad/scripts/mod.py:2"], proc.stdout
    assert removed_lines(proc) == ['REMOVED: h-mad/scripts/mod.py:2 if "if x:"'], proc.stdout


def test_removed_lines_are_numbered_on_the_base_side(tmp_path: Path) -> None:
    base_py = "import os\n\n" + GUARDED
    head_py = "import os\n" + UNGUARDED
    repo, base = make(tmp_path, {"h-mad/scripts/mod.py": base_py}, {"h-mad/scripts/mod.py": head_py})

    assert removed_lines(census(repo, base))[0] == 'REMOVED: h-mad/scripts/mod.py:4 if "if x:"'


def test_a_removed_shell_decision_is_listed_by_the_shell_rule(tmp_path: Path) -> None:
    repo, base = make(tmp_path, {"h-mad/hooks/gate.sh": SH_HEAD}, {"h-mad/hooks/gate.sh": SH_BASE})

    proc = census(repo, base)

    assert removed_count(proc) == 8, proc.stdout
    assert 'REMOVED: h-mad/hooks/gate.sh:5 control,test "if [ \\"$want\\" = yes ]; then"' in proc.stdout, proc.stdout


def test_a_renamed_file_reads_as_delete_plus_add(tmp_path: Path) -> None:
    """`--no-renames`: the old file's decisions are all REMOVED, the new file's all candidates."""
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    base = commit(repo, {f"{SPECS}/keep.json": spec([]), "h-mad/scripts/old.py": PY_HEAD})
    git(repo, "mv", "h-mad/scripts/old.py", "h-mad/scripts/new.py")
    git(repo, "commit", "-q", "-am", "rename")

    proc = census(repo, base)

    assert counts(proc) == (6, 0, 6) and removed_count(proc) == 6, proc.stdout


def test_a_removed_line_in_an_undecodable_base_is_unparsed_base_not_unreadable(tmp_path: Path) -> None:
    repo, base = make(tmp_path, {"h-mad/scripts/mod.py": b"def f(x):\n    if x:\n        return '\xff'\n"},
                      {"h-mad/scripts/mod.py": b"def f(x):\n    return 1\n"})

    proc = census(repo, base)

    assert token(proc).endswith("removed=0 unparsed_base=1"), proc.stdout
    assert proc.returncode == 0


# ----------------------------------------------------------- several spec dirs

HANDOFF_SPECS = "handoff/tests/mutation-specs"


def two_trees(tmp_path: Path, with_h_mad_specs: bool = True) -> tuple[Path, str]:
    base_files = {"handoff/scripts/h.py": PY_BASE}
    if with_h_mad_specs:
        base_files[f"{SPECS}/keep.json"] = spec([])
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    base = commit(repo, base_files, "base")
    commit(repo, {"handoff/scripts/h.py": PY_HEAD,
                  f"{HANDOFF_SPECS}/h.json": spec([row("scripts/h.py", "    elif x < 0:\n")])}, "head")
    return repo, base


def test_the_default_reads_both_spec_directories(tmp_path: Path) -> None:
    repo, base = two_trees(tmp_path)

    assert counts(census(repo, base))[1] == 1


def test_a_missing_default_directory_is_not_an_error_when_the_other_exists(tmp_path: Path) -> None:
    repo, base = two_trees(tmp_path, with_h_mad_specs=False)

    proc = census(repo, base)

    assert counts(proc)[1] == 1, proc.stdout


def test_an_explicit_spec_dir_replaces_the_default(tmp_path: Path) -> None:
    repo, base = two_trees(tmp_path)

    assert counts(census(repo, base, "--spec-dir", SPECS))[1] == 0
    assert counts(census(repo, base, "--spec-dir", HANDOFF_SPECS))[1] == 1


def test_spec_dir_is_repeatable(tmp_path: Path) -> None:
    repo, base = two_trees(tmp_path)

    proc = census(repo, base, "--spec-dir", SPECS, "--spec-dir", HANDOFF_SPECS)

    assert counts(proc)[1] == 1


def test_a_missing_explicit_directory_stays_UNREADABLE_even_if_another_exists(tmp_path: Path) -> None:
    repo, base = two_trees(tmp_path)

    proc = census(repo, base, "--spec-dir", HANDOFF_SPECS, "--spec-dir", "no/such")

    assert token(proc) == "GUARD-CENSUS: UNREADABLE reason=spec-dir"


def test_no_default_directory_at_all_is_UNREADABLE(tmp_path: Path) -> None:
    repo, base = make(tmp_path, {"x/a.py": PY_BASE}, {"x/a.py": PY_HEAD})
    git(repo, "rm", "-q", f"{SPECS}/keep.json")
    git(repo, "commit", "-q", "-m", "no specs")

    assert token(census(repo, base)) == "GUARD-CENSUS: UNREADABLE reason=spec-dir"


# ------------------------------------------------------------- python holes

def test_an_awaited_call_statement_and_a_with_header_are_decision_lines(tmp_path: Path) -> None:
    head = ("async def f(x):\n"
            "    await deny(x)\n"
            "    with lock_or_refuse(x):\n"
            "        y = 1\n"
            "    async with gate(x):\n"
            "        pass\n")
    repo, base = make(tmp_path, {"h-mad/scripts/mod.py": PY_BASE}, {"h-mad/scripts/mod.py": head})

    got = candidates(census(repo, base))

    assert {k.rsplit(":", 1)[1]: v[0] for k, v in got.items()} == {"2": "call", "3": "with", "4": "assign",
                                                                   "5": "with"}, got


def test_a_bare_carriage_return_does_not_shift_the_attribution(tmp_path: Path) -> None:
    """ast counts a lone CR as a newline, git does not: lines are mapped by offset."""
    head = b"a = 1\rb = 2\nif a:\n    print(b)\n"
    repo, base = make(tmp_path, {"h-mad/scripts/cr.py": PY_BASE}, {"h-mad/scripts/cr.py": head})

    proc = census(repo, base)

    rows = [ln.split("\t") for ln in proc.stdout.splitlines() if ln.startswith("h-mad/scripts/cr.py:")]
    assert [(r[0], r[1]) for r in rows] == [("h-mad/scripts/cr.py:1", "assign"), ("h-mad/scripts/cr.py:1", "assign"),
                                            ("h-mad/scripts/cr.py:2", "if"), ("h-mad/scripts/cr.py:3", "call")], rows
    assert counts(proc) == (4, 0, 4)


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


def test_a_deleted_suffixless_shell_script_lists_its_decisions_as_removed(tmp_path: Path) -> None:
    """Only the deleted file's BASE blob can say it was a shell script; the head has nothing to read."""
    repo, base = make(tmp_path, {"h-mad/bin/launch": SH_HEAD}, {}, remove=("h-mad/bin/launch",))

    proc = census(repo, base)

    assert removed_count(proc) == 8, proc.stdout
    assert " deleted=1" in proc.stdout and "other=0" in proc.stdout, proc.stdout


# ------------------------------------------------- second review: base side, counters, paths

def scope(proc: subprocess.CompletedProcess, key: str) -> int:
    m = re.search(rf"\b{key}=(\d+)", proc.stdout)
    assert m, proc.stdout
    return int(m[1])


def skipped_line(proc: subprocess.CompletedProcess) -> str:
    return next(ln for ln in proc.stdout.splitlines() if ln.startswith("SKIPPED: "))


def unparsed(proc: subprocess.CompletedProcess) -> list[str]:
    return [ln for ln in proc.stdout.splitlines() if ln.startswith("UNPARSED-BASE: ")]


def test_a_deleted_gitlink_does_not_lose_the_census(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    commit(repo, {f"{SPECS}/keep.json": spec([]), "h-mad/scripts/mod.py": PY_BASE})
    sha = git(repo, "rev-parse", "HEAD").strip()
    git(repo, "update-index", "--add", "--cacheinfo", f"160000,{sha},h-mad/sub")
    git(repo, "commit", "-q", "-m", "gitlink")
    base = git(repo, "rev-parse", "HEAD").strip()
    git(repo, "rm", "-q", "--cached", "h-mad/sub")
    commit(repo, {"h-mad/scripts/mod.py": PY_HEAD}, "drop it and change something")

    proc = census(repo, base)

    assert counts(proc) == (6, 0, 6), proc.stdout
    assert scope(proc, "link") == 1, skipped_line(proc)


def test_a_deleted_symlink_is_a_link_not_python(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    commit(repo, {f"{SPECS}/keep.json": spec([]), "h-mad/scripts/t.py": PY_BASE})
    (repo / "h-mad/scripts/s.py").symlink_to("t-1.py")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "link")
    base = git(repo, "rev-parse", "HEAD").strip()
    git(repo, "rm", "-q", "h-mad/scripts/s.py")
    git(repo, "commit", "-q", "-m", "rm link")

    proc = census(repo, base)

    assert counts(proc) == (0, 0, 0) and removed_count(proc) == 0, proc.stdout
    assert scope(proc, "link") == 1 and not unparsed(proc), proc.stdout


def test_a_symlink_changed_to_a_file_reads_only_the_file_side(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    commit(repo, {f"{SPECS}/keep.json": spec([]), "h-mad/scripts/t.py": PY_BASE})
    (repo / "h-mad/scripts/s.py").symlink_to("t-1.py")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "link")
    base = git(repo, "rev-parse", "HEAD").strip()
    (repo / "h-mad/scripts/s.py").unlink()
    commit(repo, {"h-mad/scripts/s.py": PY_HEAD}, "now a file")

    proc = census(repo, base)

    assert counts(proc) == (6, 0, 6) and removed_count(proc) == 0, proc.stdout


def test_a_python_file_replaced_by_a_symlink_lists_its_removed_guards(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    base = commit(repo, {f"{SPECS}/keep.json": spec([]), "h-mad/scripts/g.py": GUARDED,
                         "h-mad/scripts/t.py": PY_BASE})
    (repo / "h-mad/scripts/g.py").unlink()
    (repo / "h-mad/scripts/g.py").symlink_to("t.py")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "now a link")

    proc = census(repo, base)

    assert removed_count(proc) == 3 and counts(proc)[0] == 0, proc.stdout


def test_an_unparsable_base_is_listed_and_the_census_goes_on(tmp_path: Path) -> None:
    repo, base = make(tmp_path, {"h-mad/scripts/broken.py": "def f(:\n    if x:\n", "h-mad/scripts/mod.py": PY_BASE},
                      {"h-mad/scripts/mod.py": PY_HEAD}, remove=("h-mad/scripts/broken.py",))

    proc = census(repo, base)

    assert counts(proc) == (6, 0, 6), proc.stdout
    assert unparsed(proc) == ["UNPARSED-BASE: h-mad/scripts/broken.py"], proc.stdout
    assert token(proc) == "GUARD-CENSUS: DONE decision=6 anchored=0 unanchored=6 removed=1 unparsed_base=1"


def test_a_broken_file_that_is_fixed_is_unparsed_base_not_unreadable(tmp_path: Path) -> None:
    repo, base = make(tmp_path, {"h-mad/scripts/mod.py": "def f(:\n"}, {"h-mad/scripts/mod.py": PY_HEAD})

    proc = census(repo, base)

    assert counts(proc) == (6, 0, 6) and len(unparsed(proc)) == 1, proc.stdout


def test_a_non_utf8_base_is_unparsed_base_too(tmp_path: Path) -> None:
    repo, base = make(tmp_path, {"h-mad/hooks/gate.sh": b"#!/bin/bash\nX=\xff\n"}, {"h-mad/hooks/gate.sh": SH_BASE})

    proc = census(repo, base)

    assert len(unparsed(proc)) == 1 and removed_count(proc) == 0, proc.stdout


def test_an_unparsable_head_side_stays_UNREADABLE(tmp_path: Path) -> None:
    repo, base = make(tmp_path, {"h-mad/scripts/mod.py": PY_BASE}, {"h-mad/scripts/mod.py": "def f(:\n"})

    assert token(census(repo, base)) == "GUARD-CENSUS: UNREADABLE reason=unreadable-file"


@pytest.mark.parametrize("spelled", [".", "./", "ABS"])
def test_a_path_naming_the_whole_repo_matches_everything(tmp_path: Path, spelled: str) -> None:
    repo, base = simple(tmp_path, [])
    value = str(repo) if spelled == "ABS" else spelled

    proc = census(repo, base, "--path", value)

    assert counts(proc) == (6, 0, 6), proc.stdout


def test_a_path_outside_the_repository_is_UNREADABLE(tmp_path: Path) -> None:
    repo, base = simple(tmp_path, [])

    assert token(census(repo, base, "--path", str(tmp_path))) == "GUARD-CENSUS: UNREADABLE reason=path-no-match"


def test_the_base_side_language_comes_from_the_old_blob(tmp_path: Path) -> None:
    """bash -> python: the old shell text must not be parsed as Python, nor the new Python as shell."""
    repo, base = make(tmp_path, {"h-mad/bin/tool": SH_HEAD}, {"h-mad/bin/tool": "#!/usr/bin/env python3\n" + PY_HEAD})

    proc = census(repo, base)

    assert counts(proc)[0] == 6 and removed_count(proc) == 8 and not unparsed(proc), proc.stdout


def test_a_python_script_that_became_data_still_lists_its_removed_guards(tmp_path: Path) -> None:
    repo, base = make(tmp_path, {"h-mad/bin/tool": "#!/usr/bin/env python3\nimport sys\nif sys.argv:\n    raise SystemExit\n"},
                      {"h-mad/bin/tool": "just data\n"})

    proc = census(repo, base)

    assert removed_count(proc) == 2, proc.stdout
    assert counts(proc) == (0, 0, 0)


@pytest.mark.parametrize("name", ["a.vue", "a.mts", "a.pyw", "a.pyi", "a.dart", "a.awk", "a.cxx", "a.tcl",
                                  "weird.xyz", "Makefile"])
def test_an_unknown_suffix_is_unmeasured_not_a_document(tmp_path: Path, name: str) -> None:
    repo, base = make(tmp_path, {"h-mad/scripts/mod.py": PY_BASE}, {f"x/{name}": "stuff\n"})

    proc = census(repo, base)

    assert scope(proc, "unmeasured") == 1 and scope(proc, "other") == 0, proc.stdout


@pytest.mark.parametrize("name", ["a.md", "a.json", "a.log", "a.xsd", "a.csv", "a.txt", "a.yaml", "a.tex",
                                  "run/rc", "run/stderr", "LICENSE", ".gitignore", "a.png"])
def test_documents_and_data_are_other(tmp_path: Path, name: str) -> None:
    repo, base = make(tmp_path, {"h-mad/scripts/mod.py": PY_BASE}, {f"x/{name}": "stuff\n"})

    proc = census(repo, base)

    assert scope(proc, "other") == 1 and scope(proc, "unmeasured") == 0, proc.stdout


def test_the_skipped_counters_are_disjoint_and_never_count_a_measured_file(tmp_path: Path) -> None:
    repo, base = make(tmp_path, {"h-mad/scripts/gone.py": GUARDED, "data.bin": b"\x00\x01", "h-mad/tests/test_a.py": PY_BASE},
                      {"data.bin": b"\x00\x02\x00", "h-mad/tests/test_a.py": PY_HEAD}, remove=("h-mad/scripts/gone.py",))

    proc = census(repo, base)

    assert scope(proc, "files") == 1 and scope(proc, "deleted") == 1, proc.stdout
    assert "deleted=" not in skipped_line(proc), skipped_line(proc)
    assert scope(proc, "binary") == 1 and scope(proc, "tests") == 1, skipped_line(proc)


def test_the_unparsable_base_replay_on_the_real_history() -> None:
    """ff8234bb deleted a hematology-paper-writer copy whose hpw_upgrade_core.py never parsed."""
    repo = SKILL_DIR.parent
    for commit_id in ("ff8234bb", "ff8234bb~1"):
        if subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"{commit_id}^{{commit}}"],
                          capture_output=True).returncode != 0:
            pytest.skip(f"commit {commit_id} is not in this clone; the replay needs it")
    proc = subprocess.run([sys.executable, str(SCRIPT), "--repo", str(repo), "--base", "ff8234bb~1",
                           "--head", "ff8234bb"], capture_output=True, text=True, timeout=300)
    assert proc.returncode == 0 and token(proc).startswith("GUARD-CENSUS: DONE"), proc.stdout
    assert "UNPARSED-BASE: hematology-paper-writer/tools/draft_generator/hpw_upgrade_core.py" in proc.stdout


@pytest.mark.parametrize("name", ["hooks/pre-commit.sample", "hooks/rc", "hooks/run.conf"])
def test_a_shell_shebang_beats_the_document_allow_list(tmp_path: Path, name: str) -> None:
    repo, base = sh_repo(tmp_path, None, SH_HEAD, name)

    assert counts(census(repo, base))[0] == 8


def test_a_python_shebang_beats_the_document_allow_list(tmp_path: Path) -> None:
    head = "#!/usr/bin/env python3\nx = 1\n"
    repo, base = make(tmp_path, {"run.conf": head}, {"run.conf": head + "if x:\n    pass\n"})

    assert "run.conf:3" in candidates(census(repo, base))


def test_a_dot_beside_another_path_still_names_everything(tmp_path: Path) -> None:
    repo, base = make(tmp_path, {"b.py": "x = 1\n", "sub/a.py": "x = 1\n"},
                      {"b.py": "x = 1\nif x:\n    pass\n", "sub/a.py": "x = 1\nif x:\n    pass\n"})

    listed = candidates(census(repo, base, "--path", ".", "--path", "sub"))
    assert "b.py:2" in listed and "sub/a.py:2" in listed, listed
