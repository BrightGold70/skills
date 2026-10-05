#!/usr/bin/env python3
"""Stage one ADVISORY `doc-auditor` delta review per phase (SKILL.md §"Delta self-review").

The delta review was dispatched by hand six times across two rounds, identical shape
each time: one `doc-auditor` per phase, subject `git show <sha> -- <doc>` plus the
audit reports that revision answered, and a report named OUTSIDE the audit filename
grammar so it cannot join the codex-leg ledger. It found fix-introduced musts in 3
of 3 passes at roughly a quarter of a gating round's cost. The naming constraint was
the part left to the caller's memory, and a delta report named `….v4.md` would be
counted as an audit cycle by every consumer of `h_mad_cycle_counts._VERSION_RE`.

So this script MINTS the report name and there is no flag to override it: minting it
is the enforcement. The tag is `<sha7>-<UTC yyyymmddTHHMMSSZ>` and never `vN`,
because `_VERSION_RE` matches `….v1.1.md`. The minted name is then checked against
the ledger's own selectors, IMPORTED rather than copied so the check follows the
grammar if it widens; a match is `name_in_audit_grammar` and nothing is staged.

What it does NOT do is dispatch. It stages the dispatch (claims the paths, writes the
prompt file) and prints the exact `Agent(...)` call; issuing it stays the
orchestrator's, by design.

Order is everything-then-anything: every check runs before the first claim, and a
check that cannot be EVALUATED (git fails, a file cannot be read) halts like a check
that failed. Report and prompt paths are claimed once with the assembler's
machinery (`$XDG_CACHE_HOME/h-mad/handed`) and never re-handed (#49o).

Usage:
  h_mad_delta_stage.py --feature F --project-root ROOT --sha SHA \\
      --phase plan [--phase design ...] --answers REPORT [--answers REPORT ...]

Prints `DELTA-STAGE: STAGED phase=<p> report=<path> prompt=<path>` plus the
`Agent(...)` call per phase and exits 0; `DELTA-STAGE: HALT <what>:<reason>` lines
and exit 3 when anything is refused (nothing claimed, nothing written -- except
`prompt:unwritable`, which removes what it wrote but may leave `docs/03-analysis`
created); exit 2 on a usage error. Stdlib only.
"""
from __future__ import annotations

import argparse
import os
import re
import stat
import subprocess
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import h_mad_assemble_audit as aa
import h_mad_audit_gate as ag
import h_mad_cycle_counts as cc

PHASES = ("spec", "plan", "design", "impl-plan")
STAGE_HALT = 3
# A feature name reaches a pathspec, a prompt line and a quoted Agent(prompt: "...")
# string, so it is held to the names features actually have: no whitespace, quote,
# glob or control character can split a line or widen a match. `fullmatch`, because
# `$` also matches before a trailing newline.
_FEATURE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
# Every value the prompt interpolates is one line of a `KEY=value` dispatch the auditor
# reads: a newline in an --answers path wrote a second, column-0 `REPORT=` and steered
# the report back INTO the audit grammar. So control characters are refused as a CLASS
# -- C0/C1/DEL (Cc) and the Unicode line/paragraph separators (Zl, Zp) -- not only `\n`.
_CONTROL_CATEGORIES = ("Cc", "Zl", "Zp")


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args],
                          capture_output=True, text=True)


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _report_name(feature: str, phase: str, sha7: str, stamp: str) -> str:
    return f"{feature}.{phase}.delta-review.{sha7}-{stamp}.md"  # M:DSTAGE-NAME


def in_audit_grammar(name: str) -> bool:
    """Would any audit-ledger selector read `name` as an audit report?

    Module attributes are read at CALL time, so a widened grammar is honoured here
    without an edit. `_STAMP_NAME_RE` is tested against the name's gate stamp; today
    every name it accepts is also caught by the other two, and it is kept so a stamp
    grammar that drops `.audit.` is still followed.
    """
    return bool(cc._VERSION_RE.search(name)  # M:DSTAGE-GRAMMAR-VERSION
                or ag._STAMP_NAME_RE.match(name + ag.STAMP_SUFFIX)  # M:DSTAGE-GRAMMAR-STAMP
                or ".audit." in name)  # M:DSTAGE-GRAMMAR-AUDIT


def _has_control(value: str) -> bool:
    return any(unicodedata.category(c) in _CONTROL_CATEGORIES  # M:DSTAGE-CONTROL
               for c in value)


