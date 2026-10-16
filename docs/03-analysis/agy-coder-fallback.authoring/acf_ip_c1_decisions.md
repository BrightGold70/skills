# agy-coder-fallback — impl-plan audit cycle 1 decision sheet (orchestrator)
Reports: docs/01-plan/features/agy-coder-fallback.impl-plan.audit.v1.p1.md (codex: 9 must, 3 should), .v1.p2.md (agy: 2 must, 2 should). Audited impl-plan v1.0 @fc6b497e.
Classification (set before reading): build = changes code/tests 5d/5e write; measurement = a published count/stamp only. Reviewers' tags accepted. Codex findings cite executed controlled pairs; the author re-verifies each premise anyway and declines with evidence if one fails.
Overlap: Task 3 post-GREEN re-run of probes/fr3_state_line_grammar.py prints PROBE: FAIL after the grammar change (codex #1 + agy #1) — update the probe (or its expected result) as part of Task 3.
Answer EVERY must and should in both reports. Close the class where one is visible:
- every documented command's path is valid from its stated cwd (codex #2 anchor-check path);
- every normal FAIL verdict in any new/changed script exits 0 with its token (codex #3, Task 5 self-check);
- every new halt has an [H-MAD] marker at the transition (codex #8);
- every RED split derives from what is actually absent at RED (codex #6 Task 20, codex Task 22 two timeout tests);
- every wiring task has BOTH mutation directions (codex #7 Task 10);
- every Task that edits a mutation-anchored line lists the re-anchor (agy CX-FOLD in Task 4) — sweep all 23 Tasks with --check-anchors logic, not only Task 4;
- spec FR-9 requirements for codex-implementer-prompt.md all appear in Task 15 (agy #2: opening line names "the Phase-5 implementer", Hook: line includes grok, …) — re-read FR-9 whole against Task 15.
OPERATOR DECISION OD-2 (2026-10-16): a class-(b) target naming a directory ('.', 'src/', any existing directory) is REFUSED with kind=judge-error under S={active, unknown} and allowed under inactive. Codex observed canonicalise(root, ".", root) → unresolvable=False, names=() which under T6 would ALLOW — so Task 6 must add an explicit directory check (and fixtures: '.', 'src/' under active/unknown/inactive) plus its mutation row. Close OD-2 in the plan; note the design/spec owe a line recording it (report it as owed; do not edit them).
OD-1 (operator): option (A) — transcription test over written procedure — confirmed; close OD-1.
Measurement (agy should #2, Task 9 hook_wiring.json is 12 rows not 10): fix the count (cheap) — state what the 10 counts (rows over scripts/h_mad_hook_wiring.py) vs 12 total.
