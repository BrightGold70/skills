# Plan: fanout-integrity-and-defects

## Executive Summary

Guard `worktree-rm` at the point work becomes unrecoverable, give `worktree-create` a task-id so the
orchestration verbs work on both dispatch paths, and correct the two record-level defects (epoch
`started_ts`, contentless `DONE_WITH_CONCERNS`) that make a run's own evidence untrustworthy.

## Overview

Wave 3 ran the Phase-5 worktree fanout live for the first time and it worked — but only because the
orchestrator noticed, by hand, that both workers had left their output uncommitted. Run exactly as
documented, the merge gate would have merged an up-to-date branch, found no unmerged paths,
auto-recorded a clean merge, and `worktree-rm` would then have destroyed the only copy of the work,
reporting success throughout. Wave 4's payload is designed to be fanned out over that same
machinery, so this feature repairs the instrument first. J8 and J10, already folded into Wave 4 and
each diagnosed to a line, ride along because they are the same category: defects that corrupt what a
run records about itself.

## Scope

In scope: the `worktree-rm` and `worktree-create` verbs in `hmad-dispatch.sh`, the `started_ts`
default in `h_mad_state_write.py`, the `DONE_WITH_CONCERNS` contract in `h_mad_extract_verdict.py`,
their tests, and the prose in `SKILL.md`, `references/orchestration-mode.md` and
`references/codex-implementer-prompt.md`.

User-visible behavior: `worktree-rm` gains two refusal modes with distinct reasons and an existing
`--force` escape; `worktree-create` emits an additional identifier; a feature created without
`--started-ts` gets a real timestamp; a contentless `DONE_WITH_CONCERNS` becomes exit 2 instead of a
verdict. No verb is added or removed.

## Goals

- Make destroying unrecovered work impossible without an explicit override — FR-1, FR-2, FR-3
- Preserve every existing `worktree-rm` behaviour where the guard does not fire — FR-4
- Remove the dispatch-path fork so `await` and `gate-create` work uniformly — FR-5
- Stop stamping new feature records with a sentinel indistinguishable from real data — FR-6
- Stop a verdict declaring doubt without stating it from passing as a verdict — FR-7, FR-8
- Leave the documentation describing the machinery that exists — FR-9

## Requirements

- FR-1: `worktree-rm` refuses a worktree with uncommitted changes
- FR-2: `worktree-rm` refuses a worktree holding unmerged commits
- FR-3: `--force` overrides both guards and announces itself
- FR-4: unguarded paths behave exactly as before
- FR-5: `worktree-create` surfaces a task-id
- FR-6: a new feature record is stamped with the current time
- FR-7: a contentless `DONE_WITH_CONCERNS` is an error, not a verdict
- FR-8: the concern obligation is stated to the implementer
- FR-9: documentation matches the shipped machinery

## Implementation Strategy

Three files change, each for one reason, and they do not interact:

- `hmad-dispatch.sh` — FR-1 to FR-5. New private helpers plus edits to `_cmd_worktree_rm` and
  `_cmd_worktree_create`. No new script: the wrapper already owns substrate detection and Orca
  invocation, and a separate file would add a cross-file contract for a guard that is a dozen lines.
- `h_mad_state_write.py` — FR-6. One expression.
- `h_mad_extract_verdict.py` — FR-7. A scoped validation applied to one value of one key.

**Guard the irreversible step, not the instruction.** The filed fix direction for J15 was to tell
the fanout worker to commit. Both Wave-3 workers had already been told to self-review and neither
committed, so an instruction a worker can ignore leaves the loss reachable. The guard therefore sits
on `worktree-rm`, which is where the work actually becomes unrecoverable. Nothing has to be read for
the data to be safe — the same reasoning that made Wave 3's send-refusal effective where Wave 2's
mandated read was not.

**Refuse only on positive evidence.** `_orca_handle_live` returns three values, and its "unknown"
case deliberately does not block, because a pin must keep working when the listing cannot be read.
The `worktree-rm` guard inherits that stance: an unresolvable selector is not evidence that a
worktree is safe to destroy, but neither is it evidence of work, and the existing suite pins this
(`test_worktree_rm_argv_force_and_failure` removes the bare name `wt-7`, which resolves to no
directory). Only a resolvable worktree that demonstrably holds work refuses.

**`--force` short-circuits before any lookup.** The same existing test asserts the forced path
produces exactly one Orca call. The guard must therefore be skipped, not merely overridden after
running.

Deliberately untouched: the verb set, `worktree-rm`'s existing failure marker and exit-code
passthrough, the cmux refusal, teardown idempotence, and every other verb.

## Architecture Considerations

- **Selector resolution is the hard part, not the guard.** Selectors arrive as `<repoId>::<path>`, a
  bare name, an id, or `active`. Splitting on `::` handles the shape Wave 3 produced and silently
  mishandles the rest. The design must state how a selector becomes a path and what happens when it
  cannot — and per the spec's compatibility constraint, "cannot" must not mean "refuse".
- **The comparison ref for FR-2 is not recorded.** h-mad does not stamp a base ref on a worktree it
  creates. Options are to derive it at removal time, require it as an argument, or ask whether the
  branch's commits exist anywhere else. Each has a different failure mode; the design must choose
  one and justify it, and AC-2.4 already concedes that an undeterminable ref must not refuse.
