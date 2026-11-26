# Handoff — h-mad-app-profile: Phase 3 closed at the round cap; Phase 4 design next

**Date:** 2026-11-26
**Branch:** BrightGold70/h-mad-app-profile
**Project:** skills
**Supersedes:** 2026-11-26-BrightGold70-h-mad-app-profile__h-mad-app-profile-start.md
**Next-Session Focus:** `/h-mad h-mad-app-profile` in this worktree → Phase 4 (design): run the opt-in Stitch decisions into the design-author brief, dispatch `design-author`, then the dual-surface design audit (2-round cap).
**Suggested-Skills:** h-mad (the feature), handoff (READ first), design-md / generate-design (only if a pilot design under `ux_producer: stitch` is exercised; this repo itself declares no profile)

## Session Summary

Took over the start brief, restarted Phase 1 at the operator's request (brainstorm v2.2), and drove Phases 2 and 3 to exit. Spec v1.4 (51 ACs) and plan v1.3 are committed at `e66f43e4`; state reads `last_completed_phase=3, current_phase=4`. The plan audit ran two gating rounds (cycle 1 codex+agy FAIL 19/5; cycle 2 codex FAIL 9/1) and exited at the round cap through a corrective revision that was not re-audited, with one OPEN-DECISION the operator then ruled on. Outcome: Phase 3 done; Phase 4 not started.

## Key Learnings

- The audit assembler's duplicate-rubric preflight keys on each rubric file's FIRST LINE (`h_mad_assemble_audit.py:217`), so a plan quoting the invariants heading halted cycle 1 before dispatch, and a front-matter invariants file would halt every audit (`'---' appears 41x`). Filed as J57 on main (`360f4357`); this feature's spec AC-2.9 fixes only the front-matter half.
- `audit-cycle` dispatches via headless `exec`, so `PREFLIGHT: FAIL unresolved=codex,agy` (no pinned panes) does not block it — that refusal guards only pane `send`.
- Writing ANY non-ignored file into the worktree while an audit cycle's suite runs stamps `SUITE: … tree_moved=<path>` (cycle 2: the advisory delta-review report landed mid-suite). Run doc-auditor delta reviews before or after the cycle, never during.
- Spec-side findings must reach the spec BEFORE the plan revision: three codex "plan" findings had no spec AC to satisfy and forced a spec v1.3 round. Route by "does an AC exist?", not by which document the reviewer named.
- My own corrected census grammar (`[^A-Z0-9-]`) was wrong — it matched `DEFAULT_RUNNER:`. The spec-author caught it; the committed boundary is `(^|[^A-Za-z0-9_-])NAME:([ \`]|$)`.
- Stitch skills: `upload-to-stitch` as shipped routes the API key through the agent and argv and accepts any `--api-url`; installed only with local hardening (`LOCAL-EDITS.patch` in each skill dir). `extract-static-html` inlines arbitrary local paths into HTML that `code-to-design` uploads — held.

## Next Steps

