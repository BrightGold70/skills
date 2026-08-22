"""Protect real session state from the test suite.

Every test isolates its pin file by passing `HMAD_ORCA_PIN_FILE`. That isolation
is honoured by ONE branch in `_pin_file`, and J2 made the fallback resolve to the
enclosing repository rather than the cwd — so if that branch ever stops working,
writes land on the developer's live `<repo>/.h-mad/orca-pins.env` instead of a
temp path.

That is not hypothetical. Mutation-testing `_pin_file`'s override branch (the
practice `invariants.base.md` §"Test discrimination" mandates) deleted exactly
that branch and redirected the whole suite's pin writes onto the real file,
replacing two live agent handles with `term_live`/`term_explicit`. The suite
reported 642 passed while doing it: from the tests' point of view nothing was
wrong, because they never assert where the file is NOT.

So the protection belongs here rather than in any single test — snapshot the real
file before the session and restore it after if anything moved it, loudly.
"""
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _live_pin_file() -> Path:
    """The same path `_pin_file` resolves to for an unset override, from here."""
    try:
        root = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, OSError):
        return REPO_ROOT / ".h-mad" / "orca-pins.env"
    return Path(root) / ".h-mad" / "orca-pins.env"


@pytest.fixture(scope="session", autouse=True)
def _protect_live_pin_file():
    target = _live_pin_file()
    before = target.read_bytes() if target.is_file() else None
    yield
    after = target.read_bytes() if target.is_file() else None
    # J18 pin-file guard mutation anchor. Distinct from the wire-registry anchor
    # below because `if after == before:` appears once per guard, and the mutation
    # harness refuses any anchor it cannot match exactly once.
    if after == before:
        return
    # Restore first, complain second: a developer's live agent handles matter
    # more than the tidiness of this message.
    if before is None:
        try:
            target.unlink()
        except FileNotFoundError:
            pass
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(before)
    pytest.fail(
        f"the test suite modified the live pin file {target} and it has been "
        "restored. Some test is not isolating HMAD_ORCA_PIN_FILE, or a mutation "
        "disabled the override branch in _pin_file. Re-run `hmad-dispatch env` "
        "to confirm your agent handles.",
        pytrace=False,
    )


def _live_wire_registry_file() -> Path:
    """The repository's real wire registry, independent of the test cwd."""
    try:
        root = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, OSError):
        return REPO_ROOT / ".h-mad" / "wires.jsonl"
    return Path(root) / ".h-mad" / "wires.jsonl"


@pytest.fixture(scope="session", autouse=True)
def _protect_live_wire_registry():
    target = _live_wire_registry_file()
    before = target.read_bytes() if target.is_file() else None
    yield
    after = target.read_bytes() if target.is_file() else None
    # J18 guard mutation anchor.
    if after == before:
        return
    if before is None:
        try:
            target.unlink()
        except FileNotFoundError:
            pass
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(before)
    pytest.fail(
        f"the test suite modified the live wire registry {target} and it has been "
        "restored. Some test is not isolating its registry path, or a mutation "
        "disabled the path-redirection branch in the wire registry writer.",
        pytrace=False,
    )
