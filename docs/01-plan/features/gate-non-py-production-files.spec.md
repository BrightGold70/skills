# Spec: gate-non-py-production-files

## Executive Summary
During H-MAD Phase 5, a file that is not Python and not exempt as a test, fixture or doc is TDD-judged on all three write gates (Claude, codex, agy) **if and only if** the active feature's impl-plan lists it on some Task's **Production file** line. It is judged by that Task's listed test files, using the same RED rule as `.py`. Unlisted non-`.py` files stay allowed. Wire-pin 5b stops printing its `ungated:` line, because that line's claim is no longer true.

## Goal
Bring the code that most h-mad Phase-5 Tasks touch (shell scripts such as `h-mad/scripts/hmad-dispatch.sh` and extensionless launchers such as `h-mad/bin/hmad-dispatch`) under the same test-first gate as Python. This closes row 2856's gate half (skills defect #8) without making unrelated `.md`/`.json` writes need a Task.

## Terms used in this spec
- **Active chain.** The judge's `read_chain(root, target)` returns `value == "active"` for the target.
- **Listed.** Some canonical name of the target (see FR-3) matches an entry in some Task's `production` list, in the impl-plan of some active record. The match is the judge's existing `resolve` comparison.
- **Exempt.** The target sits under a `tests` or `fixtures` path component, or under the project root's own `docs/` first component, or outside the project root. These are the existing exemption rules of each gate, and this feature does not change them.
- **Non-`.py`.** No canonical name of the target ends in `.py` after `h_mad_target_identity.fold_py_suffix`. This includes the `.pY`/`.Py`/`.PY` folds.
- **Verdicts, per host.** These are the observable forms each hook emits today:
  - Claude (`h-mad/hooks/h-mad-tdd-gate.sh`): ALLOW is exit 0 with no stdout. DENY is a `hookSpecificOutput` JSON object with `permissionDecision: "deny"` and reason `[H-MAD-TDD-GATE] BLOCK kind=<kind>: …`.
  - codex (`h-mad/hooks/h-mad-codex-tdd-gate.py`): ALLOW is exit 0 with no stdout. DENY is the same `hookSpecificOutput` deny object, with `kind=<kind>` in the reason.
  - agy (`h-mad/hooks/h-mad-agy-tdd-gate.py`): `{"decision": "allow"}` or `{"decision": "deny", "reason": "… kind=<kind>"}`.

## Fixture used by the acceptance criteria
The fixture is a scratch git repo `R`. It contains `docs/.bkit-memory.json` holding an active Phase-5 record for feature `f` (`implementer` unset, codex and agy available), and `docs/01-plan/features/f.impl-plan.md` holding:

```markdown
## Task 1: tool
**Task shape**: `new-behaviour`
**Production file**: `scripts/tool.sh`, `bin/launch`
**Test file**: `tests/test_tool.py`
```

`R/scripts/tool.sh`, `R/bin/launch` and `R/scripts/other.sh` exist. "Test absent" means `R/tests/test_tool.py` does not exist. "Test passing" means it holds one passing pytest test. "Test failing" means it holds one test that fails on an assertion. Each host is driven through its real hook entry point with that host's write payload naming the target.

## Functional Requirements

