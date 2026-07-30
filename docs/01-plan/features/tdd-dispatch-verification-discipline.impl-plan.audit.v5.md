## Summary
The implementation plan is exceptionally thorough and rigorous, providing exact file paths, verbatim string literals, and explicit executable commands for both regression testing and the Phase-6 incident replay. It adheres strictly to the single-source contract and correctly scopes its doc-tests to verify the exact mutations applied. There are no invariant violations.

## Must-fix
None

## Should-fix
- In AC-IR Step 4 (RED-side replay), the verification step ("confirm the reply flags the test as vacuous...") does not provide an explicit validation command, whereas Step 3 provides a precise script invocation (`h_mad_extract_verdict.py`). Specify how to verify the RED-side output (e.g., `cat /tmp/ir_red_out.txt` for manual visual confirmation, or a specific `grep` command).
- The FR-2 single-source doc-test (`test_verifier_points_to_skill_not_restates`) asserts mechanism phrase counts across "both files" (`SKILL.md` and `codex-verifier-prompt.md`). To fully secure the single-source invariant, the test should also assert that the mechanism phrases are absent from `codex-implementer-prompt.md` (checking across all three files).

## Nit
- In the Acceptance Criteria list, the FR-2 single-source and FR-3 author rule items lack the "AC-X:" prefix used by the other items. Labeling them consistently (e.g., AC-6 and AC-7) would improve clarity.
