#!/usr/bin/env python3
"""Run an impl-plan's prescribed python blocks against their target module's guards.

A test module can guard ITSELF: a test that reads its own source and refuses a
literal (`test_hmad_dispatch.py` bans the temp-dir constructor) or a count
(`test_h_mad_collect_report_docs.py` allows one hand-rolled bash extraction). An
impl-plan that prescribes a helper block for such a module is then wrong in a way
no reader sees: the block is correct Python, and the collision exists only once
the block sits inside the module. pin-agents-tail-banner passed 53 audit cycles
with one, and its first RED dispatch returned 3 failures where 2 were stated.

For each python block attributed to exactly one EXISTING test module (its own
first-line comment names it, or the prose since the previous fence does), this appends the block to a scratch copy of that module and runs the
module's self-source guards with reads of the module's own path through
`open`/`io.open`/`Path.read_text`/`Path.read_bytes` redirected to the copy
(`tokenize.open`, `linecache`, `os.open` and subprocesses are not). A guard is
selected by what it does, never by its name (only one of the repo's three is
called `*_guard`): a test that reads its own file (`read_text`/`read_bytes`/`open`
of `__file__`, of `Path(__file__)`, of a name bound to either, or of
`<dir> / "<own name>"`), directly or through a module- or class-level helper or
constant that does.

    python3 h_mad_prescribed_block_guards.py <impl-plan.md> [--repo-root DIR]

Verdicts, one canonical token line:

    PRESCRIBED-BLOCKS: PASS checked=N skipped=M guards=G                    exit 0
    PRESCRIBED-BLOCKS: FAIL collisions=K unrunnable=U baseline_red=B ...    exit 0
    PRESCRIBED-BLOCKS: INCOMPLETE unrunnable=U baseline_red=B ...           exit 0
    PRESCRIBED-BLOCKS: UNREADABLE                                           exit 2

followed by `COLLISION:` / `BASELINE-RED:` / `UNRUNNABLE:` / `WRAPPED:` lines.
`INCOMPLETE` is not a pass: a guard that could not run, or was already red on the
live module, checked nothing. Read the token, never `$?`.

How the block goes in: verbatim, when the module plus the block still parses, so
a guard that `ast.parse`s its own source sees it as code. An excerpt that does not
parse in place is appended as a string literal instead and reported `WRAPPED:`;
a text guard still sees it, an AST guard does not.

Why reads are redirected rather than `__file__` rebound: the module is imported
from its live path, so its `Path(__file__).parent / ...` sibling lookups keep
working, while a constant read at import, a helper, or a decorated guard all read
the copy. The redirect is installed before the import.

What it deliberately does not check:
- a block whose prose names no test module, two of them, or one that resolves to
  nothing (counted as `skipped`) — a new module has no guards to collide with, so
  prose that says `create`/`new` disables suffix resolution;
- a template `**Code structure**` block under a `**Production file**` that is not
  a test module: that block is the production file's code, with the test file
  named beside it (when the production file IS a test module, it is checked);
- a mutation row's `replace`/`find` text, which is meant to trip a guard;
- a guard that reads ANOTHER module's source (`dbe.__file__`);
- a guard the plan itself adds. It does not exist when this runs, before RED.
A block that REPLACES code rather than adding it can over-report a count guard,
because the old code is still in the copy. Read the guard and judge.

The live module is never written: the copy goes to a temp directory.
"""
from __future__ import annotations

import argparse
import ast
import builtins
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

_PY_INFO = {"python", "python3", "py"}
_TEST_PATH = re.compile(r"(?<![\w/.-])((?:[\w.-]+/)*test_\w+\.py)(?![\w/])")
_MUTATION_PROSE = re.compile(r"`(?:replace|find)`")  # M:PBG-MUTATION-SKIP
_PRODUCTION_LINE = re.compile(r"\*\*Production file\*\*:?[ \t]*`([^`]+)`")
_LABEL = re.compile(r"^\*\*([^*\n]+)\*\*:", re.M)
_PY_PATH = re.compile(r"[\w./-]+\.py\b")
_NEW_MODULE_PROSE = re.compile(r"\b(?:create[sd]?|new)\b", re.I)
# A fence the shared scanner cannot see: indented 4+ inside a list item.
_INDENTED_OPEN = re.compile(r"^(?P<indent>[ \t]{4,})(?P<marks>`{3,}|~{3,})(?P<info>[^`~]*)$")
_CHILD_SECONDS = 120


