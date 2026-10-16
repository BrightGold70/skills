# agy-coder-fallback — impl-plan audit cycle 2 decision sheet — FINAL CORRECTIVE REVISION
Round cap (2) reached. Not re-audited: fix ONLY what is listed; mechanically checkable; no new scope; anything new → OPEN-DECISION on its Task (resolved in 5d) only if an implementation that satisfies it can be named, otherwise fix it.
Reports: docs/01-plan/features/agy-coder-fallback.impl-plan.audit.v2.p1.md (codex: 4 must, 1 should; controlled executions), .v2.p2.md (agy: clean). Audited impl-plan v1.1 @fc92becf.

IMPL-PLAN (implplan-author):
I1 Task 6 key-presence mutant survives its killer after OD-2 → pick a fixture that distinguishes value-guard vs key-presence (e.g. a non-str truthy value or a key present with a valid in-root target vs absent), or replace the row with one that bites; prove it by the stated controlled pair.
I2 Task 20 captured run_command test cannot verify the workdir key → assert on an observable that differs when the captured workdir key ≠ Cwd (e.g. a command the shared policy allows only under root vs outside, or assert the reader's parsed cwd directly).
I3 Task 9 budget-to-floor connection unenforced (59/60 fixtures identical for formula vs hardcoded 60) → add a fixture that changes the budget source (monkeypatch JUDGE_BUDGET_S) and asserts the floor moves; add the converse mutation.
I4 ORCHESTRATOR DECISION: Task 4 FIXES the pre-existing Codex gate --self-check shell-policy FAIL to print its token on stdout and exit 0 (base invariant, same file Task 4 already edits). Add RED/GREEN counts and a mutation row; update any existing test that pins exit 2 for that verdict (regression provenance: it pinned the defect — say so). Remove the "residual, not changed" text.
I5 (should) Task 20 suite assertions must not read docs/03-analysis/probes (archivable) → put the captured record under h-mad/tests/fixtures/ (or similar), as Task 22 does.

SPEC (spec-author) — owed lines from impl-plan v1.1 report:
P1 record OD-2 (operator, 2026-10-16) as a decision: a class-(b) directory target is refused (kind=judge-error) under S={active,unknown}, allowed under inactive; residual: a trailing-'/' path naming no existing directory.
P2 FR-2: name the halts — step5:implementer_unresolved, step5:implementer_invalid (and step5:implementer_switch_unrecorded) — or state the plan's names are adopted.
P3 FR-4/FR-5 self-check: a normal FAIL verdict prints its token and exits 0 (orchestrator decision, also applied to the Codex gate's pre-existing self-check in Task 4).
P4 FR-9 Hook-line list: add Claude's h-mad-tdd-gate.sh (pinned by test_hook_line_names_both_gates).
DESIGN (design-author) — owed lines:
Q1 OD-2 (as P1) in FR-4 T-sequence: a T2a directory check before T6.
Q2 FR-4 --self-check: normal FAIL exits 0 (replace "a nonzero exit"); note the Codex gate's self-check is corrected in Task 4.
Q3 FR-2 halt names as P2.
