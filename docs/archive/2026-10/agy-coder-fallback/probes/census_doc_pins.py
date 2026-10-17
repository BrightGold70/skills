#!/usr/bin/env python3
"""Census literal test pins in every named FR-9/FR-10 rewrite surface.

Run from the repository root:
  python3 docs/03-analysis/probes/agy-coder-fallback/census_doc_pins.py

Control (the altered expectation uses the normal comparison):
  python3 docs/03-analysis/probes/agy-coder-fallback/census_doc_pins.py --expected-literals 0

The census is the plan's deleted scratch-script method: parse every tracked
``h-mad/tests/*.py`` file that names a rewrite surface, collect string constants
at least 16 characters long which contain a space, and retain the constants
which occur verbatim in that surface's section.  The plan records a numeric
reading only for the whole implementer prompt (23 distinct literals in 8 test
files at ``d90decc6``); every other displayed count is deliberately marked
``expected=not recorded in plan``.  The fixed ``EXPECT`` literals are the
separately listed hand pins, including short, negative, and structural cases.

The final ``PROBE:`` line is a normal verdict and exits zero.  Exit 2 means an
input or git operation could not be read.
"""
import argparse
import ast
import subprocess
import sys
import warnings
from pathlib import Path


EXPECT_LITERALS = 23
EXPECT_FILES = 8
TEST_GLOB = "h-mad/tests/*.py"
PROMPT = "h-mad/references/codex-implementer-prompt.md"
EXPECT = {
    "skill-authorship": (
        "no write-time test-first gate", "fallback-grok", "HMAD_CODEX_UNAVAILABLE",
        "fallback_agent", "### Codex authors Phase 5 — enforced, not just instructed", "Phase 5 implementation is **Codex's job**",
        "Test files, docs, config, and shell are never gated; only production `.py`.",
        "FIRST component", "relative to the project root", "`src/docs/foo.py`", "Both gates",
    ),
    "skill-dispatch": ("### Exit-code dispatch for 5d/5e (`hmad-dispatch exec`) — default for one-shot", "exec grok", "--agent grok", "hmad-dispatch exec agy", "hmad-dispatch exec codex"),
    "skill-phase7-closure": ("7. **Closure (autonomous)**", "SKIPPED_NO_PANE", "must name a LOCAL branch", "git branch main origin/main"),
    "skill-teammate": ("It does not license Claude to write Phase 5 production code", "ACTIVE", "every", "unavailable", "exhausted", "## Teammate audit leg — when codex is unavailable", "--surfaces agy,grok", "unmeasured"),
    "skill-5d-wiring": ("The third task shape is `wiring`, and counts cannot gate it.", "failure mode per test, not only the count"),
    "agy-tdd-gate": ("h-mad-codex-tdd-gate.py", "h-mad-tdd-gate.sh", "permissionDecision", "rc 0"),
    "failure-recovery-5d": ("step5d:red_wrong_reason:<module>",),
    "assembler-wiring": ("never a missing",),
    "prompt": ("`Concerns:`", "prose", "contentless", "run --timeout", "gtimeout", "halt", "coreutils", "Hook: ", "apply_patch", "shell", "Write", "Edit", "impl-plan", "name map", "summary", "N failed", "test_*.py", "*_test.py", "conftest*.py"),
}
EXPECT_ABSENT = {
    "agy-tdd-gate": ("exit-code protocol",),
    "prompt-hook-block": ("<", ">"),
}
RESIDUAL = (
    "short literals; space-free literals; run-time-built literals; negative assertions; "
    "structural locators"
)


def markdown_section(text: str, heading: str) -> str:
    """Return an ATX section, ignoring heading-like lines inside fenced code."""
    lines = text.splitlines(keepends=True)
    start_line = next(i for i, line in enumerate(lines) if line.rstrip("\n") == heading)
    level = len(heading) - len(heading.lstrip("#"))
    fenced = False
    for i in range(start_line + 1, len(lines)):
        stripped = lines[i].lstrip()
        if stripped.startswith(("```", "~~~")):
            fenced = not fenced
            continue
        if not fenced and lines[i].startswith("#"):
            next_level = len(lines[i]) - len(lines[i].lstrip("#"))
            if next_level <= level:
                return "".join(lines[start_line:i])
    return "".join(lines[start_line:])


def phase7_closure(text: str) -> str:
    start = text.index("7. **Closure (autonomous)**")
    return text[start : text.index("\n## Phase 5", start)]


def line_with(text: str, needle: str) -> str:
    return next(line for line in text.splitlines() if needle in line)


def prompt_hook_block(text: str) -> str:
    """Return the unique Hook line and the contiguous bullets that follow it."""
    lines = text.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if line.startswith("Hook: ")]
    if len(starts) != 1:
        raise ValueError(f"expected one Hook line, found {len(starts)}")
    end = starts[0] + 1
    while end < len(lines) and lines[end].startswith("- "):
        end += 1
    return "".join(lines[starts[0]:end])


def assembler_span(path: Path) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "assemble":
            values = [
                n.value
                for n in ast.walk(node)
                if isinstance(n, ast.Constant)
                and isinstance(n.value, str)
                and "never a missing" in n.value
            ]
            if len(values) == 1:
                return values[0]
            raise ValueError(f"expected one wiring literal in assemble, found {len(values)}")
    raise ValueError("assemble function not found")


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True, check=True
    ).stdout