- **FR-5 changes an output contract.** `_cmd_worktree_create` currently prints one line, the
  selector, via `_orca_json`. Anything that parses it whole-line breaks if a second value is
  appended to the same line. Backward compatibility is a base invariant, so the design must pick a
  shape — additional line, prefixed lines, or a flag — and pin the current behaviour with a test
  before changing it.
- **FR-7 needs the report body, which the pure function does not take.** `extract_verdict(scrape,
  key, allowed)` returns a value from a line. Judging "was a concern stated" requires the surrounding
  text. Either the function's contract widens or the CLI applies a second check after extraction;
  the latter keeps the function honest to its name and keeps the new rule out of the `VERDICT:` and
  `ASSESSMENT:` paths by construction.
- **These four fixes must not be one commit.** They touch unrelated failure modes; a regression in
  any one should be bisectable to it.

## Deliverables

| Deliverable | Type | Satisfies |
|---|---|---|
| Uncommitted-changes guard on `worktree-rm` | CLI behavior | FR-1 |
| Unmerged-commits guard on `worktree-rm` | CLI behavior | FR-2 |
| `--force` short-circuit + bypass notice | CLI behavior | FR-3 |
| Selector→path resolution helper | internal function | FR-1, FR-2, FR-4 |
| Preserved passthrough, cmux refusal, idempotent teardown | regression tests | FR-4 |
| Task registration + id surfacing in `worktree-create` | CLI behavior | FR-5 |
| `now(UTC)` default for `started_ts` | script change | FR-6 |
| Contentless-concern rejection | script change | FR-7 |
| Concern obligation in the Codex template | docs | FR-8 |
| Guard + unified-path documentation | docs | FR-9 |

## Risks and Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| The guard refuses on an unresolvable selector and breaks teardown | High — every fanout run ends unable to clean up | Spec constraint: unresolvable never refuses. Pin with an explicit AC (AC-4.1) and keep the existing bare-name test unchanged |
| `--force` runs a lookup and breaks the exact-capture assertion | Medium — an existing test fails | Short-circuit before resolution; AC-3.2 asserts the capture byte-for-byte |
| FR-2's comparison ref is guessed wrong and refuses legitimate teardown | Medium | AC-2.3 requires the discriminating negative case; AC-2.4 requires an undeterminable ref not to refuse |
| Appending a task-id breaks a caller parsing `worktree-create` stdout | Medium | Pin current output with a test first, then choose a shape that leaves the selector obtainable as-is (AC-5.3) |
| Task registration failure blocks worktree creation | Medium — a fanout cannot start | AC-5.4 makes the task-id an enrichment, never a gate |
| The concern check leaks into `VERDICT:`/`ASSESSMENT:` | Medium — an architectural review starts failing spuriously | Scope by key *and* value; AC-7.4 asserts the other contracts are unaffected |
| Guards written so they pass vacuously | Medium — ships an unenforced feature behind green tests | Every guard carries a negative-case AC (AC-1.4, AC-2.3, AC-4.1, AC-7.4); verify each by mutation before accepting it |
| J8's fix makes an existing test asserting the epoch fail | Low | Expected and correct — such a test encodes the defect; update it and say so |

## Convention Prerequisites

- Feature branch `feature/193-fanout-integrity-and-defects` cut at Phase 5c from current `main`.
- **Phase 5 runs serially.** The fanout is the subject of the repair; using it here would be the
  same category error as auditing the assembler with the assembler.
- Base Axis B: audit-gate signal discipline, single-source contract, backward compatibility,
  operator-override preservation, marker discipline.
- Project Axis B: skill self-containment, skill manifest integrity.
- Tests run under `/opt/anaconda3/bin/python3` (jsonschema).
- Dispatches now run against Wave 3's enforced preflight — `send` refuses without a valid receipt.

## Success Criteria

- All 34 ACs in the spec pass automated tests
- Full suite green with zero regressions against the 550-test baseline
- Every existing `worktree-rm` and `worktree-create` assertion still passes, or its change is
  justified in the design
- Each guard demonstrated to *discriminate* by mutation, not merely to pass
- A worktree holding uncommitted work is demonstrably not removable without `--force`, shown against
  a real worktree rather than only a stub
- Phase 6a-prime returns `READY_TO_MERGE`

## Out-of-Scope (confirmed from spec)

- Wave 4's candidate batch — the two `invariants.base.md` discipline rules, the
  `file-issue-then-fix-under-TDD` tooling, the staged-prompt repair sweep, the stub-harness probe,
  and the two `SKILL.md` prose notes
- Rewriting historical telemetry rows
- Judging whether a stated concern is a good concern
- `stablyai/orca#9870`

## Next Steps

Plan v1.0 approval, then the Phase-3 audit cycle: assemble via `h_mad_assemble_audit.py --phase
plan`, assert `ASSEMBLE: PASS`, dispatch to agy, run `h_mad_audit_gate.py`, and cycle until both
must-fix and should-fix reach zero.

## Version History
- v1.0: Initial plan draft.
