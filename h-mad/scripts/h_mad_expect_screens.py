#!/usr/bin/env python3
"""Run every published `# expect <N>` screen AT a freeze sha before certifying it.

    h_mad_expect_screens.py <doc.md> [<doc.md>...] --at <sha> --project-root ROOT [--timeout S]

Three decision-sheet entries certified that a tooling commit moved no scoped
census while the design's own published trip-wire (`... | grep -vc '^docs/'
# expect 0`) read 8 at that commit; nobody ran it (#49w,
`measurement-discipline.md` §FREEZE). The documents publish these screens with
their commands, so certifying a freeze can execute them instead of trusting them.

What a screen is. A statement inside a fenced `bash` or `sh` block whose last
line ends with a `# expect <N>` comment, N an integer. The comment is found by a
quote-aware scan (`'…'`, `"…"`, `$'…'`; a `#` after a blank or `;&|()<>`), so
`echo "a # expect 0"` is not one. The integer may be
followed by end of line or by an annotation after `,` `;` `(` `--` or an em
dash (`# expect 0 (VACUOUS while BASE==HEAD)` is a screen); an integer followed
by a word (`# expect 4 methods x 2`) is not, because the expectation is not the
bare integer. A statement spans lines the way bash joins them: a line ending in
an unquoted `\\`; a line whose code (comment stripped) ends in `|` or `&&`,
across any blank or comment-only lines after it; a quoted string that
runs onto the next line; and a here-document (a `<<` in unquoted code outside
`((…))` arithmetic), whose body and terminator belong to the line that opened
it. A leading `|` with no backslash above it is a bash syntax error, so it is
not joined: the block dies there and the screen reads UNREADABLE. Fail closed
against the lexer itself: every line carrying `# expect <N>` that it did not
accept as a screen -- inside a quoted string or a heredoc body, or behind a
misread quote -- is reported `UNREADABLE:unparsed`, never dropped; only a
comment-only line the lexer read as one is left out. Fences come from the
repo's ONE scanner, `h_mad_doc_block_exec._fence_events`; blocks with no screen
are never run.

Coverage, said once and printed every run: ONLY comment-tagged screens are
covered. An expectation stated in prose beside a command (`# the freeze: prints
8`, "It returns `0`") is not a screen and is not run.

Where things are read and where they run. Each document is read from the
WORKING TREE as given -- the document publishes the screens -- and every screen
is evaluated AT the sha, in a throwaway detached worktree of ROOT's repository
(`git worktree add --detach`, hooks off). The worktree is removed on return, on
an exception, and on SIGTERM/SIGHUP (which also kill the running block's process
group); only this run's own worktree entry is ever deleted, never by a
repo-wide prune. `GIT_DIR` and the other repository-redirecting `GIT_*`
variables are dropped first, so neither `git` here nor a screen reads another
repository. Blocks read stdin from /dev/null and run under /bin/bash (`BASH`, pinned in
`h_mad_doc_block_exec`), never PATH's first `bash`; the `bash -n` oracle asks the same one. When ROOT is a subdirectory of its
repository, screens run in the same subdirectory of the worktree. Residual: a
statement that leaves the worktree by absolute path (`cd /abs`, `git -C /abs`)
reads that tree, not the sha.

How a reading is taken. Each qualifying block runs ONCE (non-strict bash, so a
grep that matches nothing does not end the block), via `run_block`, with marker
lines inserted around each screen so its stdout is captured alone and every
earlier line still runs to define variables. Every block runs under
`set -o pipefail`, so an errored non-final member fails its pipeline
(`git diff nosuchref | cat > f` exits 128, not 0), and an ERR trap with `set -E`
(errtrace: it also fires in function bodies, subshells and command
substitutions, writing to one file), disarmed inside screens, records every
command before a screen that bash reports to it: a simple command, pipeline,
assignment or function call that exits non-zero. No status is judged benign
from command text. bash runs NO ERR trap for a non-final member of an `&&`/`||`
list, for a background `&` job, or for an `if`/`while`/`until` condition or a
`!`-negated command. The first two cannot be recorded, so they are REFUSED: a
block with an `&&`, an `||` or a `&` at or before a screen -- at top level, in a
`{ }` group, a `( )` subshell, a function body, or a `$(…)`/backtick -- makes
that screen `UNREADABLE:unsupported_construct=<&&|"||"|&>@<doc>:<line>`, never
PASS. Every `||` is refused -- there is no declared form. Each lexical exception
tried had a hole: `|| true`/`|| :` mask every status; `|| exit 0`/`|| return 0`
end with 0 over a failure (review round 6); a list inside an `if`/`while`
condition leaked past `if (true) then` (round 6); an unbraced `… | grep P ||
[ $? = 1 ]` binds to the whole pipeline and swallows git's 128 (round 7); and
even the braced `git … | { grep P || [ $? = 1 ]; } > f` read PASS, because bash
3.2 runs no ERR trap for a pipeline that ends in such a group (round 8). Nor
is an `&&`/`||` inside `[[ ]]` or `(( ))` exempt: keyed on text, `echo [[ ; …`
and `((cmd) && …)` switched list detection off (round 9, E1/E2), so the
over-refusal of `[[ a && b ]]` is accepted -- write separate `[ ]` statements.
Round 10 found three more lexer misreads, each a PASS over git's 128 (a list in an
unquoted heredoc body's `$(…)`, ` #` inside `${…}` read as a comment, `\\&&` read
as a redirect), so lists are no longer found by the lexer at all. `backstop` reads
the RAW text on its own smaller model and refuses every `&&`, `||`, job `&` and
unread `<<`; the lexer only supplies the readings it may agree with. Round 11 found
seven constructs that fooled both the same way, since the two share one quote and
heredoc model (`$$'`, quotes in code backticks or in `"${…}"`, a heredoc opener
ending in `\\`, bash 3.2 closing `$(` at a `)` in a heredoc body, `$[1<<E ]`, and the
carve-out below after `export \\`). So bash itself is the third reader (`BashParse`):
`bash -n` on perturbed copies of the block, which parses and never executes. A position
is excluded only when all three read it as literal: a quoted-delimiter heredoc body both
models read as one, or a position both read as single-quoted, that a bash probe PROVES is
that text (round 13: closer runs could not leave every nesting). So it OVER-refuses:
`&`, `&&` or `||` in double-quoted text, in a comment or in an unquoted heredoc body, a
`<<` the lexer did not read as a heredoc (an arithmetic shift outside a plain `$((…))`,
`<<\\EOF`), `>&$fd`, a single-quoted operator inside `$(…)`, backticks or `${…}` (bash
defers all three to run time, so no probe proves the quote), one right after a backslash
(even a literal one in single quotes), one in `$'…'`, and a quoted heredoc body inside
`$(…)` or before another heredoc opened on the same line, and one in a top-level
`NAME=( … )` of a block that ends in an EOF-ended heredoc or a `\\`. Single-quote such text at top
level, keep the heredoc at top level, or write the text to a file outside the block. bash
cannot be run, or cannot parse the block: nothing is excluded.
Not refused, because each is recorded or is no list:
  - the `&` of a redirection (`2>&1`, `>&2`, `>&-`, `<&0`, `&>`): a trailing
    `&` job after one is still refused;
  - the whole value of a one-line `NAME=$(…)` that bash reads as the start of a
    statement (not an argument after `export \\` or `echo \\`, nor a one-word slot such
    as a `case` subject or a `[[ -n` operand), whose body is ONE
    `&&` chain, with no `;`, `||`, `&` or newline: only then is the substitution's status the
    failing member's, which the assignment carries to the trap (probe on bash
    3.2: `X=$(grep x /nonexistent && echo y)` traps rc=2). In an `if`, `while`,
    `until` or `elif` condition, or after `!`, bash runs no trap at all, so the
    assignment carries nothing there: that is the disclosed condition residual, not
    this carve-out (review round 13, N1). `X=$(a || b)`,
    `X=$(a && b; c)` and `X=$(a & wait)` end on another command's status and
    are refused; `{ … && …; }`, `( … && … )` and `echo $(… && …)` trap nothing.
A screen is UNREADABLE -- never PASS --
when a recorded failure precedes it (`failed_command=<doc>:<line>:<status>`), its markers are missing,
repeated or mangled (the block died, or the screen sits in a loop), any member
of its own pipeline exited >= 2 (the error-reads-as-zero class:
`grep x missing | wc -l` prints 0), its trimmed stdout is empty or not one
integer, or the block timed out or could not launch. Inside the screen a member
may exit 1, because the measured `grep -c`/`grep -vc` exits 1 exactly when it
reads 0; that is the screen's own reading, judged member by member.

The cost, accepted because a false UNREADABLE never certifies: a statement
before a screen that legitimately exits non-zero makes every later screen in
its block UNREADABLE. Four triggers, each with its remedy, which belongs to the
document's author:
  - a grep that matches nothing (status 1): filter with a tool that exits 0 on
    no match, so no `||` is needed -- `awk '/PAT/'`, `sed -n '/PAT/p'`, or for a
    count `awk '/PAT/{n++} END{print n+0}'`. Under pipefail an upstream error
    still surfaces: `$(git diff --name-only nosuchref HEAD | awk '/\\.py$/')`
    reads `failed_command=…:128`, and a good base with no match reads 0. `|| true`
    is refused: it masks every status, git's 128 included, and would certify a
    freeze against a mistyped base;
  - `xargs grep`: BSD xargs exits 1 when any batch's grep matches nothing (on
    HemaSuite, `git ls-files -z | xargs -0 grep -n … | grep -v …` has
    PIPESTATUS `0 1 0`): `git ls-files -z | xargs -0 awk '/PAT/{print FILENAME":"FNR":"$0}'`;
  - `yes | head -1` (SIGPIPE, 141): restructure so no producer outlives its
    reader before a screen (there is no declared form for it);
  - an untracked tool, missing from the throwaway worktree (a `.venv/bin/python`
    exits 127, because `.venv` is not in the commit): call a tracked tool, an
    absolute path, or a PATH lookup (`python3`) instead.
A SIGPIPE inside a screen's own pipeline reads UNREADABLE:exit_status=141,….
Residuals: `export X=$(cmd)` exits 0 in bash itself; a non-final member of a
screen's own pipeline that fails with status 1 (`cat` on a missing file) reads
as grep's no-match; and a failing command earlier on the screen's own line
(`false; echo 0   # expect 0`) is not seen; and a failure inside a CHILD SHELL
-- `bash -c '…'`, `sh script`, a heredoc fed to `bash`, `xargs sh -c`, `eval` of
a list -- never reaches this trap (it is not inherited across processes), so
`bash -c 'git diff nosuchref > f; echo ok'` reads as clean; and a failing
`if`/`while`/`until` CONDITION or a `!`-NEGATED command is neither refused nor
recorded (bash runs no ERR trap for either): `if git diff nosuchref …; then …;
fi` and `X=$(true && ! git diff nosuchref …)` read as clean. No text check can close
these; the `coverage:` line states them on every run.

Code the parse cannot see is refused at RUN time (task #14; review rounds 14 and 17).
`bash -n` reads with aliases off, so an alias defined in single quotes (`alias q='git
diff nosuchref > f && echo'`) runs a list no reader saw; and `.`/`source` runs a body --
a heredoc, stdin, or a file -- that no reader parsed, in this shell. A DEBUG trap cannot
watch for either (it clobbers bash 3.2's PIPESTATUS), so: `source` and `.` are shadowed
by functions that record `!source@<line>`, a top-level RETURN trap records the same for
`builtin .`, `command source` and posix mode (where the special builtin outranks a
function), and both markers of every screen sample `expand_aliases`, posix mode and
`alias -p`, recording `!aliases@<line>`. Any such record reads
`UNREADABLE:unsupported_runtime=<source|aliases>@<doc>:<line>`. Every source is refused,
a tracked file's too: its body is as unparsed as a heredoc's. The preamble runs
`unalias -a` first, so a BASH_ENV's aliases are not the document's. Residuals: aliases
turned on and off again between two screens' markers, a `builtin`/`command` source
inside a function (no RETURN trap there without `set -T`, which would fire on every
function return), and a block that disarms the guard (`trap - RETURN`, `unset -f
source`). The trap is disarmed inside screens
because bash 3.2 reports a partial PIPESTATUS to it and leaves its own
PIPESTATUS behind.

Output and exit:

    screen: <doc>:<line> expect=<N> got=<value|UNREADABLE:reason> <PASS|FAIL>
    EXPECT: PASS screens=S                          exit 0
    EXPECT: FAIL screens=S failed=F unreadable=U    exit 1  (F: read and wrong; U: unreadable)
    EXPECT: CANNOT_JUDGE reason=<r>                 exit 2  (usage, bad sha, unreadable doc,
                                                             worktree add/remove failure,
                                                             terminated by a signal)
    EXPECT: NONE                                    exit 3  (no tagged screen: nothing certified)
    coverage: ...
"""

