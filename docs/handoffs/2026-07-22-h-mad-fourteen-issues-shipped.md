# Handoff — h-mad: 14 issues filed and shipped, plus a state write path

**Date:** 2026-07-22
**Branch:** `main` (skills, clean, in sync with origin)
**Project:** BrightGold70/skills (h-mad skill) — with knock-on work in BrightGold70/HemaSuite

## Session Summary

Started as housekeeping (consolidate the auto-memory store, add a SessionStart hook) and turned
into a full reliability pass on the h-mad skill. Filed 14 issues in two waves and closed all 14:
wave 1 (#1–#7) fixed dispatch-layer defects found by driving the skill end-to-end; wave 2 (#8–#14)
fixed protocol-layer gaps found by watching the workflow actually fail on a live feature. Test suite
went 64 → 332. Along the way ran the Phase 6a gap analysis that a live feature had skipped, measured
it at 0%, **published a materially wrong conclusion and had to correct it**, then amended that
feature's design and spec from the corrected finding. Everything on `skills` is merged and pushed;
`skills` main is clean and in sync.

## Key Learnings

- **A green test suite certified a 0% match rate.** 7372 tests passing said nothing about spec
  conformance, because the tests encoded the *design* and the design had silently diverged from the
  *spec* in three places. Test-passing and requirement-satisfying are independent axes.
- **I published a wrong analysis with confident, actionable instructions.** The FR verifiers were
  briefed to distrust the design and check code against spec — right for anchor drift, wrong here.
  Three ACs they reported as implementation defects were deliberate design narrowings with recorded
  rationale, one reached only after 68 test regressions across 6 files. My instruction to "delete or
  invert" those tests would have repeated abandoned work. **Verifying against one document cannot
  distinguish "code diverged from design" from "design diverged from spec".** Fixed as #11.
- **Halt conditions phrased as halt-on-bad-value fail open.** "Halt on `VERDICT: DRIFT`" means a
  scrape with *no verdict at all* greps clean — so agent silence read as approval and committed the
  module. Extraction must fail closed; readiness probes cannot help, because an idle pane with no
  output is genuinely idle.
- **Two wrong ways to count commits, and the second looked right.** `rev-list --count <branch>`
  returned 2404 for an 18-commit feature (whole reachable history). `merge-base..<branch>` fixed
  that and returned 0 once the branch merged — blind exactly where the real incident was. Only
  grepping the log for commits naming the feature survives a merge.
- **I invented a state key in the same change that documents "never invent a key."** Writing
  `archreview` would have failed `--strict-only` because the schema is `additionalProperties: false`.
  Caught by checking the schema before committing. This is why the write path now validates.
- **zsh ate two commands silently this session.** `git merge -m "…#1-#7"` executed the backticks in
  the message and glob-failed on `#`; leading-dash paths broke `basename`/`cmp`. Both produced
  *no-ops that looked like success* — caught only by verifying state afterwards, not by reading exit
  codes. `git merge -F <file>` works; `-F -` does not (unlike `git commit`).
- **Sentinel echo trap:** a sentinel written literally into a dispatch prompt is echoed in the pane,
  so the orchestrator's grep matches its own instruction rather than the agent's report. Split it
  across string fragments.

## Next Steps

1. **Re-run Phase 6a on `review-pipeline-correctness` once the other session's work settles** — the
   0% measurement predates `CorrectnessHalt` and the registry repairs. Command:
   `python3 ~/.claude/skills/h-mad/scripts/h_mad_phase7_preconditions.py docs/.bkit-memory.json --feature review-pipeline-correctness`
   from `orca/HemaSuite/hematology-paper-writer` — currently BLOCKED on both counts.
2. **Fix the stale phase counter in HemaSuite state** — `last_completed_phase` is 4 while 23 commits
   reference the feature. The staleness checker flags it today:
   `python3 ~/.claude/skills/h-mad/scripts/h_mad_state_staleness.py docs/.bkit-memory.json --feature review-pipeline-correctness`
   Correct it with `h_mad_state_write.py`, do not hand-edit.
3. **Push HemaSuite's `8eb44ed1`** (CorrectnessHalt) — 1 commit ahead of origin, plus 7 dirty files
   from the concurrent session. Coordinate before pushing; that work is not mine.
4. **[suggested] Adopt the new gates in an actual run.** Nothing has yet exercised
   `h_mad_phase7_preconditions.py`, `h_mad_state_staleness.py`, `claim/release`, or Axis C on a live
   feature end to end. They are unit-tested and replay-verified against historical data, not
   battle-tested.
5. **[suggested] Re-measure the agent size cliff on the current host** — `references/agent-substrate.md`
   records 49 KB emitted / 53 KB silent from one agent in one session, explicitly marked
   order-of-magnitude. Axis C pushes design-audit prompts to ~88 KB, past it.

## Open / Blocked Items

- **Axis C prompt size** — status: shipped with a documented constraint, not solved. Design audits on
  a large feature assemble to ~88 KB against a ~50 KB cliff, and the baseline was already 72 KB
  before Axis C. Trimming the design is *not* available (it makes `absent` undetectable, which is the
  point of the axis). Shipped because #4's extraction guard makes an over-long prompt halt rather
  than silently pass. Recourse documented: split the audit by FR group.
- **#1 (`tui-idle`) is the one fix without a reproduction** — status: logic-verified only. A stub is
  idle by construction, so nothing here exercises a genuinely mid-response agent.
  `references/agent-substrate.md` carries a "Verification status" note naming the symptom to watch
  for (a partial read after `wait` returns) and says to reopen if seen.
- **HemaSuite `review-pipeline-correctness` Phase 6/7** — status: not mine to close. The other
  session corrected its Phase-7 report to 0% (`69976bf1`), so the contradiction I flagged is
  resolved, and it is now implementing design §8. Phase 6a-prime still never ran (no reviewer pane).
- **Two skills-repo worktrees were created and removed** — status: done, no residue. `git worktree list`
  shows one entry.

## Context for Next Session

**Files touched this session (skills, all merged + pushed):**
- `h-mad/scripts/` — new: `h_mad_state_write.py`, `h_mad_state_staleness.py`,
  `h_mad_phase7_preconditions.py`, `h_mad_extract_report.py`, `h_mad_extract_verdict.py`,
  `h_mad_state_validate.py`, `h_mad_state_schema_historical.json`; modified: `hmad-dispatch.sh`,
  `h_mad_emit_marker.sh`, `h_mad_resume_decision.py`, `h_mad_state_schema.json`
- `h-mad/bin/hmad-dispatch` (new PATH shim)
- `h-mad/SKILL.md`, `h-mad/audit-prompt.template.md`,
  `h-mad/references/{agent-substrate,failure-recovery,inline-protocols,state-schema}.md`
- `h-mad/tests/` — 9 new test files; suite 64 → 332

**Outside the repo:**
- `~/.claude/projects/-Users-kimhawk-orca/memory/` — consolidated store (92 files); four slugs
  symlinked to it
- `~/.claude/hooks/orca-memory-link.sh` — new SessionStart hook, registered in `settings.json`
- `~/.claude/skills/h-mad` and `~/.claude/hooks/h-mad-tdd-gate.sh` — both repointed from the stale
  `Coding/skills` clone to `orca/skills`

**Uncommitted changes:** none in `skills`. In `orca/HemaSuite`: 7 modified files and 1 unpushed
commit belonging to a concurrent session — do not stage them.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills            # main, clean, in sync
V=/Users/kimhawk/Coding/HemaSuite/hematology-paper-writer/.venv/bin/python
"$V" -m pytest h-mad/tests/ -q           # expect 332 passed

# HemaSuite side (concurrent session active — check before touching):
cd /Users/kimhawk/orca/HemaSuite/hematology-paper-writer
export PYTHONPATH=/Users/kimhawk/orca/HemaSuite/hematology-paper-writer   # dual-checkout hazard
```

**Related docs:**
- `https://github.com/BrightGold70/skills/issues?q=is%3Aissue` — all 14, closed, each with the
  measurement that motivated it
- `orca/HemaSuite/hematology-paper-writer/docs/03-analysis/review-pipeline-correctness.analysis.md`
  — the 0% analysis, v1.1 with the Gap 1 correction
- `orca/HemaSuite/hematology-paper-writer/docs/02-design/features/review-pipeline-correctness.design.md`
  §7–§9 — the reconciliation the operator decided; marked **not audited**
- Prior handoff: `docs/handoffs/2026-07-21-orca-arc-complete-hemasuite-wiring.md`
