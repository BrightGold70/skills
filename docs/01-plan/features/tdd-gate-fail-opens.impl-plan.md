# Implementation Plan: tdd-gate-fail-opens

> Source: docs/02-design/features/tdd-gate-fail-opens.design.md v1.2 (48d639f7), the contract.
> Spec v1.4 (644f8bf6), plan v1.4 (1254595a).
> Branch target: feature/tdd-gate-fail-opens, cut from `main` after this document is approved.

## Executive Summary

Fourteen tasks deliver the design's T0 to T12. T10 is split into T10a (the callee
`session_id_from_git_dir`) and T10b (the flag that calls it), so the resume WIRE-PIN goes red for a
caller reason. T0 lands the probe and the comparator. T1 lands the shared canonicaliser module.
T2 (Codex gate) and T3 (Claude gate) are the two `wiring` tasks that route each gate through it. T4
lands the header grammar and T5 the bounded reap. T10a, T10b, T11 and T12 land the FR-8 resume
oracle. T6 is the cross-gate differential, T7 the documentation surfaces, T8 the mutation census and
T9 the fixed reading. The feature writes 34 mutation rows: 26 carry an AC-7.1 guard (the plan's
floor is 25, and AC-3.3 gets one row per gate), 6 are connection rows and 2 are T11's
post-registration guard rows for the AC-8.2 option refusals. H6 and H11 are re-derived
at their existing guards and are not counted.

## Where this document departs from plan v1.4

Orchestrator decision 1: where plan v1.4 and design v1.2 differ, the design governs. Each difference
is stated once here. Where the plan text disagrees, do not follow it.

1. **Comparator verdict and exit status.** `compare_readings.py` prints `COMPARE: PASS softened=N approved=N`
   or `COMPARE: FAIL`, and exits 0 on both verdicts. A non-zero exit is only for a reading path that is
   missing, unreadable or invalid, and that path prints no `COMPARE:` token. Plan PD-4 says the
   comparator exits non-zero on its verdicts. That text is superseded.
2. **T0 self-comparison.** It prints `COMPARE: PASS softened=0 approved=0` and exits 0. Plan PD-4 and
   the plan's T0 row say `PASS softened=0`, without the `approved=` field. The injected unapproved
   key prints `COMPARE: FAIL` and exits 0. T9 prints `COMPARE: PASS softened=6 approved=6` and exits 0.
3. **Reap shape.** After `killpg`, `_run_bounded` runs `proc.communicate(timeout=REAP_GRACE_S)`. On
   `subprocess.TimeoutExpired` it closes `stdout` and `stderr` and reaps with
   `proc.wait(timeout=remaining)`, where `remaining = max(0.0, REAP_GRACE_S - elapsed)` and `elapsed`
   starts when the post-kill reap starts. The reap never uses `proc.poll`. Plan PD-2 copies the
   `h_mad_doc_block_exec.py` shape, whose second wait takes a fresh `DRAIN_SECONDS`. That shape is
   superseded.
4. **File paths.** Test and mutation-spec paths are the design's. The plan does not name
   `h-mad/tests/test_h_mad_tdd_gate_differential.py`,
   `h-mad/tests/mutation-specs/target_identity.json` or
   `h-mad/tests/mutation-specs/resume_decision_git_dir.json`. They are named here.

## Where this document departs from design v1.2 (orchestrator decision, impl-plan audit round 1)

1. **`_pct_capture` assigns by name, not through a nameref.** Design §"Claude record and the one
   call" says `_pct_capture` "assigns with `printf -v` through a nameref". A nameref is
   `local -n`, which needs bash 4.3. The hook's shebang is `#!/bin/bash`, and the hook is run
   directly, so the shebang interpreter runs it. On this host `/bin/bash --version` reads
   `GNU bash, version 3.2.57(1)-release`, where `local -n` prints `local: -n: invalid option`
   and the assignment lands nowhere. The design's intent is kept with the bash 3.2 form
   `printf -v "$1" ...`, which assigns to the variable named by the first argument (bash 3.1 and
   later). The contract is otherwise the design's: one command substitution, one `0x01`
   sentinel, exactly one trailing `0x01` stripped, never itself called via command substitution
   or backticks. The 3.2 form was run under `/bin/bash` 3.2.57 on the five value classes (ends in
   a newline, only newlines, ends in `0x01`, only `0x01`, empty), and each survived byte for byte.
   The probe was deleted after the run.
2. **Interpreter.** Design §"Test Strategy" names the suite interpreter by one host's absolute
   install path. This document does not write that path into any command, test or mutation spec. The interpreter is chosen by the rule in §"Execution rules" (**Interpreter**).

## Where this document refines the design (not contradictions; stated for the auditor)

- **T10 split.** The design's T10 is one row. As one task, its WIRE-PIN would go red because the
  flag is unrecognised, and that is a missing-callee reason. T10a lands `session_id_from_git_dir`,
  `GIT_DIR_BOUND_S` and `build_parser` as `new-behaviour`. T10b lands the flag and the call from
  `main` as `wiring`. At T10b's RED the callee exists, so the pin fails on the caller's stdout
  token.
- **Newline round-trip placement.** The design's T1 row puts "the newline round-trip" in
  `h-mad/tests/test_h_mad_target_identity.py`. Its capture half reads fields back through the bash
  `_pct_capture`, and `_pct_capture` is T3's. T1 lands the emit half,
  `test_emit_canon_encodes_trailing_newlines`. T3 lands the capture half in the same file,
  `test_canon_record_fields_survive_pct_capture`, and also lands
  `test_py_suffixes_match_bash_fold`, which reads `_fold_py`.
- **`reap_failed` in `resolve`.** The design says both production unpacks read `reap_failed` "before
  the `# M:K3` assignment". Only `judge` carries `# M:K3`. In `resolve` (the name-map run) the read
  goes immediately before `if timed_out:`, the line after `mapped = out.strip()  # M:R5`. The `# M:R5`
  line stays byte-identical.
- **AC-8.1 adapter half.** AC-8.1 takes its command from each adapter's oracle line, and that line
  changes at T12. At T11 the adapter line still carries `$(cat`. T11 therefore tests the literal
  `--session-id` UUID form and a flag form that the test builds itself. T12 adds the
  adapter-sourced case, `test_codex_hook_admits_adapter_oracle_lines`.
- **How `_read_canon` tells a directory record from a file record.** The `CANON 1` record has no
  file/directory field. For a file referent `target` is the referent's parent directory, and for a
  directory referent `target` is the directory itself, so the type of `target` cannot separate
  them. The reader decides from the spelled path the hook already holds: `_read_canon` joins
  `RAW_TARGET` to the spelled root when `RAW_TARGET` is relative, and tests the result with
  `[ -d ... ]`, which follows symlinks. Only a resolvable record with a non-empty `target` is
  checked. When the spelled path is a directory, `names` must be `0`. Otherwise `names` must be
  at least `1`. An absent leaf (`src/brandnew.py`, `src/newpkg/mod.py`) is not a directory, and its
  record carries the one spelled leaf, so it parses. An unresolvable record and the empty-target
  record are not checked by this rule. A referent that changes type between the one call and the
  test yields a protocol error, which is `judge-error` (fail-closed). The alternative, a new record
  field, would change the design's grammar and is not taken.
- **AC-2.5 placement.** Plan v1.4 lists AC-2.5 under T4. AC-2.5's patch
  `*** Update File: src/prod.PY` already parses under `PATCH_TARGET`, so T2's fold turns it from
  allow to deny. It is T2's RED. If it waited for T4 it would already pass at T4's RED.

## Fixed facts carried from design v1.2's Phase-5 findings (grok report, orchestrator decision 2)

Each of these is settled, and none is an open decision:

- The Test Plan's "Git-dir bound expired" row is the FR-8 bound arm's own test. It is not a seventh
  AC-8.4 acceptance case. AC-8.4 names six cases. T10a and T10b run the bound arm as its own
  parametrised case under both hosts and label it `bound-expired`, not AC-8.4.
- The reap is `proc.wait(timeout=remaining)` (T5). `proc.poll` also reaps and sets `returncode`, but
  it is not the written call. A `poll` implementation is a defect, even though it produces the same
  reap observation.
- Errno 13 on a contained payload cwd at mode `0311` (or `000`) leaves `is_dir()` true, so
  `_payload_cwd_base` returns that directory. It does not fall back to root. T2 pins this in
  `test_codex_payload_cwd_oserror_uses_payload_cwd_base[mode0311]`. Do not "fix" errno 13 by forcing
  root.
- The comparator's grammar carries `approved=N` on `PASS`. The design's §"Invariant Compliance"
  sentence ("prints `COMPARE: PASS` or `COMPARE: FAIL`") is shorthand. The grammar is
  `COMPARE: PASS softened=N approved=N`.
- The design's structural census is stamped at `1254595a`. This document re-ran the premises it uses
  at `48d639f7` (§"Verified premises").

## Residuals carried (orchestrator decision 3)

- **`h_mad_state_write.py` lines.** The five state-write lines in each adapter's fence keep the
  `$(cat "$(git rev-parse --absolute-git-dir)/h-mad-session-id.<feature>")` substitution. FR-8
  closes the oracle line only. This feature does not change them, and they are recorded as a
  residual on T12. No task is added for them.

- **Existing spec interpreters.** Nine existing spec files under `h-mad/tests/mutation-specs/`
  write an absolute anaconda interpreter path as `command[0]`, three of which gain rows here
  (§"Verified premises"). This feature does not rewrite their `command` fields. Only its two new
  specs are held to the **Interpreter** rule.

## Execution rules for every task

- **Transport.** Every 5d and 5e dispatch is `hmad-dispatch exec codex`. No committed test, probe or
  mutation `command` invokes the `codex`, `agy` or `grok` binary. Where a gate's `codex` lookup must
  succeed, the existing stub `_bin(tmp_path, codex=True)` in
  `h-mad/tests/test_h_mad_tdd_gate_judge.py` stands in.
- **Interpreter.** No command, test or mutation spec in this feature names an absolute interpreter
  path. Inside tests the interpreter is `sys.executable`. For run commands, `PY` is chosen by the
  rule of `h_mad_assemble_tdd.py`'s `interpreter_has_pytest`: an interpreter for which
  `"$PY" -c 'import pytest'` exits 0, probed before use and never assumed. Set it with
  `PY=$(command -v python3.11)` and run the probe. If the probe fails, choose another candidate
  from `find_interpreters_with_pytest`'s list. `python3` is not a safe default: on this host it has
  no pytest (§"Verified premises"). The two new mutation specs (`target_identity.json`,
  `resume_decision_git_dir.json`) write `"python3.11"` as `command[0]`, the spelling most existing
  specs use. New subprocess-spawning tests build `PATH` as a private `bin/` (`python3` pointing to
  `sys.executable`, plus `dirname`, `basename` and `jq`) followed by `/usr/bin:/bin`.
- **Bash 3.2 for the Claude gate.** `h-mad/hooks/h-mad-tdd-gate.sh` runs under `/bin/bash`, which is
  3.2.57 on this host. Every bash construct this document prescribes for that hook is bash 3.2
  compatible. These are forbidden in the hook: namerefs (`local -n`, `declare -n`, `typeset -n`),
  `mapfile` and `readarray`, associative arrays (`declare -A`, `local -A`), `declare -g`, and case
  modification (`${var,,}`, `${var^^}`, `${var,}`, `${var^}`). Indexed arrays, `printf -v NAME`,
  `$'...'` quoting and `${var%...}` are allowed. `test_claude_gate_is_bash_3_2_clean` (T3) pins this
  rule.
- **RED/GREEN counts are per test function.** A parametrised function counts once. Its parameter ids
  are listed. The counts are forecasts. 5d gates on each WIRE-PIN's failure reason and on its
  mutation, not on the counts alone.
- **Full suite per task.** At each task's GREEN, run
  `"$PY" -m pytest -q -p no:cacheprovider h-mad/tests`. The scoped files are not
  the gate. The collection floor is re-measured at the branch base with
  `"$PY" -m pytest --collect-only -q -p no:cacheprovider h-mad/tests | tail -1`,
  which read `4632 tests collected` at `48d639f7` on 2026-09-29.
- **Anchors per task.** At each task's GREEN,
  `python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/*.json`
  prints `ANCHORS: ANCHORS_OK` with `drifted=0`. Read the token, not `$?`.
- **Mutation rows.** A row is written at its owning task's GREEN against the landed source. The row's
  `find`/`replace` text is derived then, not here. A row whose catching test lands in a later task is
  parked in `docs/03-analysis/tdd-gate-fail-opens.pending-mutation-specs/` as one file per row, named
  for the row with the suffix `.json.pending` (for example `TI1.json.pending`). It is promoted when
  that test lands. Each spec is scored alone, for example
  `python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/target_identity.json`,
  reading the `MUTATION:` token (`ALL_CAUGHT`). Mutation `test` keys are relative to `h-mad/`, because every
  spec here has `"root": "../.."`.
- **Case-dependent tests** call `assert_case_insensitive(directory)` from
  `h-mad/tests/tdd_gate_support.py` (added in T1). It creates `a` and asserts `os.path.exists("A")`,
  and it raises `AssertionError` with a message naming the precondition. It never skips (AC-1.10).
  The same holds for every `PermissionError` precondition: assert, never skip. At each task's GREEN,
  `grep -n -E 'pytest\.skip|skipif|importorskip'` over the files the task adds or edits prints no
  line the task added.

---

## Task 0: probe-and-comparator

**Production file**: `docs/03-analysis/probes/tdd-gate-fail-opens/reproduce.py`, `docs/03-analysis/probes/tdd-gate-fail-opens/compare_readings.py`
**Test file**: none (measurement; the controls below are executed)
**Task shape**: `gate` (measurement and verdict; writes no production file under `h-mad/`)

