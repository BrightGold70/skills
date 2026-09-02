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
  - AC-1.6: **Disjoint namespace, proven by property, not by a production assert.** A
    derived docs basename always contains `.audit.v<N>` (dots) and `TRANSPORT_RE` requires a
    dot-free stem, so the two grammars are disjoint by construction and no runtime check is
    needed (a check that can never fire cannot be mutation-tested). The property is pinned by
    a test: for every `(feature, surface)` in a fixture that includes the adversarial pairs
    `("audit_f", "report")`, `("audit_x", "report_md")`, `("audit_", "p")` and ordinary ones,
    `_collected_path(...)` basename matches `h_mad_cycle_counts._VERSION_RE` and does NOT
    match `h_mad_audit_gate.TRANSPORT_RE`. Mutations: `TRANSPORT_RE` loosened to
    `^audit_.*\.report\.md$` (the v1.2 grammar) → this test bites on `audit_f`/`report`;
    the docs pattern loses its `.audit.v` dots (force) → AC-1.1/1.2 bite. `_collected_path`
    imports nothing from the gate.

### FR-2: `h_mad_collect_report.py` — the codex-leg collector
- **Description**: A stdlib-only CLI over `collect()`:
  `h_mad_collect_report.py --feature <f> --phase plan|design|impl-plan --cycle <N>
  --surface <s> --report <RP> [--out <out>] --project-root <root> [--grace <s>]`.
  It prints one contract line `COLLECT: OK|MISSING|CONFLICT path=<docs path>
  delivered=report-file|out|none` followed by `[H-MAD] <feature> collect <verdict>`,
  exits 0 on every verdict and 2 on an operational error (unreadable project root, bad
  `--surface`, unwritable docs directory, missing required flag). `--out` is optional; when
  omitted the `--out` fallback rung is skipped and a missing report is `MISSING`.
  **Internal contract** (compatible with every existing caller): `PassSpec.out_path` may be
  `None`, in which case `collect()` skips `_run_extract_report`; `_copy_collected_report`
  gains a keyword `overwrite: bool = True` and, when `False` and the target exists with
  different bytes, raises `CollectConflict(OperationalError)` without writing.
  `audit-cycle` keeps `overwrite=True` (a re-dispatched cycle replaces its own collected
  file); the CLI passes `overwrite=False` unless `--force` is given and renders the
  exception as `COLLECT: CONFLICT`. **The policy covers BOTH delivery rungs**:
  `_write_collected_report` (the `--out` extract rung) takes the same `overwrite` keyword
  and raises the same `CollectConflict`. `collect()`'s `(delivered, collected_path)` return
  is unchanged. **Every mutating step reads itself back** (base invariant "Mutation
  verification"): after a copy or forced overwrite the collector re-reads the docs file and
  compares bytes to the source; after removing a docs-path `.done` marker it re-checks
  `exists()`; a disagreement is an operational failure — exit 2, no `COLLECT:` line, and
  a `[H-MAD] … collect readback_failed` marker.
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
    clobbered). With `--force` the same input prints `COLLECT: OK … forced=1` and the docs
    file now equals `<RP>`.
  - AC-2.6: With `<RP>` absent and `--out <out>` present containing a sentinel-wrapped report
    for `(feature, phase, cycle)`: `COLLECT: OK … delivered=out`, exit 0, docs file holds the
    extracted text (byte-identity to `<RP>` is NOT asserted for `delivered=out`).
  - AC-2.6a: `<RP>` absent, `--out` valid, docs file present with DIFFERENT bytes →
    `COLLECT: CONFLICT … delivered=out`, docs bytes unchanged; with `--force` → `OK …
    delivered=out forced=1`, docs now equals the extracted text.
  - AC-2.6b: `<RP>` absent, `--out` valid, docs file present and identical to the extracted
    text → `COLLECT: OK … delivered=out`, mtime unchanged.
  - AC-2.7: `--surface p2` (or any `p\d+`) → exit 2, stderr names the token, no `COLLECT:` line.
    `--surface codex.draft` → exit 2 likewise.
  - AC-2.8: When `--report` resolves (`Path.resolve()`) to the derived docs path itself:
    no copy is attempted; verdict `OK` iff the file is non-empty and `<path>.done` exists;
    the `.done` marker is removed and a detail line `marker: removed <path>.done` is printed;
    otherwise `MISSING`.
  - AC-2.9: **Incident replay** (suite test, synthetic bytes) — in an isolated project root
    with NO docs copy: (i) `h_mad_audit_gate.py <RP>` → `GATE: INVALID`, exit 2 (cannot gate
    before collection); (ii) `collect-report --surface codex` → `COLLECT: OK … delivered=
    report-file`, docs file created, `filecmp.cmp(<RP>, docs, shallow=False)` True;
    (iii) `h_mad_audit_gate.py <docs path>` → `GATE: PASS|FAIL …`, exit 0. The same three
    steps are run once by hand against a real survivor (`/tmp/audit_nlmpin_plan_cycle8_codex.report.md`
    copied into a scratch project root, never HemaSuite's live tree) and the transcript is
    recorded in the plan's Version History.
  - AC-2.10: Operational errors exit 2 and print **no** `COLLECT:` line: `--project-root`
    that is not a directory; a docs directory that cannot be created or written (e.g. a
    file at `docs/01-plan/features`); a missing required flag (`--surface`, `--report`).
  - AC-2.12: Readback: with the writer patched to land wrong bytes (test seam), the CLI
    exits 2, prints no `COLLECT:` line and prints `[H-MAD] … collect readback_failed`; with
    the marker remover patched to a no-op, the AC-2.8 case exits 2 likewise.
  - AC-2.11: Existing-identical docs file with `--surface` given and `<RP>.done` absent →
    `COLLECT: OK … delivered=report-file` (the docs copy already IS the collected report; the
    marker is only required when a copy must be made).

### FR-3: The gate refuses a transport file
- **Description**: `h_mad_audit_gate.py` refuses to score any path whose basename matches
  the **transport grammar** `TRANSPORT_RE = ^audit_[^.]+\.report\.md$` — prefix `audit_`,
  a dot-free stem, suffix `.report.md` — defined ONCE in `h_mad_audit_gate.py`; the only
  other importers are the tests (AC-1.6, AC-3.5a). Neither the CLI nor `_collected_path`
  imports it — no production code needs it besides the gate (base invariant "Single-source
  contract"). The dot-free stem is what makes the two
  grammars disjoint by construction: every docs audit name contains `.audit.v<N>` (dots),
  every transport name observed in `/tmp` (2026-09-02, 331 files) has no dot before
  `.report.md`.
  It prints exactly `GATE: INVALID must=0 should=0` and `[H-MAD] <feature> gate INVALID
  (transport file — collect it into docs first: h_mad_collect_report.py)`, exit 2.
  Why prefix+suffix and not a `_cycle<N>` stem: the field stages transport files by hand
  too — observed in `/tmp` on 2026-09-02: `audit_hnag_c28_agy.report.md`,
  `audit_hnag_implplan_c11.report.md`, `audit_x_cycle8_agy_p2.report.md` — none carrying
  `_cycle<N>`, all carrying the prefix and suffix; and a surface token may contain `_`
  (`_VERSION_RE` accepts `[A-Za-z0-9_-]`), which a `[A-Za-z0-9-]` stem would miss. A bare
  `*.report.md` is NOT refused: Phase-7 reports are `<feature>.report.md` with hyphenated
  slugs (`docs/04-report/features/*.report.md`: 7 files, 0 starting `audit_`; this feature's
  own will be `audit-report-docs-copy.report.md`, hyphen). A docs artifact whose feature
  happens to start with `audit_` and whose surface is `report`
  (`audit_f.plan.audit.v8.report.md`) is NOT transport (it has dots) — AC-1.6 pins that no
  derived name can be. **Backward compatibility**: the
  base invariant preserves the PASS verdict of every audit DOC; a transport file is not an
  audit doc, no recipe or test gated one (grep: 0), and the same bytes at their docs path
  keep their verdict — pinned by AC-3.7.
- **Acceptance Criteria**:
  - AC-3.1: `h_mad_audit_gate.py /tmp/audit_f_plan_cycle3_codex.report.md` on a well-formed
    report (has `## Must-fix`/`## Should-fix`) prints `GATE: INVALID must=0 should=0`, the
    `[H-MAD]` line contains `transport file`, exit 2. The same for the hand-staged shapes
    `audit_hnag_c28_agy.report.md`, `audit_hnag_implplan_c11.report.md`,
    `audit_f_plan_cycle8_codex_draft.report.md`, `audit_f_plan_cycle8_agy_p2.report.md`.
  - AC-3.2: The same bytes at `docs/01-plan/features/f.plan.audit.v3.codex.md` gate normally
    (`GATE: PASS|FAIL …`, exit 0).
  - AC-3.3: `h_mad_audit_cycle.gate()` handed a transport-stem path returns
    `("INVALID", 0, 0, [])` (rc 2 is already mapped) and `combine()` renders `UNVERIFIED`
    with reason `no_gate_sections:p<i>` — no new verdict word.
  - AC-3.4: `h_mad_do_preconditions.py` is unaffected: it reads docs paths only (existing
    tests pass).
  - AC-3.5: The refusal is by **basename grammar**, not directory: `audit_f_plan_cycle3_codex.report.md`
    is refused wherever it sits, including under `docs/`; `f.report.md`,
    `gate-blindness-hardening.report.md`, `audit-report-docs-copy.report.md` (hyphen) and any
    `.md` under `/tmp` not matching `TRANSPORT_RE` are scored normally, and so is
    `audit_f.plan.audit.v8.report.md` (dots in the stem) (force-refusal mutation: a gate
    that refuses every `.report.md` breaks this test).
  - AC-3.5a: **Shared corpus, both directions** — one fixture list of names with an expected
    `transport: True|False` per name (every staged shape above, every docs shape:
    `.audit.v<N>.md`, `.audit.v<N>.p<i>.md`, `.audit.v<N>.codex.md`, `.audit.v<N>.codex_draft.md`,
    `<feature>.report.md`, and the collision candidates `audit_f.plan.audit.v8.report.md` /
    `audit_f.plan.audit.v8.codex.md`) is asserted against `TRANSPORT_RE` **and** against
    `h_mad_cycle_counts._VERSION_RE` (an audit-doc name must match `_VERSION_RE` and not
    `TRANSPORT_RE`; a transport name the reverse; NO name in the fixture matches both). The stem the wrapper stages is pinned by
    running `audit-cycle` under the existing stub harness and asserting the `--report-file`
    the stub received matches `TRANSPORT_RE`; the SKILL.md 6.6 literal is asserted to match
    it too.
  - AC-3.7: **Verdict preservation** — for every `*.audit.v*.md` under this repo's `docs/`
    (live and archive), `is_transport_path()` is False, so the gate's verdict for every
    existing audit doc is unchanged by this feature.
  - AC-3.6: A Phase-7 report path (`docs/04-report/features/x.report.md` with gate sections)
    gates normally (`GATE: PASS|FAIL`, exit 0).

### FR-4: `hmad-dispatch collect-report` wrapper verb
- **Description**: A thin verb delegating to the script, exactly as `report-wait` delegates to
  `h_mad_report_wait.py`, so the SKILL.md recipe stays in `hmad-dispatch` vocabulary.
- **Acceptance Criteria**:
  - AC-4.1: `hmad-dispatch collect-report <args…>` execs `python3 <here>/h_mad_collect_report.py
    <args…>` and propagates its exit code and stdout unchanged — pinned by a wrapper test
    that runs the verb against a stub script dir (`HMAD_AUDIT_CYCLE_SCRIPT_DIR`, the same
    hook the audit-cycle tests use) and fails when the route is severed.
  - AC-4.2: The verb is listed in the wrapper's header verb list (line 3) and in
    `references/orchestration-mode.md`'s verb table beside `report-wait`.
  - AC-4.3: Negative route: `hmad-dispatch collect-reportx …` prints `unknown verb` and does
    NOT exec the script (stub script dir records zero invocations).

### FR-5: The codex-leg recipe exists in SKILL.md
- **Description**: SKILL.md gains a block (beside the `audit-cycle` documentation, outside the
  slices `test_h_mad_audit_cycle_docs.py` pins) documenting the second-surface leg:
  assemble with `--report-file "$RP"` → `exec codex … --out --log` → `hmad-dispatch
  collect-report --surface codex …` → **read the `COLLECT:` token**: anything but `OK` halts
  `<phase>:report_not_collected` with an `[H-MAD]` marker and the gate is NOT run → on `OK`,
  gate the **printed** docs path, never `$RP`. The helper registry gains an
  `h_mad_collect_report.py` entry. Step 9 gains one sentence: the gate refuses the transport
  stem.
- **Acceptance Criteria**:
  - AC-5.1: `grep -c 'collect-report' h-mad/SKILL.md` ≥ 2 (recipe block + registry).
  - AC-5.2: `test_h_mad_audit_cycle_docs.py` passes unchanged (anchors intact).
  - AC-5.3: A docs test asserts the recipe block orders `exec codex` before `collect-report`
    before a `COLLECT:`-token read that names `report_not_collected` before
    `h_mad_audit_gate.py`, and that the gate line in the block does not contain `$RP`.
  - AC-5.4: The registry entry names the token set `COLLECT: OK|MISSING|CONFLICT` and the
    exit contract (0 on verdict / 2 on operational error).

### FR-6: Pinned both directions, mutation-verified
- **Description**: Tests and a mutation spec make the guard's absence visible.
- **Acceptance Criteria**:
  - AC-6.1: `tests/test_h_mad_collect_report.py` covers AC-2.1–2.8 and AC-1.1–1.4.
  - AC-6.2: `tests/test_h_mad_audit_gate.py` (or a new file) covers AC-3.1, 3.2, 3.5.
  - AC-6.3: `tests/mutation-specs/collect_report.json` has ≥ 8 mutations, each with a named
    `test`, pairing every new connection in BOTH directions (base invariant "Connection
    enforcement"): (a) the copy writes an empty file → AC-2.1 bites; (b) CONFLICT branch
    replaced by overwrite → AC-2.5 bites; (b′) overwrite forced to refuse even with `--force`
    → AC-2.5 force case bites; (c) surface validation removed → AC-2.7 bites; (c′) surface
    validation forced to reject every token → AC-2.1 bites; (d) `_collected_path` ignores
    `surface` (drop) → AC-1.2 bites; (d′) `_collected_path` emits `.<surface>` even when
    `surface=None` (force) → AC-1.1 bites; (e) CLI no longer calls `collect()` (delegation
    severed: returns a hard-coded `OK`) → AC-2.2 bites; (e′) CLI calls `collect()` on the
    fall-through path too (after a rejected `--surface` / bad project root) → AC-2.7/2.10
    (exit 2 with NO `COLLECT:` line) bite; (f) `hmad-dispatch collect-report` route severed
    (execs nothing / wrong script) → AC-4.1 bites; (f′) the wrapper routes the fall-through
    (an unknown verb such as `collect-reportx`) to the script (force) → AC-4.3 bites; (g)
    gate transport refusal removed → AC-3.1 bites; (g′) gate refuses every `.report.md`
    (force) → AC-3.5/3.6 bite; (h) copy readback removed → AC-2.12 bites; (h′) out-rung
    conflict check removed → AC-2.6a bites; (i) `TRANSPORT_RE` loosened to the v1.2 `.*`
    stem → AC-1.6 property bites; (i′) `_collected_path` docs pattern loses its `.audit.v`
    dots (force toward transport shape) → AC-1.1/1.2 bite; (j) gate refusal keeps exit 2 +
    token but drops its `[H-MAD]` marker → AC-3.1 bites; (j′) CLI operational-error path
    drops its marker → AC-2.10 bites; (k) gate refusal exits 0 → AC-3.1 bites; (k′) gate
    refusal prints a PASS token → AC-3.1 bites; (l) CLI error path exits 0 → AC-2.10 bites;
    (l′) CLI error path prints a `COLLECT:` line → AC-2.10 bites. 23 mutations.
    `h_mad_mutation_harness.py` reports `MUTATION: ALL_CAUGHT`.
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
- The transport-file basename grammar is `^audit_[^.]+\.report\.md$` (prefix, dot-free stem,
  suffix): every recipe-staged AND hand-staged transport file observed in `/tmp` on
  2026-09-02 (331) matches it, and no docs audit name can — they all carry `.audit.v<N>`
  (`find docs -name 'audit_*'` → 0; Phase-7 reports are `<feature>.report.md` with hyphenated
  slugs). v1.0 claimed the bare suffix was transport-only (false: Phase 7); v1.1 claimed a
  `_cycle<N>` stem (false: hand-staged names); v1.2's `^audit_.*` overlapped a derivable docs
  name (`audit_f` + `report`) — hence the dot rule and the AC-1.6 disjointness property test.
- `h_mad_audit_cycle.gate()`'s rc-2 → `INVALID` mapping and `_gate_token`'s regex remain as
  read on 2026-09-02.
- The live run in the main checkout keeps reading `~/.claude/skills/h-mad` (main checkout);
  this worktree's edits are invisible to it until merge.

## Version History
- v1.0: Initial specification draft.
- v1.6: 5b-audit v2 sweep: exit-only/token-only mutants (k, k′, l, l′) → 23.
- v1.5: Design-audit v8 sweep: marker-stripping mutants (j)/(j′) → 19 mutations (Mutation verification: one mutant per separable output part).
- v1.4: Plan-audit v6 fix (codex): the AC-1.6 production assert was unreachable under the dot-free grammar (a check that can never fire cannot be mutation-tested) — replaced by a property test over adversarial `(feature, surface)` pairs; `TRANSPORT_RE` is imported only by the gate and the tests; mutation (i) loosens the regex instead of removing an assert.
- v1.3: Plan-audit v3 fixes (codex): `TRANSPORT_RE` stem is dot-free (`^audit_[^.]+\.report\.md$`) so the grammars are disjoint by construction; `_collected_path` asserts it never derives a transport-shaped name (AC-1.6, mutations i/i′ → 17); the CLI does not import the regex — `_collected_path` and the tests do; collision candidates added to the AC-3.5a corpus.
- v1.2: Plan-audit v2 fixes (codex): transport grammar is `TRANSPORT_RE = ^audit_.*\.report\.md$`, single-sourced in the gate — hand-staged names in the field carry no `_cycle<N>` and a surface may contain `_`; conflict policy + readback on BOTH rungs (AC-2.6a/2.6b/2.12); force-direction mutants for the CLI and the verb (e′, f′, AC-4.3); shared two-direction corpus (AC-3.5a) and verdict preservation over the repo's audit docs (AC-3.7) for the Backward-compatibility invariant.
- v1.1: Plan-audit v1 fixes (agy p1 + codex): collector contract (`CollectConflict`, `out_path` optional, `--force`); transport refusal narrowed to the `audit_*_cycle<N>*.report.md` stem — `*.report.md` collides with Phase-7 `<feature>.report.md`; recipe halts on non-`OK` `COLLECT:`; AC-2.9 is an incident replay; AC-2.10/2.11/3.6 added; AC-6.3 is 11 bidirectional mutations; AC-4.1 pinned by a wrapper wiring test.
