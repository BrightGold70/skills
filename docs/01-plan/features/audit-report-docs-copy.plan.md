# Plan: audit-report-docs-copy

## Executive Summary
Move the audit report's docs copy from a remembered `cp` to the collector that already knows
`(feature, phase, cycle, surface)`, expose that collector to the codex leg as a verb, and make
the gate refuse a transport file — so an audit that was never persisted cannot score.

## Overview
Under Orca's report-file transport an audit pass lands at
`/tmp/audit_<feature>_<phase>_cycle<N>[_<surface>].report.md`. The agy leg runs inside
`hmad-dispatch audit-cycle`, whose `collect()` copies to `docs/…audit.v<N>.p<i>.md`; the codex
leg runs outside the verb and its docs copy `…audit.v<N>.codex.md` is a hand `cp` with no
recipe step. Seven of eight consecutive plan cycles on HemaSuite `nlm-cli-version-pin` skipped
it; the reports survived only because `/tmp` had not been wiped yet. This plan closes the
recipe half (the consumer-side guard already landed in HemaSuite `d1e73d53`).

## Scope
- `h-mad/scripts/h_mad_audit_cycle.py` — `_collected_path()` / `collect()` gain an optional
  `surface`; `_copy_collected_report` / `_write_collected_report` gain `overwrite` (default
  `True`, so `audit-cycle`'s re-dispatch semantics are unchanged; the CLI passes `False`
  unless `--force`).
- New `h-mad/scripts/h_mad_collect_report.py` — CLI over `collect()`; `COLLECT:` contract.
- `h-mad/scripts/h_mad_audit_gate.py` — defines `TRANSPORT_RE = ^audit_[^.]+\.report\.md$`
  (the one transport grammar: `audit_` prefix, dot-free stem, `.report.md` suffix) and
  refuses a basename matching it (NOT bare `*.report.md`: Phase-7 reports are
  `<feature>.report.md`). Every refusal emits `[H-MAD] <feature> gate INVALID (transport
  file …)`.
- `h-mad/scripts/hmad-dispatch.sh` — `collect-report` verb delegating to the script.
- `h-mad/SKILL.md`, `h-mad/references/orchestration-mode.md` — codex-leg recipe, registry
  entry, verb table row, one sentence in step 9.
- Tests + `h-mad/tests/mutation-specs/collect_report.json`.
- User-visible behaviour: `audit-cycle` unchanged; a new verb; the gate now refuses one path
  shape it used to score.

## Goals
- The docs copy is derived, never typed — FR-1, FR-2.
- A report that was not collected (`COLLECT: MISSING|CONFLICT`) is never gated — FR-2, FR-5.
- The codex leg has a mechanical collect step and a written recipe — FR-2, FR-4, FR-5.
- A `/tmp`-only report cannot gate — FR-3.
- A collected copy is byte-identical to its transport file and never silently overwrites a
  committed report — FR-2 (AC-2.1, 2.4, 2.5).
- Every guard is pinned RED and mutation-verified — FR-6.

## Requirements
- FR-1: surface-aware `_collected_path` — single derivation.
- FR-2: `h_mad_collect_report.py` with `COLLECT: OK|MISSING|CONFLICT path=<docs path>
  delivered=report-file|out|none [forced=1]` +
  `[H-MAD] <feature> collect <verdict>` on every verdict and `[H-MAD] … collect
  readback_failed` on a readback disagreement (Marker discipline), exit 0 on any verdict /
  2 on operational error; `--force` to overwrite a differing docs copy; internal contract
  `CollectConflict` + optional `PassSpec.out_path`.
- FR-3: gate refuses `TRANSPORT_RE` (`audit_` prefix, dot-free stem, `.report.md` suffix,
  single-sourced in the gate; imported only by the tests — not by the CLI, not by
  `_collected_path`) with exactly `GATE: INVALID must=0 should=0` + the `[H-MAD] …
  gate INVALID (transport file …)` marker, exit 2; `<feature>.report.md` (Phase 7) still
  scores; verdict preserved for every existing audit doc (AC-3.7, Backward compatibility).
- FR-1 (AC-1.6): disjointness of the two grammars is a property test over adversarial
  `(feature, surface)` pairs, not a production assert (an unreachable check cannot be
  mutation-tested).
