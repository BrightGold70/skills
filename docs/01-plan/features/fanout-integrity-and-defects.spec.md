# Spec: fanout-integrity-and-defects

## Executive Summary

`hmad-dispatch worktree-rm` refuses to destroy a worktree that still holds work, `worktree-create`
surfaces a task-id so the orchestration verbs work on both dispatch paths, a new feature record is
stamped with the real time instead of the epoch, and a `DONE_WITH_CONCERNS` naming no concern is
treated as an error rather than a verdict.

## Goal

Make the Phase-5 fanout safe to run, and remove the two verdict/telemetry defects that make a run's
own records untrustworthy — so Wave 4's candidate batch can be fanned out over machinery that
cannot silently lose it.

## Definitions

- **Holds work** — the worktree has uncommitted changes (tracked modifications, staged changes, or
  untracked non-ignored files), **or** has commits not reachable from the comparison ref.
- **Resolvable selector** — a selector `worktree-rm` can map to an existing directory on disk.
  Selectors appear as `<repoId>::<path>`, a bare name, an id, or `active`.
- **Contentless `DONE_WITH_CONCERNS`** — a report whose last `STATUS:` line reads
  `DONE_WITH_CONCERNS` while naming no concern: the concerns section is absent, empty, or says only
  a negation (`none`, `n/a`, `no concerns`, or equivalent).

## Compatibility constraints (established by existing tests — read before auditing)

Two assertions in `h-mad/tests/test_hmad_dispatch.py::test_worktree_rm_argv_force_and_failure`
constrain FR-1–FR-4 and are **not** negotiable without an explicit decision:

1. `worktree-rm wt-7 --force` asserts the stub capture is **exactly**
   `orca worktree rm --worktree wt-7 --force --json` — one call, nothing else. So `--force` must
   short-circuit before any resolution lookup.
2. `worktree-rm wt-7` with the stub exiting 1 asserts rc=1 and the existing
   `[H-MAD] worktree-rm failed selector=wt-7 rc=1` marker. `wt-7` is a bare name that resolves to no
   directory, so an unresolvable selector must **not** by itself cause a refusal.

Constraint 2 also resolves the brainstorm's open conflict in the direction the codebase already
takes elsewhere: `_orca_handle_live` treats an unreadable listing as *unknown*, never as death, so
only **positive evidence** blocks. This loses nothing against the real hazard — the Wave-3 case that
motivated J15 used a `<repoId>::<path>` selector pointing at an existing directory.

## Functional Requirements

### FR-1: `worktree-rm` refuses a worktree with uncommitted changes
- **Description**: When the selector resolves to a directory whose git status is not clean,
  `worktree-rm` refuses: non-zero, nothing removed, reason on stderr.
