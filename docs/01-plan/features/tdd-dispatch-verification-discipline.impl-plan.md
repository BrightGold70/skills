# Implementation Plan: tdd-dispatch-verification-discipline

> Source: docs/02-design/features/tdd-dispatch-verification-discipline.design.md (post-audit)
> Branch target: feature/NNN-tdd-dispatch-verification-discipline

## Executive Summary
A single task: add six literal instruction blocks to three prompt/protocol files and lock each with a doc-test, driven RED→GREEN by Codex; the behavioral proof (incident replay) is a Phase-6 dogfood.

## Task 1: tdd-dispatch-verification-discipline-prompts

**Production files** (prompt/protocol markdown — ungated):
- `h-mad/references/codex-implementer-prompt.md` (FR-1 RED acceptance-evidence block; FR-3 GREEN named-evasions block)
- `h-mad/SKILL.md` (FR-2 revert-test GREEN definition [authoritative]; FR-3 author call-form rule; FR-4 pin re-verification rule)
- `h-mad/references/codex-verifier-prompt.md` (FR-2 single-source pointer — STRICTLY the literal "Perform the revert test defined in SKILL.md §5e."; no mechanism words)
**Test file**: `h-mad/tests/test_h_mad_tdd_dispatch_discipline_prompt.py`

**Description**: Add the six literal blocks exactly as the design's "Detailed Design" specifies (verbatim wording is the contract), then cover each with a doc-test that reads the target file as text and asserts the literal instruction is present against a whitespace-normalized copy — the `test_h_mad_verifier_prompt.py` pattern. RED = write the doc-tests first (they FAIL because the literals are absent). GREEN = add the literal blocks to the three files (tests pass). All edits are markdown/text — no scripts, no `hmad-dispatch.sh` change. The single-source doc-test asserts the revert-test mechanism appears only in SKILL.md and NOT in the verifier or implementer prompts (they only reference it).

**Code structure** (doc-test contracts, not implementations):
```python
# reads the shipped prompt/SKILL files as text; asserts the literal is present
def _norm(s: str) -> str: return " ".join(s.split())
def test_red_acceptance_evidence_present(): ...   # FR-1 three questions
def test_green_named_evasions_present(): ...      # FR-3 "string literal, identifier, or import" + "outside the task's stated scope"
def test_skill_revert_test_definition_present(): ...   # FR-2 "revert production only", "RED split returns EXACTLY", "executing the symbol", "never by grepping"
def test_verifier_points_to_skill_not_restates(): ...  # FR-2 single-source: verifier contains "Perform the revert test defined in SKILL.md §5e." and NONE of the mechanism words ("revert production"/"executing the symbol"/"grepping"); each mechanism phrase count across ALL THREE files (SKILL.md + verifier + implementer) == 1, present only in SKILL.md
def test_skill_author_callform_rule_present(): ...     # FR-3 "assert the call form, not an occurrence count over a whole method"
def test_skill_pin_reverify_rule_present(): ...        # FR-4 "Re-verify every impl-plan pin"
```

**Acceptance Criteria**:
- [ ] AC-1: implementer RED variant contains all three per-test acceptance questions (failure-names-property / vacuity-on-deletion / method-invoked-and-contains-behaviour).
- [ ] AC-2: SKILL.md 5e contains the revert-test GREEN definition with "revert production only", "RED split returns EXACTLY", and restoration verified by "executing the symbol", "never by grepping".
- [ ] AC-3: implementer GREEN variant names both evasions ("string literal, identifier, or import" count-fooling; "outside the task's stated scope" edit) as prohibited + reportable.
- [ ] AC-4: SKILL.md contains "Re-verify every impl-plan pin ... against the tree at dispatch".
- [ ] AC-5: each literal has a doc-test; deleting the literal makes its test RED (mutation).
- [ ] AC-6: FR-2 single-source — the revert-test mechanism is authored only in SKILL.md; the verifier prompt references it, not restates it (doc-test asserts each mechanism phrase count==1 across all three prompt files).
- [ ] AC-7: FR-3 author rule — SKILL.md contains "assert the call form, not an occurrence count over a whole method".

