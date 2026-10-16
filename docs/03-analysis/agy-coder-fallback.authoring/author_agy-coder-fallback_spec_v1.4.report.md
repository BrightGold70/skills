SPEC-AUTHOR: DONE version=v1.4 path=/Users/kimhawk/orca/skills/docs/01-plan/features/agy-coder-fallback.spec.md lines=823 sha256=2f9991b21340088c6a60ada6fd4005b0a0dcf460f560da30747f4abc75800202

premises verified:
- Pre-write assert: sha256 231b46e7…, newest VH line v1.3, last commit e7730f78. Matched; no other writer seen.
- Assembler exit: `grep -n 'return 2\|exit 0 on PASS' h-mad/scripts/h_mad_assemble_tdd.py` shows the docstring "exit 0 on PASS, 2 on any HALT" and `return 2` after each `HALT` print. That confirms F1's premise.
- Wiring-check precedent: `h_mad_hook_wiring.py` prints `WIRING: FAIL` with return 0 and `WIRING: UNKNOWN reason=no_settings` with return 2.
- invariants.base.md: the §"Audit-gate signal discipline", §"Guard narrowing" and §"Incident replay" texts are quoted correctly in the spec.
- F2 probe, run with /opt/anaconda3/bin/python3. For `{"type":"string","format":"date-time"}`, `not-a-date` is accepted by Draft7Validator (True) and by _MiniDraft7 (True). With `FORMAT_CHECKER`, `not-a-date`, `2026-02-30T00:00:00Z` and `2026-10-16` are all refused. `rfc3339_validator` imports there. /opt/homebrew/bin/python3 has no jsonschema.
- _MiniDraft7's docstring says "`format` is ignored on purpose".
- Writer timestamp form: `h_mad_state_write.py` `_utc_now` uses `%Y-%m-%dT%H:%M:%SZ`.
- `grep -n -B3 '"format"' h_mad_state_schema.json` gives 3 matching lines: started_ts, owner_heartbeat_ts, halt_ts.
- FR-9 has no code implementation: `git ls-files h-mad | grep -v '\.md$' | xargs grep -ln 'red_wrong_reason\|missing.symbol'` returns 2 files, both tests (test_h_mad_wire_pin_gate.py, test_h_mad_wiring_task_shape_docs.py). No script hit.
- HemaSuite at 86c3d0c8d:
  - the analysis.md F-3 item exists and is tracked, and so is test_notebooklm_resolver.py;
  - the impl-plan WIRE-PIN table rows for T4, T5 and T6 W2 are present;
  - each `git log --oneline --grep` locator returns exactly 1 commit: 531a6296b (T4), 7aa0d9dec (T5), c2d671f6b (T6);
  - the source of the spec's existing "T4 GREEN was refused once" claim is report.md, not analysis.md.
- F6 tests read: test_format_state_line_emits_the_fallback_fold, test_fold_outcome_round_trips_through_the_gate_ere, test_fallback_tag, test_state_line_escape_and_blocker, test_state_line_empty_values_encode_as_percent, test_state_line_path_with_space_decodes.
- State-line shape: `format_state_line` emits `active codex-escape= blocker= records= fallback=`, then the records. In STATE_ACTIVE_RE, group(4) is the fallback capture.
- `bash -c '[[ a =~ (?:a) ]]'` gives rc=2 (POSIX ERE has no non-capturing group).

findings applied:
- F1, FR-5:
  - New exit-code table. WIRED and UNWIRED (all 7 reasons, no-hooks-file included) exit 0 on the check, and the assembler's agy_tdd_hook_unverified HALT exits 0. UNREADABLE exits 2, and a check that prints no token gives `HALT … check=no-token` with exit 2.
  - Residual: the existing assembler HALTs keep exit 2, and the docstring "2 on any HALT" is rewritten.
  - New AC-5.2. The old line "It exits 2, as every HALT already does" is removed.
