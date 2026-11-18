# Handoff — OMC update check: no release since 5.8.4, patch still needed

**Date:** 2026-11-18
**Branch:** main
**Project:** skills
**Supersedes:** 2026-11-12-main__omc-upstream-check.md
**Next-Session Focus:** Nothing in flight. Run `upstream.py` before the next OMC update; Macmini catch-up is optional.

## Session Summary

Resume-only session, with no code changes. The 2026-11-12 resume reconciled clean. The operator asked for todo #4 (check before any OMC update): there was no update to check for. Plugin `oh-my-claudecode@omc`, global npm `oh-my-claude-sisyphus` and the npm latest version were all **5.8.4**. Re-run on 2026-11-18 before writing this doc: still 5.8.4. `upstream.py` read `UPSTREAM: EMITS tag=v5.8.4 npm=5.8.4` and `verify.py` read `VERIFY: OK files=4`.

## Key Learnings

None worth recording. The only new fact is that OMC published no release between 11-12 and 11-18.

## Next Steps

None owed. Optional:

1. **When OMC publishes a release newer than 5.8.4, before updating:** `python3 /Users/kimhawk/orca/skills/docs/patches/omc-codex-mcp-no-type/upstream.py`. `EMITS` → update, then `apply.py` + `verify.py`. `FIXED` → README §Retiring. Check for a release with `npm view oh-my-claude-sisyphus version`.
2. **On the Macmini** (MacStudio cannot reach it by ssh), after `git pull`:
   - `cp /Users/kimhawk/orca/skills/docs/patches/patch-verify-on-update.sh ~/.claude/hooks/`
   - `python3 /Users/kimhawk/orca/skills/docs/patches/codex-duplicate-handoff/verify.py --fix`, then fix any `NOT FIXED` by hand per its README
   - `python3 /Users/kimhawk/orca/skills/docs/patches/omc-codex-mcp-no-type/apply.py`, then `verify.py`
3. **Retire the OMC patch** once `upstream.py` reads `FIXED`: `docs/patches/omc-codex-mcp-no-type/README.md` §Retiring.

## Open / Blocked Items

**From this session:**
- **OMC MCP server `plugin:oh-my-claudecode:t` failed to connect** ("Connection closed") in both the 11-12 and 11-18 starts of this session. Not investigated. The no-type patch's own `verify.py` passes, so the patch is not implicated by any evidence, but it is also not ruled out. Status: unexamined, informational.

**Carried from 2026-11-12 (omc-upstream-check):**
- **Next Step 1, run `upstream.py` before any OMC update:** done for the current state (no update exists). It stays a standing step, now Next Step 1.
- **Next Step 2, Macmini catch-up:** unchanged since 2026-11-11.
- **Next Step 3, retire the OMC patch:** still blocked on upstream (5.8.4 still emits, re-measured 2026-11-18).
- **OMC patch applied on MacStudio for 5.8.4** (4 runtime files, `*.pre-omc-codex-mcp-no-type` backups beside them; outside the repo): unchanged, `VERIFY: OK files=4` on 11-18.
- **`upstream.py` checks the GitHub tag and npm, not the plugin marketplace's cache build:** unchanged, accepted.
- **Scratch artifacts** in `/private/tmp/claude-501/-Users-kimhawk-orca-skills/991d87bb-7237-4449-80eb-f0db25ed87ca/scratchpad/`: unchanged, temporary.
- **Codex config edits outside the repo** (`[[skills.config]]` pins in `~/.codex/config.toml` and `$CODEX_HOME/config.toml`; Orca's `skills/handoff` copy deleted; backups in `/private/tmp/claude-501/-Users-kimhawk-orca-skills/a571186a-8d52-49d8-a61e-ac4740e2ac73/scratchpad/backup/`): unchanged. `codex-duplicate-handoff/verify.py` read `VERIFY: OK 2 Codex config(s)` on 11-12.
- **Orca copy may reappear if OMX setup re-runs:** unchanged; the DUPLICATE check warns.
- **Pins break on every Matt Pocock plugin update:** unchanged; the STALE check warns and `--fix` repoints.
- **Known limits of `codex-duplicate-handoff`** (flow-mapping `{name: handoff}`, scan depth `skills/<a>/<b>/`, plain-file race before `--fix`'s rename, Codex loader on nested/BOM SKILL.md unverified): unchanged, accepted.
- **Predecessor scratch artifacts** (`a571186a…/scratchpad/` review reports, suite logs, `mprev.mDCm`): unchanged, temporary.
- **OMC patch exists only on MacStudio:** unchanged (Macmini = Next Step 2).
- **`~/.claude.json` context7/sequential-thinking entries:** unchanged, expected.
- **Older scratchpad backups (`b68348df…`, `013414ea…`):** unchanged, temporary.
- **Edits outside the repo from 2026-11-09** (registry, two Codex configs, hook copy): unchanged; 0 `type` lines.
- **Two timing-based tests kept as fixed sleeps:** unchanged, accepted.
- **Pyright `timeout=None` warning** at `test_hmad_dispatch_exec_stamp.py:458`: unchanged, harmless.
- **opencode `$schema` change (`bd6a47ca`):** unchanged, informational.
- **Orca worktree comment:** this WRITE restamps it.
- **Hand-started Codex session still ungated:** unchanged, accepted.
- **Another hook in `.codex/hooks.json` withholds the bypass:** unchanged, by design.
- **Two unanchored hook-trust plumbing lines:** unchanged, accepted.
- **Rust toolchain `stable-aarch64-apple-darwin`:** unchanged, informational.
- **Hard-link kinds differ by host (all DENY):** unchanged, accepted.
- **Predecessor-machine scratch dirs (`f7b82980…`) and 43 unreviewed scratch `.md` reports:** unchanged, on another machine.
- **Foreign PID 32561:** informational, unchanged.
- **Accepted items, unchanged since 2026-11-08:** `argument_not_printable` refuses NBSP/U+202F/ZWJ; two unpinned `_enc` print sites; `unreadable-file` reported first; `crash_visible=0/0` on host specs; scout row `hand-applied-single-mutants` (no).
- **Items closed in predecessors:** unchanged (scratch-dir deletion `6df9db7a…`, commits `899d9bdf`/`cd885d09`, Macmini sync #16, dispatch `NOT enforced` watch, heartbeat flake + mutation row, codex `ignoring 2 unrecognized configuration settings`).
- **HemaSuite drafting quality without `CLAUDE.md`:** handed over, owned by HemaSuite. Unchanged.
- **Macmini untracked `GEMINI.md`, `.gemini/`, `.grok/`:** not carried, by operator choice. Never stage them.
- **The Macmini cannot be reached from MacStudio by ssh:** unchanged. Do not retry.

## Context for Next Session

**Files touched this session:** this handoff doc only.

**Uncommitted changes:** none (before this doc).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch
npm view oh-my-claude-sisyphus version                    # >5.8.4 means an update exists
python3 docs/patches/omc-codex-mcp-no-type/upstream.py   # EMITS until OMC ships a fixed build
python3 docs/patches/omc-codex-mcp-no-type/verify.py     # expect VERIFY: OK files=4 on MacStudio
python3 docs/patches/codex-duplicate-handoff/verify.py   # expect VERIFY: OK 2 Codex config(s)
```

**Related docs:**
- `docs/patches/omc-codex-mcp-no-type/README.md` (§Check upstream before updating, §Retiring)
- `docs/handoffs/2026-11-12-main__omc-upstream-check.md`
