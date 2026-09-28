AUDIT-multi-host-runtime-impl-plan-v2-BEGIN
## Summary
The wire-pin parser reports `PASS tasks=19 wiring=3`, but the implementation plan still has three blocking consistency and test-discrimination gaps. Two smaller probe instructions can mismeasure the required baseline or real-root comparison.
Evidence: 14 files opened, 12 greps run; two targeted Python controls and the wire-pin gate executed. 🌱 graft saved ~68,095 tokens (~$0.04) this turn, 1 call.

## Must-fix
- Task 0 still puts the calibration sidecar after the design gate, while the binding design makes that committed sidecar a prerequisite to clearing the gate. Deviation 7 acknowledges the conflict but leaves no reconciled implementation order; revise the design's order or obtain the stated orchestrator decision before treating 5c as executable.
  class: build
  quote: docs/02-design/features/multi-host-runtime.design.md › `The design gate cannot clear under this order until it does.`
  quote: docs/01-plan/features/multi-host-runtime.impl-plan.md › `Placing the three files at 5c is the orchestrator's decision, and this plan cannot move work`
- The required codex R14(a) rehearsal cannot yield its prescribed `FAIL` from a literal multiline command: the codex reader takes only the next log line after `exec` and requires that line to end with `in <cwd>`. A controlled regex check on the first line of the specified command returned false; the plan itself predicts `UNVERIFIED` and halts, so `REHEARSAL: PASS n=92` has no executable path until the design changes the reader, fixture, or expectation.
  class: build
  quote: docs/02-design/features/multi-host-runtime.design.md › ``(a) `echo x # c`, a newline, then a script run → `FAIL``
  quote: docs/01-plan/features/multi-host-runtime.impl-plan.md › `If codex writes that command's newline`
- Newly added, initially green guards have no specified loss-of-behavior run. Task 14 calls the four codex/agy routing nodes guards although they pass before its change and has no mutation rows for them; Task 2's source-scanner guards likewise have no named mutation. Under the base Test discrimination invariant, observe each guard fail when its subject is removed or permissively stubbed before claiming it is enforced.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.impl-plan.md › `Passing now, and kept as guards: the four codex/agy ids`

## Should-fix
- Spell out expansion of `~` in Task 16's B2 `--skills-link` argument. `subprocess.run` with an argv list does not invoke a shell, and the current install checker constructs `Path(args.skills_link)` without `expanduser`; passing the printed argument literally checks a relative `~/.claude` path instead of the real default root, invalidating arm B's closed diff.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.impl-plan.md › `B2 (`--skills-link ~/.claude/skills/h-mad --repo /Users/kimhawk/orca/skills`)`
- Task 1's suite-baseline command keeps only the last three pytest output lines while requiring every failing node id and reason. Preserve the full output or parse all `FAILED`/`ERROR` lines before recording the baseline, since a second or later failure can be silently omitted.
  class: measurement
  quote: docs/01-plan/features/multi-host-runtime.impl-plan.md › `2>&1 | tail -3`.

## Nit
None
AUDIT-multi-host-runtime-impl-plan-v2-END
