## Summary
The design cleanly introduces a strictly opt-in, bounded bash block executor using `tempfile.mkdtemp()` and `subprocess` to evaluate documented recipes without external dependencies. However, there are stale references to `open(path, "a")` that contradict the updated atomic `os.open` descriptor-level logic, and a contradiction regarding the exact count of tests added to the migration consumer file.

## Must-fix
- Stale `open(path, "a")` mechanism in exception and mutation tables — The `Error Handling Strategy` table maps `StreamPathUnwritable` to "the open(path, 'a') itself", and the `stream-reserved-with-truncation` mutation describes its mechanism as "reservation opens 'w' instead of 'a'". This contradicts the `Detailed Design` and `Plan`, which explicitly specify that stream reservation uses a two-arm atomic loop with `os.open` and `O_APPEND`/`O_EXCL` flags.
- Contradictory test count in AC-6.4 floor calculation — The design's AC-6.1-6.6 text introduces a new test `test_only_the_exec_scan_hand_rolls_extraction` to pin the `:412` scan as the single remaining occurrence, but explicitly claims there are exactly "five" named tests added to `test_h_mad_collect_report_docs.py` (and omits this sixth test from the floor calculation list), creating a contradiction in the test floor baseline.

## Should-fix
- Contradictory wording regarding `docsections.json` mutations in the Plan — The Plan states it "anchors three of its four mutations... on lines that leave tests/docsections.py", but then says "the third stays (it mutates section_from's call, which remains)". If the mutated call remains in `docsections.py`, the anchor does not leave the file (the Design correctly states that two leave and two stay).

## Nit
None
