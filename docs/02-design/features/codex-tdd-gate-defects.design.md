# Design: codex-tdd-gate-defects

## Executive Summary

One new stdlib module, `h-mad/scripts/h_mad_tdd_judge.py`, holds the chain reader, the test
resolver, the interpreter selector and the summary scorer. The Codex gate imports it. The Claude
gate runs its CLI. The CLI has two verbs, `state` (one `TDD-STATE:` line) and `judge` (one
`TDD-JUDGE:` line). The Claude gate emits every refusal through one function, in the one form V-0
chose, and an `EXIT` trap routes every exit that nothing decided into that function.

## Overview

The design implements spec v1.3 FR-0…FR-8 and plan v1.2. OD-1…OD-9 and the orchestrator's
OD-A…OD-D are resolved as spec v1.3 records them. Spec v1.3 was read in the working tree, where the
spec author was revising it in parallel with this revision; its Version History line `v1.3` is the
text this design answers. Operator decisions: OD-8 refuses an unreadable chain `judge-error` in the chosen form.
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
- the shell-policy venv executable lookup;
- how the Claude gate avoids hanging on a terminal stdin (spec FR-6 leaves it to the design);
- the `fallback` field and rebase contract that `grok-codex-fallback` D2 builds on (D13).

Some decisions here go beyond the spec's or the plan's wording. Each is marked **DD-n**, and
§"Supersedes the plan or the spec on" lists them.

## Supersedes the plan or the spec on

Each item names the sentence it departs from, the reason, and the revert. The last column says
where the item stands now: which spec v1.3 text adopted it, and which plan v1.2 sentences still
state the old rule. The report routes each open item to its owner. IDs are stable: a withdrawn row
keeps its number.