- FR-4: `hmad-dispatch collect-report` wrapper verb.
- FR-5: SKILL.md codex-leg recipe (halt `<phase>:report_not_collected` emits its `[H-MAD]`
  marker, per Marker discipline) + helper-registry entry + step-9 sentence.
- FR-6: tests for every AC including the incident replay (AC-2.9), operational errors
  (AC-2.10) and readback (AC-2.12); mutation spec with 17 named-test mutations — every new
  connection dropped AND forced on its fall-through path, plus the grammar-disjointness
  property (regex loosened / docs pattern de-dotted); wrapper wiring test for the verb in both directions (AC-4.1, AC-4.3);
  suite green.

## Implementation Strategy
Layers that change: the audit-cycle collector (python), the gate (python), the dispatch
wrapper (bash, delegation only), and the recipe (markdown). Patterns followed: the
verdict-token contract every h-mad gate uses (`h_mad_new_gate.py`'s three invariants — a
cannot-judge carries no counts, exit 0 on any verdict, docs pinned bidirectionally); the
`report-wait` delegation shape for the verb; one derivation function for the docs path.
Deliberately not touched: `h_mad_report_wait.py`, `h_mad_extract_report.py`, `exec`'s flags,
`audit-cycle`'s dispatch loop, `h_mad_cycle_counts.py` (its grammar is read, not changed).

Order of work (each a RED→GREEN task in the impl-plan): (1) `_collected_path` + `collect()`
surface threading and the `overwrite` keyword on both writers; (2) the gate refusal
(`TRANSPORT_RE` + the AC-1.6 / AC-3.5a grammar tests); (3) the CLI; **then the
AC-2.9 tracer** — it needs (2)'s refusal for its step (i) and (3)'s CLI for step (ii), so it
cannot run earlier — against a real `/tmp` survivor copied into a scratch project root;
(4) the wrapper verb; (5) docs + docs-tests; (6) mutation spec.

## Architecture Considerations
- **One copier.** `audit-cycle` already calls `collect()`; the CLI calls the same function.
  Two copiers would drift on the fallback ladder (report-file → `--out` → none) and on the
  clobber rule.
- **The transport-file grammar is a name, not a directory — prefix `audit_` plus suffix
  `.report.md`, defined once.** The cycle-1 rule (bare `*.report.md`) was wrong because Phase-7
  reports are `<feature>.report.md`; the cycle-2 rule (a `_cycle<N>[_tok]` stem) was wrong
  because the field hand-stages transport files without `_cycle<N>` and a surface token may
  carry `_`; the cycle-3 rule (`^audit_.*\.report\.md$`) still overlapped a derivable docs
  name (`feature="audit_f"`, `surface="report"` → `audit_f.plan.audit.v8.report.md`). The
  v1.3 grammar requires a **dot-free stem**: every docs audit name carries `.audit.v<N>`,
  every transport name observed has no dot before `.report.md`, so the sets are disjoint by
  construction. That property is pinned by a test over adversarial `(feature, surface)`
  pairs (AC-1.6) rather than by a production assert: the v1.3 draft put an assert in
  `_collected_path`, and cycle 6 showed it could never fire under the dot rule — an
  unreachable guard cannot be mutation-tested and would have shipped as the appearance of
  coverage. All corrections came from executing the candidate regex over the real `/tmp`
  and `docs/` listings (Assumption table). `TRANSPORT_RE` lives in `h_mad_audit_gate.py`;
  only the tests import it (the CLI and `_collected_path` have no use for it), and one
  two-direction corpus fixture is asserted against it and against `_VERSION_RE` so the two
  grammars cannot drift apart silently. Deliberately not
  `startswith("/tmp")` — pytest's `tmp_path` lives under `/tmp` on Linux.
- **Backward compatibility is measured, not argued.** The invariant preserves the PASS of
  every audit DOC. A transport path is not an audit doc — no recipe, test or doc ever gated
  one (grep: 0) — and its bytes keep their verdict at the docs path. AC-3.7 runs
  `is_transport_path()` over every `*.audit.v*.md` in this repo's `docs/` (live + archive)
  and requires False, so the change is provably verdict-neutral for the existing corpus.
  The refusal itself is an operator decision (2026-09-02: "refuse, not warn").
