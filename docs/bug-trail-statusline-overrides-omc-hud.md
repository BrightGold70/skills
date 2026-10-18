# trail (graft) silently replaces the OMC HUD status line

**Observed:** 2026-10-18, trail `0.23.0`, Claude Code `2.1.302`, oh-my-claudecode HUD.
**Status:** root cause confirmed in trail's shipped code. Workaround applied on this Mac
2026-10-18 (both parts; backups `~/.claude/settings.json.bak3`,
`.claude/settings.local.json.bak`). Not reported upstream.

## Conclusion

The OMC HUD is not broken: its files and its `statusLine` entry in `~/.claude/settings.json` are
intact. It is **overridden per repo**. trail writes its own `statusLine` into the repo's
`.claude/settings.local.json`. Claude Code honours only one status line, and project-local
settings outrank user settings, so in every repo trail wires, trail's bar replaces the HUD.

It keeps coming back because trail rewires repos at session start on its own: when a
graft-wired repo first sees trail installed, and again on every trail version change. Each
rewire writes the status line again.

## Mechanism (trail 0.23.0, `$(npm root -g)/@trailhq/trail-code/dist/`)

1. **The guard is blind to scope.** `claude/settings-merge.js` `mergeTrailLocal(existing)` adds
   `statusLine` / `subagentStatusLine` whenever `existing` (the **repo-local** file it is about to
   write) has none:

   ```js
   if (!merged[key]) merged[key] = { type: 'command', command: TRAIL_SL_CMD };
   else if (key === 'statusLine') warnings.push('Existing statusLine left untouched …');
   ```

   `claude/init.js` `runTrailInit` feeds it `readSettings(local)` only. The user-level
   `~/.claude/settings.json`, where OMC installs its HUD, is never read. So the "leave an
   existing statusLine alone" promise never fires for an OMC user, and no warning is printed.

2. **Rewiring happens with nobody asking.** trail's global `SessionStart` hook
   (`~/.claude/helpers/graft-hooks.cjs session-start` → `claude/hooks.js` → `runUpkeep`), and its
   MCP server's startup, call `reconcileWiring` (`upkeep.js`). That re-runs init for every wired
   host when
   - the stamp's version differs from the running trail (every upgrade), or
   - `shouldMoveToTrail(repo)` is true: trail is now installed in a repo graft wired.

   It replays the stamp's `opts`, and `DEFAULT_WIRING_OPTS.statusline` is `true`. The stamp lives
   at `.trail/cache/.cache/wiring-stamp.json` (formerly `graft/.cache/`).

3. **Evidence in this repo.** `.claude/settings.local.json`, `.trail/statusline.cjs`,
   `GEMINI.md` and `~/.claude/helpers/graft-hooks.cjs` share one mtime, 12:30:38 KST, which equals
   the stamp's `"at": "2026-10-18T03:30:38Z"`. The stamp records hosts `agents, antigravity,
   claude, gemini, grok` and `statusline: true`. The same rewire added 6 graft hook entries to
   `~/.claude/settings.json` and changed nothing else there: no OMC hook removed, and
   `statusLine` untouched.

## Fix

Two parts. Doing only the first lets the next trail upgrade put the override back.

1. **Stop future rewires from claiming the status line.** Add to the `env` block of
   `~/.claude/settings.json`:

   ```json
   "GRAFT_NO_STATUSLINE": "1"
   ```

   trail reads this name under both brands (`envNoStatusline()` in `settings-merge.js`). With it
   set, a rewire *removes* trail's own status line, because `withoutOurs()` strips any
   `statusLine` matching `(graft|trail)-statusline.cjs|.trail/statusline.cjs`, and does not add it
   back. This relies on the hook processes inheriting the `env` block. That is expected but was
   **not tested** here: after a restart, confirm with a session that a later rewire leaves no
   `statusLine` in the repo's local file.

2. **Remove the override already written**, in each affected repo: delete the `statusLine` and
   `subagentStatusLine` keys from `<repo>/.claude/settings.local.json`, keeping the rest (trail's
   allowlist and `footerLinksRegexes`). Then restart Claude Code.

   Alternative per repo: `trail init --no-statusline`, which also records `statusline: false` in
   the stamp.

**Find affected repos:**

```bash
bash -c 'find ~/orca ~/Coding -maxdepth 4 -path "*/.claude/settings.local.json" 2>/dev/null \
  | xargs grep -l "statusline.cjs"'
```

On 2026-10-18 only `/Users/kimhawk/orca/skills` matched, and it was the only trail/graft-wired
repo found (`wiring-stamp.json` search).

## Watch out

- `claude plugin list` and similar report a fresh process. A running session keeps the status
  line it started with, so check after a restart.
- Wanting both bars means writing a wrapper command that runs the HUD and trail's
  `.trail/statusline.cjs` and joins their output. Claude Code itself takes one `statusLine` only.
- Separately, `.mcp.json` was deleted and `AGENTS.md`/`opencode.json` were modified in this repo at
  12:42:47, 12 minutes after the rewire. Whether trail did that (its MCP server also runs upkeep)
  was not investigated.
- Upstream fix to propose: `mergeTrailLocal` should consult the effective `statusLine` from user
  and project scopes, not just the file it writes, and print its warning when it defers.
