# Plan: anchor-precheck-phase-5e-wiring

## Executive Summary

Turn the anchor sweep from a documented step into an enforced one — asserted by the test suite and
required by the mutation run itself — and make the committed specs portable enough for that
assertion to hold anywhere but one developer's machine.

## Overview

A mutation spec's anchor must match its target source exactly once; when it does not, the mutation
never lands, the suite stays green, and the run reports the guard as enforced. The sweep that
detects this exists and is documented, but nothing obliges anyone to run it. When it was first run
across the committed specs, seven of 177 anchors were drifted, two of them broken by a refactor made
minutes earlier in the same session. (That measurement was taken over 14 specs; the tree now carries
213 anchors across 16.)

This matters now because the same failure recurred three times in one day, to an author who knew the
tool existed. The obligation has to stop depending on memory.

## Scope

In scope: how `h_mad_mutation_harness.py` resolves a spec's `root`; what a mutation run does before
applying its first mutation; the `root` value carried by every committed spec in the repository; a
new test asserting the committed specs are un-drifted; and the documentation that describes the
resulting contract.

User-visible behaviour changes in three ways. A mutation run may now refuse before doing anything,
with a new verdict word. A relative `root` in a spec means something different than it did. And the
test suite acquires a failure mode it did not have — a drifted committed anchor now fails the suite.

## Goals

- Make a drifted anchor detectable without anyone choosing to look — FR-5.
- Make it impossible for a mutation run to report on guards while its sibling specs are unverified — FR-3, FR-4.
- Make a spec mean the same thing wherever it is run from, and wherever the repository is checked out — FR-1, FR-2.
- Keep the sweep's coverage honest about what it did and did not examine — FR-6.
- Leave the contract documented well enough that the next reader is not told to do by hand what is now automatic — FR-7.

## Requirements

- FR-1: A relative `root` in a mutation spec resolves against the spec's own directory.
- FR-2: Every committed mutation spec carries a portable, spec-relative root.
- FR-3: The mutation run refuses when any spec in its set has drifted.
- FR-4: The set-wide refusal is a distinct verdict carrying no mutation counts.
- FR-5: The suite asserts that the repository's own committed specs are un-drifted.
- FR-6: A non-spec file in the specs directory is never mistaken for drift.
- FR-7: SKILL.md documents the obligation as mechanical rather than advisory.

## Implementation Strategy

Two enforcement points, deliberately covering different moments, because neither subsumes the other:
the suite assertion fires whether or not a mutation runs, and the run-time refusal fires whether or
not the suite runs.

Root resolution is corrected **first**, because the suite assertion cannot be portable until it is —
the committed specs currently name one machine's checkout, so the assertion would fail everywhere
else. This ordering is a real dependency, not a preference.

Patterns to follow, all already established in this repository:

- **One rule, one implementation.** The sweep, the run, and the new test all reach the same
  `precheck_spec()` and the same root resolver. A second copy of the one-match rule is precisely how
  the sweep and the run would come to disagree about what drift means.
- **A cannot-judge carries no counts.** The new verdict reports what the sweep measured and omits
  the mutation counts entirely, so a pre-refusal can never be read as a run that caught nothing.
- **Exit 0 is reserved for a run that measured the guards.** The new verdict exits non-zero, joining
  the harness's existing family of outcomes that measured nothing.
- **Report what was skipped.** A file the sweep declined to examine is named, so narrowed coverage
  is visible rather than inferred.

Deliberately not touched: the `--check-anchors` CLI's own verdict word and exit code, which diverge
from the house contract in a way that is real but fails toward re-anchoring — the safe direction.
Correcting it in the same cycle that wires this harness in would couple two changes whose reverts
would have to discriminate each other. The inline path sidesteps inheriting that divergence by
classifying files itself rather than reusing the CLI's collapsed verdict.

## Architecture Considerations

- **The harness must stay stdlib-only and free of git.** It is invoked with a bare `python3` and
  touches git zero times today. The worktree correctness this plan delivers comes from resolving
  paths relative to the spec file, which needs no VCS knowledge at all — a git-based approach would
  buy the same result at the cost of a dependency the tool has deliberately never had.
- **The two coupled suites.** `~/.claude/skills/h-mad` is a symlink into this repository, so a
  sibling project's tests reach these scripts through it. A change here can fail a suite in a
  project this plan does not otherwise touch, and both must pass before merge.
- **The change is self-referential.** The harness's own mutation spec anchors the exact summary line
  the new verdict modifies, so implementing it drifts the guard being built. This is the failure the
  feature exists to catch, arriving inside the feature's own construction; the re-anchor belongs in
  the same commit as the change that causes it.
- **Set-wide refusal couples sibling specs.** A drifted spec blocks mutation work on its neighbours.
  That is the intended forcing function, and it puts weight on the refusal message: it must name
  which spec drifted, and distinguish the one being run from a sibling, or the coupling reads as an
  unexplained blockage.
- **The two projects' specs are not structurally alike.** h-mad's 16 already root at their own skill
  directory; handoff's one roots at the repository, prefixes its targets with `handoff/`, and runs
  pytest from there. The domain layer requires a skill to remain runnable from a bare clone with no
  hardcoded path outside its own directory, so handoff's spec needs its prefixes and command changed
  as well as its root — otherwise it stops being machine-pinned while still resolving above its own
  skill. This is why the re-rooting guard is expressed over anchor text rather than over which keys
  are allowed to change.
