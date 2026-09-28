# Spec: codex-tdd-gate-defects

## Executive Summary

Both H-MAD Phase-5 TDD gates (`h-mad/hooks/h-mad-codex-tdd-gate.py` for Codex and
`h-mad/hooks/h-mad-tdd-gate.sh` for Claude Code) must permit a production write when, and only
when, a failing test has been measured for it. They must deny with a named reason in every other
case. One shared judge serves both gates. It resolves the test from the active impl-plan Task, then
from the name map. It runs pytest under a repo-contained project interpreter. It scores pytest's
summary line, never its exit code. Before any Claude-gate blocking form is changed, a live probe
measures whether Claude Code honours the gate's current `exit 1`.

## Goal

When a Phase-5 feature is active, a legitimate GREEN write is allowed, and every write without a
measured failing test is refused, on either host, including in the HemaSuite sub-project layout.

## Binding decisions and where this spec goes beyond them

The brainstorm (`docs/01-plan/features/codex-tdd-gate-defects-brainstorm.md`, v1.1, commit
`76b2501`) is operator-approved. Its decisions **D1–D4** bind this spec. Measuring the tree for
this spec surfaced defects and conflicts that D1–D4 do not decide. Each one is written below as an
**open decision (OD)**. The spec carries the recommended resolution so that its ACs are testable.
Every AC that depends on an OD is tagged with it, and the operator must confirm or overturn each OD
before the plan is audited. None of them weakens D1–D4.

| OD | Conflict or gap (measured) | Recommended resolution used by this spec |
|---|---|---|
| OD-1 | D2 says a venv interpreter is trusted only if "its realpath stays inside the git root". A standard venv's `bin/python` is a symlink to the base interpreter. For HemaSuite, `realpath(hematology-paper-writer/.venv/bin/python)` resolves into `/opt/homebrew/Cellar/python@3.14/…`, outside the root. Read literally, D2 rejects the one interpreter it exists to admit. | Containment is checked on the **venv directory**, not on the interpreter's last symlink hop (FR-3). |
| OD-2 | The brief says `_project_root` makes the `hematology-paper-writer/` prefix present, and calls Codex's cwd diagnosis wrong. Measured: the gate resolves a relative patch target against the git root, not against the payload `cwd`. A cwd-relative `tools/x.py`, sent from a sub-project cwd, reproduces the blocked report's exact denial: "requires a failing test before tools/x.py; no derived test file exists". | A relative target resolves against the payload `cwd` when that is a directory inside the project root. Otherwise it resolves against the root, as today (FR-5). |
| OD-3 | The two gates read state differently. `_target_phase5_status` (Codex gate) takes the **nearest** `docs/.bkit-memory.json` above the target. `_resolve_state_file` (Claude gate) takes the **root** file first. In HemaSuite the step5 record lives in the root `docs/.bkit-memory.json`, while `hematology-paper-writer/docs/.bkit-memory.json` holds no step5 record. Measured: with the target correctly placed in the sub-project, the Codex gate **allows the write with no test run**. Fixing OD-2 alone therefore opens a silent fail-open. | One chain reader: a target is governed if any state file on the chain from the target's directory up to the project root holds a step5 record. Any unreadable file on the chain means `unknown` (FR-5). |
| OD-4 | The Claude gate reads a top-level `file_path` from stdin. Claude Code sends `tool_input.file_path`. Measured: a Claude-Code-shaped payload yields rc=0 with no stderr on a step5 fixture where Codex is available. The installed hook (`$HOME/.claude/hooks/h-mad-tdd-gate.sh`, a symlink to the tracked file, registered with no positional argument) therefore stands down on every Claude write. This is the measured reason the orchestrator's 2026-09-28 D4 probe "exited 0 before reaching any BLOCK branch". | The Claude gate reads `tool_input.file_path`, falling back to the top-level `file_path` and then to the positional argument (FR-6). The D4 probe is re-specified so that it does not depend on this fix (FR-0). |
| OD-5 | The same fail-open defect class exists on the Claude side and is not named by D3. The Claude gate runs bare `pytest` scored on rc, and only when the target already exists. Measured: with a **passing** test and no `pytest` on PATH, it exits 0. | The Claude gate uses the shared judge (FR-1…FR-4), so D3 scoring applies to both gates (FR-6). |
| OD-6 | D3 denies on a collection error. A RED test that imports a not-yet-written module at top level produces `1 error`, not `N failed`. The GREEN write that creates that module would then be denied. HemaSuite's #28 plan already writes some RED tests to import "inside its body", which avoids this. | D3 is kept as written: a collection error is DENY `pytest-error`. The deny reason tells the author to move the import into the test body (FR-4, AC-4.6). |
| OD-7 | The brainstorm says reuse `h_mad_wire_pin_gate._parse_tasks` and `h_mad_audit_gate._suite_summary`, and that the change touches only "the hook, its tests, and the `codex-runtime.md` trust section". Neither function can be reused unchanged. `_parse_tasks` captures only `Task shape`/`WIRE`/`WIRE-PIN`, because its `_FIELD_RE` has no Production/Test label. `_suite_summary("1 failed in 0.03s")` returns `None`, because `_SUITE_RE` requires `passed`, and it drops `error` counts. | Extend both functions in place, so there is still exactly one parser each. Their existing callers keep their current results, except for the one change to the audit gate named in FR-4. The file scope grows to include `h-mad/scripts/h_mad_wire_pin_gate.py` and `h-mad/scripts/h_mad_audit_gate.py` (FR-2, FR-4). |

