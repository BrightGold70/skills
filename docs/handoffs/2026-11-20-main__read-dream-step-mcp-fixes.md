# Handoff — READ dream-age step shipped; codex and OMC MCP servers repaired

**Date:** 2026-11-20
**Branch:** main
**Project:** skills
**Supersedes:** 2026-11-20-main__memory-dream.md
**Next-Session Focus:** Confirm at session start that `plugin:oh-my-claudecode:t` now connects, then pick from the small backlog below.

## Session Summary

Resumed from the memory-dream handoff and closed its top item: the READ dream-age step is committed and pushed as `5746011c` after a full suite of 9256 passed. The first full run failed one host-construct parity test that the handoff's scoped run could not see, so the commit grew from 2 files to 6. Three environment repairs were also made outside the repo: the stale codex and agy Orca pins were re-pinned, codex's `ai-memory` and `serena` MCP startup failures were fixed and confirmed after a restart, and the OMC MCP server's "Connection closed" was traced to a missing `node_modules` and fixed. The OMC fix is proven by a direct probe only; this session's own connection was never retried.

## Key Learnings

- **A new Claude-only path in split-body skill text needs a registry entry and three adapter rows.** `handoff/references/read-mode.md` sits behind a split marker, so `h-mad/tests/host_parity.py` scans it as `handoff/SKILL.md`. Adding `$HOME/.claude/projects` there failed `test_live_registry_and_skill_files_are_clean` with `UNDECLARED_SKILL` and `UNREGISTERED`, while all 38 handoff tests passed. The fix is to list the skill under the construct in `h-mad/references/host-constructs.json` and add a row to each `<host>-runtime.md`.
- **OMC's plugin cache ships without `node_modules`.** `bridge/mcp-server.cjs` leaves 9 requires external (`zod-to-json-schema`, `ajv-formats`, `fast-uri` and others) and exits 1 in 0.3 s. Upstream's `scripts/plugin-setup.mjs` step 5 would install them, but nothing in the plugin's `hooks.json` or `plugin.json` runs it for a Claude Code cache install. Every cached version back to 5.7.30 had the same gap.
- **`ai-memory`'s stdio bridge avoids the token export.** The vendor's codex snippet uses `bearer_token_env_var = "AI_MEMORY_AUTH_TOKEN"`, which nothing exports where Orca launches codex. `ai-memory mcp-bridge --no-session-id --server-url …` reads the token from the data directory itself and listed 24 tools with the variable stripped.
- **Serena takes about 76 s to answer its first MCP request here** (measured while the full suite was running, so likely inflated). Codex's default startup timeout is 30 s.
- **A codex pane can be restarted in place without losing its Orca handle.** Read the old process's arguments with `ps -o command= -ww -p <pid>`, `/quit`, then re-run `codex --no-daemon` with the same six `-c` settings from the pane's shell. The handle and the pin stay valid.
- **Closing codex's warning view with F2 clears the status-line counter** even though the causes remain. The warnings return at the next start.

## Next Steps

1. **Confirm the OMC MCP server connects.** At the next Claude Code start the system notice should no longer list `plugin:oh-my-claudecode:t` as failed. If it does, run `node ~/.claude/plugins/cache/omc/oh-my-claudecode/5.8.4/bridge/mcp-server.cjs` and read stderr.
2. **Queue-note hook nits, once the HemaSuite lane is quiet.** The hook in `~/.claude/projects/-Users-kimhawk-orca-skills/memory/MEMORY.md` cites `main 37efbefeb`, which the note body lacks, so `dream_lint` reports `hooks=1`. The index is now 17,761 B, 261 over the 17,500 target. Add the sha to their status line and trim. Show the diff and get approval first; re-read before writing.
3. **Before any OMC update:** `python3 /Users/kimhawk/orca/skills/docs/patches/omc-codex-mcp-no-type/upstream.py`. Last read 2026-11-18: `EMITS` on 5.8.4. Not re-checked this session.
4. **After any OMC update:** in the new `~/.claude/plugins/cache/omc/oh-my-claudecode/<version>/` run `npm install --omit=dev --ignore-scripts`, then `npm rebuild better-sqlite3`. Never run `scripts/plugin-setup.mjs` (it overwrites `statusLine`).
5. **On the Macmini**, after `git pull`: copy `docs/patches/patch-verify-on-update.sh` to `~/.claude/hooks/`; `python3 docs/patches/codex-duplicate-handoff/verify.py --fix`; `python3 docs/patches/omc-codex-mcp-no-type/apply.py` then `verify.py`; `ln -s ~/orca/skills/memory-dream ~/.claude/skills/memory-dream`. The OMC `npm install` from step 4 is probably needed there too (not checked).
6. **Retire the OMC patch** once `upstream.py` reads `FIXED` (`docs/patches/omc-codex-mcp-no-type/README.md` §Retiring).

