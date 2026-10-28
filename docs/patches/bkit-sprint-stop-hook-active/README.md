# bkit sprint Stop handler — do not block a turn that is already continuing

**Status:** APPLIED locally to bkit `2.1.40` on 2026-10-29 (`2.1.38` is a symlink to it on this Mac).
**Why:** Claude Code sets `stop_hook_active: true` on a Stop payload when the turn is already
continuing because a Stop hook blocked, and documents checking it "to avoid blocking on a
condition that will never resolve" (`code.claude.com/docs/en/hooks.md`, Stop input). bkit's
`scripts/sprint-skill-stop.js` never reads it: after a `/sprint` operation on an active sprint it
returns `{decision:'block', reason:<executive summary>}`, and it returns the same block again on the
continued turn. Measured 2026-10-29 by driving the real `scripts/unified-stop.js`: with an active
sprint it blocked with `stop_hook_active` both `false` and `true`.
**Target file:** `~/.claude/plugins/cache/bkit-marketplace/bkit/<version>/scripts/sprint-skill-stop.js`
**Coexists with:** `../bkit-subagentstop-additionalcontext/` and the other bkit patches here (different files).

## Scope — why one handler and not five

`lib/core/io.js` `outputStopSurface` (`decision:'block'`) is also called by `pdca-skill-stop.js`,
`plan-plus-stop.js`, `gap-detector-stop.js` and `iterator-stop.js`. None of those four can block:
each begins with the bare-require guard `if (require.main !== module) { module.exports = {}; return; }`,
`unified-stop.js` (the only `Stop` entry in `hooks/hooks.json`) loads them with `require()`, and no
skill or agent frontmatter registers them directly. Driving `unified-stop.js` with each of them
active produced no stdout at all, with `stop_hook_active` false or true. A guard there could never
run, so this patch does not add one. `sprint-skill-stop.js` is reachable because it exports `run()`,
which `unified-stop.js` calls.

Earlier text in this repository (the `ea21a222` `h-mad/SKILL.md` bullet) and the first version of
upstream issue `ww-w-ai/bkit-claude-code#162` named all five as blocking handlers. That was read off
the source, not run; it is corrected here, in `h-mad/SKILL.md`, and in a comment on #162.

## What changes

| Stop payload, active sprint after a `/sprint` operation | upstream | patched |
|---|---|---|
| `stop_hook_active: false` (first stop) | `decision:block` + summary | unchanged |
| `stop_hook_active: true` (turn already continuing) | `decision:block` again | `{}` (clean stop) |

`run()`'s `finally` still clears the active-skill marker on the guarded path. In a real session the
handler is reached through that consume-once marker, which already bounds the loop; the guard makes
the documented contract hold without relying on it.

## Re-applying after a bkit update

```bash
# 1. Did the update drop the patch?
node /Users/kimhawk/orca/skills/docs/patches/bkit-sprint-stop-hook-active/verify.js
#    exit 1 + "patch MISSING" => re-apply. exit 2 = CANNOT JUDGE (the control did not block,
#    e.g. the sprint state layout changed) — that is NOT a pass.

# 2. Re-apply (adjust <version>)
cd ~/.claude/plugins/cache/bkit-marketplace/bkit/<version>
patch -p1 --dry-run < /Users/kimhawk/orca/skills/docs/patches/bkit-sprint-stop-hook-active/sprint-skill-stop.patch
patch -p1           < /Users/kimhawk/orca/skills/docs/patches/bkit-sprint-stop-hook-active/sprint-skill-stop.patch

# 3. Confirm
node /Users/kimhawk/orca/skills/docs/patches/bkit-sprint-stop-hook-active/verify.js
```

Undo with `patch -p1 -R < …/sprint-skill-stop.patch`. **Each Mac needs it separately.**

## How `verify.js` decides

It runs the real `scripts/unified-stop.js` twice in a throwaway project holding one active sprint
(`.bkit/state/sprints/verify.json`), with `skill_name: "sprint"` and a `/sprint phase` message:

1. **Control:** `stop_hook_active: false` must still produce `decision:block`. If it does not, the
   script exits 2 (`CANNOT JUDGE`): "no block" would otherwise also pass when sprint never surfaces.
2. `stop_hook_active: true` must not produce `decision:block`.

## Verification evidence (2026-10-29)

- `verify.js` red-green on 2.1.40: before the patch `1/2`, control ok (exit 1); after it `2/2` (exit 0).
- `patch -p1 --dry-run` and `-R --dry-run` apply cleanly; `node --check` passes.
- bkit's own sprint tests, identical with and without the patch: `test/unit/sprint-skill-stop.test.js`
  20/20, `test/contract/sprint-skill-handler-registration.test.js` 5/5,
  `test/contract/v2122-stop-hook-output-schema.test.js` (all Stop emitters conform),
  `test/regression/enh-417-sprint-stop-false-report.test.js` 7/7.
- `../bkit-subagentstop-additionalcontext/verify.js` still OK (different file).
