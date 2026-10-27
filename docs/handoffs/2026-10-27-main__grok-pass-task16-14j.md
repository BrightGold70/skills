# Handoff — grok-audit-surface scored PASS; Task 16 and Task 14j merged; backlog decisions recorded

**Date:** 2026-10-27
**Branch:** main
**Project:** skills
**Supersedes:** 2026-10-25-main__fixes-merged-back-to-studio.md

## Session Summary

On the Mac Studio, Task 15 step 11 finished. 9 fresh blind AI labellers labelled 130 findings, and
`check_labels` accepted all 130 first time. The score commit is `05cc3935` on
`calibration/grok-audit-surface`, pushed. `rescore` from `main` read **`SEEDSCORE: PASS`**:

| surface | recall | fabrication |
|---|---|---|
| grok | 12/27 | 0/38 |
| agy | 10/27 | 0/23 |
| codex | 6/27 | 0/25 |

The operator chose to publish PASS as measured. Three branches were merged and pushed, each after a
review, all fixes closed, and a green full suite:

- **Task 16** (S3 publish, the measurement doc) as `2614364b`.
- **Task 14j** (`scan_log` normalizes every comparison base; it supersedes the parked `60635019`) as
  `c0300c1c`.
- **Backlog rows 27 and 29** as `b25a2302`.

Also done this session:

- The operator decided triage rows 16, 19, 28 and 47.
- Row 17's scope was drafted and is waiting for approval.
- bkit is updated to 2.1.40 here, with the G-001 patch applied.
- A new G-004 precision patch stops bkit asking before routine push, merge or pull on main.

`main` is at `12fbe9c3`, in sync with origin.

## Key Learnings

- **All 130 labels came back HIT or REAL.** There was no FABRICATED and no UNDECIDABLE, against 6
  fabrications in 37 must-fixes in the prior measurement. The PASS rests on the equal-fabrication
  clause (0/38 = 0/23) with recall 12 > 10, so it holds by one label:
  - one grok must-fix relabelled FABRICATED would give MISS;
  - two grok HITs relabelled REAL would give MISS;
  - one grok must-fix relabelled UNDECIDABLE would give INCONCLUSIVE (`undecidable_flips`).

  The labels are committed add-only and cannot be amended. The measurement doc's Residuals record
  all of this.
- **A suite running beside the mutation harness measures nothing.** It stops at `SUITE: BUSY …`
  because the two share `.h-mad/mutation.lock`. The background task still reported exit 0, but that
  was the trailing `tail`'s code, not pytest's. Run them one after the other, and read the summary
  line, never `$?`.
- **Another session commits to `main` in this same checkout.** `ca10f69b` and `951c99f2` landed
  mid-session. Fetch before every merge or push. Branch suites ran on the old base; after merging,
  only targeted tests were re-run.
- **A subagent that hits its session limit takes its background runs with it.** That is how the
  Task 14j fixer died. Its commit survived, but its gates had to be re-run.
- **bkit's PreToolUse detector reads trigger strings inside a command, even test literals.**
  A `--force` literal in a smoke test blocked the whole Bash call. Put trigger strings in a script
  file, as `verify.js` does by building them at runtime.
- **bkit's `detect` signature is `detect(toolName, toolInput)`.** Calling `detect(cmd)` returns
  "clean" for everything, which is the silent false pass the first `verify.js` draft hit.
- **bkit asks are not suppressed in `auto` permission mode** (`ASK_SUPPRESSING_MODES` = acceptEdits,
  dontAsk, bypassPermissions), and bkit has no rule off-switch, by design. The only relief is rule
  precision.

## Next Steps

1. **Approve row 17's scope**: `docs/superpowers/specs/2026-10-27-hmad-test-boundaries-design.md`.
   Two calls are still mine: the table goes in the design, and old features are exempt. On approval,
   write the plan (`superpowers:writing-plans`), then run it as a full h-mad feature.