def _blocks(text: str) -> tuple[list[tuple[int, str, str]], list[int]]:
    """(fence line, preceding prose, body) for every python fence, and unclosed ones.

    The prose is everything since the previous fence or heading, so a path named
    above an EARLIER block never attributes a later one.
    """
    from h_mad_doc_block_exec import _fence_events

    lines = text.splitlines(keepends=True)
    out: list[tuple[int, str, str]] = []
    unclosed: list[int] = []
    prose: list[str] = []
    current: tuple[int, str, list[str]] | None = None
    nested: tuple[int, str, list[str], str, str] | None = None  # + indent, closer

    def is_py(info: str) -> bool:
        words = info.split()
        return bool(words) and words[0] in _PY_INFO

    for event in _fence_events(text):
        line = lines[event.lineno - 1]
        if nested is not None:
            if event.kind == "prose":
                if line.rstrip("\r\n").rstrip() == nested[3] + nested[4]:
                    out.append((nested[0], nested[1], "".join(nested[2])))
                    nested = None
                    prose = []
                else:
                    body = line[len(nested[3]):] if line.startswith(nested[3]) else line.lstrip()
                    nested[2].append(body)
                continue
            unclosed.append(nested[0])  # a fence or heading cut it off
            nested = None
        if event.kind == "open":
            current = (event.lineno, "".join(prose), []) if is_py(event.info) else None
            prose = []  # M:PBG-PROSE-RESET
        elif event.kind == "body":
            if current is not None:
                current[2].append(line)
        elif event.kind == "close":
            if current is not None:
                out.append((current[0], current[1], "".join(current[2])))
            current = None
        elif event.kind == "heading":
            prose = [line]  # M:PBG-HEADING-RESET
        else:
            match = _INDENTED_OPEN.match(line.rstrip("\r\n"))
            if match and is_py(match["info"]):  # M:PBG-INDENTED
                nested = (event.lineno, "".join(prose), [], match["indent"], match["marks"])
                prose = []
            else:
                prose.append(line)
    if current is not None:
        unclosed.append(current[0])
    if nested is not None:
        unclosed.append(nested[0])
    return out, unclosed


def _test_index(root: Path) -> list[Path]:
    return [p for p in root.rglob("test_*.py")
            if ".git" not in p.parts and "__pycache__" not in p.parts]


def _resolve(token: str, root: Path, index_cache: list, suffix: bool = True) -> Path | None:
    """The repo-relative path, else the ONE test file whose path ends with the token.

    One rule covers a bare basename and a subproject-relative path quoted from a
    spec (`tests/test_x.py` for `h-mad/tests/test_x.py`). Two matches is no match.
    `suffix=False` when the prose announces a NEW module: a same-named file in
    another sub-project is not the block's target.
    """
    candidate = root / token
    if candidate.is_file():
        return candidate
    if not suffix:  # M:PBG-NEW-NO-SUFFIX
        return None
    if not index_cache:
        index_cache.append(_test_index(root))
    hits = [p for p in index_cache[0]
            if p.relative_to(root).as_posix().endswith("/" + token)]
    return hits[0] if len(hits) == 1 else None  # M:PBG-UNIQUE-SUFFIX


def _target(prose: str, body: str, root: Path, index_cache: list) -> Path | None:
    if _MUTATION_PROSE.search(prose):
        return None
    suffix = not _NEW_MODULE_PROSE.search(prose)
    first = next((ln.strip() for ln in body.splitlines() if ln.strip()), "")
    paths = _PY_PATH.findall(first) if first.startswith("#") else []  # M:PBG-SELF-NAMED-LEADS
    if paths and _TEST_PATH.fullmatch(paths[0]):
        # `# h-mad/tests/test_x.py — added beside ...`: the block names its own file.
        resolved = _resolve(paths[0], root, index_cache, suffix)  # M:PBG-SELF-NAMED
        return resolved.resolve() if resolved else None
    labels = _LABEL.findall(prose)
    production = _PRODUCTION_LINE.search(prose)  # M:PBG-PRODUCTION
    if production and labels and labels[-1].strip() == "Code structure":  # M:PBG-CODE-STRUCTURE
        # The template's **Code structure** block is the PRODUCTION file's code,
        # whatever test file is named beside it. Checked only when that file is
        # itself a test module (a harness change), never against the test file.
        token = production[1]
        if not _TEST_PATH.fullmatch(token):  # M:PBG-PRODUCTION-TARGET
            return None
        resolved = _resolve(token, root, index_cache, suffix)
        return resolved.resolve() if resolved else None
    targets: set[Path] = set()
    for token in set(_TEST_PATH.findall(prose)):
        resolved = _resolve(token, root, index_cache, suffix)
        if resolved is None:
            return None  # M:PBG-UNRESOLVED-REFUSES
        targets.add(resolved.resolve())
    return next(iter(targets)) if len(targets) == 1 else None


