## Summary
This is an advisory delta review of `86d4a528` (impl-plan v1.0 to v1.1). Most hunks close what they claim, and I checked that by running them:
- All 14 new `find`s (E9 and the 13 WR rows) count 0 in today's tree (`grep -cF`). Each WR find lands exactly once in the plan's own code blocks, or once by construction for WR4/WR11. None overlaps any of the 907 committed finds in either direction.
- The E9 kill is an assertion, not a crash. I ran the `pytest.fail` wrapper against today's `scan()` (the E9 mutant state), and the harness's own `crash_kill` returned `None`.
- The renderer prints 13 lines on F0, as the plan says.
- The Task 17 smoke, run against a stub wrapper and stub readers, halted with its own `FAIL:` line on each of 16 single-condition breaks under both bash and zsh. The unbroken run printed `SMOKE: PASS`.

There is one blocking defect. Task 16's newly hard-guarded node-id floor fails on every run, because the base collect runs from an archive that has no `docs/`. There are also three should-fix gaps: the unmodified gate still has a hole, the jq-shim list misses a member, and Task 7 test 12's RED assertion is not specified.

Evidence: 22 files opened, 41 greps run.

## Must-fix
- Task 16's floor now halts with `FAIL: node ids collected at BASE_SHA are gone` on every run, even when nothing changed. I ran the plan's exact base and head collect commands at one commit (`HEAD`, where `h-mad/` and `handoff/` are identical to `507214d`):
  - Base collect (`git archive … h-mad handoff`) listed 3886 ids. Head collect listed 3893.
  - `comm -23` printed one line: `h-mad/tests/test_h_mad_audit_cycle.py::test_premise_items_match_gate_count_real_artifacts[NOTSET]`.
  - The cause: that test is `@pytest.mark.parametrize("report", REAL_AUDIT_REPORTS, …)` (`h-mad/tests/test_h_mad_audit_cycle.py:1727`), and its list is globbed from `docs/`. The archive leaves out `docs/`, so the list is empty and pytest emits `[NOTSET]`. The head collect instead finds 8 real reports.
  - v1.0 only printed this line under a `# must print nothing` comment. v1.1 turned it into a hard `exit 1`, so 5e can never reach `FLOOR: PASS`.
  - instance of: *a base collect run in an environment that differs from the head collect's*. Any test whose collection reads files outside `h-mad handoff` diverges the same way. Collection errors are also dropped silently, because `grep '::'` filters them out and `[ -s base.txt ]` only checks that the file is non-empty.
  - Rule: collect the base from the whole tree at `BASE_SHA`.
  - Repairs, each executed at `HEAD` with the result `comm -23` = 0 and `comm -13` = 0:
    - (a) `git archive "$BASE_SHA" | tar -x -C "$T"` (whole tree).
    - (b) `git archive "$BASE_SHA" h-mad handoff docs | tar -x -C "$T"`.
    - (c) Unexecuted: `git worktree add --detach "$T" "$BASE_SHA"`.
  - Repair (a) brings `pytest.ini` into `$T`. The Preamble sentence "Task 16's base collect runs from a `git archive` that has no `pytest.ini`" then needs rewording. It is harmless, because the paths are passed explicitly.
  - Separately, the base collect's summary line should be asserted free of `error`. Otherwise a base import failure quietly shrinks the floor.
  class: build
  quote: docs/01-plan/features/grok-codex-fallback.impl-plan.md › `git archive "$BASE_SHA" h-mad handoff | tar -x -C "$T" || { echo "FAIL: git archive $BASE_SHA"; exit 1; }`

## Should-fix
- The "unmodified gate" hunk (codex must 3) closes the instance the reviewer named (a skip decorator added to a `test_*.py`). It does not close the class: *any tracked file that can change a pre-existing test's outcome*.
  - The filter `(test_[^/]*\.py|conftest\.py)$` leaves out these files tracked at `507214d` under the three test paths: 5 `h-mad/tests/stubs/*`, 10 `h-mad/tests/fixtures/*`, 2 `h-mad/tests/specs/*`, and 2 helper modules. It also leaves out the root `pytest.ini`.
  - One of those helpers already decides skips: `h-mad/tests/claudebinary.py:74` `pytest.skip(reason)`.
  - The plan itself edits two of the excluded files: Task 1 changes `stubs/codex` and `stubs/agy`, and the plan names them as outside the check.
  - The node-id floor cannot see a skip, because a skipped test still collects.
  - Rule: `git diff --exit-code "$BASE_SHA"` over every file tracked at `BASE_SHA` under the three paths, plus `pytest.ini`. Exempt a named allowlist (`h-mad/tests/stubs/codex`, `h-mad/tests/stubs/agy`) whose diff is printed into the record.
  - Alternative: also compare the `pytest -rs` skipped count between base and head.
  - Residual: environment-driven skips inside unchanged files (for example the claude-binary probe), which a skip-count comparison would surface and a diff would not.
  class: build
  quote: docs/01-plan/features/grok-codex-fallback.impl-plan.md › `are test support, not test files, and are outside this list by its filter`