| DD | Departs from | Design | Why | Revert | Now |
|---|---|---|---|---|---|
| DD-1 | Plan §"Implementation Strategy", layer 6 (**Claude gate.**), step 3, which begins "The `state` verb decides governance" and precedes step 4's exemptions; spec v1.2 FR-6 | The Claude gate runs the exemptions and the `.py` filter **before** the `state` verb | Under the plan's order, an unreadable state file refuses every write, including an exempt `.json` write that would repair it. That is a deadlock nobody asked for. For every readable state the verdicts are identical under either order | Swap the two blocks | Adopted by spec v1.3 (OD-A; FR-6 "Order"; AC-6.9). Owed: the plan's layer-6 step order |
| DD-2 | Plan §"What we deliberately do not touch" and plan §"Out-of-Scope (confirmed from spec)", each listing the no-`jq` fail-open as kept; spec v1.2 §Out-of-Scope | The gate no longer reads state with `jq`, so the `jq` dependency and its "no `jq` → allow" path are removed | Spec v1.2 FR-6 "Unchanged" already said "if the design removes that dependency, this path goes with it". Keeping a `command -v jq` allow with nothing left that uses `jq` would be a silent stand-down with no reason behind it | Restore the `command -v jq` check before the `state` call | Adopted by spec v1.3 (FR-6; AC-6.12; §Out-of-Scope). Owed: both plan sections |
| DD-3 | Plan §"Two explicit branches" in `run_suite` | One predicate: a parsed summary that carries neither a `passed` nor a `failed` phrase stays `UNREADABLE no_summary` | The two-branch form moves `3 skipped in …`, `5 deselected in …` and `1 xfailed in …` from `no_summary` to `no_tests_ran` (measured in D7). The one predicate closes that axis | Two branches, and accept the three reason changes | Adopted by spec v1.3 (FR-4 "Audit-gate non-change"). Owed: the plan section |
| DD-4 | Plan summary-line rule | SGR colour sequences are stripped before a line is matched | Measured: today `_suite_summary` reads a coloured `1 failed, 1 passed` as `(1, 0)`, which `run_suite` scores PASS. The plan's whole-line rule turns that into `UNREADABLE`. Stripping turns it into the correct `FAIL` | Drop the strip; coloured runs then read `no_summary` | Adopted by spec v1.3 (OD-D; FR-4 "Colour", audit-gate change 2). Owed: the plan's rule |
| DD-5 | Spec v1.2 FR-4 classification (7 rules, no final else) | Rule 8: any other parsed summary (0 failed, 0 passed, 0 errors, not `no tests ran`) → `no-tests-ran` | The v1.2 list is not total. Without rule 8 a skipped-only run has no kind | Rule 8 → `no-summary` instead. That keeps FR-1's kind table meaning "`no tests ran`" alone for `no-tests-ran`, and stretches `no-summary` instead. Both kinds DENY | Adopted by spec v1.3 (FR-4 rule 8; FR-1 kind table) |
| DD-6 | — | **Withdrawn in v1.1** (orchestrator OD-C). The shell policy implements spec FR-3 as written: a contained venv interpreter passes the existing argv rules, H-MAD control allowlist included (D8) | v1.0 narrowed FR-3 to `-m pytest …` without the spec's agreement | — | Spec v1.3 AC-3.6. Owed: the plan's expected softened set gains the control-allowlist rows (D8 "Differential") |
| DD-7 | (not stated in spec v1.2 or plan v1.2) | The Claude gate makes a relative target absolute against the project root before any check | Without this, the fast path resolves a relative target against the process cwd while the judge resolves it against the root, and the two disagree. The softening it causes is published by the D9 differential: exactly two rows | Leave targets raw; the fast path then defers every relative target to the `state` verb | Kept (orchestrator OD-E, author's call). Spec v1.3 FR-6 and AC-6.15 bind it |
| DD-8 | (not stated; today an empty target with an ACTIVE record is allowed) | An empty target on a governed root is refused `judge-error` | OD-4's root cause is payload-shape drift. A payload the gate cannot read yields an empty target, which today is a silent allow. The Codex gate already refuses "could not identify this write target" | Allow on an empty target, as today | Adopted by spec v1.3 (FR-6; AC-6.13) |
| DD-9 | (not stated) | A Claude-gate target outside the project root has the root alone as its chain | A chain from outside the root is empty, so the target would read `none` and be allowed. Today the root-first reader governs it. This keeps today's refusal | Read `none` for an outside target | Adopted by spec v1.3 (FR-6; AC-6.14) |
| DD-10 | Plan §"Architecture Considerations", the "Time bound" bullet: "The judge bounds pytest with `subprocess.run(timeout=…)`" | `Popen(start_new_session=True)` with `communicate(timeout=…)`, and `os.killpg` on timeout (D6) | Measured in D6: `subprocess.run(timeout=1)` returned and left the shim's `sleep` alive; the process-group kill left none. A surviving pytest child can write into the tree after the gate decided | `subprocess.run(timeout=…)`, accepting survivors | Owed: the plan bullet |
| DD-11 | Spec FR-4 classification rule 2: "`No module named pytest` in the output" | Rule 2 matches only a whole line, after stripping, that ends with `: No module named pytest` (D7) | A RED test whose assertion message quotes the phrase would otherwise read `pytest-missing`. The narrowing is fail-closed: a real missing-pytest output the rule misses has no summary line and still reads DENY `no-summary` | Substring match anywhere in the output | Owed: spec FR-4 rule 2 wording |

## Architecture Overview

```
Codex host ──stdin JSON──▶ h-mad-codex-tdd-gate.py ──import──▶ h_mad_tdd_judge (core)
                              │ shell policy: _safe_shell_command ──▶ judge.venv_contained
                              └ per write target: judge.read_chain → judge.judge → _deny / allow

Claude host ─stdin JSON──▶ h-mad-tdd-gate.sh
                              ├ EXIT trap installed first (undecided exit → refusal)
                              ├ payload → target (stdin tool_input.file_path | file_path | path; else $1)
                              ├ _chain_may_hold_state fast path (proved no state name on the chain → allow)
                              ├ empty target → root governance                  [DD-8]
                              ├ exemptions, .py filter                          [DD-1]
                              ├ python3 <hook-realpath>/../scripts/h_mad_tdd_judge.py state …  → TDD-STATE:
                              ├ Codex-authorship check (codex-escape=/blocker= from TDD-STATE, env override, codex on PATH)
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
  - Premise: `/usr/bin/python3 -c 'import sys; sys.dont_write_bytecode=True; import h_mad_wire_pin_gate, h_mad_audit_gate, h_mad_wire_registry; print(sys.version.split()[0], "ok")'`,
    run in `h-mad/scripts` at skills `76e7af19`, printed `3.9.6 ok`. (v1.0 quoted this reading
    under a command with no `print`, which cannot produce it.)
- **Types** (`typing.NamedTuple`):
  - `Record(key: str, codex_status: str, state_file: Path, fallback: str)`. `codex_status` is the
    record's value, or `"available"` when it is absent or `null`. A non-string value is
    stringified. `fallback` is the record's `fallback_agent` tag (D13): `absent`, `null`, `grok`,
    `claude`, or `invalid:<json>`.
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
  is false is skipped. Every other path is a state file, whatever its type (spec v1.3 FR-5: a
  name present on the chain that is not a regular file is unreadable, never absent).
  - The read is `fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)`, then `os.fstat(fd)`. If the
    mode is not `S_ISREG`, the error is `not-a-regular-file`. Otherwise the bytes are read from
    that same `fd`, decoded as UTF-8, and passed to `json.loads`. Opening with `O_NONBLOCK` and
    testing the opened descriptor closes two holes at once: a FIFO cannot block the open, and a
    file swapped between a `stat` and an `open` cannot be read unchecked.
  - Executed under `/usr/bin/python3` 3.9.6 in a scratch tree (deleted): a FIFO →
    `not-a-regular-file` in 0.0 s; a directory → `not-a-regular-file`; a dangling symlink →
    `FileNotFoundError`; a regular file → read. `os.path.lexists` was true for all four.
  - `OSError`, `UnicodeDecodeError`, `ValueError`, `not-a-regular-file`, a top level that is not
    an object, or an `orchestrator_state` that is present and not an object each end the walk:
    `Chain("unreadable", (), <file>, <exception class name, "not-a-regular-file" or "not-an-object">)`.
  - The first unreadable file decides. A readable step5 record elsewhere on the chain does not
    rescue it (FR-5: "any unreadable file on the chain means `unknown`").
- A record is ACTIVE when it is a dict whose `phase == "step5"`. Records are ordered nearest state
  file first, and in JSON key order within a file. Each ACTIVE record's `fallback` tag is computed
  here, by D13's rule, so no later reader parses the state file again.
- Result: `Chain("active", records, None, "")` when any record is ACTIVE, else `Chain("none", …)`.
- **The fast path is bound to this reader.** v1.0 kept today's `_resolve_state_file`, which tests
  with `-f` and `cd`s into the target's parent. Measured against this reader, it allowed two
  governed writes before the reader ran: a dangling-symlink state (`-f` false, reader
  `unreadable`), and a new file under a directory that does not exist yet with the state one level
  up (`cd` fails, reader `active`). The class is "any input on which the fast path says no state
  and this reader does not say `none`". D9 step 4 replaces the function with one that tests the
  same names this reader tests (`lexists`), over the same directories, and defers to the `state`
  verb on every input where it cannot prove the two agree.
- **Residuals.**
  - A state file inside a directory the process cannot search reads as absent to both
    `os.path.lexists` and the fast path's `[ -e ] || [ -L ]`. Both gates agree, and both allow.
    This is today's behaviour.
  - The Codex gate's `_any_phase5_status` (spec FR-5: unchanged) still calls `read_text` on every
    `docs/.bkit-memory.json` under the root, and `main` calls it for every payload. A FIFO there
    blocks the Codex gate before this reader runs, and the host's hook timeout then decides.

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
   - A candidate is *present* when `os.stat` succeeds and its mode is `S_ISREG`. Every other
     candidate (absent, a dangling symlink, a directory, a FIFO) is *missing*. Missing candidates
     are never run.
   - If no candidate is present, the verdict is `test-missing`. The reason names every candidate
     and says "author the failing test first".
   - If some are present and some missing, only the present ones run (D7 "Several candidates").
     Any DENY that follows names each missing candidate as `missing`. So a mixed set cannot reach
     pytest's `file or directory not found`, whose `no tests ran` would otherwise outrank
     `test-passing` in D7's precedence.
   - The candidate run's cwd is that candidate's `B` (FR-4).
6. **Name map.** If no task matched, the judge calls the name map on the target's root-relative
   POSIX path:
   `subprocess.run(["bash", <scripts>/h_mad_derive_test_path.sh, rel], cwd=root, capture_output=True, text=True, timeout=<remaining budget>)`.
   - A non-empty stdout resolves against `root`. The candidate is that file, and its cwd is `root`.
   - If that candidate is missing (rule of step 5), the verdict is `test-missing`.
7. **Deny.** If neither source yields a path, the verdict is `no-test-resolved`.
8. **Plan outcomes ride on every DENY.** The resolver keeps one plan-outcome note per plan path
   tried: `matched none`, `matched`, `absent` or `impl-plan unreadable: <class>`. It also keeps the
   literal name-map result when the name map ran (`name map: <path>`, `name map: empty for <rel>`
   or `name map: target outside root`). Every DENY reason of that `judge()` call ends with these
   notes, whatever its kind: `test-missing`, `no-test-resolved`, and every kind a candidate run
   produces. The class is "a DENY reached after a plan read failed", and its members are every DENY
   kind that can follow resolution. So AC-2.8's route (invalid UTF-8 plan, then a name-map test that
   does not exist) returns DENY `test-missing` whose reason contains `impl-plan unreadable`, and so
   does the same plan with a passing name-map test (`test-passing`). Residual: an ALLOW carries no
   reason field (D10), so a RED name-map ALLOW does not report the unreadable plan.

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
- **Process-group kill** (DD-10). Each run is started with
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
  - The Claude Code command-hook default timeout is **not measured here**. The installed
    registration sets none: `~/.claude/settings.json` PreToolUse `Write|Edit` →
    `{'type': 'command', 'command': '$HOME/.claude/hooks/h-mad-tdd-gate.sh'}`.
  - The unit of a registration's `timeout` cannot be read off this machine either. The other
    installed `~/.claude/settings.json` hook registrations carry values of 5 and 10 on some
    entries and 5000, 8000 and 15000 on others (read with a `json.load` over every hook entry).
  - No Codex hook timeout is documented in `h-mad/references/codex-runtime.md`. The Codex gate is
    not registered on this machine at all: `~/.codex/hooks.json` has no entry naming
    `codex-tdd-gate`, and HemaSuite's `.codex/hooks.json` is `{"hooks": {}}`.
  - So the design does not pick a host timeout blind. It makes the host's behaviour a measured
    merge condition instead: the 5g step "OQ-D1 host-deadline probe" (§"Implementation Order")
    runs a governed write whose judge takes longer than 30 s through the live Claude Code host,
    and requires the gate's own decision to land. If the host cancels the hook first, the
    registration gains an explicit `timeout` large enough for the probe to pass, in whatever
    unit the probe shows, and the probe is re-run. OQ-D1 stays open until that probe reads.
  - AC-1.2's two `timeout` fixtures run at the full budget, because the CLI exposes no budget
    knob. They add about 80 s to the suite (two runs of about 40 s each), which is the stated
    cost of testing the gate-level `timeout` through the real entry points.
- **Portable time bounds.** The bound is `communicate(timeout=…)` in Python. No `timeout` or
  `gtimeout` CLI is used.

### D7 — Summary scoring: `_suite_summary` extended in place, and the classifier (FR-4, OD-7)

- **Parser.** `h_mad_audit_gate._suite_summary(text)` now returns
  `SuiteSummary(passed, failed, errors, no_tests_ran, phrases)` (a `NamedTuple`, where `phrases`
  is a `frozenset` of the category strings seen, such as `"passed"` or `"subtests passed"`), or
  `None`.
  - There is no second summary parser, and `_SUITE_RE` is removed. Premise:
    `git grep -n "_suite_summary" -- h-mad handoff ':!h-mad/tests/fixtures'` → 2 matching lines,
    both in `h_mad_audit_gate.py` (the definition and `run_suite`'s call). No test calls it
    directly.
- **Summary-line grammar** (plan's whole-line rule, with an open category axis):
  - Each line of `stdout + stderr` has SGR sequences (`\x1b\[[0-9;]*m`) removed, then surrounding
    whitespace, then `=` padding, then whitespace again.
  - A summary line then matches
    `^(?:(?P<ph>\d+ C(?:, \d+ C)*)|no tests ran)(?P<timed> in \d+(?:\.\d+)?s(?: \(\d+:\d{2}:\d{2}\))?)?$`,
    where `C`, the category, is `[a-z][a-z-]*(?: [a-z][a-z-]*)*`: one or more lowercase words.
  - Each phrase is `(\d+) (C)`. Its category string goes into `phrases`. A phrase adds to a count
    only when its category is exactly `passed`, exactly `failed`, or exactly `error` or `errors`.
    So `2 subtests passed` adds nothing to `passed`.
  - A timed line beats an untimed one, and within each kind the last line wins.
  - A count phrase inside a longer line is never read.
- **Why the category axis is open (the class, not the instance).** v1.0 closed it to eleven
  words and so rejected pytest 9.1.1's own `subtests` phrases: a whole summary line then failed to
  match, which moved a PASS to `UNREADABLE`. The axis is open-ended, because pytest 9.1.1's
  `_pytest.terminal.KNOWN_TYPES` has three two-word entries (`subtests passed`, `subtests failed`,
  `subtests skipped`), and pytest appends any category a plugin reports. The rule is therefore
  over the shape of a category, not over a list of them. Every `KNOWN_TYPES` entry, read by
  `/opt/anaconda3/bin/python -c 'import _pytest.terminal as t; print(t.KNOWN_TYPES)'` (pytest
  9.1.1), matches `C`.
- **Residual, stated** (spec v1.3 FR-4 asks for it). A plugin category that is not lowercase
  words (a digit, an uppercase letter, or punctuation other than `-`) makes its whole line fail to
  match. That line is then not a summary line. If no other summary line exists, the judge denies
  `no-summary` and `run_suite` reads `UNREADABLE no_summary`, which fails closed. A lowercase
  plugin category is a summary phrase. It adds to no count, so its verdict follows from the
  `passed`, `failed` and `error` phrases beside it. A line holding only such phrases reads
  `UNREADABLE no_summary` in `run_suite` (DD-3's predicate) and `no-tests-ran` in the judge
  (rule 8).
- **Measured `subtests` lines.** pytest 9.1.1 under `/opt/anaconda3/bin/python -m pytest <f> -x -q --no-header -p no:cacheprovider`,
  on scratch files (deleted):
  - two passing subtests plus one passing test → `2 passed, 2 subtests passed in 0.00s`, rc 0;
  - one passing subtest, one failing subtest and one failing test, with `-x` →
    `2 failed, 1 subtests passed in 0.02s`, rc 1; without `-x` → `3 failed, 1 subtests passed in 0.02s`;
  - a skipped subtest → `1 passed, 1 skipped in 0.00s`. No run printed `subtests failed` or
    `subtests skipped`; a failing subtest was counted under `failed`.
- **Grammar executed at skills `76e7af19`**, by an inline `/usr/bin/python3` heredoc that also
  imported today's `_suite_summary` (nothing was written). Readings, as (passed, failed, errors,
  no_tests_ran), with today's reading after `today`:
  - `1 failed in 0.01s` → (0,1,0,F); today `None`;
  - `1 error in 0.06s` → (0,0,1,F); today `None`;
  - `no tests ran in 0.00s` → (0,0,0,T); today `None`;
  - `2 passed in 0.1s` followed by a line `1 failed` → (2,0,0,F); today `(2, 0)`;
  - untimed `1 failed, 8 passed` → (8,1,0,F); today `(8, 1)`;
  - the coloured line below → (1,1,0,F); today `(1, 0)`;
  - `9 passed, 1 warning in 1.09s` → (9,0,0,F); today `(9, 0)`;
  - `==== 1 failed, 2 passed in 65.20s (0:01:05) ====` → (2,1,0,F); today `(2, 1)`;
  - `1 xfailed in 0.1s` → (0,0,0,F); today `None`;
  - `2 passed, 2 subtests passed in 0.00s` → (2,0,0,F); today `(2, 0)`;
  - `2 failed, 1 subtests passed in 0.02s` → (0,2,0,F); today `None`;
  - the same line under `--color=yes` (its bytes captured with `od -c`: the `3 failed` and
    `1 subtests passed` phrases each wrapped in SGR sequences) → (0,3,0,F) for the `3 failed`
    variant; today `None`;
  - `1 passed, 1 skipped in 0.00s` → (1,0,0,F); today `(1, 0)`;
  - `3 skipped in 0.1s`, `5 deselected in 0.1s` and `2 subtests failed in 0.1s` → (0,0,0,F);
    today `None`;
  - `3 apples in 0.1s` → (0,0,0,F), with `phrases` = {`apples`}; today `None`. It is a summary
    line now, by the open axis; it still scores `no_summary` in `run_suite` and `no-tests-ran` in
    the judge, and both deny;
  - `collected 0 items`, `E   assert '1 failed' in x`, `FAILED t.py::a - 1 failed` and
    `3 Apples in 0.1s` → None; today `None`.
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
    if not ({"passed", "failed"} & summary.phrases):
        return {"reason": "no_summary", "verdict": "UNREADABLE", "rc": run.returncode}
    ```

    The test is on exact category strings, so `subtests passed` alone does not satisfy it.
- **Today's readings for DD-3's population**, taken by calling today's `_suite_summary` under
  `/usr/bin/python3` at skills `1ef1a782`: `3 skipped in 0.1s`, `5 deselected in 0.1s`,
  `1 xfailed in 0.1s`, `1 error in 0.06s` and `no tests ran in 0.00s` each → `None`, so each scores
  `UNREADABLE no_summary`. After the change each still scores `no_summary`.
- **The table.** The plan's nine-row table holds cell by cell, and these four rows are added:

  | Stub prints | `run_suite` today | after |
  |---|---|---|
  | coloured `1 failed, 1 passed in 0.04s` | PASS | **FAIL** |
  | `3 skipped in 0.1s` | UNREADABLE `no_summary` | UNREADABLE `no_summary` |
  | `2 passed, 2 subtests passed in 0.00s` | PASS | PASS |
  | `2 failed, 1 subtests passed in 0.02s` | UNREADABLE `no_summary` | **FAIL** |

  These are spec v1.3 FR-4's three audit-gate changes (a failures-without-passes summary, the
  coloured row, the `subtests` row) and its non-change. The coloured row moves PASS to FAIL, so it
  blocks where today allows. No row moves toward PASS, so no stamp flips toward PASS.
