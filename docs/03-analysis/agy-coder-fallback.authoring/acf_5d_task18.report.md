# Task 18 — pre-merge re-measurement

Repository / working directory: `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback`

Branch: `feature/agy-coder-fallback`

Measured HEAD: `3236ade63000759101b8d5de7e4bdc1558329b73`

Result: AC-9.1 passes; line=10 files, joined=10 files, union=10 files, unparsed=0. Every union hit was read in context; all six live rule copies contain the complete carve-out. Other hits are tests, mutation controls or captured historical evidence. No review-independence hit states an agy-only trigger.

Only repository file authored by this task: `docs/03-analysis/probes/agy-coder-fallback/fr9_union_sweep.py`. No production/test file edits, no commit, and no full suite. The coordinator owns committing the SHA-stamped readings. An unrelated concurrent `fr9_incident_replay.py` appeared while this task ran; it was left untouched.

## Probe source summary

New probe: 204 lines; SHA-256 `e65b1c8788253b635c9a25634305c66460e53e6bd40105e2140903fbd78aab6b`. Stdlib only. Uses `git ls-files -z -- h-mad/`, scans all tracked working-tree bytes, applies the plan's case-insensitive regex to physical lines, parses each Python str constant using ast, tokenizes COMMENT independently, and collapses whitespace in those readings plus whole non-Python texts. No exclusions for test fixtures or mutation payloads. Parse/tokenize errors count by distinct file and produce FAIL with exit 0. Unreadable input/git errors exit 2.

The in-source review ledger records the manual classification of every hit and binds it to a SHA-256 of the reviewed bytes. Unknown, changed or missing hits fail for renewed manual reading. No numeric census expectation is tuned. The control invalidates one digest and follows that same failure path. This records a hand review; it is not an automatic semantic classifier. Runtime interpolation remains outside the regex/constant sweep's reach.

Invocation from repository root: `/Users/kimhawk/.agents/skills/h-mad/bin/hmad-dispatch run --timeout 60 -- /opt/anaconda3/bin/python3 docs/03-analysis/probes/agy-coder-fallback/fr9_union_sweep.py`.

472 tracked files examined, including 241 Python files. ast-string hits: 5 files; comment hits: 0; normalized non-Python text hits: 5; joined total: 10. Line-minus-joined and joined-minus-line are both empty. No file needs an unparsed-file manual exception.

## Census comparison against the requested later records

Task 0 probes were run unchanged with no expectation overrides. Their original FAIL tokens are preserved below; exit codes were all 0. Numeric comparisons for this gate use the Task 3 record, moved-rows=0, and D5d-6 as requested.

| Reading | Shipped value | Requested comparison |
|---|---|---|
| M-2 Claude hook | 62 rows / 6 specs | Exactly Task 3 record |
| M-2 judge | 41 rows / 10 specs | Exactly Task 3 record |
| M-2 Codex hook | 35 rows / 4 specs | Record current value; extraction changes ownership |
| M-2 assembler | 65 rows / 8 specs | Record current value |
| M-2 Phase-7 preconditions | 16 rows / 3 specs | Record current value |
| M-2 hook wiring | 18 rows / 2 specs | Record current value |
| M-2 state writer | 26 rows / 5 specs | Record current value |
| M-2 target identity | 46 rows / 5 specs | Record current value |
| M-3 | 10 rows / 5 specs | Exactly Task 3 record; by-spec 5+1+1+2+1 |
| FR-3 _read_state | 10 | Exactly Task 3 record |
| FR-3 authorship boundary / rows | absent / 0 | Exactly Task 3 record; old block was replaced |
| FR-3 _active_records | 1 | Unchanged region |
| FR-3 format_state_line | 5 | Exactly Task 3 record |
| FR-3 total / hook / judge | 16 / 10 / 6 | Sum of above regions |
| M-4 Codex rows inside moved spans | 0 | Required moved-rows=0: MATCH |
| M-4 Codex absent / non-unique anchors | 0 / 0 | No anchor drift among current Codex rows |
| Prompt doc pins | 27 literals / 9 files | D5d-6: MATCH |
| State-line / four-pattern files | 7 / 12 | Current readings; old 6 / 7 expectations retained |
| Inventory total / a / b / c / d | 58 / 11 / 5 / 1 / 41 | Original probe PASS |

Task 3 reference: `docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task3_decisions.md` (post-Task-3 reading a9102c1d). D5d-6 reference: `docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task15_decisions.md` explicitly records 27/9; its four added literals come from the Task-13 canonical-copy test. No hand pin is reported missing and no boundary/negative pin failed in this run.

M-4 limitation made explicit: the unchanged probe cannot rediscover its old local definition closure after extraction, so it prints an empty closure and 15 missing local moved definitions. Its measured moved-rows=0 satisfies this task's stated value; a supplemental read independently confirms the full fixed 25-name set exists in `scripts/h_mad_target_identity.py`. This gate does not claim a new mutation execution or substitute the old 31-row expectation. No expectation or span was widened.

State-line membership changed through the feature: the first query now also names `test_h_mad_tdd_gate_peers.py`; the four-pattern query also reaches peer/implementer tests, the new peer mutation spec, and SKILL.md. All memberships are printed verbatim below; this is recorded drift, not silently re-baselined.

## fr9_union_sweep.py — full output

Working directory: `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback`

Command: `/Users/kimhawk/.agents/skills/h-mad/bin/hmad-dispatch run --timeout 60 -- /opt/anaconda3/bin/python3 docs/03-analysis/probes/agy-coder-fallback/fr9_union_sweep.py`

Exit code: 0

