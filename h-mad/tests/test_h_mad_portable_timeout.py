"""`timeout` is not a macOS system component, and the reflex after 127 is worse than the 127.

NOTE (2026-08-25, found on a resume): this box now HAS both, from a deliberate
`brew install coreutils` (9.11, `installed_on_request: true`). That does not
soften the rule, it sharpens it. The form is unportable in *both* directions:
absent, it is a 127 followed by an unbounded retry; present, it silently works
and the improvisation silently succeeds -- with the loud 127 that used to expose
it now gone, and the bound resting on a CLI h-mad cannot assume any box has. So the
rule text may not rest on an absence claim any reader can refute in one
`command -v`; see `test_no_surface_rests_on_an_unconditional_absence_claim`.

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
        "a `timeout <n> <cmd>` form is present; `timeout` is not a macOS system "
        "component, so this either fails at 127 and invites an unbounded retry or "
        "silently binds the artifact to a separately-installed CLI. Use "
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


# A rule whose stated reason a reader can refute in one command is a rule a
# reader will discount. Each of these was the live text until 2026-08-25, when
# coreutils turned every one of them into a locally false claim; `stock macOS
# ships neither` stays legal because it is true on both kinds of box.
# An unconditional "it isn't there" claim. Enumerating English is leaky by
# nature, so the enumeration is PINNED by test_absence_detector_behaviour below:
# every phrasing an audit has actually produced is a row in that table, and a
# future editor who narrows this regex fails there rather than silently letting
# the claim back in.
# `_W` swallows one optional intervening word -- an adverb (`natively ships`) or
# a noun (`the timeout command doesn't exist`). Audit pass C slipped both past a
# strictly-adjacent version of this list.
_W = r"(?:\w+ ){0,1}"
_ABSENCE_CLAIMS = [
    rf"macos {_W}(?:ships|has|have|carries|includes|comes with) (?:neither|no g?timeout)",
    rf"macos {_W}(?:does not|doesn't) (?:ship|have|carry|include|come with) (?:a |the )?g?timeout",
    rf"neither {_W}(?:exists|is available|is present|is installed|ships) on macos",
    rf"g?timeout {_W}(?:does not|doesn't) exist on macos",
    rf"g?timeout {_W}(?:isn't|is not) (?:on |available on |present on |installed on )macos",
    rf"g?timeout {_W}is (?:absent|missing) from macos",
    r"no g?timeout on macos",
]
_UNCONDITIONAL_ABSENCE = re.compile("|".join(_ABSENCE_CLAIMS), re.IGNORECASE)

# Only this word, standing immediately before the claim, qualifies it. `stock
# macOS ships neither` is true on a bare box AND on this one, so it stays legal.
_QUALIFIER = "stock"


def _normalize(text):
    """Collapse whitespace and strip Markdown emphasis/code punctuation.

    Two separate reasons, both measured against earlier drafts of this guard:

    * Line-scoped scanning made paragraph REFLOW decide whether the guard fires
      -- the first draft false-fired on its own author's `stock \n macOS ships
      neither`, and rewrapping the prose would have hidden the symptom while
      leaving the guard wrong.
    * Markdown made EMPHASIS decide it -- `**stock** macOS ships neither` is the
      legal hedge, but the raw bytes put `**` between qualifier and claim.
    """
    return " ".join(text.replace("*", "").replace("_", "").replace("`", "").split())


def _absence_offenders(text):
    """Offending absence claims in `text`, each with surrounding context.

    The qualifier must ADJOIN the claim as a whole word. A proximity window was
    tried first and let `macOS ships neither` through because an unrelated
    `system component` sat 40 characters upstream -- i.e. it accepted the exact
    text this guard exists to reject. A bare `(?<!stock )` lookbehind failed the
    other way: `non-stock macOS ships neither` ends in `stock ` and so satisfied
    it, silently licensing a claim that is explicitly false.
    """
    flat = _normalize(text)
    out = []
    for m in _UNCONDITIONAL_ABSENCE.finditer(flat):
        preceding = flat[:m.start()].split()
        prev = preceding[-1].lower().strip(".,;:()[]—-") if preceding else ""
        if prev == _QUALIFIER:
            continue
        out.append("…" + flat[max(0, m.start() - 80):min(len(flat), m.end() + 40)] + "…")
    return out


