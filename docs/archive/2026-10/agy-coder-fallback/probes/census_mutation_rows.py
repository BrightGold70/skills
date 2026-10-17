#!/usr/bin/env python3
"""M-2, M-3, FR-3 regions and M-4, measured from tracked mutation specs.

Working directory: h-mad/ (relative to the repository root).
Invocation: python3 ../docs/03-analysis/probes/agy-coder-fallback/census_mutation_rows.py
Control: python3 ../docs/03-analysis/probes/agy-coder-fallback/census_mutation_rows.py --control
The control overrides the first M-2 expected row count with 57; it exercises the
same comparison as the unmodified input. --root PATH selects another h-mad tree.
Readings in EXPECT are the plan's 4e4b5ded readings, never re-baselined to HEAD.
Find starts use the first occurrence, as M-4 prescribes. Python definition and
assignment spans come from ast; shell spans use the named top-level boundaries.
Absent boundaries/names are drift, not permission to widen a measurement region.
PASS and FAIL exit 0; unreadable/unparseable input or failed git discovery exits 2.
"""
import argparse
import ast
import collections
import json
import re
import subprocess
import sys
from pathlib import Path

HOOK = "hooks/h-mad-tdd-gate.sh"
JUDGE = "scripts/h_mad_tdd_judge.py"
CODEX = "hooks/h-mad-codex-tdd-gate.py"
EXPECT = {
    "M-2": {
        HOOK: (56, 5), JUDGE: (36, 8), CODEX: (62, 5),
        "scripts/h_mad_assemble_tdd.py": (60, 6),
        "scripts/h_mad_phase7_preconditions.py": (12, 2),
        "scripts/h_mad_hook_wiring.py": (10, 1),
        "scripts/h_mad_state_write.py": (21, 4),
        "scripts/h_mad_target_identity.py": (15, 2),
    },
    "M-3/rows": 8,
    "M-3/specs": 3,
    "M-3/by-spec": {"claude_gate_judge_wiring.json": 5, "tdd_judge_chain.json": 2,
                    "tdd_gate_fallback_agent.json": 1},
    "FR-3/rows": 13,
    "FR-3/hook-rows": 8,
    "FR-3/judge-rows": 5,
    "FR-3/_read_state": ["H17", "W5BR", "W5BF", "W5BF2", "W5BF3",
                          "wr12-2-gate-never-reads-the-fold", "g9-fallback-position-unchecked"],
    "FR-3/authorship": ["H3"],
    "FR-3/_active_records": ["g3-reads-another-feature"],
    "FR-3/format_state_line": ["C3G", "wr12-1-state-line-never-folds", "C3", "C5"],
    "M-4/total-rows": 62,
    "M-4/moved-names": 25,
    "M-4/moved-rows": 31,
    "M-4/specs": 4,
    "M-4/by-spec": {"codex_gate_judge_wiring.json": 21, "codex_gate_shell_allowance.json": 6,
                    "assemble_tdd_mutation_rows.json": 2, "tdd_gate_differential.json": 2},
    "M-4/absent-anchors": 0,
    "M-4/non-unique-anchors": 0,
}
PATTERN = re.compile(
    r"TDD-STATE:|STATE_ACTIVE_RE|codex-escape|ESCAPE_STATUSES|command -v codex|HMAD_CODEX_UNAVAILABLE"
)
CLOSURE = {
    "_contained_venv_executable", "_cwd_escapes_root", "_load_judge", "_option_value",
    "_path_within", "_payload_cwd_base", "_safe_argv", "_safe_hmad_script",
    "_safe_shell_command", "_trusted_executable",
}
EXTRA_FUNCTIONS = {
    "_shell_allowance", "_operator_allowed", "_is_shell_allowance", "_read_regular_text",
    "_state_status", "_any_phase5_status", "_is_production_python",
}
CONSTANTS = {
    "SIMPLE_SHELL_COMMAND", "READ_ONLY_COMMANDS", "SAFE_DISPATCH_VERBS",
    "SAFE_HMAD_SCRIPT_OPTIONS", "TEMP_OUTPUT_OPTIONS", "SHELL_ALLOW_FILE",
    "TRUSTED_BIN_DIRS", "MALFORMED_WORKDIR",
}


def definitions(text):
    """Only module-level bindings belong to the plan's moved set."""
    functions, assignments = {}, {}
    for node in ast.parse(text).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions[node.name] = node
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    assignments[target.id] = node
    return functions, assignments


def span(node):
    return (node.lineno, node.end_lineno) if node is not None else None


def shell_spans(text):
    lines = text.splitlines()
    spans = {}
    starts = [i for i, line in enumerate(lines) if line == "_read_state() {"]
    if len(starts) == 1:
        start = starts[0]
        end = next((i for i in range(start + 1, len(lines)) if lines[i] == "}"), None)
        if end is not None:
            spans["_read_state"] = (start + 2, end)  # body, excluding braces
    starts = [i for i, line in enumerate(lines)
              if line == '_read_state --target "$TARGET_PATH"  # M:H3']
    if len(starts) == 1:
        start = starts[0]
        end = next((i for i in range(start + 1, len(lines)) if lines[i] == "fi"), None)
        if end is not None and any("_refuse codex-authorship " in line for line in lines[start:end]):
            spans["authorship"] = (start + 1, end + 1)
    return spans


def find_line(text, find):
    at = text.find(find)
    return text.count("\n", 0, at) + 1 if at >= 0 else None