## Open / Blocked Items

**From this session:**
- **OMC MCP fix unconfirmed in a live session** — status: fixed by probe (initialize answered, 50 tools), awaiting next session start (Next Step 1). It adds 173 MB of `node_modules` and a `package-lock.json` to the 5.8.4 cache dir and lasts only until the next OMC update (Next Step 4).
- **npm reported `1 high severity vulnerability`** in OMC's dependency tree — status: not examined. `npm audit fix --force` was not run because it can break pinned versions.
- **Codex config edits outside the repo** — status: done, confirmed after restart (warnings 3 → 1). Files: `/Users/kimhawk/Library/Application Support/orca/codex-accounts/29a32904-80ea-407f-8b54-30bf2320ca0a/home/config.toml` (`ai-memory` via stdio bridge, `serena` `startup_timeout_sec = 180`) and `/Users/kimhawk/.codex/config.toml` (serena timeout only). Backups sit beside each as `config.toml.pre-mcp-warnings-20261120-105251`.
- **A later `ai-memory setup` may write the bearer-token form back** — status: open risk. `ai-memory install-mcp --client codex` still prints that form.
- **Codex `code_mode` under-development warning** — status: left alone, informational.
- **No ai-memory or serena tool was called from inside codex** — status: unverified. Evidence is the F2 warning view plus both servers running as children of the new codex process.
- **Serena's slow start (about 76 s)** — status: not investigated; the timeout was raised instead.
- **The codex pane was relaunched without its old `resume 01a1947a-c963-7592-86d5-fc23735a5d20` argument** — status: informational. The old session showed 0 tokens in and out. Codex moved from 0.169.1 to 0.170.0.
- **Orca pins** — status: done. `.h-mad/orca-pins.env` holds `codex=term_6dbcd56e-0d16-4dc4-aa21-f1f1b2b6d11a` and `agy=term_4fb1b762-3e75-40c3-95c5-c065be3e0659`; `hmad-dispatch env` read `PREFLIGHT: PASS`. Handles go stale when a pane is closed.
- **ai-memory flagged a never-ended session `2fafec5c-e52f-41aa-9ee3-829b6eb0a08c`** in this project at session start — status: not read. It may hold activity no handoff covers.
- **Scratch files** under `/private/tmp/claude-501/-Users-kimhawk-orca-skills/c10b8b07-4044-441a-bb2b-305ec37a352e/scratchpad/` (`fullsuite.log`, `fullsuite2.log`, MCP probe scripts, `codex_relaunch.txt`, npm logs) — temporary, safe to lose.

**Carried from 2026-11-20 (memory-dream):**
- **Next Step 1, commit the READ dream-age step:** closed — `5746011c`, pushed, full suite 9256 passed.
- **Next Step 2, queue-note hook nits:** unchanged, index now 17,761 B (Next Step 2).
- **Next Steps 3–5 (`upstream.py`, Macmini catch-up, retire the OMC patch):** unchanged (Next Steps 3, 5, 6).
- **Memory-store edits are outside the repo** (`~/.claude/projects/-Users-kimhawk-orca-skills/memory/`), backed up under `~/.claude/memory-dream-backups/`; newest full snapshot `20261119-105940-judgment`; nothing prunes before 2026-12-19: unchanged.
- **`dream_lint` now:** `links total=1032 RESOLVED=1022 DANGLING=10`, `orphans=0`, `hooks=1`, `last_dream=1d ago`, `index OK bytes=17761 frac=71%`.
- **10 dangling links kept as deliberate markers** (review-comment-dedup, wsg_task15_shipped, exec_missing_report_recovery, task12_m3_anchor_migration, sapphire_g_revision, unified_subsystem_consolidation_audit, asset-legend-native-citations, synopsis_resource_consumption, f6_quality_checker, bmad): unchanged, accepted.
- **AC-7 live run (asset-legend-native-citations):** handed over, owned by HemaSuite. Brief `/Users/kimhawk/orca/HemaSuite/docs/handoffs/2026-11-19-main__asset-legend-ac7-live-run.md`, taken over by HemaSuite session f9973721. Not ours; not re-checked.
- **HemaSuite #178 test leak:** owned by the HemaSuite lane, FYI only. Their Orca checkpoint this morning read "next: find #178 test leak, then #157 fixes".
- **Deferred memory-dream ideas** (a generic `split` subcommand, still the one open row in `docs/skill-candidates.md`; the rejected hook-older-than-body check): unchanged.
- **Older scratch dirs** under `/private/tmp/claude-501/` (`hookdev-*`, `prunedev-*`, `bkctl-*`, `dl-copy`, `readdream-*`, `readctl-*`, `hdl*`): unchanged, temporary.

