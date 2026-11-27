"""Compare Phase 5 hook verdicts against the archived baseline."""

from __future__ import annotations

import argparse
import errno
import importlib.util
import io
import itertools
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple, Sequence


ROOT = Path(__file__).resolve().parents[4]
BASELINE = "7a3cca48"
VARIABLES = ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_CEILING_DIRECTORIES")
SURFACES = ("codex-shell", "codex-write", "agy-shell", "agy-write", "claude")
CLASSES = ("D1", "D2", "D3", "D4", "D5", "D6", "D7")
BRANCHES = ("arming", "other")
CHANGES_IN_FORCE: dict[tuple[str, str], frozenset[str]] = {
    (surface, branch): frozenset() for surface in SURFACES for branch in BRANCHES
}
LEGACY_RAISE_LIFTED: frozenset[str] = frozenset()


class CaseSpec(NamedTuple):
    name: str
    surface: str
    kinds: tuple[str, ...]
    branch: str
    call: dict
    env: dict[str, str]


class Case(NamedTuple):
    spec: CaseSpec
    root: Path
    labels: frozenset[str]


class Verdict(NamedTuple):
    decision: str
    kind: str
    git_processes: int


STATE_PATH = Path("docs/.bkit-memory.json")
BASELINE_MARKER = ".baseline-commit"
DEEP_JSON_BYTES = b"[" * 1_000_000 + b"]" * 1_000_000
PRESENCE_SHAPES = (
    "regular", "file-link", "dangling-link", "looping-link", "directory-in-place",
    "docs-symlink", "case-variant-docs", "case-variant-file",
)
MALFORMED_SHAPES = (
    "inaccessible-docs", "unparsable-json", "invalid-utf8", "deep-json", "fifo",
    "directory-in-place", "not-object", "state-not-object", "dangling-link", "looping-link",
)
SHELL_COMMANDS = {"safe": "pwd", "allowance": "true", "refused": "false"}
MENTION_COMMAND = "true h_mad_state_write phase=step5"
ARMING_FIELD_MENTION_RE = re.compile(r"(?<![a-z0-9_])(phase|implementation_checkout|phase5_stage)\s*=")
WRITE_NAMES = {
    "test": "src/test_example.py",
    "document": "src/example.md",
    "production": "src/example.py",
    "listed": "bin/example",
}
TARGET_PREFIX = {"inside": "", "outside": "../outside/", "tmp": "../tmp/"}


def _fixture_env() -> dict[str, str]:
    env = {
        key: value for key, value in os.environ.items()
        if not key.startswith(("GIT_", "HMAD_STUB_"))
    }
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    return env


@lru_cache(maxsize=1)
def _fixture_feature() -> str:
    result = subprocess.run(
        [str(ROOT / "h-mad/tests/stubs/orca"), "worktree", "set", "comment", "fixture"],
        env=dict(_fixture_env(), HMAD_STUB_HOSTILE="all"),
        capture_output=True, check=True, text=True, timeout=10,
    )
    return json.loads(result.stdout)["result"]["worktree"]["comment"]


def _shell_payload(surface: str, command: str, cwd: str = ".") -> dict:
    if surface == "codex-shell":
        return {"tool_name": "exec_command", "tool_input": {"cmd": command, "workdir": cwd}}
    return {"toolCall": {"name": "run_command", "args": {"CommandLine": command, "Cwd": cwd}}}


def _write_payload(surface: str, target: str) -> dict:
    if surface == "agy-write":
        return {"toolCall": {"name": "write_to_file", "args": {"TargetFile": target}}}
    return {"tool_name": "Write", "tool_input": {"file_path": target}}


def _payload(surface: str, operation: str, location: str = "inside") -> dict:
    if surface.endswith("-shell"):
        return _shell_payload(surface, SHELL_COMMANDS[operation])
    return _write_payload(surface, TARGET_PREFIX[location] + WRITE_NAMES[operation])


def _is_arming_call(surface: str, call: dict) -> bool:
    if surface.endswith("-shell"):
        command = (
            call["toolCall"]["args"]["CommandLine"]
            if surface == "agy-shell" else call["tool_input"]["cmd"]
        )
        folded = command.replace("'", "").replace('"', "").casefold()
        return "h_mad_state_write" in folded and bool(ARMING_FIELD_MENTION_RE.search(folded))
    parts = Path(_scope_target(call, surface)).parts
    return parts[-2:] == STATE_PATH.parts or ".git" in parts


def _fixture_spec(
    surface: str, name: str, states: tuple[str, ...],
    operation: str, location: str = "inside",
) -> CaseSpec:
    kind = f"call:{operation}"
    if not surface.endswith("-shell"):
        kind += f":{location}"
    payload = _payload(surface, operation, location)
    branch = "arming" if _is_arming_call(surface, payload) else "other"
    return CaseSpec(name, surface, (*states, kind), branch, payload, {})


def crossed_corpus() -> tuple[CaseSpec, ...]:
    rows = []
    for surface in SURFACES:
        shell = surface.endswith("-shell")
        calls = (
            [(op, "inside") for op in SHELL_COMMANDS] if shell
            else list(itertools.product(WRITE_NAMES, TARGET_PREFIX))
        )
        for state, folder, (operation, location) in itertools.product(
            ("absent", "inactive", "live", "unreadable"), ("root", "subproject"), calls,
        ):
            call = operation if shell else f"{operation}-{location}"
            rows.append(_fixture_spec(
                surface, f"cross-{state}-{folder}-{call}", (f"state:{folder}:{state}",),
                operation, location,
            ))
        operation = "refused" if shell else "production"
        for shape in PRESENCE_SHAPES:
            rows.append(_fixture_spec(
                surface, f"presence-{shape}", (f"state:root:{shape}",), operation,
            ))
        for shape, neighbour in itertools.product(MALFORMED_SHAPES, ("alone", "beside-live")):
            states = (f"state:root:{shape}",)
            if neighbour == "beside-live":
                states = ("state:subproject:live", *states)
            rows.append(_fixture_spec(surface, f"malformed-{shape}-{neighbour}", states, operation))
        if shell:
            mention_call = _shell_payload(surface, MENTION_COMMAND)
            rows.append(CaseSpec(
                "mention-unknown-program", surface, ("state:root:live", "call:mention"),
                "arming" if _is_arming_call(surface, mention_call) else "other", mention_call, {},
            ))
        rows.extend(scoped_specs(surface))
        rows.extend(variable_specs(surface))
    return tuple(rows)


