# omc-codex-mcp-no-type: stop OMC writing `type` into Codex MCP blocks

**Status:** applied locally on 2026-11-09 (OMC 5.8.0). Retire it once upstream fixes this; see "Retiring" below.
**2026-11-10, OMC 5.8.3:** NOT retirable yet. #4903 (merged to `dev`, contained in the v5.8.3 tag) fixed only `src/installer/mcp-registry.ts`. The compiled `dist/installer/mcp-registry.js` in the same tag, and the npm `oh-my-claude-sisyphus@5.8.3` tarball (`gitHead 73e0d61`), still contain `lines.push(`type = ${renderTomlString(entry.type)}`)`. The auto-update to 5.8.3 dropped the patch (`verify.py`: MISSING, renderer emits 2 `type` lines). It was re-applied (`VERIFY: OK files=4`).
**Upstream:** [Yeachan-Heo/oh-my-claudecode#4899](https://github.com/Yeachan-Heo/oh-my-claudecode/issues/4899)

## The problem

`renderCodexServerBlock()` (`src/installer/mcp-registry.ts:877` upstream) copies a registry entry's `type` into the managed `[mcp_servers.<name>]` block it writes to `$CODEX_HOME/config.toml`. Codex 0.167 has no such key. On every run it prints:

```
warning: Codex is ignoring 2 unrecognized configuration settings. Check for typos or deprecated settings.
  user (<CODEX_HOME>/config.toml): `mcp_servers.context7.type` is ignored.
```

Measured on 2026-11-09 with config-only temp `CODEX_HOME`s. All of `type = "stdio"`, `"http"` and `"streamable-http"` are ignored. A `url` entry with no `type` still runs as HTTP, so Codex never needs the key.

The registry-data workaround has already been applied: `"type"` was removed from `~/.omc/mcp-registry.json`. This patch covers the code path, so a registry entry that gets a `type` back (for example from a fresh bootstrap of Claude's config) cannot bring the warning back.

## What the patch does

It replaces the one emission line in each runtime copy:

```js
lines.push(`type = ${renderTomlString(entry.type)}`);   // entry2 in bridge/cli.cjs
```

with the marker comment `/* omc-codex-mcp-no-type: codex ignores mcp_servers.*.type (OMC #4899) */`.

Nothing else changes. The parse and compare side (`codexEntriesEqual`) already treats a missing Codex `type` as the inferred transport. So both codex homes stay in sync with no rewrite churn (`inspectUnifiedMcpRegistrySync().codexMismatched == []`, checked after patching).

**Not covered:** OMC still never deletes a `type` line that is already in a Codex file (the second half of #4899). Existing lines must be removed by hand once.

## Targets

`targets.py` finds them at run time:

- the active plugin install from `~/.claude/plugins/installed_plugins.json` (`oh-my-claudecode@*`): `dist/installer/mcp-registry.js` and `bridge/cli.cjs`
- the global npm CLI `/opt/homebrew/lib/node_modules/oh-my-claude-sisyphus` (`omc`): the same two files

`~/.claude/plugins/marketplaces/omc/src/` is the upstream git clone. It does not run and is not patched.

## Re-apply after an update

```bash
python3 /Users/kimhawk/orca/skills/docs/patches/omc-codex-mcp-no-type/apply.py    # idempotent
python3 /Users/kimhawk/orca/skills/docs/patches/omc-codex-mcp-no-type/verify.py   # expect VERIFY: OK
```

`apply.py` refuses a file whose emission line does not match exactly once (exit 2, nothing written). That means upstream changed the code: re-read it before forcing anything. The first apply leaves a `*.pre-omc-codex-mcp-no-type` backup beside each file.

`verify.py` exit codes: 0 = patched everywhere, and the real renderer, fed entries that carry `type`, emits 2 server blocks and 0 `type` lines; 1 = MISSING; 2 = could not judge, which is not a pass. Before the patch it reported MISSING on all 4 files and "renderer still emits 2 type lines" (the control).

The SessionStart hook `patch-verify-on-update.sh` runs `verify.py` whenever its fingerprint changes. Since 2026-11-09 that fingerprint also covers the npm package: `package.json` plus the mtime and size of the 2 patched files (`NPM_FILES` in the hook). So a `npm update -g oh-my-claude-sisyphus`, or a same-version reinstall, triggers a re-check. Measured: with the npm `cli.cjs` reverted to unpatched, the previous hook stayed silent and the new one reported `omc-codex-mcp-no-type: patch MISSING`.

## Retiring

When #4899 is fixed in a released OMC: update, run `verify.py`. It will report MISSING, because the marker is gone. Then grep the new renderer: if no `type =` emission is left, delete this directory and mark it RETIRED here.

Grep the **installed `dist/` and `bridge/cli.cjs`**, not the upstream source or the release notes. 5.8.3 shipped a fixed `.ts` with a stale build. `verify.py`'s real-renderer check settles it: after an update, `MISSING` together with `renderer still emits N type lines` means the build is still unfixed, so re-apply.
