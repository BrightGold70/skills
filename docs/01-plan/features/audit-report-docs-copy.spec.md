# Spec: audit-report-docs-copy

## Executive Summary
Every audit report the h-mad recipe gates must first exist in the feature's docs store at a
path derived from `(feature, phase, cycle, surface)`, copied byte-for-byte from the transport
file by the one collector that already knows that tuple, and the gate refuses to score a
transport file at all.

## Goal
Make the docs copy of an audit report a mechanical step of the recipe — performed by
`h_mad_audit_cycle.collect()` for every leg, exposed as a CLI for the codex leg run outside
`audit-cycle` — so a `/tmp`-only report can neither be lost on reboot nor gate a phase.

## Functional Requirements

### FR-1: Surface-aware collected path — one derivation
- **Description**: `h_mad_audit_cycle._collected_path()` accepts an optional `surface` token.
  With `surface=None` it returns exactly what it returns today
  (`docs/<dir>/<feature>.<phase>.audit.v<cycle>.p<index>.md`). With a surface it returns
  `docs/<dir>/<feature>.<phase>.audit.v<cycle>.<surface>.md`. `collect()` threads the token
  through unchanged. No other code derives an audit docs path.
- **Acceptance Criteria**:
  - AC-1.1: `_collected_path(project_root=r, feature="f", phase="plan", cycle=8, index=1)` and
    the same call with `surface=None` return the identical `Path` ending `f.plan.audit.v8.p1.md`.
  - AC-1.2: `_collected_path(..., cycle=8, index=1, surface="codex")` returns a `Path` ending
    `docs/01-plan/features/f.plan.audit.v8.codex.md`; `phase="design"` maps to
    `docs/02-design/features/`; `phase="impl-plan"` maps to `docs/01-plan/features/`.
  - AC-1.3: A `surface` that does not match the single dot-free token grammar
    (`h_mad_cycle_counts._VERSION_RE`'s discriminator: `[A-Za-z0-9][A-Za-z0-9_-]*`) or that
    matches `^p\d+$` raises `ValueError` naming the token — the path is never built.
  - AC-1.4: `collect(spec, ..., surface="codex")` writes its collected file at the AC-1.2 path;
    `collect(spec, ...)` with no `surface` keyword writes at the AC-1.1 path (existing
    `test_h_mad_audit_cycle.py` collect tests pass unchanged).
  - AC-1.5: `grep -rn 'audit\.v' h-mad/scripts/*.py` shows the docs-path string built in
    exactly one function (`_collected_path`); the new CLI imports it rather than re-deriving.

### FR-2: `h_mad_collect_report.py` — the codex-leg collector
- **Description**: A stdlib-only CLI over `collect()`:
  `h_mad_collect_report.py --feature <f> --phase plan|design|impl-plan --cycle <N>
  --surface <s> --report <RP> [--out <out>] --project-root <root> [--grace <s>]`.
  It prints one contract line `COLLECT: OK|MISSING|CONFLICT path=<docs path>
  delivered=report-file|out|none` followed by `[H-MAD] <feature> collect <verdict>`,
  exits 0 on every verdict and 2 on an operational error (unreadable project root, bad
  `--surface`, unwritable docs directory, missing required flag). `--out` is optional; when
  omitted the `--out` fallback rung is skipped and a missing report is `MISSING`.
- **Acceptance Criteria**:
  - AC-2.1: With `<RP>` present, non-empty, `<RP>.done` present, and no existing docs file:
    prints `COLLECT: OK path=<AC-1.2 path> delivered=report-file`, exit 0, and the docs file's
    bytes equal `<RP>`'s bytes (`filecmp.cmp(shallow=False)` is True).
  - AC-2.2: With `<RP>` absent and no `--out` (or `--out` absent/empty): prints
    `COLLECT: MISSING path=<AC-1.2 path> delivered=none`, exit 0, and no file exists at the
    docs path afterwards (RED direction: nothing to gate).
  - AC-2.3: With `<RP>` present but `<RP>.done` absent, and `--grace 0`: verdict is `MISSING`
    (the marker, not file existence, is completion — same contract as `report_wait`).
  - AC-2.4: With the docs file already present and byte-identical to `<RP>`: `COLLECT: OK …
    delivered=report-file`, exit 0, and the docs file's mtime is unchanged (no write).
  - AC-2.5: With the docs file already present and DIFFERENT from `<RP>`: `COLLECT: CONFLICT
    path=… delivered=report-file`, exit 0, and the docs file's bytes are unchanged (never
    clobbered). `_copy_collected_report` no longer unlinks-then-writes over differing content.
  - AC-2.6: With `<RP>` absent and `--out <out>` present containing a sentinel-wrapped report
    for `(feature, phase, cycle)`: `COLLECT: OK … delivered=out`, exit 0, docs file holds the
    extracted text (byte-identity to `<RP>` is NOT asserted for `delivered=out`).
  - AC-2.7: `--surface p2` (or any `p\d+`) → exit 2, stderr names the token, no `COLLECT:` line.
    `--surface codex.draft` → exit 2 likewise.
  - AC-2.8: When `--report` resolves (`Path.resolve()`) to the derived docs path itself:
    no copy is attempted; verdict `OK` iff the file is non-empty and `<path>.done` exists;
    the `.done` marker is removed and a detail line `marker: removed <path>.done` is printed;
    otherwise `MISSING`.
  - AC-2.9: Tracer against the live corpus: `h_mad_collect_report.py --feature
    nlm-cli-version-pin --phase plan --cycle 8 --surface codex --report
    /tmp/audit_nlmpin_plan_cycle8_codex.report.md --project-root
    /Users/kimhawk/orca/HemaSuite/hematology-paper-writer` prints `COLLECT: OK path=…/
    nlm-cli-version-pin.plan.audit.v8.codex.md delivered=report-file` and `git status --short`
    in that repo is unchanged (existing-identical → no write). Recorded in the plan, not
    asserted by the suite (the corpus is machine-local).