def _write_state(root: Path, shape: str) -> frozenset[str]:
    docs = root / ("Docs" if shape == "case-variant-docs" else "docs")
    name = STATE_PATH.name.upper() if shape == "case-variant-file" else STATE_PATH.name
    target = docs / name
    if shape == "absent":
        assert not os.path.lexists(target)
        return frozenset()
    if shape == "docs-symlink":
        (root / "real-documents").mkdir()
        docs.symlink_to("real-documents", target_is_directory=True)
    else:
        docs.mkdir(parents=True, exist_ok=True)

    contents = {
        "unreadable": b"{",
        "unparsable-json": b"{",
        "invalid-utf8": b"\xff",
        "deep-json": DEEP_JSON_BYTES,
        "not-object": b"[]",
        "state-not-object": b'{"orchestrator_state":[]}',
    }.get(shape)
    if contents is None:
        phase = "step4" if shape == "inactive" else "step5"
        contents = json.dumps({"orchestrator_state": {_fixture_feature(): {"phase": phase}}}).encode()

    if shape == "directory-in-place":
        target.mkdir()
        assert stat.S_ISDIR(os.lstat(target).st_mode)
    elif shape == "fifo":
        os.mkfifo(target)
        assert stat.S_ISFIFO(os.lstat(target).st_mode)
    elif shape in {"file-link", "dangling-link", "looping-link"}:
        destination = target if shape == "looping-link" else docs / "state-source"
        if shape == "file-link":
            destination.write_bytes(contents)
        target.symlink_to(destination.name)
        assert stat.S_ISLNK(os.lstat(target).st_mode)
        if shape == "file-link":
            assert target.read_bytes() == contents
        else:
            try:
                target.stat()
            except OSError as exc:
                expected = errno.ENOENT if shape == "dangling-link" else errno.ELOOP
                assert exc.errno == expected
            else:
                raise AssertionError(f"unexpected link destination for {shape}")
    else:
        target.write_bytes(contents)
        assert stat.S_ISREG(os.lstat(target).st_mode)
        assert target.read_bytes() == contents

    if shape == "inaccessible-docs":
        # See the private record.
        if os.geteuid() == 0:
            raise OSError("inaccessible-docs: lstat must raise an OSError other than absence")
        docs.chmod(0)
        try:
            os.lstat(target)
        except (FileNotFoundError, NotADirectoryError):
            docs.chmod(0o755)
            raise AssertionError("lstat must raise an OSError other than absence")
        except OSError:
            return frozenset()
        docs.chmod(0o755)
        raise AssertionError("lstat must raise an OSError other than absence")
    if shape == "docs-symlink":
        assert stat.S_ISLNK(os.lstat(docs).st_mode)
        return frozenset({"D4"})
    if shape in {"file-link", "dangling-link", "looping-link", "directory-in-place", "fifo"}:
        return frozenset({"D4"})
    if shape in {"case-variant-docs", "case-variant-file"}:
        assert docs.name in os.listdir(root) and name in os.listdir(docs)
        canonical = root / STATE_PATH
        if os.path.lexists(canonical):
            assert os.path.samestat(os.lstat(canonical), os.lstat(target))
            return frozenset({"D4"})
    return frozenset()


def _build_call(root: Path, spec: CaseSpec, parts: list[str]) -> None:
    operation, *locations = parts
    if spec.surface.endswith("-shell"):
        allowance = root / ".h-mad/phase5-shell-allow"
        if operation == "mention":
            assert spec.call == _shell_payload(spec.surface, MENTION_COMMAND)
            allowance.write_text("true\n", encoding="utf-8")
            assert stat.S_ISREG(os.lstat(allowance).st_mode)
            return
        assert spec.call == _payload(spec.surface, operation)
        if operation == "allowance":
            allowance.write_text(SHELL_COMMANDS[operation] + "\n", encoding="utf-8")
            assert stat.S_ISREG(os.lstat(allowance).st_mode)
        else:
            assert not os.path.lexists(allowance)
        return
    location, = locations
    assert spec.call == _payload(spec.surface, operation, location)
    if location == "tmp":
        scratch_link = root.parent / "tmp"
        scratch_link.symlink_to("/tmp", target_is_directory=True)
        assert stat.S_ISLNK(os.lstat(scratch_link).st_mode)
    else:
        target = root / (TARGET_PREFIX[location] + WRITE_NAMES[operation])
        target.parent.mkdir(parents=True)
        target.touch()
        assert stat.S_ISREG(os.lstat(target).st_mode)
    if operation == "listed":
        state_kind = next(kind for kind in spec.kinds if kind.startswith("state:"))
        _, folder, _ = state_kind.split(":")
        project = root if folder in {"root", "."} else root / folder
        plan = project / "docs/01-plan/features" / f"{_fixture_feature()}.impl-plan.md"
        plan.parent.mkdir(parents=True)
        plan.write_text("## Task 1: Example\n\n"
                        "**Production file**: `bin/example`\n"
                        "**Test file**: `src/test_example.py`\n", encoding="utf-8")
        assert stat.S_ISREG(os.lstat(plan).st_mode)


