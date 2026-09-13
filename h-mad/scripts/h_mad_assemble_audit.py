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


# An inline code span: a run of backticks, content carrying neither a backtick nor a
# newline, then the SAME run. `{{` inside one is content, exactly as it is inside a fence --
# design v1.94 and impl-plan v1.38 both quote the old bounder as `rf"^#{{1,{level}}} "` in
# running prose, and a bare `"{{" in ln` refused to emit both prompts (2026-09-04).
# Residual, stated exactly: a span that uses a multi-backtick run *in order to contain* a
# backtick is not matched, so a `{{` inside one still halts. That fails closed -- it refuses a
# clean prompt rather than passing a leaked one -- and no document here has that shape.
_INLINE_CODE = re.compile(r"(`+)[^`\n]*?\1")


def _braces_outside_fences(text: str) -> list[str]:
    """Lines carrying `{{` that are NOT inside a fenced code block.

    A `{{ONLY:…}}` / `{{END-ONLY}}` directive is prose-level; an inlined document may
    legitimately quote source such as `rf"^#{{1,{level}}} "` inside a ``` fence (an
    impl-plan's literal mutation payload did, 2026-09-03), and that is content, not a
    surviving conditional. Fence tracking follows CommonMark: an opener is 0-3 spaces
    plus a run of 3+ backticks or tildes; the closer is a run of the same marker at
    least as long, alone on its line.
    """
    import re as _re
    leaked: list[str] = []
    fence_char = ""
    fence_len = 0
    for ln in text.splitlines():
        m = _re.match(r"^ {0,3}(`{3,}|~{3,})", ln)
        if fence_char:
            if m and m.group(1)[0] == fence_char and len(m.group(1)) >= fence_len \
                    and ln.strip() == m.group(1).strip():
                fence_char, fence_len = "", 0
            continue
        if m and (m.group(1)[0] == "~" or "`" not in ln[m.end():]):
            fence_char, fence_len = m.group(1)[0], len(m.group(1))
            continue
        if "{{" in _INLINE_CODE.sub("", ln):
            leaked.append(ln)
    return leaked


def preflight(text: str, inlined: dict[str, str]) -> list[str]:
    """Return the reasons this prompt must not be dispatched (empty == clean)."""
    problems = []
    if residual := [ln for ln in text.splitlines() if "<INLINE_" in ln]:
        problems.append(f"unfilled_slot: {residual[0].strip()[:80]!r}"
                        + (f" (+{len(residual) - 1} more)" if len(residual) > 1 else ""))
    if leaked := _braces_outside_fences(text):
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


# --- step 6.7: output contract at the head -----------------------------------

# The output-framing block is the LAST section of the template, and at audit-prompt
# sizes a reviewer drops it: on `grounding-evidence-coverage` impl-plan cycle 21 BOTH
# passes ignored the entire block — no sentinels, no `## Summary`/`## Must-fix`/
# `## Should-fix`/`## Nit` schema, no report file, no `.done` — and each invented its
# own verdict line, so `h_mad_audit_gate.py` scored `GATE: INVALID` on two passes that
# had done real work (one of them holding a genuine must-fix).
#
# This is PLACEMENT, not size. With the contract at the tail it was lost 2 of 2 at
# 206.4 KB; duplicated at the head it was honoured 4 of 4 at LARGER sizes (219.8,
# 224.5, 229.4 KB). Larger prompts succeeding is what rules size out — and J30's size
# premise was separately refuted 8/8.
#
# The head copy is SLICED from the assembled text, never hand-written: a hand-written
# copy would hardcode a report path and schema that drift from the template's.
CONTRACT_ANCHOR = "Output framing (mandatory"

