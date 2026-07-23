"""An unrecognised flag must fail loudly, not vanish.

Eleven arg loops ended in `*) shift ;;`, which silently discards anything the
verb does not recognise. Wave 4a declined it as pre-existing and out of scope,
with the note that if it changed, all eleven should change together.

The cost is a typo that reads as success. `worktree-rm <sel> --bse main` drops
the base and silently falls back to origin/HEAD, so the unmerged check runs
against the wrong ref -- which is exactly the J15/J17 failure family, reached by
a spelling mistake. `read agy --form-start` returns a 50-line tail while the
caller believes it asked for the whole buffer, which is J3. In every case the
operator gets a plausible answer to a question they did not ask.

Every one of these loops consumes its positional arguments BEFORE the loop
begins, so anything still present when the loop runs is meant to be a flag.
That is what makes erroring safe rather than a behaviour change for
positional-taking verbs.

Exit 2 is deliberate: `invariants.base.md` §"Audit-gate signal discipline"
reserves non-zero for operational errors, and a misspelled flag is exactly that
-- it is not a verdict about the world, it is a malformed request.
"""
import subprocess
import sys
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parent.parent
WRAPPER = SKILL / "scripts" / "hmad-dispatch.sh"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_hmad_dispatch import _bindir, run  # noqa: E402


# (argv, bad_flag, extra env). The bad flag is named rather than inferred from
# position -- some cases have no trailing value, and inferring argv[-2] made two
# of them assert against the wrong token.
CASES = [
    (["launch", "codex", "--worktre", "x"], "--worktre", {}),
    (["await", "task_1", "--timeut", "5"], "--timeut", {}),
    (["gate-wait", "gate_1", "--timeut", "5"], "--timeut", {}),
    (["worktree-create", "n", "--bse", "main"], "--bse", {}),
    (["worktree-ps", "--limt", "5"], "--limt", {}),
    (["worktree-rm", "sel", "--bse", "main"], "--bse", {}),
    (["file-diff", "a.py", "--rev"], "--rev", {}),
    (["file-open-changed", "--sinc", "HEAD"], "--sinc", {}),
    (["read", "agy", "--form-start"], "--form-start",
     {"HMAD_ORCA_AGY_TERMINAL": "t-a"}),
    (["wait", "agy", "--timeut", "5"], "--timeut",
     {"HMAD_ORCA_AGY_TERMINAL": "t-a"}),
]


@pytest.mark.parametrize("argv,bad,extra", CASES,
                         ids=[c[0][0] for c in CASES])
def test_unknown_flag_is_rejected(argv, bad, extra, tmp_path):
    b = _bindir(tmp_path, ["orca", "cmux"])
    env = {"_BINDIR": b, "HMAD_ORCA_PIN_FILE": str(tmp_path / "pins.env")}
    env.update(extra)
    r = run(argv, substrate="orca", env=env)
    assert r.returncode == 2, (
        f"{argv[0]} accepted the misspelled flag {bad!r} "
        f"(rc={r.returncode}); it was silently dropped"
    )
    assert "unknown option" in r.stderr.lower(), r.stderr
    # The message must name the offending token, or the operator re-reads --help
    # instead of their own command line.
    assert bad in r.stderr


def test_no_silent_flag_drop_remains_in_the_wrapper():
    # All eleven at once, per Wave 4a's "change all 11 as its own feature".
    src = WRAPPER.read_text(encoding="utf-8")
    assert "*) shift ;;" not in src, (
        "a silent flag-drop arm is back; unknown flags must fail loudly"
    )


def test_known_flags_still_work(tmp_path):
    # The guard must reject typos without rejecting the real thing.
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    r = run(["worktree-ps", "--limit", "5"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_PIN_FILE": str(tmp_path / "p.env")},
            capture=cap)
    assert r.returncode == 0, r.stderr
    assert "--limit 5" in cap.read_text()
