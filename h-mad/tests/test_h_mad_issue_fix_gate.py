"""Wave 4b candidate `file-issue-then-fix-under-TDD` (recurrence 14, verdict yes).

The shape ran 14 times in one session: measure something, file an issue carrying
the measurement, write ONE failing test file per issue, fix it, close via a
`Closes #N` trailer. What actually goes wrong in that loop is never the fixing —
it is the LINKAGE. An issue gets fixed with no test naming it, or a test lands
with no trailer closing the issue, and six weeks later nothing on disk says which
measurement the test exists to pin.

This gate checks the linkage and nothing else. It deliberately does NOT file or
close issues: `invariants.base.md` §"No new external dependency" forbids the
skill acquiring a new CLI, and `gh` is not one of its dependencies. Printing a
suggested `gh` command is not a dependency; requiring it to run would be.

Verdict discipline per `invariants.base.md` §"Audit-gate signal discipline": a
PASS/FAIL verdict is an `ISSUEFIX:` stdout token with **exit 0**; a non-zero exit
is reserved for genuine operational errors.
"""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GATE = REPO_ROOT / "h-mad" / "scripts" / "h_mad_issue_fix_gate.py"


def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True, check=True)


def _repo(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir(parents=True)
    _git(repo.parent, "init", "r")
    _git(repo, "config", "user.email", "t@e")
    _git(repo, "config", "user.name", "T")
    (repo / "seed.txt").write_text("seed\n")
    _git(repo, "add", "seed.txt")
    _git(repo, "commit", "-m", "seed")
    _git(repo, "branch", "-M", "main")
    return repo


def _run(repo, *args):
    return subprocess.run(
        [sys.executable, str(GATE), "--repo-root", str(repo), *args],
        capture_output=True, text=True)


def _land(repo, test_rel, body, message):
    p = repo / test_rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body)
    _git(repo, "add", str(test_rel))
    _git(repo, "commit", "-m", message)
    return p


def test_pass_when_test_names_issue_and_trailer_closes_it(tmp_path):
    repo = _repo(tmp_path)
    _land(repo, "tests/test_thing.py", "# pins #42\ndef test_x():\n    assert True\n",
          "fix: the thing\n\nCloses #42")
    r = _run(repo, "--issue", "42", "--test", "tests/test_thing.py", "--base", "main")
    assert r.returncode == 0, r.stderr
    assert "ISSUEFIX: PASS" in r.stdout
    assert "issue=42" in r.stdout


def test_fail_is_exit_zero_with_a_token(tmp_path):
    # Signal discipline: FAIL is a verdict, not an operational error, so it must
    # not exit non-zero -- a non-zero exit registers as a PostToolUseFailure.
    repo = _repo(tmp_path)
    r = _run(repo, "--issue", "42", "--test", "tests/nope.py", "--base", "main")
    assert r.returncode == 0, r.stderr
    assert "ISSUEFIX: FAIL" in r.stdout
    assert "test_missing" in r.stdout


def test_fail_when_test_does_not_name_the_issue(tmp_path):
    # A test that does not name its issue loses the link to the measurement.
    repo = _repo(tmp_path)
    _land(repo, "tests/test_thing.py", "def test_x():\n    assert True\n",
          "fix: the thing\n\nCloses #42")
    r = _run(repo, "--issue", "42", "--test", "tests/test_thing.py", "--base", "main")
    assert r.returncode == 0
    assert "ISSUEFIX: FAIL" in r.stdout
    assert "test_omits_issue" in r.stdout


def test_fail_when_no_closing_trailer(tmp_path):
    repo = _repo(tmp_path)
    _land(repo, "tests/test_thing.py", "# pins #42\ndef test_x():\n    assert True\n",
          "fix: the thing")
    r = _run(repo, "--issue", "42", "--test", "tests/test_thing.py", "--base", "main")
    assert r.returncode == 0
    assert "ISSUEFIX: FAIL" in r.stdout
    assert "trailer_missing" in r.stdout


def test_accepts_fixes_and_resolves_trailers(tmp_path):
    # GitHub closes on Closes/Fixes/Resolves; accepting only one would fail a
    # correctly-closed issue.
    for word in ("Fixes", "Resolves", "closes"):
        repo = _repo(tmp_path / word)
        _land(repo, "tests/test_thing.py", "# pins #7\ndef test_x():\n    assert True\n",
              f"fix: thing\n\n{word} #7")
        r = _run(repo, "--issue", "7", "--test", "tests/test_thing.py", "--base", "main")
        assert "ISSUEFIX: PASS" in r.stdout, f"{word} not accepted: {r.stdout}"


def test_issue_number_matches_on_a_boundary_not_a_prefix(tmp_path):
    # `#4` must not be satisfied by `#42` -- a prefix match would let the wrong
    # issue's test and trailer pass the gate for this one.
    repo = _repo(tmp_path)
    _land(repo, "tests/test_thing.py", "# pins #42\ndef test_x():\n    assert True\n",
          "fix: thing\n\nCloses #42")
    r = _run(repo, "--issue", "4", "--test", "tests/test_thing.py", "--base", "main")
    assert "ISSUEFIX: FAIL" in r.stdout
    assert "test_omits_issue" in r.stdout
    assert "trailer_missing" in r.stdout


def test_operational_error_exits_two(tmp_path):
    # Not a git repo -> cannot compute a verdict at all. That IS the reserved
    # non-zero case, and it must be distinguishable from FAIL.
    plain = tmp_path / "plain"
    plain.mkdir()
    r = _run(plain, "--issue", "1", "--test", "tests/t.py", "--base", "main")
    assert r.returncode == 2
    assert "ISSUEFIX:" not in r.stdout


def test_emits_a_gh_command_without_requiring_gh(tmp_path):
    # The base invariant forbids a new CLI dependency. Suggesting the command is
    # allowed; shelling out to it is not. Assert the script never invokes gh.
    src = GATE.read_text(encoding="utf-8")
    assert 'subprocess' in src
    for forbidden in ('"gh"', "'gh'", "gh issue", "gh api"):
        assert f"run([{forbidden}" not in src, f"gate shells out to gh via {forbidden}"
    repo = _repo(tmp_path)
    r = _run(repo, "--issue", "42", "--test", "tests/nope.py", "--base", "main",
             "--suggest")
    assert "gh issue" in r.stdout, "--suggest should print the command for the operator"


def test_non_numeric_issue_is_an_operational_error(tmp_path):
    # `--issue HEAD` or a typo'd slug cannot produce a meaningful verdict: the
    # regexes would be built from junk and quietly match nothing, which reads as
    # FAIL ("not linked") when the truth is "you asked the wrong question".
    # Surfaced by mutation testing -- the guard existed and nothing covered it.
    repo = _repo(tmp_path)
    r = _run(repo, "--issue", "not-a-number", "--test", "tests/t.py", "--base", "main")
    assert r.returncode == 2
    assert "ISSUEFIX:" not in r.stdout
    assert "must be a number" in r.stderr


def test_leading_hash_on_issue_is_accepted(tmp_path):
    # `--issue #42` is the form a human copies out of a tracker.
    repo = _repo(tmp_path)
    _land(repo, "tests/test_thing.py", "# pins #42\ndef test_x():\n    assert True\n",
          "fix: thing\n\nCloses #42")
    r = _run(repo, "--issue", "#42", "--test", "tests/test_thing.py", "--base", "main")
    assert r.returncode == 0
    assert "ISSUEFIX: PASS" in r.stdout