from __future__ import annotations

import argparse
import functools
import itertools
import os
import re
import secrets
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from h_mad_doc_block_exec import (  # noqa: E402
    BASH, Block, BlockTimeout, DocBlockError, _fence_events, _validate_timeout, run_block,
)

SCREEN = re.compile(r"#[ \t]*expect[ \t]+(-?\d+)[ \t]*(?:$|[,;(]|--|—)")
RAW_SCREEN = re.compile(r"(?:^|[ \t;&|()<>])" + SCREEN.pattern)
ASSIGN_SUBST = re.compile(r"[ \t]*[A-Za-z_][A-Za-z0-9_]*=\$\((?!\()")
# The delimiter must end the word: bash's delimiter for `<<'E'x` is `Ex`, and reading it as `E`
# would end the body early or late -- a body the backstop skips as data. No match reads as code.
HEREDOC = re.compile(r"<<(-?)[ \t]*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\2"
                     r"(?![^ \t;&|<>()])")  # M:HEREDOC-WORD-END
INTEGER = re.compile(r"-?\d+")
# A `$((…))` with no parens, quotes, backticks or escapes inside cannot hold a subshell or a
# heredoc, so its `<<` is a shift. A bare `((…))` gets no such pass: `((cmd) <<E` is two
# subshells and a heredoc (review round 9, E2).
PURE_ARITH = re.compile(r"\$\(\([^()'\"`\\]*\)\)")
GIT_REDIRECTS = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR",
                 "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE")
