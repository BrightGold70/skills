# Handoff — phase5-gate-feature-scope: public-text review ruled; Drop-Grok and OMC retirement shipped

**Date:** 2026-11-26
**Branch:** main
**Project:** skills
**Supersedes:** 2026-11-25-main__phase5-gate-phase4-exit.md, 2026-11-26-BrightGold70-h-mad-app-profile__h-mad-app-profile-start.md
**Next-Session Focus:** phase5-gate-feature-scope — dispatch spec-author, plan-author and design-author with the pre-commit review's rewrite list (operator ruled option C), then operator wording approval; 5a stays held until the h-mad-app-profile lane finishes its current audit round.
**Suggested-Skills:** h-mad (the feature; read `references/teammate-authors.md` before the first author dispatch), handoff (closeout), verify-hmad-gates (gate changes in Phase 5)

## Session Summary

Resumed from the Phase 4 exit. Shipped and pushed three things on `main` (`origin/main` = `0975a796`): the OMC no-type patch retirement (`52d88bd4`, OMC 5.8.9 verified fixed), Drop Grok as an audit/review leg (`95f10269`, full suite 9348 passed, 4 new mutation rows ALL_CAUGHT), and the h-mad-app-profile handover brief (`0975a796`). Ran a memory dream (index 19,485 → 17,498 B). Started h-mad-app-profile and handed it to its own lane, which took it over and is in Phase 2. For phase5-gate-feature-scope, the operator confirmed a bot-relayed go-ahead for Phase 5 and the pre-commit public-text review ran (not safe to commit as-is: 0 bypasses, 24 weakness passages, 7 private details); the operator ruled option C. No phase5-gate document has been edited or committed yet.

## Key Learnings

