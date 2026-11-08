"""Listing and non-Python scoring contracts for the shared TDD judge."""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

import pytest

from tdd_gate_support import hermetic_env, write_plan, write_state

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
JUDGE_PATH = SCRIPTS / "h_mad_tdd_judge.py"
sys.path.insert(0, str(SCRIPTS))
import h_mad_tdd_judge as judge  # noqa: E402


@pytest.fixture(autouse=True)
def _strip_ambient(monkeypatch):
    for name in list(os.environ):
        if name.startswith("CLAUDE") or name in (
            "HPW_AGENT_BACKEND", "HMAD_HOST", "HMAD_CODEX_UNAVAILABLE", "CODEX_PROJECT_DIR",
            "PYTHONPATH",
        ):
            monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")


@pytest.fixture
def root(tmp_path):
    path = tmp_path / 'root "agent" % H-MAD:MARKER\nnext'
    path.mkdir()
    return path


def _records(root, *keys):
    write_state(root, {key: {"phase": "step5"} for key in keys or ("f",)})
    chain = judge.read_chain(root, root / "scripts/tool.sh")
    assert chain.value == "active", chain
    return chain.records


def _plan(root, *production, key="f", test="tests/test_tool.py"):
    entries = ", ".join(f"`{entry}`" for entry in production)
    return write_plan(
        root, key,
        '## Task 1: agent "quoted" \\ input\n'
        '[H-MAD:MARKER] human note with `odd * markdown`\n'
        "<!-- hostile input: **not a field**\nsecond line -->\n"
        f"**Production file**: {entries}\n"
        f"**Test file**: `{test}`\n"
        "**Task shape**: `new-behaviour`\n",
    )


def _target(root, relative="scripts/tool.sh"):
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("#!/bin/sh\n", encoding="utf-8")
    return target


def _test_file(root, body):
    path = root / "tests/test_tool.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _cli(root, *names):
    argv = [sys.executable, str(JUDGE_PATH), "listing", "--root", str(root)]
    for name in names:
        argv.extend(("--name", name))
    return subprocess.run(argv, env=hermetic_env(), stdin=subprocess.DEVNULL,
                          capture_output=True, text=True, timeout=60.0, check=False)


def _assert_cli(result, line):
    assert result.returncode == 0, result.stderr
    assert result.stdout == line + "\n", "listing must emit exactly the specified stdout line"
    assert result.stderr == "", result.stderr


def test_listing_selects_the_least_listed_name(root):
    records = _records(root)
    zulu = _target(root, "scripts/zulu.sh")
    alpha = root / "zzz/alpha.sh"
    alpha.parent.mkdir()
    os.link(zulu, alpha)
    _plan(root, "scripts/zulu.sh", "zzz/alpha.sh")

    result = judge.listing(root, [zulu, alpha], records)

    assert result == judge.Listing("listed", alpha, None, ""), (
        "listing must select the least basename, independent of input or directory order", result)


def test_listing_any_canonical_name_lists_the_target(root):
    records = _records(root)
    target = _target(root)
    hard = root / "scripts/hard.sh"
    os.link(target, hard)
    _plan(root, "scripts/tool.sh")

    result = judge.listing(root, [hard, target], records)

    assert result == judge.Listing("listed", target, None, ""), (
        "a later listed canonical hard-link name must be considered", result)


def test_listing_a_target_only_a_later_readable_plan_lists_is_listed(root):
    records = _records(root, "f", "g")
    target = _target(root)
    _plan(root, "scripts/other.sh", key="f", test="tests/test_other.py")
    _plan(root, "scripts/tool.sh", key="g")

    result = judge.listing(root, [target], records)

    assert result == judge.Listing("listed", target, None, ""), (
        "every readable active plan is consulted, not only the first", result)


def test_listing_not_listed_when_no_name_matches(root):
    records = _records(root)
    target = _target(root)
    _plan(root, "scripts/other.sh")

    result = judge.listing(root, [target], records)

    assert result == judge.Listing("not-listed", None, None, ""), (
        "a readable plan for another production file must not list this target", result)


