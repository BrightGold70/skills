# codex-tdd-gate-defects analysis

## DD-7 differential

The probe at `docs/03-analysis/probes/codex-tdd-gate-defects/dd7_differential.py`
compared the pre-feature hook from `git show main:h-mad/hooks/h-mad-tdd-gate.sh`
(`main` at `aa5c43c747af21790e7463a6ca472595088c8e95`) with the worktree hook.
It ran all 126 positional-input cells with a resolved temporary root, a Codex stub,
and an active or step3-only state. The command exited 0 with
`DD7: DONE cells=126 softened=6 tightened=8`. The six softened cells were the
active relative `tests/x.py` and `fixtures/x.py` cells for each of the three
root shapes. The eight tightened cells were active dot-prefixed and absolute
`tests/../x.py` for each shape, plus active absolute `x.py` for roots under
`tests/repo` and `fixtures/repo`. There were no other changed cells.

## Baseline at BASE_SHA

Task 0 was run in `/Users/kimhawk/orca/skills-codex-tdd-gate-defects` on branch
`feature/codex-tdd-gate-defects`. The command
`python3 h-mad/scripts/h_mad_baseline_sha.py --branch feature/codex-tdd-gate-defects`
returned `BASELINE: OK sha=d68635159ad5ec64b03d2852dc25536c4e3ea657 branch=feature/codex-tdd-gate-defects trunk=main`.
Thus `BASE_SHA=d68635159ad5ec64b03d2852dc25536c4e3ea657`.

### P0 and V-0

`git show "$BASE_SHA:<path>"` confirms that all four P0 probes are committed at
`BASE_SHA`; SHA-256 of their committed bytes matches the plan's pins:

| Probe | SHA-256 |
| --- | --- |
| `reproduce.py` | `45f763ee14162b4747fe1c3dee3afa1478f9cc86d2599717f3993bd34939d974` |
| `v0-blocking-contract.sh` | `04700d9ffc254a603387f4baf1a62a1b115956fd410d88c3484db3fc50ddaff4` |
| `v1-offline-replay.sh` | `8dd639240265d338ee24aa6a52e80929302c52c14ee8c41b8bb9360cd2e4ee10` |
| `wire-registry-grammar.py` | `9d20448039ca662b646981fbb57ddc1879fa852faaaa4dbef2b0654150b82650` |

The committed `reproduce.reading.a35707b8.txt` has 24 `REPRO:` lines.
`wire-registry-grammar.reading.a35707b8.txt` ends with
`WRGRAMMAR: files=84 task_counter_divergent_files=4 singular_label_multi_path_lines=14 axis_label_lines_unread_by_registry=64` followed by its divergent file list.
`v1-offline-replay.reading.a35707b8.txt` ends with
`V-1r: DONE VERDICT=FAIL fails=4/6 skills=a35707b8 hemasuite_red=1fbf8022 hemasuite_green=31bfcfe4` followed by its scratch path.

`git show "$BASE_SHA:docs/03-analysis/probes/codex-tdd-gate-defects/v0.out"`
has no committed file: **V-0 not yet run**. Task 8 waits for V-0; Tasks 1–7 do not.

### Suite, collection and anchors

The full suite command is
`/opt/anaconda3/bin/python -m pytest -q -p no:cacheprovider h-mad/tests handoff/tests handoff/scripts`.
Its subprocess environment strips every `CLAUDE*` variable, `HPW_AGENT_BACKEND`,
and `HMAD_HOST`. A parent with `CLAUDE_ZZZ_PROBE=1` produced a child with zero
`CLAUDE*` variables and no `HPW_AGENT_BACKEND` or `HMAD_HOST`.

The suite returned exit 1. Its `tail -3` is:

```text
=========================== short test summary info ============================
FAILED h-mad/tests/test_h_mad_check_plugin_hooks.py::TestAgainstTheLiveBinary::test_top_level_key_set_still_matches
1 failed, 3892 passed, 1 warning in 540.44s (0:09:00)
```

That node fails at `h-mad/tests/test_h_mad_check_plugin_hooks.py:138` because
`hits == []`: the installed Claude binary has no occurrence of
`new Set(["description","hooks","modules","surface"])`. The assertion says
`TOP` in `h_mad_check_plugin_hooks.py` may be stale. There are no other failing
nodes. The complete run output is `/private/tmp/hmad-ctg-task0-suite.txt`.