@lru_cache(maxsize=1)
def _git_template() -> tuple[tuple[str, ...], tuple[tuple[str, bytes], ...]]:
    with tempfile.TemporaryDirectory() as tmp:
        empty = Path(tmp) / "empty"
        empty.mkdir()
        repo = Path(tmp) / "repo"
        repo.mkdir()
        subprocess.run(
            ["git", "init", "-q", f"--template={empty}"],
            cwd=repo, env=_fixture_env(), capture_output=True, check=True, timeout=10,
        )
        git_dir = repo / ".git"
        (git_dir / "info").mkdir(exist_ok=True)
        dirs = []
        files = []
        for parent, _, filenames in os.walk(git_dir):
            rel = Path(parent).relative_to(git_dir)
            if str(rel) != ".":
                dirs.append(str(rel))
            for name in filenames:
                file_rel = rel / name if str(rel) != "." else Path(name)
                files.append((str(file_rel), (Path(parent) / name).read_bytes()))
        return tuple(dirs), tuple(files)


def _init_git_repo(directory: Path) -> None:
    dirs, files = _git_template()
    git_dir = directory / ".git"
    git_dir.mkdir(parents=True, exist_ok=True)
    for rel in dirs:
        (git_dir / rel).mkdir(parents=True, exist_ok=True)
    for rel, content in files:
        (git_dir / rel).write_bytes(content)


def _build_fixture_root(where: Path) -> Path:
    root = where.resolve() / "repo"
    root.mkdir(parents=True)
    _init_git_repo(root)
    for folder in (".agents", ".h-mad"):
        (root / folder).mkdir()
    assert stat.S_ISDIR(os.lstat(root / ".git").st_mode)
    return root


def build_case(spec: CaseSpec, where: Path) -> Case:
    if spec.name in _SCOPED_LAYOUTS:
        return build_scoped_case(spec, where)
    if any(kind.startswith("variable:") for kind in spec.kinds):
        return build_variable_case(spec, where)
    root = _build_fixture_root(where)
    has_excludes = any(
        "excluded" in Path(kind.split(":")[1]).parts
        for kind in spec.kinds if kind.startswith("state:")
    )
    if has_excludes:
        (root / ".git/info/exclude").write_text("excluded/\n", encoding="utf-8")
    has_nested = False
    for kind in spec.kinds:
        if kind.startswith("checkout:"):
            _, nested_rel = kind.split(":", 1)
            checkout = root / nested_rel
            checkout.mkdir(parents=True, exist_ok=True)
            _init_git_repo(checkout)
            assert _checkout(checkout) == checkout
            has_nested = True
    labels = set()
    if _is_arming_call(spec.surface, spec.call):
        labels.add("D6")
    # Prepare call inputs before state files; see the private record.
    for kind in spec.kinds:
        family, *parts = kind.split(":")
        if family == "call":
            _build_call(root, spec, parts)
    for kind in spec.kinds:
        family, *parts = kind.split(":")
        if family == "state":
            folder, shape = parts
            project = root if folder in {"root", "."} else root / folder
            labels.update(_write_state(project, shape))
            if shape != "absent" and project != root:
                if has_excludes and _excluded(root, project):
                    labels.add("D1")
                if has_nested and _checkout(project) != root:
                    labels.add("D2")
                if _fixture_directory(root, project):
                    labels.add("D3")
        elif family not in {"call", "checkout"}:
            raise ValueError(f"unknown fixture kind {kind!r}")
    return Case(spec, root, frozenset(labels))


class _ScopeLayout(NamedTuple):
    stores: tuple[tuple[str, str], ...]
    nested: str = ""
    target_project: str = ""
    arming_target: bool = False


_SCOPED_LAYOUTS = {
    "D1-control": _ScopeLayout((("excluded", "live"),)),
    "D1-neighbour": _ScopeLayout((("included", "live"),)),
    "D2-control": _ScopeLayout((("nested", "live"),), "nested"),
    "D2-neighbour": _ScopeLayout((("included", "live"),)),
    "D3-control": _ScopeLayout((("fixtures/example", "live"),)),
    "D3-neighbour": _ScopeLayout((("examples", "live"),)),
    "D4-control": _ScopeLayout(((".", "dangling-link"),)),
    "D4-neighbour": _ScopeLayout(((".", "live"),)),
    "excluded-alone": _ScopeLayout((("excluded", "live"),)),
    "excluded-beside-live-root": _ScopeLayout((("excluded", "live"), (".", "live"))),
    "excluded-not-object": _ScopeLayout((("excluded", "not-object"),)),
    "excluded-object-not-live": _ScopeLayout((("excluded", "inactive"),)),
    "nested-beside-live-root": _ScopeLayout((("nested", "live"), (".", "live")), "nested"),
    "nested-target-inside": _ScopeLayout(
        (("shared/nested", "live"),), "shared/nested", "shared/nested",
    ),
    "nested-in-excluded-tree": _ScopeLayout(
        (("shared/excluded/nested", "live"),), "shared/excluded/nested", "shared/excluded/nested",
    ),
    "nested-below-fixtures": _ScopeLayout(
        (("fixtures/nested", "live"),), "fixtures/nested", "fixtures/nested", True,
    ),
}


def _scope_target(call: dict, surface: str) -> str:
    if surface == "agy-write":
        return call["toolCall"]["args"]["TargetFile"]
    if not surface.endswith("-shell"):
        return call["tool_input"]["file_path"]
    return ""


