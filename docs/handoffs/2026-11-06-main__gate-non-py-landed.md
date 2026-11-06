# Handoff — gate-non-py-production-files landed on origin/main

**Date:** 2026-11-06
**Branch:** main
**Project:** skills
**Supersedes:** 2026-11-05-main__gate-non-py-phase5-complete.md
**Next-Session Focus:** No feature is in flight here. Choose from the carried backlog; the first item is the five H-MAD tool candidates from 2026-11-05.
**Suggested-Skills:** handoff (resume), h-mad (only if a candidate grows into a feature)

## Session Summary

Done: H-MAD feature `gate-non-py-production-files` (row 2856) ran Phases 6 and 7 and is on `origin/main` at `fbb47d8a`, 98 commits pushed. All three TDD gates now judge a listed code-like non-`.py` file; doc and data files stay exempt. Phase 6 changed production code as well as documents: a file named exactly `.py` is now Python on codex and agy, and `_tmp_report_target` reads every canonical name through `canonicalise`.

Final readings at the merged tree: suite 8645 passed, `INTEGRATE: MERGED … identity=n suite=PASS`. At `bbcd731b`: mutation 161 of 161 across 13 specs, anchors 3043 of 3043, analysis v5 100% (55 of 55 ACs), and one earlier full run with 1 failure. FR-9 33 of 33 at `e524b58a`; no hook or script changed after it.

## Key Learnings

- **A marker census cannot see unmarked code.** v1 read 100% from matching `# M:` markers; v2 found 3 unmarked arms by reading, and a diff-derived census in v3 found 16 more, 3 with no test at all. The code had not moved, so the first 100% was over-stated. AC-9.3 now rests on v4's census, and a fourth was declined by the operator.
- **The suite can pass a branch the live hook never takes.** Test `_run` uses `sys.executable` (Python 3.11), while the hooks run under `python3` (3.15 here). `Path.resolve()` raises on a symlink loop on 3.12 and earlier and returns on 3.13 and later, so a test asserting the `RuntimeError` text passed for the wrong reason.
- **An empty path reads as the process cwd.** Every unresolvable `Identity` has `target=""`, and `_path_within("", /tmp)` resolves that against cwd, so it reads True for a hook process under `/tmp`. That is why `# M:CX-TMP-PY-UNRESOLVABLE` is a real guard, and it survived mutation until its test's process ran under `/tmp`.
- **All-unreadable fixtures hid a class.** Every second-plan fixture wrote invalid UTF-8, so no test had a readable second active plan, and a first-plan-only mutant read ALLOW on all hosts with 242 tests passing while `L-ANY-PLAN` reported caught.
- **`--isolate` with a relative `--python` falsely reads `BASELINE_NOT_GREEN`,** on every spec. Pass an absolute path. Codex's sandbox refuses `--isolate` entirely, so the orchestrator must run the harness; that is how a `SURVIVED` was caught behind a codex `STATUS: DONE`.
- **`h_mad_baseline_sha.py` reads `UNVERIFIED` when phase documents were committed on the branch before 5c.** The handoff's merge-base would have fed every audit document into the review as new; I took the last commit before the first RED, by hand.
- **Three of six agy reviews saw nothing at issue for the code later changed, and v2 and v3 did not mention the hard link.** agy's citations also drift: wrong line numbers and paraphrased "quotes" in v2. Conclusions had to be checked against the tree each time.
- **`PHASE7: READY` checks 90%, not the verifier's verdict.** It read READY at 91% with must-fixes open, so the gate alone would have let those through.

## Next Steps

