# Handoff — skills backlog cleared: tdd-gate residuals, codex run verb, plugin-hooks 2.1.286, leak reaper

**Date:** 2026-10-01
**Branch:** main
**Project:** skills
**Supersedes:** 2026-09-30-main__tdd-gate-fail-opens-merged.md, 2026-10-01-main__codex-run-verb-conflict.md

## Session Summary

This session cleared the whole carried backlog on `main`. Everything is pushed, and HEAD is
`86479f73`.

- **Decided and coded:** operator decisions D-1 to D-4 and N-1, plus a fail-open in the `.`-then-`..`
  spelling found by review. Two of the three spellings were already on `main`.
- **Taken over and fixed:** the HemaSuite handover `codex-run-verb-conflict`. The Codex gate now
  admits `hmad-dispatch run` when it wraps a trusted command.
- **Re-based:** the plugin-hooks checker now follows Claude Code 2.1.286. This was the one
  long-standing failing test.
- **Live run:** the mhr V-11 smoke ran on 3 hosts.
- **Also landed:** the carried residuals (#11), a session-end leak reaper (#8), and skill candidates
  (a) and (c) (#12).

The full suite is **5259 passed, 0 failed**. It was the first fully green run in this repo for some
time.

## Key Learnings

- **A fresh-context reviewer found a fail-open that 300 targeted tests, mutation ALL_CAUGHT and a
  green suite all missed.** `tests/./../src/prod.py` resolved under `tests/`, so the Claude gate
  allowed a governed production write. A kept `.` component let the next `..` strip only itself. Two
  of the three spellings predated today's N-1 change. Probing 41k spellings beats reasoning about
  `dirname`.
- **A spec-literal pre-merge script can be unrunnable after the merge.** The mhr V-11 smoke halts on
  "integration already pushed", and its `recover()` reverts `PRE..HEAD`. Running it on `main` would
  revert history. Run part 2 only and drop the revert.
- **A residual's own count can be wrong.** The report said "three specs with an absolute
  interpreter". The census found nine in `command`, and another nine in `target_command` that the
  first fix missed.
- **There are two mutation-spec directories.** `h-mad/tests/mutation-specs/` and
  `h-mad/tests/specs/` are separate, and `--check-anchors mutation-specs/*.json` is blind to the
  second. Three anchors drifted there and were caught only by doc tests in the suite.
- **`git stash` on a clean tree is a trap.** It stashes nothing, so the following `stash pop` applies
  someone else's stash. This happened today with the foreign `resolved-model` stash. Only
  `handoff/SKILL.md` was touched and it was restored; the stash entry is intact. To measure old code,
  use `git show <rev>:path > tmp`.
- **A prediction miss is evidence and should be recorded, not adjusted away.** AC-1.9 (hard link)
  was predicted `no-test-resolved` and measured `test-missing`, because the gate judges the
  production name. The cell now pins the stricter measured behaviour.
- **Two mutation rows survived the first test set,** LR-ANCESTRY and the original
  `schema-becomes-an-allowed-top-level-key` (which became the real behaviour). Writing the mutation
  rows is what exposed a test that could not discriminate.

## Next Steps

1. **Operator decision:** should agy be required to load its runtime adapter even for a read-only
   `/h-mad status`? V-11.1 currently FAILs `no adapter read` on agy; it read
   `docs/.bkit-memory.json` directly. See
   `docs/archive/2026-09/multi-host-runtime/multi-host-runtime.live-smoke.md` §"Reading the two
   non-passes".
2. **Check once that HemaSuite picked up the run-verb fix.** The `citation-fidelity-judge-99` session
   was messaged to drop its "run pytest unbounded" ORCHESTRATOR NOTE. The send succeeded, which does
   not mean it was picked up. Look in
   `/Users/kimhawk/orca/workspaces/HemaSuite/citation-fidelity-judge` dispatch prompts for the
   note.
3. **[suggested]** Exercise `h_mad_assemble_tdd.py --phase green --mutation-spec <spec>` live on the
   next h-mad feature's 5e. It has only been tested offline.

## Open / Blocked Items

- **agy adapter question (V-11.1)** — status: blocked on an operator decision (Next Step 1).
- **HemaSuite run-verb notification** — status: delivered, pickup unverified.
  - repo: `/Users/kimhawk/orca/workspaces/HemaSuite/citation-fidelity-judge`
  - branch: `BrightGold70/citation-fidelity-judge`
  - The fix is on skills `main` `92b00839`, live through the symlink.
- **Foreign `stash@{0}` ("resolved-model")** — unchanged since 2026-09-29; untouched. It was briefly
  popped by mistake (see Key Learnings), the pop was reverted, and the entry is intact.
- **HemaSuite pointer `2026-09-14-main__wsg-backlog-two-items-owed-here.md`** — unchanged since
  2026-09-14; ownership stays here.
- **tdd-gate-fail-opens evidence bookkeeping** — recorded, deliberately not done. This covers
  `reading-fixed.txt` MANUAL R-4/R-5, the T0 absent-line control, the T7 record and census counts;
  see report §"Residual disposition".
- **Closed this session**, with commits:
  - D-1 to D-4, N-1: `8d9c9047`, `962c47fb`, `97bb84fc`.
  - `.`-then-`..` fail-open: `20b470ba`.
  - `codex-run-verb-conflict`, all brief Next Steps 1–4: `b5fd60c2`, `92b00839`. The claim was
    released.
  - #11 carried residuals: `4a3499a5`, `df8f8db6`, `b8df7822`. The two timing flakes were not
    reproduced (15 of 15 under 24-core load) and were left unchanged.
  - #13 `test_top_level_key_set_still_matches`: `58344684`, re-based on 2.1.286.
  - #14 mhr V-11 live smoke: `e4a1b286`. The grok-author trial decision is "not routine; optional",
    recorded in memory.
  - #15 locked worktree `agent-ae2695dac68faa13d`: removed together with its merged branch, after
    checking it had no live process and no unmerged commits.
  - #8 exec-pane wrapper leak: `4affd9e0`. A leak reaper runs at session end, and the full suite
    reported 0 leaks.
  - #12 skill candidates (a) and (c): `86479f73`.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/h_mad_target_identity.py`, `h-mad/hooks/h-mad-tdd-gate.sh`,
  `h-mad/hooks/h-mad-codex-tdd-gate.py`
- `h-mad/scripts/h_mad_resume_decision.py`, `h-mad/scripts/h_mad_check_plugin_hooks.py`,
  `h-mad/scripts/h_mad_audit_cycle.py`, `h-mad/scripts/h_mad_assemble_tdd.py`
- `h-mad/tests/conftest.py`, `h-mad/tests/leak_reaper.py`, many test files, and new mutation specs:
  `tdd_gate_differential`, `leak_reaper`, `audit_cycle_self_report`, `assemble_tdd_mutation_rows`
- `h-mad/SKILL.md` (5e `--mutation-spec`), `h-mad/references/codex-implementer-prompt.md`,
  `h-mad/references/agent-substrate.md`
- `docs/archive/2026-09/tdd-gate-fail-opens/*.{spec,design,report}.md`,
  `docs/archive/2026-09/multi-host-runtime/multi-host-runtime.live-smoke.md`,
  `docs/skill-candidates.md`

**Uncommitted changes:** none, apart from this handoff.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills && git checkout main && git pull --ff-only
# Next Step 1: decide the agy adapter question (live-smoke.md)
```

**Related docs:**
- `docs/archive/2026-09/tdd-gate-fail-opens/tdd-gate-fail-opens.report.md` §"Carry Items"
  (decisions and residual disposition)
- `docs/archive/2026-09/multi-host-runtime/multi-host-runtime.live-smoke.md`
