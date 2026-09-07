## Summary
The design implements all 49 specified acceptance criteria as written; the reconciliation table records that coverage by identifier. Two required safeguards are not verification-ready: the generic helper mutation specification is only named, and the combined timeout/cleanup-precedence test loses its only stated coverage under root.

| Spec AC identifiers | Classification |
|---|---|
| AC-1.1–AC-1.9 | implemented-as-written |
| AC-2.1–AC-2.8 | implemented-as-written |
| AC-3.1–AC-3.14 | implemented-as-written |
| AC-4.1–AC-4.6 | implemented-as-written |
| AC-5.1–AC-5.6 | implemented-as-written |
| AC-6.1–AC-6.6 | implemented-as-written |

## Must-fix
- The new `h-mad/tests/mutation-specs/doc_block_exec.json` is only declared as “guards for FR-1..FR-5”; unlike the wire and `docsections` specs, the design supplies no mutation names, exact anchors, or per-mutation named RED tests for its load-bearing scanner, substitution, launch, timeout, stream, and verdict guards — a harness invocation cannot prove guards that the plan never specifies, contradicting the claimed “every guard carries a mutation” and the base Mutation verification/Test discrimination invariants. Define the concrete entries and their `target_command`/`test` bindings, then require `ALL_CAUGHT`.
- `test_cleanup_failure_outranks_timeout` is specified through the real `chmod 000` permission fixture, while the design says that fixture is skipped when `euid == 0`; the two deterministic `rmtree` injections only prove recorded-error and read-back behavior, not the required pending-`BlockTimeout` → `CleanupFailed(__cause__)` precedence — on a root runner the precedence guard is absent, so the stated safety check is not discriminated in a supported environment. Add a fault-injected combined timeout-plus-`rmtree` failure test that runs everywhere and asserts the final exception, `cleanup_error`, cleanup read-back, and `BlockTimeout` cause.

## Should-fix
None

## Nit
None