## Measured premises

Readings were taken at skills `ae7593a1` and HemaSuite `ffa87323` on 2026-09-28. The scratch
probes were deleted after running, so the committed re-run belongs under
`docs/03-analysis/probes/codex-tdd-gate-defects/` and is owed by the orchestrator. Beside it
already sits the blocked Codex report, `hemasuite-t7_green.blocked1.report.md`.

- **D1 (tree).** `h-mad/scripts/h_mad_derive_test_path.sh` maps a path only when it begins with
  `hematology-paper-writer/`, `clinical-statistics-analyzer/` or `shared/`, and it returns
  `<project>/tests/test_<basename>.py`. Examples:
  - `hematology-paper-writer/cli/_parser.py` → `hematology-paper-writer/tests/test__parser.py`, which does not exist.
  - An **absolute** path → empty.
  - `tools/review_round/guideline_excerpts.py` → empty.

  The Claude gate passes Claude Code's absolute path to the derive script, so every non-exempt
  `.py` write that reaches it hits "cannot derive". Both gates call this script. The Claude gate
  uses `DERIVE_SCRIPT="$HOME/.claude/skills/h-mad/scripts/h_mad_derive_test_path.sh"`, and the
  Codex gate uses `_derived_test`.
- **D2 (tree).** `_trusted_executable` accepts a token only if the token's **unresolved** parent is
  in `TRUSTED_BIN_DIRS`, which is `/bin`, `/usr/bin`, `/usr/local/bin`, `/opt/homebrew/bin` and
  the hook interpreter's resolved directory. It also accepts the bundled `hmad-dispatch`.
- **D3 (reproduced).** Setup: a step5 fixture whose name-mapped test file **passes**, with the
  Codex gate run by `/opt/homebrew/bin/python3` (3.14.7, `No module named pytest`). Result: rc=0,
  empty stdout, and the write is **allowed**. `_test_exit` discards pytest's output and the
  refusal condition is `test_exit != 1`.
- **pytest 9.1.1 `-x -q --no-header` final lines (measured).**

  | Test file | rc | Final line |
  |---|---|---|
  | RED | 1 | `1 failed in 0.01s` |
  | GREEN | 0 | `1 passed in 0.00s` |
  | Import error | 2 | `1 error in 0.06s` |
  | Empty | 5 | `no tests ran in 0.00s` |

  A missing pytest gives rc=1 with no summary line.
- **D4 (tree).**
  - `h-mad/hooks/h-mad-tdd-gate.sh` has 5 lines matching `^\s*exit 1\s*$`, one per `BLOCK:` message.
  - It has 0 lines containing `exit 2` or `permissionDecision`.
  - Command: `grep -c` on the file, unit = matching lines.
- **Field labels (measured).** The corpus is 83 tracked, non-`archive/` `*.impl-plan.md` files
  across HemaSuite and skills. Matching lines per label spelling:

  | Label | Lines |
  |---|---|
  | `**Test file**:` | 306 |
  | `**Production file**:` | 273 |
  | `**Production files**:` | 46 |
  | `**Test**:` | 21 |
  | `**Production**:` | 18 |
  | `**Test files**:` | 13 |
  | `**Test:**` (colon inside the bold) | 4 |

  Among the `Production file`/`Test file` lines, 0 carry an unbackticked `.py` path and 1 is a
  `none (…)` value that still carries a backticked `.py`.