def inside(line, bounds):
    return line is not None and bounds is not None and bounds[0] <= line <= bounds[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--control", action="store_true")
    args = parser.parse_args()
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=args.root, text=True).strip()
        print(f"HEAD: {head}")
        paths = subprocess.check_output(
            ["git", "ls-files", "-z", "tests/mutation-specs/*.json"], cwd=args.root
        ).decode().split("\0")
        rows = []
        for path in filter(None, paths):
            data = json.loads((args.root / path).read_text(encoding="utf-8"))
            rows.extend((Path(path).name, row) for row in data.get("mutations", []))
        sources = {path: (args.root / path).read_text(encoding="utf-8") for path in (HOOK, JUDGE, CODEX)}
        judge_functions, _ = definitions(sources[JUDGE])
        functions, assignments = definitions(sources[CODEX])
    except (OSError, ValueError, SyntaxError, UnicodeError, subprocess.CalledProcessError) as exc:
        print(f"probe cannot run: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    ok = True

    def compare(label, actual, expected):
        nonlocal ok
        same = actual == expected
        ok &= same
        print(f"{label}: computed={actual!r} expected={expected!r} {'OK' if same else 'MOVED'}")

    for file, (want_rows, want_specs) in EXPECT["M-2"].items():
        matching = [(spec, row) for spec, row in rows if row.get("file") == file]
        if args.control and file == HOOK:
            want_rows += 1
            print("CONTROL: expected M-2 hook rows overridden to 57")
        compare(f"M-2/{file}/rows", len(matching), want_rows)
        compare(f"M-2/{file}/specs", len({spec for spec, _ in matching}), want_specs)
        print("  specs: " + ", ".join(sorted({spec for spec, _ in matching})))

    contract = [(spec, row) for spec, row in rows if row.get("file") in (HOOK, JUDGE)
                and PATTERN.search(row["find"] + "\n" + row["replace"])]
    compare("M-3/rows", len(contract), EXPECT["M-3/rows"])
    compare("M-3/specs", len({spec for spec, _ in contract}), EXPECT["M-3/specs"])
    compare("M-3/by-spec", dict(sorted(collections.Counter(spec for spec, _ in contract).items())),
            dict(sorted(EXPECT["M-3/by-spec"].items())))
    for spec, row in contract:
        print(f"  M-3: {spec}:{row['name']}")

    hook_spans = shell_spans(sources[HOOK])
    regions = {name: (HOOK, hook_spans.get(name)) for name in ("_read_state", "authorship")}
    regions.update({name: (JUDGE, span(judge_functions.get(name)))
                    for name in ("_active_records", "format_state_line")})
    region_counts = collections.Counter()
    for name, (file, bounds) in regions.items():
        compare(f"FR-3/{name}/boundary-present", bounds is not None, True)
        print(f"  span: {file}:{bounds}")
        matches = [(spec, row) for spec, row in rows if row.get("file") == file
                   and inside(find_line(sources[file], row["find"]), bounds)]
        region_counts[file] += len(matches)
        compare(f"FR-3/{name}/rows", len(matches), len(EXPECT[f"FR-3/{name}"]))
        compare(f"FR-3/{name}/names", sorted(row["name"] for _, row in matches),
                sorted(EXPECT[f"FR-3/{name}"]))
        for spec, row in matches:
            print(f"  FR-3: {spec}:{row['name']}")
    compare("FR-3/rows", sum(region_counts.values()), EXPECT["FR-3/rows"])
    compare("FR-3/hook-rows", region_counts[HOOK], EXPECT["FR-3/hook-rows"])
    compare("FR-3/judge-rows", region_counts[JUDGE], EXPECT["FR-3/judge-rows"])

    closure, pending = set(), ["_safe_shell_command"]
    while pending:
        name = pending.pop()
        if name in closure or name not in functions:
            continue
        closure.add(name)
        pending.extend(node.func.id for node in ast.walk(functions[name])
                       if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                       and node.func.id in functions)
    compare("M-4/closure-names", sorted(closure), sorted(CLOSURE))
    moved = closure | EXTRA_FUNCTIONS | CONSTANTS
    nodes = {**functions, **assignments}
    compare("M-4/moved-names", len(moved), EXPECT["M-4/moved-names"])
    compare("M-4/missing-definitions", sorted(moved - nodes.keys()), [])
    moved_spans = {name: span(nodes.get(name)) for name in moved}
    codex_rows = [(spec, row) for spec, row in rows if row.get("file") == CODEX]
    qualified, absent, non_unique = [], [], []
    for spec, row in codex_rows:
        find = row["find"]
        count = sources[CODEX].count(find)
        if count == 0:
            absent.append(f"{spec}:{row['name']}")
        if count > 1:
            non_unique.append(f"{spec}:{row['name']}")
        line = find_line(sources[CODEX], find)
        owners = sorted(name for name, bounds in moved_spans.items() if inside(line, bounds))
        if owners:
            qualified.append((spec, row))
            print(f"  M-4: {spec}:{row['name']} line={line} symbol={','.join(owners)}")
    figures = {
        "M-4/total-rows": len(codex_rows), "M-4/moved-rows": len(qualified),
        "M-4/specs": len({spec for spec, _ in qualified}),
        "M-4/by-spec": dict(sorted(collections.Counter(spec for spec, _ in qualified).items())),
        "M-4/absent-anchors": len(absent), "M-4/non-unique-anchors": len(non_unique),
    }
    for label, actual in figures.items():
        compare(label, actual, EXPECT[label])
    for label, anchors in (("absent", absent), ("non-unique", non_unique)):
        for anchor in anchors:
            print(f"  {label}: {anchor}")
    print("PROBE: " + ("PASS" if ok else "FAIL"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
