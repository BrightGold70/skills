# Handoff — five branches merged on Hawui-Macmini; back to the Mac Studio for Task 15 step 11

**Date:** 2026-10-25
**Branch:** main
**Project:** skills
**Supersedes:** 2026-10-25-main__step11-extract-done-blind-labels.md

## Session Summary

This session ran on **Hawui-Macmini**, which does not have the Task 15 run state, so step 11 could
not continue here. Copying the state over failed: rsync from the original Mac did not connect.
Instead the session closed independent backlog:

- the skill-candidates reconcile (26 `yes` rows re-probed);
- the bkit G-001 heredoc item (fixed upstream; a new false negative was patched locally and filed
  upstream);
- task #7, the WIRE-PIN `runner` field, implemented and merged;
- eight skill-candidates rows plus one triage row (the harness SyntaxWarning).

Every merge passed independent review, with every must-fix closed, and a full suite with 0 new
failures against `main`'s environmental baseline. `main` is `da1584c7`, pushed. A full triage of
the carried backlog (52 items) is in `docs/03-analysis/2026-10-25-backlog-triage.md`. **Next:
resume step 11 on the Mac Studio.**

## Key Learnings

- **This Mac's `docs/.bkit-memory.json` is a stale copy** (last written 2026-10-18; it shows
  `grok-audit-surface` at phase 3). The state file is untracked and stays on each machine, so a
  resume check here answers against week-old state. On the Mac Studio, trust that machine's file;
  never copy this one over it.
- **A skill body must not contain positional shell tokens.** awk's `$1`/`$2` inside the SKILL.md
  §5e block failed `test_no_renderer_substituted_token_survives`. The slash-command renderer
  rewrites them. Use `while read -r a b` instead.
- **Claim-liveness design (operator decision):** `--claim`, `--release` and the resume oracle now
  share `owner_proven_live`, which reads only the **owner's own transcript**. `ps` was dropped
  because it can be the claimant's own shell. The lane commit clock was dropped because it can be
  anyone's. Codex and agy owners (minted ids) stay heartbeat-only.
- **The harness now takes `--python <interp>` and `--only <row>`.** On this Mac, run specs with
  `--python /opt/homebrew/bin/python3.14`; temporary spec copies are no longer needed.
  `--only` narrows the rows only; the baseline still runs the spec's full command.
- **A review round is worth it here.** All four review passes found real must-fixes, including a
  dodge in the wire registry, writer/oracle disagreement, and a stale-stash race. Each was
  reproduced before it was fixed.
- **`test_heartbeat_elapsed_values_are_monotonic` is load-flaky.** It failed once under two
  concurrent full suites and passed alone (56/56). The dispatch code was untouched.

## Next Steps

1. **On the Mac Studio, Task 15 step 11.** First `git pull` (to `66e22a08` or later), then follow
   `2026-10-25-main__step11-extract-done-blind-labels.md` Next Steps 1-7 unchanged: rebuild the
   label package, lock `$RUN`, dispatch the 9 blind labellers, merge, check the labels, restore,
   then the score commit. **Ask the operator before the push.** The run state is
   `~/.local/state/h-mad/grok-audit-surface/` on that machine.
2. **Then Task 16** (measurement doc). It must record the labeller-package deviation (design rows
   122-123; triage row 2).
3. **After step 11, fold in the parked 14h fix:** branch `park/grok-14h-home-rstrip`
   (`60635019`, pushed). Make it a `grok-audit-surface` task. The security review asks that every
   comparison base in `scan_log` be normalized (`needle_dirs`, `root`, `checkout`), not just
   `home`. Row 15 (unquoted canary prompt paths) is deliberate per the impl-plan at `:2787`;
   revisit it inside the feature.
4. **Decisions waiting on the operator (triage NEEDS-DECISION):**
   - row 16: Policy B;
   - row 19: progressive disclosure;
   - row 28: the 14d AC.5 module split;
   - row 47: the agy live smoke.

   Rows 9 and 53 were closed on 2026-10-26 (`66e22a08`). `origin/fix/gate-task-authors-test` and
   five other remote branches already merged into main were deleted, and the untracked
   delta-review stub was deleted.
5. **After step 11, delete `origin/feature/218-grok-audit-surface`.** Its tip is already in `main`,
   but it was kept because it is the Task 15 branch on the Mac Studio.

## Open / Blocked Items

**This session:**

- **`fix/*` worktrees and branches:** all four (`fix/independent-bugs`, `fix/batch-2`,
  `fix/batch-3`, `feat/wire-pin-runner`) were merged, then their worktrees and local branches
  deleted. Status: done.
- **`park/grok-14h-home-rstrip`:** parked, unmerged, pushed. repo: `/Users/kimhawk/orca/skills` ·
  branch: `park/grok-14h-home-rstrip` · worktree: none. Status: deferred to `grok-audit-surface`
  after step 11.
