# Design: tdd-dispatch-verification-discipline

## Executive Summary
Insert six concrete literal blocks across three prompt/protocol files — a RED-side per-test acceptance gate, a revert-test GREEN definition, a single-source pointer to it from the verifier, two named evasions, an author call-form rule, and a pin re-verification rule — each anchored by a doc-test on its literal string, plus a Phase-6 incident replay against the `feature/193` defects.

## Overview
Prompt/protocol text only; no scripts, no `hmad-dispatch.sh` change. Each FR lands in exactly one authoritative surface (single-source); the verifier prompt only *points* at SKILL.md §5e for the revert test. Every added instruction is a fixed sentence so `test_h_mad_*_prompt.py` can assert it is present and wired, mutation-verified by deleting the sentence.

## Architecture Overview
```
codex-implementer-prompt.md
  ├─ RED variant  → FR-1: three per-test acceptance questions, added to the report format
  └─ GREEN variant→ FR-3: two named evasions, prohibited + reportable
SKILL.md Phase 5e
  ├─ FR-2 (authoritative): revert-test = definition of GREEN; restore verified by executing the symbol
  ├─ FR-3 reciprocal author rule: assert the call form, not an occurrence count over a method
  └─ FR-4: re-verify every impl-plan pin (line#/site-count/live-defect) against the tree at dispatch
codex-verifier-prompt.md
  └─ FR-2 pointer (single-source, reference only — mechanism defined solely in SKILL.md §5e)
h-mad/tests/test_h_mad_tdd_dispatch_discipline_prompt.py
  └─ doc-tests: each literal present + wired; mutation = delete the sentence → RED
Phase 6 incident replay
  └─ dispatch the new prompts against the feature/193 defect reconstruction → agent STOPs/reports
```

## Detailed Design

### FR-1 — RED-side acceptance gate (codex-implementer-prompt.md, RED variant + Report Format)
Add a required report block after the RED "Your Job" / "Report Format":
> **RED acceptance evidence (required — one line per test):**
> 1. For each FAILING test: does the failure message name the property under test? (An `ImportError`/`AttributeError` standing in for a behavioural assertion is not a RED — it is an unwritten test.)
> 2. For each PASSING test: would it still pass if the behaviour it names were deleted? If yes, it is vacuous — fix or remove it.
> 3. For each behavioural test: name the method actually invoked, and confirm it is the one that contains the behaviour under test.
> A RED report that omits these answers is incomplete and will be re-dispatched.

### FR-2 — revert test as the definition of GREEN (SKILL.md Phase 5e, authoritative)
Add before the anti-gaming verify step:
> **GREEN is established by the revert test, not by "tests pass".** For the module: revert production only (tests untouched) → confirm the RED split returns EXACTLY (the same tests fail) → restore production → confirm green returns. **Verify restoration by executing the symbol** (import it / run the test), **never by grepping the source** — a field-reorder or same-mtime-second `cp` leaves stale `.pyc` bytecode running while the source reads restored. Reading a diff cannot establish this. Only then run the anti-gaming verify.

### FR-2 pointer (codex-verifier-prompt.md, reference only)
Add one line to the verifier's verification section — a **pure reference**, with the entire mechanism (including the execute-to-restore / not-grepping clause) defined only in SKILL.md §5e:
> Perform the revert test defined in SKILL.md §5e.

No part of the rule is restated here — SKILL.md §5e is the single source, so the two files cannot diverge.

### FR-3 — over-constraint is a reportable conflict (codex-implementer-prompt.md, GREEN variant)
Strengthen the existing "if a test looks wrong, STOP and report" with:
> Two evasions are **prohibited and must be reported instead of performed**:
> - do not restructure a string literal, identifier, or import to change how a source-level assertion counts it;
> - do not modify code outside the task's stated scope to satisfy a counting assertion.
> If either would be needed to make a test pass, the assertion is wrong → STOP and report `STATUS: BLOCKED` naming it.

### FR-3 reciprocal author rule (SKILL.md, prompt-authoring guidance)
> **When authoring a source-level assertion, assert the call form, not an occurrence count over a whole method.** A count over a method policing one call site over-constrains it and recruits the implementer into damaging unrelated code; assert the specific call/argument shape at the one site the contract concerns.

### FR-4 — re-verify plan pins against the tree (SKILL.md, prompt-authoring guidance / 5a)
> **Re-verify every impl-plan pin against the tree at dispatch time.** Every line number, site count, and "live defect" claim must be confirmed against the current tree before it is passed to an implementer — a stale pin produces a wrong edit or a fabricated failure (measured on `feature/193`: `:1583`→`:1575`, "three log sites"→two, "live defect"→already-citable).

## Components Changed / Added
| Component | File path | Change | Satisfies |
|---|---|---|---|
| RED acceptance-evidence block | `h-mad/references/codex-implementer-prompt.md` | modify | FR-1, AC-1 |
| Named-evasions STOP rule | `h-mad/references/codex-implementer-prompt.md` | modify | FR-3, AC-3 |
| Revert-test GREEN definition + author rule + pin rule | `h-mad/SKILL.md` | modify | FR-2/FR-3/FR-4, AC-2/AC-4 |
| Revert-test pointer | `h-mad/references/codex-verifier-prompt.md` | modify | FR-2 single-source |
| Doc-tests for the six literal blocks | `h-mad/tests/test_h_mad_tdd_dispatch_discipline_prompt.py` | new | AC-5 |