CONTRACT_BANNER = (
    "!!! READ THIS BLOCK FIRST AND OBEY IT LAST !!!\n"
    "This is the OUTPUT CONTRACT. It is repeated verbatim at the end of this prompt.\n"
    "Your reply is machine-scored: a report that omits the sentinels or the exact\n"
    "`## Summary` / `## Must-fix` / `## Should-fix` / `## Nit` headings is scored\n"
    "INVALID and discarded no matter what it says. Do NOT invent your own verdict\n"
    "line. Re-read this block before you write a single word of your report.\n\n"
)

CONTRACT_SEPARATOR = (
    "\n\n====== END OUTPUT CONTRACT — the audit prompt begins below ======\n\n"
)


def prepend_output_contract(text: str, *, sentinel: str,
                            report_file: str) -> tuple[str, list[str]]:
    """Duplicate the tail output-contract block at the head of the prompt.

    Returns `(text, problems)` in preflight's shape. A non-empty `problems` is a
    HALT verdict, not a crash: a template that cannot carry a head contract is a
    prompt that must not be dispatched, and signal discipline reserves a non-zero
    exit for unusable inputs. `text` comes back unchanged in that case, so the
    caller's preflight still reports everything else wrong with it.

    The checks are deliberately NOT `assert`: asserts vanish under `python -O`,
    which would silently ship a prompt with no head contract and reintroduce the
    exact defect this function exists to close.
    """
    i = text.find(CONTRACT_ANCHOR)
    if i == -1:
        return text, [
            f"output_contract: anchor {CONTRACT_ANCHOR!r} not found — this template "
            "cannot carry a head contract, and the tail copy alone is dropped at "
            "audit sizes"
        ]
    contract = text[i:]
    # The slice must carry the per-pass values, or the head copy would instruct the
    # reviewer with a sentinel/path that is not this pass's.
    problems = [
        f"output_contract: {label} {value!r} missing from the contract slice"
        for label, value in (("sentinel", sentinel), ("report path", report_file))
        if value and value not in contract
    ]
    if problems:
        return text, problems
    return CONTRACT_BANNER + contract + CONTRACT_SEPARATOR + text, []


# --- assembly ----------------------------------------------------------------

def _read(path: Path, *, required: bool) -> str:
    if not path.is_file():
        if required:
            raise FileNotFoundError(path)
        return ""
    return path.read_text(encoding="utf-8")


# Every known delivery surface refuses a prompt past this many characters:
# codex `exec` answers `input_too_large max_chars=1048576` (measured 2026-09-05
# on two real gating prompts, re-measured the same day with a 1,111,089-char
# probe: rc=1, empty last message, one `Error: turn/start … "input_error_code":
# "input_too_large"` transcript line), and agy's `--print` arg is bounded at the
# same figure. The assembler used to print PASS past it and say exec had no limit.
MAX_PROMPT_CHARS = 1_048_576

# The Agent-tool (in-process Opus/Sonnet) leg has a LOWER ceiling than either
# CLI: a 740 KB assembled prompt killed one with "Prompt is too long" (measured
# 2026-09-05 on gateway-consolidation, #100 defect B). The CLIs take it fine, so
# this is a warning tier, not a refusal — but it names the axis the old
# `size_status=unverified` (a PANE figure) did not, and prints the prompt's
# layout so a windowed leg can be briefed by line range instead of by feel.
AGENT_TOOL_WARN_BYTES = 700 * 1024
_CONTRACT_HEAD = "!!! READ THIS BLOCK FIRST AND OBEY IT LAST !!!"


def layout(text: str) -> list[tuple[str, int, int]]:
    """`(label, first_line, last_line)` for each top-level region of an assembled prompt.

    Regions are the two contract blocks (head and repeated tail) and every H1
    (`# `) heading in between — which is how the inlined documents, the
    invariants and the rubrics announce themselves. Derived from the text, not
    from the assembler's parts, so it stays true for a prompt a caller edited.
    """
    lines = text.splitlines()
    starts: list[tuple[str, int]] = []
    seen_contract = False
    for i, line in enumerate(lines, 1):
        if line.startswith(_CONTRACT_HEAD):
            starts.append(("contract (repeated)" if seen_contract else "contract", i))
            seen_contract = True
        elif line.startswith("# "):
            starts.append((line[2:].strip()[:60], i))
    out: list[tuple[str, int, int]] = []
    for idx, (label, first) in enumerate(starts):
        last = starts[idx + 1][1] - 1 if idx + 1 < len(starts) else len(lines)
        out.append((label, first, last))
    return out


