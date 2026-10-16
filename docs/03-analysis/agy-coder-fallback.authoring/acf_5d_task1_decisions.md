# agy-coder-fallback — 5d Task 1 decisions

## D5d-1 · item 15 literal is vacuous at RED (2026-10-17)
- **Found by:** Codex RED c1 (`STATUS: BLOCKED`, report `acf_5d_task1_red_c1.report.md`), confirmed
  by orchestrator re-run outside the sandbox: `113 failed, 9 passed` (6 pre-existing + 3 new).
- **Defect:** impl-plan v1.2 Task 1 item 15 asserts the `state-schema.md` `fallback_agent` row
  "contains `agy`". The row already carries `--surfaces agy,grok` (audit routing), so the
  assertion holds before any change.
- **Settlement:** item 15 asserts the row contains `agy is out too` — the FR-2 condition the design
  (§FR-1, "All four surfaces are rewritten to the FR-2 condition") pins on the description via
  item 14 and `test_fallback_agent_description_states_the_four_facts`. RED split back to the plan's
  114 F / 2 P. No other count, item or row changes.
- **Owed:** impl-plan item 15 wording to be aligned at the next impl-plan revision (one line).
- **Not a defect:** the sandbox-only teardown `ERROR` (leak-reaper `ps` → `PermissionError`)
  does not occur outside the sandbox.
