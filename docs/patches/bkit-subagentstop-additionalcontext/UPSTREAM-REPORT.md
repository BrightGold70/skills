# Upstream report — FILED

**Filed 2026-10-28:** https://github.com/ww-w-ai/bkit-claude-code/issues/162
(`popup-studio-ai/bkit-claude-code` now redirects to `ww-w-ai/bkit-claude-code`; the `bug` label
was requested but did not attach.)

The posted issue inlines the diff and a standalone reproduction, and omits all local paths. The
reproduction was run as posted against 2.1.40 before filing: unpatched it prints `additionalContext`,
patched the key is absent. Text below is the posted body.

If upstream ships the fix, drop the local patch rather than re-applying it.

---

## Title

SubagentStop handler returns next-action hint as additionalContext, re-waking every subagent up to 8x per stop

## Summary

`scripts/subagent-stop-handler.js` returns the next-action hint as `hookSpecificOutput.additionalContext` on every `SubagentStop`. Claude Code documents `additionalContext` on `SubagentStop` as feedback that **keeps the subagent running**, so every subagent that finishes is woken again with `[SUGGEST] Sub-agent <type> completed. Next: /pdca analyze <feature>` as a new turn — up to eight times per stop. The handler never reads `stop_hook_active`.

The hint is meant for the user (it is already in `systemMessage`), but `additionalContext` delivers it to the subagent that just stopped.

## What Claude Code documents

From the hooks reference (https://code.claude.com/docs/en/hooks), SubagentStop decision control:

> SubagentStop hooks use the same decision control format as Stop hooks, including `hookSpecificOutput.additionalContext` with `hookEventName` set to `"SubagentStop"`, for non-error feedback that keeps the subagent running.

and Stop input:

> Claude Code applies an 8-consecutive-continuation cap: after stop hooks have continued the turn eight times in a row, Claude Code overrides the next block and ends the turn. The count of consecutive continuations resets each time Claude calls a tool.

So a subagent that ignores the hint is woken 8 times per stop, and a subagent that *acts* on it (e.g. runs the suggested `/pdca analyze`, which is a tool call) resets the counter and can be woken without bound.

## Measured

Claude Code 2.1.312, bkit 2.1.40, macOS. Counted from the subagent transcript (`attachment.type == "hook_additional_context"` with `hookEvent: "SubagentStop"`, and the agent's assistant turns):

| run | SubagentStop hints delivered to the subagent | final-report turns |
|---|---|---|
| one stop of a read-only subagent | 9 (~2 s apart) | 9 (1 real answer + 8 re-wakes; the 9th hint was overridden by the cap) |
| one planning subagent over three dispatches | 36 | 27 DONE turns in three bursts of 9 |
| same read-only subagent, handler patched as below | 0 | 1 |

Each re-wake is a full model turn on the subagent's whole context (~120k tokens in the planning case). The `<feature>` in the hint is bkit's `primaryFeature`, which in our repositories was derived from a directory name (`tools`, `.claude`), so the suggestion is unrelated to the subagent's work.

## Reproduction (no Claude Code session needed)

Run the real handler against a throwaway project whose PDCA status has a primary feature in a phase:

```js
// repro.js — node repro.js <path-to-bkit>/scripts/subagent-stop-handler.js
const fs = require('fs'), os = require('os'), path = require('path');
const { spawnSync } = require('child_process');
const proj = fs.mkdtempSync(path.join(os.tmpdir(), 'bkit-repro-'));
fs.mkdirSync(path.join(proj, '.bkit/state'), { recursive: true });
fs.writeFileSync(path.join(proj, '.bkit/state/pdca-status.json'), JSON.stringify({
  version: '2.0', primaryFeature: 'demo', activeFeatures: ['demo'], features: { demo: { phase: 'do' } },
}));
const r = spawnSync('node', [process.argv[2]], {
  input: JSON.stringify({ hook_event_name: 'SubagentStop', stop_hook_active: false, agent_id: 'a1', agent_type: 'Explore' }),
  env: { ...process.env, CLAUDE_PROJECT_DIR: proj }, encoding: 'utf8',
});
console.log(JSON.parse(r.stdout.trim().split('\n').pop()).hookSpecificOutput);
```

Output on 2.1.40 includes `additionalContext: '[SUGGEST] Sub-agent Explore completed. Next: /pdca analyze demo'`; with the fix below, the key is absent.

## bkit already declines this for the main session

The ENH-482 comment in `lib/core/io.js` (`outputAllow`) explains that the `Stop` next-action hint in `unified-stop.js` is composed and never delivered, because the only channel that would deliver it (`decision: 'block'`) "forces the turn to continue" — "a product decision, not a bug fix". `subagent-stop-handler.js` bypasses `outputAllow` and builds its response directly, so it does exactly that to every subagent.

## Suggested fix

Drop `additionalContext` from the SubagentStop response and keep the hint in `systemMessage`:

```diff
--- a/scripts/subagent-stop-handler.js
+++ b/scripts/subagent-stop-handler.js
@@ -132,7 +132,6 @@
       agentName,
       agentType,
       status,
-      ...(nextActionHint ? { additionalContext: nextActionHint } : {}),
     }
   };
```

A `stop_hook_active` guard alone would not be enough here: the first continuation happens while `stop_hook_active` is still `false`, so every subagent would still get one extra turn. If a hint for the *parent* session is wanted, the docs point to a `PostToolUse` hook on the `Agent` tool instead.

With this change applied locally, `test/contract/orchestrator.test.js` (23/23) and `test/contract/l2-smoke.test.js` (104/104) still pass, and no bkit test asserts `additionalContext` on this handler.

## Related: Stop handlers without a loop guard

Five Stop handlers return `decision: 'block'` (via `outputStopSurface`) and none reads `stop_hook_active`: `pdca-skill-stop.js`, `plan-plus-stop.js`, `sprint-skill-stop.js`, `gap-detector-stop.js`, `iterator-stop.js`. Those continuations are intentional, but returning early when `stop_hook_active` is `true` would keep them to one continuation instead of relying on Claude Code's cap. Separately, `unified-stop.js` falls back to `pdcaStatus.session.lastSkill` when no live skill is found, so a stale `lastSkill: "pdca"` would route every main-session stop to a blocking handler.

## Environment

- bkit 2.1.40 (`hooks/hooks.json` → `SubagentStop` → `scripts/subagent-stop-handler.js`)
- Claude Code 2.1.312
- macOS
