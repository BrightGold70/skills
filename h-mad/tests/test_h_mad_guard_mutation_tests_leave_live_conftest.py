"""The conftest-guard mutation tests must never write the live `h-mad/tests/conftest.py`.

`test_pin_file_guard_mutation_is_caught_by_harness` and
`test_wire_registry_guard_mutation_is_caught_by_harness` prove their conftest guards
bite by mutating conftest through `run_spec`. When the spec root was the live repo,
the harness rewrote the TRACKED conftest on disk for the length of each inner pytest,
and any concurrent pytest in the same tree imported the mutant.

A before/after hash of the file cannot see that: the harness restores it. So this
observes the live file at the moment each inner command runs -- the window a sibling
pytest would import it in.
"""

import hashlib
import sys
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(TESTS.parent / "scripts"))
import h_mad_mutation_harness as harness  # noqa: E402
import test_h_mad_pin_file_guard  # noqa: E402
import test_h_mad_wire_registry  # noqa: E402

LIVE_CONFTEST = TESTS / "conftest.py"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize("mutation_test", [
    test_h_mad_pin_file_guard.test_pin_file_guard_mutation_is_caught_by_harness,
    test_h_mad_wire_registry.test_wire_registry_guard_mutation_is_caught_by_harness,
], ids=["pin-file-guard", "wire-registry-guard"])
def test_guard_mutation_test_never_writes_the_live_conftest(
    mutation_test, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = _sha(LIVE_CONFTEST)
    seen: list[str] = []
    real_run = harness._run

    def observing_run(command, root):
        seen.append(_sha(LIVE_CONFTEST))
        return real_run(command, root)

    monkeypatch.setattr(harness, "_run", observing_run)
    mutation_test(tmp_path)

    # Positive control: the observer must actually have watched the inner runs,
    # or an empty `seen` would pass this test vacuously.
    assert len(seen) >= 2, seen
    assert all(s == original for s in seen), (
        "the live h-mad/tests/conftest.py was rewritten while an inner pytest ran; "
        f"sha before={original}, during={sorted(set(seen) - {original})}"
    )
    assert _sha(LIVE_CONFTEST) == original
