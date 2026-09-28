# Handoff — three parallel H-MAD features: grok-codex-fallback (5d/5e 4/17), multi-host-runtime (P4 next), codex-tdd-gate-defects (P3 c2 next)

**Date:** 2026-09-28
**Branch:** main
**Project:** skills
**Supersedes:** 2026-09-28-main__codex-tdd-gate-defects.md, 2026-09-28-main__grok-codex-fallback.md, 2026-09-15-main__two-false-task-premises.md, 2026-09-21-main__assembler-wiring-drops-counts-and-guards.md, 2026-09-23-main__hemasuite-foreign-three.md

## Session Summary

This session took over two inbound HemaSuite briefs, `grok-codex-fallback` and `codex-tdd-gate-defects`, and opened a third feature, `multi-host-runtime`, at the operator's request. It then ran all three through H-MAD in parallel, stopping at the 70% context mark.

| Feature | Status | Where |
|---|---|---|
| `grok-codex-fallback` | Implementing. Phases 1–5b closed. Tasks 1–4 of 17 are GREEN, each with a verified revert test and, for wiring tasks, a wire-scoped revert. | Branch `feature/216-grok-codex-fallback`, worktree `/Users/kimhawk/orca/skills-grok-codex-fallback` |
| `multi-host-runtime` | Spec v1.2 and plan v1.2 are closed. Phase 4 (design) is next. | main |
| `codex-tdd-gate-defects` | Spec v1.1 and plan v1.1. Plan audit cycle 2 is next. | main |

Nothing is merged or pushed. main is 48 commits ahead of origin.

## Key Learnings

- **The Claude-side TDD gate (`h-mad/hooks/h-mad-tdd-gate.sh`) is inert as installed.** It never reads `tool_input.file_path`. A replayed payload exits 0 before any BLOCK branch, and the blocking-form check (exit 1 against exit 2 / JSON deny) is a second, independent problem. The codex-tdd-gate-defects spec-author found this (OD-4), and it explains the inconclusive probe I ran. The Phase-5 "Claude must not self-author" enforcement has effectively never applied on Claude. Treat the Claude gate as advisory until codex-tdd-gate-defects ships.
- **Git stash is shared across worktrees.** In the revert test, a `git stash push` that stashed nothing (zsh does not word-split an unquoted `$PROD` into a pathspec) followed by `git stash pop` applied a *foreign* stash (`stash@{0}` "feat resolved-model"). That produced a UU conflict on `handoff/SKILL.md`, which I restored from HEAD. Always use `stash push -m <name>`, then grep that `stash@{0}` is yours before you pop. This is saved to docs/learnings.md.
- **Locale-dependent `sort` made codex's GREEN pass in its sandbox and fail on this machine.** The CLAUDE* capture in the stubs sorted `CLAUDE_EFFORT` before `CLAUDECODE` under en_US.UTF-8. The fix is `LC_ALL=C sort`. Re-run tests under both `LC_ALL=en_US.UTF-8` and `LC_ALL=C`.
- **grok is a near drop-in Claude host.** `grok inspect` lists `~/.claude/skills` (including h-mad and handoff), 71 agents (including our authors), and Claude hooks from `~/.claude/settings.json`, with tool-name aliasing. That is why multi-host-runtime uses a delta adapter (D1).
- **The grok `streaming-json` final message is the last non-empty text segment.** `tool_call`, `tool_call_update`, `usage` and `end` close a segment. Concatenating the deltas loses turn boundaries (`…"probe".STATUS: DONE`). Taking the text after the last tool/usage event returns empty, because `usage` and `end` come after the final text. Probe: `docs/03-analysis/probes/grok-codex-fallback/stream-json.2026-09-28.md`.
- **Environment traps:**
  - `python3` is Homebrew 3.14 with no pytest, and `rtk` can misreport `python3 -m pytest --version` as working. Use `rtk proxy …` and pass `--suite-cmd "/opt/anaconda3/bin/python -m pytest h-mad/tests -q -p no:cacheprovider"` to `audit-cycle`.
  - codex's sessions run graft, which dirties the worktree (`.gitignore`, `.ignore`, `graft/`). Revert those before every commit.