- **Judge classifier** `score(proc_output, timed_out)`, first match wins:
  1. `timed_out` → `timeout`.
  2. Some whole line, after stripping, ends with `: No module named pytest` (DD-11). That is the
     unquoted `-m` form, measured as
     `/Applications/Xcode.app/Contents/Developer/usr/bin/python3: No module named pytest`, rc 1,
     and again in this revision as `<scratch venv>/bin/python: No module named pytest` from a
     `--without-pip` venv built by `/opt/anaconda3/bin/python`. → `pytest-missing`.
  3. `_suite_summary` is `None` → `no-summary`.
  4. `no_tests_ran` → `no-tests-ran`.
  5. `errors ≥ 1` → `pytest-error`. The reason contains "import" and "inside the test body"
     (AC-4.6).
  6. `failed ≥ 1` → `red-measured`.
  7. `passed ≥ 1` → `test-passing`.
  8. Otherwise → `no-tests-ran` (DD-5; spec v1.3 FR-4 rule 8).

  The rc appears in the reason only.
- **Residual of rule 2.** A RED test whose output holds a whole line ending
  `: No module named pytest` is denied `pytest-missing`. That is a false deny, and it fails closed.
- **Several candidates** (spec FR-2 rule 4). The present candidates (D3 step 5) run in order; a
  missing candidate is never run and is named `missing` in any DENY reason.
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
- **`_payload_cwd_base(root, cwd) -> Path`** (OD-2), the one statement of the payload-`cwd` rule.
  It returns `c = Path(cwd).expanduser().resolve()` when `cwd` is a non-empty string, `c` is a
  directory, and `c == root` or `root in c.parents`. Otherwise it returns `root`. `root` is
  already resolved (`_project_root` returns `.resolve()`d paths on every branch), and the cwd is
  resolved before the comparison. That order matters here: `TMPDIR` is under `/var/folders/…` and
  `/var` is a symlink to `private/var`, so an unresolved cwd compared with a resolved root would
  fall back to `root`. Both callers below use this helper, and neither restates the rule.
- **`_relative_target(root, raw, cwd=None)`** (OD-2).
  - An absolute `raw` resolves as today.
  - A relative `raw` resolves against `_payload_cwd_base(root, cwd)`.
  - `main` passes `payload.get("cwd")` to both `_relative_target` and `_safe_shell_command`,
    never the process cwd, so
    `test_codex_hook_resolves_git_root_from_nested_cwd` (no payload `cwd`, process cwd nested)
    still resolves against the root.
- **Per target.**
  1. `chain = judge.read_chain(root, absolute)`.
  2. `unreadable` → `_deny("H-MAD state governing this write is unreadable (<file>: <error>); refusing fail-closed. kind=judge-error")`.
  3. `none` → continue.
  4. `active` and `_is_production_python(relative)` → `verdict = judge.judge(root, absolute, chain.records)`.

  Step 2 comes before the production filter, as today's `_target_phase5_status` check does. So on
  the Codex side an exempt write on an unreadable chain is still refused, while the Claude side
  allows it (DD-1, OD-A). The asymmetry is kept on purpose. The Codex gate is the implementer's
  gate, and repairing orchestrator state is the orchestrator's job, done through Claude's
  `Write` or `h_mad_state_write.py`. Spec v1.3 does not state the asymmetry; a sentence in FR-5 is
  owed.
  5. `DENY` → `_deny(f"H-MAD Phase 5 requires a failing test before {relative}: kind={kind}; {reason}")`.
     `relative` is root-relative, so AC-5.1's deny names `hematology-paper-writer/tools/review_round/guideline_excerpts.py`.
- **Crash guard** (AC-5.4). The whole body of `main` after `--self-check` sits inside
  `try: … except Exception as exc: return _deny(f"H-MAD Phase 5 gate raised {type(exc).__name__}: {exc}; refusing fail-closed. kind=judge-error")`.
  `_deny` prints JSON and returns 0.
- **Shell policy** (spec FR-3 as written; orchestrator OD-C; DD-6 withdrawn). New helper
  `_contained_venv_executable(token, root, cwd) -> Optional[Path]`.
  - `p = os.path.normpath(os.path.join(_payload_cwd_base(root, cwd), os.path.expanduser(token)))`.
    An absolute `token` ignores the base, because `os.path.join` does.
  - It returns `Path(p)`, the **lexical** path, when every one of these holds, else `None`:
    - `token` contains `/`;
    - `Path(p).name.startswith("python")`;
    - `Path(p).parent.name == "bin"`;
    - `Path(p).parent.parent.name == ".venv"`;
    - `Path(p).is_file()`;
    - `h_mad_tdd_judge.venv_contained(Path(p).parent.parent.parent, root)`.
  - `_safe_shell_command(command, root=None, cwd=None)` changes one line. The executable is found
    by `resolved_executable = (_contained_venv_executable(argv[0], root, cwd) if root is not None else None) or _trusted_executable(argv[0])`.
    Every argv rule after that line is unchanged. So under a contained-venv token, exactly the
    rules that apply to a `python*` executable apply: `-m pytest …`, and a script under the hook's
    own `h-mad/scripts/` that `_safe_hmad_script` accepts. That is FR-3's "only `python -m pytest …`
    and the H-MAD control allowlist pass" (AC-3.6).
  - **Why the lexical path, not its realpath.** The argv rules key on `resolved_executable.name`.
    The lexical name is `python*` by the predicate above. A contained venv's `bin/python` may
    symlink anywhere (OD-1), and its realpath's name could be `cat` or `hmad-dispatch`, which
    would reach `READ_ONLY_COMMANDS` or the dispatch branch. Keying on the lexical name keeps a
    venv token inside the `python*` rules whatever it points at.
  - `_trusted_executable` is unchanged, and `--self-check` passes `root=None`, so the new lookup
    is inert there.
  - `-c`, `-m pip` and a script outside `h-mad/scripts/` under a venv token reach the `python*`
    rules and are rejected by them, as they are under `/usr/bin/python3` today.
  - Residual, pre-existing and unchanged: the control branch resolves a relative *script*
    argument against the process cwd (`Path.cwd()`), not the payload `cwd`.
- **Differential.** The plan's corpus (§"Guard narrowing: shell policy") is crossed in full,
  through the gate's real entry point. The fixture tree is D12's.
  - One argv row is added: `<the hook's h-mad/scripts>/h_mad_state_write.py <root>/docs/.bkit-memory.json`,
    an argv `_safe_hmad_script` accepts under `/usr/bin/python3`.
  - **Expected softened set:** {contained venv} × {spellings that resolve into it, `python-evil`
    included} × {`-m pytest tests/test_x.py`, the `h_mad_state_write.py` row}. Every other
    softened row is a defect; every tightened row is justified by name.
  - This is wider than plan v1.2's expected set, which stops at `-m pytest …`. The plan's
    §"Guard narrowing: shell policy" accounting sentence is owed that change; FR-3 has always
    permitted it.