## Functional Requirements

### FR-0: Measure the Claude gate's blocking contract first (D4)

- **Description**: FR-6's blocking form is not specified until one live probe has settled whether
  Claude Code refuses a Write when a PreToolUse hook exits 1. Record the 2026-09-28 probe as
  **inconclusive**: the hook exited 0 before any BLOCK branch ran. OD-4 is the measured cause,
  because the installed gate never receives Claude Code's `tool_input.file_path`. The installed
  gate therefore cannot provide the probe's precondition until FR-6 lands. So the probe measures
  the contract with a throwaway sentinel hook, and it has controls.
- **Procedure**: this is a verification step, V-0, not a pytest AC. Run it in a scratch directory
  outside every repository, with a project-local hook registration that is deleted afterwards.
  - Arm E1: the hook reads stdin JSON. If `tool_input.file_path` ends in `SENTINEL_E1.py`, it
    writes a reason to stderr and runs `exit 1`. Otherwise it runs `exit 0`.
  - Arm E2 (positive control): the same hook, but with `exit 2`.
  - Arm E0 (negative control): the same hook, but with `exit 0` in both cases.
  - **Precondition for every arm**, checked before any real tool call: capture a real Claude Code
    PreToolUse payload for a Write of the sentinel file. Take it from a logging hook, not from
    hand-written JSON. Replay it into the arm's hook by hand and read the rc: E1 must give 1, E2
    must give 2 and E0 must give 0. If the rc is anything else, the arm is **not run** and the
    probe records `UNMEASURED` for it.
  - Then ask a Claude Code session to Write the sentinel file, and record whether the file exists
    afterwards.
