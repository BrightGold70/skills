#!/usr/bin/env python3
"""h_mad_guard_census.py — list the decision lines a diff adds or changes that no mutation row anchors.

A `# M:` marker census cannot see an unmarked arm, and hand-built diff censuses
took two Phase 6 rounds and found 16 and then 2 verdict-deciding lines that a
marker count had read as none. This enumerates the candidates mechanically; WHICH
of them is a real guard is a reviewer's call, so the tool never says PASS on
guards. It lists candidates and counts them.

    h_mad_guard_census.py --base <ref> [--head <ref>] [--spec-dir DIR ...]
                          [--path P ...] [--repo DIR]

    <file>:<line>\\t<kind>\\t<note>\\t<text>   one per UNANCHORED candidate
    REMOVED: <file>:<line> <kind> "<text>"       one per decision line the head no longer has
    UNPARSED-BASE: <file>                        a base side that could not be read (not a guard)
    GUARD-CENSUS: DONE decision=<n> anchored=<m> unanchored=<k> removed=<r> unparsed_base=<u>
    GUARD-CENSUS: UNREADABLE reason=<reason>

exit 0 on DONE (even with candidates: the tool measures, it does not judge), 2 on
UNREADABLE. The UNREADABLE line carries no counts, because a zero would be
byte-identical to "nothing was measured". Read the token, never `$?`.
`decision` is always `anchored + unanchored`; `removed` and `unparsed_base` are counted apart.

What is compared. Everything is read from git objects, never the working tree:
every entry of `git diff <base> <head>`, each side read by its own mode and blob
(`--path` narrows it, repeatable; `.`, `./` and the repo top name everything; a
`--path` that matches no change, or lies outside the repo, is UNREADABLE, never a zero) and the spec directories as they stand at `--head`
(default HEAD). `--spec-dir` is repeatable and repo-relative; the default is
`h-mad/tests/mutation-specs` AND `handoff/tests/mutation-specs`, of which one may
be absent. An explicit `--spec-dir` replaces the default and must exist.

Entries that are not measured, each counted ONCE on `SKIPPED:` (the counters are
disjoint; a measured file is never counted there): `binary` (a binary change),
`tests` (a `tests`/`test` directory component, `test_*.py`, `*_test.py`,
`conftest.py`: not census targets), `link` (a symlink or gitlink on every side
that exists; a deleted symlink or gitlink, or one changed to a file, is never
read as source), `unmeasured` (see Language), `other` (documents and data from
the allow-list below). `CENSUS-SCOPE:` gives `files=` (measured entries) and
`deleted=` (how many of those are deletions).

Language, read PER SIDE from that side's own blob (a script that was bash and is
now python is read as shell on the base and python on the head). `.py`, or a `#!`
python script of any name, is Python; `.sh .bash .zsh .ksh`, or any file with a
`#!` shell shebang (`gate.v2`), is shell. Fail closed: only an allow-list of
documents and data (`DOC_SUFFIXES`, `DOC_NAMES` in the source: `.md .json .txt
.log .csv .xsd .png ...`, `LICENSE`, `rc`) is `other`; EVERYTHING else (`.ts .vue
.pyw .r`, an unknown suffix, `Makefile`, any other `#!`) is `unmeasured`, counted
on `SKIPPED:` and listed as `UNMEASURED: <file>`. An entry with one measured
side and one unmeasured side is measured and also counted unmeasured.

Decision lines in Python (`ast`; the unit is a statement, reported at its first
line, and it counts when any physical line of it is added or changed). For a
compound statement only the header counts, its body statements are their own:
  * `if` / `elif` (kind `if`, `elif`), `while`, `for`, `except`, `match` / `case`
  * `return`, `raise`, `assert`, `continue`, `break`
  * a `with` / `async with` header (a context manager can refuse)
  * any assignment (`=`, `+=`, annotated), and a call used as a statement
    (`result.append(...)`, `await deny(x)`), because the lines that moved a verdict in the
    calibration were transports and recordings, not only conditions
  * the kind also names conditional forms inside the statement: `ifexp`,
    `comp-if`, `boolop`
Not decisions: imports, `def`/`class` headers, decorators, `pass`, `global`,
docstrings and other bare expressions. An unanchored statement whose nearest
enclosing branch header is itself anchored is annotated `arm-of-anchored:<line>`
(and counted on the `ARMS:` line); it stays a candidate, because an arm can
matter on its own. Only non-header statements are annotated: an `elif`, a
nested `if` or a loop is a decision of its own and never an arm.

Decision lines in a shell hook (see Language). The unit is the physical line; blank lines,
comments, bare `then do else fi done esac { } ;;` and function headers are not.
A line counts when it:
  * starts a control command: `if elif while until for case select`
  * contains a test, `[ ... ]` or `[[ ... ]]`, or `&&` / `||`
  * is a case arm (`pattern)` at the end of the line, or contains `;;`)
  * runs `return`, `exit`, `break` or `continue` as a command
  * is an assignment (`NAME=…`, `NAME[i]=…`, after `local`/`export`/…)
  * calls a verdict helper: a command named like `_refuse`, `_allow`, `_deny`,
    `_block`, `_die`, `_fail`
The match is naive about quotes and heredocs. A plain command call
(`_read_listing`) is not a decision line.

Anchored. A line is anchored when a mutation row in a spec whose resolved `file`
is that file has a `find` that occurs EXACTLY ONCE in the file and whose span
overlaps the line. A `find` that occurs twice or not at all anchors nothing (a
mutant that cannot be applied proves nothing) and is counted on the `ROWS:` line.
A `# M:` marker with no row anchors nothing; that is the blind spot this closes.
A shell line with several `;;` case arms is anchored only if every arm is
overlapped, since a row on one arm says nothing about the others.

Removed lines. A guard deleted from a modified file adds nothing to the head, so
the base side is read too: every decision line (same rule, parsed from the base
blob) on a line the hunk removes or rewrites is listed as `REMOVED:` with its
BASE line number. A rewritten decision line is therefore both a candidate and a
`REMOVED` line. A deleted file, or a file whose head is no longer code (python
that became data or a symlink), lists all its decision lines. A rename is read as
delete plus add (`--no-renames`): the old file's lines are `REMOVED` and the new
file's are candidates. REMOVED lines are never "anchored"; the code is gone. A base
side that cannot be read (not UTF-8, does not parse) never ran a guard, so it does not
lose the census: it is listed as `UNPARSED-BASE:` and counted as `unparsed_base=`.
An unreadable HEAD side stays UNREADABLE.

Line numbers are git's (LF-counted). `ast` also counts a bare CR as a newline, so
statement lines are mapped through character offsets.

Limits, stated so they are not read as coverage: a row's `find` overlapping a
line does not prove the row kills a mutant of every decision on it; a mutant
that moves only a reason string is a candidate here; and a spec whose `root` is
absolute and outside the repository cannot be mapped, and is counted as `outside`.

UNREADABLE reasons: `git` (git fails or is absent), `bad-ref`, `spec-dir`
(missing from the head tree, or outside the repository), `spec-unreadable` (not
JSON, not UTF-8, or a row without string `file`/`find`), `unreadable-file`
(a measured HEAD side is not UTF-8 or does not parse), `path-no-match`.

Stdlib-only.
"""
from __future__ import annotations