**Description**: This task commits the probe and the comparator (plan PD-4), together with the
unfixed reading and the output of the three comparator controls.
`reproduce.py` drives both gates through `h-mad/tests/tdd_gate_support.py` and prints one `REPRO:`
line per key in the design's §"REPRO line grammar". Gate keys use
`REPRO: cell=... gate=claude|codex state=step5|step3 decision=allow|deny kind=...`, in that fixed
field order, with `kind=-` on an allow that prints no kind. The cells are M-1 through M-23,
`leaf-symlink`, `FR-8 cat-subst`, `FR-8 literal-uuid`, `FR-8 flag`, the OQ-P1 cells of AC-3.6 (a)
and (b) under `step5` and `step3`, and R-3's outside-root cells. The non-key lines are
`REPRO: family=primitive`, `REPRO: family=oq-p1`, `REPRO: family=d5` and
`REPRO: agent-cli-reachable=no`. Manual R-4 and R-5 rows are entered by hand as lines beginning
`MANUAL:`, and the script never prints them.
`compare_readings.py OLD NEW` keys gate lines on `(cell, gate, state)`. It fails on a key present in
one reading and absent from the other, and on any deny-to-allow key outside the approved six:
`M-10`/claude/step5, `M-10`/codex/step5, `M-11`/claude/step5, `leaf-symlink`/claude/step5,
`FR-8 literal-uuid`/codex/step5, `FR-8 flag`/codex/step5. On `COMPARE: FAIL` it prints each
offending key on stdout.
A reading is valid only when its `REPRO: agent-cli-reachable=` line carries the value `no` (design
§"REPRO line grammar"). `parse_reading` reads that line itself, not only the gate keys, and raises
`ValueError` when the value is anything else or the line is absent. `main` maps that to a non-zero
exit with the message on stderr and prints no `COMPARE:` token, in either argument position.

**Code structure**:
```python
# compare_readings.py
APPROVED: frozenset[tuple[str, str, str]]  # the six (cell, gate, state) keys above
def parse_reading(path: Path) -> dict[tuple[str, str, str], tuple[str, str]]: ...  # key -> (decision, kind); raises ValueError on an invalid reading
def compare(old: dict, new: dict) -> tuple[bool, int, int, list[str]]: ...  # ok, softened, approved, offending
def main(argv: list[str]) -> int: ...  # prints the COMPARE: token; 0 on PASS and on FAIL
```

**Acceptance Criteria**:
- [ ] The unfixed reading is committed as `docs/03-analysis/probes/tdd-gate-fail-opens/reading-unfixed.txt`
  and contains `REPRO: agent-cli-reachable=no`.
- [ ] Control 1 (self-comparison): `python3 docs/03-analysis/probes/tdd-gate-fail-opens/compare_readings.py reading-unfixed.txt reading-unfixed.txt`
  prints `COMPARE: PASS softened=0 approved=0` and exits 0. The output is committed beside the reading.
- [ ] Control 2 (injected unapproved key): the same comparison, against a copy with one unapproved
  deny-to-allow key, prints `COMPARE: FAIL` and the key, and exits 0. The copy is deleted after the
  run, and the output is committed.
- [ ] A missing reading path exits non-zero and prints no `COMPARE:` token (executed once, then
  recorded).
- [ ] Control 3 (invalid reading): `reading-invalid.txt`, a copy of `reading-unfixed.txt` whose
  `REPRO: agent-cli-reachable=no` line is changed to `REPRO: agent-cli-reachable=yes`, with every
  gate line unchanged. `compare_readings.py reading-unfixed.txt reading-invalid.txt` and
  `compare_readings.py reading-invalid.txt reading-unfixed.txt` each exit non-zero, and each output contains no
  `COMPARE:` token. Both outputs are committed, and `reading-invalid.txt` is deleted after the run.
  RED expectation: the gate lines of the copy equal the original's, so a comparator that keys only
  on gate lines and skips the non-key line prints `COMPARE: PASS softened=0 approved=0` and exits 0
  on both runs. Run control 3 once before `parse_reading`'s validity check is written, and record
  that `COMPARE: PASS` output as the RED. GREEN is the non-zero exit with no `COMPARE:` token.
- [ ] `grep -n -E '\bcodex\b|\bagy\b|\bgrok\b' docs/03-analysis/probes/tdd-gate-fail-opens/*.py`
  prints no line that invokes a binary. Cell tokens such as `gate=codex` are data, not
  invocations.

**Mutation rows**: 0.
**Dependencies on other tasks**: None.

---

## Task 1: target-identity-module

**Production file**: `h-mad/scripts/h_mad_target_identity.py` (new), `h-mad/tests/tdd_gate_support.py` (adds `assert_case_insensitive`)
**Test file**: `h-mad/tests/test_h_mad_target_identity.py` (new)
**Task shape**: `new-behaviour`

**Description**: This task adds the stdlib-only (`os`, `fcntl`, `stat`) canonicaliser that both
gates share. It implements §"Canonicaliser" and §"Which component is opened, listed, or neither"
exactly.

- `canonical_directory` opens the path `O_RDONLY` and reads `fcntl.F_GETPATH` into `bytes(1024)`. It
  strips trailing NULs, decodes with `os.fsdecode` and closes the fd on every path. When `F_GETPATH`
  is absent, it falls back to `os.path.realpath`.
- `canonicalise` does the `lstat`/`stat` walk. Arm 1 is `lstat` succeeding and `stat` raising. Arm 2
  is an `OSError` from `canonical_directory` on the root, from `canonical_directory` on the target's
  deepest existing directory, or from `scandir` of the final referent's parent. That `OSError` is
  caught and returned as an arm-2 `Identity`, never propagated. A leaf symlink is followed with one
  `os.open` without `O_NOFOLLOW` to the final referent. The scan admits an entry only when
  `DirEntry.is_symlink()` is false and `DirEntry.stat(follow_symlinks=False)` has the referent's
  `(st_dev, st_ino)`. The resulting names are sorted.
- `fold_py_suffix` folds the four `PY_SUFFIXES` without calling `str.casefold`.
- `emit_canon` prints the `CANON 1` record. It encodes each field with `os.fsencode` and then `%HH`
  for every byte outside ASCII alphanumerics and `/-._`.

**Code structure**:
```python
PY_SUFFIXES = (".py", ".pY", ".Py", ".PY")

class Identity(NamedTuple):
    root: str
    target: str
    prefix: str
    names: tuple[str, ...]
    unresolvable: bool
    arm: int          # 0, 1 or 2
    component: str    # spelled component that failed, or ""

def canonical_directory(path: str) -> str: ...
def canonicalise(root: str, target: str, cwd: str | None = None) -> Identity: ...
def fold_py_suffix(name: str) -> str: ...
def emit_canon(identity: Identity) -> None: ...
```

**Arm-1 branch separability (adopted: two handlers).** AC-7.1 asks for separate mutations on
the dangling branch (AC-3.1) and the loop branch (AC-3.2). The design's arm-1 predicate is one
`stat` raising, so one `except OSError` would make the two mutants the same edit. A mutant that
narrows the clause to one errno would propagate the other as an uncaught exception. On the Claude
side that is a crash, and a crash is `judge-error`, the same observable as the fixed tree, so the
mutant survives. The implementation that satisfies both: the `stat` call has two handlers, each on
its own marked line. The first is `except FileNotFoundError:` (dangling, `# M:TI4`). The second is
`except OSError:` (loop and every other errno, `# M:TI5`). Each handler returns the arm-1 `Identity`.
Each mutant makes its handler take the absent-component path instead (split the remainder), so M-12
or M-14 becomes a resolvable spelling and the gate's verdict moves.

**Acceptance Criteria** (all tests in `h-mad/tests/test_h_mad_target_identity.py`; the module is
imported inside a fixture named `identity`, so each test fails on its own at RED and the file does
not raise a collection error):
- [ ] AC-1.7: `test_canonical_directory_returns_on_disk_spelling[m8-root]` and `[m9-dir]` assert the
  on-disk spelling (`Case`, `Tests`) for a path spelled in the other case. They call
  `assert_case_insensitive` first. The realpath negative control is mutation row TI1, which is run
  and not asserted.
- [ ] AC-1.9 (unit half): `test_hard_link_names_share_the_canonical_parent`. `src/prod.py` and
  `src/test_prod.py` are on one inode, spelled `src/test_prod.py`. The test asserts the precondition
  `os.stat(a).st_ino == os.stat(b).st_ino`, then `names == ("prod.py", "test_prod.py")`.
- [ ] FR-1 step 4: `test_leaf_symlink_scans_the_referent_parent`. `src/link.py -> ../tests/t.py`, with
  hard link `tests/t_hard.py` and symlink `tests/alias.py -> t.py`. The expected result is
  `names == ("t.py", "t_hard.py")` and `target` in the referent's parent.
- [ ] `test_symlink_chain_resolves_in_one_open`: `src/chain.py -> mid.py -> ../tests/t.py` resolves to
  the referent's parent and inode.
- [ ] `test_directory_referent_has_no_names`: `src/todir -> ../tests` gives `names == ()`,
  `unresolvable is False`, and `target` the `tests` directory.
- [ ] AC-1.8 (unit half): `test_absent_leaf_names_the_spelled_leaf[absent-leaf]` (`src/brandnew.py`)
  and `[absent-parent]` (`src/newpkg/mod.py`). For each, `target` equals the spelled absolute path,
  `names` is the spelled leaf, and `unresolvable is False`.
- [ ] AC-3.1 and AC-3.2 (unit half): `test_dangling_leaf_is_arm_1[leaf]` (`src/dang.py -> nowhere/x.py`)
  and `[intermediate]` (`lnk/x.py`, `lnk -> nowhere`). Each gives `unresolvable`, `arm == 1`, and the
  spelled component.
- [ ] AC-3.4 (unit half): `test_loop_is_arm_1` (`src/loopa.py -> loopb.py -> loopa.py`) gives `arm == 1`.
- [ ] AC-3.4 control: `test_loop_path_realpath_returns_without_error` returns normally from
  `os.path.realpath` of the same loop path. It is its own test.
- [ ] AC-3.6 (unit half): `test_unreadable_directory_is_arm_2[a-absent-leaf]` covers on-disk `Tests/`
  at `0311` spelled `tests/newmod.py`. `[b-existing-leaf]` covers `src/` at `0311` holding
  `src/prod.py`. Each asserts that `os.listdir` raises `PermissionError`, then `arm == 2` and the
  spelled component. The mode is restored in teardown.
- [ ] Root arm 2: `test_root_open_failure_is_arm_2`. The root is at mode `0311`. The expected result
  is `arm == 2`, with `root`, `prefix` and `component` all the spelled root and `target == ""`.
- [ ] FR-2: `test_fold_py_suffix_folds_four_spellings` folds all four suffixes and leaves the stem
  byte-identical. `fold_py_suffix("prod.py ") == "prod.py "` and `fold_py_suffix("d.md") == "d.md"`.
- [ ] Encoding: `test_non_utf8_name_round_trips_through_percent_encoding` creates no directory entry.
  It asserts `%FF` in the encoded field, the `os.fsencode` round trip, `UnicodeDecodeError` from a
  strict decode, and `UnicodeEncodeError` from a strict encode.
- [ ] Record grammar: `test_emit_canon_record_grammar[file]`, `[directory]`, `[unresolvable]`,
  `[empty-target]`, `[root-failure]`. Each record has the field order of §"Claude record and the one
  call" and the per-kind field rules (the directory record has `names 0` and a non-empty `target`).
- [ ] `test_emit_canon_encodes_trailing_newlines`: for an `Identity` whose `root`, `target`, `prefix`,
  `component` and each name end in a newline, each emitted field is one physical line carrying
  `%0A`.
- [ ] AC-3.4 (Claude resolver half, one shared resolver): `test_emit_canon_loop_record_is_unresolvable`.
  `emit_canon(canonicalise(root, "src/loopa.py"))` prints `unresolvable yes` and `arm 1`.
- [ ] AC-1.10: `test_case_insensitive_precondition_is_asserted` calls `assert_case_insensitive(tmp_path)`.

**RED/GREEN**: 17 test functions, 16 RED and 1 regression guard. The guard is
`test_loop_path_realpath_returns_without_error`, which uses no module symbol and passes at RED.
**Regression guards**: the full suite. No existing test changes.
**Mutation rows**: 0 committed. TI1–TI6 are drafted at this task's GREEN and parked as
`.json.pending`, because their catching tests are T3's Claude-gate tests. T3 promotes them.
**Dependencies on other tasks**: Task 0.

---

## Task 2: codex-gate-identity

**Production file**: `h-mad/hooks/h-mad-codex-tdd-gate.py`
**Test file**: `h-mad/tests/test_h_mad_codex_tdd_gate_judge.py`
**Task shape**: `wiring` (the new-behaviour RED rows below land in the same task, and the split is
stated in prose)
**WIRE 1**: `h-mad/hooks/h-mad-codex-tdd-gate.py:_load_identity` → `h_mad_target_identity.canonical_directory` / `canonicalise` (placements: the four `_project_root` returns, a usable contained payload cwd, `_relative_target`)
**WIRE-PIN 1**: `tests/test_h_mad_codex_tdd_gate_judge.py::test_codex_case_directory_m9_denies`
**WIRE 2**: `h-mad/hooks/h-mad-codex-tdd-gate.py:_is_production_python` → `h_mad_target_identity.fold_py_suffix`
**WIRE-PIN 2**: `tests/test_h_mad_codex_tdd_gate_judge.py::test_codex_fold_new_leaf_denies`

**Description**: This task implements §"Codex call sites".

- `_load_identity` mirrors `_load_judge`.
- `_project_root` keeps its selection. Each of its four returns passes through `canonical_directory`
  instead of `Path.resolve()` / `Path.cwd().resolve()`. An `OSError` on the selected root becomes the
  arm-2 `Identity` and never reaches `# M:G2`. Its `component` is `str` of the path `_project_root`
  handed to `canonical_directory` (after `expanduser()`, before any resolve).
