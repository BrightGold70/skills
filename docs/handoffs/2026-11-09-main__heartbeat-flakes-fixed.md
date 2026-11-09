# Handoff — Both watch items closed; heartbeat-test flakes fixed

**Date:** 2026-11-09
**Branch:** main
**Project:** skills
**Supersedes:** 2026-11-09-main__macstudio-resume-scratch-closed.md
**Next-Session Focus:** Nothing in flight and no watch items. Pick new work.

## Session Summary

Resumed on MacStudio and closed both of the predecessor's watch items. A real `hmad-dispatch exec codex` run printed no `gate is NOT enforced` warning, and codex 0.167.0 accepted `--dangerously-bypass-hook-trust`. The heartbeat test never failed in 23 isolated runs or in a full h-mad suite run (8563 passed). It was still fixed structurally: the codex and agy test stubs now wait for the beat the test asserts on, instead of sleeping a fixed time. Also fixed the suite's 3 pytest warnings and committed opencode's `$schema` line. Five commits, `a8edeb05..aaf3caf5`, all pushed.

## Key Learnings

- **`hmad-dispatch.sh` cannot be sourced.** It ends with `main "$@"; exit $?`, so sourcing it runs main. To test one function, extract it (`sed -n '/^_fn() {/,/^}/p'`). Or use `run_fn` in `h-mad/tests/test_hmad_dispatch.py`, which strips that last line.
- **This repo runs only one pytest session at a time.** A second session exits `SUITE: BUSY … lock=.h-mad/mutation.lock`. Running 8 copies of a test in parallel therefore runs 1 and creates no load. For load tests, use non-pytest CPU burners (`python3 -c` busy loops that stop themselves) and kill them by PID.
- **Fixing a timing-flaky stub test:** make the stub wait for the exact event the test asserts on, with a deadline. On the deadline the stub exits normally, so a broken feature fails the test's own assertion and not a wrapper timeout (rc=124). Prove it with a positive control: disable the heartbeat line in `hmad-dispatch.sh` (`-ge "$hb_interval"` → `-ge 999`), confirm red, restore with `git checkout`. Under load the agy beat test took up to 10.7s, well past the old fixed 4s sleep.
- **opencode adds `"$schema"` to every config it loads.** It did so to this repo's and the global `opencode.json` in the same second (log `~/.local/share/opencode/log/opencode.log`, run `3c6bb2b6`). Saved to `docs/learnings.md`.
- **The bkit destructive detector blocks any command containing `rm -rf`,** even on a scratchpad path. Use `mktemp -d` to get a fresh directory instead of clearing an old one.

## Next Steps

None owed: there are no watch items. If you want something, these optional items are the only candidates.

1. (optional) Register the heartbeat positive control as a mutation row. This is scout row `heartbeat-sync-mutation-rows` (`candidate: maybe`), the only open row. Mutate `-ge "$hb_interval"` in `h-mad/scripts/hmad-dispatch.sh`, and expect both the codex beat-sync tests (`h-mad/tests/test_hmad_dispatch_exec_stamp.py`) and the agy one (`h-mad/tests/test_hmad_dispatch_progress.py`) to go red.
2. (optional) Find the 2 settings codex warns it is ignoring: run `codex exec` on any trivial prompt and look for `Codex is ignoring 2 unrecognized configuration settings`. Suspects: the untracked `.codex/config.toml` and `~/.codex/config.toml`.

## Open / Blocked Items

**From this session:**
- **codex `ignoring 2 unrecognized configuration settings`:** informational, not investigated. It appeared in the log of the real dispatch. It is harmless, since the run succeeded.
- **Two timing-based tests left as fixed sleeps, by design:**
  - `test_heartbeat_shorter_than_stamp_timeout_terminates` (`h-mad/tests/test_hmad_dispatch_exec_stamp.py`) tests an upper bound (`< 5s`);
  - `test_agy_transcript_is_written_DURING_the_run_not_after` (`h-mad/tests/test_hmad_dispatch_progress.py`) needs the agent alive while it reads the log.

  `test_agy_exec_timeout_kills_and_returns_124` also keeps its sleep: the sleep must outlast `--timeout 1`.
- **Pyright `timeout=None` type warning** at `test_hmad_dispatch_exec_stamp.py:458`: it predates this session and is harmless.
- **opencode was launched in this repo at 09:40:49 KST, not by this session.** Its `$schema` change is committed (`bd6a47ca`). Informational only.

