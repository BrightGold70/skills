# Brainstorm: fanout-integrity-and-defects

## Executive Summary

Fix the four instrument defects that Wave 3 surfaced or carried — the fanout's ability to destroy
uncommitted work (J15), its two incompatible dispatch paths (J14), the epoch `started_ts` sentinel
(J8), and the contentless `DONE_WITH_CONCERNS` verdict (J10) — before Wave 4's candidate batch is
fanned out over that machinery.

## Problem Statement

Wave 4's payload is designed to be dispatched via the Phase-5 worktree fanout, but Wave 3's live run
proved the fanout can silently destroy a worker's output. Running the batch first would risk exactly
that. Two further defects (J8, J10) were already folded into Wave 4 and are diagnosed to a line.
All four are *the instrument*, so the sequence doc's own first ordering principle — "fix the
instrument before you measure" — applies to this wave as much as it did to Wave 1.

## Proposed Approach

Four independent fixes, each at the point where the failure actually becomes irreversible or
unactionable rather than at the point where prose could describe it.

- **J15 — guard `worktree-rm`.** It currently forwards straight to `orca worktree rm`
  (`hmad-dispatch.sh:709-717`) with no inspection whatsoever. Make it refuse (rc=1, nothing removed)
  when the worktree holds uncommitted changes, or holds commits not reachable from the base/target
  ref. `--force` overrides and says so. Guarding the *destructive* step means the work survives
  regardless of whether any instruction was read — the same reasoning that made Wave 3's send
  refusal actually work, where a mandated read had not.
- **J14 — remove the fork instead of documenting it.** `worktree-create --prompt-file` starts the
  agent immediately and yields no task-id, while `await` and `gate-create` both require one. Have
  `worktree-create` register a task as well and surface its id, so both paths support the same
  verbs. In Wave 3 this gap forced a worker-less task to be created purely to hang the merge gates
  on.
- **J8 — default `started_ts` to `now(UTC)`.** One line at `h_mad_state_write.py:138`. Existing rows
  stay wrong; the log is append-only history.
- **J10 — make the concern mandatory, and enforce it in the reader.** `h_mad_extract_verdict.py`
  accepts `DONE_WITH_CONCERNS` purely as a member of the allowed set (`:29`), with no visibility
  into whether a concern was stated. Make a contentless one raise the same error as a missing
  verdict, and state the obligation in `references/codex-implementer-prompt.md`.

## Alternatives Considered

- **J15 as prose only** ("tell the worker to commit") — the filed fix direction, rejected because
  both Wave-3 workers were *already* told to self-review and still committed nothing. An
  instruction that a worker can ignore leaves the data-loss path reachable; this repo has twice
  demonstrated that an unread instruction is worth nothing.
- **J15 with an additional pre-merge verb** — rejected as the primary mechanism for the same
  reason: a verb the merge gate *may* call is advisory. The irreversible-step guard subsumes the
  danger. (Refusing to remove a worktree whose commits are not in the target also catches the
  empty-merge case from the other side, which is the useful half.)
- **J10 downgraded to plain `DONE`** — rejected: it discards the signal. If the agent had a real
  concern and merely mis-formatted it, downgrading erases it, converting a loud problem into a
  silent one — the opposite of the fix's intent.
- **J14 documented as two modes** — honest and cheap, rejected because it leaves the simpler and
  more likely-used path permanently unable to record a merge gate.
- **Running the full Wave 4 batch in one feature** — rejected on ordering: it would have to run
  serially anyway (fanning out over an unfixed J15 is the hazard), which forfeits the batch's whole
  rationale.

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| The `worktree-rm` guard cannot resolve a selector to a filesystem path | H | Selectors take several forms (`<repoId>::<path>`, a name, an id, `active`). Resolve via `worktree-ps`/`worktree-current` rather than string-splitting on `::`; if the path cannot be resolved at all, that is *not* evidence of safety — decide the fail direction explicitly in design |
| Guarding `worktree-rm` breaks the documented fanout teardown, which is specified as idempotent | M | Teardown after a *clean* merge stays a no-op change (nothing uncommitted, commits reachable). Assert the happy path still removes, and that a gone selector still logs-and-no-ops |
| `worktree-create` emitting a task-id changes an existing stdout contract | M | Base Axis B protects backward compatibility; today it prints the selector. Decide in design whether to append, add a flag, or emit on separate lines — and pin the current behavior with a test first |
| J10's concern detection produces false positives on unusual phrasing | M | Fail-closed is deliberate; the cost is one loud re-dispatch. Define the negative set explicitly (absent / empty / none / n/a) rather than trying to judge substance |
| The J10 reader change breaks existing callers of `extract_verdict` | M | The function is called for three keys; only `STATUS` is affected, and only for one value. Needs the scrape body, which the CLI already has — but the pure function's signature may need to change |
| Fixing four defects at once obscures which one a regression came from | L | One task per defect, one commit per task, each with its own tests |

## Dependencies

None external. Builds on Wave 3 (`4111297`), on `main`. Touches `h-mad/scripts/hmad-dispatch.sh`,
`h-mad/scripts/h_mad_state_write.py`, `h-mad/scripts/h_mad_extract_verdict.py`, their tests, and
`h-mad/SKILL.md` + `references/orchestration-mode.md` + `references/codex-implementer-prompt.md`.

**Phase 5 runs serially.** The fanout is the thing under repair; using it to repair itself would be
the same category error as auditing the assembler with the assembler.

## Open Questions

- **How does `worktree-rm` resolve an arbitrary selector to a path?** And what is the fail direction
  when it cannot — refuse (safe, but breaks teardown when the listing is unreadable) or proceed
  (matches `_orca_handle_live`'s "only positive evidence blocks" stance, but leaves a hole)? The
  existing rc=2 philosophy argues for proceed; the data-loss severity argues for refuse. Resolve in
  design and justify.
- **What exactly is "commits not reachable from the base"?** The base ref is not recorded on the
  worktree by h-mad today. Derive it from the merge target, require it as an argument, or check only
  "has commits not in any local branch"? Resolve in design.
- **Does `worktree-create` gain the task-id unconditionally or behind a flag?** Depends on whether
  any existing caller parses its stdout.
- **Where does J10's concern check live** — inside `extract_verdict` (needs the whole scrape, not
  just the key) or as a separate validation the CLI applies after extraction? The latter keeps the
  pure function honest to its name.
- **Should `--force` on `worktree-rm` remain a single flag** that means both "orca, force it" and
  "h-mad, skip your guard", or do those need separating?

## Version History
- v1.0: Initial brainstorm draft.
