"""Locate explicitly tagged shell blocks using one fence-aware Markdown scanner."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
import math
import os
import re
import shutil
import signal
import subprocess
import tempfile
import argparse
import io
import json
import stat
import sys
import unicodedata

__all__ = [
    "DocBlockError", "DocUnreadable", "BadInfoString", "BlockNotFound",
    "AmbiguousBlock", "AmbiguousHeading", "BadIndex", "BadSubstArg",
    "MissingSubstitution", "OverlappingSubstitution", "BadTimeout", "BlockTimeout",
    "CleanupFailed", "LaunchFailed", "StreamPathUnwritable", "StreamPathsAlias",
    "PreambleUnreadable", "StreamWriteFailed", "StreamCloseFailed", "BadArgs",
    "Block", "extract", "select", "fence_aware_end", "find_heading", "substitute",
    "RunResult", "run_block", "main",
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
    def __init__(self, leftover: str | None = None):
        self.leftover = leftover
        super().__init__(leftover)


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


def _is_valid_substitution_key(key: str) -> bool:
    """Return whether a substitution key is valid on every public surface."""
    return bool(key)


def substitute(block: Block, subs: Mapping[str, str]) -> tuple[Block, dict[str, int]]:
    """Replace independent literal keys once, preserving original-text counts."""
    if not subs:
        return replace(block), {}
    if not all(_is_valid_substitution_key(key) for key in subs):
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


VERDICT_TABLE: dict[str, int] = {
    "RAN": 0, "NOT_FOUND": 0, "AMBIGUOUS": 0, "AMBIGUOUS_HEADING": 0,
    "BAD_INDEX": 0, "BAD_TIMEOUT": 0, "BAD_ARGS": 0, "BAD_SUBST": 0,
    "SUBST_MISSING": 0, "SUBST_OVERLAP": 0, "BAD_INFO": 0, "TIMEOUT": 0,
    "CLEANUP_FAILED": 2,
    "LAUNCH_FAILED stage=mkdtemp": 2, "LAUNCH_FAILED stage=spawn": 2,
    "LAUNCH_FAILED stage=reap": 2, "LAUNCH_FAILED stage=collect": 2,
    "UNREADABLE reason=doc_unreadable": 2,
    "UNREADABLE reason=preamble_unreadable": 2,
    "UNREADABLE reason=stream_paths_alias": 2,
    "UNREADABLE reason=stream_path_unwritable": 2,
    "UNREADABLE reason=stream_write_failed": 2,
    "UNREADABLE reason=stream_close_failed": 2,
}
_VERDICT_FOR: dict[type[DocBlockError], Callable[[DocBlockError], str]] = {
    BlockNotFound: lambda e: "NOT_FOUND",
    AmbiguousBlock: lambda e: "AMBIGUOUS",
    AmbiguousHeading: lambda e: "AMBIGUOUS_HEADING",
    BadIndex: lambda e: "BAD_INDEX",
    BadTimeout: lambda e: "BAD_TIMEOUT",
    BadArgs: lambda e: "BAD_ARGS",
    BadSubstArg: lambda e: "BAD_SUBST",
    MissingSubstitution: lambda e: "SUBST_MISSING",
    OverlappingSubstitution: lambda e: "SUBST_OVERLAP",
    BadInfoString: lambda e: "BAD_INFO",
    BlockTimeout: lambda e: "TIMEOUT",
    CleanupFailed: lambda e: "CLEANUP_FAILED",
    LaunchFailed: lambda e: f"LAUNCH_FAILED stage={e.stage}",
    DocUnreadable: lambda e: "UNREADABLE reason=doc_unreadable",
    PreambleUnreadable: lambda e: "UNREADABLE reason=preamble_unreadable",
    StreamPathsAlias: lambda e: "UNREADABLE reason=stream_paths_alias",
    StreamPathUnwritable: lambda e: "UNREADABLE reason=stream_path_unwritable",
    StreamWriteFailed: lambda e: "UNREADABLE reason=stream_write_failed",
    StreamCloseFailed: lambda e: "UNREADABLE reason=stream_close_failed",
}
DETAIL_KEYS: tuple[str, ...] = (
    "missing_key:", "overlap:", "intersect:", "duplicate_key:", "os_error:", "pgid:",
    "written:", "failed:", "skipped:", "verify:", "stream:", "leftover:",
)


def _field(value: object) -> str:
    """Quote the 20 dynamic values; the seven bare fields never reach this renderer.

    Stringify first, JSON-escape quotes and backslashes, then escape remaining
    control and line separator characters while keeping other Unicode readable.
    """
    encoded = json.dumps(str(value), ensure_ascii=False)
    return "".join(f"\\u{ord(ch):04x}" if unicodedata.category(ch) in {"Cc", "Zl", "Zp"}
                   else ch for ch in encoded)


def _reserve(path: str) -> tuple[io.TextIOWrapper, bool]:
    for _ in range(3):
        try:
            fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_EXCL, 0o644)
            created = True
        except FileExistsError:
            try:
                fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_NONBLOCK)
                created = False
            except FileNotFoundError:
                continue
        try:
            identity = os.fstat(fd)
            if not stat.S_ISREG(identity.st_mode):
                raise OSError("stream path is not a regular file")
            handle = os.fdopen(fd, "a", encoding="utf-8")
        except BaseException:
            os.close(fd)
            raise
        handle.reserved_identity = (identity.st_dev, identity.st_ino)
        return handle, created
    raise StreamPathUnwritable() from None


def _close_stream(handle: io.TextIOWrapper) -> None:
    handle.close()


def _final_write(handle: io.TextIOWrapper, text: str) -> None:
    pending = None
    try:
        handle.seek(0)
        handle.truncate()
        handle.write(text)
        handle.flush()
    except OSError as err:
        pending = err
    finally:
        try:
            _close_stream(handle)
        except OSError as err:
            if pending is None:
                pending = err
            else:
                pending.__context__ = err
    if pending is not None:
        raise pending


def _verify(path: str, text: str) -> bool:
    try:
        return Path(path).read_bytes() == text.encode("utf-8", errors="replace")
    except OSError:
        return False


def _remove_created(path: str, handle: io.TextIOWrapper) -> str | None:
    """Remove only the reserved inode, and report any surviving path."""
    try:
        current = os.lstat(path)
        if (current.st_dev, current.st_ino) != handle.reserved_identity:
            return path
        os.unlink(path)
    except OSError:
        pass
    if os.path.lexists(path):
        return path
    return None


def _run_with_streams(args, block: Block, preamble: str | None, timeout: float) -> RunResult:
    streams = []
    pending = None
    close_error = None
    try:
        try:
            for name in ("stdout", "stderr"):
                path = getattr(args, name)
                if path is not None:
                    handle, created = _reserve(path)
                    streams.append((name, path, handle, created))
        except (OSError, StreamPathUnwritable) as err:
            leftover = None
            for name, path, handle, created in streams:
                try:
                    _close_stream(handle)
                except OSError:
                    pass
                finally:
                    if created:
                        leftover = _remove_created(path, handle) or leftover
            failure = StreamPathUnwritable(leftover)
            if isinstance(err, OSError):
                raise failure from err
            raise failure from None

        try:
            if len(streams) == 2:
                first, second = (os.fstat(entry[2].fileno()) for entry in streams)
                if (first.st_dev, first.st_ino) == (second.st_dev, second.st_ino):
                    leftover = None
                    for name, path, handle, created in streams:
                        if created:
                            leftover = _remove_created(path, handle) or leftover
                    raise StreamPathsAlias(leftover)
        except OSError as err:
            raise StreamPathUnwritable() from err

        result = run_block(block, preamble=preamble, timeout=timeout)
        written = []
        for i, (name, path, handle, created) in enumerate(streams):
            skipped = [entry[0] for entry in streams[i + 1:]]
            text = getattr(result, name)
            try:
                _final_write(handle, text)
            except OSError as err:
                raise StreamWriteFailed(written, name, skipped) from err
            if not _verify(path, text):
                raise StreamWriteFailed(written, name, skipped, verify=name)
            written.append(name)
    except DocBlockError as err:
        pending = err
    finally:
        for name, path, handle, created in streams:
            if not handle.closed:
                try:
                    _close_stream(handle)
                except OSError as err:
                    if close_error is None:
                        close_error = (name, err)
    if pending is not None and VERDICT_TABLE[_VERDICT_FOR[type(pending)](pending)] == 2:
        if close_error is not None:
            pending.__context__ = close_error[1]
        raise pending
    if close_error is not None:
        raise StreamCloseFailed(*close_error) from pending
    if pending is not None:
        raise pending
    return result


def _render_error(error: DocBlockError, heading: str | None) -> int:
    head = _VERDICT_FOR[type(error)](error)
    fields = ""
    details = []
    if isinstance(error, (BlockNotFound, AmbiguousBlock, AmbiguousHeading)):
        if isinstance(error, AmbiguousBlock):
            fields += f" blocks={error.n}"
        elif isinstance(error, AmbiguousHeading):
            fields += f" count={error.n}"
        fields += f" heading={_field(heading)}"
    elif isinstance(error, BadIndex):
        fields = f" index={_field(error.n)}"
    elif isinstance(error, BadTimeout):
        fields = f" value={_field(error.value)}"
    elif isinstance(error, BadArgs):
        fields = f" message={_field(error.message)}"
    elif isinstance(error, BadSubstArg):
        fields = f" arg={_field(error.raw)}"
        if error.duplicate_key is not None:
            details.append("duplicate_key: " + _field(error.duplicate_key))
    elif isinstance(error, MissingSubstitution):
        fields = f" keys={len(error.keys)}"
        details.extend("missing_key: " + _field(key) for key in error.keys)
    elif isinstance(error, OverlappingSubstitution):
        fields = f" keys={len({key for pair in error.pairs for key in pair[1:3]})}"
        for kind, a, b, offset in error.pairs:
            if kind == "intersect":
                details.append(f"intersect: {_field(a)} {_field(b)} {_field(offset)}")
            else:
                details.append(f"overlap: {_field(a)} {_field(b)}")
    elif isinstance(error, BadInfoString):
        fields = f" key={_field(error.key)}"
    elif isinstance(error, BlockTimeout):
        fields = f" seconds={_field(error.seconds)}"
    elif isinstance(error, CleanupFailed):
        fields = f" path={_field(error.path)}"
        if error.cleanup_error is not None:
            details.append("os_error: " + _field(error.cleanup_error))
    elif isinstance(error, LaunchFailed):
        details.append("os_error: " + _field(error.err))
        if error.pgid is not None:
            details.append("pgid: " + _field(error.pgid))
    elif isinstance(error, StreamWriteFailed):
        if error.written:
            details.append("written: " + _field(" ".join(error.written)))
        details.append("failed: " + _field(error.failed))
        if error.skipped:
            details.append("skipped: " + _field(" ".join(error.skipped)))
        if error.verify is not None:
            details.append("verify: " + _field(error.verify))
    elif isinstance(error, StreamCloseFailed):
        details.append("stream: " + _field(error.stream))
        details.append("os_error: " + _field(error.close_error))
    elif isinstance(error, (StreamPathUnwritable, StreamPathsAlias)):
        if error.leftover is not None:
            details.append("leftover: " + _field(error.leftover))
    print("DOCBLOCK: " + head + fields)
    for line in details:
        print(line)
    return VERDICT_TABLE[head]


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise BadArgs(message)


def main(argv: Sequence[str] | None = None) -> int:
    heading = None
    try:
        parser = _ArgumentParser(allow_abbrev=False)
        parser.add_argument("doc")
        parser.add_argument("--heading", required=True)
        parser.add_argument("--index", type=str)
        parser.add_argument("--subst", action="append")
        parser.add_argument("--preamble-file")
        parser.add_argument("--shell-timeout", type=str, default="30")
        parser.add_argument("--stdout")
        parser.add_argument("--stderr")
        args = parser.parse_args(argv)
        heading = args.heading
        blocks = extract(args.doc, heading)
        try:
            index = int(args.index) if args.index is not None else None
        except ValueError:
            raise BadIndex(args.index)
        block = select(blocks, index)
        subs = {}
        for raw in args.subst or []:
            if "=" not in raw:
                raise BadSubstArg(raw)
            key, value = raw.split("=", 1)
            if not _is_valid_substitution_key(key):
                raise BadSubstArg(raw)
            if key in subs:
                raise BadSubstArg(raw, duplicate_key=key)
            subs[key] = value
        substituted, counts = substitute(block, subs)
        timeout = _validate_timeout(args.shell_timeout)
        preamble = None
        if args.preamble_file is not None:
            try:
                preamble = Path(args.preamble_file).read_bytes().decode("utf-8")
            except (OSError, UnicodeDecodeError) as err:
                raise PreambleUnreadable() from err
        result = _run_with_streams(args, substituted, preamble, timeout)
    except DocBlockError as err:
        return _render_error(err, heading)
    print(f"DOCBLOCK: RAN rc={result.rc} blocks=1 shell={result.shell}")
    return VERDICT_TABLE["RAN"]


if __name__ == "__main__":
    sys.exit(main())