- **Committing an unscorable audit report under the `*.audit.v<N>.*` grammar breaks `test_calibration_no_committed_report_is_refused`.** Keep non-gateable reports under `docs/03-analysis/probes/`.
- **`invariants.base.md` has been amended (`0b3f969`).** Dispatched agent CLIs (codex, agy, grok) are not script dependencies, and the list is closed to operator decision.

## Next Steps

1. **grok-codex-fallback Task 5 RED.** In the worktree, run `python3 ~/.claude/skills/h-mad/scripts/h_mad_assemble_tdd.py --feature grok-codex-fallback --task "Task 5" --phase red --project-root /Users/kimhawk/orca/skills-grok-codex-fallback --impl-plan <wt>/docs/01-plan/features/grok-codex-fallback.impl-plan.md --python /opt/anaconda3/bin/python …`, taking the counts and guards from the Task 5 section. Dispatch with `hmad-dispatch exec codex … --cd <wt>` via `run_in_background`. Never use a bare `&`: it produces no harness notification.
2. **Verify every GREEN before committing it:**
   - re-run the tests under both locales;
   - run the module revert with a named stash;
   - for `wiring` tasks, run the wire-scoped revert (cut only the WIRE line and confirm the WIRE-PIN fails);
   - revert the graft pollution.

   Pattern: the Task 3 and Task 4 commits `f76fa9dd` and `b5735730`.
3. **multi-host-runtime Phase 4.** Dispatch `design-author` with spec v1.2 (`b51c5b2a`) and plan v1.2 (`e32ffe5c`) as input. The plan's "owed" list is in its v1.2 report and also inside the plan.
4. **codex-tdd-gate-defects plan audit cycle 2.** Run `hmad-dispatch audit-cycle --feature codex-tdd-gate-defects --phase plan --cycle 2 --passes 1 --surfaces codex --gated docs/01-plan/features/codex-tdd-gate-defects.plan.md --legs codex --project-tests h-mad/tests --suite-cmd "/opt/anaconda3/bin/python -m pytest h-mad/tests -q -p no:cacheprovider"` plus a doc-auditor delta review of plan v1.0→v1.1 (`85d61ba8`). Spec v1.1 (`96bf1cd1`) already carries S-1..S-6.
5. **Operator pre-step, required before any live verification.** Create the symlinks `~/.agents/skills/{h-mad,handoff}` and `~/.gemini/config/skills/{h-mad,handoff}` pointing into `/Users/kimhawk/orca/skills`. The merge-order cycle was broken on the assumption that this is done.
6. **Merge order:** codex-tdd-gate-defects, then grok-codex-fallback, then multi-host-runtime. Rebase each onto its predecessor before its 5c baseline. multi-host-runtime's live smoke runs AFTER local integration into main and BEFORE push; if it fails, `git revert` the unpushed merge.

## Open / Blocked Items

- **grok-codex-fallback Tasks 5–17** are in progress.
  - Location: `repo: /Users/kimhawk/orca/skills · branch: feature/216-grok-codex-fallback · worktree: /Users/kimhawk/orca/skills-grok-codex-fallback`
  - 5c baseline is `1a8450c2`; impl-plan v1.3 is on the branch.
  - Task 17 is the live `exec grok` smoke. It must use the worktree wrapper by absolute path and read back `b.txt`, and it halts to the operator if grok cannot run.
  - Scratch prompts live in `/private/tmp/claude-501/-Users-kimhawk-orca-skills/8a0b0625-ef06-41aa-9d4f-04fe14f2a32f/scratchpad/t{1..4}_{red,green}.*`.
