# D9 isolated mutation proof

Interpreter: `/opt/anaconda3/bin/python3.11` (3.11.8).
Each node ran separately with `-m pytest <node> -q -p no:cacheprovider --tb=short`.
The isolated runs used temporary copies of the module and test file; each mutation's
anchor was asserted to occur exactly once. Bytecode was removed between runs and
the temporary tree was removed on exit. The mutants are exactly the two new rows
in `h-mad/tests/mutation-specs/doc_block_exec_task3.json`.

## A: stderr-not-closed

Node: `tests/test_h_mad_doc_block_exec.py::test_stderr_is_closed_after_drain_timeout`

```text
ORIGINAL
1 passed in 0.10s
MUTANT
    assert proc.stderr.closed, "production must close stderr after drain timeout"
E   AssertionError: production must close stderr after drain timeout
E   assert False
1 failed in 0.04s
```

The test retains the real `Popen` and its real pipes. Injected collection and drain
timeouts force the explicit pipe-close branch without creating an escaped child.
The assertion runs before the fixture closes either pipe.

## B: kill-skipped-after-collect-failure

Node: `tests/test_h_mad_doc_block_exec.py::test_collect_failure_kills_running_group`

```text
ORIGINAL
1 passed in 0.02s
MUTANT
    assert proc.poll() == -signal.SIGKILL, "production must kill the leader after collect failure"
E   AssertionError: production must kill the leader after collect failure
E   assert None == -<Signals.SIGKILL: 9>
1 failed in 5.07s
```

Only the first communicate raises the injected OSError. The subsequent drain is
real. The test checks the leader's SIGKILL return code and group absence before
teardown. `exec sleep 300` keeps the process group to one owned leader.

## C: repaired poll assertion under mutant B

Node: `tests/test_h_mad_doc_block_exec.py::test_poll_oserror_is_launch_failed_collect`

```text
ORIGINAL
1 passed in 1.02s
MUTANT
    with pytest.raises(ProcessLookupError):
E   Failed: DID NOT RAISE <class 'ProcessLookupError'>
1 failed in 6.08s
```

The poll-only assertion moved from the end of `collect_case`'s teardown into its
try body, ahead of teardown. Its original cleanup remains in `finally`; other
existing tests and assertions are unchanged. The new fixture likewise polls to
reap before signalling, signals only a running leader, waits, closes both pipes,
and removes any remaining private working directory even after assertion failure.

## Verification

```text
98 passed in 37.33s
ANCHORS: doc_block_exec_task3.json ok ok=28/28
ANCHORS: ANCHORS_OK specs=1 mutations=28 ok=28 drifted=0 unreadable=0 skipped=0 unclassifiable=0
CENSUS test_definitions=98 unique_tests=98 mutation_rows=28 unique_rows=28
MUTATION: ALL_CAUGHT mutations=28 caught=28 survived=0 refused=0 unreadable=0
```

The full harness caught both new rows by their respective named tests, and caught
`poll-oserror-unmapped` with the repaired existing test. Final
`git diff --stat -- h-mad/scripts/` is empty.