COVERAGE = ("coverage: only statements ending in a '# expect <N>' comment inside a bash/sh "
            "fence are screened; expectations stated in prose or untagged commands are not run; "
            "a failure inside a child shell (bash -c, sh script, a heredoc fed to bash, "
            "xargs sh, eval) never reaches this trap and is not seen; "
            "a failing if/while/until condition or !-negated command is neither refused nor "
            "recorded; "
            "every . or source, and aliases on at a screen (expand_aliases, posix, an alias "
            "defined), is refused at run time, but aliases turned on and off again between "
            "screens, a builtin or command source inside a function, or a block that disarms "
            "the guard (trap - RETURN, unset -f source) is not seen; "  # M:COVERAGE-UNPARSED
            "a statement that leaves the worktree by absolute path reads that tree, not the sha")
# The ERR trap records EVERY non-zero status outside a screen: no status is judged benign
# from command text (three rounds of text heuristics each opened a hole in another). It
# writes to a file, not a variable, so a function body, subshell or command substitution
# (reached through `set -E`) records into the same list as the top level.
TRAP = '__hmad_r=$?; echo "$((LINENO - __hmad_l0 - 1)):$__hmad_r" >> "$__hmad_ff"'  # M:ANY-NONZERO
# Code no parse saw (task #14). A `.`/`source` runs a body -- a heredoc, stdin, or a file --
# that no reader parsed, in this shell, so a list in it is unrecorded: every one is recorded
# as `!source@<line>` and refused. Shadow functions see a call from any depth; a top-level
# RETURN trap (no `set -T`, so no function return fires it) also sees `builtin .`,
# `command source` and posix mode, where the special builtin outranks a function.
SOURCED = "!source@$(({line} - __hmad_l0 - 1))"
SHADOWS = "\n".join(
    f'{name}() {{ echo "{SOURCED.format(line="BASH_LINENO[0]")}" >> "$__hmad_ff"; '
    f'builtin {name} "$@"; }}' for name in ("source", "."))  # M:SOURCE-SHADOW
RETURN_TRAP = f'echo "{SOURCED.format(line="LINENO")}" >> "$__hmad_ff"'  # M:SOURCE-RETURN
# Aliases are parsed with expansion off by `bash -n`; a block that turns expansion (or posix
# mode) on and defines one runs text no reader read. Sampled at both markers of every screen
# (the begin marker runs with the ERR trap already disarmed), each word backslashed so an
# alias cannot expand it.
ALIAS_CHECK = ('{ \\shopt -q expand_aliases || \\shopt -qo posix || '
               '\\test -n "$(\\alias -p)"; } && '  # M:ALIAS-SAMPLE
               '\\echo "!aliases@$((LINENO - __hmad_l0 - 1))" >> "$__hmad_ff"')


class CannotJudge(Exception):
    pass


class Terminated(Exception):
    pass


@dataclass
class Screen:
    doc: str
    line: int
    expect: int
    got: str = "UNREADABLE:not_run"
    verdict: str = "FAIL"  # M:DEFAULT-FAIL


@dataclass
class Line:
    text: str
    code: str = ""
    comment: str = ""
    quoted: bool = False             # the line starts inside a quoted string
    body: int | None = None          # heredoc body or terminator: the opener's index
    heredoc_end: int | None = None   # on an opener: its last terminator's index
    backslash: bool = False
    op: bool = False
    literal: bool = False            # a body line of a quoted-delimiter heredoc: pure data
    heredoc: tuple | None = None     # on a body line: (opener index, `<<` position)
    term: str | None = None          # on a body line: the terminator the lexer read
    openers: set = field(default_factory=set)  # `<<` positions the lexer read as heredocs
    chain: tuple | None = None       # a whole one-line `NAME=$(…)`: its paren positions
    squote: set = field(default_factory=set)  # positions the lexer read as single-quoted