def test_listing_absent_plan_is_not_listed(root):
    records = _records(root)

    result = judge.listing(root, [root / "scripts/tool.sh"], records)

    assert result == judge.Listing("not-listed", None, None, ""), (
        "an absent impl-plan is not an unreadable plan", result)


def test_listing_listed_outranks_an_unreadable_sibling(root):
    records = _records(root, "f", "g")
    target = _target(root)
    hard = root / "scripts/hard.sh"
    os.link(target, hard)
    _plan(root, "scripts/tool.sh")
    bad = write_plan(root, "g", "placeholder")
    bad.write_bytes(b"\xff\xfe")

    result = judge.listing(root, [hard, target], records)

    assert result == judge.Listing("listed", target, None, ""), (
        "a readable listing of either name must outrank an unreadable sibling plan", result)


def test_listing_unreadable_when_no_plan_lists_the_target(root):
    records = _records(root, "f", "g")
    target = _target(root)
    hard = root / "scripts/hard.sh"
    os.link(target, hard)
    _plan(root, "scripts/other.sh")
    bad = write_plan(root, "g", "placeholder")
    bad.write_bytes(b"\xff\xfe")

    result = judge.listing(root, [hard, target], records)

    assert result == judge.Listing("unreadable", None, bad, "UnicodeDecodeError"), (
        "without a readable listing, return the unreadable impl-plan and exception", result)


@pytest.mark.parametrize("case", ["plan-entry-case", "absent-leaf-case", "other-directory-hard-link"])
def test_listing_residual_spellings_are_not_listed(root, case):
    records = _records(root)
    if case == "plan-entry-case":
        target = _target(root)
        entry = "scripts/TOOL.sh"
    elif case == "absent-leaf-case":
        target = root / "scripts/TOOL.sh"
        target.parent.mkdir()
        entry = "scripts/tool.sh"
        assert not target.exists() and not (root / entry).exists()
    else:
        original = _target(root)
        target = root / "other/tool.sh"
        target.parent.mkdir()
        os.link(original, target)
        assert os.path.samefile(original, target)
        entry = "scripts/tool.sh"
    _plan(root, entry)

    result = judge.listing(root, [target], records)

    assert result == judge.Listing("not-listed", None, None, ""), (
        f"{case}: listing must retain the matcher's realpath spelling comparison", result)


def test_listing_cli_chain_none_prints_not_listed(root):
    _assert_cli(_cli(root, "scripts/tool.sh"), "TDD-LISTING: not-listed")


def test_listing_cli_chain_unreadable_prints_unreadable(root):
    state = write_state(root, {"f": {"phase": "step5"}})
    state.write_bytes(b"\xff\xfe")

    _assert_cli(_cli(root, "scripts/tool.sh"),
                f"TDD-LISTING: unreadable file={quote(str(state), safe='/._-')} error=UnicodeDecodeError")


def test_listing_cli_active_not_listed_prints_not_listed(root):
    _records(root)
    _plan(root, "scripts/other.sh")

    _assert_cli(_cli(root, "scripts/tool.sh"), "TDD-LISTING: not-listed")


def test_listing_cli_active_unreadable_prints_unreadable(root):
    _records(root)
    plan = write_plan(root, "f", "placeholder")
    plan.write_bytes(b"\xff\xfe")

    _assert_cli(_cli(root, "scripts/tool.sh"),
                f"TDD-LISTING: unreadable file={quote(str(plan), safe='/._-')} error=UnicodeDecodeError")


def test_listing_cli_listed_prints_the_encoded_target(root):
    _records(root)
    target = _target(root, 'scripts/tool"human"%[H-MAD:MARKER].sh')
    hard = root / "scripts/hard.sh"
    os.link(target, hard)
    _plan(root, target.relative_to(root).as_posix())

    _assert_cli(_cli(root, "scripts/hard.sh", target.relative_to(root).as_posix()),
                f"TDD-LISTING: listed target={quote(str(target), safe='/._-')}")


