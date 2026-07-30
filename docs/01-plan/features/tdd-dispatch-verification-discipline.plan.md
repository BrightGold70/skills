# Plan: tdd-dispatch-verification-discipline

## Executive Summary
Add a RED-side acceptance gate, a revert-test definition of GREEN, and two named anti-evasion rules to the h-mad Codex prompts + SKILL.md 5d/5e protocol — all prompt/protocol text, no new scripts — and lock the new report-format literals with doc-tests across both coupled suites.

## Overview
On HemaSuite `feature/193`, six Codex-authored RED tests were defective and two GREEN dispatches worked around the tests instead of reporting the conflict; the existing 5e anti-gaming step missed all of it because it runs *after* GREEN and only asks whether a test *can* fail. This feature closes the RED-side and GREEN-definition gaps with prompt/protocol changes. It matters now because 5d/5e is the primary path every H-MAD feature runs through, and the defect shape ("assert against the assumed shape, not the code in front of you") is author-general, not Codex-specific.

## Scope
`h-mad/references/codex-implementer-prompt.md` (RED variant for FR-1, GREEN variant for FR-3), `h-mad/references/codex-verifier-prompt.md` (the 5e anti-gaming verifier — gets a one-line **reference** to the revert test, "perform the revert test defined in SKILL.md §5e; verify restoration by executing the symbol, not grepping": a pointer, not a restatement), `h-mad/SKILL.md` (Phase 5d/5e protocol: the **authoritative** FR-2 revert-test GREEN definition incl. execute-to-restore, plus FR-3 reciprocal author rule and FR-4 pin-verification guidance), and `h-mad/tests/` (doc-tests for the new report-format literals). No new scripts. **Single-source contract:** each FR has exactly ONE authoritative surface — FR-1 in the implementer RED variant, FR-2's full definition in SKILL.md §5e (the verifier-prompt only points at it, so there is no rule to diverge) — never a duplicated rule across files. No behavioral change to `hmad-dispatch.sh`.

