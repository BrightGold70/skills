# Plan: cycle-telemetry-fidelity

## Executive Summary

Add a stdlib-only derivation module that computes both cycle counters from the versioned
artifacts on disk, wire it into `h_mad_telemetry.py` at record and summary time, extend Phase 6b
to emit one analysis artifact per iterate cycle, and give the telemetry module the first tests it
has ever had.

## Overview

`h_mad_telemetry.py` reports two cycle counters that are structurally always zero, so both drift
warnings it implements are unreachable. The counters are state fields nothing increments. This
plan replaces the state read with a derivation over artifacts each cycle already writes, and
closes the one gap in that evidence — Phase 6b overwrites its analysis instead of versioning it.

It matters now because every quality signal H-MAD emits about its own runs is currently false,
and the remediation sequence's later waves are meant to be measured by exactly these numbers.

## Scope

In scope: the `h-mad/scripts/` telemetry path, a new derivation module, the Phase 6/6b protocol
prose in `h-mad/references/inline-protocols.md`, and tests under `h-mad/tests/`.

User-visible behaviour: `h_mad_telemetry.py summary` prints real cycle counts for current and
historical features and can emit its drift warnings; `record` appends rows with real counts;
Phase 6b leaves a readable per-cycle analysis trail instead of overwriting one file.

## Goals

- Derive `audit_cycles` from audit artifacts rather than state — FR-1
- Make iterate cycles evidence-bearing by versioning the analysis artifact — FR-2
- Derive `iterate_cycles` from that evidence — FR-3
- Correct counts at write time — FR-4
- Correct counts for historical rows at read time, without mutating the log — FR-5
- Find features wherever they live, live or archived — FR-6
- Match filenames precisely enough that neighbouring features and templates cannot pollute a
  count — FR-7

## Requirements

- FR-1: Audit cycle counts are derived from audit artifacts
- FR-2: Phase 6b emits one analysis artifact per iterate cycle
- FR-3: Iterate cycle counts are derived from analysis artifacts
- FR-4: `telemetry record` writes derived counts
- FR-5: `telemetry summary` backfills historical rows on read
- FR-6: Archived and live features are both found
- FR-7: Matching is anchored and excludes non-feature files

## Implementation Strategy

**One new module, one changed module, one changed document.** Derivation lands in a new
`h-mad/scripts/h_mad_cycle_counts.py` exposing pure functions over a docs root and a feature
name. `h_mad_telemetry.py` imports it at both call sites. Nothing else in `h-mad/scripts/`
changes.

**Pure functions, no I/O contract of their own.** The module takes a docs root and returns
counts; it does not read state, write files, or print. That keeps it directly unit-testable
without fixtures for the state store, and it means the two telemetry call sites share one
implementation rather than each globbing (AC-1.5).

**Stdlib only — deliberately not like the state scripts.** `h_mad_state_*.py` require
`jsonschema`, which the default `python3` on this machine lacks (F8); every state call this
session needed `/opt/anaconda3/bin/python3`. Telemetry runs fine under bare `python3` today and
must keep doing so, or this fix inherits F8's blast radius and `summary` breaks for anyone
without a conda install. `pathlib` + `re` are sufficient.

**Derivation reads filenames, never file contents.** The counts come from the `v<N>` segment of
machine-written filenames. No parsing of headings or prose — that is the failure class this
codebase keeps re-encountering (the B4 `isolate_bibliography` heading matcher, the audit gate's
bullet-only classifier, and the `## Version History` convention that one of two sampled analyses
simply does not have).

