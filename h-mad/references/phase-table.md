# Phase Table — 7-phase /h-mad v2.2 (standalone)

| # | Phase | Orchestrator action | Pass gate | Mode |
|---|---|---|---|---|
| 1 | Brainstorm | Inline brainstorm protocol (`references/inline-protocols.md §Phase 1`). Output: `docs/01-plan/features/<feature>-brainstorm.md`. Prompt to advance. | User approves | Manual |
| 2 | Specify | Inline spec protocol (`references/inline-protocols.md §Phase 2`). Output: `docs/01-plan/features/<feature>.spec.md`. Prompt. | User approves | Manual |
| 3 | Plan + Audit-Plan | Inline plan generation (`references/inline-protocols.md §Phase 3`). Output: `docs/01-plan/features/<feature>.plan.md`. Wait for user-approved v1.0. Auto-cycle: audit-plan via agy → awk gate → if must-fix > 0, surface bullets + wait for user revision → re-audit. Exit when must-fix = 0. | Plan exists AND latest `.plan.audit.vN.md` must-fix=0 | Manual (per audit cycle) |
| 4 | Design + Audit-Design | Inline design generation (`references/inline-protocols.md §Phase 4`). Output: `docs/02-design/features/<feature>.design.md`. Same audit cycle pattern as Phase 3. Back-propagation: if design fix invalidates a plan decision, return to Phase 3 for re-clean, then re-enter Phase 4 audit from cycle 1. | Design exists AND latest `.design.audit.vN.md` must-fix=0 AND plan unchanged-since-last-audit | Manual (per audit cycle) — **last user touchpoint** |
| **5** | **Implementation** | Autonomous sub-steps 5a–5g (see SKILL.md §Phase 5). | All RED→GREEN; impl-plan audit must-fix=0; zero hook violations | **Autonomous** |
| **6** | **Verification** | Autonomous: 6a-prime (agy architectural review), 6a (inline gap analysis), 6b (inline iterate). | Architectural review READY_TO_MERGE; match rate ≥90% AND 100% test pass | **Autonomous** |
| **7** | **Closure** | Autonomous: 7a (telemetry), 7b (inline report), 7c (inline archive), 7d (commit), 7e (push). | Push to origin/main succeeds | **Autonomous** |

## Phase 6 sub-steps

- **6a-prime** — Final architectural review via agy (`references/agy-architectural-reviewer-prompt.md`). Halt on `WITH_FIXES` or `NO` verdict.
- **6a** — Inline gap analysis (`references/inline-protocols.md §Phase 6`) → `docs/03-analysis/<feature>.analysis.md`. Parse match rate.
- **6b** — If match rate < 90%, inline iterate (`references/inline-protocols.md §Phase 6b`) — 5-cycle cap. After each cycle, re-run gap analysis. Loop until ≥90% AND 100% test pass. On cap exhaust: halt `step6:iterate_max_cycles`.

## Phase 7 sub-steps

- **7a** — `python3 ~/.claude/skills/h-mad/scripts/h_mad_telemetry.py record --feature <feature> --state docs/.bkit-memory.json --out .h-mad/telemetry.jsonl`. Non-fatal on failure.
- **7b** — Inline report (`references/inline-protocols.md §Phase 7 §Report`) → `docs/04-report/features/<feature>.report.md`.
- **7c** — Inline archive (`references/inline-protocols.md §Phase 7 §Archive`) → moves feature docs to `docs/archive/<YYYY-MM>/<feature>/`.
- **7d** — `git add -A && git commit -m "feat(<feature>): closure — report + archive"`.
- **7e** — `git push origin main`. Emit `[H-MAD] <feature> phase7 complete`.

## Cycle caps

| Cycle type | Cap | Halt reason on exhaust |
|---|---|---|
| Plan audit | 5 | `step3:audit_max_cycles` |
| Design audit | 5 | `step4:audit_max_cycles` |
| Impl-plan audit | 5 | `step5b:impl_plan_audit_max_cycles` |
| Codex GREEN retries | 3 | `step5e:green_unreachable:<module>` |
| Verification iterate | 5 | `step6:iterate_max_cycles` |

## Logger marker

All phase transitions emit a `[H-MAD]` marker via `h_mad_emit_marker.sh`:

```bash
bash ~/.claude/skills/h-mad/scripts/h_mad_emit_marker.sh "<feature>" "<N>" "<gate_passed|halted|complete>"
```

Pattern: `[H-MAD] <feature> phase<N> <decision>`
