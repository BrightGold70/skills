#!/usr/bin/env python3
"""Replay the three historical FR-9 pins without checking out the HemaSuite clone.

Working directory: repository root (all child working directories are printed).
Invocation: /opt/anaconda3/bin/python3 docs/03-analysis/probes/agy-coder-fallback/fr9_incident_replay.py
Optional: --hemasuite PATH selects another read-only HemaSuite clone.
Only git archive exports in automatically removed temporary directories are edited.
The probe uses stdlib orchestration and imports Task 14's old_rule/new_rule; its
interpreter must supply pytest and the historical project's installed dependencies.
Every child is bounded by this checkout's hmad-dispatch run --timeout wrapper.
Unreproduced cases print their commands/errors and count against AC-9.3. Verdicts
exit 0, including FAIL; an unusable probe setup exits 2. No full suite is run.
"""

import argparse
import ast
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
DISPATCH = ROOT / "h-mad/bin/hmad-dispatch"
PROJECT = "hematology-paper-writer"
MODULE = "tools/notebooklm_integration.py"
MUTATIONS = "tests/mutation-specs/notebooklm_integration_interface.json"
ARCHIVE_DOCS = "docs/archive/2026-10/notebooklm-integration-interface"
ANALYSIS = f"{ARCHIVE_DOCS}/notebooklm-integration-interface.analysis.md"
PLAN = f"{ARCHIVE_DOCS}/notebooklm-integration-interface.impl-plan.md"
CASES = (
    {"name": "T4 WIRE-PIN 1", "sha": "531a6296b",
     "file": "test_notebooklm_resolver.py",
     "pin": "test_resolver_calls_registry_arm_notebook_id_once",
     "caller": "resolve_registry_notebook",
     "callee": "registry_arm_notebook_id", "evidence": "M4.1"},
    {"name": "T5 WIRE-PIN 1", "sha": "7aa0d9dec",
     "file": "test_notebooklm_initialize.py",
     "pin": "test_initialize_entry_point_resolves_through_registry_arm",
     "caller": "initialize_project_notebook",
     "callee": "resolve_registry_notebook", "evidence": "M5.1"},
    {"name": "T6 WIRE-PIN 2", "sha": "c2d671f6b",
     "file": "test_notebooklm_status_report.py",
     "pin": "test_status_entry_point_resolves_through_registry_arm",
     "caller": "generate_setup_report",
     "callee": "resolve_registry_notebook", "evidence": "WIRE 2"},
)


class ReplayFailure(Exception):
    """A counted case failure, including an unavailable historical dependency."""


def run(argv, cwd, env, seconds=30):
    command = [str(DISPATCH), "run", "--timeout", str(seconds), "--", *map(str, argv)]
    print(f"COMMAND cwd={cwd} argv={shlex.join(command)}", flush=True)
    result = subprocess.run(
        command, cwd=cwd, env=env, capture_output=True, text=True,
        stdin=subprocess.DEVNULL, timeout=seconds + 10,
    )
    print(f"RETURN: {result.returncode}")
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.stderr:
        print(result.stderr, end="" if result.stderr.endswith("\n") else "\n")
    return result


def require(condition, message):
    if not condition:
        raise ReplayFailure(message)


def git(repo, args, env):
    result = run(["git", "-C", repo, *args], ROOT, env)
    require(result.returncode == 0, f"git command failed: {shlex.join(args)}")
    return result.stdout.strip()


def export(repo, revision, paths, destination, env):
    destination.mkdir(parents=True, exist_ok=True)
    # A disk-backed archive avoids holding a whole historical project in memory.
    with tempfile.TemporaryDirectory(prefix="fr9-tar-", dir=destination.parent) as scratch:
        archive = Path(scratch) / "export.tar"
        git(repo, ["archive", "--format=tar", f"--output={archive}", revision, *paths], env)
        result = run(["tar", "-xf", archive, "-C", destination], ROOT, env, 60)
        require(result.returncode == 0, "tar extraction failed")


def function(source, name):
    nodes = [n for n in ast.walk(ast.parse(source))
             if isinstance(n, ast.FunctionDef) and n.name == name]
    require(len(nodes) == 1, f"expected one definition of {name}, measured {len(nodes)}")
    return nodes[0]


