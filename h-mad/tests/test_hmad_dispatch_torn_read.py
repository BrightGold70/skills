"""The wrapper must not mis-parse itself when a dispatch rewrites it mid-run (#3).

Bash reads a script incrementally by byte offset. Phase-5 tasks routinely rewrite
`hmad-dispatch.sh` while a dispatch through it is still running, so after the final
call returns bash seeks to its remembered offset in a file that has since grown and
parses whatever now lives there.

Measured on two real dispatches, both AFTER the child had already succeeded:

    codex exec rc=0
    line 3597: ame: command not found          <- tail of a split identifier
    line 3619: unexpected EOF while looking for matching `'

turning a good dispatch into a wrapper rc of 127 and 2. The reported line numbers
point at a blank line and a comment in the version measured, which is the signature
of a stale offset rather than a real syntax error — and is why this went unexplained
long enough to reach a backlog as "two wrapper bugs". It is one defect with two
symptoms.

There was no coverage for this. The suite's only torn-read handling is for torn LOG
LINES, an unrelated concern.
"""

import subprocess
import textwrap
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WRAPPER = REPO / "h-mad" / "scripts" / "hmad-dispatch.sh"


def test_the_wrapper_exits_on_the_same_line_as_its_final_call():
    """The guard itself, asserted structurally.

    `exit` must share the input line with the call: bash parses a whole line before
    executing it, so reaching `exit` there terminates the shell without another
    read. On its own line it would be a second read, at the stale offset, which is
    the bug.
    """
    last = WRAPPER.read_text().rstrip("\n").splitlines()[-1].strip()
    assert last == 'main "$@"; exit $?', (
        f"the wrapper's last line is {last!r}; a bare final call re-reads the file "
        "at a stale offset when a dispatch has rewritten it"
    )


def _run_rewritten_midflight(tmp_path: Path, tail: str) -> subprocess.CompletedProcess:
    """Run a wrapper-shaped script that grows while it is still executing."""
    script = tmp_path / "wrapper.sh"
    padding = "\n".join(
        f"# padding line {i} long enough to move the byte offset meaningfully"
        for i in range(200)
    )
    script.write_text(
        textwrap.dedent(
            f"""\
            #!/bin/bash
            main() {{
              printf 'child exec rc=0\\n'
              # a dispatch rewriting the wrapper it is running under
              cat "{tmp_path}/grown.sh" > "{script}"
              sleep 0.2
            }}
            {tail}
            """
        )
    )
    grown = tmp_path / "grown.sh"
    grown.write_text(script.read_text() + padding + "\nx='unterminated\n")
    return subprocess.run(
        ["bash", str(script)], capture_output=True, text=True, timeout=60
    )


def test_a_bare_final_call_reproduces_the_reported_torn_read(tmp_path):
    """The control. Without the guard the defect is real, not theoretical.

    Asserted so the guard below is known to be load-bearing: a fix whose control
    does not fail is a fix for nothing.
    """
    r = _run_rewritten_midflight(tmp_path, 'main "$@"')
    assert "child exec rc=0" in r.stdout, "the child must succeed in both arms"
    assert (
        "unexpected EOF" in r.stderr or "command not found" in r.stderr
    ), f"expected a torn read, got stderr={r.stderr!r}"


def test_exiting_on_the_call_line_survives_the_same_rewrite(tmp_path):
    r = _run_rewritten_midflight(tmp_path, 'main "$@"; exit $?')
    assert "child exec rc=0" in r.stdout
    assert "unexpected EOF" not in r.stderr, r.stderr
    assert "command not found" not in r.stderr, r.stderr
    assert r.returncode == 0, f"rc={r.returncode} stderr={r.stderr!r}"


def test_nothing_sources_the_wrapper_so_exit_cannot_kill_a_callers_shell():
    """The one way this guard could do harm, ruled out rather than assumed.

    `exit` in a sourced file terminates the SOURCING shell. Every caller execs the
    wrapper — `h-mad/bin/hmad-dispatch` uses `exec bash "$REAL" "$@"` — so there is
    no such caller. If one is ever added, this test is where it announces itself.
    """
    r = subprocess.run(
        ["grep", "-rnE", r"(^|\s)(source|\.)\s+\S*hmad-dispatch\.sh",
         str(REPO / "h-mad"), str(REPO / "docs")],
        capture_output=True, text=True,
    )
    # grep exits 1 on no match, which is the passing case.
    assert r.returncode == 1, f"something sources the wrapper:\n{r.stdout}"


# --- #22: an omitted --timeout must not mean an unbounded wait ----------------
# `exec agy` was twice observed still running for its full timeout AFTER agy had
# finished and written the report: the wrapper waits on the PID, never on the
# completion signal already on disk. Through `audit-cycle` the cost is capped
# because it always passes a --timeout; a hand-run `exec agy` had no cap at all.


def test_exec_defaults_its_timeout_to_a_ceiling():
    """The guard, asserted where a reader will find it.

    Not a live dispatch — that would cost an agent run. The contract is that the
    empty case is replaced before `secs` reaches the deadline branch.
    """
    src = WRAPPER.read_text()
    assert 'local wait_secs="${timeout:-3600}"' in src, (
        "an omitted --timeout must fall back to a ceiling; without it the deadline "
        "branch is skipped and the wrapper waits on the pid forever"
    )


def test_the_ceiling_is_above_every_timeout_the_skill_documents():
    """A ceiling that truncates real work is worse than none.

    The longest timeout documented anywhere in the skill is 1800, so the default
    must sit clear of it. If someone documents a longer dispatch, this fails and
    the ceiling gets raised deliberately rather than silently clipping a run.
    """
    import re
    docs = (REPO / "h-mad" / "SKILL.md").read_text()
    documented = [int(m) for m in re.findall(r"--timeout (\d{2,5})", docs)]
    assert documented, "no documented --timeout values found; the guard is unanchored"
    assert max(documented) < 3600, (
        f"the default ceiling 3600 is not clear of the longest documented timeout "
        f"{max(documented)}"
    )
