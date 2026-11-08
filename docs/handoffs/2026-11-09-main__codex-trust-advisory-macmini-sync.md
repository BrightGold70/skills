# Handoff — Codex trust advisory landed; Macmini sync closed

**Date:** 2026-11-09
**Branch:** main
**Project:** skills
**Supersedes:** 2026-11-08-main__carries-closed-codex-gate-armed.md
**Next-Session Focus:** Nothing is in flight and no scout row is open. Only cleanup and watch items remain.
**Suggested-Skills:** handoff (resume)

## Session Summary

Done and pushed. `origin/main` = `cd885d09`. Host: Hawui-Macmini.
- **Macmini sync (#16): closed.**
  - Pulled up to `1d92ef9c`. The 2026-11-01 `assemble_tdd` stash was dropped (`git stash list` is empty).
  - Failure diff, `88b3fbe9` vs `7256be26`: `FAILDIFF: FIXED_ONLY subject_only=0 both=9 control_only=1`. The 9 failures are env-only; their IDs are in memory `python-interpreters-this-mac`.
- **Both 2026-11-08 scout rows: LANDED.**
  - `codex-hook-trust-unseen-by-install-check`: `h_mad_install_check.py` now prints a `CODEX_HOOK_*` advisory when codex would skip the gate. It is never counted in `issues=` (`533ccff1`, stamped `30f93b6d`).
  - `hand-inserted-mutation-rows`: phase5-substeps 5e now points at `--append-row` (`bdea3727`).
- **Mutation spec `install_check_codex_trust.json`:** 9 rows, all pinned to their enclosing symbol, ALL_CAUGHT 9/9 (`899d9bdf`, `cd885d09`).
- **graft→trail agent-config migration:** committed (`88b3fbe9`).

## Key Learnings

- **A new check that reads the real `.codex/hooks.json` turned 13 existing install-check tests red.** They now print an UNKNOWN line. The fix is an env override (`HMAD_CODEX_HOOKS_JSON`) plus an autouse conftest fixture that points it and `CODEX_HOME` at absent paths. Any future host-config probe needs the same hermetic default.
- **A "summary unchanged" test that compares two runs that both carry the advisory cannot kill a counting mutant.** The fix was to compare against a third run whose hooks path is unwired, so it prints no advisory line.
- **Run `h_mad_failure_diff.py` with `--subject-snapshot --include-dirty` when the checkout may change mid-run.** A plain run ends `UNREADABLE reason=subject-changed`. A snapshot with untracked files but without `--include-dirty` ends `subject-dirty`.
- **A test's pytest tmp dir cannot be captured during a full-suite run.** The suite's nested pytest calls rotate `pytest-of-<user>/pytest-N` out. Re-run the single test with `--basetemp`.

## Next Steps

1. Delete this session's scratch dirs. The `rm -rf` deny policy blocked me, so run: `! rm -rf /private/tmp/claude-501/-Users-kimhawk-orca-skills/6df9db7a-6b8f-4b54-bd28-427f8da80cbf/scratchpad/faildiff /private/tmp/claude-501/-Users-kimhawk-orca-skills/6df9db7a-6b8f-4b54-bd28-427f8da80cbf/scratchpad/faildiff2`. The rest of that scratchpad (`red/ green/ ct-rows/ bt-rows/ trustprobe/ sc.md`) can go too.
2. On the next real `hmad-dispatch` codex run on this Mac, watch dispatch stderr for `the h-mad gate is NOT enforced` — `h-mad/scripts/hmad-dispatch.sh` (`_codex_hook_trust_arg`).

## Open / Blocked Items

**From this session:**
- **Scratch-dir deletion:** blocked on the user's `rm -rf` deny policy. I did not try to work around it. See Next Step 1.
- **Commits after the measured tree:** `899d9bdf` and `cd885d09` came after `88b3fbe9` and are not in the failure-diff measurement. They are test/spec-only. I verified them directly: the new test file passes and the spec is ALL_CAUGHT 9/9. Status: accepted.

**Carried from 2026-11-08 (carries-closed-codex-gate-armed), updated:**
- **Macmini sync (#16):** CLOSED. Stash dropped; failure diff FIXED_ONLY, both=9 env-only.
- **Dispatch `NOT enforced` stderr watch on Macmini:** unverified. No real codex dispatch ran this session. Next Step 2.
- **Heartbeat test `test_heartbeat_stamps_across_three_intervals`:** passed again in this session's full suite. Watch continues, unchanged — `h-mad/tests/test_hmad_dispatch_exec_stamp.py:426`.
- **Scout rows `hand-inserted-mutation-rows`, `codex-hook-trust-unseen-by-install-check`:** CLOSED, LANDED (`bdea3727`, `30f93b6d`). Census: OPEN(yes+maybe)=0.
- **Hand-started codex session still ungated:** unchanged, accepted. The new install-check advisory now surfaces this.
- **Another hook in `.codex/hooks.json` withholds the bypass:** unchanged, by design.
- **Two unanchored hook-trust plumbing lines:** unchanged, accepted.
- **Rust toolchain `stable-aarch64-apple-darwin`:** unchanged, informational. It was set on the predecessor's machine.
- **Hard-link kinds differ by host (all DENY):** unchanged, accepted.
- **Predecessor scratch dirs** (`f7b82980…/scratchpad/{codexhome.*,cxwork.*,…}`) and the 43 unreviewed `.md` reports in old scratchpads: not present on this Mac (path absent). They live on the predecessor's machine. Unchanged, harmless.
- **Foreign PID 32561:** not present on this Mac. Informational. It belongs to the other machine.
- **Accepted items, unchanged since 2026-11-08:**
  - `argument_not_printable` refuses NBSP/U+202F/ZWJ;
  - two unpinned `_enc` print sites;
  - `unreadable-file` is reported first;
  - `crash_visible=0/0` on host specs;
  - scout row `hand-applied-single-mutants` (no).
- **HemaSuite drafting quality without `CLAUDE.md`:** handed over and owned by HemaSuite. Not tracked here.
- **Pre-existing untracked `GEMINI.md`, `.gemini/`, `.grok/`:** not carried, by operator choice. Never stage them.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/h_mad_install_check.py`
- `h-mad/tests/conftest.py`
- `h-mad/tests/test_h_mad_install_check_codex_trust.py`
- `h-mad/tests/mutation-specs/install_check_codex_trust.json`
- `h-mad/references/{codex-runtime,helper-scripts,phase5-substeps}.md`
- `docs/01-plan/features/codex-hook-trust-advisory.plan.md`
- `docs/skill-candidates.md`
- `AGENTS.md`, `opencode.json`, `.mcp.json`, `.trail/learnings/2026-11-08-*.md`

**Uncommitted changes:** none except the pre-existing untracked `GEMINI.md`, `.gemini/` and `.grok/`.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch
python3 handoff/scripts/skill_candidates_census.py docs/skill-candidates.md   # expect OPEN(yes+maybe)=0
```

**Related docs:**
- `docs/01-plan/features/codex-hook-trust-advisory.plan.md`
- `h-mad/references/codex-runtime.md` §hooks (trust paragraph + advisory)
