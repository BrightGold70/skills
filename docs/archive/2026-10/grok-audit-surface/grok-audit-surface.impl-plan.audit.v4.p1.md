## Summary
The S0c plan retains blocking gaps in regression migration, canary fixture reachability, and enforcement of the usage-error halt contract. This was a static audit; no repository files were changed and no tests were run.
Evidence: 21 files opened, 14 greps run.

## Must-fix
- Task 18 omits an existing test that contradicts the new sandbox contract — `h-mad/tests/test_hmad_dispatch_exec_grok.py::test_exec_grok_translates_model_effort_sandbox[given]` supplies `--sandbox s1` without the override and requires the agent capture file to exist. The planned refusal prevents that launch, so the mandatory full suite cannot stay green. Add this module to Task 18's migration scope, identify its permissive-profile expectation as superseded, and preserve its model/effort translation coverage using the explicit override. This also supplies the regression provenance required before changing an existing test.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › ``A value other than `strict` without the flag exits 2``
  quote: h-mad/tests/test_hmad_dispatch_exec_grok.py › `(["--model", "m1", "--effort", "high", "--sandbox", "s1"], True),`
- Task 23's truncated fixture cannot reach the predicate its mutation row targets — removing the `end` event makes the shipped `_cmd_exec` classify the stream as incomplete and return 3, even when text is recoverable. Passing that actual rc into the planned judge selects `cannot_run:grok_rc:3` before its `truncated` check. Consequently the prescribed fixture cannot establish GREEN for `cannot_run:truncated` or discriminate `canary-truncated-disarmed`. Exercise the judge's truncated branch separately with a readable no-end log and `--rc 0`, retaining the real wrapper's rc-3 path as a regression control; alternatively, explicitly revise the wrapper/judge contract and its paired design before implementation.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › ``sleep past `--timeout`, no `end` event).``
  quote: h-mad/tests/test_hmad_dispatch_exec_grok.py › `assert r.returncode == 3, "exec grok must mark a stream without end as incomplete"`
- Task 22 leaves its usage-error fail-closed path unpinned — its failure fixture raises from the reader, after argument parsing, whereas an unknown flag or missing argument can fail before a Namespace containing `--halt-file` exists. That fixture and `require-fail-closed-dropped` do not enforce recovery of the halt path on a parser error. Add a usage-error case with an explicit halt path, assert exit 2 and the resulting HALT file, then verify that the next audit-cycle launches nothing. Give the parser-error recovery connection its own negative observation, so dropping only that connection fails the test.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › `usage or internal error, after writing the halt file when one was named.`

## Should-fix
- Correct the reset-fixture parent description in Task 24 and Task 5's S0c note — they say accepted reset roots are under the stand-in system temp, although the concrete root path `<tmp_path>/run/roots` and stand-in `<tmp_path>/systemp` are siblings. The new temp guard rejects the former description. Change that wording to “outside the stand-in system temp”; the concrete prescribed paths already express the intended setup, so this correction requires no implementation change.
  class: measurement
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › ``with `--dest-parent <tmp_path>/run/roots` under the stand-in system temp, and guard 3 is inverted``

## Nit
None