def test_listing_cli_internal_exception_exits_2(root, monkeypatch, capsys):
    def raiser(*args, **kwargs):
        raise RuntimeError('agent "quoted" % [H-MAD:MARKER]')

    monkeypatch.setattr(judge, "read_chain", raiser)

    assert judge.main(["listing", "--root", str(root), "--name", "x.sh"]) == 2, (
        "an internal listing exception must return 2")
    captured = capsys.readouterr()
    assert captured.out == "", "an internal listing exception must not print a verdict"
    assert captured.err == 'RuntimeError: agent "quoted" % [H-MAD:MARKER]\n'


@pytest.mark.parametrize("suffix", ["sh", "extensionless"])
def test_target_module_names_is_empty_for_a_non_py_target(root, suffix):
    target = root / ("scripts/tool.sh" if suffix == "sh" else "scripts/tool")

    assert judge.target_module_names(root, target) == frozenset(), (
        "non-Python targets must have no Python import module names")


def test_non_py_module_not_found_scores_pytest_error(root):
    records = _records(root)
    target = root / "scripts/tool.sh"
    _plan(root, "scripts/tool.sh")
    test = _test_file(root, "import tool\n\ndef test_collection():\n    assert True\n")
    assert not target.exists(), "the non-Python production target must be absent"
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", str(test), "-q", "-p", "no:cacheprovider"],
        cwd=root, env=hermetic_env(), stdin=subprocess.DEVNULL,
        capture_output=True, text=True, timeout=60.0, check=False,
    )
    output = proc.stdout + "\n" + proc.stderr
    assert re.search(r"\b1 error\b", output), output
    assert "ModuleNotFoundError: No module named 'tool'" in output, output
    import_target = judge.ImportTarget(judge.target_module_names(root, target), str(target), False)

    scored = judge.score(output, False, import_target)
    verdict = judge.judge(root, target, records, fallback_interpreter=sys.executable)

    assert (scored, verdict.decision, verdict.kind) == ("pytest-error", "DENY", "pytest-error"), (
        "a non-Python target cannot repair a Python collection import error", scored, verdict)


def test_judge_listed_non_py_failing_test_is_red_measured(root):
    records = _records(root)
    target = _target(root)
    _plan(root, "scripts/tool.sh")
    test = _test_file(root, "def test_red():\n    assert False\n")

    verdict = judge.judge(root, target, records, fallback_interpreter=sys.executable)

    assert verdict == judge.Verdict("ALLOW", "red-measured", "", "impl-plan", test), (
        "a listed non-Python target must use its plan's failing test", verdict)


def test_judge_listed_non_py_passing_test_is_test_passing(root):
    records = _records(root)
    target = _target(root)
    _plan(root, "scripts/tool.sh")
    _test_file(root, "def test_green():\n    assert True\n")

    verdict = judge.judge(root, target, records, fallback_interpreter=sys.executable)

    assert (verdict.decision, verdict.kind) == ("DENY", "test-passing"), verdict
    assert "tests/test_tool.py: test-passing" in verdict.reason, verdict.reason


def test_judge_listed_non_py_absent_test_is_test_missing(root):
    records = _records(root)
    target = _target(root)
    _plan(root, "scripts/tool.sh")

    verdict = judge.judge(root, target, records, fallback_interpreter=sys.executable)

    assert (verdict.decision, verdict.kind) == ("DENY", "test-missing"), verdict
    assert "tests/test_tool.py" in verdict.reason, verdict.reason


def test_judge_listed_non_py_with_no_pytest_file_is_test_missing(root):
    records = _records(root)
    target = _target(root)
    _plan(root, "scripts/tool.sh", test="tests/tool.bats")
    other = root / "tests/tool.bats"
    other.parent.mkdir()
    other.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")

    verdict = judge.judge(root, target, records, fallback_interpreter=sys.executable)

    assert (verdict.decision, verdict.kind) == ("DENY", "test-missing"), verdict
    assert "matched" in verdict.reason, verdict.reason


def test_judge_unlisted_non_py_is_no_test_resolved(root):
    records = _records(root)
    target = _target(root)
    _plan(root, "scripts/other.sh")
    _test_file(root, "def test_red():\n    assert False\n")

    verdict = judge.judge(root, target, records, fallback_interpreter=sys.executable)

    assert (verdict.decision, verdict.kind) == ("DENY", "no-test-resolved"), verdict
    assert "matched none" in verdict.reason, verdict.reason
