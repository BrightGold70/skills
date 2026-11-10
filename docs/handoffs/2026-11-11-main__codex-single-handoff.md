# Handoff — Codex loads exactly one handoff; the patch hook guards it three ways, and --fix repairs two

**Date:** 2026-11-11
**Branch:** main
**Project:** skills
**Supersedes:** 2026-11-10-main__untracked-spec-warning.md
**Next-Session Focus:** Nothing in flight. Optional: the Macmini (copy the hook in, run `verify.py --fix`) and OMC patch retirement.

## Session Summary

The session started as a resume and became work on making Codex load exactly one `handoff` skill, this repo's. Six commits (`4a8c6e3b..cf80157f`) are on `origin/main`.

- **Untracked MacStudio files triaged.**
  - Three analyses committed: `4a8c6e3b`.
  - The superseded `hemasuite/docs/research/pdfcraft-application-priorities.md` draft deleted. HemaSuite holds the newer copy on `BrightGold70/hemasuite-document-workbench`, commit `efcaae522`.
  - The repo's `.codex/config.toml` deleted. It did nothing (see Key Learnings).
- **Codex setup fixed, outside the repo.**
  - Matt Pocock's handoff disabled in both user configs: `~/.codex/config.toml` and Orca's `$CODEX_HOME/config.toml`.
  - The 4 KB "Handoff for Codex" copy deleted from Orca's Codex account folder (`$CODEX_HOME/skills/handoff`).
  - Checked in a real `codex exec` session file.
- **The new check `docs/patches/codex-duplicate-handoff/` runs from `patch-verify-on-update.sh`:**
  - **MISSING**: the `~/.agents/skills/handoff` link to the repo is absent or broken.
  - **STALE**: the Matt Pocock pin points at a plugin version that is no longer installed.
  - **DUPLICATE**: a second skill named `handoff` exists for Codex.
- **`verify.py --fix`** repoints stale pins and creates or repairs the link, with race guards. It never deletes a duplicate.
- **Verification:** every feature had fresh-context review rounds, and every finding was fixed with a test. The check has 114 tests. The last bare suite passed 9129. The installed hook in `~/.claude/hooks/` matches the repo copy.

## Key Learnings

- **Codex 0.167 ignores `skills.config` in a project `.codex/config.toml`, even in a trusted project.**
  - The same entry works from `-c` or a user-level config.
  - Under Orca, Codex reads its user config from `$CODEX_HOME` (the Orca account folder), not `~/.codex`.
- **`codex debug prompt-input` renders exactly what the model sees, with no model call.** But it does not expand `$skill` mentions, and it omits `disable-model-invocation: true` skills.
  - So proving whether an explicitly invoked skill loads needs a real `codex exec`, then a grep of its session file (`$CODEX_HOME/sessions/…/rollout-*.jsonl`) for the skill body.
  - The model's own LOADED/ABSENT answer is not evidence.
  - `codex exec` hangs on "Reading additional input from stdin" unless given `</dev/null`.
- **pathlib's `exists()`/`is_symlink()` swallow PermissionError on Python 3.15 but raise on 3.11.**
  - The patch hook runs `python3` (3.15), while pytest here is 3.11.
  - The check's tests now run verify.py under the hook's `python3`.
  - Link states are decided with `os.lstat`/`os.stat`.
- **Under a UTF-8 locale, BSD awk will not match `\xef\xbb\xbf` against a line starting with U+FEFF.**
  - Two attempts to parse SKILL.md frontmatter in the bash hook each missed changes verify.py sees.
  - The hook now hashes the whole SKILL.md content instead.
- **A "re-check before acting" guard must re-check the STATE, not only the identity.** A dangling link whose target folder comes back keeps its target string and now works.
  - Also record the observed value at classification time, not from a later read.
  - Review reproduced both races overwriting a working link.
- **Fixes introduced defects in this session repeatedly.**
  - Examples: indented YAML keys matching after the parser was widened, and the walk guard hiding a folder first reached through a deep link.
  - Each was caught only by a remediation review round. Keep reviewing the fix, not just the feature.
- **The `run_in_background` task exit code said 0 on a pytest collection error.** RUN_RC was 2. Read the log, never the notification.

## Next Steps

None owed. Optional:

1. **On the Macmini** (MacStudio cannot reach it by ssh), after `git pull`:
   - copy the hook in: `cp /Users/kimhawk/orca/skills/docs/patches/patch-verify-on-update.sh ~/.claude/hooks/`;
   - run `python3 /Users/kimhawk/orca/skills/docs/patches/codex-duplicate-handoff/verify.py --fix`, which creates the link and the pins where it safely can;
   - fix any `NOT FIXED` lines by hand per that README;
   - also apply the OMC patch: `python3 /Users/kimhawk/orca/skills/docs/patches/omc-codex-mcp-no-type/apply.py`, then `verify.py`.
2. **Retire the OMC patch** once an OMC release's installed `dist/` and `bridge/cli.cjs` no longer write `type =`.
   - After an update, run `python3 docs/patches/omc-codex-mcp-no-type/verify.py`.
   - `MISSING` without "renderer still emits" means the build is fixed.
   - Then follow that README's §Retiring.