def lex(texts: list[str]) -> list[Line]:
    """Quote, comment, here-document and list structure of one block, line by line."""
    lines = [Line(t) for t in texts]
    quote, pending, current = None, [], None
    for i, info in enumerate(lines):
        text = info.text
        if current is not None:
            delim, tabs, opener, literal, at = current
            info.body, info.literal, info.heredoc = opener, literal, (opener, at)
            info.term = delim
            if (text.lstrip("\t") if tabs else text) == delim:
                lines[opener].heredoc_end = i
                current = pending.pop(0) if pending else None
            continue  # M:HEREDOC-BODY: a body line has no code and no comment
        info.quoted = quote is not None
        cut, k, arith, parens, ticks = len(text), 0, 0, [], []
        assign = None if info.quoted else ASSIGN_SUBST.match(text)
        assign_open = assign.end() - 1 if assign else None
        assign_close = None
        while k < len(text):
            ch = text[k]
            if quote == "'":
                info.squote.add(k)  # M:LEX-SQUOTE
                quote = None if ch == "'" else quote
            elif quote == '"' and text.startswith("$(", k) and not text.startswith("$((", k):
                parens.append((k + 1, '"'))  # M:DQUOTE-SUBST: `"$(…)"` holds code, not text
                quote = None
                k += 1
            elif quote == '"' and ch == "`":
                ticks.append('"')
                quote = None
            elif quote in ('"', "$'"):  # `$'…'` honours backslash escapes like `"…"`
                if ch == "\\":
                    k += 1
                elif ch == quote[-1]:
                    quote = None
            elif ch == "\\":
                k += 1
            elif ch == "$" and text[k + 1:k + 2] == "'":  # M:ANSI-C
                quote = "$'"
                k += 1
            elif ch in "'\"":
                quote = ch
            elif text.startswith("((", k):  # arithmetic: `<<` there is a shift
                arith += 1
                k += 1
            elif arith and text.startswith("))", k):
                arith -= 1
                k += 1
            elif ch == "(":
                parens.append((k, None))
            elif ch == ")" and parens:
                opened, outer = parens.pop()
                if opened == assign_open:
                    assign_close = k
                quote = outer
            elif ch == "`" and ticks:
                quote = ticks.pop()
            elif (text.startswith("<<", k) and not arith  # M:ARITH-NOT-HEREDOC: a shift
                  and not text.startswith("<<<", k) and text[k - 1:k] != "<"):
                match = HEREDOC.match(text, k)  # only unquoted code reaches here
                if match:
                    pending.append((match.group(3), match.group(1) == "-", i,
                                    bool(match.group(2)), k))
                    info.openers.add(k)
                    k = match.end()
                    continue
            elif ch == "#" and (k == 0 or text[k - 1] in " \t;&|()<>"):  # M:COMMENT-UNQUOTED
                cut = k
                break
            k += 1
        info.code, info.comment = text[:cut], text[cut:]
        # A one-line `NAME=$(…)` whose code ends at its closing paren: `backstop` decides whether
        # its body is the one `&&` chain the assignment carries to the trap.
        if assign_close is not None and assign_close == len(info.code.rstrip()) - 1:
            info.chain = (assign_open, assign_close)  # M:AND-CHAIN-ONLY
        if quote is None:
            info.backslash = (not info.comment
                              and (len(text) - len(text.rstrip("\\"))) % 2 == 1)
            info.op = info.code.rstrip().endswith(("|", "&&", "|&"))  # M:CONT-OP-CODE
            if current is None and pending:
                current = pending.pop(0)
    for _, _, opener, _, _ in ([current] if current else []) + pending:
        lines[opener].heredoc_end = len(lines) - 1
    return lines


def _raw_op(text: str, k: int, prev: str | None) -> tuple[str | None, int]:
    """(kind, width) of the operator at k: `&&`, `||`, a job `&`, `;`, or (None, 1).

    No `&&` or `||` is exempt by its text -- not in `[[ ]]` or `(( ))`, not in a condition,
    not `|| true` or `|| [ $? = 1 ]`: each such exemption had a hole (rounds 6-9).
    """
    if text.startswith("&&", k):
        return "&&", 2  # M:REFUSE-AND
    if text.startswith("||", k):
        return "||", 2  # M:REFUSE-OR: no `||` is exempt
    if text.startswith(";;", k):
        return None, 2
    if text[k] == ";":
        return ";", 1
    if text[k] != "&":
        return None, 1
    nxt = text[k + 1:k + 2]
    redirect = (nxt == ">" or prev in ("<", "|")  # `&>`, `<&` (`&>>`, `|&`: bash 4 only)
                or (prev == ">" and nxt != "" and nxt in "0123456789-"))  # M:BACKSTOP-REDIRECT
    return (None if redirect else "&"), 1  # M:REFUSE-JOB


def _one_chain(text: str, parens: tuple[int, int], code: list[tuple[str, int]]) -> bool:
    """The `NAME=$(a && b)` carve-out: the substitution's status is the failing member's, which
    the assignment carries to the trap (`X=$(grep x /nonexistent && echo y)` traps rc=2). It
    holds only when every operator on the line is an `&&` between the lexer's parens: `a || b`,
    `a && b; c` and `a & wait` end on another command's status, and an operator after the
    paren -- the lexer reads `)#&& …` as a comment, bash as a word and a list -- is outside."""
    opened, closed = parens
    return all(kind == "&&" and opened < pos < closed for kind, pos in code)  # M:BACKSTOP-CHAIN


def _quote_blind(text: str) -> list[tuple[str, int]]:
    """Every operator in a line read with no quote state at all: an unquoted heredoc body."""
    found, prev, k = [], " ", 0
    while k < len(text):
        kind, width = _raw_op(text, k, prev)
        if kind:
            found.append((kind, k))
        prev, k = text[k + width - 1], k + width
    return found