### FR-3: The gate refuses a transport file
- **Description**: `h_mad_audit_gate.py` refuses to score any path whose basename ends
  `.report.md`, printing exactly `GATE: INVALID must=0 should=0` and
  `[H-MAD] <feature> gate INVALID (transport file — collect it into docs first:
  h_mad_collect_report.py)`, exit 2. All other behaviour unchanged.
- **Acceptance Criteria**:
  - AC-3.1: `h_mad_audit_gate.py /tmp/audit_f_plan_cycle3_codex.report.md` on a well-formed
    report (has `## Must-fix`/`## Should-fix`) prints `GATE: INVALID must=0 should=0`, the
    `[H-MAD]` line contains `transport file`, exit 2.
  - AC-3.2: The same bytes at `docs/01-plan/features/f.plan.audit.v3.codex.md` gate normally
    (`GATE: PASS|FAIL …`, exit 0).
  - AC-3.3: `h_mad_audit_cycle.gate()` handed a `.report.md` path returns
    `("INVALID", 0, 0, [])` (rc 2 is already mapped) and `combine()` renders `UNVERIFIED`
    with reason `no_gate_sections:p<i>` — no new verdict word.
  - AC-3.4: `h_mad_do_preconditions.py` is unaffected: it reads docs paths only (existing
    tests pass).
  - AC-3.5: The refusal is by **basename grammar**, not directory: a `.report.md` inside
    `docs/` is refused too; a `.md` under `/tmp` that is not `.report.md` is not refused by
    this rule.

### FR-4: `hmad-dispatch collect-report` wrapper verb
- **Description**: A thin verb delegating to the script, exactly as `report-wait` delegates to
  `h_mad_report_wait.py`, so the SKILL.md recipe stays in `hmad-dispatch` vocabulary.
