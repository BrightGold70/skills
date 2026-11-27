# Handoff — h-mad-app-profile: design v1.0 approved (now v1.2); design audit paused on phase5-gate

**Date:** 2026-11-27
**Branch:** BrightGold70/h-mad-app-profile
**Project:** skills
**Supersedes:** 2026-11-26-BrightGold70-h-mad-app-profile__phase3-exit-design-next.md
**Next-Session Focus:** Check whether phase5-gate's Codex gate fix has landed on `origin/main`. If it has, re-claim and run design audit cycle 1. If not, stop.
**Suggested-Skills:** handoff (READ first), h-mad (the feature; Phase 4 audit)

## Session Summary

Phase 4 design authored and **approved by the operator (v1.0, `57787ff8`)**, then revised twice:
- v1.1 (`856c32a5`): cleanups after spec v1.5.
- v1.2 (`907deb69`): pilot run pinned to `94e3318e`, per the lane supervisor.

Owed items went to the other documents:
- spec v1.5 (`0260e2ad`);
- plan v1.4 (`0bf4dd8b`), a corrective revision that was not re-audited.

The design-measurements probe is committed (`b0377296`), and both foreign-repo legs are now pinned to fixed commits (`e45b56bc`, `da09ff1c`). All three legs read MATCH with 0 drift.

**The design audit was NOT run.** The operator ruled "author, then pause": phase5-gate has armed its repo-wide Codex TDD gate, and Codex audit legs may be refused until its fix lands (`msg_3efdda92a391`). The fix had not landed at close: `origin/main` was still at `992b7166`.

The claim is **released** (observed `owner_session_id=None`; the oracle reads `resume_manual`). Recorded phase: `last_completed_phase=3`, `current_phase=4`.

## Key Learnings

- **A `LIVENESS: LIVE` reading can be your own process.** Orca launched this terminal as `claude --resume 0f32e68b…`, and `/clear` then minted a new session id (`7fb5bc3e`). So the liveness `ps` clock matched our own process, and the owner's transcript was last touched at the `/clear` instant. Walk your own process ancestry (`ps -o pid,ppid,command -p $$` upward) before acting on that reading. Then take the claim with `--release --session-id <old-id>` followed by a plain `--claim`, not `--force`. I used `--force`; memory `feedback_idle_session_is_not_a_dead_session.md` names the honest route.
- **`git ls-tree` pathspecs are literal prefixes, not globs.** `git ls-tree -r --name-only REF -- 'dir/test-*.cjs'` lists 0 files. List the tree and filter with `fnmatch`. Treat an empty listing as UNREADABLE, never as a drift of (0,0,0). This was my bug; the design-author caught it independently.
- **Pin every probe reading over a foreign repo to a fixed commit.** Both Hematology_wiki (94e3318e → c8ea3eb7 → b077f7cd within hours) and HemaSuite (6546f517 → 0fcf1459) moved during the session through docs-only commits. Each move showed up as a probe drift, although the measured readings were unchanged. Read the tree at the ref (`git show REF:path`, `git grep … REF`, `git checkout --detach REF` in a throwaway clone), and print the live HEAD as information only.
- **The spec-author deliberately kept one dated reading in AC-1.3's measurement bullet** ("11 files at 57787ff8"). Its reason: a "none of them" claim needs a denominator and a stamp. The operator was told; reverting it means deleting one sentence.
- **The design's connection rows are now R1–R17,** so they cannot be confused with the spec's slice ids S1–S14. The design also has a "Revert" row kind, which could read like an R prefix; a §4 sentence disambiguates. K, Q, N, T, X and V are free if the operator prefers another prefix.

## Next Steps

