# Handoff — exec-missing-report-recovery SHIPPED via /h-mad

**Date:** 2026-07-30
**Branch:** main
**Project:** orca/skills (h-mad + handoff skills)

## Session Summary

Ran a full 7-phase `/h-mad "exec-missing-report-recovery"` end-to-end and shipped it: `hmad-dispatch exec` now recovers from an empty primary verdict channel (auto-`--log` retained on empty, reserved rc 3 over a clean exit, last-`^(STATUS|VERDICT):` recovered to stdout, git tree-delta) instead of silently exiting 0 — turning the manual playbook the earlier `feat/exec-missing-report` docs merge described into wrapper behavior. Merged to main `0b3a642`, pushed, both suites green. This continued the day's arc (prior: `2026-07-30-main__dispatch-prompt-size-frontier-92kb.md`).

## Key Learnings

- **A review finding can be right about the symptom and wrong about the prescription — check it against the tests before applying.** The 5e spec-review returned DRIFT with 2 findings that matched my *design doc's words* but contradicted FR-1.4 and the RED tests. I applied the drift-fix before verifying → it broke 2 tests. The impl was correct; the *design doc* was over-specified. Reverted, back-propagated design to v1.2. [[feedback verify-review-finding-before-acting]] — reinforced.
- **The assembler's residual-slot preflight also fires on slot tokens that appear in inlined doc CONTENT.** My spec/plan prose wrote the literal `<REPORT_FILE_PATH>`; inlined into the audit prompt it tripped `ASSEMBLE: HALT unfilled_slot` (the spec text is substituted after the slot). Fix: refer to slots by bare name (`REPORT_FILE_PATH`), never bracketed, in feature docs — same rule SKILL.md step 7.2 already states for templates.
- **The feature dogfooded itself live.** During the 5e-review dispatch, `exec agy` timed out (rc=1, empty output) and the NEW recovery arm fired correctly: `EMPTY final message — agent exited 1` (rc NOT overridden to 3), `tree delta: 5 changed`, rc=1 preserved.
- **The in-flight-skill-edit hazard is real but benign here:** a transient `hmad-dispatch.sh: line 1597: syntax error` appeared when a dispatch read the file mid-GREEN-write; `bash -n` was clean once the write completed. Editing the live symlinked skill during a run risks a half-read.
- **`exec agy` is less reliable than the pane for long reviews** — it timed out twice (Gemini capacity), while the pane agy (report-file transport) answered all 8 audit/review dispatches cleanly. Prefer the pane for agy reviews; exec agy is fine for short audits.
- **`h_mad_state_write.py` rejects `current_phase=complete`** (not a schema enum) — completion is carried by `last_completed_phase=7` + the shipped report, not a `current_phase` value.

## Next Steps

1. [suggested] Nothing owed on this feature — it is shipped, merged, pushed, both suites green. Optional: run one live `/h-mad` 5d/5e on the DEFAULT exec path to confirm the recovery arm never false-triggers on a normal (non-empty) run in a real feature. — `h-mad/SKILL.md` §"Exit-code dispatch for 5d/5e".
2. [carry] #2 `wait --not-while-regex 'Waiting for background terminal'` false-idle guard — still unit-tested only, awaiting a HemaSuite live exercise (from the 2026-07-29 arc). — `h-mad/scripts/hmad-dispatch.sh` `_cmd_wait`.

## Open / Blocked Items

- None for exec-missing-report-recovery — COMPLETE (match 100%, archreview READY_TO_MERGE, merged `0b3a642`).
- #2 false-idle guard live validation — status: delegated to a HemaSuite session (2026-07-29), not blocking. repo: `/Users/kimhawk/orca/HemaSuite/hematology-paper-writer` · branch: `main` · worktree: main (Orca-managed).

## In-Flight Processes

None — all Codex/agy exec + pane dispatches completed or were reaped; no live background work at handoff.

## Context for Next Session

**Feature shipped this session (feature/211, merged + deleted):**
- `h-mad/scripts/hmad-dispatch.sh` — `_cmd_exec` empty-output recovery (rc 3 + log recovery + tree delta), both codex/agy branches
- `h-mad/SKILL.md` — FR-6 docs (rc 3 + exec terminal-mode; playbook retained)
- `h-mad/tests/test_hmad_dispatch_exec.py` + `h-mad/tests/stubs/{codex,agy}` — RED+GREEN tests, all guards mutation-verified
- `docs/01-plan/features/exec-missing-report-recovery.*` + `docs/02-design/…design.md` (v1.2) + `docs/03-analysis/…analysis.md` + `docs/04-report/features/…report.md`

**Commits on main:** `b302c9e` (docs P1-5b) → `2914900` (impl) → `a47c3d1` (P6-7 docs) → `0b3a642` (merge). The earlier `feat/exec-missing-report` docs (`68c9f22`/`53807f1`) reached origin with this push too.

**Uncommitted changes:** none (local `main` = `origin/main` `0b3a642`).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main && git pull --ff-only
/opt/anaconda3/bin/python3 -m pytest h-mad/tests/ -q   # 754/0
```

**Related docs:**
- `docs/04-report/features/exec-missing-report-recovery.report.md` (closure)
- Prior handoff (same day): `docs/handoffs/2026-07-30-main__dispatch-prompt-size-frontier-92kb.md`
