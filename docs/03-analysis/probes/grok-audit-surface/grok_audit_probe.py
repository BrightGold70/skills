"""Probe entry point for the Grok audit surface calibration."""

import argparse
from collections import Counter
from fractions import Fraction
import errno
import hashlib
import importlib.util
import io
import json
import math
import os
import random
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import traceback
from pathlib import Path
from typing import Callable, NoReturn


REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "h-mad" / "scripts"))
import h_mad_audit_gate as _gate
import h_mad_audit_cycle as _cycle
from h_mad_audit_origins import ORIGINS
from h_mad_review_evidence import _GROK_TYPES
import h_mad_tool_calls


SOURCES: dict[str, str] = {
    "audit-report-docs-copy": "docs/archive/2026-09",
    "tdd-gate-fail-opens": "docs/archive/2026-09",
    "agy-coder-fallback": "docs/archive/2026-10",
}
CALIBRATION = Path("docs/03-analysis/probes/grok-audit-surface/calibration")
GRAMMAR: dict[str, tuple[str, str]] = {
    "check-ledger": ("LEDGER:", "UNREADABLE"),
    "build-root": ("ROOT:", "UNREADABLE"),
    "record-cycle": ("RECORD:", "REFUSED"),
    "commit-data": ("COMMIT:", "REFUSED"),
    "smoke": ("SMOKE:", "UNREADABLE"),
    "extract": ("FINDINGS:", "UNREADABLE"),
    "score": ("SEEDSCORE:", "UNREADABLE"),
    "rescore": ("SEEDSCORE:", "UNREADABLE"),
    "main-leak": ("MAINLEAK:", "UNREADABLE"),
}
MODES: dict[str, Callable[[argparse.Namespace], int]] = {}
_OPEN_INPUT: str | None = None


class ProbeRefusal(Exception):
    """Base for declared refusals, which do not print tracebacks."""


class UsageError(ProbeRefusal):
    """A command line outside the probe's grammar."""


class ResetArgsConflict(ProbeRefusal):
    """Reset and a fresh-root destination were both requested."""


class ResetPurposeNotS1(ProbeRefusal):
    """Only S1 may reuse a root between cycles."""


class ResetTargetNotAbsolute(ProbeRefusal):
    """The reset spelling is not an absolute path."""


class ResetTargetNotDirectory(ProbeRefusal):
    """The reset target is not an existing directory."""


class ParentNotDirectory(ProbeRefusal):
    """The parent is not an absolute existing directory."""


class ParentInSystemTemp(ProbeRefusal):
    """The resolved parent lies inside a system temporary directory."""


class WorkDirInGitTree(ProbeRefusal):
    """The scratch parent is reachable from a Git tree."""


class ResetTargetInSystemTemp(ProbeRefusal):
    """The resolved reset target lies inside system temp."""


class ResetTargetOutsideRoots(ProbeRefusal):
    """The resolved reset target's parent is not named roots."""


class ResetTargetPrefix(ProbeRefusal):
    """The target does not name this document's S1 root."""


class RootResetMismatch(ProbeRefusal):
    """The restored root differs from the fresh expected tree."""


class Refusal(ProbeRefusal):
    """A mode's declared refusal reason."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class _TokenArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs) -> None:
        kwargs["add_help"] = False  # M:GAS-NO-HELP
        kwargs["allow_abbrev"] = False  # M:GAS-NO-ABBREV
        super().__init__(*args, **kwargs)

    def error(self, message: str) -> NoReturn:
        print(f"{self.prog}: error: {message}", file=sys.stderr)
        raise UsageError(message)  # M:GAS-USAGE


def parse_sources(value: str) -> dict[str, str]:
    """Parse the synthetic fixtures' ordered source-directory overrides."""
    sources = {}
    for item in value.split(","):
        name, separator, directory = item.partition("=")
        if not separator or not name or not directory or name in sources:
            raise argparse.ArgumentTypeError("expected unique name=archive-dir entries")
        sources[name] = directory
    return sources


def read_ledger(tree: Path) -> list[dict]:
    """Read one JSON object per line, mapping unreadable input to its refusal."""
    try:
        lines = (tree / CALIBRATION / "ledger.jsonl").read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise Refusal("ledger_counts") from exc
    records = []
    for line in lines:
        try:
            record = json.loads(line)
        except ValueError:
            record = None
        if not isinstance(record, dict):  # M:GAS-LEDGER-JSON
            raise Refusal("ledger_counts")
        records.append(record)
    return records


def check_ledger(tree: Path, sources: dict[str, str]) -> dict[str, int]:
    """Validate the class rule, imported origins and exact seed reconstruction."""
    documents = [
        (Path(directory) / feature / f"{feature}.{phase}.md").as_posix()
        for feature, directory in sources.items()
        for phase in ("plan", "design", "impl-plan")
    ]
    records = read_ledger(tree)
    required = set("id source phase class origin section original seeded expected".split())
    for record in records:
        if not required <= record.keys():  # M:GAS-LEDGER-FIELD
            raise Refusal("ledger_counts")
        if record["source"] not in documents:  # M:GAS-LEDGER-SOURCE
            raise Refusal("ledger_counts")
        if not record["original"]:  # M:GAS-LEDGER-EMPTY-ORIGINAL
            raise Refusal("ledger_counts")
        if not record["expected"]:  # M:GAS-LEDGER-EMPTY-EXPECTED
            raise Refusal("ledger_counts")

    classes = ("C1", "C2", "C3", "C4")
    expected_totals = Counter()
    actual_totals = Counter()
    for index, source in enumerate(documents):
        permitted = [value for slot, value in enumerate(classes) if slot != index % len(classes)]
        actual = [record["class"] for record in records if record["source"] == source]
        if sorted(actual) != sorted(permitted):  # M:GAS-LEDGER-CLASS
            raise Refusal("ledger_counts")
        expected_totals.update(permitted)
        actual_totals.update(actual)
    if actual_totals != expected_totals:
        raise Refusal("ledger_counts")

    for record in records:
        if record["origin"] not in ORIGINS:  # M:GAS-ORIGIN
            raise Refusal("ledger_origin")

    for source in documents:
        try:
            original_document = (tree / source).read_bytes()
            seeded_document = (tree / CALIBRATION / "seeded" / Path(source).name).read_bytes()
        except OSError as exc:
            raise Refusal("seed_rebuild") from exc
        rebuilt = original_document
        occupied_sections = set()
        for record in records:
            if record["source"] != source:
                continue
            original = record["original"].encode("utf-8")
            seeded = record["seeded"].encode("utf-8")
            if original_document.count(original) != 1:  # M:GAS-REBUILD-ORIGINAL-ONCE
                raise Refusal("seed_rebuild")
            position = original_document.find(original)
            headings = list(re.finditer(rb"^(#{2,3})[ \t]+([^\r\n]+)", original_document, re.MULTILINE))
            preceding = [heading for heading in headings if heading.start() < position]
            heading = preceding[-1] if preceding else None
            section = heading.start() if heading is not None else None
            if section in occupied_sections:  # M:GAS-REBUILD-SECTION-TWICE
                raise Refusal("seed_rebuild")
            occupied_sections.add(section)
            parents = [item for item in preceding if item.group(1) == b"##"]
            if parents and parents[-1].group(2).strip() == b"Version History":  # M:GAS-REBUILD-VERSION-HISTORY
                raise Refusal("seed_rebuild")
            if heading is None or heading.group(2).strip().decode("utf-8") != record["section"]:  # M:GAS-REBUILD-SECTION-NAME
                raise Refusal("seed_rebuild")
            if seeded_document.count(seeded) != 1:  # M:GAS-REBUILD-SEEDED-ONCE
                raise Refusal("seed_rebuild")
            rebuilt = rebuilt.replace(original, seeded, 1)
        if rebuilt != seeded_document:  # M:GAS-REBUILD-BYTES
            raise Refusal("seed_rebuild")
    return {"seeds": sum(actual_totals.values()), "docs": len(documents),
            **{value: actual_totals[value] for value in classes}}


def _mode_check_ledger(args: argparse.Namespace) -> int:
    if args.tree is not None:
        counts = check_ledger(args.tree, args.sources)
    else:
        try:
            archive = subprocess.run(
                ["git", "-C", str(args.repo), "archive", "--format=tar", args.calibration_sha],
                capture_output=True, check=True, timeout=15,
            ).stdout
        except (OSError, subprocess.SubprocessError) as exc:
            raise Refusal(f"calibration_ref:sha_unknown:{args.calibration_sha}") from exc
        with tempfile.TemporaryDirectory(prefix="gas-ledger-", dir=args.work_dir) as directory:  # M:GAS-SCRATCH-LEDGER-REPO
            tree = Path(directory)
            with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
                bundle.extractall(tree, filter="data")
            counts = check_ledger(tree, args.sources)
    print("LEDGER: OK " + " ".join(f"{key}={value}" for key, value in counts.items()))
    return 0


MODES["check-ledger"] = _mode_check_ledger


def normalise(data: bytes) -> str:
    return re.sub(r"\s+", " ", data.decode("utf-8", errors="replace"))  # M:GAS-LEAK-NORMALISE


def _git_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_OBJECT_DIRECTORY",
                 "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_INDEX_FILE"):
        environment.pop(name, None)
    return environment


def checked_parent(path, *, git_guard: bool) -> Path:
    if path is None or not os.path.isabs(path) or not os.path.isdir(path):  # M:GAS-PARENT-ISDIR
        raise ParentNotDirectory()
    parent = Path(path).resolve()
    if any(parent.is_relative_to(Path(directory).resolve()) for directory in {tempfile.gettempdir(), "/tmp", "/private/tmp"}):  # M:GAS-PARENT-TMPDIR
        raise ParentInSystemTemp()
    if git_guard:
        result = subprocess.run(
            ["git", "-C", str(parent), "rev-parse", "--git-dir"],
            capture_output=True, timeout=15, env=_git_environment(),
        )
        if result.returncode == 0:  # M:GAS-WORKDIR-GIT
            raise WorkDirInGitTree()
    return parent


def _git_bytes(repo: Path, *arguments: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(repo), *arguments], capture_output=True, check=True,
        timeout=15, env=_git_environment(),
    ).stdout


def read_exclusions(repo: Path, list_commit: str) -> tuple[list[tuple[str, str]], str, str]:
    path = CALIBRATION.parent / "exclusions.txt"
    try:
        commit = _git_bytes(repo, "rev-parse", f"{list_commit}^{{commit}}").decode().strip()
        blob = _git_bytes(repo, "rev-parse", f"{commit}:{path}").decode().strip()
        text = _git_bytes(repo, "cat-file", "blob", blob).decode("utf-8")
    except (OSError, subprocess.SubprocessError, UnicodeError) as exc:
        raise Refusal(f"leak:{path}") from exc
    entries = []
    for line in text.splitlines():
        line = line.partition("#")[0].strip()
        if not line:
            continue
        words = line.split(maxsplit=1)
        valid = len(words) == 2 and words[0] in ("dir", "name-contains")
        if valid and words[0] == "dir":
            value = Path(words[1])
            valid = not value.is_absolute() and bool(value.parts) and ".." not in value.parts
        if not valid:  # M:GAS-LEAK-LIST-GRAMMAR
            raise Refusal(f"leak:{path}")
        entries.append((words[0], words[1]))
    return entries, commit, blob