1. Resume: `cd /Users/kimhawk/orca/workspaces/skills/h-mad-app-profile && python3 ~/.claude/skills/h-mad/scripts/h_mad_resume_decision.py --state docs/.bkit-memory.json --feature h-mad-app-profile --session-id <new-id>`. Within 2h of 08:58Z it reads `owned_elsewhere` (claim kept by `0f32e68b`, operator's choice): check `python3 ~/.claude/skills/h-mad/scripts/h_mad_lane_liveness.py <lane> --feature h-mad-app-profile`; this session has ended, so take it with `h_mad_state_write.py docs/.bkit-memory.json --feature h-mad-app-profile --claim <new-id>` (add `--force` only if the reading is not QUIET and you have confirmed `0f32e68b` is gone).
2. Phase 4: read `h-mad/references/teammate-authors.md`, then dispatch `design-author` (REPORT= path) with: spec v1.4, plan v1.3 (`docs/01-plan/features/h-mad-app-profile.{spec,plan}.md`), the plan's §"Next Steps" list of design-owed items (front-matter grammar, APP-DOC-SHAPE entry point + path rules, per-adapter report/id form, HemaSuite suites for AC-2.8, AC-8.4 census, W4 closed interim entry point + names, matrix table grammar, Stitch route reference file, launch-failure version/rc representation), and the rulings below.
3. Give design-author these as decisions: (a) OPEN-DECISION ruled — under `SET` an undeclared pytest form that `BASE` trusts STAYS trusted; `SET` only adds declared argvs (plan ~line 537 / D15). (b) Stitch route + privacy rules and install status (memory `project_hmad_app_profile_stitch_route.md`). (c) Design-owed nits: AC-4.1's `APP-DOC-SHAPE: NOT_ARMED` token lacks `path=<p>`; spec AC-1.3 should stop quoting "10 files" (the census moves with worktrees, now 11); spec FR-16 S1 row could name the APP-DOC-SHAPE entry point.
4. Design audit: `hmad-dispatch audit-cycle --feature h-mad-app-profile --phase design --cycle 1 --passes 2 --surfaces codex,agy --project-root <root> --gated <root>/docs/02-design/features/h-mad-app-profile.design.md --legs codex --legs agy --project-tests <root>/h-mad/tests --suite-cmd "python3.11 -m pytest <root>/h-mad/tests -q" --timeout 1800`; precheck the design first; first line of no inlined doc may equal a rubric file's first line (J57).
5. Before Phase 5 (not now): confirm `phase5-gate-feature-scope` closed Phase 7 with the archived-path check the plan gives (Convention Prerequisites), then merge `origin/main` into this branch (brings J57 `360f4357`, the brief `0975a796`, `63b33b6a`) and record `BASE`.

## Open / Blocked Items

- **h-mad-app-profile Phase 4** — status: not started (next). repo: `/Users/kimhawk/orca/skills` · branch: `BrightGold70/h-mad-app-profile` · worktree: `/Users/kimhawk/orca/workspaces/skills/h-mad-app-profile`. Claim: `owner_session_id=0f32e68b-45ba-4f53-a92b-86008129d2fc`, heartbeat `2026-11-26T08:58:35Z` (observed), oracle `resume_manual`.
- **Phase 5 ordering vs `phase5-gate-feature-scope`** (carried from the start brief, Next Step 4) — status: agreed in spec/plan: this feature's Phase 5 waits for that feature's Phase 7 (operator OQ9). Unchanged blocker. That lane (main checkout `/Users/kimhawk/orca/skills`) is holding its own 5a "until the h-mad-app-profile lane finishes its current audit round" (its memory note, 11-26 14:15) — our plan audit round ended at `e66f43e4`; its owner may want to know. Not ours to act on.
- **Probe for the plan's own readings** — status: owed by the orchestrator (plan-author cannot write it): suite size, glob censuses, anchor census `1166/87`, invariants files, readlink, pilot clone run, Phase 5 check. Add beside `docs/03-analysis/probes/h-mad-app-profile/spec_measurements.2026-11-26.0f32e68b.py`.
- **Plan cites spec v1.3 (`0df4ae8e`), spec is v1.4** — status: measurement-class staleness; the v1.4 change is one token. Fix in the next plan revision.
- **Stitch skills held** — `extract-static-html`, `code-to-design` (local-file inlining into uploads, Chrome `--no-sandbox`, unpinned installs); build set `react-components`, `react-native` waits for follow-on B. Reviewed source was in the session scratchpad (not durable); upstream `google-labs-code/stitch-skills@75f4696f`.
- **Follow-on features** — B `h-mad-app-runners` (S6–S12), C `h-mad-app-desktop-release` (S13–S14), and the Rust port of h-mad's tooling (rust-anything) — status: deferred, recorded in spec §"Follow-on features" and brainstorm v2.1/v2.2.
- **Memory store dream report** — `dream_lint.py` read `links total=1052 RESOLVED=1039 DANGLING=13`, `orphans=0`, `last_dream=0d ago` (pre-existing dangling links, not from this session). No action from WRITE.
- **Start-brief items closed:** Phase 1 approval (done, brainstorm v2.0 approved, then v2.2); `chore/drop-grok-reviewer` dependency (merged here as `b979eb64`); operator answers in v1.1 (superseded by the Phase 1 restart, v2.0); Phase 2 spec dispatch (done, spec v1.1 → v1.4); takeover stamp (on main in `0975a796`; redundant ref/branch deleted).

## Context for Next Session

**Files touched this session (all on the branch unless noted):**
- `docs/01-plan/features/h-mad-app-profile-brainstorm.md` (v2.2), `.spec.md` (v1.4), `.plan.md` (v1.3)
- `docs/01-plan/features/h-mad-app-profile.plan.audit.v1.p1.md`, `.v1.p2.md`, `.v2.p1.md` (+ `.effort.json`)
- `docs/03-analysis/h-mad-app-profile.plan.delta-review.e4b16e1-20261126T074649Z.md` (+ `.md.txt` prompt)
- `docs/03-analysis/h-mad-app-profile.audit-origins.jsonl`
- `docs/03-analysis/probes/h-mad-app-profile/spec_measurements.2026-11-26.0f32e68b.py`
- main (`360f4357`): `docs/skill-monitoring.md` (J57), `handoff/tests/test_skill_candidates_census.py` (pins 53→54, 4→5)
- outside repo: `~/.claude/skills/{design-md,generate-design,upload-to-stitch,manage-design-system}` (installed; last two hardened); memory notes `project_hmad_app_profile_stitch_route.md`, `project_hmad_rust_port_rust_anything.md`

**Worktree:**
- Worktree root: `/Users/kimhawk/orca/workspaces/skills/h-mad-app-profile` — branch: `BrightGold70/h-mad-app-profile`
- Parent repo: `/Users/kimhawk/orca/skills` — branch: `main` (local 1 behind origin after J57)

**Uncommitted changes:** none in the worktree.

**To resume:**
```bash
cd /Users/kimhawk/orca/workspaces/skills/h-mad-app-profile
git status --short --branch
python3 ~/.claude/skills/h-mad/scripts/h_mad_resume_decision.py --state docs/.bkit-memory.json --feature h-mad-app-profile --session-id <new-id>
python3 -I docs/03-analysis/probes/h-mad-app-profile/spec_measurements.2026-11-26.0f32e68b.py   # expect PROBE-VERDICT: MATCH
```

**Related docs:** `h-mad/references/teammate-authors.md`, `h-mad/references/audit-prompt-assembly.md`, `h-mad/references/inline-protocols.md` §Phase 4; spec §"Follow-on features"; `docs/skill-monitoring.md` J57.
