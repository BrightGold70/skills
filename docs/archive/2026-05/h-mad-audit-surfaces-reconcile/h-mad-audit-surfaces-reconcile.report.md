# Report: h-mad-audit-surfaces-reconcile

## Executive Summary

Shipped three reconciliations to the `/h-mad` skill via the 7-phase H-MAD workflow. **(A) Audit-gate**: extracted the empty-section + blocking-count contract into one python-stdlib verdict unit (`h_mad_audit_gate.py`) consumed by both the orchestrator gate-step and `h_mad_do_preconditions.py`; the gate now signals via a `GATE: PASS|FAIL` stdout token + `[H-MAD]` marker and exits 0 on any verdict, so a legitimate gate-FAIL no longer registers as a Claude Code tool failure (the root cause of the OMC `[TOOL ERROR - RETRY REQUIRED]` noise). **(B) Doc templates**: extended all 7 phase-document templates to a superset satisfying the bkit PDCA validator's required sections while retaining the h-mad sections. **(C) Two-layer Axis B invariants**: added a skill-shipped `invariants.base.md` (workflow-universal) inlined before the per-project domain layer, so universal rules are enforced everywhere without re-copying. Outcome: **done** — 32 tests green, backward-compatible with all historical audits, agy architectural review READY_TO_MERGE.

## Outcome

- 8 implementation tasks, 6 feature commits + 1 fix commit on `feature/001-h-mad-audit-surfaces-reconcile`.
- Audit convergence: plan 3 cycles, design 2 cycles, impl-plan 1 cycle (all gate-clean). 6a-prime architectural review: 1 WITH_FIXES cycle (2 criticals fixed) → READY_TO_MERGE.
- Match rate 100% of Phase-5 ACs; full suite 32 passed.
- Dogfooded throughout: this feature's own plan/design/report validate clean against the bkit validator; the `- None` gate bug bit the audit-writing twice (live proof of the fix); the new gate reproduces every awk verdict from this feature's own audit history.

## Key Learnings

- The audit gate's `END{exit (c>0)}` exit-code-as-verdict was simultaneously the empty-`- None` false-FAIL bug AND the source of OMC retry-guidance noise (non-zero exit → `PostToolUseFailure` → `last-tool-error.json` → retry injection). One fix (token + exit 0) closed both.
- "Project-specific invariants" already existed (one file per repo); the missing layer was a **shared base** — without it, projects like HemaSuite enforced zero workflow invariants in their audits.
- A doc that embeds the literal `<INLINE_*>` slot tokens corrupts itself when inlined into an audit prompt; reference slot names descriptively in prose.

## Dependency Inventory (FR-6)

Verified this feature introduces **no new external dependency**:
- **Plugin dependencies: NONE.** `omc` = 0 references (passive runtime conflict only, documented in SKILL.md "Known interactions"); `bkit` = filename coupling (`docs/.bkit-memory.json`) + doc-structure target only; `spec-kit`/`b-mad`/`pdca` = disclaimers.
- **Intrinsic CLIs (not internalizable):** `cmux`, `agy`, `codex` — the multi-agent dispatch substrate.
- **Tooling:** `jq` (existing tdd-gate only), `jsonschema` (state-validate snippet), `pytest`. The new verdict unit is python-stdlib-only (enforced by `test_production_module_uses_only_stdlib_imports`).

## Version History

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-05-28 | Closure report — A/B/C shipped, 32 tests green, READY_TO_MERGE, dependency inventory confirmed zero new deps. |