**Deliberately untouched**: `h_mad_state_write.py` (the `audit_cycles`/`iterate_cycles` fields
stay in the schema and simply stop being telemetry's source of truth), `h_mad_audit_gate.py`,
`h_mad_phase7_preconditions.py`, and every HemaSuite file.

## Architecture Considerations

**The unversioned analysis path is load-bearing and must not move.**
`h_mad_phase7_preconditions.py:133` defaults to `docs/03-analysis/<feature>.analysis.md` and
`:33` parses the **first** match rate it finds. FR-2 therefore keeps writing that path as the
latest cycle's content. This also closes a latent bug: had Phase 6b ever appended cycles into
that one file, Phase 7 would have gated on the oldest measurement in it.

**The doc-template test reads the protocol document.**
`tests/test_h_mad_doc_templates.py:11` parses `inline-protocols.md` and maps phase `6` to the
`analysis` doc type, extracting its fenced template block. FR-2 edits that section, so this test
is a regression surface, not just a new-test target.

**Telemetry has no tests at all.** All 454 current tests, and none touch `h_mad_telemetry.py`.
That absence is why a counter could be dead since it was written and stay dead: nothing asserted
the number, so nothing failed. The new tests are the first coverage this module has had, and the
one that matters most is the assertion that a drift warning *can fire* — the check that would
have caught the original defect.

**Verification against live data, not only fixtures.** The repo's own archive supplies ground
truth, and one case is better than anything I would have invented: the archived
`orca-git-native-checkpoints-and-merge-gate` has `design.audit.v2.md` with **no v1**. That is
AC-1.3's numbering gap occurring naturally. Expected derived counts, read off the archive:

| Archived feature | plan | design | impl_plan |
|---|---|---|---|
| `orca-git-native-checkpoints-and-merge-gate` | 2 | 2 (v1 absent) | 1 |
| `worktree-parallel-multi-module-tdd` | 3 | 2 | 2 |
| `dispatch-resolve-verb` | 2 | 1 | 1 |

## Deliverables

| Deliverable | Type | Satisfies |
|---|---|---|
| `h-mad/scripts/h_mad_cycle_counts.py` | module | FR-1, FR-3, FR-6, FR-7 |
| `h_mad_telemetry.py` — `cmd_record` derives counts, `--docs-root` | CLI | FR-4 |
| `h_mad_telemetry.py` — `cmd_summary` recomputes on read, `--docs-root` | CLI | FR-5 |
| `references/inline-protocols.md` §Phase 6 + §Phase 6b | protocol doc | FR-2 |
| `h-mad/tests/test_h_mad_cycle_counts.py` | tests | FR-1, FR-3, FR-6, FR-7 |
| `h-mad/tests/test_h_mad_telemetry.py` | tests | FR-4, FR-5 |

## Risks and Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| Editing §Phase 6's template block breaks `test_h_mad_doc_templates.py` | Suite red on an unrelated contract | Treat that test as a regression gate for FR-2; run it before and after the prose edit rather than discovering it at 5f |
| Importing the new module makes telemetry require a non-stdlib dependency | `summary` breaks under the default `python3` — F8 all over again | Stdlib-only constraint stated in the spec's NFRs; a test asserts the module imports under a bare interpreter |
| A naive glob counts `docs/templates/audit-example.audit.v1.md` | Every feature's count polluted by a template | AC-7.2 pins that exact real filename as a fixture |
| Prefix-colliding feature names cross-match (`feat` / `feat-ab`) | Wrong counts, silently | AC-7.1; anchor on `<feature>.`, the defect `handoff_paths.py` fixed with its `__` separator |
| Recomputing unconditionally zeroes a real stored number when a docs tree is gone | Silent data loss in the displayed history | AC-5.2 falls back to the stored row when no artifacts are found |
| Phase 6b's new versioned write is skipped by an orchestrator that follows the old prose | `iterate_cycles` stays 0 for that run | AC-2.4 requires the protocol to name what depends on the artifact, so its purpose is visible at the edit site |
| Derived counts disagree with an operator's memory of a run | Confusion, no arbiter | The artifacts are the evidence; a disagreement means a file is missing, which is itself worth surfacing |

## Convention Prerequisites

- Branch `feature/NNN-cycle-telemetry-fidelity` cut from `main` at Phase 5c; `main` is currently
  in sync with `origin/main`.
- Baseline suite: **454 passed** (`/opt/anaconda3/bin/python3 -m pytest h-mad/tests/ -q`). Phase
  5f must reach 454 + new tests, zero failures.
- TDD gate hook armed at 5a, disarmed only at 5g.
- State scripts run under `/opt/anaconda3/bin/python3` (F8); the new module and its tests must
  run under either interpreter.

## Success Criteria

- All 30 ACs across FR-1..FR-7 pass automated tests.
- Full h-mad suite green: 454 pre-existing + new tests, 0 failures.
- **Replay against live data**: derived counts for the three archived features in
  §Architecture Considerations match the table exactly, run against the real `docs/archive/`
  tree rather than a fixture.
- `h_mad_telemetry.py summary` executed on this repo's real `.h-mad/telemetry.jsonl` prints
  non-zero audit cycles for at least one historical feature — the observable proof that the
  original defect is closed.
- `h_mad_telemetry.py` still runs under bare `python3` (no `jsonschema`).
- `.h-mad/telemetry.jsonl` is byte-identical before and after a `summary` run.

## Out-of-Scope (confirmed from spec)

- Changing the `> 3` drift-warning thresholds.
- Adding `--increment` to `h_mad_state_write.py`; the state fields stay, unused by telemetry.
- Backfilling or rewriting `.h-mad/telemetry.jsonl`.
- Any HemaSuite change.
- Fixing F8 (`jsonschema` absent from the default `python3`).
- Retro-generating versioned analysis artifacts for already-shipped features.

## Next Steps

Operator approves plan v1.0 → audit cycle begins per SKILL.md §"Audit prompt assembly"
(`h_mad_assemble_audit.py --phase plan`), dispatched to agy via report-file transport, gated by
`h_mad_audit_gate.py` until must-fix = 0 and should-fix = 0 → Phase 4 design.

## Version History
- v1.0: Initial plan draft.
