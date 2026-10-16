Files changed:

- `h-mad/tests/test_h_mad_tdd_gate_peers.py` (new; 14 tests).
- No production code, existing test file, fixture-consequence literal, mutation spec, probe, or workflow state was edited. No commit was created.

pytest output (last 10 lines of the requested scoped RED run):

Command: `hmad-dispatch run --timeout 600 -- /opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_tdd_gate_peers.py -v` (invoked through `rtk proxy`).

```text
FAILED h-mad/tests/test_h_mad_tdd_gate_peers.py::test_format_state_line_takes_the_author_from_resolve_implementer
FAILED h-mad/tests/test_h_mad_tdd_gate_peers.py::test_hook_reads_authorship_from_the_state_line_not_the_environment
FAILED h-mad/tests/test_h_mad_tdd_gate_peers.py::test_agy_authorship_refused_when_agy_resolves
FAILED h-mad/tests/test_h_mad_tdd_gate_peers.py::test_implementer_invalid_refused
FAILED h-mad/tests/test_h_mad_tdd_gate_peers.py::test_implementer_invalid_outranks_codex_authorship
FAILED h-mad/tests/test_h_mad_tdd_gate_peers.py::test_chain_fold_blocks_on_the_first_eligible_record
FAILED h-mad/tests/test_h_mad_tdd_gate_peers.py::test_today_shape_state_line_is_judge_error
FAILED h-mad/tests/test_h_mad_tdd_gate_peers.py::test_agy_authorship_message_names_the_dispatch_and_the_switches
ERROR h-mad/tests/test_h_mad_tdd_gate_peers.py::test_three_message_bodies_match_a8d9ba99
==================== 8 failed, 6 passed, 1 error in 10.79s =====================
```

Regression command: `hmad-dispatch run --timeout 600 -- /opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_tdd_gate_judge.py h-mad/tests/test_h_mad_tdd_gate_fallback_agent.py h-mad/tests/test_h_mad_tdd_judge.py -q` (invoked through `rtk proxy`). Last 10 lines:

```text
                if errno_num != 0:
                    err_msg = os.strerror(errno_num)
                if err_filename is not None:
>                   raise child_exception_type(errno_num, err_msg, err_filename)
E                   PermissionError: [Errno 1] Operation not permitted: 'ps'

/opt/anaconda3/lib/python3.11/subprocess.py:1953: PermissionError
=========================== short test summary info ============================
ERROR h-mad/tests/test_h_mad_tdd_judge.py::test_three_nine_floor[h_mad_audit_gate]
451 passed, 1 error in 252.00s (0:04:12)
```

Environment note: both sessions encountered the coordinator-declared sandbox-only session-teardown artifact, `conftest.py -> find_leaked -> ps -> PermissionError`. This is not a test-body failure and does not decide STATUS. The message-byte test itself passed before session teardown. No fixture was disabled or modified. An initial attempt to start regression guards while the RED session still held the tree lock was refused with `SUITE: BUSY` (exit 75; nothing measured); the regression command above was then run after RED completed. The first measured regression run had 451 passing test bodies and no assertion failures.

Self-review findings:

The requested split is reproduced exactly across the 14 test bodies: failures at items 1, 2, 3, 5, 8, 10, 11, 13; passes at items 4, 6, 7, 9, 12, 14. Every failing test fails through an AssertionError about observable caller behavior. There is no ImportError, AttributeError, or NameError standing in for a wire assertion. Task 2's resolver and Implementer type already exist.

Per-test RED acceptance evidence (one entry per test; names below are in `h-mad/tests/test_h_mad_tdd_gate_peers.py`):