## Open / Blocked Items

**From this session:**
- **Codex config edits outside the repo**, done this session with no commit:
  - `[[skills.config]]` pins in `~/.codex/config.toml` and `$CODEX_HOME/config.toml`;
  - Orca's `skills/handoff` copy deleted.
  - Backups of the originals are in `/private/tmp/claude-501/-Users-kimhawk-orca-skills/a571186a-8d52-49d8-a61e-ac4740e2ac73/scratchpad/backup/`. That folder is temporary.
- **The Orca copy may reappear if OMX setup re-runs.** OMX probably installed it; that is unconfirmed. The DUPLICATE check warns when it comes back.
- **The pins break on every Matt Pocock plugin update**, because the path holds the version. The STALE check warns, and `verify.py --fix` repoints them.
- **Known limits of `codex-duplicate-handoff`**, accepted and documented in its README:
  - it does not read a flow-mapping `{name: handoff}`;
  - its scan depth is capped at `skills/<a>/<b>/`;
  - a plain file created in the instant before `--fix`'s rename would be replaced;
  - how Codex's own loader handles nested or BOM SKILL.md files is unverified.
- **Scratch artifacts** in the scratchpad above: review reports (`review-*.md`), suite logs, and the `mprev.mDCm` folder (bkit blocked its `rm -rf`). All temporary.

**Carried from 2026-11-10 (untracked-spec-warning), updated:**
- **Next Step 1, apply the OMC patch on the Macmini:** unchanged; folded into Next Step 1 above.
- **Next Step 2 and Open item, retire the OMC patch:** unchanged. Still blocked on upstream: v5.8.3 was still the latest release on 2026-11-10.
- **Re-applied OMC patch on MacStudio** (the 4 runtime files, with `*.pre-omc-codex-mcp-no-type` backups): unchanged. `verify.py` printed `VERIFY: OK files=4` at session start.
- **Predecessor scratch artifacts (`b68348df…/scratchpad/`):** unchanged, temporary.
- **MacStudio untracked files:** CLOSED in `4a8c6e3b` and by deletion. The three analyses are committed, and the pdfcraft draft and `.codex/config.toml` are deleted.
- **OMC patch exists only on MacStudio:** unchanged.
- **`~/.claude.json` context7/sequential-thinking entries:** unchanged, expected.
- **Predecessor-session scratchpad backups (`013414ea…/scratchpad/`):** unchanged, temporary.
- **Edits outside the repo from 2026-11-09** (registry, two Codex configs, the hook copy):
  - unchanged; 0 `type` lines;
  - the two Codex configs now also carry this session's `[[skills.config]]` pin;
  - the hook copy was re-copied several times this session and matches the repo.
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
- **Accepted items, unchanged since 2026-11-08:**
  - `argument_not_printable` refuses NBSP/U+202F/ZWJ;
  - two unpinned `_enc` print sites;
  - `unreadable-file` reported first;
  - `crash_visible=0/0` on host specs;
  - scout row `hand-applied-single-mutants` (no).
- **Items closed in predecessors:** unchanged. They are the scratch-dir deletion (`6df9db7a…`), commits after the measured tree (`899d9bdf`, `cd885d09`), the Macmini sync (#16), the dispatch `NOT enforced` watch, the heartbeat test flake and mutation row, and codex's `ignoring 2 unrecognized configuration settings`.
- **HemaSuite drafting quality without `CLAUDE.md`:** handed over, owned by HemaSuite. Unchanged.
- **Macmini untracked `GEMINI.md`, `.gemini/`, `.grok/`:** not carried, by operator choice. Never stage them.
- **The Macmini cannot be reached from MacStudio by ssh:** unchanged. Do not retry.

## Context for Next Session

**Files touched this session (all committed):**
- `docs/03-analysis/2026-10-22-ai-memory-hmad-handoff-integration.analysis.md`, `…-billion-context-…`, `2026-10-23-mattpocock-skills-…`: `4a8c6e3b`
- `docs/patches/codex-duplicate-handoff/{verify.py,README.md,tests/test_codex_duplicate_handoff_verify.py}`: `bf394767`, renamed in `423e16ab`, then `0606312f`, `70db8583`, `cf80157f`
- `docs/patches/patch-verify-on-update.sh` (`codex_fp`, `skills_fp`): `bf394767`, `423e16ab`, `70db8583`
- `pytest.ini` (testpaths): `bf394767`, `423e16ab`

**Uncommitted changes:** none tracked. No untracked files remain.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch
python3 docs/patches/codex-duplicate-handoff/verify.py   # expect VERIFY: OK 2 Codex config(s) …
python3 docs/patches/omc-codex-mcp-no-type/verify.py      # expect VERIFY: OK files=4 on MacStudio
gh release list -R Yeachan-Heo/oh-my-claudecode -L 3      # a release after v5.8.3 may carry the rebuild
```

**Related docs:**
- `docs/patches/codex-duplicate-handoff/README.md`
- `docs/patches/omc-codex-mcp-no-type/README.md`
- `docs/handoffs/2026-11-10-main__untracked-spec-warning.md`
