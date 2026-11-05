# Handoff — gate-non-py-production-files: Phase 5 complete, Phase 6 next

**Date:** 2026-11-05
**Branch:** main
**Project:** skills
**Supersedes:** 2026-11-04-main__backlog-rows-closed-to-one.md
**Next-Session Focus:** Run Phase 6 of H-MAD feature `gate-non-py-production-files` (6a-prime architectural review, then gap analysis), working in its worktree, not in `~/orca/skills`.
**Suggested-Skills:** h-mad (Phase 6 and 7 of the feature), handoff (resume)

## Session Summary

Hawk-MacStudio. The feature went from design v1.0 through both audits and all 8 Phase-5 Tasks. All three gates (Claude, codex, agy) now judge a listed code-like non-`.py` file, and doc/data files stay exempt. Nothing is integrated: the branch is local only, 54 ahead of `origin/main`, HEAD `f3eacfde`.

Final readings at `f3eacfde`: full suite 8583 passed, 0 failed; mutation run over the 10 feature specs `ALL_CAUGHT` 100/100, refused 0; anchors `ANCHORS_OK`; FR-9 9/9 `FR9-DRIVE: PASS`, 33 rows, none mismatched; agy spec review `COMPLIANT` on all 8 Tasks. One commit landed on `main` and was pushed: `e097dfcb`, the plugin-hooks constants test fix.

The operator chose to stop here and run Phase 6 in a fresh session because this one reached 71% context.

## Key Learnings

- **The codex gate trusts its own interpreter's directory, and it runs under Homebrew `python3` 3.15, which has no pytest.** `TRUSTED_BIN_DIRS` includes `Path(sys.executable).resolve().parent`. So `/opt/anaconda3/bin/python3.11 -m pytest` is denied, while `.venv/bin/python -m pytest` is admitted. A probe of that gate must run under the hook's own `python3`: mine ran under `python3.11` and said ALLOW for a command the hook denies.
- **The thin `.venv` at 5c is required in this repo too.** `python3.11 -I -m venv --without-pip --system-site-packages .venv`, then assemble with `--python .venv/bin/python`. I skipped it and lost a RED round.
- **`export PATH="$W/h-mad/bin:$PATH"` makes bare `hmad-dispatch run` resolve to the worktree's wrapper, which the gate does not trust.** Codex must use `/Users/kimhawk/.agents/skills/h-mad/bin/hmad-dispatch run …` or direct `.venv/bin/python -m pytest`. This cost one no-op Task 6 GREEN.
- **Hostile scratch paths have limits.** pytest rejects `[]` in a path, Python's venv builder rejects `:`, and FR-1's grammar excludes whitespace in a listed token. Quotes, `%` and newline are fine. This hit Tasks 3 and 4, and telling the implementer up front stopped it on Tasks 5 and 6.
- **A kind-only test cannot pin a fail-closed guard when the crash path denies the same kind.** `CX-LIST-UNREADABLE` survived: with the guard off, `judge.judge(root, None, …)` raises and `# M:G2` still denies `judge-error`. The test must assert the reason text.
- **A corrective revision past the round cap still found real defects by prototype.** Design v1.4 was not re-audited, and the impl-plan author measured 7 defects in it on a scratch tree. Each is fixed in the plan and named under §"Where this plan departs".
- **agy's design audit fabricated quotes again.** Three of its must-fixes and one should-fix cited text absent from the design (`design.rejections.md`). On impl-plan cycle 1 it filed nothing, and it was accurate as a per-Task spec reviewer. Check quotes against the tree before acting on any agy finding.
- **zsh: `echo === X` fails with `== not found`.** It killed a background script after its suite had finished, so the mutation run never started. The "failed" notification was that typo, not a test.

## Next Steps

1. **Resume in the worktree and claim:**
   ```bash
   cd /Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files
   python3 ~/.claude/skills/h-mad/scripts/h_mad_resume_decision.py --state docs/.bkit-memory.json --feature gate-non-py-production-files --session-id "$CLAUDE_CODE_SESSION_ID"   # read enter_autonomous at this handoff
   python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py docs/.bkit-memory.json --feature gate-non-py-production-files --claim "$CLAUDE_CODE_SESSION_ID"
   ```