def scoped_specs(surface: str) -> tuple[CaseSpec, ...]:
    shell = surface.endswith("-shell")
    rows = []
    for name, layout in _SCOPED_LAYOUTS.items():
        if layout.target_project and shell:
            continue
        kinds = [f"state:{project}:{shape}" for project, shape in layout.stores]
        if layout.nested:
            kinds.append(f"checkout:{layout.nested}")
        if layout.arming_target:
            call = _write_payload(surface, str(Path(layout.target_project) / STATE_PATH))
        else:
            call = _payload(surface, "refused" if shell else "production")
            if layout.target_project:
                target = str(Path(layout.target_project) / _scope_target(call, surface))
                call = _write_payload(surface, target)
        branch = "arming" if _is_arming_call(surface, call) else "other"
        rows.append(CaseSpec(name, surface, (*kinds, "call:scope"), branch, call, {}))
    return tuple(rows)


def variable_specs(surface: str) -> tuple[CaseSpec, ...]:
    shell = surface.endswith("-shell")
    explicit_roots = (False, True) if surface.startswith("codex-") else (False,)
    rows = []
    for variable, explicit in itertools.product(VARIABLES, explicit_roots):
        sub_session = variable in {"GIT_CEILING_DIRECTORIES", "GIT_COMMON_DIR"}
        if explicit:
            name = f"variable-explicit-{variable}"
        elif variable == "GIT_DIR":
            name = "variable-beside-live-root"
        else:
            name = f"variable-{variable}"
        if sub_session:
            value = "." if variable == "GIT_CEILING_DIRECTORIES" else "../not-common"
            env = {variable: value}
            if explicit:
                env["CODEX_PROJECT_DIR"] = "sub"
            state_folder = "sub" if (explicit or surface == "claude") else "root"
            kinds = (
                f"state:{state_folder}:live", f"variable:{variable}",
                "session:sub", "call:variable",
            )
            call = (
                _shell_payload(surface, SHELL_COMMANDS["refused"], cwd="sub")
                if shell else _write_payload(surface, f"sub/{WRITE_NAMES['production']}")
            )
        else:
            value = "../other" if variable == "GIT_WORK_TREE" else "../other/.git"
            env = {variable: value}
            if explicit:
                env["CODEX_PROJECT_DIR"] = "."
            kinds = ("state:root:live", f"variable:{variable}", "call:variable")
            call = _payload(surface, "refused" if shell else "production")
        rows.append(CaseSpec(name, surface, kinds, "other", call, env))
    return tuple(rows)


def _scope_git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=root, env=_fixture_env(), capture_output=True, text=True, timeout=10,
    )


def _checkout(folder: Path) -> Path:
    result = _scope_git(folder, "rev-parse", "--show-toplevel")
    result.check_returncode()
    return Path(result.stdout.rstrip("\n")).resolve()


def _excluded(root: Path, project: Path) -> bool:
    if project == root:
        return False
    result = _scope_git(root, "check-ignore", "--quiet", "--", str(project.relative_to(root)))
    if result.returncode not in (0, 1):
        result.check_returncode()
    return result.returncode == 0


def _fixture_directory(root: Path, project: Path) -> bool:
    return bool({"tests", "fixtures"}.intersection(project.relative_to(root).parts))


def build_scoped_case(spec: CaseSpec, where: Path) -> Case:
    layout = _SCOPED_LAYOUTS[spec.name]
    root = _build_fixture_root(where)
    if any("excluded" in Path(project).parts for project, _ in layout.stores):
        (root / ".git/info/exclude").write_text("excluded/\n", encoding="utf-8")
    if layout.nested:
        checkout = root / layout.nested
        checkout.mkdir(parents=True)
        _init_git_repo(checkout)
        assert _checkout(checkout) == checkout

    target = _scope_target(spec.call, spec.surface)
    if target:
        target_path = root / target
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.touch()
        assert stat.S_ISREG(os.lstat(target_path).st_mode)
    else:
        assert spec.call == _payload(spec.surface, "refused")
        assert not os.path.lexists(root / ".h-mad/phase5-shell-allow")

    labels = set()
    if _is_arming_call(spec.surface, spec.call):
        labels.add("D6")
    for project, shape in layout.stores:
        folder = root / project
        labels.update(_write_state(folder, shape))
        assert stat.S_ISDIR(os.lstat(folder / "docs").st_mode)
        excluded = _excluded(root, folder)
        assert excluded == ("excluded" in Path(project).parts)
        if excluded:
            labels.add("D1")
        if _checkout(folder) != root:
            labels.add("D2")
        if _fixture_directory(root, folder):
            labels.add("D3")
    return Case(spec, root, frozenset(labels))


def build_variable_case(spec: CaseSpec, where: Path) -> Case:
    root = _build_fixture_root(where)
    variable = next(kind.split(":", 1)[1] for kind in spec.kinds if kind.startswith("variable:"))
    session = root / "sub" if "session:sub" in spec.kinds else root
    if session != root:
        for folder in (".agents", ".h-mad"):
            (session / folder).mkdir(parents=True)
        if variable == "GIT_COMMON_DIR":
            not_common = root.parent / "not-common"
            not_common.mkdir()
            assert stat.S_ISDIR(os.lstat(not_common).st_mode)
        assert _checkout(session) == root
        redirected = subprocess.run(
            ["git", "-C", str(session), "rev-parse", "--show-toplevel"],
            env=dict(_fixture_env(), **{variable: str(root / spec.env[variable])}),
            capture_output=True, text=True, timeout=10,
        )
        assert redirected.returncode != 0
    else:
        other = root.parent / "other"
        for folder in (".agents", ".h-mad"):
            (other / folder).mkdir(parents=True)
        _init_git_repo(other)
        _scope_git(other, "config", "core.worktree", str(other)).check_returncode()
        assert _checkout(root) == root and not os.path.lexists(other / STATE_PATH)
        redirected = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            env=dict(_fixture_env(), **{variable: str(root / spec.env[variable])}),
            capture_output=True, text=True, check=True, timeout=10,
        )
        assert Path(redirected.stdout.rstrip("\n")).resolve() == other

    target = _scope_target(spec.call, spec.surface)
    if target:
        target_path = root / target
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.touch()
        assert stat.S_ISREG(os.lstat(target_path).st_mode)
    else:
        assert not os.path.lexists(session / ".h-mad/phase5-shell-allow")
    labels = {"D7"} if set(VARIABLES).intersection(spec.env) else set()
    for kind in spec.kinds:
        if kind.startswith("state:"):
            _, folder, shape = kind.split(":")
            project = root if folder in {"root", "."} else root / folder
            labels.update(_write_state(project, shape))
            if shape != "absent" and project != root and _fixture_directory(root, project):
                labels.add("D3")
    return Case(spec, root, frozenset(labels))