def string_constants(path: Path) -> set[str]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and len(node.value) >= 16
        and " " in node.value
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", default=PROMPT, help="prompt path relative to the repository root")
    parser.add_argument("--expected-literals", type=int, default=EXPECT_LITERALS)
    parser.add_argument("--expected-files", type=int, default=EXPECT_FILES)
    args = parser.parse_args()

    try:
        root = Path(git(Path.cwd(), "rev-parse", "--show-toplevel").strip())
        head = git(root, "rev-parse", "HEAD").strip()
        skill = (root / "h-mad/SKILL.md").read_text(encoding="utf-8")
        runtime = (root / "h-mad/references/agy-runtime.md").read_text(encoding="utf-8")
        recovery = (root / "h-mad/references/failure-recovery.md").read_text(encoding="utf-8")
        schema = (root / "h-mad/references/state-schema.md").read_text(encoding="utf-8")
        prompt = (root / args.prompt).read_text(encoding="utf-8")
        test_paths = [root / name for name in git(root, "ls-files", TEST_GLOB).splitlines()]
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"probe cannot run: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    builders = {
        "skill-authorship": ("h-mad/SKILL.md", lambda: markdown_section(skill, "### Codex authors Phase 5 — enforced, not just instructed")),
        "skill-dispatch": ("h-mad/SKILL.md", lambda: markdown_section(skill, "### Exit-code dispatch for 5d/5e (`hmad-dispatch exec`) — default for one-shot")),
        "skill-phase7-closure": ("h-mad/SKILL.md", lambda: phase7_closure(skill)),
        "skill-teammate": ("h-mad/SKILL.md", lambda: markdown_section(skill, "## Teammate audit leg — when codex is unavailable")),
        "skill-5d-wiring": ("h-mad/SKILL.md", lambda: line_with(skill, "The third task shape is `wiring`")),
        "agy-tdd-gate": ("h-mad/references/agy-runtime.md", lambda: markdown_section(runtime, "## The TDD gate")),
        "agy-hooks": ("h-mad/references/agy-runtime.md", lambda: markdown_section(runtime, "## Hooks")),
        "agy-construct-mapping": ("h-mad/references/agy-runtime.md", lambda: markdown_section(runtime, "## Construct mapping")),
        "failure-recovery-5d": ("h-mad/references/failure-recovery.md", lambda: line_with(recovery, "step5d:red_wrong_reason")),
        "state-schema-fields": ("h-mad/references/state-schema.md", lambda: markdown_section(schema, "## Field semantics (v2.2)")),
        "assembler-wiring": ("h-mad/scripts/h_mad_assemble_tdd.py", lambda: assembler_span(root / "h-mad/scripts/h_mad_assemble_tdd.py")),
        "prompt": (args.prompt, lambda: prompt),
        "prompt-hook-block": (args.prompt, lambda: prompt_hook_block(prompt)),
    }
    surfaces = {}
    surface_errors = {}
    for name, (surface_path, build) in builders.items():
        try:
            surfaces[name] = (surface_path, build())
        except (ValueError, StopIteration) as exc:
            surfaces[name] = (surface_path, "")
            surface_errors[name] = f"{type(exc).__name__}: {exc}"
    hits: dict[str, dict[str, set[str]]] = {name: {} for name in surfaces}
    try:
        for path in test_paths:
            source = path.read_text(encoding="utf-8")
            constants = string_constants(path)
            for name, (surface_path, section) in surfaces.items():
                if Path(surface_path).name not in source and surface_path not in source:
                    continue
                for literal in constants:
                    if literal in section:
                        hits[name].setdefault(literal, set()).add(str(path.relative_to(root)))
    except (OSError, SyntaxError, UnicodeError) as exc:
        print(f"probe cannot run: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    print(f"HEAD: {head}")
    failures = []
    for name, (surface_path, section) in surfaces.items():
        matched = hits[name]
        files = {path for owners in matched.values() for path in owners}
        expected = f"{args.expected_literals}" if name == "prompt" else "not recorded in plan"
        files_expected = f"{args.expected_files}" if name == "prompt" else "not recorded in plan"
        print(f"SURFACE: {name} path={surface_path} constants={len(matched)} expected={expected} files={len(files)} files_expected={files_expected}")
        for literal, owners in sorted(matched.items()):
            print(f"HIT[{name}]: {literal!r} :: {', '.join(sorted(owners))}")
        print("EXPECT-LITERALS[{}]: {}".format(name, ", ".join(repr(x) for x in EXPECT.get(name, ())) or "none"))
        missing = [literal for literal in EXPECT.get(name, ()) if literal not in section]
        absent = [literal for literal in EXPECT_ABSENT.get(name, ()) if literal in section]
        if name in EXPECT_ABSENT:
            print("EXPECT-ABSENT[{}]: {}".format(name, ", ".join(repr(x) for x in EXPECT_ABSENT[name])))
        if name in surface_errors:
            print(f"BOUNDARY[{name}]: {surface_errors[name]}")
            failures.append(f"boundary:{name}")
        print(f"EXPECT[{name}]: " + ("OK" if not missing else "MISSING " + ", ".join(repr(x) for x in missing)))
        if missing:
            failures.append(f"pins:{name}")
        if absent:
            print(f"EXPECT-ABSENT[{name}]: PRESENT " + ", ".join(repr(x) for x in absent))
            failures.append(f"negative_pins:{name}")
        if name == "prompt":
            if len(matched) != args.expected_literals:
                failures.append("distinct_literals")
            if len(files) != args.expected_files:
                failures.append("test_files")
            print(f"prompt distinct literals: actual={len(matched)} expected={args.expected_literals}")
            print(f"prompt test files: actual={len(files)} expected={args.expected_files}")
    print("hand-found pins: listed in EXPECT; they are not derived by the >=16-character matcher")
    print(f"residual: {RESIDUAL}")
    if failures:
        print(f"moved figures: {', '.join(failures)}")
        print("PROBE: FAIL")
    else:
        print("PROBE: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
