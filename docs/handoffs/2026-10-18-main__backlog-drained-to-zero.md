# Handoff — agy-coder-fallback COMPLETE; skill-candidate backlog drained to OPEN=0

**Date:** 2026-10-18
**Branch:** main
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-10-17-main__agy-coder-fallback-merged.md

## Session Summary

Done. agy-coder-fallback ran FR-8 post-merge (Tasks 20–22) live on agy 1.4.0, closed Phase 7, and was archived. That makes it COMPLETE. Its worktree, its local and remote branch, and the fixture project are deleted. After that, the session triaged and drained the whole skill-candidate backlog: census OPEN 17 → 0. That covered 8 shortlist items, the pass-log pruning, and all 6 trigger-deferred rows, which the operator chose to build anyway ("Build all 6"). Two defects were fixed along the way: a silent skip in census `--apply`, and a security-review finding on the gate probe handoff. `origin/main` = `282ab531`, in sync. Final full suite at the rebased tree: 6976 passed and 2 failed. Both failures were stale census pins; after the bump the census module passes 94/94. The whole suite was not re-run after the bump.

## Key Learnings

- **agy 1.4.0's `init.tools` is not the model's tool set.** `multi_replace_file_content`, `sed_file` and `notebook_edit` are listed there, but no model is ever offered them (4 attempts, 3 model families). Only `write_to_file`, `replace_file_content` and `run_command` can be called. `replace_file_content` names its target `TargetFile`. `[gotcha, 0.7]`
- **In agy hooks.json, an earlier handler's `deny` short-circuits the later handlers.** Put a capture or observer hook FIRST. A handler that runs past its `timeout` is killed and the call is blocked (`timeout-blocks`). `[gotcha, 0.7]`
- **Hand-applied mutations read stale `__pycache__`.** A same-size rewrite within the same mtime second reused the old bytecode, which gave a false "1 failed" after the restore. Use the harness, which purges bytecode, or delete `__pycache__`. `[gotcha, 0.7]`
- **Running the suite while committing produces `TREE_MOVED`.** Run the full suite and mutation sweeps in a detached worktree (`git worktree add --detach`, or the new `--isolate`) so the main tree stays editable. `[pattern, 0.7]`
- **A row's surviving mutant can be masked by a later guard** (the row-2491 case, reproduced in reproduce_flake). The fix is to pin the test to the SPECIFIC refusal reason, not just "UNREADABLE". `[pattern, 0.5]`
- **Unescaped `|` in a markdown table cell breaks the row.** Census `--apply` used to skip such a row silently; it now refuses. Escape `\|` in status text. `[gotcha, 0.7]`
- **Live-count census pins break when another session adds J entries.** `origin/main` itself went red after J54–J56 landed without the pin bump. Bump the pins in the same commit as the J entry. `[gotcha, 0.5]`

## Next Steps

None owed. Every task is closed and no feature is in flight. The only open backlog row is the one this closeout's scout filed: "backlog-row TDD cycle driver", census OPEN=1.
1. [suggested] Run `/handoff read` next session and pick new work. The low-value residuals are listed below.

## Open / Blocked Items

**Carried from 2026-10-17-main__agy-coder-fallback-merged.md, each one accounted for:**
- **FR-8 Tasks 20–22 + Phase 7 closure:** CLOSED.
  - Commits: `61c620e7`/`5e55d1c9` (T20), `fb4a0680` (T21), `4e59c50e`/`f3233797` (T22), `4cf31977` (archive), `3d6c260e`.
  - Task 20 was narrowed to 3 tools by operator decision D-FR8-1.
  - The feature is recorded `last_completed_phase=7`.
- **Feature worktree removal:** CLOSED. The worktree, the local branch and `origin/feature/agy-coder-fallback` are deleted, per the operator.
- **Owed impl-plan wording (D5d-1 item 15, D5d-5 Task 12):** CLOSED, written before the archive.
- **Tooling gaps:** CLOSED.
  - `gate` shape and repeatable `--test-path`: `c046bc38`.
  - Teardown error declarable: `a1fc3622`.
  - wire_registry interpreter: `6396ac38`.
