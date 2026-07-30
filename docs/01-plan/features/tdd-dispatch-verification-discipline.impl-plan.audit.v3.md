## Summary
The implementation plan and design are detailed and well-structured, successfully anchoring the six new instruction blocks with specific doc-tests and strictly adhering to the single-source contract for the FR-2 revert-test mechanism. The Phase 6 incident replay procedure provides strong behavioral proof by leveraging the real `feature/193` artifacts. However, a claimed assumption verification citation is missing entirely from the text, violating a base invariant.

## Must-fix
- Missing assumption citation — The design claims under the Invariant Compliance section that the "prompt-section/symlink assumptions were probed and cited in the plan (v1.2)". However, no such citation or observed output exists anywhere in the plan. This violates the Axis B `Assumption verification` invariant, which explicitly requires that "the design cites the observed output" of throwaway commands used to verify load-bearing assumptions, and states that the evidence belongs in the document itself.

## Should-fix
- Vague prompt staging in AC-IR — Step 3 specifies `hmad-dispatch exec codex <prompt> ...`, leaving `<prompt>` as a loose placeholder. The plan should specify exactly how the prompt payload is constructed and passed (e.g., via a specific file and the `--prompt-file` flag) to prevent ambiguity and ensure consistent execution during the Phase 6 dogfooding.

## Nit
None
