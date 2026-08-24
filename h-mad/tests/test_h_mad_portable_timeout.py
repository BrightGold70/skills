"""`timeout` does not exist on macOS, and the reflex after 127 is worse than the 127.

Measured in a live session: an agent reached for `timeout <n> <cmd>`, got
`command not found`, narrated "timeout isn't on macOS. Checking auth directly",
and re-ran the same command **unbounded**. That is a silent downgrade, not a
fallback -- an unbounded probe does not fail at the deadline, it hangs, and in
every log h-mad reads (a `--log` tail, `progress`, a transcript) a hang and slow
work are the same bytes.

h-mad had owned a portable watchdog since `exec` shipped (`_exec_run`: absolute
deadline off bash's SECONDS, TERM -> grace -> KILL, signalled to the whole
process group because macOS ships no `setsid`), but it was private -- five
internal call sites and no verb. So nothing an agent or a prompt could call
existed, which is why the improvisation happened at all. `run` exposes it.

These tests pin the contract the callers depend on: the GNU exit-124 convention
(so a caller already branching on 124 needs no change), the child's own exit
code otherwise, inherited stdio, process-group death for grandchildren, and the
rule text in the four documents that reach the two surfaces which can improvise
-- the orchestrator (SKILL.md, agent-substrate.md) and a dispatched agent
(codex-implementer-prompt.md, invariants.base.md).
"""
import os
import re
import subprocess
import time
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parent.parent
WRAPPER = SKILL / "scripts" / "hmad-dispatch.sh"


def _run(argv, *, stdin=None, timeout=60):
    env = dict(os.environ)
    env.pop("HMAD_SUBSTRATE", None)
    return subprocess.run(
        [str(WRAPPER), *argv],
        input=stdin, capture_output=True, text=True, env=env, timeout=timeout,
    )


# --------------------------------------------------------------------------
# Exit-code contract
# --------------------------------------------------------------------------

def test_zero_exit_and_stdout_pass_through():
    r = _run(["run", "--timeout", "10", "--", "echo", "hello"])
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "hello"


def test_nonzero_child_exit_is_the_verbs_exit():
    # Not collapsed to 0/1: a caller distinguishes "the command failed" from
    # "the command timed out", and only the child's own code carries the first.
    r = _run(["run", "--timeout", "10", "--", "sh", "-c", "exit 3"])
    assert r.returncode == 3, (r.returncode, r.stderr)


def test_deadline_exits_124_and_actually_bounds_the_wall_clock():
    t0 = time.monotonic()
    r = _run(["run", "--timeout", "2", "--", "sleep", "60"])
    elapsed = time.monotonic() - t0
    assert r.returncode == 124, (r.returncode, r.stderr)
    # The bound is the point. A generous ceiling still fails a watchdog that
    # counts completed sleeps instead of reading an absolute deadline.
    assert elapsed < 15, f"did not bound the command: {elapsed:.1f}s"


def test_timeout_names_the_command_on_stderr():
    # GNU `timeout` is silent here. h-mad's callers read logs, and a bare 124 in
    # a transcript loses which command owned it.
    r = _run(["run", "--timeout", "2", "--", "sleep", "60"])
    assert "run_timeout" in r.stderr, r.stderr
    assert "sleep" in r.stderr, r.stderr


def test_stdin_reaches_the_child():
    # `_exec_run` backgrounds the child; bash redirects a backgrounded command's
    # stdin from /dev/null unless it is handed over explicitly. That exact bug
    # once starved `codex exec -` of its piped prompt.
    r = _run(["run", "--timeout", "10", "--", "cat"], stdin="piped\n")
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "piped"


# --------------------------------------------------------------------------
# Process-group death -- the reason a bare `kill $pid` is not enough
# --------------------------------------------------------------------------