def size_notes(size: int, text: str) -> list[str]:
    """Advisory lines to print after `ASSEMBLE: PASS`, largest concern first."""
    notes: list[str] = []
    if size > AGENT_TOOL_WARN_BYTES:
        notes.append(
            f"  ! {size / 1024:.1f} KB exceeds ~{AGENT_TOOL_WARN_BYTES // 1024} KB, the size at "
            "which an Agent-tool (in-process Opus) leg was killed with \"Prompt is too long\" "
            "(measured 2026-09-05 at 740 KB). Dispatch such a leg via `hmad-dispatch exec` "
            "(codex/agy read files themselves), or brief a windowed leg with the contract "
            "and rubric ranges below and the documents by path:"
        )
        regions = layout(text)
        if not regions:
            notes.append("    (no contract block or H1 heading found — nothing to window on)")
        for label, first, last in regions:
            notes.append(f"    lines {first}–{last}: {label}")
    return notes

# What `hmad-dispatch exec` appends to the assembled text before the agent sees
# it: a newline, the `===HMAD-DISPATCH-BOUNDARY===` marker, a newline (30 chars;
# `_dispatch_boundary` in scripts/hmad-dispatch.sh). codex counts THOSE chars
# too — the probe above was a 1,111,059-char file reported as `actual_chars`
# 1,111,089. So a text that passes `len(text) <= MAX_PROMPT_CHARS` by fewer than
# the overhead is still refused. Reserve headroom here rather than in the
# caller's head; 64 leaves slack for a longer HMAD_DISPATCH_BOUNDARY override.
DISPATCH_OVERHEAD_CHARS = 64


def prompt_oversize(chars: int) -> bool:
    """True when a prompt of `chars` characters cannot be delivered by any surface
    once the dispatch wrapper's boundary overhead is added."""
    return chars + DISPATCH_OVERHEAD_CHARS > MAX_PROMPT_CHARS


def _vh_noop(ref: str, why: str) -> None:
    """Say when a requested Version History trim removed nothing.

    To stderr, so it cannot be mistaken for part of the assembled prompt or
    corrupt the `ASSEMBLE:`/`ARCHREVIEW:` token on stdout. A trim that silently
    no-ops is indistinguishable from one that worked and freed nothing, which is
    how an operator following the oversize halt's own advice loops.
    """
    print(f"[h-mad] vh-tail: nothing trimmed from {ref}: {why}", file=sys.stderr)


#: The ONE anchor for "where the Version History section begins".
#: `_trim_version_history` omits everything from here on from the audit prompt;
#: `h_mad_precheck_doc.py` demotes EVERY hard finding from here on, because this
#: section holds prose ABOUT changes and the detectors read it as the changes
#: themselves -- measured, #29: one document failed entirely on its own changelog
#: saying "TBD placeholders removed". (Not because the reviewer never sees the
#: text: `--vh-tail` defaults to `None`, a strict no-op, so by default it is
#: inlined.) Two copies of this literal
#: would let the two disagree about what the audit's subject is, silently, which
#: is the defect rather than a risk of it.
VH_MARKER = "\n## Version History"


