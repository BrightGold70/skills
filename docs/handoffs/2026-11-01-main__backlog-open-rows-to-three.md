# Handoff — Backlog down to 3 open rows: F3, 2854, 2729 git half, 2853 warn, 2816 re-anchor diff

**Date:** 2026-11-01
**Branch:** main
**Project:** skills
**Supersedes:** 2026-11-01-main__triage-closed-codex-unwedged.md
**Next-Session Focus:** Decide the 3 open `docs/skill-candidates.md` rows (2729 interpreter half, 2855 `.sh` gate as an /h-mad feature, 2889 append-row), or check HemaSuite's state file on the Mac Studio for owned null-heartbeat claims.
**Suggested-Skills:** handoff (resume and carry-forward), h-mad (row 2855 gate half, if chosen)

## Session Summary

This session ran on Hawui-Macmini. It resumed `2026-10-31-main__skill-backlog-clusters-a-d.md` and took the backlog from 9 open rows to 3. Every row got a user ruling, and each change was built test-first and pushed (`f6864fbd`..`acb228e0`). The commits landed:

- **Scout rows 2878–2881:** stamped. Two turned out to describe tools that already existed and were marked SUPERSEDED (`census --apply`, `h_mad_failure_diff.py`).
- **Auto-param-id lint (2889):** landed in `--check-anchors`, along with fixing the 6 auto-id rows it found.
- **TLA+ F3 (`437fb457`):** a missing or unparseable heartbeat now means unknown age, not a live owner.
- **2854:** DECLINED.
- **2729, git half (`23449c7c`):** the Phase-5 gate admits 9 read-only `git` verbs, with the denylist the user agreed.
- **2853, warn half (`af943118`):** the wire-pin check prints `ungated:` lines for non-`.py` production files.
- **2816 (`93adcc7c`):** new `h_mad_reanchor_diff.py`, using the refined edit-delta rule. All finished.

## Key Learnings

- **Calibrate a user-ruled rule on real history before shipping it.** For 2816, the "identical removed and added tokens" rule flagged 7 of 10 real re-anchors. One of them was this session's legitimate `empty-argv-returns-clean` re-anchor: a mutant that deletes a whole statement removes more tokens when that statement grows. Requiring the same added tokens, with nested removed sets, flags only the 2 rows from the known-bad `2d087a39` rewrite. The user re-ruled on that data.
- **Never edit the subject tree while `h_mad_failure_diff.py run` is measuring it.** I appended tests mid-run, which put the measurement at risk; I moved the work to a separate worktree and cherry-picked it back. Always pass `--log-dir` and never pipe the run through `tail`, or the subject-only test ids are lost and the whole run (about 1h) has to be repeated.
- **A DECLINED stamp needs `(triage: ...)` within 40 characters of `DECLINED`**, because `TRIAGE` in `skill_candidates_census.py:73` searches for it. `(user ruling, calibrated)` broke `test_the_live_backlog_has_no_unqualified_declined`. The fix is `(triage: not-useful, calibrated; user ruling)`.
- **Widening a gate's allowlist breaks tests that used the newly admitted command as their "refused" example.** `git status` was that example in the agy/codex differential and in two `test_h_mad_codex_runtime.py` lists; the replacement example is `git stash`. Grep the tests for the command before running the full suite.
- **The Phase-5 gate is a TDD-discipline gate, not a sandbox.** It does not refuse writes to `.git/config` (non-`.py` writes are ungated). It already admits `pytest` on test files Codex can write, so a configured `diff.external` adds no new capability. I first told the user otherwise and corrected it.

## Next Steps