2. **Phase 6a-prime, architectural review via agy** (`h-mad/references/agy-architectural-reviewer-prompt.md`, `h-mad/SKILL.md` §"Phase 6 (Verification) sub-steps"). Run it headless with `hmad-dispatch exec agy`. Base is `e097dfcb`, which is also `git merge-base HEAD origin/main`. Require `h_mad_review_evidence` code>0, because the gate counts tools rather than code reads.
3. **Phase 6a gap analysis, then 6b if under 90%** — `docs/03-analysis/gate-non-py-production-files.analysis.v1.md` plus the latest copy.
4. **Bring the closed documents into line before the feature closes**, routed to their authors:
   - Design v1.4: nine refusals, `plan-absent-at-base`, and the three-arm skip test. Verbatim text is in the impl-plan author's v1.1 report, summarised in Open Items below because the scratchpad will not persist.
   - Impl-plan v1.3: 100 mutation rows, not 99, because Task 6 added `H-LIST-CONTEXT`; Task 6 is 26 rows and `claude_gate_listing.json` 13.
5. **Pick up the five H-MAD candidates** in `docs/skill-candidates.md` (rows added this session) as they are picked up.
6. **Phase 7, on the operator's go-ahead only.** Run from the worktree holding `main`, `/Users/kimhawk/orca/skills`, when it is clean: `python3 h-mad/scripts/h_mad_phase7_integrate.py --feature gate-non-py-production-files --base main --route merge --branch BrightGold70/gate-non-py-production-files`. It reads BLOCKED from the feature worktree or without `--branch`. Plan first, then `--apply --suite "python3.11 -m pytest"`. Then stamp row 2856 LANDED.
7. **[suggested] Review or retire draft plan `backlog-row-cycle`** — `docs/01-plan/features/backlog-row-cycle.plan.md`.
8. **[suggested] Review draft plan `hpw-duplicate-copy-retirement`** — `docs/01-plan/features/hpw-duplicate-copy-retirement.plan.md`.

## Open / Blocked Items

**This session:**
- **`gate-non-py-production-files` (row 2856, the sole OPEN row in the census).** Status: Phase 5 complete, Phase 6 not started. `repo: /Users/kimhawk/orca/skills · branch: BrightGold70/gate-non-py-production-files · worktree: /Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files` (Orca selector `47c13b8f-e5c5-4169-8038-1c413c982778::/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files`).
  - **Observed state:** `current_phase=6`, `last_completed_phase=5`, `phase=None`, owner `None`, oracle `enter_autonomous`. The worktree tree is clean. Not pushed.
  - **Documents:** spec v1.13, plan v1.6, design v1.4, impl-plan v1.3, under `docs/01-plan/features/` and `docs/02-design/features/`. Audit reports `*.audit.v{1,2}*`, ledgers `design.rejections.md` and `impl-plan.rejections.md`, delta reviews and `audit-origins.jsonl` under `docs/03-analysis/`.
  - **FR-9 evidence:** `docs/03-analysis/probes/gate-non-py-production-files/fr9/20261105T094753Z-c4cedc6d0d00/`. The driver refuses a replay once base equals HEAD, so any re-run must happen before the Phase 7 push. Before side ran a hook from base `e097dfcb` (sha `c88d29f5`), after side the worktree's (sha `73b0dbc5`).
  - **Keep refs** `backup/gate-non-py-pre-rebase-767be799` and `backup/gate-non-py-pre-rebase-22fd2b2a` while docs cite pre-rebase SHAs. `e4979ecd`, cited by spec AC-9.5, is reachable only through them. Local `.venv` is gitignored and must stay.