1. `test_format_state_line_takes_the_author_from_resolve_implementer` — FAIL, WIRE-PIN 1, existing-callee wiring assertion. Invokes `judge.read_chain` then the actual caller `judge.format_state_line`, with `judge.resolve_implementer` replaced by a recording fake returning `Implementer("agy", "agy", None, None, "")`. Failure mode: "format_state_line must propagate resolve_implementer's author into the fourth comma field"; actual `['absent', 'absent']`, expected `['agy', 'agy']`. The serialization method contains the missing connection. The same test also requires one resolver call per record in chain order and shared env/which inputs.
2. `test_hook_reads_authorship_from_the_state_line_not_the_environment` — FAIL, WIRE-PIN 2, caller-decision assertion. Invokes `_gate`, executing the copied actual HOOK and its `_read_state` against a judge stub returning author `peers-out`, codex status `available`, and ALLOW. Codex is on the isolated PATH and HMAD_CODEX_UNAVAILABLE is unset. Failure mode: "_read_state must honor author=peers-out despite codex on PATH and no unavailable override"; actual deny/judge-error with "state verb printed no well-formed state line", expected allow. `_read_state` contains the state consumption being pinned. This fixture also distinguishes the planned wire cut and the forced-codex converse.
3. `test_agy_authorship_refused_when_agy_resolves` — FAIL, behavioral assertion. Invokes `_gate` with the real judge, explicit implementer `agy`, exhausted codex and an agy stub in this test's bin directory. The actual HOOK main refusal block should consume `_read_state` authorship. Failure: "a resolved agy implementer must refuse Claude authorship"; expected deny/agy-authorship, got allow.
4. `test_codex_authorship_refused_when_codex_resolves` — PASS, regression guard. Invokes `_gate` with the real judge and codex stub; asserts deny/codex-authorship and the decoded hostile feature key and state-file path. Non-vacuous: deleting the codex-authorship refusal lets the deliberately RED name-mapped test allow the write, failing this assertion. The behavior resides in the actual HOOK main refusal block.
5. `test_implementer_invalid_refused` — FAIL, behavioral assertion. Invokes `_gate` with the real judge, implementer `gpt` and both peers exhausted. Failure: "an invalid implementer must fail closed"; expected deny/implementer-invalid, got allow. The HOOK main invalid-author precedence is the missing behavior. The test additionally requires the JSON value `implementer="gpt"` and `--set implementer=codex|agy|null` repair.
6. `test_fallback_grok_refused_when_peers_out` — PASS, regression guard. Invokes `_gate` with the real judge and both peers exhausted; asserts deny/fallback-grok and `hmad-dispatch exec grok`. Non-vacuous: removing the actual HOOK fallback-grok arm lets the deliberately RED test allow the write, failing the assertion.
7. `test_fallback_invalid_refused_when_peers_out` — PASS, regression guard. Invokes `_gate` with the real judge, both peers exhausted and a hostile invalid fallback string. Asserts deny/fallback-invalid, surviving marker text and the repair switches. Non-vacuous: removing the actual HOOK fallback-invalid arm permits the RED-test path and fails the assertion.
8. `test_implementer_invalid_outranks_codex_authorship` — FAIL, behavioral precedence assertion. Invokes `_gate` with the real judge and ordered records `[codex-available, invalid]`. Failure: "a later invalid implementer must outrank the first peer"; expected deny/implementer-invalid, got deny/codex-authorship. The actual HOOK must scan every record in `_read_state` before its main refusal precedence. The test also requires the later hostile key and implementer repair in the reason.
9. `test_peer_refusal_outranks_fallback_invalid` — PASS, regression guard. Invokes `_gate` with the real judge and ordered records `[codex-available, peers-out/invalid-fallback]`; asserts deny/codex-authorship identifying the first hostile key. Non-vacuous: deleting peer refusal or moving fallback-invalid ahead of it produces a fallback-invalid decision and fails the assertion. This exercises the actual HOOK main precedence.
10. `test_chain_fold_blocks_on_the_first_eligible_record` — FAIL, behavioral ordering assertion. Invokes `_gate` with the real judge, records `[agy, codex]`, and both peer stubs. Failure: "the first eligible chain record must select the refusing peer"; expected deny/agy-authorship, got deny/codex-authorship. The actual `_read_state` scan/main refusal block must select the first peer. Subsequent assertions require the first hostile key and exclude the second key.
11. `test_today_shape_state_line_is_judge_error` — FAIL, behavioral grammar assertion. Invokes `_gate` with the actual copied HOOK and an explicit old four-field state-line stub plus ALLOW. Failure: "the old four-field state record must be rejected"; expected deny/judge-error, got allow. `_read_state` contains the grammar validation. This fixture stays explicitly four-field when the shared default changes at GREEN.
12. `test_unknown_author_field_is_judge_error` — PASS, closed-author-set guard. Invokes `_gate` with the actual copied HOOK and a five-field record whose author is `grok`, plus ALLOW. As specified, RED rejects this extra field already; after GREEN it pins the closed author alternation in `_read_state`. Non-vacuous for that contract: removing author validation or admitting grok allows the stub verdict and fails the deny/judge-error assertion.
13. `test_agy_authorship_message_names_the_dispatch_and_the_switches` — FAIL, behavioral message assertion. Invokes `_gate` with the real judge and agy stub. Failure: "the agy refusal must explain the agy dispatch and switches"; expected deny/agy-authorship, got allow. The actual HOOK agy refusal body is the behavior under test; after that assertion it requires `hmad-dispatch exec agy`, `h_mad_assemble_tdd.py --agent agy`, `--set agy_status=exhausted`, `export HMAD_AGY_UNAVAILABLE=1 for a one-off`, `h_mad_tdd_judge.py implementer`, the hostile feature key and state path.
14. `test_three_message_bodies_match_a8d9ba99` — PASS, byte regression guard. Invokes `git show a8d9ba99:h-mad/hooks/h-mad-tdd-gate.sh` and reads the actual HOOK text; deliberately a source-literal comparison rather than a runtime refusal call. Extracts exactly one literal for each of codex-authorship, fallback-grok and fallback-invalid; normalizes PEER_ to BLOCKER_ on both sides; asserts equality. Non-vacuous: deleting a refusal fails the exactly-one count, and changing its body fails byte equality, except the expressly permitted variable rename.