# Rows marked `True` are claims this box refutes with one `command -v timeout`.
# Every one of them was produced by a real audit pass or an earlier draft.
@pytest.mark.parametrize("text,flagged,why", [
    ("macOS ships neither and the call fails at 127", True, "bare unhedged claim"),
    ("stock macOS ships neither", False, "the one legal hedge"),
    ("**stock** macOS ships neither", False, "hedge behind Markdown emphasis"),
    ("stock\n  macOS ships neither", False, "hedge split by a line wrap"),
    ("non-stock macOS ships neither", True, "negated prefix must not qualify"),
    ("timeout isn't on macOS", True, "the narration from the original incident"),
    ("macOS doesn't ship timeout", True, "contraction + alternate verb"),
    ("macOS does not have timeout", True, "alternate verb"),
    ("`timeout` is absent from macOS", True, "absence stated without a verb of shipping"),
    ("neither exists on macOS", True, "the original SKILL.md phrasing"),
    ("`gtimeout` is not available on macOS", True, "gtimeout, the obvious second guess"),
    ("macOS has no `setsid`", False, "a DIFFERENT and still-true claim: do not over-match"),
    ("neither is a macOS system component", False, "the correct portability framing"),
    # Audit pass C: an intervening word defeated a strictly-adjacent match.
    ("macOS natively ships neither", True, "adverb between subject and verb"),
    ("The timeout command doesn't exist on macOS", True, "noun between subject and verb"),
    ("macOS comes with neither", True, "alternate verb phrase"),
    ("timeout is not installed on macOS", True, "installed-on phrasing"),
    ("On stock, macOS ships neither.", False, "qualifier separated by punctuation"),
    ("What this box has is not an input to this rule", False,
     "the replacement framing must not trip its own guard"),
    # Audit pass D: not every "macOS … has no timeout" is about the CLI.
    ("the macOS network stack has no timeout", False,
     "a noun phrase about something else must not be read as the CLI claim"),
])
def test_absence_detector_behaviour(text, flagged, why):
    assert bool(_absence_offenders(text)) is flagged, why


@pytest.mark.parametrize("path", _SCANNED, ids=lambda p: p.name)
def test_no_document_or_script_rests_on_an_unconditional_absence_claim(path):
    offenders = _absence_offenders(path.read_text(encoding="utf-8"))
    assert not offenders, (
        f"{path.name} justifies the rule with an absence claim that one "
        "`command -v timeout` refutes on any box carrying coreutils -- and a "
        "reason a reader can refute is a rule a reader discounts. Ground it on "
        "portability (`not a macOS system component`) instead:\n"
        + "\n".join(offenders)
    )


# Why the form stays forbidden on a box that HAS coreutils. Any one of these
# carries it. The reason must be UNCONDITIONAL -- either "what your box has does
# not exempt you" or "this is a dependency" -- never a conditional downstream
# failure. "It dies at 127 on the next box" is disqualified twice over: false on
# Linux, which ships coreutils, and an open invitation to reason "there is no
# next box here, so the rule does not apply to me".
# Deliberately NOT "external cli dependency": that clause is routinely written
# conditionally ("for anything committed or dispatched it is a dependency"), and
# a conditional reason is the exact loophole this guard exists to close -- an
# agent reasons "mine is neither committed nor dispatched". Only a phrasing that
# denies the exemption outright counts. Verified by mutation: with the softer
# token in the set, deleting the unconditional sentence from SKILL.md still
# passed.
_DEPENDENCY_HAZARD = ("not an input to", "not licence")


_CONDITIONAL_OPENERS = ("if ", "when ", "unless ", "should you ", "in the event")


def _conditionally_hedged(window):
    """True if every hazard token in `window` sits in a conditional sentence.

    The token set says "your box does not exempt you". Wrapping that in `If the
    script is committed, …` hands the exemption straight back, while still
    matching the substring -- so the substring alone cannot be the whole check.
    """
    low = window.lower()
    found = False
    for tok in _DEPENDENCY_HAZARD:
        start = 0
        while (i := low.find(tok, start)) >= 0:
            found = True
            head = low.rfind(".", 0, i)
            sentence = low[head + 1:i].strip()
            if not sentence.startswith(_CONDITIONAL_OPENERS):
                return False        # at least one unconditional statement
            start = i + 1
    return found


