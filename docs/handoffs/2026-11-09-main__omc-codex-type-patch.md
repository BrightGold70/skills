# Handoff — Heartbeat mutation row landed; OMC codex `type` warning fixed, patched and proven

**Date:** 2026-11-09
**Branch:** main
**Project:** skills
**Supersedes:** 2026-11-09-main__heartbeat-flakes-fixed.md
**Next-Session Focus:** Nothing in flight. Optional: apply the OMC patch on other Macs, and watch OMC #4899.

## Session Summary

This session closed both of the predecessor's optional items, then did follow-up work on the second one. Four commits (`c0780235..0a9dd491`) are on `origin/main`.

- **Heartbeat mutation row:** `exec_heartbeat_cadence.json` landed. It is `ALL_CAUGHT` for both the codex and the agy beat test.
- **Codex `ignoring 2 unrecognized configuration settings`:** the 2 settings were `mcp_servers.{context7,sequential-thinking}.type`, written by OMC 5.8.0's MCP registry sync. They were fixed in the registry data and in both codex homes.
  - OMC's renderer is patched locally in all 4 runtime copies (`docs/patches/omc-codex-mcp-no-type/`), and the issue is filed upstream as OMC #4899, with an http follow-up comment.
  - The SessionStart patch-verify hook now also fingerprints the npm OMC package.
  - `verify.py` has its own tests and 3 mutation rows, all caught.
- **Suite:** a full bare run passed 9006 tests, with the tree unchanged during the run.

## Key Learnings

- **The codex `ignoring N unrecognized configuration settings` warning names the keys on the indented lines below it.** Read those before guessing at files. Here it named neither suspect config: it named Orca's per-account `codex-accounts/<id>/home/config.toml`.
- **`codex mcp list` never prints that warning,** even for a config that has the bad keys. Only `codex exec` does, and without `</dev/null` it hangs on `Reading additional input from stdin...` (rc=124).
- **Codex 0.167 ignores `type` on every MCP transport:** `stdio`, `http` and `streamable-http`. A `url` entry with no `type` still runs as HTTP. This was measured with temp `CODEX_HOME`s that held only a `config.toml` and no credentials; the warning prints at config load, before the auth failure.
- **OMC never deletes a `type` line already in a codex file.** `codexEntriesEqual` infers `stdio` from `command`, so `syncCodexConfigToml` returns `changed: false`. Delete such lines by hand.
- **The Orca shell exports `CODEX_HOME`.** Any OMC or codex inspection meant for `~/.codex` must set `CODEX_HOME` explicitly, or it reads the Orca home.
- **zsh `echo "$json"` expands `\n` inside JSON strings** and breaks `json.load`. Pipe captured JSON with `printf '%s'`.
- **The mutation-spec corpus is discovered with `git ls-files`.** Stage a new spec before any bare `--check-anchors` or sweep, or they silently skip it.
- **`pytest.ini` `testpaths` gates what a bare `pytest` sees.** A new test folder outside the 3 listed dirs must be added there. `docs/patches/omc-codex-mcp-no-type/tests` now is. Side effect: `test_suite_collection.py` treats each top-level dir named in `testpaths` as a "skill", so `docs/` is now one, and any future test dir under `docs/` must be declared too.
- **Editing files during a suite run prints `SUITE: TREE_MOVED`,** and a pass then measured a tree that changed partway through. This session's first full run hit it, and a second clean run was needed.

## Next Steps

None owed. Optional:

1. **On each other Mac running OMC 5.8.0** (e.g. the Macmini), after `git pull`:
   - re-copy the hook: `cp /Users/kimhawk/orca/skills/docs/patches/patch-verify-on-update.sh ~/.claude/hooks/`;
   - apply the patch: `python3 /Users/kimhawk/orca/skills/docs/patches/omc-codex-mcp-no-type/apply.py`;
   - check it: `verify.py` should print `VERIFY: OK`;
   - remove `type` from that Mac's `~/.omc/mcp-registry.json` and any existing `type =` lines in its codex homes. The patch alone doesn't delete existing lines.