- **Compare collected test IDs, not totals.** A suite's `N passed` and `--collect-only` counts measure different things (52d88bd4 collects 9,350 while its runs pass 9,348); my expected count was off by 2 for that reason, and only an ID diff (`comm` over sorted node ids) proved the change was exactly −7/+5.
- **bkit's G-012 refuses a command whose TEXT contains `curl|wget|eval(`-style alternations** — including a read-only `grep` searching for them. Delegate such scans to a reviewer agent or split the pattern.
- **A mutation-harness row costs ~15-20 min here** (each row re-runs the spec's 12-file command); and the harness edits files in place, so never run the full suite in the same tree meanwhile.
- **The memory index is written by other lanes concurrently** — diff against a fresh backup before attributing growth (a HemaSuite lane added 29 B to its own hook while I edited mine).
- **A new Orca agent lane in a fresh worktree stops at Claude's folder-trust prompt**, and a second taker lane can appear; locate the real owner by its transcript's project folder (`~/.claude/projects/<slug>/<session>.jsonl`), not by worktree names.

## Next Steps

1. **Public-text edits (option C), via the owning authors.** Read `h-mad/references/teammate-authors.md` first, then dispatch `spec-author`, `plan-author`, `design-author` (one each; in parallel is fine, separate files) with the rewrite list in the private review `/Users/kimhawk/orca/_worktree-backups/2026-11-24/phase5-gate-feature-scope/precommit-public-text-review.private.md` (sha256 `c4f3f709…`; must=23, should=9). Pre-edit copies: `.../phase5-gate-feature-scope/pre-public-edit-20261126-140940/`. Then a delta self-review per diff, then operator wording approval. The brainstorm (L22, L49, L67) is the orchestrator's to edit. Rulings: last section of `.../plan-cycle1-decision-sheet.md`.
2. **Then the feature worktree:** under option C the docs are NOT committed to main; copy the edited untracked docs into a new feature worktree from `main` and commit them only on the local feature branch (not pushed). Re-check hashes, claim (`h_mad_resume_decision.py --state docs/.bkit-memory.json --feature phase5-gate-feature-scope --session-id <id>`, oracle observed `enter_autonomous`, owner `None`).
3. **5a — HELD** until the h-mad-app-profile lane (`/Users/kimhawk/orca/workspaces/skills/h-mad-app-profile`) finishes its current audit round: 5a sets `step5`, which arms the OLD gate across `orca/skills` and would block that lane's Codex audits. Check its state and tell it before arming. Then `implplan-author` with `open-decisions-5a.md` (OD-1..15).
4. **Probe privately** the one unverified audit claim the review flagged (decision sheet, last section, "Open, private"). Never in public text.
5. **At landing:** final public-text pass; publish with option A's scoped Security wording; redact the four flagged audit reports with `[redacted: private, operator record]` markers.

## Open / Blocked Items

**phase5-gate-feature-scope** (repo: `/Users/kimhawk/orca/skills` · branch: main · worktree: none yet):
- State observed 2026-11-26: `current_phase 5`, `last_completed_phase 4`, owner `None`, `last_marker phase4_exit_cap_wording_approved_2026-11-25`, oracle `enter_autonomous` — do not start Phase 5 from the token alone; the operator's go-ahead has the 5a hold attached.
- Documents (untracked, unchanged today): spec v1.16 `29e0fa44`, plan v1.15 `5ce72c40`, design v1.9 `cf75fd79`, design sidecar `8eb5207a`, brainstorm `f0c39cda`.
- Pre-commit review: DONE (report above); edits not started — status: next step 1.
- New evidence (private, cite by path): `/Users/kimhawk/.orca/bots/hawk-orca-bot/reports/hmad-codex-plan-audit-block-report.md` — field evidence for the repo-wide arming problem this feature fixes (a HemaSuite 5b audit refused under Codex). Logged in `.../phase5-gate-feature-scope/evidence-log.private.md`.
- Landing risk tests (`test_symlinked_hook_runs_its_own_trees_judge`, `h-mad/tests/test_h_mad_tdd_gate_judge.py:472`; `test_hook_reads_authorship_from_the_state_line_not_the_environment`, `test_h_mad_tdd_gate_peers.py:113`) — unchanged since 2026-11-25, Phase 5 must run them.
- Plan sidecar `docs/01-plan/features/phase5-gate-feature-scope.plan.audit.v3.md` needs findings' exact text — unchanged since 2026-11-25, blocks nothing.
- Not measured / not re-run (from 2026-11-25): unchanged.

**Closed this session (from the predecessor's list):**
- Item 1 (operator decisions before 5a) — decided 2026-11-26: proceed; order review → edits → worktree → claim → 5a; 5a held for the app-profile lane.
- Item 2 (pre-commit review) — review done, rulings recorded (option C, redact-with-markers, authors + approval); the edits are next step 1.
- Item 7 (drop Grok as reviewer) — done, `95f10269`, pushed.
- Item 8 (OMC no-type patch) — retired, `52d88bd4`, pushed; OMC 5.8.9 MCP server starts without `node_modules`, so the npm install half was not needed. The startup `omc-codex-mcp-no-type … MISSING` line is gone (hook copied, state re-checked OK).
- Item 13 (`/memory-dream`) — done: 3 Active entries archived, notebooklm note corrected, 32 Feedback hooks shortened; index 17,498 B (70%), `.last-dream` 2026-11-26.
- Brief `2026-11-26-BrightGold70-h-mad-app-profile__h-mad-app-profile-start.md` — handed over and taken over (session `0f32e68b`, stamped `**Taken-Over-By:**`); that lane now owns h-mad-app-profile (repo `/Users/kimhawk/orca/skills` · branch `BrightGold70/h-mad-app-profile` · worktree `/Users/kimhawk/orca/workspaces/skills/h-mad-app-profile`; observed `current_phase 2`, brainstorm v2.0 approved, Drop-Grok merged in). Not this lane's item any more.

**Carried, unchanged unless noted:**
- OMX 0.21.5 → v0.22.24, then `omx setup` once (Orca home `.omx` is a symlink) — unchanged.
- Code 127 check in the interactive codex pane (`term_39f30d1a-a7f7-4d58-acb2-548f49bd6c45`) — unchanged.
- P16: confirm closed — unchanged; a `h-mad: codex hemasuite-p16 · running` comment was still on a worktree at 2026-11-26.
- Reason Network: `reason-network folder <path> off` for private folders before anyone joins — unchanged; daemon PID 27220 up 2 d 04 h, hand-started.
- **Macmini (operator, after `git pull` to ≥ `0975a796`) — REVISED:** (1) `cp ~/orca/skills/docs/patches/patch-verify-on-update.sh ~/.claude/hooks/` (new hook, npm block removed); (2) `python3 docs/patches/codex-duplicate-handoff/verify.py --fix`; (3) omc-no-type steps DROPPED (retired); (4) OMC `node_modules`: probe `node <cache>/<ver>/bridge/mcp-server.cjs </dev/null` first, install only if it fails; (5) `ln -s ~/orca/skills/memory-dream ~/.claude/skills/memory-dream`; (6) `agent-messaging` links, OMX Node path; (7) optional: copy the 4 Stitch skills. Unreachable by ssh.
- Private gate follow-ups S4, S5, R2, R3, T1 and one new (`/Users/kimhawk/orca/_worktree-backups/2026-11-23/skills-p14-gate-exception/open-gate-finding.md`) — unchanged; re-ask sub-project relative state writes after the feature.
- Codex and Reason Network, Gate work earlier, Owned elsewhere (HemaSuite #187 worktree, AC-7 live run, P16), Codex environment, Memory store, Accepted/informational — all unchanged since the 2026-11-25 handoff (see it for the full lists); OMC/Claude Code block: the no-type MISSING line is closed, the rest unchanged.
- The HemaSuite `contested-claims-author-report` lane passed `--surfaces codex,agy,grok`; that lane must use `codex,agy` (not this repo's code).

- Memory index at 17,687 B (71%, target 70%) after another lane added an entry during this closeout; `links 1038/1051`, `orphans 0`, `last_dream 0d`. The next dream should archive whole settled entries (hook trimming is exhausted).

**New this session:**
- Stitch skills installed in `~/.claude/skills/` (shadcn-ui, extract-design-md, enhance-prompt, taste-design; upstream `75f4696`, reviewed 25/25 files, unscoped `Bash` pre-approval removed, see each `STITCH-SOURCE.md`). The other 12 need a Stitch MCP setup — deferred.

## Context for Next Session

**Files touched this session:**
- Committed: `docs/patches/omc-codex-mcp-no-type/` (retired), `docs/patches/patch-verify-on-update.sh`, `pytest.ini`, `docs/patches/codex-duplicate-handoff/tests/test_codex_duplicate_handoff_verify.py`, `h-mad/SKILL.md`, `h-mad/references/state-schema.md`, `h-mad/scripts/h_mad_state_schema.json`, `h-mad/tests/test_grok_*_docs.py`, `h-mad/tests/mutation-specs/grok_audit_surface.json`, `docs/handoffs/2026-11-26-BrightGold70-h-mad-app-profile__h-mad-app-profile-start.md`
- Outside the repo: `~/.claude/hooks/patch-verify-on-update.sh`, `~/.claude/skills/{shadcn-ui,extract-design-md,enhance-prompt,taste-design}`, auto-memory (dream + OMC + No-Grok notes), the private phase5-gate directory (review, rulings, evidence log, pre-edit copies)

**Uncommitted changes:** the 20 untracked `phase5-gate-feature-scope` docs only (do not commit to main — option C).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch
shasum -a 256 docs/01-plan/features/phase5-gate-feature-scope.{spec,plan}.md docs/02-design/features/phase5-gate-feature-scope.design.md   # 29e0fa44 5ce72c40 cf75fd79
```

**Related docs:** private review and decision sheet (paths above); `h-mad/references/teammate-authors.md`; `h-mad/references/phase5-substeps.md`.