1. **Pick up the five H-MAD candidates of 2026-11-05, plus this session's** — `docs/skill-candidates.md`, sections `2026-11-05 — gate-non-py-phase5-complete` and `2026-11-06 — gate-non-py-landed`. Run `python3 handoff/scripts/skill_candidates_census.py docs/skill-candidates.md` for the open set.
2. **Hawui-Macmini sync** — on that machine: `git pull`; drop the 2026-11-01 `assemble_tdd` stash; compare its 9 Macmini-only env failures with `h_mad_failure_diff.py`. The pull now brings the new gates too.
3. **If `test_heartbeat_stamps_across_three_intervals` fails again, keep the run's `calls` capture before re-running** — `h-mad/tests/test_hmad_dispatch_exec_stamp.py:427`. Only that separates a starved loop from a dropped beat.
4. **Remove the worktree when no longer wanted, after copying its state record if you want it kept** — `git worktree remove /Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files`. Kept for now on purpose; see Open Items.
5. **[suggested] Review or retire draft plan `backlog-row-cycle`** — `docs/01-plan/features/backlog-row-cycle.plan.md`.
6. **[suggested] Review draft plan `hpw-duplicate-copy-retirement`** — `docs/01-plan/features/hpw-duplicate-copy-retirement.plan.md`.

## Open / Blocked Items

**From this session:**
- **Intermittent suite failure, cause unestablished.** `test_heartbeat_stamps_across_three_intervals` failed 1 of 3 full runs of this content; beats were at 0s and 3s. `FAILDIFF: SAME` over 5 repeats with 0 failures, and `FLAKE-VERDICT: NOT_REPRODUCED runs=30`. The feature does not touch the test or the wrapper. "Flake" is an inference. Status: open, watch.
- **AC-9.3 rests on v4's census.** Censuses found 3, 16 and 2 lines; the operator declined a fourth on 2026-11-06, so more unanchored lines may exist. Status: accepted, not closed by proof.
- **The recorded `READY_TO_MERGE` was earned under a narrowed rubric.** My sixth-review prompt restricted Critical. Tests and rows added after `e524b58a` were read by verifiers, not agy. Stated in `archreview.v6.md`'s commit and the impl-plan. Status: accepted.
- **Named residuals, not fixed, by operator choice.** A listed file with a same-directory `test_*.py` hard link reads DENY on Claude and ALLOW on codex and agy, predating this feature. A hard link in a different directory reads ALLOW on all three hosts. Both are in spec v1.15. Status: deferred.
- **`crash_visible=0/0` on the host specs.** `crash_kills=0` has no denominator there, so only reading the assertion line tells a crash from a guard. Rows beyond those read this session stay unread. Status: open; candidate filed.
- **Primary record of the 2026-11-04 operator ruling behind the ninth FR-9 refusal: not found.** Visible only through the impl-plan. AC-9.5 does not depend on it. Status: open, needs the operator's memory if it matters.
- **11 nits** in `docs/archive/2026-11/gate-non-py-production-files/gate-non-py-production-files.analysis.v5.md`, including the double `kind=` token on codex for `scripts/kind=x.sh`. Status: deferred.
- **Machine-wide `pkill` disclosure.** Stopping a run, I ran `pkill -f "h_mad_mutation_harness.py --isolate"`, not scoped to this worktree. A sibling lane's isolated mutation run could have died around 2026-11-06 early morning; a re-run is enough. No evidence either way. Status: informational.
- **Feature record exists only in the worktree's gitignored state.** `orchestrator_state` in `/Users/kimhawk/orca/skills/docs/.bkit-memory.json` has no record for this feature; the worktree's reads `last_completed_phase=7`, owner `None`, oracle `complete`. Removing the worktree loses it; the report, archive and row stamp remain. Status: informational.
- **Foreign, not owned here: BUG-4's step-5 record sits in the CSA worktree's state.** `repo: /Users/kimhawk/orca/HemaSuite · branch: feature/211-csa-tier3-sandbox-runner · worktree: /Users/kimhawk/orca/workspaces/HemaSuite/csa-tier3-sandbox-runner`, file `docs/.bkit-memory.json`, record `bug-4-publication-integrity`, `phase=step5`, owner `094da1cc`, while its impl-plan is absent there. Not touched: it may have a live owner. It looks misplaced, and I did not establish why. Status: raised to the operator in this session's report.
- **Leftovers outside any repository:** `/private/tmp/claude-501/-Users-kimhawk-orca-skills/85400c95-33ed-40d1-b2e9-1d8141402dc6/scratchpad/specv115.ZiEcdd` and `/var/folders/7s/9n332lmj54511rf57fgf8pz40000gn/T/tmp.XQvHmCxplQ`; the delete hook blocked both. Status: harmless.