1. **Check HemaSuite on the Mac Studio for owned records with a null heartbeat.** Since `437fb457`, such a record is takeable unless its owner's transcript is fresh. Inspect `owner_session_id` / `owner_heartbeat_ts` in `/Users/kimhawk/orca/HemaSuite/docs/.bkit-memory.json` (machine-local on the Studio).
2. **Decide row 2729's interpreter half** (`docs/skill-candidates.md:2729`): `h_mad_assemble_tdd.py:633` emits `{python} {harness} --check-anchors`, and `_safe_argv` refuses `/opt/anaconda3/bin/python3`. The fix direction is to emit the anchor check with a trusted interpreter.
3. **Row 2855 gate half** (`.sh` production files gated by Task, not by suffix) is an `/h-mad` feature. It touches `h_mad_wire_pin_gate._parse_tasks`, the Claude/Codex/agy write gates, and the judge's red rules.
4. **Row 2889 (`maybe`):** append mutation rows without reformatting the spec. Decide, or keep it deferred.
5. **Fix the `test_grok_audit_surface_wrapper.py` stamp-leg failures** (carried from the predecessor's Next Step 3). This Mac sees 4 failing (`test_codex_agy_cycle_stamps_carry_the_legs_that_ran`, `test_three_surface_stamps_carry_sorted_legs`, `test_three_surfaces_map_pass_index_to_agent`, `test_three_surfaces_print_no_repeated_warning`). They fail on both the subject and the control tree, so they predate this session. The predecessor's diagnosis is a missing `h_mad_test_boundaries_check.py` symlink in `real-cycle-scripts/`.
6. **New scout row (this closeout, `candidate: yes`):** `failure-diff cannot see the subject tree change mid-run`. Hash the subject before and after each run and end `UNREADABLE reason=subject-changed` when the hashes differ — `h-mad/scripts/h_mad_failure_diff.py:435`. Census is now `OPEN=4`.
7. **[suggested]** Wire `h_mad_reanchor_diff.py` into the step where an implementer re-anchors rows (currently manual): `h-mad/scripts/h_mad_reanchor_diff.py --base <ref> <spec>...`.

## Open / Blocked Items

**Carried from `2026-11-01-main__triage-closed-codex-unwedged.md`:**

- **Mac Studio bkit `2.1.40 → 2.1.41` + patches:** closed. The user reported on 2026-11-01 that all Mac Studio todos are resolved; not verified from the Mini.
- **Codex pin stale on Mac Studio:** closed (predecessor, plus the user's report).
- **Census `OPEN=5`:** now `OPEN=3`.
  - 2854 DECLINED (`a9545dc2`, qualifier fixed in `acb228e0`).
  - 2816 LANDED (`93adcc7c`).
  - 2729: git half landed (`23449c7c`), interpreter half open (Next Step 2).
  - 2853, now line 2855: warn landed (`af943118`), gate deferred (Next Step 3).
  - 2885, now line 2889: open (Next Step 4).
- **`test_grok_audit_surface_wrapper.py` stamp-leg failures:** open, unchanged (Next Step 5).
- **Watch-only rows in `docs/03-analysis/2026-10-25-backlog-triage.md`** (19, 51, etc.): unchanged since 2026-10-27.
- **Residuals from the 2026-10-31 stamps** (name-map `*test_*` skip, archreview `.assembled` receipt, user-level agy `hooks.json`, Codex hook timeout): unchanged since 2026-10-31.
- **Run 8 attempts 1–2:** evidence only, never a score. Unchanged since 2026-10-27.
- **HemaSuite Task 6 WIRE-RUNNER (local task #13), wire-registry `missing=268` (#14):** closed in `d05c85da` per the predecessor.

**New this session:**

- **Residuals of this session's landings** (recorded in the row stamps, not filed as rows):
  - Git config already present (`diff.external`, `core.fsmonitor`, textconv) still runs under admitted `git diff`/`git status`.
  - `--text` is refused, as a prefix of `--textconv`.
  - The re-anchor rule passes a rewrite that keeps the added tokens but deletes a larger unrelated region.
- **Environment-only failures on Hawui-Macmini:** 38, the same set on subject and control (`python3.11` and `/opt/anaconda3` absent, `hmad_dispatch_audit_cycle`, and others). Use `h_mad_failure_diff.py`, never counts.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/h_mad_state_ownership.py`, `h-mad/scripts/h_mad_state_write.py`
- `h-mad/scripts/h_mad_target_identity.py`
- `h-mad/scripts/h_mad_wire_pin_gate.py`
- `h-mad/scripts/h_mad_reanchor_diff.py` (new)
- `h-mad/scripts/h_mad_mutation_harness.py` (auto-param-id lint)
- `h-mad/audit-prompt.template.md`, `h-mad/references/codex-implementer-prompt.md`, `h-mad/references/codex-verifier-prompt.md`
- Tests:
  - `test_h_mad_claim_staleness.py`, `test_h_mad_state_write.py`
  - `test_h_mad_gate_git_verbs.py` (new), `test_h_mad_reanchor_diff.py` (new), `test_h_mad_mutation_auto_param_ids.py` (new)
  - `test_h_mad_wire_pin_gate.py`, `test_h_mad_agy_tdd_gate_differential.py`, `test_h_mad_codex_runtime.py`, `test_h_mad_tdd_judge.py`
- Mutation specs (new): `null_heartbeat_unknown_age.json`, `gate_git_verbs.json`, `wire_pin_ungated.json`, `reanchor_diff.json`, `auto_param_ids.json`
- `handoff/scripts/skill_candidates_census.py`, `handoff/SKILL.md`, `handoff/tests/*`
- `docs/skill-candidates.md`

**Uncommitted changes:** none from this session (the pre-existing untracked items the predecessor listed may remain).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main && git pull --ff-only
python3 handoff/scripts/skill_candidates_census.py --list-open docs/skill-candidates.md
# full-suite gate on this Mac:
P=/opt/homebrew/opt/python@3.14/bin/python3.14
$P h-mad/scripts/h_mad_failure_diff.py run --base <ref> --python $P --log-dir <dir> -- h-mad/tests handoff/tests
```

**Related docs:**
- `docs/handoffs/2026-11-01-main__triage-closed-codex-unwedged.md`
- `docs/skill-candidates.md` (rows 2729, 2855, 2889)
