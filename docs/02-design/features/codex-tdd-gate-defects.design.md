# Design: codex-tdd-gate-defects

## Executive Summary

One new stdlib module, `h-mad/scripts/h_mad_tdd_judge.py`, holds the chain reader, the test
resolver, the interpreter selector and the summary scorer. The Codex gate imports it. The Claude
gate runs its CLI. The CLI has two verbs, `state` (one `TDD-STATE:` line) and `judge` (one
`TDD-JUDGE:` line). The Claude gate emits every refusal through one function, in the one form V-0
chose, and an `EXIT` trap routes every exit that nothing decided into that function.

## Overview

The design implements spec v1.2 FR-0…FR-8 and plan v1.2. OD-1…OD-9 are resolved as the spec
records them. Operator decisions: OD-8 refuses an unreadable chain `judge-error` in the chosen form.
OD-9 lets the Codex-authorship escape apply only when every ACTIVE record declares Codex unavailable.
The registry keeps its own `Production` grammar (D-A). Existing Claude-gate assertions migrate
according to the chosen form (D-B). V-0 never chooses `exit 1`: the form is (b) when
`FORM_B=BLOCKS`, otherwise (a) rc 2 (D-C).

The design owns these items, which the spec and plan left open:
- the judge's file name;
- the `TDD-STATE:` line format for `none`, `active` and `unreadable`;
- the `TDD-JUDGE:` field encoding;
- the time bound and its latency measurement;
- the `EXIT`-trap shape and the refusal function;
- the summary-line grammar;
- the shell-policy venv branch.

Some decisions here go beyond the spec's or the plan's wording. Each is marked **DD-n**, and
§"Supersedes the plan or the spec on" lists them.

## Supersedes the plan or the spec on

Each item names the document sentence it departs from, the reason, and the revert. The report
routes each item to its owner.

| DD | Departs from | Design | Why | Revert |
|---|---|---|---|---|
| DD-1 | Spec FR-6 order: governance first, then the exemptions | The Claude gate runs the exemptions and the `.py` filter **before** the `state` verb | Under the spec's order, an unreadable state file refuses every write, including an exempt `.json` write that would repair it. That is a deadlock the spec does not ask for. An exempt write is allowed under either order, so for every readable state the verdicts are identical | Swap the two blocks |
| DD-2 | Plan §"What we deliberately do not touch": the no-`jq` fail-open | The gate no longer reads state with `jq`, so the `jq` dependency and its "no `jq` → allow" path are removed | Spec FR-6 "Unchanged" names this case: "if the design removes that dependency, this path goes with it". Keeping a `command -v jq` allow with nothing left that uses `jq` would be a silent stand-down with no reason behind it | Restore the `command -v jq` check before the `state` call |
| DD-3 | Plan §"Two explicit branches" in `run_suite` | One predicate: a parsed summary that carries neither a `passed` nor a `failed` phrase stays `UNREADABLE no_summary` | The two-branch form covers `no tests ran` and errors-only summaries. It moves `3 skipped in …`, `5 deselected in …` and `1 xfailed in …` from `no_summary` to `no_tests_ran`, which breaks spec FR-4's "the one change" (measured below). The one predicate closes that axis | Two branches, and accept the three reason changes |
| DD-4 | Plan summary-line rule | SGR colour sequences are stripped before a line is matched, and the count words are a closed set | Measured: today `_suite_summary` reads a coloured `1 failed, 1 passed` as `(1, 0)`, which `run_suite` scores PASS. The plan's whole-line rule turns that reading into `UNREADABLE`. Stripping turns it into the correct `FAIL` | Drop the strip; coloured runs then read `no_summary` |
| DD-5 | Spec FR-4 classification (7 rules, no final else) | Rule 8: any other parsed summary (0 failed, 0 passed, 0 errors, not `no tests ran`, e.g. `3 skipped in …`) → `no-tests-ran` | The spec's list is not total. Without rule 8 a skipped-only run has no kind | None needed; this totalises the spec's list |
| DD-6 | Spec FR-3 "Shell policy": a contained venv interpreter passes the existing argv rules, "so only `python -m pytest …` and the H-MAD control allowlist pass" | The venv interpreter is admitted for `-m pytest …` only | The plan's expected softened set is exactly {contained venv} × {spellings} × {`-m pytest …`}. Admitting the control-script allowlist too would add softened rows that nobody asked for. Narrower than the spec's upper bound | Route the venv token through `_trusted_executable`'s existing argv rules |
| DD-7 | (not stated anywhere) | The Claude gate makes a relative target absolute against the project root before any check | Without this, `_resolve_state_file` resolves a relative target against the process cwd while the judge resolves it against the root, and the two disagree. Parity with the Codex gate's `_is_production_python`, which exempts `tests/x.py` given relative | Leave targets raw; the fast path and the judge then disagree on relative targets |
| DD-8 | (not stated; today an empty target with an ACTIVE record is allowed) | An empty target on a governed root is refused `judge-error` | OD-4's root cause is payload-shape drift. A payload the gate cannot read yields an empty target, which today is a silent allow. The Codex gate already refuses "could not identify this write target" | Allow on an empty target, as today |
| DD-9 | (not stated) | A Claude-gate target outside the project root has the root alone as its chain | A chain from outside the root is empty, so the target would read `none` and be allowed. Today the root-first reader governs it. This keeps today's refusal | Read `none` for an outside target |

## Architecture Overview

```
Codex host ──stdin JSON──▶ h-mad-codex-tdd-gate.py ──import──▶ h_mad_tdd_judge (core)
                              │ shell policy: _safe_shell_command ──▶ judge.venv_contained
                              └ per write target: judge.read_chain → judge.judge → _deny / allow

Claude host ─stdin JSON──▶ h-mad-tdd-gate.sh
                              ├ EXIT trap installed first (undecided exit → refusal)
                              ├ payload → target (tool_input.file_path | file_path | $1)
                              ├ _resolve_state_file fast path (no state file → allow)
                              ├ exemptions, .py filter                          [DD-1]
                              ├ python3 <hook-realpath>/../scripts/h_mad_tdd_judge.py state …  → TDD-STATE:
                              ├ Codex-authorship check (codex-escape= from TDD-STATE, env override, codex on PATH)
                              └ python3 …/h_mad_tdd_judge.py judge …  → TDD-JUDGE:  → _allow | _refuse

h_mad_tdd_judge ──import──▶ h_mad_wire_pin_gate._parse_tasks   (Production/Test fields, FR-2)
                ──import──▶ h_mad_audit_gate._suite_summary     (summary line, FR-4)
                ──subprocess──▶ bash h_mad_derive_test_path.sh  (name map, fallback)
                ──subprocess──▶ <interpreter> -m pytest <test> -x -q --no-header  (bounded)
```

Both hooks find the judge through their own resolved path. The Codex gate uses
`Path(__file__).resolve().parents[1] / "scripts"`. The Claude gate resolves `${BASH_SOURCE[0]}`
through `python3 os.path.realpath`. Neither hook uses `$HOME/.claude/skills` (plan layer 6, W6).

## Detailed Design

### D1 — The judge module: `h-mad/scripts/h_mad_tdd_judge.py` (FR-1)

- **Constraints.**
  - The module is stdlib only, has `from __future__ import annotations`, and imports under
    Python 3.9 (plan rule (i)).
  - At import it inserts its own resolved directory at `sys.path[0]` when that directory is
    absent, so `h_mad_wire_pin_gate` and `h_mad_audit_gate` resolve beside it whoever imports it.
  - `h_mad_wire_pin_gate` imports `h_mad_wire_registry` at module top, and that module imports
    `h_mad_audit_gate`. So the floor test covers four modules: the judge, `h_mad_wire_pin_gate`,
    `h_mad_wire_registry` and `h_mad_audit_gate`.
  - Premise: `/usr/bin/python3 -c 'import sys; sys.dont_write_bytecode=True; import h_mad_wire_pin_gate, h_mad_audit_gate, h_mad_wire_registry'`,
    run in `h-mad/scripts` at skills `1ef1a782`, printed `3.9.6 ok`.
