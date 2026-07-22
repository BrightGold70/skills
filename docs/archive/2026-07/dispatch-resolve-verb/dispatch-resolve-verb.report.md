# Report: dispatch-resolve-verb

## Executive Summary
Added `hmad-dispatch resolve <agent>` — a scriptable single-agent handle lookup — as a pure forwarder to `_resolve_target`, shipped through a full 7-phase H-MAD run with every audit cycle delivered over report-file transport.

## Summary
The verb exposes the resolution `env` already computes for both agents, for one agent at a time: handle→stdout/exit 0, empty stdout + stderr diagnostic/exit 1 when unresolved, exit 2 for unknown/missing agent. The load-bearing decision — surfaced by the plan audit — was to make `_cmd_resolve` a pure forwarder with no agent allowlist of its own, so `_resolve_target` stays the single source for both resolution and validation (Single-source invariant). Outcome: 6 FRs, 100% AC coverage, 393/393 suite, live-verified against the real Orca runtime.

## Metrics

| Metric | Value |
|---|---|
| Plan audit cycles | 2 (v1 must-fix: duplicate agent validation → v2 clean) |
| Design audit cycles | 1 (clean, all 16 ACs `implemented-as-written`) |
| Impl-plan audit cycles | 1 (clean) |
| Iterate cycles (Phase 6b) | 0 (100% match on first gap analysis) |
| Final match rate | 100% |
| 6a-prime architectural review | `READY_TO_MERGE` |
| Tests | 393 passing / 0 failing (7 new resolve cases) |
| Phases with back-propagation | None |

## What Went Well
- **Report-file transport carried every audit + TDD verdict** (plan ×2, design ×1, impl-plan ×1, Codex RED, Codex GREEN, agy 5e review, agy 6a-prime) with zero screen-scrape, zero sentinel extraction, zero dedent/normalize — the mechanism this run set out to validate, proven end-to-end.
- **The plan audit earned its keep**: it caught the duplicate-validation Single-source violation before any code existed, so the fix was a doc edit, not a refactor.
- **Independent RED verification** caught that `-k resolve` also matches pre-existing tests; the authoritative `-k test_resolve_` run (0 passed / 7 failed) confirmed a genuine RED.

## What To Improve Next Time
- **Codex editing the very wrapper the coordinator polls with caused a transient syntax-error race**: a `report-wait` fired while Codex was mid-save on `hmad-dispatch.sh` and hit `syntax error near unexpected token ')'`; `bash -n` was clean moments later. When the implementer's target file IS the dispatch wrapper, poll the report marker with a tolerance for a transient unparseable wrapper (or copy the wrapper aside for polling).
- **Codex identity by preview decays**: mid-run, `resolve codex` went UNRESOLVED because the Codex pane's model-id banner (`gpt-5.6-terra`) scrolled out of the preview window after it did work — the H2 alias match only helps on a fresh banner. Pinning `HMAD_ORCA_CODEX_TERMINAL` (this run did) is the durable fix; auto-detect is a convenience, not a guarantee, for Codex.

## Carry Items
- Consider persisting the Codex/agy pins to `.h-mad/` or documenting the pin-on-decay behavior in `agent-substrate.md` so a long autonomous run doesn't lose the Codex pane after the banner scrolls (H2 alias is best-effort only).

## Version History
- v1.0: Initial report draft.
