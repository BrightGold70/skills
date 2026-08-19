"""The zsh-pane viewport recipe carries three traps; the doc must keep naming them.

A pane is a cheap way to make a headless dispatch visible to a human (it renders in
Orca's UI process, so it costs the orchestrator no context). But three measured
facts break a naive version of it, and each fails toward a FALSE PASS or toward the
very blindness the recipe is meant to cure:

  1. a pane running `exec` bare shows nothing, because `exec` redirects the stream
     into `--log` -- the blindness relocated, not fixed;
  2. `orca terminal wait --for exit` reports exitCode 0 for a command that exited 9,
     so reading it as the dispatch rc turns every failure into a success;
  3. `wait --for exit` has no usable completion shape at all -- it either loses the
     scrollback or times out.

Docs decay by having their caveats trimmed as "noise" long before the code changes.
These tests make the caveats load-bearing. They assert the WARNING survives, not the
prose around it.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_MD = REPO_ROOT / "h-mad" / "SKILL.md"


def _section() -> str:
    """The section body, whitespace-normalised and bounded at a REAL heading.

    Two bugs this helper had, both of which made the guards useless in opposite
    directions, and both caught only because a passing assertion was checked
    against the text it had actually captured:

      * bounding only on "\\n### " found no next h3 and swallowed 200 lines of
        unrelated protocol -- every assertion below would then pass on prose from
        somewhere else entirely;
      * adding "\\n# " as a boundary matched a SHELL COMMENT inside this section's
        own fenced bash block, truncating the section before any of the warnings
        it exists to guard.

    So: track fences, and only accept a heading found outside one. Whitespace is
    normalised because markdown prose gets re-wrapped constantly and a test that
    fails on a moved line boundary gets deleted rather than fixed -- assert the
    CLAIM, not where the newlines fell.
    """
    text = SKILL_MD.read_text()
    marker = "### Making a dispatch visible in Orca (zsh shell pane)"
    assert marker in text, "the pane viewport section is gone"
    body = text.split(marker, 1)[1]

    kept, in_fence = [], False
    for line in body.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            kept.append(line)
            continue
        if not in_fence and line.startswith("#"):
            break
        kept.append(line)
    section = "\n".join(kept)
    # A section that ran away is not evidence about anything; fail loudly instead
    # of asserting against the rest of the document.
    assert len(section.splitlines()) < 120, "section boundary ran away"
    return " ".join(section.split())


class TestPaneIsAViewportNotATransport:
    def test_says_the_verdict_still_comes_from_the_file(self):
        s = _section()
        assert "--out" in s
        assert "never scrape the pane" in s.lower()

    def test_distinguishes_this_from_the_failed_pane_dispatch_path(self):
        """The reader has been burned by the pane path; if the doc does not say why
        a shell pane is different, the reasonable reaction is to refuse it."""
        s = _section()
        assert "identity" in s.lower()
        assert "9870" in s
        assert "viewport" in s.lower()


class TestTheThreeTraps:
    def test_warns_a_bare_exec_in_a_pane_is_blind(self):
        s = _section()
        assert "BLIND" in s or "blind" in s
        assert "--log" in s
        # the cure must be named, not just the hazard
        assert "tail" in s.lower() or "digest" in s.lower()

    def test_warns_terminal_wait_exit_code_is_not_the_dispatch_rc(self):
        """The single most dangerous fact here: it fails toward a false PASS."""
        s = _section()
        assert "exitCode" in s
        assert "exit 9" in s
        assert "every failure into a success" in s

    def test_names_the_rc_capture_that_actually_works(self):
        s = _section()
        assert "echo $? >" in s or "echo \\$? >" in s

    def test_warns_wait_for_exit_has_no_usable_completion_shape(self):
        s = _section()
        assert "times out" in s
        assert "scrollback" in s

    def test_points_at_report_wait_as_the_transport_agnostic_signal(self):
        s = _section()
        assert "report-wait" in s


class TestTailFStaysBannedForTheOrchestrator:
    def test_the_pane_is_marked_as_the_one_place_tail_f_is_allowed(self):
        """`tail -f` is banned for the orchestrator because it never returns. The
        pane is the exception, and an unqualified mention here would read as a
        reversal of that rule."""
        s = _section()
        assert "tail -f" in s
        assert "never an orchestrator" in s or "never an orchestrator tool call" in s


def test_context_cost_asymmetry_is_stated():
    """The reason to prefer a pane for a HUMAN audience is that it costs the
    orchestrator nothing; without that, the two channels look redundant and the
    expensive one gets used by default."""
    s = _section()
    assert "zero" in s.lower()
    assert "context" in s.lower()
