AUDIT-pin-agents-tail-banner-impl-plan-v22-BEGIN
## Summary
The core implementation and mutation plan is coherent, and the stated 290-test baseline, 40-node RED table, and 27-mutation count all re-derive correctly. One base-invariant blocker remains in the newly isolated live-check procedure, with two lesser cross-document/test-precision gaps.

## Must-fix
- The isolated live check verifies a no-op as though it were a mutation — `HMAD_ORCA_PIN_FILE="$(mktemp -d)/orca-pins.env"` names a fresh, absent file, after which `pin-agents --clear` runs `rm -f` and the plan treats the file's continued absence as proof that clearing landed. The same observation holds if the clear path is broken or never runs, so this violates Mutation verification; either seed the isolated file with known dummy pins and prove they are removed, or omit the redundant clear and describe the fresh absent path as a precondition rather than a verified mutation.

## Should-fix
- The isolation fix was applied only to the impl-plan — the source plan's Success Criteria and paired design v1.17 still direct the operator to run `pin-agents --clear` against the ambient pin file, while the impl-plan says all three documents require the isolated path. Back-propagate the safe procedure so following either declared source cannot erase live operator pins; also update the impl-plan's stale header citation from design v1.16 to v1.17.
- `test_os_evidence_pass_renumbered_to_four` pins the new `Pass 4 (J18)` label and absence of the old “Reached only…” sentence, but never asserts the replacement explanation shown in T5's code block. An implementation that deletes the false explanation entirely passes, so add a positive assertion for the new “no pass above resolved exactly one handle” wording if that correction is part of the task contract.

## Nit
- AC-6.12…AC-6.20 says its nine listed mutations are “one mutation per node that is green at RED,” but the final two here-string mutations target AC-3.16 and AC-4.5, both RED: FAIL; rephrase the sentence to distinguish the seven green-at-RED proofs from the two independent SIGPIPE guard mutations.
AUDIT-pin-agents-tail-banner-impl-plan-v22-END
