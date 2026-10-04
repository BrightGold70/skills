AUDIT-pin-agents-tail-banner-impl-plan-v13-BEGIN
## Summary
The implementation path and cross-document behavior are largely consistent, and the stated 37/11/26 RED counts reproduce. Three mutation-discrimination gaps remain: one mutant is killed by a shell abort, two SIGPIPE regression tests lack reject-direction verification, and one unreadable-tail mutant depends on an unstated fixture shape.

## Must-fix
- `resolve-on-ge-0` is a crash mutant, not a discriminator for AC-3.5 — with `tn=0`, the relaxed branch executes `tail_h="$(printf ... | grep . | head -n 1)"`; `grep` returns 1 and global `set -euo pipefail` aborts before the mutant can resolve or fall through (reproduced as rc 1 with empty stdout/stderr). A targeted-test failure would therefore be credited to an operational crash, violating Test discrimination; replace it with a mutant that makes one readable nonmatching candidate enter `tail_ids` (and pin that fixture), or otherwise make the permissive path produce an observable wrong resolution without aborting.
- The two long-tail tests are not verified against the defect they were added to catch — `test_tail_pass_long_tail_early_signature_resolves` and `test_tail_pass_long_tail_early_rival_rejected` are RED when the entire pass is absent, but T6 has no mutation changing either here-string back to `printf ... | grep -q`. Thus their size/order dimensions have never been shown to bite in the integrated code, despite the plan calling the here-string load-bearing and claiming every new guard is mutation-tested; add one wanted-check pipeline mutant and one rival-check pipeline mutant, each pinned to the corresponding long-tail node and verified by its `mechanism:` line.
- `tail-sig-fabricates-banner-on-failure` has an unstated kill precondition — its hardcoded `OpenAI Codex` output changes the expected decline only for exactly one unreadable candidate while resolving `codex`. Two unreadable candidates fabricate two matches and still decline on ambiguity, while an `agy` fixture does not get a wanted match; require `test_tail_pass_all_unreadable_declines` to use exactly one unreadable Codex candidate, or redesign the mutation so every permitted fixture changes behavior, otherwise AC-3.11's green-at-RED proof can survive and violates Test discrimination.

## Should-fix
- Task 4 still lists AC-4.2 as an active acceptance criterion, but its own later explanation and the test-name contract call that same task-local AC “withdrawn” — mark it withdrawn at the Task 4 list or remove it there so implementers do not create a fifth T4 node that contradicts the stated four-node/37-node dispatch contract.

## Nit
- The paired spec still assumes that the launch command remains visible above the alternate-screen region even though v1.5 explicitly made launch text non-evidence; remove it or restate the actual banner-retention assumption to avoid suggesting a dependency the feature no longer uses.
AUDIT-pin-agents-tail-banner-impl-plan-v13-END