- **Conflict policy and readback cover both delivery rungs.** `_copy_collected_report`
  (report-file) and `_write_collected_report` (`--out` extract) both take `overwrite` and
  both re-read what they wrote; the docs-path marker removal re-checks `exists()`. A
  readback that disagrees is an operational failure (exit 2, no `COLLECT:` line).
- **A non-`OK` collect never reaches the gate.** `MISSING` and `CONFLICT` exit 0 (verdicts),
  so the recipe must read the token: anything but `OK` halts `<phase>:report_not_collected`
  and the gate is not invoked — otherwise a `CONFLICT` (preserved, DIFFERENT docs bytes)
  followed by "gate the printed path" scores the stale report. `audit-cycle` is unaffected:
  it overwrites its own per-pass file on purpose (a re-dispatched cycle replaces the prior
  attempt), so `overwrite=True` stays its default and `CollectConflict` is raised only when
  the CLI asks for `overwrite=False`.
- **Signal discipline.** `COLLECT: MISSING` and `CONFLICT` are verdicts, so they exit 0;
  the teeth are in the gate (FR-3), not in the collector's exit code. `audit_cycle.gate()`
  already maps rc 2 → `INVALID` → `UNVERIFIED`, so no consumer gains a new word.
- **Docs-path-as-RP is a real workaround in the field.** The live `pin-agents-tail-banner`
  run points `$RP` at the docs file directly, leaving `.done` litter in `docs/`. The
  collector must treat that as already-collected (AC-2.8) rather than as a self-copy.
- **The live run reads the OLD recipe.** `~/.claude/skills/h-mad` resolves to the main
  checkout; this worktree's edits reach it only at merge. This feature's own codex audit
  passes must therefore run the collect step by hand until the CLI exists, and via the CLI
  from this worktree's path afterwards.

## Assumption verification (evidence, 2026-09-02)
| Assumption | Evidence |
|---|---|
| The agy leg is already persisted by the verb | 23 `nlm-cli-version-pin.plan.audit.v*.p1.md` in HemaSuite docs; `h_mad_audit_cycle.py::_copy_collected_report` |
| The codex leg has no recipe step | `grep -c 'exec codex.*audit\|\.codex\.md' h-mad/SKILL.md h-mad/references/*.md` → 0; recipe found only in two memory files |
| `exec` has no `--report-file` | `_cmd_exec` option loop (`hmad-dispatch.sh:2493-2499`): `--cd --model --out --log --timeout --sandbox --effort` only |
| Nothing gates a transport file today | `grep -rn 'audit_gate.*report\.md' h-mad/tests h-mad/SKILL.md h-mad/references` → 0; `audit_cycle.gate()` is only called on `collected_path` |
| `*.report.md` is NOT transport-only | `ls docs/04-report/features/*.report.md` → 7 Phase-7 reports (e.g. `gate-blindness-hardening.report.md`); `docs/archive/2026-08/audit-cycle-verb/audit-cycle-verb.report.md` — a suffix rule would refuse them, hence prefix+suffix |
| Re-dispatching a cycle overwrites its collected file | `_copy_collected_report`: `unlink(missing_ok=True)` then write; the low-evidence remedy is "re-dispatch that pass" at the SAME cycle number |
| `_gate_token` requires the exact INVALID shape | `GATE_RE = ^GATE:\s+(\S+)\s+must=(\d+)\s+should=(\d+)\s*$`; gate prints `GATE: INVALID must=0 should=0` |
| Surface grammar is one dot-free token, `p<i>` never co-occurs; `_` is legal in a surface | executed `_VERSION_RE.search` (2026-09-02): `f.plan.audit.v8.p1.md`→True, `….v8.codex.md`→True, `….v8.codex_draft.md`→**True**, `….v8.codex.draft.md`→False, `f.report.md`→False, `audit_f_plan_cycle8_codex.report.md`→False |
| Transport names in the field always carry `audit_` + `.report.md`, NOT always `_cycle<N>` | `ls /tmp \| grep -E '^audit_.*\.report\.md$'` (2026-09-02): 144 `_p1`, 129 `_p2`, 36 `_codex`, 14 `_agy`, 1 `_agy_p2`, and 7 hand-staged `audit_hnag_c28_agy.report.md` / `audit_hnag_implplan_c11.report.md` …; executed candidate regexes: the `_cycle<N>` stem matched 0 of those 7 and missed `_codex_draft`; `^audit_.*\.report\.md$` matched all |
| No docs artifact starts with `audit_` | `find docs -name 'audit_*'` → 0 (this repo); same under HemaSuite `docs/` → 0; all 7 `docs/04-report/features/*.report.md` basenames match `^[a-z0-9-]+\.report\.md$` |
| Transport stems are dot-free; docs names always carry `.audit.v<N>` | executed 2026-09-02: `ls /tmp \| grep -E '^audit_.*\.report\.md$' \| grep -E '^audit_[^.]*\..*\.report\.md$'` → 0 of 331; `^audit_[^.]+\.report\.md$` on `audit_f.plan.audit.v8.report.md` → False while `_VERSION_RE` → True; on `audit_hnag_c28_agy.report.md` → True / False; on `f.plan.audit.v8.p1.md` → False / True |
| The `--out` rung also clobbers | `grep -n unlink h_mad_audit_cycle.py` → lines 92 (`_copy_collected_report`) AND 169 (`_write_collected_report`) |
| Unknown verb is a fall-through, not an exec | `hmad-dispatch collect-reportx` → `hmad-dispatch: unknown verb 'collect-reportx'` |
| Transport and docs copies are byte-identical in the field | 21/21 overlapping `nlm-cli-version-pin` codex cycles `cmp -s` equal |
| `/tmp` decays | 31 codex reports at handover (2026-09-02 morning) → 21 the same day |

