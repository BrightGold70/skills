# Handoff — Untracked-spec warning shipped in all bare modes; OMC 5.8.3 found to ship a stale build, patch kept

**Date:** 2026-11-10
**Branch:** main
**Project:** skills
**Supersedes:** 2026-11-09-main__omc-codex-type-patch.md
**Next-Session Focus:** Nothing in flight. Optional: apply the OMC patch on the Macmini, and wait for an OMC release whose installed build drops `type =`.

## Session Summary

This session closed the last open scout row and checked whether the OMC patch could be retired. Four commits (`f7d54ef3..afb66636`) are on `origin/main`.

- **`untracked-spec-warning` LANDED.** A bare `--check-anchors`, `--sweep` and `--sweep --isolate` now print `[H-MAD] note: untracked spec not swept: <path>` on stderr for each untracked, non-ignored JSON that is or may be a spec. Stdout is byte-identical.
  - A fresh-context `change-reviewer` found 1 must-fix (a UTF-16 untracked JSON crashed the sweep) and 4 should-fix items. All were fixed before the first commit.
  - `harness_check_anchors_discovery.json` is ALL_CAUGHT 18/18. The last full bare suite passed 9015 tests, with the tree unchanged during the run.
  - The skill-candidates census is now `OPEN(yes+maybe)=0`.