- **Upstream bkit issue `ww-w-ai/bkit-claude-code#161`** (bare-tag heredoc false negative). The
  local patch is applied on Hawui-Macmini bkit 2.1.40 only. **The Mac Studio is on bkit 2.1.38:**
  update bkit there, then apply `docs/patches/bkit-g001-bare-heredoc-substitution/` per its
  README. Status: watch.
- **HemaSuite `document-intake-source-review::Task 6`:** needs `**WIRE-RUNNER**: playwright`, and
  its record needs `runner: playwright` added. That happens in HemaSuite, now that `runner` exists
  on `main`. Status: owed by HemaSuite.

**Carried from `2026-10-25-main__step11-extract-done-blind-labels.md`** (per-item status with
evidence in `docs/03-analysis/2026-10-25-backlog-triage.md`):

- **Task 15 step 11:** in progress, blocked on the Mac Studio. Unchanged. `extract` is done (seed
  `773509911`, 130 findings). The run dir `run-ab2c85dc2e25-20261024T132452Z` is on the Mac Studio.
- **The labeller-package procedure deviation** for Task 16's measurement doc: unchanged.
- **h-mad claim on `grok-audit-surface`:** released at the previous closeout. Unchanged. Check it
  on the Mac Studio with `h_mad_resume_decision.py`. This Mac's copy is stale; don't use it.
- **Wire-registry `missing=268`** (task #2): open, blocked on a HemaSuite checkout. Unchanged.
- **Playwright WIRE-PIN:** closed. Decided in `8118f6fc`, implemented and merged in `94cf6d7b`.
- **bkit G-001 local patch:** closed in `c0c73e51`, and issue #161 was filed (see above).
- **Skill-candidates reconcile:** closed in `4e4a3b04`. This session also closed 8 rows; the
  census reads OPEN 24.
- **Worktree `../skills-gate-authoring`:** closed (gone). The remote branch was deleted on 2026-10-26
  (row 9).
- **Codex pin `term_134b0865…` is stale:** unchanged. Re-pin before any codex dispatch.
- **Run 8 attempts 1-2 are evidence; never score them:** unchanged.
- **Everything carried from `2026-10-24-main__task15-runs4-7-14h-green.md`:** unchanged. Each
  item is classified, with evidence, in the triage doc. Actionable rows not reached this session:
  17, 18, 27, 29, 33, 35, 38, 39, 44, 46. Blocked on the other Mac: 2, 23, 24, 26, 34. Blocked on
  HemaSuite: 41, 49, 50, 52. Watch-only: as listed there.

## Context for Next Session

**Merged and pushed this session (`main`):**

| commit | change |
|---|---|
| `4e4a3b04` | skill-candidates reconcile |
| `c0c73e51` | bkit G-001 patch record |
| `8118f6fc` | runner decision |
| `a9c6c692` | merge `fix/independent-bugs` |
| `94cf6d7b` | merge `feat/wire-pin-runner` |
| `039837bd` | merge `fix/batch-2` |
| `da1584c7` | merge `fix/batch-3` |

**Files touched (main areas):**
- `h-mad/scripts/`: `h_mad_wire_registry.py`, `h_mad_wire_pin_gate.py`,
  `h_mad_mutation_harness.py`, `h_mad_extract_verdict.py`, `h_mad_audit_gate.py`,
  `h_mad_audit_cycle.py`, `h_mad_state_write.py`, `h_mad_state_ownership.py`,
  `h_mad_resume_decision.py`, `h_mad_assemble_tdd.py`
- `h-mad/SKILL.md`; `h-mad/references/` (`inline-protocols.md` and both Codex prompts);
  `handoff/SKILL.md`; `docs/skill-candidates.md`
- `docs/patches/bkit-g001-bare-heredoc-substitution/`; `docs/03-analysis/` (the decision and the
  triage doc)

**Worktree:** only `/Users/kimhawk/orca/skills` on `main` remains.

**Uncommitted changes:** none. The working tree is clean; the foreign delta-review stub was deleted on 2026-10-26.

**To resume (Mac Studio):**
```bash
cd /Users/kimhawk/orca/skills && git pull --ff-only            # -> 66e22a08 or later
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
python3 ~/.claude/skills/h-mad/scripts/h_mad_resume_decision.py --state docs/.bkit-memory.json --feature grok-audit-surface --session-id <id>
source ~/.local/state/h-mad/grok-audit-surface/run-current.env && ls "$READING"   # extract.txt findings.jsonl key.jsonl, no labels.jsonl
```

**Related docs:**
- `docs/03-analysis/2026-10-25-backlog-triage.md`: the full carried backlog, with classes and this session's outcome
- `docs/03-analysis/wire-registry.decision-2026-10-25-runner-field.md`
- `docs/patches/bkit-g001-bare-heredoc-substitution/README.md`
- Predecessor: `docs/handoffs/2026-10-25-main__step11-extract-done-blind-labels.md`