def placements(doc: str, sources: dict[str, str]) -> dict[str, str]:
    """Map a target and exactly its assembler pairs to their committed blobs."""
    if not re.fullmatch(r"d[1-9][0-9]*", doc):
        raise ValueError("unknown document")
    feature_index, phase_index = divmod(int(doc[1:]) - 1, 3)
    feature, directory = list(sources.items())[feature_index]
    phase = ("plan", "design", "impl-plan")[phase_index]
    name = f"{feature}.{phase}.md"
    live_directory = "docs/02-design/features" if phase == "design" else "docs/01-plan/features"
    selected = {f"{live_directory}/{name}": f"{CALIBRATION}/seeded/{name}"}
    for paired_phase in {"plan": ("spec",), "design": ("spec", "plan"),
                         "impl-plan": ("design",)}[phase]:
        paired_directory = "docs/02-design/features" if paired_phase == "design" else "docs/01-plan/features"
        paired_name = f"{feature}.{paired_phase}.md"
        selected[f"{paired_directory}/{paired_name}"] = f"{directory}/{feature}/{paired_name}"
    return selected


def _root_entries(root: Path) -> list[Path]:
    paths = []
    for directory, directories, files in os.walk(root, followlinks=False):
        paths.extend(Path(directory) / name for name in directories + files)
    return sorted(paths, key=lambda path: path.relative_to(root).as_posix())


def scan_root(root: Path, ledger: list[dict], sources: dict[str, str], doc: str) -> None:
    selected = placements(doc, sources)
    for path in _root_entries(root):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():  # M:GAS-LEAK-SYMLINK
            raise Refusal(f"leak:{relative}")
        if not path.is_file():
            continue
        data = path.read_bytes()
        text = normalise(data)
        digest = hashlib.sha256(data).hexdigest()
        for record in ledger:
            # The digest is captured from the validated archive before exclusions.
            exempt = (selected.get(relative) == record["source"] and digest == record.get("_source_sha256"))  # M:GAS-LEAK-EXEMPT-SHA
            if normalise(record["original"].encode("utf-8")) in text:  # M:GAS-LEAK-ORIGINAL
                if not exempt:
                    raise Refusal(f"leak:{relative}")
            if normalise(record["expected"].encode("utf-8")) in text:  # M:GAS-LEAK-EXPECTED
                raise Refusal(f"leak:{relative}")  # M:GAS-LEAK-EXEMPT-ORIGINAL-ONLY


def reach_check(root: Path) -> None:
    for path in _root_entries(root):
        if path.name == ".git":  # M:GAS-REACH-DOTGIT
            raise Refusal(f"root_git:{path.relative_to(root).as_posix()}")
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--absolute-git-dir"],
        capture_output=True, text=True, timeout=15, env=_git_environment(),
    )
    if result.returncode == 0:  # M:GAS-REACH-REVPARSE
        raise Refusal(f"root_git:{result.stdout.strip()}")


def _extract_archive(archive: bytes, tree: Path) -> None:
    try:
        with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
            bundle.extractall(tree, filter="data")  # M:GAS-LEAK-TAR
    except tarfile.FilterError as exc:
        raise Refusal(f"leak:{exc.tarinfo.name}") from exc


def _remove_tree(path: Path) -> None:
    if stat.S_ISDIR(os.lstat(path).st_mode):
        shutil.rmtree(path)
    else:
        os.unlink(path)


def _build_root(args: argparse.Namespace, *, step6: bool = True) -> tuple[str, list[dict]]:
    entries, list_commit, list_blob = read_exclusions(args.repo, args.list_commit)
    try:
        calibration = _git_bytes(args.repo, "rev-parse", f"{args.calibration_sha}^{{commit}}").decode().strip()
        archive = _git_bytes(args.repo, "archive", "--format=tar", calibration)
    except (OSError, subprocess.SubprocessError) as exc:
        raise Refusal(f"calibration_ref:sha_unknown:{args.calibration_sha}") from exc
    with tempfile.TemporaryDirectory(prefix="gas-ledger-", dir=args.work_dir) as directory:  # M:GAS-SCRATCH-LEDGER-TREE
        tree = Path(directory)
        _extract_archive(archive, tree)
        check_ledger(tree, args.sources)
        ledger = read_ledger(tree)
        for record in ledger:
            record["_source_sha256"] = hashlib.sha256((tree / record["source"]).read_bytes()).hexdigest()

    root = Path(tempfile.mkdtemp(prefix=f"gas-root-{args.doc}-{args.purpose}-", dir=args.dest_parent or args.work_dir)).resolve()  # M:GAS-SCRATCH-ROOT
    try:
        _extract_archive(archive, root)
        absent = 0
        for kind, value in entries:
            def matches(path: Path) -> bool:
                relative = path.relative_to(root).as_posix()
                return (relative == value or relative.startswith(value + "/")) if kind == "dir" else value in path.name

            paths = [path for path in _root_entries(root) if matches(path)]
            absent += not bool(paths)
            for path in reversed(paths):
                if path.is_symlink() or path.is_file():
                    path.unlink()
                elif path.is_dir():
                    _remove_tree(path)
            for path in _root_entries(root):
                if matches(path):
                    raise Refusal(f"leak:{path.relative_to(root).as_posix()}")
        for live, source in placements(args.doc, args.sources).items():
            path = root / live
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(_git_bytes(args.repo, "cat-file", "blob", f"{calibration}:{source}"))
        if step6:
            scan_root(root, ledger, args.sources, args.doc)
            reach_check(root)
    except Exception:
        _remove_tree(root)
        raise
    line = (f"ROOT: READY doc={args.doc} purpose={args.purpose} path={root} "
            f"calibration={calibration} list_commit={list_commit} list_blob={list_blob} absent={absent}")
    return line, ledger


def build_root(args: argparse.Namespace) -> str:
    return _build_root(args)[0]


def check_reset_target(target: str, doc: str) -> Path:
    if not os.path.isabs(target):  # M:GAS-RESET-ABS
        raise ResetTargetNotAbsolute()
    if not os.path.isdir(target):  # M:GAS-RESET-ISDIR
        raise ResetTargetNotDirectory()
    root = Path(target).resolve()
    if any(root.is_relative_to(Path(directory).resolve()) for directory in {tempfile.gettempdir(), "/tmp", "/private/tmp"}):  # M:GAS-RESET-TMPDIR
        raise ResetTargetInSystemTemp()
    if root.parent.name != "roots":  # M:GAS-RESET-ROOTS
        raise ResetTargetOutsideRoots()
    if not root.name.startswith(f"gas-root-{doc}-s1-"):  # M:GAS-RESET-PREFIX
        raise ResetTargetPrefix()
    reach_check(root)  # M:GAS-RESET-REACH
    return root


def remove_absent(live: Path, expected: Path) -> int:
    expected_modes = {path.relative_to(expected): stat.S_IFMT(os.lstat(path).st_mode)
                      for path in _root_entries(expected)}
    removed = 0
    # Children first: count every removed path, including directories, without
    # losing entries when their containing directory is removed.
    for path in reversed(_root_entries(live)):
        mode = os.lstat(path).st_mode
        if stat.S_ISLNK(mode):
            os.unlink(path)  # M:GAS-RESET-NOFOLLOW-REMOVE
        elif expected_modes.get(path.relative_to(live)) != stat.S_IFMT(mode):
            _remove_tree(path)  # M:GAS-RESET-REMOVE
        else:
            continue
        removed += 1
    return removed


def restore_expected(live: Path, expected: Path) -> int:
    live.mkdir(exist_ok=True)
    restored = 0
    for source in _root_entries(expected):
        relative = source.relative_to(expected)
        source_mode = os.lstat(source).st_mode
        is_directory = stat.S_ISDIR(source_mode)
        if not is_directory and not stat.S_ISREG(source_mode):
            raise RootResetMismatch()
        parent = live
        parts = relative.parts if is_directory else relative.parts[:-1]
        for part in parts:
            parent = parent / part
            try:
                mode = os.lstat(parent).st_mode
            except FileNotFoundError:
                parent.mkdir()
            else:
                if not stat.S_ISDIR(mode):  # M:GAS-RESET-NOFOLLOW-PARENT
                    os.unlink(parent)
                    parent.mkdir()
        if is_directory:
            continue
        path = live / relative
        data = source.read_bytes()
        try:
            mode = os.lstat(path).st_mode
        except FileNotFoundError:
            mode = 0
        if stat.S_ISREG(mode) and path.read_bytes() == data:
            continue
        if stat.S_ISDIR(mode):
            _remove_tree(path)
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o666)  # M:GAS-RESET-NOFOLLOW-WRITE
        except OSError as exc:
            if exc.errno != errno.ELOOP:
                raise
            os.unlink(path)
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o666)
        with os.fdopen(fd, "wb") as output:
            output.write(data)
        restored += 1
    return restored


def rewalk_matches(live: Path, expected: Path) -> None:
    def manifest(root: Path) -> dict:
        result = {}
        for path in _root_entries(root):
            mode = os.lstat(path).st_mode
            digest = hashlib.sha256(path.read_bytes()).digest() if stat.S_ISREG(mode) else None
            result[path.relative_to(root)] = (stat.S_IFMT(mode), digest)
        return result

    actual = manifest(live)
    matches = actual == manifest(expected) and all(
        mode in (stat.S_IFDIR, stat.S_IFREG) for mode, _ in actual.values()
    )
    if not matches:  # M:GAS-RESET-REWALK
        raise RootResetMismatch()


def reset_root(args: argparse.Namespace) -> str:
    if args.dest_parent is not None:  # M:GAS-RESET-EXCLUSIVE
        raise ResetArgsConflict()
    if args.purpose != "s1":  # M:GAS-RESET-PURPOSE
        raise ResetPurposeNotS1()
    live = check_reset_target(args.reset, args.doc)
    line, ledger = _build_root(args, step6=False)
    fields = parse_root_line(line)
    expected = Path(fields["path"])
    try:
        removed = remove_absent(live, expected)
        restored = restore_expected(live, expected)
        rewalk_matches(live, expected)
        scan_root(live, ledger, args.sources, args.doc)  # M:GAS-RESET-SCAN
        reach_check(live)  # M:GAS-RESET-STEP6-REACH
    finally:
        _remove_tree(expected)
    fields["path"] = str(live)
    print(f"RESET: removed={removed} restored={restored}")
    return "ROOT: READY " + " ".join(f"{key}={value}" for key, value in fields.items())


def parse_root_line(line: str) -> dict[str, str] | None:
    if not line.startswith("ROOT: READY "):
        return None
    fields = {}
    for word in line.split()[2:]:
        key, separator, value = word.partition("=")
        if not separator or not value or key in fields:
            return None
        fields[key] = value
    required = {"doc", "purpose", "path", "calibration", "list_commit", "list_blob", "absent"}
    if fields.keys() != required:  # M:GAS-PARSE-ROOT
        return None
    return fields


def parse_run_line(text: str) -> dict[str, str] | None:
    """Parse the single runbook checkout/home authority line."""
    lines = [line for line in text.splitlines() if line.startswith("RUN: ")]
    if len(lines) != 1:  # M:GAS-PARSE-RUN-ONE
        return None
    fields = {}
    words = re.split(r"\s+(?=(?:checkout|home)=)", lines[0][len("RUN: "):])
    for word in words:
        key, separator, value = word.partition("=")
        if not separator or not value:
            return None
        if key in fields:  # M:GAS-PARSE-RUN-DUP
            return None
        if re.search(r"\s+[A-Za-z0-9_-]+=\S+", value):  # M:GAS-PARSE-RUN
            return None
        fields[key] = value.strip()
    if fields.keys() != {"checkout", "home"}:  # M:GAS-PARSE-RUN
        return None
    return fields


