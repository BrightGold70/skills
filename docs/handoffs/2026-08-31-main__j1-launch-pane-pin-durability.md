# Handoff — J1: `hmad-dispatch launch` cannot pin its pane, and the item tracking it evaporated

**Date:** 2026-08-31
**Branch:** `main`
**Project:** `/Users/kimhawk/orca/skills` (h-mad)
**Handover-From:** HemaSuite · feature/41-headless-nlm-auth-gating · session e66079ba-411b-4aae-af8f-97b8516a3654

## Session Summary

Handed over from a HemaSuite lane that carried this as "h-mad defect, NOT ours — hand over, do not
adopt" across at least two handoffs without the handover ever being performed. The work is a
**tracking failure plus an unresolved upstream premise**, not a code change that is owed today:
`hmad-dispatch launch <codex|agy>` still cannot pin a pane when Orca's create response omits
`paneKey`, the guard that makes that fail loud is correct and deliberate, and the only record that
the residual was being watched was a TodoList number (`#54`) in a session that has since ended.
Nothing is claimed, nothing is blocked, and the receiving lane's own newest handoff already reports
`Open / Blocked Items: None` — which is precisely the problem this brief fixes.

## What was actually verified this session

Re-probed rather than carried. All four hold as of `214450a` on `main`:

| Claim | Verdict | Evidence |
|---|---|---|
| The J1 guard exists and fails loud | **HOLDS** | `h-mad/scripts/hmad-dispatch.sh:889` emits `create response carries no paneKey, so the pane cannot be identified; nothing was pinned`, then `return 1` |
| It is pinned by a test | **HOLDS** | `h-mad/tests/test_hmad_dispatch.py:859` — `assert "carries no paneKey" in r.stderr` |
| It is documented | **HOLDS** | `h-mad/references/agent-substrate.md:27` — "`.result.terminal.handle` … is a pre-adoption placeholder the pane never has (J1, confirmed 3×)" |
| `#54` is tracked somewhere durable | **FALSE** | `grep -rn '#54' docs/` → zero hits. `#NN` in these handoffs are TodoList numbers, not GitHub issues; the owning session is gone |

**Correction to the inherited framing.** The HemaSuite handoff said "`hmad-dispatch launch codex`
cannot pin its pane" as though the wrapper were broken. It is not. `launch` *refuses* to pin
`.result.terminal.handle` because pinning that placeholder once made every later dispatch vanish
into a handle that never appeared in `terminal list` — the comment at `hmad-dispatch.sh:875-884`
records the direct probe. Failing loud **is** the fix. The residual defect is upstream: Orca's
`terminal create --json` response sometimes carries no `paneKey`, and h-mad cannot resolve identity
without it.

## Key Learnings

- **A TodoList number is not a tracking system.** This item was referenced as "todo #54" in another
  repo's handoff for at least two sessions. TodoList state does not survive `/clear`, so the
  reference pointed at nothing by the time anyone tried to follow it. Anything meant to outlive a
  session belongs in `docs/skill-candidates.md` or a handoff Open Item, never in a `#NN`.
- **"Hand over, do not adopt" is not a handover.** Writing that line in the *sender's* doc is a note
  to the sender. The receiving lane never saw it, and closed out with `Open / Blocked Items: None`
  on the same day. The location rule makes an item findable; only HANDOVER makes it found.
- **`PREFLIGHT`/`UNRESOLVED` is about panes, never about code.** Reading `codex -> UNRESOLVED` as a
  dispatch failure has previously cost 7 audit cycles and produced a false gate. `exec codex` is
  pane-independent and works headless regardless.

## Next Steps

1. **Decide whether the upstream premise still holds.** Nothing here re-probed Orca itself — only
   h-mad's handling of it. Run a real launch against a scratch worktree and read the raw response:
   `orca terminal create --worktree <sel> --command 'codex' --title codex --json | jq '.result.terminal | {paneKey, handle}'`.
   If `paneKey` is present and stable now, the guard is dormant and the row closes as a doc note.
   If absent, it is an Orca bug worth filing the way `stablyai/orca#13005` was.
2. **File it durably either way** — append a row to `docs/skill-candidates.md` under a
   `2026-08-31 — j1-launch-pane-pin` heading, so its status has a home that is not a session.
3. **Consider whether `pin-agents` should be the documented default.** `h-mad/references/agent-substrate.md:27`
   still presents `launch` as "the zero-manual durable identity path (H5)" while
   `hmad-dispatch.sh:860` says to use `pin`/`pin-agents` instead. Both halves of that doc claim
   should agree; today they do not.

## Open / Blocked Items

- **Upstream `paneKey` omission** — status: premise unverified this session. Not blocking: both
  documented workarounds work today. `pin-agents` (Pass-0 `agentType` join) resolves panes, and
  `exec codex --sandbox read-only` needs no pane at all.
- **Unrelated stale claim, FYI not a task** — `handoff-linked-worktree-commit` in
  `docs/.bkit-memory.json` is still owned by session `36032fe8-d90f-42cd-8ddb-965ece6c1dfb`,
  heartbeat `2026-08-29T20:23:58Z`, while its work merged at `4a86ed3`. Stale, takeable by plain
  `--claim`. Left alone deliberately — it is not the item being handed over, and releasing another
  lane's claim uninvited is not this brief's business.

## Context for Next Session

**Files that carry the defect:**
- `h-mad/scripts/hmad-dispatch.sh:860` (the "use `pin`/`pin-agents` instead" comment), `:875-889` (J1 guard)
- `h-mad/references/agent-substrate.md:27` (the `launch` row — the half that disagrees)
- `h-mad/tests/test_hmad_dispatch.py:859` (the pin)

**Uncommitted changes:** none introduced by this brief beyond the brief itself.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
python3 ~/.claude/skills/h-mad/scripts/h_mad_install_check.py   # INSTALL: PASS
grep -n 'carries no paneKey' h-mad/scripts/hmad-dispatch.sh
```

**Related docs:**
- `docs/handoffs/2026-08-02-main__wire-retro-verify-task5-parked.md` — the original J1 report
- `docs/handoffs/2026-08-20-main__audit-cycle-verb-phases-3-4.md:67` — `PREFLIGHT: FAIL unresolved` did not block 54 dispatches
- `docs/skill-candidates.md` — where step 2 files this
