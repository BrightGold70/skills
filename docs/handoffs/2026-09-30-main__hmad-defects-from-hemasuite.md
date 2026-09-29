# Handoff — h-mad defects observed on HemaSuite #10 (asset-legend-native-citations)

**Date:** 2026-09-30
**Branch:** main
**Project:** skills
**Handover-From:** HemaSuite · main · session 7c01aa37-1ca2-424b-b714-7c57a5a3363d
**Supersedes:** none — first on this branch for this topic

## Session Summary

HemaSuite ran feature #10 (`asset-legend-native-citations`) through h-mad Phases 2–7, plus a Task 13 follow-up, on 2026-09-29/30. It merged as HemaSuite `fcca5ccb`. The run surfaced four h-mad defects and one tooling collision. None has been filed in this repo; this brief files them. Each item below states its measured evidence. Re-verify each premise before acting; a brief is a claim from a stopped session.

## Key Learnings

- Item (a)'s refusal is in `h-mad/scripts/h_mad_audit_cycle.py`, around the zero-evidence comment near line 61. It is not in `h_mad_collect_report.py`. The HemaSuite handoff had misattributed it to `collect-report`.

## Next Steps

1. **Triage and file** each item below as a `docs/skill-monitoring.md` row or a `docs/skill-candidates.md` row, whichever fits. Stamp `**Taken-Over-By:**` on this brief.
2. For each confirmed item, fix it test-first per the usual loop, or park it with a reason.

## Open / Blocked Items

- **(a) An agy report that self-reports "0 files opened" is refused as zero-evidence even when its NDJSON shows real reads.**
  - Status: to file.
  - Evidence: 2 of 2 agy audit legs on #10. `h_mad_review_evidence.py` on the `--log` read `EVIDENCE: PASS` with 20+ tools, yet the report's own `Evidence: 0 files opened` line was scored as zero-evidence. Both reports were kept unscored.
  - Evidence files: repo `/Users/kimhawk/orca/HemaSuite` · `docs/archive/2026-09/asset-legend-native-citations/asset-legend-native-citations.{design-audit-v1-agy,plan-audit-v2-agy}.unscored-zero-evidence.md`.
  - Open question: agy may count `run_command cat …` as 0 files opened. The self-reported line and the measured tool count disagree, and only the self-report is scored. Relates to the existing candidate at `docs/skill-candidates.md:1617` (the deliberate `zero-evidence` refusal); this is its false-positive side.
- **(b) `test_h_mad_tdd_gate.py::test_phase5_active_blocks_production_without_test` fails in HemaSuite's suite on main.**
  - Status: to file.
  - Evidence: red in three full HPW runs on 2026-09-30, on HemaSuite main: at merge `fcca5ccb` (12643 passed / 1 failed) and in two other lanes' merged-tree runs.
  - Cause is presumably drift between HemaSuite's copy of the test and the live hook (this checkout's `feature/tdd-gate-fail-opens` is changing that hook right now). Decide whether HemaSuite's copy should exist at all, or track the skills version.
- **(c) The Phase 5d/5e assembler (`h_mad_assemble_tdd.py`) never asks Codex for a mutation spec, and Codex's `workspace-write` sandbox cannot run `h_mad_mutation_harness.py`.**
  - Status: to file.
  - Evidence: on #10 Tasks 1–11 and on HemaSuite Task 13, MIGRATE-DETAIL and the reingest fix (2026-09-30), the spec was written only because the orchestrator added it to the prompt by hand, and the orchestrator ran every harness run itself.
  - Possible fix: an assembler flag that appends a "write (do not run) `tests/mutation-specs/<name>.json`" section.
- **(d) NEW: Codex cannot send `worker_done` from inside `exec codex`.**
  - Status: to file.
  - Evidence: 3 of 3 `hmad-dispatch exec codex` dispatches on 2026-09-30 (scratchpad outputs `t13.out`, `md.out`, `rl.out`) ended with "Orca rejected the `worker_done` send with `runtime_access_denied` (EPERM)". So the coordinator-signal path fails under the exec sandbox, while `rc` and `--out` still worked. Either the prompt should stop asking for `worker_done` on the exec path, or the sandbox needs the Orca socket.
- **(note, not h-mad) graft rewrites `.gitignore` and adds `.ignore` in every fresh git worktree.**
  - The uncommitted `.gitignore` edit made `git rebase` refuse (`Please commit or stash them`) in a HemaSuite worktree on 2026-09-30.
  - Worth a line only if h-mad's fanout `worktree-create` should anticipate it.

Location of all evidence: repo `/Users/kimhawk/orca/HemaSuite` · branch `main` (merged) · worktree none. Nothing is claimed in any h-mad state file for this brief.

## Context for Next Session

**Files touched this session (sender):** none in this repo apart from this brief.

**Uncommitted changes:** none from the sender.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
/handoff takeover   # adopt this brief, then triage (a)–(d)
```

**Related docs:**
- HemaSuite handoff that first listed (a)–(c): `/Users/kimhawk/orca/HemaSuite/docs/handoffs/2026-09-30-feature-10-asset-legend-native-citations__phase7-ready.md`
- The #10 report: `/Users/kimhawk/orca/HemaSuite/docs/archive/2026-09/asset-legend-native-citations/asset-legend-native-citations.report.md`