- `_main_guarded` branches on that `Identity` immediately after `root = _project_root(payload)` and
  before the existing `phase5_status = _any_phase5_status(root)` line, so that line and everything
  after it only ever see a `Path`. The branch is `if not isinstance(root, Path):`, which given the
  `Path | Identity` return is exactly the arm-2 case and needs no second `_load_identity()` call to
  name the class. Inside it the status scan runs on
  `Path(root.component)`, the spelled root, inside `try`/`except OSError`, where `OSError` gives
  `"unknown"`. `active` and `unknown` return the `judge-error` deny naming `root.component`, and
  `inactive` returns 0. The branch returns in every case, so neither `_targets` nor
  `_safe_shell_command` nor `_relative_target` runs on an arm-2 root.
- The payload cwd goes through `canonical_directory` only when it is a usable contained directory.
  On an `OSError` the original cwd string goes to `_payload_cwd_base`, whose body stays
  byte-identical.
- `_relative_target` returns `Identity | None`. It returns `None` only when the result is resolvable
  and outside the root.
- `_is_production_python` calls `fold_py_suffix` before its suffix and basename tests.
- The unmarked `if` under `for raw in targets:  # M:G5` decides "production" when any name is
  production. An unresolvable `Identity` refuses `judge-error` naming the component when
  `phase5_status` is in `{"active", "unknown"}`, and it is skipped otherwise.
- `absolute` is the canonical parent joined with the lexicographically first production name.
- These lines stay byte-identical: `# M:G1`, `# M:G5`, `# M:G7`, `# M:G10`, `# M:W1`, `# M:W5A`.

**Code structure**:
```python
def _load_identity() -> Any: ...
def _project_root(payload: dict[str, Any]) -> Path | Identity: ...   # Identity only on an arm-2 root
def _relative_target(root: Path, raw: str, cwd: Any = None) -> Identity | None: ...
def _is_production_python(relative: str) -> bool: ...                 # folds first
def _main_guarded() -> int: ...   # "if not isinstance(root, Path):" branch before _any_phase5_status(root)
```

**WIRE-PIN RED reason (caller-observable)**: T1 has landed, so at this task's RED the callee exists
and imports. `test_codex_case_directory_m9_denies` fails because the unfixed gate allows M-9: the
spelled `tests/` component is exempt. The assertion is on the gate's decision, not on an import.
`test_codex_fold_new_leaf_denies[pY]` fails because the unfixed `_is_production_python` returns
false for `.pY`, so the gate allows.

**Acceptance Criteria** (Codex halves; every test in `h-mad/tests/test_h_mad_codex_tdd_gate_judge.py`):
- [ ] AC-1.4: `test_codex_case_root_m8_denies[forward]` and `[reverse]`. Deny `no-test-resolved`
  where the unfixed gate says "outside".
- [ ] AC-1.5: `test_codex_case_directory_m9_denies`. Deny `no-test-resolved`.
- [ ] AC-1.6: `test_codex_toward_allow_m10` allows. `test_codex_m11_stays_allow` allows, fixed and
  unfixed.
- [ ] AC-1.8: `test_codex_new_file_denies_without_judge_error[absent-leaf]` and `[absent-parent]`.
- [ ] AC-1.9: `test_codex_hard_link_alias_denies`, with the inode precondition asserted.
- [ ] AC-2.1: `test_codex_fold_existing_leaf_denies` (M-2).
- [ ] AC-2.2: `test_codex_fold_new_leaf_denies[m3]`, `[pY]`, `[Py]`. Each is its own case.
- [ ] AC-2.3: `test_codex_test_shaped_names_stay_exempt`. `sub/test_x.PY`, `sub/x_test.PY` and
  `sub/conftest.PY` allow. `sub/TEST_x.py` denies.
- [ ] AC-2.4: `test_codex_trailing_space_is_not_folded`. `src/prod.py ` allows.
- [ ] AC-2.5: `test_codex_d1_repro_patch_denies`. The patch is `*** Update File: src/prod.PY`.
- [ ] AC-3.1, AC-3.2, AC-3.5: `test_codex_unresolvable_governed_is_judge_error[m12]`, `[m13-leaf]`,
  `[m13-intermediate]`, `[m14]`. Each reason carries `kind=judge-error` and the component.
- [ ] AC-3.3: `test_codex_unresolvable_step3_allows[m13-leaf]`, `[m13-intermediate]`, `[m14]` (M-18).
- [ ] AC-3.4 (Codex resolver): `test_codex_resolver_reports_loop_unresolvable` calls
  `_relative_target` directly on the loop and gets an unresolvable `Identity`.
- [ ] AC-3.6 (a), (b): `test_codex_unreadable_component_step5[a]` and `[b]` deny `judge-error`
  naming the component. `os.listdir` must raise `PermissionError`, and the test fails, never skips,
  when it does not.
- [ ] AC-3.6 (c): `test_codex_unreadable_component_step3_allows[a]` and `[b]` allow, with the same
  precondition.
- [ ] Root arm 2: `test_codex_root_open_failure_refuses_only_when_governed[active]`, `[unknown]`,
  `[inactive]`. `CODEX_PROJECT_DIR` is at mode `0311`. `active` and `unknown` refuse `judge-error`
  naming the spelled root, and `inactive` allows.
- [ ] Payload cwd: `test_codex_payload_cwd_oserror_uses_payload_cwd_base[missing]`, `[loop]`,
  `[mode000]`, `[mode0311]`. A relative target joins root for `missing` and `loop`, and joins the
  cwd for `mode000` and `mode0311`. No case is unresolvable.
- [ ] Connection, forced arm 1: `test_codex_safe_shell_script_keeps_path_resolve_spelling`. The
  observable is `_safe_shell_command`'s boolean, which is the only thing it exposes. The test
  imports the real hook with `importlib.util.spec_from_file_location` and calls
  `_safe_shell_command(command, root, str(root))` twice with a safe-listed script,
  `h_mad_wire_registry.py challenge`, run by `python3`. The first call spells the script under the
  hook's own `scripts` directory in its on-disk case and must return `True` (the positive control).
  The second call spells the same file under `SCRIPTS`. It first asserts `os.path.exists` of the
  `SCRIPTS` spelling, with a message naming the case-insensitive precondition, and fails, never
  skips, when it does not hold. It does not call `assert_case_insensitive` here, because that
  helper creates a file in the directory it is given and the directory is the skill's own. That
  call must return `False`. `Path.resolve` keeps the spelled `SCRIPTS`, so
  `script.relative_to(scripts_root)` raises `ValueError`. With `canonical_directory` forced onto
  `script.resolve()` (CX-FORCE-SCRIPT), the path takes the on-disk `scripts` spelling, the
  containment test passes, and the call returns `True`. CX-FORCE-SCRIPT is scored alone and must
  be caught by this test alone. Reading on the unfixed tree at `48d639f7`: `scripts` gives `True`
  and `SCRIPTS` gives `False` (§"Verified premises").
- [ ] Connection, forced arm 2: `test_codex_empty_cwd_joins_root`. A governed relative `src/prod.py`
  with `cwd == ""` denies `no-test-resolved`, not `judge-error`.
- [ ] Connection, forced fold: `test_codex_forced_fold_does_not_exempt_dangling_test_name`. A governed
  dangling `sub/test_x.PY` denies `judge-error`.

**RED/GREEN**: 21 test functions, 12 RED and 9 regression guards.
- RED: `test_codex_case_root_m8_denies`, `test_codex_case_directory_m9_denies`,
  `test_codex_toward_allow_m10`, `test_codex_hard_link_alias_denies`,
  `test_codex_fold_existing_leaf_denies`, `test_codex_fold_new_leaf_denies`,
  `test_codex_d1_repro_patch_denies`, `test_codex_unresolvable_governed_is_judge_error`,
  `test_codex_resolver_reports_loop_unresolvable`, `test_codex_unreadable_component_step5`,
  `test_codex_root_open_failure_refuses_only_when_governed`,
  `test_codex_forced_fold_does_not_exempt_dangling_test_name`.
- Regression guards (pass at RED): `test_codex_m11_stays_allow`,
  `test_codex_new_file_denies_without_judge_error`, `test_codex_test_shaped_names_stay_exempt`,
  `test_codex_trailing_space_is_not_folded`, `test_codex_unresolvable_step3_allows`,
  `test_codex_unreadable_component_step3_allows`,
  `test_codex_payload_cwd_oserror_uses_payload_cwd_base`,
  `test_codex_safe_shell_script_keeps_path_resolve_spelling`, `test_codex_empty_cwd_joins_root`.
  The existing `test_codex_gate_kind` (every row) also stays green. Its `judge-error` fixture keeps
  `h_mad_target_identity.py` absent (§"Copied-hook fixtures"), so `_load_identity` fails first and
  `# M:G2` still maps the failure to `kind=judge-error`.

**Mutation rows** (7, in `h-mad/tests/mutation-specs/codex_gate_judge_wiring.json`, `file` = `hooks/h-mad-codex-tdd-gate.py`):

| Row | Guard | Mutant | `test` |
|---|---|---|---|
| CX-CANON | AC-1.4 root canonicalisation | the `_project_root` returns use `Path.resolve()` again | `tests/test_h_mad_codex_tdd_gate_judge.py::test_codex_case_root_m8_denies` |
| CX-FOLD | AC-2.2 fold (Codex) | `fold_py_suffix` call removed from `_is_production_python`, callee intact | `tests/test_h_mad_codex_tdd_gate_judge.py::test_codex_fold_new_leaf_denies` |
| CX-GOV | AC-3.3 governing-state (Codex) | the unresolvable branch refuses without consulting `phase5_status` | `tests/test_h_mad_codex_tdd_gate_judge.py::test_codex_unresolvable_step3_allows` |
| CX-RESOLVE-M9 | connection removal (WIRE 1) | `_relative_target` resolves with `Path.resolve()`, import intact | `tests/test_h_mad_codex_tdd_gate_judge.py::test_codex_case_directory_m9_denies` |
| CX-FORCE-SCRIPT | connection forced (WIRE 1) | `canonical_directory` forced onto `script.resolve()` inside `_safe_shell_command` only | `tests/test_h_mad_codex_tdd_gate_judge.py::test_codex_safe_shell_script_keeps_path_resolve_spelling` |
| CX-FORCE-CWD | connection forced (WIRE 1) | `canonical_directory` forced on an empty payload cwd | `tests/test_h_mad_codex_tdd_gate_judge.py::test_codex_empty_cwd_joins_root` |
| CX-FOLD-FORCE | connection forced (WIRE 2) | `_is_production_python` (folding) consulted before the unresolvable branch | `tests/test_h_mad_codex_tdd_gate_judge.py::test_codex_forced_fold_does_not_exempt_dangling_test_name` |

**Dependencies on other tasks**: Task 1.

---

## Task 3: claude-gate-identity

**Production file**: `h-mad/hooks/h-mad-tdd-gate.sh`
**Test file**: `h-mad/tests/test_h_mad_tdd_gate_judge.py`, `h-mad/tests/test_h_mad_target_identity.py`
**Task shape**: `wiring` (the new-behaviour RED rows below land in the same task, and the split is
stated in prose)
**WIRE**: `h-mad/hooks/h-mad-tdd-gate.sh:# M:H11 python3 -c call` → `h_mad_target_identity.canonicalise` + `emit_canon`
**WIRE-PIN**: `tests/test_h_mad_tdd_gate_judge.py::test_claude_case_directory_m9_denies`

**Description**: This task implements §"Claude record and the one call" and §"Claude per-name
loops".

- One `python3 -c` call carries `# M:H11` and replaces both the
  `ROOT_ABS=$(cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null && pwd -P) || ROOT_ABS=""` assignment and the
  `os.path.normpath` call. It runs unconditionally, with `RAW_TARGET=$TARGET_PATH` kept immediately
  before it. The call resolves its own script path as `# M:W6` does and prints one `CANON 1` record.
  It is not wrapped in `||`.
