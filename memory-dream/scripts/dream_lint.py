#!/usr/bin/env python3
"""Mechanical half of a memory "dream": lint an auto-memory store, optionally repair links.

The judgment half (is this note still TRUE?) lives in ../SKILL.md. This script only
answers questions that have one correct answer:

  links     every `[[target]]` / `[[target|label]]` outside code, classified as
              RESOLVED   target is exactly one file's stem or frontmatter `name:` slug
              FIXABLE    no exact match, but spelling-normalised (case, '-', '_', ' ') it
                         matches exactly ONE file, AND a replacement spelling exists that
                         re-classifies as RESOLVED to that same file — the one safe rewrite
              UNSAFE     one normalised target, but no spelling of it resolves back to that
                         file (its slug collides, quotes, or contains '.') — never rewritten
              AMBIGUOUS  the target (exact or normalised) matches two or more files
              DANGLING   matches nothing. The memory spec allows this: a link with no page
                         yet marks something worth writing later. Reported, never "fixed"
                         and never counted as a defect.
              NONLINK    looks like `[[x]]` but cannot be a slug (`[[skills.config]]` TOML
                         header, `[[:space:]]` regex class) — ignored
            "Outside code" excludes fenced blocks (CommonMark closing rule: same character,
            at least as long), indented lines (4+ spaces or a tab — conservative: a link in
            a deeply indented list item is skipped rather than risked), and code spans,
            including ones that span lines.
  orphans   topic files that neither MEMORY.md nor MEMORY-ARCHIVE.md links to
  index     MEMORY.md against Claude Code's load caps (via h_mad_check_memory_index)
  oversized topic files above --max-note-bytes: candidates for a SPLIT (proposal only)
  stubs     files already retired to a single `MOVED TO [[slug]]` line
  last dream  age of the `.last-dream` stamp the skill writes after a full pass

Repair (`--fix-links`) rewrites FIXABLE links only. Without `--apply` it prints the diff
and writes nothing. With `--apply`, each file's bytes are read ONCE — the hash and the
text the fix is built from come from the same read — and per file the script: re-reads
and compares the hash, SKIPS the file if another session changed it, skips symlinks,
copies the original into a fresh timestamped subdirectory of --backup-dir (fsynced), and
replaces the file atomically with its mode and line endings preserved. A window of
microseconds between the final hash check and the rename remains; the backup covers it.

Exit: 0 nothing actionable · 1 actionable findings (FIXABLE, UNSAFE, AMBIGUOUS, orphans,
an index at WARN/OVER, or a skipped write) · 2 unreadable store, I/O failure or usage
error. Unreadable is never reported as clean.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import difflib
import hashlib
import os
import pathlib
import re
import shutil
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "h-mad" / "scripts"))
from h_mad_check_memory_index import assess, measure  # noqa: E402

INDEXES = ("MEMORY.md", "MEMORY-ARCHIVE.md")
STAMP = ".last-dream"
DEFAULT_MAX_NOTE_BYTES = 16384

FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
INDENTED = re.compile(r"^(?: {4}|\t)")
BACKTICK_RUN = re.compile(r"`+")
BLANK_LINE = re.compile(r"\n[ \t]*\r?\n")
LINK = re.compile(r"\[\[([^\[\]\n]+?)\]\]")
FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.S)
NAME = re.compile(r"^name:\s*(.+?)\s*$", re.M)
INDEX_LINK = re.compile(r"\]\((?:\./)?([^)\s#]+\.md)(?:#[^)\s]*)?\)")
STUB = re.compile(r"^\s*MOVED TO \[\[[^\]]+\]\]\s*$")
NONLINK = re.compile(r"^:|\.|^\s*$|[{}<>=\"'`]")


def norm(s: str) -> str:
    return re.sub(r"[-_\s]+", "", s.strip().lower()).removesuffix(".md")


def mask_code(text: str) -> str:
    """Length-preserving copy of `text` with every code character replaced by a space.

    Offsets into the result are offsets into the original, which is what makes the
    rewrite safe: links are FOUND in the mask and REPLACED in the original.
    """
    out = []
    fence: tuple[str, int] | None = None
    for line in text.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        m = FENCE.match(body)
        if fence is not None:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= fence[1] \
                    and not m.group(2).strip():
                fence = None
            out.append(re.sub(r"[^\r\n]", " ", line))
        elif m and not (m.group(1)[0] == "`" and "`" in m.group(2)):
            fence = (m.group(1)[0], len(m.group(1)))
            out.append(re.sub(r"[^\r\n]", " ", line))
        elif INDENTED.match(line):
            out.append(re.sub(r"[^\r\n]", " ", line))
        else:
            out.append(line)
    return mask_code_spans("".join(out))


def mask_code_spans(text: str) -> str:
    """Mask CommonMark code spans with a linear scan (no regex backtracking).

    An opening run of N backticks closes at the next run of EXACTLY N; runs of any
    other length inside are content. A span never crosses a blank line. An opening
    run with no closer is literal text and scanning resumes after it.
    """
    runs = list(BACKTICK_RUN.finditer(text))
    blanks = [m.start() for m in BLANK_LINE.finditer(text)]
    chars = list(text)
    i = 0
    while i < len(runs):
        opener = runs[i]
        n = len(opener.group(0))
        limit = next((b for b in blanks if b >= opener.end()), len(text))
        j = i + 1
        while j < len(runs) and runs[j].start() < limit and len(runs[j].group(0)) != n:
            j += 1
        if j < len(runs) and runs[j].start() < limit:
            for k in range(opener.start(), runs[j].end()):
                if chars[k] not in "\r\n":
                    chars[k] = " "
            i = j + 1
        else:
            i += 1
    return "".join(chars)


def link_spans(text: str):
    """Yield (start, end, inner) for every [[...]] outside code, offsets into `text`."""
    for lm in LINK.finditer(mask_code(text)):
        yield lm.start(), lm.end(), text[lm.start(1):lm.end(1)]


def frontmatter_name(text: str) -> str | None:
    fm = FRONTMATTER.match(text)
    if not fm:
        return None
    m = NAME.search(fm.group(1))
    return m.group(1).strip() if m else None


class Store:
    def __init__(self, root: pathlib.Path):
        self.root = root
        self.raw: dict[str, bytes] = {}
        self.text: dict[str, str] = {}
        for p in sorted(root.glob("*.md")):
            b = p.read_bytes()            # ONE read: hash and text share these bytes
            self.raw[p.name] = b
            self.text[p.name] = b.decode("utf-8")
        if "MEMORY.md" not in self.text:
            raise OSError(f"no MEMORY.md in {root}")
        self.topics = [n for n in self.text if n not in INDEXES]
        self.hashes = {n: sha(self.raw[n]) for n in self.topics}
        self.exact: dict[str, set[str]] = {}
        self.by_norm: dict[str, set[str]] = {}
        self.slug: dict[str, str | None] = {}
        for n in self.topics:
            stem = n[:-3]
            slug = frontmatter_name(self.text[n])
            self.slug[n] = slug
            for key in {stem, slug} - {None}:
                self.exact.setdefault(key, set()).add(n)
                self.by_norm.setdefault(norm(key), set()).add(n)

    def replacement(self, target_file: str) -> str | None:
        """A spelling that re-classifies as RESOLVED to `target_file`, slug preferred.

        A slug such as `x]]y` or `pipe|name` is an exact key yet writes a broken link
        (`[[x]]y]]` parses as `x`; `[[pipe|name]]` classifies as `pipe`), so brackets,
        pipes and newlines disqualify a candidate. With NONLINK that leaves only
        spellings that parse back as exactly themselves.
        """
        for cand in (self.slug[target_file], target_file[:-3]):
            if (cand and not NONLINK.search(cand) and not re.search(r"[\[\]|\r\n]", cand)
                    and self.exact.get(cand) == {target_file}):
                return cand
        return None

    def classify(self, inner: str) -> tuple[str, str | None]:
        target = inner.split("|", 1)[0].strip()
        if NONLINK.search(target):
            return "NONLINK", None
        hit = self.exact.get(target)
        if hit:
            return ("RESOLVED", next(iter(hit))) if len(hit) == 1 else ("AMBIGUOUS", None)
        hits = self.by_norm.get(norm(target), set())
        if len(hits) == 1:
            tgt = next(iter(hits))
            return ("FIXABLE", tgt) if self.replacement(tgt) else ("UNSAFE", tgt)
        if len(hits) > 1:
            return "AMBIGUOUS", None
        return "DANGLING", None

    def links(self):
        """Yield (file, start, end, inner, kind, target_file) over every topic file."""
        for n in self.topics:
            for s, e, inner in link_spans(self.text[n]):
                kind, tgt = self.classify(inner)
                yield n, s, e, inner, kind, tgt

    def orphans(self) -> list[str]:
        linked = set()
        for idx in INDEXES:
            linked |= set(INDEX_LINK.findall(self.text.get(idx, "")))
        return sorted(n for n in self.topics if n not in linked)

    def stubs(self) -> list[str]:
        return sorted(n for n in self.topics if STUB.match(self.text[n]))


def rewrite(text: str, spans) -> str:
    """Apply (start, end, replacement) spans, last first so offsets stay valid."""
    for s, e, rep in sorted(spans, reverse=True):
        text = text[:s] + rep + text[e:]
    return text


def fixed_text(store: Store, name: str) -> str:
    spans = []
    for s, e, inner in link_spans(store.text[name]):
        kind, tgt = store.classify(inner)
        if kind != "FIXABLE" or tgt is None:
            continue
        new = store.replacement(tgt)
        label = inner.split("|", 1)[1] if "|" in inner else None
        new_inner = f"{new}|{label}" if label is not None else f"{new}"
        spans.append((s, e, f"[[{new_inner}]]"))
    return rewrite(store.text[name], spans)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _fsync_write(path: pathlib.Path, data: bytes) -> None:
    with open(path, "xb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())


def atomic_write(path: pathlib.Path, data: bytes) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        shutil.copymode(path, tmp)
        os.replace(tmp, path)
    except BaseException:
        pathlib.Path(tmp).unlink(missing_ok=True)
        raise


def apply_fixes(store: Store, backup_root: pathlib.Path,
                before_write=None) -> tuple[list[str], list[str], pathlib.Path]:
    """Write each changed file; return (written, skipped, backup_dir).

    `before_write` is a test seam called just before the final hash check.
    """
    written, skipped = [], []
    backup_dir = backup_root / _dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup_dir.mkdir(parents=True, exist_ok=False)
    for name in store.topics:
        new = fixed_text(store, name)
        if new == store.text[name]:
            continue
        path = store.root / name
        if path.is_symlink() or path.stat().st_nlink > 1:
            skipped.append(f"{name} (symlink or hard link: edit the real file by hand)")
            continue
        if before_write:
            before_write(path)
        try:
            current = path.read_bytes()
        except FileNotFoundError:
            skipped.append(f"{name} (deleted)")
            continue
        if sha(current) != store.hashes[name]:
            skipped.append(f"{name} (changed since read)")
            continue
        _fsync_write(backup_dir / name, current)
        atomic_write(path, new.encode("utf-8"))
        written.append(name)
    return written, skipped, backup_dir


def last_dream_days(root: pathlib.Path, today: _dt.date) -> int | None:
    try:
        stamp = _dt.date.fromisoformat((root / STAMP).read_text().strip()[:10])
    except (OSError, ValueError):
        return None
    return (today - stamp).days


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Lint (and optionally repair links in) an auto-memory store")
    ap.add_argument("memory_dir", type=pathlib.Path)
    ap.add_argument("--max-note-bytes", type=int, default=DEFAULT_MAX_NOTE_BYTES)
    ap.add_argument("--fix-links", action="store_true", help="print the FIXABLE-link diff")
    ap.add_argument("--apply", action="store_true", help="with --fix-links: write it")
    ap.add_argument("--backup-dir", type=pathlib.Path,
                    help="with --apply: each run copies originals into a new timestamped subdir here")
    ap.add_argument("--verbose", action="store_true", help="list every non-resolved link")
    args = ap.parse_args(argv)
    if args.apply and not (args.fix_links and args.backup_dir):
        print("DREAM_LINT: USAGE --apply needs --fix-links and --backup-dir", file=sys.stderr)
        return 2

    try:
        store = Store(args.memory_dir)
        b, ln = measure(store.root / "MEMORY.md")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"DREAM_LINT: UNREADABLE {args.memory_dir} ({exc})", file=sys.stderr)
        return 2

    counts: dict[str, int] = {}
    rows = []
    for n, _s, _e, inner, kind, tgt in store.links():
        counts[kind] = counts.get(kind, 0) + 1
        if kind != "RESOLVED":
            rows.append((kind, n, inner, tgt))
    total = sum(v for k, v in counts.items() if k != "NONLINK")
    kinds = ("RESOLVED", "FIXABLE", "UNSAFE", "AMBIGUOUS", "DANGLING", "NONLINK")
    print(f"links total={total} " + " ".join(f"{k}={counts.get(k, 0)}" for k in kinds))
    for kind, n, inner, tgt in sorted(rows):
        if args.verbose or kind in ("FIXABLE", "UNSAFE", "AMBIGUOUS"):
            rep = store.replacement(tgt) if tgt else None
            arrow = f" -> [[{rep}]]" if kind == "FIXABLE" else (f" (one target: {tgt})" if tgt else "")
            print(f"  {kind:<9} {n}: [[{inner}]]{arrow}")

    orphans = store.orphans()
    print(f"orphans={len(orphans)}")
    for o in orphans:
        print(f"  ORPHAN    {o}")

    a = assess(b, ln)
    print(f"index {a['verdict']} bytes={b} lines={ln} worst={a['dimension']} frac={a['frac']:.0%}")

    big = sorted(((len(store.raw[n]), n) for n in store.topics
                  if len(store.raw[n]) > args.max_note_bytes), reverse=True)
    print(f"oversized(>{args.max_note_bytes}B)={len(big)}")
    for size, n in big:
        print(f"  OVERSIZED {n} {size}B")
    print(f"stubs={len(store.stubs())}")
    days = last_dream_days(store.root, _dt.date.today())
    print(f"last_dream={'never' if days is None else f'{days}d ago'}")

    blocking = bool(counts.get("UNSAFE") or counts.get("AMBIGUOUS") or orphans
                    or a["verdict"] != "OK")
    actionable = blocking or bool(counts.get("FIXABLE"))
    if args.fix_links:
        for n in store.topics:
            new = fixed_text(store, n)
            if new != store.text[n]:
                sys.stdout.writelines(difflib.unified_diff(
                    store.text[n].splitlines(keepends=True), new.splitlines(keepends=True),
                    f"a/{n}", f"b/{n}", n=0))
        if args.apply:
            try:
                written, skipped, bdir = apply_fixes(store, args.backup_dir)
            except OSError as exc:
                print(f"DREAM_LINT: IO_ERROR during --apply ({exc}); see backups under "
                      f"{args.backup_dir}", file=sys.stderr)
                return 2
            print(f"FIX: written={len(written)} skipped={len(skipped)} backup={bdir}")
            for s in skipped:
                print(f"  SKIPPED   {s}")
            return 1 if (skipped or blocking) else 0
    return 1 if actionable else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
