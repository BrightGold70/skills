#!/usr/bin/env python3
"""h_mad_done_gate.py — verify an author's DONE line against the artifact on disk.

A subagent's "stopped writing" is an INSTANT, not a state. The orchestrator can
dispatch again after a `DONE` arrives — a `SendMessage`, a successor spawned on a
`Prompt is too long` notification — and the author resumes from its transcript and
keeps writing. So "the notification came back" is not evidence that the file the
author described is the file now on disk, and neither is the author's own prose.
The only durable proof is a digest the author computed over the finished artifact
and the orchestrator re-derives with the same command.

That protocol existed for five live dispatches (`spec-author` x1, `design-author`
x2, `implplan-author` x1, `plan-author` x1) and five for five matched — but it
lived only in hand-written dispatch prompts. Nothing in `agents/*.md` required it
and nothing in `SKILL.md` gated on it, so the next orchestrator to skip it would
have skipped it silently. Echoing the sha into the log is not a gate; the gate is
this script's token, read and acted on.

Verdicts, printed as a canonical token:

    DONEGATE: PASS path=<p> sha256=<hex> lines_check=ok|disagree|absent    exit 0
    DONEGATE: FAIL reason=<r> ...                                          exit 1
    DONEGATE: UNREADABLE reason=<r> ...                                    exit 2

**Read the token, never `$?`** — and note that `$?` is doubly wrong here: `set -e`
is inert in the Bash tool's top-level shell (measured), so a bare invocation whose
exit is 1 falls through to the next command and the orchestrator commits an
artifact the gate refused. Every call site spells the gate `|| exit 1`.

`lines=` never gates. `wc -l` counts newlines, so an artifact with no trailing
newline reads one short — a units trap, and a units trap that fails the build is
worse than one that is merely reported. A matching `sha256` already proves the
file is byte-identical to what the author hashed, which is the whole claim;
`lines_check=disagree` beside a PASS means the author miscounted, not that the
artifact moved.

The three verdicts partition on WHO the failure belongs to:

  * `FAIL` — the claim is refuted. The line is malformed, is not first, names a
    path that is not there, or carries a sha the artifact does not have. Every one
    of these is a statement about the author's report, which is what is being
    gated.
  * `UNREADABLE` — the gate could not judge. The message file is missing, or the
    artifact exists and cannot be read. A cannot-judge that exits 1 is
    indistinguishable from a refutation, and the caller would "fix" the wrong
    thing (`invariants.base.md` §"Audit-gate signal discipline").
  * A missing artifact is deliberately `FAIL`, not `UNREADABLE`: the author
    asserted a file with that digest exists. Absence refutes the assertion — it is
    not the gate failing to look.

Stdlib-only.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

# `<ROLE>: DONE ` — the four authors and the auditor all emit this shape. Anchored
# at the start of the line so a DONE quoted mid-sentence in a report body cannot be
# mistaken for the contract line.
DONE_RE = re.compile(r"^(?P<role>[A-Z][A-Z-]*): DONE\b(?P<rest>.*)$")

# Values run to the next space. No path in this repo's document trees contains one,
# and accepting spaces would make `path=` swallow `lines=` on a malformed line —
# turning a malformed report into a confident wrong answer.
FIELD_RE = re.compile(r"(?P<key>[A-Za-z0-9_]+)=(?P<value>\S*)")

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class Unreadable(Exception):
    """The gate could not judge — never a verdict about the author."""


def _emit(token: str, code: int) -> int:
    print(token)
    return code


def find_done_line(text: str) -> tuple[str, str]:
    """`(role, rest)` for the DONE line, which must be the FIRST non-blank line.

    DONE-first is itself a contract (`SKILL.md` §"Teammate authors" rule 4): four
    r17 reports were truncated before a trailing DONE and read as unfinished. A
    gate that accepts a DONE anywhere in the message re-opens that hole, because a
    trailing DONE that survived truncation *this* time still says nothing about
    the next report.
    """
    first_nonblank: str | None = None
    found: tuple[str, str] | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if first_nonblank is None:
            first_nonblank = line
        m = DONE_RE.match(line)
        if m and found is None:
            found = (m.group("role"), m.group("rest"))
            break
    if found is None:
        raise ValueError("no_done_line")
    if DONE_RE.match(first_nonblank or "") is None:
        raise ValueError("done_line_not_first")
    return found


def parse_fields(rest: str) -> dict[str, str]:
    return {m.group("key"): m.group("value") for m in FIELD_RE.finditer(rest)}


def digest(path: Path) -> tuple[str, int]:
    """`(sha256, line count)` for `path`, or raise `Unreadable`.

    Read as BYTES and count `b"\\n"`, matching `wc -l` exactly. Decoding to text
    first would make the count depend on the platform's newline translation and on
    the file being valid UTF-8 — two ways for the gate's number to differ from the
    author's for reasons that have nothing to do with whether the file moved.
    """
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise Unreadable(f"artifact_unreadable detail={exc.__class__.__name__}") from exc
    return hashlib.sha256(data).hexdigest(), data.count(b"\n")


def run(message: str, repo: Path, expect_path: str | None) -> tuple[str, int]:
    try:
        _role, rest = find_done_line(message)  # role is not gated: any of the five may answer
    except ValueError as exc:
        return f"DONEGATE: FAIL reason={exc}", 1

    fields = parse_fields(rest)

    reported_path = fields.get("path")
    if not reported_path:
        return "DONEGATE: FAIL reason=no_path_field", 1

    reported_sha = fields.get("sha256")
    if not reported_sha:
        return f"DONEGATE: FAIL reason=no_sha_field path={reported_path}", 1
    if not SHA256_RE.match(reported_sha):
        return (f"DONEGATE: FAIL reason=malformed_sha path={reported_path} "
                f"reported={reported_sha}"), 1

    # The path check is not redundant with the sha check, and it is the half that
    # catches the likelier mistake: an author that hashes the WRONG file reports a
    # digest that verifies perfectly against the file it named. Only comparing
    # against the document the orchestrator dispatched for can see that.
    if expect_path is not None:
        want = (repo / expect_path).resolve()
        got = (repo / reported_path).resolve()
        if want != got:
            return (f"DONEGATE: FAIL reason=path_mismatch reported={reported_path} "
                    f"expected={expect_path}"), 1

    artifact = repo / reported_path
    if not artifact.exists():
        return f"DONEGATE: FAIL reason=artifact_absent path={reported_path}", 1

    try:
        actual_sha, actual_lines = digest(artifact)
    except Unreadable as exc:
        return f"DONEGATE: UNREADABLE reason={exc} path={reported_path}", 2

    if actual_sha != reported_sha:
        return (f"DONEGATE: FAIL reason=sha_mismatch path={reported_path} "
                f"reported={reported_sha} actual={actual_sha}"), 1

    reported_lines = fields.get("lines")
    if reported_lines is None:
        lines_check = "absent"
    elif reported_lines.isdigit() and int(reported_lines) == actual_lines:
        lines_check = "ok"
    else:
        lines_check = "disagree"

    return (f"DONEGATE: PASS path={reported_path} sha256={actual_sha} "
            f"lines_check={lines_check} lines={actual_lines}"), 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="verify an author's DONE line against the artifact on disk")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--done-line", help="the author's DONE line, verbatim")
    src.add_argument("--message-file",
                     help="file holding the author's final message; the DONE line "
                          "must be its first non-blank line")
    ap.add_argument("--repo", default=".",
                    help="root that a relative `path=` is resolved against")
    ap.add_argument("--expect-path",
                    help="the document this dispatch was for; when given, `path=` "
                         "must name it")
    args = ap.parse_args(argv)

    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        return _emit(f"DONEGATE: UNREADABLE reason=repo_absent repo={args.repo}", 2)

    if args.message_file is not None:
        mf = Path(args.message_file)
        try:
            message = mf.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return _emit(f"DONEGATE: UNREADABLE reason=message_file_unreadable "
                         f"path={args.message_file}", 2)
        if not message.strip():
            return _emit(f"DONEGATE: UNREADABLE reason=message_file_empty "
                         f"path={args.message_file}", 2)
    else:
        message = args.done_line

    token, code = run(message, repo, args.expect_path)
    return _emit(token, code)


if __name__ == "__main__":
    sys.exit(main())