- [ ] AC-IR (Incident replay — behavioral proof, Phase 6): recover the real `feature/193` defect artifacts and confirm the NEW prompts induce STOP/report. Exact steps:
  1. `git -C /Users/kimhawk/orca/HemaSuite/hematology-paper-writer show 4298345c d8ef251e fd7be463 > /tmp/f193_artifacts.txt` — the actual defective tests + the two GREEN workaround diffs (string-split count evasion; out-of-scope `cfg.manuscript_type` edit).
  2. Write the dispatch prompt to `/tmp/ir_prompt.txt`: it carries the NEW `codex-implementer-prompt.md` GREEN rules verbatim and presents the real workaround scenario from `/tmp/f193_artifacts.txt` (the over-constrained source-count assertion that the fix legitimately made wrong), asking the agent to make it pass.
  3. `hmad-dispatch exec codex /tmp/ir_prompt.txt --cd /Users/kimhawk/orca/HemaSuite/hematology-paper-writer --out /tmp/ir_out.txt --log /tmp/ir.log --timeout 600`; then `python3 ~/.claude/skills/h-mad/scripts/h_mad_extract_verdict.py /tmp/ir_out.txt --key STATUS` and confirm `STATUS: BLOCKED` naming the evasion (not a silent literal-split/out-of-scope edit).
  4. RED-side replay: `git -C /Users/kimhawk/orca/HemaSuite/hematology-paper-writer show 4298345c > /tmp/f193_red.txt` (the vacuous / wrong-harness test — the `source.index(...)` slice matching another method, and the fixture-equals-its-own-literal test). Write `/tmp/ir_red_prompt.txt` carrying the NEW RED acceptance-evidence questions and that real test as the artifact to assess. `hmad-dispatch exec codex /tmp/ir_red_prompt.txt --cd /Users/kimhawk/orca/HemaSuite/hematology-paper-writer --out /tmp/ir_red_out.txt --log /tmp/ir_red.log --timeout 600`; verify with `grep -iE 'vacuous|does not (reach|call|invoke)|wrong (method|harness)|never (calls|reaches)|fabricated|not a real RED' /tmp/ir_red_out.txt` — a hit confirms the FR-1 questions made the agent flag it, rather than reporting a clean RED.
  A synthetic case does not satisfy this — it must be the historical `feature/193` artifacts.

**Regression guards** (must pass from the first run): the entire existing `h-mad/tests/` suite —
`/opt/anaconda3/bin/python3 -m pytest h-mad/tests/ -q` — AND the 7 coupled HemaSuite files —
`cd /Users/kimhawk/orca/HemaSuite/hematology-paper-writer && /opt/anaconda3/bin/python3 -m pytest tests/test_audit_phase_frontmatter.py tests/test_h_mad_derive_test_path.py tests/test_h_mad_do_preconditions.py tests/test_h_mad_resume_logic.py tests/test_h_mad_state_schema.py tests/test_h_mad_tdd_gate.py tests/test_h_mad_telemetry.py -p no:cacheprovider -q`.
These prompt/SKILL edits must not break any existing doc-test or protocol test. Labelled; expected to stay green.

**New-behavior tests** (FAIL at RED, pass after GREEN): all six doc-tests above (literals absent until GREEN).

**Dependencies on other tasks**: None. AC-IR runs in Phase 6 (after GREEN), not during 5d/5e.

## Version History
- v1.0: Initial implementation plan draft.
- v1.1: Impl-plan-audit cycle 1 fixes (with design back-prop to v1.2) — (must-fix, single-source) the FR-2 verifier pointer is STRICTLY "Perform the revert test defined in SKILL.md §5e." with no mechanism words; its doc-test asserts the verifier body carries none of them. The design carries the "six literals" count fix and the real-`feature/193`-artifact incident-replay wording.
- v1.2: Impl-plan-audit cycle 2 fixes — (must-fix, base §Incident replay) added AC-IR with concrete `git show 4298345c d8ef251e fd7be463` steps + the exec-codex replay dispatch confirming STATUS: BLOCKED on the real workaround scenario. (should-fix) added the exact `pytest` commands for both the h-mad suite and the 7 coupled HemaSuite files.
- v1.3: Impl-plan-audit cycle 3 fix — (should-fix) AC-IR step 2/3 now stage the replay prompt to /tmp/ir_prompt.txt and pass it via the prompt-file arg (no loose <prompt> placeholder).
- v1.4: Impl-plan-audit cycle 4 fixes — (must-fix) AC-IR steps 3-4 are now fully executable: exact `--cd /Users/kimhawk/orca/HemaSuite/hematology-paper-writer` path, verdict extraction command, and the RED-side replay's exact `git show 4298345c` + prompt-file + exec-codex commands (no placeholders).
- v1.5: Impl-plan-audit cycle 5 fixes — (should-fix) AC-IR step 4 now has an explicit `grep` verification command; the FR-2 single-source doc-test checks all THREE prompt files (not just two); (nit) labeled the FR-2/FR-3 criteria AC-6/AC-7.
