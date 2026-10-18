# Handoff — grok-audit-surface: Phase 3 plan audit in flight

**Date:** 2026-10-18
**Branch:** main
**Project:** skills
**Supersedes:** 2026-10-18-main__backlog-cycle-driver-landed.md

## Session Summary

Started `/h-mad grok-audit-surface`. The goal is to make grok a standing third audit leg (codex+agy+grok) on a document's first gating cycle, but only after a seeded-defect calibration shows grok beats agy. Phases 1–2 are done and committed, and plan v1.1 is committed. **Phase 3 audit cycle 1 (codex + agy) was still running at handoff:** both passes had finished and the full-suite step was running. Bootstrap needed repairs first: 8 stale skill copies were replaced with symlinks, and `docs/.bkit-memory.json` had vanished and was recreated.

## Key Learnings

- **Agents registered mid-session can't be dispatched yet.** Agent types load at session start, so a freshly registered `spec-author` is "not found". Substitute a `general-purpose` agent given the full `h-mad/agents/<name>.md` text as its contract. The types do appear later in the same session; they became available after about 10 minutes. Filed as a scout row.
- **Two install-check failures are false positives.** `INSTALL: FAIL issues=2` comes from `~/.agents/skills/{pdf,skill-creator}`, which are `anthropics/skills` vendor installs pinned in `~/.agents/.skill-lock.json`. They are not stale copies; they merely share a name with this repo's OpenCode variants. The operator chose to keep them. A backlog row is filed for the check.
- **SKILL.md documents a command that can't run.** It says `h_mad_audit_cycle.py --surfaces agy,grok`, but only `hmad-dispatch audit-cycle` parses `--surfaces`. Spec AC-6.2 fixes it.
- **The leak scan needed an exemption.** A design or impl-plan audit root must hold a byte-identical paired document, so a literal "no seed original anywhere" scan always refuses. Spec v1.2 adds a narrow exemption: a seed's original may appear in its own source doc's paired copy, never its expected text.
- **`--exit-check` already handles the leg-set change.** It refuses `codex+agy` → `codex` as `legs_changed`, and two codex-only revision cycles still reach READY. Adding grok needs no gate code change (spec FR-9; probed by spec-author).
- **Use the full pytest interpreter path.** Bare `python3.14` resolves to `~/.local/bin/python3.14`, which has no pytest. Use `/opt/homebrew/opt/python@3.14/bin/python3.14`. The auto-memory is corrected.

## Next Steps

0. **BLOCKER: plan audit cycle 1 came back `AUDITCYCLE: UNVERIFIED reason=unscorable_report:p2`. Repair agy before re-running.**
   - **Cause:** project `.agents/hooks.json` (untracked, created 2026-10-18 11:52) registers `python3 ~/.gemini/config/skills/h-mad/hooks/h-mad-agy-tdd-gate.py` on every agy tool call. `~/.gemini/config/skills/` does not exist, so the hook exits 2, agy treats that as a refusal, and every tool call fails.
   - **Effect:** p2 shows `tools=4 ok=0 failed=4`, so it read nothing. Every agy dispatch in this repo since 11:52 is hollow the same way.
   - **Remedy** (`h-mad/references/agy-runtime.md` §Install): `mkdir -p ~/.gemini/config/skills && ln -s /Users/kimhawk/orca/skills/h-mad ~/.gemini/config/skills/h-mad && ln -s /Users/kimhawk/orca/skills/handoff ~/.gemini/config/skills/handoff`. Then confirm one agy tool call succeeds.
   - The operator deferred this repair at close.
   - **Then re-run cycle 1 and commit nothing while it runs.** This run's `SUITE: FAIL passed=6685 failed=39 tree_moved=HEAD` is invalid, because the handoff commits landed mid-suite.
   - **Codex p1 did deliver:** `docs/01-plan/features/grok-audit-surface.plan.audit.v1.p1.md`. Read its findings; they stand on their own.
   - **The slot warning (`prompt carries live template slots <INLINE_PAIRED_*>`) is a false positive.** The plan's own prose names the slots, at assembled-prompt line 341.