- The Convention 1 jq-shim list names three members, and the class has a fourth: Task 12 test 11 (`test_fallback_read_error_fails_closed`, a "`jq` shim in the cell's bindir").
  - Task 12's cell bindir "links the real `jq`", and `cell_env["PATH"]` is `f"{bindir}:/usr/bin:/bin"`, so the same collision applies.
  - That shim also "execs the real `jq`". Once it has replaced `bin/jq`, a bare `jq` inside it resolves to itself. It must exec an absolute path captured before the unlink (for example `shutil.which("jq")` read before replacing the link).
  - instance of: *every jq shim placed in a bindir that already links the real jq*.
  - Rule: name every member in Convention 1, or state the rule without a list. The rule is to replace the existing link, and a delegating shim execs the absolute path captured first. I did not open Task 12's intended helper code (none exists yet). The recursion hazard is inferred from the plan's text, not executed.
  class: build
  quote: docs/01-plan/features/grok-codex-fallback.impl-plan.md › `(Task 8 test 7, Task 9 test 22, Task 10 test 9)`
- Task 7 test 12's RED is not pinned by the assertion the text specifies. At Task 7 RED, Task 5 has landed:
  - `measure_effort(deep_line_200k() + f0_text())` returns `scan()` counts with shape `unparseable`.
  - `measure_effort(F0)` returns the same dict. I read `h-mad/scripts/h_mad_audit_cycle.py:530-566`: both texts have no agy events and no banner, and the deep line is now skipped.
  - So a test asserting only "equals `measure_effort` on F0" passes at RED, and the split becomes 9/10, not 10/9.
  - The plan's RED reason ("the result is shape `unparseable`, not `grok`") only holds if the test also asserts `shape == "grok"`. The text has that only as a parenthetical.
  - Repair: state both assertions (`r_deep == r_f0` and `r_deep["shape"] == "grok"`).
  - Alternatively, accept test 12 as a first-run pass and move it to the passing column (failing 177, passing 180; the census and v1.1 history line change with it).
  - Note: its RecursionError arm can never be RED at Task 7, because Task 5 already closed it. Its only kill for that property is E9, through Task 5 test 11.
  class: build
  quote: docs/01-plan/features/grok-codex-fallback.impl-plan.md › `on F0 (shape`
- The class-rule membership census for deviation 1 is a text grep, not an argument-surface census, yet the document calls the zero "load-bearing" on the argument surface.
  - `grep -ln -- '--log'` matches `h_mad_audit_cycle.py` only in comments (lines 533, 555, 563; it has no `"--log"` `add_argument`). It matches `h_mad_review_evidence.py` only in comments and help text (lines 126, 184); its log is the positional `log`.
  - The members come out right. I checked every importer of `h_mad_review_evidence`: only `h_mad_audit_cycle.py:17` and `h_mad_archreview_cycle.py:117`. I also checked the argument surfaces of the other line-parsing `json.loads` files (`audit_origins`, `context_budget`, `response_probe`, `telemetry`, `wire_registry`): none reads a dispatch transcript.
  - But a future transcript consumer that takes its path positionally, and never writes `--log`, escapes the stated criterion.
  - State the criterion as "reads a dispatch transcript (any argument name)" and cite the importer grep as the census.
  - The figures themselves reproduce at `HEAD`: 28 matching lines in 17 files, 5 files, 2 in both.
  class: measurement
  quote: docs/01-plan/features/grok-codex-fallback.impl-plan.md › `that zero follows from the argument surface, which is load-bearing`
- The design was not amended. It still says "`scan()` is untouched" at `grok-codex-fallback.design.md:877` (last design commit `40635c4f`, before this one), and its mutation total is still 43 in six specs.
  - The teammate's finding said the fix "has to go into both documents". v1.1 records a deviation and says the design "can be amended", but names no owner and no phase for doing it. A later audit reading design and plan together will see two binding documents that contradict each other.
  - Name when the design gets its v1.3 (before 5d dispatch), or say that the Deviations section overrides it for 5d/5e.
  class: measurement
  quote: docs/01-plan/features/grok-codex-fallback.impl-plan.md › `so the design can be amended to match`

## Nit
- Deviation 1 puts a paraphrase in quote marks: "the CLI prints F0's EVIDENCE line on the malformed fixture". The design's row at line 1731 actually reads "…and the CLI prints F0's `EVIDENCE:` line (row E4)". Quote it verbatim or drop the quote marks.
- The per-spec headers ("**`audit_cycle_grok.json`** — file `scripts/h_mad_audit_cycle.py`") read as a spec-level `file` key. The WR paragraph's "so `file` is per row (as `review_evidence_format.json` already does)" implies the other specs do it differently. In fact the harness requires `file` on every row (`h_mad_mutation_harness.py:290`), and all 907 committed rows carry it. Say that every row carries `file`.
- Task 10's grok arm does `printf '%s\n' "$grender" | tail -n "$n"`. On a window whose only events render nothing (for example only `available_commands`), this prints one blank line rather than nothing. Guard it with `[ -n "$grender" ]`.
- Task 17 leaves `$S` behind on any `FAIL:` path. The record says "`$S` is removed after the record is written", which only covers the pass path. State that a failed smoke keeps `$S` for the record.
- Task 17's worktree lookup takes `$2` of the `worktree ` line, which truncates a worktree path containing a space. Harmless for the current path.
- Task 16's `FLOOR: PASS` is printed even when the unguarded full-suite line above it is red. The prose says to read the suite verdict separately, but the AC bullet list puts "the script's last line is `FLOOR: PASS`" beside the suite requirement. Make it explicit that `FLOOR: PASS` does not certify the suite.