def _check_answers(path: str) -> str | None:
    """None when `path` is a readable non-empty regular file, else the HALT reason.

    A FIFO (or a device) passes `open()` and then blocks on the read, so the kind is
    checked first: a stage that hangs is not a HALT.
    """
    try:
        st = os.stat(path)
    except (FileNotFoundError, NotADirectoryError):
        return "missing"
    except OSError:
        return "unreadable"
    if not stat.S_ISREG(st.st_mode):  # M:DSTAGE-ANSWERS-REGULAR
        return "not_a_file"
    try:
        with open(path, "rb") as f:
            head = f.read(1)
    except OSError:  # M:DSTAGE-ANSWERS-FAILCLOSED
        return "unreadable"
    return None if head else "empty"  # M:DSTAGE-ANSWERS-EMPTY


def _resolve_commit(root: Path, sha: str) -> tuple[str | None, str | None]:
    """`(full_sha, None)` or `(None, halt_reason)`."""
    try:
        kind = _git(root, "cat-file", "-t", sha)
        if kind.returncode != 0:
            return None, "unresolvable"
        if kind.stdout.strip() != "commit":  # M:DSTAGE-COMMIT
            return None, "not_a_commit"
        full = _git(root, "rev-parse", "--verify", f"{sha}^{{commit}}")
    except OSError:
        return None, "unresolvable"
    if full.returncode != 0 or not full.stdout.strip():
        return None, "unresolvable"
    return full.stdout.strip(), None


def _touched(root: Path, sha: str, rel: str) -> str | None:
    """None when `sha` changed `rel`, else the HALT reason. Never passes on an error.

    `:(literal)`: a bare `-- <rel>` is a PATHSPEC, so a `*` in it matched a changed
    sibling and an untouched document read as changed.
    """
    try:
        show = _git(root, "show", "--format=", "--no-color", "--no-ext-diff",
                    sha, "--", f":(literal){rel}")  # M:DSTAGE-LITERAL
    except OSError:
        return "git_error"
    if show.returncode != 0:  # M:DSTAGE-SHOW-RC
        return "git_error"
    return None if show.stdout.strip() else "unchanged"  # M:DSTAGE-UNCHANGED


def _prompt_text(*, root: Path, report: str, sha: str, rel: str, phase: str,
                 feature: str, answers: list[str]) -> str:
    listed = "\n".join(f"  - {a}" for a in answers)
    return (
        "PROMPT=<none — a delta review has no assembled prompt; your subject is below>\n"
        f"PROJECT_ROOT={root}\n"
        f"REPORT={report}\n"
        "This pass is ADVISORY.\n"
        "\n"
        f"Subject ({feature}, phase {phase}): `git show {sha} -- {rel}` — run it in "
        "PROJECT_ROOT — and the findings that revision answers:\n"
        f"{listed}\n"
        "\n"
        "For each hunk: does it close the finding it claims, or only the instance the "
        "reviewer named?\n"
        "Did it break a claim elsewhere in this document or in a sibling — a count, a "
        "cross-reference, a value stated in more than one place?\n"
        "\n"
        "Write your report at REPORT exactly. Its name is deliberately outside the audit "
        "filename grammar (`<feature>.<phase>.audit.v<N>[.<token>].md`) so it never joins "
        "the audit ledger — do not rename it into that grammar.\n"
    )


