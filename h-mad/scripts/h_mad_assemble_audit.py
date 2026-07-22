#!/usr/bin/env python3
"""Assemble an h-mad audit prompt: SKILL.md steps 1, 1.5, 2-6.6 and the 7.2 preflight.

Assembly used to be prose an orchestrator executed by hand every cycle, and every
defect in this area came from that: the rubrics were inlined twice into a mangled
header blockquote, `{Design only - cross-doc:}` reached the reviewer in 69 of 69
dispatched prompts, and a hand-written duplication grep hardcoded a heading that is
project-authored. None of those raised an error; all reached the reviewer.

This script performs the whole sequence deterministically and refuses to emit a
prompt that would fail the preflight.

Signal discipline (base invariant "Audit-gate signal discipline"): the verdict goes
to stdout as `ASSEMBLE: PASS` or `ASSEMBLE: HALT`, and BOTH exit 0 -- a HALT is a
normal verdict, not a process failure. A non-zero exit means an operational error
(missing or unreadable input), never "the prompt was rejected".

Usage:
  h_mad_assemble_audit.py --feature <name> --phase plan|design|impl-plan \\
      --project-root <path> [--docs-dir <path>] [--out <path>] \\
      [--sentinel <stem>] [--report-file <path>] [--template <path>]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent

NOTE_START = "<!-- ORCHESTRATOR-NOTE:START"
NOTE_END = "ORCHESTRATOR-NOTE:END -->"
MARKER = re.compile(r"\{\{ONLY:([a-z,\-]+)\}\} ?")
END_ONLY = "{{END-ONLY}}"
PHASES = ("plan", "design", "impl-plan")


# --- steps 1 and 1.5 ---------------------------------------------------------

def strip_orchestrator_note(template: str) -> str:
    """Step 1: drop the leading orchestrator note; it is assembly guidance."""
    if NOTE_START not in template:
        return template
    head, _, rest = template.partition(NOTE_START)
    _, _, tail = rest.partition(NOTE_END)
    return head + tail.lstrip("\n")


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def resolve(text: str, audit_type: str) -> str:
    """Step 1.5: resolve `{{ONLY:…}}` applicability markers.

    Applies -> drop the marker, keep the content. Does not apply -> drop the
    marker AND the content it governs. Inline form governs the rest of its line
    plus deeper-indented continuation lines; block form (marker alone on a line)
    governs down to the matching `{{END-ONLY}}`.
    """
    lines = text.splitlines()
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        m = MARKER.search(line)
        if not m:
            out.append(line)
            i += 1
            continue

        applies = audit_type in m.group(1).split(",")
        stripped = MARKER.sub("", line, count=1)

        if not stripped.strip():  # block form
            j = i + 1
            while j < len(lines) and lines[j].strip() != END_ONLY:
                j += 1
            if j == len(lines):
                raise ValueError(f"unterminated {{{{ONLY:…}}}} block on line {i + 1}")
            if applies:
                out.extend(lines[i + 1 : j])
            i = j + 1
        else:  # inline form
            base = _indent(line)
            j = i + 1
            while j < len(lines) and lines[j].strip() and _indent(lines[j]) > base:
                j += 1
            if applies:
                out.append(stripped)
                out.extend(lines[i + 1 : j])
            i = j
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


# --- step 7.2 ----------------------------------------------------------------

def preflight(text: str, inlined: dict[str, str]) -> list[str]:
    """Return the reasons this prompt must not be dispatched (empty == clean)."""
    problems = []
    if residual := [ln for ln in text.splitlines() if "<INLINE_" in ln]:
        problems.append(f"unfilled_slot: {residual[0].strip()[:80]!r}"
                        + (f" (+{len(residual) - 1} more)" if len(residual) > 1 else ""))
    if leaked := [ln for ln in text.splitlines() if "{{" in ln]:
        problems.append(f"unresolved_conditional: {leaked[0].strip()[:80]!r}"
                        + (f" (+{len(leaked) - 1} more)" if len(leaked) > 1 else ""))
    for token in ("<AUDIT_SENTINEL>", "<REPORT_FILE_PATH>"):
        if token in text:
            problems.append(f"unfilled_slot: {token}")
    # Duplication. Derive each needle from the inlined file's own first line: the
    # project invariants heading is project-authored (HemaSuite's is
    # "# HPW Project Axis B Invariants"), so a hardcoded needle reports a false 0
    # in every repo but the one it was written against -- and 0 reads as "the
    # project layer was never inlined", the opposite of what happened.
    for label, body in inlined.items():
        if not body.strip():
            continue
        needle = body.splitlines()[0]
        if (n := text.count(needle)) != 1:
            problems.append(f"{label} rubric ({needle[:50]!r}) appears {n}x, want 1")
    return problems


# --- assembly ----------------------------------------------------------------

def _read(path: Path, *, required: bool) -> str:
    if not path.is_file():
        if required:
            raise FileNotFoundError(path)
        return ""
    return path.read_text(encoding="utf-8")


def assemble(*, feature: str, phase: str, project_root: Path, docs_dir: Path,
             sentinel: str, report_file: str, template: Path,
             design_dir: Path | None = None) -> tuple[str, list[str]]:
    text = resolve(strip_orchestrator_note(_read(template, required=True)), phase)

    # Design documents do NOT live beside the others: Phase 4 writes
    # `docs/02-design/features/<feature>.design.md` (the bkit PDCA layout the
    # doc-template invariant requires), while spec/plan/impl-plan sit under
    # `docs/01-plan/features/`. Assuming one directory for everything makes every
    # design and impl-plan audit unassemblable.
    design_dir = design_dir or (project_root / "docs/02-design/features")

    def doc(kind: str) -> Path:
        base = design_dir if kind == "design" else docs_dir
        return base / f"{feature}.{kind}.md"

    base_md = _read(SKILL_DIR / "invariants.base.md", required=True)
    project_md = _read(project_root / ".h-mad" / "invariants.md", required=False)

    slots = {
        "<INLINE_TARGET_DOC>": _read(doc(phase), required=True),
        "<INLINE_BASE_INVARIANTS>": base_md,
        "<INLINE_PROJECT_INVARIANTS>": project_md,
        "<AUDIT_SENTINEL>": sentinel,
        "<REPORT_FILE_PATH>": report_file,
    }
    if phase in ("plan", "design"):
        slots["<INLINE_PAIRED_SPEC>"] = _read(doc("spec"), required=True)
    if phase == "design":
        slots["<INLINE_PAIRED_PLAN>"] = _read(doc("plan"), required=True)
    if phase == "impl-plan":
        slots["<INLINE_PAIRED_DESIGN>"] = _read(doc("design"), required=True)

    for slot, value in slots.items():
        text = text.replace(slot, value)

    return text, preflight(text, {"base": base_md, "project": project_md})


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--feature", required=True)
    ap.add_argument("--phase", required=True, choices=PHASES)
    ap.add_argument("--project-root", required=True, type=Path)
    ap.add_argument("--docs-dir", type=Path,
                    help="spec/plan/impl-plan; default: <project-root>/docs/01-plan/features")
    ap.add_argument("--design-dir", type=Path,
                    help="design docs; default: <project-root>/docs/02-design/features")
    ap.add_argument("--out", type=Path, help="default: /tmp/audit_<feature>_<phase>_cycle<N>.txt")
    ap.add_argument("--cycle", default="1")
    ap.add_argument("--sentinel", help="default: AUDIT-<feature>-<phase>-v<cycle>")
    ap.add_argument("--report-file", default="",
                    help="Orca report-file transport path; empty for the sentinel scrape")
    ap.add_argument("--template", type=Path, default=SKILL_DIR / "audit-prompt.template.md")
    args = ap.parse_args(argv)

    docs_dir = args.docs_dir or (args.project_root / "docs/01-plan/features")
    sentinel = args.sentinel or f"AUDIT-{args.feature}-{args.phase}-v{args.cycle}"
    out = args.out or Path(f"/tmp/audit_{args.feature}_{args.phase}_cycle{args.cycle}.txt")

    try:
        text, problems = assemble(
            feature=args.feature, phase=args.phase, project_root=args.project_root,
            docs_dir=docs_dir, design_dir=args.design_dir, sentinel=sentinel,
            report_file=args.report_file, template=args.template,
        )
    except (FileNotFoundError, ValueError) as exc:
        # Operational error, not a verdict: the inputs are unusable.
        print(f"hmad-assemble: cannot assemble — {exc}", file=sys.stderr)
        return 1

    if problems:
        # A verdict, so exit 0 with an explicit stdout token. The prompt is NOT
        # written: an unwritten prompt cannot be dispatched by mistake.
        print(f"ASSEMBLE: HALT {args.phase}:preflight")
        for p in problems:
            print(f"  - {p}")
        return 0

    out.write_text(text, encoding="utf-8")
    size = len(text.encode())
    print(f"ASSEMBLE: PASS {out} {size}B ({size / 1024:.1f} KB) sentinel={sentinel}")
    # Measured: one reviewer emits normally at 49 KB and returns nothing at 53.
    # Warn *approaching* it, not only past it -- a real design audit assembled to
    # 48.4 KB, which passed silently with 0.6 KB of headroom, and the next feature
    # to add a few ACs crosses the cliff with no warning ever having fired.
    if size > 49 * 1024:
        print(f"  ! {size / 1024:.1f} KB is past the measured 49 KB reviewer cliff — "
              "split the audit by FR group (SKILL.md step 5.5); a silent empty "
              "reply is the expected failure")
    elif size > 44 * 1024:
        print(f"  ~ {size / 1024:.1f} KB is approaching the measured 49 KB reviewer "
              "cliff — inlining only the spec's '## Functional Requirements' "
              "section saves ~7 KB and loses no AC (SKILL.md step 5.5)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
