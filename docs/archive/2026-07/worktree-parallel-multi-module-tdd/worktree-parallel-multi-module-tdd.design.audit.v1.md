# Design Audit v1 — worktree-parallel-multi-module-tdd

Reviewer: agy (Gemini 3.1 Pro High), Reviewer.adversarial_consistency + Analyzer.cross_doc_consistency. Cycle 1.

## Summary
The design comprehensively addresses the paired plan (three Orca worktree verbs, concurrency cap, Phase-5 fanout). But it exhibits silent drift from the plan's implementation strategy: it fails to reuse a single JSON-extraction helper, instead forking the parsing logic inline across the three new verbs.

## Must-fix
- Cross-doc consistency gap / Single-source contract violation — the plan mandated "Reuse the same JSON-extraction helper Tier 2 uses for orchestration output — do not fork a second parser," but the design inlines a new `jq -r` fallback chain per verb ("identical in spirit to `_cmd_task_create`'s taskId chain"). Three inlined re-implementations can silently diverge, breaching the Axis B single-source contract. (Note: Tier-2 has NO shared extractor function — it inlines the idiom — so the plan's "reuse the helper" premise is itself inaccurate and must be corrected via back-propagation.)

## Should-fix
None

## Nit
- Plan goal G4 (reconcile Orca argv against schema v1 "at build time") is validated in tests via hardcoded stub JSON; the design does not state whether schema pinning is automated or manual.
