Files changed:
- h-mad/scripts/h_mad_tdd_judge.py
- h-mad/hooks/h-mad-tdd-gate.sh
- h-mad/tests/test_h_mad_tdd_gate_judge.py — only the _tree_b default state_line literal.
- h-mad/tests/test_h_mad_tdd_gate_fallback_agent.py — only the RECORD literal.
- h-mad/tests/test_h_mad_tdd_judge.py — only the ACTIVE_RE literal.
- h-mad/tests/mutation-specs/claude_gate_judge_wiring.json — W5BF, W5BF2, W5BF3 replacement records re-shaped.
- h-mad/tests/mutation-specs/tdd_gate_peers.json — seven new rows.

pytest output (last 10 lines):

Standalone requested peer run:
`hmad-dispatch run --timeout 180 -- /opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_tdd_gate_peers.py -v`

```text
                if errno_num != 0:
                    err_msg = os.strerror(errno_num)
                if err_filename is not None:
>                   raise child_exception_type(errno_num, err_msg, err_filename)
E                   PermissionError: [Errno 1] Operation not permitted: 'ps'

/opt/anaconda3/lib/python3.11/subprocess.py:1953: PermissionError
=========================== short test summary info ============================
ERROR h-mad/tests/test_h_mad_tdd_gate_peers.py::test_three_message_bodies_match_a8d9ba99
========================= 14 passed, 1 error in 2.28s ==========================
```

Final settled-tree scoped regression run:
`hmad-dispatch run --timeout 600 -- /opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_tdd_gate_*.py h-mad/tests/test_h_mad_tdd_judge.py -q --tb=short`

```text
    with Popen(*popenargs, **kwargs) as process:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^
/opt/anaconda3/lib/python3.11/subprocess.py:1026: in __init__
    self._execute_child(args, executable, preexec_fn, close_fds,
/opt/anaconda3/lib/python3.11/subprocess.py:1953: in _execute_child
    raise child_exception_type(errno_num, err_msg, err_filename)
E   PermissionError: [Errno 1] Operation not permitted: 'ps'
=========================== short test summary info ============================
ERROR h-mad/tests/test_h_mad_tdd_judge.py::test_three_nine_floor[h_mad_audit_gate]
527 passed, 1 error in 274.75s (0:04:34)
```

Self-review findings:
- Implemented the fifth record field through resolve_implementer exactly once per record, with one env snapshot and which binding per format_state_line call.
- Only implementer invalidity produces author=invalid:<percent-encoded JSON>; exhausted peers, including an invalid fallback, produce peers-out so the existing fallback fold and refusal block retain their role.
- The hook reads the author after stripping three leading fields. It scans the full chain for the first invalid implementer and the first eligible peer. Precedence is implementer-invalid, then codex/agy-authorship, then fallback policy.
- Header integrity checks and _fallback_fold are unchanged. BLOCKER_RECORD was removed.
- The codex-authorship, fallback-grok, and fallback-invalid message bodies pass the byte-preservation regression against a8d9ba99 (normalizing only PEER_/BLOCKER_ variable names).
- The new agy text names all five required dispatch/status/diagnostic switches.
- git diff against a8d9ba99 for the three fixture files contains exactly the three permitted literal edits. _bin and every other existing test_h_mad_tdd_gate_*.py remain unchanged. The Phase-5d peer tests were not modified.
- The initial peer run reproduced the specified 8 failing / 6 passing split. WIRE-PIN 1 failed with "format_state_line must propagate resolve_implementer's author into the fourth comma field"; WIRE-PIN 2 failed with "_read_state must honor author=peers-out despite codex on PATH and no unavailable override" and kind=judge-error. Both were caller assertions, with the resolver present.
- Final standalone peer assertions: 14 passed. Final scoped regression assertions: 527 passed, including the peer tests. No full or unscoped suite was run.
- An earlier regression run overlapped mutation-spec edits and printed SUITE: TREE_MOVED; it was discarded. The final run above used the settled tree and printed no TREE_MOVED warning.
- Bash 3.2 and Bash 5.3 syntax checks, Python AST parsing, and git diff --check all passed.
- No implementation or self-review issues remain.

Known sandbox artifact (excluded from STATUS as explicitly instructed):
The session leak-reaper teardown invokes ps, which this sandbox denies with PermissionError. Both pytest commands therefore exit 1 despite every test assertion passing. The standard new-spec harness consequently reports MUTATION: BASELINE_NOT_GREEN before applying any mutant. No test, fixture, harness, or production behavior was weakened to suppress this error. Standard mutation scoring must be repeated by the coordinator outside this sandbox; this report does not claim MUTATION: ALL_CAUGHT.

