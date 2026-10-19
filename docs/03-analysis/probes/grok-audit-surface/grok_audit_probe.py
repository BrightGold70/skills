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


class ResetTargetOutsideTempdir(ProbeRefusal):
    """The resolved target is not directly under the temporary directory."""


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
        with tempfile.TemporaryDirectory(prefix="gas-ledger-") as directory:
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
    with tempfile.TemporaryDirectory(prefix="gas-ledger-") as directory:
        tree = Path(directory)
        _extract_archive(archive, tree)
        check_ledger(tree, args.sources)
        ledger = read_ledger(tree)
        for record in ledger:
            record["_source_sha256"] = hashlib.sha256((tree / record["source"]).read_bytes()).hexdigest()

    root = Path(tempfile.mkdtemp(prefix=f"gas-root-{args.doc}-{args.purpose}-",
                                 dir=args.dest_parent)).resolve()
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
    if root.parent != Path(tempfile.gettempdir()).resolve():  # M:GAS-RESET-TMPDIR
        raise ResetTargetOutsideTempdir()
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
            _remove_tree(path)
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


def _mode_build_root(args: argparse.Namespace) -> int:
    print(reset_root(args) if args.reset is not None else build_root(args))
    return 0


MODES["build-root"] = _mode_build_root


def record_cycle(args: argparse.Namespace) -> str:
    """Validate one wrapper run before copying its D3 recording files."""
    contents = {path: b"" for path in (args.root_record, args.stdout, args.command)}
    missing = [path for path in (args.stem, args.root) if not path.is_dir()]
    for path in contents:
        try:
            contents[path] = path.read_bytes()
        except OSError:
            missing.append(path)
    if missing:  # M:GAS-RECORD-INPUT
        raise Refusal(f"input_missing:{missing[0]}")

    lines = [line for line in contents[args.root_record].decode("utf-8", errors="replace").splitlines()
             if line.startswith("ROOT: READY ")]
    if len(lines) != 1:  # M:GAS-RECORD-ROOT-LINE
        raise Refusal("root_record:no_line")
    root_line = next(iter(lines), "")
    fields = parse_root_line(root_line)
    if fields is None:
        raise Refusal("root_record:no_line")  # M:GAS-RECORD-ROOT-MALFORMED
    if Path(fields["path"]).resolve() != args.root.resolve():  # M:GAS-RECORD-ROOT-PATH
        raise Refusal("root_record:path_mismatch")
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
        + r"(.+)_p([1-9][0-9]*)(\.txt|\.asm\.txt|\.out\.txt|\.log|\.report\.md)"
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
            suffix = ".prompt.txt" if match[3] == ".txt" else match[3]
            copies[f"p{match[2]}{suffix}"] = source

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
    recorded = {"root.txt": (root_line + "\n").encode("utf-8"),
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
        with tempfile.TemporaryDirectory(prefix="gas-commit-") as directory:
            environment = _git_environment()
            environment["GIT_INDEX_FILE"] = str(Path(directory) / "index")
            _git(args.repo, "read-tree", parent_oid, env=environment).check_returncode()
            for path, destination in sources:
                blob = _git(args.repo, "hash-object", "-w", "--stdin", stdin=path.read_bytes())
                blob.check_returncode()
                _git(args.repo, "update-index", "--add", "--cacheinfo", "100644",
                     blob.stdout.decode().strip(), destination.as_posix(),
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
                    pass
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


def extract_all(tree: Path, s2_dir: Path, sources: dict[str, str]) -> list[dict]:
    """Re-extract delivered findings from the standing cycles in external S2."""
    check_ledger(tree, sources)
    findings = []
    for report in _standing_reports(s2_dir, sources):
        path = report["path"]
        must, should, _must_count, _should_count = extract_report(
            path.read_text(encoding="utf-8"), report["report"])
        root_lines = (path.parent.parent / "root.txt").read_text(encoding="utf-8").splitlines()
        root = next((parsed["path"] for line in root_lines
                     if (parsed := parse_root_line(line)) is not None), "")
        for section, texts in (("must", must), ("should", should)):
            for text in texts:
                findings.append({
                    **{key: value for key, value in report.items() if key != "path"},
                    "section": section, "text": text,
                    "quotes": [line.strip() for line in text.splitlines()
                               if line.strip().startswith("quote:")],
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
        with tempfile.TemporaryDirectory(prefix="gas-extract-") as directory:
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


def check_key(tree: Path, findings: list[dict], key: list[dict], reextracted: list[dict]) -> None:
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
            command = shlex.split((tree / CALIBRATION / "s2" / doc / f"v{cycle}" / "command.txt").read_text(encoding="utf-8"))
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
        return [json.loads(line) for line in (tree / CALIBRATION / f"{name}.jsonl").read_text(encoding="utf-8").splitlines()]
    except (OSError, UnicodeError, ValueError) as exc:
        raise Refusal(reason) from exc


def score(tree: Path, sources: dict[str, str], calibration: str | None, score_sha: str | None) -> tuple[list[str], str]:
    # extract_all validates the ledger, every standing cycle, and must counts first.
    reextracted = extract_all(tree, tree / CALIBRATION / "s2", sources)
    findings = _score_table(tree, "findings", "key_mismatch")
    key = _score_table(tree, "key", "key_mismatch")
    check_key(tree, findings, key, reextracted)
    documents = [(Path(directory) / feature / f"{feature}.{phase}.md").as_posix()
                 for feature, directory in sources.items() for phase in ("plan", "design", "impl-plan")]
    doc_ids = {source: f"d{index}" for index, source in enumerate(documents, 1)}
    ledger = [{**seed, "doc": doc_ids[seed["source"]]} for seed in read_ledger(tree)]
    labelled = check_labels(findings, _score_table(tree, "labels", "label:unknown"), ledger)
    keyed = {row["id"]: row for row in key}
    phases = {seed["doc"]: seed["phase"] for seed in ledger}
    joined = [{**finding, **keyed[finding["id"]], **labelled.get(finding["id"], {}),
               "phase": phases[finding["doc"]]} for finding in findings if finding["id"] in keyed]
    delivered_counts = Counter()
    evidence = {}
    for doc in doc_ids.values():
        directory = stands(tree / CALIBRATION / "s2" / doc)
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
    token = f"SEEDSCORE: {outcome}" + (f" reason={reason}" if reason else "")
    token += f" calibration={calibration or 'unstated'} score={score_sha or 'unstated'}"
    return lines, token


def _mode_score(args: argparse.Namespace) -> int:
    lines, token = score(args.tree, args.sources, args.calibration_sha, args.score_sha)
    for line in lines:
        print(line)
    print(token)
    return 0


MODES["score"] = _mode_score


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
    for flag in ("--stem", "--root", "--root-record", "--stdout", "--command", "--dest"):
        record.add_argument(flag, type=Path, required=True)

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
    score.add_argument("--sources", type=parse_sources, default=SOURCES.copy())

    rescore = subparsers.add_parser("rescore")
    rescore.add_argument("--repo", type=Path, required=True)
    rescore.add_argument("--calibration-sha", required=True)
    rescore.add_argument("--smoke-sha", required=True)
    rescore.add_argument("--score-sha", required=True)
    rescore.add_argument("--remote", default="origin")
    rescore.add_argument("--sources", type=parse_sources, default=SOURCES.copy())

    leak = subparsers.add_parser("main-leak")
    leak.add_argument("--repo", type=Path, required=True)
    leak.add_argument("--calibration-sha", required=True)
    leak.add_argument("--smoke-sha", required=True)
    leak.add_argument("--score-sha")
    leak.add_argument("--remote", default="origin")
    leak.add_argument("--sources", type=parse_sources, default=SOURCES.copy())
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
        return MODES[mode](args)
    except Exception as exc:
        if not isinstance(exc, ProbeRefusal):  # M:GAS-TRACEBACK-SCOPE
            traceback.print_exc(file=sys.stderr)
        print(refusal_token(mode, exc, argv))
        print(f"[H-MAD] grok-audit-surface {mode} {GRAMMAR[mode][1]}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