2. (optional) Scout row `untracked-spec-warning` (`candidate: maybe`, the only open row): make bare `--check-anchors` warn when a `tests/mutation-specs/` dir holds an untracked `*.json`. The discovery is in `h-mad/scripts/h_mad_mutation_harness.py` (`git ls-files` call near line 2171).
3. **Watch [OMC #4899](https://github.com/Yeachan-Heo/oh-my-claudecode/issues/4899).** When a fixed OMC ships, update it and run `verify.py`; it will report MISSING by design. If the new renderer has no `type =` line, retire the patch per its README §Retiring.

## Open / Blocked Items

**From this session:**
- **Upstream OMC #4899:** open, filed this session. The local patch carries the fix until it lands.
- **OMC patch exists only on MacStudio.** The plugin cache and npm tree are per-machine. Until a Mac runs `apply.py`, its patch-verify hook reports `omc-codex-mcp-no-type: patch MISSING` every session.
- **`~/.claude.json` context7/sequential-thinking entries:** OMC sees them as out of date (they still have `type`, the registry no longer does). Its next sync rewrites them without `type`, which Claude reads as stdio. Expected; nothing to do.
- **Backups in this session's scratchpad** (`/private/tmp/claude-501/-Users-kimhawk-orca-skills/013414ea-ec2f-408f-a756-c53805fe546d/scratchpad/`): `omc-mcp-registry.json.bak`, `default-codex-config.toml.bak`, `orca-codex-config.toml.bak`. The scratchpad is temporary. The patched OMC files also have `*.pre-omc-codex-mcp-no-type` backups beside them.
- **Edits outside the repo (no commit):**
  - `~/.omc/mcp-registry.json` (`type` removed);
  - `~/.codex/config.toml` and the Orca codex config (2 `type` lines removed from each);
  - the 4 OMC runtime files (patched);
  - `~/.claude/hooks/patch-verify-on-update.sh` (re-copied).

**Carried from 2026-11-09 (heartbeat-flakes-fixed), updated:**
- **Next Step 1, heartbeat mutation row:** CLOSED in `c0780235`. The census is now `OPEN(yes+maybe)=0`.
- **Next Step 2 and Open item, codex `ignoring 2 unrecognized configuration settings`:** CLOSED, see the Summary. Confirmed gone with a real `codex exec`: rc=0, `OK`, 0 ignore lines in the captured stderr.
- **Two timing-based tests kept as fixed sleeps, by design** (`test_heartbeat_shorter_than_stamp_timeout_terminates`, `test_agy_transcript_is_written_DURING_the_run_not_after`, plus `test_agy_exec_timeout_kills_and_returns_124`): unchanged, accepted.
- **Pyright `timeout=None` type warning** at `test_hmad_dispatch_exec_stamp.py:458`: unchanged, harmless.
- **opencode `$schema` change (`bd6a47ca`):** unchanged, informational.
- **MacStudio untracked files** (`.codex/config.toml`, three `docs/03-analysis/2026-10-2*.analysis.md`, `hemasuite/docs/research/`): unchanged. Never stage them.
- **Orca worktree comment:** this WRITE restamps it.
- **Hand-started codex session still ungated:** unchanged, accepted.
- **Another hook in `.codex/hooks.json` withholds the bypass:** unchanged, by design.
- **Two unanchored hook-trust plumbing lines:** unchanged, accepted.
- **Rust toolchain `stable-aarch64-apple-darwin`:** unchanged, informational.
- **Hard-link kinds differ by host (all DENY):** unchanged, accepted.
- **Predecessor-machine scratch dirs (`f7b82980…`) and 43 unreviewed scratch `.md` reports:** unchanged, on another machine.
- **Foreign PID 32561:** informational, unchanged.
- **Accepted items, unchanged since 2026-11-08:** `argument_not_printable` refuses NBSP/U+202F/ZWJ; two unpinned `_enc` print sites; `unreadable-file` reported first; `crash_visible=0/0` on host specs; scout row `hand-applied-single-mutants` (no).
- **Scratch-dir deletion (`6df9db7a…/scratchpad`), commits after the measured tree (`899d9bdf`, `cd885d09`), Macmini sync (#16), dispatch `NOT enforced` watch, heartbeat test flake:** CLOSED in predecessors, unchanged.
- **HemaSuite drafting quality without `CLAUDE.md`:** handed over, owned by HemaSuite. Unchanged.
- **Macmini untracked `GEMINI.md`, `.gemini/`, `.grok/`:** not carried, by operator choice. Never stage them.
- **The Macmini cannot be reached from MacStudio by ssh:** unchanged. Do not retry. This is why Next Step 1 must be run on the Macmini itself.

## Context for Next Session

**Files touched this session:**
- `h-mad/tests/mutation-specs/exec_heartbeat_cadence.json`, `docs/skill-candidates.md` (`c0780235`)
- `docs/patches/omc-codex-mcp-no-type/{README.md,apply.py,targets.py,verify.py}` (`808cd13c`, `0a9dd491`)
- `docs/patches/patch-verify-on-update.sh` (`299d2565`)
- `docs/patches/omc-codex-mcp-no-type/tests/{test_verify.py,mutation-specs/verify_drop.json}`, `pytest.ini` (`0a9dd491`)
- `docs/handoffs/2026-11-09-main__omc-codex-type-patch.md` (this doc)

**Uncommitted changes:** none tracked. MacStudio's untracked files are listed above.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch
python3 docs/patches/omc-codex-mcp-no-type/verify.py                         # expect VERIFY: OK files=4 on MacStudio
python3 handoff/scripts/skill_candidates_census.py docs/skill-candidates.md  # expect OPEN(yes+maybe)=1 (untracked-spec-warning, maybe)
```

**Related docs:**
- `docs/patches/omc-codex-mcp-no-type/README.md`
- OMC issue https://github.com/Yeachan-Heo/oh-my-claudecode/issues/4899, and the follow-up comment #issuecomment-6734049071
- `docs/handoffs/2026-11-09-main__heartbeat-flakes-fixed.md`
