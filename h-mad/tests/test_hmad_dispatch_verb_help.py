"""`hmad-dispatch <verb> --help` must never run the verb.

Only `run` has a help arm. Every other verb received `--help` as an ordinary
argument, and the ones whose first positional is a free-form value then ACTED on
it, exiting 0:

    worktree-comment --help   ->  orca worktree set --worktree active --comment "--help"
    worktree-create  --help   ->  creates a worktree named "--help"
    automation-run   --help   ->  orca automations run "--help"
    gate-wait        --help   ->  polls a gate named "--help" for 600 s

The first one overwrites the active worktree's comment -- a person's note or a
handoff stamp -- with the literal string, which is the kind of quiet clobber the
handoff skill's worktree-comment rules exist to prevent. Asking a tool how to use
it must be the one invocation guaranteed to change nothing.

The guard sits in the dispatcher and reads only the FIRST argument, so
`run --timeout 5 -- cmd --help` still hands `--help` to the wrapped command.
"""
import re
import subprocess
import sys
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parent.parent
WRAPPER = SKILL / "scripts" / "hmad-dispatch.sh"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_hmad_dispatch import _isolated_env  # noqa: E402


def _verbs():
    src = WRAPPER.read_text(encoding="utf-8")
    m = re.search(r'^_HMAD_VERBS="(.+)"\s*$', src, re.M)
    assert m, "could not find the `_HMAD_VERBS=` verb list in the wrapper"
    return m.group(1).split()


def _dispatched_verbs():
    """The verbs `main()` actually routes, read from its case arms."""
    src = WRAPPER.read_text(encoding="utf-8")
    body = src[src.index("\nmain() {"):]
    body = body[:body.index("\n}\n")]
    return sorted(set(re.findall(r"^    ([a-z][a-z-]*)\)", body, re.M)))


def test_the_verb_list_matches_the_dispatcher():
    # The guard trusts the list to name every verb; a verb missing from it would
    # bypass the guard and take `--help` as its argument again.
    assert sorted(_verbs()) == _dispatched_verbs()
    assert len(_verbs()) > 30


def _tripwire_bin(tmp_path):
    """`orca`/`cmux` that record any call and fail, so an action is visible."""
    b = tmp_path / "bin"
    b.mkdir()
    for name in ("orca", "cmux"):
        p = b / name
        p.write_text(f'#!/bin/sh\necho "{name} $*" >> "{tmp_path}/calls"\nexit 1\n')
        p.chmod(0o755)
    return b


@pytest.mark.parametrize("flag", ["--help", "-h"])
@pytest.mark.parametrize("verb", _verbs())
def test_help_runs_nothing(verb, flag, tmp_path):
    b = _tripwire_bin(tmp_path)
    e = _isolated_env(substrate="orca", bindir=b,
                      env={"HMAD_ORCA_PIN_FILE": str(tmp_path / "pins.env")})
    r = subprocess.run(["bash", str(WRAPPER), verb, flag], capture_output=True,
                       text=True, env=e, cwd=tmp_path, timeout=30)
    calls = tmp_path / "calls"
    assert not calls.exists(), (
        f"`{verb} {flag}` reached the runtime:\n{calls.read_text()}")
    assert r.returncode == 0, (r.returncode, r.stdout, r.stderr)
    if verb == "run":
        assert "usage: hmad-dispatch run" in r.stdout, r.stdout
    else:
        assert "nothing was run" in r.stdout and verb in r.stdout, r.stdout


def test_help_after_the_first_argument_still_reaches_the_wrapped_command(tmp_path):
    e = _isolated_env(env={})
    r = subprocess.run(["bash", str(WRAPPER), "run", "--timeout", "5", "--",
                        "echo", "--help"], capture_output=True, text=True, env=e,
                       cwd=tmp_path, timeout=30)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "--help"


def test_an_unknown_verb_with_help_is_still_unknown(tmp_path):
    e = _isolated_env(env={})
    r = subprocess.run(["bash", str(WRAPPER), "no-such-verb", "--help"],
                       capture_output=True, text=True, env=e, cwd=tmp_path, timeout=30)
    assert r.returncode == 2
    assert "unknown verb 'no-such-verb'" in r.stderr