Additional checks:

- Hostile input fixture sets `HMAD_STUB_HOSTILE=all`, clears ambient peer/host overrides and uses actual hostile feature keys containing quotes, backslashes, a newline, marker text, percent, comma, glob characters and Unicode. The invalid-fallback test also passes that hostile payload as the field value. Protocol enumerators and the specifically prescribed invalid value `gpt` retain their specified spellings.
- Real-judge `_gate` calls explicitly use `path_tail="/usr/bin:/bin"`. Every PATH directory is colon-free; hostile data stays in record contents. The new file writes its own agy executable into the existing `_bin` result and does not edit `_bin`.
- Existing helpers HOOK, TARGET, _bin, _gate, _root and _tree_b are imported directly from `test_h_mad_tdd_gate_judge` following the adjacent fallback-agent file's pattern.
- Final `git status --short` lists only `?? h-mad/tests/test_h_mad_tdd_gate_peers.py`; tracked `git diff --name-only` is empty. `git diff --no-index --check /dev/null h-mad/tests/test_h_mad_tdd_gate_peers.py` emitted no whitespace findings.
- All 14 specified nodes exist. Functional precedence, the two connections, stale/unknown grammar and message preservation have corresponding tests. No assertion was weakened and no artificial failure was inserted into the new test bodies. The small name-mapped failing test fixtures intentionally exercise the gate's existing RED-allow path.
- GREEN-only production changes, the three fixture-consequence literals, grammar shipped/control probe, mutation-spec creation/re-anchoring, wire-cut/converse execution and census are deferred to Phase 5e as directed. No mutation spec was written and no full suite was run.
- Required OneContext lookup was attempted, but the CLI reported that context is unavailable outside a OneContext dashboard session. The supplied task and repository evidence were sufficient; this did not block RED.

Concerns: Phase 5e remains required: the eight expected assertion failures demonstrate that author-field serialization and hook authorship precedence are still unimplemented. This RED-only dispatch is complete, but it cannot claim GREEN. There are no unexpected test-body failures or unresolved implementation-scope questions.

Summary: Added only the requested new test file; reproduced 8 failing / 6 passing test bodies with both wire pins failing on caller assertions; all 451 existing regression test bodies passed. The declared sandbox teardown artifact is excluded from the phase verdict. The next and final delivery action creates this report's `.done` marker.

🌱 graft saved ~48,019 tokens this turn, 3 calls.

STATUS: DONE_WITH_CONCERNS