class _Own:
    """What counts as the module's own file: its basename and the names bound to it."""

    def __init__(self, basename: str):
        self.basename = basename
        self.paths: set[str] = set()    # names bound to the file's PATH
        self.readers: set[str] = set()  # names bound to its CONTENT, or helpers returning it

    def _named(self, node: ast.AST, names: set[str]) -> bool:
        return ((isinstance(node, ast.Name) and node.id in names)
                or (isinstance(node, ast.Attribute) and node.attr in names))  # self.SOURCE

    def is_path(self, node: ast.AST) -> bool:
        """`__file__`, `Path(__file__)`, a name bound to either, `<dir> / "<own name>"`,
        each optionally under `.resolve()`/`.absolute()`."""
        while (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
               and node.func.attr in {"resolve", "absolute"}):
            node = node.func.value
        if (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)
                and isinstance(node.right, ast.Constant)
                and node.right.value == self.basename):  # M:PBG-DIR-SLASH-NAME
            return True
        if self._named(node, self.paths):  # M:PBG-PATH-NAMES
            return True
        if isinstance(node, ast.Call) and len(node.args) == 1:
            node = node.args[0]
        return isinstance(node, ast.Name) and node.id == "__file__"

    def reads(self, tree: ast.AST) -> bool:
        """Reads its own source, directly or through a name that does.

        `Path(__file__).parent / "specs"` names `__file__` too, and is not a read.
        """
        for node in ast.walk(tree):
            if self._named(node, self.readers):
                return True
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if (isinstance(func, ast.Attribute)
                    and func.attr in {"read_text", "read_bytes", "open"}  # M:PBG-READ-METHODS
                    and self.is_path(func.value)):
                return True
            if (isinstance(func, ast.Name) and func.id == "open" and node.args  # M:PBG-OPEN
                    and self.is_path(node.args[0])):
                return True
        return False

    def learn(self, tree: ast.Module) -> None:
        """Module- and class-level names bound to the file or its content, to a fixed point."""
        scopes = [tree.body] + [n.body for n in tree.body if isinstance(n, ast.ClassDef)]
        while True:
            before = len(self.paths) + len(self.readers)
            for body in scopes:
                for node in body:
                    if (isinstance(node, ast.FunctionDef) and not node.name.startswith("test")
                            and self.reads(node)):
                        self.readers.add(node.name)  # M:PBG-READERS-HELPER
                    elif isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
                        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                        names = {t.id for t in targets if isinstance(t, ast.Name)}
                        if self.is_path(node.value):
                            self.paths.update(names)
                        elif self.reads(node.value):  # M:PBG-READERS
                            self.readers.update(names)
            if len(self.paths) + len(self.readers) == before:
                return


def _guards(module: Path) -> list[tuple[str, list[str]]]:
    """(node id within the module, fixture parameter names) for each self-source test."""
    tree = ast.parse(module.read_text(encoding="utf-8"))
    own = _Own(module.name)
    own.learn(tree)
    found: list[tuple[str, list[str]]] = []

    def params(fn: ast.FunctionDef, method: bool) -> list[str]:
        names = [a.arg for a in fn.args.posonlyargs + fn.args.args + fn.args.kwonlyargs]
        return names[1:] if method else names

    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test"):
            if own.reads(node):  # M:PBG-SELECT-BY-BEHAVIOUR
                found.append((node.name, params(node, False)))
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            for item in node.body:
                if (isinstance(item, ast.FunctionDef) and item.name.startswith("test")
                        and own.reads(item)):
                    found.append((f"{node.name}::{item.name}", params(item, True)))
    return found