The node-id command is
`/opt/anaconda3/bin/python -m pytest --collect-only -q -p no:cacheprovider h-mad/tests handoff/tests handoff/scripts 2>&1 | grep '::' | sort`.
It returned `3893 tests collected in 0.46s`, exit 0, and wrote 3893 sorted
node IDs to `/private/tmp/hmad-ctg-base-nodeids.txt`. The intended git-dir path
is `/Users/kimhawk/orca/skills/.git/worktrees/skills-codex-tdd-gate-defects/hmad-ctg-base-nodeids.txt`;
the worker sandbox cannot write there, so the orchestrator must place the file.
The collection subprocess also received no `CLAUDE*`, `HPW_AGENT_BACKEND`, or
`HMAD_HOST` values despite ambient `CLAUDE_ZZZ_PROBE=1`.

`/opt/anaconda3/bin/python h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/*.json`
returned exit 0 and
`ANCHORS: ANCHORS_OK specs=99 mutations=907 ok=907 drifted=0 unreadable=0 skipped=0 unclassifiable=0`.

### Top-level diff probe controls

`docs/03-analysis/probes/codex-tdd-gate-defects/toplevel_diff.py` is a stdlib
probe of modified Python test files, their existing ancestor `conftest.py`
files, and existing imported sibling modules. It compares top-level AST source
segments and reports changed and removed keys.

- C0.1: `/opt/anaconda3/bin/python docs/03-analysis/probes/codex-tdd-gate-defects/toplevel_diff.py --base "$BASE_SHA" --head "$BASE_SHA"`
  returned `TOPDIFF: DONE files=0 changed=0 removed=0`, exit 0.
- C0.2: a `tempfile.TemporaryDirectory` repository with two commits changed
  `test_x` and removed `test_y`. `/opt/anaconda3/bin/python <probe> --repo <tmp> --base <first-commit>`
  returned `TOPDIFF: changed h-mad/tests/test_a.py::test_x`,
  `TOPDIFF: removed h-mad/tests/test_a.py::test_y`, and
  `TOPDIFF: DONE files=1 changed=1 removed=1`, exit 0.
- C0.3: `/opt/anaconda3/bin/python docs/03-analysis/probes/codex-tdd-gate-defects/toplevel_diff.py --base deadbeef`
  returned `TOPDIFF: UNREADABLE reason=bad_sha`, exit 2.

An additional temporary-repository check changed a test that imports an
unchanged sibling module and has an unchanged `conftest.py`; the probe returned
`TOPDIFF: DONE files=3 changed=1 removed=0`, confirming both supporting files
were included.

### Shell-policy differential

Task 7 compared the hook at `BASE_SHA=d68635159ad5ec64b03d2852dc25536c4e3ea657`
with the uncommitted GREEN hook in this worktree. The old hook came from
`git show "$BASE_SHA":h-mad/hooks/h-mad-codex-tdd-gate.py`; the probe staged
it beside a symlink to this worktree's `h-mad/scripts` so both hooks resolved
the same scripts root. SHA-256: old hook
`cde57cc8d6604143e7c91886fb362561a80da6d8a9664db721ec0e18b3a9dfe0`,
new hook `90513b85f2f8fe0124d203839dca340ef8f3fb93866f8d3226826e66b84627ae`,
probe `e038929d578f58aec4c008dd87f6936e59862f5dbb612ba370f687b34ff24edd`.

`/opt/anaconda3/bin/python docs/03-analysis/probes/codex-tdd-gate-defects/shell_differential.py --old /private/tmp/hmad-codex-tdd-gate-old.py --new h-mad/hooks/h-mad-codex-tdd-gate.py`
returned exit 0 and `SHELLDIFF: DONE rows=251 softened=14 tightened=0 unexpected=0`.
The 14 changed rows are the seven contained venv token spellings with each of
`-m pytest` and the allowed `h_mad_state_write.py` invocation. All 234 deny
rows and three pre-existing allow controls retained their verdicts.

## Task 10 re-verification (orchestrator)

Codex returned `STATUS: DONE_WITH_CONCERNS`. The orchestrator re-ran each of the eight specs:
`--check-anchors` gave `ANCHORS_OK` for all eight (15 + 37 + 17 + 6 + 8 + 6 + 3 + 6 = 98 rows),
and the harness gave `ALL_CAUGHT … crash_kills=0` for all eight. One transient: in the sequential
sweep `tdd_judge_wiring.json` read `MUTATION: BASELINE_NOT_GREEN`; its baseline command alone
read `113 passed`, and an isolated harness re-run read `ALL_CAUGHT mutations=6 caught=6`. The
likely mechanism is the in-tree `conftest.py` mutation below. Task 8's three wires: W2R, W5BR and
W6R replace each wire with a constant and are killed by WIRE-PIN 1, 2 and 3; W2F, W5BF–W5BF3 and
W6F force the opposite outcome. Deviation: Task 1's planned `# M:S…` tags are absent from the
committed audit parser, so the S rows and W4C anchor on the equivalent lines (plan text stale).
Committed as `ab83ae92`.