- **Acceptance Criteria**:
  - AC-4.1: `hmad-dispatch collect-report <args…>` execs `python3 <here>/h_mad_collect_report.py
    <args…>` and propagates its exit code and stdout unchanged.
  - AC-4.2: The verb is listed in the wrapper's header verb list (line 3) and in
    `references/orchestration-mode.md`'s verb table beside `report-wait`.

### FR-5: The codex-leg recipe exists in SKILL.md
- **Description**: SKILL.md gains a block (beside the `audit-cycle` documentation, outside the
  slices `test_h_mad_audit_cycle_docs.py` pins) documenting the second-surface leg:
  assemble with `--report-file "$RP"` → `exec codex … --out --log` → `hmad-dispatch
  collect-report --surface codex …` → gate the **printed** docs path, never `$RP`. The helper
  registry gains an `h_mad_collect_report.py` entry. Step 9 gains one sentence: the gate
  refuses `*.report.md`.
- **Acceptance Criteria**:
  - AC-5.1: `grep -c 'collect-report' h-mad/SKILL.md` ≥ 2 (recipe block + registry).
  - AC-5.2: `test_h_mad_audit_cycle_docs.py` passes unchanged (anchors intact).
  - AC-5.3: A docs test asserts the recipe block orders `exec codex` before `collect-report`
    before `h_mad_audit_gate.py`, and that the gate line in the block does not contain `$RP`.
  - AC-5.4: The registry entry names the token set `COLLECT: OK|MISSING|CONFLICT` and the
    exit contract (0 on verdict / 2 on operational error).

### FR-6: Pinned both directions, mutation-verified
- **Description**: Tests and a mutation spec make the guard's absence visible.
- **Acceptance Criteria**:
  - AC-6.1: `tests/test_h_mad_collect_report.py` covers AC-2.1–2.8 and AC-1.1–1.4.
  - AC-6.2: `tests/test_h_mad_audit_gate.py` (or a new file) covers AC-3.1, 3.2, 3.5.
  - AC-6.3: `tests/mutation-specs/collect_report.json` has ≥ 4 mutations, each with a named
    `test`: (a) the copy writes an empty file → AC-2.1 test bites; (b) CONFLICT branch
    replaced by overwrite → AC-2.5 bites; (c) surface validation removed → AC-2.7 bites;
    (d) gate transport refusal removed → AC-3.1 bites. `h_mad_mutation_harness.py` reports
    `MUTATION: ALL_CAUGHT`.
  - AC-6.4: `test_hmad_dispatch_audit_cycle.py::test_audit_cycle_mutation_specs_*` and
    `…_name_existing_failure_tests` pass with the new spec present.
  - AC-6.5: Full `h-mad/tests` suite green from this worktree.

## Non-Functional Requirements
- Performance: N/A (one file copy per audit pass).
- Security: no new external dependency; stdlib only; no network.
- Compatibility: `_collected_path`/`collect()` default-argument change is source-compatible
  with every existing caller; `audit-cycle` output is byte-identical when no surface is given.
  Filenames stay inside the documented grammar (`SKILL.md` §"Audit filename grammar").

## Out-of-Scope
- Teaching `audit-cycle` to dispatch codex as a pass (`--agents`) — deferred by operator
  decision 2026-09-02.
- Any change to `h_mad_report_wait.py`, `h_mad_extract_report.py`, or `exec`'s flag surface.
- Consuming or deleting `/tmp` transport files after collection (they stay; `/tmp` is the
  agent's channel, not ours) — except the AC-2.8 docs-path `.done` marker.
- Back-filling the 98 historically surface-named audits or changing `h_mad_cycle_counts`.

## Assumptions
- The transport-file basename grammar is exactly `*.report.md` and no docs artifact uses it
  (corpus: 1120 audit files, all `.audit.v<N>[.tok].md`).
- `h_mad_audit_cycle.gate()`'s rc-2 → `INVALID` mapping and `_gate_token`'s regex remain as
  read on 2026-09-02.
- The live run in the main checkout keeps reading `~/.claude/skills/h-mad` (main checkout);
  this worktree's edits are invisible to it until merge.

## Version History
- v1.0: Initial specification draft.