**Carried from 2026-11-18 (omc-update-check), via the predecessor:**
- **OMC MCP server `plugin:oh-my-claudecode:t` "Connection closed":** cause found and fixed this session, pending confirmation (above).
- **OMC patch applied on MacStudio for 5.8.4** (4 runtime files, `*.pre-omc-codex-mcp-no-type` backups): re-verified today after the `npm install`, `VERIFY: OK files=4`.
- **`upstream.py` checks the GitHub tag and npm, not the marketplace cache build:** unchanged, accepted.
- **Codex config edits outside the repo from 11-18** (`[[skills.config]]` pins in `~/.codex/config.toml` and `$CODEX_HOME/config.toml`; Orca's `skills/handoff` copy deleted; backups in `/private/tmp/claude-501/-Users-kimhawk-orca-skills/a571186a-8d52-49d8-a61e-ac4740e2ac73/scratchpad/backup/`): unchanged. Today's edits touched the same two files but only the `mcp_servers` sections.
- **Orca copy may reappear if OMX setup re-runs; pins break on every Matt Pocock plugin update:** unchanged.
- **Known limits of `codex-duplicate-handoff`** (flow-mapping `{name: handoff}`, scan depth, plain-file race, nested/BOM SKILL.md): unchanged, accepted.
- **OMC patch exists only on MacStudio; the Macmini is unreachable by ssh from MacStudio** (do not retry): unchanged.
- **Older scratch artifacts** (`991d87bb…`, `a571186a…`, `b68348df…`, `013414ea…`, `f7b82980…`, 43 unreviewed scratch reports on another machine): unchanged, temporary.
- **`~/.claude.json` context7/sequential-thinking entries; edits outside the repo from 2026-11-09 (0 `type` lines):** unchanged, expected.
- **Two timing-based tests kept as fixed sleeps; Pyright `timeout=None` warning at `test_hmad_dispatch_exec_stamp.py:458`; opencode `$schema` change (`bd6a47ca`):** unchanged, accepted.
- **Hand-started Codex session still ungated; another hook in `.codex/hooks.json` withholds the bypass; two unanchored hook-trust plumbing lines; hard-link kinds differ by host (all DENY):** unchanged, accepted.
- **Rust toolchain `stable-aarch64-apple-darwin`; foreign PID 32561:** unchanged, informational.
- **Accepted items unchanged since 2026-11-08** (`argument_not_printable` NBSP/U+202F/ZWJ refusal; two unpinned `_enc` print sites; `unreadable-file` first; `crash_visible=0/0` on host specs; scout row `hand-applied-single-mutants`): unchanged.
- **Items closed in predecessors** (scratch-dir deletion `6df9db7a…`, `899d9bdf`/`cd885d09`, Macmini sync #16, dispatch `NOT enforced` watch, heartbeat flake + mutation row, codex `ignoring 2 unrecognized configuration settings`): unchanged.
- **HemaSuite drafting quality without `CLAUDE.md`:** handed over, owned by HemaSuite, unchanged.
- **Macmini untracked `GEMINI.md`, `.gemini/`, `.grok/`:** not carried, by operator choice. Never stage them.
- **Orca worktree comment:** this WRITE restamps it.

## Context for Next Session

**Files touched this session (committed in `5746011c`):**
- `handoff/references/read-mode.md`
- `handoff/tests/test_handoff_dream_lint_step.py`
- `h-mad/references/host-constructs.json`
- `handoff/references/codex-runtime.md`
- `handoff/references/agy-runtime.md`
- `handoff/references/grok-runtime.md`

**Outside the repo:** the two codex `config.toml` files and their backups; `~/.claude/plugins/cache/omc/oh-my-claudecode/5.8.4/node_modules` and `package-lock.json`; `.h-mad/orca-pins.env` (untracked).

**Uncommitted changes:** none before this handoff's own files.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch        # expect clean, in sync with origin/main
hmad-dispatch env                  # expect PREFLIGHT: PASS; re-pin if a pane was closed
python3 memory-dream/scripts/dream_lint.py ~/.claude/projects/-Users-kimhawk-orca-skills/memory
```

**Related docs:** `docs/handoffs/2026-11-20-main__memory-dream.md`; `docs/patches/omc-codex-mcp-no-type/README.md`; `h-mad/references/agent-substrate.md` (pin and launch verbs); `memory-dream/SKILL.md`.
