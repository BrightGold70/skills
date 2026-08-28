# 6a-prime architectural review — wire-registry-feature-scoped-key

**Reviewer:** agy 1.1.22, headless `exec agy` · **Date:** 2026-08-27
**Range:** `d275d7b`..`9e20c94` · **Verdict:** `READY_TO_MERGE`
**Evidence gate:** `EVIDENCE: PASS tools=12 ok=12 failed=0 thinking=8392 status=SUCCESS`

Run out of band, after the fix had already shipped, because `9e20c94` was a defect fix made
directly on main rather than a feature through the ladder — so there is no 5c/5g pair and no
audited design. The prompt said so explicitly rather than letting the reviewer assume one, and
named the three things I was least confident about so the review had somewhere real to bite.

---

I have completed the review by successfully opening and inspecting all of the requested files via absolute paths:
- `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_wire_registry.py`
- `/Users/kimhawk/orca/skills/h-mad/tests/test_h_mad_wire_registry.py`
- `/Users/kimhawk/orca/skills/h-mad/tests/mutation-specs/wire_registry_key.json`
- `/Users/kimhawk/orca/skills/docs/skill-monitoring.md`
- `/Users/kimhawk/orca/skills/.h-mad/invariants.md`
- `/Users/kimhawk/orca/skills/.h-mad/wires.jsonl`

Here are my judgements on the specific concerns you raised:

### 1. Halt-reason shape (`<feature>::<id>`)
This is the correct choice. As stated in J43, a halt reason's primary purpose is to be actionable; emitting `step5f:undeclared_removal:Task 4` on a project with multiple features is inherently ambiguous. The `::` is the idiomatic scoping operator in the pytest ecosystem (where this domain lives), making it a natural fit for "task scoped within feature." While a naive downstream script splitting purely by `:` might see a longer array, preserving an ambiguous and unactionable string to avoid breaking hypothetical fragile regexes is the wrong trade-off. You also correctly updated the `test_h_mad_wire_registry.py` fidelity scraper and `SKILL.md` to reflect the new contract in sync.

### 2. Composite key `(owning_feature, id)` vs changing `id`
Keying on `(owning_feature, id)` is precisely the right architectural fix. The `id` field ("Task N") carries vital semantic meaning: it binds the registry record directly to the numbering in the feature's `.h-mad/impl-plan.md`. If you had changed `id` to a UUID, you would have severed that traceability. If you had redefined `id` to store `"feature::Task N"` inside the JSON payload, you would have triggered a mandatory data migration for every `wires.jsonl` in every repository. Since `owning_feature` was already a required schema field (L51), composing the primary key dynamically in memory gives you the correct identity matrix with zero migration debt.

### 3. Exposure of `record["id"]` in other consumers
I audited the file and verified your assessment. 
- **`challenge()`**: Safe. It reads IDs via `_parse_tasks(impl_plan)`. Because those IDs only need to be unique *within the single implementation plan being parsed*, the bare `Task N` remains a perfectly sound identity for that scope.
- **`partition()`**: Safe. It iterates over the records and partitions them strictly by their `pin` resolution status. It does not use identity for deduplication, dictionary keys, or lookups, so it is immune.
- **`register()`, `compare()`, `verify()`**: Safe. All correctly utilize the new `_record_key()` and `_record_label()` helpers.
- The only remaining usages of the string `"id"` are `validate_record` ensuring the field exists, and the CLI parser mapping `--id` into the record payload, both of which remain correct.

### General Audit
- **Cross-module coupling**: None. `_record_key` and `_record_label` are kept private to the module, only accessed externally by the test suite (which is expected). 
- **Pattern violations**: None. The error handling, structural invariants, and token outputs match existing norms exactly.
- **Missing tests**: The `TestFeatureScopedKey` class explicitly includes `test_same_id_under_the_same_feature_still_updates_in_place` (the accept direction) alongside `test_same_id_under_a_different_feature_does_not_evict` (the reject direction). Mutation testing guarantees the assert strength.
- **Invariant compliance**: Fully compliant with Axis B (`.h-mad/invariants.md`). No external dependencies were introduced, and the skill contract in `SKILL.md` was appropriately synchronized.

ASSESSMENT: READY_TO_MERGE