- **multi-host-runtime**: Phase 4 not started, unblocked.
- **codex-tdd-gate-defects**: Phase 3 cycle 2 not started, unblocked. It depends on the Next Step 5 symlinks only for the live V-0/V-1 steps.
- **grok quality measurement** (GREEN, mutation, wiring, audit precision) is deferred by D4 to a follow-up. It is unchanged since 2026-09-28 (todo from the grok brief).
- **Carried from `2026-09-15-main__two-false-task-premises.md`**, unchanged and **not re-verified this session**:
  - (a) `docs/skill-candidates.md` open rows, 51 as of 2026-09-15. Census with `python3.11 handoff/scripts/skill_candidates_census.py --list-open docs/skill-candidates.md`.
  - (b) Close the `exec-pane` wrapper leak with a conftest finalizer; see the skill-candidates row.
  - (c) Send a pointer to HemaSuite: `/Users/kimhawk/orca/HemaSuite/docs/handoffs/2026-09-14-main__wsg-backlog-two-items-owed-here.md` Next Step 1 is answered by `docs/04-report/features/wsg-56-impl-plan-ac-enumeration.probe.v1.md`.
- **Closed from `2026-09-21-main__assembler-wiring-drops-counts-and-guards.md`**: fixed in `448fd8f3` ("stop the assembler dropping counts and guards on wiring tasks"). The sibling item it mentions (`--test-path` subproject-relative) stays on HemaSuite's list; SKILL.md already documents a `test_path_misrooted` refusal.
- **Closed from `2026-09-23-main__hemasuite-foreign-three.md`**:
  - whitespace squeeze: `fd20459`;
  - #89 anchor migration: `a82d9a4`;
  - #106 coordinator handle and backend env: `9af64b5`.
- **HemaSuite #28 runs with the codex TDD hook disarmed** until codex-tdd-gate-defects ships and is live-verified.
  - Location: `repo: /Users/kimhawk/orca/HemaSuite · branch: feature/28-review-manifest-guideline-evidence`
  - Ownership stays here; HemaSuite only waits.

## Context for Next Session

**Claims:** all three features are released at this closeout (session 8a0b0625). A new session should `--claim` each one before working it.

**State (`docs/.bkit-memory.json`, gitignored):**

| Feature | State |
|---|---|
| grok-codex-fallback | `phase=step5`, current 5, last_completed 4. The Claude TDD hook is nominally armed but inert (see Key Learnings). |
| multi-host-runtime | current 4, last_completed 3 |
| codex-tdd-gate-defects | current 3, last_completed 2 |

**Worktree:**
- Worktree root: `/Users/kimhawk/orca/skills-grok-codex-fallback`, branch `feature/216-grok-codex-fallback` (9 commits ahead of main; untracked `graft/` only).
- Parent repo: `/Users/kimhawk/orca/skills`, branch `main`.

**Uncommitted changes (main):** pre-existing and not this session's: `.gitignore`, `.ignore`, `.mcp.json`, `AGENTS.md`, `docs/03-analysis/jev-system-one-adaptation.md`, `opencode.json`. Only `docs/learnings.md` is this session's, and it is committed with this handoff.

**Foreign stash:** `stash@{0}` ("feat resolved-model") is untouched, but it was accidentally applied once and then restored.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills-grok-codex-fallback   # grok implementation
git status --short                                   # expect only ?? graft/
/opt/anaconda3/bin/python -m pytest h-mad/tests/test_grok_fixtures.py h-mad/tests/test_h_mad_state_fallback_agent.py h-mad/tests/test_h_mad_assemble_tdd_agent.py h-mad/tests/test_h_mad_resolved_model_grok.py -q -p no:cacheprovider   # expect 40 passed
```

**Related docs:**
- grok-codex-fallback:
  - spec v1.4 `docs/01-plan/features/grok-codex-fallback.spec.md`
  - design v1.2 `docs/02-design/features/grok-codex-fallback.design.md`
  - impl-plan (branch) `docs/01-plan/features/grok-codex-fallback.impl-plan.md`
  - audit origins `docs/03-analysis/grok-codex-fallback.audit-origins.jsonl`
- multi-host-runtime: `docs/01-plan/features/multi-host-runtime.{brainstorm,spec,plan}.md`
- codex-tdd-gate-defects:
  - `docs/01-plan/features/codex-tdd-gate-defects{-brainstorm,.spec,.plan}.md`
  - blocked T7 report `docs/03-analysis/probes/codex-tdd-gate-defects/hemasuite-t7_green.blocked1.report.md`