class BashParse:
    """bash's own reading of one block, taken with `bash -n` on perturbed copies of it.

    The third reader, and the only one that does not share the lexer's and the backstop's
    quote and heredoc model: seven constructs fooled both of those the same way (review
    round 11, M1-M7). `-n` parses and never executes. `declare -f` of the block wrapped in a
    function was rejected, because a block that closes the wrapper runs at top level.

    bash vouches for a position only on POSITIVE evidence, never because a perturbation
    failed to break the parse. bash 3.2 defers `$(…)`, backticks, `${…}` and arithmetic to
    run time, so anything inside them parses under `-n` whatever it is. Rounds 11 and 12
    pushed a doubled operator out to top level with runs of closers, and round 13 found
    that no finite set of closers leaves every nesting: inside `"$(…)"`, `"`…`"`,
    `${x:-$(…)}` or `$[ $(…) ]` the `)`s land in the enclosure, and one later backtick
    paired with the backtick run. So each probe proves where the position IS, against a
    control that differs only in the probe's payload:
      - single-quoted text (`code_at`): ` '` + doubled operator + `' ` breaks the parse and
        ` 'x' ` does not. Only a `'` that CLOSES a quote at a parsed level puts the payload in
        code; where the `'` opens a quote, or the text is deferred or in `"…"`, the two
        copies read alike. The blanks keep the payload a word of its own: joined to the word
        before it, its text became part of a heredoc delimiter (`<<E'x'` ends at a line
        `Ex`), and the two copies then ended the body on different lines (review round 14).
        Only the leading blank does that work; the trailing one is belt and braces. A
        position right after a backslash is refused: a live one escapes the first blank and
        joins the payload to the word again (`<<E\\ 'x'` is the delimiter `E x`). A proof
        counts as it stands or inside `{ … }`: bash 3.2 exits 1, not 2, on a syntax error in
        a top-level `NAME=( … )` (review round 15), while the group alone fails a block with
        an EOF-ended heredoc or a last line ending in `\\` (review round 16). A quote in a
        top-level array in such a block is proven by neither: an accepted over-refusal;
      - a heredoc body line (`body_code_at`): a line `xx…\\`, a terminator line, a doubled
        operator, then `:<<'TERM'` to reopen breaks the parse, and the same with `x` does
        not. The `\\` line proves the body QUOTED: in an unquoted body bash joins it to the
        terminator, which then ends nothing (review round 15: a `<<E` hidden from both
        models was proven by its terminator alone). Its `x`s are chosen so that `xx…TERM`
        occurs NOWHERE in the block, backslash-newlines removed -- not merely as no word: a
        body line ending in `\\` joins in front of the join line, so a hidden UNQUOTED
        delimiter need only END in `xx…TERM` (`<<axE` after a line `a\\`), and `<<xE` was
        ended by the join itself (review rounds 16 and 17). An unquoted delimiter is
        written out in full; any quoting in one makes its body literal. A
        line of the doubled operator inserted before the body line must also parse: at a
        parsed code level it cannot, even where the line's own operator sits deferred in
        `$(…)` (round 11's M5, review round 16), while the reopened heredoc would swallow
        the rest and let the control parse.
    So bash vouches for nothing inside a substitution, backticks or `${…}`: a single-quoted
    operator or a heredoc body there is refused (accepted over-refusals). Fail closed: a
    block bash cannot parse, or a bash call that cannot run, times out, is killed or exits
    other than 0 or 2 (2 is its syntax error; see the group above), vouches for nothing --
    `_parses` answers None there, never False.
    """

    def __init__(self, texts: list[str]):
        self.text = "\n".join(texts)
        self.starts = [0]
        for t in texts[:-1]:
            self.starts.append(self.starts[-1] + len(t) + 1)

    @staticmethod
    def _parses(text: str) -> bool | None:
        """True on bash -n's 0, False on its syntax error 2; None when bash gave no answer."""
        try:
            status = subprocess.run([BASH, "-n", "-c", text], stdin=subprocess.DEVNULL,  # M:ORACLE-PINNED
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                    timeout=10).returncode
        except (OSError, ValueError, subprocess.SubprocessError):  # ValueError: a NUL byte
            return None  # M:ORACLE-NO-BASH
        return {0: True, 2: False}.get(status)  # M:ORACLE-STATUS

    @functools.cached_property
    def parses(self) -> bool | None:
        return self._parses(self.text)

    def _proves(self, probe: str, control: str) -> bool:
        return self._parses(probe) is False and self._parses(control) is True  # M:ORACLE-PROVES

    def code_at(self, i: int, k: int, op: str) -> bool:
        """Whether the operator `op` at line i, column k is anything but single-quoted text."""
        if self.parses is not True:
            return True  # M:ORACLE-UNPARSED
        at = self.starts[i] + k
        before, after = self.text[:at], self.text[at + len(op):]
        if before.endswith("\\"):
            return True  # M:ORACLE-BACKSLASH
        wraps = (lambda payload: before + payload + after,  # M:ORACLE-UNGROUPED
                 lambda payload: "{\n" + before + payload + after + "\n}")  # M:ORACLE-GROUP
        return not any(self._proves(wrap(f" '{op} {op}' "), wrap(" 'x' "))  # M:ORACLE-SQUOTE
                       for wrap in wraps)

    def body_code_at(self, i: int, op: str, term: str | None) -> bool:
        """Whether line i, holding the operator `op`, is anything but quoted heredoc body text,
        where `term` is the terminator the lexer read for that body."""
        # Belt and braces, not separately pinned: `HEREDOC` never captures a `'`, and an
        # unparsed block or a missing terminator rarely survives the probes below.
        if self.parses is not True or not term or "'" in term:
            return True  # M:ORACLE-BODY-UNPARSED
        line = self.starts[i]
        if self._parses(self.text[:line] + f"{op} {op}\n" + self.text[line:]) is not True:
            return True  # M:ORACLE-BODY-LINE
        flat = self.text.replace("\\\n", "")
        join = next(p for p in ("x" * n for n in itertools.count(1))
                    if p + term not in flat)  # M:ORACLE-JOIN-UNSEEN
        cut = lambda payload: (self.text[:line] + f"{join}\\\n{term}\n{payload}\n:<<'{term}'\n"  # noqa: E731
                               + self.text[line:])  # M:ORACLE-QUOTED-BODY
        return not self._proves(cut(f"{op} {op}"), cut("x"))  # M:ORACLE-HEREDOC

    def starts_statement(self, i: int, k: int) -> bool:
        """Whether line i, column k is where bash starts a statement. A stray `then` breaks
        the parse there, but also in a slot that takes ONE word (a `case` subject, a `[[ -n`
        operand); a plain extra word parses at a statement start and not in such a slot
        (review round 12, M2). Both answers must be definite."""
        if self.parses is not True:
            return False  # M:ORACLE-STATEMENT-UNPARSED
        at = self.starts[i] + k
        return (self._parses(self.text[:at] + "then " + self.text[at:]) is False  # M:ORACLE-STATEMENT
                and self._parses(self.text[:at] + "x " + self.text[at:]) is True)  # M:ORACLE-WORD


