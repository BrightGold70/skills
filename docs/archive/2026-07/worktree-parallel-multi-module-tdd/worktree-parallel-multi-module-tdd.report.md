# Report: worktree-parallel-multi-module-tdd

## Executive Summary
Shipped Tier-3 of the Orca adaptation arc: three Orca-only `hmad-dispatch` worktree verbs plus a Phase-5 parallel-fanout protocol that lets independent impl-plan modules implement concurrently in isolated worktrees, with the serial path preserved as the unconditional fallback. Full suite 91/0, agy 6a-prime READY_TO_MERGE.

## Summary
Added `_json_extract` (single-source JSON helper) + `worktree-create`/`worktree-ps`/`worktree-rm` verbs to `hmad-dispatch.sh`, and documented the Phase-5 fanout protocol (partition → engage-conjunction → worktree-per-module dispatch → Tier-2 await → per-module merge with `git merge --no-ff` conflict detection → cleanup) in `SKILL.md` + `references/orchestration-mode.md`. Key design decision (via design-audit back-propagation): all three verbs route JSON extraction through one shared `_json_extract` helper to satisfy the Axis-B single-source contract — the plan's original "reuse Tier-2's helper" premise was inaccurate (Tier-2 inlines the idiom). Feature is additive; every non-orca / linear-DAG / unpinned-coordinator path keeps the current serial behavior.

## Metrics

| Metric | Value |
|---|---|
| Plan audit cycles | 3 (incl. back-propagation re-clean) |
| Design audit cycles | 2 |
| Impl-plan audit cycles | 2 |
| Iterate cycles (Phase 6b) | 0 (100% first pass) |
| Final match rate | 100% |
| Tests | 91 passing / 0 failing |
| Phases with back-propagation | Phase 4 → Phase 3 (single-source `_json_extract`) |

## What Went Well
- The design-audit cross-doc check caught a genuine single-source drift (3 inlined jq chains) AND surfaced that the plan's "reuse Tier-2 helper" premise was factually wrong — back-propagation corrected both docs before any code.
- Independent Codex authorship improved the spec: `_cmd_worktree_rm` used `local rc=0; orca … || rc=$?` (survives `set -euo pipefail`) instead of the naive `orca …; local rc=$?` in the impl-plan — agy 5e flagged it as an improvement.
- Schema-verified every `orca worktree …` argv against `agent-context --json` at build time (Tier-1 lesson), avoiding the guessed-verb class of bug.

## What To Improve Next Time
- The impl-plan's `_cmd_worktree_rm` snippet had a latent `set -euo pipefail` abort bug; pre-check bash error-handling idioms in impl-plan code blocks before dispatch.
- The 19.7KB audit prompt fragmented on the first `hmad-dispatch send` (paste threshold); switched to short-message file-indirection. For any prompt >5-10KB, default to file-indirection from the start (F-12).

## Carry Items
- **Live-Orca e2e** — every worktree verb + the fanout protocol is stub-tested only; no real Orca-hosted-agent runtime has exercised `worktree-create → dispatch → await → merge → rm`. Standing gap shared with Tier 1/2/launch-profile. Deferred (non-blocking).
- **`test_json_extract_helper`** — the design named a standalone helper unit test; Codex folded 100% path coverage into the create/ps verb tests (agy-confirmed non-critical). Optional future: add the named direct test for clarity.
- Cmux default agent map in `hmad-dispatch.sh` (`codex→surface:5`, `agy→surface:2`) remains STALE vs the live layout (Codex=surface:4, agy=surface:5); pinned via env this session. Pre-existing, out of this feature's scope.

## Version History
- v1.0: Initial report draft.