- **Design v1.4 owed text (status: not applied; the design phase exited at the cap).** "eight `FR9-DRIVE: UNREADABLE` reasons" and "each of the eight refusals" become nine. Add a fixture bullet after `base-is-head`: `plan-absent-at-base`, `--scenario replay --side after`, a base without the plan path, a later HEAD adding it, `refs/remotes/origin/main` at the base, so `git cat-file blob <base>:<path>` exits 128. The residual becomes: an uncaught exception, such as a missing `git`, exits 1 with no token and reads as no verdict. The skip test becomes three arms: real volume, `os.path.exists` forced True (must return), forced False (must skip). Realpath check precedes the blob check.
- **Accepted deviations (status: recorded, no action unless review objects):** `H-LIST-CONTEXT` adds `target=<path>:` to Claude's code-like denials, matching the other two hosts. Task 3's `root` fixture lost `[H-MAD:MARKER]`, so bracket transport is covered only by `test_listing_cli_listed_prints_the_encoded_target`. `CX-ACTIVE` and `AG-ACTIVE` use `if True:` because `if False:` is equivalent; dropping them gives 98.
- **Prototype readings marked unverified in the impl-plan** (hook timings, launch counts, `H-LIST-LINES`, `H-LIST-INROOT`, `--check-anchors` total): each Task's tests re-read them, and all are now green.

**Closed:**
- Design audit: UNVERIFIED then FAIL must=4, exited at cap with corrective v1.4. Impl-plan audit: FAIL must=4 then must=2, exited at cap with corrective v1.2, plus operator-directed v1.3.
- In-flight design audit PIDs 85325 / 95978 / 95984 from the predecessor: finished; artifacts committed.
- Row 2952: closed in the predecessor with row 2953 (`5db87e97`); my restored todo for it is dropped.
- `verify-hmad-gates` with `HMAD_VERIFY_H_MAD_ROOT`: the predecessor suggested it for FR-9, but the operator's ruling R-B stands and the feature's own driver was used. The driver passed.
- Plugin-hooks constants test: fixed and pushed, `e097dfcb`.

**Carried unchanged:**
- **Hawui-Macmini sync** — unchanged since 2026-11-02 (`git pull`; drop the 2026-11-01 `assemble_tdd` stash; optionally apply config cuts; compare its 9 Macmini-only env failures with `h_mad_failure_diff.py`). `repo: /Users/kimhawk/orca/skills (Hawui-Macmini) · branch: main · worktree: none`.
- **Watch-only triage rows; residuals of the 2026-10-31 stamps and 2026-11-01 landings; Run 8 attempts 1–2** — unchanged since their dates.
- **HemaSuite-owned items** (drafting quality without CLAUDE.md, the judge-sdk branch, unconditional restores) — unchanged; not owned here. `repo: /Users/kimhawk/orca/HemaSuite · branch: main · worktree: none`.
- **Pre-existing untracked files in `~/orca/skills`** (`.codex/config.toml`, three `docs/03-analysis/2026-10-2*.analysis.md`, `hemasuite/docs/research/`) — not mine, untouched.

## Context for Next Session

**Files touched this session:** on the feature branch, `h-mad/hooks/h-mad-tdd-gate.sh`, `h-mad-codex-tdd-gate.py`, `h-mad-agy-tdd-gate.py`; `h-mad/scripts/h_mad_wire_pin_gate.py`, `h_mad_target_identity.py`, `h_mad_tdd_judge.py`; `h-mad/references/{codex-implementer-prompt,codex-runtime,phase5-substeps,helper-scripts}.md`; new and modified tests and mutation specs under `h-mad/tests/`; `docs/03-analysis/probes/gate-non-py-production-files/fr9_drive.py` and evidence; the phase documents above. On `main`: `h-mad/tests/test_h_mad_check_plugin_hooks.py`, `docs/skill-candidates.md`, `docs/learnings.md`.

**Worktree:**
- Worktree root: `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files` — branch: `BrightGold70/gate-non-py-production-files`
- Parent repo: `/Users/kimhawk/orca/skills` — branch: `main`, shared with other lanes; check it right before any write.

**Uncommitted changes:** worktree none; `~/orca/skills` has only the pre-existing untracked files above.

**To resume:**
```bash
cd /Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files
git status --short --branch
git rev-list --left-right --count origin/main...HEAD   # 0 54 at handoff
.venv/bin/python -c 'import pytest; print(pytest.__version__)'
```

**Related docs:**
- `docs/02-design/features/gate-non-py-production-files.design.md`; `docs/01-plan/features/gate-non-py-production-files.impl-plan.md` §"Where this plan departs"
- `docs/03-analysis/gate-non-py-production-files.impl-plan.delta-review.corrective-93e33e3e.md`