- **Outcomes** (the probe's only readings):
  - `E1_BLOCKS`: E1 absent, E2 absent, E0 present. `exit 1` blocks.
  - `E1_DOES_NOT_BLOCK`: E1 present, E2 absent, E0 present. This confirms the defect.
  - `INCONCLUSIVE`: any other combination, or any arm `UNMEASURED`. Nothing in FR-6's
    blocking-form ACs is implemented until a re-run yields one of the two readings above.
- **Acceptance Criteria**:
  - AC-0.1: The probe's recipe and its one reading are committed under
    `docs/03-analysis/probes/codex-tdd-gate-defects/`, together with the Claude Code version it ran
    on. The reading is stamped at the skills sha, the capture of the replayed payload is stored,
    and the three hand-replay rcs are recorded.
  - AC-0.2: The recorded reading is exactly one of `E1_BLOCKS`, `E1_DOES_NOT_BLOCK` or
    `INCONCLUSIVE`, and FR-6 selects its branch from it (AC-6.5 or AC-6.6).

### FR-1: One shared judge serves both gates (D1)

- **Description**: One Python unit under `h-mad/scripts/` decides whether a governed production
  write may proceed. The Codex gate imports it. The Claude gate runs its CLI. Neither gate keeps
  its own resolver, interpreter selection or scorer. The design names the file. The contract is:
  - **Input**: the project root, the target as an absolute path, and the ACTIVE step5 features with
    the state file each came from (FR-5).
  - **Output**: exactly one verdict, `ALLOW` or `DENY`, carrying a `kind` from the closed set below
    and a human-readable `reason`.

  | `kind` | Verdict | Meaning | Caller's action |
  |---|---|---|---|
  | `red-measured` | ALLOW | A resolved test file's pytest summary shows `N failed` with N>0 and 0 errors (FR-4). | Permit the write. |
  | `no-test-resolved` | DENY | No Task matched and the name map yielded nothing. The reason names the impl-plan path(s) consulted, or states that none exists, and the name-map result. | Refuse and surface the reason. |
  | `test-missing` | DENY | A source resolved a path but no such file exists. The reason says "author the failing test first". | Same. |
  | `venv-escapes-root` | DENY | The nearest `.venv` fails containment (FR-3). | Same. |
  | `pytest-missing` | DENY | The run printed `No module named pytest`. | Same. |
  | `pytest-error` | DENY | The summary shows ≥1 `error`. | Same. |
  | `no-tests-ran` | DENY | The summary is `no tests ran`. | Same. |
  | `no-summary` | DENY | No summary line was parsed. | Same. |
  | `test-passing` | DENY | The summary shows 0 failed and ≥1 passed: nothing is RED. | Same. |
  | `timeout` | DENY | The pytest run exceeded its bound. | Same. |
  | `judge-error` | DENY | The judge itself raised, or its CLI output was not exactly one well-formed verdict line. | Same, fail-closed. |

- **CLI contract**: the CLI prints exactly one line to stdout:
  - `TDD-JUDGE: ALLOW kind=red-measured source=<impl-plan|name-map> test=<repo-relative path>`, or
  - `TDD-JUDGE: DENY kind=<kind> reason=<text>`.

  The caller reads the token, never `$?`. Zero lines, more than one line, an unknown verb or an
  unknown `kind` all mean DENY `judge-error`.
- **Acceptance Criteria**:
  - AC-1.1: `git grep -n "h_mad_derive_test_path.sh"` over `h-mad/hooks/` returns no match.
    Both hooks reach the name map only through the shared judge.
  - AC-1.2: For each of the 11 `kind` values, a fixture drives the Codex gate through stdin JSON and
    asserts the exact verdict and `kind`. The same fixtures drive the Claude gate through stdin JSON
    in Claude Code's payload shape. `judge-error` is exercised through each gate's own failure path:
    the Codex import raises, and the Claude CLI's output is malformed.
  - AC-1.3: A stubbed judge CLI prints each of these, and each one yields a Claude-gate DENY with
    `kind=judge-error`: an empty line, two verdict lines, `TDD-JUDGE: MAYBE`, and a DENY whose
    `kind` is outside the set.

### FR-2: Test resolution — impl-plan Task first, then the name map, then deny (D1)

- **Description**: Resolution follows these rules, in order.
  1. **Plan location.** For each ACTIVE feature `F` whose record came from
     `<S>/docs/.bkit-memory.json`, read `<S>/docs/01-plan/features/F.impl-plan.md`.
  2. **Parsing.** Parse with `h_mad_wire_pin_gate._parse_tasks`, extended so that each task dict
     also carries `production` and `tests`, which are lists of path strings. Do not add a second
     parser.
     - **Label axis.** A Production label is `Production file`, `Production files` or
       `Production`. A Test label is `Test file`, `Test files` or `Test`. Bold is optional, the
       colon may sit inside or outside the bold, and matching ignores case.
     - **Value axis.** An entry is a backtick-quoted token ending in `.py`. A value whose first
       word is `none` has no entries, even when it goes on to quote a path.
     - **Residuals, stated.** A label written `Tests` (plural, with no `file`) is not read: the
       corpus uses it for prose counts such as "**Tests** (5 functions, …)". A path continued on the
       next line is not read. An unbackticked path is not read, and the measured corpus has 0 of
       them.
  3. **Matching.** An entry `P` matches the target `T` when some directory `B` exists such that
     `B` is `T`'s parent or an ancestor of it, `B` is the project root or lies below it, and
     `(B / P).resolve() == T`. That Task's test entries then resolve against the same `B`. `B` is
     the base the plan's paths are relative to. For HemaSuite that is `hematology-paper-writer/`
     while the plan itself sits at the git root.
  4. **Multiple matches.** A production file can be named by several Tasks. In the #28 plan,
     `tools/references/restoration.py` belongs to two. The candidate set is then the union of their
     test entries, in plan order.
  5. **Authority of a Task match.** If any Task matched, the name map is **not** consulted. If none
     of the candidates exists, the verdict is `test-missing`.
  6. **Name-map fallback.** If no Task matched, or no impl-plan exists, or it cannot be read or
     decoded, call the name map with the **root-relative** path of `T`. Its result is resolved
     against the root. A read or decode failure is carried into any later DENY reason, as
     `impl-plan unreadable: <error class>`.
  7. **Deny.** If neither source yields a path, the verdict is `no-test-resolved`, and the reason
     names the impl-plan path(s) tried and the name-map outcome.
- **Acceptance Criteria**:
  - AC-2.1 (HemaSuite layout): the fixture is a git root holding `docs/.bkit-memory.json`, whose
    step5 record is `feat`, and `docs/01-plan/features/feat.impl-plan.md`. The plan's Task lists
    `` `tools/review_round/guideline_excerpts.py`, `cli/_parser.py` `` as Production and
    `` `tests/test_certificate_lock_removed.py` `` as Test, with paths relative to
    `hematology-paper-writer/`. For a write to
    `hematology-paper-writer/cli/_parser.py`, the resolved test is
    `hematology-paper-writer/tests/test_certificate_lock_removed.py`, with `source=impl-plan`.
  - AC-2.2: Each label spelling from the axis resolves the same, with one fixture per spelling. A
    `**Tests** (5 functions, …)` line in the same Task contributes no entry.
  - AC-2.3: A Task whose Production value is `` none (writes `docs/…/derive_readings.py`) `` does
    not match a write to that path.
  - AC-2.4: Two Tasks name the same production file with different test files. The first test
    passes and the second fails, so the verdict is ALLOW `red-measured` and names the second file.
    The same fixture with both tests passing gives DENY `test-passing`, and the reason names both
    files.
  - AC-2.5: A Task matches but its test file is absent, while a name-map file does exist and fails.
    The verdict is DENY `test-missing`: the name map is not consulted.
  - AC-2.6: With no Task match, the name-map fallback resolves `hematology-paper-writer/tools/w.py`
    to `hematology-paper-writer/tests/test_w.py`, `source=name-map`. It does so whether the gate
    received an absolute or a relative target.
  - AC-2.7: With no Task match and an unmapped path, the verdict is DENY `no-test-resolved`, and the
    reason contains both the impl-plan path and the literal name-map outcome.
  - AC-2.8: The impl-plan file holds invalid UTF-8, so the name map is used. Its failing test
    allows the write. When no name-map test exists either, the DENY reason contains
    `impl-plan unreadable`.
  - AC-2.9: `h-mad/tests` tests for `h_mad_wire_pin_gate` and `h_mad_assemble_tdd`, which imports
    `_parse_tasks`, pass unmodified.

### FR-3: Project interpreter — trusted only when its venv stays inside the root (D2; OD-1)

- **Description**:
  - **Selection.** For each candidate test file, walk from the file's directory up to the project
    root, inclusive. The first directory `D` that holds `.venv/bin/python` supplies the
    interpreter.
  - **Containment** [OD-1]. The venv is contained when `realpath(D/.venv)` and
    `realpath(D/.venv/bin)` both lie inside `realpath(project root)`, and `D/.venv/pyvenv.cfg` is a
    regular file. The interpreter's final symlink hop to its base interpreter is **not** required
    to be contained, because every standard venv's hop leaves the root.
  - **Failure.** If the nearest venv fails containment, the verdict is DENY `venv-escapes-root`.
    The judge never skips to a more distant venv or to another interpreter.
  - **No venv.** If no venv is found, the judge's own interpreter (`sys.executable`) runs pytest.
  - **Shell policy.** The Codex gate's shell policy (`_trusted_executable` / `_safe_shell_command`)
    also accepts a token naming `<D>/.venv/bin/python*` under the same containment rule. Relative
    tokens resolve against the payload `cwd` (OD-2). The existing argv rules still apply, so only
    `python -m pytest …` and the H-MAD control allowlist pass.
  - **Residuals, stated.** `.venv/bin/pytest` is still refused. Venvs not named `.venv`, such as
    `venv/` or `env/`, are not discovered. A `.venv/bin/python` inside a contained venv that
    symlinks to an arbitrary binary outside the root is accepted. That is the same trust already
    extended to repo test code (see `h-mad/references/codex-runtime.md` §"Trust boundary").
- **Acceptance Criteria**:
  - AC-3.1 (HemaSuite layout, nested venv): the fixture places a contained venv at
    `hematology-paper-writer/.venv`. Its `bin/python` is a shim that runs an interpreter with
    pytest, and the resolved RED test sits under `hematology-paper-writer/tests/`. The write is
    ALLOWED, and a marker the shim writes proves the venv interpreter ran pytest.
  - AC-3.2 (symlink escape): `hematology-paper-writer/.venv` is a symlink to a venv directory
    outside the root. The verdict is DENY `venv-escapes-root`, and the shim's marker is not written.
  - AC-3.3 [OD-1]: the fixture is a contained venv whose `bin/python` is a symlink to an
    interpreter outside the root, which is the real HemaSuite shape. It is accepted. This AC flips
    to DENY if the operator keeps D2's literal wording, and then AC-3.1 is the only allowed shape.
  - AC-3.4: A Codex `shell_command` payload `hematology-paper-writer/.venv/bin/python -m pytest
    tests/test_x.py` with `cwd` set to the sub-project is allowed during step5 when the venv is
    contained. It is denied when the venv escapes.
    `hematology-paper-writer/.venv/bin/python -c "open('x','w')"` is denied in both cases.
  - AC-3.5: The existing test `test_codex_hook_rejects_untrusted_executable_paths` passes
    unmodified.

### FR-4: Score on pytest's summary line, never on rc (D3)

- **Description**: The judge runs `<interpreter> -m pytest <test> -x -q --no-header` with a bounded
  timeout, capturing stdout and stderr. The design owns the bound's value.
  - **Working directory.** The run's cwd is the base `B` from FR-2 for an impl-plan source, and the
    project root for a name-map source.
  - **Parser.** The summary is parsed by the audit gate's scorer, `h_mad_audit_gate._suite_summary`,
    extended in place [OD-7]. It must read `failed`, `passed` and `error`/`errors` counts
    independently, so that `1 failed in 0.01s` and `1 error in 0.06s` both parse. It must also
    report `no tests ran`.
  - **Classification**, first match wins:
    1. Timeout → `timeout`.
    2. `No module named pytest` in the output → `pytest-missing`.
    3. No summary → `no-summary`.
    4. `no tests ran` → `no-tests-ran`.
    5. errors ≥ 1 → `pytest-error`.
    6. failed ≥ 1 → `red-measured`.
    7. passed ≥ 1 → `test-passing`.
  - **The rc** appears in DENY reasons for diagnosis only, and never selects a branch.
  - **Audit-gate change.** The one change to the audit gate: `run_suite` now scores a summary with
    failures but no passes, such as `3 failed in …`, as `FAIL`. Today it scores it
    `UNREADABLE no_summary`.
- **Acceptance Criteria**:
  - AC-4.1 (fail-open regression, the brief's reproduction): the fixture's resolved test file
    **passes**, and pytest runs under an interpreter with no pytest, built as a
    `python -m venv --without-pip` venv. The verdict is DENY `pytest-missing`. The fixture is run
    twice: once as the project `.venv`, and once with no project venv and the gate itself run by
    that interpreter. Both runs deny.
  - AC-4.2: RED gives ALLOW `red-measured`. GREEN gives DENY `test-passing`. An empty test file
    gives DENY `no-tests-ran`.
  - AC-4.3: A test file whose import fails gives DENY `pytest-error`, even though it exits
    non-zero.
  - AC-4.4: An interpreter shim that prints `1 failed in 0.01s` and exits 0 gives ALLOW. A shim that
    prints nothing and exits 1 gives DENY `no-summary`. This pins that rc selects nothing.
  - AC-4.5: A shim that sleeps past the bound gives DENY `timeout` within the bound plus a stated
    margin.
  - AC-4.6 [OD-6]: The `pytest-error` reason contains the words "import" and "inside the test body".
  - AC-4.7: `_suite_summary` returns parsed counts for each final line in §Measured premises. The
    audit gate's existing tests pass, apart from any test that pinned the `3 failed` →
    `UNREADABLE` behaviour. That test is updated, and the update is named in the impl-plan.

### FR-5: Codex gate — target base and governing state (OD-2, OD-3)

- **Description**:
  - **Target base.** `_relative_target` resolves a relative target against the payload `cwd` when
    that `cwd` is a directory inside the project root. Otherwise it resolves against the root, as
    today.
  - **Chain reader.** `_target_phase5_status` is replaced by one chain reader, shared with the
    Claude gate through the judge unit. The ACTIVE features are every step5 record in every state
    file from the target's directory up to the root, inclusive. Any unreadable file on the chain
    means `unknown`, which denies fail-closed, as today.
  - **Unchanged.** `_any_phase5_status` for the shell policy is unchanged.
  - **Crashes.** An exception anywhere in the gate's main path yields `_deny(...)` with
    `judge-error`, never an uncaught traceback.
- **Acceptance Criteria**:
  - AC-5.1 [OD-2]: payload `cwd` = `<root>/hematology-paper-writer`, patch target
    `tools/review_round/guideline_excerpts.py`, and a Task resolving it to a failing test. The
    write is ALLOWED. The deny path in the same fixture names
    `hematology-paper-writer/tools/review_round/guideline_excerpts.py`, never the unprefixed
    `tools/review_round/guideline_excerpts.py`.
  - AC-5.2 [OD-3]: the root state holds a step5 record, and the sub-project state holds none. A
    write to a sub-project production file with a **passing** test is DENIED `test-passing`, never
    allowed. This pins the fail-open measured in OD-3.
  - AC-5.3: The existing tests `test_codex_hook_scopes_nested_state_to_the_target_project` and
    `test_codex_hook_resolves_git_root_from_nested_cwd` pass unmodified.
    `test_codex_hook_rejects_pytest_no_tests_collected_as_red` is updated: its assertion on the
    literal `exit 1` in the reason becomes an assertion on `no-tests-ran`.
  - AC-5.4: A judge import failure, simulated by a broken shared module on the import path, gives a
    JSON deny with `judge-error`, rc 0 and parseable stdout.

### FR-6: Claude gate — payload, shared judge, blocking form (OD-4, OD-5, D4)

- **Description**:
  - **Payload.** The gate reads `tool_input.file_path`, then the top-level `file_path`, then the
    positional argument [OD-4].
  - **Judge.** After its existing exemptions and the Codex-authorship check, the gate calls the
    judge's CLI for every governed production `.py` write, whether or not the target exists yet
    [OD-5]. It reads the `TDD-JUDGE:` token. The gate passes the judge its project root
    (`CLAUDE_PROJECT_DIR`, as today) and the absolute target. The judge derives the ACTIVE features
    itself, with FR-5's chain reader. `_resolve_state_file` keeps only its role of taking the fast
    no-op path when no state file exists.
  - **Blocking form.** Every refusal site uses one form. The Codex-authorship BLOCK, every judge
    DENY and `judge-error` are all refusal sites. The form is chosen by FR-0's reading.
  - **Unchanged.** The non-blocking paths are unchanged: no state, no `jq`, not step5, and the
    exemptions.
- **Acceptance Criteria**:
  - AC-6.1 [OD-4]: A Claude-Code-shaped stdin payload
    `{"tool_name":"Write","tool_input":{"file_path":"<abs>"}, …}` on a step5 fixture with `codex`
    on PATH and `codex_status` available reaches the Codex-authorship refusal. Today it exits 0
    silently.
  - AC-6.2: The existing positional-argument tests in `test_h_mad_tdd_gate_state_resolution.py` and
    `test_h_mad_tdd_gate_codex.py` pass. Their rc assertions change only as AC-6.5 requires.
  - AC-6.3 [OD-5]: No `pytest` on PATH, and the resolved test passes. The result is a refusal with
    `kind=pytest-missing` or `test-passing`, never an allow.
  - AC-6.4: A **new** production file, whose target does not exist yet, with a passing resolved
    test is refused `test-passing`. Today it is allowed without a run.
  - AC-6.5 (branch `E1_DOES_NOT_BLOCK`): every refusal site emits one blocking form, chosen in the
    design. The recommended form is **(b)**, for parity with the Codex gate's `_deny`.
    - **(a)** rc = 2 with the reason on stderr.
    - **(b)** rc = 0 and exactly one stdout JSON object with
      `hookSpecificOutput.hookEventName == "PreToolUse"`,
      `hookSpecificOutput.permissionDecision == "deny"` and a non-empty
      `permissionDecisionReason`.

    For each refusal site, a test asserts that exact form, and asserts that rc is not 1. A test
    that asserts only "non-zero" does not satisfy this AC. `grep -c '^\s*exit 1\s*$'` on the hook
    returns 0.
  - AC-6.6 (branch `E1_BLOCKS`): the exit codes are unchanged. For each refusal site, a test asserts
    rc = 1 **and** the `[H-MAD-TDD-GATE] BLOCK:` stderr prefix, so that a later change of form is
    visible. The FR-0 reading is cited in the test module's docstring.
  - AC-6.7 (branch `INCONCLUSIVE`): neither AC-6.5 nor AC-6.6 is implemented, and Phase 4 does not
    start for this FR. AC-6.1 through AC-6.4 are independent of the branch and still ship.

### FR-7: Document the trust boundary (D2)

- **Description**: `h-mad/references/codex-runtime.md` §"Trust boundary" states the venv rule from
  FR-3: which venv is chosen, the containment test, the residuals, and the `venv-escapes-root`
  denial. It also states that the gate scores pytest's summary line, never rc.
- **Acceptance Criteria**:
  - AC-7.1: The section contains `.venv`, `realpath`, `venv-escapes-root` and "summary line". The
    existing test `test_codex_adapter_states_pytest_trust_boundary` passes.

### FR-8: Every guard bites

- **Description**: Each guard added by FR-2…FR-6 is mutation-tested, and each mutation is scored on
  the pytest summary.
- **Acceptance Criteria**:
  - AC-8.1: For each of the following guards, deleting or negating it turns at least one named AC
    test red: the Task-match authority (AC-2.5), the `none` value rule (AC-2.3), venv containment
    (AC-3.2), the `pytest-missing` branch (AC-4.1), the `errors ≥ 1` branch (AC-4.3), rc-blindness
    (AC-4.4), the payload `cwd` base (AC-5.1), the chain reader (AC-5.2), the `tool_input` read
    (AC-6.1) and the blocking form (AC-6.5 or AC-6.6). A branch of an alternation is mutated on
    its own, never together with its siblings.

## Live verification (not pytest ACs)

- **V-0**: FR-0's probe. It runs before FR-6's blocking form is implemented.
- **V-1**: This check runs before HemaSuite re-arms the Codex gate. **Dependency:** it needs
  `~/.agents/skills/h-mad`, which is absent today (`ls` reports "No such file or directory"). That
  install is owned by feature `multi-host-runtime`, and V-1 cannot run until it lands. V-1 has two
  arms:
  1. **Positive:** a real Codex GREEN `apply_patch` on a HemaSuite #28 production file whose Task
     test is RED is allowed.
  2. **Negative control:** the same payload, replayed by hand against a production file whose
     resolved test passes, is denied `test-passing`.

  An allow with no denying control is not a pass.

## Non-Functional Requirements

- **Performance**: each governed write runs pytest once per candidate test file. It stops at the
  first `red-measured`, is bounded by FR-4's timeout, and makes no whole-suite run. The latency is
  stated in the design, measured on the HemaSuite #28 Task 7 test file.
- **Security**: this is a workflow guard, not a sandbox (`codex-runtime.md` §"Trust boundary"). No
  new interpreter becomes trusted outside the containment rule, and no knob or environment variable
  is added (D2, D3). The existing declared `codex_status` and `HMAD_CODEX_UNAVAILABLE` escapes on
  the Claude side are unchanged.
- **Compatibility**: every write the gates allow today on a non-Phase-5 target is still allowed.
  Every existing test in `h-mad/tests` passes, apart from the updates FR-4, FR-5 and FR-6 name
  explicitly. The Codex gate's `--self-check` still prints `CODEX-TDD-GATE: PASS`.

## Out-of-Scope

- Installing `~/.agents/skills/h-mad`, including its `h_mad_install_check.py` entry. This is owned
  by `multi-host-runtime`, and V-1 depends on it.
- Changing the name map itself (`h_mad_derive_test_path.sh`'s three prefixes).
- How the grok host treats `exit 1`. That is owned by `multi-host-runtime`.
- The Claude gate's other fail-open paths, which stay as documented: no state, no `jq`, and the
  file-type exemptions.
- Venvs not named `.venv`, and `.venv/bin/pytest` as a shell entry point (FR-3 residuals).

## Assumptions

- Codex PreToolUse payloads carry `cwd`, which `_project_root` already reads, and `apply_patch`
  targets are relative to it. OD-2 rests on the blocked report and on the reproduced denial, not
  on a captured payload, so V-1 captures one.
- Claude Code honours `hookSpecificOutput.permissionDecision: "deny"` on exit 0, as the Codex gate
  already assumes. This is not measured here. If FR-0 is re-run, E2 is its only exit-code control.
- The impl-plan for an ACTIVE feature sits at `<state dir>/docs/01-plan/features/<feature>.impl-plan.md`.
  This holds for HemaSuite #28.

## Version History
- v1.0: Initial specification draft from brainstorm v1.1 (76b2501); D1–D4 bind; OD-1..OD-7 raised from tree measurements at ae7593a1 / HemaSuite ffa87323, each owed operator confirmation (2026-09-28).
