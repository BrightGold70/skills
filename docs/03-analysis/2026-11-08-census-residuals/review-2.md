# Change review — working tree vs cdd36a6f (census-r2.diff, round 2) — GATING

## Evidence
- read: 2 files. I read the r2 diff (all 205 lines, census-script hunks closely) and `h_mad_guard_census.py` around 405-450, 624-645, 689-702 and 741 in the scratch tree. That script is byte-identical to the working tree's.
- ran: 9 commands.
  - In-process: `ast.parse` RecursionError threshold vs Python stack depth (python3.11.8).
  - 17 throwaway-repo CLI runs: a doc-named `run.conf` holding `#!/usr/bin/env python3\nx = 1+1+…`, scanning N from 2900 to 3000 terms.
- tests run: `h-mad/tests/test_h_mad_guard_census.py` (whole file), result `135 passed, 4 skipped`. I did not run the mutation harness.

## Round-1 findings
- **Must-fix (RecursionError crash): closed for the reported input.** The pre-check now calls `_python_decisions`, which catches `RecursionError` (line 409) and raises `Unreadable`. The new test with 200000 terms passes.
- **Should-fix (base guards uncounted): closed.** `h_kind, h_text = None, ""` keeps the measured base side. `census()` then sets `old_lines` to every base line when `not e.h_kind`, so all base decisions land on `REMOVED:`. The new test (removed=3) passes, and its HEAD-ONLY → `continue` row targets it.
- **Should-fix (unanchored new lines): closed** for the pre-check gate and the head-only line. Both now have rows, and the coordinator reports ALL_CAUGHT 82/82; I did not re-run that.
- **Should-fix (`ValueError`): moot.** The except is now just `Unreadable`.
- **Nit (BOM / leading space): addressed** as a stated rule in the docstring.

## Must-fix
- **The stack-depth window is narrowed, not closed: a doc-named head 1 frame from the limit still makes the whole census UNREADABLE, which falsifies the new docstring.** The docstring says such a head "is `unmeasured` rather than the census UNREADABLE".
  - Mechanism: in 3.11, ast construction's recursion budget is the recursion limit minus the CURRENT stack depth. I measured the cost in process: each extra frame lowers the passing term count by 3 (depth 0 → 2983, 5 → 2968, 10 → 2953, 11 → 2950).
  - The two calls sit at different depths. The pre-check runs at `census → _python_decisions` (line 630). The decision pass runs one frame deeper, at `census → _census_added → _python_decisions` (line 702).
  - Executed scenario: base `run.conf` = `x = 1\n`; head `run.conf` = `#!/usr/bin/env python3\nx = ` + `+`.join(["1"] × N). Results by N:
    - N=2977: `DONE decision=1` (measured).
    - N=2978, 2979, 2980: `run.conf: does not parse (RecursionError)` then `GUARD-CENSUS: UNREADABLE reason=unreadable-file`.
    - N=2981+: `UNMEASURED: run.conf … DONE`.
  - The result fails closed: it is UNREADABLE, the pre-change behaviour, not a wrong count. But the property the change claims is false for a reproducible 3-wide window, and that window moves with interpreter, recursion limit and call depth.
  - Fix that closes it by construction: keep the pre-check's result and reuse it. Store the decisions on the `Entry` (for every py head, or at least the doc-named ones) and have `_census_added` use them instead of re-parsing. Then the head is parsed exactly once and no second-depth parse exists. A pin: the same fixture at the measured boundary is fragile, so a better test monkeypatches or counts calls to show `_python_decisions` runs once per head.
  quote: h-mad/scripts/h_mad_guard_census.py:630 › `_python_decisions(h_text, ch.path)  # the same parse, and the same exceptions, as below`
  quote: h-mad/scripts/h_mad_guard_census.py:702 › `for d in sorted(_python_decisions(text, ch.path), key=lambda d: (d.line, d.kind)):`

## Should-fix
- **The pre-check's comment claims more than it guarantees.** "the same parse, and the same exceptions, as below" is true of the exception set, but not of the outcome: the window above shows the same parse can succeed at one depth and fail at the other. If the fix reuses the result, the comment becomes true as written.
  quote: h-mad/scripts/h_mad_guard_census.py:630 › `# the same parse, and the same exceptions, as below`

## Nit
None
