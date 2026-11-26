# omc-codex-mcp-no-type: RETIRED 2026-11-26 (OMC 5.8.9)

This local patch stopped OMC writing a `type` key into the `[mcp_servers.<name>]` blocks it
manages in `$CODEX_HOME/config.toml`. Codex has no such key and printed
`Codex is ignoring 2 unrecognized configuration settings` on every run. Upstream:
[Yeachan-Heo/oh-my-claudecode#4899](https://github.com/Yeachan-Heo/oh-my-claudecode/issues/4899),
fixed in source by #4903; the compiled build stayed unfixed through 5.8.3 and 5.8.4.

## Why it was retired

Measured on 2026-11-26, with OMC 5.8.9 installed in the plugin cache and as the global npm
`oh-my-claude-sisyphus@5.8.9`:

- `verify.py` reported `MISSING` on all 4 runtime files **without** `renderer still emits N type
  lines`: the real renderer, fed entries that carry `type`, emitted none. This was the retirement
  condition this README set.
- `upstream.py --tag v5.8.9`: `UPSTREAM: FIXED` on the tag and npm tarball, both files each.
- The installed `dist/installer/mcp-registry.js` and `bridge/cli.cjs` (plugin cache and npm) each
  contain 0 `type = ${…}` emissions and still define `renderCodexServerBlock`.
- Neither `~/.codex/config.toml` nor the Orca account home's `config.toml` carries a stale
  `type =` line, so no hand cleanup was owed (OMC never deletes one that is already there).

## What was removed

`apply.py`, `verify.py`, `upstream.py`, `targets.py` and `tests/` (with their `pytest.ini`
testpaths entry). The SessionStart hook `docs/patches/patch-verify-on-update.sh` discovers
patches by `*/verify.py`, so it no longer checks this one; its npm fingerprint block
(`NPM_FILES`, `PATCH_VERIFY_NPM_ROOT`), which existed only for this patch, was removed too.
The scripts are in git history before this commit.

## If the warning comes back

Run a real `codex exec … </dev/null` with stderr captured (`codex mcp list` never prints it) and
grep the installed OMC `dist/` and `bridge/cli.cjs` for a `type = ${` emission. The registry-data
workaround (no `"type"` in `~/.omc/mcp-registry.json`) is user data and still in place.