import argparse
import ast
import bisect
import json
import os
import posixpath
import re
import subprocess
import sys
import tokenize
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

TOKEN = "GUARD-CENSUS"
DEFAULT_SPEC_DIRS = ("h-mad/tests/mutation-specs", "handoff/tests/mutation-specs")
SHELL_SUFFIXES = (".sh", ".bash", ".zsh", ".ksh")
PY_HEAD = re.compile(rb"^#!\s*(?:\S*/)?(?:env\s+(?:-\S+\s+)*)?python[\d.]*\b")
# Fail closed: only these are documents or data. Everything else that is not Python or shell
# is `unmeasured`, so a new language shows up as a count, never as a document.
DOC_SUFFIXES = {".md", ".markdown", ".rst", ".txt", ".json", ".jsonl", ".ndjson", ".yaml", ".yml",
                ".toml", ".ini", ".cfg", ".conf", ".csv", ".tsv", ".lock", ".log", ".out", ".stdout",
                ".stderr", ".xsd", ".xml", ".html", ".htm", ".css", ".svg", ".png", ".jpg", ".jpeg",
                ".gif", ".ico", ".icns", ".pdf", ".tex", ".sty", ".bib", ".patch", ".diff", ".plist",
                ".canvas", ".dot", ".mplstyle", ".gz", ".zip", ".docx", ".xlsx", ".pptx", ".pbtxt",
                ".sample", ".example", ".backup", ".original", ".pending", ".wall", ".zh",
                ".sha_before", ".sha_after", ".enl", ".ris", ".rtf"}
DOC_NAMES = {"LICENSE", "README", "NOTICE", "CHANGELOG", "AUTHORS", ".gitignore", ".gitattributes",
             ".gitmodules", ".gitkeep", ".ignore", ".DS_Store", "rc", "stdout", "stderr"}