### FR-1: The task parser records every backticked production path in `production`
- **Description**: `h_mad_wire_pin_gate._parse_tasks` adds every non-`.py` path token on a **Production file** line to `task["production"]`, alongside the `.py` tokens. Today those tokens go to `task["ungated"]`. Non-`.py` tokens are recognised by the existing `_NON_PY_PATH_RE` grammar: a backticked token with no whitespace that contains `/` or `.`. `task["tests"]` stays `.py`-only, because the judge runs pytest. This settles Open Question (a) by widening the existing field, not by adding a sibling one. The census in §"Resolved open questions" shows the judge is the only reader of `production`, and the judge is the reader that must see these paths.
- **Acceptance Criteria**:
  - AC-1.1: The input `## Task 1: t` / `**Production files**: `h-mad/scripts/hmad-dispatch.sh`, `h-mad/scripts/a.py`, `h-mad/bin/hmad-dispatch`` parses to a `production` list that contains exactly those three strings.
  - AC-1.2: On a **Production file** line that has no non-`.py` token, `production` is unchanged in both items and order. The existing tests in `h-mad/tests/test_h_mad_parse_tasks_paths.py` (`test_paths_label_spelling`, `test_none_value_contributes_nothing`, `test_none_rule_keeps_a_real_path`, `test_label_lines_accumulate`, `test_existing_fields_unchanged`, `test_corpus_old_fields_unperturbed`) pass unmodified.
  - AC-1.3: A `none` value (the `_NONE_VALUE_RE` rule) still contributes nothing. `**Production file**: none (writes `docs/x/run.sh`)` yields `production == []`.
  - AC-1.4: A non-`.py` token on a **Test file** line contributes nothing. `**Test file**: `h-mad/tests/mutation-specs/x.json`` yields `tests == []`.
  - AC-1.5: `shape`, `wire`, `pin`, `wires`, `pins`, `path_labels`, `runner`, `runner_error` and `judge_budget` are identical for a Task with and without a non-`.py` production token.

### FR-2: Wire-pin 5b no longer reports listed non-`.py` files as `ungated`
- **Description**: Wire-pin 5b currently prints `  ungated: <task> (<name>): `<path>` — not .py, so no TDD judge or wire-pin covers it`. FR-4 through FR-7 make the "no TDD judge" part false, so the line is retired, together with the `ungated` key of `check()`'s result and of the task dict. The `WIREPIN:` summary token, its fields and its verdicts (`PASS`, `FAIL`, `UNSHAPED`, `UNREADABLE`) are unchanged. This settles Open Question (b).
- **Acceptance Criteria**:
  - AC-2.1: `python3 h-mad/scripts/h_mad_wire_pin_gate.py <plan>` on a plan whose only Task is `new-behaviour` with **Production file** `h-mad/scripts/x.sh` prints first line `WIREPIN: PASS tasks=1 wiring=0 unpinned=0 mislabeled=0`, and no output line contains `ungated:`.
  - AC-2.2: `check(<that plan>)` returns a dict with no `ungated` key, and `_parse_tasks` returns task dicts with no `ungated` key.
  - AC-2.3: An `UNSHAPED` plan with a non-`.py` production token still returns `verdict == "UNSHAPED"`, with its other keys unchanged.
  - AC-2.4: The guarantees the retired U1 and U2 mutants protected are re-pinned on `production` (FR-1): a `.sh` token is collected and an extensionless token is collected. Every mutant in `h-mad/tests/mutation-specs/wire_pin_ungated.json` is either retired or re-pointed at a test that still exists, and a mutation run over that spec scores no mutant as SURVIVED.

### FR-3: One listing matcher, shared by the judge and all three gates, alias-closed on the target side
- **Description**: Whether a target is listed is decided by exactly one implementation: the impl-plan match inside `h_mad_tdd_judge.resolve`. That match walks each ancestor `base` of the target from its parent up to the root, and compares `os.path.realpath(base / entry)` with the target's realpath for each `production` entry. The codex and agy gates reach it in-process through `h_mad_target_identity._load_judge()`. The Claude gate reaches it through a judge CLI verb or flag, whose output is one line with an enumerated set of values: one value for listed, one for not listed, and one for unreadable. The design must name every value. The gate refuses with `kind=judge-error` on zero lines, several lines, a non-zero exit or an unrecognised value, as it does for the `state` and `judge` verbs today. No gate re-implements the match.

  Alias spellings are closed by evaluating the predicate over the target's canonical names from `h_mad_target_identity.canonicalise`, never over the spelled path. `canonicalise` follows symlinks to the referent. For an existing file it returns the on-disk spelling, so a case-variant spelling folds. Its `names` holds every same-directory hard link. The target is listed if any of those names is listed.