2. **`grok-audit-surface` Task 17**, the S4 route (PASS only), at
   `docs/01-plan/features/grok-audit-surface.impl-plan.md` §"Task 17". Then 5e/5f/5g, Phase 6 and
   Phase 7. Claim the feature first:
   `python3 ~/.claude/skills/h-mad/scripts/h_mad_resume_decision.py --state docs/.bkit-memory.json --feature grok-audit-surface --session-id <id>`
   (it was released at this closeout).
3. **Row 28 split** (operator decision). Move the two real-cycle test ids out of the path-scope test
   module so the TDD judge's 40 s budget holds under load. See
   `docs/03-analysis/grok-audit-surface.task14d-gate-2026-10-23.md`.
4. **Row 18**: brainstorm the scope (handoff redaction, a next-session focus field, scout remedy
   classes), then run it as an h-mad feature. It may split into three smaller features.
5. **Remaining actionable triage rows**: 33, 35, 38, 39, 44, 46. They are listed in
   `docs/03-analysis/2026-10-25-backlog-triage.md`.

## Open / Blocked Items

**This session:**

- **Row 17 scope:** drafted and committed as `2c43cd1c`, with the operator's decisions on
  enforcement (Phase 4 audit gate), coverage (non-test rows allowed) and calibration (fixture
  tables). Status: awaiting the operator's approval of the doc.
- **The bkit G-004 precision patch** (`docs/patches/bkit-g004-protected-branch-precision/`) is
  applied to 2.1.38 and 2.1.40 on the **Mac Studio only**:
  - `verify.js` reads 16/16.
  - 3 vendor tests fail as expected: DT-004, GP-19 and bash-pre `MUST_ASK git merge main`.
  - A bkit update drops it; re-run `verify.js`.
  - Hawui-Macmini needs it applied too.

  Status: watch.
- **The G-001 patch** is now applied on the Mac Studio as well (`9e5b39d0`). Upstream issue
  `ww-w-ai/bkit-claude-code#161`. Status: watch, unchanged.
- **New `skill-candidates` rows:** 7 rows from triage row 27 (#3, #7, #8, #11, judge-mapping, F1,
  F2+F3). The census now reads OPEN 31. Status: open backlog.

**Carried from `2026-10-25-main__fixes-merged-back-to-studio.md`:**

- **Task 15 step 11:** closed. Score sha `05cc3935`, `SEEDSCORE: PASS`. Step outputs are in
  `$RUN/work/` (`labeller-*`, `rescore.txt`, `mainleak.txt`).
- **Task 16 measurement doc:** closed, merged in `2614364b`. It records the labeller-package
  deviation (row 2).
- **The parked 14h fix** (`park/grok-14h-home-rstrip`): closed. It was superseded by Task 14j
  (`c0300c1c`), and the branch is deleted. Row 15 was reviewed and left as designed.
- **Operator decisions on rows 16, 19, 28, 47:** closed in `190939a8`.
  - 16: dropped.
  - 19: kept deferred.
  - 28: split, which is Next Step 3.
  - 47: dropped.
- **`origin/feature/218-grok-audit-surface`:** closed. It was deleted, along with the local branches
  `feature/218-grok-audit-surface` and `feature/218b-grok-containment`.
- **Worktree `../skills-gate-authoring`:** closed. It was removed, and `fix/gate-task-authors-test`
  was deleted.
- **bkit on the Mac Studio:** closed. It is on 2.1.40 with the G-001 patch applied.
- **The h-mad claim on `grok-audit-surface`:** released at this closeout by session `34a538a0`.
  Re-claim before Task 17.
- **HemaSuite `document-intake-source-review::Task 6`** needs `**WIRE-RUNNER**: playwright` and
  `runner: playwright`. Status: owed by HemaSuite, unchanged.
