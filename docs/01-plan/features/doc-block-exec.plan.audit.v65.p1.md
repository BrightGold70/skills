## Summary
The plan strictly implements the specification, handling edge cases such as process group escapes, concurrent stream artifacts, and atomic reservations. Axis C reconciliation shows perfect alignment across all functional requirements, with one deliberate and necessary restatement in FR-6 to satisfy the base invariants.

| Requirement | Classification | Meaning |
|---|---|---|
| FR-1 | `implemented-as-written` | Plan covers addressing by doc, heading, tag, duplicate headings, ordinal selection, and authoritative bounding. |
| FR-2 | `implemented-as-written` | Plan covers substitution with explicit map, absent key refusal, empty key refusal, simultaneous replace, and `--subst` parsing. |
| FR-3 | `implemented-as-written` | Plan covers disposable cwd via mkdtemp, shell mode, temp cwd cleanup, stdout/stderr artifacts, and fixture preamble. |
| FR-4 | `implemented-as-written` | Plan covers verdict-token CLI, quoting JSON fields, strict exit code partition (0 vs 2), and mapping helper's own errors. |
| FR-5 | `implemented-as-written` | Plan covers bounded execution via Python's communicate, timeout validation, race handling with `poll` before `killpg`, and bounded drain. |
| FR-6 | `restated` | Plan wraps the out-of-suite gate command in `hmad-dispatch run --timeout` to enforce the time-bounds invariant. |

## Must-fix
- FR-6 gate command restated — Spec AC-6.4 explicitly dictates the out-of-suite gate command: `python3.11 -m pytest -q -p no:cacheprovider > /tmp/doc_block_exec_suite.log; RC=$?; tail -1 /tmp/doc_block_exec_suite.log; echo "SUITE: rc=$RC"`. The Plan restates this by wrapping the suite command in the `hmad-dispatch run --timeout` wrapper to comply with the base invariant "Portable time bounds", and breaking it across two lines: `hmad-dispatch run --timeout 1200 -- python3.11 -m pytest -q -p no:cacheprovider > /tmp/doc_block_exec_suite.log; RC=$?` and `tail -1 /tmp/doc_block_exec_suite.log; echo "SUITE: rc=$RC"`. The plan is narrower and correctly enforces the time bound required by the invariant, which the spec omitted. Update the spec to carry the wrapped command.

## Should-fix
None

## Nit
- Misplaced registry sentence — In FR-3, the sentence "The registry entry carries a detail row for that reason like every other emittable line (AC-4.5)" is placed immediately after the discussion of a preamble lacking a trailing newline. This makes it read as though a missing trailing newline emits a refusal/detail line, when in fact it is a successful composition. The sentence was likely meant to follow the earlier discussion of `UNREADABLE reason=preamble_unreadable`.