def direct_form(source, pin):
    """Remove only the target pin's getattr default and exception scaffold."""
    node = function(source, pin)
    assignments = [n for n in node.body if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == "caller" for t in n.targets)]
    tries = [n for n in node.body if isinstance(n, ast.Try)]
    require(len(assignments) == len(tries) == 1, "committed scaffold shape moved")
    assignment, scaffold = assignments[0], tries[0]
    lookup = assignment.value
    require(isinstance(lookup, ast.Call) and isinstance(lookup.func, ast.Name)
            and lookup.func.id == "getattr" and len(lookup.args) == 3
            and isinstance(lookup.args[-1], ast.Constant) and lookup.args[-1].value is None,
            "expected committed three-argument getattr")
    require(len(scaffold.handlers) == 1
            and ast.unparse(scaffold.handlers[0].type) == "(Exception, SystemExit)"
            and not scaffold.orelse and not scaffold.finalbody,
            "expected committed exception-catching scaffold")
    lookup.args.pop()
    lines = source.splitlines(keepends=True)
    # Edit backwards so source offsets remain those of the committed artifact.
    body = lines[scaffold.body[0].lineno - 1:scaffold.body[-1].end_lineno]
    lines[scaffold.lineno - 1:scaffold.end_lineno] = [line[4:] for line in body]
    lines[assignment.lineno - 1:assignment.end_lineno] = [
        " " * assignment.col_offset + "caller = " + ast.unparse(lookup) + "\n"
    ]
    rewritten = "".join(lines)
    before = [ast.dump(n) for n in ast.walk(node) if isinstance(n, ast.Assert)]
    after = [ast.dump(n) for n in ast.walk(function(rewritten, pin)) if isinstance(n, ast.Assert)]
    require(before == after, "direct-form rewrite changed the pin assertions")
    return rewritten


def resolution(case, project, env, caller_present):
    owner = "integration.NotebookLMIntegration" if case["caller"] == "generate_setup_report" else "integration"
    callee_owner = "ko" if case["callee"] == "registry_arm_notebook_id" else "integration"
    script = (
        "import tools.notebooklm_integration as integration; "
        "import engine._ko_notebooks as ko; "
        f"callee = getattr({callee_owner}, {case['callee']!r}); "
        f"present = hasattr({owner}, {case['caller']!r}); "
        "print(f'CALLEE_RESOLVES={callable(callee)} CALLER_PRESENT={present}'); "
        f"assert callable(callee) and present is {caller_present!r}"
    )
    result = run([sys.executable, "-c", script], project, env)
    return result.returncode == 0


def pytest_pin(case, project, env, label):
    print(f"READING: {label}")
    target = f"tests/{case['file']}::{case['pin']}"
    result = run([
        sys.executable, "-m", "pytest", target, "-q", "--tb=short",
        "--color=no", "-p", "no:cacheprovider",
    ], project, env, 60)
    output = result.stdout + result.stderr
    exceptions = re.findall(
        r"^E\s+((?:AttributeError|ImportError|ModuleNotFoundError|NameError|AssertionError)\b[^\n]*)",
        output, re.M,
    )
    exception_line = exceptions[-1] if exceptions else ""
    # Score the selected test's call failure, never the overall rc. The known
    # sandbox leak-reaper teardown PermissionError does not alter that reading.
    failed = (bool(re.search(r"\b1 failed\b", output))
              and f"FAILED {target}" in output and bool(exception_line))
    passed = bool(re.search(r"\b1 passed\b", output)) and not re.search(r"\b\d+ failed\b", output)
    print(f"MEASURED: {label} failed={failed} passed={passed} exception={exception_line!r}")
    return {"failed": failed, "passed": passed, "exception_line": exception_line,
            "exception": exception_line.split(":", 1)[0]}


