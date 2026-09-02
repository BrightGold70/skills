# Report: audit-report-docs-copy

## Executive Summary
The hand-run codex audit leg now has a documented, tested, mutation-verified path from its transport file into the docs audit record, and the gate refuses to score a transport file directly — shipped at 100% gap match after four 6a-prime cycles surfaced six design deviations the earlier gates could not see.

## Summary
Built one collector (`h_mad_audit_cycle.py`) that serves both audit legs through a surface-aware docs path, a `h_mad_collect_report.py` CLI with a `COLLECT: OK|MISSING|CONFLICT` contract, a `hmad-dispatch collect-report` verb wired to it, a gate refusal for transport-named paths (`^audit_[^.]+\.report\.md$`, disjoint from the docs grammar by construction), and the operator recipe in SKILL.md. The brief's premise narrowed on reproduction: only the codex leg lacked a docs-copy step; the agy leg was already persisted by `audit-cycle`. Every finding acted on this session was reproduced live before a fix was dispatched, and every fix was pinned RED first; two implementer patches were rejected for overreach, one of which would have collected agent narration as an audit report.

## Metrics

| Metric | Value |
|---|---|
| Plan audit cycles | 8 |
| Design audit cycles | 10 |
| Impl-plan audit cycles | 12 |
| Iterate cycles (Phase 6b) | 0 |
| Final match rate | 100% (6/6 FRs, 40/40 ACs) |
| 6a-prime architectural review | `READY_TO_MERGE` (cycle 4; cycles 1–3 `WITH_FIXES`, 6 findings, all fixed) |
| Tests | 2424 passing / 0 failing attributable; 1 pre-existing load-sensitive flake outside the feature (`test_await_defaults_timeout_and_requires_coordinator`, bash `SECONDS` tick, passes 5/5 alone, predates the 5c baseline) |
| Mutation spec | `ALL_CAUGHT mutations=23 caught=23 survived=0`, re-run after every collector change |
| Wire registry | `PASS registered=8 verified=8 broken=0` |
| Phases with back-propagation | None |

## What Went Well
- 6a-prime found six real design deviations (resolve-based same-file detection, grace honoured on the same-file branch, the dead empty-report guard, the empty-pair short-circuit, the recipe's missing `--out` rung, and a staged-prompt collision between the two legs) that four 5e review cycles, an anti-gaming verifier, 23 mutations and a 2424-test suite all missed. It is the only pass positioned to see design-versus-implementation drift, and it earned its place.
- Every finding was reproduced live before acting. Two of the six had prescriptions that were wrong even though their facts were right: one asked to revert to the design's literal text (which would have reintroduced two measured defects and deleted four pins), one implementer patch added a boundary-slicing fallback that collected narration as an audit. Both rejected on measured evidence, both recorded in the commit.
- Task 6's single survivor was a real gap: the impl-plan's stated observable for the project-root guard was wrong (a root that is a FILE cannot discriminate; a root that does not EXIST can, and the mutant silently mkdir-p's a docs tree under the typo). The discriminating test was written and verified to fail under the mutant before the mutation was repointed.
- The Task 5 recipe was verified by running the documented bash block, not reading it — for both phases, all three tokens, empty output, a root containing a space, `set -euo pipefail`, and the `forced=1` field. Two of the four review-cycle defects in that block were only visible by execution.

## What To Improve Next Time
- A fix aimed at one rung of a ladder needs probing at the rungs below it. The cycle-2 collector fix was verified against the case it addressed, genuine conflicts and grace-0, but not against the `--out` rung downstream of the branch it touched; cycle 3 found the regression. Probe the whole ladder after any change to a branch above it.
- Three of my own probes were wrong before the code was: a preamble that interpolated paths unquoted, a fixture without the dispatch boundary, a pin with an unframed body. Each read as a defect until the measurement was checked. Build the fixture the way production produces it, then trust it.
- The impl-plan's Task 6 test names were aspirational — 15 of 16 resolved to nothing — and its stated observable for one mutant was wrong. A plan should be re-verified against the tree at 5d dispatch time, which the skill already says; the handoff's warning was what made it happen here.
- Two 6a-prime cycles wrote probe files into the repository or ran the mutation harness inside it despite being told not to. The tree was restored both times, but an audit that mutates what it measures is a check that has to be re-run every cycle. Worth a harder prompt rule or a post-dispatch tree diff in the archreview scorer.
- Reviewer citations resolved through the installed-skill symlink to a different checkout on cycle 1 and cost a full re-verification of which tree was read. The worktree-path rule is now in the cycle prompt; it belongs in the template.
- Running the full suite concurrently with a verifier that mutates the dispatch script produced two false failures. One heavy tree-touching job at a time.

## Carry Items
- `test_await_defaults_timeout_and_requires_coordinator` (h-mad/tests/test_hmad_dispatch.py) is load-sensitive: `local deadline=$(( SECONDS + timeout ))` and `remaining=$(( deadline - SECONDS ))` straddle a second boundary under load, yielding 599000 vs 600000 ms. Pre-existing (9b493e4, before the 5c baseline), outside this feature. Fix direction: assert `--timeout-ms` within [599000, 600000], or compute `remaining` from a captured start.
- The 6a-prime prompt template should carry the worktree-citation rule and the no-mutation rule verbatim; both were added per-cycle here.
- The archreview scorer could diff `git status --short` before and after the dispatch and report a delta as a finding, closing the "audit mutated the tree" check mechanically.
- Merge to `main` is the operator's call. The main checkout (`/Users/kimhawk/orca/skills`) is on `feature/pin-agents-tail-banner` with a live run; `~/.claude/skills/h-mad` resolves there, so this branch's edits reach the installed skill only at merge.
- 16 stamped handover briefs remain in `carry-forward-sources` for this repo, unconsumed by any handoff's `**Supersedes:**` (deferred two sessions running).

## Version History
- v1.0: Initial report draft.