- **Design FR-4 `FAIL parser` sentence; ASSEMBLE-TDD HALT classification:** WITHDRAWN. The design is archived and the feature COMPLETE.
- **failure-recovery rows for `step5:implementer_*`:** CLOSED (`3d6c260e`).
- **Fix 3 (#8) / `hmad-notebooklm-carry-fixes` record:** CLOSED. The record was set to phase 7. Origin: Handover-From HemaSuite · main · session 0980df8b.
- **Skill-candidate triage, deferred rows, review residuals:** CLOSED. Census OPEN 17 → 0, then 1 when this closeout's scout filed a new row; see `docs/03-analysis/skill-candidates-triage-2026-10-18.md`, including its #22 addendum.
- **#56 residue, graft statusline, V-11.1, tdd-gate-fail-opens bookkeeping, over-refusals:** CLOSED. Each was dropped as convention, by design, already landed, or a user decision, per the triage table.
- **Pass-log rotation:** CLOSED (`3d54d49f`).
- **Memory index above 17500B:** CLOSED. It is now 17443 B / 123 lines.
- **HemaSuite canonical 1/1 diverged:** CLOSED.
  - Local `main` matches `origin/main` (0 0).
  - The checkout is now on another lane's `feature/claim-verdict-lineage`, with 108 dirty lines. It is not ours and was left untouched.
- **NS2 HemaSuite feature/204 `no-mutation-spec`:** unchanged; HemaSuite's call. Location: repo `/Users/kimhawk/orca/HemaSuite`.
- **Foreign `stash@{0}` (`resolved-model`):** unchanged. Do not touch.
- **Bash pin blast radius:** unchanged and inert; the probe reads `regex_hits=0` on HemaSuite.
- **`.git/info/exclude` narrowed to `/.agents/skills/`:** keep. The committed `.agents/hooks.json` relies on it.
- **Row 1412 four-clock liveness limits:** watch-only; reopen if one is observed. Unchanged.

**New this session:**
- Agy-coder-fallback carries a `review_independence_unrecorded` warning. Post-merge Tasks 20 and 22 had no 5e review leg; this was accepted and recorded in the report.

## Context for Next Session

**Files touched this session (all committed, pushed):**
- **agy-coder-fallback FR-8:**
  - `h-mad/hooks/h-mad-agy-tdd-gate.py` (`PATH_KEYS`)
  - `h-mad/scripts/h_mad_assemble_tdd.py` (agy default 900)
  - `.agents/hooks.json`
  - `h-mad/references/agy-runtime.md`
  - `h-mad/tests/fixtures/agy-payloads/`
  - `docs/archive/2026-10/agy-coder-fallback/` (49 files)
- **Backlog features:**
  - `h-mad/tests/{leak_reaper.py,conftest.py}`
  - `h-mad/scripts/h_mad_assemble_tdd.py`: `--phase gate`, multi `--test-path`, guard scope, PROBE-COMMANDS
  - `h-mad/scripts/h_mad_mutation_harness.py`: `--isolate`, `requires`/`host_skipped`, `--reachability`, `masked-hint`
  - `h-mad/scripts/h_mad_tdd_judge.py`: newest-first
  - `handoff/scripts/skill_candidates_census.py`: `--rev`, `--apply`, malformed refusal
  - `h-mad/scripts/h_mad_wire_registry.py`
  - `h-mad/scripts/h_mad_archreview_cycle.py`: tree snapshot
  - `h-mad/scripts/h_mad_audit_cycle.py`: `prune_pass_logs`
  - **New:** `h-mad/scripts/h_mad_reproduce_flake.py`
  - Matching tests, mutation specs, and `h-mad/SKILL.md`
- **Docs:**
  - `docs/skill-candidates.md`
  - `docs/03-analysis/skill-candidates-triage-2026-10-18.md`
  - `h-mad/references/{failure-recovery,codex-implementer-prompt}.md`

**Uncommitted changes:** none.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
python3 handoff/scripts/skill_candidates_census.py --list-open docs/skill-candidates.md   # expect OPEN=1 (the new scout row)
/opt/anaconda3/bin/python3 -m pytest h-mad/tests handoff/tests -q -p no:cacheprovider    # 6978 expected
```

**Related docs:**
- `docs/03-analysis/skill-candidates-triage-2026-10-18.md` (triage + #22 addendum)
- `docs/archive/2026-10/agy-coder-fallback/agy-coder-fallback.report.md`
- `docs/archive/2026-10/agy-coder-fallback/probes/fr8_tracer.md`, `fr8_payload_capture.md`
