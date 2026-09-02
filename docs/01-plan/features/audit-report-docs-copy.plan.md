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
  `surface`; `_copy_collected_report` stops clobbering differing content.
- New `h-mad/scripts/h_mad_collect_report.py` — CLI over `collect()`; `COLLECT:` contract.
- `h-mad/scripts/h_mad_audit_gate.py` — refuses `*.report.md` by basename.
- `h-mad/scripts/hmad-dispatch.sh` — `collect-report` verb delegating to the script.
- `h-mad/SKILL.md`, `h-mad/references/orchestration-mode.md` — codex-leg recipe, registry
  entry, verb table row, one sentence in step 9.
- Tests + `h-mad/tests/mutation-specs/collect_report.json`.
- User-visible behaviour: `audit-cycle` unchanged; a new verb; the gate now refuses one path
  shape it used to score.

## Goals
- The docs copy is derived, never typed — FR-1, FR-2.
- The codex leg has a mechanical collect step and a written recipe — FR-2, FR-4, FR-5.
- A `/tmp`-only report cannot gate — FR-3.
- A collected copy is byte-identical to its transport file and never silently overwrites a
  committed report — FR-2 (AC-2.1, 2.4, 2.5).
- Every guard is pinned RED and mutation-verified — FR-6.

## Requirements
- FR-1: surface-aware `_collected_path` — single derivation.
- FR-2: `h_mad_collect_report.py` with `COLLECT: OK|MISSING|CONFLICT path= delivered=`,
  exit 0 on any verdict / 2 on operational error.
- FR-3: gate refuses `*.report.md` with exactly `GATE: INVALID must=0 should=0`, exit 2.
- FR-4: `hmad-dispatch collect-report` wrapper verb.
- FR-5: SKILL.md codex-leg recipe + helper-registry entry + step-9 sentence.
- FR-6: tests for every AC; mutation spec with ≥ 4 named-test mutations; suite green.

## Implementation Strategy
Layers that change: the audit-cycle collector (python), the gate (python), the dispatch
wrapper (bash, delegation only), and the recipe (markdown). Patterns followed: the
verdict-token contract every h-mad gate uses (`h_mad_new_gate.py`'s three invariants — a
cannot-judge carries no counts, exit 0 on any verdict, docs pinned bidirectionally); the
`report-wait` delegation shape for the verb; one derivation function for the docs path.
Deliberately not touched: `h_mad_report_wait.py`, `h_mad_extract_report.py`, `exec`'s flags,
`audit-cycle`'s dispatch loop, `h_mad_cycle_counts.py` (its grammar is read, not changed).

Order of work (each a RED→GREEN task in the impl-plan): (1) `_collected_path` + `collect()`
surface threading, with the clobber fix; (2) the CLI; (3) the gate refusal; (4) the wrapper
verb; (5) docs + docs-tests; (6) mutation spec. The tracer (AC-2.9) runs after (2) against
the live HemaSuite corpus before any later task starts.

## Architecture Considerations
- **One copier.** `audit-cycle` already calls `collect()`; the CLI calls the same function.
  Two copiers would drift on the fallback ladder (report-file → `--out` → none) and on the
  clobber rule.
- **The transport-file grammar is a name, not a directory.** `*.report.md` is the staged
  name in step 6.6 and in `audit-cycle`'s stem; refusing by basename keeps the gate correct
  when a transport file is staged somewhere other than `/tmp` and when a docs path is passed
  from a `/tmp` cwd. Deliberately not `startswith("/tmp")` — pytest's `tmp_path` lives under
  `/tmp` on Linux.
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
| Nothing gates a `.report.md` today | `grep -rn 'audit_gate.*report\.md' h-mad/tests h-mad/SKILL.md h-mad/references` → 0; `audit_cycle.gate()` is only called on `collected_path` |
| `_gate_token` requires the exact INVALID shape | `GATE_RE = ^GATE:\s+(\S+)\s+must=(\d+)\s+should=(\d+)\s*$`; gate prints `GATE: INVALID must=0 should=0` |
| Surface grammar is one dot-free token, `p<i>` never co-occurs | `h_mad_cycle_counts.py:24-41` comment + `_VERSION_RE` |
| Transport and docs copies are byte-identical in the field | 21/21 overlapping `nlm-cli-version-pin` codex cycles `cmp -s` equal |
| `/tmp` decays | 31 codex reports at handover (2026-09-02 morning) → 21 the same day |

## Deliverables
| Deliverable | Type | Satisfies |
|---|---|---|
| `_collected_path(surface=None)` + `collect(surface=None)` | module change | FR-1 |
| `_copy_collected_report` conflict-safe | module change | FR-2 (AC-2.5) |
| `h_mad_collect_report.py` | CLI | FR-2 |
| gate transport refusal | module change | FR-3 |
| `hmad-dispatch collect-report` | CLI verb | FR-4 |
| SKILL.md codex-leg block, registry entry, step-9 sentence; orchestration-mode verb row | docs | FR-5 |
| `tests/test_h_mad_collect_report.py`, gate tests, docs tests | tests | FR-6 |
| `tests/mutation-specs/collect_report.json` | mutation spec | FR-6 |

## Risks and Mitigation
| Risk | Impact | Mitigation |
|---|---|---|
| This run's own codex audits lose their docs copy (old recipe live) | the defect recurs inside the feature fixing it | hand-collect + `cmp -s` before reading any codex GATE line, every cycle; after task 2, use the worktree CLI |
| `_collected_path` signature change breaks a caller | suite red | keyword-only `surface=None`; grep every caller (`audit_cycle.py` only) |
| `test_h_mad_audit_cycle_docs.py` slices SKILL.md by exact anchors | docs test red | insert outside `## Audit prompt assembly`→`## Putting …` and `6.6.`→`\n7.`; run that test after each edit |
| Mutation-spec tests refuse a spec without named failure tests | test red | write the spec and the tests in one task; run `--check-anchors` |
| Basename refusal catches a docs artifact named `.report.md` | false INVALID | corpus: none exist; documented in the grammar section |
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
- All 32 ACs in the spec pass automated tests (AC-2.9 is a recorded tracer).
- `MUTATION: ALL_CAUGHT` on `collect_report.json`.
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