def wire_cut(case, project):
    path = project / MODULE
    source = path.read_text(encoding="utf-8")
    caller = function(source, case["caller"])
    lines = source.splitlines(keepends=True)
    segment = "".join(lines[caller.lineno - 1:caller.end_lineno])
    if case["evidence"] in {"M4.1", "M5.1"}:
        rows = json.loads((project / MUTATIONS).read_text(encoding="utf-8"))["mutations"]
        matches = [row for row in rows if row["name"] == case["evidence"] + " wire cut"]
        require(len(matches) == 1, "historical wire-cut mutation row missing")
        row = matches[0]
        require(row["file"] == MODULE and row["symbol"] == case["caller"]
                and row["test"] == f"tests/{case['file']}::{case['pin']}",
                "historical mutation points to another wire")
        find, replacement = row["find"], row["replace"]
    else:
        # The T6 commit cites a hand revert rather than a mutation registry row:
        # inline the registry value while retaining caller and resolver definitions.
        find = "            res = resolve_registry_notebook(key)"
        replacement = (
            '            res = RegistryResolution("resolved", key, '
            'RegistryManager().get_project(key).get("notebook_id"), "")'
        )
    require(segment.count(find) == 1, "wire-cut call site is not unique")
    changed = segment.replace(find, replacement, 1)
    def calls(text):
        return sum(isinstance(n, ast.Call) and (
            isinstance(n.func, ast.Name) and n.func.id == case["callee"]
            or isinstance(n.func, ast.Attribute) and n.func.attr == case["callee"]
        ) for n in ast.walk(ast.parse(text)))
    # Method text needs dedenting before parsing; the actual file keeps its indent.
    import textwrap
    before, after = calls(textwrap.dedent(segment)), calls(textwrap.dedent(changed))
    require((before, after) == (1, 0), f"wire call counts moved: {before} -> {after}")
    lines[caller.lineno - 1:caller.end_lineno] = [changed]
    mutated = "".join(lines)
    ast.parse(mutated)
    path.write_text(mutated, encoding="utf-8")
    print(f"WIRE-CUT: {MODULE}:{caller.lineno} calls={before}->{after} "
          f"find={find!r} replace={replacement!r}")


def citations(case, evidence, hema_sha, message):
    found = []
    for path in (ANALYSIS, PLAN):
        for number, line in enumerate((evidence / path).read_text(encoding="utf-8").splitlines(), 1):
            if case["evidence"] in line:
                print(f"CITATION: {hema_sha}:{path}:{number}: {line.strip()}")
                found.append(path)
    for number, line in enumerate(message.splitlines(), 1):
        if case["evidence"] in line:
            print(f"CITATION: {case['sha']} commit-message:{number}: {line.strip()}")
    return ANALYSIS in found and PLAN in found and case["evidence"] in message