### D9 — Claude gate (`h-mad/hooks/h-mad-tdd-gate.sh`; FR-6, OD-4, OD-5, OD-8, OD-9)

The gate is rewritten top to bottom. The shebang stays `#!/bin/bash`, and it must run under
`/bin/bash` 3.2.57. These constructs were executed under `/bin/bash` 3.2.57 at skills `1ef1a782`
by a scratch script, since deleted (the constructs v1.1 adds carry their own readings in the
steps below):
- the JSON escaper round-trips `a "q" \ back<TAB>tab<LF>nl` through
  `python3 json.load` as `'a "q" \\ back tab nl'`;
- `[[ $L =~ $re ]]` with `BASH_REMATCH` accepts a valid DENY line and rejects `kind=bogus`;
- `*$'\n'*` detects a second line;
- `set -f` word splitting counts two `record=` fields;
- an `EXIT` trap turns an errexit from `X=$(exit 3)` into the trap's `exit 2`, and the final rc is
  2.

**Order of the script** (spec v1.3 FR-6 "Order": fast path, empty target, exemptions,
governance, Codex authorship, judge):

1. **Start-up.** `set -euo pipefail`, then `readonly REFUSAL_FORM=<a|b>`, then `DECIDED=""`, then
   `TRC=0 SRC=0 JRC=0`, then `trap _on_exit EXIT`.
   - `REFUSAL_FORM` is a literal, written at implementation from V-0's `CHOSEN=`. It is not read
     from the environment (NFR: no knob).
   - The three status variables are initialised because each is later assigned only on a
     failure (`X=$(…) || TRC=$?`). Under `set -u` an uninitialised one would abort the success
     path into the trap, and every governed write would be refused.
   - The trap is installed before the first fallible command.
2. **Target** (OD-4, OD-B; stdin first, `$1` only as fallback).
   - `TP=$(python3 -c "$READER") || TRC=$?`. The reader is an inline program:
     - it reads nothing when `os.isatty(0)` is true;
     - otherwise it reads fd 0 with `select.select` and `os.read` until EOF or until 2.0 s have
       passed in total;
     - it parses the bytes as UTF-8 JSON and prints the first non-empty string among
       `tool_input.file_path`, the top-level `file_path` and the top-level `path`;
     - it exits 3, printing nothing, when that string holds a control character (`ord < 32` or
       127);
     - it prints nothing and exits 0 when stdin is empty, is not a JSON object, or has no such
       field.
   - Then:
     - `TRC == 0` and `TP` non-empty → `TARGET_PATH=$TP`, even when `$1` is also given;
     - `TRC == 0` and `TP` empty → `TARGET_PATH=${1:-}`;
     - any other `TRC` → `TARGET_PATH=""`. A payload was present but unusable, or the reader
       failed, so `$1` is not trusted in its place. The empty-target rule (step 5) decides.
   - **Why this never hangs.** Claude Code's registration passes no argument and writes the
     payload on stdin. A hand invocation from a terminal has a tty on fd 0, which is not read. A
     pipe held open with no data costs the 2.0 s bound and then falls back to `$1`.
   - **Executed** under `/bin/bash` 3.2.57 with this reader, in a scratch script (deleted):
     - stdin `{"tool_input":{"file_path":"/stdin/win.py"}}` plus `$1=/positional/lose.py` →
       `/stdin/win.py`;
     - stdin `/dev/null` plus `$1` → the `$1` path;
     - stdin `{"file_path":"/top.py"}`, no `$1` → `/top.py`;
     - stdin whose `tool_input.file_path` holds an escaped newline, plus `$1` → rc 3. The v1.1
       rule then leaves the target empty; the scratch script, which fell back to `$1` on rc 3,
       showed why that fallback must not exist;
     - stdin held open by a `sleep 6` writer, plus `$1` → the `$1` path after 2.06 s;
     - no stdin redirection, run from a Python `subprocess.run` inside the Bash tool → the `$1`
       path after 0.06 s.
3. **Absolute target** (DD-7). `ROOT_ABS=$(cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null && pwd -P) || ROOT_ABS=""`.
   A non-empty relative `TARGET_PATH` becomes `$ROOT_ABS/$TARGET_PATH` when `ROOT_ABS` is
   non-empty. This is string work only.
4. **Fast path** (spec v1.3 AC-6.11). `_chain_may_hold_state "$ROOT_ABS" "$TARGET_PATH" || _allow`.
   The function returns 1 only when it has *proved* that no `docs/.bkit-memory.json` name exists on
   the chain D2's reader walks. On every input where it cannot prove that, it returns 0, and the
   `state` verb decides. It replaces `_resolve_state_file`, whose `-f` test and `cd` into the
   target's parent let two governed writes through (D2).
   - `_lexists p` is `[ -e "$p" ] || [ -L "$p" ]`, the shell twin of `os.path.lexists`. A
     dangling symlink, a directory and a FIFO at the state path all count as present.
   - With `ROOT_ABS` non-empty, a present `$ROOT_ABS/docs/.bkit-memory.json` → 0.
   - An empty target → 1. Its chain is the root alone, already tested.
   - A target that is not absolute (only possible when `ROOT_ABS` is empty), or that holds a `.`
     or `..` segment → 0. `realpath` folds `..` after a missing directory lexically, and the shell
     walk would not.
   - Otherwise `d` starts at `dirname(target)` and climbs while `d` is not present. A directory
     that does not exist yet holds no state file, so skipping it loses nothing. Then
     `d=$(cd "$d" && pwd -P)`, and a failed `cd` → 0. This is `realpath` of the target's parent,
     computed on its existing prefix.
   - With `ROOT_ABS` non-empty and `d` outside it → 1. D2 then reads the root alone (DD-9), and
     the root's state was absent.
   - Walk `d` upward, testing `_lexists "$d/docs/.bkit-memory.json"` at each step, and stop after
     `ROOT_ABS` (or after `/` when `ROOT_ABS` is empty). A present name → 0. Otherwise → 1.
   - **Executed** under `/bin/bash` 3.2.57 in a scratch tree (deleted):
     - a dangling-symlink root state → defer;
     - no root state, `sub/docs/.bkit-memory.json` present, and a target under
       `sub/newdir/deeper/` that does not exist → defer;
     - no state anywhere → allow;
     - a target outside the root, no root state → allow;
     - a target with a `..` segment → defer;
     - an empty target, no root state → allow;
     - an empty `ROOT_ABS` with a state on the target's ancestors → defer, and without one → allow;
     - a relative target → defer.
   - **Residual.** A state file in a directory the process cannot search is absent to both this
     function and D2's reader, so both allow. That is today's behaviour.
5. **Empty target** (DD-8). If `TARGET_PATH` is empty, the gate runs `_find_judge` (step 7) and
   `_read_state` with no `--target`: `active` or `unreadable` → `_refuse judge-error "could not identify the write target"`,
   and `none` → `_allow`.
6. **Exemptions and the `.py` filter** (DD-1, OD-A). Both `case` blocks keep their exact patterns,
   then `[[ "$TARGET_PATH" != *.py ]] && _allow`. No `python3` process is started for an exempt
   write, and no state is read, so an exempt write on an unreadable chain is allowed and the
   broken state file can be repaired.
7. **Judge path.** `_find_judge` sets
   `JUDGE=$(python3 -c 'import os,sys;print(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[1]))),"scripts","h_mad_tdd_judge.py"))' "${BASH_SOURCE[0]}")`,
   unless step 5 already set it. A failure here is an errexit, and the trap turns it into
   `judge-error`.
8. **Governance.** `_read_state --target "$TARGET_PATH"`, the one function steps 5 and 8 share:
   - an empty `ROOT_ABS` → `_refuse judge-error "project root (CLAUDE_PROJECT_DIR) cannot be entered"`.
     The CLI would also reject `--root ""` with a usage error (D10), which refuses the same way;
     the gate check exists so that the message names the cause;
   - `SOUT=$(python3 "$JUDGE" state --root "$ROOT_ABS" [--target …] 2>/dev/null) || SRC=$?`;
   - any non-zero `SRC`, zero lines, more than one line, or a line matching no `TDD-STATE:` form
     (D10) → `_refuse judge-error`;
   - `none` → `_allow`;
   - `unreadable` → `_refuse judge-error "H-MAD state is unreadable (<decoded file>: <error>)"`
     (OD-8, AC-6.9);
   - `active` → continue.
9. **Codex authorship** (OD-9). Under `set -f`, the gate reads `codex-escape=` and `blocker=` from
   the `state` line. It applies no status rule of its own: the judge decides which record blocks
   (D10), and the gate takes `record=` number `blocker` for the hint.
   - If `HMAD_CODEX_UNAVAILABLE` is empty, `codex-escape=no`, and `command -v codex` succeeds, the
     gate emits `_refuse codex-authorship "<today's five-line message>"`, with the blocker's key and
     its state file in the `h_mad_state_write.py … "<file>"` remedy.
   - Both values are percent-decoded by `_pct_decode` before printing, so the hint prints the
     absolute path as today (D10 makes the field absolute). `_pct_decode` is
     `printf '%b' "${1//%/\\x}"`. Executed under `/bin/bash` 3.2.57 on the `quote(…, safe="/._-")`
     encoding of `/a b/"q"\x/%z,é`, it returned that string byte for byte.
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
- `_chain_may_hold_state`, `_read_state` and `_pct_decode` are specified in steps 4, 8 and 9.
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
- `_resolve_state_file`, replaced by `_chain_may_hold_state` (step 4);
- the `jq` dependency and the no-`jq` allow (DD-2);
- the `ACTIVE`/`head -1` read;
- `CODEX_STATUS` from `jq`;
- `DERIVE_SCRIPT` and every `h_mad_derive_test_path.sh` reference (AC-1.1);
- the bare `pytest` run and its `[ -f "$TARGET_PATH" ]` guard (OD-5, AC-6.4);
- every `exit 1`.

