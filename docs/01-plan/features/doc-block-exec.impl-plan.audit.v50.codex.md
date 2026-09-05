## Summary

The plan has three blocking gaps in mutation discrimination, rollback verification, and parser behavior. Read-only permissions prevented creating the requested report and `.done` files; the repository remains unchanged.
Evidence: 10 files opened, 7 greps run.

## Must-fix

- Task 3’s `preamble-composed-with-unsubstituted-text` mutation has no implementable distinction at its assigned boundary — `run_block` receives the already-substituted block and composes using its `block.text`; it has no original text to substitute incorrectly. The specified replacement is therefore equivalent, or requires inventing an unavailable variable. Move this mutation and its killer to the caller that holds both blocks, or specify a different discriminating mechanism before requiring `ALL_CAUGHT`.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › ``comp oses`` is not used; the exact prescribed expression is ``preamble.rstrip("\n") + "\n" + block.text`` and the task states `` `run_block` never substitutes.`` 
  quote: docs/02-design/features/doc-block-exec.design.md › ``| `preamble-composed-with-unsubstituted-text` | composition uses `block.text`, not `text′` | `test_preamble_and_substitution_compose` (AC-3.11) |``

- Alias-refusal rollback explicitly omits verification — when both stream arguments name the same initially absent path, reservation creates a file and the alias branch deletes it. Without a read-back, a silent unlink failure leaves that new artifact behind without reporting it. This violates the base Mutation verification invariant; verify this deletion and add a discriminating failure test.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › ``alias refusal also unlinks the files this call created, and that path is unchanged and grows no``

- The parser does not enforce the stated help-only exception — on Python 3.11.8, the prescribed parser prints help and raises `SystemExit(0)` for both `--help` and `--bogus --help`; adding a valid document and heading before `--help` also bypasses verdict rendering. The controlled probe contradicts the claimed invocation partition. Either enforce the singleton exemption or explicitly broaden the contract and test its boundary.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › ``Exactly one invocation still leaves without a``; `` `DOCBLOCK:` line — `--help` alone, which keeps argparse's own help text — and it exits **0**,``

## Should-fix

- The collateral-failure enumeration is still incomplete — `strict-flags-dropped` also breaks `test_pipefail_strict_vs_plain`, beyond its canonical unset-variable test. Executing both documented fixtures under strict and plain Bash produced return codes `1/0` for each. Re-derive actual test effects, or scope the enumeration to explicitly documented collateral relationships.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › ``the only rows in **`doc_block_exec.json`** whose mutant reds a second named test;``
  quote: docs/02-design/features/doc-block-exec.design.md › ``| `strict-flags-dropped` | `bash -c` always, never `-euo pipefail` | `test_unset_variable_fails_under_strict` (AC-3.3) |``

- The close-only test is incorrectly classified as a collateral killer — moving close after the flush does not move it outside the caller’s `OSError` mapping. An in-memory controlled pair produced `stream_write_failed` under both implementations when close alone failed; only the flush-plus-close case distinguished whether close ran. Correct the collateral claim while retaining the canonical test.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › ``a regression test for `final-write-close-not-in-finally`, not its `test` key``

- Later RED accounting still calls Task 2’s tests “ten,” although Task 2 now specifies eleven — reconcile both later regression-block descriptions so implementers receive one consistent count.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › ``Task 1's block, Task 2's ten, and this task's own``; ``**Acceptance Criteria** (**eleven** tests``

- Several no-injection CLI tests contradict the mandatory subprocess transport rule — the dynamic-field, quote, Unicode-separator, and malformed-invocation tests explicitly call `main` in-process. Move these real-input cases to subprocesses or document a precise exception to the convention.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `` `test_dynamic_field_cannot_forge_a_token` (in-process main, no injection)``

## Nit

None