- **Acceptance Criteria**:
  - AC-3.1: The codex gate, the agy gate and the Claude gate's CLI path all call the same function for the listing decision. A mutation that makes that function always return "not listed" turns AC-5.1, AC-6.1 and AC-7.1 from DENY to ALLOW on all three hosts. Each host has its own failing test, run with that host alone.
  - AC-3.2 (symlink): `R/link.sh` is a symlink to `R/scripts/tool.sh`. With the test absent, a write to `link.sh` is DENY `kind=test-missing` on each host.
  - AC-3.3 (case fold, existing file, case-insensitive volume): with the test absent, a write spelled `scripts/TOOL.SH` is DENY `kind=test-missing` on each host.
  - AC-3.4 (hard link, same directory): `R/scripts/hard.sh` is a hard link to `R/scripts/tool.sh`. With the test absent, a write to `scripts/hard.sh` is DENY `kind=test-missing` on each host. The judge receives a listed name, so its resolution source is `impl-plan` and never `name-map`.
  - AC-3.5 (residual, stated, not closed): the spec names the three spellings below as known ALLOW, so no gate is expected to deny them. A test pins each one as ALLOW so that a later change to it is visible:
    1. An impl-plan entry whose case differs from the on-disk name. `resolve` realpaths the plan entry, and realpath does not fold case on macOS. Measured with `os.path.realpath` and `canonicalise` on APFS at `0cb7b9b0`: the realpath keeps `HMAD-Dispatch.SH` while `canonicalise` returns `hmad-dispatch.sh`.
    2. A not-yet-existing target spelled in a case that differs from the plan entry. For an absent leaf, `canonicalise` returns the spelled basename (`New.SH` stays `New.SH`).
    3. A hard link in a different directory. `Identity.names` lists same-directory names only.

    All three are residuals of today's `.py` path too, where the name-map fallback may still catch them. For non-`.py` there is no fallback.

### FR-4: The judge judges a listed non-`.py` target by its Task's tests only
- **Description**: `h_mad_tdd_judge.judge` handles a listed non-`.py` target the way it handles a listed `.py` one. Resolution source is `impl-plan`. Candidates are the matched Task's `tests` entries, newest first. The verdict is `ALLOW kind=red-measured` on the first failing test, and the Task's **Judge budget** applies. Two Python-only shortcuts are disabled for such a target. The first is the name-map fallback (`h_mad_derive_test_path.sh`), which the judge must never reach for a listed target. The second is the import-failure RED shortcut, `score`'s `M:K-IMPORT-RED` arm: `target_module_names` returns an empty set for a non-`.py` target, because writing a shell script never fixes a Python `ModuleNotFoundError`. This settles Open Question (c).
- **Acceptance Criteria**:
  - AC-4.1: The fixture is used with test failing on an assertion. `judge(R, R/scripts/tool.sh, records)` returns `Verdict("ALLOW", "red-measured", …)` with source `impl-plan` and test `R/tests/test_tool.py`.
  - AC-4.2: Same with the test passing: `DENY kind=test-passing`.
  - AC-4.3: Same with the test absent: `DENY kind=test-missing`. The reason names `tests/test_tool.py`.
  - AC-4.4: The Task's **Test file** is `tests/tool.bats`, so `tests` is empty. The verdict is `DENY kind=test-missing`. A listed non-`.py` file whose Task names no pytest file can never be written while Phase 5 is active.
  - AC-4.5: `target_module_names(R, R/scripts/tool.sh)` and `target_module_names(R, R/bin/launch)` return `frozenset()`. A failing test whose only `E` line is `E   ModuleNotFoundError: No module named 'tool'`, run against the absent target `R/scripts/tool.sh`, scores `pytest-error`, never `red-measured`. A `.py` target keeps today's behaviour, and the existing `M:K-IMPORT-*` tests pass unmodified.
  - AC-4.6: For an unlisted non-`.py` target, `judge` still returns `DENY kind=no-test-resolved`, because `h_mad_derive_test_path.sh` prints nothing for a non-`.py` path. The gates never route an unlisted target to `judge` (FR-5 to FR-7). This AC pins the fail-closed backstop.