5g greps, unit matching lines:
- `grep -c '^\s*exit 1\s*$'` → 0;
- `grep -c 'orchestrator_state'` → 0;
- `grep -c '_resolve_state_file'` → 0;
- `git grep -n "h_mad_derive_test_path.sh" -- h-mad/hooks` → no match.

**DD-7 guard-narrowing differential** (orchestrator OD-E; spec v1.3 AC-6.15; invariant §"Guard
narrowing").
- **Corpus.** {relative, `./`-relative, absolute} × {`tests/x.py`, `fixtures/x.py`,
  `sub/tests/x.py`, `test_x.py`, `x.md`, `x.py`} × {no state, root state with one ACTIVE step5
  record}. Each cell runs through the positional entry point with stdin `/dev/null`, process cwd
  and `CLAUDE_PROJECT_DIR` both at the fixture root, and `PATH` = a bin dir holding a `codex`
  stub, `jq` and `python3`, then `/usr/bin:/bin`. So every gated production cell stops at the
  Codex-authorship refusal under both gates, and the comparison never depends on a test run.
- **Old versus new.** The old gate is `git show <base>:h-mad/hooks/h-mad-tdd-gate.sh`, the new one
  the worktree's. A cell's class is *allow* or *refuse*, read in the chosen form (rc 2, or the
  stdout JSON deny); the old gate's `exit 1` is *refuse*.
- **Old verdicts, executed** at eec0c7a6's gate (identical to 1ef1a782's) under `/bin/bash`
  3.2.57 in a scratch tree (deleted). All 18 no-state cells allow. In the 18 active cells, the old
  gate refuses exactly these 5: relative `tests/x.py`, relative `fixtures/x.py`, and `x.py` in all
  three forms.
- **Expected softened set:** exactly the two active cells relative `tests/x.py` and relative
  `fixtures/x.py`. `./tests/x.py` is not softened, because `./tests/x.py` already matches
  `*/tests/*` today (the old gate allowed it, as it did `./fixtures/x.py`). The three `x.py` cells
  stay refused. Any other softened cell is a defect, and any tightened cell is named.
- **Residual, stated.** The Claude gate's `*/tests/*` and `*/fixtures/*` match the whole absolute
  path, root prefix included, while the Codex gate's `_is_production_python` tests only
  root-relative parts. A project whose root lies under a `tests/` or `fixtures/` directory is
  therefore fully exempt on the Claude side only. That was already true for absolute targets
  before this feature, and DD-7 extends it to relative ones.

### D10 — Line formats (FR-1; the `TDD-STATE:` format the spec owes)

- **Field encoding.** Every variable field value is `urllib.parse.quote(value, safe="/._-")`, so a
  value holds no space, comma, `=` or glob character. `~` stays unquoted, because it is always safe
  in `quote`, and a word produced by an expansion is never tilde-expanded.
  - A **state-file** path (`record=` third field, `unreadable file=`) is the file's absolute
    path, as D2 read it. It is absolute so that the Codex-authorship hint, which prints it as the
    `h_mad_state_write.py` argument, works from any cwd, as today's `$STATE_FILE` does.
  - The ALLOW `test=` path is root-relative POSIX when inside the root, else absolute.
  - The gate decodes a field with `_pct_decode` (D9 step 9) before printing it.
- **`state` verb** (`h_mad_tdd_judge.py state --root <dir> [--target <path>]`), exactly one line on
  stdout, rc 0:

  | Value | Line |
  |---|---|
  | none | `TDD-STATE: none` |
  | active | `TDD-STATE: active codex-escape=<yes\|no> blocker=<B> records=<N> record=<key>,<codex_status>,<state-file>,<fallback>` … (N `record=` fields, chain order) |
  | unreadable | `TDD-STATE: unreadable file=<state-file> error=<exception class name \| not-a-regular-file \| not-an-object>` |

  - `codex-escape=yes` holds exactly when N ≥ 1 and every record's `codex_status` is in
    `ESCAPE_STATUSES` (OD-9).
  - `blocker=B` is the 1-based position of the first record whose `codex_status` is not in
    `ESCAPE_STATUSES`, and 0 exactly when `codex-escape=yes`. The gate names that record in the
    Codex-authorship hint and applies no status test of its own. So every rule over record
    statuses has one implementation, in the judge; v1.0's gate re-implemented the escape set to
    find the blocker.
  - `<fallback>` is the record's `fallback_agent` tag (D13).
  - An exception in the verb prints nothing to stdout, prints a message to stderr, and exits 2.
  - An empty `--root`, or one that is not a directory, is a usage error: rc 2, nothing on stdout.
    It never falls back to the process cwd.
- **`judge` verb** (same arguments), exactly one line, rc 0:
  - `TDD-JUDGE: ALLOW kind=red-measured source=<impl-plan|name-map> test=<quoted path>`;
  - `TDD-JUDGE: DENY kind=<kind> reason=<text>`.

  The reason text has `[[:cntrl:]]` mapped to spaces, so it is one line.
  - If the chain is not `active` at judge time, the verdict is DENY `judge-error`.
  - Any exception is caught and printed as DENY `judge-error` with `reason=<class>: <message>`.
  - The usage-error rule for `--root` is the same as for `state`.
- **Grammar the Claude gate enforces** (bash ERE, whole line):
  - `^TDD-STATE: none$`
  - `^TDD-STATE: unreadable file=[^ ]+ error=[A-Za-z_-][A-Za-z0-9_-]*$`
  - `^TDD-STATE: active codex-escape=(yes|no) blocker=(0|[1-9][0-9]*) records=([1-9][0-9]*)( record=[^ ,]+,[^ ,]+,[^ ,]+,(absent|null|grok|claude|invalid:[^ ,]+))+$`,
    with three cross-checks: the count of `record=` words equals `records=`; `blocker=0` exactly
    when `codex-escape=yes`; and `blocker` ≤ `records`.
  - `^TDD-JUDGE: ALLOW kind=red-measured source=(impl-plan|name-map) test=[^ ]+$`
  - `^TDD-JUDGE: DENY kind=(no-test-resolved|test-missing|venv-escapes-root|pytest-missing|pytest-error|no-tests-ran|no-summary|test-passing|timeout|judge-error) reason=(.+)$`

  Anything else is `judge-error`. That includes an unknown verb's usage error, which argparse
  reports on stderr with rc 2.
  - The active-line ERE was executed under `/bin/bash` 3.2.57 (scratch, deleted) on lines built by
    this encoding. It matched two records with an `invalid:` tag for `false`, a `grok` tag, an
    `invalid:` tag for `""`, and an `invalid:` tag for `{"a":[1,2]}` (encoded
    `invalid:%7B%22a%22%3A%5B1%2C2%5D%7D`). It rejected a record with three fields, and a
    fourth field of `bogus`.
- **Extension rule.** The line is a closed grammar, not a key bag. v1.1 appends the fourth
  `record=` field now (D13). Any later field is appended the same way, and the gate's ERE changes
  in the same commit.

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
- **`h-mad/references/codex-implementer-prompt.md`, the line beginning `Hook: ` and the bullets
  under it.**
  - The `Hook:` line itself goes stale too. Today it reads "PreToolUse hook at
    `~/.claude/hooks/h-mad-tdd-gate.sh` is ARMED during this phase", but this prompt is dispatched
    to Codex, whose writes reach `h-mad/hooks/h-mad-codex-tdd-gate.py`. It is rewritten to name the
    Codex gate for Codex's `apply_patch` and shell writes, and the Claude gate for Claude's
    `Write`/`Edit`. It keeps the `Hook: ` prefix, which is the AC-7.2 locator after the edit.
  - The production bullet reads: the test named by the impl-plan Task, else the name map, and
    "failing" means pytest's summary shows `N failed`.
  - The test bullet names the basename rule (`test_*.py`, `*_test.py`, `conftest*.py`).
  - Spec FR-7 names this file's bullets, not its `Hook:` line; the line is added here, and the
    report routes that to the spec.
- **`h-mad/scripts/h_mad_derive_test_path.sh`'s header comment.** It says it is "Used by
  ~/.claude/hooks/h-mad-tdd-gate.sh", which goes false. It becomes "Used by h_mad_tdd_judge.py".
  This site is in the plan's stale-prose census (2 matching lines in that file) and is not in the
  spec's three-file list.
- **Residual** (spec FR-7). Prose that describes the gate without naming a file is not covered.

### D12 — Fixture tree for the shell-policy differential and the venv ACs

- `tmp/root` is `git init`'d. `root/docs/.bkit-memory.json` holds one step5 record.
- **The builder interpreter** is the test run's own `sys.executable`. pytest is importable in it
  by construction, because it is running the test.
- `root/hematology-paper-writer/.venv/` is made by
  `[sys.executable, "-m", "venv", "--without-pip", "--system-site-packages", <dir>]`. Its
  `bin/python` is then a real symlink to the builder, which leaves the root (the AC-3.3 shape),
  and `pyvenv.cfg` is real. `--system-site-packages` is what lets that venv import pytest.
  - Executed with `/opt/anaconda3/bin/python` (3.11.8) as builder, in a scratch dir (deleted):
    `bin/python -> /opt/anaconda3/bin/python`, `bin/python3 -> python`,
    `bin/python3.11 -> python`, `pyvenv.cfg` holding `include-system-site-packages = true`.
    `bin/python -c 'import pytest'` printed the venv's `sys.prefix` and pytest 9.1.1, and
    `bin/python -m pytest` ran a RED file to `2 failed, 1 subtests passed in 0.02s`.
  - The same build **without** `--system-site-packages` printed
    `<venv>/bin/python: No module named pytest`. v1.0 specified that build for this tree, so
    AC-3.1's RED test could never reach `red-measured` through it. It remains the right build for
    the `pytest-missing` fixtures (AC-4.1), and only for those.
  - **The versioned spelling** is derived from the builder: `f"python{sys.version_info[0]}.{sys.version_info[1]}"`
    (`python3.11` under `/opt/anaconda3/bin/python`). Plan v1.2 writes it as `.venv/bin/python3.14`,
    a name that exists only when the builder is 3.14; a literal `python3.14` row would silently
    stop testing a versioned name under any other builder.