````text
HEAD: 3236ade63000759101b8d5de7e4bdc1558329b73
ROOT: /Users/kimhawk/orca/workspaces/skills/agy-coder-fallback
REGEX: missing.symbol|tests the callee|ImportError.*AttributeError|AttributeError.*ImportError (case-insensitive)
TRACKED: files=472 python=241
READING: line=10 strings=5 comments=0 text=5 joined=10 union=10 unparsed=0
LINE-MINUS-JOINED: []
JOINED-MINUS-LINE: []
UNION: h-mad/SKILL.md
HIT[line]: h-mad/SKILL.md:500-500:   **The third task shape is `wiring`, and counts cannot gate it.** When the deliverable is a connection rather than new behaviour, carry the task's `WIRE:` and `WIRE-PIN:` lines from the impl-plan into the dispatch, and require the RED report to give the **failure mode per test, not only the count**. A test whose RED is an `ImportError`/`AttributeError`/`NameError` — the callee missing — is not a wire test: it fails for the callee's absence and goes green the moment the callee exists, wired or not. The `WIRE-PIN` test's RED must be an assertion about the **caller's** observable behaviour (the call was not made; the value did not propagate). The traceback already carries this, so the check costs nothing. A `WIRE-PIN` whose RED reason is a missing symbol → halt `step5d:red_wrong_reason:<module>`. A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails. A `wiring` task dispatched with no `WIRE-PIN` at all → halt `step5d:no_wire_pin:<module>`; do not let 5e establish GREEN for it, because nothing downstream can see the wire (`invariants.base.md` §"Connection enforcement").
HIT[text]: h-mad/SKILL.md:1-3431: whitespace-collapsed whole-file text matches
REVIEW: OK sha256=f8413f73eb7d155d1b6a49bfa36ff446fbae1c63cf3424b7bc1ee139bf36308f :: RULE WITH CARVE-OUT: line 500 includes caller-created, callee-resolves, name-both and call-only wire-cut conditions.
UNION: h-mad/references/codex-implementer-prompt.md
HIT[line]: h-mad/references/codex-implementer-prompt.md:60-60: 1. For each FAILING test: does the failure message name the property under test? For a `wiring` task (a dispatch carrying `WIRE:`/`WIRE-PIN:` — see below), an `ImportError`/`AttributeError`/`NameError` standing in for a behavioural assertion is not a RED — it is an unwritten test. For a task that introduces a NEW symbol, the first RED is `AttributeError`/`ImportError` **by construction** (the symbol does not exist yet); that is acceptable only when the same test also asserts the behaviour that must hold once the symbol exists, so it stays meaningful after GREEN. Say which case each failing test is. A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails.
HIT[line]: h-mad/references/codex-implementer-prompt.md:68-68: **If the dispatch carries a `WIRE:` / `WIRE-PIN:` line, this is a `wiring` task and the pin is its single load-bearing test.** The pin must fail because the **caller** does not reach the callee — the call was not made, the value did not propagate — and NOT because the callee is missing. An `ImportError`/`AttributeError`/`NameError` RED on the pin means the pin is testing the callee, so it will go green the moment the callee exists whether or not anything wires it; report that and stop rather than accepting it. A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails. State the pin's failure **mode**, quoted, not just its pass/fail count. In GREEN, the pin must still fail if the connection alone is deleted with the callee left in place — if it does not, say so; do not repair it silently.
HIT[line]: h-mad/references/codex-implementer-prompt.md:72-72: For GREEN phase (5e): implement the minimal code to make the failing tests pass. Verify GREEN by running `pytest <test_path> -v`. Then refactor if helpful, keeping tests green. A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails.
HIT[text]: h-mad/references/codex-implementer-prompt.md:1-150: whitespace-collapsed whole-file text matches
REVIEW: OK sha256=98cbbab1bb1e9b6fef835ec7f0d1e8d75f781bf883720c8904609d7c8711ae49 :: RULE WITH CARVE-OUT: all three copies, lines 60, 68 and 72, carry the full three-sentence block individually.
UNION: h-mad/references/failure-recovery.md
HIT[line]: h-mad/references/failure-recovery.md:36-36: | 5d | `WIRE-PIN` test's RED is a missing symbol, not caller behaviour | `step5d:red_wrong_reason:<module>` | "An `ImportError`/`AttributeError`/`NameError` RED means the pin tests the callee, so it goes green the moment the callee exists — wired or not. Re-dispatch the pin as an assertion on the caller's observable behaviour (the call was not made; the value did not propagate). Counts cannot catch this; only the failure mode can. A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails." |
HIT[text]: h-mad/references/failure-recovery.md:1-100: whitespace-collapsed whole-file text matches
REVIEW: OK sha256=e08033f2e9ac2aa233486e740d889cdf1b27085f0764b37b10e1f2c9904030fe :: RULE WITH CARVE-OUT: the line 36 remedy contains the full block.
UNION: h-mad/scripts/h_mad_assemble_tdd.py
HIT[string]: h-mad/scripts/h_mad_assemble_tdd.py:477-483: The WIRE-PIN is this task's single load-bearing test. Its RED must be an assertion about the CALLER's observable behaviour, never a missing symbol. A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails.
HIT[line]: h-mad/scripts/h_mad_assemble_tdd.py:480-480:             "A missing-symbol RED on the pin is valid **only** when the missing symbol is "
REVIEW: OK sha256=ecb14c4aa31e42254c886869902b625f3b027daaecc6c08a5bd3e7068a798468 :: RULE WITH CARVE-OUT: the joined wiring header at lines 477-483 contains the full block after its general prohibition.
UNION: h-mad/tests/fixtures/codex-text-8-exec.log
HIT[line]: h-mad/tests/fixtures/codex-text-8-exec.log:974-974: fails on `len(calls) == 2` — never an `ImportError`/`AttributeError`. At GREEN the reload
HIT[text]: h-mad/tests/fixtures/codex-text-8-exec.log:1-1910: whitespace-collapsed whole-file text matches
REVIEW: OK sha256=cc0843bf8790c04f83c5fd4a0f06247f165b92abbb733873954200ac7252055b :: NO GENERAL RULE: line 974 describes one existing-caller recorder test's len(calls) assertion in captured output, not universal RED policy.
UNION: h-mad/tests/mutation-specs/new_caller_carveout_copies.json
HIT[line]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:23-23:       "find": "Say which case each failing test is. A missing-symbol RED on the pin is valid **only** when",
HIT[line]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:24-24:       "replace": "Say which case each failing test is. A missing-symbol RED on the pin is valid when",
HIT[line]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:32-32:       "find": "report that and stop rather than accepting it. A missing-symbol RED on the pin is valid **only** when",
HIT[line]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:33-33:       "replace": "report that and stop rather than accepting it. A missing-symbol RED on the pin is valid when",
HIT[line]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:41-41:       "find": "halt `step5d:red_wrong_reason:<module>`. A missing-symbol RED on the pin is valid **only** when",
HIT[line]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:42-42:       "replace": "halt `step5d:red_wrong_reason:<module>`. A missing-symbol RED on the pin is valid when",
HIT[line]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:50-50:       "find": "only the failure mode can. A missing-symbol RED on the pin is valid **only** when",
HIT[line]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:51-51:       "replace": "only the failure mode can. A missing-symbol RED on the pin is valid when",
HIT[line]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:59-59:       "find": "The WIRE-PIN is this task's single load-bearing test. Its RED must be \"\n            \"an assertion about the CALLER's observable behaviour, never a missing \"\n            \"symbol. \"\n            \"A missing-symbol RED on the pin is valid **only** when",
HIT[line]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:60-60:       "replace": "The WIRE-PIN is this task's single load-bearing test. Its RED must be \"\n            \"an assertion about the CALLER's observable behaviour, never a missing \"\n            \"symbol. \"\n            \"A missing-symbol RED on the pin is valid when",
HIT[line]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:68-68:       "find": "keeping tests green. A missing-symbol RED on the pin is valid **only** when",
HIT[line]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:69-69:       "replace": "keeping tests green. A missing-symbol RED on the pin is valid when",
HIT[line]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:77-77:       "find": "only the failure mode can. A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails.",
HIT[line]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:78-78:       "replace": "only the failure mode can. A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails.",
HIT[line]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:86-86:       "find": "only the failure mode can. A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails.",
HIT[line]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:87-87:       "replace": "only the failure mode can. A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the callee only, keep the caller, and confirm the pin fails.",
HIT[text]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:1-109: whitespace-collapsed whole-file text matches
REVIEW: OK sha256=de2c68a37ae31c71117e5c54535989cb0a704062b60ace56d206a69d13848b3b :: MUTATION DATA: find/replace pairs deliberately damage individual carve-out sentences; these are negative controls, not operative rules.
UNION: h-mad/tests/test_h_mad_agent_definitions.py
HIT[line]: h-mad/tests/test_h_mad_agent_definitions.py:77-77:     assert "the first RED is `AttributeError`/`ImportError` **by construction**" in body
HIT[string]: h-mad/tests/test_h_mad_agent_definitions.py:77-77: the first RED is `AttributeError`/`ImportError` **by construction**
REVIEW: OK sha256=86b40df7c613ec0b7d80267e581f884ec74b50e4df30347801cbb90854c9b8f8 :: NO BLANKET RULE: line 77 pins new-symbol import-shaped RED wording; it does not forbid the new-caller carve-out.
UNION: h-mad/tests/test_h_mad_new_caller_carveout_copies.py
HIT[line]: h-mad/tests/test_h_mad_new_caller_carveout_copies.py:17-17:     "A missing-symbol RED on the pin is valid **only** when the missing symbol is "
HIT[string]: h-mad/tests/test_h_mad_new_caller_carveout_copies.py:17-20: A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails.
REVIEW: OK sha256=61f337263e106b5451506642ec76f3ea78267faf3c48725288d725a32ee3e66d :: RULE WITH CARVE-OUT: CANONICAL at lines 16-21 contains the full block; the six locators require each individual copy.
UNION: h-mad/tests/test_h_mad_wire_pin_gate.py
HIT[string]: h-mad/tests/test_h_mad_wire_pin_gate.py:576-582: Call main with the additive CLI namespace expected by Task 5. The RED phase must not add argparse or production wiring. Injecting the future namespace lets these tests reach the existing caller and fail on the observable absence of the register call, rather than on an import-shaped missing symbol or an argparse setup detail.
HIT[line]: h-mad/tests/test_h_mad_wire_pin_gate.py:581-581:     missing symbol or an argparse setup detail.
REVIEW: OK sha256=c475e310a0802e46b390f5bacf62d8b6f3a985987c19a2baf135ceb0873a5112 :: NO GENERAL RULE: lines 576-582 explain scaffolding for an existing caller's registration assertion; they prescribe no universal halt.
UNION: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py
HIT[line]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:16-16:         "name": "new-caller", "missing_symbol": "new_caller", "role": "caller",
HIT[string]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:16-16: missing_symbol
HIT[line]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:21-21:         "name": "missing-callee", "missing_symbol": "callee", "role": "callee",
HIT[string]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:21-21: missing_symbol
HIT[line]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:26-26:         "name": "both-missing", "missing_symbol": "new_caller", "role": "caller",
HIT[string]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:26-26: missing_symbol
HIT[line]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:30-30:         "name": "unrelated-import", "missing_symbol": "fr9_unrelated_dependency",
HIT[string]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:30-30: missing_symbol
HIT[line]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:39-39:         "name": "other-symbol", "missing_symbol": "other_symbol", "role": "other",
HIT[string]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:39-39: missing_symbol
HIT[line]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:48-48: MISSING_ERRORS = {"ImportError", "ModuleNotFoundError", "AttributeError", "NameError"}
HIT[line]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:52-52:     """Before FR-9: every missing-symbol RED on the wiring pin is a halt."""
HIT[string]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:52-52: Before FR-9: every missing-symbol RED on the wiring pin is a halt.
HIT[line]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:57-57:     """FR-9: the missing symbol must be the new caller AND the callee resolve."""
HIT[string]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:57-57: FR-9: the missing symbol must be the new caller AND the callee resolve.
HIT[line]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:99-99:             r"^E\s+((?:ImportError|ModuleNotFoundError|AttributeError|NameError):[^\n]*)$",
HIT[string]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:99-99: ^E\s+((?:ImportError|ModuleNotFoundError|AttributeError|NameError):[^\n]*)$
HIT[line]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:103-103:             f"{declaration['name']}: expected one missing-symbol exception line\n{output}"
HIT[string]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:103-103: : expected one missing-symbol exception line
HIT[line]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:107-107:             "name": declaration["name"], "missing_symbol": declaration["missing_symbol"],
HIT[string]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:107-107: missing_symbol
HIT[string]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:107-107: missing_symbol
HIT[line]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:135-135:     assert f"'{declaration['missing_symbol']}'" in row["exception_line"], (
HIT[string]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:135-135: missing_symbol
HIT[line]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:136-136:         f"{row['name']}: exception must name the declared missing symbol: {row['exception_line']}"
HIT[string]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:136-136: : exception must name the declared missing symbol:
HIT[line]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:159-159:     assert "the missing symbol is the caller the task creates" in CANONICAL, (
HIT[string]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:159-159: the missing symbol is the caller the task creates
REVIEW: OK sha256=a093daa2d47684990ca0a3911010baa877c7f279161153ee1b68825916785837 :: RULE WITH CARVE-OUT: new_rule at lines 56-62 requires caller AND callee resolution; old_rule is explicitly Before FR-9 for comparison. Other hits are case keys, exception recognition and assertions.
PROBE: PASS
````

## fr9_union_sweep.py --control — full output

Working directory: `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback`

Command: `/Users/kimhawk/.agents/skills/h-mad/bin/hmad-dispatch run --timeout 60 -- /opt/anaconda3/bin/python3 docs/03-analysis/probes/agy-coder-fallback/fr9_union_sweep.py --control`

Exit code: 0

````text
HEAD: 3236ade63000759101b8d5de7e4bdc1558329b73
ROOT: /Users/kimhawk/orca/workspaces/skills/agy-coder-fallback
REGEX: missing.symbol|tests the callee|ImportError.*AttributeError|AttributeError.*ImportError (case-insensitive)
TRACKED: files=472 python=241
READING: line=10 strings=5 comments=0 text=5 joined=10 union=10 unparsed=0
LINE-MINUS-JOINED: []
JOINED-MINUS-LINE: []
CONTROL: invalidated hand-review digest for h-mad/SKILL.md
UNION: h-mad/SKILL.md
HIT[line]: h-mad/SKILL.md:500-500:   **The third task shape is `wiring`, and counts cannot gate it.** When the deliverable is a connection rather than new behaviour, carry the task's `WIRE:` and `WIRE-PIN:` lines from the impl-plan into the dispatch, and require the RED report to give the **failure mode per test, not only the count**. A test whose RED is an `ImportError`/`AttributeError`/`NameError` — the callee missing — is not a wire test: it fails for the callee's absence and goes green the moment the callee exists, wired or not. The `WIRE-PIN` test's RED must be an assertion about the **caller's** observable behaviour (the call was not made; the value did not propagate). The traceback already carries this, so the check costs nothing. A `WIRE-PIN` whose RED reason is a missing symbol → halt `step5d:red_wrong_reason:<module>`. A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails. A `wiring` task dispatched with no `WIRE-PIN` at all → halt `step5d:no_wire_pin:<module>`; do not let 5e establish GREEN for it, because nothing downstream can see the wire (`invariants.base.md` §"Connection enforcement").
HIT[text]: h-mad/SKILL.md:1-3431: whitespace-collapsed whole-file text matches
REVIEW: NEEDS_HAND_READING sha256=f8413f73eb7d155d1b6a49bfa36ff446fbae1c63cf3424b7bc1ee139bf36308f :: RULE WITH CARVE-OUT: line 500 includes caller-created, callee-resolves, name-both and call-only wire-cut conditions.
UNION: h-mad/references/codex-implementer-prompt.md
HIT[line]: h-mad/references/codex-implementer-prompt.md:60-60: 1. For each FAILING test: does the failure message name the property under test? For a `wiring` task (a dispatch carrying `WIRE:`/`WIRE-PIN:` — see below), an `ImportError`/`AttributeError`/`NameError` standing in for a behavioural assertion is not a RED — it is an unwritten test. For a task that introduces a NEW symbol, the first RED is `AttributeError`/`ImportError` **by construction** (the symbol does not exist yet); that is acceptable only when the same test also asserts the behaviour that must hold once the symbol exists, so it stays meaningful after GREEN. Say which case each failing test is. A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails.
HIT[line]: h-mad/references/codex-implementer-prompt.md:68-68: **If the dispatch carries a `WIRE:` / `WIRE-PIN:` line, this is a `wiring` task and the pin is its single load-bearing test.** The pin must fail because the **caller** does not reach the callee — the call was not made, the value did not propagate — and NOT because the callee is missing. An `ImportError`/`AttributeError`/`NameError` RED on the pin means the pin is testing the callee, so it will go green the moment the callee exists whether or not anything wires it; report that and stop rather than accepting it. A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails. State the pin's failure **mode**, quoted, not just its pass/fail count. In GREEN, the pin must still fail if the connection alone is deleted with the callee left in place — if it does not, say so; do not repair it silently.
HIT[line]: h-mad/references/codex-implementer-prompt.md:72-72: For GREEN phase (5e): implement the minimal code to make the failing tests pass. Verify GREEN by running `pytest <test_path> -v`. Then refactor if helpful, keeping tests green. A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails.
HIT[text]: h-mad/references/codex-implementer-prompt.md:1-150: whitespace-collapsed whole-file text matches
REVIEW: OK sha256=98cbbab1bb1e9b6fef835ec7f0d1e8d75f781bf883720c8904609d7c8711ae49 :: RULE WITH CARVE-OUT: all three copies, lines 60, 68 and 72, carry the full three-sentence block individually.
UNION: h-mad/references/failure-recovery.md
HIT[line]: h-mad/references/failure-recovery.md:36-36: | 5d | `WIRE-PIN` test's RED is a missing symbol, not caller behaviour | `step5d:red_wrong_reason:<module>` | "An `ImportError`/`AttributeError`/`NameError` RED means the pin tests the callee, so it goes green the moment the callee exists — wired or not. Re-dispatch the pin as an assertion on the caller's observable behaviour (the call was not made; the value did not propagate). Counts cannot catch this; only the failure mode can. A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails." |
HIT[text]: h-mad/references/failure-recovery.md:1-100: whitespace-collapsed whole-file text matches
REVIEW: OK sha256=e08033f2e9ac2aa233486e740d889cdf1b27085f0764b37b10e1f2c9904030fe :: RULE WITH CARVE-OUT: the line 36 remedy contains the full block.
UNION: h-mad/scripts/h_mad_assemble_tdd.py
HIT[string]: h-mad/scripts/h_mad_assemble_tdd.py:477-483: The WIRE-PIN is this task's single load-bearing test. Its RED must be an assertion about the CALLER's observable behaviour, never a missing symbol. A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails.
HIT[line]: h-mad/scripts/h_mad_assemble_tdd.py:480-480:             "A missing-symbol RED on the pin is valid **only** when the missing symbol is "
REVIEW: OK sha256=ecb14c4aa31e42254c886869902b625f3b027daaecc6c08a5bd3e7068a798468 :: RULE WITH CARVE-OUT: the joined wiring header at lines 477-483 contains the full block after its general prohibition.
UNION: h-mad/tests/fixtures/codex-text-8-exec.log
HIT[line]: h-mad/tests/fixtures/codex-text-8-exec.log:974-974: fails on `len(calls) == 2` — never an `ImportError`/`AttributeError`. At GREEN the reload
HIT[text]: h-mad/tests/fixtures/codex-text-8-exec.log:1-1910: whitespace-collapsed whole-file text matches
REVIEW: OK sha256=cc0843bf8790c04f83c5fd4a0f06247f165b92abbb733873954200ac7252055b :: NO GENERAL RULE: line 974 describes one existing-caller recorder test's len(calls) assertion in captured output, not universal RED policy.
UNION: h-mad/tests/mutation-specs/new_caller_carveout_copies.json
HIT[line]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:23-23:       "find": "Say which case each failing test is. A missing-symbol RED on the pin is valid **only** when",
HIT[line]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:24-24:       "replace": "Say which case each failing test is. A missing-symbol RED on the pin is valid when",
HIT[line]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:32-32:       "find": "report that and stop rather than accepting it. A missing-symbol RED on the pin is valid **only** when",
HIT[line]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:33-33:       "replace": "report that and stop rather than accepting it. A missing-symbol RED on the pin is valid when",
HIT[line]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:41-41:       "find": "halt `step5d:red_wrong_reason:<module>`. A missing-symbol RED on the pin is valid **only** when",
HIT[line]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:42-42:       "replace": "halt `step5d:red_wrong_reason:<module>`. A missing-symbol RED on the pin is valid when",
HIT[line]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:50-50:       "find": "only the failure mode can. A missing-symbol RED on the pin is valid **only** when",
HIT[line]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:51-51:       "replace": "only the failure mode can. A missing-symbol RED on the pin is valid when",
HIT[line]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:59-59:       "find": "The WIRE-PIN is this task's single load-bearing test. Its RED must be \"\n            \"an assertion about the CALLER's observable behaviour, never a missing \"\n            \"symbol. \"\n            \"A missing-symbol RED on the pin is valid **only** when",
HIT[line]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:60-60:       "replace": "The WIRE-PIN is this task's single load-bearing test. Its RED must be \"\n            \"an assertion about the CALLER's observable behaviour, never a missing \"\n            \"symbol. \"\n            \"A missing-symbol RED on the pin is valid when",
HIT[line]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:68-68:       "find": "keeping tests green. A missing-symbol RED on the pin is valid **only** when",
HIT[line]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:69-69:       "replace": "keeping tests green. A missing-symbol RED on the pin is valid when",
HIT[line]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:77-77:       "find": "only the failure mode can. A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails.",
HIT[line]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:78-78:       "replace": "only the failure mode can. A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails.",
HIT[line]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:86-86:       "find": "only the failure mode can. A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails.",
HIT[line]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:87-87:       "replace": "only the failure mode can. A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the callee only, keep the caller, and confirm the pin fails.",
HIT[text]: h-mad/tests/mutation-specs/new_caller_carveout_copies.json:1-109: whitespace-collapsed whole-file text matches
REVIEW: OK sha256=de2c68a37ae31c71117e5c54535989cb0a704062b60ace56d206a69d13848b3b :: MUTATION DATA: find/replace pairs deliberately damage individual carve-out sentences; these are negative controls, not operative rules.
UNION: h-mad/tests/test_h_mad_agent_definitions.py
HIT[line]: h-mad/tests/test_h_mad_agent_definitions.py:77-77:     assert "the first RED is `AttributeError`/`ImportError` **by construction**" in body
HIT[string]: h-mad/tests/test_h_mad_agent_definitions.py:77-77: the first RED is `AttributeError`/`ImportError` **by construction**
REVIEW: OK sha256=86b40df7c613ec0b7d80267e581f884ec74b50e4df30347801cbb90854c9b8f8 :: NO BLANKET RULE: line 77 pins new-symbol import-shaped RED wording; it does not forbid the new-caller carve-out.
UNION: h-mad/tests/test_h_mad_new_caller_carveout_copies.py
HIT[line]: h-mad/tests/test_h_mad_new_caller_carveout_copies.py:17-17:     "A missing-symbol RED on the pin is valid **only** when the missing symbol is "
HIT[string]: h-mad/tests/test_h_mad_new_caller_carveout_copies.py:17-20: A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails.
REVIEW: OK sha256=61f337263e106b5451506642ec76f3ea78267faf3c48725288d725a32ee3e66d :: RULE WITH CARVE-OUT: CANONICAL at lines 16-21 contains the full block; the six locators require each individual copy.
UNION: h-mad/tests/test_h_mad_wire_pin_gate.py
HIT[string]: h-mad/tests/test_h_mad_wire_pin_gate.py:576-582: Call main with the additive CLI namespace expected by Task 5. The RED phase must not add argparse or production wiring. Injecting the future namespace lets these tests reach the existing caller and fail on the observable absence of the register call, rather than on an import-shaped missing symbol or an argparse setup detail.
HIT[line]: h-mad/tests/test_h_mad_wire_pin_gate.py:581-581:     missing symbol or an argparse setup detail.
REVIEW: OK sha256=c475e310a0802e46b390f5bacf62d8b6f3a985987c19a2baf135ceb0873a5112 :: NO GENERAL RULE: lines 576-582 explain scaffolding for an existing caller's registration assertion; they prescribe no universal halt.
UNION: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py
HIT[line]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:16-16:         "name": "new-caller", "missing_symbol": "new_caller", "role": "caller",
HIT[string]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:16-16: missing_symbol
HIT[line]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:21-21:         "name": "missing-callee", "missing_symbol": "callee", "role": "callee",
HIT[string]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:21-21: missing_symbol
HIT[line]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:26-26:         "name": "both-missing", "missing_symbol": "new_caller", "role": "caller",
HIT[string]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:26-26: missing_symbol
HIT[line]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:30-30:         "name": "unrelated-import", "missing_symbol": "fr9_unrelated_dependency",
HIT[string]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:30-30: missing_symbol
HIT[line]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:39-39:         "name": "other-symbol", "missing_symbol": "other_symbol", "role": "other",
HIT[string]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:39-39: missing_symbol
HIT[line]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:48-48: MISSING_ERRORS = {"ImportError", "ModuleNotFoundError", "AttributeError", "NameError"}
HIT[line]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:52-52:     """Before FR-9: every missing-symbol RED on the wiring pin is a halt."""
HIT[string]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:52-52: Before FR-9: every missing-symbol RED on the wiring pin is a halt.
HIT[line]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:57-57:     """FR-9: the missing symbol must be the new caller AND the callee resolve."""
HIT[string]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:57-57: FR-9: the missing symbol must be the new caller AND the callee resolve.
HIT[line]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:99-99:             r"^E\s+((?:ImportError|ModuleNotFoundError|AttributeError|NameError):[^\n]*)$",
HIT[string]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:99-99: ^E\s+((?:ImportError|ModuleNotFoundError|AttributeError|NameError):[^\n]*)$
HIT[line]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:103-103:             f"{declaration['name']}: expected one missing-symbol exception line\n{output}"
HIT[string]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:103-103: : expected one missing-symbol exception line
HIT[line]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:107-107:             "name": declaration["name"], "missing_symbol": declaration["missing_symbol"],
HIT[string]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:107-107: missing_symbol
HIT[string]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:107-107: missing_symbol
HIT[line]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:135-135:     assert f"'{declaration['missing_symbol']}'" in row["exception_line"], (
HIT[string]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:135-135: missing_symbol
HIT[line]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:136-136:         f"{row['name']}: exception must name the declared missing symbol: {row['exception_line']}"
HIT[string]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:136-136: : exception must name the declared missing symbol:
HIT[line]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:159-159:     assert "the missing symbol is the caller the task creates" in CANONICAL, (
HIT[string]: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py:159-159: the missing symbol is the caller the task creates
REVIEW: OK sha256=a093daa2d47684990ca0a3911010baa877c7f279161153ee1b68825916785837 :: RULE WITH CARVE-OUT: new_rule at lines 56-62 requires caller AND callee resolution; old_rule is explicitly Before FR-9 for comparison. Other hits are case keys, exception recognition and assertions.
PROBE: FAIL
````

## census_mutation_rows.py — full unchanged output

Working directory: `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad`

Command: `/Users/kimhawk/.agents/skills/h-mad/bin/hmad-dispatch run --timeout 60 -- /opt/anaconda3/bin/python3 ../docs/03-analysis/probes/agy-coder-fallback/census_mutation_rows.py`

Exit code: 0

````text
HEAD: 3236ade63000759101b8d5de7e4bdc1558329b73
M-2/hooks/h-mad-tdd-gate.sh/rows: computed=62 expected=56 MOVED
M-2/hooks/h-mad-tdd-gate.sh/specs: computed=6 expected=5 MOVED
  specs: claude_gate_judge_wiring.json, grok_wire_reverts.json, tdd_gate_differential.json, tdd_gate_fallback_agent.json, tdd_gate_peers.json, tdd_gate_scratchpad.json
M-2/scripts/h_mad_tdd_judge.py/rows: computed=41 expected=36 MOVED
M-2/scripts/h_mad_tdd_judge.py/specs: computed=10 expected=8 MOVED
  specs: claude_gate_judge_wiring.json, grok_wire_reverts.json, tdd_gate_fallback_agent.json, tdd_gate_peers.json, tdd_judge_chain.json, tdd_judge_implementer.json, tdd_judge_resolution.json, tdd_judge_scoring.json, tdd_judge_venv.json, tdd_judge_wiring.json
M-2/hooks/h-mad-codex-tdd-gate.py/rows: computed=35 expected=62 MOVED
M-2/hooks/h-mad-codex-tdd-gate.py/specs: computed=4 expected=5 MOVED
  specs: codex_gate_judge_wiring.json, codex_gate_shell_allowance.json, codex_gate_tmp_reports.json, shared_gate_policy.json
M-2/scripts/h_mad_assemble_tdd.py/rows: computed=65 expected=60 MOVED
M-2/scripts/h_mad_assemble_tdd.py/specs: computed=8 expected=6 MOVED
  specs: assemble_tdd.json, assemble_tdd_agent.json, assemble_tdd_agy.json, assemble_tdd_env_known.json, assemble_tdd_mutation_rows.json, fill_slots.json, grok_wire_reverts.json, new_caller_carveout_copies.json
M-2/scripts/h_mad_phase7_preconditions.py/rows: computed=16 expected=12 MOVED
M-2/scripts/h_mad_phase7_preconditions.py/specs: computed=3 expected=2 MOVED
  specs: phase7_analysis_anchor.json, phase7_preconditions_gates.json, phase7_review_independence.json
M-2/scripts/h_mad_hook_wiring.py/rows: computed=18 expected=10 MOVED
M-2/scripts/h_mad_hook_wiring.py/specs: computed=2 expected=1 MOVED
  specs: hook_wiring.json, hook_wiring_agy.json
M-2/scripts/h_mad_state_write.py/rows: computed=26 expected=21 MOVED
M-2/scripts/h_mad_state_write.py/specs: computed=5 expected=4 MOVED
  specs: heartbeat_beat.json, lane_liveness.json, release_ownership_guard.json, state_undeclared_keys.json, state_write_append.json
M-2/scripts/h_mad_target_identity.py/rows: computed=46 expected=15 MOVED
M-2/scripts/h_mad_target_identity.py/specs: computed=5 expected=2 MOVED
  specs: assemble_tdd_mutation_rows.json, codex_gate_judge_wiring.json, codex_gate_shell_allowance.json, target_identity.json, tdd_gate_differential.json
M-3/rows: computed=10 expected=8 MOVED
M-3/specs: computed=5 expected=3 MOVED
M-3/by-spec: computed={'claude_gate_judge_wiring.json': 5, 'tdd_gate_fallback_agent.json': 1, 'tdd_gate_peers.json': 1, 'tdd_judge_chain.json': 2, 'tdd_judge_implementer.json': 1} expected={'claude_gate_judge_wiring.json': 5, 'tdd_gate_fallback_agent.json': 1, 'tdd_judge_chain.json': 2} MOVED
  M-3: claude_gate_judge_wiring.json:C3G
  M-3: claude_gate_judge_wiring.json:W5BR
  M-3: claude_gate_judge_wiring.json:W5BF
  M-3: claude_gate_judge_wiring.json:W5BF2
  M-3: claude_gate_judge_wiring.json:W5BF3
  M-3: tdd_gate_fallback_agent.json:g2-env-bypasses-block-grok
  M-3: tdd_gate_peers.json:wire2-hook-rederives-from-env
  M-3: tdd_judge_chain.json:C3
  M-3: tdd_judge_chain.json:C5
  M-3: tdd_judge_implementer.json:fr2-cause-status-dropped
FR-3/_read_state/boundary-present: computed=True expected=True OK
  span: hooks/h-mad-tdd-gate.sh:(151, 194)
FR-3/_read_state/rows: computed=10 expected=7 MOVED
FR-3/_read_state/names: computed=['H17', 'W5BF', 'W5BF2', 'W5BF3', 'W5BR', 'fr3-invalid-scan-first-record-only', 'g9-fallback-position-unchecked', 'wire2-every-author-is-a-peer', 'wire2-hook-rederives-from-env', 'wr12-2-gate-never-reads-the-fold'] expected=['H17', 'W5BF', 'W5BF2', 'W5BF3', 'W5BR', 'g9-fallback-position-unchecked', 'wr12-2-gate-never-reads-the-fold'] MOVED
  FR-3: claude_gate_judge_wiring.json:H17
  FR-3: claude_gate_judge_wiring.json:W5BR
  FR-3: claude_gate_judge_wiring.json:W5BF
  FR-3: claude_gate_judge_wiring.json:W5BF2
  FR-3: claude_gate_judge_wiring.json:W5BF3
  FR-3: grok_wire_reverts.json:wr12-2-gate-never-reads-the-fold
  FR-3: tdd_gate_fallback_agent.json:g9-fallback-position-unchecked
  FR-3: tdd_gate_peers.json:fr3-invalid-scan-first-record-only
  FR-3: tdd_gate_peers.json:wire2-hook-rederives-from-env
  FR-3: tdd_gate_peers.json:wire2-every-author-is-a-peer
FR-3/authorship/boundary-present: computed=False expected=True MOVED
  span: hooks/h-mad-tdd-gate.sh:None
FR-3/authorship/rows: computed=0 expected=1 MOVED
FR-3/authorship/names: computed=[] expected=['H3'] MOVED
FR-3/_active_records/boundary-present: computed=True expected=True OK
  span: scripts/h_mad_tdd_judge.py:(176, 183)
FR-3/_active_records/rows: computed=1 expected=1 OK
FR-3/_active_records/names: computed=['g3-reads-another-feature'] expected=['g3-reads-another-feature'] OK
  FR-3: tdd_gate_fallback_agent.json:g3-reads-another-feature
FR-3/format_state_line/boundary-present: computed=True expected=True OK
  span: scripts/h_mad_tdd_judge.py:(458, 478)
FR-3/format_state_line/rows: computed=5 expected=4 MOVED
FR-3/format_state_line/names: computed=['C3', 'C3G', 'C5', 'wire1-author-not-from-resolver', 'wr12-1-state-line-never-folds'] expected=['C3', 'C3G', 'C5', 'wr12-1-state-line-never-folds'] MOVED
  FR-3: claude_gate_judge_wiring.json:C3G
  FR-3: grok_wire_reverts.json:wr12-1-state-line-never-folds
  FR-3: tdd_gate_peers.json:wire1-author-not-from-resolver
  FR-3: tdd_judge_chain.json:C3
  FR-3: tdd_judge_chain.json:C5
FR-3/rows: computed=16 expected=13 MOVED
FR-3/hook-rows: computed=10 expected=8 MOVED
FR-3/judge-rows: computed=6 expected=5 MOVED
M-4/closure-names: computed=[] expected=['_contained_venv_executable', '_cwd_escapes_root', '_load_judge', '_option_value', '_path_within', '_payload_cwd_base', '_safe_argv', '_safe_hmad_script', '_safe_shell_command', '_trusted_executable'] MOVED
M-4/moved-names: computed=15 expected=25 MOVED
M-4/missing-definitions: computed=['MALFORMED_WORKDIR', 'READ_ONLY_COMMANDS', 'SAFE_DISPATCH_VERBS', 'SAFE_HMAD_SCRIPT_OPTIONS', 'SHELL_ALLOW_FILE', 'SIMPLE_SHELL_COMMAND', 'TEMP_OUTPUT_OPTIONS', 'TRUSTED_BIN_DIRS', '_any_phase5_status', '_is_production_python', '_is_shell_allowance', '_operator_allowed', '_read_regular_text', '_shell_allowance', '_state_status'] expected=[] MOVED
M-4/total-rows: computed=35 expected=62 MOVED
M-4/moved-rows: computed=0 expected=31 MOVED
M-4/specs: computed=0 expected=4 MOVED
M-4/by-spec: computed={} expected={'codex_gate_judge_wiring.json': 21, 'codex_gate_shell_allowance.json': 6, 'assemble_tdd_mutation_rows.json': 2, 'tdd_gate_differential.json': 2} MOVED
M-4/absent-anchors: computed=0 expected=0 OK
M-4/non-unique-anchors: computed=0 expected=0 OK
PROBE: FAIL
````

## census_state_line.py — full unchanged output

Working directory: `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback`

Command: `/Users/kimhawk/.agents/skills/h-mad/bin/hmad-dispatch run --timeout 60 -- /opt/anaconda3/bin/python3 docs/03-analysis/probes/agy-coder-fallback/census_state_line.py`

Exit code: 0

````text
HEAD: 3236ade63000759101b8d5de7e4bdc1558329b73
DO-1a files: computed=7 expected=6 MOVED
  h-mad/hooks/h-mad-tdd-gate.sh
  h-mad/scripts/h_mad_tdd_judge.py
  h-mad/tests/mutation-specs/claude_gate_judge_wiring.json
  h-mad/tests/test_h_mad_tdd_gate_fallback_agent.py
  h-mad/tests/test_h_mad_tdd_gate_judge.py
  h-mad/tests/test_h_mad_tdd_gate_peers.py
  h-mad/tests/test_h_mad_tdd_judge.py
DO-1a/four-pattern files: computed=12 expected=7 MOVED
  h-mad/SKILL.md
  h-mad/hooks/h-mad-tdd-gate.sh
  h-mad/scripts/h_mad_tdd_judge.py
  h-mad/tests/mutation-specs/claude_gate_judge_wiring.json
  h-mad/tests/mutation-specs/grok_wire_reverts.json
  h-mad/tests/mutation-specs/tdd_gate_peers.json
  h-mad/tests/test_h_mad_agy_authorship_docs.py
  h-mad/tests/test_h_mad_tdd_gate_fallback_agent.py
  h-mad/tests/test_h_mad_tdd_gate_judge.py
  h-mad/tests/test_h_mad_tdd_gate_peers.py
  h-mad/tests/test_h_mad_tdd_judge.py
  h-mad/tests/test_h_mad_tdd_judge_implementer.py
PROBE: FAIL
````

## census_doc_pins.py — full unchanged output

Working directory: `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback`

Command: `/Users/kimhawk/.agents/skills/h-mad/bin/hmad-dispatch run --timeout 60 -- /opt/anaconda3/bin/python3 docs/03-analysis/probes/agy-coder-fallback/census_doc_pins.py`

Exit code: 0

````text
HEAD: 3236ade63000759101b8d5de7e4bdc1558329b73
SURFACE: skill-authorship path=h-mad/SKILL.md constants=18 expected=not recorded in plan files=8 files_expected=not recorded in plan
HIT[skill-authorship]: ' --check-anchors ' :: h-mad/tests/test_h_mad_codex_runtime.py
HIT[skill-authorship]: '### Codex authors Phase 5' :: h-mad/tests/test_h_mad_mutation_harness.py
HIT[skill-authorship]: 'Codex authors Phase 5 — enforced, not just instructed' :: h-mad/tests/test_grok_fallback_docs.py, h-mad/tests/test_h_mad_agy_authorship_docs.py
HIT[skill-authorship]: 'MUTATION: PRECHECK_FAILED' :: h-mad/tests/test_h_mad_mutation_harness.py
HIT[skill-authorship]: 'Mutation verification' :: h-mad/tests/test_h_mad_batch_doc_rules.py, h-mad/tests/test_h_mad_invariants_layering.py
HIT[skill-authorship]: "Phase 5 implementation is **Codex's job**" :: h-mad/tests/test_h_mad_agy_authorship_docs.py, h-mad/tests/test_h_mad_mutation_harness.py
HIT[skill-authorship]: 'Test files, docs, config, and shell are never gated; only production `.py`.' :: h-mad/tests/test_h_mad_tdd_gate_docs.py
HIT[skill-authorship]: 'a refusal measures NOTHING' :: h-mad/tests/test_h_mad_mutation_harness.py
HIT[skill-authorship]: 'does not control the environment' :: h-mad/tests/test_h_mad_ab_dispatch.py
HIT[skill-authorship]: 'expected one argument' :: h-mad/tests/test_h_mad_ab_dispatch.py
HIT[skill-authorship]: 'h_mad_tdd_judge.py implementer' :: h-mad/tests/test_h_mad_agy_authorship_docs.py
HIT[skill-authorship]: 'no longer exists' :: h-mad/tests/test_h_mad_mutation_harness.py
HIT[skill-authorship]: 'no write-time test-first gate' :: h-mad/tests/test_grok_fallback_docs.py
HIT[skill-authorship]: 'nothing was measured' :: h-mad/tests/test_h_mad_mutation_harness.py
HIT[skill-authorship]: 'performs the sibling sweep' :: h-mad/tests/test_h_mad_mutation_harness.py
HIT[skill-authorship]: 'refuses on sibling drift' :: h-mad/tests/test_h_mad_mutation_harness.py
HIT[skill-authorship]: 'relative spec `root`' :: h-mad/tests/test_h_mad_mutation_harness.py
HIT[skill-authorship]: 'relative to the project root' :: h-mad/tests/test_h_mad_tdd_gate_docs.py
EXPECT-LITERALS[skill-authorship]: 'no write-time test-first gate', 'fallback-grok', 'HMAD_CODEX_UNAVAILABLE', 'fallback_agent', '### Codex authors Phase 5 — enforced, not just instructed', "Phase 5 implementation is **Codex's job**", 'Test files, docs, config, and shell are never gated; only production `.py`.', 'FIRST component', 'relative to the project root', '`src/docs/foo.py`', 'Both gates'
EXPECT[skill-authorship]: OK
SURFACE: skill-dispatch path=h-mad/SKILL.md constants=11 expected=not recorded in plan files=7 files_expected=not recorded in plan
HIT[skill-dispatch]: '- **Stage the implementer.**' :: h-mad/tests/test_h_mad_agy_authorship_docs.py
HIT[skill-dispatch]: '--feature <feature>' :: h-mad/tests/test_h_mad_wire_registry.py
HIT[skill-dispatch]: '--sandbox workspace-write' :: h-mad/tests/test_hmad_dispatch_exec.py
HIT[skill-dispatch]: 'Exit-code dispatch for 5d/5e (`hmad-dispatch exec`) — default for one-shot' :: h-mad/tests/test_grok_fallback_docs.py, h-mad/tests/test_h_mad_agy_authorship_docs.py
HIT[skill-dispatch]: 'h_mad_assemble_tdd.py --agent' :: h-mad/tests/test_h_mad_agy_authorship_docs.py
HIT[skill-dispatch]: 'h_mad_tdd_judge.py implementer' :: h-mad/tests/test_h_mad_agy_authorship_docs.py
HIT[skill-dispatch]: 'hmad-dispatch exec' :: h-mad/tests/test_host_runtime_docs.py
HIT[skill-dispatch]: 'hmad-dispatch exec agy' :: h-mad/tests/test_h_mad_context_budget_docs.py
HIT[skill-dispatch]: 'hmad-dispatch exec codex' :: h-mad/tests/test_h_mad_assemble_tdd.py
HIT[skill-dispatch]: 'hmad-dispatch progress' :: h-mad/tests/test_h_mad_assemble_tdd.py
HIT[skill-dispatch]: 'python3 ~/.claude/skills/h-mad/scripts/h_mad_tdd_judge.py implementer --root . --feature "$FEATURE" --record' :: h-mad/tests/test_h_mad_agy_authorship_docs.py
EXPECT-LITERALS[skill-dispatch]: '### Exit-code dispatch for 5d/5e (`hmad-dispatch exec`) — default for one-shot', 'exec grok', '--agent grok', 'hmad-dispatch exec agy', 'hmad-dispatch exec codex'
EXPECT[skill-dispatch]: OK
SURFACE: skill-phase7-closure path=h-mad/SKILL.md constants=26 expected=not recorded in plan files=6 files_expected=not recorded in plan
HIT[skill-phase7-closure]: ' docs/.bkit-memory.json' :: h-mad/tests/test_h_mad_codex_runtime.py
HIT[skill-phase7-closure]: '--append review_independence=' :: h-mad/tests/test_h_mad_review_attribution_docs.py
HIT[skill-phase7-closure]: '--feature <feature>' :: h-mad/tests/test_h_mad_wire_registry.py
HIT[skill-phase7-closure]: '7. **Closure (autonomous)**' :: h-mad/tests/test_h_mad_archreview_pane_halt.py, h-mad/tests/test_h_mad_review_attribution_docs.py
HIT[skill-phase7-closure]: 'A `SKIPPED_NO_PANE` archreview **blocks** the gate — a headless `exec agy` review satisfies the gate.' :: h-mad/tests/test_h_mad_archreview_pane_halt.py
HIT[skill-phase7-closure]: 'After each 5e-review, 5e-verify and 6a-prime leg' :: h-mad/tests/test_h_mad_review_attribution_docs.py
HIT[skill-phase7-closure]: 'Carry every `WARNING` line into the Phase-7 report' :: h-mad/tests/test_h_mad_review_attribution_docs.py
HIT[skill-phase7-closure]: "If the reviewer is in that module's author set" :: h-mad/tests/test_h_mad_review_attribution_docs.py
HIT[skill-phase7-closure]: "Otherwise `implementer` is the agent of the module's latest entry" :: h-mad/tests/test_h_mad_review_attribution_docs.py
HIT[skill-phase7-closure]: 'The author set is read from `implementation_authors` only' :: h-mad/tests/test_h_mad_review_attribution_docs.py
HIT[skill-phase7-closure]: 'When no author can be read, no entry is written' :: h-mad/tests/test_h_mad_review_attribution_docs.py
HIT[skill-phase7-closure]: '`implementer` is read from the dispatch' :: h-mad/tests/test_h_mad_review_attribution_docs.py
HIT[skill-phase7-closure]: '`implementer` is the reviewer and `independent` is `false`' :: h-mad/tests/test_h_mad_review_attribution_docs.py
HIT[skill-phase7-closure]: '`independent` is `reviewer != implementer`' :: h-mad/tests/test_h_mad_review_attribution_docs.py
HIT[skill-phase7-closure]: 'accepted fix dispatch' :: h-mad/tests/test_h_mad_review_attribution_docs.py
HIT[skill-phase7-closure]: 'for every implementer' :: h-mad/tests/test_h_mad_review_attribution_docs.py
HIT[skill-phase7-closure]: 'git branch main origin/main' :: h-mad/tests/test_h_mad_phase7_integrate_docs.py
HIT[skill-phase7-closure]: 'halted, timed out or was rejected' :: h-mad/tests/test_h_mad_review_attribution_docs.py
HIT[skill-phase7-closure]: 'must name a LOCAL branch' :: h-mad/tests/test_h_mad_phase7_integrate_docs.py
HIT[skill-phase7-closure]: 'never read from `implementer_switch.to` or from the `implementer` field' :: h-mad/tests/test_h_mad_review_attribution_docs.py
HIT[skill-phase7-closure]: 'one 6a-prime entry per module' :: h-mad/tests/test_h_mad_review_attribution_docs.py
HIT[skill-phase7-closure]: 'property_valid("implementation_authors", [entry])' :: h-mad/tests/test_h_mad_review_attribution_docs.py
HIT[skill-phase7-closure]: 'satisfies the gate' :: h-mad/tests/test_h_mad_phase7_preconditions.py
HIT[skill-phase7-closure]: 'the field is present and holds no well-formed entry' :: h-mad/tests/test_h_mad_review_attribution_docs.py
HIT[skill-phase7-closure]: 'the field is present and is not a list, or holds an entry that is not well-formed' :: h-mad/tests/test_h_mad_review_attribution_docs.py
HIT[skill-phase7-closure]: 'the record has no `implementation_authors` field' :: h-mad/tests/test_h_mad_review_attribution_docs.py
EXPECT-LITERALS[skill-phase7-closure]: '7. **Closure (autonomous)**', 'SKIPPED_NO_PANE', 'must name a LOCAL branch', 'git branch main origin/main'
EXPECT[skill-phase7-closure]: OK
SURFACE: skill-teammate path=h-mad/SKILL.md constants=13 expected=not recorded in plan files=7 files_expected=not recorded in plan
HIT[skill-teammate]: ' --project-root ' :: h-mad/tests/test_h_mad_collect_report_docs.py
HIT[skill-teammate]: ' docs/.bkit-memory.json' :: h-mad/tests/test_h_mad_codex_runtime.py
HIT[skill-teammate]: '- **It does not license Claude to write Phase 5 production code' :: h-mad/tests/test_h_mad_agy_authorship_docs.py, h-mad/tests/test_h_mad_tdd_gate_docs.py
HIT[skill-teammate]: '--feature <feature>' :: h-mad/tests/test_h_mad_wire_registry.py
HIT[skill-teammate]: '--phase plan|design|impl-plan' :: h-mad/tests/test_h_mad_collect_report_docs.py
HIT[skill-teammate]: '--surfaces agy,grok' :: h-mad/tests/test_grok_fallback_docs.py
HIT[skill-teammate]: 'REPORT=<the $RP above>' :: h-mad/tests/test_h_mad_report_path_handed.py
HIT[skill-teammate]: 'RUN=$(date -u +%Y%m%dT%H%M%SZ)-$$' :: h-mad/tests/test_h_mad_report_path_handed.py
HIT[skill-teammate]: 'Read the `COLLECT:` token exactly as the codex leg does' :: h-mad/tests/test_h_mad_report_path_handed.py
HIT[skill-teammate]: 'Teammate audit leg — when codex is unavailable' :: h-mad/tests/test_grok_fallback_docs.py
HIT[skill-teammate]: 'echo "RUN=$RUN RP=$RP"' :: h-mad/tests/test_h_mad_report_path_handed.py
HIT[skill-teammate]: 'h_mad_tdd_judge.py implementer' :: h-mad/tests/test_h_mad_agy_authorship_docs.py
HIT[skill-teammate]: 'stage the report under a `teammate` surface' :: h-mad/tests/test_h_mad_report_path_handed.py
EXPECT-LITERALS[skill-teammate]: 'It does not license Claude to write Phase 5 production code', 'ACTIVE', 'every', 'unavailable', 'exhausted', '## Teammate audit leg — when codex is unavailable', '--surfaces agy,grok', 'unmeasured'
EXPECT[skill-teammate]: OK
SURFACE: skill-5d-wiring path=h-mad/SKILL.md constants=6 expected=not recorded in plan files=4 files_expected=not recorded in plan
HIT[skill-5d-wiring]: '**The third task shape is `wiring`, and counts cannot gate it.**' :: h-mad/tests/test_h_mad_new_caller_carveout_copies.py
HIT[skill-5d-wiring]: 'A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails.' :: h-mad/tests/test_h_mad_new_caller_carveout_copies.py
HIT[skill-5d-wiring]: 'Connection enforcement' :: h-mad/tests/test_h_mad_assemble_tdd.py, h-mad/tests/test_h_mad_invariants_layering.py
HIT[skill-5d-wiring]: 'The third task shape is `wiring`, and counts cannot gate it.' :: h-mad/tests/test_h_mad_wiring_task_shape_docs.py
HIT[skill-5d-wiring]: 'failure mode per test, not only the count' :: h-mad/tests/test_h_mad_wiring_task_shape_docs.py
HIT[skill-5d-wiring]: '§"Connection enforcement"' :: h-mad/tests/test_h_mad_wiring_task_shape_docs.py
EXPECT-LITERALS[skill-5d-wiring]: 'The third task shape is `wiring`, and counts cannot gate it.', 'failure mode per test, not only the count'
EXPECT[skill-5d-wiring]: OK
SURFACE: agy-tdd-gate path=h-mad/references/agy-runtime.md constants=1 expected=not recorded in plan files=1 files_expected=not recorded in plan
HIT[agy-tdd-gate]: 'h_mad_assemble_tdd.py --agent' :: h-mad/tests/test_h_mad_agy_authorship_docs.py
EXPECT-LITERALS[agy-tdd-gate]: 'h-mad-codex-tdd-gate.py', 'h-mad-tdd-gate.sh', 'permissionDecision', 'rc 0'
EXPECT-ABSENT[agy-tdd-gate]: 'exit-code protocol'
EXPECT[agy-tdd-gate]: OK
SURFACE: agy-hooks path=h-mad/references/agy-runtime.md constants=0 expected=not recorded in plan files=0 files_expected=not recorded in plan
EXPECT-LITERALS[agy-hooks]: none
EXPECT[agy-hooks]: OK
SURFACE: agy-construct-mapping path=h-mad/references/agy-runtime.md constants=2 expected=not recorded in plan files=1 files_expected=not recorded in plan
HIT[agy-construct-mapping]: 'Construct mapping' :: h-mad/tests/test_h_mad_agy_authorship_docs.py
HIT[agy-construct-mapping]: '| `hook-event` |' :: h-mad/tests/test_h_mad_agy_authorship_docs.py
EXPECT-LITERALS[agy-construct-mapping]: none
EXPECT[agy-construct-mapping]: OK
SURFACE: failure-recovery-5d path=h-mad/references/failure-recovery.md constants=1 expected=not recorded in plan files=1 files_expected=not recorded in plan
HIT[failure-recovery-5d]: 'A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails.' :: h-mad/tests/test_h_mad_new_caller_carveout_copies.py
EXPECT-LITERALS[failure-recovery-5d]: 'step5d:red_wrong_reason:<module>'
EXPECT[failure-recovery-5d]: OK
SURFACE: state-schema-fields path=h-mad/references/state-schema.md constants=2 expected=not recorded in plan files=2 files_expected=not recorded in plan
HIT[state-schema-fields]: '--surfaces agy,grok' :: h-mad/tests/test_grok_fallback_docs.py
HIT[state-schema-fields]: 'h_mad_tdd_judge.py implementer' :: h-mad/tests/test_h_mad_state_schema_fr1_docs.py
EXPECT-LITERALS[state-schema-fields]: none
EXPECT[state-schema-fields]: OK
SURFACE: assembler-wiring path=h-mad/scripts/h_mad_assemble_tdd.py constants=2 expected=not recorded in plan files=1 files_expected=not recorded in plan
HIT[assembler-wiring]: 'A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails.' :: h-mad/tests/test_h_mad_new_caller_carveout_copies.py
HIT[assembler-wiring]: "The WIRE-PIN is this task's single load-bearing test." :: h-mad/tests/test_h_mad_new_caller_carveout_copies.py
EXPECT-LITERALS[assembler-wiring]: 'never a missing'
EXPECT[assembler-wiring]: OK
SURFACE: prompt path=h-mad/references/codex-implementer-prompt.md constants=27 expected=23 files=9 files_expected=8
HIT[prompt]: '## Report Format' :: h-mad/tests/test_h_mad_prompt_tails.py
HIT[prompt]: '## The last line' :: h-mad/tests/test_h_mad_prompt_tails.py
HIT[prompt]: '**If the dispatch carries a `WIRE:` / `WIRE-PIN:` line' :: h-mad/tests/test_h_mad_new_caller_carveout_copies.py
HIT[prompt]: '1. For each FAILING test:' :: h-mad/tests/test_h_mad_new_caller_carveout_copies.py
HIT[prompt]: 'A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails.' :: h-mad/tests/test_h_mad_new_caller_carveout_copies.py
HIT[prompt]: 'Drive any fixture value that originates from an agent or a human with a hostile payload using HMAD_STUB_HOSTILE.' :: h-mad/tests/test_h_mad_tdd_dispatch_discipline_prompt.py
HIT[prompt]: 'For GREEN phase (5e):' :: h-mad/tests/test_h_mad_new_caller_carveout_copies.py
HIT[prompt]: 'For a `wiring` task' :: h-mad/tests/test_h_mad_agent_definitions.py
HIT[prompt]: 'For each FAILING test: does the failure message name the property under test?' :: h-mad/tests/test_h_mad_agent_definitions.py, h-mad/tests/test_h_mad_tdd_dispatch_discipline_prompt.py
HIT[prompt]: 'For each PASSING test: would it still pass if the behaviour it names were deleted?' :: h-mad/tests/test_h_mad_tdd_dispatch_discipline_prompt.py
HIT[prompt]: 'For each behavioural test: name the method actually invoked, and confirm it is the one that contains the behaviour under test.' :: h-mad/tests/test_h_mad_tdd_dispatch_discipline_prompt.py
HIT[prompt]: 'STATUS: <DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT>' :: h-mad/tests/test_h_mad_prompt_tails.py
HIT[prompt]: 'Say which case each failing test is.' :: h-mad/tests/test_h_mad_agent_definitions.py
HIT[prompt]: 'Tidy ASCII fixtures let a real defect through every gate.' :: h-mad/tests/test_h_mad_tdd_dispatch_discipline_prompt.py
HIT[prompt]: '[H-MAD] worker_done coordinator handle' :: h-mad/tests/test_hmad_dispatch.py
HIT[prompt]: '`INLINE_*` placeholders substituted' :: h-mad/tests/test_h_mad_assemble_tdd.py
HIT[prompt]: 'at least one concern' :: h-mad/tests/test_h_mad_preflight_docs.py
HIT[prompt]: 'do not manufacture a failure' :: h-mad/tests/test_h_mad_preflight_docs.py
HIT[prompt]: 'expected failing/passing counts' :: h-mad/tests/test_h_mad_preflight_docs.py
HIT[prompt]: 'no code fence around it' :: h-mad/tests/test_h_mad_prompt_tails.py
HIT[prompt]: "outside the task's stated scope" :: h-mad/tests/test_h_mad_tdd_dispatch_discipline_prompt.py
HIT[prompt]: 'regression guards' :: h-mad/tests/test_h_mad_preflight_docs.py
HIT[prompt]: 'restructure a string literal, identifier, or import' :: h-mad/tests/test_h_mad_tdd_dispatch_discipline_prompt.py
HIT[prompt]: 'the first RED is `AttributeError`/`ImportError` **by construction**' :: h-mad/tests/test_h_mad_agent_definitions.py
HIT[prompt]: 'this is a `wiring` task and the pin is its single load-bearing test' :: h-mad/tests/test_h_mad_wiring_task_shape_docs.py
HIT[prompt]: 'very last line of your reply' :: h-mad/tests/test_h_mad_prompt_tails.py
HIT[prompt]: 'worker_done coordinator handle' :: h-mad/tests/test_hmad_dispatch_exec.py
EXPECT-LITERALS[prompt]: '`Concerns:`', 'prose', 'contentless', 'run --timeout', 'gtimeout', 'halt', 'coreutils', 'Hook: ', 'apply_patch', 'shell', 'Write', 'Edit', 'impl-plan', 'name map', 'summary', 'N failed', 'test_*.py', '*_test.py', 'conftest*.py'
EXPECT[prompt]: OK
prompt distinct literals: actual=27 expected=23
prompt test files: actual=9 expected=8
SURFACE: prompt-hook-block path=h-mad/references/codex-implementer-prompt.md constants=0 expected=not recorded in plan files=0 files_expected=not recorded in plan
EXPECT-LITERALS[prompt-hook-block]: none
EXPECT-ABSENT[prompt-hook-block]: '<', '>'
EXPECT[prompt-hook-block]: OK
hand-found pins: listed in EXPECT; they are not derived by the >=16-character matcher
residual: short literals; space-free literals; run-time-built literals; negative assertions; structural locators
moved figures: distinct_literals, test_files
PROBE: FAIL
````

## class_inventory.py — full unchanged output

Working directory: `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback`

Command: `/Users/kimhawk/.agents/skills/h-mad/bin/hmad-dispatch run --timeout 60 -- /opt/anaconda3/bin/python3 docs/03-analysis/probes/agy-coder-fallback/class_inventory.py`

Exit code: 0

````text
HEAD: 3236ade63000759101b8d5de7e4bdc1558329b73
LOG: docs/03-analysis/probes/multi-host-runtime/rehearsal/live-agy-2026-10-01.log
total names: computed=58 expected=58 OK
a names: computed=11 expected=11 OK
  ask_question, command_status, find_by_name, finish, grep_search, list_dir, read_url_content, search_web, view_file, wait, wait_5_seconds
b names: computed=5 expected=5 OK
  multi_replace_file_content, notebook_edit, replace_file_content, sed_file, write_to_file
c names: computed=1 expected=1 OK
  run_command
d names: computed=41 expected=41 OK
  ask_custom_permission, ask_permission, browser_click_element, browser_drag_pixel_to_pixel, browser_get_dom, browser_get_network_request, browser_input, browser_list_network_requests, browser_mouse_down, browser_mouse_up, browser_move_mouse, browser_press_key, browser_refresh_page, browser_resize_window, browser_scroll, browser_scroll_dom, browser_select_option, browser_subagent, call_mcp_tool, capture_browser_console_logs, capture_browser_screenshot, click_browser_pixel, define_subagent, delete_knowledge, execute_browser_javascript, generate_image, invoke_subagent, list_browser_pages, list_permissions, list_resources, manage_inbox, manage_subagents, manage_task, notebook_execution, open_browser_url, read_browser_page, read_resource, run_workflow, schedule, send_command_input, send_message
PROBE: PASS
````

## Manual reading of EVERY sweep hit file

The quotes below reproduce every physical hit line and each Python joined-string hit from discovery. Normalized non-Python whole-text matches introduce no additional file; those texts were checked in their quoted context. No comment hits or unparsed files exist. Source evidence remains included even when it is a historical comparator or a deliberate broken mutation.

### h-mad/SKILL.md

States the operative rule WITH the full carve-out in line 500. The nearby blanket halt is qualified in the same paragraph: missing symbol must be the caller the task creates, callee resolves at RED base, RED names both, GREEN cuts the call only while preserving both. No unqualified operative copy.

`line 500`:

````text
  **The third task shape is `wiring`, and counts cannot gate it.** When the deliverable is a connection rather than new behaviour, carry the task's `WIRE:` and `WIRE-PIN:` lines from the impl-plan into the dispatch, and require the RED report to give the **failure mode per test, not only the count**. A test whose RED is an `ImportError`/`AttributeError`/`NameError` — the callee missing — is not a wire test: it fails for the callee's absence and goes green the moment the callee exists, wired or not. The `WIRE-PIN` test's RED must be an assertion about the **caller's** observable behaviour (the call was not made; the value did not propagate). The traceback already carries this, so the check costs nothing. A `WIRE-PIN` whose RED reason is a missing symbol → halt `step5d:red_wrong_reason:<module>`. A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails. A `wiring` task dispatched with no `WIRE-PIN` at all → halt `step5d:no_wire_pin:<module>`; do not let 5e establish GREEN for it, because nothing downstream can see the wire (`invariants.base.md` §"Connection enforcement").
````

### h-mad/references/codex-implementer-prompt.md

States the operative rule WITH the full carve-out in EACH of lines 60 (RED question), 68 (WIRE-PIN paragraph), and 72 (GREEN). Each was read separately, so one healthy copy does not mask another. Each requires new caller + existing callee, both named in RED, and the call-only wire-cut.

`line 60`:

````text
1. For each FAILING test: does the failure message name the property under test? For a `wiring` task (a dispatch carrying `WIRE:`/`WIRE-PIN:` — see below), an `ImportError`/`AttributeError`/`NameError` standing in for a behavioural assertion is not a RED — it is an unwritten test. For a task that introduces a NEW symbol, the first RED is `AttributeError`/`ImportError` **by construction** (the symbol does not exist yet); that is acceptable only when the same test also asserts the behaviour that must hold once the symbol exists, so it stays meaningful after GREEN. Say which case each failing test is. A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails.
````

`line 68`:

````text
**If the dispatch carries a `WIRE:` / `WIRE-PIN:` line, this is a `wiring` task and the pin is its single load-bearing test.** The pin must fail because the **caller** does not reach the callee — the call was not made, the value did not propagate — and NOT because the callee is missing. An `ImportError`/`AttributeError`/`NameError` RED on the pin means the pin is testing the callee, so it will go green the moment the callee exists whether or not anything wires it; report that and stop rather than accepting it. A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails. State the pin's failure **mode**, quoted, not just its pass/fail count. In GREEN, the pin must still fail if the connection alone is deleted with the callee left in place — if it does not, say so; do not repair it silently.
````

`line 72`:

````text
For GREEN phase (5e): implement the minimal code to make the failing tests pass. Verify GREEN by running `pytest <test_path> -v`. Then refactor if helpful, keeping tests green. A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails.
````

### h-mad/references/failure-recovery.md

States the operative rule WITH the full carve-out in the remedy cell of row 36. The row's terse symptom and initial callee prohibition are qualified by its own complete three-sentence remedy; no unconditional halt remains as a separate remedy.

`line 36`:

````text
| 5d | `WIRE-PIN` test's RED is a missing symbol, not caller behaviour | `step5d:red_wrong_reason:<module>` | "An `ImportError`/`AttributeError`/`NameError` RED means the pin tests the callee, so it goes green the moment the callee exists — wired or not. Re-dispatch the pin as an assertion on the caller's observable behaviour (the call was not made; the value did not propagate). Counts cannot catch this; only the failure mode can. A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails." |
````

### h-mad/scripts/h_mad_assemble_tdd.py

States the operative rule WITH the full carve-out in the joined string at lines 477–483. The phrase 'never a missing symbol' is immediately qualified by new caller + resolving callee, name both, and call-only wire-cut. Read the joined literal rather than line 480 alone.

`line 480`:

````text
            "A missing-symbol RED on the pin is valid **only** when the missing symbol is "
````

`string 477–483`:

````text
The WIRE-PIN is this task's single load-bearing test. Its RED must be an assertion about the CALLER's observable behaviour, never a missing symbol. A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails.
````

### h-mad/tests/fixtures/codex-text-8-exec.log

Does NOT state a general missing-symbol rule. This is captured output quoting a particular docsections recorder test. Lines 940–976 scaffold an existing caller with a fake module; line 974 describes its actual len(calls) == 2 RED, not universal policy. No carve-out is stated here because no general rule is stated. Retained in the union. This agrees with the plan's explicit classification at lines 598–601.

`line 974`:

````text
fails on `len(calls) == 2` — never an `ImportError`/`AttributeError`. At GREEN the reload
````

### h-mad/tests/mutation-specs/new_caller_carveout_copies.json

Contains quoted rule fragments and deliberately damaged carve-outs as mutation DATA, not operative instructions. Rows L1–L6 remove **only**, sentence-2 removes name-both, and sentence-3 substitutes callee deletion; these are negative controls whose intended consequence is test failure. The corpus rows remove caller/callee conditions independently. All quoted damaged forms remain reported, not excluded from the sweep.

`line 23`:

````text
      "find": "Say which case each failing test is. A missing-symbol RED on the pin is valid **only** when",
````

`line 24`:

````text
      "replace": "Say which case each failing test is. A missing-symbol RED on the pin is valid when",
````

`line 32`:

````text
      "find": "report that and stop rather than accepting it. A missing-symbol RED on the pin is valid **only** when",
````

`line 33`:

````text
      "replace": "report that and stop rather than accepting it. A missing-symbol RED on the pin is valid when",
````

`line 41`:

````text
      "find": "halt `step5d:red_wrong_reason:<module>`. A missing-symbol RED on the pin is valid **only** when",
````

`line 42`:

````text
      "replace": "halt `step5d:red_wrong_reason:<module>`. A missing-symbol RED on the pin is valid when",
````

`line 50`:

````text
      "find": "only the failure mode can. A missing-symbol RED on the pin is valid **only** when",
````

`line 51`:

````text
      "replace": "only the failure mode can. A missing-symbol RED on the pin is valid when",
````

`line 59`:

````text
      "find": "The WIRE-PIN is this task's single load-bearing test. Its RED must be \"\n            \"an assertion about the CALLER's observable behaviour, never a missing \"\n            \"symbol. \"\n            \"A missing-symbol RED on the pin is valid **only** when",
````

`line 60`:

````text
      "replace": "The WIRE-PIN is this task's single load-bearing test. Its RED must be \"\n            \"an assertion about the CALLER's observable behaviour, never a missing \"\n            \"symbol. \"\n            \"A missing-symbol RED on the pin is valid when",
````

`line 68`:

````text
      "find": "keeping tests green. A missing-symbol RED on the pin is valid **only** when",
````

`line 69`:

````text
      "replace": "keeping tests green. A missing-symbol RED on the pin is valid when",
````

`line 77`:

````text
      "find": "only the failure mode can. A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails.",
````

`line 78`:

````text
      "replace": "only the failure mode can. A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails.",
````

`line 86`:

````text
      "find": "only the failure mode can. A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails.",
````

`line 87`:

````text
      "replace": "only the failure mode can. A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the callee only, keep the caller, and confirm the pin fails.",
````

### h-mad/tests/test_h_mad_agent_definitions.py

Does NOT restate the blanket missing-symbol prohibition. Line 77 asserts the implementer prompt's generic new-symbol RED wording; surrounding lines 71–78 also pin its wiring scope and behavioral question. No new-caller carve-out is contradicted or forbidden by this assertion; no separate general rule requires qualification here.

`line 77`:

````text
    assert "the first RED is `AttributeError`/`ImportError` **by construction**" in body
````

`string 77`:

````text
the first RED is `AttributeError`/`ImportError` **by construction**
````

### h-mad/tests/test_h_mad_new_caller_carveout_copies.py

States the canonical rule WITH the full carve-out at lines 16–21. It includes both prerequisites, naming both, and the call-only wire-cut. Six separate locators enforce each source copy, with zero/two-span controls. This is the test authority, not a seventh unqualified production rule.

`line 17`:

````text
    "A missing-symbol RED on the pin is valid **only** when the missing symbol is "
````

`string 17–20`:

````text
A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails.
````

### h-mad/tests/test_h_mad_wire_pin_gate.py

Does NOT state a general missing-symbol rule. The helper docstring at lines 576–582 explains injecting the future CLI namespace to reach the existing registration caller's observable missing-call assertion. It describes one fixture, not a universal rejection of missing new callers; no general-rule carve-out is owed here. Retained in the union.

`line 581`:

````text
    missing symbol or an argparse setup detail.
````

`string 576–582`:

````text
Call main with the additive CLI namespace expected by Task 5. The RED phase must not add argparse or production wiring. Injecting the future namespace lets these tests reach the existing caller and fail on the observable absence of the register call, rather than on an import-shaped missing symbol or an argparse setup detail.
````

### h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py

States the CURRENT rule WITH the caller/callee carve-out in new_rule (56–62): missing_is_caller AND callee_resolves. old_rule's unqualified halt at line 52 is explicitly labeled 'Before FR-9' and is required as the historical comparator, not shipped advice. Remaining hits are case keys, exception-recognition text and assertion messages. Lines 158–164 tie the transcription to both canonical prerequisites.

`line 16`:

````text
        "name": "new-caller", "missing_symbol": "new_caller", "role": "caller",
````

`line 21`:

````text
        "name": "missing-callee", "missing_symbol": "callee", "role": "callee",
````

`line 26`:

````text
        "name": "both-missing", "missing_symbol": "new_caller", "role": "caller",
````

`line 30`:

````text
        "name": "unrelated-import", "missing_symbol": "fr9_unrelated_dependency",
````

`line 39`:

````text
        "name": "other-symbol", "missing_symbol": "other_symbol", "role": "other",
````

`line 48`:

````text
MISSING_ERRORS = {"ImportError", "ModuleNotFoundError", "AttributeError", "NameError"}
````

`line 52`:

````text
    """Before FR-9: every missing-symbol RED on the wiring pin is a halt."""
````

`line 57`:

````text
    """FR-9: the missing symbol must be the new caller AND the callee resolve."""
````

`line 99`:

````text
            r"^E\s+((?:ImportError|ModuleNotFoundError|AttributeError|NameError):[^\n]*)$",
````

`line 103`:

````text
            f"{declaration['name']}: expected one missing-symbol exception line\n{output}"
````

`line 107`:

````text
            "name": declaration["name"], "missing_symbol": declaration["missing_symbol"],
````

`line 135`:

````text
    assert f"'{declaration['missing_symbol']}'" in row["exception_line"], (
````

`line 136`:

````text
        f"{row['name']}: exception must name the declared missing symbol: {row['exception_line']}"
````

`line 159`:

````text
    assert "the missing symbol is the caller the task creates" in CANONICAL, (
````

`string 52`:

````text
Before FR-9: every missing-symbol RED on the wiring pin is a halt.
````

`string 57`:

````text
FR-9: the missing symbol must be the new caller AND the callee resolve.
````

`string 16`:

````text
missing_symbol
````

`string 21`:

````text
missing_symbol
````

`string 26`:

````text
missing_symbol
````

`string 30`:

````text
missing_symbol
````

`string 39`:

````text
missing_symbol
````

`string 136`:

````text
: exception must name the declared missing symbol:
````

`string 159`:

````text
the missing symbol is the caller the task creates
````

`string 99`:

````text
^E\s+((?:ImportError|ModuleNotFoundError|AttributeError|NameError):[^\n]*)$
````

`string 103`:

````text
: expected one missing-symbol exception line
````

`string 107`:

````text
missing_symbol
````

`string 107`:

````text
missing_symbol
````

`string 135`:

````text
missing_symbol
````

## review_independence_unrecorded — feature-edited scope

Scope base: `git merge-base HEAD main` = `2cd5d7f129f39348ebc55e3370ed48a09966a9ce`. Read `git diff --name-only -z 2cd5d7f129f39348ebc55e3370ed48a09966a9ce HEAD`: 105 feature-edited tracked paths, including feature reports and the impl-plan. Then executed `git grep -n 'review_independence_unrecorded' -- <each of those paths>` with a structured argv list, no shell expansion. The new untracked probe contains no such identifier. No path was excluded because it was a report, test, or mutation spec.

Read all 35 hits below, with surrounding context where the line names only a code or a parameterized example. Every hit's agy-only answer is NO.

Full git-grep output:

````text
docs/01-plan/features/agy-coder-fallback.impl-plan.md:1383:naming leg, module and agent; `review_independence_unrecorded` when `record.get("archreview")` is in
docs/01-plan/features/agy-coder-fallback.impl-plan.md:1769:   `review_non_independent`, `review_independence_unrecorded`, `review_independence_malformed`. F.
docs/01-plan/features/agy-coder-fallback.impl-plan.md:1831:- `git grep -n 'review_independence_unrecorded'` over the files this feature edited; each hit is
docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task12_decisions.md:6:  `review_independence`, so FR-7's `review_independence_unrecorded` correctly fires. Five tests
docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task12_green.report.md:7:E       AssertionError: assert not [{'code': 'review_independence_unrecorded', 'detail': '6a-prime review independence is unrecorded; authors=unrecorded'}]
docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task12_green.report.md:32:Blockers: Five existing assertions conflict with the newly required warning. Their READY fixtures contain archreview=READY_TO_MERGE without well-formed 6a-prime review evidence, so FR-7 requires review_independence_unrecorded. These assertions demand no warnings or an exact pre-FR-7 set:
docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task12_red.report.md:42:5. test_unrecorded_fires_for_each_implementer[codex-field-absent] — FAIL; invokes actual p7.check; AssertionError "review_independence_unrecorded must fire independently of routing {}"; behavioral missing-warning failure, not missing-symbol failure.
docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task12_red.report.md:43:6. test_unrecorded_fires_for_each_implementer[codex] — FAIL; invokes actual p7.check; AssertionError names review_independence_unrecorded and routing implementer=codex; behavioral missing-warning failure, not missing-symbol failure.
docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task12_red.report.md:44:7. test_unrecorded_fires_for_each_implementer[agy] — FAIL; invokes actual p7.check; AssertionError names review_independence_unrecorded and routing implementer=agy; behavioral missing-warning failure, not missing-symbol failure.
docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task12_red.report.md:45:8. test_unrecorded_fires_for_each_implementer[grok] — FAIL; invokes actual p7.check; AssertionError names review_independence_unrecorded and implementer_switch.to=grok; behavioral missing-warning failure, not missing-symbol failure.
docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task12_red.report.md:46:9. test_unrecorded_fires_for_each_implementer[claude] — FAIL; invokes actual p7.check; AssertionError names review_independence_unrecorded and implementer_switch.to=claude; behavioral missing-warning failure, not missing-symbol failure.
docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task12_red.report.md:47:10. test_unrecorded_fires_for_each_archreview_value[READY_TO_MERGE] — FAIL; invokes actual p7.check; AssertionError "review_independence_unrecorded must fire for archreview=READY_TO_MERGE"; behavioral missing-warning failure, not missing-symbol failure.
docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task12_red.report.md:48:11. test_unrecorded_fires_for_each_archreview_value[WITH_FIXES] — FAIL; invokes actual p7.check; AssertionError "review_independence_unrecorded must fire for archreview=WITH_FIXES"; behavioral missing-warning failure, not missing-symbol failure.
docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task12_red.report.md:49:12. test_unrecorded_fires_for_each_archreview_value[NO] — FAIL; invokes actual p7.check; AssertionError "review_independence_unrecorded must fire for archreview=NO"; behavioral missing-warning failure, not missing-symbol failure.
docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task12_red.report.md:55:18. test_unrecorded_detail_names_entry_authors_not_routing — FAIL; invokes actual p7.check; AssertionError "review_independence_unrecorded must expose entry authors"; behavioral missing-warning failure, not missing-symbol failure; subsequent assertions require codex, exclude agy, and check sorted distinct authors.
docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task12_red.report.md:56:19. test_unrecorded_detail_without_5e_entries_says_unrecorded — FAIL; invokes actual p7.check; AssertionError "review_independence_unrecorded must warn when the entry list is empty"; behavioral missing-warning failure, not missing-symbol failure; subsequent assertion requires authors=unrecorded.
h-mad/SKILL.md:346:   Carry every `WARNING` line into the Phase-7 report, including `review_non_independent`, `review_independence_unrecorded` and `review_independence_malformed`; warnings do not change readiness.
h-mad/SKILL.md:354:   When no author can be read, no entry is written for the module, in exactly three cases: the record has no `implementation_authors` field (a pre-field feature); the field is present and holds no well-formed entry for that module; or the field is present and is not a list, or holds an entry that is not well-formed (even for another module, invalidating the record's author set). An absent field is never an empty author set. `review_independence_unrecorded` detects no 6a-prime entry at all, but cannot detect one missing module among other recorded modules.
h-mad/scripts/h_mad_phase7_preconditions.py:143:            "code": "review_independence_unrecorded",
h-mad/tests/mutation-specs/review_attribution_docs.json:22:      "find": "Carry every `WARNING` line into the Phase-7 report, including `review_non_independent`, `review_independence_unrecorded` and `review_independence_malformed`; warnings do not change readiness.",
h-mad/tests/test_h_mad_phase7_preconditions.py:43:# unrelated to review independence (review_independence_unrecorded would otherwise fire).
h-mad/tests/test_h_mad_phase7_preconditions.py:623:                    if w["code"] == "review_independence_unrecorded"]
h-mad/tests/test_h_mad_phase7_preconditions.py:625:            f"review_independence_unrecorded must fire independently of routing {routing!r}"
h-mad/tests/test_h_mad_phase7_preconditions.py:635:                    if w["code"] == "review_independence_unrecorded"]
h-mad/tests/test_h_mad_phase7_preconditions.py:637:            f"review_independence_unrecorded must fire for archreview={archreview}"
h-mad/tests/test_h_mad_phase7_preconditions.py:653:        assert "review_independence_unrecorded" not in {w["code"] for w in result["warnings"]}, (
h-mad/tests/test_h_mad_phase7_preconditions.py:654:            f"review_independence_unrecorded must stay quiet for {case}"
h-mad/tests/test_h_mad_phase7_preconditions.py:665:            "review_independence_malformed", "review_independence_unrecorded",
h-mad/tests/test_h_mad_phase7_preconditions.py:675:                    if w["code"] == "review_independence_unrecorded"]
h-mad/tests/test_h_mad_phase7_preconditions.py:676:        assert len(warnings) == 1, "review_independence_unrecorded must expose entry authors"
h-mad/tests/test_h_mad_phase7_preconditions.py:685:                    if w["code"] == "review_independence_unrecorded"]
h-mad/tests/test_h_mad_phase7_preconditions.py:698:                    if w["code"] == "review_independence_unrecorded"]
h-mad/tests/test_h_mad_phase7_preconditions.py:699:        assert len(warnings) == 1, "review_independence_unrecorded must warn when the entry list is empty"
h-mad/tests/test_h_mad_phase7_preconditions.py:731:                     "review_independence_unrecorded"):
h-mad/tests/test_h_mad_review_attribution_docs.py:53:    for code in ("review_non_independent", "review_independence_unrecorded",
````

### Per-hit readings

`docs/01-plan/features/agy-coder-fallback.impl-plan.md:1383`

````text
naming leg, module and agent; `review_independence_unrecorded` when `record.get("archreview")` is in
````

Agy-only trigger? NO. The continuation at 1384–1388 explicitly says no implementer condition, and defines archreview in READY_TO_MERGE/WITH_FIXES/NO plus no well-formed 6a-prime entry.

`docs/01-plan/features/agy-coder-fallback.impl-plan.md:1769`

````text
   `review_non_independent`, `review_independence_unrecorded`, `review_independence_malformed`. F.
````

Agy-only trigger? NO. Names the three warning codes for the closure doc pin; the next test explicitly covers every implementer.

`docs/01-plan/features/agy-coder-fallback.impl-plan.md:1831`

````text
- `git grep -n 'review_independence_unrecorded'` over the files this feature edited; each hit is
````

Agy-only trigger? NO. Instructs this sweep to check that no edited surface restricts the trigger to agy.

`docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task12_decisions.md:6`

````text
  `review_independence`, so FR-7's `review_independence_unrecorded` correctly fires. Five tests
````

Agy-only trigger? NO. Describes READY fixtures with archreview=READY_TO_MERGE and no review_independence; the warning is required without a routing condition.

`docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task12_green.report.md:7`

````text
E       AssertionError: assert not [{'code': 'review_independence_unrecorded', 'detail': '6a-prime review independence is unrecorded; authors=unrecorded'}]
````

Agy-only trigger? NO. Historical assertion output reports missing 6a-prime evidence with authors=unrecorded; no implementer restriction.

`docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task12_green.report.md:32`

````text
Blockers: Five existing assertions conflict with the newly required warning. Their READY fixtures contain archreview=READY_TO_MERGE without well-formed 6a-prime review evidence, so FR-7 requires review_independence_unrecorded. These assertions demand no warnings or an exact pre-FR-7 set:
````

Agy-only trigger? NO. Historical blocker explains the archreview/evidence trigger for five old READY fixtures; no agy-only condition.

`docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task12_red.report.md:42`

````text
5. test_unrecorded_fires_for_each_implementer[codex-field-absent] — FAIL; invokes actual p7.check; AssertionError "review_independence_unrecorded must fire independently of routing {}"; behavioral missing-warning failure, not missing-symbol failure.
````

Agy-only trigger? NO. One of five adjacent routing cases (field absent, codex, agy, grok, claude) documenting the same required warning; the agy case is an example, not an exclusive trigger.

`docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task12_red.report.md:43`

````text
6. test_unrecorded_fires_for_each_implementer[codex] — FAIL; invokes actual p7.check; AssertionError names review_independence_unrecorded and routing implementer=codex; behavioral missing-warning failure, not missing-symbol failure.
````

Agy-only trigger? NO. One of five adjacent routing cases (field absent, codex, agy, grok, claude) documenting the same required warning; the agy case is an example, not an exclusive trigger.

`docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task12_red.report.md:44`

````text
7. test_unrecorded_fires_for_each_implementer[agy] — FAIL; invokes actual p7.check; AssertionError names review_independence_unrecorded and routing implementer=agy; behavioral missing-warning failure, not missing-symbol failure.
````

Agy-only trigger? NO. One of five adjacent routing cases (field absent, codex, agy, grok, claude) documenting the same required warning; the agy case is an example, not an exclusive trigger.

`docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task12_red.report.md:45`

````text
8. test_unrecorded_fires_for_each_implementer[grok] — FAIL; invokes actual p7.check; AssertionError names review_independence_unrecorded and implementer_switch.to=grok; behavioral missing-warning failure, not missing-symbol failure.
````

Agy-only trigger? NO. One of five adjacent routing cases (field absent, codex, agy, grok, claude) documenting the same required warning; the agy case is an example, not an exclusive trigger.

`docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task12_red.report.md:46`

````text
9. test_unrecorded_fires_for_each_implementer[claude] — FAIL; invokes actual p7.check; AssertionError names review_independence_unrecorded and implementer_switch.to=claude; behavioral missing-warning failure, not missing-symbol failure.
````

Agy-only trigger? NO. One of five adjacent routing cases (field absent, codex, agy, grok, claude) documenting the same required warning; the agy case is an example, not an exclusive trigger.

`docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task12_red.report.md:47`

````text
10. test_unrecorded_fires_for_each_archreview_value[READY_TO_MERGE] — FAIL; invokes actual p7.check; AssertionError "review_independence_unrecorded must fire for archreview=READY_TO_MERGE"; behavioral missing-warning failure, not missing-symbol failure.
````

Agy-only trigger? NO. One of the three archreview trigger values, independent of routing.

`docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task12_red.report.md:48`

````text
11. test_unrecorded_fires_for_each_archreview_value[WITH_FIXES] — FAIL; invokes actual p7.check; AssertionError "review_independence_unrecorded must fire for archreview=WITH_FIXES"; behavioral missing-warning failure, not missing-symbol failure.
````

Agy-only trigger? NO. One of the three archreview trigger values, independent of routing.

`docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task12_red.report.md:49`

````text
12. test_unrecorded_fires_for_each_archreview_value[NO] — FAIL; invokes actual p7.check; AssertionError "review_independence_unrecorded must fire for archreview=NO"; behavioral missing-warning failure, not missing-symbol failure.
````

Agy-only trigger? NO. One of the three archreview trigger values, independent of routing.

`docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task12_red.report.md:55`

````text
18. test_unrecorded_detail_names_entry_authors_not_routing — FAIL; invokes actual p7.check; AssertionError "review_independence_unrecorded must expose entry authors"; behavioral missing-warning failure, not missing-symbol failure; subsequent assertions require codex, exclude agy, and check sorted distinct authors.
````

Agy-only trigger? NO. Attribution-detail test requires codex from review entries and excludes agy from routing; it does not restrict warning generation to agy.

`docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task12_red.report.md:56`

````text
19. test_unrecorded_detail_without_5e_entries_says_unrecorded — FAIL; invokes actual p7.check; AssertionError "review_independence_unrecorded must warn when the entry list is empty"; behavioral missing-warning failure, not missing-symbol failure; subsequent assertion requires authors=unrecorded.
````

Agy-only trigger? NO. Empty review-entry list requires authors=unrecorded; no agent restriction.

`h-mad/SKILL.md:346`

````text
   Carry every `WARNING` line into the Phase-7 report, including `review_non_independent`, `review_independence_unrecorded` and `review_independence_malformed`; warnings do not change readiness.
````

Agy-only trigger? NO. Requires carrying all three warnings into Phase 7 and leaves readiness unchanged; no routing condition.

`h-mad/SKILL.md:354`

````text
   When no author can be read, no entry is written for the module, in exactly three cases: the record has no `implementation_authors` field (a pre-field feature); the field is present and holds no well-formed entry for that module; or the field is present and is not a list, or holds an entry that is not well-formed (even for another module, invalidating the record's author set). An absent field is never an empty author set. `review_independence_unrecorded` detects no 6a-prime entry at all, but cannot detect one missing module among other recorded modules.
````

Agy-only trigger? NO. Describes absence of any 6a-prime entry and the per-module detection limitation, within an attribution procedure explicitly applying to every implementer.

`h-mad/scripts/h_mad_phase7_preconditions.py:143`

````text
            "code": "review_independence_unrecorded",
````

Agy-only trigger? NO. Read enclosing lines 136–146: branch depends only on the three archreview values and absence of well-formed 6a-prime evidence. Detail derives authors from well-formed 5e entries, never routing.

`h-mad/tests/mutation-specs/review_attribution_docs.json:22`

````text
      "find": "Carry every `WARNING` line into the Phase-7 report, including `review_non_independent`, `review_independence_unrecorded` and `review_independence_malformed`; warnings do not change readiness.",
````

Agy-only trigger? NO. Mutation anchor quotes the all-warning reporting instruction; deletion control adds no implementer condition.

`h-mad/tests/test_h_mad_phase7_preconditions.py:43`

````text
# unrelated to review independence (review_independence_unrecorded would otherwise fire).
````

Agy-only trigger? NO. Comment explains why the REVIEWED fixture supplies a well-formed 6a-prime entry for unrelated exact-warning guards. Its example codex implementer/agy reviewer does not condition the trigger.

`h-mad/tests/test_h_mad_phase7_preconditions.py:623`

````text
                    if w["code"] == "review_independence_unrecorded"]
````

Agy-only trigger? NO. Parameterized over absent field, codex, agy, grok and claude; assertion explicitly requires independence from routing.

`h-mad/tests/test_h_mad_phase7_preconditions.py:625`

````text
            f"review_independence_unrecorded must fire independently of routing {routing!r}"
````

Agy-only trigger? NO. Parameterized over absent field, codex, agy, grok and claude; assertion explicitly requires independence from routing.

`h-mad/tests/test_h_mad_phase7_preconditions.py:635`

````text
                    if w["code"] == "review_independence_unrecorded"]
````

Agy-only trigger? NO. Parameterized over READY_TO_MERGE, WITH_FIXES and NO, with no implementer condition.

`h-mad/tests/test_h_mad_phase7_preconditions.py:637`

````text
            f"review_independence_unrecorded must fire for archreview={archreview}"
````

Agy-only trigger? NO. Parameterized over READY_TO_MERGE, WITH_FIXES and NO, with no implementer condition.

`h-mad/tests/test_h_mad_phase7_preconditions.py:653`

````text
        assert "review_independence_unrecorded" not in {w["code"] for w in result["warnings"]}, (
````

Agy-only trigger? NO. Quiet cases are valid 6a-prime evidence, absent archreview and two skipped statuses, not an agent exemption.

`h-mad/tests/test_h_mad_phase7_preconditions.py:654`

````text
            f"review_independence_unrecorded must stay quiet for {case}"
````

Agy-only trigger? NO. Quiet cases are valid 6a-prime evidence, absent archreview and two skipped statuses, not an agent exemption.

`h-mad/tests/test_h_mad_phase7_preconditions.py:665`

````text
            "review_independence_malformed", "review_independence_unrecorded",
````

Agy-only trigger? NO. Requires malformed 6a-prime evidence to produce both malformed and unrecorded warnings, regardless of agent.

`h-mad/tests/test_h_mad_phase7_preconditions.py:675`

````text
                    if w["code"] == "review_independence_unrecorded"]
````

Agy-only trigger? NO. Tests warning detail from codex/grok 5e entry authors while routing/implementation_authors name agy; agy routing is a deliberately conflicting fixture, not an exclusive trigger.

`h-mad/tests/test_h_mad_phase7_preconditions.py:676`

````text
        assert len(warnings) == 1, "review_independence_unrecorded must expose entry authors"
````

Agy-only trigger? NO. Tests warning detail from codex/grok 5e entry authors while routing/implementation_authors name agy; agy routing is a deliberately conflicting fixture, not an exclusive trigger.

`h-mad/tests/test_h_mad_phase7_preconditions.py:685`

````text
                    if w["code"] == "review_independence_unrecorded"]
````

Agy-only trigger? NO. Tests warning detail from codex/grok 5e entry authors while routing/implementation_authors name agy; agy routing is a deliberately conflicting fixture, not an exclusive trigger.

`h-mad/tests/test_h_mad_phase7_preconditions.py:698`

````text
                    if w["code"] == "review_independence_unrecorded"]
