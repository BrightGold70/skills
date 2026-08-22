"""Coverage for the J18 guard: the fixture that keeps the suite off the live pin file.

J18: mutation-testing `_pin_file`'s explicit-override branch -- the branch every test
relies on to point `HMAD_ORCA_PIN_FILE` at a temp path -- redirected the WHOLE suite's
pin writes onto the developer's real `<repo>/.h-mad/orca-pins.env`, replacing two live
agent handles with test fixtures. The suite reported 642 passed throughout, because
tests assert what a file contains and never where it is *not*. It was caught only when
the next `hmad-dispatch env` showed handles that had never existed.

The remedy was `conftest._protect_live_pin_file`. This file is the coverage that remedy
never got. Its younger sibling `_protect_live_wire_registry` -- written later, modelled
on it -- has both a fixture test and a mutation test in test_h_mad_wire_registry.py;
the original had neither, and a session-scoped autouse fixture that nothing tests is one
deletion away from being gone, silently, because the suite stays green either way.

That asymmetry is the whole point: the protection J18 exists to provide was the one
piece of it left unguarded.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import conftest  # noqa: E402


def test_pin_file_guard_fires_on_a_deliberate_live_file_leak(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Drive the fixture directly: a modified live pin file must fail AND be restored."""
    target = tmp_path / "orca-pins.env"
    target.write_text("HMAD_ORCA_CODEX_TERMINAL=term_real\n", encoding="utf-8")
    monkeypatch.setattr(conftest, "_live_pin_file", lambda: target)

    guard = conftest._protect_live_pin_file.__wrapped__()
    next(guard)
    target.write_text("HMAD_ORCA_CODEX_TERMINAL=term_leaked\n", encoding="utf-8")

    with pytest.raises(pytest.fail.Exception, match="live pin file"):
        next(guard)

    assert target.read_text(encoding="utf-8") == "HMAD_ORCA_CODEX_TERMINAL=term_real\n", (
        "the guard must RESTORE the real handles, not merely report the leak"
    )


def test_pin_file_guard_removes_a_file_the_suite_created(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Absent-before is the live case on this machine, and it inverts the restore.

    When no pin file exists at session start, `before` is None and there is nothing to
    write back -- the correct repair is to DELETE what the suite created. A guard that
    only handled the overwrite case would leave a fabricated pin file behind on exactly
    the machines that have no agents pinned.
    """
    target = tmp_path / "orca-pins.env"
    assert not target.exists()
    monkeypatch.setattr(conftest, "_live_pin_file", lambda: target)

    guard = conftest._protect_live_pin_file.__wrapped__()
    next(guard)
    target.write_text("HMAD_ORCA_AGY_TERMINAL=term_invented\n", encoding="utf-8")

    with pytest.raises(pytest.fail.Exception, match="live pin file"):
        next(guard)

    assert not target.exists(), "a file the suite invented must be removed, not restored"


def test_pin_file_guard_is_silent_when_nothing_changed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The other direction: a guard that fires on a clean run is worse than none.

    Without this, the two tests above are satisfied by a fixture that always fails.
    """
    target = tmp_path / "orca-pins.env"
    target.write_text("HMAD_ORCA_CODEX_TERMINAL=term_real\n", encoding="utf-8")
    monkeypatch.setattr(conftest, "_live_pin_file", lambda: target)

    guard = conftest._protect_live_pin_file.__wrapped__()
    next(guard)
    with pytest.raises(StopIteration):
        next(guard)
    assert target.read_text(encoding="utf-8") == "HMAD_ORCA_CODEX_TERMINAL=term_real\n"


def test_pin_file_guard_mutation_is_caught_by_harness(tmp_path: Path) -> None:
    """Prove the guard BITES, not merely that it exists.

    Mutating its comparison to `if True:` makes the fixture return early on every run --
    the exact shape of the guard being deleted. The baseline command runs only the leak
    test above, so the harness measures this guard and nothing else.
    """
    from h_mad_mutation_harness import run_spec

    root = Path(__file__).resolve().parents[2]
    spec = tmp_path / "mutations.json"
    spec.write_text(json.dumps({
        "root": str(root),
        "command": [
            sys.executable, "-m", "pytest",
            "h-mad/tests/test_h_mad_pin_file_guard.py::"
            "test_pin_file_guard_fires_on_a_deliberate_live_file_leak", "-q",
        ],
        "mutations": [{
            "name": "make pin-file guard permissive",
            "file": "h-mad/tests/conftest.py",
            "find": "    # J18 pin-file guard mutation anchor. Distinct from the wire-registry anchor",
            "replace": "    if True:\n        return\n    # J18 pin-file guard mutation anchor. Distinct from the wire-registry anchor",
        }],
    }), encoding="utf-8")
    result = run_spec(spec)
    assert result["verdict"] == "ALL_CAUGHT", result