Mutation evidence:
- Reviewed all 96 pre-existing rows targeting the production files: 56 hook rows and 40 judge rows (including Task 2's four).
- All pre-existing find anchors still matched exactly once. No find or test ID needed relocation.
- Re-shaped replacement records in claude_gate_judge_wiring.json rows W5BF, W5BF2, W5BF3 from four fields to five, retaining their forced codex-authorship intent and original test IDs. These are the complete list of moved/updated existing rows.
- New rows: fr3-implementer-invalid-dropped; fr3-invalid-scan-first-record-only; fr3-agy-arm-dropped; fr3-peers-out-alternative-dropped; wire1-author-not-from-resolver; wire2-hook-rederives-from-env; wire2-every-author-is-a-peer.
- symbol is set to format_state_line for WIRE 1 and _read_state for the invalid scan and both WIRE 2 rows. It is omitted only for top-level shell sites: fr3-implementer-invalid-dropped, fr3-agy-arm-dropped, fr3-peers-out-alternative-dropped.
- Supplemental assertion-only validation used scratch copies of production files and invoked each unchanged named test body, including its hostile-input fixture (HMAD_STUB_HOSTILE=all). Seven baseline executions passed; each of the seven corresponding mutants failed its intended behavioral assertion. No worktree production files were mutated by this supplemental check.
- Reproducible supplemental artifact: /private/tmp/claude-501/-Users-kimhawk-orca-skills/c83a0ffe-4d6b-4b3a-bac9-efa79608444a/scratchpad/acf5d/t3pin_probe.py
- Supplemental invocation: `hmad-dispatch run --timeout 180 -- /opt/anaconda3/bin/python3 <artifact-path> /Users/kimhawk/orca/workspaces/skills/agy-coder-fallback`
- Supplemental last line: `SUPPLEMENTAL: 7/7 original test bodies pass on baseline and fail on their scratch mutants`
- WIRE 1's cut failed on "format_state_line must propagate resolve_implementer's author into the fourth comma field".
- WIRE 2's environment cut and forced-peer converse each denied codex-authorship where its original test requires allow.
- This supplementary check invokes original assertions without pytest session machinery; it supplements, rather than replaces, the normal harness verdict.
- Only tdd_gate_peers.json was attempted without --check-anchors. The other eleven full sweeps remain coordinator-owned, as instructed.

Anchor check over all twelve required specs:
```text
ANCHORS: claude_gate_judge_wiring.json ok ok=45/45
ANCHORS: grok_wire_reverts.json ok ok=14/14
ANCHORS: tdd_gate_differential.json ok ok=8/8
ANCHORS: tdd_gate_fallback_agent.json ok ok=12/12
ANCHORS: tdd_gate_scratchpad.json ok ok=5/5
ANCHORS: tdd_judge_chain.json ok ok=6/6
ANCHORS: tdd_judge_resolution.json ok ok=8/8
ANCHORS: tdd_judge_scoring.json ok ok=10/10
ANCHORS: tdd_judge_venv.json ok ok=3/3
ANCHORS: tdd_judge_wiring.json ok ok=6/6
ANCHORS: tdd_judge_implementer.json ok ok=4/4
ANCHORS: tdd_gate_peers.json ok ok=7/7
ANCHORS: ANCHORS_OK specs=12 mutations=128 ok=128 drifted=0 unreadable=0 skipped=0 unclassifiable=0
```
The existing H3 self-matching advisory remains unchanged.

The requested standalone new-spec anchor command used /Users/kimhawk/orca/skills/h-mad/scripts/h_mad_mutation_harness.py:
```text
ANCHORS: tdd_gate_peers.json ok ok=7/7
ANCHORS: ANCHORS_OK specs=1 mutations=7 ok=7 drifted=0 unreadable=0 skipped=0 unclassifiable=0
[H-MAD] anchors ANCHORS_OK
```
The last line is quoted verbatim above. Its only symbol advisory concerns the three documented top-level shell sites.

Grammar probe:
Command: `/opt/anaconda3/bin/python3 docs/03-analysis/probes/agy-coder-fallback/fr3_state_line_grammar.py /bin/bash /opt/homebrew/bin/bash`
```text
shipped literal == grammar derived from a8d9ba99
mode=shipped control=no hook=h-mad/hooks/h-mad-tdd-gate.sh
grok-fold: python=match want=match
grok-fold: bash 3.2.57(1)-release groups 1,2,3,4,6 == python
grok-fold: bash 5.3.20(1)-release groups 1,2,3,4,6 == python
agy-record: python=match want=match
agy-record: bash 3.2.57(1)-release groups 1,2,3,4,6 == python
agy-record: bash 5.3.20(1)-release groups 1,2,3,4,6 == python
invalid-implementer: python=match want=match
invalid-implementer: bash 3.2.57(1)-release groups 1,2,3,4,6 == python
invalid-implementer: bash 5.3.20(1)-release groups 1,2,3,4,6 == python
today-shape: python=nomatch want=nomatch
today-shape: bash 3.2.57(1)-release groups 1,2,3,4,6 == python
today-shape: bash 5.3.20(1)-release groups 1,2,3,4,6 == python
author-grok: python=nomatch want=nomatch
author-grok: bash 3.2.57(1)-release groups 1,2,3,4,6 == python
author-grok: bash 5.3.20(1)-release groups 1,2,3,4,6 == python
PROBE: PASS
```

Same command with --control:
```text
shipped literal == grammar derived from a8d9ba99
mode=shipped control=yes hook=h-mad/hooks/h-mad-tdd-gate.sh
grok-fold: python=nomatch want=match
grok-fold: bash 3.2.57(1)-release groups 1,2,3,4,6 == python
grok-fold: bash 5.3.20(1)-release groups 1,2,3,4,6 == python
agy-record: python=match want=match
agy-record: bash 3.2.57(1)-release groups 1,2,3,4,6 == python
agy-record: bash 5.3.20(1)-release groups 1,2,3,4,6 == python
invalid-implementer: python=match want=match
invalid-implementer: bash 3.2.57(1)-release groups 1,2,3,4,6 == python
invalid-implementer: bash 5.3.20(1)-release groups 1,2,3,4,6 == python
today-shape: python=nomatch want=nomatch
today-shape: bash 3.2.57(1)-release groups 1,2,3,4,6 == python
today-shape: bash 5.3.20(1)-release groups 1,2,3,4,6 == python
author-grok: python=nomatch want=nomatch
author-grok: bash 3.2.57(1)-release groups 1,2,3,4,6 == python
author-grok: bash 5.3.20(1)-release groups 1,2,3,4,6 == python
PROBE: FAIL
```

Post-Task M-3 reading:
- Re-ran the unchanged census_mutation_rows.py with --root h-mad. The probe uses git ls-files, so its tracked-only reading excludes the new, untracked peer spec: 9 rows / 4 specs (5 claude_gate_judge_wiring, 1 tdd_gate_fallback_agent, 2 tdd_judge_chain, 1 tdd_judge_implementer).
- Reused that probe's exact PATTERN over all working-tree spec files to include the new spec: 10 rows / 5 specs. Distribution: claude_gate_judge_wiring.json=5; tdd_gate_fallback_agent.json=1; tdd_gate_peers.json=1; tdd_judge_chain.json=2; tdd_judge_implementer.json=1.
- The added M-3 row is wire2-hook-rederives-from-env; Task 2's fr2-cause-status-dropped accounts for the other increase over the original 8-row reading.
- The original census emits PROBE: FAIL because its plan-time EXPECT values and old authorship-block boundary intentionally were not re-baselined; it is a census reading, not the FR-3 grammar probe. M-4 remains 62 rows / 31 moved rows / 4 specs, with zero absent or non-unique anchors.
- No probe files, repository index, commits, or phase state were changed.

Acceptance review:
- AC-3.1: items 3–10 pass.
- AC-3.2: old-shape rejection and byte-preservation guards pass; exactly the three fixture literals changed.
- Both WIRE-PINs pass on production; both cuts and the WIRE 2 converse fail the intended original test assertions on scratch copies.
- Grammar probe: shipped/PASS on both bashes; control/FAIL.
- All twelve anchor checks: ANCHORS_OK. Formal ALL_CAUGHT sweeps remain the coordinator's external validation; no unmeasured sweep is presented as passing.

Concerns: none in the implementation or self-review. The known sandbox limitation is reported separately above and does not determine STATUS, per dispatch.

🌱 graft saved ~46,012 tokens this turn, 3 calls.

STATUS: DONE
