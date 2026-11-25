# Handoff — phase5-gate-feature-scope: Phase 4 exited, Phase 5 not started

**Date:** 2026-11-25
**Branch:** main
**Project:** skills
**Supersedes:** 2026-11-25-main__phase5-gate-design-cycle2.md
**Next-Session Focus:** `/h-mad phase5-gate-feature-scope`, Phase 5 from 5a, once the operator says when the worktree may be created and how the untracked documents reach it. Do not let the resume token start it unasked.
**Suggested-Skills:** h-mad (the feature, 5a), verify-hmad-gates and verify-hmad-claims (gate or writer changes), memory-dream (due 2026-11-26)

## Session Summary

All 13 findings of design cycle 2 were verified against the tree (11 must, 2 should; none rejected). The documents were revised by their authors, one at a time, to **spec v1.16, plan v1.15 and design v1.9**, with two advisory delta reviews (of design v1.7 and v1.8) and a final check by the orchestrator. The operator approved the wording of all three and agreed the routing of what stays open; **Phase 4 is exited** on the two-round cap (no passing stamp exists; the gate on the cycle 2 report stays FAIL must=10 should=2). Nothing is staged or committed, no gate code has changed, and Phase 5 has not started.

## Key Learnings

- **A mutation experiment needs its mirror arm.** I first called a finding half wrong from one arrangement (anchors moved to the helper); the opposite one (anchors left in the caller, helper unused) showed every spec stays green. The finding held in full.
- **Simplest form first.** I recommended a deadline for a long-lived process, then an explicit ending for it; each revision drew a must in its own new text. The last review's must and about half of its shoulds were about that ending, so the operator had it taken out (no review has read the result).
- **Ask the operator about the whole class.** My first question on a Python difference named one place and one call; the author measured more. Re-ask, do not stretch the ruling.
- **A sidecar `[key]` does nothing unless the report's own finding carries the same key.** The plan's sidecar uses keys only, so its acknowledgements do not count in the gate (cycle 1's codex report still reads measurement=3). The finding's exact text is what matches.
- **Delta tooling needs a commit.** `h_mad_delta_stage.py` cannot stage a review of untracked documents; the reviews were dispatched by hand, report names outside the audit grammar.
- **Never commit public text that describes a state in which a gate does not see a record.** That detail of this feature is private (`residual-3.12.private.md`).

## Next Steps

**The feature** (private directory for everything below: `/Users/kimhawk/orca/_worktree-backups/2026-11-24/phase5-gate-feature-scope/`; the end of `plan-cycle1-decision-sheet.md` holds every disposition, ruling and the Phase 4 exit record)

1. **Operator decisions before 5a:** (a) when the worktree may be created and how the documents get there: they are untracked, so a worktree made from `main` will not contain them; either copy them in, or complete item 2 and commit them first; (b) arming gates every lane that shares this repository, so pick a moment for it. The state reads `current_phase 5`, so the resume oracle answers `enter_autonomous`: a session must not take that as an order to start.
2. **Pre-commit review of public text** (nothing is committed until it is done): spec, plan, design, all audit reports, `.effort.json` files and fixtures. The operator chose to settle the spec's Security sentence ("No public artifact ... reproduction of a gate weakness") and the ruled limits it sits beside there, not now. The lists are in the private author reports (`author_*_spec_v16`, `author_*_plan_v15`). Reports that quote private detail are private: never commit the private directory or an author report.
3. **Claim and resume:** `python3 ~/.claude/skills/h-mad/scripts/h_mad_resume_decision.py --state docs/.bkit-memory.json --feature phase5-gate-feature-scope --session-id <id>`, then claim. Re-check the hashes below first.
4. **5a impl-plan** (`implplan-author`): write the OPEN-DECISION items (`open-decisions-5a.md`, OD-1 to OD-15; some are notes, OD-8 is in the sidecar, OD-9 points to the private record, OD-15 is item 2). One wiring task per row and step of the plan's wire table. Documents still say their wording is not approved: correct that at each one's next revision.
5. **Landing risk** (accepted privately): re-state it beside the landing report; it stays out of public text. **Phase 5 must run** `test_symlinked_hook_runs_its_own_trees_judge` (`h-mad/tests/test_h_mad_tdd_gate_judge.py:472`) and `test_hook_reads_authorship_from_the_state_line_not_the_environment` (`h-mad/tests/test_h_mad_tdd_gate_peers.py:113`) for the `_tree_b` helper edit. Nothing has run them with it. A worktree is required before 5a.
6. **Plan sidecar:** `docs/01-plan/features/phase5-gate-feature-scope.plan.audit.v3.md` needs the findings' exact text in place of keys alone before anyone relies on it (see Key Learnings); Phase 3 is closed on the cap, so this blocks nothing.

**Other work**

7. **Drop Grok as a reviewer** (operator, 2026-11-25): in a worktree, not inside the feature: `h-mad/SKILL.md` §"Never gate on one audit pass" and §"Teammate audit leg", `h-mad/tests/test_grok_audit_surface_docs.py`, `test_grok_fallback_docs.py`. Phase 5 fallback and dispatch support stay.
8. **OMC 5.8.7:** retire the no-type patch (`docs/patches/omc-codex-mcp-no-type/README.md` §"Retiring"), remove it from `patch-verify-on-update.sh` and the Macmini steps; `npm install --omit=dev --ignore-scripts` then `npm rebuild better-sqlite3` in the 5.8.7 cache, never `scripts/plugin-setup.mjs`.
9. **OMX:** update 0.21.5 to v0.22.24, then `omx setup` once (the Orca account home may refuse: its `.omx` is a symlink).
10. **Code 127 check** in an interactive codex pane (pinned `term_39f30d1a-a7f7-4d58-acb2-548f49bd6c45`).
11. **P16:** confirm closed; its HemaSuite worktree `feature-016-csa-column-mapper-jev` no longer existed at this session's resume, and a "running" comment remains on the `Current studies` workspace.
12. **Before anyone else joins the Reason Network team:** `reason-network folder <path> off` for private folders.
13. **`/memory-dream`** (due 2026-11-26): `links 1035/1048`, `DANGLING=13`, `orphans=0`, `last_dream=6d`; index 19,466 B against 17,500.
14. **Macmini (operator, after `git pull`):** copy `docs/patches/patch-verify-on-update.sh` to `~/.claude/hooks/`; `python3 docs/patches/codex-duplicate-handoff/verify.py --fix`; omc-no-type `apply.py`/`verify.py` only until retired; `ln -s ~/orca/skills/memory-dream ~/.claude/skills/memory-dream`; probably `npm install`; `agent-messaging` links; OMX Node path. Unreachable by ssh: do not retry.
15. **Private gate follow-ups** S4, S5, R2, R3, T1 and one new (`/Users/kimhawk/orca/_worktree-backups/2026-11-23/skills-p14-gate-exception/open-gate-finding.md`); re-ask sub-project relative state writes after the feature.

## Open / Blocked Items

**phase5-gate-feature-scope** (repo: `/Users/kimhawk/orca/skills` · branch: main · worktree: none yet, required before 5a):
- **State observed 2026-11-25 17:24** (before the close): `last_completed_phase 4`, `current_phase 5`, `phase null`, `halt_reason null`, `owner_session_id None` (released), `last_marker phase4_exit_cap_wording_approved_2026-11-25`, oracle `enter_autonomous`.
- **Documents** (untracked): spec v1.16 `29e0fa44…`, plan v1.15 `5ce72c40…`, design v1.9 `cf75fd79…`, design sidecar `design.audit.v3.md` `8eb5207a…`; brainstorm v1.3. Every earlier version, diffs, author reports, delta reviews and probes are in the private directory.
- **Wording:** approved by the operator (spec v1.10 to v1.16, plan v1.8 to v1.15, design v1.1 to v1.9); design v1.9's new text has had no independent review (operator: "My diff check, then stop"). Author and orchestrator choices can still be reversed; they are in the `author_*` reports.
- **Rulings this session:** F1, F3, F4 corrected in the design; streaming process: waits only, no ending, a failed exchange kills the direct child; a partly answered first batch counts whole; answered paths keep their answer; the Python residual is ruled and its detail private; routing of the rest to OPEN-DECISIONs; public limits settled at pre-commit review.
- **Not measured:** whole-hook medians; codex and agy hooks; a target in another checkout (as before; also OD-14).
- **Not re-run by me:** the author's five-thousand-run probe of the Python residual beyond the overlap I repeated; Claude hook behaviour under any of it; Linux.

**Codex and Reason Network** (inherited, unchanged unless noted): code 127 (item 10); edits outside the repo in both Codex `hooks.json` with backups under `~/.codex-backups/2026-11-24-…`; OMX upstream (#4153 fixed by #4155; gaps `node@NN`, `process.execPath` unreported); `agent-messaging` / `reason-network` skill review gaps (`review2.md` in `/Users/kimhawk/orca/_worktree-backups/2026-11-24/agent-messaging-codex-hooks/`); Reason Network pilot, one machine, one member, daemon PID 27220 hand-started (up 1 d 07 h), not a login service; longer idle, another machine and plain `~/.codex` not tested.

**Gate work, earlier** (inherited, unchanged): option-judging fix `74ba0661` (last test-only edit not re-reviewed); sub-project relative state writes refused today, re-ask after the feature; `--authors-test` `e506d871` (edits after its last review not re-reviewed, limits accepted); retired P14 exception (backup with item 15).

**Owned elsewhere** (inherited, not re-checked): HemaSuite #187 worktree, AC-7 live run (session f9973721), HemaSuite drafting quality without `CLAUDE.md`; P16 per item 11.

**Codex environment** (inherited, unchanged): `~/.codex/AGENTS.md` Orca block, `gpt-6-luna` subagent defaults, `omx setup` on both homes, backups `~/.codex-backups/2026-11-22-pre-omx-setup/`, `…-orca-home/`, `AGENTS.md.pre-orca-block-20261122`, `config.toml.pre-subagent-model-20261122`; no implementer gate dispatch has run with the OMX `PreToolUse` hook; duplicate codex skills in backup; ai-memory stdio bridge and serena timeout 180; `code_mode` warning, ai-memory and serena inside codex not investigated; `[[skills.config]]` pins break on Pocock plugin update; known limits of `codex-duplicate-handoff`, unanchored hook-trust lines and hard-link kinds accepted.

**OMC and Claude Code** (inherited, unchanged): `zod` advisory GHSA-mrhx-c7xc-m3w5 not fixed; `.omc/notepad.md.bak-2026-11-22-pre-trim` is the only copy of the old entries; code mode stays `0`, not re-tested since 2.1.330; ai-memory calls resolve to `default/scratch`: pass `workspace=default`, `project=skills`; `~/.claude.json` context7/sequential-thinking entries expected; startup still prints `omc-codex-mcp-no-type … MISSING`, expected until item 8.

**Memory store** (inherited, unchanged): backups under `~/.claude/memory-dream-backups/`, no prune before 2026-12-19; 10 dangling links kept as markers, 3 not examined; deferred ideas (generic `split`, rejected hook-older-than-body check).

**Accepted or informational** (inherited, unchanged): Macmini unreachable by ssh; its untracked `GEMINI.md`, `.gemini/`, `.grok/` never staged; two timing tests with fixed sleeps; Pyright `timeout=None` warning at `test_hmad_dispatch_exec_stamp.py:458`; opencode `$schema` change (`bd6a47ca`); Rust toolchain; foreign PID 32561; items since 2026-11-08 listed in the superseded handoff; local branch `fix/suite-timeout` is an ancestor of `main`. Scratch, safe to lose: the session scratchpad (what matters is in the private directory).

**Closed:** design cycle 2 premise check (all hold); design cap exit terms (sidecar, routing); wording approvals; this feature's Phase 4.

## In-Flight Processes

| PID | Command | Log | Started | Elapsed @ handoff | ETA | What to check on exit |
|---|---|---|---|---|---|---|
| 27220 | `reason-network daemon` | `~/.reason/network/daemon.log` | 2026-11-24 09:38 | 31 h 46 m | stays up | `reason-network doctor`; a reboot stops it |

## Context for Next Session

**Files touched this session:**
- Untracked feature documents: spec, plan, design (revised by their authors) and `docs/02-design/features/phase5-gate-feature-scope.design.audit.v3.md` (new)
- `docs/handoffs/2026-11-25-main__phase5-gate-phase4-exit.md`, `docs/learnings.md`, `docs/skill-candidates.md` (this close)
- Outside the repo: the private directory; auto-memory (project entry)

**Uncommitted changes:** 20 untracked `phase5-gate-feature-scope` files only. Do not stage them before item 2.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch
shasum -a 256 docs/01-plan/features/phase5-gate-feature-scope.{spec,plan}.md docs/02-design/features/phase5-gate-feature-scope.design.md   # 29e0fa44… 5ce72c40… cf75fd79…
```

**Related docs:** the private directory's `plan-cycle1-decision-sheet.md`; `docs/02-design/features/phase5-gate-feature-scope.design.audit.v2.p1.md`; `h-mad/references/phase5-substeps.md`; `h-mad/references/teammate-authors.md`.