**Carried unchanged:**
- **Five H-MAD candidates of 2026-11-05** (`assemble-tdd-red-forbids-plan-stubs`, `green-prompt-demands-a-wire-cut-the-gate-refuses`, `assembled-test-command-the-gate-denies`, `hostile-path-limits-in-the-red-template`, `assemble-the-agy-spec-review`) — not picked up, unchanged since 2026-11-05.
- **Hawui-Macmini sync** — unchanged since 2026-11-02. `repo: /Users/kimhawk/orca/skills (Hawui-Macmini) · branch: main · worktree: none`.
- **Watch-only triage rows; residuals of the 2026-10-31 stamps and 2026-11-01 landings; Run 8 attempts 1–2** — unchanged since their dates.
- **HemaSuite-owned items** (drafting quality without CLAUDE.md, the judge-sdk branch, unconditional restores) — unchanged; not owned here. `repo: /Users/kimhawk/orca/HemaSuite · branch: main · worktree: none`.
- **Pre-existing untracked files in `~/orca/skills`** (`.codex/config.toml`, three `docs/03-analysis/2026-10-2*.analysis.md`, `hemasuite/docs/research/`) — not mine, untouched.
- **Draft plans** `backlog-row-cycle` and `hpw-duplicate-copy-retirement` — unchanged.

**Closed:**
- **Row 2856** — LANDED, `fbb47d8a`, stamped in `docs/skill-candidates.md`.
- **Phase 6a-prime, 6a, Phase 7** — six reviews and five analyses, under `docs/archive/2026-11/gate-non-py-production-files/`; report beside them.
- **Design v1.4 owed text (nine refusals, `plan-absent-at-base`, three-arm skip test)** — done in v1.5, now v1.12. **Impl-plan 99-to-100 row correction** — superseded; v1.11 reads 124.
- **Accepted deviations** (`H-LIST-CONTEXT`, Task 3's fixture, `if True:` rows) — recorded in the impl-plan's departures; review did not object.
- **Prototype readings marked unverified** — re-read by each Task's tests and all green, per predecessor.
- **FR-9 retake before push** — re-run at each hook change; latest at `e524b58a`, 33 of 33. The driver refuses a replay once base equals HEAD, which now holds.
- **Backup refs** `backup/gate-non-py-pre-rebase-767be799` and `-22fd2b2a`: kept, because AC-9.5 cites `e4979ecd`, reachable only through them. Do not delete.

## Context for Next Session

**Files touched this session:** on the merged branch, `h-mad/hooks/h-mad-codex-tdd-gate.py`, `h-mad-agy-tdd-gate.py`; `h-mad/scripts/h_mad_target_identity.py`; `h-mad/tests/test_h_mad_{tdd_gate_non_py,codex_tdd_gate_non_py,agy_tdd_gate_non_py,codex_gate_tmp_reports,tdd_judge_listing,parse_tasks_non_py}.py`, `non_py_gate_support.py`; mutation specs `listing_matcher`, `claude_gate_listing`, `codex_gate_listing`, `agy_gate_listing`, `shared_gate_policy`, `codex_gate_tmp_reports`, `agy_tdd_gate`; FR-9 evidence directories; spec v1.15, design v1.12, impl-plan v1.11, archived; `docs/04-report/features/gate-non-py-production-files.report.md`, archived. On `main` after merge: this doc, `docs/learnings.md`, `docs/skill-candidates.md`.

**Worktree:**
- Worktree root: `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files` — branch: `BrightGold70/gate-non-py-production-files`, merged, clean. Kept.
- Parent repo: `/Users/kimhawk/orca/skills` — branch: `main`, shared with other lanes; check it right before any write.

**Uncommitted changes:** none but the pre-existing untracked files above.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch
python3 handoff/scripts/skill_candidates_census.py docs/skill-candidates.md
```

**Related docs:**
- `docs/archive/2026-11/gate-non-py-production-files/gate-non-py-production-files.report.md`
- `docs/archive/2026-11/gate-non-py-production-files/gate-non-py-production-files.analysis.md` (v5)
- `docs/archive/2026-11/gate-non-py-production-files/gate-non-py-production-files.impl-plan.md` §"Where this plan departs", items 11 to 17