def _remove_store(project: Path, shape: str) -> None:
    docs = project / ("Docs" if shape == "case-variant-docs" else "docs")
    if docs.exists() and not docs.is_symlink() and stat.S_IMODE(docs.lstat().st_mode) == 0:
        docs.chmod(0o755)
    target = docs / (STATE_PATH.name.upper() if shape == "case-variant-file" else STATE_PATH.name)
    if not os.path.lexists(target):
        return
    if stat.S_ISDIR(os.lstat(target).st_mode):
        shutil.rmtree(target)
    else:
        target.unlink()


def _canonicalize_store(project: Path) -> None:
    docs = project / "docs"
    state = project / STATE_PATH
    try:
        mode = os.lstat(state).st_mode
    except FileNotFoundError:
        return
    try:
        contents = state.read_bytes() if stat.S_ISREG(state.stat().st_mode) else b"{"
    except OSError:
        contents = b"{"
    if docs.is_symlink():
        docs.unlink()
        docs.mkdir()
    elif "docs" not in os.listdir(project):
        temporary = docs.with_name("canonical-docs")
        docs.rename(temporary)
        temporary.rename(docs)
    if stat.S_ISDIR(mode) and state.is_dir():
        state.rmdir()
    else:
        state.unlink(missing_ok=True)
    state.write_bytes(contents)
    assert "docs" in os.listdir(project) and STATE_PATH.name in os.listdir(docs)
    assert stat.S_ISDIR(os.lstat(docs).st_mode) and stat.S_ISREG(os.lstat(state).st_mode)


def apply_scope_changes(case: Case, changes: frozenset[str], legacy_raise_lifted: bool) -> Case:
    root = case.root
    scope = root
    target_rel = _scope_target(case.spec.call, case.spec.surface)
    if target_rel and ({"D1", "D2", "D3"} & changes):
        target_parent = (root / target_rel).resolve().parent
        if (target_parent == root or root in target_parent.parents) and target_parent.is_dir():
            scope = _checkout((root / _scope_target(case.spec.call, case.spec.surface)).parent)
    stores = (
        ("." if project == "root" else project, shape)
        for kind in case.spec.kinds if kind.startswith("state:")
        for _, project, shape in [kind.split(":")]
    )
    for project, shape in stores:
        folder = root / project
        if shape != "absent" and folder.is_dir() and ({"D1", "D2", "D3"} & changes):
            owner = _checkout(folder)
            authority = scope if owner == scope else root
            discard = (
                ("D1" in changes and _excluded(authority, folder))
                or ("D2" in changes and owner not in {root, scope})
                or ("D3" in changes and _fixture_directory(authority, folder))
            )
            if discard and (shape != "not-object" or legacy_raise_lifted):
                _remove_store(folder, shape)
                continue
        if "D4" in changes and "D4" in case.labels and shape in {*PRESENCE_SHAPES[1:], "fifo"}:
            _canonicalize_store(folder)
    return case


def _load_test_support():
    path = ROOT / "h-mad/tests/tdd_gate_support.py"
    name = "_differential_gate_test_support"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load the hook decoder from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_TEST_SUPPORT = _load_test_support()


_SHIM_LOCK = threading.Lock()
_BASELINE_LOCK = threading.Lock()
_SHIM_DIR: tempfile.TemporaryDirectory[str] | None = None


def _shim_templates() -> tuple[Path, Path]:
    global _SHIM_DIR
    with _SHIM_LOCK:
        if _SHIM_DIR is not None:
            base = Path(_SHIM_DIR.name)
            git_shim = base / "git"
            bad_shim = base / "malformed"
            if git_shim.is_file() and bad_shim.is_file():
                return git_shim, bad_shim
        _SHIM_DIR = tempfile.TemporaryDirectory(prefix="phase5-diff-shim-")
        base = Path(_SHIM_DIR.name)
        git_shim = base / "git"
        _shell_shim(
            git_shim,
            'if [ -n "${_DIFF_PROBE_GIT_LOG:-}" ]; then\n'
            '    printf \'.\\n\' >> "$_DIFF_PROBE_GIT_LOG"\n'
            'fi\n'
            'if [ -n "${_DIFF_PROBE_GIT_EXEC:-}" ]; then\n'
            '    exec "$_DIFF_PROBE_GIT_EXEC" "$@"\n'
            'fi\n',
        )
        bad_shim = base / "malformed"
        _shell_shim(bad_shim, "printf '%s\\n' 'broken hook answer {'\n")
        subprocess.run([str(git_shim)], env={"PATH": os.defpath}, check=True, timeout=10)
        subprocess.run([str(bad_shim)], env={"PATH": os.defpath}, capture_output=True, check=True, timeout=10)
        return git_shim, bad_shim