- F2, FR-1: `.ts` is defined as RFC 3339 date-time. Refusal on both paths is the requirement. The mechanism is a design obligation with three options, plus the rfc3339-validator hazard. Residual covers the 3 existing date-time fields (they need a classify_store run if the mechanism is schema-wide). New AC-1.2.
- F3, FR-9: differential corpus over 4 cases (new-caller, missing-callee, both-missing, unrelated-import). The changed set must equal {new-caller}. New AC-9.2.
- F4, FR-9: incident replay of the 3 F-3 cases at their RED bases, with a wire-cut re-run and a citation of M4.1/M5.1/the WIRE 2 revert, stamped with both shas. New AC-9.3.
- F5, FR-8: new step 2a (forced handler timeout). The delay hook sleeps at least 2T against a configured timeout of T. Four outcomes are classified. Step 2 now settles two unknowns. The FR-5 re-run trigger includes 2a. New AC-8.2.
- F6: no contradiction with FR-3/AC-3.2. FR-3 had not listed the assertions over the real line, so I added them as placement constraints and extended AC-3.2 to test_h_mad_tdd_judge.py.

values swept (all run on the spec, which includes fenced blocks and tables):
- `grep -n -i 'three unknowns\|exits 2\|exit 2\|any HALT\|handler times out\|times out\|ISO-8601'`: every remaining hit is the new text.
- `grep -n -i 'exit\|\$?'` before editing: the only "exits 2" was the FR-5 line, now replaced.
- AC count: `h_mad_ac_census.py` gave `ACS: OK count=13 frs=9` before and `ACS: OK count=18 frs=9` after (+AC-1.2, 5.2, 8.2, 9.2, 9.3).
- VH test count: the v1.4 entry first said "five tests in test_h_mad_tdd_judge.py". Corrected to four after `awk` + `grep -o` over the FR-3 paragraph (6 distinct test names: 2 in the fallback_agent file, 4 in the judge file).

contradictions found:
- p2's F6 remedy suggests "header fields after fallback=<fold> and before record=". That breaks the byte-identical pin `" records=1 fallback=grok:1 record="`. The only header slot left is between `active ` and `codex-escape=`, and an alternation there shifts group(4). The free slot is per-record, between the state_file field and the tag. The spec now says so, and the plan's DO-1/DO-1a must not adopt p2's placement.
- My judgement call: no-hooks-file is treated as a verdict (exit 0), which diverges from h_mad_hook_wiring's no_settings → exit 2. The reason is stated in FR-5. The orchestrator can reverse it.

placeholder scan: clean. `PRECHECK: PASS issues=0`. Its 13 advisories are PATH not-yet-exist hits. Kept, because each is either a new file (h-mad-agy-tdd-gate.py, .agents/hooks.json) or a HemaSuite-relative path verified above (.codex/hooks.json, analysis.md, test_notebooklm_resolver.py).

owed by other documents:
- PLAN, F1: mirror the FR-5 exit table and AC-5.2. Tests must pin token and exit separately, and the docstring rewrite goes in h_mad_assemble_tdd.py.
- PLAN DO-4, F2: correct the premise (format is enforced on neither path). Pick a mechanism and cite the probe. Carry the rfc3339-validator hazard and the AC-1.2 package-absent fixture. If the mechanism is schema-wide, carry the classify_store run over the live state files.
- PLAN stage 6, F3/F4: corpus fixtures for the 4 cases, and the HemaSuite replay probe under docs/03-analysis/probes/agy-coder-fallback/ with both shas.
- PLAN stage 8, F5: step 2a with the delay hook, its deletion, the byte-identity check on .agents/hooks.json and outcome classification. A `timeout-allows` outcome triggers the agy-runtime.md residual and an operator question.
- PLAN DO-1/DO-1a, F6: adopt the spec's placement constraints (per-record slot; no header field after `fallback=`). Name the 6 tests.
- PLAN F7 and S1: not spec-owned, untouched.
- Later feature: classify the existing ASSEMBLE-TDD HALT reasons as verdict or operational (FR-5 residual).
