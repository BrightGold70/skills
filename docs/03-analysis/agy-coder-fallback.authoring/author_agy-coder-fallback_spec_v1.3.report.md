SPEC-AUTHOR: DONE version=v1.3 path=/Users/kimhawk/orca/skills/docs/01-plan/features/agy-coder-fallback.spec.md lines=620 sha256=231b46e7c1fdae2d2ed0d732d16139a324ded81528e41e6a24b5768ad35b744f

Pre-write assertion: the spec was at sha e18239c2…, its newest entry was v1.2, mtime 1792123677, and it was re-checked right before the first write. The tree has had no h-mad change since a8d9ba99 (`git diff --stat a8d9ba99 HEAD -- h-mad` is empty), so the readings stamped 17d73037 also hold at HEAD 4bcfb6f5.

## Premises verified
- `tests/test_h_mad_tdd_gate_judge.py` `_tree_b`: its default `state_line` is an old-shape `TDD-STATE: active …` line (`grep -n '_tree_b\|TDD-STATE'`).
- `tests/test_h_mad_tdd_gate_fallback_agent.py`: `PREFIX`/`RECORD` build the stub lines through `_stub_outcome`. Several of these tests assert non-judge-error kinds (`fallback-grok`, `fallback-invalid`), and `test_state_stub_fallback_field_is_judge_error[missing-field]` asserts judge-error for a missing field.
- `tests/test_h_mad_tdd_judge.py` `ACTIVE_RE` ends in `$` and is used with `fullmatch` (`sed -n 25,29p`).
- Gate test files: 7 files match `test_h_mad_tdd_gate_*.py`. Two of them contain `TDD-STATE: active` (`git ls-files h-mad/tests | grep … | xargs grep -l`). Note that `test_h_mad_tdd_judge.py` does not match that glob, so AC-3.2 never covered it.
- `h_mad_state_write.py`: `--set` is `action=append` of KEY=VALUE pairs, JSON-decoded, with no append-to-array operation (`sed -n 452,500p`).
- Mutation rows with `file` naming codex-tdd-gate: 62 rows across 5 specs (python json scan; this matches the plan's 62/5). The 19-row closure census is the plan's M-4. I did not re-derive it, and the spec does not restate it.
- `test_h_mad_codex_tdd_gate_judge.py` calls `module._safe_shell_command` at two sites (`grep -n`). From this I derived a new obligation: the moved names must stay bound on the Codex gate module.
- `references/failure-recovery.md`: there is a 5d row for `step5d:red_wrong_reason:<module>`, and its remedy states the old rule. `test_h_mad_wiring_task_shape_docs.py` `HALT_TOKENS` pins the token in both failure-recovery.md and SKILL.md.
- Rule-surface sweep: `git ls-files h-mad | xargs grep -ln -i 'missing.symbol\|tests the callee\|ImportError.*AttributeError\|AttributeError.*ImportError'` hits 6 files: SKILL.md, the prompt, failure-recovery.md, `test_h_mad_agent_definitions.py`, `test_h_mad_wire_pin_gate.py` and a fixture log.
  - `test_h_mad_agent_definitions.py` pins item 1's sentences, which is a new constraint.
  - h-mad has no tracked archive (`grep -c '^h-mad/archive/'` gives 0).
- `fallback_agent` descriptions: `h_mad_state_schema.json` says "read only when codex is out", and `state-schema.md` says "Optional Phase-5 author when Codex is out". `test_h_mad_state_fallback_agent.py` `test_fallback_agent_description_states_the_four_facts` pins four substrings, and that is a new constraint.
- `hooks/h-mad-tdd-gate.sh`: the `fallback-grok` text says "while codex is out". I stated this as a residual under byte-identity.
- `agy-runtime.md` `SessionStart`: 2 matching lines, one under §"Hooks" and one in the §"Construct mapping" `hook-event` row (awk heading scan). hooks.md has 3 matching lines, and agy is 1.3.6.
- `h_mad_ac_census.py` grammar is `^\s*-\s+(?:\*\*)?AC-(\d+)\.(\d+)…[:.]`. Before the change it printed `ACS: NONE count=0`.

## Findings applied
1. **AC-3.2 vs FR-3.** Decision: an **exception**, not "the design keeps old stubs passing". FR-3 now states that a missing state-line field refuses judge-error, which is the tree's existing rule for `fallback=` (missing-field fixture). Keeping old stubs passing would need optional fields, and that fails open.
   - The permitted edit is limited to the stub literals and the constants they are composed from. Assertions, kinds, reason substrings, names and ids stay byte-identical, checked by a diff against a8d9ba99.
   - A new fixture shows that a line in today's shape refuses judge-error.
   - `ACTIVE_RE` in `test_h_mad_tdd_judge.py` and the mutation rows that quote the line follow the line, outside AC-3.2.
   - This narrows "unmodified" to a precise invariant. It does not weaken the requirement, and the tree precedent forces it. The orchestrator can revert it if it prefers that the design try optional fields. I advise against that because it fails open.
2. **FR-7 append.** The spec now says the writer has no append. The requirement is "an add never removes or alters an entry, validated, refused means unchanged". The mechanism is a named design obligation: an append operation is preferred, and a read-modify-write must state how it detects a lost entry. The 5e missing-entry residual is stated. AC-7.1 gains the two-entry fixture. The D-11 bullet's "appends … with h_mad_state_write.py" is swept to "adds … by the Record mechanism".
3. **FR-6.** "Mutation rows stay green" became "re-pointed to the shared module in the same change, then ALL_CAUGHT". A zero-match row reads as mutation_unverified. The census is deferred to the plan's M-4. I also added that moved names stay bound on the Codex gate module, and AC-6.1 gained the re-pointed-rows clause.
4. **FR-9 / AC-9.1 / FR-10.** Added the failure-recovery.md 5d row carve-out with an unchanged token. The rule surfaces are closed: 4 today, and the GREEN variant is added as a 5th. The sweep command and its residual are stated, and two pinned tests are named. AC-9.1 and FR-10 were updated.
5. **FR-1 / FR-10 / AC-1.1.** Both `fallback_agent` description surfaces are rewritten to the both-peers condition. The four pinned substrings are named. The test is either kept or changed in the same commit, and never deleted. The hook-text residual is stated.
6. **§Owed.** Both `agy-runtime.md` surfaces are named, and they are corrected together.
7. **Census grammar.** All AC labels are now `- **AC-n.m:**`. `h_mad_ac_census.py <spec> <plan>` returns **`ACS: OK count=13 frs=9`** against **14 AC items**.
   - **The gap is AC-X.** Its id has no digits, so it cannot match the grammar `AC-(\d+)\.(\d+)`. Reformatting cannot close this.
   - I kept the id because the plan cites "AC-X" on 3 lines (`grep -n -o 'AC-X' plan`).
   - **Offered:** rename AC-X to a numbered id (for example under a cross-cutting FR), with the plan's 3 citations owed. This is the orchestrator's call, so I did not apply it.

## Values swept
- "append(s)": `grep -n -i 'append'` on the spec. The two orchestrator-append sites are changed. The ones left are FR-2's "` record=failed` appended" (output text) and the new "preferred … appends one entry".
- "stay(s) green" / "unmodified": `grep -n -i 'stay green\|stays green\|unmodified'`.
  - FR-6 now reads "existing tests pass unmodified", and the rows are re-pointed.
  - AC-3.2 was reworded.
  - AC-6.1 keeps "shell tests pass unmodified", which is true for tests.
  - The FR-2 and FR-9 "stays green" sites are unchanged and correct.
- `SessionStart`, `failure-recovery`, `fallback_agent`: grepped the whole spec. Every surface touched is listed above.
- AC labels: `grep -n '^- \*\*AC-'` gives 14 lines, and all of them are in the new form.
- Derived figures: none. No measured value changed. `JUDGE_BUDGET_S` 40.0, the floor of 60 and 1500 s are untouched.

## Contradictions found
- **Orchestrator brief vs tree (finding 7).** "Census count equals number of ACs" cannot hold while AC-X exists: 13 vs 14. Details are under Findings applied 7.
- **Plan R-4 / DO-1a** offered the design "keep old stubs passing". This spec now rules that out: missing field = judge-error. DO-1a should be closed accordingly. That edit belongs to the plan or the design, not to me.

## Placeholder scan
Clean: `PRECHECK: PASS issues=0`. I kept 8 PATH advisories deliberately. They are new files (`h-mad/hooks/h-mad-agy-tdd-gate.py`, `.agents/hooks.json`) or HemaSuite's `.codex/hooks.json`, which lives in another repository. `VERSION-HISTORY: OK version=v1.3 line=620 placement=append`.

## Owed by other documents
- **Plan:**
  - DO-1a / R-4 now resolve to the AC-3.2 exception (the stub literals are re-shaped, not kept). Close the "or the design keeps old stubs passing" branch.
  - The §"Owed by other documents" spec items are all answered in v1.3.
  - If AC-X is renamed, three plan lines cite it.
- **Design:**
  - Choose the review_independence add mechanism (FR-7).
  - Fix the moved-name set and keep those names bound on the Codex gate module (FR-6).
  - Choose the new TDD-STATE shape, with no optional peer fields (FR-3).
  - Report any gate test whose asserted outcome no new-shape stub can reach.
- **Observation, not applied:** FR-10 has no acceptance criterion of its own. Its SKILL.md §"Codex authors Phase 5" and §"Exit-code dispatch" rewrites, and the Phase-7 WARNING carry, are not gated by any AC.
