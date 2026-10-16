PLAN-AUTHOR: DONE version=v1.1 path=/Users/kimhawk/orca/skills/docs/01-plan/features/agy-coder-fallback.plan.md lines=440 sha256=8827b5f43e90458b0183b720160044aa491e5228e369ff8cb577c1e38bc3d398

## Pre-write check
Before the first write the plan was at sha a212da32…, its newest VH entry was v1.0, and its mtime was 1792124262. I checked again just before the first Edit. HEAD is e7730f78.

## What changed (orchestrator decisions 1, 2, 3, 5 only)
1. **Header.** Re-sourced to spec v1.3 at e7730f78. The 17d73037 readings still hold for h-mad/: `git diff --stat 17d73037 e7730f78 -- h-mad` printed 0 lines.
2. **DO-1a / R-4 (decision 1).** I removed the "design keeps old stubs passing / or the spec relaxes" branch.
   - DO-1a now states the spec v1.3 rule: a missing field means judge-error, so optional fields are forbidden.
   - It also states the AC-3.2 exception (stub literals plus their constants, assertions byte-identical against a8d9ba99), and that ACTIVE_RE and the M-3 rows follow the line.
   - The design still owes a report of any unreachable gate test.
   - R-4 now covers the remaining risk, an edit that grows past the exception. Its mitigation is a per-file diff against a8d9ba99.
3. **FR-7 (decision 3).** Updated DO-3, stage 7, R-5 and the Deliverables row. The design chooses the mechanism. An add never removes or alters an entry. It is validated first, and a refused add leaves the store unchanged. A read-modify-write must state its lost-entry detection. The 5e-missing residual is kept.
4. **FR-6 (decision 3).** Updated stage 4, DO-5 and R-3. Moved names stay bound on the Codex gate module by import. Rows are re-pointed, then each holding spec runs ALL_CAUGHT. A zero-match row reads as mutation_unverified.
5. **FR-9 (decision 3).** Updated stage 6 and the halt-surface census.
   - Stage 6 adds the failure-recovery.md 5d row carve-out (token unchanged), the test_h_mad_agent_definitions.py `test_implementer_scopes_the_import_error_red_rule_to_wiring_tasks` pin, and the HALT_TOKENS pin.
   - The census paragraph now points to the spec's closed list of 4+1 surfaces instead of restating it.
6. **FR-1/FR-10 (decision 3).** Stage 1 now names the four pinned substrings in test_h_mad_state_fallback_agent.py. The rewrite keeps all four or changes the test in the same commit, and the test is never deleted. I dropped the line "spec does not list this surface".
7. **FR-10 gate (decision 5).** Added a Success Criteria bullet. A doc-derived test, mutation-checked, pins four needles:
   - SKILL.md Phase-5 section: `agy-authorship` and `h_mad_tdd_judge.py implementer`;
   - Exit-code dispatch section: `exec agy` as an implementer dispatch;
   - Phase-7 closure: the report carries `WARNING` lines;
   - agy-runtime.md §"The TDD gate": the new gate and AGY-GATE.

   Each has a baseline measured at e7730f78. I also added a Deliverables row. Its residual is that the pins check presence, not meaning. Since the plan now gates FR-10, the spec owes nothing for it.
8. **Owed section (decision 2).** All six v1.0 spec items are marked answered by v1.3 (e7730f78). The Design list gains the three v1.3-derived obligations.
9. **Next Steps.** The order is now audit cycle, then operator approval.
10. **Not done (decision 4).** AC-X was not touched.

## Measurements re-run, at HEAD e7730f78 (each command was run in this session)
- `git diff --stat 17d73037 e7730f78 -- h-mad | wc -l` → 0 lines.
- `grep -n -A 14 'def test_fallback_agent_description_states_the_four_facts' h-mad/tests/test_h_mad_state_fallback_agent.py` → the 4 substrings as stated.
- `grep -n '_safe_shell_command' h-mad/tests/test_h_mad_codex_tdd_gate_judge.py` → 2 matching lines.
- `grep -n 'red_wrong_reason' h-mad/references/failure-recovery.md` → the 5d row is present.
- `git ls-files -z h-mad | xargs -0 grep -l 'red_wrong_reason'` → 3 files: SKILL.md, failure-recovery.md, test_h_mad_wiring_task_shape_docs.py.
- `git ls-files -z h-mad/tests | xargs -0 grep -l 'Codex authors Phase 5'` → 2 files: test_grok_fallback_docs.py, test_h_mad_mutation_harness.py.
- FR-10 baselines, from an awk slice of SKILL.md from the heading to the next `#{1,3}` heading:
  - Phase-5 section: `agy-authorship` 0 lines and `h_mad_tdd_judge.py implementer` 0 lines;
  - Exit-code dispatch section: 1 `exec agy` line, the review/audit bullet;
  - `grep -c 'WARNING' h-mad/SKILL.md` → 0;
  - agy-runtime.md §"The TDD gate": `h-mad-agy-tdd-gate\|AGY-GATE` → 0 lines.
- I did not re-derive M-1..M-5. h-mad/ is unchanged since 17d73037, and none of them is over a class this revision touches.

## Tree contradictions / new findings
- **New finding, R-8.** The SKILL.md heading `### Codex authors Phase 5 — enforced, not just instructed` is pinned by two tests: test_grok_fallback_docs.py `PHASE5_HEADING` and test_h_mad_mutation_harness.py `skill.index("### Codex authors Phase 5")`. FR-10 makes that section implementer-neutral, and neither the spec nor plan v1.0 named these pins. R-8 now says to keep the heading or update both pins in the same commit, never deleting one.
- **v1.0 census was self-moving.** v1.0 counted `red_wrong_reason` tree-wide (4 files, the spec included). At e7730f78 that count would include this plan too. I re-scoped it to h-mad/ (3 files) and stated why (rule 12).

## Tool results
- `VERSION-HISTORY: OK … version=v1.1 line=440 placement=append`.
- `PRECHECK: PASS issues=0`. I kept these advisories deliberately:
  - PATH for `h-mad/hooks/h-mad-agy-tdd-gate.py` and `.agents/hooks.json`, which are new files;
  - COUNT L388 ("3 specs" beside an 8-row sentence, v1.0 text) and COUNT L418 (a six-item answered list rendered as sub-bullets), both false positives.

  The PATH advisories for h-mad-relative paths that I introduced were fixed by making the paths root-relative.
- `ACS: OK count=13 frs=9`. The 14th AC is AC-X, which cannot match the census grammar. That is a known gap, and per decision 4 it was not renamed.

## Owed by other documents
- **Spec:** nothing. Optional: the spec could give FR-10 its own AC mirroring the plan's Success Criteria bullet. It is not required, because the plan gates it.
- **Design:** DO-1..DO-6, plus:
  - choose the TDD-STATE shape with no optional peer fields;
  - report any unreachable gate test;
  - name the review_independence add mechanism and its lost-entry detection;
  - fix the moved-name set and keep those names bound on the Codex gate;
  - account for the two heading pins (R-8) if the FR-10 rewrite renames the heading.
