# Handoff — codex TDD gate: three measured defects block a real Phase 5 GREEN

**Date:** 2026-09-28
**Branch:** main
**Project:** skills
**Handover-From:** HemaSuite · feature/28-review-manifest-guideline-evidence · session 23401af7-3efe-4845-8f67-98e9efda02af
**Supersedes:** none — first on this branch

## Session Summary

`h-mad/hooks/h-mad-codex-tdd-gate.py` was armed for the first time on a real feature (HemaSuite #28
Task 7 GREEN) and refused a legitimate production edit. Three defects, all measured below. The
operator chose to disarm it (the `~/.agents/skills/h-mad` symlink was removed again) and route the fix
here. Nothing in the hook was edited.

## Key Learnings

- **The install path the project wires does not exist by default.** HemaSuite's tracked
  `.codex/hooks.json` runs `python3 $HOME/.agents/skills/h-mad/hooks/h-mad-codex-tdd-gate.py`, and
  `~/.agents/skills/h-mad` was absent, so every codex shell/`apply_patch` call was denied. Codex worked
  around it with a Node file tool (unmatched by the hook's matcher) and `hmad-dispatch run`, so work
  still landed — i.e. the missing hook is a **bypass**, not a block. `codex-runtime.md` §"Package and
  project roots" documents the self-check but never the install step for `~/.agents/skills/h-mad`.
- **Codex's own diagnosis was wrong.** It blamed the dispatch cwd (`--cd hematology-paper-writer`) for
  paths lacking the `hematology-paper-writer/` prefix. `_project_root` resolves the git toplevel, so
  the prefix is present; the real cause is defect 1.

## Next Steps

1. **D1 — derivation assumes one test file per module (blocks every write).** `_derived_test` calls
   `scripts/h_mad_derive_test_path.sh`, which maps by module name only. Measured:
   `hematology-paper-writer/tools/review_round/guideline_excerpts.py -> …/tests/test_guideline_excerpts.py`,
   `cli/_parser.py -> tests/test__parser.py`, `tools/references/restoration.py -> tests/test_restoration.py`.
   None exist; an impl-plan names tests per task (`**Test file**:` — here
   `tests/test_certificate_lock_removed.py`). Fix direction: resolve the test from the active
   impl-plan Task whose `**Production file**:` lists the target, falling back to the name map.
2. **D2 — project virtualenv untrusted.** `_trusted_executable` accepts only `TRUSTED_BIN_DIRS`
   (`/bin`, `/usr/bin`, `/usr/local/bin`, `/opt/homebrew/bin`), so
   `.venv/bin/python -m pytest …` — the only interpreter with pytest in HPW — is denied under Phase 5.
3. **D3 — the gate can pass vacuously (fail-open).** `_test_exit` runs `[sys.executable, "-m",
   "pytest", …]`; the hook runs under `python3` = python3.14 with **no pytest**. Measured:
   `/opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest --version` → rc=1
   (`No module named pytest`). `test_exit != 1` is the refusal condition, so a missing pytest reads as
   "the test fails" and the write is **allowed** without running any test, wherever D1 finds a file.
   Fix: run the project interpreter, and score on pytest's summary line, never on rc (a missing module
   and a failing test both exit 1).
4. Then: document the `~/.agents/skills/h-mad` symlink install in `codex-runtime.md`, add it to
   `h_mad_install_check.py`, and live-verify on a real GREEN before re-arming in HemaSuite.

## Open / Blocked Items

- HemaSuite #28 continues with the hook disarmed (degraded mode). repo: /Users/kimhawk/orca/HemaSuite ·
  branch: feature/28-review-manifest-guideline-evidence · worktree: none. Blocked codex report:
  `/private/tmp/claude-501/-Users-kimhawk-orca-HemaSuite/23401af7-3efe-4845-8f67-98e9efda02af/scratchpad/t7_green.blocked1.report.md`
  (scratchpad — copy it if needed; it is not durable).

## Context for Next Session

**Files touched:** none in this repo besides this brief.
**Uncommitted changes:** another lane's (`docs/01-plan/features/grok-codex-fallback.plan.md`, `.gitignore`) — not mine.
**To resume:** `cd /Users/kimhawk/orca/skills && /handoff takeover`
