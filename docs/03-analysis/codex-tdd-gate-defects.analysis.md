# codex-tdd-gate-defects analysis

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