def backstop(lexed: list[Line]) -> list[tuple[int, str]]:
    """(index, kind) of every `&&`, `||`, job `&` and unread `<<` in the RAW text.

    The module's only list detector. `lex` found lists until round 10, and every exemption
    it keyed on text opened a hole the next review found (a heredoc body's `$(…)`, ` #` in
    `${…}`, `\\&&`). This reader has its own, smaller model, and excludes text only where
    `lex` agrees AND `BashParse` -- bash's own parse -- reads it as text. The two models
    share one quote and heredoc model, so agreement between them alone was fooled seven
    ways in round 11; bash is the reader that does not share it:
      - quotes (`'…'`, `"…"`, `$'…'`) and backslash escapes outside `'…'`, carried across
        lines -- so `\\&&` is a literal `&` then a job, and `\\|&` is not bash 4's `|&`;
      - a comment only at a blank-preceded `#` in code outside `${…}`: a strict subset of
        bash's rule, so the comment never hides a quote bash sees. Operators in a comment
        are still counted (prose `&` there over-refuses);
      - a heredoc only where the lexer read one AND this reader is in code at its `<<`. A
        quoted-delimiter body is skipped; an unquoted body is counted with no quote state,
        since its quotes are text. A `<<` the lexer did not read as a heredoc refuses.
    Nothing is excluded except a position BOTH readers call single-quoted; double-quoted
    text is counted, because `"$(a && b)"` is code. The one `NAME=$(a && b)` carve-out
    survives only where the lexer applied it, this reader finds nothing else on the line,
    and bash reads the assignment as the start of a statement.
    """
    hits, quote, opened, confirmed = [], None, 0, set()
    bash = BashParse([info.text for info in lexed])
    for i, info in enumerate(lexed):
        text = info.text
        if info.heredoc in confirmed:  # M:BACKSTOP-BODY
            hits.extend((i, kind) for kind, k in _quote_blind(text) if kind != ";"
                        and (not info.literal  # M:BACKSTOP-LITERAL-BODY
                             or bash.body_code_at(i, kind, info.term)))  # M:ORACLE-BODY
            continue
        found, spans, braces, comment, prev, k, shift_until = [], [], 0, False, " ", 0, -1
        opened = -1 if quote == "'" else opened
        while k < len(text):
            ch = text[k]
            if ch == "\\" and quote != "'" and not comment:
                prev, k = None, k + 2  # M:BACKSTOP-ESCAPE: an escaped character is no operator
                continue
            if comment or quote is not None:
                if comment or ch != quote[-1]:
                    kind, width = _raw_op(text, k, prev)
                    if kind:
                        found.append((kind, k))
                    prev, k = text[k + width - 1], k + width
                    continue
                if quote == "'":
                    spans.append((opened, k))
                quote = None
            elif text.startswith("$'", k):
                quote, prev, k = "$'", None, k + 2
                continue
            elif ch == "'" or ch == '"':
                quote, opened = ch, k
            elif text.startswith("${", k):
                braces += 1
            elif text.startswith("$((", k) and PURE_ARITH.match(text, k):
                shift_until = PURE_ARITH.match(text, k).end()
            elif ch == "}" and braces:
                braces -= 1
            elif ch == "#" and not braces and prev in (" ", "\t"):  # M:BACKSTOP-COMMENT
                comment = True
            elif text.startswith("<<<", k):
                prev, k = "<", k + 3
                continue
            elif text.startswith("<<", k) and k < shift_until:
                prev, k = "<", k + 2  # M:BACKSTOP-SHIFT
                continue
            elif text.startswith("<<", k):
                if k in info.openers:
                    confirmed.add((i, k))
                else:
                    found.append(("<<", k))  # M:BACKSTOP-UNREAD-HEREDOC
                prev, k = "<", k + 2
                continue
            else:
                kind, width = _raw_op(text, k, prev)
                if kind:
                    found.append((kind, k))
                prev, k = text[k + width - 1], k + width
                continue
            prev, k = ch, k + 1
        if quote == "'":
            spans.append((opened, len(text)))
        lexer_says = info.squote  # M:BACKSTOP-AGREE-LEXER
        data = lambda pos: (pos in lexer_says  # noqa: E731
                            and any(a < pos < b for a, b in spans))  # M:BACKSTOP-AGREE-OWN
        code = [(kind, pos) for kind, pos in found
                if not data(pos) or ((kind != ";" or info.chain)  # a `;` matters to the carve-out
                                     and bash.code_at(i, pos, kind))]  # M:ORACLE-DATA
        name = len(text) - len(text.lstrip(" \t"))
        if (info.chain and _one_chain(text, info.chain, code)  # M:CHAIN-APPLIED
                and bash.starts_statement(i, name)):  # M:ORACLE-CHAIN-START
            code = []
        hits.extend((i, kind) for kind, _ in code if kind != ";")  # M:BACKSTOP-HITS
    return hits


def statement_start(lines: list[Line], end: int, floor: int) -> int:
    """Walk up from a tagged line to the first line of its statement."""
    start = end
    while start > floor:
        if lines[start].quoted or lines[start].body is not None:  # M:CONT-QUOTED
            start -= 1
            continue
        j = start - 1
        if lines[j].backslash:  # M:CONT-BACKSLASH
            start = j
            continue
        while (j > floor and lines[j].body is None and not lines[j].quoted
               and not lines[j].code.strip()):  # M:CONT-SKIP-BLANK
            j -= 1
        k = lines[j].body if lines[j].body is not None else j
        if lines[k].op:  # M:CONT-OP
            start = k
            continue
        break
    return start


def shell_blocks(text: str) -> list[list[tuple[int, str]]]:
    """Every bash/sh fence body as (doc line, dedented line) pairs."""
    blocks, body, indent = [], None, 0
    for event in _fence_events(text):
        if event.kind == "open":
            words = event.info.split()
            body = [] if words and words[0] in ("bash", "sh") else None  # M:SHELL-ONLY
            indent = event.indent
        elif event.kind == "body" and body is not None:
            line = text[event.start:event.end].rstrip("\r\n")
            removed = min(indent, len(line) - len(line.lstrip(" ")))
            body.append((event.lineno, line[removed:]))
        elif event.kind == "close" and body is not None:
            blocks.append(body)
            body = None
    if body is not None:
        blocks.append(body)
    return blocks


def screens_in(texts: list[str]) -> list[tuple[int, int, int, int]]:
    """(first index, last index, tagged index, N) of each tagged statement, in order."""
    lines = lex(texts)
    found, floor = [], 0
    for i, info in enumerate(lines):
        if i < floor:
            continue
        match = SCREEN.match(info.comment)  # M:SCREEN-IN-COMMENT
        if not match:
            continue
        start = statement_start(lines, i, floor)
        if start == i and not info.code.strip():
            continue  # M:COMMENT-ONLY: a comment-only line is not a statement
        end = info.heredoc_end if info.heredoc_end is not None else i  # M:HEREDOC-END
        found.append((start, end, i, int(match.group(1))))
        floor = end + 1
    return found