## Deliverables
| Deliverable | Type | Satisfies |
|---|---|---|
| `_collected_path(surface=None)` + `collect(surface=None)` | module change | FR-1 |
| `_copy_collected_report` conflict-safe | module change | FR-2 (AC-2.5) |
| `h_mad_collect_report.py` | CLI | FR-2 |
| `TRANSPORT_RE` + `is_transport_path()` + refusal in the gate | module change | FR-3 |
| `hmad-dispatch collect-report` | CLI verb | FR-4 |
| SKILL.md codex-leg block, registry entry, step-9 sentence; orchestration-mode verb row | docs | FR-5 |
| `tests/test_h_mad_collect_report.py` (incl. incident replay AC-2.9, operational errors AC-2.10), gate tests (AC-3.1–3.6), docs tests (AC-5.1–5.4) | tests | FR-6 |
| wrapper wiring test: `collect-report` verb → script (severed route fails) | test | FR-4, FR-6 |
| `tests/mutation-specs/collect_report.json` — 17 mutations, drop/force pairs per connection incl. fall-through paths and the grammar-disjointness property | mutation spec | FR-6 |
| two-direction name corpus fixture asserted against `TRANSPORT_RE` and `_VERSION_RE`; verdict-preservation sweep over `docs/**/*.audit.v*.md` | tests | FR-3 (AC-3.5a, 3.7) |

## Risks and Mitigation
| Risk | Impact | Mitigation |
|---|---|---|
| This run's own codex audits lose their docs copy (old recipe live) | the defect recurs inside the feature fixing it | hand-collect + `cmp -s` before reading any codex GATE line, every cycle; after task 2, use the worktree CLI |
| `_collected_path` signature change breaks a caller | suite red | keyword-only `surface=None`; grep every caller (`audit_cycle.py` only) |
| `test_h_mad_audit_cycle_docs.py` slices SKILL.md by exact anchors | docs test red | insert outside `## Audit prompt assembly`→`## Putting …` and `6.6.`→`\n7.`; run that test after each edit |
| Mutation-spec tests refuse a spec without named failure tests | test red | each task's RED names the tests its mutations will cite; task 6 assembles the spec from them and runs `--check-anchors` |
| Tracer scheduled before the code it exercises exists | replay cannot pass at its scheduled point | tracer is ordered after tasks (1)–(3); the impl-plan carries it as its own checkpoint between task 3 and task 4 |
| Transport grammar drifts from what gets staged (a future naming change silently un-guards) | transport files score again | one grammar (`TRANSPORT_RE`), one corpus fixture in both directions, the wrapper's staged `--report-file` asserted against it under the stub harness, the 6.6 literal asserted too (AC-3.5a) |
| `CONFLICT` followed by a hand-run gate scores stale bytes | wrong verdict on a preserved old report | recipe halt on non-`OK` (AC-5.3 docs test); `--force` is the only overwrite path |
| `--out` extract is not byte-identical to any `/tmp` file | a byte-identity test would fail | assert identity only for `delivered=report-file`; token carries `delivered=` |
| bkit heredoc-in-substitution hook denies the commit idiom | commit refused | `git commit -F <file>` |