def test_forked_grandchild_dies_with_the_deadline():
    marker = "hmad_portable_timeout_probe_%d" % os.getpid()
    r = _run(["run", "--timeout", "2", "--", "sh", "-c",
              f"sleep 90 & echo {marker} >&2; wait"])
    assert r.returncode == 124, (r.returncode, r.stderr)
    time.sleep(1.0)
    # The grandchild is a bare `sleep 90` with no distinguishing argv, so match
    # on the process tree instead: nothing may remain in the killed group.
    ps = subprocess.run(["pgrep", "-f", "sleep 90"], capture_output=True, text=True)
    survivors = [p for p in ps.stdout.split() if p]
    for pid in survivors:
        # Another test run (or an unrelated process) may legitimately own one.
        # Only a child of THIS wrapper invocation would be orphaned to init.
        st = subprocess.run(["ps", "-o", "ppid=", "-p", pid],
                            capture_output=True, text=True)
        assert st.stdout.strip() != "1", (
            f"sleep 90 (pid {pid}) was orphaned to init: the watchdog killed the "
            "direct child only, not the process group"
        )


# --------------------------------------------------------------------------
# Malformed requests fail loudly (invariants.base.md §Audit-gate signal discipline)
# --------------------------------------------------------------------------

@pytest.mark.parametrize("argv,why", [
    (["run", "--timeut", "2", "--", "true"], "misspelled flag"),
    (["run", "--", "true"], "no --timeout"),
    (["run", "--timeout", "abc", "--", "true"], "non-numeric --timeout"),
    (["run", "--timeout", "0", "--", "true"], "zero --timeout"),
    (["run", "--timeout", "2", "--"], "no command"),
])
def test_malformed_request_exits_2_and_runs_nothing(argv, why):
    r = _run(argv)
    assert r.returncode == 2, (why, r.returncode, r.stdout, r.stderr)
    assert r.stdout.strip() == "", (why, r.stdout)


def test_run_is_a_registered_verb():
    r = _run(["run"])
    assert "unknown verb" not in r.stderr, r.stderr


# --------------------------------------------------------------------------
# The rule, on both surfaces that can improvise
# --------------------------------------------------------------------------

# A `timeout <n> <cmd>` COMMAND form. `--timeout 900`, `--wait-timeout`, and
# `--print-timeout` are flags on h-mad's own verbs and are deliberately excluded
# by the leading-`-` guard.
_TIMEOUT_CMD = re.compile(r"(?:^|[^-\w])timeout\s+\d+")

_SCANNED = [
    SKILL / "SKILL.md",
    SKILL / "invariants.base.md",
    SKILL / "invariants.example.md",
    SKILL / "audit-prompt.template.md",
    *sorted((SKILL / "references").glob("*.md")),
    *sorted((SKILL / "scripts").glob("*.sh")),
    *sorted((SKILL / "scripts").glob("*.py")),
    *sorted((SKILL / "hooks").glob("*.sh")),
]


@pytest.mark.parametrize("path", _SCANNED, ids=lambda p: p.name)
def test_no_document_or_script_emits_a_bare_timeout_command(path):
    offenders = [
        f"{path.name}:{i}: {line.strip()}"
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if _TIMEOUT_CMD.search(line) and "run --timeout" not in line
    ]
    assert not offenders, (
        "a `timeout <n> <cmd>` form is present; macOS has no `timeout`, so this "
        "fails at 127 and invites an unbounded retry. Use "
        "`hmad-dispatch run --timeout <s> -- <cmd...>`:\n" + "\n".join(offenders)
    )


@pytest.mark.parametrize("relpath", [
    "SKILL.md",                                # orchestrator: NEVER list
    "references/agent-substrate.md",           # orchestrator: verb table
    "references/codex-implementer-prompt.md",  # dispatched implementer
    "invariants.base.md",                      # dispatched auditor (spliced in)
])
def test_the_rule_reaches_every_surface_that_can_improvise(relpath):
    body = (SKILL / relpath).read_text(encoding="utf-8")
    assert "run --timeout" in body, (
        f"{relpath} does not name the replacement command; a prohibition with no "
        "replacement is what produced the unbounded fallback in the first place"
    )
    assert "gtimeout" in body, (
        f"{relpath} does not rule out `gtimeout`; it is the obvious second guess "
        "and is equally absent from a stock macOS"
    )