**Finding (pre-existing, outside this feature):** `test_h_mad_pin_file_guard.py` (since
`b1f8954c`, 2026-08-22) and `test_h_mad_wire_registry.py` run the mutation harness against the
tracked `h-mad/tests/conftest.py` in place. `git status` taken mid-suite showed
`M h-mad/tests/conftest.py`, clean a moment later. Any pytest running concurrently in the same
tree imports the mutated conftest. This is the likely cause of the post-Task-9
`test_wire_registry_guard_mutation_is_caught_by_harness` failure, which passed 3 of 3 alone.

## Task 11 — phase-5 merge gate readings

At worktree `HEAD` `ab83ae92`, `BASE_SHA=d68635159ad5ec64b03d2852dc25536c4e3ea657`.

1. **Suite.** `1 failed, 4196 passed, 1 warning in 700.61s`; with `CLAUDE_ZZZ_PROBE=1` exported,
   `1 failed, 4196 passed, 1 warning in 701.50s`. Both failures are
   `test_top_level_key_set_still_matches` at `test_h_mad_check_plugin_hooks.py:138`, the same
   reason Task 0 recorded. Collected 4197 = 3893 + 304. PASS.
2. **Node-id floor.** `comm -23` (both sides `LC_ALL=C sort`) printed 0 lines. PASS.
3. **Top-level diff.** First reading: `TOPDIFF: DONE files=5 changed=20 removed=0` against the
   19 keys of §"Regression provenance" (form b). **FAIL at plan v1.2.** The extra key is
   `test_h_mad_audit_suite_gate.py::run`; its only change (Task 1 RED `fbd78d91`) is
   `stdin=subprocess.DEVNULL` (Convention 4). The provenance was amended (plan v1.3, 20 keys); the
   re-run reads `changed=20`, equal key for key. PASS after amendment.
4. **Anchors.** `ANCHORS: ANCHORS_OK specs=107 mutations=1005 ok=1005 drifted=0`. PASS.
5. **Self-check.** `CODEX-TDD-GATE: PASS`. PASS.
6. **V-1r.** `V-1r: DONE VERDICT=PASS fails=0/6 skills=ab83ae92 hemasuite_red=1fbf8022
   hemasuite_green=31bfcfe4` (`probes/…/v1-offline-replay.reading.ab83ae92.txt`). PASS.
7. **`reproduce.py` post-merge.** `D3 nopytest` and `OD-3 nearest-state` read `(0, 'deny', …)`
   (Codex side); `OD-4 tool_input`, `OD-3c claude-root-first` and `OD-5 nopytest` read
   `(0, 'deny', '[H-MAD-TDD-GATE] BLOCK kind=…')` (Claude side, form b). The plan's `(0, 'deny', '')`
   expected an empty stderr; design line "the gate writes the reason to stderr under both forms"
   says otherwise, and the shipped `_refuse` follows the design. Plan text stale; all five
   fail-opens are closed. Reading: `probes/…/reproduce.reading.ab83ae92.txt`. PASS.
8. **5g greps.** 0, 0, 0, no match, 0, empty diff. PASS.
9. **Stale prose.** The census now lists `SKILL.md 6, agy-runtime.md 2,
   codex-implementer-prompt.md 1, codex-runtime.md 2, h_mad_derive_test_path.sh 1,
   h_mad_hook_wiring.py 1, h_mad_install_check.py 3, h_mad_tdd_judge.py 1`. All four known-false
   candidates are rewritten (agy "exit-code protocol" gone; judge registered beside the mapper;
   implementer prompt reads impl-plan-first and `N failed`; basename exemption list). The
   path-constant census hits only `test_h_mad_install_check.py` and
   `test_h_mad_resume_decision.py`, neither this feature's. PASS.
10. **`parse_corpus.py`.** `PARSECORPUS: files=84 id_mismatch_files=0 py_symbol_label_lines=2
    parenthesised_label_lines=1` (skills `ab83ae92`, HemaSuite `f6bc694f`); residuals equal
    design D5's 2 and 1. Positive control (scratch only): a base parser mutated to drop `shape`
    gave 14 mismatching files. PASS.
11. **`judge_latency.py`.** `LATENCY: runs=3 worst_s=17.51 budget_s=40.0` (17.51, 11.07, 10.73;
    each `DENY kind=test-passing`, i.e. all four candidates ran). PASS.
12. **OQ-D1 host-deadline probe.** NOT RUN — needs a live Claude Code session write; operator
    merge condition, open.
13. **Wire-pin gate.** `WIREPIN: PASS tasks=12 wiring=4 unpinned=0 mislabeled=0`. PASS.

Twelve of thirteen items pass; item 12 is open and blocks the merge.
