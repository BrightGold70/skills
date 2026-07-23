# Report: preflight-read-enforcement

## Executive Summary

The Wave-2 `PREFLIGHT:` token is now machinery rather than protocol: `hmad-dispatch env` writes a
fingerprinted receipt on PASS and `send` refuses to dispatch without a fresh, matching one — closing
the FR-4/FR-5 carry and the previously unguarded agent-conflict case.

## Summary

Built as the Wave-3 dogfood payload of `docs/01-plan/h-mad-remediation-sequence.md`. Six shell
helpers were added to `hmad-dispatch.sh` and wired into two call sites; no new script, no new
component. The load-bearing decision was to anchor the receipt path to the **pin file's directory**
rather than a hardcoded `.h-mad/`, which made the existing test harness isolate receipts for free
(the J7 fix already assigns each invocation a unique absent pin path) and so removed any need for a
suite-wide `HMAD_SKIP_PREFLIGHT` default — a default that would have made every enforcement
assertion in the feature vacuous. Tasks 1 and 2 were implemented by two Codex workers in parallel
Orca worktrees and merged through the winner-merge gate; Tasks 3 and 4 ran serially. Final state:
100% match rate, 550/550 tests, `READY_TO_MERGE`.

## Metrics

| Metric | Value |
|---|---|
| Plan audit cycles | 1 |
| Design audit cycles | 1 |
| Impl-plan audit cycles | 2 |
| Iterate cycles (Phase 6b) | 1 |
| Final match rate | 100% (9/9 FRs, 37/37 ACs) |
| 6a-prime architectural review | `READY_TO_MERGE` |
| Tests | 550 passing / 0 failing (baseline 530) |
| Phases with back-propagation | None |
| Elapsed | 76.1 min |

## What Went Well

- **The receipt-path-anchored-to-pin-file decision paid for itself twice.** It gave FR-8's isolation
  for free and, more importantly, removed the need for a suite-wide bypass. It also means the
  receipt *inherits* rather than duplicates the cwd-relativity already filed as J2, so one fix later
  covers both artifacts.
- **Mutation testing caught what a green suite could not.** Every guard was verified by disabling it
  and confirming tests fail: `_receipt_valid` → 4 failures, `_preflight_conflict_check` → 1,
  a removed `SKILL.md` token → 2, TTL default → 1, bypass ordering → 1. Both Phase-6b tests were
  regression guards that passed on arrival — precisely the shape that ships unenforced coverage.
- **The gap analysis found two ACs the implementer's self-review had declared covered.** Task 3
  reported "every acceptance criterion has a direct assertion"; AC-5.4 and AC-6.4 had none. Reading
  the assertions rather than the report is what surfaced them.
- **Comparing assertions, not labels, avoided four false gaps.** A label-only diff reported AC-3.4,
  AC-5.3, AC-6.2 and AC-8.3 as missing; three were covered without naming the AC in a docstring, and
  the fourth is measured by design.
- **The first live worktree fanout worked.** Two Codex workers on disjoint modules, both faithful to
  the impl-plan's code blocks with no improvisation, both merged clean, `530 → 539`.
- **The feature was validated live, not only in tests.** All four refusal reasons were fired against
  the real wrapper, and the positive path (`env` → receipt → `send` rc=0) confirmed — a green suite
  has certified a dead tool in this repo before.

## What To Improve Next Time

- **Give fanout workers an explicit commit instruction.** Both workers reported `DONE` with green
  suites and left everything uncommitted. Run exactly as documented, the merge gate would have
  merged an up-to-date branch, auto-recorded a clean merge, and `worktree-rm` would then have
  destroyed the only copy of the work. Filed as J15; it is the most dangerous finding of the run.
- **Do not trust an implementer's coverage self-assessment.** Two of the three Codex dispatches
  claimed complete AC coverage; one was wrong by two ACs. Cheap to check, expensive to miss.
- **Budget the audit prompt against the design's size, not the spec's.** The design audit assembled
  to 53.5 KB and the documented remedy (split by FR group) would not have helped, because 46.2 KB of
  it was fixed cost carried by every split (J13).
- **Pass `--started-ts` explicitly when creating a feature.** Doing so is why this run's telemetry
  reports `elapsed_min: 76.1` instead of the ~56-year epoch sentinel every prior feature carries
  (J8, still unfixed and scheduled for Wave 4).

## Carry Items

- **Wave-2 FR-5 — the `ASSEMBLE: PASS` mandated read — remains protocol, not machinery.** Held out
  of scope deliberately: this run dogfooded `h_mad_assemble_audit.py`, and changing that instrument
  during the measurement would have invalidated both. J12 now records a concrete defect in it.
- **J11–J15 filed and unfixed** (`docs/skill-monitoring.md`): J11 an unexecutable telemetry
  instruction; J12 `ASSEMBLE: PASS` returned for a prompt predicted to fail; J13 the oversize remedy
  that does not reduce size; J14 the fanout dispatch/await path conflict; J15 the uncommitted-worker
  hazard. J15 is 🔴 and should be fixed before the next fanout.
- **The ~49 KB reviewer cliff did not reproduce.** A 52,168 B prompt delivered by file indirection
  was answered normally by Antigravity 1.1.5 / Gemini 3.1 Pro. Recorded as evidence; the original
  measurement did not distinguish TUI paste from agent-side file reads. Worth a deliberate
  re-measurement before anyone trims a design to satisfy the old number.
- **Pre-existing Pyright warning** on `_remove_stray_pin_file` (unused-symbol false positive; it is
  `atexit`-registered). Present on `main` before this feature; not touched.

## Version History
- v1.0: Initial report draft.