def unparsed_in(texts: list[str], spans) -> list[tuple[int, int]]:
    """(index, N) of every `# expect <N>` the lexer did not accept: counted, never dropped.

    A misread quote or here-document would otherwise turn later screens into string or
    body text and drop them silently while the verdict certifies. A comment-only line the
    lexer read as one is no statement, so it is the only raw match left out.
    """
    lines, tagged, out = lex(texts), {t for _, _, t, _ in spans}, []
    for i, text in enumerate(texts):
        match = RAW_SCREEN.search(text)
        if not match or i in tagged:
            continue
        info = lines[i]
        if (info.body is None and not info.quoted and not info.code.strip()
                and SCREEN.match(info.comment)):
            continue
        out.append((i, int(match.group(1))))  # M:UNPARSED-COUNTED
    return out


def instrument(texts: list[str], spans, nonce: str) -> str:
    out = []
    starts = {s: n for n, (s, _, _, _) in enumerate(spans)}
    ends = {e: n for n, (_, e, _, _) in enumerate(spans)}
    for k, line in enumerate(texts):
        if k in starts:
            out.append(f"trap - ERR; {ALIAS_CHECK}; "  # M:ALIAS-AT-BEGIN
                       f"printf '\\n%s\\n' 'HMADB_{nonce}_{starts[k]}'")
        out.append(line)
        if k in ends:
            out.append(f"__hmad_ps=\"${{PIPESTATUS[*]}}\"; {ALIAS_CHECK}; "  # M:ALIAS-AT-END
                       f"printf '\\n%s %s|%s\\n' 'HMADE_{nonce}_{ends[k]}' "
                       f"\"$__hmad_ps\" \"$(tr '\\n' ' ' < \"$__hmad_ff\")\"; "
                       f"trap \"$__hmad_trap\" ERR")
    return "\n".join(out) + "\n"


def read_screen(stdout: str, nonce: str, i: int, expect: int,
                where=lambda line: str(line)) -> tuple[str, str]:
    lines = stdout.split("\n")
    begin = [k for k, line in enumerate(lines) if line == f"HMADB_{nonce}_{i}"]
    end = [k for k, line in enumerate(lines) if line.startswith(f"HMADE_{nonce}_{i} ")]
    if len(begin) > 1 or len(end) > 1:
        return "UNREADABLE:markers_repeated", "FAIL"
    if not end and len(begin) <= 1:
        return "UNREADABLE:block_died", "FAIL"
    tail = lines[end[0]].split(" ", 1)[1]
    if len(begin) != 1 or begin[0] > end[0] or "|" not in tail:  # M:MARKERS-ONCE
        return "UNREADABLE:markers_mangled", "FAIL"
    status_field, failed_field = tail.split("|", 1)
    statuses = status_field.split()
    if not statuses or any(not s.isdigit() or int(s) >= 2 for s in statuses):  # M:PIPESTATUS
        return "UNREADABLE:exit_status=" + ",".join(statuses), "FAIL"
    failures = failed_field.split()
    unread = [f[1:] for f in failures if f.startswith("!")]
    if unread:  # M:UNREAD-CODE: anywhere in the list, ahead of any recorded status
        kind, _, line = unread[0].partition("@")
        return f"UNREADABLE:unsupported_runtime={kind}@{where(line)}", "FAIL"
    if failures:  # M:EARLIER-FAILURE
        line, _, status = failures[0].partition(":")
        return f"UNREADABLE:failed_command={where(line)}:{status}", "FAIL"
    value = "\n".join(lines[begin[0] + 1:end[0]]).strip()
    if not value:
        return "UNREADABLE:empty_output", "FAIL"
    if not INTEGER.fullmatch(value):  # M:INTEGER-ONLY
        return "UNREADABLE:non_integer", "FAIL"
    return value, "PASS" if int(value) == expect else "FAIL"  # M:COMPARE


def _git(root: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "-C", root, *args],
                          capture_output=True, text=True)


def _preamble(cwd: str, pidfile: str) -> str:
    failfile = os.path.join(os.path.dirname(pidfile), "failures")
    return "\n".join([
        "exec </dev/null",  # M:STDIN-NULL
        f"echo $$ > {shlex.quote(pidfile)}",
        f"cd -- {shlex.quote(cwd)} || exit 97",  # M:CD-WORKTREE
        f"__hmad_ff={shlex.quote(failfile)}; : > \"$__hmad_ff\"",
        "set -E",  # M:ERRTRACE: the trap also fires inside function bodies
        "set -o pipefail",  # M:PIPEFAIL: an errored non-final member fails its pipeline
        f"__hmad_trap={shlex.quote(TRAP)}",
        'trap "$__hmad_trap" ERR',  # M:TRAP-ARMED
        "\\unalias -a",  # M:UNALIAS: a BASH_ENV's aliases are not the document's
        SHADOWS,
        f"trap {shlex.quote(RETURN_TRAP)} RETURN",  # M:RETURN-ARMED
        "__hmad_l0=$LINENO",
    ])


def evaluate(blocks, cwd: str, timeout: float, pidfile: str) -> list[Screen]:
    screens = []
    for doc, lines_at in blocks:
        texts = [line for _, line in lines_at]
        spans = screens_in(texts)
        batch = [Screen(doc, lines_at[t][0], n) for _, _, t, n in spans]
        unparsed = [Screen(doc, lines_at[i][0], n, "UNREADABLE:unparsed")
                    for i, n in unparsed_in(texts, spans)]
        screens.extend(sorted(batch + unparsed, key=lambda s: s.line))
        if not spans:
            continue  # M:SKIP-UNTAGGED
        nonce = secrets.token_hex(8)
        script = instrument(texts, spans, nonce)
        origin = _origins(texts, spans, lines_at)
        block = Block(script, "plain", lines_at[0][0], "")
        try:
            result = run_block(block, timeout=timeout, preamble=_preamble(cwd, pidfile))
        except BlockTimeout:
            for s in batch:
                s.got = "UNREADABLE:timeout"
            continue
        except DocBlockError as error:
            for s in batch:
                s.got = f"UNREADABLE:{type(error).__name__}"
            continue

        def where(line: str, doc=doc, origin=origin) -> str:
            n = int(line) if line.isdigit() else -1
            return f"{doc}:{origin[n] if 0 <= n < len(origin) else '?'}"
        for i, s in enumerate(batch):
            s.got, s.verdict = read_screen(result.stdout, nonce, i, s.expect, where)
        _refuse_untracked(batch, spans, lex(texts), doc, lines_at)
    return screens