````

Agy-only trigger? NO. Requires warning and authors=unrecorded for an empty entry list despite conflicting agy/grok routing; no exclusivity.

`h-mad/tests/test_h_mad_phase7_preconditions.py:699`

````text
        assert len(warnings) == 1, "review_independence_unrecorded must warn when the entry list is empty"
````

Agy-only trigger? NO. Requires warning and authors=unrecorded for an empty entry list despite conflicting agy/grok routing; no exclusivity.

`h-mad/tests/test_h_mad_phase7_preconditions.py:731`

````text
                     "review_independence_unrecorded"):
````

Agy-only trigger? NO. CLI-output assertion requires printing all warning codes and unchanged READY; no routing restriction.

`h-mad/tests/test_h_mad_review_attribution_docs.py:53`

````text
    for code in ("review_non_independent", "review_independence_unrecorded",
````

Agy-only trigger? NO. Pins reporting of all three warning codes; adjacent test requires review append for every implementer.

## Verification and scope

Ran only the four requested census probes, the new sweep and its control, and bounded in-memory checks of the sweep reader. The reader checks cover a joined-only adjacent literal, a comment-only hit, hard-wrapped Markdown, invalid Python preserving line/comment evidence, and case-insensitivity. Independently compared its physical-line file set against actual `git grep -l -i -E`; the sets match exactly. The fixed 25-name moved set is present in its new owner. No full suite or corpus pytest run was performed.

````text
adjacent-string-only: kinds=['string'] unparsed=False OK
comment-only: kinds=['comment', 'line'] unparsed=False OK
markdown-wrap-only: kinds=['text'] unparsed=False OK
invalid-python: kinds=['comment', 'line'] unparsed=True OK
case-insensitive: kinds=['comment', 'line'] unparsed=False OK
Independent git grep line-set equivalence: 10 files OK
M-4 supplemental: fixed moved names=25 present in scripts/h_mad_target_identity.py
VERIFICATION: PASS
````

Probe compiled in memory, has no trailing whitespace, and `git diff --check` passed. Tracked working-tree diff is empty. The only repository file authored here is fr9_union_sweep.py; the concurrent incident replay probe was not touched. HEAD remained the supplied SHA throughout all captures.

Final observed worktree status:

````text
?? docs/03-analysis/probes/agy-coder-fallback/fr9_incident_replay.py
?? docs/03-analysis/probes/agy-coder-fallback/fr9_union_sweep.py
````

OneContext history lookup was attempted per workspace instructions but was unavailable outside its dashboard session. The supplied current plan and checked-in Task 3 / D5d-6 decisions provided the required evidence. No leak-reaper teardown occurred in these stdlib probes, and the known sandbox artefact was not used as a status input.

All requested readings and per-hit decisions are recorded. No discrepancy remains against the requested post-Task-3, M-4=0, or D5d-6 comparisons. Original census FAIL tokens remain visible as measurement evidence. No commit was made; coordinator check-in remains outside this dispatched write scope.

STATUS: DONE
