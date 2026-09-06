"""Locate explicitly tagged shell blocks using one fence-aware Markdown scanner."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
import re
import subprocess

__all__ = [
    "DocBlockError", "DocUnreadable", "BadInfoString", "BlockNotFound",
    "AmbiguousBlock", "AmbiguousHeading", "BadIndex", "BadSubstArg",
    "MissingSubstitution", "OverlappingSubstitution", "BadTimeout", "BlockTimeout",
    "CleanupFailed", "LaunchFailed", "StreamPathUnwritable", "StreamPathsAlias",
    "PreambleUnreadable", "StreamWriteFailed", "StreamCloseFailed", "BadArgs",
    "Block", "extract", "select", "fence_aware_end", "find_heading",
]


class DocBlockError(Exception):
    """Base for document-block refusals."""


class DocUnreadable(DocBlockError):
    pass


class BadInfoString(DocBlockError):
    def __init__(self, key: str):
        self.key = key
        super().__init__(key)


class BlockNotFound(DocBlockError):
    pass


class AmbiguousBlock(DocBlockError):
    def __init__(self, n: int):
        self.n = n
        super().__init__(n)


class AmbiguousHeading(DocBlockError):
    def __init__(self, n: int):
        self.n = n
        super().__init__(n)


class BadIndex(DocBlockError):
    def __init__(self, n: object):
        self.n = n
        super().__init__(n)


class BadSubstArg(DocBlockError):
    def __init__(self, raw: str, duplicate_key: str | None = None):
        self.raw = raw
        self.duplicate_key = duplicate_key
        super().__init__(raw)


class MissingSubstitution(DocBlockError):
    def __init__(self, keys: list[str]):
        self.keys = keys
        super().__init__(keys)


class OverlappingSubstitution(DocBlockError):
    def __init__(self, pairs: list[tuple[str, str, str, int | None]]):
        self.pairs = pairs
        super().__init__(pairs)


class BadTimeout(DocBlockError):
    def __init__(self, value: object):
        self.value = value
        super().__init__(value)


class BlockTimeout(DocBlockError):
    def __init__(self, seconds: float):
        self.seconds = seconds
        super().__init__(seconds)


class CleanupFailed(DocBlockError):
    def __init__(self, path: str, cleanup_error: OSError | None):
        self.path = path
        self.cleanup_error = cleanup_error
        super().__init__(path, cleanup_error)


class LaunchFailed(DocBlockError):
    def __init__(self, stage: str, err: OSError | subprocess.TimeoutExpired | ValueError,
                 pgid: int | None = None):
        self.stage = stage
        self.err = err
        self.pgid = pgid
        super().__init__(stage, err)


class StreamPathUnwritable(DocBlockError):
    def __init__(self, leftover: str | None = None):
        self.leftover = leftover
        super().__init__(leftover)


class StreamPathsAlias(DocBlockError):
    pass


class PreambleUnreadable(DocBlockError):
    pass


class StreamWriteFailed(DocBlockError):
    def __init__(self, written: list[str], failed: str, skipped: list[str],
                 verify: str | None = None):
        self.written = written
        self.failed = failed
        self.skipped = skipped
        self.verify = verify
        super().__init__(written, failed, skipped, verify)


class StreamCloseFailed(DocBlockError):
    def __init__(self, stream: str, close_error: OSError):
        self.stream = stream
        self.close_error = close_error
        super().__init__(stream, close_error)


class BadArgs(DocBlockError):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


@dataclass(frozen=True)
class Block:
    text: str
    shell: str
    lineno: int
    info: str


@dataclass(frozen=True)
class _FenceEvent:
    lineno: int
    kind: str
    start: int
    end: int
    marker: str | None = None
    run: int = 0
    indent: int = 0
    info: str = ""
    level: int = 0
    text: str = ""
    candidate: bool = False


def _fence_events(text: str) -> Iterator[_FenceEvent]:
    """Recognize all fence and ATX grammar, yielding one event per source line."""
    opener = re.compile(r"^(?P<indent> {0,3})(?P<marks>`{3,}|~{3,})(?P<info>.*)$")
    closer = re.compile(r"^ {0,3}(?P<marks>`{3,}|~{3,})[ \t]*$")
    heading = re.compile(r"^ {0,3}(?P<marks>#{1,6})(?:[ \t](?P<title>.*)|$)")
    fence = None
    cursor = 0
    for lineno, raw in enumerate(text.splitlines(keepends=True), 1):
        start, cursor = cursor, cursor + len(raw)
        line = raw.rstrip("\r\n")
        if fence is not None:
            match = closer.fullmatch(line)
            if (match and match["marks"][0] == fence[0]
                    and len(match["marks"]) >= fence[1]):
                fence = None
                yield _FenceEvent(lineno, "close", start, cursor)
            else:
                yield _FenceEvent(lineno, "body", start, cursor)
            continue
        match = opener.fullmatch(line)
        if match and not (match["marks"][0] == "`" and "`" in match["info"]):
            marker, run = match["marks"][0], len(match["marks"])
            fence = (marker, run)
            info = match["info"]
            words = info.split()
            yield _FenceEvent(lineno, "open", start, cursor, marker, run,
                              len(match["indent"]), info,
                              candidate=marker == "`" and bool(words) and words[0] == "bash")
            continue
        match = heading.fullmatch(line)
        if match:
            title = re.sub(r"[ \t]+#+[ \t]*$", "", match["title"] or "").strip(" \t")
            yield _FenceEvent(lineno, "heading", start, cursor,
                              level=len(match["marks"]), text=title)
        else:
            yield _FenceEvent(lineno, "prose", start, cursor)


def fence_aware_end(text: str, start: int, level: int) -> int:
    """Bound a section using complete scanner lines, including the prefix state."""
    for event in _fence_events(text):
        if event.kind == "heading" and event.start >= start and event.level <= level:
            return event.start
    return len(text)


def find_heading(text: str, heading: str) -> tuple[int, int] | None:
    """Find a normalized ATX title, with full-form requests taking precedence.

    A title beginning with an ATX prefix is consequently addressable only by
    its full heading line. Requests use the same scanner as document lines.
    """
    request = next(_fence_events(heading), None)
    full = request is not None and request.kind == "heading"
    if full:
        title = request.text
    else:
        title = next(_fence_events("# " + heading)).text
    matches = [event for event in _fence_events(text)
               if event.kind == "heading" and event.text == title
               and (not full or event.level == request.level)]
    if len(matches) > 1:
        raise AmbiguousHeading(len(matches))
    if not matches:
        return None
    return matches[0].end, matches[0].level


def extract(doc: str | Path, heading: str) -> list[Block]:
    """Read a UTF-8 path and return tagged bash fences in the named section."""
    try:
        text = Path(doc).read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise DocUnreadable(str(doc)) from error
    found = find_heading(text, heading)
    if found is None:
        return []
    start, level = found
    end = fence_aware_end(text, start, level)
    blocks = []
    selected = None
    body = []
    shell = "strict"
    info = ""
    for event in _fence_events(text):
        if event.start < start or event.start >= end:
            continue
        if event.kind == "open" and event.candidate:
            info = event.info.lstrip()[len("bash"):]
            tokens = info.split()
            if "hmad:exec" not in tokens:
                continue
            seen = set()
            shell = "strict"
            for token in tokens:
                key = token.split("=", 1)[0]
                if token not in ("hmad:exec", "shell=strict", "shell=plain") or key in seen:
                    raise BadInfoString(token)
                seen.add(key)
                if key == "shell":
                    shell = token.split("=", 1)[1]
            selected = event
            body = []
        elif event.kind == "body" and selected is not None:
            line = text[event.start:event.end]
            removed = min(selected.indent, len(line) - len(line.lstrip(" ")))
            body.append(line[removed:])
        elif event.kind == "close" and selected is not None:
            blocks.append(Block("".join(body), shell, selected.lineno, info))
            selected = None
    if selected is not None:
        blocks.append(Block("".join(body), shell, selected.lineno, info))
    return blocks


def select(blocks: Sequence[Block], index: int | None = None) -> Block:
    """Apply one-based ordinal policy after the pure scan."""
    if index is not None and index < 1:
        raise BadIndex(index)
    if not blocks or (index is not None and index > len(blocks)):
        raise BlockNotFound()
    if index is None and len(blocks) > 1:
        raise AmbiguousBlock(len(blocks))
    return blocks[0 if index is None else index - 1]