def _append(module_text: str, block: str) -> tuple[str, bool]:
    """(the copy's text, whether the block had to be wrapped as a string literal)."""
    joined = module_text.rstrip("\n") + "\n\n\n" + block
    try:
        ast.parse(joined)  # M:PBG-AS-CODE
        return joined, False
    except SyntaxError:
        pass
    for quote in ("'''", '"""'):
        if quote not in block and not block.endswith("\\"):
            return module_text + f"\n\n_H_MAD_PRESCRIBED_BLOCK = r{quote}{block}{quote}\n", True
    return module_text + "\n\n" + "".join(f"# {ln}\n" for ln in block.splitlines()), True  # M:PBG-WRAP-FALLBACK


def _redirect(live: Path, source: Path) -> None:
    """Every read of the live module's path reads `source` instead."""
    live = live.resolve()
    orig_open, orig_read_text, orig_read_bytes = io.open, Path.read_text, Path.read_bytes

    def is_live(target: object) -> bool:
        if not isinstance(target, (str, os.PathLike)):
            return False
        try:
            return Path(target).resolve() == live
        except (OSError, ValueError):
            return False

    def open_(file, *args, **kwargs):
        return orig_open(source if is_live(file) else file, *args, **kwargs)

    def read_text(self, *args, **kwargs):
        return orig_read_text(source if is_live(self) else self, *args, **kwargs)

    def read_bytes(self):
        return orig_read_bytes(source if is_live(self) else self)

    # pathlib's read_text/read_bytes go through io.open on 3.11-3.13, so patching them
    # too is belt and braces for a pathlib that stops doing so; a mutant removing
    # either is equivalent on this host and is deliberately not a spec row.
    builtins.open = io.open = open_
    Path.read_text = read_text  # type: ignore[method-assign]
    Path.read_bytes = read_bytes  # type: ignore[method-assign]


