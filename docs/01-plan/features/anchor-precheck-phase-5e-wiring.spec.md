# Spec: anchor-precheck-phase-5e-wiring

## Executive Summary

Make the anchor sweep an obligation a run cannot silently skip, by asserting it as a property of the
test suite and by refusing any mutation run whose sibling specs have drifted — and fix the
machine-pinned spec roots that would otherwise make the suite assertion fail everywhere but one
developer's box.

## Goal

No mutation run reports a guard as enforced while the anchors that would test that guard have
drifted, and no drift sits undetected between the edit that caused it and the next time someone
happens to run the affected spec.

## Functional Requirements

### FR-1: A relative `root` in a mutation spec resolves against the spec's own directory

- **Description**: `h_mad_mutation_harness.py` currently resolves `root` as
  `Path(spec.get("root") or spec_path.parent).resolve()`, so a **relative** value resolves against
  the invoking process's cwd. That makes a spec's meaning depend on where it is run from, and it is
  the reason no committed spec can express its own root portably (they all hardcode absolute paths).
  A relative `root` must instead resolve against the directory containing the spec file. An absolute
  `root` is unchanged, and an omitted `root` continues to default to the spec's directory.
- **Acceptance Criteria**:
  - AC-1.1: A spec at `<dir>/s.json` with `"root": ".."` resolves its targets against `<dir>/..`
    when the harness is invoked from `<dir>`, from `/tmp`, and from the repository root — all three
    yielding byte-identical resolved target paths.
  - AC-1.2: A spec with an absolute `root` resolves to exactly that path, unchanged from current
    behaviour, from any cwd.
  - AC-1.3: A spec with no `root` key resolves to the spec file's own directory, unchanged from
    current behaviour.
  - AC-1.4: The resolution rule is shared by `precheck_spec()` and `run_spec()` — a single helper,
    not two copies. A test asserts both entry points resolve the same spec to the same root.
  - AC-1.5: Re-running the existing `h-mad/tests/test_h_mad_mutation_harness.py` suite passes
    unchanged, confirming the change is non-breaking (verified precondition: every existing spec
    root, in tests and in both projects, is absolute).

### FR-2: Every committed mutation spec carries a portable, spec-relative root

- **Description**: All 17 committed specs hardcode an absolute path naming one machine's checkout —
  16 in `h-mad/tests/mutation-specs/` pointing at `<repo>/h-mad`, and 1 in
  `handoff/tests/mutation-specs/` pointing at `<repo>`. Besides being unusable off that machine,
  this makes a mutation run inside a git worktree resolve to the **main** checkout, which matters
  because Phase-5 fanout creates worktrees. Each must be re-rooted to the spec-relative form enabled
  by FR-1.
- **Acceptance Criteria**:
  - AC-2.1: No committed spec under any `tests/mutation-specs/` directory contains an absolute
    `root`. A test asserts this over the whole repository, so a future spec cannot reintroduce one.
  - AC-2.2: `--check-anchors` over all 16 h-mad specs returns `ANCHORS_OK specs=16 mutations=213
    ok=213 drifted=0 unreadable=0` when run from the repository root, from `/tmp`, and from a
    directory outside the repository.
  - AC-2.3: The same sweep returns the same verdict when the repository is checked out at a
    different absolute path (simulated by copying or `git worktree add` to a temporary location),
    proving the machine-pinning is gone.
  - AC-2.4: A mutation run executed from within a git worktree resolves its targets inside **that
    worktree** and leaves the main checkout's files unmodified.
  - AC-2.5: Re-rooting changes only `root` values — every spec's `mutations`, `command`,
    `target_command`, and anchor text are byte-identical before and after, verified by a diff
    restricted to the `root` key.

### FR-3: The mutation run refuses when any spec in its set has drifted

- **Description**: Before applying any mutation, `run_spec()` sweeps every spec in the same
  directory as the spec being run and refuses the entire run if any anchor has drifted. The refusal
  is set-wide: running module M's spec refuses when unrelated sibling spec Y has drifted, because
  the goal is that no run reports success while the tree holds unverified guards.
- **Acceptance Criteria**:
  - AC-3.1: Given a directory holding a clean spec and a drifted spec, running the **clean** one
    refuses and applies **zero** mutations, verified by the target files being byte-identical before
    and after.
  - AC-3.2: Given a directory in which every spec is clean, a run proceeds and returns its ordinary
    verdict, so the precheck does not change the outcome of a healthy run.
  - AC-3.3: The refusal names each drifted spec by filename, each drifted mutation by name, and the
    **resolved** root for that spec — so a spec whose root points somewhere unexpected produces a
    diagnosable message rather than a filename the operator cannot locate.
  - AC-3.4: The refusal distinguishes "the spec you ran has drifted" from "a sibling spec has
    drifted", because the two prescribe different actions.
  - AC-3.5: The sweep is scoped to the running spec's own directory and does not read specs in any
    other directory, verified by a run in a directory whose sibling tree contains a drifted spec
    that must not affect the verdict.