- `_pct_capture` is the only capture: one command substitution with a `0x01` sentinel, `printf -v`
  to the variable named by its first argument (bash 3.2 form, §"Where this document departs from
  design v1.2"), and exactly one trailing `0x01` stripped. `_read_canon` is the only reader. Any
  parse error is `_refuse judge-error`.
- `_read_canon` separates a directory record from a file record by `[ -d ... ]` on the spelled
  path (§"Where this document refines the design"). A spelled directory with `names` above `0`, and
  a spelled non-directory with `names` `0` and a non-empty `target`, are protocol errors.
- Every bash construct in this task follows the **Bash 3.2** rule in §"Execution rules".
- `_fold_py` holds the four literals.
- Bash order after a parsed record:
  1. A parse failure is `judge-error`.
  2. An empty target keeps `# M:H13`.
  3. On `unresolvable=yes`, `_chain_may_hold_state` and `_read_state` run on `prefix`. For a root
     failure, `prefix` is the spelled root and is passed as both arguments. Governed refuses
     `judge-error` with reason `unresolvable arm=N component=...`. Otherwise `_allow`.
  4. On a resolvable record, the three per-name loops run: the `# M:H6` basename case, the
     unmarked suffix-allow case, and the non-`.py` test.
- `TARGET_PATH` becomes the canonical parent joined with the lexicographically first production
  name.
- These lines stay byte-identical: `# M:H8`, `# M:H15`, `# M:H18`, `# M:H19`, `# M:H20`, `# M:W2`,
  `# M:H3`, `# M:H16`.
- `JUDGE_DENY_RE` is not touched here. T5 changes it.
- `_tree_b` in `h-mad/tests/test_h_mad_tdd_gate_judge.py` also writes
  `scripts/h_mad_target_identity.py`, a stub that emits a resolvable `CANON 1` record (one name,
  `unresolvable no`) for the spelled path.

**Code structure** (bash):
```bash
_pct_capture() { local _pct_v; _pct_v=$(_pct_decode "$2"; printf '\001'); printf -v "$1" '%s' "${_pct_v%$'\001'}"; }
_read_canon() { ... }   # reads the record from the one call; sets CANON_ROOT CANON_TARGET CANON_PREFIX CANON_UNRESOLVABLE CANON_ARM CANON_COMPONENT CANON_NAMES[]
_fold_py() { ... }      # .py .pY .Py .PY -> .py on a trailing suffix only
```
The `_pct_capture` line above shows the contract, not final text. It must not itself be called via
command substitution or backticks. Its first argument is the destination variable's name, and no
caller passes `_pct_v`, which would assign to the function's own local.

**WIRE-PIN RED reason (caller-observable)**: at RED the module exists (T1), and the hook does not yet
call it. `test_claude_case_directory_m9_denies` fails because the unfixed hook allows M-9: the
spelled `tests` basename directory is exempt. The assertion is on rc and stdout, not on an import.
Scaffold: none needed. The real module is in the hook's own tree.

**Acceptance Criteria** (Claude halves; gate tests in `h-mad/tests/test_h_mad_tdd_gate_judge.py`):
- [ ] AC-1.1: `test_claude_symlinked_test_dir_denies[m4]` and `[m5]` deny `no-test-resolved`.
- [ ] AC-1.2: `test_claude_dotdot_after_symlink_denies` (M-6).
- [ ] AC-1.3: `test_claude_symlinked_root_denies` (M-7). The control, root and target spelled
  `R/real`, denies with the same kind. The test asserts the precondition that the symlinked root
  contains a `tests` component.
- [ ] AC-1.4: `test_claude_case_root_m8_denies[forward]` and `[reverse]`.
- [ ] AC-1.5: `test_claude_case_directory_m9_denies`.
- [ ] AC-1.6: `test_claude_toward_allow_m10_m11[m10]` and `[m11]` allow.
- [ ] AC-1.8: `test_claude_new_file_denies_without_judge_error[absent-leaf]` and `[absent-parent]`.
- [ ] AC-1.9: `test_claude_hard_link_alias_denies`.
- [ ] AC-1.11: `test_claude_outside_root_symlink_keeps_raw_conjunct[lnk]` denies
  `no-test-resolved`, `[tests]` allows and `[src]` denies. This is a regression pin. The existing
  `H20B` is its discriminator and is scored after this task.
- [ ] AC-2.1: `test_claude_fold_existing_leaf_denies`. AC-2.2: `test_claude_fold_new_leaf_denies[m3]`,
  `[pY]`, `[Py]`. AC-2.3: `test_claude_test_shaped_names_stay_exempt`. AC-2.4:
  `test_claude_trailing_space_is_not_folded`.
- [ ] AC-3.1, AC-3.2, AC-3.5: `test_claude_unresolvable_governed_is_judge_error[m12]`, `[m13-leaf]`,
  `[m13-intermediate]`, `[m14]`. Each prints `BLOCK kind=judge-error` with `arm=` and the component.
- [ ] AC-3.3: `test_claude_unresolvable_step3_allows` (M-18).
- [ ] AC-3.6: `test_claude_unreadable_component_step5[a]` and `[b]`, and
  `test_claude_unreadable_component_step3_allows[a]` and `[b]`. Each asserts the `PermissionError`
  precondition and fails, never skips, when it does not hold.
- [ ] Root arm 2: `test_claude_root_open_failure_refuses_only_when_governed[active]` and
  `[inactive]`. `CLAUDE_PROJECT_DIR` is at mode `0311`. Governed refuses `judge-error` naming the
  root, and ungoverned allows.
- [ ] Protocol: `test_claude_canon_protocol_error_is_judge_error[unknown-key]`, `[missing-key]`,
  `[second-header]`, `[version-2]`, `[arm-3]`, `[unresolvable-maybe]`, `[names-negative]`,
  `[count-mismatch]`, `[bad-pct]`, `[directory-with-names]`, `[file-with-zero-names]`. Each case uses
  a stub module (the `_tree_b` layout) that emits the malformed record. Each refuses `judge-error`.
  For `[directory-with-names]` the spelled target is an existing directory and the stub emits
  `names 1`. For `[file-with-zero-names]` the spelled target is an existing regular file and the
  stub emits `names 0` with a non-empty `target`. The test asserts each spelled target's type
  (`is_dir()` true, then `is_file()` true) before it runs the hook.
- [ ] Bash 3.2: `test_claude_gate_is_bash_3_2_clean` has two halves. The static half reads the hook
  text and checks each forbidden construct of the **Bash 3.2** rule with its own pattern, reporting
  zero matches for each: nameref `\b(local|declare|typeset)\s+-[a-zA-Z]*n`, associative
  `\b(local|declare|typeset)\s+-[a-zA-Z]*A`, global `\b(declare|typeset)\s+-[a-zA-Z]*g`,
  `\b(mapfile|readarray)\b`, and case modification `\$\{[A-Za-z_][A-Za-z0-9_]*(\[[^]]*\])?(,|\^)`.
  Each pattern is first asserted to match its own positive fixture string (`local -n _out=$1`,
  `declare -A m`, `declare -g X=1`, `mapfile -t a < f`, `${name,,}`) and none of the other four. The
  dynamic half runs the hook explicitly as `["/bin/bash", str(HOOK)]`, not through its shebang, on
  the `test_claude_new_file_denies_without_judge_error[absent-leaf]` fixture. It asserts a deny
  whose kind is not `judge-error`, as AC-1.8 does, and that stderr contains none of `invalid option`, `bad substitution` and
  `command not found`. Under a nameref `_pct_capture`, `/bin/bash` 3.2 prints
  `local: -n: invalid option`, and every field arrives empty, so the record fails to parse and the
  decision becomes `judge-error`.
- [ ] One canonicaliser: `test_claude_single_pwd_p_is_the_h8_walk`. The hook has exactly one line
  matching `pwd -P`, and it carries `# M:H8`.
- [ ] Capture (in `h-mad/tests/test_h_mad_target_identity.py`):
  `test_canon_record_fields_survive_pct_capture` builds a `CANON 1` record in which `root`,
  `target`, `prefix`, `component` and `name` each end in a newline. It also includes a field that is
  only newlines, a field ending in `0x01`, a field that is only `0x01`, and an empty field. It reads
  each field through the hook's `_pct_decode` and `_pct_capture` (extracted from the hook text by
  function name and run by `/bin/bash` explicitly) and compares bytes. It does the same for a record `emit_canon` produced.
- [ ] Fold equivalence (in `h-mad/tests/test_h_mad_target_identity.py`):
  `test_py_suffixes_match_bash_fold` asserts that the literals in `_fold_py`'s body equal
  `PY_SUFFIXES`. It also asserts that the basename case, the suffix-allow case and the non-`.py`
  test each read a `_fold_py`-folded name.

**RED/GREEN**: 23 test functions, 16 RED and 7 regression guards.
- RED: `test_claude_symlinked_test_dir_denies`, `test_claude_dotdot_after_symlink_denies`,
  `test_claude_symlinked_root_denies`, `test_claude_case_root_m8_denies`,
  `test_claude_case_directory_m9_denies`, `test_claude_toward_allow_m10_m11`,
  `test_claude_hard_link_alias_denies`, `test_claude_fold_existing_leaf_denies`,
  `test_claude_fold_new_leaf_denies`, `test_claude_unresolvable_governed_is_judge_error`,
  `test_claude_unreadable_component_step5`,
  `test_claude_root_open_failure_refuses_only_when_governed`,
  `test_claude_canon_protocol_error_is_judge_error`, `test_claude_single_pwd_p_is_the_h8_walk`,
  `test_canon_record_fields_survive_pct_capture`, `test_py_suffixes_match_bash_fold`.
- New regression guards (pass at RED): `test_claude_new_file_denies_without_judge_error`,
  `test_claude_outside_root_symlink_keeps_raw_conjunct`, `test_claude_test_shaped_names_stay_exempt`,
  `test_claude_trailing_space_is_not_folded`, `test_claude_unresolvable_step3_allows`,
  `test_claude_unreadable_component_step3_allows`, `test_claude_gate_is_bash_3_2_clean` (the
  unfixed hook holds none of the five constructs, and it denies the absent leaf
  with a kind other than `judge-error` under `/bin/bash`).
- Existing guards that must stay green: `test_symlinked_hook_runs_its_own_trees_judge` (it needs the
  `_tree_b` identity stub), `test_trap_member_refuses_in_form` (its `*os.path.realpath*` shim still
  matches the `# M:W6` locator), `test_outside_root_exemption_needs_both_spellings`,
  `test_dd7_differential_matches_the_published_cells` (assertion text
  `assert len(observed) == 126 and observed.count("deny") == 18` unchanged), and
  `test_claude_gate_kind`.