SHELL_HEAD = re.compile(rb"^#!\s*(?:\S*/)?(?:env\s+(?:-\S+\s+)*)?(?:ba|z|da|k)?sh\b")
# A branch header is a decision of its own, never an "arm" that an outer row speaks for.
HEADERS = {"if", "elif", "while", "for", "except", "match", "case"}
HUNK = re.compile(rb"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


class Unreadable(Exception):
    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(reason)
        self.reason = reason
        self.detail = detail


# ---------------------------------------------------------------- git access

def _git(top: Path, *args: str, stdin: bytes | None = None) -> bytes:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    try:
        proc = subprocess.run(["git", "--literal-pathspecs", "-C", str(top), *args],
                              input=stdin, capture_output=True, env=env, check=False)
    except OSError as exc:
        raise Unreadable("git", f"cannot run git: {exc}") from exc
    if proc.returncode != 0:
        raise Unreadable("git", proc.stderr.decode("utf-8", "replace").strip()[:300])
    return proc.stdout


def _toplevel(repo: Path) -> Path:
    if not repo.is_dir():
        raise Unreadable("git", f"not a directory: {repo}")
    return Path(_git(repo, "rev-parse", "--show-toplevel").decode("utf-8", "replace").strip())


def _commit(top: Path, ref: str) -> str:
    try:
        return _git(top, "rev-parse", "--verify", "--quiet",
                    f"{ref}^{{commit}}").decode().strip()
    except Unreadable as exc:
        raise Unreadable("bad-ref", f"not a commit: {ref!r}") from exc


def _blobs(top: Path, shas: list[str]) -> dict[str, bytes]:
    """Blob contents by sha, through one `git cat-file --batch`."""
    out = _git(top, "cat-file", "--batch", stdin="".join(s + "\n" for s in shas).encode())
    result: dict[str, bytes] = {}
    pos = 0
    for sha in shas:
        end = out.index(b"\n", pos)
        header = out[pos:end].split()
        if len(header) != 3 or header[1] != b"blob":
            raise Unreadable("git", f"cannot read blob {sha}")
        size = int(header[2])
        result[sha] = out[end + 1:end + 1 + size]
        pos = end + 1 + size + 1
    return result


@dataclass
class Change:
    path: str
    status: str
    new_mode: str
    new_sha: str
    old_sha: str = ""
    old_mode: str = ""
    binary: bool = False


REGULAR = ("100644", "100755")
LINKS = ("120000", "160000")
MEASURED = ("py", "sh")


@dataclass
class Entry:
    """One changed path with the sides that can be measured (None = not measured)."""
    ch: Change
    h_kind: str | None
    h_text: str
    b_kind: str | None
    b_blob: bytes | None


def _changes(top: Path, base: str, head: str, paths: list[str]) -> list[Change]:
    tail = ["--", *paths] if paths else []
    raw = _git(top, "diff", "--raw", "-z", "--no-renames", "--no-abbrev", "--no-ext-diff",
               base, head, *tail).split(b"\0")
    binary: set[str] = set()
    numstat = _git(top, "diff", "--numstat", "-z", "--no-renames", "--no-ext-diff",
                   base, head, *tail).split(b"\0")
    for entry in numstat:
        parts = entry.split(b"\t", 2)
        if len(parts) == 3 and parts[0] == b"-" and parts[1] == b"-":
            binary.add(parts[2].decode("utf-8", "surrogateescape"))
    changes = []
    for meta, path in zip(raw[0::2], raw[1::2]):
        fields = meta.lstrip(b":").split()
        if len(fields) < 5:
            continue
        name = path.decode("utf-8", "surrogateescape")
        changes.append(Change(name, fields[4].decode(), fields[1].decode(), fields[3].decode(),
                              fields[2].decode(), fields[0].decode(), name in binary))
    return changes


def _changed_lines(top: Path, base: str, head: str, path: str) -> tuple[set[int], set[int]]:
    """(added or changed lines on the head side, removed or changed lines on the base side)."""
    diff = _git(top, "diff", "--unified=0", "--no-color", "--no-ext-diff", "--no-textconv",
                "--no-renames", base, head, "--", path)
    new: set[int] = set()
    old: set[int] = set()
    for row in diff.split(b"\n"):
        hit = HUNK.match(row)
        if hit:
            o_start, o_count = int(hit.group(1)), 1 if hit.group(2) is None else int(hit.group(2))
            n_start, n_count = int(hit.group(3)), 1 if hit.group(4) is None else int(hit.group(4))
            old.update(range(o_start, o_start + o_count))
            new.update(range(n_start, n_start + n_count))
    return new, old


# --------------------------------------------------------------------- specs

def _is_test(path: str) -> bool:
    parts = path.split("/")
    name = parts[-1]
    return (any(p in ("tests", "test") for p in parts[:-1]) or name == "conftest.py"
            or name.startswith("test_") or name.endswith("_test.py"))


def _anchor_spans(top: Path, head: str, spec_dirs: list[str], explicit: bool, targets: set[str]
                  ) -> tuple[dict[str, list[tuple[str, str]]], dict[str, int]]:
    """{target file: [(spec name, find)]}, and the spec/row counts for the ROWS line.

    A missing DEFAULT directory is skipped; a missing explicit one, or none at all, is UNREADABLE.
    """
    entries = []
    seen: set[str] = set()
    for spec_dir in spec_dirs:
        listing = _git(top, "ls-tree", "-r", "-z", head, "--", spec_dir.rstrip("/") + "/")
        found = 0
        for row in listing.split(b"\0"):
            if not row:
                continue
            meta, _, name = row.partition(b"\t")
            mode, kind, sha = meta.decode().split()
            text = name.decode("utf-8", "surrogateescape")
            if kind == "blob" and mode != "120000" and text.endswith(".json"):
                found += 1
                if text not in seen:
                    seen.add(text)
                    entries.append((text, sha))
        if not found and explicit:
            raise Unreadable("spec-dir", f"no spec files under {spec_dir!r} at {head[:9]}")
    if not entries:
        raise Unreadable("spec-dir", f"no spec files under {', '.join(spec_dirs)} at {head[:9]}")
    blobs = _blobs(top, [sha for _, sha in entries])
    rows: dict[str, list[tuple[str, str]]] = {}
    stats = {"specs": 0, "nonspec": 0, "outside": 0, "rows": 0}
    for path, sha in entries:
        try:
            doc = json.loads(blobs[sha].decode("utf-8"))
        except ValueError as exc:   # UnicodeDecodeError is a ValueError
            raise Unreadable("spec-unreadable", f"{path}: {type(exc).__name__}") from exc
        if not isinstance(doc, dict) or not isinstance(doc.get("mutations"), list):
            stats["nonspec"] += 1
            continue
        stats["specs"] += 1
        root_value = doc.get("root")
        if root_value and posixpath.isabs(str(root_value)):
            root = posixpath.normpath(str(root_value))
            prefix = str(top).replace(os.sep, "/").rstrip("/") + "/"
            if not (root + "/").startswith(prefix):
                stats["outside"] += 1
                continue
            root = root[len(prefix):] or "."
        else:
            root = posixpath.normpath(posixpath.join(posixpath.dirname(path),
                                                     str(root_value or ".")))
        for row_doc in doc["mutations"]:
            if (not isinstance(row_doc, dict) or not isinstance(row_doc.get("file"), str)
                    or not isinstance(row_doc.get("find"), str)):
                raise Unreadable("spec-unreadable", f"{path}: a row without string file/find")
            stats["rows"] += 1
            target = posixpath.normpath(posixpath.join(root, row_doc["file"]))
            if target in targets:
                rows.setdefault(target, []).append((path, row_doc["find"]))
    return rows, stats


class Spans:
    """The find spans of one file, as character offsets, and which rows could not apply."""

    def __init__(self, text: str, finds: list[tuple[str, str]]) -> None:
        self.spans: list[tuple[int, int]] = []
        self.ambiguous = 0
        self.stale = 0
        for _, find in finds:
            n = text.count(find) if find else 0
            if n == 1:
                at = text.index(find)
                self.spans.append((at, at + len(find)))
            elif n == 0:
                self.stale += 1
            else:
                self.ambiguous += 1

    def overlaps(self, lo: int, hi: int) -> bool:
        return any(a < hi and lo < b for a, b in self.spans)


def _line_offsets(text: str) -> list[int]:
    """Start offset of each line; lines split on LF only, as git counts them."""
    starts = [0]
    for m in re.finditer("\n", text):
        starts.append(m.end())
    return starts


# ------------------------------------------------------------------- Python

@dataclass
class Decision:
    line: int
    kind: str
    lo: int          # first and last physical line the statement spans (header only if compound)
    hi: int
    parent: int | None = None      # header line of the nearest enclosing branch
    parent_span: tuple[int, int] | None = None


def _flags(node: ast.AST) -> list[str]:
    out = []
    for sub in ast.walk(node):
        if isinstance(sub, ast.IfExp):
            out.append("ifexp")
        elif isinstance(sub, ast.comprehension) and sub.ifs:
            out.append("comp-if")
        elif isinstance(sub, ast.BoolOp):
            out.append("boolop")
    return sorted(set(out))


def _ast_starts(text: str) -> list[int]:
    """Start offset of each line as the Python tokenizer counts them: LF, CRLF or a bare CR."""
    return [0] + [m.end() for m in re.finditer(r"\r\n|\r|\n", text)]


def _is_call(value: ast.AST) -> bool:
    return isinstance(value, ast.Call) or (isinstance(value, ast.Await) and isinstance(value.value, ast.Call))


def _python_decisions(text: str, path: str) -> list[Decision]:
    """Decision statements, with git's line numbers (LF-counted) even where ast counts a bare CR."""
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError, RecursionError) as exc:
        raise Unreadable("unreadable-file", f"{path}: does not parse ({type(exc).__name__})") from exc
    a_starts = _ast_starts(text)
    g_starts = _line_offsets(text)

    def git_line(offset: int) -> int:
        return bisect.bisect_right(g_starts, offset)

    def first(lineno: int) -> int:
        return git_line(a_starts[lineno - 1])

    def last(lineno: int) -> int:
        end = a_starts[lineno] - 1 if lineno < len(a_starts) else len(text) - 1
        return git_line(max(end, 0))

    def ast_line_text(lineno: int) -> str:
        end = a_starts[lineno] if lineno < len(a_starts) else len(text)
        return text[a_starts[lineno - 1]:end]

    found: list[Decision] = []

    def add(node: ast.AST, kind: str, hi: int, parent: Decision | None, *, expr: ast.AST | None = None):
        flags = _flags(expr if expr is not None else node)
        label = ",".join([kind, *flags]) if flags else kind
        found.append(Decision(first(node.lineno), label, first(node.lineno), last(hi),
                              parent.line if parent else None,
                              (parent.lo, parent.hi) if parent else None))
        return found[-1]

    def visit(body: list[ast.stmt], parent: Decision | None, in_orelse_of: ast.If | None = None):
        for st in body:
            if isinstance(st, ast.If):
                is_elif = (in_orelse_of is not None and len(in_orelse_of.orelse) == 1
                           and ast_line_text(st.lineno).lstrip().startswith("elif"))
                me = add(st, "elif" if is_elif else "if", st.test.end_lineno, parent, expr=st.test)
                visit(st.body, me)
                visit(st.orelse, me, st)
            elif isinstance(st, (ast.While, ast.For, ast.AsyncFor)):
                head = st.test if isinstance(st, ast.While) else st.iter
                me = add(st, "while" if isinstance(st, ast.While) else "for", head.end_lineno,
                         parent, expr=head)
                visit(st.body, me)
                visit(st.orelse, me)
            elif isinstance(st, (ast.Try, getattr(ast, "TryStar", ast.Try))):
                visit(st.body, parent)
                for handler in st.handlers:
                    top = handler.type.end_lineno if handler.type else handler.lineno
                    me = add(handler, "except", top, parent)
                    visit(handler.body, me)
                visit(st.orelse, parent)
                visit(st.finalbody, parent)
            elif isinstance(st, (ast.With, ast.AsyncWith)):
                add(st, "with", max(item.context_expr.end_lineno for item in st.items), parent,
                    expr=st.items[0].context_expr)
                visit(st.body, parent)
            elif isinstance(st, ast.Match):
                me = add(st, "match", st.subject.end_lineno, parent)
                for case in st.cases:
                    tail = (case.guard or case.pattern)
                    sub = Decision(first(case.pattern.lineno), "case", first(case.pattern.lineno),
                                   last(tail.end_lineno), me.line, (me.lo, me.hi))
                    found.append(sub)
                    visit(case.body, sub)
            elif isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                visit(st.body, None)
            elif isinstance(st, (ast.Return, ast.Raise, ast.Assert)):
                add(st, type(st).__name__.lower(), st.end_lineno, parent)
            elif isinstance(st, (ast.Continue, ast.Break)):
                add(st, type(st).__name__.lower(), st.end_lineno, parent)
            elif isinstance(st, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
                add(st, "assign", st.end_lineno, parent)
            elif isinstance(st, ast.Expr) and _is_call(st.value):
                add(st, "call", st.end_lineno, parent)

    visit(tree.body, None)
    return found


def _decode_python(blob: bytes, path: str) -> str:
    try:
        encoding, _ = tokenize.detect_encoding(BytesIO(blob).readline)
        return blob.decode(encoding)
    except (SyntaxError, UnicodeDecodeError, LookupError) as exc:
        raise Unreadable("unreadable-file", f"{path}: cannot decode ({type(exc).__name__})") from exc


# --------------------------------------------------------------------- shell

_CONTROL = re.compile(r"(?:^|[;&|(]\s*|\bthen\s+|\bdo\s+|\belse\s+)(?:if|elif|while|until|for|case|select)\b")
_TEST = re.compile(r"(?:^|[\s;&|(!])\[\[?\s")
_JUMP = re.compile(r"(?:^|[;&|(]\s*|\bthen\s+|\bdo\s+|\belse\s+)(?:return|exit|break|continue)\b")
_ARM_END = re.compile(r"""^\(?(?:"[^"]*"|'[^']*'|[^\s()"']+)(?:\s*\|\s*(?:"[^"]*"|'[^']*'|[^\s()"']+))*\)\s*(?:#.*)?$""")
_ASSIGN = re.compile(r"^(?:(?:local|declare|readonly|export|typeset)(?:\s+-\w+)*\s+)?[A-Za-z_]\w*(?:\[[^\]]*\])?\+?=")
_VERDICT = re.compile(r"(?:^|[;&|(]\s*|\bthen\s+|\bdo\s+|\belse\s+)_?(?:refuse|allow|deny|block|die|fail)\w*\b")
_NOISE = re.compile(r"^(?:then|do|else|fi|done|esac|\{|\}|;;|\))\s*(?:#.*)?$")
_FUNC = re.compile(r"^(?:function\s+)?[A-Za-z_][\w-]*\s*\(\)\s*\{?\s*(?:#.*)?$|^function\s+[\w-]+\s*\{?\s*$")


def _shell_kind(line: str) -> str | None:
    s = line.strip()
    if not s or s.startswith("#") or _NOISE.match(s) or _FUNC.match(s):
        return None
    kinds = []
    if _CONTROL.search(s):
        kinds.append("control")
    if _TEST.search(s):
        kinds.append("test")
    if "&&" in s or "||" in s:
        kinds.append("andor")
    if ";;" in s or _ARM_END.match(s):
        kinds.append("arm")
    if _JUMP.search(s):
        kinds.append("jump")
    if _ASSIGN.match(s):
        kinds.append("assign")
    if _VERDICT.search(s):
        kinds.append("verdict")
    return ",".join(kinds) if kinds else None


def _arm_segments(text: str, start: int, line: str) -> list[tuple[int, int]]:
    """Offsets of each `;;`-terminated arm on one physical line (a single span if < 2)."""
    cuts = [m.end() for m in re.finditer(r";;", line)]
    if len(cuts) < 2:
        return []
    bounds = [0, *cuts[:-1], len(line)]   # text after the last `;;` (`esac`) belongs to that arm
    return [(start + a, start + b) for a, b in zip(bounds, bounds[1:]) if line[a:b].strip()]


# ---------------------------------------------------------------------- core

def _language(path: str, blob: bytes) -> str:
    """`py`, `sh`, `other` (an allow-listed document or data file) or `unmeasured` (anything else)."""
    name = posixpath.basename(path)
    suffix = posixpath.splitext(name)[1].lower()
    if suffix == ".py":
        return "py"
    if suffix in SHELL_SUFFIXES:
        return "sh"
    first = blob.split(b"\n", 1)[0]
    if SHELL_HEAD.match(first):
        return "sh"
    if PY_HEAD.match(first):
        return "py"
    if suffix in DOC_SUFFIXES or name in DOC_NAMES:
        return "other"
    return "unmeasured"


def _text(blob: bytes, kind: str, path: str) -> str:
    if kind == "py":
        return _decode_python(blob, path)
    try:
        return blob.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Unreadable("unreadable-file", f"{path}: not UTF-8") from exc


def _line_text(text: str, line: int) -> str:
    rows = text.split("\n")
    return rows[line - 1] if 0 < line <= len(rows) else ""


def census(repo: Path, base: str, head: str, spec_dirs: list[str] | None, paths: list[str]) -> dict:
    top = _toplevel(repo)
    base_sha, head_sha = _commit(top, base), _commit(top, head)
    explicit = bool(spec_dirs)
    dirs = [_repo_relative(top, d) for d in spec_dirs] if spec_dirs else list(DEFAULT_SPEC_DIRS)
    named_paths = [_repo_relative(top, p, "path-no-match") for p in paths]
    wanted = [] if "." in named_paths else named_paths
    changes = _changes(top, base_sha, head_sha, wanted)
    for want in wanted:
        stem = want.rstrip("/")
        if not any(ch.path == stem or ch.path.startswith(stem + "/") for ch in changes):
            raise Unreadable("path-no-match", f"--path {want!r} matches no change between the refs")
    skipped = {"binary": 0, "link": 0, "tests": 0, "other": 0}
    unmeasured: list[str] = []
    plan: list[Change] = []
    for ch in changes:
        if ch.binary:
            skipped["binary"] += 1
        elif _is_test(ch.path):
            skipped["tests"] += 1
        else:
            plan.append(ch)
    # A side is read only if it exists and is a regular file: a gitlink's sha is a commit, a
    # symlink's blob is its target text, and neither is source.
    def head_regular(ch: Change) -> bool:
        return ch.status != "D" and ch.new_mode in REGULAR

    def base_regular(ch: Change) -> bool:
        return ch.status != "A" and ch.old_mode in REGULAR

    wanted_shas = {ch.new_sha for ch in plan if head_regular(ch)} | {ch.old_sha for ch in plan if base_regular(ch)}
    contents = _blobs(top, sorted(wanted_shas))
    work: list[Entry] = []
    for ch in plan:
        h_blob = contents[ch.new_sha] if head_regular(ch) else None
        b_blob = contents[ch.old_sha] if base_regular(ch) else None
        h_kind = _language(ch.path, h_blob) if h_blob is not None else (
            "link" if ch.status != "D" and ch.new_mode in LINKS else None)
        b_kind = _language(ch.path, b_blob) if b_blob is not None else (
            "link" if ch.status != "A" and ch.old_mode in LINKS else None)
        measured = [k for k in (h_kind, b_kind) if k in MEASURED]
        if "unmeasured" in (h_kind, b_kind):
            unmeasured.append(ch.path)
        if not measured:
            if "unmeasured" not in (h_kind, b_kind):
                skipped["link" if "link" in (h_kind, b_kind) else "other"] += 1
            continue
        h_text = _text(h_blob, h_kind, ch.path) if h_kind in MEASURED else ""
        work.append(Entry(ch, h_kind if h_kind in MEASURED else None, h_text,
                          b_kind if b_kind in MEASURED else None, b_blob))
    anchors, stats = _anchor_spans(top, head_sha, dirs, explicit,
                                   {e.ch.path for e in work if e.h_kind})

    out: list[str] = []
    removed_out: list[str] = []
    totals = {"decision": 0, "anchored": 0, "unanchored": 0, "arm": 0, "ambiguous": 0, "stale": 0,
              "removed": 0}
    unparsed: list[str] = []
    for e in sorted(work, key=lambda w: w.ch.path):
        ch = e.ch
        new_lines: set[int] = set()
        old_lines: set[int] = set()
        if e.h_kind:
            new_lines, old_lines = _changed_lines(top, base_sha, head_sha, ch.path)
            _census_added(ch, e.h_kind, e.h_text, new_lines, anchors.get(ch.path, []), totals, out)
        if e.b_kind:
            try:
                old_text = _text(e.b_blob, e.b_kind, ch.path)
            except Unreadable:
                unparsed.append(ch.path)   # a file that never parsed never ran a guard
                continue
            if not e.h_kind:   # the head is no longer code: every base decision is gone
                old_lines = set(range(1, old_text.count("\n") + 2))
            if old_lines:
                try:
                    _census_removed(ch, e.b_kind, old_text, old_lines, totals, removed_out)
                except Unreadable:
                    unparsed.append(ch.path)
    header = [
        f"CENSUS-SCOPE: base={base_sha[:9]} head={head_sha[:9]} files={len(work)} "
        f"deleted={sum(1 for e in work if e.ch.status == 'D')} "
        f"specs={stats['specs']} spec_rows={stats['rows']}",
        f"SKIPPED: binary={skipped['binary']} link={skipped['link']} "
        f"tests={skipped['tests']} other={skipped['other']} unmeasured={len(unmeasured)} "
        f"nonspec_json={stats['nonspec']} outside_repo_specs={stats['outside']}",
        f"ROWS: ambiguous_find={totals['ambiguous']} stale_find={totals['stale']} "
        f"(rows over the census files that anchor nothing)",
        f"ARMS: unanchored_arm_of_anchored={totals['arm']}",
    ]
    header += [f"UNMEASURED: {_enc(path)}" for path in sorted(unmeasured)]
    header += [f"UNPARSED-BASE: {_enc(path)}" for path in sorted(unparsed)]
    return {"lines": header + out + removed_out, **totals, "unparsed_base": len(unparsed)}


def _census_added(ch: Change, kind: str, text: str, changed: set[int],
                  finds: list[tuple[str, str]], totals: dict, out: list[str]) -> None:
    offsets = _line_offsets(text)
    spans = Spans(text, finds)
    totals["ambiguous"] += spans.ambiguous
    totals["stale"] += spans.stale
    n_lines = len(offsets)

    def span_of(lo: int, hi: int) -> tuple[int, int]:
        end = offsets[hi] if hi < n_lines else len(text)
        return offsets[lo - 1], end

    if kind == "py":
        for d in sorted(_python_decisions(text, ch.path), key=lambda d: (d.line, d.kind)):
            touched = [n for n in range(d.lo, d.hi + 1) if n in changed]
            if not touched:
                continue
            totals["decision"] += 1
            lo, hi = span_of(touched[0], touched[-1])
            if spans.overlaps(lo, hi):
                totals["anchored"] += 1
                continue
            totals["unanchored"] += 1
            note = ""
            if (d.kind.split(",")[0] not in HEADERS and d.parent is not None and d.parent_span
                    and spans.overlaps(*span_of(*d.parent_span))):
                note = f"arm-of-anchored:{d.parent}"
                totals["arm"] += 1
            out.append(_row(ch.path, d.line, d.kind, note, text))
        return
    for n in sorted(changed):
        if n > n_lines:
            continue
        line = text[offsets[n - 1]:(offsets[n] if n < n_lines else len(text))].rstrip("\n")
        kind_name = _shell_kind(line)
        if kind_name is None:
            continue
        totals["decision"] += 1
        arms = _arm_segments(text, offsets[n - 1], line)
        hit = all(spans.overlaps(a, b) for a, b in arms) if arms else spans.overlaps(*span_of(n, n))
        if hit:
            totals["anchored"] += 1
            continue
        totals["unanchored"] += 1
        note = "arms-not-all-anchored" if arms and any(spans.overlaps(a, b) for a, b in arms) else ""
        out.append(_row(ch.path, n, kind_name, note, text))


def _census_removed(ch: Change, kind: str, old_text: str, old_lines: set[int],
                    totals: dict, out: list[str]) -> None:
    """Decision lines on the base side of the diff: guards the head no longer has (or has changed)."""
    if kind == "py":
        found = [(d.line, d.kind) for d in sorted(_python_decisions(old_text, ch.path),
                                                   key=lambda d: (d.line, d.kind))
                 if any(n in old_lines for n in range(d.lo, d.hi + 1))]
    else:
        found = []
        for n in sorted(old_lines):
            name = _shell_kind(_line_text(old_text, n))
            if name is not None:
                found.append((n, name))
    for line, name in found:
        totals["removed"] += 1
        source = json.dumps(_line_text(old_text, line).strip()[:120], ensure_ascii=False)
        out.append(f"REMOVED: {_enc(ch.path)}:{line} {name} {source}")


def _enc(value: str) -> str:
    return "".join(c if c.isprintable() else f"\\x{ord(c):02x}" for c in value)


def _row(path: str, line: int, kind: str, note: str, text: str) -> str:
    source = _line_text(text, line).strip()
    return f"{_enc(path)}:{line}\t{kind}\t{note}\t{_enc(source)[:120]}"


def _repo_relative(top: Path, value: str, reason: str = "spec-dir") -> str:
    p = Path(value)
    if p.is_absolute():
        try:
            return p.resolve().relative_to(top.resolve()).as_posix()
        except ValueError as exc:
            raise Unreadable(reason, f"outside the repository: {value}") from exc
    return posixpath.normpath(value)


def render(result: dict) -> str:
    if "decision" not in result:
        return f"{TOKEN}: {result['verdict']} reason={result['reason']}"
    return (f"{TOKEN}: DONE decision={result['decision']} anchored={result['anchored']} "
            f"unanchored={result['unanchored']} removed={result['removed']} "
            f"unparsed_base={result['unparsed_base']}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--base", required=True, help="base ref")
    ap.add_argument("--head", default="HEAD", help="head ref (default HEAD)")
    ap.add_argument("--spec-dir", action="append", default=[], metavar="DIR",
                    help="repo-relative spec directory at --head, repeatable; replaces the default "
                         f"({' and '.join(DEFAULT_SPEC_DIRS)})")
    ap.add_argument("--path", action="append", default=[], metavar="P",
                    help="limit the diff to this repo-relative path (repeatable)")
    ap.add_argument("--repo", type=Path, default=Path.cwd(), help="repository (default cwd)")
    args = ap.parse_args(argv)
    try:
        result = census(args.repo, args.base, args.head, args.spec_dir or None, args.path)
    except Unreadable as exc:
        if exc.detail:
            print(f"  {_enc(exc.detail)}")
        print(render({"verdict": "UNREADABLE", "reason": exc.reason}))
        return 2
    print("\n".join(result["lines"]))
    print(render(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
