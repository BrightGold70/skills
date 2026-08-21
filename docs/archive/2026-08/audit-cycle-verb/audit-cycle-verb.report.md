# Report: audit-cycle-verb

## Executive Summary

`hmad-dispatch audit-cycle` replaces the five-call hand-assembled h-mad audit cycle with one verb
that assembles, dispatches N concurrent `exec agy` passes, collects, union-gates and emits a single
`AUDITCYCLE:` verdict — shipped at 100% match rate with 1580 tests green and a `READY_TO_MERGE`
architectural review.

## Summary

Nine tasks built the verb bottom-up: a new stdlib-only helper `h_mad_audit_cycle.py` owns
collection, gating and the verdict line, while `hmad-dispatch.sh` owns assembly, dispatch and
reaping. Six call sites are wire-pinned and re-verified at 5f (`WIREREG: PASS verified=6/6`). The
verb audited **its own feature** through Phases 6–7, which is how three of the defects below were
found. Both mutation specs are `ALL_CAUGHT` (6/6 and 12/12, `survived=0 refused=0`), re-run after
the final code changes rather than inherited from an earlier pass.

## Metrics

| Metric | Value |
|---|---|
| Plan audit cycles | 14 |
| Design audit cycles | 24 |
| Impl-plan audit cycles | 10 |
| Iterate cycles (Phase 6b) | 0 |
| Final match rate | 100% (10/10 FRs, 57/57 ACs) |
| 6a-prime architectural review | `READY_TO_MERGE` |
| Tests | 1580 passing / 0 failing |
| Phases with back-propagation | None |

## What Went Well

- **The verb found defects in itself.** Running `audit-cycle` on its own planning documents produced
  J36 (a false measurement in three gated docs), J37 (five call sites where there are six) and, at
  Phase 7, J42. A feature that is its own first user surfaces things a synthetic test cannot.
- **Mutual discrimination proved its worth repeatedly.** Every guard added this cycle was mutated in
  *both* directions, and in three cases the two mutations were caught by *different* tests — the
  `gate()` exit-code guard, the `--passes` default, and the cycle-counter regex. That is what
  distinguishes a guard that bites from a pair of tests that merely coexist.
- **Probing beat re-reading, four times.** J36's premise, J37's count, J39's reconciliation question
  and J41's concurrency claim were each settled by running something, and in three of the four the
  answer inverted what the document said.

## What To Improve Next Time

- **A carried claim decays into a fact.** "Real concurrency untested by every lane" survived three
  handoffs, was restated each time, and dissolved in ten minutes of probing (J41). Two of its four
  shapes already had direct tests. Re-run a carried repro before re-reporting it.
- **Falsify the claim, not the story around it.** The `--passes` finding arrived with a fabricated
  symptom (a bash error that does not occur). The symptom falsified cleanly and was allowed to
  discharge the whole finding — but the concern was real and spec AC-3.1 was genuinely unimplemented
  (J38). A finding's facts, concern and prescription fail independently.
- **A verdict-shaped line is not a verdict.** The first 6a-prime dispatch returned
  `ASSESSMENT: READY_TO_MERGE` from a run whose only tool call errored, whose result carried
  `status: ERROR`, and which had read no files (J40). Every gate in the chain accepted it. 6a-prime
  should require at least one successful tool call before recording a pass.
- **Downstream consumers are outside the diff.** J42 lived in a file the feature never touched, so
  no diff-scoped review could see it. Phases that *read* what a feature *writes* deserve an explicit
  check at close-out.

## Carry Items

- **J40 — 6a-prime accepts a review that read nothing.** Filed `MONITORING`. The path fix (absolute
  paths in the prompt) is applied to this feature only; the protocol obligation — require ≥1
  successful tool call in the run's `--log` before recording `READY_TO_MERGE` — is unwritten. Note
  it must count *any* successful tool call: agy used `view_file`/`grep_search` on one dispatch and
  `run_command` on the next, and a hardcoded tool-name check reported a false zero.
- **`test_verb_no_self_invocation` has no mutation coverage.** Accepted, not fixed: the natural
  mutation recurses without bound, and the assertion may be structurally immune. Recorded rather
  than implied clean.
- **`PREFLIGHT: FAIL unresolved=codex,agy`** in this worktree is cosmetic — zero candidate panes,
  and `exec` is pane-independent and was proven live. Do not launch panes to green it.

## Version History
- v1.0: Initial report. Metrics derived from disk via `h_mad_cycle_counts.py` after the J42 fix;
  the pre-fix reading was `0/0/0`.