- **Scoping by directory keeps projects independent.** Each project's runs guard that project's
  specs, which matches how the specs are already organised and avoids inventing a repository-root
  notion the harness does not have.

## Deliverables

| Deliverable | Type | Satisfies |
|---|---|---|
| Spec-relative root resolver, shared by the sweep and the run | function | FR-1 |
| Portable roots across all 17 committed specs; handoff's also re-prefixed for self-containment | data | FR-2 |
| Guard against an absolute `root` reappearing in a committed spec | test | FR-2 |
| Sibling sweep executed before the first mutation is applied | behaviour | FR-3 |
| `MUTATION: PRECHECK_DRIFTED` verdict, counts, exit code, and `[H-MAD]` marker | CLI contract | FR-4 |
| Refusal message naming spec, mutation, resolved root, and own-vs-sibling | CLI output | FR-3 |
| Suite assertion over the repository's own committed specs | test | FR-5 |
| Non-zero spec-count assertion in that test | test | FR-5 |
| Structural classification of spec / non-spec / unclassifiable files | function | FR-6 |
| SKILL.md §Phase-5e rewrite, registry entry, recovery-table row, doc test | docs | FR-7 |

## Risks and Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| Re-rooting 17 specs silently corrupts one, and the sweep still reports clean because the anchor text was untouched | High | Guard the anchors, not the key set: require every `find`/`replace` byte-identical before and after, and identical per-spec anchor counts. A corrupted target path with intact anchor text is exactly what the sweep cannot see, so key-set stability is the wrong invariant to assert |
| The new verdict word is missed by an existing consumer of the `MUTATION:` token | Medium | Enumerate consumers before changing the line; the recovery table and the registry entry are both deliverables, not afterthoughts |
| Implementing the new verdict drifts the harness's own spec, and the drift is discovered late | Medium | Pinned as an acceptance criterion; re-anchor in the same commit and sweep afterwards |
| Set-wide refusal blocks unrelated work and the operator cannot tell why | Medium | The refusal names the drifted spec and distinguishes sibling from self; this is the whole reason those are acceptance criteria rather than nice-to-haves |
| A future spec reintroduces an absolute root and portability regresses silently | Medium | Asserted by test rather than by convention |
| Changing root resolution breaks a caller relying on the cwd-relative reading | Low | Verified before speccing: every existing root in both projects and all test-constructed specs is absolute, so no caller exercises the changed path; the existing suite passing is an acceptance criterion |
| The suite assertion passes vacuously if its glob matches nothing | Medium | Non-zero spec count asserted explicitly; the protection exists in the CLI but not in the layer a test would use |

## Convention Prerequisites

- Work proceeds on a feature branch cut at Phase 5c; phase documents land on the default branch.
- The harness's tests and the sibling project's tests both run before merge, because the skills
  symlink couples them.
- Editing this skill while a run is in flight is done in a worktree; the working tree is the live
  skill.
- Every guard delivered here is mutation-verified, and the anchors for those mutations are swept
  after the last edit — the obligation this feature creates applies to the feature itself.

## Success Criteria

- All 35 acceptance criteria in the spec pass automated tests.
- A sweep of the committed specs returns a clean verdict when run from inside the repository, from
  an unrelated directory, and from a checkout at a different absolute path.
- A mutation run inside a worktree modifies only that worktree.
- Deliberately drifting one committed anchor fails the suite; restoring it passes — the assertion
  demonstrably bites.
- Both coupled suites pass at 100%.
- The harness imports nothing outside the standard library and invokes git zero times.

## Out-of-Scope (confirmed from spec)

- The `--check-anchors` CLI's verdict word and exit code, which diverge from the house contract.
  Filed as a monitoring row.
- The four `h_mad_ab_dispatch.py` defects found while staging the Phase-1 probe: no environment
  control between arms, first-match rather than last-match observation, only two substituted tokens,
  and flag-shaped tokens rejected in the documented invocation form. Monitoring rows.
- Any new orchestrator step or gate script. Rejected in Phase 1: a gate is itself a documented step,
  which reproduces this feature's own failure mode one level up.
- Any receipt, cache, or persisted sweep state. Rejected in Phase 1 on measurement — the sweep is
  cheaper than an honest validation of a cache of it.
- Judging whether a spec's mutations aim at the right behaviour; the sweep asserts that anchors
  match, not that guards are well chosen.

## Next Steps

Approval of v1.0, then the Phase 3 audit cycle: assemble the audit prompt with the spec inlined as
the Axis C source of truth, dispatch, gate, and revise until must-fix and should-fix both reach
zero. Phase 4 then derives the design, including the concrete shape of the resolver and the refusal
output that this plan deliberately leaves unspecified.

## Version History

- v1.0: Initial plan draft, derived from the approved spec.
- v1.1: Audit v1 nits from plan.audit.v1.p2 — corrected the drift measurement to 7-of-177 (the tree now carries 213 across 16 specs) and named the [H-MAD] marker in the FR-4 deliverable.
- v1.2: F13 from manual probing: the re-rooting guard is now expressed over anchor text rather than over which keys may change, and the architecture section records that handoff's spec roots above its own skill and needs its prefixes and command changed for self-containment.
