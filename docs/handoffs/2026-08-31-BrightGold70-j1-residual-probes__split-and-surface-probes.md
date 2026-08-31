# Handoff — J1 residuals: the two response shapes nobody has measured

**Date:** 2026-08-31
**Branch:** `BrightGold70/j1-residual-probes`
**Project:** `/Users/kimhawk/orca/skills` (h-mad)
**Handover-From:** skills · main · session dbb07b5d-3005-4ef1-8bfc-4199894b1e15

## Session Summary

The J1 pane-pin item was taken over on `main` today and its **code half is finished and merged** —
`exec-pane` now joins by `paneKey` like `launch` does, with a spec and a green suite. What is handed
over is the half that was deliberately **not** guessed at: two response shapes that no probe in this
repo has ever seen, both of which the finished work depends on being wrong about only in one
direction. Nothing is blocked, nothing is claimed, and the claim on
`j1-launch-pane-pin-durability` was **released** before this brief was written. Do not re-derive the
completed half — re-verify it cheaply (below) and spend the session on the two probes.

## What is already DONE — do not redo

On `main`, all pushed:

| Commit | What |
|---|---|
| `a53b07c` | Took over the inbound HemaSuite brief (it was untracked) |
| `c9b57fa` | Filed the paneKey probe results in `docs/skill-candidates.md` |
| `cb4f046` | Date-scoped the J1 "placeholder" claim across 5 sites |
| `21c796e` | `exec-pane` resolves its created pane by `paneKey`, with fallback |
| `e42c776` | Persisted the 3 mutants as `mutation-specs/exec_pane_panekey.json` |

Verified at handover: full h-mad suite **2281 passed** (`RUN_RC` captured on the command, not read
from a background notification), spec **ALL_CAUGHT 3/3**, anchors **ANCHORS_OK specs=29
mutations=340 ok=340 drifted=0**.

## The two things being handed over

### 1. `.result.split.handle` — a sibling of the bug that was just fixed, unprobed

`hmad-dispatch.sh` `_cmd_exec_pane`'s `--split` branch reads a handle out of `.result.split`, a
**different object** from the `.result.terminal` the create branch reads, and pools it via
`_pane_slot_register` the same way. The create branch was just changed to stop trusting its handle
(J1: it has been observed to be a pre-adoption placeholder the pane never adopts). The split branch
still trusts its own.

This was left alone **on purpose**, and the reason is the task, not an excuse: nobody has ever
looked at a split response. Whether it even carries a `paneKey` is unknown, and writing a join
against a field nobody has seen is how a guard gets built on an imagined shape. So:

```bash
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
# create a throwaway pane, split it, and read the RAW response — the whole object, not two fields
H=$(orca terminal create --worktree active --command 'sleep 300' --title j1-split-probe --json \
      | jq -r '.result.terminal.handle')
orca terminal split --terminal "$H" --direction right --command 'sleep 300' --json | jq '.result'
orca terminal list --json | jq -r '.result.terminals[] | "\(.handle) \(.tabId):\(.leafId)"'
orca terminal close --terminal "$H" --tab      # clean up BOTH panes when done
```

Decide from what comes back, not from symmetry with `create`:
- carries a `paneKey` that joins → route it through the existing `_resolve_pane_by_key` helper, same
  fallback contract as the create branch, and add the mutants to `exec_pane_panekey.json`.
- carries no `paneKey` → there is nothing to join on; record the shape in
  `docs/skill-candidates.md` under the existing `2026-08-31 — j1-launch-pane-pin` heading and close
  the row. That is a real outcome, not a failure.

### 2. The missing `paneKey` — REPRODUCED at handover, and `surface` is not the cause

**This item changed while the handover was being delivered. Read this instead of the framing you
may have seen elsewhere.**

The inherited hypothesis was that a response omits `paneKey` when the UI cannot adopt the pane —
`orca terminal create --help` says it *"falls back to a background handle if the UI cannot adopt
it"* — and that it had never been induced. Creating the agent terminal for **this very worktree**
induced it:

```
orca terminal create --worktree id:47c13b8f-…::/Users/kimhawk/orca/workspaces/skills/j1-residual-probes \
  --title j1-residual-probes --command 'codex' --json
  -> {"handle":"term_69165bc9-686b-4298-9e01-15c3dfa599e8","paneKey":null,"surface":"visible"}
```

Three things follow, and the second is the one that matters most:

1. **The guard is not dormant.** `hmad-dispatch launch` against that create would have refused, and
   `exec-pane` would have taken its fallback. Do not delete the no-`paneKey` guard.
2. **`surface` does NOT discriminate.** The failing response carried `"surface":"visible"`, so the
   adopt-failure/background-handle hypothesis is **falsified as stated**. Anyone continuing this
   should not go looking for a `surface` value that predicts the omission; there isn't one in the
   evidence.
3. **The create handle was REAL.** `term_69165bc9…` appears in `terminal list` exactly once, with a
   `tabId`/`leafId`. So this instance is the *inverse* of the original J1 report: the response
   omitted the key while the handle was genuine. Refusing to pin would have been the wrong call
   here, which is precisely why `exec-pane` falls back rather than refusing.

