# Phase Table — 7-phase /h-mad v2.2

| # | Phase | Orchestrator action | Pass gate | Mode |
|---|---|---|---|---|
| 1 | Brainstorm | Invoke `/brainstorm`; wait for user-approved `_bmad-output/brainstorming/brainstorming-session-*.md`. Prompt to advance. | User approves | Manual |
| 2 | Specify | Invoke `/speckit.specify`; wait for `specs/NNN-feature/spec.md`. Prompt. | User approves | Manual |
| 3 | Plan + Audit-Plan | Invoke `/pdca plan`; wait for `<feature>.plan.md` v1.0 user approval. Auto-cycle: `/pdca audit-plan` → awk gate → if must-fix > 0, surface bullets + wait for user revision → re-audit. Exit when must-fix = 0. | Plan exists AND latest `.plan.audit.v<N>.md` must-fix=0 | Manual (per audit cycle) |
| 4 | Design + Audit-Design | Same pattern as Phase 3 with `/pdca design` + `/pdca audit-design` (adversarial + cross-doc). Back-propagation: if design fix invalidates plan, return to Phase 3 for re-clean. | Design exists AND latest `.design.audit.v<N>.md` must-fix=0 AND plan unchanged-since-last-audit | Manual (per audit cycle) — **last user touchpoint** |
| **5** | **Implementation** | Autonomous sub-steps 5a–5g (see SKILL.md) | All RED→GREEN; impl-plan audit must-fix=0; zero hook violations | **Autonomous** |
| **6** | **Verification** | Autonomous sub-steps 6a-prime, 6a, 6b (see below) | Architectural review READY_TO_MERGE; match rate ≥ 90% AND 100% test pass | **Autonomous** |
| **7** | **Closure** | Autonomous sub-steps 7a–7e (see below) | Push to origin/main succeeds | **Autonomous** |

## Phase 6 sub-steps

- **6a-prime (v2.1 NEW)** — Final architectural review via `references/agy-architectural-reviewer-prompt.md`. Halt on WITH_FIXES or NO verdict.
- **6a** — Invoke `/pdca analyze` → `docs/03-analysis/<feature>.analysis.md`. Parse match rate.
- **6b** — If match rate < 90%, invoke `/pdca iterate` (5-cycle cap). After each iterate, re-run `/pdca analyze`. Loop until ≥ 90% AND 100% test pass. On 5-cycle exhaust, halt `step6:iterate_max_cycles`.

## Phase 7 sub-steps

- **7a** — Invoke `/pdca report` → `docs/04-report/features/<feature>.report.md`. Verify exists + non-empty.
- **7b** — Invoke `/pdca archive` → moves plan/design/impl-plan/audit/analysis/report docs to `docs/archive/<YYYY-MM>/<feature>/`. Verify archive dir + source paths emptied.
- **7c** — `git add -A && git commit -m "feat(<feature>): land via /h-mad\n\n<body>"`. Body from state + analysis match rate. No `--no-verify`.
- **7d** — Pre-push: branch is `main`. `git push origin main`. Verify SHA.
- **7e** — Clear or tombstone `orchestrator_state[<feature>]`. Emit complete marker. `cmux notify`.

## Cycle caps

| Cap | Where | Value |
|---|---|---|
| Audit cycles per phase | Phases 3, 4 (per audit-phase spec) | 5 |
| Impl-plan audit cycles | Phase 5b (v2.1 NEW) | 5 |
| Iterate cycles | Phase 6b (existing `/pdca iterate`) | 5 |
| Codex retries per module | Phase 5e GREEN | 3 |

## Logger marker

`[H-MAD] <feature> phase<N> <decision>` where decision ∈ `entered | gate_passed | gate_failed | autonomous_entered | autonomous_complete | halted | back_propagated | audit_cycle_started | audit_clean`.

Use `scripts/h_mad_emit_marker.sh <feature> <N> <decision>` to write.