def parse_profile_line(text: str) -> dict[str, str] | None:
    """Parse the single exec profile and its provenance."""
    lines = [line for line in text.splitlines() if line.startswith("GROK-PROFILE: ")]
    if len(lines) != 1:
        return None
    fields = {}
    for word in lines[0][len("GROK-PROFILE: "):].split():
        key, separator, value = word.partition("=")
        if not separator or not value or key in fields:
            return None
        fields[key] = value
    if fields.keys() != {"profile", "origin"}:  # M:GAS-PARSE-PROFILE
        return None
    if fields.get("origin") not in {"default", "override"}:  # M:GAS-PARSE-PROFILE-ORIGIN
        return None
    return fields


def _mode_build_root(args: argparse.Namespace) -> int:
    print(reset_root(args) if args.reset is not None else build_root(args))
    return 0


MODES["build-root"] = _mode_build_root


def record_cycle(args: argparse.Namespace) -> str:
    """Validate one wrapper run before copying its D3 recording files."""
    pass_records = args.pass_root_record
    if args.root_record is not None and pass_records:  # M:GAS-RECORD-FORMS-BOTH
        raise UsageError("choose one root-record form")
    if args.root_record is None and not pass_records:  # M:GAS-RECORD-FORMS-NEITHER
        raise UsageError("a root-record form is required")
    records = pass_records or ([args.root_record] if args.root_record is not None else [])
    contents = {path: b"" for path in (*records, args.stdout, args.command)}
    missing = [path for path in (args.stem, args.root) if not path.is_dir()]
    for path in contents:
        try:
            contents[path] = path.read_bytes()
        except OSError:
            missing.append(path)
    if missing:  # M:GAS-RECORD-INPUT
        raise Refusal(f"input_missing:{missing[0]}")

    root_records, pass_roots = {}, []
    for index, record in enumerate(records, 1):  # M:GAS-RECORD-PASS-LOOP
        lines = [line for line in contents[record].decode("utf-8", errors="replace").splitlines()
                 if line.startswith("ROOT: READY ")]
        if len(lines) != 1:  # M:GAS-RECORD-ROOT-LINE
            raise Refusal("root_record:no_line")
        root_line = next(iter(lines), "")
        fields = parse_root_line(root_line)
        if fields is None:
            raise Refusal("root_record:no_line")  # M:GAS-RECORD-ROOT-MALFORMED
        if index == 1 and Path(fields["path"]).resolve() != args.root.resolve():  # M:GAS-RECORD-ROOT-PATH  # M:GAS-RECORD-PASS-PATH
            raise Refusal("root_record:path_mismatch")
        name = f"p{index}.root.txt" if pass_records else "root.txt"  # M:GAS-RECORD-PASS-NAME
        root_records[name] = (root_line + "\n").encode("utf-8")
        pass_roots.append(Path(fields["path"]))
    stdout_lines = contents[args.stdout].decode("utf-8", errors="replace").splitlines()
    if not any(line.startswith("AUDITCYCLE: ") for line in stdout_lines):  # M:GAS-RECORD-AUDITCYCLE
        raise Refusal(f"no_auditcycle_line:{args.stdout}")

    flags = ("--feature", "--phase", "--cycle")
    values = dict.fromkeys(flags, "")
    try:
        words = shlex.split(contents[args.command].decode("utf-8"))
        seen = set()
        for index, word in enumerate(words):
            flag, separator, value = word.partition("=")
            if flag not in values:
                continue
            if flag in seen:
                raise ValueError("repeated cycle flag")
            seen.add(flag)
            values[flag] = value if separator else words[index + 1]
    except (ValueError, IndexError, UnicodeError):
        values = dict.fromkeys(flags, "")
    feature, phase, cycle = (values[flag] for flag in flags)
    valid_command = (bool(feature) and not feature.startswith("--")
                     and phase in ("plan", "design", "impl-plan")
                     and re.fullmatch(r"[1-9][0-9]*", cycle))
    if not valid_command:  # M:GAS-RECORD-COMMAND
        raise Refusal(f"command_unparseable:{args.command}")

    stem_pattern = re.compile(
        re.escape(f"audit_{feature}_{phase}_cycle{cycle}_run")
        + r"(.+)_p([1-9][0-9]*)(\.txt|\.asm\.txt|\.out\.txt|\.log|\.report\.md|\.log\.profile)"  # M:GAS-RECORD-PROFILE
    )
    stem_files = [(path, stem_pattern.fullmatch(path.name)) for path in sorted(args.stem.iterdir())
                  if path.is_file()]
    prefixes = {match[1] for _path, match in stem_files if match is not None}
    if len(prefixes) != 1:  # M:GAS-RECORD-STEM-PREFIX
        raise Refusal(f"stem_prefix:{len(prefixes)}")
    prefix = next(iter(sorted(prefixes)), "")
    copies = {}
    for source, match in stem_files:
        if match is not None and match[1] == prefix:
            suffix = {".txt": ".prompt.txt", ".log.profile": ".profile.txt"}.get(match[3], match[3])
            copies[f"p{match[2]}{suffix}"] = source

    report_roots = {int(match[2]): args.root for _source, match in stem_files if match is not None}
    if pass_records:
        report_roots = dict(enumerate(pass_roots, 1))
    stem_name = f"audit_{feature}_{phase}_cycle{cycle}_run{prefix}"
    for index, root in report_roots.items():
        report = root / ".hmad-report" / f"{stem_name}_p{index}.report.md"
        if report.is_file():  # M:GAS-RECORD-PASS-REPORT
            copies[f"p{index}.report.md"] = report

    report_name = re.escape(f"{feature}.{phase}.audit.v{cycle}") + r"\.p[1-9][0-9]*\.md"
    report_dir = "docs/02-design/features" if phase == "design" else "docs/01-plan/features"
    for directory, destination, pattern in (
        (args.root / report_dir, "collected", report_name + r"(?:\.effort\.json)?"),
        (args.root / ".h-mad/pass-logs", "pass-logs", report_name + r"\.log"),
    ):
        if directory.is_dir():
            for source in sorted(directory.iterdir()):
                if source.is_file() and re.fullmatch(pattern, source.name):
                    copies[f"{destination}/{source.name}"] = source

    # Read every selected source before creating any destination file.
    recorded = {**root_records,
                "command.txt": contents[args.command], "auditcycle.txt": contents[args.stdout]}
    for destination, source in copies.items():
        try:
            recorded[destination] = source.read_bytes()
        except OSError as exc:
            raise Refusal(f"input_missing:{source}") from exc
    args.dest.mkdir(parents=True, exist_ok=True)
    for relative, data in recorded.items():
        path = args.dest / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    count = sum(path.is_file() for path in args.dest.rglob("*"))
    return f"RECORD: OK dest={args.dest.resolve()} files={count}"


def _git(repo: Path, *argv: str, env: dict[str, str] | None = None,
         stdin: bytes | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *argv], input=stdin, capture_output=True,
        timeout=15, env=_git_environment() if env is None else env,
    )


def commit_data(args: argparse.Namespace) -> str:
    """Publish calibration blobs using a private index and an expected-old ref."""
    ref = "refs/heads/calibration/grok-audit-surface"
    parent = _git(args.repo, "rev-parse", "--verify", f"{args.parent}^{{commit}}")
    if parent.returncode != 0:  # M:GAS-COMMIT-PARENT
        raise Refusal(f"parent_unknown:{args.parent}")
    parent_oid = parent.stdout.decode().strip()
    current = _git(args.repo, "rev-parse", "--verify", ref)
    old = current.stdout.decode().strip() if current.returncode == 0 else ""
    if old and old != parent_oid:  # M:GAS-COMMIT-REF-MOVED
        raise Refusal(f"ref_moved:{old}")

    sources = []
    for path in sorted(args.src.rglob("*")):
        if not path.resolve().is_relative_to(args.src.resolve()):  # M:GAS-COMMIT-OUTSIDE
            raise Refusal(f"outside_calibration_dir:{path}")
        if path.is_file():
            sources.append((path, CALIBRATION / path.relative_to(args.src)))
    try:
        parent_tree = _git(args.repo, "ls-tree", "-r", "-z", parent_oid, "--", CALIBRATION.as_posix())
        parent_tree.check_returncode()
        parent_blobs = {}
        for entry in parent_tree.stdout.split(b"\0"):
            if not entry:
                continue
            metadata, name = entry.split(b"\t", 1)
            _mode, kind, oid = metadata.split()
            if kind == b"blob":
                parent_blobs[os.fsdecode(name)] = oid.decode()
        additions = []
        for path, destination in sources:
            blob = _git(args.repo, "hash-object", "-w", "--stdin", stdin=path.read_bytes())
            blob.check_returncode()
            oid = blob.stdout.decode().strip()
            previous = parent_blobs.get(destination.as_posix())
            relative = path.relative_to(args.src)
            authoring = relative == Path("ledger.jsonl") or relative.as_posix().startswith("seeded/")  # M:GAS-COMMIT-AUTHORING
            if previous is not None and previous != oid and not authoring:  # M:GAS-COMMIT-REPLACE
                raise Refusal(f"would_replace:{destination.as_posix()}")
            if previous != oid:
                additions.append((destination, oid))
        with tempfile.TemporaryDirectory(prefix="gas-commit-") as directory:
            environment = _git_environment()
            environment["GIT_INDEX_FILE"] = str(Path(directory) / "index")
            _git(args.repo, "read-tree", parent_oid, env=environment).check_returncode()
            for destination, oid in additions:
                _git(args.repo, "update-index", "--add", "--cacheinfo", "100644",
                     oid, destination.as_posix(),
                     env=environment).check_returncode()
            tree = _git(args.repo, "write-tree", env=environment)
            tree.check_returncode()
            commit = _git(args.repo, "commit-tree", tree.stdout.decode().strip(),
                          "-p", parent_oid, "-m", args.message)
            commit.check_returncode()
            new = commit.stdout.decode().strip()
            _git(args.repo, "update-ref", ref, new, old).check_returncode()
    except subprocess.CalledProcessError as exc:
        raise Refusal("ref_unconfirmed") from exc
    confirmed = _git(args.repo, "rev-parse", "--verify", ref)
    if confirmed.returncode != 0 or confirmed.stdout.decode().strip() != new:  # M:GAS-COMMIT-REREAD
        raise Refusal("ref_unconfirmed")
    return f"COMMIT: OK sha={new} ref={ref}"


def _mode_record_cycle(args: argparse.Namespace) -> int:
    print(record_cycle(args))
    return 0


def _mode_commit_data(args: argparse.Namespace) -> int:
    print(commit_data(args))
    return 0


MODES["record-cycle"] = _mode_record_cycle
MODES["commit-data"] = _mode_commit_data


AUDITCYCLE_RE = re.compile(r"^AUDITCYCLE: (PASS|FAIL|UNVERIFIED)( \S+)*$")
GROK_ITEM_RE = re.compile(r"^p1 tools=\d+ ok=\d+ unresolved=\d+ thinking=\d+ format=grok( |$)")
COUNTS_ITEM_RE = re.compile(r"^p1 tools=\d+ ok=\d+ failed=\d+ thinking=\d+( |$)")


def parse_auditcycle(text: str) -> dict | None:
    lines = [line for line in text.split("\n") if line.startswith("AUDITCYCLE:")]
    if len(lines) != 1:  # M:GAS-PARSE-AUDITCYCLE-ONE
        return None
    if not AUDITCYCLE_RE.fullmatch(lines[0]):
        return None
    words = lines[0].split()
    parsed = {"verdict": words[1]}
    for word in words[2:]:
        key, separator, value = word.partition("=")
        if separator:
            parsed[key] = value
    # S1 has one pass. Retain its report basename to name a missing collected copy;
    # the recorded absolute path still names the original export root.
    for line in text.split("\n"):
        if line.startswith("reports: "):
            parsed["report_name"] = Path(line.removeprefix("reports: ")).name
    return parsed