### FR-5: Claude gate — the non-`.py` early allows become "allow unless listed"
- **Description**: In `h-mad/hooks/h-mad-tdd-gate.sh`, the `ALL_SUFFIX_NAMES` and `ALL_NON_PY` early allows no longer allow a target that is listed. Everything before them stays in order and unchanged: the canonicalisation, the unresolvable arm, `_chain_may_hold_state`, the `.py` test-name allow, and the `tests`/`fixtures`/root-`docs/`/scratch exemptions. For a non-`.py` target that reaches them, the gate does four things in order. It reads state; `TDD-STATE: none` means ALLOW. It decides listing through FR-3; not listed means ALLOW. A listed target then passes through the existing implementer, peer-authorship and fallback refusals unchanged. Finally the judge is called with a listed canonical name as `--target`. The `.py` path is unchanged.
- **Acceptance Criteria**:
  - AC-5.1: With the test absent, a Claude `Write` to `R/scripts/tool.sh` (with `implementer=null` so Claude is the author) is DENY `kind=test-missing`.
  - AC-5.2: Same with the test passing: DENY `kind=test-passing`. Same with the test failing: ALLOW.
  - AC-5.3: A Claude `Write` to `R/bin/launch` with the test absent is DENY `kind=test-missing`. An extensionless listed file is judged.
  - AC-5.4 (control): a Claude `Write` to the unlisted `R/scripts/other.sh` and to `R/notes.md` is ALLOW, in the same state as AC-5.1.
  - AC-5.5: With the default implementer (codex resolves), a Claude `Write` to `R/scripts/tool.sh` is DENY `kind=codex-authorship`. A Claude `Write` to the unlisted `R/notes.md` in that state is ALLOW, as today.
  - AC-5.6: Without `docs/.bkit-memory.json`, or with a record that is not active, a Claude `Write` to `R/scripts/tool.sh` is ALLOW.
  - AC-5.7: A listed `R/tests/helper.sh` (listed as `tests/helper.sh`) is ALLOW, by the existing `_dir_match` exemption.

### FR-6: codex gate — judge a listed non-`.py` target
- **Description**: In `h-mad/hooks/h-mad-codex-tdd-gate.py`'s per-target loop, the selection becomes this: a name qualifies when `_is_production_python(relative)` is true, or when it is non-`.py`, not exempt, and listed per FR-3. If any name is production Python, the existing `min(production)` selection over the `.py` names is kept. Otherwise the smallest listed name is judged. The existing `read_chain`, `judge` and deny path is used unchanged.
- **Acceptance Criteria**:
  - AC-6.1: With the test absent, a codex `apply_patch` with header `*** Update File: scripts/tool.sh` is DENY with `kind=test-missing` in the reason.
  - AC-6.2: Same with the test passing: DENY `kind=test-passing`. Same with the test failing: ALLOW.
  - AC-6.3 (control): `*** Update File: scripts/other.sh` and `*** Add File: notes.md` are ALLOW in the AC-6.1 state.
  - AC-6.4: A patch touching both `scripts/other.sh` and `scripts/tool.sh` is DENY when the test is absent. One listed target in a multi-target patch is enough.

### FR-7: agy gate — judge a listed non-`.py` target
- **Description**: `h-mad/hooks/h-mad-agy-tdd-gate.py` follows the same selection rule as FR-6, in its write-class (T6–T7) loop. The existing T1–T5 checks run first and are unchanged: unresolvable, directory, outside-root, and the allowance file.
- **Acceptance Criteria**:
  - AC-7.1: With the test absent, an agy write call targeting `scripts/tool.sh` produces `{"decision": "deny", …}` with a reason ending `kind=test-missing`.
  - AC-7.2: Same with the test passing: deny `kind=test-passing`. Same with the test failing: `{"decision": "allow"}`.
  - AC-7.3 (control): agy writes to `scripts/other.sh` and `notes.md` produce `{"decision": "allow"}`.