def _halt(lines: list[str],
          footer: str = "nothing was claimed and nothing was written.") -> int:
    for line in lines:
        print(f"DELTA-STAGE: HALT {line}")
    print(f"  - {footer}")
    return STAGE_HALT


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--feature", required=True)
    ap.add_argument("--project-root", required=True, type=Path)
    ap.add_argument("--sha", required=True, help="the revision under review")
    ap.add_argument("--phase", required=True, action="append", choices=PHASES,
                    help="repeatable; one delta review is staged per phase")
    ap.add_argument("--answers", required=True, action="append", metavar="PATH",
                    help="an audit report this revision answers (repeatable, >=1)")
    args = ap.parse_args(argv)

    # Before every other check, so a tainted value never reaches a HALT line raw
    # (`!r` below) and nothing is claimed: a refusal, exit 3, like any other HALT.
    raw = ([("feature", args.feature), ("sha", args.sha),
            ("project-root", str(args.project_root))]
           + [("answers", a) for a in args.answers])  # M:DSTAGE-CONTROL-ARGS
    tainted = [f"{name}:control_char value={value!r}" for name, value in raw
               if _has_control(value)]
    if tainted:  # M:DSTAGE-CONTROL-HALT
        return _halt(tainted)

    if len(set(args.phase)) != len(args.phase):  # M:DSTAGE-DUP-PHASE
        ap.error("--phase given twice for one phase")
    if not _FEATURE_RE.fullmatch(args.feature):  # M:DSTAGE-FEATURE
        ap.error("--feature must match [A-Za-z0-9][A-Za-z0-9._-]* (no whitespace, "
                 "quote, glob, '/' or control character)")
    if not args.project_root.is_dir():
        ap.error(f"--project-root {args.project_root} is not a directory")
    root = Path(os.path.abspath(args.project_root))
    answers = [os.path.abspath(a) for a in args.answers]

    # 1. Validate everything. No side effects until every check has passed.
    halts: list[str] = []
    sha, why = _resolve_commit(root, args.sha)
    if why:
        halts.append(f"sha:{why} sha={args.sha}")
    docs: dict[str, str] = {}
    for phase in args.phase:
        doc = aa.doc_path(args.feature, phase, root)
        rel = os.path.relpath(doc, root)
        docs[phase] = rel
        if not doc.is_file():
            halts.append(f"{phase}:doc_missing path={doc}")
        elif sha and (why := _touched(root, sha, rel)):
            halts.append(f"{phase}:{why} sha={args.sha} path={rel}")
    for path in answers:
        if why := _check_answers(path):
            halts.append(f"answers:{why} path={path}")
    if halts:  # steps 2-4 need a resolved sha
        return _halt(halts)

    # 2. Mint, self-check against the ledger grammar, and measure freshness.
    stamp = _utc_stamp()
    analysis = root / "docs" / "03-analysis"
    staged: list[tuple[str, str, str]] = []
    for phase in args.phase:
        name = _report_name(args.feature, phase, sha[:7], stamp)
        report = str(analysis / name)
        prompt = str(aa._default_out(report))
        if _has_control(report) or _has_control(prompt):  # M:DSTAGE-CONTROL-MINTED
            halts.append(f"{phase}:control_char path={report!r}")
            continue
        if in_audit_grammar(name):  # M:DSTAGE-GRAMMAR
            halts.append(f"{phase}:name_in_audit_grammar name={name}")
            continue
        try:
            held = next((p for p in (report, prompt) if aa._present(p)), None)  # M:DSTAGE-FRESH
        except OSError as exc:
            halts.append(f"{phase}:report_path_unreadable path={report} ({exc})")
            continue
        if held:
            halts.append(f"{phase}:report_path_handed path={report} held={held}")
            continue
        staged.append((phase, report, prompt))
    if halts:  # M:DSTAGE-MINT-HALTS
        return _halt(halts)

    # 3. Claim every path, or none: a refused claim releases what THIS run just took
    #    (those names are fresh, so nobody else was handed them) and deletes nothing else.
    taken: list[str] = []

    def release() -> None:
        for path in taken:
            aa._marker(path).unlink(missing_ok=True)  # M:DSTAGE-RELEASE

    line = f"{stamp} delta-stage feature={args.feature} sha={sha}"
    for phase, report, prompt in staged:
        for path in (report, prompt):  # M:DSTAGE-CLAIM-BOTH
            try:
                claimed = aa._claim(path, f"{line} phase={phase} path={path}\n")
            except OSError as exc:
                release()  # M:DSTAGE-RELEASE-MARKER
                return _halt([f"{phase}:report_path_marker_unwritable path={path} ({exc})"])
            if not claimed:  # M:DSTAGE-HELD
                release()
                return _halt([f"{phase}:report_path_handed path={report} held={path}"])
            taken.append(path)

    # 4. Write the prompts, exclusively. A failure undoes this run's own work only.
    written: list[str] = []
    try:
        analysis.mkdir(parents=True, exist_ok=True)
        for phase, report, prompt in staged:
            text = _prompt_text(root=root, report=report, sha=sha, rel=docs[phase],
                                phase=phase, feature=args.feature, answers=answers)
            with open(prompt, "x", encoding="utf-8") as f:
                written.append(prompt)
                f.write(text)
    except (OSError, ValueError) as exc:  # M:DSTAGE-WRITE-ERRORS
        # ValueError: UnicodeEncodeError from a surrogate-escaped (non-UTF-8) path.
        for path in written:
            Path(path).unlink(missing_ok=True)  # M:DSTAGE-UNLINK-WRITTEN
        release()  # M:DSTAGE-RELEASE-WRITE
        return _halt([f"prompt:unwritable ({exc})"],
                      footer="this run's prompt files and claims were removed; "
                             f"{analysis} may have been created and left empty.")

    for phase, report, prompt in staged:
        print(f"DELTA-STAGE: STAGED phase={phase} report={report} prompt={prompt}")
        print(f'Agent(subagent_type: "doc-auditor", prompt: "Read {prompt} and follow it '
              f'exactly. It is an ADVISORY delta review of {args.feature} {phase} at '
              f'{sha[:7]}; write your report at {report} and nowhere else.")')
    print(f"[H-MAD] delta-stage STAGED phases={len(staged)} sha={sha[:7]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