def _child(module: str, source: str, names: list[str], result_path: str) -> int:
    """Import the live module with its own reads redirected, run each named guard."""
    path = Path(module)
    out: dict = {"results": {}}
    sys.dont_write_bytecode = True  # the live tree is never written, .pyc included
    _redirect(path, Path(source))  # M:PBG-REDIRECT
    sys.path.insert(0, str(path.parent))
    try:
        spec = importlib.util.spec_from_file_location(f"_hmad_pbg_{path.stem}", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except BaseException as error:  # noqa: BLE001 — any import failure is unrunnable
        out = {"import_error": f"{type(error).__name__}: {error}"}
    else:
        for name in names:
            try:
                if "::" in name:
                    cls_name, meth = name.split("::")
                    getattr(getattr(mod, cls_name)(), meth)()
                else:
                    getattr(mod, name)()
                out["results"][name] = {"status": "pass"}
            except AssertionError as error:
                first = (str(error).splitlines() or [""])[0]
                out["results"][name] = {"status": "fail", "msg": first or "assertion failed"}
            except BaseException as error:  # noqa: BLE001 — a red guard is red
                out["results"][name] = {"status": "fail",
                                        "msg": f"{type(error).__name__}: {error}"}
    Path(result_path).write_text(json.dumps(out), encoding="utf-8")
    return 0


def _run_guards(module: Path, source: Path, names: list[str], root: Path) -> dict:
    """The child's result, read from a file of its own — never scraped from stdout."""
    with tempfile.TemporaryDirectory(prefix="hmad-pbg-result-") as tmp:
        result = Path(tmp) / "result.json"
        try:
            proc = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "--child",
                 str(module), str(source), json.dumps(names), str(result)],
                capture_output=True, text=True, cwd=root, timeout=_CHILD_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return {"import_error": f"guards did not finish in {_CHILD_SECONDS}s"}  # M:PBG-TIMEOUT
        try:
            data = json.loads(result.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = None
    if isinstance(data, dict) and ("import_error" in data or isinstance(data.get("results"), dict)):
        return data
    tail = (proc.stderr.strip().splitlines() or ["no output"])[-1]
    return {"import_error": f"child left no result (rc={proc.returncode}): {tail}"}


def check(plan: Path, root: Path) -> tuple[str, list[str]]:
    text = plan.read_text(encoding="utf-8")
    root = root.resolve()
    index_cache: list = []
    details: list[str] = []
    checked = skipped = collisions = unrunnable = baseline_red = 0
    module_state: dict[Path, set[str] | None] = {}
    all_guards: set[str] = set()

    def rel(path: Path) -> str:
        try:
            return str(path.relative_to(root))
        except ValueError:
            return str(path)

    blocks, unclosed = _blocks(text)
    for lineno in unclosed:
        unrunnable += 1
        details.append(f"UNRUNNABLE: {plan}:{lineno} -- python fence never closed")

    with tempfile.TemporaryDirectory(prefix="hmad-pbg-") as scratch:
        for lineno, prose, body in blocks:
            module = _target(prose, body, root, index_cache)
            if module is None:
                skipped += 1
                continue
            checked += 1
            if module not in module_state:
                module_state[module] = None
                try:
                    guards = _guards(module)
                except (SyntaxError, UnicodeDecodeError) as error:
                    unrunnable += 1
                    details.append(f"UNRUNNABLE: {rel(module)} -- {type(error).__name__}: {error}")
                    continue
                runnable: list[str] = []
                for name, extra in guards:
                    if extra:  # M:PBG-FIXTURE
                        unrunnable += 1
                        details.append(f"UNRUNNABLE: {rel(module)}::{name} -- takes {', '.join(extra)}")
                    else:
                        runnable.append(name)
                green: set[str] = set()
                if runnable:
                    base = _run_guards(module, module, runnable, root)
                    if "import_error" in base:
                        unrunnable += 1
                        details.append(f"UNRUNNABLE: {rel(module)} -- {base['import_error']}")
                        continue
                    for name in runnable:
                        if base["results"].get(name, {}).get("status") == "pass":  # M:PBG-BASELINE
                            green.add(name)
                        else:
                            baseline_red += 1
                            details.append(f"BASELINE-RED: {rel(module)}::{name}")
                module_state[module] = green
                all_guards.update(f"{module}::{n}" for n in green)
            green = module_state[module]
            if not green:
                continue
            copy_dir = Path(scratch) / f"b{lineno}"
            copy_dir.mkdir()
            copy = copy_dir / module.name
            copy_text, wrapped = _append(module.read_text(encoding="utf-8"), body)
            copy.write_text(copy_text, encoding="utf-8")
            if wrapped:
                details.append(f"WRAPPED: {plan}:{lineno} -- not valid Python in place; "
                               "an AST-reading guard sees it as a string")
            names = sorted(green)
            result = _run_guards(module, copy, names, root)
            if "import_error" in result:
                unrunnable += 1
                details.append(f"UNRUNNABLE: {rel(module)} -- {result['import_error']}")
                continue
            for name in names:
                outcome = result["results"].get(name)  # M:PBG-MISSING-RESULT
                if outcome is None:
                    unrunnable += 1
                    details.append(f"UNRUNNABLE: {rel(module)}::{name} -- no result for {plan}:{lineno}")
                elif outcome.get("status") != "pass":
                    collisions += 1
                    details.append(f"COLLISION: {plan}:{lineno} {rel(module)}::{name}"
                                   f" -- {outcome.get('msg', 'no message')}")

    counts = f"checked={checked} skipped={skipped} guards={len(all_guards)}"
    not_run = f"unrunnable={unrunnable} baseline_red={baseline_red}"
    if collisions:
        token = f"PRESCRIBED-BLOCKS: FAIL collisions={collisions} {not_run} {counts}"
    elif unrunnable or baseline_red:  # M:PBG-INCOMPLETE
        token = f"PRESCRIBED-BLOCKS: INCOMPLETE {not_run} {counts}"
    else:
        token = f"PRESCRIBED-BLOCKS: PASS {counts}"
    return token, details


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["--child"]:
        return _child(argv[1], argv[2], json.loads(argv[3]), argv[4])
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("plan", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    if not args.plan.is_file() or not args.repo_root.is_dir():
        print("PRESCRIBED-BLOCKS: UNREADABLE")
        return 2
    try:
        token, details = check(args.plan, args.repo_root)
    except (OSError, UnicodeDecodeError) as error:
        print("PRESCRIBED-BLOCKS: UNREADABLE")
        print(f"REASON: {type(error).__name__}: {error}", file=sys.stderr)
        return 2
    print(token)
    for line in details:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