def _hook_environment(root: Path, overrides: dict[str, str]) -> dict[str, str]:
    env = _TEST_SUPPORT.hermetic_env(
        PYTHONPATH="", PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1",
    )
    env = {
        name: value for name, value in env.items()
        if not name.startswith(("GIT_", "HMAD_", "PYTHONHOME", "_DIFF_PROBE_"))
        and name not in {"BASH_ENV", "ENV", "XDG_CONFIG_HOME"}
    }
    for name, value in overrides.items():
        env[name] = str(root / value) if name.startswith("GIT_") or name == "CODEX_PROJECT_DIR" else value
    return env


def _shell_shim(path: Path, body: str) -> None:
    path.write_text("#!/bin/sh\n" + body, encoding="utf-8")
    path.chmod(0o755)


def _run_hook(tree: Path, case: Case, interpreter: str, *, malformed: bool) -> Verdict:
    root = case.root.resolve()
    host = case.spec.surface.split("-", 1)[0]
    package = tree.resolve() / "h-mad"
    wrapper = package / "bin/hmad-dispatch"
    env = _hook_environment(root, case.spec.env)
    path = env.get("PATH", os.defpath)
    git = shutil.which("git", path=path)
    if git is None:
        raise FileNotFoundError("git is required for the differential probe")
    git_shim, bad_shim = _shim_templates()

    with tempfile.TemporaryDirectory(prefix="run-", dir=root.parent) as directory:
        scratch = Path(directory)
        home = scratch / "home"
        home.mkdir()
        env["HOME"] = str(home)
        env["PATH"] = os.pathsep.join((str(scratch), str(wrapper.parent), path))
        selected = shutil.which("hmad-dispatch", path=env["PATH"])
        if selected != str(wrapper) or wrapper.resolve() != wrapper:
            raise ValueError(f"hmad-dispatch did not resolve to the selected tree's wrapper: {selected!r}")
        git_log = scratch / "git.log"
        env["_DIFF_PROBE_GIT_LOG"] = str(git_log)
        env["_DIFF_PROBE_GIT_EXEC"] = os.path.abspath(git)
        (scratch / "git").symlink_to(git_shim)
        (scratch / "python3").symlink_to(Path(interpreter).absolute())

        session = root / "sub" if "session:sub" in case.spec.kinds else root
        cwd = session
        if host == "claude":
            launcher, hook = "bash", "h-mad-tdd-gate.sh"
            env["CLAUDE_PROJECT_DIR"] = str(session)
        elif host == "agy":
            launcher, hook = "python3", "h-mad-agy-tdd-gate.py"
            cwd = session / ".agents"
        elif host == "codex":
            launcher, hook = "python3", "h-mad-codex-tdd-gate.py"
        else:
            raise ValueError(f"unknown hook surface {case.spec.surface!r}")

        if malformed:
            shim = scratch / launcher
            shim.unlink(missing_ok=True)
            shim.symlink_to(bad_shim)

        payload = _hook_payload(host, case.spec.call, root)
        result = subprocess.run(
            [launcher, str(package / "hooks" / hook)],
            cwd=cwd, env=env, input=json.dumps(payload), capture_output=True, text=True,
            check=False, timeout=20,
        )
        outcome = _TEST_SUPPORT.host_decision(host, result)
        git_processes = git_log.read_bytes().count(b"\n") if git_log.exists() else 0
    return Verdict(outcome.decision, outcome.kind, git_processes)


def _hook_payload(host: str, call: dict, root: Path) -> dict:
    payload = call.copy()
    if host == "agy":
        tool = {**payload["toolCall"]}
        args = {**tool.get("args", {})}
        tool["args"] = args
        payload["toolCall"] = tool
        path_keys = ("Cwd", "TargetFile", "Path")
    else:
        args = {**payload.get("tool_input", {})}
        payload["tool_input"] = args
        path_keys = ("workdir", "file_path", "path")
        for key in ("cwd", "project_dir"):
            if isinstance(payload.get(key), str) and payload[key]:
                payload[key] = str(root / payload[key])
    for key in path_keys:
        if isinstance(args.get(key), str) and args[key]:
            args[key] = str(root / args[key])
    return payload


def run_hook(tree: Path, case: Case, interpreter: str) -> Verdict:
    for kind in case.spec.kinds:
        if kind.endswith(":inaccessible-docs"):
            _, location, _ = kind.split(":")
            project = case.root if location in {"root", "."} else case.root / location
            check = (
                "import os, sys\n"
                "try:\n    os.lstat(sys.argv[1])\n"
                "except (FileNotFoundError, NotADirectoryError):\n    sys.exit(1)\n"
                "except OSError:\n    sys.exit(0)\n"
                "sys.exit(1)"
            )
            result = subprocess.run([interpreter, "-I", "-c", check, str(project / STATE_PATH)],
                                    check=False, timeout=10)
            if result.returncode != 0:
                raise AssertionError("lstat must raise an OSError other than absence")
    return _run_hook(tree, case, interpreter, malformed=False)


def calibrate_decoders(tree: Path, where: Path, interpreter: str) -> None:
    where = where.resolve()
    root = where / "repo"
    (root / ".agents").mkdir(parents=True)
    env = _hook_environment(root, {})
    home = where / "home"
    home.mkdir()
    env["HOME"] = str(home)
    subprocess.run(["git", "init", "-q"], cwd=root, env=env, check=True, timeout=10)
    (root / "subject.py").touch()
    state = root / "docs/.bkit-memory.json"
    state.parent.mkdir()
    calls = {
        "claude": ("claude", {"tool_name": "Write", "tool_input": {"file_path": "subject.py"}}),
        "codex": ("codex-shell", {"tool_name": "exec_command", "tool_input": {"cmd": "pwd", "workdir": "."}}),
        "agy": ("agy-shell", {"toolCall": {"name": "run_command", "args": {"CommandLine": "pwd", "Cwd": "."}}}),
    }
    deny_kinds = {"claude": "judge-error", "codex": "", "agy": "judge-error"}
    for host, (surface, payload) in calls.items():
        case = Case(CaseSpec(f"decoder-{host}", surface, (), "other", payload, {}), root, frozenset())
        state.unlink(missing_ok=True)
        allow = run_hook(tree, case, interpreter)
        state.write_text("{", encoding="utf-8")
        deny = run_hook(tree, case, interpreter)
        malformed = _run_hook(tree, case, interpreter, malformed=True)
        actual = [(verdict.decision, verdict.kind) for verdict in (allow, deny, malformed)]
        expected = [("allow", ""), ("deny", deny_kinds[host]), ("invalid", "")]
        if actual != expected:
            raise ValueError(f"{host} decoder controls expected {expected!r}, observed {actual!r}")