### FR-8: An undecidable listing fails closed
- **Description**: In some states, listing cannot be decided for a non-`.py`, non-exempt target. Each gate then denies with `kind=judge-error` instead of allowing. The cases are: the chain is unreadable (`read_chain` returns `unreadable`, or the Claude gate's state line matches `STATE_UNREADABLE_RE`), or an active record's impl-plan exists but raises `OSError` or `UnicodeDecodeError` on read. An absent impl-plan, where `resolve` notes `absent`, is "not listed", so the write is ALLOW. This tightens today's behaviour for unlisted files in exactly these states, and nowhere else. See §"Assumptions".
- **Acceptance Criteria**:
  - AC-8.1: `R/docs/01-plan/features/f.impl-plan.md` is replaced by a file with invalid UTF-8. A write to `R/notes.md` is DENY `kind=judge-error` on each host.
  - AC-8.2: `R/docs/.bkit-memory.json` is made unparsable. A write to `R/scripts/other.sh` is DENY `kind=judge-error` on each host.
  - AC-8.3: The record is active and `f.impl-plan.md` is absent. A write to `R/notes.md` is ALLOW on each host.

### FR-9: End-to-end proof on every host, with a control
- **Description**: The feature is demonstrated by driving each host's real hook entry point against scratch repos built to the fixture above, using the `verify-hmad-gates` skill (orchestrator decision 3). Every DENY row has a paired control that runs the same write to an unlisted `.sh` in the same state. Each host is run on its own, so a healthy host cannot cover a sick one.
- **Acceptance Criteria**:
  - AC-9.1: For each of Claude, codex and agy, the run records the following verdicts: listed `scripts/tool.sh` with the test absent is DENY `test-missing`; with the test failing it is ALLOW; the unlisted `scripts/other.sh` in the test-absent state is ALLOW.
  - AC-9.2: Each host's run records which hook file it executed, by path and sha256 at the commit under test, so the reading cannot have come from the live `~/.claude/skills/h-mad` symlink, which points at a different checkout.
  - AC-9.3: Every new guard in FR-1 and FR-3 to FR-8 has a mutation-spec entry. Each mutant is killed by a test that fails for the guard's own reason. Results are scored on the pytest summary, not on `$?`.

## Non-Functional Requirements
- **Performance.** An unlisted non-`.py` write whose ancestor chain holds no `docs/.bkit-memory.json` starts no new process, because `_chain_may_hold_state` keeps its early allow. Where state exists, the Claude gate starts at most two extra short Python processes for such a write (the state read and the listing decision), and the design may merge them into one. The pytest run is paid by listed targets only.
- **Security.** There is no new allow path. Every change either turns an ALLOW into a judged decision or keeps it. FR-8 states every case that turns an existing ALLOW into a DENY.
- **Compatibility.** The Claude gate stays runnable under macOS `/bin/bash` 3.2 (the shebang is `#!/bin/bash`). `WIREPIN:`, `TDD-JUDGE:` and `TDD-STATE:` keep their current shapes and value sets. The `.py` behaviour of all three gates and of `judge` is byte-identical on every existing test.

## Resolved open questions (measured at `0cb7b9b0`, from PROJECT_ROOT)

**(a) Consumers of `_parse_tasks`, and what each does with a non-`.py` path.**

Commands:
- `graft callers _parse_tasks --depth all`
- `git grep -n "_parse_tasks" -- ':!docs/archive'`
- `git grep -n '"production"' -- h-mad/`

Results:
- `_parse_tasks` has 5 production call sites in 4 files, one per consumer bullet (the next five). Both commands agree.
- `h_mad_assemble_tdd.assemble` reads `id`, `shape`, `wire` and `pin` only, so a non-`.py` path changes nothing.
- `h_mad_wire_pin_gate.check` reads `shape`, `wires`, `pins`, `path_labels` and (today) `ungated`, never `production`, so nothing changes except FR-2.
- `h_mad_wire_pin_gate.main` (registration, `_register_wiring_tasks`) reads `id`, `name`, `shape`, `wires`, `pins`, `runner` and `runner_error`, so nothing changes.
- `h_mad_wire_registry.challenge` takes `tasks` but builds its claims with its own `_production_claims` line regex. That regex already sees non-`.py` values. It reads only `*.py` diffs (`changed_files` passes `-- '*.py'` to git), so nothing changes.
- `h_mad_tdd_judge.resolve` is the only reader of `task["production"]` among scripts. It gains the non-`.py` entries, which is the intended change.
- The other hits are tests (`test_h_mad_parse_tasks_paths.py`, `test_h_mad_tdd_judge.py`) and one archived probe under `docs/archive/`, which no gate executes.
- The reason this zero (no other reader) holds is load-bearing: `production` was introduced as the judge's map (comment at `_NON_PY_PATH_RE`). A future consumer that assumes `.py` must filter for itself.

**(b) `ungated:`.** FR-2: retired. `git grep -n -e "no TDD judge" -e "ungated:" -- h-mad ':!h-mad/tests'` finds the wording only in `h_mad_wire_pin_gate.py`, in the task-dict comment and the `main` print. No reference or SKILL.md surface restates it. The tests that pin it are `test_h_mad_wire_pin_gate.py`'s six `…ungated…` functions (counted with `grep -c`: 6 function definitions, one of them parametrised three ways) and the 5 mutants in `wire_pin_ungated.json` (U1 to U5, counted from its `mutations` array).

**(c) Test-path derivation from the filename.** `h_mad_derive_test_path.sh` prints nothing for any path that is not `*.py`, through its explicit non-`.py` early exit. The judge reaches it only when no impl-plan Task matched. The judge also derives `target_module_names` from the filename, by stripping any suffix, so `scripts/tool.sh` yields `{"scripts.tool", "tool"}` and `bin/launch` yields `{"bin.launch", "launch"}` today (run at `0cb7b9b0`). That is the one suffix-blind derivation, and FR-4 / AC-4.5 close it.

**(d) Every suffix filter on the write path.** Census: `git grep -n -e _is_production_python -e fold_py_suffix -e PY_SUFFIXES -- h-mad`, plus a read of each gate's decision loop.
- Judge: verbs `state` and `implementer` do not filter by suffix. Verb `judge` adds the name-map `*.py` filter and `target_module_names`.
- Identity: `PY_SUFFIXES` / `fold_py_suffix`, and `_is_production_python`, which is false for any non-`.py` suffix.
- Claude gate: `_fold_py`, the `.py` test-name allow (`ALL_TEST_NAMES`), `ALL_SUFFIX_NAMES`, `ALL_NON_PY` and the `PRODUCTION_TARGET` selection.
- codex gate: `_tmp_report_target`, where a `.py` under `/tmp` stays refused, and `_is_production_python` in the target loop.
- agy gate: `outside_allowed`, where a `.py` outside the root stays refused, and `_is_production_python` in T6.

The out-of-root rules are unaffected, because a listed target is in-root by construction: `resolve` requires `_inside(real_target, real_root)`. `h_mad_mutation_harness.py` reads `mutation-specs/` but is not on any write gate's path.

## Out-of-Scope
- Unlisted non-`.py` files. They are allowed exactly as today, except in the FR-8 states (operator, 2026-11-03).
- Wire-registry challenge for non-`.py` files. `changed_files` passes `-- '*.py'` to git, and `ast_targets` parses Python, so a cross-boundary call added in a `.sh` is never challenged. The census in (a) found no consumer that needs it.
- Non-pytest test runners for the judge, such as `.bats` and shell test harnesses. AC-4.4 states the consequence.
- Production tokens the `_NON_PY_PATH_RE` grammar does not capture, listed with their consequence:
  - A bare root-level name with neither `/` nor `.`, such as `` `Makefile` ``, is not collected and is not gated. Spelling it `` `./Makefile` `` collects it.
  - A directory token (`` `h-mad/scripts/` ``) or a glob token is collected, but it equals no file's realpath, so it gates nothing and is not reported.

  The parser probe at `0cb7b9b0` showed `Makefile` dropped and `h-mad/scripts/` collected.
- Writes made by a shell command that an operator allowance (`.h-mad/phase5-shell-allow`) or the safe-command list admits. Like `.py` writes by the same route, they are not judged.
- The three alias residuals of AC-3.5.
- A target with both a production-`.py` name and a listed non-`.py` name. It is judged by its `.py` name (today's selection), so the listed Task's tests are consulted only if the `.py` name also resolves.

## Assumptions
- FR-8 refines orchestrator decision 1 ("unlisted non-`.py` files stay allowed exactly as today") for the one case where listed-ness cannot be decided. It fails closed, following the project-wide fail-closed invariant. The operator ruled this way on 2026-11-03 (judgement call 4, below), so "allow when undecidable" is not an open alternative.
- Operator rulings, 2026-11-03, binding. They confirm v1.0 as drafted and change no requirement. Call 1: widen `task["production"]` (FR-1). Call 2: retire the `ungated:` line and the `ungated` key (FR-2). Call 3: the import-failure RED shortcut is disabled for a non-`.py` target (FR-4, AC-4.5). Call 4: FR-8 fails closed. Call 5: the Claude gate takes its listing decision from a CLI whose values the design names (FR-3).
- The impl-plan Task grammar (`_TASK_RE`, `_PATHS_FIELD_RE`, `_NON_PY_PATH_RE`, `_NONE_VALUE_RE`) is unchanged. `test_field_re_is_unchanged` keeps pinning `_FIELD_RE`.
- The `verify-hmad-gates` skill is available to the orchestrator at Phase 5. It lives in the main checkout's project-scoped skills directory, `/Users/kimhawk/orca/skills/.claude/skills/verify-hmad-gates/` (it holds `SKILL.md`, `bin/` and `features/`). That directory is ignored by the `.claude/` entry in `.gitignore` and is untracked, so it is absent from this worktree; it is also absent from `~/.claude/skills`. Verified 2026-11-04 with `ls -d` on both paths and `git check-ignore -v .claude/skills/verify-hmad-gates`, which names the `.gitignore` `.claude/` rule. FR-9's ACs are written against the hooks' observable verdicts and do not depend on the skill's internals, so a change to the skill cannot change what FR-9 requires.
- Work happens in the worktree `gate-non-py-production-files`. The live hooks under `~/.claude/skills/h-mad` resolve to another checkout and are never the system under test.

## Version History
- v1.0: Initial specification draft (2026-11-03), from the approved brainstorm v1.0 and orchestrator decisions 1-3. Resolves open questions (a)-(d) from the tree at 0cb7b9b0. No audit cycle answered (first draft).
- v1.1: Corrects the `verify-hmad-gates` availability claim in §"Assumptions" (2026-11-04): the skill is present at `/Users/kimhawk/orca/skills/.claude/skills/verify-hmad-gates/`, untracked and ignored by `.gitignore` `.claude/`, so absent from this worktree only; FR-9 stays independent of the skill's internals. Records the operator rulings of 2026-11-03 (judgement calls 1-5, all confirming v1.0) and removes FR-8's open "if the ruling is instead" alternative. Operator approval of v1.0 was conditional on this correction. No audit cycle answered (orchestrator-verified finding, no audit report).
