# token-weather

A Claude Code mod: a live forecast of the context window, drawn above the prompt —
fill percentage, a sparkline of recent turns, and a bar of what fills the window in
`/context`'s colours.

## Install on a Mac

The mod loads from `~/.claude/mods/token-weather`, which is a symlink into this
checkout, so a `git pull` updates it and the settings line is the same on every
machine.

```bash
# 1. Link the mod (adjust the checkout path if yours differs). If a real
#    ~/.claude/mods/token-weather directory already exists, move it away first:
#    `ln -sfn` onto a directory puts the link INSIDE it instead of replacing it.
mkdir -p ~/.claude/mods
ln -sfn ~/orca/skills/mods/token-weather ~/.claude/mods/token-weather

# 2. Register it: add to the "env" block of ~/.claude/settings.json
#      "CLAUDE_CODE_PLUGIN_DIRS": "/Users/<you>/.claude/mods/token-weather"
#    Several plugin folders are joined with ':'. Use an absolute path or ~.

# 3. Check it, then restart Claude Code
claude plugin validate ~/.claude/mods/token-weather
claude plugin test ~/.claude/mods/token-weather
```

A running session never picks up a newly registered mod — the plugin table is fixed
at launch — so restart after step 2. `claude plugin list` reports a fresh process,
not your session, and can say `loaded` while the session you are in has not.

## Files

- `.claude-plugin/plugin.json` — manifest
- `hooks/hooks.json` → `hooks/register.tsx` — the hooks module
- `hooks/weather.ts` — pure helpers; `hooks/weather.test.ts` tests them
- `types/index.d.ts` — the `$.state` contract

`.claude-plugin/types/` is written by Claude Code at every load (API typings for
`tsc -p`) and ignores itself; it is never committed.