def check_admission_control(baseline: Path, new_tree: Path, where: Path, interpreter: str) -> None:
    where = where.resolve()
    root = _build_fixture_root(where)
    _write_state(root, "live")
    allowance = root / ".h-mad/phase5-shell-allow"
    command = "true"
    for host in ("codex", "agy"):
        surface = f"{host}-shell"
        for declared in (True, False):
            allowance.write_text(command + "\n" if declared else "", encoding="utf-8")
            for spelling in (command, f"hmad-dispatch run --timeout 60 -- {command}"):
                payload = _shell_payload(surface, spelling)
                case = Case(
                    CaseSpec("admission-control", surface, (), "other", payload, {}),
                    root, frozenset(),
                )
                for side, tree in (("old", baseline), ("new", new_tree)):
                    verdict = run_hook(tree, case, interpreter)
                    expected_decision = "allow" if declared else "deny"
                    expected_kind = "" if (declared or host == "codex") else "shell-not-admitted"
                    if (verdict.decision, verdict.kind) != (expected_decision, expected_kind):
                        raise ValueError(
                            f"{host} {side} admission control failed for {spelling!r} "
                            f"(declared={declared}): {verdict!r}"
                        )


_PRECONDITIONS_LOCK = threading.Lock()
_PRECONDITIONS_VERIFIED: set[tuple[Path, Path]] = set()


def ensure_preconditions(
    interpreter: str, baseline: Path | None = None, *, force: bool = False,
) -> None:
    resolved_python = Path(interpreter).resolve(strict=True)
    cache_key = (resolved_python, ROOT.resolve())
    with _PRECONDITIONS_LOCK:
        if not force and cache_key in _PRECONDITIONS_VERIFIED:
            return
        verified_base = (
            baseline.resolve()
            if baseline is not None and _is_baseline_extraction(baseline)
            else None
        )
        with tempfile.TemporaryDirectory(prefix="phase5-precond-") as tmp:
            scratch = Path(tmp)
            active_base = (
                verified_base
                if verified_base is not None
                else extract_old_tree(scratch / "baseline")
            )
            calibrate_decoders(active_base, scratch / "decoders", str(resolved_python))
            check_admission_control(active_base, ROOT, scratch / "admission", str(resolved_python))
        _PRECONDITIONS_VERIFIED.add(cache_key)


# Interpreter resolution, baseline extraction, and oracle.


def resolve_interpreters(launchers: Sequence[str] | None = None) -> dict[str, str | None]:
    if launchers is None:
        versions = set(range(11, 16))
        for directory in os.get_exec_path():
            try:
                entries = os.listdir(directory)
            except OSError:
                continue
            for entry in entries:
                match = re.fullmatch(r"python3\.(\d+)", entry)
                if match and int(match[1]) >= 11:
                    versions.add(int(match[1]))
        launchers = ["/usr/bin/python3", "python3", *(f"python3.{v}" for v in sorted(versions))]
    resolved = {}
    identities = set()
    for launcher in launchers:
        command = shutil.which(launcher)
        if command is None:
            name = Path(launcher).name.replace("python", "py", 1)
            resolved.setdefault(name, None)
            continue
        output = subprocess.check_output(
            [command, "-I", "-c", "import json, sys; print(json.dumps([sys.executable, list(sys.version_info[:2])]))"],
            text=True, timeout=10,
        )
        executable, version = json.loads(output)
        path = Path(executable).resolve(strict=True)
        info = path.stat()
        identity = info.st_dev, info.st_ino
        if identity in identities:
            continue
        identities.add(identity)
        base = "py%d.%d" % tuple(version)
        key = base
        index = 1
        while resolved.get(key) is not None:
            index += 1
            key = f"{base}-{index}"
        resolved[key] = str(path)
    return resolved


@lru_cache(maxsize=8)
def _baseline_files(repo: str, commit: str) -> tuple[tuple[str, ...], tuple[tuple[str, bytes, int], ...]]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    archive = subprocess.check_output(
        ["git", "archive", "--format=tar", "--end-of-options", commit,
         "h-mad/hooks", "h-mad/scripts", "h-mad/bin"],
        cwd=repo, env=env, timeout=30,
    )
    dirs = set()
    files = []
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as tar:
        for member in tar.getmembers():
            if member.isdir():
                dirs.add(member.name)
            elif member.isfile():
                parent = str(Path(member.name).parent)
                if parent != ".":
                    dirs.add(parent)
                extracted = tar.extractfile(member)
                assert extracted is not None
                files.append((member.name, extracted.read(), member.mode))
    return tuple(sorted(dirs)), tuple(files)


def extract_old_tree(dest: Path, commit: str = BASELINE) -> Path:
    dirs, files = _baseline_files(str(ROOT), commit)
    dest.mkdir(parents=True, exist_ok=True)
    for rel in dirs:
        (dest / rel).mkdir(parents=True, exist_ok=True)
    for rel, content, mode in files:
        path = dest / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        if mode & 0o111:
            path.chmod(mode)
    (dest / BASELINE_MARKER).write_text(f"{commit}\n", encoding="utf-8")
    return dest.resolve()