def parse_effort_items(text: str) -> list[str] | None:
    lines = text.split("\n")
    starts = [index for index, line in enumerate(lines) if line == "Effort:"]
    if len(starts) > 1:  # M:GAS-PARSE-EFFORT-TWICE
        return None
    if not starts:
        return []
    items = []
    for line in lines[starts[0] + 1:]:
        if not line.startswith("- "):
            break
        item = line[2:]
        if not re.match(r"^p\d+ ", item):  # M:GAS-PARSE-EFFORT-ITEM
            return None
        items.append(item)
    if not items:  # M:GAS-PARSE-EFFORT-EMPTY
        return None
    return items


def grok_log_types(text: str) -> dict[str, list[dict]]:
    events: dict[str, list[dict]] = {}
    for line in text.split("\n"):
        try:
            event = json.loads(line)
        except (ValueError, RecursionError):
            continue
        if isinstance(event, dict) and isinstance(event.get("type"), str):
            events.setdefault(event["type"], []).append(event)
    return events


def effort_form(item: str) -> str:
    if GROK_ITEM_RE.match(item):
        return "grok"
    if item.startswith("p1 not measured (grok log truncated"):
        return "truncated"
    if COUNTS_ITEM_RE.match(item):
        return "counts"
    if (item == "p1 unreadable (log named but not readable)"
            or item.startswith("p1 not measured (codex-text log")):
        return "wrong-file"
    return "unknown"


def _smoke_read(path: Path) -> str:
    global _OPEN_INPUT
    _OPEN_INPUT = str(path)
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        if True:  # M:GAS-SMOKE-MISSING-AUDITCYCLE
            raise Refusal(f"input_missing:{path}") from exc
        return ""
    except UnicodeError as exc:
        raise Refusal(f"input_unparseable:{path}") from exc


def vocab_sets(vocab_py: Path, vocab_sh: Path) -> tuple[frozenset[str], frozenset[str]]:
    global _OPEN_INPUT
    _OPEN_INPUT = str(vocab_py)
    try:
        spec = importlib.util.spec_from_file_location("_gas_vocab_py", vocab_py)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        py_types = module._GROK_TYPES
        if not isinstance(py_types, frozenset) or not all(isinstance(t, str) for t in py_types):
            raise ValueError("expected a string frozenset")
    except (OSError, ValueError, TypeError, AttributeError, SyntaxError, ImportError) as exc:
        raise Refusal(f"input_unparseable:{vocab_py}") from exc
    try:
        text = _smoke_read(vocab_sh)
        match = re.search(r"^_GROK_TYPES_RE=['\"]([^'\"\n]*)['\"]$", text, re.MULTILINE)
        if match is None:
            raise ValueError("missing vocabulary regexp")
        sh_types = frozenset(match[1].split("|"))
    except (ProbeRefusal, ValueError) as exc:
        raise Refusal(f"input_unparseable:{vocab_sh}") from exc
    return py_types, sh_types