### FR-4: The set-wide refusal is a distinct verdict carrying no mutation counts

- **Description**: The existing `MUTATION: REFUSED` line carries
  `mutations=/caught=/survived=/refused=`, which describe a run that applied mutations and had some
  anchors fail to land. A pre-run refusal applies nothing, so reporting those counts — necessarily
  as zeros — would be indistinguishable from a run that applied mutations and caught none. Per the
  house rule that a cannot-judge carries no counts, the pre-refusal needs its own verdict word and
  its own counts.
- **Acceptance Criteria**:
  - AC-4.1: A set-wide pre-refusal prints `MUTATION: PRECHECK_DRIFTED specs=<N> drifted=<K>` and
    **does not** print `mutations=`, `caught=`, `survived=`, or `refused=`.
  - AC-4.2: `MUTATION: PRECHECK_DRIFTED` exits **2**, matching the harness's existing convention
    that exit 0 is reserved for a run that measured the guards (`ALL_CAUGHT`, `SURVIVED`) and
    anything that measured nothing exits non-zero.
  - AC-4.3: The verdict word `PRECHECK_DRIFTED` does not appear in any existing consumer's match on
    `REFUSED`, verified by grepping the repository and SKILL.md for consumers of the `MUTATION:`
    token.
  - AC-4.4: An `[H-MAD]` marker line is emitted for the pre-refusal, matching the pattern every
    other verdict in this script already follows.
  - AC-4.5: `h-mad/tests/mutation-specs/mutation_harness.json` carries a mutation named
    `change-the-summary-line-callers-parse`, anchored on the exact summary-line f-string this FR
    modifies. That anchor is re-anchored in the same commit as the change, and a sweep afterwards
    returns `ANCHORS_OK` — the feature's own change would otherwise drift the guard it is building,
    which is the same self-inflicted pattern that produced two of the original seven.

### FR-5: The suite asserts that the repository's own committed specs are un-drifted

- **Description**: No test currently sweeps the repository's committed specs — every
  `precheck_spec()` call in the suite builds a synthetic spec under `tmp_path` — so all 213 real
  anchors can drift with the suite fully green, which is how seven of them did. A test must sweep
  the project's own `tests/mutation-specs/*.json` and fail naming every drifted anchor.
- **Acceptance Criteria**:
  - AC-5.1: A test sweeps every spec in its own project's `tests/mutation-specs/` and fails if any
    anchor does not match exactly once, naming each drifted spec, mutation, and resolved root.
  - AC-5.2: The test asserts a **non-zero** spec count before evaluating drift, so an empty or
    mis-pathed glob fails loudly rather than passing vacuously. A test drives this by pointing the
    helper at an empty directory and asserting it fails.
  - AC-5.3: The test locates the specs directory relative to the test file, not relative to cwd, so
    it passes under `pytest` invoked from the repository root, from the project directory, and via
    the skills symlink.
  - AC-5.4: The test calls `precheck_spec()` and does not re-implement the one-match rule, so the
    suite assertion and the sweep can never disagree about what drift means.
  - AC-5.5: Deliberately drifting one committed anchor makes this test fail, and restoring it makes
    the test pass — the mutation-style check that the assertion actually bites.

### FR-6: A non-spec file in the specs directory is never mistaken for drift

- **Description**: Both the inline sweep (FR-3) and the suite assertion (FR-5) glob a directory, so
  a file that is not a mutation spec must not be able to block every run. Equally, a genuinely
  corrupt spec must not be silently skipped. The two cases need different handling and both need to
  be visible.
- **Acceptance Criteria**:
  - AC-6.1: A file that parses as JSON but has no `mutations` key is not a spec: it is skipped and
    does not contribute to the drift count.
  - AC-6.2: A file that does not parse as JSON at all cannot be classified, so it is **reported by
    name** and does not contribute to the drift count. It is never silently ignored.
  - AC-6.3: A file that parses as JSON and has a `mutations` key is a spec, so any failure to sweep
    it is a real finding and is reported as such rather than skipped.
  - AC-6.4: Skipped and unclassifiable files are named in the output, so "the sweep covered fewer
    specs than you think" is always visible.
  - AC-6.5: Verified precondition holds as a test: every `.json` file currently in
    `h-mad/tests/mutation-specs/` has a `mutations` key, so none is skipped today.