def replay(case, repo, hema_sha, evidence, base, env, old_rule, new_rule):
    print(f"\nCASE: {case['name']} task={case['sha']} caller={case['caller']} callee={case['callee']}")
    # Validate object identity and reachability before exporting any case bytes.
    require(git(repo, ["cat-file", "-t", case["sha"]], env) == "commit", "not a commit")
    git(repo, ["merge-base", "--is-ancestor", case["sha"], "HEAD"], env)
    task_sha = git(repo, ["rev-parse", case["sha"]], env)
    parent_sha = git(repo, ["rev-parse", case["sha"] + "^"], env)
    print(f"REVISIONS: task={task_sha} parent={parent_sha}")
    message = git(repo, ["show", "-s", "--format=%B", task_sha], env)
    cited = citations(case, evidence, hema_sha, message)
    parent, task = base / "parent", base / "task"
    export(repo, parent_sha, [PROJECT], parent, env)
    export(repo, task_sha, [PROJECT], task, env)
    # The new pin and its real fixture helpers come from the task commit; all
    # production code and pytest configuration at the RED base stay at its parent.
    export(repo, task_sha, [f"{PROJECT}/tests/{case['file']}",
                           f"{PROJECT}/tests/_notebooklm_harness.py"], parent, env)
    red_project, green_project = parent / PROJECT, task / PROJECT
    pin = red_project / "tests" / case["file"]
    committed = pin.read_text(encoding="utf-8")
    resolved = resolution(case, red_project, env, False)
    if case["evidence"] != "M4.1":
        pin.write_text(direct_form(committed, case["pin"]), encoding="utf-8")
        print("DIRECT-FORM: removed getattr default and try/except; assertions unchanged")
    direct = pytest_pin(case, red_project, env, "direct-parent-RED")
    # Missing-symbol role is tied to the named caller in the observed exception,
    # not assigned merely because a RED occurred.
    caller_missing = (direct["exception"] in {"AttributeError", "ImportError"}
                      and repr(case["caller"]) in direct["exception_line"])
    reading = dict(direct, role="caller" if caller_missing else "other", callee_resolves=resolved)
    old, new = old_rule(reading), new_rule(reading)
    direct_ok = direct["failed"] and caller_missing and resolved and (old, new) == ("halt", "valid")
    print(f"RECORD direct: exception={direct['exception_line']!r} callee_resolves={resolved} "
          f"old={old} new={new} reproduced={direct_ok}")
    scaffold_ok = True
    if case["evidence"] != "M4.1":
        pin.write_text(committed, encoding="utf-8")
        scaffold = pytest_pin(case, red_project, env, "committed-scaffold-parent-RED")
        old_scaffold = old_rule(scaffold)
        scaffold_ok = scaffold["failed"] and scaffold["exception"] == "AssertionError" and old_scaffold == "valid"
        print(f"RECORD scaffold: exception={scaffold['exception_line']!r} "
              f"old={old_scaffold} reproduced={scaffold_ok}")
    else:
        print("RECORD scaffold: not applicable; committed T4 pin is the direct form")
    present = resolution(case, green_project, env, True)
    green = pytest_pin(case, green_project, env, "committed-task-GREEN-control")
    wire_cut(case, green_project)
    kept = resolution(case, green_project, env, True)
    cut = pytest_pin(case, green_project, env, "committed-task-wire-cut-RED")
    cut_ok = present and green["passed"] and kept and cut["failed"] and cut["exception"] == "AssertionError"
    print(f"RECORD wire-cut: green={green['passed']} caller_and_callee_kept={kept} "
          f"exception={cut['exception_line']!r} reproduced={cut_ok}")
    print(f"RECORD citation: evidence={case['evidence']} located={cited}")
    ok = bool(direct_ok and scaffold_ok and cut_ok and cited)
    print(f"CASE RESULT: {case['name']} reproduced={ok}")
    return ok


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hemasuite", type=Path, default=Path("/Users/kimhawk/orca/HemaSuite"))
    args = parser.parse_args()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
               HMAD_STUB_HOSTILE="all")
    for key in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTHONPATH"):
        env.pop(key, None)
    try:
        if not DISPATCH.is_file() or not os.access(DISPATCH, os.X_OK):
            raise OSError(f"portable time-bounder unavailable: {DISPATCH}")
        sys.dont_write_bytecode = True
        sys.path[:0] = [str(ROOT / "h-mad/tests"), str(ROOT / "h-mad/scripts")]
        from test_h_mad_wire_pin_new_caller_corpus import old_rule, new_rule
        skills_sha = git(ROOT, ["rev-parse", "HEAD"], env)
        hema_sha = git(args.hemasuite, ["rev-parse", "HEAD"], env)
        print(f"SKILLS_HEAD: {skills_sha}\nHEMASUITE_HEAD: {hema_sha}")
        print(f"INVOCATION: {shlex.join([sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]])}")
        print(f"WORKING_DIRECTORY: {Path.cwd()}")
        reproduced = 0
        with tempfile.TemporaryDirectory(prefix="fr9-incident-") as scratch:
            temporary = Path(scratch)
            env["MPLCONFIGDIR"] = str(temporary / "mpl-cache")
            evidence = temporary / "evidence"
            try:
                export(args.hemasuite, hema_sha, [ANALYSIS, PLAN], evidence, env)
                evidence_error = None
            except (ReplayFailure, OSError, subprocess.SubprocessError) as exc:
                evidence_error = exc
            for index, case in enumerate(CASES, 1):
                try:
                    require(evidence_error is None, f"evidence export failed: {evidence_error}")
                    reproduced += replay(case, args.hemasuite, hema_sha, evidence,
                                         temporary / f"case-{index}", env, old_rule, new_rule)
                except (ReplayFailure, OSError, ValueError, SyntaxError, subprocess.SubprocessError) as exc:
                    print(f"CASE RESULT: {case['name']} reproduced=False error={type(exc).__name__}: {exc}")
                    print("NON-REPRODUCED: failing command and its output are printed above; no substitute reading")
        print(f"AC-9.3: cases={len(CASES)} reproduced={reproduced} non_reproduced={len(CASES) - reproduced}")
        print(f"PROBE: {'PASS' if reproduced == len(CASES) else 'FAIL'}")
        return 0
    except (ImportError, OSError, ReplayFailure, subprocess.SubprocessError) as exc:
        print(f"OPERATIONAL ERROR: {type(exc).__name__}: {exc}")
        print("PROBE: FAIL")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