1. Check whether the gate fix landed. Run `git -C /Users/kimhawk/orca/workspaces/skills/h-mad-app-profile fetch -q origin && git log --oneline -5 origin/main`. Also check `git -C /Users/kimhawk/orca/workspaces/skills/phase5-gate-feature-scope log --oneline -5`, which was at `6f2b5373` (5b wire pins) at close. If nothing landed, stop and report.
2. If it landed, re-claim: `python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py docs/.bkit-memory.json --feature h-mad-app-profile --claim <sid>`. The claim is released, so no `--force` is needed.
3. Precheck the design: `python3 ~/.claude/skills/h-mad/scripts/h_mad_precheck_doc.py docs/02-design/features/h-mad-app-profile.design.md --phase design --root <root>`. Then run design audit cycle 1: `hmad-dispatch audit-cycle --feature h-mad-app-profile --phase design --cycle 1 --passes 2 --surfaces codex,agy --project-root <root> --gated <root>/docs/02-design/features/h-mad-app-profile.design.md --legs codex --legs agy --project-tests <root>/h-mad/tests --suite-cmd "python3.11 -m pytest <root>/h-mad/tests -q" --timeout 1800`.
   - Read `h-mad/references/audit-prompt-assembly.md` and `h-mad/references/phase5-substeps.md` (the opening part, plus "Dispatch channels") first.
   - J57: no inlined document may start with a rubric file's first line.
   - Do not write any file into the tree while the suite runs.
   - If Codex is refused, set `codex_status`, use doc-auditor (GATING) plus agy, and report the refusal to the operator (per the operator's ruling).
4. Answer the audit through `design-author` (2-round cap). Back-propagate to spec-author or plan-author only for findings with no AC in those documents.
5. Before Phase 5 (not now): confirm `phase5-gate-feature-scope` has closed its Phase 7, then merge `origin/main` into this branch and record `BASE`.

## Open / Blocked Items

- **h-mad-app-profile Phase 4 design audit** — status: blocked. It waits for phase5-gate's Codex gate fix (operator 2026-11-27: "author, then pause"). Design v1.2 at `907deb69`; v1.0 is the approved version. repo: `/Users/kimhawk/orca/skills` · branch: `BrightGold70/h-mad-app-profile` · worktree: `/Users/kimhawk/orca/workspaces/skills/h-mad-app-profile`. Claim released (observed `owner_session_id=None`, oracle `resume_manual`).
- **Phase 5 ordering vs `phase5-gate-feature-scope`** (carried from 11-26) — status: unchanged blocker. This feature's Phase 5 waits for that feature's Phase 7 (OQ9). That lane is at 5b: `6f2b5373` in `/Users/kimhawk/orca/workspaces/skills/phase5-gate-feature-scope`. Not ours to act on.
- **Probe for the plan's own readings** (carried from 11-26) — status: partly covered. The design probe `docs/03-analysis/probes/h-mad-app-profile/design_measurements.2026-11-27.7fb5bc3e.py` now covers:
  - the anchor census, which plan v1.4 points to;
  - the pilot run and pilot names (pinned to 94e3318e);
  - the scanner censuses.

  Still owed as plan-specific probe ids:
  - suite size;
  - the invariants files (the spec probe covers the spec's reading);
  - readlink;
  - the Phase 5 check.

  Add them beside the existing probes if the audit asks.
- **Design-audit measurement note** — status: open. `design.hemasuite.hpw_four` is always SKIPPED, because no command pins "four of the seven" HPW lines. An auditor may file this as measurement-class.
- **AC-1.3 dated reading** — status: operator informed; it stays unless the operator asks to delete it (spec v1.5).
- **Stitch skills held** (carried) — status: unchanged since 11-26. `extract-static-html` and `code-to-design` are held; `react-components` and `react-native` wait for follow-on B.
- **Follow-on features** (carried) — status: deferred, unchanged. B `h-mad-app-runners` (now also owns the `h_mad_assemble_tdd.py` "-m pytest" run-line residual, per spec v1.5), C `h-mad-app-desktop-release`, and the Rust port.
- **Memory store** (carried) — status: unchanged. dream_lint at session start: `links total=1052 RESOLVED=1039 DANGLING=13`, `orphans=0`, `last_dream=1d ago`.
- **Closed this session** (from the 11-26 doc):
  - Next Step 1, claim: taken from `0f32e68b`, a pre-`/clear` id of this same process; now released.
  - Next Step 2, design-author dispatch: design v1.0 to v1.2.
  - Next Step 3, decisions relayed: (a) ruling in design §12; (b) Stitch route in §18; (c) nits fixed in spec v1.5.
  - "Plan cites spec v1.3": fixed in plan v1.4 `0bf4dd8b`.

## Context for Next Session

**Files touched this session (all committed on the branch):**
- `docs/02-design/features/h-mad-app-profile.design.md` (v1.0 → v1.2)
- `docs/01-plan/features/h-mad-app-profile.spec.md` (v1.5), `docs/01-plan/features/h-mad-app-profile.plan.md` (v1.4)
- `docs/03-analysis/h-mad-app-profile.{design.author-report.v1.0,v1.1,v1.2,spec.author-report.v1.5,plan.author-report.v1.4}.md`
- `docs/03-analysis/probes/h-mad-app-profile/design_measurements.2026-11-27.7fb5bc3e.py`
- `docs/.bkit-memory.json` (claim taken, beaten, released)

**Worktree:**
- Worktree root: `/Users/kimhawk/orca/workspaces/skills/h-mad-app-profile` — branch: `BrightGold70/h-mad-app-profile` (no upstream; nothing pushed)
- Parent repo: `/Users/kimhawk/orca/skills` — branch: `main` (in sync with origin at session start)

**Uncommitted changes:** none.

**To resume:**
```bash
cd /Users/kimhawk/orca/workspaces/skills/h-mad-app-profile
git status --short --branch
git fetch -q origin && git log --oneline -5 origin/main      # gate fix landed?
python3 ~/.claude/skills/h-mad/scripts/h_mad_resume_decision.py --state docs/.bkit-memory.json --feature h-mad-app-profile --session-id <new-id>
python3 -I docs/03-analysis/probes/h-mad-app-profile/design_measurements.2026-11-27.7fb5bc3e.py   # expect PROBE-VERDICT: MATCH
```

**Related docs:**
- Design §12 (admission corpus and ruling), §18 (Stitch route), §21 (censuses), §23 (pilot, P1 reference commit).
- `h-mad/references/audit-prompt-assembly.md`.
- Orchestration messages received this session: `msg_3efdda92a391` (gate armed), `msg_d4d9f8702851` (pin pilot), `msg_0e018ff2da3d` (run --hemasuite).