- **Types** (`typing.NamedTuple`):
  - `Record(key: str, codex_status: str, state_file: Path)`. `codex_status` is the record's value,
    or `"available"` when it is absent or `null`. A non-string value is stringified.
  - `Chain(value: str, records: tuple, error_file: Optional[Path], error: str)`. `value` is one of
    `none`, `active` or `unreadable`.
  - `Verdict(decision: str, kind: str, reason: str, source: str, test: Optional[Path])`.
    `decision` is `ALLOW` or `DENY`. `source` is `impl-plan`, `name-map` or `""`.
- **Constants:**
  - `KINDS`: the 11 spec kinds, a frozenset;
  - `STATE_VALUES = ("none", "active", "unreadable")`;
  - `JUDGE_BUDGET_S = 40.0` (D6);
  - `ESCAPE_STATUSES = frozenset({"unavailable", "exhausted"})`.
- **Pure core.** `read_chain`, `resolve`, `select_interpreter`, `venv_contained`, `score` and
  `judge` raise only on programming errors. Every I/O failure becomes a `Chain` value or a
  `Verdict`.

### D2 — Chain reader `read_chain(root, target)` (FR-5, OD-3, OD-8)

- `root` is realpath'd. When `target` is `None`, the chain is `[root]`. Otherwise `d` is the
  realpath of the target's parent directory (`os.path.realpath` accepts a path that does not exist
  yet). If `d == root`, or `root` is an ancestor of `d`, the chain is `d, d.parent, …, root`.
  Otherwise the chain is `[root]` (DD-9).
- Each chain directory is read at `D/docs/.bkit-memory.json`. A path for which `os.path.lexists`
  is false is skipped.
  - Any other path is read with `read_text(encoding="utf-8")` and `json.loads`.
  - `OSError` (which covers a directory and a dangling symlink), `UnicodeDecodeError`, `ValueError`,
    a top level that is not an object, or an `orchestrator_state` that is present and not an object
    each end the walk: `Chain("unreadable", (), <file>, <exception class name, or "not-an-object">)`.
  - The first unreadable file decides. A readable step5 record elsewhere on the chain does not
    rescue it (FR-5: "any unreadable file on the chain means `unknown`").
- A record is ACTIVE when it is a dict whose `phase == "step5"`. Records are ordered nearest state
  file first, and in JSON key order within a file.
- Result: `Chain("active", records, None, "")` when any record is ACTIVE, else `Chain("none", …)`.
- **Residual.** The Claude fast path `_resolve_state_file` tests with `-f`. A dangling-symlink state
  file is therefore "no state" to the fast path, and the gate allows before the chain reader runs.
  That is today's fail-open, unchanged (spec Out-of-Scope: "no state").

### D3 — Resolution `resolve(root, target, records)` (FR-2)

1. **Plans.**
   - For each record, in chain order, the plan is `S/docs/01-plan/features/<key>.impl-plan.md`,
     where `S` is the record's state file's grandparent. Duplicate plan paths are read once.
   - A plan that is absent is recorded as `absent`. A plan that fails `OSError` or
     `UnicodeDecodeError` is recorded as `impl-plan unreadable: <class>`.
2. **Tasks.** `_parse_tasks(text)` (D5) gives each task's `production` and `tests` lists.
3. **Matching.**
   - The bases are the target's parent, then each ancestor up to and including `root`.
   - An entry `P` matches with base `B` when `os.path.realpath(B / P) == realpath(target)`. The first
     `B` that matches, nearest first, is the task's base.
   - A target outside `root` has no base and matches nothing.
4. **Candidates.** The candidates are the union of every matched task's `tests` entries, in plan
   order and then task order. Each entry resolves to `realpath(B / entry)`, and duplicates are
   dropped. A candidate that resolves outside `root` is dropped, and the drop is noted in any later
   DENY reason.
5. **Authority.**
   - If any task matched, the name map is not consulted.
   - If no candidate is a regular file, the verdict is `test-missing`. The reason names every
     candidate and says "author the failing test first".
   - The candidate run's cwd is that candidate's `B` (FR-4).
6. **Name map.** If no task matched, the judge calls the name map on the target's root-relative
   POSIX path:
   `subprocess.run(["bash", <scripts>/h_mad_derive_test_path.sh, rel], cwd=root, capture_output=True, text=True, timeout=<remaining budget>)`.
   - A non-empty stdout resolves against `root`. The candidate is that file, and its cwd is `root`.
   - If the file does not exist, the verdict is `test-missing`.
7. **Deny.** If neither source yields a path, the verdict is `no-test-resolved`. The reason names
   every plan path tried with its outcome (`matched none`, `absent` or `impl-plan unreadable: …`)
   and the literal name-map result (`name map: empty for <rel>` or `name map: target outside root`).

### D4 — Interpreter selection and venv containment (FR-3, OD-1)

- `select_interpreter(test, root, fallback)` walks from `test.parent` up to `root`, inclusive.
  - The first directory `D` for which `os.path.lexists(D/.venv/bin/python)` is the venv directory,
    and the judge never looks further.
  - When `venv_contained(D, root)` holds, the interpreter is the **unresolved**
    `str(D/.venv/bin/python)`, so that the venv's `sys.prefix` applies.
  - When it does not hold, the verdict is DENY `venv-escapes-root`. The reason names `D/.venv`
    and its realpath.
  - When no `D` is found, the interpreter is `fallback`: `sys.executable` for the Codex gate, and
    the `python3` that runs the CLI for the Claude gate.
- `venv_contained(D, root)` holds when all three of these hold:
  1. `realpath(D/.venv)` is inside `realpath(root)`;
  2. `realpath(D/.venv/bin)` is inside `realpath(root)`;
  3. `stat.S_ISREG(os.lstat(D/.venv/pyvenv.cfg).st_mode)` is true. A symlinked `pyvenv.cfg` fails
     this check, and so does a missing one.

  Where the interpreter's own last symlink hop leads is not checked (OD-1).
- The shell policy (D8) calls this same function. The containment rule has one implementation.
- **Premise.** `realpath` of HemaSuite's `hematology-paper-writer/.venv/bin/python` leaves the
  root (plan P9). At HemaSuite `3f0c9f3a`, `ls -l` shows `hematology-paper-writer/.venv/bin/python -> python3.14`.
- **Residuals** (spec FR-3):
  - `.venv/bin/pytest` is not an entry point;
  - `venv/` and `env/` are not discovered;
  - a contained venv whose `bin/python` points at an arbitrary binary is trusted.

### D5 — `_parse_tasks` extended in place (FR-2, OD-7)

