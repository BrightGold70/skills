"""A missing required argument must print usage, not a shell internals error.

Sibling defect to `test_hmad_dispatch_unknown_flags.py`. That file's own reasoning
names the gap: "Every one of these loops consumes its positional arguments BEFORE
the loop begins, so anything still present when the loop runs is meant to be a
flag." The loops therefore reject a misspelled FLAG correctly -- but an ABSENT
POSITIONAL never reaches the loop. Under `set -u` the function dies on its first
line instead:

    $ hmad-dispatch send
    hmad-dispatch.sh: line 2136: $1: unbound variable
    $ hmad-dispatch send --help
    hmad-dispatch.sh: line 2136: $2: unbound variable

Both reproduce the same bug; `--help` is not special, it just lands in `$1` and
leaves `$2` unset. This was first reported as "`send --help` crashes", which is
the symptom that happens to be typed most often, not the class.

`run --help` already had this exact defect and was fixed for `run` alone (#143,
`-h|--help) _cmd_run_usage`). Fixing one verb's spelling of it left the other
arity errors reporting a line number inside the wrapper -- the operator reads
`$2: unbound variable` and has no way to learn they omitted an argument.

Exit 2 matches `unknown_flags`: `invariants.base.md` §"Audit-gate signal
discipline" reserves non-zero for operational errors, and an incomplete command
line is a malformed request, not a verdict about the world.
"""
import re
import subprocess
import sys
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parent.parent
WRAPPER = SKILL / "scripts" / "hmad-dispatch.sh"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_hmad_dispatch import _bindir, _isolated_env  # noqa: E402


def _run(argv, tmp_path, extra=None):
    """Like test_hmad_dispatch.run, but with a timeout.

    A verb that waits (`wait`, `await`, `gate-wait`) must not hang the suite if a
    future edit makes it reach its poll loop with no argument.
    """
    b = _bindir(tmp_path, ["orca", "cmux"])
    env = {"_BINDIR": str(b), "HMAD_ORCA_PIN_FILE": str(tmp_path / "pins.env")}
    env.update(extra or {})
    e = _isolated_env(substrate="orca", env=env, bindir=b)
    return subprocess.run(["bash", str(WRAPPER), *argv], capture_output=True,
                          text=True, env=e, timeout=60)


# (argv, the verb) -- each omits a REQUIRED positional the verb reads unguarded.
# Both the zero-arg and the partial form are listed where the verb takes two,
# because they fail on different parameters ($1 vs $2) and a guard that only
# defaults the first still crashes on the second.
CASES = [
    (["send"], "send"),
    (["send", "codex"], "send"),
    # `send --help` used to land here by accident. `--help` is now answered by the
    # dispatcher before any verb runs: test_hmad_dispatch_verb_help.py.
    (["clear"], "clear"),
    (["interrupt"], "interrupt"),
    (["wait"], "wait"),
    (["alive"], "alive"),
    (["notify"], "notify"),
    (["notify", "a-title"], "notify"),
]


@pytest.mark.parametrize("argv,verb", CASES, ids=[" ".join(c[0]) for c in CASES])
def test_missing_positional_reports_usage(argv, verb, tmp_path):
    r = _run(argv, tmp_path)
    combined = r.stdout + r.stderr
    assert "unbound variable" not in combined, (
        f"`{' '.join(argv)}` died on a shell internals error instead of "
        f"reporting the missing argument:\n{combined}"
    )
    assert r.returncode == 2, (
        f"`{' '.join(argv)}` should exit 2 for a malformed request, "
        f"got {r.returncode}:\n{combined}"
    )
    # The operator must be able to learn what they omitted from the message
    # alone, without opening the wrapper at the reported line number.
    assert "usage" in combined.lower(), combined
    assert verb in combined, combined


def _verbs():
    """The verb list, read from the wrapper's own `_HMAD_VERBS` (what its help prints).

    Derived rather than hardcoded so a NEW verb with this defect is caught by
    the sweep below without anyone remembering to extend this file.
    """
    src = WRAPPER.read_text(encoding="utf-8")
    m = re.search(r'^_HMAD_VERBS="(.+)"\s*$', src, re.M)
    assert m, "could not find the `_HMAD_VERBS=` verb list in the wrapper"
    return m.group(1).split()


def test_the_verb_list_was_found():
    # Guards the sweep's oracle: an empty list would make it pass vacuously.
    v = _verbs()
    assert len(v) > 20, v
    assert "send" in v and "notify" in v


@pytest.mark.parametrize("verb", _verbs())
def test_no_verb_dies_on_an_unbound_variable(verb, tmp_path):
    """Class-wide sweep: no verb may report a shell internals error.

    Safe to invoke every verb because `_isolated_env` puts only stub `orca`/`cmux`
    on PATH -- nothing here reaches a real runtime, a real pane, or a real
    worktree. Asserts ONLY the absence of the crash: a verb that legitimately
    succeeds with no arguments (`env`, `worktree-ps`) is equally acceptable.
    """
    r = _run([verb], tmp_path)
    combined = r.stdout + r.stderr
    assert "unbound variable" not in combined, (
        f"`hmad-dispatch {verb}` with no arguments died on a shell internals "
        f"error; it must report usage instead:\n{combined}"
    )