- **The marker shim** (spec AC-3.1, AC-3.2). For the rows that must prove which interpreter ran,
  `bin/python` is replaced by an executable `/bin/sh` script. It appends its own path to a marker
  file named by the fixture (outside the root), then runs `exec <builder> "$@"`. The builder
  has pytest, so the shim is pytest-capable, and the marker proves the selected interpreter ran.
  - AC-3.1: the contained venv's shim; the write is ALLOWED and the marker holds that shim's path.
  - AC-3.2: `.venv` is a symlink to `tmp/outside-venv/`, whose `bin/python` is the same kind of
    shim writing the same marker file. The verdict is DENY `venv-escapes-root`, and the marker
    file does not exist afterwards.
- `root/hematology-paper-writer/.venv/bin/python-evil` is an executable regular file, placed in
  the contained venv's `bin/` directory (the plan's `python-evil` spelling row).
- `root/hematology-paper-writer/tests/test_x.py` is RED.
- `tmp/outside-venv/` is a second venv outside the root, built the same way.
- Each venv-state row mutates a copy of this tree:
  - `.venv` → symlink to `outside-venv`;
  - `.venv/bin` → symlink to `outside-venv/bin`;
  - `pyvenv.cfg` removed;
  - `pyvenv.cfg` replaced by a symlink (to a regular file inside the root, so the row tests the
    link itself and not an escape).
