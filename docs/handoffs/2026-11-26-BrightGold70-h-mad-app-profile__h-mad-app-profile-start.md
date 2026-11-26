# Handoff — h-mad-app-profile: Phase 1 brainstorm drafted, awaiting operator approval

**Date:** 2026-11-26
**Branch:** BrightGold70/h-mad-app-profile
**Project:** skills
**Handover-From:** skills · main · session 6f371175-4b07-4f7a-8da7-6f4e3279a54b
**Taken-Over-By:** skills · BrightGold70/h-mad-app-profile · session 0f32e68b-45ba-4f53-a92b-86008129d2fc · 2026-11-26
**Supersedes:** none — first on this branch
**Next-Session Focus:** take over, then `/h-mad h-mad-app-profile` in this worktree; first action is getting the operator's approval of brainstorm v1.1 (Phase 1 gate), then Phase 2 spec via `spec-author`.
**Suggested-Skills:** handoff (takeover), h-mad (the feature), extract-design-md / taste-design (UX-track examples, optional)

## Session Summary

The operator asked to extend h-mad for general app development (UX/UI design, platform awareness) instead of building a second skill; the recommendation (update h-mad with an opt-in app profile) was accepted and the operator started `/h-mad h-mad-app-profile` in a new Orca worktree, then asked for the feature to run on its own lane. Bootstrap passed, the feature record was created, Phase 1's clarifying questions were answered, and brainstorm v1.1 was written. Nothing is committed; the claim was released for this lane to take.

## Key Learnings

- The h-mad core is already project-agnostic: SKILL.md's HemaSuite mentions are measured examples, and project rules live in `.h-mad/invariants.md`. The real blocker for app work is not UX but the test gates: about 27 scripts read pytest's summary line, and only Playwright is partly supported (as a wiring runner, `scripts/h_mad_wire_registry.py:23`).
- `docs/.bkit-memory.json` is gitignored, so this worktree has its own state file (created at bootstrap). Do not look for the record in `/Users/kimhawk/orca/skills/docs/.bkit-memory.json`.

## Next Steps

1. Take over this brief (`/handoff takeover`), then run `/h-mad h-mad-app-profile` from `/Users/kimhawk/orca/workspaces/skills/h-mad-app-profile`; the oracle should answer `resume_manual` at Phase 1. Claim with `h_mad_state_write.py docs/.bkit-memory.json --feature h-mad-app-profile --claim <session-id>`.
2. Show the operator `docs/01-plan/features/h-mad-app-profile-brainstorm.md` (v1.1) and get explicit approval (Phase 1 advance gate). Apply any correction as v1.2 and re-confirm.
3. Phase 2: dispatch `spec-author` (see h-mad §"Teammate authors"). The spec must settle the two items under the brainstorm's Open Questions: the pilot's first stack, and which of the five slices are v1-blocking.
4. Before Phase 5: agree ordering with `phase5-gate-feature-scope` (same repo; its Phase 5 arms the gate repo-wide and edits the same gate scripts).

## Open / Blocked Items

- **h-mad-app-profile** — status: Phase 1, brainstorm v1.1 awaiting approval. repo: `/Users/kimhawk/orca/skills` · branch: `BrightGold70/h-mad-app-profile` · worktree: `/Users/kimhawk/orca/workspaces/skills/h-mad-app-profile` (Orca selector `47c13b8f-e5c5-4169-8038-1c413c982778::/Users/kimhawk/orca/workspaces/skills/h-mad-app-profile`). Artifacts: `docs/01-plan/features/h-mad-app-profile-brainstorm.md` (untracked), `docs/.bkit-memory.json` (record: `current_phase 1`, owner released 2026-11-26).
- **Operator answers recorded in v1.1** (do not re-ask): platforms web, iOS/iPadOS, macOS; UX track inside Phase 4; runner adapters Vitest/Jest, Playwright (full), XCTest; JUnit/Gradle deferred with Android; Windows/Linux out; visual-regression baselines and non-Python mutation IN v1; release lane out; profile per project in `.h-mad/invariants.md` with a per-feature narrowing override; pilot Hematology_wiki (`/Users/kimhawk/Coding/Hematology_wiki`, `github.com/BrightGold70/Hematology_wiki` — inferred from the operator's "Hema_wiki"; confirm).
- **Dependency, blocked on ordering:** `phase5-gate-feature-scope` (main repo, Phase 4 exited, Phase 5 not started) — overlapping gate scripts.
- **Dependency, in flight in another lane:** `chore/drop-grok-reviewer` edits `h-mad/SKILL.md` (§"Never gate on one audit pass", §"Teammate audit leg"); this worktree was cut from `main` at `52d88bd4`, before it merges. Rebase or merge `main` before Phase 2 documents cite those sections.

## Context for Next Session

**Files touched this session:**
- `/Users/kimhawk/orca/workspaces/skills/h-mad-app-profile/docs/01-plan/features/h-mad-app-profile-brainstorm.md`
- `/Users/kimhawk/orca/workspaces/skills/h-mad-app-profile/docs/.bkit-memory.json` (gitignored)

**Worktree:**
- Worktree root: `/Users/kimhawk/orca/workspaces/skills/h-mad-app-profile` — branch: `BrightGold70/h-mad-app-profile`
- Parent repo: `/Users/kimhawk/orca/skills` — branch: `main`

**Uncommitted changes:** the brainstorm doc and the `docs/` skeleton from bootstrap, untracked.

**To resume:**
```bash
cd /Users/kimhawk/orca/workspaces/skills/h-mad-app-profile
git status --short --branch
python3 ~/.claude/skills/h-mad/scripts/h_mad_resume_decision.py --state docs/.bkit-memory.json --feature h-mad-app-profile --session-id <your-session-id>
```

**Related docs:** `h-mad/references/inline-protocols.md` §Phase 1 and §Phase 2; `h-mad/references/teammate-authors.md`.