def delivered(cycle_dir: Path, parsed: dict) -> bool:
    global _OPEN_INPUT
    delivery = parsed.get("delivered", "").split(",")[0]
    if delivery not in ("report-file", "out"):  # M:GAS-SMOKE-DELIVERED
        return False
    reports = sorted((cycle_dir / "collected").glob("*.p1.md"))
    report = (reports[0] if reports else
              cycle_dir / "collected" / parsed.get("report_name", "p1.md"))
    if not report.is_file():  # M:GAS-SMOKE-MISSING-COLLECTED
        raise Refusal(f"input_missing:{report}")
    _OPEN_INPUT = str(report)
    try:
        result = subprocess.run(
            [sys.executable, str(REPO / "h-mad/scripts/h_mad_audit_gate.py"), str(report)],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode not in (0, 2):
            raise _cycle.OperationalError("audit gate did not run")
        verdict, _must, _should = _cycle._gate_token(result.stdout, report)
    except (OSError, UnicodeError, subprocess.SubprocessError, _cycle.OperationalError) as exc:
        raise Refusal(f"input_unparseable:{report}") from exc
    return verdict in ("PASS", "FAIL")


def _event_keys(value: object, depth: int = 2) -> list[str]:
    if depth == 0:
        return []
    if isinstance(value, dict):
        return [str(key).lower() for key in value] + [
            key for child in value.values() for key in _event_keys(child, depth - 1)
        ]
    if isinstance(value, list):
        return [key for child in value for key in _event_keys(child, depth - 1)]
    return []


def smoke(data: Path, vocab_py: Path, vocab_sh: Path) -> tuple[list[str], str]:
    cycles = {}
    deliveries = {}
    types = {}
    form = "unknown"
    for surface in ("grok", "agy", "codex"):
        directory = data / surface
        if surface == "codex" and not directory.exists():
            continue
        audit = directory / "auditcycle.txt"
        text = _smoke_read(audit)
        parsed = parse_auditcycle(text)
        if parsed is None:  # M:GAS-SMOKE-UNPARSEABLE-AUDITCYCLE
            raise Refusal(f"input_unparseable:{audit}")
        parsed = parsed or {}
        cycles[surface] = parsed
        if surface == "grok":
            items = parse_effort_items(text)
            if items is None:  # M:GAS-SMOKE-EFFORT-MALFORMED
                raise Refusal(f"input_unparseable:{audit}")
            if "delivered" in parsed:
                log = directory / "p1.log"
                types = grok_log_types(_smoke_read(log))
                if not types:
                    raise Refusal(f"input_unparseable:{log}")
                item = next((item for item in (items or []) if item.startswith("p1 ")), "")
                form = effort_form(item)
                if form in ("grok", "truncated"):
                    pass
                elif form == "counts":  # M:GAS-SMOKE-EFFORT-COUNTS
                    if {"end", "tool_call", "tool_call_update"} <= types.keys():  # M:GAS-SMOKE-EFFORT-NONGROK-CONTRADICTED
                        raise Refusal(f"input_unparseable:{audit}")
                elif item.startswith("p1 not measured (codex-text log"):
                    if True:  # M:GAS-SMOKE-EFFORT-CODEX-TEXT
                        raise Refusal(f"input_unparseable:{audit}")
                elif item == "p1 unreadable (log named but not readable)":
                    if True:  # M:GAS-SMOKE-EFFORT-UNREADABLE
                        raise Refusal(f"input_unparseable:{audit}")
                else:
                    if True:  # M:GAS-SMOKE-EFFORT-UNKNOWN
                        raise Refusal(f"input_unparseable:{audit}")
        deliveries[surface] = delivered(directory, parsed)
    py_types, sh_types = vocab_sets(vocab_py, vocab_sh)
    accepts = {surface: deliveries[surface] and parsed.get("verdict") != "UNVERIFIED"
               for surface, parsed in cycles.items()}
    reasons = []
    if form == "truncated":  # M:GAS-SMOKE-TRUNCATED
        reasons.append("truncated")
    if py_types != sh_types:  # M:GAS-SMOKE-VOCAB-SPLIT
        reasons.append("vocab_split")
    for kind in ("end", "tool_call", "tool_call_update"):
        if kind not in types:  # M:GAS-SMOKE-VOCAB-MISSING
            reasons.append(f"vocab_missing:{kind}")
    if not deliveries["grok"]:  # M:GAS-SMOKE-NO-DELIVERY
        reasons.append("no_delivery")
    for surface in ("grok", "agy"):
        if not accepts[surface]:  # M:GAS-SMOKE-ACCEPTS
            reasons.append(f"nongit_root_refused:{surface}")

    lines = []
    for kind, events in sorted(types.items()):
        keys = [key for event in events for key in _event_keys(event)]
        tool = any("tool" in key for key in keys)
        usage = any("usage" in key or "token" in key for key in keys)
        lines.append(f"VOCAB: type={kind} re={'in' if kind in sh_types else 'out'} "
                     f"frozenset={'in' if kind in py_types else 'out'} "
                     f"tool={'yes' if tool else 'no'} usage={'yes' if usage else 'no'}")
    if "delivered" not in cycles["grok"]:
        lines.append("VOCAB: none reason=no_grok_dispatch")
    lines.append("ROOT-ACCEPT: " + " ".join(
        f"{surface}={'not_run' if surface not in accepts else 'accepted' if accepts[surface] else 'refused'}"
        for surface in ("grok", "agy", "codex")))
    try:
        wall = int(_smoke_read(data / "grok/wall_seconds.txt").strip())
        lines.append(f"TIMEOUT: wall_seconds={wall} derived={max(900, math.ceil(1.5 * wall / 60) * 60)}")
    except (ProbeRefusal, ValueError, OverflowError):
        lines.append("TIMEOUT: wall_seconds=unrecorded")
    binary = "GROK-BINARY: unrecorded"
    try:
        first = _smoke_read(data / "versions.txt").split("\n")[0]
        if first.startswith("grok_binary="):
            path, separator, version = first.removeprefix("grok_binary=").partition(" ")
            if separator and Path(path).is_absolute() and version:
                binary = f"GROK-BINARY: path={path} version={version}"
    except ProbeRefusal:
        pass
    lines.append(binary)
    token = "SMOKE: FAIL reason=" + ",".join(reasons) if reasons else "SMOKE: PASS"
    return lines, token


def _mode_smoke(args: argparse.Namespace) -> int:
    lines, token = smoke(args.data, args.vocab_py, args.vocab_sh)
    for line in lines:
        print(line)
    print(token)
    return 0


MODES["smoke"] = _mode_smoke


def report_findings(text: str) -> dict[str, list[str]]:
    """Preserve finding spans while following the gate's section decisions."""
    sections = {key: [] for key in _gate.BLOCKING_SECTIONS.values()}
    current = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped in _gate.BLOCKING_SECTIONS:
            current = _gate.BLOCKING_SECTIONS[stripped]
        elif stripped.startswith("## "):
            current = None
        elif current and stripped:
            sections[current].append(line)

    found = {"must": [], "should": []}
    for key, content in sections.items():
        payloads = [_gate._payload(line) for line in content]
        if all(_gate._is_none_sentinel(payload) for payload in payloads):
            continue
        findings = found[key.removesuffix("_count")]
        for group in _gate._bullet_groups(content):
            if _gate._collapses(group, set()):  # M:GAS-COLLAPSE-WIRE
                findings.append("\n".join(group["lines"]))
            else:
                flat = iter(_gate._flat_findings(group["lines"]))
                span = None
                for line in group["lines"]:
                    if _gate._bullet_remainder(line.strip()) is not None:
                        if span is not None:
                            findings.append("\n".join(span))
                        payload = _gate._payload(line)
                        span = None
                        if payload and not _gate._is_none_sentinel(payload):
                            next(flat)
                            span = [line]
                    elif span is not None:
                        span.append(line)
                if span is not None:
                    findings.append("\n".join(span))
        if not findings:
            findings.append("\n".join(content))
    return found


def extract_report(text: str, report: str) -> tuple[list[str], list[str], int, int]:
    found = report_findings(text)
    must, should = found["must"], found["should"]
    _counts = _gate.classify(text)
    must_count = _counts["must_count"]  # M:GAS-MUST-COUNT-WIRE
    should_count = _counts["should_count"]  # M:GAS-SHOULD-COUNT-WIRE
    if len(must) != must_count:
        raise Refusal(f"must_count_mismatch:{report}")
    if len(should) != should_count:
        print(f"SHOULD-COUNT: {report} walk={len(should)} gate={should_count}")
    return must, should, must_count, should_count


def _recorded_cycle(directory: Path) -> dict:
    reason = f"cycle_token:{directory.parent.name}.{directory.name}"
    try:
        text = (directory / "auditcycle.txt").read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        text = ""
    lines = [line for line in text.splitlines() if line.startswith("AUDITCYCLE:")]
    parsed = parse_auditcycle(text)
    if not lines:  # M:GAS-CYCLE-NO-LINE
        raise Refusal(reason)
    if lines and parsed is None:  # M:GAS-CYCLE-UNPARSEABLE
        raise Refusal(reason)
    return parsed or {}


def stands(doc_dir: Path) -> Path:
    """Choose the whole recorded cycle, using only the wrapper's verdict."""
    for directory in sorted(doc_dir.glob("v*")):
        match = re.fullmatch(r"v(\d+)", directory.name)
        if match and int(match[1]) >= 3:  # M:GAS-CYCLE-V3
            raise Refusal(f"cycle_token:{doc_dir.name}.{directory.name}")
    v1, v2 = doc_dir / "v1", doc_dir / "v2"
    parsed = _recorded_cycle(v1)
    standing = v1
    if parsed.get("verdict") == "UNVERIFIED":  # M:GAS-STANDS-V1-UNVERIFIED
        if not v2.is_dir():  # M:GAS-CYCLE-V2-MISSING
            raise Refusal(f"cycle_token:{doc_dir.name}.v2")
        if v2.is_dir():
            standing = v2
    elif v2.exists():  # M:GAS-CYCLE-V2-EXTRA
        raise Refusal(f"cycle_token:{doc_dir.name}.v2")
    return standing


def containment_checks(s2_dir: Path, sources: dict[str, str]) -> None:
    run_record = s2_dir / "run.txt"
    try:
        run_fields = parse_run_line(run_record.read_text(encoding="utf-8"))
    except (OSError, UnicodeError):
        run_fields = None
    if run_fields is None:  # M:GAS-CONTAIN-RUN-RECORD
        raise Refusal("list_changed:unrecorded")  # M:GAS-CONTAIN-RUN-RECORD
    cycles = []
    for index in range(1, len(sources) * 3 + 1):
        doc_dir = s2_dir / f"d{index}"
        for cycle in sorted(doc_dir.glob("v*"), key=lambda path: int(path.name[1:])):
            reason = f"cycle_token:{doc_dir.name}.{cycle.name}"
            try:
                command = shlex.split((cycle / "command.txt").read_text(encoding="utf-8"))
                surfaces = command[command.index("--surfaces") + 1].split(",")
                passes = int(command[command.index("--passes") + 1])
            except (OSError, UnicodeError, ValueError, IndexError):
                raise Refusal(reason)
            if passes != len(surfaces) or not surfaces:
                raise Refusal(reason)
            cycles.append((cycle, passes, reason, surfaces))

    recorded_roots = []
    for cycle, passes, reason, surfaces in cycles:
            roots = []
            for pass_index in range(1, passes + 1):
                record = cycle / f"p{pass_index}.root.txt"
                fields = None
                if record.is_file():
                    try:
                        lines = [parse_root_line(line) for line in record.read_text(encoding="utf-8").splitlines()
                                 if line.startswith("ROOT: READY ")]
                    except (OSError, UnicodeError):
                        lines = []
                    fields = lines[0] if len(lines) == 1 else None
                if fields is None:  # M:GAS-CONTAIN-ROOT-UNRECORDED
                    raise Refusal("list_changed:unrecorded")  # M:GAS-CONTAIN-ROOT-UNRECORDED
                roots.append(fields)
            recorded_roots.append((cycle, passes, reason, surfaces, roots))

    for cycle, passes, reason, surfaces, roots in recorded_roots:
            for record in cycle.glob("p*.root.txt"):
                match = re.fullmatch(r"p([1-9][0-9]*)\.root\.txt", record.name)
                if match and int(match[1]) > passes:  # M:GAS-CYCLE-ROOT-COUNT
                    raise Refusal(reason)
            paths = [Path(fields["path"]) for fields in roots]
            if len({str(path) for path in paths}) != len(paths):  # M:GAS-CYCLE-ROOT-SAME
                raise Refusal(reason)
            if any(left in right.parents or right in left.parents
                   for left_index, left in enumerate(paths)
                   for right in paths[left_index + 1:]):  # M:GAS-CYCLE-ROOT-NESTED
                raise Refusal(reason)
            if len({fields["calibration"] for fields in roots}) != 1:  # M:GAS-CYCLE-ROOT-CALIBRATION
                raise Refusal(reason)
            if len({fields["list_blob"] for fields in roots}) != 1:  # M:GAS-CYCLE-ROOT-LIST
                raise Refusal(reason)

    needles = [f"{directory}/{feature}" for feature, directory in sources.items()]
    cycles_to_scan = recorded_roots  # M:GAS-CONTAIN-EVERY-CYCLE
    for cycle, passes, reason, surfaces, roots in cycles_to_scan:
        for pass_index, surface in enumerate(surfaces, 1):
            if surface != "grok":  # M:GAS-CONTAIN-GROK-ONLY
                continue
            log = cycle / f"p{pass_index}.log"
            try:
                text = log.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                text = None
            root = roots[pass_index - 1]["path"]
            scan = h_mad_tool_calls.scan_log(text, "grok", root=root, checkout=run_fields["checkout"], home=run_fields["home"], needle_dirs=needles) if text is not None else {"word": "UNREADABLE"}  # M:GAS-CONTAIN-SCAN
            if scan["word"] == "OUT_OF_ROOT":  # M:GAS-CONTAIN-OUT-OF-ROOT
                raise Refusal(f"out_of_root:{cycle.parent.name}.{cycle.name}")
            if scan["word"] == "UNREADABLE":  # M:GAS-CONTAIN-UNREADABLE
                raise Refusal(f"out_of_root:{cycle.parent.name}.{cycle.name}")


def containment_lines(s2_dir: Path, sources: dict[str, str]) -> list[str]:
    try:
        run_fields = parse_run_line((s2_dir / "run.txt").read_text(encoding="utf-8"))
    except (OSError, UnicodeError):
        run_fields = None
    if run_fields is None:
        raise Refusal("list_changed:unrecorded")
    needles = [f"{directory}/{feature}" for feature, directory in sources.items()]
    lines = []
    for index in range(1, len(sources) * 3 + 1):
        doc = f"d{index}"
        cycle = stands(s2_dir / doc)
        try:
            command = shlex.split((cycle / "command.txt").read_text(encoding="utf-8"))
            surfaces = command[command.index("--surfaces") + 1].split(",")
        except (OSError, UnicodeError, ValueError, IndexError):
            raise Refusal(f"cycle_token:{doc}.{cycle.name}")
        for pass_index, surface in enumerate(surfaces, 1):
            root_record = cycle / f"p{pass_index}.root.txt"
            try:
                root_lines = [parse_root_line(line) for line in root_record.read_text(encoding="utf-8").splitlines()
                              if line.startswith("ROOT: READY ")]
            except (OSError, UnicodeError):
                root_lines = []
            roots = [fields for fields in root_lines if fields is not None]
            if len(roots) != 1:
                raise Refusal("list_changed:unrecorded")
            try:
                text = (cycle / f"p{pass_index}.log").read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                text = ""
            scan = h_mad_tool_calls.scan_log(text, surface, root=roots[0]["path"], checkout=run_fields["checkout"], home=run_fields["home"], needle_dirs=needles)  # M:GAS-CONTAIN-LINES
            tail = (f"mcp_unmeasured={scan['mcp_unmeasured']}" if surface == "codex"
                    else f"nonjson={scan['nonjson']}")
            line = (f"CONTAINMENT: {doc}.v{cycle.name[1:]} p{pass_index} surface={surface} scan={scan['word']} "
                    f"calls={scan['calls']} out_of_root={scan['out_of_root']} "
                    f"checkout={scan['checkout']} exempt={scan['exempt']} {tail}")
            if surface == "grok":
                profile_path = cycle / f"p{pass_index}.profile.txt"
                try:
                    profile = parse_profile_line(profile_path.read_text(encoding="utf-8"))
                except (OSError, UnicodeError):
                    profile = None
                line += (f" profile={profile['profile']} origin={profile['origin']}"
                         if profile else " profile=none")  # M:GAS-CONTAIN-PROFILE
            lines.append(line)
    return lines


def _standing_reports(s2_dir: Path, sources: dict[str, str]) -> list[dict]:
    reports = []
    for index in range(1, len(sources) * 3 + 1):
        doc = f"d{index}"
        directory = stands(s2_dir / doc)
        parsed = _recorded_cycle(directory)
        reason = f"cycle_token:{doc}.{directory.name}"
        try:
            command = shlex.split((directory / "command.txt").read_text(encoding="utf-8"))
            surfaces = command[command.index("--surfaces") + 1].split(",")
        except (OSError, UnicodeError, ValueError, IndexError):
            surfaces = []
        if surfaces not in (["codex", "agy", "grok"], ["agy", "grok"]):  # M:GAS-CYCLE-SURFACES
            raise Refusal(reason)
        deliveries = parsed.get("delivered", "").split(",")
        for pass_index, surface in enumerate(surfaces, 1):
            delivery = deliveries[pass_index - 1] if pass_index <= len(deliveries) else "none"
            if delivery in ("report-file", "out"):  # M:GAS-EXTRACT-DELIVERED
                collected = sorted((directory / "collected").glob(f"*.p{pass_index}.md"))
                collected = [path for path in collected if path.is_file()]
                if delivery in ("report-file", "out") and not collected:  # M:GAS-CYCLE-COLLECTED
                    raise Refusal(reason)
                for path in collected:
                    reports.append({
                        "doc": doc, "cycle": int(directory.name[1:]),
                        "pass": pass_index, "surface": surface,
                        "report": "s2/" + path.relative_to(s2_dir).as_posix(),
                        "path": path,
                    })
    return reports


def quote_hints(text: str) -> list[str]:
    lines = text.splitlines()
    quotes = []
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if not line.startswith("quote:"):
            index += 1
            continue
        block = [line]
        index += 1
        while index < len(lines) and not block[-1].endswith("`"):
            block.append(lines[index].strip())
            index += 1
        quotes.append("\n".join(block))
    return quotes


def extract_all(tree: Path, s2_dir: Path, sources: dict[str, str]) -> list[dict]:
    """Re-extract delivered findings from the standing cycles in external S2."""
    check_ledger(tree, sources)
    findings = []
    reports = _standing_reports(s2_dir, sources)
    containment_checks(s2_dir, sources)
    for report in reports:
        path = report["path"]
        must, should, _must_count, _should_count = extract_report(
            path.read_text(encoding="utf-8"), report["report"])
        # Root paths support quote hints; list_check validates record provenance.
        root_record = path.parent.parent / f"p{report['pass']}.root.txt"  # M:GAS-HINT-PASS-ROOT
        if not root_record.is_file():
            root_record = path.parent.parent / "root.txt"
        root_lines = root_record.read_text(encoding="utf-8").splitlines() if root_record.is_file() else []
        root = next((parsed["path"] for line in root_lines
                     if (parsed := parse_root_line(line)) is not None), "")
        for section, texts in (("must", must), ("should", should)):
            for text in texts:
                findings.append({
                    **{key: value for key, value in report.items() if key != "path"},
                    "section": section, "text": text,
                    "quotes": quote_hints(text),
                    "root": root,
                })
    return findings


def blind(findings: list[dict], shuffle_seed: int) -> tuple[list[dict], list[dict]]:
    generator = random.Random(shuffle_seed)
    rows, keys = [], []
    used = set()
    for finding in findings:
        identifier = f"F{generator.getrandbits(32):08x}"
        while identifier in used:
            identifier = f"F{generator.getrandbits(32):08x}"
        used.add(identifier)
        rows.append({"id": identifier, **{key: finding[key] for key in
                     ("doc", "cycle", "section", "text", "quotes")}})
        keys.append({"id": identifier, **{key: finding[key] for key in
                     ("doc", "cycle", "pass", "surface", "report")}})
    generator.shuffle(rows)
    return rows, keys


def hints(findings: list[dict], tree: Path, sources: dict[str, str]) -> list[str]:
    ledger = read_ledger(tree)
    lines = []
    for finding in findings:
        selected = placements(finding["doc"], sources)
        for quote in finding["quotes"]:
            path_text, separator, span = quote.removeprefix("quote:").partition(" › ")
            if not separator:
                continue
            path = Path(path_text.strip())
            root = finding.get("root", "")
            if root and path.is_relative_to(root):
                path = path.relative_to(root)
            relative = selected.get(path.as_posix(), path.as_posix())
            span = span.strip()
            if span.startswith("`") and span.endswith("`"):
                span = span[1:-1]
            span = normalise(span.encode("utf-8")).strip()
            try:
                content = normalise((tree / relative).read_bytes())
            except OSError:
                content = ""
            if not span or span not in content:
                lines.append(f"HINT: {finding['id']} candidate-fabrication")
                continue
            positions = [match.start() for match in re.finditer(re.escape(span), content)]
            for seed in ledger:
                seeded_path = (CALIBRATION / "seeded" / Path(seed["source"]).name).as_posix()
                if relative != seeded_path:
                    continue
                seeded = normalise(seed["seeded"].encode("utf-8")).strip()
                start = content.find(seeded)
                if start >= 0 and any(position < start + len(seeded)
                                      and start < position + len(span) for position in positions):
                    lines.append(f"HINT: {finding['id']} candidate-hit:{seed['id']}")
    return list(dict.fromkeys(lines))


def _mode_extract(args: argparse.Namespace) -> int:
    def write(tree: Path) -> None:
        findings = extract_all(tree, args.s2, args.sources)
        reports = len(_standing_reports(args.s2, args.sources))
        rows, keys = blind(findings, args.shuffle_seed)
        hint_lines = hints([{**finding, "id": key["id"]}
                            for finding, key in zip(findings, keys)], tree, args.sources)
        args.out.mkdir(parents=True, exist_ok=True)
        for name, records in (("findings.jsonl", rows), ("key.jsonl", keys)):
            (args.out / name).write_text("".join(
                json.dumps(record, ensure_ascii=False) + "\n" for record in records), encoding="utf-8")
        (args.out / "extract.txt").write_text(
            shlex.join([str(Path(__file__)), *args.argv]) + "\n", encoding="utf-8")
        for line in hint_lines:
            print(line)
        must = sum(row["section"] == "must" for row in rows)
        should = len(rows) - must
        print(f"FINDINGS: WRITTEN findings={len(rows)} must={must} should={should} reports={reports}")

    if args.tree is not None:
        write(args.tree)
    else:
        try:
            archive = _git_bytes(args.repo, "archive", "--format=tar", args.base_sha)
        except (OSError, subprocess.SubprocessError) as exc:
            raise Refusal(f"calibration_ref:sha_unknown:{args.base_sha}") from exc
        with tempfile.TemporaryDirectory(prefix="gas-extract-", dir=args.work_dir) as directory:  # M:GAS-SCRATCH-EXTRACT
            tree = Path(directory)
            _extract_archive(archive, tree)
            write(tree)
    return 0


MODES["extract"] = _mode_extract


def d3(fg: Fraction, rg: int, fa: Fraction, ra: int) -> bool:
    if fg < fa and rg >= ra:  # M:GAS-D3-LOWER
        return True
    return fg == fa and rg > ra  # M:GAS-D3-EQUAL


def verdict(totals: dict[str, tuple[int, int, int, int]]) -> tuple[str, str | None]:
    if not any(hits for hits, _n, _f, _u in totals.values()):  # M:GAS-VERDICT-UNDETECTED
        return "INCONCLUSIVE", "seeds_undetected"
    bounds = {}
    for surface in ("grok", "agy"):
        hits, n, f, u = totals[surface]
        pessimistic, optimistic = (Fraction(f + u, n), Fraction(f, n)) if n else (Fraction(0), Fraction(0))  # M:GAS-FAB-FRACTION
        bounds[surface] = (hits, pessimistic, optimistic)
    rg, pess_g, opt_g = bounds["grok"]
    ra, pess_a, opt_a = bounds["agy"]
    if d3(pess_g, rg, opt_a, ra):
        return "PASS", None
    if not d3(opt_g, rg, pess_a, ra):
        return "MISS", "bar_missed"
    return "INCONCLUSIVE", "undecidable_flips"  # M:GAS-VERDICT-FLIPS


def check_key(tree: Path, findings: list[dict], key: list[dict], reextracted: list[dict],
              selected_root: Path | None = None) -> None:
    s2_root = (selected_root or tree / CALIBRATION) / "s2"
    by_id = {row["id"]: row for row in findings}
    keyed = {row["id"]: row for row in key}
    if by_id.keys() != keyed.keys():  # M:GAS-KEY-ID-SETS
        raise Refusal("key_mismatch")
    if len(by_id) != len(findings):  # M:GAS-KEY-DUP-FINDINGS
        raise Refusal("key_mismatch")
    if len(keyed) != len(key):  # M:GAS-KEY-DUP-KEY
        raise Refusal("key_mismatch")
    mapped = []
    for identifier in by_id.keys() & keyed.keys():
        finding, row = by_id[identifier], keyed[identifier]
        doc, cycle = finding["doc"], finding["cycle"]
        if row["doc"] != doc:  # M:GAS-KEY-DOC
            raise Refusal("key_mismatch")
        if row["cycle"] != cycle:  # M:GAS-KEY-CYCLE
            raise Refusal("key_mismatch")
        try:
            command = shlex.split((s2_root / doc / f"v{cycle}" / "command.txt").read_text(encoding="utf-8"))
            surfaces = command[command.index("--surfaces") + 1].split(",")
            pass_index = row["pass"]
            surface = dict(enumerate(surfaces, 1)).get(pass_index)
            feature = command[command.index("--feature") + 1]
            phase = command[command.index("--phase") + 1]
        except (OSError, UnicodeError, ValueError, IndexError, TypeError) as exc:
            raise Refusal("key_mismatch") from exc
        if surface is None or row["surface"] != surface:  # M:GAS-KEY-SURFACE
            raise Refusal("key_mismatch")
        report = f"s2/{doc}/v{cycle}/collected/{feature}.{phase}.audit.v{cycle}.p{pass_index}.md"
        if row["report"] != report:  # M:GAS-KEY-REPORT
            raise Refusal("key_mismatch")
        # Compare content at the independently validated recorded location.
        mapped.append((report, finding["section"], finding["text"]))
    extracted = [(row["report"], row["section"], row["text"]) for row in reextracted]
    # A content comparison is meaningful only for a complete id join.
    if by_id.keys() == keyed.keys() and Counter(mapped) != Counter(extracted):  # M:GAS-KEY-REEXTRACT
        raise Refusal("key_mismatch")


def check_labels(findings: list[dict], labels: list[dict], ledger: list[dict]) -> dict[str, dict]:
    by_id = {row["id"]: row for row in findings}
    counts = Counter(row["id"] for row in labels)
    labelled = {row["id"]: row for row in labels}
    seeds = {row["id"]: row for row in ledger}
    for identifier in by_id:
        if identifier not in labelled:  # M:GAS-LABEL-MISSING
            raise Refusal(f"label:{identifier}")
    for row in labels:
        identifier, label = row["id"], row["label"]
        if counts[identifier] > 1:  # M:GAS-LABEL-DUP
            raise Refusal(f"label:{identifier}")
        if identifier not in by_id:  # M:GAS-LABEL-UNKNOWN-ID
            raise Refusal(f"label:{identifier}")
        if label not in ("REAL", "FABRICATED", "UNDECIDABLE") and not label.startswith("HIT:"):  # M:GAS-LABEL-VALUE
            raise Refusal(f"label:{identifier}")
        if label == "UNDECIDABLE" and not row.get("why", "").strip():  # M:GAS-LABEL-WHY
            raise Refusal(f"label:{identifier}")
        if label.startswith("HIT:"):
            seed = seeds.get(label.removeprefix("HIT:"))
            if seed is None:  # M:GAS-LABEL-SEED-UNKNOWN
                raise Refusal(f"label:{identifier}")
            if seed is not None and seed["doc"] != by_id.get(identifier, {}).get("doc"):  # M:GAS-LABEL-SEED-DOC
                raise Refusal(f"label:{identifier}")
    return labelled


def _score_totals(rows: list[dict]) -> tuple[int, int, int, int]:
    labels = [row.get("label", "") for row in rows]
    hits = {label.removeprefix("HIT:") for label in labels if label.startswith("HIT:")}
    return len(hits), len(rows), labels.count("FABRICATED"), labels.count("UNDECIDABLE")


def observational_lines(rows: list[dict], ledger: list[dict]) -> list[str]:
    """Publish should and split observations from each surface's joined findings."""
    lines = []
    for row in rows:
        surface, findings = row["surface"], row["findings"]
        hits, n, f, u = _score_totals([item for item in findings if item["section"] == "should"])
        lines.append(f"SHOULD: {surface} hits={hits}/{len(ledger)} should={n} fabricated={f} undecidable={u}")
        musts = [item for item in findings if item["section"] == "must"]
        for phase in ("plan", "design", "impl-plan"):
            phase_rows = [item for item in musts if item["phase"] == phase]
            hits, n, f, _u = _score_totals(phase_rows)
            denominator = sum(seed["phase"] == phase for seed in ledger)
            lines.append(f"SPLIT: {surface} phase={phase} recall={hits}/{denominator} musts={n} fabricated={f}")
        hit_ids = {item.get("label", "").removeprefix("HIT:") for item in musts
                   if item.get("label", "").startswith("HIT:")}
        for cls in ("C1", "C2", "C3", "C4"):
            seed_ids = {seed["id"] for seed in ledger if seed["class"] == cls}
            lines.append(f"SPLIT: {surface} class={cls} recall={len(hit_ids & seed_ids)}/{len(seed_ids)}")
    return lines


def _score_table(tree: Path, name: str, reason: str) -> list[dict]:
    try:
        return [json.loads(line) for line in (tree / f"{name}.jsonl").read_text(encoding="utf-8").splitlines()]
    except (OSError, UnicodeError, ValueError) as exc:
        raise Refusal(reason) from exc


def score(tree: Path, sources: dict[str, str], calibration: str | None, score_sha: str | None,
          run_id: str | None = None) -> tuple[list[str], str]:
    # extract_all validates the ledger, every standing cycle, and must counts first.
    selected_root = reading_root(tree, run_id)
    reextracted = extract_all(tree, selected_root / "s2", sources)
    findings = _score_table(selected_root, "findings", "key_mismatch")
    key = _score_table(selected_root, "key", "key_mismatch")
    check_key(tree, findings, key, reextracted, selected_root)
    documents = [(Path(directory) / feature / f"{feature}.{phase}.md").as_posix()
                 for feature, directory in sources.items() for phase in ("plan", "design", "impl-plan")]
    doc_ids = {source: f"d{index}" for index, source in enumerate(documents, 1)}
    ledger = [{**seed, "doc": doc_ids[seed["source"]]} for seed in read_ledger(tree)]
    labelled = check_labels(findings, _score_table(selected_root, "labels", "label:unknown"), ledger)
    keyed = {row["id"]: row for row in key}
    phases = {seed["doc"]: seed["phase"] for seed in ledger}
    joined = [{**finding, **keyed[finding["id"]], **labelled.get(finding["id"], {}),
               "phase": phases[finding["doc"]]} for finding in findings if finding["id"] in keyed]
    delivered_counts = Counter()
    evidence = {}
    for doc in doc_ids.values():
        directory = stands(selected_root / "s2" / doc)
        text = (directory / "auditcycle.txt").read_text(encoding="utf-8")
        parsed = _recorded_cycle(directory)
        command = shlex.split((directory / "command.txt").read_text(encoding="utf-8"))
        surfaces = command[command.index("--surfaces") + 1].split(",")
        deliveries = parsed.get("delivered", "").split(",")
        items = parse_effort_items(text)
        for index, surface in enumerate(surfaces, 1):
            delivered_counts[surface] += index <= len(deliveries) and deliveries[index - 1] in ("report-file", "out")
            evidence.setdefault(surface, 0)
            if items is None:  # M:GAS-SCORE-EFFORT-MALFORMED
                evidence[surface] = "unreadable"
            if evidence[surface] != "unreadable":
                evidence[surface] += sum(item.startswith(f"p{index} ") and " low-evidence (" in item for item in (items or []))
    rows, totals, lines = [], {}, []
    for surface in ("codex", "agy", "grok"):
        if surface not in evidence:
            lines.append(f"SURFACE: {surface} not_run")
            continue
        surface_rows = [row for row in joined if row["surface"] == surface]
        rows.append({"surface": surface, "findings": surface_rows})
        hits, n, f, u = totals[surface] = _score_totals([row for row in surface_rows if row["section"] == "must"])
        lines.append(f"SURFACE: {surface} recall={hits}/{len(ledger)} musts={n} fabricated={f} "
                     f"undecidable={u} fab_rate={f}/{n - u} "
                     f"delivered={delivered_counts[surface]} low_evidence={evidence[surface]}")
    outcome, reason = verdict(totals)
    lines.extend(observational_lines(rows, ledger))
    lines.extend(containment_lines(selected_root / "s2", sources))
    token = f"SEEDSCORE: {outcome}" + (f" reason={reason}" if reason else "")
    token += f" calibration={calibration or 'unstated'} score={score_sha or 'unstated'}"
    return lines, token


def _mode_score(args: argparse.Namespace) -> int:
    lines, token = score(args.tree, args.sources, args.calibration_sha, args.score_sha,
                         args.run_id)
    for line in lines:
        print(line)
    print(token)
    return 0


MODES["score"] = _mode_score


def calibration_data_files(tree: Path) -> list[str]:
    """Return D3's data set, retaining metadata that carries calibration text."""
    data = tree / CALIBRATION
    ledger = read_ledger(tree)
    seeded = [normalise(row["seeded"].encode()).strip() for row in ledger]
    expected = [normalise(row["expected"].encode()).strip() for row in ledger]
    findings = []
    reports = [*data.glob("s1/*/collected/*.md"),
               *data.glob("s2/d*/v*/collected/*.md"),
               *data.glob("runs/*/s2/d*/v*/collected/*.md")]
    for report in sorted(reports):
        for spans in report_findings(report.read_text(encoding="utf-8")).values():
            for span in spans:
                lines = span.splitlines()
                if lines and _gate._bullet_remainder(lines[0].strip()) is not None:
                    lines = lines[:1]
                findings.extend(normalise(_gate._payload(line).encode()).strip()
                                for line in lines)
    selected = []
    for path in sorted(data.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(tree).as_posix()
        relative_to_data = path.relative_to(data)
        candidate = (path.name in {"command.txt", "root.txt", "wall_seconds.txt",
                                   "resolved_model.txt", "extract.txt"}
                     or path == data / "s1/versions.txt"
                     or ("resmoke" in relative_to_data.parts and "canary" in relative_to_data.parts)
                     or (relative_to_data.parts[-2:] == ("resmoke", "run.txt"))
                     or ("resmoke" in relative_to_data.parts
                         and relative_to_data.parts[-1] == "versions.txt")
                     or ("resmoke" in relative_to_data.parts
                         and len(relative_to_data.parts) >= 3
                         and re.fullmatch(r"p[1-9][0-9]*\.profile\.txt", path.name))
                     or (relative_to_data.parts[-2:] == ("s2", "run.txt"))
                     or ("s2" in relative_to_data.parts
                         and re.fullmatch(r"p[1-9][0-9]*\.(root|profile|scan)\.txt", path.name)))  # M:GAS-CALSET-METADATA
        if candidate:
            text = normalise(path.read_bytes())
            if any(needle and needle in text for needle in seeded):  # M:GAS-CALSET-SEEDED
                selected.append(relative)
                continue
            if any(needle and needle in text for needle in expected):  # M:GAS-CALSET-EXPECTED
                selected.append(relative)
                continue
            if any(needle and needle in text for needle in findings):  # M:GAS-CALSET-FINDING
                selected.append(relative)
            continue
        selected.append(relative)
    return selected


def ref_checks(repo: Path, remote: str, shas: list[str]) -> str:
    ref = "refs/heads/calibration/grok-audit-surface"
    private = "refs/h-mad-probe/grok-audit-surface/calibration"
    advertised = _git(repo, "ls-remote", "--exit-code", remote, ref)
    if advertised.returncode == 2:  # M:GAS-REF-ABSENT
        raise Refusal("calibration_ref:ref_absent")
    fetched = _git(repo, "fetch", "--no-tags", remote, f"+{ref}:{private}")
    resolved = _git(repo, "rev-parse", "--verify", private)
    if advertised.returncode or fetched.returncode or resolved.returncode:  # M:GAS-REF-FETCH
        raise Refusal("calibration_ref:fetch_failed")
    tip = resolved.stdout.decode().strip() if resolved.returncode == 0 else shas[-1]
    for sha in shas:
        known = _git(repo, "cat-file", "-e", f"{sha}^{{commit}}")
        if known.returncode != 0:  # M:GAS-REF-SHA-UNKNOWN
            raise Refusal(f"calibration_ref:sha_unknown:{sha}")
        ancestor = _git(repo, "merge-base", "--is-ancestor", sha, tip)
        if ancestor.returncode == 1:  # M:GAS-REF-NOT-ON-REF
            raise Refusal(f"calibration_ref:not_on_ref:{sha}")
    return tip


def drift_check(repo: Path, calibration: str, later: str) -> None:
    if _git(repo, "merge-base", "--is-ancestor", calibration, later).returncode != 0:  # M:GAS-DRIFT-ANCESTOR
        raise Refusal("calibration_drift:not_descendant")
    changed = _git_bytes(repo, "diff", "--no-renames", "--name-only", "-z", calibration, later)
    for name in sorted(changed.split(b"\0")):
        if not name:
            continue
        path = os.fsdecode(name)
        if not path.startswith(CALIBRATION.as_posix() + "/"):  # M:GAS-DRIFT-PATH
            raise Refusal(f"calibration_drift:{path}")
    entries = _git_bytes(repo, "ls-tree", "-r", "-z", calibration, "--", str(CALIBRATION))
    for entry in sorted(filter(None, entries.split(b"\0")), key=lambda item: item.split(b"\t", 1)[1]):
        metadata, name = entry.split(b"\t", 1)
        _mode, kind, oid = metadata.split()
        if kind != b"blob":
            continue
        path = os.fsdecode(name)
        current = _git(repo, "rev-parse", "--verify", f"{later}:{path}")
        if current.returncode != 0:
            if True:  # M:GAS-DRIFT-ABSENT
                raise Refusal(f"calibration_drift:{path}")
            continue
        if current.stdout.strip() != oid:  # M:GAS-DRIFT-BLOB
            raise Refusal(f"calibration_drift:{path}")


def main_leak(repo: Path, data_sha: str, sources: dict[str, str], work_dir: Path) -> tuple[str, str, int]:
    head = _git_bytes(repo, "rev-parse", "HEAD^{commit}").decode().strip()
    data_sha = _git_bytes(repo, "rev-parse", f"{data_sha}^{{commit}}").decode().strip()
    with tempfile.TemporaryDirectory(prefix="gas-main-leak-", dir=work_dir) as directory:  # M:GAS-SCRATCH-MAIN-LEAK
        tree = Path(directory)
        _extract_archive(_git_bytes(repo, "archive", "--format=tar", data_sha), tree)
        reach_check(tree)
        digests = {hashlib.sha256((tree / path).read_bytes()).digest()
                   for path in calibration_data_files(tree)}
        ledger = read_ledger(tree)
        expected = [normalise(row["expected"].encode()).strip() for row in ledger]
        documents = {(Path(base) / feature / f"{feature}.{phase}.md").as_posix()
                     for feature, base in sources.items()
                     for phase in ("plan", "design", "impl-plan")}
        seeded = []
        for row in ledger:
            if row["source"] not in documents:
                raise Refusal("ledger_counts")
            needle = normalise(row["seeded"].encode()).strip()
            if needle not in normalise((tree / row["source"]).read_bytes()):
                seeded.append(needle)
        entries = _git_bytes(repo, "ls-tree", "-r", "-z", head)
        blobs = []
        for entry in filter(None, entries.split(b"\0")):
            metadata, name = entry.split(b"\t", 1)
            _mode, kind, oid = metadata.split()
            if kind == b"blob":
                blobs.append((name, oid))
        blobs.sort()
        batch = _git_bytes_batch(repo, [oid for _name, oid in blobs])
        for (name, _oid), content in zip(blobs, batch):
            path = os.fsdecode(name)
            if hashlib.sha256(content).digest() in digests:  # M:GAS-MAINLEAK-I
                raise Refusal(f"main_leak:{path}")
            text = normalise(content)
            if any(needle and needle in text for needle in expected):  # M:GAS-MAINLEAK-II
                raise Refusal(f"main_leak:{path}")
            if any(needle and needle in text for needle in seeded):  # M:GAS-MAINLEAK-III
                raise Refusal(f"main_leak:{path}")
        return head, data_sha, len(blobs)


def _git_bytes_batch(repo: Path, oids: list[bytes]) -> list[bytes]:
    result = _git(repo, "cat-file", "--batch", stdin=b"".join(oid + b"\n" for oid in oids))
    result.check_returncode()
    stream = io.BytesIO(result.stdout)
    blobs = []
    for oid in oids:
        object_id, kind, size = stream.readline().split()
        if object_id != oid or kind != b"blob":
            raise ValueError("unexpected cat-file object")
        content = stream.read(int(size))
        if len(content) != int(size) or stream.read(1) != b"\n":
            raise ValueError("truncated cat-file blob")
        blobs.append(content)
    return blobs


def reading_root(tree: Path, run_id: str | None = None) -> Path:
    root = tree / CALIBRATION
    return root / "runs" / run_id if run_id else root  # M:GAS-RUN-ID


def list_check(export: Path, repo: Path, run_id: str | None = None) -> str:
    def check_recorded_list_blob(blob: str) -> None:
        if blob != current:  # M:GAS-LIST-CHANGED
            raise Refusal(f"list_changed:{blob}")

    _entries, _commit, current = read_exclusions(repo, "HEAD")
    data = reading_root(export, run_id)
    cycles = [data / "s1" / surface for surface in ("grok", "agy", "codex")
              if (data / "s1" / surface).is_dir()]
    cycles.extend(data / "resmoke" / surface for surface in ("grok", "agy", "codex")
                  if (data / "resmoke" / surface).is_dir())  # M:GAS-LIST-RESMOKE
    docs = sorted((data / "s2").glob("d*"),
                  key=lambda path: int(path.name[1:]))
    pass_cycles = []
    for doc in docs:
        for cycle in sorted(doc.glob("v*"), key=lambda path: int(path.name[1:])):
            try:
                words = shlex.split((cycle / "command.txt").read_text(encoding="utf-8"))
                surfaces = words[words.index("--surfaces") + 1].split(",")
            except (OSError, UnicodeError, ValueError, IndexError):
                surfaces = []
            if not surfaces:  # M:GAS-LIST-SURFACES
                raise Refusal("list_changed:unrecorded")
            pass_cycles.append((cycle, len(surfaces)))
    recorded = []
    for cycle in cycles:
        path = cycle / "root.txt"
        if not path.is_file():
            if True:  # M:GAS-LIST-UNRECORDED
                raise Refusal("list_changed:unrecorded")
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        records = [parse_root_line(line) for line in lines if line.startswith("ROOT: READY ")]
        fields = records[0] if len(records) == 1 else None
        if fields is None:  # M:GAS-LIST-MALFORMED
            raise Refusal("list_changed:unrecorded")
        if fields is None:
            continue
        blob = fields["list_blob"]
        check_recorded_list_blob(blob)
        recorded.append(blob)
    for cycle, passes in pass_cycles:
        for pass_index in range(1, passes + 1):  # M:GAS-LIST-PASS-RECORDS
            path = cycle / f"p{pass_index}.root.txt"
            if not path.is_file():
                raise Refusal("list_changed:unrecorded")
            lines = [parse_root_line(line) for line in path.read_text(encoding="utf-8").splitlines()
                     if line.startswith("ROOT: READY ")]
            fields = lines[0] if len(lines) == 1 else None
            if fields is None:
                raise Refusal("list_changed:unrecorded")
            blob = fields["list_blob"]
            check_recorded_list_blob(blob)
            recorded.append(blob)
    return f"LIST: recorded={','.join(recorded)} current={current}"


def _branch_checks(args: argparse.Namespace) -> None:
    shas = [args.calibration_sha, args.smoke_sha]
    if args.score_sha is not None:
        shas.append(args.score_sha)
    ref_checks(args.repo, args.remote, shas)
    for later in shas[1:]:
        drift_check(args.repo, args.calibration_sha, later)
    if args.score_sha is not None:
        if _git(args.repo, "merge-base", "--is-ancestor", args.smoke_sha, args.score_sha).returncode != 0:  # M:GAS-DRIFT-SMOKE-ANCESTOR
            raise Refusal("calibration_drift:not_descendant")


def rescore(args: argparse.Namespace) -> tuple[list[str], str]:
    directories = []
    try:
        _branch_checks(args)
        export = Path(tempfile.mkdtemp(prefix="gas-rescore-", dir=args.work_dir))  # M:GAS-SCRATCH-RESCORE
        directories.append(export)
        _extract_archive(_git_bytes(args.repo, "archive", "--format=tar", args.score_sha), export)
        reach_check(export)
        head, data, blobs = main_leak(args.repo, args.score_sha, args.sources, args.work_dir)
        listing = list_check(export, args.repo, args.run_id)
        lines = [f"SCANNED: main={head} data={data} blobs={blobs}", listing]
        check_ledger(export, args.sources)
        for index in range(1, len(args.sources) * 3 + 1):
            root_args = argparse.Namespace(
                repo=args.repo, calibration_sha=args.calibration_sha, sources=args.sources,
                doc=f"d{index}", purpose="rescore", list_commit="HEAD",
                dest_parent=args.work_dir, work_dir=args.work_dir,
            )
            root_line = build_root(root_args)
            directories.append(Path(parse_root_line(root_line)["path"]))
        observations, token = score(export, args.sources, args.calibration_sha,
                                    args.score_sha, args.run_id)
        return lines + observations, token
    finally:
        for directory in reversed(directories):
            try:
                _remove_tree(directory)
            except OSError as exc:
                print(f"[H-MAD] cleanup failed path={directory}: {exc}", file=sys.stderr)
        for directory in directories:
            try:
                if directory in directory.parent.iterdir():
                    print(f"[H-MAD] cleanup remains path={directory}", file=sys.stderr)
            except OSError as exc:
                print(f"[H-MAD] cleanup re-list failed path={directory}: {exc}", file=sys.stderr)
        print("[H-MAD] grok-audit-surface rescore cleanup complete", file=sys.stderr)


def _mode_main_leak(args: argparse.Namespace) -> int:
    _branch_checks(args)
    head, data, blobs = main_leak(args.repo, args.score_sha or args.smoke_sha, args.sources, args.work_dir)
    print(f"MAINLEAK: CLEAN scanned={head} data={data} blobs={blobs}")
    return 0


def _mode_rescore(args: argparse.Namespace) -> int:
    lines, token = rescore(args)
    for line in lines:
        print(line)
    print(token)
    return 0


MODES["main-leak"] = _mode_main_leak
MODES["rescore"] = _mode_rescore


def build_parser() -> _TokenArgumentParser:
    parser = _TokenArgumentParser()
    subparsers = parser.add_subparsers(dest="mode", parser_class=_TokenArgumentParser)

    ledger = subparsers.add_parser("check-ledger")
    ledger_input = ledger.add_mutually_exclusive_group(required=True)
    ledger_input.add_argument("--tree", type=Path)
    ledger_input.add_argument("--repo", type=Path)
    ledger.add_argument("--calibration-sha")
    ledger.add_argument("--sources", type=parse_sources, default=SOURCES.copy())

    root = subparsers.add_parser("build-root")
    root.add_argument("--repo", type=Path, required=True)
    root.add_argument("--calibration-sha", required=True)
    root.add_argument("--doc", required=True)
    root.add_argument("--purpose", choices=("s1", "s2v1", "s2v2", "rescore"), required=True)
    root.add_argument("--list-commit", default="HEAD")
    root.add_argument("--dest-parent", type=Path)
    root.add_argument("--reset")
    root.add_argument("--sources", type=parse_sources, default=SOURCES.copy())

    record = subparsers.add_parser("record-cycle")
    for flag in ("--stem", "--root", "--stdout", "--command", "--dest"):
        record.add_argument(flag, type=Path, required=True)
    record.add_argument("--root-record", type=Path)
    record.add_argument("--pass-root-record", type=Path, action="append", default=[])

    commit = subparsers.add_parser("commit-data")
    commit.add_argument("--repo", type=Path, required=True)
    commit.add_argument("--parent", required=True)
    commit.add_argument("--src", type=Path, required=True)
    commit.add_argument("--message", required=True)

    smoke = subparsers.add_parser("smoke")
    smoke.add_argument("--data", type=Path, required=True)
    smoke.add_argument("--vocab-py", type=Path, default=REPO / "h-mad/scripts/h_mad_review_evidence.py")
    smoke.add_argument("--vocab-sh", type=Path, default=REPO / "h-mad/scripts/hmad-dispatch.sh")

    extract = subparsers.add_parser("extract")
    extract_input = extract.add_mutually_exclusive_group(required=True)
    extract_input.add_argument("--tree", type=Path)
    extract_input.add_argument("--repo", type=Path)
    extract.add_argument("--base-sha")
    extract.add_argument("--s2", type=Path, required=True)
    extract.add_argument("--shuffle-seed", type=int, required=True)
    extract.add_argument("--out", type=Path, required=True)
    extract.add_argument("--sources", type=parse_sources, default=SOURCES.copy())

    score = subparsers.add_parser("score")
    score.add_argument("--tree", type=Path, required=True)
    score.add_argument("--calibration-sha")
    score.add_argument("--score-sha")
    score.add_argument("--run-id")
    score.add_argument("--sources", type=parse_sources, default=SOURCES.copy())

    rescore = subparsers.add_parser("rescore")
    rescore.add_argument("--repo", type=Path, required=True)
    rescore.add_argument("--calibration-sha", required=True)
    rescore.add_argument("--smoke-sha", required=True)
    rescore.add_argument("--score-sha", required=True)
    rescore.add_argument("--run-id", required=True)
    rescore.add_argument("--remote", default="origin")
    rescore.add_argument("--sources", type=parse_sources, default=SOURCES.copy())

    leak = subparsers.add_parser("main-leak")
    leak.add_argument("--repo", type=Path, required=True)
    leak.add_argument("--calibration-sha", required=True)
    leak.add_argument("--smoke-sha", required=True)
    leak.add_argument("--score-sha")
    leak.add_argument("--remote", default="origin")
    leak.add_argument("--sources", type=parse_sources, default=SOURCES.copy())
    for command in (ledger, root, extract, rescore, leak):
        command.add_argument("--work-dir", type=Path)
    return parser


def refusal_token(mode: str, exc: BaseException, argv: list[str]) -> str:
    prefix, verdict = GRAMMAR[mode]
    if isinstance(exc, Refusal):
        reason = exc.reason  # M:GAS-REFUSAL-REASON
    elif mode == "smoke":
        path = ""
        if _OPEN_INPUT is not None:  # M:GAS-OPEN-INPUT
            path = _OPEN_INPUT
        else:
            for index, word in enumerate(argv):
                if word == "--data":
                    path = argv[index + 1] if index + 1 < len(argv) else ""
                    break
                if word.startswith("--data="):
                    path = word.partition("=")[2]
                    break
        reason = f"input_unparseable:{path}"
    else:
        reason = f"internal:{type(exc).__name__}"  # M:GAS-LAST-RESORT
    return f"{prefix} {verdict} reason={reason}"


def main(argv: list[str] | None = None) -> int:
    global _OPEN_INPUT
    _OPEN_INPUT = None
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    if not argv or argv[0] not in GRAMMAR:
        print("PROBE: UNREADABLE reason=unknown_mode")  # M:GAS-UNKNOWN-MODE
        parser.print_usage(sys.stderr)
        print("[H-MAD] grok-audit-surface unknown_mode UNREADABLE", file=sys.stderr)
        return 2
    mode = argv[0]
    try:
        args = parser.parse_args(argv)
        args.argv = argv
        if mode == "check-ledger" and (args.repo is not None) != (args.calibration_sha is not None):
            parser.error("--repo and --calibration-sha must be supplied together")
        if mode == "extract" and (args.repo is not None) != (args.base_sha is not None):
            parser.error("--repo and --base-sha must be supplied together")
        if mode == "score" and (args.calibration_sha is None) != (args.score_sha is None):
            parser.error("--calibration-sha and --score-sha must be supplied together")
        needs_work_dir = mode in ("build-root", "main-leak", "rescore") or (
            mode in ("check-ledger", "extract") and args.repo is not None)
        if needs_work_dir and args.work_dir is None:  # M:GAS-WORK-DIR-REQUIRED
            parser.error("--work-dir is required")
        if needs_work_dir:
            args.work_dir = checked_parent(args.work_dir, git_guard=True)  # M:GAS-WORK-DIR-CHECK
        if mode == "build-root":
            if args.dest_parent is None and args.reset is None:  # M:GAS-PARENT-REQUIRED
                parser.error("one of --dest-parent and --reset is required")
            if args.reset is None:
                args.dest_parent = checked_parent(args.dest_parent, git_guard=False)  # M:GAS-DEST-PARENT-CHECK
        return MODES[mode](args)
    except Exception as exc:
        if not isinstance(exc, ProbeRefusal):  # M:GAS-TRACEBACK-SCOPE
            traceback.print_exc(file=sys.stderr)
        print(refusal_token(mode, exc, argv))
        print(f"[H-MAD] grok-audit-surface {mode} {GRAMMAR[mode][1]}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
