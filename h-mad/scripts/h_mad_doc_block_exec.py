"""Locate explicitly tagged shell blocks using one fence-aware Markdown scanner."""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
import math
import os
import re
import shutil
import signal
import subprocess
import tempfile

__all__ = [
    "DocBlockError", "DocUnreadable", "BadInfoString", "BlockNotFound",
    "AmbiguousBlock", "AmbiguousHeading", "BadIndex", "BadSubstArg",
    "MissingSubstitution", "OverlappingSubstitution", "BadTimeout", "BlockTimeout",
    "CleanupFailed", "LaunchFailed", "StreamPathUnwritable", "StreamPathsAlias",
    "PreambleUnreadable", "StreamWriteFailed", "StreamCloseFailed", "BadArgs",
    "Block", "extract", "select", "fence_aware_end", "find_heading", "substitute",
    "RunResult", "run_block",
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
        self.pairs = list(pairs)
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


def substitute(block: Block, subs: Mapping[str, str]) -> tuple[Block, dict[str, int]]:
    """Replace independent literal keys once, preserving original-text counts."""
    if not subs:
        return replace(block), {}
    if "" in subs:
        raise BadSubstArg("")

    text = block.text
    keys = sorted(subs)
    pairs = []
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            if a in b or b in a:
                shorter, longer = sorted((a, b), key=len)
                pairs.append(("overlap", shorter, longer, None))
    pairs.sort(key=lambda pair: (pair[1], pair[2]))

    spans = {
        k: [(m.start(), m.start() + len(k))
            for m in re.finditer(r"(?=" + re.escape(k) + r")", text)]
        for k in keys
    }
    intersections = []
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            left = right = 0
            while left < len(spans[a]) and right < len(spans[b]):
                a_start, a_end = spans[a][left]
                b_start, b_end = spans[b][right]
                if max(a_start, b_start) < min(a_end, b_end):
                    intersections.append(("intersect", a, b, max(a_start, b_start)))
                    break
                if a_end <= b_end:
                    left += 1
                else:
                    right += 1
    pairs.extend(sorted(intersections, key=lambda pair: (pair[3], pair[1], pair[2])))
    if pairs:
        raise OverlappingSubstitution(pairs)

    counts = {key: text.count(key) for key in subs}
    missing = [key for key, count in counts.items() if count == 0]
    if missing:
        raise MissingSubstitution(missing)
    result = re.sub("|".join(map(re.escape, keys)), lambda m: subs[m.group(0)], text)
    return replace(block, text=result), counts


@dataclass(frozen=True)
class RunResult:
    rc: int
    stdout: str
    stderr: str
    shell: str


_MAX_TIMEOUT_SECONDS = (2**31 - 1) / 1000  # CPython's INT_MAX-milliseconds selector limit.
DRAIN_SECONDS = 5.0


def _validate_timeout(value: object) -> float:
    """Refuse invalid bounds before allocating a directory or launching a child."""
    try:
        t = float(value)
    except (TypeError, ValueError, OverflowError):
        raise BadTimeout(value)
    if not (math.isfinite(t) and 0 < t <= _MAX_TIMEOUT_SECONDS):
        raise BadTimeout(value)
    return t


def _compose(preamble: str | None, text: str) -> str:
    return preamble.rstrip("\n") + "\n" + text if preamble is not None else text


def run_block(block: Block, *, preamble: str | None = None,
              timeout: float = 30.0) -> RunResult:
    """Execute one bash in a private cwd, bounding recovery and verifying cleanup."""
    timeout = _validate_timeout(timeout)
    cwd = None
    pending = None
    cleanup_error = None

    def record_collect(err: OSError) -> None:
        nonlocal pending
        if isinstance(pending, LaunchFailed):
            # Preserve an existing collect/reap verdict and its earlier context.
            err.__context__ = pending.__context__
            pending.__context__ = err
        else:
            outcome = LaunchFailed("collect", err, pgid=proc.pid)
            outcome.__context__ = pending
            pending = outcome

    try:
        try:
            cwd = tempfile.mkdtemp()
            os.chmod(cwd, 0o700)
        except OSError as err:
            pending = LaunchFailed("mkdtemp", err)
        if pending is None:
            script = _compose(preamble, block.text)
            try:
                proc = subprocess.Popen(
                    ["bash", "-euo", "pipefail", "-c", script]
                    if block.shell == "strict" else ["bash", "-c", script],
                    cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, encoding="utf-8", errors="replace",
                    start_new_session=True,
                )
            except (OSError, ValueError) as err:
                pending = LaunchFailed("spawn", err)
            else:
                try:
                    stdout, stderr = proc.communicate(timeout=timeout)
                except subprocess.TimeoutExpired:
                    pending = BlockTimeout(timeout)
                except OSError as err:
                    pending = LaunchFailed("collect", err, pgid=proc.pid)

                if pending is not None:
                    try:
                        proc.poll()
                    except OSError as err:
                        record_collect(err)
                    signalled = False
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                        signalled = True
                    except ProcessLookupError:
                        signalled = True
                    except OSError as err:
                        outcome = LaunchFailed("reap", err, pgid=proc.pid)
                        outcome.__context__ = pending
                        pending = outcome
                    try:
                        proc.communicate(timeout=DRAIN_SECONDS)
                    except subprocess.TimeoutExpired:
                        for pipe in (proc.stdout, proc.stderr):
                            try:
                                pipe.close()
                            except OSError as err:
                                record_collect(err)
                        if signalled:
                            try:
                                proc.wait(timeout=DRAIN_SECONDS)
                            except OSError as err:
                                record_collect(err)
                            except subprocess.TimeoutExpired as err:
                                outcome = LaunchFailed("reap", err, pgid=proc.pid)
                                outcome.__context__ = pending
                                pending = outcome
                    except OSError as err:
                        record_collect(err)
    finally:
        if cwd is not None:
            try:
                shutil.rmtree(cwd)
            except OSError as err:
                cleanup_error = err

    if cwd is not None and (cleanup_error is not None or os.path.lexists(cwd)):
        err = CleanupFailed(cwd, cleanup_error)
        if pending is not None:
            raise err from pending
        else:
            raise err from cleanup_error
    elif pending is not None:
        raise pending
    return RunResult(rc=proc.returncode, stdout=stdout, stderr=stderr, shell=block.shell)