def version_history_start(text: str) -> int | None:
    """1-based line number of the `## Version History` heading, or `None`.

    Deliberately IDENTICAL to `_trim_version_history`'s own lookup: first
    occurrence, section runs to end of text, no fence awareness. Agreement
    between the assembler and the precheck is the property being bought here, so
    a shared limitation is one bug in one place rather than two that drift apart
    -- the same reasoning `h_mad_archreview_cycle._trim_vh` records for reaching
    into this module rather than copying its twenty lines.

    A document whose very FIRST line is the heading returns `None`, because the
    marker carries a leading newline. That is the assembler's behaviour too, and
    a phase document that opens with its own Version History does not occur.
    """
    i = text.find(VH_MARKER)
    if i < 0:
        return None
    # `text[:i]` stops BEFORE the marker's leading newline, so the heading sits
    # one line past the count: `"a\n## Version History"` -> i=1, 0 newlines, L2.
    return text.count("\n", 0, i) + 2


def _trim_version_history(text: str, keep: int | None, *, ref: str) -> str:
    """Keep the body verbatim and only the LAST `keep` `## Version History`
    entries; replace the omitted ones with a single line that states the count
    and the way back to the record.

    Why: Version History measured ~36% of every doc-block-exec document
    (design 172,720 of 483,815 chars; impl-plan 193,134 of 536,527) and was
    embedded verbatim into every audit prompt -- the target's AND each paired
    sibling's -- which is what carried two of three gating prompts past
    MAX_PROMPT_CHARS. The omitted entries are dated records, not the audit's
    subject; auditors that need them run `git show <sha>:<doc>`, which is how
    every auditor this round actually read them. `keep=None` (the default) is a
    strict no-op so existing callers and prompt hashes are unaffected.
    """
    if keep is None:
        return text

    # A negative tail is not a tail, and 0 means "inline none" -- a legitimate
    # maximum-trim request and the natural escalation when `--vh-tail 1` is still
    # too large. Both used to land on `entry_idx[-keep]`, where Python's -0 == 0
    # selects the FIRST entry: every entry survived while the note below claimed
    # they had been omitted, so the result was LONGER than the untrimmed text. The
    # one value an operator reaches for when the halt fires was the one that made
    # the prompt bigger, silently. Measured: keep=1 -> 228 chars, keep=0 -> 249.
    keep = max(keep, 0)

    i = text.find(VH_MARKER)
    if i < 0:
        _vh_noop(ref, "no `## Version History` heading")
        return text
    body, vh = text[:i], text[i:]
    lines = vh.split("\n")
    entry_idx = [k for k, ln in enumerate(lines) if ln.startswith("- v")]
    if not entry_idx:
        # The heading is there and nothing matched `- v`. Real documents in this
        # repo render their history as a markdown TABLE, and for those this
        # function returns byte-identical text -- so `--vh-tail`, the remedy the
        # oversize halt prescribes by name, does nothing and says nothing, and the
        # operator re-runs it with a smaller N and loops. Announcing it is the
        # whole fix available here: trimming a table is a different feature, and
        # guessing at its row grammar would be worse than saying so.
        _vh_noop(ref, "the `## Version History` section has no `- v` entries "
                      "(a table-formatted history is not trimmable)")
        return text
    if len(entry_idx) <= keep:
        _vh_noop(ref, f"only {len(entry_idx)} entries, which is not more than "
                      f"--vh-tail {keep}")
        return text
    omitted = len(entry_idx) - keep
    head = lines[:entry_idx[0]]            # "" + heading + any preamble
    # `keep == 0` drops every entry but preserves whatever follows the last one --
    # `lines[entry_idx[-0]:]` would have kept them all, and a bare `[]` would
    # silently swallow any section that comes after the history.
    kept = lines[entry_idx[-keep]:] if keep else lines[entry_idx[-1] + 1:]
    note = (f"<!-- h-mad assembler: {omitted} of {len(entry_idx)} Version History "
            f"entries omitted from this inline copy (--vh-tail {keep}); they are dated "
            f"records, not this audit's subject -- read them with `git show <sha>:{ref}` -->")
    return body + "\n".join(head + [note] + kept)


