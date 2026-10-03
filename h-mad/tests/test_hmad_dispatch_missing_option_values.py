"""An option given without its value must print a message, not a shell internals error.

Third member of the malformed-request family, after `test_hmad_dispatch_unknown_flags.py`
(a flag the verb does not know) and `test_hmad_dispatch_missing_positionals.py` (a
required positional the caller omitted). Same root cause as the second -- `set -u` --
in a second location: an option arm that consumes a value,

    --limit) limit="$2"; shift 2 ;;

dies on `$2: unbound variable` when the option is the LAST token, so the operator
reads a line number inside the wrapper instead of learning which option lacked a
value:

    $ hmad-dispatch worktree-ps --limit
    hmad-dispatch.sh: line 1634: $2: unbound variable

The arms that already read `${2:-}` are not safe either. They survive the read and
then reach `shift 2` with only one argument left, which fails without shifting; under
`set -e` that aborts the wrapper with no message at all.

Exit 2 matches the two sibling files: `invariants.base.md` §"Audit-gate signal
discipline" reserves non-zero for operational errors, and an option with no value is a
malformed request, not a verdict about the world.
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

# One `case` arm on one line: `--opt) <body> ;;`. Arms here never span lines.
_ARM = re.compile(r"(?<![\w-])((?:-[\w-]+\|)*--?[\w-]+(?:\|-[\w-]+)*)\)\s*((?:(?!;;).)*?)\s*;;")


def _value_arms():
    """Every option arm that consumes a value: reads `$2` and shifts it away.

    Derived from the wrapper rather than listed, so an option added later with the
    same defect is caught without anyone remembering to extend this file.
    """
    arms = []
    for lineno, line in enumerate(WRAPPER.read_text(encoding="utf-8").splitlines(), 1):
        for m in _ARM.finditer(line):
            body = m.group(2)
            if re.search(r"\$\{?2\b", body) and "shift 2" in body:
                arms.append((lineno, m.group(1), body))
    return arms


def test_the_value_arm_list_was_found():
    # Guards the sweep's oracle: an empty list would make it pass vacuously.
    arms = _value_arms()
    assert len(arms) >= 60, len(arms)
    assert any(opt == "--limit" for _, opt, _ in arms)


@pytest.mark.parametrize("lineno,opt,body", _value_arms(),
                         ids=[f"{a[1]}@{a[0]}" for a in _value_arms()])
def test_every_value_arm_checks_its_value_is_present(lineno, opt, body):
    # Structural, because no single invocation reaches every arm: most sit behind
    # required positionals and a runtime the stub env does not provide. The
    # behavioural cases below prove the guard itself does the right thing.
    guard = body.find("_need_val ")
    read = re.search(r"\$\{?2\b", body)
    assert guard != -1 and guard < read.start(), (
        f"line {lineno}: `{opt}` reads $2 without `_need_val` first, so "
        f"`{opt}` as the last argument dies on an unbound variable:\n  {body}"
    )


def _run(argv, tmp_path, extra=None):
    b = _bindir(tmp_path, ["orca", "cmux"])
    env = {"_BINDIR": str(b), "HMAD_ORCA_PIN_FILE": str(tmp_path / "pins.env")}
    env.update(extra or {})
    e = _isolated_env(substrate="orca", env=env, bindir=b)
    return subprocess.run(["bash", str(WRAPPER), *argv], capture_output=True,
                          text=True, env=e, timeout=60)


_AGY = {"HMAD_ORCA_AGY_TERMINAL": "t-a"}

# (argv, the option left without a value, extra env). Includes `run --timeout`,
# whose arm already read `${2:-}` and failed at `shift 2` instead.
CASES = [
    (["worktree-ps", "--limit"], "--limit", {}),
    (["worktree-list", "--limit"], "--limit", {}),
    (["launch", "codex", "--worktree"], "--worktree", {}),
    (["await", "task_1", "--timeout"], "--timeout", {}),
    (["gate-wait", "gate_1", "--interval"], "--interval", {}),
    (["worktree-rm", "sel", "--base"], "--base", {}),
    (["file-diff", "a.py", "--worktree"], "--worktree", {}),
    (["file-open-changed", "--mode"], "--mode", {}),
    (["read", "agy", "--lines"], "--lines", _AGY),
    (["wait", "agy", "--timeout"], "--timeout", _AGY),
    (["run", "--timeout"], "--timeout", {}),
]


@pytest.mark.parametrize("argv,opt,extra", CASES, ids=[" ".join(c[0]) for c in CASES])
def test_missing_option_value_is_reported(argv, opt, extra, tmp_path):
    r = _run(argv, tmp_path, extra)
    combined = r.stdout + r.stderr
    assert "unbound variable" not in combined, (
        f"`{' '.join(argv)}` died on a shell internals error:\n{combined}"
    )
    assert r.returncode == 2, (
        f"`{' '.join(argv)}` should exit 2 for a malformed request, "
        f"got {r.returncode}:\n{combined}"
    )
    # The message alone must say which option lacked a value.
    assert opt in r.stderr and "requires a value" in r.stderr, r.stderr