## Convention Prerequisites
- Work only in worktree `/Users/kimhawk/orca/workspaces/skills/audit-report-docs-copy`
  (branch `BrightGold70/audit-report-docs-copy`); never edit `/Users/kimhawk/orca/skills`.
- Feature claimed in this worktree's `docs/.bkit-memory.json`.
- Codex authors Phase 5 via `hmad-dispatch exec codex` (TDD gate armed at 5a).
- Run the suite from the repo root: `python3 -m pytest h-mad/tests -q`.
- Mutation anchors checked with `h_mad_mutation_harness.py --check-anchors` before push
  (pre-push hook sweeps them).

## Success Criteria
- All 40 unique ACs in the spec pass automated tests (AC-2.9's hand replay is recorded, its suite half asserted).
- `MUTATION: ALL_CAUGHT` on `collect_report.json` (17 mutations, every connection dropped
  AND forced, fall-through paths included).
- Incident replay (AC-2.9) passes in the suite and once by hand against a real `/tmp`
  survivor in a scratch root, transcript in Version History.
- `h-mad/tests` suite green from this worktree; `audit-cycle` output byte-identical on the
  existing stub suite.
- The codex leg of THIS feature's Phase 4/5b audits is collected by the new verb and each
  docs copy is `cmp -s`-identical to its `/tmp` report.

## Out-of-Scope (confirmed from spec)
- `audit-cycle --agents` (codex as an in-verb pass).
- Changes to `h_mad_report_wait.py`, `h_mad_extract_report.py`, `exec` flags.
- Deleting `/tmp` transport files after collection (only the AC-2.8 docs-path marker).
- Back-filling historical surface-named audits; `h_mad_cycle_counts` changes.

## Next Steps
Operator approves v1.0 → Phase 3 audit cycle (agy via `audit-cycle --passes 1` + codex via
assemble/exec/hand-collect) until `must=0 should=0` on the union → Phase 4 design.

## Version History
- v1.0: Initial plan draft.
- v1.1: Audit v1 fixes from audit-report-docs-copy.plan.audit.v1.p1.md (agy) + .v1.codex.md — verb wiring test in Deliverables; transport refusal is the audit_*_cycle<N> STEM, not *.report.md (Phase-7 reports share the suffix — corpus claim corrected); recipe halts on non-OK COLLECT; 11 bidirectional mutations; incident-replay tracer; collector contract (CollectConflict, optional out_path, --force).
- v1.2: Audit v2 fixes from audit-report-docs-copy.plan.audit.v2.codex.md (agy v2 clean) — transport grammar single-sourced as TRANSPORT_RE (prefix+suffix; hand-staged field names have no _cycle<N>, surfaces may carry _); conflict policy + readback on both rungs; force mutants for CLI/verb fall-through; two-direction corpus + verdict-preservation sweep for Backward compatibility; Assumption rows now cite executed probe output; AC census by command.
- v1.3: Audit v3 fixes from .plan.audit.v3.p1.md (agy: [H-MAD] markers named in Requirements) + .v3.codex.md (TRANSPORT_RE stem is dot-free so the grammars are disjoint by construction; _collected_path asserts it, AC-1.6, 17 mutations; the CLI does not import the regex).
- v1.4: Audit v4 fixes from .plan.audit.v4.codex.md (agy v4 clean, low-evidence) — work order reordered so the gate refusal (task 2) precedes the CLI (task 3) and the AC-2.9 tracer runs after task 3, the first point at which both its steps can pass.
- v1.5: Audit v6 fixes from .plan.audit.v6.codex.md (agy v6 clean, low-evidence) — AC-1.6 is a grammar-disjointness property test, not an unreachable production assert; forced=1 in the FR-2 contract line; Scope wording distinguishes the CLI's no-clobber default from audit-cycle's unchanged overwrite.
