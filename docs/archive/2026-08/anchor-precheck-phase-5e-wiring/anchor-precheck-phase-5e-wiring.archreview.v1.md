An architectural review of the Phase 5 implementation against the `anchor-precheck-phase-5e-wiring` design reveals three Critical invariant and contract violations.

The implementation fails to uphold the structural boundary for the new verdict shape, modifies a string output contract that must remain stable, and silently drops skipped files from the suite assertion.

### Findings

- **File/Line:** `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_mutation_harness.py:471-475` (inside `run_spec`) and `:748` (inside `main`)
  - **What's wrong:** `run_spec` returns `result["verdict"] = "REFUSED"` and uses a side-channel boolean flag `result["precheck_failed"] = True` to tell `main()` the real verdict. Because it reuses the initialized `result` dict, the returned object also contains `mutations`, `caught`, `survived`, and `refused` keys.
  - **Why it matters:** This violates AC-4.1 ("The dict still deliberately carries **no** `mutations`/`caught`/`survived`/`refused` keys... so the no-counts rule cannot regress into printing zeros"). It creates an unprincipled boundary where `REFUSED` internally absorbs the precheck failure, exactly what the design explicitly warned against avoiding.
  - **How to fix:** Do not use `result["precheck_failed"] = True` or append to `result["refused"]`. Instead, construct and return a new dictionary directly: `return {"verdict": "PRECHECK_FAILED", "precheck": precheck, "drifted": result["drifted"], "unreadable": result["unreadable"]}`. Update `main()` to simply read `verdict = result["verdict"]`.
  - **Operator override:** Unreasonable. This is a core architectural invariant of the design (preventing silent regressions).

- **File/Line:** `/Users/kimhawk/orca/skills/handoff/tests/test_mutation_specs_clean.py:15-23` and `/Users/kimhawk/orca/skills/h-mad/tests/test_h_mad_mutation_harness.py:1441-1449` (`_own_committed_mutation_specs`)
  - **What's wrong:** The helper `_own_committed_mutation_specs` silently drops files classified as `not-a-spec` or `unclassifiable`. They are never passed to the assertion failure message builder.
  - **Why it matters:** The design mandates (FR-5 / AC-6.4): "Files classified `not-a-spec` or `unclassifiable` are named in the assertion message for the same reason they are named at runtime." If the test fails due to drift, these skipped files vanish from the diagnostic output, silently breaking the visibility rule that prevents narrowing.
  - **How to fix:** Have `_own_committed_mutation_specs` return both the list of valid specs AND the list of skipped/unclassifiable file details, and append the skipped ones to the `failures` list in `_committed_spec_drift_messages` so they appear in the final `assert not failures` output.
  - **Operator override:** Unreasonable. This defeats the visibility requirements of the suite assertion.

- **File/Line:** `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_mutation_harness.py:695-697` (inside `_check_anchors`)
  - **What's wrong:** The final summary line is printed as `ANCHORS: {verdict} specs={specs} mutations={mutations} ok={ok} drifted={drifted} unreadable={unreadable} skipped={skipped} unclassifiable={unclassifiable}`.
  - **Why it matters:** The design's Test Plan specifically requires the exact literal shape: `ANCHORS_OK specs=<N> mutations=<M> ok=<M> drifted=0 unreadable=0`. Adding `skipped=` and `unclassifiable=` to this summary line breaks consumers expecting the previous token format. The design only specified that skipped/unclassifiable files "are always named in output" (which is correctly handled by the per-file `ANCHORS: ... SKIPPED` detail lines you added earlier), not that they alter the final summary string.
  - **How to fix:** Remove `skipped={skipped} unclassifiable={unclassifiable}` from the final summary `print()` in `_check_anchors`.
  - **Operator override:** Unreasonable. This breaks the explicit string formatting contract detailed in the spec.

```
ASSESSMENT: WITH_FIXES
```
