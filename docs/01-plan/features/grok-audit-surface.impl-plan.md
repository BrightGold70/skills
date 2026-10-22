# Implementation Plan: grok-audit-surface

> Source: `docs/02-design/features/grok-audit-surface.design.md` v1.11, spec v1.15 and plan v1.11
> (all three at `9628c857`), the Phase 5 carry list
> `docs/03-analysis/grok-audit-surface.phase5-carry.md` (15 items), operator decision D4
> (`docs/03-analysis/grok-audit-surface.decision-2026-10-19-d4.md`) and the incident record
> `docs/03-analysis/grok-audit-surface.incident-2026-10-20-grok-root-escape.md`. Tasks 14a–14d and
> the D21 additions to Tasks 15 and 16 (v1.8, revised in v1.9 to design v1.14 `8fd0f637` and spec
> v1.20 `d78cca8d`) are from design v1.13 (`8a27d264`) and spec v1.19
> (`d9f25dc2`), and the route (b) ruling in
> `docs/03-analysis/grok-audit-surface.incident-2026-10-22-task15-halts.md` (`242c26bd`).
> Branches: S0 (Tasks 0–14) ran on `feature/218-grok-audit-surface`, merged to `main`. **S0c (Tasks
> 18–30) runs on `feature/218b-grok-containment`**, a name this plan proposes because neither the design
> nor the plan names one; Phase 5c may rename it, and every later reference reads "the S0c branch".

Tasks 0–14 were written against the tree at `30917a1a` and are implemented on `main`; their text is
kept as built, except where an S0c Task changes a test they name (each such site says so). Tasks 15–30
were read from the tree at `9628c857`: every `path:symbol`, existing test name, marker, mutation
`find` and count in them was re-read there. `h-mad/` and the probe are unchanged from the S0 merge to
`9628c857` except by the feature's own phase documents. Tasks 14a–14d (v1.8) answer design v1.13
(`8a27d264`, D21) and spec v1.19 (`d9f25dc2`) and were read from the tree at `d9f25dc2`; Task 15's
and Task 16's D21 additions were read there too.

## Executive Summary

Thirty-five Tasks. Tasks 0–14 are the S0 instrument, implemented and merged to `main`. Tasks 18–30
are S0c (FR-11 containment, AC-3.8, the AC-6.6 scan and `out_of_root`): Tasks 18–28 are TDD Tasks on
the S0c branch, Task 29 is their Phase 5e gate, and Task 30 is the operator's non-seeded live round
trip, which must pass before the S0c branch merges. Tasks 14a–14c (v1.8) are the AC-3.9 path-scope
clause and the AC-3.6 assembler pin (design D21), and Task 14d is their Phase 5e gate; they are
numbered as sub-Tasks of 14 so that no later Task number moves. Task 15 is the operator's live
sequence (not CI), which starts only after S0c and Tasks 14a–14c are merged. Task 16 is S3 on every outcome that publishes; Task 17 is S4
and runs only on `SEEDSCORE: PASS` from a fresh S2 that was not halted.

| Task | Shape | What lands | Design |
|---|---|---|---|
| 0 | operational | the `exec agy` `workspaceDirs=` tracer into a `mktemp -d` root, recorded before S1 | D8 (agy provenance); carry 9 |
| 1 | new-behaviour | `exclusions.txt` and its doc pin | D5 |
| 2 | new-behaviour | the probe's entry point: imports, the nine D2 subparsers, the last resort, usage-error tokens, the mutation spec file | D1, D2; carry 12 |
| 3 | new-behaviour | `check-ledger` (D4) and the synthetic archive and temp-repo builder | D4 |
| 4 | new-behaviour | `build-root` without `--reset`: export, exclusion list, placements, content scan, reach check | D5, D6, D7 |
| 5 | new-behaviour | `build-root --reset`: the target precondition, the no-follow reset, re-walk, step 6 | D5; carry 1, 2, 3, 13 |
| 6 | new-behaviour | `record-cycle` and `commit-data` | D8, D9; carry 14 |
| 7 | new-behaviour | `smoke` and the `AUDITCYCLE:` and `Effort:` parsers | D10, D11; carry 4, 5, 10, 14, 15 |
| 8 | wiring | `extract`: the gate walk, the three `classify`/`_collapses` wires, `cycle_token`, the stands rule | D10, D12; carry 11 |
| 9 | new-behaviour | `score`: `key_mismatch`, `label`, D3, the verdict, the observational lines | D13 |
| 10 | new-behaviour | `main-leak`, `rescore`, the calibration-data set, the grammar sweeps over all nine modes | D3, D9, D2 |
| 11 | new-behaviour | the `HMAD_ASSEMBLE_SAME_REPORT_P<i>` stub knob and the identical-prompts test | Components, Wrapper pins |
| 12 | new-behaviour | FR-8, FR-9, FR-10 and AC-7.2-stamp pins over unchanged code, and the M1/M2 authority test | Gate pins, Wrapper pins |
| 13 | new-behaviour | SKILL.md AC-6.2a and AC-9.5 text and the S0 doc pins | D14 |
| 14 | gate | the Phase 5e verdict over the whole spec, the anchors, the fixture-name check, the two counts | Mutation spec; carry 11 |
| 14a | new-behaviour | `PATH_SCOPE_CLAUSE`, `assemble(path_scope=)` and `--path-scope` in the assembler; the path-scope test module | D21; spec AC-3.9 (1), (2), (4), (5) |
| 14b | wiring | `audit-cycle` forwards `--path-scope` when `--pass-root` is given; the armed `${stem}.here.txt` record and the pre-divergence `path_scope_missing:pN` halt; the stub's clause line and knob | D21, D17; spec AC-3.9 (3), (6) |
| 14c | new-behaviour | `assembler-read`, `assembler-check` (with `--stems`), `require --verb assembler`, in the new assembler-pin test module | D21, D20, D8; spec AC-3.6 |
| 14d | gate | the path-scope Phase 5e verdict, the cross-spec anchors, the counts, the module's time budget | D21; Mutation spec |
| 15 | operational | the live sequence after S0c and Tasks 14a–14c merge: codex tracer pair, quarantine, canary, assembler start reading, re-smoke, smoke, re-smoke commit, quarantine, fresh S2 with per-cycle scans, `require` and the halt, assembler end reading and gate, positive control, extract, labels, score sha (operator) | D8, D9, D16, D18, D19, D20, D21; carry 6, 10 |
| 16 | new-behaviour | S3: `main-leak`, `rescore`, the measurement doc, `grok-runtime.md`, AC-6.2/6.3 text and pins, K2 re-anchor | D9, D14, D15 |
| 17 | new-behaviour | S4 on PASS from an unhalted fresh S2 only: AC-7.1–7.3 and AC-8.3 text and pins | D14 |
| 18 | new-behaviour | `exec grok`: the `strict` default, `--allow-weaker-sandbox`, `-u GROK_SANDBOX`, the profile record; `exec-pane` pin | D16 |
| 19 | new-behaviour | `exec grok`'s staging directory (`.h-mad/tmp/` in a work tree with its three refusals, `<cd>/.tmp/` outside one), prompt and `TMPDIR`; codex and agy prompt and last-message beside the log | D16 |
| 20 | new-behaviour | `audit-cycle --pass-root` (one root per pass) and `--halt-file` | D17 |
| 21 | new-behaviour | `h-mad/scripts/h_mad_tool_calls.py`: parsers, path grammar, classification, `scan` CLI | D19 |
| 22 | new-behaviour | `h-mad/scripts/h_mad_grok_containment.py`: `quarantine` and `require`; the end-to-end halt test | D20, D8, D17 |
| 23 | wiring | `hmad-dispatch grok-canary` wiring `canary-plant` → `exec` → `canary-judge`; the seven forms | D18 |
| 24 | new-behaviour | the probe's `--work-dir`, `checked_parent`, the six scratch sites, the reset guards re-anchored | D5, D2 |
| 25 | new-behaviour | `record-cycle` per-pass records and profile copy; `commit-data` add-only | D3, D8, D9 |
| 26 | new-behaviour | reading namespace and `--run-id`; `parse_run_line`, `parse_profile_line`; the run record and root-record containment checks; `cycle_token` trigger (8); the list check over `resmoke/` and the per-pass `pN.root.txt` records; the smoke residuals closed | D2, D3, D8, D9, D10, D11, D12 |
| 27 | wiring | `containment_checks` and the `CONTAINMENT:` lines wired to `h_mad_tool_calls.scan_log`; `out_of_root` | D12, D13, D19 |
| 28 | new-behaviour | the FR-11 entry-contract text in `h-mad/SKILL.md` and `h-mad/references/agent-substrate.md`; K8 | D14 |
| 29 | gate | the S0c Phase 5e verdict, the cross-spec anchors, the counts, the suite floor | Mutation spec |
| 30 | operational | the non-seeded live round trip (`grok-canary`, then `exec grok` in a scratch work tree) and its evidence file, before the S0c merge | D8 "S0c" |

Shapes: `operational` 3 (Tasks 0, 15, 30); `new-behaviour` 25 (Tasks 1, 2, 3, 4, 5, 6, 7, 9, 10, 11,
12, 13, 14a, 14c, 16, 17, 18, 19, 20, 21, 22, 24, 25, 26, 28); `wiring` 4 (Tasks 8, 14b, 23, 27);
`gate` 3 (Tasks 14, 14d, 29). 3 + 25 + 4 + 3 = 35.

Mutation rows at S0 (after Task 13): 180 in `h-mad/tests/mutation-specs/grok_audit_surface.json`.
Per Task: 6 (T2) + 15 (T3) + 14 (T4) + 14 (T5) + 12 (T6) + 29 (T7) + 20 (T8) + 26 (T9) + 22 (T10) +
2 (T11) + 17 (T12) + 3 (T13) = 180. Of these, 28 are the design's named rows (W1–W10, G1–G5, C1–C4,
K1–K3, X1–X6) and 152 are P-rows (one per refusal or non-default-verdict fixture, design §"Mutation
spec", "P-rows"). The 180 was read at `9628c857` with Task 14's row-count command (rows).

Mutation rows added by S0c (Tasks 18–28): 13 (T18) + 16 (T19) + 13 (T20) + 24 (T21) + 26 (T22) +
33 (T23) + 22 (T24) + 11 (T25) + 28 (T26) + 9 (T27) + 1 (T28) = 196, so the spec holds 376 rows after
Task 28. Task 24 also rewrites one S0 row in place (`p-reset-tmpdir`), which moves no count. Two
operator-approved fixes after the S0c merge each added one row (`f3714912`
`canary-token-window-reverted-to-hex-run`; `2925febd` `canary-denial-case-sensitive`), so the spec holds 378 rows at `d9f25dc2` (rows, read with Task 14's
row-count command; 376 at `bfd76555`, Task 28; still 378 at `8fd0f637`, where `h-mad/` is unchanged).
Tasks 14a–14c add 6 (T14a) + 9 (T14b) + 27 (T14c) = 42: the 15 design rows PS1–PS15 and 27
assembler-pin rows, 420 after Task 14c. Task 16 adds the named rows K6 and K7 on every outcome, and
K4 and K5 only on MISS or INCONCLUSIVE: 422 on PASS or a smoke failure, 424 on MISS or INCONCLUSIVE.

Marker sites (matching lines, `grep -c` per file):
- the probe, `M:GAS-`: 125 at S0 (per Task: 6 + 14 + 11 + 13 + 11 + 19 + 12 + 21 + 18; Task 5's
  `p-traceback-scope-reset` reuses Task 2's `GAS-TRACEBACK-SCOPE` and adds no site), read 125 at
  `9628c857`; S0c adds 15 (T24) + 9 (T25) + 19 (T26) + 7 (T27) = 50, so 175;
- `h-mad/scripts/hmad-dispatch.sh`, `# M:`: 8 at `9628c857` (`PROBE-*`, `STEM-*`); S0c adds 8 (T18)
  + 13 (T19) + 11 (T20) + 8 (T23) = 40, so 48;
- `h-mad/scripts/h_mad_tool_calls.py`, `# M:TOOLSCAN-`: 21 (T21);
- `h-mad/scripts/h_mad_grok_containment.py`, `# M:`: 16 (T22) + 18 (T23) = 34;
- the additions of Tasks 14a–14c, each counted by its own prefix (matching lines): `M:PATH-SCOPE-` 2 in
  `h-mad/scripts/h_mad_assemble_audit.py` (T14a) and 5 in `h-mad/scripts/hmad-dispatch.sh` (T14b);
  `# M:ASSEMBLER-` 19 and `# M:REQUIRE-OK-ASSEMBLER` 1 in `h-mad/scripts/h_mad_grok_containment.py`
  (T14c). All of these read 0 at `8fd0f637`:
  `grep -rnE 'M:ASSEMBLER-|REQUIRE-OK-ASSEMBLER|M:PATH-SCOPE|path_scope|PATH_SCOPE|path-scope' h-mad/ | wc -l`
  printed 0 (matching lines).

The design carries none of these totals ("Two units, two derivations, neither carried"); Tasks 14
and 29 re-derive them with the design's two commands, and Task 29 also over the three new or changed
files.

## Rules every Task follows

- **Interpreter.** Every pytest run and every mutation spec uses `/opt/anaconda3/bin/python3.11`.
  `python3` (3.15 here) has no pytest, and the RTK hook rewrites `python3 -m pytest`, so a
  precondition is probed as `rtk proxy /opt/anaconda3/bin/python3.11 -m pytest --version`.
- **Full suite per Task**, never a scoped selection as the gate:
  `rtk proxy /opt/anaconda3/bin/python3.11 -m pytest h-mad/tests -q -p no:cacheprovider`, from the
  repository root, in the foreground, gated on the summary line and never on `$?`. The scoped
  `--test-path` given to the 5d/5e assembler is the Task's own test file, repo-root-relative
  (`h-mad/tests/<file>.py`).
- **RED counts are pytest node IDs.** A parametrised test counts once per id. `F` fails at RED, `P`
  passes at RED. A `P` is a regression guard and is labelled as one.
- **Node-id spelling.** In WIRE-PIN lines and assembler arguments a test is written repo-root-relative
  (`h-mad/tests/test_x.py::test_y`). In mutation rows the `test` key is relative to the spec's root
  `../..`, which resolves to `h-mad/` (`tests/test_x.py::test_y`). The function name is identical
  in both.
- **Driving the probe.** Each probe test module defines
  `PROBE = REPO / "docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py"` as one literal
  (what `h_mad_archive_feature.probe_readers` matches) and runs it as
  `subprocess.run([sys.executable, str(PROBE), ...])`, asserting the exit code and the **exact**
  last stdout line together. A test that replaces a function calls `main(argv)` in process with
  `monkeypatch` and `capsys`, and reads `capsys.readouterr()` before asserting.
- **Tracebacks are surfaced, so a mutant's crash is visible (axis: a traceback a mutant causes in
  the probe).** The mutation harness counts a crash kill only from tracebacks visible in the scoring
  run's output (`crash_kill` returns `None` when the traceback is not printed). So: (1) the probe
  prints a traceback on stderr only for an exception outside its declared refusal classes (one base,
  `ProbeRefusal`, which `Refusal`, `UsageError`, `ResetArgsConflict`, `ResetPurposeNotS1`, the four
  `ResetTarget…` classes and `RootResetMismatch` subclass). A declared refusal prints its token and
  no traceback (`# M:GAS-TRACEBACK-SCOPE`). (2) Every assertion on a probe run passes that run's
  stderr as its message: a subprocess assertion passes the child's (`assert lines[-1] == expected, r.stderr`),
  and an in-process `main(argv)` assertion passes the captured one
  (`out, err = capsys.readouterr()`, then `assert out.splitlines()[-1] == expected, err`). So a
  mutant-caused `KeyError`, `TypeError` or `NameError` reaches the harness and is counted, whichever
  way the test drives the probe. (3) The only exceptions are the
  tests that inject an exception on purpose or assert on stderr's content
  (`test_internal_failure_prints_the_mode_token`, `test_smoke_last_resort_names_the_open_input`, and
  the traceback-absence assertions of `test_usage_error_prints_the_mode_token` and of the Task 5
  refusal tests AC-T5.1 lists): these compute their figures into locals first
  (`n = r.stderr.count("Traceback")` for a subprocess, `n = err.count("Traceback")` after
  `out, err = capsys.readouterr()` in process) and assert on the locals with a fixed message, never
  echoing stderr. **Order (axis: an assertion whose message withholds stderr).** In every test that
  has both a token assertion and a traceback-count assertion, the token assertion, with stderr as
  its message, comes first, and the traceback count second. So a mutant that crashes changes the
  token, fails the first assertion with its traceback visible, and is counted as a crash kill. The
  fixed-message count assertion is reached only when the token was right. Residual: a mutant whose only effect is that one declared refusal class falls through to
  another declared class prints no traceback by design. That kill is an assertion kill, which is
  the correct reading. The design's D1 sentence ("prints the traceback on stderr") is read as
  covering only exceptions that escape the declared checks; that reading is owed to the design.
- **In-process loads never use bytecode (axis: a mutation that lands but does not execute).** The
  harness purges `__pycache__` only under its root (`h-mad/`), and the probe lives under `docs/`.
  A same-size mutation written within one mtime second is then read from a stale `.pyc`. Every
  in-process test therefore loads the probe with `grokauditfixtures.load_probe(PROBE)`, which
  compiles the source text (`compile(path.read_bytes(), str(path), "exec")`) into a fresh
  `types.ModuleType`, so no `.pyc` is read or written. A subprocess run is unaffected, because
  `subprocess.run([sys.executable, str(PROBE), ...])` runs the probe as `__main__`, which Python
  never caches. The probe's own imports are `h-mad/scripts` modules,
  which sit under the purged root. This also keeps the probe directory free of `__pycache__`,
  which matters because the plan restricts that directory to the probe and the exclusion list.
- **Synthetic only.** Every fixture is invented text built under `tmp_path` (at S0 the reset
  fixtures used `tempfile.gettempdir()`, removed by the fixture's finalizer; from Task 24 every root
  and scratch directory lies under `tmp_path`, with the probe run under the stand-in system temp
  `TMPDIR=<tmp_path>/systemp`, D5's test seam). No test reads the
  real calibration ref, dispatches an agent, or touches the network. A test whose clean case needs
  its root outside a work tree first asserts `git -C <that parent> rev-parse --git-dir` fails; it
  never skips. No `skip`, `xfail` or `.only` anywhere.
- **Mutation spec.** One file, `h-mad/tests/mutation-specs/grok_audit_surface.json`, created by
  Task 2 with `"root": "../.."`, `"target_command": ["/opt/anaconda3/bin/python3.11", "-m", "pytest", "-q"]`
  and a `command` that names the feature's test files that exist at that Task. Each later Task that
  creates a test file inserts it into `command` at its design position, so after Task 13 `command`
  equals the design's seven-file list at S0 (read at `9628c857`), and after Task 21 it equals design
  v1.11's eight-file list, with `tests/test_grok_audit_surface_containment.py` after
  `tests/test_grok_audit_surface_docs.py`; after Task 14c it equals design v1.14's ten-file list,
with `tests/test_grok_audit_surface_path_scope.py` (Task 14a) and then
`tests/test_grok_audit_surface_assembler_pin.py` (Task 14c) after the containment module. S0c rows in `h-mad/scripts/` name `file` relative to
  `h-mad/` (`scripts/hmad-dispatch.sh`, `scripts/h_mad_tool_calls.py`,
  `scripts/h_mad_grok_containment.py`). Rows carry `name`, `file`, `find`, `replace`, `test` and
  `symbol` (the enclosing function or class). Probe rows name `file`
  `../docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py` (one committed precedent names a
  file outside `h-mad/`: `host_runtime_docs.json`, `../handoff/SKILL.md`). Each Task's rows are
  added at its GREEN, against the committed bytes; their intent and `test` are fixed here.
- **P-rows.** Each probe guard line carries a marker comment `# M:GAS-<NAME>`, and nothing else in
  the probe contains the text `M:GAS-`. A P-row's `find` is that marker's line. Its `replace` keeps
  the code running (never introduces an exception, an undefined name or a type change), because
  Phase 5e accepts only `crash_kills=0`; so a row changes a condition, a constant or a printed
  reason, never deletes a statement that later code needs. Where two guards print the same token, a
  `replace` that only disables one of them falls through to the other and survives as an
  equivalent mutant; those rows (named in Task 7) turn the refusal into acceptance instead.
- **Verdicts.** Each Task that adds rows runs, from the repository root,
  `python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/grok_audit_surface.json`
  and requires `MUTATION: ALL_CAUGHT` with `untargeted=0/` followed by the row count so far and
  `crash_kills=0`, then the same with `--check-anchors` and `ANCHORS: ANCHORS_OK`, read from the
  token lines.
- **Markers.** Every probe run writes `[H-MAD] grok-audit-surface` followed by the mode and the
  token's verdict word to stderr, after the token line is printed (base §"Marker discipline").
- **S0c scripts and the wrapper (Tasks 18–28).** The two new scripts follow the probe's traceback
  rule: a usage error prints its token with no traceback, and any other escaping exception prints
  its `internal:<ExceptionName>` token (or, for the canary, no line) and its traceback on stderr. Every
  assertion on a run passes that run's stderr as its message, token assertion first. The test
  modules load a new script with `importlib.util.spec_from_file_location` inside a fixture, never at
  import time, so at RED each node fails on its own and collection never errors. Wrapper tests drive
  `h-mad/bin/hmad-dispatch` as a subprocess with stub agents on `PATH` (`STUBS` from
  `test_hmad_dispatch`), assert the exit code beside the stdout token or stderr message, and, for
  every refusal, that the stub never ran (its record file is absent). A P-row whose disarm would make
  later code read a value the guard rejected changes the printed reason instead (the
  `# M:GAS-RECORD-ROOT-MALFORMED` precedent), so every row stays a test kill (`crash_kills=0`).
  In a file name, `pN` is pass N's file (`p1`, `p2`, `p3`), the design D3 per-pass naming.
- **Lines other specs anchor on stay byte-identical (Tasks 19, 20).** At `9628c857`, three rows in
  two other committed specs find the `audit-cycle` launch line
  `      _cmd_exec "${agent[$i]}" "${prompt[$i]}" --cd "$root" \` (`verb_no_self_invocation.json`: 2
  rows; `grok_exec.json`: 1 row, by its prefix), and one row (`grok_wire_reverts.json`
  `wr9-2-child-env-scrub-dropped`) finds the grok launch line's
  `"$wait_secs" env "${child_env[@]}" grok "${gargs[@]}"`. S0c changes neither line: the per-pass
  `--cd` is a new line before the launch inside the pass's subshell, and the grok environment changes
  are edits of `child_env`. Task 29 runs `--check-anchors` over every spec that names
  `scripts/hmad-dispatch.sh` (28 specs at `9628c857`). Task 14b is the one Task that must move such a
  line: the assembler call's third line, which `verb-assemble-drop` in
  `h-mad/tests/specs/audit_cycle_connections.mutation.json` finds, gains the `--path-scope` expansion,
  and that row is re-anchored with an unchanged `replace` (Task 14b). That spec lives in
  `h-mad/tests/specs/`, which Task 29's loop does not search; Task 14d's loop searches both directories.

## Task 0: agy workspace tracer

**Production files**: none
**Test files**: none
**Task shape**: `operational` — runs an existing wrapper verb once and records what it wrote; it
builds and mutates nothing in the repository.

**Description**: Before S1, one `exec agy` dispatch into a fresh `mktemp -d` directory records which
spelling agy's own cli log gives that directory on its `workspaceDirs=` line: the `mktemp` spelling
(`/var/folders/…`) or its physical one (`/private/var/folders/…`). D8's agy-provenance selection
matches either spelling; until this reading exists, whether the `exec agy` leg logs the root at
all is unmeasured (D8 residual). The tracer runs first because nothing in Tasks 1–14 depends on it
and Task 15 cannot start S1 without it. The tracer's prompt and reading live under the kept
directory, never in the repository; Task 16 copies the reading into the measurement doc's Readings.

```bash
KEEP="$HOME/.local/state/h-mad/grok-audit-surface"; TR="$KEEP/agy-tracer"; mkdir -p "$TR"
AGYLOG="$HOME/.gemini/antigravity-cli/log"; /bin/ls "$AGYLOG" > "$TR/before.txt"
printf 'Reply with the single word OK.\n' > "$TR/prompt.txt"
T=$(mktemp -d)
h-mad/bin/hmad-dispatch exec agy "$TR/prompt.txt" --cd "$T" --timeout 300 --out "$TR/out.txt"
{ echo "T=$T"; echo "TP=$(cd "$T" && pwd -P)"
  for f in "$AGYLOG"/cli-*.log; do
    grep -qxF -- "${f##*/}" "$TR/before.txt" && continue
    echo "new=${f##*/} $(grep -o -m1 'workspaceDirs=\[[^]]*\]' "$f")"
  done; } > "$TR/reading.txt"
rm -rf "$T"
```

**Acceptance Criteria**:
- [ ] AC-T0.1: `$TR/reading.txt` exists and holds its `T=` and `TP=` lines and every `new=` line
  the loop printed.
- [ ] AC-T0.2: The result is classified from the file, as exactly one of: one `new=` line whose
  `workspaceDirs=[…]` value equals the `T=` value (`mktemp` spelling), or equals the `TP=` value
  (physical spelling); or anything else (zero `new=` lines, several, or neither spelling). The
  classification is written as the file's last line, `CLASS=mktemp`, `CLASS=physical` or
  `CLASS=unmatched`.
- [ ] AC-T0.3: On `CLASS=unmatched`, Task 15 re-derives D8's selection from this reading before
  any S1 dispatch (D8: "If it names neither spelling, the selection above is re-derived from that
  reading before S1 dispatches"); the re-derived selection is recorded in the runbook Task 16
  publishes.
- [ ] AC-T0.4: The `mktemp -d` directory is gone after the run (`test -e "$T"` fails).

**Dependencies on other tasks**: None. Must complete before Task 15's S1 step.

---

## Task 1: the declared exclusion list

**Production file**: `docs/03-analysis/probes/grok-audit-surface/exclusions.txt`
**Test file**: `h-mad/tests/test_grok_audit_surface_docs.py`
**Task shape**: `new-behaviour`

**Description**: The exclusion list D5 specifies, committed on `main`, and the doc pin that it holds
the required entries. Its grammar is two line kinds (`dir`, `name-contains`) plus `#` comments; it
holds exactly D5's six entries.

```
dir docs/archive/2026-09/audit-report-docs-copy
dir docs/archive/2026-09/tdd-gate-fail-opens
dir docs/archive/2026-10/agy-coder-fallback
dir docs/03-analysis/probes/grok-audit-surface
dir docs/03-analysis/agy-coder-fallback.authoring
name-contains grok-audit-surface
```

**Code structure**:
```python
# h-mad/tests/test_grok_audit_surface_docs.py
REPO = Path(__file__).resolve().parents[2]
EXCLUSIONS = REPO / "docs/03-analysis/probes/grok-audit-surface/exclusions.txt"
def test_exclusion_list_holds_the_required_entries() -> None: ...
```

**Acceptance Criteria**:
- [ ] AC-T1.1: `test_exclusion_list_holds_the_required_entries` asserts the non-comment,
  non-blank lines of the file are exactly the six above, in that order.

**RED split**: 1 node; 1 F (the file is absent), 0 P.

**Mutation rows**: none (the doc pin's discrimination is its RED; the list is data).

**Dependencies on other tasks**: None.

---

## Task 2: the probe's entry point

**Production files**: `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py` (create),
`h-mad/tests/mutation-specs/grok_audit_surface.json` (create)
**Test files**: `h-mad/tests/test_grok_audit_surface_probe.py` (create),
`h-mad/tests/grokauditfixtures.py` (create, holding `load_probe` only; Task 3 extends it)
**Task shape**: `new-behaviour`

**Description**: The probe file with D1's imports and D2's nine subparsers, every command line exactly
as the D2 table writes it, and D1's token discipline: one `try` around the mode, and an escaping
exception printed as the traceback on stderr followed by the mode's refusal token with
`reason=internal:` and the class name, exit 2 (`smoke`: `input_unparseable:` and the path D1 names).
`MODES` maps a mode name to its handler; each later Task adds its own handler, so at this Task a
mode whose handler has not landed reaches the last resort as `internal:KeyError`. That is the
transitional state of a feature branch, not a shipped one: Task 10's `test_success_token_shape_per_mode`
fails until all nine handlers exist.

**Every argparse exit path ends on the mode's token (carry 12; axis: argparse's exits).** Measured on
`/opt/anaconda3/bin/python3.11` (3.11.8) and `/opt/homebrew/opt/python@3.15/bin/python3.15` (3.15.0): argparse's only `sys.exit` is in
`ArgumentParser.exit`, which has three callers: `error()`, the help action and the version action
(4 `.exit(` sites in the module source on each interpreter: 2 `parser.exit()` in the help and
version actions, 1 `_sys.exit(status)` in `exit`, 1 `self.exit(2, …)` in `error`). `python3` here
is pinned by its absolute path, `/opt/homebrew/opt/python@3.15/bin/python3.15`, so the reading does
not depend on `PATH`. Reproduce:

```bash
P315=/opt/homebrew/opt/python@3.15/bin/python3.15
for py in /opt/anaconda3/bin/python3.11 $P315; do $py -c 'import argparse,inspect,sys;v=sys.version.split()[0];[print(v, l.strip()) for l in inspect.getsource(argparse).splitlines() if ".exit(" in l]'; done
# 3.11.8 parser.exit()
# 3.11.8 parser.exit()
# 3.11.8 _sys.exit(status)
# 3.11.8 self.exit(2, _('%(prog)s: error: %(message)s\n') % args)
# 3.15.0 parser.exit()
# 3.15.0 parser.exit()
# 3.15.0 _sys.exit(status)
# 3.15.0 self.exit(2, fmt % args)
for py in /opt/anaconda3/bin/python3.11 $P315; do $py -c '
import argparse,sys,io,contextlib
p=argparse.ArgumentParser(prog="p"); s=p.add_subparsers(dest="m"); s.add_parser("smoke").add_argument("--data")
o=io.StringIO()
try:
    with contextlib.redirect_stdout(o): p.parse_args(["smoke","--help"])
except SystemExit as e: print(sys.version.split()[0], "SystemExit", e.code, "stdout_bytes", len(o.getvalue()))'; done
# 3.11.8 SystemExit 0 stdout_bytes 105
# 3.15.0 SystemExit 0 stdout_bytes 105
# a plain top-level parser over a token-raising subparser class: the top level reports the extra flag
for py in /opt/anaconda3/bin/python3.11 $P315; do $py -c '
import argparse,sys
class UE(Exception): pass
class TP(argparse.ArgumentParser):
    def error(self, m): raise UE(m)
p=argparse.ArgumentParser(prog="top"); s=p.add_subparsers(dest="m", parser_class=TP); s.add_parser("smoke").add_argument("--data")
try: p.parse_args(["smoke","--data","x","--no-such-flag"]); print("parsed")
except UE: print(sys.version.split()[0], "UsageError")
except SystemExit as e: print(sys.version.split()[0], "SystemExit", e.code)' 2>&1; done
# usage: top [-h] {smoke} ...
# top: error: unrecognized arguments: --no-such-flag
# 3.11.8 SystemExit 2
# usage: top [-h] {smoke} ...
# top: error: unrecognized arguments: --no-such-flag
# 3.15.0 SystemExit 2
# allow_abbrev: --tre is read as --tree when on, refused when off
for py in /opt/anaconda3/bin/python3.11 $P315; do $py -c '
import argparse,sys
for ab in (True, False):
    p=argparse.ArgumentParser(prog="p", allow_abbrev=ab); p.add_argument("--tree")
    try: print(sys.version.split()[0], "allow_abbrev", ab, vars(p.parse_args(["--tre","t"])))
    except SystemExit as e: print(sys.version.split()[0], "allow_abbrev", ab, "SystemExit", e.code)' 2>/dev/null; done
# 3.11.8 allow_abbrev True {'tree': 't'}
# 3.11.8 allow_abbrev False SystemExit 2
# 3.15.0 allow_abbrev True {'tree': 't'}
# 3.15.0 allow_abbrev False SystemExit 2
```

The rule:
- Every parser, the top-level one included, is a `_TokenArgumentParser`
  (`build_parser()` returns one, and `add_subparsers(parser_class=_TokenArgumentParser)`). This
  matters because an unrecognised flag after a subcommand is reported by the **top-level**
  parser's `error()`: with a plain top-level parser, `smoke --data x --no-such-flag` exits 2 with
  no token.
- `_TokenArgumentParser.error()` prints the message on stderr and raises `UsageError`
  (`# M:GAS-USAGE`).
- Every parser is built with `add_help=False` (`# M:GAS-NO-HELP`) and `allow_abbrev=False`
  (`# M:GAS-NO-ABBREV`), and no parser defines a `version` action. With `add_help` left at its
  default, `<mode> --help` prints help on stdout and exits through `SystemExit(0)` with no token.
  With `allow_abbrev` left on, `check-ledger --tre t` is silently read as `--tree t` rather than
  refused.

So `ArgumentParser.exit` is unreachable. `--help`, `-h`, an abbreviation, an unknown flag, a
missing value and a bad `type=` conversion all reach `error()`, and the last resort prints that
mode's refusal token with `reason=internal:UsageError`. The `smoke` refusal reads its path from the
**raw argv**, never from a `Namespace`: a `UsageError` raised inside `parse_args` returns no
`Namespace`, and a subparser's error fires before its values are copied up. So
`refusal_token(mode, exc, argv)` gives `SMOKE: UNREADABLE reason=input_unparseable:` followed by
the first of: the module-level `_OPEN_INPUT` (a `str` or `None`, set to `None` at the start of
every `main` call and assigned by Task 7's `smoke` to each input's path immediately before it
opens that input), when it is not `None`; else the word after the first exact `--data` in argv (or
the `--data=` value); else the empty string. That is D1's order: the input the derivation had
open, then the `--data` directory. `refusal_token` reads `_OPEN_INPUT` directly; no other channel
carries it (`# M:GAS-OPEN-INPUT` marks that arm; its fixture and row are Task 7's, because only
`smoke` assigns it). `_OPEN_INPUT` is not cleared when an input closes. An exception raised after
the last input is read therefore names that last input. That is the plan's reading of D1's "the
input the derivation had open when the exception escaped, or the `--data` directory when none was
open yet": once any input has been opened, the last one opened is reported. **A `Refusal` reaches
its token through `refusal_token` (axis: where a declared refusal becomes its token).** Mode
handlers do not catch `Refusal`; it propagates to `main`'s last resort. `refusal_token` prints
`reason=` followed by `exc.reason` for a `Refusal` (`# M:GAS-REFUSAL-REASON`; its first fixtures
and its row are Task 3's), `internal:` and the class name for every other exception except in
`smoke`, where a non-`Refusal` exception prints `input_unparseable:` and the D1 path above. Residual, stated exactly: a future Python whose argparse
gains another `exit` caller is not covered. Task 2's tests run under the interpreter the suite
uses, and the measured site count above is what would change.

**An argv with no mode prints a cannot-judge token first (operator ruling, 2026-10-19).** When the
first argv word is not one of the nine `GRAMMAR` keys, or argv is empty, `main` checks this before
any parsing: it prints exactly one stdout line, `PROBE: UNREADABLE reason=unknown_mode`, carrying no
counts (`# M:GAS-UNKNOWN-MODE`), then the top-level usage on stderr and the `[H-MAD]` marker, and
returns 2. So AC-5.1 holds as written: there is no exit without a token. `PROBE:` is a tenth token
prefix that belongs to no mode, and no mode's published line or token starts with it. It is an
addition to D2's grammar, owed to the design and the spec.

**Code structure**:
```python
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "h-mad" / "scripts"))
import h_mad_audit_gate as _gate
import h_mad_audit_cycle as _cycle
from h_mad_audit_origins import ORIGINS
from h_mad_review_evidence import _GROK_TYPES

SOURCES: dict[str, str] = {
    "audit-report-docs-copy": "docs/archive/2026-09",
    "tdd-gate-fail-opens": "docs/archive/2026-09",
    "agy-coder-fallback": "docs/archive/2026-10",
}
GRAMMAR: dict[str, tuple[str, str]] = {  # mode -> (token prefix, refusal word), D2
    "check-ledger": ("LEDGER:", "UNREADABLE"), "build-root": ("ROOT:", "UNREADABLE"),
    "record-cycle": ("RECORD:", "REFUSED"), "commit-data": ("COMMIT:", "REFUSED"),
    "smoke": ("SMOKE:", "UNREADABLE"), "extract": ("FINDINGS:", "UNREADABLE"),
    "score": ("SEEDSCORE:", "UNREADABLE"), "rescore": ("SEEDSCORE:", "UNREADABLE"),
    "main-leak": ("MAINLEAK:", "UNREADABLE"),
}
MODES: dict[str, Callable[[argparse.Namespace], int]] = {}
_OPEN_INPUT: str | None = None  # the input smoke has open; reset by main, read by refusal_token

class ProbeRefusal(Exception): ...          # base of every declared refusal; no traceback
class UsageError(ProbeRefusal): ...
class _TokenArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs) -> None: ...  # forces add_help=False, allow_abbrev=False
    def error(self, message: str) -> NoReturn: ...
def parse_sources(value: str) -> dict[str, str]: ...
def build_parser() -> _TokenArgumentParser: ...
def refusal_token(mode: str, exc: BaseException, argv: list[str]) -> str: ...
def main(argv: list[str] | None = None) -> int: ...
# h-mad/tests/grokauditfixtures.py
def load_probe(path: Path) -> types.ModuleType: ...  # compile from source; no .pyc read or written
```

**Tests** (in `h-mad/tests/test_grok_audit_surface_probe.py`):
1. `test_internal_failure_prints_the_mode_token`, parametrised over the nine D2 modes (9 ids). In
   process: `monkeypatch.setitem(probe.MODES, mode, raiser)` with a handler raising `RuntimeError`;
   the argv is the mode plus the minimal D2 arguments with `tmp_path` values. The last stdout line is
   that mode's refusal token with `reason=internal:RuntimeError` (`smoke`:
   `SMOKE: UNREADABLE reason=input_unparseable:` plus the `--data` value), `main` returns 2, and
   stderr carries `Traceback`.
2. `test_usage_error_prints_the_mode_token` (plan-added, carry 12), parametrised over the nine modes
   (9 ids), as a subprocess: argv `[mode, "--no-such-flag"]` for the eight non-smoke modes and
   `["smoke", "--data", str(tmp_path / "s1"), "--no-such-flag"]` for `smoke`. Exit 2 and the last
   stdout line is the mode's refusal token with `reason=internal:UsageError` (`smoke`: with
   `input_unparseable:` and the `--data` value), and `n = r.stderr.count("Traceback")` is 0 (a
   declared refusal prints no traceback).
3. `test_unknown_mode_prints_the_probe_token` (operator ruling), parametrised over two argvs (2 ids):
   `[]` and `["no-such-mode"]`, as a subprocess. Exit 2; stdout is exactly the one line
   `PROBE: UNREADABLE reason=unknown_mode`; stderr contains `usage:`.
4. `test_help_flag_prints_the_mode_token` (plan-added, audit cycle 1), parametrised over the nine
   modes (9 ids), as a subprocess: argv `[mode, "--help"]` (`smoke`: with `--data` before it).
   Exit 2, stdout has no line other than the token, and the token is the mode's refusal token with
   `reason=internal:UsageError` (`smoke`: `SMOKE: UNREADABLE reason=input_unparseable:` followed by
   the `--data` value, as in Tests 1 and 2).
5. `test_abbreviated_flag_is_a_usage_error` (plan-added, audit cycle 1), 1 id, as a subprocess:
   argv `["check-ledger", "--tre", str(tmp_path)]`. Exit 2 and
   `LEDGER: UNREADABLE reason=internal:UsageError`. With abbreviations allowed, the same argv runs
   the ledger check on `tmp_path` and prints a different reason.

**Acceptance Criteria**:
- [ ] AC-T2.1: The five tests pass for all 30 ids (9 + 9 + 2 + 9 + 1).
- [ ] AC-T2.2: The probe imports only the stdlib and the four D1 modules; `grep -nE '^(import|from) ' docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py`
  shows nothing else.
- [ ] AC-T2.3: `MODES` is the only dispatch table; `main` never calls a handler by name.
- [ ] AC-T2.4: The spec file exists with the header above and `command`
  `["/opt/anaconda3/bin/python3.11", "-m", "pytest", "tests/test_grok_audit_surface_probe.py", "tests/test_grok_audit_surface_docs.py", "-q"]`.

**RED split**: 30 nodes; 30 F (the probe is absent), 0 P.

**Mutation rows** (6):

| name | find (marker line) | intent of `replace` | test |
|---|---|---|---|
| `p-last-resort-reason` | `# M:GAS-LAST-RESORT` | print `internal:Exception` in place of the class name | `tests/test_grok_audit_surface_probe.py::test_internal_failure_prints_the_mode_token` |
| `p-usage-token` | `# M:GAS-USAGE` | `error()` calls `argparse.ArgumentParser.error` (no token) | `tests/test_grok_audit_surface_probe.py::test_usage_error_prints_the_mode_token` |
| `p-unknown-mode-token` | `# M:GAS-UNKNOWN-MODE` | the token line removed (its `print` call replaced by `pass`); usage and exit 2 unchanged | `tests/test_grok_audit_surface_probe.py::test_unknown_mode_prints_the_probe_token` |
| `p-no-help` | `# M:GAS-NO-HELP` | `add_help=True` | `tests/test_grok_audit_surface_probe.py::test_help_flag_prints_the_mode_token` |
| `p-no-abbrev` | `# M:GAS-NO-ABBREV` | `allow_abbrev=True` | `tests/test_grok_audit_surface_probe.py::test_abbreviated_flag_is_a_usage_error` |
| `p-traceback-scope` | `# M:GAS-TRACEBACK-SCOPE` | print the traceback for every exception, declared refusals included | `tests/test_grok_audit_surface_probe.py::test_usage_error_prints_the_mode_token` |

**Dependencies on other tasks**: Task 1 (the docs test module exists for `command`).

---

## Task 3: ledger checks

**Production file**: `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py` (extend)
**Test files**: `h-mad/tests/test_grok_audit_surface_probe.py` (extend),
`h-mad/tests/grokauditfixtures.py` (extend; Task 2 created it with `load_probe`)
**Task shape**: `new-behaviour`

**Description**: `check-ledger` per D4, in both front doors (`--tree` and
`--repo . --calibration-sha`), and the fixture builder every later Task uses.
`grokauditfixtures.py` builds (a) a synthetic archive of three invented features, each with spec,
plan, design and impl-plan, giving nine seeded documents `d1`…`d9` in feature order and then plan,
design, impl-plan; (b) a 27-record ledger obeying the AC-2.2 class rule, with seeded copies made by
replacing each `original` once; (c) a temporary repository at `tmp_path/work` whose `origin` is a
bare `tmp_path/origin.git`, with a `main` commit and the calibration branch created by plumbing.
Every probe call in a fixture passes `--sources` with the synthetic archive's mapping. Each check is
one guard with its own marker; the per-document class rule refuses before the totals comparison, so
the totals comparison has no fixture that reaches it and carries no marker.

**Code structure**:
```python
def read_ledger(tree: Path) -> list[dict]: ...
def check_ledger(tree: Path, sources: dict[str, str]) -> dict[str, int]: ...  # raises Refusal("ledger_counts" | "ledger_origin" | "seed_rebuild")
class Refusal(ProbeRefusal):
    def __init__(self, reason: str) -> None: ...
def _mode_check_ledger(args: argparse.Namespace) -> int: ...
# grokauditfixtures.py
def build_archive(root: Path) -> dict[str, str]: ...        # returns the --sources mapping
def build_ledger(tree: Path, sources: dict[str, str]) -> list[dict]: ...
def build_repo(tmp_path: Path) -> tuple[Path, Path]: ...   # (work, origin.git)
```

**Tests** (16, in the probe test module, each with its one trigger alone):
`test_ledger_counts_refuses_a_repeated_class_with_totals_kept` (d1 C2, C2, C4 and d4 C1, C3, C3),
`test_ledger_counts_refuses_a_moved_class`, `test_ledger_counts_refuses_an_unparseable_line`,
`test_ledger_counts_refuses_a_missing_field`, `test_ledger_counts_refuses_a_source_outside_the_nine`,
`test_ledger_counts_refuses_an_empty_original`, `test_ledger_counts_refuses_an_empty_expected`,
`test_ledger_origin_refuses_an_unknown_origin`, `test_seed_rebuild_refuses_one_byte`,
`test_seed_rebuild_refuses_a_twice_occurring_original`,
`test_seed_rebuild_refuses_two_seeds_in_one_section`,
`test_seed_rebuild_refuses_a_seed_under_version_history`,
`test_seed_rebuild_refuses_a_wrong_section_name`, `test_seed_rebuild_refuses_a_seeded_span_not_once`,
`test_ledger_ok_reports_derived_counts`, `test_check_ledger_tree_and_repo_forms_agree`.

**Acceptance Criteria**:
- [ ] AC-T3.1: Each refusal test's last stdout line is exactly `LEDGER: UNREADABLE reason=ledger_counts`,
  `reason=ledger_origin` or `reason=seed_rebuild` as its name says, with exit 2.
- [ ] AC-T3.2: `test_ledger_ok_reports_derived_counts` reads exactly
  `LEDGER: OK seeds=27 docs=9 C1=6 C2=7 C3=7 C4=7` on the clean fixture, exit 0, and the probe source
  holds none of `6`, `7` or `27` as a count literal in `check_ledger` (the totals are derived from the
  rule).
- [ ] AC-T3.3: The two front doors give the same last line on the same content.

**RED split**: 16 nodes; 16 F (no `check-ledger` handler: `internal:KeyError`), 0 P.

**Mutation rows** (15; markers 14):

| name | marker | test |
|---|---|---|
| `p-ledger-class-repeated` | `# M:GAS-LEDGER-CLASS` | `tests/test_grok_audit_surface_probe.py::test_ledger_counts_refuses_a_repeated_class_with_totals_kept` |
| `p-ledger-class-moved` | `# M:GAS-LEDGER-CLASS` | `tests/test_grok_audit_surface_probe.py::test_ledger_counts_refuses_a_moved_class` |
| `p-ledger-json` | `# M:GAS-LEDGER-JSON` | `tests/test_grok_audit_surface_probe.py::test_ledger_counts_refuses_an_unparseable_line` |
| `p-ledger-field` | `# M:GAS-LEDGER-FIELD` | `tests/test_grok_audit_surface_probe.py::test_ledger_counts_refuses_a_missing_field` |
| `p-ledger-source` | `# M:GAS-LEDGER-SOURCE` | `tests/test_grok_audit_surface_probe.py::test_ledger_counts_refuses_a_source_outside_the_nine` |
| `p-ledger-empty-original` | `# M:GAS-LEDGER-EMPTY-ORIGINAL` | `tests/test_grok_audit_surface_probe.py::test_ledger_counts_refuses_an_empty_original` |
| `p-ledger-empty-expected` | `# M:GAS-LEDGER-EMPTY-EXPECTED` | `tests/test_grok_audit_surface_probe.py::test_ledger_counts_refuses_an_empty_expected` |
| `p-origin` | `# M:GAS-ORIGIN` | `tests/test_grok_audit_surface_probe.py::test_ledger_origin_refuses_an_unknown_origin` |
| `p-rebuild-bytes` | `# M:GAS-REBUILD-BYTES` | `tests/test_grok_audit_surface_probe.py::test_seed_rebuild_refuses_one_byte` |
| `p-rebuild-original-once` | `# M:GAS-REBUILD-ORIGINAL-ONCE` | `tests/test_grok_audit_surface_probe.py::test_seed_rebuild_refuses_a_twice_occurring_original` |
| `p-rebuild-section-twice` | `# M:GAS-REBUILD-SECTION-TWICE` | `tests/test_grok_audit_surface_probe.py::test_seed_rebuild_refuses_two_seeds_in_one_section` |
| `p-rebuild-version-history` | `# M:GAS-REBUILD-VERSION-HISTORY` | `tests/test_grok_audit_surface_probe.py::test_seed_rebuild_refuses_a_seed_under_version_history` |
| `p-rebuild-section-name` | `# M:GAS-REBUILD-SECTION-NAME` | `tests/test_grok_audit_surface_probe.py::test_seed_rebuild_refuses_a_wrong_section_name` |
| `p-rebuild-seeded-once` | `# M:GAS-REBUILD-SEEDED-ONCE` | `tests/test_grok_audit_surface_probe.py::test_seed_rebuild_refuses_a_seeded_span_not_once` |
| `p-refusal-reason` | `# M:GAS-REFUSAL-REASON` | `tests/test_grok_audit_surface_probe.py::test_ledger_counts_refuses_an_unparseable_line` |

Each `replace` makes its condition never fire, except `p-refusal-reason`'s, which prints
`internal:Refusal` in place of `exc.reason` (Task 2's `refusal_token`; a `Refusal` is a declared
class, so no traceback is printed and the kill is by assertion).

**Dependencies on other tasks**: Task 2.

---

## Task 4: build-root, content scan, reach check

**Production file**: `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py` (extend)
**Test files**: `h-mad/tests/test_grok_audit_surface_probe.py` (extend), `h-mad/tests/grokauditfixtures.py` (extend)
**Task shape**: `new-behaviour`

**Description**: `build-root` steps 1–6 of D5 for a fresh root (`--dest-parent` or the default
`tempfile.mkdtemp(prefix=f"gas-root-d{k}-{purpose}-")`): the list read at the `--list-commit` commit with
`git cat-file blob`, D4 on the calibration sha, `git archive` read by `tarfile` with
`extractall(filter="data")`, list removal with a re-walk, `placements(doc, sources)`, then D6 and
D7, then `ROOT: READY`. The D6 normaliser is the one function for needle and haystack. The
`ROOT: READY` parser `parse_root_line` lands here, since its authority is this mode. `--reset` is
parsed (Task 2) and not handled until Task 5. The design writes `placements(doc)`; the plan passes
the parsed `sources` mapping as a second argument because D1 requires every in-process check to
receive the one parsed mapping.

**Code structure**:
```python
def normalise(data: bytes) -> str: ...
def read_exclusions(repo: Path, list_commit: str) -> tuple[list[tuple[str, str]], str, str]: ...  # (entries, list_commit sha40, list_blob)
def placements(doc: str, sources: dict[str, str]) -> dict[str, str]: ...  # live path -> tree path
def scan_root(root: Path, ledger: list[dict], sources: dict[str, str], doc: str) -> None: ...  # raises Refusal("leak:" + path)
def reach_check(root: Path) -> None: ...  # raises Refusal("root_git:" + path)
def build_root(args: argparse.Namespace) -> str: ...  # the ROOT: READY line
def parse_root_line(line: str) -> dict[str, str] | None: ...  # None unless every D2 field is present
def _mode_build_root(args: argparse.Namespace) -> int: ...
```

**Tests** (21):
- Leak (11): `test_leak_original_hit`, `test_leak_expected_hit`, `test_leak_hit_only_after_rewrap`,
  `test_leak_symlink_to_file`, `test_leak_symlink_to_dir`,
  `test_leak_original_in_paired_copy_with_other_sha`,
  `test_leak_expected_in_byte_identical_paired_copy`, `test_leak_on_the_seeded_target`,
  `test_leak_tar_member_leaving_the_root`, `test_leak_exclusion_line_outside_the_grammar`, and the
  must-not-refuse `test_original_in_byte_identical_own_source_copy_does_not_refuse`.
- Reach (4): `test_root_git_dot_git_directory`, `test_root_git_dot_git_file`,
  `test_root_git_root_nested_in_work_tree`, `test_root_git_ignores_ambient_git_dir_env`.
- Root build (4): `test_build_root_places_only_the_phase_pairs`,
  `test_build_root_removes_every_exclusion_entry`,
  `test_build_root_reads_the_list_from_the_commit_not_the_work_tree`,
  `test_build_root_prints_list_commit_and_blob`.
- Parser (2): `test_root_line_parser_reads_build_root_output`, and its must-not-parse fixture
  `test_root_line_parser_rejects_a_malformed_root_line` (D10: every token parser has one). It
  calls `parse_root_line` in process on (a) a `ROOT: READY` line rendered by `build-root` with its
  `list_blob=` field removed, and (b) a `ROOT: UNREADABLE reason=leak:x` line, and asserts `None`
  for each. Callers map `None` to their own reasons (`root_record:no_line` in `record-cycle`,
  `list_changed:unrecorded` in `rescore`).

**Acceptance Criteria**:
- [ ] AC-T4.1: Each leak test's last line is `ROOT: UNREADABLE reason=leak:` followed by the
  fixture's root-relative path (the list's tree path for the grammar test), exit 2; each reach test
  `reason=root_git:` followed by the path D7 names.
- [ ] AC-T4.2: The two must-not-refuse tests read `ROOT: READY`, exit 0.
- [ ] AC-T4.3: `test_build_root_prints_list_commit_and_blob` checks `list_commit=` and `list_blob=`
  against `git rev-parse HEAD` and `git rev-parse HEAD:docs/03-analysis/probes/grok-audit-surface/exclusions.txt`
  in the fixture repo.
- [ ] AC-T4.4: `placements` is the only function that maps a document to live paths (grep shows one
  definition and no second mapping).

**RED split**: 21 nodes; 21 F (no handler; `parse_root_line` absent), 0 P.

**Mutation rows** (14; markers 11):

| name | marker | test |
|---|---|---|
| `p-leak-original` | `# M:GAS-LEAK-ORIGINAL` | `tests/test_grok_audit_surface_probe.py::test_leak_original_hit` |
| `p-leak-expected` | `# M:GAS-LEAK-EXPECTED` | `tests/test_grok_audit_surface_probe.py::test_leak_expected_hit` |
| `p-leak-normalise` | `# M:GAS-LEAK-NORMALISE` | `tests/test_grok_audit_surface_probe.py::test_leak_hit_only_after_rewrap` |
| `p-leak-symlink-file` | `# M:GAS-LEAK-SYMLINK` | `tests/test_grok_audit_surface_probe.py::test_leak_symlink_to_file` |
| `p-leak-symlink-dir` | `# M:GAS-LEAK-SYMLINK` | `tests/test_grok_audit_surface_probe.py::test_leak_symlink_to_dir` |
| `p-leak-exempt-sha-paired` | `# M:GAS-LEAK-EXEMPT-SHA` | `tests/test_grok_audit_surface_probe.py::test_leak_original_in_paired_copy_with_other_sha` |
| `p-leak-exempt-sha-target` | `# M:GAS-LEAK-EXEMPT-SHA` | `tests/test_grok_audit_surface_probe.py::test_leak_on_the_seeded_target` |
| `p-leak-exempt-original-only` | `# M:GAS-LEAK-EXEMPT-ORIGINAL-ONLY` | `tests/test_grok_audit_surface_probe.py::test_leak_expected_in_byte_identical_paired_copy` |
| `p-leak-tar` | `# M:GAS-LEAK-TAR` | `tests/test_grok_audit_surface_probe.py::test_leak_tar_member_leaving_the_root` |
| `p-leak-list-grammar` | `# M:GAS-LEAK-LIST-GRAMMAR` | `tests/test_grok_audit_surface_probe.py::test_leak_exclusion_line_outside_the_grammar` |
| `p-reach-dotgit-dir` | `# M:GAS-REACH-DOTGIT` | `tests/test_grok_audit_surface_probe.py::test_root_git_dot_git_directory` |
| `p-reach-dotgit-file` | `# M:GAS-REACH-DOTGIT` | `tests/test_grok_audit_surface_probe.py::test_root_git_dot_git_file` |
| `p-reach-revparse` | `# M:GAS-REACH-REVPARSE` | `tests/test_grok_audit_surface_probe.py::test_root_git_root_nested_in_work_tree` |
| `p-parse-root` | `# M:GAS-PARSE-ROOT` | `tests/test_grok_audit_surface_probe.py::test_root_line_parser_rejects_a_malformed_root_line` |

**Dependencies on other tasks**: Task 3.

---

## Task 5: the S1 root reset

**Production file**: `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py` (extend)
**Test file**: `h-mad/tests/test_grok_audit_surface_probe.py` (extend)
**Task shape**: `new-behaviour`

**Description**: `build-root --reset` per D5, "Resetting the S1 root between its cycles": the mode
checks `--reset` against `--dest-parent` first (`ResetArgsConflict`, `# M:GAS-RESET-EXCLUSIVE`), then
the purpose (below), then the five target guards in D5's order (`# M:GAS-RESET-ABS`,
`# M:GAS-RESET-ISDIR`, `# M:GAS-RESET-TMPDIR`, `# M:GAS-RESET-PREFIX`, `# M:GAS-RESET-REACH`), and only
then builds the expected tree (steps 1–5 into a fresh `mkdtemp`), makes the live root equal to it,
re-walks it (`RootResetMismatch`, `# M:GAS-RESET-REWALK`), runs step 6 on the live root
(`# M:GAS-RESET-SCAN`, `# M:GAS-RESET-STEP6-REACH`), removes the expected tree, and prints
the published `RESET:` line (D5) and then the `ROOT: READY` token with `path=` the live root.

**The reset never follows a link (carry 2, destructive class).** A symlinked placed document, a
symlinked by-product directory, or a symlinked directory on the path to a placed document would let
the reset write or delete outside the root before step 6 sees the link. The reset therefore walks the
live root with `os.walk(followlinks=False)` and judges every entry by `os.lstat`: an entry that is a
link is removed with `os.unlink` (never `shutil.rmtree`, never by its target), whether or not its
path is in the expected tree (`# M:GAS-RESET-NOFOLLOW-REMOVE`). Every ancestor directory between
the root and a path `restore_expected` writes is `lstat`-ed, and an ancestor that is a link is
unlinked and recreated as a real directory before the write (`# M:GAS-RESET-NOFOLLOW-PARENT`).
The file itself is opened with `os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW`
(`# M:GAS-RESET-NOFOLLOW-WRITE`). Measured on this Mac: that open of a link fails with `ELOOP`,
and `restore_expected` then unlinks the link and creates the file with
`O_CREAT | O_EXCL | O_NOFOLLOW`. `O_NOFOLLOW` guards only the last path component (measured: an
`O_NOFOLLOW` open through a linked parent directory wrote the outside file), which is why the
ancestor check is a separate guard. Reproduce (the temporary directory removes itself):

```bash
/opt/anaconda3/bin/python3.11 -c '
import os,errno,tempfile
with tempfile.TemporaryDirectory() as d:
    v=os.path.join(d,"victim"); open(v,"w").write("S"); l=os.path.join(d,"link"); os.symlink(v,l)
    try: os.open(l, os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW); print("opened")
    except OSError as e: print("link:", errno.errorcode[e.errno])
    o=os.path.join(d,"out"); os.mkdir(o); open(os.path.join(o,"doc"),"w").write("S"); os.symlink(o, os.path.join(d,"feat"))
    fd=os.open(os.path.join(d,"feat","doc"), os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW); os.write(fd,b"X"); os.close(fd)
    print("parent link, outside file now:", open(os.path.join(o,"doc")).read())'
# link: ELOOP
# parent link, outside file now: X
```

A real directory absent from the expected tree is removed with `shutil.rmtree`, which does not
follow the links it meets inside it.

**Which test can see which guard (audit cycle 1; axis: a link present when a write happens).**
`remove_absent` runs first and unlinks every link in the live root, so by the time
`restore_expected` runs, an end-to-end reset fixture has no link left. A write-through or
parent-through mutant of `restore_expected` is therefore invisible to any end-to-end fixture: it
survives, and the end-to-end fixture shows nothing about it. The two restore guards are tested
at `restore_expected`'s own boundary instead. Their tests call
`probe.restore_expected(live, expected)` in process (loaded with `load_probe`) on a live tree that
holds the link at that moment. `remove_absent`'s guard keeps its end-to-end fixture. Residual,
stated exactly: a link created inside the root *between* `restore_expected`'s check of a path and
its write of that path (a concurrent writer) is outside every guard. The reset assumes no writer
runs in the root, and the post-reset `lstat` re-walk (`RootResetMismatch`) reports a link that
is present afterwards, but not a write that has already happened outside.

**`--reset` requires `--purpose s1` (carry 13).** Guard 4's prefix is the literal `s1`, so
`--purpose s2v1 --reset` on an S1 root passes all five guards and would reset the S1 root under a
`purpose=s2v1` token: the S1 root reused for S2, which D5 forbids ("The S1 root is never reused for
S2"). Right after the exclusivity check, `--reset` with any `--purpose` other than `s1` raises
`ResetPurposeNotS1` (`# M:GAS-RESET-PURPOSE`), printed by the last resort as
`ROOT: UNREADABLE reason=internal:ResetPurposeNotS1`, before anything is removed. This is a guard the
design does not name; it is reported to the design as owed.

**Fixtures (carry 3).** Every reset fixture builds its S1 root with the default parent (no
`--dest-parent`, so the root is directly under `tempfile.gettempdir()`) and with `--purpose s1 --doc d1`,
and resets it with the same `--doc d1 --purpose s1` and the root's own `--list-commit`, so guards 3
and 4 pass; the only exceptions are the fixtures whose trigger is that value
(`…_outside_the_tempdir` uses a `tmp_path` directory, `…_another_documents_root` a
`gas-root-d2-s1-` directory with `--doc d1`, `…_non_s1_purpose` `--purpose s2v1`). Each built root is
removed by the fixture's finalizer. The carry-2 fixtures put every link target under `tmp_path`, so a
mutant that follows a link can only damage the test's own directory. **S0c (Task 24) changes this
paragraph's parent:** there is no default parent any more, so every reset fixture builds its S1 root
with `--dest-parent <tmp_path>/run/roots`, outside the stand-in system temp (`<tmp_path>/run/roots`
and `<tmp_path>/systemp` are siblings), and guard 3 is inverted
(`ResetTargetInSystemTemp`); the test named `…_outside_the_tempdir` above is renamed
`test_build_root_reset_refuses_a_target_in_system_temp` by Task 24, which also rewrites its fixture.

**OPEN-DECISION: D5's post-reset re-walk raises `RootResetMismatch` before step 6 runs, so
`test_build_root_reset_runs_the_reach_check` and `test_build_root_reset_rescans_after_removal`, whose
in-process replaced removal step leaves an extra path in the live root, cannot reach the `leak:` or
`root_git:` token they assert (carry 1, must) — resolve in 5d.** Two implementations satisfy both
tests: (a) reorder D5 so step 6 (scan, then reach) runs on the live root before the re-walk
assertion; or (b) keep D5's order and have those two fixtures also replace `rewalk_matches` with a
function that returns without raising, so step 6 is reached. (b) changes only the two fixtures; (a)
changes D5's order of operations and is owed to the design if chosen. Either way
`test_build_root_reset_mismatch_is_internal` keeps its token. The RED at 5d cannot show the choice
(the reset is absent then); the first GREEN attempt shows which fixture is unsatisfiable under D5 as
written, and the choice is recorded in the Task's GREEN report.

**Code structure**:
```python
class ResetArgsConflict(ProbeRefusal): ...
class ResetPurposeNotS1(ProbeRefusal): ...
class ResetTargetNotAbsolute(ProbeRefusal): ...
class ResetTargetNotDirectory(ProbeRefusal): ...
class ResetTargetOutsideTempdir(ProbeRefusal): ...
class ResetTargetPrefix(ProbeRefusal): ...
class RootResetMismatch(ProbeRefusal): ...
def check_reset_target(target: str, doc: str) -> Path: ...
def remove_absent(live: Path, expected: Path) -> int: ...
def restore_expected(live: Path, expected: Path) -> int: ...
def rewalk_matches(live: Path, expected: Path) -> None: ...
def reset_root(args: argparse.Namespace) -> str: ...  # the ROOT: READY line
```

**Tests** (15):
- From D5 (11): `test_build_root_reset_removes_by_products_and_restores_placed_files`,
  `test_build_root_reset_rescans_after_removal`, `test_build_root_reset_runs_the_reach_check`,
  `test_build_root_reset_mismatch_is_internal`, `test_build_root_reset_and_dest_parent_are_exclusive`,
  `test_build_root_reset_refuses_an_empty_target`, `test_build_root_reset_refuses_a_missing_target`,
  `test_build_root_reset_refuses_a_target_in_system_temp` (built at S0 as `…_outside_the_tempdir`;
  renamed and rewritten by Task 24),
  `test_build_root_reset_refuses_another_documents_root`, `test_build_root_reset_refuses_a_git_target`,
  and the must-not-refuse `test_build_root_reset_accepts_the_physical_spelling_of_its_root`.
- Carry 2 (3, plan-added), each asserting both directions of one link kind — the link is not
  followed (the outside target is unchanged) and the link is acted on (it is gone or replaced):
  `test_build_root_reset_does_not_delete_through_a_symlinked_by_product_dir` (end to end:
  `.h-mad/pass-logs` in the live root is a link to `tmp_path/outside/logs/` holding a sentinel file;
  afterwards that directory and its sentinel exist with unchanged bytes, the live root has no
  `.h-mad/pass-logs` entry, and the token is `ROOT: READY`);
  `test_restore_expected_does_not_write_through_a_symlinked_placed_document` (in process, at
  `restore_expected`'s boundary: a live tree equal to `expected` except that the seeded target's path
  is a link to `tmp_path/outside/victim.md` holding sentinel bytes; after
  `restore_expected(live, expected)` the victim's bytes are unchanged and the live path is a regular
  file whose sha256 equals the expected file's);
  `test_restore_expected_does_not_write_through_a_symlinked_parent_directory` (in process: the seeded
  target's parent directory in the live tree is a link to `tmp_path/outside/features/`, which holds a
  sentinel file of the target's name; afterwards the sentinel's bytes are unchanged, the live parent
  is a real directory, and the file in it equals the expected file).
- Carry 13 (1, plan-added): `test_build_root_reset_refuses_a_non_s1_purpose` (an S1 root of `d1`,
  reset with `--purpose s2v1`: `ROOT: UNREADABLE reason=internal:ResetPurposeNotS1`, and a sentinel
  planted in the root is unchanged).

**Acceptance Criteria**:
- [ ] AC-T5.1: Task 5's refusal tests are these 10:
  - the precondition and argument refusals (`internal:` and a declared reset class):
    `test_build_root_reset_and_dest_parent_are_exclusive`,
    `test_build_root_reset_refuses_a_non_s1_purpose`,
    `test_build_root_reset_refuses_an_empty_target`,
    `test_build_root_reset_refuses_a_missing_target`,
    `test_build_root_reset_refuses_a_target_in_system_temp` (Task 24's name),
    `test_build_root_reset_refuses_another_documents_root`;
  - `test_build_root_reset_mismatch_is_internal` (`RootResetMismatch`);
  - the `Refusal`-raising ones: `test_build_root_reset_refuses_a_git_target` (`root_git:`),
    `test_build_root_reset_rescans_after_removal` (`leak:`),
    `test_build_root_reset_runs_the_reach_check` (`root_git:`).

  Each asserts, in this order:
  1. its exact token as D5's Test Plan entry states it, with stderr as the message;
  2. for the six precondition and argument refusals, that its sentinel is still there with its
     bytes unchanged (the missing-target test: the path is still absent);
  3. that the traceback count, computed into a local `n` as rule (3) spells it, is 0.

  So the traceback-absence check covers both a declared reset class and `Refusal`.
- [ ] AC-T5.2: `test_build_root_reset_removes_by_products_and_restores_placed_files` asserts the path
  set and every sha256 equal a fresh build's, the published line `RESET: removed=` with the planted
  count and `restored=1`, and the original `ROOT: READY` line as the token.
- [ ] AC-T5.3: The three carry-2 tests pass, and `grep -n 'rmtree' docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py` shows `rmtree` called
  only on paths whose `os.lstat` is a directory and not a link.
- [ ] AC-T5.4: The OPEN-DECISION above is resolved and the choice is stated in the GREEN report.

**RED split**: 15 nodes; 15 F (at RED `--reset` is parsed and ignored, so every end-to-end test sees
a fresh root's token or no refusal, and the two `restore_expected` tests find no such attribute), 0 P.

**Mutation rows** (14; markers 13, plus the reused `GAS-TRACEBACK-SCOPE`). Each `replace` makes its
condition never fire, except `p-traceback-scope-reset`'s, which narrows Task 2's traceback scope to
`UsageError` alone, so a declared reset class prints a traceback and the count assertion of its
target fails after its token assertion has passed; and except the three
no-follow rows, whose `replace` follows the link: the unlink becomes removal of the resolved target
(its target is under `tmp_path`); `O_NOFOLLOW` is dropped from the first open; the ancestor check is
skipped. Each of those three mutants then writes or deletes through the link that its own fixture
holds at that moment, so the kill is by assertion on the outside sentinel, never a crash:

| name | marker | test |
|---|---|---|
| `p-reset-exclusive` | `# M:GAS-RESET-EXCLUSIVE` | `tests/test_grok_audit_surface_probe.py::test_build_root_reset_and_dest_parent_are_exclusive` |
| `p-reset-purpose` | `# M:GAS-RESET-PURPOSE` | `tests/test_grok_audit_surface_probe.py::test_build_root_reset_refuses_a_non_s1_purpose` |
| `p-reset-abs` | `# M:GAS-RESET-ABS` | `tests/test_grok_audit_surface_probe.py::test_build_root_reset_refuses_an_empty_target` |
| `p-reset-isdir` | `# M:GAS-RESET-ISDIR` | `tests/test_grok_audit_surface_probe.py::test_build_root_reset_refuses_a_missing_target` |
| `p-reset-tmpdir` (rewritten in place by Task 24) | `# M:GAS-RESET-TMPDIR` | `tests/test_grok_audit_surface_probe.py::test_build_root_reset_refuses_a_target_in_system_temp` |
| `p-reset-prefix` | `# M:GAS-RESET-PREFIX` | `tests/test_grok_audit_surface_probe.py::test_build_root_reset_refuses_another_documents_root` |
| `p-reset-reach` | `# M:GAS-RESET-REACH` | `tests/test_grok_audit_surface_probe.py::test_build_root_reset_refuses_a_git_target` |
| `p-reset-rewalk` | `# M:GAS-RESET-REWALK` | `tests/test_grok_audit_surface_probe.py::test_build_root_reset_mismatch_is_internal` |
| `p-reset-scan` | `# M:GAS-RESET-SCAN` | `tests/test_grok_audit_surface_probe.py::test_build_root_reset_rescans_after_removal` |
| `p-reset-step6-reach` | `# M:GAS-RESET-STEP6-REACH` | `tests/test_grok_audit_surface_probe.py::test_build_root_reset_runs_the_reach_check` |
| `p-reset-nofollow-write` | `# M:GAS-RESET-NOFOLLOW-WRITE` | `tests/test_grok_audit_surface_probe.py::test_restore_expected_does_not_write_through_a_symlinked_placed_document` |
| `p-reset-nofollow-remove` | `# M:GAS-RESET-NOFOLLOW-REMOVE` | `tests/test_grok_audit_surface_probe.py::test_build_root_reset_does_not_delete_through_a_symlinked_by_product_dir` |
| `p-reset-nofollow-parent` | `# M:GAS-RESET-NOFOLLOW-PARENT` | `tests/test_grok_audit_surface_probe.py::test_restore_expected_does_not_write_through_a_symlinked_parent_directory` |
| `p-traceback-scope-reset` | `# M:GAS-TRACEBACK-SCOPE` | `tests/test_grok_audit_surface_probe.py::test_build_root_reset_refuses_an_empty_target` |

**Dependencies on other tasks**: Task 4.

---

## Task 6: record-cycle and commit-data

**Production file**: `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py` (extend)
**Test files**: `h-mad/tests/test_grok_audit_surface_probe.py` (extend), `h-mad/tests/grokauditfixtures.py` (extend)
**Task shape**: `new-behaviour`

**Description**: `record-cycle` per D8 (`--feature`, `--phase`, `--cycle` read from the command
file; the stem's single prefix of the form `audit_${feature}_${phase}_cycle${cycle}_run`, matching the wrapper's
`stem="${stem_dir}/audit_${feature}_${phase}_cycle${cycle}_run…"` in `_cmd_audit_cycle`; the D3 file
map; only this cycle's `v<N>` reports, sidecars and pass logs; `root.txt` from `--root-record`;
`mkdir(parents=True, exist_ok=True)`; the re-list and `files=`). `commit-data` per D9 (temporary
index, `hash-object`, `update-index --cacheinfo`, `write-tree`, `commit-tree`, `update-ref` with the
expected old value, the re-read). The stem files are copied byte for byte, so `p1.log` is exactly
the file the wrapper passed as `--log` (`log[$i]="${stem}_p${i}.log"`); that is what keeps D11 step
3's wrong-file guard unreachable on real inputs (carry 14), and a plan-added test pins it. D2 names
three `record-cycle` reasons the design's Test Plan gives no fixture (`input_missing:`,
`stem_prefix:`, `command_unparseable:`); each gets one here, plan-added and reported to the design.
**`parse_root_line`'s `None` (Task 4) maps here to `root_record:no_line`** (`# M:GAS-RECORD-ROOT-MALFORMED`):
a `--root-record` file whose one `ROOT: READY` line lacks a D2 field (for example `list_blob=`) is
refused exactly like a file with no such line. D5 defines `root_record:no_line` as "no `ROOT: READY`
line or more than one"; extending it to a malformed line is a plan extension, owed to the design.

**Code structure**:
```python
def record_cycle(args: argparse.Namespace) -> str: ...  # the RECORD: OK line
def commit_data(args: argparse.Namespace) -> str: ...   # the COMMIT: OK line
def _git(repo: Path, *argv: str, env: dict[str, str] | None = None, stdin: bytes | None = None) -> subprocess.CompletedProcess: ...
def _mode_record_cycle(args: argparse.Namespace) -> int: ...
def _mode_commit_data(args: argparse.Namespace) -> int: ...
```

**Tests** (16):
- From D5/D8/D9 (10): `test_record_cycle_writes_root_txt`,
  `test_record_cycle_refuses_a_root_record_without_a_line`,
  `test_record_cycle_refuses_a_root_record_for_another_root`,
  `test_record_cycle_refuses_stdout_without_auditcycle`,
  `test_record_cycle_copies_only_its_own_cycle_reports`,
  `test_commit_data_never_touches_work_tree_or_index`, `test_commit_data_refuses_an_unknown_parent`,
  `test_commit_data_refuses_a_moved_ref`, `test_commit_data_refuses_outside_calibration_dir`,
  `test_commit_data_rereads_the_ref` (in process: the probe's ref read after `update-ref` replaced to
  return another oid; `COMMIT: REFUSED reason=ref_unconfirmed`).
- Plan-added (6): `test_record_cycle_refuses_a_root_record_with_a_malformed_ready_line` (a
  `ROOT: READY` line rendered by `build-root` with its `list_blob=` field removed:
  `RECORD: REFUSED reason=root_record:no_line`), `test_record_cycle_copies_stem_files_byte_for_byte` (carry 14: every copied file's
  sha256 equals its stem source's), `test_record_cycle_refuses_a_missing_input` (`--stdout` absent:
  `RECORD: REFUSED reason=input_missing:` and that path), `test_record_cycle_refuses_zero_stem_prefixes`
  (`reason=stem_prefix:0`), `test_record_cycle_refuses_two_stem_prefixes` (`reason=stem_prefix:2`),
  `test_record_cycle_refuses_a_command_without_cycle_flags` (a command file lacking `--cycle`:
  `reason=command_unparseable:` and that file).

**Acceptance Criteria**:
- [ ] AC-T6.1: Each refusal test asserts its exact `RECORD: REFUSED` or `COMMIT: REFUSED` token and
  exit 2, then the state that refusal leaves (axis: when the refusal fires relative to `update-ref`).
  - Pre-write refusals (`parent_unknown`, `ref_moved`, `outside_calibration_dir`) fire before
    `update-ref` runs. Their tests assert that
    `git rev-parse --verify refs/heads/calibration/grok-audit-surface` reads the pre-test value (or
    fails, when the ref did not exist).
  - The post-write refusal (`ref_unconfirmed`, `test_commit_data_rereads_the_ref`) fires after a
    successful `update-ref`. D9 specifies no rollback, and the probe performs none, so the test
    asserts the ref's actual value: the commit `commit-tree` made, read through a real
    `git rev-parse` outside the replaced function. Residual, stated exactly: a `ref_unconfirmed`
    refusal can leave the ref moved. The operator reads the ref with `git rev-parse` before
    re-running, and the next `commit-data` takes that value as `--parent` or refuses `ref_moved`.
  - `record-cycle` refusals assert that no dest file was written.
- [ ] AC-T6.2: `test_commit_data_never_touches_work_tree_or_index` asserts `git status --porcelain`
  and the sha256 of `.git/index` are unchanged across the call.

**RED split**: 16 nodes; 16 F (no handlers), 0 P.

**Mutation rows** (12; markers 11). Each `replace` makes its condition never fire, except
`p-record-root-malformed`'s, which maps `parse_root_line`'s `None` to `root_record:path_mismatch` in place
of `root_record:no_line` (a declared reason, so the code keeps running and the kill is by assertion):

| name | marker | test |
|---|---|---|
| `p-record-root-line` | `# M:GAS-RECORD-ROOT-LINE` | `tests/test_grok_audit_surface_probe.py::test_record_cycle_refuses_a_root_record_without_a_line` |
| `p-record-root-path` | `# M:GAS-RECORD-ROOT-PATH` | `tests/test_grok_audit_surface_probe.py::test_record_cycle_refuses_a_root_record_for_another_root` |
| `p-record-root-malformed` | `# M:GAS-RECORD-ROOT-MALFORMED` | `tests/test_grok_audit_surface_probe.py::test_record_cycle_refuses_a_root_record_with_a_malformed_ready_line` |
| `p-record-auditcycle` | `# M:GAS-RECORD-AUDITCYCLE` | `tests/test_grok_audit_surface_probe.py::test_record_cycle_refuses_stdout_without_auditcycle` |
| `p-record-input` | `# M:GAS-RECORD-INPUT` | `tests/test_grok_audit_surface_probe.py::test_record_cycle_refuses_a_missing_input` |
| `p-record-stem-zero` | `# M:GAS-RECORD-STEM-PREFIX` | `tests/test_grok_audit_surface_probe.py::test_record_cycle_refuses_zero_stem_prefixes` |
| `p-record-stem-two` | `# M:GAS-RECORD-STEM-PREFIX` | `tests/test_grok_audit_surface_probe.py::test_record_cycle_refuses_two_stem_prefixes` |
| `p-record-command` | `# M:GAS-RECORD-COMMAND` | `tests/test_grok_audit_surface_probe.py::test_record_cycle_refuses_a_command_without_cycle_flags` |
| `p-commit-parent` | `# M:GAS-COMMIT-PARENT` | `tests/test_grok_audit_surface_probe.py::test_commit_data_refuses_an_unknown_parent` |
| `p-commit-ref-moved` | `# M:GAS-COMMIT-REF-MOVED` | `tests/test_grok_audit_surface_probe.py::test_commit_data_refuses_a_moved_ref` |
| `p-commit-outside` | `# M:GAS-COMMIT-OUTSIDE` | `tests/test_grok_audit_surface_probe.py::test_commit_data_refuses_outside_calibration_dir` |
| `p-commit-reread` | `# M:GAS-COMMIT-REREAD` | `tests/test_grok_audit_surface_probe.py::test_commit_data_rereads_the_ref` |

**Dependencies on other tasks**: Task 4 (`parse_root_line` reads `--root-record`).

---

## Task 7: smoke

**Production file**: `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py` (extend)
**Test files**: `h-mad/tests/test_grok_audit_surface_smoke.py` (create),
`h-mad/tests/test_grok_audit_surface_probe.py` (extend)
**Task shape**: `new-behaviour`

**Description**: `smoke` per D11, with D10's `parse_auditcycle` and `parse_effort_items` (each with a
must-parse fixture rendered by `h_mad_audit_cycle.render` / `_effort_items` and a must-not-parse
fixture), the UNREADABLE checks in D11's fixed order, the five step-3 forms, the reasons in AC-1.7
order, the published `VOCAB:`, `ROOT-ACCEPT:`, `TIMEOUT:` and `GROK-BINARY:` lines, and exit 0 on
PASS/FAIL, 2 on UNREADABLE. `_gate_token` raises `h_mad_audit_cycle.OperationalError` when the gate
prints no `GATE:` line; the smoke maps that to `input_unparseable:` and the collected report's path.
The smoke assigns each input's path to the module-level `_OPEN_INPUT` immediately before it opens
that input (Task 2's `refusal_token` reads it), so the last resort's `input_unparseable:` path is
that input (D1). Fixture grok logs come from `grokfixtures` (`f0_text`, `f_trunc`, `f0_with_completed`).

**One reader for the grok log's type set (carry 5).** `grok_log_types(text)` is the one function
step 2, `vocab_missing` and the `VOCAB:` lines read. Its line acceptance is `scan_grok`'s in every
step but one: it splits on `"\n"`, skips a line whose `json.loads` raises `ValueError` or
`RecursionError`, skips a non-dict, and takes a string `type`; the one difference is that it does not
apply `scan_grok`'s `_json_deeper_than(event, GROK_MAX_DEPTH)` skip and does not filter to
`_GROK_TYPES`. So the open class of lines that this reader counts and `scan_grok` skips is exactly:
lines that parse to a dict with a string `type` and hold a value nested deeper than `GROK_MAX_DEPTH`.
That is D11 residual (2) stated exactly. A line whose `json.loads` raises `RecursionError` is skipped
by both readers, so it is not in residual (2); D11's sentence naming it there, and its "guaranteed"
for `unparseable` (which holds only for logs outside this class), are reported to the design.

**Residual-(2) fixture depth (carry 15).** `test_smoke_deep_grok_types_with_unparseable_item_refuses`
(built at S0 as `…_is_the_stated_residual`, asserting `SMOKE: PASS`; renamed and flipped to
`SMOKE: UNREADABLE` by Task 26, design v1.8) builds its nested value from the imported constant, never a literal: `v = 0`, then `GROK_MAX_DEPTH`
times `v = [v]`, and each line is `{"type": t, "x": v}`. It first asserts
`_json_deeper_than(event, GROK_MAX_DEPTH)` is true for each line and that `measure_effort` gives shape
`unparseable`.

**Unrecognised Effort item (carry 4).** D11 step 3's default branch (an item in none of the five
forms) gets its own fixture, `test_smoke_unrecognised_effort_item_refuses`: a `grok/auditcycle.txt`
whose `p1` Effort item is `p1 measured by a renderer this design does not name` beside a `p1.log`
holding `f0_text()`; `SMOKE: UNREADABLE reason=input_unparseable:` followed by the
`grok/auditcycle.txt` path, exit 2.

**Wrong-file fixtures are synthetic pairings (carry 14).** Step 2 refuses a recorded wrong file first,
so the three wrong-file fixtures put `f0_text()` in `grok/p1.log` beside the wrong-file item; the
wrapper does not produce that pairing, and Task 6's byte-for-byte copy pin is what keeps it from
arising on real records.

**A wrong-file UNREADABLE cannot be cleared by AC-1.7's remedy (carry 10).** A `missing`, `empty` or
`codex-text` item is rendered by the wrapper into `auditcycle.txt`, so restoring inputs and deriving
again from the same passes gives the same token; only a new smoke (a new reading) clears it. The spec
gap is reported; Task 16's runbook states it beside the UNREADABLE remedy.

**Code structure**:
```python
AUDITCYCLE_RE = re.compile(r"^AUDITCYCLE: (PASS|FAIL|UNVERIFIED)( \S+)*$")
GROK_ITEM_RE = re.compile(r"^p1 tools=\d+ ok=\d+ unresolved=\d+ thinking=\d+ format=grok( |$)")
COUNTS_ITEM_RE = re.compile(r"^p1 tools=\d+ ok=\d+ failed=\d+ thinking=\d+( |$)")
def parse_auditcycle(text: str) -> dict: ...
def parse_effort_items(text: str) -> list[str] | None: ...  # [] with no Effort: line; None for a malformed block
def grok_log_types(text: str) -> dict[str, list[dict]]: ...  # type -> its events
def effort_form(item: str) -> str: ...  # "grok" | "truncated" | "counts" | "wrong-file" | "unknown"
def vocab_sets(vocab_py: Path, vocab_sh: Path) -> tuple[frozenset[str], frozenset[str]]: ...
def delivered(cycle_dir: Path, parsed: dict) -> bool: ...
def smoke(data: Path, vocab_py: Path, vocab_sh: Path) -> tuple[list[str], str]: ...  # (published lines, token)
def _mode_smoke(args: argparse.Namespace) -> int: ...
```

**Tests** — smoke module (44), each asserting its exit code beside its exact token:
- PASS and FAIL (11): `test_smoke_pass`, `test_smoke_pass_on_out_delivery`, `test_smoke_truncated`,
  `test_smoke_vocab_split`, `test_smoke_vocab_missing_end`, `test_smoke_vocab_missing_tool_call`,
  `test_smoke_vocab_missing_tool_call_update`, `test_smoke_no_delivery`,
  `test_smoke_no_delivery_on_unscorable`, `test_smoke_nongit_root_refused_grok`,
  `test_smoke_nongit_root_refused_agy`.
- UNREADABLE (3): `test_smoke_input_missing`, `test_smoke_input_missing_delivered_collected_report`,
  `test_smoke_input_unparseable`.
- Step 3 (11): `test_smoke_drifted_log_with_unparseable_item_fails`,
  `test_smoke_drifted_log_with_parsed_item_fails`,
  `test_smoke_effort_codex_text_item_refuses_as_wrong_file`,
  `test_smoke_effort_missing_item_refuses_as_wrong_file`,
  `test_smoke_effort_empty_item_refuses_as_wrong_file`, `test_smoke_unrecognised_effort_item_refuses`
  (plan-added, carry 4), `test_smoke_parsed_item_with_all_three_types_refuses`,
  `test_smoke_deep_grok_types_with_unparseable_item_refuses` (both built at S0 under
  `…_is_the_stated_residual` names asserting `SMOKE: PASS`; renamed and flipped by Task 26),
  `test_smoke_effort_grok_item_with_targets_is_grok`, `test_grok_item_predicate_matches_the_renderer`
  (derives the seven `measure_effort` shapes with the D11 regex and maps each to its one form),
  `test_truncated_predicate_matches_the_renderer`.
- Must not fail or refuse (4): `test_smoke_codex_refusal_is_not_a_reason`,
  `test_smoke_out_of_vocabulary_type_is_not_a_reason`,
  `test_smoke_halted_agy_cycle_is_a_refusal_not_unreadable`, `test_smoke_codex_text_log_is_not_an_input`.
- Grok binary (2): `test_smoke_publishes_grok_binary_line`,
  `test_smoke_grok_binary_unrecorded_is_not_unreadable`.
- Ordering and contracts (4): `test_smoke_two_reasons_in_order`, `test_smoke_coupled_reasons_in_order`,
  `test_smoke_unreadable_outranks_fail`, `test_smoke_prints_timeout_derivation`.
- Caller contracts (2, plan-added, delta review 5f10a1d):
  - `test_smoke_last_resort_names_the_open_input` (in process, loaded with `load_probe`): a clean
    S1 fixture in which `grok_log_types` is replaced by a function raising `RuntimeError`. So
    `smoke` has assigned `_OPEN_INPUT` to the `grok/p1.log` path and opened it when the exception
    escapes. The last stdout line is `SMOKE: UNREADABLE reason=input_unparseable:` followed by
    that `grok/p1.log` path, not the `--data` value. It is a rule-(3) member (an exception injected
    on purpose).
  - `test_smoke_refuses_a_malformed_effort_block`: a grok cycle that did not reach dispatch (its
    `AUDITCYCLE:` line has no `delivered=`, so D11 step 3 does not apply) whose
    `grok/auditcycle.txt` also holds an `Effort:` block of shape (a) below. The smoke reads the
    block in step 1, and `parse_effort_items` returns `None`. The test asserts
    `SMOKE: UNREADABLE reason=input_unparseable:` followed by the `grok/auditcycle.txt` path, exit 2.
    The fixture is chosen so that the mapping is the only guard: on a cycle that reached dispatch,
    step 3's absent-item check prints the same token, and the mapping's row would survive as an
    equivalent mutant. With the mapping disarmed, this fixture reaches the reasons and prints
    `SMOKE: FAIL`.
- Opposed pairs (7): `test_m3_d1_end_event_beside_truncated_item_is_truncated`,
  `test_m3_d2_no_end_beside_grok_item_is_not_truncated`,
  `test_m4_e1_report_file_inputs_beside_delivered_none_is_no_delivery`,
  `test_m4_e2a_none_inputs_beside_report_file_is_delivered`,
  `test_m4_e2b_none_inputs_beside_out_is_delivered`,
  `test_m5_f1_unverified_token_beside_busy_log_refuses_root`,
  `test_m5_f2_pass_token_beside_hollow_log_accepts_root`. Each first runs its field's authority on the
  raw inputs (D10: `scan_grok`; `collect` with `PassSpec(index, report_path, out_path, rc, log_path)`
  and `grace=0`; `measure_effort` and `combine`) and asserts the verdict opposite to the recorded
  token.

11 + 3 + 11 + 4 + 2 + 4 + 2 + 7 = 44.

**Tests** — probe module (4): `test_auditcycle_parser_reads_render_output`,
`test_auditcycle_parser_rejects_two_lines`, `test_effort_parser_reads_effort_items_output`, and the
Effort parser's must-not-parse fixture `test_effort_parser_rejects_a_malformed_effort_block`.

**The `Effort:` block grammar (delta review 5f10a1d; axis: what `parse_effort_items` returns).**
`h_mad_audit_cycle.render` writes `Effort:` only `if effort:`, then one `- {item}` line per item
(`lines.extend(f"- {item}" for item in effort)`). After the items comes the `[H-MAD]` line on the
UNVERIFIED branch, or `Premise checklist:` / `Premise checklist: empty` on the other branch. So:
- Text with no `Effort:` line returns `[]`. That is a halted cycle or a pass with no log, and it is
  never a refusal by itself. D11 step 3's "absent" check, for a grok cycle that reached dispatch,
  is what refuses there.
- An `Effort:` line opens the block, and the block is the run of lines that follow it and begin
  with `- `. The first line that does not begin with `- ` ends it.
- The result is `None` exactly when:
  - (a) an item's text after `- ` does not begin with `p` followed by digits and a space
    (`# M:GAS-PARSE-EFFORT-ITEM`);
  - (b) the block holds no item (`# M:GAS-PARSE-EFFORT-EMPTY`);
  - (c) the text holds more than one `Effort:` line (`# M:GAS-PARSE-EFFORT-TWICE`).

Each of the three is a separate condition. The test calls `parse_effort_items` in process on
fixtures (a) `Effort:` then `- x1 tools=1 ok=1 failed=0 thinking=0`, (b) `Effort:` followed directly
by the `[H-MAD]` line, and (c) two complete `Effort:` blocks, and asserts `None` for each. It also
asserts `[]` on a halted `AUDITCYCLE:` text rendered by `render` with no results (the must-not-refuse
half).

**Callers of `None`:** `smoke` maps it to `input_unparseable:` and the `grok/auditcycle.txt` path
(`# M:GAS-SMOKE-EFFORT-MALFORMED`, pinned by `test_smoke_refuses_a_malformed_effort_block`). Task 9's
`score`, if it reads the block for the `low_evidence=` count, carries its mapping as Task 9's
OPEN-DECISION. Task 8's `extract` does not call `parse_effort_items`.

**Acceptance Criteria**:
- [ ] AC-T7.1: Every coupled-reason test asserts the full list, e.g. `test_smoke_no_delivery` reads
  exactly `SMOKE: FAIL reason=no_delivery,nongit_root_refused:grok`.
- [ ] AC-T7.2: The two drifted-log tests read exactly
  `SMOKE: FAIL reason=vocab_missing:end,vocab_missing:tool_call,vocab_missing:tool_call_update`, exit 0.
- [ ] AC-T7.3: `grok_log_types` is the only function in the probe that iterates a grok log's lines
  (one definition; step 2, `vocab_missing` and `VOCAB:` call it).
- [ ] AC-T7.4: The smoke test module imports `GROK_MAX_DEPTH` and `_json_deeper_than` from
  `h_mad_review_evidence` and holds no literal `65`.
- [ ] AC-T7.5: The smoke module adds `tests/test_grok_audit_surface_smoke.py` to the spec's `command`
  after the probe module.

**RED split**: 48 nodes; 48 F (no `smoke` handler, no parsers), 0 P.

**Mutation rows** (29; markers 19). Each `replace` makes its condition never fire, except `p-open-input`'s, which
skips the `_OPEN_INPUT` arm so the `--data` value is printed, and except the four
step-3 refusal rows (`p-smoke-effort-codex-text`, `p-smoke-effort-missing`, `p-smoke-effort-empty`,
`p-smoke-effort-unknown`): a wrong-file branch that merely stops firing falls to the
unrecognised-item refusal, which prints the same token, so that mutant is equivalent; these rows
instead turn the refusal into acceptance (the item reaches the reasons, where the `f0_text()` log
fires none, so the token becomes `SMOKE: PASS`). The three-alternative sites (`VOCAB-MISSING` over
`end`, `tool_call`, `tool_call_update`; `ACCEPTS` over grok and agy; `DELIVERED` over `report-file`
and `out`) get one row per alternative, each removing that alternative alone.

| name | marker | test |
|---|---|---|
| `p-smoke-delivered-report-file` | `# M:GAS-SMOKE-DELIVERED` | `tests/test_grok_audit_surface_smoke.py::test_smoke_pass` |
| `p-smoke-delivered-out` | `# M:GAS-SMOKE-DELIVERED` | `tests/test_grok_audit_surface_smoke.py::test_smoke_pass_on_out_delivery` |
| `p-smoke-truncated` | `# M:GAS-SMOKE-TRUNCATED` | `tests/test_grok_audit_surface_smoke.py::test_smoke_truncated` |
| `p-smoke-truncated-m3` | `# M:GAS-SMOKE-TRUNCATED` | `tests/test_grok_audit_surface_smoke.py::test_m3_d1_end_event_beside_truncated_item_is_truncated` |
| `p-smoke-vocab-split` | `# M:GAS-SMOKE-VOCAB-SPLIT` | `tests/test_grok_audit_surface_smoke.py::test_smoke_vocab_split` |
| `p-smoke-vocab-missing-end` | `# M:GAS-SMOKE-VOCAB-MISSING` | `tests/test_grok_audit_surface_smoke.py::test_smoke_vocab_missing_end` |
| `p-smoke-vocab-missing-tool-call` | `# M:GAS-SMOKE-VOCAB-MISSING` | `tests/test_grok_audit_surface_smoke.py::test_smoke_vocab_missing_tool_call` |
| `p-smoke-vocab-missing-tool-call-update` | `# M:GAS-SMOKE-VOCAB-MISSING` | `tests/test_grok_audit_surface_smoke.py::test_smoke_vocab_missing_tool_call_update` |
| `p-smoke-no-delivery` | `# M:GAS-SMOKE-NO-DELIVERY` | `tests/test_grok_audit_surface_smoke.py::test_smoke_no_delivery` |
| `p-smoke-no-delivery-unscorable` | `# M:GAS-SMOKE-NO-DELIVERY` | `tests/test_grok_audit_surface_smoke.py::test_smoke_no_delivery_on_unscorable` |
| `p-smoke-no-delivery-m4` | `# M:GAS-SMOKE-NO-DELIVERY` | `tests/test_grok_audit_surface_smoke.py::test_m4_e1_report_file_inputs_beside_delivered_none_is_no_delivery` |
| `p-smoke-accepts-grok` | `# M:GAS-SMOKE-ACCEPTS` | `tests/test_grok_audit_surface_smoke.py::test_smoke_nongit_root_refused_grok` |
| `p-smoke-accepts-agy` | `# M:GAS-SMOKE-ACCEPTS` | `tests/test_grok_audit_surface_smoke.py::test_smoke_nongit_root_refused_agy` |
| `p-smoke-accepts-m5` | `# M:GAS-SMOKE-ACCEPTS` | `tests/test_grok_audit_surface_smoke.py::test_m5_f1_unverified_token_beside_busy_log_refuses_root` |
| `p-smoke-missing-auditcycle` | `# M:GAS-SMOKE-MISSING-AUDITCYCLE` | `tests/test_grok_audit_surface_smoke.py::test_smoke_input_missing` |
| `p-smoke-missing-collected` | `# M:GAS-SMOKE-MISSING-COLLECTED` | `tests/test_grok_audit_surface_smoke.py::test_smoke_input_missing_delivered_collected_report` |
| `p-smoke-unparseable-auditcycle` | `# M:GAS-SMOKE-UNPARSEABLE-AUDITCYCLE` | `tests/test_grok_audit_surface_smoke.py::test_smoke_input_unparseable` |
| `p-smoke-effort-counts-unparseable` | `# M:GAS-SMOKE-EFFORT-COUNTS` | `tests/test_grok_audit_surface_smoke.py::test_smoke_drifted_log_with_unparseable_item_fails` |
| `p-smoke-effort-counts-parsed` | `# M:GAS-SMOKE-EFFORT-COUNTS` | `tests/test_grok_audit_surface_smoke.py::test_smoke_drifted_log_with_parsed_item_fails` |
| `p-smoke-effort-codex-text` | `# M:GAS-SMOKE-EFFORT-CODEX-TEXT` | `tests/test_grok_audit_surface_smoke.py::test_smoke_effort_codex_text_item_refuses_as_wrong_file` |
| `p-smoke-effort-missing` | `# M:GAS-SMOKE-EFFORT-UNREADABLE` | `tests/test_grok_audit_surface_smoke.py::test_smoke_effort_missing_item_refuses_as_wrong_file` |
| `p-smoke-effort-empty` | `# M:GAS-SMOKE-EFFORT-UNREADABLE` | `tests/test_grok_audit_surface_smoke.py::test_smoke_effort_empty_item_refuses_as_wrong_file` |
| `p-smoke-effort-unknown` | `# M:GAS-SMOKE-EFFORT-UNKNOWN` | `tests/test_grok_audit_surface_smoke.py::test_smoke_unrecognised_effort_item_refuses` |
| `p-parse-auditcycle-one` | `# M:GAS-PARSE-AUDITCYCLE-ONE` | `tests/test_grok_audit_surface_probe.py::test_auditcycle_parser_rejects_two_lines` |
| `p-parse-effort-item` | `# M:GAS-PARSE-EFFORT-ITEM` | `tests/test_grok_audit_surface_probe.py::test_effort_parser_rejects_a_malformed_effort_block` |
| `p-parse-effort-empty` | `# M:GAS-PARSE-EFFORT-EMPTY` | `tests/test_grok_audit_surface_probe.py::test_effort_parser_rejects_a_malformed_effort_block` |
| `p-parse-effort-twice` | `# M:GAS-PARSE-EFFORT-TWICE` | `tests/test_grok_audit_surface_probe.py::test_effort_parser_rejects_a_malformed_effort_block` |
| `p-smoke-effort-malformed` | `# M:GAS-SMOKE-EFFORT-MALFORMED` | `tests/test_grok_audit_surface_smoke.py::test_smoke_refuses_a_malformed_effort_block` |
| `p-open-input` | `# M:GAS-OPEN-INPUT` | `tests/test_grok_audit_surface_smoke.py::test_smoke_last_resort_names_the_open_input` |

**Dependencies on other tasks**: Task 2.

---

## Task 8: extract

**Production file**: `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py` (extend)
**Test files**: `h-mad/tests/test_grok_audit_surface_probe.py` (extend), `h-mad/tests/grokauditfixtures.py` (extend)
**Task shape**: `wiring` — the extractor's counts must come from the gate (`_gate.classify`) and its
grouping decision from `_gate._collapses`; the walk, the blinding, the hints, the stands rule and
`cycle_token` are new behaviour carried in the same Task, and their RED split is stated below.
**WIRE 1**: `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py:extract_report` → `h_mad_audit_gate.classify` (the `must_count` field)
**WIRE-PIN 1**: `h-mad/tests/test_grok_audit_surface_probe.py::test_must_count_mismatch_through_production_path`
**WIRE 2**: `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py:report_findings` → `h_mad_audit_gate._collapses`
**WIRE-PIN 2**: `h-mad/tests/test_grok_audit_surface_probe.py::test_extract_parity_collapsing_group`
**WIRE 3**: `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py:extract_report` → `h_mad_audit_gate.classify` (the `should_count` field)
**WIRE-PIN 3**: `h-mad/tests/test_grok_audit_surface_probe.py::test_should_findings_are_written_on_a_count_difference`

**Description**: `extract` per D12: `extract_all(tree, s2_dir, sources)` (the one function `score`
calls for re-extraction; the design writes `extract_all(tree, s2_dir)`, and the plan adds the parsed
`sources` mapping as a third, required argument for the same D1 reason it adds it to `placements`,
since quote resolution calls `placements`; Task 9's `score` passes its own parsed `sources`), `report_findings(text)` making `_gate`'s own calls in `_section_detail`'s order
(`_payload`, `_is_none_sentinel`, `_bullet_groups`, `_collapses(group, set())` on the line marked
`# M:GAS-COLLAPSE-WIRE`, `_flat_findings`, `_bullet_remainder`, the fail-safe), the section split as
`classify_detail` does it over `_gate.BLOCKING_SECTIONS`, and `extract_report` written as D12's five
lines in that order, with the two marked wire lines. The stands rule, the seven `cycle_token`
triggers (trigger 7 per delivery value), pass → surface from `command.txt`, blinding with
`random.Random(shuffle_seed)`, and `HINT:` lines on stdout only. Quote paths resolve through
`placements` (Task 4).

**Scaffold that makes each WIRE-PIN's RED an assertion about the caller.** At RED the probe from
Task 2 exists and imports `h_mad_audit_gate as _gate` (so every callee resolves), and `MODES` has no
`extract` entry. All three pins drive `main(["extract", …])` in process — WIRE-PIN 1 and 3 after
`monkeypatch.setattr(probe._gate, "classify", fake)` with a `fake` returning the real counts plus one
on the field under test — and assert the last stdout line: WIRE-PIN 1
`FINDINGS: UNREADABLE reason=must_count_mismatch:` plus the report's tree path; WIRE-PIN 2 the
`FINDINGS: WRITTEN` token with `must=1` and `should=1`, equal to `_gate.classify`'s counts on the
same text; WIRE-PIN 3 the exact line `SHOULD-COUNT:` with `walk=` the walk's count and `gate=` one
more, then `FINDINGS: WRITTEN`. At RED each reads `FINDINGS: UNREADABLE reason=internal:KeyError`,
so each fails on its token assertion, never on an import. The parity tests therefore run through
`main(["extract", …])` on a one-report tree, not by importing `extract_report`.

**Wire cuts at GREEN** (the mutation rows): X1 cuts WIRE 1, X4 cuts WIRE 2, X5 cuts WIRE 3; X2, X3,
X6 force them. Each cut must fail its WIRE-PIN with the callee and the tests intact.

**Code structure**:
```python
def report_findings(text: str) -> dict[str, list[str]]: ...  # {"must": [...], "should": [...]}
def extract_report(text: str, report: str) -> tuple[list[str], list[str], int, int]: ...
def stands(doc_dir: Path) -> Path: ...  # the v<N> directory that stands; raises Refusal("cycle_token:...")
def extract_all(tree: Path, s2_dir: Path, sources: dict[str, str]) -> list[dict]: ...
def blind(findings: list[dict], shuffle_seed: int) -> tuple[list[dict], list[dict]]: ...  # (findings rows, key rows)
def hints(findings: list[dict], tree: Path, sources: dict[str, str]) -> list[str]: ...
def _mode_extract(args: argparse.Namespace) -> int: ...
```

**Tests** (33):
- Extraction (12): `test_must_count_mismatch_through_production_path`,
  `test_extract_writes_findings_for_clean_reports`, `test_extract_reads_s2_beside_the_base_tree`,
  `test_should_findings_are_extracted_with_their_section`,
  `test_should_findings_are_written_on_a_count_difference`, `test_extract_parity_nested_label_group`
  (3 and 3), `test_extract_parity_real_parent_none_child_real_child` (2 and 2),
  `test_extract_parity_collapsing_group` (1 and 1), `test_extract_parity_prose_only` (1 and 1),
  `test_findings_carry_no_surface`, `test_hint_resolves_a_live_target_path_to_the_seeded_copy`,
  `test_hint_resolves_a_live_paired_path_to_the_archive`. Each parity fixture places the same shape in
  `## Must-fix` and in `## Should-fix`.
- `cycle_token` (8): `test_cycle_token_no_recorded_line`, `test_cycle_token_unparseable_line`,
  `test_cycle_token_v2_missing_after_unverified_v1`, `test_cycle_token_v2_present_when_v1_not_unverified`,
  `test_cycle_token_v3_present`, `test_cycle_token_unparseable_surfaces`,
  `test_cycle_token_report_file_delivery_without_collected`, `test_cycle_token_out_delivery_without_collected`.
  These are triggers (1)–(7); trigger (8) (spec v1.10, AC-3.8) lands in Task 26, so the
  `cycle_token` fixtures number eight triggers after S0c.
- Stands rule (3): `test_whole_v2_stands_for_every_surface`, `test_undelivered_pass_counts_zero_findings`,
  `test_low_evidence_delivered_report_is_scored`.
- Opposed pairs (10): `test_m1_a1_foreign_line_beside_dispatched_token_does_not_fail`,
  `test_m1_a2_identical_prompts_beside_dispatched_token_does_not_fail`,
  `test_m1_b_report_path_only_beside_divergence_token_fails`,
  `test_m2_c1_pass_asm_beside_halt_token_is_halted`, `test_m2_c2_halt_asm_beside_pass_token_is_not_halted`,
  `test_m4_e1_score_ignores_report_beside_delivered_none`,
  `test_m4_e2a_score_reads_collected_beside_report_file`,
  `test_m4_e2b_score_reads_collected_beside_out`, `test_m5_f1_unverified_token_requires_v2`,
  `test_m5_f2_pass_token_beside_hollow_log_stands`.

12 + 8 + 3 + 10 = 33.

**Acceptance Criteria**:
- [ ] AC-T8.1: The three WIRE-PINs pass, and each fails when only its wire is cut (X1, X4, X5).
- [ ] AC-T8.2: `extract_report` contains D12's five lines verbatim and in order; each marker occurs
  once in the probe (`grep -c` of each of `M:GAS-MUST-COUNT-WIRE`, `M:GAS-SHOULD-COUNT-WIRE`,
  `M:GAS-COLLAPSE-WIRE` prints 1).
- [ ] AC-T8.3: `findings.jsonl` rows carry exactly `id doc cycle section text quotes`; `key.jsonl`
  rows exactly `id doc cycle pass surface report`; `extract.txt` holds the argv with the shuffle seed.
- [ ] AC-T8.4: No file the probe writes contains a `HINT:` line.

**RED split** (stated for the record; the WIRE-PINs, not the split, gate this Task): 33 nodes; 33 F
(no `extract` handler, so every test reads `internal:KeyError` or finds no output files), 0 P.

**Mutation rows** (20; markers 12). The design's X1–X6, verbatim:

| name | find | replace | test |
|---|---|---|---|
| `must-count-severed` (X1) | `must_count = _counts["must_count"]  # M:GAS-MUST-COUNT-WIRE` | `must_count = len(must)  # M:GAS-MUST-COUNT-WIRE` | `tests/test_grok_audit_surface_probe.py::test_must_count_mismatch_through_production_path` |
| `must-count-forced` (X2) | the same | `must_count = _counts["must_count"] + 1  # M:GAS-MUST-COUNT-WIRE` | `tests/test_grok_audit_surface_probe.py::test_extract_writes_findings_for_clean_reports` |
| `collapse-forced` (X3) | the probe line marked `# M:GAS-COLLAPSE-WIRE` | its `_gate._collapses(group, set())` call replaced by `True` | `tests/test_grok_audit_surface_probe.py::test_extract_parity_nested_label_group` |
| `collapse-severed` (X4) | the same | the call replaced by `False` | `tests/test_grok_audit_surface_probe.py::test_extract_parity_collapsing_group` |
| `should-count-severed` (X5) | `should_count = _counts["should_count"]  # M:GAS-SHOULD-COUNT-WIRE` | `should_count = len(should)  # M:GAS-SHOULD-COUNT-WIRE` | `tests/test_grok_audit_surface_probe.py::test_should_findings_are_written_on_a_count_difference` |
| `should-count-forced` (X6) | the same | `should_count = _counts["should_count"] + 1  # M:GAS-SHOULD-COUNT-WIRE` | `tests/test_grok_audit_surface_probe.py::test_should_findings_are_written_on_a_count_difference` |

P-rows (14), each `replace` making its condition never fire except the `DELIVERED` rows, which
remove one delivery value each (`report-file`, `out`) or, for `p-extract-undelivered-m4`, count
`none` as delivered:

| name | marker | test |
|---|---|---|
| `p-cycle-no-line` | `# M:GAS-CYCLE-NO-LINE` | `tests/test_grok_audit_surface_probe.py::test_cycle_token_no_recorded_line` |
| `p-cycle-unparseable` | `# M:GAS-CYCLE-UNPARSEABLE` | `tests/test_grok_audit_surface_probe.py::test_cycle_token_unparseable_line` |
| `p-cycle-v2-missing` | `# M:GAS-CYCLE-V2-MISSING` | `tests/test_grok_audit_surface_probe.py::test_cycle_token_v2_missing_after_unverified_v1` |
| `p-cycle-v2-extra` | `# M:GAS-CYCLE-V2-EXTRA` | `tests/test_grok_audit_surface_probe.py::test_cycle_token_v2_present_when_v1_not_unverified` |
| `p-cycle-v3` | `# M:GAS-CYCLE-V3` | `tests/test_grok_audit_surface_probe.py::test_cycle_token_v3_present` |
| `p-cycle-surfaces` | `# M:GAS-CYCLE-SURFACES` | `tests/test_grok_audit_surface_probe.py::test_cycle_token_unparseable_surfaces` |
| `p-cycle-collected-report-file` | `# M:GAS-CYCLE-COLLECTED` | `tests/test_grok_audit_surface_probe.py::test_cycle_token_report_file_delivery_without_collected` |
| `p-cycle-collected-out` | `# M:GAS-CYCLE-COLLECTED` | `tests/test_grok_audit_surface_probe.py::test_cycle_token_out_delivery_without_collected` |
| `p-stands-m1` | `# M:GAS-STANDS-V1-UNVERIFIED` | `tests/test_grok_audit_surface_probe.py::test_m1_b_report_path_only_beside_divergence_token_fails` |
| `p-stands-m2` | `# M:GAS-STANDS-V1-UNVERIFIED` | `tests/test_grok_audit_surface_probe.py::test_m2_c1_pass_asm_beside_halt_token_is_halted` |
| `p-stands-m5` | `# M:GAS-STANDS-V1-UNVERIFIED` | `tests/test_grok_audit_surface_probe.py::test_m5_f1_unverified_token_requires_v2` |
| `p-extract-undelivered-m4` | `# M:GAS-EXTRACT-DELIVERED` | `tests/test_grok_audit_surface_probe.py::test_m4_e1_score_ignores_report_beside_delivered_none` |
| `p-extract-delivered-report-file` | `# M:GAS-EXTRACT-DELIVERED` | `tests/test_grok_audit_surface_probe.py::test_m4_e2a_score_reads_collected_beside_report_file` |
| `p-extract-delivered-out` | `# M:GAS-EXTRACT-DELIVERED` | `tests/test_grok_audit_surface_probe.py::test_m4_e2b_score_reads_collected_beside_out` |

6 + 14 = 20.

**Dependencies on other tasks**: Tasks 4 (placements) and 7 (`parse_auditcycle`, `delivered`).

---

## Task 9: score

**Production file**: `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py` (extend)
**Test files**: `h-mad/tests/test_grok_audit_surface_probe.py` (extend), `h-mad/tests/grokauditfixtures.py` (extend)
**Task shape**: `new-behaviour`

**Description**: `score` per D13: refusals in D13's order (`ledger_counts`, `ledger_origin`,
`seed_rebuild`, `cycle_token`, re-extracted `must_count_mismatch`, `key_mismatch`, `label:`), the
`key_mismatch` and `label:` triggers each its own guard, per-surface totals over must findings only,
`fab_rate` as `Fraction` with `0/0` read as `Fraction(0)`, `d3` and `verdict(totals)` taking the
per-surface `(hits, n, f, u)` only, the `SURFACE:` lines, the observational `SHOULD:` and `SPLIT:`
lines from a function the verdict never calls, and the `SEEDSCORE:` token. Re-extraction calls
Task 8's `extract_all(tree, tree / "docs/03-analysis/probes/grok-audit-surface/calibration/s2", sources)`, with
`sources` the mapping `score` parsed (D1).

**OPEN-DECISION: where `SURFACE:`'s `low_evidence=` count comes from, and what a `None` from
`parse_effort_items` maps to in `score` (delta review 5f10a1d, should-fix 2 (iv); D13 names the
field but not its source) — resolve in 5d.** Two implementations satisfy it:
- (a) Count the ` low-evidence (` suffix on the scored passes' `Effort:` items through
  `parse_effort_items`, with `None` refusing with AC-5.4's `cycle_token:` reason for that cycle. This extends AC-5.4
  trigger (2) ("a recorded line that does not parse") to the recorded `Effort:` block, so it is owed
  to the spec and design if chosen.
- (b) The same count, with `None` publishing `low_evidence=unreadable` on that surface's
  `SURFACE:` line and never refusing. This needs no AC-5.4 change, because `low_evidence=` never
  moves the verdict (`verdict` takes `(hits, n, f, u)` only).

Either way the Task carries one more test and one more P-row, both counted below:
`test_score_maps_a_malformed_effort_block` (a scored cycle whose collected `auditcycle.txt` holds an
`Effort:` block of Task 7's shape (a); it asserts (a)'s `SEEDSCORE: UNREADABLE` token or (b)'s
`low_evidence=unreadable` field, whichever 5d picks) and row `p-score-effort-malformed`
(`# M:GAS-SCORE-EFFORT-MALFORMED`).

**Code structure**:
```python
def d3(fg: Fraction, rg: int, fa: Fraction, ra: int) -> bool: ...
def verdict(totals: dict[str, tuple[int, int, int, int]]) -> tuple[str, str | None]: ...
def check_key(tree: Path, findings: list[dict], key: list[dict], reextracted: list[dict]) -> None: ...
def check_labels(findings: list[dict], labels: list[dict], ledger: list[dict]) -> dict[str, dict]: ...
def observational_lines(rows: list[dict], ledger: list[dict]) -> list[str]: ...
def score(tree: Path, sources: dict[str, str], calibration: str | None, score_sha: str | None) -> tuple[list[str], str]: ...
def _mode_score(args: argparse.Namespace) -> int: ...
```

**Tests** (32):
- `key_mismatch` (8): `test_key_mismatch_id_sets_differ`, `test_key_mismatch_duplicate_id_in_findings`,
  `test_key_mismatch_duplicate_id_in_key`, `test_key_mismatch_surface_moved_grok_to_agy`,
  `test_key_mismatch_doc_differs`, `test_key_mismatch_cycle_differs`, `test_key_mismatch_report_differs`,
  `test_key_mismatch_reextraction`.
- `label:` (8): `test_label_unlabelled_finding`, `test_label_identical_duplicate`,
  `test_label_conflicting_duplicate`, `test_label_unknown_id`, `test_label_unknown_value`,
  `test_label_undecidable_without_why`, `test_label_hit_unknown_seed`, `test_label_hit_seed_of_other_doc`.
- Verdicts (11): `test_d3_strictly_lower_fab_equal_recall_pass`, `test_d3_equal_fab_greater_recall_pass`,
  `test_d3_full_tie_miss`, `test_d3_equal_fab_lower_recall_miss`,
  `test_d3_unreduced_equal_fab_equal_recall_miss`, `test_undecidable_flips_inconclusive`,
  `test_seeds_undetected_inconclusive`, `test_seeds_undetected_outranks_a_fabrication_pass`,
  `test_seeds_undetected_outranks_a_fabrication_miss`, `test_zero_decidable_musts_prints_0_over_0`,
  `test_score_exit_codes`.
- Observational (3): `test_split_lines_never_move_the_verdict`, `test_should_hits_never_move_the_verdict`,
  `test_should_and_split_lines_are_printed`.
- Hints (1): `test_hints_never_move_the_score`.
- Effort mapping (1, the OPEN-DECISION above): `test_score_maps_a_malformed_effort_block`.

8 + 8 + 11 + 3 + 1 + 1 = 32.

**Acceptance Criteria**:
- [ ] AC-T9.1: Each `key_mismatch` and `label:` test reads its exact `SEEDSCORE: UNREADABLE` token, exit 2.
- [ ] AC-T9.2: Each verdict test reads its exact `SEEDSCORE:` token with `calibration=unstated score=unstated`
  when no shas are given; `test_score_exit_codes` reads exit 0 for PASS, MISS and INCONCLUSIVE and 2
  for UNREADABLE.
- [ ] AC-T9.3: `verdict` takes only the per-surface totals (its signature) and `observational_lines`
  is not called from `verdict` or `d3`.

**RED split**: 32 nodes; 32 F (no `score` handler; `d3` and `verdict` absent), 0 P.

**Mutation rows** (26; markers 21). Each `replace` makes its condition never fire, except: the
`GAS-D3-EQUAL` rows for the full tie and lower recall, which force the recall comparison
(`rg > ra` to `rg >= ra`, and to `rg != ra`); `p-fab-fraction`, which keeps every value a
`Fraction` and shifts the worst-case denominator by one (`Fraction(f + u, n)` to
`Fraction(f + u, n + 1)`, the same on the optimistic side), so the fixture's `1/4` against `2/8`
becomes `1/5` against `2/9`, unequal (measured: `Fraction(1, 5) < Fraction(2, 9)` is true), and the
verdict moves off `MISS`; and `p-verdict-flips`, which returns `MISS` in place of the final
`INCONCLUSIVE`. Residual, stated exactly, for `p-fab-fraction`: `Fraction` normalises on
construction (measured: `Fraction(2, 8)` is `1/4`), so no `Fraction`-preserving mutant can make the
two sides differ in representation alone. The row therefore shows the test can fail at this
fixture's tie boundary. That a non-`Fraction` comparison (a string or an unreduced pair) would also
fail it is pinned by the test's construction, not by a row, because the only mutants that reach it
change the value's type, which the P-row rule forbids.
Reproduce both `Fraction` readings:

```bash
/opt/anaconda3/bin/python3.11 -c 'from fractions import Fraction as F; print(F(1,5) < F(2,9), F(2,8), F(1,4) == F(2,8))'
# True 1/4 True
```

`test_zero_decidable_musts_prints_0_over_0` and `test_score_exit_codes` are format and
exit contracts over guards rowed here, and the three observational tests and the hint test are
invariance tests; none of them gets a row.

| name | marker | test |
|---|---|---|
| `p-key-id-sets` | `# M:GAS-KEY-ID-SETS` | `tests/test_grok_audit_surface_probe.py::test_key_mismatch_id_sets_differ` |
| `p-key-dup-findings` | `# M:GAS-KEY-DUP-FINDINGS` | `tests/test_grok_audit_surface_probe.py::test_key_mismatch_duplicate_id_in_findings` |
| `p-key-dup-key` | `# M:GAS-KEY-DUP-KEY` | `tests/test_grok_audit_surface_probe.py::test_key_mismatch_duplicate_id_in_key` |
| `p-key-surface` | `# M:GAS-KEY-SURFACE` | `tests/test_grok_audit_surface_probe.py::test_key_mismatch_surface_moved_grok_to_agy` |
| `p-key-doc` | `# M:GAS-KEY-DOC` | `tests/test_grok_audit_surface_probe.py::test_key_mismatch_doc_differs` |
| `p-key-cycle` | `# M:GAS-KEY-CYCLE` | `tests/test_grok_audit_surface_probe.py::test_key_mismatch_cycle_differs` |
| `p-key-report` | `# M:GAS-KEY-REPORT` | `tests/test_grok_audit_surface_probe.py::test_key_mismatch_report_differs` |
| `p-key-reextract` | `# M:GAS-KEY-REEXTRACT` | `tests/test_grok_audit_surface_probe.py::test_key_mismatch_reextraction` |
| `p-label-missing` | `# M:GAS-LABEL-MISSING` | `tests/test_grok_audit_surface_probe.py::test_label_unlabelled_finding` |
| `p-label-dup-identical` | `# M:GAS-LABEL-DUP` | `tests/test_grok_audit_surface_probe.py::test_label_identical_duplicate` |
| `p-label-dup-conflicting` | `# M:GAS-LABEL-DUP` | `tests/test_grok_audit_surface_probe.py::test_label_conflicting_duplicate` |
| `p-label-unknown-id` | `# M:GAS-LABEL-UNKNOWN-ID` | `tests/test_grok_audit_surface_probe.py::test_label_unknown_id` |
| `p-label-value` | `# M:GAS-LABEL-VALUE` | `tests/test_grok_audit_surface_probe.py::test_label_unknown_value` |
| `p-label-why` | `# M:GAS-LABEL-WHY` | `tests/test_grok_audit_surface_probe.py::test_label_undecidable_without_why` |
| `p-label-seed-unknown` | `# M:GAS-LABEL-SEED-UNKNOWN` | `tests/test_grok_audit_surface_probe.py::test_label_hit_unknown_seed` |
| `p-label-seed-doc` | `# M:GAS-LABEL-SEED-DOC` | `tests/test_grok_audit_surface_probe.py::test_label_hit_seed_of_other_doc` |
| `p-d3-lower` | `# M:GAS-D3-LOWER` | `tests/test_grok_audit_surface_probe.py::test_d3_strictly_lower_fab_equal_recall_pass` |
| `p-d3-equal-greater` | `# M:GAS-D3-EQUAL` | `tests/test_grok_audit_surface_probe.py::test_d3_equal_fab_greater_recall_pass` |
| `p-d3-equal-tie` | `# M:GAS-D3-EQUAL` | `tests/test_grok_audit_surface_probe.py::test_d3_full_tie_miss` |
| `p-d3-equal-lower` | `# M:GAS-D3-EQUAL` | `tests/test_grok_audit_surface_probe.py::test_d3_equal_fab_lower_recall_miss` |
| `p-fab-fraction` | `# M:GAS-FAB-FRACTION` | `tests/test_grok_audit_surface_probe.py::test_d3_unreduced_equal_fab_equal_recall_miss` |
| `p-verdict-flips` | `# M:GAS-VERDICT-FLIPS` | `tests/test_grok_audit_surface_probe.py::test_undecidable_flips_inconclusive` |
| `p-verdict-undetected` | `# M:GAS-VERDICT-UNDETECTED` | `tests/test_grok_audit_surface_probe.py::test_seeds_undetected_inconclusive` |
| `p-verdict-undetected-pass` | `# M:GAS-VERDICT-UNDETECTED` | `tests/test_grok_audit_surface_probe.py::test_seeds_undetected_outranks_a_fabrication_pass` |
| `p-verdict-undetected-miss` | `# M:GAS-VERDICT-UNDETECTED` | `tests/test_grok_audit_surface_probe.py::test_seeds_undetected_outranks_a_fabrication_miss` |
| `p-score-effort-malformed` | `# M:GAS-SCORE-EFFORT-MALFORMED` | `tests/test_grok_audit_surface_probe.py::test_score_maps_a_malformed_effort_block` |

8 + 8 + 9 + 1 = 26.

**Dependencies on other tasks**: Task 8.

---

## Task 10: main-leak, rescore, the calibration-data set, the grammar sweeps

**Production file**: `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py` (extend)
**Test files**: `h-mad/tests/test_grok_audit_surface_probe.py` (extend), `h-mad/tests/grokauditfixtures.py` (extend)
**Task shape**: `new-behaviour`

**Description**: `calibration_data_files(tree)` per D3 (the six named candidates excluded only when
they carry none of (a), (b), (c), with (c)'s needles from Task 8's `report_findings` per line). D9's
ref and sha checks, drift check, main leak check (triggers i–iii over `git ls-tree -r -z HEAD` read
through `git cat-file --batch`), `main-leak`, and `rescore`'s eight steps in AC-6.4's order, ending
in a `finally` that removes and re-lists every temporary directory. **`parse_root_line`'s `None`
(Task 4) maps here to `list_changed:unrecorded`** (`# M:GAS-LIST-MALFORMED`): a recorded `root.txt`
whose `ROOT: READY` line lacks a D2 field is treated like an absent record. The spec defines
`unrecorded` as "a root record that is absent", so extending it to a malformed record is a plan
extension, owed to the spec and design. The three D2 grammar sweeps land
here because they need all nine handlers.

**Code structure**:
```python
def calibration_data_files(tree: Path) -> list[str]: ...
def ref_checks(repo: Path, remote: str, shas: list[str]) -> str: ...  # the fetched tip
def drift_check(repo: Path, calibration: str, later: str) -> None: ...
def main_leak(repo: Path, data_sha: str, sources: dict[str, str]) -> tuple[str, str, int]: ...  # (HEAD sha40, data sha40, blobs)
def list_check(export: Path, repo: Path) -> str: ...  # the LIST: line
def rescore(args: argparse.Namespace) -> tuple[list[str], str]: ...
def _mode_main_leak(args: argparse.Namespace) -> int: ...
def _mode_rescore(args: argparse.Namespace) -> int: ...
```

**Tests** (31 functions, 44 node ids):
- Calibration-data set (4): `test_calibration_data_set_is_the_directory_minus_the_metadata_names`
  (built at S0 as `…_minus_six_named_files`; renamed and extended to design v1.11's metadata names by
  Task 26),
  `test_calibration_data_set_keeps_an_excluded_name_carrying_a_finding_text`,
  `test_calibration_data_set_keeps_an_excluded_name_carrying_a_seeded_span`,
  `test_calibration_data_set_keeps_an_excluded_name_carrying_an_expected_sentence`.
- Drift (6): `test_drift_outside_calibration_dir`, `test_drift_not_descendant`,
  `test_drift_score_not_descendant_of_smoke_commit`, `test_drift_seeded_copy_changed_at_score_sha`,
  `test_drift_ledger_changed_at_smoke_commit`, `test_drift_ledger_absent_at_score_sha`.
- Main leak (9): `test_main_leak_trigger_i_byte_equal_copy`,
  `test_main_leak_trigger_i_on_a_captured_wrapper_stdout`,
  `test_main_leak_trigger_i_smoke_commit_without_score_sha`,
  `test_main_leak_trigger_i_on_an_excluded_name_carrying_a_finding_text`,
  `test_main_leak_trigger_ii_expected`, `test_main_leak_trigger_iii_seeded_span`, the must-not-refuse
  `test_seeded_span_also_in_its_own_archive_source_does_not_refuse` and
  `test_main_leak_ignores_a_main_blob_equal_to_wall_seconds`, and `test_main_leak_prints_the_scanned_commit`.
- Ref (4): `test_ref_fetch_failed_no_remote`, `test_ref_absent`, `test_ref_sha_unknown`, `test_ref_not_on_ref`.
- List (3): `test_list_changed_recorded_blob_differs`, `test_list_changed_unrecorded_root_record`,
  `test_list_changed_malformed_root_record` (plan-added: one cycle's `root.txt` holds a `ROOT: READY`
  line without `list_blob=`; `SEEDSCORE: UNREADABLE reason=list_changed:unrecorded`).
- End to end (2): `test_main_leak_mode_clean_on_a_smoke_failure_branch`,
  `test_rescore_reproduces_the_score_and_removes_its_temp_dirs`.
- Grammar sweeps (3 functions, 16 ids): `test_success_token_shape_per_mode` (9 ids, one per D2 mode),
  `test_no_published_line_uses_another_modes_prefix` (1), `test_sources_override_reaches_every_ledger_mode`
  (6 ids: `check-ledger`, `build-root`, `extract`, `score`, `rescore`, `main-leak`).

4 + 6 + 9 + 4 + 3 + 2 = 28 functions with one id each, plus 9 + 1 + 6 = 16: 44 ids.

**Acceptance Criteria**:
- [ ] AC-T10.1: Every refusal test reads its exact `MAINLEAK: UNREADABLE` or `SEEDSCORE: UNREADABLE`
  token, exit 2, built on `tmp_path/work` with `tmp_path/origin.git` as `origin`.
- [ ] AC-T10.2: `test_rescore_reproduces_the_score_and_removes_its_temp_dirs` reads the same
  `SEEDSCORE:` line as `score --tree` on the same export, the published `SCANNED:` and `LIST:` lines,
  and finds none of the probe's `mkdtemp` directories after the run.
- [ ] AC-T10.3: `calibration_data_files` is the only definition of the set; `main_leak` and the four
  calibration-set tests call it.
- [ ] AC-T10.4: The spec's `command` is unchanged by this Task (no new test file).

**RED split**: 44 ids; 33 F, 11 P. F: the 28 single-id functions (the two modes are absent, and
`calibration_data_files` is absent); `test_success_token_shape_per_mode[rescore]` and `[main-leak]`;
`test_no_published_line_uses_another_modes_prefix` (it runs every mode);
`test_sources_override_reaches_every_ledger_mode[rescore]` and `[main-leak]`. P (regression guards on
modes Tasks 3–9 built): `test_success_token_shape_per_mode` for `check-ledger`, `build-root`,
`record-cycle`, `commit-data`, `smoke`, `extract`, `score` (7), and
`test_sources_override_reaches_every_ledger_mode` for `check-ledger`, `build-root`, `extract`,
`score` (4). 28 + 2 + 1 + 2 = 33; 7 + 4 = 11.

**Mutation rows** (22; markers 18), each `replace` making its condition never fire (for
`p-list-malformed`: a malformed record is skipped instead of refused, so the run goes on to score):

| name | marker | test |
|---|---|---|
| `p-calset-finding` | `# M:GAS-CALSET-FINDING` | `tests/test_grok_audit_surface_probe.py::test_calibration_data_set_keeps_an_excluded_name_carrying_a_finding_text` |
| `p-calset-seeded` | `# M:GAS-CALSET-SEEDED` | `tests/test_grok_audit_surface_probe.py::test_calibration_data_set_keeps_an_excluded_name_carrying_a_seeded_span` |
| `p-calset-expected` | `# M:GAS-CALSET-EXPECTED` | `tests/test_grok_audit_surface_probe.py::test_calibration_data_set_keeps_an_excluded_name_carrying_an_expected_sentence` |
| `p-drift-path` | `# M:GAS-DRIFT-PATH` | `tests/test_grok_audit_surface_probe.py::test_drift_outside_calibration_dir` |
| `p-drift-ancestor` | `# M:GAS-DRIFT-ANCESTOR` | `tests/test_grok_audit_surface_probe.py::test_drift_not_descendant` |
| `p-drift-smoke-ancestor` | `# M:GAS-DRIFT-SMOKE-ANCESTOR` | `tests/test_grok_audit_surface_probe.py::test_drift_score_not_descendant_of_smoke_commit` |
| `p-drift-blob-seeded` | `# M:GAS-DRIFT-BLOB` | `tests/test_grok_audit_surface_probe.py::test_drift_seeded_copy_changed_at_score_sha` |
| `p-drift-blob-ledger` | `# M:GAS-DRIFT-BLOB` | `tests/test_grok_audit_surface_probe.py::test_drift_ledger_changed_at_smoke_commit` |
| `p-drift-absent` | `# M:GAS-DRIFT-ABSENT` | `tests/test_grok_audit_surface_probe.py::test_drift_ledger_absent_at_score_sha` |
| `p-mainleak-i-copy` | `# M:GAS-MAINLEAK-I` | `tests/test_grok_audit_surface_probe.py::test_main_leak_trigger_i_byte_equal_copy` |
| `p-mainleak-i-stdout` | `# M:GAS-MAINLEAK-I` | `tests/test_grok_audit_surface_probe.py::test_main_leak_trigger_i_on_a_captured_wrapper_stdout` |
| `p-mainleak-i-smoke` | `# M:GAS-MAINLEAK-I` | `tests/test_grok_audit_surface_probe.py::test_main_leak_trigger_i_smoke_commit_without_score_sha` |
| `p-mainleak-i-finding` | `# M:GAS-MAINLEAK-I` | `tests/test_grok_audit_surface_probe.py::test_main_leak_trigger_i_on_an_excluded_name_carrying_a_finding_text` |
| `p-mainleak-ii` | `# M:GAS-MAINLEAK-II` | `tests/test_grok_audit_surface_probe.py::test_main_leak_trigger_ii_expected` |
| `p-mainleak-iii` | `# M:GAS-MAINLEAK-III` | `tests/test_grok_audit_surface_probe.py::test_main_leak_trigger_iii_seeded_span` |
| `p-ref-fetch` | `# M:GAS-REF-FETCH` | `tests/test_grok_audit_surface_probe.py::test_ref_fetch_failed_no_remote` |
| `p-ref-absent` | `# M:GAS-REF-ABSENT` | `tests/test_grok_audit_surface_probe.py::test_ref_absent` |
| `p-ref-sha-unknown` | `# M:GAS-REF-SHA-UNKNOWN` | `tests/test_grok_audit_surface_probe.py::test_ref_sha_unknown` |
| `p-ref-not-on-ref` | `# M:GAS-REF-NOT-ON-REF` | `tests/test_grok_audit_surface_probe.py::test_ref_not_on_ref` |
| `p-list-changed` | `# M:GAS-LIST-CHANGED` | `tests/test_grok_audit_surface_probe.py::test_list_changed_recorded_blob_differs` |
| `p-list-unrecorded` | `# M:GAS-LIST-UNRECORDED` | `tests/test_grok_audit_surface_probe.py::test_list_changed_unrecorded_root_record` |
| `p-list-malformed` | `# M:GAS-LIST-MALFORMED` | `tests/test_grok_audit_surface_probe.py::test_list_changed_malformed_root_record` |

3 + 6 + 6 + 4 + 3 = 22.

**Dependencies on other tasks**: Tasks 6 (`commit-data` builds the fixture branch commits), 8, 9.

---

## Task 11: the identical-prompts stub knob

**Production file**: `h-mad/tests/test_hmad_dispatch_audit_cycle.py` (modify `install_audit_cycle_stubs` only)
**Test file**: `h-mad/tests/test_grok_audit_surface_wrapper.py` (create)
**Task shape**: `new-behaviour`

**Description**: The test-only knob the design's Components table names. In the stub
`h_mad_assemble_audit.py` that `install_audit_cycle_stubs` writes, `HMAD_ASSEMBLE_SAME_REPORT_P<i>=1`
writes the constant `Report path: SAME` in place of both report-path lines of that pass's prompt (the
stub writes the path twice, `Head contract report path:` and `Report path:`), so two passes can
assemble byte-identical prompts and `_cmd_audit_cycle`'s empty-diff branch
(`if [ -z "$div" ] || [ "$foreign" -ne 0 ]; then`) halts them. Unset, the stub's output is
byte-for-byte what it is at `30917a1a`. No other helper changes.

**Tests** (1): `test_identical_prompts_halt_prompt_divergence` — with `HMAD_ASSEMBLE_SAME_REPORT_P1=1`
and `HMAD_ASSEMBLE_SAME_REPORT_P2=1`, the `AUDITCYCLE:` lines are exactly
`["AUDITCYCLE: UNVERIFIED reason=prompt_divergence passes=2 size_status=verified"]` and zero agents are
dispatched (the capture file's dispatch count is 0), using `project_with_docs`, `dispatch_args`,
`run_audit_cycle` and `install_audit_cycle_stubs` imported from `test_hmad_dispatch_audit_cycle`.

**Acceptance Criteria**:
- [ ] AC-T11.1: The test passes; every existing test in `h-mad/tests/test_hmad_dispatch_audit_cycle.py`
  passes unchanged (regression guard).
- [ ] AC-T11.2: The spec's `command` gains `tests/test_grok_audit_surface_wrapper.py` and
  `tests/test_hmad_dispatch_audit_cycle.py` at their design positions.

**RED split**: 1 node; 1 F (without the knob the two prompts differ on their report-path lines only,
the wrapper's check passes them, and the cycle dispatches). Regression guards: all of
`h-mad/tests/test_hmad_dispatch_audit_cycle.py`.

**Mutation rows** (2), the design's:

| name | file | find | replace | test |
|---|---|---|---|---|
| `divergence-empty-branch-dropped` (W7) | `scripts/hmad-dispatch.sh` | `␣␣␣␣if [ -z "$div" ] \|\| [ "$foreign" -ne 0 ]; then` | `␣␣␣␣if [ "$foreign" -ne 0 ]; then` | `tests/test_grok_audit_surface_wrapper.py::test_identical_prompts_halt_prompt_divergence` |
| `divergence-foreign-branch-dropped` (W8) | `scripts/hmad-dispatch.sh` | the same | `␣␣␣␣if [ -z "$div" ]; then` | `tests/test_hmad_dispatch_audit_cycle.py::test_verb_prompt_divergence` |

`␣` is one space (four leading spaces); the table cell escapes the two `|` of `||`.

**Dependencies on other tasks**: Task 2 (the spec file).

---

## Task 12: pins over unchanged code

**Production files**: none (the gate, the cycle helper and the wrapper are pinned, not edited)
**Test files**: `h-mad/tests/test_grok_audit_surface_gate_pins.py` (create),
`h-mad/tests/test_grok_audit_surface_wrapper.py` (extend)
**Task shape**: `new-behaviour` — tests over existing behaviour; each is expected to pass at RED, and
its ability to fail is shown only by its mutation row (design §"Test Strategy").

**Description**: FR-8 through `combine` over `pass_result` indices 1–3 (`audit_cycle()` and
`pass_result` from `test_h_mad_audit_cycle`; p3 efforts from `grokfixtures.f0_text` and `f_trunc`);
FR-9 through the gate CLI (`--exit-check`, and `--round-cap 2` with the cap first, as `main` parses
it) over stamps named `gas-fx.design.audit.v<N>.p<i>.md.gated.json`, written with `verdict`, `suite`
and `legs` the way `test_h_mad_audit_leg_set_gate.py`'s `_stamp` methods write them; FR-10 and
AC-7.2's stamp claim through `run_with_cmd_exec_stub` / `_dispatch_artifacts_by_pass` and
`run_audit_cycle` with `_BINDIR` (a bin dir holding the `STUBS` `codex`, `agy`, `grok` stubs and `jq`),
`HMAD_AUDIT_CYCLE_SCRIPT_DIR` from `_script_dir_with_stub_assemble_and_real_cycle(tmp_path)`, and
`HMAD_STUB_AGY_RESP` / `HMAD_STUB_CODEX_LAST` from `_audit_response(...)`; and the D10 M1/M2 authority
test, which drives the real `_cmd_audit_cycle` through `install_audit_cycle_stubs` and
`run_audit_cycle` on the three M1 shapes (a foreign line via `HMAD_ASSEMBLE_DIVERGE_P2`; identical
prompts via Task 11's knob; report-path-only differences, the default) and on an `ASSEMBLE: HALT`
shape (`HMAD_ASSEMBLE_HALT_P2`), asserting the wrapper's own verdicts.

**Tests** (14):
- Gate pins (8): `test_union_three_passes_only_grok_must_fails`, `test_union_three_passes_all_clean_pass`,
  `test_floor_low_evidence_at_index_3`, `test_floor_truncated_at_index_3`,
  `test_exit_three_leg_first_gate_then_codex_blocks_legs_changed`, `test_exit_two_codex_revisions_ready`,
  `test_round_cap_first_gate_counts_one_cycle`, `test_exit_mixed_first_gate_legs_disagree`.
- Wrapper pins (6): `test_three_surfaces_map_pass_index_to_agent`,
  `test_three_surfaces_print_no_repeated_warning`, `test_three_surface_stamps_carry_sorted_legs`
  (asserts exactly the two stamps `….p1.md.gated.json` and `….p2.md.gated.json`, each with
  `"legs": ["agy", "codex", "grok"]`), `test_codex_agy_cycle_stamps_carry_the_legs_that_ran` (both
  stamps `"legs": ["agy", "codex"]`), `test_two_surfaces_for_three_passes_exit_2`,
  `test_m1_m2_raw_shapes_are_what_the_wrapper_says`.

**Acceptance Criteria**:
- [ ] AC-T12.1: All 14 pass; no file under `h-mad/scripts/` changes (`git diff --quiet -- h-mad/scripts`).
- [ ] AC-T12.2: Every one of the 13 tests other than `test_m1_m2_raw_shapes_are_what_the_wrapper_says`
  is the `test` of at least one row below, and the 17 rows are all caught.
- [ ] AC-T12.3: The spec's `command` gains `tests/test_grok_audit_surface_gate_pins.py`.

**RED split**: 14 nodes; 0 F, 14 P (all regression guards over unchanged code). An F here falsifies
the design's "unchanged code" premise for that property: the Task stops and reports it, and no
production file is edited to make it pass.

**Mutation rows** (17), the design's, verbatim (`␣` is one space; `\|` in a cell is a literal `|`):

| name | file | find | replace | test |
|---|---|---|---|---|
| `surf-map-rotate` (W1) | `scripts/hmad-dispatch.sh` | `agent[$i]="${_surf[$((i - 1))]}"` | `agent[$i]="${_surf[$((i % passes))]}"` | `tests/test_grok_audit_surface_wrapper.py::test_three_surfaces_map_pass_index_to_agent` |
| `surf-map-fixed` (W2) | `scripts/hmad-dispatch.sh` | the same | `agent[$i]="grok"` | `tests/test_grok_audit_surface_wrapper.py::test_three_surfaces_map_pass_index_to_agent` |
| `surf-map-fixed-warns` (W3) | `scripts/hmad-dispatch.sh` | the same | `agent[$i]="grok"` | `tests/test_grok_audit_surface_wrapper.py::test_three_surfaces_print_no_repeated_warning` |
| `legs-default-dropped` (W4) | `scripts/hmad-dispatch.sh` | `␣␣␣␣legs=("${_surf[@]}")` | `␣␣␣␣legs=()` | `tests/test_grok_audit_surface_wrapper.py::test_three_surface_stamps_carry_sorted_legs` |
| `legs-default-fixed` (W5) | `scripts/hmad-dispatch.sh` | the same | `␣␣␣␣legs=(codex)` | `tests/test_grok_audit_surface_wrapper.py::test_three_surface_stamps_carry_sorted_legs` |
| `surfaces-count-check-dropped` (W6) | `scripts/hmad-dispatch.sh` | `␣␣␣␣[ "${#_surf[@]}" -eq "$passes" ] \|\| {` | `␣␣␣␣true \|\| {` | `tests/test_grok_audit_surface_wrapper.py::test_two_surfaces_for_three_passes_exit_2` |
| `legs-default-dropped-two-surface` (W9) | `scripts/hmad-dispatch.sh` | W4's find | `␣␣␣␣legs=()` | `tests/test_grok_audit_surface_wrapper.py::test_codex_agy_cycle_stamps_carry_the_legs_that_ran` |
| `legs-default-fixed-two-surface` (W10) | `scripts/hmad-dispatch.sh` | W5's find | `␣␣␣␣legs=(codex)` | `tests/test_grok_audit_surface_wrapper.py::test_codex_agy_cycle_stamps_carry_the_legs_that_ran` |
| `leg-key-input-order` (G1) | `scripts/h_mad_audit_gate.py` | `␣␣␣␣return sorted({str(name).strip() for name in legs if str(name).strip()})` | `␣␣␣␣return list(dict.fromkeys(str(name).strip() for name in legs if str(name).strip()))` | `tests/test_grok_audit_surface_wrapper.py::test_three_surface_stamps_carry_sorted_legs` |
| `legs-changed-dropped` (G2) | `scripts/h_mad_audit_gate.py` | `␣␣␣␣␣␣␣␣if first != second:` | `␣␣␣␣␣␣␣␣if False:` | `tests/test_grok_audit_surface_gate_pins.py::test_exit_three_leg_first_gate_then_codex_blocks_legs_changed` |
| `legs-disagree-dropped` (G3) | `scripts/h_mad_audit_gate.py` | `␣␣␣␣␣␣␣␣if len(distinct) > 1:` | `␣␣␣␣␣␣␣␣if False:` | `tests/test_grok_audit_surface_gate_pins.py::test_exit_mixed_first_gate_legs_disagree` |
| `legs-disagree-always` (G4) | `scripts/h_mad_audit_gate.py` | the same | `␣␣␣␣␣␣␣␣if True:` | `tests/test_grok_audit_surface_gate_pins.py::test_exit_two_codex_revisions_ready` |
| `round-counts-stamps` (G5) | `scripts/h_mad_audit_gate.py` | `␣␣␣␣␣␣␣␣grouped.add(key)` | `␣␣␣␣␣␣␣␣grouped.add((key[0], key[1], (key[2], path.name)))` | `tests/test_grok_audit_surface_gate_pins.py::test_round_cap_first_gate_counts_one_cycle` |
| `union-drops-p3` (C1) | `scripts/h_mad_audit_cycle.py` | `␣␣␣␣␣␣␣␣if result.verdict == "FAIL":` | `␣␣␣␣␣␣␣␣if result.verdict == "FAIL" and result.index != 3:` | `tests/test_grok_audit_surface_gate_pins.py::test_union_three_passes_only_grok_must_fails` |
| `floor-skips-last-pass` (C2) | `scripts/h_mad_audit_cycle.py` | `␣␣␣␣␣␣␣␣if result.effort is None:` | `␣␣␣␣␣␣␣␣if result.effort is None or result.index == len(results):` | `tests/test_grok_audit_surface_gate_pins.py::test_floor_low_evidence_at_index_3` |
| `floor-skips-last-pass-truncated` (C3) | `scripts/h_mad_audit_cycle.py` | the same | the same as C2 | `tests/test_grok_audit_surface_gate_pins.py::test_floor_truncated_at_index_3` |
| `union-always-fails` (C4) | `scripts/h_mad_audit_cycle.py` | C1's find | `␣␣␣␣␣␣␣␣if True:` | `tests/test_grok_audit_surface_gate_pins.py::test_union_three_passes_all_clean_pass` |

Each find was re-counted at `30917a1a` with `grep -cF` in its file: 1 matching line each.

**Dependencies on other tasks**: Task 11 (the knob for the M1 identical-prompts shape; the wrapper
module).

---

## Task 13: SKILL.md S0 text

**Production file**: `h-mad/SKILL.md`
**Test file**: `h-mad/tests/test_grok_audit_surface_docs.py` (extend)
**Task shape**: `new-behaviour`

**Description**: D14's two S0 edits. AC-6.2a: in §"Teammate audit leg — when codex is unavailable",
the code span `h_mad_audit_cycle.py --surfaces agy,grok` becomes
`hmad-dispatch audit-cycle --feature <feature> --phase <phase> --cycle <N> --project-root <root> --passes 2 --surfaces agy,grok`,
and nothing else in that section changes. AC-9.5: this sentence is appended to the §"What you NEVER do"
bullet that starts "**Name the reviewer legs with `--legs`…**": "The first gate and the revisions run
different leg sets by design, so the streak, when it is reached, is among revision cycles." The RED
run of `test_no_h_mad_md_pairs_audit_cycle_py_with_surfaces` against the uncorrected SKILL.md is
recorded first: its pytest summary line is quoted in the RED report and in the RED commit's message.
Doc tests read sections with `titled_section` and collapse each whitespace run to one space.

**Tests** (3): `test_teammate_section_names_hmad_dispatch_audit_cycle`,
`test_no_h_mad_md_pairs_audit_cycle_py_with_surfaces` (scans `git ls-files -z 'h-mad/*.md'` with
`h_mad_audit_cycle\.py[^\n]*\n?[^\n]*--surfaces`; 0 occurrences after the edit),
`test_never_do_legs_bullet_states_the_first_gate_leg_set`.

**Acceptance Criteria**:
- [ ] AC-T13.1: The three tests pass; `tests/test_grok_fallback_docs.py` passes unchanged (its
  teammate test still finds `--surfaces agy,grok` and `unmeasured`, each once in the section at
  `30917a1a`).
- [ ] AC-T13.2: The teammate section's diff is that one code span; the §"What you NEVER do" diff is
  that one appended sentence.
- [ ] AC-T13.3: The spec's `command` gains `tests/test_grok_fallback_docs.py`, completing the design's
  seven-file list.

**RED split**: 3 nodes; 3 F, 0 P. Regression guards: `h-mad/tests/test_grok_fallback_docs.py`.

**Mutation rows** (3), the design's:

| name | file | find | replace | test |
|---|---|---|---|---|
| `teammate-surfaces-pin` (K1) | `SKILL.md` | `--project-root <root> --passes 2 --surfaces agy,grok` | `--project-root <root> --passes 2 --surfaces agy,codex` | `tests/test_grok_fallback_docs.py::test_teammate_section_documents_the_grok_leg` |
| `teammate-unmeasured-pin` (K2) | `SKILL.md` | `audit precision remain **unmeasured** (D4)` | `audit precision remain **measured** (D4)` | `tests/test_grok_fallback_docs.py::test_teammate_section_documents_the_grok_leg` |
| `never-gate-surfaces-pin` (K3) | `SKILL.md` | ``When Codex is unavailable and `fallback_agent=grok`, use `--surfaces agy,grok` `` | the same with `--surfaces agy,codex` | `tests/test_grok_fallback_docs.py::test_never_gate_section_cross_references_the_grok_leg` |

K2 and K3's finds occur once in `h-mad/SKILL.md` at `30917a1a`; K1's find is written by this Task
(0 occurrences before it, 1 after).

**Dependencies on other tasks**: Task 1 (the docs module), Task 2 (the spec).

---

## Task 14: Phase 5e verdict

**Production files**: none
**Test files**: none
**Task shape**: `gate` — reads verdicts over what Tasks 1–13 built; writes no production file.

**Description**: One run over the whole spec and the closing checks the design names.

```bash
rtk proxy /opt/anaconda3/bin/python3.11 -m pytest --version
rtk proxy /opt/anaconda3/bin/python3.11 -m pytest h-mad/tests -q -p no:cacheprovider
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/grok_audit_surface.json
python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/grok_audit_surface.json
git ls-files 'h-mad/tests/*' | grep -E '\.(plan|design|impl-plan|spec)\.md$'
grep -c 'M:GAS-' docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py
/opt/anaconda3/bin/python3.11 -c 'import json; print(len(json.load(open("h-mad/tests/mutation-specs/grok_audit_surface.json"))["mutations"]))'
```

**Acceptance Criteria**:
- [ ] AC-T14.1: The first command prints a pytest version; the full suite's summary line shows no failure.
- [ ] AC-T14.2: `MUTATION: ALL_CAUGHT` with `untargeted=0/180` and `crash_kills=0`, and
  `ANCHORS: ANCHORS_OK`, read from the token lines.
- [ ] AC-T14.3: The `git ls-files` line prints nothing (the zero holds because every synthetic phase
  document is written under `tmp_path`; it was 0 files at `30917a1a`).
- [ ] AC-T14.4 (carry 11): the marker-site count (matching lines) and the row count (rows) are
  re-derived by the last two commands at this Task's sha and reported with their units. This plan
  expects 125 and 180; a different figure is reported against this plan with the Task whose table
  it contradicts, never silently accepted.

**Dependencies on other tasks**: Tasks 1–13.

---

## Tasks 14a–14d: the AC-3.9 path-scope clause and the assembler pin (design D21)

These four Tasks answer design v1.14 (`8fd0f637`; D21 as revised from v1.13 `8a27d264`, and its edits
to D2, D8, D15, D17, D18, D20) and spec v1.20 (`d78cca8d`: AC-3.9 tests (1)–(6), AC-3.6's assembler
commit). They gate run 3 of Task 15 (design "Implementation Order" item 12), so they sit before it.
They are numbered 14a–14d rather than 15–18 because renumbering would move every cross-reference
to Tasks 15–30, which earlier Tasks, the audit reports and the S0c notes cite by number. They run on
a branch Phase 5c names (this plan proposes `feature/218c-path-scope`), cut from `main` after the
S0c merge.

Every `path:symbol`, line, anchor and count below was read at `8fd0f637`, where `h-mad/` is
byte-identical to `d9f25dc2` (`git diff --stat d9f25dc2 8fd0f637 -- h-mad` prints nothing).

**Phase 5 constraints these Tasks encode** (`docs/03-analysis/grok-audit-surface.phase5-s0c-notes.md`):
- Codex authors Phase 5, and its source reads are refused, so every edit to an existing file is
  given below as an exact old text and its new text. Each old text is stated with the unit that
  makes it unique: `-cF` (substring, matching lines), `-cxF` (whole line), or a multi-line pair whose
  lines are unique together. Each such count was run at `8fd0f637` and is 1 unless stated.
- The TDD judge runs the mapped test file with `-x` inside `JUDGE_BUDGET_S = 40`
  (`h-mad/scripts/h_mad_tdd_judge.py:29`). `h-mad/tests/test_grok_audit_surface_containment.py` is
  already over it (85 passed in 41.33 s on this Mac, 40.51 s in the audit's run, about 70 s under
  load per the notes), so no Task here adds a test to it. The new tests go in two new modules,
  `h-mad/tests/test_grok_audit_surface_path_scope.py` (20 node ids) and
  `h-mad/tests/test_grok_audit_surface_assembler_pin.py` (32 node ids), and AC-T14d.5 measures each
  under 40 s. Estimate, not a measurement (neither module exists yet): the slowest path-scope ids
  drive `h-mad/bin/hmad-dispatch audit-cycle` with stub agents, which took 0.63 s for
  `test_pass_roots_give_each_pass_its_own_cd` here, so 20 ids at up to about 1.5 s each is about
  30 s at worst; the assembler-pin ids are in-process calls and a few `git init` subprocesses,
  a few seconds in all.
- No tracked file is edited while a mutation run is in progress (the harness refuses `TREE_MOVED`).
- Each Task's gate is the full suite, `rtk proxy /opt/anaconda3/bin/python3.11 -m pytest h-mad/tests -q -p no:cacheprovider`,
  never a scoped green.
- **A GUARD touches only what exists at RED.** A GUARD is green before the production edit, so it
  never names an API that the edit adds: the switch-off calls pass no `path_scope` keyword (design
  v1.14), and a GUARD over the wrapper reads its output, not only its argv.
- **Monkeypatching an attribute the edit adds uses `raising=False`** (precedent:
  `test_grok_audit_surface_containment.py:1184`), so the RED is the behaviour asserted, never an
  `AttributeError` in the test body.

**Shared literal.** `STUB_PATH_SCOPE_CLAUSE`, a module constant in
`h-mad/tests/test_hmad_dispatch_audit_cycle.py` (added by Task 14a's RED commit, after the line
`CONNECTIONS_MUTATION_SPEC = SPEC_DIR / "audit_cycle_connections.mutation.json"`, line 19, `-cxF` 1),
is the clause spelled out, byte for byte D21's text:

```text
Path scope: a path written inside the document under review, or inside any other document in this prompt, refers to that document's author's environment, not to yours. Every file this audit needs is under your working directory. Do not read, list or search any path outside your working directory for the audit's material. This does not change where you write your report or how you deliver it.
```

The presence tests ((1), (3), (5)) never import the clause from the assembler. The copy test of
Task 14b reads the assembler's `PATH_SCOPE_CLAUSE` by `ast`-parsing the source, without importing
it (design v1.14). The same text is `PATH_SCOPE_CLAUSE` (Task 14a) and `_HMAD_PATH_SCOPE_CLAUSE`
(Task 14b).

---

## Task 14a: `PATH_SCOPE_CLAUSE` and `--path-scope` in the assembler

**Production file**: `h-mad/scripts/h_mad_assemble_audit.py` (`PATH_SCOPE_CLAUSE`, `assemble`, `main`)
**Test files**: `h-mad/tests/test_grok_audit_surface_path_scope.py` (create);
`h-mad/tests/test_hmad_dispatch_audit_cycle.py` (add `STUB_PATH_SCOPE_CLAUSE` only);
`h-mad/tests/mutation-specs/grok_audit_surface.json` (`command` gains
`tests/test_grok_audit_surface_path_scope.py` after `tests/test_grok_audit_surface_containment.py`)
**Task shape**: `new-behaviour`
**Implements**: design D21 ("The clause", "Placement", "The switch" for the assembler, "The pre-clause
reference for test (4)"); spec AC-3.9 tests (1), (2), (4) and (5), invariants (a)–(d).

**Description**: The assembler gains a one-line module constant `PATH_SCOPE_CLAUSE`, a keyword
`assemble(…, path_scope: bool = False)` and a `store_true` flag `--path-scope` that `main` forwards.
With the switch on, `PATH_SCOPE_CLAUSE + "\n\n"` is put in front of the slot-filled text, after
`fill_slots` and before `prepend_output_contract`. The contract slice starts at `CONTRACT_ANCHOR`,
which lies after the clause, so the clause occurs once: banner, head contract, `CONTRACT_SEPARATOR`,
clause, then the body from `You are the agy audit reviewer.` (template line 44) to
`Target document:` (template line 61) and on. With the switch off nothing changes, so production
prompts are byte-identical to the `7e10f543` assembler's.

**Edits, exact** (`h-mad/scripts/h_mad_assemble_audit.py`, `8fd0f637` line numbers; each old text
`-cF` 1):
1. After the `CONTRACT_SEPARATOR` assignment (lines 217–219, whose middle line is
   `    "\n\n====== END OUTPUT CONTRACT — the audit prompt begins below ======\n\n"`, `-cF` 1, and whose
   last line is `)`), add one blank line and:
   ```python
   # grok-audit-surface AC-3.9 (design D21): calibration cycles only, behind --path-scope.
   PATH_SCOPE_CLAUSE = "Path scope: a path written inside the document under review, or inside any other document in this prompt, refers to that document's author's environment, not to yours. Every file this audit needs is under your working directory. Do not read, list or search any path outside your working directory for the audit's material. This does not change where you write your report or how you deliver it."
   ```
2. Old (line 453): `             vh_tail: int | None = None) -> tuple[str, list[str]]:`
   New: `             vh_tail: int | None = None,` followed by
   `             path_scope: bool = False) -> tuple[str, list[str]]:`
3. Old (line 485): `    text, template_residue = fill_slots(text, slots)`
   New: that line, followed by
   `    text = (PATH_SCOPE_CLAUSE + "\n\n" + text) if path_scope else text  # M:PATH-SCOPE-INSERT`
4. Old (line 611): `    args = ap.parse_args(argv)`
   New: these three lines, then that line:
   ```python
       ap.add_argument("--path-scope", action="store_true",
                       help="calibration cycles only (grok-audit-surface AC-3.9): put the "
                            "path-scope clause at the head of the audit body")
   ```
5. Old (line 628): `            vh_tail=args.vh_tail,`
   New: that line, followed by `            path_scope=args.path_scope,  # M:PATH-SCOPE-FLAG`

No mutation row in any committed spec spans lines 215–222, 448–495 or 600–630 of this file (every
row naming `scripts/h_mad_assemble_audit.py` was located; none overlaps; the audit's simulation of
these edits over all 34 specs naming the three scripts agreed).

**Tests** (6 functions, 10 node ids) in the new module, which loads the assembler per test with
`importlib.util.spec_from_file_location("h_mad_assemble_audit_under_test", …)` inside a fixture,
builds its stub feature with `_project_with_history` and `_vh_doc` imported from
`test_h_mad_assemble_audit`, and relies on the conftest's autouse `_hermetic_report_path_claims`
(`XDG_CACHE_HOME` under `tmp_path`). Every switch-off call passes **no** `path_scope` keyword:
- `test_path_scope_clause_present_when_switched_on` (RED): `assemble(path_scope=True)` for the stub
  feature holds `STUB_PATH_SCOPE_CLAUSE` as exactly one line, after `CONTRACT_SEPARATOR` and before
  `Target document:`.
- `test_path_scope_flag_reaches_the_prompt_through_the_cli` (RED): the same through
  `main([... "--path-scope"])` with `--report-file` and `--out` under `tmp_path`; the prompt file read back.
- `test_assembled_prompt_carries_no_root_path` (GUARD, switch off, no `path_scope` keyword):
  `--project-root` is a symlink to the real stub root, the report file lies inside the root, and
  `vh_tail` is smaller than an inlined document's `- v` entry count, so the Version History omission
  note is present. After every occurrence of the report-file string is removed, neither the given
  nor the resolved root spelling occurs.
- `test_path_scope_clause_is_identical_across_roots_and_report_paths` (RED): two switch-on assemblies
  that differ only in project root and report file give byte-identical clause lines, and the
  root-path assertion above holds for both.
- `test_switch_off_prompt_is_byte_identical_to_the_pinned_assembler` (GUARD), parametrized `[plan]`,
  `[design]`, `[impl-plan]`: `git show 7e10f543237267643824c8d452b0415b10103d33:h-mad/scripts/h_mad_assemble_audit.py`
  and `…:h-mad/audit-prompt.template.md` into `tmp_path/ref/scripts/h_mad_assemble_audit.py` and
  `tmp_path/ref/audit-prompt.template.md`, the current `h-mad/invariants.base.md` copied to
  `tmp_path/ref/invariants.base.md`, the reference module loaded with `spec_from_file_location`. Both
  `assemble(...)` calls take the same feature, phase, project root, docs dirs, sentinel, report file
  and `vh_tail`; the reference call gets the reference template and the current call the current
  default template, and the current call passes **no** `path_scope` keyword (design v1.14: at RED
  `assemble` is keyword-only with no such parameter, so `path_scope=False` would raise `TypeError`,
  which the audit ran). The two texts are equal.
- `test_switch_on_prompt_is_switch_off_plus_the_clause_only` (RED), parametrized `[plan]`, `[design]`,
  `[impl-plan]`: removing `STUB_PATH_SCOPE_CLAUSE + "\n\n"` once from the switch-on prompt gives the
  switch-off prompt (no keyword) byte for byte.

**Acceptance Criteria**:
- [ ] AC-T14a.1: The 10 ids pass; the full suite's summary line shows no failure.
- [ ] AC-T14a.2: `grep -c 'M:PATH-SCOPE-' h-mad/scripts/h_mad_assemble_audit.py` prints 2 (matching lines).
- [ ] AC-T14a.3: The spec's `command` holds `tests/test_grok_audit_surface_path_scope.py` right after
  `tests/test_grok_audit_surface_containment.py` (Task 14c then adds the assembler-pin module, which
  completes design v1.14's ten-file list).
- [ ] AC-T14a.4: The four GUARD ids are run, and pass, before the production edit (spec AC-3.9: test (4)
  and the no-root-path half of (2) hold on today's assembler).

**RED split**: 10 ids; 6 F (`assemble` has no `path_scope` keyword and `main` no `--path-scope`
flag: a `TypeError` or an argparse exit per node, never a collection error), 4 P (GUARD:
`test_assembled_prompt_carries_no_root_path` and the three `test_switch_off_prompt_is_byte_identical_to_the_pinned_assembler`
ids, none of which names `path_scope`). PS2 and PS9 are the negative observations for the GUARDs;
PS2 still flips test (4) with the keyword omitted, because then the default is the mutated branch.

**Mutation rows** (6; markers 2). `file` `scripts/h_mad_assemble_audit.py`; tests in
`tests/test_grok_audit_surface_path_scope.py`. Each `find` is its whole marker line (PS9's, the
whole line `            ref = str(path.resolve().relative_to(project_root.resolve()))`, line 463,
`-cF` 1); each `replace` is that line with only the part named changed, the marker kept.

| # | name | replace | test |
|---|---|---|---|
| PS1 | `path-scope-insert-dropped` | `if path_scope else text` becomes `if False else text` | `test_path_scope_clause_present_when_switched_on` |
| PS2 | `path-scope-insert-always` | `if path_scope else text` becomes `if True else text` | `test_switch_off_prompt_is_byte_identical_to_the_pinned_assembler[plan]` |
| PS3 | `path-scope-flag-severed` | `path_scope=args.path_scope` becomes `path_scope=False` | `test_path_scope_flag_reaches_the_prompt_through_the_cli` |
| PS9 | `prompt-names-the-root` | the line becomes `            ref = str(path.resolve())` | `test_assembled_prompt_carries_no_root_path` |
| PS10 | `path-scope-extra-byte` | `PATH_SCOPE_CLAUSE + "\n\n"` becomes `PATH_SCOPE_CLAUSE + "\n\n\n"` | `test_switch_on_prompt_is_switch_off_plus_the_clause_only[plan]` |
| PS11 | `path-scope-clause-names-the-root` | `PATH_SCOPE_CLAUSE + "\n\n"` becomes `PATH_SCOPE_CLAUSE + " " + str(project_root) + "\n\n"` | `test_path_scope_clause_is_identical_across_roots_and_report_paths` |

PS9's omission note is written only when a document has more `- v` entries than `vh_tail`, which
is why its target inlines one with more entries than the `vh_tail` it passes.

**Dependencies on other tasks**: Tasks 18–30 merged to `main` (the S0c merge).

---

## Task 14b: `audit-cycle` turns the switch on with `--pass-root`, records its `$here`, and halts on a missing clause

**Production file**: `h-mad/scripts/hmad-dispatch.sh` (`_HMAD_PATH_SCOPE_CLAUSE`, `_cmd_audit_cycle`)
**Test files**: `h-mad/tests/test_grok_audit_surface_path_scope.py` (extend);
`h-mad/tests/test_hmad_dispatch_audit_cycle.py` (`install_audit_cycle_stubs`: the clause line and the
knob `HMAD_ASSEMBLE_DROP_CLAUSE_PN`, N a pass number); `h-mad/tests/specs/audit_cycle_connections.mutation.json`
(row `verb-assemble-drop` re-anchored, below)
**Task shape**: `wiring` — WIRE 1 forwards the switch from the wrapper to the assembler. The armed
check and the `$here` record this Task also adds are new behaviour; their RED is stated in prose
under "RED split".
**Implements**: design D21 ("The switch", "Fail closed", "The wrapper records its `$here`", "A
switch the assembler does not recognise", "Fixtures that change"), D17 ("The path-scope switch");
spec AC-3.9 tests (3) and (6), "Fail closed"; spec AC-3.6 (the `$here` the run's prompts used).

**WIRE 1**: `h-mad/scripts/hmad-dispatch.sh:_cmd_audit_cycle` → `h-mad/scripts/h_mad_assemble_audit.py:main` (`--path-scope`, on every pass's assembly, exactly when `pass_root_count > 0`)
**WIRE-PIN 1**: `h-mad/tests/test_grok_audit_surface_path_scope.py::test_audit_cycle_with_pass_roots_passes_the_switch_to_every_pass`
**WIRE-PIN 2**: `h-mad/tests/test_grok_audit_surface_path_scope.py::test_calibration_cycle_carries_the_clause_in_every_pass_and_reaches_dispatch`

**Scaffold that makes each WIRE-PIN's RED an assertion about the caller.** The callee exists at RED
(Task 14a's GREEN is on the branch), so no fake module is needed. WIRE-PIN 1 drives the stub
assembler of `install_audit_cycle_stubs`, which records its argv in `assemble_calls.jsonl`; at RED
the assertion that every recorded argv holds `--path-scope` fails. WIRE-PIN 2 runs the real
assembler; at RED each pass's prompt file in the stem dir (`_p1.txt`, `_p2.txt`, `_p3.txt` after the
stem) holds the clause line 0 times, and the assertion on that count fails. Neither RED is an import
or collection error.

**Description**: A calibration cycle is recognised by `--pass-root` (D21): with any given,
`_cmd_audit_cycle` sets `scope_arg=(--path-scope)` and adds `${scope_arg[@]+"${scope_arg[@]}"}` to
every pass's assembler argv; with none, `scope_arg=()` and the argv is exactly as before. After the
assembly loop and its `ASSEMBLE: HALT` branch, and before the divergence check, the check is armed
by the array's **length** (`"${#scope_arg[@]}" -gt 0`; never `[ -n "${scope_arg[@]+x}" ]`, which is
true for an empty array: the audit ran that form and 38 of 86 tests failed). Armed, the wrapper
first writes `here=` and its `$here` to `${stem}.here.txt` in the stem dir, then requires each pass's
prompt to hold exactly one line equal to `_HMAD_PATH_SCOPE_CLAUSE`. The count is captured with
`|| true` (D21's `set -e` class rule: `grep -c` exits 1 on a count of 0, which is exactly the case
this check exists for) and compared as a string, so an empty count also halts. On the first pass N
that does not (`pN` below is that pass's number, as in the Rules' file names): append
`path_scope_missing:pN` to `--halt-file` when one was given, write
`[H-MAD] audit-cycle halted path_scope_missing:pN` to stderr, print
`REQUIRE: STOP reason=path_scope_missing:pN` as the last stdout line, launch nothing, print no
`AUDITCYCLE:` line, return 0. A pre-clause assembler rejects the flag (argparse exit 2), and the
existing `[ "$arc" -eq 0 ] || exit 4` launches nothing. With the switch off nothing is written and
nothing is checked.

**Edits, exact** (`h-mad/scripts/hmad-dispatch.sh`, `8fd0f637` line numbers; the script runs under
`set -euo pipefail`, line 5):
1. Old (line 3559, `-cxF` 1): `_cmd_audit_cycle() {`
   New: a top-level line, one blank line, then that line:
   `_HMAD_PATH_SCOPE_CLAUSE="Path scope: a path written inside the document under review, or inside any other document in this prompt, refers to that document's author's environment, not to yours. Every file this audit needs is under your working directory. Do not read, list or search any path outside your working directory for the audit's material. This does not change where you write your report or how you deliver it."`
   (the clause holds no `"`, `$`, backtick or backslash, so it is literal inside double quotes).
2. Old (line 3566, `-cF` 1): `  pass_args=(); gated=(); legs=(); pass_root=()`
   New: that line, followed by `  local -a scope_arg; scope_arg=()`
3. Old (lines 3646–3649, a multi-line text unique because its first line is, `-cF` 1):
   `      echo "hmad-dispatch: audit-cycle: --pass-root first root is not --project-root" >&2` /
   `      return 2` / `    fi` / `  fi`
   New: those four lines, followed by
   `  if [ "$pass_root_count" -gt 0 ]; then scope_arg=(--path-scope); fi  # M:PATH-SCOPE-SWITCH`
4. Old (line 3739, `-cF` 1): `         --report-file "${report[$i]}" --out "${prompt[$i]}" >"${asm[$i]}"`
   New: `         --report-file "${report[$i]}" --out "${prompt[$i]}" ${scope_arg[@]+"${scope_arg[@]}"} >"${asm[$i]}"`
5. Insert after the blank line (3774) that follows the `ASSEMBLE: HALT` branch's closing `  fi`
   (line 3773) and before the line
   `  # Two prompts for the same cycle must differ ONLY in the per-pass report path.` (line 3775, `-cF` 1):
   ```bash
     if [ "${#scope_arg[@]}" -gt 0 ]; then  # M:PATH-SCOPE-CHECK-ARMED
       printf 'here=%s\n' "$here" > "${stem}.here.txt" || exit 4  # M:PATH-SCOPE-HERE
       local n
       i=1
       while [ "$i" -le "$passes" ]; do
         n="$(grep -cxF -e "$_HMAD_PATH_SCOPE_CLAUSE" -- "${prompt[$i]}" || true)"
         if [ "$n" != 1 ]; then  # M:PATH-SCOPE-CHECK
           [ -z "$halt_file" ] || printf '%s\n' "path_scope_missing:p$i" >> "$halt_file"  # M:PATH-SCOPE-HALT-FILE
           echo "[H-MAD] audit-cycle halted path_scope_missing:p$i" >&2
           echo "REQUIRE: STOP reason=path_scope_missing:p$i"
           return 0
         fi
         i=$((i + 1))
       done
     fi

   ```
   `n` is not used elsewhere in `_cmd_audit_cycle` (lines 3559–3900 searched at `8fd0f637`). The
   audit ran the array-length guard under `/bin/bash` 3.2.57 and `/opt/homebrew/bin/bash` 5.3.20
   with `set -euo pipefail`: off for an empty array, on for one element, and 86 passed over the
   wrapper and audit-cycle modules with the plan's other edits applied.

**Other specs' anchors (Rules, "Lines other specs anchor on").** Edit 4 changes the third line of
`verb-assemble-drop`'s three-line `find` in `h-mad/tests/specs/audit_cycle_connections.mutation.json`
(its `failure_test` is `test_verb_assemble_halt_no_dispatch`). That row is re-anchored in the GREEN
commit: its `find` gains the same ` ${scope_arg[@]+"${scope_arg[@]}"}` text, and its `replace`
(`    if : >"${asm[$i]}"`) is unchanged, so its intent is unchanged (the Task 20 precedent in the S0c
notes). Edit 5 is placed after the blank line, so `verb-helper-force`, whose `find` ends with that
branch's `  fi` and its newline, stays byte-identical. Edits 1, 2 and 3 touch no line any row finds
(every row naming `scripts/hmad-dispatch.sh` in `h-mad/tests/mutation-specs/` and
`h-mad/tests/specs/` was located; only `pass-root-project-disarmed`, at line 3645, and these two
`audit_cycle_connections` rows meet the edited spans, and edit 3 keeps line 3645 byte-identical; the
audit's simulation over all 34 specs found only `verb-assemble-drop` drifting).

**Stub edits, exact** (`h-mad/tests/test_hmad_dispatch_audit_cycle.py`, `install_audit_cycle_stubs`,
inside its f-string; the source bytes are quoted as they stand in the file):
1. Old (line 197, 16 leading spaces; `-cxF` 1, while `-cF` is 2 because line 362 of another stub,
   with 20 spaces, contains it):
   `                extra = "Unexpected prompt-only divergence\\n"`
   New: that line, followed by
   ```python
               scope = ""
               if "--path-scope" in args and not os.environ.get(f"HMAD_ASSEMBLE_DROP_CLAUSE_P{{pass_index}}"):
                   scope = {STUB_PATH_SCOPE_CLAUSE!r} + "\\n"
   ```
2. Old (lines 211–212, a multi-line pair: its first line alone is `-cF` 3 and `-cxF` 2, at lines
   211, 368 and 1394; its second line `                + head_report_line +` is `-cxF` 1, so the pair is unique):
   `                "Audit prompt\\n"` followed by `                + head_report_line +`
   New: `                "Audit prompt\\n" + scope` followed by `                + head_report_line +`

Without `--path-scope` the stub writes byte-for-byte what it writes at `8fd0f637`. The stub line
`report = Path(args[args.index("--report-file") + 1])` stays exactly once, because
`_pass_root_case` (`test_grok_audit_surface_wrapper.py:687`) asserts that count before patching it.
After GREEN, `test_pass_roots_give_each_pass_its_own_cd` and
`test_pass_root_report_path_lies_in_its_own_root`, the only tests that reach dispatch with
`--pass-root` (`grep -c -- '--pass-root'` over `h-mad/tests/*.py` at `8fd0f637`: 6 matching lines in
`test_grok_audit_surface_wrapper.py`, 1 in `test_grok_audit_surface_probe.py`, a
`--pass-root-record` argument), pass the check because the stub writes the clause.

**Tests** (8 functions, 10 node ids), added to the path-scope module. The stub-driven ones reuse
`_pass_root_case` and `_run_pass_roots`, imported from `test_grok_audit_surface_wrapper`:
- WIRE-PIN 1, `test_audit_cycle_with_pass_roots_passes_the_switch_to_every_pass` (RED): three pass
  roots; every row of `assemble_calls.jsonl` holds `--path-scope`.
- `test_audit_cycle_without_pass_roots_does_not_pass_the_switch` (GUARD; argv **and** output): no
  `--pass-root`; no recorded argv holds `--path-scope`; stdout has exactly one `AUDITCYCLE:` line and
  no `REQUIRE: STOP`; the stem dir holds no `*.here.txt`. So an armed check without `--pass-root`
  fails it (PS14).
- WIRE-PIN 2, `test_calibration_cycle_carries_the_clause_in_every_pass_and_reaches_dispatch` (RED):
  `audit-cycle --passes 3 --pass-root …` with `HMAD_AUDIT_CYCLE_SCRIPT_DIR` removed from the
  environment (so the real assembler and the real `h_mad_audit_cycle.py` run), stub agents,
  `HMAD_AUDIT_STEM_DIR` under `tmp_path`, and plain test-written documents (not `HOSTILE_DOC`) of
  which one holds an absolute path line, as d1 did. It asserts that each pass's `_p1.asm.txt`,
  `_p2.asm.txt` and `_p3.asm.txt` file in the stem dir reads `ASSEMBLE: PASS`, that each pass's
  prompt file there holds the clause line exactly once, three dispatches, and no
  `reason=prompt_divergence`.
- `test_calibration_cycle_records_its_here` (RED, design v1.14): the setup of the test above; the
  stem dir holds exactly one `*.here.txt`, whose one line is `here=` followed by the `pwd -P` of
  `h-mad/scripts`.
- `test_calibration_cycle_halts_when_a_pass_lacks_the_clause` (RED), parametrized `[p2]`
  (`HMAD_ASSEMBLE_DROP_CLAUSE_P2=1`), `[p1]` (`…_P1=1`), `[all]` (`…_P1`, `…_P2`, `…_P3` all `1`),
  with `--halt-file` naming `HALT` under `tmp_path`: exit 0; last stdout line exactly
  `REQUIRE: STOP reason=path_scope_missing:p2` for `[p2]` and `…:p1` for `[p1]` and `[all]`; no
  `AUDITCYCLE:` line; `dispatch_count` 0; `cycle_calls.jsonl` empty; the halt file holds that
  reason line once; the stderr marker present.
- `test_calibration_cycle_with_the_clause_in_every_pass_launches` (RED, the negative control of PS6
  and PS7): the same case with no knob and `--halt-file` naming an absent path; three dispatches, one
  `AUDITCYCLE:` line, no `REQUIRE: STOP`, and each prompt holds `STUB_PATH_SCOPE_CLAUSE` once.
- `test_pre_clause_assembler_refuses_the_switch_and_nothing_launches` (RED): a script dir `old/scripts`
  under `tmp_path` holding the `7e10f543` assembler (`git show`) and copies of the real
  `h_mad_audit_cycle.py` and of the three modules it imports, `h_mad_extract_report.py`,
  `h_mad_review_evidence.py` (`h_mad_audit_cycle.py:18-20`) and `h_mad_audit_gate.py` (its lazy import,
  line 764), with the `7e10f543` template and the current `invariants.base.md` in `old/`, as
  `HMAD_AUDIT_CYCLE_SCRIPT_DIR`; three pass roots. It asserts `dispatch_count == 0` **first**, then
  wrapper exit 4 and no `AUDITCYCLE:` line, so a mutant that dispatches fails on the dispatch, not on
  a helper crash.
- `test_wrapper_clause_copy_equals_the_assembler_constant` (RED): reads
  `^_HMAD_PATH_SCOPE_CLAUSE="([^"\n]*)"$` (multiline) from `hmad-dispatch.sh`, exactly one match;
  reads `PATH_SCOPE_CLAUSE` from `h-mad/scripts/h_mad_assemble_audit.py` by `ast.parse`, taking the
  module-level assignment's string constant, without importing the module (design v1.14); both equal
  `STUB_PATH_SCOPE_CLAUSE`.

**Acceptance Criteria**:
- [ ] AC-T14b.1: The 10 ids pass, and the 10 Task 14a ids still pass; the full suite's summary line
  shows no failure, `test_grok_audit_surface_wrapper.py` and `test_hmad_dispatch_audit_cycle.py`
  included, unchanged.
- [ ] AC-T14b.2: Each WIRE-PIN fails when only WIRE 1 is cut (PS4, PS12) and passes on the restored line.
- [ ] AC-T14b.3: `grep -c 'M:PATH-SCOPE-' h-mad/scripts/hmad-dispatch.sh` prints 5,
  `grep -c '^_HMAD_PATH_SCOPE_CLAUSE=' h-mad/scripts/hmad-dispatch.sh` prints 1, and
  `grep -c 'scope_arg\[@\]+x' h-mad/scripts/hmad-dispatch.sh` prints 0 (matching lines).
- [ ] AC-T14b.4: `--check-anchors` reads `ANCHORS: ANCHORS_OK` on
  `h-mad/tests/specs/audit_cycle_connections.mutation.json`, and its mutation run reads
  `MUTATION: ALL_CAUGHT` with `crash_kills=0`.

**RED split** (stated for the record; the WIRE-PINs, not the split, gate this Task): 10 ids; 9 F, 1
P (GUARD: `test_audit_cycle_without_pass_roots_does_not_pass_the_switch`, whose argv and output both
hold before the edit; its negative observations are PS5 and PS14). The three halt ids, the `$here`
test and the copy test fail because the check, the record and the constant do not exist (the cycle
launches; no `*.here.txt`; the regex finds nothing); the control and the pre-clause test fail because
no flag is forwarded (no clause in any prompt; the old assembler builds a prompt and the cycle
dispatches). The stub edits and `STUB_PATH_SCOPE_CLAUSE` are test-side and land in the RED commit;
without `--path-scope` in the argv they change nothing, so no existing test moves at RED.

**Mutation rows** (9; markers 5). `file` `scripts/hmad-dispatch.sh`; tests in
`tests/test_grok_audit_surface_path_scope.py`. Each `find` is its whole marker line (PS8's, the
whole `_HMAD_PATH_SCOPE_CLAUSE=` line); each `replace` is that line with only the part named
changed, the marker kept.

| # | name | marker or find | replace | test |
|---|---|---|---|---|
| PS4 | `path-scope-switch-dropped` | `# M:PATH-SCOPE-SWITCH` | `if [ "$pass_root_count" -gt 0 ]` becomes `if false` | `test_audit_cycle_with_pass_roots_passes_the_switch_to_every_pass` |
| PS5 | `path-scope-switch-always` | `# M:PATH-SCOPE-SWITCH` | the same condition becomes `if true` | `test_audit_cycle_without_pass_roots_does_not_pass_the_switch` |
| PS6 | `path-scope-check-dropped` | `# M:PATH-SCOPE-CHECK` | `[ "$n" != 1 ]` becomes `false` | `test_calibration_cycle_halts_when_a_pass_lacks_the_clause[p2]` |
| PS7 | `path-scope-halt-file-dropped` | `# M:PATH-SCOPE-HALT-FILE` | the statement becomes `:` | `test_calibration_cycle_halts_when_a_pass_lacks_the_clause[p2]` |
| PS8 | `path-scope-clause-copy-drifted` | the `_HMAD_PATH_SCOPE_CLAUSE=` line | `Every file` becomes `Each file` | `test_wrapper_clause_copy_equals_the_assembler_constant` |
| PS12 | `path-scope-switch-dropped-real-cycle` | `# M:PATH-SCOPE-SWITCH` | as PS4 | `test_calibration_cycle_carries_the_clause_in_every_pass_and_reaches_dispatch` |
| PS13 | `path-scope-switch-dropped-old-assembler` | `# M:PATH-SCOPE-SWITCH` | as PS4 | `test_pre_clause_assembler_refuses_the_switch_and_nothing_launches` |
| PS14 | `path-scope-check-always` | `# M:PATH-SCOPE-CHECK-ARMED` | `[ "${#scope_arg[@]}" -gt 0 ]` becomes `true` | `test_audit_cycle_without_pass_roots_does_not_pass_the_switch` |
| PS15 | `path-scope-here-dropped` | `# M:PATH-SCOPE-HERE` | the `printf … || exit 4` statement becomes `:` | `test_calibration_cycle_records_its_here` |

PS13's target dispatches under the mutant: with no flag forwarded, the pre-clause assembler builds
a prompt, and `dispatch_count == 0`, asserted first, fails. Under PS6 with
`HMAD_ASSEMBLE_DROP_CLAUSE_P2`, the cycle reaches the divergence check, whose differing line names no
report path, so it records `prompt_divergence` instead of the halt token. Under PS14 with no
`--pass-root`, the stub writes no clause, so the armed check halts `path_scope_missing:p1`.

**Dependencies on other tasks**: Task 14a (the callee and `STUB_PATH_SCOPE_CLAUSE`).

---

## Task 14c: `assembler-read`, `assembler-check` and `require --verb assembler`

**Production file**: `h-mad/scripts/h_mad_grok_containment.py`
**Test files**: `h-mad/tests/test_grok_audit_surface_assembler_pin.py` (create);
`h-mad/tests/mutation-specs/grok_audit_surface.json` (`command` gains
`tests/test_grok_audit_surface_assembler_pin.py` right after `tests/test_grok_audit_surface_path_scope.py`,
which makes it design v1.14's ten-file list)
**Task shape**: `new-behaviour`
**Implements**: design D21 ("The assembler pin", "The wrapper records its `$here`"), D20 (`require`),
D8 (`require` scope, four prefixes); spec AC-3.6 (the assembler commit; an unpinned run is not scored).

**Module placement (design v1.14).** The fixtures go in the new module, not in
`test_grok_audit_surface_containment.py`, which is over the judge's 40 s budget. The new module
imports `containment_module`, `_containment_cli`, `_containment_main` and `_assert_containment_token`
from `test_grok_audit_surface_containment`, and `STUB_PATH_SCOPE_CLAUSE` from
`test_hmad_dispatch_audit_cycle`, as the wrapper module imports its helpers. The containment
module is not edited, so its existing Task 22 and Task 23 ids are unchanged.

**Description**: two verbs and one `require` verb, both run with `GIT_DIR`, `GIT_WORK_TREE`,
`GIT_COMMON_DIR`, `GIT_OBJECT_DIRECTORY` and `GIT_ALTERNATE_OBJECT_DIRECTORIES` removed from git's
environment.
- `assembler-read [--here <dir>]` prints one line,
  `ASSEMBLER-READING: sha=<sha40|unreadable> dirty=<no|yes|unknown> script_dir_env=<unset|set> here=<abs>`,
  exit 0. `here` is `SELF_DIR = Path(__file__).resolve().parent` unless `--here` is given (tests
  only). `sha` is the stdout of `git -C <here> rev-parse --verify HEAD` when it is exactly 40
  lowercase hex, else `unreadable` (`# M:ASSEMBLER-READ-SHA`). `dirty` is `unknown` when
  `git -C <here>/.. status --porcelain --untracked-files=all -- .` fails, `yes` when it prints
  anything, `no` otherwise (`# M:ASSEMBLER-READ-DIRTY`). `script_dir_env` is `set` when
  `HMAD_AUDIT_CYCLE_SCRIPT_DIR` is in the environment, an empty value included
  (`# M:ASSEMBLER-READ-ENV`). An escaping exception prints
  `ASSEMBLER-READING: unreadable reason=internal:<ExceptionName>`, exit 2. A usage error prints
  `ASSEMBLER-READING: unreadable reason=internal:UsageError`, exit 2, from its own branch in `main`'s
  `except UsageError` block (`# M:ASSEMBLER-READ-USAGE`; design v1.14).
- `assembler-check --start <file> --end <file> --reading <dir> --stems <dir> --stages <resmoke|resmoke,s2>`
  prints one token line, exit 0, the first that applies, in D21's order:
  - `ASSEMBLER: UNPINNED reason=` one of:
    - `reading_unparseable:start`, then `:end` (an absent file, or not exactly one line beginning
      `ASSEMBLER-READING: ` that fullmatches `sha=(\S+) dirty=(\S+) script_dir_env=(\S+) here=(.+)`
      after the prefix; `# M:ASSEMBLER-READING-UNPARSEABLE`);
    - `script_dir_set` (either reading; `# M:ASSEMBLER-SCRIPT-DIR-SET`);
    - `sha_unreadable` (either; `# M:ASSEMBLER-SHA-UNREADABLE`);
    - `here_changed` (`# M:ASSEMBLER-HERE-CHANGED`);
    - `sha_changed` (`# M:ASSEMBLER-SHA-CHANGED`);
    - `dirty:yes` or `dirty:unknown`, the start reading's `dirty` value when it is not `no`, else the
      end reading's (`# M:ASSEMBLER-DIRTY`);
    - `here_not_self` (the readings' `here` is not `str(SELF_DIR)`; `# M:ASSEMBLER-HERE-NOT-SELF`);
    - `here_unrecorded:` and the cycle id, or `here_mismatch:` and the cycle id (design v1.14). The
      cycle directories are the entries of `--stems` whose names fullmatch
      `^(s1-[a-z]+|s2-d[0-9]+-v[0-9]+)$` (`# M:ASSEMBLER-STEMS-DIRS`), which skips the sibling
      `.agy-log` directories and `.txt` files, checked in sorted order, the first failure reported.
      `here_unrecorded` when a cycle directory does not hold exactly one `*.here.txt` whose content
      is exactly one `here=` line (`# M:ASSEMBLER-HERE-UNRECORDED`); `here_mismatch` when that
      line's value is not the readings' `here` (`# M:ASSEMBLER-HERE-MISMATCH`).
  - Then `ASSEMBLER: NO_CLAUSE reason=` one of the three reasons below, then ` sha=` and the start
    reading's sha: `clause_unavailable` (the `h_mad_assemble_audit.py` beside `SELF_DIR` is absent,
    raises on load with `spec_from_file_location`, or has no non-empty one-line `str`
    `PATH_SCOPE_CLAUSE`; `# M:ASSEMBLER-CLAUSE-UNAVAILABLE`), `no_prompts:resmoke` or
    `no_prompts:s2` (in `--stages` order, a stage whose glob, `resmoke/*/p*.prompt.txt` or
    `s2/d*/v*/p*.prompt.txt` under `--reading`, matches nothing; `# M:ASSEMBLER-NO-PROMPTS`), or
    `clause_missing:` and the path relative to `--reading` (the first prompt, sorted by that relative
    path over every named stage, whose lines do not hold the clause exactly once; lines are the bytes
    decoded as UTF-8 and split on `"\n"` only, never `splitlines()`, so the count agrees with the
    wrapper's `grep -cxF`; `# M:ASSEMBLER-CLAUSE-MISSING`).
  - Otherwise `ASSEMBLER: PINNED sha=<sha40> prompts=<n> here=<abs>`.
  An escaping exception prints `ASSEMBLER: UNPINNED reason=internal:<ExceptionName>` and exits 2
  (`# M:ASSEMBLER-LAST-RESORT` on that branch's `return 2`). A usage error prints
  `ASSEMBLER: UNPINNED reason=internal:UsageError`, exit 2, from its own branch
  (`# M:ASSEMBLER-CHECK-USAGE`; design v1.14).
- `require --verb assembler`: `REQUIRE: OK` only when the last line begins `ASSEMBLER: PINNED sha=`
  (`# M:REQUIRE-OK-ASSEMBLER`); otherwise `REQUIRE: STOP reason=<that line | no_token:<file>>`. Like
  the canary and quarantine verbs it writes no halt file.

**Edits to existing lines, exact** (`8fd0f637` line numbers):
1. Old (line 20, `-cxF` 1): `class UsageError(Exception):` — New: `SELF_DIR = Path(__file__).resolve().parent`,
   two blank lines, then that line.
2. Old (lines 102–103, a multi-line pair: the first line is `-cF` 1, the second, `    else:`, is
   `-cxF` 1): `        ok = line == "GROK-CANARY: PASS"  # M:REQUIRE-OK-CANARY` / `    else:`
   New: the first line, then `    elif args.verb == "assembler":`,
   `        ok = line.startswith("ASSEMBLER: PINNED sha=")  # M:REQUIRE-OK-ASSEMBLER`, then `    else:`.
   Lines 100, 102, 104, 108 and 110, which rows of Task 22 find, stay byte-identical.
3. Old (line 253, `-cF` 1): `        consume.add_argument("--verb", choices=("toolscan", "grok-canary", "quarantine"), required=True)`
   New: the same with `choices=("toolscan", "grok-canary", "quarantine", "assembler")`.
4. Old (line 261, `-cxF` 1): `        args = parser.parse_args(argv)` — New: before it, the two
   sub-parsers (`assembler-read` with `--here`; `assembler-check` with `--start`, `--end`,
   `--reading`, `--stems` required and `--stages` required with `choices=("resmoke", "resmoke,s2")`),
   each `add_help=False, allow_abbrev=False`; after it, `if args.mode == "assembler-read": return assembler_read(args)`
   and the same for `assembler-check`, before the existing `if args.mode == "quarantine":`.
5. Old (line 276, `-cF` 1): `        print("QUARANTINE: REFUSED reason=internal:UsageError")  # M:QUARANTINE-USAGE`
   New: before it,
   ```python
           if mode == "assembler-read":
               print("ASSEMBLER-READING: unreadable reason=internal:UsageError")  # M:ASSEMBLER-READ-USAGE
               return 2
           if mode == "assembler-check":
               print("ASSEMBLER: UNPINNED reason=internal:UsageError")  # M:ASSEMBLER-CHECK-USAGE
               return 2
   ```
   then that line, unchanged.
6. Old (line 284, `-cF` 1): `        print(f"QUARANTINE: REFUSED reason=internal:{type(exc).__name__}")`
   New: before it, the two `mode` branches printing `ASSEMBLER-READING: unreadable reason=internal:{type(exc).__name__}`
   and `ASSEMBLER: UNPINNED reason=internal:{type(exc).__name__}`, the `assembler-check` branch ending
   `            return 2  # M:ASSEMBLER-LAST-RESORT`; then that line, unchanged. Lines 247, 276, 281,
   283 and 285, which Task 22 and Task 23 rows find, stay byte-identical.

**Code structure** (new):
```python
SELF_DIR = Path(__file__).resolve().parent
def _git(here: Path, *args: str) -> subprocess.CompletedProcess: ...  # scrubbed GIT_* env
def assembler_read(args: argparse.Namespace) -> int: ...
def parse_assembler_reading(path: str) -> dict[str, str] | None: ...
def _assembler_clause() -> str | None: ...
def _recorded_here(stems: Path, here: str) -> str | None: ...  # the first here_* reason, or None
def assembler_check(args: argparse.Namespace) -> int: ...
```

**Tests** (24 functions, 32 node ids) in the new module. Every fixture asserts the exit code beside
the exact last stdout line through `_assert_containment_token`. The `assembler-read` fixtures run
`_containment_cli("assembler-read", "--here", …)` against a git repository made under `tmp_path`
with the GIT_* variables removed (`h-mad/scripts/` committed, `HMAD_AUDIT_CYCLE_SCRIPT_DIR` removed
unless the test sets it). The `assembler-check` fixtures call `_containment_main` in process with
`monkeypatch.setattr(module, "SELF_DIR", <temp dir>, raising=False)`, the temp dir holding a stand-in
`h_mad_assemble_audit.py` that defines `PATH_SCOPE_CLAUSE` as `STUB_PATH_SCOPE_CLAUSE`, readings
written by the test, a `--reading` tree whose prompts hold the clause once, and a `--stems` tree
whose cycle directories (`s1-grok`, `s2-d1-v1`) each hold one `*.here.txt` with the readings' `here`;
so each fixture plants its one condition alone:
- `assembler-read` (6 functions, 7 ids): `test_assembler_read_clean_tree_reads_sha_and_no`,
  `test_assembler_read_dirty_h_mad_reads_yes` (an untracked file under `h-mad/`),
  `test_assembler_read_outside_git_reads_unreadable` (`sha=unreadable dirty=unknown`; it first asserts
  `git -C` on its parent with `rev-parse --git-dir` fails), `test_assembler_read_records_a_set_script_dir_env`
  parametrized `[nonempty]` and `[empty]`, `test_assembler_read_sha256_repository_reads_unreadable`
  (plan-added: a repository made with `git init --object-format=sha256` and one commit, so
  `rev-parse` succeeds with 64 hex characters, which the impl-plan audit measured on git 2.54.0;
  `sha=unreadable dirty=no`), and `test_assembler_read_usage_error_exits_2` (an unknown flag:
  exactly `ASSEMBLER-READING: unreadable reason=internal:UsageError`, exit 2, no `QUARANTINE:` line).
- `assembler-check` (17 functions, 20 ids): `test_assembler_check_pinned` (the must-not-refuse
  control), `test_assembler_check_unparseable_reading` (the start reading broken, the end one intact:
  `reading_unparseable:start`), `test_assembler_check_script_dir_set`,
  `test_assembler_check_sha_unreadable`, `test_assembler_check_here_changed`,
  `test_assembler_check_sha_changed`, `test_assembler_check_dirty` parametrized `[yes]` and
  `[unknown]`, `test_assembler_check_here_not_self`, `test_assembler_check_here_unrecorded`
  parametrized `[none]` (a cycle directory with no `*.here.txt`) and `[two]` (one with two),
  `test_assembler_check_here_mismatch`, `test_assembler_check_ignores_sibling_agy_log_dirs` (an
  `s2-d1-v1.agy-log` directory and an `s2-d1-v1.p1.root.txt` file beside the cycle directories, with
  no `*.here.txt`: still `PINNED`), `test_assembler_check_clause_unavailable`,
  `test_assembler_check_no_prompts` parametrized `[resmoke]` (no resmoke prompt) and `[s2]`
  (`--stages resmoke,s2`, resmoke prompts with the clause, no S2 prompt),
  `test_assembler_check_clause_missing`, `test_assembler_check_clause_twice_is_missing`,
  `test_assembler_check_internal_exits_2` (a helper the check calls replaced in process, with
  `raising=False`, by one raising `RuntimeError`: exactly
  `ASSEMBLER: UNPINNED reason=internal:RuntimeError`, exit 2), and
  `test_assembler_check_usage_error_exits_2` (an unknown flag: exactly
  `ASSEMBLER: UNPINNED reason=internal:UsageError`, exit 2, no `QUARANTINE:` line).
- `test_require_assembler_ok_only_on_pinned` (1 function, 5 ids), parametrized `[PINNED]`
  (`REQUIRE: OK`), `[UNPINNED]`, `[NO_CLAUSE]`, `[empty]` and `[absent]` (each `REQUIRE: STOP`), exit
  0 each, and no halt file created in any case.

**Acceptance Criteria**:
- [ ] AC-T14c.1: The 32 ids pass; the full suite's summary line shows no failure.
- [ ] AC-T14c.2: `grep -c '# M:ASSEMBLER-' h-mad/scripts/h_mad_grok_containment.py` prints 19 and
  `grep -c '# M:REQUIRE-OK-ASSEMBLER' h-mad/scripts/h_mad_grok_containment.py` prints 1 (matching lines).
- [ ] AC-T14c.3: `test_require_ok_per_verb` keeps its three ids (`[toolscan]`, `[grok-canary]`,
  `[quarantine]`), `test_grok_audit_surface_containment.py` is unchanged
  (`git diff --quiet` on it), and every Task 22 and Task 23 row still finds its line (`--check-anchors`).

**RED split**: 32 ids; 32 F, 0 P. At RED both verbs are unknown sub-commands, so `main` takes the
usage branch and prints a `QUARANTINE:` token, and `--verb assembler` is rejected by `choices`. The
in-process `assembler-check` ids set `SELF_DIR` and the injected helper with `raising=False`, so they
reach `main` and fail on that token, not on an `AttributeError` (impl-plan audit should-fix).

**Mutation rows** (27; markers 20). `file` `scripts/h_mad_grok_containment.py`; tests in
`tests/test_grok_audit_surface_assembler_pin.py`. Rows 6, 7, 19 and 25 change the printed reason
rather than disarm, so no mutant reaches later code with a value the guard rejected (Rules, "S0c
scripts"). Each `find` is its whole marker line, and each marked condition sits on its marker line.
D21 requires one row per `# M:ASSEMBLER-<REASON>` guard, one per usage branch and one for
`# M:REQUIRE-OK-ASSEMBLER`: rows 6, 7, 8, 9, 10, 11, 12, 14, 15, 17, 19, 20, 22, 24, 25 and 26 (16).
Rows 1–5, 13, 16, 18, 21, 23 and 27 (11) are plan-added, one per alternative that a single disarm
cannot tell apart, as Task 21 added its own.

| # | name | marker | replace | test |
|---|---|---|---|---|
| 1 | `assembler-read-sha-dropped` | `# M:ASSEMBLER-READ-SHA` | `sha` always `unreadable` | `test_assembler_read_clean_tree_reads_sha_and_no` |
| 2 | `assembler-read-sha-unchecked` | `# M:ASSEMBLER-READ-SHA` | the stdout taken without the 40-hex check | `test_assembler_read_sha256_repository_reads_unreadable` |
| 3 | `assembler-read-dirty-never` | `# M:ASSEMBLER-READ-DIRTY` | `yes` never chosen | `test_assembler_read_dirty_h_mad_reads_yes` |
| 4 | `assembler-read-dirty-unknown-dropped` | `# M:ASSEMBLER-READ-DIRTY` | `unknown` never chosen (a failed status reads `no`) | `test_assembler_read_outside_git_reads_unreadable` |
| 5 | `assembler-read-env-nonempty-only` | `# M:ASSEMBLER-READ-ENV` | `set` only for a non-empty value | `test_assembler_read_records_a_set_script_dir_env[empty]` |
| 6 | `assembler-read-usage-reason` | `# M:ASSEMBLER-READ-USAGE` | prints `internal:Usage` | `test_assembler_read_usage_error_exits_2` |
| 7 | `assembler-reading-unparseable-reason` | `# M:ASSEMBLER-READING-UNPARSEABLE` | prints `reading_unparseable:end` for either reading | `test_assembler_check_unparseable_reading` |
| 8 | `assembler-script-dir-set-disarmed` | `# M:ASSEMBLER-SCRIPT-DIR-SET` | condition never fires | `test_assembler_check_script_dir_set` |
| 9 | `assembler-sha-unreadable-disarmed` | `# M:ASSEMBLER-SHA-UNREADABLE` | condition never fires | `test_assembler_check_sha_unreadable` |
| 10 | `assembler-here-changed-disarmed` | `# M:ASSEMBLER-HERE-CHANGED` | condition never fires | `test_assembler_check_here_changed` |
| 11 | `assembler-sha-changed-disarmed` | `# M:ASSEMBLER-SHA-CHANGED` | condition never fires | `test_assembler_check_sha_changed` |
| 12 | `assembler-dirty-disarmed` | `# M:ASSEMBLER-DIRTY` | condition never fires | `test_assembler_check_dirty[yes]` |
| 13 | `assembler-dirty-yes-only` | `# M:ASSEMBLER-DIRTY` | fires only on `yes` | `test_assembler_check_dirty[unknown]` |
| 14 | `assembler-here-not-self-disarmed` | `# M:ASSEMBLER-HERE-NOT-SELF` | condition never fires | `test_assembler_check_here_not_self` |
| 15 | `assembler-here-unrecorded-disarmed` | `# M:ASSEMBLER-HERE-UNRECORDED` | condition never fires | `test_assembler_check_here_unrecorded[none]` |
| 16 | `assembler-here-unrecorded-at-least-one` | `# M:ASSEMBLER-HERE-UNRECORDED` | fires only on zero files | `test_assembler_check_here_unrecorded[two]` |
| 17 | `assembler-here-mismatch-disarmed` | `# M:ASSEMBLER-HERE-MISMATCH` | condition never fires | `test_assembler_check_here_mismatch` |
| 18 | `assembler-stems-dirs-widened` | `# M:ASSEMBLER-STEMS-DIRS` | every directory entry is a cycle directory | `test_assembler_check_ignores_sibling_agy_log_dirs` |
| 19 | `assembler-clause-unavailable-reason` | `# M:ASSEMBLER-CLAUSE-UNAVAILABLE` | prints `no_prompts:clause` | `test_assembler_check_clause_unavailable` |
| 20 | `assembler-no-prompts-disarmed` | `# M:ASSEMBLER-NO-PROMPTS` | condition never fires | `test_assembler_check_no_prompts[resmoke]` |
| 21 | `assembler-no-prompts-resmoke-only` | `# M:ASSEMBLER-NO-PROMPTS` | fires only for the `resmoke` stage | `test_assembler_check_no_prompts[s2]` |
| 22 | `assembler-clause-missing-disarmed` | `# M:ASSEMBLER-CLAUSE-MISSING` | condition never fires | `test_assembler_check_clause_missing` |
| 23 | `assembler-clause-missing-at-least-once` | `# M:ASSEMBLER-CLAUSE-MISSING` | fires only on a count below 1 | `test_assembler_check_clause_twice_is_missing` |
| 24 | `assembler-last-resort-exit-0` | `# M:ASSEMBLER-LAST-RESORT` | `return 0` | `test_assembler_check_internal_exits_2` |
| 25 | `assembler-check-usage-reason` | `# M:ASSEMBLER-CHECK-USAGE` | prints `internal:Usage` | `test_assembler_check_usage_error_exits_2` |
| 26 | `require-ok-assembler-narrowed` | `# M:REQUIRE-OK-ASSEMBLER` | never OK | `test_require_assembler_ok_only_on_pinned[PINNED]` |
| 27 | `require-ok-assembler-widened` | `# M:REQUIRE-OK-ASSEMBLER` | OK on any `ASSEMBLER: ` line | `test_require_assembler_ok_only_on_pinned[UNPINNED]` |

`test_assembler_check_pinned` has no row of its own: it is the must-not-refuse control of rows 8–23.
Row 2's kill does not depend on whether the implementation also checks the return code: in its
fixture `rev-parse` succeeds, so only the 40-hex check can turn a 64-character sha into `unreadable`.

**Dependencies on other tasks**: Task 22 (`require`), Task 14b (the `${stem}.here.txt` record that
`--stems` reads; the fixtures write their own, so 14c's tests do not need 14b's GREEN), Task 14a
(`PATH_SCOPE_CLAUSE`; the fixtures use a stand-in).

---

## Task 14d: the path-scope Phase 5e verdict

**Production files**: none
**Test files**: none
**Task shape**: `gate` — reads verdicts over what Tasks 14a–14c built; writes no production file.
**Implements**: design "Implementation Order" item 12 (full suite, then Phase 5e, before run 3);
design Test Plan "Mutation spec" (the v1.13 and v1.14 rows).

```bash
rtk proxy /opt/anaconda3/bin/python3.11 -m pytest --version
rtk proxy /opt/anaconda3/bin/python3.11 -m pytest h-mad/tests -q -p no:cacheprovider
rtk proxy /opt/anaconda3/bin/python3.11 -m pytest h-mad/tests/test_grok_audit_surface_path_scope.py -x -q -p no:cacheprovider
rtk proxy /opt/anaconda3/bin/python3.11 -m pytest h-mad/tests/test_grok_audit_surface_assembler_pin.py -x -q -p no:cacheprovider
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/grok_audit_surface.json
python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/grok_audit_surface.json
for s in $(grep -l '"scripts/hmad-dispatch.sh"\|"scripts/h_mad_assemble_audit.py"\|"scripts/h_mad_grok_containment.py"' h-mad/tests/mutation-specs/*.json h-mad/tests/specs/*.json); do python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors "$s" | tail -1; done
grep -c 'M:PATH-SCOPE-' h-mad/scripts/h_mad_assemble_audit.py
grep -c 'M:PATH-SCOPE-' h-mad/scripts/hmad-dispatch.sh
grep -c '# M:ASSEMBLER-' h-mad/scripts/h_mad_grok_containment.py
/opt/anaconda3/bin/python3.11 -c 'import json; print(len(json.load(open("h-mad/tests/mutation-specs/grok_audit_surface.json"))["mutations"]))'
```

**Acceptance Criteria**:
- [ ] AC-T14d.1: The first command prints a pytest version; the full suite's summary line shows no failure.
- [ ] AC-T14d.2: `MUTATION: ALL_CAUGHT` with `untargeted=0/420` and `crash_kills=0`, and
  `ANCHORS: ANCHORS_OK`, read from the token lines.
- [ ] AC-T14d.3: Every spec the loop names prints `ANCHORS: ANCHORS_OK` (34 files name one of the
  three scripts at `8fd0f637`; the loop re-derives the set).
- [ ] AC-T14d.4: The three marker counts (matching lines) and the row count (rows) are re-derived at
  this Task's sha and reported with their units. This plan expects 2, 5, 19 and 420 (378 at
  `8fd0f637`, read with the last command, plus 6 + 9 + 27); a different figure is reported against
  the Task whose table it contradicts, never silently accepted.
- [ ] AC-T14d.5: Each new module's summary line, run under `-x` as the judge runs it, reads all
  passed in under 40 s (the judge's `JUDGE_BUDGET_S`): 20 passed for the path-scope module and 32 for
  the assembler-pin module.

**Dependencies on other tasks**: Tasks 14a–14c.

---

## Task 15: the live sequence after S0c (operator)

**Production files**: none on `main` (calibration data goes only to `calibration/grok-audit-surface`, by Task 6's `commit-data`)
**Test files**: none
**Task shape**: `operational` — runs the probe, the wrapper and the two S0c scripts live, in design
D8's "Order of a run"; not CI.

**Description**: S0b and the first S1 have run (calibration sha
`ab2c85dc2e25be31dcc13740ee9e71a0703d8cc7`; first smoke commit `f7520e72`, superseded by the re-smoke,
spec AC-1.9). The 2026-10-20 S2 run that followed is incident evidence only (the incident record
`docs/03-analysis/grok-audit-surface.incident-2026-10-20-grok-root-escape.md`); it stays in
`$KEEP/run-ab2c85dc2e25/`, is never committed to the branch and is never scored, and its one later
reader is the step-10 positive control. Task 0's `exec agy` tracer has run; its kept reading
(`$KEEP/agy-tracer/reading.txt`) showed the given spelling logged, so D8's agy selection, re-derived
in design v1.6 for roots under `$RUN/roots/`, is used as written and AC-T0.3 does not fire.

The operator runs the steps below from a `main` clone at the S0c merge, each step entered only on the
previous step's token line, read from stdout or from a token file, never from `$?`. Every
`GROK-CANARY:`, `QUARANTINE:`, `TOOLSCAN:` and `ASSEMBLER:` token is read by
`python3 h-mad/scripts/h_mad_grok_containment.py require`, with `--verb` naming the token's verb
(`quarantine`, `grok-canary`, `toolscan` or `assembler`; design v1.13 D8, D21) and `--token-file` the
file the token was teed to, and the run stops at any `REQUIRE: STOP`. Every `python3 h-mad/scripts/…`
and `h-mad/bin/hmad-dispatch` command runs from the same repository root, so the containment
module's `SELF_DIR` is the directory `_cmd_audit_cycle` uses as `$here` (D21), and no commit is made
on this checkout between the two assembler readings (D21 residual (4); `commit-data` moves only the
calibration ref, never `HEAD`). Variables: `KEEP="$HOME/.local/state/h-mad/grok-audit-surface"`;
`CAL_SHA=ab2c85dc2e25be31dcc13740ee9e71a0703d8cc7`; `CAL12=${CAL_SHA:0:12}`;
`LIST_SHA=$(git rev-parse HEAD)` on `main`. Every command block is D8's, with its template slots filled
from these variables and from the `ROOT: READY` line of the root it names.

0. **Entry.** S0c is merged to `main` (Task 30's evidence file is on `main` and Task 29's tokens are
   green at the merge), and Tasks 14a–14c are merged to `main` with Task 14d's tokens green at the
   merge (design "Implementation Order" item 12: run 3 starts only after that, in a new run directory).
1. **Setup**, exactly D8 "Setup": `RUN="$KEEP/run-$CAL12-$(date -u +%Y%m%dT%H%M%SZ)"` made with a plain `mkdir` (a
   name that exists stops the run), `READING="$RUN/data/runs/${RUN##*/}"`, the one `mkdir -p` of
   `$RUN/roots`, `$RUN/work`, `$RUN/stem`, `$RUN/canary`, `$RUN/assembler` (design v1.13),
   `$READING/resmoke` and `$READING/s2`, then
   `$RUN/run.txt` and its two copies into `$READING/resmoke/run.txt` and `$READING/s2/run.txt`.
2. **The codex last-message tracer pair** (D16): the control
   `h-mad/bin/hmad-dispatch exec codex "$RUN/work/tracer-prompt.txt" --cd "$RUN/roots" --log "$(mktemp -d)/codex-control.log"`
   and the treatment, the same command with `--log "$RUN/work/codex-treatment.log"`, the prompt a
   one-line file; both stdouts and stderrs kept under `$RUN/work/`. Each passes when its stdout holds
   the reply and its stderr no `EMPTY final message` line. The cell of D16's four-cell table it lands
   in decides the shape: pass/pass is the codex shape; every other cell is the codex-unavailable
   shape (`--surfaces agy,grok` in S2), and only pass/fail is attributed to the last-message placement
   (spec AC-11.2's instruction applies to that cell). A failed treatment is not a stop.
3. **The first quarantine**: `python3 h-mad/scripts/h_mad_grok_containment.py quarantine | tee "$RUN/work/quarantine-1.txt"`, then
   `require --verb quarantine --token-file "$RUN/work/quarantine-1.txt"`: `REQUIRE: OK`.
4. **The canary**, the run's first grok call:
   `h-mad/bin/hmad-dispatch grok-canary --run-dir "$RUN" | tee "$RUN/canary/stdout.txt"`, then
   `require --verb grok-canary --token-file "$RUN/canary/stdout.txt"`: `REQUIRE: OK`. Then copy
   `$RUN/canary/` into `$READING/resmoke/canary/` (D18).
5. **The re-smoke** (AC-1.9), `--doc d1 --purpose s1`, in one root under `$RUN/roots/`: first the
   start reading of the assembler pin (D8 step 4, D21),
   `python3 h-mad/scripts/h_mad_grok_containment.py assembler-read > "$RUN/assembler/start.txt"`,
   before the versions and the first re-smoke cycle; then versions
   (D8 "Versions", into `$READING/resmoke/versions.txt`); the grok cycle (`--cycle 1 --passes 1
   --surfaces grok`, `--root-record`), its `record-cycle` into `$READING/resmoke/grok`,
   `wall_seconds.txt` and `resolved_model.txt`, then its scan, `h_mad_tool_calls.py scan --surface grok`
   into `$READING/resmoke/grok/p1.scan.txt`, read by `require --verb toolscan --halt-file "$RUN/HALT"`;
   the agy cycle (`--cycle 2`, `--reset "${ROOT_1:?}"`), with D8's agy provenance block placed as carry
   6 places it (the `cli-*.log` listing right after this cycle block's `STEM=…; mkdir -p "$STEM"` line
   and before its `build-root` line; the selection after its `record-cycle` and before the codex block);
   the codex cycle (`--cycle 3`, `--reset`) only when `command -v codex` succeeds and step 2 landed in
   pass/pass. Every cycle's `audit-cycle` carries `--halt-file "$RUN/HALT"` and
   `--pass-root "$ROOT_1"` (D8's cycle block, the re-smoke included; `--pass-root` is what turns
   D21's `--path-scope` switch on) and omits `--timeout`. An `audit-cycle` whose last stdout line is
   `REQUIRE: STOP reason=path_scope_missing:p1` has appended that reason to `$RUN/HALT`: the run is
   halted, as in step 9.
6. **The smoke**: `python3 "$PROBE" smoke --data "$READING/resmoke"`. On `SMOKE: UNREADABLE`, restore
   the named input and derive again (a wrong-file Effort item is not cleared that way, carry 10, and
   needs a new run). `SMOKE: FAIL` takes the smoke-failure branch after step 7 (Task 16 publishes;
   steps 8–11 do not run). On that branch the end reading follows the last re-smoke cycle (D21):
   `python3 h-mad/scripts/h_mad_grok_containment.py assembler-read > "$RUN/assembler/end.txt"`, then
   `python3 h-mad/scripts/h_mad_grok_containment.py assembler-check --start "$RUN/assembler/start.txt" --end "$RUN/assembler/end.txt" --reading "$READING" --stems "$RUN/stem" --stages resmoke > "$RUN/assembler/check.txt"`,
   then `python3 h-mad/scripts/h_mad_grok_containment.py require --verb assembler --token-file "$RUN/assembler/check.txt"`.
   Task 16 publishes the smoke-failure doc only on `REQUIRE: OK` (design v1.14 D15); on
   `REQUIRE: STOP` the run is not a reading and goes only to an incident record on `main`, with the
   readings and the `ASSEMBLER:` line verbatim.
7. **The re-smoke commit**, on `SMOKE: PASS` or `SMOKE: FAIL`: run the calibration-ref precondition
   below, then `git fetch --no-tags origin +refs/heads/calibration/grok-audit-surface:refs/heads/calibration/grok-audit-surface`,
   `TIP=$(git rev-parse refs/heads/calibration/grok-audit-surface)`, confirm
   `git ls-remote origin refs/heads/calibration/grok-audit-surface` prints `$TIP`, then
   `python3 "$PROBE" commit-data --repo . --parent "$TIP" --src "$RUN/data" --message "grok-audit-surface re-smoke ${RUN##*/}"` while
   `$READING` holds only `resmoke/` and `s2/run.txt`; push without force; confirm with `ls-remote`.
   Its parent is the confirmed tip (for the first run, `f7520e72`), never a hard-wired sha (D9).
   This commit is the smoke commit every later reading cites (`--smoke-sha`).
8. **The second quarantine**, only on `SMOKE: PASS` and step 5's `REQUIRE: OK` for the grok scan:
   as step 3, into `$RUN/work/quarantine-2.txt`: `REQUIRE: OK`.
9. **The fresh S2** under `$READING/s2/`: all nine documents, every first cycle `v1`, `--passes 3
   --surfaces codex,agy,grok` (or `--passes 2 --surfaces agy,grok` on the codex-unavailable shape, or
   when codex refused the root at the re-smoke); one fresh `build-root --purpose s2v1 --dest-parent "$RUN/roots"`
   per pass, the lines teed to `$STEM.p1.root.txt`, `$STEM.p2.root.txt` and (codex shape)
   `$STEM.p3.root.txt`, their paths passed to `audit-cycle` as `--pass-root` in pass order, with `--project-root "$ROOT_1" --halt-file "$RUN/HALT"`; `record-cycle` with one
   `--pass-root-record` per pass; then the scan of the cycle's grok pass (`p3` on the codex shape,
   `p2` without codex) into `$DEST/p3.scan.txt` (or `$DEST/p2.scan.txt`), read by
   `require --verb toolscan --token-file` on that file `--halt-file "$RUN/HALT"`.
   A `REQUIRE: STOP` halts the run: no further cycle is dispatched (cycles already past
   `audit-cycle`'s launch test finish and are recorded), the run is not scored, and the halt is
   recorded as an incident on `main`; only a new run is a reading. Each AC-3.4 re-dispatch is built the
   same way, `--purpose s2v2`, `--cycle 2`. No third cycle. An `audit-cycle` that prints
   `REQUIRE: STOP reason=path_scope_missing:pN` (N its first pass without the clause) launched nothing and appended that reason to
   `$RUN/HALT` (D21), so it halts the run in the same way.
9a. **The assembler pin** (D8 step 6, D21; spec AC-3.6), after the last S2 cycle's scan and its
    `require`, and before step 10:
    `python3 h-mad/scripts/h_mad_grok_containment.py assembler-read > "$RUN/assembler/end.txt"`, then
    `python3 h-mad/scripts/h_mad_grok_containment.py assembler-check --start "$RUN/assembler/start.txt" --end "$RUN/assembler/end.txt" --reading "$READING" --stems "$RUN/stem" --stages resmoke,s2 > "$RUN/assembler/check.txt"`,
    then `python3 h-mad/scripts/h_mad_grok_containment.py require --verb assembler --token-file "$RUN/assembler/check.txt"`:
    `REQUIRE: OK`. A `REQUIRE: STOP` (`ASSEMBLER: UNPINNED` or `NO_CLAUSE`) means no `extract`, no
    labels and no score sha: the run is evidence only, recorded as an incident on `main` as a halted
    run is, and only a new run on a clean commit that carries the clause is a reading. The three
    files stay in `$RUN/assembler/`, outside the reading namespace, and are never committed to the
    calibration branch.
10. **The positive control** (D19), after the S2 scans and before `extract`:
    `python3 h-mad/scripts/h_mad_tool_calls.py scan --surface grok --log "$KEEP/run-ab2c85dc2e25/data/s2/d5/v1/p3.log"`
    with `--root` the `path=` of that cycle's recorded `root.txt`, `--checkout` the live checkout
    (`checkout=` of `$RUN/run.txt`) and `--home "$HOME"`, into `$RUN/work/positive-control.txt`. Its
    `checkout=` must be above 0. A control that reads 0 makes the scan invalid: no scan line of the run
    is published, the scan is repaired through TDD and run again.
11. **Extract, labels, score sha**: `extract --repo . --base-sha <step-7 smoke commit> --work-dir "$RUN/work" --s2 "$READING/s2" --shuffle-seed "$SEED" --out "$READING"`,
    with `SEED=$(od -An -N4 -tu4 /dev/urandom | tr -d ' ')` drawn once and recorded by `extract.txt`;
    hand labels of every must and should finding into `$READING/labels.jsonl` by a labeller without the
    key; the calibration-ref precondition, then the fetch, `TIP` and confirm as in step 7, then
    `commit-data --parent "$TIP" --src "$RUN/data"` (the `resmoke/` files are identical re-adds); push;
    confirm. That commit is the score sha.

**The calibration-ref precondition (design rev4's Phase-5 note).** The forced fetch in steps 7 and 11
overwrites the local branch ref, so a local ref ahead of origin (an unpushed commit-data) would be
discarded. Before each fetch:

```bash
L=$(git rev-parse -q --verify refs/heads/calibration/grok-audit-surface || true)
O=$(git ls-remote origin refs/heads/calibration/grok-audit-surface | awk '{print $1}')
[ -n "$O" ] || { echo "STOP: no calibration ref on origin"; exit 1; }
[ -z "$L" ] || [ "$L" = "$O" ] || { echo "STOP: local calibration ref $L differs from origin $O"; exit 1; }
```

A `STOP` here is resolved by pushing the local commit (when origin's tip is its ancestor) or by an
operator decision, never by the forced fetch.

**Acceptance Criteria**:
- [ ] AC-T15.1: Every step's entry condition is read from the previous step's token line or from a
  `REQUIRE:` line, never `$?`; the canary, both quarantines, every grok scan and the `ASSEMBLER:`
  token are read by `require`.
- [ ] AC-T15.2: The shas Task 16 needs (calibration, re-smoke commit, score sha or its absence, list
  commit and blob, the S0c merge on `main`) are each confirmed by `git ls-remote` or by the
  `ROOT: READY` line that printed them.
- [ ] AC-T15.3: The calibration-ref precondition printed no `STOP` before each forced fetch.
- [ ] AC-T15.4: On a halt, `$RUN/HALT` exists, no cycle launched after it (each later `audit-cycle`
  printed `REQUIRE: STOP reason=halt_file`), no `extract` or score sha exists for the run, and the
  incident record is on `main`.
- [ ] AC-T15.5: The positive control's token line is kept beside the run's scan lines, with
  `checkout=` above 0, before any scan line is published.
- [ ] AC-T15.6 (design v1.13 D21): `$RUN/assembler/start.txt` was written before the versions line,
  `end.txt` after the last S2 cycle's `require` (or, on a smoke failure, after the last re-smoke
  cycle), `assembler-check` ran with `--stems "$RUN/stem"`, and `require --verb assembler` printed
  `REQUIRE: OK` before `extract` ran (scored outcome) or before the doc was published (smoke failure).
  Every re-smoke and S2 `audit-cycle` carried `--pass-root`.

**Dependencies on other tasks**: Tasks 0–14 (merged); Tasks 18–28 merged to `main` with Task 29's
tokens green and Task 30's evidence file on `main`; Tasks 14a–14c merged to `main` with Task 14d's
tokens green.

---

## Task 16: S3 publish

**Production files**: `docs/03-analysis/grok-audit-surface.measurement.md` (create),
`h-mad/references/grok-runtime.md`, `h-mad/SKILL.md`, `h-mad/tests/mutation-specs/grok_audit_surface.json` (K2 re-anchor; K6 and K7 added on every outcome; K4 and K5 added on MISS or INCONCLUSIVE)
**Test file**: `h-mad/tests/test_grok_audit_surface_docs.py` (extend)
**Task shape**: `new-behaviour`

**Description**: On every outcome that publishes (`SMOKE: FAIL`, or a non-UNREADABLE `SEEDSCORE:`):
`main-leak` runs before the measurement doc is committed (without `--score-sha` on a smoke failure);
on a scored outcome `rescore` runs from a `main` checkout and its `SEEDSCORE:` line is the one
published. The measurement doc holds D15's contents, including the runbook as run (with Task 15's
carry-6 placement and the carry-10 note beside the UNREADABLE remedy), Task 0's tracer reading as a
Reading beside `T` and its `pwd -P` form, and the `GROK-BINARY:` line naming the version that ran
(operator decision D4: no phase document names a target version). `grok-runtime.md` §"Version and
compatibility" gains the AC-1.5 sentence (scored outcome) or the AC-1.8 sentence (smoke failure);
"These mappings were checked against grok 1.0.41." stays unchanged. SKILL.md's two AC-6.2 sites
change per D14's branch for the outcome; on INCONCLUSIVE both sites carry the measured fractions,
"not decidable on this seed set", the score's one `reason=` and "fallback-only" (design v1.10). K2's
`find` is re-pointed to the S3 text's remaining `**unmeasured**` clause, same intent and test.

**S0c additions (design D15, v1.6–v1.11).** The doc's stamp publishes the exclusion list's contents
(`git cat-file blob` of the doc's stated `list_blob=` value, verbatim, in a fenced block). Its re-run command
is `python3 docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py rescore --repo . --calibration-sha "$CAL_SHA" --smoke-sha "$SMOKE_SHA" --score-sha "$SCORE_SHA" --run-id "${RUN##*/}" --work-dir "$WORK"`
(on a smoke failure, `main-leak` without `--score-sha`, with `--work-dir`), where `SMOKE_SHA` is the
re-smoke commit, `SCORE_SHA` the score sha and `WORK` any existing directory outside system temp and
outside every git work tree. On every published outcome it cites the incident record
`docs/03-analysis/grok-audit-surface.incident-2026-10-20-grok-root-escape.md` with the sentence that the
2026-10-20 S2 run is incident evidence and is not scored, cites `f7520e72` as the superseded smoke,
and carries the first `QUARANTINE: VERIFIED` line, the canary's `GROK-CANARY:` and `grok.txt` lines,
the re-smoke grok pass's `TOOLSCAN:` line, the codex tracer pair's four outputs and its cell, and the
AC-2.6 residual (3) per surface. On a scored outcome it adds the second `QUARANTINE: VERIFIED` line, the
positive-control `TOOLSCAN:` line, every `CONTAINMENT:` line and the codex and agy passes with
`checkout=` above 0, by name; on a smoke failure it states, in one line,
`Not run: second quarantine, fresh S2, positive control, CONTAINMENT lines (smoke failed)`. A halted
run publishes no measurement doc (Task 15 AC-T15.4).

**D21 additions (design v1.14 D15; spec AC-3.6, AC-3.9, FR-6).** The doc is published only from a
run whose `ASSEMBLER:` token is `PINNED`, read by `require --verb assembler` (Task 15 step 9a, or step
6 on the smoke-failure shape through its `--stages resmoke` gate). An `UNPINNED` or `NO_CLAUSE` run is
not a reading: it has no measurement doc and no stamp, and its readings and token go only to an
incident record on `main`. On every published outcome the stamp carries the assembler commit and
the prompt delta:
- the two `ASSEMBLER-READING:` lines (`$RUN/assembler/start.txt`, `end.txt`) and the `ASSEMBLER:`
  token (`$RUN/assembler/check.txt`), verbatim;
- the stamp line `assembler=` followed by the 40-hex `sha=` value copied from the `ASSEMBLER: PINNED`
  token;
- beside it, this sentence, verbatim: "The calibration prompt is the production prompt plus exactly
  the path-scope clause below, inserted once at the head of the audit body; production grok legs do
  not receive it, and whether a production grok leg without it behaves the same is not measured
  (spec AC-3.9 residual (3))", followed by the clause, verbatim, as one line in a fenced `text`
  block, equal byte for byte to `PATH_SCOPE_CLAUSE` at the stamped assembler sha (the text under
  "Shared literal" above Task 14a).

**Tests**: every outcome (6): `test_both_unmeasured_sites_point_to_the_measurement_doc`,
`test_measurement_doc_states_the_transfer_residual`, `test_unmeasured_sites_match_the_outcome`,
`test_grok_runtime_states_the_outcome_sentence`, and, from design v1.8 and v1.10,
`test_measurement_doc_on_smoke_failure_marks_later_stages_not_run` (on a smoke failure: the `Not run:`
line, and no `CONTAINMENT:` or `SEEDSCORE:` line; on a scored outcome: the second group's items and no
`Not run:` line) and `test_measurement_doc_publishes_the_exclusion_list` (the fenced block equals, byte
for byte, `git cat-file blob` of the doc's stated `list_blob`). `test_grok_runtime_states_the_outcome_sentence` reads §"Version and compatibility" of
`h-mad/references/grok-runtime.md` with `titled_section`, whitespace collapsed. On a scored
outcome it asserts the AC-1.5 sentence naming the version read from the measurement doc's
`GROK-BINARY:` line by D14's slot rule and naming `docs/03-analysis/grok-audit-surface.measurement.md`;
on a smoke failure it asserts the AC-1.8 sentence instead. **It also asserts the other branch's
sentence is absent** (axis: each outcome sentence's presence and its absence). On a scored outcome
the AC-1.8 smoke-failure sentence is absent; on a smoke failure the AC-1.5 "re-smoked" sentence is
absent. Spec AC-1.8 says the AC-1.5 sentence "does **not** ship", and AC-1.5 says it ships only
when the smoke passes and the score is not `UNREADABLE`. On every outcome it asserts that
"These mappings were checked against grok 1.0.41." is present, unchanged. On MISS or INCONCLUSIVE
only (1 more): `test_never_gate_section_keeps_two_surface_routing_off_pass`.

**Acceptance Criteria**:
- [ ] AC-T16.1: The `MAINLEAK: CLEAN` line in the doc names the commit it scanned.
- [ ] AC-T16.2: `test_unmeasured_sites_match_the_outcome` fails when the doc has no `GROK-BINARY:` line,
  when it reads `GROK-BINARY: unrecorded`, or when D14's slot rule yields no version on a smoke failure.
- [ ] AC-T16.3: `--check-anchors` reads `ANCHORS: ANCHORS_OK` after the K2 re-anchor, and the spec run
  reads `MUTATION: ALL_CAUGHT` with `crash_kills=0` and `untargeted=0/422` on PASS or a smoke
  failure (K6 and K7 below), or `untargeted=0/424` on MISS or INCONCLUSIVE (K4, K5, K6 and K7 below).
  The base is 420 after Task 14d (AC-T14d.4); until v1.7 of this plan these read 378 and 380, which
  predate the two post-S0c fix rows and Tasks 14a–14c.
- [ ] AC-T16.5: The doc cites the incident record and the superseded `f7520e72` smoke on every
  published outcome, and its re-run command carries `--run-id` and `--work-dir`.
- [ ] AC-T16.6 (D21): in the doc, `grep -c '^assembler='` prints 1 and `grep -c '^ASSEMBLER-READING: '`
  prints 2 (matching lines); the delta sentence occurs once (whitespace collapsed), and the clause
  line occurs once as a whole line (`grep -cxF` with the clause as the pattern prints 1). These are
  checked by command at Task 16, not by a pinned doc test: design v1.14 names none. The `assembler=`
  value equals the `sha=` of the doc's `ASSEMBLER: PINNED` line, and no `assembler=unpinned` line exists.
- [ ] AC-T16.4 (MISS or INCONCLUSIVE only; audit cycle 1): before K4 and K5 are added,
  `test_never_gate_section_keeps_two_surface_routing_off_pass` is observed failing against each of
  the two mutated texts and passing on the restored text. The harness run is that observation: each
  row is required green before it is applied and failing after.

**RED split**: PASS, MISS, INCONCLUSIVE or smoke failure: the 6 every-outcome tests F
(`test_grok_runtime_states_the_outcome_sentence` fails at RED because the AC-1.5 or AC-1.8
sentence is absent; that RED is the negative observation for its outcome-sentence assertion; the two
measurement-doc tests fail because the doc is absent). MISS or
INCONCLUSIVE adds `test_never_gate_section_keeps_two_surface_routing_off_pass`, which is P at RED (the
section is unchanged at S0), so 7 nodes, 6 F, 1 P; on PASS or a smoke failure, 6 nodes, 6 F, 0 P.
Because that one test is P at RED, a RED run never shows that it can fail. K4 and K5 show it (axis:
a test that is P at RED needs a negative run).

**Mutation rows**: on every outcome, 2 new rows:
- K6. Its target's host-mapping assertion passes at RED (the 1.0.41 sentence is there at S0), so K6
  is the negative observation for that assertion.
- K7. Its `replace` appends the other branch's sentence after the 1.0.41 sentence (the AC-1.8
  sentence on a scored outcome, the AC-1.5 sentence on a smoke failure), so it is the negative
  observation for the absence assertion. Its `replace` text is written at Task 16 for the branch
  that shipped.
K2 is re-anchored, not added. On MISS or INCONCLUSIVE, 2 more rows, K4 and K5, one per property
the off-PASS test asserts:

| name | file | find | replace | test |
|---|---|---|---|---|
| `never-gate-three-surface-leak` (K4) | `SKILL.md` | ``When Codex is unavailable and `fallback_agent=grok`, use `--surfaces agy,grok` `` | the same with `--surfaces codex,agy,grok` | `tests/test_grok_audit_surface_docs.py::test_never_gate_section_keeps_two_surface_routing_off_pass` |
| `never-gate-family-sentence-dropped` (K5) | `SKILL.md` | `that is three reports, of which two share a model family` | `that is three reports, of which two share a vendor` | `tests/test_grok_audit_surface_docs.py::test_never_gate_section_keeps_two_surface_routing_off_pass` |
| `grok-runtime-host-sentence-changed` (K6) | `references/grok-runtime.md` | `These mappings were checked against grok 1.0.41.` | `These mappings were checked against grok 1.0.40.` | `tests/test_grok_audit_surface_docs.py::test_grok_runtime_states_the_outcome_sentence` |
| `grok-runtime-other-branch-sentence-added` (K7) | `references/grok-runtime.md` | `These mappings were checked against grok 1.0.41.` | the same followed by one space and the other branch's sentence | `tests/test_grok_audit_surface_docs.py::test_grok_runtime_states_the_outcome_sentence` |

K4's find is K3's (1 matching line in `h-mad/SKILL.md` at `30917a1a`). K6's find has 1 matching line in
`h-mad/references/grok-runtime.md` at `30917a1a` (`grep -cF`). K5's find is on one line (line
2024 at `30917a1a`, 1 matching line by `grep -cF`); the test collapses whitespace, so a change to
either half of the sentence fails it.

**Dependencies on other tasks**: Task 15.

---

## Task 17: S4 route (PASS only)

**Production file**: `h-mad/SKILL.md`
**Test file**: `h-mad/tests/test_grok_audit_surface_docs.py` (extend)
**Task shape**: `new-behaviour`

**Entry gate (plan v1.11 S4 row; spec FR-11 "Gating").** All three, each read from its record: S0c
merged to `main` (Task 30's evidence file on `main`); a fresh S2 run under its own reading
namespace that was **not halted** (no `$RUN/HALT`, and every grok scan of the run read `REQUIRE: OK`);
and that run **scored from its own score sha** to a `SEEDSCORE:` token by `rescore --run-id` (Task 16).
No reading from the 2026-10-20 run and no reading taken before S0c merged opens this Task.

**Description**: Runs only when Task 16 published `SEEDSCORE: PASS` under that gate. D14's AC-7.1 (the
"**Which two surfaces …**" paragraph of §"Never gate on one audit pass" names
`--surfaces codex,agy,grok` and points to the measurement doc; the "three reports, of which two share a
model family" sentence is reworded per AC-7.1), AC-7.2 (D14's availability-fallback words, verbatim),
AC-8.3 (D14's falsification sentence, verbatim, at the AC-7.1 text). Both AC-8.3 targets are heading
lines of `h-mad/SKILL.md` at `30917a1a` (`## Verifying a review finding before acting on it`,
`### Record a rejected finding in the rejections ledger, never in a gated document`).

**Tests** (4): `test_never_gate_section_names_three_surface_first_gate`,
`test_never_gate_section_names_grok_falsification`,
`test_never_gate_section_names_the_grok_unavailable_fallback`,
`test_never_gate_section_names_the_twice_unverified_grok_fallback`.

**Acceptance Criteria**:
- [ ] AC-T17.1: The four tests pass; `tests/test_grok_fallback_docs.py` still passes (K3's pin
  survives the edit, and `--check-anchors` reads `ANCHORS: ANCHORS_OK`).

**RED split**: 4 nodes; 4 F, 0 P.

**Mutation rows**: none.

**Dependencies on other tasks**: Task 30 (S0c merged), Task 15 (a fresh S2 not halted) and Task 16
with `SEEDSCORE: PASS` scored from that run's score sha.

---

## S0c: Tasks 18–30 (FR-11 containment, AC-3.8, AC-6.6, `out_of_root`)

S0c runs on the S0c branch, cut from `main` at Phase 5c. **The 5c baseline expectation:** the branch
point's full suite is green, and its collection count is the floor. At `9628c857` the collection read
`7007 tests collected` (`rtk proxy /opt/anaconda3/bin/python3.11 -m pytest h-mad/tests --collect-only -q -p no:cacheprovider | tail -1`,
node ids), which equals plan R1's reading at `e3d84865` because `h-mad/` did not change between the two;
5c re-measures it at the branch point, and that reading, not this one, is the floor. Tasks 18–28 add
219 collected node ids (218 in the feature's own modules, listed per Task, plus the
`test_no_verb_dies_on_an_unbound_variable[grok-canary]` id that Task 23's new verb adds to
`h-mad/tests/test_hmad_dispatch_missing_positionals.py`) and remove 4 (the four S0 tests Tasks 24 and 26
rename), so after Task 28 the collection is the floor plus 215, and at every GREEN in between it is at
least the floor plus the ids added so far minus the ids removed so far. Every Task runs the full suite
per the Rules, from the S0c branch's worktree.

---

## Task 18: `exec grok`'s profile

**Production file**: `h-mad/scripts/hmad-dispatch.sh` (`_cmd_exec`, its option loop and usage comment)
**Test files**: `h-mad/tests/test_grok_audit_surface_wrapper.py` (extend),
`h-mad/tests/test_hmad_dispatch_exec_grok.py` (modify one parametrize case)
**Task shape**: `new-behaviour`

**Description**: D16's profile rules, in `_cmd_exec`, grok only, each marked line carrying its `# M:`
comment (the file's convention, as `# M:STEM-DIR` at line 3601 at `9628c857`):
1. The option loop gains `--allow-weaker-sandbox` (no value). Given with codex or agy it is an unknown
   option: `_unknown_opt exec --allow-weaker-sandbox`, exit 2 (`# M:GROK-OVERRIDE-GROK-ONLY`).
2. After option parsing and before anything is created or launched, on the value **as given** (before
   the default applies, so the two alternatives stay distinct): the flag with no `--sandbox` exits 2
   (`# M:GROK-SANDBOX-OVERRIDE-ALONE`), and the flag with `--sandbox strict` exits 2
   (`# M:GROK-SANDBOX-OVERRIDE-STRICT`), each with the stderr line
   `hmad-dispatch: exec: --allow-weaker-sandbox needs a --sandbox weaker than strict` (the design names
   no text for this refusal; this plan names it). A value other than `strict` without the flag exits 2
   with D16's line, the given value expanded where D16 writes its slot:
   `hmad-dispatch: exec: grok --sandbox ${sandbox} is weaker than strict or unknown; pass --allow-weaker-sandbox to run it, and it is recorded`
   (`# M:GROK-SANDBOX-WEAKER`).
3. An empty `sandbox` becomes `strict` (`# M:GROK-SANDBOX-DEFAULT`), and the line at `9628c857`
   `    [ -n "$sandbox" ] && gargs+=(--sandbox "$sandbox")` becomes an unconditional
   `gargs+=(--sandbox "$sandbox")` (`# M:GROK-SANDBOX-ARG`).
4. `child_env=(-u GROK_SANDBOX "${child_env[@]}")` in the grok branch (`# M:GROK-SANDBOX-ENV`):
   `env` takes `-u` options before assignments, and `child_env` already holds the `-u CLAUDE*` entries
   and then `HPW_AGENT_BACKEND=${HPW_AGENT_BACKEND:-claude}` (lines 3181–3192 at `9628c857`), so the new entry goes first. The launch
   line `"$wait_secs" env "${child_env[@]}" grok "${gargs[@]}"` is not edited (Rules, "Lines other
   specs anchor on").
5. Before the launch, `printf 'GROK-PROFILE: profile=%s origin=%s\n' "$sandbox" "$origin" > "$log.profile"`
   with `origin` `override` exactly when the flag was given (`# M:GROK-PROFILE-RECORD`); with an
   automatic log the record is removed with the log.

`exec-pane` is unchanged: `_cmd_exec_pane` still accepts only `codex|agy` (line 3910 at `9628c857`).

**Tests** (9 functions, 11 node ids), each with a stub `grok` on `PATH` that records its argv and
environment to a file:
- `test_exec_grok_defaults_to_strict` (no `--sandbox`: argv carries `--sandbox strict`; `$log.profile`
  reads `GROK-PROFILE: profile=strict origin=default`).
- `test_exec_grok_explicit_strict` (`--sandbox strict`: the same argv and the same record).
- `test_exec_grok_weaker_profile_refused` (`--sandbox workspace` without the flag: exit 2, D16's stderr
  line, the stub never ran, no `$log.profile`).
- `test_exec_grok_weaker_profile_with_override_is_recorded` (`--sandbox workspace --allow-weaker-sandbox`:
  argv carries `--sandbox workspace`; the record reads `profile=workspace origin=override`).
- `test_exec_grok_override_alone_exits_2`, parametrized `[no-sandbox]` (the flag alone) and `[strict]`
  (the flag with `--sandbox strict`): exit 2, this plan's stderr line, no `unknown option` text, the
  stub never ran.
- `test_exec_grok_child_has_no_grok_sandbox_env` (`GROK_SANDBOX=workspace` in the caller: absent from
  the stub's recorded environment).
- `test_audit_cycle_writes_a_profile_record_per_grok_pass` (an `audit-cycle --passes 2 --surfaces agy,grok`
  through `install_audit_cycle_stubs`: the stem dir's `_p2.log.profile` file reads
  `profile=strict origin=default` and no `_p1.log.profile` file exists).
- `test_exec_pane_still_refuses_grok` (`exec-pane grok <prompt>`: exit 2 and
  `unknown agent 'grok' (expected codex|agy)`).
- `test_allow_weaker_sandbox_is_unknown_for_codex_and_agy` (plan-added: D16 states the behaviour and
  names no test), parametrized `[codex]` and `[agy]`: exit 2 and
  `hmad-dispatch: exec: unknown option '--allow-weaker-sandbox'`, the stub never ran.

**Acceptance Criteria**:
- [ ] AC-T18.1: The 11 ids pass; `h-mad/tests/test_hmad_dispatch.py` and
  `h-mad/tests/test_hmad_dispatch_audit_cycle.py` pass unchanged; `h-mad/tests/test_hmad_dispatch_exec_grok.py`
  passes with only the `[given]` case's options changed (`git diff` of that file touches line 112 only).
- [ ] AC-T18.2: The launch line `"$wait_secs" env "${child_env[@]}" grok "${gargs[@]}"` is byte-identical
  (`grep -cF` prints 1 before and after), and
  `python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/grok_wire_reverts.json`
  reads `ANCHORS: ANCHORS_OK`.

**An existing test this contract supersedes (impl-plan audit cycle 4).** At `b17e1b36`,
`h-mad/tests/test_hmad_dispatch_exec_grok.py::test_exec_grok_translates_model_effort_sandbox[given]`
passes `["--model", "m1", "--effort", "high", "--sandbox", "s1"]` (line 112) and asserts that the stub
was reached and that argv carries `--sandbox s1` (lines 117–121). Under this Task `s1` is a weaker or
unknown profile without the flag, so `exec` exits 2 before launching and the `[given]` id would fail.
Its permissive-profile expectation (an unflagged non-`strict` value is forwarded) is superseded by D16;
its model, effort and sandbox **translation** coverage is kept by changing only that case's options to
`["--model", "m1", "--effort", "high", "--sandbox", "s1", "--allow-weaker-sandbox"]`, so argv still
carries `--model m1`, `--reasoning-effort high` and `--sandbox s1`. The `[none]` id is unchanged and
still passes: it asserts `--sandbox s1` is absent, and argv now carries `--sandbox strict`. The
change lands in the GREEN commit with the code (at RED `--allow-weaker-sandbox` is still an unknown
option, so the new options would fail there), so both ids are regression guards: P before the GREEN
commit with the old options, P after it with the new ones. Collection is unchanged (2 ids). No other
test under `h-mad/tests/` passes a grok `--sandbox` (a `grep -l '\-\-sandbox'` over the files that name
`grok` prints only this module at `b17e1b36`).

**RED split**: 11 ids; 8 F (`defaults_to_strict`, `explicit_strict` (no record at RED),
`weaker_profile_refused`, `weaker_profile_with_override_is_recorded`, both `override_alone` ids (at RED
the flag is an unknown option, whose message the test excludes), `child_has_no_grok_sandbox_env`,
`audit_cycle_writes_a_profile_record_per_grok_pass`); 3 P, regression guards over unchanged
refusals: `test_exec_pane_still_refuses_grok` and both `test_allow_weaker_sandbox_is_unknown_for_codex_and_agy`
ids. Their negative observations are rows 8, 9 and 13 below (axis: a test that is P at RED needs a
negative run).

**Mutation rows** (13; markers 8). `file` is `scripts/hmad-dispatch.sh`; each test is in
`tests/test_grok_audit_surface_wrapper.py`.

| # | name | find | replace | test |
|---|---|---|---|---|
| 1 | `grok-sandbox-default-dropped` | the `# M:GROK-SANDBOX-DEFAULT` line | no default (the line keeps its marker and sets nothing) | `test_exec_grok_defaults_to_strict` |
| 2 | `grok-sandbox-default-forced` | the same | `sandbox="strict"` whatever was given | `test_exec_grok_weaker_profile_with_override_is_recorded` |
| 3 | `grok-sandbox-arg-dropped` | the `# M:GROK-SANDBOX-ARG` line | no `--sandbox` appended | `test_exec_grok_defaults_to_strict` |
| 4 | `grok-sandbox-arg-forced` | the same | `gargs+=(--sandbox strict)` | `test_exec_grok_weaker_profile_with_override_is_recorded` |
| 5 | `grok-sandbox-weaker-disarmed` | the `# M:GROK-SANDBOX-WEAKER` line | its condition never fires | `test_exec_grok_weaker_profile_refused` |
| 6 | `grok-override-alone-disarmed` | the `# M:GROK-SANDBOX-OVERRIDE-ALONE` line | its condition never fires | `test_exec_grok_override_alone_exits_2[no-sandbox]` |
| 7 | `grok-override-strict-disarmed` | the `# M:GROK-SANDBOX-OVERRIDE-STRICT` line | its condition never fires | `test_exec_grok_override_alone_exits_2[strict]` |
| 8 | `grok-only-flag-codex` | the `# M:GROK-OVERRIDE-GROK-ONLY` line | the flag accepted for every agent | `test_allow_weaker_sandbox_is_unknown_for_codex_and_agy[codex]` |
| 9 | `grok-only-flag-agy` | the same | the same | `test_allow_weaker_sandbox_is_unknown_for_codex_and_agy[agy]` |
| 10 | `grok-sandbox-env-dropped` | the `# M:GROK-SANDBOX-ENV` line | `child_env` unchanged | `test_exec_grok_child_has_no_grok_sandbox_env` |
| 11 | `grok-profile-origin-forced` | the `# M:GROK-PROFILE-RECORD` line | `origin=default` written always | `test_exec_grok_weaker_profile_with_override_is_recorded` |
| 12 | `grok-profile-record-dropped` | the same | no record written | `test_audit_cycle_writes_a_profile_record_per_grok_pass` |
| 13 | `exec-pane-admits-grok` | `    *) echo "hmad-dispatch: exec-pane: unknown agent '$agent' (expected codex\|agy)" >&2; return 2 ;;` | `    *) [ "$agent" = grok ] \|\| { echo "hmad-dispatch: exec-pane: unknown agent '$agent' (expected codex\|agy)" >&2; return 2; } ;;` | `test_exec_pane_still_refuses_grok` |

Each marked line's exact text is written at GREEN and its row's `find` is that line, against the
committed bytes (Rules, "Mutation spec"); row 13's find occurs once at `9628c857` (`grep -cF`, 1 matching
line), a fact Task 29's `--check-anchors` re-reads.

**Dependencies on other tasks**: Task 11 (`install_audit_cycle_stubs`); Tasks 0–14 merged.

---

## Task 19: `exec grok`'s staging directory, prompt and `TMPDIR`; codex and agy beside the log

**Production file**: `h-mad/scripts/hmad-dispatch.sh` (`_cmd_exec`)
**Test file**: `h-mad/tests/test_grok_audit_surface_wrapper.py` (extend)
**Task shape**: `new-behaviour`

**Description**: D16 "Where grok's staging directory is", "Prompt staging", "`TMPDIR` and cleanup"
and codex's last-message file, in `_cmd_exec`:
1. For grok only, before anything is created or launched, `LC_ALL=C env -u GIT_DIR -u GIT_WORK_TREE -u GIT_COMMON_DIR -u GIT_OBJECT_DIRECTORY -u GIT_ALTERNATE_OBJECT_DIRECTORIES git -C "$cd_dir" rev-parse --show-toplevel`
   (`# M:GROK-TMP-ENV`, the environment line). Exit 0: `T` is the printed top level; `pwd -P` of
   `$cd_dir` and of `T` differ → exit 2 (`# M:GROK-TMP-SUBDIR`);
   the same scrubbed environment then runs
   `git -C "$T" check-ignore -q .h-mad/tmp/hmad_exec_grok.probe`, non-zero → exit 2
   (`# M:GROK-TMP-IGNORED`; v1.6, impl-plan audit cycle 3: an inherited `GIT_DIR` would make this call
   consult another repository's ignore rules, so every `git` call on the staging path runs scrubbed,
   both on marked lines); otherwise `mkdir -p "$T/.h-mad/tmp"` and
   `S=$(mktemp -d "$T/.h-mad/tmp/hmad_exec_grok.XXXXXX")` (`# M:GROK-TMP-GIT`). Non-zero with
   `not a git repository` on stderr: `S="$cd_dir/.tmp"`, `mkdir -p` (`# M:GROK-TMP-ROOT`). Any other
   non-zero → exit 2 (`# M:GROK-TMP-GITFAIL`). Each refusal prints its own stderr line and launches
   nothing: `hmad-dispatch: exec: grok staging: --cd is below the git top level`,
   `hmad-dispatch: exec: grok staging: .h-mad/tmp/ is not ignored by git`, and
   `hmad-dispatch: exec: grok staging: git rev-parse failed`, followed by git's own message. Each
   refusal test asserts its own line, so a disarmed guard that falls to a sibling refusal still fails
   its test (the class audit cycle 3 named in Task 23, closed for every exit-2 guard of Tasks 18–23).
2. The bounded prompt: for grok `mktemp "$S/hmad_exec_prompt.XXXXXX"` (`# M:GROK-PROMPT-IN-CD`); for codex
   and agy `mktemp "$(dirname -- "$log")/hmad_exec_prompt.XXXXXX"` (`# M:EXEC-PROMPT-BESIDE-LOG`). The
   existing `mktemp -t hmad_exec_prompt.XXXXXX` line (3142 at `9628c857`) is replaced by those two.
3. `child_env+=("TMPDIR=$S")` in the grok branch (`# M:GROK-TMPDIR`), the launch line unchanged.
4. In a work tree, on every path out of `exec` after `S` is created, `rm -rf -- "$S"`, run only when `S`
   begins with `$T/.h-mad/tmp/hmad_exec_grok.` (`# M:GROK-TMP-RMGUARD`). In an export root `<cd>/.tmp/`
   is not removed (D16).
5. codex's last-message file: `mktemp "$(dirname -- "$log")/hmad_exec_last.XXXXXX"`
   (`# M:EXEC-LAST-BESIDE-LOG`), replacing `mktemp -t hmad_exec_last.XXXXXX` (line 3220 at `9628c857`).
6. The agy `OVERSIZE` branch gains `rm -f "$bounded_prompt"` before its `return 2`
   (`# M:EXEC-PROMPT-OVERSIZE-RM`), and the existing post-run `rm -f "$bounded_prompt"` line gains the
   comment `# M:EXEC-PROMPT-RM` and no other change.

**Tests** (12 functions, 12 node ids). Each work-tree test runs alone in a temporary git repository
whose `.gitignore` holds `.h-mad/*` unless it says otherwise; each export-root test uses a `tmp_path`
directory outside any work tree, first asserting `git -C <it> rev-parse --git-dir` fails:
- `test_exec_grok_stages_the_prompt_in_cd_tmp` (outside a work tree: the `--prompt-file` the stub
  received lies under `<cd>/.tmp/`).
- `test_exec_grok_removes_the_staged_prompt` (that file is gone after `exec`).
- `test_exec_grok_sets_tmpdir_to_cd_tmp` (the stub's `TMPDIR` is `<cd>/.tmp`).
- `test_exec_grok_in_a_work_tree_stages_under_h_mad_tmp` (the `--prompt-file` and `TMPDIR` lie in one
  fresh `<top>/.h-mad/tmp/hmad_exec_grok.*` directory).
- `test_exec_grok_in_a_work_tree_leaves_git_status_unchanged` (`git status --porcelain --untracked-files=all`
  identical before and after a stub that writes a file into `TMPDIR`; the stub's `TMPDIR` began
  `<top>/.h-mad/tmp/hmad_exec_grok.`, which is the test's own positive control, and that directory is
  gone afterwards).
- `test_exec_grok_two_dispatches_get_distinct_staging_dirs`.
- `test_exec_grok_in_a_work_tree_subdirectory_exits_2`.
- `test_exec_grok_staging_not_ignored_exits_2` (no `.h-mad/*` ignore).
- `test_exec_grok_rev_parse_failure_exits_2` (a `git` stub first on `PATH` that exits 128 printing
  `dubious ownership`).
- `test_exec_grok_ignores_an_ambient_git_dir` (`GIT_DIR` set to a second repository whose
  `.gitignore` does **not** ignore `.h-mad/*`, while the `--cd` repository's does: staging still lies
  under the `--cd` repository's `.h-mad/tmp/`, so neither the top-level lookup nor `check-ignore` read
  the ambient repository).
- `test_exec_codex_stages_prompt_and_last_beside_the_log` (a stub `codex` records its prompt path and
  `--output-last-message` path: both in the `--log`'s directory).
- `test_exec_agy_oversize_removes_the_staged_prompt` (an oversize prompt with `TMPDIR` set to a test
  directory: exit 2, and no `hmad_exec_prompt.*` remains beside the log or in that directory).

In each refusal case the stub grok never ran and stderr carries that refusal's own line.

**Acceptance Criteria**:
- [ ] AC-T19.1: The 12 ids pass, each alone; each builds its own repository or directory.
- [ ] AC-T19.2: `grep -c 'mktemp -t hmad_exec_prompt\|mktemp -t hmad_exec_last' h-mad/scripts/hmad-dispatch.sh`
  prints 0 (matching lines); `hmad_exec_log`, `hmad_exec_wt`, `hmad_probe` and `hmad_pane_log` keep
  `mktemp -t` (D16's classification).
- [ ] AC-T19.3: The grok launch line is byte-identical (as AC-T18.2).
- [ ] AC-T19.4: Every `git` call `_cmd_exec` makes to resolve the staging directory carries the scrubbed
  environment: `sed -n '/^_cmd_exec()/,/^}/p' h-mad/scripts/hmad-dispatch.sh | grep -E 'git -C' | grep -vc 'env -u GIT_DIR'`
  prints 0 (matching lines).

**RED split**: 12 ids; 11 F; 1 P, `test_exec_grok_removes_the_staged_prompt`, a regression guard (the
existing `rm -f "$bounded_prompt"` already removes the system-temp prompt at `9628c857`); its negative
observation is row 15.

**Residual, stated exactly.** `# M:GROK-TMP-RMGUARD`'s refusal direction (a damaged `S` that does not
begin with the prefix) has no fixture: the wrapper offers no seam that damages `S`, so row 9 shows
only that removal passes through the guard. A signal between creation and removal leaves `S` (D16).

**Mutation rows** (16; markers 13). `file` is `scripts/hmad-dispatch.sh`; tests in
`tests/test_grok_audit_surface_wrapper.py`.

| # | name | marker | replace | test |
|---|---|---|---|---|
| 1 | `grok-tmp-subdir-disarmed` | `# M:GROK-TMP-SUBDIR` | condition never fires | `test_exec_grok_in_a_work_tree_subdirectory_exits_2` |
| 2 | `grok-tmp-ignored-disarmed` | `# M:GROK-TMP-IGNORED` | condition never fires | `test_exec_grok_staging_not_ignored_exits_2` |
| 3 | `grok-tmp-gitfail-disarmed` | `# M:GROK-TMP-GITFAIL` | the other non-zero exits take the export-root branch | `test_exec_grok_rev_parse_failure_exits_2` |
| 4 | `grok-tmp-git-severed` | `# M:GROK-TMP-GIT` | `S="$cd_dir/.tmp"` | `test_exec_grok_in_a_work_tree_stages_under_h_mad_tmp` |
| 5 | `grok-tmp-git-shared` | `# M:GROK-TMP-GIT` | one fixed `$T/.h-mad/tmp/hmad_exec_grok.shared` (made with `mkdir -p`) | `test_exec_grok_two_dispatches_get_distinct_staging_dirs` |
| 6 | `grok-tmp-root-severed` | `# M:GROK-TMP-ROOT` | `S=$(mktemp -d)` (system temp) | `test_exec_grok_stages_the_prompt_in_cd_tmp` |
| 7 | `grok-tmp-env-ambient` | `# M:GROK-TMP-ENV` | `-u GIT_DIR` dropped | `test_exec_grok_ignores_an_ambient_git_dir` |
| 7b | `grok-tmp-ignored-env-ambient` | `# M:GROK-TMP-IGNORED` | `-u GIT_DIR` dropped from the `check-ignore` call | `test_exec_grok_ignores_an_ambient_git_dir` |
| 8 | `grok-prompt-in-cd-severed` | `# M:GROK-PROMPT-IN-CD` | `mktemp -t hmad_exec_prompt.XXXXXX` | `test_exec_grok_stages_the_prompt_in_cd_tmp` |
| 9 | `grok-tmp-rmguard-never` | `# M:GROK-TMP-RMGUARD` | the guard never passes | `test_exec_grok_in_a_work_tree_leaves_git_status_unchanged` |
| 10 | `grok-tmpdir-dropped` | `# M:GROK-TMPDIR` | no `TMPDIR` entry | `test_exec_grok_sets_tmpdir_to_cd_tmp` |
| 11 | `grok-tmpdir-forced` | `# M:GROK-TMPDIR` | `TMPDIR=/tmp` | `test_exec_grok_sets_tmpdir_to_cd_tmp` |
| 12 | `exec-prompt-beside-log-severed` | `# M:EXEC-PROMPT-BESIDE-LOG` | `mktemp -t hmad_exec_prompt.XXXXXX` | `test_exec_codex_stages_prompt_and_last_beside_the_log` |
| 13 | `exec-last-beside-log-severed` | `# M:EXEC-LAST-BESIDE-LOG` | `mktemp -t hmad_exec_last.XXXXXX` | `test_exec_codex_stages_prompt_and_last_beside_the_log` |
| 14 | `exec-prompt-oversize-rm-dropped` | `# M:EXEC-PROMPT-OVERSIZE-RM` | the `rm -f` removed (the `return 2` kept) | `test_exec_agy_oversize_removes_the_staged_prompt` |
| 15 | `exec-prompt-rm-dropped` | `# M:EXEC-PROMPT-RM` | the `rm -f` removed | `test_exec_grok_removes_the_staged_prompt` |

**Dependencies on other tasks**: Task 18 (the grok branch's `child_env` edit and the profile record
precede this Task's edits of the same branch).

---

## Task 20: `audit-cycle --pass-root` and `--halt-file`

**Production file**: `h-mad/scripts/hmad-dispatch.sh` (`_cmd_audit_cycle`)
**Test file**: `h-mad/tests/test_grok_audit_surface_wrapper.py` (extend)
**Task shape**: `new-behaviour`

**Description**: D17. `--pass-root <dir>` is repeatable, in pass order; with none given, every
behaviour is as at `9628c857`. With any given, before any assembly, each its own marked check, exit 2
with its own stderr line in the `--surfaces` count check's form, each beginning
`hmad-dispatch: audit-cycle: --pass-root` and ending, per check, `count differs from --passes`,
`is not absolute`, `contains ':'`, `is not an existing directory`, `names one root twice`,
`lies inside another --pass-root` and `first root is not --project-root`:
their number equals `--passes` (`# M:PASS-ROOT-COUNT`); each is absolute (`# M:PASS-ROOT-DIR-ABS`),
holds no `:` (`# M:PASS-ROOT-DIR-COLON`) and is an existing directory (`# M:PASS-ROOT-DIR`), the
three split as `# M:STEM-DIR-ABS`, `# M:STEM-DIR-COLON` and `# M:STEM-DIR-EXISTS` split the stem
dir's check (lines 3602–3604 at `9628c857`); their `pwd -P` forms are pairwise distinct
(`# M:PASS-ROOT-DISTINCT`) and none lies inside another (`# M:PASS-ROOT-NESTED`); the first one's
`pwd -P` form equals `--project-root`'s (`# M:PASS-ROOT-PROJECT`). Pass `i`'s report path becomes
`<pass root i>/.hmad-report/<stem name>_p<i>.report.md` on a new line after the existing
`report[$i]=` line, with `.hmad-report/` created before assembly (`# M:PASS-ROOT-REPORT`). The
per-pass `--cd` is a new first line inside the pass's `( … ) &` subshell,
`root="${pass_root[$i]:-$root}"` (`# M:PASS-ROOT-CD`), so the launch line
`      _cmd_exec "${agent[$i]}" "${prompt[$i]}" --cd "$root" \` stays byte-identical (Rules) and the
reassignment cannot reach the parent's `root`, which assembly and collection keep using.

`--halt-file <path>`: immediately before the pass-launch loop, after assembly and the divergence
check, the file is tested (`# M:AUDIT-HALT-GATE`). If it exists, no pass is launched and no
`AUDITCYCLE:` line is printed; the last stdout line is exactly `REQUIRE: STOP reason=halt_file`, the
stderr marker is `[H-MAD] audit-cycle halted halt_file=<the given path>`, and the verb returns 0
(`# M:AUDIT-HALT-EXIT`, design v1.10).

**Residual, stated exactly (design rev4's Phase-5 note: `REQUIRE:` has two printers).** After this Task
a `REQUIRE:` line is printed by `h_mad_grok_containment.py require` (Task 22) and by `audit-cycle`'s
halt branch. A consumer that reads a `REQUIRE:` line cannot tell from the prefix which printed it;
the runbook reads `audit-cycle`'s only to see that no cycle launched, and the halt line is pinned to
exactly `REQUIRE: STOP reason=halt_file` by `test_audit_cycle_launches_nothing_after_a_halt`, a reason
`require` never prints (its reasons are a token line or `no_token:` followed by the token file's path).

**Tests** (9 functions, 11 node ids), stub agents through `install_audit_cycle_stubs`:
- `test_pass_roots_give_each_pass_its_own_cd` (three passes: each `exec` gets its own `--cd`, no two
  equal, and the cycle's prompts pass the divergence check).
- `test_pass_root_report_path_lies_in_its_own_root`.
- `test_pass_root_count_mismatch_exits_2`.
- `test_pass_root_not_a_directory_exits_2`, parametrized `[relative]`, `[missing]`, `[colon]`.
- `test_pass_roots_not_distinct_exit_2` (the second root a symlinked spelling of the first).
- `test_pass_root_nested_in_another_exits_2`.
- `test_first_pass_root_not_project_root_exits_2`.
- `test_audit_cycle_launches_nothing_after_a_halt` (the halt file present: no stub agent ran, no
  `AUDITCYCLE:` line, last stdout line exactly `REQUIRE: STOP reason=halt_file`, the marker on stderr,
  exit 0).
- `test_audit_cycle_without_a_halt_file_launches` (`--halt-file` naming an absent path: every pass
  launched and an `AUDITCYCLE:` line printed).

Each exit-2 test also asserts that no assembly ran, that stderr carries no `unknown option` text, and
that stderr carries its own check's line, so a disarmed check that falls to a sibling check (a relative
or colon path then failing the existing-directory check) fails its test (impl-plan audit cycle 3).

**Acceptance Criteria**:
- [ ] AC-T20.1: The 11 ids pass; `h-mad/tests/test_hmad_dispatch_audit_cycle.py` passes unchanged.
- [ ] AC-T20.2: `grep -cF '      _cmd_exec "${agent[$i]}" "${prompt[$i]}" --cd "$root" \' h-mad/scripts/hmad-dispatch.sh`
  prints 1, and `--check-anchors` reads `ANCHORS: ANCHORS_OK` on
  `h-mad/tests/mutation-specs/verb_no_self_invocation.json` and `h-mad/tests/mutation-specs/grok_exec.json`.

**RED split**: 11 ids; 11 F (at RED both flags are unknown options, which every test excludes or
fails on), 0 P.

**Mutation rows** (13; markers 11). `file` `scripts/hmad-dispatch.sh`; tests in
`tests/test_grok_audit_surface_wrapper.py`.

| # | name | marker | replace | test |
|---|---|---|---|---|
| 1 | `pass-root-count-disarmed` | `# M:PASS-ROOT-COUNT` | condition never fires | `test_pass_root_count_mismatch_exits_2` |
| 2 | `pass-root-abs-disarmed` | `# M:PASS-ROOT-DIR-ABS` | condition never fires | `test_pass_root_not_a_directory_exits_2[relative]` |
| 3 | `pass-root-exists-disarmed` | `# M:PASS-ROOT-DIR` | condition never fires | `test_pass_root_not_a_directory_exits_2[missing]` |
| 4 | `pass-root-colon-disarmed` | `# M:PASS-ROOT-DIR-COLON` | condition never fires | `test_pass_root_not_a_directory_exits_2[colon]` |
| 5 | `pass-root-distinct-disarmed` | `# M:PASS-ROOT-DISTINCT` | condition never fires | `test_pass_roots_not_distinct_exit_2` |
| 6 | `pass-root-nested-disarmed` | `# M:PASS-ROOT-NESTED` | condition never fires | `test_pass_root_nested_in_another_exits_2` |
| 7 | `pass-root-project-disarmed` | `# M:PASS-ROOT-PROJECT` | condition never fires | `test_first_pass_root_not_project_root_exits_2` |
| 8 | `pass-root-cd-dropped` | `# M:PASS-ROOT-CD` | `root="$root"` | `test_pass_roots_give_each_pass_its_own_cd` |
| 9 | `pass-root-cd-forced` | `# M:PASS-ROOT-CD` | `root="${pass_root[1]:-$root}"` | `test_pass_roots_give_each_pass_its_own_cd` |
| 10 | `pass-root-report-dropped` | `# M:PASS-ROOT-REPORT` | the report path kept in the stem dir | `test_pass_root_report_path_lies_in_its_own_root` |
| 11 | `audit-halt-gate-disarmed` | `# M:AUDIT-HALT-GATE` | the test never fires | `test_audit_cycle_launches_nothing_after_a_halt` |
| 12 | `audit-halt-gate-always` | `# M:AUDIT-HALT-GATE` | fires whenever `--halt-file` is given | `test_audit_cycle_without_a_halt_file_launches` |
| 13 | `audit-halt-exit-2` | `# M:AUDIT-HALT-EXIT` | `return 2` | `test_audit_cycle_launches_nothing_after_a_halt` |

**Dependencies on other tasks**: Task 18 (the grok pass's profile record is written through the
`exec` this Task launches per root).

---

## Task 21: `h_mad_tool_calls.py`, the out-of-root scan

**Production file**: `h-mad/scripts/h_mad_tool_calls.py` (create)
**Test files**: `h-mad/tests/test_grok_audit_surface_containment.py` (create);
`h-mad/tests/mutation-specs/grok_audit_surface.json` (`command` gains the module after
`tests/test_grok_audit_surface_docs.py`)
**Task shape**: `new-behaviour`

**Description**: D19, stdlib only: the three per-surface parsers (grok NDJSON per line, a line raising
`ValueError` or `RecursionError` skipped and counted in `nonjson`; agy `step_update` calls keyed by
`(conversation_id, step_index)`; codex `exec` blocks after the last dispatch-boundary line, with
`mcp_unmeasured` counted and never scanned), the path grammar (`named_paths(strings, home)`: four
spellings, `~/`, `$HOME/` and `${HOME}/` rewritten to `<home>/`, `posixpath.normpath`), the per-path and
per-call classification, the word per surface, `scan_log(text, surface, *, root, checkout, home, needle_dirs)`,
and the CLI `scan --surface --log --root --checkout --home [--needle-dir]…` ending on its one
`TOOLSCAN:` token line, exit 0 on `CLEAN|OUT_OF_ROOT|UNMEASURED` and 2 on `UNREADABLE`.

**Code structure**:
```python
def named_paths(strings: list[str], home: str) -> list[str]: ...
def classify_path(path: str, surface: str, *, root: str, home: str) -> str: ...  # "inside" | "exempt" | "out"
def scan_log(text: str, surface: str, *, root: str, checkout: str, home: str, needle_dirs: list[str]) -> dict: ...
def main(argv: list[str] | None = None) -> int: ...
```

**Tests** (20 functions, 26 node ids), each with its one trigger alone, in the new containment
module:
- The design's 17: `test_scan_grok_clean`, `test_scan_counts_an_escape_after_a_non_json_line` (the
  on-`main` positive control (1): `out_of_root=1 nonjson=1`), `test_scan_grok_live_checkout_counts_checkout`,
  `test_scan_grok_absent_log_is_unreadable`, `test_scan_grok_no_event_is_unreadable`,
  `test_scan_dev_path_is_exempt`, `test_scan_own_session_dir_is_exempt` and
  `test_scan_grok_skills_is_exempt` (each parametrized `[absolute]`, `[tilde]`, `[home]`, `[brace]`),
  `test_scan_other_session_dir_is_out_of_root`, `test_scan_sessions_dir_itself_is_out_of_root`,
  `test_scan_other_grok_path_is_out_of_root`, `test_scan_mixed_exempt_and_out_of_root_counts_out_of_root`,
  `test_scan_codex_own_looking_session_path_is_out_of_root`, `test_scan_codex_no_call_is_unmeasured`,
  `test_scan_codex_skips_the_prompt_echo`, `test_scan_agy_groups_active_and_done_events`,
  `test_scan_cli_and_function_agree`.
- Plan-added (3), one per alternative D19 names and the design gives no fixture: 
  `test_scan_grok_needle_dir_counts_checkout` (an out-of-root path containing a `--needle-dir` tree
  path: `checkout=1`), `test_scan_grok_unreadable_log_is_unreadable` (`--log` naming a directory:
  `TOOLSCAN: UNREADABLE reason=log_unreadable`), `test_scan_usage_error_is_internal` (an unknown flag:
  `TOOLSCAN: UNREADABLE reason=internal:UsageError`, exit 2, no traceback).

**Acceptance Criteria**:
- [ ] AC-T21.1: The 26 ids pass; each asserts the exact last stdout line and the exit code.
- [ ] AC-T21.2: The spec's `command` equals design v1.11's eight-file list.
- [ ] AC-T21.3: `grep -c 'json.load(' h-mad/scripts/h_mad_tool_calls.py` prints 0 (matching lines): no
  whole-stream JSON reader (D19).

**RED split**: 26 ids; 26 F (the module is absent; the fixture that loads it fails each node), 0 P.

**Mutation rows** (24; markers 21). `file` `scripts/h_mad_tool_calls.py`; tests in
`tests/test_grok_audit_surface_containment.py`. Rows 20, 21 and 23 change the printed reason rather
than disarm (Rules, "S0c scripts").

| # | name | marker | replace | test |
|---|---|---|---|---|
| 1 | `toolscan-inside-disarmed` | `# M:TOOLSCAN-INSIDE` | never inside | `test_scan_grok_clean` |
| 2 | `toolscan-dev-disarmed` | `# M:TOOLSCAN-DEV` | never exempt | `test_scan_dev_path_is_exempt` |
| 3 | `toolscan-own-session-disarmed` | `# M:TOOLSCAN-OWN-SESSION` | never exempt | `test_scan_own_session_dir_is_exempt[absolute]` |
| 4 | `toolscan-spell-tilde-dropped` | `# M:TOOLSCAN-SPELL-TILDE` | `~/` not a path start | `test_scan_own_session_dir_is_exempt[tilde]` |
| 5 | `toolscan-spell-home-dropped` | `# M:TOOLSCAN-SPELL-HOME` | `$HOME/` not a path start | `test_scan_own_session_dir_is_exempt[home]` |
| 6 | `toolscan-spell-brace-dropped` | `# M:TOOLSCAN-SPELL-BRACE` | `${HOME}/` not a path start | `test_scan_own_session_dir_is_exempt[brace]` |
| 7 | `toolscan-skills-disarmed` | `# M:TOOLSCAN-SKILLS` | never exempt | `test_scan_grok_skills_is_exempt[absolute]` |
| 8 | `toolscan-own-session-widened` | `# M:TOOLSCAN-OWN-SESSION` | any path below `<home>/.grok/sessions/` | `test_scan_other_session_dir_is_out_of_root` |
| 9 | `toolscan-own-session-widened-self` | `# M:TOOLSCAN-OWN-SESSION` | at or below `<home>/.grok/sessions` | `test_scan_sessions_dir_itself_is_out_of_root` |
| 10 | `toolscan-grok-only-dropped` | `# M:TOOLSCAN-GROK-ONLY` | the grok-only exemptions for every surface | `test_scan_codex_own_looking_session_path_is_out_of_root` |
| 11 | `toolscan-skills-widened` | `# M:TOOLSCAN-SKILLS` | at or below `<home>/.grok` | `test_scan_other_grok_path_is_out_of_root` |
| 12 | `toolscan-per-call-exempt-first` | `# M:TOOLSCAN-PER-CALL` | `exempt` decided before `out_of_root` | `test_scan_mixed_exempt_and_out_of_root_counts_out_of_root` |
| 13 | `toolscan-word-never-out` | `# M:TOOLSCAN-OUT-OF-ROOT` | the grok word is `CLEAN` whatever the count | `test_scan_counts_an_escape_after_a_non_json_line` |
| 14 | `toolscan-nonjson-ends-scan` | `# M:TOOLSCAN-NONJSON` | a non-JSON line ends the scan | `test_scan_counts_an_escape_after_a_non_json_line` |
| 15 | `toolscan-checkout-disarmed` | `# M:TOOLSCAN-CHECKOUT` | never counted | `test_scan_grok_live_checkout_counts_checkout` |
| 16 | `toolscan-needle-disarmed` | `# M:TOOLSCAN-NEEDLE` | never counted | `test_scan_grok_needle_dir_counts_checkout` |
| 17 | `toolscan-codex-unmeasured-dropped` | `# M:TOOLSCAN-CODEX-UNMEASURED` | `CLEAN calls=0` | `test_scan_codex_no_call_is_unmeasured` |
| 18 | `toolscan-codex-boundary-dropped` | `# M:TOOLSCAN-CODEX-BOUNDARY` | the scan starts at line 1 | `test_scan_codex_skips_the_prompt_echo` |
| 19 | `toolscan-agy-key-dropped` | `# M:TOOLSCAN-AGY-KEY` | each event its own call | `test_scan_agy_groups_active_and_done_events` |
| 20 | `toolscan-log-absent-reason` | `# M:TOOLSCAN-LOG-ABSENT` | prints `log_unreadable` | `test_scan_grok_absent_log_is_unreadable` |
| 21 | `toolscan-log-unreadable-reason` | `# M:TOOLSCAN-LOG-UNREADABLE` | prints `log_absent` | `test_scan_grok_unreadable_log_is_unreadable` |
| 22 | `toolscan-no-event-disarmed` | `# M:TOOLSCAN-NO-EVENT` | condition never fires (`CLEAN calls=0`) | `test_scan_grok_no_event_is_unreadable` |
| 23 | `toolscan-usage-reason` | `# M:TOOLSCAN-LAST-RESORT` | prints `internal:Usage` | `test_scan_usage_error_is_internal` |
| 24 | `toolscan-token-field-swap` | `# M:TOOLSCAN-TOKEN` | the CLI prints `exempt=` from the `out_of_root` count | `test_scan_cli_and_function_agree` |

The `[tilde]`, `[home]` and `[brace]` ids of `test_scan_grok_skills_is_exempt` read the same spelling
lines as rows 4–6 and are covered by them through the `own_session` ids; the `[absolute]` id of
`own_session` has row 3.

**Dependencies on other tasks**: Tasks 0–14 merged (the spec file and the docs module exist).

---

## Task 22: `h_mad_grok_containment.py`: `quarantine` and `require`

**Production file**: `h-mad/scripts/h_mad_grok_containment.py` (create)
**Test files**: `h-mad/tests/test_grok_audit_surface_containment.py` (extend),
`h-mad/tests/test_grok_audit_surface_wrapper.py` (extend: the end-to-end halt test)
**Task shape**: `new-behaviour`

**Description**: D20 `quarantine` (reads `$HOME`; the store `$HOME/.grok/sessions/`; the quarantine
`$HOME/.local/state/h-mad/grok-audit-surface/grok-quarantine-<yyyymmddThhmmssZ>/` by `os.mkdir`; entries
matching `*gas-root-*`, never followed, moved with `os.rename` and never copied or deleted; one
`MOVED: <name>` line each; the token `QUARANTINE: VERIFIED moved=<n> dest=<abs>` or
`QUARANTINE: REFUSED reason=<r>`, the first of the five ordered reasons, exit 0 on all six; the sixth
form `internal:<ExceptionName>`, exit 2). D8 and D20 `require --verb <toolscan|grok-canary|quarantine> --token-file <file> [--halt-file <file>]`:
it reads only the token file's last line; `REQUIRE: OK` needs exactly `GROK-CANARY: PASS`, a line
beginning `QUARANTINE: VERIFIED moved=`, or one beginning `TOOLSCAN: CLEAN surface=grok `, for the verb
named; anything else prints `REQUIRE: STOP reason=<that line | no_token:<file>>`, and for `toolscan`
it first appends that reason to `--halt-file` with `O_APPEND|O_CREAT`; exit 0 on both; exit 2 only on a
usage or internal error, after writing the halt file when one was named. A usage error can fail before
argparse returns a Namespace (an unknown flag, or a missing `--token-file`), so `require` reads the
`--halt-file` value from the raw argv first, before parsing, the way the probe reads `--data` (Task 2,
carry 12), and writes the halt file from that value on a usage error (`# M:REQUIRE-FAIL-CLOSED-ARGV`,
impl-plan audit cycle 4). `# M:REQUIRE-FAIL-CLOSED` stays the internal-error path.

**Tests** (18 functions, 27 node ids):
- Quarantine, stand-in `$HOME` (10): `test_quarantine_verifies_and_moves_every_match` (non-matching
  entries stay), `test_quarantine_verifies_zero_matches`, `test_quarantine_refuses_an_existing_quarantine`,
  `test_quarantine_refuses_a_failed_move` (`os.rename` replaced in process by one raising for one entry),
  `test_quarantine_refuses_residue` (a matching directory planted after the move: `residue:1`),
  `test_quarantine_refuses_a_count_mismatch`, `test_quarantine_refuses_an_unreadable_store` (no store),
  `test_quarantine_never_deletes` (directory entries; `shutil.rmtree`, `os.unlink` and `os.rmdir`
  replaced by recorders, which record no call, and every entry is in the store or the quarantine),
  `test_quarantine_internal_on_an_injected_exception` (the move step replaced by one raising
  `RuntimeError`: exactly `QUARANTINE: REFUSED reason=internal:RuntimeError`, exit 2, every matching
  entry still in the store), `test_quarantine_internal_on_a_usage_error` (an unknown flag: exactly
  `QUARANTINE: REFUSED reason=internal:UsageError`, exit 2, no quarantine created, nothing moved). Each
  asserts the exit code beside the token.
- `require` (6 functions, 11 ids): `test_require_ok_per_verb` `[toolscan]`, `[grok-canary]`,
  `[quarantine]`; `test_require_stop_on_another_token` `[toolscan]` (`TOOLSCAN: OUT_OF_ROOT surface=grok …`),
  `[toolscan-codex-clean]` (`TOOLSCAN: CLEAN surface=codex …`), `[grok-canary]`
  (`GROK-CANARY: REFUSED reason=escaped`), `[quarantine]` (`QUARANTINE: REFUSED reason=residue:1`);
  `test_require_stop_on_an_empty_file`; `test_require_stop_on_an_absent_file`;
  `test_require_toolscan_stop_writes_the_halt_file`; `test_require_internal_error_still_writes_the_halt_file`
  (the reader replaced by one raising: exit 2, the halt file written).
- Usage-error fail-closed (wrapper module, 1 function, 2 ids; impl-plan audit cycle 4):
  `test_require_usage_error_still_writes_the_halt_file`, parametrized `[unknown-flag]`
  (`require --verb toolscan --token-file <tmp_path>/clean.txt --halt-file <tmp_path>/HALT --no-such-flag`,
  the token file holding a `TOOLSCAN: CLEAN surface=grok` line) and
  `[missing-token-file]` (`require --verb toolscan --halt-file <tmp_path>/HALT`): exit 2, `<tmp_path>/HALT` exists and holds
  one line, and then `audit-cycle --halt-file <tmp_path>/HALT`
  with stub agents launches no agent and prints `REQUIRE: STOP reason=halt_file`.
- End to end (wrapper module, 1 function, 4 ids): `test_out_of_root_scan_stops_the_next_cycle`,
  parametrized `[out_of_root]`, `[unreadable]`, `[empty]`, `[absent]` over the scan's token file
  (D17 names the `OUT_OF_ROOT` run and parametrizes it over the other three; this plan reads that as four
  ids): `require --verb toolscan --halt-file` prints `REQUIRE: STOP`, then `audit-cycle --halt-file`
  with stub agents launches nothing and prints `REQUIRE: STOP reason=halt_file`.

**Acceptance Criteria**:
- [ ] AC-T22.1: The 27 ids pass, each asserting its exit code beside its token.
- [ ] AC-T22.2: `grep -cE 'shutil\.(copy|rmtree)|os\.(unlink|remove|rmdir)' h-mad/scripts/h_mad_grok_containment.py`
  prints 0 before Task 23 (matching lines): the quarantine neither copies nor deletes.

**RED split**: 27 ids; 27 F (the module is absent), 0 P.

**Mutation rows** (26; markers 16). `file` `scripts/h_mad_grok_containment.py`; tests in
`tests/test_grok_audit_surface_containment.py` except rows 21–26 (`tests/test_grok_audit_surface_wrapper.py`).

| # | name | marker | replace | test |
|---|---|---|---|---|
| 1 | `quarantine-exists-disarmed` | `# M:QUARANTINE-EXISTS` | `os.makedirs(…, exist_ok=True)` | `test_quarantine_refuses_an_existing_quarantine` |
| 2 | `quarantine-move-failed-disarmed` | `# M:QUARANTINE-MOVE-FAILED` | condition never fires | `test_quarantine_refuses_a_failed_move` |
| 3 | `quarantine-residue-disarmed` | `# M:QUARANTINE-RESIDUE` | condition never fires | `test_quarantine_refuses_residue` |
| 4 | `quarantine-count-mismatch-disarmed` | `# M:QUARANTINE-COUNT-MISMATCH` | condition never fires | `test_quarantine_refuses_a_count_mismatch` |
| 5 | `quarantine-unreadable-reason` | `# M:QUARANTINE-UNREADABLE` | prints `count_mismatch` | `test_quarantine_refuses_an_unreadable_store` |
| 6 | `quarantine-last-resort-exit-0` | `# M:QUARANTINE-LAST-RESORT` | returns 0 | `test_quarantine_internal_on_an_injected_exception` |
| 7 | `quarantine-usage-reason` | `# M:QUARANTINE-USAGE` | prints `internal:Usage` | `test_quarantine_internal_on_a_usage_error` |
| 8 | `quarantine-match-widened` | `# M:QUARANTINE-MATCH` | every entry matches | `test_quarantine_verifies_and_moves_every_match` |
| 9 | `quarantine-move-copies` | `# M:QUARANTINE-MOVE` | `shutil.copytree(src, dst, symlinks=True); shutil.rmtree(src)` | `test_quarantine_never_deletes` |
| 10 | `require-ok-toolscan-narrowed` | `# M:REQUIRE-OK-TOOLSCAN` | never OK | `test_require_ok_per_verb[toolscan]` |
| 11 | `require-ok-canary-narrowed` | `# M:REQUIRE-OK-CANARY` | never OK | `test_require_ok_per_verb[grok-canary]` |
| 12 | `require-ok-quarantine-narrowed` | `# M:REQUIRE-OK-QUARANTINE` | never OK | `test_require_ok_per_verb[quarantine]` |
| 13 | `require-ok-toolscan-widened` | `# M:REQUIRE-OK-TOOLSCAN` | OK on any `TOOLSCAN: ` line | `test_require_stop_on_another_token[toolscan]` |
| 14 | `require-ok-toolscan-any-surface` | `# M:REQUIRE-OK-TOOLSCAN` | OK on `TOOLSCAN: CLEAN ` for any surface | `test_require_stop_on_another_token[toolscan-codex-clean]` |
| 15 | `require-ok-canary-widened` | `# M:REQUIRE-OK-CANARY` | OK on any `GROK-CANARY: ` line | `test_require_stop_on_another_token[grok-canary]` |
| 16 | `require-ok-quarantine-widened` | `# M:REQUIRE-OK-QUARANTINE` | OK on any `QUARANTINE: ` line | `test_require_stop_on_another_token[quarantine]` |
| 17 | `require-no-token-reason-absent` | `# M:REQUIRE-NO-TOKEN` | prints `missing:` in place of `no_token:` | `test_require_stop_on_an_absent_file` |
| 18 | `require-no-token-reason-empty` | `# M:REQUIRE-NO-TOKEN` | the same | `test_require_stop_on_an_empty_file` |
| 19 | `require-toolscan-stop-no-append` | `# M:REQUIRE-TOOLSCAN-STOP` | the halt file not written | `test_require_toolscan_stop_writes_the_halt_file` |
| 20 | `require-fail-closed-dropped` | `# M:REQUIRE-FAIL-CLOSED` | the error path skips the halt write | `test_require_internal_error_still_writes_the_halt_file` |
| 21 | `require-halt-e2e-out-of-root` | `# M:REQUIRE-TOOLSCAN-STOP` | the halt file not written | `test_out_of_root_scan_stops_the_next_cycle[out_of_root]` |
| 22 | `require-halt-e2e-unreadable` | `# M:REQUIRE-TOOLSCAN-STOP` | the same | `test_out_of_root_scan_stops_the_next_cycle[unreadable]` |
| 23 | `require-halt-e2e-empty` | `# M:REQUIRE-TOOLSCAN-STOP` | the same | `test_out_of_root_scan_stops_the_next_cycle[empty]` |
| 24 | `require-halt-e2e-absent` | `# M:REQUIRE-TOOLSCAN-STOP` | the same | `test_out_of_root_scan_stops_the_next_cycle[absent]` |
| 25 | `require-fail-closed-argv-unknown-flag` | `# M:REQUIRE-FAIL-CLOSED-ARGV` | the raw-argv `--halt-file` read dropped (no halt path on a usage error) | `test_require_usage_error_still_writes_the_halt_file[unknown-flag]` |
| 26 | `require-fail-closed-argv-missing-token-file` | `# M:REQUIRE-FAIL-CLOSED-ARGV` | the same | `test_require_usage_error_still_writes_the_halt_file[missing-token-file]` |


**Dependencies on other tasks**: Task 20 (`audit-cycle --halt-file`) and Task 21 (the containment test
module and `TOOLSCAN:` tokens the fixtures copy).

---

## Task 23: `hmad-dispatch grok-canary`

**Production files**: `h-mad/scripts/h_mad_grok_containment.py` (extend: `canary-plant`,
`canary-judge`), `h-mad/scripts/hmad-dispatch.sh` (`_cmd_grok_canary`, its dispatch-table arm beside
`audit-cycle) _cmd_audit_cycle "$@" ;;` (line 4471 at `9628c857`), `grok-canary` added to `_HMAD_VERBS`
(line 4433), its usage line)
**Test file**: `h-mad/tests/test_grok_audit_surface_containment.py` (extend)
**Task shape**: `wiring` — the verb must run grok only through `_cmd_exec`, so the canary has every
grok leg's profile, `TMPDIR` and staging, and must hand `exec`'s exit code to the judge; `canary-plant`
and `canary-judge` are new behaviour carried in the same Task (design D18 lands them together), and
their RED split is stated below.
**WIRE 1**: `h-mad/scripts/hmad-dispatch.sh:_cmd_grok_canary` → `h-mad/scripts/hmad-dispatch.sh:_cmd_exec`
**WIRE-PIN 1**: `h-mad/tests/test_grok_audit_surface_containment.py::test_canary_pass`
**WIRE 2**: `h-mad/scripts/hmad-dispatch.sh:_cmd_grok_canary` → `h-mad/scripts/h_mad_grok_containment.py:canary_judge`
**WIRE-PIN 2**: `h-mad/tests/test_grok_audit_surface_containment.py::test_canary_grok_rc`
**WIRE 3**: `h-mad/scripts/hmad-dispatch.sh:_cmd_grok_canary` → `h-mad/scripts/h_mad_grok_containment.py:canary_plant`
**WIRE-PIN 3**: `h-mad/tests/test_grok_audit_surface_containment.py::test_canary_target_preexisting`

**Description**: D18. `hmad-dispatch grok-canary --run-dir <abs> [--timeout <s>]` (default 300). Usage
errors exit 2 with usage on stderr and no `GROK-CANARY:` line, each its own marked check: no
`--run-dir` (`# M:CANARY-RUNDIR-GIVEN`), relative (`# M:CANARY-RUNDIR-ABS`), missing
(`# M:CANARY-RUNDIR-EXISTS`), inside system temp, the D5 set `{$TMPDIR, /tmp, /private/tmp}` each
resolved (`# M:CANARY-RUNDIR-TMP`), no `roots/` (`# M:CANARY-RUNDIR-ROOTS`). Each prints its own
stderr line before the usage, `hmad-dispatch: grok-canary: --run-dir` followed by, per check,
`is required`, `is not absolute`, `does not exist`, `lies in system temp` and `has no roots/`, because
without its own line a disarmed check falls to its sibling (a missing directory then fails `roots/`,
an absent flag then fails the absolute-path check) with the same exit 2, no token and the same usage
line, and its row survives (impl-plan audit cycle 3). Then
`python3 h-mad/scripts/h_mad_grok_containment.py canary-plant --run-dir <dir>`; only on its
`PLANT: READY …` line (`# M:CANARY-PLANT-GATE`), `_cmd_exec grok canary/prompt.txt --cd <cwd> --log canary/log.ndjson --timeout <s>`
with no `--sandbox` (`# M:CANARY-EXEC-WIRE`); then `canary-judge --run-dir <dir> --rc "$rc"`
(`# M:CANARY-RC-WIRE`). The verb's last stdout line is the judge's (or plant's) token; it exits 0 on
`PASS` and every reason form, 2 only on a usage or escaping internal error. `canary-plant` creates every
canary file `O_CREAT|O_EXCL` (`# M:CANARY-EXCL`), writes `secrets.token_hex(16)` to `sentinel.txt`,
reads it back, writes `canary/plant.txt` holding one `PLANT: ` line (`sha256=` the token's sha256, then `sentinel=`, `denied=` and `cwd=`
with their absolute paths) and no
plain token (`# M:CANARY-PLANT-RECORD`), and a prompt naming the sentinel's path and never its content
(`# M:CANARY-PROMPT`). The seven forms in spec AC-11.4's order, the first that applies winning, each
its own marked line: plant's `target_preexisting` (`# M:CANARY-TARGET-PREEXISTING`),
`cannot_run:grok_absent` (`# M:CANARY-GROK-ABSENT`), `no_read_check:sentinel_unplanted`
(`# M:CANARY-SENTINEL-UNPLANTED`); judge's `escaped` (`# M:CANARY-ESCAPED`), `read_escaped` by hash
(`# M:CANARY-READ-BY-HASH`), `cannot_run:timeout` / `grok_rc:` with `exec`'s exit code / `truncated`
(`# M:CANARY-TIMEOUT`, `# M:CANARY-GROK-RC`, `# M:CANARY-TRUNCATED`), `no_read_check:log_unreadable` /
`sentinel_changed` by hash / `not_attempted` (`# M:CANARY-LOG-UNREADABLE`, `# M:CANARY-SENTINEL-BY-HASH`,
`# M:CANARY-NOT-ATTEMPTED`), `no_control` (`# M:CANARY-NO-CONTROL`), `no_denial` with its two
alternatives, no call naming the target (`# M:CANARY-NO-DENIAL`) and no update with the same
`toolCallId` carrying `Operation not permitted` (`# M:CANARY-DENIAL-ID`). The judge's expected value
is read only from `plant.txt`. An escaping exception in `canary-judge` exits 2
(`# M:CANARY-LAST-RESORT`). `not_attempted` reads `named_paths` from Task 21's module.

**Scaffold that makes each WIRE-PIN's RED an assertion about the caller.** At RED Task 22's
`h_mad_grok_containment.py` exists without the two canary subcommands, Task 18's `exec` writes the
profile record, and the wrapper has no `grok-canary` verb. Each pin runs
`h-mad/bin/hmad-dispatch grok-canary --run-dir <stand-in run dir>` as a subprocess with a stub `grok` on
`PATH` that plants its outcome and records its argv and environment, and asserts the last stdout line
first: WIRE-PIN 1 `GROK-CANARY: PASS`, then `canary/log.ndjson.profile` reads
`GROK-PROFILE: profile=strict origin=default` and the stub's argv carries `--sandbox strict`; WIRE-PIN 2
`GROK-CANARY: REFUSED reason=cannot_run:grok_rc:7` from a stub exiting 7; WIRE-PIN 3
`GROK-CANARY: REFUSED reason=target_preexisting`, then the stub's record file is absent. At RED each
run prints the wrapper's unknown-verb usage and no token, so each pin fails on its token assertion,
never on an import.

**Wire cuts at GREEN** (rows 27–30): row 27 cuts WIRE 1 and row 28 forces it; row 29 cuts WIRE 2; row
30 cuts WIRE 3. Each must fail its WIRE-PIN with the callees and the tests intact.

**Tests** (21 functions, 28 node ids):
- The design's 20: `test_canary_target_preexisting`, `test_canary_escaped` (planted with the denial
  text logged, so the order is pinned), `test_canary_read_escaped_in_tool_result` and
  `test_canary_read_escaped_in_message_text` (each with the control present and the denial logged),
  `test_canary_grok_absent`, `test_canary_grok_rc`, `test_canary_timeout`, `test_canary_truncated`
  (parametrized `[judge]` and `[wrapper]`, below),
  `test_canary_sentinel_unplanted`, `test_canary_log_unreadable`, `test_canary_sentinel_changed`,
  `test_canary_not_attempted`, `test_canary_no_control`, `test_canary_no_denial` (parametrized
  `[no-call]` and `[unmatched-update]`, one per D18 alternative), `test_canary_pass` (its prompt is
  asserted not to contain the token), `test_canary_second_run_overwrites_nothing`,
  `test_canary_replaced_sentinel_is_sentinel_changed` and
  `test_canary_deleted_sentinel_with_token_in_log_is_read_escaped` (both through the real plant →
  exec → judge path), `test_canary_usage_error_exits_2` (parametrized `[no-run-dir]`, `[relative]`,
  `[missing]`, `[in-system-temp]`, `[no-roots]`: exit 2, no `GROK-CANARY:` line, stderr carries the
  verb's own usage line `usage: hmad-dispatch grok-canary --run-dir`, and stderr carries that id's own
  check line and none of the other four), `test_canary_injected_exception_exits_2`
  (`main(["canary-judge", …])` in process with `canary_judge` replaced by a recorder that raises:
  exit 2, no `GROK-CANARY:` line, and the recorder was called).
- `test_require_canary_without_a_token_is_stop`, parametrized `[exit-0]` and `[exit-2]`: a token file
  holding a run's stdout that ends in a line other than a `GROK-CANARY:` line (the exit-0 one ends in an
  `[H-MAD]` line, the exit-2 one in the usage text): `require --verb grok-canary` prints `REQUIRE: STOP`
  both times.

Every fixture asserts that `plant.txt`, when it exists, holds no plain token, and asserts the exit code
beside the token (0 for `PASS` and every reason form).

**The stub's default transcript (impl-plan audit cycle 3).** `_cmd_exec` turns a grok run that exits 0
with no final message into rc 3 (`hmad-dispatch.sh` lines 3366–3374 at `121ae4ce`, `EMPTY final
message`), and the judge decides `cannot_run` before every `no_read_check`, `no_control` and
`no_denial` form. So a stub that logs nothing makes every later form unreachable. The stub grok
therefore writes, by default, a completed streaming-json transcript in `grokfixtures.f0_text()`'s shape
(the shape `_grok_final_message` reads): the planted outcome's own
`tool_call` and `tool_call_update` events (none of them carrying the token unless the fixture plants
it), then an `end` event and a final message `DONE`, and exits 0. Only `test_canary_grok_rc`,
`test_canary_timeout` and `test_canary_truncated` depart from it, each in its one field (exit code,
sleep past `--timeout`, no `end` event).

**`test_canary_truncated` reaches its own branch (impl-plan audit cycle 4).** An end-less stream never
reaches the judge with rc 0 through the real wrapper: `_cmd_exec` sets `final_empty=1` when
`_grok_region_state` is not `complete` (`hmad-dispatch.sh` lines 3207–3218 at `b17e1b36`), and then turns
rc 0 into rc 3 (lines 3366–3370), the behaviour `h-mad/tests/test_hmad_dispatch_exec_grok.py::test_exec_grok_truncated_recovers_the_verdict`
pins (`assert r.returncode == 3`, line 302). The judge decides the `grok_rc:` form (a non-zero exit code) before `truncated`, so an
end-to-end end-less run prints `cannot_run:grok_rc:3`. The test is therefore parametrized:
`test_canary_truncated[judge]` runs the real `canary-plant`, writes a readable end-less
`canary/log.ndjson` itself (`grokfixtures.f_trunc()`'s shape), and calls
`python3 h-mad/scripts/h_mad_grok_containment.py canary-judge --run-dir <the run dir> --rc 0`, asserting
`GROK-CANARY: REFUSED reason=cannot_run:truncated`; `test_canary_truncated[wrapper]` runs the whole verb
with an end-less stub and asserts `GROK-CANARY: REFUSED reason=cannot_run:grok_rc:3`, the regression
control that keeps the real wrapper's rc 3 in view. Row 10 targets `[judge]`; row 33 targets
`[wrapper]`. In particular `test_canary_replaced_sentinel_is_sentinel_changed`
runs the real plant → exec → judge path with a stub that overwrites `sentinel.txt` with another 32-hex
token and writes the completed default transcript, holding no 32-hex run equal to the planted hash, so
the judge reaches and prints `no_read_check:sentinel_changed`; the design's "logs nothing" is read as
"logs no tool result carrying a token". Each fixture first asserts that `exec`'s stderr carries no
`EMPTY final message` line, except the three that plant a `cannot_run` form.

**Residual, stated exactly (design rev4's Phase-5 note).** `read_escaped` searches maximal runs of
exactly 32 lowercase hex characters, `(?<![0-9a-f])[0-9a-f]{32}(?![0-9a-f])`. A log that carries the
token glued to further hex characters (a longer hex run containing it) is not matched, so the canary
then reads `no_read_check:sentinel_changed` or `PASS` according to the other checks; it fails open
toward `PASS` only when grok echoes the token inside a longer hex run and leaves the sentinel intact.
Upper-case hex is not matched either. Neither shape is fixtured.

**Acceptance Criteria**:
- [ ] AC-T23.1: The three WIRE-PINs pass, and each fails when only its wire is cut (rows 27, 29, 30).
- [ ] AC-T23.2: The 28 ids pass; `h-mad/tests/test_hmad_dispatch_missing_positionals.py` passes,
  including its new `test_no_verb_dies_on_an_unbound_variable[grok-canary]` id.
- [ ] AC-T23.3: `grep -c '_cmd_exec grok' h-mad/scripts/hmad-dispatch.sh` prints 1 (matching lines),
  inside `_cmd_grok_canary`, and that function runs no `grok` binary itself
  (`sed -n '/^_cmd_grok_canary()/,/^}/p' h-mad/scripts/hmad-dispatch.sh | grep -cE '(^|[^_a-z])grok --'`
  prints 0).

**RED split** (stated for the record; the WIRE-PINs, not the split, gate this Task): 28 ids; 26 F (no
verb, no canary subcommands); 2 P, both `test_require_canary_without_a_token_is_stop` ids, regression
guards over Task 22's `require`, whose negative observations are rows 31–32.

**Mutation rows** (33; markers 26: 18 in `scripts/h_mad_grok_containment.py`, 8 in
`scripts/hmad-dispatch.sh`). Tests in `tests/test_grok_audit_surface_containment.py`. Rows 3 and 11
change the printed reason (Rules, "S0c scripts").

| # | name | file | marker | replace | test |
|---|---|---|---|---|---|
| 1 | `canary-target-preexisting-disarmed` | containment | `# M:CANARY-TARGET-PREEXISTING` | never fires | `test_canary_target_preexisting` |
| 2 | `canary-grok-absent-disarmed` | containment | `# M:CANARY-GROK-ABSENT` | never fires | `test_canary_grok_absent` |
| 3 | `canary-sentinel-unplanted-reason` | containment | `# M:CANARY-SENTINEL-UNPLANTED` | prints `target_preexisting` | `test_canary_sentinel_unplanted` |
| 4 | `canary-escaped-disarmed` | containment | `# M:CANARY-ESCAPED` | never fires | `test_canary_escaped` |
| 5 | `canary-read-by-hash-disarmed` | containment | `# M:CANARY-READ-BY-HASH` | never matches | `test_canary_read_escaped_in_tool_result` |
| 6 | `canary-read-by-hash-message` | containment | `# M:CANARY-READ-BY-HASH` | the same | `test_canary_read_escaped_in_message_text` |
| 7 | `canary-read-by-hash-deleted` | containment | `# M:CANARY-READ-BY-HASH` | the same | `test_canary_deleted_sentinel_with_token_in_log_is_read_escaped` |
| 8 | `canary-timeout-disarmed` | containment | `# M:CANARY-TIMEOUT` | 124 read as `grok_rc:124` | `test_canary_timeout` |
| 9 | `canary-grok-rc-disarmed` | containment | `# M:CANARY-GROK-RC` | never fires | `test_canary_grok_rc` |
| 10 | `canary-truncated-disarmed` | containment | `# M:CANARY-TRUNCATED` | never fires | `test_canary_truncated[judge]` |
| 11 | `canary-log-unreadable-reason` | containment | `# M:CANARY-LOG-UNREADABLE` | prints `not_attempted` | `test_canary_log_unreadable` |
| 12 | `canary-sentinel-by-hash-disarmed` | containment | `# M:CANARY-SENTINEL-BY-HASH` | never fires | `test_canary_sentinel_changed` |
| 13 | `canary-sentinel-by-hash-replaced` | containment | `# M:CANARY-SENTINEL-BY-HASH` | the same | `test_canary_replaced_sentinel_is_sentinel_changed` |
| 14 | `canary-not-attempted-disarmed` | containment | `# M:CANARY-NOT-ATTEMPTED` | never fires | `test_canary_not_attempted` |
| 15 | `canary-no-control-disarmed` | containment | `# M:CANARY-NO-CONTROL` | never fires | `test_canary_no_control` |
| 16 | `canary-no-denial-disarmed` | containment | `# M:CANARY-NO-DENIAL` | never fires | `test_canary_no_denial[no-call]` |
| 17 | `canary-denial-id-dropped` | containment | `# M:CANARY-DENIAL-ID` | any update's text counts | `test_canary_no_denial[unmatched-update]` |
| 18 | `canary-excl-dropped` | containment | `# M:CANARY-EXCL` | `O_EXCL` dropped | `test_canary_second_run_overwrites_nothing` |
| 19 | `canary-last-resort-exit-0` | containment | `# M:CANARY-LAST-RESORT` | returns 0 | `test_canary_injected_exception_exits_2` |
| 20 | `canary-plant-record-plain` | containment | `# M:CANARY-PLANT-RECORD` | the token written beside its hash | `test_canary_pass` |
| 21 | `canary-prompt-names-token` | containment | `# M:CANARY-PROMPT` | the prompt carries the token | `test_canary_pass` |
| 22 | `canary-rundir-given-disarmed` | dispatch | `# M:CANARY-RUNDIR-GIVEN` | never fires | `test_canary_usage_error_exits_2[no-run-dir]` |
| 23 | `canary-rundir-abs-disarmed` | dispatch | `# M:CANARY-RUNDIR-ABS` | never fires | `test_canary_usage_error_exits_2[relative]` |
| 24 | `canary-rundir-exists-disarmed` | dispatch | `# M:CANARY-RUNDIR-EXISTS` | never fires | `test_canary_usage_error_exits_2[missing]` |
| 25 | `canary-rundir-tmp-disarmed` | dispatch | `# M:CANARY-RUNDIR-TMP` | never fires | `test_canary_usage_error_exits_2[in-system-temp]` |
| 26 | `canary-rundir-roots-disarmed` | dispatch | `# M:CANARY-RUNDIR-ROOTS` | never fires | `test_canary_usage_error_exits_2[no-roots]` |
| 27 | `canary-exec-wire-cut` | dispatch | `# M:CANARY-EXEC-WIRE` | `rc=0` (no call) | `test_canary_pass` |
| 28 | `canary-exec-wire-weaker` | dispatch | `# M:CANARY-EXEC-WIRE` | the call with `--sandbox workspace --allow-weaker-sandbox` | `test_canary_pass` |
| 29 | `canary-rc-wire-cut` | dispatch | `# M:CANARY-RC-WIRE` | `--rc 0` | `test_canary_grok_rc` |
| 30 | `canary-plant-gate-cut` | dispatch | `# M:CANARY-PLANT-GATE` | `exec` runs whatever plant printed | `test_canary_target_preexisting` |
| 31 | `require-ok-canary-any-line-exit-0` | containment | `# M:REQUIRE-OK-CANARY` | OK on any non-empty last line | `test_require_canary_without_a_token_is_stop[exit-0]` |
| 32 | `require-ok-canary-any-line-exit-2` | containment | `# M:REQUIRE-OK-CANARY` | the same | `test_require_canary_without_a_token_is_stop[exit-2]` |
| 33 | `canary-grok-rc-no-end` | containment | `# M:CANARY-GROK-RC` | never fires (an end-less run then reads `truncated`) | `test_canary_truncated[wrapper]` |

"containment" is `scripts/h_mad_grok_containment.py` and "dispatch" is `scripts/hmad-dispatch.sh`.
Rows 31–32 mutate Task 22's marker and add no site.

**Dependencies on other tasks**: Tasks 18 and 19 (the profile and staging the canary inherits), Task 21
(`named_paths`), Task 22 (the module and `require`).

---

## Task 24: the probe's `--work-dir`, parents and re-anchored reset guards

**Production file**: `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py` (extend)
**Test files**: `h-mad/tests/test_grok_audit_surface_probe.py` (extend and modify),
`h-mad/tests/grokauditfixtures.py` (modify)
**Task shape**: `new-behaviour`

**Description**: D5 "Parent directory", "Where the probe writes" and the reset target precondition
as v1.6 re-anchors it, and D2's two v1.6 paired-flag rules:
1. `checked_parent(path, *, git_guard)`, each guard its own marked line and class: an absolute
   existing directory, else `ParentNotDirectory` (`# M:GAS-PARENT-ISDIR`; `None` fails here too); its
   resolved path not inside system temp, the set `{tempfile.gettempdir(), /tmp, /private/tmp}` each
   resolved, else `ParentInSystemTemp` (`# M:GAS-PARENT-TMPDIR`); for `--work-dir` only,
   `git -C <dir> rev-parse --git-dir` in D7's environment exits non-zero, else `WorkDirInGitTree`
   (`# M:GAS-WORKDIR-GIT`). The two call sites are the marked wires `# M:GAS-WORK-DIR-CHECK` and
   `# M:GAS-DEST-PARENT-CHECK`.
2. `--work-dir` is required by `build-root`, `main-leak`, `rescore` and the `--repo` forms of
   `check-ledger` and `extract`, checked in `main()` through `parser.error`
   (`# M:GAS-WORK-DIR-REQUIRED`); `build-root` requires one of `--dest-parent` and `--reset`
   (`# M:GAS-PARENT-REQUIRED`; both stays `ResetArgsConflict`). Both print
   `<PREFIX> UNREADABLE reason=internal:UsageError`, with the mode's prefix.
3. The six `mkdtemp`/`TemporaryDirectory` sites take `dir=` (lines 224, 359, 367, 1175, 1459 and 1560
   at `9628c857`): `gas-ledger-` twice (`# M:GAS-SCRATCH-LEDGER-TREE`, `# M:GAS-SCRATCH-LEDGER-REPO`),
   the root (`--dest-parent`, or `--work-dir` for `rescore` and the reset's expected tree;
   `# M:GAS-SCRATCH-ROOT`), `gas-extract-` (`# M:GAS-SCRATCH-EXTRACT`), `gas-main-leak-`
   (`# M:GAS-SCRATCH-MAIN-LEAK`) and `gas-rescore-` (`# M:GAS-SCRATCH-RESCORE`). The seventh,
   `gas-commit-` (line 665), stays in system temp (D5: it holds only a `GIT_INDEX_FILE`).
4. Reset guard 3 keeps its marker and its line and inverts: the line at `9628c857`,
   `    if root.parent != Path(tempfile.gettempdir()).resolve():  # M:GAS-RESET-TMPDIR`, becomes the test
   "resolved target inside system temp", raising `ResetTargetInSystemTemp` (the class
   `ResetTargetOutsideTempdir` is renamed). New guard 4, its resolved parent named `roots`, raises
   `ResetTargetOutsideRoots` (`# M:GAS-RESET-ROOTS`). Guards 5 and 6 are unchanged.
5. The reset's removal of a live entry absent from the expected tree is one marked line,
   `# M:GAS-RESET-REMOVE` (the `GAS-RESET-NOFOLLOW-REMOVE` line keeps the link case).

**Churn in existing tests (modified, not duplicated; names kept unless stated).**
- Every invocation of `build-root`, `main-leak`, `rescore` and the `--repo` forms of `check-ledger` and
  `extract` gains `--work-dir <tmp_path>/scratch`, a directory the shared helpers create as a sibling
  of the fixture checkout and pass through (impl-plan audit cycle 3: `build_repo` makes
  `<tmp_path>/work` a `git init`ed checkout, `h-mad/tests/grokauditfixtures.py` lines 117–122 at
  `121ae4ce`, so a `--work-dir` there trips `WorkDirInGitTree` before any case reaches its own check;
  `<tmp_path>/scratch` lies outside that checkout and outside the stand-in system temp, and each helper
  first asserts `git -C <tmp_path>/scratch rev-parse --git-dir` fails), and every probe run that needs an accepted parent runs
  with `TMPDIR=<tmp_path>/systemp` (subprocess) or `tempfile.tempdir` monkeypatched to it (in process).
  At `9628c857` the invocations sit in 20 `def` blocks of `h-mad/tests/test_grok_audit_surface_probe.py`
  whose text names `"build-root"`, `"main-leak"`, `"rescore"` or `"--repo"` (functions, by a
  `def`-block split of the file), helpers included (`_minimal_argv`, `_run_ledger`, `_run_root`,
  `_branch_argv`, `_assert_branch_refusal`, `_assert_main_clean`, `_successful_mode_run`); `_run_commit`
  drives `commit-data`, which takes no `--work-dir`. 5d re-derives the list with the same split.
- `test_root_line_parser_reads_build_root_output` and `test_root_line_parser_rejects_a_malformed_root_line`
  assert at `9628c857` that the root's parent is `tempfile.gettempdir()` (lines 829 and 856 of the test
  file); they now pass `--dest-parent` and assert the parent equals it.
- Every Task 5 reset fixture builds its root with `--dest-parent <tmp_path>/run/roots`, outside the
  stand-in system temp (`<tmp_path>/run/roots` and `<tmp_path>/systemp` are siblings), the probe run
  with `TMPDIR=<tmp_path>/systemp`; `test_build_root_reset_refuses_a_missing_target` names its absent path in that
  `roots/` directory.
- `test_build_root_reset_refuses_a_target_outside_the_tempdir` is renamed
  `test_build_root_reset_refuses_a_target_in_system_temp` and rewritten (below).

These are regression guards: each is P before this Task's GREEN commit and P after it, because the
invocation change lands in the GREEN commit with the code. The RED commit holds only the new and the
renamed tests.

**Tests** (11 new or renamed functions, 34 node ids):
- `test_dest_parent_must_be_a_directory` (`ROOT: UNREADABLE reason=internal:ParentNotDirectory`).
- `test_dest_parent_in_system_temp_refuses` (`internal:ParentInSystemTemp`).
- `test_work_dir_in_system_temp_refuses` (`internal:ParentInSystemTemp`).
- `test_work_dir_in_a_git_work_tree_refuses` (`internal:WorkDirInGitTree`).
- `test_build_root_requires_a_parent` (neither flag: `ROOT: UNREADABLE reason=internal:UsageError`).
- `test_every_scratch_dir_lies_under_the_work_dir`, parametrized over the six sites `[ledger-tree]`,
  `[ledger-repo]`, `[root]`, `[extract]`, `[main-leak]`, `[rescore]`: `tempfile.mkdtemp` and
  `TemporaryDirectory` replaced in process by recorders; every recorded directory lies under the
  run's `--work-dir` (`[root]`: under `--dest-parent` for `build-root`).
- `test_build_root_reset_refuses_a_target_in_system_temp` (a `gas-root-d1-s1-x` directory in a `roots/`
  directory under the stand-in system temp: `internal:ResetTargetInSystemTemp`, the sentinel unchanged,
  no traceback).
- `test_build_root_reset_refuses_a_target_outside_a_roots_dir` (a `gas-root-d1-s1-x` directory outside
  system temp whose parent is not named `roots`: `internal:ResetTargetOutsideRoots`, the same checks).
- `test_build_root_reset_removes_an_in_root_report_and_tmp` (a built root holding
  `.hmad-report/<stem name>_p1.report.md`, its collected copy and a `.tmp/` with a staged prompt: the
  reset removes all three, and the path set equals a fresh build's).
- `test_work_dir_is_required_where_a_directory_is_created` (plan-added: D2 states the rule and names no
  fixture), parametrized `[build-root]`, `[main-leak]`, `[rescore]`, `[check-ledger-repo]`,
  `[extract-repo]`: each without `--work-dir` prints its mode's `internal:UsageError` token.
- `test_reset_precondition_old_new_differential` (impl-plan audit cycle 3, the base guard-narrowing
  rule: re-anchoring guard 3 accepts targets the shipped reset refused, so every verdict the change
  moves is enumerated). The old predicate is the shipped one, never a re-implementation:
  `check_reset_target` of the probe as committed at `66ff0894` (the last commit that touched it before
  S0c), read with `git show 66ff0894:docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py`
  and compiled as `load_probe` compiles; the test first asserts that source holds the line
  `    if root.parent != Path(tempfile.gettempdir()).resolve():  # M:GAS-RESET-TMPDIR` (its positive
  control that it loaded the old guard). The new predicate is the working probe's. Both run on the same
  target, `--doc d1`, under the same stand-in system temp, and the outcome is the returned path or the
  raised class name (`Refusal` with its reason for the reach guard). Parametrized over 15 targets, each
  asserting the exact (old, new) pair:

  | id | target | old | new |
  |---|---|---|---|
  | `[systemp-child]` | `gas-root-d1-s1-x` directly in system temp | accepted | `ResetTargetInSystemTemp` |
  | `[roots-outside-temp]` | `<tmp_path>/run/roots/gas-root-d1-s1-x` | `ResetTargetOutsideTempdir` | accepted |
  | `[roots-inside-temp]` | `roots/gas-root-d1-s1-x` under system temp | `ResetTargetOutsideTempdir` | `ResetTargetInSystemTemp` |
  | `[non-roots-parent]` | `<tmp_path>/other/gas-root-d1-s1-x` | `ResetTargetOutsideTempdir` | `ResetTargetOutsideRoots` |
  | `[wrong-doc-prefix]` | `<tmp_path>/run/roots/gas-root-d2-s1-x` | `ResetTargetOutsideTempdir` | `ResetTargetPrefix` |
  | `[wrong-purpose-prefix]` | `<tmp_path>/run/roots/gas-root-d1-s2v1-x` | `ResetTargetOutsideTempdir` | `ResetTargetPrefix` |
  | `[nested-root]` | `<tmp_path>/run/roots/gas-root-d1-s1-a/gas-root-d1-s1-b` | `ResetTargetOutsideTempdir` | `ResetTargetOutsideRoots` |
  | `[sibling-roots-dir]` | `<tmp_path>/other-run/roots/gas-root-d1-s1-x` (another run's `roots/`) | `ResetTargetOutsideTempdir` | accepted |
  | `[symlink-into-roots]` | a link in system temp naming `<tmp_path>/run/roots/gas-root-d1-s1-x` | `ResetTargetOutsideTempdir` | accepted |
  | `[symlink-into-temp]` | a link in `<tmp_path>/run/roots/` naming a `gas-root-d1-s1-x` in system temp | accepted | `ResetTargetInSystemTemp` |
  | `[physical-spelling]` | the `[roots-outside-temp]` target reached through a symlinked ancestor of `<tmp_path>/run` | `ResetTargetOutsideTempdir` | accepted |
  | `[git-target]` | `<tmp_path>/run/roots/gas-root-d1-s1-x`, `git init`ed | `ResetTargetOutsideTempdir` | `Refusal` `root_git:.git` |
  | `[git-target-in-temp]` | `gas-root-d1-s1-x` in system temp, `git init`ed | `Refusal` `root_git:.git` | `ResetTargetInSystemTemp` |
  | `[empty]` / `[missing]` | `""` / an absent absolute path | `ResetTargetNotAbsolute` / `ResetTargetNotDirectory` | the same |

  (`[empty]` and `[missing]` are two ids in one row.) The softened verdicts, old refused and new
  accepted, are exactly four: `[roots-outside-temp]`, `[sibling-roots-dir]`, `[symlink-into-roots]` and
  `[physical-spelling]`. All four are one class, a `gas-root-d1-s1-` directory whose resolved parent is
  a directory named `roots` outside system temp and that is not a git target. That class is the design's
  intended acceptance (D5 guard 4 and its stated residual: "guard 4 accepts any directory named `roots`
  outside system temp, not only this run's"). Every other moved verdict hardens: a refusal where the
  old guard accepted, or a different refusal class. A softened verdict outside this class fails the
  test.

**Acceptance Criteria**:
- [ ] AC-T24.1: The 34 ids and every churned test pass; the two reset-refusal tests follow AC-T5.1's
  three-step assertion order.
- [ ] AC-T24.2: `grep -n 'gettempdir' docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py`
  shows it only inside the system-temp set of `checked_parent` and reset guard 3.
- [ ] AC-T24.3: `grep -c 'M:GAS-RESET-TMPDIR' docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py`
  prints 1 (the marker kept its one line).

**RED split**: 34 ids; 32 F (at RED `--work-dir` is an unknown flag, the default parent still exists,
guard 3 still requires `tempfile.gettempdir()` as the parent, and 13 differential ids expect a new
verdict the unchanged probe does not give); 2 P, `test_reset_precondition_old_new_differential[empty]`
and `[missing]`, whose old and new verdicts are equal by design; rows 21–22 are their negative
observations. Regression guards: the churned tests above.

**Mutation rows** (22 new; markers 15 new). `p-reset-tmpdir` is rewritten in place: its `find` is the
inverted `# M:GAS-RESET-TMPDIR` line, its `replace` makes that condition never fire, and its `test` is
`tests/test_grok_audit_surface_probe.py::test_build_root_reset_refuses_a_target_in_system_temp`
(`--check-anchors` shows the move). Every test below is in `tests/test_grok_audit_surface_probe.py`;
`file` is the probe.

| # | name | marker | replace | test |
|---|---|---|---|---|
| 1 | `p-parent-isdir` | `# M:GAS-PARENT-ISDIR` | condition never fires | `test_dest_parent_must_be_a_directory` |
| 2 | `p-parent-tmpdir-dest` | `# M:GAS-PARENT-TMPDIR` | condition never fires | `test_dest_parent_in_system_temp_refuses` |
| 3 | `p-parent-tmpdir-work` | `# M:GAS-PARENT-TMPDIR` | the same | `test_work_dir_in_system_temp_refuses` |
| 4 | `p-workdir-git` | `# M:GAS-WORKDIR-GIT` | condition never fires | `test_work_dir_in_a_git_work_tree_refuses` |
| 5 | `p-work-dir-check` | `# M:GAS-WORK-DIR-CHECK` | `Path(args.work_dir)` unvetted | `test_work_dir_in_system_temp_refuses` |
| 6 | `p-dest-parent-check` | `# M:GAS-DEST-PARENT-CHECK` | `Path(args.dest_parent)` unvetted | `test_dest_parent_in_system_temp_refuses` |
| 7 | `p-parent-required` | `# M:GAS-PARENT-REQUIRED` | condition never fires (the run reaches `checked_parent(None)`, `ParentNotDirectory`) | `test_build_root_requires_a_parent` |
| 8 | `p-work-dir-required-build-root` | `# M:GAS-WORK-DIR-REQUIRED` | condition never fires (the same fall-through) | `test_work_dir_is_required_where_a_directory_is_created[build-root]` |
| 9 | `p-work-dir-required-main-leak` | `# M:GAS-WORK-DIR-REQUIRED` | the same | `test_work_dir_is_required_where_a_directory_is_created[main-leak]` |
| 10 | `p-work-dir-required-rescore` | `# M:GAS-WORK-DIR-REQUIRED` | the same | `test_work_dir_is_required_where_a_directory_is_created[rescore]` |
| 11 | `p-work-dir-required-check-ledger` | `# M:GAS-WORK-DIR-REQUIRED` | the same | `test_work_dir_is_required_where_a_directory_is_created[check-ledger-repo]` |
| 12 | `p-work-dir-required-extract` | `# M:GAS-WORK-DIR-REQUIRED` | the same | `test_work_dir_is_required_where_a_directory_is_created[extract-repo]` |
| 13 | `p-reset-roots` | `# M:GAS-RESET-ROOTS` | condition never fires | `test_build_root_reset_refuses_a_target_outside_a_roots_dir` |
| 14 | `p-reset-remove-dot` | `# M:GAS-RESET-REMOVE` | entries whose name starts with `.` are kept | `test_build_root_reset_removes_an_in_root_report_and_tmp` |
| 15 | `p-scratch-ledger-tree` | `# M:GAS-SCRATCH-LEDGER-TREE` | `dir=` dropped | `test_every_scratch_dir_lies_under_the_work_dir[ledger-tree]` |
| 16 | `p-scratch-ledger-repo` | `# M:GAS-SCRATCH-LEDGER-REPO` | `dir=` dropped | `test_every_scratch_dir_lies_under_the_work_dir[ledger-repo]` |
| 17 | `p-scratch-root` | `# M:GAS-SCRATCH-ROOT` | `dir=` dropped | `test_every_scratch_dir_lies_under_the_work_dir[root]` |
| 18 | `p-scratch-extract` | `# M:GAS-SCRATCH-EXTRACT` | `dir=` dropped | `test_every_scratch_dir_lies_under_the_work_dir[extract]` |
| 19 | `p-scratch-main-leak` | `# M:GAS-SCRATCH-MAIN-LEAK` | `dir=` dropped | `test_every_scratch_dir_lies_under_the_work_dir[main-leak]` |
| 20 | `p-scratch-rescore` | `# M:GAS-SCRATCH-RESCORE` | `dir=` dropped | `test_every_scratch_dir_lies_under_the_work_dir[rescore]` |
| 21 | `p-reset-abs-differential` | `# M:GAS-RESET-ABS` (Task 5's marker) | condition never fires | `test_reset_precondition_old_new_differential[empty]` |
| 22 | `p-reset-isdir-differential` | `# M:GAS-RESET-ISDIR` (Task 5's marker) | condition never fires | `test_reset_precondition_old_new_differential[missing]` |

Rows 7–12 fall through to `checked_parent(None)`, a declared `ProbeRefusal` with its own token and no
traceback, so each is a test kill.

**Dependencies on other tasks**: Tasks 0–14 merged.

---

## Task 25: per-pass root records and the add-only commit

**Production file**: `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py` (extend)
**Test files**: `h-mad/tests/test_grok_audit_surface_probe.py` (extend),
`h-mad/tests/grokauditfixtures.py` (extend)
**Task shape**: `new-behaviour`

**Description**: D8 `record-cycle` v1.6 and D9 v1.6/v1.10:
1. `record-cycle` takes exactly one of `--root-record <file>` (written `root.txt`) and one or more
   `--pass-root-record <file>` in pass order (written `p1.root.txt`, `p2.root.txt` and so on, `# M:GAS-RECORD-PASS-NAME`); both
   (`# M:GAS-RECORD-FORMS-BOTH`) or neither (`# M:GAS-RECORD-FORMS-NEITHER`) is `internal:UsageError`.
   Every record gets the existing D5 checks (`# M:GAS-RECORD-ROOT-LINE`, `# M:GAS-RECORD-ROOT-MALFORMED`)
   in a loop over all records (`# M:GAS-RECORD-PASS-LOOP`); the first record's `path=` must be the
   resolved `--root` (`root_record:path_mismatch`, `# M:GAS-RECORD-PASS-PATH`).
2. The stem pattern also matches the stem's `_pN.log.profile` files (N the pass index), each copied as
   `pN.profile.txt`
   (`# M:GAS-RECORD-PROFILE`); each pass's `p<i>.report.md` is copied from
   `<pass root>/.hmad-report/<stem name>_p<i>.report.md` when that file exists, else from the stem dir
   (`# M:GAS-RECORD-PASS-REPORT`), the pass root being the record's `path=` (for `--root-record`,
   `--root`).
3. `commit-data` refuses `would_replace:` followed by the calibration path when the parent's tree holds a blob at that
   calibration path whose id differs from the file's `git hash-object` id, checked for every `--src`
   file in sorted order before any `update-index` (`# M:GAS-COMMIT-REPLACE`); an identical re-add is a
   no-op; `ledger.jsonl` and `seeded/` are exempt (`# M:GAS-COMMIT-AUTHORING`).

**Tests** (10 functions, 11 node ids):
- `test_record_cycle_writes_one_root_record_per_pass` (three `--pass-root-record` files: `p1.root.txt`
  … `p3.root.txt`, no `root.txt`).
- `test_record_cycle_copies_the_report_from_its_pass_root`.
- `test_record_cycle_copies_the_profile_record`.
- `test_record_cycle_refuses_both_root_record_forms`, parametrized `[both]` and `[neither]` (design names
  the both-or-neither usage error; this plan gives each alternative its id): `RECORD: REFUSED reason=internal:UsageError`
  and no file under `--dest`.
- `test_record_cycle_refuses_a_first_pass_record_for_another_root` (`root_record:path_mismatch`).
- `test_record_cycle_refuses_a_malformed_second_pass_record` (plan-added: the second of three records
  without `list_blob=`: `root_record:no_line`, so the checks reach every record).
- `test_commit_data_refuses_a_replaced_blob` (`would_replace:` followed by that path).
- `test_commit_data_accepts_an_identical_re_add` (must not refuse).
- `test_commit_data_appends_a_second_reading_after_an_earlier_resmoke` (a temporary repository whose
  branch holds `runs/run-a/resmoke/`; a second commit adding `runs/run-b/resmoke/` with `--parent` its
  tip: `COMMIT: OK`, `runs/run-a/` byte-identical; a stale `--parent` refuses `ref_moved:` followed by the tip's sha).
- `test_commit_data_accepts_a_changed_authoring_file` (plan-added: a changed `ledger.jsonl` against a
  parent that holds one: `COMMIT: OK`, the exemption's must-not-refuse fixture).

**Acceptance Criteria**:
- [ ] AC-T25.1: The 11 ids pass, and Task 6's 16 tests pass unchanged.

**RED split**: 11 ids; 6 F (`writes_one_root_record_per_pass`, `copies_the_report_from_its_pass_root`,
`copies_the_profile_record`, `refuses_a_first_pass_record_for_another_root`,
`refuses_a_malformed_second_pass_record`, `refuses_a_replaced_blob`); 5 P: both
`refuses_both_root_record_forms` ids (at RED the unknown flag, and a missing `--root-record`, already
give `internal:UsageError`), `accepts_an_identical_re_add`, `appends_a_second_reading_after_an_earlier_resmoke`
and `accepts_a_changed_authoring_file` (at RED nothing refuses a re-add, and `ref_moved` already
exists). Each P is shown able to fail by its row: rows 1, 2, 9, 11 and 10.

**Mutation rows** (11; markers 9 new). `file` the probe; tests in `tests/test_grok_audit_surface_probe.py`.

| # | name | marker | replace | test |
|---|---|---|---|---|
| 1 | `p-record-forms-both` | `# M:GAS-RECORD-FORMS-BOTH` | condition never fires (the pass records win) | `test_record_cycle_refuses_both_root_record_forms[both]` |
| 2 | `p-record-forms-neither` | `# M:GAS-RECORD-FORMS-NEITHER` | condition never fires (no record is written) | `test_record_cycle_refuses_both_root_record_forms[neither]` |
| 3 | `p-record-pass-path` | `# M:GAS-RECORD-PASS-PATH` | condition never fires | `test_record_cycle_refuses_a_first_pass_record_for_another_root` |
| 4 | `p-record-pass-loop` | `# M:GAS-RECORD-PASS-LOOP` | only the first record checked | `test_record_cycle_refuses_a_malformed_second_pass_record` |
| 5 | `p-record-pass-name` | `# M:GAS-RECORD-PASS-NAME` | every record written as `root.txt` | `test_record_cycle_writes_one_root_record_per_pass` |
| 6 | `p-record-pass-report` | `# M:GAS-RECORD-PASS-REPORT` | always the stem dir's copy | `test_record_cycle_copies_the_report_from_its_pass_root` |
| 7 | `p-record-profile` | `# M:GAS-RECORD-PROFILE` | `.log.profile` not matched | `test_record_cycle_copies_the_profile_record` |
| 8 | `p-commit-replace` | `# M:GAS-COMMIT-REPLACE` | condition never fires | `test_commit_data_refuses_a_replaced_blob` |
| 9 | `p-commit-replace-identical` | `# M:GAS-COMMIT-REPLACE` | fires whenever the parent holds the path | `test_commit_data_accepts_an_identical_re_add` |
| 10 | `p-commit-authoring` | `# M:GAS-COMMIT-AUTHORING` | no path exempt | `test_commit_data_accepts_a_changed_authoring_file` |
| 11 | `p-commit-ref-moved-append` | `# M:GAS-COMMIT-REF-MOVED` (Task 6's marker; no new site) | condition never fires | `test_commit_data_appends_a_second_reading_after_an_earlier_resmoke` |

**Dependencies on other tasks**: Task 24 (`--work-dir` in the fixtures this Task extends).

---

## Task 26: the reading namespace, the run record and `cycle_token` trigger (8)

**Production file**: `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py` (extend)
**Test files**: `h-mad/tests/test_grok_audit_surface_probe.py` (extend and modify),
`h-mad/tests/test_grok_audit_surface_smoke.py` (modify), `h-mad/tests/grokauditfixtures.py` (modify)
**Task shape**: `new-behaviour`

**Description**:
1. **Parsers (D10).** `parse_run_line(text)`: exactly one line starting `RUN: ` (`# M:GAS-PARSE-RUN-ONE`),
   exactly the keys `checkout` and `home` (`# M:GAS-PARSE-RUN`), each once (`# M:GAS-PARSE-RUN-DUP`) and
   non-empty, else `None`. `parse_profile_line(text)`: exactly one `GROK-PROFILE:` line with `profile`
   and `origin` once and non-empty (`# M:GAS-PARSE-PROFILE`), `origin` in `{default, override}`
   (`# M:GAS-PARSE-PROFILE-ORIGIN`), else `None`.
2. **The reading namespace (D2, D3, D8).** `score` and `rescore` take `--run-id`; with it the reading
   root is `calibration/runs/<run-id>/`, without it the calibration directory itself
   (`# M:GAS-RUN-ID`). `rescore --run-id` is required by D2's grammar.
3. **`containment_checks(s2_dir, sources)`, passes (a) and (b) (D12)**, called by `extract` and
   `score` after triggers (1)–(7) for every document, over every recorded S2 cycle in document and cycle
   order: (a) `s2/run.txt` through `parse_run_line`, absent or `None` → `list_changed:unrecorded`
   (`# M:GAS-CONTAIN-RUN-RECORD`); then every pass's `pN.root.txt` (N from 1 to `P`, `P` from `--surfaces`) through
   `parse_root_line`, absent or `None` → `list_changed:unrecorded` (`# M:GAS-CONTAIN-ROOT-UNRECORDED`);
   (b) trigger (8), `cycle_token:` followed by the cycle (`d1.v1` form), one marked guard per shape:
   `# M:GAS-CYCLE-ROOT-COUNT`, `# M:GAS-CYCLE-ROOT-SAME`, `# M:GAS-CYCLE-ROOT-NESTED`,
   `# M:GAS-CYCLE-ROOT-CALIBRATION`, `# M:GAS-CYCLE-ROOT-LIST`. Pass (c) is Task 27's.
4. **The list check (D9 step 5).** Records in record order: `s1/<surface>/root.txt`, then under the
   reading root `resmoke/<surface>/root.txt` (`# M:GAS-LIST-RESMOKE`), then each S2 cycle's
   `p1.root.txt` … `p<P>.root.txt` with `P` from `--surfaces` (`# M:GAS-LIST-PASS-RECORDS`); an S2 cycle
   with no parseable `--surfaces` refuses `list_changed:unrecorded` (`# M:GAS-LIST-SURFACES`); an S2
   cycle's `root.txt` is not read.
5. **The calibration-data set (D3).** The metadata names become D3's v1.11 list, the per-pass `pN.root.txt`,
   `pN.profile.txt` and `pN.scan.txt`, each reading's `resmoke/run.txt`, `s2/run.txt` and every file
   under `resmoke/canary/` added, with the `runs/*` globs (`# M:GAS-CALSET-METADATA`).
6. **The smoke (D11 v1.8).** Step 3 refuses a non-grok counts item whose log carries all three of `end`,
   `tool_call` and `tool_call_update`: `input_unparseable:<data>/grok/auditcycle.txt`
   (`# M:GAS-SMOKE-EFFORT-NONGROK-CONTRADICTED`).

**Trigger (8)'s count shape (orchestrator ruling on v1.5's OPEN-DECISION, option (b)).** An absent
per-pass record is `list_changed` trigger (a), refused by pass (a) before pass (b) runs, so the count
shape cannot be "one root record fewer than the cycle has passes". It is restated as **"more root
records than the cycle has passes"**: a `pN.root.txt` with N above `P` beside a cycle whose records
1…`P` are all present and well formed, which is the stale or shared-root record that shape exists to
catch. `# M:GAS-CYCLE-ROOT-COUNT` fires on it, reachable because pass (a) reads only records 1…`P`.
Spec AC-5.5 and design D12 are being changed to this wording in parallel; this plan cites the ruling
and does not edit them.
7. **The hint lookup reads the finding's own pass record (impl-plan audit cycle 3, should-fix).** At
   `121ae4ce` `extract_all` reads the cycle's `root.txt` for every finding's quote hints
   (`grok_audit_probe.py` line 1078: `root_record = path.parent.parent / "root.txt"`). An S2 cycle has
   no `root.txt` after S0c, so a pass 2 or pass 3 quote naming its own root by absolute path would be
   looked up on the live file system. The lookup becomes the finding's pass record,
   `pN.root.txt` with N its report's `pass`, when the cycle holds per-pass records, and `root.txt`
   otherwise (`# M:GAS-HINT-PASS-ROOT`). Hints stay advisory and never move the score (AC-4.4).

**Churn (modified, not duplicated).** S2 fixtures (`write_extract_cycle`, `build_score_inputs`,
`build_rescore_inputs` in `h-mad/tests/grokauditfixtures.py`) write `pN.root.txt` per pass and
`s2/run.txt`, and the score and rescore fixtures use the reading layout `calibration/runs/<run-id>/`
with `--run-id`; `test_rescore_reproduces_the_score_and_removes_its_temp_dirs` passes `--run-id`. These
land in the GREEN commit and are regression guards. Renamed: `test_calibration_data_set_is_the_directory_minus_six_named_files`
→ `test_calibration_data_set_is_the_directory_minus_the_metadata_names`;
`test_smoke_parsed_item_with_all_three_types_is_the_stated_residual` →
`test_smoke_parsed_item_with_all_three_types_refuses`;
`test_smoke_deep_grok_types_with_unparseable_item_is_the_stated_residual` →
`test_smoke_deep_grok_types_with_unparseable_item_refuses`.

**Tests** (26 functions, 32 node ids):
- Parsers (4 functions, 7 ids): `test_run_line_parser_reads_the_runbook_line` (the runbook's own
  `printf`, D8), `test_run_line_parser_rejects_a_malformed_run_line` `[missing-home]`, `[repeated-key]`,
  `[two-lines]`; `test_profile_line_parser_reads_the_exec_line` (the line Task 18's `exec` writes, read
  from a real `$log.profile`), `test_profile_line_parser_rejects_a_malformed_profile_line`
  `[missing-origin]`, `[origin-outside]`.
- Trigger (8) (6): `test_cycle_token_more_root_records_than_passes` (a three-pass cycle with
  `p1.root.txt`–`p3.root.txt` well formed and a stale `p4.root.txt` beside them:
  `cycle_token:d1.v1`),
  `test_cycle_token_two_passes_same_root`, `test_cycle_token_root_inside_another`,
  `test_cycle_token_roots_differ_in_calibration`, `test_cycle_token_roots_differ_in_list_blob`, and the
  must-not-refuse `test_cycle_with_one_identical_root_per_pass_does_not_refuse`.
- Run record and root records (6 functions, 9 ids): `test_list_changed_run_record_absent`;
  `test_list_changed_run_record_malformed` `[no-run-line]`, `[two-run-lines]`, `[missing-home]`,
  `[extra-key]` (spec AC-5.5's four malformed (c) shapes, each alone; design v1.11 names one test);
  `test_containment_pass_root_record_absent`, `test_containment_no_ready_line`,
  `test_containment_two_ready_lines`, `test_containment_ready_line_without_list_blob`. Each is
  `list_changed:unrecorded`, never skipped.
- List check (3): `test_list_changed_one_pass_root_record_absent`, `test_list_changed_pass_records_without_surfaces`,
  `test_list_check_reads_resmoke_records`. The first two carry a valid S2 `root.txt` too, so at RED the
  pre-v1.6 reader passes them and they fail.
- `--run-id` (2, plan-added: D8 states both behaviours and names no fixture):
  `test_score_reads_the_reading_named_by_run_id` (two readings, `run-a` and `run-b`, with different
  labels: the token is `run-b`'s), `test_score_without_run_id_on_a_namespaced_reading_refuses`
  (`cycle_token`, D8's "a forgotten `--run-id` refuses").
- Smoke (3): `test_smoke_parsed_item_with_all_three_types_refuses`,
  `test_smoke_deep_grok_types_with_unparseable_item_refuses` (each
  `SMOKE: UNREADABLE reason=input_unparseable:<data>/grok/auditcycle.txt`, exit 2),
  `test_smoke_rederives_from_an_exported_namespaced_reading` (a synthetic branch commit holding
  `calibration/runs/<run-id>/resmoke/`, exported with `git archive`, gives the same token as the
  on-disk reading, and that token is `SMOKE: PASS`).
- `test_calibration_data_set_is_the_directory_minus_the_metadata_names` (1).
- Hint lookup (1): `test_hint_resolves_a_pass_2_absolute_quote_through_its_pass_record` (an S2 cycle
  with three per-pass records and no `root.txt`; a pass-2 finding whose `quote:` names a seeded span by
  its absolute path under pass 2's root; the live roots are deleted before `extract` runs; the hint is
  a `HINT:` line for that finding reading `candidate-hit:` and the seed's id, not `candidate-fabrication`, and the
  `FINDINGS: WRITTEN` token is the one the same tree gives with every hint removed). At RED the lookup
  reads the absent `root.txt`, the quote stays absolute, and the deleted file gives
  `candidate-fabrication`, so it fails.

**Acceptance Criteria**:
- [ ] AC-T26.1: The 32 ids pass.
- [ ] AC-T26.2: The token parsers in the probe are exactly D10's six: `parse_auditcycle`,
  `parse_effort_items`, `parse_root_line`, `parse_run_line`, `parse_profile_line` and the imported
  `_gate_token`; no mode reads a `RUN:` or `GROK-PROFILE:` line any other way.

**RED split**: 32 ids; 30 F; 2 P: `test_cycle_with_one_identical_root_per_pass_does_not_refuse` (a
must-not-refuse negative control; nothing refuses at RED) and
`test_smoke_rederives_from_an_exported_namespaced_reading` (the smoke reads only `--data`, D11 "with no
code change"; it pins equality of two derivations whose shared token is pinned by the `test_smoke_pass`
rows, so it has no row of its own).

**Mutation rows** (28; markers 19 new). `file` the probe; tests in
`tests/test_grok_audit_surface_probe.py` except rows 16–17 (`tests/test_grok_audit_surface_smoke.py`).
Rows 19–27 change the printed reason to `list_changed:unrecorded_run` (19–23) or
`list_changed:unrecorded_root` (24–27) rather than disarm, because Task 27's scan reads the run and root
records those guards reject (Rules, "S0c scripts").

| # | name | marker | replace | test |
|---|---|---|---|---|
| 1 | `p-parse-run-keys` | `# M:GAS-PARSE-RUN` | key set not checked | `test_run_line_parser_rejects_a_malformed_run_line[missing-home]` |
| 2 | `p-parse-run-dup` | `# M:GAS-PARSE-RUN-DUP` | a repeated key accepted | `test_run_line_parser_rejects_a_malformed_run_line[repeated-key]` |
| 3 | `p-parse-run-one` | `# M:GAS-PARSE-RUN-ONE` | the first `RUN:` line read | `test_run_line_parser_rejects_a_malformed_run_line[two-lines]` |
| 4 | `p-parse-profile-keys` | `# M:GAS-PARSE-PROFILE` | key set not checked | `test_profile_line_parser_rejects_a_malformed_profile_line[missing-origin]` |
| 5 | `p-parse-profile-origin` | `# M:GAS-PARSE-PROFILE-ORIGIN` | any value accepted | `test_profile_line_parser_rejects_a_malformed_profile_line[origin-outside]` |
| 6 | `p-cycle-root-count` | `# M:GAS-CYCLE-ROOT-COUNT` | condition never fires | `test_cycle_token_more_root_records_than_passes` |
| 7 | `p-cycle-root-same` | `# M:GAS-CYCLE-ROOT-SAME` | condition never fires | `test_cycle_token_two_passes_same_root` |
| 8 | `p-cycle-root-nested` | `# M:GAS-CYCLE-ROOT-NESTED` | condition never fires | `test_cycle_token_root_inside_another` |
| 9 | `p-cycle-root-calibration` | `# M:GAS-CYCLE-ROOT-CALIBRATION` | condition never fires | `test_cycle_token_roots_differ_in_calibration` |
| 10 | `p-cycle-root-list` | `# M:GAS-CYCLE-ROOT-LIST` | condition never fires | `test_cycle_token_roots_differ_in_list_blob` |
| 11 | `p-list-pass-records` | `# M:GAS-LIST-PASS-RECORDS` | only `p1.root.txt` enumerated | `test_list_changed_one_pass_root_record_absent` |
| 12 | `p-list-surfaces` | `# M:GAS-LIST-SURFACES` | condition never fires (no records enumerated) | `test_list_changed_pass_records_without_surfaces` |
| 13 | `p-list-resmoke` | `# M:GAS-LIST-RESMOKE` | `resmoke/` not enumerated | `test_list_check_reads_resmoke_records` |
| 14 | `p-run-id-ignored` | `# M:GAS-RUN-ID` | the reading root is always the calibration directory | `test_score_reads_the_reading_named_by_run_id` |
| 15 | `p-run-id-newest` | `# M:GAS-RUN-ID` | without `--run-id`, the last `runs/*` in sort order | `test_score_without_run_id_on_a_namespaced_reading_refuses` |
| 16 | `p-smoke-nongrok-parsed` | `# M:GAS-SMOKE-EFFORT-NONGROK-CONTRADICTED` | condition never fires (disarmed to acceptance) | `test_smoke_parsed_item_with_all_three_types_refuses` |
| 17 | `p-smoke-nongrok-deep` | `# M:GAS-SMOKE-EFFORT-NONGROK-CONTRADICTED` | the same | `test_smoke_deep_grok_types_with_unparseable_item_refuses` |
| 18 | `p-calset-metadata` | `# M:GAS-CALSET-METADATA` | the six S0 names | `test_calibration_data_set_is_the_directory_minus_the_metadata_names` |
| 19 | `p-contain-run-record-absent` | `# M:GAS-CONTAIN-RUN-RECORD` | reason `list_changed:unrecorded_run` | `test_list_changed_run_record_absent` |
| 20 | `p-contain-run-record-no-line` | `# M:GAS-CONTAIN-RUN-RECORD` | the same | `test_list_changed_run_record_malformed[no-run-line]` |
| 21 | `p-contain-run-record-two-lines` | `# M:GAS-CONTAIN-RUN-RECORD` | the same | `test_list_changed_run_record_malformed[two-run-lines]` |
| 22 | `p-contain-run-record-missing-home` | `# M:GAS-CONTAIN-RUN-RECORD` | the same | `test_list_changed_run_record_malformed[missing-home]` |
| 23 | `p-contain-run-record-extra-key` | `# M:GAS-CONTAIN-RUN-RECORD` | the same | `test_list_changed_run_record_malformed[extra-key]` |
| 24 | `p-contain-root-absent` | `# M:GAS-CONTAIN-ROOT-UNRECORDED` | reason `list_changed:unrecorded_root` | `test_containment_pass_root_record_absent` |
| 25 | `p-contain-root-no-line` | `# M:GAS-CONTAIN-ROOT-UNRECORDED` | the same | `test_containment_no_ready_line` |
| 26 | `p-contain-root-two-lines` | `# M:GAS-CONTAIN-ROOT-UNRECORDED` | the same | `test_containment_two_ready_lines` |
| 27 | `p-contain-root-no-list-blob` | `# M:GAS-CONTAIN-ROOT-UNRECORDED` | the same | `test_containment_ready_line_without_list_blob` |
| 28 | `p-hint-pass-root` | `# M:GAS-HINT-PASS-ROOT` | always the cycle's `root.txt` | `test_hint_resolves_a_pass_2_absolute_quote_through_its_pass_record` |

**Dependencies on other tasks**: Task 25 (the `pN.root.txt` and `pN.profile.txt` records), Task 18
(the `GROK-PROFILE:` line the parser fixture reads).

---

## Task 27: the containment scan and the `CONTAINMENT:` lines

**Production file**: `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py` (extend: imports
`h_mad_tool_calls`, the fifth D1 import)
**Test files**: `h-mad/tests/test_grok_audit_surface_probe.py` (extend), `h-mad/tests/grokauditfixtures.py` (extend)
**Task shape**: `wiring` — the probe must take every grok pass's scan from `h_mad_tool_calls.scan_log`,
never a second copy; the refusal rules over the scan's word and the published lines are new behaviour
carried in the same Task, and their RED split is stated below.
**WIRE 1**: `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py:containment_checks` → `h_mad_tool_calls.scan_log`
**WIRE-PIN 1**: `h-mad/tests/test_grok_audit_surface_probe.py::test_out_of_root_absolute_path_outside_the_root`
**WIRE 2**: `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py:containment_lines` → `h_mad_tool_calls.scan_log`
**WIRE-PIN 2**: `h-mad/tests/test_grok_audit_surface_probe.py::test_containment_lines_name_every_standing_pass`

**Description**: D12 pass (c) and D13's containment lines. Pass (c): for each grok pass of every
recorded S2 cycle (`# M:GAS-CONTAIN-EVERY-CYCLE`), `scan_log` on the pass's `pN.log` with that pass's root
`path=`, and `checkout=`/`home=` from `s2/run.txt` (`# M:GAS-CONTAIN-SCAN`); a word `OUT_OF_ROOT`
(`# M:GAS-CONTAIN-OUT-OF-ROOT`, AC-5.4 trigger (1)) or `UNREADABLE` (`# M:GAS-CONTAIN-UNREADABLE`,
trigger (2)) refuses `out_of_root:` followed by the cycle (`d1.v1` form); a codex or agy pass never refuses (`# M:GAS-CONTAIN-GROK-ONLY`).
`containment_lines(...)`, called by `score` after the observational lines and never by `verdict`: one
`CONTAINMENT:` line per pass of every standing cycle from `scan_log`'s counts (`# M:GAS-CONTAIN-LINES`),
a grok line adding the `profile=` and `origin=` values of `pN.profile.txt`, read through `parse_profile_line`, or
`profile=none` when absent or unparseable, never `strict` (`# M:GAS-CONTAIN-PROFILE`).

**Scaffold that makes each WIRE-PIN's RED an assertion about the caller.** At RED the probe has Task
26's `containment_checks` passes (a) and (b), `h_mad_tool_calls` exists (Task 21), and the probe
neither imports it nor prints `CONTAINMENT:`. WIRE-PIN 1 runs `score` on a synthetic score tree whose
one grok `p3.log` holds a `tool_call` naming an absolute path outside its root and asserts the last
stdout line `SEEDSCORE: UNREADABLE reason=out_of_root:d1.v1`; at RED the tree scores and prints a
non-UNREADABLE `SEEDSCORE:` line. WIRE-PIN 2 asserts one `CONTAINMENT:` line per standing pass with
`scan_log`'s own counts for the same log, computed in the test by calling `scan_log` directly; at RED
there is no such line. Each fails on its assertion, never on an import.

**Wire cuts at GREEN**: row 1 cuts WIRE 1 and row 2 forces it; row 3 cuts WIRE 2.

**Tests** (18 functions, 24 node ids), each on a synthetic grok NDJSON log with its one trigger alone:
- Refusals (10): `test_out_of_root_absolute_path_outside_the_root`, `test_out_of_root_live_checkout`,
  `test_out_of_root_after_a_non_json_line` (the positive-control shape), `test_out_of_root_absent_log`,
  `test_out_of_root_log_without_event`, `test_out_of_root_on_a_non_standing_cycle`,
  `test_out_of_root_other_session_dir`, `test_out_of_root_sessions_dir_itself`,
  `test_out_of_root_other_grok_path`, `test_out_of_root_mixed_exempt_and_outside`.
- Must not refuse (5 functions, 11 ids): `test_clean_grok_log_does_not_refuse`,
  `test_exempt_dev_path_does_not_refuse`, `test_exempt_own_session_dir_does_not_refuse` and
  `test_exempt_grok_skills_does_not_refuse` (each publishing `exempt=1`, the last two parametrized
  `[absolute]`, `[tilde]`, `[home]`, `[brace]`), and `test_codex_or_agy_count_does_not_refuse`
  (publishing its count; a codex pass naming an own-looking session path or `$HOME/.grok/skills/` counts
  it in `out_of_root`). Each asserts its published `CONTAINMENT:` counts beside the non-refusal.
- Containment lines (3): `test_containment_lines_name_every_standing_pass`,
  `test_containment_line_profile_none_without_record`, `test_containment_lines_never_move_the_verdict`
  (two trees with equal labels and different scans: equal `SEEDSCORE:` lines, different `CONTAINMENT:`
  lines).

**Acceptance Criteria**:
- [ ] AC-T27.1: The two WIRE-PINs pass, and each fails when only its wire is cut (rows 1 and 3).
- [ ] AC-T27.2: `grep -c 'h_mad_tool_calls.scan_log(' docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py`
  prints 2 (matching lines: the two wires), and the probe holds no path-grammar or classification code
  of its own (`grep -c 'grok/sessions' docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py`
  prints 0).
- [ ] AC-T27.3: No published line of the probe starts with `TOOLSCAN:` (Task 2's
  `test_no_published_line_uses_another_modes_prefix` still passes).

**RED split** (stated for the record; the WIRE-PINs gate this Task): 24 ids; 24 F (no scan at RED, so
no refusal and no `CONTAINMENT:` line, which every must-not-refuse test also asserts), 0 P.

**Residual, stated exactly.** `test_containment_lines_never_move_the_verdict` has no row: its negative
is a verdict that reads containment, which no one-line mutation of the probe produces without a new
data flow, so that independence is shown by the test only. The probe-level fixtures whose difference
lies in the scan's classification (`live_checkout`, `other_session_dir`, `sessions_dir_itself`,
`other_grok_path`, `mixed_exempt_and_outside`, and the exempt ids) are shown able to fail by Task 21's
rows on the same classification, which target the containment module's twin fixtures.

**Mutation rows** (9; markers 7 new). `file` the probe; tests in `tests/test_grok_audit_surface_probe.py`.

| # | name | marker | replace | test |
|---|---|---|---|---|
| 1 | `p-contain-scan-severed` | `# M:GAS-CONTAIN-SCAN` | a constant `CLEAN` result with zero counts | `test_out_of_root_absolute_path_outside_the_root` |
| 2 | `p-contain-scan-forced` | `# M:GAS-CONTAIN-SCAN` | a constant `OUT_OF_ROOT` result | `test_clean_grok_log_does_not_refuse` |
| 3 | `p-contain-lines-severed` | `# M:GAS-CONTAIN-LINES` | counts from a constant zero result | `test_containment_lines_name_every_standing_pass` |
| 4 | `p-contain-out-of-root` | `# M:GAS-CONTAIN-OUT-OF-ROOT` | `OUT_OF_ROOT` not refused | `test_out_of_root_absolute_path_outside_the_root` |
| 5 | `p-contain-unreadable-absent` | `# M:GAS-CONTAIN-UNREADABLE` | `UNREADABLE` not refused | `test_out_of_root_absent_log` |
| 6 | `p-contain-unreadable-no-event` | `# M:GAS-CONTAIN-UNREADABLE` | the same | `test_out_of_root_log_without_event` |
| 7 | `p-contain-every-cycle` | `# M:GAS-CONTAIN-EVERY-CYCLE` | standing cycles only | `test_out_of_root_on_a_non_standing_cycle` |
| 8 | `p-contain-profile-strict` | `# M:GAS-CONTAIN-PROFILE` | a missing record prints `profile=strict` | `test_containment_line_profile_none_without_record` |
| 9 | `p-contain-grok-only` | `# M:GAS-CONTAIN-GROK-ONLY` | every surface's scan refuses | `test_codex_or_agy_count_does_not_refuse` |

**Dependencies on other tasks**: Task 21 (`scan_log`), Task 26 (passes (a) and (b), `parse_run_line`,
`parse_profile_line`, the reading layout).

---

## Task 28: the FR-11 entry-contract text

**Production files**: `h-mad/SKILL.md`, `h-mad/references/agent-substrate.md`,
`h-mad/tests/mutation-specs/grok_audit_surface.json` (K8)
**Test file**: `h-mad/tests/test_grok_audit_surface_docs.py` (extend)
**Task shape**: `new-behaviour`

**Description**: D14 "FR-11's entry contract". In `h-mad/SKILL.md`, the bullet that begins
"**`exec grok`** — an explicit RED/GREEN implementer fallback" (line 621 at `9628c857`) gains D14's
sentence, verbatim, after its last sentence. In `h-mad/references/agent-substrate.md`, the `exec grok`
row (line 34 at `9628c857`): `[--sandbox <mode>]` becomes `[--sandbox <profile>] [--allow-weaker-sandbox]`
in the command cell, and the sentence "`GROK_SANDBOX` is inherited, and `--sandbox` is forwarded when
supplied." is replaced by D14's replacement sentence, verbatim. Doc tests read with `titled_section` and
collapse whitespace.

**Tests** (2): `test_exec_grok_bullet_states_the_strict_contract`,
`test_agent_substrate_grok_row_states_the_strict_default`.

**Acceptance Criteria**:
- [ ] AC-T28.1: The 2 tests pass; `tests/test_grok_fallback_docs.py::test_agent_substrate_documents_exec_grok_and_grok_sandbox`
  passes unchanged (the replacement keeps `GROK_SANDBOX` in the row).
- [ ] AC-T28.2: K8's find occurs once in `h-mad/SKILL.md` after the edit (`grep -cF`, 1 matching line;
  0 before).

**RED split**: 2 nodes; 2 F, 0 P. Regression guards: `h-mad/tests/test_grok_fallback_docs.py`.

**Mutation rows** (1), the design's:

| name | file | find | replace | test |
|---|---|---|---|---|
| `exec-grok-strict-sentence-pin` (K8) | `SKILL.md` | `` `--allow-weaker-sandbox` is also given `` | `` `--allow-weaker-sandbox` is optional `` | `tests/test_grok_audit_surface_docs.py::test_exec_grok_bullet_states_the_strict_contract` |

The agent-substrate pin's discrimination is its RED (the Task 1 precedent); the design names no row for
it.

**Dependencies on other tasks**: Tasks 18 and 19 (the text describes their behaviour).

---

## Task 29: the S0c Phase 5e verdict

**Production files**: none
**Test files**: none
**Task shape**: `gate` — reads verdicts over what Tasks 18–28 built; writes no production file.

**Description**: One run over the whole spec and the cross-spec checks, from the S0c branch's
worktree root.

```bash
rtk proxy /opt/anaconda3/bin/python3.11 -m pytest --version
rtk proxy /opt/anaconda3/bin/python3.11 -m pytest h-mad/tests -q -p no:cacheprovider
rtk proxy /opt/anaconda3/bin/python3.11 -m pytest h-mad/tests --collect-only -q -p no:cacheprovider | tail -1
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/grok_audit_surface.json
python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/grok_audit_surface.json
for s in $(grep -l '"scripts/hmad-dispatch.sh"' h-mad/tests/mutation-specs/*.json); do python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors "$s" | tail -1; done
git ls-files 'h-mad/tests/*' | grep -E '\.(plan|design|impl-plan|spec)\.md$'
grep -c 'M:GAS-' docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py
grep -c '# M:' h-mad/scripts/hmad-dispatch.sh
grep -c '# M:TOOLSCAN-' h-mad/scripts/h_mad_tool_calls.py
grep -c '# M:' h-mad/scripts/h_mad_grok_containment.py
/opt/anaconda3/bin/python3.11 -c 'import json; print(len(json.load(open("h-mad/tests/mutation-specs/grok_audit_surface.json"))["mutations"]))'
```

**Acceptance Criteria**:
- [ ] AC-T29.1: The first command prints a pytest version; the full suite's summary line shows no
  failure; the collection line is at least the 5c floor plus 215 (S0c's preamble).
- [ ] AC-T29.2: `MUTATION: ALL_CAUGHT` with `untargeted=0/376` and
  `crash_kills=0`, and `ANCHORS: ANCHORS_OK`, read from the token lines.
- [ ] AC-T29.3: Every spec the loop names prints `ANCHORS: ANCHORS_OK` (28 specs name
  `scripts/hmad-dispatch.sh` at `9628c857`; the loop re-derives the set).
- [ ] AC-T29.4: The `git ls-files` line prints nothing.
- [ ] AC-T29.5: The four marker counts (matching lines) and the row count (rows) are re-derived at this
  Task's sha and reported with their units. This plan expects 175, 48, 21, 34 and 376; a different figure is reported against the Task whose table it contradicts, never
  silently accepted.

**Dependencies on other tasks**: Tasks 18–28.

---

## Task 30: the S0c live round trip (operator, before merge)

**Production file**: `docs/03-analysis/grok-audit-surface.s0c-live-roundtrip.md` (create, on the S0c
branch, so it reaches `main` with the merge)
**Test files**: none
**Task shape**: `operational` — runs the S0c branch's wrapper live once against no calibration data.

**Description**: Design D8 "S0c: the live, non-seeded round trip", run by the operator from the S0c
branch's worktree after Task 29 is green and before the merge. No export, ledger or seeded file exists
anywhere it runs, so FR-11's gating does not forbid the grok calls.

```bash
KEEP="$HOME/.local/state/h-mad/grok-audit-surface"; mkdir -p "$KEEP"
X="$KEEP/s0c-$(date -u +%Y%m%dT%H%M%SZ)"; mkdir "$X" "$X/roots" "$X/canary"
h-mad/bin/hmad-dispatch grok-canary --run-dir "$X" | tee "$X/canary.stdout.txt"
python3 h-mad/scripts/h_mad_grok_containment.py require --verb grok-canary --token-file "$X/canary.stdout.txt"
G="$X/wt"; git init -q "$G"; printf '.h-mad/*\n' > "$G/.gitignore"
printf 'Reply with the single word OK.\n' > "$X/wt-prompt.txt"
git -C "$G" status --porcelain --untracked-files=all > "$X/status-before.txt"
h-mad/bin/hmad-dispatch exec grok "$X/wt-prompt.txt" --cd "$G" --log "$X/wt.log" > "$X/wt.stdout.txt" 2> "$X/wt.stderr.txt"
tail -1 "$X/wt.stdout.txt"
grep -c 'hmad-dispatch: exec: grok stopReason=' "$X/wt.stderr.txt"
grep -c 'EMPTY final message\|grok staging:' "$X/wt.stderr.txt"
grep -c '"type": *"end"' "$X/wt.log"
cat "$X/wt.log.profile"
git -C "$G" status --porcelain --untracked-files=all > "$X/status-after.txt"
cmp "$X/status-before.txt" "$X/status-after.txt" && echo STATUS=same || echo STATUS=changed
ls -d "$G"/.h-mad/tmp/hmad_exec_grok.* 2>/dev/null | wc -l | tr -d ' '
git rev-parse HEAD
```

The canary log is not scanned (spec AC-6.6: the canary "is not scanned").

**Acceptance Criteria**:
- [ ] AC-T30.1: `require` prints `REQUIRE: OK`.
- [ ] AC-T30.2: The work-tree dispatch ran to completion, which is checked before its cleanup
  results are read (impl-plan audit cycle 3: a staging refusal also leaves `git status` unchanged and no
  staging directory, so those two alone cannot tell a completed dispatch from one that never launched).
  Four positive markers, all required: the last line of `$X/wt.stdout.txt` is `OK`; `$X/wt.stderr.txt`
  holds 1 `grok stopReason=` line (printed only on a complete transcript with a final message,
  `hmad-dispatch.sh` line 3213 at `121ae4ce`) and 0 `EMPTY final message` or `grok staging:` lines;
  `$X/wt.log` holds at least one line matching `"type": *"end"`; `$X/wt.log.profile` reads
  `GROK-PROFILE: profile=strict origin=default`.
- [ ] AC-T30.5: Only then: `STATUS=same`, and the staging-directory count prints `0`.
- [ ] AC-T30.3: The evidence file holds every command above verbatim, the canary's token line,
  `$X/canary/grok.txt`'s line, the `GROK-PROFILE:` line of `$X/canary/log.ndjson.profile`, the
  work-tree leg's four positive markers (AC-T30.2), both `git status` captures, and the S0c branch sha `git rev-parse HEAD` printed; it carries no calibration
  data.
- [ ] AC-T30.4: A `REQUIRE: STOP`, a missing positive marker, `STATUS=changed` or a non-zero staging
  count blocks the merge; the
  defect goes back through TDD (a Task's RED), and Task 30 runs again after Task 29 is green again.

**Dependencies on other tasks**: Task 29.

---

## Carry list disposition

| Carry item | Lands in |
|---|---|
| 1 OPEN-DECISION, re-walk before step 6 | Task 5, as `OPEN-DECISION … — resolve in 5d` with implementations (a) and (b) |
| 2 destructive symlink-following reset | Task 5: the no-follow rule; three fixtures, each asserting the link is not followed and is acted on: delete-through directory end to end, and write-through file and write-through parent at `restore_expected`'s own boundary (an end-to-end fixture cannot see those two guards, audit cycle 1); three rows; the concurrent-writer residual stated |
| 3 reset fixtures' default parent and `--purpose s1 --doc d1` | Task 5, "Fixtures" |
| 4 `test_smoke_unrecognised_effort_item_refuses` and its P-row | Task 7 (`p-smoke-effort-unknown`) |
| 5 one grok type-set reader, or the exact open class | Task 7: `grok_log_types`, one difference from `scan_grok` stated exactly; the design's "guaranteed" and its `RecursionError` clause reported |
| 6 agy provenance `$STEM` placement | Task 15 step 5; Task 16 publishes it in the runbook |
| 7 (measurement) X3/X4 find the collapse marker | "Measurement acknowledgements" below; Task 8's X3/X4 rows find the marked line |
| 8 (measurement) "seven" vs "eight" reset tests | "Measurement acknowledgements" below |
| 9 pre-S1 `exec agy` tracer | Task 0 (run; its kept reading is cited in Task 15's description) |
| 10 wrong-file UNREADABLE needs a new smoke | Task 7 (stated), Task 15 step 6, Task 16 runbook; spec gap reported |
| 11 collapse marker, per-alternative P-rows, re-derived counts | Tasks 5, 7, 8 (rows), Task 14 (AC-T14.4) |
| 12 argparse usage errors | Task 2: every argparse exit path (`error()`, help, version, abbreviation) ends on the mode's token (`_TokenArgumentParser` at every level, `add_help=False`, `allow_abbrev=False`, the `--data` path read from raw argv); `test_usage_error_prints_the_mode_token`, `test_help_flag_prints_the_mode_token`, `test_abbreviated_flag_is_a_usage_error`; the no-mode argv per the operator ruling (`PROBE: UNREADABLE reason=unknown_mode`, `test_unknown_mode_prints_the_probe_token`) |
| 13 `--reset` with a non-`s1` purpose | Task 5 (`ResetPurposeNotS1`, `test_build_root_reset_refuses_a_non_s1_purpose`) |
| 14 step-3 wrong-file reachability | Task 7 (synthetic pairing stated), Task 6 (`test_record_cycle_copies_stem_files_byte_for_byte`) |
| 15 residual-(2) depth from `GROK_MAX_DEPTH` | Task 7 |

## Measurement acknowledgements

Both are readings of the design text at `30917a1a` (unchanged since `a6a1571a`); neither is moved by
this plan, and neither has a Task.

- **Carry 7.** Re-run: `grep -n 'M:GAS-' docs/02-design/features/grok-audit-surface.design.md`.
  Reading: `M:GAS-COLLAPSE-WIRE` occurs 2 times in the design (lines 296 and 555), neither inside the
  D12 fenced code block (lines 301–307), which holds only the `MUST-COUNT` and `SHOULD-COUNT` markers.
  So the rows preamble's "their finds are the two marked lines of the D12 code block" covers X1, X2,
  X5, X6 and not X3, X4, whose find is the probe line carrying `# M:GAS-COLLAPSE-WIRE` (Task 8).
- **Carry 8.** The carried re-run command, `git diff de149bc6 a6a1571a -- docs/02-design/features/grok-audit-surface.design.md | grep -o 'test_build_root_reset_[a-z_]*' | sort -u`,
  prints 11 distinct names, because it reads context lines as well as additions. The count of names
  new in v1.4 is
  `comm -13 <(git show de149bc6:docs/02-design/features/grok-audit-surface.design.md | grep -o 'test_build_root_reset_[a-z_]*' | sort -u) <(git show a6a1571a:docs/02-design/features/grok-audit-surface.design.md | grep -o 'test_build_root_reset_[a-z_]*' | sort -u) | wc -l`:
  8 distinct test names (3 at `de149bc6`, 11 at `a6a1571a`): seven refusals plus one must-not-refuse,
  as the carry item says, against the v1.4 change log's "seven".

**S0c readings (v1.5), each a tree measurement at `9628c857` that no S0c Task moves before Task 29
re-derives it.** The S0c figures this plan expects after Task 28 (175, 48, 21, 34, 376) are claims over
classes S0c adds to, so they are not frozen here; Task 29 derives them.
- Rows and markers at S0: `len(json.load(open("h-mad/tests/mutation-specs/grok_audit_surface.json"))["mutations"])`
  prints 180 (rows); `grep -c 'M:GAS-' docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py`
  prints 125 and `grep -c '# M:' h-mad/scripts/hmad-dispatch.sh` prints 8 (matching lines).
- Suite collection: 7007 (node ids), by S0c's preamble command; the 5c floor is re-measured at the
  branch point.
- Cross-spec anchors: `grep -l '"scripts/hmad-dispatch.sh"' h-mad/tests/mutation-specs/*.json | wc -l`
  prints 28 (files, 151 rows by `grep -h -o`); the launch-line and grok-launch-line finds of
  Rules "Lines other specs anchor on" were found by scanning those rows' `find` first lines against
  `h-mad/scripts/hmad-dispatch.sh` lines 3062, 3106, 3142, 3200, 3220, 3221, 3299, 3617 and 3701 and by
  `grep -l 'gargs'` over the specs (1 file, `grok_wire_reverts.json`, holding 1 row whose `find`
  names `gargs`).
- The test-invocation churn of Task 24: 20 `def` blocks of `h-mad/tests/test_grok_audit_surface_probe.py`
  name `"build-root"`, `"main-leak"`, `"rescore"` or `"--repo"` (functions, by a `def`-block split);
  0 such blocks in `h-mad/tests/test_grok_audit_surface_smoke.py` and `h-mad/tests/grokauditfixtures.py`.
- The calibration ref: the local `refs/heads/calibration/grok-audit-surface` and the remote-tracking
  `refs/remotes/origin/calibration/grok-audit-surface` both read `f7520e72c87e1c3c34e1c5f25fb3807343d84782`
  in this clone (`git rev-parse`, not `ls-remote`), which is why Task 15's precondition reads origin by
  `ls-remote` at run time rather than trusting a carried value.

## Version History
- v1.0: Initial impl-plan draft (Phase 5a, 2026-10-19), from design v1.4 (`a6a1571a`), spec v1.7 and plan v1.5 (`28ec5bfc`); answers no audit cycle (first draft) and places all 15 Phase 5 carry items. 18 Tasks; 165 mutation rows (28 named, 137 P-rows); 111 marker sites. Premises read at `30917a1a`.
- v1.1: 2026-10-19, answers the operator ruling on the AC-5.1 / D2 unknown-mode gap (no audit cycle): an argv whose first word is not one of the nine modes now prints PROBE: UNREADABLE reason=unknown_mode first, then usage, exit 2; Task 2 adds test_unknown_mode_prints_the_probe_token (2 ids) and row p-unknown-mode-token; RED 20 F; totals 166 rows (138 P-rows), 112 marker sites.
- v1.2: 2026-10-19, answers impl-plan audit cycle 1 (agy p1: 1 must, 2 should; codex p2: 6 must, 1 should; on v1.1, document sha256 5490674): every argparse exit path ends on the mode's token (top-level _TokenArgumentParser, add_help=False, allow_abbrev=False, --data read from raw argv; +2 tests, +2 rows); tracebacks only for undeclared exceptions and surfaced in assertion messages (+1 row); in-process loads compile from source (load_probe); Task 5's write and parent no-follow guards tested at restore_expected's boundary; AC-T6.1 split pre-write vs ref_unconfirmed; extract_all takes sources; p-fab-fraction Fraction-preserving; Task 16 adds K4/K5 on MISS/INCONCLUSIVE. Rejected: agy should-fix on Task 17 counts (quoted text absent). Totals 169 rows at S0 (141 P-rows), 171 on MISS/INCONCLUSIVE, 115 marker sites; Task 2 RED 30 F.
- v1.3: 2026-10-19, corrective revision answering impl-plan audit cycle 2 (agy p1: 0 must, 2 should; codex p2: 3 must, 2 should; on v1.2, document sha256 4b8400ba): Refusal and the reset classes subclass ProbeRefusal, with a traceback-absence check on Task 5's refusals; in-process main(argv) assertions forward captured stderr; reproduce commands and outputs beside the argparse and O_NOFOLLOW readings; Test 4's smoke token carries input_unparseable plus the --data value; the smoke's open input reaches refusal_token through _OPEN_INPUT; must-not-parse fixtures for the ROOT and Effort parsers (+2 tests, +2 rows); Task 16 pins grok-runtime.md (test_grok_runtime_states_the_outcome_sentence, row K6). Totals 171 rows at S0 (143 P-rows), 172 or 174 after Task 16, 117 marker sites.
- v1.4: 2026-10-19, answers the advisory delta review of v1.3 (commit 5f10a1d9, document sha256 3015ade9; 0 must, 7 should, 4 nits): _OPEN_INPUT pinned by test_smoke_last_resort_names_the_open_input and p-open-input, with its never-cleared reading stated; the Effort block grammar ([] with no block, terminator, three distinct None conditions with a row each) and its callers (smoke pinned by test_smoke_refuses_a_malformed_effort_block; score as a Task 9 OPEN-DECISION with test_score_maps_a_malformed_effort_block); parse_root_line's None mapped and pinned in Task 6 and Task 10; token assertion before the traceback count; AC-T5.1 names its 10 refusal tests including three Refusal-raising ones; Refusal becomes its token via exc.reason in refusal_token (p-refusal-reason) and the scope narrowing is pinned (p-traceback-scope-reset); Task 16 asserts each outcome sentence's absence on the other branch (K7); reproduce commands for the plain-top-level parser, allow_abbrev and Fraction readings, with python3.15 pinned by absolute path and the exit-site lines printed; rule (3)'s in-process spelling; Task 16's production-files line. Totals 180 rows at S0 (152 P-rows), 182 or 184 after Task 16, 125 marker sites.
- v1.5: 2026-10-20, corrective revision at 9628c857 (not an audit-cycle answer; the impl-plan was last revised at 2ccfd32e) bringing the impl-plan to design v1.11, spec v1.15 and plan v1.11 and answering the OWED-to-impl-plan items of the spec-author rev1-7, plan-author rev1-5 and design-author rev1-4 reports (void-cycle items withdrawn). New S0c Tasks 18-30 on the proposed branch feature/218b-grok-containment: exec grok strict default, override flag and profile record (18); staging, prompt and TMPDIR (19); audit-cycle --pass-root and --halt-file (20); h_mad_tool_calls.py scan (21); quarantine and require (22); grok-canary wiring plant, exec and judge (23); probe --work-dir and re-anchored reset guards (24); per-pass records and add-only commit (25); reading namespace, run record, cycle_token trigger (8), smoke residuals closed (26); containment scan wiring and CONTAINMENT lines (27); entry-contract text and K8 (28); S0c Phase 5e gate (29); operator non-seeded live round trip before merge (30). Task 15 rewritten to design D8's run order with the calibration-ref precondition; Task 16 cites the incident record and the superseded smoke and gains two S3 tests; Task 17 gated on S0c merged and an unhalted, scored fresh S2. Renamed S0 tests updated in place in Tasks 5, 7 and 10. Totals: 31 Tasks (3 wiring); 189 rows added, 369 after Task 28 (368 under Task 26 OPEN-DECISION option (a)), 371 or 373 after Task 16; probe marker sites 174; 200 node ids added, 4 removed.
- v1.6: 2026-10-20, answers impl-plan audit cycle 3, gating round 1 (docs/01-plan/features/grok-audit-surface.impl-plan.audit.v3.p1.md: codex 7 must, 1 should; p2 agy filed none), at 121ae4ce, with the orchestrator ruling on the v1.5 Task 26 OPEN-DECISION (option (b)). Task 26: trigger (8)'s count shape restated as more root records than passes, test_cycle_token_more_root_records_than_passes, GAS-CYCLE-ROOT-COUNT reachable, OPEN-DECISION removed; the hint lookup at grok_audit_probe.py:1078 moves to the finding's pass record (GAS-HINT-PASS-ROOT, test_hint_resolves_a_pass_2_absolute_quote_through_its_pass_record). Task 24: --work-dir is <tmp_path>/scratch, a sibling of build_repo's git checkout; test_reset_precondition_old_new_differential compares the shipped 66ff0894 predicate with the new one over 15 targets, softened verdicts exactly the roots-outside-system-temp class. Task 19: check-ignore runs in the scrubbed git env (row 7b, AC-T19.4). Class closed for Tasks 19, 20 and 23: every exit-2 guard prints and its test asserts its own stderr line. Task 23: the stub grok writes a completed transcript by default, because exec turns an empty final message into rc 3 (hmad-dispatch.sh:3366-3374). Task 30: four positive markers prove the work-tree dispatch ran. Totals: 193 rows added, 373 after Task 28, 375 or 377 after Task 16; probe marker sites 175; 216 node ids added, 4 removed.
- v1.7: 2026-10-20, final corrective revision at b17e1b36 after the round cap (not re-audited), fixing only docs/01-plan/features/grok-audit-surface.impl-plan.audit.v4.p1.md (codex: 3 must, 1 measurement should; p2 agy filed none). Task 18 names and migrates test_hmad_dispatch_exec_grok.py::test_exec_grok_translates_model_effort_sandbox[given] (its options gain --allow-weaker-sandbox in the GREEN commit; ids unchanged, both regression guards). Task 23: test_canary_truncated split into [judge] (canary-judge --rc 0 on a readable end-less log, row 10) and [wrapper] (the real rc 3 from hmad-dispatch.sh:3207-3218 and 3366-3370, cannot_run:grok_rc:3, new row 33). Task 22: test_require_usage_error_still_writes_the_halt_file [unknown-flag] and [missing-token-file], the raw-argv halt path marked M:REQUIRE-FAIL-CLOSED-ARGV with rows 25-26. Measurement: the reset-fixture parent is outside the stand-in system temp (siblings) in Task 5's note and Task 24. Totals: 196 rows added, 376 after Task 28, 378 or 380 after Task 16; containment markers 34; 219 node ids added, 4 removed.
- v1.8: 2026-10-22, answers no audit cycle: brings the plan to design v1.13 (8a27d264, D21) and spec v1.19 (d9f25dc2) after the route (b) ruling (242c26bd); sole author, not audited. New Tasks 14a (assembler PATH_SCOPE_CLAUSE and --path-scope; 10 ids, 6 rows), 14b (wiring: audit-cycle forwards the switch on --pass-root and halts path_scope_missing:pN before the divergence check; stub clause line and knob; verb-assemble-drop re-anchored; 9 ids, 7 rows), 14c (assembler-read, assembler-check, require --verb assembler, tests at the top of the containment module for the 40 s judge budget; 25 ids, 20 rows, 8 of them plan-added) and 14d (gate), placed before Task 15. Task 15 gains the assembler directory, start and end readings, step 9a's gate and --pass-root on the re-smoke; Task 16 gains the D15 assembler stamp, delta sentence and clause, and its row totals move to 413 or 415. Totals: 35 Tasks (4 wiring); 378 rows at d9f25dc2, 411 after Task 14c.
- v1.9: 2026-10-22, answers the impl-plan audit of v1.8 (scratchpad audit-implplan-route-b.md: 2 must, 5 should) and takes design v1.14 (8fd0f637) and spec v1.20 (d78cca8d), under the orchestrator's decisions; sole author, not re-audited. Must: the armed check tests the array length (# M:PATH-SCOPE-CHECK-ARMED, row PS14) and the production GUARD also asserts one AUDITCYCLE line, no REQUIRE: STOP and no here file; the test (4) and no-root-path GUARDs pass no path_scope keyword. Should: the assembler-pin fixtures move to the new module test_grok_audit_surface_assembler_pin.py; SELF_DIR and the injected helper are monkeypatched with raising=False; row assembler-read-sha-unchecked targets a new sha256-repository fixture; the pre-clause test copies the three imported helpers and asserts dispatch_count first; each anchor states its matching unit, class UsageError is line 20. Design v1.14: the ${stem}.here.txt record (PS15, test_calibration_cycle_records_its_here), assembler-check --stems with here_unrecorded and here_mismatch, the two usage-error branches, the copy test reads the clause by ast parse, newline-only line split, and the doc is published only from a PINNED run (Task 15 steps 6 and 9a gain --stems and the smoke-failure require). Totals: 6 + 9 + 27 = 42 new rows, 420 after Task 14c, 422 or 424 after Task 16; new modules 20 and 32 node ids.