def assemble(*, feature: str, phase: str, project_root: Path, docs_dir: Path,
             sentinel: str, report_file: str, template: Path,
             design_dir: Path | None = None,
             vh_tail: int | None = None) -> tuple[str, list[str]]:
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

    def doc_text(kind: str) -> str:
        path = doc(kind)
        try:
            ref = str(path.resolve().relative_to(project_root.resolve()))
        except ValueError:
            ref = path.name
        return _trim_version_history(_read(path, required=True), vh_tail, ref=ref)

    base_md = _read(SKILL_DIR / "invariants.base.md", required=True)
    project_md = _read(project_root / ".h-mad" / "invariants.md", required=False)

    slots = {
        "<INLINE_TARGET_DOC>": doc_text(phase),
        "<INLINE_BASE_INVARIANTS>": base_md,
        "<INLINE_PROJECT_INVARIANTS>": project_md,
        "<AUDIT_SENTINEL>": sentinel,
        "<REPORT_FILE_PATH>": report_file,
    }
    if phase in ("plan", "design"):
        slots["<INLINE_PAIRED_SPEC>"] = doc_text("spec")
    if phase == "design":
        slots["<INLINE_PAIRED_PLAN>"] = doc_text("plan")
    if phase == "impl-plan":
        slots["<INLINE_PAIRED_DESIGN>"] = doc_text("design")

    for slot, value in slots.items():
        text = text.replace(slot, value)

    # After slot fill, so the head copy arrives pre-filled and preflight's
    # unfilled-slot check stays honest. The framing block sits after both
    # invariants slots in the template, so the duplicate cannot trip preflight's
    # rubric-duplication needles.
    text, contract_problems = prepend_output_contract(
        text, sentinel=sentinel, report_file=report_file)

    return text, contract_problems + preflight(text, {"base": base_md, "project": project_md})


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
    ap.add_argument("--vh-tail", type=int, default=None, metavar="N",
                    help="inline only the last N `## Version History` entries of every "
                         "embedded document (target and paired), replacing the rest with a "
                         "one-line omission note; default: embed the whole history")
    args = ap.parse_args(argv)

    docs_dir = args.docs_dir or (args.project_root / "docs/01-plan/features")
    sentinel = args.sentinel or f"AUDIT-{args.feature}-{args.phase}-v{args.cycle}"
    out = args.out or Path(f"/tmp/audit_{args.feature}_{args.phase}_cycle{args.cycle}.txt")

    try:
        text, problems = assemble(
            feature=args.feature, phase=args.phase, project_root=args.project_root,
            docs_dir=docs_dir, design_dir=args.design_dir, sentinel=sentinel,
            report_file=args.report_file, template=args.template,
            vh_tail=args.vh_tail,
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

    if prompt_oversize(len(text)):
        # A verdict, not a process failure: exit 0, explicit token, NO file --
        # an unwritten prompt cannot be dispatched by mistake. This replaces a
        # PASS that two surfaces refused outright on 2026-09-05. The comparison
        # reserves the wrapper's boundary overhead (see DISPATCH_OVERHEAD_CHARS):
        # a bare `len(text) > MAX_PROMPT_CHARS` passed the last 30 chars of room
        # that codex then refused.
        print(f"ASSEMBLE: HALT {args.phase}:oversize chars={len(text)} "
              f"limit={MAX_PROMPT_CHARS} headroom={DISPATCH_OVERHEAD_CHARS}")
        print("  - no known surface accepts a prompt this large: codex exec refuses it "
              "(input_too_large) and agy's arg path is capped at the same figure. "
              "Re-run with --vh-tail N to inline only the last N Version History "
              "entries of each embedded document; the omitted entries stay reachable "
              "via `git show <sha>:<doc>`.")
        return 0

    out.write_text(text, encoding="utf-8")
    size = len(text.encode())
    # J12: size travels ON the verdict line, not beside it. SKILL.md mandates
    # asserting `ASSEMBLE: PASS`, so a separate warning line is a signal nothing
    # is obliged to read -- the defect the PREFLIGHT: token was created to fix,
    # one signal over.
    #
    # The verdict token itself stays exactly PASS/HALT. `PASS_OVERSIZE` (the
    # filed suggestion) matches `grep "ASSEMBLE: PASS"` and
    # `startswith("ASSEMBLE: PASS")` -- how every consumer reads it -- so it would
    # have reproduced J12 instead of fixing it. And HALT is contradicted by
    # evidence: J13 measured five file-indirection prompts across 53-61 KB, all
    # answered. Proceeding is correct; being unable to MISS the size is the fix.
    # The frontier below is PANE-PATH-SPECIFIC. It is anchored to the largest
    # prompt CONFIRMED answered when delivered by `hmad-dispatch send` into a TUI
    # pane -- the path where the silent-output failure mode lives (the TUI reflows
    # a large reply across redraw frames; see references/agent-substrate.md
    # §"Prompt size"). Six file-indirection observations spanning 52,997-92,055 B
    # were all answered; there is no file-indirection silence on record. The old
    # 49 KB "cliff" was a delivery-mode artifact (a paste, not file indirection)
    # and never reproduced -- it once cost a real design audit a needless trim,
    # and a 61,493 B "ceiling" that replaced it was itself falsified 2026-07-30 by
    # a 92,055 B pane prompt answered cleanly (agy/Gemini 3.1 Pro; reply fragmented
    # across frames, so read the full buffer, never a tail).
    #
    # `hmad-dispatch exec` (codex stdin / agy `--print` arg) has no PANE frontier
    # but IS capped: codex refuses past MAX_PROMPT_CHARS with `input_too_large`
    # (measured 2026-09-05, 1,123,643 and 1,053,882 chars both refused) and agy's
    # arg is bounded at the same figure; a >90 KB exec prompt was confirmed
    # answered 2026-07-30, and 266,342 B (260.1 KB) was confirmed answered 8 of 8 on
    # 2026-08-22 (agy 1.1.18) with both the report-file slot and the sentinel pair
    # honoured every time -- three times the largest audit this assembler emits.
    # That measurement also refutes J30's size premise at this agy version; its
    # 5-of-5 drop was on an older build under the text-mode transport.
    # So on the exec path these warnings are advisory only.
    # The assembler cannot know which transport the caller will use, so it warns on
    # the conservative (pane) basis; ignore it when you will dispatch via `exec`.
    CONFIRMED_OK = 92_055  # largest PANE prompt observed answered (2026-07-30)
    size_status = "verified" if size <= CONFIRMED_OK else "unverified"
    print(f"ASSEMBLE: PASS {out} {size}B ({size / 1024:.1f} KB) "
          f"sentinel={sentinel} size_status={size_status}")
    for note in size_notes(size, text):
        print(note)
    if size > CONFIRMED_OK:
        print(f"  ! {size / 1024:.1f} KB exceeds the largest prompt confirmed answered "
              f"on the pane path ({CONFIRMED_OK / 1024:.1f} KB) — unverified there, not "
              "known-bad; `hmad-dispatch exec` accepts up to 1,048,576 chars on both agents "
              "(codex refuses past it with input_too_large). If a PANE reply comes back "
              "empty, suspect size and see SKILL.md "
              "step 5.5; the failure mode is silent, so read the full buffer, never a tail")
    elif size > 84 * 1024:
        print(f"  ~ {size / 1024:.1f} KB is approaching the largest prompt confirmed "
              f"answered on the pane path ({CONFIRMED_OK / 1024:.1f} KB) — a non-issue via "
              "`hmad-dispatch exec`; on the pane path, inlining only the spec's "
              "'## Functional Requirements' section saves ~7 KB and loses no AC "
              "(SKILL.md step 5.5)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
