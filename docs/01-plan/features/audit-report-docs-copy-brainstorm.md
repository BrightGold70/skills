# Brainstorm: audit-report-docs-copy

## Executive Summary
The h-mad audit recipe delivers a codex-surface audit report to `/tmp` and never copies it
into the feature's docs store, so the copy is a hand `cp` that was forgotten on 7 of 8
consecutive cycles; put the copy at the one seam that already knows the
`(feature, phase, cycle, surface)` tuple — `h_mad_audit_cycle.collect()` — expose it as a
thin CLI for the codex leg, and make the gate refuse a transport file so a `/tmp`-only
report cannot score.

## Problem Statement
Under Orca's report-file transport an audit pass writes `/tmp/audit_<feature>_<phase>_cycle<N>[_<surface>].report.md`.
The agy leg runs inside `hmad-dispatch audit-cycle`, whose `collect()` copies the report to
`docs/<dir>/<feature>.<phase>.audit.v<N>.p<i>.md` automatically. The codex leg runs OUTSIDE
the verb (`h_mad_assemble_audit.py --report-file … + hmad-dispatch exec codex …`), the gate is
run on the `/tmp` path, and the docs copy `<feature>.<phase>.audit.v<N>.codex.md` is a manual
`cp` with no recipe step anywhere in SKILL.md or its references (the codex-leg recipe lives
only in two memory files). Measured on HemaSuite `nlm-cli-version-pin` (2026-09-02): plan
cycles 8, 10–15 had codex reports in `/tmp`, cited by the plan's Version History, absent from
docs and from `git log --all`; the consumer-side sync guard scored cycles 10/12/14 PASS on the
surviving agy leg. All seven were recovered from `/tmp` (HemaSuite `9e855dfa`) — `/tmp` is
wiped on reboot and had already shrunk from 31 to 21 files by the next morning, so the
recovery window was luck.

## Proposed Approach
1. **One derivation, one copier.** Extend `h_mad_audit_cycle._collected_path()` with an
   optional `surface` token: `.<surface>.md` when given, else the existing `.p<i>.md`.
   Thread it through `collect()`. The verb's behaviour is byte-identical when `surface` is
   omitted.