- **New regex.** A new module-level regex sits beside `_FIELD_RE`, which is left byte-identical:

  ```python
  _PATHS_FIELD_RE = re.compile(
      r"^\s*(?:[-*•]\s+)?\*{0,2}\s*(?P<label>Production(?:\s+files?)?|Test(?:\s+files?)?)"
      r"\s*(?::\s*\*{0,2}|\*{0,2}\s*:)\s*(?P<value>.*)$",
      re.IGNORECASE,
  )
  _PY_TOKEN_RE = re.compile(r"`([^`]+\.py)`")
  _NONE_VALUE_RE = re.compile(r"^[\s*_`]*none(?![\w/-]|\.\w)", re.IGNORECASE)
  ```

- **Task dict.** Each task dict gains `"production": []` and `"tests": []`.
- **Loop.** Inside the per-line loop, `_PATHS_FIELD_RE` is tried only when `_FIELD_RE` did not
  match. The two label sets are disjoint, so no existing field changes.
- **Values.**
  - A `none` value contributes nothing.
  - Otherwise every `_PY_TOKEN_RE` match is appended, to `production` when the label starts with
    `production`, and to `tests` otherwise.
  - Several label lines in one task accumulate.
- **Label axis, as the spec states it.**
  - `**Test file**:`, `**Test:**`, `Production files:`, and so on.
  - `Tests` with no `file` is not read: the label `Test` must be followed by the colon or by `**:`.
- **Controls executed at skills `1ef1a782`**, by a scratch script, since deleted:
  - `_NONE_VALUE_RE` matches `` none (writes `docs/x/derive_readings.py`) ``, `**none** — x`,
    `None.` and `none`.
  - It does not match `` `none.py` ``, `` `tools/a.py` ``, ``nonexistent `a.py` `` or
    ``none/`a.py` ``.
  - The first draft, `^\W*none\b`, matched `` `none.py` ``. The lookahead is there because that
    control failed.
- **Replay on the incident's plan.** The same scratch parser, with `_TASK_RE` imported from the
  tree, was run on HemaSuite's `review-manifest-guideline-evidence.impl-plan.md` at `1fbf8022` and
  at `31bfcfe4`. Both times it put `tools/review_round/guideline_excerpts.py` in `Task 7`'s
  `production`, with `tests` equal to the four entries plan P11 lists, in that order.
- **Residuals** (spec FR-2), plus two measured here:
  - A `` `path.py::symbol` `` token is not an entry, because it does not end in `.py`.
  - A label with a parenthesised qualifier (`**Production files** (…):`) is not read.
  - Reading at skills `1ef1a782` / HemaSuite `3f0c9f3a`, over the 83 tracked, non-`archive/`
    `*.impl-plan.md` files:
    - 2 label lines carry a `.py::` token. Both are `Production` lines. One of them has no plain
      `.py` token and so contributes no entry: `` `engine/manuscript_orchestrator.py::run_manuscript` ``.
    - 1 real parenthesised label line exists, and its value is markdown with no `.py`.
  - Both residuals fail closed: the write falls to the name map, or to `no-test-resolved`.
  - Command: the scratch parser above over `git -C <repo> ls-files '*.impl-plan.md'` minus
    `archive/`. The committed probe is owed under `docs/03-analysis/probes/codex-tdd-gate-defects/`.

### D6 — Running pytest and the time bound (FR-4, NFR Performance)

- **The command** is the spec's, exactly: `[interpreter, "-m", "pytest", str(test), "-x", "-q", "--no-header"]`.
  Its cwd is the candidate's base (D3). stdout and stderr are both captured.
- **One budget per judge call.** `JUDGE_BUDGET_S = 40.0` covers every subprocess one `judge()` call
  starts: the name map and every candidate run. Each run's timeout is the remaining budget. When
  the remaining budget is ≤ 0 before a run, the verdict is `timeout` without starting it.
- **Process-group kill.** Each run is started with
  `subprocess.Popen(..., start_new_session=True)` and read with `communicate(timeout=remaining)`. On
  `TimeoutExpired` the judge calls `os.killpg(proc.pid, SIGKILL)` and then `communicate()`, and the
  verdict is `timeout`.
  - Executed at skills `1ef1a782` under `/usr/bin/python3` 3.9.6, with a `/bin/sh` shim running
    `sleep 7.3x; echo done`:
    - `subprocess.run(timeout=1)` returned after 1.0 s and left the `sleep` alive (`pgrep -f` → 1
      survivor);
    - `Popen(start_new_session=True)` plus `killpg` returned after 1.0 s with 0 survivors.
  - The probe was deleted, and the leftover `sleep` was killed.
  - A timed-out pytest whose children survive can go on writing into the tree after the gate has
    decided. That is why the kill is by process group.
- **Latency (NFR).**
  - The measurement ran in the HemaSuite checkout (its HEAD `3f0c9f3a`, a HemaSuite commit), from
    `hematology-paper-writer/`, with
    `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest <file> -x -q --no-header -p no:cacheprovider`
    timed by `time.monotonic()` in a wrapper.
  - `tests/test_certificate_lock_removed.py`, three runs: 1.83 s, 1.83 s and 1.87 s wall. Each
    read `9 passed, 1 warning in 1.09s`.
  - All four Task 7 candidates in plan order: 1.90 s + 1.66 s + 6.98 s + 2.39 s = 12.93 s. That is
    the GREEN-deny worst case, because every candidate runs.
  - HemaSuite's `git status --porcelain | shasum` read the same before and after.
  - `-p no:cacheprovider` was added only to keep the measurement read-only. The judge's own command
    omits it (spec FR-4).
  - Judge start-up and parsing are not in these figures, because no judge exists yet. The 5g
    reading re-measures through the judge.
- **The bound's value.** 40 s is 3.1× the measured worst case.
  - The Claude Code command-hook default timeout is **not measured here** (the installed
    registration sets none: `~/.claude/settings.json` PreToolUse `Write|Edit` →
    `{'type': 'command', 'command': '$HOME/.claude/hooks/h-mad-tdd-gate.sh'}`).
  - No Codex hook timeout is documented in `h-mad/references/codex-runtime.md`.
  - If a host kills the hook before 40 s, the host's own timeout behaviour decides the write, and
    this design cannot bound that. This is an open risk, OQ-D1.
- **Portable time bounds.** The bound is `communicate(timeout=…)` in Python. No `timeout` or
  `gtimeout` CLI is used.

### D7 — Summary scoring: `_suite_summary` extended in place, and the classifier (FR-4, OD-7)

- **Parser.** `h_mad_audit_gate._suite_summary(text)` now returns
  `SuiteSummary(passed, failed, errors, no_tests_ran, words)` (a `NamedTuple`, where `words` is a
  `frozenset` of the phrase words seen), or `None`.
  - There is no second summary parser, and `_SUITE_RE` is removed. Premise:
    `git grep -n "_suite_summary" -- h-mad handoff ':!h-mad/tests/fixtures'` → 2 matching lines,
    both in `h_mad_audit_gate.py` (the definition and `run_suite`'s call). No test calls it
    directly.
- **Summary-line grammar** (plan's rule, closed):
  - Each line of `stdout + stderr` has SGR sequences (`\x1b\[[0-9;]*m`) removed, then surrounding
    whitespace, then `=` padding.
  - A summary line then matches
    `^(?:(?P<ph>\d+ W(?:, \d+ W)*)|no tests ran)(?P<timed> in \d+(?:\.\d+)?s(?: \(\d+:\d{2}:\d{2}\))?)?$`,
    where `W` is the closed word set `passed|failed|error|errors|skipped|deselected|xfailed|xpassed|warning|warnings|rerun`.
  - A timed line beats an untimed one, and within each kind the last line wins.
  - A count phrase inside a longer line is never read.
- **Grammar executed at skills `1ef1a782`**, by an inline `/usr/bin/python3` heredoc (nothing was
  written). Readings, as (passed, failed, errors, no_tests_ran):
  - `1 failed in 0.01s` → (0,1,0,F);
  - `1 error in 0.06s` → (0,0,1,F);
  - `no tests ran in 0.00s` → (0,0,0,T);
  - `2 passed in 0.1s` followed by a line `1 failed` → (2,0,0,F);
  - untimed `1 failed, 8 passed` → (8,1,0,F);
  - the coloured line below → (1,1,0,F);
  - `9 passed, 1 warning in 1.09s` → (9,0,0,F);
  - `==== 1 failed, 2 passed in 65.20s (0:01:05) ====` → (2,1,0,F);
  - `1 xfailed in 0.1s` → (0,0,0,F);
  - `collected 0 items`, `E   assert '1 failed' in x`, `3 apples in 0.1s` and
    `FAILED t.py::a - 1 failed` → None.
- **The coloured line** (DD-4) is pytest 9.1.1's `--color=yes` summary for one failing and one
  passing test, captured with `od -c`:
  `\x1b[31m\x1b[31m\x1b[1m1 failed\x1b[0m, \x1b[32m1 passed\x1b[0m\x1b[31m in 0.04s\x1b[0m\x1b[0m`.
  Today's `_suite_summary` on those bytes → `(1, 0)`, which `run_suite` scores PASS.
- **`run_suite`.** The anchored lines keep their bytes.
  - `passed, failed = summary` becomes `passed, failed = summary.passed, summary.failed`.
  - Between the `summary is None` return and `if passed == 0 and failed == 0:`, one predicate is
    added (DD-3). Its dict keys are ordered so that the line is not byte-identical to
    `audit_suite_gate.json`'s anchored `no_summary` return:

    ```python
    if not ({"passed", "failed"} & summary.words):
        return {"reason": "no_summary", "verdict": "UNREADABLE", "rc": run.returncode}
    ```
- **Today's readings for DD-3's population**, taken by calling today's `_suite_summary` under
  `/usr/bin/python3` at skills `1ef1a782`: `3 skipped in 0.1s`, `5 deselected in 0.1s`,
  `1 xfailed in 0.1s`, `1 error in 0.06s` and `no tests ran in 0.00s` each → `None`, so each scores
  `UNREADABLE no_summary`. After the change each still scores `no_summary`.
- **The table.** The plan's nine-row table holds cell by cell, and the coloured row is added:

  | Stub prints | `run_suite` today | after |
  |---|---|---|
  | coloured `1 failed, 1 passed in 0.04s` | PASS | **FAIL** |
  | `3 skipped in 0.1s` | UNREADABLE `no_summary` | UNREADABLE `no_summary` |

  The first row is a verdict change outside spec FR-4's "one change". It is owed to the spec (see
  the report). It moves PASS to FAIL, so it blocks where today allows, and no stamp flips toward
  PASS.
- **Judge classifier** `score(proc_output, timed_out)`, first match wins:
  1. `timed_out` → `timeout`.
  2. Some whole line, after stripping, ends with `: No module named pytest`. That is the unquoted
     `-m` form, measured as
     `/Applications/Xcode.app/Contents/Developer/usr/bin/python3: No module named pytest`, rc 1.
     → `pytest-missing`.
  3. `_suite_summary` is `None` → `no-summary`.
  4. `no_tests_ran` → `no-tests-ran`.
  5. `errors ≥ 1` → `pytest-error`. The reason contains "import" and "inside the test body"
     (AC-4.6).
  6. `failed ≥ 1` → `red-measured`.
  7. `passed ≥ 1` → `test-passing`.
  8. Otherwise → `no-tests-ran` (DD-5).

  The rc appears in the reason only.
- **Residual of rule 2.** A RED test whose output holds a whole line ending
  `: No module named pytest` is denied `pytest-missing`. That is a false deny, and it fails closed.
- **Several candidates** (spec FR-2 rule 4). Candidates run in order.
  - The first `red-measured` returns ALLOW, naming that test.
  - `venv-escapes-root`, `timeout` and `pytest-missing` return DENY at once: the next candidate
    would run under the same interpreter, or with less budget.
  - Otherwise every candidate runs. The DENY kind is the first of `pytest-error`, `no-summary`,
    `no-tests-ran` and `test-passing`, in that precedence, that any candidate produced. The reason
    names every candidate with its kind and its summary line (AC-2.4).

### D8 — Codex gate changes (`h-mad/hooks/h-mad-codex-tdd-gate.py`; FR-3, FR-5)

- **Removed:** `_target_phase5_status`, `_derived_test` and `_test_exit`. `_state_status` and
  `_any_phase5_status` are unchanged (spec FR-5).
- **Loading the judge.** `_load_judge()` inserts `Path(__file__).resolve().parents[1] / "scripts"`
  at `sys.path[0]`, then `import h_mad_tdd_judge`. It is called lazily, the first time the main path
  needs the judge, and never when `_any_phase5_status(root) == "inactive"`. So a broken judge
  cannot affect a project with no step5 record, which matches the Claude fast path.
- **`_relative_target(root, raw, cwd=None)`** (OD-2).
  - An absolute `raw` resolves as today.
  - A relative `raw` resolves against `Path(cwd).expanduser().resolve()` when `cwd` is given, is a
    directory, and equals `root` or lies below it. Otherwise it resolves against `root`.
  - `main` passes `payload.get("cwd")`, never the process cwd, so
    `test_codex_hook_resolves_git_root_from_nested_cwd` (no payload `cwd`, process cwd nested)
    still resolves against the root.
- **Per target.**
  1. `chain = judge.read_chain(root, absolute)`.
  2. `unreadable` → `_deny("H-MAD state governing this write is unreadable (<file>: <error>); refusing fail-closed. kind=judge-error")`.
  3. `none` → continue.
  4. `active` and `_is_production_python(relative)` → `verdict = judge.judge(root, absolute, chain.records)`.
  5. `DENY` → `_deny(f"H-MAD Phase 5 requires a failing test before {relative}: kind={kind}; {reason}")`.
     `relative` is root-relative, so AC-5.1's deny names `hematology-paper-writer/tools/review_round/guideline_excerpts.py`.
- **Crash guard** (AC-5.4). The whole body of `main` after `--self-check` sits inside
  `try: … except Exception as exc: return _deny(f"H-MAD Phase 5 gate raised {type(exc).__name__}: {exc}; refusing fail-closed. kind=judge-error")`.
  `_deny` prints JSON and returns 0.
- **Shell policy** (DD-6). New helper `_contained_venv_python(token, root, cwd) -> bool`.
  - `p = os.path.normpath(os.path.join(base, os.path.expanduser(token)))`. `base` is the payload
    `cwd` when it is inside `root`, else `root`. An absolute `token` ignores `base`.
  - Every one of these must hold:
    - `token` contains `/`;
    - `Path(p).name.startswith("python")`;
    - `Path(p).parent.name == "bin"`;
    - `Path(p).parent.parent.name == ".venv"`;
    - `Path(p).is_file()`;
    - `h_mad_tdd_judge.venv_contained(Path(p).parent.parent.parent, root)`.
  - `_safe_shell_command(command, root=None, cwd=None)` gains one early branch, after the
    `SIMPLE_SHELL_COMMAND` and leading-assignment checks and before `_trusted_executable`:
    `if root is not None and argv[1:3] == ["-m", "pytest"] and _contained_venv_python(argv[0], root, cwd): return True`.
  - `_trusted_executable` and every other branch are unchanged, and `--self-check` passes
    `root=None`, so the branch is inert there.
  - `-c`, `-m pip` and a script argv under a venv token fall through to `_trusted_executable`,
    which rejects the venv path as today, because its parent is not in `TRUSTED_BIN_DIRS`.
- **Differential.** The plan's corpus (§"Guard narrowing: shell policy") is crossed in full. One
  argv row is added: `h_mad_state_write.py <root>/docs/.bkit-memory.json` under a venv token, which
  is expected unchanged (deny) and proves DD-6's narrowing. The fixture tree is D12's.

### D9 — Claude gate (`h-mad/hooks/h-mad-tdd-gate.sh`; FR-6, OD-4, OD-5, OD-8, OD-9)

The gate is rewritten top to bottom. The shebang stays `#!/bin/bash`, and it must run under
`/bin/bash` 3.2.57. Every construct below was executed under `/bin/bash` 3.2.57 at skills
`1ef1a782` by a scratch script, since deleted:
- the JSON escaper round-trips `a "q" \ back<TAB>tab<LF>nl` through
  `python3 json.load` as `'a "q" \\ back tab nl'`;
- `[[ $L =~ $re ]]` with `BASH_REMATCH` accepts a valid DENY line and rejects `kind=bogus`;
- `*$'\n'*` detects a second line;
- `set -f` word splitting counts two `record=` fields;
- an `EXIT` trap turns an errexit from `X=$(exit 3)` into the trap's `exit 2`, and the final rc is
  2.

**Order of the script:**

1. **Start-up.** `set -euo pipefail`, then `readonly REFUSAL_FORM=<a|b>`, then `DECIDED=""`, then
   `trap _on_exit EXIT`.
   - `REFUSAL_FORM` is a literal, written at implementation from V-0's `CHOSEN=`. It is not read
     from the environment (NFR: no knob).
   - The trap is installed before the first fallible command.
2. **Target.** From `$1`, else from stdin JSON via the existing `python3` snippet (`|| true`),
   reading `tool_input.file_path`, then `file_path`, then `path` (OD-4).
3. **Absolute target** (DD-7). `ROOT_ABS=$(cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null && pwd -P) || ROOT_ABS=""`.
   A non-empty relative `TARGET_PATH` becomes `$ROOT_ABS/$TARGET_PATH` when `ROOT_ABS` is
   non-empty. This is string work only.
4. **Fast path.** `STATE_FILE=$(_resolve_state_file "$TARGET_PATH" || true)`, then
   `[ -f "$STATE_FILE" ] || _allow`. `_resolve_state_file` is unchanged. Its answer is used for
   existence only.
5. **Empty target** (DD-8). If `TARGET_PATH` is empty, the gate runs `_find_judge` (step 7), then
   calls `state` with no `--target`, and reads the line as step 8 does: `active` or
   `unreadable` → `_refuse judge-error "could not identify the write target"`, and `none` →
   `_allow`.
6. **Exemptions and the `.py` filter** (DD-1). Both `case` blocks keep their exact patterns, then
   `[[ "$TARGET_PATH" != *.py ]] && _allow`. No `python3` process is started for an exempt write.
7. **Judge path.** `_find_judge` sets
   `JUDGE=$(python3 -c 'import os,sys;print(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[1]))),"scripts","h_mad_tdd_judge.py"))' "${BASH_SOURCE[0]}")`,
   unless step 5 already set it. A failure here is an errexit, and the trap turns it into
   `judge-error`.
8. **Governance.** `SOUT=$(python3 "$JUDGE" state --root "$ROOT_ABS" --target "$TARGET_PATH" 2>/dev/null) || SRC=$?`.
   - Any non-zero `SRC`, zero lines, more than one line, or a line matching no `TDD-STATE:` form
     (D10) → `_refuse judge-error`.
   - `none` → `_allow`.
   - `unreadable` → `_refuse judge-error "H-MAD state is unreadable (<file>: <error>)"` (OD-8,
     AC-6.9).
   - `active` → continue.
9. **Codex authorship** (OD-9). Under `set -f`, the gate reads `codex-escape=` and the first
   `record=` whose status field is not `unavailable` or `exhausted`: the blocker, which names
   `--feature` and the state file in the hint.
   - If `HMAD_CODEX_UNAVAILABLE` is empty, `codex-escape=no`, and `command -v codex` succeeds, the
     gate emits `_refuse codex-authorship "<today's five-line message, with the blocker's key and state file>"`.
10. **Judge.** `JOUT=$(python3 "$JUDGE" judge --root "$ROOT_ABS" --target "$TARGET_PATH" 2>/dev/null) || JRC=$?`.
    - `JRC == 0` and `JOUT` a well-formed ALLOW line → `_allow`.
    - A well-formed DENY line → `_refuse <kind> <reason>`.
    - Anything else, **including a well-formed ALLOW with a non-zero rc**, → `_refuse judge-error`
      (AC-1.3).
11. **End.** The script's last line is `_refuse judge-error "gate fell through without a decision"`.
    It is unreachable by construction, and it exists so that falling off the end can never read as
    an allow.

**Functions:**

- `_allow` → `DECIDED=allow; exit 0`.
- `_refuse <kind> <text>` does four things:
  - it builds `MSG="[H-MAD-TDD-GATE] BLOCK kind=<kind>: <text>"`;
  - it prints `MSG` to stderr;
  - under `REFUSAL_FORM=b` it prints
    `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":<json-string of MSG>}}`
    to stdout as `printf … || exit 2`, then sets `DECIDED=refused` and exits 0. So
    `DECIDED=refused` is recorded only after the JSON was written;
  - under `a` it sets `DECIDED=refused` and exits 2.
- `_json_str` escapes `\`, then `"`, then maps `[[:cntrl:]]` to a space. Newlines in the
  Codex-authorship message become spaces inside the JSON, and stderr keeps them.
- `_on_exit` is the trap:
  - it captures `rc=$?`, runs `trap - EXIT`, and runs `set +euo pipefail`;
  - `DECIDED=allow` → `exit 0`;
  - `DECIDED=refused` → `exit $rc`, which is the form's own status;
  - anything else is an exit nobody chose. The trap calls `_refuse judge-error "gate exited rc=$rc before deciding"`.
    Under (b), if that `printf` itself fails, the trap falls back to `exit 2`, the form that
    `FORM_A=BLOCKS` proves on both conclusive readings.
- **Residual.** A signal that kills `bash`, and a parse error before the trap is installed (plan
  layer 6). The only exit outside the chosen form is the (b)-to-`exit 2` fallback, taken only when
  stdout cannot be written.

**What leaves the gate:**
- the `jq` dependency and the no-`jq` allow (DD-2);
- the `ACTIVE`/`head -1` read;
- `CODEX_STATUS` from `jq`;
- `DERIVE_SCRIPT` and every `h_mad_derive_test_path.sh` reference (AC-1.1);
- the bare `pytest` run and its `[ -f "$TARGET_PATH" ]` guard (OD-5, AC-6.4);
- every `exit 1`.

5g greps, unit matching lines:
- `grep -c '^\s*exit 1\s*$'` → 0;
- `grep -c 'orchestrator_state'` → 0;
- `git grep -n "h_mad_derive_test_path.sh" -- h-mad/hooks` → no match.

### D10 — Line formats (FR-1; the `TDD-STATE:` format the spec owes)

- **Field encoding.** Every variable field value is `urllib.parse.quote(value, safe="/._-")`, so a
  value holds no space, comma, `=` or glob character. `~` stays unquoted, because it is always safe
  in `quote`, and a word produced by an expansion is never tilde-expanded. Paths are root-relative
  POSIX when inside the root, else absolute.
- **`state` verb** (`h_mad_tdd_judge.py state --root <dir> [--target <path>]`), exactly one line on
  stdout, rc 0:

  | Value | Line |
  |---|---|
  | none | `TDD-STATE: none` |
  | active | `TDD-STATE: active codex-escape=<yes\|no> records=<N> record=<key>,<codex_status>,<state-file>` … (N `record=` fields, chain order) |
  | unreadable | `TDD-STATE: unreadable file=<state-file> error=<exception class name \| not-an-object>` |

  - `codex-escape=yes` holds exactly when N ≥ 1 and every record's `codex_status` is in
    `ESCAPE_STATUSES` (OD-9). The rule has one implementation, in the judge.
  - An exception in the verb prints nothing to stdout, prints a message to stderr, and exits 2.
- **`judge` verb** (same arguments), exactly one line, rc 0:
  - `TDD-JUDGE: ALLOW kind=red-measured source=<impl-plan|name-map> test=<quoted repo-relative path>`;
  - `TDD-JUDGE: DENY kind=<kind> reason=<text>`.

  The reason text has `[[:cntrl:]]` mapped to spaces, so it is one line.
  - If the chain is not `active` at judge time, the verdict is DENY `judge-error`.
  - Any exception is caught and printed as DENY `judge-error` with `reason=<class>: <message>`.
- **Grammar the Claude gate enforces** (bash ERE, whole line):
  - `^TDD-STATE: none$`
  - `^TDD-STATE: unreadable file=[^ ]+ error=[A-Za-z_-][A-Za-z0-9_-]*$`
  - `^TDD-STATE: active codex-escape=(yes|no) records=([1-9][0-9]*)( record=[^ ,]+,[^ ,]+,[^ ,]+)+$`,
    and the count of `record=` words must equal `records=`.
  - `^TDD-JUDGE: ALLOW kind=red-measured source=(impl-plan|name-map) test=[^ ]+$`
  - `^TDD-JUDGE: DENY kind=(no-test-resolved|test-missing|venv-escapes-root|pytest-missing|pytest-error|no-tests-ran|no-summary|test-passing|timeout|judge-error) reason=(.+)$`

  Anything else is `judge-error`. That includes an unknown verb's usage error, which argparse
  reports on stderr with rc 2.
- **Extension point.** A later field is appended to `record=` as a fourth comma field. The gate's
  ERE must then change with it, because the line is a closed grammar and not a key bag.

### D11 — Documentation (FR-7)

Each span is located by heading or by line prefix, never by line number:

- **`h-mad/references/codex-runtime.md` §"Trust boundary".** Add a paragraph stating:
  - the nearest `.venv` from the test file up to the root;
  - `realpath` containment of `.venv` and `.venv/bin`, plus a regular `pyvenv.cfg`;
  - DENY `venv-escapes-root` when containment fails;
  - the residuals;
  - that the verdict is scored on pytest's summary line, never rc.
- **`h-mad/SKILL.md`, the registry.** Under §"Helper scripts (all in `~/.claude/skills/h-mad/scripts/`)",
  a new bullet registers `h_mad_tdd_judge.py`, beside `h_mad_derive_test_path.sh`. The bullet
  states the two verbs, their tokens, and that a copied (not symlinked) Claude hook finds no judge
  and refuses `judge-error`.
- **`h-mad/SKILL.md`, the gate bullets.** Every line naming `hooks/h-mad-tdd-gate.sh` is re-read.
  `grep -c 'hooks/h-mad-tdd-gate.sh' h-mad/SKILL.md` → 4 matching lines at `1ef1a782`:
  - the `HOOK_NOT_INSTALLED` table row;
  - the "`Write|Edit` PreToolUse hook" bullet;
  - the `HMAD_CODEX_UNAVAILABLE=1` paragraph;
  - the "reads the **same** `codex_status` for whichever feature is in `step5`" bullet.

  The last one gains the OD-9 rule: with several ACTIVE records on the chain, every one must
  declare it.
- **`h-mad/references/agy-runtime.md` §"The TDD gate".** The sentence "is written to Claude Code's
  exit-code protocol" is replaced by the chosen form: rc 2 on stderr for (a), or a
  `permissionDecision` JSON deny on rc 0 for (b).
- **`h-mad/references/codex-implementer-prompt.md`, the bullets under the line beginning
  `Hook: PreToolUse hook at`.**
  - The production bullet reads: the test named by the impl-plan Task, else the name map, and
    "failing" means pytest's summary shows `N failed`.
  - The test bullet names the basename rule (`test_*.py`, `*_test.py`, `conftest*.py`).
- **`h-mad/scripts/h_mad_derive_test_path.sh`'s header comment.** It says it is "Used by
  ~/.claude/hooks/h-mad-tdd-gate.sh", which goes false. It becomes "Used by h_mad_tdd_judge.py".
  This site is in the plan's stale-prose census (2 matching lines in that file) and is not in the
  spec's three-file list.
- **Residual** (spec FR-7). Prose that describes the gate without naming a file is not covered.

### D12 — Fixture tree for the shell-policy differential and the venv ACs

- `tmp/root` is `git init`'d. `root/docs/.bkit-memory.json` holds one step5 record.
- `root/hematology-paper-writer/.venv/` is made by `python -m venv --without-pip`, so its
  `bin/python` is a real venv link and `pyvenv.cfg` is real.
- Next to it sits `bin/python-evil`, an executable regular file.
- `root/hematology-paper-writer/tests/test_x.py` is RED.
- `tmp/outside-venv/` is a second venv outside the root.
- Each venv-state row mutates a copy of this tree:
  - `.venv` → symlink to `outside-venv`;
  - `.venv/bin` → symlink out;
  - `pyvenv.cfg` removed;
  - `pyvenv.cfg` replaced by a symlink.
- The `realpath` check (plan: "a fixture asserts that `realpath` follows each symlink … as the rule
  assumes") runs `os.path.realpath` on each mutated path and asserts that it leaves the root.

## Components Changed / Added

| Component | File path | Change type | Purpose |
|---|---|---|---|
| Judge | `h-mad/scripts/h_mad_tdd_judge.py` | new | chain reader, resolver, interpreter selection, scorer, `state`/`judge` CLI (D1–D7, D10) |
| Codex gate | `h-mad/hooks/h-mad-codex-tdd-gate.py` | modify | lazy judge import, crash guard, `cwd` base, chain reader, venv shell branch (D8) |
| Claude gate | `h-mad/hooks/h-mad-tdd-gate.sh` | modify (rewrite) | payload, fast path, `state`/`judge` calls, refusal function, `EXIT` trap (D9) |
| Task parser | `h-mad/scripts/h_mad_wire_pin_gate.py` | modify | `_parse_tasks` gains `production`/`tests` (D5) |
| Summary scorer | `h-mad/scripts/h_mad_audit_gate.py` | modify | `_suite_summary` → `SuiteSummary`; `run_suite` predicate (D7) |
| Name map | `h-mad/scripts/h_mad_derive_test_path.sh` | modify (comment only) | header names its new caller (D11) |
| Registry | `h-mad/scripts/h_mad_wire_registry.py` | none | D-A; no diff against the base (AC-2.9) |
| Docs | `h-mad/references/codex-runtime.md`, `h-mad/SKILL.md`, `h-mad/references/agy-runtime.md`, `h-mad/references/codex-implementer-prompt.md` | modify | D11 |
| Tests | see §"Test Plan" | new / modify | ACs, wires, trap members |
| Mutation specs | `h-mad/tests/mutation-specs/` | new; `audit_suite_gate.json` re-checked | FR-8 (§"Test Strategy") |
| Probes | `docs/03-analysis/probes/codex-tdd-gate-defects/` | new (orchestrator, step P0) | plan P0; D5's grammar probe and D6's latency probe are owed there too |

## Implementation Order

1. **P0 and V-0** (orchestrator, plan §"Convention Prerequisites"). Commit the probes and run V-0.
   The FR-6 form task (step 6) does not start until V-0 reads conclusively.
2. **`_suite_summary` / `run_suite`** (D7). The run_suite table tests, AC-4.7, and
   `--check-anchors` in the same commit.
3. **`_parse_tasks` fields** (D5). AC-2.2, AC-2.3, and AC-2.9's corpus differential.
4. **Judge core and CLI** (D1–D4, D6, D7 classifier, D10). AC-2.1, AC-2.4–2.8, AC-3.1–3.3,
   AC-4.1–4.6, the CLI grammar tests, and the 3.9 floor.
5. **Codex gate** (D8). AC-1.2 (Codex half), AC-3.4, AC-3.5, AC-5.1–5.4, the differential, and W1
   and W5a.
6. **Claude gate** (D9), in the worktree only.
   - First the two `HOOK` constants move to `Path(__file__).resolve().parents[1] / "hooks" / "h-mad-tdd-gate.sh"`.
   - Then the payload, the `state`/`judge` calls and the trap.
   - Then `REFUSAL_FORM` from V-0's `CHOSEN=`, and the AC-6.2 migration for that form.
   - Tests: AC-1.2 (Claude half), AC-1.3, AC-6.1–6.10, the trap members, and W2, W5b and W6.
7. **Docs** (D11) and the AC-7 doc test.
8. **Mutation specs** (FR-8), run and scored on the pytest summary.
9. **5g.**
   - V-1r → `VERDICT=PASS fails=0/6`.
   - `reproduce.py`'s post-merge reading.
   - The node-id floor and the top-level-statement diff (plan Success Criteria).
   - `ANCHORS_OK drifted=0`.
   - `--self-check` PASS.
   - The stale-prose re-read.
   - The judge latency re-measured through the judge on the Task 7 file.

## Data Model / Schema Changes

- **State file** (`docs/.bkit-memory.json`): no schema change. The judge reads
  `orchestrator_state.<key>.phase` and `.codex_status`.
- **`_parse_tasks` task dict:** `+ "production": list[str]`, `+ "tests": list[str]`.
  - Existing keys are unchanged.
  - Consumers are listed by
    `git grep -n "_parse_tasks" -- h-mad handoff ':!h-mad/tests/fixtures' | grep -v '^h-mad/scripts/h_mad_wire_pin_gate.py'`,
    which gives `h_mad_assemble_tdd.py` (2 matching lines), `h_mad_wire_registry.py` (2) and a
    `SKILL.md` prose line (1). Both code consumers read named keys.
- **`h_mad_audit_gate.SuiteSummary(passed: int, failed: int, errors: int, no_tests_ran: bool, words: FrozenSet[str])`**:
  the return of `_suite_summary`, replacing `tuple[int, int]`.
- **Wire formats:** the `TDD-STATE:` and `TDD-JUDGE:` lines (D10).

## API / Interface Changes

- **`h_mad_tdd_judge` (new):**
  - `read_chain(root: Path, target: Optional[Path]) -> Chain`
  - `resolve(root: Path, target: Path, records: Sequence[Record]) -> Resolution`
  - `venv_contained(venv_parent: Path, root: Path) -> bool`
  - `select_interpreter(test: Path, root: Path, fallback: str) -> Union[str, Verdict]`
  - `judge(root: Path, target: Path, records: Sequence[Record], *, budget_s: float = JUDGE_BUDGET_S, fallback_interpreter: str = sys.executable) -> Verdict`
  - `format_state_line(chain: Chain, root: Path) -> str`
  - `format_verdict_line(verdict: Verdict, root: Path) -> str`
  - `main(argv: Optional[list] = None) -> int`

  The `budget_s` parameter exists for AC-4.5's core-level test. The CLI exposes no flag for it,
  and no environment variable reaches it (NFR Security: no knob).
- **CLI:** `h_mad_tdd_judge.py {state|judge} --root DIR [--target PATH]`. A relative `--target`
  resolves against `--root`.
- **Codex gate:** `_relative_target(root, raw, cwd=None)`,
  `_safe_shell_command(command, root=None, cwd=None)`, new `_contained_venv_python`, new
  `_load_judge`. The removals are listed in D8.
- **Claude gate:** stdin `tool_input.file_path` is read first. Refusal is by `REFUSAL_FORM`: (a)
  rc 2 with the reason on stderr, or (b) rc 0 with one stdout JSON deny. Exit 1 is never used.
- **`h_mad_audit_gate._suite_summary(text) -> Optional[SuiteSummary]`.**
- **`h_mad_wire_pin_gate._parse_tasks(text) -> list[dict]`:** the same list, with two keys added
  per dict.

## Error Handling Strategy

| Where | Failure | Surfaces as |
|---|---|---|
| Judge core | unreadable state file | `Chain("unreadable", …)`, never an exception |
| Judge core | impl-plan unreadable | recorded, name map used, carried into any DENY reason (AC-2.8) |
| Judge core | interpreter cannot start (`OSError` from `Popen`) | DENY `no-summary`, the reason naming the error |
| Judge core | budget exhausted | DENY `timeout`, the process group killed |
| Judge CLI `judge` | any exception | DENY `judge-error` line, rc 0 |
| Judge CLI `state` | any exception | no line, stderr message, rc 2 → the Claude gate refuses `judge-error` |
| Codex gate | import failure, or any exception after `--self-check` | `_deny(… kind=judge-error)`, rc 0, parseable JSON (AC-5.4) |
| Codex gate | chain unreadable | `_deny("H-MAD state governing this write is unreadable …")` |
| Claude gate | judge/state rc ≠ 0, zero or two lines, grammar miss | `_refuse judge-error` |
| Claude gate | errexit, `pipefail` or `nounset` anywhere | `EXIT` trap → `_refuse judge-error` in the chosen form |

The rc of the judge never selects ALLOW (spec FR-1). Every refusal names its `kind`. The Claude
gate writes the reason to stderr under both forms.

## Test Strategy

- **Layers.**
  - The judge core is unit-tested in-process against real files in `tmp_path`, with real pytest
    runs. There is no mock at the subprocess boundary: shims are real executables.
  - Each gate is tested only through its real entry point: stdin JSON, plus the positional
    argument for the Claude gate, run as a subprocess.
  - Claude-gate fixtures follow plan rule (ii). An allow- or `test-passing`-expecting fixture puts
    `python3 → sys.executable` in its bin dir. A `pytest-missing` fixture uses a
    `--without-pip` venv.
- **Worktree correctness.** Every test resolves hooks and scripts from `Path(__file__)` (plan layer
  6). The W6 test uses two distinct trees (plan §"Connection enforcement").
- **Stubs.**
  - AC-1.3's `state`/`judge` stubs are tree-B-style copies: a scratch tree holding the real hook
    beside a stub `scripts/h_mad_tdd_judge.py`. Each stub is its own fixture and is run alone.
  - The stubs are:
    - for `judge`: an empty line; two lines; `TDD-JUDGE: MAYBE`; an unknown-`kind` DENY; a
      traceback with rc 1; a valid ALLOW with rc 1;
    - for `state`: zero lines; two lines; a value outside the three; `TDD-STATE: none` with rc 1.
- **`EXIT`-trap members**, one fixture each (plan layer 6):
  - the traceback rc 1 stub;
  - the valid-ALLOW rc 1 stub;
  - a `python3` stub that fails the realpath call;
  - an unset variable on the refusal path, injected by mutation.
- **Mutation (FR-8).** Each guard gets one spec file, and each alternation branch is mutated
  alone. Scoring is on the pytest summary. The new spec files and their guards:

  | Spec file | Guard (AC) | Mutations |
  |---|---|---|
  | `tdd_judge_resolution.json` | Task-match authority (AC-2.5); the `none` rule (AC-2.3) | skip the authority `if`; `_NONE_VALUE_RE` → never match |
  | `tdd_judge_venv.json` | containment (AC-3.2): each of the three conjuncts alone | each conjunct → `True` |
  | `tdd_judge_scoring.json` | `pytest-missing` (AC-4.1); `errors ≥ 1` (AC-4.3); rc-blindness (AC-4.4); rule 8 (DD-5) | delete each branch alone; score on `returncode` |
  | `tdd_judge_chain.json` | chain reader (AC-5.2); unreadable decides (AC-6.9); the OD-9 all-records rule (AC-6.10) | nearest file only; skip unreadable; `all` → `any` |
  | `codex_gate_judge_wiring.json` | payload `cwd` base (AC-5.1); W1; W5a; crash guard (AC-5.4) | ignore `cwd`; bypass the judge (remove / force ALLOW); nearest-only status; drop the `try` |
  | `claude_gate_judge_wiring.json` | `tool_input` read (AC-6.1); `state` governance (AC-6.8); non-zero-rc refusal (AC-1.3); the blocking form (AC-6.5/6.6); W2; W5b; W6 two-tree; each trap member | per row, alone |
  | `audit_suite_summary_line.json` | DD-3 predicate, each word of `{"passed","failed"}` alone; the timed-beats-untimed rule; the SGR strip | per row, alone |

  The existing `audit_suite_gate.json` (9 mutations) and the three `wire_pin_*.json` specs anchor in
  files this feature edits, so `--check-anchors` runs in each edit's commit.
  - Reading at skills `1ef1a782`: `python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/*.json | grep '^ANCHORS: ANCHORS_OK'`
    → `specs=99 mutations=907 ok=907 drifted=0`.
  - `git grep -l 'h-mad-codex-tdd-gate\|h-mad-tdd-gate' -- h-mad/tests/mutation-specs | wc -l`
    → 0 files: no spec anchors in either gate today.
  - The `specs=`/`mutations=` figures grow by construction and are re-read at 5g, never carried.

## Test Plan

**New test modules** (paths resolved from `Path(__file__)`):

- **`h-mad/tests/test_h_mad_tdd_judge.py`**, the core:
  - AC-2.1–2.9;
  - AC-3.1–3.3;
  - AC-4.1–4.6, with AC-4.5 run through `judge(..., budget_s=1.0)` against a 30 s sleeper shim,
    asserting `timeout` within 1.0 s + a 5.0 s margin and no surviving shim process;
  - the D7 grammar rows, including the coloured and `2 passed`/stray-`1 failed` rows;
  - the D10 line grammar, round-tripped through the formatters;
  - the 3.9 floor: `ast.parse(src, feature_version=(3, 9))` over the four modules in D1;
  - the corpus differential of AC-2.9: same task ids, same order, over the tracked impl-plan
    corpus.
- **`h-mad/tests/test_h_mad_codex_tdd_gate_judge.py`**, the Codex gate:
  - AC-1.2, with 11 kinds; `timeout` runs at the default budget, about 40 s;
  - AC-3.4;
  - AC-5.1, AC-5.2, AC-5.4;
  - W1 and W5a;
  - the shell-policy differential with its published accounting.
- **`h-mad/tests/test_h_mad_tdd_gate_judge.py`**, the Claude gate:
  - AC-1.2, with the Claude-Code-shaped payload and 11 kinds;
  - AC-1.3, one stub per fixture;
  - AC-6.1, AC-6.3, AC-6.4, AC-6.5 or AC-6.6 per the chosen form, AC-6.8, AC-6.9, AC-6.10;
  - DD-1, DD-7 and DD-8 fixtures;
  - the four trap members;
  - W2, W5b and the two-tree W6.
- **`h-mad/tests/test_h_mad_tdd_gate_docs.py`:** AC-7.2's structural locators, each failing when
  its locator matches nothing.

**Existing modules, the named changes only** (invariant §"Regression provenance"):

- **`test_h_mad_codex_runtime.py::test_codex_hook_rejects_pytest_no_tests_collected_as_red`.**
  The assertion on the literal `exit 1` becomes an assertion on `no-tests-ran` (AC-5.3). It pinned
  the rc-scoring that FR-4 removes.
- **`test_h_mad_tdd_gate_codex.py` and `test_h_mad_tdd_gate_state_resolution.py`.**
  - The `HOOK` constant changes under either form.
  - The assertion migration follows spec AC-6.2's list for the chosen form: the 4 `returncode == 1`
    matching lines, by `grep -n 'returncode == 1'` over the two files at `1ef1a782`.
- **`test_h_mad_audit_suite_gate.py::test_an_empty_selection_is_not_a_pass`.** A docstring
  correction only (plan §"Regression census").
- **`test_h_mad_audit_suite_gate.py`:** new cases for the run_suite table rows and AC-4.7. The
  existing tests are unmodified.

**Commands** (plan §"Convention Prerequisites"):

```bash
/opt/anaconda3/bin/python -m pytest -q -p no:cacheprovider h-mad/tests handoff/tests handoff/scripts | tail -1
python3 h-mad/hooks/h-mad-codex-tdd-gate.py --self-check            # CODEX-TDD-GATE: PASS
bash docs/03-analysis/probes/codex-tdd-gate-defects/v1-offline-replay.sh <worktree> /Users/kimhawk/orca/HemaSuite > v1r.out; test $? = 0
grep -q '^V-1r: DONE VERDICT=PASS fails=0/6 ' v1r.out
```

## Verified premises (design-level)

Every command below ran at skills `1ef1a782` (`git log 2f262f8a..HEAD -- h-mad handoff` → empty,
so the plan's h-mad readings stand) unless stated otherwise:

- The two hooks, `_parse_tasks`, `_FIELD_RE`, `_suite_summary` and `run_suite` were read in full
  at their current text.
- The 21 existing test functions that spec v1.2 and plan v1.2 name (the 13 of AC-6.2's list, the
  5 of plan P7, and the 3 audit-suite tests of plan §"Regression census") each exist. Checked by
  one `grep -ln "def <name>\b" h-mad/tests/*.py` per name: 21 names, 1 file each.
- `git grep -n 'refusing fail-closed\|no derived test file\|not test-failure exit\|permits only explicit' -- h-mad/tests handoff | wc -l`
  → 0 matching lines. No test pins the Codex gate's reason text, so D8's new reason strings move
  no assertion.
- `git grep -n -i 'jq' -- 'h-mad/tests/test_h_mad_tdd_gate_*.py' | wc -l` → 7 matching lines,
  all in the two `_bin` helpers that symlink `jq`. No test removes `jq` or asserts the no-`jq`
  allow, so DD-2 moves no assertion. That zero holds because the helpers always install `jq`, and
  that is incidental: a future test that drops `jq` would now see the gate proceed.
- `readlink ~/.claude/hooks/h-mad-tdd-gate.sh` → `/Users/kimhawk/orca/skills/h-mad/hooks/h-mad-tdd-gate.sh`.
  `readlink ~/.claude/skills/h-mad` → `/Users/kimhawk/orca/skills/h-mad`.
- `git grep -c "h-mad-tdd-gate\|h-mad-codex-tdd-gate\|h_mad_derive_test_path\|exit-code protocol" -- h-mad handoff ':!h-mad/tests' ':!*/archive/*'`
  → the same nine per-file counts as the plan's stale-prose census.

## Invariant Compliance

- **Audit-gate signal discipline.**
  - The judge CLI prints a token and exits 0 on every verdict, DENY included.
  - A non-zero exit is reserved for an operational error: `state` raising, or argparse usage.
  - The Claude gate's rc 2 under form (a) is a host protocol that the host consumes. It is not an
    h-mad gate verdict read by the orchestrator.
- **Single-source contract.**
  - There is one chain reader, one resolver, one containment rule and one scorer.
  - The OD-9 escape rule lives only in the judge.
  - The registry's second `Production` grammar is the stated residual (D-A).
  - `_suite_summary` stays the audit gate's parser and is shared, not copied.
- **Standalone; no new external dependency.**
  - stdlib, `bash` and `pytest` only. `jq` is dropped from the Claude gate, which is a removal.
  - `codex` is still probed with `command -v`, as today, which is not an invocation.
- **Portable time bounds.** `Popen.communicate(timeout=…)` with `killpg`. No `timeout`/`gtimeout`.
- **Doc-template superset.** Every Phase-4 section is present. The shape check runs at save.
- **Operator-override preservation; backward compatibility.**
  - The audit gate's pass/fail logic changes only by moving a failures-without-passes summary from
    `UNREADABLE` to `FAIL`, and a coloured red summary from PASS to FAIL. Both block.
  - Committed stamps are not re-derived (plan §"Stamps"). No PASS flips.
- **Marker discipline.** No orchestrator transition is added.
- **Mutation verification.** Every mutation is re-read before it is scored (harness).
  `--check-anchors` runs in the same commit as each edit to an anchored file.
- **Test discrimination.** Each new pin names the observation that differs:
  - AC-6.1: `(0,'','')` today versus a refusal;
  - AC-5.2: allow today versus `test-passing`;
  - D7: `(1, 0)` today versus FAIL for the coloured row.

  Each is run red against the unfixed tree (plan P3, `reproduce.py`).
- **Guard narrowing.** The shell-policy relaxation ships with the full differential (D8, D12).
  DD-7's `tests/…` relative exemption is a second softening: a relative `tests/x.py` was gated and
  is now exempt. It is listed by name, and it matches the Codex gate's existing rule.
- **Connection enforcement.** W1–W6 are mutated in both directions (plan table), and W6 uses two
  trees.
- **Incident replay.** V-1r replays HemaSuite `1fbf8022`/`31bfcfe4` against the worktree gate. It
  is a merge condition.
- **Assumption verification; behavioural premises carry their command.**
  - Each load-bearing assumption was executed here, and its command sits beside its reading:
    `pgrep` survivors, bash 3.2 constructs, the grammar rows, the `none` controls, today's
    `_suite_summary` readings, the latency figures.
  - Not executed: the host hook timeouts (OQ-D1) and the live V-0.
- **Regression provenance.** Every changed existing assertion is named in §"Test Plan" with what it
  pinned.
- **Both halves of a doc change.** Each doc edit in D11 lands with the behaviour it describes, and
  AC-7.2 pins the new wording by locator, not by the old text's absence.
- **Reimplementation parity.** None: no third-party dependency is replaced.
- **Project: skill self-containment.** The judge lives inside `h-mad/`. The hooks reach it by their
  own path, and no other skill is imported.
- **Project: skill manifest integrity.** `SKILL.md` registers the judge, and its gate bullets state
  the shipped gate (D11).

## Open Questions

- **OQ-D1 (operator).** The hosts' own PreToolUse hook timeouts are not measured: Claude Code's
  default for an unregistered `timeout`, and Codex's. If either host kills the hook inside 40 s,
  the host's timeout semantics decide the write, and that may be an allow. Measure them in V-0's
  session, or register an explicit `timeout` above 40 s at install?
- **OQ-D2 (spec).** Should the value axis read `` `path.py::symbol` `` as `path.py` (D5 residual,
  1 corpus line affected)?
- **Carried:** plan OQ-1 (no `.venv` and no pytest → `pytest-missing`) and OQ-3 (`2 passed, 1 error`
  scores PASS) stand unanswered.

## Version History
- v1.0: Initial design (2026-09-28) from spec v1.2 and plan v1.2 at skills 1ef1a782: judge h-mad/scripts/h_mad_tdd_judge.py with state/judge verbs; TDD-STATE and TDD-JUDGE line formats (D10); 40 s whole-judge budget with process-group kill (D6); summary-line grammar with SGR strip and closed word set (D7); Claude gate refusal function, REFUSAL_FORM literal and EXIT trap (D9); venv shell branch for -m pytest only (D8). DD-1..DD-9 depart from plan or spec wording, each with its revert. OQ-D1 (host hook timeouts), OQ-D2 raised.
