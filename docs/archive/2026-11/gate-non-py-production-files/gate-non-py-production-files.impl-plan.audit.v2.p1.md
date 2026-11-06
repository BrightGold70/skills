AUDIT-gate-non-py-production-files-impl-plan-v2-BEGIN
## Summary
The plan follows the intended architecture, but its new host verdict guards lack required mutation entries, and retained prototype readings lack runnable provenance. This was a read-only source audit; planned tests and removed prototypes were not executed.
Evidence: 25 files opened, 15 greps run.

## Must-fix
- Tasks 4 and 5 omit mutation entries for their new non-Python verdict guards — neither host's catalog mutates the new `if verdict.decision != "ALLOW":` condition. The listing connection mutants operate upstream and leave it intact, so they do not satisfy AC-9.3's entry-per-guard requirement. Add uniquely marked, symbol-pinned mutants disabling these conditions, scored on each host's listed-absent-test denial; reconcile the remaining new guards against the catalog and update the ledger.
  class: build
  quote: docs/01-plan/features/gate-non-py-production-files.impl-plan.md › `if verdict.decision != "ALLOW":`
  quote: docs/01-plan/features/gate-non-py-production-files.spec.md › `Every new guard in FR-1, FR-3 to FR-8 and FR-11 has a mutation-spec entry.`

- Task 6 retains measured prototype timing and process-count claims without the exact commands and scratch-fixture preparation that produced them — the future pytest commands do not reproduce those historical measurements on the deleted prototype. This breaches Behavioural premises carry their command. Supply runnable reproduction recipes with the observed outputs, or withdraw these readings as unverified, as was done for the regression-prototype reading.
  class: measurement
  quote: docs/01-plan/features/gate-non-py-production-files.impl-plan.md › `a real hook call read 0.31 s absent and up to 0.76 s with a listed failing test on the prototype`; ``Prototype reading through a logging `python3` shim, total launches, each including the hook's 2 launches before any of these decisions: 4 for the unlisted code-like write where state exists, 2 for the doc/data write, 2 for the unlisted code-like write with no state file.``

## Should-fix
- Task 8 should distinguish the environment for repository Git commands from the hermetic hook environment — its plan-blob-mismatch fixture requires the injected Git configuration to reach `git hash-object`, whereas applying the declared restricted subprocess environment there removes that trigger. Specify that boundary explicitly, or set core.autocrlf in the fixture repository's local configuration, so an implementer cannot accidentally make the refusal fixture ineffective.
  class: build
  quote: docs/01-plan/features/gate-non-py-production-files.impl-plan.md › ``**Hermetic environment.** `subprocess.run(env=...)` with `HOME`, `PATH`, `LANG` (default `en_US.UTF-8`) and `TMPDIR```; ``a base commit holding a CRLF plan, a later HEAD, and `GIT_CONFIG_COUNT=1`, `GIT_CONFIG_KEY_0=core.autocrlf`, `GIT_CONFIG_VALUE_0=true` in the driver's environment, so `git hash-object` normalises the copy and differs from the blob id``

## Nit
None
AUDIT-gate-non-py-production-files-impl-plan-v2-END