def _is_baseline_extraction(candidate: Path, commit: str = BASELINE) -> bool:
    marker = candidate / BASELINE_MARKER
    if not marker.is_file():
        return False
    try:
        if marker.read_text(encoding="utf-8").strip() != commit:
            return False
        _, files = _baseline_files(str(ROOT), commit)
        for rel, expected_bytes, _ in files:
            target = candidate / rel
            if not target.is_file() or target.read_bytes() != expected_bytes:
                return False
    except OSError:
        return False
    return True


def _oracle_baseline(scratch: Path) -> Path:
    for ancestor in (scratch.parent, scratch.parent.parent):
        candidate = ancestor / "baseline"
        if _is_baseline_extraction(candidate):
            return candidate.resolve()
    shared = scratch.parent / ".oracle-baseline"
    with _BASELINE_LOCK:
        if not _is_baseline_extraction(shared):
            extract_old_tree(shared)
    return shared.resolve()


def build_twin(spec: CaseSpec, where: Path, changes: frozenset[str], legacy_raise_lifted: bool) -> Case:
    case = build_case(spec, where)
    if "D7" in changes:
        env = {key: value for key, value in case.spec.env.items() if key not in VARIABLES}
        case = case._replace(spec=case.spec._replace(env=env))
    if changes:
        case = apply_scope_changes(case, changes, legacy_raise_lifted)
    return case


def _twin_holds_governing_state(twin: Case, changes: frozenset[str]) -> bool:
    folders = [
        twin.root if folder in {"root", "."} else twin.root / folder
        for kind in twin.spec.kinds if kind.startswith("state:")
        for _, folder, _ in [kind.split(":")]
    ]
    for folder in folders:
        docs = folder / "docs"
        if docs.exists() and not docs.is_symlink() and stat.S_IMODE(docs.lstat().st_mode) == 0:
            return True
        state = folder / STATE_PATH
        if not os.path.lexists(state):
            continue
        try:
            mode = state.lstat().st_mode if "D4" in changes else state.stat().st_mode
            if not stat.S_ISREG(mode):
                if "D4" in changes or not state.is_symlink():
                    return True
                continue
            parsed = json.loads(state.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, RecursionError):
            return True
        if not isinstance(parsed, dict):
            return True
        records = parsed.get("orchestrator_state", {})
        if not isinstance(records, dict):
            return True
        if any(isinstance(value, dict) and value.get("phase") == "step5" for value in records.values()):
            return True
    return False


def _restore_docs(where: Path) -> None:
    for parent, dirs, _ in os.walk(where):
        if "docs" in dirs:
            docs = Path(parent) / "docs"
            if stat.S_IMODE(docs.lstat().st_mode) == 0:
                docs.chmod(0o755)


def expected_verdict(spec: CaseSpec, interpreter: str, changes: frozenset[str], scratch: Path,
                     legacy_raise_lifted: bool = False) -> Verdict:
    scratch.mkdir(parents=True, exist_ok=True)
    tree = _oracle_baseline(scratch)
    with tempfile.TemporaryDirectory(dir=scratch) as tmp:
        where = Path(tmp)
        try:
            twin = build_twin(spec, where / "twin", changes, legacy_raise_lifted)
            verdict = run_hook(tree, twin, interpreter)
            if "D6" in changes and spec.branch == "arming" and _twin_holds_governing_state(twin, changes):
                host = spec.surface.split("-", 1)[0]
                return Verdict("deny", "" if host == "codex" else "arming-input", verdict.git_processes)
            return verdict
        finally:
            _restore_docs(where / "twin")


def _compare_cell(scratch: Path, executable: str, spec: CaseSpec) -> str | None:
    with tempfile.TemporaryDirectory(dir=scratch) as temporary:
        cell = Path(temporary)
        changes = CHANGES_IN_FORCE[spec.surface, spec.branch]
        lifted = spec.surface == "claude" or spec.surface in LEGACY_RAISE_LIFTED
        try:
            required = expected_verdict(spec, executable, changes, cell / "oracle", lifted)
            actual = run_hook(ROOT, build_case(spec, cell / "actual"), executable)
        finally:
            _restore_docs(cell / "actual")
        if required.decision not in {"allow", "deny"} or actual[:2] != required[:2]:
            return spec.name
    return None


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    try:
        rows = crossed_corpus()
        if rows:
            _git_template()
            _fixture_feature()
        count = 0
        with tempfile.TemporaryDirectory(prefix="phase5-differential-") as directory:
            scratch = Path(directory)
            baseline = extract_old_tree(scratch / "baseline")
            for ident, executable in resolve_interpreters().items():
                if executable is None:
                    print(f"SKIP {ident}: interpreter unavailable", file=sys.stderr)
                    continue
                ensure_preconditions(executable, baseline, force=True)
                active_rows = []
                for spec in rows:
                    if os.geteuid() == 0 and spec.name.startswith("malformed-inaccessible-docs-"):
                        print(f"SKIP {spec.name}: lstat must raise an OSError other than absence", file=sys.stderr)
                        continue
                    active_rows.append(spec)
                if len(active_rows) <= 1 or sys.getprofile() is not None:
                    outcomes = [_compare_cell(scratch, executable, spec) for spec in active_rows]
                else:
                    with ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as pool:
                        outcomes = list(pool.map(lambda s: _compare_cell(scratch, executable, s), active_rows))
                for failed in outcomes:
                    if failed is not None:
                        print(f"DIFFERENTIAL: FAIL case={failed}")
                        return 0
                    count += 1
    except (OSError, subprocess.SubprocessError, ValueError, RuntimeError) as exc:
        print(f"differential error: {exc}", file=sys.stderr)
        return 2
    print(f"DIFFERENTIAL: PASS cases={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
