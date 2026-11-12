# Handoff — OMC 5.8.4 dropped the no-type patch; re-applied, update test added, upstream.py checks tag + npm

**Date:** 2026-11-12
**Branch:** main
**Project:** skills
**Supersedes:** 2026-11-11-main__codex-single-handoff.md
**Next-Session Focus:** Nothing in flight. Before the next OMC update run `upstream.py`; optional Macmini catch-up.

## Session Summary

Started as a resume (2026-11-11) and found OMC 5.8.4 had auto-updated and dropped the `omc-codex-mcp-no-type` patch. Re-applied it on MacStudio (`VERIFY: OK files=4`), then added two safeguards, both pushed to `origin/main`:

- **`2cd772c4`**: tests that drive `roots()`' real `installed_plugins.json` lookup through an update to a fresh, unpatched version dir (fixture HOME + new `OMC_NPM_ROOT` override). Before this, every test bypassed the lookup via `OMC_PATCH_ROOTS`; a broken lookup would have read `VERIFY: OK files=2` from the patched npm copy alone.
- **`412f1078` + `0be56a8b`**: `docs/patches/omc-codex-mcp-no-type/upstream.py` checks the newest OMC release (or `--tag`) **before** updating: the compiled `dist/installer/mcp-registry.js` and `bridge/cli.cjs` from the GitHub tag (`gh api`) and from the npm tarball `oh-my-claude-sisyphus@<ver>` (`npm pack`, read in memory). One verdict over 4 files: `EMITS` 1 / `FIXED` 0 / `UNREADABLE` 2.
- **Verification:** each change had a full suite run read from its log (9132 → 9140 → 9146 passed, RUN_RC=0) and a mutation spec (`verify_drop.json` 4/4, `upstream_drop.json` 6/6, all assertion kills). Live: v5.8.4, v5.8.3, v5.8.2 read `EMITS`; a bogus tag reads `UNREADABLE`.

## Key Learnings

- **OMC 5.8.4 (2026-11-10) still ships the `type` emission** in both the GitHub tag and the npm tarball; the patch is still needed after every OMC update. The predecessor's "v5.8.3 still latest on 11-10" was already stale when written.
- **A test that sets an override env var bypasses the code that override replaces.** `OMC_PATCH_ROOTS` made every verify.py test skip `roots()`' plugin lookup, the one part that has to follow an update. Test the lookup itself under a fixture HOME.
- **The mutation harness's `crash_kills` counter is worth reading.** A row was "caught" by a KeyError traceback (exit 1, which `upstream.py` callers read as EMITS). Restructuring so the missing case is reported in one place turned it into an assertion kill and removed the crash path from the real script.
- **`npm pack <pkg>@<ver> --pack-destination <tmp>` plus `tarfile.extractfile`** reads a published package's files without installing or extracting to disk.

## Next Steps

None owed. Optional:

1. **Before any OMC update:** `python3 /Users/kimhawk/orca/skills/docs/patches/omc-codex-mcp-no-type/upstream.py`. `EMITS` → update, then `apply.py` + `verify.py`. `FIXED` → README §Retiring.
2. **On the Macmini** (no ssh from MacStudio), after `git pull`:
   - `cp /Users/kimhawk/orca/skills/docs/patches/patch-verify-on-update.sh ~/.claude/hooks/`;
   - `python3 /Users/kimhawk/orca/skills/docs/patches/codex-duplicate-handoff/verify.py --fix`; fix any `NOT FIXED` by hand per its README;
   - `python3 /Users/kimhawk/orca/skills/docs/patches/omc-codex-mcp-no-type/apply.py`, then `verify.py`.
3. **Retire the OMC patch** when `upstream.py` reads `FIXED` — `docs/patches/omc-codex-mcp-no-type/README.md` §Retiring.

## Open / Blocked Items

**From this session:**
- **OMC patch re-applied on MacStudio for 5.8.4** (4 runtime files, `*.pre-omc-codex-mcp-no-type` backups beside them): outside the repo, no commit. `verify.py` read `VERIFY: OK files=4` after apply.
- **`upstream.py` checks the GitHub tag and npm, not the plugin marketplace's own cache build.** The plugin cache is installed from the tag; not verified that the two are byte-identical. Accepted.
- **Scratch artifacts** in `/private/tmp/claude-501/-Users-kimhawk-orca-skills/991d87bb-7237-4449-80eb-f0db25ed87ca/scratchpad/` (suite logs, `omc584/` downloaded files): temporary.

**Carried from 2026-11-11 (codex-single-handoff), updated:**
- **Next Step 1, Macmini hook copy + `verify.py --fix` + OMC patch:** unchanged; now Next Step 2.
- **Next Step 2, retire the OMC patch:** still blocked on upstream (5.8.4 still emits); now Next Step 3, with `upstream.py` as the check.
- **Codex config edits outside the repo** (`[[skills.config]]` pins in `~/.codex/config.toml` and `$CODEX_HOME/config.toml`; Orca's `skills/handoff` copy deleted; backups in `/private/tmp/claude-501/-Users-kimhawk-orca-skills/a571186a-8d52-49d8-a61e-ac4740e2ac73/scratchpad/backup/`, temporary): unchanged. `codex-duplicate-handoff/verify.py` read `VERIFY: OK 2 Codex config(s)` at resume.
- **Orca copy may reappear if OMX setup re-runs:** unchanged; DUPLICATE check warns.
- **Pins break on every Matt Pocock plugin update:** unchanged; STALE check warns, `--fix` repoints.
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

**Files touched this session (all committed):**
- `docs/patches/omc-codex-mcp-no-type/targets.py` (`OMC_NPM_ROOT`): `2cd772c4`
- `docs/patches/omc-codex-mcp-no-type/tests/test_verify.py`, `tests/mutation-specs/verify_drop.json`: `2cd772c4`
- `docs/patches/omc-codex-mcp-no-type/upstream.py`, `tests/test_upstream.py`, `tests/mutation-specs/upstream_drop.json`: `412f1078`, `0be56a8b`
- `docs/patches/omc-codex-mcp-no-type/README.md`: all three commits

**Uncommitted changes:** none.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch
python3 docs/patches/omc-codex-mcp-no-type/upstream.py   # EMITS until OMC ships a fixed build
python3 docs/patches/omc-codex-mcp-no-type/verify.py     # expect VERIFY: OK files=4 on MacStudio
python3 docs/patches/codex-duplicate-handoff/verify.py   # expect VERIFY: OK 2 Codex config(s)
```

**Related docs:**
- `docs/patches/omc-codex-mcp-no-type/README.md` (§Check upstream before updating, §Retiring)
- `docs/handoffs/2026-11-11-main__codex-single-handoff.md`