- **The oracle is per row**, because the rows fail containment for different reasons (plan: "a
  fixture asserts that `realpath` follows each symlink … as the rule assumes"):
  - the two directory-symlink rows: `os.path.realpath(<mutated path>)` lies outside the root;
  - `pyvenv.cfg` removed: `os.path.lexists(<cfg>)` is false. A realpath oracle is wrong here: the
    realpath of a missing file under a contained venv stays inside the root;
  - `pyvenv.cfg` a symlink: `os.path.islink(<cfg>)` is true, and `stat.S_ISREG(os.lstat(<cfg>).st_mode)`
    is false.

### D13 — Rebase contract for grok-codex-fallback D2

This section fixes what `grok-codex-fallback` D2 ("TDD gate: typed, fail-closed `fallback_agent`
read") must build on once this feature merges. It does not implement grok's feature. It ships one
field, and it states the rest as a contract for grok's Task 12 (`tdd-gate-fallback-agent`) to be
re-planned onto.

- **Why now.** Plan §"Convention Prerequisites" merges this feature first, and plan R2 says grok's
  "new refusals must use this feature's refusal function". Read-only readings in grok's worktree
  `/Users/kimhawk/orca/skills-grok-codex-fallback`:
  - its HEAD moved during this revision, from `29e055fa` (Task 9 RED) to `199eaf89` (Task 9
    GREEN); both readings are below Task 12;
  - `grep -c fallback_agent h-mad/hooks/h-mad-tdd-gate.sh` there → 0 matching lines, so Task 12
    is not implemented;
  - its gate file's last commit is `dde1c7ad`, the same pre-feature gate this feature rewrites.
- **What grok D2 builds on, and what this feature removes.**

  | grok D2 construct | After this feature |
  |---|---|
  | A `jq` read of `.orchestrator_state[$k].fallback_agent` | No `jq` in the gate (DD-2). The value arrives as the fourth `record=` field of the `state` line |
  | `$ACTIVE`, the first ACTIVE key of the root state file (`head -1`) | No `$ACTIVE`. The `state` line carries every ACTIVE record on the target's chain (OD-8, OD-9) |
  | `exit 1 ;;` arms for BLOCK-GROK and BLOCK-INVALID | No `exit 1`. Every refusal goes through `_refuse <kind> <text>` in the chosen form (D9) |
  | Placement after the BLOCK-CODEX `if`'s `fi` | Placement directly after D9 step 9 and before step 10. Step 9 refuses whenever codex is not out, so code placed after it still runs only when codex is out, which is D2's placement argument unchanged |
  | "With no `jq` on PATH, the hook exits 0 before this block" (grok D2, "Inherited fail-open") | False after DD-2. A missing `jq` no longer stands the gate down (spec v1.3 AC-6.12) |

- **The field this feature ships.** `Record.fallback`, computed in `read_chain` for each ACTIVE
  record (D2) and printed as the fourth `record=` field (D10). The tag rule mirrors grok D2's `jq`
  table, type for type:
  - the record has no `fallback_agent` key → `absent`;
  - the value is JSON `null` → `null`;
  - the value is a `str` equal to `"grok"` → `grok`, and to `"claude"` → `claude`;
  - any other value → `invalid:` followed by the D10 encoding of
    `json.dumps(value, separators=(",", ":"))`. So `false`, `true`, `0`, `""`, `"Grok"`, `"null"`,
    `"codex"`, `{}` and `[]` all reach `invalid:`, and JSON `null` and the string `"null"` stay
    distinct (`null` versus `invalid:%22null%22`), as grok D2 requires.
  - The `isinstance(value, str)` test comes first, so `True == 1`-style Python equalities cannot
    reach `grok` or `claude`.
  - `json.dumps` escapes non-ASCII (`ensure_ascii=True`), where `jq`'s `tojson` does not. grok's
    Task 12 test 2 already builds its expected text with
    `json.dumps(value, separators=(",", ":"))`, so this encoding matches it.
  - The tag is data, and this feature makes no decision on it: no verdict here reads it.
- **Contract for grok's re-planned Task 12.** Each item is a constraint on grok's design, not
  work done here.
  1. **Where the rule lives.** The fold over records is added to the judge, as a line-level field
     on the `state` line (for example `fallback-block=none|grok:<B>|invalid:<B>`, with `B` the
     1-based record position). The gate reads that field and applies no rule of its own. This is
     the single-source rule that moved `blocker=` into the judge (D10).
  2. **Which record governs.** grok D2 reads only `$ACTIVE`. With several ACTIVE records (OD-9),
     the fold is over all of them and does not depend on their order. Any `invalid:` record →
     BLOCK-INVALID, naming the first such record. Otherwise any `grok` record → BLOCK-GROK, naming
     the first such record. Otherwise → fall through. The most restrictive record wins, which
     fails closed.
  3. **When it is read.** Codex is out when `HMAD_CODEX_UNAVAILABLE` is non-empty, or the `state`
     line says `codex-escape=yes`, or `codex` is not on PATH. D9 step 9 refuses every other case
     first.
  4. **Refusal kinds.** BLOCK-GROK is `_refuse fallback-grok "<grok's text>"` and BLOCK-INVALID
     is `_refuse fallback-invalid "<grok's text>"`. The first stderr line therefore begins
     `[H-MAD-TDD-GATE] BLOCK kind=fallback-grok: ` rather than `[H-MAD-TDD-GATE] BLOCK: `. The
     feature key and the state file in the remedy come from the governing record, percent-decoded
     by `_pct_decode`.
  5. **The gate ERE.** If the fold field is added, the active-line ERE in D10 gains it in the same
     commit, with a cross-check that its `B` is ≤ `records`.
- **What grok's Task 12 must re-plan** (read from its impl-plan's Task 12, read-only):
  - its code-structure block (the `jq` filter and the `case` with `exit 1` arms) → a `case` over
    the judge's fold field, with `_refuse` arms;
  - `test_gate_matrix`, `test_absent_null_claude_match_the_base_hook` and every outcome-class
    reader. They read stderr's first line and `exit 1`, and they compare byte for byte with the
    pre-feature base hook. After the merge, the base is this feature's gate, and the prefix and
    the form both change;
  - `test_fallback_read_error_fails_closed`, which shims `jq`. There is no `jq` left to shim. A
    read error is now the `state` verb's `unreadable` or failure, refused `judge-error` at D9
    step 8, before the fallback block runs. The `*)` arm's role, an unforeseen tag, is taken by
    the ERE: an unknown fourth field fails the line, and the gate refuses `judge-error`;
  - its wire-scoped revert WR12, which edits `(.orchestrator_state[$k] // {}) as $r`. That text no
    longer exists. The equivalent revert forces `Record.fallback` to `absent` in the judge;
  - its test harness's `cwd=project` with a relative target (`shared/widget.py`). DD-7 makes that
    target absolute against `CLAUDE_PROJECT_DIR`, which the harness sets to the same directory,
    so the cells keep their meaning.
- **Residual.** This contract transports the value and fixes where the rule over it lives. It
  does not decide grok's FR-2 table, its stderr wording, or its mutation rows.

## Components Changed / Added

| Component | File path | Change type | Purpose |
|---|---|---|---|
| Judge | `h-mad/scripts/h_mad_tdd_judge.py` | new | chain reader, resolver, interpreter selection, scorer, `state`/`judge` CLI, `blocker=` and the `fallback` record field (D1–D7, D10, D13) |
| Codex gate | `h-mad/hooks/h-mad-codex-tdd-gate.py` | modify | lazy judge import, crash guard, `_payload_cwd_base`, chain reader, venv executable lookup (D8) |
| Claude gate | `h-mad/hooks/h-mad-tdd-gate.sh` | modify (rewrite) | stdin-first payload, `_chain_may_hold_state` fast path, `state`/`judge` calls, refusal function, `EXIT` trap (D9) |
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
   - **OQ-D1 host-deadline probe** (D6), in the live Claude Code session V-0 uses. A governed
     production write is attempted whose resolved test sleeps 35 s and then fails. Pass: the gate's
     own decision lands (an ALLOW naming `red-measured`), not a host cancellation. If the host
     cancels first, the registration gains an explicit `timeout`, in the unit the probe shows, and
     the probe re-runs. This is a merge condition.

## Data Model / Schema Changes

- **State file** (`docs/.bkit-memory.json`): no schema change. The judge reads
  `orchestrator_state.<key>.phase` and `.codex_status`.
- **`_parse_tasks` task dict:** `+ "production": list[str]`, `+ "tests": list[str]`.
  - Existing keys are unchanged.
  - Consumers are listed by
    `git grep -n "_parse_tasks" -- h-mad handoff ':!h-mad/tests/fixtures' | grep -v '^h-mad/scripts/h_mad_wire_pin_gate.py'`,
    which gives `h_mad_assemble_tdd.py` (2 matching lines), `h_mad_wire_registry.py` (2) and a
    `SKILL.md` prose line (1). Both code consumers read named keys.
- **`h_mad_tdd_judge.Record`** gains `fallback: str` (D1, D13). Nothing outside the judge
  constructs it.
- **`h_mad_audit_gate.SuiteSummary(passed: int, failed: int, errors: int, no_tests_ran: bool, phrases: FrozenSet[str])`**:
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
  `_safe_shell_command(command, root=None, cwd=None)`, new `_payload_cwd_base`, new
  `_contained_venv_executable`, new `_load_judge`. The removals are listed in D8.
- **Claude gate:** the stdin payload's target is read first, and `$1` only when stdin yields none
  (D9 step 2). Refusal is by `REFUSAL_FORM`: (a)
  rc 2 with the reason on stderr, or (b) rc 0 with one stdout JSON deny. Exit 1 is never used.
- **`h_mad_audit_gate._suite_summary(text) -> Optional[SuiteSummary]`.**
- **`h_mad_wire_pin_gate._parse_tasks(text) -> list[dict]`:** the same list, with two keys added
  per dict.

## Error Handling Strategy

| Where | Failure | Surfaces as |
|---|---|---|
| Judge core | unreadable state file | `Chain("unreadable", …)`, never an exception |
| Judge core | impl-plan unreadable | recorded, name map used, carried into every DENY reason of that call, `test-missing` included (D3 step 8, AC-2.8) |
| Judge core | a state path that is a FIFO, a directory or a dangling symlink | `Chain("unreadable", …)` with `not-a-regular-file` or the `OSError` class; never a blocking read (D2) |
| Judge CLI | empty or non-directory `--root` | usage error, rc 2, nothing on stdout → the Claude gate refuses `judge-error` |
| Judge core | interpreter cannot start (`OSError` from `Popen`) | DENY `no-summary`, the reason naming the error |
| Judge core | budget exhausted | DENY `timeout`, the process group killed |
| Judge CLI `judge` | any exception | DENY `judge-error` line, rc 0 |
| Judge CLI `state` | any exception | no line, stderr message, rc 2 → the Claude gate refuses `judge-error` |
| Codex gate | import failure, or any exception after `--self-check` | `_deny(… kind=judge-error)`, rc 0, parseable JSON (AC-5.4) |
| Codex gate | chain unreadable | `_deny("H-MAD state governing this write is unreadable …")` |
| Claude gate | judge/state rc ≠ 0, zero or two lines, grammar miss | `_refuse judge-error` |
| Claude gate | stdin payload present but unusable (a control character in the target, or the reader failed) | target left empty, `$1` not consulted → the empty-target rule (DD-8) |
| Claude gate | `CLAUDE_PROJECT_DIR` cannot be entered, and the fast path defers | `_refuse judge-error` naming the root (D9 step 8); exempt writes are still allowed |
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
  | `tdd_judge_resolution.json` | Task-match authority (AC-2.5); the `none` rule (AC-2.3); plan notes on every DENY (AC-2.8); the present/missing candidate split (D3 step 5) | skip the authority `if`; `_NONE_VALUE_RE` → never match; drop the notes from the `test-missing` return; run missing candidates |
  | `tdd_judge_venv.json` | containment (AC-3.2): each of the three conjuncts alone | each conjunct → `True` |
  | `tdd_judge_scoring.json` | `pytest-missing` (AC-4.1); `errors ≥ 1` (AC-4.3); rc-blindness (AC-4.4); rule 8 (AC-4.2, the skipped-only fixture) | delete each branch alone; score on `returncode` |
  | `tdd_judge_chain.json` | chain reader (AC-5.2); unreadable decides (AC-6.9); the OD-9 all-records rule (AC-6.10); the non-regular-file rule (spec v1.3 FR-5); `blocker=` (D10) | nearest file only; skip unreadable; `all` → `any`; drop the `S_ISREG` test; `blocker` → 1 |
  | `tdd_judge_wiring.json` | W3 and W4, each in both directions, plus one callee-side mutant each (table below) | per row, alone |
  | `codex_gate_judge_wiring.json` | payload `cwd` base (AC-5.1); W1; W5a; crash guard (AC-5.4); the venv executable lookup (AC-3.4, AC-3.6) | ignore `cwd`; bypass the judge (remove / force ALLOW); nearest-only status; drop the `try`; return the realpath instead of the lexical path |
  | `claude_gate_judge_wiring.json` | `tool_input` read (AC-6.1); stdin-before-`$1` (AC-6.1, the conflicting-input fixture); `state` governance (AC-6.8); non-zero-rc refusal (AC-1.3); the blocking form (AC-6.5/6.6); exemptions-before-governance (AC-6.9, the exempt-write fixtures); the fast path's `-L` half of `_lexists` (AC-6.11a) and its missing-parent handling (AC-6.11b), one mutant per fixture. The AC-6.11b mutant restores v1.0's shape in one edit: no climb, and a failed `cd` returns 1. Each half alone survives, because the climb and the failed-`cd` deferral back each other up; that redundancy is deliberate and stated here. Executed on D9 step 4's scratch function under `/bin/bash` 3.2.57: either half alone → defer on the AC-6.11b fixture, both together → allow; dropping `-L` → the AC-6.11a fixture allows; the empty-target refusal (AC-6.13); the outside-root chain (AC-6.14); W2; W5b; W6 two-tree; each trap member | per row, alone |
  | `audit_suite_summary_line.json` | DD-3 predicate, each word of `{"passed","failed"}` alone; the timed-beats-untimed rule; the SGR strip; the exact-category count rule (AC-4.7, the `2 failed, 1 subtests passed` fixture) | per row, alone |

  The guards named by spec v1.3 AC-8.1 each appear in one row above. The outside-root chain
  guard sits in the judge's `read_chain` (DD-9), and the Claude-gate test observes it; its
  mutant lives in `claude_gate_judge_wiring.json` because that is the test the spec names.

  **Wire mutants W3 and W4** (`tdd_judge_wiring.json`; plan §"Connection enforcement"; codex
  audit must-fix). Each call-site mutant keeps the callee byte-identical, and each callee-side
  mutant is scored against the **judge's** tests only. That second kind is what proves the judge
  reads through the callee and has not grown an equivalent local parser, which a call-site mutant
  alone cannot show.

  | Wire | Remove (call site) → must fail | Force (call site) → must fail | Callee-side, scored on judge tests |
  |---|---|---|---|
  | W3 judge → `_parse_tasks` | `_parse_tasks(text)` → `[]`: AC-2.1 no longer resolves `source=impl-plan` | `_parse_tasks(text)` → `[dict(t, production=[]) for t in _parse_tasks(text)]`, so no Task ever matches and the name map is always asked: AC-2.5 inverts (the failing name-map test ALLOWS) | `_PATHS_FIELD_RE`'s `Production` label alternative → `Productionx` in `h_mad_wire_pin_gate.py`: the judge's AC-2.1 fails |
  | W4 judge → `_suite_summary` | `_suite_summary(out)` → `None`: AC-4.2's RED no longer ALLOWS, and AC-4.4's shim that prints `1 failed` with rc 0 no longer ALLOWS | `_suite_summary(out)` → `SuiteSummary(0, 1, 0, False, frozenset({"failed"}))`: AC-4.2's GREEN reads RED | the `failed` count in `_suite_summary` forced to 0 in `h_mad_audit_gate.py`: the judge's AC-4.2 RED fails |

  The existing `audit_suite_gate.json` (9 mutations) and the three `wire_pin_*.json` specs anchor in
  files this feature edits, so `--check-anchors` runs in each edit's commit.
  - Reading at skills `76e7af19` (re-run for v1.1; v1.0's `1ef1a782` reading was the same):
    `python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/*.json | grep '^ANCHORS: ANCHORS_OK'`
    → `specs=99 mutations=907 ok=907 drifted=0`.
  - `git grep -l 'h-mad-codex-tdd-gate\|h-mad-tdd-gate' -- h-mad/tests/mutation-specs | wc -l`
    → 0 files: no spec anchors in either gate today.
  - The `specs=`/`mutations=` figures grow by construction and are re-read at 5g, never carried.

## Test Plan

**New test modules** (paths resolved from `Path(__file__)`):

- **`h-mad/tests/test_h_mad_tdd_judge.py`**, the core:
  - AC-2.1–2.9, with AC-2.8's two routes (a missing name-map test → `test-missing`, a passing
    one → `test-passing`), each asserting `impl-plan unreadable` in the reason;
  - the mixed-candidate fixtures (D3 step 5): Task 1's test missing and Task 2's RED → ALLOW
    naming Task 2's test; Task 1's missing and Task 2's GREEN → DENY `test-passing` naming Task 1's
    test as `missing`;
  - AC-3.1–3.3, on D12's tree: AC-3.1 and AC-3.2 read the marker file, AC-3.3 uses the real
    `bin/python` symlink;
  - the non-regular state paths (spec v1.3 FR-5): a FIFO, a directory and a dangling symlink, each
    → `unreadable`, and the FIFO case returning within 1.0 s;
  - the `fallback` tag table of D13, one row per value, round-tripped through `format_state_line`
    and the D10 ERE;
  - AC-4.1–4.6, with AC-4.5 run through `judge(..., budget_s=1.0)` against a 30 s sleeper shim,
    asserting `timeout` within 1.0 s + a 5.0 s margin and no surviving shim process;
  - the D7 grammar rows, including the coloured, the `2 passed`/stray-`1 failed`, the two
    measured `subtests` and the `3 apples` rows;
  - the D10 line grammar, round-tripped through the formatters;
  - the 3.9 floor: `ast.parse(src, feature_version=(3, 9))` over the four modules in D1;
  - the corpus differential of AC-2.9: same task ids, same order, over the tracked impl-plan
    corpus.
- **`h-mad/tests/test_h_mad_codex_tdd_gate_judge.py`**, the Codex gate:
  - AC-1.2, with 11 kinds; `timeout` runs at the default budget, about 40 s;
  - AC-3.4, AC-3.6;
  - AC-5.1, AC-5.2, AC-5.4, with a `TMPDIR`-based payload `cwd` (unresolved `/var/…` against a
    resolved root) for `_payload_cwd_base`;
  - W1 and W5a;
  - the shell-policy differential with its published accounting.
- **`h-mad/tests/test_h_mad_tdd_gate_judge.py`**, the Claude gate:
  - AC-1.2, with the Claude-Code-shaped payload and 11 kinds;
  - AC-1.3, one stub per fixture;
  - AC-6.1 with its conflicting-input fixture (stdin names one path, `$1` another; the stdin
    path is decided), AC-6.3, AC-6.4, AC-6.5 or AC-6.6 per the chosen form, AC-6.8, AC-6.10;
  - AC-6.9: the production `.py` refusal, and the three exempt writes on the same unreadable
    chain (the state file itself, `tests/test_x.py`, `notes.md`), each alone and each allowed;
  - AC-6.11 (a) and (b), each alone; AC-6.12 (no `jq` on PATH); AC-6.13; AC-6.14;
  - AC-6.15 and the DD-7 differential (D9), publishing its softened rows;
  - a control-character stdin target with `$1` also given → the empty-target rule, never `$1`;
  - an unenterable `CLAUDE_PROJECT_DIR` with a state on the target's chain → `judge-error`;
  - the Codex-authorship hint names the blocker record's key and its absolute state file, for a
    state path containing a space;
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
so the plan's h-mad readings stand) unless stated otherwise. At `76e7af19`, where v1.1's new
readings ran, `git log --oneline 1ef1a782..HEAD -- h-mad handoff` is again empty, so the two
stamps read the same h-mad tree:

- The two hooks, `_parse_tasks`, `_FIELD_RE`, `_suite_summary` and `run_suite` were read in full
  at their current text.
- The 21 existing test functions that spec v1.2 and plan v1.2 name (the 13 of AC-6.2's list, the
  5 of plan P7, and the 3 audit-suite tests of plan §"Regression census") each exist. Checked by
  one `grep -ln "def <name>\b" h-mad/tests/*.py` per name: 21 names, 1 file each.
- Tests do pin substrings of the Codex gate's reason text. v1.0 said none did, because it
  searched only for the old full phrases; that zero was the search's, not the tree's.
  `git grep -n 'permissionDecisionReason"\]' -- h-mad/tests handoff` at skills `76e7af19` → 6
  matching lines, all in `h-mad/tests/test_h_mad_codex_runtime.py`. Each survives D8:
  - `"failing test"`, twice (production writes with no derivable or no failing test): every D8
    judge DENY begins "H-MAD Phase 5 requires a failing test before …";
  - `"apply_patch"` (the shell-policy deny): that message is unchanged;
  - `"exit 1"` (`test_codex_hook_rejects_pytest_no_tests_collected_as_red`): AC-5.3's named
    change, to `no-tests-ran`;
  - `"identify"` (an unparseable patch): that message is unchanged;
  - `"state"`, lower-cased (`test_codex_hook_fails_closed_on_malformed_state`): D8's unreadable
    deny begins "H-MAD state governing this write is unreadable".
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
  - Every rule over ACTIVE records lives only in the judge: the OD-9 escape (`codex-escape=`),
    the blocker (`blocker=`), and, under D13's contract, grok's fallback fold. The gate applies
    none of them.
  - The payload-`cwd` rule has one statement, `_payload_cwd_base` (D8).
  - The registry's second `Production` grammar is the stated residual (D-A).
  - `_suite_summary` stays the audit gate's parser and is shared, not copied.
- **Standalone; no new external dependency.**
  - stdlib, `bash` and `pytest` only. `jq` is dropped from the Claude gate, which is a removal.
  - `codex` is still probed with `command -v`, as today, which is not an invocation.
- **Portable time bounds.** `Popen.communicate(timeout=…)` with `killpg`. No `timeout`/`gtimeout`.
- **Doc-template superset.** Every Phase-4 section is present. The shape check runs at save.
- **Operator-override preservation; backward compatibility.**
  - The audit gate's pass/fail logic changes only as spec v1.3 FR-4 lists: a failures-without-passes
    summary and a failing `subtests` summary move from `UNREADABLE` to `FAIL`, and a coloured red
    summary moves from PASS to FAIL. All three block. `2 passed, 2 subtests passed` keeps PASS.
  - Committed stamps are not re-derived (plan §"Stamps"). No PASS flips.
- **Marker discipline.** No orchestrator transition is added.
- **Mutation verification.** Every mutation is re-read before it is scored (harness).
  `--check-anchors` runs in the same commit as each edit to an anchored file.
- **Test discrimination.** Each new pin names the observation that differs:
  - AC-6.1: `(0,'','')` today versus a refusal;
  - AC-5.2: allow today versus `test-passing`;
  - D7: `(1, 0)` today versus FAIL for the coloured row.

  Each is run red against the unfixed tree (plan P3, `reproduce.py`).
- **Guard narrowing.** Two softenings, each with its old-versus-new differential and a published
  expected softened set:
  - the shell-policy relaxation (D8 "Differential", D12), whose expected set now includes the
    H-MAD control-allowlist row (OD-C);
  - DD-7's relative exemption (D9 "DD-7 guard-narrowing differential"), whose expected set is
    exactly two cells, measured against the old gate.
  - The stdin-first target read (OD-B) is not a softening: when both sources name a target, the
    gate decides the one the host actually writes.
- **Connection enforcement.** W1–W6 are mutated in both directions (plan table); W3 and W4 carry
  their concrete call-site mutants and a callee-side mutant each (§"Test Strategy"), and W6 uses two
  trees.
- **Incident replay.** V-1r replays HemaSuite `1fbf8022`/`31bfcfe4` against the worktree gate. It
  is a merge condition.
- **Assumption verification; behavioural premises carry their command.**
  - Each load-bearing assumption was executed here, and its command sits beside its reading:
    `pgrep` survivors, bash 3.2 constructs, the grammar rows, the `none` controls, today's
    `_suite_summary` readings, the latency figures.
  - Not executed: the host hook timeouts (OQ-D1, now a 5g merge condition) and the live V-0.
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

- **OQ-D1 (operator), narrowed.** The Claude half is now a measured merge condition: the 5g
  "OQ-D1 host-deadline probe" (§"Implementation Order", D6). The Codex half stays open. The Codex
  gate is not registered on this machine (D6), so there is no live host to probe. Whoever
  registers it must also measure that the Codex host lets a 40 s hook finish, and
  `codex-runtime.md`'s existing `step5:codex_tdd_hook_unverified` halt covers the case where
  activation cannot be shown.
- **OQ-D2 (spec).** Should the value axis read `` `path.py::symbol` `` as `path.py` (D5 residual,
  1 corpus line affected)?
- **Carried:** plan OQ-1 (no `.venv` and no pytest → `pytest-missing`) and OQ-3 (`2 passed, 1 error`
  scores PASS) stand unanswered.

## Version History
- v1.0: Initial design (2026-09-28) from spec v1.2 and plan v1.2 at skills 1ef1a782: judge h-mad/scripts/h_mad_tdd_judge.py with state/judge verbs; TDD-STATE and TDD-JUDGE line formats (D10); 40 s whole-judge budget with process-group kill (D6); summary-line grammar with SGR strip and closed word set (D7); Claude gate refusal function, REFUSAL_FORM literal and EXIT trap (D9); venv shell branch for -m pytest only (D8). DD-1..DD-9 depart from plan or spec wording, each with its revert. OQ-D1 (host hook timeouts), OQ-D2 raised.
- v1.1: Answers design audit cycle 1 (codex p1: 9 must, 1 should; teammate: 3 must, 12 should) against spec v1.3 in the working tree, applying orchestrator OD-A..OD-F (2026-09-28). OD-A: DD-1 kept (exemptions before governance), exempt-write fixtures, Codex-side asymmetry stated. OD-B: stdin target first, $1 fallback only, bounded tty-safe reader, control-character targets unidentifiable. OD-C: DD-6 withdrawn; contained venv executable returned lexically and run through the existing argv rules, control-allowlist row added to the expected softened set. OD-D: open lowercase category grammar with exact-category counts; measured pytest 9.1.1 subtests lines and table rows. OD-E: DD-7 kept with a measured old-versus-new differential (two softened cells). OD-F: D13 rebase contract for grok-codex-fallback D2 and the fourth record field. Also: _chain_may_hold_state fast path replaces _resolve_state_file; non-regular state paths unreadable via O_NONBLOCK open plus fstat; plan notes on every DENY (AC-2.8); present/missing candidate split; blocker= and absolute state-file fields; empty --root a usage error; _payload_cwd_base; W3/W4 remove, force and callee-side mutants; D12 fixture rebuilt (system-site-packages venv, marker shim, per-row oracle, derived versioned spelling); OQ-D1 Claude half made a 5g merge condition; DD-10 and DD-11 added; false reason-pin absence corrected.