### FR-7: SKILL.md documents the obligation as mechanical rather than advisory

- **Description**: SKILL.md §Phase-5e currently tells the reader to run `--check-anchors` by hand.
  With FR-3 and FR-5 in place the obligation is enforced, and the documentation must say so — both
  because a stale instruction to do it manually invites the reader to believe it is optional, and
  because the helper-scripts registry entry is the contract for the new verdict word.
- **Acceptance Criteria**:
  - AC-7.1: SKILL.md §Phase-5e states that the mutation run performs the sweep itself and refuses on
    sibling drift, rather than instructing the operator to run it beforehand.
  - AC-7.2: The `h_mad_mutation_harness.py` registry entry documents `MUTATION: PRECHECK_DRIFTED`,
    its counts, and its exit code.
  - AC-7.3: SKILL.md documents that a relative spec `root` is spec-relative, since FR-1 changes a
    behaviour a spec author can observe.
  - AC-7.4: A doc test asserts the presence of the new verdict word in SKILL.md, matching the
    existing pattern for `ANCHORS_DRIFTED`.
  - AC-7.5: `references/failure-recovery.md` gains a recovery row for `MUTATION: PRECHECK_DRIFTED`
    naming its halt reason and remedy. Its existing 5e row lists `REFUSED`, `BASELINE_NOT_GREEN`,
    `RESTORE_FAILED`, and `UNREADABLE` against `step5e:mutation_unverified:<module>`; a verdict
    absent from that table has no documented route, which is how an operator meets a token with no
    prescribed action.

## Non-Functional Requirements

- **Performance**: The inline sweep must not meaningfully lengthen a mutation run. Measured
  baseline: 16 specs / 213 anchors sweep in 59 ms, against a mutation run that executes the suite
  once per mutation. Budget: the precheck adds under 250 ms for the current spec set.
- **Security**: N/A. This is a local developer tool, not a trust boundary; the precheck is a
  correctness guard, not a control anyone is expected to attack.
- **Compatibility**: `h_mad_mutation_harness.py` remains **stdlib-only** and must continue to touch
  git **zero** times — it is invoked with a bare `python3` and must not acquire a VCS dependency.
  Both coupled suites (`h-mad/` and `handoff/`) must pass, since the skills symlink couples them.

## Out-of-Scope

- **F2 — the `--check-anchors` CLI verdict/exit discipline.** `ANCHORS_DRIFTED` is a real verdict
  that exits 2, and an unusable spec JSON collapses into that same word. Deferred deliberately;
  FR-6 keeps the inline path from inheriting the collapse by classifying files itself. Files as a
  `docs/skill-monitoring.md` row at Phase 7.
- **F3–F6 — `h_mad_ab_dispatch.py` defects** found while staging the Phase-1 probe: no environment
  control between arms, first-match instead of last-match observation, only `{prompt}`/`{log}`
  substituted, and `--run` rejecting flag-shaped tokens in the documented form. Monitoring rows.
- Adding a Phase-5 gate script or any new orchestrator step. Rejected in Phase 1: a gate is itself a
  documented step, which reproduces this feature's own failure mode one level up.
- Any receipt, cache, or persisted sweep state. Rejected in Phase 1 on measurement.
- Judging whether a spec's mutations aim at the right behaviour. The sweep asserts anchors match,
  not that guards are well chosen; that remains the mutation run's job.

## Assumptions

- Every existing spec `root` is absolute, so FR-1's change to relative-root resolution breaks no
  current caller. **Verified 2026-08-26** across all 17 committed specs and all 8 test-constructed
  specs; FR-1 AC-1.5 re-asserts it.
- Mutation specs live in a directory named `tests/mutation-specs/` within each project. Both
  projects follow this today.
- FR-5 is per-project by construction. Applying it to `handoff/` as well as `h-mad/` follows from
  FR-2 re-rooting handoff's spec; if the audit judges `handoff/` out of bounds for this feature,
  FR-2 and FR-5 must be narrowed together, not separately, or handoff is left re-rooted but unswept.
- The 7-of-177 drift measurement and the 59 ms sweep timing were taken on this repository at
  2026-08-26 and are used as design inputs, not as acceptance criteria.

## Version History

- v1.0: Initial specification draft. Carries the Phase-1 settled design (two mechanisms, no receipt,
  no gate), the operator's F9 remedy decision (spec-relative resolution plus re-rooting all 17
  specs), and the contract decision that a set-wide pre-refusal needs its own verdict word rather
  than reusing `REFUSED`'s count-bearing shape.
