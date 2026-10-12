# Mutation sweep, 2026-10-12: hollow-kill negative control

Full `h_mad_mutation_harness.py --sweep` at `846fcfec`, run in a detached throwaway worktree because a live HemaSuite session was using the symlinked skill. Raw log: session scratchpad `sweep.log` (volatile). This file is the durable copy.

```
SWEEP: ALL_CAUGHT specs=165 all_caught=165 survived=0 unmeasured=0
RC=0
```

## Every forwarded kill (paths relative to the worktree)

```
  kill: h-mad/tests/mutation-specs/audit_cycle_grok.json :: a1-grok-truncated-render-dropped :: crash: KeyError in h_mad_audit_cycle.py
  kill: h-mad/tests/mutation-specs/audit_effort.json :: four-field-caller-rejected :: crash: ArgumentTypeError in h_mad_audit_cycle.py
  kill: h-mad/tests/mutation-specs/audit_effort.json :: log-field-not-last-so-colons-split :: crash: ArgumentTypeError in h_mad_audit_cycle.py
  kill: h-mad/tests/mutation-specs/audit_origins.json :: a-zero-denominator-reports-zero-percent-instead-of-n-a :: crash: ZeroDivisionError in h_mad_audit_origins.py
  kill: h-mad/tests/mutation-specs/delta_stage.json :: encode-error-escapes-rollback :: crash: UnicodeEncodeError in h_mad_delta_stage.py
  kill: h-mad/tests/mutation-specs/delta_stage.json :: answers-kind-unchecked :: timeout: subprocess.TimeoutExpired — unattributed; a guard that fires returns, so this is unlikely to be the property
  kill: h-mad/tests/mutation-specs/doc_block_exec.json :: doc-decode-error-unwrapped :: crash: UnicodeDecodeError in h_mad_doc_block_exec.py
  kill: h-mad/tests/mutation-specs/doc_block_exec.json :: precedence-timeout-raised-in-handler :: timeout: subprocess.TimeoutExpired — unattributed; a guard that fires returns, so this is unlikely to be the property
  kill: h-mad/tests/mutation-specs/doc_block_exec.json :: wait-expiry-unmapped :: timeout: subprocess.TimeoutExpired — unattributed; a guard that fires returns, so this is unlikely to be the property
  kill: h-mad/tests/mutation-specs/doc_block_exec.json :: drain-oserror-unmapped :: timeout: subprocess.TimeoutExpired — unattributed; a guard that fires returns, so this is unlikely to be the property
  kill: h-mad/tests/mutation-specs/doc_block_exec.json :: stream-open-blocking :: timeout: subprocess.TimeoutExpired — unattributed; a guard that fires returns, so this is unlikely to be the property
  kill: h-mad/tests/mutation-specs/doc_consumers_run.json :: non-utf8-output-crashes :: crash: UnicodeDecodeError in h_mad_doc_consumers.py
  kill: h-mad/tests/mutation-specs/docsections.json :: docsections-syspath-setup-removed :: crash: ModuleNotFoundError in docsections.py
  kill: h-mad/tests/mutation-specs/evidence_targets.json :: root-itself-counted :: crash: IndexError in h_mad_review_evidence.py
  kill: h-mad/tests/mutation-specs/exec_pane_panekey.json :: join-never-expires :: timeout: subprocess.TimeoutExpired — unattributed; a guard that fires returns, so this is unlikely to be the property
  kill: h-mad/tests/mutation-specs/failure_diff.json :: R2-N3-reconfigure-unguarded :: crash: AttributeError in h_mad_failure_diff.py
  kill: h-mad/tests/mutation-specs/mutation_harness.json :: a-bad-spec-aborts-the-sweep :: crash: SpecError in h_mad_mutation_harness.py
  kill: h-mad/tests/mutation-specs/release_ownership_guard.json :: a-stale-claim-now-needs-force :: crash: StateWriteError in h_mad_state_write.py
  kill: h-mad/tests/mutation-specs/release_ownership_guard.json :: a-session-cannot-release-its-own-claim :: crash: StateWriteError in h_mad_state_write.py
  kill: h-mad/tests/mutation-specs/release_ownership_guard.json :: force-no-longer-opens-the-takeover-route :: crash: StateWriteError in h_mad_state_write.py
  kill: h-mad/tests/mutation-specs/review_evidence_grok.json :: e4-membership-before-type-check :: crash: TypeError in h_mad_review_evidence.py
  kill: h-mad/tests/mutation-specs/review_evidence_grok.json :: e4-membership-before-type-check :: hollow: TypeError at h_mad_review_evidence.py:350 inside the replacement — the mutant's own new text failed to run, so this kill says nothing
  kill: h-mad/tests/mutation-specs/review_evidence_grok.json :: e10-scan-event-membership-unguarded :: crash: TypeError in h_mad_review_evidence.py
  kill: h-mad/tests/mutation-specs/review_evidence_grok.json :: e10-scan-event-membership-unguarded :: hollow: TypeError at h_mad_review_evidence.py:418 inside the replacement — the mutant's own new text failed to run, so this kill says not
  kill: h-mad/tests/mutation-specs/review_evidence_grok.json :: d1-grok-nonfinite-guard-dropped :: crash: OverflowError in h_mad_review_evidence.py
  kill: h-mad/tests/mutation-specs/review_evidence_grok.json :: d1-agy-nonfinite-guard-dropped :: crash: OverflowError in h_mad_review_evidence.py
  kill: h-mad/tests/mutation-specs/state_undeclared_keys.json :: the-repair-strips-a-declared-key-too :: crash: StateWriteError in h_mad_state_write.py
  kill: h-mad/tests/mutation-specs/wire_registry_base_path.json :: no-work-tree-raises-instead-of-deferring :: crash: RegistryError in h_mad_wire_registry.py
```

## Verdict: the refusal is NOT wired

- 165 specs ALL_CAUGHT. 20 crash kills, 6 timeout kills, and 2 flagged `hollow`.
- Both hollow flags are real kills. `review_evidence_grok.json` rows `e4-membership-before-type-check` and `e10-scan-event-membership-unguarded` each remove an `isinstance(..., str)` guard. Their named tests feed a malformed or unhashable value. The mutant then runs `x in _SET` on that value and raises `TypeError` on the replacement's own line. That crash IS the property violation the guard prevents. These are the same two real `TypeError` kills the 2026-10-04 calibration listed.
- The corpus holds 0 true hollow kills: the 2026-09-14 four were fixed by hand in `32789ad9`. The positive control (that replay) flagged 3 of 5.
- So the site rule cannot tell "the new text cannot run" (`NameError`, an unknown kwarg) from "the new text ran an operation the removed guard protected". Refusing on it would refuse 2 of 20 real kills. The flag stays an annotation for the author, and its wording no longer claims the kill says nothing about the guard.
- What a refusal would need is a property that does not depend on the input, e.g. the replacement raising the same exception on the BASELINE inputs of an unrelated passing test. That is a new design and needs its own calibration. It is not a widened exclusion list.
