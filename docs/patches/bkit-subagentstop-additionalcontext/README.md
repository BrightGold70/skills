# bkit SubagentStop — stop returning the next-action hint as `additionalContext`

**Status:** APPLIED locally to bkit `2.1.40` on 2026-10-28 (`2.1.38` is a symlink to it on this Mac).
**Why:** bkit's `SubagentStop` handler returns `hookSpecificOutput.additionalContext` —
`[SUGGEST] Sub-agent <type> completed. Next: /pdca analyze <feature>` — on every subagent stop, and
never reads `stop_hook_active`. Claude Code documents `SubagentStop` `additionalContext` as
"non-error feedback that keeps the subagent running" (`code.claude.com/docs/en/hooks.md`), under an
8-consecutive-continuation cap that resets each time the agent calls a tool. So every subagent that
reports is woken again, up to eight times, and an agent that acts on the hint can be woken without
limit. Measured 2026-10-28 on Claude Code 2.1.312: one stop of a `spec-author` probe drew 9 hints and
8 extra `DONE` turns; in HemaSuite one `plan-author` was re-woken 35 times across three dispatches.
The `<feature>` is bkit's own primary feature, usually derived from a directory name, so the hint is
never about the subagent's work. Full write-up: `h-mad/SKILL.md` §"Known interactions".
**Target file:** `~/.claude/plugins/cache/bkit-marketplace/bkit/<version>/scripts/subagent-stop-handler.js`
**Coexists with:** `../bkit-g004-protected-branch-precision/`, `../bkit-g001-bare-heredoc-substitution/`,
`../bkit-enh310-quoted-heredoc-body/` (different files).

## What changes

| output field | upstream | patched |
|---|---|---|
| `systemMessage` (shown to the user) | `Subagent <name> stopped (<status>)` + hint | unchanged |
| `hookSpecificOutput.additionalContext` (delivered to the stopped subagent) | the hint | **absent** |
| `hookSpecificOutput.agentId/agentName/agentType/status` | present | unchanged |

Team-state updates, progress, and the caching-cost telemetry earlier in the handler are untouched.

bkit's own code already takes this position for the main session: the ENH-482 comment in
`lib/core/io.js` (`outputAllow`) declines to deliver the `Stop` next-action hint because the only
channel that would deliver it "forces the turn to continue", calling that "a product decision, not a
bug fix". The `SubagentStop` handler bypasses `outputAllow` and does exactly that to every subagent.

## Re-applying after a bkit update

```bash
# 1. Did the update drop the patch?
node /Users/kimhawk/orca/skills/docs/patches/bkit-subagentstop-additionalcontext/verify.js
#    exit 1 + "patch MISSING" => re-apply. exit 2 = the check could not run (no hint was
#    generated, or the handler output did not parse) — that is NOT a pass. Check upstream's
#    handler first: if it now guards on stop_hook_active or drops additionalContext, drop this patch.

# 2. Re-apply (adjust <version>)
cd ~/.claude/plugins/cache/bkit-marketplace/bkit/<version>
patch -p1 --dry-run < /Users/kimhawk/orca/skills/docs/patches/bkit-subagentstop-additionalcontext/subagent-stop-handler.patch
patch -p1           < /Users/kimhawk/orca/skills/docs/patches/bkit-subagentstop-additionalcontext/subagent-stop-handler.patch

# 3. Confirm
node /Users/kimhawk/orca/skills/docs/patches/bkit-subagentstop-additionalcontext/verify.js
```

Undo with `patch -p1 -R < …/subagent-stop-handler.patch`. The hook spawns a fresh `node` per stop,
so the change takes effect without a restart. **Each Mac needs it separately.** The plugin cache is
machine-local.

## How `verify.js` decides

It runs the real handler as a subprocess on a SubagentStop payload, with `CLAUDE_PROJECT_DIR` set to
a throwaway project whose `.bkit/state/pdca-status.json` has a primary feature in phase `do`. Two
checks:

1. **Control:** the hint `/pdca analyze verify-probe` still appears in `systemMessage`. Without it,
   "no `additionalContext`" would also pass when no hint was generated at all, so a failed control
   exits 2 (`CANNOT JUDGE`), never 0.
2. `hookSpecificOutput` carries no `additionalContext` key.

## Verification evidence (2026-10-28)

- `verify.js` red-green on 2.1.40: before the patch `1/2 checks correct`, control ok (exit 1); after
  it `2/2` (exit 0).
- `patch -p1 --dry-run` and `patch -p1 -R --dry-run` both apply cleanly; `node --check` passes on the
  patched handler.
- bkit's own suites on patched 2.1.40: `test/contract/orchestrator.test.js` 23/23,
  `test/contract/l2-smoke.test.js` 104/104. `tests/qa/v2112-deep-qa-fixes.test.js` is 23 passed /
  5 failed **both with and without the patch** (byte-identical output modulo timings) — the five are
  `ENOENT` on `.bkit/runtime/control-state.json` inside the plugin cache, environmental and
  unrelated. No bkit test asserts `additionalContext` on this handler.
- Live: see "Live probe" below.

## Live probe

The same read-only `spec-author` probe (told to make no tool call after `DONE`), dispatched in
`orca/skills` before and after the patch, measured from its subagent transcript:

| | `SubagentStop` hints injected | `DONE` turns | tool calls after first `DONE` |
|---|---|---|---|
| unpatched (06:31Z) | 9 | 9 (1 answer + 8 re-wakes) | 0 |
| patched (07:31Z) | 0 | 1 | 0 |

## Upstream

Filed 2026-10-28 as https://github.com/ww-w-ai/bkit-claude-code/issues/162 (the repository moved
from `popup-studio-ai`). Posted text: `UPSTREAM-REPORT.md`. It also named five `Stop` handlers
that return `decision:block` without a `stop_hook_active` guard, and the sticky
`session.lastSkill` fallback in `unified-stop.js`. **Correction (2026-10-29):** only
`sprint-skill-stop.js` of those five is reachable from the Stop hook; the other four return at
their bare-require guard. Posted as a comment on #162; the sprint guard is carried in
`../bkit-sprint-stop-hook-active/`.