**Mutation rows** (9: 3 in `h-mad/tests/mutation-specs/claude_gate_judge_wiring.json` and 6 in the
new `h-mad/tests/mutation-specs/target_identity.json`, promoted from T1's pending drafts):

| Row | Spec, `file` | Guard | Mutant | `test` |
|---|---|---|---|---|
| CG-CANON | claude, `hooks/h-mad-tdd-gate.sh` | AC-1.1 Claude canonicaliser (= WIRE removal) | the one call emits a record from `os.path.normpath(os.path.join(root, target))` without calling `canonicalise`; module file left in place | `tests/test_h_mad_tdd_gate_judge.py::test_claude_case_directory_m9_denies` |
| CG-FOLD | claude, `hooks/h-mad-tdd-gate.sh` | AC-2.2 fold (Claude) | `_fold_py` returns its input unchanged | `tests/test_h_mad_tdd_gate_judge.py::test_claude_fold_new_leaf_denies` |
| CG-GOV | claude, `hooks/h-mad-tdd-gate.sh` | AC-3.3 governing-state (Claude) | the unresolvable branch refuses without reading state | `tests/test_h_mad_tdd_gate_judge.py::test_claude_unresolvable_step3_allows` |
| TI1 | target_identity, `scripts/h_mad_target_identity.py` | AC-1.5 on-disk spelling (also AC-1.7's realpath negative control, run) | `canonical_directory` returns `os.path.realpath(path)` | `tests/test_h_mad_tdd_gate_judge.py::test_claude_case_directory_m9_denies` |
| TI2 | target_identity | AC-1.9 hard-link rule | `names` holds only the spelled leaf | `tests/test_h_mad_tdd_gate_judge.py::test_claude_hard_link_alias_denies` |
| TI3 | target_identity | AC-1.3 root canonicalisation | the root is kept as spelled (no `canonical_directory`) | `tests/test_h_mad_tdd_gate_judge.py::test_claude_symlinked_root_denies` |
| TI4 | target_identity | AC-3.1 dangling branch (`# M:TI4`) | the dangling handler takes the absent-component path | `tests/test_h_mad_tdd_gate_judge.py::test_claude_unresolvable_governed_is_judge_error` |
| TI5 | target_identity | AC-3.2 loop branch (`# M:TI5`) | the loop handler takes the absent-component path | `tests/test_h_mad_tdd_gate_judge.py::test_claude_unresolvable_governed_is_judge_error` |
| TI6 | target_identity | AC-3.6 cannot-be-read arm | an `OSError` from the open or the listing falls back to the spelling | `tests/test_h_mad_tdd_gate_judge.py::test_claude_unreadable_component_step5` |

`target_identity.json` carries `"root": "../.."` and runs this command:
`["python3.11", "-m", "pytest", "tests/test_h_mad_target_identity.py", "tests/test_h_mad_tdd_gate_judge.py", "tests/test_h_mad_codex_tdd_gate_judge.py", "-q"]`.

**Re-derived at the same guard (not counted)**:
- `H11` moves onto the new call line. It keeps its test key
  `tests/test_h_mad_tdd_gate_judge.py::test_traversal_target_is_gated[absolute]`. Its mutant skips
  normalisation of the joined path.
- `H6` moves onto the per-name `case` line. It keeps
  `tests/test_h_mad_tdd_gate_judge.py::test_exempt_write_on_unreadable_chain_is_allowed[state-file]`.
- The existing `H20B` is scored after this task and must report caught (AC-1.11).

**AC-1.7 negative control (run, not asserted)**: run
`python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/target_identity.json`
and read TI1 caught. Also record that
`tests/test_h_mad_target_identity.py::test_canonical_directory_returns_on_disk_spelling` fails
under TI1.

**Dependencies on other tasks**: Task 1.

---

## Task 4: codex-header-grammar

**Production file**: `h-mad/hooks/h-mad-codex-tdd-gate.py`
**Test file**: `h-mad/tests/test_h_mad_codex_tdd_gate_judge.py`
**Task shape**: `new-behaviour`

**Description**: This task implements §"Header grammar". `_patch_header_paths(patch)` replaces
`PATCH_TARGET.findall`, and the `PATCH_TARGET` constant is removed.

- The patch is split on `\n` only, with `str.split`.
- Both ends are trimmed of characters for which `str.isspace()` is true and whose code point is
  outside U+001C to U+001F.
- The markers are matched exactly: `*** Add File: `, `*** Update File: `, `*** Delete File: `,
  `*** Move to: `.
- An empty path, or one still containing U+0000 to U+001F or U+007F, is a bad header.
- The empty path is reachable only through this rule: the line `*** Update File: ` trims to
  `*** Update File:`, which no longer starts with the exact marker. A trimmed line that equals a
  marker with its one trailing space removed (`*** Add File:`, `*** Update File:`,
  `*** Delete File:`, `*** Move to:`) is that marker with an empty path, and so a bad header. It is
  equality, not a prefix test, so the M-22 spelling `*** Update File:\tsrc/prod.py` is still not a
  header. Dropping such a line as a non-header would reach the generic "could not identify" refusal,
  which carries no `kind=`.
- `_targets` returns `TargetParse(tool, paths, command, bad_header)`. Only `_main_guarded` unpacks
  it. A bad header never raises. When governed it refuses the whole patch `judge-error`, with the
  reason naming the header. When inactive it contributes no target.
- `--self-check` calls `_patch_header_paths` and gains a trailing-space case and an indented-header
  case, each yielding `src/prod.py`.

**Code structure**:
```python
class TargetParse(NamedTuple):
    tool: str
    paths: list[str]
    command: str
    bad_header: str   # "" when none

def _patch_header_paths(patch: str) -> tuple[list[str], str]: ...   # (paths, first bad header or "")
def _targets(payload: dict[str, Any]) -> TargetParse: ...
```

**Acceptance Criteria**:
- [ ] AC-4.1: `test_codex_trailing_header_whitespace_denies[crlf]`, `[space]`, `[tab]`, `[nbsp]`,
  `[u3000]`, `[u2028]`, `[u0085]`, `[u2003]`, `[vt]`, `[ff]` (the ten M-15 variants) deny with M-1's
  kind.
- [ ] AC-4.2: `test_codex_indented_header_denies[m16]` denies `no-test-resolved`, and `[m17]` denies.
- [ ] AC-4.3: `test_codex_move_to_trailing_space_denies` (M-19).
- [ ] AC-4.4: `test_codex_control_byte_header_is_judge_error[m20]` and `[u0001]` deny `judge-error`.
  `test_codex_control_byte_header_step3_allows[m20]` and `[u0001]` allow under `step3`.
- [ ] AC-4.5: `test_codex_inexact_marker_is_unidentified`, with one case for each of the five M-22
  spellings, denies "could not identify" fixed and unfixed.
- [ ] AC-4.6: `test_codex_trim_set_code_points` has one case per code point. U+0020, U+0009, U+000B,
  U+000C, U+000D, U+0085, U+00A0, U+3000 and U+2028 are trimmed. U+001C, U+001F, U+200B and U+FEFF
  are not trimmed. `test_patch_header_paths_split_on_newline_only`: a patch containing U+2028,
  U+001C and U+0085 inside one line yields that line whole.
- [ ] Bad header inactive: `test_codex_bad_header_does_not_raise_when_inactive` allows, and its output
  carries no `raised`.
- [ ] Empty path: `test_codex_empty_header_path_is_judge_error`. Under governing `step5`, the patch
  `*** Begin Patch\n*** Update File: \n@@\n-a\n+b\n*** End Patch\n` denies with
  `kind=judge-error`, and the reason names the header. The test asserts both, and asserts that the
  reason does not contain `could not identify`. RED: on the unfixed tree `PATCH_TARGET`'s `(.+)$`
  needs at least one character after `: `, so `findall` returns `[]` (run at `48d639f7`,
  §"Verified premises"), the targets are empty, and the gate denies with "H-MAD Phase 5 could not
  identify this write target", which has no `kind=`. The `kind=judge-error` assertion fails. GREEN:
  the trimmed line equals `*** Update File:`, the empty path is the bad header, and the governed
  refusal is `judge-error`.
- [ ] AC-4.7: the existing `test_codex_hook_self_check_reports_machine_readable_pass` in
  `h-mad/tests/test_h_mad_codex_runtime.py` stays green. The trim-removed control is row CX-TTRIM,
  run. Under it, `python3 h-mad/hooks/h-mad-codex-tdd-gate.py --self-check` prints
  `CODEX-TDD-GATE: FAIL parser`, and that output is recorded at GREEN.

**RED/GREEN**: 10 test functions, 7 RED and 3 regression guards.
- RED: `test_codex_trailing_header_whitespace_denies`, `test_codex_indented_header_denies`,
  `test_codex_move_to_trailing_space_denies`, `test_codex_control_byte_header_is_judge_error`,
  `test_codex_trim_set_code_points`, `test_patch_header_paths_split_on_newline_only`,
  `test_codex_empty_header_path_is_judge_error`.
- Regression guards: `test_codex_inexact_marker_is_unidentified`,
  `test_codex_control_byte_header_step3_allows`,
  `test_codex_bad_header_does_not_raise_when_inactive`. The existing
  `test_codex_hook_self_check_reports_machine_readable_pass` also stays green.

**Mutation rows** (4, in `h-mad/tests/mutation-specs/codex_gate_judge_wiring.json`):

| Row | Guard | Mutant | `test` |
|---|---|---|---|
| CX-LTRIM | AC-4.2 leading trim | leading trim removed | `tests/test_h_mad_codex_tdd_gate_judge.py::test_codex_indented_header_denies` |
| CX-TTRIM | AC-4.1 trailing trim (AC-4.7 control) | trailing trim removed | `tests/test_h_mad_codex_tdd_gate_judge.py::test_codex_trailing_header_whitespace_denies` |
| CX-CTRL | AC-4.4 control-byte refusal | control-byte check removed | `tests/test_h_mad_codex_tdd_gate_judge.py::test_codex_control_byte_header_is_judge_error` |
| CX-SPLIT | AC-4.6 `\n`-only split | `patch.split("\n")` becomes `patch.splitlines()` | `tests/test_h_mad_codex_tdd_gate_judge.py::test_patch_header_paths_split_on_newline_only` |

**Dependencies on other tasks**: Task 2.

---

## Task 5: judge-bounded-reap

**Production file**: `h-mad/scripts/h_mad_tdd_judge.py`, `h-mad/hooks/h-mad-tdd-gate.sh` (the `JUDGE_DENY_RE` alternative only), `h-mad/tests/tdd_gate_support.py` (adds `detaching_sleeper`)
**Test file**: `h-mad/tests/test_h_mad_tdd_judge.py`, `h-mad/tests/test_h_mad_tdd_gate_judge.py`, `h-mad/tests/test_h_mad_codex_tdd_gate_judge.py`
**Task shape**: `new-behaviour`

**Description**: This task implements §"Judge reap".

- Add `REAP_GRACE_S = 1.0`. `DRAIN_SECONDS` is not reused.
- `_run_bounded` returns `BoundedRun`: today's five fields in today's order, then
  `reap_failed: bool`.
- After `killpg` it runs `proc.communicate(timeout=REAP_GRACE_S)`. On `TimeoutExpired` it closes
  `stdout` and `stderr`, then runs `proc.wait(timeout=remaining)` with
  `remaining = max(0.0, REAP_GRACE_S - elapsed)`, and sets `reap_failed=True`. If that `wait`
  raises `TimeoutExpired`, `reap_failed` stays true and the runner does not wait again.
- `timed_out` stays true. The `error` field keeps its meaning.
- In `resolve`, `reap_failed` is read immediately before `if timed_out:` and returns a
  `judge-timeout` deny. In `judge`, it is read before the `# M:K3` line, which stays byte-identical,
  and sets the kind to `judge-timeout`.
- `judge-timeout` joins the `break` set.
- The priority tuple becomes
  `("judge-timeout", "timeout", "pytest-missing", "pytest-error", "no-summary", "no-tests-ran", "test-passing")`.
- `KINDS` gains `judge-timeout`.
- `JUDGE_DENY_RE` in `h-mad/hooks/h-mad-tdd-gate.sh` gains `judge-timeout` as one more alternative.
- `detaching_sleeper(path, pidfile, seconds)` writes a fake interpreter that starts a
  `start_new_session=True` grandchild. The grandchild inherits the pipes and writes its pid to
  `pidfile`. Teardown kills it through the pidfile.

**Code structure**:
```python
REAP_GRACE_S = 1.0

class BoundedRun(NamedTuple):
    returncode: Optional[int]
    out: str
    err: str
    timed_out: bool
    error: str
    reap_failed: bool

def _run_bounded(argv: Sequence[str], cwd: Path, deadline: float) -> BoundedRun: ...
```

**Acceptance Criteria**:
- [ ] AC-5.1: `test_run_bounded_reap_failure_is_bounded`. The deadline is `start + 2.0`, on a child
  that detaches `sleep 12` and sleeps 30. It returns in under 4.0 s with `reap_failed=True`, and the
  sleeper is killed through its pidfile in teardown. The unfixed return at about 12 s is observed
  at RED and recorded.
- [ ] AC-5.2: `test_run_bounded_plain_timeout_is_not_reap_failure` gives `timed_out=True` and
  `reap_failed=False`. `test_run_bounded_kills_the_process_group` moves to the six-field result.
  `test_name_map_runs_under_the_budget` and `test_timeout_kind` keep their `< 6.0 s` bounds and are
  not edited.
- [ ] AC-5.3: `test_judge_name_map_detach_is_judge_timeout` calls `judge()` with `NAME_MAP`
  monkeypatched to a detaching script. `test_judge_venv_interpreter_detach_is_judge_timeout` calls
  `judge()` with `select_interpreter` returning a `detaching_sleeper` interpreter and the name map
  intact. Each is its own test and returns DENY `judge-timeout` within `budget_s + REAP_GRACE_S + 1.0`
  s, using the `budget_s` the test passes.
- [ ] Priority: `test_judge_timeout_has_priority`. Two present tests: the first scores `pytest-error`
  and the second detaches. The kind is `judge-timeout`.
- [ ] AC-5.4: `test_claude_gate_judge_timeout_stub` (in `h-mad/tests/test_h_mad_tdd_gate_judge.py`)
  uses `_tree_b` with `judge_line="TDD-JUDGE: DENY kind=judge-timeout reason=r"` and rc 0, and gives
  `BLOCK kind=judge-timeout`. `test_codex_gate_judge_timeout_reason` (in
  `h-mad/tests/test_h_mad_codex_tdd_gate_judge.py`) finds `kind=judge-timeout` in the reason.
- [ ] AC-5.5: `test_claude_gate_kind[judge-timeout]` and `test_codex_gate_kind[judge-timeout]` are
  added as parametrised rows. The fixture is `detaching_sleeper` in place of `sleeper`.

**RED/GREEN**: 10 test functions touched: 7 new, 1 modified, and 2 existing functions that each gain
one row. 9 are RED and 1 is a guard.
- RED (9): the new `test_run_bounded_reap_failure_is_bounded`,
  `test_run_bounded_plain_timeout_is_not_reap_failure`, `test_judge_name_map_detach_is_judge_timeout`,
  `test_judge_venv_interpreter_detach_is_judge_timeout`, `test_judge_timeout_has_priority` and
  `test_claude_gate_judge_timeout_stub`; the modified `test_run_bounded_kills_the_process_group`
  (six-field unpack); and the `judge-timeout` rows of `test_claude_gate_kind` and
  `test_codex_gate_kind`.
- Guard (1): the new `test_codex_gate_judge_timeout_reason`. The Codex gate formats `verdict.kind`, so
  it passes at RED. The unedited `test_name_map_runs_under_the_budget` and `test_timeout_kind` also
  stay green.

**Mutation rows** (5: 4 in `h-mad/tests/mutation-specs/tdd_judge_scoring.json` with `file`
`scripts/h_mad_tdd_judge.py`, and 1 in `claude_gate_judge_wiring.json`):

| Row | Guard | Mutant | `test` |
|---|---|---|---|
| JT-REAP | AC-5.1 bounded reap | the post-kill `communicate` loses its timeout | `tests/test_h_mad_tdd_judge.py::test_run_bounded_reap_failure_is_bounded` |
| JT-NM | AC-5.3 name-map mapping | `resolve` ignores `reap_failed` | `tests/test_h_mad_tdd_judge.py::test_judge_name_map_detach_is_judge_timeout` |
| JT-PY | AC-5.3 pytest-path mapping | `judge` ignores `reap_failed` | `tests/test_h_mad_tdd_judge.py::test_judge_venv_interpreter_detach_is_judge_timeout` |
| JT-PRIO | priority of `judge-timeout` | `judge-timeout` moved to the end of the priority tuple | `tests/test_h_mad_tdd_judge.py::test_judge_timeout_has_priority` |
| CG-JT | AC-5.4 `JUDGE_DENY_RE` branch | `judge-timeout` alternative removed | `tests/test_h_mad_tdd_gate_judge.py::test_claude_gate_judge_timeout_stub` |

JT-PRIO's mutant must break its test. With `judge-timeout` in the `break` set, a detaching second
test is the last outcome, so with the tuple mutated `pytest-error` wins. Confirm that at GREEN
before the row is committed.

**Dependencies on other tasks**: None (independent of T1 to T4). Existing finds `K3` and `K3B` stay
matching.

---

## Task 6: cross-gate-differential

**Production file**: none
**Test file**: `h-mad/tests/test_h_mad_tdd_gate_differential.py` (new)
**Task shape**: `gate` (a test-only verdict task that writes no production file)

**Description**: This task adds a differential over spec FR-6's domain. It imports `decision` and
`hermetic_env` from `h-mad/tests/tdd_gate_support.py`. The `conftest.py` fixture named
`hermetic_env` is a different function.

- Cells: M-1 to M-14, with M-13 as `m13-leaf` and `m13-intermediate`, and M-18 over `m13-leaf`,
  `m13-intermediate` and `m14`. The controls are `notes.md`, `tests/test_x.py` and `sub/test_x.PY`.
  Each cell is its own row, under `step5` and, for the unresolvable cells, `step3`.
- Unresolvable cells assert that their resolved prefix is inside the canonical root: M-12 `R/docs`,
  M-13 leaf `R/src`, M-13 intermediate `R`, M-14 `R/src`.
- Assertions, each with its own message:
  1. The two gates' decisions are equal.
  2. Where both deny, their kinds are equal. The Codex kind is parsed with `kind=([a-z-]+)`.
  3. Decision and kind equal the published expectation table.
  4. The deny count is derived from the table and never typed.

**Acceptance Criteria**:
- [ ] AC-6.1 (fixed): `test_differential_cell` passes on every row, and
  `test_expectation_table_deny_count_is_derived` passes.
- [ ] AC-6.1 (unfixed, run, not asserted): run
  `B=$(git merge-base HEAD main); T=$(mktemp -d); git archive "$B" h-mad | tar -x -C "$T"; cp h-mad/tests/test_h_mad_tdd_gate_differential.py h-mad/tests/tdd_gate_support.py "$T/h-mad/tests/"; "$PY" -m pytest -q -p no:cacheprovider "$T/h-mad/tests/test_h_mad_tdd_gate_differential.py"; rm -rf "$T"`.
  The overlay is the two test-side files only: the differential and the fixed
  `tdd_gate_support.py`, which carries T1's `assert_case_insensitive` that the M-8 and M-9 rows
  call. `h-mad/hooks/` and `h-mad/scripts/` stay the base's, so both gates are the unfixed ones.
  Before recording, check that `$T/h-mad/scripts/h_mad_target_identity.py` does not exist and that
  the pytest output has no `ERROR` collection line, so every failure is an assertion failure and
  not an import or collection error.
  Record it. The gate-equality assertion fails on exactly M-4, M-5, M-6, M-7, M-8, M-11 and M-12. The
  expectation-table assertion also fails on M-2, M-3, M-9, M-10, M-13 and M-14. Record each set as
  its own check.
- [ ] AC-6.2 (run once per gate, not asserted): in a temporary copy of `h-mad/`, apply CG-CANON's
  replace alone and run the differential; it fails. In a second copy, apply CX-CANON's and
  CX-RESOLVE-M9's replaces together, plus a payload-cwd site restored to `Path.resolve()`, and run
  the differential; it fails. Delete both copies after the runs.
- [ ] AC-6.3: re-run `python3 docs/03-analysis/probes/codex-tdd-gate-defects/dd7_differential.py` on
  the fixed tree. Any changed cell is a stated, reviewed delta. The existing
  `test_dd7_differential_matches_the_published_cells` keeps its assertion text.

**RED/GREEN**: 2 test functions. Both pass when written (T2 and T3 are GREEN), and neither has a RED.
Their discrimination is the executed AC-6.1 unfixed run and the AC-6.2 removal runs above.
**Mutation rows**: 0.
**Dependencies on other tasks**: Task 2, Task 3.

---

## Task 7: documentation-surfaces

**Production file**: `h-mad/references/codex-implementer-prompt.md`, `h-mad/SKILL.md`, `h-mad/references/codex-runtime.md`
**Test file**: `h-mad/tests/test_h_mad_tdd_gate_docs.py` (unchanged; guards)
**Task shape**: `refactor` (documentation catches up with landed behaviour; no new test)

**Description**: This task implements §"Documentation surfaces (T7 and T12)".

- `codex-implementer-prompt.md`: rewrite the resolved-identity and any-case `.py` sentences in place,
  inside the one paragraph under `## Context` that begins `Hook:`. No second `Hook:` line is added.
- `h-mad/SKILL.md`: the bullet beginning ``- `h_mad_tdd_judge.py` —`` gains `judge-timeout`. The
  frontmatter `name: h-mad` and the description beginning "Orchestrate the seven-phase H-MAD
  development workflow" stay byte-identical.
- `codex-runtime.md`, `### Trust boundary`, gains two sentences. The first: a reap that fails is DENY
  `judge-timeout`. The second: a governed target the canonicaliser cannot resolve is DENY
  `judge-error` naming the component. No closed kind list is added.
- Nothing is added under `## The TDD gate` in `grok-runtime.md` or `agy-runtime.md`.
- After T12, re-check the other gate sentences in the three adapters against the fixed gates.

**Acceptance Criteria**:
- [ ] `grep -c '^Hook:' h-mad/references/codex-implementer-prompt.md` prints `1`. The existing
  `test_h_mad_tdd_gate_docs.py` assertion carrying `# M:D1` stays green. `D1`'s find still matches.
- [ ] ``grep -n '^- `h_mad_tdd_judge.py` —' h-mad/SKILL.md`` prints one line containing
  `judge-timeout`.
- [ ] `sed -n '/^### Trust boundary/,/^##/p' h-mad/references/codex-runtime.md | grep -c -F judge-timeout`
  prints at least `1`, and the same range with `grep -c -F judge-error` prints at least `1`.
- [ ] Judge-kind tokens in `## The TDD gate` of `grok-runtime.md` and `agy-runtime.md`: 0 matching
  lines in each, measured with the design's §"Verified premises" command.

**RED/GREEN**: no new test and no RED. Regression guards: `h-mad/tests/test_h_mad_tdd_gate_docs.py`
and `h-mad/tests/test_host_runtime_docs.py` stay green.
**Mutation rows**: 0.
**Dependencies on other tasks**: Task 2, Task 3, Task 4, Task 5, Task 12.

---

## Task 8: mutation-census

**Production file**: none (spec files are committed by their owning tasks; this task promotes any remaining `.json.pending` and runs the census)
**Test file**: `h-mad/tests/mutation-specs/target_identity.json`, `h-mad/tests/mutation-specs/claude_gate_judge_wiring.json`, `h-mad/tests/mutation-specs/codex_gate_judge_wiring.json`, `h-mad/tests/mutation-specs/tdd_judge_scoring.json`, `h-mad/tests/mutation-specs/resume_decision_git_dir.json`
**Task shape**: `gate`

**Description**: This task runs each of the five specs in the Test file line alone with
`python3 h-mad/scripts/h_mad_mutation_harness.py`, passing the spec path as the only argument, and
reads the `MUTATION:` token. It then
runs `--check-anchors` over `h-mad/tests/mutation-specs/*.json`.
`h-mad/tests/mutation-specs/resume_decision_cannot_judge.json` is not edited.
`docs/03-analysis/tdd-gate-fail-opens.pending-mutation-specs/` must be empty at the end of this task.

**Acceptance Criteria**:
- [ ] Each of the five specs prints `MUTATION: ALL_CAUGHT` with `survived=0`. H20B is caught on the
  fixed tree.
- [ ] `ANCHORS: ANCHORS_OK` with `drifted=0`.
- [ ] The per-guard census has one line per AC-7.1 guard, 25 guards over 26 rows (the table below),
  and each is reported caught. The plan's floor of 25 is met.
- [ ] Re-measure the floor with plan v1.4's command at the spec's sha (644f8bf6). The readings should
  be 21, 3 and 1. If the spec moved, re-derive.

AC-7.1 guard census (one row per guard; AC-3.3 is named once in AC-7.1 and has a row in each gate):

| # | AC-7.1 guard | Row(s) | Task |
|---|---|---|---|
| 1 | Claude-gate canonicaliser (AC-1.1) | CG-CANON | T3 |
| 2 | Codex-gate canonicaliser (AC-1.4) | CX-CANON | T2 |
| 3 | on-disk-spelling step (AC-1.5) | TI1 | T3 |
| 4 | hard-link rule (AC-1.9) | TI2 | T3 |
| 5 | root canonicalisation (AC-1.3) | TI3 | T3 |
| 6 | fold, Claude gate (AC-2.2) | CG-FOLD | T3 |
| 7 | fold, Codex gate (AC-2.2) | CX-FOLD | T2 |
| 8 | dangling branch (AC-3.1) | TI4 | T3 |
| 9 | loop branch (AC-3.2) | TI5 | T3 |
| 10 | cannot-be-read arm (AC-3.6) | TI6 | T3 |
| 11 | governing-state condition (AC-3.3) | CG-GOV, CX-GOV | T3, T2 |
| 12 | leading trim (AC-4.2) | CX-LTRIM | T4 |
| 13 | trailing trim (AC-4.1) | CX-TTRIM | T4 |
| 14 | control-byte refusal (AC-4.4) | CX-CTRL | T4 |
| 15 | `\n`-only split (AC-4.6) | CX-SPLIT | T4 |
| 16 | bounded reap (AC-5.1) | JT-REAP | T5 |
| 17 | reap-failure mapping, name-map path (AC-5.3) | JT-NM | T5 |
| 18 | reap-failure mapping, pytest path (AC-5.3) | JT-PY | T5 |
| 19 | priority of `judge-timeout` (AC-5.3) | JT-PRIO | T5 |
| 20 | `JUDGE_DENY_RE` branch (AC-5.4) | CG-JT | T5 |
| 21 | safe-list entry (AC-8.1) | CX-SAFE | T11 |
| 22 | entry equals parser options (AC-8.2) | CX-EQ | T11 |
| 23 | id-file read (AC-8.3) | RD-READ | T10b |
| 24 | `cannot_judge` answer (AC-8.4) | RD-CJ | T10b |
| 25 | mutual exclusion (AC-8.5) | RD-MX | T10b |

The table has 25 guard lines, which matches the plan's floor: AC-7.1 has 21 `(AC-` parentheticals,
plus one for each of the 3 "separate mutations" pairs, plus one for "in each gate", so
21 + 3 + 1 = 25. Guard 11 carries two rows, one per gate, so the census holds 26 rows. Connection
rows beyond the census, 6 in total: CX-RESOLVE-M9, CX-FORCE-SCRIPT,
CX-FORCE-CWD, CX-FOLD-FORCE (T2), and RD-WIRE, RD-FORCE (T10b). Post-registration guard rows
beyond the census, 2 in total: CX-OPT-LONG and CX-OPT-SHORT (T11). They are scored with the rest
of `codex_gate_judge_wiring.json`, and each is reported caught by its own parametrised case.

**Mutation rows**: 0 new (census only).
**Dependencies on other tasks**: Task 1, Task 2, Task 3, Task 4, Task 5, Task 6, Task 10b, Task 11.

---

## Task 9: fixed-reading

**Production file**: `docs/03-analysis/probes/tdd-gate-fail-opens/reading-fixed.txt`
**Test file**: none
**Task shape**: `operational` (runs the probe and the comparator built in T0 against the fixed tree)

**Description**: This task re-runs `reproduce.py` on the fixed tree and commits the reading. It then
runs `compare_readings.py reading-unfixed.txt reading-fixed.txt` and commits that output.

**Acceptance Criteria**:
- [ ] The comparison prints `COMPARE: PASS softened=6 approved=6` and exits 0.
- [ ] `FR-8 cat-subst` is present in both readings and stays deny.
- [ ] The fixed reading contains `REPRO: agent-cli-reachable=no`.

**Mutation rows**: 0.
**Dependencies on other tasks**: Task 1 to Task 8, Task 10a, Task 10b, Task 11, Task 12.

---

## Task 10a: resume-git-dir-reader

**Production file**: `h-mad/scripts/h_mad_resume_decision.py`
**Test file**: `h-mad/tests/test_h_mad_resume_decision.py`
**Task shape**: `new-behaviour`

**Description**: This task adds three things.

- `GIT_DIR_BOUND_S = 10.0`, distinct from `REAP_GRACE_S` and `DRAIN_SECONDS`.
- `session_id_from_git_dir(feature)`. It runs
  `subprocess.run(["git", "rev-parse", "--absolute-git-dir"], timeout=GIT_DIR_BOUND_S, capture_output=True, text=True)`,
  reads `h-mad-session-id.` plus the feature name inside that git dir, and strips it. It returns the
  id, or `None` on each of six failure arms: `git` absent (`FileNotFoundError` from `subprocess.run`),
  a non-zero git exit, `subprocess.TimeoutExpired`, the id file absent, `OSError` on the read, and an
  empty id after stripping.
- A module-level `build_parser()` that `main` calls, carrying today's five options unchanged:
  `--state`, `--feature`, `--host`, `--session-id` and `--now`. The flag itself is T10b's.

The `timeout` and `gtimeout` CLIs are not used. The bound is the stdlib `timeout=` argument.

**Code structure**:
```python
GIT_DIR_BOUND_S = 10.0
def build_parser() -> argparse.ArgumentParser: ...
def session_id_from_git_dir(feature: str) -> str | None: ...
```

**Acceptance Criteria**:
- [ ] AC-8.3 (unit half): `test_session_id_from_git_dir_reads_minted_id[repo]` and `[worktree]` use
  a linked worktree whose git dir is not `root/.git`. The id is minted with a trailing newline, as
  the adapter's mint line writes it, and the function returns it stripped.
- [ ] AC-8.4 (unit half), plus the bound arm: `test_session_id_from_git_dir_failure_returns_none[absent]`,
  `[empty]`, `[whitespace]`, `[mode000]`, `[outside-repo]`, `[no-git]`, `[bound-expired]`.
  - `[mode000]` asserts that reading raises `PermissionError`, and it fails, never skips, when it
    does not.
  - `[no-git]` uses a hermetic `PATH` without `git`.
  - `[bound-expired]` puts a `git` stub that sleeps on `PATH` and monkeypatches `GIT_DIR_BOUND_S` to
    `0.5`. It is the FR-8 bound arm and not an AC-8.4 case.
- [ ] `test_build_parser_is_module_level`: `build_parser()` exists and its long options include
  each of the five above. It asserts inclusion, not equality, so it stays green when T10b adds the
  sixth option. The exact set of six is T10b's `test_build_parser_offers_the_git_dir_flag`.
- [ ] `test_git_dir_bound_constant`: `GIT_DIR_BOUND_S == 10.0`.

**RED/GREEN**: 4 test functions, all RED: the symbols are absent, and each test reads them as module
attributes, so each fails on its own. The 12 existing test functions in the file are regression
guards.
**Mutation rows**: 0. RD-READ's guard lives in this task's function, but its catching test is T10b's
CLI test, so the row is parked as `.json.pending` and committed at T10b.
**Dependencies on other tasks**: None (independent of T0 to T9).

---

## Task 10b: resume-git-dir-flag

**Production file**: `h-mad/scripts/h_mad_resume_decision.py`
**Test file**: `h-mad/tests/test_h_mad_resume_decision.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/scripts/h_mad_resume_decision.py:main` → `session_id_from_git_dir`
**WIRE-PIN**: `tests/test_h_mad_resume_decision.py::test_git_dir_flag_matches_session_id_token`

**Description**: `build_parser()` puts `--session-id-from-git-dir` (`store_true`) and `--session-id`
in one argparse mutually exclusive group. With the flag, `main` calls
`session_id_from_git_dir(args.feature)` before `decide`. On `None` it prints `cannot_judge`, returns
0 and does not call `decide`. Otherwise it passes the id as `session_id`. Without the flag, `main` is
unchanged and the git dir is not read.

**WIRE-PIN RED reason (caller-observable)**: at RED, `session_id_from_git_dir` exists (T10a) and
nothing calls it. `test_git_dir_flag_matches_session_id_token[repo-owner]` runs the CLI with
`--host codex --session-id-from-git-dir`. It expects `enter_autonomous`, the token that
`--session-id` of the file content prints. The unwired parser rejects the flag, so stdout is empty,
and the assertion on the stdout token fails. Under wire removal (RD-WIRE: the flag is accepted and
the call is skipped), `--host codex` with a `None` id prints `cannot_judge`, and the same assertion
fails.

**Acceptance Criteria**:
- [ ] AC-8.3: `test_git_dir_flag_matches_session_id_token[repo-owner]`, `[repo-other]`,
  `[worktree-owner]`, `[worktree-other]`. The state holds the feature with `last_completed_phase` 4.
  Owned by the minted id, the command prints `enter_autonomous`. Owned by another live session under
  `--now`, it prints `owned_elsewhere`. Each token equals the output of `--session-id` with the file
  content.
- [ ] AC-8.4, plus the bound arm: `test_git_dir_flag_failure_is_cannot_judge` has fourteen cases,
  `[codex-absent]` through `[claude-bound-expired]`: the seven failure ids of T10a under each of
  `--host codex` and `--host claude`. Each prints `cannot_judge`. The `claude` cases discriminate: a
  `None` into `decide` prints `enter_autonomous` against the AC-8.3 state. `bound-expired` is the
  FR-8 bound arm and is not an AC-8.4 case.
- [ ] AC-8.5: `test_git_dir_flag_excludes_session_id`. `--session-id x --session-id-from-git-dir`
  exits 2 with empty stdout, and stderr contains `not allowed with argument`. A `git` stub on `PATH`
  that records its invocation shows the read did not run.
- [ ] `test_build_parser_offers_the_git_dir_flag`: the parser's long options minus `--help` are the
  six of design §"FR-8 git-dir read".
- [ ] Connection, forced arm: `test_session_id_alone_does_not_read_git_dir`. It puts the recording
  `git` stub of `test_git_dir_flag_excludes_session_id` first on `PATH`, and it mints the id file so
  that a read would succeed. `--session-id` of another live session, without the flag, prints
  `owned_elsewhere`, and the stub's record file shows no invocation. The token alone does not
  discriminate: an unconditional read whose result is discarded still prints `owned_elsewhere`. The
  absent invocation does. Under RD-FORCE the read runs, the stub records a
  `rev-parse --absolute-git-dir` call, and the test fails.

**RED/GREEN**: 5 test functions, 4 RED and 1 guard.
- RED: `test_git_dir_flag_matches_session_id_token`, `test_git_dir_flag_failure_is_cannot_judge`,
  `test_git_dir_flag_excludes_session_id` (unfixed stderr says `unrecognized arguments`),
  `test_build_parser_offers_the_git_dir_flag`.
- Guard: `test_session_id_alone_does_not_read_git_dir` (at RED nothing calls the reader, so the
  stub records nothing). The T10a tests stay green: `test_build_parser_is_module_level` asserts
  inclusion of the five options, and the sixth does not break it.

**Mutation rows** (5, in the new `h-mad/tests/mutation-specs/resume_decision_git_dir.json`,
`"root": "../.."`, command
`["python3.11", "-m", "pytest", "tests/test_h_mad_resume_decision.py", "-q"]`, `file`
`scripts/h_mad_resume_decision.py`):

| Row | Guard | Mutant | `test` |
|---|---|---|---|
| RD-READ | AC-8.3 id-file read | the read returns an empty string | `tests/test_h_mad_resume_decision.py::test_git_dir_flag_matches_session_id_token` |
| RD-CJ | AC-8.4 `cannot_judge` answer | the `None` branch removed, so `decide` is called with `None` | `tests/test_h_mad_resume_decision.py::test_git_dir_flag_failure_is_cannot_judge` |
| RD-MX | AC-8.5 mutual exclusion | the flag added outside the exclusive group | `tests/test_h_mad_resume_decision.py::test_git_dir_flag_excludes_session_id` |
| RD-WIRE | connection removal | flag accepted, `session_id_from_git_dir` not called | `tests/test_h_mad_resume_decision.py::test_git_dir_flag_matches_session_id_token` |
| RD-FORCE | connection forced | the read runs even when only `--session-id` is passed | `tests/test_h_mad_resume_decision.py::test_session_id_alone_does_not_read_git_dir` |

**Dependencies on other tasks**: Task 10a.

---

## Task 11: codex-safe-list-resume-key

**Production file**: `h-mad/hooks/h-mad-codex-tdd-gate.py`
**Test file**: `h-mad/tests/test_h_mad_codex_runtime.py`
**Task shape**: `new-behaviour`

**Description**: `SAFE_HMAD_SCRIPT_OPTIONS` gains the key `h_mad_resume_decision.py`. Its value is
exactly `--state`, `--feature`, `--host`, `--session-id`, `--now` and `--session-id-from-git-dir`.
`_safe_hmad_script` gains no per-script branch. The key falls through to its closing `return True`.

**Acceptance Criteria**:
- [ ] AC-8.2: `test_safe_list_resume_options_equal_parser` builds the set from
  `h_mad_resume_decision.build_parser()` actions' `option_strings`, minus `--help` and `-h`, and
  asserts that it equals the entry. It never types the set.
- [ ] AC-8.1 (literal halves): `test_codex_hook_admits_resume_oracle_forms[literal-uuid]` and
  `[git-dir-flag]` use the shell payload shape of
  `test_codex_hook_allows_exact_safe_hmad_control_script`, under governing state, with the command
  built in the test. Each gives rc 0 and empty stdout.
- [ ] AC-8.1 control: `test_codex_hook_refuses_cat_subst_oracle`. The pre-FR-8 `$(cat` line is
  denied, fixed and unfixed.
- [ ] AC-8.2 refusals: `test_codex_hook_refuses_unknown_resume_options[bogus]` (`--bogus x`) and
  `[dash-h]` (`-h`) are each denied, fixed and unfixed. Each case's command is the `[git-dir-flag]`
  command of `test_codex_hook_admits_resume_oracle_forms` with the one option appended, so the
  appended option is the only difference from an admitted command.
- [ ] Post-registration permissive mutations: at RED the resume key is absent, so
  `_safe_hmad_script` returns `False` at `if allowed_options is None:` and both cases pass without
  reaching the option loop. Their green at RED proves nothing about option filtering. Each case
  is therefore also run under a mutant of the landed T11 source, where the resume key is present and
  one option check is disabled: CX-OPT-LONG (the condition of
  `if token.startswith("--") and token.split("=", 1)[0] not in allowed_options:` replaced by
  `False`) must be caught by `[bogus]`, and CX-OPT-SHORT (the condition of
  `if token.startswith("-") and not token.startswith("--"):` replaced by `False`) must be caught
  by `[dash-h]`. The condition is replaced, never the `return False` line deleted: a deleted body
  is a `SyntaxError`, and that is not a catch.
  Verify each mutation landed before reading its verdict: `--check-anchors` reports the row ok
  (its `find` text matches exactly once in the landed source), and the named case's failure,
  printed by the harness, is the case's deny assertion on an rc 0, empty-stdout allow. An error,
  an import failure or an unmutated source is not a catch.

**RED/GREEN**: 4 test functions, 2 RED and 2 guards.
- RED: `test_safe_list_resume_options_equal_parser`, `test_codex_hook_admits_resume_oracle_forms`.
- Guards: `test_codex_hook_refuses_cat_subst_oracle`, `test_codex_hook_refuses_unknown_resume_options`.
  The existing `test_codex_hook_allows_exact_safe_hmad_control_script` stays green.
  `test_codex_hook_refuses_unknown_resume_options` counts as a guard only with CX-OPT-LONG and
  CX-OPT-SHORT caught at GREEN (above).

**Mutation rows** (4, in `h-mad/tests/mutation-specs/codex_gate_judge_wiring.json`):

| Row | Guard | Mutant | `test` |
|---|---|---|---|
| CX-SAFE | AC-8.1 safe-list entry | the resume key deleted | `tests/test_h_mad_codex_runtime.py::test_codex_hook_admits_resume_oracle_forms` |
| CX-EQ | AC-8.2 equality | one option added to the entry | `tests/test_h_mad_codex_runtime.py::test_safe_list_resume_options_equal_parser` |
| CX-OPT-LONG | AC-8.2 refusal, long option (post-registration) | resume key present; the condition of the `--` membership `if` in `_safe_hmad_script` replaced by `False` | `tests/test_h_mad_codex_runtime.py::test_codex_hook_refuses_unknown_resume_options[bogus]` |
| CX-OPT-SHORT | AC-8.2 refusal, single-dash option (post-registration) | resume key present; the condition of the single-dash `if` in `_safe_hmad_script` replaced by `False` | `tests/test_h_mad_codex_runtime.py::test_codex_hook_refuses_unknown_resume_options[dash-h]` |

**Dependencies on other tasks**: Task 10b.

---

## Task 12: adapter-oracle-lines

**Production file**: `h-mad/references/codex-runtime.md`, `h-mad/references/grok-runtime.md`, `h-mad/references/agy-runtime.md`
**Test file**: `h-mad/tests/test_host_runtime_docs.py`, `h-mad/tests/test_h_mad_codex_runtime.py`
**Task shape**: `new-behaviour`

**Description**: In each adapter, the one fenced `h_mad_resume_decision.py` invocation becomes the
following line, one per file:
- `python3 "<HMAD_SKILL_ROOT>/scripts/h_mad_resume_decision.py" --host codex --state docs/.bkit-memory.json --feature "<feature>" --session-id-from-git-dir`
- `python3 "<HMAD_SKILL_ROOT>/scripts/h_mad_resume_decision.py" --host grok --state docs/.bkit-memory.json --feature "<feature>" --session-id-from-git-dir`
- `python3 "<HMAD_SKILL_ROOT>/scripts/h_mad_resume_decision.py" --host agy --state docs/.bkit-memory.json --feature "<feature>" --session-id-from-git-dir`

The angle-bracketed `HMAD_SKILL_ROOT` and `feature` slots in those lines are the adapters' own
literal text, unchanged from today's oracle line. The empty-id
paragraph becomes one sentence in all three: "the oracle cannot read the id and returns
`cannot_judge`". Today it begins "If the id file becomes unreadable" in codex and agy, and "An
unreadable id file gives the oracle an empty id" in grok.

**Residual (orchestrator decision 3)**: the five `h_mad_state_write.py` lines in the same fence keep
their `$(cat` substitution, and this feature leaves them out of scope. The `--session-id "<this
session's id>"` line in `h-mad/SKILL.md` for the Claude host stays.

**Acceptance Criteria**:
- [ ] AC-8.6: `test_claims_section_fenced_lines[h-mad-codex-oracle]`, `[h-mad-agy-oracle]` and
  `[h-mad-grok-oracle]`. The `oracle` condition moves from `"--session-id " + SID_READ` to
  `"--session-id-from-git-dir"` with no `$` in the line. The `no-dollar-sid` case keeps
  `any(SID_READ in line)`.
- [ ] AC-8.6: `test_claims_lines_execute_across_invocations` selects the oracle line by the flag, and
  its oracle run still returns the minted owner's token. The control no longer uses
  `oracle.replace(SID_READ, '""')`. It removes the minted id file before the control run and asserts
  `cannot_judge`.
- [ ] AC-8.1 (adapter half): `test_codex_hook_admits_adapter_oracle_lines[codex]`, `[grok]`, `[agy]`
  (in `h-mad/tests/test_h_mad_codex_runtime.py`). Each reads the adapter's oracle line, replaces
  the `HMAD_SKILL_ROOT` slot with the absolute skill root and the `feature` slot with the literal
  name `fixture-feature`, and gets rc 0 and empty stdout under governing state.

**RED/GREEN**: 3 test functions, all RED: the two modified `test_host_runtime_docs.py` functions and
`test_codex_hook_admits_adapter_oracle_lines`. Guards: every other case of
`test_claims_section_fenced_lines` (`create-claim`, `claim`, `beat`, `set`, `release`, `mint`,
`oracle-first`, `no-dollar-sid`, `prose-once-at-bootstrap`, `prose-never-deleted`) stays green.
**Mutation rows**: 0.
**Dependencies on other tasks**: Task 10b, Task 11.

---

## Execution order

T0 → T1 → T2 → T3 → T4 → T5 → T10a → T10b → T11 → T12 → T6 → T7 → T8 → T9. T5 and T10a have no
upstream dependency and may run earlier. The order above keeps one task in flight.

## Counts

- Tasks: 14 (T0, T1, T2, T3, T4, T5, T6, T7, T8, T9, T10a, T10b, T11, T12). By shape: `wiring` 3
  (T2, T3, T10b), `new-behaviour` 6 (T1, T4, T5, T10a, T11, T12), `refactor` 1 (T7), `gate` 3
  (T0, T6, T8), `operational` 1 (T9). 3 + 6 + 1 + 3 + 1 = 14.
- Mutation rows by owning task: T2 7, T3 9, T4 4, T5 5, T10b 5, T11 4. 7 + 9 + 4 + 5 + 5 + 4 = 34.
  Of those, 26 are AC-7.1 rows over 25 guards (the census table), 6 are connection rows
  (CX-RESOLVE-M9, CX-FORCE-SCRIPT, CX-FORCE-CWD, CX-FOLD-FORCE, RD-WIRE, RD-FORCE) and 2 are
  post-registration guard rows (CX-OPT-LONG, CX-OPT-SHORT). 26 + 6 + 2 = 34.
  Re-derived only, not counted: H11 and H6. Existing and scored after T3: H20B.
- New or modified test functions with a RED: T1 16, T2 12, T3 16, T4 7, T5 9, T10a 4, T10b 4,
  T11 2, T12 3.

## Verified premises

One reading, at `48d639f7` (`git rev-parse --short=8 HEAD`), 2026-09-29, from `/Users/kimhawk/orca/skills`.
Units are matching lines unless stated.

| Premise | Command | Result |
|---|---|---|
| `ROOT_ABS` `pwd -P` and `# M:H11` normpath | `grep -n 'pwd -P\|M:H11' h-mad/hooks/h-mad-tdd-gate.sh` | 3 lines: the `# M:H8` walk, `ROOT_ABS=$(cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null && pwd -P) \|\| ROOT_ABS=""`, and the `os.path.normpath` call carrying `# M:H11` |
| `RAW_TARGET` placement | `grep -n 'RAW_TARGET=' h-mad/hooks/h-mad-tdd-gate.sh` | 1 line, immediately before the `ROOT_ABS=` line |
| `_pct_decode` body | `grep -n '^_pct_decode()' h-mad/hooks/h-mad-tdd-gate.sh` | 1 line: `_pct_decode() { [ "$1" = % ] && return 0; printf '%b' "${1//%/\\x}"; }` |
| `_pct_capture`, `_read_canon`, `_fold_py` absent | `grep -c '^_pct_capture\|^_read_canon\|^_fold_py' h-mad/hooks/h-mad-tdd-gate.sh` | 0. Load-bearing: T3 adds them |
| `JUDGE_DENY_RE` | `grep -n '^JUDGE_DENY_RE=' h-mad/hooks/h-mad-tdd-gate.sh` | 1 line, 10 alternatives, no `judge-timeout` |
| basename case and per-name targets | `grep -n 'M:H6\|M:H19\|M:H20\|M:H13' h-mad/hooks/h-mad-tdd-gate.sh` | `case "${TARGET_PATH##*/}" in  # M:H6`, the `# M:H19` in-root line, `elif _dir_match "$TARGET_PATH" && _dir_match "$RAW_TARGET"; then  # M:H20`, the `# M:H13` refusal |
| Codex symbols | `grep -n 'def _load_judge\|def _project_root\|def _payload_cwd_base\|def _relative_target\|def _is_production_python\|def _targets\|def _main_guarded\|PATCH_TARGET\|M:G1 \|M:G5\|M:G7\|M:G2\|M:W1\|M:W5A' h-mad/hooks/h-mad-codex-tdd-gate.py` | all present. `_relative_target(root: Path, raw: str, cwd: Any = None) -> tuple[Path, str] \| None`. `_targets(payload) -> tuple[str, list[str], str]`. `PATCH_TARGET` is used in `_targets` and in `--self-check` |
| `_project_root` returns | `ast` walk of `Return` nodes in the function (via `"$PY"`) | 4 |
| Safe-list and git refusal | import the Codex gate with `importlib.util.spec_from_file_location`; print `len(SAFE_HMAD_SCRIPT_OPTIONS)`, key membership, `_safe_shell_command("git rev-parse --absolute-git-dir", ".", ".")` | `10 False False` |
| `KINDS` and budget | import `h_mad_tdd_judge` | `11` kinds, `JUDGE_BUDGET_S` `40.0` |
| `_run_bounded` shape | `grep -n 'def _run_bounded\|_run_bounded(\|M:K3\|M:R5' h-mad/scripts/h_mad_tdd_judge.py` | the `def` returns a 5-tuple; unpacks in `resolve` (followed by `mapped = out.strip()  # M:R5` and `if timed_out:`) and in `judge` (followed by the `# M:K3` line). `resolve` has no `# M:K3` |
| priority tuple | `grep -n '"timeout", "pytest-missing"' h-mad/scripts/h_mad_tdd_judge.py` | 1 line in `judge` |
| resume parser | `grep -n 'def \|ArgumentParser\|add_argument' h-mad/scripts/h_mad_resume_decision.py` | no `build_parser`. The parser is built inside `main` with 5 `add_argument` calls. `CANNOT_JUDGE_WITHOUT_SESSION = "cannot_judge"` |
| New files absent | `test -e` on `h-mad/scripts/h_mad_target_identity.py`, `h-mad/tests/test_h_mad_target_identity.py`, `h-mad/tests/test_h_mad_tdd_gate_differential.py`, `h-mad/tests/mutation-specs/target_identity.json`, `h-mad/tests/mutation-specs/resume_decision_git_dir.json`, `docs/03-analysis/probes/tdd-gate-fail-opens`, `docs/03-analysis/tdd-gate-fail-opens.pending-mutation-specs` | all 7 absent |
| Existing tests named here | `grep -n -F 'def NAME'` for `_tree_b`, `test_claude_gate_kind`, `test_symlinked_hook_runs_its_own_trees_judge`, `test_trap_member_refuses_in_form`, `test_dd7_differential_matches_the_published_cells`, `test_outside_root_exemption_needs_both_spellings` (all in `h-mad/tests/test_h_mad_tdd_gate_judge.py`); `test_codex_gate_kind` (`h-mad/tests/test_h_mad_codex_tdd_gate_judge.py`); `test_run_bounded_kills_the_process_group`, `test_name_map_runs_under_the_budget`, `test_timeout_kind` (`h-mad/tests/test_h_mad_tdd_judge.py`); `test_codex_hook_allows_exact_safe_hmad_control_script`, `test_codex_hook_self_check_reports_machine_readable_pass` (`h-mad/tests/test_h_mad_codex_runtime.py`); `test_claims_section_fenced_lines`, `test_claims_lines_execute_across_invocations` (`h-mad/tests/test_host_runtime_docs.py`) | each 1 definition |
| Support helpers | `grep -n 'def decision\|def hermetic_env\|def sleeper\|def fake_venv' h-mad/tests/tdd_gate_support.py`; `grep -n 'def hermetic_env' h-mad/tests/conftest.py` | all present in `tdd_gate_support.py`; `conftest.py` has its own `hermetic_env` fixture |
| New helpers absent | `grep -c 'def assert_case_insensitive\|def detaching_sleeper' h-mad/tests/tdd_gate_support.py` | 0. Load-bearing: T1 and T5 add them |
| Mutation spec layout | read `root`, `command`, and the `H11`, `H6`, `H20B` objects of `h-mad/tests/mutation-specs/claude_gate_judge_wiring.json` | `"root": "../.."`. `H11` test `tests/test_h_mad_tdd_gate_judge.py::test_traversal_target_is_gated[absolute]`, `H6` test `tests/test_h_mad_tdd_gate_judge.py::test_exempt_write_on_unreadable_chain_is_allowed[state-file]`, `H20B` test `tests/test_h_mad_tdd_gate_judge.py::test_outside_root_exemption_needs_both_spellings[dotdot-relative]`. The claude spec's command runs `tests/test_h_mad_tdd_gate_judge.py` and `tests/test_h_mad_tdd_gate_docs.py`; the codex spec's runs `tests/test_h_mad_codex_tdd_gate_judge.py` and `tests/test_h_mad_codex_runtime.py`; `tdd_judge_scoring.json` runs `tests/test_h_mad_tdd_judge.py` |
| Adapter oracle lines | `grep -c -F 'h_mad_resume_decision.py'` on `h-mad/references/codex-runtime.md`, `grok-runtime.md`, `agy-runtime.md` and on `handoff/references/*-runtime.md` | 1 in each h-mad adapter; 0 in each handoff adapter. The claims tests parametrise over the h-mad adapters only (`HOST_ADAPTERS`) |
| Doc surfaces | `grep -n '^Hook:'` in `codex-implementer-prompt.md`; ``grep -n '^- `h_mad_tdd_judge.py` —'`` in `h-mad/SKILL.md`; `grep -n '^### Trust boundary'` in `codex-runtime.md` | 1 line each |
| Mutation harness | `grep -n 'ANCHORS_OK\|ALL_CAUGHT' h-mad/scripts/h_mad_mutation_harness.py` | tokens `MUTATION: ALL_CAUGHT` and `ANCHORS: ANCHORS_OK` with `drifted=` |
| Suite collection | `"$PY" -m pytest --collect-only -q -p no:cacheprovider h-mad/tests \| tail -1` | `4632 tests collected` |
| Hook interpreter | `head -1 h-mad/hooks/h-mad-tdd-gate.sh`; `/bin/bash --version \| head -1`; `grep -n 'subprocess.run(\[str(hook)\]' h-mad/tests/test_h_mad_tdd_gate_judge.py` | `#!/bin/bash`; `GNU bash, version 3.2.57(1)-release (arm64-apple-darwin26)`; 1 line: `_gate` runs the hook file directly, so its shebang interpreter runs it |
| Bash 3.2 forbidden constructs in the hook today | the five patterns of `test_claude_gate_is_bash_3_2_clean`, applied with `re.findall(..., re.M)` to the hook text; each also applied to all five fixture strings | 0 occurrences for each pattern in the hook; each pattern matches its own fixture and none of the other four. The zero is incidental (nothing has written such a construct yet); the rule and T3's test make it load-bearing |
| Nameref under `/bin/bash` 3.2 | a scratch script run by `/bin/bash`, deleted after the run | `local: -n: invalid option`, and the named variable stays empty. The `printf -v "$1"` form of `_pct_capture` returned each of the five value classes byte for byte |
| Script-path case in `_safe_shell_command` | import the Codex gate with `importlib.util.spec_from_file_location`; call `_safe_shell_command(f"python3 {p} challenge", root, str(root))` with `p` under `h-mad/scripts/` and under `h-mad/SCRIPTS/` | `scripts` gives `True`, `SCRIPTS` gives `False` (the path exists under both spellings; `Path.resolve` keeps `SCRIPTS`) |
| Interpreter probe | `command -v python3.11`; `python3.11 -c 'import sys,pytest;print(sys.version.split()[0],pytest.__version__)'`; the same import under `python3` | `python3.11` resolves to a 3.11.8 with pytest 9.1.1; `python3` raises `ModuleNotFoundError: No module named 'pytest'` |
| Empty header path under `PATCH_TARGET` | `PATCH_TARGET.findall` (the constant's pattern, copied) on `*** Begin Patch\n*** Update File: \n@@\n-a\n+b\n*** End Patch\n` | `[]`. The governed empty-target line of `_main_guarded` is `return _deny("H-MAD Phase 5 could not identify this write target; refusing fail-closed.")`, which carries no `kind=` |
| `_main_guarded` order | `grep -n 'root = _project_root(payload)\|phase5_status = _any_phase5_status(root)' h-mad/hooks/h-mad-codex-tdd-gate.py` | 2 lines, 349 and 351, with `tool, targets, command = _targets(payload)` between them |
| Option checks in `_safe_hmad_script` | `grep -c -F` of `if token.startswith("--") and token.split("=", 1)[0] not in allowed_options:` and of `if token.startswith("-") and not token.startswith("--"):` in the hook | 1 each. A scratch copy with the resume key added (six options) and each condition replaced by `False`, run through `_safe_shell_command` on the `--session-id-from-git-dir` oracle command, then deleted: landed `[True, False, False]` for (plain, `--bogus x`, `-h`); long check off `[True, True, False]`; single-dash check off `[True, False, True]` |
| Spec `command[0]` spellings | `json.load` each `h-mad/tests/mutation-specs/*.json` and print `command[0]` | 119 spec files: 110 write `python3.11`; 8 write the host's absolute anaconda `python` and 1 (`collect_report.json`) its absolute anaconda `python3.11`. The 8 include the three this feature adds rows to (`claude_gate_judge_wiring.json`, `codex_gate_judge_wiring.json`, `tdd_judge_scoring.json`). This feature does not change their `command`; see the Residuals |

## Version History
- v1.0: First draft (2026-09-29), Phase 5a, planned against design v1.2 (48d639f7), spec v1.4 (644f8bf6), plan v1.4 (1254595a); answers no audit cycle. Fourteen tasks: design T10 split into T10a (callee) and T10b (wiring) so the resume WIRE-PIN goes red for a caller reason. Design governs over plan v1.4 on comparator exit status and approved= field, the proc.wait remaining-grace reap, and file paths. 32 mutation rows: 26 over the 25 AC-7.1 guards, 6 connection rows.
- v1.1: Answers impl-plan audit round 1 (codex p1: 3 must, 1 should, 1 nit; agy p2: 3 must) (2026-09-29). Bash 3.2 rule for the Claude gate stated once, _pct_capture moved from a nameref to printf -v by name, new guard test_claude_gate_is_bash_3_2_clean (T3 now 23 functions, 16 RED, 7 guards); no absolute interpreter path in any command or new spec (PY probed per interpreter_has_pytest, new specs write python3.11); T10a asserts inclusion of the five options; T6 unfixed run overlays tdd_gate_support.py; T2 forced-script test observes _safe_shell_command's boolean; T10b forced guard asserts the recording git stub saw no call; _read_canon directory/file rule specified; T1 heading renamed. Tasks 14, wiring 3, mutation rows 32 unchanged.
- v1.2: Corrective revision, not re-audited (2026-09-29), answering docs/01-plan/features/tdd-gate-fail-opens.impl-plan.audit.v2.p1.md (codex: 3 must, 1 should; the agy p2 pass was hollow and disregarded). T0 gains control 3 (reading-invalid.txt with agent-cli-reachable=yes: non-zero exit, no COMPARE: token, both argument orders; RED recorded as COMPARE: PASS before the validity check). T4 gains test_codex_empty_header_path_is_judge_error and the trimmed-marker-equality rule that makes the empty path reachable (T4 now 10 functions, 7 RED, 3 guards). T11 gains post-registration mutation rows CX-OPT-LONG and CX-OPT-SHORT, each caught by its own case of test_codex_hook_refuses_unknown_resume_options, with a landed-mutation check (mutation rows 32 to 34: 26 AC-7.1, 6 connection, 2 post-registration). T2 specifies the _main_guarded arm-2 branch (not isinstance(root, Path)) before _any_phase5_status, scanning Path(root.component). Tasks 14, wiring 3, floor 25 unchanged.