def _refuse_untracked(batch, spans, lexed, doc, lines_at) -> None:
    """An `&&`/`||` list or a `&` job at or before a screen is refused, never read.

    bash runs no ERR trap for a non-final member of an `&&`/`||` list or for a background
    job, so their failures cannot be recorded. This module refuses them rather than adding
    another tracking mechanism. `backstop` finds them: `lex` keeps no list detection of its own,
    since every hit it made the backstop makes too (round 10).
    """
    found = backstop(lexed)  # M:BACKSTOP-APPLIED
    for (_, end, _, _), s in zip(spans, batch):
        first = next(((k, kind) for k, kind in found if k <= end), None)
        if first is not None:  # M:REFUSE-APPLIED
            s.got = f"UNREADABLE:unsupported_construct={first[1]}@{doc}:{lines_at[first[0]][0]}"
            s.verdict = "FAIL"


def _origins(texts, spans, lines_at) -> list[int]:
    """Doc line of every instrumented script line (a marker line takes its neighbour's;
    a heredoc body or terminator line, where bash reports the command, takes its opener's)."""
    starts = {s for s, _, _, _ in spans}
    ends = {e for _, e, _, _ in spans}
    lexed = lex(texts)
    origin = []
    for k in range(len(texts)):
        doc_line = lines_at[lexed[k].body if lexed[k].body is not None else k][0]  # M:ORIGIN-OPENER
        if k in starts:
            origin.append(doc_line)
        origin.append(doc_line)
        if k in ends:
            origin.append(doc_line)
    return origin


def _kill_block(pidfile: str) -> None:
    try:
        with open(pidfile) as handle:
            os.killpg(int(handle.read().strip()), signal.SIGKILL)
    except (OSError, ValueError):
        pass


def _remove(root: str, parent: str, wt: str, admin: str | None) -> bool:
    _git(root, "worktree", "remove", "--force", wt)
    if admin and os.path.basename(os.path.dirname(admin)) == "worktrees" \
            and os.path.isdir(admin):  # M:OWN-ENTRY
        shutil.rmtree(admin, ignore_errors=True)
    shutil.rmtree(parent, ignore_errors=True)
    listed = _git(root, "worktree", "list", "--porcelain")
    return (listed.returncode == 0 and not os.path.lexists(parent)
            and f"worktree {wt}" not in listed.stdout.splitlines())


def certify(docs: list[str], sha: str, root: str, timeout: float) -> list[Screen]:
    if sha.startswith("-") or _git(root, "cat-file", "-t", sha).stdout.strip() != "commit":
        raise CannotJudge(f"not_a_commit sha={sha}")  # M:SHA-COMMIT
    prefix = _git(root, "rev-parse", "--show-prefix")
    if prefix.returncode != 0:
        raise CannotJudge("root_not_a_git_repository")
    blocks = []
    for doc in docs:
        try:
            text = Path(doc).read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError):
            raise CannotJudge(f"doc_unreadable doc={doc}")
        blocks.extend((doc, body) for body in shell_blocks(text) if body)
    tagged = [(screens_in(t), t) for t in ([line for _, line in body] for _, body in blocks)]
    if not any(spans or unparsed_in(texts, spans) for spans, texts in tagged):
        return []
    parent = os.path.realpath(tempfile.mkdtemp(prefix="hmad-expect-"))
    wt, pidfile = os.path.join(parent, "wt"), os.path.join(parent, "block.pid")
    screens, admin, removed = None, None, False
    try:
        if _git(root, "worktree", "add", "--detach", "--quiet", wt, sha).returncode != 0:
            raise CannotJudge("worktree_add_failed")
        found = _git(wt, "rev-parse", "--absolute-git-dir")
        admin = found.stdout.strip() if found.returncode == 0 else None
        screens = evaluate(blocks, os.path.join(wt, prefix.stdout.strip()), timeout, pidfile)
    except BaseException:
        _kill_block(pidfile)  # M:KILL-BLOCK
        raise
    finally:
        removed = _remove(root, parent, wt, admin)  # M:ALWAYS-REMOVE
    if not removed:
        raise CannotJudge(f"worktree_not_removed path={wt}")
    return screens


def _terminate(signum, frame):
    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, signal.SIG_IGN)  # cleanup must not be interrupted twice
    raise Terminated(signum)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("docs", nargs="+")
    parser.add_argument("--at", required=True)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--timeout", default="120")
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        print("EXPECT: CANNOT_JUDGE reason=usage")
        return 2
    for name in GIT_REDIRECTS:
        os.environ.pop(name, None)  # M:GIT-ENV
    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, _terminate)  # M:SIGNALS
    try:
        timeout = _validate_timeout(args.timeout)
        screens = certify(args.docs, args.at, args.project_root, timeout)
    except DocBlockError:
        print(f"EXPECT: CANNOT_JUDGE reason=bad_timeout value={args.timeout}")
        return 2
    except CannotJudge as error:
        print(f"EXPECT: CANNOT_JUDGE reason={error}")
        return 2
    except Terminated as error:
        print(f"EXPECT: CANNOT_JUDGE reason=terminated signal={error}")
        return 2
    except Exception as error:  # fail closed: an evaluation error never reads as PASS
        print(f"EXPECT: CANNOT_JUDGE reason=error detail={type(error).__name__}: {error}")
        return 2
    for s in screens:
        print(f"screen: {s.doc}:{s.line} expect={s.expect} got={s.got} {s.verdict}")
    if not screens:  # M:NONE-NOT-PASS
        print("EXPECT: NONE")
        print(COVERAGE)
        return 3
    unreadable = sum(s.got.startswith("UNREADABLE") for s in screens)
    failed = sum(s.verdict != "PASS" for s in screens) - unreadable
    if failed or unreadable:  # M:VERDICT
        print(f"EXPECT: FAIL screens={len(screens)} failed={failed} unreadable={unreadable}")
        code = 1
    else:
        print(f"EXPECT: PASS screens={len(screens)}")
        code = 0
    print(COVERAGE)
    return code


if __name__ == "__main__":
    sys.exit(main())