def _rule_windows(text, span=650):
    """Every `gtimeout` mention and the text FOLLOWING it, normalized.

    Forward-only, and deliberately tight: a symmetric 1800-char window passed on
    `invariants.base.md` by reaching BACKWARDS into the neighbouring section
    §"No new external dependency", whose own prose contains the token -- the same
    tautology, one notch narrower. Measured span from prohibition to justification
    across the four surfaces: 240-491 characters.

    ALL occurrences, not the first. Anchoring on `find()` meant one earlier
    unrelated mention -- a changelog line, an intro paragraph -- would silently
    move the window off the rule and pass the file on text that is not the rule.
    """
    flat = _normalize(text)
    low = flat.lower()
    out, i = [], low.find("gtimeout")
    while i >= 0:
        out.append(flat[i:i + span])
        i = low.find("gtimeout", i + 1)
    return out


@pytest.mark.parametrize("relpath", [
    "SKILL.md",
    "references/agent-substrate.md",
    "references/codex-implementer-prompt.md",
    "invariants.base.md",
])
def test_every_rule_surface_keeps_the_halt(relpath):
    """`halt` is the whole rule; without it the prohibition has no safe exit.

    The measured incident was not the 127 -- it was what came after: the same
    command re-run UNBOUNDED, which turns a deadline into a hang that no log can
    tell from slow work. `halt` is the instruction that forecloses it.

    Guarded because an audit pass actually proposed DELETING it, reasoning that
    a universally-available verb makes "if no time-bounder is reachable" dead
    text. It is not dead: the verb is reachable wherever `hmad-dispatch` is, and
    a sandboxed or PATH-less agent is exactly the case that produced the
    original unbounded retry.
    """
    # 1100, not the 650 the sibling checks use: SKILL.md states the rule as one
    # long bullet and its halt clause sits 953 characters past the prohibition.
    # Measured across the four surfaces: 384 / 558 / 582 / 953.
    window = " ".join(_rule_windows(
        (SKILL / relpath).read_text(encoding="utf-8"), span=1100))
    assert "halt" in window.lower(), (
        f"{relpath} prohibits the form without saying what to do when no "
        "time-bounder is reachable. That gap is the original defect: the reflex "
        "is to re-run the command unbounded and narrate it as checking directly"
    )


@pytest.mark.parametrize("relpath", [
    "SKILL.md",
    "references/agent-substrate.md",
    "references/codex-implementer-prompt.md",
    "invariants.base.md",
])
def test_every_rule_surface_accounts_for_the_coreutils_present_case(relpath):
    """The rule must state the present-box hazard WHERE THE RULE IS.

    Scoped to the rule's own paragraph, not the whole file. A bare
    `"coreutils" in body` passes on a 1400-line document that mentions the word
    anywhere -- including in a sentence asserting macOS does not have it, which
    is the very claim the sibling guard exists to reject.
    """
    windows = _rule_windows((SKILL / relpath).read_text(encoding="utf-8"))
    assert windows, f"{relpath}: no `gtimeout` prohibition found to scope the check to"
    window = next(
        (w for w in windows
         if "coreutils" in w.lower()
         and any(t in w.lower() for t in _DEPENDENCY_HAZARD)),
        windows[0],
    )
    assert "coreutils" in window.lower(), (
        f"{relpath} states the prohibition without naming the box where `timeout` "
        "IS present. There the call succeeds, so the loud 127 that exposed the "
        "improvisation never fires -- the case a rule written only against a "
        "stock box misses entirely"
    )
    assert not _conditionally_hedged(window), (
        f"{relpath} states the reason CONDITIONALLY (\"if committed…\", \"when "
        "dispatched…\"). That is the loophole, not the fix: an agent whose case "
        "falls outside the condition reads itself as exempt. State it flat"
    )
    assert any(t in window.lower() for t in _DEPENDENCY_HAZARD), (
        f"{relpath} names the coreutils case but not why it is still forbidden "
        f"there. Say it in the rule itself (one of {_DEPENDENCY_HAZARD}): writing "
        "the command incurs a dependency on a separately-installed CLI at the "
        "moment it is written. Without that, an agent whose box happens to have "
        "coreutils reads the rule as inapplicable to it"
    )