**Carried from 2026-11-09 (macstudio-resume-scratch-closed), updated:**
- **Dispatch `NOT enforced` stderr watch:** CLOSED.
  - Real `hmad-dispatch exec codex`, `workspace-write`, trivial prompt: rc=0, and the wrapper's stderr was only `hmad-dispatch: codex exec rc=0`.
  - The codex log shows `--dangerously-bypass-hook-trust` accepted.
  - The gate itself was not exercised, because codex made no tool call. It was shown to deny a write live on 11-08.
- **Heartbeat test `test_heartbeat_stamps_across_three_intervals`:** CLOSED. It was never reproduced: 23/23 isolated runs, plus the full suite at 8563 passed / 0 skipped. Fixed anyway in `d99d33ec`, along with 4 sibling tests. The sibling agy test was fixed in `aaf3caf5`.
- **MacStudio untracked files** (`.codex/config.toml`, three `docs/03-analysis/2026-10-2*.analysis.md` files, `hemasuite/docs/research/`): unchanged. Never stage them.
- **Orca worktree comment stale:** CLOSED. The predecessor restamped it, and it read current at this session's start. This WRITE restamps it again.
- **Scratch-dir deletion (`6df9db7a…/scratchpad`):** CLOSED in the predecessor, unchanged.
- **Commits after the measured tree (`899d9bdf`, `cd885d09`):** accepted, unchanged.
- **Macmini sync (#16):** CLOSED, unchanged.
- **Scout rows:** census was `OPEN(yes+maybe)=0` at this session's start. It is now 1, from this session's own `heartbeat-sync-mutation-rows` (`maybe`); see Next Step 1.
- **Hand-started codex session still ungated:** unchanged, accepted.
- **Another hook in `.codex/hooks.json` withholds the bypass:** unchanged, by design. This session's isolated run of `_codex_hook_trust_arg` confirmed both warnings still fire when they should.
- **Two unanchored hook-trust plumbing lines:** unchanged, accepted.
- **Rust toolchain `stable-aarch64-apple-darwin`:** unchanged, informational.
- **Hard-link kinds differ by host (all DENY):** unchanged, accepted.
- **Predecessor-machine scratch dirs (`f7b82980…`) and 43 unreviewed scratch `.md` reports:** unchanged. They are on another machine and harmless.
- **Foreign PID 32561:** informational, unchanged.
- **Accepted items, unchanged since 2026-11-08:**
  - `argument_not_printable` refuses NBSP/U+202F/ZWJ;
  - two unpinned `_enc` print sites;
  - `unreadable-file` is reported first;
  - `crash_visible=0/0` on host specs;
  - scout row `hand-applied-single-mutants` (no).
- **HemaSuite drafting quality without `CLAUDE.md`:** handed over, owned by HemaSuite. Unchanged.
- **Macmini untracked `GEMINI.md`, `.gemini/`, `.grok/`:** not carried, by operator choice. Never stage them.
- **The Macmini cannot be reached from MacStudio by ssh:** unchanged. Do not retry.

## Context for Next Session

**Files touched this session:**
- `h-mad/tests/test_h_mad_audit_origins.py`, `h-mad/tests/test_h_mad_state_write.py`, `h-mad/tests/test_h_mad_check_memory_index.py` (`a8edeb05`)
- `opencode.json` (`bd6a47ca`)
- `docs/learnings.md` (`07a7af4b`, plus this closeout's learnings)
- `h-mad/tests/stubs/codex`, `h-mad/tests/test_hmad_dispatch_exec_stamp.py` (`d99d33ec`)
- `h-mad/tests/stubs/agy`, `h-mad/tests/test_hmad_dispatch_progress.py` (`aaf3caf5`)
- `docs/handoffs/2026-11-09-main__heartbeat-flakes-fixed.md` (this doc)

**Uncommitted changes:** none tracked. MacStudio's untracked files are listed above.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch
python3 handoff/scripts/skill_candidates_census.py docs/skill-candidates.md   # expect OPEN(yes+maybe)=1
```

**Related docs:**
- `docs/handoffs/2026-11-09-main__macstudio-resume-scratch-closed.md`
- Commit messages of `d99d33ec` and `aaf3caf5`, which record the verification in full.