## Implementation Order
1. codex-implementer-prompt.md (FR-1 RED block, FR-3 GREEN evasions).
2. SKILL.md (FR-2 revert-test authoritative, FR-3 author rule, FR-4 pin rule).
3. codex-verifier-prompt.md (FR-2 pointer).
4. Doc-tests anchoring each literal (AC-5).
5. Phase-6 incident replay against feature/193 (behavioral proof).

## Data Model / Schema Changes
None.

## API / Interface Changes
None — prompt/protocol text only; no flags, no scripts, no `hmad-dispatch.sh` behavior change.

## Error Handling Strategy
N/A (no code paths). The "failure mode" is a doc-test going RED if a literal is missing; the gate for the behavior is the Phase-6 incident replay.

## Test Strategy
Doc-tests import each prompt/SKILL file as text and assert the literal instruction is present against a whitespace-normalized copy (the `test_h_mad_verifier_prompt.py` pattern). Mutation: delete each sentence → the matching doc-test goes RED (proves discrimination). Behavioral proof is the Phase-6 replay, not a unit test.

## Test Plan
`h-mad/tests/test_h_mad_tdd_dispatch_discipline_prompt.py` (verify: `/opt/anaconda3/bin/python3 -m pytest h-mad/tests/ -q`):
- FR-1: implementer RED text contains the three per-test questions (property-named / vacuity / method-invoked) — AC-1.
- FR-2: SKILL.md 5e contains "revert production only", "RED split returns EXACTLY", "executing the symbol", "never by grepping" — AC-2.
- FR-2 pointer: verifier prompt contains exactly "Perform the revert test defined in SKILL.md §5e." and does NOT contain the mechanism words ("revert production", "executing the symbol", "grepping") — those live only in SKILL.md (single-source: assert each mechanism phrase count is 1 across the two files, and the verifier body carries none of them).
- FR-3: implementer GREEN names both evasions ("string literal, identifier, or import"; "outside the task's stated scope") — AC-3.
- FR-3 author rule: SKILL.md contains "assert the call form, not an occurrence count over a whole method".
- FR-4: SKILL.md contains "Re-verify every impl-plan pin" — AC-4.
- Mutation: delete each literal → its test RED (AC-5 discrimination).
- Full skills suite + all 7 coupled HemaSuite files — AC-6.
- Phase-6 incident replay against the **real** `feature/193` artifacts (not a synthetic case): recover the actual defective test + the workaround diff from the historical commits (`git -C <HemaSuite> show 4298345c d8ef251e fd7be463`), present that exact code to a dispatch carrying the new prompts, and confirm the agent now STOPs/reports the string-restructuring evasion and flags the vacuous/wrong-harness test.

## Invariant Compliance
- **Skill self-containment** (Axis B): complies — edits inside the skill dir, no cross-skill import, no new dependency.
- **Skill manifest integrity** (Axis B): complies — no SKILL.md frontmatter change; the edits are protocol body text.
- **Base — single-source contract**: FR-2's definition lives only in SKILL.md §5e; the verifier prompt points at it. A doc-test asserts the mechanism is not restated in both.
- **Base — Incident replay**: the Phase-6 replay against `feature/193` is the behavioral proof; doc-tests alone are necessary-not-sufficient.
- **Base — Assumption verification** (probes, 2026-07-31, cited here):
  ```
  $ grep -nE 'For RED phase|For GREEN phase|Self-Review|Report Format' h-mad/references/codex-implementer-prompt.md
    37: For RED phase (5d)…   41: For GREEN phase (5e)…   70: ## Before Reporting Back: Self-Review   79: ## Report Format
  $ ls h-mad/tests/test_h_mad_verifier_prompt.py            → exists (the doc-test literal-assertion pattern to copy)
  $ ls -ld ~/.claude/skills/h-mad                           → symlink → /Users/kimhawk/orca/skills/h-mad
  $ ls HemaSuite/…/tests/test_h_mad_*.py test_audit_phase_frontmatter.py | wc -l → 7 coupled files
  ```
  Confirms the implementer prompt has the RED/GREEN/Self-Review/Report-Format sections FR-1/FR-3 extend, the verifier doc-test pattern exists for AC-5, and the symlink couples 7 HemaSuite test files (AC-6).
- **Base — no new dependency / mutation discipline**: text only; each guard (doc-test) mutation-verified.

## Version History
- v1.0: Initial design draft.
- v1.1: Design-audit cycle 1 fix — (must-fix, single-source) removed the parenthetical mechanism restatement from the FR-2 verifier pointer; it is now a pure reference to SKILL.md §5e, matching plan v1.5 and the design's own Test Plan.
- v1.2: Impl-plan-audit cycle 1 back-prop — (must-fix, single-source) the FR-2 pointer is now STRICTLY "Perform the revert test defined in SKILL.md §5e." with the execute-to-restore/not-grepping clause removed (it lives only in SKILL.md); the doc-test asserts the verifier body carries none of the mechanism words. (should-fix) Components table "five"→"six" literals. (should-fix) incident replay now runs against the REAL `feature/193` commit artifacts (`git show`), not a synthetic case.
- v1.3: Impl-plan-audit cycle 3 fix — (must-fix, base §Assumption verification) inlined the actual probe output into the design's Invariant Compliance section instead of pointing at the plan (the impl-plan audit cannot see the plan).
