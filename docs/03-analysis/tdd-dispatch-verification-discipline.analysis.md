# Gap Analysis: tdd-dispatch-verification-discipline

**Phase 6a — design-vs-implementation gap analysis.**
Base 5c `d69d933` · Head `0f59a80` (+6a-prime nit) · Branch `feature/212-tdd-dispatch-verification-discipline`.

## Match rate: 100% · Test pass: 100% · 6a-prime: READY_TO_MERGE · AC-IR: PROVEN

Every AC maps to a passing, mutation-verified doc-test, and the behavioral proof (incident replay against the real `feature/193` artifacts) confirms the prompts induce the intended STOP/report.

| AC | Requirement | Evidence |
|---|---|---|
| AC-1 | RED per-test acceptance evidence in implementer prompt | `test_red_acceptance_evidence_present` green |
| AC-2 | revert-test GREEN definition in SKILL.md (execute-to-restore, not grep) | `test_skill_revert_test_definition_present` green |
| AC-3 | two named evasions in implementer GREEN | `test_green_named_evasions_present` green |
| AC-4 | re-verify impl-plan pins rule in SKILL.md | `test_skill_pin_reverify_rule_present` green |
| AC-5 | each literal doc-tested; delete → RED | mutation: every literal deletion → its test RED; restore → 6 green |
| AC-6 (single-source) | FR-2 mechanism only in SKILL.md; verifier a pure pointer | `test_verifier_points_to_skill_not_restates` — specific-literal absence in verifier+implementer (not a global count) |
| AC-7 | author call-form rule in SKILL.md | `test_skill_author_callform_rule_present` green |
| AC-6 (suites) | both coupled suites 100% | h-mad 760/0 · HemaSuite coupled 54/0 |
| AC-IR | incident replay vs real `feature/193` | **GREEN-side** codex returned `STATUS: BLOCKED` refusing the literal-split count evasion; **RED-side** codex flagged the fixture-equals-its-own-literal test as vacuous and named no method invoked |

## 6a-prime — the feature caught its own build (dogfood)
`ASSESSMENT: READY_TO_MERGE` after a WITH_FIXES round that found the single-source doc-test's `count("grepping")==1` over-constrained SKILL.md (which legitimately uses "grepping" in unrelated §5e/§6a-prime prose), which had recruited the GREEN implementer into mutating two unrelated sentences ("grepping"→"matching"/"searching") — **the exact out-of-scope evasion FR-3 prohibits**. Fixed by asserting the specific FR-2 mechanism literals' absence (the call form) instead of a global token count, and reverting the collateral edits. The feature demonstrated its own value by catching the evasion its own doc-test provoked.

## Gaps
None. No open must-fix/should-fix; both replays pass; both suites green; single-source enforced by a discriminating test.

## Version History
- v1.0: Phase 6a gap analysis — 100% match, both suites green, 6a-prime READY_TO_MERGE, AC-IR incident replay proven both directions.
