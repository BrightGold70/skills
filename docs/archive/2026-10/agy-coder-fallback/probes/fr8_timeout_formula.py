#!/usr/bin/env python3
"""FR-8 step 4: recompute agy's default dispatch timeout from the tracer's readings.

Working directory: repository root.
Invocation: python3 docs/03-analysis/probes/agy-coder-fallback/fr8_timeout_formula.py
Control:    python3 docs/03-analysis/probes/agy-coder-fallback/fr8_timeout_formula.py --control
The control adds 300 s to the slower reading (117 -> 417 -> 3 x 417 = 1251 -> 1260), so the
recomputed figure must move off the assembler's default and the probe must FAIL.

Readings: the RED and GREEN `hmad-dispatch exec agy` wall times recorded by Task 21 in
docs/03-analysis/agy-coder-fallback.authoring/fr8_tracer/s3_{red,green}.wall
(lines `rc=0 RED_WALL=<s>` / `rc=0 GREEN_WALL=<s>`). Formula (spec FR-8 step 4):
max(900, 3 x slower), rounded up to a multiple of 60. The figure is compared with
TIMEOUT_DEFAULTS["agy"] read from h-mad/scripts/h_mad_assemble_tdd.py by `ast`, not import.
PASS and FAIL exit 0; unreadable input exits 2.
"""
import argparse
import ast
import math
import re
import subprocess
import sys
from pathlib import Path

READINGS = Path("docs/03-analysis/agy-coder-fallback.authoring/fr8_tracer")
ASSEMBLER = Path("h-mad/scripts/h_mad_assemble_tdd.py")


def wall(path, label):
    match = re.search(rf"\b{label}_WALL=(\d+)\b", path.read_text(encoding="utf-8"))
    if not match:
        raise ValueError(f"{path}: no {label}_WALL reading")
    return int(match.group(1))


def assembler_default():
    tree = ast.parse(ASSEMBLER.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "TIMEOUT_DEFAULTS" for t in node.targets):
            return ast.literal_eval(node.value)["agy"]
    raise ValueError("TIMEOUT_DEFAULTS not assigned in the assembler")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--control", action="store_true")
    args = parser.parse_args()
    try:
        print("HEAD: " + subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip())
        red = wall(READINGS / "s3_red.wall", "RED")
        green = wall(READINGS / "s3_green.wall", "GREEN")
        default = assembler_default()
    except (OSError, ValueError, KeyError, SyntaxError, subprocess.CalledProcessError) as exc:
        print(f"probe cannot run: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    slower = max(red, green)
    if args.control:
        slower += 300
        print("CONTROL: slower reading inflated by 300 s")
    figure = math.ceil(max(900, 3 * slower) / 60) * 60
    print(f"readings: RED={red}s GREEN={green}s slower={slower}s")
    print(f"formula: max(900, 3 x {slower}) rounded up to 60 = {figure}")
    print(f"assembler TIMEOUT_DEFAULTS['agy'] = {default}")
    print("PROBE: " + ("PASS" if default == figure else "FAIL"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