- **Acceptance Criteria**:
  - AC-1.1: With a resolvable worktree holding a modified tracked file, `worktree-rm` returns
    non-zero and makes no `orca worktree rm` call.
  - AC-1.2: The refusal names a distinct reason token on stderr identifying uncommitted work.
  - AC-1.3: Untracked, non-ignored files alone are enough to refuse (this is the Wave-3 shape — the
    workers' output was untracked-and-modified, not staged).
  - AC-1.4: A file ignored by `.gitignore` alone does **not** cause a refusal — the guard
    discriminates rather than refusing on any `git status` output.

### FR-2: `worktree-rm` refuses a worktree holding unmerged commits
- **Description**: When the worktree's branch has commits not reachable from the comparison ref,
  `worktree-rm` refuses. This is the other half of the Wave-3 hazard: committed-but-never-merged
  work is destroyed just as silently as uncommitted work.
- **Acceptance Criteria**:
  - AC-2.1: With a clean worktree whose branch has a commit not reachable from the comparison ref,
    `worktree-rm` returns non-zero and makes no `orca worktree rm` call.
  - AC-2.2: The refusal names a distinct reason token on stderr, different from FR-1's.
  - AC-2.3: A clean worktree whose commits are all reachable from the comparison ref is removed
    normally — the guard discriminates.
  - AC-2.4: How the comparison ref is determined is documented, and a worktree for which it cannot
    be determined does not refuse on that basis alone (per the compatibility constraint above).

### FR-3: `--force` overrides both guards and announces itself
- **Description**: `--force` skips FR-1 and FR-2 entirely and proceeds to removal, logging that it
  did so.
- **Acceptance Criteria**:
  - AC-3.1: With `--force` and a worktree holding uncommitted changes, removal proceeds.
  - AC-3.2: With `--force`, the stub capture contains exactly the one existing
    `orca worktree rm --worktree <sel> --force --json` call and no resolution lookup — the existing
    assertion is preserved byte-for-byte.
  - AC-3.3: A forced removal that bypassed a guard emits a notice on stderr naming the bypass.

### FR-4: Unguarded paths behave exactly as before
- **Description**: Existing `worktree-rm` behavior is preserved wherever the guard does not fire.
- **Acceptance Criteria**:
  - AC-4.1: An unresolvable selector (bare name, no such directory) is removed as today — the guard
    does not refuse on inability to check.
  - AC-4.2: A failing `orca worktree rm` still returns its exit code and emits the existing
    `[H-MAD] worktree-rm failed selector=<sel> rc=<n>` marker unchanged.
  - AC-4.3: `worktree-rm` on a non-orca substrate still returns 2 with the existing
    "requires orchestration mode" message and makes no call.
  - AC-4.4: Removing an already-gone selector still logs and no-ops — teardown stays idempotent.

### FR-5: `worktree-create` surfaces a task-id
- **Description**: `worktree-create` registers an orchestration task alongside the worktree and
  surfaces its id, so `await` and `gate-create` — which both require `--task` — work on the
  prompt-at-create path as well as the task-dispatch path.
- **Acceptance Criteria**:
  - AC-5.1: **When `--prompt-file` is supplied**, `worktree-create` emits both the worktree selector
    and a task-id, each separately parseable by a caller. Without `--prompt-file` its behaviour is
    unchanged and no task is registered.

    *Amended in v1.1 after the cycle-1 design audit raised this as an Axis C narrowing.* The
    original wording was unconditional, and honouring it literally would (a) break
    `test_worktree_create_argv_orca`, which pins the bare-form stub capture to **exactly one**
    `orca` call, and (b) register an orphan orchestration task for every worktree created outside a
    fanout. `--prompt-file` is the fanout path and the only one where `await`/`gate-create` are
    needed, so gating on it costs nothing that J14 was filed to buy: the create-with-prompt route
    can now record a merge gate, which is the defect. Backward compatibility is a base Axis B
    invariant and outranks the convenience of an unconditional rule.
  - AC-5.2: The emitted task-id is accepted by `gate-create` as a `--task` value.
  - AC-5.3: The existing worktree-selector output remains obtainable by existing callers without
    them changing how they parse it (base Axis B: backward compatibility).
  - AC-5.4: If task registration fails, `worktree-create` still creates the worktree and still
    reports the selector — a task-id is an enrichment, never a gate on worktree creation.

### FR-6: A new feature record is stamped with the current time
- **Description**: `h_mad_state_write.py` defaults `started_ts` to `now(UTC)` instead of the
  hardcoded `1970-01-01T00:00:00Z` sentinel (J8).
- **Acceptance Criteria**:
  - AC-6.1: Creating a feature without `--started-ts` records a `started_ts` within a few seconds of
    now, not the epoch.
  - AC-6.2: An explicitly supplied `--started-ts` is still honoured verbatim.
  - AC-6.3: A telemetry row derived from a record created without `--started-ts` reports a plausible
    `elapsed_min` (single-digit minutes for a just-created feature), not ~29,744,612.
  - AC-6.4: Existing records already carrying the epoch are left untouched — the store is history,
    and nothing rewrites it.

### FR-7: A contentless `DONE_WITH_CONCERNS` is an error, not a verdict
- **Description**: `h_mad_extract_verdict.py` refuses to return `DONE_WITH_CONCERNS` when the report
  names no concern, raising the same way it does for a missing verdict (J10).
- **Acceptance Criteria**:
  - AC-7.1: A report whose `STATUS:` is `DONE_WITH_CONCERNS` with a substantive concerns section
    returns the verdict normally.
  - AC-7.2: The same verdict with no concerns section at all exits 2 and prints no verdict.
  - AC-7.3: The same verdict whose concerns section says only a negation (`none`, `n/a`,
    `no concerns`) exits 2 and prints no verdict.
  - AC-7.4: `DONE`, `BLOCKED` and `NEEDS_CONTEXT` are unaffected by the concern check, as are the
    `VERDICT:` and `ASSESSMENT:` contracts — the check is scoped to one value of one key.
  - AC-7.5: The error message distinguishes "no concern stated" from "no verdict line", so the
    operator can tell a mis-formatted report from a silent agent.
  - AC-7.6: A concerns section whose text merely *contains* a negation word while stating a real
    concern — e.g. `Concerns: none of the tests cover submodules, which is a real gap` — returns the
    verdict normally. The negation test matches a normalised whole value, never a substring.

    *Added in v1.2 during implementation-plan validation.* Prototyping the detector against the 13
    real `DONE_WITH_CONCERNS` reports on this machine showed two things the spec had not pinned: a
    substring match would silently discard a stated concern that happens to begin with "none", and a
    prefix-only label match rejects the real label form `Working-tree concern:`. AC-7.1 now names
    that label form and this AC pins the substring hazard.

### FR-8: The concern obligation is stated to the implementer
- **Description**: `references/codex-implementer-prompt.md` requires that reporting
  `DONE_WITH_CONCERNS` means naming at least one concern, and says to report `DONE` otherwise.
- **Acceptance Criteria**:
  - AC-8.1: The template states the obligation and the "if you cannot name one, report `DONE`" rule.
  - AC-8.2: The template states that a contentless `DONE_WITH_CONCERNS` will be rejected by the
    orchestrator, so the consequence is visible to the agent.

### FR-9: Documentation matches the shipped machinery
- **Description**: `SKILL.md` and `references/orchestration-mode.md` describe the `worktree-rm`
  guards and the unified task-id path.
- **Acceptance Criteria**:
  - AC-9.1: The fanout teardown documentation states that `worktree-rm` refuses to destroy a
    worktree holding work, and names both reason tokens.
  - AC-9.2: The fanout protocol no longer presents `worktree-create --prompt-file` and
    `task-create`+`dispatch` as one sequence; it states the task-id is available from either.
  - AC-9.3: `SKILL.md`'s verb-behaviour table for `worktree-rm` reflects the guard.
  - AC-9.4: `SKILL.md` frontmatter (`name`, `description`) remains valid — project Axis B, skill
    manifest integrity.

## Non-Functional Requirements

- **Performance**: The guard may add at most one filesystem-local git invocation per `worktree-rm`,
  plus at most one Orca lookup when the selector needs resolving. `--force` adds nothing.
- **Security**: N/A — no credentials, no external transport.
- **Compatibility**: Base Axis B. Every existing `worktree-rm` and `worktree-create` assertion must
  continue to pass unchanged, or the change must be justified explicitly in the design. Operator
  overrides keep their precedence.

## Out-of-Scope

- **Wave 4's candidate batch** — the two `invariants.base.md` discipline rules, the
  `file-issue-then-fix-under-TDD` tooling, the staged-prompt repair sweep, the stub-harness probe,
  and the two `SKILL.md` prose notes. They are the payload for the *next* feature, fanned out over
  the machinery this one repairs.
- **Rewriting historical telemetry rows.** The four epoch-stamped rows stay wrong; the log is
  append-only history (AC-6.4).
- **Judging whether a stated concern is a *good* concern.** FR-7 checks that one was stated, not its
  quality — the negative set is enumerable, substance is not.
- **`stablyai/orca#9870`** — still blocked upstream.

## Assumptions

- Wave 3 (`4111297`) is on `main` and unmodified by this feature.
- `orca orchestration task-create` can be called independently of a worker, as demonstrated during
  Wave 3 (`task_c7af32f52ab2` was created with no dispatched agent).
- The agents are `codex` and `agy`, and the substrate under test is orca.
- Tests run under an interpreter with `jsonschema` (`/opt/anaconda3/bin/python3`).

## Version History
- v1.0: Initial specification draft.
- v1.2: AC-7.6 added and AC-7.1 widened during implementation-plan validation, after replaying the
  detector against the 13 real `DONE_WITH_CONCERNS` reports on this machine. Both changes close
  false-negative paths that a purely synthetic test set would not have surfaced: a substring
  negation match discards a real concern beginning with "none", and a prefix-only label match
  rejects `Working-tree concern:`.
- v1.1: **Back-propagation from the Phase-4 design audit (cycle 1).** AC-5.1 amended from an
  unconditional task-id to one gated on `--prompt-file`, with the reasoning recorded inline. The
  audit classified the design's version as an Axis C narrowing and raised it as a must-fix so the
  reconciliation would be a decision rather than a silent divergence; the decision was to change
  this document, not the design, because the unconditional form conflicts with the
  backward-compatibility invariant.