1. **Collect plan audit cycle 1** (superseded by step 0's re-run). Read `/private/tmp/claude-501/-Users-kimhawk-orca-skills/1f39eb76-d775-4dc8-b33d-b680f83a32ee/scratchpad/plan_audit_c1.out`. Take the `AUDITCYCLE:` line, the `Effort:` block (low-evidence?) and the `SUITE:` line. Reports are in `docs/01-plan/features/grok-audit-surface.plan.audit.v1.*.md`, collected by the driver; if absent, use `/tmp/audit_grok-audit-surface_plan_cycle1_run20261018T114339Z-60516_p{1,2}.report.md`.
2. **Check every must-fix against source** (SKILL.md §"Verifying a review finding"). Tag its origin with `h_mad_audit_origins.py append`. Re-dispatch `plan-author` with the verified must-fix and should-fix bullets. Class rule: build-class drives the loop; measurement-class is acknowledged with its re-run command.
3. **Read a red suite against the known baseline first.** `SUITE:` red is expected here: 36 SKILL.md consumer tests fail environmentally on this Mac. Compare against that before calling it a regression.
4. **Run cycle 2.** Same invocation with `--cycle 2`. Per the round cap, revision cycles are codex gating plus a doc-auditor delta review. Cap: 2 gating rounds, then exit with OPEN-DECISIONs on impl-plan tasks.
5. **Then Phase 4:** dispatch `design-author`. The design owes four things:
   - the `HMAD_AUDIT_STEM_DIR` location outside the export roots;
   - AC-3.4 whole-cycle re-dispatch semantics;
   - the AC-10.1 pass-index mapping, not time order;
   - the scorer module name and fixture layout.

## Open / Blocked Items

**New this session:**
- **grok-audit-surface:** status in progress, Phase 3 cycle 1.
  - Location: repo `/Users/kimhawk/orca/skills` · branch `main` · worktree none.
  - Claim held by session `1f39eb76-d775-4dc8-b33d-b680f83a32ee`; it goes stale after 2h. Next session: run `h_mad_resume_decision.py`, then `--claim`.
  - State: `current_phase=3`, `codex_status=available`, `substrate={orca, exec}`.
  - Docs:
    - brainstorm `0be0f064`
    - spec v1.2 `1a470339` (sha256 `cd558ae1…`)
    - plan v1.1 `db990c70` (sha256 `6853fb92…`)
  - Author reports are in the scratchpad: `author_grok-audit-surface_{spec_v1,spec_v1.1,spec_v1.2,plan_v1,plan_v1.1}.report.md`.
- **Install check reports `INSTALL: FAIL issues=2`:** status known false positive. Backlog row "install check reports vendor-pinned skills as stale copies" is OPEN.
- **`h-mad-advisor-warn.sh` not wired (`WIRING: FAIL HOOK_NOT_WIRED`):** deferred; advisory only.
- **`docs/.bkit-memory.json` loss:** CLOSED as unrecoverable. The file is untracked and vanished with only its `.lock` left, so every pre-existing feature record is gone. It was recreated holding only grok-audit-surface. Do not expect older features to resume.
- **Stale-copy backups:** `/private/tmp/claude-501/-Users-kimhawk-orca-skills/1f39eb76-d775-4dc8-b33d-b680f83a32ee/scratchpad/skill-copy-backup/` holds the 8 replaced copies, which were byte-identical to the checkout. Safe to delete.

**Carried from 2026-10-18-main__backlog-cycle-driver-landed.md:**
- **Backlog row "mutation harness interpreter override" (`--python` flag):** OPEN, unchanged. Re-verified 0 occurrences of `"--python"` in `h-mad/scripts/h_mad_mutation_harness.py`.
- **backlog_cycle LOW review residuals** (no-`commits` KeyError, store-race restore, `git-failed` message omits the path, `resolve()` follows symlinks, trailing-backslash cell): deferred, unchanged since 2026-10-18.
- **Census `--help` crashes with `FileNotFoundError`:** deferred, unchanged.
- **`h_mad_mutation_harness.py:2300` `SyntaxWarning: 'return' in a 'finally' block`:** deferred, unchanged.
- **Full suite not rerun after the pin bump (`282ab531`):** superseded. Plan audit cycle 1 runs the full `h-mad/tests` suite, so read its `SUITE:` line.
- **NS2 HemaSuite feature/204 `no-mutation-spec`:** unchanged; HemaSuite's call. Repo `/Users/kimhawk/orca/HemaSuite`.
- **Foreign `stash@{0}` (`resolved-model`):** unchanged. Do not touch.
- **Bash pin blast radius:** unchanged and inert.
- **`.git/info/exclude` entries `/.agents/skills/` and `.trail/`:** keep; unchanged.
- **Row 1412 four-clock liveness limits:** watch-only; unchanged.
- **Agy-coder-fallback `review_independence_unrecorded` warning:** accepted; unchanged. Note that its state record was lost with the store.

## In-Flight Processes

| PID | Command | Log | Started | Elapsed @ handoff | ETA | What to check on exit |
|---|---|---|---|---|---|---|
| 60516 | `hmad-dispatch.sh audit-cycle --feature grok-audit-surface --phase plan --cycle 1 --passes 2 --surfaces codex,agy …` | `/private/tmp/claude-501/-Users-kimhawk-orca-skills/1f39eb76-d775-4dc8-b33d-b680f83a32ee/scratchpad/plan_audit_c1.out` | 20:43 | ~22m | suite step | `AUDITCYCLE:` + `SUITE:` lines in the log |
| 70162 | `python3.14 -m pytest -q h-mad/tests` (the cycle's suite) | stdout (captured by 60516) | 20:47 | ~18m | minutes | finishes into 60516's `SUITE:` line |

## Context for Next Session

**Files touched this session:**
- `docs/01-plan/features/grok-audit-surface-brainstorm.md`, `.spec.md`, `.plan.md`
- `docs/skill-candidates.md` (3 rows)
- `.trail/learnings/2026-10-18-h-mad-bootstrap-vendor-skill-collisions-hawk.md`
- `docs/.bkit-memory.json` (recreated, untracked)
- `~/.claude/agents/*.md` (6 symlinks), `~/.claude/skills/onecontext`, `~/.agents/skills/{brainstorming,docx,find-skills,frontend-design,pptx,ui-ux-pro-max,xlsx}` (symlinks)

**Uncommitted changes:** `docs/skill-candidates.md` (scout rows) plus this handoff; both are committed by this closeout.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
cat /private/tmp/claude-501/-Users-kimhawk-orca-skills/1f39eb76-d775-4dc8-b33d-b680f83a32ee/scratchpad/plan_audit_c1.out
/h-mad "grok-audit-surface"     # resume oracle → claim → continue Phase 3
```

**Related docs:**
- `h-mad/SKILL.md` §"Never gate on one audit pass", §"Teammate audit leg", §"Document-audit round cap"
- `h-mad/references/grok-runtime.md`
- `docs/03-analysis/hmad-audit-evidence-gate.measurement.md` (prior fabrication corpus)