2. **A thin CLI over `collect()`** — `h_mad_collect_report.py --feature --phase --cycle
   --surface <s> --report <RP> [--out <out>] --project-root <root>` — printing
   `COLLECT: OK|MISSING|CONFLICT path=<docs path> delivered=report-file|out` (+ `[H-MAD]`
   marker), exit 0 on `OK`, non-zero on `MISSING`/`CONFLICT`. It:
   - validates `--surface` against the single dot-free token grammar
     (`h_mad_cycle_counts._VERSION_RE`) and refuses `p<i>` (reserved for pass index);
   - is idempotent: existing docs file with identical bytes → `OK`, no write; existing but
     different → `CONFLICT`, no write (fixes `_copy_collected_report`'s unlink-then-write clobber);
   - asserts byte-identity (`filecmp`/bytes compare) for `delivered=report-file`;
   - handles `--report` resolving to the derived docs path itself (the workaround the live
     `pin-agents-tail-banner` run is already using — `.audit.v16-19.codex.md.done` litter in
     docs/): skip the copy, require non-empty + `.done`, remove the marker.
3. **Gate teeth.** `h_mad_audit_gate.py` refuses a basename ending `.report.md` — the
   transport-file grammar — printing exactly `GATE: INVALID must=0 should=0` (the token shape
   `_gate_token` requires) with the reason on the `[H-MAD]` line, exit 2. `audit_cycle.gate()`
   already maps rc 2 → `UNVERIFIED`. No test or doc gates a `.report.md` today.
4. **Recipe.** SKILL.md gets the codex-leg block it has never had, beside the `audit-cycle`
   docs: assemble `--report-file` → `exec codex` → `collect-report --surface codex` → gate the
   PRINTED docs path, never `$RP`. Helper-registry entry; `test_h_mad_audit_cycle_docs.py`
   anchors preserved.
5. **Pinned both directions**: RED — report and out both absent → `MISSING`, no docs file,
   non-zero; gate on `x.report.md` → `INVALID` exit 2; differing existing → `CONFLICT`;
   surface `p2` refused. GREEN — docs copy `cmp -s`-identical to `$RP`; existing-identical is a
   no-op `OK`. Mutation spec row + named failure test (the audit-cycle spec tests enforce both).

Why this over alternatives: `collect()` is the only code that already knows the whole tuple
and the fallback ladder (report-file → `--out` extract → none). A second copier drifts; a flag
on `exec` cannot work because `exec` has no `--report-file` and knows no tuple.

## Alternatives Considered
- **Brief candidate (b): `hmad-dispatch exec --report-file … --persist-to <docs>`** — rejected:
  `exec` has no `--report-file` flag (the path enters via `h_mad_assemble_audit.py`), and
  `exec` does not know `(feature, phase, cycle, surface)`, so the docs path would be hand-typed
  — the failure being fixed.
- **Brief candidate (c): `h_mad_report_wait.py` returns only after the docs copy exists** —
  rejected: `report_wait` is the marker poller used by every caller including `exec --out`
  polling; giving it a docs-path side effect couples a transport primitive to the audit
  filename grammar and changes every existing caller.
- **Teach `audit-cycle` a `--agents agy,codex` pass surface** — deferred (operator decision
  2026-09-02): correct long-term, but it pulls in the bash verb, codex sandbox rules for
  audits (`read-only` blocks the report-file write), and three 1.5–1.9k-line test files. The
  collect CLI is the seam it would call anyway, so it is not wasted.
- **Gate warns instead of refusing** — rejected (operator decision): the seven missed cycles
  would all have scored with a warning nobody read.
- **Rely on the consumer-side guard** (HemaSuite `_absent_audit_citations`) — rejected as the
  only line: it fires at test time, after the gate has already been read, and only in repos
  that carry it.

## Risks & Mitigations
| Risk | Likelihood | Mitigation |
|---|---|---|
| The live run in the main checkout reads `~/.claude/skills/h-mad` → OLD recipe; this run's own codex passes are exposed to the defect | H | For every codex pass in this run, run the collect step by hand and verify the docs copy before reading any GATE line; edit only in this worktree |
| `_collected_path` signature change breaks an existing caller | L | `surface=None` default; every existing 5-kwarg call unchanged; suite run |
| Gate refusal by basename catches a legitimate docs file named `*.report.md` | L | corpus scan of 1120 audit files shows the docs grammar is `.audit.v<N>[.tok].md`; `.report.md` is only ever the staged transport name |
| `test_h_mad_audit_cycle_docs.py` slices SKILL.md by exact headings and `6.6.`→`\n7.` | M | insert the codex-leg block outside those slices; run that test after every SKILL.md edit |
| Mutation-spec tests refuse a new guard without a spec row + named failure test | M | add the row and the test in the same task |
| `--out` extract text is by construction not byte-identical to any `/tmp` file | certain | byte-identity asserted only for `delivered=report-file`; token carries `delivered=` so tests know which case they assert |

## Dependencies
None external. Internal: `h_mad_audit_cycle.py` (collect seam), `h_mad_audit_gate.py`,
`h_mad_cycle_counts._VERSION_RE` (surface grammar), `h_mad_report_wait.py` (unchanged, called
by `collect()`), SKILL.md + helper registry, `tests/mutation-specs/`.

## Open Questions
- Should `audit-cycle` itself call the new CLI for its `p<i>` passes (dogfooding the one
  copier) or keep calling `collect()` directly? Either satisfies "one copier"; decide in design.
- Should `COLLECT: MISSING` exit 1 (verdict, like `report-wait`'s timeout) or 0 with a token
  (audit-gate signal discipline says a verdict exits 0)? Design must pick one and pin it.
- Wrapper verb `hmad-dispatch collect-report` delegating to the script, or script-only?

## Version History
- v1.0: Initial brainstorm draft.