- **Wire-registry `missing=268`** (task #2): blocked on a HemaSuite checkout, unchanged.
- **The codex pin `term_134b0865…` is stale.** Re-pin before any codex dispatch. Unchanged.
  - The Task 14j executor routed one production edit through Codex anyway; the verifying pass
    confirmed the diff.
- **Run 8 attempts 1-2** are evidence only; never score them. Unchanged.
- **Rows formerly blocked on the other Mac:**
  - Row 2: closed by Task 16.
  - Rows 23 (local-only `verify-hmad-*` skills) and 34 (~179 leaked `hmad_exec_prompt.*` temp
    files): this *is* the run Mac, but neither was looked at this session. Status: unverified,
    actionable here.
  - Row 24 (F1-F4): F1-F3 were filed by row 27, and F4 does not reproduce. Closed.
  - Row 26 (Tasks 16-17, 5f/5g, Phases 6-7): Task 16 is done; the rest is Next Step 2.
- **Rows blocked on HemaSuite** (41, 49, 50, 52): unchanged.
- **Watch-only rows:** unchanged, as listed in the triage doc.

## Context for Next Session

**Merged and pushed this session (`main`):**

| commit | change |
|---|---|
| `2614364b` | merge of Task 16, the S3 publish (measurement doc, SKILL.md routing sites, grok-runtime.md, K2/K6/K7) |
| `9e5b39d0` | G-001 patch record for the Mac Studio |
| `c0300c1c` | merge of Task 14j (`scan_log` `_base()` normalization, spec AC-6.6, design D19, mutation rows) |
| `190939a8` | triage decisions on rows 16/19/28/47; rows 2 and 14 closed |
| `b25a2302` | merge of rows 27/29 (skill-candidates filings; 14c `status_dir` note) |
| `2c43cd1c` | row 17 scope doc |
| `12fbe9c3` | bkit G-004 precision patch record |

Calibration branch: `05cc3935` (score commit).

**Gates on the merged branches:**

- Task 16: suite 7431 passed; mutation 434/434.
- Task 14j: suite 7457 passed; mutation 445/445, `untargeted=0/445`.

**Files touched (main areas):**

- `docs/03-analysis/grok-audit-surface.measurement.md` (new)
- `h-mad/SKILL.md`, `h-mad/references/grok-runtime.md`, `h-mad/scripts/h_mad_tool_calls.py`
- `h-mad/tests/test_grok_audit_surface_{docs,containment,toolscan_pattern}.py`,
  `h-mad/tests/mutation-specs/grok_audit_surface.json`
- `docs/01-plan/features/grok-audit-surface.{impl-plan,spec}.md`,
  `docs/02-design/features/grok-audit-surface.design.md`
- `docs/skill-candidates.md`, `docs/03-analysis/2026-10-25-backlog-triage.md`
- `docs/patches/bkit-g00{1,4}-*/`, `docs/superpowers/specs/2026-10-27-hmad-test-boundaries-design.md`
- Outside the repo: the bkit cache at `~/.claude/plugins/cache/bkit-marketplace/bkit/{2.1.38,2.1.40}`.

**Worktree:** only `/Users/kimhawk/orca/skills` on `main`.

**Uncommitted changes:** six untracked items predate this session and are not this session's work.
They are `.codex/config.toml`, three 10-22/10-23 analysis docs, `hemasuite/docs/research/` and
`kimhawk@Hawui-Macmini.local/`.

**To resume (Mac Studio):**
```bash
cd /Users/kimhawk/orca/skills && git pull --ff-only
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
node docs/patches/bkit-g004-protected-branch-precision/verify.js   # expect RESULT: OK
python3 ~/.claude/skills/h-mad/scripts/h_mad_resume_decision.py --state docs/.bkit-memory.json --feature grok-audit-surface --session-id <id>
```

**Related docs:**

- `docs/03-analysis/grok-audit-surface.measurement.md`: the published S3 result and its residuals.
- `docs/03-analysis/2026-10-25-backlog-triage.md`: the backlog, with the 2026-10-26/27 outcome
  sections.
- `docs/superpowers/specs/2026-10-27-hmad-test-boundaries-design.md`: the row 17 scope.
- `docs/patches/bkit-g004-protected-branch-precision/README.md` and
  `docs/patches/bkit-g001-bare-heredoc-substitution/README.md`.
- Predecessor: `docs/handoffs/2026-10-25-main__fixes-merged-back-to-studio.md`.
