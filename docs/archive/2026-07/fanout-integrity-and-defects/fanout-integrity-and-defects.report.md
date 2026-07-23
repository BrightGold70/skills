# Report: fanout-integrity-and-defects

## Executive Summary

The Phase-5 fanout can no longer silently destroy a worker's output, its two dispatch paths now
support the same orchestration verbs, and the two record-level defects that made a run's own
evidence untrustworthy — the epoch `started_ts` and the contentless `DONE_WITH_CONCERNS` — are
fixed.

## Summary

Wave 4's payload is designed to be fanned out, but J15 meant the fanout could destroy the work it
was carrying, so this feature repaired the instrument first. Four guards were added across three
scripts, each placed where its failure becomes irreversible rather than where prose could describe
it: `worktree-rm` refuses to remove a worktree holding uncommitted or unmerged work, and
`h_mad_extract_verdict.py` refuses to return a verdict that declares doubt without stating it.
100% match rate (9/9 FRs, 35/35 ACs), 592/592 tests against a 550 baseline, `READY_TO_MERGE`.

## Metrics

| Metric | Value |
|---|---|
| Plan audit cycles | 1 |
| Design audit cycles | 2 |
| Impl-plan audit cycles | 2 |
| Iterate cycles (Phase 6b) | 0 |
| Final match rate | 100% (9/9 FRs, 35/35 ACs) |
| 6a-prime architectural review | `READY_TO_MERGE` |
| Tests | 592 passing / 0 failing (baseline 550) |
| Phases with back-propagation | Phase 4 → Phase 2 (AC-5.1 narrowing); Phase 5a → Phase 2 (AC-7.6 added) |
| Elapsed | 70.9 min |

## What Went Well

- **Guarding the irreversible step worked where instructing the worker had not.** The filed J15 fix
  direction was "tell the fanout worker to commit". Both Wave-3 workers had already been told to
  self-review and neither committed. Putting the guard on `worktree-rm` means the work survives
  without anything needing to be read — the same reasoning that made Wave 3's send-refusal effective
  where Wave 2's mandated read was not.
- **`git status --porcelain` turned out to be the entire uncommitted test.** It reports staged,
  unstaged and untracked-non-ignored entries while honouring `.gitignore`, so AC-1.3 and AC-1.4 both
  fall out of one command with no filtering logic to get wrong. Verified empirically before it was
  written into the design.
- **Mutation testing found two guards that were passing while unenforced.** Neither was visible to
  review or to a green suite. The `--prompt-file` gate could be replaced with `true` and nothing
  failed, because `run()` strips `HMAD_ORCA_*`, so `task-create` bailed before calling `orca` and the
  capture stayed clean for the wrong reason. My own `--base` doc test passed with the guidance
  deleted. Both are now the only thing keeping their assertions green.
- **Replaying against history caught a bug that 14 synthetic cases missed.** A prefix-based concern
  label rejected the real form `Working-tree concern:` — discarding a report that *did* state its
  concern. The replay also measured the true rate: **7 of 13** historical `DONE_WITH_CONCERNS`
  reports name no concern, where J10 was filed on one instance.
- **Live testing found a gap no test would have.** Against a real Orca worktree, the guard reported
  7 commits ahead of `main` purely because the worktree branched from a feature branch — meaning
  teardown would refuse indefinitely and train the operator to reach for `--force`, the exact reflex
  J15 exists to prevent. Fixed by documenting `--base <feature-branch>`, with a discriminating test.
- **The Wave-3 receipt earned its keep twice mid-run.** Handles rotated twice (`stale=agy`, then
  `stale=codex,agy`) and both halted the run instead of dispatching into dead panes.

## What To Improve Next Time

- **Write the code before claiming the plan is complete.** The impl-plan's `...` placeholders were
  rejected by the audit, and writing the real implementation is what surfaced the label bug. A plan
  that defers the hard part hides its defects until an implementer inherits them.
- **A label comparison is not a coverage check.** Three ACs (6.2, 7.5, 7.6) have assertions without
  naming the AC; a label-only diff would have reported three false gaps, exactly as in Wave 3.
- **Suppressing stderr on an Orca call converts a loud error into a wrong conclusion.** Probing a
  pane with `--lines` (the flag is `--limit`) plus `2>/dev/null` rendered an `invalid_argument`
  envelope as an empty pane, briefly reading as "the agent is gone".
- **The documented reviewer cliff is now costing work.** Prompts of 52,997 B, 53,058 B and 58,536 B
  were all answered normally, against a documented 53,066 B "silent" point. A design audit was
  trimmed on the strength of that number. It needs re-measuring or removing (J13).

## Carry Items

- **J16 is an opportunity, not a defect, and it is the most valuable thing this run found.**
  `orca worktree ps` carries `agents[].agentType` keyed by `paneKey` (`<tabId>:<leafId>`), which
  joins to `terminal list`'s `tabId`/`leafId`. That is exactly the identity field
  [orca#9870](https://github.com/stablyai/orca/issues/9870) says does not exist — it is simply in a
  different call. It resolved two panes that both reported `title: "Codex - skills repo"` with empty
  previews and identical (reset) buffers, which no existing heuristic could separate. **Attempt this
  before Wave 5 continues waiting on #9870**, and report upstream; it may make the issue moot. Note
  `agentType` is `antigravity`, not `agy`.
- **Wave 4's remaining payload is untouched**: the two `invariants.base.md` discipline rules, the
  `file-issue-then-fix-under-TDD` tooling (recurrence 14), the staged-prompt repair sweep, the
  stub-harness probe, and the two `SKILL.md` prose notes. They can now be fanned out safely, which
  was the point of doing this first.
- **The `*) shift ;;` catch-all** silently drops unrecognised flags at 11 sites in
  `hmad-dispatch.sh`. Raised by the impl-plan audit, declined here as pre-existing and out of scope;
  if it changes it should change at all 11 sites as its own feature.
- **FR-2 under-protects on repos with no `origin/HEAD`, `main` or `master`** — the unmerged check is
  skipped rather than failed, by design (AC-2.4), because refusing on an undeterminable ref would
  break teardown everywhere. Stated rather than hidden.
- **Pre-existing Pyright warning** on `_remove_stray_pin_file` (an `atexit`-registered symbol);
  present on `main` before this feature, untouched.

## Version History
- v1.0: Initial report draft.
