AUDIT-pin-agents-tail-banner-impl-plan-v9-BEGIN
## Summary
The plan is unusually concrete, but it is not dispatchable as written: its timeout test rejects the existing correct bounder, its RED-count commands compute impossible values, and one claimed mutation proof is behaviorally equivalent. The paired design also claims a live-check back-propagation that is absent from its body, leaving the authoritative documents inconsistent.

## Must-fix
- AC-2.6's `elapsed >= 1.0` assertion is false for the specified `_cmd_run` implementation — the existing bounder uses integer-valued Bash `SECONDS`, and five read-only probes of `run --timeout 1 -- sleep 3` completed in 0.89, 0.89, 1.16, 0.89, and 1.15 seconds. A correct T2 implementation will therefore fail intermittently; use a tolerant lower bound or a longer timeout/lower-bound pair that matches the owned bounder's measured behavior while still rejecting an instant return.
- The prescribed RED-count derivation commands do not count the authoritative table — `grep -c '^| `test_'` returns 0 because every row starts with `| AC-…`, while unanchored `grep -c 'RED: PASS'` returns 13 because it also counts prose outside the table, not the table's 11 PASS nodes. Passing their difference to `--expect-fail` makes the required 5d dispatch invalid, so the plan must supply table-scoped commands and verify they yield 35 total, 11 pass, and 24 fail.
- `tail-sig-swallows-failure` is an equivalent mutant for its named test — replacing `return 1` with `return 0` exits `_orca_tail_sig` with empty stdout; the pass enters the branch, the empty text fails `$tail_re`, and `continue` produces exactly the same all-unreadable decline. Thus `test_tail_pass_all_unreadable_declines` stays green and the harness reports a survivor, violating Test discrimination; use a non-equivalent permissive mutant that turns unreadable evidence into a matching candidate, or stop claiming this node has a reject-direction proof.
- The paired design is stale despite its v1.10 history claim — its actual Verification item 3 still requires only that `hmad-dispatch env` resolve codex and close a created pane, while the plan requires cleared pins, earlier-pass blindness, the tail-evidence marker, and verified cleanup. The plan also still labels its source as design v1.8 although that file's history reaches v1.10; update the design body and the plan's source citation before treating the back-propagation as complete.

## Should-fix
- T2's supposedly executable harness calls an undefined `_run_bash` and specifies its environment factoring only in prose — provide the concrete shared environment helper, `_run_bash` implementation, and revised `run()` call so the task does not leave the load-bearing isolation refactor to interpretation.
- AC-6.12 through AC-6.17 provide only six AC numbers but claim one mutation for each of seven listed green-at-RED nodes — correct the range or give each mutation an explicit AC mapping so traceability and counts agree.

## Nit
None
AUDIT-pin-agents-tail-banner-impl-plan-v9-END