**What was ruled out** — two immediate isolation probes, both `surface: visible`, both with a
`paneKey`:

| Probe | Condition | `paneKey` |
|---|---|---|
| P6 | same brand-new worktree, `path:` selector, `--command 'sleep 300'` | present |
| P7 | pre-existing worktree, `id:` selector | present |

So neither "the worktree is new" nor "the `id:` selector" is sufficient on its own. Tally across
the day: **1 omission in 8 creates.** The one difference not yet ruled out is timing — the failing
call was issued seconds after `worktree create`, while that worktree's UI was still materialising,
whereas P6 into the same worktree came later and succeeded. That is a hypothesis, not a finding;
it has n=1 and must be treated as such.

Next probe worth running: create repeatedly and immediately after `worktree create`, N≈10, and see
whether the omission tracks elapsed time since the worktree appeared. If it does, the guard's
message should say "retry" rather than "pin manually". If it does not, record the rate and stop —
an intermittent upstream omission with a working fallback on both call sites is a filed bug, not a
blocker, and is worth reporting upstream the way `stablyai/orca#13005` was.

## Key Learnings

- **A create-response field can be right and still be the wrong thing to trust.** The J1 doc claimed
  `.result.terminal.handle` is "a pre-adoption placeholder the pane never has (confirmed 3×)". On
  1.4.192 it equalled the adopted handle **5/5**. Both observations are real; the claim was written
  in the wrong tense. The paneKey join is kept because it is correct under **both** behaviours — an
  argument that survives the next Orca build, unlike the falsified invariant it replaced.
- **`launch` and `exec-pane` disagree on failure deliberately.** `launch` refuses a missing
  `paneKey` (its product is a durable pin; a wrong value poisons the session). `exec-pane` warns and
  falls back (its product is a dispatch already running; refusing strands live work). If you find
  yourself "fixing" that inconsistency, read the comment above each call site first — a fail-loud
  `exec-pane` passes a "resolves by paneKey" test and breaks every host build that omits the field.
- **Two of my own measurements read as success while being wrong**, both worth copying as habits:
  a mutant that appended `; true` inside a command substitution produced an empty `resolved` — the
  fallback the test already expects — so it landed on the same behaviour and *survived while proving
  nothing*; and a hand-run anchor sweep reported `ANCHORS_NOTHING_SWEPT` purely because **zsh does
  not word-split unquoted expansions**, sending all 86 paths as one argument. Run sweeps under
  `bash -c` with `mapfile`.
- **`orca terminal read` beats previews for pane identity.** `hmad-dispatch env` reported
  `codex -> UNRESOLVED` over 3 candidates that Orca named in no `agents[]` and whose previews were
  empty. `.result.terminal.tail` identified all three on the first try. The field is `tail` —
  `.content` / `.output` / `.preview` are all absent and return nothing in a way that looks exactly
  like an empty pane.

## Next Steps

1. Probe the split response shape — commands in §1 above. Close the row either way.
2. Attempt to induce `surface: background`; record "not inducible" if that is the answer — `h-mad/scripts/hmad-dispatch.sh` (no-paneKey guard) stays regardless.
3. Reconcile `docs/skill-candidates.md` under the `2026-08-31 — j1-launch-pane-pin` heading with whatever both probes return — that file is the item's durable home, replacing the TodoList `#54` that pointed at nothing for two sessions.

## Open / Blocked Items

- **Both items above** — status: not started, not blocked. Neither has a dependency; run them in either order.
  - `repo: /Users/kimhawk/orca/skills · branch: BrightGold70/j1-residual-probes · worktree: /Users/kimhawk/orca/workspaces/skills/j1-residual-probes`
  - Code: `h-mad/scripts/hmad-dispatch.sh` (`_cmd_exec_pane` split branch; `_resolve_pane_by_key`)
  - Tests: `h-mad/tests/test_hmad_dispatch_exec_pane.py`, spec `h-mad/tests/mutation-specs/exec_pane_panekey.json`
  - Row: `docs/skill-candidates.md`, heading `2026-08-31 — j1-launch-pane-pin (takeover probe)`
- **Claim** — `j1-launch-pane-pin-durability` in `docs/.bkit-memory.json` was **released** by the
  sender before this brief was written. It is free; claim it on takeover rather than reaching for
  `--force`.

## Context for Next Session

**Uncommitted changes:** none. `main` is clean and 0/0 with origin at `e42c776`.

**To resume:**
```bash
cd /Users/kimhawk/orca/workspaces/skills/j1-residual-probes
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
git log --oneline -5                      # a53b07c..e42c776 is the finished half
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/exec_pane_panekey.json
# expect: MUTATION: ALL_CAUGHT mutations=3 caught=3 survived=0
```

**Related docs:**
- `docs/handoffs/2026-08-31-main__j1-launch-pane-pin-durability.md` — the inbound brief this one succeeds
- `h-mad/references/agent-substrate.md:27` — the `launch` row, now date-scoped
- `docs/skill-candidates.md` — the durable row for this item