## Goals
- Make a RED dispatch report per-test evidence: for each FAILING test, the failure message names the property under test; **for each PASSING test, would it still pass if the behaviour it names were deleted? (if yes, it is vacuous)**; and **name the method actually invoked and confirm it is the one that contains the behaviour under test** (defect-A mitigation) — FR-1, in `codex-implementer-prompt.md` RED variant only.
- Redefine GREEN as the revert test (revert production → RED returns exactly → restore → green returns), restoration verified by executing the symbol not grepping — FR-2.
- Name the two observed evasions — **do not restructure a string literal, identifier, or import to change how a source-level assertion counts it; do not modify code outside the task's stated scope to satisfy a counting assertion** — as prohibited + reportable in `codex-implementer-prompt.md` GREEN, and add the reciprocal author rule (assert the call form, not an occurrence count over a whole method) as **prompt-authoring guidance in `SKILL.md`** (§"Audit prompt assembly"/prompt-authoring, beside FR-4) — FR-3.
- Require re-verifying every impl-plan pin (line#/site-count/live-defect claim) against the tree at dispatch time — FR-4.
- Lock the new report-format requirements with doc-tests — AC-5; both suites green — AC-6.

## Requirements
- FR-1: RED-side acceptance gate (codex-implementer-prompt.md RED variant + report format).
- FR-2: revert-test GREEN definition (SKILL.md 5e), restoration by execution.
- FR-3: named evasions prohibited/reportable (codex-implementer-prompt.md GREEN variant) + author rule.
- FR-4: prompt-authoring rule — re-verify plan pins against the tree.

## Implementation Strategy
Edit the prompt/protocol files in place, following their existing structure: `codex-implementer-prompt.md` already has "For RED phase (5d)" and "For GREEN phase (5e)" sections plus a "Self-Review" checklist and a "Report Format" block — FR-1 extends the RED report contract + self-review, FR-3 extends the GREEN "STOP and report" rule. `codex-verifier-prompt.md` gets a one-line pointer to the revert test ("perform the revert test defined in SKILL.md §5e; verify restoration by executing the symbol, not grepping") beside its existing anti-gaming audit — a reference, not a restatement, so the authoritative definition lives only in SKILL.md. FR-1 is NOT applied here (it belongs to the implementer RED variant alone). `SKILL.md` Phase 5e already runs the anti-gaming verify — FR-2 adds the revert-test as the GREEN *definition* (an orchestrator step, before the anti-gaming pass), and FR-3's reciprocal author rule + FR-4 land as prompt-authoring guidance near §"Audit prompt assembly" / the 5a impl-plan step. Each new instruction is a literal sentence the doc-tests can anchor on (the pattern `test_h_mad_verifier_prompt.py` established: assert the literal instruction string against a whitespace-normalized copy, mutation-verified). No script gains logic; the discipline lives in the prompts the agents read and the protocol the orchestrator follows.

## Architecture Considerations
- **These are prompt/protocol contracts, not code** — a doc-test asserting the literal instruction is present and wired (as the 5e verifier template was tested) is **necessary but not sufficient**. It proves the text exists, not that the prompt *induces the behavior*. Per base §Incident replay, the fix must also be replayed against the artifacts that motivated it: dispatch the new prompts against a reconstruction of the `feature/193` defects and confirm the agent now STOPs/reports rather than evades. That behavioral proof is a Phase-6 dogfood, alongside the doc-tests.
- **Symlink coupling** — `~/.claude/skills/h-mad` is a symlink into this repo; ~5 HemaSuite `test_h_mad_*` tests reach these files by path, so both suites are the acceptance boundary (AC-6). Edits during an in-flight run go through a worktree.
- **FR-2's revert test is heavier than the current single-guard mutation** — it reverts *all* production for the module and confirms the RED split returns exactly, then restores by executing the symbol (defeating the stale-`.pyc` trap, defect D). It is the strongest discrimination check; the protocol should place it as the GREEN gate, not replace the anti-gaming verify.
- **FR-4 partially overlaps** invariants.base.md §Assumption/Mutation verification, but applies specifically to impl-plan *pins at dispatch time* — a sharper, dispatch-point application, not a duplicate rule.

## Assumption verification (evidence, 2026-07-31)
Throwaway probes of the load-bearing structural claims (base §Assumption verification):
```
$ grep -nE 'For RED phase|For GREEN phase|Self-Review|Report Format' h-mad/references/codex-implementer-prompt.md
  37: For RED phase (5d): …          41: For GREEN phase (5e): …
  70: ## Before Reporting Back: Self-Review     79: ## Report Format (REQUIRED …)
$ ls h-mad/tests/test_h_mad_verifier_prompt.py            → exists (9 literal/assert lines — the doc-test pattern)
$ ls -ld ~/.claude/skills/h-mad                           → symlink → /Users/kimhawk/orca/skills/h-mad
$ ls HemaSuite/…/tests/test_h_mad_*.py test_audit_phase_frontmatter.py | wc -l → 7 files (54 tests) reach the skill by path
```
Confirms: the implementer prompt has the RED/GREEN/Self-Review/Report-Format sections FR-1/FR-3 extend; the verifier doc-test pattern exists to copy for AC-5; and the symlink couples **7** HemaSuite test files (the spec's "~5" is an undercount — AC-6 must run all 7).

## Deliverables
| Deliverable | Type | Satisfies |
|---|---|---|
| RED-variant per-test acceptance questions + report-format additions | prompt text | FR-1, AC-1 |
| SKILL.md 5e revert-test GREEN definition (execute-to-restore) — **authoritative** | protocol text | FR-2, AC-2 |
| `codex-verifier-prompt.md` one-line **pointer** to SKILL.md §5e's revert test (reference, not restatement) | prompt text | FR-2 (single-source) |
| GREEN-variant named evasions (prohibited/reportable) + author call-form rule | prompt text | FR-3, AC-3 |
| Prompt-authoring rule: re-verify plan pins against the tree | protocol text | FR-4, AC-4 |
| Doc-tests for the new report-format literals | tests | AC-5 |
| **Incident replay**: dispatch the NEW RED/GREEN prompts against a reconstruction of the `feature/193` defects (`4298345c`/`d8ef251e`/`fd7be463`) and confirm the agent now STOPs-and-reports the evasion / names the vacuous test — behavioral proof, not literal presence | validation (Phase 6 dogfood) | FR-1/FR-3, base §Incident replay |
| Both-suite green run | verification | AC-6 |

## Risks and Mitigation
| Risk | Impact | Mitigation |
|---|---|---|
| Doc-test asserts a paraphrase, not the literal → passes with the guidance deleted | vacuous test | anchor each doc-test on the literal instruction string against a whitespace-normalized copy; mutation-test by deleting the sentence |
| FR-1 RED report bloats the dispatch prompt / agent skips it | ignored gate | keep the per-test questions terse and make them a required report line, not prose; doc-test asserts the requirement text is present |
| FR-2 revert-test wording ambiguous → agent greps to "restore" (defect D) | false verification | wording must say "verify restoration by executing the symbol, never by grepping the source"; doc-test anchors that literal |
| Symlink edit breaks HemaSuite mid-run | unrelated suite red | run both suites before merge; worktree if a run is live |
| Overlap with existing 5e verifier confuses the protocol | double gate | FR-2 is the GREEN definition *before* the anti-gaming pass; SKILL.md states the order explicitly |

## Convention Prerequisites
- Feature branch `feature/NNN-tdd-dispatch-verification-discipline` off `main` (Phase 5c).
- Prompt/protocol + test files only; no production `.py`, so the Phase-5 Codex-authors gate applies only to the doc-test file (test paths are ungated) — Claude may author the prompt/SKILL text (markdown, ungated), Codex authors the doc-tests RED+GREEN.
- No new external dependency.

## Success Criteria
- All 6 spec ACs met; each new instruction is a literal, doc-tested, mutation-verified string.
- Both coupled suites 100%.
- **Incident replay passes**: the new prompts, dispatched against a reconstruction of the `feature/193` defects, induce the agent to STOP-and-report the string-restructuring / out-of-scope-edit evasion and to flag the vacuous/wrong-harness RED test — proving behavioral effect, not just literal presence.

## Out-of-Scope (confirmed from spec)
- Not a rewrite of the 5e anti-gaming step.
- Not automation — no new scripts.
- No `hmad-dispatch.sh` behavior change.

## Next Steps
User approves v1.0 → auto-cycle plan audit via agy → gate to must-fix=0 AND should-fix=0 → Phase 4 design.

## Version History
- v1.0: Initial plan draft.
- v1.1: Plan-audit cycle 1 fix — (must-fix, base §Incident replay) added an incident-replay validation: the new prompts must be dispatched against a reconstruction of the `feature/193` defects to prove behavioral effect (STOP/report), not just literal presence via doc-tests.
- v1.2: Plan-audit cycle 2 fix — (must-fix, base §Assumption verification) added an evidence block citing the probes for the implementer-prompt sections, the verifier doc-test pattern, and the symlink coupling (corrected ~5 → 7 HemaSuite test files).
- v1.3: Plan-audit cycle 3 fixes — (must-fix) restored `codex-verifier-prompt.md` as a target; (must-fix) FR-1 now requires confirming the invoked method contains the behaviour under test (defect-A mitigation); (must-fix) FR-3's reciprocal author rule explicitly lands in `SKILL.md` prompt-authoring guidance.
- v1.4: Plan-audit cycle 4 fixes (resolving a c3↔c4 oscillation by the spec's intent) — (must-fix, single-source) `codex-verifier-prompt.md` now receives **FR-2** (revert-test / execute-to-restore, defect D), NOT a duplicated FR-1; FR-1 stays in the implementer RED variant only. (must-fix, Axis C) restored the full spec wording for FR-1's vacuity check ("would it still pass if the behaviour it names were deleted?") and FR-3's evasion list ("string literal, identifier, or import").
- v1.5: Plan-audit cycle 5 fixes — (must-fix, single-source) FR-2's authoritative definition lives ONLY in SKILL.md §5e; `codex-verifier-prompt.md` gets a one-line **pointer** to it (reference, not restatement), so no rule is duplicated across files. (must-fix, Axis A) added the verifier-prompt pointer as its own deliverables row, resolving the scope-vs-deliverables contradiction. Closes the c3–c5 verifier-target oscillation.