- **OMC patch NOT retired.** v5.8.3 contains #4903, but only `src/` is fixed. The compiled `dist/` in the tag and the npm 5.8.3 tarball still emit `type =`.
  - The auto-update to 5.8.3 had dropped the local patch. It was re-applied (`VERIFY: OK files=4`).
  - This is recorded in the patch README (`afb66636`) and was reported upstream: [#4899 comment 6754281731](https://github.com/Yeachan-Heo/oh-my-claudecode/issues/4899#issuecomment-6754281731). The issue stays closed.

## Key Learnings

- **An upstream "fixed in release X" can ship a fixed `.ts` with a stale build.** OMC v5.8.3 contains the #4903 merge commit and its `src/` is fixed, but `dist/installer/mcp-registry.js:794` (tag and npm) and `bridge/cli.cjs:44224` (npm) still emit `type =`. Judge the INSTALLED files: `verify.py` reporting `MISSING` plus `renderer still emits N type lines` means the build is unfixed.
- **The skill-candidates census counts a verdict as terminal only when it is bold.** `candidate: LANDED (…)` parsed into a separate lowercase `landed=1` bucket and left `terminal` unchanged. `candidate: **LANDED** (…)` counted. Recount after every verdict flip.
- **`--isolate` sweep output embeds the random `.h-mad-isolate-*` worktree path in each per-spec `SWEEP:` line.** A stdout comparison between two isolate runs must normalise it.
- **The npm `gitHead` can differ from the release tag's commit.** For OMC 5.8.3 they were `73e0d61` and `a803de7`. Check the published tarball itself, not just the tag.
- **The GitHub contents API cannot return files over 1 MB.** OMC's `bridge/cli.cjs` came back empty; read it from the npm tarball instead.

## Next Steps

None owed. Optional:

1. **On the Macmini, which MacStudio cannot reach by ssh**, after `git pull`:
   - re-copy the hook: `cp /Users/kimhawk/orca/skills/docs/patches/patch-verify-on-update.sh ~/.claude/hooks/`;
   - apply the patch: `python3 /Users/kimhawk/orca/skills/docs/patches/omc-codex-mcp-no-type/apply.py`;
   - check it: `verify.py` should print `VERIFY: OK`;
   - remove `type` from that Mac's `~/.omc/mcp-registry.json` and from any `type =` lines in its codex homes. The Macmini is probably on OMC 5.8.3 too, which still needs the patch.
2. **Retire the OMC patch** once a release's installed `dist/` and `bridge/cli.cjs` no longer write `type =`. After an update, `python3 docs/patches/omc-codex-mcp-no-type/verify.py`: `MISSING` without `renderer still emits` means the build is fixed. Then follow the README §Retiring. That means deleting the directory, and also removing its `pytest.ini` `testpaths` entry and its `NPM_FILES` lines in `docs/patches/patch-verify-on-update.sh` (re-copy the hook afterwards).

## Open / Blocked Items

**From this session:**
- **OMC patch retirement:** blocked on upstream. The fixed source in v5.8.3 was shipped with a stale `dist/`. The #4899 comment asks for a rebuild.
- **Re-applied OMC patch on MacStudio** (outside the repo, no commit): the 4 runtime files under the 5.8.3 plugin cache and `/opt/homebrew/lib/node_modules/oh-my-claude-sisyphus/`. New `*.pre-omc-codex-mcp-no-type` backups sit beside each.
- **Scratch artifacts** in `/private/tmp/claude-501/-Users-kimhawk-orca-skills/b68348df-47c5-4f93-82bb-c3ff92d3143f/scratchpad/`: `review.md` (the change review), `omc583/` (the npm 5.8.3 tarball), `suite*.log`, and `omc4899-comment.md`. They are temporary; the review's findings are all fixed and committed.

**Carried from 2026-11-09 (omc-codex-type-patch), updated:**
- **Next Step 1, apply the OMC patch on other Macs:** unchanged. It is Next Step 1 above.
- **Next Step 2, scout row `untracked-spec-warning`:** CLOSED in `f7d54ef3`, `15b4f477` and `d6e469fa`. The row is `**LANDED**`.
- **Next Step 3 and Open item, watch OMC #4899:** UPDATED. The issue was closed as fixed and the fix ships in v5.8.3 source, but the 5.8.3 build is stale. See above.
- **OMC patch exists only on MacStudio:** unchanged.
- **`~/.claude.json` context7/sequential-thinking entries:** unchanged, expected.
- **Predecessor-session scratchpad backups (`013414ea…/scratchpad/`):** unchanged. They are temporary, and `*.pre-omc-codex-mcp-no-type` backups sit beside the patched files.
- **Edits outside the repo from the predecessor** (registry, the 2 codex configs, the hook copy): unchanged. Re-checked this session: 0 `type` lines in the registry, `~/.codex/config.toml` and the Orca codex config.
- **Two timing-based tests kept as fixed sleeps, by design:** unchanged, accepted.
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
- **Scratch-dir deletion (`6df9db7a…/scratchpad`), commits after the measured tree (`899d9bdf`, `cd885d09`), Macmini sync (#16), dispatch `NOT enforced` watch, heartbeat test flake, heartbeat mutation row, codex `ignoring 2 unrecognized configuration settings`:** CLOSED in predecessors, unchanged.
- **HemaSuite drafting quality without `CLAUDE.md`:** handed over, owned by HemaSuite. Unchanged.
- **Macmini untracked `GEMINI.md`, `.gemini/`, `.grok/`:** not carried, by operator choice. Never stage them.
- **The Macmini cannot be reached from MacStudio by ssh:** unchanged. Do not retry.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/h_mad_mutation_harness.py` (`_untracked_specs`, `_warn_untracked_specs`, `_run_main`): `f7d54ef3`, `15b4f477`
- `h-mad/tests/test_h_mad_mutation_harness.py` (10 new tests): `f7d54ef3`, `15b4f477`, `d6e469fa`
- `h-mad/tests/mutation-specs/harness_check_anchors_discovery.json` (14 new rows, 18 total): the same 3 commits
- `docs/skill-candidates.md` (`untracked-spec-warning` → `**LANDED**`): `f7d54ef3`, `15b4f477`
- `docs/patches/omc-codex-mcp-no-type/README.md` (the 5.8.3 finding, a sharper §Retiring): `afb66636`
- `docs/handoffs/2026-11-10-main__untracked-spec-warning.md` (this doc)

**Uncommitted changes:** none tracked. MacStudio's untracked files are listed above.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch
python3 docs/patches/omc-codex-mcp-no-type/verify.py                         # expect VERIFY: OK files=4 on MacStudio
python3 handoff/scripts/skill_candidates_census.py docs/skill-candidates.md  # expect OPEN(yes+maybe)=0
gh release list -R Yeachan-Heo/oh-my-claudecode -L 3                         # a release after v5.8.3 may carry the rebuild
```

**Related docs:**
- `docs/patches/omc-codex-mcp-no-type/README.md`
- OMC #4899 and its comments: https://github.com/Yeachan-Heo/oh-my-claudecode/issues/4899
- `docs/handoffs/2026-11-09-main__omc-codex-type-patch.md`
