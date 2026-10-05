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
an unquoted `\\`; a line whose code (comment stripped) ends in `|`, `&&` or
`|&`, across any blank or comment-only lines after it; a quoted string that
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
repository. Blocks read stdin from /dev/null. When ROOT is a subdirectory of its
repository, screens run in the same subdirectory of the worktree. Residual: a
statement that leaves the worktree by absolute path (`cd /abs`, `git -C /abs`)
reads that tree, not the sha.

How a reading is taken. Each qualifying block runs ONCE (non-strict bash, so a
grep that matches nothing does not end the block), via `run_block`, with marker
lines inserted around each screen so its stdout is captured alone and every
earlier line still runs to define variables. An ERR trap with `set -E`
(errtrace, so it also fires in function bodies, subshells and command
substitutions, writing to one file), disarmed inside screens, records every
earlier command that failed: a non-zero status of an assignment from a command
substitution -- except status 1 when the substitution's last command is a grep,
which is its no-match -- of `cd`, `pushd`, `popd`, `source` or `.`, and a
status >= 2 of anything else. An env-prefixed command (`LC_ALL=C grep …`) is a
command, not an assignment. A screen is
UNREADABLE -- never PASS -- when such a failure precedes it
(`failed_command=<doc>:<line>:<status>`), its markers are missing, repeated or
mangled (the block died, or the screen sits in a loop), any member of its
pipeline exited >= 2 (the error-reads-as-zero class: `grep x missing | wc -l`
prints 0), its trimmed stdout is empty or not one integer, or the block timed out
or could not launch. Residuals: a non-assignment that fails with status 1 (`cat`
on a missing file) is indistinguishable from grep's no-match, at the top level, in
a function or inside a substitution; `export X=$(cmd)` exits 0 in bash itself;
and a failing command earlier on the screen's own line
(`false; echo 0   # expect 0`) is not seen. The trap is
disarmed inside screens because bash 3.2 reports a partial PIPESTATUS to it and
leaves its own PIPESTATUS behind.

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
import os
import re
import secrets
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from h_mad_doc_block_exec import (  # noqa: E402
    Block, BlockTimeout, DocBlockError, _fence_events, _validate_timeout, run_block,
)

SCREEN = re.compile(r"#[ \t]*expect[ \t]+(-?\d+)[ \t]*(?:$|[,;(]|--|—)")
RAW_SCREEN = re.compile(r"(?:^|[ \t;&|()<>])" + SCREEN.pattern)
HEREDOC = re.compile(r"<<(-?)[ \t]*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\2")
INTEGER = re.compile(r"-?\d+")
GIT_REDIRECTS = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR",
                 "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE")
COVERAGE = ("coverage: only statements ending in a '# expect <N>' comment inside a bash/sh "
            "fence are screened; expectations stated in prose or untagged commands are not run; "
            "a statement that leaves the worktree by absolute path reads that tree, not the sha")
# The ERR trap's classifier. `case`, not `[[ =~ ]]`: bash 3.2 never matched `=~` inside an
# ERR trap. Failures go to a file, not a variable, so a function body, subshell or command
# substitution (reached through `set -E`) records into the same list as the top level.
FAIL_FN = """__hmad_fail() {
  local r=$1 c=$2 at=$3 n t k=0
  case "$c" in *=*)
    n=${c%%=*}
    case "$n" in ""|[0-9]*|*[!A-Za-z0-9_]*) ;; *)
      case "$c" in
        "$n="'$('*')'|"$n="'"$('*')"')
          k=1; t=${c#*\\$(}; t=${t##*|}; t=${t#"${t%%[![:space:]]*}"}  # M:SUBST-ASSIGN
          case "$t" in grep*|egrep*|fgrep*) if [ "$r" = 1 ]; then k=0; fi;; esac;;  # M:GREP-NOMATCH
        "$n="*[[:space:]]*) ;;  # M:ENV-PREFIX: `VAR=x cmd` is a command, not an assignment
        *) k=1;;
      esac;;
    esac;;
  esac
  case "$c" in cd|cd[[:space:]]*|pushd|pushd[[:space:]]*|popd|popd[[:space:]]*|source[[:space:]]*|.[[:space:]]*) k=1;; esac
  if [ "$k" = 1 ] || [ "$r" -ge 2 ]; then echo "$at:$r" >> "$__hmad_ff"; fi  # M:TRAP-RULE
}"""
TRAP = '__hmad_fail $? "$BASH_COMMAND" $((LINENO - __hmad_l0 - 1))'


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


def lex(texts: list[str]) -> list[Line]:
    """Quote, comment and here-document structure of one block, line by line."""
    lines = [Line(t) for t in texts]
    quote, pending, current = None, [], None
    for i, info in enumerate(lines):
        text = info.text
        if current is not None:
            delim, tabs, opener = current
            info.body = opener
            if (text.lstrip("\t") if tabs else text) == delim:
                lines[opener].heredoc_end = i
                current = pending.pop(0) if pending else None
            continue  # M:HEREDOC-BODY: a body line has no code and no comment
        info.quoted = quote is not None
        cut, k, arith = len(text), 0, 0
        while k < len(text):
            ch = text[k]
            if quote == "'":
                quote = None if ch == "'" else quote
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
            elif (text.startswith("<<", k) and not arith  # M:ARITH-NOT-HEREDOC
                  and not text.startswith("<<<", k) and text[k - 1:k] != "<"):
                match = HEREDOC.match(text, k)  # only unquoted code reaches here
                if match:
                    pending.append((match.group(3), match.group(1) == "-", i))
                    k = match.end()
                    continue
            elif ch == "#" and (k == 0 or text[k - 1] in " \t;&|()<>"):  # M:COMMENT-UNQUOTED
                cut = k
                break
            k += 1
        info.code, info.comment = text[:cut], text[cut:]
        if quote is None:
            info.backslash = (not info.comment
                              and (len(text) - len(text.rstrip("\\"))) % 2 == 1)
            info.op = info.code.rstrip().endswith(("|", "&&", "|&"))  # M:CONT-OP-CODE
            if current is None and pending:
                current = pending.pop(0)
    for _, _, opener in ([current] if current else []) + pending:
        lines[opener].heredoc_end = len(lines) - 1
    return lines


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
            out.append(f"trap - ERR; printf '\\n%s\\n' 'HMADB_{nonce}_{starts[k]}'")
        out.append(line)
        if k in ends:
            out.append(f"__hmad_ps=\"${{PIPESTATUS[*]}}\"; "
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
        FAIL_FN,
        "set -E",  # M:ERRTRACE: the trap also fires inside function bodies
        f"__hmad_trap={shlex.quote(TRAP)}",
        'trap "$__hmad_trap" ERR',  # M:TRAP-ARMED
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
    return screens


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
